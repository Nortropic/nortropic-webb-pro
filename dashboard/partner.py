"""partner.py — Nortropic-partnerns samtal i arbetsytan (ägarens uppdrag 2026-10-09, etapp 4; kunskap/arbetsyta.md).

Partnern är en riktig Claude Code-session per kund: första meddelandet startar `claude -p --session-id <id>`, varje
senare `claude -p --resume <id>`, så samtalet fortsätter i samma session och ingen ny konversation startas per meddelande
eller omladdning. Ett meddelande i taget: en tur som pågår, eller en interaktiv `claude --resume <id>` i en terminal,
gör att nästa meddelande nekas (två skrivande processer får aldrig ha samma sessionsidentitet).

Partnern är arbetsledning, inte utförare: den har bara Read, i en egen tom arbetskatalog, och får läsa repots publika
kunskap och kundens underlag i en tillåtelselista (dontAsk nekar allt annat utanför arbetskatalogen; prövat 2026-10-09).
Den skriver inga filer, startar inget arbete och fattar inga beslut. Varje meddelande bär arbetsytans läge ur samma
läsväg som vyn (arbetsyta.lage, blindat på servervägen) och ägarens markering: kund, körning, kandidat och version,
vy, sida och del. Ändringar går ägarens väg: knappen Skicka ändring (arbetsyta.skicka_andring), aldrig partnerns svar.

Lagring (privat): underlag/<slug>/arbetsyta/PARTNER.json bär kopplingen (sessions-id, modell) och meddelandenas id,
avsikt, markering, ägarens text och processens identitet; turen strömmas som Claude Codes egna händelser
(`--output-format stream-json --include-partial-messages`) till underlag/<slug>/arbetsyta/partner/strom-<id>.jsonl, och
dess slutpost står som svarsfil i svar-<id>.json (samma fält som `--output-format json`). Delhändelserna (textdeltan,
verktygsanrop) visas i vyn medan turen pågår, åtskilda från svaret; svaret är bara slutposten. Ingen annan status.
"""
import calendar
import fcntl
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

ID = re.compile(r'^[A-Za-z0-9_-]{8,80}$')
SESSION = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
AVSIKTER = {'fraga': 'Fråga', 'plan': 'Planförslag', 'andring': 'Ändring (mandat)'}
KONTEXTFALT = ('vy', 'kandidat', 'version', 'sida', 'del', 'korning')
MAX_TEXT = 8000
LAS = threading.Lock()
KUNDFILER = ('VERKSAMHET.json', 'UPPDRAG.md', 'BRIEF.md', 'RESEARCH.md', 'TEXTUNDERLAG.md', 'INNEHALL.md', 'BESTALLNING.md')

SYSTEM = """Du är Nortropic-partnern i ägarens arbetsyta: arbetsledare för ett kunduppdrag i Nortropics webbmotor.
Ägaren skriver till dig i arbetsytan bredvid kundens förhandsvisning och de sessioner som arbetar.

Ditt ansvar: förstå läget, svara på frågor, föreslå planer och formulera tydliga överlämningar (mål, avgränsning,
förväntat resultat). Du ändrar inga filer och startar inget arbete; du har bara Read. Ägaren skickar ändringar själv med
knappen Skicka ändring, och motorn genomför dem i sina egna sessioner. Säg aldrig att något pågår, är klart eller godkänt
om inte arbetsytans läge i meddelandet visar det. Hitta inte på procent, tid kvar, poäng eller användningssiffror; ett
värde som saknas är okänt.

Skilj ägarens avsikt: en fråga besvaras utan ändring; ett planförslag beskriver steg utan att något startas; en ändring
med mandat formuleras som en överlämning. När ägaren ber om en ändring, avsluta svaret med ett block exakt så här:
```overlamning
{"kandidat": "<id eller null>", "version": "<version eller null>", "sida": "<sida eller null>", "del": "<del eller null>",
 "mal": "<vad som ska bli annorlunda>", "avgransning": "<vad som inte ska röras>", "forvantat": "<hur resultatet känns igen>"}
```
Ägaren läser blocket, kan ändra det och skickar det själv.

Är läget blindat ("blind: ja") har ägaren inte fattat sitt första beslut i körningen: bedömningar, skäl och granskning är
dolda för ägaren. Försök inte ta reda på dem och spekulera inte om vilken kandidat som är bäst.

Du får läsa: repots README.md, CLAUDE.md, BESLUT.md, kunskap/, kritik/ och backlog/ och kundens underlag i listan
nedan. Allt annat nekas. Svara på svenska, kort och konkret."""


def profil():
    """Arbetsledningens modellprofil (ägarens uppdrag: Fable 5.1 som kandidat; en hypotes, ingen kvalitetssanning)."""
    return {'modell': os.environ.get('NWP_PARTNER_MODELL') or 'claude-fable-5-1',
            'effort': os.environ.get('NWP_PARTNER_EFFORT') or 'medium',
            'frist': int(os.environ.get('NWP_PARTNER_FRIST') or 600), 'max_turer': int(os.environ.get('NWP_PARTNER_TURER') or 12)}


