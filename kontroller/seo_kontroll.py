#!/usr/bin/env python3
"""SEO-kontroll: teknisk och innehållsmässig läsning av ett renderat bygge (katalog med HTML eller en sitemap-lista av
lokala filer) mot brief och verksamhetsuppgifter. Rapport, inga rankningslöften: metadata eller Lighthouse-SEO ensamt är
ingen SEO-funktion (ordern avsnitt 4). Kontrollerar per sida: title och description (längd, unika), en h1, canonical,
robots/noindex-läge mot avsett läge (förhandsvisning: noindex; lansering: index), hreflang-par, JSON-LD (giltig JSON,
typ och egenskaper mot schema.org:s vokabulär, sanningsenlighet mot VERKSAMHET.json: namn, telefon, adress bara när
publik, öppettider), interna länkar som löser, bildalt; per sajt: sitemap.xml och robots.txt finns och stämmer, kanonisk
domän, omdirigeringskarta vid migrering (--omdirigeringar FIL: gamla URL:er ska finnas som mål eller 301-rad).

    python3 -B verktyg/seo_kontroll.py --bygge KATALOG --lage forhandsvisning|lansering [--verksamhet VERKSAMHET.json]
        [--doman example.se] [--omdirigeringar REDIRECTS.json] --ut RAPPORT.json [--md RAPPORT.md]

Exit 0 (rapport skriven), 2 vid felaktiga argument. Ingen nätåtkomst: läser filer.
"""
import argparse
import html as htmlmod
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)
import verksamhetsuppgifter as vu  # noqa: E402

TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.S | re.I)
META = re.compile(r'<meta\s+[^>]*>', re.I)
ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*["\']([^"\']*)["\']')
H1 = re.compile(r'<h1\b', re.I)
LINK = re.compile(r'<link\s+[^>]*>', re.I)
A = re.compile(r'<a\s+[^>]*href=["\']([^"\'#?]+)[^"\']*["\']', re.I)
IMG = re.compile(r'<img\b[^>]*>', re.I)
JSONLD = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
LANG = re.compile(r'<html\b[^>]*\blang=["\']([^"\']+)["\']', re.I)


def attrs(tag):
    a = {k.lower(): htmlmod.unescape(v) for k, v in ATTR.findall(tag)}
    # attribut utan värde (<img alt src=…>, som Astro skriver för alt=""): tom alt är giltig för dekor
    utan_varden = re.sub(r'=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', '', tag)
    for k in re.findall(r'\s([a-zA-Z][a-zA-Z0-9-]*)', utan_varden):
        a.setdefault(k.lower(), '')
    return a


def sidor(bygge):
    root = Path(bygge)
    for f in sorted(root.rglob('*.html')):
        if not (set(f.parts) & {'node_modules', '.git', '.next', '.vercel'}):
            yield f


def url_for(root, f):
    rel = f.relative_to(root).as_posix()
    if rel.endswith('index.html'):
        rel = rel[:-len('index.html')]
    return '/' + rel.lstrip('/')


def finns_lokalt(root, href):
    p = urlparse(href)
    if p.scheme or p.netloc:
        return None  # extern: inte kontrollerad
    path = p.path
    if not path.startswith('/'):
        return None
    cands = [root / path.lstrip('/'), root / path.lstrip('/') / 'index.html', root / (path.lstrip('/').rstrip('/') + '.html'), root / (path.lstrip('/').rstrip('/') + '/index.html')]
    return any(c.is_file() for c in cands)


