#!/usr/bin/env python3
"""Stoppvakten (loop 1): en obevakad körning får inte avsluta förrän kontrollerna är gröna, RAPPORT.md finns och den
oberoende granskaren har godkänt sajten.

Gäller bara när NWP_SLUG är satt (kor.sh sätter den). Interaktiva sessioner påverkas inte.
Kör kontroller/prova.py själv och litar inte på en STATUS.json som sessionen kan ha skrivit. När provet är grönt och
rapporten finns kör den kontroller/granska.py, som återanvänder en granskning av exakt samma bygge eller startar en ny
i en egen session. Underkänd granskning blockerar med granskarens kritik.
Exit 0 = får avsluta. Exit 2 = blockerad; skälet går till sessionen på stderr.
Tak: efter NWP_STOPP_TAK blockeringar (standard 8), eller när granskningarna i körningen nått sitt tak
(NWP_GRANSKNING_MAX), släpps avslutet ändå, och kunder/<slug>/prov/STOPPVAKT.json säger det, så att ägaren ser det.
NWP_GRANSKNING=av stänger av granskningen (till exempel i rökprov).
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAK = int(os.environ.get('NWP_STOPP_TAK', '8'))
FRIST = 780  # provet; inställningens timeout är 2700 s
GRANSKNING_FRIST = 1750  # granskningen väntar högst 1700 s; provet och granskningen ryms tillsammans i 2700 s
UTFALL = {0: 'godkänd', 1: 'underkänd', 2: 'kunde inte startas', 3: 'taket för granskningar nått', 4: 'granskaren föll', 5: 'pågår'}


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
    granskning, kritik = None, ''
    if gront and har_rapport:
        if os.environ.get('NWP_GRANSKNING') == 'av':
            granskning = 'avstängd'
        else:
            try:
                g = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'granska.py'), slug, '--vanta', '1700'],
                                   capture_output=True, text=True, timeout=GRANSKNING_FRIST, cwd=str(ROOT))
                grc, kritik = g.returncode, (g.stdout + g.stderr).strip()
            except subprocess.TimeoutExpired:
                grc, kritik = 5, 'granskningen svarade inte inom %d s' % GRANSKNING_FRIST
            granskning = UTFALL.get(grc, 'okänt utfall %d' % grc)
        post['granskning'] = granskning

    if gront and har_rapport and granskning in ('godkänd', 'avstängd'):
        post.update(slapp=True, skal='kontrollerna gröna, RAPPORT.md finns och granskningen är %s' % granskning)
    elif gront and har_rapport and granskning == 'taket för granskningar nått':
        post.update(slapp=True, skal='släppt utan godkänd granskning: taket för granskningar i körningen är nått')
    elif n >= TAK:
        brist = 'röda kontroller' if not gront else ('saknad rapport' if not har_rapport else 'granskning %s' % granskning)
        post.update(slapp=True, skal='stoppvaktens tak nått: avslutet släpptes med %s' % brist)
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
    if granskning == 'underkänd':
        skal.append('Den oberoende granskaren underkände sajten. Rätta varje blockerande fynd, kör '
                    '.venv/bin/python kontroller/prova.py %s, uppdatera RAPPORT.md och försök avsluta igen. Är en '
                    'invändning fel: skriv varför under Granskningen i rapporten. Granskarens kritik:\n\n%s' % (slug, kritik[:9000]))
    elif granskning and granskning not in ('godkänd', 'avstängd'):
        skal.append('Granskningen: %s.\n\n%s\n\nFörsök avsluta igen.' % (granskning, kritik[:3000]))
    skal.append('Stoppvakten, försök %d av %d. Vid försök %d släpps avslutet och ägaren ser varför.' % (n, TAK, TAK))
    print('\n\n'.join(skal), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:  # en krok som dör släpper igenom; den här blockerar och säger varför
        print('stoppvakten föll: %s: %s. Kör .venv/bin/python kontroller/prova.py <slug> och läs felet.' % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)
