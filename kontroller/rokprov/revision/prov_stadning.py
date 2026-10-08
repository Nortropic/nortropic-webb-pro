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
- slutgranskningen av r94: en amendad och en rebasad worktree som slagits samman och pushats tas bort, och de ersatta
  commitarna står kvar i grenens reflogg (BÖR-1); en worktree vars HEAD-reflogg eller git log inte svarar väntar på
  ägaren (KAN-1); den skarpa npm-rensningen låter npm själv avgöra cachen, och torrläget kör inte npm utan redovisar
  sökvägen som en uppskattning (KAN-2);
- ägarens beslut 2026-10-07 om städningens villkor, ett fall per villkor som redovisas för sig och är rött mot 84c6994:
  en katalog med repots prefix men utan giltig registrering raderas inte och redovisas som äldre rest; en registrerad
  katalog vars körning lever raderas inte; en registrerad katalog vars körning är avslutad raderas, med registreringen i
  skälet; ingen symlänk följs (en scratchpad-rot som pekar ut, en länk i en registrerad katalog); en gemensam förälder
  raderas aldrig; en arbetsyta med en oregistrerad rapport eller bild väntar på ägaren med listan; en arbetsyta där allt
  är registrerat tas bort; och hjälparen korregister.egen_tmp skriver den ägarfil som städningen läser;
- och det tidigare: huvudutcheckningens underlag/ och kunder/ byte för byte oförändrade, worktrees, processer,
  tillfälliga kataloger, scratchpad, npm-cachens tre fall, diskvakten, torrläget, redovisningens fält och underhållets
  rapport.

    .venv/bin/python kontroller/rokprov/revision/prov_stadning.py <repo>

