#!/usr/bin/env python3
"""prospekt_poang.py — signaler ur mätningen av en främmande sajt och poäng 0–10 per kategori, utan modell.

signaler(diagnos, kalla, sondering) läser verktygens filer under underlag/<slug>/diagnos/ och underlag/<slug>/kalla/
och ger en platt ordbok där okänt är None. poang(signaler, vikter) tillämpar kunskap/prospekt-vikter.json: bas och
avdrag i ordning, första träffen per signal gäller, 0–10 per kategori, total = summa vikt × (10 − kategori) = "mest
att vinna". Reglerna står i viktfilen; koden utvärderar bara jämförelser.

    .venv/bin/python kontroller/prospekt_poang.py underlag/<slug>            # skriv ut signaler och poäng

Exit 0. Ingen nätåtkomst: läser filer.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIKTER = ROOT / 'kunskap' / 'prospekt-vikter.json'
KATEGORIER = ('hastighet', 'seo', 'mobil', 'design')
KARUSELL = re.compile(r'\b(slick|swiper|owl-carousel|revslider|rev_slider|carousel|slider|flexslider|slideshow)\b', re.I)
BYGGVERKTYG = re.compile(r'(wix\.com|weebly|webnode|hemsida24|one\.com|simplesite|jimdo|site123|wordpress\.com|squarespace|webflow|godaddy|strikingly|yola)', re.I)
VALKOMMEN = re.compile(r'^\s*(välkommen|valkommen|welcome)\b', re.I)
GENERISK_TITEL = re.compile(r'^\s*(hem|home|start|startsida|välkommen|welcome|index)\b[\s|–-]*$', re.I)
ORGNR = re.compile(r'\b(\d{6})[-\s]?(\d{4})\b')
COPYRIGHT = re.compile(r'(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})', re.I)
LOREM = re.compile(r'lorem ipsum', re.I)
LOKALA_TYPER = ('LocalBusiness', 'Electrician', 'Plumber', 'HousePainter', 'RoofingContractor', 'GeneralContractor', 'HomeAndConstructionBusiness',
                'Locksmith', 'MovingCompany', 'HairSalon', 'BeautySalon', 'Dentist', 'Restaurant', 'Store', 'AutoRepair', 'Organization')
MILJO_META = re.compile(r'<meta\s+[^>]*>', re.I)
ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*["\']([^"\']*)["\']')

# Registret över signaler: namn → var den kommer ifrån. rokprov kontrollerar att varje signal i viktfilen finns här.
SIGNALER = {
    'prestanda': 'lighthouse mobil /', 'tillganglighet': 'lighthouse mobil /', 'lh_seo': 'lighthouse mobil /',
    'lcpMs': 'lighthouse', 'tbtMs': 'lighthouse', 'cls': 'lighthouse', 'vikt_byte': 'lighthouse total-byte-weight',
    'js_byte': 'lighthouse network-requests', 'css_byte': 'lighthouse network-requests', 'bild_storsta_byte': 'lighthouse network-requests',
    'renderingsblockerande': 'lighthouse render-blocking-insight', 'target_size': 'lighthouse target-size', 'viewport_meta': 'lighthouse meta-viewport / html',
    'zoom_sparrad': 'html viewport-meta', 'kontrast': 'lighthouse color-contrast / axe', 'soft_404': 'axe /finns-inte-nwp',
    'axe_allvarliga': 'axe', 'spill_390': 'inspektion 390', 'spill_320': 'inspektion reflow 320', 'h1_i_forsta_vyn': 'inspektion 390',
    'h1_antal': 'inspektion 390 / html', 'konsolfel': 'inspektion', 'natverksfel': 'inspektion',
    'sma_ytor': 'stil 390', 'sidhuvud_px': 'stil 390', 'foto_saknas_forsta': 'stil 390', 'radlangd_390': 'stil 390', 'centrerad': 'stil',
    'typsnitt_familjer': 'stil', 'hamburgare': 'stil 390',
    'title_saknas': 'html', 'title_langd': 'html', 'title_generisk': 'html', 'description_saknas': 'html', 'description_langd': 'html',
    'lang_saknas': 'html', 'canonical_saknas': 'html', 'noindex_start': 'html', 'robots_nekar_allt': 'hamta_sajt robots',
    'sidkarta_saknas': 'hamta_sajt sidkarta', 'lokal_schema_saknas': 'html json-ld', 'titlar_dubbla': 'hamta_sajt sidor',
    'orgnr_pa_sajt': 'html', 'tel_lank_start': 'html', 'karusell': 'html', 'valkommen_rubrik': 'html', 'copyright_ar': 'html',
    'copyright_gammal': 'html', 'byggverktyg_enkelt': 'html generator / lighthouse stackPacks', 'wordpress_gammal': 'html generator',
    'lorem_ipsum': 'html', 'generator': 'html', 'stackpack': 'lighthouse', 'jquery_version': 'lighthouse js-libraries',
    'https': 'sondering', 'http_till_https': 'sondering', 'hsts': 'sondering', 'cert_fel': 'sondering', 'server': 'sondering',
    'last_modified': 'sondering', 'bilder_antal': 'hamta_sajt', 'formular_antal': 'html', 'cookie_banner': 'html',
    'sidor_hamtade': 'hamta_sajt', 'sprak': 'html lang', 'tredjeparter': 'lighthouse third-parties-insight',
}


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def attrs(tag):
    return {k.lower(): v for k, v in ATTR.findall(tag)}


def ar(v):
    """Heltal av ett årtal eller None."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def startsida_html(kalla):
    """Startsidans sparade HTML ur hamta_sajt (start.html), annars första .html-filen."""
    kalla = Path(kalla)
    for namn in ('start.html', 'index.html'):
        f = kalla / namn
        if f.is_file():
            return f.read_text(encoding='utf-8', errors='replace')
    for f in sorted(kalla.glob('*.html')):
        return f.read_text(encoding='utf-8', errors='replace')
    return None


