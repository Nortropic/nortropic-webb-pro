#!/usr/bin/env python3
"""stadning.py — städregeln för arbetskopior, processer och cacher (ägarens beslut 2026-10-06 ~14:35Z, delvis ersatt samma
dag: ingenting arkiveras, skrot raderas, och det som verkar värdefullt raderas inte utan väntar på ägaren; ordagrant i
BESLUT.md, avsnittet "Tillägg 2026-10-06: städregel för arbetskopior, processer och cacher"). Det dagliga underhållet
(kontroller/underhall.py) städar vid varje körning och skriver redovisningen i sin rapport; startkontrollens diskvakt
(kontroller/startkontroll.py, punkt 6) städar före starten när disken har under 15 % ledigt och skriver redovisningen i
samma rapport. Går också att köra själv:

    .venv/bin/python kontroller/stadning.py [--torr] [--json]

Räckvidden är bara det flödet och agenterna skapat under ~/nortropic-repos, /tmp (/private/tmp och macOS tempkatalog,
$TMPDIR) och scratchpad (/private/tmp/claude-<uid>). Huvudutcheckningen är alltid ~/nortropic-repos/nortropic-webb-pro
(HUVUDUTCHECKNING) med sina registrerade worktrees. Den rörs aldrig, inte heller underlag/ och kunder/ i den, det den
länkar till, ~/Arkiv eller det ägaren skapat, och dashboarden på port 4771 stoppas aldrig. Körs städningen från något
annat än huvudutcheckningen eller en av dess worktrees (till exempel ur en full kopia med eget .git) städas ingenting:
allt redovisas bara (granskningen av r94, B1). Det en levande process använder (arbetskatalog, öppen fil eller
argument) lämnas, och det prövas igen direkt före varje radering.

1. Worktrees: en registrerad worktree vars gren fått egna commits, är sammanslagen i main och finns i origin/main, utan
   ocommittade ändringar, utan eget material och utan ändringar det senaste dygnet, tas bort med git worktree remove,
   aldrig --force. Grenen och dess commits finns kvar. En gren som aldrig fått en egen commit är okänd (en session kan
   vänta på den) och väntar på ägaren efter ett dygn. Misslyckas borttagningen redovisas felet.
2. Kopior av repot: bara kataloger vars namn tydligt är en kopia (kopia* och <namn>-kopia…), aldrig huvudutcheckningen
   eller en worktree, inte heller via realpath eller en symlänk. En kopia utan eget material, utan egna commits och utan
   ändringar det senaste dygnet raderas; med eget material väntar den på ägaren, med listan (sökväg och storlek). En
   katalog med repots kännetecken som inte heter kopia rörs inte, utan väntar på ägaren.
3. Processer: förhandsvisningar och servrar (astro preview och dev, python -m http.server, dashboards på andra portar än
   4771) med arbetskatalog i en worktree, en kopia, en av flödets kataloger i /tmp och $TMPDIR (nwp-* och repots
   tempprefix) eller scratchpad, utan levande förälder (ppid 1) och äldre än ett dygn, stoppas med SIGTERM, när pid och
   starttid fortfarande är processens. Allt annat lämnas. Punkten körs först, så att en kopia som en gammal
   förhandsvisning höll kan städas i samma körning.
4. Tillfälliga filer (villkoren delvis ersatta av ägarens beslut 2026-10-07, BESLUT.md: bara det som är registrerat som
   eget, inte prefixet): en katalog direkt i /tmp och $TMPDIR med repots prefix (TMP_PREFIX) raderas bara när den är
   registrerad som en körnings egen (ägarfilen ur korregister.egen_tmp, giltig enligt korregister.tmp_agare), körningen
   som äger den är avslutad (korregister.tmp_avslutad), den inte ändrats på ett dygn och ingen process använder den. En
   katalog med prefixet men utan giltig registrering är en äldre rest: den raderas aldrig, utan redovisas för sig med
   sökväg, storlek och ålder ("äldre rest, väntar på identifiering"). Scratchpads sessionskataloger
   (<projekt>/<session>/) som inte ändrats på sju dygn raderas när ingen process använder dem och varje vanlig fil i
   dem, oavsett ändelse, redan är beständigt registrerad eller går att återskapa (oregistrerade, Kvitton: sha256 i
   underlag/granskningar/FORTECKNING.jsonl, ett VERSION.json eller ett omtags KVITTO.json, med filen kvar i
   underlag/, eller en blob som nås från en ref i huvudutcheckningens git); bara node_modules/, __pycache__/ och en
   riktig venvs egna kataloger undantas. Annars väntar arbetsytan på ägaren med listan över filerna. En sessions scratchpad rörs bara
   när ingen process nämner sessionens id (argument eller öppen fil), ingen claude-process med okänt sessions-id hör
   till samma projekt och transkriptet inte ändrats på sju dygn: när det är oklart står den kvar. Ingen symlänk följs
   (lstat, os.walk med followlinks=False och shutil.rmtree med filbeskrivare; en länk i en katalog som raderas tas bort
   som länk, och dess mål rörs inte), och bara katalogen själv raderas: aldrig /tmp, $TMPDIR, scratchpads rot eller en annan gemensam förälder
   (far_inte_raderas, direkt_under). En scratchpad-rot som är en symlänk följs inte alls.
5. npm-cachen: npm cache clean --force när disken är fylld över 85 %, annars när förra rensningen är äldre än 30 dygn
   (tiden i underhållets läge, NPM-CACHE.json). Aldrig medan en körning, ett underhåll, ett intag eller en
   npm-installation pågår. npm avgör själv vilken cache den rensar; sökvägen och storleken i redovisningen är en
   uppskattning.
7. Redovisningen: varje åtgärd med vad, sökväg, storlek före, tid (UTC, ur klockan), utfall och skäl.

Eget material (punkt 1 och 2) är varje fil i kopian eller worktreen som inte går att återskapa: allt utom .git, det
härledda (node_modules och __pycache__ var som helst, dist och .astro bredvid en package.json), rökprovets fixtur
(kunder/ och underlag/rokprov-mall), .DS_Store och symlänkar, och utom det som finns byte för byte på samma sökväg i
huvudutcheckningen eller som blob i dess git. Ignorerade filer räknas alltså: kirurgen/, .env, nycklar och
uppladdningar (granskningen av r94, B2).

Ändrat betyder den senaste ändringen av en fil eller symlänk (den senare av mtime och ctime: en kopia med bevarade tider
är ny fast filerna har gamla mtime) eller när en katalog skapades (en katalogs mtime flyttas när något tas bort ur den).
Allt som rör omvärlden (rötterna, klockan, diskmåttet, processlistan, stoppet, npm och vad som pågår) går genom Ram, så
att provet (kontroller/rokprov/revision/prov_stadning.py) aldrig rör det verkliga systemet. Om en registrerad
tempkatalogs körning lever prövas med ps för just den pid som registreringen anger (korregister.tmp_avslutad); det
läser bara. NWP_STADNING=av stänger av
städningen mot det verkliga systemet; rökprovet sätter den. --torr ändrar ingenting och listar vad som skulle göras. Två
städningar körs aldrig samtidigt (ett lås bredvid körregistret).
"""
import argparse
import bisect
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korregister  # noqa: E402  (processernas identitet och liv, som körregistret läser dem)
import verktygslada as vl  # noqa: E402

# Huvudutcheckningen är alltid den kanoniska vägen, aldrig den som koden råkar köras ur (granskningen av r94, B1: körd ur
# en full kopia med eget .git räknade städningen den riktiga huvudutcheckningen som en kopia). Provet byter ut den.
HUVUDUTCHECKNING = Path.home() / 'nortropic-repos' / 'nortropic-webb-pro'
DYGN = 86400
TMP_ALDER = DYGN                 # punkt 4: en katalog i /tmp som inte ändrats på ett dygn
SCRATCH_ALDER = 7 * DYGN         # punkt 4: en scratchpad-session som inte ändrats på sju dygn
PROCESS_ALDER = DYGN             # punkt 3: en förhandsvisning eller server som gått mer än ett dygn
AKTIV = DYGN                     # punkt 1 och 2: en worktree eller kopia som ändrats det senaste dygnet är i arbete
NPM_FYLLD = 0.85                 # punkt 5: disken fylld över 85 %
NPM_INTERVALL = 30 * DYGN        # punkt 5: annars en gång i månaden
NPM_LAGE = 'NPM-CACHE.json'      # förra rensningen, i underhållets läge
# punkt 5 i redovisningen, också i torrläget där npm aldrig körs (slutgranskningen av r94, KAN-2)
NPM_RENSNING = 'npm cache clean --force utan --cache: npm avgör själv vilken cache som rensas, och sökvägen och storleken före ' \
               'är en uppskattning ur $npm_config_cache, ~/.npmrc eller ~/.npm'
DASHBOARD_PORT = 4771            # ägarens dashboard: stoppas aldrig
MATERIAL_MAX = 200               # så många filer av det egna materialet sparas i redovisningen (antal och summa alltid)

