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
import threading
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


def dold(dash, slug):
    """(blind, ab_dold) på servervägen, stängt vid fel: en arm i en blind jämförelse som ägaren inte valt i än döljer allt
    om körningen (som flode och bygge), och en körning före ägarens första val är blind. Går jämförelsen eller flödet inte
    att läsa räknas kunden som dold respektive blind."""
    try:
        if dash.ab_oavgjord(slug):
            return True, True
    except Exception:  # noqa: BLE001
        return True, True
    try:
        f = dash.flode(slug)
    except Exception:  # noqa: BLE001
        return True, False
    return bool(f.get('blind')) or bool(f.get('ab_dold')), bool(f.get('ab_dold'))


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
        try:
            ab = bool(dash.ab_oavgjord(s))
        except Exception:  # noqa: BLE001
            ab = True
        aktiv = 0 if ab else max(_mtid(dash.UNDERLAG / s / 'atelje' / 'STATUS.json'), _mtid(dash.UNDERLAG / s / 'atelje' / 'sessioner'),
                                 _mtid(dash.KUNDER / s / 'korningar'), _mtid(dash.UNDERLAG / s / 'ateljestarter'))
        ut.append({'slug': s, 'namn': v.get('namn') if isinstance(v, dict) else None, 'testdata': bool(isinstance(v, dict) and v.get('fiktiv')),
                   'senast_andrad': _iso(aktiv)})
    return sorted(ut, key=lambda x: (x['senast_andrad'] or '', x['slug']), reverse=True)


# --- sessionerna ---

def _lage_ateljesession(post, ob, akt, svarsfel=None):
    """(läge, text) för en session i ateljéns förteckning. Livet avgörs av processen (pagar: pid:en är en levande nästlad
    claude-session), aldrig av hur nyligen något hände; ett avslut är inget godkännande. svarsfel: sessionens svarsfil
    (--output-format json) säger is_error; transkripten har ingen resultatrad."""
    utfall = str(post.get('utfall') or '')
    if post.get('slut'):
        if utfall == 'avslutad, kod 0':
            fel = bool(svarsfel) or bool(((ob or {}).get('slut') or {}).get('fel'))
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


def _svarsfel(dash, slug, post):
    """Sessionens svarsfil (svar-<roll>.json, i ateljén eller kandidatens katalog) säger is_error; None när den saknas."""
    namn = str(post.get('svar') or '')
    if not re.fullmatch(r'svar-[A-Za-z0-9_.-]{1,80}\.json', namn):
        return None
    rot = dash.UNDERLAG / slug / 'atelje'
    f = rot / 'kandidater' / post['kandidat'] / namn if KID.fullmatch(str(post.get('kandidat') or '')) else rot / namn
    d = dash.las_json(f) if f.is_file() and not f.is_symlink() else None
    # samma roll kan skriva om samma filnamn: svarsfilen gäller bara sessionen vars id den bär
    if not isinstance(d, dict) or str(d.get('session_id') or '') != str(post.get('session_id') or ''):
        return None
    return bool(d.get('is_error'))


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
        akt, sam = None, None
        tr = bildkedja.transkript(post['session_id'])
        if tr:
            akt, _skal = observation.aktivitet(tr, slug, vagar=not blind)
            try:
                sam = observation.sammanfattning(tr, slug)
            except Exception:  # noqa: BLE001 — kompetensraden är en extra
                sam = None
        ob = post.get('observation') or {}
        lage, text = _lage_ateljesession(post, ob, akt, _svarsfel(dash, slug, post))
        styr = styrning_for(slug, post['session_id'])
        ut.append({'session_id': post['session_id'], 'roll': None if blind else post.get('roll'), 'roll_dold': bool(blind),
                   'ansvar': ansvar_for(post.get('roll')),
                   'kandidat': post.get('kandidat'), 'korning': korning.get('id'), 'start': post.get('start'), 'slut': post.get('slut'),
                   'utfall': post.get('utfall'), 'pid': post.get('pid'), 'lage': lage, 'lage_text': text,
                   'foralder': {'typ': 'ateljéns arbetare', 'pid': korning.get('pid'), 'start_id': korning.get('start_id')},
                   'modell_konfigurerad': post.get('modell'), 'modell_observerad': ob.get('modell'),
                   'senaste_handelse': ob.get('senaste_handelse'), 'kontext': ob.get('kontext'),
                   'komprimeringar': len(ob.get('komprimeringar') or []), 'nekade': ob.get('nekade') or 0,
                   'aktivitet': akt, 'lasfel': ob.get('lasfel'), 'ofullstandig': post.get('ofullstandig'), 'kalla': 'ateljén',
                   'styrning': styr, 'kompetens': kompetensnivaer(sam, styr, blind)})
    return ut


