#!/usr/bin/env python3
"""stadning.py — städregeln för arbetskopior, processer och cacher (ägarens beslut 2026-10-06 ~14:35Z, delvis ersatt samma
dag: ingenting arkiveras, skrot raderas, och det som verkar värdefullt raderas inte utan väntar på ägaren; ordagrant i
BESLUT.md, avsnittet "Tillägg 2026-10-06: städregel för arbetskopior, processer och cacher"). Det dagliga underhållet
(kontroller/underhall.py) städar vid varje körning och skriver redovisningen i sin rapport; startkontrollens diskvakt
(kontroller/startkontroll.py, punkt 6) städar före starten när disken har under 15 % ledigt. Går också att köra själv:

    .venv/bin/python kontroller/stadning.py [--torr] [--json]

Räckvidden är bara det flödet och agenterna skapat under ~/nortropic-repos, /tmp (/private/tmp) och scratchpad
(/private/tmp/claude-<uid>). Huvudutcheckningens underlag/ och kunder/, ~/Arkiv och det ägaren skapat rörs aldrig, och
dashboarden på port 4771 stoppas aldrig. Det en levande process använder (arbetskatalog, öppen fil eller argument) lämnas.

1. Worktrees: en registrerad worktree (git worktree list) vars gren är sammanslagen i main och finns i origin/main, utan
   ocommittade ändringar, utan eget material i underlag/ och kunder/ och utan ändringar det senaste dygnet (en ny gren
   som ännu inte fått en commit pekar också på main), tas bort med git worktree remove, aldrig --force. Grenen och dess
   commits finns kvar. Misslyckas det redovisas felet, och inget raderas.
2. Kopior av repot (kopia* och kataloger med repots kännetecken, kor.sh och kontroller/, som inte är registrerade
   worktrees): underlag/ och kunder/ jämförs med huvudutcheckningen (relativ sökväg och sha256). Utan eget material, utan
   egna commits och utan ändringar det senaste dygnet raderas kopian; med eget material står den kvar och väntar på
   ägaren, med listan (sökväg och storlek). En kopia av okänt ursprung väntar också på ägaren.
3. Processer: förhandsvisningar och servrar (astro preview och dev, python -m http.server, dashboards på andra portar än
   4771) med arbetskatalog i en worktree, en kopia, /tmp eller scratchpad, utan levande förälder (ppid 1) och äldre än
   ett dygn, stoppas med SIGTERM. Allt annat lämnas. Punkten körs först, så att en kopia som en gammal förhandsvisning
   höll kan städas i samma körning.
4. Tillfälliga filer: kataloger direkt i /tmp med repots egna tempfile- och mktemp-prefix (TMP_PREFIX) som inte ändrats
   på ett dygn, och scratchpads sessionskataloger (<projekt>/<session>/) som inte ändrats på sju dygn, raderas när ingen
   process använder dem.
5. npm-cachen: npm cache clean --force när disken är fylld över 85 %, annars när förra rensningen är äldre än 30 dygn
   (tiden i underhållets läge, underlag/startkontroll/NPM-CACHE.json). Aldrig medan en körning eller en npm-installation
   pågår.
7. Redovisningen: varje åtgärd med vad, sökväg, storlek före, tid (UTC, ur klockan), utfall och skäl.

Ändrat betyder här den senaste ändringen av en fil eller symlänk under katalogen (den senare av mtime och ctime: en kopia
med bevarade tider är ny fast filerna har gamla mtime) eller när en katalog i den skapades (en katalogs mtime flyttas
också när något tas bort ur den). Allt som rör omvärlden (rötterna, klockan, diskmåttet, processlistan, stoppet och npm) går
genom Ram, så att provet (kontroller/rokprov/revision/prov_stadning.py) aldrig rör det verkliga systemet. NWP_STADNING=av
stänger av städningen mot det verkliga systemet; rökprovet sätter den. --torr ändrar ingenting och listar vad som skulle
göras.
"""
import argparse
import bisect
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korregister  # noqa: E402  (processernas identitet och liv, som körregistret läser dem)
import verktygslada as vl  # noqa: E402

DYGN = 86400
TMP_ALDER = DYGN                 # punkt 4: en katalog i /tmp som inte ändrats på ett dygn
SCRATCH_ALDER = 7 * DYGN         # punkt 4: en scratchpad-session som inte ändrats på sju dygn
PROCESS_ALDER = DYGN             # punkt 3: en förhandsvisning eller server som gått mer än ett dygn
AKTIV = DYGN                     # punkt 1 och 2: en worktree eller kopia som ändrats det senaste dygnet är i arbete
NPM_FYLLD = 0.85                 # punkt 5: disken fylld över 85 %
NPM_INTERVALL = 30 * DYGN        # punkt 5: annars en gång i månaden
NPM_LAGE = 'NPM-CACHE.json'      # förra rensningen, i underhållets läge
DASHBOARD_PORT = 4771            # ägarens dashboard: stoppas aldrig
MATERIAL_MAX = 200               # så många filer av det egna materialet sparas i redovisningen (antal och summa alltid)

# Repots egna prefix för tempfile.mkdtemp, TemporaryDirectory, mkdtempSync och mktemp (punkt 4). Provet söker igenom
# koden och blir rött när ett prefix saknas här. Pythons förval (tmp) och andra verktygs kataloger rörs aldrig.
TMP_PREFIX = (
    'nwp-underhall-', 'nwp-global-', 'nwp-skill-', 'nwp-skillintag-', 'nwp-skillreserv-', 'nwp-sajtpaket-',
    'nwp-instrument-', 'nwp-pip-', 'nwp-nodeprov-', 'nwp-motor-',                  # underhall.py
    'nwp-vaktprov-',                                                                  # verktygslada.py
    'nwp-torr-',                                                                      # granska.py
    'nwp-kundrepo-',                                                                  # exportera.py
    'nwp-yt-', 'nwp-sub-',                                                            # youtube.py
    'nwp-lh-',                                                                        # lighthouse.mjs
    'upptagna-',                                                                      # upptagna_val.py (slugvakt.tmp_katalog)
    'nwp-tillbaka-',                                                                  # rokprov.sh
    'nwp-sandlada-prov.',                                                             # sandlada_prov.sh (mktemp)
    'nwp-startprov-', 'nwp-observation-', 'nwp-rev-', 'nwp-granskning-', 'nwp-pg-',  # rökprovets prov
    'nwp-stadprov-',                                                                  # prov_stadning.py
)
# fasta kataloger i /tmp som aldrig är tillfälliga: körregistret och intagslåset, läget när underlag/ är låst, och
# granskarnas och byggenas arbetsrötter (deras verktyg städar dem)
ALDRIG_TMP = ('nwp-korningar', 'nwp-startkontroll', 'nwp-granskning', 'nwp-granskarforsok')
ALDRIG_TMP_PREFIX = ('nwp-bygge-',)
# punkt 2: inget material, var de än ligger (byggen, beroenden, cacher och Finders metadata)
INTE_MATERIAL = ('node_modules', 'dist', '.astro', '__pycache__')
INTE_MATERIAL_FILER = ('.DS_Store',)
# flödets egna prov- och lägesdata, som rökprovet och verktygslådan skriver i varje utcheckning: inget kundmaterial
FLODETS_EGNA = ('underlag/rokprov-mall', 'kunder/rokprov-mall', 'underlag/startkontroll')

