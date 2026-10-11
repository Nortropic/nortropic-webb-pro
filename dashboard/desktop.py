"""desktop.py — motorns sida av kontraktet `desktop/1` för Nortropic.app (kunskap/desktop.md).

Identiteten: appen skickar en slumpad utmaning och motorn svarar med HMAC-SHA256(dashboardnyckeln, utmaningen, instansen,
roten, pid, porten, commit), så att appen kan pröva att den talar med rätt motor innan den skickar nyckeln (RFC 2104;
ingen egen kryptografi). Svaret lämnar aldrig ut nyckeln.

Sessionen: appen hämtar med nyckeln (native, aldrig i renderern) en engångskod som gäller i 60 sekunder; motorns
inloggningsväg byter koden mot en slumpad session i en HttpOnly-kaka med SameSite=Strict. Kakan gäller skrivningar
bara tillsammans med samma ursprung (Origin lika med http://<Host>) och Sec-Fetch-Site same-origin, så en
förhandsvisad sajt på en annan port i samma värd aldrig kan skriva som ägaren. Sessionerna lever i minnet: en omstartad
motor har inga, och låset eller utloggningen återkallar dem. Strömmarna som öppnats med en session stängs när den
återkallas.

Översikten, uppmärksamheten och det pågående arbetet räknas fram ur det som redan finns (arbetsytans projekt,
Kundstarts ärenden, flödets kundlägen och körregistret). Ingen egen status, ingen modell.
"""
import hashlib
import hmac
import json
import re
import os
import secrets
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

KONTRAKT = 'desktop/1'
KAKA = 'nwp_session_%d'
KOD_TID = 60
SESSION_TID = 12 * 3600  # högst en arbetsdag; låset och utloggningen återkallar tidigare
SESSION_TOMGANG = 2 * 3600

INSTANS = secrets.token_hex(16)
STARTAD = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
_LAS = threading.Lock()
_KODER = {}       # kod -> utgång
_SESSIONER = {}   # sid -> {'skapad', 'senast'}
_KONF = {'rot': None, 'port': None, 'commit': None}
_CACHE = {}


