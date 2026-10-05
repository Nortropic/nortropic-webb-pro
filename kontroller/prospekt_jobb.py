#!/usr/bin/env python3
"""prospekt_jobb.py — dashboardens körare för prospektpipelinen: svep → sajter → analysera i följd, löst kopplad från
servern. Skriver underlag/prospekt/<kampanj>/JOBB.json {pid, steg, start, rc, slut, fel} som dashboarden läser, och
loggar varje stegs utdata i <kampanj>/jobb-<stamp>.log. Stannar vid första steg som inte ger 0.

    .venv/bin/python kontroller/prospekt_jobb.py kampanj <id> --kommun 2580 --bransch hantverkare [--max 10]
    .venv/bin/python kontroller/prospekt_jobb.py analysera <id> [--max 10]

Exit: pipelinens sista exitkod (0 ok · 2 fel i anropet · 3 nyckel saknas · 4 yttre fel).
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import inte_i_bygge  # noqa: E402  (revisionen 2026-10-03, F1: körs aldrig inne i ett bygge)
import nastlad  # noqa: E402  (nästlade sessioner: inget automatiskt minne)
import prospektfiler as pf  # noqa: E402

ROOT = pf.ROOT
PROSPEKT = ROOT / 'kontroller' / 'prospekt.py'


def ren_miljo():
    return nastlad.miljo(behall=lambda k: k.startswith('NWP_PROSPEKT_'))


def main(argv=None):
    p = argparse.ArgumentParser(prog='prospekt_jobb', description=__doc__.split('\n\n')[0])
    p.add_argument('lage', choices=('kampanj', 'analysera'))
    p.add_argument('kampanj')
    p.add_argument('--kommun')
    p.add_argument('--bransch')
    p.add_argument('--max', type=int, default=10)
    p.add_argument('--sajter-max', type=int, default=40)
    a = p.parse_args(argv)
    inte_i_bygge('prospekt_jobb.py')
    kdir = pf.kampanjkatalog(a.kampanj)
    kdir.mkdir(parents=True, exist_ok=True)
    if a.lage == 'kampanj' and not (a.kommun and a.bransch):
        print('kampanj kräver --kommun och --bransch', file=sys.stderr)
        return 2
    steg = []
    if a.lage == 'kampanj':
        steg.append(('svep', ['svep', '--kampanj', a.kampanj, '--kommun', a.kommun, '--bransch', a.bransch]))
    steg.append(('sajter', ['sajter', '--kampanj', a.kampanj, '--max', str(a.sajter_max)]))
    steg.append(('analysera', ['analysera', '--kampanj', a.kampanj, '--max', str(a.max)]))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    logg = kdir / ('jobb-%s.log' % stamp)
    jobb = {'pid': os.getpid(), 'lage': a.lage, 'steg': None, 'start': pf.nu(), 'rc': {}, 'slut': None, 'fel': None, 'logg': str(logg.relative_to(ROOT))}
    pf.skriv_json(kdir / 'JOBB.json', jobb)
    rc = 0
    with open(logg, 'ab') as ut:
        for namn, args in steg:
            jobb['steg'] = namn
            pf.skriv_json(kdir / 'JOBB.json', jobb)
            ut.write(('\n=== %s %s ===\n' % (pf.nu(), ' '.join(args))).encode())
            ut.flush()
            r = subprocess.run([sys.executable, '-B', str(PROSPEKT), *args], cwd=str(ROOT), env=ren_miljo(), stdout=ut, stderr=subprocess.STDOUT)
            rc = r.returncode
            jobb['rc'][namn] = rc
            if rc != 0:
                jobb['fel'] = {2: 'fel i anropet eller en körning pågår redan', 3: 'SCB-nyckel saknas eller är ogiltig', 4: 'yttre fel eller dagsbudgeten slut'}.get(rc, 'rc %d' % rc) + ' i steget %s' % namn
                break
    jobb['steg'] = None
    jobb['slut'] = pf.nu()
    pf.skriv_json(kdir / 'JOBB.json', jobb)
    return rc


if __name__ == '__main__':
    sys.exit(main())
