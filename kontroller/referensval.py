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


def referensbilder(slug, underlag, tak=16):
    """Bilderna till skapare och granskare: [(Path, text)]. Bildvalen först, i byggarens ordning (den är prioriteringen när
    taket nås), sedan första vyn för referenser som saknar bildval, upp till taket."""
    ut, sedda, med_val = [], set(), set()
    for v in bildval(slug, underlag):
        if v['fil'] and v['fil'] not in sedda:
            ut.append((v['fil'], '%s — Fråga: %s' % (v['vad'], v['fraga'])))
            sedda.add(v['fil'])
            med_val.add(v['fil'].parent.name if v['fil'].parent.name not in ('390', '1440') else v['fil'].parents[1].name)
    for p, text in forsta_vyer(slug, underlag):
        if p not in sedda and p.parent.name not in med_val:
            ut.append((p, text))
            sedda.add(p)
    return ut[:tak]
