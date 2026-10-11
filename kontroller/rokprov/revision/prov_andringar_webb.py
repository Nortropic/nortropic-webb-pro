#!/usr/bin/env python3
"""Ändringsflikens webbläsarprov (kunskap/andringar.md, Proven): den riktiga dashboardservern i en isolerad rot med
provprojektet (andringar_fixtur.py) och provagenten i claudes ställe, och prov_andringar_webb.mjs som klickar och skriver
i fliken i Chromium (xterm.js, svenska tecken, inklistring, storlek, Ctrl+C, omladdning, en andra vy, bilagor, stopp).
Med NWP_ANDRINGAR_VERKLIGT=1 körs i stället en riktig Claude Code-session (litet modellprov, manuellt; aldrig i rökprovet):
då skrivs uppdragen i terminalen på riktigt och arbetskopian ändras.

    .venv/bin/python -B kontroller/rokprov/revision/prov_andringar_webb.py [--bevis <katalog>]
"""
import argparse
import contextlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as dash  # noqa: E402
import andringar  # noqa: E402
import andringsflik  # noqa: E402
import andringar_fixtur  # noqa: E402
import atelje  # noqa: E402
import exportera  # noqa: E402
import korregister  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FEJK = ROOT / 'kontroller' / 'rokprov' / 'andringar' / 'fejkclaude.py'


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('--bevis', default=None, help='katalog för vyernas skärmbilder')
    x = a.parse_args(argv)
    verkligt = os.environ.get('NWP_ANDRINGAR_VERKLIGT') == '1'
    with contextlib.ExitStack() as st:
        rot = Path(st.enter_context(korregister.egen_tmp_med('nwp-andringar-', 'ändringsflikens webbläsarprov'))).resolve()
        for m in (atelje, exportera, dash):
            st.enter_context(patch.multiple(m, ROOT=rot, UNDERLAG=rot / 'underlag', KUNDER=rot / 'kunder'))
        if not verkligt:
            st.enter_context(patch.dict(os.environ, {'NWP_ANDRINGAR_PROVAGENT': str(FEJK)}))
        andringar_fixtur.bygg(rot, med_sajt=verkligt and (andringar_fixtur.MALLSAJT / 'node_modules').is_dir())
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        st.callback(srv.server_close)
        st.callback(srv.shutdown)
        host = '127.0.0.1:%d' % srv.server_port
        st.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        st.enter_context(patch.dict(dash.NYCKEL, {'varde': 'provnyckel-andringar'}))
        st.callback(andringsflik.stang_alla)
        slug, slug2 = andringar_fixtur.WEBBPLATSER[0][0], andringar_fixtur.WEBBPLATSER[1][0]
        r = subprocess.run(['node', str(Path(__file__).with_suffix('.mjs')), 'http://' + host, 'provnyckel-andringar', slug, slug2,
                            '1' if verkligt else '0', x.bevis or '', str(rot)], cwd=str(ROOT), timeout=3600)
        logg = (andringar.privat(slug) / 'LOGG.jsonl')
        handelser = [json.loads(z)['handelse'] for z in logg.read_text(encoding='utf-8').splitlines()] if logg.is_file() else []
        print(json.dumps({'webblasarprov_slutkod': r.returncode, 'handelser': handelser}, ensure_ascii=False))
        if r.returncode:
            return r.returncode
        if verkligt:
            # uppdraget är gjort först när ändringen är committad genom commitvägen och redovisad, och kunskapen skriven
            repo = rot / 'kunder' / slug / 'kundrepo'
            git = lambda *a: subprocess.run(['git', '-c', 'core.fsmonitor=false', *a], cwd=str(repo), capture_output=True, text=True).stdout  # noqa: E731
            logg_ = git('log', '--format=%h %s', '-5')
            print(logg_)
            print('status:', git('status', '--short') or '(ren)')
            d = andringar.privat(slug)
            for namn in ('KUNSKAP.md', 'ANDRINGAR.md'):
                print('%s:' % namn, (d / namn).stat().st_size if (d / namn).is_file() else 'saknas', 'byte')
            k = andringar.senaste_kontroll(slug) or {}
            trad = git('rev-parse', 'HEAD^{tree}').strip()
            print('kontrollen för HEAD:s träd:', bool(k.get('ok') and k.get('tillstand') == trad))
            for _ in range(40):  # kvitteringen efter turens slut går i en egen tråd
                kvitton = sorted((rot / 'kunder' / slug / 'exporter').glob('*-andring/EXPORT.json'))
                if kvitton:
                    break
                time.sleep(0.5)
            print('kvitton:', [p.parent.name for p in kvitton])
            # den nya sessionen (acceptansprov 7–8): ändringen efter den externa strukturcommiten ligger i komponenten, sidan
            # fick ingen ny rad med tiderna, och kunskapen nämner den nya källan
            efter = git('log', '--format=%h %s', '--grep', '^Struktur: ', '-1').strip()
            nya = git('diff', '--name-only', git('rev-list', '--max-parents=0', 'HEAD').split()[0], 'HEAD').split()
            sista = git('log', '--format=%h', '--grep', '^Ändring: ', '-1').strip()
            komp = (repo / 'src' / 'components' / 'Oppettider.astro')
            sidan = (repo / 'src' / 'pages' / 'index.astro').read_text(encoding='utf-8')
            kunskap = (d / 'KUNSKAP.md').read_text(encoding='utf-8') if (d / 'KUNSKAP.md').is_file() else ''
            print('strukturcommit:', efter, '| senaste ändring:', sista, '| ändrade filer:', git('show', '--name-only', '--format=', sista).split())
            brister = [b for b, ok in (('ingen commit "Ändring: …"', any(z.split(' ', 1)[1].startswith('Ändring: ') for z in logg_.splitlines() if ' ' in z)),
                                       ('KUNSKAP.md saknas', bool(kunskap)), ('ANDRINGAR.md saknas', (d / 'ANDRINGAR.md').is_file()),
                                       ('komponenten har inte 08–16', komp.is_file() and '08–16' in komp.read_text(encoding='utf-8')),
                                       ('startsidan fick tiderna igen', '08–16' not in sidan and '07–16' not in sidan),
                                       ('kunskapen nämner inte komponenten', 'Oppettider' in kunskap),
                                       ('ingen ny bild sedan exporten', any(Path(f).suffix.lower() in ('.png', '.webp', '.jpg', '.jpeg', '.avif') for f in nya))) if not ok]
            if brister:
                print('FEL: %s' % '; '.join(brister), file=sys.stderr)
                return 1
        for krav in ('start', 'stopp', 'slut'):
            if krav not in handelser:
                print('FEL: loggen saknar %s' % krav, file=sys.stderr)
                return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
