#!/usr/bin/env python3
"""upptagna_val.py — vilka val tidigare byggen redan har gjort (typsnitt, färger, toppsektion) och vilka standardval
modellen själv faller tillbaka på, så att nästa bygge väljer med skäl i stället för av vana. Byggaren ser valen, inte
sajterna.

    .venv/bin/python kontroller/upptagna_val.py <slug>

Skriver underlag/<slug>/UPPTAGNA-VAL.md (privat, utanför git). Läser kunder/<annat>/prov/stil/STIL.json och mäter med
kontroller/stil.mjs de byggen som saknar en. Källa för standardvalen: Anthropic, Prompting Claude Opus 5.5, Frontend
design defaults ("a general instruction such as 'avoid a generic AI look' mostly swaps one default for another …
check which styles the first result used instead, and extend the list").
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova  # noqa: E402

ROOT = prova.ROOT
KUNDER = ROOT / 'kunder'
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
MODELLENS_STANDARDVAL = [
    'cream- eller off-white-bakgrund (nära #F4F1EA) med kontrastrik serif och terrakotta-accent',
    'nära svart bakgrund med en enda stark accent (syragrön, vermiljon eller gul)',
    'kursiva eller färgade accentord i rubriker',
    'numrerade etiketter 01/02/03',
    'monospace-etiketter',
    'pillerformade knappar',
    'spärrade versaletiketter över varje rubrik',
    'tidningslayout med hårlinjer och noll radie',
    'likadana rundade kort med samma mjuka skugga',
    'rubrik i fyra rader till vänster med ett block till höger och en ringknapp under',
]


STRUKTURMONSTER = [  # ägarens mall-lukt i domarna L1–L3 (LARDOMAR.md)
    'tjänstelista i två spalter med rubrik och en mening per tjänst (L1, L3)',
    'sidfot i tre spalter (L1)',
    'undersidor byggda av samma block om och om igen: rubrik till vänster, text till höger (L2)',
    'omdömeslista med hårlinjer mellan citaten (L2)',
]


def stil_for(bygge):
    """STIL.json för ett tidigare bygge: provets om den finns, annars mätt nu i en tillfällig katalog."""
    f = bygge / 'prov' / 'stil' / 'STIL.json'
    if f.is_file():
        return json.loads(f.read_text(encoding='utf-8'))
    dist = bygge / 'sajt' / 'dist'
    if not (dist / 'index.html').is_file():
        return None
    with tempfile.TemporaryDirectory() as tmp, prova.Server(dist) as srv:
        p = subprocess.run([prova.NODE, str(ROOT / 'kontroller' / 'stil.mjs'), '--url=' + srv.url,
                            '--sidor=' + ','.join(prova.sidor_i(dist)[:4]), '--ut=' + tmp], capture_output=True, text=True, timeout=300)
        try:
            return json.loads((Path(tmp) / 'STIL.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            print('kunde inte mäta %s: %s' % (bygge.name, p.stderr[-200:]), file=sys.stderr)
            return None


def rad(namn, s):
    sm = s.get('sammanfattning', {})
    topp = {t['vy']: t for t in s.get('toppsektion', [])}
    h1 = (topp.get('1440') or {}).get('h1') or {}
    return '| %s | %s | %s | %s (%s) | %s | %s |' % (
        namn, ', '.join(sm.get('rubriktypsnitt') or []) or '-',
        ', '.join(t for t in sm.get('typsnitt') or [] if t not in (sm.get('rubriktypsnitt') or [])) or 'samma',
        ', '.join(sm.get('bakgrund') or []), ', '.join(sm.get('familjer', {}).get('bakgrund') or []),
        ', '.join(sm.get('accent') or []) or '-',
        ('h1 %s, vikt %s, bredd %s' % (h1.get('storlek', '?'), h1.get('vikt', '?'), h1.get('stil', '?'))) if h1 else '-')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or not SLUG.match(argv[0]):
        print(__doc__.split('\n\n')[1].strip())
        return 2
    slug = argv[0]
    syskon = (KUNDER / slug / 'AB-SYSKON').read_text().strip() if (KUNDER / slug / 'AB-SYSKON').is_file() else None
    andra = sorted(p for p in KUNDER.iterdir() if p.is_dir() and SLUG.match(p.name) and p.name not in (slug, syskon, 'ab')
                   and not p.name.startswith('rokprov'))
    rader, varningar = [], {}
    for b in andra:
        s = stil_for(b)
        if not s:
            continue
        rader.append(rad(b.name, s))
        for v in s.get('varningar', []):
            varningar.setdefault(v, []).append(b.name)
    ut = ROOT / 'underlag' / slug / 'UPPTAGNA-VAL.md'
    ut.parent.mkdir(parents=True, exist_ok=True)
    md = ['# Upptagna val', '',
          'Det här har tidigare byggen redan valt, och det här faller modellen tillbaka på när ingen riktning ges. Du ser',
          'valen, inte sajterna. Ett upptaget val är tillåtet när verksamhetens eget material motiverar det (ägaren',
          'godtog Archivo för målaren i dom L2); välj det aldrig av vana. Skriv i KONCEPT.md, för varje val härifrån som du',
          'ändå gör, varför just den här verksamheten.', '',
          '## Tidigare byggen', '',
          '| Bygge | Rubriktypsnitt | Brödtext | Bakgrund | Accent | Toppsektion |', '|---|---|---|---|---|---|',
          *(rader or ['| inga tidigare byggen | | | | | |']), '',
          '## Varningar som återkommer i tidigare byggen', '',
          *(['- %s (%s)' % (v, ', '.join(b)) for v, b in sorted(varningar.items(), key=lambda x: -len(x[1]))] or ['Inga.']), '',
          '## Strukturmönster som gått igen', '',
          'Ägaren pekade ut dem som mall i domarna. Använd ett av dem bara med skäl ur verksamhetens material, och skriv',
          'skälet i KONCEPT.md.', '',
          *['- ' + m for m in STRUKTURMONSTER], '',
          '## Modellens egna standardval', '',
          'Anthropic om Opus 5.5: ett allmänt förbud mot AI-stil byter mest en standard mot en annan; namngivna mönster',
          'fungerar. Listan byggs ut när stilrapporten visar ett nytt mönster som går igen.', '',
          *['- ' + v for v in MODELLENS_STANDARDVAL], '']
    ut.write_text('\n'.join(md), encoding='utf-8')
    print('skrev %s (%d tidigare byggen)' % (ut.relative_to(ROOT), len(rader)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
