#!/usr/bin/env python3
"""observation.py — den passiva observatören av designarbetet (ägarens uppdrag 2026-10-06 om Claude Mods och observation).

Gör fyra saker synliga i dashboarden medan en körning pågår, ur det som redan finns:
A referenserna: körningens referenspaket, Refero- och Mobbin-anropen med utfall, lästa referensfiler och referensbilder;
B kompetensen: installerade skills (startkvittot), erbjudna (sessionens skillista), laddade via skillsystemet och lästa
  skillfiler, hela eller utdrag; tillämpningen bedöms för sig (flödets kompetenskvitto, kandidatens granskning);
C prototypen: senaste förhandsvarvet per kandidat, med tid, och den fotograferade versionen;
D arbetsläget: steg, sessioner, senaste händelse, kontextens storlek och komprimeringar, med tider.

Källorna: ateljéns sessionsförteckning underlag/<slug>/atelje/sessioner/<session_id>.json (metadata per nästlad session,
skriven av atelje.session, som ger sessionen sitt id från start med --session-id), Claude Codes transkript
~/.claude/projects/<katalog>/<session_id>.jsonl (bildkedja.transkript), tjänstesessionernas strömmade loggar
underlag/<slug>/referenser/**/session-*.jsonl, statusfilerna, förhandsvarven, planen och startkvittot.

Observatören ändrar ingenting, startar inga modeller och gör inga egna anrop till Refero eller Mobbin. Den lagrar bara
förteckningens metadatafält; resten räknas fram vid läsning och hålls i minnet. Ur ett anrop tas verktygets namn, tiden,
utfallets klass och antalet träffar, bilder och bildlänkar, för Read också sökvägen och omfånget, för de skrivande
verktygen (Edit, Write, MultiEdit, NotebookEdit) bara sökvägen (arbetsytans följvy, 2026-10-09), för skillverktyget
skillens namn; aldrig promptar, övriga verktygsargument, verktygssvar, skrivet innehåll eller bilddata. Etiketterna säger vad som observerats,
aldrig att något använts eller förståtts, och det som saknas heter "inte observerat". Ett fel här gör vyn ofullständig,
aldrig arbetet. En fil som inte går att läsa om visar det senast lästa läget med felet och tiden för den senaste lyckade
läsningen, så att vyn kan säga att det är inaktuellt; en fil som aldrig gått att läsa, och ett transkript som inte längre
finns, heter "inte observerat".

Varför ingen mod: transkriptet bär redan verktygsanropen, läsningarnas omfång, skillverktyget, skillistan, nekanden,
användningen per modellanrop och komprimeringarna. En mod körs i den process som laddar den (--plugin-dir eller en
installerad plugin) och utanför sandlådan; varje claude -p-process, som ateljéns sessioner och tjänstesessionerna, ser
bara en mod som laddats i just den. Underagenter som en session startar körs i samma process: en mod där får agent.spawn
när de startar och ser deras verktygsanrop (tool.call) och modellanrop (turn.step med agentId). Observatören läser bara
sessionens transkript, och underagentens anrop står i ett eget (<session_id>/subagents/agent-*.jsonl), så här syns bara
Agent-anropet och dess utfall. Ateljéns sessioner har inget Agent-verktyg (--tools listar bara det sessionen använder);
en skill som körs i en egen kontext (context: fork) kan ändå starta en underagent, och då syns bara skillanropet.
Kontexten är tokenantalet i senaste modellanropets indata, en uppskattning: det som tillkommit efter anropet räknas inte,
och andelen visas inte, eftersom transkriptet inte anger fönstrets storlek. En mod kan läsa Claude Codes egen siffra
($.session.usage(): tokens, fönster och procent); också den är Claude Codes beräkning, inget oberoende mått.

Av: NWP_OBSERVATION=av i arbetarens miljö (inget sessions-id, ingen förteckning, sessionens argument som förut).
Säkerhetskrokarna och kundvakten berörs inte.
"""
import json
import os
import re
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bildkedja  # noqa: E402  (transkriptens plats, samma som domarnas läsning)

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
KATALOG = 'sessioner'  # under underlag/<slug>/atelje/
FALT = ('session_id', 'roll', 'kandidat', 'svar', 'start', 'modell', 'pid', 'slut', 'utfall')  # förteckningens enda fält
SKILLFIL = re.compile(r'(?:^|/)\.claude/skills/([^/]+)/(.+)$')
BILDLANK = re.compile(r'https?://[^\s"\'<>()\\]+?\.(?:png|jpe?g|webp|avif)(?=[\s"\'<>()\\?#]|$)', re.I)
FOR_STORT = re.compile(r'^Error: result \(.{0,80}exceeds maximum allowed tokens', re.S)
# nekanden utan toolDenialKind (de strömmade loggarna), förankrade i Claude Codes egna texter: behörighetsregler och
# dontAsk, PreToolUse-krokar (kundvakten) och deny-regler för filer; en tjänsts eget felmeddelande är aldrig ett nekande
NEKAT = re.compile(r"^\s*(?:<tool_use_error>\s*)?(?:Permission to \w+\b|Claude requested permissions? to use\b|PreToolUse:\S+ hook\b"
                   r"|File is (?:in a directory that is denied|covered by a \w+ deny rule))")