class Upptagen(ValueError):
    """Ett meddelande som inte kan tas emot nu (en tur pågår, sessionen är öppen i en terminal): HTTP 409."""


class Dold(ValueError):
    """Kunden är en arm i en blind jämförelse som ägaren inte valt i än: varken samtalet eller en ny tur (HTTP 409)."""


def bindning(dash, slug):
    """Vad partnersessionen är bunden till nu, ur samma källor som arbetsytans läsväg: körningen (STATUS.json:s startad)
    och blindläget (arbetsyta.dold, stängt vid fel). En sparad session återupptas bara i samma körning, och i ett blint
    läge bara om den startades blind: en ny blind körning ärver aldrig ett samtal där tidigare bedömningar eller
    försöksarmar kan stå (att dölja det senaste meddelandet rensar inte sessionens minne)."""
    import arbetsyta
    blind, ab = arbetsyta.dold(dash, slug)
    try:
        korning = (dash.las_json(dash.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}).get('startad')
    except Exception:  # noqa: BLE001 — okänd körning: ingen sparad session passar, och nästa meddelande får en ny
        korning = '?'
    return {'korning': korning, 'blind': bool(blind), 'ab_dold': bool(ab)}


def _galler(d, b):
    """Den sparade sessionen i d får återupptas under bindningen b."""
    return bool(d.get('session_id')) and d.get('korning') == b['korning'] and (not b['blind'] or d.get('blind_vid_start') is True)


def _arkivera(d):
    """Den gällande sessionen flyttas oförändrad till tidigare; nästa meddelande startar en ny session."""
    if not d.get('session_id'):
        return d
    gammal = {k: d.get(k) for k in ('session_id', 'skapad', 'modell', 'effort', 'korning', 'blind_vid_start', 'meddelanden')}
    return {'schema': 'partner/1', 'slug': d.get('slug'), 'tidigare': list(d.get('tidigare') or []) + [gammal], 'meddelanden': []}


def _katalog(dash, slug):
    return dash.UNDERLAG / slug / 'arbetsyta'


def _fil(dash, slug):
    return _katalog(dash, slug) / 'PARTNER.json'


def _las(dash, slug):
    try:
        d = json.loads(_fil(dash, slug).read_text(encoding='utf-8'))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _skriv(dash, slug, d):
    f = _fil(dash, slug)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name('.PARTNER.json.%d.tmp' % os.getpid())
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, f)


@contextmanager
def _lasat(dash, slug):
    k = _katalog(dash, slug)
    k.mkdir(parents=True, exist_ok=True)
    with LAS:
        fd = os.open(str(k / '.partner.lock'), os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)


def _lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (OSError, TypeError, ValueError):
        return False


def _ps():
    try:
        return subprocess.run(['ps', '-A', '-o', 'pid=,command='], capture_output=True, text=True, timeout=10,
                              env=dict(os.environ, LC_ALL='C')).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def andra_processer(sid, utom=()):
    """Levande processer vars argument nämner sessionens id (en interaktiv claude --resume i en terminal, eller en tur
    som en tidigare dashboard startade), utom de egna."""
    if not SESSION.match(str(sid or '')):
        return []
    ut = []
    for rad in _ps().splitlines():
        d = rad.strip().split(None, 1)
        # bara ett claude-program (som städningens ar_claude), inte ett skal eller en sökning som råkar nämna id:t
        forsta = d[1].split()[0] if len(d) == 2 and d[1].split() else ''
        ar_claude = os.path.basename(forsta) == 'claude' or '/@anthropic-ai/claude-code/' in (d[1] if len(d) == 2 else '')
        if len(d) == 2 and d[0].isdigit() and int(d[0]) not in utom and sid in d[1] and ar_claude:
            ut.append({'pid': int(d[0]), 'kommando': 'claude %s' % ('-p (partnerns tur)' if ' -p ' in d[1] + ' ' else '(interaktiv)')})
    return ut


def _resultat(f):
    """Slutposten (type result) ur en strömfil, eller None. Den står sist; en tur som avbröts har ingen."""
    try:
        with open(f, 'rb') as fh:
            fh.seek(0, os.SEEK_END)
            storlek = fh.tell()
            fh.seek(max(0, storlek - (1 << 20)))
            rader = fh.read().split(b'\n')
    except OSError:
        return None
    for rad in reversed(rader):
        if b'"result"' not in rad:
            continue
        try:
            d = json.loads(rad)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get('type') == 'result':
            return d
    return None


