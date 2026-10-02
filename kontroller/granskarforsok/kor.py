"""Kör granskarförsökets granskningar: arm A (dagens text) sex gånger, arm persona och arm c tre gånger var, per bygge.

Varje granskning är granska.arbetare i byggets isolerade kopia, med armens granskartext, utan originalitetsdomaren
och med läsning nekad i de riktiga repona, minnet och arkivet. Redan klara granskningar hoppas över (återupptagbart).
"""
import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HEM = str(Path.home())
REPOS = str(Path(__file__).resolve().parents[3])  # mappen med repona: granskaren och domaren får inte läsa där
G = Path(os.environ.get('NWP_FORSOK') or '/tmp/nwp-granskarforsok')  # utdata, utanför repot
KOD = Path(__file__).resolve().parent
PY = str(Path(__file__).resolve().parents[2] / '.venv' / 'bin' / 'python')
BYGGEN = ['lulea-snickaren', 'sundboms-el', 'paint-it-black-maleri']
# kor.py [parallellt] [arm=antal ...]: A är dagens kritik/GRANSKARE.md, övriga armar kritik/GRANSKARE-<arm>.md
PARALLELLT = int(sys.argv[1]) if len(sys.argv) > 1 else 4
ARMAR = {a: int(n) for a, n in (x.split('=') for x in sys.argv[2:])} or {'A': 6, 'persona': 3, 'c': 3}

KORNING = r'''
import json, sys
from pathlib import Path
rot, slug, arm, namn, repos, hem = sys.argv[1:7]
sys.path.insert(0, rot + '/kontroller')
import granska as g, prova
g.INSTRUKTION = 'kritik/GRANSKARE.md' if arm == 'A' else 'kritik/GRANSKARE-%s.md' % arm
g.NEKAS = g.NEKAS + ['Read(/' + repos + '/**)', 'Read(/' + hem + '/.claude/**)']
kund = Path(rot) / 'kunder' / slug
rdir = kund / 'ab-granskare' / namn
rdir.mkdir(parents=True, exist_ok=True)
upp = {'slug': slug, 'runda': 0, 'korning': 'ab-granskare', 'tid': g.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'),
       'modell': 'opus[1m]', 'effort': 'high', 'frist': 1800, 'originalitet': 'av', 'granskare': 1}
(rdir / 'UPPDRAG.json').write_text(json.dumps(upp))
(rdir / 'PAGAR').write_text('')
g.arbetare(str(rdir))
'''


def logg(text):
    with open(G / 'logg.txt', 'a') as f:
        f.write('%s %s\n' % (time.strftime('%H:%M:%S', time.gmtime()), text))


def jobb(slug, arm, n):
    rot = G / slug / 'rot'
    namn = '%s-%d' % (arm, n)
    rdir = rot / 'kunder' / slug / 'ab-granskare' / namn
    if (rdir / 'GRANSKNING.json').is_file():
        return
    (rdir / 'FEL.txt').unlink(missing_ok=True)
    start = time.time()
    logg('start %s %s' % (slug, namn))
    r = subprocess.run([PY, '-B', '-c', KORNING, str(rot), slug, arm, namn, REPOS, HEM], cwd=str(rot), capture_output=True, text=True)
    status = 'klar' if (rdir / 'GRANSKNING.json').is_file() else 'FEL ' + ((rdir / 'FEL.txt').read_text()[:300] if (rdir / 'FEL.txt').is_file() else r.stderr[-300:])
    logg('%s %s %s %.0f s' % (status, slug, namn, time.time() - start))


def main():
    alla = [(s, arm, n) for arm, antal in ARMAR.items() for n in range(1, antal + 1) for s in BYGGEN]
    random.Random(20261002).shuffle(alla)
    logg('%d granskningar, %d åt gången' % (len(alla), PARALLELLT))
    with ThreadPoolExecutor(PARALLELLT) as ex:
        list(ex.map(lambda j: jobb(*j), alla))
    logg('alla klara')


if __name__ == '__main__':
    main()