def html_signaler(raw, kalla):
    s = {}
    if raw is None:
        return s
    low = raw.lower()
    m = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I)
    title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
    s['title_saknas'] = not title
    s['title_langd'] = len(title) if title else None
    s['title_generisk'] = bool(title) and bool(GENERISK_TITEL.match(title))
    metas = [attrs(t) for t in MILJO_META.findall(raw)]
    desc = next((mm.get('content') for mm in metas if (mm.get('name') or '').lower() == 'description'), None)
    s['description_saknas'] = desc is None or not desc.strip()
    s['description_langd'] = len(desc.strip()) if desc else None
    robots = next((mm.get('content', '').lower() for mm in metas if (mm.get('name') or '').lower() == 'robots'), '')
    s['noindex_start'] = 'noindex' in robots
    viewport = next((mm.get('content', '') for mm in metas if (mm.get('name') or '').lower() == 'viewport'), None)
    s['viewport_meta'] = viewport is not None
    s['zoom_sparrad'] = bool(viewport) and bool(re.search(r'user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b', viewport, re.I))
    gen = next((mm.get('content', '') for mm in metas if (mm.get('name') or '').lower() == 'generator'), None)
    s['generator'] = gen or None
    lang = re.search(r'<html[^>]*\slang\s*=\s*["\']?([a-zA-Z-]+)', raw, re.I)
    s['lang_saknas'] = lang is None
    s['sprak'] = lang.group(1).lower() if lang else None
    s['canonical_saknas'] = not re.search(r'<link[^>]+rel\s*=\s*["\']canonical["\']', raw, re.I)
    s['h1_antal_html'] = len(re.findall(r'<h1\b', raw, re.I))
    s['orgnr_pa_sajt'] = bool(ORGNR.search(raw))
    s['tel_lank_start'] = 'href="tel:' in low or "href='tel:" in low
    s['karusell'] = bool(KARUSELL.search(raw))
    h1 = re.search(r'<h1\b[^>]*>(.*?)</h1>', raw, re.S | re.I)
    h1text = re.sub(r'<[^>]+>', '', h1.group(1)) if h1 else ''
    s['valkommen_rubrik'] = bool(VALKOMMEN.match(h1text)) or bool(title and VALKOMMEN.match(title))
    cy = [ar(x) for x in COPYRIGHT.findall(raw)]
    cy = [x for x in cy if x and 1990 <= x <= 2100]
    s['copyright_ar'] = max(cy) if cy else None
    s['lorem_ipsum'] = bool(LOREM.search(raw))
    s['formular_antal'] = len(re.findall(r'<form\b', raw, re.I))
    s['cookie_banner'] = bool(re.search(r'(cookie|kakor|cookiebot|onetrust|cookieconsent)', low))
    jsonld = ' '.join(re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', raw, re.S | re.I))
    s['lokal_schema_saknas'] = not any(t in jsonld for t in LOKALA_TYPER)
    verktyg = BYGGVERKTYG.search(gen or '') or BYGGVERKTYG.search(low[:200000])
    s['byggverktyg_enkelt'] = bool(verktyg)
    wp = re.search(r'wordpress\s+(\d+)(?:\.(\d+))?', gen or '', re.I)
    s['wordpress_gammal'] = bool(wp) and int(wp.group(1)) < 6
    return s


def lighthouse_signaler(diagnos):
    s = {}
    lh = las_json(Path(diagnos) / 'lighthouse' / 'lighthouse.json')
    if not lh or not lh.get('rader'):
        return s
    mob = [r for r in lh['rader'] if r.get('form') == 'mobil'] or lh['rader']
    start = next((r for r in mob if r.get('sida') == '/'), mob[0])
    s['prestanda'] = start.get('prestanda')
    s['tillganglighet'] = start.get('tillganglighet')
    s['lh_seo'] = start.get('seo')
    s['lcpMs'] = start.get('lcpMs')
    s['tbtMs'] = start.get('tbtMs')
    s['cls'] = start.get('cls')
    s['vikt_byte'] = start.get('viktByte')
    s['matning_osaker'] = bool(start.get('belastning') and start['belastning'] > 4)
    full = las_json(Path(diagnos) / 'lighthouse' / 'hem-mobil.json')
    a = (full or {}).get('audits') or {}

    def poang(id_):
        x = a.get(id_) or {}
        return x.get('score') if x.get('scoreDisplayMode') not in ('notApplicable', 'manual', 'informative', 'error') else None

    if a:
        if s.get('vikt_byte') is None:
            s['vikt_byte'] = (a.get('total-byte-weight') or {}).get('numericValue')
        poster = ((a.get('network-requests') or {}).get('details') or {}).get('items') or []
        js = sum(int(p.get('transferSize') or 0) for p in poster if p.get('resourceType') == 'Script')
        css = sum(int(p.get('transferSize') or 0) for p in poster if p.get('resourceType') == 'Stylesheet')
        bilder = [int(p.get('transferSize') or 0) for p in poster if p.get('resourceType') == 'Image']
        s['js_byte'] = js if poster else None
        s['css_byte'] = css if poster else None
        s['bild_storsta_byte'] = max(bilder) if bilder else (0 if poster else None)
        rb = poang('render-blocking-insight')
        s['renderingsblockerande'] = (rb is not None and rb < 1) if rb is not None else None
        ts = poang('target-size')
        s['target_size'] = (ts >= 1) if ts is not None else None
        mv = poang('meta-viewport')
        if mv is not None and 'viewport_meta' not in s:
            s['viewport_meta'] = mv >= 1
        kk = poang('color-contrast')
        s['kontrast'] = (kk is not None and kk < 1) if kk is not None else None
        bib = ((a.get('js-libraries') or {}).get('details') or {}).get('items') or []
        jq = next((b.get('version') for b in bib if (b.get('name') or '').lower() == 'jquery'), None)
        s['jquery_version'] = jq
        tp = ((a.get('third-parties-insight') or {}).get('details') or {}).get('items') or []
        s['tredjeparter'] = len(tp) if tp else 0
    pack = [p.get('id') for p in (full or {}).get('stackPacks') or []]
    s['stackpack'] = pack[0] if pack else None
    return s


def axe_signaler(diagnos):
    s = {}
    ax = las_json(Path(diagnos) / 'axe' / 'axe.json')
    if not ax:
        return s
    s['axe_allvarliga'] = ax.get('allvarliga')
    rader = ax.get('rader') or []
    if s.get('kontrast') is None:
        s['kontrast'] = any(v.get('id') == 'color-contrast' for r in rader for v in r.get('overtradelser') or []) or None
    saknas = [r for r in rader if r.get('sida') == '/finns-inte-nwp' and r.get('http') is not None]
    s['soft_404'] = (saknas[0]['http'] == 200) if saknas else None
    return s


def inspektion_signaler(diagnos):
    s = {}
    ins = las_json(Path(diagnos) / 'inspektion' / 'INSPEKTION.json')
    if not ins:
        return s
    v = (ins.get('vyer') or {}).get('390') or {}
    if v:
        s['spill_390'] = (v.get('spill') or {}).get('spill')
        s['spill_320'] = ((v.get('tillstand') or {}).get('reflow_320') or {}).get('spill')
        s['h1_i_forsta_vyn'] = v.get('h1_i_forsta_vyn')
        s['h1_antal'] = v.get('h1')
        s['konsolfel'] = sum(1 for k in v.get('konsol') or [] if k.get('typ') == 'error')
        s['natverksfel'] = len((v.get('natverk') or {}).get('fel') or [])
    return s


def stil_signaler(diagnos):
    s = {}
    st = las_json(Path(diagnos) / 'stil' / 'STIL.json')
    if not st:
        return s
    rader = st.get('rader') or []
    r390 = next((r for r in rader if r.get('vy') == '390' and r.get('sida') == '/'), None) or next((r for r in rader if r.get('vy') == '390'), None)
    if r390:
        s['sma_ytor'] = len(r390.get('smaYtor') or [])
        mob = r390.get('mobil') or {}
        s['sidhuvud_px'] = mob.get('sidhuvud')
        s['hamburgare'] = mob.get('hamburgare')
        s['foto_saknas_forsta'] = bool(mob.get('bilder')) and not mob.get('fotoIForsta') if mob else None
        s['radlangd_390'] = (r390.get('monster') or {}).get('radlangd')
    if rader:
        c = [(r.get('monster') or {}).get('centrerad') for r in rader if (r.get('monster') or {}).get('centrerad') is not None]
        s['centrerad'] = max(c) if c else None
    fam = (st.get('sammanfattning') or {}).get('typsnitt')
    s['typsnitt_familjer'] = len(fam) if fam is not None else None
    return s


def hamta_signaler(kalla, hamtning):
    """hamtning = det hamta_sajt returnerade (sparas i PROSPEKT.json av prospekt.py), kalla = katalogen."""
    s = {}
    h = hamtning or {}
    s['sidor_hamtade'] = h.get('sidor')
    s['bilder_antal'] = h.get('bilder')
    s['sidkarta_saknas'] = (not h.get('sidkarta')) if 'sidkarta' in h else None
    rob = h.get('robots')
    s['robots_nekar_allt'] = ('nekar allt' in str(rob).lower()) if rob else None
    titlar = [x.get('titel') for x in (h.get('sidlista') or []) if x.get('titel')]
    md = Path(kalla) / 'SIDOR.md'
    if not titlar and md.is_file():
        titlar = [r.split('|')[5].strip() for r in md.read_text(encoding='utf-8').splitlines() if r.startswith('| ') and r.count('|') >= 6 and not r.startswith('| Fil')]
    s['titlar_dubbla'] = (len(titlar) != len(set(titlar))) if len(titlar) >= 2 else None
    return s


def signaler(diagnos, kalla, sondering=None, hamtning=None):
    """Alla signaler i en platt ordbok; okänt är None (okänt förblir okänt, hittas aldrig på)."""
    s = {}
    s.update(sondering or {})
    s.update(hamta_signaler(kalla, hamtning))
    s.update(html_signaler(startsida_html(kalla), kalla))
    s.update(lighthouse_signaler(diagnos))
    s.update(axe_signaler(diagnos))
    s.update(inspektion_signaler(diagnos))
    s.update(stil_signaler(diagnos))
    if s.get('h1_antal') is None:
        s['h1_antal'] = s.get('h1_antal_html')
    s.pop('h1_antal_html', None)
    import datetime
    ar_nu = datetime.date.today().year
    s['copyright_gammal'] = (s['copyright_ar'] <= ar_nu - 2) if s.get('copyright_ar') else None
    return s


def traffar(rad, varde):
    if varde is None:
        return False
    for op in ('over', 'under', 'minst', 'lika', 'skiljer'):
        if op in rad:
            t = rad[op]
            try:
                if op == 'over':
                    return varde > t
                if op == 'under':
                    return varde < t
                if op == 'minst':
                    return varde >= t
                if op == 'lika':
                    return varde == t
                if op == 'skiljer':
                    return varde != t
            except TypeError:
                return False
    return False


def kategori(namn, regel, sig):
    """(poäng 0–10 eller None, varför-rader)."""
    bas = regel.get('bas')
    varfor = []
    if isinstance(bas, dict):
        v = sig.get(bas.get('signal'))
        if v is None:
            return None, varfor
        p = float(v) / float(bas.get('dela') or 1)
        varfor.append({'kategori': namn, 'signal': bas['signal'], 'varde': v, 'poang': round(p, 2), 'varfor': 'utgångspunkt: %s %s' % (bas['signal'], v)})
    else:
        # en kategori utan en enda känd signal är okänd, inte felfri (okänt förblir okänt)
        if not any(sig.get(r.get('signal')) is not None for r in regel.get('avdrag') or []):
            return None, varfor
        p = float(bas if bas is not None else 10)
    traffade = set()
    for rad in regel.get('avdrag') or []:
        sg = rad.get('signal')
        if sg in traffade:
            continue
        v = sig.get(sg)
        if traffar(rad, v):
            traffade.add(sg)
            p += float(rad.get('poang') or 0)
            varfor.append({'kategori': namn, 'signal': sg, 'varde': v, 'poang': rad.get('poang'), 'varfor': rad.get('varfor') or sg})
    return round(max(0.0, min(10.0, p)), 1), varfor


def poang(sig, vikter=None):
    v = vikter or las_json(VIKTER) or {}
    ut, varfor = {}, []
    for k in KATEGORIER:
        regel = (v.get('kategorier') or {}).get(k) or {'bas': 10, 'avdrag': []}
        ut[k], rader = kategori(k, regel, sig)
        varfor += rader
    w = v.get('vikter') or {k: 0.25 for k in KATEGORIER}
    kanda = {k: ut[k] for k in KATEGORIER if ut[k] is not None}
    if kanda:
        summa_w = sum(float(w.get(k, 0)) for k in kanda) or 1.0
        total = sum(float(w.get(k, 0)) / summa_w * (10 - kanda[k]) for k in kanda)
        ut['total'] = round(total, 1)
    else:
        ut['total'] = None
    ut['version'] = v.get('version')
    ut['osaker'] = len(kanda) < len(KATEGORIER) or bool(sig.get('matning_osaker'))
    sv = v.get('svag') or {}
    ut['svag'] = bool(ut['total'] is not None and (ut['total'] >= float(sv.get('total_minst', 5)) or any(x <= float(sv.get('kategori_hogst', 3)) for x in kanda.values())))
    return {'poang': ut, 'varfor': varfor}


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('katalog', help='underlag/<slug>')
    a = p.parse_args(argv)
    bas = Path(a.katalog)
    pr = las_json(bas / 'PROSPEKT.json') or {}
    sig = signaler(bas / 'diagnos', bas / 'kalla', pr.get('sondering'), pr.get('hamtning'))
    print(json.dumps({'signaler': sig, **poang(sig)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
