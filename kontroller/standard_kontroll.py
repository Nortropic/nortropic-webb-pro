#!/usr/bin/env python3
"""standard_kontroll.py — byggstandardens maskinkontrollerbara D-punkter (kunskap/byggstandard.md) prövade på den
byggda sajten. Läser bara dist/; kör ingenting.

    .venv/bin/python kontroller/standard_kontroll.py --bygge kunder/<slug>/sajt/dist --ut STANDARD.json [--md STANDARD.md]

Två nivåer. **fel** är entydiga avsteg som alltid går att rätta (provets grind `standard` blir röd). **info** är
sådant som kräver omdöme eller kan vara rätt i sammanhanget (rapporteras, stoppar inte). Det som redan prövas av
seo_kontroll (title- och descriptionlängd uppåt, en h1, lang finns, canonical, alt) och axe (kontrast, träffytor,
etiketter) upprepas inte här.
Exit 0 = rapporten skriven; 2 = fel i anropet.
"""
import argparse
import json
import re
import shutil
import struct
import subprocess
import tempfile
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

TOM = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
LOKALA_TYPER = {
    'LocalBusiness', 'HomeAndConstructionBusiness', 'ProfessionalService', 'Electrician', 'GeneralContractor',
    'HVACBusiness', 'HousePainter', 'Locksmith', 'MovingCompany', 'Plumber', 'RoofingContractor', 'AutomotiveBusiness',
    'AutoRepair', 'BeautySalon', 'HairSalon', 'HealthAndBeautyBusiness', 'FoodEstablishment', 'Restaurant', 'Store',
    'LegalService', 'AccountingService', 'MedicalBusiness', 'Dentist', 'CleaningService', 'ChildCare', 'SportsActivityLocation'}
ALLMANNA_TYPER = {'LocalBusiness', 'HomeAndConstructionBusiness', 'ProfessionalService'}
RASTER = ('.jpg', '.jpeg', '.png', '.gif')
GENERISKA_LANKTEXTER = {'läs mer', 'klicka här', 'här', 'mer', 'länk', 'läs mer här', 'se mer', 'read more', 'click here'}
SIPS = shutil.which('sips')
KIB = 1024