# Repots egna prefix för tempfile.mkdtemp, TemporaryDirectory, mkdtempSync och mktemp (punkt 4). Provet söker igenom
# koden, skapar en katalog för varje prefix där tempfile skapar den och blir rött när ett prefix saknas här. Pythons
# förval (tmp) och andra verktygs kataloger rörs aldrig.
TMP_PREFIX = (
    'nwp-workersprov-',  # kundrepots Worker i workerd (kontroller/workersprov.py)
    'nwp-kandidatmaterial-',                                                         # kandidater.py
    'nwp-kallgap-',                                                                  # prov_kallgap.py
    'nwp-underhall-', 'nwp-global-', 'nwp-skill-', 'nwp-skillintag-', 'nwp-skillreserv-', 'nwp-sajtpaket-',
    'nwp-instrument-', 'nwp-pip-', 'nwp-nodeprov-', 'nwp-motor-',                  # underhall.py
    'nwp-vaktprov-',                                                                  # verktygslada.py
    'nwp-torr-',                                                                      # granska.py
    'nwp-export-', 'nwp-kundrepo-',                                                  # exportera.py, kundrepo.py
    'nwp-preview-',                                                                   # kundrepo.py (förhandsvisningens frysta underlag)
    'nwp-yt-', 'nwp-sub-',                                                            # youtube.py
    'nwp-lh-',                                                                        # lighthouse.mjs
    'upptagna-',                                                                      # upptagna_val.py (slugvakt.tmp_katalog,
    'nwp-tillbaka-',                                                                  # rokprov.sh
    'nwp-sandlada-prov.',                                                             # sandlada_prov.sh (mktemp)
    'nwp-startprov-', 'nwp-observation-', 'nwp-rev-', 'nwp-granskning-', 'nwp-pg-',  # rökprovets prov
    'nwp-dokumentation-',                                                             # prov_dokumentation.py
    'nwp-flode-',                                                                     # prov_flode.py
    'nwp-dokvy-',                                                                     # prov_dokumentationsvy.py
    'nwp-stadprov-',                                                                  # prov_stadning.py
    'nwp-startkvitto-',                                                               # prov_startkvitto.py
    'nwp-dyad-',                                                                      # prov_dyad.py (repots kopia och dumparna)
    'nwp-slutpost-',                                                                  # prov_slutpost.py
    'nwp-skisskritik-',                                                               # prov_skisskritik.py
    'nwp-ateljeslut-',                                                                # prov_ateljeslut.py
    'nwp-kundstart-',                                                                 # isolerade kundärendeprov
    'nwp-kirurg-',                                                                    # isolerade förbättringsprov
    'nwp-lasgrans-',                                                                  # prov_lasgrans.py
    'nwp-refinsp-',                                                                   # prov_referensinspektion.py
    'nwp-canvashig-',                                                                 # prov_canvas_hig.py
    'nwp-rorelse-',                                                                   # prov_rorelse.py
    'nwp-fangst-',                                                                    # prov_fangst.py
    'nwp-arbetsyta-',                                                                 # prov_arbetsyta.py
    'nwp-meddelanden-', 'nwp-bevakning-',                                                               # prov_meddelanden.py
    'nwp-pilotsession-',                                                              # kundstart_modell.py (Kundstarts pilotsession)
    'nwp-blind-',                                                                     # atelje.py (de blinda sessionernas arbetskatalog)
)
# fasta kataloger i /tmp som aldrig är tillfälliga: körregistret och intagslåset, läget när underlag/ är låst, och
# granskarnas och byggenas arbetsrötter (deras verktyg städar dem)
ALDRIG_TMP = ('nwp-korningar', 'nwp-startkontroll', 'nwp-granskning', 'nwp-granskarforsok')
ALDRIG_TMP_PREFIX = ('nwp-bygge-',)
# det som går att återskapa och därför inte är eget material (B2)
HARLEDDA = ('node_modules', '__pycache__')    # var som helst
BYGGEN = ('dist', '.astro')                    # bara bredvid en package.json: ett hämtat dist/ i underlag/ är material (K2)
INTE_MATERIAL_FILER = ('.DS_Store',)
FIXTUR = ('kunder/rokprov-mall', 'underlag/rokprov-mall')  # rökprovets egen fixtur, som det skriver i varje utcheckning
KOPIA_NAMN = re.compile(r'(?i)^(?:.*[-_.])?kopia(?:[-_.\d].*)?$')

RADERAD, STOPPAD, RENSAD, KVAR, VANTAR, FEL = 'raderad', 'stoppad', 'rensad', 'kvar', 'väntar på ägaren', 'fel'
REST = 'äldre rest, väntar på identifiering'  # repots prefix men ingen giltig registrering: raderas aldrig (2026-10-07)
TORRT = {RADERAD: 'skulle raderas', STOPPAD: 'skulle stoppas', RENSAD: 'skulle rensas'}
UTFALL = (RADERAD, STOPPAD, RENSAD, KVAR, VANTAR, FEL, REST) + tuple(TORRT.values())
# en sessions arbetsyta tas bort först när varje vanlig fil i den är registrerad eller går att återskapa (ägarens beslut
# 2026-10-07; granskningen av r100, BÖR-1): alla filer prövas, oavsett ändelse. Undantaget är bara det som bevisligen är
# härlett: node_modules/ och __pycache__/ var som helst, och i en riktig venv (riktig_venv) bara venvens egna delar
# (venv_harlett). En katalog som bara heter venv prövas som allt annat, och så gör projektets egna lib/, bin/ och include/
# också när en venv ligger i projektets rot (granskningen GR-20261007-r100-om, KAN-B och scenariot C11).
HARLETT_ALLTID = ('node_modules', '__pycache__')
VENV_TOLK = re.compile(r'python(3(\.\d+)?)?w?$')  # bin/python, python3, python3.12: tolken eller länken till den
VENV_AKTIVERA = ('activate', 'activate.bat', 'activate.csh', 'activate.fish', 'activate.nu', 'activate.ps1', 'activate.xsh',
                 'activate_this.py', 'Activate.ps1', 'deactivate.bat')  # venv-modulens och virtualenvs aktiveringsskript
VERSION_KVITTON = ('*/VERSION.json', '*/*/VERSION.json')  # uppdragens kvitton i huvudutcheckningens underlag/ (pilotens moment)
OMTAG = 'omtag'  # underlag/<slug>/omtag/<stämpel>/…/KVITTO.json: det bedömda som omtaget sparat (kontroller/atelje.py)
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
SESSION = re.compile(UUID)
SESSION_ARG = re.compile(r'(?:--resume|--session-id|-r)(?:=|\s+)(%s)' % UUID)
SESSION_FIL = re.compile(r'/projects/[^/]+/%s\.jsonl$|/claude-\d+/[^/]+/%s/' % (UUID, UUID))
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


def verklig_sokvag(p):
    return Path(os.path.realpath(p))


def huvudutcheckning(rot):
    """Den utcheckning som äger .git för koden i rot (en worktree ger sin huvudutcheckning). Faller git blir det rot
    själv, och då är det inte HUVUDUTCHECKNING: städningen redovisar bara."""
    rc, ut = vl.kor(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], timeout=30, cwd=rot, bara_ut=True)
    return verklig_sokvag(Path(ut.strip()).parent) if rc == 0 and ut.strip() else verklig_sokvag(rot)


def npm_cache_katalog(miljo=None, hem=None):
    """En uppskattning av npm:s cache utan att köra npm: npm config get roterar ~/.npm/_logs, också i torrläget
    (omgranskningen av r94, K-b). $npm_config_cache, annars cache= i ~/.npmrc, annars ~/.npm. Den följer inte alla npm:s
    regler (NPM_CONFIG_USERCONFIG, att den sista raden gäller, kommentarer och ${VAR}), så den används bara för mätningen
    och redovisningen: den skarpa rensningen låter npm själv avgöra cachen (npm_rensa; slutgranskningen av r94, KAN-2).
    None när ~/.npmrc inte går att läsa eller anger något annat än en absolut sökväg: då redovisas cachen som inte
    kontrollerad."""
    miljo = os.environ if miljo is None else miljo
    hem = Path(hem) if hem else Path.home()

    def sokvag(v):
        v = re.sub(r'\$\{(\w+)\}', lambda m: miljo.get(m.group(1), ''), v.strip().strip('"\''))
        v = str(hem) + v[1:] if v.startswith('~/') or v == '~' else v
        return Path(v) if os.path.isabs(v) else None

    for k in ('npm_config_cache', 'NPM_CONFIG_CACHE'):
        if miljo.get(k):
            return sokvag(miljo[k])
    rc = hem / '.npmrc'
    if os.path.lexists(rc):
        try:
            text = rc.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None
        for rad in text.splitlines():
            m = re.match(r'\s*cache\s*=(.*)$', rad)
            if m:
                return sokvag(m.group(1))
    return hem / '.npm'