def _svar(dash, slug, m):
    """Svaret ur Claude Codes svarsfil (eller strömmens slutpost, om dashboarden startades om innan svarsfilen skrevs):
    text, fel, användning och modell; None innan turen har en slutpost."""
    katalog = _katalog(dash, slug) / 'partner'
    f = katalog / Path(str(m.get('svarsfil') or 'saknas')).name
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        d = _resultat(katalog / Path(str(m['stromfil'])).name) if m.get('stromfil') else None
    if not isinstance(d, dict):
        return None
    u = d.get('usage') if isinstance(d.get('usage'), dict) else {}
    return {'text': str(d.get('result') or ''), 'fel': bool(d.get('is_error')), 'subtyp': d.get('subtype'), 'session_id': d.get('session_id'),
            'turer': d.get('num_turns'), 'ms': d.get('duration_ms'),
            'anvandning': {'in': u.get('input_tokens'), 'ut': u.get('output_tokens'), 'cache_las': u.get('cache_read_input_tokens'),
                           'cache_skriv': u.get('cache_creation_input_tokens'), 'listpris_usd': d.get('total_cost_usd'),
                           'modeller': sorted((d.get('modelUsage') or {}).keys()) if isinstance(d.get('modelUsage'), dict) else []},
            'nekade': [str((x.get('tool_input') or {}).get('file_path') or x.get('tool_name'))[:200] for x in d.get('permission_denials') or [] if isinstance(x, dict)]}


OVERLAMNING = re.compile(r'```overlamning\s*\n(.*?)\n```', re.S)


def _meddelandelage(dash, slug, m, sid=None):
    """Ett meddelandes läge ur processen och svarsfilen, prövat nu: skickat (journalfört, ingen process än), arbetar
    (processen lever), svarat, fel eller avbrutet (processen lever inte och inget svar finns)."""
    s = _svar(dash, slug, m)
    if m.get('vantande'):
        lage = 'vantande'
    elif s:
        lage = 'fel' if s['fel'] else 'svarat'
    elif m.get('pid') and _lever(m['pid']) and (not sid or sid in _kommando(m['pid'])) \
            and time.time() - _epok(m.get('tid')) <= profil()['frist'] + 60:
        lage = 'arbetar'
    elif m.get('pid'):
        lage = 'avbrutet'
    else:
        lage = 'fel' if m.get('fel') else 'skickat'
    forslag = None
    if s and s['text']:
        x = OVERLAMNING.search(s['text'])
        if x:
            try:
                forslag = json.loads(x.group(1))
                forslag = {k: forslag.get(k) for k in ('kandidat', 'version', 'sida', 'del', 'mal', 'avgransning', 'forvantat')} if isinstance(forslag, dict) else None
            except ValueError:
                forslag = {'oläsligt': True}
    return {'id': m.get('id'), 'tid': m.get('tid'), 'avsikt': m.get('avsikt'), 'kontext': m.get('kontext'), 'text': m.get('text'),
            'lage': lage, 'svar': s, 'fel': m.get('fel'), 'overlamning': forslag, 'slut': m.get('slut')}


