#!/usr/bin/env python3
"""Direktredigering i den levande förhandsvisningen, partnerns ström och Genomför i utkastet i den riktiga appen
(kunskap/arbetsyta.md, Den levande förhandsvisningen; kunskap/desktop.md, Prov). Provbyggda Nortropic.app i riktig
WKWebView mot en provinstans med ett fiktivt testprojekt (arbetsyta_fixtur.py, en riktig Astro-kandidat).

    .venv/bin/python -B desktop/prov/prov_redigering_app.py --port 4791 --ut <katalog> [--slug testdata-redigering]
        [--partner] [--genomfor]

Redigeringen: en provdrivare i kandidatens byggda sida (bara i provets dist/, som försvinner vid ombygget) gör det en
människa gör i förhandsvisningen: klickar på texten när arbetsytan säger Redigera text, skriver den nya texten och trycker
Enter. Bryggan, arbetsytan, motorns karta, flödesstarten, ombygget och fotograferingen är de riktiga. --partner skickar en
fråga till partnern (provinstansens NWP_PARTNER_MODELL, en riktig modell) och mäter när det första delsvaret och svaret
syns; --genomfor ber partnern om en ändring och genomför dess överlämning, och stoppar sedan arbetet i Kontroller.
"""
import argparse
import html
import json
import re
import sys
import tempfile
import time
import traceback
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appdrivare as ad  # noqa: E402

ROT = ad.ROT
sys.path.insert(0, str(ROT / 'kontroller'))
sys.path.insert(0, str(ROT / 'kontroller' / 'rokprov' / 'revision'))
VERKTYG = {'claude': '/opt/homebrew/bin/claude', 'node': '/opt/homebrew/bin/node'}
RESULTAT = []


def fall(namn, prov, fn):
    t = time.time()
    try:
        belagg = fn() or {}
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'godkänt', 'belagg': belagg, 'sekunder': round(time.time() - t, 2)})
        print('ok   %s %s' % (namn, json.dumps(belagg, ensure_ascii=False)[:500]), flush=True)
    except Exception as e:  # noqa: BLE001
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'underkänt', 'fel': '%s: %s' % (type(e).__name__, e), 'spår': traceback.format_exc()[-2000:]})
        print('FEL  %s %s: %s' % (namn, type(e).__name__, e), flush=True)


def forbered(slug):
    """Testprojektet (fiktivt) med ägarens första val gjort, och en text i k01 som direktredigeringen kan knyta."""
    import arbetsyta_fixtur
    import atelje
    import direktredigering
    import kandidater
    import skapande
    assert atelje.ROOT.resolve() == ROT.resolve(), 'provet skriver bara i worktreens egna underlag/ och kunder/'
    if not (atelje.UNDERLAG / slug).exists():
        arbetsyta_fixtur.bygg(ROT, slug)
    if not any(d.get('beslut') == 'valj' for d in skapande.domar(slug, atelje.UNDERLAG)):
        p = kandidater.plan_tid(slug)
        skapande.lagg_till_dom(slug, 'ägaren', 'valj', 'Ägarens ord i provet: valj.', avser='skapandeflödet, kandidatplanen %s' % p,
                               underlag=atelje.UNDERLAG, plan=p, kandidater=[{'id': 'k01', 'version': kandidater.las_status(slug, 'k01').get('version'),
                                                                               'etikett': 'Förslag A', 'plan': p, 'metod': None}])
    if kandidater.projektets_version(slug, 'k01') != kandidater.las_status(slug, 'k01').get('version'):
        # fixturen ändrar startsidan efter sin fotografering (kodvyns diff); en riktig fotografering först, som i en körning
        st = kandidater.fotografera(slug, 'k01')
        print('förberedelse: k01 fotograferad: %s %s' % (st.get('status'), str(st.get('skal'))[:200]), flush=True)
    st = json.loads((atelje.UNDERLAG / slug / 'atelje' / 'STATUS.json').read_text(encoding='utf-8'))
    if st.get('steg') != 'klar_for_bedomning' or st.get('pid'):
        raise AssertionError('testprojektets körning väntar inte på ägaren: %s' % st.get('steg'))
    dist = kandidater.ksajt(slug, 'k01') / 'dist' / 'index.html'
    sidan = dist.read_text(encoding='utf-8')
    for m in re.finditer(r'<(h1|h2|h3|p|li)\b[^>]*>([^<>{}]{8,120})</\1>', sidan):
        text = html.unescape(re.sub(r'\s+', ' ', m.group(2))).strip()
        try:
            direktredigering.kartlagg(slug, 'k01', text)
            return dist, text
        except direktredigering.EjMappbar:
            continue
    raise AssertionError('ingen text i k01 kunde knytas entydigt till källan')


