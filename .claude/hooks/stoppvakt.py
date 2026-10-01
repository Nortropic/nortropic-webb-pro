#!/usr/bin/env python3
"""Stoppvakten (loop 1): en obevakad körning får inte avsluta förrän kontrollerna är gröna och RAPPORT.md finns.

Gäller bara när NWP_SLUG är satt (kor.sh sätter den). Interaktiva sessioner påverkas inte.
Kör kontroller/prova.py själv och litar inte på en STATUS.json som sessionen kan ha skrivit.
Exit 0 = får avsluta. Exit 2 = blockerad; skälet går till sessionen på stderr.
Tak: efter NWP_STOPP_TAK blockeringar (standard 4) släpps avslutet även med röda kontroller, och
kunder/<slug>/prov/STOPPVAKT.json säger det, så att ägaren ser det.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAK = int(os.environ.get('NWP_STOPP_TAK', '4'))
FRIST = 780  # inställningens timeout är 900 s; provet får inte äta upp den


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    slug = os.environ.get('NWP_SLUG', '')
    if not slug:
        return 0
    if not re.fullmatch(r'[a-z0-9-]{2,60}', slug):
        print('stoppvakten: NWP_SLUG är ogiltig (%r)' % slug, file=sys.stderr)
        return 2
    kund = ROOT / 'kunder' / slug
    prov = kund / 'prov'
    prov.mkdir(parents=True, exist_ok=True)
    raknare = prov / '.stoppvakt-antal'
    try:
        n = int(raknare.read_text().strip()) + 1
    except (OSError, ValueError):
        n = 1
    raknare.write_text(str(n))

    try:
        p = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'prova.py'), slug],
                           capture_output=True, text=True, timeout=FRIST, cwd=str(ROOT))
        rc, ut = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        rc, ut = 124, 'provet tog längre än %d s' % FRIST
    gront = rc == 0
    rapport = kund / 'RAPPORT.md'
    har_rapport = rapport.is_file() and rapport.stat().st_size > 300

    post = {'tid': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'forsok': n, 'tak': TAK,
            'kontroller_grona': gront, 'rapport_finns': har_rapport}
    if gront and har_rapport:
        post.update(slapp=True, skal='kontrollerna gröna och RAPPORT.md finns')
    elif n >= TAK:
        post.update(slapp=True, skal='taket nått: avslutet släpptes med %s' % ('röda kontroller' if not gront else 'saknad rapport'))
    else:
        post.update(slapp=False, skal='blockerad')
    (prov / 'STOPPVAKT.json').write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if post['slapp']:
        return 0

    skal = []
    if not gront:
        skal.append('Kontrollerna är röda. Rätta och försök avsluta igen. Provets sammanfattning '
                    '(hela i kunder/%s/prov/PROV.md):\n\n%s' % (slug, ut.strip()[:6000]))
    if not har_rapport:
        skal.append('kunder/%s/RAPPORT.md saknas eller är nästan tom. Skriv den enligt steg 7 i skillen bygg-sajt.' % slug)
    skal.append('Stoppvakten, försök %d av %d. Vid försök %d släpps avslutet och ägaren ser att det var rött.' % (n, TAK, TAK))
    print('\n\n'.join(skal), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:  # en krok som dör släpper igenom; den här blockerar och säger varför
        print('stoppvakten föll: %s: %s. Kör .venv/bin/python kontroller/prova.py <slug> och läs felet.' % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)