def tmp_rotar():
    """/tmp och macOS tempkatalog ($TMPDIR, där tempfile och Nodes tmpdir() lägger repots kataloger; granskningen av r94, Ö5)."""
    ut = [verklig_sokvag('/tmp')]
    if verklig_sokvag(tempfile.gettempdir()) not in ut:
        ut.append(verklig_sokvag(tempfile.gettempdir()))
    return ut


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
    """Städningens omvärld: rötterna, klockan, diskmåttet, processlistan, stoppet, npm och vad som pågår. Provet ger
    egna; verklig() ger maskinens. Det som inte anges här finns inte: en Ram utan $TMPDIR-rot eller transkript läser
    inget därifrån."""

    def __init__(self, repo, repos_rot, tmp_rot, scratch_rot, npm_cache, tillstand, klocka=time.time, disk=None,
                 processer=None, stoppa=None, npm=None, upptagen=None, torr=False, vanta_stopp=5.0, skyddade=(),
                 tmp_extra=(), claude_projekt=None, las=None, npm_pagar=None):
        self.repo = verklig_sokvag(repo)  # huvudutcheckningen för koden som kör (ska vara HUVUDUTCHECKNING)
        self.repos_rot = verklig_sokvag(repos_rot)
        self.tmp_rot = verklig_sokvag(tmp_rot) if tmp_rot else None
        self.tmp_extra = [verklig_sokvag(p) for p in tmp_extra if p]
        # scratchpads rot ligger i /tmp: är den själv en symlänk följs den inte, och då är den ingen rot (2026-10-07)
        self.scratch_angiven = Path(os.path.abspath(scratch_rot)) if scratch_rot else None
        self.scratch_lank = bool(scratch_rot) and os.path.islink(self.scratch_angiven)
        self.scratch_rot = verklig_sokvag(scratch_rot) if scratch_rot and not self.scratch_lank else None
        self.npm_cache = Path(npm_cache) if npm_cache else None  # uppskattningen: bara för mätningen och redovisningen (KAN-2)
        self.tillstand = Path(tillstand) if tillstand else None
        self.claude_projekt = Path(claude_projekt) if claude_projekt else None
        self.las = Path(las) if las else None
        self.klocka = klocka
        self.disk = disk or (lambda: disk_matt(self.repos_rot))
        self.processer = processer or las_processer
        self.stoppa = stoppa or (lambda pid: os.kill(pid, signal.SIGTERM))
        self.npm = npm or npm_rensa
        self.upptagen = upptagen or upptaget
        self.npm_pagar = npm_pagar or npm_installerar
        self.torr = torr
        self.vanta_stopp = vanta_stopp
        # raderas aldrig, och inget som innehåller dem: huvudutcheckningens underlag/ och kunder/ och ~/Arkiv (hela
        # huvudutcheckningen skyddas av far_inte_raderas)
        self.skyddade = [self.repo / 'underlag', self.repo / 'kunder', Path.home() / 'Arkiv'] + [Path(p) for p in skyddade]
        self.worktree_vagar = []  # registrerade worktrees: tas bara bort av punkt 1 (git worktree remove)
        self.lankmal = []         # det huvudutcheckningen länkar till (K1)
        self.kvitton = None       # det beständigt registrerade i huvudutcheckningen (Kvitton), läst när det behövs

    @classmethod
    def verklig(cls, tillstand=None, torr=False):
        """Maskinens rötter: ~/nortropic-repos, /tmp och $TMPDIR, scratchpad (/private/tmp/claude-<uid>), npm:s cache och
        Claude Codes transkript. Läget (förra npm-rensningen och diskvaktens städningar) i huvudutcheckningens
        underlag/startkontroll/, där underhållets rapport ligger."""
        rotar = tmp_rotar()
        konfig = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
        return cls(repo=huvudutcheckning(vl.ROOT), repos_rot=HUVUDUTCHECKNING.parent, tmp_rot=rotar[0], tmp_extra=rotar[1:],
                   scratch_rot=rotar[0] / ('claude-%d' % os.getuid()), npm_cache=npm_cache_katalog(),
                   tillstand=tillstand or HUVUDUTCHECKNING / 'underlag' / 'startkontroll', claude_projekt=konfig / 'projects',
                   las=korregister.KATALOG / '.stadning', torr=torr)

    def tmp_alla(self):
        return [x for x in [self.tmp_rot] + self.tmp_extra if x]

    def rotar(self):
        return [x for x in [self.repos_rot] + self.tmp_alla() + [self.scratch_rot] if x]

    def huvuden(self):
        """Huvudutcheckningen som den står (HUVUDUTCHECKNING) och som den är (realpath), och utcheckningen koden kör ur."""
        return {Path(os.path.abspath(HUVUDUTCHECKNING)), verklig_sokvag(HUVUDUTCHECKNING), self.repo, Path(os.path.abspath(self.repo))}


def utanfor_huvudutcheckningen(ram):
    """Skälet när städningen inte körs från huvudutcheckningen (HUVUDUTCHECKNING) eller en av dess worktrees, annars
    None. Då städas ingenting, allt redovisas bara (granskningen av r94, B1)."""
    h = Path(os.path.abspath(HUVUDUTCHECKNING))
    if h.is_symlink() or not (h / '.git').is_dir():
        return 'huvudutcheckningen %s finns inte som en katalog med eget .git' % h
    if ram.repo != verklig_sokvag(h):
        return 'städningen körs från %s, som varken är huvudutcheckningen %s eller en av dess worktrees' % (ram.repo, h)
    return None


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


def projektnamn(sokvag):
    """Claude Codes namn på projektet för en arbetskatalog (scratchpad /private/tmp/claude-<uid>/<projekt>/ och
    transkripten ~/.claude/projects/<projekt>/): varje tecken utom bokstäver och siffror blir ett bindestreck."""
    return re.sub(r'[^A-Za-z0-9]', '-', str(sokvag))


def ar_claude(kommando):
    forsta = (kommando or '').split(None, 1)
    return bool(forsta) and os.path.basename(forsta[0]) == 'claude' or '/@anthropic-ai/claude-code/' in (kommando or '')


class Anvandning:
    """Vad maskinens processer använder: arbetskataloger och öppna filer sorterade för uppslag (hundratals
    scratchpad-sessioner mot tiotusentals öppna filer), kommandoraderna, de sessions-id processerna nämner, och projekten
    med en claude-process vars sessions-id inte syns."""

    def __init__(self, processer):
        self.processer = processer
        self.okand = None
        if processer is None:
            self.okand = 'processerna kunde inte läsas (ps)'
        elif any(x.get('cwd_kand') is False for x in processer):
            self.okand = 'processernas arbetskataloger kunde inte läsas (lsof)'
        poster, self.sessioner, self.okanda = [], {}, {}
        for x in processer or ():
            if x.get('cwd'):
                poster.append((x['cwd'], x, 'har sin arbetskatalog där'))
            for f in x.get('filer') or ():
                poster.append((f, x, 'har %s öppen' % f))
            kom = x.get('kommando') or ''
            for u in set(SESSION.findall(kom)):
                self.sessioner.setdefault(u, 'pid %d nämner sessionens id i sina argument (%s)' % (x['pid'], kort(kom)))
            for f in x.get('filer') or ():
                for u in set(SESSION.findall(f)):
                    self.sessioner.setdefault(u, 'pid %d har %s öppen (%s)' % (x['pid'], f, kort(kom)))
            if ar_claude(kom) and not SESSION_ARG.search(kom) and not any(SESSION_FIL.search(f) for f in x.get('filer') or ()):
                self.okanda.setdefault(projektnamn(x['cwd']) if x.get('cwd') else '*', x['pid'])
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

    def session(self, projekt, uuid):
        """Skälet när sessionen kan leva (Ö3): en process nämner dess id i argumenten eller i en öppen fil, eller en
        claude-process i samma projekt har ett id som inte syns (oklart: kvar). Annars None."""
        if self.okand:
            return self.okand
        if uuid in self.sessioner:
            return self.sessioner[uuid]
        pid = self.okanda.get('*') or self.okanda.get(projekt)
        if pid:
            return 'claude-processen pid %d i samma projekt har ett sessions-id som inte syns i argumenten eller i öppna ' \
                   'filer: oklart, kvar' % pid
        return None


def anvands(anv, p):
    """Skälet när en levande process använder p, annars None (Anvandning.skal; None som anv: processerna är okända)."""
    return (anv or Anvandning(None)).skal(p)


def anvands_nu(ram, p, session=None):
    """Samma prövning med en ny processlista, direkt före en radering (K13): en process som börjat använda katalogen
    medan städningen mätte och jämförde syns."""
    try:
        anv = Anvandning(ram.processer())
    except Exception:  # noqa: BLE001 — okända processer: använd
        anv = Anvandning(None)
    return anv.skal(p) or (anv.session(*session) if session else None)


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
        return ' '.join(korregister.startad(x['pid']).split()) == ' '.join(str(x.get('lstart') or '').split())
    if not korregister.lever(x['pid']) or not samma():
        return KVAR, 'processen finns inte längre, eller pid:en har en annan starttid (återanvänd); inget stoppat'
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


def hasha(p):
    """(sha256, git-blobbens sha1) för filen, i en läsning."""
    h256, blob = hashlib.sha256(), hashlib.sha1()
    with open(p, 'rb') as f:
        blob.update(b'blob %d\0' % os.fstat(f.fileno()).st_size)
        for bit in iter(lambda: f.read(1 << 20), b''):
            h256.update(bit)
            blob.update(bit)
    return h256.hexdigest(), blob.hexdigest()


def _kasta(e):
    raise e


def git_saknas(repo, objekt):
    """De av objekten (sha1) som inte finns i repots git, ur git cat-file --batch-check. Kastar OSError när git inte svarar."""
    objekt = sorted(set(objekt))
    if not objekt:
        return set()
    rc, ut = vl.kor(['git', 'cat-file', '--batch-check'], cwd=repo, indata='\n'.join(objekt) + '\n', timeout=600, bara_ut=True)
    rader = [r.split() for r in ut.splitlines() if r.strip()]
    if rc or len(rader) != len(objekt):
        raise OSError('git cat-file svarade inte i %s (kod %s)' % (repo, rc))
    return {r[0] for r in rader if len(r) >= 2 and r[1] == 'missing'}


def eget_material(kandidat, repo):
    """[(relativ sökväg, storlek)] för det i kandidaten (en kopia eller worktree) som inte går att återskapa ur
    huvudutcheckningen (B2): varje fil utom .git, det härledda (node_modules och __pycache__ var som helst, dist och .astro
    bredvid en package.json), rökprovets fixtur, .DS_Store och symlänkar, som varken finns byte för byte på samma
    relativa sökväg i huvudutcheckningen (lstat: en länk där räknas inte, K1) eller som blob i dess git. Ignorerade filer
    räknas: kirurgen/, .env, nycklar och uppladdningar. Kastar OSError när något inte går att läsa eller git inte svarar:
    det som inte går att jämföra raderas aldrig."""
    kandidat, repo, kvar = Path(kandidat), Path(repo), {}
    for rot, mappar, filer in os.walk(kandidat, onerror=_kasta):
        r = Path(rot)
        rel_rot = r.relative_to(kandidat)
        paket = 'package.json' in filer
        mappar[:] = [m for m in mappar if not ((str(rel_rot) == '.' and m == '.git') or m in HARLEDDA or (m in BYGGEN and paket)
                                               or (rel_rot / m).as_posix() in FIXTUR or os.path.islink(r / m))]
        for f in filer:
            if f in INTE_MATERIAL_FILER or (str(rel_rot) == '.' and f == '.git'):
                continue
            p = r / f
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode):  # symlänkar och uttag är inget material
                continue
            rel = (rel_rot / f).as_posix()
            s256, blob = hasha(p)
            try:
                hs = os.lstat(repo / rel)
                lika = stat.S_ISREG(hs.st_mode) and hs.st_size == st.st_size and sha256_fil(repo / rel) == s256
            except OSError:
                lika = False
            if not lika:
                kvar.setdefault(blob, []).append((rel, st.st_size))
    saknas = git_saknas(repo, kvar)
    return sorted(x for b, xs in kvar.items() if b in saknas for x in xs)


