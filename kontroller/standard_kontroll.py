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
import html
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import sys
from html import unescape as avkoda_html
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

TOM = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
LOKALA_TYPER_RESERV = {
    'LocalBusiness', 'HomeAndConstructionBusiness', 'ProfessionalService', 'Electrician', 'GeneralContractor',
    'HVACBusiness', 'HousePainter', 'Locksmith', 'MovingCompany', 'Plumber', 'RoofingContractor', 'AutomotiveBusiness',
    'AutoRepair', 'BeautySalon', 'HairSalon', 'HealthAndBeautyBusiness', 'FoodEstablishment', 'Restaurant', 'Store',
    'LegalService', 'AccountingService', 'MedicalBusiness', 'Dentist', 'CleaningService', 'ChildCare', 'SportsActivityLocation'}
ALLMANNA_TYPER = {'LocalBusiness', 'HomeAndConstructionBusiness', 'ProfessionalService'}


def _lokala_typer():
    """LocalBusiness och alla dess undertyper ur schema.org-hierarkin (kontroller/data/schemaorg.json), så att Bakery
    och CafeOrCoffeeShop räknas (revisionen 2026-10-03, F21); den handskrivna listan är reserv om filen saknas."""
    try:
        kl = json.loads((Path(__file__).resolve().parent / 'data' / 'schemaorg.json').read_text(encoding='utf-8'))['klasser']
    except (OSError, ValueError, KeyError, TypeError):
        return set(LOKALA_TYPER_RESERV)
    ut = set()
    for k in kl:
        stack, sedda = [k], set()
        while stack:
            x = stack.pop()
            if x not in sedda:
                sedda.add(x)
                stack.extend(kl.get(x, []))
        if 'LocalBusiness' in sedda:
            ut.add(k)
    return ut | set(LOKALA_TYPER_RESERV)


LOKALA_TYPER = _lokala_typer()
# CSP: skript bara med hash (byggstandarden 8.2); källor som släpper igenom annat gör direktivet verkningslöst
CSP_SKRIPT_OK = re.compile(r"^('self'|'none'|'strict-dynamic'|'sha(256|384|512)-[A-Za-z0-9+/=]+'|'nonce-[A-Za-z0-9+/=_-]+')$")
RASTER = ('.jpg', '.jpeg', '.png', '.gif')
GENERISKA_LANKTEXTER = {'läs mer', 'klicka här', 'här', 'mer', 'länk', 'läs mer här', 'se mer', 'read more', 'click here'}
SIPS = shutil.which('sips')
TYPSNITT_BUDGET_KB = 300  # sajtens självhostade typsnitt tillsammans (WOFF2); den verkliga prestandan prövar Lighthouse-grinden
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
        self.formular = []  # {'attr', 'falt', 'lankar'} per <form>
        self._form = None
        self._fangar, self._buf, self._a = None, '', None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if a.get('id'):
            self.ids.add(a['id'])
        self.el.append((tag, a, self._djup['header'] > 0, self._djup['main'] > 0))
        if tag == 'form':
            self._form = {'attr': a, 'falt': [], 'lankar': [], 'knappar': []}
            self.formular.append(self._form)
        elif self._form is not None:
            if tag in ('input', 'textarea', 'select'):
                self._form['falt'].append(dict(a, _tag=tag))
            elif tag == 'a':
                self._form['lankar'].append(a.get('href', ''))
            elif tag == 'button':
                self._form['knappar'].append(a)
            if a.get('id') == 'forfragan-saknas':
                self._form.setdefault('felbesked', []).append(a)
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
        if tag == 'form':
            self._form = None
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


def langd(v, vy=None):
    """En CSS-längd i px: px, rem och em (16 px), vw vid fönsterbredden vy, och calc(), min(), max() och clamp() av sådana.
    None när värdet inte går att tolka (granskningen av steg 2, punkt 4: byggena skriver sizes i rem och calc())."""
    s = (v or '').strip().lower()
    if not s:
        return None

    def px(m):
        if m.group(2) == 'vw' and vy is None:
            raise ValueError('vw utan fönsterbredd')
        return '%.4f' % (float(m.group(1)) * {'px': 1, 'rem': 16, 'em': 16, 'vw': (vy or 0) / 100, '': 1}[m.group(2)])
    try:
        uttryck = re.sub(r'(\d*\.?\d+)(px|rem|em|vw|)\b', px, s).replace('calc(', '(')
        rest = re.sub(r'\b(min|max|clamp)\(', '(', uttryck)
        if not re.fullmatch(r'[0-9.+\-*/(), ]+', rest) or '**' in rest:
            return None
        varde = eval(uttryck, {'__builtins__': {}}, {'min': min, 'max': max, 'clamp': lambda a, b, c: max(a, min(b, c))})  # noqa: S307 — bara tal, operatorer och tre funktioner
        return float(varde)
    except Exception:  # noqa: BLE001
        return None


def villkor_galler(villkor, vy):
    """Ett mediavillkor vid fönsterbredden vy: min-width, max-width och width med jämförelse (px, rem, em), flera med and.
    None när villkoret inte går att tolka."""
    for d in re.split(r'\s+and\s+', (villkor or '').strip().lower()):
        d = d.strip()
        if d in ('all', 'screen', 'only screen'):
            continue
        m = re.fullmatch(r'\(\s*(min|max)-width\s*:\s*([^()]+?)\s*\)', d) or re.fullmatch(r'\(\s*width\s*(>=|<=|>|<)\s*([^()]+?)\s*\)', d)
        x = langd(m.group(2)) if m else None
        if x is None:
            return None
        if not {'min': vy >= x, 'max': vy <= x, '>=': vy >= x, '<=': vy <= x, '>': vy > x, '<': vy < x}[m.group(1)]:
            return False
    return True


def delat(v):
    """Kommaseparerade delar utanför parenteser (calc(), min() och clamp() har egna kommatecken)."""
    delar, djup, start = [], 0, 0
    for i, c in enumerate(v or ''):
        djup += {'(': 1, ')': -1}.get(c, 0)
        if c == ',' and djup == 0:
            delar.append(v[start:i]); start = i + 1
    delar.append((v or '')[start:])
    return [d.strip() for d in delar if d.strip()]