def samverkan_kort(dash, slug, blind):
    """Bussens läge i korthet för huvudvyn: öppna meddelanden till ägaren, senaste ändring (vyn hämtar listan när den
    ändras) och projektets paus."""
    _kontroller()
    import meddelanden
    alla = meddelanden.alla(slug)
    kn = meddelanden.korning(slug)
    oppna = [m for m in alla if (m.get('avsandare') or {}).get('typ') != 'agare' and (m.get('mottagare') or {}).get('typ') == 'agare' and not m.get('beslut')]
    p = meddelanden.paus_galler(slug)
    return {'antal': len(alla), 'oppna': len(oppna), 'senast': max([h.get('tid') or '' for m in alla for h in m.get('handelser') or []] or [''] ) or None,
            'nyckel': '%d:%s' % (len(alla), max([str(len(m.get('handelser') or [])) + (m.get('id') or '') for m in alla] or [''])),
            'projektpaus': p and p.get('omfattning') == 'projekt' and {'begard': p.get('begard'), 'vantande_start': p.get('vantande_start')},
            'mandat': len([x for x in meddelanden.mandat(slug) if not x.get('aterkallat') and x.get('korning') == kn])}


def styrning_for(slug, sid):
    """Löparens läge för sessionen (kontroller/meddelanden.py, lopare.py), utan argumenten: om den går att nå med
    meddelanden och pausa, om paus är begärd eller gäller, och vilka verktyg som fortfarande arbetar."""
    _kontroller()
    import meddelanden
    s = meddelanden.sessionslage(slug, sid)
    if not s:
        return {'lopare': False, 'text': 'startad utan löpare: tar inte emot meddelanden och kan bara stoppas'}
    lever = not s.get('slut') and _lever(s.get('pid')) and _lever(s.get('lopare_pid'))
    p = meddelanden.paus_galler(slug, sid)
    lage = s.get('lage') if lever else 'avslutad'
    if lever and p and lage == 'arbetar':
        lage = 'paus_begard'
    return {'lopare': True, 'lever': lever, 'blind': bool(s.get('blind')), 'lage': lage, 'sedan': s.get('sedan'),
            'paus': p and {'omfattning': p.get('omfattning'), 'begard': p.get('begard')},
            'verktyg_kvar': s.get('verktyg_kvar') or [], 'turer': s.get('turer'), 'max_turer': s.get('max_turer'),
            'aterupptagen': s.get('aterupptagen'), 'avvisade': len(s.get('avvisade') or []),
            'kan_meddelas': lever and not s.get('blind'), 'kan_pausas': lever and lage == 'arbetar' and not p}


def kompetensnivaer(sam, styr, blind):
    """Kompetensen i fyra nivåer, var för sig (ägarens uppdrag 2026-10-09, punkt 10): erbjuden (skills i sessionens
    lista och MCP-servrarnas anslutning), laddad (skills aktiverade med skillverktyget eller vars SKILL.md lästs),
    anropad (MCP- och skillanrop) och belagd påverkan, som inte går att se i en session: den bedöms i kandidatens
    kompetenskvitto och granskning. Ingen nivå står för en annan."""
    if not sam:
        return None
    mcp = sam.get('mcp_lage') or {}
    return {'erbjuden': {'skills': sam.get('skills_erbjudna'), 'mcp': {k: v for k, v in mcp.items()} if mcp else None},
            'laddad': {'skills': sorted({x.get('skill') for x in sam.get('skills_laddade') or [] if x.get('skill')}),
                       'skillfiler': len(sam.get('skillfiler') or [])},
            'anropad': {'mcp': len(sam.get('mcp') or []), 'mcp_tjanster': sorted({x.get('tjanst') for x in sam.get('mcp') or [] if x.get('tjanst')}),
                        'skillanrop': len(sam.get('skills_laddade') or []),
                        'per_verktyg': {k: sum(v.values()) for k, v in (sam.get('verktyg') or {}).items() if isinstance(v, dict)}},
            'paverkan': 'inte observerbar i sessionen: bedöms i kandidatens kompetenskvitto och granskning' + (' (efter ditt första val)' if blind else '')}


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
        lever = bool(start.get('pid') and _lever(start['pid']) and 'kor.sh' in _kommando(start['pid']))
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


