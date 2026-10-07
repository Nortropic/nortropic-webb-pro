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
import re
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT_REAL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-startprov-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):  # också när provet faller: annars fyller kvarlämnade kopior disken
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
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
for f in ('README.md', 'BESLUT.md', 'CLAUDE.md', 'LARDOMAR.md', 'kor.sh', 'requirements.txt', 'requirements-lock.txt', '.gitignore'):
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
(FAKE / 'bin' / 'claude').write_text('#!/bin/bash\nD=%s\necho "$*" >> "$D/claude-anrop"\ncase "$1" in --version) cat "$D/version";; --help) cat "$D/help";; '
                                     'mcp) echo x >> "$D/mcp-anrop"; cat "$D/mcp";; *) echo "{}";; esac\n' % FAKE)
(FAKE / 'bin' / 'vercel').write_text('#!/bin/bash\necho "Vercel CLI 60.0.1"\n')
(FAKE / 'bin' / 'npm').write_text('#!/bin/bash\ncase "$1" in root) echo %s/npm-global;; --version) echo 10.9.8;; ci) mkdir -p node_modules;; *) exit 1;; esac\n' % FAKE)
for b in ('claude', 'vercel', 'npm'):
    (FAKE / 'bin' / b).chmod(0o755)
PATH_URSPRUNG = os.environ['PATH']  # den riktiga node och npm, för provet som låter npm läsa ett lås
os.environ['PATH'] = '%s:%s' % (FAKE / 'bin', os.environ['PATH'])
os.environ['NWP_CLAUDE_BIN'] = str(FAKE / 'bin' / 'claude')
os.environ['NWP_SPANING_AV'] = '1'
os.environ['NWP_KORREGISTER'] = str(TMP / 'korregister')  # körningarna i provet anmäler sig aldrig i maskinens register
# provet är oberoende av anroparens miljö: också inne i underhållets eget rökprov (NWP_UNDERHALL_PROV) anmäler sig
# provets körningar, i provets eget register
for k in ('NWP_SLUG', 'NWP_STARTKONTROLL', 'NWP_UNDERHALL_PROV'):
    os.environ.pop(k, None)
# städregeln (kontroller/stadning.py) städar aldrig det verkliga systemet här, inte heller i kor.sh:s egen process;
# prov_stadning.py prövar den med egna rötter
os.environ['NWP_STADNING'] = 'av'

sys.path.insert(0, str(KOPIA / 'kontroller'))
import verktygslada as vl  # noqa: E402
import startkontroll as sk  # noqa: E402
import underhall as uh  # noqa: E402
BREW_ORIGINAL = uh.brew  # den riktiga, före provens falska (spärren mot brew upgrade på allt prövas på den)
import refero_mcp  # noqa: E402
import korregister  # noqa: E402
import stadning  # noqa: E402
assert korregister.KATALOG == TMP / 'korregister' and uh.BYTESLAS == TMP / 'korregister' / '.byte', korregister.KATALOG
# diskvakten ser 40 % ledigt oberoende av maskinens disk, och städningen mot det verkliga systemet fäller provet
stadning.disk_matt = lambda p: (1000, 400)
stadning.Ram.verklig = classmethod(lambda cls, *a, **k: (_ for _ in ()).throw(AssertionError('provet städar aldrig det verkliga systemet')))
assert vl.ROOT == KOPIA and vl.LAGE == KOPIA / 'underlag' / 'startkontroll', vl.ROOT

# --- falska uppslag och prov (räknade) ---
ANROP = {'npm': 0, 'pypi': 0, 'brew': 0, 'git': 0, 'modell': 0, 'refero': 0, 'webb': 0, 'detektor': 0, 'vakt': 0}
GAMMAL = '2026-01-01T00:00:00Z'  # publicerad långt före karenstiden
TIDER = {}  # paket → {version: publicerad} utöver den senaste: huvudversioner, patchar och versioner i karenstid
NPM = {'@anthropic-ai/claude-code': '2.1.289', 'vercel': '60.0.1'}
PYPI = {}
BREW = {'node@22': '22.23.2', 'node@24': '24.21.0_1', 'python@3.12': '3.12.13_4', 'git': '2.55.0', 'gh': '2.97.0'}
AKTIV = {'node@22': '22.23.2', 'python@3.12': '3.12.13_4', 'git': '2.55.0', 'gh': '2.97.0'}
NODE_MAL = {'major': 22, 'version': '22.23.2', 'vercel': [20, 22, 24], 'lts': [20, 22, 24]}


def mogen(p, v):
    tider = dict(TIDER.get(p) or {})
    if v:
        tider.setdefault(v, GAMMAL)
    return vl.mogna(tider) if tider else None


def f_npm(p):
    ANROP['npm'] += 1
    for dep in ('mall/astro', 'mall/leverans', 'kontroller'):
        v = vl.paketberoenden(KOPIA / dep).get(p)
        if v:
            return mogen(p, NPM.get(p, v))
    return mogen(p, NPM.get(p))


def f_pypi(n):
    ANROP['pypi'] += 1
    return mogen(n, PYPI.get(n) or vl.las_krav(KOPIA / 'requirements.txt').get(n))


def f_brew(f):
    ANROP['brew'] += 1
    return {'senaste': BREW[f], 'installerade': [AKTIV.get(f)], 'lankad': AKTIV.get(f), 'keg_only': '@' in f}


def f_git(repo):
    ANROP['git'] += 1
    return None  # källorna svarar inte: okänd, aldrig grön (fall 5)


vl.npm_versioner, vl.pypi_versioner, vl.brew_info, vl.git_head = f_npm, f_pypi, f_brew, f_git
vl.node_lts_vercel = lambda: dict(NODE_MAL)
vl.motor_releaser = lambda: '0.1.11'
vl.softwareupdate_lista = lambda: []
vl.brew_senaste_release = lambda: '6.0.22'
vl.brew_aktiv = lambda f: AKTIV.get(f)
BREW_API = {}  # formel → {'senaste', 'tid'} när API:t skiljer sig från det lokala indexet (karenstiden, ett gammalt index)
vl.brew_api = lambda f: BREW_API.get(f) or {'senaste': BREW[f], 'tid': GAMMAL}
NODE_FORMEL = vl.node_formel  # den riktiga, som startar node
vl.node_formel = lambda: ('node@22', '22.23.2')
NODE_UR_VAG = vl.node_formel_ur_vag  # den riktiga, för provet att länkprovet aldrig startar node (2026-10-06)
vl.node_formel_ur_vag = lambda: 'node@22'
vl.pip_frys = lambda py: dict(vl.las_krav(KOPIA / 'requirements-lock.txt'))


def f_modell(b, m, timeout=240, schema=False):
    ANROP['modell'] += 1
    return None


vl.modellsvar = f_modell


def f_vakt(b, modell=None, timeout=300):
    ANROP['vakt'] += 1
    return None


vl.vaktprov = f_vakt


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


riktig_detektor = vl.prova_detektorn
vl.prova_webblasaren, vl.prova_detektorn = f_webb, f_detektor
# Mobbins fullständiga prov ur underhållet (här: ett sparat resultat)
lage = vl.lagekatalog()
vl.Cache(lage / 'CACHE.json').spara('prov:mobbin', 'v1', resultat='ok', detalj='sökning och 3 bilder (falskt prov)')


def gammal_git():
    """git-miljö för uppströmskällans commits: daterade före karenstiden."""
    return dict(os.environ, GIT_AUTHOR_DATE=GAMMAL, GIT_COMMITTER_DATE=GAMMAL)


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
# diskvakten (städregeln, punkt 6): en rad och en mening i varje kvitto; över 15 % ledigt städas inget
assert rad['diskvakten']['resultat'] == 'ok' and 'över 15 %' in rad['diskvakten']['detalj'] and kv1['diskvakt']['fore']['andel_ledig'] == 0.4, rad['diskvakten']
assert 'Diskvakten: 40,0 % ledigt' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
# fall 5: källor som inte svarar (skillsens git, utan underhåll) är okända, aldrig gröna
okanda = [r for r in kv1['rader'] if r['grupp'] == 'skill' and r.get('installerat') != 'egen']
assert okanda and all(r['resultat'] == 'okand' for r in okanda), [(r['namn'], r['resultat']) for r in okanda][:3]
assert kv1['status'] == 'begransad', 'okänt ger aldrig redo'
print('startkontrollen: kvittot, förmågan, kundens behov och okända källor ok (%.1f s)' % (time.time() - t0))

# fall 1: en oförändrad miljö upprepar inga prov
m_fore = (FAKE / 'mcp-anrop').read_text().count('x')
nollstall()
kv2 = sk.kor_kontroll(SLUG, 'ny')
assert ANROP['modell'] == 0 and ANROP['refero'] == 0 and ANROP['webb'] == 0 and ANROP['detektor'] == 0 and ANROP['vakt'] == 0, ANROP
assert next(r for r in kv2['rader'] if r['namn'] == 'kundvaktens mekanik')['resultat'] == 'ok', 'vaktprovet är en rad i kvittot'
assert (FAKE / 'mcp-anrop').read_text().count('x') == m_fore, 'claude mcp list körs inte om inom giltigheten'
assert not [u for u in kv2['utfort'] if u.startswith(('prov:', 'modell:', 'mcp:'))], kv2['utfort']
assert {'mcp:lista', 'prov:refero'} <= set(kv2['ateranvant']), kv2['ateranvant']
print('fall 1: oförändrad miljö upprepar inget ok')

# repots identitet och dokumentationens informationsrad i kvittot (ägarens uppdrag 2026-10-06 om dokumentations- och
# rapportstrukturen; README.md, Var information finns): commit, gren och ocommittade filer ur git, "ej angivet" utan
# git, och den privata förteckningen över sparade granskningar som information som aldrig stoppar en start
huvud_ = sh('git', 'rev-parse', 'HEAD').strip()
assert kv1['repo'] == {'commit': huvud_, 'gren': 'main', 'ocommittade': 0}, kv1['repo']
assert 'Repot: commit %s, gren main, ocommittade filer: 0.' % huvud_ in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
startlogg_ = [json.loads(r) for r in (vl.lagekatalog() / 'startlogg.jsonl').read_text().splitlines() if r.strip()]
assert startlogg_[-1]['commit'] == huvud_, startlogg_[-1]
(KOPIA / 'kunskap' / 'ocommittad-anteckning.md').write_text('x\n')
claude_md_ = (KOPIA / 'CLAUDE.md').read_text()
(KOPIA / 'CLAUDE.md').write_text(claude_md_ + '\n')
assert sk.repo_identitet()['ocommittade'] == 2, 'en ospårad och en ändrad fil: %s' % sk.repo_identitet()
(KOPIA / 'kunskap' / 'ocommittad-anteckning.md').unlink()
(KOPIA / 'CLAUDE.md').write_text(claude_md_)
EJ_ = {'commit': 'ej angivet', 'gren': 'ej angivet', 'ocommittade': 'ej angivet'}
(TMP / 'utan-git').mkdir()
os.environ['GIT_CEILING_DIRECTORIES'] = str(TMP)  # git letar aldrig ovanför provets katalog
try:
    assert sk.repo_identitet(TMP / 'utan-git') == EJ_, sk.repo_identitet(TMP / 'utan-git')
finally:
    os.environ.pop('GIT_CEILING_DIRECTORIES', None)
spara_kor_ = vl.kor
vl.kor = lambda args, **kw: (127, 'FileNotFoundError: git') if args[0] == 'git' else spara_kor_(args, **kw)
try:
    assert sk.repo_identitet() == EJ_, 'git saknas'
    assert 'Repot: commit ej angivet, gren ej angivet, ocommittade filer: ej angivet.' in sk.markdown(dict(kv1, repo=sk.repo_identitet()))
finally:
    vl.kor = spara_kor_
assert kv1['dokumentation'] == {'platsregel': True, 'forteckning': None}, kv1['dokumentation']
assert 'Dokumentationen (information; stoppar aldrig en start): platsregeln finns i README.md' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
g_ = KOPIA / 'underlag' / 'granskningar'
(g_ / 'sessioner').mkdir(parents=True)
(g_ / 'sessioner' / 'GR-a.md').write_text('a\n')
(g_ / 'sessioner' / 'GR-b.md').write_text('b, ändrad efter kopieringen\n')
(g_ / 'FORTECKNING.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in (
    {'fil': 'granskningar/sessioner/GR-a.md', 'sha256': vl.sha(b'a\n')},
    {'fil': 'granskningar/sessioner/GR-b.md', 'sha256': vl.sha(b'b\n')},
    {'fil': 'granskningar/sessioner/GR-borta.md', 'sha256': vl.sha(b'c\n')})))
kv3 = sk.kor_kontroll(SLUG, 'ny')
assert kv3['dokumentation']['forteckning'] == {'poster': 3, 'saknas': 1, 'fel_sha': 1, 'ej_kontrollerade': 0}, kv3['dokumentation']
assert kv3['status'] == kv2['status'] and kv3['stoppar'] == kv2['stoppar'], 'förteckningen stoppar aldrig: %s %s' % (kv3['status'], kv3['stoppar'])
assert '3 poster, 1 filer saknas, 1 med fel sha256' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
readme_ = (KOPIA / 'README.md').read_text()
(KOPIA / 'README.md').write_text(readme_.replace('## Var information finns', '## Något annat'))
assert sk.dokumentationen()['platsregel'] is False and 'platsregeln saknas' in sk.dokumentation_text(sk.dokumentationen())
(KOPIA / 'README.md').write_text(readme_)
# informationen stoppar aldrig en start, inte heller när en förteckningsrad eller hela kontrollen kastar (granskningen av
# r97, B1): en för lång sökväg och en katalog utan läsrätt ger OSError i pathlib, och ett fel i dokumentationen() eller
# repo_identitet() blir "ej kontrollerad" i kvittot; status och stopp är desamma som utan förteckningen
(g_ / 'sessioner' / 'stangd').mkdir()
(g_ / 'sessioner' / 'stangd' / 'GR-c.md').write_text('c\n')
with open(g_ / 'FORTECKNING.jsonl', 'a') as f_:
    for x in ({'fil': 'granskningar/' + 'x' * 300 + '.md', 'sha256': vl.sha(b'x')},
              {'fil': 'granskningar/' + '/'.join(['y' * 200] * 10), 'sha256': vl.sha(b'y')},
              {'fil': 'granskningar/sessioner/stangd/GR-c.md', 'sha256': vl.sha(b'c\n')}):
        f_.write(json.dumps(x) + '\n')
os.chmod(g_ / 'sessioner' / 'stangd', 0)
try:
    kv4 = sk.kor_kontroll(SLUG, 'ny')
finally:
    os.chmod(g_ / 'sessioner' / 'stangd', 0o755)
assert kv4['status'] == kv2['status'] and kv4['stoppar'] == kv2['stoppar'], (kv4['status'], kv4['stoppar'])
assert kv4['dokumentation']['forteckning'] == {'poster': 6, 'saknas': 1, 'fel_sha': 1, 'ej_kontrollerade': 3}, kv4['dokumentation']


def kastar(*a, **k):
    raise RuntimeError('provets fel')


spara_info_ = sk.dokumentationen, sk.repo_identitet
sk.dokumentationen = sk.repo_identitet = kastar
try:
    kv5 = sk.kor_kontroll(SLUG, 'ny')
finally:
    sk.dokumentationen, sk.repo_identitet = spara_info_
