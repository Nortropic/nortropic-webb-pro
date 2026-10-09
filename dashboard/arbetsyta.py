"""arbetsyta.py — arbetsytans gemensamma läsväg (ägarens uppdrag 2026-10-09, BESLUT.md; kunskap/arbetsyta.md).

Ett läge per kund, samlat ur det som redan finns: flödets steg, besked, handlingar och blindning (server.flode), ateljéns
status och kandidater (kandidater.sammanstall), observatörens sessioner och transkript (kontroller/observation.py),
startjournalen (underlag/<slug>/ateljestarter/), helbyggets START.json, stream-json-logg och slutpost, domloggen och
partnersamtalets koppling (partner.py). Inget här är en egen sanningskälla: läget räknas fram vid varje läsning, och en
del som inte går att läsa står som ofullständig med skälet. Läsningen startar inget och gör inga modellanrop.

Samma läge används av huvudvyn (dashboard/arbetsyta.js), strömmen (/api/arbetsyta/<slug>/strom) och modden
(mod/nortropic-arbetsyta). Blindningen gäller här, på servervägen: före ägarens första val i en körning bär läget inga
bedömningar, skäl, sökvägar i sessionernas aktivitet eller körningsloggens fria text.
"""
import difflib
import hashlib
import json
import os
import re
import stat
import sys
import time
from pathlib import Path

SCHEMA = 'arbetsyta/1'
# sessionens läge: nyckeln står i läget, etiketten i vyn; ingen av dem betyder godkänt
LAGEN = {'vantar': 'väntar på start', 'startar': 'start pågår', 'aktiv': 'arbetar', 'verktyg': 'väntar på verktyg',
         'beslut': 'väntar på ditt beslut', 'avslutad': 'avslutad', 'avbruten': 'avbruten', 'okant': 'okänt läge'}
ANSVAR = (('arbetsledning', 'Arbetsledning'), ('utforande', 'Utförande'), ('granskning', 'Granskning'))
KID = re.compile(r'^k\d{2}$')
V12 = re.compile(r'^[0-9a-f]{12}$')
STAMP = re.compile(r'^\d{8}T\d{6}Z$')
MAX_FIL = 512 * 1024
TEXTFILER = ('.astro', '.css', '.js', '.mjs', '.ts', '.json', '.md', '.html', '.svg', '.txt', '.yml', '.yaml')


def _las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def _nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def _mtid(p):
    try:
        return os.stat(p).st_mtime
    except OSError:
        return 0


def _iso(t):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t)) if t else None


def _lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (OSError, TypeError, ValueError):
        return False


def _kontroller():
    rot = Path(__file__).resolve().parents[1] / 'kontroller'
    if str(rot) not in sys.path:
        sys.path.insert(0, str(rot))


def ansvar_for(roll):
    """Vilket av de tre ansvaren en roll hör till: skaparna och förfiningen utför, kritikerna, panelen, jämförelsen och
    planprövningen granskar; research och plan är utförande i flödets mening."""
    _kontroller()
    import observation
    r = str(roll or '')
    if r.startswith('planprovning'):
        return 'granskning'
    return {'granskare': 'granskning'}.get(observation.sida(r), 'utforande')


def konfigurerade(dash):
    """Modellerna som är konfigurerade per ansvar i dag, ur motorns egna konstanter (ingen ändras här)."""
    _kontroller()
    import atelje
    import kandidater
    import partner
    p = partner.profil()
    return {'arbetsledning': {'text': '%s, effort %s (partnersamtalet)' % (p['modell'], p['effort']), 'modell': p['modell']},
            'utforande': {'text': 'ateljén %s, effort %s; helbygget %s' % (atelje.MODELL, atelje.EFFORT, os.environ.get('NWP_MODELL') or 'opus[1m]'),
                          'modell': atelje.MODELL},
            'granskning': {'text': 'kandidatgranskarna %s; helbyggets granskare enligt kontroller/granska.py' % kandidater.GRANSKARE_MODELL,
                           'modell': kandidater.GRANSKARE_MODELL}}


# --- projekten ---

def projekt(dash):
    """Kunderna arbetsytan kan öppna: flödets kunder och skapandeflödets, med namn och testmarkering, senast aktiva först."""
    slugar = set(dash.flode_slugar()) | set(dash.prototyp_slugar())
    ut = []
    for s in slugar:
        v = dash.las_json(dash.UNDERLAG / s / 'VERKSAMHET.json') or {}
        aktiv = max(_mtid(dash.UNDERLAG / s / 'atelje' / 'STATUS.json'), _mtid(dash.UNDERLAG / s / 'atelje' / 'sessioner'),
                    _mtid(dash.KUNDER / s / 'korningar'), _mtid(dash.UNDERLAG / s / 'ateljestarter'))
        ut.append({'slug': s, 'namn': v.get('namn') if isinstance(v, dict) else None, 'testdata': bool(isinstance(v, dict) and v.get('fiktiv')),
                   'senast_andrad': _iso(aktiv)})
    return sorted(ut, key=lambda x: (x['senast_andrad'] or '', x['slug']), reverse=True)


# --- sessionerna ---

