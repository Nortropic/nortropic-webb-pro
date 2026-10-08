#!/usr/bin/env python3
"""bildstatus.py — leveransens visuella status ur beställningen: visuellt färdig, eller visuellt begränsad av saknat
material (bevakningen 2026-10-03, Codex: systemet ska skilja en visuellt färdig sajt från ett förslag som begränsas av
saknat kundmaterial; backloggen B-20261003-bildernas-uppgift-och-leveransens-visuella-statu).

    .venv/bin/python kontroller/bildstatus.py <slug>

Bär underlag/<slug>/BESTALLNING.md en bildbeställning, ett avsnitt "## Bilder" med minst en rad i en lista eller i en
tabells kropp, är leveransen "visuellt begränsad av saknat material", och raderna är det som saknas. Annars är den
"visuellt färdig". Utan beställning, eller när den inte går att läsa, finns ingen status. Samma besked står i RAPPORT.md
(bygg-sajt steg 7, punkt 13) och som chip i dashboarden (bygget). Statusen säger vad som saknas, inte hur bra sajten
är: granskarens betyg sätts på sajten som den visas (kritik/GRANSKARE.md, Saknat underlag). Exit 0.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
BEGRANSAD = 'visuellt begränsad av saknat material'
FARDIG = 'visuellt färdig'
RUBRIK = re.compile(r'^##\s+Bilder\b', re.I)
LISTRAD = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+\S')
TABELLRAD = re.compile(r'^\s*\|.*\|\s*$')
AVSKILJARE = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$')


def bestallda_bilder(text):
    """Raderna i beställningens avsnitt Bilder: listpunkter och tabellens kropp (inte rubrikraden eller avskiljaren)."""
    rader = text.split('\n')
    i = next((n for n, r in enumerate(rader) if RUBRIK.match(r)), None)
    if i is None:
        return []
    avsnitt = []
    for r in rader[i + 1:]:
        if re.match(r'^#{1,2}\s', r):
            break
        avsnitt.append(r)
    ut = []
    for n, r in enumerate(avsnitt):
        if LISTRAD.match(r):
            ut.append(r.strip())
        elif TABELLRAD.match(r) and not AVSKILJARE.match(r):
            if n + 1 < len(avsnitt) and AVSKILJARE.match(avsnitt[n + 1]):
                continue  # tabellens rubrikrad
            ut.append(r.strip())
    return ut


def visuell_status(slug, underlag=None):
    """{'status': FARDIG, BEGRANSAD eller None, 'text', 'kalla', 'bestallda'} för kunden."""
    f = Path(underlag or UNDERLAG) / slug / 'BESTALLNING.md'
    kalla = 'underlag/%s/BESTALLNING.md' % slug
    try:
        if f.is_symlink() or not f.is_file():
            return {'status': None, 'text': 'ingen beställning till verksamheten', 'kalla': None, 'bestallda': []}
        text = f.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        return {'status': None, 'text': 'beställningen går inte att läsa: %s' % e, 'kalla': kalla, 'bestallda': []}
    best = bestallda_bilder(text)
    if best:
        return {'status': BEGRANSAD, 'kalla': kalla, 'bestallda': best,
                'text': '%s: %d bilder beställda i %s' % (BEGRANSAD, len(best), kalla)}
    return {'status': FARDIG, 'kalla': kalla, 'bestallda': [], 'text': '%s: ingen bildbeställning i %s' % (FARDIG, kalla)}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 1:
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        return 2
    s = visuell_status(a[0])
    print(json.dumps(s, ensure_ascii=False, indent=1) if s['status'] is None else s['text'])
    for r in s['bestallda']:
        print('  ' + r)
    return 0


if __name__ == '__main__':
    sys.exit(main())
