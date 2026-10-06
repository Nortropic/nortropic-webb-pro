#!/usr/bin/env python3
"""prov_stadning.py — städregeln (kontroller/stadning.py; ägarens beslut 2026-10-06 i BESLUT.md, delvis ersatt samma dag)
i temporära kataloger, med en lokal bar git-origin, provets egna processer och en injicerad klocka, diskmått och
processlista. Varje fall kan bli rött:

- kopior: en med eget kundmaterial står kvar och väntar på ägaren, med listan (sökväg och storlek); en utan eget material
  raderas (node_modules, dist, .astro, rökprovets testsajt och en symlänk till huvudutcheckningen är inget material), och
  likaså en liknande katalog som inte heter kopia; en som en process använder, en med egna commits och en av okänt
  ursprung står kvar;
- huvudutcheckningens underlag/ och kunder/ är byte för byte oförändrade (sha256 före och efter), och skyddet vägrar
  radera dem;
- worktrees: en sammanslagen och pushad tas bort och grenen finns kvar; en osammanslagen, en sammanslagen med
  ocommittade ändringar, en som inte är pushad, en med eget material, en som ändrats det senaste dygnet och en som används
  står kvar;
- processer: en föräldralös förhandsvisning eller server inom räckvidden stoppas (också den som höll en kopia, som sedan
  raderas i samma körning); en utanför räckvidden, en med levande förälder, en som inte är en server, ägarens dashboard
  på 4771 och en som är yngre än ett dygn lämnas;
- tillfälliga kataloger: en gammal med känt prefix raderas; en okänd, en ung och en som används lämnas; scratchpads
  sessioner raderas efter sju dygn; varje tempfile- och mktemp-prefix i koden finns i listan;
- npm-cachen: över 85 %, under 85 % med färsk rensning och under 85 % med 31 dygn gammal rensning;
- diskvakten under och över 15 %, och startkvittot med ledigt före och efter;
- torrläget ändrar ingenting; redovisningens fält; underhållets rapport; NWP_STADNING=av når aldrig det verkliga systemet.

    .venv/bin/python kontroller/rokprov/revision/prov_stadning.py <repo>

Processlistan är maskinens (ps och lsof), men bara provets egna processer räknas, och stoppet vägrar alla andra. Det
verkliga systemet (~/nortropic-repos, /tmp, ~/.npm) rörs aldrig: Ram.verklig fäller provet om något anropar den.
"""
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


def klar(namn):
    KLARA.append(namn)
    print('ok: ' + namn)