def lage(dash, slug, samtal=False):
    """Partnerns läge för arbetsytan: sessionen (som en rad bland rollsessionerna), meddelandenas läge och, med samtal,
    hela samtalet. Läsningen ändrar ingenting."""
    p = profil()
    b = bindning(dash, slug)
    if b['ab_dold']:
        return {'session_id': None, 'lage': 'dold', 'dold': True, 'profil': p, 'meddelanden': [] if samtal else None, 'antal': 0,
                'lage_text': 'kunden är en arm i en blind jämförelse: partnersamtalet visas och tar emot meddelanden efter ditt val',
                'tidigare': None, 'session': None}
    d = _las(dash, slug)
    if d.get('session_id') and not _galler(d, b):
        d = _arkivera(d)  # bara i läsningen; filen ändras först när nästa meddelande skickas
    tidigare = [t for t in d.get('tidigare') or [] if isinstance(t, dict)]
    hist = {'tidigare': len(tidigare)}
    if samtal and not b['blind']:
        hist['tidigare_samtal'] = [{'session_id': t.get('session_id'), 'korning': t.get('korning'), 'skapad': t.get('skapad'),
                                    'meddelanden': [_meddelandelage(dash, slug, m) for m in t.get('meddelanden') or [] if isinstance(m, dict)]}
                                   for t in tidigare]
    if not d.get('session_id'):
        return dict({'session_id': None, 'lage': 'vantar', 'profil': p, 'meddelanden': [] if samtal else None, 'antal': 0, 'session': None,
                     'lage_text': 'inget meddelande i den här körningen än' if hist['tidigare'] else 'inget meddelande än',
                     'bindning': {'korning': b['korning'], 'blind': b['blind']}}, **hist)
    med = [_meddelandelage(dash, slug, m, d.get('session_id')) for m in d.get('meddelanden') or [] if isinstance(m, dict)]
    vantande = next((m['id'] for m in med if m['lage'] == 'vantande'), None)
    senaste = next((m for m in reversed(med) if m['lage'] != 'vantande'), None)
    egna = {m.get('pid') for m in d.get('meddelanden') or [] if isinstance(m, dict) and m.get('pid')}
    andra = andra_processer(d['session_id'], utom=egna)
    sl = ('aktiv' if senaste and senaste['lage'] == 'arbetar' else 'startar' if senaste and senaste['lage'] == 'skickat'
          else 'aktiv' if andra else 'avslutad' if senaste and senaste['lage'] == 'svarat' else 'avbruten' if senaste and senaste['lage'] in ('fel', 'avbrutet')
          else 'vantar')
    text = {'aktiv': 'partnern svarar' if not andra else 'sessionen är öppen i en annan process (%s)' % andra[0]['kommando'],
            'startar': 'meddelandet är journalfört; processen har inte startat', 'avslutad': 'partnern har svarat; nästa tur startar när du skriver',
            'avbruten': 'senaste turen gav inget svar', 'vantar': 'inget meddelande än'}[sl]
    akt = None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kontroller'))
        import bildkedja
        import observation
        tr = bildkedja.transkript(d['session_id'])
        if tr:
            akt, _ = observation.aktivitet(tr, slug, n=20)
    except Exception:  # noqa: BLE001 — aktiviteten är en extra; läget gäller utan den
        akt = None
    modeller = sorted({x for m in med if m['svar'] for x in m['svar']['anvandning']['modeller']})
    session = {'session_id': d['session_id'], 'roll': 'partner', 'ansvar': 'arbetsledning', 'kandidat': None, 'korning': None,
               'start': d.get('skapad'), 'slut': (senaste or {}).get('slut'), 'pid': (d.get('meddelanden') or [{}])[-1].get('pid') if d.get('meddelanden') else None,
               'lage': sl, 'lage_text': text, 'foralder': {'typ': 'dashboarden (en process per tur, samma sessions-id)', 'pid': None, 'start_id': None},
               'modell_konfigurerad': d.get('modell'), 'modell_observerad': ', '.join(modeller) or None, 'aktivitet': akt,
               'senaste_handelse': (akt or {}).get('senaste_handelse'), 'kalla': 'partnersamtalet'}
    ut = {'session_id': d['session_id'], 'skapad': d.get('skapad'), 'modell': d.get('modell'), 'effort': d.get('effort'), 'profil': p,
          'lage': sl, 'lage_text': text, 'session': session, 'antal': len(med), 'senaste': {k: (senaste or {}).get(k) for k in ('id', 'lage', 'tid')},
          'vantande': vantande,
          'andra_processer': andra, 'terminal': 'claude --resume %s' % d['session_id'],
          'arbetskatalog': str(_rum(dash, slug)), 'bindning': {'korning': d.get('korning'), 'blind_vid_start': d.get('blind_vid_start')}}
    ut.update(hist)
    if samtal:
        ut['meddelanden'] = med
    return ut


def _rum(dash, slug):
    """Partnerns egen tomma arbetskatalog: allt utanför den kräver en regel i tillåtelselistan."""
    return _katalog(dash, slug) / 'partner' / 'rum'


def tillatet(dash, slug):
    root = str(Path(dash.ROOT).resolve()).strip('/')
    regler = ['Read(//%s/%s)' % (root, x) for x in ('README.md', 'CLAUDE.md', 'BESLUT.md', 'kunskap/**', 'kritik/**', 'backlog/**')]
    regler += ['Read(//%s/underlag/%s/%s)' % (root, slug, f) for f in KUNDFILER]
    return regler


def kontexttext(dash, slug, markering):
    """Arbetsytans läge som text till partnern, ur samma läsväg som vyn (arbetsyta.lage, blindat)."""
    import arbetsyta
    l = arbetsyta.lage(dash, slug)
    k = l.get('korning') or {}
    rader = ['[Arbetsytans läge, läst %s ur samma läsväg som vyn]' % l.get('tid'),
             'Kund: %s (%s)%s' % (slug, (l.get('projekt') or {}).get('namn') or 'namn saknas', ' — TESTDATA, fiktiv verksamhet' if (l.get('projekt') or {}).get('testdata') else ''),
             'Blind: %s' % ('ja (ägarens första val i körningen är inte gjort)' if l.get('blind') else 'nej'),
             'Körning: %s' % ('startad %s, läge %s, steg %s, arbetaren %s%s' % (k.get('startad'), k.get('lage'), k.get('steg'), k.get('arbetaren'),
                                                                                 ', fel: ' + str(k.get('fel'))[:200] if k.get('fel') else '') if k else 'ingen'),
             'Moment: %s' % ('%s. %s (%s)' % (l['moment']['nr'], l['moment']['namn'], l['moment']['status']) if l.get('moment') else 'okänt')]
    for x in l.get('kandidater') or []:
        rader.append('Kandidat %s (%s): %s, version %s%s' % (x['etikett'], x['id'], x.get('statustext') or x.get('status'), x.get('version') or 'ingen',
                                                            ', förhandsvisning finns' if x['preview']['finns'] else ''))
    for s in l.get('sessioner') or []:
        if s.get('kalla') == 'partnersamtalet':
            continue
        rader.append('Session %s%s: %s (%s)' % (s.get('roll') or ({'granskning': 'granskning', 'utforande': 'utförande'}.get(s.get('ansvar'), '?') + ', roll dold före ägarens val'),
                                               ' ' + s['kandidat'] if s.get('kandidat') else '', arbetsyta.LAGEN.get(s.get('lage'), s.get('lage')), s.get('lage_text') or ''))
    for nyckel, r in (l.get('roller') or {}).items():
        rader.append('Ansvar %s: %s — %s' % (r['rubrik'], arbetsyta.LAGEN.get(r['lage'], r['lage']), r['lage_text']))
    rader.append('Nästa tillåtna handlingar: %s' % (', '.join(h['text'] for h in l.get('handlingar') or []) or 'inga'))
    if l.get('ofullstandig'):
        rader.append('Ofullständigt i läget: %s' % '; '.join(l['ofullstandig'])[:600])
    rader.append('Kundens underlag du får läsa: %s' % ', '.join('underlag/%s/%s' % (slug, f) for f in KUNDFILER if (dash.UNDERLAG / slug / f).is_file()))
    mk = {k: v for k, v in (markering or {}).items() if v}
    rader.append('Ägarens markering: %s' % (', '.join('%s %s' % (k, v) for k, v in mk.items()) or 'ingen'))
    return '\n'.join(rader), l