def _kommando(pid):
    _kontroller()
    try:
        import korregister
        return korregister.kommando(pid) or ''
    except Exception:  # noqa: BLE001
        return ''


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
                   'slutkod': j.get('slutkod'), 'stopp_begart': bool(j.get('stoppbegard') or j.get('stoppad')), 'stopp_sent': bool(j.get('stoppbegard_sen')),
                   'stopp_tid': j.get('stoppad') if isinstance(j.get('stoppad'), str) else j.get('stoppbegard_tid'),
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
        if nyckel == 'utforande' and korning.get('vantar_pa_agaren') and lage not in ('aktiv', 'verktyg', 'startar'):
            lage, text = 'beslut', text + '; körningen väntar på ditt beslut'
        elif nyckel == 'granskning' and korning.get('vantar_pa_agaren') and lage not in ('aktiv', 'verktyg', 'startar'):
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


def synliga_versioner(slug, kid, st, blind):
    """De bevarade versionerna ägaren får se. Före ägarens första val bara den aktuella (fotograferade): föreversionen
    före en förbättringsrunda håller kandidater.sammanstall tillbaka till dess, och en diff mot den skulle visa vad
    kritiken ändrade."""
    _kontroller()
    import kandidater
    alla = [p.name for p in sorted((kandidater.kdir(slug, kid) / 'versioner').glob('*'), key=_mtid)
            if V12.fullmatch(p.name) and kandidater.bevarad(slug, kid, p.name)]
    nu12 = str(st.get('version') or '')[:12]
    return [v for v in alla if v == nu12] if blind else alla


_BILDSHA = {}


def bild_sha(dash, rel):
    """sha256 för en bild under underlag/ (ögonblicksbilden ägaren ser och godkänner), cachad på väg, ändringstid och
    storlek; None när filen saknas."""
    if not rel:
        return None
    p = dash.ROOT / str(rel)
    try:
        st = os.stat(p)
    except OSError:
        return None
    nyckel = (str(p), st.st_mtime_ns, st.st_size)
    if nyckel not in _BILDSHA:
        if len(_BILDSHA) > 2000:
            _BILDSHA.clear()
        _BILDSHA[nyckel] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return _BILDSHA[nyckel]


def _uppdragspost(st):
    """Det senaste uppdraget på kandidaten, som arbetsytan visar det: typen, versionen före, före/efter-bedömningens
    utfall med avsändare och fortsättningen (förs vidare, kräver fortsatt lösning, återställd eller oklart)."""
    f = st.get('forfining') if isinstance(st.get('forfining'), dict) else {}
    if not f.get('typ'):
        return None
    fe = f.get('fore_efter') if isinstance(f.get('fore_efter'), dict) else {}
    return {'typ': f.get('typ'), 'namn': (f.get('uppdrag') or {}).get('namn'), 'fran': str(f.get('fran') or '')[:12], 'klar': f.get('klar'),
            'utfall': fe.get('utfall'), 'skal': fe.get('skal'), 'avsandare': fe.get('avsandare'), 'sett': fe.get('sett'),
            'fortsattning': (f.get('fortsattning') or {}).get('beslut'), 'omfattning_brister': f.get('omfattning_brister') or []}


