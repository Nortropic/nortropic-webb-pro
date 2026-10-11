#!/usr/bin/env python3
"""Kompetenskartans webbläsarprov (kontroller/kompetenskarta.py, dashboard/kompetenskarta.js): den riktiga
dashboardservern med en isolerad underlagskatalog med syntetiska kompetenskvitton (som i prov_kompetenskarta.py), och
prov_kompetenskarta_webb.mjs som öppnar Systemförbättring, Kompetenskartan, byter flik med tangentbordet och prövar
varje flik med axe och spill i 390 och 1440 px.

    .venv/bin/python -B kontroller/rokprov/revision/prov_kompetenskarta_webb.py [--bevis <katalog>]
"""
import argparse
import contextlib
import json
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as dash  # noqa: E402
import korregister  # noqa: E402
import prov_kompetenskarta as prov  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('--bevis', default=None)
    x = a.parse_args(argv)
    with contextlib.ExitStack() as st:
        rot = Path(st.enter_context(korregister.egen_tmp_med('nwp-kompetenskarta-', 'kompetenskartans webbläsarprov'))).resolve()
        u = rot / 'underlag'
        for rel, data in (('kund-a/atelje/kandidater/k01/STATUS.json', {'kompetens': {'rorelse': {'pass': 'rorelse', 'kvitto': prov.kvitto('rorelse', lasta_hela=False)}}}),
                          ('kund-a/atelje/FORSKNING.json', {'kompetens': prov.kvitto('forska', mcp={'mcp__mobbin__search_screens': 2})})):
            (u / rel).parent.mkdir(parents=True, exist_ok=True)
            (u / rel).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        (rot / 'kunder').mkdir()
        st.enter_context(patch.multiple(dash, UNDERLAG=u, KUNDER=rot / 'kunder'))
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        st.callback(srv.server_close)
        st.callback(srv.shutdown)
        host = '127.0.0.1:%d' % srv.server_port
        st.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        st.enter_context(patch.dict(dash.NYCKEL, {'varde': 'provnyckel-kompetenskarta'}))
        r = subprocess.run(['node', str(Path(__file__).with_suffix('.mjs')), 'http://' + host, 'provnyckel-kompetenskarta', x.bevis or ''], cwd=str(ROOT), timeout=600)
        return r.returncode


if __name__ == '__main__':
    sys.exit(main())