def _rensa_kontext(k):
    if not isinstance(k, dict):
        return {}
    return {f: str(k[f])[:200] for f in KONTEXTFALT if k.get(f) not in (None, '')}


def args(dash, slug, sid, ny, p):
    _kontroller_in()
    import atelje
    # stream-json med delmeddelanden: verkliga svarsdeltan medan turen pågår (Claude Code 2.1.290, prövat 2026-10-10)
    return [atelje.claude(), '-p', '--session-id' if ny else '--resume', sid, '--output-format', 'stream-json', '--verbose',
            '--include-partial-messages', '--model', p['modell'],
            '--effort', p['effort'], '--max-turns', str(p['max_turer']), '--permission-mode', 'dontAsk', '--setting-sources', 'project,local',
            '--strict-mcp-config', '--tools', 'Read', '--allowedTools', *tillatet(dash, slug), '--append-system-prompt', SYSTEM]


def _kontroller_in():
    rot = str(Path(__file__).resolve().parents[1] / 'kontroller')
    if rot not in sys.path:
        sys.path.insert(0, rot)


def skicka(dash, slug, data, starta=True):
    """Ett meddelande till partnern. Samma meddelande-id ger samma post (dubbelklick, två flikar, tappat svar); en tur som
    pågår eller en annan process med sessionens id ger Upptagen. Med vanta sparas meddelandet medan en tur pågår som en
    väntande instruktion (en åt gången, ingen ny process): den startar som nästa tur i samma session när turen är klar
    (starta_vantande), och går att ta bort innan dess. Ger meddelandets läge."""
    _kontroller_in()
    import nastlad
    if not isinstance(data, dict):
        raise ValueError('meddelandet ska vara ett objekt')
    mid, text, avsikt = str(data.get('meddelande_id') or ''), str(data.get('text') or '').strip(), data.get('avsikt') or 'fraga'
    if not ID.fullmatch(mid):
        raise ValueError('ett meddelande-id behövs')
    if not text or len(text) > MAX_TEXT:
        raise ValueError('skriv ett meddelande (högst %d tecken)' % MAX_TEXT)
    if avsikt not in AVSIKTER:
        raise ValueError('okänd avsikt')
    b = bindning(dash, slug)
    if b['ab_dold']:
        raise Dold('kunden är en arm i en blind jämförelse som du inte valt i än: partnern tar emot meddelanden efter ditt val')
    with _lasat(dash, slug):
        d = _las(dash, slug)
        if d.get('session_id') and not _galler(d, b):
            d = _arkivera(d)  # skrivs tillsammans med det nya meddelandet, efter arbetskatalogens prövning
        for m in d.get('meddelanden') or []:
            if isinstance(m, dict) and m.get('id') == mid:
                return dict(_meddelandelage(dash, slug, m), upprepat=True)
        for t in d.get('tidigare') or []:  # en flik från en tidigare session: ingen ny tur och inget av det gamla svaret
            for m in (t.get('meddelanden') or []) if isinstance(t, dict) else []:
                if isinstance(m, dict) and m.get('id') == mid:
                    return {'id': mid, 'tid': m.get('tid'), 'lage': 'tidigare', 'upprepat': True, 'svar': None, 'text': None,
                            'fel': 'meddelandet hör till en tidigare partnersession (en annan körning eller ett annat blindläge)'}
        if d.get('session_id'):
            for m in d.get('meddelanden') or []:  # en tur som överlevt sin frist (dashboarden startades om mitt i den) stoppas här
                if isinstance(m, dict) and m.get('pid') and not m.get('slut') and _lever(m['pid']) and not _svar(dash, slug, m) \
                        and time.time() - _epok(m.get('tid')) > profil()['frist'] + 60 and str(d['session_id']) in _kommando(m['pid']):
                    nastlad.doda_trad(m['pid'])
                    m.update(slut=_nu(), fel='fristen (%d s) tog slut medan dashboarden startades om; turen stoppades' % profil()['frist'])
                    _skriv(dash, slug, d)
            pagar = [m for m in d.get('meddelanden') or [] if isinstance(m, dict) and m.get('pid') and _lever(m['pid'])
                     and not _svar(dash, slug, m) and str(d['session_id']) in _kommando(m['pid'])]
            if any(isinstance(x, dict) and x.get('vantande') for x in d.get('meddelanden') or []):
                raise Upptagen('en väntande instruktion finns redan; ta bort den eller låt den starta först')
            if pagar and data.get('vanta'):
                m = {'id': mid, 'tid': _nu(), 'avsikt': avsikt, 'kontext': _rensa_kontext(data.get('kontext')), 'text': text[:MAX_TEXT],
                     'svarsfil': 'svar-%s.json' % mid, 'stromfil': 'strom-%s.jsonl' % mid, 'pid': None, 'modell': d.get('modell'), 'vantande': True}
                d['meddelanden'] = list(d.get('meddelanden') or []) + [m]
                _skriv(dash, slug, d)
                return _meddelandelage(dash, slug, m)
            if pagar:
                raise Upptagen('partnern svarar på ett tidigare meddelande; vänta på svaret eller spara meddelandet som väntande')
            andra = andra_processer(d['session_id'], utom={m.get('pid') for m in d.get('meddelanden') or [] if isinstance(m, dict)})
            if andra:
                raise Upptagen('sessionen är öppen i en annan process (%s, pid %d); avsluta den först' % (andra[0]['kommando'], andra[0]['pid']))
        rum = _rum(dash, slug)
        # prövas innan något skrivs i PARTNER.json och innan en katalog skapas: ingen länk på vägen, och inget i katalogen som
        # Claude Code läser in (projektets inställningar och CLAUDE.md skulle annars kunna vidga partnerns läsrätt)
        if any(x.is_symlink() for x in (rum, rum.parent, rum.parent.parent)):
            raise ValueError('partnerns arbetskatalog %s får inte vara en länk' % rum)
        rum.mkdir(parents=True, exist_ok=True)
        if rum.is_symlink() or any(x.name not in ('.DS_Store',) for x in rum.iterdir()):
            raise ValueError('partnerns arbetskatalog %s ska vara tom (en .claude/ eller CLAUDE.md där skulle läsas in); ta bort det som '
                             'ligger där' % rum)
        p = profil()
        ny = not d.get('session_id')
        if ny:
            d = {'schema': 'partner/1', 'slug': slug, 'session_id': str(uuid.uuid4()), 'skapad': _nu(), 'modell': p['modell'],
                 'effort': p['effort'], 'korning': b['korning'], 'blind_vid_start': b['blind'], 'meddelanden': [],
                 **({'tidigare': d['tidigare']} if d.get('tidigare') else {})}
        kontext = _rensa_kontext(data.get('kontext'))
        try:
            ktext, _lage = kontexttext(dash, slug, kontext)
        except Exception as e:  # noqa: BLE001 — utan läge vet partnern det, och säger det
            ktext = '[Arbetsytans läge kunde inte läsas: %s]' % type(e).__name__
        m = {'id': mid, 'tid': _nu(), 'avsikt': avsikt, 'kontext': kontext, 'text': text[:MAX_TEXT], 'svarsfil': 'svar-%s.json' % mid,
             'stromfil': 'strom-%s.jsonl' % mid, 'pid': None, 'modell': p['modell']}
        d['meddelanden'] = (d.get('meddelanden') or []) + [m]
        _skriv(dash, slug, d)
        if not starta:
            return _meddelandelage(dash, slug, m)
        tur = _starta_tur(dash, slug, d, m, ny, p, rum, ktext)
    if tur:
        threading.Thread(target=_vakta, args=(dash, slug, mid) + tur + (p['frist'],), daemon=True).start()
    return _meddelandelage(dash, slug, m)