def kandidatlista(dash, slug, blind):
    """Kandidaterna med neutrala etiketter (kandidater.sammanstall, som Förslagen), version, förhandsvisning och den
    bevarade ögonblicksbilden. Före ägarens första val utan skapare- och granskningstext."""
    _kontroller()
    import forhandsvisa
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
        versioner = synliga_versioner(slug, kid, st, blind)
        b = k.get('bilder') or {}
        # är ögonblicksbilden kandidatens sida? fotograferingens inspektion bredvid bilden (forhandsvisa.ogiltig_sida;
        # None när inspektionen saknas och det inte går att säga)
        ins = dash.las_json(dash.ROOT / Path(str(b.get('390-forsta'))).parent / 'INSPEKTION.json') if b.get('390-forsta') else None
        ogiltig = forhandsvisa.ogiltig_sida(ins) if ins else []
        ut.append({'id': kid, 'etikett': k.get('etikett') or kid, 'status': k.get('status'), 'statustext': k.get('statustext') or k.get('status'),
                   'version': str(st.get('version') or '')[:12] or None, 'version_hel': st.get('version'), 'fotograferad': st.get('fotograferad'),
                   'preview': {'url': '/visa/%s/%s' % (slug, kid), 'finns': dist.is_file(),
                               'byggd': _iso(_mtid(dist)) if dist.is_file() else None},
                   'snapshot': {'390': b.get('390-forsta'), '1440': b.get('1440-forsta') or b.get('1280-forsta'), 'version': str(st.get('version') or '')[:12] or None,
                                'tid': st.get('fotograferad'),
                                'sha': {'390': bild_sha(dash, b.get('390-forsta')), '1440': bild_sha(dash, b.get('1440-forsta') or b.get('1280-forsta'))},
                                'giltig': None if ins is None else not ogiltig, 'ogiltig': ogiltig},
                   'versioner': versioner, 'referens': _referens(k.get('referensjamforelse')),
                   # versionerna som kan väljas (före och efter varje uppdrag), med hela versionen; ägarens uppdrag 2026-10-09, punkt 10
                   'valbara': [] if blind else [v for v in kandidater.valbara_versioner(st) if kandidater.bevarad(slug, kid, v)],
                   'uppdrag': None if blind else _uppdragspost(st)})
    return ut, None


def _referens(rj):
    """Huvudreferensens fångade startsida bredvid kandidaten (kandidater.referensjamforelse, som Förslagen visar också
    före ditt första val), eller skälet att den saknas."""
    if not isinstance(rj, dict):
        return None
    r = rj.get('referens') or {}
    return {'namn': r.get('namn'), '390': r.get('390-forsta'), '1440': r.get('1440-forsta'), 'saknas': rj.get('saknas'), 'egen': rj.get('egen')}


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
        ab = bool(dash.ab_oavgjord(slug))
    except Exception as e:  # noqa: BLE001 — stängt vid fel: en jämförelse som inte går att pröva behandlas som oavgjord
        ab = True
        ut['ofullstandig'].append('jämförelsen: %s: %s' % (type(e).__name__, str(e)[:160]))
    if ab:  # en arm i en blind jämförelse: inget om körningen, sessionerna, koden eller loggarna före ditt val (som flode och bygge)
        ut.update({'blind': True, 'ab_dold': True, 'steg': [], 'besked': None, 'handlingar': [], 'startmiljo': None, 'moment': None,
                   'korning': {}, 'kandidater': [], 'sessioner': [], 'helbygge': [], 'startjournal': [], 'overlamningar': [], 'roller': {},
                   'preview': [], 'partner': None,
                   'dold': 'Kunden är en arm i en blind jämförelse som du inte har valt i än. Arbetsytan visar den efter ditt val i Jämförelser.'})
        return ut
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
    if f.get('ab_dold'):  # flödet säger armen dold fast jämförelsen ovan inte gjorde det: dölj ändå
        ut.update({'korning': {}, 'kandidater': [], 'sessioner': [], 'helbygge': [], 'startjournal': [], 'overlamningar': [], 'roller': {},
                   'preview': [], 'partner': None, 'dold': 'Kunden är en arm i en blind jämförelse.'})
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
        ut['samverkan'] = samverkan_kort(dash, slug, ut.get('blind'))
    except Exception as e:  # noqa: BLE001
        ut['samverkan'] = None
        ut['ofullstandig'].append('meddelandena: %s: %s' % (type(e).__name__, str(e)[:160]))
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
            osaker = k.get('status') in ('fel', 'under_arbete', 'ofullstandig')
            ut.append({'typ': 'arbetsversion', 'kalla': 'kandidat', 'kandidat': k['id'], 'url': k['preview']['url'], 'byggd': k['preview']['byggd'],
                       'osaker': osaker, 'etikett': '%s, arbetsversion byggd %s%s' % (
                           k['etikett'], k['preview']['byggd'], '; kandidaten byggs om eller senaste bygget föll, så den kan vara äldre' if osaker else '')})
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
    try:
        delar.append('ab:%s' % bool(dash.ab_oavgjord(slug)))
    except Exception:  # noqa: BLE001
        delar.append('ab:fel')
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
    a = u / 'arbetsyta'  # meddelandebussen, löparnas lägen, pauserna och mandaten (kontroller/meddelanden.py)
    lagg(a / 'STYRNING.json')
    for under in ('meddelanden', 'styrning', 'mandat'):
        for p in sorted((a / under).glob('*.json')) if (a / under).is_dir() else []:
            lagg(p)
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
                if _inom(kandidater.atelje.KUNDER / slug, p):
                    ut['%s/%s' % (namn, r.as_posix())] = p
    return ut