def _git(rot, *a):
    try:
        return subprocess.run(['/usr/bin/git', '-C', str(rot), *a], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ''


def konfigurera(rot, port):
    _KONF['rot'] = str(Path(rot).resolve())
    _KONF['port'] = int(port)
    _KONF['commit'] = _git(rot, 'rev-parse', 'HEAD')


def ui_version(dashkatalog):
    """Hash över gränssnittets filer så som de serveras nu (servern läser dem från disk vid varje anrop): samma lista som
    serverns statiska filer, så att en ändring i studion eller kirurgens vy också ger appen en ny version."""
    h = hashlib.sha256()
    for namn in ('index.html', 'arbetsyta.js', 'arbetsyta.css', 'studio.js', 'studio.css', 'andringar.js', 'andringar.css', 'repovaljare.js', 'repovaljare.css', 'kompetenskarta.js', 'kompetenskarta.css', 'kundstart-agare.js',
                 'kundstart-agare.css', 'kirurg-forbattring.js', 'portal.js', 'portal.css', 'vendor/xterm/xterm.js', 'vendor/xterm/xterm.css',
                 'vendor/xterm/addon-fit.js'):
        p = Path(dashkatalog) / namn
        try:
            h.update(namn.encode() + b'\0' + p.read_bytes())
        except OSError:
            h.update(namn.encode() + b'\0-')
    return h.hexdigest()[:16]


def identitet(utmaning, nyckel, dashkatalog):
    if not (isinstance(utmaning, str) and 32 <= len(utmaning) <= 128 and all(c in '0123456789abcdef' for c in utmaning)):
        raise ValueError('utmaningen ska vara 32–128 hextecken')
    rot, port, commit = _KONF['rot'], _KONF['port'], _KONF['commit'] or ''
    pa_disk = _git(rot, 'rev-parse', 'HEAD')
    pid = os.getpid()
    meddelande = 'nwp-desktop/1\n%s\n%s\n%s\n%d\n%d\n%s' % (utmaning, INSTANS, rot, pid, port, commit)
    bevis = hmac.new((nyckel or '').encode(), meddelande.encode(), hashlib.sha256).hexdigest()
    return {'kontrakt': KONTRAKT, 'instans': INSTANS, 'rot': rot, 'pid': pid, 'port': port,
            'version': {'commit': commit, 'commit_pa_disk': pa_disk, 'utdaterad': bool(pa_disk and commit and pa_disk != commit),
                        'ui': ui_version(dashkatalog), 'startad': STARTAD},
            'stod': {'arbetsyta': 'arbetsyta/1'}, 'bevis': bevis}


_NONCER = {}  # nonce -> tid, för appens bevisade skrivningar (en nonce gäller en gång)
BEVIS_FONSTER = 120


def bevis_ok(huvud, vag, kropp, nyckel):
    """Appens skrivning till /api/desktop/session och /las bevisas med HMAC-SHA256(nyckeln, tid, nonce, väg, kroppens
    sha256) i X-Desktop-Bevis, så att nyckeln själv aldrig skickas över en anslutning. Tiden högst BEVIS_FONSTER sekunder
    bort, och varje nonce en gång."""
    try:
        ts, nonce, mac = (huvud or '').split('.', 2)
        t = int(ts)
    except ValueError:
        return False
    if not nyckel or abs(time.time() - t) > BEVIS_FONSTER or not (16 <= len(nonce) <= 64 and all(c in '0123456789abcdef' for c in nonce)):
        return False
    msg = 'nwp-desktop/1 skriv\n%s\n%s\n%s\n%s' % (ts, nonce, vag, hashlib.sha256(kropp or b'').hexdigest())
    if not hmac.compare_digest(mac, hmac.new(nyckel.encode(), msg.encode(), hashlib.sha256).hexdigest()):
        return False
    with _LAS:
        nu = time.time()
        for k in [k for k, v in _NONCER.items() if nu - v > 2 * BEVIS_FONSTER]:
            del _NONCER[k]
        if nonce in _NONCER:
            return False
        _NONCER[nonce] = nu
    return True


def ny_kod(instans):
    if instans != INSTANS:
        raise ValueError('koden gäller en annan instans av motorn')
    kod = secrets.token_urlsafe(32)
    with _LAS:
        nu = time.time()
        for k in [k for k, t in _KODER.items() if t < nu]:
            del _KODER[k]
        _KODER[kod] = nu + KOD_TID
    return {'kod': kod, 'giltig_s': KOD_TID}


def los_in(kod):
    """Engångskoden mot en ny session; en använd, okänd eller utgången kod ger None."""
    with _LAS:
        t = _KODER.pop(kod or '', None)
        if not t or t < time.time():
            return None
        sid = secrets.token_urlsafe(32)
        _SESSIONER[sid] = {'skapad': time.time(), 'senast': time.time()}
        return sid


def giltig(sid, rora=True):
    if not sid:
        return False
    with _LAS:
        s = _SESSIONER.get(sid)
        nu = time.time()
        if not s or nu - s['skapad'] > SESSION_TID or nu - s['senast'] > SESSION_TOMGANG:
            _SESSIONER.pop(sid, None)
            return False
        if rora:
            s['senast'] = nu
        return True


def aterkalla(sid=None):
    """En session (utloggningen) eller alla (appens lås)."""
    with _LAS:
        if sid:
            _SESSIONER.pop(sid, None)
        else:
            _SESSIONER.clear()
            _KODER.clear()


def kaka_sider(cookie_huvud, port):
    """Alla värden med kakans namn. En förhandsvisad sajt i samma värd kan sätta en kaka med samma namn och längre
    sökväg, som webbläsaren skickar först; därför prövas varje värde, aldrig bara det första."""
    namn = KAKA % int(port)
    ut = []
    for del_ in (cookie_huvud or '').split(';'):
        k, _, v = del_.strip().partition('=')
        if k == namn and v:
            ut.append(v)
    return ut


def kaka_sid(cookie_huvud, port):
    """Den giltiga sessionen bland kakans värden, eller None."""
    return next((v for v in kaka_sider(cookie_huvud, port) if giltig(v, rora=False)), None)


def kaka(sid, port, ta_bort=False):
    if ta_bort:
        return '%s=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0' % (KAKA % int(port))
    # en sessionskaka (ingen Max-Age): den försvinner när appen avslutas, och motorn återkallar sessionen vid avslutet
    return '%s=%s; Path=/; HttpOnly; SameSite=Strict' % (KAKA % int(port), sid)


def session_skriv_ok(headers, port):
    """En skrivning med sessionskakan: samma ursprung exakt och Sec-Fetch-Site same-origin när webbläsaren skickar det."""
    vard = (headers.get('Host') or '').strip().lower()
    if (headers.get('Origin') or '').strip().lower() != 'http://' + vard:
        return False
    sfs = (headers.get('Sec-Fetch-Site') or '').strip().lower()
    if sfs and sfs != 'same-origin':
        return False
    sid = kaka_sid(headers.get('Cookie'), port)
    return giltig(sid) if sid else False


def _cachat(namn, sek, f):
    t, v = _CACHE.get(namn, (0, None))
    if time.time() - t < sek:
        return v
    v = f()
    _CACHE[namn] = (time.time(), v)
    return v


def _iso(t):
    """Kundstarts tider är sekunder sedan epok, arbetsytans ISO-strängar: översikten jämför och visar dem som ISO."""
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return t if isinstance(t, str) else None


def pagaende(rot):
    """Arbete som motorns egen utcheckning kör just nu (körregistret: ateljéns arbetare och helbyggen)."""
    import korregister
    rot = str(Path(rot).resolve())
    ut = []
    for d in korregister.poster(rensa=False):
        if d.get('vad') not in ('arbetare', 'bygge'):
            continue
        utch = d.get('utcheckning')
        if utch and str(Path(utch).resolve()) != rot:
            continue
        ut.append({'slug': d.get('slug'), 'vad': 'helbygge' if d.get('vad') == 'bygge' else 'skapandeflödet', 'pid': d.get('pid'), 'start': d.get('start')})
    return ut


def oversikt(dash):
    """Startsidans data: kunderna (företagen) med deras ärenden, var de står och nästa handling, skilda från testkunderna.
    Ett företag identifieras av sin slug; Kundstarts ärende och byggprojektet med samma slug är samma kund."""
    import arbetsyta
    import kundstart_agare
    projekt = {p['slug']: p for p in arbetsyta.projekt(dash)}
    try:
        arenden = kundstart_agare.lista(dash.ROOT).get('arenden', [])
    except Exception as e:  # noqa: BLE001 — Kundstarts lager som inte går att läsa fäller inte översikten
        arenden, kfel = [], '%s: %s' % (type(e).__name__, str(e)[:160])
    else:
        kfel = None
    lagen = {k['slug']: k for k in _cachat('kundlagen', 15, dash.kundlagen)}
    vantar = {}
    kunder = {}
    for a in arenden:
        s = a['slug']
        b = a.get('bestallning') or {}
        kunder.setdefault(s, {'slug': s, 'namn': a.get('foretag'), 'test': bool(a.get('fiktiv', True)), 'arenden': [], 'projekt': None})
        kunder[s]['arenden'].append({'id': a['id'], 'uppdaterad': _iso(a.get('uppdaterad')), 'modell': a.get('modell'), 'fragor': a.get('fragor'),
                                     'aktuell_bestallning': bool(b.get('aktuell'))})
    for s, p in projekt.items():
        k = kunder.setdefault(s, {'slug': s, 'namn': None, 'test': False, 'arenden': [], 'projekt': None})
        k['projekt'] = {'senast_andrad': p.get('senast_andrad')}
        k['namn'] = p.get('namn') or k['namn']
        k['test'] = bool(p.get('testdata')) or (k['test'] and not k['arenden'] == [])
    # en levererad webbplats med kundrepo (kunder/<slug>/KUNDREPO.json) är en kund också utan ärende eller projekt: dess
    # ändringar görs i fliken Ändringar (kunskap/andringar.md)
    for p in sorted(dash.KUNDER.glob('*/KUNDREPO.json')) if dash.KUNDER.is_dir() else []:
        s = p.parent.name
        if p.is_symlink() or not re.fullmatch(r'[a-z0-9-]{2,60}', s) or s.endswith('-forhandsvisning'):
            continue
        v = dash.las_json(dash.UNDERLAG / s / 'VERKSAMHET.json') or {}
        k = kunder.setdefault(s, {'slug': s, 'namn': None, 'test': bool(v.get('fiktiv')) if isinstance(v, dict) else False, 'arenden': [], 'projekt': None})
        k['kundrepo'] = True
    for s, k in kunder.items():
        k.setdefault('kundrepo', False)
        if not k['namn']:
            v = dash.las_json(dash.UNDERLAG / s / 'VERKSAMHET.json') or {}
            k['namn'] = v.get('namn') if isinstance(v, dict) else None
        l = lagen.get(s) or {}
        k['vantar'] = l.get('vantar') or []
        k['pagar'] = l.get('pagar') or []
        k['blind'] = bool(l.get('blind') or l.get('ab_dold'))
        tider = [x for x in [((k.get('projekt') or {}).get('senast_andrad'))] + [a.get('uppdaterad') for a in k['arenden']] if x]
        k['senast'] = max(tider) if tider else None
        if k['vantar']:
            k['nasta'] = 'Väntar på dig: ' + ', '.join(k['vantar'][:2])
            vantar[s] = k
        elif k['pagar']:
            k['nasta'] = 'Pågår: ' + ', '.join(k['pagar'][:2])
        elif k['arenden'] and not k['projekt']:
            k['nasta'] = 'Kundintervjun' if not any(a['aktuell_bestallning'] for a in k['arenden']) else 'Omfattningen är accepterad'
        else:
            k['nasta'] = None
        k['vy'] = '#/arbetsyta/' + s if k['projekt'] else ('#/kundstart/' + k['arenden'][0]['id'] if k['arenden'] else '#/andringar/' + s if k['kundrepo'] else '#/arbetsyta/' + s)
        k['senaste'] = k['nasta'] or ''
    lista = sorted(kunder.values(), key=lambda k: (k['senast'] or '', k['slug']), reverse=True)
    return {'tid': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'kunder': lista,
            'uppmarksamhet': [{'slug': k['slug'], 'namn': k['namn'], 'test': k['test'], 'vad': k['vantar'], 'vy': k['vy']} for k in vantar.values()],
            'pagaende': pagaende(dash.ROOT), 'kundstart_fel': kfel}


def uppmarksamhet(dash):
    """Det som väntar på ägaren (för appens avisering): antal och första raden, utan annan kunduppgift."""
    def r():
        import arbetsyta
        test = {p['slug'] for p in arbetsyta.projekt(dash) if p.get('testdata')}
        ut = []
        for k in dash.kundlagen():
            if k.get('vantar') and not k.get('ab_dold') and k['slug'] not in test:
                ut.append('%s: %s' % (k['slug'], ', '.join(k['vantar'][:2])))
        return {'antal': len(ut), 'forsta': ut[0] if ut else None}
    return _cachat('uppmarksamhet', 15, r)


class DubblettKund(ValueError):
    """En kund med samma namn (slug) finns redan: öppna den i stället för att skapa en dubblett. arende är None när den
    befintliga är av det andra slaget (test mot riktig), som aldrig öppnas i stället."""
    def __init__(self, text, arende):
        super().__init__(text)
        self.arende = arende


def _slug(namn):
    import re
    import unicodedata
    s = unicodedata.normalize('NFKD', namn).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:44].strip('-') or 'kund'