DRIVARE = """<script>/* provdrivaren (prov_redigering_app.py): bara i provets dist/ */
(() => { const GAMMAL = %s, NY = %s;
  const hitta = () => Array.from(document.querySelectorAll('h1,h2,h3,p,li')).find((e) => e.textContent.replace(/\\s+/g, ' ').trim() === GAMMAL);
  addEventListener('message', (ev) => { const d = ev.data; if (!d || d.nwp !== 'forhandsbrygga/1') return;
    if (d.typ === 'lage' && d.lage === 'redigera') setTimeout(() => hitta()?.click(), 600);
    if (d.typ === 'redigera-start') setTimeout(() => { const el = document.querySelector(d.selektor); if (!el) return; el.textContent = NY;
      el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })); }, 600);
  });
})();</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--ut', required=True)
    ap.add_argument('--slug', default='testdata-redigering')
    ap.add_argument('--partner', action='store_true')
    ap.add_argument('--genomfor', action='store_true')
    a_ = ap.parse_args()
    if a_.port == 4771:
        raise SystemExit('provet körs mot en provinstans, aldrig mot huvudutcheckningens :4771')
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    slug = a_.slug
    import direktredigering
    import kandidater
    dist, gammal = forbered(slug)
    ny = gammal.rstrip('.') + ' – ändrad i appen'
    sidan = dist.read_text(encoding='utf-8')
    if 'provdrivaren' not in sidan:
        i = sidan.lower().rfind('</body>')
        dist.write_text(sidan[:i] + DRIVARE % (json.dumps(gammal), json.dumps(ny)) + sidan[i:], encoding='utf-8')
    fore_v = kandidater.las_status(slug, 'k01').get('version')
    a = ad.App(ROT, a_.port, data=Path(tempfile.mkdtemp(prefix='nwp-desktop-red-')))
    a.registrera(VERKTYG)
    a.starta()
    lage_js = "(function(){var x=new XMLHttpRequest();x.open('GET','/api/arbetsyta/%s',false);x.send();return JSON.parse(x.responseText)})()" % slug
    try:
        a.vanta(lambda: a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden && !document.getElementById('las-upp').disabled"), text='låsvyn')
        a.js("document.getElementById('las-upp').click(), true")
        a.vanta(lambda: a.js("!!document.querySelector('.pt-primara')"), text='Hem')
        a.js("location.hash = '#/arbetsyta/%s', true" % slug)
        a.vanta(lambda: a.js("!!document.querySelector('[data-material=forhandsvisning]')"), tid=30, text='materialets knappar')
        a.js("document.querySelector('[data-material=forhandsvisning]').click(), true")  # en väntande körning visar först den bevarade bilden
        a.vanta(lambda: a.js("!!(window.__arbetsyta && window.__arbetsyta.forhandsUrsprung)"), tid=40, text='bryggan i förhandsvisningen (redo)')
        ursprung = a.js("window.__arbetsyta.forhandsUrsprung")

        def redigera():
            a.js("document.querySelector('[data-forhandslage=redigera]').click(), true")
            a.vanta(lambda: 'Ändra i källan' in (a.js("(document.getElementById('ay-redigering')||{}).innerText||''") or ''), tid=40, text='bekräftelsen')
            panel = a.js("document.getElementById('ay-redigering').innerText")
            bild1 = a.bild(ut / 'red-1-bekrafta.png').name
            t = time.time()
            a.js("document.querySelector('[data-red-spara]').click(), true")
            slutlage = a.vanta(lambda: (lambda r: r if r and r[-1]['status'] in ('klar', 'aterstalld', 'konflikt', 'fel', 'stoppad', 'nekad') else None)(a.js(lage_js).get('redigeringar')),
                               tid=900, steg=2, text='redigeringens slut')[-1]
            sekunder = round(time.time() - t, 1)
            assert slutlage['status'] == 'klar', slutlage
            kalla = (kandidater.ksajt(slug, 'k01') / slutlage['fil']).read_text(encoding='utf-8')
            visad = urllib.request.urlopen(ursprung + '/', timeout=10).read().decode('utf-8')
            a.vanta(lambda: 'Direktredigering klar' in (a.js("(document.getElementById('ay-redigering')||{}).innerText||''") or ''), tid=30, text='klar i panelen')
            time.sleep(3)
            bild2 = a.bild(ut / 'red-2-klar.png').name
            efter_v = kandidater.las_status(slug, 'k01').get('version')
            assert html.escape(ny, quote=False) in kalla or ny in kalla
            assert ny in html.unescape(visad), 'förhandsvisningen visar den ombyggda sidan'
            assert efter_v != fore_v and kandidater.bevarad(slug, 'k01', fore_v) and kandidater.bevarad(slug, 'k01', efter_v)
            return {'gammal': gammal, 'ny': ny, 'fil': slutlage['fil'], 'panel': ' '.join(panel.split())[:300], 'sekunder_till_klar': sekunder,
                    'version': [fore_v[:12], efter_v[:12]], 'skal': slutlage.get('skal'), 'forhandsvisningen_visar_nya_texten': True, 'bilder': [bild1, bild2]}
        fall('direktredigering i den levande förhandsvisningen: källan, ombygget, versionen', 'U23 E6 D21', redigera)

        if a_.partner:
            def partner():
                a.js("document.querySelector('[data-forhandslage=besok]').click(), true")
                a.js("document.querySelector('#ay-skriv [data-avsikt=fraga]').click(), true")
                a.js("(function(){var t=document.getElementById('ay-text');t.value='Vilka två saker i förslag A skulle du förbättra först, och varför? Svara kort.';"
                     "t.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#ay-skriv [data-skicka=partner]').click();return 1})()")
                t0 = time.time()
                forsta = a.vanta(lambda: a.js("(function(){var e=document.querySelector('#ay-samtal .ay-deltext, #ay-samtal .ay-aktivitet');return e?e.innerText:null})()"),
                                 tid=240, steg=0.2, text='det första delsvaret')
                t_del = round(time.time() - t0, 1)
                bild = a.bild(ut / 'red-3-delsvar.png').name
                delar = []
                for _ in range(6):
                    v = a.js("(function(){var e=document.querySelector('#ay-samtal .ay-deltext');return e?e.innerText.length:null})()")
                    delar.append(v)
                    time.sleep(0.5)
                meddelanden = lambda: a.js("(function(){var x=new XMLHttpRequest();x.open('GET','/api/arbetsyta/%s/partner',false);x.send();"  # noqa: E731
                                           "return JSON.parse(x.responseText).meddelanden||[]})()" % slug)
                svar = a.vanta(lambda: (lambda m: m[-1] if m and m[-1].get('lage') in ('svarat', 'fel', 'avbrutet') else None)(meddelanden()), tid=600, steg=1, text='svaret')
                t_svar = round(time.time() - t0, 1)
                time.sleep(2)
                kvar = a.js("document.querySelectorAll('#ay-samtal .ay-deltext').length")
                assert svar['lage'] == 'svarat', svar.get('fel')
                return {'forsta_delhandelse_s': t_del, 'forsta_delhandelse': ' '.join(str(forsta).split())[:200], 'delsvarets_langd_over_tid': delar,
                        'svar_s': t_svar, 'modell': (svar.get('svar') or {}).get('anvandning', {}).get('modeller'), 'svar': (svar.get('svar') or {}).get('text', '')[:300],
                        'delsvar_kvar_efter_svaret': kvar, 'bild': bild}
            fall('partnerns ström med en riktig modell: delsvar före svaret, svaret ur slutposten', 'U26 E7', partner)

        if a_.genomfor:
            def genomfor():
                a.js("document.querySelector('#ay-skriv [data-avsikt=andring]').click(), true")
                time.sleep(0.5)
                a.js("(function(){var t=document.getElementById('ay-text');t.value='Gör rubriken i första vyn kortare och tydligare. Rör inte bilderna eller färgerna. Formulera en överlämning.';"
                     "t.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#ay-skriv [data-skicka=partner]').click();return 1})()")
                a.vanta(lambda: a.js("!!document.querySelector('[data-genomfor-oppna]')"), tid=600, steg=1, text='överlämningen')
                a.js("document.querySelector('[data-genomfor-oppna]').click(), true")
                falt = a.js("(function(){var r={};document.querySelectorAll('[data-g]').forEach(function(e){r[e.dataset.g]=e.value});return r})()")
                for k, v in (('resultat', 'En kortare och tydligare rubrik i första vyn'), ('omfattning', 'rubriken i första vyn'), ('bevara', 'bilderna och färgerna')):
                    if not (falt.get(k) or '').strip():
                        a.js("(function(){var e=document.querySelector('[data-g=%s]');e.value=%s;e.dispatchEvent(new Event('input',{bubbles:true}));return 1})()" % (k, json.dumps(v)))
                bild1 = a.bild(ut / 'red-4-genomfor.png').name
                a.js("document.querySelector('[data-genomfor]').click(), true")
                besked = a.vanta(lambda: (lambda t: t if t and ('Operations-id' in t or 'Inte' in t or 'nekades' in t) else None)(
                    a.js("(function(){var e=document.querySelector('[data-genomfor-svar], .ay-overlamning [role=status]');return e?e.innerText:null})()")), tid=60, text='beskedet')
                j = a.js(lage_js).get('startjournal') or []
                start = next((x for x in j if x.get('handling') == 'valda'), None)
                stopp = None
                if start:  # arbetet stoppas igen genom Kontroller: provet ska inte låta en hel körning gå
                    a.vanta(lambda: any(h['id'] == 'stoppa' for h in a.js(lage_js).get('handlingar') or []), tid=60, text='Stoppa i Kontroller')
                    stopp = a.js("(function(){var x=new XMLHttpRequest();x.open('POST','/api/flode/%s/start',false);x.setRequestHeader('Content-Type','application/json');"
                                 "x.send(JSON.stringify({handling:'stoppa',start_id:'provstopp-'+Date.now()}));return x.status})()" % slug)
                assert start, ('ingen start i journalen', besked)
                return {'besked': besked, 'start': {k: start.get(k) for k in ('start_id', 'handling', 'status')}, 'stopp_http': stopp, 'bild': bild1}
            fall('Genomför i utkastet ur en riktig överlämning: uppdraget och starten med samma operations-id', 'U16 E5', genomfor)
    finally:
        a.avsluta()
    (ut / 'prov_redigering_app.json').write_text(json.dumps({'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'slug': slug, 'resultat': RESULTAT},
                                                            ensure_ascii=False, indent=1), encoding='utf-8')
    print('%d av %d godkända' % (sum(r['utfall'] == 'godkänt' for r in RESULTAT), len(RESULTAT)))
    return 0 if all(r['utfall'] == 'godkänt' for r in RESULTAT) else 1


if __name__ == '__main__':
    sys.exit(main())