def _lage_ateljesession(post, ob, akt):
    """(läge, text) för en session i ateljéns förteckning. Livet avgörs av processen (pagar: pid:en är en levande nästlad
    claude-session), aldrig av hur nyligen något hände; ett avslut är inget godkännande."""
    utfall = str(post.get('utfall') or '')
    if post.get('slut'):
        if utfall == 'avslutad, kod 0':
            fel = bool(((ob or {}).get('slut') or {}).get('fel'))
            return ('avbruten', 'avslutad med fel i sessionens svar') if fel else ('avslutad', 'avslutad %s' % post['slut'])
        m = re.search(r'kod -(\d+)', utfall)
        if m:  # en negativ slutkod är en signal: processen avbröts utifrån, till exempel av ett stopp
            return 'avbruten', 'avbruten av signal %s (%s)' % (m.group(1), utfall)
        return 'avbruten', utfall or 'avslutad utan känt utfall'
    if post.get('pagar'):
        if not post.get('transkript'):
            return 'startar', 'processen lever; transkriptet har inte observerats än'
        if akt and akt.get('pagaende'):
            return 'verktyg', 'väntar på %s' % ', '.join(akt['pagaende'][-2:])
        return 'aktiv', 'processen lever'
    if post.get('pid') and not _lever(post['pid']):
        return 'avbruten', 'inget slutbesked: processen lever inte och sessionens slut observerades aldrig'
    if post.get('pid'):
        return 'okant', 'processen %s lever men är inte en session ur flödet (pid:en kan ha återanvänts)' % post['pid']
    return 'okant', post.get('ofullstandig') or 'ingen process och inget slut i förteckningen'


def ateljesessioner(dash, slug, korning, blind):
    """Ateljéns sessioner i den aktuella körningen (förteckningen arkiveras vid varje ny körning), med läge och aktivitet."""
    _kontroller()
    import bildkedja
    import observation
    ut = []
    poster = observation.sessioner(slug)
    for post in poster:
        if post.get('ofullstandig') and not post.get('session_id'):
            ut.append({'session_id': None, 'roll': None, 'ansvar': 'utforande', 'lage': 'okant', 'lage_text': post['ofullstandig'],
                       'kalla': 'ateljén'})
            continue
        if korning.get('startad') and str(post.get('start') or '') < str(korning['startad']):
            continue  # en äldre körnings session som ligger kvar (förteckningen arkiveras vid nästa start)
        akt = None
        tr = bildkedja.transkript(post['session_id'])
        if tr:
            akt, _skal = observation.aktivitet(tr, slug, vagar=not blind)
        ob = post.get('observation') or {}
        lage, text = _lage_ateljesession(post, ob, akt)
        ut.append({'session_id': post['session_id'], 'roll': post.get('roll'), 'ansvar': ansvar_for(post.get('roll')),
                   'kandidat': post.get('kandidat'), 'korning': korning.get('id'), 'start': post.get('start'), 'slut': post.get('slut'),
                   'utfall': post.get('utfall'), 'pid': post.get('pid'), 'lage': lage, 'lage_text': text,
                   'foralder': {'typ': 'ateljéns arbetare', 'pid': korning.get('pid'), 'start_id': korning.get('start_id')},
                   'modell_konfigurerad': post.get('modell'), 'modell_observerad': ob.get('modell'),
                   'senaste_handelse': ob.get('senaste_handelse'), 'kontext': ob.get('kontext'),
                   'komprimeringar': len(ob.get('komprimeringar') or []), 'nekade': ob.get('nekade') or 0,
                   'aktivitet': akt, 'lasfel': ob.get('lasfel'), 'ofullstandig': post.get('ofullstandig'), 'kalla': 'ateljén'})
    return ut


def _init_ur_logg(f):
    """Sessionens id, modell och Claude Codes version ur stream-json-loggens första init-rad (de första 256 kB)."""
    try:
        with open(f, 'rb') as fh:
            data = fh.read(256 * 1024)
    except OSError:
        return {}
    for rad in data.split(b'\n'):
        try:
            r = json.loads(rad)
        except ValueError:
            continue
        if isinstance(r, dict) and r.get('type') == 'system' and r.get('subtype') == 'init':
            return {'session_id': r.get('session_id'), 'modell': r.get('model'), 'claude_code': r.get('claude_code_version')}
    return {}