def material_falt(eget):
    return {'material': [{'sokvag': r, 'storlek': s} for r, s in eget[:MATERIAL_MAX]], 'material_antal': len(eget),
            'material_storlek': sum(s for _r, s in eget)}


def material_kort(eget, n=5):
    return ', '.join('%s (%s)' % (r, storlek_text(s)) for r, s in eget[:n]) + (' och %d till' % (len(eget) - n) if len(eget) > n else '')


def lankmal(ram):
    """Målen (realpath) för symlänkarna i huvudutcheckningens underlag/ och kunder/, utom i node_modules: det som
    huvudutcheckningen länkar till raderas aldrig (granskningen av r94, K1)."""
    ut = []
    for h in sorted({verklig_sokvag(x) for x in ram.huvuden()}):
        for topp in ('underlag', 'kunder'):
            for rot, mappar, filer in os.walk(h / topp):
                mappar[:] = [m for m in mappar if m != 'node_modules']
                for n in mappar + filer:
                    q = os.path.join(rot, n)
                    if os.path.islink(q):
                        ut.append((verklig_sokvag(q), Path(q)))
    return ut


def relation(r, s):
    """r är s, ligger i s, eller innehåller s."""
    return r == s or s in r.parents or r in s.parents


def far_inte_raderas(ram, p, worktree=False):
    """Skälet när p aldrig får raderas, annars None: en symlänk, huvudutcheckningen (HUVUDUTCHECKNING, realpath, och
    utcheckningen koden kör ur) eller något i eller runt den, underlag/ och kunder/, ~/Arkiv, en registrerad worktree
    (utom i punkt 1), något huvudutcheckningen länkar till, en rot eller en gemensam förälder till en rot (också en
    $TMPDIR som ligger i /tmp; ägarens beslut 2026-10-07), eller något utanför rötterna."""
    p = Path(p)
    if p.is_symlink():
        return 'en symlänk'
    r = verklig_sokvag(p)
    for x in ram.rotar() + [y for y in (ram.scratch_angiven,) if y]:
        if r == verklig_sokvag(x) or r in verklig_sokvag(x).parents:
            return 'en rot eller en gemensam förälder (%s)' % x
    for h in ram.huvuden():
        if relation(r, h):
            return 'huvudutcheckningen (%s)' % h
    for s in ram.skyddade:
        if relation(r, verklig_sokvag(s)):
            return 'skyddad (%s)' % s
    for w in ram.worktree_vagar:
        if (not worktree or w != r) and relation(r, w):
            return 'en registrerad worktree (%s)' % w
    for mal, lank in ram.lankmal:
        if relation(r, mal):
            return 'huvudutcheckningen länkar hit (%s)' % lank
    if not any(x in r.parents for x in ram.rotar()):
        return 'utanför städregelns rötter'
    return None


def identitet(p):
    """(st_dev, st_ino) för p med lstat, eller None."""
    try:
        st = os.lstat(p)
        return (st.st_dev, st.st_ino)
    except OSError:
        return None


def ta_bort_trad(p, ident=None):
    """Tar bort katalogen p och allt i den utan att följa någon symlänk (ägarens beslut 2026-10-07). p prövas först med
    lstat: en länk eller en fil tas inte bort. Själva raderingen görs av shutil.rmtree, som på den här plattformen går
    med filbeskrivare och prövar varje katalog med lstat och fstat (avoids_symlink_attacks): en länk som byts in mellan
    provet och raderingen följs aldrig, och en länk i katalogen tas bort som länk utan att dess mål rörs (granskningen av
    r100, KAN-1). Ger felen ([] när allt gick)."""
    p = str(p)
    st = os.lstat(p)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        return ['%s är ingen riktig katalog (en länk eller en fil): inget borttaget' % p]
    if ident is not None and (st.st_dev, st.st_ino) != tuple(ident):  # en katalog som bytts ut efter prövningen (KAN-C)
        return ['%s byttes ut efter prövningen (en annan katalog under samma namn): inget borttaget' % p]
    if not shutil.rmtree.avoids_symlink_attacks:  # utan filbeskrivare går en utbytt länk inte att utesluta: inget raderas
        return ['%s: plattformens shutil.rmtree kan följa en länk som byts in; inget borttaget' % p]
    fel = []
    shutil.rmtree(p, onexc=lambda f, s, e: fel.append('%s: %s' % (s, getattr(e, 'strerror', None) or e)))
    return fel


def radera(ram, p, ident=None):
    """None, eller felet. Bara inom rötterna och aldrig det skyddade (far_inte_raderas); symlänkar följs aldrig
    (ta_bort_trad). ident: katalogens (st_dev, st_ino) vid prövningen; en katalog som bytts ut sedan dess raderas aldrig
    (granskningen GR-20261007-r100-om, KAN-C)."""
    skal = far_inte_raderas(ram, p)
    if skal:
        return 'raderas aldrig: %s' % skal
    try:
        fel = ta_bort_trad(p, ident)
    except OSError as e:
        fel = ['%s: %s' % (p, e.strerror or e)]
    return '; '.join(fel[:3]) if fel else None


def direkt_under(ram, d, rotar):
    """Skälet när d inte är en riktig katalog direkt under en av rotarna, annars None (ägarens beslut 2026-10-07: bara den
    registrerade katalogen själv, aldrig /tmp, $TMPDIR eller en gemensam förälder). lstat: d är ingen länk; föräldern är
    roten (rotens egna länkar, som /tmp → /private/tmp, är redan lösta); d löses inte till något annat; och d är varken en
    rot eller en förälder till en."""
    try:
        st = os.lstat(d)
    except OSError as e:
        return 'går inte att läsa (%s)' % (e.strerror or e)
    if stat.S_ISLNK(st.st_mode):
        return 'en symlänk följs aldrig'
    if not stat.S_ISDIR(st.st_mode):
        return 'ingen katalog'
    d = Path(d)
    rotar = [verklig_sokvag(x) for x in rotar]
    foralder = verklig_sokvag(d.parent)
    if foralder not in rotar:
        return 'ligger inte direkt under %s' % ' eller '.join(str(x) for x in rotar)
    if verklig_sokvag(d) != foralder / d.name:
        return 'sökvägen löses till %s' % verklig_sokvag(d)
    r = foralder / d.name
    for x in ram.rotar():
        if r == x or r in x.parents:
            return 'en rot eller en gemensam förälder (%s)' % x
    return None


# --- git ---

def git(*a, cwd, timeout=120, bara_ut=False):
    return vl.kor(['git', *a], timeout=timeout, cwd=cwd, bara_ut=bara_ut)


def worktrees(ram):
    """De registrerade worktrees utom huvudutcheckningen (git worktree list --porcelain -z): [{sokvag, head, gren, last,
    saknas}], eller None när git inte svarar."""
    rc, ut = git('worktree', 'list', '--porcelain', '-z', cwd=ram.repo, bara_ut=True)
    if rc != 0:
        return None
    alla, cur = [], None
    for falt in ut.split('\0'):
        if falt.startswith('worktree '):
            cur = {'sokvag': Path(falt[len('worktree '):]), 'head': None, 'gren': None, 'last': None, 'saknas': False, 'bar': False}
        elif cur is None:
            continue
        elif falt.startswith('HEAD '):
            cur['head'] = falt[5:].strip()
        elif falt.startswith('branch '):
            cur['gren'] = falt[7:].strip()
        elif falt == 'bare':
            cur['bar'] = True
        elif falt.startswith('locked'):
            cur['last'] = falt[6:].strip() or 'utan skäl'
        elif falt.startswith('prunable'):
            cur['saknas'] = True
        elif not falt:
            alla.append(cur)
            cur = None
    if cur:
        alla.append(cur)
    return [w for w in alla if not w['bar'] and verklig_sokvag(w['sokvag']) not in ram.huvuden()]


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


def egen_commit(ram, w):
    """Har grenen (eller den frikopplade HEAD) fått en egen commit sedan den skapades? True, False (bara skapad, ännu
    inte påbörjad: en session kan vänta på den) eller None (ingen reflogg att läsa). Ur reflogens ämnesrader: commit,
    cherry-pick, revert eller am gjorda där (granskningen av r94, Ö2). En rebase eller en snabbspolning på ett nyare main
    är ingen egen commit: en gren som bara uppdaterats så väntar på ägaren (omgranskningen av r94)."""
    if w['gren']:
        rc, ut = git('reflog', 'show', '--format=%gs', w['gren'], cwd=ram.repo, bara_ut=True)
    else:
        rc, ut = git('reflog', 'show', '--format=%gs', 'HEAD', cwd=w['sokvag'], bara_ut=True)
    if rc or not ut.strip():
        return None
    return any(re.match(r'(?:commit|cherry-pick|revert|am)\b', x) for x in ut.splitlines())


def onada_commits(ram, w):
    """Commitarna i worktreens HEAD-reflogg (och dess HEAD) som försvinner med worktreen: de nås varken från en gren,
    från origin/main eller från en reflogg som står kvar i huvudutcheckningens .git, till exempel en commit på en
    frikopplad HEAD. Reflogen försvinner med worktreens adminkatalog, och då blir de onåbara tills git gc rensar dem
    (omgranskningen av r94, Ö1 för worktrees): de räknas som eget material. En commit som ersatts av en rebase eller amend
    står kvar i grenens reflogg efter git worktree remove och räknas inte (slutgranskningen av r94, BÖR-1). --reflog efter
    --single-worktree, körd i huvudutcheckningen, är grenarnas, stashens och huvudutcheckningens egna refloggar, men ingen
    worktrees HEAD-reflogg: den här worktreens försvinner nu, de andras när deras worktrees tas bort. [(sha, ämne)], eller
    None när reflogen eller git inte svarar. En post vars commit redan saknas i git går inte att rädda och räknas inte."""
    rc, ut = git('reflog', 'show', '--format=%H', 'HEAD', cwd=w['sokvag'], bara_ut=True)
    if rc:
        return None
    shas = list(dict.fromkeys([s for s in ut.split() if re.fullmatch(r'[0-9a-f]{40}', s)] + ([w['head']] if w['head'] else [])))
    try:
        shas = [s for s in shas if s not in git_saknas(ram.repo, shas)]
    except OSError:
        return None
    if not shas:
        return []
    rc, ut = git('log', '--format=%H %s', *shas, '--not', '--branches', 'refs/remotes/origin/main', '--single-worktree', '--reflog',
                 cwd=ram.repo, timeout=300, bara_ut=True)
    if rc:
        return None
    return [tuple(r.split(' ', 1)) if ' ' in r else (r, '') for r in ut.splitlines() if r.strip()]