def _inom(bas, p):
    """Ligger p under bas utan någon länk på vägen och inom bas verkliga väg (_saker_fil)? Prövas när filen listas och
    igen när den läses, så att en länk som byts in däremellan inte följs."""
    try:
        return _saker_fil(bas, Path(p).relative_to(bas).as_posix()) is not None
    except ValueError:
        return False


def _versionsfiler(slug, kid, v12, blind):
    _kontroller()
    import kandidater
    if not V12.fullmatch(str(v12 or '')) or not kandidater.bevarad(slug, kid, v12):
        return None
    d = kandidater.kdir(slug, kid) / 'versioner' / v12
    return {r: p for r, p in kandidater.version_filer(d) if not r.startswith(kandidater.MATERIAL + '/')
            and (r != 'DESIGN.md' or not blind) and Path(r).suffix.lower() in TEXTFILER and _inom(kandidater.atelje.UNDERLAG / slug, p)}


def kod(dash, slug, kid, rel=None, mot=None):
    """Kandidatens filer (arbetsversionen) och, för en fil, dess text och en diff mot den namngivna bevarade versionen mot
    (versioner/<v12>/). Bara textfiler under projektets egna kataloger; ingenting skrivs."""
    _kontroller()
    import kandidater
    blind, ab = dold(dash, slug)
    if ab:
        raise ValueError('kunden är en arm i en blind jämförelse som du inte har valt i än')
    if not KID.fullmatch(str(kid or '')) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    sajt = kandidater.ksajt(slug, kid)
    if any(x.is_symlink() for x in (sajt, sajt.parent, sajt.parent.parent)):
        raise ValueError('kandidatens projekt är en länk; det visas inte')
    arbete = _arbetsfiler(slug, kid, blind)
    st = kandidater.las_status(slug, kid)
    versioner = synliga_versioner(slug, kid, st, blind)
    if mot and mot not in versioner:
        raise ValueError('versionen finns inte bland de bevarade versionerna du kan se')
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
        a = _text(arbete.get(rel)) if rel in arbete and _inom(kandidater.atelje.KUNDER / slug, arbete[rel]) else None
        b = _text(jamf[rel]) if jamf and rel in jamf and _inom(kandidater.atelje.UNDERLAG / slug, jamf[rel]) else None
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

HEMLIGT = (  # (mönster, ersättning): värdet ersätts, det som visar vad det var står kvar
    (re.compile(r'(?i)(authorization["\']?\s*[:=]\s*["\']?(?:bearer|basic|token)?\s*)([^\s"\',]{6,})'), r'\1•••'),
    (re.compile(r'(?i)\b(bearer\s+)([A-Za-z0-9._~+/=-]{8,})'), r'\1•••'),
    (re.compile(r'\b(sk-(?:ant-)?[a-z0-9]{0,6}-?)[A-Za-z0-9_-]{8,}'), r'\1•••'),
    (re.compile(r'\b(re_)(?=[A-Za-z0-9_]*[0-9])(?=[A-Za-z0-9_]*[A-Z])[A-Za-z0-9_]{16,}'), r'\1•••'),  # Resends nycklar, inte re_render_x
    (re.compile(r'(?i)([?&](?:key|api_key|apikey|token|access_token|nyckel|secret)=)[^&\s"\']+'), r'\1•••'),
    (re.compile(r'(?i)(api[_-]?key|token|secret|nyckel|password|passwd|lösenord)(["\']?\s*[=:]\s*["\']?|\s+)([^\s"\'&,]{6,})'), r'\1\2•••'),
)


