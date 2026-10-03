#!/usr/bin/env python3
"""slugvakt.py — binder skrivande verktyg till körningens eget bygge (revisionen 2026-10-03, F1: en körning kunde
köra ta_bort.py eller prova.py med en annan kunds slug, eller skriva med --ut i en annan kunds katalog).

När NWP_SLUG är satt (kor.sh sätter den för bygget och stoppvakten) får ett verktyg bara ta den sluggen som argument
och bara skriva under kunder/<slug>/, underlag/<slug>/ eller körningens eget temporära område <tmp>/nwp-bygge-<slug>/;
en utkatalog med en symlänk som leder ut därifrån vägras också. Utan NWP_SLUG (dashboarden,
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


HOPPA = {'node_modules', '.git', '.astro'}
MAX_POSTER = 20000


def tmp_omrade(slug):
    """Körningens eget temporära område: <tmp>/nwp-bygge-<slug>/. Hela tmp tilläts förut, vilket nådde andra granskares
    arbetskataloger under /tmp/nwp-granskning (omgång fyra, F1); prefixet bygge- skiljer det från granskarnas rot också
    när en slug råkar heta granskning (omgång fem)."""
    return [Path('/tmp') / ('nwp-bygge-' + slug), Path(tempfile.gettempdir()) / ('nwp-bygge-' + slug)]


def tmp_katalog(prefix='nwp-'):
    """En temporär katalog som vakten tillåter: under körningens eget område när NWP_SLUG är satt, annars systemets.
    Verktyg som startar barnprocesser (upptagna_val → stil.mjs) måste använda den (omgång fem, F30)."""
    e = egen_slug()
    if e:
        rot = tmp_omrade(e)[0]
        rot.mkdir(parents=True, exist_ok=True)
        return tempfile.mkdtemp(prefix=prefix, dir=str(rot))
    return tempfile.mkdtemp(prefix=prefix)


def symlank_ut(katalog, rotar):
    """Första symlänk under katalogen vars mål ligger utanför de tillåtna rötterna, annars None. Ett verktyg skriver filer
    under sin utkatalog; en planterad länk där skulle annars leda skrivningen till ett annat bygge (omgång fem, F1)."""
    sedda = 0
    for mapp, mappar, filer in os.walk(katalog, followlinks=False):
        mappar[:] = [m for m in mappar if m not in HOPPA]
        for namn in mappar + filer:
            sedda += 1
            if sedda > MAX_POSTER:
                return None
            v = Path(mapp) / namn
            if v.is_symlink():
                mal = v.resolve()
                if not any(mal == r or mal.is_relative_to(r) for r in rotar):
                    return v
    return None


def tillaten_vag(p, slug):
    r = Path(p).resolve()  # följer symlänkar i de delar som finns; målet prövas, inte namnet
    rotar = [t.resolve() for t in [ROOT / 'kunder' / slug, ROOT / 'underlag' / slug] + tmp_omrade(slug)]
    if not any(r == t or r.is_relative_to(t) for t in rotar):
        return False
    if r.is_dir():  # en planterad symlänk under utkatalogen får inte leda skrivningen ut
        return symlank_ut(r, rotar) is None
    return True


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
        print('slugvakten: %s %s ligger inte i kunder/%s/, underlag/%s/ eller /tmp/nwp-bygge-%s/ (NWP_SLUG), eller innehåller en symlänk '
              'som leder ut därifrån; vägrar' % (vad, p, e, e, e), file=sys.stderr)
        sys.exit(2)
