#!/usr/bin/env python3
"""Repoväljarens webbläsarprov (kunskap/andringar.md, Repoväljaren): den riktiga dashboardservern i en isolerad rot med
repovaljare_fixtur.py (provets gh, lokala nakna repon som organisationens GitHub) och provagenten i claudes ställe, och
prov_repovaljaren_webb.mjs som öppnar väljaren med knappen och ⌘O, filtrerar med tangentbordet, klonar, kopplar, byter
repo under en levande agent (låter den arbeta, och stoppar den), läser om med utgången inloggning och hämtar och
uppdaterar i Ändringar. Sedan startas en ny serverinstans, och Senast öppnade ska stå kvar.

    .venv/bin/python -B kontroller/rokprov/revision/prov_repovaljaren_webb.py [--bevis <katalog>]
"""
import argparse
import contextlib
import importlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as dash  # noqa: E402
import andringsflik  # noqa: E402
import atelje  # noqa: E402
import exportera  # noqa: E402
import korregister  # noqa: E402
import kundrepo  # noqa: E402
import repovaljare  # noqa: E402
import repovaljare_fixtur as fixtur  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FEJK = ROOT / 'kontroller' / 'rokprov' / 'andringar' / 'fejkclaude.py'
NYCKEL = 'provnyckel-repovaljaren'


def serva(st):
    srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    host = '127.0.0.1:%d' % srv.server_port
    st.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
    return srv, 'http://' + host


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('--bevis', default=None, help='katalog för vyernas skärmbilder')
    x = a.parse_args(argv)
    with contextlib.ExitStack() as st:
        rot = Path(st.enter_context(korregister.egen_tmp_med('nwp-repovaljaren-', 'repoväljarens webbläsarprov'))).resolve()
        for m in (atelje, exportera, dash):
            st.enter_context(patch.multiple(m, ROOT=rot, UNDERLAG=rot / 'underlag', KUNDER=rot / 'kunder'))
        st.enter_context(patch.dict(os.environ, dict(fixtur.bygg(rot), NWP_ANDRINGAR_PROVAGENT=str(FEJK))))
        st.enter_context(patch.dict(dash.NYCKEL, {'varde': NYCKEL}))
        repovaljare.CACHE.update(tid=0.0, svar=None)
        st.callback(andringsflik.stang_alla)
        # två commits på fjärren från "en annan dator": alfa ligger efter först när Hämta har körts
        for t in ('Ändring från en annan dator', 'En till från samma dator'):
            fixtur.ny_commit_pa_fjarren(rot, 'kund-alfa', t)
        srv, url = serva(st)
        mjs = str(Path(__file__).with_suffix('.mjs'))
        r = subprocess.run(['node', mjs, 'del1', url, NYCKEL, str(rot), x.bevis or ''], cwd=str(ROOT), timeout=900)
        srv.shutdown()
        srv.server_close()
        if r.returncode:
            return r.returncode
        # agentprocessen som stoppades i väljaren finns inte kvar (verklig processkontroll), och ingen andra startades
        handelser = [json.loads(z) for z in (rot / 'underlag' / 'alfa' / 'andringar' / 'LOGG.jsonl').read_text(encoding='utf-8').splitlines()]
        starter = [h for h in handelser if h['handelse'] == 'start']
        if len(starter) != 1:
            print('FEL: väntade en agentstart för alfa, fick %d' % len(starter), file=sys.stderr)
            return 1
        try:
            os.kill(starter[0]['pid'], 0)
            print('FEL: alfas agentprocess %s lever efter stoppet' % starter[0]['pid'], file=sys.stderr)
            return 1
        except ProcessLookupError:
            pass
        for slug in ('beta', 'gamma'):
            if not kundrepo.ar_repo(kundrepo.repo(slug)) or not kundrepo.las_kvitto(slug):
                print('FEL: %s klonades inte till sin plats med kvitto' % slug, file=sys.stderr)
                return 1
        # en ny serverinstans med modulerna lästa på nytt (inget i minnet): Senast öppnade står kvar
        andringsflik.stang_alla()
        andringsflik.SESSIONER.clear()
        importlib.reload(repovaljare)
        srv2, url2 = serva(st)
        st.callback(srv2.server_close)
        st.callback(srv2.shutdown)
        r = subprocess.run(['node', mjs, 'del2', url2, NYCKEL, str(rot), x.bevis or ''], cwd=str(ROOT), timeout=300)
        print(json.dumps({'webblasarprov_slutkod': r.returncode, 'senast': [z['repo'] for z in repovaljare.senast()]}, ensure_ascii=False))
        return r.returncode


if __name__ == '__main__':
    sys.exit(main())