GAFFLAD = re.compile(r'\(forked execution')  # Claude Codes svar när en skill med context: fork körts av en underagent
TOMT = re.compile(r'(?i)^\s*(no results?( found)?|0 results|inga träffar|nothing found)\b')
AVSLUTADE = ('klar', 'klar_for_bedomning', 'fel', 'forkastad', 'tillbaka')
# sessionens sida ur rollen (svarsfilens namn): skaparens arbete, granskningen eller körningens gemensamma steg
SKAPARE = re.compile(r'^(skiss|skapa|pass|forbattra|forfina|divergera)(-|$)')
GRANSKARE = re.compile(r'^(skisskritik|kritik-a|kritik-b|jamforelse|domare)(-|$)')
STATUS_SV = {'connected': 'ansluten', 'failed': 'misslyckades', 'needs-auth': 'kräver inloggning', 'pending': 'ansluter', 'disabled': 'avstängd'}
HJALP_FRIST = 15
HJALP_OMPROVA_S = 600


def nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def pa():
    return os.environ.get('NWP_OBSERVATION', 'pa') != 'av'


_HJALP = {}
_HJALP_LAS = threading.Lock()
_STROM = {}  # claude --help listar --input-format och --replay-user-messages (löparen, lopare.py); fylls av samma fråga


def flaggan_finns(claude_bin, env=None):
    """Listar claude --help --session-id? Ett tydligt svar gäller resten av processen; ett fel (tidsgräns, saknat
    program) ger nej och prövas igen efter tio minuter, och sessionen startar då som förut. Bara programmets egna fel
    fångas: arbetarens stopp (atelje.Stoppad) går igenom."""
    with _HJALP_LAS:
        svar = _HJALP.get(claude_bin)
        if svar and (svar[1] is None or time.time() - svar[1] < HJALP_OMPROVA_S):
            return svar[0]
        try:
            r = subprocess.run([claude_bin, '--help'], capture_output=True, text=True, timeout=HJALP_FRIST, stdin=subprocess.DEVNULL, env=env)
            _HJALP[claude_bin] = ('--session-id' in r.stdout, None) if r.returncode == 0 else (False, time.time())
            _STROM[claude_bin] = r.returncode == 0 and '--input-format' in r.stdout and '--replay-user-messages' in r.stdout
        except (OSError, subprocess.SubprocessError, ValueError):
            _HJALP[claude_bin] = (False, time.time())
        return _HJALP[claude_bin][0]


def stromflaggor(claude_bin):
    """Listade samma claude --help som flaggan_finns läste strömmande in- och utdata med eko? Ingen egen fråga: utan ett
    svar från flaggan_finns är det nej, och sessionen körs som förut."""
    with _HJALP_LAS:
        return bool(_STROM.get(claude_bin))


# --- förteckningen (atelje.session skriver; ett fel här stoppar aldrig en session) ---

def katalog(slug):
    return UNDERLAG / slug / 'atelje' / KATALOG


