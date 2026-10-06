#!/usr/bin/env python3
"""prov_stadning.py — städregeln (kontroller/stadning.py; ägarens beslut 2026-10-06 i BESLUT.md, delvis ersatt samma dag)
i temporära kataloger, med en lokal bar git-origin, provets egna processer och en injicerad klocka, diskmått och
processlista. Varje fall kan bli rött, också granskarens (granskningen av r94):

- B1, först: körd ur en full kopia med eget .git (cp -R) städas ingenting och huvudutcheckningen står kvar, och likaså
  när huvudutcheckningen är en symlänk eller git inte svarar; körd ur huvudutcheckningen raderas kopian. Mot 1bcef37
  blir provet rött här;
- B2: allt som inte går att återskapa är eget material, också ignorerade filer (kirurgen/, .env) och kod och anteckningar
  i en kopia utan .git; det härledda, rökprovets fixtur och det som finns i huvudutcheckningens arbetsträd eller git är
  det inte;
- Ö1–Ö2: en frikopplad HEAD, stash@{1} och en köad ändring i en kopia; en ny worktree utan egen commit väntar på ägaren;
- Ö3: en levande sessions scratchpad står kvar (id i argumenten eller en öppen fil, okänt id i samma projekt,
  transkriptet ändrat), en övergiven raderas;
- Ö4: diskvakten och npm-rensningen hoppar över medan en körning, ett underhåll eller ett intag pågår, och läsningen av
  körregistret skriver inget;
- Ö5: varje tempfile- och mktemp-prefix i koden, skapad med tempfile i $TMPDIR, hittas och raderas;
- Ö6: diskvaktens städning står i underhållets rapport;
- Ö7: worktree remove utan --force, ps och lsof som faller, oläsbara kataloger och filer, identiteten före SIGTERM, en
  process som inte går att stoppa, en låst worktree, okända worktrees, dashboarden utan --port och symlänkskyddet;
- och det tidigare: huvudutcheckningens underlag/ och kunder/ byte för byte oförändrade, worktrees, processer,
  tillfälliga kataloger, scratchpad, npm-cachens tre fall, diskvakten, torrläget, redovisningens fält och underhållets
  rapport.

    .venv/bin/python kontroller/rokprov/revision/prov_stadning.py <repo>

Processlistan är maskinens (ps och lsof), men bara provets egna processer räknas, och stoppet vägrar alla andra. Det
verkliga systemet (~/nortropic-repos, /tmp, ~/.npm) rörs aldrig: Ram.verklig fäller provet om något anropar den.
"""
import fcntl
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-stadprov-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):  # också när provet faller: annars fyller kvarlämnade kopior disken
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
os.environ['NWP_KORREGISTER'] = str(TMP / 'korregister')  # före importen: provets körningar i ett eget register
os.environ.pop('NWP_UNDERHALL_PROV', None)  # provets körningar anmäler sig, också inne i underhållets eget rökprov
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister  # noqa: E402
import stadning  # noqa: E402
import startkontroll as sk  # noqa: E402
import underhall as uh  # noqa: E402
import verktygslada as vl  # noqa: E402


def verkligt(*a, **k):
    raise AssertionError('provet når aldrig det verkliga systemet (stadning.Ram.verklig)')