def _starta_tur(dash, slug, d, m, ny, p, rum, ktext):
    """Turens process (under partnerns lås): prompten, strömfilen och claude med sessionens id. Ger (proc, prompt, fu, fe),
    eller None med felet i posten."""
    import nastlad
    prompt = '%s\n\nÄgarens avsikt: %s\n\n%s' % (ktext, AVSIKTER.get(m.get('avsikt'), 'Fråga'), m['text'])
    ut = _katalog(dash, slug) / 'partner'
    try:
        fu = open(ut / m['stromfil'], 'wb')
        fe = open(ut / ('svar-%s.err' % m['id']), 'wb')
        proc = subprocess.Popen(args(dash, slug, d['session_id'], ny, p), stdin=subprocess.PIPE, stdout=fu, stderr=fe,
                                cwd=str(rum), env=nastlad.miljo(), start_new_session=True)
    except OSError as e:
        m['fel'] = 'kunde inte starta claude: %s' % e
        _skriv(dash, slug, d)
        return None
    m['pid'] = proc.pid
    _skriv(dash, slug, d)
    return proc, prompt, fu, fe


def starta_vantande(dash, slug, mid=None):
    """Den väntande instruktionen startar som nästa tur i samma session när ingen tur pågår: efter turen (_vakta) eller
    med ägarens Skicka nu (till exempel efter en omstart av dashboarden). Markeringen är den som frystes när instruktionen
    sparades; arbetsytans läge läses nu. En session som bytts (ny körning, annat blindläge) startar den inte. Ger
    meddelandets läge, eller None utan väntande instruktion."""
    _kontroller_in()
    b = bindning(dash, slug)
    if b['ab_dold']:
        raise Dold('kunden är en arm i en blind jämförelse som du inte valt i än')
    with _lasat(dash, slug):
        d = _las(dash, slug)
        m = next((x for x in d.get('meddelanden') or [] if isinstance(x, dict) and x.get('vantande') and (mid is None or x.get('id') == mid)), None)
        if not m:
            return None
        if not _galler(d, b):
            m.update(vantande=False, fel='sessionen byttes (en ny körning eller ett annat blindläge) innan instruktionen startade; skriv den igen',
                     slut=_nu())
            _skriv(dash, slug, d)
            return _meddelandelage(dash, slug, m)
        pagar = [x for x in d.get('meddelanden') or [] if isinstance(x, dict) and x.get('pid') and _lever(x['pid'])
                 and not _svar(dash, slug, x) and str(d['session_id']) in _kommando(x['pid'])]
        if pagar:
            return _meddelandelage(dash, slug, m)
        andra = andra_processer(d['session_id'], utom={x.get('pid') for x in d.get('meddelanden') or [] if isinstance(x, dict)})
        if andra:
            raise Upptagen('sessionen är öppen i en annan process (%s, pid %d); avsluta den först' % (andra[0]['kommando'], andra[0]['pid']))
        try:
            ktext, _lage = kontexttext(dash, slug, m.get('kontext'))
        except Exception as e:  # noqa: BLE001
            ktext = '[Arbetsytans läge kunde inte läsas: %s]' % type(e).__name__
        p = profil()
        m.update(vantande=False, startad=_nu())
        tur = _starta_tur(dash, slug, d, m, False, p, _rum(dash, slug), ktext)
    if tur:
        threading.Thread(target=_vakta, args=(dash, slug, m['id']) + tur + (p['frist'],), daemon=True).start()
    return _meddelandelage(dash, slug, m)


