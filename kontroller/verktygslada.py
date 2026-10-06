#!/usr/bin/env python3
"""verktygslada.py — verktygslådans komponenter, versioner, prov och läge, gemensamt för startkontrollen
(kontroller/startkontroll.py: snabb, före varje start) och underhållet (kontroller/underhall.py: dagligt, prövar och tar
in). Ägarens uppdrag 2026-10-05 19:13Z, 20:27Z och ~20:50Z (ordagrant i minnet): ingenting i verktygslådan släpar efter;
målet är alltid den senaste versionen som klarat våra prov, låst för varje körning.

Komponenterna: Claude Code och Vercel CLI (globala npm-paket), skillsen (källa och commit ur KALLA.md), sajtens paket
(mall/astro och mall/leverans, i grupper som byts tillsammans), mätinstrumenten (kontroller/package.json och Playwrights
Chromium), Python-paketen (requirements.txt och requirements-lock.txt), Homebrew-formlerna node (senaste LTS som Vercel
stöder), python@3.12, git och gh, Impeccables motor, och macOS, Xcode-verktygen och Homebrew självt (bara redovisade).
Hur var och en prövas och tas in: kunskap/beroenden.md, avsnittet Underhåll.

Läget ligger i underlag/startkontroll/ (utanför git): CACHE.json (uppslag och prov med fingeravtryck och tid),
AVVISADE.json (avvisad version och felet per komponent; prövas om först när en nyare version kommer), GODKANDA.json
(prövade men inte intagna, till exempel för att en körning startade), ANDRINGAR.jsonl (det som tagits in, med commit;
mätinstrumenten märkta) och UNDERHALL.json och .md (senaste underhållet).
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
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
KUNDER = ROOT / 'kunder'
SKILLS = ROOT / '.claude' / 'skills'
LAGE = UNDERLAG / 'startkontroll'
TIMME = 3600
GILTIGHET = {
    'version': 6 * TIMME,       # startkontrollen slår inte upp på nytt; äldre uppslag står med sin tid
    'underhall': 1 * TIMME,     # underhållet slår upp på nytt efter en timme
    'prov': 24 * TIMME,         # förmågeprov (Refero, webbläsarkedjan, detektorn) återanvänds ett dygn
    'modell': 24 * TIMME,
    'mcp': 5 * 60,              # nödvändiga MCP:er bekräftas vid varje start (en server som faller syns inom fem minuter)
    'mobbin': 48 * TIMME,       # Mobbins fullständiga prov görs i underhållet; starten bekräftar anslutningen
    'underhall_aldst': 36 * TIMME,
    'spaning': 7 * 24 * TIMME,
    'lasdatum': 365 * 24 * TIMME,
}
# karenstid: en version räknas först när den varit publicerad så här länge (den oberoende granskningen 2026-10-06, fynd 4:
# en komprometterad release upptäcks oftast inom timmar eller dagar)
KARENS_DAGAR = float(os.environ.get('NWP_UNDERHALL_KARENS_DAGAR') or 3)
# provens miljö: bara det som behövs för att köra, inga nycklar, tokens eller sessionens variabler (fynd 4)
PROVMILJO = ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TERM', 'SHELL', 'TMPDIR', 'PLAYWRIGHT_BROWSERS_PATH')
# Homebrew: bara den namngivna formeln och dess egna beroenden. NO_INSTALLED_DEPENDENTS_CHECK hindrar att andra formler
# som beror på ett uppgraderat beroende uppgraderas på köpet (ägarens ord: aldrig brew upgrade på allt); underhållet
# prövar i stället bibliotekslänkarna efteråt (underhall.lankprov). NO_INSTALL_CLEANUP sparar den förra kegen för en
# återlänkning.
BREW_MILJO = {'HOMEBREW_NO_AUTO_UPDATE': '1', 'HOMEBREW_NO_INSTALL_CLEANUP': '1', 'HOMEBREW_NO_ENV_HINTS': '1',
              'HOMEBREW_NO_ANALYTICS': '1', 'HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK': '1'}
# flaggorna flödet använder och som claude --help listar; --max-turns är dold i hjälpen och prövas av modellsvaret
FLAGGOR = ('--json-schema', '--allowedTools', '--disallowedTools', '--settings', '--setting-sources', '--tools',
           '--permission-mode', '--strict-mcp-config', '--mcp-config', '--effort', '--model', '--output-format')
PROVMODELL = 'claude-haiku-4-5-20251001'  # en kandidatversion av Claude Code prövas med den minsta modellen
GLOBALA = (  # (npm-paket, binär, namn, grupp, nödvändig)
    ('@anthropic-ai/claude-code', 'claude', 'Claude Code', 'Claude Code', True),
    ('vercel', 'vercel', 'Vercel CLI', 'leverans', False),
)
SAJT_GRUPPER = {  # paket som byts tillsammans (samma huvudversion, kamrater)
    'astro': ('astro', '@astrojs/react', '@astrojs/vercel'),
    'react': ('react', 'react-dom'),
    'tailwind': ('tailwindcss', '@tailwindcss/vite'),
}
MATINSTRUMENT = ('playwright', 'axe-core', 'lighthouse', 'html-validate', 'chrome-launcher')
BREW_FORMLER = ('python@3.12', 'git', 'gh')  # node hanteras efter LTS-regeln
EGNA_TILLAGG = ('KALLA.md', 'LICENSE', 'NOTICE.md', 'LICENSE-nous-research')
NODE_INDEX = 'https://nodejs.org/dist/index.json'
VERCEL_NODE = 'https://vercel.com/docs/functions/runtimes/node-js/node-js-versions'
MOTOR_RELEASER = 'https://api.github.com/repos/pbakaus/impeccable/releases?per_page=40'
BREW_RELEASE = 'https://api.github.com/repos/Homebrew/brew/releases/latest'


# --- små hjälpare ---

def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def tid_s(t):
    try:
        return datetime.strptime(str(t), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        return 0


def alder(t):
    return time.time() - tid_s(t) if t else float('inf')


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else str(data).encode('utf-8')).hexdigest()


def sha_fil(p):
    try:
        return sha(Path(p).read_bytes())
    except OSError:
        return None


def las_json(p, standard=None):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return standard


def skriv_json(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.%d.tmp' % os.getpid())
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


def sista(text, n=240):
    return ' '.join(str(text or '').split())[-n:]


def versionstal(v):
    return [int(x) for x in re.findall(r'\d+', str(v or ''))]


def nyare(a, b):
    """Är version a nyare än b?"""
    return bool(a) and bool(b) and versionstal(a) > versionstal(b)


def huvud(v):
    t = versionstal(v)
    return t[0] if t else None


def miljo(extra=None):
    """Barnens miljö: utan körningens NWP_SLUG och NWP_KORNING (provens kataloger ligger utanför kundens) och utan den
    anropande Claude-sessionens variabler."""
    m = {k: v for k, v in os.environ.items()
         if k not in ('NWP_SLUG', 'NWP_KORNING', 'CLAUDECODE') and not k.startswith('CLAUDE_CODE_')}
    m.update(extra or {})
    return m


def provmiljo(extra=None):
    """Miljön för prov som kör nya versioner: bara PROVMILJO, inga nycklar eller tokens (fynd 4)."""
    m = {k: v for k, v in os.environ.items() if k in PROVMILJO}
    m.update(extra or {})
    return m


AVBRUTEN = 130  # slutkoden från kor() när avbryt() svarade ja
SLUTVANTAN = 15  # sekunder kor() väntar på en dödad process; en som sitter fast i kärnan (UE) lämnas (2026-10-06)


def avsluta_trad(pid):
    """Processen, dess grupp och alla ättlingar, också de som startat egna sessioner (ett rökprov vars prov i sin tur
    kör kor(); granskningen av r72, L9)."""
    import nastlad
    barn = nastlad.efterkommande(pid)
    for x in [pid] + barn:
        for f in (lambda q: os.killpg(q, signal.SIGKILL), lambda q: os.kill(q, signal.SIGKILL)):
            try:
                f(x)
            except OSError:
                pass


def kor(args, timeout=120, cwd=None, env=None, indata=None, bara_ut=False, avbryt=None):
    """(slutkod, text): stdout och stderr ihop, eller bara stdout. Kommandot får en egen processgrupp, och en tidsgräns
    avslutar hela gruppen (ett rökprov lämnar inga barn efter sig; fynd 15). avbryt() frågas var femte sekund; svarar
    den ja avslutas gruppen och slutkoden är AVBRUTEN."""
    try:
        p = subprocess.Popen([str(a) for a in args], stdin=subprocess.PIPE if indata is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(cwd or ROOT),
                             env=env if env is not None else miljo(), start_new_session=True)
    except OSError as e:
        return 127, '%s: %s' % (type(e).__name__, e)
    slut = time.time() + timeout
    while True:
        try:
            ut, fel = p.communicate(input=indata, timeout=max(0.1, min(5, slut - time.time())) if avbryt else timeout)
            break
        except subprocess.TimeoutExpired:
            indata = None  # indata skickas bara en gång; utdata går inte förlorad mellan försöken
            avbrutet = bool(avbryt) and time.time() < slut and avbryt()
            if not avbrutet and avbryt and time.time() < slut:
                continue
            avsluta_trad(p.pid)
            try:
                ut, fel = p.communicate(timeout=SLUTVANTAN)
            except subprocess.TimeoutExpired:
                # en process som inte går att avsluta (en krasch som väntar på krashrapporteringen, 2026-10-06) väntas
                # inte in: underhållet och startkontrollen går vidare med ett fel i stället för att hänga
                for s_ in (p.stdout, p.stderr):
                    try:
                        s_ and s_.close()
                    except OSError:
                        pass
                return (AVBRUTEN if avbrutet else 124), 'tidsgränsen %d s nåddes (%s); processen avslutades inte och lämnades' % (
                    timeout, ' '.join(str(a) for a in args[:3]))
            if avbrutet:
                return AVBRUTEN, 'avbrutet (%s)\n%s' % (' '.join(str(a) for a in args[:3]), sista((ut or '') + (fel or ''), 2000))
            return 124, 'tidsgränsen %d s nåddes (%s)' % (timeout, ' '.join(str(a) for a in args[:3]))
    return p.returncode, (ut or '') if bara_ut else (ut or '') + (fel or '')


def hamta_url(url, timeout=30, max_byte=4_000_000, huvuden=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'nortropic-underhall', **(huvuden or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(max_byte)


def lagekatalog():
    try:
        LAGE.mkdir(parents=True, exist_ok=True)
        return LAGE
    except OSError:  # kor.sh låser underlag/ under ett bygge (chflags uchg): läget hamnar då i tmp
        d = Path(tempfile.gettempdir()) / 'nwp-startkontroll'
        d.mkdir(parents=True, exist_ok=True)
        return d


@contextmanager
def las(fil, vanta=True, max_s=None):
    """Ett fillås (fcntl): vanta=False ger False direkt när någon annan håller det; max_s väntar högst så länge."""
    Path(fil).parent.mkdir(parents=True, exist_ok=True)
    f = open(fil, 'a+')
    try:
        if vanta and max_s is None:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield True
            return
        slut = time.time() + (max_s or 0)
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if not vanta or time.time() > slut:
                    yield False
                    return
                time.sleep(1)
        yield True
    finally:
        f.close()


# --- läget: cache, avvisade, godkända och ändringar ---

class Cache:
    def __init__(self, fil):
        self.fil = Path(fil)
        self.d = las_json(self.fil, {}) or {}

    def hamta(self, nyckel, avtryck, giltighet):
        x = self.d.get(nyckel)
        if not isinstance(x, dict) or x.get('avtryck') != avtryck or alder(x.get('tid')) > giltighet:
            return None
        return x

    def spara(self, nyckel, avtryck, **v):
        self.d[nyckel] = dict(v, avtryck=avtryck, tid=nu())
        try:
            skriv_json(self.fil, self.d)
        except OSError:
            pass
        return self.d[nyckel]


# Provreglerna: en avvisning gäller den prövning som gjorde den. När reglerna för hur en version prövas rättas (ett prov
# som en granskning visat dömde fel) räknas äldre avvisningar inte, och versionen prövas en gång till; höj då värdet.
# 2026-10-06-r76: npm audit jämförs advisory för advisory med det installerade trädet (Vercel CLI 60.1.3 avvisades
# 02:49Z av jämförelsen utan bas). 2026-10-06-r77: karenstidens marginal, plattformspaketen, ETARGET och miljöfel
# behåller versionen, båda träden granskas på samma sätt (granskningen av r79, F). 2026-10-06-r90: pinningens prov ärvde
# provmiljöns PATH, där node@24 låg först i underhållets prov av node@24, och avvisade node@24 12:47Z för provets skull.
PROVREGLER = '2026-10-06-r90'


def avvisad(avvisade, id_, version):
    """Avvisningen av versionen när den gjordes med de nuvarande provreglerna, annars None: versionen prövas igen."""
    a = avvisade.for_version(id_, version)
    return a if a and a.get('provregler') == PROVREGLER else None


class Register:
    """{id: {version: {'fel' eller 'avtryck', 'tid', ...}}}: AVVISADE.json och GODKANDA.json. En komponent kan ha flera
    versioner registrerade (en avvisad huvudversion och en patch)."""

    def __init__(self, fil):
        self.fil = Path(fil)
        d = las_json(self.fil, {}) or {}
        self.d = {i: v for i, v in d.items() if isinstance(v, dict) and all(isinstance(x, dict) for x in v.values())}

    def for_version(self, id_, version):
        x = (self.d.get(id_) or {}).get(str(version))
        return dict(x, version=str(version)) if isinstance(x, dict) else None

    def alla(self, id_):
        return [dict(x, version=v) for v, x in (self.d.get(id_) or {}).items()]

    def satt(self, id_, version, **f):
        self.d.setdefault(id_, {})[str(version)] = dict(f, tid=nu())
        skriv_json(self.fil, self.d)

    def ta_bort(self, id_, upp_till=None):
        """Allt för komponenten, eller (upp_till) bara versionerna som inte är nyare än den intagna."""
        fore = json.dumps(self.d.get(id_), sort_keys=True)
        if upp_till is None:
            self.d.pop(id_, None)
        elif id_ in self.d:
            self.d[id_] = {v: x for v, x in self.d[id_].items() if nyare(v, upp_till) or (v != upp_till and not versionstal(v))}
            if not self.d[id_]:
                self.d.pop(id_)
        if json.dumps(self.d.get(id_), sort_keys=True) != fore:
            skriv_json(self.fil, self.d)


# förmågeprov som starten kan göra själv; ett misslyckat görs om i stället för att stoppa starter tills det går ut, och
# underhållet gör dem om varje dygn (Mobbins prov är en liten session och görs i starten bara när det fallit eller gått
# ut; granskningen av r72, M1)
OMPROVBARA = ('prov:refero', 'prov:webblasare', 'prov:detektor', 'prov:vakt', 'prov:mobbin')


class Kontext:
    """En startkontroll eller ett underhåll: med nät eller inte, med prov eller inte, och vad som gjordes respektive
    återanvändes (redovisas i kvittot; proven för fallet "oförändrad miljö upprepar inget")."""

    def __init__(self, nat=True, prova=True, max_alder=None, katalog=None):
        self.nat, self.prova = nat, prova
        self.max_alder = GILTIGHET['version'] if max_alder is None else max_alder
        self.katalog = Path(katalog) if katalog else lagekatalog()
        self.cache = Cache(self.katalog / 'CACHE.json')
        self.avvisade = Register(self.katalog / 'AVVISADE.json')
        self.godkanda = Register(self.katalog / 'GODKANDA.json')
        self.prov_dir = self.katalog / 'prov'
        self.utfort, self.ateranvant = [], []
        self.farsk = False  # underhållet gör de snabba förmågeproven om (Refero, webbläsaren, detektorn, vakten, modellerna)

    def minns(self, nyckel, avtryck='v1', giltighet=None):
        omprovbart = nyckel in OMPROVBARA or nyckel.startswith('modell:')
        if self.farsk and omprovbart:
            return None
        x = self.cache.hamta(nyckel, avtryck, self.max_alder if giltighet is None else giltighet)
        # ett misslyckat förmågeprov som kan göras om återanvänds inte: en tjänst som kommit tillbaka efter ett kort
        # avbrott stoppar då inte varje start ett dygn
        if x and omprovbart and self.prova and x.get('resultat') not in (None, 'ok'):
            return None
        if x:
            self.ateranvant.append(nyckel)
        return x

    def spara(self, nyckel, avtryck='v1', **v):
        self.utfort.append(nyckel)
        return self.cache.spara(nyckel, avtryck, **v)

    def senast_kanda(self, nyckel, avtryck='v1'):
        x = self.cache.d.get(nyckel)
        return x if isinstance(x, dict) and x.get('avtryck') == avtryck else None


def logga_andring(katalog, **post):
    Path(katalog).mkdir(parents=True, exist_ok=True)
    with open(Path(katalog) / 'ANDRINGAR.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(dict(post, tid=nu()), ensure_ascii=False) + '\n')


def andringar(katalog, sedan=None):
    ut = []
    try:
        for rad in (Path(katalog) / 'ANDRINGAR.jsonl').read_text(encoding='utf-8').splitlines():
            try:
                d = json.loads(rad)
            except ValueError:
                continue
            if not sedan or d.get('tid', '') > sedan:
                ut.append(d)
    except OSError:
        pass
    return ut


def uppslag(k, nyckel, hamta, avtryck='v1'):
    """Ett versionsuppslag: färskt nog ur cachen, annars nytt (med nät), annars det senast kända med sin tid.
    Ger (värde, tid, fel)."""
    x = k.minns(nyckel, avtryck)
    if x:
        return x.get('varde'), x['tid'], None
    fel = None
    if k.nat:
        try:
            v = hamta()
        except Exception as e:  # noqa: BLE001 — ett uppslag som faller är okänt, aldrig grönt
            v, fel = None, '%s: %s' % (type(e).__name__, sista(e, 160))
        if v is not None:
            x = k.spara(nyckel, avtryck, varde=v)
            return v, x['tid'], None
    gammal = k.senast_kanda(nyckel, avtryck)
    if gammal:
        return gammal.get('varde'), gammal.get('tid'), fel
    return None, None, fel or ('inte uppslaget (utan nät)' if not k.nat else 'uppslaget gav inget svar')


# --- versionsuppslagen (varje nätanrop har en egen funktion, så att proven kan byta ut den) ---

def iso_s(t):
    try:
        return datetime.fromisoformat(str(t).replace('Z', '+00:00')).timestamp()
    except (TypeError, ValueError):
        return 0


def forhand(v):
    """Förhandsversion (1.2.0-beta.1, 2.0rc1, 3.0.dev2)?"""
    return bool(re.search(r'[a-zA-Z]', str(v).split('+')[0]))


def mogna(tider, nu_s=None):
    """Versionerna som räknas ur {version: publiceringstid}: inga förhandsversioner, och bara de som varit publicerade
    minst KARENS_DAGAR. Ger {'senaste', 'per_huvud': {huvudversion: senaste inom den}, 'nyaste', 'nyaste_tid'}."""
    nu_s = nu_s or time.time()
    ok, nyaste = [], None
    for v, tid_ in tider.items():
        if forhand(v) or not re.match(r'^\d', str(v)):
            continue
        if nyaste is None or versionstal(v) > versionstal(nyaste[0]):
            nyaste = (v, tid_)
        if iso_s(tid_) and nu_s - iso_s(tid_) >= KARENS_DAGAR * 86400:
            ok.append(v)
    per = {}
    for v in ok:
        h = str(huvud(v))
        if h not in per or versionstal(v) > versionstal(per[h]):
            per[h] = v
    return {'senaste': max(ok, key=versionstal) if ok else None, 'per_huvud': per,
            'nyaste': nyaste[0] if nyaste else None, 'nyaste_tid': nyaste[1] if nyaste else None}


def npm_versioner(paket):
    """mogna() ur npm:s publiceringstider (npm view <paket> time)."""
    rc, ut = kor(['npm', 'view', paket, 'time', '--json'], timeout=90, bara_ut=True)
    if rc:
        return None
    d = json.loads(ut or '{}')
    return mogna({v: tid_ for v, tid_ in d.items() if v not in ('created', 'modified')})


def pypi_versioner(namn):
    """mogna() ur PyPI:s uppladdningstider (den tidigaste filen per version; dragna filer räknas inte)."""
    d = json.loads(hamta_url('https://pypi.org/pypi/%s/json' % namn, max_byte=20_000_000))
    tider = {}
    for v, filer in (d.get('releases') or {}).items():
        t_ = sorted(f.get('upload_time_iso_8601') for f in filer or [] if not f.get('yanked') and f.get('upload_time_iso_8601'))
        if t_:
            tider[v] = t_[0]
    return mogna(tider)


def ny_info(info):
    """(senaste, nyare_men_i_karens): den senaste som räknas och en nyare som ännu är i karenstiden."""
    if not isinstance(info, dict):
        return None, None
    s, n = info.get('senaste'), info.get('nyaste')
    return s, (n if n and (not s or nyare(n, s)) else None)


def kandidater_for(installerat, info):
    """Kandidaterna ur en versionsinfo: den senaste som räknas, och när den är en ny huvudversion också den senaste inom
    den nuvarande (en avvisad huvudversion blockerar aldrig patchar; fynd 10)."""
    senaste, _n = ny_info(info)
    ut = []
    if installerat and senaste and nyare(senaste, installerat):
        ut.append(kandidat(senaste, installerat))
        if huvud(senaste) != huvud(installerat):
            inom = (info.get('per_huvud') or {}).get(str(huvud(installerat)))
            if inom and nyare(inom, installerat):
                ut.append(kandidat(inom, installerat, huvudversion=False, inom_huvudversion=True))
    return ut


def brew_info(formel):
    rc, ut = kor(['brew', 'info', '--json=v2', '--formula', formel], timeout=180, env=miljo(BREW_MILJO), bara_ut=True)
    if rc:
        return None
    f = (json.loads(ut).get('formulae') or [None])[0]
    if not f:
        return None
    rev = f.get('revision') or 0
    return {'senaste': f['versions']['stable'] + ('_%d' % rev if rev else ''),
            'installerade': [i.get('version') for i in f.get('installed') or []],
            'lankad': f.get('linked_keg'), 'keg_only': bool(f.get('keg_only'))}


BREW_API = 'https://formulae.brew.sh/api/formula/%s.json'
BREW_HISTORIK = 'https://api.github.com/repos/Homebrew/homebrew-core/commits?path=Formula/%s/%s.rb&per_page=1'


def brew_api(formel):
    """Formelns senaste version ur Homebrews API (formulae.brew.sh) och när formeln senast ändrades (homebrew-core):
    {'senaste', 'tid'}. Det lokala formelindexet uppdateras bara av brew update, som uppdaterar Homebrew självt och
    därför bara redovisas (granskningen av r72, L2 och L5)."""
    f = json.loads(hamta_url(BREW_API % formel, timeout=60))
    rev = f.get('revision') or 0
    ut = {'senaste': f['versions']['stable'] + ('_%d' % rev if rev else ''), 'tid': None}
    try:
        h = json.loads(hamta_url(BREW_HISTORIK % (formel[0], formel), timeout=60, huvuden={'Accept': 'application/vnd.github+json'}))
        ut['tid'] = ((h[0].get('commit') or {}).get('committer') or {}).get('date') if h else None
    except Exception:  # noqa: BLE001 — utan tid räknas formeln som i karenstid
        pass
    return ut


def brew_kandidat(k, formel, installerat, lokal):
    """(kandidat eller None, anteckningar) för en formel som byts på plats: versionen ur det lokala formelindexet (den
    brew kan installera), om den är nyare än den installerade och har passerat karenstiden enligt formelns senaste
    ändring; och om Homebrews API har en nyare version som indexet inte känner till."""
    api, _t, _f = uppslag(k, 'brewapi:' + formel, lambda f=formel: brew_api(f))
    noter = {}
    if api and lokal and nyare(api['senaste'], lokal):
        noter['index_gammalt'] = api['senaste']
    if not (installerat and lokal and nyare(lokal, installerat)):
        return None, noter
    senast_andrad = (api or {}).get('tid')
    # den senaste ändringen av formeln måste ha passerat karenstiden, också när det lokala indexet visar en äldre version:
    # den kan vara lika färsk (granskningen av r73, N2)
    if not api or not senast_andrad or time.time() - iso_s(senast_andrad) < KARENS_DAGAR * 86400:
        noter['i_karens'] = lokal  # den senaste ändringen är färsk eller okänd: prövas när karenstiden gått ut
        return None, noter
    return {'version': lokal, 'formel': formel, 'huvudversion': huvud(lokal) != huvud(installerat)}, noter


def git_head(repo):
    rc, ut = kor(['git', 'ls-remote', repo.rstrip('/') + '.git', 'HEAD'], timeout=60, bara_ut=True)
    h = ut.split()[0] if rc == 0 and ut.strip() else ''
    return h if re.fullmatch(r'[0-9a-f]{40}', h) else None


def node_lts_vercel():
    """Senaste LTS-huvudversionen som Vercel stöder: Nodes versionslista (nodejs.org) och Vercels dokumentation."""
    idx = json.loads(hamta_url(NODE_INDEX, max_byte=20_000_000))
    lts, datum = {}, {}
    for x in idx:  # nyast först
        if x.get('lts'):
            lts.setdefault(huvud(x['version']), x['version'].lstrip('v'))
            datum[x['version'].lstrip('v')] = x.get('date')
    html = hamta_url(VERCEL_NODE).decode('utf-8', 'replace')
    text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))
    m = re.search(r'Current available versions are:\s*((?:\d{2}\.x(?:\s*\([^)]*\))?\s*)+)', text)
    vercel = sorted({int(x) for x in re.findall(r'(\d{2})\.x', m.group(1))}) if m else []
    if not vercel:
        raise RuntimeError('Vercels lista över Node-versioner gick inte att läsa (%s)' % VERCEL_NODE)
    mojliga = [mj for mj in lts if mj in vercel]
    if not mojliga:
        raise RuntimeError('ingen LTS-version som Vercel stöder (LTS %s, Vercel %s)' % (sorted(lts), vercel))
    mj = max(mojliga)
    return {'major': mj, 'version': lts[mj], 'vercel': vercel, 'lts': sorted(lts),
            'datum': {v: d for v, d in datum.items() if huvud(v) in mojliga}}


def motor_releaser():
    d = json.loads(hamta_url(MOTOR_RELEASER, huvuden={'Accept': 'application/vnd.github+json'}))
    v = [str(r.get('tag_name'))[len('engine-v'):] for r in d
         if str(r.get('tag_name', '')).startswith('engine-v') and not r.get('prerelease') and not r.get('draft')]
    return max(v, key=versionstal) if v else None


def brew_senaste_release():
    return json.loads(hamta_url(BREW_RELEASE, huvuden={'Accept': 'application/vnd.github+json'})).get('tag_name')


def softwareupdate_lista():
    """Väntande systemuppdateringar (macOS, Xcode-verktygen); bara läsning, ingen installation."""
    rc, ut = kor(['softwareupdate', '--list'], timeout=300)
    return [m.group(1).strip() for m in re.finditer(r'^\s*\* Label: (.+)$', ut, re.M)] if rc == 0 or 'Label' in ut else None


# --- inventeringen ---

def version_av(args, timeout=60):
    rc, ut = kor(args, timeout=timeout)
    m = re.search(r'(\d+\.\d+\.\d+)', ut)
    return m.group(1) if rc == 0 and m else None


def npm_global_rot():
    rc, ut = kor(['npm', 'root', '-g'], timeout=60, bara_ut=True)
    return ut.strip() if rc == 0 else None


def rad(id_, grupp, namn, typ, **f):
    r = {'id': id_, 'grupp': grupp, 'namn': namn, 'typ': typ, 'kandidater': []}
    r.update({a: b for a, b in f.items() if b is not None})
    return r


def kandidat(version, installerat, **f):
    return dict(f, version=version, huvudversion=bool(f.pop('huvudversion', huvud(version) != huvud(installerat))))


def inv_globala(k):
    ut = []
    rot = npm_global_rot()
    for paket, binar, namn, grupp, nodv in GLOBALA:
        b = os.environ.get('NWP_CLAUDE_BIN') if binar == 'claude' and os.environ.get('NWP_CLAUDE_BIN') else shutil.which(binar)
        inst = version_av([b, '--version']) if b else None
        info, tid, fel = uppslag(k, 'npm:' + paket, lambda p=paket: npm_versioner(p), avtryck='v2')
        senaste, karens = ny_info(info)
        via_npm = bool(b and rot and os.path.realpath(b).startswith(os.path.join(rot, paket) + os.sep))
        r = rad('npm-global:' + paket, grupp, namn, 'npm-global', paket=paket, bin=b, binar=binar, installerat=inst, senaste=senaste,
                kontrollerad=tid, kalla='npm ' + paket, nodvandig=nodv, via_npm=via_npm, uppslagsfel=fel, i_karens=karens,
                paketkatalog=os.path.join(rot, paket) if via_npm else None)  # underhållets npm audit jämför med trädet där
        r['kandidater'] = kandidater_for(inst, info)
        spar = Path(rot).parent / ('.nwp-spar-' + re.sub(r'[^\w.-]+', '_', paket)) if rot else None
        if not inst and spar and (spar / Path(paket).name / 'package.json').is_file():  # ett intag som dog (granskningen av r79, C)
            r['detalj'] = ('det installerade trädet saknas efter ett avbrutet intag; klonen ligger i %s, och underhållet lägger '
                           'tillbaka den när ingen npm-installation pågår och inget annat ligger kvar (annars redovisas det i '
                           'underhållets rapport)' % spar)
        ut.append(r)
    return ut


def kalla_for(d):
    """({'repo', 'vag', 'commit'}, None), (None, 'egen') utan KALLA.md, eller (None, felet)."""
    f = Path(d) / 'KALLA.md'
    if not f.is_file():
        return None, 'egen'
    m = re.search(r'\*\*Källa:\*\*(.*?)(?=\n- \*\*|\n\n|\Z)', f.read_text(encoding='utf-8'), re.S)
    if not m:
        return None, 'KALLA.md saknar raden Källa'
    t = ' '.join(m.group(1).split())
    repo = re.search(r'https://github\.com/[\w.-]+/[\w.-]+', t)
    vag = re.search(r'`([^`\s]+/)`', t)
    commit = re.search(r'commit\s+`?([0-9a-f]{7,40})\b', t)
    if not repo or not commit:
        return None, 'källraden saknar repo eller commit'
    return {'repo': repo.group(0).rstrip('.,'), 'vag': (vag.group(1) if vag else '').strip('/'), 'commit': commit.group(1)}, None


def mappavtryck(d):
    d = Path(d)
    return sha(''.join(sorted('%s:%s\n' % (p.relative_to(d).as_posix(), sha_fil(p)) for p in d.rglob('*')
                              if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts)))


def inv_skills(k):
    ut = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir() and not p.is_symlink()):
        kalla, fel = kalla_for(d)
        if not kalla:
            ut.append(rad('skill:' + d.name, 'skill', d.name, 'skill', installerat='egen' if fel == 'egen' else None,
                          resultat='ok' if fel == 'egen' else 'okand',
                          detalj='egen skill, ingen extern källa' if fel == 'egen' else fel))
            continue
        head, tid, ufel = uppslag(k, 'git:' + kalla['repo'], lambda r=kalla['repo']: git_head(r))
        r = rad('skill:' + d.name, 'skill', d.name, 'skill', installerat=kalla['commit'][:12], senaste=head[:12] if head else None,
                kontrollerad=tid, kalla=kalla['repo'], uppslagsfel=ufel, skill=kalla, mapp=str(d))
        if head and not head.startswith(kalla['commit']):
            plan = k.senast_kanda('skillplan:' + d.name, sha('%s|%s|%s' % (kalla['commit'], head, mappavtryck(d))))
            if plan and not plan.get('andrat'):
                r['detalj'] = 'källan har nyare commits, men mappen är oförändrad sedan %s (jämfört %s)' % (kalla['commit'][:12], plan['tid'])
            elif plan:
                r['kandidater'].append(kandidat(head, None, huvudversion=False, filer=plan.get('filer'), konflikter=plan.get('konflikter')))
            else:
                r['kandidater'].append(kandidat(head, None, huvudversion=False, ojamfort=True))
        ut.append(r)
    return ut


def paketberoenden(katalog):
    return dict((las_json(Path(katalog) / 'package.json', {}) or {}).get('dependencies') or {})


def installerat_i(node_modules, paket):
    return (las_json(Path(node_modules) / paket / 'package.json', {}) or {}).get('version')


def inv_sajt(k):
    """Sajtens paket i grupper: mall/astro och mall/leverans byts tillsammans."""
    mall, lev = paketberoenden(ROOT / 'mall' / 'astro'), paketberoenden(ROOT / 'mall' / 'leverans')
    alla = sorted(set(mall) | set(lev))
    grupper, sedda = [], set()
    for g, medl in SAJT_GRUPPER.items():
        m = [p for p in medl if p in alla]
        if m:
            grupper.append((g, m))
            sedda.update(m)
    grupper += [(p, [p]) for p in alla if p not in sedda]
    ut = []
    for g, medl in grupper:
        inst, senaste, tider, olika, ufel, inom_v = {}, {}, [], [], None, {}
        for p in medl:
            a, b = mall.get(p), lev.get(p)
            if a and b and a != b:
                olika.append('%s: mallen %s, leveransen %s' % (p, a, b))
            inst[p] = a or b
            info, t, f = uppslag(k, 'npm:' + p, lambda p_=p: npm_versioner(p_), avtryck='v2')
            senaste[p], _karens = ny_info(info)
            inom = (info or {}).get('per_huvud', {}).get(str(huvud(inst[p]))) if isinstance(info, dict) else None
            inom_v[p] = inom if inom and nyare(inom, inst[p]) else None
            tider.append(t)
            ufel = ufel or f
        kand = {p: senaste[p] for p in medl if senaste.get(p) and nyare(senaste[p], inst[p])}
        r = rad('sajt:' + g, 'sajtens paket', ', '.join(medl), 'sajt', medlemmar=medl,
                installerat=', '.join('%s %s' % (p, inst[p]) for p in medl),
                senaste=', '.join('%s %s' % (p, senaste[p] or '?') for p in medl) if any(senaste.values()) else None,
                kontrollerad=min((t for t in tider if t), default=None), kalla='npm', uppslagsfel=ufel,
                detalj=('; '.join(olika)) if olika else None, nodvandig=False)
        if kand:
            nya = dict(inst, **kand)
            stor = any(huvud(kand[p]) != huvud(inst[p]) for p in kand)
            r['kandidater'].append({'version': ', '.join('%s %s' % (p, nya[p]) for p in medl), 'paket': nya, 'huvudversion': stor})
            inom = {p: inom_v[p] for p in medl if inom_v.get(p)}
            if stor and inom:  # den senaste inom nuvarande huvudversioner, så att patchar inte väntar på huvudversionen (fynd 10)
                nya2 = dict(inst, **inom)
                r['kandidater'].append({'version': ', '.join('%s %s' % (p, nya2[p]) for p in medl), 'paket': nya2, 'huvudversion': False,
                                        'inom_huvudversion': True})
        if any(senaste.get(p) is None for p in medl):
            r['ofullstandigt'] = True
        ut.append(r)
    return ut


WEBBLASARE = ('chromium', 'chromium-headless-shell', 'webkit')  # rökprovets resor går i Chromium och WebKit


def webblasare(node_modules=None):
    """[(namn, revision, webbläsarversion, installerad)] för Playwrights webbläsare ur playwright-core/browsers.json."""
    nm = Path(node_modules or ROOT / 'kontroller' / 'node_modules')
    d = las_json(nm / 'playwright-core' / 'browsers.json', {}) or {}
    cache = Path(os.environ.get('PLAYWRIGHT_BROWSERS_PATH') or Path.home() / 'Library' / 'Caches' / 'ms-playwright')
    ut = []
    for b in d.get('browsers') or []:
        if b.get('name') in WEBBLASARE:
            katalog = cache / ('%s-%s' % (b['name'].replace('-', '_'), b.get('revision')))
            ut.append((b['name'], b.get('revision'), b.get('browserVersion'), katalog.is_dir()))
    return ut


def inv_instrument(k):
    kontr = ROOT / 'kontroller'
    pins = paketberoenden(kontr)
    ut = []
    for p in MATINSTRUMENT:
        pin = pins.get(p)
        ins = installerat_i(kontr / 'node_modules', p)
        info, t, f = uppslag(k, 'npm:' + p, lambda p_=p: npm_versioner(p_), avtryck='v2')
        v, karens = ny_info(info)
        r = rad('instrument:' + p, 'mätinstrument', p, 'instrument', installerat=pin, senaste=v, kontrollerad=t, kalla='npm ' + p,
                matinstrument=True, nodvandig=True, uppslagsfel=f, i_karens=karens)
        if not ins:
            r.update(resultat='fel', detalj='%s saknas i kontroller/node_modules: kör npm ci i kontroller/' % p)
        elif ins != pin:
            r.update(resultat='fel', detalj='node_modules har %s men låset %s: kör npm ci i kontroller/' % (ins, pin))
        r['kandidater'] = kandidater_for(pin, info)
        ut.append(r)
    wb = webblasare()
    saknas = [n for n, _r, _v, finns in wb if not finns]
    ut.append(rad('instrument:webblasare', 'mätinstrument', 'Playwrights webbläsare', 'webblasare',
                  installerat=', '.join('%s %s (r%s)' % (n, v or '', r) for n, r, v, _f in wb) or None,
                  matinstrument=True, nodvandig=True, kalla='följer Playwright-versionen',
                  resultat='ok' if wb and not saknas else 'fel',
                  detalj='installerade' if wb and not saknas else 'saknas: %s (npx playwright install %s, i kontroller/)' % (
                      ', '.join(saknas) or 'browsers.json', ' '.join(WEBBLASARE))))
    return ut


def python_las_filer(rot=None):
    rot = Path(rot or ROOT)
    return rot / 'requirements.txt', rot / 'requirements-lock.txt'


def las_krav(fil):
    """{namn (gemener, bindestreck): version} ur en kravfil med exakta versioner."""
    ut = {}
    try:
        for r in Path(fil).read_text(encoding='utf-8').splitlines():
            m = re.match(r'^\s*([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;#]+)', r)
            if m:
                ut[re.sub(r'[-_.]+', '-', m.group(1)).lower()] = m.group(2)
    except OSError:
        pass
    return ut


def venv_python(rot=None):
    return Path(rot or ROOT) / '.venv' / 'bin' / 'python'


def pip_frys(python):
    rc, ut = kor([python, '-m', 'pip', 'freeze', '--all', '--exclude', 'pip'], timeout=120, bara_ut=True)
    return {re.sub(r'[-_.]+', '-', a).lower(): b for a, _, b in (r.partition('==') for r in ut.splitlines() if '==' in r)} if rc == 0 else None


def inv_python(k):
    krav, lasfil = python_las_filer()
    ut = []
    if not krav.is_file() or not lasfil.is_file():
        return [rad('pip:las', 'Python', 'versionslåset', 'pip-las', resultat='behallen', nodvandig=False,
                    detalj='requirements.txt och requirements-lock.txt saknas; underhållet skapar låset ur .venv först')]
    las_ = las_krav(lasfil)
    frys = pip_frys(venv_python())
    if frys is None:
        ut.append(rad('pip:miljo', 'Python', '.venv mot låset', 'pip-miljo', resultat='fel', nodvandig=True, detalj='.venv svarar inte'))
    else:
        avvik = sorted(set('%s %s≠%s' % (n, frys.get(n), v) for n, v in las_.items() if frys.get(n) != v)
                       | set('%s (utanför låset)' % n for n in frys if n not in las_))
        ut.append(rad('pip:miljo', 'Python', '.venv mot låset', 'pip-miljo', installerat='%d paket' % len(frys), nodvandig=False,
                      resultat='ok' if not avvik else 'fel', detalj='samma som requirements-lock.txt' if not avvik else
                      'avviker: %s (installera med .venv/bin/python -m pip install -r requirements-lock.txt)' % ', '.join(avvik[:6])))
    for namn, pin in sorted(las_krav(krav).items()):
        info, t, f = uppslag(k, 'pypi:' + namn, lambda n=namn: pypi_versioner(n), avtryck='v2')
        v, karens = ny_info(info)
        r = rad('pip:' + namn, 'Python', namn, 'pip', installerat=pin, senaste=v, kontrollerad=t, kalla='PyPI ' + namn, uppslagsfel=f,
                i_karens=karens)
        r['kandidater'] = kandidater_for(pin, info)
        ut.append(r)
    return ut


def brew_prefix():
    b = shutil.which('brew')
    return Path(b).parent.parent if b else Path('/opt/homebrew')


def brew_aktiv(formel):
    """Den aktiva versionen av en formel, lokalt och utan nät: målet för opt-länken (…/opt/<formel> → ../Cellar/<formel>/<version>)."""
    try:
        return Path(os.readlink(brew_prefix() / 'opt' / formel)).name
    except OSError:
        return None


def node_formel_ur_vag():
    """Formeln för den node som PATH ger, ur sökvägen (…/Cellar/node@22/22.23.2/bin/node), utan att starta node: en node
    med trasiga bibliotekslänkar kan krascha och hänga (2026-10-06), så länkprovet får aldrig börja med att köra den."""
    b = shutil.which('node')
    m = re.search(r'/Cellar/(node(?:@\d+)?)/([^/]+)/', os.path.realpath(b)) if b else None
    return m.group(1) if m else None


def node_formel():
    """(formel, version) för den länkade node, ur sökvägen (…/Cellar/node@22/22.23.2/bin/node)."""
    b = shutil.which('node')
    if not b:
        return None, None
    m = re.search(r'/Cellar/(node(?:@\d+)?)/([^/]+)/', os.path.realpath(b))
    v = version_av([b, '--version'])
    return (m.group(1) if m else None), v


def node_pinnad(formel):
    """PATH-posten som pinnar en versionsformel (…/opt/node@22/bin före /opt/homebrew/bin), eller None. Då följer `node`
    den formeln oavsett vad som är länkat, och en ny huvudversion tas in först när ägaren bytt raden (fynd 6)."""
    if not formel or '@' not in formel:
        return None
    for d in os.environ.get('PATH', '').split(':'):
        if re.search(r'/opt/%s/bin/?$' % re.escape(formel), d) or re.search(r'/Cellar/%s/[^/]+/bin/?$' % re.escape(formel), d):
            return d
    return None


def node_aldre_an_karens(version, mal):
    """Är Node-versionen (Homebrews, utan revision) utgiven för minst KARENS_DAGAR sedan, enligt Nodes versionslista?"""
    d = ((mal or {}).get('datum') or {}).get(str(version).split('_')[0])
    return bool(d) and time.time() - iso_s(d + 'T00:00:00+00:00') >= KARENS_DAGAR * 86400


def inv_brew(k):
    ut = []
    formel, inst = node_formel()
    inst = (brew_aktiv(formel) if formel else None) or inst  # Homebrews version med revision (22.23.3_1), jämförbar med brew info
    mal, tid, fel = uppslag(k, 'node-mal', node_lts_vercel)
    r = rad('brew:node', 'Homebrew', 'node', 'brew-node', formel=formel, installerat=inst, kontrollerad=tid, nodvandig=True,
            kalla='Homebrew; regeln: senaste LTS som Vercel stöder (%s)' % ('%s.x' % mal['major'] if mal else 'okänd'), uppslagsfel=fel,
            mal=mal)
    r['pinnad'] = node_pinnad(formel)
    if mal and inst:
        mal_formel = 'node@%d' % mal['major']
        bi, _t, _f = uppslag(k, 'brew:' + mal_formel, lambda f=mal_formel: brew_info(f))
        if bi:
            r['senaste'] = '%s (%s)' % (bi['senaste'], mal_formel)
            if huvud(bi['senaste']) != huvud(inst) and huvud(bi['senaste']) > (huvud(inst) or 0):
                if node_aldre_an_karens(bi['senaste'], mal):
                    r['kandidater'].append({'version': bi['senaste'], 'formel': mal_formel, 'huvudversion': True})
                else:
                    r['i_karens'] = bi['senaste']
        if formel:
            egen, _t, _f = uppslag(k, 'brew:' + formel, lambda f=formel: brew_info(f))
            kand, noter = brew_kandidat(k, formel, inst, (egen or {}).get('senaste'))
            r.update(noter)
            if kand and kand['huvudversion']:  # en oversionerad node: huvudversioner tas in som node@NN (granskningen av r72)
                r['hall_skal'] = '%s skulle byta huvudversion på plats; en ny huvudversion tas in som node@NN efter LTS-regeln' % kand['version']
            elif kand:
                r['kandidater'].append(kand)
        if not formel:
            r['detalj'] = 'node kommer inte från Homebrew (%s); uppdateras där' % os.path.realpath(shutil.which('node') or '')
            r['kandidater'] = []
    ut.append(r)
    for f in BREW_FORMLER:
        bi, tid, fel = uppslag(k, 'brew:' + f, lambda f_=f: brew_info(f_))
        inst = brew_aktiv(f)
        r = rad('brew:' + f, 'Homebrew', f, 'brew', formel=f, installerat=inst, senaste=(bi or {}).get('senaste'), kontrollerad=tid,
                kalla='Homebrew ' + f, nodvandig=f in ('python@3.12', 'git'), uppslagsfel=fel)
        kand, noter = brew_kandidat(k, f, inst, (bi or {}).get('senaste'))  # en ny huvudversion (git 3, gh 3) prövas med hela rökprovet
        r.update(noter)
        if noter.get('index_gammalt'):
            r['senaste'] = noter['index_gammalt']
        if kand:
            r['kandidater'].append(kand)
        ut.append(r)
    return ut


def motor_hem():
    return Path.home() / '.impeccable' / 'bin'


def inv_motor(k):
    import detektor
    try:
        onskad = (detektor.SKILL / 'scripts' / 'VERSION').read_text().strip()
    except OSError:
        onskad = None
    hem = motor_hem()
    installerade = sorted((p.parent.name for p in hem.glob('*/impeccable') if os.access(p, os.X_OK)), key=versionstal)
    aktiv = detektor.motor()
    senaste, tid, fel = uppslag(k, 'motor:releaser', motor_releaser)
    r = rad('motor:impeccable', 'mätinstrument', 'Impeccables motor', 'motor', installerat=aktiv.parent.name if aktiv else None,
            senaste=senaste, kontrollerad=tid, kalla='github.com/pbakaus/impeccable (releaser engine-v*); skillen pinnar %s' % (onskad or '?'),
            matinstrument=True, uppslagsfel=fel, onskad=onskad, installerade=installerade)
    if onskad and onskad not in installerade:
        r['kandidater'].append({'version': onskad, 'huvudversion': False, 'text': 'skillens pinnade version'})
    elif senaste and onskad and nyare(senaste, onskad):
        r['detalj'] = 'motorn %s finns; skillen pinnar %s och följer med när skillen uppdateras' % (senaste, onskad)
    ut = [r]
    return ut


def inv_system(k):
    """macOS, Xcode-verktygen och Homebrew självt: redovisas bara (lösenord eller omstart)."""
    mac = kor(['sw_vers', '-productVersion'])[1].strip() or None
    m = re.search(r'version: (\S+)', kor(['pkgutil', '--pkg-info=com.apple.pkg.CLTools_Executables'])[1])
    brew = re.search(r'Homebrew (\S+)', kor(['brew', '--version'], env=miljo(BREW_MILJO))[1])
    lista, tid, fel = uppslag(k, 'softwareupdate', softwareupdate_lista)
    brew_s, btid, bfel = uppslag(k, 'brew:release', brew_senaste_release)
    skal = 'redovisas bara: kräver lösenord eller omstart'
    ut = []
    for id_, namn, inst, monster in (('system:macos', 'macOS', mac, r'macos'), ('system:clt', 'Xcode-verktygen', m.group(1) if m else None, r'command line tools')):
        vant = [x for x in lista or [] if re.search(monster, x, re.I)]
        ut.append(rad(id_, 'system', namn, 'system', installerat=inst, senaste=vant[0] if vant else ('ingen väntande uppdatering' if lista is not None else None),
                      kontrollerad=tid, uppslagsfel=fel, system_resultat='behallen' if vant else ('ok' if lista is not None else 'okand'),
                      detalj=('%s väntar; %s' % (vant[0], skal)) if vant else skal))
    bi = brew.group(1) if brew else None
    ut.append(rad('system:homebrew', 'system', 'Homebrew', 'system', installerat=bi, senaste=brew_s, kontrollerad=btid, uppslagsfel=bfel,
                  system_resultat='behallen' if bi and brew_s and nyare(brew_s, bi) else ('ok' if bi and brew_s else 'okand'), detalj=skal))
    return ut


def inventera(k, delar=None):
    delar = delar or ('globala', 'skills', 'sajt', 'instrument', 'python', 'brew', 'motor', 'system')
    fn = {'globala': inv_globala, 'skills': inv_skills, 'sajt': inv_sajt, 'instrument': inv_instrument, 'python': inv_python,
          'brew': inv_brew, 'motor': inv_motor, 'system': inv_system}
    ut = []
    for d in delar:
        try:
            ut += fn[d](k)
        except Exception as e:  # noqa: BLE001 — en del som faller blir en okänd rad, aldrig tystnad
            ut.append(rad('fel:' + d, d, 'inventeringen av %s' % d, 'fel', resultat='okand', detalj='%s: %s' % (type(e).__name__, sista(e, 200))))
    return ut


def bedom(r, avvisade, underhall_tid=None):
    """Sätter resultat och detalj på en inventeringsrad: ok, behallen (nyare väntar på underhållets prov), avvisad (nyare
    prövad och avvisad, med felet), okand eller fel."""
    if r.get('resultat'):
        return r
    if r.get('typ') == 'system':  # redovisas bara, men ett gammalt eller fallet uppslag är okänt också här (granskningen av r72)
        if r.get('uppslagsfel') or not r.get('kontrollerad') or alder(r['kontrollerad']) > GILTIGHET['underhall_aldst']:
            r['resultat'] = 'okand'
            r['detalj'] = '%s; uppslaget %s' % (r.get('detalj') or '', r.get('uppslagsfel') or ('gjordes %s' % r['kontrollerad'] if r.get('kontrollerad') else 'saknas'))
        else:
            r['resultat'] = r.get('system_resultat') or 'okand'
        return r
    if not r.get('installerat'):
        r['resultat'] = 'fel' if r.get('nodvandig') else 'okand'
        r.setdefault('detalj', 'inte installerad eller svarar inte')
        return r
    if not r.get('senaste') and not r['kandidater']:
        r['resultat'] = 'okand'
        r.setdefault('detalj', 'senaste versionen okänd: %s' % (r.get('uppslagsfel') or 'inte uppslagen'))
        return r
    if r.get('uppslagsfel'):  # ett uppslag som föll är okänt, också när ett äldre värde finns (fynd 9)
        r['resultat'] = 'okand'
        r['detalj'] = 'senaste uppslaget föll: %s' % r['uppslagsfel']
        return r
    if r.get('kontrollerad') and alder(r['kontrollerad']) > GILTIGHET['underhall_aldst']:
        r['resultat'] = 'okand'  # ett gammalt uppslag säger inget om nuläget (fynd 9)
        r['detalj'] = 'senaste uppslaget gjordes %s, äldre än %d timmar: underhållet slår upp på nytt' % (r['kontrollerad'], GILTIGHET['underhall_aldst'] // TIMME)
        return r
    if not r['kandidater'] and r.get('i_karens'):
        r['resultat'] = 'behallen'
        r['detalj'] = '%s finns men är yngre än karenstiden (%g dygn); prövas när den gått ut' % (r['i_karens'], KARENS_DAGAR)
        return r
    if not r['kandidater'] and r.get('hall_skal'):  # behållen av ett skäl som inventeringen redan vet (granskningen av r73, N7)
        r['resultat'] = 'behallen'
        r['detalj'] = r['hall_skal']
        return r
    if not r['kandidater'] and r.get('index_gammalt'):
        r['resultat'] = 'behallen'
        r['detalj'] = ('%s finns (formulae.brew.sh), men Homebrews formelindex här känner inte till den: brew update behövs först, och '
                       'den uppdaterar Homebrew självt, som bara redovisas' % r['index_gammalt'])
        return r
    if not r['kandidater']:
        r['resultat'] = 'ok'
        r.setdefault('detalj', 'senaste versionen' + ('' if not r.get('ofullstandigt') else ' (för de paket som kunde slås upp)'))
        if r.get('ofullstandigt'):
            r['resultat'] = 'okand'
        return r
    for kand in r['kandidater']:
        a = avvisad(avvisade, r['id'], kand['version'])
        if a:
            continue
        nar = ('underhållet senast %s' % underhall_tid) if underhall_tid else 'underhållet har inte körts'
        r['resultat'] = 'behallen'
        r['detalj'] = '%s%s finns; prövas i underhållet (%s)' % (kand['version'], ' (huvudversion, med hela rökprovet)' if kand.get('huvudversion') else '', nar)
        if kand.get('ojamfort'):
            r['detalj'] = 'källan har nyare commits (%s); underhållet har inte jämfört mappen än (%s)' % (kand['version'][:12], nar)
        return r
    a = avvisad(avvisade, r['id'], r['kandidater'][0]['version'])
    r['resultat'] = 'avvisad'
    r['detalj'] = '%s avvisades %s: %s; prövas igen när en nyare version kommer' % (r['kandidater'][0]['version'], a.get('tid'), a.get('fel'))
    return r


# --- pågående körningar ---

def pagaende(egna=None):
    """Körningar som pågår: på hela maskinen ur körregistret (kontroller/korregister.py: arbetare, kor.sh och rokprov.sh i
    alla utcheckningar; fynd 3), och i den här utcheckningen ateljéns arbetare och helbygget. Ingen uppdatering får ändra
    deras miljö."""
    import atelje
    import korregister
    egna = set(egna or ()) | {os.getpid(), os.getppid()}
    poster_ = [d for d in korregister.poster() if int(d['pid']) not in egna]
    egna |= {int(d['pid']) for d in poster_}  # samma körning räknas en gång
    ut = ['%s%s (pid %d, %s)' % (d['vad'], (' ' + d['slug']) if d.get('slug') else '', d['pid'], d.get('utcheckning') or '?') for d in poster_]
    for f in sorted(UNDERLAG.glob('*/atelje/STATUS.json')):
        slug = f.parent.parent.name
        try:
            pid = int((las_json(f, {}) or {}).get('pid'))
        except (TypeError, ValueError):
            continue
        if pid not in egna and atelje.lever(pid) and atelje.ar_arbetare(pid, slug):
            ut.append('%s (arbetaren, pid %d)' % (slug, pid))
    try:
        bp = int((KUNDER / '.bygge-pid').read_text().strip())
        if bp not in egna and atelje.lever(bp):
            ut.append('helbygget (kor.sh, pid %d)' % bp)
    except (OSError, ValueError):
        pass
    return ut


# --- förmågeproven (små; återanvänds medan förutsättningarna är oförändrade) ---

def claude_bin():
    return os.environ.get('NWP_CLAUDE_BIN') or shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')


def flaggor_saknas(b, env=None):
    rc, ut = kor([b, '--help'], timeout=60, env=env)
    return [f for f in FLAGGOR if f not in ut] if rc == 0 else list(FLAGGOR)


def modellsvar(b, modell, timeout=240, schema=False, env=None):
    """Ett kort svar ur modellen genom claude-binären b (prenumerationen, utan verktyg och MCP): None när svaret kom,
    annars felet. schema=True prövar också strukturerat svar (--json-schema), som flödet bygger på. env: en kandidat
    prövas med provmiljön (underhall.prova_globalt)."""
    import nastlad
    args = [b, '-p', '--max-turns', '3', '--model', modell, '--output-format', 'json', '--setting-sources', 'project,local',
            '--strict-mcp-config', '--tools', '', '--permission-mode', 'dontAsk']
    if schema:
        args += ['--json-schema', json.dumps({'type': 'object', 'required': ['svar'], 'additionalProperties': False,
                                              'properties': {'svar': {'type': 'string'}}})]
    try:
        r = subprocess.run([str(a) for a in args], input='Svara med ordet OK och inget annat.' + (' Lägg det i fältet svar.' if schema else ''),
                           capture_output=True, text=True, timeout=timeout, cwd=str(ROOT), env=env or nastlad.miljo())
    except subprocess.TimeoutExpired:
        return 'inget svar inom %d s' % timeout
    except OSError as e:
        return str(e)
    try:
        d = json.loads(r.stdout or '{}')
    except ValueError:
        return 'oläsbart svar (kod %d): %s' % (r.returncode, sista(r.stderr or r.stdout, 200))
    text = str((d.get('structured_output') or {}).get('svar') if schema else d.get('result'))
    if r.returncode or d.get('is_error') or 'OK' not in text.upper():
        return 'svarade inte som väntat (kod %d): %s' % (r.returncode, sista(d.get('result') or r.stderr, 200))
    return None


VAKTKROK = """import json, sys
d = json.load(sys.stdin)
p = str((d.get('tool_input') or {}).get('file_path', ''))
if p.endswith('tillaten.txt'):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow', 'permissionDecisionReason': 'vaktprovet'}}))
"""


def vaktprov(b, modell=PROVMODELL, timeout=300, env=None):
    """Prövar den mekanik kundvakten bygger på (fynd 11): utan tillåtelselista och med dontAsk får sessionen skriva en fil
    som en PreToolUse-krok uttryckligen tillåter, och nekas en fil som kroken lämnar utan beslut. None när det håller,
    annars felet."""
    import nastlad
    with tempfile.TemporaryDirectory(prefix='nwp-vaktprov-') as d:
        d = Path(d).resolve()
        (d / 'krok.py').write_text(VAKTKROK, encoding='utf-8')
        inst = {'hooks': {'PreToolUse': [{'matcher': 'Write', 'hooks': [{'type': 'command', 'timeout': 30,
                                                                         'command': '%s %s' % (sys.executable, d / 'krok.py')}]}]}}
        args = [b, '-p', '--model', modell, '--max-turns', '6', '--output-format', 'stream-json', '--verbose', '--setting-sources', 'project,local',
                '--strict-mcp-config', '--permission-mode', 'dontAsk', '--settings', json.dumps(inst), '--tools', 'Write']
        prompt = ('Använd verktyget Write två gånger: skriv texten ALFA i filen %s och sedan texten BETA i filen %s. Svara sedan '
                  'kort vilka skrivningar som gick igenom.' % (d / 'tillaten.txt', d / 'nekad.txt'))
        try:
            r = subprocess.run([str(a) for a in args], input=prompt, capture_output=True, text=True, timeout=timeout, cwd=str(d),
                               env=env or nastlad.miljo())
        except subprocess.TimeoutExpired:
            return 'inget svar inom %d s' % timeout
        except OSError as e:
            return str(e)
        tillaten = (d / 'tillaten.txt').read_text(encoding='utf-8').strip() if (d / 'tillaten.txt').is_file() else None
        if tillaten != 'ALFA':
            return 'krokens uttryckliga tillåtelse släppte inte igenom skrivningen (kod %d): %s' % (r.returncode, sista(r.stdout or r.stderr, 160))
        if (d / 'nekad.txt').exists():
            return 'dontAsk nekade inte en skrivning som kroken lämnade utan beslut: kundvakten skulle inte hålla'
        forsokt = False  # ett prov där modellen aldrig försökte skriva den nekade filen bevisar inget
        for rad_ in (r.stdout or '').splitlines():
            try:
                h = json.loads(rad_)
            except ValueError:
                continue
            for c in ((h.get('message') or {}).get('content') or []) if h.get('type') == 'assistant' else []:
                if isinstance(c, dict) and c.get('type') == 'tool_use' and str((c.get('input') or {}).get('file_path', '')).endswith('nekad.txt'):
                    forsokt = True
        if not forsokt:
            return 'provet ofullständigt: modellen försökte aldrig skriva den fil som skulle nekas'
        return None


def prova_vakten(k):
    """Vaktprovet för den installerade claude, återanvänt per version (ett dygn)."""
    version = version_av([claude_bin(), '--version'])
    x = k.minns('prov:vakt', str(version), GILTIGHET['prov'])
    if x:
        return dict(x, ateranvant=True)
    if not k.prova:
        return {'resultat': 'okand', 'detalj': 'inte provad (utan prov)'}
    fel = vaktprov(claude_bin())
    return k.spara('prov:vakt', str(version), resultat='fel' if fel else 'ok',
                   detalj=fel or 'krokens tillåtelse släpper igenom och dontAsk nekar resten (kundvaktens mekanik)')


def prova_refero(k, prov_dir):
    """Autentisering, verktygslistan, stilsökning, stilhämtning och bildleverans, direkt utan modell. Ger dict."""
    import refero_mcp
    try:
        avtryck = sha(refero_mcp.nyckel())[:16]
    except refero_mcp.ReferoFel as e:
        return {'resultat': 'fel', 'detalj': str(e), 'tid': nu()}
    x = k.minns('prov:refero', avtryck, GILTIGHET['prov'])
    if x:
        return dict(x, ateranvant=True)
    if not k.prova:
        return {'resultat': 'okand', 'detalj': 'inte provad (utan prov)'}
    try:
        kl = refero_mcp.Klient()
        kl.starta()
        verktyg = kl.verktyg()
        stilar = kl.json('refero_search_styles', {'query': 'editorial craft workshop website'}).get('records') or []
        if not stilar:
            raise refero_mcp.ReferoFel('stilsökningen gav inga träffar')
        stil = kl.json('refero_get_style', {'style_id': stilar[0]['uuid']})
        if not stil.get('colors') or not stil.get('typography'):
            raise refero_mcp.ReferoFel('stilen saknar färger eller typografi')
        bild = refero_mcp.ladda_bild(stilar[0]['preview_url'], Path(prov_dir) / 'refero-forhandsbild')
        res, detalj = 'ok', 'sökning, stil (%d färger, %d typsnitt) och bild (%d byte) fungerar' % (len(stil['colors']), len(stil['typography']), bild.stat().st_size)
    except Exception as e:  # noqa: BLE001
        verktyg, res, detalj = [], 'fel', sista(e, 200)
    return k.spara('prov:refero', avtryck, resultat=res, detalj=detalj, verktyg=verktyg)


def mobbin_bevis(max_alder):
    """Ett färskt resultat ur en riktig körning: Mobbin ok med levererade bilder (referenser/tjanster/TJANSTER.json)."""
    bast = None
    for f in UNDERLAG.glob('*/referenser/tjanster/TJANSTER.json'):
        d = las_json(f, {}) or {}
        m = (d.get('tjanster') or {}).get('mobbin') or {}
        if m.get('ok') and m.get('bilder') and not d.get('torr') and alder(d.get('tid')) < max_alder:
            if not bast or d['tid'] > bast['tid']:
                bast = {'tid': d['tid'], 'slug': f.parent.parent.parent.name, 'bilder': m.get('bilder')}
    return bast


MOBBIN_PROVFRIST = 300  # s: startens prov väntar aldrig längre (granskningen av r73, N4)


def prova_mobbin(k, ansluten=None, frist=None):
    """Mobbins sökning och bildleverans genom flödets egen tjänstesession på ett fiktivt provunderlag (en liten
    Sonnet-session; i starten högst frist=MOBBIN_PROVFRIST, i underhållet sessionens vanliga gräns), eller ett färskt
    resultat ur en riktig körning. ansluten=False (claude mcp
    list visar att Mobbin inte ansluter): inget nytt prov, eftersom starten ändå stoppas på anslutningen."""
    b = mobbin_bevis(GILTIGHET['mobbin'])
    if b:
        return {'resultat': 'ok', 'tid': b['tid'], 'detalj': 'sökning och %d bilder i en riktig körning (%s)' % (b['bilder'], b['slug']), 'ateranvant': True}
    x = k.minns('prov:mobbin', 'v1', GILTIGHET['mobbin'])
    if x:
        return dict(x, ateranvant=True)
    if not k.prova or ansluten is False:
        gammal = k.senast_kanda('prov:mobbin')
        return dict(gammal, ateranvant=True, gammalt=True) if gammal else {'resultat': 'okand', 'detalj': 'inget fullständigt prov än (underhållet gör det)'}
    import referenstjanster
    u = k.katalog / 'provunderlag'
    (u / 'startprov').mkdir(parents=True, exist_ok=True)
    (u / 'startprov' / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provfirman Startkontroll AB', 'kategorier': ['Byggfirma'],
                                                                 'adress': {'ort': 'Provby'}}), encoding='utf-8')
    try:
        _rot, res = referenstjanster.samla('startprov', {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form for a local service business',
                                                                      'syfte': 'underhållets prov', 'typ': 'skarm'}]}, underlag=u,
                                           kor=(lambda t, p, l, m: referenstjanster.kor_session(t, p, l, m, frist=frist)) if frist else
                                           referenstjanster.kor_session)
        m = (res.get('tjanster') or {}).get('mobbin') or {}
        ok = bool(m.get('ok') and m.get('bilder'))
        detalj = ('sökning och %d bilder levererade (provunderlag)' % m.get('bilder')) if ok else 'gav inga bilder: %s' % sista('; '.join(m.get('anmarkningar') or []), 200)
    except Exception as e:  # noqa: BLE001
        ok, detalj = False, '%s: %s' % (type(e).__name__, sista(e, 160))
    return k.spara('prov:mobbin', 'v1', resultat='ok' if ok else 'fel', detalj=detalj)


def webblasar_avtryck(node_modules=None):
    """Webbläsarprovets förutsättningar: Playwrights version, webbläsarna och inspektionsverktyget. Ändras något av dem
    görs provet om."""
    nm = Path(node_modules or ROOT / 'kontroller' / 'node_modules')
    return sha('%s|%s|%s' % (installerat_i(nm, 'playwright'), webblasare(nm), sha_fil(ROOT / 'kontroller' / 'webblasare' / 'inspektera.mjs')))


def prova_webblasaren(k, prov_dir, node_modules=None):
    """En sida öppnas, renderas och inspekteras med flödets eget verktyg (kontroller/webblasare/inspektera.mjs)."""
    import prova as prova_mod
    avtryck = webblasar_avtryck(node_modules)
    x = k.minns('prov:webblasare', avtryck, GILTIGHET['prov'])
    if x:
        return dict(x, ateranvant=True)
    if not k.prova:
        return {'resultat': 'okand', 'detalj': 'inte provad (utan prov)'}
    sajt = Path(prov_dir) / 'sida'
    sajt.mkdir(parents=True, exist_ok=True)
    (sajt / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Startprov</title></head>'
                                     '<body><main><h1>Startkontrollens prov</h1><p>En sida som öppnas och inspekteras.</p></main></body></html>')
    ut = Path(prov_dir) / 'inspektion'
    shutil.rmtree(ut, ignore_errors=True)
    try:
        with prova_mod.Server(sajt) as srv:
            rc, out = kor(['node', ROOT / 'kontroller' / 'webblasare' / 'inspektera.mjs', '--adress', srv.url + '/', '--ut', ut,
                           '--vyer', '390', '--tillstand', 'inga'], timeout=300)
        vy = ((las_json(ut / 'INSPEKTION.json', {}) or {}).get('vyer') or {}).get('390') or {}
        ok = rc == 0 and vy.get('status') == 200 and (ut / 'vy-390-forsta.png').is_file() and vy.get('h1') == 1
        detalj = 'sidan öppnades (200), renderades och inspekterades' if ok else 'inspektionen föll (kod %s): %s' % (rc, sista(out, 200))
    except Exception as e:  # noqa: BLE001
        ok, detalj = False, '%s: %s' % (type(e).__name__, sista(e, 160))
    return k.spara('prov:webblasare', avtryck, resultat='ok' if ok else 'fel', detalj=detalj)


def prova_detektorn(k, prov_dir):
    import detektor
    m = detektor.motor()
    if not m:
        return {'resultat': 'fel', 'detalj': 'motorn saknas (~/.impeccable/bin)'}
    x = k.minns('prov:detektor', str(m), GILTIGHET['prov'])
    if x:
        return dict(x, ateranvant=True)
    if not k.prova:
        return {'resultat': 'okand', 'detalj': 'inte provad (utan prov)'}
    f = Path(prov_dir) / 'detektor.html'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('<!doctype html><html><head><style>body{font-family:Inter}</style></head><body><h1>Prov</h1></body></html>')
    fynd, fel = detektor.detektera(f)
    return k.spara('prov:detektor', str(m), resultat='ok' if fynd is not None else 'fel',
                   detalj=('motorn %s svarade (%d fynd på provsidan)' % (m.parent.name, len(fynd))) if fynd is not None else fel)


def mcp_lista(k):
    """{namn: {'status', 'besked'}} ur `claude mcp list`, eller None; cachad i fem minuter (GILTIGHET['mcp']). Listan läser
    användarens konfiguration, inte bara våra filer, så det är tiden som gör att en server som faller syns (fynd 14)."""
    avtryck = sha('|'.join(sorted('%s:%s' % (p.name, sha_fil(p)) for p in (ROOT / 'kontroller' / 'mcp').glob('*.json'))))
    x = k.minns('mcp:lista', avtryck, GILTIGHET['mcp'])
    if x:
        return x['servrar'], x['tid']
    if not k.prova:
        return None, None
    rc, ut = kor([claude_bin(), 'mcp', 'list'], timeout=180)
    servrar = {}
    for r in ut.splitlines():
        m = re.match(r'^(.+?): (.+) - (✔|✓|!|✗|×)\s*(.*)$', r.strip())
        if m:
            ok = m.group(3) in '✔✓' and 'fail' not in m.group(4).lower()
            servrar[m.group(1).strip()] = {'status': 'ok' if ok else 'fel', 'besked': m.group(4).strip()[:120]}
    if not servrar:
        return None, None
    x = k.spara('mcp:lista', avtryck, servrar=servrar)
    return servrar, x['tid']
