#!/usr/bin/env python3
"""referensval.py — referensbeslutets bilder: raderna i underlag/<slug>/REFERENSER.md som pekar ut sektion eller tillstånd.

    Bildval: referenser/<namn>/<fil>.png — <vad som jämförs> — Fråga: <jämförelsefrågan>

En rad per bild, under referensens rubrik i REFERENSER.md. Ateljén (kontroller/atelje.py) och granskaren
(kontroller/granska.py) får just de bilderna med frågan, i den ordning byggaren skrev dem; första vyn
(vy-390-forsta.png, vy-1440-forsta.png per referens) är reserv när raderna saknas. Backlogposten om
referensöverföringen (Codex 2026-10-03): det som faktiskt nådde skapare och granskare var sidornas toppar, fast
referensjakten vill jämföra rytm, sektioner och undersidor.

Ingen CLI. Importeras från kontroller/.
"""
import os
import re
from pathlib import Path

RAD = re.compile(r'^Bildval:\s*(?P<fil>referenser/\S+)\s+[—–-]+\s+(?P<vad>.+?)\s+[—–-]+\s+Fråga:\s*(?P<fraga>.+?)\s*$', re.M | re.I)  # tankstreck med mellanslag runt; filnamn saknar mellanslag
RUBRIK = re.compile(r'^#{1,3}\s+(.+?)\s*$', re.M)
BILD = {'.png', '.jpg', '.jpeg', '.webp'}
HUVUD = re.compile(r'^\s*(?:[-*]\s+)?\**Huvudreferens(?![a-zåäö])\**:?\**\s*(?P<namn>.+?)\s+[—–-]+\s+(?P<vad>.+?)\s*$', re.I)  # en rad: namn — vad den bär
# en kandidat per grundidé (Codex via ägaren 2026-10-05: sammanhållningen ska följa ett välgrundat val, inte låsas före
# utforskningen); ateljén väljer riktning, och den valda riktningens referens blir huvudreferensen (VINNARE.json)
KANDIDAT = re.compile(r'^\s*(?:[-*]\s+)?\**Huvudreferenskandidat\**:?\**\s*(?P<namn>.+?)\s+[—–-]+\s+(?P<vad>.+?)\s*$', re.I)


def huvudreferens(slug, underlag):
    """Den sammanhängande huvudreferensen för komposition, typografi, proportioner och bildbehandling, med sina Bildval-
    bilder (raderna under referensens rubrik). Efter ateljéns val är det den valda riktningens referens
    (underlag/<slug>/atelje/VINNARE.json, fältet huvudreferens): sammanhållningen följer valet (Codex via ägaren
    2026-10-05). Före ett val: raden `Huvudreferens: <referensens rubrik> — <vad den bär>` i REFERENSER.md (designprovet,
    ägarbeslut 2026-10-04). Ger {'namn', 'vad', 'bilder': [(Path, text)], 'kalla'} eller None."""
    v = vald(slug, underlag)
    if v:
        return dict(referens(slug, underlag, v['namn']), vad=v['vad'], kalla='ateljéns val (VINNARE.json)')
    rader = huvudreferensrader(slug, underlag)
    if len({n.lower() for n, _ in rader}) != 1:
        return None  # ingen eller flera olika: tvetydigt, aldrig den första som råkar stå överst
    namn, vad = rader[0]
    return dict(referens(slug, underlag, namn), vad=vad, kalla='REFERENSER.md')


def referens(slug, underlag, namn):
    """En referens ur REFERENSER.md med sina Bildval-bilder, matchad exakt på rubrikens namn: {'namn', 'bilder'}."""
    return {'namn': namn, 'bilder': [(v['fil'], '%s — Fråga: %s' % (v['vad'], v['fraga'])) for v in bildval(slug, underlag)
                                     if v['fil'] and rubriknamn(v['referens']) == str(namn).strip().lower()]}


def vald(slug, underlag):
    """Ateljéns valda huvudreferens ({'namn', 'vad'}) ur underlag/<slug>/atelje/VINNARE.json, eller None."""
    try:
        import json
        h = json.loads((Path(underlag) / slug / 'atelje' / 'VINNARE.json').read_text(encoding='utf-8')).get('huvudreferens')
    except (OSError, ValueError, AttributeError):
        return None
    if isinstance(h, dict) and isinstance(h.get('namn'), str) and h['namn'].strip():
        return {'namn': h['namn'].strip(), 'vad': str(h.get('vad') or '').strip()}
    return None


def _rader(slug, underlag, monster):
    f = Path(underlag) / slug / 'REFERENSER.md'
    ut, staket = [], False
    for rad in (f.read_text(encoding='utf-8').splitlines() if f.is_file() else []):
        if rad.lstrip().startswith(('```', '~~~')):
            staket = not staket
            continue
        m = None if staket else monster.match(rad)
        if m:
            ut.append((m.group('namn').strip().strip('*`').strip(), m.group('vad').strip().strip('*').strip()))
    return ut


def huvudreferensrader(slug, underlag):
    """Alla Huvudreferens-rader i REFERENSER.md utanför kodstaket: [(namn, vad)]. Godtar fet stil och listprefix."""
    return _rader(slug, underlag, HUVUD)


