#!/usr/bin/env python3
"""Dashboard för nortropic-webb-pro. Lokal, läser repot och skriver bara ägarens domar.

    .venv/bin/python dashboard/server.py [--port 4771]     (eller ./dashboard.sh)

Visar byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag, körningens senaste händelser),
lärdomarna, kirurgens register och kommandona. Skriver bara när ägaren skickar frågeformuläret efter ett bygge:
kunder/<slug>/DOM.json (strukturerat, privat), underlag/LARDOMAR-original.md (ordagrant, privat) och en post utan
personuppgifter i LARDOMAR.md (i git): bara betygen och valen; lärdomen skriver sessionen som gör ändringen (BESLUT.md 2026-10-03).
Lyssnar bara på 127.0.0.1. POST kräver samma ursprung. Undantaget är visningen av en byggd sajt i telefonen: knappen
I telefonen startar en statisk server för kunder/<slug>/sajt/dist på datorns adress i det lokala nätverket och visar
den som QR-kod (dashboard/qr.py, ritad lokalt). Den servern visar bara sajten; --utan-lan stänger av den.
"""
import argparse
import html
import ipaddress
import socket
import json
import mimetypes
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
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
                        mal = inp.get('file_path') or inp.get('command') or inp.get('url') or inp.get('pattern') or inp.get('subject') or inp.get('description') or ''
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
        'slappt_utan_godkannande': bool(sv.get('slapp')) and not str(sv.get('skal') or '').startswith('kontrollerna gröna'),
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


def fil_tillaten(rel):
    """/fil/<rel>: aldrig jämförelsernas facit (kunder/ab/), och för en arm som ägaren inte valt i än bara provets
    skärmbilder, som den blinda jämförelsen behöver (revisionen 2026-10-03, F14)."""
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
    if rel.startswith('underlag/%s/atelje/' % slug) and not designprov_domt(slug):
        return bool(DP_FIL.match(rel))  # designprovet: bara förslagens bilder tills ägaren dömt alla (panelens dom döljs)
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
    if val not in p['byggen'] + ['lika']:
        raise ValueError('välj A, B eller lika')
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
             '- **Ägarens val (blint):** %s' % ('lika' if val == 'lika' else '%s (%s=%s)' % (etikett[val], p['variabel'], p['varden'][val])),
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
DP_FIL = re.compile(r'^underlag/([a-z0-9-]{2,60})/atelje/(\d|vinnare/bilder)/(undersida/|stiltavla/)?vy-(390|1440)-(forsta|hela|ruta-\d{2})\.png$')
DP_REF = re.compile(r'^underlag/([a-z0-9-]{2,60})/referenser/[A-Za-z0-9._/-]+\.(png|jpe?g|webp)$')


def designprov_slugar():
    """Byggen med en fotograferad ateljé (underlag/<slug>/atelje/FOTOGRAFERADE.json)."""
    return sorted(p.parent.parent.name for p in UNDERLAG.glob('*/atelje/FOTOGRAFERADE.json') if SLUG.match(p.parent.parent.name))


def designprov_ordning(slug, riktningar):
    """Blind ordning: stabil per bygge, oberoende av riktningsnumren (A, B, C …)."""
    import hashlib
    return sorted(riktningar, key=lambda n: hashlib.sha256(('designprov-%s-%d' % (slug, n)).encode()).hexdigest())


def designprov_domt(slug):
    """Har ägaren dömt alla förslag i bygget? (utan fotograferad ateljé finns inget att dölja)"""
    rot = UNDERLAG / slug / 'atelje'
    manifest = las_json(rot / 'FOTOGRAFERADE.json') or {}
    riktningar = [n for n in (manifest.get('riktningar') or {}) if str(n).isdigit()]
    if not riktningar:
        return True
    domar = las_json(rot / 'AGARENS-DOM.json') or {}
    return all(b in domar for b in 'ABCDE'[:len(riktningar)])


def designprov(slug):
    """Förslagen under bokstäver, med startsidans första vy och helsida i båda bredderna och undersidans början, och
    huvudreferensens bilder. Vilken riktning en bokstav är, och panelens dom, visas först när ägaren dömt alla."""
    import referensval
    rot = UNDERLAG / slug / 'atelje'
    manifest = las_json(rot / 'FOTOGRAFERADE.json') or {}
    riktningar = sorted(int(n) for n in (manifest.get('riktningar') or {}) if str(n).isdigit())
    domar = las_json(rot / 'AGARENS-DOM.json') or {}
    forslag = []
    for b, n in zip('ABCDE', designprov_ordning(slug, riktningar)):
        bilder = {}
        for namn, fil in (('390-forsta', 'vy-390-forsta.png'), ('1440-forsta', 'vy-1440-forsta.png'), ('390-hela', 'vy-390-hela.png'),
                          ('1440-hela', 'vy-1440-hela.png'), ('undersida-390', 'undersida/vy-390-forsta.png'), ('undersida-1440', 'undersida/vy-1440-forsta.png')):
            if (rot / str(n) / fil).is_file():
                bilder[namn] = 'underlag/%s/atelje/%d/%s' % (slug, n, fil)
        forslag.append({'bokstav': b, 'bilder': bilder, 'dom': domar.get(b)})
    hr = referensval.huvudreferens(slug, UNDERLAG)
    svar = {'slug': slug, 'forslag': forslag,
            'huvudreferens': {'namn': hr['namn'], 'vad': hr['vad'], 'bilder': [{'fil': str(p.relative_to(ROOT)), 'text': t} for p, t in hr['bilder']]} if hr else None}
    if forslag and all(f['dom'] for f in forslag):
        val = las_json(rot / 'VAL.json') or {}
        svar['avslojat'] = {'karta': {b: n for b, n in zip('ABCDE', designprov_ordning(slug, riktningar))},
                            'panelens_val': val.get('val'), 'ribban': val.get('ribban'), 'nivaer': val.get('nivaer'), 'poang': val.get('poang'),
                            'val_md': md(las_text(rot / 'VAL.md') or '')}
    return svar


