#!/usr/bin/env python3
"""Arbetsytans testprojekt: en fiktiv verksamhet (märkt testdata) med en ateljékörning i kandidatflödet, två kandidater, en
bevarad version och en arbetsversion som skiljer sig från den, och en riktig byggd sajt ur mallens Astro-projekt.

    .venv/bin/python -B kontroller/rokprov/revision/arbetsyta_fixtur.py <rot> [--slug testdata-provverkstaden] [--sajt <mallens sajt>]

Rot är en isolerad katalog (provets tempkatalog eller en worktrees egna underlag/ och kunder/), aldrig huvudutcheckningen.
Sajten kopieras ur en redan byggd mallsajt (kunder/rokprov-mall/sajt i huvudutcheckningen, byggd av rökprovet): källan,
dist/ och en länk till dess node_modules, så att en session kan bygga om den på riktigt. Inget här kör en modell.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

SLUG = 'testdata-provverkstaden'
MALLSAJT = Path.home() / 'nortropic-repos' / 'nortropic-webb-pro' / 'kunder' / 'rokprov-mall' / 'sajt'
STARTAD = '2026-10-09T05:00:00Z'
PLAN = '2026-10-09T05:05:00Z'


def skriv(p, x):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=1) + '\n' if not isinstance(x, str) else x, encoding='utf-8')


def bygg(rot, slug=SLUG, mallsajt=MALLSAJT, med_sajt=True):
    rot = Path(rot)
    u, k = rot / 'underlag' / slug, rot / 'kunder' / slug
    if u.exists() or k.exists():
        raise SystemExit('finns redan: %s (ta bort testprojektet först)' % u)
    skriv(u / 'VERKSAMHET.json', {'schema': 1, 'namn': 'Provverkstaden (testdata)', 'fiktiv': True, 'kontaktvagar': [],
                                  'rackvidd': {'typ': 'lokal', 'ort': 'Testby'}, 'tjanster': ['Reparationer (testdata)']})
    skriv(u / 'UPPDRAG.md', '# Uppdrag (testdata)\n\nFiktiv verksamhet för arbetsytans prov. Inga riktiga kunduppgifter.\n')
    skriv(u / 'BRIEF.md', '# Brief (testdata)\n\nToppuppgift: boka en reparation. Primär handling: ring verkstaden.\n')
    skriv(u / 'RESEARCH.md', '# Research (testdata)\n\nBara de har: en påhittad verkstad i Testby, för prov.\n')
    skriv(u / 'TEXTUNDERLAG.md', '# Textunderlag (testdata)\n\nRubrik: Reparationer i Testby.\n')
    skriv(u / 'atelje' / 'STATUS.json', {'slug': slug, 'kandidatflode': True, 'lage': 'ny', 'pid': None, 'startad': STARTAD,
                                         'steg': 'klar_for_bedomning', 'modell': 'claude-fable-5-1', 'effort': 'max',
                                         'tider': {'plan': PLAN, 'skiss': '2026-10-09T05:30:00Z'}, 'start_id': 'testdata-start-0001'})
    skriv(u / 'atelje' / 'KANDIDATPLAN.json', {'tid': PLAN, 'lage': 'skiss', 'antal': 2,
                                               'kandidater': {'k01': {'titel': 'Testdata: verkstaden i arbete'}, 'k02': {'titel': 'Testdata: lugn lista'}}})
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import kandidater
    for kid, status in (('k01', 'klar'), ('k02', 'klar')):
        d = u / 'atelje' / 'kandidater' / kid
        skriv(d / 'STATUS.json', {'id': kid, 'status': status, 'skal': 'testdata', 'tid': '2026-10-09T05:30:00Z', 'titel': 'Testdata %s' % kid,
                                  'logg': [{'tid': '2026-10-09T05:30:00Z', 'status': status, 'skal': 'testdata'}]})
        # riktningen med huvudreferensraden, som motorn kräver av en förfinad version (kandidater.riktningens_referens)
        (d / 'RIKTNING.md').write_text('# Riktning (testdata)\n\nHuvudreferens: egen — en enkel testriktning utan extern referens, '
                                       'för provets fiktiva material.\n', encoding='utf-8')
    if med_sajt:
        sajt = k / 'kandidater' / 'k01' / 'sajt'
        sajt.mkdir(parents=True)
        for namn in ('src', 'public', 'dist'):
            shutil.copytree(mallsajt / namn, sajt / namn, symlinks=False)
        for namn in ('package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json', 'DESIGN.md'):
            if (mallsajt / namn).is_file():
                shutil.copyfile(mallsajt / namn, sajt / namn)
        if (sajt / 'DESIGN.md').is_file():  # designens huvudreferens som riktningens (egen), som designkontrollen kräver före ett godkännande
            import json as _json
            import re as _re
            t = (sajt / 'DESIGN.md').read_text(encoding='utf-8')
            m = _re.search(r'```json design\n(.*?)\n```', t, _re.S)
            if m:
                v_ = _json.loads(m.group(1))
                v_['huvudreferens'] = 'egen'
                (sajt / 'DESIGN.md').write_text(t[:m.start(1)] + _json.dumps(v_, ensure_ascii=False, indent=1) + t[m.end(1):], encoding='utf-8')
        if (mallsajt / 'node_modules').is_dir():
            # kundens delade beroenden (processgränsen kräver att kandidatens länk pekar dit): en APFS-klon av mallens, så att
            # byggets cacher aldrig skrivs i huvudutcheckningen
            delad = k / 'sajt' / 'node_modules'
            delad.parent.mkdir(parents=True, exist_ok=True)
            import subprocess
            subprocess.run(['cp', '-Rc', str(mallsajt / 'node_modules'), str(delad)], check=True)
            os.symlink(delad, sajt / 'node_modules')
        # den bevarade versionen: kandidatens kod som den var vid fotograferingen
        d = u / 'atelje' / 'kandidater' / 'k01'
        _kopiera_kod(sajt, d, kandidater)
        v = kandidater.version_av(d)
        bevarad = d / 'versioner' / v[:12]
        for n in ('kod', kandidater.KODSRC):
            if (d / n).is_dir():
                shutil.copytree(d / n, bevarad / n)
        if (d / 'DESIGN.md').is_file():
            shutil.copyfile(d / 'DESIGN.md', bevarad / 'DESIGN.md')
        (bevarad / 'VERSION').write_text(v + '\n', encoding='utf-8')
        st = json.loads((d / 'STATUS.json').read_text(encoding='utf-8'))
        st.update(version=v, fotograferad='2026-10-09T05:30:00Z')
        skriv(d / 'STATUS.json', st)
        # arbetsversionen efter fotograferingen: en rad ändrad i startsidan, så att diffen mot den bevarade versionen har innehåll
        index = sajt / 'src' / 'pages' / 'index.astro'
        if index.is_file():
            index.write_text(index.read_text(encoding='utf-8') + '\n<!-- arbetsytans testdata: ändrad efter fotograferingen -->\n', encoding='utf-8')
    return u, k


def _kopiera_kod(sajt, d, kandidater):
    """kod/ ur sidorna utan mallens sidor och kod-src/ ur resten av src/ utan kundens bilder, som kandidater.projektets_version."""
    src = sajt / 'src'
    for p in sorted(src.rglob('*')):
        if not p.is_file() or p.is_symlink():
            continue
        r = p.relative_to(src)
        if r.parts[0] == 'pages':
            if r.parts[1] in kandidater.MALLSIDOR:
                continue
            mal = d / 'kod' / Path(*r.parts[1:])
        elif kandidater.src_ovrigt(r):
            mal = d / kandidater.KODSRC / r
        else:
            continue
        mal.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, mal)
    if (sajt / 'DESIGN.md').is_file():
        shutil.copyfile(sajt / 'DESIGN.md', d / 'DESIGN.md')


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('rot')
    a.add_argument('--slug', default=SLUG)
    a.add_argument('--sajt', default=str(MALLSAJT))
    x = a.parse_args()
    if Path(x.rot).resolve() == (Path.home() / 'nortropic-repos' / 'nortropic-webb-pro').resolve():
        raise SystemExit('testprojektet skapas aldrig i huvudutcheckningen')
    print(*bygg(x.rot, x.slug, Path(x.sajt)), sep='\n')
