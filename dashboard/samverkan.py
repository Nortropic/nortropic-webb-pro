"""samverkan.py — arbetsytans samverkan mellan sessioner: ägarens meddelanden, beslut över agenternas förslag,
granskarmandat, paus och återupptagning, sessionshistorik och följdfrågor, beslut och godkännande, och den externa
granskarens väg (ägarens uppdrag 2026-10-09 om den kompletta arbetsplatsen; kunskap/arbetsyta.md).

Bussen och styrningen är kontroller/meddelanden.py; den här modulen är dashboardens del: den sätter avsändaren (ägaren
med nyckeln, en extern granskare med sin granskarnyckel), prövar blindningen och A/B-spärren på servervägen
(arbetsyta.dold, stängt vid fel) och visar meddelandena med det som går att belägga. Före ägarens första val i körningen
visas inte agenternas text, belägg, svar eller kvitton, och sessionernas historik och följdfrågor är stängda; en arm i
en blind jämförelse visar ingenting. Ägarens egna meddelanden och deras leveranslägen syns alltid.
"""
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

DOLT = 'visas efter ditt första val i körningen'
ID = re.compile(r'^[A-Za-z0-9_-]{8,80}$')
SESSION = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
NAMN = re.compile(r'^[a-z][a-z0-9-]{1,30}$')
GREN_LAS = threading.Lock()
FRIST_GREN = int(os.environ.get('NWP_GREN_FRIST') or 600)


def _kontroller():
    rot = str(Path(__file__).resolve().parents[1] / 'kontroller')
    if rot not in sys.path:
        sys.path.insert(0, rot)


def _m():
    _kontroller()
    import meddelanden
    return meddelanden


class Dold(ValueError):
    """En arm i en blind jämförelse, eller något som visas först efter ägarens första val (HTTP 409)."""


def _dold(dash, slug):
    import arbetsyta
    return arbetsyta.dold(dash, slug)


def _spärr(dash, slug, blind_stangd=False):
    blind, ab = _dold(dash, slug)
    if ab:
        raise Dold('kunden är en arm i en blind jämförelse som du inte valt i än')
    if blind_stangd and blind:
        raise Dold('sessionernas innehåll %s' % DOLT)
    return blind


# --- meddelandena i ägarens vy ---

def _genomforande(slug, m):
    """Det som går att belägga om en ändringsinstruktion: kvittot är mottagarens påstående; belagt bara när kandidatens
    fotograferade version ändrats efter att meddelandet mottogs."""
    M = _m()
    if m.get('syfte') != 'andringsinstruktion' or M.lage(m) not in ('besvarat', 'genomfort'):
        return None
    k = m.get('kvitto') or {}
    if k.get('genomfort') is False:
        return {'lage': 'avstatt', 'text': 'mottagaren säger att den avstod', 'beskrivning': k.get('beskrivning')}
    if not k:
        return {'lage': 'okant', 'text': 'inget kvitto från mottagaren; genomförandet är okänt'}
    try:
        import kandidater
        st = kandidater.las_status(slug, m.get('kandidat')) if m.get('kandidat') else {}
    except Exception:  # noqa: BLE001
        st = {}
    mottaget = max([h.get('tid') or '' for h in m.get('handelser') or [] if h.get('lage') == 'mottaget'] or [''])
    ny = st.get('version')
    if ny and m.get('version') and ny != m['version'] and (st.get('fotograferad') or '') > mottaget:
        return {'lage': 'belagt', 'text': 'kvitterat, och kandidaten har en ny fotograferad version efter mottagandet',
                'version_fore': m['version'][:12], 'version_efter': ny[:12], 'beskrivning': k.get('beskrivning')}
    return {'lage': 'pastatt', 'text': 'mottagaren säger att den är genomförd; ingen ny fotograferad version belägger det än',
            'beskrivning': k.get('beskrivning')}