def platsbredd(sizes, vy):
    """Bildens platsbredd i px vid fönsterbredden vy ur sizes, som webbläsaren läser den: första posten vars villkor gäller,
    annars 100vw. None när det första villkor som kan gälla, eller dess värde, inte går att tolka: då mäts inget, i
    stället för att en senare post (oftast 100vw) får tala för bilden."""
    for post in delat(sizes) or ['100vw']:
        if post.endswith(')'):  # värdet är en funktion (calc, min, max, clamp) eller saknas: leta upp dess öppning
            djup, i = 0, len(post)
            for i in range(len(post) - 1, -1, -1):
                djup += {')': 1, '(': -1}.get(post[i], 0)
                if djup == 0:
                    break
            fn = re.search(r'(calc|min|max|clamp)$', post[:i].lower())
            villkor, varde = (post[:fn.start()], post[fn.start():]) if fn else (post, None)
        else:
            villkor, varde = post[:post.rfind(' ') + 1], post[post.rfind(' ') + 1:]
        if villkor.strip():
            g = villkor_galler(villkor, vy)
            if g is None:
                return None
            if not g:
                continue
        return langd(varde, vy) if varde else None
    return float(vy)


def vald_kandidat(src, srcset, sizes, vy, dpr):
    """Bilden webbläsaren hämtar vid fönsterbredden vy och pixeltätheten dpr: med w-kandidater den minsta som räcker för
    platsbredden gånger dpr, annars den största; med x-kandidater (och src som 1x) den minsta täthet som räcker för dpr;
    utan srcset src (backlogposten om bildvikten i 4.2: Astros Image lägger originalet i src). None när sizes inte går att
    tolka."""
    w_, x_ = [], []
    for d in delat(srcset):
        delar = d.split()
        if len(delar) == 1:
            x_.append((1.0, delar[0]))
        elif len(delar) == 2 and re.fullmatch(r'\d+w', delar[1]):
            w_.append((int(delar[1][:-1]), delar[0]))
        elif len(delar) == 2 and re.fullmatch(r'\d*\.?\d+x', delar[1]):
            x_.append((float(delar[1][:-1]), delar[0]))
    if w_:
        bredd = platsbredd(sizes, vy)
        if bredd is None:
            return None
        w_.sort()
        return next((u for w, u in w_ if w >= bredd * dpr), w_[-1][1])
    if x_:
        if src and not any(x == 1.0 for x, _ in x_):
            x_.append((1.0, src))
        x_.sort()
        return next((u for x, u in x_ if x >= dpr), x_[-1][1])
    return src


BILDTYPER = ('image/avif', 'image/webp', 'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml')


def hamtad_bild(el, i, vy, dpr):
    """Bilden webbläsaren hämtar för <img> på plats i i sidans elementlista: står den i en <picture>, den första <source>
    vars media gäller och vars type stöds; annars bildens egna src, srcset och sizes. None när villkor eller sizes inte går
    att tolka."""
    kallor = []
    for t, a, *_ in reversed(el[:i]):
        if t == 'source':
            kallor.insert(0, a)
            continue
        if t != 'picture':
            kallor = []
        break
    for a in kallor:
        if a.get('type') and a['type'].split(';')[0].strip().lower() not in BILDTYPER:
            continue
        g = villkor_galler(a['media'], vy) if a.get('media') else True
        if g is None:
            return None
        if g:
            return vald_kandidat(None, a.get('srcset'), a.get('sizes'), vy, dpr)
    a = el[i][1]
    return vald_kandidat(a.get('src'), a.get('srcset'), a.get('sizes'), vy, dpr)


def typer(ld):
    """Alla @type i ett JSON-LD-block, också i @graph, utan schema.org-prefix (https://schema.org/Bakery räknas som
    Bakery; omgång fem, F20)."""
    ut = []
    for d in (ld if isinstance(ld, list) else [ld]):
        if isinstance(d, dict):
            if '@graph' in d:
                ut += typer(d['@graph'])
            t = d.get('@type')
            ut += [re.sub(r'^(https?://schema\.org/|schema:)', '', str(x)) for x in ((t if isinstance(t, list) else [t]) if t else [])]
    return ut


def kontaktmodell(brief):
    """Kundens kontaktvägar ur BRIEF.md §4 (Primär handling): {'telefon', 'skriftlig', 'bokning'} som sanningsvärden,
    eller None när briefen eller avsnittet saknas. Kontrollerna följer kundens kontaktmodell, inte en fast placering
    (Codex via ägaren 2026-10-05, punkt 2: en fungerande annan kontaktlösning får inte underkännas)."""
    try:
        text = Path(brief).read_text(encoding='utf-8') if brief else ''
    except (OSError, UnicodeDecodeError):
        return None
    m = re.search(r'^##\s*§\s*4\b[^\n]*\n(.*?)(?=^##\s|\Z)', text, re.M | re.S)
    if not m:
        return None
    s = m.group(1)
    return {'telefon': bool(re.search(r'\btel:|\b[Rr]ing\b|\bringa\b|telefon', s)),
            'skriftlig': bool(re.search(r'formulär|förfrågan|/api/forfragan|skriftlig|e-post|mejl', s, re.I)),
            'bokning': bool(re.search(r'\bbok(a|ning)', s, re.I))}


def designstruktur(dist):
    """DESIGN.md:s deklarerade informationsstruktur ({'brodsmulor': True/False}) ur json design-blocket bredvid bygget,
    eller {} när den inte är deklarerad. Brödsmulor är en designhypotes (kunskap/designregler.md): kontrollen kräver dem
    bara när designen säger att sajten har dem."""
    try:
        import design
        v, _f = design.las((Path(dist).parent / 'DESIGN.md').read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError):
        return {}
    s = (v or {}).get('struktur') if isinstance(v, dict) else None
    return s if isinstance(s, dict) else {}