def egna_commits(ram, d):
    """Det i en kopias eget git som inte finns kvar i huvudutcheckningen: ocommittade och köade ändringar (git status),
    och varje commit som går att nå ur kopians refs, HEAD och refloggar (en frikopplad HEAD, stash@{1} och äldre; Ö1)
    men som saknas i huvudutcheckningens git. [] när allt finns där."""
    rc, st = git('--no-optional-locks', 'status', '--porcelain', cwd=d, bara_ut=True)
    if rc:
        return ['git status svarade inte i kopian']
    ut = ['ocommittad ändring: %s' % r[3:] for r in st.splitlines() if r.strip()][:10]
    rc, revs = git('rev-list', '--all', '--reflog', cwd=d, timeout=300, bara_ut=True)
    if rc:
        return ut + ['kopians commits gick inte att läsa']
    try:
        saknas = git_saknas(ram.repo, revs.split())
    except OSError as e:
        return ut + [str(e)]
    return ut + ['egen commit: %s' % s[:12] for s in sorted(saknas)[:10]] + (['och %d till' % (len(saknas) - 10)] if len(saknas) > 10 else [])


# --- vad som pågår (Ö4) ---

def underhall_pagar(kataloger):
    """Skälet när ett annat underhåll pågår (UNDERHALL-PAGAR.json med en levande pid som kör underhall.py), annars None."""
    for k in kataloger:
        d = vl.las_json(Path(k) / 'UNDERHALL-PAGAR.json', {}) or {}
        try:
            pid = int(d.get('pid'))
        except (TypeError, ValueError):
            continue
        if pid != os.getpid() and korregister.lever(pid) and 'underhall' in korregister.kommando(pid):
            return 'underhållet pågår (pid %d, sedan %s)' % (pid, d.get('start'))
    return None


def intag_pagar(laset=None):
    """Skälet när underhållets intagslås är taget (ett intag pågår), annars None. Skapar aldrig låsfilen."""
    try:
        fd = os.open(str(laset or korregister.BYTESLAS), os.O_RDONLY)
    except OSError:
        return None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 'ett intag pågår (intagslåset är taget)'
    finally:
        os.close(fd)
    return None


def upptaget(kataloger=None, laset=None):
    """Skälet när en körning (körregistret och ateljén), ett underhåll eller ett intag pågår, annars None. Läser bara:
    körregistrets döda poster står kvar (torrläget skriver inget; K6)."""
    p = vl.pagaende(rensa=False)
    if p:
        return 'en körning pågår (%s)' % ', '.join(p)
    return underhall_pagar(kataloger or [HUVUDUTCHECKNING / 'underlag' / 'startkontroll', vl.LAGE]) or intag_pagar(laset)


def npm_installerar():
    import underhall
    return underhall.npm_installerar()


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
    """([(kopia, med repots kännetecken)], [kataloger med repots kännetecken som inte heter kopia]) direkt under
    ~/nortropic-repos. En kopia heter kopia* eller <namn>-kopia…, är ingen symlänk och varken är, innehåller eller ligger
    i huvudutcheckningen (sökvägen eller realpath) eller en registrerad worktree (B1). Dolda kataloger och annat utan
    repots kännetecken rörs inte."""
    kanda = [verklig_sokvag(w['sokvag']) for w in wts]
    kop, andra = [], []
    try:
        innehall = sorted(ram.repos_rot.iterdir())
    except OSError:
        return [], []
    for d in innehall:
        if d.name.startswith('.') or d.is_symlink() or not d.is_dir():
            continue
        r = verklig_sokvag(d)
        if any(relation(r, h) for h in ram.huvuden()) or any(relation(r, w) for w in kanda):
            continue
        kannetecken = (d / 'kor.sh').is_file() and (d / 'kontroller').is_dir()
        if KOPIA_NAMN.match(d.name):
            kop.append((d, kannetecken))
        elif kannetecken:
            andra.append(d)
    return kop, andra


def bedom_worktree(ram, w, anv, senast, mfel):
    """(utfall, skäl, fält) för en registrerad worktree; RADERAD betyder att den får tas bort. senast och mfel ur matt(),
    mätta innan något git-kommando körts i den."""
    p = w['sokvag']
    gren = w['gren'][len('refs/heads/'):] if (w['gren'] or '').startswith('refs/heads/') else w['gren']
    if w['saknas'] or not p.is_dir():
        return KVAR, 'katalogen finns inte längre; registreringen står kvar tills git worktree prune körs', {}
    skal = far_inte_raderas(ram, p, worktree=True)
    if skal:
        return KVAR, 'rörs inte: %s' % skal, {}
    if verklig_sokvag(p) == verklig_sokvag(vl.ROOT):
        return KVAR, 'städningen körs från den här utcheckningen', {}
    if w['last']:
        return KVAR, 'låst med git worktree lock (%s)' % w['last'], {}
    ref = w['gren'] or w['head']
    if not ref:
        return KVAR, 'varken gren eller HEAD i git worktree list', {}
    vem = ('grenen %s' % gren) if gren else ('den frikopplade HEAD %s' % (w['head'] or '?')[:12])
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
        return VANTAR, '%d sökvägar gick inte att läsa; worktreen går inte att jämföra, ägaren avgör' % mfel, {}
    if ram.klocka() - senast <= AKTIV:
        return KVAR, 'ändrad det senaste dygnet (%s): arbetet kan pågå' % iso(senast), {}
    egen = egen_commit(ram, w)
    if egen is not True:
        return VANTAR, 'okänd: %s ser sammanslagen ut bara för att den %s; en session kan vänta på den, ägaren avgör' % (
            vem, 'inte fått någon egen commit sedan den skapades' if egen is False else 'saknar en reflogg som visar en egen commit'), {}
    try:
        eget = eget_material(p, ram.repo)
    except OSError as e:
        return VANTAR, 'worktreen går inte att jämföra med huvudutcheckningen (%s); ägaren avgör' % e, {}
    onada = onada_commits(ram, w)
    if onada is None:
        return VANTAR, 'worktreens HEAD-reflogg gick inte att pröva mot grenarna, origin/main och huvudutcheckningens ' \
                       'refloggar; ägaren avgör', {}
    delar, falt = [], {}
    if eget:
        delar.append('%d filer (%s) som inte går att återskapa ur huvudutcheckningen: %s' % (
            len(eget), storlek_text(sum(s for _r, s in eget)), material_kort(eget)))
        falt.update(material_falt(eget))
    if onada:
        delar.append('%d commits som bara finns i worktreens HEAD-reflogg och försvinner med den (ingen gren, origin/main eller '
                     'reflogg i huvudutcheckningen når dem, till exempel på en frikopplad HEAD): %s' % (
                         len(onada), ', '.join('%s %s' % (s[:12], a) for s, a in onada[:5])))
        falt['commits'] = [{'sha': s, 'amne': a} for s, a in onada[:MATERIAL_MAX]]
    if delar:
        return VANTAR, '%s är sammanslagen och pushad, men har %s; ägaren avgör' % (vem, ' och '.join(delar)), falt
    return RADERAD, '%s har egna commits, är sammanslagen i main och pushad, och inget i worktreen eller dess reflogg saknas i ' \
                    'huvudutcheckningen; tas bort med git worktree remove, grenen och dess commits finns kvar' % vem, {}


def punkt1(ram, red, wts, anv):
    """Worktrees som är påbörjade, sammanslagna och pushade, utan eget material, tas bort med git worktree remove
    (aldrig --force)."""
    if wts is None:
        red.post(1, 'worktree', ram.repo, None, KVAR, 'git worktree list svarade inte; inga worktrees tas bort')
        return
    for w in wts:
        p = w['sokvag']
        gren = (w['gren'] or '').replace('refs/heads/', '') or None
        storlek, senast, mfel = matt(p) if p.is_dir() else (None, 0.0, 0)
        utfall, skal, falt = bedom_worktree(ram, w, anv, senast, mfel)
        if utfall == RADERAD and not ram.torr:
            nu = anvands_nu(ram, p)
            if nu:
                utfall, skal = KVAR, 'används: %s' % nu
            else:
                rc, ut = git('worktree', 'remove', str(p), cwd=ram.repo)  # aldrig --force: en smutsig worktree står kvar
                if rc:
                    utfall, skal = FEL, 'git worktree remove föll (%s); kontrollera vad som finns kvar i %s' % (vl.sista(ut, 240), p)
                elif gren and git('rev-parse', '--verify', '-q', 'refs/heads/' + gren, cwd=ram.repo)[0] != 0:
                    utfall, skal = FEL, 'worktreen togs bort, men grenen %s finns inte längre' % gren
        red.post(1, 'worktree', p, storlek, utfall, skal, gren=gren, **falt)