def maskera(rad):
    for m, ers_ in HEMLIGT:
        rad = m.sub(ers_, rad)
    return rad


def korningslogg(dash, slug, rader=200):
    """Körningens loggar som text: arbetarens logg i startjournalen och ateljéns arbetare.log, helbyggets vakt- och
    webbtjänstloggar. Före ägarens första val visas bara journalens rader (loggarna kan bära bedömningar). Värden efter
    ord som nyckel, token och lösenord maskeras; texten visas som text, aldrig som HTML."""
    blind, ab = dold(dash, slug)
    if ab:
        return {'tid': _nu(), 'blind': True, 'loggar': [], 'dold': 'kunden är en arm i en blind jämförelse som du inte har valt i än'}
    u, k = dash.UNDERLAG / slug, dash.KUNDER / slug
    kallor = []
    st = dash.las_json(u / 'atelje' / 'STATUS.json') or {}
    if re.fullmatch(r'[A-Za-z0-9_-]{8,80}', str(st.get('start_id') or '')):
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
        r = [maskera(x) for x in text.splitlines()[-rader:]]
        ut.append({'fil': _relativ(dash, p), 'rader': r, 'andrad': _iso(_mtid(p))})
    return {'tid': _nu(), 'blind': blind, 'loggar': ut}


# --- ägarens ändring ---

ANDRING_ID = re.compile(r'^[A-Za-z0-9_-]{8,80}$')
ANDRINGSBESLUT = ('uppdrag',)  # en ändring är ett uppdrag: rätta, omarbeta designen eller bygg ut (ägarens uppdrag 2026-10-09, punkt 8)


