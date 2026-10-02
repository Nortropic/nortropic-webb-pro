"""Förbereder granskarförsöket: en isolerad repokopia per dömt bygge, blind för byggets egen dom.

Per bygge X: repots spårade filer vid main, LARDOMAR.md utan X:s domblock, kunder/X utan DOM.json, granskning och
körloggar, de två andra dömda byggena bara med det kalibreringen läser (DOM.json, GRANSKNING.json, första vyn),
underlag/X, armarnas granskartexter, och ett färskt snabbprov med dagens kontroller.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
G = Path(os.environ.get('NWP_FORSOK') or '/tmp/nwp-granskarforsok')  # utdata, utanför repot
KOD = Path(__file__).resolve().parent
BYGGEN = ['lulea-snickaren', 'sundboms-el', 'paint-it-black-maleri']


def kor(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit('fel: %s\n%s%s' % (' '.join(map(str, args)), r.stdout[-2000:], r.stderr[-2000:]))
    return r.stdout


def utan_dom(text, slug):
    block = re.split(r'(?m)^(?=## L)', text)
    return ''.join(b for b in block if not re.match(r'## L\d+ · [\d-]+ · %s\s*$' % re.escape(slug), b.split('\n', 1)[0]))


def forbered(x):
    rot = G / x / 'rot'
    if rot.exists():
        shutil.rmtree(rot)
    rot.mkdir(parents=True)
    arkiv = subprocess.run(['git', '-C', str(MAIN), 'archive', 'HEAD'], capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', str(rot)], input=arkiv, check=True)
    (rot / '.venv').symlink_to(MAIN / '.venv')
    (rot / 'kontroller' / 'node_modules').symlink_to(MAIN / 'kontroller' / 'node_modules')
    lar = (rot / 'LARDOMAR.md').read_text(encoding='utf-8')
    filtrerad = utan_dom(lar, x)
    assert filtrerad != lar and ('· %s\n' % x) not in filtrerad, x
    (rot / 'LARDOMAR.md').write_text(filtrerad, encoding='utf-8')
    (rot / 'kunder').mkdir()
    (rot / 'underlag').mkdir()
    kor(['cp', '-cR', str(MAIN / 'kunder' / x), str(rot / 'kunder' / x)])
    for f in ['DOM.json']:
        (rot / 'kunder' / x / f).unlink(missing_ok=True)
    shutil.rmtree(rot / 'kunder' / x / 'granskning', ignore_errors=True)
    for f in (rot / 'kunder' / x).glob('korning-*.jsonl'):
        f.unlink()
    kor(['cp', '-cR', str(MAIN / 'underlag' / x), str(rot / 'underlag' / x)])
    for y in BYGGEN:
        if y == x:
            continue
        k = rot / 'kunder' / y
        (k / 'granskning').mkdir(parents=True)
        (k / 'prov' / 'inspektion' / 'hem').mkdir(parents=True)
        shutil.copy2(MAIN / 'kunder' / y / 'DOM.json', k / 'DOM.json')
        shutil.copy2(MAIN / 'kunder' / y / 'granskning' / 'GRANSKNING.json', k / 'granskning' / 'GRANSKNING.json')
        for vy in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
            shutil.copy2(MAIN / 'kunder' / y / 'prov' / 'inspektion' / 'hem' / vy, k / 'prov' / 'inspektion' / 'hem' / vy)
    for arm in ('persona', 'c'):
        shutil.copy2(KOD / ('GRANSKARE-%s.md' % arm), rot / 'kritik' / ('GRANSKARE-%s.md' % arm))
    print(x, 'kopia klar; snabbprov …', flush=True)
    r = subprocess.run([str(rot / '.venv' / 'bin' / 'python'), '-B', str(rot / 'kontroller' / 'prova.py'), x, '--snabb'],
                       cwd=str(rot), capture_output=True, text=True)
    prov = rot / 'kunder' / x / 'prov'
    print(x, 'snabbprov rc', r.returncode, '; standard.md', (prov / 'standard.md').is_file(), '; STIL.md',
          (prov / 'stil' / 'STIL.md').is_file(), '; rutor', len(list(prov.glob('inspektion/*/vy-390-ruta-*.png'))), flush=True)


if __name__ == '__main__':
    for x in sys.argv[1:] or BYGGEN:
        forbered(x)