def granska(dist, kontakt=None):
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
    # Astro lägger små stilmallar direkt i sidan; de räknas också
    all_css += '\n'.join(m for f in sidor for m in re.findall(r'<style[^>]*>(.*?)</style>', f.read_text(encoding='utf-8', errors='replace'), re.S))
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
            i0 = next(i for i, (t, _a, _h, m) in enumerate(p.el) if t == 'img' and m)
            for vy, dpr in ((390, 2), (1440, 1)):  # mobilen med tät skärm, datorn: den kandidat webbläsaren faktiskt hämtar
                u = hamtad_bild(p.el, i0, vy, dpr)
                if u is None:
                    I('4.2', sida, 'första bildens sizes eller media går inte att tolka i %d px; bildvikten i första vyn mättes inte där' % vy)
                    continue
                lf = lokal(dist, u)
                if lf and lf.is_file() and lf.stat().st_size > 200 * KIB:
                    I('4.2', sida, 'första bilden i main är %d kB i %d px (%s); största bilden i första vyn ska vara under 200 kB' % (
                        lf.stat().st_size // KIB, vy, urlparse(u).path.rsplit('/', 1)[-1][:60]))
                    break
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
            for namn, kallor in csp_skriptkallor(csp[0]).items():
                if kallor is None:
                    F('8.2', sida, 'CSP:ns %s saknas (och ingen script-src eller default-src att falla tillbaka på)' % namn)
                    continue
                otillatna = [k for k in kallor if not CSP_SKRIPT_OK.match(k)]
                if otillatna:
                    F('8.2', sida, "CSP:ns %s släpper igenom annat än 'self' och hashar: %s" % (namn, ' '.join(otillatna[:4])))
        # 9.2 nästa steg på varje indexerbar sida, med kundens kontaktvägar (BRIEF.md §4); var de står (sidhuvud, list,
        # sektion) är riktningens val, aldrig ett fel
        if sida not in ('/404.html',) and rel.name != '404.html' and not any(
                a.get('name') == 'robots' and 'noindex' in a.get('content', '') for t_, a, *_ in p.el if t_ == 'meta'):
            tel = [a for t, a, *_ in p.el if t == 'a' and a.get('href', '').startswith('tel:')]
            if kontakt and kontakt.get('telefon') and not tel:
                F('9.2', sida, 'kundens kontaktmodell (BRIEF.md §4) har telefonen, men sidan saknar tel-länk')
            nasta = tel or p.formular or [a for t, a, *_ in p.el if t == 'a' and re.match(
                r'^(mailto:|/kontakt/?(#|$)|/offert/?(#|$)|/boka/?(#|$))|#(forfragan|kontakt|skriv)', a.get('href', ''))]
            if not nasta:
                F('9.2', sida, 'sidan saknar ett nästa steg (tel-länk, formulär eller länk till kontaktvägen)')

    # sajtövergripande
    rorelse = re.search(r'@keyframes|scroll-behavior\s*:\s*smooth|(?<![\w-])(?:transition|animation)\s*:\s*(?!none\b)', all_css)
    if rorelse and 'prefers-reduced-motion' not in all_css:
        F('3.5', '(alla)', 'sidan har rörelse (%s) men ingen @media (prefers-reduced-motion); mallens Bas.astro har blocket'
          % rorelse.group(0).split(':')[0].strip())
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
    # 4.3 vikt: bedöms mot den valda designen och den verkliga prestandan (Lighthouse-grinden), inte mot fasta gränser per
    # fil ur en gammal jämförelse (Codex via ägaren 2026-10-05; ägarens A/B 2026-10-02, 47 mot 99 kB, är ett exempel).
    # Fel när sajtens typsnitt tillsammans går över budgeten; en tung fil är information med råd.
    bredd = re.search(r"font-stretch\s*:\s*(?!100%|normal)|'wdth'", all_css)
    woff2 = sorted(dist.rglob('*.woff2'))
    totalt = sum(f.stat().st_size for f in woff2) // 1024
    if totalt > TYPSNITT_BUDGET_KB:
        F('4.3', '(alla)', 'typsnitten väger %d kB tillsammans, över budgeten %d kB; ta latin-subset med bara de axlar och vikter som används' % (totalt, TYPSNITT_BUDGET_KB))
    for f in woff2:
        kb = f.stat().st_size // 1024
        if kb > 80:
            I('4.3', '(alla)', '%s är %d kB%s; latin-subset med bara de axlar som används brukar ge 40–50 kB per familj' % (
                f.name, kb, ' med bredd-axeln (behåll den om bredden bär formen)' if bredd else ''))
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
        # högst två är en designhypotes (kunskap/designregler.md): fler godtas när varje familj är en roll i sajtens
        # DESIGN.md, den aktuella (godkända) designen; annars är det ett avsteg
        deklarerade = set()
        try:  # bara en giltig DESIGN.md som är den ägaren godkänt (VINNARE.json, sha_design) avgör (granskningen M5)
            import design
            import skapande
            md_ = dist.parent / 'DESIGN.md'
            v_, _f = design.las(md_.read_text(encoding='utf-8'))
            g_ = ((skapande.las_json(skapande.UNDERLAG / dist.parent.parent.name / 'atelje' / 'VINNARE.json') or {}).get('godkand') or {})
            if v_ is not None and not design.validera(v_) and g_.get('sha_design') == skapande.sha256_fil(md_):
                deklarerade = {str(x.get('familj') or '').strip().lower() for x in (v_.get('typsnitt') or {}).values() if isinstance(x, dict)}
        except (OSError, UnicodeDecodeError, AttributeError):
            pass
        if deklarerade and {f.lower() for f in familjer} <= deklarerade:
            I('4.3', '(alla)', '%d typsnittsfamiljer (%s), alla roller i den godkända DESIGN.md' % (len(familjer), ', '.join(sorted(familjer))))
        else:
            F('4.3', '(alla)', '%d typsnittsfamiljer (%s); högst två, eller roller i den godkända DESIGN.md' % (len(familjer), ', '.join(sorted(familjer))))
    # 4.3 reserv: varje självhostat typsnitt följs i sin stack av ett reservtypsnitt med local() och size-adjust eller
    # ascent-override, så att texten inte hoppar när typsnittet laddats. Stacken kan stå i font-family eller i en
    # CSS-variabel (Astros typsnitts-API skriver '"Familj", "Familj fallback: Arial", sans-serif' i en variabel).
    namn = lambda s: s.strip().strip('"\'').strip().lower()  # noqa: E731
    reserver = {namn(m.group(1)) for blk in re.findall(r'@font-face\s*{([^}]*)}', all_css)
                if 'local(' in blk and re.search(r'size-adjust|ascent-override', blk)
                for m in [re.search(r'font-family\s*:\s*([^;]+)', blk)] if m}
    stackar = [[namn(x) for x in v.split(',')] for v in re.findall(r'(?:font-family|--[\w-]+)\s*:\s*([^;{}]+)', re.sub(r'@font-face\s*{[^}]*}', '', all_css)) if ',' in v]
    for fam in sorted(familjer):
        f = fam.lower()
        if not any(f in s and set(s[s.index(f) + 1:]) & reserver for s in stackar):
            F('4.3', '(alla)', 'typsnittet %s saknar reservtypsnitt med size-adjust i sin stack (@font-face med local() och size-adjust efter det); se mallens README' % fam)
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
    else:
        # en sida med noindex hör inte hemma i sitemap.xml (ägarens dom L4: /tack/ stod där)
        for loc in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', (dist / 'sitemap.xml').read_text(encoding='utf-8', errors='replace')):
            vag = urlparse(loc).path or '/'
            fil = dist / vag.lstrip('/') / 'index.html' if vag.endswith('/') else dist / vag.lstrip('/')
            sp = sidobjekt.get(fil)
            if sp and any(a.get('name') == 'robots' and 'noindex' in a.get('content', '') for t_, a, *_ in sp.el if t_ == 'meta'):
                F('7.2', vag, 'sidan har noindex men står i sitemap.xml; ta bort den ur sitemap (mallens sitemap.xml.ts hoppar över noindex)')
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
    # 4.2 GPS-läge i en publicerad bild är en personuppgift; astro:assets tar bort metadata, en fil i public/ gör det inte
    from bilddatum import BILDER, avif_metadata, exif, tiff_block
    for f in sorted(x for x in dist.rglob('*') if x.suffix.lower() in BILDER):
        try:
            data = f.read_bytes()
            if f.suffix.lower() == '.avif':  # alla publiceringsformat prövas; oläsbar metadata är inte grön (omgång elva, F33)
                lage, varde = avif_metadata(data)
                if lage == 'oklar':
                    F('4.2', '/' + f.relative_to(dist).as_posix(), 'bildens metadata kan inte verifieras (%s); lägg den i src/assets/ (astro:assets tar bort metadata) eller rensa den' % varde)
                    continue
                block = varde if lage == 'tiff' else None
            else:
                block = tiff_block(data)
            gps = exif(block).get('gps') if block else False
        except Exception:  # noqa: BLE001 — ett parserfel i deklarerad metadata är inte grönt (omgång tretton, F33)
            F('4.2', '/' + f.relative_to(dist).as_posix(), 'bildens metadata kan inte verifieras (parserfel i deklarerad metadata); lägg den i src/assets/ (astro:assets tar bort metadata) eller rensa den')
            continue
        if gps:
            F('4.2', '/' + f.relative_to(dist).as_posix(), 'bilden bär GPS-läge i sin metadata; lägg den i src/assets/ (astro:assets tar bort metadata) eller rensa den')
    # 9.4 mening som löper ihop med nästa utan mellanslag ("förfrågan.Så", L1: ").Läs"), också över inline-element
    for f in sidor:
        raw = re.sub(r'<(script|style|head)\b.*?</\1>', ' ', f.read_text(encoding='utf-8', errors='replace'), flags=re.S | re.I)
        # ord mot länk utan mellanslag: Astro klistrar ihop en länk på egen rad i källan med texten runt ("på<a", "</a>eller";
        # backlogposten om 9.4 och länkar efter radbrytning). Bara element som alltid står i löptext räknas bort; en span,
        # small, time eller data är ofta en egen post i flex eller grid. Hårt mellanslag är ett mellanslag, och en annan
        # entitet räknas som ett tecken utanför ordet (granskningen av steg 2, punkt 2).
        ihop = re.sub(r'</?(strong|em|b|i|abbr|mark|cite|q|sup|sub|bdi)\b[^>]*>', '', raw, flags=re.I)
        ihop = re.sub(r'&#?\w+;', '&', re.sub(r'&nbsp;|&#0*160;|&#x0*a0;|\xa0', ' ', ihop, flags=re.I))
        m2 = re.search(r'[A-Za-zÅÄÖåäöÉé0-9.,:;!?)\]](?=<a\b)|</a>(?=[A-Za-zÅÄÖåäöÉé0-9(])', ihop, flags=re.I)
        if m2:
            ren = lambda s: avkoda_html(re.sub(r'<[^>]+>', '', re.sub(r'^[^<]*>|<[^>]*$', '', s))).replace('\n', ' ')  # noqa: E731
            utdrag = ren(ihop[max(0, m2.end() - 300):m2.end()])[-30:] + ren(ihop[m2.end():m2.end() + 400])[:30]
            F('9.4', sida_av(dist, f), 'mellanslag saknas mellan text och länk: "%s"' % utdrag.strip())
        raw = re.sub(r'</?(a|span|strong|em|b|i|small|abbr|time|mark|cite|q|sup|sub|bdi|data)\b[^>]*>', '', raw, flags=re.I)
        text = avkoda_html(re.sub(r'<[^>]+>', '\n', raw))
        for m in re.finditer(r'[a-zåäöé)\]]\.[A-ZÅÄÖ][a-zåäö]', text):
            F('9.4', sida_av(dist, f), 'mellanslag saknas efter punkt: "%s"' % text[max(0, m.start() - 15):m.end() + 12].replace('\n', ' ').strip())
            break
    # 7.3 brödsmulor: en designhypotes (ägarens A/B-omdöme 2026-10-02, kunskap/designregler.md). Krävs bara när DESIGN.md:s
    # struktur säger att sajten har dem; strukturerade data ska alltid stämma med det synliga (Googles riktlinjer)
    struktur = designstruktur(dist)
    for f, p in sidobjekt.items():
        sida = sida_av(dist, f)
        if sida in ('/', '/404.html') or f.name == '404.html':
            continue
        if any(a.get('name') == 'robots' and 'noindex' in a.get('content', '') for t_, a, *_ in p.el if t_ == 'meta'):
            continue
        smulor = any(t_ == 'nav' and re.search(r'du är här|brödsmul|breadcrumb', a.get('aria-label', ''), re.I) for t_, a, *_ in p.el)
        lista = any('BreadcrumbList' in ld for ld in p.jsonld)
        if struktur.get('brodsmulor') is True:
            if not smulor:
                F('7.3', sida, 'DESIGN.md:s struktur har brödsmulor, men sidan saknar <nav aria-label="Du är här"> (mallens Brodsmulor.astro)')
            if not lista:
                F('7.3', sida, 'DESIGN.md:s struktur har brödsmulor, men BreadcrumbList saknas i JSON-LD (mallens Brodsmulor.astro)')
        elif lista and not smulor:
            F('7.3', sida, 'BreadcrumbList i JSON-LD utan synliga brödsmulor; strukturerade data ska stämma med det synliga')
        elif smulor and not lista:
            I('7.3', sida, 'synliga brödsmulor utan BreadcrumbList i JSON-LD (mallens Brodsmulor.astro har båda)')
        if smulor and any(t_ == 'nav' and i_main and re.search(r'du är här|brödsmul|breadcrumb', a.get('aria-label', ''), re.I)
                          for t_, a, _h, i_main in p.el):
            I('7.3', sida, 'brödsmulorna står inne i <main>; lägg dem mellan sidhuvudet och <main> (GOV.UK), så hamnar varken länkarna eller JSON-LD i huvudinnehållet (ägarens dom L4)')
    # 9.4 den kastbara sidan för tvåan-riktningen (bygg-sajt steg 5) tas bort efter skärmbilderna
    if (dist / 'tvaan').exists():
        F('9.4', '/tvaan/', 'den kastbara sidan med tvåan-riktningen finns kvar; ta bort kunder/<slug>/sajt/src/pages/tvaan med kontroller/ta_bort.py')
    for kvar in sorted(dist.glob('atelje-*')):
        F('9.4', '/%s/' % kvar.name, 'en kastbar ateljésida finns kvar; ta bort kunder/<slug>/sajt/src/pages/%s med kontroller/ta_bort.py' % kvar.name)
    # 6 skriftlig förfrågan (ägarens dom L1: "standarden ska inte tillåta att 'ring' är enda vägen")
    mal_ok = ('/api/forfragan/', '/api/forfragan')  # med snedstreck; utan svarar Vercel 308 och inskicket skickas två gånger
    forfragan = [(s, fm) for s, fm in ((sida_av(dist, f), fm) for f, p in sidobjekt.items() for fm in p.formular)
                 if fm['attr'].get('method', '').lower() == 'post' and fm['attr'].get('action') in mal_ok]
    if not forfragan:
        F('6.1', '(alla)', 'ingen skriftlig förfrågningsväg: formulär med method="post" och action="/api/forfragan/" saknas (mallens Forfragan.astro)')
    for sida, fm in forfragan:
        if fm['attr'].get('action') == '/api/forfragan':
            I('6.1', sida, 'formuläret postar till /api/forfragan utan snedstreck: på Vercel svarar sajten 308 och webbläsaren skickar inskicket, bilden inräknad, två gånger; använd /api/forfragan/')
    for sida, fm in forfragan:  # det effektiva målet: en skickaknapp med formaction/formmethod överstyr formuläret (omgång elva, F31)
        knappar = [k for k in fm.get('knappar', []) if (k.get('type') or 'submit').lower() == 'submit'] + \
                  [x for x in fm['falt'] if x.get('_tag') == 'input' and (x.get('type') or '').lower() == 'submit']
        for k in knappar:
            if (k.get('formaction') and k['formaction'] not in mal_ok) or (k.get('formmethod') and k['formmethod'].lower() != 'post'):
                F('6.1', sida, 'skickaknappen överstyr formulärets mål (formaction=%r, formmethod=%r); det effektiva målet ska vara POST /api/forfragan/' % (k.get('formaction'), k.get('formmethod')))
    for sida, fm in forfragan[:3]:
        falt = {x.get('name'): x for x in fm['falt']}
        for namn in ('namn', 'telefon', 'meddelande'):
            if namn not in falt:
                F('6.1', sida, 'förfrågan saknar fältet %r' % namn)
        tel = falt.get('telefon') or {}
        if tel and (tel.get('type') != 'tel' or tel.get('autocomplete') != 'tel'):
            F('6.2', sida, 'telefonfältet ska ha type="tel" och autocomplete="tel"')
        if tel and not tel.get('pattern'):
            F('6.2', sida, 'telefonfältet saknar pattern; "abc" går igenom (ägarens dom L4, mallens Forfragan.astro)')
        utan_fel = [n for n in ('namn', 'telefon', 'meddelande') if n in falt and not (falt[n].get('aria-describedby') or '').strip()]
        if utan_fel:
            F('6.2', sida, 'felbeskedet som text vid fältet (aria-describedby) saknas för %s; bara webbläsarens bubbla räcker inte (ägarens dom L4)' % ', '.join(utan_fel))
        if (falt.get('namn') or {}) and (falt.get('namn') or {}).get('autocomplete') != 'name':
            F('6.2', sida, 'namnfältet ska ha autocomplete="name"')
        if (falt.get('webbplats') or {}).get('tabindex') != '-1':
            F('6.5', sida, 'honeypoten (fältet webbplats med tabindex="-1") saknas')
        if 'fylltid' not in falt:
            F('6.5', sida, 'tidsfällan (dolt fält fylltid, varaktighet mätt i webbläsaren) saknas')
        if any(x.get('type') == 'file' for x in fm['falt']) and fm['attr'].get('enctype') != 'multipart/form-data':
            F('6.3', sida, 'formulär med bildfält behöver enctype="multipart/form-data"')
        if not any(x.get('id') == 'forfragan-saknas' for x in fm.get('felbesked', [])):
            F('6.2', sida, 'förfrågan saknar felbeskedet #forfragan-saknas som visas utan JavaScript')
        if not any(h.rstrip('/').endswith('/integritet') for h in fm['lankar']):
            F('6.8', sida, 'förfrågan saknar länk till /integritet/ vid knappen')
    if forfragan:
        tack = dist / 'tack' / 'index.html'
        if not tack.is_file():
            F('6.7', '(alla)', 'tacksidan /tack/ saknas')
        elif 'noindex' not in ''.join(m.get('content', '') for t_, m, *_ in sidobjekt[tack].el if t_ == 'meta' and m.get('name') == 'robots'):
            F('6.7', '/tack/', 'tacksidan saknar noindex')
        if not (dist / 'integritet' / 'index.html').is_file():
            F('6.8', '(alla)', 'integritetssidan /integritet/ saknas (ansvarig, ändamål, rättslig grund, lagringstid, rättigheter, kontakt)')
    # 2.5 giltig HTML, lokalt (W3C:s tjänst skulle få verksamhetens sidor skickade till sig)
    for sida, text in giltig_html(dist):
        F('2.5', sida or '(alla)', text)  # också ett verktygsfel: ej mätt är inte godkänt (revisionen 2026-10-03, F9)
    return fel, info, len(sidor)


def csp_skriptkallor(policy):
    """Den effektiva skriptpolicyn per direktiv: webbläsaren läser script-src-elem för skriptelement och script-src-attr
    för händelseattribut, var och en med script-src och sist default-src som reserv (revisionen 2026-10-03, F22: ett
    separat script-src-elem gick förbi kontrollen av script-src). Värdet None betyder att inget direktiv gäller."""
    direktiv = {}
    for del_ in policy.split(';'):
        bitar = del_.split()
        if bitar:
            direktiv.setdefault(bitar[0].lower(), bitar[1:])
    reserv = direktiv.get('script-src', direktiv.get('default-src'))
    # script-src självt styr fortfarande 'unsafe-eval' och är reserv för båda; det prövas också (omgång tre, F22)
    return {'script-src': reserv, 'script-src-elem': direktiv.get('script-src-elem', reserv), 'script-src-attr': direktiv.get('script-src-attr', reserv)}


def sida_av(dist, f):
    rel = f.relative_to(dist)
    if rel.name == 'index.html':
        return '/' if rel.parent == Path('.') else '/%s/' % rel.parent.as_posix()
    return '/' + rel.as_posix()


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
    """Byggstandarden 3.3 ur stilrapporten (stil.mjs mäter i webbläsaren i 390 px). Ej mätt är inte godkänt: saknad eller
    oläsbar rapport, och en sida vars 390-mätning föll, ger fel (revisionen 2026-10-03, F9)."""
    try:
        data = json.loads(Path(stil).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return [{'punkt': '3.3', 'sida': '(alla)', 'text': 'klickytorna är inte mätta: stilrapporten (prov/stil/STIL.json) saknas eller är oläsbar'}]
    ut = [{'punkt': '3.3', 'sida': f.get('sida', '?'), 'text': 'klickytorna är inte mätta i 390: %s' % (f.get('fel') or 'mätningen föll')}
          for f in data.get('fel') or [] if f.get('vy') == '390']
    if not any(r.get('vy') == '390' for r in data.get('rader') or []):
        ut.append({'punkt': '3.3', 'sida': '(alla)', 'text': 'klickytorna är inte mätta: ingen sida mätt i 390'})
    per_sida = {}
    for y in data.get('smaYtor', []):
        per_sida.setdefault(y['sida'], []).append(y)
    return ut + [{'punkt': '3.3', 'sida': s, 'text': '%d klickytor under 24 px i 390, t.ex. "%s" %d×%d' % (len(ys), ys[0]['text'], ys[0]['bredd'], ys[0]['hojd'])}
                 for s, ys in sorted(per_sida.items())]


def smaknappar(stil):
    """Byggstandarden 3.3, primära knappar 44×44: information ur stilrapporten (vilka som är primära avgör granskaren)."""
    try:
        data = json.loads(Path(stil).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    per_sida = {}
    for y in data.get('smaKnappar', []):
        per_sida.setdefault(y['sida'], []).append(y)
    return [{'punkt': '3.3', 'sida': s, 'text': '%d knappar eller ring-/mejllänkar under 44 px i 390, t.ex. "%s" %d×%d; primära knappar ska vara 44×44' % (
        len(ys), ys[0]['text'], ys[0]['bredd'], ys[0]['hojd'])} for s, ys in sorted(per_sida.items())]


def konsolfel(inspektion):
    """Byggstandarden 8.7 ur provets inspektion (inspektera.mjs per sida och vy): inga fel i webbläsarens konsol och
    inga sidfel. En CSP-överträdelse, ett skript, typsnitt eller en bild som inte laddas syns där (designprovet
    2026-10-05: inbäddade typsnitt som CSP:n vägrade). Ej mätt är inte godkänt."""
    rot = Path(inspektion)
    filer = sorted(rot.glob('*/INSPEKTION.json'))
    if not filer:
        return [{'punkt': '8.7', 'sida': '(alla)', 'text': 'konsolen är inte läst: provets inspektion (prov/inspektion/*/INSPEKTION.json) saknas'}]
    ut = []
    for f in filer:
        sida = '/' if f.parent.name == 'hem' else '/%s/' % f.parent.name
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            ut.append({'punkt': '8.7', 'sida': sida, 'text': 'inspektionen är oläsbar: %s' % f.name})
            continue
        sida = urlparse(str(d.get('adress') or '')).path or sida  # sidans väg ur adressen, inte katalognamnet
        # bara felen på den här sidan (inspektionens bakåt/framåt besöker en länkad sida), och varje text en gång
        egen = lambda x: not x.get('url') or urlparse(str(x['url'])).path == sida  # noqa: E731
        fel = {}
        for vy, r in sorted((d.get('vyer') or {}).items()):
            for x in [x for x in r.get('konsol') or [] if x.get('typ') == 'error' and egen(x)]:
                fel.setdefault(str(x.get('text', ''))[:160], []).append(vy)
            for x in [x for x in r.get('sidfel') or [] if egen(x)]:
                fel.setdefault('sidfel: ' + str(x.get('text', ''))[:150], []).append(vy)
        if fel:
            ut.append({'punkt': '8.7', 'sida': sida, 'text': '%d olika fel i webbläsarens konsol: %s' % (
                len(fel), '; '.join('%s (%s)' % (t, ', '.join(sorted(set(v)))) for t, v in list(fel.items())[:3]))})
    return ut


def egna_bilder(dist):
    """Verksamhetens egna fotografier i bygget: olika rasterbilder i <img>, utan logotyper och ikoner."""
    srcs = set()
    for f in Path(dist).rglob('*.html'):
        for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', f.read_text(encoding='utf-8', errors='replace')):
            if re.search(r'\.(webp|avif|jpe?g|png)(\?|$)', src, re.I) and not re.search(r'logo|ikon|icon|favicon|marke', src, re.I):
                srcs.add(re.sub(r'\.[0-9a-zA-Z_-]{6,}\.(webp|avif|jpe?g|png)$', '', src.split('?')[0]))
    return len(srcs)


def bestallning_finns(bestallning):
    try:
        return bool(bestallning) and len(Path(bestallning).read_text(encoding='utf-8').strip()) > 40
    except OSError:
        return False


def _ihop(s):
    return re.sub(r'\s+', '', html.unescape(re.sub(r'<[^>]+>', ' ', s)).lower())


def adress(dist, verksamhet):
    """7.4: gatuadressen som verksamheten själv visar (adress.publik) står i sidfoten på varje sida, på kontaktsidan och
    som streetAddress i JSON-LD (ägarens A/B-omdöme 2026-10-02: fullständig NAP avgjorde). Är den inte publik står den
    ingenstans (domarna L5 och L6)."""
    try:
        adr = json.loads(Path(verksamhet).read_text(encoding='utf-8')).get('adress') or {}
    except (OSError, ValueError):
        return []
    if not adr.get('gata'):
        return []
    if adr.get('publik') is not True:
        # obekräftad eller enbart registrerad adress står ingenstans, inte heller i JSON-LD (ägarens domar L5 och L6)
        gata, fel = _ihop(adr['gata']), []
        for f in sorted(Path(dist).rglob('*.html')):
            if gata in _ihop(f.read_text(encoding='utf-8', errors='replace')):
                fel.append({'punkt': '7.4', 'sida': sida_av(dist, f),
                            'text': 'gatuadressen "%s" står på sidan fast adress.publik är falsk (obekräftad eller bara i register)' % adr['gata']})
        return fel
    gata, fel, ld = _ihop(adr['gata']), [], False
    for f in sorted(Path(dist).rglob('*.html')):
        sida = sida_av(dist, f)
        raw = f.read_text(encoding='utf-8', errors='replace')
        if re.search(r'name="robots"[^>]*noindex', raw):
            continue
        fot = re.search(r'<footer\b.*?</footer>', raw, re.S)
        if not fot or gata not in _ihop(fot.group(0)):
            fel.append({'punkt': '7.4', 'sida': sida, 'text': 'gatuadressen "%s" saknas i sidfoten (adress.publik är sann)' % adr['gata']})
        if 'kontakt' in sida and gata not in _ihop(re.sub(r'<(script|style)\b.*?</\1>', ' ', raw, flags=re.S)):
            fel.append({'punkt': '7.4', 'sida': sida, 'text': 'gatuadressen "%s" saknas på kontaktsidan' % adr['gata']})
        for m in re.finditer(r'"streetAddress"\s*:\s*"([^"]*)"', raw):
            ld = ld or _ihop(m.group(1)) == gata
    if not ld:
        fel.append({'punkt': '7.4', 'sida': '(alla)', 'text': 'JSON-LD saknar streetAddress "%s" (adress.publik är sann)' % adr['gata']})
    return fel


# Domäner som stoppar robotar eller kräver inloggning: listas men prövas inte (sdmg15-intaget: vitlista i länkkontrollen)
EJ_PROVADE = ('google.', 'goo.gl', 'facebook.com', 'fb.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'youtu.be',
              'tiktok.com', 'twitter.com', 'x.com', 'messenger.com', 'wa.me', 'whatsapp.com')


WEBBLASARE = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'


def utgaende(dist, tidsgrans=8):
    """Sajtens utgående länkar och om de svarar: HEAD, och GET som reserv. Ingen grind, bara information (7.4: en
    felaktig omdömes- eller kataloglänk är ett förtroendefel). PROV_OFFLINE hoppar över nätet."""
    import concurrent.futures
    import urllib.request
    egen = None
    start = Path(dist) / 'index.html'
    if start.is_file():
        m = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', start.read_text(encoding='utf-8', errors='replace'))
        egen = urlparse(m.group(1)).hostname if m else None
    lankar = {}
    for f in sorted(Path(dist).rglob('*.html')):
        for href in re.findall(r'<a\b[^>]*href="(https?://[^"#]+)', f.read_text(encoding='utf-8', errors='replace')):
            href = html.unescape(href)
            if urlparse(href).hostname and urlparse(href).hostname != egen:
                lankar.setdefault(href, []).append(sida_av(dist, f))

    import hamta_sajt as hs  # adresskontroll i anslutningen: en länk i sajten får inte nå det egna nätet (revisionen, F5)

    def pröva(url):
        vard = (urlparse(url).hostname or '').lower()
        if any(vard == d.rstrip('.') or vard.endswith('.' + d.rstrip('.')) or (d.endswith('.') and (vard.startswith(d) or ('.' + d) in vard)) for d in EJ_PROVADE):
            return 'ej prövad (stoppar robotar)'
        if os.environ.get('PROV_OFFLINE'):
            return 'ej prövad (offline)'
        try:
            hs.adress_ok(url)
            hs.adress_for(urlparse(url).hostname)  # bara publika adresser prövas; anslutningen prövar igen
        except hs.NekadAdress as e:
            return 'ej prövad (%s)' % e
        svar = None
        for metod in ('HEAD', 'GET'):
            try:
                req = urllib.request.Request(url, method=metod, headers={'User-Agent': 'Mozilla/5.0 (compatible; nortropic-webb-pro/1)'})
                with hs.oppnare().open(req, timeout=tidsgrans) as r:
                    return str(r.status)
            except urllib.error.HTTPError as e:
                if metod == 'GET' or e.code not in (400, 403, 404, 405, 501):
                    svar = str(e.code)
                    break
                svar = str(e.code)
            except Exception as e:  # noqa: BLE001 — nätfel är ett svar i sig
                svar = 'svarar inte (%s)' % type(e).__name__
        # En del sajter nekar robotar men svarar en webbläsare (imy.se gav 404 här och 200 i webbläsaren samma minut,
        # salong-kreativ 2026-10-03): pröva en gång till med webbläsarhuvud innan felet skrivs.
        try:
            req = urllib.request.Request(url, headers={'User-Agent': WEBBLASARE, 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
                                                       'Accept-Language': 'sv-SE,sv;q=0.9'})
            with hs.oppnare().open(req, timeout=tidsgrans) as r:
                return '%d med webbläsarhuvud, nekar robotar (%s)' % (r.status, svar)
        except Exception:  # noqa: BLE001 — då gäller robotens svar
            return svar
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        svar = dict(zip(lankar, ex.map(pröva, lankar)))
    return [{'url': u, 'svar': svar[u], 'sidor': sorted(set(s))} for u, s in lankar.items()]


def rapport(bygge, stil=None, bestallning=None, verksamhet=None, inspektion=None, brief=None):
    kontakt = kontaktmodell(brief)
    fel, info, n = granska(bygge, kontakt)
    if brief and kontakt is None:
        info.append({'punkt': '9.2', 'sida': '(alla)', 'text': 'BRIEF.md saknar §4 Primär handling; kontaktvägarna prövades bara som ett nästa steg per sida'})
    lankar = utgaende(bygge)
    for x in lankar:
        if x['svar'].startswith(('4', '5', 'svarar inte')):
            info.append({'punkt': '7.4', 'sida': x['sidor'][0], 'text': 'utgående länk svarar %s: %s' % (x['svar'], x['url'])})
    if verksamhet:
        fel += adress(bygge, verksamhet)
    if stil:
        fel += klickytor(stil)
        info += smaknappar(stil)
    if inspektion:
        fel += konsolfel(inspektion)
    antal = egna_bilder(bygge)
    if antal < 5 and not bestallning_finns(bestallning):
        fel.append({'punkt': '9.3', 'sida': '(alla)', 'text': '%d egna bilder och ingen beställning: beställ bilderna av verksamheten i underlag/<slug>/BESTALLNING.md (ägarens domar L2, L3)' % antal})
    elif antal < 5:
        info.append({'punkt': '9.3', 'sida': '(alla)', 'text': '%d egna bilder; beställningen finns, sajten är klar att visas men inte att lanseras' % antal})
    summa = {}
    for x in fel:
        summa[x['punkt']] = summa.get(x['punkt'], 0) + 1
    return {'schema': 1, 'bygge': str(bygge), 'sidor': n, 'fel': fel, 'info': info, 'fel_per_punkt': summa, 'utgaende': lankar,
            'standard': 'kunskap/byggstandard.md',
            'not': 'fel = entydiga avsteg från D-punkterna; info = kräver omdöme. Övriga punkter prövas av seo, axe, lighthouse, spill, utan-js och granskaren.'}


def markdown(r):
    rad = ['# Byggstandarden · %d sidor · %d fel · %d info' % (r['sidor'], len(r['fel']), len(r['info'])), '',
           'Punkterna står i `kunskap/byggstandard.md`. Fel stoppar provet; info kräver omdöme.', '']
    for rubrik, lista in (('Fel', r['fel']), ('Info', r['info'])):
        rad += ['## ' + rubrik, '']
        rad += ['| Punkt | Sida | Fynd |', '|---|---|---|'] + ['| %s | %s | %s |' % (x['punkt'], x['sida'], x['text'].replace('|', '/')) for x in lista] if lista else ['Inga.']
        rad.append('')
    rad += ['## Utgående länkar', '']
    rad += (['| Adress | Svar | Sidor |', '|---|---|---|'] + ['| %s | %s | %s |' % (x['url'], x['svar'], ', '.join(x['sidor'][:4])) for x in r.get('utgaende') or []]
            if r.get('utgaende') else ['Inga.'])
    rad.append('')
    return '\n'.join(rad)


def main(argv=None):
    p = argparse.ArgumentParser(prog='standard_kontroll', description=__doc__.split('\n\n')[0])
    p.add_argument('--bygge', required=True)
    p.add_argument('--ut', required=True)
    p.add_argument('--md')
    p.add_argument('--stil', help='STIL.json från stil.mjs, för klickytorna (3.3)')
    p.add_argument('--bestallning', help='underlag/<slug>/BESTALLNING.md, för bildkravet (9.3)')
    p.add_argument('--verksamhet', help='underlag/<slug>/VERKSAMHET.json, för den publika adressen (7.4)')
    p.add_argument('--inspektion', help='prov/inspektion/ med INSPEKTION.json per sida, för konsolen (8.7)')
    p.add_argument('--brief', help='underlag/<slug>/BRIEF.md, för kundens kontaktmodell (§4, punkt 9.2)')
    a = p.parse_args(argv)
    krav_vag(a.ut, "--ut")
    krav_vag(getattr(a, "md", None), "--md")
    krav_vag(getattr(a, "brief", None), "--brief")
    if not Path(a.bygge).is_dir():
        print('finns inte: ' + a.bygge, file=sys.stderr)
        return 2
    r = rapport(Path(a.bygge), a.stil, a.bestallning, a.verksamhet, a.inspektion, a.brief)
    Path(a.ut).write_text(json.dumps(r, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if a.md:
        Path(a.md).write_text(markdown(r), encoding='utf-8')
    print(json.dumps({'sidor': r['sidor'], 'fel': len(r['fel']), 'info': len(r['info']), 'fel_per_punkt': r['fel_per_punkt']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