GIT = ['git', '-c', 'user.name=prov', '-c', 'user.email=prov@exempel.se', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']


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


# --- huvudutcheckningen, origin och kundmaterialet ---
ORIGIN = TMP / 'origin.git'
sh('git', 'init', '-q', '--bare', '-b', 'main', ORIGIN)
REPOS = TMP / 'repos'
HUVUD = REPOS / 'nortropic-webb-pro'
(HUVUD / 'kontroller').mkdir(parents=True)
(HUVUD / 'kor.sh').write_text('#!/bin/bash\n')
(HUVUD / 'kontroller' / 'x.py').write_text('x = 1\n')
(HUVUD / '.gitignore').write_text('underlag/\nkunder/\nnode_modules/\ndist/\n.astro/\n')
git('init', '-q', '-b', 'main', cwd=HUVUD)
git('add', '-A', cwd=HUVUD)
git('commit', '-q', '-m', 'början', cwd=HUVUD)
git('remote', 'add', 'origin', ORIGIN, cwd=HUVUD)
git('push', '-q', '-u', 'origin', 'main', cwd=HUVUD)
MATERIAL = {'underlag/kund-a/BRIEF.md': b'# Brief\n', 'underlag/kund-a/bilder/jobb.jpg': b'\xff\xd8\xff' + bytes(range(256)) * 8,
            'underlag/kund-a/DESIGNDOMAR.jsonl': b'{"dom": "ny riktning"}\n', 'kunder/kund-a/sajt/src/pages/index.astro': b'<h1>Kund A</h1>\n',
            'kunder/kund-a/sajt/node_modules/paket/index.js': b'module.exports = 1\n'}
for rel_, data_ in MATERIAL.items():
    (HUVUD / rel_).parent.mkdir(parents=True, exist_ok=True)
    (HUVUD / rel_).write_bytes(data_)
FORE = manifest(HUVUD)
assert len(FORE) == len(MATERIAL), FORE


# --- worktrees ---
def worktree(gren, fil):
    wt = REPOS / ('nortropic-webb-pro-' + gren)
    git('worktree', 'add', '-q', '-b', gren, wt, 'main', cwd=HUVUD)
    (wt / fil).write_text(gren + '\n')
    git('add', '-A', cwd=wt)
    git('commit', '-q', '-m', gren, cwd=wt)
    return wt


WT_KLAR, WT_SMUTSIG, WT_MATERIAL, WT_AKTIV, WT_ANVAND = (worktree(g, g + '.md') for g in ('klar', 'smutsig', 'material', 'aktiv', 'anvand'))
git('merge', '-q', '--no-ff', '-m', 'sammanslagning', 'klar', 'smutsig', 'material', 'aktiv', 'anvand', cwd=HUVUD)
git('push', '-q', 'origin', 'main', cwd=HUVUD)
WT_PAGAR = worktree('pagar', 'pagar.md')  # inte sammanslagen
WT_LOKAL = worktree('lokal', 'lokal.md')
git('merge', '-q', '--no-ff', '-m', 'lokal', 'lokal', cwd=HUVUD)  # sammanslagen men inte pushad
(WT_SMUTSIG / 'smutsig.md').write_text('ändrad men inte committad\n')
EGET_WT = b'bara i worktreen\n'
(WT_MATERIAL / 'underlag' / 'kund-b').mkdir(parents=True)
(WT_MATERIAL / 'underlag' / 'kund-b' / 'ANTECKNING.md').write_bytes(EGET_WT)
for rel_ in ('kunder/rokprov-mall/prov/STATUS.json', 'underlag/startkontroll/CACHE.json', 'kunder/kund-a/sajt/node_modules/x/i.js'):
    (WT_KLAR / rel_).parent.mkdir(parents=True, exist_ok=True)  # rökprovets testsajt, verktygslådans läge, beroenden: inget material
    (WT_KLAR / rel_).write_text('{}\n')
os.utime(WT_AKTIV / 'aktiv.md', (T - 3600, T - 3600))  # ändrad det senaste dygnet


# --- kopior ---
def kopia(namn):
    d = REPOS / namn
    shutil.copytree(HUVUD, d, symlinks=True)
    return d


EGEN_1, EGEN_2 = b'bara i kopian\n', b'<h1>Kund A, ny rubrik</h1>\n'
K_MATERIAL = kopia('kopia-material')
(K_MATERIAL / 'underlag' / 'kund-a' / 'ANTECKNINGAR.md').write_bytes(EGEN_1)
(K_MATERIAL / 'kunder' / 'kund-a' / 'sajt' / 'src' / 'pages' / 'index.astro').write_bytes(EGEN_2)  # samma sökväg, annat innehåll
K_TOM = kopia('kopia4')
for rel_ in ('kunder/kund-a/sajt/dist/index.html', 'kunder/kund-a/sajt/.astro/typer.d.ts', 'kunder/kund-a/sajt/node_modules/ny/index.js',
             'kunder/rokprov-mall/prov/STATUS.json', 'underlag/rokprov-mall/BESTALLNING.md', 'underlag/startkontroll/CACHE.json',
             'underlag/kund-a/.DS_Store'):
    (K_TOM / rel_).parent.mkdir(parents=True, exist_ok=True)
    (K_TOM / rel_).write_text('provets egna\n')
os.symlink(HUVUD / 'kunder', K_TOM / 'kunder' / 'lank-till-huvudutcheckningen')  # följs aldrig
K_GAMMAL = kopia('nortropic-webb-pro-r68')  # liknande: repots kännetecken, inte en registrerad worktree
K_ANVAND = kopia('kopia-anvand')
K_SERVER = kopia('nortropic-webb-pro-kopia-server')
K_COMMIT = kopia('kopia-commit')
(K_COMMIT / 'kontroller' / 'eget.py').write_text('eget = 1\n')
git('add', '-A', cwd=K_COMMIT)
git('commit', '-q', '-m', 'en egen commit', cwd=K_COMMIT)
K_OKAND = REPOS / 'kopia-okand'
K_OKAND.mkdir()
(K_OKAND / 'anteckning.txt').write_text('okänt ursprung\n')
ANNAT = REPOS / 'annat-projekt'
ANNAT.mkdir()
(ANNAT / 'fil.txt').write_text('ägarens\n')

# --- /tmp och scratchpad ---
TMPROT = TMP / 'tmp'
for n_ in ('nwp-skill-gammal', 'nwp-pip-anvand', 'nwp-motor-ung', 'okand-katalog', 'nwp-korningar', 'nwp-bygge-prov',
           'forhand-a', 'forhand-b', 'forhand-c', 'forhand-d', 'forhand-e'):
    (TMPROT / n_).mkdir(parents=True)
    (TMPROT / n_ / 'fil.txt').write_text(n_)
(TMPROT / 'nwp-lh-en-fil').write_text('en fil, ingen katalog\n')
os.utime(TMPROT / 'nwp-motor-ung' / 'fil.txt', (T - 3600, T - 3600))
SCR = TMP / 'scratch' / 'claude-501'
S_GAMMAL = SCR / '-Users-prov' / '11111111-2222-3333-4444-555555555555'
S_UNG = SCR / '-Users-prov' / '22222222-3333-4444-5555-666666666666'
S_ANVAND = SCR / '-Users-prov' / '33333333-4444-5555-6666-777777777777'
S_EJ = SCR / '-Users-prov' / 'inte-en-session'
S_ANNAT = SCR / 'bash-edit-diff'
for s_ in (S_GAMMAL, S_UNG, S_ANVAND, S_EJ, S_ANNAT):
    (s_ / 'scratchpad').mkdir(parents=True)
    (s_ / 'scratchpad' / 'anteckning.md').write_text('x\n')
    satt_tid(s_, T - 8 * DYGN)
os.utime(S_UNG / 'scratchpad' / 'anteckning.md', (T - 6 * DYGN, T - 6 * DYGN))
# en katalog vars mtime flyttats när något i den togs bort (som nattens städning i /tmp): ändrad räknas ur filerna och
# katalogens birthtime, så sessionen är fortfarande gammal
os.utime(S_GAMMAL / 'scratchpad', (T - 3600, T - 3600))
UTANFOR = TMP / 'utanfor'
UTANFOR.mkdir()
NPM = TMP / 'npm'
LAGE = TMP / 'lage'
vl.skriv_json(LAGE / 'NPM-CACHE.json', {'tid': iso(T - DYGN)})  # färsk rensning: punkt 5 rensar inget i huvudkörningarna
(NPM / '_cacache' / 'content-v2').mkdir(parents=True)
(NPM / '_cacache' / 'content-v2' / 'paket').write_bytes(b'x' * 5000)

# --- provets egna processer ---
EGNA, BARN, STOPPADE = set(), [], []


def vanta_pa(pid, namn, utan_foralder):
    for _ in range(200):
        if korregister.ps('command', pid).startswith(namn) and (not utan_foralder or korregister.ps('ppid', pid) == '1'):
            return pid
        time.sleep(0.05)
    raise AssertionError('pid %d blev aldrig "%s" (ppid 1: %s): %r' % (pid, namn, utan_foralder, korregister.ps('command', pid)))


def foraldralos(katalog, namn):
    """En process utan levande förälder (ppid 1) med namnet som kommando och arbetskatalogen katalog."""
    r = subprocess.run(['bash', '-c', '(cd "$1" && exec -a "$2" sleep 600) </dev/null >/dev/null 2>&1 & echo $!', 'prov', str(katalog), namn],
                       capture_output=True, text=True, timeout=30)
    pid = int(r.stdout.strip())
    EGNA.add(pid)
    return vanta_pa(pid, namn, True)


def med_foralder(katalog, namn):
    p = subprocess.Popen(['bash', '-c', 'exec -a "$1" sleep 600', 'prov', namn], cwd=str(katalog), stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    EGNA.add(p.pid)
    BARN.append(p)
    return vanta_pa(p.pid, namn, False)


def egna_processer():
    alla = stadning.las_processer()
    assert alla is not None, 'ps svarar inte'
    return [x for x in alla if x['pid'] in EGNA]


def stoppa(pid):
    assert pid in EGNA, 'provet stoppar bara sina egna processer (pid %d)' % pid
    STOPPADE.append(pid)
    os.kill(pid, signal.SIGTERM)


def ram(klocka=lambda: T, disk=None, torr=False, upptagen=lambda: None):
    return stadning.Ram(repo=HUVUD, repos_rot=REPOS, tmp_rot=TMPROT, scratch_rot=SCR, npm_cache=NPM, tillstand=LAGE, klocka=klocka,
                        disk=disk or (lambda: (1000 * 2 ** 30, 500 * 2 ** 30)), processer=egna_processer, stoppa=stoppa,
                        upptagen=upptagen, torr=torr, vanta_stopp=10)


def poster(rap, sokvag=None, punkt=None):
    return [p for p in rap['poster'] if (sokvag is None or p['sokvag'] == str(sokvag)) and (punkt is None or p['punkt'] == punkt)]


def en(rap, sokvag, punkt=None):
    x = poster(rap, sokvag, punkt)
    assert len(x) == 1, (str(sokvag), x)
    return x[0]


try:
    P_ASTRO = foraldralos(TMPROT / 'forhand-a', 'astro preview')  # stoppas
    P_UTANFOR = foraldralos(UTANFOR, 'astro preview')  # utanför räckvidden: lämnas
    P_FORALDER = med_foralder(TMPROT / 'forhand-b', 'astro dev')  # levande förälder: lämnas
    P_HTTP = foraldralos(WT_PAGAR, 'python3 -m http.server 8000')  # i en worktree: stoppas
    P_4771 = foraldralos(TMPROT / 'forhand-c', '.venv/bin/python -B dashboard/server.py --port 4771')  # ägarens: lämnas
    P_4772 = foraldralos(TMPROT / 'forhand-d', '.venv/bin/python -B dashboard/server.py --port 4772')  # stoppas
    P_SLEEP = foraldralos(TMPROT / 'forhand-e', 'sleep')  # inte en server: lämnas
    P_KOPIA = foraldralos(K_SERVER, 'astro preview')  # håller kopian: stoppas, och kopian raderas
    U_KOPIA = med_foralder(K_ANVAND, 'sleep')
    U_TMP = med_foralder(TMPROT / 'nwp-pip-anvand', 'sleep')
    U_SCR = med_foralder(S_ANVAND, 'sleep')
    U_WT = med_foralder(WT_ANVAND, 'sleep')
    lasta = {x['pid']: x for x in egna_processer()}
    assert set(lasta) == EGNA and lasta[P_KOPIA]['cwd'] == str(K_SERVER) and lasta[P_ASTRO]['ppid'] == 1, lasta
    assert lasta[P_FORALDER]['ppid'] == os.getpid() and all(x['start'] and x['lstart'] for x in lasta.values())
    klar('processlistan: ps och lsof ger förälder, start, kommando och arbetskatalog för provets processer')

    # ===== yngre än ett dygn (provets klocka är den riktiga): inget stoppas och inget raderas =====
    rap0 = stadning.stada(ram(klocka=time.time), punkter=(1, 2, 3, 4))
    assert not [p for p in rap0['poster'] if p['utfall'] in ('raderad', 'stoppad', 'fel')], [p for p in rap0['poster'] if p['utfall'] in ('raderad', 'stoppad', 'fel')]
    assert not STOPPADE and all(korregister.lever(p) for p in EGNA)
    assert 'yngre än ett dygn' in en(rap0, TMPROT / 'forhand-a', 3)['skal'] and 'ändrad det senaste dygnet' in en(rap0, WT_KLAR, 1)['skal']
    assert 'ändrad det senaste dygnet' in en(rap0, K_TOM, 2)['skal']
    klar('yngre än ett dygn: processen, worktreen och kopian lämnas')

    # ===== torrläget: listan, inget ändrat =====
    rapA = stadning.stada(ram(torr=True))
    assert rapA['torr'] and not STOPPADE and all(korregister.lever(p) for p in EGNA), STOPPADE
    for d_, pk_ in ((K_TOM, 2), (K_SERVER, 2), (K_GAMMAL, 2), (WT_KLAR, 1), (TMPROT / 'nwp-skill-gammal', 4), (S_GAMMAL, 4)):
        assert d_.exists() and en(rapA, d_, pk_)['utfall'] == 'skulle raderas', (d_, poster(rapA, d_))
    for d_ in (TMPROT / 'forhand-a', TMPROT / 'forhand-d', WT_PAGAR, K_SERVER):
        assert en(rapA, d_, 3)['utfall'] == 'skulle stoppas', poster(rapA, d_, 3)
    assert manifest(HUVUD) == FORE and not [p for p in rapA['poster'] if p['utfall'] in ('raderad', 'stoppad', 'rensad')]
    assert 'Torrläge: inget ändrat' in '\n'.join(stadning.markdown(rapA))
    klar('torrläget listar vad som skulle göras och ändrar ingenting')

    # ===== städningen på riktigt =====
    rapB = stadning.stada(ram())
    assert not [p for p in rapB['poster'] if p['utfall'] == 'fel'], [p for p in rapB['poster'] if p['utfall'] == 'fel']

    # kopior
    p_ = en(rapB, K_MATERIAL)
    assert K_MATERIAL.is_dir() and p_['utfall'] == 'väntar på ägaren' and p_['material_antal'] == 2, p_
    assert {(m['sokvag'], m['storlek']) for m in p_['material']} == {('underlag/kund-a/ANTECKNINGAR.md', len(EGEN_1)),
                                                                   ('kunder/kund-a/sajt/src/pages/index.astro', len(EGEN_2))}, p_['material']
    assert p_['storlek_fore'] > 0 and 'underlag/kund-a/ANTECKNINGAR.md' in p_['skal']
    md_ = '\n'.join(stadning.markdown(rapB))
    assert '`underlag/kund-a/ANTECKNINGAR.md` (%d B)' % len(EGEN_1) in md_ and '**Väntar på ägaren**' in md_, md_
    klar('en kopia med eget kundmaterial står kvar och väntar på ägaren, med listan (sökväg och storlek)')
    assert not K_TOM.exists() and en(rapB, K_TOM)['utfall'] == 'raderad', poster(rapB, K_TOM)
    assert not K_GAMMAL.exists() and en(rapB, K_GAMMAL)['utfall'] == 'raderad'
    klar('en kopia utan eget material raderas (node_modules, dist, .astro, testsajten och en symlänk är inget material), också en liknande')
    assert K_ANVAND.is_dir() and en(rapB, K_ANVAND)['utfall'] == 'kvar' and 'pid %d' % U_KOPIA in en(rapB, K_ANVAND)['skal']
    assert K_COMMIT.is_dir() and en(rapB, K_COMMIT)['utfall'] == 'väntar på ägaren' and 'egen commit' in en(rapB, K_COMMIT)['skal']
    assert K_OKAND.is_dir() and en(rapB, K_OKAND)['utfall'] == 'väntar på ägaren' and 'okänt ursprung' in en(rapB, K_OKAND)['skal']
    assert ANNAT.is_dir() and not poster(rapB, ANNAT) and (ANNAT / 'fil.txt').read_text() == 'ägarens\n'
    klar('kopior som används, har egna commits eller har okänt ursprung står kvar; annat i ~/nortropic-repos rörs inte')

    # huvudutcheckningen
    assert manifest(HUVUD) == FORE and (HUVUD / '.git').is_dir() and git('status', '--porcelain', cwd=HUVUD) == ''
    r_ = ram()
    for p_s in (HUVUD, HUVUD / 'kunder', HUVUD / 'underlag', HUVUD / 'underlag' / 'kund-a', REPOS, TMPROT, SCR, UTANFOR):
        assert stadning.radera(r_, p_s).startswith('raderas aldrig') and p_s.exists(), p_s
    assert manifest(HUVUD) == FORE
    klar('huvudutcheckningens underlag/ och kunder/ är byte för byte oförändrade, och skyddet vägrar radera dem')

    # worktrees
    assert not WT_KLAR.exists() and en(rapB, WT_KLAR)['utfall'] == 'raderad' and en(rapB, WT_KLAR)['gren'] == 'klar', poster(rapB, WT_KLAR)
    assert git('rev-parse', '--verify', '-q', 'refs/heads/klar', cwd=HUVUD).strip() and str(WT_KLAR) not in git('worktree', 'list', cwd=HUVUD)
    klar('en sammanslagen och pushad worktree tas bort med git worktree remove, och grenen finns kvar')
    for wt_, del_ in ((WT_PAGAR, 'inte sammanslagen'), (WT_SMUTSIG, 'ocommittade ändringar'), (WT_LOKAL, 'inte pushad'),
                      (WT_AKTIV, 'ändrad det senaste dygnet'), (WT_ANVAND, 'pid %d' % U_WT)):
        p_ = en(rapB, wt_, 1)
        assert wt_.is_dir() and p_['utfall'] == 'kvar' and del_ in p_['skal'], (wt_, p_)
    p_ = en(rapB, WT_MATERIAL, 1)
    assert WT_MATERIAL.is_dir() and p_['utfall'] == 'väntar på ägaren' and p_['material'] == [{'sokvag': 'underlag/kund-b/ANTECKNING.md', 'storlek': len(EGET_WT)}], p_
    assert (WT_SMUTSIG / 'smutsig.md').read_text() == 'ändrad men inte committad\n'
    klar('osammanslagen, sammanslagen med ocommittade ändringar, inte pushad, ändrad nyss, använd och med eget material står kvar')

    # processer
    stoppade_ = {P_ASTRO, P_HTTP, P_4772, P_KOPIA}
    assert set(STOPPADE) == stoppade_ and not any(korregister.lever(p) for p in stoppade_), (STOPPADE, stoppade_)
    for d_ in (TMPROT / 'forhand-a', TMPROT / 'forhand-d', WT_PAGAR, K_SERVER):
        assert en(rapB, d_, 3)['utfall'] == 'stoppad' and en(rapB, d_, 3)['pid'] in stoppade_, poster(rapB, d_, 3)
    assert not K_SERVER.exists() and en(rapB, K_SERVER, 2)['utfall'] == 'raderad', 'förhandsvisningen stoppas före kopian den höll'
    klar('föräldralösa servrar inom räckvidden (astro preview, http.server, dashboard på 4772) stoppas med SIGTERM')
    assert all(korregister.lever(p) for p in (P_UTANFOR, P_FORALDER, P_4771, P_SLEEP))
    assert not poster(rapB, UTANFOR) and not poster(rapB, TMPROT / 'forhand-e')
    assert 'föräldern lever' in en(rapB, TMPROT / 'forhand-b', 3)['skal'] and 'ägarens dashboard' in en(rapB, TMPROT / 'forhand-c', 3)['skal']
    klar('utanför räckvidden, med levande förälder, inte en server och ägarens dashboard på 4771 lämnas')

    # tillfälliga kataloger och scratchpad
    assert not (TMPROT / 'nwp-skill-gammal').exists() and en(rapB, TMPROT / 'nwp-skill-gammal')['utfall'] == 'raderad'
    for d_ in ('okand-katalog', 'nwp-motor-ung', 'nwp-korningar', 'nwp-bygge-prov', 'nwp-lh-en-fil'):
        assert (TMPROT / d_).exists() and not poster(rapB, TMPROT / d_), d_
    assert (TMPROT / 'nwp-pip-anvand').is_dir() and 'pid %d' % U_TMP in en(rapB, TMPROT / 'nwp-pip-anvand')['skal']
    klar('en gammal tempkatalog med känt prefix raderas; en okänd, en ung, en fast och en som används lämnas')
    assert not S_GAMMAL.exists() and en(rapB, S_GAMMAL)['utfall'] == 'raderad'
    assert S_UNG.is_dir() and not poster(rapB, S_UNG) and S_EJ.is_dir() and S_ANNAT.is_dir()
    assert S_ANVAND.is_dir() and 'pid %d' % U_SCR in en(rapB, S_ANVAND)['skal']
    klar('scratchpads sessioner raderas efter sju dygn utan process, också när en katalogs mtime flyttats av en borttagning; '
         'yngre, använda och annat i scratchpad lämnas')

    # prefixen i koden
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
    klar('varje tempfile- och mktemp-prefix i koden (%d) finns i städningens lista' % len(FUNNA))

    # ===== npm-cachen =====
    NPM_POSTER = []

    def npm_fall(fylld, senast_dygn, upptagen=lambda: None):
        (NPM / '_cacache' / 'content-v2').mkdir(parents=True, exist_ok=True)
        (NPM / '_cacache' / 'content-v2' / 'paket').write_bytes(b'x' * 5000)
        vl.skriv_json(LAGE / 'NPM-CACHE.json', {'tid': iso(T - senast_dygn * DYGN)})
        rap_ = stadning.stada(ram(disk=lambda: (1000 * 2 ** 30, int(1000 * 2 ** 30 * (1 - fylld))), upptagen=upptagen), punkter=(5,))
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
    p_, finns_, lage_ = npm_fall(0.90, 31, upptagen=lambda: 'en körning pågår (prov)')
    assert p_['utfall'] == 'kvar' and finns_ and 'en körning pågår' in p_['skal'], p_
    klar('npm-cachen rensas inte medan en körning eller en npm-installation pågår')

    # ===== diskvakten =====
    k_ = vl.Kontext(nat=False, prova=False, katalog=LAGE)
    KANARIE = TMPROT / 'nwp-torr-kanarie'
    KANARIE.mkdir()
    (KANARIE / 'x').write_text('x')
    rad_, d_ = sk.diskvakt(k_, ram(disk=lambda: (1000 * 2 ** 30, 400 * 2 ** 30)))
    assert rad_['resultat'] == 'ok' and 'över 15 %' in rad_['detalj'] and 'stadning' not in d_ and KANARIE.is_dir(), (rad_, d_)
    klar('diskvakten över 15 % ledigt: ingen städning före starten')
    rad_, d_ = sk.diskvakt(k_, ram(disk=lambda: (1000 * 2 ** 30, (100 if KANARIE.exists() else 200) * 2 ** 30)))
    assert not KANARIE.exists() and d_['fore']['andel_ledig'] == 0.1 and d_['efter']['andel_ledig'] == 0.2, d_
    assert rad_['resultat'] == 'ok' and 'städningen kördes' in rad_['detalj'] and not rad_.get('nodvandig'), rad_
    kv_ = {'slug': 'prov', 'tid': iso(T), 'status': 'redo', 'start': 'ny', 'stoppar': [], 'underhall': None, 'rader': [rad_],
           'till_byggaren': [], 'las': {}, 'diskvakt': d_}
    md_ = sk.markdown(kv_)
    assert 'Diskvakten: 10,0 % ledigt (100,0 GB av 1000,0 GB) före starten, under 15 %' in md_, md_
    assert '20,0 % ledigt (200,0 GB av 1000,0 GB) efter' in md_ and '## Städningen före starten' in md_ and str(KANARIE) in md_, md_
    klar('diskvakten under 15 % ledigt: städningen körs före starten, och kvittot visar ledigt före och efter')
    DISK_POSTER = d_['stadning']['poster']

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

    # ===== underhållet: städningen i varje körning, redovisningen i rapporten =====
    os.environ.pop('NWP_STADNING', None)
    spara_ = (uh.steg_pythonlas, uh.steg_brew_update, uh.steg_laga_globala, vl.inventera, vl.pagaende)
    stadning.Ram.verklig = classmethod(lambda cls, tillstand=None, torr=False: ram(torr=torr))
    uh.steg_pythonlas = uh.steg_brew_update = lambda k, rap: None
    uh.steg_laga_globala = lambda rap: None
    vl.inventera = lambda k, delar=None: []
    vl.pagaende = lambda egna=None: []
    try:
        rap_uh = uh.underhall(k=vl.Kontext(nat=False, prova=False, katalog=TMP / 'lage-uh'), prov=False)
    finally:
        uh.steg_pythonlas, uh.steg_brew_update, uh.steg_laga_globala, vl.inventera, vl.pagaende = spara_
        stadning.Ram.verklig = classmethod(verkligt)
    md_uh = (TMP / 'lage-uh' / 'UNDERHALL.md').read_text(encoding='utf-8')
    assert rap_uh['status'] == 'klart' and rap_uh['stadning']['poster'], rap_uh
    assert '## Städningen' in md_uh and 'VÄNTAR PÅ ÄGAREN' in md_uh and '`underlag/kund-a/ANTECKNINGAR.md`' in md_uh and str(K_MATERIAL) in md_uh, md_uh
    klar('underhållet städar i varje körning och skriver redovisningen i sin rapport')

    # ===== redovisningens fält =====
    ALLA = rap0['poster'] + rapA['poster'] + rapB['poster'] + NPM_POSTER + DISK_POSTER + rap_uh['stadning']['poster']
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

print('städningens prov: %d fall gröna' % len(KLARA), file=sys.stderr)
