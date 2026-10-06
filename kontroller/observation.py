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
utfallets klass och antalet träffar, bilder och bildlänkar, för Read också sökvägen och omfånget, för skillverktyget
skillens namn; aldrig promptar, verktygsargument, verktygssvar eller bilddata. Etiketterna säger vad som observerats,
aldrig att något använts eller förståtts, och det som saknas heter "inte observerat". Ett fel här gör vyn ofullständig,
aldrig arbetet.

Varför ingen mod: en mod laddas per process med --plugin-dir, ärvs inte av underagenter och körs utanför sandlådan, medan
transkriptet redan bär verktygsanropen, läsningarnas omfång, skillverktyget, skillistan, nekanden, användningen per tur
och komprimeringarna. Det en mod hade gett utöver det är kontextens exakta andel; här är storleken en uppskattning.

Av: NWP_OBSERVATION=av i arbetarens miljö (inget sessions-id, ingen förteckning, sessionens argument som förut).
Säkerhetskrokarna och kundvakten berörs inte.
"""
import json
import os
import re
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
SKILLFIL = re.compile(r'(?:^|/)\.claude/skills/([^/]+)/(.+)$')
BILDLANK = re.compile(r'https?://[^\s"\'<>()\\]+?\.(?:png|jpe?g|webp|avif)(?=[\s"\'<>()\\?#]|$)', re.I)
FOR_STORT = re.compile(r'^Error: result \(.{0,80}exceeds maximum allowed tokens', re.S)
NEKAT = re.compile(r"(?i)permission to use|haven't granted|has been denied|denied by|blocked by (a )?hook|kundvakt")
TOMT = re.compile(r'(?i)^\s*(no results?( found)?|0 results|inga träffar|nothing found)\b')
AVSLUTADE = ('klar', 'klar_for_bedomning', 'fel', 'forkastad', 'tillbaka')


def nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def pa():
    return os.environ.get('NWP_OBSERVATION', 'pa') != 'av'


_HJALP = {}


def flaggan_finns(claude_bin):
    """Listar claude --help --session-id? En gång per process; ett fel ger nej, och sessionen startar då som förut."""
    if claude_bin not in _HJALP:
        try:
            r = subprocess.run([claude_bin, '--help'], capture_output=True, text=True, timeout=30)
            _HJALP[claude_bin] = r.returncode == 0 and '--session-id' in r.stdout
        except Exception:  # noqa: BLE001
            _HJALP[claude_bin] = False
    return _HJALP[claude_bin]


# --- förteckningen (atelje.session skriver; ett fel här stoppar aldrig en session) ---

def katalog(slug):
    return UNDERLAG / slug / 'atelje' / KATALOG


def anmal(slug, session_id, ut, modell=None, pid=None):
    """En post med metadata när en nästlad session startar: roll och kandidat ur svarsfilens namn och plats."""
    ut = Path(ut)
    m = re.search(r'/kandidater/(k\d{2})/', str(ut))
    post = {'session_id': session_id, 'roll': re.sub(r'^svar-', '', ut.stem), 'kandidat': m.group(1) if m else None,
            'svar': ut.name, 'start': nu(), 'modell': modell, 'pid': pid, 'slut': None, 'utfall': None}
    k = katalog(slug)
    k.mkdir(parents=True, exist_ok=True)
    (k / (session_id + '.json')).write_text(json.dumps(post, ensure_ascii=False) + '\n', encoding='utf-8')


def uppdatera(slug, session_id, **falt):
    """Sluttid och utfall i sessionens post; en post som aldrig skrevs skapas inte här."""
    f = katalog(slug) / (session_id + '.json')
    if not f.is_file():
        return
    post = json.loads(f.read_text(encoding='utf-8'))
    post.update({k: v for k, v in falt.items() if k in ('slut', 'utfall')})
    f.write_text(json.dumps(post, ensure_ascii=False) + '\n', encoding='utf-8')


# --- läsningen: transkript och strömmade loggar, stegvis (bara nya rader vid varje läsning) ---

_LAGE = {}
_LAS = threading.Lock()


def _ny(ident):
    return {'id': ident, 'pos': 0, 'anrop': {}, 'svar': {}, 'forsta': None, 'senaste': None, 'kontext': None,
            'komprimeringar': [], 'modell': None, 'skills': None, 'mcp': None, 'slut': None, 'nekade': 0}


def las_session(fil):
    """Läsläget för en session: valda metadatafält ur transkriptet eller den strömmade loggen. Bara rader som tillkommit
    sedan förra läsningen tolkas; en ofullständig sista rad väntar till nästa gång."""
    fil = Path(fil)
    with _LAS:
        try:
            st = fil.stat()
        except OSError:
            return None
        ident = (st.st_dev, st.st_ino)
        lage = _LAGE.get(str(fil))
        if lage is None or lage['id'] != ident or st.st_size < lage['pos']:
            lage = _LAGE[str(fil)] = _ny(ident)
        if st.st_size > lage['pos']:
            try:
                with open(fil, 'rb') as f:
                    f.seek(lage['pos'])
                    data = f.read(st.st_size - lage['pos'])
            except OSError:
                return lage
            slut = data.rfind(b'\n')
            if slut >= 0:
                for rad in data[:slut].split(b'\n'):
                    _rad(lage, rad)
                lage['pos'] += slut + 1
        return lage


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
            lage['modell'] = r.get('model') or lage['modell']
            lage['skills'] = [str(x.get('name') if isinstance(x, dict) else x) for x in r.get('skills') or []]
            lage['mcp'] = {str(x.get('name')): str(x.get('status')) for x in r.get('mcp_servers') or [] if isinstance(x, dict)}
        elif r.get('subtype') == 'compact_boundary':
            m = r.get('compactMetadata') or r.get('compact_metadata') or {}
            lage['komprimeringar'].append({'tid': t, 'utlost': m.get('trigger'), 'fore': m.get('preTokens') or m.get('pre_tokens')})
        return
    if typ == 'attachment':
        a = r.get('attachment') if isinstance(r.get('attachment'), dict) else {}
        if a.get('type') == 'skill_listing':
            namn = [str(x) for x in a.get('names') or []]
            lage['skills'] = namn if a.get('isInitial') or lage['skills'] is None else sorted(set(lage['skills']) | set(namn))
        elif a.get('type') == 'model':
            lage['modell'] = (a.get('identity') or {}).get('modelId') or lage['modell']
        elif a.get('type') == 'deferred_tools_delta':
            mcp = lage['mcp'] or {}
            for n in a.get('addedNames') or []:
                if str(n).startswith('mcp__'):
                    mcp[str(n).split('__')[1]] = 'ansluten'
            for falt, etikett in (('pendingMcpServers', 'ansluter'), ('needsAuthMcpServers', 'kräver inloggning'), ('failedMcpServers', 'misslyckades')):
                for n in a.get(falt) or []:
                    mcp[str(n.get('name') if isinstance(n, dict) else n)] = etikett
            lage['mcp'] = mcp
        return
    if typ == 'result':  # den strömmade loggens sista rad
        lage['slut'] = {'tid': t or lage['senaste'], 'utfall': r.get('subtype'), 'fel': bool(r.get('is_error')), 'turer': r.get('num_turns')}
        return
    msg = r.get('message') if isinstance(r.get('message'), dict) else {}
    if typ == 'assistant':
        if msg.get('model') and msg.get('model') != '<synthetic>':
            lage['modell'] = msg['model']
        u = msg.get('usage') if isinstance(msg.get('usage'), dict) else {}
        if u:
            n = sum(int(u.get(k) or 0) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))
            if n:
                lage['kontext'] = {'tokens': n, 'tid': t}
    resultat = r.get('toolUseResult', r.get('tool_use_result'))
    for c in msg.get('content') if isinstance(msg.get('content'), list) else []:
        if not isinstance(c, dict):
            continue
        if c.get('type') == 'tool_use':
            lage['anrop'][c.get('id')] = _anrop(c, t)
        elif c.get('type') == 'tool_result':
            s = _svar(lage['anrop'].get(c.get('tool_use_id')), c, resultat, r.get('toolDenialKind'), t)
            lage['nekade'] += s['utfall'] == 'nekat'
            lage['svar'][c.get('tool_use_id')] = s


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
    return a


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
    text = x if isinstance(x, str) else ''.join(y.get('text') or '' for y in x if isinstance(y, dict) and y.get('type') == 'text') if isinstance(x, list) else ''
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
            s, n, tot = int(f.get('startLine') or 1), int(f.get('numLines') or 0), int(f.get('totalLines') or 0)
            if s <= 1 and n >= tot:
                return dict(ut, utfall='fil läst (hel)')
            return dict(ut, utfall='fil läst (utdrag)', rader=[s, s + max(n, 1) - 1, tot])
        if r.get('type'):
            return dict(ut, utfall='fil läst (%s)' % str(r['type'])[:30])
        return dict(ut, utfall='fil läst (utdrag)' if (a or {}).get('begransad') else 'fil läst (omfång inte observerat)')
    if namn == 'Skill':
        return dict(ut, utfall='skill laddad via skillsystemet')
    if namn.startswith('mcp__'):
        tr, lankar = _traffar(text), len(set(BILDLANK.findall(text)))
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
    """Den kompakta vyn av en session. Läsningarna delas i referenser, skillfiler, flödets metodutdrag och övrigt."""
    if not lage:
        return None
    mcp, refs, skillfiler, metod, skills, verktyg = [], [], [], [], [], {}
    for i, a in lage['anrop'].items():
        s = lage['svar'].get(i) or {}
        utfall = s.get('utfall') or 'inget svar observerat'
        v = verktyg.setdefault(a['namn'], {})
        v[utfall] = v.get(utfall, 0) + 1
        if a['namn'].startswith(('mcp__refero__', 'mcp__mobbin__')):
            d = a['namn'].split('__', 2)
            mcp.append({'tjanst': d[1], 'verktyg': d[2], 'utfall': utfall, 'tid': a['tid'],
                        **{k: s[k] for k in ('traffar', 'bilder', 'bildlankar') if s.get(k)}})
        elif a['namn'] == 'Skill':
            skills.append({'skill': a.get('skill'), 'utfall': utfall, 'tid': a['tid']})
        elif a['namn'] == 'Read' and a.get('fil'):
            rel = _relativ(a['fil'])
            post = {'fil': rel, 'utfall': utfall, 'tid': a['tid'], **({'rader': s['rader']} if s.get('rader') else {})}
            m = SKILLFIL.search(rel)
            if m:
                skillfiler.append(dict(post, skill=m.group(1), skillmd=m.group(2) == 'SKILL.md'))
            elif slug and rel.startswith('underlag/%s/referenser/' % slug):
                refs.append(post)
            elif slug and rel.startswith('underlag/%s/atelje/' % slug) and '/METOD' in rel:
                metod.append(post)
    k = lage.get('kontext')
    return {'modell': lage.get('modell'), 'forsta_handelse': lage.get('forsta'), 'senaste_handelse': lage.get('senaste'),
            'kontext': dict(k, uppskattning=True) if k else None, 'komprimeringar': lage.get('komprimeringar') or [],
            'skills_erbjudna': len(lage['skills']) if lage.get('skills') is not None else None, 'mcp_lage': lage.get('mcp'),
            'mcp': sorted(mcp, key=lambda x: x['tid'] or ''), 'skills_laddade': skills, 'skillfiler': skillfiler,
            'metodutdrag': metod, 'referensfiler': refs, 'nekade': lage.get('nekade', 0), 'verktyg': verktyg, 'slut': lage.get('slut')}


def lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def sessioner(slug):
    """Ateljéns sessioner ur förteckningen, nyast först, med det transkriptet visar."""
    k = katalog(slug)
    filer = sorted(k.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True) if k.is_dir() else []
    ut = []
    for f in filer:
        try:
            post = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not isinstance(post, dict) or not bildkedja.SESSION.match(str(post.get('session_id') or '')):
            continue
        tr = bildkedja.transkript(post['session_id'])
        post['pagar'] = bool(not post.get('slut') and post.get('pid') and lever(post['pid']))
        post['transkript'] = _relativ(str(tr)) if tr else None
        post['observation'] = sammanfatta(las_session(tr), slug) if tr else None
        ut.append(post)
    return ut


def tjanstesessioner(slug, efter=None):
    """Refero- och Mobbin-sessionerna (researchens tjänster, uppdragsmaterialet) ur deras strömmade loggar, från efter."""
    ut = []
    for f in sorted((UNDERLAG / slug / 'referenser').glob('**/session-*.jsonl')):
        try:
            if efter and time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(f.stat().st_mtime)) < efter:
                continue
        except OSError:
            continue
        rel = f.relative_to(UNDERLAG / slug)
        ut.append({'logg': str(rel), 'tjanst': f.parent.name, 'del': rel.parts[1] if len(rel.parts) > 2 else None,
                   'observation': sammanfatta(las_session(f), slug)})
    return ut


def referenser(slug):
    """Körningens referenspaket och kandidaternas huvudreferenser ur planen (det flödet erbjöd, inte det som lästes)."""
    a = UNDERLAG / slug / 'atelje'
    fo = bildkedja.las_json(a / 'FORSKNING.json') or {}
    plan = (bildkedja.las_json(a / 'KANDIDATPLAN.json') or {}).get('kandidater') or {}
    paket = (fo.get('nytt') or {}).get('paket') or (fo.get('fore') or {}).get('paket')
    pk = UNDERLAG / slug / 'referenser' / paket if paket else None
    return {'paket': paket, 'paket_tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(pk.stat().st_mtime)) if pk and pk.is_dir() else None,
            'tjanster_tid': (fo.get('nytt') or {}).get('tjanster'),
            'kandidater': {kid: {'huvudreferens': str(k.get('huvudreferens') or '')[:200], 'referensbilder': len(k.get('referensbilder') or [])}
                           for kid, k in plan.items() if isinstance(k, dict)} if isinstance(plan, dict) else {}}


def installerat(slug):
    """De installerade skillsen enligt körningens startkvitto (startkontrollen läste dem vid starten)."""
    kv = bildkedja.las_json(UNDERLAG / slug / 'atelje' / 'STARTKVITTO.json') or {}
    rader = [r for r in kv.get('rader') or [] if isinstance(r, dict) and r.get('typ') == 'skill']
    return {'tid': kv.get('tid'), 'antal': len(rader), 'namn': sorted(str(r.get('namn')) for r in rader)} if rader else None


def prototyper(slug):
    """Per kandidat: senaste förhandsvarvet under arbetet och den fotograferade versionen, åtskilda. Tiden är när
    skärmbilden fångades (filens tid)."""
    ut = {}
    for d in sorted((UNDERLAG / slug / 'atelje' / 'kandidater').glob('k[0-9][0-9]')):
        st = bildkedja.las_json(d / 'STATUS.json') or {}
        varv = sorted((p for p in (d / 'varv' / 'start').glob('varv-[0-9][0-9]') if p.is_dir()), key=lambda p: p.name)
        senaste, bilder, fangad = (varv[-1] if varv else None), {}, None
        for b in ('390', '1280', '1440'):
            p = senaste / ('vy-%s-forsta.png' % b) if senaste else None
            if p and p.is_file():
                bilder[b] = str(p.relative_to(ROOT))
                fangad = max(fangad or '', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(p.stat().st_mtime)))
        kv = st.get('kompetens') if isinstance(st.get('kompetens'), dict) else {}
        ut[d.name] = {'status': st.get('status'), 'skal': st.get('skal'), 'varv_antal': len(varv),
                      'varv': {'namn': senaste.name, 'skarmbild_fangad': fangad, 'bilder': bilder} if senaste else None,
                      'version': (st.get('version') or '')[:12] or None, 'fotograferad': st.get('fotograferad'),
                      'kompetenskvitton': [{'pass': n, 'verifierad': (p.get('kvitto') or {}).get('verifierad'),
                                            'lasta': len((p.get('kvitto') or {}).get('lasta') or []), 'saknas': (p.get('kvitto') or {}).get('saknas') or [],
                                            'genomford': p.get('genomford')} for n, p in kv.items() if isinstance(p, dict)]}
    return ut


def arbetslage(slug):
    """Körningens steg och tider ur statusfilen (sanningskällan); om arbetaren lever ur dess pid."""
    st = bildkedja.las_json(UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    return {'steg': st.get('steg'), 'startad': st.get('startad'), 'tider': st.get('tider') or {}, 'fel': st.get('fel'),
            'avslutad': st.get('steg') in AVSLUTADE, 'arbetaren_lever': bool(st.get('pid') and lever(st['pid']))}


def oversikt(slug):
    """Allt för dashboardens vy. En del som fallerar blir ofullständig med skälet; resten visas ändå."""
    ut = {'tid': nu(), 'pa': pa()}
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
