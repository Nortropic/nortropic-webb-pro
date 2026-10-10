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
    """Hash över arbetsytans filer så som de serveras nu (servern läser dem från disk vid varje anrop)."""
    h = hashlib.sha256()
    for namn in ('index.html', 'arbetsyta.js', 'arbetsyta.css', 'kundstart-agare.js', 'kundstart-agare.css', 'portal.js', 'portal.css'):
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


def kaka_sid(cookie_huvud, port):
    namn = KAKA % int(port)
    for del_ in (cookie_huvud or '').split(';'):
        k, _, v = del_.strip().partition('=')
        if k == namn and v:
            return v
    return None


def kaka(sid, port, ta_bort=False):
    if ta_bort:
        return '%s=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0' % (KAKA % int(port))
    return '%s=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=%d' % (KAKA % int(port), sid, SESSION_TID)


def session_skriv_ok(headers, port):
    """En skrivning med sessionskakan: samma ursprung exakt och Sec-Fetch-Site same-origin när webbläsaren skickar det."""
    vard = (headers.get('Host') or '').strip().lower()
    if (headers.get('Origin') or '').strip().lower() != 'http://' + vard:
        return False
    sfs = (headers.get('Sec-Fetch-Site') or '').strip().lower()
    if sfs and sfs != 'same-origin':
        return False
    return giltig(kaka_sid(headers.get('Cookie'), port))


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
    for s, k in kunder.items():
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
        k['vy'] = '#/arbetsyta/' + s if k['projekt'] else ('#/kundstart/' + k['arenden'][0]['id'] if k['arenden'] else '#/arbetsyta/' + s)
        k['senaste'] = k['nasta'] or ''
    lista = sorted(kunder.values(), key=lambda k: (k['senast'] or '', k['slug']), reverse=True)
    return {'tid': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'kunder': lista,
            'uppmarksamhet': [{'slug': k['slug'], 'namn': k['namn'], 'test': k['test'], 'vad': k['vantar'], 'vy': k['vy']} for k in vantar.values()],
            'pagaende': pagaende(dash.ROOT), 'kundstart_fel': kfel}


def uppmarksamhet(dash):
    """Det som väntar på ägaren (för appens avisering): antal och första raden, utan annan kunduppgift."""
    def r():
        ut = []
        for k in dash.kundlagen():
            if k.get('vantar') and not k.get('ab_dold'):
                ut.append('%s: %s' % (k['slug'], ', '.join(k['vantar'][:2])))
        return {'antal': len(ut), 'forsta': ut[0] if ut else None}
    return _cachat('uppmarksamhet', 15, r)


class DubblettKund(ValueError):
    """En kund med samma namn (slug) finns redan: öppna den i stället för att skapa en dubblett."""
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
    slug = ('test-' if test else '') + _slug(foretag)
    person = kontakt or 'Kontaktperson ej angiven'
    try:
        r = kundstart_agare.skapa(dash.ROOT, {'slug': slug, 'namn': person, 'fiktiv': test, 'modellbudget': 10 if test else 0, 'operation': operation})
    except ks.Konflikt as e:
        befintligt = next((a['id'] for a in kundstart_agare.lista(dash.ROOT).get('arenden', []) if a['slug'] == slug), None)
        if befintligt:
            raise DubblettKund('En kund med det namnet finns redan.', befintligt) from e
        raise
    kundstart_agare.anteckningar(dash.ROOT, r['arende'], operation, [('foretag', foretag), ('webbplats', webb), ('syfte', syfte), ('kontakt', kontakt)])
    return {'arende': r['arende'], 'slug': slug, 'nyckel': r['nyckel'], 'aterforsok': r['aterforsok'], 'test': test}


_AI = {}  # ärende -> Popen för den AI-tur som portalen startat (en åt gången per ärende)


def starta_ai(dash, eid):
    """En AI-tur i intervjun, startad av ägarens uttryckliga klick: Kundstarts befintliga modellarbetare
    (kontroller/kundstart_modell.py) för ett köjobb med pilotens transport (--live-cli), som själv bara tar fiktiva
    ärenden och räknar budgeten. Ett verkligt ärende eller ett ärende utan köat jobb startar ingenting."""
    import kundstart_agare
    d = kundstart_agare.lager(dash.ROOT).internt(eid)
    if d.get('fiktiv') is not True:
        raise ValueError('AI-vägen i portalen gäller bara testkunder; ett verkligt ärende kräver separat aktivering')
    if (d.get('modell') or {}).get('status') != 'ko':
        raise ValueError('inget svar väntar på AI (modellens läge: %s)' % (d.get('modell') or {}).get('status'))
    p = _AI.get(eid)
    if p and p.poll() is None:
        return {'startad': False, 'pagar': True, 'pid': p.pid}
    modell = os.environ.get('NWP_KUNDSTART_MODELL') or 'claude-sonnet-5-5'
    logg = Path(dash.ROOT) / 'underlag' / 'kundstart' / 'modellturer.log'
    logg.parent.mkdir(parents=True, exist_ok=True)
    with open(logg, 'a', encoding='utf-8') as f:
        p = subprocess.Popen([str(Path(dash.ROOT) / '.venv/bin/python'), '-B', str(Path(dash.ROOT) / 'kontroller/kundstart_modell.py'),
                              '--modell', modell, '--live-cli', '--effort', os.environ.get('NWP_KUNDSTART_EFFORT') or 'medium', '--antal', '1'],
                             cwd=str(dash.ROOT), stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    _AI[eid] = p
    return {'startad': True, 'pid': p.pid, 'modell': modell, 'transport': 'live-cli (pilotens abonnemangstransport, bara fiktiva ärenden)'}
