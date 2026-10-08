#!/usr/bin/env python3
"""Dashboard för nortropic-webb-pro. Lokal, läser repot och skriver bara ägarens domar.

    .venv/bin/python dashboard/server.py [--port 4771]     (eller ./dashboard.sh)

Visar byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag, körningens senaste händelser),
lärdomarna, kirurgens register och kommandona. Skriver bara när ägaren skickar frågeformuläret efter ett bygge:
kunder/<slug>/DOM.json (strukturerat, privat), underlag/LARDOMAR-original.md (ordagrant, privat) och en post utan
personuppgifter i LARDOMAR.md (i git): bara betygen och valen; lärdomen skriver sessionen som gör ändringen (BESLUT.md 2026-10-03).
Lyssnar bara på 127.0.0.1. POST kräver samma ursprung och dashboardnyckeln (NYCKEL; dashboard.sh öppnar sidan med den). Undantaget är visningen av en byggd sajt i telefonen: knappen
I telefonen startar en statisk server för kunder/<slug>/sajt/dist på datorns adress i det lokala nätverket och visar
den som QR-kod (dashboard/qr.py, ritad lokalt). Den servern visar bara sajten; --utan-lan stänger av den.
"""
import argparse
import hmac
import secrets
import hashlib
import html
import ipaddress
import socket
import json
import stat
import mimetypes
import os
import re
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
sys.path.insert(0, str(ROOT / 'kontroller'))
from prova import Server, dist_hash  # noqa: E402  (samma statiska server som provet använder; hashen binder A/B-valet)
import backlog as bl  # noqa: E402  (samma backlog-format som kirurgen och byggena skriver)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prospektvy as pv  # noqa: E402  (prospekten: kampanjer, kort, brev; heter inte prospekt eftersom kontroller/prospekt.py ligger först på sys.path)
import kallnyckel  # noqa: E402  (spanarens nyckel: är länken redan bedömd?)
import qr  # noqa: E402  (QR-koden till visningen i telefonen, ritad lokalt)

STEG = [
    ('Underlag', lambda s: (UNDERLAG / s / 'RESEARCH.md').is_file()),
    ('Diagnos', lambda s: (UNDERLAG / s / 'DIAGNOS.md').is_file()),
    ('Brief och referenser', lambda s: (UNDERLAG / s / 'BRIEF.md').is_file()),
    ('Innehåll', lambda s: (UNDERLAG / s / 'INNEHALL.md').is_file()),
    ('Bygge', lambda s: (KUNDER / s / 'sajt' / 'package.json').is_file()),
    ('Prov', lambda s: (KUNDER / s / 'prov' / 'STATUS.json').is_file()),
    ('Rapport', lambda s: (KUNDER / s / 'RAPPORT.md').is_file()),
    ('Dom', lambda s: (KUNDER / s / 'DOM.json').is_file()),
]

DIMENSIONER = ['Hållning', 'Typografi', 'Färg', 'Luft och hierarki', 'Substans', 'Förtroende', 'Mobil ergonomi', 'Konsekvens']

# Kärnfrågorna är desamma för varje bygge, så att svaren går att jämföra över tid (träningsdata).
KARNFRAGOR = [
    {'id': 'namn', 'fraga': 'Skulle du sätta ditt namn på sajten och visa den för verksamheten?', 'typ': 'val',
     'alternativ': ['Ja, som den är', 'Ja, efter små ändringar', 'Nej, inte utan större ändringar', 'Nej']},
    {'id': 'battre', 'fraga': 'Jämfört med verksamhetens nuvarande sajt är vår …', 'typ': 'val',
     'alternativ': ['Mycket bättre', 'Bättre', 'Ungefär lika', 'Sämre', 'Kan inte jämföra']},
    {'id': 'specifik', 'fraga': 'Känns den gjord för just den här verksamheten, eller som en mall?', 'typ': 'skala',
     'min': 'Mall', 'max': 'Bara de', 'steg': 5},
    {'id': 'mall_tecken', 'fraga': 'Om något känns som mall eller AI: peka på det. Var på sidan, och vad?', 'typ': 'fritext'},
    {'id': 'forsta_intryck', 'fraga': 'Efter fem sekunder på startsidan i telefonen (knappen I telefonen ger en QR-kod; svara på mobilfrågorna ur telefonen, inte ur en emulering): vad säger sajten till dig?', 'typ': 'fritext'},
    {'id': 'basta', 'fraga': 'Det bästa med sajten. Ett konkret ställe.', 'typ': 'fritext'},
    {'id': 'samsta', 'fraga': 'Det sämsta med sajten. Ett konkret ställe.', 'typ': 'fritext'},
    {'id': 'rost', 'fraga': 'Låter texten som verksamheten?', 'typ': 'val', 'alternativ': ['Ja', 'Delvis', 'Nej'],
     'foljd': 'Klistra gärna in en mening som inte håller.'},
    {'id': 'dimensioner', 'fraga': 'De åtta dimensionerna (kunskap/referenser-professionella.md)', 'typ': 'matris',
     'rader': DIMENSIONER, 'alternativ': ['Bra', 'Okej', 'Dålig']},
    {'id': 'referenser', 'fraga': 'Hur nära referenserna som bygget valde är den?', 'typ': 'skala', 'min': 'Långt ifrån', 'max': 'I nivå', 'steg': 5},
    {'id': 'referensval', 'fraga': 'Var referenserna rätt valda? Vilken skulle du ha valt i stället?', 'typ': 'fritext'},
    {'id': 'en_andring', 'fraga': 'Om du fick ändra en sak i hur vi bygger, vad skulle det vara?', 'typ': 'fritext'},
    {'id': 'sakerhet', 'fraga': 'Hur säker är du på din dom?', 'typ': 'val', 'alternativ': ['Säker', 'Ganska säker', 'Osäker']},
]
KARN_ID = {f['id'] for f in KARNFRAGOR}


def egna_fragor(slug):
    """Byggets egna frågor ur kunder/<slug>/FRAGOR.json: bara poster med eget id. Ett id som krockar med en kärnfråga skulle
    annars låta en fritextfråga skriva över ett fast svar som publiceras (omgång tolv, F37)."""
    egna = las_json(KUNDER / slug / 'FRAGOR.json')
    if not isinstance(egna, list):
        return []
    return [f for f in egna if isinstance(f, dict) and isinstance(f.get('id'), str) and f['id'] not in KARN_ID]


def publikt_varde(f, v):
    """Det fasta svaret om det är giltigt mot kärnfrågans alternativ, skala eller matris, annars None: bara sådana värden
    får stå i den publika LARDOMAR.md (omgång tolv, F37)."""
    typ = f.get('typ')
    if typ == 'val':
        return v if isinstance(v, str) and v in (f.get('alternativ') or []) else None
    if typ == 'skala':
        if isinstance(v, bool):
            return None
        try:
            n = int(v)
        except (TypeError, ValueError):
            return None
        return n if 1 <= n <= int(f.get('steg') or 5) else None
    if typ == 'matris':
        if not isinstance(v, dict) or not all(k in (f.get('rader') or []) and x in (f.get('alternativ') or []) for k, x in v.items() if x):
            return None
        return ', '.join('%s: %s' % (k, x) for k, x in v.items() if x) or None
    return None


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def minuter_sedan(startad):
    """Ägarens minuter från att vyn öppnades (vyns tidsstämpel, startad) till att domen sparades: autonomins mått
    (Codex helhetsbedömning 2026-10-04, punkt 9). None när tidsstämpeln saknas eller är orimlig (över ett dygn)."""
    try:
        t = datetime.fromisoformat(str(startad).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None
    if t.tzinfo is None:
        return None
    m = (datetime.now(timezone.utc) - t).total_seconds() / 60
    return round(m, 1) if 0 < m < 24 * 60 else None


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def las_text(p):
    try:
        return Path(p).read_text(encoding='utf-8')
    except OSError:
        return None


# --- markdown → html (det som repots egna filer använder; allt annat blir text) ---

def _inline(t):
    # quote=True: citattecken i en adress ska inte kunna stänga href-attributet (revisionen 2026-10-03, F2)
    t = html.escape(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\w)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r'(?<![">])(https?://[^\s<)]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    return t


def md(text):
    if not text:
        return ''
    ut, rader, i = [], text.splitlines(), 0
    while i < len(rader):
        r = rader[i]
        if r.startswith('```'):
            j = i + 1
            while j < len(rader) and not rader[j].startswith('```'):
                j += 1
            ut.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(rader[i + 1:j])))
            i = j + 1
            continue
        m = re.match(r'^(#{1,4})\s+(.*)', r)
        if m:
            n = len(m.group(1)) + 1
            ut.append('<h%d>%s</h%d>' % (n, _inline(m.group(2)), n))
            i += 1
            continue
        if r.startswith('|') and i + 1 < len(rader) and re.match(r'^\|[\s:|-]+\|?\s*$', rader[i + 1]):
            cell = lambda x: [c.strip() for c in x.strip().strip('|').split('|')]
            head = cell(r)
            j, body = i + 2, []
            while j < len(rader) and rader[j].startswith('|'):
                body.append(cell(rader[j]))
                j += 1
            ut.append('<div class="tabell"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                ''.join('<th>%s</th>' % _inline(c) for c in head),
                ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % _inline(c) for c in row) for row in body)))
            i = j
            continue
        if re.match(r'^\s*([-*]|\d+\.)\s+', r):
            ordnad = bool(re.match(r'^\s*\d+\.', r))
            items = []
            while i < len(rader) and (re.match(r'^\s*([-*]|\d+\.)\s+', rader[i]) or (re.match(r'^ {2,}\S', rader[i]) and items)):
                if re.match(r'^\s*([-*]|\d+\.)\s+', rader[i]):
                    items.append(re.sub(r'^\s*([-*]|\d+\.)\s+', '', rader[i]))
                else:
                    items[-1] += ' ' + rader[i].strip()
                i += 1
            tag = 'ol' if ordnad else 'ul'
            ut.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % _inline(x) for x in items), tag))
            continue
        if r.startswith('>'):
            j, q = i, []
            while j < len(rader) and rader[j].startswith('>'):
                q.append(rader[j].lstrip('> '))
                j += 1
            ut.append('<blockquote>%s</blockquote>' % _inline(' '.join(q)))
            i = j
            continue
        if not r.strip():
            i += 1
            continue
        j, p = i, []
        while j < len(rader) and rader[j].strip() and not re.match(r'^(#{1,4}\s|```|\||>|\s*([-*]|\d+\.)\s)', rader[j]):
            p.append(rader[j].strip())
            j += 1
        if not p:
            p, j = [r.strip()], i + 1
        ut.append('<p>%s</p>' % _inline(' '.join(p)))
        i = j
    return '\n'.join(ut)


# --- läsning av ett bygge ---

def siffror(katalog):
    """Lägsta mobilvärden ur lighthouse.json och allvarliga ur axe.json i en provkatalog."""
    lh = las_json(Path(katalog) / 'lighthouse' / 'lighthouse.json')
    ax = las_json(Path(katalog) / 'axe' / 'axe.json')
    ut = {}
    if lh and lh.get('rader'):
        mob = [r for r in lh['rader'] if r.get('form') == 'mobil'] or lh['rader']
        for k in ('prestanda', 'tillganglighet', 'bastaPraxis', 'seo'):
            ut[k] = min(r[k] for r in mob)
        ut['lcpMs'] = max(r.get('lcpMs', 0) for r in mob)
    if ax:
        ut['axe_allvarliga'] = ax.get('allvarliga')
    return ut


def bilder(slug):
    def lista(bas, monster):
        return sorted(str(p.relative_to(ROOT)) for p in bas.glob(monster)) if bas.is_dir() else []
    var = lista(KUNDER / slug / 'prov' / 'inspektion', '*/vy-*-forsta.png')
    deras = lista(UNDERLAG / slug / 'diagnos' / 'inspektion', 'vy-*-forsta.png')
    ref = lista(UNDERLAG / slug / 'referenser', '*/vy-*-forsta.png')
    return {'var': var, 'deras': deras, 'referenser': ref}


def korning(slug):
    loggar = sorted((KUNDER / slug).glob('korning-*.jsonl'))
    return las_logg(loggar[-1]) if loggar else None


def las_logg(logg):
    """En claude -p-logg i stream-json: modell, senaste handlingar, senaste text, resultat, om den pågår."""
    handlingar, text, resultat, start, modell = [], None, None, None, None
    try:
        for rad in logg.read_text(encoding='utf-8', errors='replace').splitlines():
            if not rad.startswith('{'):
                continue
            try:
                e = json.loads(rad)
            except ValueError:
                continue
            t = e.get('type')
            if t == 'system' and e.get('subtype') == 'init':
                start, modell = logg.stat().st_ctime, e.get('model')
            elif t == 'assistant':
                for c in (e.get('message') or {}).get('content', []):
                    if c.get('type') == 'tool_use':
                        inp = c.get('input') or {}
                        mal = inp.get('file_path') or inp.get('command') or inp.get('url') or inp.get('pattern') or inp.get('skill') or inp.get('subject') or inp.get('description') or ''
                        handlingar.append({'verktyg': c.get('name'), 'mal': str(mal).replace(str(ROOT) + '/', '')[:160]})
                    elif c.get('type') == 'text' and c.get('text', '').strip():
                        text = c['text'].strip()  # hela texten; dashboarden kapar inte
            elif t == 'result':
                resultat = {'utfall': e.get('subtype'), 'turer': e.get('num_turns'), 'minuter': round((e.get('duration_ms') or 0) / 60000, 1)}
                if isinstance(e.get('result'), str) and e['result'].strip():
                    text = e['result'].strip()  # slutsvaret, samlat i resultathändelsen
    except OSError:
        return None
    andrad = logg.stat().st_mtime
    return {'logg': str(logg.relative_to(ROOT)), 'modell': modell, 'pagar': resultat is None and time.time() - andrad < 900,
            'senast': datetime.fromtimestamp(andrad, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'antal_handlingar': len(handlingar), 'handlingar': handlingar[-12:][::-1], 'senaste_text': text, 'resultat': resultat}


def sammanfattning(slug):
    v = las_json(UNDERLAG / slug / 'VERKSAMHET.json') or {}
    s = las_json(KUNDER / slug / 'prov' / 'STATUS.json')
    k = korning(slug)
    steg = [{'namn': n, 'klar': bool(f(slug))} for n, f in STEG]
    sv = las_json(KUNDER / slug / 'prov' / 'STOPPVAKT.json') or {}
    return {
        'slug': slug, 'namn': v.get('namn') or slug,
        # avslutat är inte godkänt: stoppvakten släpper vid sitt tak också utan godkänd granskning (ägarfråga 2 i revisionen)
        # en avstängd granskning skriver samma prefix som en godkänd (stoppvakten); fältet granskning avgör (GR-20261008-r117-claude#C8);
        # ett äldre besked utan fältet läses som förut
        'slappt_utan_godkannande': bool(sv.get('slapp')) and not (str(sv.get('skal') or '').startswith('kontrollerna gröna')
                                                                  and sv.get('granskning') in (None, 'godkänd')),
        'ort': ', '.join(((v.get('rackvidd') or {}).get('orter') or [])[:2]) or ((v.get('adress') or {}).get('ort') or ''),
        'doman': (v.get('webb') or {}).get('doman') if isinstance(v.get('webb'), dict) else None,
        'steg': steg, 'steg_klara': sum(x['klar'] for x in steg),
        'prov': {'ok': s.get('ok'), 'tid': s.get('tid'), 'snabb': s.get('snabb'),
                 'grindar': {n: g['ok'] for n, g in s.get('grindar', {}).items()}} if s else None,
        'pagar': bool(k and k['pagar']), 'domd': (KUNDER / slug / 'DOM.json').is_file(),
    }


def byggen():
    if not KUNDER.is_dir():
        return []
    # rokprov-* är kontrollernas regressionsfixtur (kontroller/rokprov.sh), inget bygge att döma
    ut = [sammanfattning(p.name) for p in KUNDER.iterdir() if p.is_dir() and SLUG.match(p.name) and not p.name.startswith('rokprov') and p.name != 'ab']
    return sorted(ut, key=lambda b: (not b['pagar'], b['domd'], b['slug']))


def ab_oavgjord(slug):
    """Är bygget en arm i en jämförelse som ägaren inte har valt i än? Då döljs allt som kan avslöja armen: koncept och
    underlag (ateljévägen skriver sig själv i KONCEPT.md), rapporten, provets text, körningens händelser och byggets
    egna frågor (riktningsfrågan bär ateljéns bilder)."""
    if not (KUNDER / slug / 'AB-SYSKON').is_file() or not AB.is_dir():
        return False
    return any(slug in (p.get('byggen') or []) and p.get('val') is None for p in (las_json(f) or {} for f in AB.glob('ab-*.json')))


def bygge(slug):
    b = sammanfattning(slug)
    s = las_json(KUNDER / slug / 'prov' / 'STATUS.json')
    egna = egna_fragor(slug)
    b.update({
        'status': s, 'stoppvakt': las_json(KUNDER / slug / 'prov' / 'STOPPVAKT.json'),
        'fore': siffror(UNDERLAG / slug / 'diagnos'), 'efter': siffror(KUNDER / slug / 'prov'),
        'bilder': bilder(slug), 'korning': korning(slug),
        'rapport': md(las_text(KUNDER / slug / 'RAPPORT.md')),
        'prov_md': md(las_text(KUNDER / slug / 'prov' / 'PROV.md')),
        'underlag': {namn: md(las_text(UNDERLAG / slug / fil)) for namn, fil in (
            ('Brief', 'BRIEF.md'), ('Referenser', 'REFERENSER.md'), ('Jämförelse', 'JAMFORELSE.md'),
            ('Femsekunderstest', 'FEMSEK.md'), ('Diagnos', 'DIAGNOS.md'), ('Research', 'RESEARCH.md'),
            ('Koncept', 'KONCEPT.md'), ('Innehåll', 'INNEHALL.md'), ('Beställning till verksamheten', 'BESTALLNING.md')) if (UNDERLAG / slug / fil).is_file()},
        'fragor': {'karna': KARNFRAGOR, 'egna': egna},
        'domar': (las_json(KUNDER / slug / 'DOM.json') or {}).get('domar', []),
        'granskning': granskningen(slug, b['domd']),
    })
    if ab_oavgjord(slug):
        dolt = '<p>Dolt tills du har valt i Jämförelser, så att jämförelsen förblir blind.</p>'
        # också byggets egna frågor: ateljéarmens riktningsfråga visar bilder ur atelje/ och avslöjar armen
        b.update({'ab_dold': True, 'rapport': dolt, 'prov_md': dolt, 'underlag': {'Dolt': dolt}, 'korning': None,
                  'fragor': {'karna': KARNFRAGOR, 'egna': []}, 'stoppvakt': None, 'status': None,
                  'bilder': dict(b['bilder'], deras=[], referenser=[])})
    return b


def kandidatkorning(slug, st):
    """Kandidatflödet känns igen på statusens flagga eller på ateljén själv (atelje.kandidatkorning, granskning 2, N1)."""
    r = UNDERLAG / slug / 'atelje'
    return bool(st.get('kandidatflode')) or (r / 'KANDIDATPLAN.json').is_file() or (r / 'kandidater').is_dir()


_NAMN = {}  # katalogernas namn, så länge katalogen är oförändrad: (sökväg, inod, ändringstid) -> (mängd, lista)


def _namn_i(kat):
    """Namnen i katalogen kat, som den bär dem. En katalog som får, tappar eller byter namn på något får en ny
    ändringstid, så en lista ur cachen gäller bara samma katalog i samma läge."""
    try:
        st_ = os.stat(kat)
    except OSError:
        return set(), []
    nyckel = (kat, st_.st_dev, st_.st_ino, st_.st_mtime_ns)
    namn = _NAMN.get(nyckel)
    if namn is None:
        try:
            lista = os.listdir(kat)
        except OSError:
            return set(), []
        if len(_NAMN) > 4096:
            _NAMN.clear()
        namn = _NAMN[nyckel] = (set(lista), lista)
    return namn


def _verklig(rot, rest):
    """Sökvägen rest under katalogen rot som filsystemet ser den: (sökvägen relativt rot, den verkliga filen eller None
    när den inte finns). Symlänkar, '.', '..' och '//' löses som realpath löser dem, och varje befintligt led får det namn
    som katalogen själv bär, eftersom APFS inte skiljer på skiftläge eller Unicode-form (realpath behåller ATELJE när
    katalogen heter atelje). Ett led som inte finns behåller sin form. None när sökvägen hamnar utanför rot eller inte går
    att tolka, som med ett nollbyte (granskningen av r99, BÖR-1–3)."""
    import unicodedata
    try:
        bas = os.path.realpath(rot)
        verklig = os.path.realpath(os.path.join(bas, rest))
    except (TypeError, ValueError, OSError):
        return None
    if not verklig.startswith(bas.rstrip(os.sep) + os.sep):
        return None
    kat, ut, finns = bas, [], True
    for d in verklig[len(bas.rstrip(os.sep)) + 1:].split(os.sep):
        if finns:
            mangd, namn = _namn_i(kat)
            if d not in mangd:
                nyckel = unicodedata.normalize('NFC', d).casefold()
                lika = [n for n in namn if unicodedata.normalize('NFC', n).casefold() == nyckel]
                finns = len(lika) == 1
                d = lika[0] if finns else d
        ut.append(d)
        kat = os.path.join(kat, d)
    return '/'.join(ut), (Path(kat) if finns and os.path.lexists(kat) else None)


def _kanonisk(rel):
    """'underlag/…' eller 'kunder/…' som den verkliga filen (_verklig, relativt underlag/ och kunder/ som de är på disken):
    (sökvägen, filen eller None), eller None när sökvägen inte börjar så eller hamnar utanför."""
    if not isinstance(rel, str):
        return None
    forsta, _, rest = rel.partition('/')
    rot = {'underlag': UNDERLAG, 'kunder': KUNDER}.get(forsta)
    v = _verklig(rot, rest) if rot is not None and rest else None
    return (forsta + '/' + v[0], v[1]) if v and v[0] else None


def _ett_namn(p):
    """Har filen ett enda namn? En hård länk syns inte på sökvägen, så en fil med flera namn kan vara en dold fil under ett
    annat namn; den visas inte. En katalog och en fil som inte finns prövas inte här. Inget verktyg i repot skapar hårda
    länkar (granskningen av r99)."""
    try:
        st_ = os.stat(p)
    except (OSError, ValueError):
        return True
    return not stat.S_ISREG(st_.st_mode) or st_.st_nlink == 1


def fil_tillaten(rel):
    """/fil/<rel>: aldrig jämförelsernas facit (kunder/ab/), och för en arm som ägaren inte valt i än bara provets
    skärmbilder, som den blinda jämförelsen behöver (revisionen 2026-10-03, F14). Prövas på den verkliga filen
    (_kanonisk), så att ./, //, .., en symlänk eller ett annat skiftläge (ATELJE) inte tar sig förbi prefixen nedan
    (granskningen av r99, BÖR-3), och en fil med flera hårda länkar visas inte (_ett_namn)."""
    k = _kanonisk(rel)
    return bool(k) and _tillaten(k[0]) and (k[1] is None or _ett_namn(k[1]))


def _tillaten(rel):
    """fil_tillaten för en sökväg som redan är den verkliga filens (_kanonisk)."""
    delar = rel.split('/')
    if len(delar) < 3 or delar[1] == 'ab':
        return False
    slug = delar[1]
    if not SLUG.match(slug):
        return False
    if ab_oavgjord(slug):
        return delar[0] == 'kunder' and rel.startswith('kunder/%s/prov/inspektion/' % slug) and rel.endswith('.png')
    if slug == 'kalibrering':  # bara skärmbilderna: URVAL.txt bär hypoteserna och DOMAR.json domarna (F40)
        return bool(KAL_FIL.match(rel))
    if rel.startswith('underlag/%s/atelje/foregaende/' % slug):
        return False  # tidigare ateljékörningar: arkiv, inget dashboarden visar (deras panelers domar döljs)
    if rel.startswith('underlag/%s/atelje/' % slug) and kandidatkorning(slug, las_json(UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}):
        import kandidater
        if not kandidater.domd(slug):  # före ägarens första beslut: bara skärmbilderna (granskningen M1)
            return bool(KAND_FIL.match(rel) or KAND_VARV.match(rel))
    if rel.startswith('underlag/%s/atelje/kandidater/' % slug):
        # kandidatflödet: skärmbilderna är det ägaren bedömer; skaparens korta redovisning ger API:t från början, och
        # granskningen, hela anteckningarna och koden när ägaren har fattat sitt första beslut (kandidater.sammanstall)
        return bool(KAND_FIL.match(rel) or KAND_VARV.match(rel))
    if rel.startswith('underlag/%s/atelje/' % slug):
        # designprovet: bara förslagens bilder tills ägaren dömt alla förslag i omgången (panelens dom döljs per omgång)
        runda = DP_RUNDA.match(delar[3]) if len(delar) > 4 else None
        kat = UNDERLAG / slug / 'atelje' / (delar[3] if runda else '')
        if not designprov_domt(slug, kat if runda else None):
            return bool(DP_FIL.match(rel))
    return True


def granskningen(slug, domd):
    """Granskarens dom visas först när ägaren har dömt bygget, så att ägarens dom är oberoende och kan jämföras."""
    gdir = KUNDER / slug / 'granskning'
    g = las_json(gdir / 'GRANSKNING.json')
    if not g:
        return {'finns': False}
    if not domd:
        return {'finns': True, 'dold': True, 'rundor': len(list(gdir.glob('runda-*')))}
    return {'finns': True, 'dold': False, 'godkand': g.get('godkand'), 'runda': g.get('runda'),
            'rundor': len(list(gdir.glob('runda-*'))), 'html': md(las_text(gdir / 'GRANSKNING.md'))}


AGARENS_NIVA = {'Ja, som den är': 0, 'Ja, efter små ändringar': 1, 'Nej, inte utan större ändringar': 2, 'Nej': 2}
GRANSKARENS_NIVA = ('godkände', 'krävde detaljrättning', 'krävde ny riktning')


def granskare_overens():
    """Per dömt och granskat bygge, i tre nivåer: granskaren godkänd / detaljrättning / ny riktning mot ägarens
    som den är / efter små ändringar / inte utan större ändringar. Äldre granskningar utan omfattning jämförs bara på
    om sajten kan visas som den är."""
    rader = []
    for p in sorted(KUNDER.iterdir()) if KUNDER.is_dir() else []:
        dom = (las_json(p / 'DOM.json') or {}).get('domar') or []
        g = las_json(p / 'granskning' / 'GRANSKNING.json')
        namn = (dom[-1].get('svar') or {}).get('namn') if dom else None
        if not (g and namn in AGARENS_NIVA):
            continue
        an = AGARENS_NIVA[namn]
        gn = g.get('niva')
        if gn is None:
            overens = bool(g.get('godkand')) == (an == 0)
            gtext = 'godkände' if g.get('godkand') else 'underkände'
        else:
            overens, gtext = gn == an, GRANSKARENS_NIVA[gn]
        sep = g.get('originalitet_separat') if isinstance(g.get('originalitet_separat'), dict) else {}
        orig = (g.get('originalitet_huvud') or (g.get('kriterier') or {}).get('originalitet') or {}).get('betyg')
        rader.append({'slug': p.name, 'granskaren': gtext, 'agarens_svar': namn, 'overens': overens,
                      'originalitet': orig, 'originalitet_separat': sep.get('betyg'),
                      'agarens_specifik': (dom[-1].get('svar') or {}).get('specifik')})
    return {'bedomda': len(rader), 'overens': sum(r['overens'] for r in rader), 'rader': rader}


OMDOMEN = ROOT / 'kunskap' / 'KIRURG-OMDOMEN.md'
DOMKLASSER = ('ta in', 'prova', 'parkera', 'nej')


def domklass(text):
    t = (text or '').lower()
    for k in DOMKLASSER:
        if t.startswith(k) or (k == 'prova' and 'prova' in t):
            return k
    return 'okänd'


def omdomen():
    """Ägarens överprövningar av kirurgens domar, ur kunskap/KIRURG-OMDOMEN.md, per registerrubrik (senaste gäller)."""
    ut = {}
    for d in (las_text(OMDOMEN) or '').split('\n### ')[1:]:
        rubrik, _, kropp = d.partition('\n')
        rubrik = rubrik.split(' · ', 1)[1] if ' · ' in rubrik else rubrik
        f = dict(re.findall(r'^- ([^:]+): (.*)$', kropp, re.M))
        ut[rubrik.strip()] = {'kirurgen': f.get('Kirurgens dom', ''), 'agaren': f.get('Ägarens dom', ''), 'ord': f.get('Ägarens ord', '').strip('"')}
    return ut


def register():
    text = las_text(ROOT / 'kunskap' / 'REGISTER.md') or ''
    delar = text.split('\n### ')[1:]
    poster, om = [], omdomen()
    for d in delar:
        rubrik, _, kropp = d.partition('\n')
        bitar = [x.strip() for x in rubrik.split('·')]
        poster.append({'rubrik': rubrik.strip(), 'datum': bitar[0] if bitar else '', 'namn': bitar[1] if len(bitar) > 1 else rubrik,
                       'dom': bitar[2] if len(bitar) > 2 else '', 'html': md(kropp), 'ersatt': '- Ersatt av:' in kropp,
                       'omdome': om.get(rubrik.strip())})
    return poster[::-1]


def overensstammelse():
    """Hur ofta ägaren håller med kirurgen, per kirurgens domklass (forskningens råd: inte bara total andel)."""
    per = {}
    for o in omdomen().values():
        k = domklass(o['kirurgen'])
        r = per.setdefault(k, {'bedomda': 0, 'haller_med': 0})
        r['bedomda'] += 1
        r['haller_med'] += o['agaren'].lower().startswith('håller med')
    tot = sum(r['bedomda'] for r in per.values())
    return {'bedomda': tot, 'haller_med': sum(r['haller_med'] for r in per.values()), 'per_dom': per}


def spara_omdome(data):
    """Ägaren överprövar en registerpost. Skrivs i kunskap/KIRURG-OMDOMEN.md, committas och pushas (ägarens egna ord)."""
    import subprocess
    rubrik = (data.get('rubrik') or '').strip()
    agaren = (data.get('agaren') or '').strip()
    if not rubrik or rubrik not in {p['rubrik'] for p in register()}:
        raise ValueError('okänd registerpost')
    if agaren != 'håller med' and agaren not in DOMKLASSER:
        raise ValueError('välj håller med, eller vilken dom det borde ha blivit')
    ord_ = (data.get('ord') or '').strip().replace('\n', ' ')[:3000]
    kirurgen = rubrik.split('·')[-1].strip()
    if not OMDOMEN.is_file():
        OMDOMEN.write_text('# Ägarens omdömen om kirurgens domar\n\nKalibrering: varje post är ägarens överprövning av en registerpost. '
                           'Kirurgen läser dem före varje intag; där ägaren inte höll med är de viktigaste exemplen.\n', encoding='utf-8')
    post = '\n### %s · %s\n- Kirurgens dom: %s\n- Ägarens dom: %s\n- Ägarens ord: "%s"\n' % (
        nu()[:10], rubrik, kirurgen, 'håller med' if agaren == 'håller med' else 'håller inte med, borde ha blivit: ' + agaren, ord_)
    with open(OMDOMEN, 'a', encoding='utf-8') as f:
        f.write(post)
    return {'sparad': True, 'git': commit_agarens(['kunskap/KIRURG-OMDOMEN.md'], 'Ägaren: omdöme om kirurgens dom (%s)' % rubrik.split('·')[1].strip()[:60])}


def commit_agarens(filer, meddelande):
    """Ägarens egna ord (domar, omdömen) committas och pushas direkt, så att de inte går förlorade."""
    import subprocess
    g = lambda *a: subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True, timeout=60)
    if g('add', *filer).returncode or g('commit', '-q', '-m', meddelande, '--', *filer).returncode:
        return 'kunde inte committa'
    p = g('push', '-q', 'origin', 'main')
    return 'committad och pushad' if p.returncode == 0 else 'committad lokalt; push misslyckades: ' + (p.stderr or '').strip()[-160:]


