#!/usr/bin/env python3
"""slugvakt.py — binder skrivande verktyg till körningens eget bygge (revisionen 2026-10-03, F1: en körning kunde
köra ta_bort.py eller prova.py med en annan kunds slug, eller skriva med --ut i en annan kunds katalog).

När NWP_SLUG är satt (kor.sh sätter den för bygget och stoppvakten) får ett verktyg bara ta den sluggen som argument
och bara skriva under kunder/<slug>/, underlag/<slug>/ eller det temporära området. Utan NWP_SLUG (dashboarden,
kirurgen, ägaren i terminalen) gör vakten ingenting. Processisoleringen (backloggen) är den fullständiga gränsen; det
här är argumentkontrollen som kompletterar den.

    from slugvakt import krav_slug, krav_vag
    krav_slug(a.slug)            # avslutar med kod 2 när sluggen inte är körningens
    krav_vag(a.ut, 'utkatalogen')  # avslutar med kod 2 när sökvägen ligger utanför det egna bygget
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def egen_slug():
    return os.environ.get('NWP_SLUG') or None


def tillaten_vag(p, slug):
    r = Path(p).resolve()
    rotar = [ROOT / 'kunder' / slug, ROOT / 'underlag' / slug, Path('/tmp'), Path('/private/tmp'), Path(tempfile.gettempdir())]
    return any(r == t.resolve() or r.is_relative_to(t.resolve()) for t in rotar if t.exists() or str(t).startswith('/'))


def krav_slug(slug, vad='slug'):
    e = egen_slug()
    if e and slug != e:
        print('slugvakten: %s %r är inte körningens bygge (NWP_SLUG=%s); vägrar' % (vad, slug, e), file=sys.stderr)
        sys.exit(2)


def krav_vag(p, vad='utkatalogen'):
    e = egen_slug()
    if not p or not e:
        return
    if not tillaten_vag(p, e):
        print('slugvakten: %s %s ligger inte i kunder/%s/, underlag/%s/ eller det temporära området (NWP_SLUG); vägrar' % (vad, p, e, e), file=sys.stderr)
        sys.exit(2)