def granska_sida(root, f, raw, lage, verksamhet, doman):
    fynd = []
    url = url_for(root, f)
    # 404-sidan och tacksidan ska ha noindex och ingen canonical (byggstandarden 6.7 och 7.2, ägarens domar L1–L3)
    ar_404 = f.relative_to(root).as_posix() in ('404.html', 'tack/index.html')
    m = TITLE.search(raw)
    title = htmlmod.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
    if not title:
        fynd.append(('title saknas', 'varje sida behöver en unik, sanningsenlig title'))
    elif len(title) > 60:
        fynd.append(('title lång (%d)' % len(title), 'högst omkring 60 tecken; inga superlativ'))
    metas = [attrs(t) for t in META.findall(raw)]
    desc = next((mm.get('content', '') for mm in metas if mm.get('name', '').lower() == 'description'), None)
    if desc is None:
        fynd.append(('description saknas', 'kort beskrivning av sidans innehåll'))
    elif len(desc) > 155:
        fynd.append(('description lång (%d)' % len(desc), 'högst omkring 155 tecken'))
    robots = next((mm.get('content', '').lower() for mm in metas if mm.get('name', '').lower() == 'robots'), '')
    noindex = 'noindex' in robots
    if lage == 'forhandsvisning' and not noindex:
        fynd.append(('index tillåten i förhandsvisning', 'förhandsvisningen ska bära noindex (och skydd); lanseringskonfigurationen är en annan'))
    if lage == 'lansering' and noindex and not ar_404:
        fynd.append(('noindex kvar vid lansering', 'noindex ska bort i lanseringskonfigurationen, annars samlar sökkonsolen inget'))
    n_h1 = len(H1.findall(raw))
    if n_h1 != 1:
        fynd.append(('h1: %d' % n_h1, 'en h1 per sida som svarar på sidans sökintention'))
    if not LANG.search(raw):
        fynd.append(('html lang saknas', 'ange sidans språk'))
    links = [attrs(t) for t in LINK.findall(raw)]
    canon = [l.get('href') for l in links if l.get('rel', '').lower() == 'canonical']
    if ar_404:
        pass
    elif not canon:
        fynd.append(('canonical saknas', 'absolut canonical per sida'))
    else:
        c = canon[0]
        if not c.startswith('https://'):
            fynd.append(('canonical inte absolut https', c))
        elif doman and urlparse(c).netloc not in (doman, 'www.' + doman):
            fynd.append(('canonical annan domän', c + ' mot ' + doman))
    hreflang = [(l.get('hreflang'), l.get('href')) for l in links if l.get('rel', '').lower() == 'alternate' and l.get('hreflang')]
    if hreflang and not any(h[0] == 'x-default' for h in hreflang):
        fynd.append(('hreflang utan x-default', 'varje variantuppsättning listar alla varianter och x-default'))
    for href in set(A.findall(raw)):
        ok = finns_lokalt(root, href)
        if ok is False:
            fynd.append(('intern länk löser inte', href))
    for tag in IMG.findall(raw):
        a = attrs(tag)
        if 'alt' not in a:
            fynd.append(('img utan alt', (a.get('src') or '')[:80]))
    for block in JSONLD.findall(raw):
        try:
            data = json.loads(block)
        except ValueError:
            fynd.append(('JSON-LD ogiltig', 'blocket är inte giltig JSON'))
            continue
        for obj in (data if isinstance(data, list) else [data]):
            fynd.extend(granska_schema(obj, verksamhet))
    # utgångna schema.org-termer fungerar än; de är information, inte fynd (räknas inte i grinden)
    return {'sida': url, 'title': title, 'noindex': noindex, 'fynd': [{'typ': t, 'text': x} for t, x in fynd if t not in INFO_TYPER],
            'info': [{'typ': t, 'text': x} for t, x in fynd if t in INFO_TYPER]}


_VOKABULAR = None
INFO_TYPER = {'JSON-LD utgången typ', 'JSON-LD utgången egenskap'}