def _vy(slug, m, blind):
    M = _m()
    agent = (m.get('avsandare') or {}).get('typ') != 'agare'
    g = _genomforande(slug, m)
    lage = 'genomfort' if g and g['lage'] == 'belagt' else M.lage(m)
    ut = {k: m.get(k) for k in ('id', 'tid', 'korning', 'avsandare', 'mottagare', 'syfte', 'kandidat', 'version', 'svar_pa', 'mandat', 'dom',
                                'levererat_till', 'beslut')}
    ut.update(lage=lage, lage_text=M.LAGEN.get(lage, lage), syfte_text=M.SYFTEN.get(m.get('syfte')), agent=agent,
              handelser=[{k: h.get(k) for k in ('tid', 'lage', 'notis', 'bevis', 'session_id')} for h in m.get('handelser') or []],
              text=m.get('text'), belagg=m.get('belagg'), svar=m.get('svar'), kvitto=m.get('kvitto'), genomforande=g)
    if blind:
        for falt in ('levererat_till',):
            if ut.get(falt):
                ut[falt] = {k: v for k, v in ut[falt].items() if k != 'roll'}
        for sida in ('avsandare', 'mottagare'):
            if isinstance(ut.get(sida), dict) and ut[sida].get('roll'):
                ut[sida] = {k: v for k, v in ut[sida].items() if k != 'roll'}
        if agent:
            ut.update(text=DOLT, belagg=[], dolt=True)
        if ut.get('svar'):
            ut['svar'] = {'tid': ut['svar'].get('tid'), 'text': DOLT, 'dolt': True}
        if ut.get('kvitto'):
            ut['kvitto'] = {'genomfort': ut['kvitto'].get('genomfort'), 'beskrivning': DOLT}
        if g and g.get('beskrivning'):
            ut['genomforande'] = dict(g, beskrivning=DOLT)
    return ut


def lage(dash, slug):
    """Meddelandena, mandaten och pausen för ägarens vy, blindade på servervägen."""
    M = _m()
    blind, ab = _dold(dash, slug)
    if ab:
        return {'dold': True, 'meddelanden': [], 'mandat': [], 'styrning': None, 'syften': M.SYFTEN, 'lagen': M.LAGEN}
    kn = M.korning(slug)
    alla = [_vy(slug, m, blind) for m in M.alla(slug)]
    styr = M.styrning(slug)
    levande = M.levande(slug)
    pausade = [s for s in levande if s.get('lage') == 'pausad']
    p = M.paus_galler(slug)
    projekt = None
    if p and p.get('omfattning') == 'projekt':
        arbetar = [s for s in levande if s.get('lage') != 'pausad']
        tjanster = _tjanster(dash, slug, levande)
        projekt = {'begard': p.get('begard'), 'lage': 'pausad' if not arbetar else 'paus_begard',
                   'lage_text': 'pausad: inga sessioner arbetar och ingen ny startar' if not arbetar else
                   'paus begärd: %d session(er) arbetar ännu' % len(arbetar),
                   'vantande_start': p.get('vantande_start'), 'arbetar': [{'session_id': s['session_id'], 'ansvar': s.get('ansvar'), 'kandidat': s.get('kandidat'),
                                                                          'lage': s.get('lage')} for s in arbetar],
                   'tjanster': tjanster}
    return {'tid': M.nu(), 'korning': kn, 'blind': blind, 'meddelanden': alla,
            'oppna': [m['id'] for m in alla if m['agent'] and (m.get('mottagare') or {}).get('typ') == 'agare' and not m.get('beslut')],
            'mandat': [dict(x, aktivt=not x.get('aterkallat') and x.get('korning') == kn) for x in M.mandat(slug)],
            'styrning': {'projekt': projekt, 'sessioner': {sid: dict(v, omfattning='session') for sid, v in (styr.get('sessioner') or {}).items()}},
            'pausade': [{'session_id': s['session_id'], 'verktyg_kvar': s.get('verktyg_kvar'), 'sedan': s.get('sedan')} for s in pausade],
            'syften': M.SYFTEN, 'lagen': M.LAGEN}