def ny_kund(dash, data):
    """P03: det minsta ärendet ur portalen genom Kundstarts egen skapandeväg (samma idempotens: samma operations-id och
    innehåll ger samma ärende; en befintlig kund med samma namn ger DubblettKund med dess ärende). Testmärkningen sätts
    här på servern ur vägens eget fält, och en testkund får en testslug; en riktig kund får ingen modellbudget (AI kräver
    separat aktivering), en testkund tio anrop för syntetiskt material. Webbplatsen och syftet sparas som ägarens
    anteckningar, skilda från kundens egna svar. Inget startas."""
    import re
    import kundstart as ks
    import kundstart_agare
    if not isinstance(data, dict) or set(data) - {'foretag', 'webbplats', 'syfte', 'kontakt', 'test', 'operation'}:
        raise ValueError('okända fält')
    foretag = str(data.get('foretag') or '').strip()
    webb = str(data.get('webbplats') or '').strip()
    syfte = str(data.get('syfte') or '').strip()
    kontakt = str(data.get('kontakt') or '').strip()
    test, operation = data.get('test'), data.get('operation')
    if not 1 <= len(foretag) <= 120:
        raise ValueError('skriv företagets namn eller ett arbetsnamn (högst 120 tecken)')
    if webb and not re.fullmatch(r'https?://[^\s/$.?#][^\s]{1,290}', webb):
        raise ValueError('webbplatsen ska vara en hel adress som börjar med https://')
    if len(syfte) > 2000 or len(kontakt) > 120:
        raise ValueError('för lång text')
    if type(test) is not bool:
        raise ValueError('test ska vara sant eller falskt')
    if not isinstance(operation, str) or not re.fullmatch(r'[0-9a-f-]{36}', operation):
        raise ValueError('operationen ska vara ett UUID')
    grund = _slug(foretag)
    # testkundernas slugar börjar med test-; en riktig kund får aldrig en sådan, så att de två aldrig kan krocka
    slug = ('test-' + grund) if test else (('k-' + grund) if grund.startswith('test-') or grund == 'test' else grund)
    person = kontakt or 'Kontaktperson ej angiven'
    for t in (foretag, webb, syfte, kontakt):  # samma prövning som anteckningarna, före skapandet (en hemlighet nekas)
        if t:
            ks.text(t, 2000)
    try:
        r = kundstart_agare.skapa(dash.ROOT, {'slug': slug, 'namn': person, 'fiktiv': test, 'modellbudget': 10 if test else 0, 'operation': operation})
    except ks.Konflikt as e:
        befintligt = next((a for a in kundstart_agare.lista(dash.ROOT).get('arenden', []) if a['slug'] == slug), None)
        if befintligt and bool(befintligt.get('fiktiv')) == test:
            raise DubblettKund('En kund med det namnet finns redan.', befintligt['id']) from e
        if befintligt:
            raise DubblettKund('Namnet krockar med en %s; välj ett annat arbetsnamn.' % ('riktig kund' if test else 'testkund'), None) from e
        raise
    kundstart_agare.anteckningar(dash.ROOT, r['arende'], operation, [('foretag', foretag), ('webbplats', webb), ('syfte', syfte), ('kontakt', kontakt)])
    return {'arende': r['arende'], 'slug': slug, 'nyckel': r['nyckel'], 'aterforsok': r['aterforsok'], 'test': test}


