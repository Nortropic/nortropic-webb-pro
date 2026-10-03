#!/usr/bin/env python3
"""slugvakt.py — binder skrivande verktyg till körningens eget bygge (revisionen 2026-10-03, F1: en körning kunde
köra ta_bort.py eller prova.py med en annan kunds slug, eller skriva med --ut i en annan kunds katalog).

När NWP_SLUG är satt (kor.sh sätter den för bygget och stoppvakten) får ett verktyg bara ta den sluggen som argument
och bara skriva under kunder/<slug>/, underlag/<slug>/ eller körningens eget temporära område <tmp>/nwp-bygge-<slug>/;
en utkatalog med en symlänk som leder ut därifrån vägras också. Utan NWP_SLUG (dashboarden,
kirurgen, ägaren i terminalen) gör vakten ingenting. Processisoleringen (backloggen) är den fullständiga gränsen; det
här är argumentkontrollen som kompletterar den.

    from slugvakt import krav_slug, krav_vag, inte_i_bygge
    krav_slug(a.slug)            # avslutar med kod 2 när sluggen inte är körningens
    krav_vag(a.ut, 'utkatalogen')  # avslutar med kod 2 när sökvägen ligger utanför det egna bygget, eller när
                                 # genomgången av den inte gick att göra färdigt (ofullständig = inte godkänd)
    inte_i_bygge('prospekt.py')  # administrativa verktyg vägrar helt när NWP_SLUG är satt
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def egen_slug():
    return os.environ.get('NWP_SLUG') or None


MAX_POSTER = 20000  # en genomgång som inte hinner klart räknas som misslyckad, aldrig som ren (omgång sex, F1)


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
    """Vad en genomgång av katalogen ger: ('ren', None), ('ut', symlänken) för första symlänk vars mål ligger utanför de
    tillåtna rötterna, ('ofullständig', None) när taket nås, eller ('fel', sökväg) när något inte gick att läsa. Varje
    post prövas som symlänk innan något undantas; inget hoppas över (omgång sex, F1). Ett verktyg skriver filer under sin
    utkatalog; en planterad länk där skulle annars leda skrivningen till ett annat bygge."""
    sedda, fel = 0, []
    besokta, ko = {os.path.realpath(katalog)}, [Path(katalog)]

    def onerror(e):
        fel.append(getattr(e, 'filename', None) or str(e))

    while ko:  # en kataloglänk till en tillåten katalog följs också: den kan i sin tur länka ut (omgång tolv, F1)
        start = ko.pop()
        for mapp, mappar, filer in os.walk(start, followlinks=False, onerror=onerror):
            if fel:
                return 'fel', fel[0]
            for namn in mappar + filer:
                sedda += 1
                if sedda > MAX_POSTER:
                    return 'ofullständig', None
                v = Path(mapp) / namn
                if v.is_symlink():
                    mal = Path(os.path.realpath(v))  # också en länk vars mål inte finns än
                    if not any(mal == r or mal.is_relative_to(r) for r in rotar):
                        return 'ut', v
                    if mal.is_dir() and str(mal) not in besokta:
                        besokta.add(str(mal))
                        ko.append(mal)
    return ('fel', fel[0]) if fel else ('ren', None)


def forankrad(slug):
    """De tillåtna rötterna, bara när ingen av dem eller deras föräldrar själv är en symlänk: kunder/eget → kunder/annat
    skulle annars göra den andra kundens katalog betrodd (omgång sex, F1). None när förankringen inte håller."""
    kedjor = [[ROOT / 'kunder', ROOT / 'kunder' / slug], [ROOT / 'underlag', ROOT / 'underlag' / slug]]
    rotar = []
    for kedja in kedjor:
        for led in kedja:
            if led.is_symlink():
                return None
        rotar.append(kedja[-1].resolve())
    for t in tmp_omrade(slug):
        if t.is_symlink():  # själva området; föräldern är systemets tmp (en symlänk på macOS) och betrodd
            return None
        rotar.append(Path(os.path.realpath(t)))
    return rotar


def tillaten_vag(p, slug):
    rotar = forankrad(slug)
    if rotar is None:
        return False
    r = Path(os.path.realpath(p))  # följer symlänkar i hela kedjan, också en länk vars mål inte finns än
    if not any(r == t or r.is_relative_to(t) for t in rotar):
        return False
    if r.is_dir():  # en planterad symlänk under utkatalogen får inte leda skrivningen ut
        return symlank_ut(r, rotar)[0] == 'ren'
    return True


def inte_i_bygge(verktyg):
    """Administrativa verktyg (prospekt, utskick, A/B, spaning …) körs aldrig inne i ett bygge (omgång sex, F1)."""
    e = egen_slug()
    if e:
        print('slugvakten: %s körs inte inne i ett bygge (NWP_SLUG=%s); vägrar' % (verktyg, e), file=sys.stderr)
        sys.exit(2)


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