def ta_bort_vantande(dash, slug, mid):
    """Ägaren tar bort sin väntande instruktion innan den startat; en som startat ger Upptagen."""
    if not ID.fullmatch(str(mid or '')):
        raise ValueError('ett meddelande-id behövs')
    with _lasat(dash, slug):
        d = _las(dash, slug)
        med = [x for x in d.get('meddelanden') or [] if isinstance(x, dict)]
        m = next((x for x in med if x.get('id') == mid), None)
        if not m:
            raise ValueError('ingen sådan instruktion i den gällande sessionen')
        if not m.get('vantande'):
            raise Upptagen('instruktionen har redan startat')
        d['meddelanden'] = [x for x in med if x.get('id') != mid]
        _skriv(dash, slug, d)
    return {'borttagen': mid}


def _vakta(dash, slug, mid, proc, prompt, fu, fe, frist):
    """Turen till slut: prompten på stdin, väntan med frist, hela processträdet stoppas vid fristen, sluttiden i posten."""
    _kontroller_in()
    import nastlad
    fel = None
    try:
        proc.communicate(input=prompt.encode(), timeout=frist)
    except subprocess.TimeoutExpired:
        fel = 'fristen (%d s) tog slut; turen stoppades' % frist
        nastlad.doda_trad(proc.pid)
        proc.communicate()
    except Exception as e:  # noqa: BLE001
        fel = '%s: %s' % (type(e).__name__, e)
    finally:
        fu.close()
        fe.close()
    try:  # slutposten blir svarsfilen; utan slutpost (avbruten tur) skrivs ingen, och läget säger fel eller avbrutet
        katalog = _katalog(dash, slug) / 'partner'
        r = _resultat(katalog / ('strom-%s.jsonl' % mid))
        if r:
            tmp = katalog / ('.svar-%s.json.tmp' % mid)
            tmp.write_text(json.dumps(r, ensure_ascii=False), encoding='utf-8')
            os.replace(tmp, katalog / ('svar-%s.json' % mid))
    except OSError:
        pass
    try:
        with _lasat(dash, slug):
            d = _las(dash, slug)
            for m in d.get('meddelanden') or []:
                if isinstance(m, dict) and m.get('id') == mid:
                    m['slut'] = _nu()
                    m['rc'] = proc.returncode
                    if fel:
                        m['fel'] = fel
            _skriv(dash, slug, d)
    except OSError:
        pass
    try:  # en väntande instruktion startar som nästa tur i samma session
        starta_vantande(dash, slug)
    except Exception:  # noqa: BLE001 — den står kvar som väntande, och ägaren kan starta den med Skicka nu
        pass


