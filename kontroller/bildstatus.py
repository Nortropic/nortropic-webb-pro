#!/usr/bin/env python3
"""bildstatus.py — leveransens visuella status ur beställningen: bildmaterialet komplett, visuellt begränsad av saknat
material, eller okänd (bevakningen 2026-10-03, Codex: systemet ska skilja en visuellt färdig sajt från ett förslag som
begränsas av saknat kundmaterial; backloggen B-20261003-bildernas-uppgift-och-leveransens-visuella-statu).

    .venv/bin/python kontroller/bildstatus.py <slug>

Kontraktet mellan den som skriver underlag/<slug>/BESTALLNING.md (bygg-sajt steg 3 och förberedelsen,
kontroller/forberedelse.py) och den som läser statusen (GR-20261009-natt-omgranskning-codex#N05): beställningen bär
ett uttryckligt besked på en egen rad, BESKED_KOMPLETT eller BESKED_SAKNAS, och varje bild som saknas som en rad i en
lista eller i en tabells kropp, under vilken rubrik som helst ("## Bilder", "## Hindrar design", "## Hindrar leverans" …).
- Visuellt begränsad av saknat material: beskedet saknas, eller det finns en rad om en saknad bild, också när beskedet
  säger komplett: en uttrycklig saknad bild går före beskedet. En rad om en saknad bild är varje rad under en rubrik om
  bilder ("## Bilder", "## Foton"), och under andra rubriker en rad som nämner en bild (huvudbild, bild, foto, porträtt,
  video, film).
- Bildmaterialet komplett: bara med beskedet komplett och ingen rad om en saknad bild.
- Okänd: ingen beställning, en länk, en fil som inte går att läsa, en tom fil, eller en beställning utan giltigt besked
  och utan rad om en saknad bild. Det som inte går att tolka blir aldrig komplett.
En rad som börjar med "Inga", "Ingen" eller "Inget" är ingen saknad bild. Samma besked står i RAPPORT.md (bygg-sajt
steg 7, punkt 13) och som chip i dashboarden (bygget). Statusen säger vad som saknas i materialet, inte hur bra sajten
är: ett komplett material är inget godkännande av formgivningen, och granskarens betyg sätts på sajten som den visas
(kritik/GRANSKARE.md, Saknat underlag). Exit 0.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
BEGRANSAD = 'visuellt begränsad av saknat material'
FARDIG = 'bildmaterialet komplett'
OKAND = 'bildmaterialets status okänd'
BESKED_KOMPLETT = 'Bildmaterial: komplett'
BESKED_SAKNAS = 'Bildmaterial: saknas'
INTE_FORMGIVNING = 'säger inget om formgivningen'
# beskedet på en egen rad, som listpunkt eller fetstil också; ett annat värde är ett ogiltigt besked
BESKED = re.compile(r'^\s*(?:[-*+]\s+)?(?:\*\*)?\s*Bildmaterial(?:et)?\s*(?:\*\*)?\s*:\s*(?:\*\*)?\s*([^\s*.,;]*)', re.I)
LISTRAD = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+(\S.*)$')
TABELLRAD = re.compile(r'^\s*\|.*\|\s*$')
AVSKILJARE = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$')
RUBRIK = re.compile(r'^#{1,6}\s')
BILDRUBRIK = re.compile(r'^#{1,6}\s+(?:bilder|bild|foton|foto|fotografier)\b', re.I)
BILDORD = re.compile(r'(?<![a-zåäö])(?:huvudbild|bild|foto|fotografi|porträtt|video|film)', re.I)
NEKAD = re.compile(r'^\W*(?:inga|ingen|inget)\b', re.I)


def rader_i(text):
    """[(rad, under en bildrubrik)] för varje rad i en lista eller i en tabells kropp (inte rubrikraden eller avskiljaren)."""
    rader = text.split('\n')
    ut, bildrubrik = [], False
    for n, r in enumerate(rader):
        if RUBRIK.match(r):
            bildrubrik = bool(BILDRUBRIK.match(r))
            continue
        if LISTRAD.match(r):
            ut.append((r.strip(), bildrubrik))
        elif TABELLRAD.match(r) and not AVSKILJARE.match(r):
            if n + 1 < len(rader) and AVSKILJARE.match(rader[n + 1]):
                continue  # tabellens rubrikrad
            ut.append((r.strip(), bildrubrik))
    return ut


def bestallda_bilder(text):
    """Raderna om en saknad bild: varje rad under en bildrubrik, och under andra rubriker en rad med ett bildord; aldrig
    beskedet eller en rad som säger att inga bilder behövs."""
    ut = []
    for r, bildrubrik in rader_i(text):
        innehall = LISTRAD.match(r).group(1) if LISTRAD.match(r) else r
        if BESKED.match(r) or NEKAD.match(innehall.strip('|').strip()):
            continue
        if bildrubrik or BILDORD.search(innehall):
            ut.append(r)
    return ut


def besked(text):
    """('komplett' | 'saknas' | 'ogiltigt' | None, raderna): beställningens uttryckliga besked. Två olika besked är ogiltigt."""
    varden = []
    for r in text.split('\n'):
        m = BESKED.match(r)
        if m:
            v = m.group(1).strip().casefold()
            varden.append(v if v in ('komplett', 'saknas') else 'ogiltigt')
    if not varden:
        return None
    return varden[0] if len(set(varden)) == 1 else 'ogiltigt'


def visuell_status(slug, underlag=None):
    """{'status': FARDIG, BEGRANSAD eller OKAND, 'text', 'kalla', 'bestallda', 'besked'} för kunden."""
    f = Path(underlag or UNDERLAG) / slug / 'BESTALLNING.md'
    kalla = 'underlag/%s/BESTALLNING.md' % slug

    def okand(skal, k=kalla):
        return {'status': OKAND, 'text': '%s: %s' % (OKAND, skal), 'kalla': k, 'bestallda': [], 'besked': None}
    try:
        if f.is_symlink():
            return okand('beställningen är en länk och läses inte')
        if not f.is_file():
            return okand('ingen beställning till verksamheten', None)
        text = f.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        return okand('beställningen går inte att läsa (%s)' % type(e).__name__)
    if not text.strip():
        return okand('beställningen är tom')
    best, b = bestallda_bilder(text), besked(text)
    if best:
        motsagelse = ' (beskedet "%s" motsägs av raderna)' % BESKED_KOMPLETT if b == 'komplett' else ''
        return {'status': BEGRANSAD, 'kalla': kalla, 'bestallda': best, 'besked': b,
                'text': '%s: %d bilder saknas enligt %s%s' % (BEGRANSAD, len(best), kalla, motsagelse)}
    if b == 'saknas':
        return {'status': BEGRANSAD, 'kalla': kalla, 'bestallda': [], 'besked': b,
                'text': '%s: beskedet "%s" i %s, utan rader om vilka bilder' % (BEGRANSAD, BESKED_SAKNAS, kalla)}
    if b == 'komplett':
        return {'status': FARDIG, 'kalla': kalla, 'bestallda': [], 'besked': b,
                'text': '%s: beskedet "%s" i %s och ingen saknad bild; %s' % (FARDIG, BESKED_KOMPLETT, kalla, INTE_FORMGIVNING)}
    return okand('%s saknar ett giltigt besked (%s eller %s) och nämner ingen saknad bild' % (
        kalla, BESKED_KOMPLETT, BESKED_SAKNAS) if b is None else '%s har ett ogiltigt besked om bildmaterialet' % kalla)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 1:
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        return 2
    s = visuell_status(a[0])
    print(s['text'])
    for r in s['bestallda']:
        print('  ' + r)
    return 0


if __name__ == '__main__':
    sys.exit(main())
