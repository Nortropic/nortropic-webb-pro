#!/usr/bin/env python3
"""Intervjuns AI-tur med en riktig modell i den riktiga appen (J02, intervjudelen; kunskap/desktop.md, Prov). En ny testkund
skapas genom appens Ny testkund, ägaren antecknar kundens svar och väljer Spara svaret och låt AI fortsätta; Kundstarts
modellarbetare tar det ärendets köjobb med pilotens transport (`--live-cli`, provinstansens NWP_KUNDSTART_MODELL eller
standardmodellen). Provet väntar på AI:s tur och läser det AI skrev: meddelandet, frågekorten och förslagen.

    .venv/bin/python -B desktop/prov/prov_intervju_ai.py --port 4791 --ut <katalog>

Kostar ett modellanrop (en tur, inom testkundens budget). Bara fiktiva testkunder får AI-turer.
"""
import argparse
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appdrivare as ad  # noqa: E402

VERKTYG = {'claude': '/opt/homebrew/bin/claude', 'node': '/opt/homebrew/bin/node'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--ut', required=True)
    a_ = ap.parse_args()
    if a_.port == 4771:
        raise SystemExit('provet körs mot en provinstans, aldrig mot huvudutcheckningens :4771')
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    a = ad.App(ad.ROT, a_.port, data=Path(tempfile.mkdtemp(prefix='nwp-desktop-ai-')))
    a.registrera(VERKTYG)
    a.starta()
    resultat = {'fall': 'intervjuns AI-tur med riktig modell', 'prov': 'J02 E4 U18'}
    namn = 'AI-intervjuprovet %s (test)' % time.strftime('%H%M%S')
    hamta = lambda vag: a.js("(function(){var x=new XMLHttpRequest();x.open('GET',%s,false);x.send();return JSON.parse(x.responseText)})()" % json.dumps(vag))  # noqa: E731
    try:
        a.vanta(lambda: a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden && !document.getElementById('las-upp').disabled"), text='låsvyn')
        a.js("document.getElementById('las-upp').click(), true")
        a.vanta(lambda: a.js("!!document.querySelector('.pt-primara')"), text='Hem')
        a.js("location.hash = '#/ny-testkund', true")
        a.vanta(lambda: a.js("!!document.getElementById('pt-foretag')"), text='formuläret')
        a.js("""(function(){var s=function(id,v){var e=document.getElementById(id);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))};
            s('pt-foretag',%s);var f=document.getElementById('pt-form');f.syfte.value='Fler bokningar av cykelservice; en enkel sajt som visar priser och öppettider.';
            f.syfte.dispatchEvent(new Event('input',{bubbles:true}));f.requestSubmit();return 1})()""" % json.dumps(namn))
        a.vanta(lambda: '#/intervju/' in (a.lage().get('url') or ''), tid=30, text='intervjun')
        eid = a.lage()['url'].split('#/intervju/')[1][:32]
        a.vanta(lambda: a.js("!!document.getElementById('pt-svar-text')"), text='svarsfältet')
        t0 = time.time()
        a.js("""(function(){var t=document.getElementById('pt-svar-text');t.value=%s;t.dispatchEvent(new Event('input',{bubbles:true}));
            var b=document.querySelector('#pt-svar-form button[name=ai][value="1"]');b.click();return 1})()""" % json.dumps(
            'Vi är en liten cykelverkstad i Testby (fiktiv). Vi gör service och säljer begagnade cyklar. Kunderna ringer oftast; vi vill att fler bokar service på nätet.'))
        a.vanta(lambda: (hamta('/api/kundstart/%s' % eid)['arende'].get('modell') or {}).get('status') not in (None, 'inte_startad'), tid=30, text='AI-jobbet köat eller startat')
        bild1 = a.bild(ut / 'ai-1-startad.png').name
        def klar():
            x = hamta('/api/kundstart/%s' % eid)['arende']
            ai_med = [m for m in x.get('meddelanden') or [] if m.get('roll') != 'kund']
            return x if ai_med or (x.get('modell') or {}).get('status') in ('fel', 'stoppad') else None
        arende = a.vanta(klar, tid=600, steg=3, text='AI:s tur')
        sekunder = round(time.time() - t0, 1)
        a.js("location.hash = '#/start'; true")
        time.sleep(0.5)
        a.js("location.hash = '#/intervju/%s'; true" % eid)
        a.vanta(lambda: a.js("document.querySelectorAll('#pt-msgs .pt-msg.ai').length") > 0, tid=30, text='AI:s meddelande i vyn')
        time.sleep(1)
        bild2 = a.bild(ut / 'ai-2-svar.png').name
        ai_med = [m for m in arende.get('meddelanden') or [] if m.get('roll') != 'kund']
        modell = arende.get('modell') or {}
        assert ai_med, ('inget AI-meddelande', modell)
        resultat.update(utfall='godkänt', belagg={
            'arende': eid, 'testkund': arende.get('fiktiv'), 'sekunder_till_ai_svar': sekunder, 'modell': {k: modell.get(k) for k in ('status', 'modell', 'modell_observerad', 'transport', 'text')},
            'budget': arende.get('budget'), 'ai_meddelande': ai_med[-1].get('text', '')[:400], 'fragekort': [q.get('text') for q in arende.get('fragor') or []][:5],
            'forslag': [f.get('text') for f in (arende.get('forslag') or {}).values()][:5], 'bilder': [bild1, bild2]})
    except Exception as e:  # noqa: BLE001
        resultat.update(utfall='underkänt', fel='%s: %s' % (type(e).__name__, e), spar=traceback.format_exc()[-1500:])
    finally:
        a.avsluta()
    (ut / 'prov_intervju_ai.json').write_text(json.dumps(resultat, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(resultat, ensure_ascii=False)[:1500])
    return 0 if resultat.get('utfall') == 'godkänt' else 1


if __name__ == '__main__':
    sys.exit(main())
