#!/usr/bin/env python3
"""Leveransvägen till Cloudflare Workers med rökprovets mallsajt, utan konto och utan nät utåt: exporten byggs och
förpackas som vid en leverans (exportera.verifiera_bygge: npm ci, astro build innanför processgränsen, dist/ utan privata
filer, wrangler deploy --dry-run), och den exporterade Workern körs sedan i workerd med lokal D1 och R2
(kontroller/workersprov.py). En fiktiv verksamhet i en egen tempkatalog; repots kunder/ och underlag/ rörs inte.

    .venv/bin/python -B kontroller/rokprov/revision/prov_workers.py [sajt]
"""
import json
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
        return 0 if ut and all(ok for ok, _ in ut.values()) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