def _skriv(f, post):
    """Hela posten eller ingen: läsaren ser aldrig en halvskriven fil."""
    tmp = f.with_name('.%s.%d-%d.tmp' % (f.name, os.getpid(), threading.get_ident()))
    tmp.write_text(json.dumps(post, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(tmp, f)


def anmal(slug, session_id, ut, modell=None, pid=None):
    """En post med metadata när en nästlad session startar: roll och kandidat ur svarsfilens namn och plats."""
    ut = Path(ut)
    m = re.search(r'/kandidater/(k\d{2})/', str(ut))
    k = katalog(slug)
    k.mkdir(parents=True, exist_ok=True)
    _skriv(k / (session_id + '.json'), {'session_id': session_id, 'roll': re.sub(r'^svar-', '', ut.stem), 'kandidat': m.group(1) if m else None,
                                        'svar': ut.name, 'start': nu(), 'modell': modell, 'pid': pid, 'slut': None, 'utfall': None})


def uppdatera(slug, session_id, **falt):
    """Sluttid och utfall i sessionens post; en post som aldrig skrevs skapas inte här."""
    f = katalog(slug) / (session_id + '.json')
    if not f.is_file():
        return
    post = json.loads(f.read_text(encoding='utf-8'))
    post.update({k: v for k, v in falt.items() if k in ('slut', 'utfall')})
    _skriv(f, post)


# --- läsningen: transkript och strömmade loggar, stegvis (bara nya rader vid varje läsning) ---

_LAGE = {}
_LAS = threading.RLock()  # dashboarden svarar i trådar: läsningen och sammanfattningen sker under samma lås


def _ny(ident):
    return {'id': ident, 'pos': 0, 'anrop': {}, 'svar': {}, 'forsta': None, 'senaste': None, 'kontext': None, 'komprimeringar': [],
            'modell': None, 'skills': None, 'mcp': None, 'mcp_verktyg': {}, 'slut': None, 'nekade': 0, 'oforstadda': 0,
            'senast_last': None, 'lasfel': None}


def _lasfel(lage, e):
    """Läget med en varning: när felet kom och vilket det var (felets slag och text, utan sökvägen)."""
    lage['lasfel'] = {'tid': nu(), 'fel': '%s: %s' % (type(e).__name__, str(getattr(e, 'strerror', None) or e)[:120])}
    return lage


def las_session(fil):
    """Läsläget för en session: valda metadatafält ur transkriptet eller den strömmade loggen. Bara rader som tillkommit
    sedan förra läsningen tolkas; en ofullständig sista rad väntar till nästa gång, och en rad med oväntad form räknas
    och hoppas över. Ett nytt eller kortare filinnehåll (en annan fil på samma plats) läses från början; storleken och
    identiteten tas från den öppnade filen. En lyckad läsning sätter senast_last. Ett läsfel (filen borta eller nekad,
    ett avbrott, en fil som inte är en vanlig fil, till exempel en FIFO som annars skulle hålla låset) ger det senast
    lästa läget, eller ett tomt, med lasfel satt, och nästa lyckade läsning tar bort det."""
    fil = Path(fil)
    with _LAS:
        lage = _LAGE.get(str(fil))
        try:
            if not stat.S_ISREG(os.stat(fil).st_mode):
                raise OSError(0, 'inte en vanlig fil')
            with open(fil, 'rb') as f:
                st = os.fstat(f.fileno())
                ident = (st.st_dev, st.st_ino)
                if lage is None or lage['id'] != ident or st.st_size < lage['pos']:
                    lage = _LAGE[str(fil)] = _ny(ident)
                f.seek(lage['pos'])
                data = f.read(st.st_size - lage['pos']) if st.st_size > lage['pos'] else b''
        except OSError as e:
            return _lasfel(lage if lage is not None else _ny(None), e)
        slut = data.rfind(b'\n')
        if slut >= 0:
            for rad in data[:slut].split(b'\n'):
                try:
                    _rad(lage, rad)
                except Exception:  # noqa: BLE001 — en rad med oväntad form stoppar aldrig läsningen
                    lage['oforstadda'] += 1
            lage['pos'] += slut + 1
        lage['senast_last'], lage['lasfel'] = nu(), None
        return lage


def _lista(x):
    return x if isinstance(x, list) else []


def _tal(x):
    try:
        return int(x or 0)
    except (TypeError, ValueError):
        return 0


def _rad(lage, rad):
    try:
        r = json.loads(rad)
    except ValueError:
        return
    if not isinstance(r, dict):
        return
    t = r.get('timestamp') if isinstance(r.get('timestamp'), str) else None
    if t:
        lage['senaste'] = t
        lage['forsta'] = lage['forsta'] or t
    typ = r.get('type')
    if typ == 'system':
        if r.get('subtype') == 'init':  # den strömmade loggens första rad
            lage['modell'] = str(r.get('model') or '') or lage['modell']
            lage['skills'] = [str(x.get('name') if isinstance(x, dict) else x) for x in _lista(r.get('skills'))]
            lage['mcp'] = {str(x.get('name')): STATUS_SV.get(str(x.get('status')), str(x.get('status'))) for x in _lista(r.get('mcp_servers')) if isinstance(x, dict)}
        elif r.get('subtype') == 'compact_boundary':
            m = r.get('compactMetadata') or r.get('compact_metadata')
            m = m if isinstance(m, dict) else {}
            lage['komprimeringar'].append({'tid': t, 'utlost': m.get('trigger'), 'fore': m.get('preTokens') or m.get('pre_tokens')})
        return
    if typ == 'attachment':
        a = r.get('attachment') if isinstance(r.get('attachment'), dict) else {}
        if a.get('type') == 'skill_listing':
            namn = [str(x) for x in _lista(a.get('names'))]
            lage['skills'] = namn if a.get('isInitial') or lage['skills'] is None else sorted(set(lage['skills']) | set(namn))
        elif a.get('type') == 'model':
            i = a.get('identity')
            lage['modell'] = (i.get('modelId') if isinstance(i, dict) else None) or lage['modell']
        elif a.get('type') == 'deferred_tools_delta':
            v = lage['mcp_verktyg']
            for n in _lista(a.get('addedNames')):
                if str(n).startswith('mcp__'):
                    v.setdefault(str(n).split('__')[1], set()).add(str(n))
            for n in _lista(a.get('removedNames')):
                if str(n).startswith('mcp__'):
                    v.setdefault(str(n).split('__')[1], set()).discard(str(n))
            mcp = lage['mcp'] or {}
            mcp.update({s_: 'ansluten' if vs else 'verktygen borttagna' for s_, vs in v.items()})
            for falt, etikett in (('pendingMcpServers', 'ansluter'), ('needsAuthMcpServers', 'kräver inloggning'), ('failedMcpServers', 'misslyckades')):
                for n in _lista(a.get(falt)):
                    mcp[str(n.get('name') if isinstance(n, dict) else n)] = etikett
            lage['mcp'] = mcp
        return
    if typ == 'result':  # den strömmade loggens sista rad
        lage['slut'] = {'tid': t or lage['senaste'], 'utfall': str(r.get('subtype') or ''), 'fel': bool(r.get('is_error')), 'turer': _tal(r.get('num_turns'))}
        return
    msg = r.get('message') if isinstance(r.get('message'), dict) else {}
    if typ == 'assistant':
        if isinstance(msg.get('model'), str) and msg['model'] != '<synthetic>':
            lage['modell'] = msg['model']
        u = msg.get('usage') if isinstance(msg.get('usage'), dict) else {}
        n = sum(_tal(u.get(k)) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))
        if n:
            lage['kontext'] = {'tokens': n, 'tid': t}
    resultat = r.get('toolUseResult', r.get('tool_use_result'))
    for c in _lista(msg.get('content')):
        if not isinstance(c, dict):
            continue
        if c.get('type') == 'tool_use':
            lage['anrop'][str(c.get('id'))] = _anrop(c, t)
        elif c.get('type') == 'tool_result':
            s = _svar(lage['anrop'].get(str(c.get('tool_use_id'))), c, resultat, r.get('toolDenialKind'), t)
            lage['nekade'] += s['utfall'] == 'nekat'
            lage['svar'][str(c.get('tool_use_id'))] = s


def _anrop(c, t):
    """Bara namnet och tiden; för Read sökvägen och om ett omfång begärdes, för skillverktyget skillens namn."""
    namn = str(c.get('name') or '?')[:120]
    inn = c.get('input') if isinstance(c.get('input'), dict) else {}
    a = {'namn': namn, 'tid': t}
    if namn == 'Read' and isinstance(inn.get('file_path'), str):
        a['fil'] = inn['file_path'][:400]
        a['begransad'] = inn.get('offset') is not None or inn.get('limit') is not None or inn.get('pages') is not None
    elif namn == 'Skill':
        s = inn.get('skill') or inn.get('command')
        a['skill'] = str(s)[:80] if s else None
    elif namn in SKRIVVERKTYG and isinstance(inn.get('file_path') or inn.get('notebook_path'), str):
        a['fil'] = (inn.get('file_path') or inn.get('notebook_path'))[:400]  # bara sökvägen (arbetsytans följvy), aldrig innehållet
    return a


SKRIVVERKTYG = ('Edit', 'Write', 'MultiEdit', 'NotebookEdit')


def aktivitet(fil, slug=None, n=40, vagar=True):
    """Sessionens senaste observerade händelser för arbetsytans följvy (ägarens uppdrag 2026-10-09), ur samma läsläge som
    sammanfattningen: verktygets namn, tid och utfallets klass, för Read och de skrivande verktygen sökvägen och för
    skillverktyget skillens namn. Inget nytt lagras och inget innehåll läses. Ett anrop utan observerat svar är pågående
    (väntar på verktyget). vagar=False tar bort sökvägarna (före ägarens första val). Ger (None, skälet) när filen aldrig
    gått att läsa."""
    with _LAS:
        lage = las_session(fil)
        if lage.get('lasfel') and not lage.get('senast_last'):
            return None, 'kunde inte läsas: %s' % lage['lasfel']['fel']
        alla = list(lage['anrop'].items())
        ut = []
        for i, a in alla[-n:]:
            s = lage['svar'].get(i)
            h = {'tid': a.get('tid'), 'verktyg': a['namn'], 'utfall': (s or {}).get('utfall') or 'pågår', 'klar_tid': (s or {}).get('tid')}
            if vagar and a.get('fil'):
                rel = _relativ(a['fil'])
                if slug and '/underlag/%s/' % slug in '/' + rel:
                    rel = rel[('/' + rel).index('/underlag/%s/' % slug):]
                h['fil'] = rel
            if a.get('skill'):
                h['skill'] = a['skill']
            ut.append(h)
        pagaende = [a['namn'] for i, a in alla if i not in lage['svar']][-5:]
        return {'handelser': ut, 'antal': len(alla), 'pagaende': pagaende, 'senaste_handelse': lage.get('senaste'),
                'slut': dict(lage['slut']) if lage.get('slut') else None, 'senast_last': lage.get('senast_last'),
                'lasfel': dict(lage['lasfel']) if lage.get('lasfel') else None}, None


# ett MCP-svar som är en feltext fast tjänsten inte satte is_error, och ett svar som säger att inget matchade
FELTEXT = re.compile(r'^\s*(?:\[?error\]?|fel|mcp error)\b', re.I)
INGA_TRAFFAR = re.compile(r'^\s*(?:no|inga|0)\b[^\n.]{0,80}\b(?:match|found|result|träff|hittade)', re.I)
# tjänster vars svar är ett dokument i text (Motions dokumentationssök), inte en lista eller bilder: en text med innehåll är
# där ett lyckat anrop med känd form (motorinventeringen F03). För Refero och Mobbin, vars svar är listor eller bilder, är
# en text utan känd lista fortfarande 'svar utan känd form' (C6:s rest).
DOKUMENTSVAR = ('mcp__motion__',)


def _traffar(text):
    """Antalet träffar i ett tjänstesvar när det går att läsa ut (Referos records, en lista); annars None."""
    try:
        d = json.loads(text)
    except ValueError:
        return 0 if TOMT.match(text or '') else None
    if isinstance(d, list):
        return len(d)
    if isinstance(d, dict):
        for k in ('records', 'results', 'screens', 'flows', 'sections', 'items'):
            if isinstance(d.get(k), list):
                return len(d[k])
    return None


def _svar(a, c, res, nekad, t):
    """Utfallets klass, aldrig innehållet."""
    namn = (a or {}).get('namn') or ''
    x = c.get('content')
    text = x if isinstance(x, str) else ''.join(str(y.get('text') or '') for y in x if isinstance(y, dict) and y.get('type') == 'text') if isinstance(x, list) else ''
    bilder = sum(1 for y in x if isinstance(y, dict) and y.get('type') == 'image') if isinstance(x, list) else 0
    ut = {'tid': t}
    if nekad or (c.get('is_error') is True and NEKAT.search(text[:600])):
        return dict(ut, utfall='nekat', slag=str(nekad)[:40] if nekad else None)
    if c.get('is_error') is True:
        return dict(ut, utfall='fel')
    if FOR_STORT.match(text):
        return dict(ut, utfall='svaret för stort, sparat till fil')
    if namn == 'Read':
        r = res if isinstance(res, dict) else {}
        f = r.get('file') if isinstance(r.get('file'), dict) else {}
        if r.get('type') == 'image' or bilder:
            return dict(ut, utfall='bild läst')
        if r.get('type') == 'text' and f:
            s, n, tot = f.get('startLine', 1), f.get('numLines'), f.get('totalLines')
            if not all(isinstance(v, int) for v in (s, n, tot)):
                return dict(ut, utfall='fil läst (omfång inte observerat)')
            if s <= 1 and n >= tot:
                return dict(ut, utfall='fil läst (hel)')
            return dict(ut, utfall='fil läst (utdrag)', rader=[s, s + max(n, 1) - 1, tot])
        if r.get('type') == 'file_unchanged':
            return dict(ut, utfall='oförändrad sedan förra läsningen')
        if r.get('type'):
            return dict(ut, utfall='fil läst (%s)' % str(r['type'])[:30])
        return dict(ut, utfall='fil läst (utdrag)' if (a or {}).get('begransad') else 'fil läst (omfång inte observerat)')
    if namn == 'Skill':
        if GAFFLAD.search(text[:400]):  # skillen kördes i en egen kontext, av en underagent, vars läsningar inte står här
            return dict(ut, utfall='skill körd av en underagent (dess läsningar syns inte)')
        return dict(ut, utfall='skill laddad via skillsystemet')
    if namn.startswith('mcp__'):
        tr, lankar = _traffar(text), len(set(BILDLANK.findall(text)))
        if tr is None and not lankar and not bilder:  # ett textsvar utan känd lista (GR-20261008-r117-claude#C6)
            if FELTEXT.match(text):
                return dict(ut, utfall='fel')
            if INGA_TRAFFAR.match(text):
                return dict(ut, utfall='tomt resultat', traffar=0)
            if text.strip():
                if namn.startswith(DOKUMENTSVAR):  # ett dokument i text är tjänstens form: svaret har innehåll
                    return dict(ut, utfall='anrop lyckades', tecken=len(text.strip()))
                return dict(ut, utfall='svar utan känd form')  # varken fel, tomt eller en läsbar lista: innehållet är inte observerat (C6:s rest; kompetens.UTAN_FORM)
        ut.update({k: v for k, v in (('traffar', tr), ('bilder', bilder), ('bildlankar', lankar)) if v})
        if bilder:
            return dict(ut, utfall='bild returnerad')
        if tr == 0 or not text.strip():
            return dict(ut, utfall='tomt resultat')
        return dict(ut, utfall='anrop lyckades')
    return dict(ut, utfall='klart')


def _relativ(vag):
    if vag.startswith(str(ROOT) + '/'):
        return vag[len(str(ROOT)) + 1:]
    if vag.startswith(str(Path.home()) + '/'):
        return '~/' + vag[len(str(Path.home())) + 1:]
    return vag


def sammanfatta(lage, slug=None):
    """Den kompakta vyn av en session, som nya objekt (aldrig läslägets egna). Läsningarna delas i referenser,
    skillfiler, flödets metodutdrag och övrigt."""
    if not lage:
        return None
    mcp, refs, skillfiler, metod, skills, verktyg = [], [], [], [], [], {}
    for i, a in list(lage['anrop'].items()):
        s = lage['svar'].get(i) or {}
        utfall = s.get('utfall') or 'inget svar observerat'
        v = verktyg.setdefault(a['namn'], {})
        v[utfall] = v.get(utfall, 0) + 1
        if a['namn'].startswith('mcp__'):  # varje tjänst sessionen anropade, också Motion och sådana flödet inte tilldelat (F03)
            d = a['namn'].split('__', 2)
            mcp.append({'tjanst': d[1], 'verktyg': d[2] if len(d) > 2 else '', 'utfall': utfall, 'tid': a['tid'],
                        **{k: s[k] for k in ('traffar', 'bilder', 'bildlankar', 'tecken') if s.get(k)}})
        elif a['namn'] == 'Skill':
            skills.append({'skill': a.get('skill'), 'utfall': utfall, 'tid': a['tid']})
        elif a['namn'] == 'Read' and a.get('fil'):
            rel = _relativ(a['fil'])
            if slug and '/underlag/%s/' % slug in '/' + rel:  # också när sessionen gick i en annan utcheckning av repot
                rel = rel[('/' + rel).index('/underlag/%s/' % slug):]
            post = {'fil': rel, 'utfall': utfall, 'tid': a['tid'], **({'rader': list(s['rader'])} if s.get('rader') else {})}
            m = SKILLFIL.search(rel)
            if m:
                skillfiler.append(dict(post, skill=m.group(1), skillmd=m.group(2) == 'SKILL.md'))
            elif slug and rel.startswith('underlag/%s/referenser/' % slug):
                refs.append(post)
            elif slug and rel.startswith('underlag/%s/atelje/' % slug) and '/METOD' in rel:
                metod.append(post)
    k = lage.get('kontext')
    return {'modell': lage.get('modell'), 'forsta_handelse': lage.get('forsta'), 'senaste_handelse': lage.get('senaste'),
            'kontext': dict(k, uppskattning=True) if k else None, 'komprimeringar': [dict(x) for x in lage.get('komprimeringar') or []],
            'skills_erbjudna': len(lage['skills']) if lage.get('skills') is not None else None,
            'mcp_lage': dict(lage['mcp']) if lage.get('mcp') is not None else None,
            'mcp': sorted(mcp, key=lambda x: x['tid'] or ''), 'skills_laddade': skills, 'skillfiler': skillfiler, 'metodutdrag': metod,
            'referensfiler': refs, 'nekade': lage.get('nekade', 0), 'oforstadda_rader': lage.get('oforstadda', 0), 'verktyg': verktyg,
            'slut': dict(lage['slut']) if lage.get('slut') else None,
            'senast_last': lage.get('senast_last'), 'lasfel': dict(lage['lasfel']) if lage.get('lasfel') else None}


def sammanfattning(fil, slug=None):
    """Läsningen och sammanfattningen under samma lås: en samtidig läsning ändrar aldrig det som sammanfattas."""
    with _LAS:
        return sammanfatta(las_session(fil), slug)


def observerad(fil, slug, vad):
    """(sammanfattningen, None), eller (None, skälet) när filen aldrig har gått att läsa: ett tomt läge med läsfel är
    ingen observation, och vyn säger då "inte observerat" med felet i stället för "inga observerade" (granskningen av
    r92, BÖR 1)."""
    ob = sammanfattning(fil, slug)
    if ob and ob.get('lasfel') and not ob.get('senast_last'):
        return None, '%s kunde inte läsas: %s' % (vad, ob['lasfel']['fel'])
    return ob, None


def lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def sida(roll):
    roll = str(roll or '')
    return 'skapare' if SKAPARE.match(roll) else 'granskare' if GRANSKARE.match(roll) else 'korning'


def _mtid(p):
    try:
        return p.stat().st_mtime
    except OSError:
        return 0


def sessioner(slug):
    """Ateljéns sessioner ur förteckningen, nyast först, med det transkriptet visar. Pågår betyder att posten saknar
    slut och att pid:en är en levande nästlad claude-session (nastlad.ar_session), inte bara en levande pid. En post som
    inte går att läsa står med som ofullständig, så att vyn säger att något saknas."""
    import nastlad
    k = katalog(slug)
    ut = []
    for f in sorted(k.glob('*.json'), key=_mtid, reverse=True) if k.is_dir() else []:
        try:
            post = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError) as e:
            ut.append(dict({x: None for x in FALT}, ofullstandig='förteckningsposten %s kunde inte läsas: %s' % (f.name[:60], type(e).__name__)))
            continue
        if not isinstance(post, dict) or not bildkedja.SESSION.match(str(post.get('session_id') or '')):
            ut.append(dict({x: None for x in FALT}, ofullstandig='förteckningsposten %s har oväntad form' % f.name[:60]))
            continue
        post = {x: post.get(x) for x in FALT}
        try:
            tr = bildkedja.transkript(post['session_id'])
            post['sida'] = sida(post['roll'])
            post['pagar'] = bool(not post.get('slut') and post.get('pid') and lever(post['pid']) and nastlad.ar_session(post['pid']))
            post['transkript'] = _relativ(str(tr)) if tr else None
            post['observation'], skal = observerad(tr, slug, 'transkriptet') if tr else (None, None)
            if skal:
                post['ofullstandig'] = skal
        except Exception as e:  # noqa: BLE001 — en session som inte går att läsa gör bara den ofullständig
            post['ofullstandig'] = '%s: %s' % (type(e).__name__, str(e)[:160])
        ut.append(post)
    return ut


