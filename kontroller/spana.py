#!/usr/bin/env python3
"""spana.py — spanaren: letar kandidater åt kirurgen utan modell. Läser källorna i kunskap/spaning-kallor.md (flöden,
leverantörsdokumentation som sidbevakning, GitHub-sökningar via gh, Hacker News, awesome-listor som pekare), rensar
texten, rankar kandidaterna deterministiskt mot våra termer, slår ihop dubbletter, tar bort allt kirurgen redan sett
(kontroller/kallnyckel.py) och sparar i kirurgen/spaning/. Kandidaterna är data; spanaren skriver aldrig i registret,
backloggen eller en not, och kör eller installerar aldrig något ur en källa.

    .venv/bin/python kontroller/spana.py spana [--kallor FIL] [--max-per-kalla 5] [--bara TYP] [--torr]
    .venv/bin/python kontroller/spana.py lista [--alla]
    .venv/bin/python kontroller/spana.py avfard <id> --skal "…"
    .venv/bin/python kontroller/spana.py intagen <id> --intag <intag-id>

Exit: 0 klar (enskilda källor får falla) · 1 alla källor föll · 2 fel i anropet eller en spaning pågår.
Miljö: NWP_SPANING_MAX_KANDIDATER (200), NWP_SPANING_MAX_ANROP (120), NWP_SPANING_MAX_PER_KALLA (5), NWP_SPANING_PAUS (1,0 s
mellan anrop till samma värd), NWP_SPANING_INTERVALL_DAGAR (7, används av dashboarden), NWP_SPANING_AV (dashboarden kör inte).
"""
import argparse
import contextlib
import fcntl
import hashlib
import html
import json
import math
import os
import re
import shlex
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kallnyckel as kn  # noqa: E402

try:
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
KALLOR = ROOT / 'kunskap' / 'spaning-kallor.md'
SPANING = ROOT / 'kirurgen' / 'spaning'
UA = 'nortropic-webb-pro-spanare/0.1 (+https://github.com/Nortropic/nortropic-webb-pro)'
MAX_KANDIDATER = int(os.environ.get('NWP_SPANING_MAX_KANDIDATER') or 200)
MAX_ANROP = int(os.environ.get('NWP_SPANING_MAX_ANROP') or 120)
MAX_PER_KALLA = int(os.environ.get('NWP_SPANING_MAX_PER_KALLA') or 5)
PAUS = float(os.environ.get('NWP_SPANING_PAUS') or 1.0)
BYTE_FLODE, BYTE_SIDA, BYTE_KANDIDAT = 4_000_000, 256_000, 64_000
NS = {'atom': 'http://www.w3.org/2005/Atom', 'media': 'http://search.yahoo.com/mrss/', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'dc': 'http://purl.org/dc/elements/1.1/'}

# Termerna är det spanaren letar efter: våra åtta steg och arbetet runt dem. Justera här, inte i koden under.
TERMER = {3: ['core web vitals', 'lcp', 'inp', 'cls', 'lighthouse', 'wcag', 'axe', 'accessibility', 'tillgänglighet', 'astro', 'claude code', 'skill',
              'nielsen', 'heuristic', 'heuristisk', 'local business', 'småföretag', 'hantverkare', 'conversion', 'konvertering', 'cognitive walkthrough',
              'five second test', 'usability test', 'användbarhet'],
          2: ['ux', 'ui', 'seo', 'local seo', 'schema.org', 'forms', 'formulär', 'copywriting', 'typography', 'typografi', 'design system', 'static site',
              'performance', 'prestanda', 'a/b', 'evals', 'evaluation', 'prompt', 'agent', 'hooks', 'plugin', 'mcp', 'webbplats', 'hemsida', 'mobile first',
              'progressive enhancement', 'html', 'css', 'images', 'webp', 'avif', 'fonts', 'typsnitt', 'layout', 'color', 'färg', 'contrast', 'kontrast'],
          1: ['web', 'website', 'frontend', 'design', 'javascript', 'react', 'template', 'theme', 'checklist', 'audit', 'guide', 'best practices',
              'workflow', 'release', 'update', 'nytt', 'ny']}