assert kv5['status'] == kv2['status'] and kv5['stoppar'] == kv2['stoppar'], (kv5['status'], kv5['stoppar'])
kvitto_ = (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
assert 'Dokumentationen (information; stoppar aldrig en start): ej kontrollerad: RuntimeError: provets fel.' in kvitto_, kvitto_[:800]
assert 'Repot: commit ej angivet, gren ej angivet, ocommittade filer: ej angivet (ej kontrollerad: RuntimeError: provets fel).' in kvitto_
assert kv5['repo']['commit'] == 'ej angivet' and json.loads((vl.lagekatalog() / 'startlogg.jsonl').read_text().splitlines()[-1])['commit'] == 'ej angivet'
shutil.rmtree(g_)
print('kvittot: repots commit, gren och ocommittade filer, "ej angivet" utan git, och dokumentationen som information, '
      'också när den inte går att kontrollera, ok')

# fall 6: en ändrad konfiguration gör gamla prov ogiltiga (claude-versionen, Referos nyckel, MCP-konfigurationen)
nollstall()
(FAKE / 'version').write_text('2.1.290 (Claude Code)\n')
NYCKEL.write_text('REFERO_MCP_TOKEN=provnyckel-tva\n')
(KOPIA / 'kontroller' / 'mcp' / 'refero.json').write_text((KOPIA / 'kontroller' / 'mcp' / 'refero.json').read_text() + '\n')
sk.kor_kontroll(SLUG, 'ny')
assert ANROP['modell'] == len(set(sk.modeller().values())) and ANROP['refero'] == 1 and ANROP['vakt'] == 1, ANROP
assert (FAKE / 'mcp-anrop').read_text().count('x') == m_fore + 1, 'ny MCP-konfiguration: listan prövas om'
(FAKE / 'version').write_text('2.1.289 (Claude Code)\n')
print('fall 6: ändrad version, nyckel och konfiguration gör om proven ok')

# fall 4: en nödvändig MCP som faller stoppar starten. claude mcp list läser användarens konfiguration, inte våra filer:
# det är listans ålder (högst fem minuter) som gör att ett avbrott syns, så provet åldrar listan i stället för att röra
# filerna. Helbygget laddar ingen MCP: där redovisas avbrottet utan att stoppa, i ett eget kvitto.


def aldra(nyckel):
    c = vl.Cache(vl.lagekatalog() / 'CACHE.json')
    c.d[nyckel]['tid'] = GAMMAL
    vl.skriv_json(c.fil, c.d)


(FAKE / 'mcp').write_text(MCP_OK.replace('mobbin: https://api.mobbin.com/mcp (HTTP) - ✔ Connected', 'mobbin: https://api.mobbin.com/mcp (HTTP) - ✗ Failed to connect'))
kv = sk.kor_kontroll(SLUG, 'ny')
assert kv['status'] != 'stoppad', 'inom fem minuter gäller den bekräftade listan'
aldra('mcp:lista')
fore_kvitto = (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.json').read_text()
kv = sk.kor_kontroll(SLUG, 'ny')
assert kv['status'] == 'stoppad' and any(s.startswith('mobbin') for s in kv['stoppar']), (kv['status'], kv['stoppar'])
assert 'STOPPAD' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO-STOPP.md').read_text() and kv['kvitto'].endswith('STARTKVITTO-STOPP.md')
assert (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.json').read_text() == fore_kvitto, 'körningens kvitto (låset en återupptagning ärver) står kvar'
kvb = sk.kor_kontroll(SLUG, 'bygge')
mob = next(r for r in kvb['rader'] if r['namn'] == 'mobbin')
assert kvb['status'] == 'begransad' and mob['resultat'] == 'fel' and not mob.get('nodvandig'), (kvb['status'], kvb['stoppar'], mob)
assert not next(r for r in kvb['rader'] if r['namn'] == 'kundvaktens mekanik').get('nodvandig')
atelje_kv = json.loads((KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO-STOPP.json').read_text())
assert atelje_kv['start'] == 'ny' and atelje_kv['status'] == 'stoppad', 'helbygget skriver inte över ateljéns kvitto'
assert json.loads((KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO-BYGGE.json').read_text())['start'] == 'bygge'
(FAKE / 'mcp').write_text(MCP_OK)
aldra('mcp:lista')
print('fall 4: nödvändig MCP som faller stoppar inom fem minuter; helbygget redovisar utan att stoppa, i eget kvitto ok')

# ett misslyckat förmågeprov återanvänds inte: en tjänst som varit nere en stund prövas om vid nästa start, i stället för
# att stoppa varje start i ett dygn
c_ = vl.Cache(vl.lagekatalog() / 'CACHE.json')
c_.d['prov:refero'].update(resultat='fel', detalj='tillfälligt nere')
vl.skriv_json(c_.fil, c_.d)
nollstall()
kv = sk.kor_kontroll(SLUG, 'ny')
assert ANROP['refero'] == 1 and next(r for r in kv['rader'] if r['namn'] == 'Refero (direkt)')['resultat'] == 'ok', ANROP
nollstall()
sk.kor_kontroll(SLUG, 'ny')
assert ANROP['refero'] == 0, 'ett lyckat prov återanvänds'
print('ett misslyckat förmågeprov prövas om vid nästa start ok')

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
# en gammal regel som når agenterna (här i en kunskapsfil) stoppar starten, med var den står
fil_s = KOPIA / 'kunskap' / 'designregler.md'
fore_s = fil_s.read_text()
fil_s.write_text(fore_s + '\nTelefonnumret som tel-länk i sidhuvudet på varje sida.\n')
kv = sk.kor_kontroll(SLUG, 'ny')
fil_s.write_text(fore_s)
styr = next(r_ for r_ in kv['rader'] if r_['namn'].startswith('gammal styrning'))
assert kv['status'] == 'stoppad' and styr['resultat'] == 'fel' and styr.get('nodvandig') and 'designregler.md' in styr['detalj'], styr
print('fall 2: ändrad skill utlöser metodkontrollen, och gammal styrning stoppar starten ok')

# fall 7: alla startvägar går genom kontrollen
import atelje  # noqa: E402
gamla = sk.for_start
REG_UNDER = []  # körregistret som startkontrollen ser det: arbetaren ska vara anmäld medan den går


def falsk_start(slug, lage):
    REG_UNDER.append([(d['vad'], d.get('slug'), d['pid']) for d in korregister.poster()])
    return {'status': 'stoppad', 'stoppar': ['mobbin: Failed to connect'], 'rader': [], 'tid': vl.nu(), 'start': lage}


sk.for_start = falsk_start
rot = KOPIA / 'underlag' / SLUG / 'atelje'
(rot / 'gammal-riktning').mkdir(parents=True, exist_ok=True)
anrop_aterkalla = []
atelje.aterkalla = lambda slug: anrop_aterkalla.append(slug)
rc = atelje.arbetare(SLUG, 'ny')
st = json.loads((rot / 'STATUS.json').read_text())
assert rc == 1 and st['steg'] == 'fel' and 'Startkontrollen stoppade starten' in st['fel'] and 'mobbin' in st['fel'], st
assert not anrop_aterkalla and (rot / 'gammal-riktning').is_dir() and not list(rot.glob('foregaende*')), 'inget arkiveras eller återkallas före kontrollen'
# en ny start som stoppas lämnar den förra körningens status och resultat, med stoppet (fynd 15)
(rot / 'STATUS.json').write_text(json.dumps({'slug': SLUG, 'steg': 'klar', 'klar': GAMMAL, 'lage': 'ny', 'faser': {'valj': {'klar': GAMMAL}}}))
rc = atelje.arbetare(SLUG, 'ny')
st = json.loads((rot / 'STATUS.json').read_text())
assert rc == 1 and st['steg'] == 'klar' and st['faser'] == {'valj': {'klar': GAMMAL}} and 'mobbin' in st['startkontroll_stopp']['fel'] and 'pid' not in st, st
assert REG_UNDER and all(x == [('arbetare', SLUG, os.getpid())] for x in REG_UNDER), REG_UNDER
assert not korregister.poster(), 'arbetaren tar bort sin post i körregistret när den slutar'
(rot / 'STATUS.json').unlink()
sk.for_start = gamla
kor = (KOPIA / 'kor.sh').read_text()
i_sk, i_inst, i_uchg = kor.index('kontroller/startkontroll.py'), kor.index('atelje.installera_godkand'), kor.index('chflags uchg "$ROOT/kunder"')
i_claude = kor.index('claude "${ARGS[@]}"')
assert i_sk < i_inst < i_uchg < i_claude, 'kor.sh: startkontrollen före installationen, låsningen och modellen'
assert 'atelje.main(' in (KOPIA / 'kontroller' / 'prototyp.py').read_text(), 'prototyp.py startar via ateljén'
assert "startkontroll.for_start(slug, lage)" in (KOPIA / 'kontroller' / 'atelje.py').read_text()
# kor.sh på riktigt: en trasig metod stoppar bygget i startkontrollen, före modellen, med kvittot för helbygget
skillfil = KOPIA / '.claude' / 'skills' / 'refero-design' / 'SKILL.md'
fore_skill = skillfil.read_text()
skillfil.write_text(fore_skill + '\nEn lokal ändring.\n')
fore_atelje = (rot / 'STARTKVITTO.json').read_text()
(FAKE / 'claude-anrop').write_text('')
env = dict(os.environ, NWP_STARTKONTROLL='torr', NWP_ATELJE='av')
sedd, vantade = None, False
with vl.las(korregister.BYTESLAS):  # ett pågående intag: kor.sh:s startkontroll väntar och säger till
    proc = subprocess.Popen(['bash', str(KOPIA / 'kor.sh'), SLUG, 'Provverksamhet, Umeå'], cwd=str(KOPIA), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=env)
    for _ in range(600):
        sedd = sedd or next((d for d in korregister.poster() if d['vad'] == 'bygge'), None)
        vantade = vantade or korregister.start_vantar()
        if (sedd and vantade) or proc.poll() is not None:
            break
        time.sleep(0.2)
ut_, fel_ = proc.communicate(timeout=600)
r = subprocess.CompletedProcess(proc.args, proc.returncode, ut_, fel_)
skillfil.write_text(fore_skill)
assert sedd and sedd['slug'] == SLUG and sedd['pid'] == proc.pid and vantade, ('kor.sh anmäler sig och väntar på intaget', sedd, vantade, ut_[-300:])
assert r.returncode == 2 and 'startkontrollen stoppade bygget' in r.stdout and 'STARTKVITTO-BYGGE-STOPP.md' in r.stdout, (r.returncode, r.stdout[-600:], r.stderr[-600:])
assert 'STOPPAD' in (rot / 'STARTKVITTO-BYGGE-STOPP.md').read_text() and (rot / 'STARTKVITTO.json').read_text() == fore_atelje
assert not [x for x in (FAKE / 'claude-anrop').read_text().splitlines() if x.startswith('-p') or ' -p ' in ' %s ' % x], 'ingen modell före startkontrollen'
assert not (KOPIA / 'kunder' / '.bygge-pid').exists() and not korregister.poster(), 'kor.sh städar låset och körregistret'
print('fall 7: arbetaren, kor.sh (på riktigt) och prototyp.py går genom startkontrollen ok')

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
NODE_MAL.update(major=24, version='24.21.0', datum={'24.21.0': '2026-01-01', '22.23.3': '2026-01-01', '22.23.2': '2025-12-01'})
k = vl.Kontext(nat=True, prova=False, max_alder=0)
nod = next(r for r in vl.inventera(k, ('brew',)) if r['id'] == 'brew:node')
BREW['node@22'] = '22.23.3_1'
nod = next(r for r in vl.inventera(k, ('brew',)) if r['id'] == 'brew:node')
assert [c['version'] for c in nod['kandidater']] == ['24.21.0_1', '22.23.3_1'] and nod['kandidater'][0]['huvudversion'], nod['kandidater']
BREWANROP, ROKPROV = [], []
uh.brew = lambda *a, timeout=0, **k_: (BREWANROP.append(a) or (0, str(FAKE)))
uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0, avbryt=None: (ROKPROV.append(etikett) or
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
# PATH pinnar den gamla formeln (ägarens skalprofil): den godkända huvudversionen behålls med skälet, ingen omlänkning,
# och provet återanvänds tills ägaren bytt raden (fynd 6)
ROKPROV.clear()
BREWANROP.clear()
uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0, avbryt=None: (ROKPROV.append(etikett) or
                                                                                               (True, 'hela rökprovet grönt i en egen worktree'))
pinnad = dict(nod, pinnad='/opt/homebrew/opt/node@22/bin', kandidater=[{'version': '24.23.0_1', 'formel': 'node@24', 'huvudversion': True}])
for varv in (1, 2):
    rap = {'rader': [], 'commits': []}
    uh.hantera(k, pinnad, rap)
    assert rap['rader'][0]['resultat'] == 'behallen' and 'PATH pinnar node@22' in rap['rader'][0]['detalj'], rap['rader']
    assert ROKPROV == ['brew:node-node@24'] and (varv == 1 or rap['rader'][0].get('prov_ateranvant')), (varv, ROKPROV, rap['rader'])
assert k.godkanda.for_version('brew:node', '24.23.0_1') and not any(a[0] == 'link' for a in BREWANROP), BREWANROP
# den behållna huvudversionen stoppar inte patchen inom den installerade (fynd 10)
BREWANROP.clear()
rap = {'rader': [], 'commits': []}
uh.hantera(k, dict(pinnad, kandidater=pinnad['kandidater'] + [{'version': '22.23.4', 'formel': 'node@22', 'huvudversion': False}]), rap)
assert [x['resultat'] for x in rap['rader']] == ['behallen', 'uppdaterad'] and ('upgrade', '--formula', 'node@22') in BREWANROP, rap['rader']
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
# git 3: en formel som byts på plats prövas med hela rökprovet efter bytet. En start som väntar avbryter provet: den förra
# kegen länkas tillbaka och versionen behålls (godkänd för omprövning), aldrig avvisad. Ett rött prov avvisar.
uh.verifiera_formel = lambda formel, version: None
ROKPROV.clear()
BREWANROP.clear()
uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0, avbryt=None: (
    ROKPROV.append((etikett, avbryt is not None)) or (False, uh.HALL + 'rökprovet avbröts: en start väntade; prövas igen vid nästa underhåll'))
rap = {'rader': [], 'commits': []}
uh.hantera(k, dict(git_rad, kandidater=[{'version': '3.0.0', 'formel': 'git', 'huvudversion': True}]), rap)
assert rap['rader'][0]['resultat'] == 'behallen' and 'avbröts' in rap['rader'][0]['detalj'] and 'återlänkad' in rap['rader'][0]['detalj'], rap['rader']
assert ROKPROV == [('brew:git', True)] and ('upgrade', '--formula', 'git') in BREWANROP and any(a[0] == 'ruby' and '2.55.0' in a[2] for a in BREWANROP)
assert not k.avvisade.for_version('brew:git', '3.0.0') and k.godkanda.for_version('brew:git', '3.0.0')
uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0, avbryt=None: (False, 'rökprovet rött (kod 1): FEL: git 3 bröt worktree')
rap = {'rader': [], 'commits': []}
uh.hantera(k, dict(git_rad, kandidater=[{'version': '3.0.1', 'formel': 'git', 'huvudversion': True}]), rap)
assert rap['rader'][0]['resultat'] == 'avvisad' and 'git 3 bröt' in rap['rader'][0]['detalj'] and 'återlänkad' in rap['rader'][0]['detalj'], rap['rader']
# ett trasigt bibliotek efter en uppgradering installeras om och prövas igen (brew linkage --test; fynd 7)
LANK = {'trasiga': {'node@22'}}


def f_brew_lank(*a, timeout=0, **k_):
    BREWANROP.append(a)
    if a[:2] == ('linkage', '--test'):
        return (1, 'Broken dependencies: libsimdjson') if a[2] in LANK['trasiga'] else (0, '')
    if a[0] == 'reinstall':
        LANK['trasiga'].discard(a[-1])
    return 0, str(FAKE)


uh.brew = f_brew_lank
BREW['node@22'] = '22.23.2_1'  # en ombyggnad av samma version (ny revision): ominstallationen byter ingen version
fel_, lagade_ = uh.laga_lankar()
assert fel_ is None and lagade_ == ['node@22'] and ('reinstall', '--formula', 'node@22') in BREWANROP, (fel_, lagade_)
# en ominstallation som skulle byta den aktiva nodens version utan prov görs aldrig (2026-10-06: node@22 22.23.2 hade
# blivit 22.23.3_1); felet säger vad och varför, och den trasiga formeln lämnas åt ägaren
BREW['node@22'] = '22.23.3_1'
LANK['trasiga'] = {'node@22'}
BREWANROP.clear()
fel_, lagade_ = uh.laga_lankar()
assert fel_ and 'byta version utan prov' in fel_ and 'node@22 22.23.2 → 22.23.3_1' in fel_ and lagade_ == [], (fel_, lagade_)
assert not any(a[0] == 'reinstall' for a in BREWANROP), BREWANROP
spara_info_l4 = vl.brew_info
vl.brew_info = lambda f: None  # indexet svarar inte: räknas som ett byte, ingen ominstallation
fel_, lagade_ = uh.laga_lankar()
vl.brew_info = spara_info_l4
assert fel_ and 'okänd version' in fel_ and lagade_ == [] and not any(a[0] == 'reinstall' for a in BREWANROP), (fel_, BREWANROP)
LANK['trasiga'] = set()
LANK['trasiga'] = {'gh', 'git'}
uh.brew = lambda *a, timeout=0, **k_: (BREWANROP.append(a) or ((1, 'trasig') if a[:2] == ('linkage', '--test') and a[2] == 'gh' else (0, str(FAKE))))
fel_, lagade_ = uh.laga_lankar()
assert fel_ and 'gh' in fel_ and lagade_ == ['gh'], (fel_, lagade_)
uh.brew = lambda *a, timeout=0, **k_: (BREWANROP.append(a) or (0, str(FAKE)))
print('avvisad huvudversion, intagen patch, ingen omprövning av samma version, återlänkning, pinnad node, git 3 och länkprovet ok')

# 2026-10-06: intaget av node@24 bredvid uppgraderade simdjson, och node@22, som PATH pinnar, startade inte; varje start
# hängde i kärnan, och underhållet fastnade i länkprovets node --version. Fyra skydd:
# (1) länkprovet bestämmer node-formeln ur sökvägen och startar aldrig node
cell_l1 = TMP / 'l1' / 'Cellar' / 'node@22' / '22.23.2' / 'bin'
cell_l1.mkdir(parents=True)
(cell_l1 / 'node').write_text('#!/bin/bash\ntouch %s\necho v22.23.2\n' % (TMP / 'l1' / 'STARTAD'))
(cell_l1 / 'node').chmod(0o755)
(TMP / 'l1' / 'bin').mkdir()
os.symlink(cell_l1 / 'node', TMP / 'l1' / 'bin' / 'node')
spara_l1 = (os.environ['PATH'], vl.node_formel_ur_vag, uh.brew, vl.node_formel)
os.environ['PATH'] = '%s:%s' % (TMP / 'l1' / 'bin', os.environ['PATH'])
vl.node_formel_ur_vag, vl.node_formel = NODE_UR_VAG, NODE_FORMEL  # båda riktiga: ett länkprov som startade node syns
BREWANROP.clear()
uh.brew = lambda *a, timeout=0, **k_: (BREWANROP.append(a) or (0, ''))
try:
    assert vl.node_formel_ur_vag() == 'node@22' and uh.lankprov() == []
    assert ('linkage', '--test', 'node@22') in BREWANROP and not (TMP / 'l1' / 'STARTAD').exists(), ('node startades', BREWANROP)
finally:
    os.environ['PATH'], vl.node_formel_ur_vag, uh.brew, vl.node_formel = spara_l1
# (2) kor väntar inte obegränsat på en process som inte går att avsluta: dödandet biter inte (som en krasch som väntar
#     på krashrapporteringen), och kor går vidare med ett fel
spara_l2 = (vl.avsluta_trad, vl.SLUTVANTAN)
vl.avsluta_trad = lambda pid: None
vl.SLUTVANTAN = 1
pidfil_l2 = TMP / 'l2.pid'
t_l2 = time.time()
try:
    rc_l2, ut_l2 = vl.kor([sys.executable, '-c', 'import os, time; open(%r, "w").write(str(os.getpid())); time.sleep(60)' % str(pidfil_l2)], timeout=2)
finally:
    vl.avsluta_trad, vl.SLUTVANTAN = spara_l2
    try:
        os.kill(int(pidfil_l2.read_text()), 9)
    except (OSError, ValueError):
        pass
assert rc_l2 == 124 and 'avslutades inte' in ut_l2 and time.time() - t_l2 < 10, (rc_l2, ut_l2, time.time() - t_l2)
# (3) en ny huvudversion installeras inte bredvid när Homebrews torrkörning säger att installationen skulle uppgradera
#     något som den aktiva node eller python@3.12, git och gh länkar mot (deras installerade kegars körtidsberoenden)
L3 = {'torr_rc': 0, 'torr': '', 'info': None, 'trasiga': set(), 'efter_install_trasiga': set(), 'installerad': False}
TORR_L3 = """==> Would install 1 formula:
node@24 24.21.0_1
==> Would upgrade 3 dependencies for node@24:
simdjson  4.6.6 -> 5.0.2
uvwasi    0.0.21 -> 0.0.22
==> Would install 2 dependencies for node@24:
hdrhistogram_c 0.11.9
uvwasi 0.0.23
\x1b[34m==>\x1b[0m \x1b[1mWould upgrade 1 dependency for node@24:\x1b[0m
homebrew/core/sqlite 3.50.1 -> 3.50.2
"""  # den färgade rubriken efter ett installationsblock: bara den som tar bort färgkoderna ser sqlite
SKYDD_L3 = {'formulae': [{'name': 'node@22', 'installed': [{'runtime_dependencies': [{'full_name': 'simdjson'}, {'full_name': 'icu4c@78'}]}]},
                         {'name': 'python@3.12', 'installed': [{'runtime_dependencies': [{'full_name': 'sqlite'}, {'full_name': 'openssl@3'}]}]},
                         {'name': 'git', 'installed': [{'runtime_dependencies': []}]}, {'name': 'gh', 'installed': []}]}


def f_brew_l3(*a, timeout=0, **k_):
    BREWANROP.append(a)
    if a[:3] == ('install', '--dry-run', '--formula'):
        return L3['torr_rc'], L3['torr']
    if a[:2] == ('info', '--json=v2'):  # som Homebrew: en varning på stderr, som bara den som läser stdout för sig slipper
        ut_ = L3['info'] if L3['info'] is not None else json.dumps(SKYDD_L3)
        return 0, ut_ if k_.get('bara_ut') else ut_ + '\nWarning: formeln har en ny revision'
    if a[:2] == ('linkage', '--test'):
        trasiga = L3['trasiga'] | (L3['efter_install_trasiga'] if L3['installerad'] else set())
        return (1, 'Broken dependencies') if a[2] in trasiga else (0, '')
    if a[:2] == ('install', '--formula'):
        L3['installerad'] = True
    if a[:2] == ('--prefix', 'node@24'):
        return 0, str(FAKE)
    return 0, ''


def node24_l3(katalog):
    BREWANROP.clear()
    L3['installerad'] = False
    return uh.prova_node_huvud(vl.Kontext(nat=False, prova=False, katalog=TMP / katalog), {'id': 'brew:node'},
                               {'version': '24.21.0_1', 'formel': 'node@24', 'huvudversion': True})[0]


spara_l3 = (uh.brew, uh.rokprov_i_worktree)
uh.brew = f_brew_l3
uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0, avbryt=None: (True, 'hela rökprovet grönt i en egen worktree')
installerades = lambda: ('install', '--formula', 'node@24') in BREWANROP  # noqa: E731
try:
    L3['torr'] = TORR_L3
    fel_l3 = node24_l3('lage-l3')
    assert fel_l3.startswith(uh.HALL) and 'simdjson 4.6.6 -> 5.0.2' in fel_l3 and 'sqlite 3.50.1 -> 3.50.2' in fel_l3, fel_l3
    assert 'uvwasi' not in fel_l3 and 'hdrhistogram' not in fel_l3 and not installerades(), (fel_l3, BREWANROP)
    # en varning på stderr ändrar inget (bara stdout läses), och uppgraderingar som inget skyddat länkar mot stoppar inte
    L3['torr'] = '==> Would upgrade 1 dependency for node@24:\nuvwasi 0.0.21 -> 0.0.22\n'
    assert node24_l3('lage-l3b') is None and installerades(), BREWANROP
    # en formel som redan är installerad och aktuell: torrkörningen säger inget, och installationen gör inget
    L3['torr'] = ''
    assert node24_l3('lage-l3c') is None and installerades()
    # går det inte att avgöra (torrkörningen faller, de skyddade beroendena går inte att läsa) installeras inget
    L3['torr_rc'], L3['torr'] = 1, 'Error: Unexpected'
    fel_l3d = node24_l3('lage-l3d')
    assert fel_l3d.startswith(uh.HALL) and 'gick inte att avgöra' in fel_l3d and not installerades(), fel_l3d
    L3['torr_rc'], L3['torr'], L3['info'] = 0, TORR_L3, 'Warning: ingen json'
    fel_l3e = node24_l3('lage-l3e')
    assert fel_l3e.startswith(uh.HALL) and 'gick inte att avgöra' in fel_l3e and not installerades(), fel_l3e
    L3['info'] = None
    # en aktiv node som redan är trasig före intaget: inget installeras och ingen torrkörning, så att patchintaget når den
    L3['trasiga'] = {'node@22'}
    fel_l3f = node24_l3('lage-l3f')
    assert fel_l3f.startswith(uh.HALL) and 'redan trasiga' in fel_l3f and not any(x[0] == 'install' for x in BREWANROP), (fel_l3f, BREWANROP)
    L3['trasiga'] = set()
    # (4) efter installationen prövas att den aktiva node fortfarande svarar; gör den inte det är miljön trasig
    L3['torr'] = ''
    spara_nod_l4 = (FAKE / 'bin' / 'node').read_text()
    (FAKE / 'bin' / 'node').write_text('#!/bin/bash\ntouch %s\nexit 1\n' % (TMP / 'l4-startad'))
    try:
        fel_l4 = node24_l3('lage-l4')
        assert installerades() and fel_l4.startswith('MILJÖN TRASIG') and 'den aktiva node' in fel_l4, fel_l4
        # har länkprovet redan sagt att den aktiva node är trasig startas den inte (den kraschar och kan hänga)
        (TMP / 'l4-startad').unlink()
        L3['efter_install_trasiga'] = {'node@22'}
        BREW['node@22'] = '22.23.3_1'
        fel_l4b = node24_l3('lage-l4b')
        assert fel_l4b.startswith('MILJÖN TRASIG') and 'byta version utan prov' in fel_l4b and not (TMP / 'l4-startad').exists(), fel_l4b
        L3['efter_install_trasiga'] = set()
    finally:
        (FAKE / 'bin' / 'node').write_text(spara_nod_l4)
finally:
    uh.brew, uh.rokprov_i_worktree = spara_l3
# kor säger avbrutet (och AVBRUTEN) när ett avbrott lämnar en process som inte går att avsluta
spara_l2b = (vl.avsluta_trad, vl.SLUTVANTAN)
vl.avsluta_trad = lambda pid: None
vl.SLUTVANTAN = 1
pidfil_l2b = TMP / 'l2b.pid'
try:
    rc_l2b, ut_l2b = vl.kor([sys.executable, '-c', 'import os, time; open(%r, "w").write(str(os.getpid())); time.sleep(60)' % str(pidfil_l2b)],
                            timeout=30, avbryt=lambda: True)
finally:
    vl.avsluta_trad, vl.SLUTVANTAN = spara_l2b
    try:
        os.kill(int(pidfil_l2b.read_text()), 9)
    except (OSError, ValueError):
        pass
assert rc_l2b == vl.AVBRUTEN and ut_l2b.startswith('avbrutet'), (rc_l2b, ut_l2b)
print('2026-10-06: länkprovet utan node, kor utan obegränsad väntan, delade beroenden och den aktiva node efter installationen ok')

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
    assert not (vl.lagekatalog() / 'UNDERHALL.json').exists(), 'ett uppskjutet underhåll ersätter inte rapporten från det senaste som kördes'
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
sh(*GIT, 'commit', '-q', '-m', 'bas', cwd=upp, env=gammal_git())
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
sh(*GIT, 'commit', '-q', '-am', 'uppdatering', cwd=upp, env=gammal_git())
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
sh(*GIT, 'commit', '-q', '-am', 'krock', cwd=upp, env=gammal_git())
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

# karenstiden: källans senaste commit är för färsk, och den senaste mogna (krocken) är redan avvisad; skillen behålls,
# och den färska commiten avvisas inte (fynd 4, och granskningen av r72, M5)
(upp / 'skills' / 'demo' / 'ref.md').write_text('Referens, nyast.\n')
sh(*GIT, 'commit', '-q', '-am', 'färsk', cwd=upp)
head3 = sh('git', 'rev-parse', 'HEAD', cwd=upp).strip()
vl.git_head = lambda repo: head3 if 'demo-skill' in repo else None
k = vl.Kontext(nat=True, prova=False, max_alder=0)
demo_rad = next(r for r in vl.inventera(k, ('skills',)) if r['id'] == 'skill:demo')
rap = {'rader': [], 'commits': []}
uh.hantera(k, demo_rad, rap)
assert rap['rader'][0]['resultat'] == 'behallen' and 'mogna' in rap['rader'][0]['detalj'] and not k.avvisade.for_version('skill:demo', head3), rap['rader']

# npm: den senaste inom huvudversionen är en egen kandidat, och en version i karenstiden räknas inte (fynd 4 och 10)
TIDER['vercel'] = {'60.2.0': GAMMAL, '62.4.0': GAMMAL, '62.5.0': vl.nu()}
NPM['vercel'] = '62.5.0'
k_ = vl.Kontext(nat=True, prova=False, katalog=TMP / 'lage-vercel')
rv = next(r for r in vl.inventera(k_, ('globala',)) if r['id'] == 'npm-global:vercel')
assert [c['version'] for c in rv['kandidater']] == ['62.4.0', '60.2.0'] and rv['kandidater'][0]['huvudversion'] and rv['i_karens'] == '62.5.0', rv
assert not rv['kandidater'][1]['huvudversion']
TIDER.pop('vercel')
NPM['vercel'] = '60.0.1'
# ett gammalt uppslag är okänt, aldrig grönt (fynd 9)
r_ = vl.bedom({'id': 'x', 'installerat': '1.0.0', 'senaste': '1.0.0', 'kandidater': [], 'kontrollerad': GAMMAL}, k_.avvisade)
assert r_['resultat'] == 'okand' and '36 timmar' in r_['detalj'], r_
# ett nätsteg som faller av ett tillfälligt skäl avvisar inget, och nästa kandidat får chansen (fynd 10)
assert uh.nat('npm error code ETIMEDOUT').startswith(uh.TILL) and uh.nat('getaddrinfo ENOTFOUND registry.npmjs.org').startswith(uh.TILL)
assert uh.nat('HTTP Error 503: Service Unavailable').startswith(uh.TILL) and uh.nat(uh.HALL + 'x') == uh.HALL + 'x'
assert not uh.nat('npm audit (high eller kritisk): sårbarhet i foo@1.503.2').startswith(uh.TILL)
k_ = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-till')
uh.PROVA['npm-global'] = lambda k, r, kand: ((uh.nat('npm error code ETIMEDOUT: registry.npmjs.org'), None) if kand['version'] == '62.4.0'
                                             else (None, {'prov': 'falskt prov'}))
uh.TA_IN['npm-global'] = lambda k, r, kand, staged: ('uppdaterad', 'falskt intag', None)
v2 = {'id': 'npm-global:vercel', 'namn': 'Vercel CLI', 'grupp': 'leverans', 'typ': 'npm-global', 'installerat': '60.0.1',
      'kandidater': [{'version': '62.4.0', 'huvudversion': True}, {'version': '60.2.0', 'huvudversion': False}]}
rap = {'rader': [], 'commits': []}
uh.hantera(k_, v2, rap)
assert [x['resultat'] for x in rap['rader']] == ['behallen', 'uppdaterad'] and rap['rader'][0]['detalj'].startswith('tillfälligt fel'), rap['rader']
assert not k_.avvisade.for_version('npm-global:vercel', '62.4.0')
# en skilluppdatering som ger behörigheter, krokar eller ändrar ett skript som flödet kör tas aldrig in (fynd 1)
a_, b_ = TMP / 'kansliga-a', TMP / 'kansliga-b'
for d_ in (a_, b_):
    (d_ / 'scripts').mkdir(parents=True)
(a_ / 'SKILL.md').write_text('---\nname: x\ndescription: y\n---\nText.\n')
(b_ / 'SKILL.md').write_text('---\nname: x\ndescription: y, bättre\nallowed-tools: Bash(curl:*)\n---\nText.\n')
(b_ / 'hooks.json').write_text('{}')
(a_ / 'scripts' / 'sok.py').write_text('print(1)\n')
(b_ / 'scripts' / 'sok.py').write_text('print(2)\n')
k1 = uh.kansliga_andringar(a_, b_, 'ui-ux-pro-max')
assert any('allowed-tools' in x for x in k1) and any('hooks.json' in x for x in k1) and any('scripts/sok.py' in x for x in k1), k1
assert not any('description' in x for x in k1) and uh.kansliga_andringar(a_, a_, 'ui-ux-pro-max') == []
assert not any('sok.py' in x for x in uh.kansliga_andringar(a_, b_, 'annan-skill')), 'bara skript som flödet kör'
# metodens radutdrag får inte flyttas tyst av en uppdatering; hela filer och avsnitt följer innehållet (fynd 5)
import metod  # noqa: E402
import re as re_  # noqa: E402
rader_ = sorted({r for rubrik in metod.STEG.values() for d in ('före', 'varv', 'uppslag')
                 for r in metod.stegets_rader(metod.tolka(metod.KARTA.read_text(encoding='utf-8')), rubrik, d)})
rad_ = next(r for r in rader_ if re_.search(r'\srad \d', r))
hel_ = next(r for r in rader_ if ' ' not in r and r.split('/')[0] != rad_.split('/')[0])
t_ = TMP / 'metodkopia'
uh.repokopia_for_metod(t_)
f_ = t_ / '.claude' / 'skills' / rad_.split()[0]
f_.write_text('En ny inledning.\n\n' + f_.read_text())
assert rad_ in uh.utdrag_som_andras(t_, rad_.split('/')[0]), (rad_, uh.utdrag_som_andras(t_, rad_.split('/')[0]))
g_ = t_ / '.claude' / 'skills' / hel_
g_.write_text(g_.read_text() + '\nEn rad till.\n')
assert uh.utdrag_som_andras(t_, hel_.split('/')[0]) == [], hel_
# en incheckning som faller lägger tillbaka filerna, och intaget behålls till nästa underhåll (fynd 8)
spar_ = TMP / 'sajt-spar'
sokv_ = ['mall/astro/package.json', 'mall/astro/package-lock.json', 'mall/leverans/package.json', 'mall/leverans/package-lock.json']
fore_ = {f: (KOPIA / f).read_bytes() for f in sokv_}
for f in sokv_:
    m_ = spar_ / f.split('/', 1)[1]
    m_.parent.mkdir(parents=True, exist_ok=True)
    m_.write_bytes(fore_[f] + b'\n')
(KOPIA / '.git' / 'index.lock').write_text('')
try:
    res_, detalj_, commit_ = uh.ta_in_sajt(k, {'installerat': '5.0.0'}, {'version': '5.1.0'}, {'mapp': str(spar_), 'prov': 'prov'})
finally:
    (KOPIA / '.git' / 'index.lock').unlink()
assert res_ == 'behallen' and 'incheckningen föll' in detalj_ and 'återställda' in detalj_ and commit_ is None, (res_, detalj_)
assert all((KOPIA / f).read_bytes() == b for f, b in fore_.items()) and not sh('git', 'status', '--porcelain', '--', 'mall').strip()
# startkontrollen väntar på ett pågående intag och säger till underhållet att den väntar; är intaget inte klart stoppas
# starten (fynd 2)
import threading  # noqa: E402
res_ = {}
with vl.las(korregister.BYTESLAS):
    tr_ = threading.Thread(target=lambda: res_.update(kv=sk.kor_kontroll(SLUG, 'ny', vanta_intag=4)))
    tr_.start()
    for _ in range(50):
        if korregister.start_vantar():
            break
        time.sleep(0.1)
    vantade = korregister.start_vantar()
    tr_.join()
assert vantade and res_['kv']['status'] == 'stoppad' and any(x.startswith('intag') for x in res_['kv']['stoppar']), res_['kv']['stoppar']
assert not korregister.start_vantar()
# förmågeprovens förutsättningar: ett ändrat inspektionsverktyg och en ny motor gör om proven (fynd 14)
a1 = vl.webblasar_avtryck()
insp = KOPIA / 'kontroller' / 'webblasare' / 'inspektera.mjs'
fore_i = insp.read_text()
insp.write_text(fore_i + '\n// ändrad\n')
assert vl.webblasar_avtryck() != a1
insp.write_text(fore_i)
assert vl.webblasar_avtryck() == a1
import detektor  # noqa: E402
spara_d = (detektor.motor, detektor.detektera)
try:
    detektor.detektera = lambda f: ([], None)
    k_ = vl.Kontext(nat=False, prova=True, katalog=TMP / 'lage-detektor')
    detektor.motor = lambda: Path('/x/0.1.10/impeccable')
    assert not riktig_detektor(k_, k_.prov_dir).get('ateranvant') and riktig_detektor(k_, k_.prov_dir).get('ateranvant')
    detektor.motor = lambda: Path('/x/0.1.11/impeccable')
    assert not riktig_detektor(k_, k_.prov_dir).get('ateranvant'), 'en ny motor prövas om'
finally:
    detektor.motor, detektor.detektera = spara_d
print('karenstid, kandidat inom huvudversionen, gammalt uppslag, tillfälliga fel, känsliga skilländringar, metodens utdrag, '
      'incheckning som faller, intagslåset och provens förutsättningar ok')

# ===== granskningen av r72: ett fall per fynd, som går rött om felet kommer tillbaka =====
# H1: ett nytt mätinstrument prövas med sin egen version i worktreen, inte HEAD:s
spara_h1 = (uh.npm, uh.audit, uh.installera_instrument, uh.rokprov_i_worktree)
try:
    sett_h1 = {}
    uh.npm = lambda args, cwd, timeout=900, env=None: (0, '')
    uh.audit = lambda cwd, **kw: None

    def f_installera(kontr):
        sett_h1['pin'] = json.loads((Path(kontr) / 'package.json').read_text())['dependencies'].get('axe-core')
        (Path(kontr) / 'node_modules' / 'axe-core').mkdir(parents=True, exist_ok=True)
        (Path(kontr) / 'node_modules' / 'axe-core' / 'package.json').write_text(json.dumps({'version': sett_h1['pin']}))
        return None
    uh.installera_instrument = f_installera
    wt_h1 = TMP / 'h1-wt'
    (wt_h1 / 'kontroller').mkdir(parents=True)
    for f_ in ('package.json', 'package-lock.json'):
        shutil.copy2(KOPIA / 'kontroller' / f_, wt_h1 / 'kontroller' / f_)
    uh.rokprov_i_worktree = lambda k, etikett, forbered, path_forst=None, timeout=0, avbryt=None: ((lambda f_: (f_ is None, f_ or 'grönt'))(forbered(wt_h1)))
    fel_h1, staged_h1 = uh.prova_instrument(vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-h1'), {'id': 'instrument:axe-core', 'namn': 'axe-core'},
                                            {'version': '9.9.9'})
    assert fel_h1 is None and sett_h1['pin'] == '9.9.9', ('worktreen installerade kandidaten', fel_h1, sett_h1)
finally:
    uh.npm, uh.audit, uh.installera_instrument, uh.rokprov_i_worktree = spara_h1

# H2: körregistrets identitet är processens starttid under LC_ALL=C: en körning med å, ä och ö i argumenten, anmäld
# under en locale, syns under en annan; en död körning tas bort; en körning i en annan utcheckning syns i pagaende()
proc_h2 = subprocess.Popen(['/bin/bash', '-c', 'sleep 60', 'kor.sh', 'Frisör Exempel, Umeå'])
try:
    bas_env = {k_: v_ for k_, v_ in os.environ.items() if not k_.startswith('LC_') and k_ != 'LANG'}
    sh(sys.executable, '-B', KOPIA / 'kontroller' / 'korregister.py', 'in', 'bygge', '--slug', 'frisor-umea', '--pid', str(proc_h2.pid),
       env=dict(bas_env, LC_ALL='C'))
    for env_h2 in (dict(bas_env, LANG='sv_SE.UTF-8'), dict(bas_env, LC_ALL='en_US.UTF-8'), dict(bas_env, LC_ALL='C')):
        ut_h2 = sh(sys.executable, '-B', KOPIA / 'kontroller' / 'korregister.py', 'lista', env=env_h2)
        assert 'frisor-umea' in ut_h2, ('posten står kvar oavsett locale', env_h2.get('LANG'), env_h2.get('LC_ALL'), ut_h2)
    post_h2 = json.loads((korregister.KATALOG / ('%d.json' % proc_h2.pid)).read_text())
    assert post_h2['pstart'] and post_h2['utcheckning'] == str(KOPIA)
    post_h2['utcheckning'] = '/en/annan/utcheckning'
    (korregister.KATALOG / ('%d.json' % proc_h2.pid)).write_text(json.dumps(post_h2))
    assert any('frisor-umea' in x and '/en/annan/utcheckning' in x for x in vl.pagaende()), vl.pagaende()
finally:
    proc_h2.kill()
    proc_h2.wait()
assert not korregister.poster(), 'en död körning tas bort ur registret'

# M1: ett misslyckat Mobbin-prov görs om vid ateljéns nästa start; helbygget gör det aldrig
import referenstjanster as rt_m1  # noqa: E402
spara_m1 = rt_m1.samla
MOBB_M1 = []
rt_m1.samla = lambda slug, uppdrag, underlag=None, **kw: (MOBB_M1.append(slug) or (None, {'tjanster': {'mobbin': {'ok': True, 'bilder': 2}}}))
try:
    c_ = vl.Cache(vl.lagekatalog() / 'CACHE.json')
    c_.d['prov:mobbin'].update(resultat='fel', detalj='nere i går')
    vl.skriv_json(c_.fil, c_.d)
    kvb_m1 = sk.kor_kontroll(SLUG, 'bygge')
    assert not MOBB_M1, 'helbygget gör inget Mobbin-prov'
    kv_m1 = sk.kor_kontroll(SLUG, 'ny')
    assert MOBB_M1 == ['startprov'] and next(r_ for r_ in kv_m1['rader'] if r_['namn'] == 'Mobbin (sökning och bilder)')['resultat'] == 'ok', MOBB_M1
finally:
    rt_m1.samla = spara_m1

# M2: Node-huvudversionens installation väntar på pågående körningar; dess godkännande beror inte på node@22:s patch
proc_m2 = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)', 'atelje.py', 'm2-kund', '--arbetare'])
try:
    korregister.registrera('arbetare', 'm2-kund', pid=proc_m2.pid)
    BREWANROP.clear()
    fel_m2, _s = uh.prova_node_huvud(vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-m2'), {'id': 'brew:node'},
                                     {'version': '24.23.0_1', 'formel': 'node@24', 'huvudversion': True})
    assert fel_m2.startswith(uh.HALL) and 'körning pågår' in fel_m2 and not any(a[0] == 'install' for a in BREWANROP), (fel_m2, BREWANROP)
finally:
    proc_m2.kill()
    proc_m2.wait()
    korregister.avregistrera(proc_m2.pid)
major_m2 = {'huvudversion': True, 'formel': 'node@24'}
assert uh.utgangslage(dict(nod, installerat='22.23.2'), major_m2) == uh.utgangslage(dict(nod, installerat='22.23.4'), major_m2)

# M3: omlåsningen låser aldrig om över en olåst ändring, och en skills godkännande gäller kartan det prövades mot
skillfil_m3 = KOPIA / '.claude' / 'skills' / 'refero-design' / 'SKILL.md'
fore_m3 = skillfil_m3.read_text()
skillfil_m3.write_text(fore_m3 + '\nEn incheckad men olåst ändring.\n')
sh(*GIT, 'commit', '-q', '-am', 'olåst ändring')
try:
    res_m3, detalj_m3, _c = uh.ta_in_skill(vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-m3'), demo_rad, demo_rad['kandidater'][0],
                                           {'mapp': str(demo), 'head': 'x' * 40, 'filer': 1, 'krockar': [], 'prov': 'prov'})
    assert res_m3 == 'behallen' and 'metodlåset stämmer inte' in detalj_m3, (res_m3, detalj_m3)
finally:
    skillfil_m3.write_text(fore_m3)
    sh(*GIT, 'commit', '-q', '-am', 'tillbaka')
a_m3 = uh.utgangslage(demo_rad)
karta_m3 = KOPIA / 'kunskap' / 'metodkarta.md'
fore_karta = karta_m3.read_text()
karta_m3.write_text(fore_karta + '\n')
assert uh.utgangslage(demo_rad) != a_m3, 'en ändrad metodkarta gör om skillens prov'
karta_m3.write_text(fore_karta)

# M4: tillfälliga fel som de ser ut på macOS, i pip och i Claudes gränser; en verklig sårbarhet är aldrig tillfällig
for f_m4 in ('hämtningen föll: <urlopen error [Errno 8] nodename nor servname provided, or not known>',
             'hämtningen föll: <urlopen error [Errno 61] Connection refused>', 'hämtningen föll: <urlopen error [Errno 65] No route to host>',
             "install föll: WARNING: Retrying after connection broken by 'NewConnectionError(...: Failed to establish a new connection')",
             'modellprovet (strukturerat svar, x): inget svar inom 240 s', 'modellprovet: svarade inte som väntat (kod 1): Claude AI usage limit reached|1791234567',
             'modellprovet: svarade inte som väntat (kod 1): 5-hour limit reached ∙ resets 3am'):
    assert uh.nat(f_m4).startswith(uh.TILL), f_m4
assert not uh.nat('den globala installationen föll (ETIMEDOUT); ÅTERSTÄLLNINGEN FÖLL: x').startswith(uh.TILL), 'en trasig miljö är aldrig tillfällig'
spara_kor_m4 = vl.kor
try:
    vl.kor = lambda args, **kw: (1, json.dumps({'vulnerabilities': {'foo': {'severity': 'high', 'via': ['ReDoS via timeout']}}}))
    assert uh.audit(TMP) == 'npm audit (high eller kritisk): foo (high)', uh.audit(TMP)
    vl.kor = lambda args, **kw: (1, json.dumps({'error': {'code': 'ENOTFOUND', 'summary': 'request to https://registry.npmjs.org failed'}}))
    assert uh.audit(TMP).startswith(uh.TILL), uh.audit(TMP)
    # jämförelsen med den installerade versionen, advisory för advisory: kända sårbarheter som redan finns där stoppar
    # inte en uppdatering, en ny gör det (Vercel CLI 2026-10-06: varje version hade samma kända sårbarheter i sina
    # beroenden; granskningen av r76, H1 och M1)
    def sv_r76(*adv, kedja=()):
        """npm audits form: advisoryn står i via hos sitt paket, och varje paket i kedjan får kedjans högsta allvar."""
        v_ = {}
        for namn_, id_, allvar_ in adv:
            e_ = v_.setdefault(namn_, {'name': namn_, 'severity': allvar_, 'via': []})
            e_['via'].append({'source': 1000 + len(e_['via']), 'name': namn_, 'dependency': namn_, 'title': 't',
                              'url': 'https://github.com/advisories/GHSA-' + id_, 'severity': allvar_, 'range': '*'})
            e_['severity'] = 'critical' if 'critical' in (allvar_, e_['severity']) else allvar_
        for namn_, via_ in kedja:
            v_[namn_] = {'name': namn_, 'severity': 'critical' if any(v_[x]['severity'] == 'critical' for x in via_) else 'high', 'via': list(via_)}
        return v_
    SVAR_A = {}
    vl.kor = lambda args, cwd=None, **kw: (1 if SVAR_A[str(cwd)] else 0, json.dumps({'vulnerabilities': SVAR_A[str(cwd)]}))
    BAS_A = sv_r76(('tar', 'a', 'critical'), ('tar', 'b', 'high'), ('braces', 'c', 'high'), kedja=[('vercel', ['tar'])])
    SVAR_A[str(TMP / 'kand')] = BAS_A
    SVAR_A[str(TMP / 'bas')] = dict(BAS_A, **sv_r76(('gammal', 'd', 'high')))
    noter_a = []
    assert uh.audit(TMP / 'kand', bas=TMP / 'bas', noter=noter_a) is None and 'inga nya sårbarheter' in noter_a[0], noter_a
    SVAR_A[str(TMP / 'bas')] = sv_r76(('braces', 'c', 'high'))
    assert uh.audit(TMP / 'kand', bas=lambda: TMP / 'bas') == \
        'npm audit: nya sårbarheter (high eller kritisk) jämfört med den installerade: tar GHSA-a (critical), tar GHSA-b (high)', uh.audit(TMP / 'kand', bas=TMP / 'bas')
    assert uh.audit(TMP / 'kand') == 'npm audit (high eller kritisk): braces GHSA-c (high), tar GHSA-a (critical), tar GHSA-b (high)', 'utan jämförelse avvisas de kända'
    SVAR_A[str(TMP / 'bas')] = {}  # den installerade har inga: alla kandidatens är nya
    assert uh.audit(TMP / 'kand', bas=TMP / 'bas').startswith('npm audit: nya sårbarheter'), uh.audit(TMP / 'kand', bas=TMP / 'bas')
    # en ny advisory mot ett paket som redan står med samma allvar (vercel i kedjan, tar som kritisk) är ny (H1)
    SVAR_A[str(TMP / 'bas')] = BAS_A
    for paket_, id_, allvar_ in (('vercel', 'e', 'high'), ('tar', 'f', 'critical')):
        k_ = json.loads(json.dumps(BAS_A))
        k_[paket_]['via'].append({'source': 9, 'name': paket_, 'dependency': paket_, 'title': 'ny', 'url': 'https://github.com/advisories/GHSA-' + id_,
                                  'severity': allvar_, 'range': '*'})
        SVAR_A[str(TMP / 'kand')] = k_
        assert uh.audit(TMP / 'kand', bas=TMP / 'bas') == \
            'npm audit: nya sårbarheter (high eller kritisk) jämfört med den installerade: %s GHSA-%s (%s)' % (paket_, id_, allvar_), uh.audit(TMP / 'kand', bas=TMP / 'bas')
    # en uppdatering som rättar tars kritiska och lämnar en känd high är ingen ny sårbarhet (M1)
    SVAR_A[str(TMP / 'kand')] = sv_r76(('tar', 'b', 'high'), ('braces', 'c', 'high'), kedja=[('vercel', ['tar'])])
    noter_a = []
    assert uh.audit(TMP / 'kand', bas=TMP / 'bas', noter=noter_a) is None and 'tar GHSA-b (high)' in noter_a[0], noter_a
    # den installerade går inte att granska: kandidaten avvisas inte (BEHÅLLEN, eller TILLFÄLLIGT för ett nätfel), och
    # skälet står i beskedet (M2); bara skälet avgör, aldrig kandidatens advisories (GHSA-x502 är inget 502-svar)
    SVAR_A[str(TMP / 'kand')] = sv_r76(('tar', 'x502-qq', 'high'))

    def bas_natfel_():
        raise RuntimeError('npm error code ENOTFOUND request to https://registry.npmjs.org/vercel failed')

    def bas_saknas_():
        raise RuntimeError('det installerade trädet finns inte (installerad utanför npm)')
    f_ = uh.audit(TMP / 'kand', bas=bas_natfel_)
    assert f_.startswith(uh.TILL) and 'kunde inte jämföras' in f_ and 'ENOTFOUND' in f_ and 'tar GHSA-x502-qq (high)' in f_, f_
    f_ = uh.audit(TMP / 'kand', bas=bas_saknas_)
    assert f_.startswith(uh.HALL) and 'installerad utanför npm' in f_ and uh.behall(f_), f_
    vl.kor = lambda args, cwd=None, **kw: ((1, json.dumps({'error': {'code': 'ENOTFOUND', 'summary': 'request failed'}})) if str(cwd) == str(TMP / 'bas')
                                           else (1, json.dumps({'vulnerabilities': SVAR_A[str(cwd)]})))
    f_ = uh.audit(TMP / 'kand', bas=TMP / 'bas')
    assert f_.startswith(uh.TILL) and 'ENOTFOUND' in f_, f_
    # prova_globalt (granskningarna av r76 och r77): kandidaten installeras som npm install -g gör (shallow) med
    # karenstidens gräns, och båda sidor granskas ur sina installerade träd; utan det installerade trädet är beskedet
    # BEHÅLLEN med skälet
    NPM_R76 = []
    LAGE_R77 = {'binar': '60.1.3', 'valfria': {}, 'las': {}, 'npm_rc': 0, 'npm_ut': '', 'intag': 'faller'}
    spara_r76 = (uh.npm, vl.version_av)

    def falsk_npm_r76(args, cwd, timeout=900, env=None):
        NPM_R76.append(list(args))
        if '--prefix' in args and LAGE_R77['npm_rc'] == 0:  # provkatalogen: kandidatens träd som npm lägger det med shallow
            d_ = Path(args[args.index('--prefix') + 1])
            (d_ / 'node_modules' / 'vercel').mkdir(parents=True, exist_ok=True)
            (d_ / 'node_modules' / 'vercel' / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.1.3',
                                                                                   'optionalDependencies': LAGE_R77['valfria']}))
            (d_ / 'package-lock.json').write_text(json.dumps({'packages': LAGE_R77['las']}))
        return LAGE_R77['npm_rc'], LAGE_R77['npm_ut']

    def falsk_kor_r77(args, cwd=None, **kw):
        if str(args[0]).endswith('/.bin/vercel'):
            return (0, 'Vercel CLI %s' % LAGE_R77['binar']) if LAGE_R77['binar'] else (1, 'Error: Cannot find module')
        return 1, json.dumps({'vulnerabilities': sv_r76(('tar', 'a', 'critical'))})
    uh.npm = falsk_npm_r76
    vl.kor = falsk_kor_r77
    spara_installerar_r77 = uh.npm_installerar
    uh.npm_installerar = lambda *a_: None  # ingen npm-installation på maskinen i provet (prövas för sig nedan)
    R_R77 = {'paket': 'vercel', 'installerat': '60.0.1', 'binar': 'vercel', 'id': 'npm-global:vercel'}
    try:
        f_, st_ = uh.prova_globalt(None, R_R77, {'version': '60.1.3'})
        assert f_.startswith(uh.HALL) and 'installerad utanför npm' in f_ and 'tar GHSA-a (critical)' in f_ and st_ is None, f_
        fore_r76 = [a_ for a_ in NPM_R76[0] if a_.startswith('--before=')]
        assert len(fore_r76) == 1 and fore_r76[0][len('--before='):] < vl.nu() and '--install-strategy=shallow' in NPM_R76[0], NPM_R76
        # gränsen har en timmes marginal mot karenstiden, så att plattformspaketen följer med (r77, M2)
        assert abs(vl.iso_s(uh.karensgrans()) - (time.time() - vl.KARENS_DAGAR * 86400 + 3600)) < 5, uh.karensgrans()
        # utan sårbarheter prövas binären: svarar den inte och ett valfritt beroende saknas i låset (uteslutet av gränsen)
        # är beskedet BEHÅLLEN; saknas inget är det en avvisning (r77, M2)
        vl.kor = lambda args, cwd=None, **kw: falsk_kor_r77(args, cwd) if str(args[0]).endswith('/.bin/vercel') else \
            (0, json.dumps({'metadata': {'dependencies': {'total': 3}}}))
        LAGE_R77.update(binar=None, valfria={'@x/bin-darwin-arm64': '1.0.0', '@x/bin-linux-x64': '1.0.0'},
                        las={'node_modules/vercel': {}, 'node_modules/vercel/node_modules/@x/bin-linux-x64': {}})
        f_, st_ = uh.prova_globalt(None, R_R77, {'version': '60.1.3'})
        assert f_.startswith(uh.HALL) and '@x/bin-darwin-arm64' in f_ and '@x/bin-linux-x64' not in f_, f_
        LAGE_R77['las']['node_modules/vercel/node_modules/@x/bin-darwin-arm64'] = {}
        f_, st_ = uh.prova_globalt(None, R_R77, {'version': '60.1.3'})
        assert f_ == 'provkatalogens vercel svarar None, väntade 60.1.3', f_
        # en annan plattforms paket som saknas förklarar inte att binären här inte svarar (r79, D)
        del LAGE_R77['las']['node_modules/vercel/node_modules/@x/bin-linux-x64']
        f_, st_ = uh.prova_globalt(None, R_R77, {'version': '60.1.3'})
        assert f_ == 'provkatalogens vercel svarar None, väntade 60.1.3', f_
        assert uh.egen_plattform('@anthropic-ai/claude-code-darwin-arm64') and not uh.egen_plattform('@anthropic-ai/claude-code-linux-arm64')
        # ingen version före gränsen (ETARGET): BEHÅLLEN, med npm:s rad hel
        LAGE_R77.update(npm_rc=1, npm_ut='npm error code ETARGET\nnpm error notarget No matching version found for vercel@60.1.3 with a date '
                                          'before 10/3/2026, 4:00:00 AM.\nnpm error notarget In most cases you or one of your dependencies are requesting\n')
        f_, st_ = uh.prova_globalt(None, R_R77, {'version': '60.1.3'})
        assert f_.startswith(uh.HALL) and 'with a date before 10/3/2026, 4:00:00 AM.' in f_, f_
        LAGE_R77.update(npm_rc=0, npm_ut='', binar='60.1.3')
        # intaget: det installerade trädet sparas som klon och läggs tillbaka med binärens länkar när intaget faller,
        # utan en ny installation av den gamla versionen (r77, M1); samma gräns som provet
        PF_ = TMP / 'prefix-r77'
        KAT_ = PF_ / 'lib' / 'node_modules' / 'vercel'
        (KAT_ / 'dist').mkdir(parents=True)
        (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.0.1'}))
        (KAT_ / 'dist' / 'vc.js').write_text('gammal')
        (PF_ / 'bin').mkdir()
        os.symlink('../lib/node_modules/vercel/dist/vc.js', PF_ / 'bin' / 'vercel')
        os.symlink('../lib/node_modules/annat/x.js', PF_ / 'bin' / 'annat')
        R_IN = dict(R_R77, bin=str(PF_ / 'bin' / 'vercel'), via_npm=True, paketkatalog=str(KAT_))

        def falsk_npm_intag(args, cwd, timeout=900, env=None):
            NPM_R76.append(list(args))
            (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.1.3'}))
            (KAT_ / 'dist' / 'vc.js').write_text('ny')
            os.unlink(PF_ / 'bin' / 'vercel')
            os.symlink('../lib/node_modules/vercel/dist/ny.js', PF_ / 'bin' / 'vercel')
            os.symlink('../lib/node_modules/vercel/dist/vc2.js', PF_ / 'bin' / 'vc')
            return (1, 'npm error code ECONNRESET\nnpm error network aborted') if LAGE_R77['intag'] == 'faller' else (0, '')
        uh.npm = falsk_npm_intag
        HJALP_ = {'trasiga': set()}
        spara_ls = uh.npm_ls_ok
        # npm ls säger att trädet är halvt för versionerna i HJALP_ (r85, M2, och r86, M1)
        uh.npm_ls_ok = lambda kat_: ('npm ls ser saknade eller ogiltiga beroenden (prov)' if (json.loads((KAT_ / 'package.json').read_text())['version']
                                     if (KAT_ / 'package.json').is_file() else None) in HJALP_['trasiga'] else None)
        spara_vanta_npm = uh.VANTA_ANNAN_NPM
        uh.VANTA_ANNAN_NPM = 0  # provet väntar inte på en annan npm (väntan prövas för sig nedan)
        kor_hj = spara_kor_m4
        vl.kor = kor_hj  # klonen görs med den riktiga cp
        vl.version_av = lambda a: json.loads((KAT_ / 'package.json').read_text())['version'] if (KAT_ / 'package.json').is_file() else None
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p', 'fore': '2026-10-03T00:00:00Z'})
        assert res_[0] == 'avvisad' and res_[1].startswith(uh.TILL) and 'lagt tillbaka' in res_[1] and len(NPM_R76) == 1, (res_, NPM_R76)
        assert json.loads((KAT_ / 'package.json').read_text())['version'] == '60.0.1' and (KAT_ / 'dist' / 'vc.js').read_text() == 'gammal'
        assert os.readlink(PF_ / 'bin' / 'vercel') == '../lib/node_modules/vercel/dist/vc.js' and not os.path.lexists(PF_ / 'bin' / 'vc')
        assert os.readlink(PF_ / 'bin' / 'annat') == '../lib/node_modules/annat/x.js' and not list((PF_ / 'lib').glob('.nwp-spar*'))
        LAGE_R77['intag'] = 'lyckas'
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p', 'fore': '2026-10-03T00:00:00Z'})
        assert res_[0] == 'uppdaterad' and '--before=2026-10-03T00:00:00Z' in NPM_R76[0] and '-g' in NPM_R76[0], (res_, NPM_R76)
        assert not list((PF_ / 'lib').glob('.nwp-spar*')), 'klonen städas också när intaget lyckas'
        assert uh.ta_in_globalt(None, dict(R_IN, paketkatalog=str(TMP / 'finns-inte')), {'version': '60.1.3'}, {'prov': 'p'})[0] == 'behallen'
        vl.kor = lambda args, **kw: (1, '') if args[:1] == ['ps'] else (0, '')  # en kopia som inte blev av: inget intag
        uh.npm_installerar = lambda *a_: None
        NPM_R76.clear()
        assert uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})[0] == 'behallen' and not NPM_R76, NPM_R76
        vl.kor = kor_hj
        # granskningarna av r79–r85: ett eget misslyckat intag lägger tillbaka klonen och tar bara bort npm:s kopior av den
        # gamla versionen; allt annat som ligger kvar redovisas och rörs inte; lagningen gör bara det som inte kan
        # förstöra något (trädet saknas helt och vår klon finns); intaget väntar när något ligger kvar eller npm arbetar
        (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.0.1'}))
        (KAT_ / 'dist' / 'vc.js').write_text('gammal')
        for f_ in ('vercel', 'vc'):
            if os.path.lexists(PF_ / 'bin' / f_):
                os.unlink(PF_ / 'bin' / f_)
        os.symlink('../lib/node_modules/vercel/dist/vc.js', PF_ / 'bin' / 'vercel')
        NM_ = PF_ / 'lib' / 'node_modules'
        SPAR_ = uh.spar_for(KAT_, 'vercel')
        uh.npm_installerar = lambda *a_: None  # ingen npm-installation på maskinen i provet
        vl.version_av = lambda a: (None if (KAT_ / 'TRASIG').exists() else json.loads((KAT_ / 'package.json').read_text())['version']) \
            if (KAT_ / 'package.json').is_file() else None
        spara_kor_hj = spara_kor_m4
        (NM_ / '.vercel-ai-abcdefgh').mkdir()  # ett annat pakets kopia: aldrig vår (r80, L1)
        assert uh.npm_undanflyttade(KAT_) == [] and [p_.name for p_ in uh.npm_undanflyttade(NM_ / 'vercel-ai')] == ['.vercel-ai-abcdefgh']

        def falsk_npm_dor(args, cwd, timeout=900, env=None):  # npm flyttar undan trädet och dör mitt i bytet
            NPM_R76.append(list(args))
            os.rename(KAT_, NM_ / '.vercel-zw0Ty2D2')
            return 1, ('npm error code ETIMEDOUT\nnpm error A complete log of this run can be found in: '
                       '/x/_logs/2026-10-06T04_37_15_429Z-debug-0.log')

        def falsk_npm_dor_framling(args, cwd, timeout=900, env=None):  # och en annan installation lämnar en kopia av en annan version
            (NM_ / '.vercel-Fram1234').mkdir()
            (NM_ / '.vercel-Fram1234' / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '61.0.0'}))
            return falsk_npm_dor(args, cwd, timeout, env)
        uh.npm = falsk_npm_dor_framling
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'avvisad' and 'lagt tillbaka' in res_[1] and res_[1].startswith(uh.TILL), res_
        assert not (NM_ / '.vercel-zw0Ty2D2').exists(), 'npm:s kopia av den gamla versionen från vårt intag borta'
        assert (NM_ / '.vercel-Fram1234').is_dir(), 'en kopia av en annan version rörs inte (r85, M3)'
        shutil.rmtree(NM_ / '.vercel-Fram1234')
        uh.npm = falsk_npm_dor
        assert (NM_ / '.vercel-ai-abcdefgh').is_dir() and json.loads((KAT_ / 'package.json').read_text())['version'] == '60.0.1'
        assert not SPAR_.exists() and not list(NM_.glob('.nwp-trasig-*'))
        # npm går igenom men versionen svarar inte: texten säger det (r80, L5)
        uh.npm = lambda args, cwd, timeout=900, env=None: (NPM_R76.append(list(args)) or (0, ''))
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'avvisad' and 'npm gick igenom, men vercel svarar 60.0.1, inte 60.1.3' in res_[1], res_
        # vercel --help svarar inte efter ett intag: inget intag, och klonen läggs tillbaka (r85, M2)
        def falsk_npm_halv(args, cwd, timeout=900, env=None):
            NPM_R76.append(list(args))
            (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.1.3'}))
            return 0, ''
        uh.npm = falsk_npm_halv
        HJALP_['trasiga'] = {'60.1.3'}
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        HJALP_['trasiga'] = set()
        assert res_[0] == 'behallen' and 'npm ls ser saknade' in res_[1] and json.loads((KAT_ / 'package.json').read_text())['version'] == '60.0.1', res_
        assert not list(NM_.glob('.nwp-trasig-*')), 'vår egen halva installation tas bort när klonen svarar'
        # en global npm-installation pågår: intaget väntar och rör ingenting (r85, M3)
        uh.npm_installerar = lambda *a_: 'en global npm-installation pågår (npm install -g x)'
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'behallen' and 'npm-installation pågår' in res_[1] and not NPM_R76, res_
        uh.npm_installerar = lambda *a_: None
        # en annan npm börjar medan vår kör: återställningen rör inte trädet, och klonen står kvar (r86, H1)
        def falsk_npm_annan(args, cwd, timeout=900, env=None):
            NPM_R76.append(list(args))
            uh.npm_installerar = lambda *a_: 'en npm-installation pågår (npm install /x/pkg.tgz)'
            (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '61.0.0-annan'}))
            return 1, 'npm error code ENOTEMPTY'
        uh.npm = falsk_npm_annan
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        uh.npm_installerar = lambda *a_: None
        assert res_[0] == 'avvisad' and 'ÅTERSTÄLLNINGEN FÖLL' in res_[1] and 'npm-installation pågår' in res_[1], res_
        assert json.loads((KAT_ / 'package.json').read_text())['version'] == '61.0.0-annan' and (SPAR_ / 'vercel' / 'package.json').is_file()
        (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.0.1'}))
        shutil.rmtree(SPAR_)
        # en installation börjar efter den första frågan men före vår npm: intaget väntar, och klonen tas bort (r86, H1)
        SVAR_I = iter([None, 'en npm-installation pågår (npm install /x/pkg.tgz)'])
        uh.npm_installerar = lambda *a_: next(SVAR_I, None)
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        uh.npm_installerar = lambda *a_: None
        assert res_[0] == 'behallen' and 'npm-installation pågår' in res_[1] and not NPM_R76 and not SPAR_.exists(), res_
        # en annan npm som rör paketet blir klar under väntan: återställningen görs (r88, M1)
        SVAR_V = iter([None, None, 'en npm-installation pågår (npm install vercel@61)', None])
        uh.npm_installerar = lambda *a_: next(SVAR_V, None)
        uh.npm = falsk_npm_dor
        uh.VANTA_ANNAN_NPM, spara_sov = 60, uh.time.sleep
        uh.time.sleep = lambda s_: None
        try:
            res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        finally:
            uh.time.sleep, uh.VANTA_ANNAN_NPM = spara_sov, 0
        uh.npm_installerar = lambda *a_: None
        assert res_[0] == 'avvisad' and 'lagt tillbaka' in res_[1] and not SPAR_.exists(), res_
        # ett avbrott (Ctrl-C) mitt i vår npm: klonen står kvar (r86, L1)
        def falsk_npm_avbrott(args, cwd, timeout=900, env=None):
            raise KeyboardInterrupt()
        uh.npm = falsk_npm_avbrott
        try:
            uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
            raise AssertionError('avbrottet skulle ha gått vidare')
        except KeyboardInterrupt:
            pass
        assert (SPAR_ / 'vercel' / 'package.json').is_file(), 'klonen står kvar efter ett avbrott'
        shutil.rmtree(SPAR_)
        # tillbakaläggningen faller: klonen står kvar och sägs
        uh.npm = falsk_npm_dor
        spara_rename = os.rename

        def rename_faller(a_, b_, *r_):
            if '.nwp-spar-' in str(a_):
                raise OSError(28, 'No space left on device')
            return spara_rename(a_, b_, *r_)
        os.rename = rename_faller
        try:
            res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        finally:
            os.rename = spara_rename
        assert res_[0] == 'avvisad' and 'ÅTERSTÄLLNINGEN FÖLL' in res_[1] and 'klonen står kvar' in res_[1], res_
        assert not KAT_.exists() and (SPAR_ / 'vercel' / 'package.json').is_file() and (SPAR_ / 'LANKAR.json').is_file()
        assert (NM_ / '.vercel-zw0Ty2D2').is_dir(), 'utan klonen på plats står npm:s kopia kvar: den kan vara den enda hela (r81, L2)'
        # klonens ägare lever (det här provet): lagningen rör ingenting, och intaget väntar
        assert uh.laga_avbrutet_intag(KAT_, 'vercel', 'vercel') is None and (SPAR_ / 'vercel' / 'package.json').is_file()
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'behallen' and not NPM_R76 and (SPAR_ / 'vercel' / 'package.json').is_file(), res_
        vl.skriv_json(SPAR_ / 'AGARE.json', {'pid': 999999, 'start': 'en process som inte finns'})
        # trädet saknas, men npm:s undanflyttade kopia ligger kvar: inget rörs, och det redovisas som trasigt (r85, M1)
        text_ = uh.laga_avbrutet_intag(KAT_, 'vercel', 'vercel')
        assert text_.startswith('MILJÖN TRASIG') and '.vercel-zw0Ty2D2' in text_ and (SPAR_ / 'vercel').is_dir() and (NM_ / '.vercel-zw0Ty2D2').is_dir(), text_
        shutil.rmtree(NM_ / '.vercel-zw0Ty2D2')  # det en människa tar bort efter att ha tittat
        # intagslåset hålls av ett annat underhåll: lagningen väntar till nästa gång
        spara_rot, spara_inv = vl.npm_global_rot, vl.inventera
        vl.npm_global_rot = lambda: str(NM_)
        try:
            with vl.las(uh.BYTESLAS):
                rap_ = {'rader': []}
                uh.steg_laga_globala(rap_)
            assert rap_.get('lagat') and 'ett intag pågår' in rap_['lagat'][0] and (SPAR_ / 'vercel').is_dir(), rap_
            # en npm-installation pågår: lagningen väntar
            uh.npm_installerar = lambda *a_: 'en global npm-installation pågår (npm install -g x)'
            assert uh.laga_avbrutet_intag(KAT_, 'vercel', 'vercel').startswith('MILJÖN TRASIG') and (SPAR_ / 'vercel').is_dir()
            uh.npm_installerar = lambda *a_: None
            # underhållets huvudflöde lagar före inventeringen (inventeringen stoppas här): trädet saknas helt och vår klon
            # finns, så klonen läggs på plats med länkarna, och binären prövas
            os.unlink(PF_ / 'bin' / 'vercel')

            def inv_stopp(k, delar=None):
                raise RuntimeError('stopp efter lagningen')
            vl.inventera = inv_stopp
            try:
                uh.underhall(k=vl.Kontext(nat=True, prova=False, katalog=TMP / 'lage-r79c'), prov=False)
                raise AssertionError('inventeringen skulle ha stoppats')
            except RuntimeError as e:
                assert 'stopp efter lagningen' in str(e), e
            # ett fel i lagningen stoppar aldrig underhållet (r85, L3)
            spara_laga = uh.laga_avbrutet_intag
            uh.laga_avbrutet_intag = lambda *a_: (_ for _ in ()).throw(OSError(5, 'I/O error'))
            SPAR_.mkdir()
            rap_ = {'rader': []}
            try:
                uh.steg_laga_globala(rap_)
            finally:
                uh.laga_avbrutet_intag = spara_laga
            assert rap_.get('trasigt') and 'lagningen föll' in rap_['trasigt'][0], rap_
            assert [x_['resultat'] for x_ in rap_['rader'] if x_['id'] == 'avbrutet-intag:vercel'] == ['fel'], rap_['rader']
            shutil.rmtree(SPAR_)
        finally:
            vl.npm_global_rot, vl.inventera = spara_rot, spara_inv
        assert json.loads((KAT_ / 'package.json').read_text())['version'] == '60.0.1' and not SPAR_.exists()
        assert os.readlink(PF_ / 'bin' / 'vercel') == '../lib/node_modules/vercel/dist/vc.js', 'länkarna tillbaka ur LANKAR.json (r80, L2)'
        rap_ = {'rader': [], 'lagat': ['vercel: ett avbrutet intag lagades']}
        assert 'Avbrutna intag före inventeringen' in uh.markdown(dict(rap_, start='t', commits=[]))
        # vår klon ligger kvar, ägaren är död och trädet finns och svarar: trädet rörs aldrig (r85)
        SPAR_.mkdir()
        shutil.copytree(KAT_, SPAR_ / 'vercel')
        (SPAR_ / 'vercel' / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '59.0.0'}))
        vl.skriv_json(SPAR_ / 'AGARE.json', {'pid': 999999, 'start': 'en process som inte finns'})
        text_ = uh.laga_avbrutet_intag(KAT_, 'vercel', 'vercel')
        assert not text_.startswith('MILJÖN TRASIG') and json.loads((KAT_ / 'package.json').read_text())['version'] == '60.0.1' \
            and (SPAR_ / 'vercel' / 'package.json').is_file(), text_
        shutil.rmtree(SPAR_)
        # något ligger kvar men det installerade svarar: det redovisas och rörs inte, och intaget väntar
        (NM_ / '.vercel-Kvar9876').mkdir()
        text_ = uh.laga_avbrutet_intag(KAT_, 'vercel', 'vercel')
        assert not text_.startswith('MILJÖN TRASIG') and 'svarar' in text_ and (NM_ / '.vercel-Kvar9876').is_dir(), text_
        NPM_R76.clear()
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'behallen' and 'intaget väntar' in res_[1] and not NPM_R76, res_
        shutil.rmtree(NM_ / '.vercel-Kvar9876')
        # någon uppdaterade under provet: intaget installerar inte en äldre version över den (r81, M3)
        (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.9.9'}))
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'behallen' and 'ändrades under provet (60.0.1 → 60.9.9)' in res_[1] and not NPM_R76, res_
        (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.0.1'}))
        # försvinner klonen under intaget flyttas aldrig trädet (r80, H1)
        def falsk_npm_tar_klonen(args, cwd, timeout=900, env=None):
            NPM_R76.append(list(args))
            shutil.rmtree(SPAR_ / 'vercel')
            (KAT_ / 'package.json').write_text(json.dumps({'name': 'vercel', 'version': '60.1.3-halv'}))
            return 1, 'npm error code ECONNRESET'
        uh.npm = falsk_npm_tar_klonen
        res_ = uh.ta_in_globalt(None, R_IN, {'version': '60.1.3'}, {'prov': 'p'})
        assert res_[0] == 'avvisad' and 'klonen saknas' in res_[1] and 'ÅTERSTÄLLNINGEN FÖLL' in res_[1] and (KAT_ / 'package.json').is_file(), res_
        uh.npm_installerar, vl.kor, uh.npm_ls_ok, uh.VANTA_ANNAN_NPM = spara_installerar_r77, spara_kor_hj, spara_ls, spara_vanta_npm
        # npm_installerar ser en global installation i ps (själva programmet, aldrig ett skal som nämner npm), och svarar när
        # ps inte går att köra
        spara_kor_ps = vl.kor
        try:
            vl.kor = lambda args, **kw: (0, 'node /opt/homebrew/bin/npm install -g vercel@62\n/bin/zsh\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert 'pågår' in (uh.npm_installerar() or '')
            vl.kor = lambda args, **kw: (0, 'node /opt/homebrew/bin/npm install --location=global x\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert 'pågår' in (uh.npm_installerar() or '')
            # npm byter sin titel till "npm" och de positionella argumenten: -g syns inte (r86, H1, mätt med en riktig npm)
            vl.kor = lambda args, **kw: (0, 'npm install /Users/x/pkg.tgz\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert 'pågår' in (uh.npm_installerar() or '')
            vl.kor = lambda args, **kw: (0, 'npm\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert uh.npm_installerar() is None, 'npm utan verb (de första tiondelarna) räknas inte'
            vl.kor = lambda args, **kw: (0, 'npm ls -g vercel\nnpm root -g\n/bin/zsh -c echo npm install -g x\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert uh.npm_installerar() is None, 'läsande npm och ett skal som nämner npm räknas inte'
            # per paket: ett npm ci i ett annat projekt räknas inte, men paketets namn, en sökväg, ett arkiv, en uppdatering
            # utan argument och npm:s förkortningar gör det (granskningen av r88, M1 och L1)
            for rad_, vantat_ in (('npm ci', None), ('npm install', None), ('npm install left-pad', None), ('npm install vercel@62.2.0', 'vercel'),
                                  ('npm i /Users/x/vercel-62.2.0.tgz', 'tgz'), ('npm update', 'update'), ('npm inst vercel', 'inst'),
                                  ('npm isnt vercel', 'isnt'), ('npm exec vercel', None)):
                vl.kor = lambda args, r_=rad_, **kw: (0, r_ + '\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
                assert bool(uh.npm_installerar('vercel')) == bool(vantat_), (rad_, uh.npm_installerar('vercel'))
            vl.kor = lambda args, **kw: (0, 'npm ci\n') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert uh.npm_installerar(), 'utan paket räknas varje skrivande npm (lagningen är försiktig)'
            vl.kor = lambda args, **kw: (1, '') if args[:1] == ['ps'] else spara_kor_ps(args, **kw)
            assert 'ps svarar inte' in (uh.npm_installerar() or '')
        finally:
            vl.kor = spara_kor_ps
    finally:
        uh.npm, vl.version_av, uh.npm_installerar = spara_r76 + (spara_installerar_r77,)
    # ett godkänt prov gäller provreglerna: nya regler gör om det (r77, L7)
    spara_regler = vl.PROVREGLER
    try:
        a1_ = uh.utgangslage(dict(v2))
        vl.PROVREGLER = 'andra-regler'
        assert uh.utgangslage(dict(v2)) != a1_
    finally:
        vl.PROVREGLER = spara_regler
    # en bas som inte granskade något beroende gör inte alla kandidatens fynd nya (L4); HTTP 500 är tillfälligt (L5); en
    # advisory utan url jämförs på sitt id (L1)
    vl.kor = lambda args, cwd=None, **kw: (0, json.dumps({'metadata': {'dependencies': {'total': 0}}})) if str(cwd) == str(TMP / 'bas') else \
        (1, json.dumps({'vulnerabilities': sv_r76(('tar', 'a', 'critical'))}))
    f_ = uh.audit(TMP / 'kand', bas=TMP / 'bas')
    assert f_.startswith(uh.HALL) and 'granskade inga beroenden' in f_, f_
    assert uh.nat('npm audit kunde inte göras: E500 500 Internal Server Error - POST https://registry.npmjs.org/-/npm/v1/security/advisories/bulk').startswith(uh.TILL)
    assert uh.nat('npm audit kunde inte göras: E500 request to https://registry.npmjs.org failed').startswith(uh.TILL), 'koden ensam räcker'
    # maskinens fel (full disk, en kvarlämnad katalog) behåller versionen; npm:s loggtid är ingen felkod (r79, A, H, I)
    for f_m in ('npm error code ENOTEMPTY\nnpm error syscall rename', 'installationen föll: ENOSPC: no space left on device, write',
                'den globala installationen föll (npm error code EACCES npm error syscall mkdir)'):
        assert uh.nat(f_m).startswith(uh.HALL) and 'miljöfel' in uh.nat(f_m), uh.nat(f_m)
    for f_m in ('modellprovet: Error: openFile failed', 'vaktprovet: EACCES: permission denied, open /x'):  # kandidatens egen utskrift (r80, M1)
        assert not uh.nat(f_m).startswith(uh.HALL), uh.nat(f_m)
    assert uh.nat('npm error code E123\nnpm error A complete log of this run can be found in: /x/_logs/2026-10-06T04_37_15_429Z-debug-0.log') \
        == 'npm error code E123\nnpm error A complete log of this run can be found in: /x/_logs/2026-10-06T04_37_15_429Z-debug-0.log'
    assert uh.npm_fel('npm error code ENOTEMPTY\nnpm error syscall rename\nnpm error path /x\n' + 'npm error x\n' * 30).startswith('npm error code ENOTEMPTY')
    vl.kor = lambda args, cwd=None, **kw: (1, json.dumps({'vulnerabilities': {'tar': {'name': 'tar', 'severity': 'high',
                                                                                         'via': [{'source': 77, 'name': 'tar', 'severity': 'high', 'title': 't'}]}}}))
    assert ('tar', 'source:77') in uh.audit_fynd(TMP)[0], uh.audit_fynd(TMP)
    # basen är det installerade trädet som det ligger på disk: versionerna, aliaset och de nästlade, aldrig en ny
    # upplösning (H1), och npm läser låset
    G_ = TMP / 'npm-global-r76' / 'vercel'
    for rel_, pj_ in (('', {'name': 'vercel', 'version': '60.0.1', 'dependencies': {'ws': '^8.0.0', '@vercel/oidc': '^3.0.0', 'p2r': 'npm:path-to-regexp@^6.0.0'}}),
                      ('node_modules/ws', {'name': 'ws', 'version': '8.21.3', 'dependencies': {'acorn': '^8.0.0'}}),
                      ('node_modules/ws/node_modules/acorn', {'name': 'acorn', 'version': '8.18.0'}),
                      ('node_modules/@vercel/oidc', {'name': '@vercel/oidc', 'version': '3.8.9'}),
                      ('node_modules/p2r', {'name': 'path-to-regexp', 'version': '6.3.0'})):
        (G_ / rel_).mkdir(parents=True, exist_ok=True)
        (G_ / rel_ / 'package.json').write_text(json.dumps(pj_))
    (G_ / 'node_modules' / '.bin').mkdir()
    os.symlink(G_ / 'node_modules' / 'ws', G_ / 'node_modules' / 'lank')
    las_ = json.loads((uh.las_ur_tradet(G_, '60.0.1', TMP / 'bas-r76') / 'package-lock.json').read_text())['packages']
    assert {k_: v_['version'] for k_, v_ in las_.items() if k_} == {
        'node_modules/vercel': '60.0.1', 'node_modules/vercel/node_modules/ws': '8.21.3', 'node_modules/vercel/node_modules/ws/node_modules/acorn': '8.18.0',
        'node_modules/vercel/node_modules/@vercel/oidc': '3.8.9', 'node_modules/vercel/node_modules/p2r': '6.3.0'}, las_
    assert las_['node_modules/vercel/node_modules/p2r']['name'] == 'path-to-regexp' and 'name' not in las_['node_modules/vercel/node_modules/ws'], las_
    npm_r76 = shutil.which('npm', path=PATH_URSPRUNG)
    r_ = subprocess.run([npm_r76, 'ls', '--package-lock-only', '--all', '--json'], cwd=str(TMP / 'bas-r76'), capture_output=True, text=True, timeout=120,
                        env=dict(os.environ, PATH=PATH_URSPRUNG))
    try:
        ls_ = json.loads(r_.stdout)['dependencies']['vercel']['dependencies']
        ok_ = r_.returncode == 0 and ls_['ws']['dependencies']['acorn']['version'] == '8.18.0' and ls_['p2r']['version'] == '6.3.0'
    except (ValueError, KeyError, TypeError):
        ok_ = False
    assert ok_, (npm_r76, r_.returncode, r_.stdout[-400:], r_.stderr[-600:])
    # npm ls i paketets egen katalog ser ett saknat beroende; med ett paketfilter hade det bara prövat att paketet finns
    # (granskningen av r88, H1, med riktig npm)
    LS_ = TMP / 'npm-ls-r88' / 'pkga'
    (LS_ / 'node_modules' / 'dep-b').mkdir(parents=True)
    (LS_ / 'package.json').write_text(json.dumps({'name': 'pkga', 'version': '1.0.0', 'dependencies': {'dep-b': '^1.0.0', 'dep-c': '^2.0.0'}}))
    (LS_ / 'node_modules' / 'dep-b' / 'package.json').write_text(json.dumps({'name': 'dep-b', 'version': '1.0.0'}))
    spara_kor_ls, vl.kor = vl.kor, spara_kor_m4
    spara_path_ls = os.environ['PATH']
    os.environ['PATH'] = PATH_URSPRUNG  # den riktiga npm (provets falska npm står annars först)
    try:
        assert uh.npm_ls_ok(LS_), 'dep-c saknas: npm ls i katalogen ser det'
        (LS_ / 'node_modules' / 'dep-c').mkdir()
        (LS_ / 'node_modules' / 'dep-c' / 'package.json').write_text(json.dumps({'name': 'dep-c', 'version': '2.1.0'}))
        assert uh.npm_ls_ok(LS_) is None, uh.npm_ls_ok(LS_)
    finally:
        os.environ['PATH'], vl.kor = spara_path_ls, spara_kor_ls
    for kat_, ver_ in ((G_, '60.1.3'), (None, '60.0.1'), (TMP / 'finns-inte', '60.0.1')):
        try:
            uh.las_ur_tradet(kat_, ver_, TMP / 'bas-r76-fel')
            raise AssertionError((kat_, ver_))
        except RuntimeError:
            pass
finally:
    vl.kor = spara_kor_m4

# M7: en återställning som faller gör miljön trasig: raden blir FEL, inget godkännande sparas och nästa kandidat prövas inte
k_m7 = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-m7')
uh.PROVA['npm-global'] = lambda k, r, kand: (None, {'prov': 'falskt prov'})
uh.TA_IN['npm-global'] = lambda k, r, kand, staged: ('avvisad', 'den globala installationen föll (ETIMEDOUT); ÅTERSTÄLLNINGEN FÖLL: npm ERR', None)
rap = {'rader': [], 'commits': []}
uh.hantera(k_m7, dict(v2, kandidater=[{'version': '62.4.0', 'huvudversion': True}, {'version': '60.2.0', 'huvudversion': False}]), rap)
assert [x['resultat'] for x in rap['rader']] == ['fel'] and rap.get('trasigt') and not k_m7.godkanda.for_version('npm-global:vercel', '62.4.0'), rap
assert 'Miljön kan vara trasig' in uh.markdown(dict(rap, start='t')), uh.markdown(dict(rap, start='t'))

# L12: en incheckning som faller tre gånger i rad avvisar versionen i stället för att återställa varje dygn
uh.TA_IN['npm-global'] = lambda k, r, kand, staged: ('behallen', 'incheckningen föll (git commit föll: krok); filerna och miljön återställda', None)
for varv_l12 in (1, 2, 3):
    rap = {'rader': [], 'commits': []}
    uh.hantera(k_m7, dict(v2, kandidater=[{'version': '60.3.0', 'huvudversion': False}]), rap)
assert rap['rader'][0]['resultat'] == 'avvisad' and '3 gånger' in rap['rader'][0]['detalj'], rap['rader']

# en avvisning gäller provreglerna som gjorde den (granskningen av r76: Vercel CLI 60.1.3 avvisades 02:49Z av jämförelsen
# utan bas): en avvisning med äldre provregler prövas en gång till och raden säger det, en med de nuvarande står
k_pr = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-provregler')
k_pr.avvisade.satt('npm-global:vercel', '60.1.3', fel='npm audit (high eller kritisk): tar (critical)')  # före provreglerna
r_pr = dict(v2, kandidater=[{'version': '60.1.3', 'huvudversion': False}])
assert vl.bedom(dict(r_pr), k_pr.avvisade)['resultat'] == 'behallen', 'startkontrollen visar den äldre avvisningen som en kandidat'
spara_pr = (uh.PROVA['npm-global'], uh.TA_IN['npm-global'])
PROVADE_PR = []
uh.PROVA['npm-global'] = lambda k, r, kand: (PROVADE_PR.append(kand['version']) or 'npm audit: nya sårbarheter (high eller kritisk) jämfört med den installerade: x GHSA-y (high)', None)
try:
    rap = {'rader': [], 'commits': []}
    uh.hantera(k_pr, dict(r_pr), rap)
    assert PROVADE_PR == ['60.1.3'] and rap['rader'][0]['resultat'] == 'avvisad' and 'äldre provregler' in rap['rader'][0]['omprovad'], rap['rader']
    assert 'prövad igen: avvisad' in uh.markdown(dict(rap, start='t')), uh.markdown(dict(rap, start='t'))
    assert k_pr.avvisade.for_version('npm-global:vercel', '60.1.3')['provregler'] == vl.PROVREGLER
    rap = {'rader': [], 'commits': []}
    uh.hantera(k_pr, dict(r_pr), rap)
    assert PROVADE_PR == ['60.1.3'] and rap['rader'][0]['resultat'] == 'avvisad' and 'prövas igen när en nyare' in rap['rader'][0]['detalj'], rap['rader']
    assert vl.bedom(dict(r_pr), k_pr.avvisade)['resultat'] == 'avvisad'
finally:
    uh.PROVA['npm-global'], uh.TA_IN['npm-global'] = spara_pr

# L8: kvittot säger skälet till att en godkänd version behålls
k_l8 = vl.Kontext(nat=False, prova=False)
k_l8.godkanda.satt('brew:node', '24.23.0_1', avtryck='x', staged={'prov': 'p'}, skal='PATH pinnar node@22 (prov)')
kv_l8 = sk.kor_kontroll(SLUG, 'ny')
nod_l8 = next(r_ for r_ in kv_l8['rader'] if r_.get('id') == 'brew:node')
assert nod_l8['resultat'] == 'behallen' and 'PATH pinnar node@22' in nod_l8['detalj'], nod_l8
k_l8.godkanda.ta_bort('brew:node')

# en incheckning som faller efter git add (en krok): indexet och filerna tillbaka, intaget behållet (fynd 8)
krok_l = KOPIA / '.git' / 'hooks' / 'pre-commit'
krok_l.write_text('#!/bin/sh\nexit 1\n')
krok_l.chmod(0o755)
try:
    res_k, detalj_k, commit_k = uh.ta_in_sajt(k, {'installerat': '5.0.0'}, {'version': '5.1.0'}, {'mapp': str(spar_), 'prov': 'prov'})
finally:
    krok_l.unlink()
assert res_k == 'behallen' and 'git commit föll' in detalj_k and commit_k is None, (res_k, detalj_k)
assert all((KOPIA / f).read_bytes() == b for f, b in fore_.items()) and not sh('git', 'status', '--porcelain', '--', 'mall').strip(), 'indexet och filerna tillbaka'

# L2: systemraderna är okända när uppslaget är gammalt eller föll, också när resultatet redan fanns
for rad_l2, vant_l2 in (({'typ': 'system', 'kontrollerad': GAMMAL, 'system_resultat': 'ok', 'kandidater': []}, 'okand'),
                        ({'typ': 'system', 'kontrollerad': vl.nu(), 'uppslagsfel': 'URLError', 'system_resultat': 'ok', 'kandidater': []}, 'okand'),
                        ({'typ': 'system', 'kontrollerad': vl.nu(), 'system_resultat': 'behallen', 'kandidater': []}, 'behallen')):
    assert vl.bedom(dict(rad_l2), k.avvisade)['resultat'] == vant_l2, rad_l2

# L5: en formels ändring väntar ut karenstiden; ett lokalt formelindex som är äldre än Homebrews API redovisas
spara_brew_l5 = (dict(BREW), dict(BREW_API))
try:
    BREW['git'] = '2.56.0'
    BREW_API['git'] = {'senaste': '2.56.0', 'tid': vl.nu()}
    BREW_API['gh'] = {'senaste': '2.99.0', 'tid': GAMMAL}
    rader_l5 = {r_['id']: vl.bedom(r_, k.avvisade, vl.nu()) for r_ in vl.inventera(vl.Kontext(nat=True, prova=False, max_alder=0, katalog=TMP / 'lage-l5'), ('brew',))}
    assert not rader_l5['brew:git']['kandidater'] and 'karenstiden' in rader_l5['brew:git']['detalj'], rader_l5['brew:git']
    assert not rader_l5['brew:gh']['kandidater'] and 'brew update' in rader_l5['brew:gh']['detalj'] and rader_l5['brew:gh']['senaste'] == '2.99.0'
    BREW_API['git'] = {'senaste': '2.56.0', 'tid': GAMMAL}
    rader_l5 = {r_['id']: r_ for r_ in vl.inventera(vl.Kontext(nat=True, prova=False, max_alder=0, katalog=TMP / 'lage-l5b'), ('brew',))}
    assert [c_['version'] for c_ in rader_l5['brew:git']['kandidater']] == ['2.56.0'], rader_l5['brew:git']
finally:
    BREW.clear(); BREW.update(spara_brew_l5[0]); BREW_API.clear(); BREW_API.update(spara_brew_l5[1])

# fynd 6: pinningen läses ur PATH, och inventeringen bär den till intaget. Provet bygger sin egen PATH utan de
# node-kataloger det ärvt: i underhållets prov av node@24 ligger node@24 först, och provet avvisade då node@24 (2026-10-06)
spara_path = os.environ['PATH']
os.environ['PATH'] = ':'.join(['/opt/homebrew/opt/node@22/bin'] + [d for d in spara_path.split(':')
                                                                    if not re.search(r'/opt/node@\d+/bin/?$|/Cellar/node@\d+/', d)])
try:
    assert vl.node_pinnad('node@22') == '/opt/homebrew/opt/node@22/bin' and vl.node_pinnad('node@24') is None
    rad_p6 = next(r_ for r_ in vl.inventera(vl.Kontext(nat=True, prova=False, max_alder=0, katalog=TMP / 'lage-p6'), ('brew',)) if r_['id'] == 'brew:node')
    assert rad_p6['pinnad'] == '/opt/homebrew/opt/node@22/bin', rad_p6
finally:
    os.environ['PATH'] = spara_path

# L4: underhållets prov skriver aldrig i huvudutcheckningens .venv eller i skalprofilen, men i sin worktree
import processgrans  # noqa: E402
rot_l4, wt_l4, hem_l4 = TMP / 'l4-rot', TMP / 'l4-wt', TMP / 'l4-hem'
for d_ in (rot_l4 / '.venv', wt_l4, hem_l4):
    d_.mkdir(parents=True)
(hem_l4 / '.zprofile').write_text('export PATH=x\n')
prof_l4 = processgrans.profil_underhallsprov(rot_l4, wt_l4, hem=hem_l4)
for mal_l4, ska in ((rot_l4 / '.venv' / 'x', False), (hem_l4 / '.zprofile', False), (wt_l4 / 'x', True)):
    r_l4 = subprocess.run([processgrans.SANDBOX_EXEC, '-p', prof_l4, '/bin/sh', '-c', 'echo prov >> "$1"', 'sh', str(mal_l4)], capture_output=True, text=True)
    assert (r_l4.returncode == 0) == ska, (mal_l4, r_l4.returncode, r_l4.stderr)
assert (hem_l4 / '.zprofile').read_text() == 'export PATH=x\n'

# L9: en tidsgräns avslutar hela trädet, också ett barn i en egen session
pidfil = TMP / 'l9-barn.pid'
rc_l9, _u = vl.kor([sys.executable, '-c', 'import subprocess, sys, time; p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], '
                    'start_new_session=True); open(sys.argv[1], "w").write(str(p.pid)); time.sleep(60)', pidfil], timeout=3)
barn_l9 = int(pidfil.read_text())
for _ in range(50):
    if not korregister.lever(barn_l9):
        break
    time.sleep(0.1)
assert rc_l9 == 124 and not korregister.lever(barn_l9), 'barnet i en egen session lever kvar efter tidsgränsen'

# L11: utan kontaktsida måste gatuadressen synas på någon sida
import standard_kontroll as stk  # noqa: E402
dist_l11 = TMP / 'l11-dist'
dist_l11.mkdir()
ver_l11 = TMP / 'l11-verksamhet.json'
ver_l11.write_text(json.dumps({'adress': {'gata': 'Storgatan 1', 'publik': True}}))
(dist_l11 / 'index.html').write_text('<html><body><main>Hej</main><script type="application/ld+json">{"streetAddress": "Storgatan 1"}</script></body></html>')
assert any('syns inte på någon sida' in f_['text'] for f_ in stk.adress(dist_l11, ver_l11)), stk.adress(dist_l11, ver_l11)
(dist_l11 / 'index.html').write_text('<html><body><main>Storgatan 1</main><script type="application/ld+json">{"streetAddress": "Storgatan 1"}</script></body></html>')
assert not [f_ for f_ in stk.adress(dist_l11, ver_l11) if f_.get('niva') != 'info'], stk.adress(dist_l11, ver_l11)

# M8: grupperingen läser bara domar efter rensningen, och utan dem körs ingen session
import gruppera as gr_m8  # noqa: E402
lar_m8 = TMP / 'm8-LARDOMAR.md'
lar_m8.write_text('# Lärdomar\n\n## L1 · 2026-10-02 · gammal-kund\n\nGammal dom.\n\n## L7 · 2026-10-07 · ny-kund\n\nAktuell dom.\n')
spara_m8 = (gr_m8.lardomar_fil, gr_m8.KUNDER)
gr_m8.lardomar_fil, gr_m8.KUNDER = (lambda: lar_m8), TMP / 'm8-kunder'
try:
    assert [d_.splitlines()[0] for d_ in gr_m8.aktuella_domar()] == ['## L7 · 2026-10-07 · ny-kund'] and gr_m8.antal_domar() == 1
    assert 'Gammal dom' not in gr_m8.uppdrag() and 'Aktuell dom' in gr_m8.uppdrag()
    lar_m8.write_text('# Lärdomar\n\n## L1 · 2026-10-02 · gammal-kund\n\nGammal dom.\n')
    assert gr_m8.main(['--torr']) == 0 and not gr_m8.aktuella_domar()
finally:
    gr_m8.lardomar_fil, gr_m8.KUNDER = spara_m8
print('granskningen av r72: instrumentets version, registrets identitet, Mobbin, Node under låset, metodlåset, tillfälliga fel, '
      'trasig miljö, incheckningar, systemraderna, Homebrews karenstid och index, pinningen, provets skrivgräns, trädet, '
      'adressen och grupperingen ok')

# ===== granskningen av r73: ett fall per fynd =====
# N1: en äldre metodkopia i körningens cache stoppar ingen start (den levereras om), och en äldre UPPTAGNA-VAL.md läses inte
metodkat = KOPIA / 'underlag' / SLUG / 'atelje' / 'metod'
metodkat.mkdir(parents=True, exist_ok=True)
(metodkat / 'METOD-skapa-1.md').write_text('Telefonnumret som tel-länk i sidhuvudet på varje sida.\n')
(KOPIA / 'underlag' / SLUG / 'UPPTAGNA-VAL.md').write_text('# Upptagna val\n\nArchivo för målaren.\n')
kv_n1 = sk.kor_kontroll(SLUG, 'ny')
styr_n1 = [r_ for r_ in kv_n1['rader'] if r_['namn'].startswith('gammal styrning')]
assert not any(r_.get('nodvandig') for r_ in styr_n1) and any('cache' in r_['namn'] and r_['resultat'] == 'okand' for r_ in styr_n1), styr_n1
assert not any('UPPTAGNA-VAL' in str(r_.get('detalj')) for r_ in styr_n1), 'en äldre UPPTAGNA-VAL.md läses inte av agenterna och räknas inte'
import upptagna_val as uv_n1  # noqa: E402
(KOPIA / 'underlag' / SLUG / 'UPPTAGNA-VAL.md').write_text('<!-- %s -->\n# Upptagna val\n\nArchivo för målaren.\n' % uv_n1.VERSION)
kv_n1 = sk.kor_kontroll(SLUG, 'ny')
styr_n1 = next(r_ for r_ in kv_n1['rader'] if r_['namn'] == 'gammal styrning i agentuppdragen och metoden')
assert styr_n1.get('nodvandig') and 'UPPTAGNA-VAL.md' in styr_n1['detalj'] and kv_n1['status'] == 'stoppad', styr_n1
shutil.rmtree(metodkat)
(KOPIA / 'underlag' / SLUG / 'UPPTAGNA-VAL.md').unlink()

# N2: formelns senaste ändring är färsk: ingen kandidat, också när det lokala indexet visar en äldre version än API:t
spara_n2 = (dict(BREW), dict(BREW_API))
try:
    BREW['git'] = '2.56.0'
    BREW_API['git'] = {'senaste': '2.56.0_1', 'tid': vl.nu()}
    r_n2 = next(r_ for r_ in vl.inventera(vl.Kontext(nat=True, prova=False, max_alder=0, katalog=TMP / 'lage-n2'), ('brew',)) if r_['id'] == 'brew:git')
    assert not r_n2['kandidater'] and r_n2.get('i_karens') == '2.56.0', r_n2
finally:
    BREW.clear(); BREW.update(spara_n2[0]); BREW_API.clear(); BREW_API.update(spara_n2[1])

# N3: med en worktree som rot nekar skrivgränsen repots git-katalog (krokar, config) och gits egen konfiguration
wt_rot_n3 = TMP / 'n3-rot'
sh(*GIT, 'worktree', 'add', '-q', '--detach', str(wt_rot_n3), 'HEAD')
try:
    hem_n3 = TMP / 'n3-hem'
    (hem_n3 / '.config' / 'git').mkdir(parents=True)
    prof_n3 = processgrans.profil_underhallsprov(wt_rot_n3, TMP / 'n3-wt', hem=hem_n3)
    for mal_n3 in (KOPIA / '.git' / 'hooks' / 'post-checkout', hem_n3 / '.config' / 'git' / 'config'):
        r_n3 = subprocess.run([processgrans.SANDBOX_EXEC, '-p', prof_n3, '/bin/sh', '-c', 'echo x >> "$1"', 'sh', str(mal_n3)], capture_output=True, text=True)
        assert r_n3.returncode != 0 and not mal_n3.exists(), (mal_n3, r_n3.returncode)
finally:
    sh(*GIT, 'worktree', 'remove', '--force', str(wt_rot_n3))

# N4: Mobbin-provet görs inte när anslutningen redan fallit, och får en egen tidsgräns
MOBB_N4, FRIST_N4 = [], []
spara_n4 = (rt_m1.samla, rt_m1.kor_session)
rt_m1.samla = lambda slug, uppdrag, underlag=None, kor=None, **kw: (MOBB_N4.append(kor) or (None, {'tjanster': {'mobbin': {'ok': True, 'bilder': 1}}}))
rt_m1.kor_session = lambda t, p, l, m, frist=0: (FRIST_N4.append(frist) or (0, None))
try:
    c_ = vl.Cache(vl.lagekatalog() / 'CACHE.json')
    c_.d['prov:mobbin'].update(resultat='fel', detalj='nere')
    vl.skriv_json(c_.fil, c_.d)
    vl.prova_mobbin(vl.Kontext(nat=False, prova=True), ansluten=False)
    assert not MOBB_N4, 'ingen session när anslutningen redan fallit'
    vl.prova_mobbin(vl.Kontext(nat=False, prova=True), ansluten=True, frist=vl.MOBBIN_PROVFRIST)
    assert MOBB_N4 and MOBB_N4[0] is not None
    MOBB_N4[0]('mobbin', 'p', 'l', 'm')
    assert FRIST_N4 == [vl.MOBBIN_PROVFRIST] and vl.MOBBIN_PROVFRIST <= 300, FRIST_N4
    c_ = vl.Cache(vl.lagekatalog() / 'CACHE.json')
    c_.d['prov:mobbin'].update(resultat='fel', detalj='nere igen')
    vl.skriv_json(c_.fil, c_.d)
    vl.prova_mobbin(vl.Kontext(nat=False, prova=True), ansluten=True)  # underhållets prov: sessionens vanliga gräns (L5)
    assert MOBB_N4[-1] is rt_m1.kor_session, MOBB_N4
finally:
    rt_m1.samla, rt_m1.kor_session = spara_n4

# N5: körregistrets identitet är oberoende av tidszonen
proc_n5 = subprocess.Popen(['/bin/bash', '-c', 'sleep 60', 'kor.sh'])
try:
    sh(sys.executable, '-B', KOPIA / 'kontroller' / 'korregister.py', 'in', 'bygge', '--slug', 'tz-prov', '--pid', str(proc_n5.pid), env=dict(os.environ, TZ='UTC'))
    for tz_ in ('Europe/Stockholm', 'America/New_York'):
        assert 'tz-prov' in sh(sys.executable, '-B', KOPIA / 'kontroller' / 'korregister.py', 'lista', env=dict(os.environ, TZ=tz_)), tz_
    post_n5 = json.loads((korregister.KATALOG / ('%d.json' % proc_n5.pid)).read_text())
    post_n5['pstart'] = korregister.startad_lokalt(proc_n5.pid)  # som den äldre koden skrev den (granskningen av r74, L6)
    (korregister.KATALOG / ('%d.json' % proc_n5.pid)).write_text(json.dumps(post_n5))
    assert any(d_['pid'] == proc_n5.pid for d_ in korregister.poster()), 'en post från före bytet till UTC räknas som samma process'
finally:
    proc_n5.kill()
    proc_n5.wait()

# N6: en formel utan färdig flaska byggs aldrig under intagslåset; testsajtens installation avbryts när en start väntar
spara_n6 = uh.brew
FLASKOR_N6 = {}
uh.brew = lambda *a, timeout=0, **k_: ((0, json.dumps({'formulae': [{'bottle': {'stable': {'files': FLASKOR_N6}}}]})) if a[:2] == ('info', '--json=v2')
                                 else (0, ''))
try:
    FLASKOR_N6.update({'arm64_sonoma': {}})  # en flaska för en äldre macOS hälls här (granskningen av r74, L1)
    assert not uh.flaska_saknas('git')
    FLASKOR_N6.clear()  # ingen flaska: Homebrew skulle bygga från källkod
    assert uh.flaska_saknas('node@24')
    fel_n6, _s = uh.prova_node_huvud(vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-n6'), {'id': 'brew:node'},
                                     {'version': '24.23.0_1', 'formel': 'node@24', 'huvudversion': True})
    assert fel_n6.startswith(uh.HALL) and 'flaska' in fel_n6, fel_n6
    fel_n6, _s = uh.prova_brew(vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-n6'), {'id': 'brew:git'},
                               {'version': '2.57.0', 'formel': 'git', 'huvudversion': False})
    assert fel_n6.startswith(uh.HALL) and 'flaska' in fel_n6, fel_n6
finally:
    uh.brew = spara_n6
wt_n6 = TMP / 'n6-wt'
(wt_n6 / 'mall' / 'astro').mkdir(parents=True)
for f_ in ('package.json', 'package-lock.json'):
    shutil.copy2(KOPIA / 'mall' / 'astro' / f_, wt_n6 / 'mall' / 'astro' / f_)
spara_npm_n6 = (FAKE / 'bin' / 'npm').read_text()
(FAKE / 'bin' / 'npm').write_text('#!/bin/bash\nsleep 30\n')
try:
    fel_n6b = uh.forbered_testsajt(wt_n6, dict(os.environ), '(version 1)\n(allow default)\n', avbryt=lambda: True)
finally:
    (FAKE / 'bin' / 'npm').write_text(spara_npm_n6)
assert fel_n6b.startswith(uh.HALL) and 'avbröts' in fel_n6b, fel_n6b

# N7: en oversionerad node med en ny huvudversion i indexet behålls med skälet, aldrig ok
spara_n7 = (vl.node_formel, dict(BREW), dict(AKTIV), dict(BREW_API), dict(NODE_MAL))
try:
    vl.node_formel = lambda: ('node', '22.23.2')
    AKTIV['node'] = '22.23.2'
    BREW['node'] = '25.1.0'
    BREW_API['node'] = {'senaste': '25.1.0', 'tid': GAMMAL}
    NODE_MAL.update(major=22, version='22.23.2')
    r_n7 = vl.bedom(next(r_ for r_ in vl.inventera(vl.Kontext(nat=True, prova=False, max_alder=0, katalog=TMP / 'lage-n7'), ('brew',))
                         if r_['id'] == 'brew:node'), k.avvisade, vl.nu())
    assert r_n7['resultat'] == 'behallen' and 'node@NN' in r_n7['detalj'], r_n7
finally:
    vl.node_formel = spara_n7[0]
    for d_, s_ in ((BREW, spara_n7[1]), (AKTIV, spara_n7[2]), (BREW_API, spara_n7[3]), (NODE_MAL, spara_n7[4])):
        d_.clear(); d_.update(s_)

# M3: kontrollen vid intaget avvisar en skill vars radutdrag ändras, prövad mot kartan som den ser ut vid intaget
spara_m3b = uh.utdrag_som_andras
uh.utdrag_som_andras = lambda tmp, namn: ['%s/SKILL.md rad 1–3' % namn]
try:
    res_m3b, detalj_m3b, _c = uh.ta_in_skill(vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-m3b'), demo_rad, demo_rad['kandidater'][0],
                                             {'mapp': str(demo), 'head': 'x' * 40, 'filer': 1, 'krockar': [], 'prov': 'prov'})
    assert res_m3b == 'avvisad' and 'vid intaget' in detalj_m3b and 'utdrag' in detalj_m3b, (res_m3b, detalj_m3b)
finally:
    uh.utdrag_som_andras = spara_m3b

# M5: ett lyckat intag av den senaste mogna commiten när källans HEAD är färsk
upp2 = TMP / 'uppstrom2'
(upp2 / 'skills' / 'demo2').mkdir(parents=True)
(upp2 / 'skills' / 'demo2' / 'SKILL.md').write_text('---\nname: demo2\n---\n# Demo2\n\nRad.\n')
(upp2 / 'skills' / 'demo2' / 'ref.md').write_text('Ett.\n')
sh(*GIT, 'init', '-q', '-b', 'main', cwd=upp2)
sh(*GIT, 'config', 'uploadpack.allowFilter', 'true', cwd=upp2)
sh(*GIT, 'add', '-A', cwd=upp2)
sh(*GIT, 'commit', '-q', '-m', 'bas', cwd=upp2, env=gammal_git())
bas2 = sh('git', 'rev-parse', 'HEAD', cwd=upp2).strip()
(upp2 / 'skills' / 'demo2' / 'ref.md').write_text('Två.\n')
sh(*GIT, 'commit', '-q', '-am', 'mogen', cwd=upp2, env=gammal_git())
mogen2 = sh('git', 'rev-parse', 'HEAD', cwd=upp2).strip()
(upp2 / 'skills' / 'demo2' / 'ref.md').write_text('Tre.\n')
sh(*GIT, 'commit', '-q', '-am', 'färsk', cwd=upp2)
farsk2 = sh('git', 'rev-parse', 'HEAD', cwd=upp2).strip()
demo2 = KOPIA / '.claude' / 'skills' / 'demo2'
demo2.mkdir()
(demo2 / 'SKILL.md').write_text('---\nname: demo2\n---\n# Demo2\n\nRad.\n')
(demo2 / 'ref.md').write_text('Ett.\n')
(demo2 / 'KALLA.md').write_text('# Källa\n\n- **Källa:** https://github.com/prov/demo2-skill, `skills/demo2/`, commit `%s` (prov).\n- **Licens:** MIT.\n'
                                '- **Krockar med våra beslut:** inga.\n' % bas2)
sh(*GIT, 'add', '-A')
sh(*GIT, 'commit', '-q', '-m', 'demo2-skillen')
os.environ.update({'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_1': 'url.file://%s.insteadOf' % upp2, 'GIT_CONFIG_VALUE_1': 'https://github.com/prov/demo2-skill.git'})
head_m5 = vl.git_head
vl.git_head = lambda repo: farsk2 if 'demo2-skill' in repo else head_m5(repo)
try:
    k_m5 = vl.Kontext(nat=True, prova=False, max_alder=0)
    rad_m5 = next(r_ for r_ in vl.inventera(k_m5, ('skills',)) if r_['id'] == 'skill:demo2')
    rap = {'rader': [], 'commits': []}
    uh.hantera(k_m5, rad_m5, rap)
    assert rap['rader'][0]['resultat'] == 'uppdaterad' and rap['rader'][0]['till'] == mogen2, rap['rader']
    assert (demo2 / 'ref.md').read_text() == 'Två.\n' and mogen2 in (demo2 / 'KALLA.md').read_text(), 'den mogna commiten, inte den färska'
finally:
    vl.git_head = head_m5

# N8: grupperingens session nekas den gamla GRUPPERING.md och domarna före rensningen
import gruppera as gr_n8  # noqa: E402
lar_n8 = TMP / 'n8-LARDOMAR.md'
lar_n8.write_text('# Lärdomar\n\n## L7 · 2026-10-07 · ny-kund\n\nAktuell dom.\n')
ARGS_N8 = []
spara_n8 = (gr_n8.lardomar_fil, gr_n8.KUNDER, gr_n8.subprocess.run)
gr_n8.lardomar_fil, gr_n8.KUNDER = (lambda: lar_n8), TMP / 'n8-kunder'
gr_n8.subprocess.run = lambda args, **kw: (ARGS_N8.append(args) or subprocess.CompletedProcess(args, 1, b'{}', b''))
try:
    gr_n8.main(['--prov'])
finally:
    gr_n8.lardomar_fil, gr_n8.KUNDER, gr_n8.subprocess.run = spara_n8
assert ARGS_N8 and 'Read(./kunskap/GRUPPERING.md)' in ARGS_N8[0] and 'Read(./LARDOMAR.md)' in ARGS_N8[0], ARGS_N8
# startkontrollens kvitton följer aldrig med förra körningens material till arkivet (de skrivs före arkiveringen)
rot_kv = TMP / 'kv-atelje'
(rot_kv / 'startkvitton').mkdir(parents=True)
for f_ in ('STARTKVITTO.json', 'STARTKVITTO.md', 'VINNARE.json', 'STATUS.json'):
    (rot_kv / f_).write_text('{}')
(rot_kv / 'startkvitton' / 'STARTKVITTO-x.json').write_text('{}')
arkiv_kv = atelje.arkivera_forra(rot_kv)
assert (rot_kv / 'STARTKVITTO.json').is_file() and (rot_kv / 'startkvitton' / 'STARTKVITTO-x.json').is_file() and not (rot_kv / 'VINNARE.json').exists()
assert (arkiv_kv / 'VINNARE.json').is_file() and not (arkiv_kv / 'STARTKVITTO.json').exists(), arkiv_kv
# en ny start utan eget kvitto (NWP_STARTKONTROLL=av) tar den förra körningens kvitto med till arkivet, så att ingen
# senare start ärver dess lås; helbyggets kvitto och historiken står kvar (granskningen av r76)
rot_av = TMP / 'kv-atelje-av'
(rot_av / 'startkvitton').mkdir(parents=True)
for f_ in ('STARTKVITTO.json', 'STARTKVITTO.md', 'STARTKVITTO-STOPP.json', 'STARTKVITTO-BYGGE.json', 'STATUS.json'):
    (rot_av / f_).write_text('{}')
assert atelje.arkivera_vid_ny_start(rot_av, kvitto=True) is None, 'med eget kvitto finns inget att arkivera'
arkiv_av = atelje.arkivera_vid_ny_start(rot_av, kvitto=False)
assert arkiv_av and (arkiv_av / 'STARTKVITTO.json').is_file() and (arkiv_av / 'STARTKVITTO-STOPP.json').is_file() and not (rot_av / 'STARTKVITTO.json').exists()
assert (rot_av / 'STARTKVITTO-BYGGE.json').is_file() and (rot_av / 'startkvitton').is_dir() and (rot_av / 'STATUS.json').is_file()
assert atelje.arkivera_vid_ny_start(rot_av, kvitto=False) is None
print('granskningen av r73: cachen och gamla upptagna val, Homebrews karenstid, skrivgränsen i en worktree, Mobbin-provet, tidszonen, '
      'flaskan och avbrottet, oversionerad node, utdragen vid intaget, den mogna commiten och grupperingen ok')

# ett bytt mätinstrument märks i nästa startkvitto
vl.logga_andring(vl.lagekatalog(), id='instrument:axe-core', namn='axe-core', grupp='mätinstrument', fran='4.13.0', till='4.14.0',
                 prov='rökprovet', commit=None, matinstrument=True)
kv = sk.kor_kontroll(SLUG, 'ny')
assert [a['namn'] for a in kv['matinstrument_bytta']] == ['axe-core'] and 'Mätinstrument bytta' in (KOPIA / 'underlag' / SLUG / 'atelje' / 'STARTKVITTO.md').read_text()
kv = sk.kor_kontroll(SLUG, 'ny')
assert not kv['matinstrument_bytta'], 'bara sedan förra starten'
# ett instrument som bytts utanför underhållet (en commit, en installation för hand) syns också (fynd 15)
pj = KOPIA / 'kontroller' / 'package.json'
fore_pj = pj.read_text()
pin = vl.paketberoenden(KOPIA / 'kontroller')['html-validate']
pj.write_text(fore_pj.replace('"html-validate": "%s"' % pin, '"html-validate": "%s-utanfor"' % pin))
kv = sk.kor_kontroll(SLUG, 'ny')
pj.write_text(fore_pj)
utanfor = [a for a in kv['matinstrument_bytta'] if a['namn'] == 'html-validate']
assert utanfor and utanfor[0]['till'] == pin + '-utanfor' and 'utanför underhållet' in utanfor[0]['tid'], kv['matinstrument_bytta']
assert kv['status'] == 'stoppad', 'låset och node_modules skiljer sig: starten stoppas, och körningens kvitto står kvar'
kv = sk.kor_kontroll(SLUG, 'ny')
assert not kv['matinstrument_bytta'], ('jämfört med den senaste start som gick är inget bytt', kv['matinstrument_bytta'])
# ett prov eller intag som kastar ett undantag för full disk behåller versionen (granskningen av r81)
k_u = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-r81u')
spara_u = (uh.PROVA['npm-global'], uh.TA_IN['npm-global'])

def prova_disk(k, r, kand):
    raise OSError(28, 'No space left on device')
uh.PROVA['npm-global'] = prova_disk
try:
    rap = {'rader': [], 'commits': []}
    uh.hantera(k_u, dict(v2, kandidater=[{'version': '60.2.0', 'huvudversion': False}]), rap)
    assert rap['rader'][0]['resultat'] == 'behallen' and 'miljöfel' in rap['rader'][0]['detalj'] and not k_u.avvisade.for_version('npm-global:vercel', '60.2.0'), rap
finally:
    uh.PROVA['npm-global'], uh.TA_IN['npm-global'] = spara_u
# en äldre avvisning som --utan-tunga hoppar över märks inte "prövad igen" (granskningen av r79, E)
k_e = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-r79e')
k_e.avvisade.satt('npm-global:vercel', '62.4.0', fel='gammalt prov')
rap = {'rader': [], 'commits': []}
uh.hantera(k_e, dict(v2, kandidater=[{'version': '62.4.0', 'huvudversion': True}]), rap, utan_tunga=True)
assert rap['rader'][0]['resultat'] == 'behallen' and 'omprovad' not in rap['rader'][0], rap['rader']
# går det senaste kvittot i historiken inte att läsa är baslinjen det närmast före (r79, G)
rot_g = TMP / 'kv-historik-g'
(rot_g / 'startkvitton').mkdir(parents=True)
(rot_g / 'startkvitton' / 'STARTKVITTO-2026-10-06T010000Z.json').write_text(json.dumps({'tid': 'a', 'matinstrument_sett': {'axe-core': '4.13.0'}}))
(rot_g / 'startkvitton' / 'STARTKVITTO-2026-10-06T020000Z.json').write_text('{trasig')
(rot_g / 'startkvitton' / 'STARTKVITTO-STOPP-2026-10-06T030000Z.json').write_text(json.dumps({'tid': 'stopp'}))
assert sk.senaste_kvitto(rot_g, 'STARTKVITTO')['tid'] == 'a', sk.senaste_kvitto(rot_g, 'STARTKVITTO')
(rot_g / 'startkvitton' / 'STARTKVITTO-2026-10-06T025000Z.json').write_text('"trasig"')  # läsbar JSON men inget objekt (r80, L4)
assert sk.senaste_kvitto(rot_g, 'STARTKVITTO')['tid'] == 'a', sk.senaste_kvitto(rot_g, 'STARTKVITTO')
# efter en start utan startkontroll (kvittot arkiverat med körningen) är baslinjen den förra starten ur historiken, så
# att ett bytt instrument ändå syns (granskningen av r77, M4); en återupptagen start utan lås att ärva säger det (L12)
rot_m4 = KOPIA / 'underlag' / SLUG / 'atelje'
undan_m4 = {f_: (rot_m4 / f_).read_bytes() for f_ in ('STARTKVITTO.json', 'STARTKVITTO.md') if (rot_m4 / f_).is_file()}
for f_ in undan_m4:
    (rot_m4 / f_).unlink()
vl.logga_andring(vl.lagekatalog(), id='instrument:axe-core', namn='axe-core', grupp='mätinstrument', fran='4.14.0', till='4.15.0',
                 prov='rökprovet', commit=None, matinstrument=True)
kv = sk.kor_kontroll(SLUG, 'ny')
assert [a['till'] for a in kv['matinstrument_bytta'] if a['namn'] == 'axe-core'] == ['4.15.0'], kv['matinstrument_bytta']
for f_ in ('STARTKVITTO.json', 'STARTKVITTO.md'):
    (rot_m4 / f_).unlink(missing_ok=True)
kv = sk.kor_kontroll(SLUG, 'fortsatt')
assert kv['aterupptagen'] == {'startad': None, 'andrat': [], 'utan_kvitto': True}, kv.get('aterupptagen')
assert 'startades utan startkontroll' in (KOPIA / kv['kvitto']).read_text(), kv['kvitto']
for f_, b_ in undan_m4.items():
    (rot_m4 / f_).write_bytes(b_)
print('mätinstrumentets byte märkt i kvittot, också utanför underhållet och efter en start utan kontroll, ok')

# brew update högst en gång per dygn, före versionsuppslagen, med Homebrews version före och efter i rapporten och
# startkvittot; aldrig brew upgrade på allt (ägarens beslut 2026-10-06, punkt 1)
BREW_B, HB_V = [], {'v': '4.6.1'}


def falsk_brew_b(*a, timeout=0, **k_):
    BREW_B.append(a)
    if a == ('--version',):
        return 0, 'Homebrew %s\n' % HB_V['v']
    if a == ('update',):
        HB_V['v'] = '4.6.2'
        return 0, 'Updated 2 taps'
    return 1, 'okänt'


spara_brew_b, spara_inv_b = uh.brew, vl.inventera
uh.brew = falsk_brew_b
try:
    k_b = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-brew')
    rap_b = {}
    hb_ = uh.steg_brew_update(k_b, rap_b)
    assert (hb_['fore'], hb_['efter'], hb_['resultat']) == ('4.6.1', '4.6.2', 'ok') and ('update',) in BREW_B, (hb_, BREW_B)
    assert '4.6.1 → 4.6.2' in uh.markdown(dict(rap_b, start='t', rader=[], commits=[]))
    BREW_B.clear()
    hb_ = uh.steg_brew_update(k_b, {})
    assert hb_['hoppad'] and ('update',) not in BREW_B and '4.6.1 → 4.6.2' in uh.homebrew_rad(hb_), 'högst en gång per dygn'
    vl.skriv_json(k_b.katalog / 'BREW-UPDATE.json', dict(vl.las_json(k_b.katalog / 'BREW-UPDATE.json'), tid='2026-01-01T00:00:00Z'))
    BREW_B.clear()
    hb_ = uh.steg_brew_update(k_b, {})
    assert ('update',) in BREW_B and not hb_.get('hoppad'), 'ett dygn senare igen'
    # underhållets huvudflöde kör den före versionsuppslagen (inventeringen stoppas här)
    BREW_B.clear()

    def inv_stopp_b(k, delar=None):
        raise RuntimeError('stopp vid uppslagen')
    vl.inventera = inv_stopp_b
    try:
        uh.underhall(k=vl.Kontext(nat=True, prova=False, katalog=TMP / 'lage-brew2'), prov=False)
        raise AssertionError('uppslagen skulle ha stoppats')
    except RuntimeError as e:
        assert 'stopp vid uppslagen' in str(e), e
    assert ('update',) in BREW_B and (TMP / 'lage-brew2' / 'BREW-UPDATE.json').is_file(), BREW_B
finally:
    uh.brew, vl.inventera = spara_brew_b, spara_inv_b
spara_kor_b = vl.kor
vl.kor = lambda args, **kw: (0, '')
try:
    for a_ in (('upgrade',), ('upgrade', '--formula')):
        try:
            BREW_ORIGINAL(*a_)
            raise AssertionError(a_)
        except RuntimeError:
            pass
    assert BREW_ORIGINAL('upgrade', '--formula', 'node@22') == (0, ''), 'en formel i taget går'
finally:
    vl.kor = spara_kor_b
assert 'Homebrew: brew update t, 4.6.1 → 4.6.2' in sk.markdown(dict(kv, homebrew={'tid': 't', 'fore': '4.6.1', 'efter': '4.6.2', 'resultat': 'ok'}))
print('brew update en gång per dygn, före uppslagen, med versionen före och efter, och aldrig brew upgrade på allt, ok')

# worktree-mekanismen för hela rökprovet: grönt och rött, och worktreen städas
riktig = importlib.reload(uh)
for f in ('kontroller/rokprov.sh',):
    (KOPIA / f).write_text('#!/bin/bash\nR="$(dirname "$0")/.."\nif [ -f "$R/KANDIDAT-SOV" ]; then sleep 60; fi\n'
                           'if [ -f "$R/KANDIDAT-ROD" ]; then echo "FEL: kandidaten bröt provet"; exit 1; fi\n'
                           # egna kopior av .venv och node_modules, aldrig länkar till utcheckningens (granskningen av r72, L4)
                           'for d in .venv kontroller/node_modules; do if [ -L "$R/$d" ] || [ ! -d "$R/$d" ]; then echo "FEL: $d är ingen egen kopia"; exit 1; fi; done\n'
                           # konsolskripten i klonen kör klonens tolk, inte originalets (granskningen av r74, M1)
                           'head -2 "$R/.venv/bin/pip" | grep -q "/wt/.venv/" || { echo "FEL: pip kör originalets venv"; exit 1; }\n'
                           '"$R/.venv/bin/python" -c "import sys; assert \'/wt/.venv\' in sys.prefix, sys.prefix" || { echo "FEL: fel venv"; exit 1; }\n'
                           'echo "rökprovet OK"\n')
sh(*GIT, 'commit', '-q', '-am', 'falskt rökprov')
ok, text = riktig.rokprov_i_worktree(vl.Kontext(nat=False, prova=False), 'prov-gront', lambda wt: None)
assert ok, text
assert 'rökprovet OK' in next((underlag_logg.read_text() for underlag_logg in sorted((vl.lagekatalog() / 'underhall').glob('rokprov-prov-gront-*.log'))), '')
ok, text = riktig.rokprov_i_worktree(vl.Kontext(nat=False, prova=False), 'prov-rott', lambda wt: (wt / 'KANDIDAT-ROD').write_text('x') and None)
assert not ok and 'FEL: kandidaten bröt provet' in text, text
# ett långt prov efter ett byte på plats avbryts när en start väntar: behållet, aldrig avvisat
t0 = time.time()
ok, text = riktig.rokprov_i_worktree(vl.Kontext(nat=False, prova=False), 'prov-avbrutet', lambda wt: (wt / 'KANDIDAT-SOV').write_text('x') and None,
                                     avbryt=lambda: True)
assert not ok and text.startswith(riktig.HALL) and 'avbröts' in text and time.time() - t0 < 40, (text, time.time() - t0)
assert sh('git', 'worktree', 'list').count('\n') == 1, sh('git', 'worktree', 'list')
print('rökprovet i en egen worktree med egna kopior av .venv och node_modules: grönt, rött med felet, avbrutet när en start väntar, och städat ok')

shutil.rmtree(TMP, ignore_errors=True)
print('startkontrollens och underhållets prov: alla ok')