def tjanstesessioner(slug, efter=None):
    """Refero- och Mobbin-sessionerna (researchens tjänster, uppdragsmaterialet) ur deras strömmade loggar, från efter."""
    ut = []
    for f in sorted((UNDERLAG / slug / 'referenser').glob('**/session-*.jsonl')):
        if efter and time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(_mtid(f))) < efter:
            continue
        rel = f.relative_to(UNDERLAG / slug)
        post = {'logg': str(rel), 'tjanst': f.parent.name, 'del': rel.parts[1] if len(rel.parts) > 2 else None}
        try:
            ob, skal = observerad(f, slug, 'loggen')
            post.update({'observation': ob} if ob else {'ofullstandig': skal})
        except Exception as e:  # noqa: BLE001
            post['ofullstandig'] = '%s: %s' % (type(e).__name__, str(e)[:160])
        ut.append(post)
    return ut


NAMNSLUT = re.compile(r'\s+[—–·-]+\s+|:\s+|:$|[,;]|\s+(?:som|med|där|för|bär|ger|with|that|which|for)\s+', re.I)


def referensnamn(text):
    """Bara huvudreferensens namn ur planens text, aldrig beskrivningen (som kandidater.sammanstall håller tillbaka före
    ägarens första beslut; BESLUT.md 2026-10-05, punkt 1): delen före det första tankstrecket, kolonet, kommat, semikolonet
    eller beskrivande ordet ("som", "med", "bär" …), utan något efter en avslutande parentes. Blir det mer än fyra ord går
    namnet inte att skilja från beskrivningen, och då None (vyn säger "inte observerad")."""
    t = str(text or '').strip().strip('*`').strip()
    fore, parentes, rest = t.partition('(')
    kort = NAMNSLUT.split(fore, maxsplit=1)[0].strip()
    # namnet direkt följt av en parentes (domänen): parentesen hel; annars, eller om den blir för lång, namnet utan den
    prova = [kort + ' (' + rest.split(')', 1)[0] + ')'] if parentes and ')' in rest and kort == fore.strip() else []
    for x in prova + [kort]:
        x = x.strip().strip('*`').strip()
        if x.lower() in ('egen', 'egen riktning', 'ingen'):
            return 'egen riktning'
        if x and len(x.split()) <= 4 and len(x) <= 60:
            return x
    return None


