#!/usr/bin/env python3
"""prov_startkontroll.py — startkontrollen och underhållet i en isolerad kopia av repot (ägarens uppdrag 2026-10-05
20:27Z och ~20:50Z): de åtta fallen (oförändrad miljö upprepar inget; en ändrad skill utlöser kontrollerna; en
uppdatering som faller redovisas; en nödvändig MCP som faller stoppar; en källa som inte svarar är okänd; en ändrad
konfiguration gör gamla prov ogiltiga; alla startvägar går genom kontrollen; en pågående körning behåller sina
förutsättningar), Python-låset, Homebrew-formlerna, en avvisad huvudversion och en uppdatering som tas in.

    .venv/bin/python kontroller/rokprov/revision/prov_startkontroll.py <repo>

Nätet, modellerna och installationerna byts mot falska svar; skillens uppdatering går på riktigt mot en lokal
uppströmskälla (git), och worktree-mekanismen mot kopians eget git. Ingenting skrivs i det riktiga repots underlag/,
kunder/, .venv eller node_modules.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT_REAL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-startprov-')).resolve()
KOPIA = TMP / 'repo'
FAKE = TMP / 'fake'


def sh(*a, cwd=None, env=None):
    r = subprocess.run([str(x) for x in a], cwd=str(cwd or KOPIA), capture_output=True, text=True, env=env)
    assert r.returncode == 0, (a, r.stdout[-400:], r.stderr[-400:])
    return r.stdout


GIT = ['git', '-c', 'user.name=prov', '-c', 'user.email=prov@exempel.se', '-c', 'commit.gpgsign=false']

# --- den isolerade kopian ---
utom = shutil.ignore_patterns('node_modules', '.git', 'underlag', 'kunder', 'dist', '.astro', '__pycache__', '.venv')
for d in ('kontroller', 'kunskap', 'kritik', 'mall', '.claude'):
    shutil.copytree(ROOT_REAL / d, KOPIA / d, ignore=utom, symlinks=True)
for f in ('BESLUT.md', 'CLAUDE.md', 'LARDOMAR.md', 'kor.sh', 'requirements.txt', 'requirements-lock.txt', '.gitignore'):
    if (ROOT_REAL / f).exists():
        shutil.copy2(ROOT_REAL / f, KOPIA / f)
os.symlink(os.path.realpath(ROOT_REAL / '.venv'), KOPIA / '.venv')
os.symlink(os.path.realpath(ROOT_REAL / 'kontroller' / 'node_modules'), KOPIA / 'kontroller' / 'node_modules')
sh(*GIT, 'init', '-q', '-b', 'main')
(KOPIA / '.git' / 'info' / 'exclude').write_text('.venv\nkontroller/node_modules\n')
sh(*GIT, 'add', '-A')
sh(*GIT, 'commit', '-q', '-m', 'kopian')

# falska binärer: claude (version, hjälp, mcp list), vercel och npm (root -g); node och git är riktiga
FAKE.mkdir()
(FAKE / 'bin').mkdir()
(FAKE / 'version').write_text('2.1.289 (Claude Code)\n')
hjalp = ' '.join(['--json-schema', '--allowedTools', '--disallowedTools', '--settings', '--setting-sources', '--tools', '--permission-mode',
                  '--strict-mcp-config', '--mcp-config', '--effort', '--model', '--output-format'])
(FAKE / 'help').write_text('Usage: claude ' + hjalp + '\n')
MCP_OK = 'refero: https://api.refero.design/mcp (HTTP) - ✔ Connected\nmobbin: https://api.mobbin.com/mcp (HTTP) - ✔ Connected\nclaude.ai Gmail: https://x - ✔ Connected\n'
(FAKE / 'mcp').write_text(MCP_OK)
(FAKE / 'bin' / 'claude').write_text('#!/bin/bash\nD=%s\ncase "$1" in --version) cat "$D/version";; --help) cat "$D/help";; mcp) echo x >> "$D/mcp-anrop"; '
                                     'cat "$D/mcp";; *) echo "{}";; esac\n' % FAKE)
(FAKE / 'bin' / 'vercel').write_text('#!/bin/bash\necho "Vercel CLI 60.0.1"\n')
(FAKE / 'bin' / 'npm').write_text('#!/bin/bash\ncase "$1" in root) echo %s/npm-global;; --version) echo 10.9.8;; *) exit 1;; esac\n' % FAKE)
for b in ('claude', 'vercel', 'npm'):
    (FAKE / 'bin' / b).chmod(0o755)
os.environ['PATH'] = '%s:%s' % (FAKE / 'bin', os.environ['PATH'])
os.environ['NWP_CLAUDE_BIN'] = str(FAKE / 'bin' / 'claude')
os.environ['NWP_SPANING_AV'] = '1'
for k in ('NWP_SLUG', 'NWP_STARTKONTROLL'):
    os.environ.pop(k, None)

sys.path.insert(0, str(KOPIA / 'kontroller'))
import verktygslada as vl  # noqa: E402
import startkontroll as sk  # noqa: E402
import underhall as uh  # noqa: E402
import refero_mcp  # noqa: E402
assert vl.ROOT == KOPIA and vl.LAGE == KOPIA / 'underlag' / 'startkontroll', vl.ROOT

# --- falska uppslag och prov (räknade) ---
ANROP = {'npm': 0, 'pypi': 0, 'brew': 0, 'git': 0, 'modell': 0, 'refero': 0, 'webb': 0, 'detektor': 0}
NPM = {'@anthropic-ai/claude-code': '2.1.289', 'vercel': '60.0.1'}
PYPI = {}
BREW = {'node@22': '22.23.2', 'node@24': '24.21.0_1', 'python@3.12': '3.12.13_4', 'git': '2.55.0', 'gh': '2.97.0'}
AKTIV = {'node@22': '22.23.2', 'python@3.12': '3.12.13_4', 'git': '2.55.0', 'gh': '2.97.0'}
NODE_MAL = {'major': 22, 'version': '22.23.2', 'vercel': [20, 22, 24], 'lts': [20, 22, 24]}


def f_npm(p):
    ANROP['npm'] += 1
    for dep in ('mall/astro', 'mall/leverans', 'kontroller'):
        v = vl.paketberoenden(KOPIA / dep).get(p)
        if v:
            return NPM.get(p, v)
    return NPM.get(p)


def f_pypi(n):
    ANROP['pypi'] += 1
    return PYPI.get(n) or vl.las_krav(KOPIA / 'requirements.txt').get(n)


def f_brew(f):
    ANROP['brew'] += 1
    return {'senaste': BREW[f], 'installerade': [AKTIV.get(f)], 'lankad': AKTIV.get(f), 'keg_only': '@' in f}


def f_git(repo):
    ANROP['git'] += 1
    return None  # källorna svarar inte: okänd, aldrig grön (fall 5)


vl.npm_view, vl.pypi_version, vl.brew_info, vl.git_head = f_npm, f_pypi, f_brew, f_git
vl.node_lts_vercel = lambda: dict(NODE_MAL)
vl.motor_releaser = lambda: '0.1.11'
vl.softwareupdate_lista = lambda: []
vl.brew_senaste_release = lambda: '6.0.22'
vl.brew_aktiv = lambda f: AKTIV.get(f)
vl.node_formel = lambda: ('node@22', '22.23.2')
vl.pip_frys = lambda py: dict(vl.las_krav(KOPIA / 'requirements-lock.txt'))


def f_modell(b, m, timeout=240, schema=False):
    ANROP['modell'] += 1
    return None


vl.modellsvar = f_modell


class FalskKlient:
    def __init__(self, *a, **k):
        ANROP['refero'] += 1

    def starta(self):
        return {}

    def verktyg(self):
        return ['refero_search_styles', 'refero_get_style', 'refero_search_apps']

    def json(self, namn, args):
        return {'records': [{'uuid': 'u1', 'preview_url': 'https://images.refero.design/x.jpg'}]} if namn == 'refero_search_styles' else \
            {'colors': [1, 2], 'typography': [1]}


NYCKEL = TMP / 'refero.env'
NYCKEL.write_text('REFERO_MCP_TOKEN=provnyckel-ett\n')
refero_mcp.Klient = FalskKlient
refero_mcp.nyckel = lambda fil=None: NYCKEL.read_text().split('=', 1)[1].strip()


def f_bild(url, mal, max_byte=0):
    p = Path(str(mal) + '.jpg')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b'\xff\xd8\xffbild')
    return p


refero_mcp.ladda_bild = f_bild


def f_webb(k, prov_dir, node_modules=None):
    x = k.minns('prov:webblasare', 'v1', vl.GILTIGHET['prov'])
    if x:
        return dict(x, ateranvant=True)
    ANROP['webb'] += 1
    return k.spara('prov:webblasare', 'v1', resultat='ok', detalj='falsk sida inspekterad')


def f_detektor(k, prov_dir):
    x = k.minns('prov:detektor', 'v1', vl.GILTIGHET['prov'])
    if x:
        return dict(x, ateranvant=True)
    ANROP['detektor'] += 1
    return k.spara('prov:detektor', 'v1', resultat='ok', detalj='falsk motor')


vl.prova_webblasaren, vl.prova_detektorn = f_webb, f_detektor
# Mobbins fullständiga prov ur underhållet (här: ett sparat resultat)
lage = vl.lagekatalog()
vl.Cache(lage / 'CACHE.json').spara('prov:mobbin', 'v1', resultat='ok', detalj='sökning och 3 bilder (falskt prov)')


def nollstall():
    for k in ANROP:
        ANROP[k] = 0


# --- briefen för en provkund ---
SLUG = 'provkund'
(KOPIA / 'underlag' / SLUG / 'bilder').mkdir(parents=True)
(KOPIA / 'underlag' / SLUG / 'BRIEF.md').write_text('# Brief\n\n## §4 Primär handling\n\nRing eller skicka en förfrågan i formuläret. Bokning av hembesök.\n')
(KOPIA / 'underlag' / SLUG / 'bilder' / 'BILDER.md').write_text('| fil | vad |\n|---|---|\n| a.jpg | jobb |\n')

# ===== startkontrollen =====
t0 = time.time()
kv1 = sk.kor_kontroll(SLUG, 'ny')
assert kv1['status'] in ('redo', 'begransad'), (kv1['status'], kv1['stoppar'])
rad = {r['namn']: r for r in kv1['rader']}
assert rad['refero']['resultat'] == 'ok' and rad['mobbin']['resultat'] == 'ok', 'MCP-anslutningarna'
assert rad['Refero (direkt)']['resultat'] == 'ok' and rad['webbläsarkedjan']['resultat'] == 'ok'
assert rad['Referos verktyg utan uppgift i flödet']['detalj'] == 'refero_search_apps', 'en Refero-förmåga utan uppgift redovisas'
assert any(r['grupp'] == 'uppdrag' and r['namn'] == 'bokning' and r['formaga'] == 'delvis' for r in kv1['rader']), 'kundens behov mot förmågan'
assert (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').is_file() and (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.json').is_file()
assert 'allt uppdaterat' not in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text().lower()
# fall 5: källor som inte svarar (skillsens git, utan underhåll) är okända, aldrig gröna
okanda = [r for r in kv1['rader'] if r['grupp'] == 'skill' and r.get('installerat') != 'egen']
assert okanda and all(r['resultat'] == 'okand' for r in okanda), [(r['namn'], r['resultat']) for r in okanda][:3]
assert kv1['status'] == 'begransad', 'okänt ger aldrig redo'
print('startkontrollen: kvittot, förmågan, kundens behov och okända källor ok (%.1f s)' % (time.time() - t0))

# fall 1: en oförändrad miljö upprepar inga prov
m_fore = (FAKE / 'mcp-anrop').read_text().count('x')
nollstall()
kv2 = sk.kor_kontroll(SLUG, 'ny')
assert ANROP['modell'] == 0 and ANROP['refero'] == 0 and ANROP['webb'] == 0 and ANROP['detektor'] == 0, ANROP
assert (FAKE / 'mcp-anrop').read_text().count('x') == m_fore, 'claude mcp list körs inte om inom giltigheten'
assert not [u for u in kv2['utfort'] if u.startswith(('prov:', 'modell:', 'mcp:'))], kv2['utfort']
assert {'mcp:lista', 'prov:refero'} <= set(kv2['ateranvant']), kv2['ateranvant']
print('fall 1: oförändrad miljö upprepar inget ok')

# fall 6: en ändrad konfiguration gör gamla prov ogiltiga (claude-versionen, Referos nyckel, MCP-konfigurationen)
nollstall()
(FAKE / 'version').write_text('2.1.290 (Claude Code)\n')
NYCKEL.write_text('REFERO_MCP_TOKEN=provnyckel-tva\n')
(KOPIA / 'kontroller' / 'mcp' / 'refero.json').write_text((KOPIA / 'kontroller' / 'mcp' / 'refero.json').read_text() + '\n')
sk.kor_kontroll(SLUG, 'ny')
assert ANROP['modell'] == len(set(sk.modeller().values())) and ANROP['refero'] == 1, ANROP
assert (FAKE / 'mcp-anrop').read_text().count('x') == m_fore + 1, 'ny MCP-konfiguration: listan prövas om'
(FAKE / 'version').write_text('2.1.289 (Claude Code)\n')
print('fall 6: ändrad version, nyckel och konfiguration gör om proven ok')

# fall 4: en nödvändig MCP som faller stoppar starten
(FAKE / 'mcp').write_text(MCP_OK.replace('mobbin: https://api.mobbin.com/mcp (HTTP) - ✔ Connected', 'mobbin: https://api.mobbin.com/mcp (HTTP) - ✗ Failed to connect'))
(KOPIA / 'kontroller' / 'mcp' / 'mobbin.json').write_text((KOPIA / 'kontroller' / 'mcp' / 'mobbin.json').read_text() + '\n')
kv = sk.kor_kontroll(SLUG, 'ny')
assert kv['status'] == 'stoppad' and any(s.startswith('mobbin') for s in kv['stoppar']), (kv['status'], kv['stoppar'])
assert 'STOPPAD' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
(FAKE / 'mcp').write_text(MCP_OK)
(KOPIA / 'kontroller' / 'mcp' / 'mobbin.json').write_text((KOPIA / 'kontroller' / 'mcp' / 'mobbin.json').read_text() + '\n')
print('fall 4: nödvändig MCP som faller stoppar ok')

# fall 2: en ändrad skill utlöser kontrollerna (metodlåset fäller ändringen; skillens fingeravtryck byts)
skillfil = KOPIA / '.claude' / 'skills' / 'refero-design' / 'SKILL.md'
fore_skill = skillfil.read_text()
avtryck_fore = vl.mappavtryck(skillfil.parent)
skillfil.write_text(fore_skill + '\nEn lokal ändring.\n')
assert vl.mappavtryck(skillfil.parent) != avtryck_fore
kv = sk.kor_kontroll(SLUG, 'ny')
metodrad = next(r for r in kv['rader'] if r['namn'] == 'metodkartan och låset')
assert metodrad['resultat'] == 'fel' and 'refero-design/SKILL.md' in metodrad['detalj'] and kv['status'] == 'stoppad', metodrad
skillfil.write_text(fore_skill)
print('fall 2: ändrad skill utlöser metodkontrollen ok')

# fall 7: alla startvägar går genom kontrollen
import atelje  # noqa: E402
gamla = sk.for_start
sk.for_start = lambda slug, lage: {'status': 'stoppad', 'stoppar': ['mobbin: Failed to connect'], 'rader': [], 'tid': vl.nu(), 'start': lage}
rot = KOPIA / 'underlag' / SLUG / 'atelje'
(rot / 'gammal-riktning').mkdir(parents=True, exist_ok=True)
anrop_aterkalla = []
atelje.aterkalla = lambda slug: anrop_aterkalla.append(slug)
rc = atelje.arbetare(SLUG, 'ny')
st = json.loads((rot / 'STATUS.json').read_text())
assert rc == 1 and st['steg'] == 'fel' and 'Startkontrollen stoppade starten' in st['fel'] and 'mobbin' in st['fel'], st
assert not anrop_aterkalla and (rot / 'gammal-riktning').is_dir() and not list(rot.glob('foregaende*')), 'inget arkiveras eller återkallas före kontrollen'
sk.for_start = gamla
kor = (KOPIA / 'kor.sh').read_text()
i_sk, i_inst, i_uchg = kor.index('kontroller/startkontroll.py'), kor.index('atelje.installera_godkand'), kor.index('chflags uchg "$ROOT/kunder"')
i_claude = kor.index('claude "${ARGS[@]}"')
assert i_sk < i_inst < i_uchg < i_claude, 'kor.sh: startkontrollen före installationen, låsningen och modellen'
assert 'atelje.main(' in (KOPIA / 'kontroller' / 'prototyp.py').read_text(), 'prototyp.py startar via ateljén'
assert "startkontroll.for_start(slug, lage)" in (KOPIA / 'kontroller' / 'atelje.py').read_text()
print('fall 7: arbetaren, kor.sh och prototyp.py går genom startkontrollen ok')

# återupptagen körning: behåller sitt låsta underlag och redovisar ändringarna
kv_ny = sk.kor_kontroll(SLUG, 'ny')
las_ny = kv_ny['las']
(KOPIA / 'mall' / 'astro' / 'package-lock.json').write_text((KOPIA / 'mall' / 'astro' / 'package-lock.json').read_text() + '\n')
kv_fort = sk.kor_kontroll(SLUG, 'fortsatt')
assert kv_fort['las'] == las_ny and 'mall_las' in kv_fort['aterupptagen']['andrat'], kv_fort.get('aterupptagen')
assert 'Återupptagen körning' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
sh(*GIT, 'checkout', '-q', '--', 'mall/astro/package-lock.json')
print('återupptagen körning: låset kvar och ändringen redovisad ok')

# ===== underhållet =====
# Python-låset skapas först, ur .venv, och checkas in
for f in ('requirements.txt', 'requirements-lock.txt'):
    (KOPIA / f).unlink()
sh(*GIT, 'commit', '-q', '-am', 'utan pythonlås')
rap = {'rader': [], 'commits': []}
vl.pip_frys = lambda py: {'ddgs': '9.16.0', 'requests': '2.34.2', 'lxml': '6.1.3', 'yt-dlp': '2026.8.19', 'urllib3': '2.8.0'}
uh.steg_pythonlas(vl.Kontext(nat=False, prova=False), rap)
krav, lasfil = vl.python_las_filer()
assert vl.las_krav(krav) == {'ddgs': '9.16.0', 'requests': '2.34.2', 'yt-dlp': '2026.8.19'}, vl.las_krav(krav)
assert vl.las_krav(lasfil)['lxml'] == '6.1.3' and len(vl.las_krav(lasfil)) == 5
assert 'Underhåll: versionslås för Python-paketen' in sh(*GIT, 'log', '-1', '--format=%s') and rap['rader'][0]['resultat'] == 'uppdaterad'
# en miljö som avviker från låset syns; en nyare version på PyPI blir en kandidat
vl.pip_frys = lambda py: {'ddgs': '9.16.0', 'requests': '2.30.0', 'lxml': '6.1.3', 'yt-dlp': '2026.8.19', 'urllib3': '2.8.0'}
k = vl.Kontext(nat=True, prova=False)
PYPI['yt-dlp'] = '2026.9.30'
py_rader = {r['id']: r for r in vl.inventera(k, ('python',))}
assert py_rader['pip:miljo']['resultat'] == 'fel' and 'requests 2.30.0≠2.34.2' in py_rader['pip:miljo']['detalj'], py_rader['pip:miljo']
assert py_rader['pip:yt-dlp']['kandidater'][0]['version'] == '2026.9.30' and not py_rader['pip:yt-dlp']['kandidater'][0]['huvudversion']
vl.pip_frys = lambda py: dict(vl.las_krav(KOPIA / 'requirements-lock.txt'))
print('Python-låset: skapat och incheckat, avvikelse och kandidat syns ok')

# OSV-granskningen tolkas rätt (falskt svar)
class FalsktSvar:
    def __init__(self, d):
        self.d = d

    def read(self):
        return json.dumps(self.d).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


gammal_urlopen = vl.urllib.request.urlopen
vl.urllib.request.urlopen = lambda req, timeout=0: FalsktSvar({'results': [{}, {'vulns': [{'id': 'GHSA-xxxx'}]}]})
assert uh.osv_granska({'a': '1', 'b': '2'}) == [('b', '2', ['GHSA-xxxx'])]
vl.urllib.request.urlopen = gammal_urlopen
print('Python: sårbarhetsgranskningen (OSV) ok')

# Homebrew: bara node, python@3.12, git och gh; Node följer senaste LTS som Vercel stöder
brew_rader = [r for r in vl.inventera(vl.Kontext(nat=True, prova=False), ('brew',))]
assert sorted(r['id'] for r in brew_rader) == ['brew:gh', 'brew:git', 'brew:node', 'brew:python@3.12'], [r['id'] for r in brew_rader]


def falsk_hamta(url, **kw):
    if 'nodejs.org' in url:
        return json.dumps([{'version': 'v26.10.0', 'lts': False}, {'version': 'v25.9.0', 'lts': False}, {'version': 'v24.21.0', 'lts': 'Krypton'},
                           {'version': 'v22.23.3', 'lts': 'Jod'}, {'version': 'v20.20.2', 'lts': 'Iron'}]).encode()
    return VERCEL_HTML.encode()


VERCEL_HTML = '<p>Current available versions are:</p><ul><li>24.x (default)</li><li>22.x</li><li>20.x</li></ul><p>Only major versions are available.</p>'
import importlib  # noqa: E402
vl_ren = importlib.import_module('verktygslada')
riktig_lts = vl_ren.__dict__['node_lts_vercel']
vl.hamta_url = falsk_hamta
mal = vl_ren.node_lts_vercel.__wrapped__() if hasattr(vl_ren.node_lts_vercel, '__wrapped__') else None
src = (KOPIA / 'kontroller' / 'verktygslada.py').read_text()
ns = {}
exec(compile('import json, re\n' + src[src.index('def node_lts_vercel'):src.index('def motor_releaser')], 'lts', 'exec'),
     {'json': json, 're': __import__('re'), 'hamta_url': falsk_hamta, 'huvud': vl.huvud, 'NODE_INDEX': vl.NODE_INDEX, 'VERCEL_NODE': vl.VERCEL_NODE}, ns)
mal = ns['node_lts_vercel']()
assert mal['major'] == 24 and mal['version'] == '24.21.0' and mal['vercel'] == [20, 22, 24], mal
VERCEL_HTML = '<p>Current available versions are: 22.x (default) 20.x</p><p>Only major versions are available.</p>'
assert ns['node_lts_vercel']()['major'] == 22, 'en LTS som Vercel inte stöder (24) väljs inte; udda 25 och 26 aldrig'
print('Homebrew: fyra formler, Node efter LTS som Vercel stöder ok')

# en avvisad huvudversion (node@24 rött i rökprovet), en uppdatering som tas in (patchen), och en avvisad version
# prövas igen först när en nyare kommer
NODE_MAL.update(major=24, version='24.21.0')
k = vl.Kontext(nat=True, prova=False, max_alder=0)
nod = next(r for r in vl.inventera(k, ('brew',)) if r['id'] == 'brew:node')
BREW['node@22'] = '22.23.3_1'
nod = next(r for r in vl.inventera(k, ('brew',)) if r['id'] == 'brew:node')
assert [c['version'] for c in nod['kandidater']] == ['24.21.0_1', '22.23.3_1'] and nod['kandidater'][0]['huvudversion'], nod['kandidater']
BREWANROP, ROKPROV = [], []
uh.brew = lambda *a, timeout=0: (BREWANROP.append(a) or (0, str(FAKE)))
uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0: (ROKPROV.append(etikett) or
                                                                                  (False, 'rökprovet rött (kod 1): FEL: provet blev rött på den rena testsajten (logg x)'))
(FAKE / 'bin' / 'node').write_text('#!/bin/bash\necho v24.21.0\n')
(FAKE / 'bin' / 'node').chmod(0o755)
uh.verifiera_formel = lambda formel, version: None
rap = {'rader': [], 'commits': []}
uh.hantera(k, nod, rap)
assert [x['resultat'] for x in rap['rader']] == ['avvisad', 'uppdaterad'], rap['rader']
assert 'rökprovet rött' in rap['rader'][0]['detalj'] and rap['rader'][0]['huvudversion'], rap['rader'][0]
assert ('install', '--formula', 'node@24') in BREWANROP and ('upgrade', '--formula', 'node@22') in BREWANROP, BREWANROP
assert not any(a and a[0] == 'upgrade' and '--formula' not in a for a in BREWANROP), 'aldrig brew upgrade på allt'
assert k.avvisade.for_version('brew:node', '24.21.0_1')['fel'].startswith('rökprovet rött')
assert any(a['id'] == 'brew:node' and a['till'] == '22.23.3_1' for a in vl.andringar(k.katalog))
# samma huvudversion prövas inte om; en nyare gör det
ROKPROV.clear()
rap = {'rader': [], 'commits': []}
uh.hantera(k, dict(nod, kandidater=[nod['kandidater'][0]]), rap)
assert not ROKPROV and rap['rader'][0]['resultat'] == 'avvisad' and 'prövas igen när en nyare version kommer' in rap['rader'][0]['detalj']
uh.hantera(k, dict(nod, kandidater=[{'version': '24.22.0', 'formel': 'node@24', 'huvudversion': True}]), {'rader': [], 'commits': []})
assert ROKPROV == ['brew:node-node@24'], ROKPROV
# en patch som inte klarar verifieringen länkas tillbaka till den förra kegen
BREWANROP.clear()
uh.verifiera_formel = lambda formel, version: 'git svarar 2.55.0, väntade 2.56.0'
cellar = FAKE / 'Cellar' / 'git'
(cellar / '2.55.0').mkdir(parents=True)
uh.brew_cellar = lambda f: cellar
git_rad = {'id': 'brew:git', 'namn': 'git', 'grupp': 'Homebrew', 'typ': 'brew', 'installerat': '2.55.0',
           'kandidater': [{'version': '2.56.0', 'formel': 'git', 'huvudversion': False}]}
rap = {'rader': [], 'commits': []}
uh.hantera(k, git_rad, rap)
assert rap['rader'][0]['resultat'] == 'avvisad' and 'återlänkad' in rap['rader'][0]['detalj'], rap['rader'][0]
assert ('unlink', 'git') in BREWANROP and any(a[0] == 'ruby' and '2.55.0' in a[2] for a in BREWANROP), BREWANROP
print('avvisad huvudversion, intagen patch, ingen omprövning av samma version och återlänkning ok')

# fall 8: en pågående körning behåller sina förutsättningar: underhållet skjuter upp; en godkänd kandidat tas in senare
proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)', 'atelje.py', 'annan-kund', '--arbetare'])
try:
    (KOPIA / 'underlag' / 'annan-kund' / 'atelje').mkdir(parents=True)
    (KOPIA / 'underlag' / 'annan-kund' / 'atelje' / 'STATUS.json').write_text(json.dumps({'pid': proc.pid, 'steg': 'skissa'}))
    assert vl.pagaende() and 'annan-kund' in vl.pagaende()[0]
    PROV = []
    uh.PROVA['npm-global'] = lambda k, r, kand: (PROV.append(kand['version']) or (None, {'prov': 'falskt prov'}))
    TAGET = []
    uh.TA_IN['npm-global'] = lambda k, r, kand, staged: (TAGET.append(kand['version']) or ('uppdaterad', 'falskt intag', None))
    rap = uh.underhall(k=vl.Kontext(nat=True, prova=False), prov=False)
    assert rap['status'] == 'uppskjutet' and not PROV and not TAGET, rap
    vercel = {'id': 'npm-global:vercel', 'namn': 'Vercel CLI', 'grupp': 'leverans', 'typ': 'npm-global', 'installerat': '60.0.1',
              'kandidater': [{'version': '62.4.0', 'huvudversion': True}]}
    rap = {'rader': [], 'commits': []}
    uh.hantera(k, vercel, rap)
    assert PROV == ['62.4.0'] and not TAGET and rap['rader'][0]['resultat'] == 'behallen' and 'tas in vid nästa underhåll' in rap['rader'][0]['detalj']
finally:
    proc.kill()
    proc.wait()
rap = {'rader': [], 'commits': []}
uh.hantera(k, vercel, rap)
assert PROV == ['62.4.0'] and TAGET == ['62.4.0'] and rap['rader'][0]['resultat'] == 'uppdaterad' and rap['rader'][0].get('prov_ateranvant'), rap['rader']
print('fall 8: pågående körning skjuter upp intaget; det godkända tas in utan nytt prov ok')

# fall 3 och en uppdatering som tas in: en skill ur en lokal uppströmskälla, trevägs med vår anpassning
upp = TMP / 'uppstrom'
(upp / 'skills' / 'demo').mkdir(parents=True)
(upp / 'skills' / 'demo' / 'SKILL.md').write_text('---\nname: demo\n---\n# Demo\n\nRad ett.\nRad två.\nRad tre.\n')
(upp / 'skills' / 'demo' / 'ref.md').write_text('Referens.\n')
sh(*GIT, 'init', '-q', '-b', 'main', cwd=upp)
sh(*GIT, 'config', 'uploadpack.allowFilter', 'true', cwd=upp)
sh(*GIT, 'add', '-A', cwd=upp)
sh(*GIT, 'commit', '-q', '-m', 'bas', cwd=upp)
bas = sh('git', 'rev-parse', 'HEAD', cwd=upp).strip()
demo = KOPIA / '.claude' / 'skills' / 'demo'
demo.mkdir()
(demo / 'SKILL.md').write_text('---\nname: demo\n---\n# Så används skillen i nortropic-webb-pro\n\nVår anpassning.\n\n# Demo\n\nRad ett.\nRad två.\nRad tre.\n')
(demo / 'ref.md').write_text('Referens.\n')
(demo / 'KALLA.md').write_text('# Källa\n\n- **Källa:** https://github.com/prov/demo-skill, `skills/demo/`, commit `%s` (prov).\n- **Licens:** MIT.\n'
                               '- **Krockar med våra beslut:** inga.\n' % bas)
sh(*GIT, 'add', '-A')
sh(*GIT, 'commit', '-q', '-m', 'demo-skillen')
(upp / 'skills' / 'demo' / 'ref.md').write_text('Referens, uppdaterad.\n')
(upp / 'skills' / 'demo' / 'SKILL.md').write_text('---\nname: demo\n---\n# Demo\n\nRad ett.\nRad två.\nRad tre, förbättrad.\n')
sh(*GIT, 'commit', '-q', '-am', 'uppdatering', cwd=upp)
head = sh('git', 'rev-parse', 'HEAD', cwd=upp).strip()
os.environ.update({'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'url.file://%s.insteadOf' % upp, 'GIT_CONFIG_VALUE_0': 'https://github.com/prov/demo-skill.git'})
vl.git_head = lambda repo: head if 'demo-skill' in repo else None
GRANSKNINGAR = []
uh.granska_andring = lambda namn, diff, krockar: (GRANSKNINGAR.append(diff) or ({'sakert': True, 'risker': [], 'nya_krockar': [], 'kommentar': 'en rad bättre'}, None))
k = vl.Kontext(nat=True, prova=False, max_alder=0)
demo_rad = next(r for r in vl.inventera(k, ('skills',)) if r['id'] == 'skill:demo')
assert demo_rad['kandidater'] and demo_rad['kandidater'][0].get('ojamfort'), demo_rad
rap = {'rader': [], 'commits': []}
uh.hantera(k, demo_rad, rap)
assert rap['rader'][0]['resultat'] == 'uppdaterad', rap['rader']
text = (demo / 'SKILL.md').read_text()
assert 'Vår anpassning.' in text and 'Rad tre, förbättrad.' in text and (demo / 'ref.md').read_text() == 'Referens, uppdaterad.\n', text
assert head in (demo / 'KALLA.md').read_text() and 'Uppdaterad av underhållet' in (demo / 'KALLA.md').read_text()
assert GRANSKNINGAR and 'förbättrad' in GRANSKNINGAR[0]
assert sh('git', 'log', '-1', '--format=%s').startswith('Underhåll: skillen demo') and rap['commits'], rap
# källan ändrar sedan raden vi anpassat: sammanslagningen krockar, avvisas med felet och mappen står kvar
fore = {p.name: p.read_bytes() for p in demo.iterdir()}
(upp / 'skills' / 'demo' / 'SKILL.md').write_text('---\nname: demo\n---\n# Demo, nytt namn\n\nVår anpassning ersatt.\n\nRad ett.\nRad två.\nRad tre, förbättrad.\n')
sh(*GIT, 'commit', '-q', '-am', 'krock', cwd=upp)
head2 = sh('git', 'rev-parse', 'HEAD', cwd=upp).strip()
vl.git_head = lambda repo: head2 if 'demo-skill' in repo else None
k = vl.Kontext(nat=True, prova=False, max_alder=0)
demo_rad = next(r for r in vl.inventera(k, ('skills',)) if r['id'] == 'skill:demo')
rap = {'rader': [], 'commits': []}
uh.hantera(k, demo_rad, rap)
assert rap['rader'][0]['resultat'] == 'avvisad' and 'krockar' in rap['rader'][0]['detalj'], rap['rader']
assert {p.name: p.read_bytes() for p in demo.iterdir()} == fore, 'mappen är orörd efter en avvisad uppdatering'
kv = sk.kor_kontroll(SLUG, 'ny')
demo_kv = next(r for r in kv['rader'] if r.get('id') == 'skill:demo')
assert demo_kv['resultat'] == 'avvisad' and 'krockar' in demo_kv['detalj'], demo_kv
print('fall 3 och intag: skillen uppdaterad trevägs och incheckad; en krock avvisas med felet och syns i kvittot ok')

# ett bytt mätinstrument märks i nästa startkvitto
vl.logga_andring(vl.lagekatalog(), id='instrument:axe-core', namn='axe-core', grupp='mätinstrument', fran='4.13.0', till='4.14.0',
                 prov='rökprovet', commit=None, matinstrument=True)
kv = sk.kor_kontroll(SLUG, 'ny')
assert [a['namn'] for a in kv['matinstrument_bytta']] == ['axe-core'] and 'Mätinstrument bytta' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
kv = sk.kor_kontroll(SLUG, 'ny')
assert not kv['matinstrument_bytta'], 'bara sedan förra starten'
print('mätinstrumentets byte märkt i kvittot ok')

# worktree-mekanismen för hela rökprovet: grönt och rött, och worktreen städas
riktig = importlib.reload(uh)
for f in ('kontroller/rokprov.sh',):
    (KOPIA / f).write_text('#!/bin/bash\nif [ -f "$(dirname "$0")/../KANDIDAT-ROD" ]; then echo "FEL: kandidaten bröt provet"; exit 1; fi\necho "rökprovet OK"\n')
sh(*GIT, 'commit', '-q', '-am', 'falskt rökprov')
ok, text = riktig.rokprov_i_worktree(vl.Kontext(nat=False, prova=False), 'prov-gront', lambda wt: None)
assert ok, text
ok, text = riktig.rokprov_i_worktree(vl.Kontext(nat=False, prova=False), 'prov-rott', lambda wt: (wt / 'KANDIDAT-ROD').write_text('x') and None)
assert not ok and 'FEL: kandidaten bröt provet' in text, text
assert sh('git', 'worktree', 'list').count('\n') == 1, sh('git', 'worktree', 'list')
print('rökprovet i en egen worktree: grönt, rött med felet, och städat ok')

shutil.rmtree(TMP, ignore_errors=True)
print('startkontrollens och underhållets prov: alla ok')
