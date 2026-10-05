#!/usr/bin/env python3
"""uxsok.py — UI UX Pro Max sökning och designsystem för flödets sessioner, läsande: skillens search.py med bara de
flaggor som läser (fråga, domän, stack, antal, format och designsystemets reglage), aldrig --persist, --output-dir,
--page eller --force, som skriver filer var som helst (granskning 4, G12: mönstret `search.py *` vidgade skrivgränsen).

    .venv/bin/python -B kontroller/uxsok.py "<fråga>" [--design-system] [--domain style|color|typography|ux|landing …]
        [--stack astro] [-n 1–20] [--json] [--full] [--format ascii|markdown] [--variance|--motion|--density 1–10]
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOK = ROOT / '.claude' / 'skills' / 'ui-ux-pro-max' / 'scripts' / 'search.py'


def main(argv=None):
    p = argparse.ArgumentParser(prog='uxsok', description=__doc__.split('\n\n')[0], allow_abbrev=False)
    p.add_argument('fraga')
    p.add_argument('--domain', '-d')
    p.add_argument('--stack', '-s')
    p.add_argument('--max-results', '-n', type=int, choices=range(1, 21))
    p.add_argument('--json', action='store_true')
    p.add_argument('--full', action='store_true')
    p.add_argument('--design-system', '-ds', action='store_true')
    p.add_argument('--format', '-f', choices=['ascii', 'markdown'])
    for reglage in ('--variance', '--motion', '--density'):
        p.add_argument(reglage, type=int, choices=range(1, 11))
    a = p.parse_args(argv)
    if not SOK.is_file():
        print('UI UX Pro Max saknas (%s)' % SOK.relative_to(ROOT), file=sys.stderr)
        return 3
    args = [sys.executable, '-B', str(SOK), a.fraga]
    for flagga, varde in (('--domain', a.domain), ('--stack', a.stack), ('--max-results', a.max_results), ('--format', a.format),
                          ('--variance', a.variance), ('--motion', a.motion), ('--density', a.density)):
        if varde is not None:
            args += [flagga, str(varde)]
    args += [f for f, pa in (('--json', a.json), ('--full', a.full), ('--design-system', a.design_system)) if pa]
    r = subprocess.run(args, cwd=str(SOK.parent), capture_output=True, text=True, timeout=120)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr[-2000:])
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