def referenser(slug):
    """Körningens referenspaket och kandidaternas huvudreferenser ur planen (det flödet erbjöd, inte det som lästes)."""
    a = UNDERLAG / slug / 'atelje'
    fo = bildkedja.las_json(a / 'FORSKNING.json') or {}
    plan = (bildkedja.las_json(a / 'KANDIDATPLAN.json') or {}).get('kandidater') or {}
    paket = (fo.get('nytt') or {}).get('paket') or (fo.get('fore') or {}).get('paket')
    pk = bildkedja.las_json(UNDERLAG / slug / 'referenser' / str(paket) / 'PAKET.json') if paket else None
    return {'paket': paket, 'paket_tid': (pk or {}).get('tid') if isinstance(pk, dict) else None,
            'tjanster_tid': (fo.get('nytt') or {}).get('tjanster'),
            'kandidater': {kid: {'huvudreferens': referensnamn(k.get('huvudreferens')), 'referensbilder': len(_lista(k.get('referensbilder')))}
                           for kid, k in plan.items() if isinstance(k, dict)} if isinstance(plan, dict) else {}}


def installerat(slug):
    """De installerade skillsen enligt körningens startkvitto (startkontrollen läste dem vid starten)."""
    kv = bildkedja.las_json(UNDERLAG / slug / 'atelje' / 'STARTKVITTO.json') or {}
    rader = [r for r in _lista(kv.get('rader')) if isinstance(r, dict) and r.get('typ') == 'skill']
    return {'tid': kv.get('tid'), 'antal': len(rader), 'namn': sorted(str(r.get('namn')) for r in rader)} if rader else None