class Sida(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.el = []          # (tag, attrs, i_header, i_main)
        self.rubriker = []
        self.jsonld, self.inline_js, self.inline_css = [], [], []
        self.lanktexter = []  # (href, text, aria-label)
        self.ids = set()
        self._djup = {'header': 0, 'main': 0}
        self._fangar, self._buf, self._a = None, '', None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if a.get('id'):
            self.ids.add(a['id'])
        self.el.append((tag, a, self._djup['header'] > 0, self._djup['main'] > 0))
        if tag in self._djup:
            self._djup[tag] += 1
        if re.fullmatch(r'h[1-6]', tag):
            self.rubriker.append(int(tag[1]))
        if tag == 'script' and 'src' not in a:
            self._fangar, self._buf = ('ld' if a.get('type') == 'application/ld+json' else 'js'), ''
        elif tag == 'style':
            self._fangar, self._buf = 'css', ''
        elif tag == 'a':
            self._a = [a.get('href', ''), '', a.get('aria-label', ''), []]

    def handle_endtag(self, tag):
        if tag in self._djup and self._djup[tag] > 0:
            self._djup[tag] -= 1
        if tag in ('script', 'style') and self._fangar:
            {'ld': self.jsonld, 'js': self.inline_js, 'css': self.inline_css}[self._fangar].append(self._buf)
            self._fangar = None
        if tag == 'a' and self._a:
            delar = self._a[3]
            ihop = any(x[-1:].isalnum() and y[:1].isalnum() for x, y in zip(delar, delar[1:]))
            self.lanktexter.append((self._a[0], ' '.join(self._a[1].split()), self._a[2], ihop, ''.join(delar).strip()))
            self._a = None

    def handle_data(self, data):
        if self._fangar:
            self._buf += data
        if self._a:
            self._a[1] += data
            if data.strip():
                self._a[3].append(data)


def matt(fil):
    """(bredd, höjd) för en bildfil: sips om det finns, annars PNG-huvudet."""
    if SIPS:
        p = subprocess.run([SIPS, '-g', 'pixelWidth', '-g', 'pixelHeight', str(fil)], capture_output=True, text=True)
        m = dict(re.findall(r'pixel(Width|Height):\s*(\d+)', p.stdout))
        if len(m) == 2:
            return int(m['Width']), int(m['Height'])
    b = fil.read_bytes()[:24]
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', b[16:24])
    return None


def lokal(dist, url):
    """Filen i dist/ som en adress pekar på, eller None för extern adress. Absoluta adresser till sajtens egen
    domän (canonical, og:image) mappas på sökvägen."""
    if not url or url.startswith(('data:', 'tel:', 'mailto:', '#')):
        return None
    u = urlparse(url)
    vag = u.path.lstrip('/')
    f = dist / vag
    if f.is_dir():
        f = f / 'index.html'
    return f


def extern(url):
    return bool(url) and (url.startswith('//') or re.match(r'^https?://', url) is not None)


def srcset_adresser(v):
    return [d.strip().split(' ')[0] for d in (v or '').split(',') if d.strip()]


def typer(ld):
    ut = []
    for d in (ld if isinstance(ld, list) else [ld]):
        if isinstance(d, dict):
            if '@graph' in d:
                ut += typer(d['@graph'])
            t = d.get('@type')
            ut += (t if isinstance(t, list) else [t]) if t else []
    return ut


def granska(dist):
    dist = Path(dist)
    fel, info = [], []

    def F(punkt, sida, text):
        fel.append({'punkt': punkt, 'sida': sida, 'text': text})

    def I(punkt, sida, text):
        info.append({'punkt': punkt, 'sida': sida, 'text': text})

    sidor = sorted(dist.rglob('*.html'))
    if not sidor:
        F('1.1', '-', 'inga HTML-sidor i bygget')
        return fel, info, 0
    css_filer = {f: f.read_text(encoding='utf-8', errors='replace') for f in dist.rglob('*.css')}
    all_css = '\n'.join(css_filer.values())
    sidobjekt = {}
    for f in sidor:
        p = Sida()
        p.feed(f.read_text(encoding='utf-8', errors='replace'))
        sidobjekt[f] = p
        all_css += '\n' + '\n'.join(p.inline_css)

    for f, p in sidobjekt.items():
        rel = f.relative_to(dist)
        if rel.name == 'index.html':
            sida = '/' if rel.parent == Path('.') else '/%s/' % rel.parent.as_posix()
        else:
            sida = '/' + rel.as_posix()
        taggar = [t for t, *_ in p.el]
        attr = lambda tag: [a for t, a, *_ in p.el if t == tag]  # noqa: E731

        # 2.1 landmärken och rubriknivåer
        saknas = [x for x in ('header', 'nav', 'main', 'footer') if x not in taggar]
        if saknas:
            F('2.1', sida, 'landmärken saknas: ' + ', '.join(saknas))
        hopp = [(a, b) for a, b in zip(p.rubriker, p.rubriker[1:]) if b - a > 1]
        if hopp:
            F('2.1', sida, 'rubriknivå hoppar: ' + ', '.join('h%d→h%d' % h for h in hopp[:4]))
        # 2.2 klickhändelser i koden
        inline = sorted({k for t, a, *_ in p.el for k in a if k.startswith('on')})
        if inline:
            F('2.2', sida, 'inline-händelser (%s); använd <button> eller <a href> och skript utan inline-attribut' % ', '.join(inline[:4]))
        # 2.3 grundtaggar
        html = (attr('html') or [{}])[0]
        if not html.get('lang', '').lower().startswith('sv'):
            F('2.3', sida, 'html lang är inte sv (%r)' % html.get('lang', ''))
        metas, links = attr('meta'), attr('link')
        if not any(m.get('name') == 'viewport' for m in metas):
            F('2.3', sida, 'meta viewport saknas')
        if not any(m.get('name') == 'theme-color' and m.get('content') for m in metas):
            F('2.3', sida, 'meta theme-color saknas')
        rels = [(l.get('rel', '').lower().split(), l) for l in links]
        ikon = [l for r, l in rels if 'icon' in r and (l.get('type') == 'image/svg+xml' or l.get('href', '').endswith('.svg'))]
        if not ikon:
            F('2.3', sida, 'favicon som SVG saknas (<link rel="icon" type="image/svg+xml" href="/favicon.svg">)')
        elif not (lokal(dist, ikon[0].get('href')) or Path('/saknas')).is_file():
            F('2.3', sida, 'favicon-filen finns inte: ' + ikon[0].get('href'))
        apple = [l for r, l in rels if 'apple-touch-icon' in r]
        if not apple:
            F('2.3', sida, 'apple-touch-icon saknas (180×180 px PNG)')
        else:
            af = lokal(dist, apple[0].get('href'))
            if not (af and af.is_file()):
                F('2.3', sida, 'apple-touch-icon-filen finns inte: ' + apple[0].get('href'))
            elif matt(af) != (180, 180):
                F('2.3', sida, 'apple-touch-icon är %s, ska vara 180×180 px' % ('×'.join(map(str, matt(af) or ('?',)))))
        # 2.4 bilder
        imgs = [(a, i_main) for t, a, _h, i_main in p.el if t == 'img']
        utan_matt = [a.get('src', '')[:60] for a, _ in imgs if not (a.get('width') and a.get('height'))]
        if utan_matt:
            F('2.4', sida, '%d bilder utan width och height, t.ex. %s' % (len(utan_matt), utan_matt[0]))
        i_main = [a for a, m in imgs if m]
        if i_main and i_main[0].get('loading') == 'lazy':
            I('2.4', sida, 'första bilden i main laddas lazy; ligger den i första vyn ska den laddas direkt')
        if sida == '/' and i_main and not any(a.get('fetchpriority') == 'high' for a, _ in imgs):
            I('2.4', sida, 'ingen bild har fetchpriority="high"; sätt den på den största bilden i första vyn')
        # 3.7 vikt
        js = sum(len(x.encode()) for x in p.inline_js)
        for s in attr('script'):
            lf = lokal(dist, s.get('src')) if s.get('src') else None
            js += lf.stat().st_size if lf and lf.is_file() else 0
        cs = sum(len(x.encode()) for x in p.inline_css)
        for r, l in rels:
            if 'stylesheet' in r:
                lf = lokal(dist, l.get('href'))
                cs += lf.stat().st_size if lf and lf.is_file() else 0
        if js > 200 * KIB:
            F('3.7', sida, 'JavaScript %d kB, högst 200 kB' % (js // KIB))
        if cs > 100 * KIB:
            F('3.7', sida, 'CSS %d kB, högst 100 kB' % (cs // KIB))
        # 4.2 bildformat och storlek
        raster = []
        for t, a, *_ in p.el:
            if t in ('img', 'source'):
                for u in [a.get('src', '')] + srcset_adresser(a.get('srcset')):
                    if urlparse(u).path.lower().endswith(RASTER):
                        raster.append(u)
        if raster:
            F('4.2', sida, '%d bilder i JPEG, PNG eller GIF; använd WebP eller AVIF (astro:assets), t.ex. %s' % (len(raster), raster[0][:60]))
        if sida == '/' and i_main:
            lf = lokal(dist, i_main[0].get('src'))
            if lf and lf.is_file() and lf.stat().st_size > 200 * KIB:
                I('4.2', sida, 'första bilden i main är %d kB; största bilden i första vyn ska vara under 200 kB' % (lf.stat().st_size // KIB))
        # 4.3 preload av typsnitt
        if sida == '/' and not any('preload' in r and l.get('as') == 'font' for r, l in rels):
            I('4.3', sida, 'inget typsnitt förladdas; preload det typsnitt som syns i första vyn')
        # 4.4 tredjepartsresurser
        ext = []
        for t, a, *_ in p.el:
            kandidater = []
            if t in ('script', 'iframe', 'img', 'source', 'video', 'audio', 'embed', 'track'):
                kandidater = [a.get('src', '')] + srcset_adresser(a.get('srcset'))
            elif t == 'object':
                kandidater = [a.get('data', '')]
            elif t == 'link' and set(a.get('rel', '').lower().split()) & {'stylesheet', 'preload', 'modulepreload', 'icon', 'apple-touch-icon', 'manifest', 'prefetch', 'preconnect', 'dns-prefetch'}:
                kandidater = [a.get('href', '')]
            ext += [u for u in kandidater if extern(u)]
        if ext:
            F('4.4', sida, '%d resurser från andra domäner laddas, t.ex. %s' % (len(ext), ext[0][:80]))
        if 'iframe' in taggar:
            I('4.4', sida, 'iframe på sidan; kartor och inbäddningar som statisk bild och länk')
        # 5.1 skiplänk först
        fokus = [(t, a) for t, a, *_ in p.el if (t == 'a' and a.get('href')) or t in ('button', 'input', 'select', 'textarea')
                 or (a.get('tabindex', '').lstrip('-').isdigit() and int(a['tabindex']) >= 0)]
        forsta = fokus[0] if fokus else None
        if not (forsta and forsta[0] == 'a' and forsta[1].get('href', '').startswith('#') and forsta[1]['href'][1:] in p.ids):
            F('5.1', sida, 'första fokuserbara elementet är ingen skiplänk till ett id på sidan')
        # 5.3 länktexter
        ihop = [x[4] for x in p.lanktexter if x[3] and not x[2]]
        if ihop:
            F('5.3', sida, 'länkens namn läses ihop utan mellanslag mellan elementen: %r; lägg mellanslag eller aria-label' % ihop[0][:50])
        generiska = [x[1] for x in p.lanktexter if x[1].lower() in GENERISKA_LANKTEXTER and not x[2]]
        if generiska:
            I('5.3', sida, 'länktexter som inte säger något utan sammanhang: ' + ', '.join(sorted(set(generiska))[:4]))
        # 5.5 autoplay
        if any(t in ('video', 'audio') and 'autoplay' in a and (t == 'audio' or 'muted' not in a) for t, a, *_ in p.el):
            F('5.5', sida, 'video eller ljud spelas automatiskt med ljud')
        # 6.2 formulärfält
        for a in attr('input'):
            namn = (a.get('name', '') + a.get('id', '')).lower()
            if a.get('type', 'text') == 'text' and re.search(r'tel|phone', namn):
                I('6.2', sida, 'telefonfältet %r har inte type="tel"' % a.get('name'))
            if a.get('type', 'text') == 'text' and re.search(r'mail', namn):
                I('6.2', sida, 'e-postfältet %r har inte type="email"' % a.get('name'))
            if a.get('type', 'text') in ('text', 'tel', 'email') and not a.get('autocomplete'):
                I('6.2', sida, 'fältet %r saknar autocomplete' % (a.get('name') or a.get('id')))
        # 7.1 delningsbild, titel- och beskrivningslängd nedåt
        og = [m.get('content', '') for m in metas if m.get('property') == 'og:image']
        if not og:
            F('7.1', sida, 'og:image saknas (delningsbild 1200×630 px)')
        else:
            of = lokal(dist, og[0])
            if not (of and of.is_file()):
                F('7.1', sida, 'og:image pekar på en fil som inte finns i bygget: ' + og[0][:80])
            elif matt(of) != (1200, 630):
                F('7.1', sida, 'og:image är %s, ska vara 1200×630 px' % ('×'.join(map(str, matt(of) or ('?',)))))
        for egenskap in ('og:title', 'og:description'):
            if not any(m.get('property') == egenskap for m in metas):
                I('7.1', sida, egenskap + ' saknas')
        titel = re.search(r'<title[^>]*>(.*?)</title>', f.read_text(encoding='utf-8', errors='replace'), re.S | re.I)
        if titel and len(titel.group(1).strip()) < 50 and f.name != '404.html':
            I('7.1', sida, 'title %d tecken; 50–60 ger mer i sökresultatet' % len(titel.group(1).strip()))
        desc = next((m.get('content', '') for m in metas if m.get('name') == 'description'), '')
        if desc and len(desc) < 120 and f.name != '404.html':
            I('7.1', sida, 'description %d tecken; sikta på 120–155' % len(desc))
        # 7.3 strukturerad data
        alla_typer = []
        for blk in p.jsonld:
            try:
                alla_typer += typer(json.loads(blk))
            except ValueError:
                pass
        if sida == '/':
            lokala = [t for t in alla_typer if t in LOKALA_TYPER]
            if not lokala:
                F('7.3', sida, 'startsidan saknar JSON-LD för verksamheten (LocalBusiness eller en mer specifik typ)')
            elif all(t in ALLMANNA_TYPER for t in lokala):
                I('7.3', sida, 'JSON-LD-typen %s är allmän; använd den mest specifika (t.ex. GeneralContractor, Electrician, HousePainter, Plumber)' % lokala[0])
        if any('"aggregateRating"' in blk for blk in p.jsonld):
            I('7.3', sida, 'aggregateRating ur Google-omdömen ger inga rikresultat (Googles regel mot självbetjänade omdömen); ofarligt men onödigt')
        if 'FAQPage' in alla_typer:
            I('7.3', sida, 'FAQPage ger inga rikresultat i Google sedan 7 maj 2026; ofarligt men ger inget')
        # 8.2 CSP i demon
        csp = [m.get('content', '') for m in metas if m.get('http-equiv', '').lower() == 'content-security-policy']
        if not csp:
            F('8.2', sida, 'ingen CSP; slå på security.csp i astro.config.mjs (se mallen)')
        else:
            skript = re.search(r"script-src([^;]*)", csp[0])
            if not skript or "'unsafe-inline'" in skript.group(1):
                F('8.2', sida, "CSP:ns script-src saknas eller tillåter 'unsafe-inline'")
        # 9.2 telefon i sidhuvudet
        tel = [(a, i_h) for t, a, i_h, _m in p.el if t == 'a' and a.get('href', '').startswith('tel:')]
        if not tel:
            F('9.2', sida, 'ingen tel-länk på sidan')
        elif not any(i_h for _, i_h in tel):
            F('9.2', sida, 'telefonnumret finns inte som tel-länk i sidhuvudet')

    # sajtövergripande
    if re.search(r'@keyframes|scroll-behavior\s*:\s*smooth', all_css) and 'prefers-reduced-motion' not in all_css:
        F('3.5', '(alla)', 'sidan har rörelse (@keyframes eller mjuk skroll) men ingen @media (prefers-reduced-motion)')
    if ':focus-visible' not in all_css:
        I('3.4', '(alla)', 'ingen :focus-visible-stil; webbläsarens standardfokus syns men följer inte designen')
    for m in re.finditer(r'font-size\s*:\s*clamp\(([^,]+),([^,]+),', all_css):
        if 'vw' in m.group(2) and not re.search(r'r?em', m.group(2)):
            I('3.2', '(alla)', 'clamp() med bara vw i mitten (%s); blanda in rem så att texten växer med zoom' % m.group(2).strip()[:30])
            break
    if re.search(r'font-awesome|material-icons|icomoon|glyphicons', all_css, re.I):
        F('3.6', '(alla)', 'ikonfont används; använd SVG')
    if re.search(r'url\(\s*["\']?(https?:)?//', all_css):
        F('4.4', '(alla)', 'CSS hämtar resurser från en annan domän (t.ex. typsnitt); självhosta')
    fontfiler = [f for f in dist.rglob('*') if f.suffix.lower() in ('.woff', '.ttf', '.otf', '.eot')]
    if fontfiler:
        F('4.3', '(alla)', '%d typsnittsfiler som inte är WOFF2, t.ex. %s' % (len(fontfiler), fontfiler[0].name))
    familjer = set()
    for blk in re.findall(r'@font-face\s*{([^}]*)}', all_css):
        if 'url(' not in blk:
            continue  # reservtypsnitt med local() och size-adjust
        fam = re.search(r'font-family\s*:\s*([^;]+)', blk)
        if fam:
            familjer.add(fam.group(1).strip().strip('"\''))
        if 'font-display' not in blk:
            F('4.3', '(alla)', '@font-face för %s saknar font-display' % (fam.group(1).strip() if fam else '?'))
    if len(familjer) > 2:
        F('4.3', '(alla)', '%d typsnittsfamiljer (%s); högst två' % (len(familjer), ', '.join(sorted(familjer))))
    robots = dist / 'robots.txt'
    if not robots.is_file():
        F('7.2', '(alla)', 'robots.txt saknas')
    else:
        rt = robots.read_text(encoding='utf-8', errors='replace')
        if re.search(r'^\s*Disallow:\s*/(_astro|.*\.(css|js))', rt, re.M | re.I):
            F('7.2', '(alla)', 'robots.txt blockerar CSS eller JS')
        if re.search(r'User-agent:\s*\*\s*\n(?:[^\n]*\n)*?\s*Disallow:\s*/\s*$', rt, re.M | re.I):
            F('7.2', '(alla)', 'robots.txt blockerar hela sajten för alla')
    if not (dist / 'sitemap.xml').is_file():
        F('7.2', '(alla)', 'sitemap.xml saknas')
    f404 = dist / '404.html'
    if not f404.is_file():
        F('7.2', '(alla)', '404.html saknas')
    else:
        p404 = sidobjekt[f404]
        if not any(x[0] in ('/', '/index.html') for x in p404.lanktexter):
            F('7.2', '/404.html', '404-sidan saknar länk till startsidan')
        m404 = [a for t, a, *_ in p404.el if t == 'meta']
        if not any(m.get('name') == 'robots' and 'noindex' in m.get('content', '') for m in m404):
            F('7.2', '/404.html', '404-sidan saknar <meta name="robots" content="noindex">')
        if any('canonical' in a.get('rel', '').lower().split() for t, a, *_ in p404.el if t == 'link'):
            F('7.2', '/404.html', '404-sidan har canonical; ta bort den (404-sidan ska inte indexeras)')
    # 2.5 giltig HTML, lokalt (W3C:s tjänst skulle få verksamhetens sidor skickade till sig)
    for sida, text in giltig_html(dist):
        (F if sida else I)('2.5', sida or '(alla)', text)
    return fel, info, len(sidor)


def giltig_html(dist):
    """html-validate med standardreglerna (kontroller/htmlvalidate.json). Ger (sida, text); sida None = verktygsfel."""
    rot = Path(__file__).resolve().parent
    hv = rot / 'node_modules' / '.bin' / 'html-validate'
    if not hv.is_file():
        return [(None, 'html-validate saknas; kör npm install i kontroller/')]
    with tempfile.TemporaryDirectory() as tmp:
        ut = Path(tmp) / 'hv.json'
        subprocess.run([str(hv), '--config', str(rot / 'htmlvalidate.json'), '--formatter', 'json=%s' % ut, str(dist)],
                       capture_output=True, text=True, timeout=300)
        try:
            data = json.loads(ut.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return [(None, 'html-validate gav inget läsbart resultat')]
    fynd = []
    for f in data:
        rel = Path(f['filePath']).resolve().relative_to(Path(dist).resolve())
        sida = '/' if rel.as_posix() == 'index.html' else ('/%s/' % rel.parent.as_posix() if rel.name == 'index.html' else '/' + rel.as_posix())
        for m in f.get('messages', []):
            if m.get('severity') == 2:
                fynd.append((sida, 'ogiltig HTML rad %s: %s (%s)' % (m.get('line'), m.get('message', '')[:120], m.get('ruleId'))))
    return fynd


def klickytor(stil):
    """Byggstandarden 3.3 ur stilrapporten (stil.mjs mäter i webbläsaren i 390 px)."""
    try:
        data = json.loads(Path(stil).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    per_sida = {}
    for y in data.get('smaYtor', []):
        per_sida.setdefault(y['sida'], []).append(y)
    return [{'punkt': '3.3', 'sida': s, 'text': '%d klickytor under 24 px i 390, t.ex. "%s" %d×%d' % (len(ys), ys[0]['text'], ys[0]['bredd'], ys[0]['hojd'])}
            for s, ys in sorted(per_sida.items())]


def rapport(bygge, stil=None):
    fel, info, n = granska(bygge)
    if stil:
        fel += klickytor(stil)
    summa = {}
    for x in fel:
        summa[x['punkt']] = summa.get(x['punkt'], 0) + 1
    return {'schema': 1, 'bygge': str(bygge), 'sidor': n, 'fel': fel, 'info': info, 'fel_per_punkt': summa,
            'standard': 'kunskap/byggstandard.md',
            'not': 'fel = entydiga avsteg från D-punkterna; info = kräver omdöme. Övriga punkter prövas av seo, axe, lighthouse, spill, utan-js och granskaren.'}


def markdown(r):
    rad = ['# Byggstandarden · %d sidor · %d fel · %d info' % (r['sidor'], len(r['fel']), len(r['info'])), '',
           'Punkterna står i `kunskap/byggstandard.md`. Fel stoppar provet; info kräver omdöme.', '']
    for rubrik, lista in (('Fel', r['fel']), ('Info', r['info'])):
        rad += ['## ' + rubrik, '']
        rad += ['| Punkt | Sida | Fynd |', '|---|---|---|'] + ['| %s | %s | %s |' % (x['punkt'], x['sida'], x['text'].replace('|', '/')) for x in lista] if lista else ['Inga.']
        rad.append('')
    return '\n'.join(rad)


def main(argv=None):
    p = argparse.ArgumentParser(prog='standard_kontroll', description=__doc__.split('\n\n')[0])
    p.add_argument('--bygge', required=True)
    p.add_argument('--ut', required=True)
    p.add_argument('--md')
    p.add_argument('--stil', help='STIL.json från stil.mjs, för klickytorna (3.3)')
    a = p.parse_args(argv)
    if not Path(a.bygge).is_dir():
        print('finns inte: ' + a.bygge, file=sys.stderr)
        return 2
    r = rapport(Path(a.bygge), a.stil)
    Path(a.ut).write_text(json.dumps(r, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if a.md:
        Path(a.md).write_text(markdown(r), encoding='utf-8')
    print(json.dumps({'sidor': r['sidor'], 'fel': len(r['fel']), 'info': len(r['info']), 'fel_per_punkt': r['fel_per_punkt']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