def punkt2(ram, red, kop, andra, anv):
    """Kopior av repot: utan eget material raderas de; med eget material väntar de på ägaren, med listan."""
    for d in andra:
        red.post(2, 'kopia', d, matt(d)[0], VANTAR, 'har repots kännetecken men heter inte kopia och är ingen registrerad '
                                                   'worktree: rörs inte, ägaren avgör')
    for d, kannetecken in kop:
        ident = identitet(d)  # katalogens identitet vid prövningen; jämförs direkt före raderingen (KAN-C)
        storlek, senast, mfel = matt(d)
        skal = far_inte_raderas(ram, d)
        if skal:
            red.post(2, 'kopia', d, storlek, KVAR, 'rörs inte: %s' % skal)
            continue
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
            red.post(2, 'kopia', d, storlek, VANTAR, 'kopian går inte att jämföra med huvudutcheckningen (%s); ägaren avgör' % e)
            continue
        if eget:
            red.post(2, 'kopia', d, storlek, VANTAR, 'eget material som inte går att återskapa ur huvudutcheckningen: %d filer '
                                                     '(%s): %s; ägaren avgör' % (len(eget), storlek_text(sum(s for _r, s in eget)),
                                                                                 material_kort(eget)), **material_falt(eget))
            continue
        nu = None if ram.torr else anvands_nu(ram, d)
        if nu:
            red.post(2, 'kopia', d, storlek, KVAR, 'används: %s' % nu)
            continue
        fel = None if ram.torr else radera(ram, d, ident)
        red.post(2, 'kopia', d, storlek, FEL if fel else RADERAD,
                 ('raderingen föll: %s' % fel) if fel else 'inget eget material och inga egna commits (jämfört med '
                                                           'huvudutcheckningen), ingen process')


def process_rotar(ram, wts, kop):
    """Där en förhandsvisning eller server får stoppas (punkt 3): registrerade worktrees inom rötterna, kopior, flödets
    egna kataloger direkt i /tmp och $TMPDIR (nwp-* och repots tempprefix) och scratchpad. Ägarens egna kataloger i /tmp
    hör inte dit (K4)."""
    ut = [verklig_sokvag(w['sokvag']) for w in wts or [] if any(x in verklig_sokvag(w['sokvag']).parents for x in ram.rotar())]
    ut += [verklig_sokvag(d) for d, k in kop if k]
    for rot in ram.tmp_alla():
        try:
            ut += [verklig_sokvag(d) for d in rot.iterdir() if (d.name.startswith('nwp-') or d.name.startswith(TMP_PREFIX)) and d.is_dir()]
        except OSError:
            pass
    return ut + ([ram.scratch_rot] if ram.scratch_rot else [])


def punkt3(ram, red, wts, kop, processer):
    """Förhandsvisningar och servrar inom räckvidden, utan levande förälder och äldre än ett dygn, stoppas med SIGTERM.
    Ger pid:arna som stoppades (eller skulle stoppas i torrläget)."""
    if processer is None:
        red.post(3, 'process', None, None, KVAR, 'processerna kunde inte läsas (ps); inget stoppat')
        return set()
    rot_var = [varianter(r) for r in process_rotar(ram, wts, kop)]
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
    """Kataloger i /tmp och $TMPDIR med repots prefix: bara de som är registrerade som en körnings egna och vars körning är
    avslutad raderas, och de oregistrerade redovisas som äldre rester (stada_tmp). Gamla scratchpad-sessioner, när ingen
    process använder dem och deras rapporter och bilder är registrerade (stada_katalog). Ingen symlänk följs."""
    for rot in ram.tmp_alla():
        if not rot.is_dir():
            continue
        for d in sorted(rot.iterdir()):
            n = d.name
            if n in ALDRIG_TMP or n.startswith(ALDRIG_TMP_PREFIX) or not n.startswith(TMP_PREFIX) or d.is_symlink() or not d.is_dir():
                continue
            if ram.scratch_rot and relation(verklig_sokvag(d), ram.scratch_rot):
                continue
            stada_tmp(ram, red, d, anv, next(x for x in TMP_PREFIX if n.startswith(x)))
    if ram.scratch_lank:
        red.post(4, 'scratchpad', ram.scratch_angiven, None, KVAR, 'scratchpads rot är en symlänk (till %s): den följs inte, och '
                                                                   'inget i den rörs' % os.path.realpath(ram.scratch_angiven))
    elif ram.scratch_rot and ram.scratch_rot.is_dir():
        for projekt in sorted(ram.scratch_rot.iterdir()):
            if not projekt.name.startswith('-') or projekt.is_symlink() or not projekt.is_dir():
                continue
            for s in sorted(projekt.iterdir()):
                if SESSION.fullmatch(s.name) and not s.is_symlink() and s.is_dir():
                    stada_katalog(ram, red, s, anv, SCRATCH_ALDER, 'scratchpad', 'en sessions scratchpad, inte ändrad på sju dygn',
                                  session=(projekt.name, s.name))


