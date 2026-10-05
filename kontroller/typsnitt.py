#!/usr/bin/env python3
"""typsnitt.py — skapandeflödets enda väg att installera paket: typsnitt ur Fontsource till kunder/<slug>/sajt.

    .venv/bin/python kontroller/typsnitt.py <slug> @fontsource/<namn> [@fontsource-variable/<namn> …]

Omgranskningen av skapandeflödet (fynd 8): tillåtelsen `npm install --prefix … @fontsource*` släppte igenom paket i
andra former (`@fontsource/x@npm:<paket>`, `@fontsource/x@git+https://…`, `@fontsource/x@file:../..`, ett extra
`ägare/repo`), och deras installationsskript kördes utanför sandlådan. Här prövas varje namn mot exakt formen
@fontsource[-variable]/<namn> med en valfri exakt version, och npm körs med --ignore-scripts: inget paket kör kod vid
installationen. Typsnittspaketen är CSS och typsnittsfiler.
Exit 0 = installerat; 2 = fel i anropet (inget installerat); annat = npm:s slutkod.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
PAKET = re.compile(r'^@fontsource(?:-variable)?/[a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?(?:@\d{1,3}\.\d{1,3}\.\d{1,3})?$')
MAX_PAKET = 6


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or not SLUG.match(argv[0]):
        print(__doc__.split('\n\n')[1].strip(), file=sys.stderr)
        return 2
    slug, paket = argv[0], argv[1:]
    fel = [p for p in paket if not PAKET.match(p)]
    if fel or len(paket) > MAX_PAKET or len(set(paket)) != len(paket):
        print('bara @fontsource/<namn> eller @fontsource-variable/<namn> (valfritt @x.y.z), högst %d, inga andra argument: %s'
              % (MAX_PAKET, ', '.join(fel) or 'för många eller dubbla'), file=sys.stderr)
        return 2
    krav_slug(slug)
    sajt = ROOT / 'kunder' / slug / 'sajt'
    krav_vag(sajt, 'sajtkatalogen')
    if not (sajt / 'package.json').is_file():
        print('kunder/%s/sajt saknas' % slug, file=sys.stderr)
        return 2
    p = subprocess.run(['npm', 'install', '--prefix', str(sajt), '--ignore-scripts', '--no-audit', '--no-fund', '--save', *paket],
                       cwd=str(ROOT), stdin=subprocess.DEVNULL, timeout=600)
    return p.returncode


if __name__ == '__main__':
    sys.exit(main())
