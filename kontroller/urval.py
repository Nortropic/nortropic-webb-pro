#!/usr/bin/env python3
"""urval.py — det aktiva urvalet för en kunds körning (ren start för Nortropic 2.0; ägarens uppdrag 2026-10-08, del 2).

Historiken bevaras privat men styr inte automatiskt: andra kunders byggbilder i granskningen (granska.tidigare_byggen),
UPPTAGNA-VAL.md ur tidigare byggen (atelje.underlag_rader), planens förhandsläsning av RIKTNINGSHISTORIK.json
(kandidater.plan_prompt; R04) och äldre domar som generella regler är av tills de valts
uttryckligen här. Kundens aktuella fakta, uttryckliga beslut (designregler.md, kundens aktuella domar efter senaste
ny_riktning), kunskapen och skills, de verifierade tekniska lärdomarna och proven gäller oförändrat. Bra externa
referenser återväljs uttryckligen: det aktiva referenspaketet är det senaste (versionerna ärver), och urvalet skriver
vilket som gällde när körningen startade.

Filen: underlag/<slug>/atelje/URVAL.json (privat), skriven när en körning startar (kandidater.kor) och ändrad bara med
det här verktyget. En ny slug, en ny riktning eller flyttade filer är inte ett urval; filen är.

    .venv/bin/python kontroller/urval.py <slug> --visa
    .venv/bin/python kontroller/urval.py <slug> --tidigare-byggbilder pa|av --upptagna-val pa|av --riktningshistorik pa|av [--skal "<varför>"]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402

VAL = ('tidigare_byggbilder', 'upptagna_val', 'riktningshistorik')  # historik som bara ett uttryckligt urval kopplar in
STANDARD = {'tidigare_byggbilder': False, 'upptagna_val': False, 'riktningshistorik': False}


def fil(slug, underlag=None):
    return (Path(underlag) if underlag else atelje.UNDERLAG) / slug / 'atelje' / 'URVAL.json'


def las(slug, underlag=None):
    """Urvalet, med standardvärdena (historiken av) när filen saknas eller inte kan läsas."""
    f = fil(slug, underlag)
    try:
        d = json.loads(f.read_text(encoding='utf-8')) if f.is_file() and not f.is_symlink() else {}
    except (OSError, ValueError):
        d = {}
    d = d if isinstance(d, dict) else {}
    h = d.get('historik') if isinstance(d.get('historik'), dict) else {}
    d['historik'] = {k: bool(h.get(k, STANDARD[k])) for k in VAL}
    d.setdefault('schema', 1)
    return d


def aktivt(slug, val, underlag=None):
    """True när historiken val är uttryckligen vald för kunden."""
    if val not in VAL:
        raise ValueError('okänt val %s' % val)
    return bool(las(slug, underlag)['historik'].get(val))


def ankare_sha(underlag=None):
    """Kalibreringens aktiva ankare (ANKARE.txt) som hash, för urvalets kvitto."""
    f = Path(underlag or atelje.UNDERLAG) / 'kalibrering' / 'ANKARE.txt'
    return hashlib.sha256(f.read_bytes()).hexdigest()[:12] if f.is_file() else None


def skriv(slug, **val):
    d = las(slug)
    for k, v in val.items():
        if k in VAL and v is not None:
            d['historik'][k] = bool(v)
    d['uppdaterad'] = atelje.nu()
    fil(slug).parent.mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(fil(slug), d)
    return d


def vid_start(slug, korning=None):
    """Urvalet när en körning startar: skapas med standardvärdena om det saknas; det aktiva referenspaketet och ankarnas
    hash skrivs in som kvitto. Ett uttryckligt urval ändras aldrig här."""
    import skapande
    d = las(slug)
    ny = not fil(slug).is_file()
    paket = skapande.senaste_paket(slug, atelje.UNDERLAG)
    d.update(korning=korning or d.get('korning'), referenspaket=paket.name if paket else None, ankare=ankare_sha(), skriven=d.get('skriven') or atelje.nu())
    if ny:
        d['skal'] = 'standard vid körningens start: historiken av tills den väljs uttryckligen (ren start 2026-10-08)'
    fil(slug).parent.mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(fil(slug), d)
    return d


def main(argv=None):
    p = argparse.ArgumentParser(prog='urval', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--visa', action='store_true')
    p.add_argument('--tidigare-byggbilder', choices=('pa', 'av'))
    p.add_argument('--upptagna-val', choices=('pa', 'av'))
    p.add_argument('--riktningshistorik', choices=('pa', 'av'))
    p.add_argument('--skal', default='')
    a = p.parse_args(argv)
    if not atelje.SLUG.match(a.slug):
        print('ogiltig slug', file=sys.stderr)
        return 2
    if a.visa or (a.tidigare_byggbilder is None and a.upptagna_val is None and a.riktningshistorik is None):
        print(json.dumps(las(a.slug), ensure_ascii=False, indent=1))
        return 0
    d = skriv(a.slug, tidigare_byggbilder=None if a.tidigare_byggbilder is None else a.tidigare_byggbilder == 'pa',
              upptagna_val=None if a.upptagna_val is None else a.upptagna_val == 'pa',
              riktningshistorik=None if a.riktningshistorik is None else a.riktningshistorik == 'pa')
    if a.skal:
        d['skal'] = a.skal[:300]
        atelje.skriv_json_atomiskt(fil(a.slug), d)
    print(json.dumps(d, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