def alder_text(sekunder):
    if sekunder is None:
        return 'okänd ålder'
    d = int(sekunder // DYGN)
    return ('%d dygn' % d) if d >= 1 else ('%d timmar' % int(sekunder // 3600))


def stada_tmp(ram, red, d, anv, prefix):
    """En katalog med repots prefix direkt i /tmp eller $TMPDIR (ägarens beslut 2026-10-07): raderas bara när den är en
    riktig katalog direkt under roten, är registrerad som en körnings egen (korregister.tmp_agare), körningen är avslutad
    (korregister.tmp_avslutad), den inte ändrats på ett dygn och ingen process använder den. Utan giltig registrering är
    den en äldre rest: den raderas aldrig och redovisas med sökväg, storlek och ålder."""
    ident = identitet(d)  # katalogens identitet vid prövningen; jämförs direkt före raderingen (KAN-C)
    storlek, senast, mfel = matt(d)
    if mfel:
        red.post(4, 'tillfällig katalog', d, storlek, KVAR, '%d sökvägar gick inte att läsa; ändringstiden är okänd' % mfel)
        return
    alder = ram.klocka() - senast
    if alder <= TMP_ALDER:
        return  # ung: lämnas och redovisas inte
    skal = far_inte_raderas(ram, d) or direkt_under(ram, d, ram.tmp_alla())
    if skal:
        red.post(4, 'tillfällig katalog', d, storlek, KVAR, 'rörs inte: %s' % skal)
        return
    post, ogiltig = korregister.tmp_agare(d)
    if not post:
        red.post(4, 'tillfällig katalog', d, storlek, REST, 'repots prefix %s men %s: prefixet ensamt räcker inte, och katalogen '
                                                              'raderas inte förrän den identifierats' % (prefix, ogiltig),
                 alder=int(alder), andrad=iso(senast))
        return
    vem = '%s (pid %d, startad %s)' % (post['vad'], post['pid'], post.get('pstart') or '?')
    avslutad, varfor = korregister.tmp_avslutad(post)
    if not avslutad:
        red.post(4, 'tillfällig katalog', d, storlek, KVAR, 'registrerad av %s, och körningen %s: %s' % (
            vem, 'pågår' if avslutad is False else 'kan pågå', varfor), registrerad=post['vad'])
        return
    a = anvands(anv, d)
    if a:
        red.post(4, 'tillfällig katalog', d, storlek, KVAR, 'används: %s' % a, registrerad=post['vad'])
        return
    nu = None if ram.torr else anvands_nu(ram, d)
    if nu:
        red.post(4, 'tillfällig katalog', d, storlek, KVAR, 'används: %s' % nu, registrerad=post['vad'])
        return
    fel = None if ram.torr else radera(ram, d, ident)
    red.post(4, 'tillfällig katalog', d, storlek, FEL if fel else RADERAD, ('raderingen föll: %s' % fel) if fel else
             'registrerad av %s, körningen avslutad (%s); repots prefix %s, inte ändrad på ett dygn (senast %s), ingen process' % (
                 vem, varfor, prefix, iso(senast)), registrerad=post['vad'])


def transkript_andrat(ram, projekt, uuid):
    """När sessionens transkript (~/.claude/projects/<projekt>/<uuid>.jsonl och katalogen bredvid) senast ändrades, eller 0."""
    if not ram.claude_projekt:
        return 0.0
    bas = ram.claude_projekt / projekt
    return max(matt(bas / (uuid + '.jsonl'))[1] if (bas / (uuid + '.jsonl')).exists() else 0.0,
               matt(bas / uuid)[1] if (bas / uuid).exists() else 0.0)


class Kvitton:
    """Det som är beständigt registrerat, eller går att återskapa, i huvudutcheckningen (ägarens beslut 2026-10-07:
    rapporter, bedömda bilder och tillhörande versionsunderlag ska ligga beständigt och vara registrerade innan en
    tillfällig arbetsyta tas bort). En fil räknas när
    - dess sha256 står i underlag/granskningar/FORTECKNING.jsonl, i ett uppdrags VERSION.json (VERSION_KVITTON) eller i
      ett omtags KVITTO.json (underlag/<slug>/omtag/<stämpel>/ och nedåt, aldrig i en dold katalog: ett sparande som inte
      blev klart; granskningen av r100, KAN-3), och den registrerade filen med samma sha256 ligger kvar: förteckningens
      och kvittots fil på sin angivna plats, VERSION.json:s någonstans i kvittots katalog. En sökväg ur en förteckning
      eller ett kvitto godtas bara när den är relativ och utan .. och dess realpath ligger i underlag/ (kvittots egen
      katalog) och utanför arbetsytan (KAN-2);
    - eller den finns byte för byte som en blob som nås från en ref i huvudutcheckningens git (git rev-list --objects
      --all: grenarna, origin och taggarna). Ett löst objekt, eller ett som bara nås ur en reflogg, kan git gc ta bort och
      räknas inte (BÖR-2).
    Kvittona läses, git frågas och de registrerade filerna hashas en gång per körning, och bara när det behövs. Ingen
    länk följs."""

    def __init__(self, repo):
        self.repo = Path(repo)
        self.underlag = self.repo / 'underlag'
        self._ul = None         # underlag/:s realpath
        self._sokvagar = None   # sha256 -> [(registrerad fil, katalogen den måste ligga i)]
        self._version = None    # sha256 -> [VERSION.json:s katalog]
        self._katalog = {}      # katalog -> {sha256} för dess filer
        self._sha = {}          # fil -> sha256
        self._git = None        # objekten som nås från en ref i huvudutcheckningens git

    @staticmethod
    def _sha256_hex(x):
        return isinstance(x, str) and re.fullmatch(r'[0-9a-f]{64}', x) is not None

    @staticmethod
    def _relativ(v):
        """En relativ sökväg utan .., . eller tomma led, som en Path; annars None (KAN-2)."""
        if not isinstance(v, str) or not v or v.startswith('/') or '\\' in v or '\0' in v:
            return None
        delar = v.split('/')
        if any(x in ('', '.', '..') for x in delar):
            return None
        return Path(*delar)

    @staticmethod
    def _inom(r, rot):
        return r == rot or r.startswith(rot.rstrip(os.sep) + os.sep)

    def _omtag_kvitton(self):
        """Omtagens KVITTO.json i underlag/<slug>/omtag/<stämpel>/ och nedåt; dolda kataloger och länkar hoppas över."""
        if not self.underlag.is_dir():
            return
        for slug in sorted(self.underlag.iterdir()):
            om = slug / OMTAG
            if slug.is_symlink() or not slug.is_dir() or om.is_symlink() or not om.is_dir():
                continue
            for st in sorted(om.iterdir()):
                if st.name.startswith('.') or st.is_symlink() or not st.is_dir():
                    continue
                for rot, mappar, filer in os.walk(st, followlinks=False):
                    mappar[:] = sorted(m for m in mappar if not m.startswith('.'))
                    k = Path(rot) / 'KVITTO.json'
                    if 'KVITTO.json' in filer and not k.is_symlink():
                        yield k

    def _las(self):
        if self._sokvagar is not None:
            return
        self._ul = os.path.realpath(self.underlag)
        self._sokvagar, self._version = {}, {}
        f = self.underlag / 'granskningar' / 'FORTECKNING.jsonl'
        if f.is_file() and not f.is_symlink():
            for rad in f.read_text(encoding='utf-8').split('\n'):  # JSONL: radslut, aldrig U+2028 (GR-20261007-r100-om#KAN-A)
                try:
                    p = json.loads(rad)
                except ValueError:
                    continue
                if not isinstance(p, dict) or not self._sha256_hex(p.get('sha256')):
                    continue
                if str(p.get('bas') or 'underlag/').rstrip('/') != 'underlag':  # förteckningen gäller underlag/, inget annat
                    continue
                rel_ = self._relativ(p.get('fil'))
                if rel_ is not None:
                    self._sokvagar.setdefault(p['sha256'], []).append((self.underlag / rel_, self._ul))
        for k in self._omtag_kvitton():
            d = vl.las_json(k, {})
            for rel_s, s in ((d or {}).get('filer') or {}).items() if isinstance(d, dict) else ():
                rel_ = self._relativ(rel_s)
                if rel_ is not None and self._sha256_hex(s):
                    self._sokvagar.setdefault(s, []).append((k.parent / rel_, os.path.realpath(k.parent)))
        for monster in VERSION_KVITTON:
            for k in sorted(self.underlag.glob(monster)):
                if k.is_file() and not k.is_symlink() and self._inom(os.path.realpath(k.parent), self._ul):
                    for s in self._hexvarden(vl.las_json(k, None)):
                        self._version.setdefault(s, []).append(k.parent)

    def _hexvarden(self, x):
        if isinstance(x, dict):
            for v in x.values():
                yield from self._hexvarden(v)
        elif isinstance(x, list):
            for v in x:
                yield from self._hexvarden(v)
        elif self._sha256_hex(x):
            yield x

    def _fil_sha(self, p):
        """sha256 för en vanlig fil (ingen länk, inget annat), annars None."""
        p = Path(p)
        if p not in self._sha:
            try:
                st = os.lstat(p)
                self._sha[p] = sha256_fil(p) if stat.S_ISREG(st.st_mode) else None
            except OSError:
                self._sha[p] = None
        return self._sha[p]

    def _katalogens(self, d):
        if d not in self._katalog:
            ut = set()
            for rot, mappar, filer in os.walk(d, followlinks=False):
                for n in filer:
                    s = self._fil_sha(Path(rot) / n)
                    if s:
                        ut.add(s)
            self._katalog[d] = ut
        return self._katalog[d]

    def var(self, sha, utom=None):
        """Var filen med sha256 ligger registrerad och beständigt, eller None. utom är arbetsytan: en registrering som pekar
        in i den räknas inte."""
        self._las()
        ut_r = os.path.realpath(utom) if utom else None
        for p, rot in self._sokvagar.get(sha, ()):
            r = os.path.realpath(p)
            if not self._inom(r, rot) or not self._inom(r, self._ul) or (ut_r and self._inom(r, ut_r)):
                continue
            if self._fil_sha(p) == sha:
                return str(p.relative_to(self.repo)) if self.repo in p.parents else str(p)
        for d in self._version.get(sha, ()):
            if (not ut_r or not self._inom(os.path.realpath(d), ut_r)) and sha in self._katalogens(d):
                return '%s (VERSION.json)' % (d.relative_to(self.repo) if self.repo in d.parents else d)
        return None

    def i_git(self, blobbar):
        """De av blobbarna (sha1) som nås från en ref i huvudutcheckningens git: git rev-list --objects --all, en gång per
        körning. Kastar OSError när git inte svarar: då går arbetsytan inte att pröva (BÖR-2)."""
        if not blobbar:
            return set()
        if self._git is None:
            rc, ut = vl.kor(['git', 'rev-list', '--objects', '--all'], cwd=self.repo, timeout=600, bara_ut=True)
            if rc:
                raise OSError('git rev-list --objects --all svarade inte i %s (kod %s)' % (self.repo, rc))
            self._git = {r.split(' ', 1)[0] for r in ut.splitlines() if r.strip()}
        return {b for b in blobbar if b in self._git}


def _site_packages(rot):
    import glob
    return [x for x in glob.glob(os.path.join(glob.escape(str(rot)), 'lib', 'python3*', 'site-packages'))
            if os.path.isdir(x) and not os.path.islink(x)]


def riktig_venv(rot):
    """En riktig venv har utöver pyvenv.cfg sina kännetecken: bin/python och lib/python3.*/site-packages. En pyvenv.cfg i
    ett projekts rot gör alltså inte projektets egna lib/, bin/ och include/ oprövade (granskningen GR-20261007-r100-om,
    KAN-B)."""
    return os.path.lexists(os.path.join(rot, 'bin', 'python')) and bool(_site_packages(rot))


def venv_harlett(rot):
    """(kataloger, filer) med absoluta sökvägar till det som bevisligen är venvens eget i den riktiga venven rot:
    lib/python*/ och lib64/python*/ (där site-packages ligger), include/site/ och include/python*/ (paketens huvudfiler),
    pyvenv.cfg, och i bin/ tolken, aktiveringsskripten och de skript som ett installerat pakets RECORD i site-packages
    listar med samma sha256 (pips ingångar). Allt annat i lib/, bin/ och include/ är projektets och prövas: en venv i ett
    projekts rot (python -m venv .) gömmer inte projektets lib/RAPPORT.md eller bin/bygg.sh (scenariot C11, KAN-B)."""
    import base64
    import glob
    rot = str(rot)
    g = glob.escape(rot)
    kat = {x for m in ('lib', 'lib64') for x in glob.glob(os.path.join(g, m, 'python*'))}
    kat |= set(glob.glob(os.path.join(g, 'include', 'python*'))) | {os.path.join(rot, 'include', 'site')}
    filer, binr, listat = {os.path.join(rot, 'pyvenv.cfg')}, os.path.join(rot, 'bin'), {}
    for sp in _site_packages(rot):
        for rec in glob.glob(os.path.join(glob.escape(sp), '*.dist-info', 'RECORD')):
            try:
                with open(rec, encoding='utf-8', errors='replace') as f:
                    rader = f.read().split('\n')
            except OSError:
                continue
            for rad in rader:
                delar = rad.rstrip('\r').rsplit(',', 2)
                if len(delar) == 3 and delar[1].startswith('sha256='):
                    mal = os.path.normpath(os.path.join(sp, delar[0]))
                    if os.path.dirname(mal) == binr:
                        listat[mal] = delar[1][len('sha256='):]
    try:
        namn = os.listdir(binr)
    except OSError:
        namn = []
    for n in namn:
        p = os.path.join(binr, n)
        if VENV_TOLK.match(n) or n in VENV_AKTIVERA:
            filer.add(p)
        elif p in listat and not os.path.islink(p):
            try:
                with open(p, 'rb') as f:
                    h = base64.urlsafe_b64encode(hashlib.sha256(f.read()).digest()).rstrip(b'=').decode()
            except OSError:
                continue
            if h == listat[p]:  # en ändrad ingång är projektets: den prövas
                filer.add(p)
    return kat, filer


def oregistrerade(ram, d, kvitton):
    """[(relativ sökväg, storlek)] för de vanliga filerna i arbetsytan d som varken är beständigt registrerade
    (Kvitton.var) eller nås från en ref i huvudutcheckningens git (Kvitton.i_git). Alla filer prövas, oavsett ändelse och
    också utan ändelse: rapporter, bilder och versionsunderlag (granskningen av r100, BÖR-1). Bara det bevisligen
    härledda undantas: node_modules/ och __pycache__/ var som helst, och i en riktig venv (riktig_venv) bara venvens egna
    delar (venv_harlett); projektets egna lib/, bin/ och include/ prövas. En katalog som bara heter venv prövas. Ingen länk
    följs, och en länk prövas inte: den tas bort som länk, och dess mål rörs inte. Kastar OSError när något inte går att
    läsa eller git inte svarar: då går arbetsytan inte att pröva, och den väntar på ägaren."""
    d, kvar, hopp_kat, hopp_fil = Path(d), {}, set(), set()
    for rot, mappar, filer in os.walk(d, onerror=_kasta, followlinks=False):
        if 'pyvenv.cfg' in filer and stat.S_ISREG(os.lstat(os.path.join(rot, 'pyvenv.cfg')).st_mode) and riktig_venv(rot):
            k_, f_ = venv_harlett(rot)
            hopp_kat |= k_
            hopp_fil |= f_
        mappar[:] = [m for m in mappar if m not in HARLETT_ALLTID and os.path.join(rot, m) not in hopp_kat
                     and not os.path.islink(os.path.join(rot, m))]
        for f in filer:
            if os.path.join(rot, f) in hopp_fil:
                continue
            p = Path(rot) / f
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode):  # en symlänk eller ett uttag: inget innehåll att förlora
                continue
            s256, blob = hasha(p)
            if kvitton.var(s256, utom=d):
                continue
            kvar.setdefault(blob, []).append((p.relative_to(d).as_posix(), st.st_size))
    i_git = kvitton.i_git(kvar)
    return sorted(x for b, xs in kvar.items() if b not in i_git for x in xs)


def stada_katalog(ram, red, d, anv, alder, vad, varfor, session=None):
    ident = identitet(d)  # katalogens identitet vid prövningen; jämförs direkt före raderingen (KAN-C)
    storlek, senast, mfel = matt(d)
    if mfel:
        red.post(4, vad, d, storlek, KVAR, '%d sökvägar gick inte att läsa; ändringstiden är okänd' % mfel)
        return
    if ram.klocka() - senast <= alder:
        return  # ung: lämnas och redovisas inte
    skal = far_inte_raderas(ram, d)
    if skal:
        red.post(4, vad, d, storlek, KVAR, 'rörs inte: %s' % skal)
        return
    a = anvands(anv, d) or (anv.session(*session) if session and anv else None)
    if a:
        red.post(4, vad, d, storlek, KVAR, ('sessionen kan leva: %s' if session else 'används: %s') % a)
        return
    if session:
        t = transkript_andrat(ram, *session)
        if ram.klocka() - t <= alder:
            red.post(4, vad, d, storlek, KVAR, 'sessionen kan leva: transkriptet ändrades %s' % iso(t))
            return
    registrerat = ''
    if session:  # rapporterna, de bedömda bilderna och versionsunderlaget först registrerade (ägarens beslut 2026-10-07)
        if ram.kvitton is None:
            ram.kvitton = Kvitton(ram.repo)
        try:
            oreg = oregistrerade(ram, d, ram.kvitton)
        except OSError as e:
            red.post(4, vad, d, storlek, VANTAR, 'arbetsytans filer gick inte att pröva mot förteckningen, kvittona och git '
                                                 '(%s); ägaren avgör' % (getattr(e, 'strerror', None) or e))
            return
        if oreg:
            red.post(4, vad, d, storlek, VANTAR, '%d filer (%s) är varken beständigt registrerade (sha256 i '
                                                 'underlag/granskningar/FORTECKNING.jsonl, ett VERSION.json eller ett omtags '
                                                 'KVITTO.json) eller nåbara i huvudutcheckningens git: %s; ägaren avgör' % (
                                                     len(oreg), storlek_text(sum(s for _r, s in oreg)), material_kort(oreg)),
                     **material_falt(oreg))
            return
        registrerat = ', och varje fil i den är beständigt registrerad eller nåbar i huvudutcheckningens git'
    nu = None if ram.torr else anvands_nu(ram, d, session)
    if nu:
        red.post(4, vad, d, storlek, KVAR, 'används: %s' % nu)
        return
    fel = None if ram.torr else radera(ram, d, ident)
    red.post(4, vad, d, storlek, FEL if fel else RADERAD, ('raderingen föll: %s' % fel) if fel else '%s (senast %s), ingen process%s%s' % (
        varfor, iso(senast), ' och ingen levande session' if session else '', registrerat))


def punkt5(ram, red):
    """npm-cachen: över 85 % fylld disk, eller förra rensningen äldre än 30 dygn; aldrig medan något pågår."""
    if not ram.npm_cache:
        red.post(5, 'npm-cachen', None, None, KVAR, 'inte kontrollerad: npm:s cache gick inte att avgöra ur $npm_config_cache, '
                                                    '~/.npmrc eller ~/.npm')
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
    hinder = ram.upptagen() or ram.npm_pagar()
    if hinder:
        red.post(5, 'npm-cachen', cacache, storlek, KVAR, '%s, men %s: rensas vid nästa städning' % (skal, hinder))
        return
    if ram.torr:
        red.post(5, 'npm-cachen', cacache, storlek, RENSAD, skal + '; ' + NPM_RENSNING)
        return
    rc, ut = ram.npm()
    if rc:
        red.post(5, 'npm-cachen', cacache, storlek, FEL, '%s, men npm cache clean föll: %s' % (skal, vl.sista(ut, 200)))
        return
    tid = iso(ram.klocka())
    try:
        vl.skriv_json(ram.tillstand / NPM_LAGE, {'tid': tid, 'storlek_fore': storlek, 'skal': skal})
    except (OSError, TypeError) as e:
        skal += '; tiden kunde inte sparas (%s)' % e
    red.post(5, 'npm-cachen', cacache, storlek, RENSAD, skal + '; ' + NPM_RENSNING)


def npm_rensa():
    """npm cache clean --force utan --cache: npm avgör själv vilken cache som rensas, efter sina egna regler (miljön,
    NPM_CONFIG_USERCONFIG och npmrc-filerna). Städningens sökväg (npm_cache_katalog) är bara en uppskattning för mätningen
    och redovisningen (slutgranskningen av r94, KAN-2). Körs aldrig i torrläget."""
    return vl.kor(['npm', 'cache', 'clean', '--force', '--no-update-notifier'], timeout=900)


def stada(ram, punkter=(1, 2, 3, 4, 5)):
    """Punkterna i ordningen 3, 1, 2, 4 och 5 (en gammal förhandsvisning stoppas före kopian den håller), och
    redovisningen. Utanför huvudutcheckningen redovisas allt bara (B1). En punkt som faller stoppar inte de andra, och
    två städningar körs aldrig samtidigt (K11)."""
    hinder = utanfor_huvudutcheckningen(ram)
    if hinder and not ram.torr:
        ram = copy.copy(ram)
        ram.torr = True
    if ram.las and not ram.torr:
        with vl.las(ram.las, vanta=False) as fick:
            if not fick:
                return {'schema': 1, 'start': iso(ram.klocka()), 'slut': iso(ram.klocka()), 'torr': ram.torr, 'poster': [],
                        'antal': {}, 'besked': 'en annan städning pågår: den här gjorde ingenting'}
            return _stada(ram, punkter, hinder)
    return _stada(ram, punkter, hinder)


def _stada(ram, punkter, hinder):
    red = Redovisning(ram)
    rap = {'schema': 1, 'start': iso(ram.klocka()), 'torr': ram.torr, 'disk_fore': None, 'disk_efter': None}
    if hinder:
        rap['besked'] = hinder + ': ingenting städas, allt redovisas bara'
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
    wts, kop, andra, processer = [], [], [], []
    if behov & {1, 2, 3, 4}:
        try:
            wts = worktrees(ram)
        except Exception:  # noqa: BLE001 — okända worktrees: punkt 1 och 2 rör då ingenting
            wts = None
        ram.worktree_vagar = [verklig_sokvag(w['sokvag']) for w in wts or []]
        try:
            ram.lankmal = lankmal(ram)
        except OSError:
            ram.lankmal = []
    # utan listan över worktrees går en worktree inte att skilja från en kopia: då rörs inga kopior
    if behov & {2, 3} and wts is not None:
        kop, andra = kopior(ram, wts)
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
    steg(2, 'kopia', lambda: punkt2(ram, red, kop, andra, anv))
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
    if rap.get('besked'):
        ut += ['**%s.**' % rap['besked'], '']
    ut += ['%sStädregeln i BESLUT.md (2026-10-06, villkoren för tempkatalogerna och arbetsytorna 2026-10-07), %s–%s. Disken: %s före, %s efter. %s.' % (
        '**Torrläge: inget ändrat.** ' if rap.get('torr') else '', rap.get('start'), rap.get('slut'), disk_text(rap.get('disk_fore')),
        disk_text(rap.get('disk_efter')), antal_text(rap.get('antal') or {})), '']
    if rap.get('poster'):
        ut += ['| Punkt | Vad | Sökväg | Storlek före | Tid | Utfall | Skäl |', '|---|---|---|---|---|---|---|']
        for p in rap['poster']:
            ut.append('| %s | %s | %s | %s | %s | %s | %s |' % (p['punkt'], p['vad'], ('`%s`' % p['sokvag']) if p.get('sokvag') else '–',
                                                               storlek_text(p.get('storlek_fore')), p['tid'],
                                                               p['utfall'].upper() if p['utfall'] in (FEL, VANTAR) else p['utfall'],
                                                               str(p['skal']).replace('|', '/').replace('\n', ' ')))
    rester = [p for p in rap.get('poster') or [] if p['utfall'] == REST]
    if rester:  # ägarens beslut 2026-10-07: äldre rester identifieras separat innan de rensas
        ut += ['', '**Äldre rester, väntar på identifiering** (repots prefix men ingen giltig registrering; raderas aldrig):', '']
        for p in rester:
            ut.append('- `%s` (%s, %s gammal, senast ändrad %s): %s' % (p['sokvag'], storlek_text(p.get('storlek_fore')),
                                                                       alder_text(p.get('alder')), p.get('andrad') or '?', p['skal']))
    vantar = [p for p in rap.get('poster') or [] if p['utfall'] == VANTAR]
    if vantar:
        ut += ['', '**Väntar på ägaren** (raderas inte förrän ägaren avgjort):', '']
        for p in vantar:
            ut.append('- `%s` (%s): %s' % (p['sokvag'], storlek_text(p.get('storlek_fore')), p['skal']))
            for m in (p.get('material') or [])[:20]:
                ut.append('  - `%s` (%s)' % (m['sokvag'], storlek_text(m['storlek'])))
            if (p.get('material_antal') or 0) > 20:
                ut.append('  - och %d filer till (%s sammanlagt)' % (p['material_antal'] - 20, storlek_text(p.get('material_storlek'))))
            for c in (p.get('commits') or [])[:20]:
                ut.append('  - commit `%s` %s' % (c['sha'][:12], c.get('amne') or ''))
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
