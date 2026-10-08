#!/usr/bin/env python3
"""styrning.py — vakten mot gammal styrning (ägarens uppdrag 2026-10-05 ~21:11Z, ordagrant i minnet: rensningen inför
Nortropic 2.0). Ersatta beslut och gamla kundsmakdomar får inte styra skapare, planerare, granskare eller kontroller, och
får inte komma tillbaka genom utdrag, ankare, mallar eller cache. Vakten läser det som når agenterna:

- instruktionerna: CLAUDE.md (laddas i varje nästlad session), kritik/GRANSKARE.md och varje skills SKILL.md;
- kunskapsfilerna i kunskap/ (metodens källor) utom historiken (BESLUT.md, LARDOMAR, registren);
- mallen (mall/astro: README och källfilernas kommentarer, som byggaren läser);
- metodens utdrag som de levereras till varje steg (kontroller/metod.py, leverera);
- med en kund: körningens cachade metod (underlag/<slug>/atelje/metod/METOD-*.md) och UPPTAGNA-VAL.md.

Ett citat som är märkt som ersatt ("Ersatt 2026-10-06: \"…\"") räknas inte: historiken bevaras där den står.

    .venv/bin/python kontroller/styrning.py [--slug S]

Slutkod 0 när inget hittas, 1 annars.
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
MONSTER = (
    (r'Ägarens domar i `?LARDOMAR\.md`?\s+gäller\s+före|ägarens domar i `?LARDOMAR\.md`?,?\s+gäller', 'LARDOMAR som regel som går före'),
    (r'exempel på vad ägaren värderar', 'ägarens domar över tidigare byggen som exempel att följa'),
    (r'\b(?:dom|domar|domarna)\s+L[1-6]\b|\(L[1-6](?:[,–-]\s*L?[1-6])*\)|\bLARDOMAR\s+L[1-6]\b', 'en enskild dom (L1–L6) som skäl för en regel'),
    (r'A/B[ -]2026-10-02|A/B-omdöme', 'A/B-omdömet 2026-10-02 som regel'),
    (r'Archivo för målaren|lulea-snickaren-abx|salongens bästa bild|abx gjorde rätt', 'ett gammalt bygge som förebild eller exempel'),
    (r'Astro, statisk, utan JavaScript|Bara CSS-recepten', 'ersatt teknikregel'),
    (r'tel-länk i sidhuvudet på varje sida|telefonnumret som tel-länk(?! när)', 'ersatt kontaktregel'),
    (r'Inga stockbilder eller genererade bilder|Använd inga andra bilder|Inga andra bilder', 'ersatt bildregel'),
    (r'gäller som hypotes för andra kunder', 'en kunds smak som hypotes för andra'),
)
HISTORIK = {'BESLUT.md', 'LARDOMAR.md', 'REGISTER.md', 'REGISTER-arkiv-20261001.md', 'KIRURG-OMDOMEN.md', 'LARDOMAR-digitala.md',
            'GRUPPERING.md', 'rensning-nortropic-2.md'}  # historiken, och rensningens egen förteckning över det ersatta
ERSATT = re.compile(r'Ersatt[^:\n]{0,60}:\s*"[^"\n]*"', re.I)
MALLTEXT = ('.md', '.astro', '.ts', '.mjs', '.js', '.css')


def fynd_i(text, kalla):
    ut = []
    for nr, rad in enumerate(ERSATT.sub(' ', text).splitlines(), 1):
        for m, vad in MONSTER:
            for traff in re.finditer(m, rad):
                ut.append({'kalla': kalla, 'rad': nr, 'vad': vad, 'text': rad.strip()[:160], 'traff': traff.group(0)})
    return ut


def kallfiler(root=None):
    root = Path(root or ROOT)
    filer = [root / 'CLAUDE.md', root / 'kritik' / 'GRANSKARE.md']
    filer += sorted((root / '.claude' / 'skills').glob('*/SKILL.md'))
    filer += sorted(p for p in (root / 'kunskap').glob('*.md') if p.name not in HISTORIK)
    mall = root / 'mall' / 'astro'
    filer += sorted(p for p in mall.rglob('*') if p.is_file() and p.suffix in MALLTEXT and 'node_modules' not in p.parts)
    return [f for f in filer if f.is_file()]


def metodens_utdrag():
    """Varje stegs levererade metod, som skaparen, planeraren och granskaren får den."""
    import metod
    ut = []
    with tempfile.TemporaryDirectory() as d:
        for steg in metod.STEG:
            try:
                res = metod.leverera(steg, Path(d) / steg)
            except Exception as e:  # noqa: BLE001 — en karta som inte levererar fälls av metodkontrollen
                ut.append({'kalla': 'metoden: %s' % steg, 'rad': 0, 'vad': 'kunde inte levereras', 'text': str(e)[:160], 'traff': ''})
                continue
            for f in res['filer']:
                ut += fynd_i(Path(f['fil']).read_text(encoding='utf-8'), 'metoden %s: %s' % (steg, Path(f['fil']).name))
    return ut


def prova(slug=None, root=None, med_metod=True):
    """Fynd: [{'kalla', 'rad', 'vad', 'text', 'traff'}]."""
    root = Path(root or ROOT)
    ut = []
    for f in kallfiler(root):
        ut += fynd_i(f.read_text(encoding='utf-8', errors='replace'), str(f.relative_to(root)))
    if med_metod:
        ut += metodens_utdrag()
    if slug:
        # körningens kopior: metoden levereras om vid varje start (kandidater.leverera_metod), och en äldre
        # UPPTAGNA-VAL.md läses aldrig av agenterna (atelje.underlag_rader); fynden där märks som cache och stoppar
        # ingen start (granskningen av r73, N1)
        import upptagna_val
        import urval
        u = root / 'underlag' / slug
        for f in sorted((u / 'atelje' / 'metod').glob('METOD-*.md')) + [u / 'UPPTAGNA-VAL.md']:
            if not f.is_file():
                continue
            text = f.read_text(encoding='utf-8', errors='replace')
            if f.name == 'UPPTAGNA-VAL.md':
                # den aktuella läses av agenterna som den står (granskningen av r74, L4), men bara när kundens aktiva urval
                # valt den (kontroller/urval.py; ren start 2026-10-08): annars läses den inte och fynden där stoppar inget
                if upptagna_val.VERSION in text and urval.aktivt(slug, 'upptagna_val', underlag=root / 'underlag'):
                    ut += fynd_i(text, str(f.relative_to(root)))
                continue
            ut += [dict(x, cache=True, vad=x['vad'] + ' (cache: körningens metodkopia, levereras om vid starten)') for x in fynd_i(text, str(f.relative_to(root)))]
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='styrning', description=__doc__.split('\n\n')[0])
    p.add_argument('--slug')
    a = p.parse_args(argv)
    fynd = prova(a.slug)
    for x in fynd:
        print('%s:%s %s: %s' % (x['kalla'], x['rad'], x['vad'], x['text']))
    print('%d fynd' % len(fynd))
    return 1 if fynd else 0


if __name__ == '__main__':
    sys.exit(main())