def helbygge(dash, slug, blind):
    """Helbyggets körningar (kunder/<slug>/korningar/<stämpel>/), nyast först, med kor.sh:s session ur stream-json-loggen.
    START.json bär start-id:t från Flöde (NWP_FLODE_START_ID), SLUT.json slutbeskedet; utan slutpost och med en död kor.sh
    är körningen avbruten utan slutbesked."""
    _kontroller()
    import observation
    k = dash.KUNDER / slug
    kat = sorted((p for p in (k / 'korningar').glob('*') if p.is_dir() and STAMP.fullmatch(p.name)), key=lambda p: p.name, reverse=True) \
        if (k / 'korningar').is_dir() else []
    korningar, sessioner = [], []
    for i, d in enumerate(kat[:5]):
        start = dash.las_json(d / 'START.json') or {}
        slut = dash.las_json(d / 'SLUT.json')
        lever = bool(start.get('pid') and _lever(start['pid']))
        lage = 'avslutad' if isinstance(slut, dict) else 'aktiv' if lever else 'avbruten'
        korningar.append({'id': d.name, 'start_id': start.get('start_id'), 'start': start.get('start'), 'pid': start.get('pid'),
                          'lage': lage, 'slutkod': (slut or {}).get('slutkod') if isinstance(slut, dict) else None,
                          'slutpost': 'kunder/%s/korningar/%s/SLUT.json' % (slug, d.name) if isinstance(slut, dict) else None,
                          'uteblev': (d / 'UTEBLEV.json').is_file()})
        logg = k / ('korning-%s.jsonl' % d.name)
        if i == 0 and logg.is_file():
            init = _init_ur_logg(logg)
            akt, skal = observation.aktivitet(logg, slug, vagar=True)
            ob = observation.sammanfattning(logg, slug) or {}
            if isinstance(slut, dict):
                sl, text = 'avslutad', 'slutkod %s' % slut.get('slutkod')
            elif lever:
                sl, text = ('verktyg', 'väntar på %s' % ', '.join(akt['pagaende'][-2:])) if akt and akt.get('pagaende') else ('aktiv', 'kor.sh lever')
            else:
                sl, text = 'avbruten', 'inget slutbesked: kor.sh lever inte och ingen slutpost finns'
            sessioner.append({'session_id': init.get('session_id'), 'roll': 'helbygge', 'ansvar': 'utforande', 'kandidat': None,
                              'korning': d.name, 'start': start.get('start'), 'slut': (slut or {}).get('datum') if isinstance(slut, dict) else None,
                              'pid': start.get('pid'), 'lage': sl, 'lage_text': text,
                              'foralder': {'typ': 'kor.sh', 'pid': start.get('pid'), 'start_id': start.get('start_id')},
                              'modell_konfigurerad': os.environ.get('NWP_MODELL') or 'opus[1m]', 'modell_observerad': init.get('modell') or ob.get('modell'),
                              'senaste_handelse': ob.get('senaste_handelse'), 'kontext': ob.get('kontext'),
                              'komprimeringar': len(ob.get('komprimeringar') or []), 'nekade': ob.get('nekade') or 0, 'aktivitet': akt,
                              'ofullstandig': skal, 'kalla': 'helbygget'})
    return korningar, sessioner


def startjournal(dash, slug):
    """Flödets startbegäranden (underlag/<slug>/ateljestarter/<start-id>.json), nyast först: mottagen, startad, stopp
    begärt och slut, med processens liv prövat nu. Journalen är ett mottagningsbesked, inte arbetets resultat."""
    d = dash.UNDERLAG / slug / 'ateljestarter'
    ut = []
    for f in sorted(d.glob('*.json'), key=_mtid, reverse=True)[:12] if d.is_dir() else []:
        j = dash.las_json(f)
        if not isinstance(j, dict):
            ut.append({'start_id': f.stem, 'status': 'oläslig'})
            continue
        pid = j.get('barn_pid') or j.get('pid')
        ut.append({'start_id': f.stem, 'handling': j.get('handling'), 'tid': j.get('tid'), 'status': j.get('status'),
                   'slutkod': j.get('slutkod'), 'stopp_begart': bool(j.get('stoppbegard')), 'stopp_sent': bool(j.get('stoppbegard_sen')),
                   'fel': str(j.get('fel'))[:300] if j.get('fel') else None, 'process_lever': bool(pid and _lever(pid)) if pid else None})
    return ut


def roller(sessioner, korning, konf, partnerlage):
    """De tre ansvaren med sina verkliga sessioner. Ett ansvar utan session i körningen står som väntande; en konfigurerad
    men inte startad granskare är ingen aktiv session."""
    ut = {}
    aktiv = korning.get('arbetaren') == 'lever'
    for nyckel, rubrik in ANSVAR:
        egna = [s for s in sessioner if s.get('ansvar') == nyckel]
        if nyckel == 'arbetsledning':
            lage = partnerlage or 'vantar'
            text = 'partnersamtalet: ' + LAGEN.get(lage, lage)
        elif egna:
            lev = [s for s in egna if s['lage'] in ('aktiv', 'verktyg', 'startar')]
            lage = lev[0]['lage'] if lev else egna[0]['lage']
            text = '%d sessioner i körningen, %d lever' % (len(egna), len(lev))
        else:
            lage = 'vantar'
            text = ('ingen session för %s har startat i körningen%s' % (rubrik.lower(), ' än; körningen pågår' if aktiv else ''))
        if nyckel != 'arbetsledning' and korning.get('vantar_pa_agaren') and lage not in ('aktiv', 'verktyg', 'startar'):
            text += '; körningen väntar på ditt beslut'
        ut[nyckel] = {'rubrik': rubrik, 'lage': lage, 'lage_text': text, 'sessioner': [s.get('session_id') for s in egna],
                      'konfigurerad': konf.get(nyckel, {}).get('text')}
    return ut


# --- läget ---