_AI = {}  # ärende -> Popen för den AI-tur som portalen startat (en åt gången per ärende)
_AI_LAS = threading.Lock()
AI_TAK = 2  # högst så många samtidiga AI-turer ur portalen


def starta_ai(dash, eid):
    """En AI-tur i intervjun, startad av ägarens uttryckliga klick: Kundstarts befintliga modellarbetare
    (kontroller/kundstart_modell.py) för det här ärendets köjobb (--arende) med pilotens transport (--live-cli), som själv
    bara tar fiktiva ärenden och räknar budgeten. Ett verkligt ärende, ett ärende utan köat jobb eller fler än AI_TAK
    samtidiga turer startar ingenting; andra ärendens jobb rörs aldrig."""
    import kundstart_agare
    d = kundstart_agare.lager(dash.ROOT).internt(eid)
    if d.get('fiktiv') is not True:
        raise ValueError('AI-vägen i portalen gäller bara testkunder; ett verkligt ärende kräver separat aktivering')
    if (d.get('modell') or {}).get('status') != 'ko':
        raise ValueError('inget svar väntar på AI (modellens läge: %s)' % (d.get('modell') or {}).get('status'))
    with _AI_LAS:
        p = _AI.get(eid)
        if p and p.poll() is None:
            return {'startad': False, 'pagar': True, 'pid': p.pid}
        if sum(1 for x in _AI.values() if x.poll() is None) >= AI_TAK:
            raise ValueError('%d AI-turer pågår redan; vänta tills en är klar' % AI_TAK)
        modell = os.environ.get('NWP_KUNDSTART_MODELL') or 'claude-sonnet-5-5'
        logg = Path(dash.ROOT) / 'underlag' / 'kundstart' / 'modellturer.log'
        logg.parent.mkdir(parents=True, exist_ok=True)
        with open(logg, 'a', encoding='utf-8') as f:
            p = subprocess.Popen([str(Path(dash.ROOT) / '.venv/bin/python'), '-B', str(Path(dash.ROOT) / 'kontroller/kundstart_modell.py'),
                                  '--modell', modell, '--live-cli', '--effort', os.environ.get('NWP_KUNDSTART_EFFORT') or 'medium', '--antal', '1', '--arende', eid],
                                 cwd=str(dash.ROOT), stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        _AI[eid] = p
    return {'startad': True, 'pid': p.pid, 'modell': modell, 'transport': 'live-cli (pilotens abonnemangstransport, bara fiktiva ärenden)'}


def utgava(rot):
    """Appens senast byggda signerade utgåva i utcheckningen (desktop/utgava/, byggd av desktop/bygg-utgava.sh; utanför
    git). Motorn intygar ingenting om den: appen prövar minisign-signaturen och versionsbindningen själv."""
    kat = Path(rot) / 'desktop' / 'utgava'
    try:
        b = json.loads((kat / 'utgava.json').read_text(encoding='utf-8'))
        artefakt = kat / 'Nortropic.app.tar.gz'
        sig = (kat / 'Nortropic.app.tar.gz.sig').read_text(encoding='utf-8').strip()
        if not artefakt.is_file():
            return None
    except (OSError, ValueError):
        return None
    return {'artefakt': artefakt, 'beskrivning': {'version': str(b.get('version') or ''), 'kontrakt': str(b.get('kontrakt') or ''), 'noter': str(b.get('noter') or '')[:2000],
                                                  'storlek': artefakt.stat().st_size, 'signatur': sig, 'byggd': b.get('byggd'), 'commit': b.get('commit')}}


def leverans(dash, slug):
    """P10–P12 för en kund, bara lästa ur de levererade kontrakten: migreringsläget med sina fem belägg
    (kontroller/migreringslage.py), aktiveringens torrkörning (kontroller/aktivera.py, inga sidoeffekter, inget nät),
    leveranskvittona och Worker-namnen. Ingen status hittas på: saknad data, ej ansluten och inte observerad står som det."""
    import kundrepo
    i = kundrepo.identitet(slug)  # ogiltig slug: ValueError
    ut = {'slug': slug, 'tid': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'worker': {'produktion': i['worker'], 'forhandsvisning': i['worker_forhandsvisning']},
          'kundrepo': bool(kundrepo.las_kvitto(slug))}
    v = dash.las_json(dash.UNDERLAG / slug / 'VERKSAMHET.json') or {}
    ut['namn'] = v.get('namn') if isinstance(v, dict) else None
    ut['test'] = bool(isinstance(v, dict) and v.get('fiktiv'))
    for nyckel, f in (('migrering', lambda: __import__('migreringslage').lage(slug)), ('aktivering', lambda: __import__('aktivera').torr(slug))):
        try:
            ut[nyckel] = f()
        except Exception as e:  # noqa: BLE001 — en del som inte går att läsa står som fel, inte som klar
            ut[nyckel] = {'fel': '%s: %s' % (type(e).__name__, str(e)[:240])}
    kvitton = []
    lev = Path(dash.KUNDER) / slug / 'leverans'
    for p in sorted(lev.glob('*.json'))[-40:] if lev.is_dir() else []:
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            j = {}
        kvitton.append({'fil': p.name, 'slag': p.name.split('-')[0].split('.')[0], 'status': j.get('status'), 'tid': j.get('tid'),
                        'version': j.get('version_id'), 'adress': j.get('adress') or j.get('url')})
    ut['kvitton'] = kvitton
    m = ut['migrering'] if isinstance(ut.get('migrering'), dict) else {}
    ut['publicerad'] = bool(m.get('i_drift'))  # bara en observerad trafikflytt efter en klar release räknas
    ut['forvaltning'] = {'analys': {'lage': 'ej_ansluten', 'text': 'Ingen besöks- eller förfrågningsstatistik är ansluten i motorn för kunden. '
                                                                   'Ingen siffra visas förrän en källa är ansluten och har mätt en hel period.'}}
    return ut


# --- kommentarerna (E6): bestående, versionsbundna arbetsobjekt på kandidatens bevarade ögonblicksbild ---

_KLAS = threading.Lock()


class Inaktuell(ValueError):
    """Kandidatens version eller bild är inte den ägaren kommenterade."""


def _kfil(dash, slug):
    # bussens katalog: nekad för sessionernas Read, Edit och Write (kunskap/arbetsyta.md), så kommentarerna är ägarens tills
    # han samlar dem till ett uppdrag
    return Path(dash.UNDERLAG) / slug / 'arbetsyta' / 'KOMMENTARER.json'


def _klasa(dash, slug):
    try:
        d = json.loads(_kfil(dash, slug).read_text(encoding='utf-8'))
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _kskriv(dash, slug, lista):
    f = _kfil(dash, slug)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name('.%s.%d.tmp' % (f.name, os.getpid()))
    tmp.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(tmp, f)


def _klage(dash, slug):
    import arbetsyta
    if slug not in {p['slug'] for p in arbetsyta.projekt(dash)}:
        raise LookupError('ingen kund som arbetsytan känner till')
    lage = arbetsyta.lage(dash, slug)
    if lage.get('ab_dold'):
        raise Inaktuell('kunden är en arm i en blind jämförelse; välj i Jämförelser först')
    return lage


def kommentarer(dash, slug):
    """Kundens kommentarer med kandidaterna som har en bevarad ögonblicksbild; en kommentar på en äldre version är
    inaktuell (den pekar på en bild som inte längre är kandidatens)."""
    lage = _klage(dash, slug)
    kand = [k for k in lage.get('kandidater') or [] if k.get('version_hel')]
    nu = {k['id']: k.get('version_hel') for k in kand}
    lista = _klasa(dash, slug)
    for c in lista:
        c['inaktuell'] = nu.get(c.get('kandidat')) != c.get('version')
    return {'slug': slug, 'namn': (lage.get('projekt') or {}).get('namn'), 'blind': lage.get('blind'), 'korning': (lage.get('korning') or {}).get('startad'),
            'vantar_pa_agaren': bool((lage.get('korning') or {}).get('vantar_pa_agaren')),
            'kandidater': [{'id': k['id'], 'etikett': k.get('etikett'), 'version': k['version_hel'],
                            'bilder': {b: k['snapshot'].get(b) for b in ('390', '1440') if (k.get('snapshot') or {}).get(b)},
                            'sha': {b: (k['snapshot'].get('sha') or {}).get(b) for b in ('390', '1440') if (k.get('snapshot') or {}).get(b)}} for k in kand],
            'kommentarer': lista}


def kommentar(dash, slug, data):
    """Ny kommentar, svar i tråden, status eller beställning. En ny kommentar binds till kandidaten, hela versionen,
    bredden, ögonblicksbilden och dess sha256 som ägaren såg; en annan version eller bild nu ger Inaktuell. En kommentar
    är ingen ändringsorder: först "bestall" knyter de valda till ett uppdrag som redan sparats genom arbetsytans
    ändringsväg. Verifierat löst kräver att ägaren sett en nyare version än den kommenterade."""
    import re
    if not isinstance(data, dict):
        raise ValueError('kommentaren ska vara ett objekt')
    h = data.get('handling')
    lage = _klage(dash, slug)
    kand = {k['id']: k for k in lage.get('kandidater') or []}
    nu = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    text = lambda n=4000: (lambda t: t if 1 <= len(t) <= n else (_ for _ in ()).throw(ValueError('skriv en text (högst %d tecken)' % n)))(str(data.get('text') or '').strip())  # noqa: E731
    with _KLAS:
        lista = _klasa(dash, slug)
        efter = {c['id']: c for c in lista}
        if h == 'ny':
            cid = str(data.get('id') or '')
            if not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', cid):
                raise ValueError('kommentarens id ska vara ett UUID')
            k = kand.get(str(data.get('kandidat') or ''))
            if not k or not k.get('version_hel'):
                raise ValueError('välj en kandidat med en bevarad version')
            el = data.get('element')
            if data.get('version') != k['version_hel']:
                raise Inaktuell('kandidaten har en annan version nu än den du kommenterade; se den nya versionen först')
            x, y = data.get('x'), data.get('y')
            if (x is None) != (y is None) or (x is not None and not all(isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1 for v in (x, y))):
                raise ValueError('punkten anges som x och y mellan 0 och 1, eller utelämnas för hela sidan')
            if el is not None:
                # studions kommentar på ett element i den levande versionen (designstudion 2026-10-11): bunden till
                # källkartans id, förekomsten, sidan och bredden i samma version; punkten gäller elementets ruta
                if not isinstance(el, dict) or not re.fullmatch(r'[0-9a-f]{12}', str(el.get('k') or '')) \
                        or not re.fullmatch(r'/(?:[a-z0-9][a-z0-9-]{0,60}/){0,3}', str(el.get('sida') or '')):
                    raise ValueError('elementet anges med källkartans id och sidan')
                try:
                    ebredd, instans = int(el.get('bredd')), int(el.get('instans') or 0)
                except (TypeError, ValueError) as e:
                    raise ValueError('elementets bredd och förekomst är heltal') from e
                if not 280 <= ebredd <= 2560 or not 0 <= instans < 200 or (el.get('barn') is not None and not re.fullmatch(r'(img|video):\d{1,2}', str(el.get('barn')))):
                    raise ValueError('ogiltig bredd, förekomst eller barnelement')
                post = {'id': cid, 'kandidat': k['id'], 'etikett': k.get('etikett'), 'version': k['version_hel'], 'bredd': str(ebredd), 'bild': None,
                        'bild_sha': None, 'element': {'k': el['k'], 'instans': instans, 'barn': el.get('barn'), 'sida': el['sida'],
                                                      'del': str(el.get('del') or '')[:200]}, 'x': x, 'y': y, 'text': text()}
            else:
                bredd = str(data.get('bredd') or '')
                if bredd not in ('390', '1440'):
                    raise ValueError('bredden ska vara 390 eller 1440')
                snap = k.get('snapshot') or {}
                if not snap.get(bredd) or snap.get(bredd) != data.get('bild') or (snap.get('sha') or {}).get(bredd) != data.get('bild_sha'):
                    raise Inaktuell('bilden du kommenterade är inte kandidatens ögonblicksbild nu; läs om')
                post = {'id': cid, 'kandidat': k['id'], 'etikett': k.get('etikett'), 'version': k['version_hel'], 'bredd': bredd, 'bild': snap[bredd],
                        'bild_sha': snap['sha'][bredd], 'x': x, 'y': y, 'text': text()}
            if cid in efter:
                if any(efter[cid].get(f) != v for f, v in post.items()):
                    raise Inaktuell('kommentarens id har redan använts för en annan kommentar')
                return {'kommentar': efter[cid], 'upprepat': True}
            post.update({'status': 'oppen', 'avsandare': 'agaren', 'tid': nu, 'korning': (lage.get('korning') or {}).get('startad'), 'svar': [], 'historik': []})
            lista.append(post)
            _kskriv(dash, slug, lista)
            return {'kommentar': post, 'upprepat': False}
        if h in ('svara', 'status'):
            c = efter.get(str(data.get('id') or ''))
            if not c:
                raise LookupError('kommentaren finns inte')
            if h == 'svara':
                c['svar'].append({'text': text(), 'tid': nu, 'avsandare': 'agaren'})
            else:
                st = data.get('status')
                if st not in ('oppen', 'avvisad', 'lost_verifierad'):
                    raise ValueError('status: oppen, avvisad eller lost_verifierad')
                if st == 'lost_verifierad' and (kand.get(c['kandidat']) or {}).get('version_hel') in (None, c['version']):
                    raise Inaktuell('verifierat löst kräver att du sett en nyare version än den du kommenterade; ett "fixat" i ett svar räcker inte')
                c['historik'].append({'fran': c['status'], 'till': st, 'tid': nu, 'avsandare': 'agaren'})
                c['status'] = st
            _kskriv(dash, slug, lista)
            return {'kommentar': c}
        if h == 'bestall':
            ids, aid = data.get('ids'), str(data.get('andring_id') or '')
            if not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', aid) or not isinstance(ids, list) or not ids or len(ids) > 30:
                raise ValueError('välj kommentarerna och ange uppdragets ändrings-id')
            valda = [efter.get(str(i)) for i in ids]
            if not all(valda):
                raise LookupError('en vald kommentar finns inte')
            if len({(c['kandidat'], c['version']) for c in valda}) != 1:
                raise ValueError('ett uppdrag gäller en kandidat och en version')
            if any(c['status'] == 'bestalld' and c.get('andring_id') != aid for c in valda) or any(c['status'] in ('avvisad', 'lost_verifierad') for c in valda):
                raise Inaktuell('en vald kommentar är redan beställd, avvisad eller löst')
            for c in valda:
                if c['status'] != 'bestalld':
                    c['historik'].append({'fran': c['status'], 'till': 'bestalld', 'tid': nu, 'avsandare': 'agaren', 'andring_id': aid})
                    c['status'], c['andring_id'] = 'bestalld', aid
            _kskriv(dash, slug, lista)
            return {'bestallda': [c['id'] for c in valda], 'andring_id': aid}
        raise ValueError('handlingen ska vara ny, svara, status eller bestall')
