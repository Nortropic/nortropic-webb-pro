#!/usr/bin/env python3
"""design.py — DESIGN.md som kontrakt för den aktuella designen (Codex 2026-10-04, glapp 1; femstegsuppdraget steg 1).

    .venv/bin/python kontroller/design.py <slug> [--skriv] [--jamfor prov/inspektion/hem] [--kandidat kNN]

Ansvar per artefakt: referenspaketet (underlag/<slug>/referenser/paket-vNN/) har frysta observationer, bilder, mätvärden
(EXTRAKT), källor och begränsningar; KONCEPT.md har prövade alternativ, beslut och varför andra förkastades; DESIGN.md
(kunder/<slug>/sajt/DESIGN.md) är den aktuella designen; den valda prototypen (ateljéns vinnare) är körbar gestaltning
som förs vidare. DESIGN.md har prosa (komposition, bildbehandling, responsiva regler, avsiktliga avvikelser från
huvudreferensen, under rubrikerna Komposition, Typografi, Bildbehandling, Responsiva regler och Avvikelser från
huvudreferensen) och exakt ett kodblock ```json design``` med värdena; varje värde har `kalla` som börjar med
`uppmätt:` (med var det mättes), `uppskattat:` (ur bilden) eller `valt:` (för kunden, med skäl). Värdena genererar
src/styles/design.css (CSS-variablerna sajten använder); layouten bor i koden.

--skriv validerar och skriver design.css (slutkod 0 när DESIGN.md är giltig och filen skriven; det som återstår
skrivs som "kvar"). Utan --skriv kontrolleras att design.css är genererad ur den aktuella DESIGN.md och att sajten
använder variablerna, som provets grind design gör. --jamfor läser byggets uppmätta extrakt (inspektera.mjs --extrahera) och listar avvikelser mot DESIGN.md
(renderat typsnitt per roll, sidans ytor): underlag för granskaren, ingen dom.
--kandidat kNN gäller en kandidats eget projekt i skapandeflödet (kunder/<slug>/kandidater/<id>/sajt; huvudreferensen
jämförs då med kandidatens RIKTNING.md, inte REFERENSER.md).
Slutkod 0 giltig och aktuell, 1 ogiltig eller inaktuell, 2 fel i anropet.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
BLOCK = re.compile(r'^```json design[ \t]*\n(.*?)^```[ \t]*$', re.M | re.S)
NAMN = re.compile(r'^[a-z][a-z0-9-]{0,30}$')
HEX = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')
KALLA = re.compile(r'^(uppmätt|uppskattat|valt|importerat):\s*\S')  # importerat: ett värde ur en stilexport (Referos stilpaket)
TOKEN = re.compile(r'^--[a-z0-9][a-z0-9-]{0,60}$')
VILLKOR = re.compile(r'^@media \([a-z-]+: ?[a-z0-9-]+\)( and \([a-z-]+: ?[0-9a-z.-]+\))?$')  # @media (prefers-color-scheme: dark)
VALJARE = re.compile(r'^(?:\[data-[a-z-]+(?:="[a-z0-9-]+")?\]|\.[a-z][a-z0-9_-]{0,40})(?:\s+\.[a-z][a-z0-9_-]{0,40})?$')
IMPORTFIL = re.compile(r'^src/styles/[a-z0-9][a-z0-9/_.-]{0,100}\.css$')
STRUKTUR = ('brodsmulor',)
LANGD = re.compile(r'^(?:0|-?(?:\d+(?:\.\d+)?|\.\d+)(?:px|rem|em|ch|ex|lh|rlh|vw|vh|svh|lvh|dvh|vmin|vmax|cqi|cqw|%)|(?:clamp|min|max|calc)\([0-9a-z.+\-*/%, ()]+\))$')
FARLIGT = re.compile(r'[;{}<>\\]|/\*|\*/')
GENERISKA = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui', 'ui-serif', 'ui-sans-serif', 'ui-monospace',
             'ui-rounded', 'math', 'emoji', 'fangsong'}
FAMILJ = re.compile(r'^[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 \-]{0,60}$')
RESERV = re.compile(r'^[A-Za-zÀ-ÿ0-9 \-]+(?:,\s*[A-Za-zÀ-ÿ0-9 \-]+)*$')
ROLLER_KRAV = ('rubrik', 'brodtext')
HUVUD = '/* Genererad av kontroller/design.py ur DESIGN.md (sha256 %s). Ändra DESIGN.md och kör design.py --skriv, inte den här filen. */'


def las(text):
    """(värden, fel): exakt ett ```json design```-block, giltig JSON-objekt."""
    block = BLOCK.findall(text.replace('\r\n', '\n'))
    if len(block) != 1:
        return None, ['DESIGN.md ska ha exakt ett kodblock ```json design``` (har %d)' % len(block)]
    try:
        v = json.loads(block[0])
    except ValueError as e:
        return None, ['json design-blocket är inte giltig JSON: %s' % e]
    if not isinstance(v, dict):
        return None, ['json design-blocket ska vara ett objekt']
    return v, []


def blockhash(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def luminans(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    def kanal(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (kanal(h[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a, b):
    la, lb = sorted((luminans(a), luminans(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def validera(v):
    fel = []
    if v.get('schema') != 1:
        fel.append('schema ska vara 1')
    farger = v.get('farger')
    if not isinstance(farger, dict):
        fel.append('farger: minst två färger med roll')
        farger = {}
    elif len(farger) < 2:
        fel.append('farger: minst två färger med roll')
    for n, f in farger.items():
        if not NAMN.match(str(n)):
            fel.append('farger.%s: namnet ska vara a–z, 0–9, bindestreck' % n)
        if not isinstance(f, dict) or not HEX.match(str(f.get('varde', ''))):
            fel.append('farger.%s: varde ska vara hex (#rgb eller #rrggbb)' % n)
            continue
        if not str(f.get('roll') or '').strip():
            fel.append('farger.%s: roll saknas (vad färgen gör och hur stor yta den har)' % n)
        if not KALLA.match(str(f.get('kalla') or '')):
            fel.append('farger.%s: kalla ska börja med uppmätt:, uppskattat: eller valt: och säga var eller varför' % n)
    typ = v.get('typsnitt')
    if not isinstance(typ, dict):
        fel.append('typsnitt saknas')
        typ = {}
    for roll in ROLLER_KRAV:
        if roll not in typ:
            fel.append('typsnitt.%s saknas' % roll)
    for n, t in typ.items():
        if not NAMN.match(str(n)) or not isinstance(t, dict):
            fel.append('typsnitt.%s: ogiltigt namn eller värde' % n)
            continue
        if not FAMILJ.match(str(t.get('familj') or '')):
            fel.append('typsnitt.%s: familj ska vara ett typsnittsnamn (bokstäver, siffror, mellanslag, bindestreck)' % n)
        if t.get('reserv') is not None and not RESERV.match(str(t['reserv'])):
            fel.append('typsnitt.%s: reserv ska vara en lista med typsnittsnamn, kommaseparerad' % n)
        if not isinstance(t.get('vikt'), int) or not 100 <= t['vikt'] <= 900:
            fel.append('typsnitt.%s: vikt ska vara ett heltal 100–900' % n)
        for falt in ('storlek', 'radavstand'):
            x = str(t.get(falt, ''))
            if not (LANGD.match(x) or (falt == 'radavstand' and re.fullmatch(r'\d+(\.\d+)?', x))):
                fel.append('typsnitt.%s: %s ska vara en CSS-längd eller clamp()/min()/max() (%r)' % (n, falt, x))
        if 'teckenavstand' in t and not LANGD.match(str(t['teckenavstand'])):
            fel.append('typsnitt.%s: teckenavstand ska vara en CSS-längd' % n)
        if 'matt' in t and not LANGD.match(str(t['matt'])):
            fel.append('typsnitt.%s: matt ska vara en CSS-längd (till exempel 65ch)' % n)
        if not KALLA.match(str(t.get('kalla') or '')):
            fel.append('typsnitt.%s: kalla ska börja med uppmätt:, uppskattat: eller valt:' % n)
    for p in v.get('kontrast') or []:
        if not (isinstance(p, list) and len(p) == 3 and p[0] in farger and p[1] in farger and isinstance(p[2], (int, float))):
            fel.append('kontrast: varje par är [förgrund, bakgrund, minsta kvot] med färgnamn ur farger (%r)' % (p,))
            continue
        k = kontrast(farger[p[0]]['varde'], farger[p[1]]['varde']) if HEX.match(str(farger[p[0]].get('varde', ''))) and HEX.match(str(farger[p[1]].get('varde', ''))) else 0
        if k < p[2]:
            fel.append('kontrast: %s på %s är %.2f:1, under %s:1' % (p[0], p[1], k, p[2]))
    for bredd, sp in (v.get('spalter') or {}).items():
        if bredd == 'kalla':
            continue
        if not re.fullmatch(r'\d{3,4}', str(bredd)) or not isinstance(sp, dict):
            fel.append('spalter.%s: nyckeln är en bredd i px (390, 1440) och värdet ett objekt' % bredd)
            continue
        for n, x in sp.items():
            if n != 'kalla' and not (NAMN.match(str(n)) and (isinstance(x, int) or LANGD.match(str(x)))):
                fel.append('spalter.%s.%s: heltal eller CSS-längd krävs (%r)' % (bredd, n, x))
    for grupp in ('avstand', 'radier'):
        for n, x in (v.get(grupp) or {}).items():
            if n == 'kalla':
                continue
            if not NAMN.match(str(n)) or not LANGD.match(str(x)):
                fel.append('%s.%s: CSS-längd krävs (%r)' % (grupp, n, x))
    def gaa(x, vag):
        if isinstance(x, dict):
            for k, y in x.items():
                gaa(y, vag + '.' + str(k))
        elif isinstance(x, list):
            for i, y in enumerate(x):
                gaa(y, '%s[%d]' % (vag, i))
        elif isinstance(x, str) and FARLIGT.search(x) and not vag.endswith('kalla') and '.roll' not in vag and 'avvikelser' not in vag and 'bild' not in vag:
            fel.append('%s: tecknen ; { } < > \\ och kommentarer är inte tillåtna i värden' % vag)
    gaa({k: v.get(k) for k in ('farger', 'typsnitt', 'avstand', 'radier', 'spalter')}, '')
    if not isinstance(v.get('avvikelser', []), list):
        fel.append('avvikelser ska vara en lista (från referensen, till vårt, varför)')
    # importerade stilvärden (Codex via ägaren 2026-10-05, punkt 6: kontraktet stödjer importerade värden och valda
    # tillstånd, så att kontrollens förmåga aldrig avgör vad kunden får)
    imp = v.get('import', [])
    if not isinstance(imp, list):
        fel.append('import ska vara en lista med {fil, kalla}')
        imp = []
    for i, x in enumerate(imp):
        if not isinstance(x, dict) or not IMPORTFIL.match(str(x.get('fil') or '')) or '..' in str(x.get('fil')):
            fel.append('import[%d]: fil ska vara en .css-fil under src/styles/ (till exempel src/styles/stil/<namn>.css)' % i)
        elif not str(x.get('kalla') or '').strip():
            fel.append('import[%d]: kalla saknas (stilexportens källa, till exempel refero: <stil> <id>)' % i)
        elif x.get('sha256') is not None and not re.fullmatch(r'[0-9a-f]{64}', str(x['sha256'])):
            fel.append('import[%d]: sha256 ska vara 64 hextecken' % i)
    for n, f in farger.items():
        if isinstance(f, dict) and f.get('token') is not None and not TOKEN.match(str(f['token'])):
            fel.append('farger.%s: token ska vara ett CSS-variabelnamn (--color-…)' % n)
    for n, t in typ.items():
        if isinstance(t, dict) and t.get('token') is not None and not TOKEN.match(str(t['token'])):
            fel.append('typsnitt.%s: token ska vara ett CSS-variabelnamn (--font-…)' % n)
    tillstand = v.get('tillstand', {})
    if not isinstance(tillstand, dict):
        fel.append('tillstand ska vara ett objekt: {namn: {villkor eller valjare, farger}}')
        tillstand = {}
    for n, s in tillstand.items():
        if not NAMN.match(str(n)) or not isinstance(s, dict):
            fel.append('tillstand.%s: ogiltigt namn eller värde' % n)
            continue
        if bool(s.get('villkor')) == bool(s.get('valjare')):
            fel.append('tillstand.%s: ange antingen villkor (@media (prefers-color-scheme: dark)) eller valjare (.band--mork, [data-tema="mork"])' % n)
        elif s.get('villkor') and not VILLKOR.match(str(s['villkor'])):
            fel.append('tillstand.%s: villkor ska vara en enkel @media-fråga, till exempel @media (prefers-color-scheme: dark)' % n)
        elif s.get('valjare') and not VALJARE.match(str(s['valjare'])):
            fel.append('tillstand.%s: valjare ska vara en klass eller ett data-attribut (.band--mork, [data-tema="mork"])' % n)
        fs = s.get('farger')
        if not isinstance(fs, dict) or not fs:
            fel.append('tillstand.%s: farger med minst en färg ur farger och dess värde i tillståndet' % n)
            continue
        for fn, hx in fs.items():
            if fn not in farger:
                fel.append('tillstand.%s.farger.%s: färgen finns inte i farger' % (n, fn))
            elif not HEX.match(str(hx)):
                fel.append('tillstand.%s.farger.%s: värdet ska vara hex' % (n, fn))
        if not KALLA.match(str(s.get('kalla') or '')):
            fel.append('tillstand.%s: kalla ska börja med uppmätt:, uppskattat:, valt: eller importerat:' % n)
        for p in v.get('kontrast') or []:  # kontrastparen gäller också i tillståndet
            if isinstance(p, list) and len(p) == 3 and p[0] in farger and p[1] in farger and isinstance(p[2], (int, float)):
                a_ = fs.get(p[0], farger[p[0]].get('varde') if isinstance(farger[p[0]], dict) else None)
                b_ = fs.get(p[1], farger[p[1]].get('varde') if isinstance(farger[p[1]], dict) else None)
                if HEX.match(str(a_)) and HEX.match(str(b_)) and kontrast(a_, b_) < p[2]:
                    fel.append('tillstand.%s: kontrast %s på %s är %.2f:1, under %s:1' % (n, p[0], p[1], kontrast(a_, b_), p[2]))
    struktur = v.get('struktur', {})
    if not isinstance(struktur, dict) or any(k not in STRUKTUR or not isinstance(x, bool) for k, x in struktur.items()):
        fel.append('struktur ska vara ett objekt med sanningsvärden: %s' % ', '.join(STRUKTUR))
    return fel


def css(v):
    rader = [HUVUD % blockhash(v), ':root {']
    for n, f in v['farger'].items():
        rader.append('  --farg-%s: %s;' % (n, f['varde']))
    for n, t in v['typsnitt'].items():
        familj = t['familj'] if t['familj'].lower() in GENERISKA else "'%s'" % t['familj']  # generiska nyckelord citeras aldrig
        reserv = ', '.join(x if x.lower() in GENERISKA or re.fullmatch(r'[A-Za-z][A-Za-z-]*', x) else "'%s'" % x
                           for x in (r.strip() for r in str(t.get('reserv') or '').split(',')) if x)
        rader.append('  --typ-%s-familj: %s%s;' % (n, familj, ', ' + reserv if reserv else ''))
        rader.append('  --typ-%s-vikt: %s;' % (n, t['vikt']))
        rader.append('  --typ-%s-storlek: %s;' % (n, t['storlek']))
        rader.append('  --typ-%s-radavstand: %s;' % (n, t['radavstand']))
        if t.get('teckenavstand') is not None:
            rader.append('  --typ-%s-teckenavstand: %s;' % (n, t['teckenavstand']))
        if t.get('matt'):
            rader.append('  --typ-%s-matt: %s;' % (n, t['matt']))
    for grupp, prefix in (('avstand', 'avstand'), ('radier', 'radie')):
        for n, x in (v.get(grupp) or {}).items():
            if n != 'kalla':
                rader.append('  --%s-%s: %s;' % (prefix, n, x))
    for bredd, s in (v.get('spalter') or {}).items():
        if bredd != 'kalla' and isinstance(s, dict):
            for n, x in s.items():
                if n != 'kalla' and NAMN.match(str(n)):
                    rader.append('  --spalt-%s-%s: %s;' % (bredd, n, x))
    rader.append('}')
    for n, s in (v.get('tillstand') or {}).items():  # de valda tillstånden: mörkt läge, en inverterad sektion
        varden = ['  --farg-%s: %s;' % (fn, hx) for fn, hx in (s.get('farger') or {}).items()]
        if s.get('villkor'):
            rader += ['%s {' % s['villkor'], '  :root {'] + ['  ' + x for x in varden] + ['  }', '}']
        else:
            rader += ['%s {' % s['valjare']] + varden + ['}']
    return '\n'.join(rader) + '\n'


def anvanda_variabler(dist):
    """Variabelnamn som sajtens byggda CSS och inline-stilar använder: var(--x) i dist/**/*.css och *.html."""
    ut = set()
    for p in list(Path(dist).rglob('*.css')) + list(Path(dist).rglob('*.html')):
        try:
            ut.update(re.findall(r'var\(\s*--([a-z0-9-]+)', p.read_text(encoding='utf-8', errors='replace')))
        except OSError:
            continue
    return ut


def startsidans_css(dist):
    """Startsidans egen CSS: inline-<style> i dist/index.html och stilmallarna den länkar till inom dist/."""
    dist = Path(dist)
    html = (dist / 'index.html').read_text(encoding='utf-8', errors='replace') if (dist / 'index.html').is_file() else ''
    delar = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S) + re.findall(r'style="([^"]*)"', html)
    for href in re.findall(r'<link[^>]+rel="?stylesheet"?[^>]*href="(/[^"]+\.css)"', html) + re.findall(r'<link[^>]+href="(/[^"]+\.css)"[^>]*rel="?stylesheet"?', html):
        p = (dist / href.lstrip('/')).resolve()
        if p.is_file() and dist.resolve() in p.parents:
            delar.append(p.read_text(encoding='utf-8', errors='replace'))
    return '\n'.join(delar)


FARGNAMN = {  # CSS-färgnamnen (CSS Color 4): minifieraren byter #rrggbb mot ett kortare namn när det finns (#ffd700 → gold)
    'aliceblue': 'f0f8ff', 'antiquewhite': 'faebd7', 'aqua': '00ffff', 'aquamarine': '7fffd4', 'azure': 'f0ffff', 'beige': 'f5f5dc',
    'bisque': 'ffe4c4', 'black': '000000', 'blanchedalmond': 'ffebcd', 'blue': '0000ff', 'blueviolet': '8a2be2', 'brown': 'a52a2a',
    'burlywood': 'deb887', 'cadetblue': '5f9ea0', 'chartreuse': '7fff00', 'chocolate': 'd2691e', 'coral': 'ff7f50',
    'cornflowerblue': '6495ed', 'cornsilk': 'fff8dc', 'crimson': 'dc143c', 'cyan': '00ffff', 'darkblue': '00008b', 'darkcyan': '008b8b',
    'darkgoldenrod': 'b8860b', 'darkgray': 'a9a9a9', 'darkgreen': '006400', 'darkgrey': 'a9a9a9', 'darkkhaki': 'bdb76b',
    'darkmagenta': '8b008b', 'darkolivegreen': '556b2f', 'darkorange': 'ff8c00', 'darkorchid': '9932cc', 'darkred': '8b0000',
    'darksalmon': 'e9967a', 'darkseagreen': '8fbc8f', 'darkslateblue': '483d8b', 'darkslategray': '2f4f4f', 'darkslategrey': '2f4f4f',
    'darkturquoise': '00ced1', 'darkviolet': '9400d3', 'deeppink': 'ff1493', 'deepskyblue': '00bfff', 'dimgray': '696969',
    'dimgrey': '696969', 'dodgerblue': '1e90ff', 'firebrick': 'b22222', 'floralwhite': 'fffaf0', 'forestgreen': '228b22',
    'fuchsia': 'ff00ff', 'gainsboro': 'dcdcdc', 'ghostwhite': 'f8f8ff', 'gold': 'ffd700', 'goldenrod': 'daa520', 'gray': '808080',
    'green': '008000', 'greenyellow': 'adff2f', 'grey': '808080', 'honeydew': 'f0fff0', 'hotpink': 'ff69b4', 'indianred': 'cd5c5c',
    'indigo': '4b0082', 'ivory': 'fffff0', 'khaki': 'f0e68c', 'lavender': 'e6e6fa', 'lavenderblush': 'fff0f5', 'lawngreen': '7cfc00',
    'lemonchiffon': 'fffacd', 'lightblue': 'add8e6', 'lightcoral': 'f08080', 'lightcyan': 'e0ffff', 'lightgoldenrodyellow': 'fafad2',
    'lightgray': 'd3d3d3', 'lightgreen': '90ee90', 'lightgrey': 'd3d3d3', 'lightpink': 'ffb6c1', 'lightsalmon': 'ffa07a',
    'lightseagreen': '20b2aa', 'lightskyblue': '87cefa', 'lightslategray': '778899', 'lightslategrey': '778899', 'lightsteelblue': 'b0c4de',
    'lightyellow': 'ffffe0', 'lime': '00ff00', 'limegreen': '32cd32', 'linen': 'faf0e6', 'magenta': 'ff00ff', 'maroon': '800000',
    'mediumaquamarine': '66cdaa', 'mediumblue': '0000cd', 'mediumorchid': 'ba55d3', 'mediumpurple': '9370db', 'mediumseagreen': '3cb371',
    'mediumslateblue': '7b68ee', 'mediumspringgreen': '00fa9a', 'mediumturquoise': '48d1cc', 'mediumvioletred': 'c71585',
    'midnightblue': '191970', 'mintcream': 'f5fffa', 'mistyrose': 'ffe4e1', 'moccasin': 'ffe4b5', 'navajowhite': 'ffdead', 'navy': '000080',
    'oldlace': 'fdf5e6', 'olive': '808000', 'olivedrab': '6b8e23', 'orange': 'ffa500', 'orangered': 'ff4500', 'orchid': 'da70d6',
    'palegoldenrod': 'eee8aa', 'palegreen': '98fb98', 'paleturquoise': 'afeeee', 'palevioletred': 'db7093', 'papayawhip': 'ffefd5',
    'peachpuff': 'ffdab9', 'peru': 'cd853f', 'pink': 'ffc0cb', 'plum': 'dda0dd', 'powderblue': 'b0e0e6', 'purple': '800080',
    'rebeccapurple': '663399', 'red': 'ff0000', 'rosybrown': 'bc8f8f', 'royalblue': '4169e1', 'saddlebrown': '8b4513', 'salmon': 'fa8072',
    'sandybrown': 'f4a460', 'seagreen': '2e8b57', 'seashell': 'fff5ee', 'sienna': 'a0522d', 'silver': 'c0c0c0', 'skyblue': '87ceeb',
    'slateblue': '6a5acd', 'slategray': '708090', 'slategrey': '708090', 'snow': 'fffafa', 'springgreen': '00ff7f', 'steelblue': '4682b4',
    'tan': 'd2b48c', 'teal': '008080', 'thistle': 'd8bfd8', 'tomato': 'ff6347', 'turquoise': '40e0d0', 'violet': 'ee82ee', 'wheat': 'f5deb3',
    'white': 'ffffff', 'whitesmoke': 'f5f5f5', 'yellow': 'ffff00', 'yellowgreen': '9acd32'}


def _tal(m):
    """Ett tal i kanonisk form: inga inledande nollor före decimalpunkten, inga avslutande decimalnollor (0.50 → .5, -0.02 → -.02, 2.0 → 2)."""
    t = ('%.6f' % float(m.group(0))).rstrip('0').rstrip('.')
    if t.startswith('0.'):
        t = t[1:]
    elif t.startswith('-0.'):
        t = '-' + t[2:]
    return '0' if t in ('', '-', '-0') else t


def normera(namn, varde):
    """Jämförbart värde, lika för DESIGN.md:s värde och minifierarens utskrift: gemener, citattecken och blanksteg bort,
    hex i sex tecken, färgnamn som hex, tal i kanonisk form, nollängder utan enhet (granskningen av r54: Vite/lightningcss
    skriver 0.5rem som .5rem, #ffffff som #fff och #ffd700 som gold)."""
    v = str(varde).strip().lower().replace('"', '').replace("'", '')
    v = re.sub(r'\s+', '', v)
    v = re.sub(r'#([0-9a-f])([0-9a-f])([0-9a-f])(?![0-9a-f])', lambda m: '#' + ''.join(c * 2 for c in m.groups()), v)
    v = re.sub(r'(?<![\w#-])([a-z]+)(?![\w-])', lambda m: '#' + FARGNAMN[m.group(1)] if m.group(1) in FARGNAMN else m.group(1), v)
    v = re.sub(r'(?<![\w#.])-?(?:\d+\.?\d*|\.\d+)', _tal, v)
    v = re.sub(r'(?<![\w.#])0(?:px|rem|em|%)(?![\w])', '0', v)
    return v


def definitioner(dist):
    """Varje definition av designvariablerna i den byggda CSS:en: {namn: {normerat värde, …}}."""
    ut = {}
    for p in list(Path(dist).rglob('*.css')) + list(Path(dist).rglob('*.html')):
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for namn, varde in re.findall(r'--((?:farg|typ|avstand|radie|spalt)-[a-z0-9-]+)\s*:\s*([^;}]+)', text):
            ut.setdefault(namn, set()).add(normera(namn, varde))
    return ut


def variabler(v):
    """Namn och värde för varje variabel som css() genererar ur DESIGN.md (grundvärdena, i :root)."""
    grund = css(v).split('\n}\n', 1)[0]
    return {m.group(1): m.group(2) for m in re.finditer(r'^  --([a-z0-9-]+): (.+);$', grund, re.M)}


def tillatna(v):
    """{variabel: {normerade värden}}: grundvärdet och de deklarerade tillståndens värden. En definition i den byggda
    CSS:en med ett annat värde är en odeklarerad omdefinition."""
    ut = {n: {normera(n, x)} for n, x in variabler(v).items()}
    for s in (v.get('tillstand') or {}).values():
        for fn, hx in (s.get('farger') or {}).items():
            ut.setdefault('farg-' + fn, set()).add(normera('farg', hx))
    return ut


def tokens(v):
    """{token: (grupp, namn, värde)} för färger och typsnittsroller som pekar på en importerad stilvariabel."""
    ut = {}
    for n, f in (v.get('farger') or {}).items():
        if isinstance(f, dict) and f.get('token'):
            ut[f['token']] = ('farger', n, f.get('varde'))
    for n, t in (v.get('typsnitt') or {}).items():
        if isinstance(t, dict) and t.get('token'):
            ut[t['token']] = ('typsnitt', n, t.get('familj'))
    return ut


def importfel(v, sajt):
    """Fel i de importerade stilfilerna: filen finns (inga länkar), är oförändrad när sha256 anges (originalexporten
    står orörd; kundanpassningen skrivs i en egen fil), och varje token som DESIGN.md pekar på finns i en av dem med
    samma färgvärde."""
    import hashlib as h_
    fel, definierat = [], {}
    for x in v.get('import') or []:
        p = Path(sajt) / str(x.get('fil'))
        if not p.is_file() or p.is_symlink():
            fel.append('import: %s saknas i sajten' % x.get('fil'))
            continue
        data = p.read_bytes()
        if x.get('sha256') and h_.sha256(data).hexdigest() != x['sha256']:
            fel.append('import: %s är ändrad sedan stilexporten (sha256); anpassa i en egen fil, aldrig i originalet' % x.get('fil'))
        for namn, varde in re.findall(r'(--[a-z0-9-]+)\s*:\s*([^;}]+)', data.decode('utf-8', 'replace')):
            definierat.setdefault(namn, varde.strip())
    for tok, (grupp, namn, varde) in tokens(v).items():
        if tok not in definierat:
            fel.append('%s.%s: token %s finns inte i de importerade stilfilerna' % (grupp, namn, tok))
        elif grupp == 'farger' and HEX.match(str(varde)) and normera('farg', definierat[tok]) != normera('farg', varde):
            fel.append('farger.%s: token %s har värdet %s i stilfilen, DESIGN.md säger %s' % (namn, tok, definierat[tok], varde))
    return fel


def sajt_for(slug, kandidat=None, kunder=None):
    bas = Path(kunder or KUNDER) / slug
    return bas / 'kandidater' / kandidat / 'sajt' if kandidat else bas / 'sajt'


def kontroll(slug, kunder=None, underlag=None, kandidat=None, huvudreferens=None):
    """{'ok', 'fel': [...], 'info': [...], 'sha'} för provet: DESIGN.md giltig, design.css genererad ur den aktuella
    DESIGN.md, sajten använder färg- och typvariablerna, och (när REFERENSER.md pekar ut en huvudreferens, eller
    kandidatens RIKTNING.md med huvudreferens) samma huvudreferens i DESIGN.md."""
    import referensval
    sajt = sajt_for(slug, kandidat, kunder)
    md, cssfil = sajt / 'DESIGN.md', sajt / 'src' / 'styles' / 'design.css'
    if not md.is_file():
        return {'ok': False, 'fel': ['%s saknas: den aktuella designen ska stå där (steg 5)' % (md.relative_to(ROOT) if md.is_relative_to(ROOT) else md)], 'info': [], 'sha': None}
    try:
        v, fel = las(md.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError) as e:
        return {'ok': False, 'fel': ['DESIGN.md kunde inte läsas: %s' % e], 'info': [], 'sha': None}
    if v is None:
        return {'ok': False, 'fel': fel, 'info': [], 'sha': None}
    fel = validera(v)
    info = []
    sha = blockhash(v)
    if not fel:
        if not cssfil.is_file():
            fel.append('src/styles/design.css saknas: kör kontroller/design.py %s --skriv' % slug)
        elif cssfil.read_text(encoding='utf-8') != css(v):
            fel.append('src/styles/design.css är inte genererad ur den aktuella DESIGN.md: kör kontroller/design.py %s --skriv' % slug)
        dist = sajt / 'dist'
        anv = anvanda_variabler(dist) if dist.is_dir() else set()
        tok = tokens(v)  # en importerad stilvariabel (Referos --color-…) räknas som användning av färgen eller rollen
        farg = [n for n in v['farger'] if 'farg-' + n in anv or (v['farger'][n].get('token') or '').lstrip('-') in anv]
        typ = [n for n in v['typsnitt'] if any(x.startswith('typ-%s-' % n) for x in anv) or (v['typsnitt'][n].get('token') or '').lstrip('-') in anv]
        if not farg or not typ:
            fel.append('sajtens CSS använder inte DESIGN.md:s variabler (färger %d av %d, typsnittsroller %d av %d)' % (len(farg), len(v['farger']), len(typ), len(v['typsnitt'])))
        # startsidan själv: dess egen CSS använder minst en färg- och en typvariabel (granskningen av r54, punkt 4)
        start = startsidans_css(dist) if dist.is_dir() else ''
        tok_farg = [t for t, (g, _n, _x) in tok.items() if g == 'farger']
        tok_typ = [t for t, (g, _n, _x) in tok.items() if g == 'typsnitt']
        if not (re.search(r'var\(\s*--farg-', start) or any(re.search(r'var\(\s*%s\b' % re.escape(t), start) for t in tok_farg)) \
                or not (re.search(r'var\(\s*--typ-', start) or any(re.search(r'var\(\s*%s\b' % re.escape(t), start) for t in tok_typ)):
            fel.append('startsidans CSS (dist/index.html och dess stilmallar) använder inte DESIGN.md:s färg- och typvariabler')
        # variablerna finns i den byggda CSS:en med DESIGN.md:s värden; en omdefinition är tillåten när den är ett
        # deklarerat tillstånd (mörkt läge, en inverterad sektion), annars är den en avvikelse från kontraktet
        defs = definitioner(dist) if dist.is_dir() else {}
        ok = tillatna(v)
        saknas = [n for n in variabler(v) if n not in defs]
        andrade = ['%s (%s)' % (n, ', '.join(sorted(defs[n] - ok.get(n, set())))) for n in variabler(v) if n in defs and defs[n] - ok.get(n, set())]
        if saknas:
            fel.append('design.css följer inte med i bygget: %d variabler saknas i dist (%s)' % (len(saknas), ', '.join(saknas[:6])))
        if andrade:
            fel.append('variabler omdefinierade med värden som varken DESIGN.md eller dess tillstånd har: ' + '; '.join(andrade[:6]))
        fel += importfel(v, sajt)
        oanv = [n for n in v['farger'] if n not in farg] + ['typ-' + n for n in v['typsnitt'] if n not in typ]
        if oanv:
            info.append('oanvända värden i DESIGN.md (finns inte i sajtens CSS): ' + ', '.join(oanv))
    if kandidat:
        if huvudreferens and str(v.get('huvudreferens') or '').strip().lower() != huvudreferens.lower():
            fel.append('DESIGN.md:s huvudreferens (%r) är inte kandidatens (%r, RIKTNING.md)' % (v.get('huvudreferens'), huvudreferens))
    else:
        hr = referensval.huvudreferens(slug, underlag or UNDERLAG)
        if hr and str(v.get('huvudreferens') or '').strip().lower() != hr['namn'].lower():
            fel.append('DESIGN.md:s huvudreferens (%r) är inte REFERENSER.md:s (%r)' % (v.get('huvudreferens'), hr['namn']))
    matt = sum(1 for g in ('farger', 'typsnitt') for x in ((v.get(g) or {}).values() if isinstance(v.get(g), dict) else []) if isinstance(x, dict) and str(x.get('kalla', '')).startswith('uppmätt'))
    info.append('källor: %d uppmätta värden, avvikelser från referensen: %d' % (matt, len(v.get('avvikelser') or [])))
    return {'ok': not fel, 'fel': fel, 'info': info, 'sha': sha}


def jamfor(v, extrakt_kat):
    """Byggets uppmätta extrakt (vy-<bredd>-extrakt.json) mot DESIGN.md: renderat typsnitt för rubrik (h1/h2) och
    brödtext (main p), och om sidans största ytor finns bland DESIGN.md:s färger. Underlag, ingen dom."""
    ut = []
    farger = {normera('farg', f['varde']) for f in v['farger'].values() if isinstance(f, dict) and HEX.match(str(f.get('varde', '')))}
    norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower().replace('variable', ''))  # noqa: E731
    for f in sorted(Path(extrakt_kat).glob('vy-*-extrakt.json')):
        try:
            x = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            ut.append('%s: kunde inte läsas' % f.name)
            continue
        vy = f.name.split('-')[1]
        for roll, taggar in (('rubrik', ('h1', 'h2')), ('brodtext', ('p',))):
            t = (v.get('typsnitt') or {}).get(roll) or {}
            e = next((e for e in x.get('element', []) if e.get('tagg') in taggar and e.get('typsnitt', {}).get('renderat')), None)
            if not t or not e:
                continue
            ren = [r['familj'] for r in e['typsnitt']['renderat']]
            if str(t.get('familj', '')).lower() in GENERISKA:  # ett generiskt val (system-ui, serif) matchar plattformens egna typsnitt
                if any(r.get('eget') is False for r in e['typsnitt']['renderat']):
                    continue
            if not any(norm(t.get('familj')) and norm(t.get('familj')) in norm(r) or norm(r) in norm(t.get('familj')) for r in ren):
                ut.append('%s px, %s (%s): renderat %s, DESIGN.md säger %s' % (vy, roll, e.get('id'), ', '.join(ren), t.get('familj')))
        for yta in (x.get('farger') or [])[:3]:
            if yta.get('andel', 0) >= 0.1 and normera('farg', yta.get('varde', '')) not in farger:
                ut.append('%s px: ytan %s (%.0f %% av sidan) finns inte bland DESIGN.md:s färger' % (vy, yta['varde'], 100 * yta['andel']))
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='design', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--skriv', action='store_true', help='validera och skriv src/styles/design.css')
    p.add_argument('--jamfor', help='katalog med byggets vy-<bredd>-extrakt.json')
    p.add_argument('--kandidat', help='en kandidats projekt i skapandeflödet (kNN)')
    a = p.parse_args(argv)
    krav_slug(a.slug)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}', a.slug) or (a.kandidat and not re.fullmatch(r'k\d{2}', a.kandidat)):
        p.print_usage()
        return 2
    sajt = sajt_for(a.slug, a.kandidat)
    md = sajt / 'DESIGN.md'
    if not md.is_file():
        print('%s saknas' % (md.relative_to(ROOT) if md.is_relative_to(ROOT) else md))
        return 1
    v, fel = las(md.read_text(encoding='utf-8'))
    fel = fel or validera(v)
    if fel:
        print('DESIGN.md är ogiltig:\n' + '\n'.join('- ' + f for f in fel))
        return 1
    if a.skriv:
        ut = sajt / 'src' / 'styles' / 'design.css'
        lankar = [x for x in (KUNDER / a.slug, sajt.parent, sajt, sajt / 'src', ut.parent) if x.is_symlink()]
        if lankar:  # kod som körts vid ett bygge kan ha lagt länken; filen skrivs aldrig genom den (granskning 6)
            print('%s är en länk; design.css skrivs inte' % lankar[0])
            return 1
        ut.parent.mkdir(parents=True, exist_ok=True)
        if ut.is_symlink():
            ut.unlink()
        ut.write_text(css(v), encoding='utf-8')
        print('Skrev %s (%d variabler).' % (ut.relative_to(ROOT) if ut.is_relative_to(ROOT) else ut, css(v).count('  --')))
    hr = None
    if a.kandidat:  # kandidatens huvudreferens står i dess RIKTNING.md (kontroller/kandidater.py)
        import kandidater
        hr = (kandidater.riktningens_referens(a.slug, a.kandidat) or {}).get('namn')
    k = kontroll(a.slug, kandidat=a.kandidat, huvudreferens=hr)
    for f in k['fel']:
        print(('kvar: ' if a.skriv else 'FEL: ') + f)
    for i in k['info']:
        print('info: ' + i)
    if a.jamfor:
        avv = jamfor(v, a.jamfor)
        print('Avvikelser mot DESIGN.md (uppmätt i bygget):' + ('\n' + '\n'.join('- ' + x for x in avv) if avv else ' inga'))
    if a.skriv:  # skrivningen lyckades; att sajten använder variablerna prövar provets grind design efter bygget
        return 0
    return 0 if k['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