def _tjanster(dash, slug, levande):
    """Arbetarens egna processer utanför sessionerna (ett bygge, en fotografering) som fortfarande arbetar under en
    projektpaus: de pausas inte, de redovisas. None när processlistan inte gick att läsa."""
    _kontroller()
    import lopare
    st = dash.las_json(dash.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    if not st.get('pid') or not _lever(st['pid']):
        return []
    alla = lopare._barn(st['pid'])
    if alla is None:
        return None
    sessioner = {s.get('pid') for s in levande if s.get('pid')}
    under = set(sessioner)
    for sp in sessioner:
        under |= {d['pid'] for d in lopare._barn(sp) or []}
    return [d for d in alla if d['pid'] not in under and 'claude' not in str(d.get('kommando'))][:20]


def skicka(dash, slug, data):
    """Ägarens meddelande (fråga eller ändringsinstruktion) till en session, en kandidats utförare eller en extern
    granskare. Avsändaren är ägaren eftersom anropet bär ägarens nyckel; texten avgör ingenting."""
    M = _m()
    blind = _spärr(dash, slug)
    syfte = data.get('syfte') or 'fraga'
    if syfte not in ('fraga', 'andringsinstruktion'):
        raise ValueError('du skickar en fråga eller en ändringsinstruktion; ett beslut fattar du med beslutsknapparna')
    mot = data.get('mottagare') if isinstance(data.get('mottagare'), dict) else {}
    m = M.skapa(slug, {'typ': 'agare', 'klient': 'arbetsytan'}, mot, syfte, data.get('text'), kandidat=data.get('kandidat') or None,
                version=data.get('version') or None, mid=data.get('id'), korning_=data.get('korning'))
    return dict(_vy(slug, m, blind), upprepat=bool(m.get('upprepat')))


def besluta(dash, slug, mid, data):
    blind = _spärr(dash, slug, blind_stangd=True)
    return _vy(slug, _m().besluta(slug, mid, data), blind)


def mandat(dash, slug, data):
    _spärr(dash, slug)
    return _m().ge_mandat(slug, data)


def aterkalla_mandat(dash, slug, mid):
    _spärr(dash, slug)
    return _m().aterkalla_mandat(slug, mid)


def paus(dash, slug, data):
    """Ägarens paus, med omfattningen i begäran: projekt eller en session. Gäller den aktuella körningen."""
    _spärr(dash, slug)
    M = _m()
    om = data.get('omfattning')
    if data.get('korning') and data['korning'] != M.korning(slug):
        raise M.Inaktuell('körningen har bytts sedan läget lästes; läs om läget')
    if om == 'projekt' and not data.get('aterta'):
        M.begar_paus(slug, 'projekt', pid_=data.get('id'))
    elif om == 'session' and not data.get('aterta'):
        M.begar_paus(slug, 'session', data.get('session_id'), pid_=data.get('id'))
    elif data.get('aterta'):
        M.aterta(slug, om, data.get('session_id'))
    else:
        raise ValueError('välj omfattningen: projekt eller session')
    return lage(dash, slug)


# --- sessionernas historik och följdfrågor ---

def _transkript(sid):
    _kontroller()
    import bildkedja
    return bildkedja.transkript(sid)


def historik(dash, slug, sid, n=80):
    """En sessions samtal ur Claude Codes transkript: uppgiften, meddelandena och sessionens texter (maskerade och
    avkortade), med verktygens namn; före ägarens första val stängd. Ändrar ingenting."""
    import arbetsyta
    _spärr(dash, slug, blind_stangd=True)
    M = _m()
    if not SESSION.fullmatch(str(sid or '')):
        raise ValueError('vilken session?')
    s = M.sessionslage(slug, sid)
    post = _las((dash.UNDERLAG / slug / 'atelje' / 'sessioner' / ('%s.json' % sid)))
    if not s and not post:
        raise ValueError('sessionen hör inte till kunden')
    tr = _transkript(sid)
    rader = []
    if tr:
        for rad in Path(tr).read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                d = json.loads(rad)
            except ValueError:
                continue
            msg = d.get('message') if isinstance(d.get('message'), dict) else {}
            c = msg.get('content')
            if d.get('type') == 'user' and isinstance(c, str):
                rader.append({'tid': d.get('timestamp'), 'typ': 'in', 'text': arbetsyta.maskera(c[:3000])})
            elif d.get('type') == 'assistant' and isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get('type') == 'text' and b.get('text'):
                        rader.append({'tid': d.get('timestamp'), 'typ': 'ut', 'text': arbetsyta.maskera(b['text'][:3000])})
                    elif isinstance(b, dict) and b.get('type') == 'tool_use':
                        rader.append({'tid': d.get('timestamp'), 'typ': 'verktyg', 'text': str(b.get('name'))})
    grenar = [g for g in _grenar(dash, slug) if g.get('foralder') == sid]
    return {'session_id': sid, 'roll': (s or post or {}).get('roll'), 'kandidat': (s or post or {}).get('kandidat'),
            'lage': (s or {}).get('lage'), 'transkript': bool(tr), 'antal': len(rader), 'rader': rader[-n:], 'grenar': grenar,
            'kalla': 'Claude Codes transkript för sessionen' if tr else 'transkriptet finns inte (sessionen startades utan id eller har städats)'}


def _las(p):
    try:
        d = json.loads(Path(p).read_text(encoding='utf-8'))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _grenkatalog(dash, slug):
    return dash.UNDERLAG / slug / 'arbetsyta' / 'grenar'


def _grenar(dash, slug):
    k = _grenkatalog(dash, slug)
    ut = []
    for f in sorted(k.glob('*.json')) if k.is_dir() else []:
        g = None if f.name.startswith('svar-') else _las(f)
        if g and g.get('id'):
            svar = _las(k / ('svar-%s.json' % g['id']))
            if svar:
                g = dict(g, svar={'text': _maskera(str(svar.get('result') or ''))[:6000], 'fel': bool(svar.get('is_error')),
                                  'session_id': svar.get('session_id'), 'listpris_usd': svar.get('total_cost_usd')},
                         session_id=svar.get('session_id') or g.get('session_id'), lage='besvarad' if not svar.get('is_error') else 'fel')
            elif g.get('pid') and _lever(g['pid']):
                g = dict(g, lage='arbetar')
            elif g.get('pid'):
                g = dict(g, lage='avbruten')
            ut.append(g)
    return ut


def _maskera(t):
    import arbetsyta
    return arbetsyta.maskera(t)


def _lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def grenar(dash, slug):
    _spärr(dash, slug, blind_stangd=True)
    return {'grenar': _grenar(dash, slug)}


def foljdfraga(dash, slug, data):
    """En följdfråga till en avslutad session: en förgrenad session (claude -p --resume <id> --fork-session) med eget id,
    registrerad med föräldern och ansvaret, som bara får läsa (Read, Glob, Grep; dontAsk) och startar i en egen tom
    katalog. Föräldern får aldrig en andra skrivande process: en session som lever förgrenas inte. Samma id ger samma gren."""
    import arbetsyta
    _spärr(dash, slug, blind_stangd=True)
    M = _m()
    gid, sid, text = str(data.get('id') or ''), str(data.get('session_id') or ''), str(data.get('text') or '').strip()
    if not ID.fullmatch(gid) or not SESSION.fullmatch(sid):
        raise ValueError('ett id och en session behövs')
    if not text or len(text) > 6000:
        raise ValueError('skriv frågan (högst 6000 tecken)')
    s = M.sessionslage(slug, sid)
    post = _las(dash.UNDERLAG / slug / 'atelje' / 'sessioner' / ('%s.json' % sid))
    if not s and not post:
        raise ValueError('sessionen hör inte till kunden')
    if (s and not s.get('slut') and _lever(s.get('pid'))) or (post and not post.get('slut') and _lever(post.get('pid'))):
        raise M.Nekad('sessionen arbetar: skriv till den med ett meddelande; en förgrening startas först när den slutat')
    if not _transkript(sid):
        raise ValueError('sessionens transkript finns inte; den kan inte förgrenas')
    k = _grenkatalog(dash, slug)
    with GREN_LAS:
        f = k / ('%s.json' % gid)
        if f.is_file():
            return dict(_las(f), upprepat=True)
        pagar = [g for g in _grenar(dash, slug) if g.get('lage') == 'arbetar']
        if pagar:
            raise M.Nekad('en följdfråga pågår redan; vänta på svaret')
        rum = k / 'rum'
        rum.mkdir(parents=True, exist_ok=True)
        if rum.is_symlink() or any(x.name != '.DS_Store' for x in rum.iterdir()):
            raise ValueError('följdfrågornas arbetskatalog %s ska vara tom' % rum)
        _kontroller()
        import atelje
        import nastlad
        kandidat = (s or post or {}).get('kandidat')
        lasbart = ['Read(//%s/%s)' % (str(Path(dash.ROOT).resolve()).strip('/'), x) for x in ('README.md', 'CLAUDE.md', 'kunskap/**', 'kritik/**')]
        lasbart += ['Read(//%s/**)' % str((dash.UNDERLAG / slug / 'atelje' / 'kandidater' / kandidat).resolve()).strip('/')] if kandidat else []
        lasbart += ['Read(//%s/**)' % str((dash.KUNDER / slug / 'kandidater' / kandidat / 'sajt' / 'src').resolve()).strip('/')] if kandidat else []
        modell = (s or {}).get('modell') or (post or {}).get('modell') or atelje.MODELL
        g = {'id': gid, 'tid': M.nu(), 'foralder': sid, 'ansvar': 'följdfråga, skrivskyddad', 'roll': (s or post or {}).get('roll'),
             'kandidat': kandidat, 'korning': M.korning(slug), 'text': text, 'modell': modell, 'session_id': None, 'pid': None,
             'behorighet': 'Read, Glob och Grep (dontAsk); egen tom arbetskatalog; föräldern skrivs aldrig'}
        args = [atelje.claude(), '-p', '--resume', sid, '--fork-session', '--output-format', 'json', '--model', modell, '--effort', 'medium',
                '--max-turns', '12', '--permission-mode', 'dontAsk', '--setting-sources', 'project,local', '--strict-mcp-config',
                '--tools', 'Read,Glob,Grep', '--allowedTools', *lasbart]
        f.parent.mkdir(parents=True, exist_ok=True)
        fu = open(k / ('svar-%s.json' % gid), 'wb')
        fe = open(k / ('svar-%s.err' % gid), 'wb')
        prompt = ('[Följdfråga från ÄGAREN (via arbetsytan) till en förgrening av sessionen; du får bara läsa och ändrar inga filer]\n\n%s'
                  % arbetsyta.maskera(text))
        try:
            p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=fu, stderr=fe, cwd=str(rum), env=nastlad.miljo(), start_new_session=True)
        except OSError as e:
            fu.close()
            fe.close()
            raise ValueError('kunde inte starta claude: %s' % e)
        g['pid'] = p.pid
        _skriv(f, g)

    def vakta():
        try:
            p.communicate(input=prompt.encode(), timeout=FRIST_GREN)
        except subprocess.TimeoutExpired:
            nastlad.doda_trad(p.pid)
            p.communicate()
        finally:
            fu.close()
            fe.close()
            g_ = _las(f) or g
            svar = _las(k / ('svar-%s.json' % gid)) or {}
            g_.update(slut=M.nu(), session_id=svar.get('session_id'))
            _skriv(f, g_)
    threading.Thread(target=vakta, daemon=True, name='gren-%s' % gid).start()
    return g