def vokabular():
    """schema.org:s klasser och egenskaper (kontroller/data/schemaorg.json, CC BY-SA 3.0); None om filen saknas."""
    global _VOKABULAR
    if _VOKABULAR is None:
        try:
            _VOKABULAR = json.loads((Path(__file__).parent / 'data' / 'schemaorg.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            _VOKABULAR = {}
    return _VOKABULAR or None


def granska_vokabular(obj, v, vag=''):
    """Varje @type ska vara en klass, varje egenskap finnas och höra till typen eller en förälder (domainIncludes);
    utgången term ger en rad med ersättaren (webstudio-intaget 2026-10-03). Inbäddade objekt prövas också."""
    fynd = []
    typer = typlista(obj)  # samma normalisering som verksamhetsnoden: också schema:Bakery (omgång sex, F20)
    kanda = [x for x in typer if x in v['klasser']]
    for x in typer:
        if x not in v['klasser']:
            fynd.append(('JSON-LD okänd typ', '%s%s finns inte i schema.org' % (vag, x)))
        elif x in v['ersatt']:
            fynd.append(('JSON-LD utgången typ', '%s%s; använd %s' % (vag, x, v['ersatt'][x])))
    anor = set()
    stack = list(kanda)
    while stack:
        k = stack.pop()
        if k not in anor:
            anor.add(k)
            stack.extend(v['klasser'].get(k, []))
    for nyckel, varde in obj.items():
        if nyckel.startswith('@'):
            continue
        nyckel = typnamn(nyckel)  # egenskaper kan också vara kompakta IRI:er (schema:name)
        if nyckel not in v['egenskaper']:
            fynd.append(('JSON-LD okänd egenskap', '%s%s finns inte i schema.org' % (vag, nyckel)))
            continue
        if nyckel in v['ersatt']:
            fynd.append(('JSON-LD utgången egenskap', '%s%s; använd %s' % (vag, nyckel, v['ersatt'][nyckel])))
        if kanda and v['egenskaper'][nyckel] and not anor & set(v['egenskaper'][nyckel]):
            fynd.append(('JSON-LD egenskap hör inte till typen', '%s%s på %s (hör till %s)' % (
                vag, nyckel, '/'.join(kanda), ', '.join(v['egenskaper'][nyckel][:4]))))
        for barn in (varde if isinstance(varde, list) else [varde]):
            if isinstance(barn, dict):
                fynd.extend(granska_vokabular(barn, v, '%s%s.' % (vag, nyckel)))
    return fynd


def noder(obj):
    """Verksamhetsnoderna i ett JSON-LD-block: objektet självt, eller noderna i en @context/@graph-behållare (giltig form
    enligt JSON-LD 1.1; revisionen 2026-10-03, F20). @type kan vara en sträng eller en lista."""
    if isinstance(obj.get('@graph'), list):
        return [n for n in obj['@graph'] if isinstance(n, dict)]
    return [obj]


def typnamn(t):
    """Typnamnet utan schema.org-prefix: https://schema.org/Bakery, http://schema.org/Bakery och schema:Bakery är giltiga
    IRI-former i JSON-LD och ska prövas som Bakery (omgång fem, F20)."""
    s = str(t).strip()
    return re.sub(r'^(https?://schema\.org/|schema:)', '', s)


def typlista(nod):
    t = nod.get('@type')
    return [typnamn(x) for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)]


def granska_schema(obj, verksamhet):
    fynd = []
    if not isinstance(obj, dict):
        return [('JSON-LD form', 'objekt väntades')]
    v = vokabular()
    for nod in noder(obj):
        typer = typlista(nod)
        if not typer:
            fynd.append(('JSON-LD utan @type', ''))
        if v:
            fynd.extend(granska_vokabular(nod, v))
        # verksamhetsnoden känns igen på typ och identitet, inte på att den råkar bära telefon eller adress (revisionen,
        # F20): en Person-nod prövas aldrig, och en annan organisation i grafen (memberOf, en branschorganisation) bara
        # när den har verksamhetens namn eller ligger på verksamhetens domän (@id eller url).
        if verksamhet and ar_verksamhetsnod(nod, typer, verksamhet, v):
            fynd.extend(granska_verksamhetsnod(nod, typer, verksamhet))
    return fynd


def ar_verksamhetsnod(nod, typer, verksamhet, v):
    """En nod i LocalBusiness-trädet är alltid verksamhetens (en lokal verksamhets sajt beskriver en verksamhet) och prövas
    mot underlaget: ett kvarlämnat mallinnehåll med annat namn, annan domän och fel telefon ska ge fynd, inte undantas
    (omgång fyra, F20). En nod i Organization-trädet prövas bara när den är verksamheten enligt namn eller värdnamn
    (parsat, inte delsträng); en annan organisation (memberOf, branschorganisation) lämnas."""
    lokal = any(t == 'LocalBusiness' or (v and 'LocalBusiness' in anor(t, v)) for t in typer)
    if lokal:
        return True
    org = any(t == 'Organization' or (v and 'Organization' in anor(t, v)) for t in typer)
    if not org:
        return False
    namn = lambda s: re.sub(r'\s+', ' ', str(s or '')).strip().casefold()  # noqa: E731
    webb = verksamhet.get('webb') if isinstance(verksamhet.get('webb'), dict) else {}
    doman = re.sub(r'^https?://', '', str((webb or {}).get('doman') or '')).strip('/').split('/')[0].casefold().removeprefix('www.')
    egna = set()
    for k in ('@id', 'url'):
        vard = (urlparse(str(nod.get(k) or '')).hostname or '').casefold().removeprefix('www.')
        if vard:
            egna.add(vard)
    return (bool(doman) and doman in egna) or namn(nod.get('name')) == namn(verksamhet.get('namn'))


def anor(typ, v):
    """Typen och alla dess överklasser i schema.org-hierarkin."""
    ut, stack = set(), [typ]
    while stack:
        k = stack.pop()
        if k not in ut:
            ut.add(k)
            stack.extend(v['klasser'].get(k, []))
    return ut


def granska_verksamhetsnod(obj, typer, verksamhet):
    """Namn, telefon och adress mot VERKSAMHET.json för en nod som beskriver verksamheten."""
    fynd = []
    n = vu.nap(verksamhet)
    if obj.get('name') and obj['name'] != verksamhet['namn']:
        fynd.append(('schema name ≠ verksamhetens namn', '%r mot %r' % (obj['name'], verksamhet['namn'])))
    if obj.get('telephone') and n['telefon_e164'] and obj['telephone'] != n['telefon_e164']:
        fynd.append(('schema telephone ≠ E.164 ur verksamheten', '%r mot %r' % (obj['telephone'], n['telefon_e164'])))
    if obj.get('address') and not n['adress_visas']:
        fynd.append(('schema bär adress fast adressen inte är publik', 'utelämna address; ange areaServed'))
    if n['adress_visas'] and not obj.get('address') and 'Organization' not in typer:
        fynd.append(('schema saknar address fast adressen är publik', 'PostalAddress med gata, postnummer NNN NN, ort, SE'))
    adr = obj.get('address') or {}
    if isinstance(adr, dict) and adr.get('postalCode') and not re.match(r'^\d{3} \d{2}$', str(adr['postalCode'])):
        fynd.append(('postalCode-form', str(adr['postalCode']) + ' ska vara "NNN NN"'))
    if isinstance(adr, dict) and n['adress_visas']:
        # fälten ska stämma med underlaget, inte bara ha rätt form (revisionen, F20)
        v_adr = verksamhet.get('adress') or {}
        slat = lambda s: re.sub(r'\s+', ' ', str(s or '')).strip().casefold()  # noqa: E731
        for falt, nyckel in (('postalCode', 'postnummer'), ('addressLocality', 'ort'), ('streetAddress', 'gata')):
            if adr.get(falt) and v_adr.get(nyckel) and slat(adr[falt]).replace(' ', '') != slat(v_adr[nyckel]).replace(' ', ''):
                fynd.append(('schema address ≠ verksamhetens adress', '%s %r mot %r' % (falt, adr[falt], v_adr[nyckel])))
    if obj.get('aggregateRating') and not verksamhet.get('omdomen_kalla'):
        fynd.append(('aggregateRating utan källa', 'betyg bara från verklig plattformsdata med källa i VERKSAMHET.json (omdomen_kalla)'))
    if 'offers' in obj and not obj.get('offers'):
        fynd.append(('offers tomt', 'utelämna hellre än att hitta på pris'))
    return fynd


def granska_sajt(root, lage, doman, omdirigeringar):
    fynd = []
    sm = root / 'sitemap.xml'
    rb = root / 'robots.txt'
    if not sm.is_file():
        fynd.append(('sitemap.xml saknas', 'genereras ur sidorna; lämnas till sökkonsolen vid lansering'))
    else:
        locs = re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', sm.read_text(encoding='utf-8', errors='replace'))
        if not locs:
            fynd.append(('sitemap utan loc', ''))
        if doman:
            for l in locs:
                if urlparse(l).netloc not in (doman, 'www.' + doman):
                    fynd.append(('sitemap loc annan domän', l))
                    break
    if not rb.is_file():
        fynd.append(('robots.txt saknas', ''))
    else:
        text = rb.read_text(encoding='utf-8', errors='replace')
        if 'Sitemap:' not in text:
            fynd.append(('robots utan Sitemap-rad', ''))
        if lage == 'lansering' and re.search(r'(?im)^Disallow:\s*/\s*$', text):
            fynd.append(('robots blockerar allt vid lansering', ''))
        if lage == 'forhandsvisning' and not re.search(r'(?im)^Disallow:\s*/\s*$', text):
            fynd.append(('robots tillåter crawl i förhandsvisning', 'förhandsvisning: Disallow: / och noindex'))
    if omdirigeringar:
        data = json.loads(Path(omdirigeringar).read_text(encoding='utf-8'))
        for rad in data.get('gamla', []):
            mal = rad.get('till')
            if not mal or rad.get('status') not in (301, 308):
                fynd.append(('omdirigering utan 301/308', rad.get('fran', '')))
            elif finns_lokalt(root, mal) is False:
                fynd.append(('omdirigeringsmål saknas', '%s → %s' % (rad.get('fran'), mal)))
    return [{'typ': t, 'text': x} for t, x in fynd]


def rapport(bygge, lage, verksamhet_fil=None, doman=None, omdirigeringar=None):
    root = Path(bygge)
    verksamhet = vu.las(verksamhet_fil) if verksamhet_fil else None
    if verksamhet and not doman:
        doman = (verksamhet.get('webb') or {}).get('doman')
    pages = []
    titles = {}
    for f in sidor(root):
        raw = f.read_text(encoding='utf-8', errors='replace')
        p = granska_sida(root, f, raw, lage, verksamhet, doman)
        titles.setdefault(p['title'], []).append(p['sida'])
        pages.append(p)
    for t, ss in titles.items():
        if t and len(ss) > 1:
            for p in pages:
                if p['sida'] in ss:
                    p['fynd'].append({'typ': 'title dubblett', 'text': ', '.join(ss)})
    sajt = granska_sajt(root, lage, doman, omdirigeringar)
    antal = sum(len(p['fynd']) for p in pages) + len(sajt)
    return {'schema': 1, 'bygge': str(root), 'lage': lage, 'doman': doman, 'sidor': len(pages), 'fynd_totalt': antal,
            'sajt': sajt, 'per_sida': pages, 'uppgiftsvarningar': vu.validera(verksamhet) if verksamhet else ['verksamhetsuppgifter ej lämnade; teknisk räckvidd'], 'kontaktberedskap': 'ofullständig' if verksamhet is not None and not verksamhet.get('kontaktvagar') else 'faktisk kontaktresa ej prövad', 'verksamhet': verksamhet['namn'] if verksamhet else None,
            'not': 'rapport över teknisk och innehållsmässig SEO-beredskap; inga rankningslöften; strukturerad data prövas mot verksamhetsuppgifterna och schema.org:s vokabulär (kontroller/data/schemaorg.json, CC BY-SA 3.0), inte mot Googles verktyg'}


def markdown(r):
    lines = ['# SEO-kontroll — %s, läge %s, %d sidor, %d fynd' % (r['bygge'], r['lage'], r['sidor'], r['fynd_totalt']), '', '## Sajt']
    lines += ['- %s: %s' % (x['typ'], x['text']) for x in r['sajt']] or ['- inga fynd']
    for p in r['per_sida']:
        lines += ['', '## %s — %s%s' % (p['sida'], p['title'] or '(ingen title)', ' [noindex]' if p['noindex'] else '')]
        lines += ['- %s: %s' % (x['typ'], x['text']) for x in p['fynd']] or ['- inga fynd']
        lines += ['- (information) %s: %s' % (x['typ'], x['text']) for x in p.get('info', [])]
    return '\n'.join(lines) + '\n\n' + r['not'] + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(prog='seo_kontroll', description=__doc__.split('\n\n')[0])
    p.add_argument('--bygge', required=True)
    p.add_argument('--lage', required=True, choices=('forhandsvisning', 'lansering'))
    p.add_argument('--verksamhet')
    p.add_argument('--doman')
    p.add_argument('--omdirigeringar')
    p.add_argument('--ut', required=True)
    p.add_argument('--md')
    a = p.parse_args(argv)
    krav_vag(a.ut, "--ut")
    krav_vag(getattr(a, "md", None), "--md")
    if not Path(a.bygge).is_dir():
        print(json.dumps({'fel': 'bygget är ingen katalog: ' + a.bygge}))
        return 2
    try:
        r = rapport(a.bygge, a.lage, a.verksamhet, a.doman, a.omdirigeringar)
    except vu.Vagrad as e:
        print(json.dumps({'fel': e.args[0]}, ensure_ascii=False))
        return 2
    Path(a.ut).write_text(json.dumps(r, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if a.md:
        Path(a.md).write_text(markdown(r), encoding='utf-8')
    print(json.dumps({'sidor': r['sidor'], 'fynd_totalt': r['fynd_totalt'], 'ut': a.ut}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