stadning.Ram.verklig = classmethod(verkligt)
DYGN = 86400
T = time.time() + 10 * DYGN  # provets klocka: det provet skapar nu är tio dygn gammalt; det som ska vara ungt får en senare tid
iso = stadning.iso
KLARA = []
GIT = ['git', '-c', 'user.name=prov', '-c', 'user.email=prov@exempel.se', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']


def klar(namn):
    KLARA.append(namn)
    print('ok: ' + namn)


def sh(*a, cwd=None):
    r = subprocess.run([str(x) for x in a], cwd=str(cwd or TMP), capture_output=True, text=True)
    assert r.returncode == 0, (a, r.stdout[-400:], r.stderr[-400:])
    return r.stdout


def git(*a, cwd):
    return sh(*GIT, *a, cwd=cwd)


def satt_tid(p, t):
    """mtime på p och allt under den, nedifrån och upp (ctime blir nu, tio dygn före provets klocka)."""
    for rot, mappar, filer in os.walk(p, topdown=False):
        for n in filer + mappar:
            q = os.path.join(rot, n)
            if not os.path.islink(q):
                os.utime(q, (t, t))
    os.utime(p, (t, t))


def manifest(rot):
    """{relativ sökväg: sha256} för allt i rot/underlag och rot/kunder; en symlänk som sitt mål."""
    ut = {}
    for topp in ('underlag', 'kunder'):
        for r, mappar, filer in os.walk(rot / topp):
            for n in filer + [m for m in mappar if os.path.islink(os.path.join(r, m))]:
                q = Path(r) / n
                ut[q.relative_to(rot).as_posix()] = ('länk:' + os.readlink(q)) if q.is_symlink() else stadning.sha256_fil(q)
    return ut


def nytt_repo(bas, material):
    """En huvudutcheckning med en bar origin (pushad main) och kundmaterial i underlag/ och kunder/ (utanför git)."""
    origin, huvud = bas / 'origin.git', bas / 'repos' / 'nortropic-webb-pro'
    sh('git', 'init', '-q', '--bare', '-b', 'main', origin)
    (huvud / 'kontroller').mkdir(parents=True)
    (huvud / 'kor.sh').write_text('#!/bin/bash\n')
    (huvud / 'kontroller' / 'x.py').write_text('x = 1\n')
    (huvud / '.gitignore').write_text('underlag/\nkunder/\nnode_modules/\ndist/\n.astro/\nkirurgen/\n.env\n__pycache__/\n')
    git('init', '-q', '-b', 'main', cwd=huvud)
    git('add', '-A', cwd=huvud)
    git('commit', '-q', '-m', 'början', cwd=huvud)
    git('remote', 'add', 'origin', origin, cwd=huvud)
    git('push', '-q', '-u', 'origin', 'main', cwd=huvud)
    for rel_, data_ in material.items():
        (huvud / rel_).parent.mkdir(parents=True, exist_ok=True)
        (huvud / rel_).write_bytes(data_)
    return huvud


EGNA, BARN, STOPPADE, LASTA_FD = set(), [], [], []
try:
    # ===== B1 (granskarens scen3): körd ur en full kopia med eget .git raderade 1bcef37 huvudutcheckningen =====
    # Bara det som fanns redan i 1bcef37 används här, så att provet blir rött där av rätt skäl.
    B1 = TMP / 'b1'
    B1_HUVUD = nytt_repo(B1, {'underlag/kund-a/BRIEF.md': b'# Brief\n', 'kunder/kund-a/sajt/src/index.astro': b'<h1>A</h1>\n'})
    B1_REPOS = B1_HUVUD.parent
    B1_W = B1_REPOS / 'nortropic-webb-pro-r90'
    git('worktree', 'add', '-q', '-b', 'r90', B1_W, 'main', cwd=B1_HUVUD)
    (B1_W / 'a.md').write_text('a\n')
    git('add', '-A', cwd=B1_W)
    git('commit', '-q', '-m', 'a', cwd=B1_W)
    B1_KOPIA = B1_REPOS / 'kopia5'
    shutil.copytree(B1_HUVUD, B1_KOPIA, symlinks=True)  # cp -R: eget .git, underlag/ och kunder/
    for d_ in ('tmp', 'scratch', 'lage'):
        (B1 / d_).mkdir()
    stadning.HUVUDUTCHECKNING = B1_HUVUD
    B1_FORE = manifest(B1_HUVUD)

    def b1_ram(repo):
        return stadning.Ram(repo=repo, repos_rot=B1_REPOS, tmp_rot=B1 / 'tmp', scratch_rot=B1 / 'scratch', npm_cache=B1 / 'npm',
                            tillstand=B1 / 'lage', klocka=lambda: T, disk=lambda: (1000, 500), processer=lambda: [],
                            stoppa=lambda pid: (_ for _ in ()).throw(AssertionError('inget stopp i B1')), upptagen=lambda: None)

    rap_b1 = stadning.stada(b1_ram(stadning.huvudutcheckning(B1_KOPIA)), punkter=(1, 2))
    assert B1_HUVUD.is_dir() and (B1_HUVUD / '.git').is_dir() and manifest(B1_HUVUD) == B1_FORE, \
        'B1: körd ur kopian raderade städningen huvudutcheckningen: %s' % [(p['utfall'], p['sokvag']) for p in rap_b1['poster']]
    assert B1_KOPIA.is_dir() and not [p for p in rap_b1['poster'] if p['utfall'] in ('raderad', 'stoppad', 'rensad', 'fel')], rap_b1['poster']
    assert 'inte är huvudutcheckningen' in rap_b1.get('besked', '') or 'varken är huvudutcheckningen' in rap_b1.get('besked', ''), rap_b1.get('besked')
    klar('B1: körd ur en full kopia med eget .git städas ingenting, och huvudutcheckningen med underlag/ och kunder/ står kvar')
    rap_b1w = stadning.stada(b1_ram(B1_W), punkter=(1, 2))  # git rev-parse föll i en worktree: den blev "huvudutcheckningen"
    assert B1_HUVUD.is_dir() and B1_KOPIA.is_dir() and rap_b1w.get('besked') and not [p for p in rap_b1w['poster'] if p['utfall'] == 'raderad']
    (B1_REPOS / 'lank-till-huvud').symlink_to(B1_HUVUD)
    stadning.HUVUDUTCHECKNING = B1_REPOS / 'lank-till-huvud'  # den kanoniska vägen är en symlänk: inget städas
    rap_b1l = stadning.stada(b1_ram(B1_HUVUD), punkter=(1, 2))
    assert B1_KOPIA.is_dir() and 'finns inte som en katalog' in rap_b1l.get('besked', ''), rap_b1l
    stadning.HUVUDUTCHECKNING = B1_HUVUD
    klar('B1: en worktree som blev "huvudutcheckningen" när git inte svarade, och en kanonisk väg som är en symlänk, städar inget')
    (B1_REPOS / 'kopia-symlank').symlink_to(B1_HUVUD)  # heter kopia men är en länk till huvudutcheckningen
    rap_b1h = stadning.stada(b1_ram(B1_HUVUD), punkter=(1, 2))
    assert not B1_KOPIA.exists() and [p['utfall'] for p in rap_b1h['poster'] if p['sokvag'] == str(B1_KOPIA)] == ['raderad'], rap_b1h['poster']
    assert B1_HUVUD.is_dir() and manifest(B1_HUVUD) == B1_FORE and (B1_REPOS / 'kopia-symlank').is_symlink() and B1_W.is_dir()
    assert not [p for p in rap_b1h['poster'] if 'kopia-symlank' in str(p['sokvag'])], 'en länk som heter kopia är ingen kopia'
    egen_kanon = B1_REPOS / 'kopia9'  # huvudutcheckningen heter som en kopia: den är ändå aldrig en kopia
    (egen_kanon / 'kontroller').mkdir(parents=True)
    (egen_kanon / 'kor.sh').write_text('')
    (egen_kanon / '.git').mkdir()
    stadning.HUVUDUTCHECKNING = egen_kanon
    assert egen_kanon not in [d for d, _k in stadning.kopior(b1_ram(egen_kanon), [])[0]], 'den kanoniska vägen räknas aldrig som en kopia'
    stadning.HUVUDUTCHECKNING = B1_HUVUD
    klar('B1: körd ur huvudutcheckningen raderas den fulla kopian; en länk som heter kopia och en kanonisk väg som heter kopia rörs inte')

    # ===== huvudutcheckningen, origin och kundmaterialet =====
    MATERIAL = {'underlag/kund-a/BRIEF.md': b'# Brief\n', 'underlag/kund-a/bilder/jobb.jpg': b'\xff\xd8\xff' + bytes(range(256)) * 8,
                'underlag/kund-a/DESIGNDOMAR.jsonl': b'{"dom": "ny riktning"}\n', 'kunder/kund-a/sajt/src/pages/index.astro': b'<h1>Kund A</h1>\n',
                'kunder/kund-a/sajt/package.json': b'{"name": "kund-a"}\n', 'kunder/kund-a/sajt/node_modules/paket/index.js': b'module.exports = 1\n',
                'kirurgen/spaning/SENAST.json': b'{"slut": "2026-10-06"}\n'}
    HUVUD = nytt_repo(TMP / 'a', MATERIAL)
    REPOS = HUVUD.parent
    stadning.HUVUDUTCHECKNING = HUVUD

    def worktree(gren, commit=True):
        wt = REPOS / ('nortropic-webb-pro-' + gren)
        git('worktree', 'add', '-q', '-b', gren, wt, 'main', cwd=HUVUD)
        if commit:
            (wt / (gren + '.md')).write_text(gren + '\n')
            git('add', '-A', cwd=wt)
            git('commit', '-q', '-m', gren, cwd=wt)
        return wt

    SAMMAN = ('klar', 'smutsig', 'material', 'aktiv', 'anvand', 'kirurg', 'env', 'last', 'race')
    WT = {g: worktree(g) for g in SAMMAN}
    git('merge', '-q', '--no-ff', '-m', 'sammanslagning', *SAMMAN, cwd=HUVUD)
    (HUVUD / 'kontroller' / 'x.py').write_text('x = 2\n')  # main går vidare: den gamla versionen finns bara i historiken
    git('commit', '-q', '-am', 'x = 2', cwd=HUVUD)
    git('push', '-q', 'origin', 'main', cwd=HUVUD)
    WT['ny'] = worktree('ny', commit=False)            # Ö2: ny gren utan egen commit, på det pushade main
    WT['pagar'] = worktree('pagar')                    # inte sammanslagen
    WT['lokal'] = worktree('lokal')
    git('merge', '-q', '--no-ff', '-m', 'lokal', 'lokal', cwd=HUVUD)  # sammanslagen men inte pushad
    (WT['smutsig'] / 'smutsig.md').write_text('ändrad men inte committad\n')
    EGET_WT = b'bara i worktreen\n'
    (WT['material'] / 'underlag' / 'kund-b').mkdir(parents=True)
    (WT['material'] / 'underlag' / 'kund-b' / 'ANTECKNING.md').write_bytes(EGET_WT)
    (WT['kirurg'] / 'kirurgen' / 'uppladdat' / '20261006').mkdir(parents=True)  # B2: ägarens uppladdning (ignorerad)
    (WT['kirurg'] / 'kirurgen' / 'uppladdat' / '20261006' / 'agarens.pdf').write_bytes(b'%PDF-1.4 bara har\n')
    (WT['env'] / '.env').write_text('NYCKEL=bara-har\n')  # B2: en nyckel (ignorerad)
    for rel_ in ('kunder/rokprov-mall/prov/STATUS.json', 'underlag/rokprov-mall/BESTALLNING.md', 'kunder/kund-a/sajt/node_modules/x/i.js',
                 'kontroller/__pycache__/x.cpython-312.pyc'):
        (WT['klar'] / rel_).parent.mkdir(parents=True, exist_ok=True)  # rökprovets fixtur och det härledda: inget material
        (WT['klar'] / rel_).write_text('{}\n')
    with open(HUVUD / '.git' / 'info' / 'exclude', 'a') as f_:  # som .venv-länken i en riktig worktree
        f_.write('lank-som-venv\n')
    os.symlink(HUVUD / 'kontroller', WT['klar'] / 'lank-som-venv')  # följs aldrig
    git('worktree', 'lock', '--reason', 'pågår', WT['last'], cwd=HUVUD)
    os.utime(WT['aktiv'] / 'aktiv.md', (T - 3600, T - 3600))  # ändrad det senaste dygnet

    def kopia(namn, med_git=True):
        d = REPOS / namn
        shutil.copytree(HUVUD, d, symlinks=True, ignore=None if med_git else shutil.ignore_patterns('.git'))
        return d

    EGEN_1, EGEN_2 = b'bara i kopian\n', b'<h1>Kund A, ny rubrik</h1>\n'
    K = {}
    K['material'] = kopia('kopia-material')
    (K['material'] / 'underlag' / 'kund-a' / 'ANTECKNINGAR.md').write_bytes(EGEN_1)
    (K['material'] / 'kunder' / 'kund-a' / 'sajt' / 'src' / 'pages' / 'index.astro').write_bytes(EGEN_2)  # samma sökväg, annat innehåll
    K['tom'] = kopia('kopia4')
    for rel_ in ('kunder/kund-a/sajt/dist/index.html', 'kunder/kund-a/sajt/.astro/typer.d.ts', 'kunder/kund-a/sajt/node_modules/ny/index.js',
                 'kunder/rokprov-mall/prov/STATUS.json', 'underlag/rokprov-mall/BESTALLNING.md', 'underlag/kund-a/.DS_Store'):
        (K['tom'] / rel_).parent.mkdir(parents=True, exist_ok=True)
        (K['tom'] / rel_).write_text('provets egna\n')
    os.symlink(HUVUD / 'kunder', K['tom'] / 'kunder' / 'lank-till-huvudutcheckningen')  # följs aldrig
    K['utan_git_ren'] = kopia('kopia-utan-git-ren', med_git=False)  # utan .git, allt finns i huvudutcheckningen
    K['gammal_version'] = kopia('kopia-gammal-version', med_git=False)
    (K['gammal_version'] / 'kontroller' / 'x.py').write_text('x = 1\n')  # en version som bara finns i huvudutcheckningens git
    K['utan_git'] = kopia('kopia-utan-git', med_git=False)  # B2/K3: ändrad kod och en anteckning i roten
    (K['utan_git'] / 'kontroller' / 'x.py').write_text('x = 99  # bara här\n')
    (K['utan_git'] / 'ANTECKNINGAR-agaren.md').write_text('ägarens ord, bara här\n')
    K['kirurg'] = kopia('kopia-kirurgen')  # B2: ägarens uppladdning i kirurgen/
    (K['kirurg'] / 'kirurgen' / 'uppladdat' / '20261006').mkdir(parents=True)
    (K['kirurg'] / 'kirurgen' / 'uppladdat' / '20261006' / 'agarens.pdf').write_bytes(b'%PDF-1.4 bara har\n')
    K['dist'] = kopia('kopia-dist')  # K2: ett hämtat dist/ i underlag/ är material
    (K['dist'] / 'underlag' / 'kund-a' / 'referens' / 'dist').mkdir(parents=True)
    (K['dist'] / 'underlag' / 'kund-a' / 'referens' / 'dist' / 'unik.css').write_text('body{}\n')
    K['frikopplad'] = kopia('kopia-frikopplad')  # Ö1: en commit på en frikopplad HEAD
    git('checkout', '-q', '--detach', cwd=K['frikopplad'])
    (K['frikopplad'] / 'kontroller' / 'eget.py').write_text('eget = 1\n')
    git('add', '-A', cwd=K['frikopplad'])
    git('commit', '-q', '-m', 'egen commit på frikopplad HEAD', cwd=K['frikopplad'])
    git('checkout', '-q', 'main', cwd=K['frikopplad'])
    K['stash'] = kopia('kopia-stash')  # Ö1: en unik ändring bara i stash@{1}
    (K['stash'] / 'kontroller' / 'x.py').write_text('x = 3  # viktig ändring\n')
    git('stash', 'push', '-q', '-m', 'äldre', cwd=K['stash'])
    (K['stash'] / 'kontroller' / 'x.py').write_text('x = 4\n')
    git('stash', 'push', '-q', '-m', 'överst', cwd=K['stash'])
    git('fetch', '-q', K['stash'], 'refs/stash:refs/heads/stash-topp', cwd=HUVUD)  # toppen finns i huvudutcheckningen
    K['koad'] = kopia('kopia-koad')  # en köad unik ändring; arbetsträdet är som huvudutcheckningen
    (K['koad'] / 'kontroller' / 'x.py').write_text('x = 7  # köad, bara här\n')
    git('add', 'kontroller/x.py', cwd=K['koad'])
    (K['koad'] / 'kontroller' / 'x.py').write_text('x = 2\n')
    K['commit'] = kopia('kopia-commit')
    (K['commit'] / 'kontroller' / 'eget.py').write_text('eget = 1\n')
    git('add', '-A', cwd=K['commit'])
    git('commit', '-q', '-m', 'en egen commit', cwd=K['commit'])
    K['olasbar_kat'] = kopia('kopia-olasbar-katalog')  # Ö7: en oläsbar katalog
    (K['olasbar_kat'] / 'underlag' / 'kund-a' / 'hemlig').mkdir()
    (K['olasbar_kat'] / 'underlag' / 'kund-a' / 'hemlig' / 'x.md').write_text('bara här\n')
    K['olasbar_fil'] = kopia('kopia-olasbar-fil')  # Ö7: en oläsbar fil som finns i huvudutcheckningen
    K['olasbar_nm'] = kopia('kopia-olasbar-node-modules')  # Ö7: oläsbart i node_modules: annars raderas kopian bara till hälften
    (K['olasbar_nm'] / 'kunder' / 'kund-a' / 'sajt' / 'node_modules' / 'last').mkdir()
    (K['olasbar_nm'] / 'kunder' / 'kund-a' / 'sajt' / 'node_modules' / 'last' / 'i.js').write_text('x')
    K['lankmal'] = kopia('kopia-lankmal')  # K1: huvudutcheckningen länkar in hit
    (K['lankmal'] / 'kunder' / 'kund-a' / 'bild.jpg').write_bytes(b'\xff\xd8 bara har\n')
    K['anvand'] = kopia('kopia-anvand')
    K['logo'] = kopia('kopia-logo')  # filen finns bara bakom en länk i huvudutcheckningen: material (lstat, inte stat)
    (K['logo'] / 'kunder' / 'kund-a' / 'logo.png').write_bytes(b'logo bara utanfor\n')
    K['server'] = kopia('nortropic-webb-pro-kopia-server')
    K['okand'] = REPOS / 'kopia-okand'
    K['okand'].mkdir()
    (K['okand'] / 'anteckning.txt').write_text('okänt ursprung\n')
    GAMMAL_UTCHECKNING = kopia('nortropic-webb-pro-r68')  # repots kännetecken men heter inte kopia
    ANNAT = REPOS / 'annat-projekt'
    ANNAT.mkdir()
    (ANNAT / 'fil.txt').write_text('ägarens\n')

    # --- /tmp, $TMPDIR och scratchpad ---
    TMPROT, TMPDIR_ROT = TMP / 'tmp', TMP / 'tmpdir'
    TMPDIR_ROT.mkdir()
    for n_ in ('nwp-skill-gammal', 'nwp-pip-anvand', 'nwp-motor-ung', 'nwp-pip-mal', 'okand-katalog', 'nwp-korningar', 'nwp-bygge-prov',
               'agarens-server', 'nwp-forhand-a', 'nwp-forhand-b', 'nwp-forhand-c', 'nwp-forhand-d', 'nwp-forhand-e', 'nwp-forhand-f',
               'nwp-forhand-g', 'nwp-forhand-h'):
        (TMPROT / n_).mkdir(parents=True)
        (TMPROT / n_ / 'fil.txt').write_text(n_)
    (TMPROT / 'nwp-lh-en-fil').write_text('en fil, ingen katalog\n')
    os.utime(TMPROT / 'nwp-motor-ung' / 'fil.txt', (T - 3600, T - 3600))
    # K1: huvudutcheckningen länkar in i en kopia och i en tempkatalog
    (HUVUD / 'kunder' / 'kund-a' / 'bild.jpg').symlink_to(K['lankmal'] / 'kunder' / 'kund-a' / 'bild.jpg')
    (HUVUD / 'underlag' / 'kund-a' / 'lank-till-tmp').symlink_to(TMPROT / 'nwp-pip-mal')
    (TMP / 'logo-utanfor.png').write_bytes(b'logo bara utanfor\n')
    (HUVUD / 'kunder' / 'kund-a' / 'logo.png').symlink_to(TMP / 'logo-utanfor.png')
    SCR = TMP / 'scratch' / 'claude-501'
    KONFIG = TMP / 'claude-konfig' / 'projects'
    CLAUDE_CWD = TMP / 'en-annan-arbetskatalog'
    CLAUDE_CWD.mkdir()
    PROJ_OKAND = stadning.projektnamn(os.path.realpath(CLAUDE_CWD))
    UU = {n: '%08d-1111-2222-3333-%012d' % (i, i) for i, n in enumerate(
        ('gammal', 'ung', 'anvand', 'arg', 'oppen', 'okand', 'transkript', 'ej-session'), 1)}
    S = {n: SCR / '-Users-prov' / u for n, u in UU.items() if n not in ('okand',)}
    S['okand'] = SCR / PROJ_OKAND / UU['okand']
    S['ej'] = SCR / '-Users-prov' / 'inte-en-session'
    S['annat'] = SCR / 'bash-edit-diff'
    for s_ in S.values():
        (s_ / 'scratchpad').mkdir(parents=True)
        (s_ / 'scratchpad' / 'anteckning.md').write_text('x\n')
        satt_tid(s_, T - 8 * DYGN)
    os.utime(S['ung'] / 'scratchpad' / 'anteckning.md', (T - 6 * DYGN, T - 6 * DYGN))
    os.utime(S['gammal'] / 'scratchpad', (T - 3600, T - 3600))  # katalogens mtime flyttad av en borttagning: fortfarande gammal
    (KONFIG / '-Users-prov' / UU['oppen'] / 'subagents').mkdir(parents=True)
    OPPEN_FIL = KONFIG / '-Users-prov' / UU['oppen'] / 'subagents' / 'agent-x.jsonl'
    OPPEN_FIL.write_text('{}\n')
    satt_tid(KONFIG / '-Users-prov' / UU['oppen'], T - 8 * DYGN)
    (KONFIG / '-Users-prov' / (UU['transkript'] + '.jsonl')).write_text('{}\n')
    os.utime(KONFIG / '-Users-prov' / (UU['transkript'] + '.jsonl'), (T - 2 * DYGN, T - 2 * DYGN))
    UTANFOR = TMP / 'utanfor'
    UTANFOR.mkdir()
    NPM, LAGE = TMP / 'npm', TMP / 'lage'
    vl.skriv_json(LAGE / 'NPM-CACHE.json', {'tid': iso(T - DYGN)})  # färsk rensning: punkt 5 rensar inget i huvudkörningarna
    (NPM / '_cacache' / 'content-v2').mkdir(parents=True)
    (NPM / '_cacache' / 'content-v2' / 'paket').write_bytes(b'x' * 5000)
    LAS = TMP / 'stadning.las'
    FORE = manifest(HUVUD)
    assert len(FORE) == len([r for r in MATERIAL if r.startswith(('underlag/', 'kunder/'))]) + 3, FORE

    # --- provets egna processer ---
    def vanta_pa(pid, namn, utan_foralder):
        for _ in range(200):
            if korregister.ps('command', pid).startswith(namn) and (not utan_foralder or korregister.ps('ppid', pid) == '1'):
                return pid
            time.sleep(0.05)
        raise AssertionError('pid %d blev aldrig "%s" (ppid 1: %s): %r' % (pid, namn, utan_foralder, korregister.ps('command', pid)))

    def foraldralos(katalog, namn, ignorera_term=False):
        """En process utan levande förälder (ppid 1) med namnet som kommando och arbetskatalogen katalog."""
        kmd = '(cd "$1" && %sexec -a "$2" sleep 600) </dev/null >/dev/null 2>&1 & echo $!' % ("trap '' TERM && " if ignorera_term else '')
        r = subprocess.run(['bash', '-c', kmd, 'prov', str(katalog), namn], capture_output=True, text=True, timeout=30)
        pid = int(r.stdout.strip())
        EGNA.add(pid)
        return vanta_pa(pid, namn, True)

    def med_foralder(katalog, namn, oppna=None):
        kmd = ('exec 3<"$2"; ' if oppna else '') + 'exec -a "$1" sleep 600'
        p = subprocess.Popen(['bash', '-c', kmd, 'prov', namn] + ([str(oppna)] if oppna else []), cwd=str(katalog),
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        EGNA.add(p.pid)
        BARN.append(p)
        return vanta_pa(p.pid, namn, False)

    FALSK_START = {}

    def egna_processer():
        alla = stadning.las_processer()
        assert alla is not None, 'ps svarar inte'
        ut = [dict(x) for x in alla if x['pid'] in EGNA]
        for x in ut:
            if x['pid'] in FALSK_START:  # som en återanvänd pid: listan säger en annan starttid än processen har
                x['lstart'], x['start'] = 'Mon Jan  1 00:00:00 2024', T - 900 * DYGN
        return ut

    def stoppa(pid):
        assert pid in EGNA, 'provet stoppar bara sina egna processer (pid %d)' % pid
        STOPPADE.append(pid)
        os.kill(pid, signal.SIGTERM)

    def ram(klocka=lambda: T, disk=None, torr=False, upptagen=lambda: None, processer=None, tillstand=None, npm_pagar=lambda: None):
        return stadning.Ram(repo=HUVUD, repos_rot=REPOS, tmp_rot=TMPROT, tmp_extra=[TMPDIR_ROT], scratch_rot=SCR, npm_cache=NPM,
                            tillstand=tillstand or LAGE, claude_projekt=KONFIG, las=LAS, klocka=klocka,
                            disk=disk or (lambda: (1000 * 2 ** 30, 500 * 2 ** 30)), processer=processer or egna_processer, stoppa=stoppa,
                            upptagen=upptagen, npm_pagar=npm_pagar, torr=torr, vanta_stopp=3)

    def poster(rap, sokvag=None, punkt=None):
        return [p for p in rap['poster'] if (sokvag is None or p['sokvag'] == str(sokvag)) and (punkt is None or p['punkt'] == punkt)]

    def en(rap, sokvag, punkt=None):
        x = poster(rap, sokvag, punkt)
        assert len(x) == 1, (str(sokvag), x)
        return x[0]

    P = {}
    P['astro'] = foraldralos(TMPROT / 'nwp-forhand-a', 'astro preview')  # stoppas
    P['utanfor'] = foraldralos(UTANFOR, 'astro preview')  # utanför räckvidden: lämnas
    P['agarens_tmp'] = foraldralos(TMPROT / 'agarens-server', 'python3 -m http.server 8001')  # ägarens katalog i /tmp: lämnas (K4)
    P['foralder'] = med_foralder(TMPROT / 'nwp-forhand-b', 'astro dev')  # levande förälder: lämnas
    P['http'] = foraldralos(WT['pagar'], 'python3 -m http.server 8000')  # i en worktree: stoppas
    P['4771'] = foraldralos(TMPROT / 'nwp-forhand-c', '.venv/bin/python -B dashboard/server.py --port 4771')  # ägarens: lämnas
    P['utan_port'] = foraldralos(TMPROT / 'nwp-forhand-f', '.venv/bin/python -B dashboard/server.py')  # utan --port är 4771: lämnas
    P['4772'] = foraldralos(TMPROT / 'nwp-forhand-d', '.venv/bin/python -B dashboard/server.py --port 4772')  # stoppas
    P['sleep'] = foraldralos(TMPROT / 'nwp-forhand-e', 'sleep')  # inte en server: lämnas
    P['kopia'] = foraldralos(K['server'], 'astro preview')  # håller kopian: stoppas, och kopian raderas
    P['term'] = foraldralos(TMPROT / 'nwp-forhand-g', 'astro preview', ignorera_term=True)  # går inte att stoppa: FEL
    P['falsk_id'] = foraldralos(TMPROT / 'nwp-forhand-h', 'astro preview')  # listans starttid stämmer inte: lämnas
    FALSK_START[P['falsk_id']] = True
    U = {'kopia': med_foralder(K['anvand'], 'sleep'), 'tmp': med_foralder(TMPROT / 'nwp-pip-anvand', 'sleep'),
         'scr': med_foralder(S['anvand'], 'sleep'), 'wt': med_foralder(WT['anvand'], 'sleep'),
         'claude_arg': med_foralder(UTANFOR, 'claude --resume=%s' % UU['arg']), 'claude_okand': med_foralder(CLAUDE_CWD, 'claude'),
         'oppen': med_foralder(UTANFOR, 'lasare', oppna=OPPEN_FIL)}
    lasta = {x['pid']: x for x in egna_processer()}
    assert set(lasta) == EGNA and lasta[P['kopia']]['cwd'] == str(K['server']) and lasta[P['astro']]['ppid'] == 1, lasta
    assert lasta[P['foralder']]['ppid'] == os.getpid() and all(x['start'] and x['lstart'] for x in lasta.values())
    assert any(f == str(OPPEN_FIL) for f in lasta[U['oppen']]['filer']), lasta[U['oppen']]['filer']
    klar('processlistan: ps och lsof ger förälder, start, kommando, arbetskatalog och öppna filer för provets processer')
    os.chmod(K['olasbar_kat'] / 'underlag' / 'kund-a' / 'hemlig', 0)
    os.chmod(K['olasbar_fil'] / 'kunder' / 'kund-a' / 'sajt' / 'src' / 'pages' / 'index.astro', 0)
    os.chmod(K['olasbar_nm'] / 'kunder' / 'kund-a' / 'sajt' / 'node_modules' / 'last', 0)

    # ===== yngre än ett dygn (provets klocka är den riktiga): inget stoppas och inget raderas =====
    rap0 = stadning.stada(ram(klocka=time.time), punkter=(1, 2, 3, 4))
    farliga0 = [p for p in rap0['poster'] if p['utfall'] in ('raderad', 'stoppad', 'fel')]
    assert not farliga0 and not STOPPADE and all(korregister.lever(p) for p in EGNA), farliga0
    assert 'yngre än ett dygn' in en(rap0, TMPROT / 'nwp-forhand-a', 3)['skal'] and 'ändrad det senaste dygnet' in en(rap0, WT['klar'], 1)['skal']
    assert 'ändrad det senaste dygnet' in en(rap0, K['tom'], 2)['skal'] and 'ändrad det senaste dygnet' in en(rap0, WT['ny'], 1)['skal']
    klar('yngre än ett dygn: processen, worktreen, den nya worktreen och kopian lämnas')

    # ===== torrläget: listan, inget ändrat =====
    LAS.unlink(missing_ok=True)
    rapA = stadning.stada(ram(torr=True))
    assert rapA['torr'] and not STOPPADE and all(korregister.lever(p) for p in EGNA), STOPPADE
    for d_, pk_ in ((K['tom'], 2), (K['server'], 2), (WT['klar'], 1), (TMPROT / 'nwp-skill-gammal', 4), (S['gammal'], 4)):
        assert d_.exists() and en(rapA, d_, pk_)['utfall'] == 'skulle raderas', (d_, poster(rapA, d_))
    for d_ in (TMPROT / 'nwp-forhand-a', TMPROT / 'nwp-forhand-d', WT['pagar'], K['server']):
        assert en(rapA, d_, 3)['utfall'] == 'skulle stoppas', poster(rapA, d_, 3)
    assert manifest(HUVUD) == FORE and not [p for p in rapA['poster'] if p['utfall'] in ('raderad', 'stoppad', 'rensad')]
    assert 'Torrläge: inget ändrat' in '\n'.join(stadning.markdown(rapA)) and not LAS.exists(), 'torrläget tar inget lås och skriver inget'
    klar('torrläget listar vad som skulle göras och ändrar ingenting')

    # ===== städningen på riktigt; git worktree remove utan --force när worktreen blir smutsig i sista stund (Ö7) =====
    git_orig = stadning.git

    def git_med_sen_fil(*a, **k):
        if a[:2] == ('worktree', 'remove') and Path(a[-1]) == WT['race']:
            (WT['race'] / 'sen-fil.txt').write_text('skapad efter prövningen\n')
        return git_orig(*a, **k)

    stadning.git = git_med_sen_fil
    try:
        rapB = stadning.stada(ram())
    finally:
        stadning.git = git_orig
    fel_ = [p for p in rapB['poster'] if p['utfall'] == 'fel']
    assert {p['sokvag'] for p in fel_} == {str(WT['race']), str(TMPROT / 'nwp-forhand-g')}, fel_
    assert WT['race'].is_dir() and (WT['race'] / 'sen-fil.txt').is_file() and 'git worktree remove föll' in en(rapB, WT['race'], 1)['skal']
    klar('git worktree remove körs utan --force: en worktree som blir smutsig i sista stund står kvar, med felet')

    # kopior
    p_ = en(rapB, K['material'])
    assert K['material'].is_dir() and p_['utfall'] == 'väntar på ägaren' and p_['material_antal'] == 2, p_
    assert {(m['sokvag'], m['storlek']) for m in p_['material']} == {('underlag/kund-a/ANTECKNINGAR.md', len(EGEN_1)),
                                                                   ('kunder/kund-a/sajt/src/pages/index.astro', len(EGEN_2))}, p_['material']
    md_ = '\n'.join(stadning.markdown(rapB))
    assert '`underlag/kund-a/ANTECKNINGAR.md` (%d B)' % len(EGEN_1) in md_ and '**Väntar på ägaren**' in md_, md_
    klar('en kopia med eget kundmaterial står kvar och väntar på ägaren, med listan (sökväg och storlek)')
    for k_ in ('tom', 'utan_git_ren', 'gammal_version', 'server'):
        assert not K[k_].exists() and en(rapB, K[k_], 2)['utfall'] == 'raderad', (k_, poster(rapB, K[k_]))
    klar('en kopia utan eget material raderas: det härledda, testsajten, en länk och en version ur huvudutcheckningens git är inget material')
    for k_, del_ in (('utan_git', 'ANTECKNINGAR-agaren.md'), ('kirurg', 'kirurgen/uppladdat/20261006/agarens.pdf'),
                     ('dist', 'underlag/kund-a/referens/dist/unik.css'), ('logo', 'kunder/kund-a/logo.png')):
        p_ = en(rapB, K[k_], 2)
        assert K[k_].is_dir() and p_['utfall'] == 'väntar på ägaren' and del_ in [m['sokvag'] for m in p_['material']], (k_, p_)
    assert 'kontroller/x.py' in [m['sokvag'] for m in en(rapB, K['utan_git'], 2)['material']]
    klar('B2: kirurgens uppladdning, ändrad kod och en anteckning i roten och ett hämtat dist/ är eget material i en kopia')
    for k_, del_ in (('frikopplad', 'egen commit'), ('stash', 'egen commit'), ('koad', 'ocommittad ändring'), ('commit', 'egen commit')):
        p_ = en(rapB, K[k_], 2)
        assert K[k_].is_dir() and p_['utfall'] == 'väntar på ägaren' and del_ in p_['skal'], (k_, p_)
    klar('Ö1: en commit på en frikopplad HEAD, stash@{1}, en köad ändring och en egen gren i en kopia väntar på ägaren')
    for k_ in ('olasbar_kat', 'olasbar_fil', 'olasbar_nm'):
        assert K[k_].is_dir() and en(rapB, K[k_], 2)['utfall'] == 'väntar på ägaren', (k_, poster(rapB, K[k_]))
    assert (K['olasbar_nm'] / 'kontroller' / 'x.py').is_file() and (K['olasbar_nm'] / 'underlag' / 'kund-a' / 'BRIEF.md').is_file(), 'inget raderat till hälften'
    try:
        stadning.eget_material(K['olasbar_kat'], HUVUD)
        raise AssertionError('en oläsbar katalog ska fälla jämförelsen')
    except PermissionError:
        pass
    klar('Ö7: en kopia med en oläsbar katalog eller fil går inte att jämföra och väntar på ägaren')
    assert K['anvand'].is_dir() and en(rapB, K['anvand'])['utfall'] == 'kvar' and 'pid %d' % U['kopia'] in en(rapB, K['anvand'])['skal']
    assert K['okand'].is_dir() and en(rapB, K['okand'])['utfall'] == 'väntar på ägaren' and 'okänt ursprung' in en(rapB, K['okand'])['skal']
    assert GAMMAL_UTCHECKNING.is_dir() and 'heter inte kopia' in en(rapB, GAMMAL_UTCHECKNING)['skal']
    assert ANNAT.is_dir() and not poster(rapB, ANNAT) and (ANNAT / 'fil.txt').read_text() == 'ägarens\n'
    lank_ = HUVUD / 'kunder' / 'kund-a' / 'bild.jpg'
    assert K['lankmal'].is_dir() and lank_.is_file() and 'huvudutcheckningen länkar hit' in en(rapB, K['lankmal'], 2)['skal']
    assert (TMPROT / 'nwp-pip-mal').is_dir() and 'huvudutcheckningen länkar hit' in en(rapB, TMPROT / 'nwp-pip-mal', 4)['skal']
    klar('kopior som används, av okänt ursprung, som inte heter kopia eller som huvudutcheckningen länkar till står kvar')

    # huvudutcheckningen
    assert manifest(HUVUD) == FORE and (HUVUD / '.git').is_dir() and git('status', '--porcelain', cwd=HUVUD) == ''
    r_ = ram()
    r_.worktree_vagar = [Path(os.path.realpath(w)) for w in WT.values() if w.is_dir()]
    (REPOS / 'lank-till-material').symlink_to(K['material'])
    for p_s in (HUVUD, HUVUD / 'kunder', HUVUD / 'underlag', HUVUD / 'underlag' / 'kund-a', HUVUD / 'kontroller', REPOS, TMPROT, SCR, UTANFOR,
                WT['material'], REPOS / 'lank-till-material'):
        assert stadning.radera(r_, p_s).startswith('raderas aldrig') and p_s.exists(), p_s
    assert manifest(HUVUD) == FORE and K['material'].is_dir()
    klar('huvudutcheckningen är byte för byte oförändrad, och skyddet vägrar radera den, en worktree och en symlänk')

    # worktrees
    assert not WT['klar'].exists() and en(rapB, WT['klar'], 1)['utfall'] == 'raderad' and en(rapB, WT['klar'], 1)['gren'] == 'klar'
    assert git('rev-parse', '--verify', '-q', 'refs/heads/klar', cwd=HUVUD).strip() and str(WT['klar']) not in git('worktree', 'list', cwd=HUVUD)
    assert (HUVUD / 'kontroller').is_dir(), 'länken i worktreen följdes inte'
    klar('en sammanslagen och pushad worktree med egna commits tas bort med git worktree remove, och grenen finns kvar')
    for g_, del_ in (('pagar', 'inte sammanslagen'), ('smutsig', 'ocommittade ändringar'), ('lokal', 'inte pushad'),
                     ('aktiv', 'ändrad det senaste dygnet'), ('anvand', 'pid %d' % U['wt']), ('last', 'låst')):
        p_ = en(rapB, WT[g_], 1)
        assert WT[g_].is_dir() and p_['utfall'] == 'kvar' and del_ in p_['skal'], (g_, p_)
    klar('osammanslagen, ocommittad, inte pushad, ändrad nyss, använd och låst worktree står kvar')
    p_ = en(rapB, WT['ny'], 1)
    assert WT['ny'].is_dir() and p_['utfall'] == 'väntar på ägaren' and 'okänd' in p_['skal'] and 'egen commit' in p_['skal'], p_
    klar('Ö2: en ny worktree utan egen commit tas inte bort, utan väntar på ägaren efter ett dygn')
    for g_, del_ in (('material', 'underlag/kund-b/ANTECKNING.md'), ('kirurg', 'kirurgen/uppladdat/20261006/agarens.pdf'), ('env', '.env')):
        p_ = en(rapB, WT[g_], 1)
        assert WT[g_].is_dir() and p_['utfall'] == 'väntar på ägaren' and [m['sokvag'] for m in p_['material']] == [del_], (g_, p_)
    assert (WT['env'] / '.env').read_text() == 'NYCKEL=bara-har\n' and (WT['smutsig'] / 'smutsig.md').read_text() == 'ändrad men inte committad\n'
    klar('B2: en worktree med eget material, ägarens uppladdning i kirurgen/ eller en .env väntar på ägaren; git worktree remove körs inte')

    # processer
    stoppade_ = {P['astro'], P['http'], P['4772'], P['kopia']}
    assert set(STOPPADE) == stoppade_ | {P['term']} and not any(korregister.lever(p) for p in stoppade_), (STOPPADE, stoppade_)
    for d_ in (TMPROT / 'nwp-forhand-a', TMPROT / 'nwp-forhand-d', WT['pagar'], K['server']):
        assert en(rapB, d_, 3)['utfall'] == 'stoppad' and en(rapB, d_, 3)['pid'] in stoppade_, poster(rapB, d_, 3)
    assert not K['server'].exists() and en(rapB, K['server'], 2)['utfall'] == 'raderad', 'förhandsvisningen stoppas före kopian den höll'
    klar('föräldralösa servrar inom räckvidden (astro preview, http.server, dashboard på 4772) stoppas med SIGTERM')
    assert korregister.lever(P['term']) and 'lever 3 s efter SIGTERM' in en(rapB, TMPROT / 'nwp-forhand-g', 3)['skal']
    assert korregister.lever(P['falsk_id']) and P['falsk_id'] not in STOPPADE and 'återanvänd' in en(rapB, TMPROT / 'nwp-forhand-h', 3)['skal']
    os.kill(P['term'], signal.SIGKILL)  # resten av provet ska inte vänta på den
    klar('Ö7: en process som lever efter SIGTERM ger FEL, och en pid vars starttid inte stämmer stoppas aldrig')
    assert all(korregister.lever(P[n]) for n in ('utanfor', 'agarens_tmp', 'foralder', '4771', 'utan_port', 'sleep'))
    assert not poster(rapB, UTANFOR) and not poster(rapB, TMPROT / 'nwp-forhand-e') and not poster(rapB, TMPROT / 'agarens-server')
    assert 'föräldern lever' in en(rapB, TMPROT / 'nwp-forhand-b', 3)['skal']
    for d_ in ('nwp-forhand-c', 'nwp-forhand-f'):
        assert 'ägarens dashboard' in en(rapB, TMPROT / d_, 3)['skal'], d_
    klar('utanför räckvidden, ägarens katalog i /tmp, levande förälder, inte en server och dashboarden på 4771 (med eller utan --port) lämnas')

    # tillfälliga kataloger och scratchpad
    assert not (TMPROT / 'nwp-skill-gammal').exists() and en(rapB, TMPROT / 'nwp-skill-gammal')['utfall'] == 'raderad'
    for d_ in ('okand-katalog', 'nwp-motor-ung', 'nwp-korningar', 'nwp-bygge-prov', 'nwp-lh-en-fil'):
        assert (TMPROT / d_).exists() and not poster(rapB, TMPROT / d_), d_
    assert (TMPROT / 'nwp-pip-anvand').is_dir() and 'pid %d' % U['tmp'] in en(rapB, TMPROT / 'nwp-pip-anvand')['skal']
    klar('en gammal tempkatalog med känt prefix raderas; en okänd, en ung, en fast och en som används lämnas')
    assert not S['gammal'].exists() and en(rapB, S['gammal'])['utfall'] == 'raderad'
    assert S['ung'].is_dir() and not poster(rapB, S['ung']) and S['ej'].is_dir() and S['annat'].is_dir()
    assert S['anvand'].is_dir() and 'pid %d' % U['scr'] in en(rapB, S['anvand'])['skal']
    klar('scratchpad: en övergiven session raderas efter sju dygn, också när en katalogs mtime flyttats; yngre, använda och annat lämnas')
    for n_, del_ in (('arg', 'pid %d nämner sessionens id' % U['claude_arg']), ('oppen', 'pid %d har %s öppen' % (U['oppen'], OPPEN_FIL)),
                     ('okand', 'pid %d i samma projekt' % U['claude_okand']), ('transkript', 'transkriptet ändrades')):
        p_ = en(rapB, S[n_], 4)
        assert S[n_].is_dir() and p_['utfall'] == 'kvar' and del_ in p_['skal'], (n_, p_)
    klar('Ö3: en levande sessions scratchpad står kvar (id i argumenten, en öppen fil, okänt id i samma projekt, färskt transkript)')

    # ===== Ö7: okända worktrees och processer rör ingenting =====
    K['extra'] = kopia('kopia-extra')
    (TMPROT / 'nwp-skill-extra').mkdir()
    (TMPROT / 'nwp-skill-extra' / 'x').write_text('x')
    worktrees_orig = stadning.worktrees
    stadning.worktrees = lambda r: None
    try:
        rap_w = stadning.stada(ram(), punkter=(1, 2))
    finally:
        stadning.worktrees = worktrees_orig
    assert K['extra'].is_dir() and 'worktrees okända' in str(rap_w['poster']) and not poster(rap_w, K['extra']), rap_w['poster']
    for proc_, del_ in ((lambda: None, 'processerna kunde inte läsas'), (lambda: [dict(x, cwd_kand=False, cwd=None, filer=[]) for x in egna_processer()], 'lsof')):
        rap_p = stadning.stada(ram(processer=proc_), punkter=(1, 2, 3, 4))
        assert K['extra'].is_dir() and (TMPROT / 'nwp-skill-extra').is_dir() and S['ung'].is_dir(), rap_p['poster']
        assert not [p for p in rap_p['poster'] if p['utfall'] in ('raderad', 'stoppad')] and del_ in str(rap_p['poster']), rap_p['poster']
    rap_x = stadning.stada(ram(), punkter=(2, 4))
    assert not K['extra'].exists() and not (TMPROT / 'nwp-skill-extra').exists(), 'samma kopia och tempkatalog raderas när allt är känt'
    klar('Ö7: utan worktree-listan rörs inga kopior, och när ps eller lsof faller raderas och stoppas ingenting')
    K['sen'] = kopia('kopia-sen')  # en process börjar använda den efter ögonblicksbilden (K13)
    anrop_ = []

    def sen_anvandare():  # ögonblicksbilden är tom; direkt före raderingen har en process börjat använda kopian
        anrop_.append(1)
        return [] if len(anrop_) == 1 else [{'pid': 99997, 'ppid': 1, 'uid': os.getuid(), 'lstart': 'x', 'start': T,
                                             'kommando': 'sleep 600', 'cwd': str(K['sen']), 'filer': [], 'cwd_kand': True}]

    rap_s = stadning.stada(ram(processer=sen_anvandare), punkter=(2,))
    assert K['sen'].is_dir() and 'pid 99997' in en(rap_s, K['sen'], 2)['skal'] and len(anrop_) >= 2, (anrop_, poster(rap_s, K['sen']))
    klar('K13: användningen prövas igen direkt före raderingen')
    fd_las = os.open(str(LAS), os.O_RDONLY | os.O_CREAT)
    LASTA_FD.append(fd_las)
    fcntl.flock(fd_las, fcntl.LOCK_EX)
    rap_l = stadning.stada(ram(), punkter=(2,))
    fcntl.flock(fd_las, fcntl.LOCK_UN)
    assert 'en annan städning pågår' in rap_l.get('besked', '') and not rap_l['poster'] and K['sen'].is_dir(), rap_l
    klar('K11: två städningar körs aldrig samtidigt')

    # ===== prefixen i koden, skapade där tempfile skapar dem ($TMPDIR; Ö5) =====
    MONSTER = (re.compile(r'''(?:mkdtemp|mkstemp|TemporaryDirectory|NamedTemporaryFile)\([^)]*?prefix=['"]([^'"]+)['"]'''),
               re.compile(r'''tmp_katalog\(\s*['"]([^'"]+)['"]'''),
               re.compile(r'''mkdtempSync\(\s*join\(\s*tmpdir\(\)\s*,\s*['"]([^'"]+)['"]'''),
               re.compile(r'''mktemp\s+-d\s+(?:/tmp/)?([A-Za-z0-9_.-]+?)X{3,}'''))
    FUNNA = {}
    filer_ = [ROOT / 'kor.sh', ROOT / 'dashboard.sh']
    for bas_ in (ROOT / 'kontroller', ROOT / 'dashboard', ROOT / '.claude' / 'hooks'):
        for r_d, mappar_, fn_ in os.walk(bas_):
            mappar_[:] = [m for m in mappar_ if m != 'node_modules']
            filer_ += [Path(r_d) / f for f in fn_ if f.endswith(('.py', '.mjs', '.js', '.sh'))]
    for f_ in filer_:
        for m_ in MONSTER:
            for x_ in m_.findall(f_.read_text(encoding='utf-8', errors='replace')):
                FUNNA.setdefault(x_, f_.relative_to(ROOT).as_posix())
    UTANFOR_TMP = {'.vinnare-ny-', 'prov-'}  # skapas i kundens katalog (kandidater.py) och under nwp-bygge-<slug> (prov_revision)
    saknas_ = {x: f for x, f in FUNNA.items() if x not in stadning.TMP_PREFIX and x not in UTANFOR_TMP}
    assert not saknas_, 'prefix i koden som städningen inte känner till: %s' % saknas_
    assert {'nwp-underhall-', 'nwp-lh-', 'nwp-sandlada-prov.', 'upptagna-', 'nwp-stadprov-', 'nwp-tillbaka-'} <= set(FUNNA), sorted(FUNNA)
    assert not [n for n in stadning.ALDRIG_TMP if n.startswith(stadning.TMP_PREFIX)], 'ett prefix når en fast katalog i /tmp'
    skapade = {}
    for prefix_ in sorted(set(FUNNA) - UTANFOR_TMP):
        d_ = Path(tempfile.mkdtemp(prefix=prefix_, dir=TMPDIR_ROT))  # som verktyget skapar den när TMPDIR pekar hit
        (d_ / 'fil').write_text(prefix_)
        skapade[prefix_] = d_
    spara_tempdir = tempfile.tempdir
    tempfile.tempdir = str(TMPDIR_ROT)
    try:
        assert Path(os.path.realpath(TMPDIR_ROT)) in stadning.tmp_rotar() and Path(os.path.realpath('/tmp')) in stadning.tmp_rotar(), \
            'den verkliga städningen söker i /tmp och $TMPDIR'
    finally:
        tempfile.tempdir = spara_tempdir
    rap_t = stadning.stada(ram(), punkter=(4,))
    for prefix_, d_ in skapade.items():
        assert not d_.exists() and en(rap_t, d_, 4)['utfall'] == 'raderad' and prefix_ in en(rap_t, d_, 4)['skal'], (prefix_, poster(rap_t, d_))
    klar('Ö5: varje tempfile- och mktemp-prefix i koden (%d), skapad med tempfile i $TMPDIR, hittas och raderas' % len(skapade))

    # ===== npm-cachen =====
    NPM_POSTER = []

    def npm_fall(fylld, senast_dygn, upptagen=lambda: None, npm_pagar=lambda: None):
        (NPM / '_cacache' / 'content-v2').mkdir(parents=True, exist_ok=True)
        (NPM / '_cacache' / 'content-v2' / 'paket').write_bytes(b'x' * 5000)
        vl.skriv_json(LAGE / 'NPM-CACHE.json', {'tid': iso(T - senast_dygn * DYGN)})
        rap_ = stadning.stada(ram(disk=lambda: (1000 * 2 ** 30, int(1000 * 2 ** 30 * (1 - fylld))), upptagen=upptagen, npm_pagar=npm_pagar),
                              punkter=(5,))
        (p5,) = poster(rap_, punkt=5)
        NPM_POSTER.append(p5)
        return p5, (NPM / '_cacache').exists(), vl.las_json(LAGE / 'NPM-CACHE.json', {})

    p_, finns_, lage_ = npm_fall(0.90, 1)
    assert p_['utfall'] == 'rensad' and not finns_ and lage_['tid'] == iso(T) and 'över 85' in p_['skal'] and p_['storlek_fore'] > 0, (p_, lage_)
    klar('npm-cachen: över 85 % fylld disk rensas, fast förra rensningen var i går')
    p_, finns_, lage_ = npm_fall(0.50, 1)
    assert p_['utfall'] == 'kvar' and finns_ and lage_['tid'] == iso(T - DYGN), (p_, lage_)
    klar('npm-cachen: under 85 % med färsk rensning lämnas')
    p_, finns_, lage_ = npm_fall(0.50, 31)
    assert p_['utfall'] == 'rensad' and not finns_ and lage_['tid'] == iso(T) and '31 dygn' in p_['skal'], (p_, lage_)
    klar('npm-cachen: under 85 % med 31 dygn gammal rensning rensas, och tiden sparas i underhållets läge')
    for hinder_ in ({'upptagen': lambda: 'underhållet pågår (pid 1)'}, {'npm_pagar': lambda: 'en npm-installation pågår (npm ci)'}):
        p_, finns_, lage_ = npm_fall(0.90, 31, **hinder_)
        assert p_['utfall'] == 'kvar' and finns_ and 'pågår' in p_['skal'], p_
    klar('Ö4: npm-cachen rensas inte medan ett underhåll, en körning, ett intag eller en npm-installation pågår')

    # ===== Ö4: vad som pågår, ur körregistret, underhållets läge och intagslåset, utan att något skrivs =====
    LAGE_U, LAS_U = TMP / 'lage-u', TMP / 'intag.las'
    LAGE_U.mkdir()
    LAS_U.write_text('')
    assert stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U) is None, stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U)
    korregister.KATALOG.mkdir(parents=True, exist_ok=True)
    dod_ = korregister.KATALOG / '999999.json'
    dod_.write_text('{"pid": 999999, "vad": "rokprov", "pstart": "x"}')
    assert stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U) is None and dod_.exists(), 'läsningen tar inte bort körregistrets döda poster (K6)'
    U['korning'] = med_foralder(UTANFOR, 'sleep')
    korregister.registrera('rokprov', pid=U['korning'])
    assert 'en körning pågår' in str(stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U))
    korregister.avregistrera(U['korning'])
    U['underhall'] = med_foralder(UTANFOR, 'python3 kontroller/underhall.py')
    vl.skriv_json(LAGE_U / 'UNDERHALL-PAGAR.json', {'pid': U['underhall'], 'start': iso(T)})
    assert 'underhållet pågår (pid %d' % U['underhall'] in str(stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U))
    vl.skriv_json(LAGE_U / 'UNDERHALL-PAGAR.json', {'pid': U['tmp'], 'start': iso(T)})  # pid:en kör inte underhållet
    assert stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U) is None
    fd_ = os.open(str(LAS_U), os.O_RDONLY)
    LASTA_FD.append(fd_)
    fcntl.flock(fd_, fcntl.LOCK_EX)
    assert 'ett intag pågår' in str(stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U))
    fcntl.flock(fd_, fcntl.LOCK_UN)
    assert stadning.upptaget(kataloger=[LAGE_U], laset=LAS_U) is None
    klar('Ö4: en körning i körregistret, ett levande underhåll och ett taget intagslås syns; en återanvänd pid gör det inte')

    # ===== diskvakten =====
    k_ = vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-k')
    LAGE_D = TMP / 'lage-d'
    KANARIE = TMPROT / 'nwp-torr-kanarie'
    KANARIE.mkdir()
    (KANARIE / 'x').write_text('x')

    def disk_kanarie():
        return (1000 * 2 ** 30, (100 if KANARIE.exists() else 200) * 2 ** 30)

    rad_, d_ = sk.diskvakt(k_, ram(disk=lambda: (1000 * 2 ** 30, 400 * 2 ** 30), tillstand=LAGE_D))
    assert rad_['resultat'] == 'ok' and 'över 15 %' in rad_['detalj'] and 'stadning' not in d_ and KANARIE.is_dir(), (rad_, d_)
    klar('diskvakten över 15 % ledigt: ingen städning före starten')
    for hinder_, kw_ in (('underhållet pågår', {'upptagen': lambda: 'underhållet pågår (pid 7)'}), ('intag', {})):
        rad_, d_ = sk.diskvakt(k_, ram(disk=disk_kanarie, tillstand=LAGE_D, **kw_), fick=bool(kw_))
        assert KANARIE.is_dir() and d_.get('hoppad') and hinder_ in rad_['detalj'] and 'hoppades över' in rad_['detalj'], (rad_, d_)
    assert not (LAGE_D / 'stadning').exists()
    klar('Ö4: diskvakten hoppar över städningen medan ett underhåll eller ett intag pågår')
    rad_, d_ = sk.diskvakt(k_, ram(disk=disk_kanarie, tillstand=LAGE_D), slug='prov', start='ny')
    assert not KANARIE.exists() and d_['fore']['andel_ledig'] == 0.1 and d_['efter']['andel_ledig'] == 0.2, d_
    assert rad_['resultat'] == 'ok' and 'städningen kördes' in rad_['detalj'] and not rad_.get('nodvandig'), rad_
    kv_ = {'slug': 'prov', 'tid': iso(T), 'status': 'redo', 'start': 'ny', 'stoppar': [], 'underhall': None, 'rader': [rad_],
           'till_byggaren': [], 'las': {}, 'diskvakt': d_}
    md_ = sk.markdown(kv_)
    assert 'Diskvakten: 10,0 % ledigt (100,0 GB av 1000,0 GB) före starten, under 15 %' in md_, md_
    assert '20,0 % ledigt (200,0 GB av 1000,0 GB) efter' in md_ and '## Städningen före starten' in md_ and str(KANARIE) in md_, md_
    klar('diskvakten under 15 % ledigt: städningen körs före starten, och kvittot visar ledigt före och efter')
    DISK_POSTER = d_['stadning']['poster']
    rapport_ = (LAGE_D / 'UNDERHALL.md').read_text(encoding='utf-8')
    assert len(list((LAGE_D / 'stadning').glob('STADNING-*.json'))) == 1 and not (LAGE_D / 'UNDERHALL.json').exists()
    assert '## Städningen före en start' in rapport_ and 'diskvakten före en start: ny, prov' in rapport_ and str(KANARIE) in rapport_, rapport_
    klar('Ö6: diskvaktens städning skrivs i underhållets läge och rapport, utan att röra UNDERHALL.json')

    # NWP_STADNING=av: diskvakten och underhållet når aldrig det verkliga systemet (Ram.verklig fäller annars)
    os.environ['NWP_STADNING'] = 'av'
    spara_dm = stadning.disk_matt
    stadning.disk_matt = lambda p: (1000, 100)
    try:
        rad_av, d_av = sk.diskvakt(k_)
    finally:
        stadning.disk_matt = spara_dm
    assert rad_av['resultat'] == 'okand' and d_av.get('avslagen') and 'avslagen' in rad_av['detalj'] and not d_av.get('fel'), (rad_av, d_av)
    rap_av = {}
    uh.steg_stadning(k_, rap_av)
    assert rap_av['stadning'] == {'avslagen': True}, rap_av
    klar('NWP_STADNING=av: diskvakten och underhållet städar inte det verkliga systemet')

    # ===== underhållet: städningen i varje körning, och diskvaktens städningar sedan förra underhållet, i rapporten =====
    os.environ.pop('NWP_STADNING', None)
    spara_ = (uh.steg_pythonlas, uh.steg_brew_update, uh.steg_laga_globala, vl.inventera, vl.pagaende)
    stadning.Ram.verklig = classmethod(lambda cls, tillstand=None, torr=False: ram(torr=torr, tillstand=LAGE_D))
    uh.steg_pythonlas = uh.steg_brew_update = lambda k, rap: None
    uh.steg_laga_globala = lambda rap: None
    vl.inventera = lambda k, delar=None: []
    vl.pagaende = lambda egna=None, rensa=True: []
    try:
        rap_uh = uh.underhall(k=vl.Kontext(nat=False, prova=False, katalog=LAGE_D), prov=False)
    finally:
        uh.steg_pythonlas, uh.steg_brew_update, uh.steg_laga_globala, vl.inventera, vl.pagaende = spara_
        stadning.Ram.verklig = classmethod(verkligt)
    md_uh = (LAGE_D / 'UNDERHALL.md').read_text(encoding='utf-8')
    assert rap_uh['status'] == 'klart' and rap_uh['stadning']['poster'] and len(rap_uh['diskvakt']) == 1, rap_uh
    assert '## Städningen' in md_uh and 'VÄNTAR PÅ ÄGAREN' in md_uh and '`underlag/kund-a/ANTECKNINGAR.md`' in md_uh and str(K['material']) in md_uh, md_uh
    assert '## Städningen före en start' in md_uh and 'städningen: ' in rap_uh['sammanfattning'] and 'väntar på ägaren' in rap_uh['sammanfattning']
    klar('underhållet städar i varje körning, och rapporten och sammanfattningen visar städningen och diskvaktens städningar')

    # ===== redovisningens fält =====
    ALLA = rap0['poster'] + rapA['poster'] + rapB['poster'] + rap_t['poster'] + NPM_POSTER + DISK_POSTER + rap_uh['stadning']['poster']
    for p_ in ALLA:
        assert {'punkt', 'vad', 'sokvag', 'storlek_fore', 'tid', 'utfall', 'skal'} <= set(p_), p_
        assert p_['punkt'] in (1, 2, 3, 4, 5) and p_['utfall'] in stadning.UTFALL and isinstance(p_['skal'], str) and p_['skal'].strip(), p_
        assert re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', p_['tid']), p_
        if p_['vad'] == 'process':
            assert p_['storlek_fore'] is None and p_.get('pid') and p_.get('kommando'), p_
        elif p_['utfall'] in ('raderad', 'skulle raderas', 'väntar på ägaren', 'rensad'):
            assert isinstance(p_['storlek_fore'], int) and p_['storlek_fore'] > 0, p_
    assert all(p_['tid'] == iso(T) for p_ in rapB['poster'] + NPM_POSTER), 'tiden kommer ur provets klocka'
    rader_ = [r for r in stadning.markdown(rapB) if r.startswith('| ') and not r.startswith('| Punkt')]
    assert len(rader_) == len(rapB['poster']) and all(r.count(' | ') == 6 for r in rader_), rader_
    klar('redovisningen: vad, sökväg, storlek före, tid ur klockan, utfall och skäl i varje post (%d poster)' % len(ALLA))
finally:
    for fd_ in LASTA_FD:
        try:
            os.close(fd_)
        except OSError:
            pass
    for pid_ in EGNA:
        try:
            os.kill(pid_, signal.SIGKILL)
        except OSError:
            pass
    for b_ in BARN:
        try:
            b_.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    for p_ in (TMP / 'a' / 'repos' / 'kopia-olasbar-katalog' / 'underlag' / 'kund-a' / 'hemlig',
               TMP / 'a' / 'repos' / 'kopia-olasbar-fil' / 'kunder' / 'kund-a' / 'sajt' / 'src' / 'pages' / 'index.astro',
               TMP / 'a' / 'repos' / 'kopia-olasbar-node-modules' / 'kunder' / 'kund-a' / 'sajt' / 'node_modules' / 'last'):
        try:
            os.chmod(p_, 0o755)
        except OSError:
            pass

print('städningens prov: %d fall gröna' % len(KLARA), file=sys.stderr)