def _skriv(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name('.%s.%d.tmp' % (p.name, os.getpid()))
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


# --- beslutet: Prototypvyns beslutstjänst, bunden till den version ägaren sett ---

def _bild_sha(dash, rel):
    p = (dash.ROOT / str(rel or '')).resolve()
    if not str(p).startswith(str((dash.UNDERLAG).resolve()) + '/') or not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def beslut(dash, slug, data):
    """Ägarens beslut från arbetsytan (välj, jämför, förkasta, ny riktning, putsa, godkänn) genom samma tjänst och
    samma skydd som vyn Prototyp (server.spara_kandidatbeslut → atelje.doma → kandidater.prova_beslut och
    forbered_vinnare: versionen ägaren såg måste vara kandidatens fotograferade och dess filer oförändrade). Arbetsytan
    lägger till belägget för vad ägaren såg: bilden och dess hash, prövad mot filen nu. Sedan ett ägarbeslut i bussen."""
    import arbetsyta
    _spärr(dash, slug)
    M = _m()
    sedd = data.get('sedd') if isinstance(data.get('sedd'), list) else []
    kand = [{'id': str(k.get('id') or ''), 'version': str(k.get('version') or '')} for k in data.get('kandidater') or [] if isinstance(k, dict)]
    if not kand and data.get('beslut') not in ('forkasta', 'ny_riktning'):
        raise ValueError('välj kandidaten beslutet gäller')
    for k in kand:
        bev = [x for x in sedd if isinstance(x, dict) and x.get('kandidat') == k['id'] and x.get('version') == k['version']]
        if data.get('beslut') == 'godkand':
            if not bev:
                raise ValueError('godkänn den version du ser: bilden av %s i version %s saknas i beslutet' % (k['id'], k['version'][:12]))
            for b in bev:
                if not b.get('bild') or _bild_sha(dash, b['bild']) != b.get('bild_sha'):
                    raise M.Inaktuell('bilden du såg av %s är inte den som finns nu; läs om och se den nya versionen först' % k['id'])
    if data.get('korning') and data['korning'] != M.korning(slug):
        raise M.Inaktuell('körningen har bytts sedan läget lästes; läs om läget')
    st = dash.las_json(dash.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    markering = {'vy': 'Arbetsyta, beslut', 'sedd': [{k_: x.get(k_) for k_ in ('kandidat', 'version', 'bild', 'bild_sha')} for x in sedd if isinstance(x, dict)][:12],
                 'korning': st.get('startad')}
    svar = dash.spara_kandidatbeslut(slug, st, {'beslut': data.get('beslut'), 'kandidater': kand, 'text': data.get('text'),
                                                'delar': data.get('delar')}, arbetsyta=markering)
    dom = svar.get('dom') or {}
    try:  # ägarbeslutet i bussen: historiken och, när en utförare lever för kandidaten, beskedet till den
        for k in kand or [{'id': None, 'version': None}]:
            M.skapa(slug, {'typ': 'agare', 'klient': 'arbetsytan'},
                    {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': k['id']} if k['id'] else {'typ': 'agare'}, 'agarbeslut',
                    'Ägarens beslut: %s%s.%s' % (data.get('beslut'), ' för %s, version %s' % (k['id'], k['version'][:12]) if k['id'] else '',
                                                 (' ' + str(data.get('text'))[:500]) if data.get('text') else ''),
                    kandidat=k['id'], mid='beslut-%s-%s' % (hashlib.sha256(json.dumps(dom, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16],
                                                            k['id'] or 'alla'), dom={'tid': dom.get('tid'), 'beslut': dom.get('beslut')})
    except Exception:  # noqa: BLE001 — beslutet står i domloggen; bussens rad är en spegel
        pass
    return svar


# --- den externa granskaren (till exempel Codex): egen nyckel, egen avsändare, bara läsning och fynd ---

def nyckelkatalog():
    return Path(os.environ.get('NWP_GRANSKARE_NYCKLAR') or Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'granskare')


def extern_namn(huvud):
    """Den externa granskarens namn ur Authorization: Bearer <nyckel>, prövad mot nyckelfilerna (granskare/<namn>.nyckel,
    0600) i konstant tid; None när ingen stämmer. Namnet kommer ur filen, aldrig ur anropet."""
    h = str(huvud or '')
    if not h.startswith('Bearer '):
        return None
    given = h[len('Bearer '):].strip().encode()
    k = nyckelkatalog()
    traff = None
    for f in sorted(k.glob('*.nyckel')) if k.is_dir() else []:
        if f.is_symlink() or not NAMN.fullmatch(f.stem):
            continue
        try:
            ratt = f.read_text(encoding='utf-8').strip().encode()
        except OSError:
            continue
        if ratt and hmac.compare_digest(given, ratt):
            traff = f.stem
    return traff


def extern_underlag(dash, slug, namn):
    """Det granskaren får se: kunden, körningen, kandidaterna med neutrala etiketter, versioner och bilder (sökvägar
    under underlag/, hämtas med /api/extern/<kund>/bild), mandaten som gäller den och blindläget. Inga bedömningar från
    ägaren eller andra granskare."""
    import arbetsyta
    blind = _spärr(dash, slug)
    M = _m()
    kand, _fel = arbetsyta.kandidatlista(dash, slug, True)
    return {'kund': slug, 'korning': M.korning(slug), 'blind': blind, 'granskare': namn,
            'kandidater': [{'id': k['id'], 'etikett': k['etikett'], 'status': k.get('status'), 'version': k.get('version_hel'),
                            'fotograferad': k.get('fotograferad'), 'bilder': {b: k['snapshot'].get(b) for b in ('390', '1440')}} for k in kand],
            'mandat': [x for x in M.mandat(slug) if (x.get('granskare') or {}).get('typ') == 'extern' and x['granskare'].get('namn') == namn
                       and not x.get('aterkallat') and x.get('korning') == M.korning(slug)],
            'syften': {k: v for k, v in M.SYFTEN.items() if k in ('granskningsfynd', 'forslag', 'fraga', 'andringsinstruktion', 'svar')},
            'regler': 'Fynd har belägg och gäller en kandidat och version. En ändringsinstruktion kräver ägarens mandat för kandidaten. '
                      'Inget du skickar är ägarens ord eller godkännande.'}


def extern_bild(dash, slug, namn, rel):
    """En kandidatbild för granskaren: bara kandidaternas bilder under underlag/<kund>/atelje/kandidater/, ingen länk."""
    _spärr(dash, slug)
    bas = (dash.UNDERLAG / slug / 'atelje' / 'kandidater').resolve()
    p = (dash.ROOT / str(rel or '')).resolve()
    if not str(p).startswith(str(bas) + '/') or p.suffix != '.png' or not p.is_file() or '/bilder/' not in str(p):
        raise ValueError('ingen sådan bild')
    return p.read_bytes()


def extern_fynd(dash, slug, namn, data):
    """Ett fynd, förslag, en fråga, ett svar eller (med mandat) en begäran om rättelse från den externa granskaren, med
    granskaren som avsändare. Till ägaren, eller till kandidatens utförare när mandatet gäller."""
    _spärr(dash, slug)
    M = _m()
    till = data.get('till') or 'agare'
    mot = {'typ': 'agare'} if till == 'agare' else {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': data.get('kandidat')} \
        if till == 'utforande' else None
    if mot is None:
        raise ValueError('till: agare eller utforande')
    m = M.skapa(slug, {'typ': 'extern', 'namn': namn}, mot, data.get('syfte') or 'granskningsfynd', data.get('text'),
                kandidat=data.get('kandidat') or None, version=data.get('version') or None, belagg=data.get('belagg'),
                svar_pa=data.get('svar_pa') or None, korning_=data.get('korning'))
    return {'id': m['id'], 'lage': M.lage(m), 'upprepat': bool(m.get('upprepat'))}


def extern_aterkoppling(dash, slug, namn):
    """Återkopplingen till granskaren: meddelanden till den, svar på dess meddelanden och ägarens beslut över dem."""
    _spärr(dash, slug)
    M = _m()
    egna = {m['id'] for m in M.alla(slug) if m.get('avsandare') == {'typ': 'extern', 'namn': namn}}
    ut = []
    for m in M.alla(slug):
        if (m.get('mottagare') or {}) == {'typ': 'extern', 'namn': namn} or m.get('svar_pa') in egna:
            ut.append({k: m.get(k) for k in ('id', 'tid', 'syfte', 'text', 'kandidat', 'version', 'svar_pa')} | {'avsandare': m['avsandare'].get('typ')})
        if m['id'] in egna:
            ut.append({'id': m['id'], 'eget': True, 'lage': M.lage(m), 'beslut': (m.get('beslut') or {}).get('val'),
                       'svar': (m.get('svar') or {}).get('text')})
    return {'aterkoppling': ut}