RADERAD, STOPPAD, RENSAD, KVAR, VANTAR, FEL = 'raderad', 'stoppad', 'rensad', 'kvar', 'väntar på ägaren', 'fel'
TORRT = {RADERAD: 'skulle raderas', STOPPAD: 'skulle stoppas', RENSAD: 'skulle rensas'}
UTFALL = (RADERAD, STOPPAD, RENSAD, KVAR, VANTAR, FEL) + tuple(TORRT.values())
SESSION = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
SERVRAR = (
    ('astro', re.compile(r'(?:^|[\s/])astro(?:\.m?js)?\s+(?:preview|dev)\b')),
    ('http.server', re.compile(r'(?i)python[\w.]*\s(?:.*\s)?-m\s*http\.server\b')),
    ('dashboard', re.compile(r'dashboard/server\.py\b')),
)
PORT = re.compile(r'--port[=\s]+(\d+)')
AGARENS_PORT = re.compile(r'(?:--port[=\s]+|:)%d\b' % DASHBOARD_PORT)


def avslagen():
    """NWP_STADNING=av: ingen städning mot det verkliga systemet (rökprovet). Torrläget och en Ram som ett prov ger berörs inte."""
    return os.environ.get('NWP_STADNING') == 'av'


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def huvudutcheckning(rot):
    """Huvudutcheckningen (den som äger .git) för en utcheckning eller en worktree."""
    rc, ut = vl.kor(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], timeout=30, cwd=rot, bara_ut=True)
    return Path(ut.strip()).parent.resolve() if rc == 0 and ut.strip() else Path(rot).resolve()


def npm_cache_katalog():
    rc, ut = vl.kor(['npm', 'config', 'get', 'cache', '--no-update-notifier'], timeout=60, bara_ut=True)
    v = (ut.strip().splitlines() or [''])[-1].strip() if rc == 0 else ''
    return Path(v) if v.startswith('/') else Path.home() / '.npm'


def disk_matt(p):
    """(totalt, ledigt) i byte för volymen där p ligger."""
    u = shutil.disk_usage(str(p))
    return u.total, u.free


def disk_post(total, ledigt):
    return {'totalt': int(total), 'ledigt': int(ledigt), 'andel_ledig': round(ledigt / total, 4) if total else None}


def storlek_text(n):
    if n is None:
        return '–'
    n = float(n)
    for enhet in ('B', 'kB', 'MB', 'GB', 'TB'):
        if n < 1024 or enhet == 'TB':
            return ('%d B' % n) if enhet == 'B' else ('%.1f %s' % (n, enhet)).replace('.', ',')
        n /= 1024
    return '–'


def disk_text(d):
    """'10,5 % ledigt (24,0 GB av 228,3 GB)', eller 'okänt'."""
    if not d or d.get('andel_ledig') is None:
        return 'okänt'
    return '%s %% ledigt (%s av %s)' % (('%.1f' % (d['andel_ledig'] * 100)).replace('.', ','), storlek_text(d['ledigt']),
                                       storlek_text(d['totalt']))


def antal_text(antal):
    return ', '.join('%s: %d' % (u, antal[u]) for u in UTFALL if antal.get(u)) or 'inget att städa'


class Ram:
    """Städningens omvärld: rötterna, klockan, diskmåttet, processlistan, stoppet, npm och om något pågår. Provet ger
    egna; verklig() ger maskinens."""

    def __init__(self, repo, repos_rot, tmp_rot, scratch_rot, npm_cache, tillstand, klocka=time.time, disk=None,
                 processer=None, stoppa=None, npm=None, upptagen=None, torr=False, vanta_stopp=5.0, skyddade=()):
        self.repo = Path(os.path.realpath(repo))
        self.repos_rot = Path(os.path.realpath(repos_rot))
        self.tmp_rot = Path(os.path.realpath(tmp_rot)) if tmp_rot else None
        self.scratch_rot = Path(os.path.realpath(scratch_rot)) if scratch_rot else None
        self.npm_cache = Path(npm_cache) if npm_cache else None
        self.tillstand = Path(tillstand) if tillstand else None
        self.klocka = klocka
        self.disk = disk or (lambda: disk_matt(self.repos_rot))
        self.processer = processer or las_processer
        self.stoppa = stoppa or (lambda pid: os.kill(pid, signal.SIGTERM))
        self.npm = npm or npm_rensa
        self.upptagen = upptagen or upptaget
        self.torr = torr
        self.vanta_stopp = vanta_stopp
        # raderas aldrig, och inget som innehåller dem: huvudutcheckningens underlag/ och kunder/ och ~/Arkiv
        self.skyddade = [self.repo / 'underlag', self.repo / 'kunder', Path.home() / 'Arkiv'] + [Path(p) for p in skyddade]

    @classmethod
    def verklig(cls, tillstand=None, torr=False):
        """Maskinens rötter: huvudutcheckningen bakom den här utcheckningen, ~/nortropic-repos (dess förälder), /tmp,
        scratchpad (/private/tmp/claude-<uid>) och npm:s cache; läget i underhållets katalog."""
        repo = huvudutcheckning(vl.ROOT)
        tmp = Path(os.path.realpath('/tmp'))
        return cls(repo=repo, repos_rot=repo.parent, tmp_rot=tmp, scratch_rot=tmp / ('claude-%d' % os.getuid()),
                   npm_cache=npm_cache_katalog(), tillstand=tillstand or repo / 'underlag' / 'startkontroll', torr=torr)

    def rotar(self):
        return [x for x in (self.repos_rot, self.tmp_rot, self.scratch_rot) if x]