def kandidater(slug, underlag):
    """Huvudreferenskandidaterna (en per grundidé) och en Huvudreferens-rad, i filens ordning, en gång per namn:
    [{'namn', 'vad', 'bilder'}]. Ateljéns riktningar bygger var och en på sin kandidat."""
    sedda, ut = set(), []
    for namn, vad in _rader(slug, underlag, KANDIDAT) + huvudreferensrader(slug, underlag):
        if namn.lower() not in sedda:
            sedda.add(namn.lower())
            ut.append(dict(referens(slug, underlag, namn), vad=vad))
    return ut


def huvudreferens_fel(slug, underlag):
    """Varför huvudreferensen inte kan läsas, eller None."""
    if vald(slug, underlag):
        return None
    rader = huvudreferensrader(slug, underlag)
    namn = sorted({n for n, _ in rader}, key=str.lower)
    if not rader:
        return 'ingen rad "Huvudreferens: <referens> — <vad den bär>"'
    if len({n.lower() for n in namn}) > 1:
        return 'flera olika huvudreferenser: %s' % ', '.join(namn)
    return None


def rubriknamn(rubrik):
    """Referensens namn ur rubriken: delen före ' — ', ' – ', ' - ', ' · ' eller ': ' ('## Snick — snickeri i Umeå' och
    '## Snick · bransch · https://…' → 'snick'), gemener. Huvudreferensen matchas exakt mot den, så att 'Snick' inte
    träffar 'Snickarglädje'."""
    r = str(rubrik).strip().lstrip('#').strip().strip('*`').strip()
    return re.split(r'\s+[—–·-]+\s+|:\s+', r, maxsplit=1)[0].strip().strip('*`').strip().lower()


def bildval(slug, underlag):
    """[{'fil': Path, 'rel': 'referenser/…', 'vad', 'fraga', 'referens', 'fel'}] i REFERENSER.md:s ordning. En rad vars fil
    saknas, inte är en bild eller ligger utanför underlag/<slug>/referenser/ får 'fel' satt och ingen 'fil'."""
    u = Path(underlag) / slug
    text = (u / 'REFERENSER.md').read_text(encoding='utf-8') if (u / 'REFERENSER.md').is_file() else ''
    rot = os.path.realpath(u / 'referenser')
    ut = []
    for m in RAD.finditer(text):
        rubriker = [r.group(1) for r in RUBRIK.finditer(text[:m.start()])]
        post = {'rel': m.group('fil'), 'vad': m.group('vad').strip(), 'fraga': m.group('fraga').strip(),
                'referens': rubriker[-1] if rubriker else '', 'fil': None, 'fel': None}
        p = u / m.group('fil')
        verklig = os.path.realpath(p)
        if not (verklig == rot or verklig.startswith(rot + os.sep)):
            post['fel'] = 'utanför referenser/'
        elif not p.is_file() or p.suffix.lower() not in BILD:
            post['fel'] = 'filen saknas eller är ingen bild'
        else:
            post['fil'] = p
        ut.append(post)
    return ut


def forsta_vyer(slug, underlag):
    """Första vyn per referens, som reserv: [(Path, 'första vyn')]."""
    u = Path(underlag) / slug / 'referenser'
    ut = []
    if not u.is_dir():
        return ut
    for d in sorted(p for p in u.glob('*') if p.is_dir()):
        for vy in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
            hit = sorted(d.rglob(vy))
            if hit:
                ut.append((hit[0], 'första vyn'))
    return ut


def referensnamn(rel):
    """Referensens identitet: första ledet i sökvägen relativt referenser/ (inte närmaste katalognamn: två referenser kan
    båda ha en undermapp kontakt; Codex 2026-10-04, F38)."""
    delar = [d for d in str(rel).replace('\\', '/').split('/') if d]
    return delar[1] if len(delar) > 1 and delar[0] == 'referenser' else (delar[0] if delar else '')


def felrader(slug, underlag):
    """Bildval som inte gick att läsa, för uppdragstexten: bygget pekade ut en bild som saknas eller ligger fel. De ersätts
    aldrig tyst med första vyn (Codex 2026-10-04, F38)."""
    return ['%s: %s (%s — Fråga: %s)' % (v['rel'], v['fel'], v['vad'], v['fraga']) for v in bildval(slug, underlag) if v['fel']]


def referensbilder(slug, underlag, tak=16):
    """Bilderna till skapare och granskare: [(Path, text)]. Bildvalen först, i byggarens ordning (den är prioriteringen när
    taket nås), sedan första vyn bara för referenser som saknar Bildval-rader helt; en referens med en felaktig rad får
    ingen reserv, felet står i felrader()."""
    ut, sedda, med_rad = [], set(), set()
    for v in bildval(slug, underlag):
        med_rad.add(referensnamn(v['rel']))
        if v['fil'] and v['fil'] not in sedda:
            ut.append((v['fil'], '%s — Fråga: %s' % (v['vad'], v['fraga'])))
            sedda.add(v['fil'])
    rot = Path(underlag) / slug / 'referenser'
    for p, text in forsta_vyer(slug, underlag):
        if p not in sedda and referensnamn('referenser/' + p.relative_to(rot).as_posix()) not in med_rad:
            ut.append((p, text))
            sedda.add(p)
    return ut[:tak]
