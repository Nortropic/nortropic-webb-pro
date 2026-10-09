#!/usr/bin/env python3
"""Leveransvägen till Cloudflare Workers med rökprovets mallsajt, utan konto och utan nät utåt: exporten byggs och
förpackas som vid en leverans (exportera.verifiera_bygge: npm ci, astro build innanför processgränsen, dist/ utan privata
filer, wrangler deploy --dry-run), och den exporterade Workern körs sedan i workerd med lokal D1 och R2
(kontroller/workersprov.py). En fiktiv verksamhet i en egen tempkatalog; repots kunder/ och underlag/ rörs inte.

Normalvägen utan Vercel (M14): Vercels miljövariabler tas bort, och en fälla som heter vercel ligger först i PATH och
loggar varje anrop; provet är rött om något i vägen anropar den.

    .venv/bin/python -B kontroller/rokprov/revision/prov_workers.py [sajt]
"""
import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exportera  # noqa: E402
import korregister  # noqa: E402
import workersprov  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def main(argv):
    sajt = Path(argv[0]) if argv else ROOT / 'kunder' / 'rokprov-mall' / 'sajt'
    tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'leveransvägens prov')).resolve()
    falla = tmp / 'falla'; falla.mkdir()
    (falla / 'vercel').write_text('#!/bin/sh\necho "$@" >> "%s/vercel-anrop.log"\nexit 1\n' % tmp); (falla / 'vercel').chmod(0o700)
    for k in [k for k in os.environ if k.startswith('VERCEL')]:
        del os.environ[k]
    os.environ['PATH'] = str(falla) + os.pathsep + os.environ.get('PATH', '')
    try:
        mal = tmp / 'kunder' / 'workersprov' / 'sajt'
        shutil.copytree(sajt, mal, ignore=shutil.ignore_patterns('node_modules', 'dist', '.astro', '.wrangler'))
        (tmp / 'underlag' / 'workersprov').mkdir(parents=True)
        (tmp / 'underlag' / 'workersprov' / 'VERKSAMHET.json').write_text(json.dumps(
            {'schema': 1, 'namn': 'Workersprovet (fiktiv)', 'fiktiv': True, 'tjanster': ['Prov'], 'kontaktvagar': []}))
        with patch.multiple(exportera, ROOT=tmp, KUNDER=tmp / 'kunder', UNDERLAG=tmp / 'underlag'):
            res = exportera.exportera('workersprov', bygg=True)  # till kundens kundrepo i tempkatalogen
        if not res.get('ok'):
            print('FEL exporten och bygget: %s' % json.dumps(res, ensure_ascii=False, default=str)[-1500:])
            return 1
        print('ok exporten byggd och förpackad för Workers (dry-run)')
        ut = workersprov.prova(Path(res['ut']))
        for k, (ok, detalj) in ut.items():
            print('%s %s%s' % ('ok ' if ok else 'FEL', k, '' if ok else ': ' + detalj))
        anrop = tmp / 'vercel-anrop.log'
        print('%s normalvägen anropar inte Vercel%s' % ('ok ' if not anrop.exists() else 'FEL', '' if not anrop.exists() else ': ' + anrop.read_text()[:200]))
        return 0 if ut and all(ok for ok, _ in ut.values()) and not anrop.exists() else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