def skicka_andring(dash, slug, data):
    """Ägarens ändring från arbetsytan: ett beslut i domloggen genom samma väg som Förslagen (server.spara_prototyp,
    atelje.doma), bundet till körningen, kandidaten och versionen ägaren såg, med arbetsytans markering (vy, sida, del)
    och ändringens id på raden. Samma id ger samma rad (dubbelklick, två flikar, tappat svar). En annan körning, en
    inaktuell version eller en körning som inte väntar på ditt beslut nekas med skälet (Inaktuell, HTTP 409); inget
    vidarebefordras blint, och inget arbete startar här: nästa handling (Starta uppdraget) startas uttryckligen. Ändringen är
    ett uppdrag med typen (rätta, omarbeta designen eller bygg ut), det önskade resultatet, omfattningen och det som ska
    bevaras; avsändaren är ägaren, eller kunden med ett belägg."""
    _kontroller()
    import kandidater
    import skapande
    if not isinstance(data, dict):
        raise ValueError('ändringen ska vara ett objekt')
    aid, text, beslut = str(data.get('andring_id') or ''), str(data.get('text') or '').strip(), data.get('beslut') or 'uppdrag'
    kid, version, korning = str(data.get('kandidat') or ''), str(data.get('version') or ''), str(data.get('korning') or '')
    if dold(dash, slug)[1]:  # stängt vid fel: en jämförelse som inte går att pröva räknas som oavgjord
        raise ValueError('kunden är en arm i en blind jämförelse, eller jämförelsen kunde inte prövas; välj i Jämförelser först')
    if not re.fullmatch(r'[0-9a-f]{64}', version) or not korning:
        raise ValueError('ändringen ska bära körningen och kandidatens hela version, som du såg dem')
    if not ANDRING_ID.fullmatch(aid):
        raise ValueError('ett ändrings-id behövs')
    if beslut not in ANDRINGSBESLUT:
        raise ValueError('en ändring är ett uppdrag: rätta, omarbeta designen eller bygg ut (valj startar inget arbete)')
    uppdrag = skapande.uppdrag_giltigt(data.get('uppdrag'))  # ValueError med skälet när typ, resultat, omfattning eller bevara saknas
    if not text or len(text) > 8000:
        raise ValueError('skriv vad som ska ändras (högst 8000 tecken)')
    if not KID.fullmatch(kid) or kid not in kandidater.lista(slug):
        raise ValueError('välj kandidaten ändringen gäller')
    markering = {k: str(data.get(k))[:200] for k in ('vy', 'sida', 'del', 'fil') if data.get(k)}
    with _ANDRING_LAS:
        for d in skapande.domar(slug, dash.UNDERLAG):
            a = d.get('arbetsyta') if isinstance(d.get('arbetsyta'), dict) else {}
            karna = lambda x: {k: (x or {}).get(k) for k in ('typ', 'resultat', 'omfattning', 'bevara')}  # noqa: E731 — uppdragets innehåll
            if a.get('andring_id') == aid or (a.get('andring_id') and str(d.get('text') or '').strip() == text and a.get('kandidat') == kid
                                              and a.get('version') == version[:12] and a.get('korning') == korning
                                              and karna(d.get('uppdrag')) == karna(uppdrag)
                                              and all(a.get(k) == markering.get(k) for k in ('vy', 'sida', 'del', 'fil'))):
                return {'ok': True, 'upprepat': True, 'dom': d}
        st = dash.las_json(dash.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
        if korning != str(st.get('startad') or ''):
            raise Inaktuell('körningen har bytts sedan du skrev ändringen (din %s, nu %s); läs läget och skriv om den mot den aktuella' % (korning, st.get('startad')))
        nu_v = str(kandidater.las_status(slug, kid).get('version') or '')
        if version != nu_v:
            raise Inaktuell('kandidaten har en ny version sedan du skrev ändringen (din %s, nu %s); stäm av mot den aktuella' % (version[:12], nu_v[:12]))
        if st.get('steg') not in ('klar_for_bedomning', 'fel'):
            raise Inaktuell('körningen väntar inte på ditt beslut (steg %s); ändringen skickas inte' % st.get('steg'))
        # din text är domens text, ordagrant; markeringen står för sig (skapande.kritikrader visar den som markerad i
        # arbetsytan), aldrig i delar, som skaparen läser som det du gillade
        res = dash.spara_kandidatbeslut(slug, st, {'beslut': beslut, 'kandidater': [{'id': kid, 'version': version}], 'text': text,
                                                   'uppdrag': dict(uppdrag, omrade=markering) if markering else uppdrag,
                                                   **({'avsandare': 'kunden', 'belagg': data.get('belagg')} if data.get('avsandare') == 'kunden' else {})},
                                        arbetsyta=dict(markering, andring_id=aid, kandidat=kid, version=version[:12], korning=korning))
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
    blind, ab = dold(dash, slug)
    if ab:
        raise ValueError('kunden är en arm i en blind jämförelse som du inte har valt i än')
    p = _arbetsfiler(slug, kid, blind).get(rel)
    if not p or p.is_symlink() or not p.is_file() or not _inom(kandidater.atelje.KUNDER / slug, p):
        raise ValueError('filen hör inte till kandidatens arbetsversion')
    argv = ['open', '-a', str(EDITOR), str(p)] if EDITOR.is_dir() else ['open', '-t', str(p)]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    if r.returncode:
        raise ValueError('editorn kunde inte öppnas: %s' % (r.stderr.strip()[:200] or r.returncode))
    return {'ok': True, 'fil': rel, 'program': 'Visual Studio Code' if EDITOR.is_dir() else 'textredigeraren'}


_DELAT = {}
_DELAT_LAS = threading.Lock()


def lage_delat(dash, slug, sig, max_alder=30):
    """Läget för strömmarna: räknas om när signaturen ändrats eller läget är äldre än max_alder sekunder, annars samma
    läge till varje ström (en ström per flik ska inte räkna fram läget varje sekund var för sig)."""
    with _DELAT_LAS:
        x = _DELAT.get(slug)
        if x and x[0] == sig and time.time() - x[1] < max_alder:
            return x[2]
    nytt = lage(dash, slug)
    with _DELAT_LAS:
        _DELAT[slug] = (sig, time.time(), nytt)
    return nytt