TERM_RE = {vikt: [(t, re.compile(r'(?<![a-zåäö0-9])' + re.escape(t) + r'(?![a-zåäö0-9])', re.I)) for t in lista] for vikt, lista in TERMER.items()}
KALLVIKT = {'rss': 1.0, 'sida': 1.0, 'github': 1.0, 'hn': 1.0, 'awesome': 1.0}
LISTICLE = re.compile(r'^\s*\d+\s+(best|top|tools|tips|ways|things)', re.I)
DOLDA = re.compile(r'[​‌‍⁠﻿­‪-‮⁦-⁩]|[\x00-\x08\x0b\x0c\x0e-\x1f]')
TILL_AGENT = re.compile(r'(ignore (all |previous |the above )?instructions|you are (an|a) (ai|assistant|agent)|system prompt|<\s*(system|assistant|instructions?)\b|do not tell the user|as an ai)', re.I)
HOPPA_VARD = re.compile(r'(^|\.)(reddit|x|twitter|instagram|facebook|tiktok)\.com$', re.I)
STRAFF_VARD = {'medium.com': 0.7, 'linkedin.com': 0.5, 'dev.to': 0.9}


class SlutPaAnrop(Exception):
    pass


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def skriv_json(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp%d' % os.getpid())  # eget namn per process; två skrivare delar aldrig temporärfil
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


@contextlib.contextmanager
def last():
    """Lås kring läs–ändra–skriv av KANDIDATER.json och SEDDA.json: spanaren och dashboardens avfärdande får inte skriva
    över varandras status (revisionen 2026-10-03, F25)."""
    SPANING.mkdir(parents=True, exist_ok=True)
    with open(SPANING / '.las', 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def las_kallor(fil=None):
    """Raderna i tabellen: typ, namn, url (eller fråga), varfor, vikt. vikt 0 hoppas över."""
    ut = []
    try:
        text = Path(fil or KALLOR).read_text(encoding='utf-8')
    except OSError:
        return ut
    for rad in text.splitlines():
        if not rad.startswith('|') or rad.startswith('|---') or rad.lower().startswith('| typ'):
            continue
        celler = [c.strip() for c in rad.strip().strip('|').split('|')]
        if len(celler) < 5:
            continue
        typ, namn, url, varfor, vikt = celler[:5]
        try:
            vikt = float(vikt.replace(',', '.'))
        except ValueError:
            vikt = 1.0
        if typ in ('rss', 'sida', 'github', 'hn', 'awesome') and vikt > 0 and url:
            ut.append({'typ': typ, 'namn': namn, 'url': url, 'varfor': varfor, 'vikt': vikt, 'id': hashlib.sha1((typ + url).encode()).hexdigest()[:8]})
    return ut


class Hamtare:
    """requests-session med egen UA, tidsgränser, bytetak, en sekund mellan anrop till samma värd och ett hårt tak."""

    def __init__(self, max_anrop=MAX_ANROP, paus=PAUS, hamta=None):
        self.max_anrop, self.paus, self.anrop, self.senast = max_anrop, paus, 0, {}
        self._hamta = hamta
        self.session = None

    def hamta(self, url, tak=BYTE_SIDA):
        if self.anrop >= self.max_anrop:
            raise SlutPaAnrop('taket %d anrop per spaning är nått' % self.max_anrop)
        self.anrop += 1
        if self._hamta:
            return self._hamta(url, tak)
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers['User-Agent'] = UA
        vard = urlsplit(url).hostname or ''
        v = self.paus - (time.time() - self.senast.get(vard, 0))
        if v > 0:
            time.sleep(v)
        self.senast[vard] = time.time()
        r = self.session.get(url, timeout=(5, 15), stream=True, allow_redirects=True)
        if r.status_code >= 400:
            r.close()
            raise OSError('HTTP %d' % r.status_code)
        data = b''
        for bit in r.iter_content(16384):
            data += bit
            if len(data) > tak:
                break
        r.close()
        return data[:tak]


def rensa(text, langd=600):
    """Kontrolltecken och dolda tecken bort, HTML strippat, längd kapad. (text, varningar)."""
    varning = []
    t = html.unescape(re.sub(r'<[^>]+>', ' ', text or ''))
    if DOLDA.search(t):
        varning.append('dolda tecken')
        t = DOLDA.sub('', t)
    t = unicodedata.normalize('NFC', re.sub(r'\s+', ' ', t)).strip()
    if TILL_AGENT.search(t):
        varning.append('text till agenter')
    return t[:langd], varning


def datum_av(s):
    """ISO-datum ur RFC 822 eller ISO 8601, annars None."""
    if not s:
        return None
    s = s.strip()
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%d'):
        try:
            return datetime.strptime(s.replace('Z', '+0000'), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    m = re.match(r'(\d{4}-\d{2}-\d{2})', s)
    return m.group(1) if m else None


def kandidat(url, titel, sammanfattning, kalla, publicerad=None, popularitet=None, extra=None):
    t, v1 = rensa(titel, 200)
    s, v2 = rensa(sammanfattning, 600)
    k = {'id': kn.nyckel(url), 'url': url.strip(), 'nyckel': kn.normalisera(url), 'titel': t, 'sammanfattning': s, 'kalla': kalla['namn'],
         'kalla_typ': kalla['typ'], 'kalla_vikt': kalla['vikt'], 'kallor': [kalla['namn']], 'publicerad': publicerad, 'hittad': nu(),
         'popularitet': popularitet, 'varning': sorted(set(v1 + v2)), 'status': 'ny', 'intag_id': None, 'avfardad': None}
    if extra:
        k.update(extra)
    return k


# --- källtyper ---

def tolka_flode(data):
    """XML ur flödet; ett flöde som klippts vid bytetaket lagas vid sista hela posten."""
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        text = data.decode('utf-8', errors='replace')
        for slut, stang in (('</item>', '</channel></rss>'), ('</entry>', '</feed>')):
            i = text.rfind(slut)
            if i > 0:
                return ET.fromstring((text[:i + len(slut)] + stang).encode('utf-8'))
        raise


def rss(kalla, h):
    data = h.hamta(kalla['url'], BYTE_FLODE)
    rot = tolka_flode(data)
    ut = []
    tag = rot.tag.lower()
    if tag.endswith('feed'):  # Atom (YouTube-kanaler, GitHub releases)
        for e in rot.findall('atom:entry', NS):
            titel = (e.findtext('atom:title', '', NS) or '')
            lank = next((l.get('href') for l in e.findall('atom:link', NS) if l.get('href') and l.get('rel') in (None, 'alternate')), None)
            vid = e.findtext('yt:videoId', None, NS)
            if vid:
                lank = 'https://www.youtube.com/watch?v=' + vid
            if not lank:
                continue
            samm = e.findtext('atom:summary', '', NS) or e.findtext('atom:content', '', NS) or ''
            mg = e.find('media:group', NS)
            if mg is not None:
                samm = mg.findtext('media:description', '', NS) or samm
            pop = None
            st = e.find('.//media:statistics', NS)
            if st is not None and st.get('views', '').isdigit():
                pop = int(st.get('views'))
            pub = datum_av(e.findtext('atom:published', None, NS) or e.findtext('atom:updated', None, NS))
            ut.append(kandidat(lank, titel, samm, kalla, pub, pop))
    else:  # RSS 2.0
        for e in rot.iter('item'):
            lank = (e.findtext('link') or '').strip() or (e.find('guid').text.strip() if e.find('guid') is not None and e.find('guid').text and e.find('guid').text.startswith('http') else '')
            if not lank:
                continue
            ut.append(kandidat(lank, e.findtext('title') or '', e.findtext('description') or e.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or '', kalla,
                               datum_av(e.findtext('pubDate') or e.findtext('dc:date', None, NS))))
    return ut


def github(kalla, h, gh_json=None):
    """gh search repos … --json; --updated 90d och --created 180d blir datumfilter."""
    delar = shlex.split(kalla['url'])
    args, termer, i = [], [], 0
    while i < len(delar):
        d = delar[i]
        if d in ('--updated', '--created') and i + 1 < len(delar):
            v = delar[i + 1]
            m = re.match(r'^(\d+)d$', v)
            if m:
                v = '>=' + (datetime.now(timezone.utc) - timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d')
            args += [d, v]
            i += 2
        elif d.startswith('--') and i + 1 < len(delar):
            args += [d, delar[i + 1]]
            i += 2
        else:
            termer.append(d)
            i += 1
    if gh_json is None:
        h.anrop += 1
        r = subprocess.run(['gh', 'search', 'repos', *termer, *args, '--limit', '10', '--json', 'fullName,description,stargazersCount,pushedAt,createdAt,license,isArchived,url'],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise OSError('gh: ' + (r.stderr or '').strip()[-200:])
        gh_json = json.loads(r.stdout or '[]')
    ut = []
    for rep in gh_json:
        if rep.get('isArchived'):
            continue
        url = rep.get('url') or 'https://github.com/' + rep.get('fullName', '')
        ut.append(kandidat(url, rep.get('fullName') or '', rep.get('description') or '', kalla, datum_av(rep.get('pushedAt')), rep.get('stargazersCount'),
                           {'licens': ((rep.get('license') or {}).get('name') if isinstance(rep.get('license'), dict) else rep.get('license'))}))
    return ut


def hn(kalla, h):
    """Algolia tar inte OR: varje led blir en egen fråga (högst tre); citattecken tas bort."""
    sedan = int((datetime.now(timezone.utc) - timedelta(days=14)).timestamp())
    traffar = []
    for fraga in [f.strip().strip('"') for f in kalla['url'].split(' OR ')][:3]:
        url = 'https://hn.algolia.com/api/v1/search_by_date?query=%s&tags=story&numericFilters=points>50,created_at_i>%d&hitsPerPage=20' % (quote(fraga), sedan)
        d = json.loads(h.hamta(url, BYTE_FLODE).decode('utf-8', errors='replace'))
        traffar += d.get('hits') or []
    ut = []
    for t in traffar:
        lank = t.get('url')
        if not lank:
            if (t.get('points') or 0) < 200:
                continue
            lank = 'https://news.ycombinator.com/item?id=%s' % t.get('objectID')
        ut.append(kandidat(lank, t.get('title') or '', t.get('story_text') or '', kalla, datum_av(t.get('created_at')), t.get('points'), {'hn': 'https://news.ycombinator.com/item?id=%s' % t.get('objectID')}))
    return ut


def awesome(kalla, h, snapshots):
    """README:ns länkar; första gången bara baslinje, sedan bara nya länkar. Listan själv blir aldrig kandidat."""
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)', kalla['url'])
    if not m:
        raise OSError('awesome-källan måste vara ett GitHub-repo')
    rå = h.hamta('https://raw.githubusercontent.com/%s/%s/HEAD/README.md' % (m.group(1), m.group(2).removesuffix('.git')), BYTE_SIDA).decode('utf-8', errors='replace')
    lankar = {}
    for rad in rå.splitlines():
        if not rad.lstrip().startswith(('-', '*', '+')):
            continue
        for mm in re.finditer(r'\[([^\]]{2,120})\]\((https?://[^)\s]+)\)', rad):
            url = mm.group(2)
            if kn.normalisera(url) == kn.normalisera(kalla['url']):
                continue
            beskrivning = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', rad.lstrip('-*+ ').split(')', 1)[-1]).strip(' -–:')
            lankar.setdefault(kn.normalisera(url), (url, mm.group(1), beskrivning[:300]))
    fil = SPANING / ('snapshot-%s.json' % kalla['id'])
    gammal = snapshots.get(kalla['id'])
    if gammal is None:
        gammal = las_json(fil)
    snapshots[kalla['id']] = {'tid': nu(), 'lankar': sorted(lankar)}
    if gammal is None:
        return [], 'baslinje satt (%d länkar)' % len(lankar)
    nya = [k for k in lankar if k not in set(gammal.get('lankar') or [])]
    return [kandidat(lankar[k][0], lankar[k][1], lankar[k][2], kalla, None, None) for k in nya], None


def sida(kalla, h, snapshots):
    """Sidbevakning: texten hashas; vid ändring blir de tillagda raderna sammanfattningen."""
    rå = h.hamta(kalla['url'], BYTE_SIDA).decode('utf-8', errors='replace')
    text = re.sub(r'<(script|style|nav|footer)[^>]*>.*?</\1>', ' ', rå, flags=re.S | re.I)
    text, _ = rensa(text, 200000)
    rader = [r.strip() for r in re.split(r'(?<=[.!?])\s+|\n', text) if len(r.strip()) > 30]
    hashen = hashlib.sha1('\n'.join(rader).encode('utf-8')).hexdigest()
    fil = SPANING / ('snapshot-%s.json' % kalla['id'])
    gammal = snapshots.get(kalla['id'])
    if gammal is None:
        gammal = las_json(fil)
    snapshots[kalla['id']] = {'tid': nu(), 'hash': hashen, 'rader': rader[:2000]}
    if gammal is None:
        return [], 'baslinje satt'
    if gammal.get('hash') == hashen:
        return [], None
    tidigare = set(gammal.get('rader') or [])
    tillagda = [r for r in rader if r not in tidigare][:12]
    if not tillagda:
        return [], None
    titel = re.search(r'<title[^>]*>(.*?)</title>', rå, re.S | re.I)
    return [kandidat(kalla['url'] + '#andrad-' + nu()[:10], (titel.group(1) if titel else kalla['namn']) + ' (ändrad)', ' '.join(tillagda), kalla, nu()[:10], None, {'nyckel_override': kn.normalisera(kalla['url']) + '#' + nu()[:10]})], None


# --- rankning ---

def poang(k):
    hay = (k.get('titel') or '') + ' ' + (k.get('sammanfattning') or '')
    traffar, relevans = [], 0.0
    for vikt, lista in TERM_RE.items():
        for term, rx in lista:
            if rx.search(hay):
                traffar.append(term)
                relevans += vikt
    relevans = min(10.0, relevans)
    if k.get('kalla_vikt', 1.0) >= 1.5:
        relevans = max(relevans, 2.0)
    vikt = float(k.get('kalla_vikt') or 1.0)
    varfor = []
    if traffar:
        varfor.append('träffar: ' + ', '.join(sorted(set(traffar))[:8]))
    if k.get('kalla_vikt', 1.0) >= 1.5:
        varfor.append('leverantörsdokumentation ×%.1f' % vikt)
    elif vikt != 1.0:
        varfor.append('källvikt ×%.1f' % vikt)
    pop = k.get('popularitet') or 0
    if k.get('kalla_typ') == 'github' and pop >= 500:
        vikt *= 1.2
        varfor.append('≥ 500 stjärnor ×1,2')
    if k.get('kalla_typ') == 'hn':
        vikt *= 1.1 if pop >= 100 else 0.9
        varfor.append('HN %d poäng ×%s' % (pop, '1,1' if pop >= 100 else '0,9'))
    popf = 1 + 0.5 * min(math.log10(max(pop, 1)), 3) / 3
    dagar = 45
    if k.get('publicerad'):
        try:
            dagar = max(0, (datetime.now(timezone.utc).date() - datetime.strptime(k['publicerad'], '%Y-%m-%d').date()).days)
        except ValueError:
            pass
    farsk = 0.5 ** (dagar / 60.0)
    varfor.append('%d dagar ×%.2f' % (dagar, farsk))
    straff = 1.0
    titel = (k.get('titel') or '').lower()
    if 'awesome' in titel or 'curated list' in (k.get('sammanfattning') or '').lower() or 'awesome-' in (k.get('url') or '').lower():
        straff *= 0.5
        varfor.append('samlingslista ×0,5')
    if LISTICLE.match(k.get('titel') or ''):
        straff *= 0.7
        varfor.append('listicle ×0,7')
    vard = (urlsplit(k.get('url') or '').hostname or '').lower().removeprefix('www.')
    for d, f in STRAFF_VARD.items():
        if vard == d or vard.endswith('.' + d):
            straff *= f
            varfor.append('%s ×%s' % (d, str(f).replace('.', ',')))
    namn = (k.get('url') or '').rstrip('/').rsplit('/', 1)[-1].lower()
    icke_latin = sum(1 for c in (k.get('titel') or '') + (k.get('sammanfattning') or '') if c.isalpha() and not ('a' <= c.lower() <= 'z' or c.lower() in 'åäöéüø'))
    bokst = sum(1 for c in (k.get('titel') or '') + (k.get('sammanfattning') or '') if c.isalpha())
    if re.search(r'-(zh|cn|ja|ko)$', namn) or (bokst > 20 and icke_latin / bokst > 0.3):
        straff *= 0.5
        varfor.append('annat språk ×0,5')
        if 'annat språk' not in k.get('varning', []):
            k.setdefault('varning', []).append('annat språk')
    k['poang'] = round(relevans * vikt * popf * farsk * straff, 2)
    k['varfor'] = varfor
    k['traffar'] = sorted(set(traffar))
    return k


def sla_ihop(kandidater):
    ut = {}
    for k in kandidater:
        n = k.get('nyckel_override') or k['nyckel']
        if n in ut:
            b = ut[n]
            if k.get('kalla_vikt', 0) > b.get('kalla_vikt', 0):
                k['kallor'] = sorted(set(b['kallor'] + k['kallor']))
                k['popularitet'] = max(k.get('popularitet') or 0, b.get('popularitet') or 0) or None
                ut[n] = k
            else:
                b['kallor'] = sorted(set(b['kallor'] + k['kallor']))
                b['popularitet'] = max(k.get('popularitet') or 0, b.get('popularitet') or 0) or None
        else:
            ut[n] = k
    return list(ut.values())


def dedupe(kandidater, kanda):
    kvar, kanda_bort = [], 0
    for k in kandidater:
        n = k.get('nyckel_override') or k['nyckel']
        tr = kanda.get(n)
        if not tr:
            kvar.append(k)
            continue
        dom = (tr.get('dom') or '').lower()
        datum = tr.get('datum') or ''
        gammal = False
        try:
            gammal = (datetime.now(timezone.utc).date() - datetime.strptime(datum[:10], '%Y-%m-%d').date()).days > 180
        except ValueError:
            pass
        if dom.startswith('nej') and gammal and k.get('publicerad') and k['publicerad'] > datum[:10]:
            k['ny_version'] = True
            k['varning'] = sorted(set(k.get('varning', []) + ['ny version']))
            k['varfor'] = k.get('varfor', []) + ['dömd nej %s, nyare nu' % datum[:10]]
            kvar.append(k)
        else:
            kanda_bort += 1
    return kvar, kanda_bort


# --- körning ---

def spana(kallor, h, torr=False, bara=None, max_per_kalla=MAX_PER_KALLA, gh_json=None, kanda=None):
    SPANING.mkdir(parents=True, exist_ok=True)
    start = time.time()
    snapshots, rapport, alla, fel = {}, [], [], []
    kanda = kn.kanda_kallor() if kanda is None else kanda
    nyckel = lambda x: x.get('nyckel_override') or x['nyckel']  # noqa: E731
    redan = set()  # nycklar som sållats bort som kända, räknade en gång var
    for kalla in kallor:
        if bara and kalla['typ'] != bara:
            continue
        post = {'namn': kalla['namn'], 'typ': kalla['typ'], 'hamtade': 0, 'nya': 0, 'fel': None, 'not': None}
        try:
            if kalla['typ'] == 'rss':
                k = rss(kalla, h)
            elif kalla['typ'] == 'github':
                k = github(kalla, h, (gh_json or {}).get(kalla['id']) if gh_json else None)
            elif kalla['typ'] == 'hn':
                k = hn(kalla, h)
            elif kalla['typ'] == 'awesome':
                k, post['not'] = awesome(kalla, h, snapshots)
            else:
                k, post['not'] = sida(kalla, h, snapshots)
            k = [x for x in k if not HOPPA_VARD.search((urlsplit(x['url']).hostname or ''))]
            post['hamtade'] = len(k)
            k = [poang(x) for x in k]
            # redan bedömda bort före antalsbegränsningen: annars tränger kända toppresultat för alltid undan nya
            # kandidater längre ned i listan (revisionen 2026-10-03, F26)
            fore = {nyckel(x) for x in k}
            k, _ = dedupe(k, kanda)
            redan |= fore - {nyckel(x) for x in k}
            k.sort(key=lambda x: (-x['poang'], x['id']))
            alla += k[:max_per_kalla]
            post['nya'] = len(k[:max_per_kalla])
        except SlutPaAnrop as e:
            post['fel'] = str(e)
            fel.append('%s: %s' % (kalla['namn'], e))
            rapport.append(post)
            break
        except Exception as e:  # en källa som faller fäller inte spaningen
            post['fel'] = ('%s: %s' % (type(e).__name__, e))[:200]
            fel.append('%s: %s' % (kalla['namn'], post['fel']))
        rapport.append(post)
    alla = sla_ihop(alla)
    fore = {nyckel(x) for x in alla}
    alla, _ = dedupe(alla, kanda)
    redan |= fore - {nyckel(x) for x in alla}
    with last():
        return _skriv_resultat(alla, rapport, fel, snapshots, len(redan), start, torr, h)


def _skriv_resultat(alla, rapport, fel, snapshots, redan, start, torr, h):
    """Slå ihop med listan på disk och skriv, under låset: ägarens avfärdande under spaningen får inte återställas."""
    gamla = las_json(SPANING / 'KANDIDATER.json') or []
    behall = []
    grans = (datetime.now(timezone.utc) - timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%SZ')
    nya_nycklar = {k['id'] for k in alla}
    for g in gamla:
        if g.get('status') != 'ny' or g['id'] in nya_nycklar or (g.get('hittad') or '') < grans:
            if g.get('status') != 'ny':
                behall.append(g)
            continue
        behall.append(poang(g))
    nya_antal = sum(1 for k in alla if k['id'] not in {g['id'] for g in gamla})
    lista = behall + alla
    lista = [k for k in lista if k.get('status') == 'ny'] + [k for k in lista if k.get('status') != 'ny']
    lista.sort(key=lambda x: (x.get('status') != 'ny', -(x.get('poang') or 0), x['id']))
    lista = lista[:MAX_KANDIDATER] + [k for k in lista[MAX_KANDIDATER:] if k.get('status') != 'ny'][:200]
    senast = {'start': datetime.fromtimestamp(start, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'slut': nu(), 'sekunder': round(time.time() - start),
              'anrop': h.anrop, 'kallor': rapport, 'nya': nya_antal, 'redan_kanda': redan, 'fel': fel, 'torr': torr, 'antal': sum(1 for k in lista if k.get('status') == 'ny')}
    if torr:
        skriv_json(SPANING / 'TORR.json', {'senast': senast, 'kandidater': [k for k in lista if k.get('status') == 'ny'][:20]})
        return senast, lista
    for kid, snap in snapshots.items():
        skriv_json(SPANING / ('snapshot-%s.json' % kid), snap)
    skriv_json(SPANING / 'KANDIDATER.json', lista)
    skriv_json(SPANING / 'SENAST.json', senast)
    with open(SPANING / 'logg.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps({'tid': nu(), 'handelse': 'spaning', **{k: senast[k] for k in ('sekunder', 'anrop', 'nya', 'redan_kanda', 'antal')}, 'fel': len(fel)}, ensure_ascii=False) + '\n')
    return senast, lista


def satt(ident, status, **falt):
    with last():
        lista = las_json(SPANING / 'KANDIDATER.json') or []
        k = next((x for x in lista if x['id'] == ident), None)
        if not k:
            raise ValueError('ingen kandidat %s' % ident)
        k['status'] = status
        k.update(falt)
        skriv_json(SPANING / 'KANDIDATER.json', lista)
        sedda = las_json(SPANING / 'SEDDA.json') or {}
        sedda[k.get('nyckel_override') or k['nyckel']] = {'status': status, 'tid': nu(), 'skal': falt.get('avfardad'), 'intag_id': falt.get('intag_id'), 'titel': k.get('titel')}
        skriv_json(SPANING / 'SEDDA.json', sedda)
    return k


def main(argv=None):
    p = argparse.ArgumentParser(prog='spana', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='kommando', required=True)
    s = sub.add_parser('spana')
    s.add_argument('--kallor')
    s.add_argument('--max-per-kalla', type=int, default=MAX_PER_KALLA)
    s.add_argument('--bara', choices=('rss', 'sida', 'github', 'hn', 'awesome'))
    s.add_argument('--torr', action='store_true')
    s = sub.add_parser('lista')
    s.add_argument('--alla', action='store_true')
    s = sub.add_parser('avfard')
    s.add_argument('id')
    s.add_argument('--skal', default='')
    s = sub.add_parser('intagen')
    s.add_argument('id')
    s.add_argument('--intag', required=True)
    s = sub.add_parser('sedd')
    s.add_argument('id')
    a = p.parse_args(argv)
    if a.kommando == 'spana':
        SPANING.mkdir(parents=True, exist_ok=True)
        pagar = SPANING / 'PAGAR'
        try:
            pid = int(pagar.read_text().strip() or 0)
            os.kill(pid, 0)
            print('en spaning pågår redan (pid %d)' % pid, file=sys.stderr)
            return 2
        except (OSError, ValueError):
            pass
        pagar.write_text(str(os.getpid()))
        try:
            kallor = las_kallor(a.kallor)
            if not kallor:
                print('inga källor i %s' % (a.kallor or KALLOR), file=sys.stderr)
                return 2
            senast, lista = spana(kallor, Hamtare(), torr=a.torr, bara=a.bara, max_per_kalla=a.max_per_kalla)
        finally:
            pagar.unlink(missing_ok=True)
        print('spaning: %d källor, %d anrop, %d nya, %d redan kända, %d fel, %d s%s' % (len(senast['kallor']), senast['anrop'], senast['nya'], senast['redan_kanda'], len(senast['fel']), senast['sekunder'], ' (torr)' if a.torr else ''))
        for f in senast['fel']:
            print('  fel: ' + f)
        for k in [x for x in lista if x.get('status') == 'ny'][:20]:
            print('  %5.2f  %-60s %s  [%s]' % (k.get('poang') or 0, k['titel'][:60], k['url'][:70], k['kalla']))
        return 0 if senast['kallor'] and len(senast['fel']) < len(senast['kallor']) else 1
    if a.kommando == 'lista':
        for k in las_json(SPANING / 'KANDIDATER.json') or []:
            if a.alla or k.get('status') == 'ny':
                print('%s  %5.2f  %-8s %-50s %s' % (k['id'], k.get('poang') or 0, k.get('status'), k['titel'][:50], k['url'][:70]))
        return 0
    if a.kommando == 'avfard':
        satt(a.id, 'avfardad', avfardad=a.skal or 'utan skäl')
        return 0
    if a.kommando == 'intagen':
        satt(a.id, 'intagen', intag_id=a.intag)
        return 0
    if a.kommando == 'sedd':
        satt(a.id, 'sedd')
        return 0
    return 2


if __name__ == '__main__':
    sys.exit(main())