# --- processerna ---

def las_processer():
    """Maskinens processer: [{pid, ppid, uid, lstart, start, kommando, cwd, filer, cwd_kand}], eller None när ps inte
    svarar. ps med LC_ALL=C och TZ=UTC som korregister.ps, så att starttiden är densamma som korregister.startad() ger
    (identiteten prövas före ett stopp). Arbetskatalogen och de öppna filerna ur lsof (-n -P: inga namnuppslag). Går lsof
    inte att läsa alls är cwd_kand False för användarens processer, och då räknas varje sökväg som använd."""
    try:
        r = subprocess.run(['ps', '-A', '-o', 'pid=,ppid=,uid=,lstart=,command='], capture_output=True, text=True, timeout=30,
                           encoding='utf-8', errors='replace', env=dict(os.environ, LC_ALL='C', TZ='UTC'))
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    ut = {}
    for rad in r.stdout.splitlines():
        d = rad.split(None, 8)
        if len(d) < 8 or not (d[0].isdigit() and d[1].isdigit() and d[2].isdigit()):
            continue
        lstart = ' '.join(d[3:8])
        try:
            start = datetime.strptime(lstart, '%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            start = None
        ut[int(d[0])] = {'pid': int(d[0]), 'ppid': int(d[1]), 'uid': int(d[2]), 'lstart': lstart, 'start': start,
                         'kommando': d[8] if len(d) > 8 else '', 'cwd': None, 'filer': [], 'cwd_kand': True}
    try:
        lsof = subprocess.run(['lsof', '-n', '-P', '-u', str(os.getuid()), '-Fpfn'], capture_output=True, text=True, timeout=120,
                              encoding='utf-8', errors='replace').stdout
    except (OSError, subprocess.SubprocessError):
        lsof = ''
    if not lsof.strip():  # lsof svarar inte: användarens processer kan ha arbetskatalogen var som helst
        for x in ut.values():
            if x['uid'] == os.getuid():
                x['cwd_kand'] = False
        return list(ut.values())
    pid, fd = None, None
    for rad in lsof.splitlines():
        if rad[:1] == 'p':
            pid, fd = (int(rad[1:]) if rad[1:].isdigit() else None), None
        elif rad[:1] == 'f':
            fd = rad[1:]
        elif rad[:1] == 'n' and pid in ut:
            if fd == 'cwd':
                ut[pid]['cwd'] = rad[1:]
            else:
                ut[pid]['filer'].append(rad[1:])
    return list(ut.values())


def varianter(p):
    """p som den kan stå i lsof eller en kommandorad: given och upplöst, med och utan /private (macOS: /tmp och /var)."""
    ut = {str(p), os.path.realpath(p)}
    for x in list(ut):
        for utan, med in (('/tmp', '/private/tmp'), ('/var', '/private/var')):
            if x == med or x.startswith(med + '/'):
                ut.add(utan + x[len(med):])
            elif x == utan or x.startswith(utan + '/'):
                ut.add(med + x[len(utan):])
    return sorted(ut, key=len, reverse=True)


def inuti(sokvag, var):
    return bool(sokvag) and any(sokvag == v or sokvag.startswith(v.rstrip('/') + '/') for v in var)


def i_kommando(kommando, var):
    k = kommando or ''
    return any(v in k and re.search(re.escape(v) + r'(?=$|[/\s\'"`:;,=)])', k) for v in var)


def kort(kommando, n=80):
    return ' '.join(str(kommando or '').split())[:n]


class Anvandning:
    """Vad maskinens processer använder: arbetskataloger och öppna filer sorterade för uppslag (hundratals
    scratchpad-sessioner mot tiotusentals öppna filer), och kommandoraderna."""

    def __init__(self, processer):
        self.processer = processer
        self.okand = None
        if processer is None:
            self.okand = 'processerna kunde inte läsas (ps)'
        elif any(x.get('cwd_kand') is False for x in processer):
            self.okand = 'processernas arbetskataloger kunde inte läsas (lsof)'
        poster = []
        for x in processer or ():
            if x.get('cwd'):
                poster.append((x['cwd'], x, 'har sin arbetskatalog där'))
            for f in x.get('filer') or ():
                poster.append((f, x, 'har %s öppen' % f))
        poster.sort(key=lambda t: t[0])
        self.nycklar, self.poster = [t[0] for t in poster], poster

    def skal(self, p):
        """Skälet när en levande process använder p (arbetskatalog, öppen fil eller argument i eller under p), annars
        None. Kan processerna eller deras arbetskataloger inte läsas räknas p som använd."""
        if self.okand:
            return self.okand
        var = varianter(p)
        for v in var:
            i = bisect.bisect_left(self.nycklar, v)
            while i < len(self.nycklar) and self.nycklar[i].startswith(v):
                n = self.nycklar[i]
                if n == v or n[len(v)] == '/':
                    _n, x, vad = self.poster[i]
                    return 'pid %d %s (%s)' % (x['pid'], vad, kort(x.get('kommando')))
                i += 1
        for x in self.processer:
            if i_kommando(x.get('kommando'), var):
                return 'pid %d nämner den i sina argument (%s)' % (x['pid'], kort(x.get('kommando')))
        return None


def anvands(anv, p):
    """Skälet när en levande process använder p, annars None (Anvandning.skal; None som anv: processerna är okända)."""
    return (anv or Anvandning(None)).skal(p)


def serverslag(kommando):
    """'astro', 'http.server' eller 'dashboard' när kommandot är en förhandsvisning eller server ur punkt 3, annars None."""
    return next((namn for namn, m in SERVRAR if m.search(kommando or '')), None)


def agarens_dashboard(kommando, slag):
    """Ägarens dashboard (port 4771): dashboard/server.py utan --port eller med 4771, eller vad som helst med port 4771."""
    if AGARENS_PORT.search(kommando or ''):
        return True
    if slag == 'dashboard':
        m = PORT.search(kommando or '')
        return not m or int(m.group(1)) == DASHBOARD_PORT
    return False


def stoppa_process(ram, x):
    """SIGTERM, och väntar högst ram.vanta_stopp sekunder på att processen försvinner. Processens identitet (pid och
    starttid) prövas först: en pid som återanvänts av en annan process stoppas aldrig. Ger (utfall, skäl)."""
    def samma():
        return ' '.join(korregister.startad(x['pid']).split()) == x['lstart']
    if not korregister.lever(x['pid']) or not samma():
        return KVAR, 'processen finns inte längre (eller pid:en har återanvänts); inget stoppat'
    ram.stoppa(x['pid'])
    slut = time.time() + ram.vanta_stopp
    while time.time() < slut:
        status = korregister.ps('stat', x['pid'])
        if not status or status.startswith('Z') or not samma():
            return STOPPAD, None
        time.sleep(0.1)
    return FEL, 'lever %g s efter SIGTERM' % ram.vanta_stopp


# --- storlek, ändring och material ---

def andrad(s):
    """När posten senast ändrades: en fil eller symlänk den senare av mtime och ctime (en kopia med bevarade tider är ny
    fast mtime är gammal), en katalog när den skapades (st_birthtime). En katalogs mtime ändras också när något i den tas
    bort: i scratchpad flyttades mtime på gamla sessioners kataloger varje natt vid midnatt när filer i dem togs bort,
    fast birthtime och filerna var veckor gamla (sett 2026-10-06). En fils ctime flyttas också när en hårdlänk till den tas
    bort någon annanstans (git-objekt i en lokal klon); det gör bara att något står kvar längre."""
    if stat.S_ISDIR(s.st_mode):
        return getattr(s, 'st_birthtime', None) or s.st_mtime
    return max(s.st_mtime, s.st_ctime)


def matt(p):
    """(storlek i byte som du räknar dem, senaste ändring enligt andrad(), antal fel) för p och allt under den.
    Symlänkar följs aldrig: länken räknas, inte målet."""
    try:
        st = os.lstat(p)
    except OSError:
        return 0, 0.0, 1
    storlek, senast, fel = st.st_blocks * 512, andrad(st), 0
    if not stat.S_ISDIR(st.st_mode):
        return storlek, senast, fel
    stack = [str(p)]
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                for e in it:
                    try:
                        s = e.stat(follow_symlinks=False)
                    except OSError:
                        fel += 1
                        continue
                    storlek += s.st_blocks * 512
                    senast = max(senast, andrad(s))
                    if stat.S_ISDIR(s.st_mode):
                        stack.append(e.path)
        except OSError:
            fel += 1
    return storlek, senast, fel


def sha256_fil(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for bit in iter(lambda: f.read(1 << 20), b''):
            h.update(bit)
    return h.hexdigest()


def _kasta(e):
    raise e


def eget_material(kopia, repo):
    """[(relativ sökväg, storlek)] för filerna i kopians underlag/ och kunder/ som inte finns med samma relativa sökväg och
    samma innehåll (sha256) i huvudutcheckningen. node_modules, dist, .astro och __pycache__ är inget material, inte
    heller .DS_Store och flödets egna prov- och lägesdata (FLODETS_EGNA); symlänkar följs aldrig. Kastar OSError när något
    i kopian inte går att läsa: material som inte går att jämföra raderas aldrig."""
    kopia, repo, ut = Path(kopia), Path(repo), []
    for topp in ('underlag', 'kunder'):
        bas = kopia / topp
        if bas.is_symlink() or not bas.is_dir():
            continue
        for rot, mappar, filer in os.walk(bas, onerror=_kasta):
            rel_rot = Path(rot).relative_to(kopia)
            mappar[:] = [m for m in mappar if m not in INTE_MATERIAL and (rel_rot / m).as_posix() not in FLODETS_EGNA
                         and not os.path.islink(os.path.join(rot, m))]
            for f in filer:
                if f in INTE_MATERIAL_FILER:
                    continue
                p = Path(rot) / f
                st = os.lstat(p)
                if not stat.S_ISREG(st.st_mode):  # symlänkar och uttag är inget material
                    continue
                rel = (rel_rot / f).as_posix()
                try:
                    hs = os.stat(repo / rel)
                    lika = stat.S_ISREG(hs.st_mode) and hs.st_size == st.st_size and sha256_fil(repo / rel) == sha256_fil(p)
                except OSError:
                    lika = False
                if not lika:
                    ut.append((rel, st.st_size))
    return ut


def material_falt(eget):
    return {'material': [{'sokvag': r, 'storlek': s} for r, s in eget[:MATERIAL_MAX]], 'material_antal': len(eget),
            'material_storlek': sum(s for _r, s in eget)}


def material_kort(eget, n=5):
    return ', '.join('%s (%s)' % (r, storlek_text(s)) for r, s in eget[:n]) + (' och %d till' % (len(eget) - n) if len(eget) > n else '')


def far_inte_raderas(ram, p):
    """Skälet när p aldrig får raderas, annars None: en symlänk, huvudutcheckningen eller något som innehåller den,
    huvudutcheckningens underlag/ och kunder/ eller något i dem, ~/Arkiv, en rot eller något utanför rötterna."""
    p = Path(p)
    if p.is_symlink():
        return 'en symlänk'
    r = Path(os.path.realpath(p))
    if r == ram.repo or r in ram.repo.parents:
        return 'huvudutcheckningen'
    for s in ram.skyddade:
        s = Path(os.path.realpath(s))
        if r == s or s in r.parents or r in s.parents:
            return 'skyddad (%s)' % s
    if not any(x in r.parents for x in ram.rotar()):
        return 'utanför städregelns rötter'
    return None


def radera(ram, p):
    """None, eller felet. Bara inom rötterna och aldrig det skyddade (far_inte_raderas); symlänkar följs aldrig."""
    skal = far_inte_raderas(ram, p)
    if skal:
        return 'raderas aldrig: %s' % skal
    fel = []
    if sys.version_info >= (3, 12):
        shutil.rmtree(p, onexc=lambda f, s, e: fel.append('%s: %s' % (s, e)))
    else:
        shutil.rmtree(p, onerror=lambda f, s, e: fel.append('%s: %s' % (s, e[1])))
    return '; '.join(fel[:3]) if fel else None


# --- git ---

def git(*a, cwd, timeout=120, bara_ut=False):
    return vl.kor(['git', *a], timeout=timeout, cwd=cwd, bara_ut=bara_ut)


def worktrees(ram):
    """De registrerade worktrees utom huvudutcheckningen (git worktree list --porcelain): [{sokvag, head, gren, last,
    saknas}], eller None när git inte svarar."""
    rc, ut = git('worktree', 'list', '--porcelain', cwd=ram.repo, bara_ut=True)
    if rc != 0:
        return None
    alla, cur = [], None
    for rad in ut.splitlines() + ['']:
        if rad.startswith('worktree '):
            cur = {'sokvag': Path(rad[len('worktree '):]), 'head': None, 'gren': None, 'last': None, 'saknas': False, 'bar': False}
        elif cur is None:
            continue
        elif rad.startswith('HEAD '):
            cur['head'] = rad[5:].strip()
        elif rad.startswith('branch '):
            cur['gren'] = rad[7:].strip()
        elif rad == 'bare':
            cur['bar'] = True
        elif rad.startswith('locked'):
            cur['last'] = rad[6:].strip() or 'utan skäl'
        elif rad.startswith('prunable'):
            cur['saknas'] = True
        elif not rad.strip():
            alla.append(cur)
            cur = None
    return [w for w in alla if not w['bar'] and Path(os.path.realpath(w['sokvag'])) != ram.repo]


def i_main(ram, ref):
    """(sammanslagen i main, finns i origin/main) för en gren eller commit."""
    def forfader(m):
        return git('merge-base', '--is-ancestor', ref, m, cwd=ram.repo)[0] == 0
    return forfader('refs/heads/main'), forfader('refs/remotes/origin/main')


def admin_katalog(wt):
    """Worktreens administrativa katalog i huvudutcheckningens .git (ur .git-filen), eller None."""
    try:
        t = (Path(wt) / '.git').read_text(encoding='utf-8')
    except OSError:
        return None
    return Path(t.split('gitdir:', 1)[1].strip()) if 'gitdir:' in t else None


def egna_commits(ram, d):
    """Det i en kopias eget git som inte finns kvar i huvudutcheckningen: ocommittade ändringar, och grenar, taggar och
    stash vars commit ingen ref i huvudutcheckningen innehåller. [] när allt finns där."""
    rc, st = git('--no-optional-locks', 'status', '--porcelain', cwd=d, bara_ut=True)
    if rc:
        return ['git status svarade inte i kopian']
    ut = ['ocommittad ändring: %s' % r[3:] for r in st.splitlines() if r.strip()][:10]
    rc, refs = git('for-each-ref', '--format=%(objectname) %(refname:short)', 'refs/heads', 'refs/tags', 'refs/stash', cwd=d, bara_ut=True)
    if rc:
        return ut + ['kopians grenar gick inte att läsa']
    for rad in refs.splitlines():
        sha, _, namn = rad.partition(' ')
        rc, inne = git('for-each-ref', '--contains', sha, '--count=1', '--format=%(refname)', cwd=ram.repo, bara_ut=True)
        if rc or not inne.strip():
            ut.append('egen commit: %s %s' % (namn, sha[:12]))
    return ut


# --- punkterna ---

class Redovisning:
    """Punkt 7: varje åtgärd med vad, sökväg, storlek före, tid (UTC, ur klockan), utfall och skäl."""

    def __init__(self, ram):
        self.ram, self.poster = ram, []

    def post(self, punkt, vad, sokvag, storlek, utfall, skal, **f):
        if self.ram.torr:
            utfall = TORRT.get(utfall, utfall)
        p = {'punkt': punkt, 'vad': vad, 'sokvag': str(sokvag) if sokvag is not None else None, 'storlek_fore': storlek,
             'tid': iso(self.ram.klocka()), 'utfall': utfall, 'skal': skal}
        p.update({k: v for k, v in f.items() if v is not None})
        self.poster.append(p)
        return p


def kopior(ram, wts):
    """[(katalog, med repots kännetecken)] direkt under ~/nortropic-repos: namnet börjar med kopia (eller <namn>-kopia),
    eller katalogen har repots kännetecken (kor.sh och kontroller/), och den är varken huvudutcheckningen eller en
    registrerad worktree. Dolda kataloger och annat som ägaren lagt där rörs inte."""
    kanda = {Path(os.path.realpath(w['sokvag'])) for w in wts}
    ut = []
    try:
        innehall = sorted(ram.repos_rot.iterdir())
    except OSError:
        return []
    for d in innehall:
        if d.name.startswith('.') or d.is_symlink() or not d.is_dir():
            continue
        r = Path(os.path.realpath(d))
        if r == ram.repo or r in kanda:
            continue
        kannetecken = (d / 'kor.sh').is_file() and (d / 'kontroller').is_dir()
        if kannetecken or re.match(r'(?i)(?:.*-)?kopia', d.name):
            ut.append((d, kannetecken))
    return ut


def bedom_worktree(ram, w, anv, senast, mfel):
    """(utfall, skäl, fält) för en registrerad worktree; RADERAD betyder att den får tas bort. senast och mfel ur matt(),
    mätta innan något git-kommando körts i den."""
    p = w['sokvag']
    gren = w['gren'][len('refs/heads/'):] if (w['gren'] or '').startswith('refs/heads/') else w['gren']
    if w['saknas'] or not p.is_dir():
        return KVAR, 'katalogen finns inte längre; registreringen tas bort med git worktree prune', {}
    skal = far_inte_raderas(ram, p)
    if skal:
        return KVAR, 'rörs inte: %s' % skal, {}
    if Path(os.path.realpath(p)) == Path(os.path.realpath(vl.ROOT)):
        return KVAR, 'städningen körs från den här utcheckningen', {}
    if w['last']:
        return KVAR, 'låst med git worktree lock (%s)' % w['last'], {}
    ref = w['gren'] or w['head']
    if not ref:
        return KVAR, 'varken gren eller HEAD i git worktree list', {}
    vem = ('grenen %s' % gren) if gren else ('den frånkopplade HEAD %s' % (w['head'] or '?')[:12])
    imain, iorigin = i_main(ram, ref)
    if not imain:
        return KVAR, '%s är inte sammanslagen i main' % vem, {}
    if not iorigin:
        return KVAR, '%s är sammanslagen i main men inte pushad (finns inte i origin/main)' % vem, {}
    adm = admin_katalog(p)
    if adm:
        senast = max(senast, matt(adm)[1])
    rc, st = git('--no-optional-locks', 'status', '--porcelain', cwd=p, bara_ut=True)
    if rc:
        return KVAR, 'git status svarade inte', {}
    andrade = [r[3:] for r in st.splitlines() if r.strip()]
    if andrade:
        return KVAR, 'ocommittade ändringar (%d): %s' % (len(andrade), ', '.join(andrade[:5])), {}
    a = anvands(anv, p)
    if a:
        return KVAR, 'används: %s' % a, {}
    if mfel:
        return KVAR, '%d sökvägar gick inte att läsa; ändringstiden är okänd' % mfel, {}
    if ram.klocka() - senast <= AKTIV:
        return KVAR, 'ändrad det senaste dygnet (%s): arbetet kan pågå' % iso(senast), {}
    try:
        eget = eget_material(p, ram.repo)
    except OSError as e:
        return VANTAR, 'underlag/ och kunder/ går inte att jämföra med huvudutcheckningen (%s); ägaren avgör' % e, {}
    if eget:
        return VANTAR, '%s är sammanslagen och pushad, men underlag/ och kunder/ har %d filer (%s) som inte finns i ' \
                       'huvudutcheckningen: %s; ägaren avgör' % (vem, len(eget), storlek_text(sum(s for _r, s in eget)),
                                                                 material_kort(eget)), material_falt(eget)
    return RADERAD, '%s är sammanslagen i main och pushad; tas bort med git worktree remove, grenen och dess commits ' \
                    'finns kvar' % vem, {}


def punkt1(ram, red, wts, anv):
    """Worktrees som är sammanslagna och pushade tas bort med git worktree remove (aldrig --force)."""
    if wts is None:
        red.post(1, 'worktree', ram.repo, None, KVAR, 'git worktree list svarade inte; inga worktrees tas bort')
        return
    for w in wts:
        p = w['sokvag']
        gren = (w['gren'] or '').replace('refs/heads/', '') or None
        storlek, senast, mfel = matt(p) if p.is_dir() else (None, 0.0, 0)
        utfall, skal, falt = bedom_worktree(ram, w, anv, senast, mfel)
        if utfall == RADERAD and not ram.torr:
            rc, ut = git('worktree', 'remove', str(p), cwd=ram.repo)  # aldrig --force: en smutsig worktree står kvar
            if rc:
                utfall, skal = FEL, 'git worktree remove föll, inget raderat: %s' % vl.sista(ut, 240)
            elif gren and git('rev-parse', '--verify', '-q', 'refs/heads/' + gren, cwd=ram.repo)[0] != 0:
                utfall, skal = FEL, 'worktreen togs bort, men grenen %s finns inte längre' % gren
        red.post(1, 'worktree', p, storlek, utfall, skal, gren=gren, **falt)


def punkt2(ram, red, kop, anv):
    """Kopior av repot: utan eget material raderas de; med eget material väntar de på ägaren, med listan."""
    for d, kannetecken in kop:
        storlek, senast, mfel = matt(d)
        if not kannetecken:
            red.post(2, 'kopia', d, storlek, VANTAR, 'okänt ursprung: heter kopia men saknar repots kännetecken (kor.sh och '
                                                     'kontroller/); ägaren avgör')
            continue
        a = anvands(anv, d)
        if a:
            red.post(2, 'kopia', d, storlek, KVAR, 'används: %s' % a)
            continue
        if mfel:
            red.post(2, 'kopia', d, storlek, VANTAR, '%d sökvägar gick inte att läsa; kopian går inte att jämföra, ägaren avgör' % mfel)
            continue
        if ram.klocka() - senast <= AKTIV:
            red.post(2, 'kopia', d, storlek, KVAR, 'ändrad det senaste dygnet (%s): provet kan pågå' % iso(senast))
            continue
        if (d / '.git').is_file():
            red.post(2, 'kopia', d, storlek, VANTAR, 'en worktree som inte är registrerad i repot (.git är en fil): ocommittade '
                                                     'ändringar går inte att se; ägaren avgör')
            continue
        if (d / '.git').is_dir():
            egna = egna_commits(ram, d)
            if egna:
                red.post(2, 'kopia', d, storlek, VANTAR, 'kopians eget git har det som inte finns i huvudutcheckningen: %s; ägaren '
                                                         'avgör' % '; '.join(egna[:6]))
                continue
        try:
            eget = eget_material(d, ram.repo)
        except OSError as e:
            red.post(2, 'kopia', d, storlek, VANTAR, 'underlag/ och kunder/ går inte att jämföra med huvudutcheckningen (%s); '
                                                     'ägaren avgör' % e)
            continue
        if eget:
            red.post(2, 'kopia', d, storlek, VANTAR, 'eget material i underlag/ och kunder/ som inte finns i huvudutcheckningen: '
                                                     '%d filer (%s): %s; ägaren avgör' % (
                                                         len(eget), storlek_text(sum(s for _r, s in eget)), material_kort(eget)),
                     **material_falt(eget))
            continue
        fel = None if ram.torr else radera(ram, d)
        red.post(2, 'kopia', d, storlek, FEL if fel else RADERAD,
                 ('raderingen föll: %s' % fel) if fel else 'inget eget material i underlag/ och kunder/ (jämfört med '
                                                           'huvudutcheckningen), ingen process och inga egna commits')


def punkt3(ram, red, wts, kop, processer):
    """Förhandsvisningar och servrar inom räckvidden, utan levande förälder och äldre än ett dygn, stoppas med SIGTERM.
    Ger pid:arna som stoppades (eller skulle stoppas i torrläget)."""
    if processer is None:
        red.post(3, 'process', None, None, KVAR, 'processerna kunde inte läsas (ps); inget stoppat')
        return set()
    rotar = [Path(os.path.realpath(w['sokvag'])) for w in wts or []] + [Path(os.path.realpath(d)) for d, k in kop if k] + \
            [x for x in (ram.tmp_rot, ram.scratch_rot) if x]
    rot_var = [varianter(r) for r in rotar]
    stoppade = set()
    for x in processer:
        slag = serverslag(x.get('kommando'))
        if not slag or not x.get('cwd') or not any(inuti(x['cwd'], v) for v in rot_var):
            continue  # inte en server, eller utanför räckvidden: lämnas och redovisas inte
        falt = {'pid': x['pid'], 'kommando': kort(x['kommando'], 160)}
        vem = 'pid %d, %s' % (x['pid'], kort(x['kommando']))
        if agarens_dashboard(x['kommando'], slag):
            red.post(3, 'process', x['cwd'], None, KVAR, '%s: ägarens dashboard (port 4771) stoppas aldrig' % vem, **falt)
            continue
        if x.get('ppid') != 1:
            red.post(3, 'process', x['cwd'], None, KVAR, '%s: föräldern lever (pid %s)' % (vem, x.get('ppid')), **falt)
            continue
        alder = ram.klocka() - x['start'] if x.get('start') else None
        if alder is None or alder <= PROCESS_ALDER:
            red.post(3, 'process', x['cwd'], None, KVAR, '%s: utan förälder men yngre än ett dygn (startad %s)' % (
                vem, iso(x['start']) if x.get('start') else '?'), **falt)
            continue
        skal = '%s (%s): utan levande förälder, startad %s' % (vem, slag, iso(x['start']))
        if ram.torr:
            red.post(3, 'process', x['cwd'], None, STOPPAD, skal + '; SIGTERM', **falt)
            stoppade.add(x['pid'])
            continue
        utfall, fel = stoppa_process(ram, x)
        if utfall == STOPPAD:
            stoppade.add(x['pid'])
        red.post(3, 'process', x['cwd'], None, utfall, skal + ('; ' + fel if fel else '; stoppad med SIGTERM'), **falt)
    return stoppade


def punkt4(ram, red, anv):
    """Gamla kataloger i /tmp med repots prefix och gamla scratchpad-sessioner, när ingen process använder dem."""
    if ram.tmp_rot and ram.tmp_rot.is_dir():
        for d in sorted(ram.tmp_rot.iterdir()):
            n = d.name
            if n in ALDRIG_TMP or n.startswith(ALDRIG_TMP_PREFIX) or not n.startswith(TMP_PREFIX) or d.is_symlink() or not d.is_dir():
                continue
            stada_katalog(ram, red, d, anv, TMP_ALDER, 'tillfällig katalog', 'repots prefix %s, inte ändrad på ett dygn' % next(
                x for x in TMP_PREFIX if n.startswith(x)))
    if ram.scratch_rot and ram.scratch_rot.is_dir():
        for projekt in sorted(ram.scratch_rot.iterdir()):
            if not projekt.name.startswith('-') or projekt.is_symlink() or not projekt.is_dir():
                continue
            for s in sorted(projekt.iterdir()):
                if SESSION.fullmatch(s.name) and not s.is_symlink() and s.is_dir():
                    stada_katalog(ram, red, s, anv, SCRATCH_ALDER, 'scratchpad', 'en sessions scratchpad, inte ändrad på sju dygn')


def stada_katalog(ram, red, d, anv, alder, vad, varfor):
    storlek, senast, mfel = matt(d)
    if mfel:
        red.post(4, vad, d, storlek, KVAR, '%d sökvägar gick inte att läsa; ändringstiden är okänd' % mfel)
        return
    if ram.klocka() - senast <= alder:
        return  # ung: lämnas och redovisas inte
    a = anvands(anv, d)
    if a:
        red.post(4, vad, d, storlek, KVAR, 'används: %s' % a)
        return
    fel = None if ram.torr else radera(ram, d)
    red.post(4, vad, d, storlek, FEL if fel else RADERAD, ('raderingen föll: %s' % fel) if fel else '%s (senast %s), ingen process' % (
        varfor, iso(senast)))


def punkt5(ram, red):
    """npm-cachen: över 85 % fylld disk, eller förra rensningen äldre än 30 dygn."""
    if not ram.npm_cache:
        red.post(5, 'npm-cachen', None, None, KVAR, 'npm:s cache hittades inte')
        return
    cacache = ram.npm_cache / '_cacache'
    storlek = matt(cacache)[0] if cacache.exists() else 0
    total, ledigt = ram.disk()
    fylld = 1 - ledigt / total if total else 0
    lage = (vl.las_json(ram.tillstand / NPM_LAGE, {}) or {}) if ram.tillstand else {}
    senast = lage.get('tid')
    sedan = ram.klocka() - vl.iso_s(senast) if senast and vl.iso_s(senast) else None
    fylld_text = ('%.1f' % (fylld * 100)).replace('.', ',')
    if fylld > NPM_FYLLD:
        skal = 'disken är fylld till %s %% (över 85 %%)' % fylld_text
    elif sedan is None:
        skal = 'disken är fylld till %s %%, och ingen tidigare rensning är registrerad (en gång i månaden)' % fylld_text
    elif sedan > NPM_INTERVALL:
        skal = 'disken är fylld till %s %%; förra rensningen %s, %d dygn sedan (en gång i månaden)' % (fylld_text, senast, sedan // DYGN)
    else:
        red.post(5, 'npm-cachen', cacache, storlek, KVAR, 'disken är fylld till %s %% (under 85 %%); förra rensningen %s, %d dygn '
                                                         'sedan' % (fylld_text, senast, sedan // DYGN))
        return
    hinder = ram.upptagen()
    if hinder:
        red.post(5, 'npm-cachen', cacache, storlek, KVAR, '%s, men %s: rensas vid nästa städning' % (skal, hinder))
        return
    if ram.torr:
        red.post(5, 'npm-cachen', cacache, storlek, RENSAD, skal + '; npm cache clean --force')
        return
    rc, ut = ram.npm(ram.npm_cache)
    if rc:
        red.post(5, 'npm-cachen', cacache, storlek, FEL, '%s, men npm cache clean föll: %s' % (skal, vl.sista(ut, 200)))
        return
    tid = iso(ram.klocka())
    try:
        vl.skriv_json(ram.tillstand / NPM_LAGE, {'tid': tid, 'storlek_fore': storlek, 'skal': skal})
    except (OSError, TypeError) as e:
        skal += '; tiden kunde inte sparas (%s)' % e
    red.post(5, 'npm-cachen', cacache, storlek, RENSAD, skal + '; npm cache clean --force')


def npm_rensa(cache):
    return vl.kor(['npm', 'cache', 'clean', '--force', '--no-update-notifier', '--cache', str(cache)], timeout=900)


def upptaget():
    """Skälet när en körning (körregistret och ateljén) eller en npm-installation pågår, annars None."""
    p = vl.pagaende()
    if p:
        return 'en körning pågår (%s)' % ', '.join(p)
    import underhall
    return underhall.npm_installerar()


def stada(ram, punkter=(1, 2, 3, 4, 5)):
    """Punkterna i ordningen 3, 1, 2, 4 och 5 (en gammal förhandsvisning stoppas före kopian den håller), och
    redovisningen. En punkt som faller stoppar inte de andra."""
    red = Redovisning(ram)
    rap = {'schema': 1, 'start': iso(ram.klocka()), 'torr': ram.torr, 'disk_fore': None, 'disk_efter': None}
    try:
        rap['disk_fore'] = disk_post(*ram.disk())
    except OSError as e:
        rap['disk_fel'] = str(e)

    def steg(punkt, vad, f):
        if punkt not in punkter:
            return None
        try:
            return f()
        except Exception as e:  # noqa: BLE001 — en punkt som faller redovisas och stoppar inte de andra
            red.post(punkt, vad, None, None, FEL, 'punkten föll: %s: %s' % (type(e).__name__, vl.sista(e, 200)))
            return None

    behov = set(punkter)
    wts, kop, processer = [], [], []
    if behov & {1, 2, 3}:
        try:
            wts = worktrees(ram)
        except Exception:  # noqa: BLE001 — okända worktrees: punkt 1 och 2 rör då ingenting
            wts = None
    # utan listan över worktrees går en worktree inte att skilja från en kopia: då rörs inga kopior
    if behov & {2, 3} and wts is not None:
        kop = kopior(ram, wts)
    if behov & {1, 2, 3, 4}:
        try:
            processer = ram.processer()
        except Exception:  # noqa: BLE001 — okända processer: allt räknas som använt
            processer = None
    stoppade = steg(3, 'process', lambda: punkt3(ram, red, wts, kop, processer)) or set()
    if stoppade:  # det de stoppade använde är fritt (i torrläget: som om de stoppats)
        if ram.torr:
            processer = [x for x in processer or [] if x['pid'] not in stoppade]
        else:
            try:
                processer = ram.processer()
            except Exception:  # noqa: BLE001
                processer = None
    anv = Anvandning(processer)
    steg(1, 'worktree', lambda: punkt1(ram, red, wts, anv))
    if 2 in behov and wts is None:
        red.post(2, 'kopia', ram.repos_rot, None, KVAR, 'worktrees okända (git worktree list svarade inte): inga kopior rörs')
    steg(2, 'kopia', lambda: punkt2(ram, red, kop, anv))
    steg(4, 'tillfällig katalog', lambda: punkt4(ram, red, anv))
    steg(5, 'npm-cachen', lambda: punkt5(ram, red))
    try:
        rap['disk_efter'] = disk_post(*ram.disk())
    except OSError:
        pass
    rap['slut'] = iso(ram.klocka())
    rap['poster'] = red.poster
    rap['antal'] = {}
    for p in red.poster:
        rap['antal'][p['utfall']] = rap['antal'].get(p['utfall'], 0) + 1
    return rap


def markdown(rap, rubrik='## Städningen'):
    """Redovisningen (punkt 7) som rader: i underhållets rapport, i startkvittot och i torrläget."""
    if not rap:
        return []
    ut = [rubrik, '']
    if rap.get('avslagen'):
        return ut + ['Avslagen mot det verkliga systemet (NWP_STADNING=av).', '']
    if rap.get('fel'):
        return ut + ['**Städningen föll:** %s. Underhållet fortsatte.' % rap['fel'], '']
    ut += ['%sStädregeln i BESLUT.md (2026-10-06), %s–%s. Disken: %s före, %s efter. %s.' % (
        '**Torrläge: inget ändrat.** ' if rap.get('torr') else '', rap.get('start'), rap.get('slut'), disk_text(rap.get('disk_fore')),
        disk_text(rap.get('disk_efter')), antal_text(rap.get('antal') or {})), '']
    if rap.get('poster'):
        ut += ['| Punkt | Vad | Sökväg | Storlek före | Tid | Utfall | Skäl |', '|---|---|---|---|---|---|---|']
        for p in rap['poster']:
            ut.append('| %s | %s | %s | %s | %s | %s | %s |' % (p['punkt'], p['vad'], ('`%s`' % p['sokvag']) if p.get('sokvag') else '–',
                                                               storlek_text(p.get('storlek_fore')), p['tid'],
                                                               p['utfall'].upper() if p['utfall'] in (FEL, VANTAR) else p['utfall'],
                                                               str(p['skal']).replace('|', '/').replace('\n', ' ')))
    vantar = [p for p in rap.get('poster') or [] if p['utfall'] == VANTAR]
    if vantar:
        ut += ['', '**Väntar på ägaren** (raderas inte förrän ägaren avgjort):', '']
        for p in vantar:
            ut.append('- `%s` (%s): %s' % (p['sokvag'], storlek_text(p.get('storlek_fore')), p['skal']))
            for m in (p.get('material') or [])[:20]:
                ut.append('  - `%s` (%s)' % (m['sokvag'], storlek_text(m['storlek'])))
            if (p.get('material_antal') or 0) > 20:
                ut.append('  - och %d filer till (%s sammanlagt)' % (p['material_antal'] - 20, storlek_text(p.get('material_storlek'))))
    return ut + ['']


def main(argv=None):
    p = argparse.ArgumentParser(prog='stadning', description=__doc__.split('\n\n')[0])
    p.add_argument('--torr', action='store_true', help='listar bara: inget raderas, stoppas eller rensas')
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    if not a.torr and avslagen():
        print('städningen är avslagen (NWP_STADNING=av)')
        return 0
    rap = stada(Ram.verklig(torr=a.torr))
    print(json.dumps(rap, ensure_ascii=False, indent=1) if a.json else '\n'.join(markdown(rap, '# Städning · %s' % rap['start'])))
    return 1 if (rap.get('antal') or {}).get(FEL) else 0


if __name__ == '__main__':
    sys.exit(main())
