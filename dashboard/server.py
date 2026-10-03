#!/usr/bin/env python3
"""Dashboard för nortropic-webb-pro. Lokal, läser repot och skriver bara ägarens domar.

    .venv/bin/python dashboard/server.py [--port 4771]     (eller ./dashboard.sh)

Visar byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag, körningens senaste händelser),
lärdomarna, kirurgens register och kommandona. Skriver bara när ägaren skickar frågeformuläret efter ett bygge:
kunder/<slug>/DOM.json (strukturerat, privat) och en post i LARDOMAR.md (ordagrant, i git).
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
from prova import Server  # noqa: E402  (samma statiska server som provet använder)
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
    t = html.escape(t, quote=False)
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
    return {
        'slug': slug, 'namn': v.get('namn') or slug,
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
    egna = las_json(KUNDER / slug / 'FRAGOR.json')
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
        'fragor': {'karna': KARNFRAGOR, 'egna': egna if isinstance(egna, list) else []},
        'domar': (las_json(KUNDER / slug / 'DOM.json') or {}).get('domar', []),
        'granskning': granskningen(slug, b['domd']),
    })
    if ab_oavgjord(slug):
        dolt = '<p>Dolt tills du har valt i Jämförelser, så att jämförelsen förblir blind.</p>'
        # också byggets egna frågor: ateljéarmens riktningsfråga visar bilder ur atelje/ och avslöjar armen
        b.update({'ab_dold': True, 'rapport': dolt, 'prov_md': dolt, 'underlag': {'Dolt': dolt}, 'korning': None,
                  'fragor': {'karna': KARNFRAGOR, 'egna': []}})
    return b


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
                   'val': p.get('val'), 'kommentar': p.get('kommentar'), 'byggen': byggen})
    return ut


def spara_ab(ident, data):
    f = AB / (ident + '.json')
    p = las_json(f) if re.fullmatch(r'ab-[a-z0-9-]+-\d{8}T\d{6}Z', ident or '') else None
    if not p:
        raise ValueError('okänd jämförelse')
    if p.get('val') is not None:
        raise ValueError('redan vald')
    val = data.get('val')
    if val not in p['byggen'] + ['lika']:
        raise ValueError('välj A, B eller lika')
    p.update(val=val, kommentar=(data.get('kommentar') or '').strip()[:4000], valt=nu(), status='vald')
    f.write_text(json.dumps(p, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    etikett = {s: 'AB'[i] for i, s in enumerate(p['byggen'])}
    rader = ['', '## AB · %s · %s: %s' % (p['valt'][:10], p['variabel'], ' mot '.join('%s=%s' % (etikett[s], p['varden'][s]) for s in p['byggen'])), '',
             '- **Ägarens val (blint):** %s' % ('lika' if val == 'lika' else '%s (%s=%s)' % (etikett[val], p['variabel'], p['varden'][val])),
             *(['- **Ägarens ord:** ' + p['kommentar'].replace('\n', ' / ')] if p['kommentar'] else []),
             *['- %s (%s=%s): %s' % (etikett[s], p['variabel'], p['varden'][s], json.dumps((p.get('korningar') or {}).get(s, {}), ensure_ascii=False))
               for s in p['byggen']], '']
    lar = ROOT / 'LARDOMAR.md'
    with open(lar, 'a', encoding='utf-8') as fh:
        fh.write('\n'.join(rader))
    return {'ok': True, 'git': commit_agarens(['LARDOMAR.md'], 'Ägaren: A/B %s' % p['variabel']), 'jamforelse': ab_lista()}


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
            'fragor': {'karna': KARNFRAGOR, 'egna': las_json(KUNDER / slug / 'FRAGOR.json') or []}}
    fil = KUNDER / slug / 'DOM.json'
    allt = las_json(fil) or {'schema': 1, 'slug': slug, 'domar': []}
    allt['domar'].append(post)
    fil.write_text(json.dumps(allt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    lar = ROOT / 'LARDOMAR.md'
    befintlig = las_text(lar) or '# Lärdomar — ägarens domar\n'
    n = max([int(x) for x in re.findall(r'^## L(\d+) ', befintlig, re.M)] or [-1]) + 1
    alla = {f['id']: f for f in KARNFRAGOR + (post['fragor']['egna'] if isinstance(post['fragor']['egna'], list) else []) if isinstance(f, dict) and 'id' in f}
    rader = ['', '## L%d · %s · %s' % (n, post['tid'][:10], slug), '']
    for fid, v in svar.items():
        if v in (None, '', {}, []):
            continue
        fraga = (alla.get(fid) or {}).get('fraga', fid)
        if isinstance(v, dict):
            v = ', '.join('%s: %s' % (k, x) for k, x in v.items() if x)
        rader.append('- **%s** %s' % (fraga, str(v).replace('\n', ' / ')))
    rader += ['', '**Ändring:** väntar', '']
    # Domen blir automatiskt en vilande post i backloggen (loop 3): en session ägaren startar gör textändringen.
    kort = (svar.get('en_andring') or svar.get('samsta') or svar.get('mall_tecken') or 'se domen').strip().replace('\n', ' ')
    sammandrag = '; '.join('%s: %s' % ((alla.get(k) or {}).get('fraga', k), svar[k]) for k in ('namn', 'battre', 'specifik', 'samsta', 'mall_tecken', 'en_andring')
                           if isinstance(svar.get(k), (str, int)) and str(svar.get(k)).strip())
    pid = bl.ny('dom', 'Dom L%d (%s): %s' % (n, slug, kort[:90]), sammandrag or 'Ägarens dom, se LARDOMAR.md.',
                forslag='Läs domen i LARDOMAR.md (L%d) och kunder/%s/DOM.json. Gör en textändring i skillen bygg-sajt eller en fil i '
                        'kunskap/ som svarar mot det ägaren pekar på. En ändring, liten nog att läsa på fem minuter.' % (n, slug),
                klart='Ändringen är committad och raden Ändring under L%d i LARDOMAR.md pekar på commiten.' % n,
                sar='L%d' % n, kallref='LARDOMAR.md L%d' % n)
    rader[-2] = '**Ändring:** väntar (backlog %s)' % pid
    with open(lar, 'a', encoding='utf-8') as f:
        f.write('\n'.join(rader))
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

VISNING = {}
VISNING_LAN = {}
LAN = {'pa': True}


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
    if slug not in VISNING_LAN:
        srv = Server(dist, vard=ip)
        srv.__enter__()
        VISNING_LAN[slug] = srv
    return VISNING_LAN[slug].url + '/'


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

    def do_GET(self):
        vag = unquote(urlsplit(self.path).path)
        try:
            if vag in ('/', '/index.html'):
                return self.skicka(200, (Path(__file__).parent / 'index.html').read_bytes(), 'text/html; charset=utf-8')
            if vag == '/api/oversikt':
                bk = backloggen()
                return self.skicka(200, {'byggen': byggen(), 'lardomar': md(las_text(ROOT / 'LARDOMAR.md')),
                                         'backlog_vilande': sum(1 for p in bk if p.get('status') == 'vilande'),
                                         'intag_pagar': sum(1 for x in intag_lista() if x['pagar']),
                                         'prospekt_vantar': pv.raknare(),
                                         'granskare': granskare_overens(), 'tid': nu()})
            if vag == '/api/ab':
                return self.skicka(200, ab_lista())
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
            if m:
                if not visa(m.group(1)):
                    return self.skicka(404, {'fel': 'sajten är inte byggd än'})
                url = visa_lan(m.group(1))
                skal = None if url else ('avstängd (--utan-lan)' if not LAN['pa'] else 'ingen adress i ett lokalt nätverk hittades')
                return self.skicka(200, {'natverk': url, 'qr': qr.svg(url) if url else None, 'skal': skal})
            m = re.match(r'^/visa/([a-z0-9-]{2,60})$', vag)
            if m:
                url = visa(m.group(1))
                if url:
                    return self.skicka(302, '', extra={'Location': url})
                return self.skicka(404, '<p>Sajten är inte byggd än.</p>', 'text/html; charset=utf-8')
            m = re.match(r'^/fil/((?:kunder|underlag)/[a-z0-9-]{2,60}/.+)$', vag)
            if m:
                p = (ROOT / m.group(1)).resolve()
                if (p.is_relative_to(KUNDER.resolve()) or p.is_relative_to(UNDERLAG.resolve())) and p.is_file() \
                        and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.md', '.json', '.txt', '.log'):
                    typ = mimetypes.guess_type(p.name)[0] or 'text/plain'
                    if typ.startswith('text/') or typ.endswith('json'):
                        typ += '; charset=utf-8'
                    return self.skicka(200, p.read_bytes(), typ)
            return self.skicka(404, {'fel': 'finns inte'})
        except Exception as e:  # dashboarden ska visa felet, inte dö
            return self.skicka(500, {'fel': '%s: %s' % (type(e).__name__, e)})

    def do_POST(self):
        vag = urlsplit(self.path).path
        ursprung = self.headers.get('Origin') or ''
        vard = self.headers.get('Host') or ''
        if urlsplit(ursprung).netloc != vard:
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
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    print('Dashboard: http://127.0.0.1:%d' % a.port, flush=True)
    def spaningsklocka():
        while True:
            try:
                spaning_vid_behov()
            except Exception as e:  # en klocka som dör ska inte ta med servern
                print('spaningen startade inte: %s' % e, flush=True)
            time.sleep(3600)
    import threading
    threading.Thread(target=spaningsklocka, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