def _kort_vag(dash, v):
    """En fil som partnern läser, relativt repot; utanför repot bara filnamnet."""
    v = str(v or '')
    for rot in {str(Path(dash.ROOT).resolve()), str(Path(dash.ROOT))}:
        if v.startswith(rot + '/'):
            return v[len(rot) + 1:][:200]
    return os.path.basename(v)[:200]


def _handelser(dash, rad):
    """En rad ur turens strömmade utdata som vyns delhändelser: textdeltan, ett nytt textstycke, att modellen resonerar
    (innehållet visas inte), verktygsanrop med fil, verktygssvarens utfall (inte innehållet) och slutposten. Init, kvotläge
    och allt annat visas inte."""
    try:
        d = json.loads(rad)
    except ValueError:
        return []
    if not isinstance(d, dict):
        return []
    t = d.get('type')
    if t == 'stream_event' and isinstance(d.get('event'), dict):
        e = d['event']
        if e.get('type') == 'content_block_start':
            typ = (e.get('content_block') or {}).get('type') if isinstance(e.get('content_block'), dict) else None
            return [{'typ': 'stycke'}] if typ == 'text' else [{'typ': 'resonerar'}] if typ in ('thinking', 'redacted_thinking') else []
        delta = e.get('delta') if isinstance(e.get('delta'), dict) else {}
        if e.get('type') == 'content_block_delta' and delta.get('type') == 'text_delta':
            return [{'typ': 'text', 'text': str(delta.get('text') or '')}]
        return []
    innehall = (d.get('message') or {}).get('content') if isinstance(d.get('message'), dict) else None
    if t == 'assistant' and isinstance(innehall, list):
        return [{'typ': 'verktyg', 'namn': str(c.get('name') or '?')[:40],
                 'fil': _kort_vag(dash, (c.get('input') or {}).get('file_path')) if isinstance(c.get('input'), dict) and (c.get('input') or {}).get('file_path') else None}
                for c in innehall if isinstance(c, dict) and c.get('type') == 'tool_use']
    if t == 'user' and isinstance(innehall, list):
        return [{'typ': 'verktygssvar', 'fel': bool(c.get('is_error'))} for c in innehall if isinstance(c, dict) and c.get('type') == 'tool_result']
    if t == 'result':
        return [{'typ': 'resultat', 'fel': bool(d.get('is_error')), 'subtyp': str(d.get('subtype') or '')[:40]}]
    return []


def delvis(dash, slug, mid, fran=0, max_byte=8 << 20):
    """Delhändelserna i ett meddelandes tur från byteposition fran (bara hela rader), den nya positionen och, när turen
    är slut och allt är läst, meddelandets läge. Bara den gällande sessionens meddelanden, och aldrig i en blind
    jämförelse. Läsningen ändrar ingenting."""
    if not ID.fullmatch(str(mid or '')):
        raise ValueError('ett meddelande-id behövs')
    b = bindning(dash, slug)
    if b['ab_dold']:
        raise Dold('kunden är en arm i en blind jämförelse som du inte valt i än')
    d = _las(dash, slug)
    med = d.get('meddelanden') if d.get('session_id') and _galler(d, b) else []
    m = next((x for x in med or [] if isinstance(x, dict) and x.get('id') == mid), None)
    if not m:
        raise ValueError('meddelandet finns inte i den gällande partnersessionen')
    handelser, pos, storlek = [], max(0, int(fran or 0)), 0
    if m.get('stromfil'):
        f = _katalog(dash, slug) / 'partner' / Path(str(m['stromfil'])).name
        try:
            with open(f, 'rb') as fh:
                storlek = os.fstat(fh.fileno()).st_size
                fh.seek(pos)
                bit = fh.read(max_byte)
        except OSError:
            bit = b''
        slut = bit.rfind(b'\n')
        if slut >= 0:
            for rad in bit[:slut].split(b'\n'):
                handelser += _handelser(dash, rad.decode('utf-8', 'replace'))
            pos += slut + 1
        elif len(bit) >= max_byte:  # en rad längre än max_byte (ett stort verktygssvar) hoppas över; resten av den tolkas inte
            pos += len(bit)
    klar = bool(m.get('slut')) or (bool(m.get('pid')) and not _lever(m['pid'])) or (not m.get('pid') and bool(m.get('fel')))
    ut = {'handelser': handelser, 'pos': pos, 'klar': klar and pos >= storlek}
    if ut['klar']:
        ml = _meddelandelage(dash, slug, m, d.get('session_id'))
        ut['lage'] = ml['lage']
        ut['fel'] = ml.get('fel') or ('turen slutade med fel (%s)' % (ml['svar'] or {}).get('subtyp') if (ml['svar'] or {}).get('fel') else None)
    return ut


def _nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def _epok(t):
    try:
        return calendar.timegm(time.strptime(str(t), '%Y-%m-%dT%H:%M:%SZ'))
    except (TypeError, ValueError):
        return 0


def _kommando(pid):
    try:
        return subprocess.run(['ps', '-o', 'command=', '-p', str(int(pid))], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return ''