def _korning(dash, slug):
    _kontroller()
    import atelje
    st = dash.las_json(dash.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    if not st:
        return {}
    pid = st.get('pid')
    lever = bool(pid and _lever(pid))
    avslutad = st.get('steg') in atelje.AVSLUTADE
    arbetaren = 'lever' if lever and not avslutad else 'lever inte' if pid else 'okänt'
    vantar = st.get('steg') in ('klar_for_bedomning', 'klar') and not lever
    return {'id': st.get('startad'), 'startad': st.get('startad'), 'lage': st.get('lage'), 'steg': st.get('steg'), 'fas': st.get('fas'),
            'start_id': st.get('start_id'), 'start_handling': st.get('start_handling'), 'pid': pid, 'arbetaren': arbetaren,
            'avslutad': avslutad, 'avbruten': atelje.avbruten(st), 'fel': str(st.get('fel'))[:400] if st.get('fel') else None,
            'vantar_pa_agaren': vantar, 'klar': st.get('klar')}


def _moment(steg):
    """Det moment som pågår eller väntar på ägaren; annars det senaste som påbörjats."""
    for s in steg:
        if s.get('status') in ('pågår', 'väntar på ägaren'):
            return {'nr': s['nr'], 'namn': s['namn'], 'status': s['status']}
    gjorda = [s for s in steg if s.get('status') not in ('inte påbörjat', 'inte observerat')]
    s = gjorda[-1] if gjorda else (steg[0] if steg else None)
    return {'nr': s['nr'], 'namn': s['namn'], 'status': s['status']} if s else None


def kandidatlista(dash, slug, blind):
    """Kandidaterna med neutrala etiketter (kandidater.sammanstall, som vyn Prototyp), version, förhandsvisning och den
    bevarade ögonblicksbilden. Före ägarens första val utan skapare- och granskningstext."""
    _kontroller()
    import kandidater
    ut = []
    try:
        kand = kandidater.sammanstall(slug)
    except Exception as e:  # noqa: BLE001
        return [], '%s: %s' % (type(e).__name__, str(e)[:160])
    for k in kand:
        kid = k.get('id')
        if not KID.fullmatch(str(kid or '')):
            continue
        st = kandidater.las_status(slug, kid)
        dist = kandidater.ksajt(slug, kid) / 'dist' / 'index.html'
        versioner = sorted((p.name for p in (kandidater.kdir(slug, kid) / 'versioner').glob('*')
                            if V12.fullmatch(p.name) and kandidater.bevarad(slug, kid, p.name)), reverse=False)
        b = k.get('bilder') or {}
        ut.append({'id': kid, 'etikett': k.get('etikett') or kid, 'status': k.get('status'), 'statustext': k.get('statustext') or k.get('status'),
                   'version': str(st.get('version') or '')[:12] or None, 'version_hel': st.get('version'), 'fotograferad': st.get('fotograferad'),
                   'preview': {'url': '/visa/%s/%s' % (slug, kid), 'finns': dist.is_file(),
                               'byggd': _iso(_mtid(dist)) if dist.is_file() else None},
                   'snapshot': {'390': b.get('390-forsta'), '1440': b.get('1440-forsta') or b.get('1280-forsta'), 'version': str(st.get('version') or '')[:12] or None,
                                'tid': st.get('fotograferad')},
                   'versioner': versioner})
    return ut, None


def overlamningar(dash, slug, kandidater_, korning):
    """Ägarens ändringar som skickats från arbetsytan (domloggens rader med arbetsyta-fältet), med det som går att belägga
    efteråt: skickad (raden finns), mottagen (en körning startade efter raden), arbete startat (en session för kandidaten
    startade efter raden), resultat sparat (kandidaten har en ny version) och verifierat (ägarens senare beslut över den
    nya versionen). Inget av stegen sätts av arbetsytan själv."""
    _kontroller()
    import skapande
    try:
        domar = skapande.domar(slug, dash.UNDERLAG)
    except Exception:  # noqa: BLE001
        return []
    ut = []
    nuvarande = {k['id']: k for k in kandidater_}
    sess = None
    for d in domar:
        a = d.get('arbetsyta') if isinstance(d.get('arbetsyta'), dict) else None
        if not a:
            continue
        tid = str(d.get('tid') or '')
        kand = [x for x in d.get('kandidater') or [] if isinstance(x, dict)]
        kid = (kand[0] if kand else {}).get('id') or a.get('kandidat')
        fore = str((kand[0] if kand else {}).get('version') or a.get('version') or '')[:12]
        steg = {'skickad': tid}
        if korning.get('startad') and str(korning['startad']) > tid:
            steg['mottagen'] = korning['startad']
        if sess is None:
            _kontroller()
            import observation
            sess = observation.sessioner(slug)
        startad = sorted(str(s.get('start')) for s in sess if s.get('kandidat') == kid and str(s.get('start') or '') > tid)
        if startad:
            steg['arbete_startat'] = startad[0]
        ny = (nuvarande.get(kid) or {}).get('version')
        if ny and fore and ny != fore and 'arbete_startat' in steg:
            steg['resultat_sparat'] = ny
            senare = [x for x in domar if str(x.get('tid') or '') > tid and skapande.ar_agarens(x)
                      and any(isinstance(y, dict) and y.get('id') == kid and str(y.get('version') or '')[:12] == ny for y in x.get('kandidater') or [])]
            if senare:
                steg['verifierat'] = senare[0].get('tid')
        ut.append({'id': a.get('andring_id'), 'tid': tid, 'beslut': d.get('beslut'), 'kandidat': kid, 'version': fore or None,
                   'vy': a.get('vy'), 'sida': a.get('sida'), 'del': a.get('del'), 'avsandare': d.get('kalla'), 'steg': steg,
                   'aktuell': bool(not ny or ny == fore)})
    return ut[-10:]


def lage(dash, slug):
    """Arbetsytans läge för en kund. Varje del som fallerar står som ofullständig med skälet; resten visas ändå."""
    _kontroller()
    import partner
    ut = {'schema': SCHEMA, 'tid': _nu(), 'slug': slug, 'ofullstandig': []}
    v = dash.las_json(dash.UNDERLAG / slug / 'VERKSAMHET.json') or {}
    ut['projekt'] = {'slug': slug, 'namn': v.get('namn') if isinstance(v, dict) else None,
                     'testdata': bool(isinstance(v, dict) and v.get('fiktiv'))}
    try:
        f = dash.flode(slug)
    except Exception as e:  # noqa: BLE001
        f = {'blind': True, 'steg': [], 'handlingar': [], 'besked': None}
        ut['ofullstandig'].append('flödet: %s: %s' % (type(e).__name__, str(e)[:160]))
    blind = bool(f.get('blind'))
    ut.update({'blind': blind, 'ab_dold': bool(f.get('ab_dold')), 'steg': f.get('steg') or [], 'besked': f.get('besked'),
               'handlingar': f.get('handlingar') or [], 'startmiljo': f.get('startmiljo')})
    ut['moment'] = _moment(ut['steg'])
    korning = _korning(dash, slug)
    ut['korning'] = korning
    if f.get('ab_dold'):  # en arm i en blind jämförelse: inget om ateljén, sessionerna eller bygget före valet (som flode)
        ut.update({'kandidater': [], 'sessioner': [], 'helbygge': [], 'startjournal': [], 'overlamningar': [], 'roller': {},
                   'preview': None, 'partner': None})
        return ut
    kand, fel = kandidatlista(dash, slug, blind) if korning else ([], None)
    if fel:
        ut['ofullstandig'].append('kandidaterna: ' + fel)
    ut['kandidater'] = kand
    sessioner = []
    for namn, fn in (('ateljéns sessioner', lambda: ateljesessioner(dash, slug, korning, blind) if korning else []),):
        try:
            sessioner += fn()
        except Exception as e:  # noqa: BLE001
            ut['ofullstandig'].append('%s: %s: %s' % (namn, type(e).__name__, str(e)[:160]))
    try:
        hk, hs = helbygge(dash, slug, blind)
        ut['helbygge'] = hk
        sessioner += hs
    except Exception as e:  # noqa: BLE001
        ut['helbygge'] = []
        ut['ofullstandig'].append('helbygget: %s: %s' % (type(e).__name__, str(e)[:160]))
    try:
        p = partner.lage(dash, slug)
    except Exception as e:  # noqa: BLE001
        p = None
        ut['ofullstandig'].append('partnersamtalet: %s: %s' % (type(e).__name__, str(e)[:160]))
    ut['partner'] = p
    if p and p.get('session'):
        sessioner.insert(0, p['session'])
    ut['sessioner'] = sessioner
    try:
        ut['startjournal'] = startjournal(dash, slug)
    except Exception as e:  # noqa: BLE001
        ut['startjournal'] = []
        ut['ofullstandig'].append('startjournalen: %s: %s' % (type(e).__name__, str(e)[:160]))
    try:
        konf = konfigurerade(dash)
    except Exception as e:  # noqa: BLE001
        konf = {}
        ut['ofullstandig'].append('modellprofilen: %s: %s' % (type(e).__name__, str(e)[:160]))
    ut['roller'] = roller(sessioner, korning, konf, (p or {}).get('lage'))
    ut['overlamningar'] = overlamningar(dash, slug, kand, korning)
    ut['preview'] = preview(dash, slug, kand, korning)
    ut['observation'] = {'senast_last': _nu(), 'ofullstandig': list(ut['ofullstandig'])}
    return ut


def preview(dash, slug, kand, korning):
    """Huvudmaterialets förhandsvisningar, märkta: arbetsversionen (det levande bygget, kan ändras under arbetet), den
    bevarade ögonblicksbilden (fotograferad version) och exporten. Saknas bygget visas den senaste fungerande
    ögonblicksbilden som äldre, aldrig som aktuell."""
    ut = []
    sajt = dash.KUNDER / slug / 'sajt' / 'dist' / 'index.html'
    if sajt.is_file():
        ut.append({'typ': 'arbetsversion', 'kalla': 'helbygget', 'url': '/visa/%s' % slug, 'byggd': _iso(_mtid(sajt)),
                   'etikett': 'Helbyggets arbetsversion (kunder/%s/sajt/dist), byggd %s' % (slug, _iso(_mtid(sajt)))})
    for k in kand:
        if k['preview']['finns']:
            ut.append({'typ': 'arbetsversion', 'kalla': 'kandidat', 'kandidat': k['id'], 'url': k['preview']['url'], 'byggd': k['preview']['byggd'],
                       'etikett': '%s, arbetsversion byggd %s' % (k['etikett'], k['preview']['byggd'])})
        if k['snapshot'].get('390') or k['snapshot'].get('1440'):
            ut.append({'typ': 'snapshot', 'kalla': 'kandidat', 'kandidat': k['id'], 'bilder': {'390': k['snapshot'].get('390'), '1440': k['snapshot'].get('1440')},
                       'version': k['snapshot'].get('version'), 'tid': k['snapshot'].get('tid'), 'aldre': not k['preview']['finns'],
                       'etikett': '%s, bevarad version %s (skärmbild %s)%s' % (k['etikett'], k['snapshot'].get('version') or '?', k['snapshot'].get('tid') or '?',
                                                                            '; bygget saknas just nu, det här är den senaste fungerande' if not k['preview']['finns'] else '')})
    _kontroller()
    try:
        import exportera
        e = exportera.aktuell(slug)
    except Exception:  # noqa: BLE001
        e = None
    if e and e.get('commit'):
        ut.append({'typ': 'export', 'kalla': 'kundrepo', 'commit': str(e['commit'])[:12], 'aktuell': bool(e.get('aktuell')),
                   'etikett': 'Exportversion: commit %s i kundrepot%s' % (str(e['commit'])[:12], '' if e.get('aktuell') else ' (inte aktuell)')})
    return ut


def signatur(dash, slug):
    """En billig signatur över det läget läses ur: ändringstider och storlek för statusfiler, förteckningar, journaler och
    transkript, och liv för processerna. Ändras den läses läget om; annars inte (strömmen)."""
    _kontroller()
    import bildkedja
    u, k = dash.UNDERLAG / slug, dash.KUNDER / slug
    delar = []

    def lagg(p):
        try:
            s = os.stat(p)
            delar.append('%s:%d:%d' % (p, s.st_mtime_ns, s.st_size))
        except OSError:
            delar.append('%s:-' % p)
    for p in (u / 'atelje' / 'STATUS.json', u / 'DESIGNDOMAR.jsonl', u / 'atelje' / 'sessioner', u / 'ateljestarter', k / 'korningar',
              k / 'sajt' / 'dist' / 'index.html', u / 'arbetsyta' / 'PARTNER.json', u / 'atelje' / 'KANDIDATPLAN.json', k / 'DOM.json'):
        lagg(p)
    for p in sorted((u / 'atelje' / 'kandidater').glob('k[0-9][0-9]/STATUS.json')):
        lagg(p)
    for p in sorted((u / 'ateljestarter').glob('*.json'))[-6:]:
        lagg(p)
    for p in sorted((u / 'atelje' / 'sessioner').glob('*.json')):
        lagg(p)
        post = dash.las_json(p) or {}
        if not post.get('slut'):
            tr = bildkedja.transkript(str(post.get('session_id') or '')) if bildkedja.SESSION.match(str(post.get('session_id') or '')) else None
            if tr:
                lagg(tr)
            delar.append('pid%s:%s' % (post.get('pid'), _lever(post.get('pid')) if post.get('pid') else '-'))
    for p in sorted(k.glob('korning-*.jsonl'))[-1:]:
        lagg(p)
    st = dash.las_json(u / 'atelje' / 'STATUS.json') or {}
    if st.get('pid'):
        delar.append('arbetare:%s' % _lever(st['pid']))
    pj = dash.las_json(u / 'arbetsyta' / 'PARTNER.json') or {}
    for m in (pj.get('meddelanden') or [])[-2:]:
        if isinstance(m, dict) and m.get('pid'):
            delar.append('partner%s:%s' % (m['pid'], _lever(m['pid'])))
            if m.get('svarsfil'):
                lagg(dash.UNDERLAG / slug / 'arbetsyta' / 'partner' / Path(str(m['svarsfil'])).name)
    if pj.get('session_id') and bildkedja.SESSION.match(str(pj['session_id'])):
        tr = bildkedja.transkript(pj['session_id'])
        if tr:
            lagg(tr)
    return hashlib.sha256('\n'.join(delar).encode()).hexdigest()[:16]


# --- koden: filer och diff mot en namngiven version ---

def _saker_fil(bas, rel):
    """Filen rel under bas, eller None: ingen absolut väg, inget '..', ingen länk i någon del, en vanlig fil som ligger
    under basens verkliga väg och är högst MAX_FIL byte."""
    rel = str(rel or '')
    if not rel or rel.startswith('/') or '\x00' in rel or any(d in ('', '.', '..') for d in rel.split('/')):
        return None
    bas = Path(bas)
    try:
        if bas.is_symlink() or not bas.is_dir():
            return None
        p = bas
        for d in rel.split('/'):
            p = p / d
            if stat.S_ISLNK(os.lstat(p).st_mode):
                return None
        st_ = os.stat(p)
        verklig = os.path.realpath(p)
        if not stat.S_ISREG(st_.st_mode) or st_.st_size > MAX_FIL or not verklig.startswith(os.path.realpath(bas) + os.sep):
            return None
    except OSError:
        return None
    return p


def _arbetsfiler(slug, kid, blind):
    """Kandidatens arbetsversion i projektet som det står nu, med versionens namn på filerna (kandidater.projektets_version):
    kod/ ur sidorna utan mallens sidor, kod-src/ ur resten av src/ utan kundens bilder, och DESIGN.md (inte före ditt
    första val: den bär skaparens förklaringar)."""
    _kontroller()
    import kandidater
    sajt = kandidater.ksajt(slug, kid)
    ut = {}
    if not blind and (sajt / 'DESIGN.md').is_file() and not (sajt / 'DESIGN.md').is_symlink():
        ut['DESIGN.md'] = sajt / 'DESIGN.md'
    for bas, namn, ta_med in ((sajt / 'src' / 'pages', 'kod', lambda r: r.parts[0] not in kandidater.MALLSIDOR),
                              (sajt / 'src', kandidater.KODSRC, kandidater.src_ovrigt)):
        if not bas.is_dir() or bas.is_symlink():
            continue
        for katalog, kataloger, filer in os.walk(bas, followlinks=False):
            kataloger[:] = sorted(x for x in kataloger if not (Path(katalog) / x).is_symlink() and x != 'node_modules')
            for fn in sorted(filer):
                p = Path(katalog) / fn
                r = p.relative_to(bas)
                if p.is_symlink() or not p.is_file() or not ta_med(r) or p.suffix.lower() not in TEXTFILER:
                    continue
                ut['%s/%s' % (namn, r.as_posix())] = p
    return ut


def _versionsfiler(slug, kid, v12, blind):
    _kontroller()
    import kandidater
    if not V12.fullmatch(str(v12 or '')) or not kandidater.bevarad(slug, kid, v12):
        return None
    d = kandidater.kdir(slug, kid) / 'versioner' / v12
    return {r: p for r, p in kandidater.version_filer(d) if not r.startswith(kandidater.MATERIAL + '/')
            and (r != 'DESIGN.md' or not blind) and Path(r).suffix.lower() in TEXTFILER}


def kod(dash, slug, kid, rel=None, mot=None):
    """Kandidatens filer (arbetsversionen) och, för en fil, dess text och en diff mot den namngivna bevarade versionen mot
    (versioner/<v12>/). Bara textfiler under projektets egna kataloger; ingenting skrivs."""
    _kontroller()
    import kandidater
    if not KID.fullmatch(str(kid or '')) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    blind = bool(dash.flode(slug).get('blind'))
    arbete = _arbetsfiler(slug, kid, blind)
    st = kandidater.las_status(slug, kid)
    versioner = [p.name for p in sorted((kandidater.kdir(slug, kid) / 'versioner').glob('*'), key=_mtid) if V12.fullmatch(p.name)
                 and kandidater.bevarad(slug, kid, p.name)]
    mot = mot or (str(st.get('version') or '')[:12] if str(st.get('version') or '')[:12] in versioner else (versioner[-1] if versioner else None))
    jamf = _versionsfiler(slug, kid, mot, blind) if mot else None
    filer = sorted(set(arbete) | set(jamf or {}))
    ut = {'kandidat': kid, 'arbetsversion': 'kunder/%s/kandidater/%s/sajt (som det står nu)' % (slug, kid), 'mot': mot, 'versioner': versioner,
          'fotograferad': str(st.get('version') or '')[:12] or None, 'blind': blind,
          'filer': [{'fil': f, 'andrad': (f in arbete) != (f in (jamf or {})) or (jamf is not None and f in arbete and f in jamf
                                                                                and _las_bytes(arbete[f]) != _las_bytes(jamf[f])),
                     'ny': jamf is not None and f in arbete and f not in jamf, 'borttagen': jamf is not None and f not in arbete} for f in filer]}
    if rel:
        if rel not in arbete and rel not in (jamf or {}):
            raise ValueError('filen hör inte till kandidatens kod')
        a = _text(arbete.get(rel))
        b = _text((jamf or {}).get(rel))
        ut['fil'] = {'fil': rel, 'text': a, 'finns': rel in arbete,
                     'diff': list(difflib.unified_diff((b or '').splitlines(), (a or '').splitlines(), 'version %s' % mot, 'arbetsversionen',
                                                       lineterm='', n=3))[:4000] if mot and jamf is not None else None,
                     'sokvag': _relativ(dash, arbete.get(rel)) if rel in arbete else None}
    return ut


def _las_bytes(p):
    try:
        return Path(p).read_bytes() if os.path.getsize(p) <= MAX_FIL else None
    except OSError:
        return None


def _text(p):
    if not p:
        return None
    b = _las_bytes(p)
    if b is None:
        return None
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return None


def _relativ(dash, p):
    try:
        return str(Path(p).relative_to(dash.ROOT))
    except (ValueError, TypeError):
        return None


# --- körningsloggen ---

HEMLIGT = re.compile(r'(?i)(api[_-]?key|token|secret|nyckel|password|lösenord|authorization)(["\'=:\s]+)([^\s"\']{6,})')


def korningslogg(dash, slug, rader=200):
    """Körningens loggar som text: arbetarens logg i startjournalen och ateljéns arbetare.log, helbyggets vakt- och
    webbtjänstloggar. Före ägarens första val visas bara journalens rader (loggarna kan bära bedömningar). Värden efter
    ord som nyckel, token och lösenord maskeras; texten visas som text, aldrig som HTML."""
    f = dash.flode(slug)
    blind = bool(f.get('blind')) or bool(f.get('ab_dold'))
    u, k = dash.UNDERLAG / slug, dash.KUNDER / slug
    kallor = []
    st = dash.las_json(u / 'atelje' / 'STATUS.json') or {}
    if st.get('start_id'):
        kallor.append(u / 'ateljestarter' / ('%s.log' % st['start_id']))
    kallor.append(u / 'atelje' / 'arbetare.log')
    senaste = sorted((p for p in (k / 'korningar').glob('*') if p.is_dir() and STAMP.fullmatch(p.name)), key=lambda p: p.name) if (k / 'korningar').is_dir() else []
    if senaste:
        kallor += [k / ('korvakt-%s.log' % senaste[-1].name), k / ('webbtjanst-%s.log' % senaste[-1].name), k / 'startkontroll.log']
    ut = []
    for p in kallor:
        if not p.is_file() or p.is_symlink():
            continue
        if blind:
            ut.append({'fil': _relativ(dash, p), 'rader': [], 'dold': 'visas efter ditt första val: loggen kan bära bedömningar'})
            continue
        try:
            with open(p, 'rb') as fh:
                fh.seek(max(0, os.path.getsize(p) - 64 * 1024))
                text = fh.read().decode('utf-8', errors='replace')
        except OSError as e:
            ut.append({'fil': _relativ(dash, p), 'rader': [], 'fel': type(e).__name__})
            continue
        r = [HEMLIGT.sub(lambda m: m.group(1) + m.group(2) + '•••', x) for x in text.splitlines()[-rader:]]
        ut.append({'fil': _relativ(dash, p), 'rader': r, 'andrad': _iso(_mtid(p))})
    return {'tid': _nu(), 'blind': blind, 'loggar': ut}


# --- ägarens ändring ---

ANDRING_ID = re.compile(r'^[A-Za-z0-9_-]{8,80}$')
ANDRINGSBESLUT = ('valj', 'putsa')


def skicka_andring(dash, slug, data):
    """Ägarens ändring från arbetsytan: ett beslut i domloggen genom samma väg som vyn Prototyp (server.spara_prototyp,
    atelje.doma), bundet till körningen, kandidaten och versionen ägaren såg, med arbetsytans markering (vy, sida, del)
    och ändringens id på raden. Samma id ger samma rad (dubbelklick, två flikar, tappat svar). En annan körning, en
    inaktuell version eller en körning som inte väntar på ditt beslut nekas med skälet (Inaktuell, HTTP 409); inget
    vidarebefordras blint, och inget arbete startar här: nästa handling (Förfina de valda) startas uttryckligen."""
    _kontroller()
    import kandidater
    import skapande
    if not isinstance(data, dict):
        raise ValueError('ändringen ska vara ett objekt')
    aid, text, beslut = str(data.get('andring_id') or ''), str(data.get('text') or '').strip(), data.get('beslut') or 'valj'
    kid, version, korning = str(data.get('kandidat') or ''), str(data.get('version') or ''), str(data.get('korning') or '')
    if not ANDRING_ID.fullmatch(aid):
        raise ValueError('ett ändrings-id behövs')
    if beslut not in ANDRINGSBESLUT:
        raise ValueError('en ändring är valj (förfina kandidaten) eller putsa (förfina vidare)')
    if not text or len(text) > 8000:
        raise ValueError('skriv vad som ska ändras (högst 8000 tecken)')
    if not KID.fullmatch(kid) or kid not in kandidater.lista(slug):
        raise ValueError('välj kandidaten ändringen gäller')
    markering = {k: str(data.get(k))[:200] for k in ('vy', 'sida', 'del') if data.get(k)}
    with _ANDRING_LAS:
        for d in skapande.domar(slug, dash.UNDERLAG):
            a = d.get('arbetsyta') if isinstance(d.get('arbetsyta'), dict) else {}
            if a.get('andring_id') == aid:
                return {'ok': True, 'upprepat': True, 'dom': d}
        st = dash.las_json(dash.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
        if korning and korning != str(st.get('startad') or ''):
            raise Inaktuell('körningen har bytts sedan du skrev ändringen (din %s, nu %s); läs läget och skriv om den mot den aktuella' % (korning, st.get('startad')))
        nu_v = str(kandidater.las_status(slug, kid).get('version') or '')
        if version and version != nu_v:
            raise Inaktuell('kandidaten har en ny version sedan du skrev ändringen (din %s, nu %s); stäm av mot den aktuella' % (version[:12], nu_v[:12]))
        if st.get('steg') not in ('klar_for_bedomning', 'fel'):
            raise Inaktuell('körningen väntar inte på ditt beslut (steg %s); ändringen skickas inte' % st.get('steg'))
        del_ = '; '.join('%s: %s' % (k, v) for k, v in markering.items())
        res = dash.spara_kandidatbeslut(slug, st, {'beslut': beslut, 'kandidater': [{'id': kid, 'version': version or nu_v}],
                                                   'delar': {kid: (del_ + ' — ' if del_ else '') + text}, 'text': text},
                                        arbetsyta=dict(markering, andring_id=aid, kandidat=kid, version=(version or nu_v)[:12], korning=korning or None))
    return dict(res, upprepat=False)


class Inaktuell(ValueError):
    """En ändring eller ett beslut som gäller en äldre körning eller version: HTTP 409, med skälet."""


import threading as _threading  # noqa: E402
_ANDRING_LAS = _threading.Lock()


EDITOR = Path('/Applications/Visual Studio Code.app')


def oppna_i_editor(dash, slug, data):
    """Öppnar en fil ur kandidatens arbetsversion i ägarens editor (Visual Studio Code när den finns, annars macOS
    textredigerare), utan skal och bara en fil som kodvyn listar. Ingen skrivning sker här."""
    import subprocess
    if not isinstance(data, dict):
        raise ValueError('ange kandidat och fil')
    kid, rel = str(data.get('kandidat') or ''), str(data.get('fil') or '')
    _kontroller()
    import kandidater
    if not KID.fullmatch(kid) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    blind = bool(dash.flode(slug).get('blind'))
    p = _arbetsfiler(slug, kid, blind).get(rel)
    if not p or p.is_symlink() or not p.is_file():
        raise ValueError('filen hör inte till kandidatens arbetsversion')
    argv = ['open', '-a', str(EDITOR), str(p)] if EDITOR.is_dir() else ['open', '-t', str(p)]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    if r.returncode:
        raise ValueError('editorn kunde inte öppnas: %s' % (r.stderr.strip()[:200] or r.returncode))
    return {'ok': True, 'fil': rel, 'program': 'Visual Studio Code' if EDITOR.is_dir() else 'textredigeraren'}
