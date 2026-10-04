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
HUVUD = re.compile(r'^Huvudreferens:\s*(?P<namn>.+?)\s+[—–-]+\s+(?P<vad>.+?)\s*$', re.M | re.I)  # en rad: namn — vad den bär


def huvudreferens(slug, underlag):
    """Den sammanhängande huvudreferensen för komposition, typografi, proportioner och bildbehandling (designprovet,
    ägarbeslut 2026-10-04): raden `Huvudreferens: <referensens rubrik> — <vad den bär>` i REFERENSER.md, och dess Bildval-
    bilder (raderna under referensens rubrik). Ger {'namn', 'vad', 'bilder': [(Path, text)]} eller None."""
    u = Path(underlag) / slug
    text = (u / 'REFERENSER.md').read_text(encoding='utf-8') if (u / 'REFERENSER.md').is_file() else ''
    m = HUVUD.search(text)
    if not m:
        return None
    namn = m.group('namn').strip().strip('*`').strip()
    bilder = [(v['fil'], '%s — Fråga: %s' % (v['vad'], v['fraga'])) for v in bildval(slug, underlag)
              if v['fil'] and rubriknamn(v['referens']) == namn.lower()]
    return {'namn': namn, 'vad': m.group('vad').strip(), 'bilder': bilder}


def rubriknamn(rubrik):
    """Referensens namn ur rubriken: delen före ' — ', ' – ', ' - ' eller ': ' ('## Snick — snickeri i Umeå' → 'snick'),
    gemener. Huvudreferensen matchas exakt mot den, så att 'Snick' inte träffar 'Snickarglädje'."""
    r = str(rubrik).strip().lstrip('#').strip().strip('*`').strip()
    return re.split(r'\s+[—–-]+\s+|:\s+', r, maxsplit=1)[0].strip().strip('*`').strip().lower()


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
