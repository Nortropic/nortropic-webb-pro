#!/usr/bin/env python3
"""ta_bort.py — tar bort filer eller mappar, men bara inne i ett byggs egna mappar.

    .venv/bin/python kontroller/ta_bort.py <slug> <sökväg> [<sökväg> ...]

Tillåtet: kunder/<slug>/… och underlag/<slug>/… (efter att sökvägen lösts upp, så ../ hjälper inte). Allt annat
vägras. Finns för att rm är spärrat i obevakade körningar.
Exit 0 = borttaget; 2 = vägrat eller fel i anropet.
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2 or not re.fullmatch(r'[a-z0-9-]{2,60}', argv[0]):
        print('användning: ta_bort.py <slug> <sökväg> [...]', file=sys.stderr)
        return 2
    slug, vagar = argv[0], argv[1:]
    tillatna = [(ROOT / 'kunder' / slug).resolve(), (ROOT / 'underlag' / slug).resolve()]
    for v in vagar:
        p = (ROOT / v).resolve() if not Path(v).is_absolute() else Path(v).resolve()
        if not any(p != t and p.is_relative_to(t) for t in tillatna):
            print('vägrar: %s ligger inte i kunder/%s/ eller underlag/%s/' % (v, slug, slug), file=sys.stderr)
            return 2
        if not p.exists():
            print('finns inte: %s' % v)
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
        print('borttagen: %s' % p.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
