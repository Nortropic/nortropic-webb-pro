#!/usr/bin/env python3
"""Appens bildserie (E10): riktiga bilder av provbyggda Nortropic.app i riktig WKWebView mot en provinstans, en per panel
och läge, med metadata (appbygge, motorns commit, macOS, fönstrets storlek och pixeltäthet) bredvid varje bild.

    .venv/bin/python -B desktop/prov/bildserie.py --port 4791 --ut <katalog> [--stoppbar-motor]

--stoppbar-motor: provinstansen får stoppas på slutet för bilden av den frånkopplade motorn med senast kända läge
(provet startar den inte igen). Inget riktigt kundmaterial, ingen modell.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appdrivare as ad  # noqa: E402
from prov_app import VERKTYG, bild  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--ut', required=True)
    ap.add_argument('--stoppbar-motor', action='store_true')
    a_ = ap.parse_args()
    if a_.port == 4771:
        raise SystemExit('bildserien körs mot en provinstans, aldrig mot :4771')
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    motor = json.loads(subprocess.run(['/usr/bin/curl', '-s', 'http://127.0.0.1:%d/api/desktop/identitet?utmaning=%s' % (a_.port, 'ab' * 16)],
                                      capture_output=True, text=True).stdout or '{}').get('version', {})
    ov = json.loads(subprocess.run(['/usr/bin/curl', '-s', 'http://127.0.0.1:%d/api/desktop/oversikt' % a_.port], capture_output=True, text=True).stdout)
    test = next((k for k in ov['kunder'] if k['test'] and k['arenden']), None)
    flode = next((k for k in ov['kunder'] if k['projekt']), None)
    bilder = []
    a = ad.App(ad.ROT, a_.port)
    a.registrera(VERKTYG)
    a.starta()

    def ta(namn, hash_=None, vanta=None, vila=1.2):
        if hash_ is not None:
            a.js('location.hash=%s, true' % json.dumps(hash_))
        if vanta:
            a.vanta(lambda: a.js(vanta), text=namn)
        time.sleep(vila)
        bilder.append(bild(a, ut, namn, motor))

    try:
        a.vanta(lambda: a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
        ta('p01-last', vila=0.8)
        a.js("document.getElementById('las-upp').click(), true")
        a.vanta(lambda: a.js("!!document.querySelector('.pt-primara')"), text='Hem')
        ta('p02-hem')
        ta('kundlista', '#/kunder', "document.querySelector('#vy h1')?.textContent==='Kunder'")
        ta('testkundslista', '#/testkunder', "document.querySelector('#vy h1')?.textContent==='Testkunder'")
        ta('p03-ny-kund', '#/ny-kund', "!!document.getElementById('pt-form')")
        if test:
            eid = test['arenden'][0]['id']
            ta('p04-intervju', '#/intervju/' + eid, "!!document.getElementById('pt-svar-form')")
            ta('p05-funktioner', '#/kundstart/' + eid, "[...document.querySelectorAll('#vy h2')].some(h=>h.textContent.includes('Funktioner'))", vila=1.5)
            a.js("[...document.querySelectorAll('#vy h2')].find(h=>h.textContent.includes('Funktioner'))?.scrollIntoView(), true")
            ta('p05-funktioner-katalogen', vila=0.8)
        if flode:
            s = flode['slug']
            ta('p06-forslag', '#/arbetsyta/%s/forslag' % s, "!!document.querySelector('#vy h1, .ay-forslagen h1, #vy')", vila=3)
            ta('p07-forfining-kommentarer', '#/granska/' + s, "!!document.querySelector('#vy h1')", vila=2)
            ta('p07-arbetsyta', '#/arbetsyta/' + s, "!!document.querySelector('.ay-huvud')", vila=3)
            ta('p08-byggflode', '#/arbetsyta/%s/flode' % s, "!!document.getElementById('ay-flode')", vila=3)
            ta('p09-kod-och-preview', '#/arbetsyta/%s/kod' % s, "!!document.querySelector('.ay')", vila=3)
            ta('p10-p11-leverans', '#/leverans-kund/' + s, "!!document.getElementById('publicering')", vila=1.5)
            a.js("document.getElementById('forvaltning')?.scrollIntoView(), true")
            ta('p12-forvaltning', vila=0.8)
        a.fonster(bredd=820, hojd=900)
        ta('smal-vy-hem', '#/start', "!!document.querySelector('.pt-primara')", vila=1.5)
        if test:
            ta('smal-vy-intervju', '#/intervju/' + test['arenden'][0]['id'], "!!document.getElementById('pt-svar-form')", vila=1.5)
        a.fonster(bredd=1440, hojd=900)
        a.meny('diagnos')
        a.vanta(lambda: a.js("!!document.querySelector('[data-vy=diagnos]') && !document.querySelector('[data-vy=diagnos]').hidden"), text='diagnosen')
        ta('diagnos-och-installningar', vila=1)
        if a_.stoppbar_motor:
            pid = int(subprocess.run(['/usr/sbin/lsof', '-nP', '-iTCP@127.0.0.1:%d' % a_.port, '-sTCP:LISTEN', '-t'], capture_output=True, text=True).stdout.split()[0])
            os.kill(pid, signal.SIGTERM)
            a.vanta(lambda: 'franKopplad' in (a.lage().get('url') or '') or a.js("!!document.querySelector('[data-vy=motor]') && !document.querySelector('[data-vy=motor]').hidden"), tid=60, text='frånkopplad')
            ta('motorn-stoppad-senast-kanda', vila=2)
    finally:
        a.avsluta()
    # första starten: en tom datakatalog
    f = ad.App(ad.ROT, a_.port)
    f.starta()
    try:
        f.vanta(lambda: f.js("document.querySelector('[data-vy=forsta]') && !document.querySelector('[data-vy=forsta]').hidden"), text='första starten')
        time.sleep(0.8)
        bilder.append(bild(f, ut, 'forsta-start', motor))
    finally:
        f.avsluta()
    (ut / 'bildserie.json').write_text(json.dumps({'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'motor': motor, 'bilder': bilder}, ensure_ascii=False, indent=1))
    print(json.dumps({'bilder': bilder}, ensure_ascii=False))


if __name__ == '__main__':
    main()