def prototyper(slug):
    """Per kandidat: senaste förhandsvarvet under arbetet och den fotograferade versionen, åtskilda. Tiden är när
    skärmbilden fångades (filens tid). Flödets kompetenskvitton är läsbevis (lästa och saknade filer), inget omdöme."""
    ut = {}
    for d in sorted((UNDERLAG / slug / 'atelje' / 'kandidater').glob('k[0-9][0-9]')):
        st = bildkedja.las_json(d / 'STATUS.json') or {}
        varv = sorted((p for p in (d / 'varv' / 'start').glob('varv-[0-9][0-9]') if p.is_dir()), key=lambda p: p.name)
        senaste, bilder, fangad = (varv[-1] if varv else None), {}, None
        for b in ('390', '1280', '1440'):
            p = senaste / ('vy-%s-forsta.png' % b) if senaste else None
            if p and p.is_file():
                bilder[b] = str(p.relative_to(ROOT))
                m = _mtid(p)  # 0: tiden gick inte att läsa, och då står ingen tid (aldrig 1970)
                fangad = max(fangad or '', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(m))) if m else fangad
        kv = st.get('kompetens') if isinstance(st.get('kompetens'), dict) else {}
        ut[d.name] = {'status': st.get('status'), 'skal': st.get('skal'), 'varv_antal': len(varv),
                      'varv': {'namn': senaste.name, 'skarmbild_fangad': fangad, 'bilder': bilder} if senaste else None,
                      'version': (str(st.get('version') or ''))[:12] or None, 'fotograferad': st.get('fotograferad'),
                      'kompetenskvitton': [{'pass': n, 'verifierad': (p.get('kvitto') or {}).get('verifierad'),
                                            'lasta': len(_lista((p.get('kvitto') or {}).get('lasta'))), 'saknas': _lista((p.get('kvitto') or {}).get('saknas')),
                                            'genomford': p.get('genomford')} for n, p in kv.items() if isinstance(p, dict)]}
    return ut