Processlistan är maskinens (ps och lsof), men bara provets egna processer räknas, och stoppet vägrar alla andra. Det
verkliga systemet (~/nortropic-repos, /tmp, ~/.npm) rörs aldrig: Ram.verklig fäller provet om något anropar den, och
varje npm som provet startar har provets egen cache ($npm_config_cache) eller ett eget HOME.
"""
import fcntl
import hashlib
import json
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
# den skarpa npm-rensningen låter npm själv avgöra cachen (KAN-2): varje npm som provet startar (npm-fallen, diskvakten och
# underhållet) rensar då provets egen cache, aldrig ~/.npm; KAN-2-fallet byter den mot en egen npmrc och ett eget HOME
os.environ['npm_config_cache'] = str(TMP / 'npm')
os.environ.pop('NPM_CONFIG_CACHE', None)  # den yttre körningens cache får inte överstyra provets egen
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
# git:s automatiska underhåll av: det kan ta bort en låsfil medan provet kopierar sitt repo (granskningen av r100)
GIT = ['git', '-c', 'user.name=prov', '-c', 'user.email=prov@exempel.se', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
       '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def klar(namn):
    KLARA.append(namn)
    print('ok: ' + namn)


# ägarfilen som kontroller/korregister.py skriver (registrera_tmp). Provet skriver den själv för sina fixturer (giltiga
# och ogiltiga registreringar, levande och avslutade ägare), utan den kod som prövas; att hjälparen skriver samma form
# prövas för sig (fallet om hjälparen nedan).
AGARFIL = '.nwp-agare.json'


def agarfil(d, pid, pstart, vad='provets körning', sokvag=None):
    Path(d, AGARFIL).write_text(json.dumps({'schema': 1, 'pid': int(pid), 'pstart': pstart, 'vad': vad, 'uid': os.getuid(),
                                            'sokvag': sokvag or os.path.realpath(d), 'start': iso(time.time()),
                                            'utcheckning': str(ROOT)}, ensure_ascii=False))


def avslutad_process():
    """(pid, starttid) för en egen process som har slutat: ägaren till en avslutad körnings katalog."""
    p = subprocess.Popen(['sleep', '30'], stdin=subprocess.DEVNULL)
    s = ''
    for _ in range(200):
        s = korregister.startad(p.pid)
        if s:
            break
        time.sleep(0.02)
    p.kill()
    p.wait()
    assert s and not korregister.lever(p.pid), (p.pid, s)
    return p.pid, s


agarfil(TMP, os.getpid(), korregister.startad(os.getpid()), 'prov_stadning')  # provets egen katalog: registrerad, och körningen lever
DOD = avslutad_process()


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


def nytt_repo(bas, material, i_git=None):
    """En huvudutcheckning med en bar origin (pushad main) och kundmaterial i underlag/ och kunder/ (utanför git); i_git
    är fler filer i den första commiten."""
    origin, huvud = bas / 'origin.git', bas / 'repos' / 'nortropic-webb-pro'
    sh('git', 'init', '-q', '--bare', '-b', 'main', origin)
    (huvud / 'kontroller').mkdir(parents=True)
    (huvud / 'kor.sh').write_text('#!/bin/bash\n')
    (huvud / 'kontroller' / 'x.py').write_text('x = 1\n')
    for rel_, data_ in (i_git or {}).items():
        (huvud / rel_).parent.mkdir(parents=True, exist_ok=True)
        (huvud / rel_).write_bytes(data_)
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
    MATERIAL = {'underlag/kund-a/OPPETTIDER.md': 'Öppet 2026-10-05, ring 070-111 11 11\n'.encode(), 'underlag/kund-a/BRIEF.md': b'# Brief\n', 'underlag/kund-a/bilder/jobb.jpg': b'\xff\xd8\xff' + bytes(range(256)) * 8,
                'underlag/kund-a/DESIGNDOMAR.jsonl': b'{"dom": "ny riktning"}\n', 'kunder/kund-a/sajt/src/pages/index.astro': b'<h1>Kund A</h1>\n',
                'kunder/kund-a/sajt/package.json': b'{"name": "kund-a"}\n', 'kunder/kund-a/sajt/node_modules/paket/index.js': b'module.exports = 1\n',
                'kirurgen/spaning/SENAST.json': b'{"slut": "2026-10-06"}\n'}
    # det beständigt registrerade (ägarens beslut 2026-10-07): en rapport i förteckningen med sin kopia, en bild i ett
    # VERSION.json med filen i dess katalog, en fil i huvudutcheckningens git, och en registrerad rapport vars kopia saknas
    REG_MD = '# Granskning\nRegistrerad i förteckningen.\n'.encode()
    REG_PNG = b'\x89PNG\r\n\x1a\n en bedomd bild, registrerad'
    REG_GIT = '# Regel\nIncheckad i huvudutcheckningens git.\n'.encode()
    BORTA_MD = '# Borta\nRegistrerad, men den beständiga kopian saknas.\n'.encode()
    REG_OMTAG = b'\x89PNG\r\n\x1a\n en bild som ett omtag sparat'
    OMTAG_KV = 'underlag/kund-a/omtag/20261007T000000Z-1/k01/abcdef012345/'
    # registreringar som inte räknas (granskningen av r100): en kopia som ändrats efteråt (C7), en sha256 i VERSION.json utan
    # kopia (C8), en rad med .. in i arbetsytan, en absolut sökväg och en rad utanför underlag/ (KAN-2), och ett kvitto i en
    # dold omtagskatalog, ett sparande som aldrig blev klart (KAN-3)
    ANDRAD_ORIG, ANDRAD_NU = '# Rapport\nOriginalet.\n'.encode(), '# Rapport\nÄndrad efteråt.\n'.encode()
    UTAN_KOPIA = b'\x89PNG en bild utan kopia i VERSION.json:s katalog'
    SJALV, SJALV2 = '# Rapport\nSom pekar på sig själv med ...\n'.encode(), '# Rapport\nMed absolut sökväg.\n'.encode()
    KUND_MD = '# Kundens\nRegistrerad med bas kunder/.\n'.encode()
    DOLD_PNG = b'\x89PNG kopierad av ett sparande som dog'
    DOLD_KV = 'underlag/kund-a/omtag/.20261007T000000Z-2.tmp/k01/abcdef012345/'
    V7_S3 = TMP / 'v7' / 'arbetsyta-oregistrerad' / 'scratch' / 'claude-501' / '-Users-prov' / '00000003-7777-2222-3333-000000000003'
    HUVUD_UNDERLAG = TMP / 'a' / 'repos' / 'nortropic-webb-pro' / 'underlag'

    def sha_(b):
        return hashlib.sha256(b).hexdigest()

    REGISTER = {'underlag/granskningar/sessioner/prov/GRANSKNING.md': REG_MD,
                'underlag/figma-pilot/moment-x/bilder/dator-1440.png': REG_PNG,
                'underlag/figma-pilot/moment-x/VERSION.json': json.dumps({'schema': 1, 'varv': {'v1': {'dator-1440.png': sha_(REG_PNG)}},
                                                                         'saknad': {'utan-kopia.png': sha_(UTAN_KOPIA)}}).encode(),
                'underlag/granskningar/sessioner/prov/ANDRAD.md': ANDRAD_NU,
                'kunder/kund-a/KUND.md': KUND_MD,
                DOLD_KV + 'bilder/start/vy-390-forsta.png': DOLD_PNG,
                DOLD_KV + 'KVITTO.json': json.dumps({'schema': 1, 'filer': {'bilder/start/vy-390-forsta.png': sha_(DOLD_PNG)}}).encode(),
                OMTAG_KV + 'bilder/start/vy-390-forsta.png': REG_OMTAG,  # ett omtags kvitto (kontroller/atelje.py, spara_bedomda)
                OMTAG_KV + 'KVITTO.json': json.dumps({'schema': 1, 'filer': {'bilder/start/vy-390-forsta.png': sha_(REG_OMTAG)}}).encode(),
                'underlag/granskningar/FORTECKNING.jsonl': ''.join(json.dumps(r_) + '\n' for r_ in (
                    {'fil': 'granskningar/sessioner/prov/GRANSKNING.md', 'sha256': sha_(REG_MD), 'bas': 'underlag/'},
                    {'fil': 'granskningar/sessioner/prov/BORTA.md', 'sha256': sha_(BORTA_MD), 'bas': 'underlag/'},
                    {'fil': 'granskningar/sessioner/prov/ANDRAD.md', 'sha256': sha_(ANDRAD_ORIG), 'bas': 'underlag/'},
                    {'fil': os.path.relpath(V7_S3 / 'scratchpad' / 'SJALV.md', HUVUD_UNDERLAG), 'sha256': sha_(SJALV), 'bas': 'underlag/'},
                    {'fil': str(V7_S3 / 'scratchpad' / 'SJALV2.md'), 'sha256': sha_(SJALV2), 'bas': 'underlag/'},
                    {'fil': 'kund-a/KUND.md', 'sha256': sha_(KUND_MD), 'bas': 'kunder/'})).encode()}
    HUVUD = nytt_repo(TMP / 'a', dict(MATERIAL, **REGISTER), i_git={'kunskap/regel.md': REG_GIT})
    assert HUVUD / 'underlag' == HUVUD_UNDERLAG
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

    SAMMAN = ('klar', 'smutsig', 'material', 'aktiv', 'anvand', 'kirurg', 'env', 'last', 'race', 'frikopplad', 'catfile', 'amend',
              'reflogfel', 'logfel')
    WT = {g: worktree(g) for g in SAMMAN}
    WT['rebasad'] = worktree('rebasad', commit=False)  # Ö2: uppdateras senare med git rebase main, ingen egen commit
    WT['ff'] = worktree('ff', commit=False)            # Ö2, kontroll: uppdateras med git merge --ff-only main
    WT['omskriven'] = worktree('omskriven')            # BÖR-1: egen commit, rebasad på ett nyare main, sedan sammanslagen
    # BÖR-1: commitarna som en amend och en rebase ersätter; de står kvar i grenens reflogg efter git worktree remove
    ERSATTA = {g: git('rev-parse', 'HEAD', cwd=WT[g]).strip() for g in ('amend', 'omskriven')}
    git('commit', '-q', '--amend', '-m', 'amend, rättat meddelande', cwd=WT['amend'])
    git('checkout', '-q', '--detach', cwd=WT['frikopplad'])  # Ö1: ett experiment på en frikopplad HEAD, sedan tillbaka
    (WT['frikopplad'] / 'experiment.md').write_text('ett experiment som bara finns här\n')
    git('add', '-A', cwd=WT['frikopplad'])
    git('commit', '-q', '-m', 'experiment på frikopplad HEAD', cwd=WT['frikopplad'])
    EXPERIMENT = git('rev-parse', 'HEAD', cwd=WT['frikopplad']).strip()
    git('checkout', '-q', 'frikopplad', cwd=WT['frikopplad'])
    git('merge', '-q', '--no-ff', '-m', 'sammanslagning', *SAMMAN, cwd=HUVUD)
    (HUVUD / 'kontroller' / 'x.py').write_text('x = 2\n')  # main går vidare: den gamla versionen finns bara i historiken
    git('commit', '-q', '-am', 'x = 2', cwd=HUVUD)
    git('push', '-q', 'origin', 'main', cwd=HUVUD)
    git('rebase', '-q', 'main', cwd=WT['rebasad'])
    git('merge', '-q', '--ff-only', 'main', cwd=WT['ff'])
    assert any(r.startswith('rebase') for r in git('reflog', 'show', '--format=%gs', 'rebasad', cwd=HUVUD).splitlines())
    git('rebase', '-q', 'main', cwd=WT['omskriven'])  # BÖR-1: som r94, rebase och sedan en snabbspolande sammanslagning
    git('merge', '-q', '--ff-only', 'omskriven', cwd=HUVUD)
    git('push', '-q', 'origin', 'main', cwd=HUVUD)
    for g_, s_ in ERSATTA.items():  # den ersatta commiten: i worktreens HEAD-reflogg och grenens reflogg, men ingen gren når den
        assert s_ != git('rev-parse', 'HEAD', cwd=WT[g_]).strip() and s_ in git('reflog', 'show', '--format=%H', 'HEAD', cwd=WT[g_]).split()
        assert s_ in git('reflog', 'show', '--format=%H', g_, cwd=HUVUD).split() and not git('branch', '-a', '--contains', s_, cwd=HUVUD).strip()
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
    (WT['catfile'] / 'kirurgen').mkdir()  # E1: unik och ignorerad; när git cat-file faller går den inte att jämföra
    (WT['catfile'] / 'kirurgen' / 'intag-unik.json').write_text('{"bara": "här"}\n')
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
    K['samma_storlek'] = kopia('kopia-samma-storlek')  # E2: ägarens rättelse med samma längd
    (K['samma_storlek'] / 'underlag' / 'kund-a' / 'OPPETTIDER.md').write_bytes('Öppet 2026-10-06, ring 070-222 22 22\n'.encode())
    assert (K['samma_storlek'] / 'underlag' / 'kund-a' / 'OPPETTIDER.md').stat().st_size == len(MATERIAL['underlag/kund-a/OPPETTIDER.md'])
    K['catfile'] = kopia('kopia-catfile', med_git=False)  # E1
    (K['catfile'] / 'underlag' / 'kund-a' / 'UNIK.md').write_text('bara här\n')
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
    for n_ in ('nwp-skill-gammal', 'nwp-pip-anvand'):  # registrerade som en avslutad körnings egna (ägarens beslut 2026-10-07)
        agarfil(TMPROT / n_, *DOD)
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
        (s_ / 'scratchpad' / 'anteckning.md').write_bytes(REG_MD if s_ == S['gammal'] else b'x\n')  # den övergivna: registrerad (2026-10-07)
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
    assert len(FORE) == len([r for r in MATERIAL if r.startswith(("underlag/", "kunder/"))]) + len(REGISTER) + 3, FORE

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
    # KAN-1: worktreens HEAD-reflogg går inte att läsa (reflogfel), och git log faller för en annan worktree (logfel)
    git_orig = stadning.git
    LOGFEL_HEAD = git('rev-parse', 'HEAD', cwd=WT['logfel']).strip()

    def git_med_sen_fil(*a, **k):
        if a[:2] == ('worktree', 'remove') and Path(a[-1]) == WT['race']:
            (WT['race'] / 'sen-fil.txt').write_text('skapad efter prövningen\n')
        if a[:3] == ('reflog', 'show', '--format=%H') and os.path.realpath(k.get('cwd') or '') == os.path.realpath(WT['reflogfel']):
            return 128, 'fatal: worktreens reflogg gick inte att läsa (provets fel)'
        if a[:1] == ('log',) and LOGFEL_HEAD in a:
            return 128, 'fatal: git log föll (provets fel)'
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
    p_ = en(rapB, K['samma_storlek'], 2)
    assert K['samma_storlek'].is_dir() and p_['utfall'] == 'väntar på ägaren' and [m['sokvag'] for m in p_['material']] == ['underlag/kund-a/OPPETTIDER.md'], p_
    klar('E2: en fil med samma sökväg och storlek men annat innehåll är eget material (sha256, inte storleken)')
    for d_, pk_ in ((K['catfile'], 2), (WT['catfile'], 1)):
        assert d_.is_dir() and en(rapB, d_, pk_)['utfall'] == 'väntar på ägaren', poster(rapB, d_)

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
    p_ = en(rapB, WT['frikopplad'], 1)
    assert WT['frikopplad'].is_dir() and p_['utfall'] == 'väntar på ägaren' and [c['sha'] for c in p_.get('commits') or []] == [EXPERIMENT], p_
    assert 'frikopplad HEAD' in p_['skal'] and EXPERIMENT in git('rev-list', '--all', '--reflog', cwd=HUVUD).split()
    assert '`%s` experiment' % EXPERIMENT[:12] in '\n'.join(stadning.markdown(rapB))
    klar('Ö1: en worktree med en commit som bara finns i dess HEAD-reflogg (frikopplad HEAD) väntar på ägaren, med commiten')
    for g_ in ('rebasad', 'ff'):
        p_ = en(rapB, WT[g_], 1)
        assert WT[g_].is_dir() and p_['utfall'] == 'väntar på ägaren' and 'okänd' in p_['skal'], (g_, p_)
    klar('Ö2: en worktree som bara uppdaterats med git rebase main eller --ff-only har ingen egen commit och väntar på ägaren')
    for g_, s_ in ERSATTA.items():  # BÖR-1 (granskarens fall A och B): den ersatta commiten försvinner inte med worktreen
        p_ = en(rapB, WT[g_], 1)
        assert not WT[g_].exists() and p_['utfall'] == 'raderad' and not p_.get('commits'), (g_, p_)
        assert s_ in git('reflog', 'show', '--format=%H', g_, cwd=HUVUD).split() and s_ in git('rev-list', '--all', '--reflog', cwd=HUVUD).split(), g_
    assert 'reflogg i huvudutcheckningen' in en(rapB, WT['frikopplad'], 1)['skal'], 'skälet säger vad som faktiskt försvinner'
    klar('BÖR-1: en amendad och en rebasad worktree, sammanslagna och pushade, tas bort; de ersatta commitarna står kvar i grenens reflogg')
    for g_ in ('reflogfel', 'logfel'):  # KAN-1: Ö1:s skyddsgren
        p_ = en(rapB, WT[g_], 1)
        assert WT[g_].is_dir() and p_['utfall'] == 'väntar på ägaren' and 'HEAD-reflogg gick inte att pröva' in p_['skal'], (g_, p_)
    rap_k1 = stadning.stada(ram(), punkter=(1,))  # samma worktrees när git svarar: de tas bort
    for g_ in ('reflogfel', 'logfel'):
        assert not WT[g_].exists() and en(rap_k1, WT[g_], 1)['utfall'] == 'raderad', (g_, poster(rap_k1, WT[g_]))
    assert not [p for p in rap_k1['poster'] if p['utfall'] in ('raderad', 'fel') and p['sokvag'] not in (str(WT['reflogfel']), str(WT['logfel']))], \
        rap_k1['poster']
    klar('KAN-1: en worktree vars HEAD-reflogg eller git log inte svarar väntar på ägaren, och tas bort när git svarar')

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

    # ===== ägarens beslut 2026-10-07: städningens villkor. Ett fall per villkor, med egna rötter, och varje fall redovisas
    # för sig (mot 84c6994, som raderade på prefixet, blir vart och ett rött på sitt eget villkor) =====
    V7_FEL = []
    REST_TEXT = 'äldre rest, väntar på identifiering'

    def v7(namn):
        def kor_fallet(f):
            try:
                f()
                klar('2026-10-07: ' + namn)
            except Exception as e:  # noqa: BLE001 — varje villkor redovisas för sig
                V7_FEL.append(namn)
                print('FEL: 2026-10-07: %s: %s: %s' % (namn, type(e).__name__, str(e)[:700]), file=sys.stderr)
            return f
        return kor_fallet

    def v7_ram(bas, tmp_extra=(), scratch=None, repo=None, klocka=None):
        (bas / 'tmp').mkdir(parents=True, exist_ok=True)
        return stadning.Ram(repo=repo or HUVUD, repos_rot=REPOS, tmp_rot=bas / 'tmp', tmp_extra=list(tmp_extra), scratch_rot=scratch,
                            npm_cache=NPM, tillstand=LAGE, claude_projekt=KONFIG, las=None, klocka=klocka or (lambda: T),
                            disk=lambda: (1000 * 2 ** 30, 500 * 2 ** 30), processer=lambda: [],
                            stoppa=lambda pid: (_ for _ in ()).throw(AssertionError('inget stopp i fallen 2026-10-07')),
                            upptagen=lambda: None, npm_pagar=lambda: None)

    def stat_agare(d):
        return os.lstat(Path(d) / AGARFIL).st_mode & 0o777

    def session_v7(scr, n):
        s = scr / '-Users-prov' / ('%08d-7777-2222-3333-%012d' % (n, n))
        (s / 'scratchpad').mkdir(parents=True)
        return s

    def skriv_filer(d, filer):
        for rel_, data_ in filer.items():
            (d / rel_).parent.mkdir(parents=True, exist_ok=True)
            (d / rel_).write_bytes(data_ if isinstance(data_, bytes) else ('# %s\nInnehåll som bara finns här.\n' % rel_).encode())

    @v7('en katalog med repots prefix men utan giltig registrering raderas inte och redovisas för sig som äldre rest')
    def _v7_oregistrerad():
        bas = TMP / 'v7' / 'oregistrerad'
        (bas / 'tmp2').mkdir(parents=True)
        r = v7_ram(bas, tmp_extra=[bas / 'tmp2'])
        utan = bas / 'tmp' / 'nwp-skill-utan-agare'
        utan.mkdir()
        (utan / 'fil.txt').write_text('okänt ursprung\n')
        annan = bas / 'annan'
        annan.mkdir()
        agarfil(annan, *DOD)  # en giltig ägarfil, men för en annan katalog
        kopierad = bas / 'tmp' / 'nwp-pip-kopierad-agare'
        kopierad.mkdir()
        shutil.copy2(annan / AGARFIL, kopierad / AGARFIL)
        lankad = bas / 'tmp' / 'nwp-motor-lankad-agare'
        lankad.mkdir()
        (lankad / AGARFIL).symlink_to(annan / AGARFIL)  # en länk följs aldrig, inte heller till en giltig ägarfil
        trasig = bas / 'tmp' / 'nwp-torr-trasig-agare'
        trasig.mkdir()
        (trasig / AGARFIL).write_text('{inte json')
        stor = bas / 'tmp' / 'nwp-lh-stor-agare'
        stor.mkdir()
        agarfil(stor, *DOD, vad='x' * 5000)  # större än en registrering: läses inte
        pid1 = bas / 'tmp' / 'nwp-sub-pid-ett'
        pid1.mkdir()
        agarfil(pid1, 1, korregister.startad(1), 'launchd')  # pid 1 lever alltid och är aldrig en körnings ägare (S7)
        # samma namn i /tmp och $TMPDIR: en ägarfil kopierad från den ena till den andra gäller inte där (S6)
        tvilling_a, tvilling_b = bas / 'tmp' / 'nwp-yt-tvilling', bas / 'tmp2' / 'nwp-yt-tvilling'
        tvilling_a.mkdir()
        tvilling_b.mkdir()
        agarfil(tvilling_a, *DOD, vad='tvillingen i /tmp')
        shutil.copy2(tvilling_a / AGARFIL, tvilling_b / AGARFIL)
        for x_ in (kopierad, lankad, trasig, stor, pid1, tvilling_a, tvilling_b):
            (x_ / 'fil.txt').write_text('innehåll av okänt ursprung\n')
        rap = stadning.stada(r, punkter=(4,))
        for x_, ord_ in ((utan, 'saknas'), (kopierad, 'inte katalogens egen'), (lankad, 'ingen vanlig fil'), (trasig, 'tolka'), (stor, 'för stor'),
                         (pid1, 'pid eller användare'), (tvilling_b, 'inte katalogens egen')):
            assert x_.is_dir(), 'raderad på prefixet: %s' % x_
            p_ = en(rap, x_, 4)
            assert p_['utfall'] == REST_TEXT and ord_ in p_['skal'] and 'prefixet ensamt räcker inte' in p_['skal'], p_
            assert p_['storlek_fore'] > 0 and p_['alder'] >= 9 * DYGN and p_['andrad'], p_
        assert not tvilling_a.exists() and en(rap, tvilling_a, 4)['utfall'] == 'raderad', poster(rap, tvilling_a)
        md_ = '\n'.join(stadning.markdown(rap))
        assert '**Äldre rester, väntar på identifiering**' in md_ and '- `%s` (' % utan in md_ and 'dygn gammal' in md_, md_
        # en mycket gammal rest (45 dygn) raderas inte heller (S10)
        bas45 = TMP / 'v7' / 'oregistrerad-45'
        r45 = v7_ram(bas45, klocka=lambda: time.time() + 45 * DYGN)
        gammal = bas45 / 'tmp' / 'nwp-skill-mycket-gammal'
        gammal.mkdir()
        (gammal / 'fil.txt').write_text('mycket gammal\n')
        p_ = en(stadning.stada(r45, punkter=(4,)), gammal, 4)
        assert gammal.is_dir() and p_['utfall'] == REST_TEXT and p_['alder'] >= 44 * DYGN, p_
        # en katalog och ägarfil som ägs av en annan användare: provet kan inte byta ägare utan root, så användarens id byts
        # bara under anropet
        spara_uid = os.getuid
        os.getuid = lambda: spara_uid() + 1
        try:
            fel_ = korregister.tmp_agare(annan)[1]
        finally:
            os.getuid = spara_uid
        assert fel_ and 'annan användare' in fel_, fel_

    @v7('en registrerad katalog vars körning lever raderas inte, också när starttiden står i lokal tid eller signalen nekas')
    def _v7_levande():
        bas = TMP / 'v7' / 'levande'
        r = v7_ram(bas)
        egen = bas / 'tmp' / 'nwp-skill-levande'
        egen.mkdir()
        (egen / 'fil.txt').write_text('x')
        agarfil(egen, os.getpid(), korregister.startad(os.getpid()), 'provets levande körning')
        barn_ = med_foralder(UTANFOR, 'sleep')
        hos_barn = bas / 'tmp' / 'nwp-pip-levande-barn'
        hos_barn.mkdir()
        agarfil(hos_barn, barn_, korregister.startad(barn_), 'en annan levande körning')
        utan_start = bas / 'tmp' / 'nwp-motor-utan-starttid'
        utan_start.mkdir()
        agarfil(utan_start, barn_, '', 'levande, utan starttid')  # pid:en lever och identiteten går inte att pröva: kan pågå
        lokal = bas / 'tmp' / 'nwp-yt-lokal-tid'
        lokal.mkdir()
        agarfil(lokal, os.getpid(), korregister.startad_lokalt(os.getpid()), 'starttiden i lokal tid')  # samma tidpunkt, annan zon (KAN-7)
        rap = stadning.stada(r, punkter=(4,))
        for x_, ord_ in ((egen, 'pågår'), (hos_barn, 'pågår'), (utan_start, 'kan pågå'), (lokal, 'pågår')):
            assert x_.is_dir(), 'raderad fast körningen lever: %s' % x_
            p_ = en(rap, x_, 4)
            assert p_['utfall'] == 'kvar' and ord_ in p_['skal'] and 'registrerad av' in p_['skal'], p_
        assert korregister.lever(1), 'EPERM (pid 1 tillhör root) betyder att processen lever (KAN-7)'

    @v7('en registrerad katalog vars körning är avslutad raderas, och redovisningen säger vem som registrerade den')
    def _v7_avslutad():
        bas = TMP / 'v7' / 'avslutad'
        r = v7_ram(bas)
        avsl = bas / 'tmp' / 'nwp-skill-avslutad'
        (avsl / 'under').mkdir(parents=True)
        (avsl / 'under' / 'fil.txt').write_text('x')
        agarfil(avsl, *DOD, vad='provets avslutade körning')
        aterbrukad = bas / 'tmp' / 'nwp-pip-aterbrukad-pid'
        aterbrukad.mkdir()
        agarfil(aterbrukad, os.getpid(), 'Mon Jan  1 00:00:00 2024', 'en körning vars pid återanvänts')  # pid:en lever, men är en annan process
        rap = stadning.stada(r, punkter=(4,))
        for x_, vad_, ord_ in ((avsl, 'provets avslutade körning', 'lever inte'), (aterbrukad, 'en körning vars pid återanvänts', 'annan starttid')):
            p_ = en(rap, x_, 4)
            assert not x_.exists() and p_['utfall'] == 'raderad', p_
            assert 'registrerad av %s' % vad_ in p_['skal'] and 'avslutad' in p_['skal'] and ord_ in p_['skal'] and p_.get('registrerad') == vad_, p_

    @v7('ingen symlänk följs: scratchpads rot som pekar ut, en länk i /tmp, en länk i en registrerad katalog och en länk som byts in')
    def _v7_symlank():
        bas = TMP / 'v7' / 'symlank'
        (bas / 'tmp').mkdir(parents=True)
        ute = bas / 'utanfor-scratch'
        sess = session_v7(ute, 1)
        (sess / 'scratchpad' / 'anteckning.md').write_bytes(REG_MD)  # registrerad: bara länken avgör
        (bas / 'tmp' / 'claude-501').symlink_to(ute, target_is_directory=True)
        mal_ = bas / 'mal-utanfor'
        mal_.mkdir()
        (mal_ / 'behall.txt').write_text('målet rörs inte\n')
        med_lank = bas / 'tmp' / 'nwp-skill-med-lank'
        med_lank.mkdir()
        (med_lank / 'fil.txt').write_text('x')
        (med_lank / 'ut').symlink_to(mal_, target_is_directory=True)
        agarfil(med_lank, *DOD)
        mal2 = bas / 'mal-registrerad'  # en länk med repots prefix direkt i /tmp, till en registrerad och avslutad katalog (S11)
        mal2.mkdir()
        (mal2 / 'behall.txt').write_text('målet rörs inte\n')
        agarfil(mal2, *DOD)
        lank_ut = bas / 'tmp' / 'nwp-pip-lank-ut'
        lank_ut.symlink_to(mal2, target_is_directory=True)
        r = v7_ram(bas, scratch=bas / 'tmp' / 'claude-501')
        rap = stadning.stada(r, punkter=(4,))
        assert sess.is_dir() and (sess / 'scratchpad' / 'anteckning.md').read_bytes() == REG_MD, 'scratchpads rot är en länk ut, och den följdes'
        p_ = en(rap, bas / 'tmp' / 'claude-501', 4)
        assert p_['utfall'] == 'kvar' and 'symlänk' in p_['skal'] and 'följs inte' in p_['skal'], p_
        assert not med_lank.exists() and (mal_ / 'behall.txt').read_text() == 'målet rörs inte\n', 'länken i den registrerade katalogen följdes'
        assert stadning.radera(r, bas / 'tmp' / 'claude-501').startswith('raderas aldrig') and sess.is_dir()
        assert lank_ut.is_symlink() and (mal2 / 'behall.txt').is_file() and not poster(rap, lank_ut), ('en länk i /tmp prövas inte ens', poster(rap, lank_ut))
        # en katalog som byts mot en länk mellan provet och raderingen: länken följs aldrig (KAN-1)
        byts = bas / 'tmp' / 'nwp-skill-byts'
        byts.mkdir()
        (byts / 'f').write_text('x')
        mal3 = bas / 'mal-byte'
        mal3.mkdir()
        (mal3 / 'behall.txt').write_text('målet\n')
        orig_lstat, bytt_ = os.lstat, []

        def lstat_som_byter(q, *a_, **k_):
            r_ = orig_lstat(q, *a_, **k_)
            if str(q) == str(byts) and not bytt_:
                bytt_.append(1)
                os.rename(str(byts), str(byts) + '.undan')
                os.symlink(str(mal3), str(byts))
            return r_
        os.lstat = lstat_som_byter
        try:
            fel_ = stadning.ta_bort_trad(byts)
        except OSError as e_:
            fel_ = [str(e_)]
        finally:
            os.lstat = orig_lstat
        assert bytt_ and (mal3 / 'behall.txt').read_text() == 'målet\n', ('en länk som byttes in följdes', fel_)

    @v7('en gemensam förälder raderas aldrig: en $TMPDIR med repots prefix i /tmp, och rötterna själva')
    def _v7_foralder():
        bas = TMP / 'v7' / 'foralder'
        (bas / 'tmp').mkdir(parents=True)
        nastlad = bas / 'tmp' / 'nwp-skill-tmpdir'  # en $TMPDIR som ligger i /tmp och har repots prefix
        (nastlad / 'nwp-pip-egen').mkdir(parents=True)
        (nastlad / 'nwp-pip-egen' / 'fil.txt').write_text('x')
        (nastlad / 'annat-verktyg').mkdir()
        (nastlad / 'annat-verktyg' / 'fil.txt').write_text('ett annat verktygs katalog\n')
        agarfil(nastlad, *DOD, vad='registrerad, men en förälder')
        agarfil(nastlad / 'nwp-pip-egen', *DOD, vad='den registrerade katalogen själv')
        r = v7_ram(bas, tmp_extra=[nastlad])
        rap = stadning.stada(r, punkter=(4,))
        assert nastlad.is_dir() and (nastlad / 'annat-verktyg' / 'fil.txt').is_file(), 'den gemensamma föräldern raderades'
        p_ = en(rap, nastlad, 4)
        assert p_['utfall'] == 'kvar' and 'gemensam förälder' in p_['skal'], p_
        assert not (nastlad / 'nwp-pip-egen').exists() and en(rap, nastlad / 'nwp-pip-egen', 4)['utfall'] == 'raderad', 'katalogen själv raderas'
        for x_ in (bas / 'tmp', nastlad, bas):
            assert stadning.radera(r, x_).startswith('raderas aldrig') and x_.is_dir(), x_
        assert stadning.direkt_under(r, nastlad / 'annat-verktyg', [bas / 'tmp']), 'ligger inte direkt under roten'
        assert 'gemensam förälder' in (stadning.direkt_under(r, nastlad, [bas / 'tmp']) or ''), 'en rot är aldrig katalogen själv'

    @v7('en arbetsyta med en oregistrerad fil, oavsett ändelse, väntar på ägaren med listan; registreringar som inte gäller räknas inte')
    def _v7_arbetsyta_oregistrerad():
        bas = TMP / 'v7' / 'arbetsyta-oregistrerad'
        scr = bas / 'scratch' / 'claude-501'
        s1 = session_v7(scr, 1)
        # varje vanlig fil prövas: rapporter, bilder och versionsunderlag, med och utan ändelse, också i en katalog som bara
        # heter venv (BÖR-1); bara node_modules/, __pycache__/ och en riktig venvs egna kataloger hoppas över
        prov1 = ['scratchpad/RAPPORT.md', 'scratchpad/bild.webp', 'scratchpad/SKISS.PNG', 'scratchpad/logg.txt', 'scratchpad/RAPPORT',
                 'scratchpad/rapport.html', 'scratchpad/kod/index.astro', 'scratchpad/stil.css', 'scratchpad/resultat.jsonl', 'scratchpad/foto.jpg',
                 'scratchpad/foto.jpeg', 'scratchpad/diagram.svg', 'scratchpad/venv/RAPPORT.md', 'scratchpad/.venv/RAPPORT.md',
                 'scratchpad/env/RAPPORT.md']
        skriv_filer(s1, dict.fromkeys(prov1))
        skriv_filer(s1, {'scratchpad/GRANSKNING.md': REG_MD, 'scratchpad/env/pyvenv.cfg': b'home = /usr/bin\n',
                         'scratchpad/env/lib/python3.12/site-packages/p/README.md': None, 'scratchpad/env/bin/activate': None,
                         'scratchpad/env/include/p.h': None, 'node_modules/p/README.md': None, 'scratchpad/__pycache__/x.cpython-312.pyc': None})
        s2 = session_v7(scr, 2)
        (s2 / 'scratchpad' / 'BORTA.md').write_bytes(BORTA_MD)  # i förteckningen, men den beständiga kopian saknas
        s3 = session_v7(scr, 3)  # registreringar som inte gäller (C7, C8, KAN-2 och KAN-3)
        assert s3 == V7_S3, s3
        prov3 = {'scratchpad/ANDRAD.md': ANDRAD_ORIG, 'scratchpad/utan-kopia.png': UTAN_KOPIA, 'scratchpad/SJALV.md': SJALV,
                 'scratchpad/SJALV2.md': SJALV2, 'scratchpad/KUND.md': KUND_MD, 'scratchpad/dold.png': DOLD_PNG}
        skriv_filer(s3, prov3)
        s4 = session_v7(scr, 4)  # en fil i arbetsytan som inte går att läsa: den går inte att pröva (S4)
        (s4 / 'scratchpad' / 'last.md').write_text('# en rapport som inte går att läsa\n')
        os.chmod(s4 / 'scratchpad' / 'last.md', 0)
        s5 = session_v7(scr, 5)  # en katalog som inte går att läsa: redan mätningen stannar, och arbetsytan står kvar
        (s5 / 'scratchpad' / 'last').mkdir()
        (s5 / 'scratchpad' / 'last' / 'RAPPORT.md').write_text('# inne i en oläsbar katalog\n')
        os.chmod(s5 / 'scratchpad' / 'last', 0)
        try:
            rap = stadning.stada(v7_ram(bas, scratch=scr), punkter=(4,))
        finally:
            os.chmod(s4 / 'scratchpad' / 'last.md', 0o644)
            os.chmod(s5 / 'scratchpad' / 'last', 0o755)
        p1 = en(rap, s1, 4)
        assert s1.is_dir() and (s1 / 'scratchpad' / 'RAPPORT.md').is_file(), 'arbetsytan togs bort med oregistrerade filer'
        assert p1['utfall'] == 'väntar på ägaren' and [m['sokvag'] for m in p1['material']] == sorted(prov1), [m['sokvag'] for m in p1['material']]
        p2 = en(rap, s2, 4)
        assert s2.is_dir() and p2['utfall'] == 'väntar på ägaren' and [m['sokvag'] for m in p2['material']] == ['scratchpad/BORTA.md'], p2
        p3 = en(rap, s3, 4)
        assert s3.is_dir() and p3['utfall'] == 'väntar på ägaren' and [m['sokvag'] for m in p3['material']] == sorted(prov3), \
            [m['sokvag'] for m in p3['material']]
        p4 = en(rap, s4, 4)
        assert s4.is_dir() and p4['utfall'] == 'väntar på ägaren' and 'gick inte att pröva' in p4['skal'], p4
        p5 = en(rap, s5, 4)
        assert s5.is_dir() and p5['utfall'] == 'kvar' and 'gick inte att läsa' in p5['skal'], p5
        md_ = '\n'.join(stadning.markdown(rap))
        assert '**Väntar på ägaren**' in md_ and '`scratchpad/RAPPORT.md`' in md_ and 'varken beständigt registrerade' in md_, md_

    @v7('en arbetsyta där varje fil är beständigt registrerad eller nåbar i git tas bort, och redovisningen säger det')
    def _v7_arbetsyta_registrerad():
        bas = TMP / 'v7' / 'arbetsyta-registrerad'
        scr = bas / 'scratch' / 'claude-501'
        s = session_v7(scr, 3)
        skriv_filer(s, {'scratchpad/GRANSKNING.md': REG_MD,          # förteckningen, med den beständiga kopian
                        'scratchpad/Dator-1440.PNG': REG_PNG,        # ett VERSION.json, med filen i dess katalog (ändelsen i versaler)
                        'scratchpad/regel.md': REG_GIT,              # byte för byte i huvudutcheckningens git, på main
                        'scratchpad/x-kopia.py': b'x = 2\n',         # utan rapportändelse, men på main i huvudutcheckningens git
                        'scratchpad/jamforelse-390.png': REG_OMTAG,  # i ett omtags KVITTO.json, med filen bredvid
                        'node_modules/p/README.md': None, 'scratchpad/__pycache__/x.cpython-312.pyc': None,
                        'scratchpad/env/pyvenv.cfg': b'home = /usr/bin\n', 'scratchpad/env/lib/python3.12/site-packages/p/x.py': None,
                        'scratchpad/env/bin/python': None})
        ute = bas / 'utanfor-arbetsytan'
        ute.mkdir()
        (ute / 'HEMLIG.md').write_text('# inte registrerad, utanför arbetsytan\n')
        (s / 'scratchpad' / 'ut').symlink_to(ute, target_is_directory=True)  # följs inte, och målet rörs inte
        rap = stadning.stada(v7_ram(bas, scratch=scr), punkter=(4,))
        p_ = en(rap, s, 4)
        assert not s.exists() and p_['utfall'] == 'raderad', p_
        assert 'varje fil i den är beständigt registrerad eller nåbar i huvudutcheckningens git' in p_['skal'], p_
        assert (ute / 'HEMLIG.md').is_file(), 'länkens mål rörs inte'

    @v7('git: bara det som nås från en ref räknas; ett löst objekt, en borttagen gren och ett git som inte svarar gör det inte')
    def _v7_git():
        bas = TMP / 'v7' / 'git'
        reg2 = '# Regel\nPå main i det här repot.\n'.encode()
        g_ = nytt_repo(bas, {}, i_git={'kunskap/regel2.md': reg2})
        los, gren = '# Lös\nBara som ett löst objekt.\n'.encode(), '# Utkast\nPå en gren som togs bort.\n'.encode()
        (bas / 'los.md').write_bytes(los)
        git('hash-object', '-w', bas / 'los.md', cwd=g_)  # ett löst objekt: git gc kan ta bort det (C2)
        (bas / 'los.md').unlink()
        git('checkout', '-q', '-b', 'tillfallig', cwd=g_)  # en commit som bara nås ur HEAD:s reflogg (C6)
        (g_ / 'utkast.md').write_bytes(gren)
        git('add', 'utkast.md', cwd=g_)
        git('commit', '-q', '-m', 'utkast', cwd=g_)
        git('checkout', '-q', 'main', cwd=g_)
        git('branch', '-q', '-D', 'tillfallig', cwd=g_)
        scr = bas / 'scratch' / 'claude-501'
        s_ok, s_los, s_gren = session_v7(scr, 1), session_v7(scr, 2), session_v7(scr, 3)
        (s_ok / 'scratchpad' / 'regel2.md').write_bytes(reg2)
        (s_los / 'scratchpad' / 'los.md').write_bytes(los)
        (s_gren / 'scratchpad' / 'utkast.md').write_bytes(gren)
        spara_h = stadning.HUVUDUTCHECKNING
        stadning.HUVUDUTCHECKNING = g_
        try:
            rap = stadning.stada(v7_ram(bas, scratch=scr, repo=g_), punkter=(4,))
            s_fel = session_v7(scr, 4)  # bara en fil som finns på main, men git svarar inte (S3)
            (s_fel / 'scratchpad' / 'regel2.md').write_bytes(reg2)
            kor_ = stadning.vl.kor
            stadning.vl.kor = lambda args, *a_, **k_: (128, 'fatal: rev-list föll (provet)') if list(args[:2]) == ['git', 'rev-list'] else kor_(args, *a_, **k_)
            try:
                rap_f = stadning.stada(v7_ram(bas, scratch=scr, repo=g_), punkter=(4,))
            finally:
                stadning.vl.kor = kor_
        finally:
            stadning.HUVUDUTCHECKNING = spara_h
        for s_, namn_ in ((s_los, 'los.md'), (s_gren, 'utkast.md')):
            p_ = en(rap, s_, 4)
            assert s_.is_dir() and p_['utfall'] == 'väntar på ägaren' and [m['sokvag'] for m in p_['material']] == ['scratchpad/' + namn_], (namn_, p_)
        assert not s_ok.exists() and en(rap, s_ok, 4)['utfall'] == 'raderad', poster(rap, s_ok)
        p_ = en(rap_f, s_fel, 4)
        assert s_fel.is_dir() and p_['utfall'] == 'väntar på ägaren' and 'gick inte att pröva' in p_['skal'], p_

    @v7('hjälparen korregister.egen_tmp skriver den ägarfil som städningen läser, i en egen process och i ett skalskript')
    def _v7_hjalparen():
        bas = TMP / 'v7' / 'hjalparen'
        r = v7_ram(bas)
        (bas / 'lank-till-tmp').symlink_to(bas / 'tmp', target_is_directory=True)
        kod_ = 'import sys; sys.path.insert(0, sys.argv[1]); import korregister; print(korregister.egen_tmp(sys.argv[3], "prov hjälparen", dir=sys.argv[2]))'
        slutade = []
        for dir_, prefix_ in ((bas / 'tmp', 'nwp-skill-'), (bas / 'lank-till-tmp', 'nwp-instrument-')):  # också via en länk: realpath (S13)
            ut_ = subprocess.run([sys.executable, '-B', '-c', kod_, str(ROOT / 'kontroller'), str(dir_), prefix_], capture_output=True, text=True, timeout=60)
            assert ut_.returncode == 0, ut_.stderr[-400:]
            slutade.append(Path(ut_.stdout.strip()))  # skapad av en process som nu har slutat
        lever_ = Path(korregister.egen_tmp('nwp-pip-', 'prov hjälparen levande', dir=str(bas / 'tmp')))
        kl_ = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'korregister.py'), 'tmp', 'nwp-motor-', 'prov skalskript',
                              '--dir', str(bas / 'tmp'), '--pid', str(os.getpid())], capture_output=True, text=True, timeout=60)
        assert kl_.returncode == 0, kl_.stderr[-400:]
        skal_ = Path(kl_.stdout.strip())
        utan_pid = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'korregister.py'), 'tmp', 'nwp-sub-', 'utan pid',
                                   '--dir', str(bas / 'tmp')], capture_output=True, text=True, timeout=60)
        assert utan_pid.returncode == 2 and not list((bas / 'tmp').glob('nwp-sub-*')), ('utan --pid registreras inget mellanskal (KAN-6)', utan_pid.stdout)
        post_, fel_ = korregister.tmp_agare(slutade[0])
        assert post_ and post_['vad'] == 'prov hjälparen' and post_['sokvag'] == os.path.realpath(slutade[0]) and post_['pstart'], (post_, fel_)
        assert korregister.tmp_agare(skal_)[0]['pid'] == os.getpid() and stat_agare(skal_) == 0o600
        rap = stadning.stada(r, punkter=(4,))
        for x_ in slutade:
            x_r = Path(os.path.realpath(x_)) if x_.exists() else bas / 'tmp' / x_.name
            assert not x_r.exists() and en(rap, x_r, 4)['utfall'] == 'raderad', (x_, poster(rap, x_r))
        for x_ in (lever_, skal_):
            assert x_.is_dir() and 'pågår' in en(rap, x_, 4)['skal'], poster(rap, x_)
        with korregister.egen_tmp_med('nwp-yt-', 'prov kontext', dir=str(bas / 'tmp')) as k_:
            assert korregister.tmp_agare(k_)[0]['vad'] == 'prov kontext'
        assert not os.path.exists(k_)

    @v7('verktygen registrerar det de skapar: varje katalog med repots prefix registreras där den skapas (KAN-8)')
    def _v7_verktygen():
        filer_v = [ROOT / 'kor.sh', ROOT / 'dashboard.sh']
        for bas_ in (ROOT / 'kontroller', ROOT / 'dashboard', ROOT / '.claude' / 'hooks'):
            for r_d, mappar_, fn_ in os.walk(bas_):
                mappar_[:] = [m for m in mappar_ if m != 'node_modules']
                filer_v += [Path(r_d) / f for f in fn_ if f.endswith(('.py', '.mjs', '.js', '.sh'))]
        # en katalog som skapas direkt (tempfile.mkdtemp eller mkdtempSync) tilldelas en variabel som samma fil registrerar
        # (registrera_tmp, registrera( eller provets agarfil); TemporaryDirectory och mktemp med repots prefix går inte att
        # registrera och ska inte finnas; korregister.py tmp i ett skalskript har --pid
        raa = (re.compile(r'(\w+)\s*=\s*(?:[\w.]+\()*\s*(?:tempfile\.)?mkdtemp\([^)]*?prefix=[\'"]([^\'"]+)[\'"]'),
               re.compile(r'(\w+)\s*=\s*mkdtempSync\(\s*join\(\s*tmpdir\(\)\s*,\s*[\'"]([^\'"]+)[\'"]'))
        alltid_fel = (re.compile(r'TemporaryDirectory\([^)]*?prefix=[\'"]([^\'"]+)[\'"]'), re.compile(r'mktemp\s+-d\s+(?:/tmp/)?([A-Za-z0-9_.-]+?)X{3,}'))
        utan, provade = [], 0
        for f_ in filer_v:
            if not f_.is_file():
                continue
            rader_ = f_.read_text(encoding='utf-8', errors='replace').splitlines()
            kommentar = '//' if f_.suffix in ('.mjs', '.js') else '#'
            kod_ = '\n'.join(x for x in rader_ if not x.strip().startswith(kommentar))  # en bortkommenterad registrering räknas inte
            for m_ in raa:
                for x_ in m_.finditer(kod_):
                    var_, prefix_ = x_.group(1), x_.group(2)
                    if not prefix_.startswith(stadning.TMP_PREFIX):
                        continue
                    provade += 1
                    if not re.search(r'(?:registrera_tmp|agarfil|registrera)\(\s*(?:Path\()?\s*%s\b' % re.escape(var_), kod_):
                        utan.append('%s: %s skapas med %s utan registrering' % (f_.relative_to(ROOT), var_, prefix_))
            for m_ in alltid_fel:
                for x_ in m_.finditer(kod_):
                    if x_.group(1).startswith(stadning.TMP_PREFIX):
                        utan.append('%s: %s skapas utan hjälparen' % (f_.relative_to(ROOT), x_.group(1)))
            for rad_ in kod_.splitlines():
                if re.search(r'korregister\.py[\'"]?\s+tmp\s', rad_) and '--pid' not in rad_:
                    utan.append('%s: korregister.py tmp utan --pid: %s' % (f_.relative_to(ROOT), rad_.strip()[:120]))
        assert provade >= 8 and not utan, (provade, utan)
        # och i en körning: slugvaktens tmp_katalog (upptagna_val) registrerar det den skapar
        import slugvakt
        spara_td, spara_slug = tempfile.tempdir, os.environ.pop('NWP_SLUG', None)
        tempfile.tempdir = str(TMPDIR_ROT)
        try:
            dk_ = slugvakt.tmp_katalog('upptagna-')
        finally:
            tempfile.tempdir = spara_td
            if spara_slug is not None:
                os.environ['NWP_SLUG'] = spara_slug
        post_dk, fel_dk = korregister.tmp_agare(dk_)
        assert post_dk and post_dk['pid'] == os.getpid() and Path(dk_).parent == TMPDIR_ROT, (dk_, fel_dk)
        shutil.rmtree(dk_)

    assert not V7_FEL, 'villkoren 2026-10-07 som föll: %s' % V7_FEL

    # ===== Ö7: okända worktrees och processer rör ingenting =====
    K['extra'] = kopia('kopia-extra')
    (TMPROT / 'nwp-skill-extra').mkdir()
    (TMPROT / 'nwp-skill-extra' / 'x').write_text('x')
    agarfil(TMPROT / 'nwp-skill-extra', *DOD)
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
    kor_orig = stadning.vl.kor
    stadning.vl.kor = lambda args, *a, **k: (128, 'fatal: git cat-file föll') if list(args[:2]) == ['git', 'cat-file'] else kor_orig(args, *a, **k)
    try:
        rap_e1 = stadning.stada(ram(), punkter=(1, 2))
    finally:
        stadning.vl.kor = kor_orig
    for d_, pk_ in ((K['catfile'], 2), (WT['catfile'], 1)):
        p_ = en(rap_e1, d_, pk_)
        assert d_.is_dir() and p_['utfall'] == 'väntar på ägaren' and 'git cat-file' in p_['skal'], (d_, p_)
    assert not [p for p in rap_e1['poster'] if p['utfall'] in ('raderad', 'fel')], rap_e1['poster']
    klar('E1: när git cat-file faller går materialet inte att jämföra, och kopian och worktreen väntar på ägaren')
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
               re.compile(r'''mktemp\s+-d\s+(?:/tmp/)?([A-Za-z0-9_.-]+?)X{3,}'''),
               re.compile(r'''egen_tmp(?:_med)?\(\s*['"]([^'"]+)['"]'''),                # korregister.egen_tmp (2026-10-07)
               re.compile(r'''korregister\.py['"]?\s+tmp\s+['"]?([A-Za-z0-9_.-]+[-.])(?=['"]?\s)'''))  # hjälparens kommando i ett skalskript
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
    # .ateljeslut- är en atomisk tempfil bredvid slutposten, aldrig en katalog i systemets temp.
    UTANFOR_TMP = {'.vinnare-ny-', 'prov-', '.ateljeslut-', '.korslut-'}  # kundens katalog eller under nwp-bygge-<slug>
    saknas_ = {x: f for x, f in FUNNA.items() if x not in stadning.TMP_PREFIX and x not in UTANFOR_TMP}
    assert not saknas_, 'prefix i koden som städningen inte känner till: %s' % saknas_
    assert {'nwp-underhall-', 'nwp-lh-', 'nwp-sandlada-prov.', 'upptagna-', 'nwp-stadprov-', 'nwp-tillbaka-'} <= set(FUNNA), sorted(FUNNA)
    assert not [n for n in stadning.ALDRIG_TMP if n.startswith(stadning.TMP_PREFIX)], 'ett prefix når en fast katalog i /tmp'
    skapade = {}
    for prefix_ in sorted(set(FUNNA) - UTANFOR_TMP):
        d_ = Path(tempfile.mkdtemp(prefix=prefix_, dir=TMPDIR_ROT))  # som verktyget skapar den när TMPDIR pekar hit
        (d_ / 'fil').write_text(prefix_)
        agarfil(d_, *DOD)  # och registrerar den (korregister.egen_tmp); körningen har slutat
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

    # ===== npm-cachen: sökvägen utan att köra npm (K-b: npm config get roterar ~/.npm/_logs, också i torrläget) =====
    FALSK_NPM = TMP / 'falsk-npm'
    FALSK_NPM.mkdir()
    (FALSK_NPM / 'npm').write_text('#!/bin/bash\necho "$@" >> %s\necho /fel/cache\n' % (TMP / 'npm-anrop'))
    (FALSK_NPM / 'npm').chmod(0o755)
    spara_miljo = {k_: os.environ.get(k_) for k_ in ('PATH', 'npm_config_cache')}
    os.environ['PATH'] = '%s:%s' % (FALSK_NPM, spara_miljo['PATH'])
    os.environ['npm_config_cache'] = str(TMP / 'npm-ur-miljon')
    try:
        c_ = stadning.npm_cache_katalog()
    finally:
        for k_, v_ in spara_miljo.items():
            if v_ is None:
                os.environ.pop(k_, None)
            else:
                os.environ[k_] = v_
    assert not (TMP / 'npm-anrop').exists() and c_ == TMP / 'npm-ur-miljon', ('npm kördes för att hitta cachen', c_)
    HEM = TMP / 'hem'
    HEM.mkdir()
    assert stadning.npm_cache_katalog(miljo={}, hem=HEM) == HEM / '.npm'
    (HEM / '.npmrc').write_text('; kommentar\nregistry=https://registry.npmjs.org/\ncache = ~/annan-cache\n')
    assert stadning.npm_cache_katalog(miljo={}, hem=HEM) == HEM / 'annan-cache'
    (HEM / '.npmrc').write_text('cache=relativ/sokvag\n')
    assert stadning.npm_cache_katalog(miljo={}, hem=HEM) is None
    r_n = ram()
    r_n.npm_cache = None
    (p5_,) = poster(stadning.stada(r_n, punkter=(5,)), punkt=5)
    assert p5_['utfall'] == 'kvar' and 'inte kontrollerad' in p5_['skal'], p5_
    klar('K-b: npm-cachens sökväg ur $npm_config_cache, ~/.npmrc eller ~/.npm utan att npm körs; annars inte kontrollerad')

    # ===== KAN-2: den skarpa rensningen låter npm själv avgöra cachen; torrläget kör aldrig npm =====
    # npm:s egen konfiguration (NPM_CONFIG_USERCONFIG, granskarens N1) pekar på en annan cache än städningens uppskattning
    # (ram.npm_cache är NPM). HOME ligger i provet, så att riktig npm aldrig når ~/.npm.
    NPM_EGEN, NPM_HEM = TMP / 'npm-egen', TMP / 'npm-hem'
    NPM_HEM.mkdir()
    (NPM_HEM / 'egen-npmrc').write_text('cache=%s\n' % NPM_EGEN)

    def npm_egen_konfig(torr, falsk_npm=False):
        for c_ in (NPM, NPM_EGEN):
            (c_ / '_cacache' / 'content-v2').mkdir(parents=True, exist_ok=True)
            (c_ / '_cacache' / 'content-v2' / 'paket').write_bytes(b'x' * 5000)
        r_e = ram(torr=torr, disk=lambda: (1000 * 2 ** 30, 100 * 2 ** 30))  # 90 % fylld: rensas
        spara_e = {k_: os.environ.get(k_) for k_ in ('HOME', 'NPM_CONFIG_USERCONFIG', 'npm_config_cache', 'NPM_CONFIG_CACHE', 'PATH')}
        os.environ.pop('npm_config_cache', None)
        os.environ.pop('NPM_CONFIG_CACHE', None)  # npm läser båda stavningarna före npmrc
        os.environ.update(HOME=str(NPM_HEM), NPM_CONFIG_USERCONFIG=str(NPM_HEM / 'egen-npmrc'))
        if falsk_npm:
            os.environ['PATH'] = '%s:%s' % (FALSK_NPM, spara_e['PATH'])
        try:
            rap_e = stadning.stada(r_e, punkter=(5,))
        finally:
            for k_, v_ in spara_e.items():
                if v_ is None:
                    os.environ.pop(k_, None)
                else:
                    os.environ[k_] = v_
        (p5,) = poster(rap_e, punkt=5)
        return p5

    p_ = npm_egen_konfig(torr=False)
    assert p_['utfall'] == 'rensad' and not (NPM_EGEN / '_cacache').exists() and (NPM / '_cacache').exists(), \
        ('npm fick städningens uppskattade sökväg (--cache) i stället för att själv avgöra cachen', p_)
    assert p_['sokvag'] == str(NPM / '_cacache') and 'uppskattning' in p_['skal'] and 'utan --cache' in p_['skal'], p_
    (TMP / 'npm-anrop').unlink(missing_ok=True)
    p_ = npm_egen_konfig(torr=True, falsk_npm=True)
    assert p_['utfall'] == 'skulle rensas' and not (TMP / 'npm-anrop').exists() and (NPM_EGEN / '_cacache').exists(), p_
    assert 'uppskattning' in p_['skal'], p_
    klar('KAN-2: den skarpa rensningen kör npm cache clean utan --cache, och npm rensar cachen ur sin egen konfiguration; '
         'torrläget kör inte npm och redovisar sökvägen som en uppskattning')

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
    agarfil(KANARIE, *DOD)

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
    r_u = ram(disk=lambda: (1000 * 2 ** 30, 100 * 2 ** 30), tillstand=TMP / 'lage-utanfor')
    r_u.repo = Path(os.path.realpath(K['material']))  # körd ur något annat än huvudutcheckningen: bara redovisning
    rad_u, d_u = sk.diskvakt(k_, r_u)
    assert 'städningen redovisade bara' in rad_u['detalj'] and 'kördes' not in rad_u['detalj'] and rad_u['resultat'] == 'okand', rad_u
    assert 'städningen redovisade bara' in sk.markdown(dict(kv_, rader=[rad_u], diskvakt=d_u)) and not (TMP / 'lage-utanfor').exists()
    klar('K-f: kvittot skiljer städningen som kördes från städningen som bara redovisade')
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