def lardomar_original():
    """Ägarens domar ordagrant, privat under underlag/ (utanför git). Den publika LARDOMAR.md får bara betyg, val och
    lärdomar utan personuppgifter (ägarens beslut 2026-10-03, BESLUT.md)."""
    return UNDERLAG / 'LARDOMAR-original.md'


def skriv_original(rader):
    """Lägger en post sist i den privata filen; skapar den med ingress om den saknas."""
    f = lardomar_original()
    if not f.is_file():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('# Lärdomar — ägarens domar, ordagrant (privat)\n\nUnder underlag/, utanför git: varje dom som ägaren skrev den. Den '
                     'publika LARDOMAR.md har samma poster utan personuppgifter (ägarens beslut 2026-10-03, BESLUT.md).\n', encoding='utf-8')
        try:
            f.chmod(0o600)
        except OSError:
            pass
    with open(f, 'a', encoding='utf-8') as fh:
        fh.write('\n'.join(rader))


# --- A/B-jämförelser (kontroller/ab.py) ---

AB = KUNDER / 'ab'


def ab_lista():
    """Jämförelserna, med värdena och mätningarna dolda tills ägaren har valt (blint, parvis)."""
    ut = []
    for f in sorted(AB.glob('ab-*.json'), reverse=True) if AB.is_dir() else []:
        p = las_json(f) or {}
        visa_svar = p.get('val') is not None
        byggen = []
        for i, slug in enumerate(p.get('byggen', [])):
            b = {'slug': slug, 'etikett': 'AB'[i], 'bilder': [str(x.relative_to(ROOT)) for x in
                 [KUNDER / slug / 'prov' / 'inspektion' / 'hem' / v for v in ('vy-390-forsta.png', 'vy-1440-forsta.png')] if x.is_file()],
                 'byggd': (KUNDER / slug / 'sajt' / 'dist' / 'index.html').is_file()}
            if visa_svar:
                b['varde'] = (p.get('varden') or {}).get(slug)
                b['matt'] = (p.get('korningar') or {}).get(slug)
            byggen.append(b)
        ut.append({'id': p.get('id'), 'verksamhet': p.get('verksamhet'), 'variabel': p.get('variabel'), 'status': p.get('status'),
                   'val': p.get('val'), 'kommentar': p.get('kommentar'), 'byggen': byggen, 'klar': ab_klar(p)})
    return ut


def ab_klar(p):
    """Båda körningarna avslutade (ab.py skriver korningar per arm och klar sist); valet får inte göras förrän dess."""
    return bool(p.get('klar')) and all(s in (p.get('korningar') or {}) for s in p.get('byggen') or [])


