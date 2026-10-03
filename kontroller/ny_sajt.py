#!/usr/bin/env python3
"""ny_sajt.py — skapar kunder/<slug>/sajt/ ur mall/astro och sätter site till verksamhetens domän.

    .venv/bin/python kontroller/ny_sajt.py <slug> [--doman exempel.se] [--installera]

Domänen tas ur underlag/<slug>/VERKSAMHET.json (webb.doman) om --doman saknas. --installera kör npm install.
Skriver aldrig över en befintlig sajt. Finns för att en kopiering med cp -R mall/astro/. nekas av behörighets-
kontrollen i obevakade körningar.
Exit 0 = skapad; 2 = fel i anropet, eller sajten finns redan.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

ROOT = Path(__file__).resolve().parents[1]
MALL = ROOT / 'mall' / 'astro'


def main(argv=None):
    p = argparse.ArgumentParser(prog='ny_sajt', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--doman')
    p.add_argument('--installera', action='store_true')
    a = p.parse_args(argv)
    krav_slug(a.slug)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug):
        print('slug: a-z, 0-9 och bindestreck', file=sys.stderr)
        return 2
    mal = ROOT / 'kunder' / a.slug / 'sajt'
    krav_vag(mal.parent, 'kundkatalogen')  # en symlänk kunder/<slug> → annan kund skulle annars få kopian (omgång elva, F1)
    krav_vag(mal, 'sajtkatalogen')
    if (mal / 'package.json').exists():
        print('sajten finns redan: %s (skriver inte över)' % mal.relative_to(ROOT), file=sys.stderr)
        return 2
    doman = a.doman
    if not doman:
        try:
            v = json.loads((ROOT / 'underlag' / a.slug / 'VERKSAMHET.json').read_text(encoding='utf-8'))
            doman = (v.get('webb') or {}).get('doman')
        except (OSError, ValueError):
            doman = None
    doman = re.sub(r'^https?://', '', (doman or '')).strip('/') or 'exempel.se'
    mal.parent.mkdir(parents=True, exist_ok=True)
    krav_vag(mal, 'sajtkatalogen')  # efter mkdir: planterade symlänker
    shutil.copytree(MALL, mal, dirs_exist_ok=True, ignore=shutil.ignore_patterns('node_modules', 'dist', '.astro', 'README.md'))
    konfig = mal / 'astro.config.mjs'
    konfig.write_text(konfig.read_text(encoding='utf-8').replace('https://ERSATT-MED-DOMAN.se', 'https://' + doman), encoding='utf-8')
    print('skapad: %s (site https://%s)' % (mal.relative_to(ROOT), doman))
    if a.installera:
        r = subprocess.run(['npm', 'install', '--no-audit', '--no-fund'], cwd=mal, capture_output=True, text=True)
        print(('npm install klar' if r.returncode == 0 else 'npm install misslyckades:\n' + (r.stderr or r.stdout)[-800:]))
        if r.returncode:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