def arbetslage(slug):
    """Körningens steg och tider ur statusfilen (sanningskällan); om arbetaren lever ur dess pid, None utan pid."""
    st = bildkedja.las_json(UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    return {'steg': st.get('steg'), 'startad': st.get('startad'), 'tider': st.get('tider') if isinstance(st.get('tider'), dict) else {},
            'fel': st.get('fel'), 'avslutad': st.get('steg') in AVSLUTADE, 'arbetaren_lever': lever(st['pid']) if st.get('pid') else None}


def oversikt(slug):
    """Allt för dashboardens vy. En del som fallerar blir ofullständig med skälet; resten visas ändå."""
    ut = {'tid': nu()}
    for namn, f in (('arbetslage', arbetslage), ('referenser', referenser), ('installerat', installerat), ('prototyper', prototyper),
                    ('sessioner', sessioner)):
        try:
            ut[namn] = f(slug)
        except Exception as e:  # noqa: BLE001
            ut[namn] = {'ofullstandig': '%s: %s' % (type(e).__name__, str(e)[:160])}
    try:
        ut['tjanster'] = tjanstesessioner(slug, efter=(ut.get('arbetslage') or {}).get('startad'))
    except Exception as e:  # noqa: BLE001
        ut['tjanster'] = {'ofullstandig': '%s: %s' % (type(e).__name__, str(e)[:160])}
    return ut


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('användning: observation.py <slug>', file=sys.stderr)
        sys.exit(2)
    print(json.dumps(oversikt(sys.argv[1]), ensure_ascii=False, indent=1))