def spara_designprov(slug, bokstav, data):
    """Ägarens dom över ett förslag: håller ribban, nivå och vad som skiljer. Privat (underlag/<slug>/atelje/AGARENS-DOM.json)."""
    import fcntl
    if slug not in designprov_slugar():
        raise ValueError('okänt designprov')
    if bokstav not in {f['bokstav'] for f in designprov(slug)['forslag']}:
        raise ValueError('okänt förslag')
    if data.get('niva') not in NIVAER or not isinstance(data.get('haller'), bool):
        raise ValueError('välj nivå och om förslaget håller ribban')
    f = UNDERLAG / slug / 'atelje' / 'AGARENS-DOM.json'
    with DP_LAS, open(f.parent / '.agarens-dom.las', 'w') as las:
        fcntl.flock(las, fcntl.LOCK_EX)
        try:
            domar = {}
            if f.exists():
                try:
                    domar = json.loads(f.read_text(encoding='utf-8'))
                except (OSError, ValueError) as e:
                    raise RuntimeError('AGARENS-DOM.json går inte att läsa (%s); rätta filen innan en dom sparas' % e)
            domar[bokstav] = {'haller': data['haller'], 'niva': data['niva'], 'skiljer': (data.get('skiljer') or '').strip()[:4000], 'tid': nu()}
            tmp = f.with_name('.AGARENS-DOM.json.tmp%d' % os.getpid())
            tmp.write_text(json.dumps(domar, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            os.replace(tmp, f)
        finally:
            fcntl.flock(las, fcntl.LOCK_UN)
    return {'ok': True, 'dom': domar[bokstav]}


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
    # Domen blir automatiskt en vilande post i backloggen (loop 3): en session ägaren startar gör textändringen. Posten
    # och den publika raden får inga fritextsvar (personuppgifter; BESLUT.md 2026-10-03).
    betyg = '; '.join('%s: %s' % (karn[k]['fraga'], publikt_varde(karn[k], svar.get(k))) for k in ('namn', 'battre', 'specifik')
                      if publikt_varde(karn[k], svar.get(k)) is not None)
    pid = bl.ny('dom', 'Dom L%d (%s)' % (n, slug),
                'Ägarens dom L%d om %s: ordagrant i underlag/LARDOMAR-original.md (privat, utanför git) och kunder/%s/DOM.json. %s'
                % (n, slug, slug, betyg or 'Betygen står i LARDOMAR.md.'),
                forslag='Läs domen ordagrant i underlag/LARDOMAR-original.md (L%d, privat) och kunder/%s/DOM.json. Gör en textändring i '
                        'skillen bygg-sajt eller en fil i kunskap/ som svarar mot det ägaren pekar på. En ändring, liten nog att läsa på '
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
        ut.append(p)
    ordning = {'pagar': 0, 'vilande': 1, 'klar': 2, 'avvisad': 3}
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


def spaning_lista():
    lista = las_json(SPANING / 'KANDIDATER.json') or []
    nya = [k for k in lista if k.get('status') == 'ny']
    return {'kandidater': nya[:20], 'antal': len(nya), 'senast': las_json(SPANING / 'SENAST.json'), 'pagar': bool(spaning_pagar()),
            'av': bool(os.environ.get('NWP_SPANING_AV')), 'intervall_dagar': SPANING_INTERVALL}


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
            m = re.match(r'^/visa/([a-z0-9-]{2,60})$', vag)
            if m:
                url = visa(m.group(1))
                if url:
                    return self.skicka(302, '', extra={'Location': url})
                return self.skicka(404, '<p>Sajten är inte byggd än.</p>', 'text/html; charset=utf-8')
            m = re.match(r'^/fil/((?:kunder|underlag)/[a-z0-9-]{2,60}/.+)$', vag)
            if m:
                p = (ROOT / m.group(1)).resolve()  # den verkliga filen avgör, inte den begärda sökvägen (revisionen, F14)
                rotar = [r for r in (KUNDER.resolve(), UNDERLAG.resolve()) if p.is_relative_to(r)]
                rel = (Path(rotar[0].name) / p.relative_to(rotar[0])).as_posix() if rotar else ''
                if rotar and fil_tillaten(rel) and p.is_file() \
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
        try:
            n = int(self.headers.get('Content-Length') or 0)
            data = json.loads(self.rfile.read(min(n, 56 * 1024 * 1024)) or b'{}')
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
            m = re.match(r'^/api/designprov/([a-z0-9-]{2,60})/([A-E])$', vag)
            if m:
                return self.skicka(200, spara_designprov(m.group(1), m.group(2), data))
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
            m = re.match(r'^/api/spaning/([a-f0-9]{12})/(ta-in|avfarda)$', vag)
            if m:
                return self.skicka(200, ta_in_kandidat(m.group(1)) if m.group(2) == 'ta-in' else avfarda_kandidat(m.group(1), data.get('skal')))
            return self.skicka(404, {'fel': 'finns inte'})
        except (ValueError, json.JSONDecodeError, OSError) as e:
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
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    print('Dashboard: http://127.0.0.1:%d' % a.port, flush=True)
    def spaningsklocka():
        while True:
            try:
                spaning_vid_behov()
            except Exception as e:  # en klocka som dör ska inte ta med servern
                print('spaningen startade inte: %s' % e, flush=True)
            time.sleep(3600)
    threading.Thread(target=spaningsklocka, daemon=True).start()
    threading.Thread(target=lan_klocka, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