def spara_ab(ident, data):
    f = AB / (ident + '.json')
    p = las_json(f) if re.fullmatch(r'ab-[a-z0-9-]+-\d{8}T\d{6}Z', ident or '') else None
    if not p:
        raise ValueError('okänd jämförelse')
    if p.get('val') is not None:
        raise ValueError('redan vald')
    if not ab_klar(p):
        raise ValueError('båda byggena måste vara avslutade innan du väljer; granskning och rättningar kan fortfarande pågå')
    val = data.get('val')
    if val not in p['byggen'] + ['lika', 'ingen']:  # ingen: ingen arm når ägarens ribba (Codex 2026-10-05, ordning 3)
        raise ValueError('välj A, B, lika eller ingen når min ribba')
    for s in p['byggen']:  # valet gäller exakt de byggen som blev klara (revisionen 2026-10-03, F15)
        sparad = (p.get('korningar') or {}).get(s, {}).get('dist_sha256')
        d = KUNDER / s / 'sajt' / 'dist'
        if not sparad:
            raise ValueError('jämförelsen saknar byggets hash för %s och kan inte verifieras; en äldre jämförelse får hashen med '
                             '.venv/bin/python kontroller/ab.py hash %s' % (s, p.get('id')))
        if not d.is_dir() or dist_hash(d) != sparad:
            raise ValueError('bygget %s har ändrats sedan jämförelsen blev klar; kör inte vidare i armarna efter kedjan' % s)
    p.update(val=val, kommentar=(data.get('kommentar') or '').strip()[:4000], valt=nu(), status='vald')
    f.write_text(json.dumps(p, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    etikett = {s: 'AB'[i] for i, s in enumerate(p['byggen'])}
    rader = ['', '## AB · %s · %s: %s' % (p['valt'][:10], p['variabel'], ' mot '.join('%s=%s' % (etikett[s], p['varden'][s]) for s in p['byggen'])), '',
             '- **Byggen:** %s' % ', '.join(p['byggen']),  # granskaren filtrerar bort avsnittet för dessa byggen (granska.lardomar_utan)
             '- **Ägarens val (blint):** %s' % ({'lika': 'lika', 'ingen': 'ingen når min ribba'}.get(val) or '%s (%s=%s)' % (etikett[val], p['variabel'], p['varden'][val])),
             *(['- **Ägarens ord:** ' + p['kommentar'].replace('\n', ' / ')] if p['kommentar'] else []),
             *['- %s (%s=%s): %s' % (etikett[s], p['variabel'], p['varden'][s], json.dumps((p.get('korningar') or {}).get(s, {}), ensure_ascii=False))
               for s in p['byggen']], '']
    skriv_original(rader)  # ordagrant, privat (BESLUT.md 2026-10-03)
    publika = [r if not r.startswith('- **Ägarens ord:**') else '- **Ägarens ord:** ordagrant i `underlag/LARDOMAR-original.md` (privat)' for r in rader]
    with open(ROOT / 'LARDOMAR.md', 'a', encoding='utf-8') as fh:
        fh.write('\n'.join(publika))
    return {'ok': True, 'git': commit_agarens(['LARDOMAR.md'], 'Ägaren: A/B %s' % p['variabel']), 'jamforelse': ab_lista()}


# --- kalibreringen: ägaren dömer externa exempel blint (backlogposten om kalibrering av visuell nivå, 2026-10-03) ---
NIVAER = ('over', 'nastan', 'generisk')
KAL_LAS = threading.Lock()
KAL_FIL = re.compile(r'^underlag/kalibrering/K\d{2}/(start|undersida)/vy-(390|1440)-(forsta|hela|ruta-\d{2})\.png$')


def kalibrering_urval():
    """Exemplen ur underlag/kalibrering/URVAL.txt: id · nivå (agentens hypotes) · adress · roll. Adress och hypotes visas
    för ägaren först efter domen, så att bedömningen är blind."""
    f = UNDERLAG / 'kalibrering' / 'URVAL.txt'
    ut = []
    for rad in (las_text(f) or '').splitlines():
        if not rad.strip() or rad.startswith('#'):
            continue
        delar = [d.strip() for d in rad.split('·')]
        if len(delar) < 3 or not re.fullmatch(r'K\d{2}', delar[0]):
            continue
        ut.append({'id': delar[0], 'hypotes': delar[1], 'url': delar[2], 'roll': delar[3] if len(delar) > 3 else ''})
    return ut


def kalibrering_lista():
    domar = las_json(UNDERLAG / 'kalibrering' / 'DOMAR.json') or {}
    ut = []
    for e in kalibrering_urval():
        bas = UNDERLAG / 'kalibrering' / e['id']
        bilder = {}
        for mapp in ('start', 'undersida'):
            for fil in ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png'):
                if (bas / mapp / fil).is_file():
                    bilder['%s-%s' % (mapp, fil[3:-4])] = 'underlag/kalibrering/%s/%s/%s' % (e['id'], mapp, fil)
        post = {'id': e['id'], 'bilder': bilder, 'dom': domar.get(e['id'])}
        if post['dom']:  # avslöjas efter domen
            post.update(url=e['url'], roll=e['roll'], hypotes=e['hypotes'])
        ut.append(post)
    return ut


def spara_kalibrering(ident, data):
    """Ägarens dom över ett exempel: nivå och vad som skiljer. Privat (underlag/kalibrering/DOMAR.json), ingen git."""
    if ident not in {e['id'] for e in kalibrering_urval()}:
        raise ValueError('okänt exempel')
    if data.get('niva') not in NIVAER:
        raise ValueError('välj tydligt över ribban, nästan eller generisk')
    import fcntl
    f = UNDERLAG / 'kalibrering' / 'DOMAR.json'
    f.parent.mkdir(parents=True, exist_ok=True)
    with KAL_LAS, open(f.parent / '.domar.las', 'w') as las:  # läs–ändra–skriv under lås, strikt läsning, atomiskt byte (F39)
        fcntl.flock(las, fcntl.LOCK_EX)
        try:
            domar = {}
            if f.exists():
                try:
                    domar = json.loads(f.read_text(encoding='utf-8'))
                except (OSError, ValueError) as e:
                    raise RuntimeError('DOMAR.json går inte att läsa (%s); rätta filen innan en dom sparas, så att ingen dom skrivs över' % e)
                if not isinstance(domar, dict):
                    raise RuntimeError('DOMAR.json är inte ett objekt; rätta filen innan en dom sparas')
            domar[ident] = {'niva': data['niva'], 'skiljer': (data.get('skiljer') or '').strip()[:4000], 'tid': nu()}
            tmp = f.with_name('.DOMAR.json.tmp%d' % os.getpid())
            tmp.write_text(json.dumps(domar, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            os.replace(tmp, f)
        finally:
            fcntl.flock(las, fcntl.LOCK_UN)
    return {'ok': True, 'dom': domar[ident], 'kvar': sum(1 for e in kalibrering_urval() if e['id'] not in domar)}


# --- designprovet: ägaren dömer ateljéns förslag blint, bredvid huvudreferensen (designprovet, ägarbeslut 2026-10-04) ---
DP_LAS = threading.Lock()
DP_FIL = re.compile(r'^underlag/([a-z0-9-]{2,60})/atelje/(omgang-\d{1,2}/)?(\d|vinnare/bilder|slutdom/[12])/(undersida/|stiltavla/)?vy-(390|1440)-(forsta|hela|ruta-\d{2})\.png$')
DP_RUNDA = re.compile(r'^omgang-(\d{1,2})$')
DP_REF = re.compile(r'^underlag/([a-z0-9-]{2,60})/referenser/[A-Za-z0-9._/-]+\.(png|jpe?g|webp)$')


def designprov_slugar():
    """Byggen med en fotograferad ateljéomgång (underlag/<slug>/atelje/FOTOGRAFERADE.json eller atelje/omgang-N/)."""
    rotter = list(UNDERLAG.glob('*/atelje/FOTOGRAFERADE.json')) + list(UNDERLAG.glob('*/atelje/omgang-*/FOTOGRAFERADE.json'))
    slugar = {(p.parents[1] if p.parent.name == 'atelje' else p.parents[2]).name for p in rotter}
    return sorted(s_ for s_ in slugar if SLUG.match(s_))


def designprov_rundor(slug):
    """Ateljékörningens fotograferade omgångar, äldst först: [(id, nummer, katalog, aktuell)]. Ateljén flyttar en
    förkastad omgång till atelje/omgang-N/ och kör nästa i roten; ägaren dömer varje omgång för sig, och domen följer
    omgångens katalog. Rotens nummer är ett mer än den högsta arkiverade, så att bokstäverna består när den arkiveras."""
    rot = UNDERLAG / slug / 'atelje'
    arkiv = []
    for p in rot.glob('omgang-*'):
        m = DP_RUNDA.match(p.name)
        if m and p.is_dir() and not p.is_symlink() and (p / 'FOTOGRAFERADE.json').is_file():
            arkiv.append((p.name, int(m.group(1)), p, False))
    arkiv.sort(key=lambda x: x[1])
    if (rot / 'FOTOGRAFERADE.json').is_file():
        nr = max([x[1] for x in arkiv] or [0]) + 1
        arkiv.append(('omgang-%d' % nr, nr, rot, True))
    return arkiv


def designprov_runda(slug, ident=None):
    """En omgång: ident None är den aktuella i roten, annars 'omgang-N'."""
    for r in designprov_rundor(slug):
        if (ident is None and r[3]) or (ident is not None and r[0] == ident):
            return r
    return None


def designprov_ordning(slug, riktningar, nummer=1):
    """Blind ordning: stabil per bygge och omgång, oberoende av riktningsnumren (A, B, C …); omgångens nummer i nyckeln
    gör att en avslöjad omgång inte avslöjar nästa."""
    import hashlib
    return sorted(riktningar, key=lambda n: hashlib.sha256(('designprov-%s-omgang-%d-%d' % (slug, nummer, n)).encode()).hexdigest())


def designprov_domt(slug, katalog=None):
    """Har ägaren dömt alla förslag i omgången (standard: den aktuella i roten)? Utan fotograferad omgång finns inget
    att dölja."""
    rot = katalog or (UNDERLAG / slug / 'atelje')
    manifest = las_json(rot / 'FOTOGRAFERADE.json') or {}
    riktningar = [n for n in (manifest.get('riktningar') or {}) if str(n).isdigit()]
    if not riktningar:
        return True
    domar = las_json(rot / 'AGARENS-DOM.json') or {}
    return all(b in domar for b in 'ABCDE'[:len(riktningar)])


def designprov_omgang(slug, ident, nummer, kat, aktuell):
    """En omgångs förslag under bokstäver, med startsidans första vy och helsida i båda bredderna och undersidans början.
    Vilken riktning en bokstav är, och panelens dom, visas först när ägaren dömt alla förslag i omgången."""
    manifest = las_json(kat / 'FOTOGRAFERADE.json') or {}
    riktningar = sorted(int(n) for n in (manifest.get('riktningar') or {}) if str(n).isdigit())
    domar = las_json(kat / 'AGARENS-DOM.json') or {}
    prefix = 'underlag/%s/atelje/%s' % (slug, '' if aktuell else ident + '/')
    ordning = designprov_ordning(slug, riktningar, nummer)
    forslag = []
    for b, n in zip('ABCDE', ordning):
        bilder = {}
        for namn, fil in (('390-forsta', 'vy-390-forsta.png'), ('1440-forsta', 'vy-1440-forsta.png'), ('390-hela', 'vy-390-hela.png'),
                          ('1440-hela', 'vy-1440-hela.png'), ('undersida-390', 'undersida/vy-390-forsta.png'), ('undersida-1440', 'undersida/vy-1440-forsta.png')):
            if (kat / str(n) / fil).is_file():
                bilder[namn] = '%s%d/%s' % (prefix, n, fil)
        forslag.append({'bokstav': b, 'bilder': bilder, 'dom': domar.get(b)})
    ut = {'id': ident, 'nummer': nummer, 'aktuell': aktuell, 'forslag': forslag}
    if forslag and all(f['dom'] for f in forslag):
        val = las_json(kat / 'VAL.json') or {}
        ut['avslojat'] = {'karta': {b: n for b, n in zip('ABCDE', ordning)}, 'panel_saknas': not (kat / 'VAL.json').is_file(),
                          'panelens_val': val.get('val'), 'ribban': val.get('ribban'), 'nivaer': val.get('nivaer'), 'poang': val.get('poang'),
                          'val_md': md(las_text(kat / 'VAL.md') or '')}
    return ut


def designprov(slug):
    """Ateljékörningens omgångar (äldst först) och huvudreferensens bilder. forslag och avslojat på toppnivån är den
    aktuella omgången, som förut; rundor har alla, också de som panelen förkastade och ateljén arkiverade."""
    import referensval
    rundor = [designprov_omgang(slug, *r) for r in designprov_rundor(slug)]
    aktuell = next((r for r in rundor if r['aktuell']), None)
    hr = referensval.huvudreferens(slug, UNDERLAG)
    svar = {'slug': slug, 'forslag': aktuell['forslag'] if aktuell else [], 'rundor': rundor,
            'huvudreferens': {'namn': hr['namn'], 'vad': hr['vad'], 'bilder': [{'fil': str(p.relative_to(ROOT)), 'text': t} for p, t in hr['bilder']]} if hr else None}
    if aktuell and aktuell.get('avslojat'):
        svar['avslojat'] = aktuell['avslojat']
    return svar


def spara_designprov(slug, bokstav, data, omgang=None, minuter=None):
    """Ägarens dom över ett förslag: håller ribban, nivå och vad som skiljer. Privat, i omgångens katalog
    (underlag/<slug>/atelje/AGARENS-DOM.json för den aktuella, atelje/omgang-N/AGARENS-DOM.json för en arkiverad)."""
    import fcntl
    if slug not in designprov_slugar():
        raise ValueError('okänt designprov')
    runda = designprov_runda(slug, omgang)
    if not runda:
        raise ValueError('okänd omgång')
    if bokstav not in {f['bokstav'] for f in designprov_omgang(slug, *runda)['forslag']}:
        raise ValueError('okänt förslag')
    if data.get('niva') not in NIVAER or not isinstance(data.get('haller'), bool):
        raise ValueError('välj nivå och om förslaget håller ribban')
    f = runda[2] / 'AGARENS-DOM.json'
    with DP_LAS, open(f.parent / '.agarens-dom.las', 'w') as las:
        fcntl.flock(las, fcntl.LOCK_EX)
        try:
            domar = {}
            if f.exists():
                try:
                    domar = json.loads(f.read_text(encoding='utf-8'))
                except (OSError, ValueError) as e:
                    raise RuntimeError('AGARENS-DOM.json går inte att läsa (%s); rätta filen innan en dom sparas' % e)
            domar[bokstav] = {'haller': data['haller'], 'niva': data['niva'], 'skiljer': (data.get('skiljer') or '').strip()[:4000], 'tid': nu(),
                              **({'minuter': minuter} if minuter is not None else {})}
            tmp = f.with_name('.AGARENS-DOM.json.tmp%d' % os.getpid())
            tmp.write_text(json.dumps(domar, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            os.replace(tmp, f)
        finally:
            fcntl.flock(las, fcntl.LOCK_UN)
    return {'ok': True, 'dom': domar[bokstav]}


# --- prototypen: skapandeflödets startsida före och efter bredvid huvudreferensen, ägarens dom i domloggen ---
# (kunskap/skapandeflodet.md; Codex via ägaren 2026-10-05: ägarens dom förs vidare automatiskt till nästa körning)
PR_LAS = threading.Lock()
PR_BILDER = (('390-forsta', 'vy-390-forsta.png'), ('390-hela', 'vy-390-hela.png'), ('1440-forsta', 'vy-1440-forsta.png'), ('1440-hela', 'vy-1440-hela.png'))
PR_BESLUT = ('godkand', 'putsa', 'ny_riktning')


KAND_FIL = re.compile(r'^underlag/([a-z0-9-]{2,60})/atelje/kandidater/k\d{2}/(?:versioner/[0-9a-f]{12}/)?bilder/[a-z0-9-]{1,80}/vy-(390|768|1280|1440)-(forsta|hela|ruta-\d{2})\.png$')
# skaparens senaste förhandsvarv, som observationen visar medan kandidaten arbetar (ägarens uppdrag 2026-10-06)
KAND_VARV = re.compile(r'^underlag/([a-z0-9-]{2,60})/atelje/kandidater/k\d{2}/varv/start/varv-\d{2}/vy-(390|1280|1440)-forsta\.png$')
KAND_BESLUT = ('valj', 'jamfor', 'forkasta', 'ny_riktning', 'putsa', 'godkand')


def prototyp_slugar():
    """Byggen med en körning i skapandeflödet (underlag/<slug>/atelje/STATUS.json med läge)."""
    ut = []
    for p in UNDERLAG.glob('*/atelje/STATUS.json'):
        st = las_json(p) or {}
        if SLUG.match(p.parent.parent.name) and st.get('lage'):
            ut.append(p.parent.parent.name)
    return sorted(ut)


def prototyp_domd(slug, st):
    """Har ägaren dömt den här körningen? En dom ur vyn bär körningens starttid i avser (spara_prototyp)."""
    import skapande
    return bool(st.get('startad')) and any(d.get('kalla') in skapande.AGAREN and st['startad'] in str(d.get('avser') or '')
                                             for d in skapande.domar(slug, UNDERLAG))


def prototyp(slug):
    """Skapandeflödets läge: riktningarna som prövades, startsidan före och efter förfiningen i 390 och 1440, den valda
    huvudreferensen, skaparens varv och ägarens domar. Vilken riktning som förfinades syns (före är panelens val, och
    ägaren dömer den synliga förbättringen mot ribban; Codex via ägaren 2026-10-05); panelens skäl, poäng och slutdom,
    förfiningens anteckningar och redovisningen visas först när ägaren dömt körningen, så att domen är oberoende av dem
    (som granskarens dom över byggen)."""
    import atelje
    import referensval
    import skapande
    rot = UNDERLAG / slug / 'atelje'
    st = las_json(rot / 'STATUS.json') or {}
    if kandidatkorning(slug, st):
        return kandidatvy(slug, st)
    domd = prototyp_domd(slug, st)
    bilder = lambda kat: {n: 'underlag/%s/atelje/%s/%s' % (slug, kat, fil) for n, fil in PR_BILDER if (rot / kat / fil).is_file()}  # noqa: E731
    vinnare = las_json(rot / 'VINNARE.json') or {}
    namn = atelje.riktningsavsnitt(rot)
    refs = atelje.riktningsreferenser(slug, rot)
    riktningar = [{'n': int(d.name), 'namn': namn.get(int(d.name), ('riktning %s' % d.name, ''))[0], 'referens': (refs.get(int(d.name)) or {}).get('namn'),
                   'bilder': bilder(d.name), 'vald': vinnare.get('riktning') == int(d.name)}
                  for d in sorted(rot.glob('[0-9]'), key=lambda x: int(x.name)) if d.is_dir() and not d.is_symlink()]
    hr = referensval.huvudreferens(slug, UNDERLAG)
    md_ = lambda n: md(las_text(rot / n) or '') if (rot / n).is_file() else ''  # noqa: E731
    return {'slug': slug, 'steg': st.get('steg'), 'lage': st.get('lage'), 'startad': st.get('startad'), 'klar': st.get('klar'), 'fel': st.get('fel'),
            'skal': st.get('skal'), 'omgangar': st.get('omgangar'), 'faser': sorted((st.get('faser') or {}).keys()), 'domd': domd,
            'startkontroll_stopp': st.get('startkontroll_stopp'),
            'riktningar': riktningar, 'fore': bilder('slutdom/1'), 'efter': bilder('slutdom/2'),
            'huvudreferens': {'namn': hr['namn'], 'vad': hr['vad'], 'bilder': [{'fil': str(p.relative_to(ROOT)), 'text': t_} for p, t_ in hr['bilder']]} if hr else None,
            'riktningar_md': md_('RIKTNINGAR.md'), 'forfining_md': md_('FORFINING.md') if domd else None,
            'val_md': md_('VAL.md') if domd else None, 'slutdom_md': md_('SLUTDOM.md') if domd else None, 'redovisning_md': md_('REDOVISNING.md') if domd else None,
            'domar': list(reversed(skapande.domar(slug, UNDERLAG))), 'godkand': vinnare.get('godkand')}


def kandidatvy(slug, st):
    """Kandidatflödet (ägarens uppdrag 2026-10-05, punkt 10, och 2026-10-06, punkt 8): alla kandidater med neutrala
    etiketter, lika stora bilder i mobil och dator (och 768 och 1280 när de finns), status och version, jämförelsen med
    huvudreferensen och skaparens korta redovisning (kandidater.sammanstall); förklaringarna, granskningen, falsk variation
    och körningens redovisning först när ägaren fattat sitt första beslut efter planen."""
    import kandidater
    import skapande
    rot = UNDERLAG / slug / 'atelje'
    domd = kandidater.domd(slug)
    kand = kandidater.sammanstall(slug)
    for k in kand:
        if k.get('riktning'):
            k['riktning_html'] = md(k.pop('riktning'))
        for r in k.get('redovisning') or []:  # en saknad rubrik (None) skiljs från en tom: vyn säger vilket
            a = r.pop('avsnitt', None)
            r.update(finns=a is not None, html=md(a) if a else '')
    vinnare = las_json(rot / 'VINNARE.json') or {}
    md_ = lambda n: md(las_text(rot / n) or '') if (rot / n).is_file() else ''  # noqa: E731
    jamf = las_json(rot / 'JAMFORELSE.json') if domd else None
    namn = {k['id']: k['etikett'] for k in kand}
    import atelje
    return {'slug': slug, 'kandidatflode': True, 'kandidatlage': kandidater.korlage(slug, st), 'tider': st.get('tider') or {},
            'startkontroll_stopp': st.get('startkontroll_stopp'),
            'steg': st.get('steg'), 'fas': st.get('fas'), 'lage': st.get('lage'), 'startad': st.get('startad'),
            'klar': st.get('klar'), 'fel': st.get('fel'), 'skal': st.get('skal'), 'domd': domd, 'kandidater': kand, 'avbruten': atelje.avbruten(st),
            'antal': (las_json(rot / 'KANDIDATPLAN.json') or {}).get('antal') or len(kand),
            'forbattring_agaren': (las_json(rot / 'FORBATTRING-AGAREN.json') or []) if domd else [],
            'jamforelse': {'sammanfattning': jamf.get('sammanfattning'), 'par': [dict(p, a=namn.get(p['a'], p['a']), b=namn.get(p['b'], p['b'])) for p in jamf.get('par') or []]}
            if isinstance(jamf, dict) else None,
            'redovisning_md': md_('REDOVISNING.md') if domd else None, 'forskning_md': md_('FORSKNING.md') if domd else None,
            'domar': list(reversed(skapande.domar(slug, UNDERLAG))), 'godkand': vinnare.get('godkand'),
            'godkand_kandidat': vinnare.get('kandidat') if vinnare.get('godkand') else None}


def visa_kandidat(slug, kid):
    """Kandidatens hela prototyp, klickbar, på en egen lokal adress (samma statiska server som provet, med formulärets
    lokala demonstration: /api/forfragan → /tack/)."""
    import kandidater
    if not kandidater.ID.fullmatch(kid) or kid not in kandidater.lista(slug):
        return None
    dist = kandidater.ksajt(slug, kid) / 'dist'
    if not (dist / 'index.html').is_file():
        return None
    nyckel = '%s/%s' % (slug, kid)
    if nyckel not in VISNING:
        srv = Server(dist)
        srv.__enter__()
        VISNING[nyckel] = srv
    return VISNING[nyckel].url + '/'


def spara_prototyp(slug, data, minuter=None):
    """Ägarens dom över körningen till domloggen (underlag/<slug>/DESIGNDOMAR.jsonl, privat): beslut godkand, putsa eller
    ny_riktning, med ägarens ord. Nästa körning läser den själv (kontroller/prototyp.py); godkand lämnar över till bygget
    (VINNARE.json, kor.sh)."""
    import atelje
    import skapande
    if slug not in prototyp_slugar():
        raise ValueError('ingen prototyp för bygget')
    st = las_json(UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    if kandidatkorning(slug, st):
        return spara_kandidatbeslut(slug, st, data, minuter)
    if st.get('steg') not in ('klar', 'forkastad', 'tillbaka'):
        raise ValueError('körningen är inte klar (steg %s)' % st.get('steg'))
    if data.get('beslut') not in PR_BESLUT:
        raise ValueError('välj godkänd, putsa vidare eller ny riktning')
    if data.get('niva') is not None and data['niva'] not in NIVAER:
        raise ValueError('okänd nivå')
    text = (data.get('text') or '').strip() or ('Godkänd.' if data['beslut'] == 'godkand' else '')
    if not text:
        raise ValueError('skriv vad som ska ändras: domen är nästa körnings kritik')
    if data['beslut'] == 'godkand' and st.get('steg') != 'klar':
        raise ValueError('bara en klar körning kan godkännas')
    with PR_LAS:  # godkännandet prövas före domen skrivs; en annan dom drar tillbaka ett tidigare godkännande (atelje.doma)
        dom = atelje.doma(slug, 'ägaren', data['beslut'], text[:20000], avser='skapandeflödet, körningen %s' % st.get('startad'),
                          **({'niva': data['niva']} if data.get('niva') else {}), **({'minuter': minuter} if minuter is not None else {}))
    return {'ok': True, 'dom': dom}


def spara_kandidatbeslut(slug, st, data, minuter=None):
    """Ägarens beslut i kandidatflödet till domloggen: valj (en eller flera vidare), jamfor (sida vid sida), forkasta
    (alla), ny_riktning, putsa (de förfinade vidare) eller godkand (en förfinad kandidat till helbygget). Kandidaterna
    följer med sina versioner, och delar är det ägaren gillade per kandidat; atelje.doma prövar dem mot kandidaternas
    läge innan domen skrivs."""
    import atelje
    if st.get('steg') not in ('klar_for_bedomning', 'fel'):
        raise ValueError('kandidaterna är inte klara för bedömning (steg %s)' % st.get('steg'))
    b = data.get('beslut')
    if b not in KAND_BESLUT:
        raise ValueError('välj ett beslut')
    kand = [{'id': str(k.get('id') or ''), 'version': str(k.get('version') or '')} for k in data.get('kandidater') or [] if isinstance(k, dict)][:12]
    delar = {str(k): str(v)[:2000] for k, v in (data.get('delar') or {}).items() if str(v).strip()} if isinstance(data.get('delar'), dict) else {}
    text = (data.get('text') or '').strip()
    if not text and b in ('forkasta', 'ny_riktning', 'putsa'):
        raise ValueError('skriv vad som inte håller och vad nästa försök ska pröva: din text är nästa körnings kritik')
    if not text:  # ingen standardfras som ägarens ordagranna ord: domloggen och prompterna säger att ägaren inte skrev något
        text = '(ägaren skrev ingen text)'
    with PR_LAS:
        dom = atelje.doma(slug, 'ägaren', b, text[:20000], avser='skapandeflödet, kandidatplanen %s' % (las_json(UNDERLAG / slug / 'atelje' / 'KANDIDATPLAN.json') or {}).get('tid'),
                          kandidater=kand, **({'delar': delar} if delar else {}), **({'minuter': minuter} if minuter is not None else {}))
    return {'ok': True, 'dom': dom}


def spara_forbattring(slug, data):
    """Ägarens omdöme om en förbättringsrunda (synpunkterna på metodkartan 2026-10-05, punkt 5): föreversionen eller den
    förbättrade är bättre, eller lika. Prövar om granskningens förbättringar hjälper; underlag/<slug>/atelje/
    FORBATTRING-AGAREN.json (privat). Bara efter ägarens första beslut, när före och efter visas."""
    import kandidater
    if slug not in prototyp_slugar() or not kandidater.domd(slug):
        raise ValueError('före och efter visas efter ditt första beslut')
    kid, val = str(data.get('kid') or ''), data.get('val')
    if not kandidater.ID.fullmatch(kid) or kid not in kandidater.lista(slug) or val not in ('fore', 'efter', 'lika'):
        raise ValueError('välj föreversionen, förbättringen eller lika för en kandidat')
    st = kandidater.las_status(slug, kid)
    f = st.get('forbattrad') or {}
    if not f.get('fore') or f.get('fore') == st.get('version'):
        raise ValueError('kandidaten har ingen förbättringsrunda att jämföra')
    fil = UNDERLAG / slug / 'atelje' / 'FORBATTRING-AGAREN.json'
    with PR_LAS:
        allt = las_json(fil) or []
        allt = [x for x in allt if x.get('kid') != kid or x.get('efter') != st.get('version')] + [
            {'tid': nu(), 'kid': kid, 'fore': f['fore'], 'efter': st.get('version'), 'val': val}]
        tmp = fil.with_name('.FORBATTRING-AGAREN.json.tmp%d' % os.getpid())
        tmp.write_text(json.dumps(allt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        os.replace(tmp, fil)
    return {'ok': True, 'antal': len(allt)}


# --- domen ---

def spara_dom(slug, data):
    if not (KUNDER / slug).is_dir():
        raise ValueError('okänt bygge')
    svar = data.get('svar')
    if not isinstance(svar, dict) or not svar:
        raise ValueError('inga svar')
    text = json.dumps(svar, ensure_ascii=False)
    if len(text) > 40000:
        raise ValueError('för långa svar')
    s = las_json(KUNDER / slug / 'prov' / 'STATUS.json') or {}
    post = {'tid': nu(), 'bygge_dist': (s.get('dist_sha256') or '')[:12], 'svar': svar,
            'fragor': {'karna': KARNFRAGOR, 'egna': egna_fragor(slug)}}
    minuter = minuter_sedan(data.get('startad'))  # från att byggets sida öppnades till domen (kontroller/autonomi.py)
    if minuter is not None:
        post['minuter'] = minuter
    fil = KUNDER / slug / 'DOM.json'
    allt = las_json(fil) or {'schema': 1, 'slug': slug, 'domar': []}
    allt['domar'].append(post)
    fil.write_text(json.dumps(allt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    lar = ROOT / 'LARDOMAR.md'
    befintlig = las_text(lar) or '# Lärdomar — ägarens domar\n'
    n = max([int(x) for x in re.findall(r'^## L(\d+) ', befintlig, re.M)] or [-1]) + 1
    alla = {f['id']: f for f in KARNFRAGOR + (post['fragor']['egna'] if isinstance(post['fragor']['egna'], list) else []) if isinstance(f, dict) and 'id' in f}
    karn = {f['id']: f for f in KARNFRAGOR}
    fasta = {f['id'] for f in KARNFRAGOR if f.get('typ') in ('val', 'skala', 'matris')}  # fasta svar utan fritext: får stå publikt
    rader = ['', '## L%d · %s · %s' % (n, post['tid'][:10], slug), '']  # ordagrant: privat (BESLUT.md 2026-10-03)
    publika = list(rader)  # bara betygen och valen: publikt, i git
    for fid, v in svar.items():
        if v in (None, '', {}, []):
            continue
        fraga = (alla.get(fid) or {}).get('fraga', fid)
        pv = publikt_varde(karn[fid], v) if fid in fasta else None  # publikt bara ett giltigt fast svar, under kärnfrågans rubrik (F37)
        if isinstance(v, dict):
            v = ', '.join('%s: %s' % (k, x) for k, x in v.items() if x)
        rader.append('- **%s** %s' % (fraga, str(v).replace('\n', ' / ')))
        if pv is not None:
            publika.append('- **%s** %s' % (karn[fid]['fraga'], pv))
    rader += ['', '**Ändring:** väntar', '']
    publika += ['', '**Ägarens ord:** ordagrant i `underlag/LARDOMAR-original.md` (privat) och `kunder/%s/DOM.json`' % slug,
                '**Lärdom:** skrivs utan personuppgifter av sessionen som gör ändringen', '**Ändring:** väntar', '']
    # Domen blir automatiskt en vilande post i backloggen (loop 3): en session ägaren startar klassar domen och gör
    # ändringen där slaget säger (backlog-skillen, steg 3; Codex via ägaren 2026-10-05, punkt 10). Posten och den publika
    # raden får inga fritextsvar (personuppgifter; BESLUT.md 2026-10-03).
    betyg = '; '.join('%s: %s' % (karn[k]['fraga'], publikt_varde(karn[k], svar.get(k))) for k in ('namn', 'battre', 'specifik')
                      if publikt_varde(karn[k], svar.get(k)) is not None)
    pid = bl.ny('dom', 'Dom L%d (%s)' % (n, slug),
                'Ägarens dom L%d om %s: ordagrant i underlag/LARDOMAR-original.md (privat, utanför git) och kunder/%s/DOM.json. %s'
                % (n, slug, slug, betyg or 'Betygen står i LARDOMAR.md.'),
                forslag='Läs domen ordagrant i underlag/LARDOMAR-original.md (L%d, privat) och kunder/%s/DOM.json. Klassa den först '
                        '(kundbeslut, smakpreferens, metodhypotes eller generell rättelse; backlog-skillen, steg 3): bara en generell '
                        'rättelse blir en ändring i skillen bygg-sajt, en fil i kunskap/ eller en kontroll. En ändring, liten nog att läsa på '
                        'fem minuter. Skriv sedan lärdomen på raden Lärdom under L%d i LARDOMAR.md utan personuppgifter: företagsnamn '
                        'får stå, inte privatpersoners namn, nummer, adresser eller hälsa.' % (n, slug, n),
                klart='Ändringen är committad, raden Lärdom under L%d i LARDOMAR.md är skriven utan personuppgifter och raden Ändring '
                      'pekar på commiten.' % n,
                sar='L%d' % n, kallref='LARDOMAR.md L%d' % n)
    rader[-2] = '**Ändring:** väntar (backlog %s)' % pid
    publika[-2] = rader[-2]
    skriv_original(rader)
    with open(lar, 'a', encoding='utf-8') as f:
        f.write('\n'.join(publika))
    git = commit_agarens(['LARDOMAR.md', 'backlog/%s.md' % pid], 'Ägaren: dom L%d (%s)' % (n, slug))
    gruppering = None
    if (n + 1) % 5 == 0:  # L0 räknas: efter var femte dom grupperas domarna och granskarens fynd (kontroller/gruppera.py)
        import subprocess
        with open(ROOT / 'kunder' / ('gruppering-L%d.log' % n), 'wb') as logg:
            subprocess.Popen([sys.executable, '-B', str(ROOT / 'kontroller' / 'gruppera.py')], cwd=str(ROOT), stdout=logg,
                             stderr=subprocess.STDOUT, start_new_session=True)
        gruppering = 'startad efter %d domar' % (n + 1)
    return {'lardom': 'L%d' % n, 'sparad': str(fil.relative_to(ROOT)), 'backlog': pid, 'git': git, 'gruppering': gruppering}


# --- backloggen och kirurgen ---

def backloggen():
    ut = []
    for p in bl.lista():
        kropp = p.pop('kropp', '')
        p['html'] = md(re.sub(r'^# .+\n', '', kropp, count=1, flags=re.M))
        p['lage'] = bl.lage(p)  # klar, inte verifierad eller klar, verifierad av <rapport> (granskningen av r97, BÖR 5)
        ut.append(p)
    ordning = {'pagar': 0, 'vilande': 1, 'klar': 2, 'ersatt': 3, 'avvisad': 4}
    return sorted(ut, key=lambda p: (ordning.get(p.get('status'), 9), p.get('prio') != 'hog', p.get('skapad', '')))


INTAG = ROOT / 'kirurgen'
# Vitlista: intaget startas med --setting-sources project,local, så ägarens egna allow-regler gäller inte här.
INTAG_VERKTYG = ['Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch', 'Skill', 'Task', 'Edit(kunskap/REGISTER.md)',
                 'Bash(.venv/bin/python kontroller/backlog.py *)', 'Bash(.venv/bin/python kontroller/youtube.py *)',
                 'Bash(node kontroller/sida.mjs *)', 'Bash(.venv/bin/python kontroller/granska_repo.py *)', 'Bash(curl -sSL -o /tmp/kirurg/*)', 'Bash(gh repo clone *)', 'Bash(gh repo view *)',
                 'Bash(cd *)', 'Bash(git add *)', 'Bash(git commit *)', 'Bash(git push origin main)',
                 'Bash(ls *)', 'Bash(find *)', 'Bash(wc *)', 'Bash(head *)', 'Bash(tail *)', 'Bash(cat *)', 'Bash(mkdir *)']
INTAG_NEKAS = ['Bash(rm *)', 'Bash(gh pr *)', 'Bash(git rebase *)', 'Bash(git checkout *)', 'Bash(git reset *)',
               'Bash(git worktree *)', 'Bash(git config *)', 'Bash(git push --force *)', 'Bash(git push -f *)']
UPPLADDNING_TYPER = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.txt', '.md'}
UPPLADDNING_MAX = 40 * 1024 * 1024


def intag_lista():
    if not INTAG.is_dir():
        return []
    ut = []
    for meta in sorted(INTAG.glob('intag-*.json'), reverse=True)[:30]:
        m = las_json(meta) or {}
        logg = meta.with_suffix('.jsonl')
        k = las_logg(logg) if logg.is_file() else None
        filer = m.get('filer') or []
        etikett = m.get('url') or ('Uppladdat: ' + ', '.join(Path(f).name for f in filer[:4]) + (' …' if len(filer) > 4 else ''))
        ut.append({'id': meta.stem, 'url': etikett, 'not': m.get('not'), 'tid': m.get('tid'),
                   'pagar': bool(k and k['pagar']), 'resultat': k and k['resultat'], 'svar': md(k['senaste_text']) if k and k.get('senaste_text') else '',
                   'handlingar': (k or {}).get('handlingar', [])[:6]})
    return ut


def spara_uppladdning(stamp, filer):
    """Ägarens uppladdade filer (base64 i JSON) till kirurgen/uppladdat/<stamp>/. Bara bilder, PDF och text."""
    import base64
    if not filer:
        return []
    if not isinstance(filer, list) or len(filer) > 30:
        raise ValueError('högst 30 filer')
    mapp = INTAG / 'uppladdat' / stamp
    mapp.mkdir(parents=True, exist_ok=True)
    sparade, total = [], 0
    for i, f in enumerate(filer):
        namn = re.sub(r'[^A-Za-z0-9._-]+', '-', str(f.get('namn') or 'fil'))[-80:].strip('-.') or 'fil'
        if Path(namn).suffix.lower() not in UPPLADDNING_TYPER:
            raise ValueError('filtypen tas inte emot: %s (bilder, PDF, txt, md)' % namn)
        data = base64.b64decode(str(f.get('data') or '').split(',', 1)[-1], validate=False)
        total += len(data)
        if total > UPPLADDNING_MAX:
            raise ValueError('uppladdningen är större än 40 MB')
        p = mapp / ('%02d-%s' % (i + 1, namn))
        p.write_bytes(data)
        sparade.append(str(p))
    return sparade


def starta_intag(url, not_, filer=None):
    import os
    import shutil
    import subprocess
    url = (url or '').strip()
    if url and not re.fullmatch(r'https?://[^\s]{4,500}', url):
        raise ValueError('ange en http- eller https-adress')
    if not url and not filer:
        raise ValueError('ange en länk eller ladda upp filer')
    if sum(1 for x in intag_lista() if x['pagar']) >= 2:
        raise ValueError('två intag pågår redan; vänta tills ett är klart')
    claude = shutil.which('claude') or str(Path.home() / '.local/bin/claude')
    INTAG.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    sparade = spara_uppladdning(stamp, filer)
    meta = INTAG / ('intag-%s.json' % stamp)
    meta.write_text(json.dumps({'url': url, 'filer': sparade, 'not': not_ or '', 'tid': nu()}, ensure_ascii=False) + '\n', encoding='utf-8')
    kalla = []
    if url:
        kalla.append('Länk: %s' % url)
    if sparade:
        kalla.append('Ägaren laddade upp dessa filer; läs varje fil med Read (bilder och PDF går att läsa):\n' + '\n'.join('- ' + f for f in sparade))
    prompt = ('Använd skillen kirurg (.claude/skills/kirurg/SKILL.md) på följande.\n\n%s\n\nÄgarens not: %s\n\nDu startades från dashboarden; '
              'ingen människa svarar under körningen. Följ skillen hela vägen: registret, och vid "ta in" eller "prova A/B" '
              'backloggen. Avsluta med domen och skälet i högst fyra meningar.') % ('\n\n'.join(kalla), (not_ or '').strip() or 'ingen')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_')}
    env['NWP_COMMIT_TILLATET'] = 'kunskap/REGISTER.md,backlog/'  # commitvakten: bara registret och backloggen
    env.pop('NWP_SLUG', None)
    # --setting-sources project,local: ägarens egna allow-regler läses inte, så INTAG_VERKTYG är en vitlista
    # (rena läskommandon tillåter Claude Code alltid). Modell och effort anges därför uttryckligen.
    anv = las_json(Path.home() / '.claude' / 'settings.json') or {}
    args = [claude, '-p', '--max-turns', os.environ.get('NWP_KIRURG_TURER', '250'), '--permission-mode', 'dontAsk',
            '--output-format', 'stream-json', '--verbose', '--setting-sources', 'project,local',
            '--strict-mcp-config',  # inga anslutningar (Gmail, Drive, Resend …) i kirurgens körning
            '--model', os.environ.get('NWP_KIRURG_MODELL') or anv.get('model') or 'opus[1m]',
            '--effort', os.environ.get('NWP_KIRURG_EFFORT') or anv.get('effortLevel') or 'high',
            '--allowedTools', *INTAG_VERKTYG, '--disallowedTools', *INTAG_NEKAS]
    gh = (anv.get('env') or {}).get('GH_CONFIG_DIR')
    if gh:
        args += ['--settings', json.dumps({'env': {'GH_CONFIG_DIR': gh}})]
    with open(meta.with_suffix('.jsonl'), 'wb') as ut:
        p = subprocess.Popen(args, cwd=str(ROOT), env=env, stdin=subprocess.PIPE, stdout=ut, stderr=subprocess.STDOUT, start_new_session=True)
        p.stdin.write(prompt.encode())
        p.stdin.close()
    return {'id': meta.stem}


# --- spanaren: kandidater åt kirurgen, utan modell (kontroller/spana.py) ---
SPANING = INTAG / 'spaning'
# Varje dygn under piloten (ägaren 2026-10-03: "jag vill ha den frekventare"); 7 när piloten är över.
SPANING_INTERVALL = float(os.environ.get('NWP_SPANING_INTERVALL_DAGAR') or 1)


def spaning_pagar():
    try:
        pid = int((SPANING / 'PAGAR').read_text().strip() or 0)
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def spaning_traffsakerhet():
    """Per källa: hur många intag som hittades av spanaren (registerposternas not 'Hittad av spanaren … via <källa>') och vad
    domen blev (rubrikens sista led: ta in, prova, parkera, nej …). Vikterna ändras efter beslut, inte automatiskt."""
    import re as re_
    ut = {}
    try:
        text = (ROOT / 'kunskap' / 'REGISTER.md').read_text(encoding='utf-8')
    except OSError:
        return []
    for post in re_.split(r'(?m)^(?=### )', text):
        m = re_.search(r'Hittad av spanaren[^\n]*?via ([^.\n]+)', post)
        if not m:
            continue
        rubrik = post.splitlines()[0]
        dom = rubrik.rsplit(' · ', 1)[-1].strip().lower() if ' · ' in rubrik else 'okänd'
        kalla = m.group(1).strip()
        k = ut.setdefault(kalla, {'kalla': kalla, 'antal': 0, 'domar': {}})
        k['antal'] += 1
        k['domar'][dom] = k['domar'].get(dom, 0) + 1
    return sorted(ut.values(), key=lambda x: -x['antal'])


def spaning_lista():
    lista = las_json(SPANING / 'KANDIDATER.json') or []
    nya = [k for k in lista if k.get('status') == 'ny']
    # tre delar (backloggen 2026-10-03): nytt sedan i går, de två bästa per område, det som svarar mot ägarens domar
    igar = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    per_omrade = {}
    for k in nya:
        per_omrade.setdefault(k.get('omrade') or 'okänt', []).append(k)
    return {'kandidater': nya[:20], 'antal': len(nya), 'senast': las_json(SPANING / 'SENAST.json'), 'pagar': bool(spaning_pagar()),
            'av': bool(os.environ.get('NWP_SPANING_AV')), 'intervall_dagar': SPANING_INTERVALL,
            'nytt_sedan_igar': [k for k in nya if (k.get('hittad') or '') >= igar][:10],
            'basta_per_omrade': {o: v[:2] for o, v in sorted(per_omrade.items())},
            'svarar_mot_domar': [k for k in nya if k.get('svarar_mot')][:10],
            'utgangna': sum(1 for k in lista if k.get('status') == 'utgangen'),
            'traffsakerhet': spaning_traffsakerhet()}


def starta_spaning(skal='ägaren'):
    import subprocess
    if spaning_pagar():
        raise ValueError('en spaning pågår redan')
    SPANING.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_') and (not k.startswith('NWP_') or k.startswith('NWP_SPANING_'))}
    env.setdefault('NWP_SPANING_MAX_ANROP', '200')  # 97 källor ger ~100 anrop; spanarens tak är 120
    gh = ((las_json(Path.home() / '.claude' / 'settings.json') or {}).get('env') or {}).get('GH_CONFIG_DIR')
    if gh:
        env['GH_CONFIG_DIR'] = gh
    with open(SPANING / 'korning.log', 'ab') as ut:
        ut.write(('\n=== %s %s ===\n' % (nu(), skal)).encode())
        subprocess.Popen([sys.executable, '-B', str(ROOT / 'kontroller' / 'spana.py'), 'spana'], cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                         stdout=ut, stderr=subprocess.STDOUT, start_new_session=True)
    return {'startad': True}


# --- underhållet: verktygslådans uppdateringar prövas och tas in mellan byggena (kontroller/underhall.py) ---
UNDERHALL_LAGE = UNDERLAG / 'startkontroll'
UNDERHALL_INTERVALL = float(os.environ.get('NWP_UNDERHALL_INTERVALL_DAGAR') or 1)  # ägarens uppdrag 2026-10-05: dagligt


def underhall_pagar():
    d = las_json(UNDERHALL_LAGE / 'UNDERHALL-PAGAR.json') or {}
    try:
        os.kill(int(d.get('pid')), 0)
        return d
    except (OSError, TypeError, ValueError):
        return None


def underhall_lage():
    rap = las_json(UNDERHALL_LAGE / 'UNDERHALL.json') or {}
    andringar = []
    try:
        for rad in (UNDERHALL_LAGE / 'ANDRINGAR.jsonl').read_text(encoding='utf-8').splitlines()[-30:]:
            try:
                andringar.append(json.loads(rad))
            except ValueError:
                pass
    except OSError:
        pass
    return {'pagar': underhall_pagar(), 'senast': {k: rap.get(k) for k in ('start', 'slut', 'sammanfattning', 'antal', 'push', 'status', 'besked')} if rap else None,
            'md': md(las_text(UNDERHALL_LAGE / 'UNDERHALL.md')) if (UNDERHALL_LAGE / 'UNDERHALL.md').is_file() else '',
            'av': bool(os.environ.get('NWP_UNDERHALL_AV')), 'intervall_dagar': UNDERHALL_INTERVALL, 'andringar': andringar[::-1][:12]}


def starta_underhall(skal='ägaren'):
    import subprocess
    if underhall_pagar():
        raise ValueError('ett underhåll pågår redan')
    UNDERHALL_LAGE.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_') and (not k.startswith('NWP_') or k.startswith('NWP_UNDERHALL_'))}
    gh = ((las_json(Path.home() / '.claude' / 'settings.json') or {}).get('env') or {}).get('GH_CONFIG_DIR')
    if gh:
        env['GH_CONFIG_DIR'] = gh
    with open(UNDERHALL_LAGE / 'underhall.log', 'ab') as ut:
        ut.write(('\n=== %s %s ===\n' % (nu(), skal)).encode())
        subprocess.Popen([sys.executable, '-B', str(ROOT / 'kontroller' / 'underhall.py')], cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                         stdout=ut, stderr=subprocess.STDOUT, start_new_session=True)
    return {'startad': True}


def underhall_vid_behov():
    """Underhållet utan schemaläggare, som spaningen: vid serverstart och varje timme, om det senaste är äldre än intervallet
    och ingen körning pågår (underhållet tar aldrig in något medan en körning pågår). Misslyckade försök väntar sex timmar."""
    if os.environ.get('NWP_UNDERHALL_AV') or underhall_pagar():
        return
    try:
        senast = (UNDERHALL_LAGE / 'UNDERHALL.json').stat().st_mtime
    except OSError:
        senast = 0
    try:
        forsok = (UNDERHALL_LAGE / 'FORSOK').stat().st_mtime
    except OSError:
        forsok = 0
    if time.time() - senast < UNDERHALL_INTERVALL * 86400 or time.time() - forsok < 6 * 3600:
        return
    import verktygslada
    if verktygslada.pagaende():
        return
    UNDERHALL_LAGE.mkdir(parents=True, exist_ok=True)
    (UNDERHALL_LAGE / 'FORSOK').write_text(nu())
    starta_underhall('automatisk, var %g dygn' % UNDERHALL_INTERVALL)


def startkvitto(slug):
    """Startkontrollens kvitto för körningen (underlag/<slug>/atelje/STARTKVITTO.json och .md), och en senare start som
    stoppades (STARTKVITTO-STOPP.json och .md) bredvid."""
    rot = UNDERLAG / slug / 'atelje'
    kv, stopp = las_json(rot / 'STARTKVITTO.json'), las_json(rot / 'STARTKVITTO-STOPP.json')
    if stopp and kv and str(stopp.get('tid') or '') < str(kv.get('tid') or ''):
        stopp = None  # en senare start gick igenom
    if not kv and not stopp:
        return None
    import startkontroll
    ut = dict(startkontroll.sammanfattning(kv), md=md(las_text(rot / 'STARTKVITTO.md')) if (rot / 'STARTKVITTO.md').is_file() else '') if kv else {}
    if stopp:
        ut['stopp'] = dict(startkontroll.sammanfattning(stopp), md=md(las_text(rot / 'STARTKVITTO-STOPP.md')) if (rot / 'STARTKVITTO-STOPP.md').is_file() else '')
    return ut


def spaning_vid_behov():
    """Spaning utan schemaläggare: vid serverstart, varje timme (spaningsklocka) och vid varje läsning av /api/kirurg, om
    den senaste är äldre än intervallet. Misslyckade försök väntar sex timmar (FORSOK) så att en död källa inte startar
    om vid varje poll. Sover datorn tas spaningen igen när den vaknar."""
    if os.environ.get('NWP_SPANING_AV') or spaning_pagar():
        return
    try:
        senast = (SPANING / 'SENAST.json').stat().st_mtime
    except OSError:
        senast = 0
    try:
        forsok = (SPANING / 'FORSOK').stat().st_mtime
    except OSError:
        forsok = 0
    if time.time() - senast < SPANING_INTERVALL * 86400 or time.time() - forsok < 6 * 3600:
        return
    SPANING.mkdir(parents=True, exist_ok=True)
    (SPANING / 'FORSOK').write_text(nu())
    starta_spaning('automatisk, var %g dygn' % SPANING_INTERVALL)


def kandidat(ident):
    lista = las_json(SPANING / 'KANDIDATER.json') or []
    k = next((x for x in lista if x.get('id') == ident), None)
    if not k:
        raise ValueError('ingen kandidat %s' % ident)
    return k


def ta_in_kandidat(ident):
    """Startar ett vanligt intag med en neutral proveniensnot: datum, källans namn och typ, våra egna termer. Aldrig källans
    text, aldrig en begäran (kirurgens dedupe-undantag ska inte väckas av spanaren)."""
    import subprocess
    k = kandidat(ident)
    if k.get('status') != 'ny':
        raise ValueError('kandidaten är redan %s' % k.get('status'))
    if k.get('ny_version'):
        raise ValueError('redan dömd nej tidigare: skicka länken själv med en not om du vill ha en ny bedömning')
    not_ = 'Hittad av spanaren %s via %s (%s); matchade: %s' % (nu()[:10], k.get('kalla'), k.get('kalla_typ'), ', '.join((k.get('traffar') or [])[:6]) or 'inga termer')
    r = starta_intag(k['url'].split('#')[0], not_)
    subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'spana.py'), 'intagen', ident, '--intag', r['id']], cwd=str(ROOT), timeout=30)
    return {'intag': r['id'], 'not': not_}


def avfarda_kandidat(ident, skal):
    import subprocess
    kandidat(ident)
    subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'spana.py'), 'avfard', ident, '--skal', (skal or '')[:300]], cwd=str(ROOT), timeout=30)
    return {'id': ident, 'status': 'avfardad'}


def redan_bedomd(url):
    n = kallnyckel.normalisera(url or '')
    tr = kallnyckel.kanda_kallor().get(n) if n else None
    return {'url': url, 'normaliserad': n, 'kand': tr}


pv.koppla(siffror=siffror, bilder=bilder, korning=korning, byggen=byggen)


# --- http ---

import threading  # noqa: E402

VISNING = {}
VISNING_LAN = {}
LAN = {'pa': True, 'tid': 2 * 3600}  # visningen i telefonen stängs efter två timmar; knappen startar den igen
LAN_LAS = threading.Lock()
VARD = {'tillatna': set()}  # Host-värden dashboarden svarar på (sätts i main); annat är DNS-rebinding eller fel adress
# Dashboardnyckeln (backlogposten B-20261005-dashboardens-api-tar-emot-agarens-domar-fran-vil): Origin lika med Host räcker inte
# mot en lokal process som sätter Origin fritt (ett bygge, en sidas byggkod, ett skript). Varje skrivande anrop kräver nyckeln
# som bara ägarens webbläsare får: dashboard.sh öppnar adressen med #nyckel=… och sidan skickar den som X-Nyckel. Sätts i
# main ur NWP_DASHBOARD_NYCKEL (som tas bort ur miljön så att inga barnprocesser ärver den) eller skapas där och skrivs till
# NYCKELFIL (0600, i hemlighetsmappen som byggena nekas läsa). None (proven utan main): inget nyckelkrav.
NYCKEL = {'varde': None}
NYCKELFIL = Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'dashboard-nyckel'


def natverksadress():
    """Datorns adress i det lokala nätverket (privat IPv4), eller None. UDP-anslutningen skickar inget paket; den
    frågar bara routingtabellen vilken adress som används utåt."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('192.0.2.1', 80))
            ip = s.getsockname()[0]
    except OSError:
        return None
    a = ipaddress.ip_address(ip)
    return ip if a.is_private and not a.is_loopback and not a.is_link_local else None


def visa_lan(slug):
    """Sajten på nätverksadressen, för ägarens telefon på samma Wi-Fi (backloggposten om mobilen i en riktig telefon).
    Bara den statiska sajten och dess demomottagare för formuläret (sparar och skickar ingenting)."""
    dist = KUNDER / slug / 'sajt' / 'dist'
    ip = natverksadress() if LAN['pa'] else None
    if not ip or not (dist / 'index.html').is_file():
        return None
    stang_lan(bara_gamla=True)
    with LAN_LAS:
        if slug not in VISNING_LAN:
            srv = Server(dist, vard=ip)
            srv.__enter__()
            VISNING_LAN[slug] = (srv, time.time())
        return VISNING_LAN[slug][0].url + '/'


def lan_lage(slug):
    """Läget för visningen i det lokala nätverket, utan att starta något (GET; omgång elva, F13)."""
    with LAN_LAS:
        post = VISNING_LAN.get(slug)
    url = post[0].url + '/' if post else None
    skal = None if url else ('avstängd (--utan-lan)' if not LAN['pa'] else 'inte startad')
    return {'natverk': url, 'qr': qr.svg(url) if url else None, 'skal': skal}


def starta_lan(slug):
    """Startar visningen (POST från dashboardens knapp, med ursprungskontroll) och svarar med läget."""
    url = visa_lan(slug)
    skal = None if url else ('avstängd (--utan-lan)' if not LAN['pa'] else 'ingen adress i ett lokalt nätverk hittades')
    return {'natverk': url, 'qr': qr.svg(url) if url else None, 'skal': skal}


def stang_lan(bara_gamla=False):
    """Stäng visningarna på nätverksadressen: alla, eller de som stått öppna längre än LAN['tid'] (ägarfråga 5 i revisionen:
    alla på nätverket når servern, så den ska inte stå öppen i veckor). Idempotent och låst: två samtidiga anrop kan
    inte ta bort samma post två gånger (revisionen, F29). Returnerar antalet stängda."""
    stangda = 0
    with LAN_LAS:
        for slug in list(VISNING_LAN):
            post = VISNING_LAN.get(slug)
            if post and (not bara_gamla or time.time() - post[1] > LAN['tid']):
                VISNING_LAN.pop(slug, None)
                try:
                    post[0].__exit__(None, None, None)
                except Exception:
                    pass
                stangda += 1
    return stangda


def lan_klocka():
    """Varje minut: stäng visningar som passerat sin tid, så att gränsen är två timmar och inte upp till tre."""
    while True:
        try:
            stang_lan(bara_gamla=True)
        except Exception as e:  # noqa: BLE001 — underhållet får aldrig ta med sig tråden
            print('kunde inte stänga visningen: %s' % e, flush=True)
        time.sleep(60)


def visa(slug):
    dist = KUNDER / slug / 'sajt' / 'dist'
    if not (dist / 'index.html').is_file():
        return None
    if slug not in VISNING:
        srv = Server(dist)
        srv.__enter__()
        VISNING[slug] = srv
    return VISNING[slug].url + '/'


# --- flödesvyn (ägarens tillägg 2026-10-06, punkt 4): det tänkta flödet ur README:s kedja, och det som faktiskt hände
# för en kund, steg för steg, ur filerna och identiteterna som redan finns; ingen ny logg. En fil som finns är inte ett
# kontrollerat steg, och ett senare steg som inte är gjort visas som sådant. Före ägarens första val i en körning visas
# bara neutral framdrift (BESLUT.md 2026-10-05, punkt 1): etikett, status, version och bilderna, ingen bedömning. ---

STATUSAR = ('skapat', 'kontrollerat', 'underkänt', 'väntar på ägaren', 'beslutat', 'inaktuellt', 'pågår', 'stoppat',
            'inte observerat', 'inte påbörjat')
KEDJAN = '## Kedjan från kundunderlag till leverans'
INTE_KUNDER = ('ab', 'kalibrering', 'prospekt', 'startkontroll', 'figma-pilot', 'kirurgen')
KVITTOSTATUS = {'ok': 'ok', 'begransad': 'begränsad', 'stopp': 'stoppad', 'okand': 'okänd'}
FLODESTEG = ('Kundunderlaget', 'Prototypen', 'Ditt val', 'Förfiningen', 'Godkännandet', 'Helbygget', 'Din dom över bygget',
             'Exporten till kundrepo', 'Leveransen')
PILOTVERSION = re.compile(r'v\d+(?:\.\d+)*')  # pilotens versioner i katalog- och filnamn: granskning-v5, v2.1, BILDDOM-v2.md


def _stampel(s):
    """kor.sh:s körnings-id (date -u +%Y%m%dT%H%M%SZ; korning-<id>.jsonl och STOPPVAKT.json) som tid i domloggens form."""
    m = re.fullmatch(r'(\d{4})(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)Z', str(s or ''))
    return '%s-%s-%sT%s:%s:%sZ' % m.groups() if m else ''


def kedjan():
    """Det tänkta flödet: tabellen under README.md:s rubrik "Kedjan från kundunderlag till leverans", grundkällan för vem
    som startar vad. Läses som den står; en rad som inte har fyra celler gör tabellen oläslig i stället för att tappas."""
    t = las_text(ROOT / 'README.md') or ''
    i = t.find(KEDJAN)
    if i < 0:
        return {'fel': 'README.md saknar avsnittet "%s"' % KEDJAN[3:]}
    rader = []
    for r in t[i:].split('\n')[1:]:
        if r.startswith('## '):
            break
        if not r.startswith('|') or set(r) <= set('|-: '):
            continue
        c = [x.strip() for x in r.strip().strip('|').split('|')]
        if len(c) != 4:
            return {'fel': 'en rad i tabellen i README.md har %d celler i stället för fyra' % len(c)}
        if c[0] != 'Steg':
            rader.append({'steg': _inline(c[0]), 'vem': _inline(c[1]), 'resultat': _inline(c[2]),
                          'saknas': '' if c[3] in ('–', '-', '') else _inline(c[3])})
    return {'kalla': 'README.md', 'steg': rader} if rader else {'fel': 'tabellen i README.md gick inte att läsa'}


def flode_slugar():
    """Kunderna som har något av kedjans filer (inte provens fixturer eller dashboardens egna kataloger)."""
    namn = set()
    for rot in (UNDERLAG, KUNDER):
        if rot.is_dir():
            namn.update(p.name for p in rot.iterdir() if p.is_dir() and SLUG.match(p.name) and p.name not in INTE_KUNDER
                        and not p.name.startswith(('rokprov', 'prov-', 'pt-')))
    return sorted(s for s in namn if (UNDERLAG / s / 'BRIEF.md').is_file() or (UNDERLAG / s / 'atelje' / 'STATUS.json').is_file()
                  or (KUNDER / s / 'prov' / 'STATUS.json').is_file())


def _fil(p, text=None):
    """En fil som steget producerat: sökvägen, en länk när dashboarden får visa filen, ändringstiden och en kort hash
    (beräknad nu; inget i körningen låser den)."""
    p = Path(p)
    if not p.is_file() or p.is_symlink():
        return None
    rel_ = p.relative_to(ROOT).as_posix()
    k = _kanonisk(rel_) if rel_.split('/')[0] in ('underlag', 'kunder') else None
    rel_ = k[0] if k and k[1] else rel_  # sökvägen och länken är den verkliga filens (granskningen av r99, BÖR-1)
    visbar = bool(k and k[1]) and _tillaten(rel_) and _ett_namn(k[1]) and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.md', '.json', '.txt')
    tid = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return {'text': text or p.name, 'sokvag': rel_, 'lank': '/fil/' + rel_ if visbar else None, 'tid': tid,
            'sha': hashlib.sha256(p.read_bytes()).hexdigest()[:12]}


def _steg(nr, namn, status, **falt):
    if status not in STATUSAR:
        raise ValueError('okänd status %r' % status)
    ut = {'nr': nr, 'namn': namn, 'status': status, 'underlag': [], 'utfall': [], 'kontroller': [], 'beslut': [], 'brister': [], 'nasta': ''}
    ut.update(falt)
    return ut



def flodesbesked(slug, blind=False):
    """Fem separata besked från befintliga slutposter, aldrig härledda ur filers datum."""
    import ateljeslut
    import korslut
    poster = [p for p in (korslut.aktuell(KUNDER / slug), ateljeslut.aktuell(slug)) if isinstance(p, dict)]
    # en kort post om en start som stannade före körningen ersätter ingen post (ateljeslut.stopp, korslut.TYP_STOPP) och får
    # inte dölja det gällande beskedet (GR-20261008-r117-claude#A4); dess skäl står i brister
    stopp = [p for p in poster if p.get('typ') in (korslut.TYP_STOPP, ateljeslut.TYP_STOPP)]
    poster = [p for p in poster if p.get('typ') not in (korslut.TYP_STOPP, ateljeslut.TYP_STOPP)]
    post = max(poster, key=lambda p: str(p.get('datum') or '')) if poster else None
    st = las_json(UNDERLAG / slug / 'atelje/STATUS.json') or {}
    pk = (post or {}).get('korning')
    poststart = (pk.get('startad') if isinstance(pk, dict) else _stampel(pk)) or (post or {}).get('datum')
    tidigare = bool(post and st.get('startad') and poststart and str(st['startad']) > str(poststart))
    if post and post.get('typ') == korslut.TYP:
        dist = str((post.get('provad') or {}).get('dist_nu') or post.get('dist_sha256') or '')[:12]
        domar = (las_json(KUNDER / slug / 'DOM.json') or {}).get('domar') or []
        blind = blind or not any(isinstance(d, dict) and dist and d.get('bygge_dist') == dist for d in domar)
    tillstand = []
    for namn, rubrik in korslut.TILLSTAND:
        p = (post.get('tillstand') or {}).get(namn) if post else None
        p = p if isinstance(p, dict) else {}
        dolt = blind and namn in ('designgranskaren_godkanner', 'agaren_godkanner', 'klart_for_leverans')
        v = None if dolt or tidigare else p.get('varde')
        status = ('dolt före ditt val' if dolt else 'saknas' if not p else 'historiskt' if tidigare or p.get('historik') is not None
                  else 'ja' if v is True else 'nej' if v is False else 'ej bedömt')
        tillstand.append({'id': namn, 'namn': rubrik, 'varde': v, 'status': status,
                          'text': 'visas efter ditt val' if dolt else 'Beskedet gäller föregående körning. ' + str(p.get('text') or '') if tidigare else str(p.get('text') or 'inget slutbesked finns'),
                          'omfattning': None if dolt else p.get('omfattning')})
    fil = None if blind or not post else post.get('slutpost')
    return {'tillstand': tillstand, 'version': (post or {}).get('dist_sha256'), 'tid': (post or {}).get('datum'),
            'brister': [] if blind else ((post or {}).get('brister') or []) + ['senare start som stannade före körningen (%s): %s' % (
                p.get('datum'), str(p.get('skal') or '')[:200]) for p in stopp if not post or str(p.get('datum') or '') > str(post.get('datum') or '')],
            'filer': [f for f in [_fil(ROOT / fil, 'slutposten för versionen') if isinstance(fil, str) else None] if f]}


def flode(slug):
    """Det som hände för kunden, i README:s nio steg, bundet till den aktuella körningen: dina val efter körningens plan,
    förfiningen efter ditt senaste val, godkännandet prövat som kor.sh prövar det (skapande.godkand_giltig) och helbygget
    prövat som korslut prövar det (korslut.ar_godkant), startat efter det godkännandet. Det som hör till en tidigare
    körning är inaktuellt, aldrig kontrollerat eller beslutat, och det som inte går att knyta till körningen är inte
    observerat (granskningen av r96, B1, B2 och R1). En arm i en blind jämförelse som du inte valt i än visas inte alls,
    som i bygge() och fil_tillaten (R3)."""
    import atelje
    import kandidater
    import korslut
    import skapande
    import prototyp as prototyp_kor
    import exportera
    import flodesstart
    if ab_oavgjord(slug):  # lika för båda armarna: inget om ateljén, provet, stoppvakten eller granskningen före valet
        return {'slug': slug, 'blind': True, 'ab_dold': True, 'korning': None, 'tid': nu(),
                'steg': [_steg(i, n, 'inte observerat') for i, n in enumerate(FLODESTEG, 1)]}
    u, k, a = UNDERLAG / slug, KUNDER / slug, UNDERLAG / slug / 'atelje'
    st = las_json(a / 'STATUS.json') or {}
    kfl = kandidatkorning(slug, st)
    # en ny körning (läget ny) vars arbetare ännu inte har arkiverat förra körningens plan, kandidater och vinnare:
    # atelje.arbeta skriver STATUS före startkontrollen och arkiverar efter den. En plan som är äldre än körningen hör till
    # förra körningen, så varken den, dess kandidater eller dina val efter den räknas hit (omgranskningen av r96, BÖR 1).
    # En start som startkontrollen stoppade arkiverar ingenting (atelje.arbeta): statusen är då förälderns med
    # startkontroll_stopp, eller steg fel med startkontrollens besked. Förra körningens plan, förslag och val är då det
    # senaste, och villkoret ovan gäller inte (omgranskning 2 av r96, BÖR 1).
    sk_ = st.get('startkontroll') if isinstance(st.get('startkontroll'), dict) else {}
    start_stoppad = bool(st.get('startkontroll_stopp')) or (st.get('steg') == 'fel' and (
        sk_.get('status') == 'stoppad' or str(st.get('fel') or '').startswith('Startkontrollen stoppade starten')))
    plan_k = kandidater.plan_tid(slug) if kfl else ''
    forra_plan = bool(plan_k) and st.get('lage') == 'ny' and plan_k < str(st.get('startad') or '') and not start_stoppad
    blind = kfl and (forra_plan or not kandidater.domd(slug))
    steg = []

    # 1. kundunderlaget
    filer = [f for f in (_fil(u / n) for n in ('VERKSAMHET.json', 'RESEARCH.md', 'BRIEF.md', 'INNEHALL.md', 'TEXTUNDERLAG.md', 'bilder/BILDER.md')) if f]
    paket = sorted((u / 'referenser').glob('paket-v[0-9]*'), key=lambda p: int(re.sub(r'\D', '', p.name) or 0))
    if paket:
        f = _fil(paket[-1] / 'PAKET.md', 'referenspaketet %s' % paket[-1].name) or _fil(paket[-1] / 'PAKET.json', 'referenspaketet %s' % paket[-1].name)
        if f:
            filer.append(f)
    karna = [n for n in ('RESEARCH.md', 'BRIEF.md') if not (u / n).is_file()] + ([] if (u / 'INNEHALL.md').is_file() or (u / 'TEXTUNDERLAG.md').is_file() else ['INNEHALL.md'])
    steg.append(_steg(1, 'Kundunderlaget', 'skapat' if filer and not karna else 'inte observerat' if not filer else 'skapat',
                      utfall=filer, brister=(['saknas: %s' % ', '.join(karna)] if filer and karna else [])
                      + ['kandidatens fotografering och godkännande bär underlagets innehållshash; filerna ovan läses nu'],
                      nasta='Prototypen: `.venv/bin/python kontroller/prototyp.py %s` (du eller en session).' % slug))

    # 2. prototypen: research, plan och skisser
    if not st or st.get('steg') in ('forberedd', 'forbereder') or st.get('lage') == 'forbered':
        steg.append(_steg(2, 'Prototypen', 'inte påbörjat', nasta='Förbered underlaget och starta sedan referensjakt och skiss med handlingen ovan.'))
        plan_t, kand = '', []
    else:
        stegnamn = st.get('steg') or ''
        status = ('stoppat' if stegnamn == 'fel' or atelje.avbruten(st) or start_stoppad else
                  'skapat' if stegnamn in ('klar_for_bedomning', 'klar') else 'pågår')
        kv = startkvitto(slug) or {}
        plan_t = '' if forra_plan else plan_k
        kand = kandidater.sammanstall(slug) if kfl and not forra_plan else []
        underlag_ = [{'text': 'körningen startad %s (läge %s)' % (st.get('startad') or '?', st.get('lage') or '?')}]
        if kv:
            underlag_.append({'text': 'startkvitto %s: %s' % (kv.get('tid') or '?', KVITTOSTATUS.get(kv.get('status'), kv.get('status') or '?'))})
        if plan_t:
            underlag_.append({'text': 'kandidatplanen %s' % plan_t})
        elif forra_plan:
            underlag_.append({'text': 'förra körningens plan (%s) ligger kvar tills arbetaren har arkiverat den; den hör inte till den här körningen' % plan_k})
        utfall = []
        for x in kand:
            b = x.get('bilder') or {}
            bild = b.get('1440-forsta') or b.get('390-forsta')
            utfall.append({'text': '%s · %s · version %s · %s varv' % (x.get('etikett') or '?', x.get('statustext') or x.get('status'),
                                                                       (x.get('version') or '–')[:12], x.get('varv') or 0),
                           'lank': '/fil/' + bild if bild and fil_tillaten(bild) else None})
        kontroller = []
        if kv:
            kontroller.append({'text': 'startkontrollen: %s' % KVITTOSTATUS.get(kv.get('status'), kv.get('status') or '?')})
        if (a / 'PLANPROVNING.json').is_file():
            kontroller.append({'text': 'planprövningen gjord'})
        if kand:
            kontroller.append({'text': '%d av %d förslag klara att bedöma' % (sum(1 for x in kand if x.get('status') in kandidater.VISBARA), len(kand))})
        brister = []
        if stegnamn == 'fel' and st.get('fel'):
            brister.append(str(st['fel'])[:300])
        elif start_stoppad:  # förälderns status med startkontrollens stopp (atelje.arbeta)
            brister.append(str((st.get('startkontroll_stopp') or {}).get('fel') or 'startkontrollen stoppade starten')[:300])
        if blind:
            kontroller.append({'text': 'skisskritiken och bristerna visas efter ditt första beslut'})
        else:
            for x in kand:
                n_ = len(x.get('brister') or []) + len(x.get('design_fel') or [])
                if n_:
                    brister.append('%s: %d brister eller DESIGN.md-fel' % (x.get('etikett') or x.get('id'), n_))
        steg.append(_steg(2, 'Prototypen', status, underlag=underlag_, utfall=utfall, kontroller=kontroller, brister=brister,
                          nasta='Ditt val i vyn Prototyp.' if status == 'skapat' else
                          'Startkontrollen stoppade starten, och förra körningens förslag och val står kvar: starta om när '
                          'verktygslådan fungerar (startkontrollens kvitto).' if start_stoppad else
                          'Ta vid med `.venv/bin/python kontroller/atelje.py %s --fortsatt`, eller börja om.' % slug if status == 'stoppat' else ''))

    # 3. ditt val i den här körningen: i kandidatflödet domarna efter körningens plan (samma gräns som kandidater.domd,
    #    som blindningen följer), i det äldre flödet domarna som bär körningens starttid (prototyp_domd). Utan plan eller
    #    körning finns inget val i körningen, och en tidigare körnings domar räknas aldrig hit (granskningen av r96, B2).
    egna = [d for d in skapande.domar(slug, UNDERLAG) if d.get('kalla') in skapande.AGAREN]
    if kfl:
        domar = [d for d in egna if plan_t and str(d.get('tid') or '') > plan_t]
    else:
        domar = [d for d in egna if st.get('startad') and st['startad'] in str(d.get('avser') or '')]
    aldre = [d for d in egna if d not in domar]
    tidigare = [{'text': '%d av dina domar hör inte till den här körningen och räknas inte här (den senaste %s)' % (len(aldre), aldre[-1].get('tid') or '?')}] if aldre else []
    namn = {x['id']: x.get('etikett') for x in kand}
    if domar:
        sista = domar[-1]['beslut']
        steg.append(_steg(3, 'Ditt val', 'beslutat', underlag=tidigare, beslut=[{'tid': d.get('tid'), 'text': '%s%s%s' % (
            d.get('beslut'), (' · ' + ', '.join('%s (%s)' % (namn.get(c.get('id'), c.get('id')), str(c.get('version') or '')[:12])
                                                for c in d.get('kandidater') or [] if isinstance(c, dict))) if d.get('kandidater') else '',
            (' · ' + re.sub(r'\s+', ' ', str(d.get('text') or ''))[:160]) if d.get('text') else '')} for d in domar[-5:]],
            nasta={'valj': 'Förfiningen: `prototyp.py %s` igen (läget valda).' % slug, 'putsa': 'Förfiningen: `prototyp.py %s` igen.' % slug,
                   'godkand': 'Helbygget: `./kor.sh %s "<verksamhet>"`.' % slug, 'ny_riktning': 'Omtaget: `prototyp.py %s`.' % slug,
                   'forkasta': 'Omtaget: `prototyp.py %s`.' % slug}.get(sista, 'Fortsätt i vyn Prototyp.')))
    else:
        steg.append(_steg(3, 'Ditt val', 'väntar på ägaren' if steg[-1]['status'] == 'skapat' else 'inte påbörjat', underlag=tidigare))

    # 4. förfiningen efter ditt senaste val (valj eller putsa) i körningen, ur kandidatens förfiningspost
    #    (kandidater.forfina_kandidat: forfining_pagar medan den pågår, forfining när den är klar för just det valet). En
    #    förfining som inte gav någon ny version står kvar på den valda versionen och är underkänd, en som pågår visas
    #    så, och en som stannade med körningen är stoppad (granskningen av r96, R2). En förfining som föll med ett
    #    undantag lämnar ingen post för valet: kandidater.forfina_valda återställer kandidaten till vald med skälet, och
    #    körningen slutar som vanligt. När körningen efter valet är avslutad och en vald kandidat saknar post för valet är
    #    förfiningen underkänd med kandidatens skäl, och utan skäl inte observerad (omgranskningen av r96, R2-rest).
    vd = next((d for d in reversed(domar) if d.get('beslut') in ('valj', 'putsa')), None) if kfl else None
    # valets förfining är den körning som bär valet i fältet dom (kandidater.forfina_valda skriver det, och --fortsatt av en
    # förfining för det vidare); en annan körning efter valet, som utforskningen med --fortsatt, är det inte (omgranskning 2)
    efter = bool(vd) and st.get('dom') == vd.get('tid')
    lagen, ids = [], kandidater.lista(slug) if vd else []
    for c in (vd or {}).get('kandidater') or []:
        kid = c.get('id') if isinstance(c, dict) else None
        if kid not in ids:
            continue
        s_ = kandidater.las_status(slug, kid)
        f_ = s_.get('forfining') or {}
        if s_.get('forfining_pagar') and s_.get('status') == 'under_arbete':
            lage = 'pagar'
        elif f_.get('dom') and f_.get('dom') == vd.get('tid'):
            lage = 'ny' if s_.get('version') and s_.get('version') != f_.get('fran') else 'ingen'
        elif efter and st.get('steg') in atelje.AVSLUTADE:  # körningen är klar, men kandidaten har ingen post för valet
            lage = 'fallen' if str(s_.get('skal') or '').strip() else 'okand'
        else:
            lage = 'ej'
        lagen.append((namn.get(kid) or kid, s_, lage))
    if lagen:
        dod = efter and (st.get('steg') == 'fel' or atelje.avbruten(st))
        oklara = any(l_ in ('pagar', 'ej') for _, _, l_ in lagen)
        status = ('stoppat' if dod and oklara else
                  'pågår' if any(l_ == 'pagar' for _, _, l_ in lagen) or (efter and oklara and st.get('steg') not in atelje.AVSLUTADE) else
                  'skapat' if any(l_ == 'ny' for _, _, l_ in lagen) else
                  'underkänt' if any(l_ in ('ingen', 'fallen') for _, _, l_ in lagen) else
                  'inte observerat' if any(l_ == 'okand' for _, _, l_ in lagen) else 'inte påbörjat')

        def beskriv(s_, l_):
            if l_ == 'ny':
                return 'från %s till %s' % (str((s_.get('forfining') or {}).get('fran') or '?')[:12], str(s_.get('version'))[:12])
            if l_ == 'ingen':
                return 'ingen ny version; den valda %s står kvar' % str(s_.get('version') or '?')[:12]
            if l_ == 'fallen':
                return 'föll utan ny version; den valda %s står kvar' % str(s_.get('version') or '?')[:12]
            if l_ == 'okand':
                return 'inget besked: körningen efter valet är klar, men kandidaten har varken förfiningens post eller ett skäl'
            if l_ == 'pagar':
                return 'pågår, från %s' % str((s_.get('forfining_pagar') or {}).get('fran') or '?')[:12]
            return 'inte påbörjad'
        pass_ = [{'text': '%s: %s %s' % (e, rec.get('pass'), ('genomfört' if rec.get('genomford') else 'inte genomfört') + (
            ' (inget observerat verktygs- eller MCP-anrop med resultat)' if rec.get('genomford') is False and rec.get('anvanda_verktyg') == [] else ''))}
                 for e, s_, l_ in lagen if l_ == 'ny' for k_, rec in sorted((s_.get('kompetens') or {}).items()) if k_.startswith('fordjupa:')]
        brister = [('%s: %s' % (e, s_.get('skal')))[:300] for e, s_, l_ in lagen if l_ in ('ingen', 'fallen') and s_.get('skal')]
        brister += ['%s: förfiningen efter valet gav inget besked som går att läsa' % e for e, s_, l_ in lagen if l_ == 'okand']
        if any(l_ == 'ny' for _, _, l_ in lagen):
            brister.append('förfiningens resultatversion sparas inte (bara versionen den utgick från); "till" är kandidatens version nu')
        steg.append(_steg(4, 'Förfiningen', status, utfall=[{'text': '%s · %s' % (e, beskriv(s_, l_))} for e, s_, l_ in lagen],
                          kontroller=pass_, brister=brister))
    else:
        steg.append(_steg(4, 'Förfiningen', 'inte påbörjat'))

    # 5. godkännandet, prövat som kor.sh prövar det (skapande.godkand_giltig): ägarens senaste dom är just godkännandet,
    #    ingen körning har startat efter det och de godkända filerna är oförändrade (granskningen av r96, R1)
    v = las_json(a / 'VINNARE.json') or {}
    g = v.get('godkand') if isinstance(v.get('godkand'), dict) else None
    g_ok, g_skal = skapande.godkand_giltig(slug, UNDERLAG, KUNDER) if g else (False, 'inget godkännande')
    if g:
        vad = namn.get(v.get('kandidat')) or v.get('kandidat') or 'startsidan'
        steg.append(_steg(5, 'Godkännandet', 'kontrollerat' if g_ok else 'inaktuellt',
                          beslut=[{'tid': g.get('tid'), 'text': 'godkänd: %s%s' % (vad, (', version %s' % str(v.get('version'))[:12]) if v.get('version') else '')}],
                          kontroller=[{'text': ('godkännandet gäller, prövat som kor.sh prövar det (%s)' if g_ok else
                                                'godkännandet gäller inte, prövat som kor.sh prövar det: %s') % g_skal}],
                          nasta='Helbygget: `./kor.sh %s "<verksamhet>"`.' % slug if g_ok else ''))
    else:
        steg.append(_steg(5, 'Godkännandet', 'väntar på ägaren' if steg[3]['status'] == 'skapat' else 'inte påbörjat'))

    # 6. helbygget. Bundet till körningen när kor.sh startade det efter ett godkännande som gäller nu: kor.sh bygger bara
    #    från ett giltigt, och vilket godkännande bygget utgick från sparas inte, så tiden är det som binder dem. Utan
    #    körning i skapandeflödet står bygget för sig. Kontrollerat bara när korslut skulle godkänna det bygge som ligger
    #    i dist/ nu (korslut.vald_granskning och ar_godkant, slutkod 0; granskningen av r96, B1). Ett bygge från före
    #    körningen eller godkännandet är inaktuellt, och ett som inte går att knyta till godkännandet inte observerat (B2).
    prov = las_json(k / 'prov' / 'STATUS.json')
    dom_b = [d for d in ((las_json(k / 'DOM.json') or {}).get('domar') or []) if isinstance(d, dict)]
    s6, bygg_t, bygge_id, galler = 'inte påbörjat', '', '', []
    if not prov:
        steg.append(_steg(6, 'Helbygget', s6))
    else:
        stopp = las_json(k / 'prov' / 'STOPPVAKT.json') or {}
        loggar = sorted(k.glob('korning-*.jsonl'))
        korning_id = loggar[-1].name[len('korning-'):-len('.jsonl')] if loggar else stopp.get('korning')
        start_b = _stampel(korning_id)
        bygg_t = start_b or str(prov.get('tid') or '')
        bygge_id = str(prov.get('dist_sha256') or '')[:12]
        start_r = str(st.get('startad') or '')
        grindar = prov.get('grindar') or {}
        kontroller = [{'text': 'provet %s: %d av %d grindar gröna' % (prov.get('tid') or '?', sum(1 for x in grindar.values() if (x.get('ok') if isinstance(x, dict) else x)), len(grindar))}]
        brister = []
        if not (k / 'sajt' / 'package.json').is_file():
            s6 = 'inaktuellt'
            brister.append('sajten är borttagen (ett omtag); provet gäller en sajt som inte finns')
        elif st and bygg_t and bygg_t < start_r:
            s6 = 'inaktuellt'
            brister.append('bygget (%s) är från före körningen i skapandeflödet (startad %s)' % (bygg_t, start_r))
        elif st and g_ok and start_b and start_b < g['tid']:
            s6 = 'inaktuellt'
            brister.append('kor.sh startade bygget %s, före godkännandet %s' % (start_b, g['tid']))
        elif st and not (g_ok and start_b):
            s6 = 'inte observerat'
            brister.append('bygget kan inte knytas till körningens godkännande: %s' % ('kor.sh:s körning är inte observerad' if g_ok else g_skal))
        else:
            try:
                g_hel, nu_hash, _, gfel = korslut.vald_granskning(k, korning_id)
                ok6, skal6 = korslut.ar_godkant(k, prov, stopp, None if gfel else g_hel, korning_id)
                s6 = 'kontrollerat' if ok6 else 'skapat' if prov.get('ok') else 'underkänt'
                bygge_id = str(nu_hash or '')[:12]
                if not ok6:
                    brister.append('korslut godkänner inte bygget: %s' % (gfel or skal6))
            except Exception as e:  # noqa: BLE001 — ett bygge som inte går att pröva är inte observerat
                s6 = 'inte observerat'
                brister.append('bygget kunde inte prövas med korslut: %s' % str(e)[:200])
            brister.append('korsluts slutkod sparas inte; statusen är korsluts prövning, gjord nu')
            brister.append(('bygget sparar inte vilket godkännande det utgick från: kor.sh prövade godkännandet när bygget startade (%s), '
                            'efter godkännandet %s' % (start_b, g['tid'])) if st else
                           'bygget sparar inte vilket godkännande det utgick från, och ingen körning i skapandeflödet finns att knyta det till')
        galler = [d for d in dom_b if bygge_id and d.get('bygge_dist') == bygge_id]
        gr = granskningen(slug, bool(galler))  # granskarens dom visas först efter din dom över just det här bygget
        if stopp:
            kontroller.append({'text': 'stoppvakten: %s' % str(stopp.get('skal') or ('släppte bygget' if stopp.get('slapp') else 'höll kvar bygget'))[:240]})
        if gr.get('finns'):
            kontroller.append({'text': 'granskningen: %d omgångar%s' % (gr.get('rundor') or 0, ', domen visas efter din dom över det här bygget' if gr.get('dold') else ', %s' % ('godkänd' if gr.get('godkand') else 'underkänd'))})
        steg.append(_steg(6, 'Helbygget', s6, kontroller=kontroller, brister=brister,
                          underlag=[{'text': 'dist %s' % str(prov.get('dist_sha256') or '?')[:12]},
                                    {'text': 'kor.sh-körningen %s' % korning_id if korning_id else 'kor.sh-körningen är inte observerad'}],
                          utfall=[f for f in (_fil(k / 'prov' / 'PROV.md', 'provets rapport'), _fil(k / 'RAPPORT.md', 'byggets rapport')) if f]))

    helpost = korslut.aktuell(k)
    if isinstance(helpost, dict):
        t = helpost.get('tillstand') or {}
        tekniskt = t.get('tekniskt_godkant') or {}
        design = t.get('designgranskaren_godkanner') or {}
        # kontrollerat betyder att korslut godkänner: tekniskt och designgranskaren (som B1 ovan); ett tekniskt ja utan godkänd
        # granskning är skapat med bristen, aldrig grönt (GR-20261008-r117-claude#C3)
        s6 = ('inaktuellt' if tekniskt.get('historik') is not None or design.get('historik') is not None
              else 'kontrollerat' if tekniskt.get('varde') is True and design.get('varde') is True
              else 'underkänt' if tekniskt.get('varde') is False
              else 'skapat' if tekniskt.get('varde') is True else 'inte observerat')
        bygg_t = str(helpost.get('datum') or '')
        bygge_id = str((helpost.get('provad') or {}).get('dist_nu') or helpost.get('dist_sha256') or '')[:12]
        galler = [d for d in dom_b if bygge_id and d.get('bygge_dist') == bygge_id]
        steg[5] = _steg(6, 'Helbygget', s6,
                         underlag=[{'text': 'körning %s · dist %s' % (helpost.get('korning'), bygge_id or 'saknas')}],
                         kontroller=[{'text': 'Tekniskt: ' + str(tekniskt.get('text') or 'ej bedömt')},
                                     {'text': 'Designgranskaren: ' + (str(design.get('text') or 'ej bedömt') if galler else
                                                                      'domen visas efter din dom över det här bygget')}],
                         brister=(['korslut godkänner inte: designgranskaren har inte godkänt bygget'] if s6 == 'skapat' else [])
                                 + ([] if blind or not galler else list(helpost.get('brister') or [])),
                         utfall=[] if blind or not galler else [f for f in (_fil(k / 'prov/PROV.md'), _fil(k / 'RAPPORT.md')) if f])

    # 7. din dom över bygget: beslutad bara över just det bygge som ligger i dist/ (domens bygge_dist, spara_dom); en dom
    #    över ett annat bygge är inaktuell (granskningen av r96, B2)
    def domrader(ds):
        return [{'tid': d.get('tid'), 'text': '%s · bygget %s' % (str((d.get('svar') or {}).get('namn') or 'dom')[:160], d.get('bygge_dist') or '?')} for d in ds]
    if s6 in ('inaktuellt', 'inte observerat'):
        steg.append(_steg(7, 'Din dom över bygget', s6 if dom_b else 'inte påbörjat', beslut=domrader(dom_b[-3:]),
                          brister=['domen gäller ett bygge som inte hör till körningen'] if dom_b else []))
    elif galler:
        steg.append(_steg(7, 'Din dom över bygget', 'beslutat', beslut=domrader(galler[-3:])))
    elif s6 != 'inte påbörjat':
        steg.append(_steg(7, 'Din dom över bygget', 'väntar på ägaren',
                          brister=['%d domar gäller ett annat bygge (det senaste %s), inte det som ligger i dist/ nu (%s)' % (
                              len(dom_b), dom_b[-1].get('bygge_dist') or '?', bygge_id or 'inte observerat')] if dom_b else []))
    else:
        steg.append(_steg(7, 'Din dom över bygget', 'inte observerat' if dom_b else 'inte påbörjat',
                          brister=['domen kan inte knytas till ett bygge: provet saknas'] if dom_b else []))

    # 8. Ny export har ett innehållsbundet kvitto. Äldre kataloger utan kvitto
    # kan öppnas men filtid räcker aldrig för ett aktuellt exportbesked.
    e = exportera.aktuell(slug)
    if e:
        s8 = 'skapat' if e.get('aktuell') else 'inaktuellt' if e.get('ok') else 'stoppat'
        kontroll = (e.get('kontroller') or {}).get('exportbygge') or {}
        steg.append(_steg(8, 'Exporten till kundrepo', s8,
                          underlag=[{'text': 'exportversion %s · källversion %s' % (str(e.get('export_sha256') or 'saknas')[:12], str(e.get('kallor_sha256') or 'saknas')[:12])}],
                          kontroller=[{'text': 'Exportens byggprov: ' + ('godkänt' if kontroll.get('varde') is True else 'underkänt' if kontroll.get('varde') is False else 'inte kört')}],
                          brister=[str(e.get('fel'))] if e.get('fel') else ['exportfilerna är inte samma som i kvittot, eller källorna har ändrats'] if not e.get('aktuell') else [],
                          utfall=[] if blind else [f for f in [_fil(Path(e['kvitto']), 'exportens versionskvitto') if e.get('kvitto') else None] if f]))
    else:
        pj = k / 'kundrepo/package.json'
        s8 = 'inte observerat' if pj.exists() or pj.is_symlink() else 'inte påbörjat'
        steg.append(_steg(8, 'Exporten till kundrepo', s8,
                          brister=['äldre export utan versionskvitto; dess kontroller och aktualitet är inte belagda'] if s8 == 'inte observerat' else []))

    import kundrepo
    kr = kundrepo.las_kvitto(slug)
    if kr:  # kundprojektets eget repo (kundrepo.py): identiteten, fjärrepot och Vercel-kopplingen som kvittot säger
        fj, vc, pu = kr.get('fjarr') or {}, kr.get('vercel') or {}, kr.get('senaste_push') or {}
        steg[-1]['underlag'].append({'text': 'kundrepo %s: lokalt %s · fjärr %s%s · Vercel %s%s' % (
            kr.get('namn'), 'git' if kundrepo.ar_repo(kundrepo.repo(slug)) else 'saknas', fj.get('status') or 'inte observerat',
            ' (%s)' % fj['adress'] if fj.get('adress') else (' (%s)' % fj['fel']) if fj.get('fel') else '',
            vc.get('status') or 'inte kopplat', ' · senaste push %s %s' % ('ok' if pu.get('ok') else 'föll', str(pu.get('commit') or '')[:12]) if pu else '')})
        if e and e.get('commit'):
            steg[-1]['underlag'].append({'text': 'exportens commit i kundrepot: %s' % str(e['commit'])[:12]})
    # 9. leveransen: förhandsvisningens kvitto (kundrepo.preview) när det finns; produktion sparas aldrig av ett verktyg, så
    #    steget visas aldrig som kontrollerat
    pv = kundrepo.preview_aktuell(slug)
    if pv:
        s9 = 'skapat' if pv.get('aktuell') else 'inaktuellt' if pv.get('status') == 'klar' else 'stoppat'
        steg.append(_steg(9, 'Leveransen', s9,
                          underlag=[{'text': 'förhandsvisning %s · commit %s · export %s · %s' % (pv.get('url') or 'saknas', str(pv.get('commit') or '')[:12], pv.get('export') or '?', pv.get('tid'))}],
                          kontroller=[{'text': 'Vercel: %s (förhandsvisning, inte produktion)' % (pv.get('vercel_status') or pv.get('status'))}],
                          brister=(['förhandsvisningen gäller en annan commit eller export än den aktuella'] if pv.get('status') == 'klar' and not pv.get('aktuell') else list(pv.get('hinder') or []))
                                  + ['förhandsvisning är inte produktion; domän, riktiga formulär och drift är inte verifierade'],
                          utfall=[] if blind else [f for f in [_fil(Path(pv['fil']), 'förhandsvisningens kvitto') if pv.get('fil') else None] if f]))
    else:
        steg.append(_steg(9, 'Leveransen', 'inte observerat' if s8 in ('skapat', 'inte observerat') else 'inte påbörjat',
                          brister=['exporten är förberedelse; verklig driftsättning, domän och formulärmottagning är inte verifierade av den']))
    return {'slug': slug, 'blind': blind, 'ab_dold': False,
            'korning': {'startad': st.get('startad'), 'steg': st.get('steg'), 'lage': st.get('lage')} if st else None,
            'steg': steg, 'tid': nu(), 'besked': flodesbesked(slug, blind=blind),
            'handlingar': prototyp_kor.handlingar(slug), 'startmiljo': flodesstart.startmiljo()}


def _pilotversion(namn, kanda):
    """Versionen ur ett katalog- eller filnamn i pilotens moment (granskning-v5, v2.1, BILDDOM-v2): ett v-nummer eller ett
    versions-id som posten själv använder (aktuell, versioner, varv); annars None, inte observerat."""
    n = namn[len('granskning-'):] if namn.startswith('granskning-') else namn
    return n if PILOTVERSION.fullmatch(n) or n in kanda else None


def figma_pilot():
    """Figma-metodprovets moment (underlag/figma-pilot/<moment>/VERSION.json), bundna till version (granskningen av r96,
    B3). Statusen "kontrollerat" eller "underkänt" i posten gäller bara när den aktuella versionen själv är bedömd, med en
    bedömning i bedomningar/ som bär versionen i namnet (BILDDOM-v5.md). Gäller bedömningen en tidigare version är den
    aktuella bara skapad, och utan någon versionsmärkt bedömning är statusen inte observerad. Varje bild och bedömning
    bär versionen ur sitt katalog- eller filnamn (granskning-v5/, v2.1/), annars "inte observerat"; bilderna är den
    aktuella versionens och den senast bedömdas."""
    ut = []
    for f in sorted((UNDERLAG / 'figma-pilot').glob('*/VERSION.json')):
        d = las_json(f) or {}
        m = f.parent
        aktuell = str(d.get('aktuell') or '')
        kanda = {aktuell} | {str(x) for n in ('versioner', 'varv') if isinstance(d.get(n), dict) for x in d[n]}
        kanda.discard('')
        bedomningar = []
        for p in sorted(m.glob('bedomningar/*.md')):
            ver = _pilotversion(p.stem.rsplit('-', 1)[1], kanda) if '-' in p.stem else None
            x = _fil(p, '%s · %s' % (p.name, ('gäller ' + ver) if ver else 'version inte observerad'))
            if x:
                bedomningar.append(dict(x, version=ver or 'inte observerat'))
        bedomda = sorted({x['version'] for x in bedomningar if x['version'] != 'inte observerat'},
                         key=lambda v_: ([int(t) for t in re.findall(r'\d+', v_)], v_))
        dekl = d.get('status') if d.get('status') in STATUSAR else 'inte observerat'
        status = dekl
        kontroller = [{'text': 'bedömda versioner: %s' % (', '.join(bedomda) if bedomda else 'ingen bedömning i bedomningar/ bär en version i namnet')}]
        if dekl in ('kontrollerat', 'underkänt') and not (aktuell and aktuell in bedomda):
            status = 'skapat' if aktuell and bedomda else 'inte observerat'
            kontroller.append({'text': 'statusen "%s" i VERSION.json gäller %s' % (dekl, (
                'en tidigare version: bedömningen gäller %s, inte den aktuella %s' % (bedomda[-1], aktuell)) if aktuell and bedomda else
                'ingen bedömd version som går att knyta till den aktuella')})
        kat = [(p, _pilotversion(p.name, kanda)) for p in sorted(m.iterdir()) if p.is_dir() and not p.is_symlink()]
        valda = [p for p, v_ in kat if aktuell and v_ == aktuell]
        valda = [p for p in valda if not p.name.startswith('granskning-')] or valda  # den aktuella versionens egna bilder först
        if bedomda and bedomda[-1] != aktuell:  # och granskningsbilderna för den senast bedömda versionen
            valda += [p for p, v_ in kat if v_ == bedomda[-1] and p.name.startswith('granskning-')] or [p for p, v_ in kat if v_ == bedomda[-1]]
        if not any(any(p.glob('*.png')) for p in valda):  # ingen katalog bär någon av dem: den senaste bildkatalogen
            for monster in ('granskning', 'bilder', 'jamforelse'):
                valda = [p for p, _ in kat if (p.name.startswith(monster) if monster == 'granskning' else p.name == monster) and any(p.glob('*.png'))][-1:]
                if valda:
                    break
        version_av = dict(kat)
        bilder = [dict(x, version=version_av.get(p) or 'inte observerat') for p in valda
                  for x in (_fil(b, '%s/%s' % (p.name, b.name)) for b in sorted(p.glob('*.png'))[-8:]) if x]
        ut.append({'id': m.name, 'moment': d.get('moment'), 'status': status, 'status_i_posten': dekl,
                   'status_skal': d.get('status_skal') or '', 'aktuell': aktuell or None, 'bedomda': bedomda, 'kontroller': kontroller,
                   'tid': d.get('tid'),
                   'figma': {'fil': (d.get('figma') or d.get('design') or {}).get('fil') or (d.get('design') or {}).get('figma'),
                             'noder': (d.get('figma') or d.get('design') or {}).get('noder')},
                   'bedomningar': bedomningar, 'bilder': bilder, 'fynd': d.get('fynd') or [], 'domar': _pilotdomar(m, d)})
    return ut


EJ = 'ej angivet'  # ett saknat värde gissas aldrig (README.md, Var information finns: rapporthuvudet)
EJ_BELAGD = 'avsändaren ej belagd'


def _pilotdomar(m, d):
    """Domarna och bedömningarna i ett pilotmoments VERSION.json (agarens_dom, inklistrad_dom, granskningar och
    bedomningar), var och en med sin version, sitt utfall och avsändaren ur fältet avsandare (ägarens uppdrag 2026-10-07,
    punkt 7). Saknas fältet för en dom eller bedömning är avsändaren inte belagd; den gissas aldrig ur fältets namn eller
    filnamnet."""
    ut = []

    def post(falt, vad, x, version=None):
        x = x if isinstance(x, dict) else {'utfall': x}
        fil = x.get('fil')
        ok = isinstance(fil, str) and fil.strip() and not Path(fil).is_absolute() and '..' not in Path(fil).parts
        ut.append({'falt': falt, 'vad': vad, 'version': str(x.get('version') or version or EJ)[:60],
                   'utfall': str(x.get('utfall') or EJ)[:400], 'tid': x.get('tid') if isinstance(x.get('tid'), str) else None,
                   'avsandare': str(x.get('avsandare') or '').strip()[:400] or EJ_BELAGD,
                   'beslutstyp': str(x.get('beslutstyp'))[:300] if x.get('beslutstyp') else None,
                   'historik': str(x.get('historik'))[:300] if x.get('historik') else None, 'fil': _fil(m / fil) if ok else None})
    for falt in ('agarens_dom', 'inklistrad_dom'):
        if isinstance(d.get(falt), dict):
            post(falt, 'dom', d[falt])
    for x in d.get('granskningar') if isinstance(d.get('granskningar'), list) else []:
        post('granskningar', 'granskning', x)
    for v, x in (d.get('bedomningar') or {}).items() if isinstance(d.get('bedomningar'), dict) else ():
        post('bedomningar', 'bedömning', x, version=v)
    return ut


# --- Dokumentation och rapporter (ägarens uppdrag 2026-10-06, punkt 8, och 2026-10-07, punkt 9): samma källor och
# metadata som filstrukturen använder (README.md, Var information finns), lästa vid varje anrop; ingen egen förteckning.
# Filer under underlag/ och kunder/ visas genom _fil och fil_tillaten, och en kunds körning som flödesvyn visar den
# (flode), utan det som hör till kandidaterna före ägarens första val. Repots publika instruktioner, som platsregeln
# och CLAUDE.md pekar på, visas av /api/dokument. Ett utfall är historik: det gäller den granskade identiteten. Att
# förteckningens filer finns och stämmer med sin sha256 är integritet, ingen verifiering av slutsatserna. ---

RAPPORTFALT = ('id', 'titel', 'typ', 'uppdrag', 'kund', 'systemdel', 'moment', 'forfattare', 'datum', 'granskad_identitet',
               'rapportstatus', 'bedomningsutfall', 'forhallande', 'foregaende', 'ersatt_av', 'underlag', 'beslut', 'atgarder',
               'rattelser', 'giltighet')  # de två sista är valfria: rättade slutsatser och giltighet (granskningen av r99, BÖR-7)
UTFALLSKLASSER = (('godkänt', ('godkänt', 'godkänd')), ('underkänt', ('underkänt', 'underkänd')),
                  ('ofullständigt', ('ofullständig',)), ('ej bedömt', ('ej bedömt', 'ej bedömd', 'inte bedömt', 'inte bedömd')))
RAPPORTSTATUSAR = ('färdig', 'utkast', 'ersatt')
AGARENS_DEL = re.compile(r'^ägarens (?:dom|beslut|bedömning)\b', re.I)  # en del av utfallet som är ägarens egen (BÖR-4)
HUVUD_NYCKEL = re.compile(r'^([A-Za-z_][\w-]*):(?:[ \t]+(.*?))?[ \t]*$')
HUVUD_DEL = re.compile(r'^(?:[ \t]+(?:-[ \t]+)?|-[ \t]+)(\S.*?)[ \t]*$')
INTEGRITET = {'ok': 'filen finns och stämmer med förteckningens sha256', 'saknas': 'filen saknas',
              'fel_sha': 'filen har ändrats sedan registreringen (en annan sha256)', 'ej_kontrollerade': 'kunde inte kontrolleras'}
INTEGRITET_NOT = ('Integritet, ingen verifiering: att en fil finns och stämmer med förteckningens sha256 säger att den är '
                  'oförändrad sedan registreringen, inte att historiken är fullständig eller att slutsatserna stämmer.')
# koden som hänvisar till granskningar (granskningen av rNN); filerna som de ligger, inte en egen lista
KODFILER = ('kor.sh', 'dashboard.sh', 'dashboard/*.py', 'dashboard/*.html', 'kontroller/*.py', 'kontroller/*.sh',
            'kontroller/*.mjs', 'kontroller/rokprov/revision/*.py', '.claude/hooks/*')
GRANSKNINGSREF = re.compile(r'\b(?:[Oo]m|[Ss]lut)?[Gg]ranskning(?:en|arna|ar)? av (r\d+[a-z]?)'
                            r'((?:(?:,\s*(?:och\s+)?|\s+och\s+)(?:r\d+[a-z]?|[A-ZÅÄÖ]{1,4}[- ]?\d+[a-z]?))*)')
RUNDA = re.compile(r'r\d+[a-z]?')
TILLAGG_RUBRIK = re.compile(r'^Tillägg (\d{4}-\d\d-\d\d)(?:, ([^:]+))?: (.+)$')
ERSATT_MARKOR = re.compile(r'\*\*(Delvis ersatt av|Ersatt av):\*\*\s*(.+?)(?=\n[ \t]*\n|\n[ \t]*(?:\d+\.|[-*])[ \t]|\Z)', re.S)
TILLAGG_REF = re.compile(r'tillägget "?(\d{4}-\d\d-\d\d)')


def _avcitera(v):
    v = v.strip()
    return v[1:-1].strip() if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'' else v


def rapporthuvud(text):
    """Rapporthuvudet (README.md, Var information finns): YAML mellan --- tolkat med en liten tolk som bara kan
    `nyckel: värde`, listor med `  - ` och indragna rader under en nyckel utan värde (som granskad_identitet med en rad
    per del). Ger (fälten, läget): ok, saknas (filen börjar inte med ---) eller trasigt (inget avslutande ---, en rad som
    inte går att tolka, inte text). Ett trasigt huvud ger inga fält, så att inget värde gissas ur en halv rad, och tolken
    kastar aldrig."""
    if not isinstance(text, str):
        return {}, 'trasigt'
    rader = text.split('\n')
    if rader[0].rstrip() != '---':
        return {}, 'saknas'
    falt, sist = {}, None
    for r in rader[1:400]:
        r = r.rstrip('\r')
        if r.rstrip() == '---':
            return falt, 'ok'
        if not r.strip() or r.lstrip().startswith('#'):
            continue
        m = HUVUD_NYCKEL.match(r)
        if m:
            sist = m.group(1)
            falt[sist] = _avcitera(m.group(2)) if m.group(2) else []
            continue
        m = HUVUD_DEL.match(r)
        if m and sist is not None:
            if isinstance(falt[sist], list):
                falt[sist].append(_avcitera(m.group(1)))
            else:  # en indragen fortsättning på ett värde
                falt[sist] += ' ' + m.group(1).strip()
            continue
        return {}, 'trasigt'
    return {}, 'trasigt'


def _falt(f, k):
    """Ett fält ur huvudet som text eller lista; tomt eller saknat är "ej angivet"."""
    v = f.get(k)
    if isinstance(v, list):
        v = [str(x)[:600] for x in v if str(x).strip()][:40]
        return v or EJ
    v = str(v or '').strip()[:1200]
    return v or EJ


def _text(v):
    return '; '.join(str(x) for x in v) if isinstance(v, list) else str(v or '')


def utfallsklass(v):
    """Bedömningsutfallet i en av klasserna godkänt, underkänt, ofullständigt eller ej bedömt (README.md, rapporthuvudet),
    efter hur fältet börjar; annars annat, och utan fält ej angivet."""
    t = _text(v).strip().lower()
    if not t or t == EJ:
        return EJ
    return next((namn for namn, borjan in UTFALLSKLASSER if t.startswith(borjan)), 'annat')


def _delar(t):
    """Utfallets delar, åtskilda av semikolon utanför parenteser: "godkänt mot X (a; b); ägarens dom: inte ännu" har två."""
    ut, djup, start = [], 0, 0
    for i, c in enumerate(t):
        djup += 1 if c in '([' else -1 if c in ')]' and djup else 0
        if c == ';' and not djup:
            ut.append(t[start:i])
            start = i + 1
    return [d.strip() for d in ut + [t[start:]] if d.strip()]


def utfallet(v, avsandare=None):
    """Bedömningsutfallet som ett eller flera utfall (granskningen av r99, BÖR-4): rapportens egna delar klassas var för
    sig efter hur de börjar (en del som inte börjar med en klass är en kommentar), och en del som är ägarens dom ("ägarens
    dom 2026-10-07: inte ännu") blir en egen rad med ägaren som avsändare, så att den inte skrivs över av rapportens.
    Ger (klassen, rapportens klass, ägarens domar). Klassen är blandat när delarna inte säger samma sak: då blir inget
    av dem ett godkännande i sammanfattningen."""
    t = _text(v).strip()
    if not t or t == EJ:
        return EJ, EJ, []
    egna, agaren = [], []
    for d in _delar(t):
        if AGARENS_DEL.match(d):
            dom = d.split(':', 1)[1].strip() if ':' in d else d
            agaren.append({'text': d, 'klass': utfallsklass(dom), 'avsandare': 'ägaren'})
        else:
            egna.append(d)
    klasser = [k for k in (utfallsklass(d) for d in egna) if k not in ('annat', EJ)]
    rapportens = (klasser[0] if len(set(klasser)) == 1 else 'blandat') if klasser else (utfallsklass(egna[0]) if egna else EJ)
    alla = {rapportens} | {a['klass'] for a in agaren} if egna else {a['klass'] for a in agaren}
    return (next(iter(alla)) if len(alla) == 1 else 'blandat'), rapportens, agaren


def rapportstatusklass(v):
    """Rapportstatusen (utkast, färdig eller ersatt), skild från utfallet: en färdig rapport kan underkänna resultatet."""
    t = _text(v).strip().lower()
    if not t or t == EJ:
        return EJ
    return next((s for s in RAPPORTSTATUSAR if t.startswith(s)), 'annat')


def _version(identitet):
    """Den granskade versionen kort: commiten efter ordet commit, annars den första hex-följden med en bokstav (7–40
    tecken), annars None; hela den granskade identiteten står bredvid."""
    t = _text(identitet)
    m = re.search(r'\bcommit ([0-9a-f]{7,40})\b', t) or re.search(r'(?<![0-9A-Za-z])((?=[0-9]*[a-f])[0-9a-f]{7,40})(?![0-9A-Za-z])', t)
    return m.group(1) if m else None


def _avsandare(f):
    """Avsändaren av rapportens bedömning: fältet avsandare, annars författaren (roll eller session); saknas båda är den
    inte belagd (ägarens uppdrag 2026-10-07, punkt 7). Den gissas aldrig ur filnamnet."""
    for k in ('avsandare', 'forfattare'):
        v = _falt(f, k)
        if v != EJ:
            return _text(v)
    return EJ_BELAGD


def _rapport(p, slag):
    """En rapport med sitt huvud: fälten (README.md, rapporthuvudet), rapportstatus och utfall som två skilda klasser, den
    granskade versionen och filen genom _fil (länken bara när fil_tillaten tillåter den)."""
    try:
        text = p.read_bytes().decode('utf-8')
    except (OSError, UnicodeDecodeError):
        text = None
    falt, lage = rapporthuvud(text)
    ut = {k: _falt(falt, k) for k in RAPPORTFALT}
    avsandare = _avsandare(falt)
    utfall, rapportens, agaren = utfallet(ut['bedomningsutfall'], avsandare)
    ut.update(slag=slag, huvud=lage, avsandare=avsandare, utfall=utfall, utfall_rapport=rapportens, agarens_dom=agaren,
              rapportstatus_klass=rapportstatusklass(ut['rapportstatus']), version=_version(ut['granskad_identitet']),
              rattelser=[] if ut['rattelser'] == EJ else (ut['rattelser'] if isinstance(ut['rattelser'], list) else [ut['rattelser']]),
              typgrupp=_text(ut['typ']).split(' (')[0].strip() if ut['typ'] != EJ else EJ, fil=_fil(p), forteckning=None)
    return ut


def forteckningen():
    """Förteckningens rader (underlag/granskningar/FORTECKNING.jsonl) som (rå rad, post eller None för en rad som inte går
    att tolka), och ett läsfel; (None, None) när förteckningen inte finns."""
    f = UNDERLAG / 'granskningar' / 'FORTECKNING.jsonl'
    if f.is_symlink() or not f.is_file():
        return None, None
    try:
        rader = f.read_text(encoding='utf-8').split('\n')
    except (OSError, UnicodeDecodeError) as e:
        return [], '%s: %s' % (type(e).__name__, str(e)[:160])
    ut = []
    for r in rader:
        if r.strip():
            try:
                d = json.loads(r)
            except ValueError:
                d = None
            ut.append((r, d if isinstance(d, dict) and isinstance(d.get('fil'), str) and isinstance(d.get('sha256'), str) else None))
    return ut, None


def _forteckningspost(d, integ):
    slag = str(d.get('slag') or EJ)[:200]
    return {'slag': slag, 'registrerad': 'registrerad med sha256 %s' % (str(d.get('sha256'))[:12] or EJ), 'kopierad': str(d.get('kopierad') or EJ)[:40],
            'session': str(d.get('session') or EJ)[:40], 'integritet': integ, 'integritet_text': INTEGRITET.get(integ, integ)}


def _under(rel):
    """En verklig sökväg 'underlag/…' eller 'kunder/…' som fil under underlag/ eller kunder/."""
    forsta, _, rest = rel.partition('/')
    return (UNDERLAG if forsta == 'underlag' else KUNDER) / rest


def _rapportfil(rel):
    """En fil under underlag/ som vyn får läsa och visa: den verkliga sökvägen (_kanonisk), eller None när filen inte
    finns eller fil_tillaten döljer den. Det är den verkliga filen som prövas, så att ./, //, .., en symlänk eller ett
    annat skiftläge inte läser in det som blindningen eller integritetsgränsen döljer (granskningen av r99, BÖR-1)."""
    k = _kanonisk(rel)
    return k[0] if k and k[1] is not None and k[1].is_file() and _ett_namn(k[1]) and _tillaten(k[0]) else None


def granskningsrapporter():
    """Rapporterna med huvud (underlag/granskningar/GR-*.md, lägesrapporterna i underlag/rapporter/ och
    projektrapporterna utanför flödet, underlag/<uppdrag>/*.md med id och rapportstatus i huvudet) och förteckningens
    äldre rapporter utan huvud, med förteckningens integritet. Varje rapport är den verkliga filen (_rapportfil), en gång,
    och bara om fil_tillaten låter dashboarden visa den."""
    import startkontroll
    ut, kanda = [], {}

    def lagg_till(rel, slag):
        r = _rapport(_under(rel), slag)
        kanda[rel] = r
        ut.append(r)
        return r

    for p in sorted((UNDERLAG / 'granskningar').glob('GR-*.md')):
        rel = _rapportfil('underlag/granskningar/' + p.name)
        if rel and rel not in kanda and rel.startswith('underlag/granskningar/GR-') and rel.count('/') == 2:
            lagg_till(rel, 'systemgranskning')
    for p in sorted((UNDERLAG / 'rapporter').glob('*.md')):
        rel = _rapportfil('underlag/rapporter/' + p.name)
        if rel and rel not in kanda and rel.startswith('underlag/rapporter/') and rel.count('/') == 2:
            lagg_till(rel, 'lägesrapport')
    egna = set(flode_slugar()) | {'granskningar', 'rapporter'}  # kundernas kataloger och de två ovan har sina egna delar
    for d in sorted(UNDERLAG.iterdir()) if UNDERLAG.is_dir() else []:
        if not d.is_dir() or not SLUG.match(d.name) or d.name.startswith(('rokprov', 'prov-', 'pt-')):
            continue
        for p in sorted(d.glob('*.md')):
            rel = _rapportfil('underlag/%s/%s' % (d.name, p.name))
            if not rel or rel in kanda or rel.count('/') != 2 or rel.split('/')[1] in egna:
                continue  # också en katalog som är en länk dit: det är den verkliga filen som räknas
            r = _rapport(_under(rel), 'projektrapport')
            if r['huvud'] == 'ok' and r['id'] != EJ and r['rapportstatus'] != EJ:
                kanda[rel] = r
                ut.append(r)
    rader, fel_ = forteckningen()
    lage = {'finns': rader is not None, 'fel': fel_, 'poster': 0, 'trasiga_rader': 0, 'dolda': 0,
            'integritet': {k: 0 for k in INTEGRITET}, 'saknas': [], 'fel_sha': [], 'not': INTEGRITET_NOT}
    rot = UNDERLAG.parent
    for rad, d in rader or []:
        lage['poster'] += 1
        integ = startkontroll.forteckningsrad(rot, rad)
        lage['integritet'][integ] = lage['integritet'].get(integ, 0) + 1
        if not d:
            lage['trasiga_rader'] += 1
            continue
        k = _kanonisk('underlag/' + d['fil'])
        if not k or not _tillaten(k[0]) or (k[1] is not None and not _ett_namn(k[1])):  # det dashboarden inte visar nämns inte här
            lage['dolda'] += 1
            continue
        sokvag = k[0]  # den verkliga filen, också när raden skrivits med ./, //, .., en länk eller ett annat skiftläge
        if integ in ('saknas', 'fel_sha'):
            lage[integ].append(sokvag)
        if sokvag in kanda:  # samma fil på en rad till (som ./ eller via en länk): den första raden för filen gäller
            if kanda[sokvag].get('forteckning') is None:
                kanda[sokvag]['forteckning'] = _forteckningspost(d, integ)
            continue
        if not sokvag.endswith('.md') or str(d.get('slag') or '').startswith(('bevis', 'mätskript')):
            continue  # bevis och mätskript är underlag till en rapport, inga egna rapporter
        if k[1] is not None and k[1].is_file():
            r = _rapport(_under(sokvag), 'äldre rapport')
        else:
            r = {k_: EJ for k_ in RAPPORTFALT}
            r.update(slag='äldre rapport', huvud='saknas', avsandare=EJ_BELAGD, utfall=EJ, utfall_rapport=EJ, agarens_dom=[], rattelser=[],
                     rapportstatus_klass=EJ, version=None, typgrupp=EJ,
                     fil={'text': sokvag.rsplit('/', 1)[-1], 'sokvag': sokvag, 'lank': None, 'tid': None, 'sha': None})
        r['forteckning'] = _forteckningspost(d, integ)
        if r['typgrupp'] == EJ:  # typen står inte i rapporten; förteckningens slag visas som sådant
            r['typgrupp'] = '%s (förteckningens slag)' % r['forteckning']['slag'].split(' (')[0]
        kanda[sokvag] = r
        ut.append(r)
    return ut, lage


def _rundnyckel(t):
    m = re.fullmatch(r'r(\d+)([a-z]?)', t)
    return (int(m.group(1)), m.group(2)) if m else (10 ** 6, t)


def saknade_rapporter(rapporter, rader):
    """Granskningar som koden hänvisar till (granskningen av rNN, också omgranskningen och slutgranskningen) utan en
    registrerad rapport: en GR-fil i underlag/granskningar/ eller en systemgranskning i förteckningen vars filnamn bär
    rundan. Innehållet återskapas aldrig; vyn säger bara att rapporten saknas och var koden nämner den."""
    reg = set()
    for r in rapporter:
        if r.get('slag') == 'systemgranskning' and r.get('fil'):
            reg |= {t for t in re.split(r'[-_.]', Path(r['fil']['sokvag']).stem) if RUNDA.fullmatch(t)}
    for _rad, d in rader or []:
        if d and str(d.get('slag') or '').startswith('systemgranskning'):
            reg |= {t for t in re.split(r'[-_.]', Path(d['fil']).stem) if RUNDA.fullmatch(t)}
    ref = {}
    for monster in KODFILER:
        for p in sorted(ROOT.glob(monster)):
            if p.is_symlink() or not p.is_file():
                continue
            try:
                rader_ = p.read_text(encoding='utf-8', errors='replace').split('\n')
            except OSError:
                continue
            rel = p.relative_to(ROOT).as_posix()
            for i, r in enumerate(rader_, 1):
                for m in GRANSKNINGSREF.finditer(r):
                    for t in [m.group(1)] + re.findall(r'\br\d+[a-z]?\b', m.group(2)):
                        ref.setdefault(t, []).append('%s:%d' % (rel, i))
    return [{'runda': t, 'antal': len(v), 'var': v[:8]} for t, v in sorted(ref.items(), key=lambda x: _rundnyckel(x[0])) if t not in reg]


def _ord(s):
    return set(re.findall(r'[a-zåäöé0-9@][a-zåäöé0-9@-]{3,}', s.lower()))


def _hanvisningar(text, lista):
    """Tilläggen som en text hänvisar till ("tillägget 2026-10-05, kväll (skissläget)"): samma datum och samma tillägg
    efter datumet (kväll, sen kväll …); finns flera avgör rubrikens titel, ordagrant eller med flest gemensamma ord. En
    hänvisning som inte går att knyta till ett enda tillägg är oklar och visar kandidaterna."""
    ut, kvalar = [], sorted({t['kval'] for t in lista if t['kval']}, key=len, reverse=True)
    for m in TILLAGG_REF.finditer(text):
        datum, efter = m.group(1), text[m.end():m.end() + 160]
        kval = next((k for k in kvalar if re.match(r', %s(?![a-zåäö])' % re.escape(k), efter)), '')
        kand = [t for t in lista if t['datum'] == datum and t['kval'] == kval]
        if len(kand) > 1:
            exakt = [t for t in kand if t['titel'] and t['titel'] in efter]
            if len(exakt) == 1:
                kand = exakt
            else:
                poang = [(len(_ord(efter[:110]) & _ord(t['titel'])), t) for t in kand]
                basta = max(p for p, _ in poang)
                if basta and sum(1 for p, _ in poang if p == basta) == 1:
                    kand = [t for p, t in poang if p == basta]
        ut.append({'datum': datum, 'kval': kval, 'mal': [t['nr'] for t in kand], 'oklart': len(kand) != 1})
    return ut


def _aterstar(rader):
    """Punkterna under **Återstår:** i ett tillägg, som de står."""
    for i, r in enumerate(rader):
        m = re.search(r'\*\*Återstår:?\*\*:?\s*(.*)$', r)
        if not m:
            continue
        punkter = [m.group(1).strip()] if m.group(1).strip() else []
        for r2 in rader[i + 1:]:
            m2 = re.match(r'^\s+[-*]\s+(.*)$', r2)
            if m2:
                punkter.append(m2.group(1).strip())
            elif re.match(r'^\s{2,}\S', r2) and punkter:
                punkter[-1] += ' ' + r2.strip()
            else:
                break
        return punkter[:30]
    return []


def beslutslogg():
    """Besluten i BESLUT.md: varje rubrik "## Tillägg …" (rubriken är beslutets id) med raden **Status:** direkt under
    (gäller, delvis ersatt av … eller ersatt av …) eller märkningen **Delvis ersatt av:** / **Ersatt av:** i texten;
    utan någon av dem "ej angivet". Hänvisningarna till ersättaren knyts till tillägget de pekar på, och åt andra hållet
    vad ett tillägg ersätter. Rubriker i kodblock räknas inte."""
    text = las_text(ROOT / 'BESLUT.md')
    if text is None:
        return {'fel': 'BESLUT.md går inte att läsa', 'tillagg': []}
    delar, staket = [], None
    for r in text.split('\n'):
        s = r.strip()
        if staket:
            if s.startswith(staket):
                staket = None
        elif s.startswith(('```', '~~~')):
            staket = s[:3]
        elif r.startswith('## '):
            delar.append((r[3:].strip(), []))
            continue
        if delar:
            delar[-1][1].append(r)
    lista = []
    for rubrik, rader in delar:
        if not rubrik.startswith('Tillägg'):
            continue
        m = TILLAGG_RUBRIK.match(rubrik)
        forsta = next((r for r in rader if r.strip()), '')
        sm = re.match(r'^\*\*Status:\*\*\s*(.+?)\s*$', forsta)
        statusrad = sm.group(1).rstrip('.').strip() if sm else None
        markorer = [(k, ' '.join(t.split())) for k, t in ERSATT_MARKOR.findall('\n'.join(rader))]
        if statusrad:
            s = statusrad.lower()
            klass = 'gäller' if s.startswith('gäller') else 'delvis ersatt' if s.startswith('delvis ersatt') else 'ersatt' if s.startswith('ersatt') else 'annat'
        else:
            klass = 'ersatt' if any(k == 'Ersatt av' for k, _ in markorer) else 'delvis ersatt' if markorer else EJ
        lista.append({'nr': len(lista), 'rubrik': rubrik, 'nyckel': rubrik[len('Tillägg '):], 'datum': m.group(1) if m else EJ,
                      'kval': (m.group(2) or '').strip() if m else '', 'titel': m.group(3).strip() if m else '',
                      'status': klass, 'statusrad': statusrad or EJ, 'markorer': markorer, 'aterstar': _aterstar(rader),
                      'html': md('\n'.join(rader)), 'ersatter': []})
    for t in lista:
        ersatt = [{'vad': 'statusraden', 'text': t['statusrad'], 'ref': _hanvisningar(t['statusrad'], lista)}] if t['status'] in ('delvis ersatt', 'ersatt') and t['statusrad'] != EJ else []
        ersatt += [{'vad': k.lower(), 'text': x[:500], 'ref': _hanvisningar(x, lista)} for k, x in t.pop('markorer')]
        t['ersatt_av'] = ersatt
        for e in ersatt:
            for ref in e['ref']:
                if not ref['oklart'] and ref['mal'][0] != t['nr'] and t['nr'] not in lista[ref['mal'][0]]['ersatter']:
                    lista[ref['mal'][0]]['ersatter'].append(t['nr'])
    for t in lista:
        t['vy'] = '#/dokumentation/beslut/%d' % t['nr']
    return {'kalla': 'BESLUT.md', 'tillagg': lista}


def _avsnitt(text, rubrik):
    """Texten under en rubrik på nivå två till nästa sådan, utanför kodblock; '' när rubriken saknas."""
    ut, inne, staket = [], False, None
    for r in (text or '').split('\n'):
        s = r.strip()
        if staket:
            staket = None if s.startswith(staket) else staket
        elif s.startswith(('```', '~~~')):
            staket = s[:3]
        elif r.startswith('## '):
            if inne:
                break
            inne = r.rstrip() == rubrik
            continue
        if inne:
            ut.append(r)
    return '\n'.join(ut)


def _sparade():
    """Filerna som git följer i repot (git ls-files): bara de kan visas som instruktioner (granskningen av r99, BÖR-2).
    Ger (mängden, ett fel eller None); utan git visas inga instruktioner, och felet står i vyn."""
    import subprocess
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        r = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, timeout=30, env=env)
    except (OSError, subprocess.SubprocessError) as e:
        return set(), '%s: %s' % (type(e).__name__, str(e)[:160])
    if r.returncode:
        return set(), (r.stderr.decode('utf-8', 'replace').strip() or 'slutkod %d' % r.returncode)[:200]
    return {x.decode('utf-8', 'surrogateescape') for x in r.stdout.split(b'\0') if x}, None


def _repofil(rel, sparade):
    """Är rel en publik .md-fil som vyn får visa? Den verkliga filen (_verklig) ska vara just rel: ingen symlänk någonstans
    i sökvägen, inget . eller .. och samma skiftläge; aldrig under underlag/ eller kunder/ (oavsett skiftläge), aldrig
    backloggens poster; spårad i git och utan andra hårda länkar (granskningen av r99, BÖR-2)."""
    if not isinstance(rel, str) or not rel.endswith('.md') or rel.split('/')[0].casefold() in ('underlag', 'kunder') \
            or rel.startswith('backlog/B-') or rel not in sparade:
        return False
    v = _verklig(ROOT, rel)
    if not v or v[0] != rel or v[1] is None:
        return False
    try:
        st_ = os.lstat(v[1])
    except OSError:
        return False
    return stat.S_ISREG(st_.st_mode) and st_.st_nlink == 1


def _repofiler(t, sparade):
    """Repots publika .md-filer som en sökväg i platsregeln eller CLAUDE.md pekar på: ett mönster som kunskap/<ämne>.md
    eller kritik/ blir filerna det täcker, och ett ensamt filnamn letas i roten och sedan i kunskap/. Varje fil prövas
    med _repofil."""
    t = t.strip()
    if not t or re.search(r'\s', t) or t.startswith(('/', '~', '.venv', 'http')) or t.split('/')[0].casefold() in ('underlag', 'kunder'):
        return []
    m = re.sub(r'<[^>]*>', '*', t).replace('ÅÅÅÅMMDD', '*').replace('ÅÅÅÅ-MM-DD', '*').replace('…', '*')
    if '**' in m or (('*' in m or m.endswith('/')) and '/' not in m.rstrip('/') and not m.endswith('/')):
        return []  # fetstil och liknande i texten, ingen sökväg
    try:
        if m.endswith('/'):
            traffar = sorted(ROOT.glob(m + '*.md'))
        elif '*' in m:
            traffar = sorted(ROOT.glob(m))
        elif '/' in m:
            traffar = [ROOT / m]
        else:
            traffar = [ROOT / m if (ROOT / m).is_file() else ROOT / 'kunskap' / m]
    except (ValueError, OSError):
        return []
    ut = []
    for p in traffar:
        try:
            rel = p.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if _repofil(rel, sparade):
            ut.append(rel)
    return ut


def _dokpost(rel):
    """Ett publikt dokument: titeln (första rubriken, eller skillens namn), statusraden om filen börjar med en
    (README.md: en fil som inte gäller fullt ut börjar med Status: historik … eller Status: vilande …) och ändringstiden."""
    p = ROOT / rel
    text = las_text(p) or ''
    falt, lage = rapporthuvud(text)
    kropp = text.split('\n---', 1)[1].split('\n', 1)[-1] if lage == 'ok' else text
    rader = [r for r in kropp.split('\n') if r.strip()][:40]
    status = next((re.sub(r'^\**Status:?\**:?\s*', '', r).strip() for r in rader[:3] if re.match(r'^\**Status:', r)), None)
    titel = next((r[2:].strip() for r in rader if r.startswith('# ')), None) or _text(falt.get('name') or '') or rel
    try:
        tid = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except OSError:
        tid = None
    return {'dok': rel, 'titel': titel[:200], 'status': status[:300] if status else None,
            'beskrivning': _text(falt.get('description') or '')[:300] or None, 'tid': tid}


def instruktioner():
    """Så fungerar Nortropic: platsregeln (README.md, Var information finns) som den står, flödeskartan (kedjan ur
    README.md, som flödesvyn läser den) och de publika filer som platsregelns tabell och CLAUDE.md pekar på, i
    tabellens slag."""
    readme = las_text(ROOT / 'README.md') or ''
    sek = _avsnitt(readme, '## Var information finns')
    claude = las_text(ROOT / 'CLAUDE.md') or ''
    sparade, git_fel = _sparade()
    # det CLAUDE.md nämner med namn (inte en hel katalog eller ett mönster)
    i_claude = {f for t in re.findall(r'`([^`]+)`', claude) if not re.search(r'[<*…]|/$', t) for f in _repofiler(t, sparade)}
    grupper, sett = [], set()
    for r in sek.split('\n'):
        if not r.startswith('|') or set(r) <= set('|-: '):
            continue
        c = [x.strip() for x in r.strip().strip('|').split('|')]
        if len(c) < 2 or c[0] == 'Slag':
            continue
        filer = (['README.md'] if c[0].startswith('Start och överblick') and _repofil('README.md', sparade) else [])
        filer += [f for t in re.findall(r'`([^`]+)`', c[1]) for f in _repofiler(t, sparade)]
        filer = [f for f in dict.fromkeys(filer) if f not in sett]
        sett |= set(filer)
        if filer:
            grupper.append({'slag': c[0], 'filer': [dict(_dokpost(f), i_claude=f in i_claude) for f in filer]})
    ovriga = [f for f in sorted(i_claude) if f not in sett]
    if ovriga:
        grupper.append({'slag': 'Övriga som CLAUDE.md pekar på', 'filer': [dict(_dokpost(f), i_claude=True) for f in ovriga]})
    return {'kalla': 'README.md, Var information finns; CLAUDE.md', 'platsregel': bool(sek.strip()),
            'platsregel_html': md(sek), 'kedjan': kedjan(), 'grupper': grupper, 'git_fel': git_fel}


def dokument(rel):
    """Ett publikt dokument som platsregeln eller CLAUDE.md pekar på (instruktioner), renderat; None för allt annat, och
    aldrig något under underlag/ eller kunder/, som bara visas genom /fil/ och fil_tillaten."""
    if not isinstance(rel, str) or rel not in {f['dok'] for g in instruktioner()['grupper'] for f in g['filer']}:
        return None
    if not _repofil(rel, _sparade()[0]):  # prövas igen när filen läses: en länk kan ha kommit till sedan listan lästes
        return None
    p = ROOT / rel
    text = las_text(p) or ''
    if rapporthuvud(text)[1] == 'ok':
        text = text.split('\n---', 1)[1].split('\n', 1)[-1]
    return dict(_dokpost(rel), html=md(text))


def backlogposter():
    """Backloggens poster (kontroller/backlog.py) med läget: klar betyder genomförd, och verifierad är posten först när
    fältet verifierad säger det."""
    ut = []
    for p in bl.lista():
        kropp = p.pop('kropp', '')
        forslag = re.search(r'^\*\*Förslag:\*\*\s*(.+)$', kropp, re.M)
        lage = bl.lage(p)
        ut.append({'id': p['id'], 'titel': p.get('titel'), 'status': p.get('status'), 'lage': lage, 'kalla': p.get('kalla'),
                   'kallref': p.get('kallref'), 'fynd': p.get('fynd'), 'rapport': (p.get('fynd') or '').split('#', 1)[0] or None,
                   'commit': p.get('commit'), 'verifierad': p.get('verifierad'), 'verifierad_tid': p.get('verifierad_tid'),
                   'steg': p.get('steg'), 'atgard': forslag.group(1).strip()[:400] if forslag else None,
                   'grupp': ('oppen' if p.get('status') in ('vilande', 'pagar') else 'verifierad' if p.get('status') == 'klar' and p.get('verifierad')
                             else 'klar' if p.get('status') == 'klar' else 'ovrig'), 'vy': '#/backlog'})
    return ut


def kundlagen():
    """Varje kunds körning som flödesvyn visar den (flode): körningen, de nio stegens status, det som väntar på ägaren
    och byggets rapporter. En arm i en blind jämförelse som ägaren inte valt i än visas inte alls."""
    ut = []
    for s in flode_slugar():
        try:
            f = flode(s)
        except Exception as e:  # noqa: BLE001 — en kund som inte går att läsa fäller inte vyn
            ut.append({'slug': s, 'fel': '%s: %s' % (type(e).__name__, str(e)[:200]), 'vy': '#/flode/' + s})
            continue
        if f.get('ab_dold'):
            ut.append({'slug': s, 'ab_dold': True, 'vy': '#/flode/' + s})
            continue
        steg = [{'nr': x['nr'], 'namn': x['namn'], 'status': x['status']} for x in f['steg']]
        s6 = next((x for x in f['steg'] if x['nr'] == 6), {})
        ut.append({'slug': s, 'blind': bool(f.get('blind')), 'korning': f.get('korning'), 'steg': steg,
                   'vantar': [x['namn'] for x in steg if x['status'] == 'väntar på ägaren'],
                   'pagar': [x['namn'] for x in steg if x['status'] == 'pågår'], 'helbygget': s6.get('status'),
                   'slutrapport': [x for x in s6.get('utfall') or [] if isinstance(x, dict) and x.get('sokvag')], 'vy': '#/flode/' + s})
    return ut


def pagaende_korningar():
    """Körningar som pågår på maskinen, ur körregistret (kontroller/korregister.py), bara lästa: döda poster står kvar
    där, och registret rensas inte härifrån."""
    import korregister
    return [{'vad': str(d.get('vad') or EJ), 'slug': d.get('slug'), 'pid': d.get('pid'), 'start': d.get('start'),
             'utcheckning': d.get('utcheckning')} for d in korregister.poster(rensa=False)]


def _naturlig(t):
    """Sorteringsnyckel där talen jämförs som tal: GR-20261007-r99 före GR-20261007-r100 (granskningen av r99, KAN 8)."""
    return [(0, int(x), '') if x.isdigit() else (1, 0, x) for x in re.split(r'(\d+)', t) if x]


def _ordning(r):
    return (_text(r.get('datum')) if r.get('datum') != EJ else '', _naturlig(_text(r.get('id')) if r.get('id') != EJ else ''))


def _id_i(text, ident):
    return bool(re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(ident), _text(text)))


def uppdragslage(tillagg, rapporter, poster):
    """Läget per ägaruppdrag: tillägget i BESLUT.md, rapporterna som anger det i fältet beslut (direkt eller genom en
    föregående rapport), den senaste av dem med sitt utfall och sin version (historik, inget aktuellt godkännande),
    fynden ur backloggen och det som enligt tillägget återstår."""
    med_id = [r for r in rapporter if r['id'] != EJ]
    knutna = {r['id']: {t['nr'] for t in tillagg if _id_i(r['beslut'], t['nyckel'])} for r in med_id}
    for _ in range(len(med_id)):  # genom föregående: en omgranskning hör till samma uppdrag som rapporten den följer
        andrat = False
        for r in med_id:
            for f in med_id:
                if f is not r and _id_i(r['foregaende'], f['id']) and not knutna[f['id']] <= knutna[r['id']]:
                    knutna[r['id']] |= knutna[f['id']]
                    andrat = True
        if not andrat:
            break
    ut = []
    for t in tillagg:
        egna = sorted((r for r in med_id if t['nr'] in knutna[r['id']]), key=_ordning)
        if not egna and not (t['aterstar'] and t['status'] in ('gäller', 'delvis ersatt')):
            continue
        foljda = {f['id'] for r in egna for f in egna if f is not r and _id_i(r['foregaende'], f['id'])}
        senaste = ([r for r in egna if r['id'] not in foljda] or egna)[-1:] if egna else []
        ids = {r['id'] for r in egna}
        fynd = [p for p in poster if p['rapport'] in ids]
        ut.append({'nr': t['nr'], 'rubrik': t['rubrik'], 'status': t['status'], 'vy': t['vy'], 'aterstar': t['aterstar'],
                   'rapporter': [r['id'] for r in reversed(egna)],
                   'senaste': dict({k: senaste[0][k] for k in ('id', 'titel', 'datum', 'utfall', 'utfall_rapport', 'agarens_dom', 'bedomningsutfall',
                                                               'rapportstatus_klass', 'version', 'granskad_identitet', 'avsandare', 'rattelser',
                                                               'giltighet')}, lank=(senaste[0]['fil'] or {}).get('lank')) if senaste else None,
                   'fynd': {'oppna': [p['id'] for p in fynd if p['grupp'] == 'oppen'], 'klara': sum(p['grupp'] == 'klar' for p in fynd),
                            'verifierade': sum(p['grupp'] == 'verifierad' for p in fynd)}})
    return ut


def dokumentation():
    """Vyn Dokumentation och rapporter: sammanfattningen först, och de fyra delarna (så fungerar Nortropic, pågående
    uppdrag, granskningar och resultat, beslut och historik), saknat underlag och en plats för kompetenskedjan och
    slutposten, som byggs i andra grenar. Allt räknas fram ur filerna nu; ett fel i en källa gör den delen oläslig, inte
    vyn."""
    fel = {}

    def las(namn, f, standard):
        try:
            return f()
        except Exception as e:  # noqa: BLE001
            fel[namn] = '%s: %s' % (type(e).__name__, str(e)[:240])
            return standard
    rapporter, forteckning = las('granskningar', granskningsrapporter, ([], {}))
    poster = las('backlog', backlogposter, [])
    beslut = las('beslut', beslutslogg, {'tillagg': []})
    instr = las('instruktioner', instruktioner, {'grupper': []})
    kunder_ = las('kunder', kundlagen, [])
    pilot = las('pilot', figma_pilot, [])
    korningar = las('korningar', pagaende_korningar, [])
    saknade = las('saknade', lambda: saknade_rapporter(rapporter, forteckningen()[0]), [])
    tillagg = beslut.get('tillagg') or []
    uppdrag = las('uppdrag', lambda: uppdragslage(tillagg, rapporter, poster), [])
    for r in rapporter:  # fynden i backloggen per rapport
        egna = [p for p in poster if r['id'] != EJ and p['rapport'] == r['id']]
        r['fynd'] = {'oppna': [p['id'] for p in egna if p['grupp'] == 'oppen'], 'klara': [p['id'] for p in egna if p['grupp'] == 'klar'],
                     'verifierade': [p['id'] for p in egna if p['grupp'] == 'verifierad']}
        r['vy'] = '#/dokumentation/granskningar/' + (r['id'] if r['id'] != EJ else (r['fil'] or {}).get('sokvag', ''))
    med_huvud = [r for r in rapporter if r['huvud'] == 'ok']
    lagesrapporter = sorted((r for r in rapporter if r['slag'] == 'lägesrapport'), key=_ordning, reverse=True)
    raknare = lambda vals: {k: sum(1 for v in vals if v == k) for k in dict.fromkeys(vals)}  # noqa: E731
    fynd = [p for p in poster if p.get('fynd')]
    vantar = [{'text': '%s: %s väntar på dig' % (k['slug'], n), 'vy': k['vy']} for k in kunder_ for n in k.get('vantar') or []]
    for r in lagesrapporter[:1]:
        if r['beslut'] != EJ:
            vantar.append({'text': 'Beslut enligt lägesrapporten %s (%s): %s' % (r['id'], _text(r['datum']), _text(r['beslut'])[:300]),
                           'vy': r['vy'], 'lank': (r['fil'] or {}).get('lank')})
    sammandrag = lambda r: dict({k: r[k] for k in ('id', 'titel', 'typgrupp', 'datum', 'utfall', 'utfall_rapport', 'agarens_dom', 'bedomningsutfall',  # noqa: E731
                                                   'rapportstatus_klass', 'version', 'granskad_identitet', 'systemdel', 'uppdrag', 'kund', 'moment',
                                                   'avsandare', 'rattelser', 'giltighet', 'vy')}, lank=(r['fil'] or {}).get('lank'))
    senaste = [sammandrag(r) for r in sorted(med_huvud, key=_ordning, reverse=True)[:6]]
    projekt = las('projekt', lambda: [dict(sammandrag(r), katalog=(r['fil'] or {}).get('sokvag', '').split('/')[1])  # KAN 7
                                      for r in sorted((r for r in rapporter if r['slag'] == 'projektrapport'), key=_ordning, reverse=True)], [])
    # rättade slutsatser och giltighet ur rapporthuvudet (rattelser, giltighet), nyast först (granskningen av r99, BÖR-7)
    rattade = [sammandrag(r) for r in sorted(rapporter, key=_ordning, reverse=True) if r.get('rattelser') or r.get('giltighet') not in (None, EJ)]
    trasiga = [{'sokvag': (r['fil'] or {}).get('sokvag'), 'vy': r['vy']} for r in rapporter if r['huvud'] == 'trasigt']
    utan_falt = [{'id': r['id'], 'saknar': [k for k in ('granskad_identitet', 'rapportstatus', 'bedomningsutfall', 'datum') if r[k] == EJ],
                  'vy': r['vy']} for r in med_huvud if r['huvud'] == 'ok' and any(r[k] == EJ for k in ('granskad_identitet', 'rapportstatus', 'bedomningsutfall', 'datum'))]
    utan_status = [{'rubrik': t['rubrik'], 'vy': t['vy']} for t in tillagg if t['status'] == EJ]
    ersatta_rapporter = [r['vy'] for r in rapporter if r['rapportstatus_klass'] == 'ersatt' or r['ersatt_av'] != EJ]
    integ = (forteckning or {}).get('integritet') or {}
    sammanfattning = {
        'instruktioner': {'filer': sum(len(g['filer']) for g in instr.get('grupper') or []),
                          'med_statusrad': sum(1 for g in instr.get('grupper') or [] for f in g['filer'] if f.get('status')),
                          'kedjan': len((instr.get('kedjan') or {}).get('steg') or [])},
        'pagaende': {'korningar': len(korningar) + sum(1 for k in kunder_ if k.get('pagar')), 'kunder': len(kunder_),
                     'uppdrag': len(uppdrag), 'pilot': len(pilot), 'lagesrapporter': len(lagesrapporter)},
        'granskningar': {'rapporter': len(rapporter), 'med_huvud': len(med_huvud), 'utan_huvud': sum(r['huvud'] == 'saknas' for r in rapporter),
                         'trasiga': sum(r['huvud'] == 'trasigt' for r in rapporter),
                         'utfall': raknare([r['utfall'] for r in med_huvud]), 'rapportstatus': raknare([r['rapportstatus_klass'] for r in med_huvud])},
        'fynd': {'oppna': sum(p['grupp'] == 'oppen' for p in fynd), 'klara_ej_verifierade': sum(p['grupp'] == 'klar' for p in fynd),
                 'verifierade': sum(p['grupp'] == 'verifierad' for p in fynd), 'ovriga': sum(p['grupp'] == 'ovrig' for p in fynd)},
        'beslut': {'tillagg': len(tillagg), 'status': raknare([t['status'] for t in tillagg])},
        'historik': {'ersatta_tillagg': sum(1 for t in tillagg if t['status'] in ('delvis ersatt', 'ersatt')), 'ersatta_rapporter': len(ersatta_rapporter),
                     'instruktioner_med_statusrad': sum(1 for g in instr.get('grupper') or [] for f in g['filer'] if f.get('status')),
                     'rattade': rattade},
        'saknat': {'rapporter': [x['runda'] for x in saknade], 'integritet': integ, 'trasiga_huvuden': len(trasiga),
                   'utan_status': len(utan_status), 'utan_falt': len(utan_falt)},
        'vantar': vantar, 'senaste': senaste,
    }
    return {
        'tid': nu(), 'sammanfattning': sammanfattning, 'fel': fel,
        'instruktioner': instr,
        'pagaende': {'korningar': korningar, 'uppdrag': uppdrag, 'kunder': kunder_,
                     'pilot': [{k: m.get(k) for k in ('id', 'moment', 'status', 'status_i_posten', 'status_skal', 'aktuell', 'bedomda', 'tid', 'domar')}
                               for m in pilot],
                     'lagesrapporter': [dict({k: r[k] for k in ('id', 'titel', 'datum', 'uppdrag', 'beslut', 'atgarder', 'rapportstatus_klass', 'utfall',
                                                                 'agarens_dom', 'bedomningsutfall', 'avsandare', 'vy')}, lank=(r['fil'] or {}).get('lank'))
                                        for r in lagesrapporter],
                     'projektrapporter': projekt,
                     'backlog': {'antal': raknare([p['lage'] if not str(p['lage']).startswith('klar, verifierad') else 'klar, verifierad' for p in poster]),
                                 'vy': '#/backlog'}},
        'granskningar': {'rapporter': sorted(rapporter, key=_ordning, reverse=True), 'fynd': fynd, 'forteckning': forteckning},
        'beslut': beslut,
        'saknat': {'rapporter': saknade, 'integritet': {'saknas': (forteckning or {}).get('saknas') or [], 'fel_sha': (forteckning or {}).get('fel_sha') or [],
                                                        'ej_kontrollerade': integ.get('ej_kontrollerade', 0), 'not': INTEGRITET_NOT},
                   'trasiga_huvuden': trasiga, 'utan_falt': utan_falt, 'utan_status': utan_status},
        'senare': {'kompetenskedjan': None, 'slutposten': None},  # visas här när datakällorna finns (KAN 10)
    }


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def skicka(self, kod, kropp, typ='application/json; charset=utf-8', extra=None):
        if isinstance(kropp, (dict, list)):
            kropp = json.dumps(kropp, ensure_ascii=False).encode()
        elif isinstance(kropp, str):
            kropp = kropp.encode()
        self.send_response(kod)
        self.send_header('Content-Type', typ)
        self.send_header('Content-Length', str(len(kropp)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(kropp)

    def vard_ok(self):
        """Host måste vara dashboardens egen adress och port (revisionen 2026-10-03, F13: Origin lika med Host räcker inte,
        en sida på ett annat namn som pekar om till 127.0.0.1 skulle annars läsa och skriva som ägaren)."""
        vard = (self.headers.get('Host') or '').strip().lower()
        return not VARD['tillatna'] or vard in VARD['tillatna']

    def do_GET(self):
        vag = unquote(urlsplit(self.path).path)
        if not self.vard_ok():
            return self.skicka(421, {'fel': 'fel värd: använd http://127.0.0.1:<port>'})
        try:
            if vag in ('/', '/index.html'):
                return self.skicka(200, (Path(__file__).parent / 'index.html').read_bytes(), 'text/html; charset=utf-8')
            if vag in ('/kundstart-agare.js', '/kundstart-agare.css', '/kirurg-forbattring.js'):
                typ = 'text/javascript; charset=utf-8' if vag.endswith('.js') else 'text/css; charset=utf-8'
                return self.skicka(200, (Path(__file__).parent / vag[1:]).read_bytes(), typ)
            if vag == '/api/kundstart':
                import kundstart_agare
                return self.skicka(200, kundstart_agare.lista(ROOT))
            if vag == '/api/kirurg/forbattringar':
                import kirurg_forbattring
                return self.skicka(200, kirurg_forbattring.vy(ROOT))
            m = re.fullmatch(r'/api/kundstart/([a-f0-9]{32})', vag)
            if m:
                import kundstart_agare
                return self.skicka(200, kundstart_agare.detalj(ROOT, m.group(1)))
            if vag == '/api/oversikt':
                bk = backloggen()
                return self.skicka(200, {'byggen': byggen(), 'lardomar': md(las_text(lardomar_original()) or las_text(ROOT / 'LARDOMAR.md')),
                                         'backlog_vilande': sum(1 for p in bk if p.get('status') == 'vilande'),
                                         'intag_pagar': sum(1 for x in intag_lista() if x['pagar']),
                                         'prospekt_vantar': pv.raknare(),
                                         'granskare': granskare_overens(), 'tid': nu()})
            if vag == '/api/ab':
                return self.skicka(200, ab_lista())
            if vag == '/api/kalibrering':
                return self.skicka(200, kalibrering_lista())
            if vag == '/api/designprov':
                return self.skicka(200, designprov_slugar())
            if vag == '/api/flode':  # det tänkta flödet (README), kunderna och Figma-piloten
                return self.skicka(200, {'kedjan': kedjan(), 'slugar': flode_slugar(), 'pilot': figma_pilot()})
            m = re.match(r'^/api/flode/([a-z0-9-]{2,60})$', vag)
            if m:  # det som hände för en kund, i kedjans nio steg
                if m.group(1) not in flode_slugar():
                    return self.skicka(404, {'fel': 'ingen kund med underlag eller bygge'})
                return self.skicka(200, flode(m.group(1)))
            if vag == '/api/dokumentation':  # Dokumentation och rapporter: samma källor som filstrukturen, lästa nu
                return self.skicka(200, dokumentation())
            if vag == '/api/dokument':  # ett publikt dokument som platsregeln eller CLAUDE.md pekar på; aldrig underlag/ eller kunder/
                d = dokument(dict(parse_qsl(urlsplit(self.path).query)).get('fil'))
                return self.skicka(200, d) if d else self.skicka(404, {'fel': 'inget dokument som platsregeln eller CLAUDE.md pekar på'})
            if vag == '/api/prototyp':
                return self.skicka(200, prototyp_slugar())
            m = re.match(r'^/api/prototyp/([a-z0-9-]{2,60})$', vag)
            if m:
                if m.group(1) not in prototyp_slugar():
                    return self.skicka(404, {'fel': 'ingen prototyp för bygget'})
                res = prototyp(m.group(1))
                try:
                    res['startkvitto'] = startkvitto(m.group(1))
                except Exception as e:  # noqa: BLE001 — kvittot får aldrig fälla vyn
                    res['startkvitto'] = {'status': 'okand', 'fel': str(e)[:200]}
                return self.skicka(200, res)
            m = re.match(r'^/api/observation/([a-z0-9-]{2,60})$', vag)
            if m:  # den passiva observationen (kontroller/observation.py): läser bara, och ett fel gör vyn ofullständig
                if m.group(1) not in prototyp_slugar():
                    return self.skicka(404, {'fel': 'ingen körning för bygget'})
                try:
                    import observation
                    return self.skicka(200, observation.oversikt(m.group(1)))
                except Exception as e:  # noqa: BLE001
                    return self.skicka(200, {'ofullstandig': '%s: %s' % (type(e).__name__, str(e)[:200])})
            m = re.match(r'^/api/designprov/([a-z0-9-]{2,60})$', vag)
            if m:
                if m.group(1) not in designprov_slugar():
                    return self.skicka(404, {'fel': 'inget designprov för bygget'})
                return self.skicka(200, designprov(m.group(1)))
            if vag == '/api/backlog':
                return self.skicka(200, backloggen())
            if vag == '/api/kirurg':
                try:
                    spaning_vid_behov()
                except Exception:
                    pass
                return self.skicka(200, {'intag': intag_lista(), 'register': register(), 'overens': overensstammelse()})
            if vag == '/api/spaning':
                return self.skicka(200, spaning_lista())
            if vag == '/api/underhall':
                return self.skicka(200, underhall_lage())
            if vag == '/api/kirurg/kand':
                return self.skicka(200, redan_bedomd(dict(parse_qsl(urlsplit(self.path).query)).get('url')))
            if vag == '/api/prospekt':
                return self.skicka(200, pv.kampanjer())
            m = re.match(r'^/api/prospekt/([a-z0-9-]{3,60})$', vag)
            if m:
                return self.skicka(200, pv.kampanj(m.group(1)))
            m = re.match(r'^/api/prospekt/([a-z0-9-]{3,60})/([a-z0-9-]{2,60})$', vag)
            if m:
                return self.skicka(200, pv.prospekt(m.group(1), m.group(2)))
            m = re.match(r'^/api/bygge/([a-z0-9-]{2,60})$', vag)
            if m and (KUNDER / m.group(1)).is_dir():
                return self.skicka(200, bygge(m.group(1)))
            m = re.match(r'^/api/visa/([a-z0-9-]{2,60})$', vag)
            if m:  # GET läser bara läget; visningen startas med POST under ursprungskontrollen (omgång elva, F13)
                if not visa(m.group(1)):
                    return self.skicka(404, {'fel': 'sajten är inte byggd än'})
                return self.skicka(200, lan_lage(m.group(1)))
            m = re.match(r'^/visa/([a-z0-9-]{2,60})/(k\d{2})$', vag)
            if m:  # en kandidats hela prototyp i kandidatflödet, eller en av dess undersidor (?sida=/väg/)
                url = visa_kandidat(m.group(1), m.group(2))
                if url:
                    import kandidater
                    sida = dict(parse_qsl(urlsplit(self.path).query)).get('sida') or ''
                    if sida in kandidater.undersidor(m.group(1), m.group(2)):
                        url += sida.lstrip('/')
                    return self.skicka(302, '', extra={'Location': url})
                return self.skicka(404, '<p>Kandidaten är inte byggd.</p>', 'text/html; charset=utf-8')
            m = re.match(r'^/visa/([a-z0-9-]{2,60})$', vag)
            if m:
                url = visa(m.group(1))
                if url:
                    return self.skicka(302, '', extra={'Location': url})
                return self.skicka(404, '<p>Sajten är inte byggd än.</p>', 'text/html; charset=utf-8')
            m = re.match(r'^/fil/((?:kunder|underlag)/[a-z0-9-]{2,60}/.+)$', vag)
            if m:
                # den verkliga filen avgör, inte den begärda sökvägen (revisionen, F14), också dess skiftläge (granskningen
                # av r99, BÖR-3); ett nollbyte eller en sökväg ut ur roten ger 404 (KAN 1)
                k = _kanonisk(m.group(1))
                p = k[1] if k else None
                if p is not None and _tillaten(k[0]) and _ett_namn(p) and p.is_file() \
                        and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.md', '.json', '.txt', '.log'):
                    typ = mimetypes.guess_type(p.name)[0] or 'text/plain'
                    if typ.startswith('text/') or typ.endswith('json'):
                        typ += '; charset=utf-8'
                    extra = {}
                    if p.suffix.lower() == '.svg':  # en SVG kan bära skript; öppnad direkt från samma ursprung får den inte köra något
                        extra['Content-Security-Policy'] = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'"
                    return self.skicka(200, p.read_bytes(), typ, extra)
            return self.skicka(404, {'fel': 'finns inte'})
        except Exception as e:  # dashboarden ska visa felet, inte dö
            return self.skicka(500, {'fel': '%s: %s' % (type(e).__name__, e)})

    def do_POST(self):
        vag = urlsplit(self.path).path
        if not self.vard_ok():
            return self.skicka(421, {'fel': 'fel värd: använd http://127.0.0.1:<port>'})
        ursprung = urlsplit(self.headers.get('Origin') or '')
        vard = (self.headers.get('Host') or '').strip().lower()
        if ursprung.scheme != 'http' or ursprung.netloc.lower() != vard:
            return self.skicka(403, {'fel': 'fel ursprung'})
        if NYCKEL['varde'] and not hmac.compare_digest(str(self.headers.get('X-Nyckel') or ''), NYCKEL['varde']):
            return self.skicka(403, {'fel': 'saknad eller fel dashboardnyckel: skrivande anrop går bara från dashboarden öppnad via ./dashboard.sh'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            data = json.loads(self.rfile.read(min(n, 56 * 1024 * 1024)) or b'{}')
            m = re.match(r'^/api/flode/([a-z0-9-]{2,60})/start$', vag)
            if m:
                import prototyp as prototyp_kor
                if not isinstance(data, dict):
                    raise ValueError('handlingen ska vara ett objekt')
                slug = m.group(1)
                if data.get('handling') not in ('stoppa','stoppa-overgang') and ab_oavgjord(slug):
                    raise ValueError('en blind jämförelse pågår; inga steg startas från flödesvyn')
                rc = prototyp_kor.fran_dashboard(slug, data.get('handling'), data.get('start_id'))
                import atelje
                avslutad = False
                if rc not in (0, 4, 5) and data.get('handling') not in ('stoppa', 'stoppa-overgang'):
                    # begäran är besvarad, inte vägrad: journalposten för samma start-id har slutat (GR-20261008-r117-claude#B1)
                    sf = atelje.startfil(UNDERLAG / slug / 'atelje', str(data.get('start_id')))
                    avslutad = bool(sf and sf.is_file() and (las_json(sf) or {}).get('status') == 'slut')
                if rc == 5 and data.get('handling') not in ('stoppa', 'stoppa-overgang'):
                    # registrerad kräver en journalpost: ett upptaget kundlås utan post (atelje.main, slutkod 5 före journalen) är
                    # ingen registrerad begäran, och fliken ska behålla sitt start-id för ett nytt försök (GR-20261008-r117-claude#B5)
                    sf = atelje.startfil(UNDERLAG / slug / 'atelje', str(data.get('start_id')))
                    if not (sf and sf.is_file()):
                        return self.skicka(409, {'slutkod': rc, 'start_id': data.get('start_id'),
                                                 'fel': 'En annan start behandlas för kunden och ingen journalpost finns för detta start-id; '
                                                        'ingen ny körning startades. Försök igen om en stund med samma start-id.'})
                if avslutad:
                    return self.skicka(200, {'slutkod': rc, 'start_id': data.get('start_id'), 'avslutad': True,
                                             'besked': 'Begäran är redan avslutad med slutkod %s; läs det aktuella beskedet. En ny handling '
                                                       'får ett nytt start-id.' % rc})
                return self.skicka(202 if rc == 5 else 200 if rc in (0, 4) else 409,
                                   {'slutkod': rc, 'start_id': data.get('start_id'),
                                    **({'fel': 'Ingen ny körning startades. Läs aktuellt läge och dess begränsningar.'} if rc not in (0, 4, 5) else {}),
                                    'besked': 'Stopp har begärts. Läs aktuellt läge tills arbetet har avslutats.' if data.get('handling')=='stoppa-overgang' and rc==5 else
                                              'Begäran är registrerad. Läs aktuellt läge och körningens besked.' if rc == 5 else
                                              'Handlingen är klar; läs det aktuella beskedet.' if rc in (0, 4) else
                                              'Ingen ny körning startades. Läs aktuellt läge och dess begränsningar.'})
            m = re.fullmatch(r'/api/kirurg/forbattringar/([a-z]+)', vag)
            if m:
                import kirurg_forbattring
                if m.group(1) not in kirurg_forbattring.HANDLINGAR:
                    return self.skicka(404, {'fel': 'finns inte'})
                return self.skicka(200, kirurg_forbattring.handling(ROOT, m.group(1), data))
            if vag == '/api/kundstart':
                import kundstart_agare
                return self.skicka(200, kundstart_agare.skapa(ROOT, data))
            m = re.fullmatch(r'/api/kundstart/([a-f0-9]{32})/([a-z_]+)', vag)
            if m:
                import kundstart_agare
                if m.group(2) not in kundstart_agare.HANDLINGAR:
                    return self.skicka(404, {'fel': 'finns inte'})
                return self.skicka(200, kundstart_agare.handling(ROOT, m.group(1), m.group(2), data))
            m = re.match(r'^/api/dom/([a-z0-9-]{2,60})$', vag)
            if m:
                return self.skicka(200, spara_dom(m.group(1), data))
            m = re.match(r'^/api/backlog/(B-[a-z0-9-]+)/status$', vag)
            if m:
                if data.get('status') not in ('avvisad', 'vilande'):
                    raise ValueError('från dashboarden går bara avvisad eller vilande')
                meta = bl.satt_status(m.group(1), data['status'], not_=(data.get('not') or 'ändrad av ägaren i dashboarden'))
                return self.skicka(200, {'id': meta['id'], 'status': meta['status']})
            m = re.match(r'^/api/ab/([a-z0-9TZ-]+)$', vag)
            if m:
                return self.skicka(200, spara_ab(m.group(1), data))
            m = re.match(r'^/api/kalibrering/(K\d{2})$', vag)
            if m:
                return self.skicka(200, spara_kalibrering(m.group(1), data))
            m = re.match(r'^/api/prototyp/([a-z0-9-]{2,60})$', vag)
            if m:
                return self.skicka(200, spara_prototyp(m.group(1), data, minuter=minuter_sedan(data.get('startad'))))
            m = re.match(r'^/api/prototyp/([a-z0-9-]{2,60})/forbattring$', vag)
            if m:
                return self.skicka(200, spara_forbattring(m.group(1), data))
            m = re.match(r'^/api/designprov/([a-z0-9-]{2,60})/(?:(omgang-\d{1,2})/)?([A-E])$', vag)
            if m:
                return self.skicka(200, spara_designprov(m.group(1), m.group(3), data, omgang=m.group(2), minuter=minuter_sedan(data.get('startad'))))
            m = re.match(r'^/api/visa/([a-z0-9-]{2,60})$', vag)
            if m:  # tillståndsändrande: bara POST med rätt ursprung (omgång elva, F13)
                if not visa(m.group(1)):
                    return self.skicka(404, {'fel': 'sajten är inte byggd än'})
                return self.skicka(200, starta_lan(m.group(1)))
            if vag == '/api/prospekt/kampanj':
                return self.skicka(200, pv.starta_kampanj(data))
            m = re.match(r'^/api/prospekt/([a-z0-9-]{3,60})/analysera$', vag)
            if m:
                return self.skicka(200, pv.starta_analys(m.group(1), data))
            m = re.match(r'^/api/prospekt/([a-z0-9-]{3,60})/([a-z0-9-]{2,60})/(status|sajt|demo|brev|brev/godkann|skicka|stryk)$', vag)
            if m:
                k, slug, h = m.groups()
                handtag = {'status': lambda: pv.satt_status(k, slug, data), 'sajt': lambda: pv.satt_sajt(k, slug, data), 'demo': lambda: pv.starta_demo(k, slug),
                           'brev': lambda: pv.starta_brev(k, slug), 'brev/godkann': lambda: pv.godkann(k, slug, data), 'skicka': lambda: pv.skicka(k, slug),
                           'stryk': lambda: pv.stryk(k, slug, data)}[h]
                return self.skicka(200, handtag())
            if vag == '/api/kirurg':
                return self.skicka(200, starta_intag(data.get('url'), data.get('not'), data.get('filer')))
            if vag == '/api/kirurg/omdome':
                return self.skicka(200, spara_omdome(data))
            if vag == '/api/spaning/kor':
                return self.skicka(200, starta_spaning())
            if vag == '/api/underhall/kor':
                return self.skicka(200, starta_underhall())
            m = re.match(r'^/api/spaning/([a-f0-9]{12})/(ta-in|avfarda)$', vag)
            if m:
                return self.skicka(200, ta_in_kandidat(m.group(1)) if m.group(2) == 'ta-in' else avfarda_kandidat(m.group(1), data.get('skal')))
            return self.skicka(404, {'fel': 'finns inte'})
        except (ValueError, json.JSONDecodeError, OSError) as e:
            if vag == '/api/kundstart' or vag.startswith('/api/kundstart/'):
                import kundstart
                if isinstance(e, kundstart.Konflikt):
                    return self.skicka(409, {'fel': str(e)})
            if isinstance(e, PermissionError) and (KUNDER / '.bygge-pid').exists():  # kor.sh låser kunder/ och underlag/ under ett bygge
                return self.skicka(400, {'fel': 'ett bygge pågår: kunder/ och underlag/ tar inga nya kataloger förrän det är klart (%s)' % e})
            return self.skicka(400, {'fel': str(e)})
        except Exception as e:  # ett oväntat fel ska bli ett svar, inte en bruten förbindelse
            import subprocess
            kod = 504 if isinstance(e, subprocess.TimeoutExpired) else 500
            return self.skicka(kod, {'fel': '%s: %s' % (type(e).__name__, e)})


def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('--port', type=int, default=4771)
    p.add_argument('--utan-lan', action='store_true', help='ingen visning av sajten på nätverksadressen (I telefonen)')
    a = p.parse_args()
    LAN['pa'] = not a.utan_lan
    VARD['tillatna'] = {'127.0.0.1:%d' % a.port, 'localhost:%d' % a.port}
    NYCKEL['varde'] = os.environ.pop('NWP_DASHBOARD_NYCKEL', None) or secrets.token_urlsafe(24)
    try:  # dashboard.sh läser filen när dashboarden redan kör; aldrig i loggen eller i barnens miljö
        NYCKELFIL.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(NYCKELFIL, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(NYCKEL['varde'] + '\n')
        os.chmod(NYCKELFIL, 0o600)
    except OSError as e:
        print('dashboardnyckeln kunde inte skrivas till %s: %s' % (NYCKELFIL, e), flush=True)
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    print('Dashboard: http://127.0.0.1:%d (öppna via ./dashboard.sh: skrivande anrop kräver nyckeln i %s)' % (a.port, NYCKELFIL), flush=True)
    def spaningsklocka():
        while True:
            try:
                spaning_vid_behov()
            except Exception as e:  # en klocka som dör ska inte ta med servern
                print('spaningen startade inte: %s' % e, flush=True)
            try:
                underhall_vid_behov()
            except Exception as e:  # noqa: BLE001
                print('underhållet startade inte: %s' % e, flush=True)
            time.sleep(3600)
    threading.Thread(target=spaningsklocka, daemon=True).start()
    threading.Thread(target=lan_klocka, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
