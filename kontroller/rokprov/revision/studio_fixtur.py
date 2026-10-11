#!/usr/bin/env python3
"""Studioprovets testprojekt (designstudion 2026-10-11; kunskap/designstudio.md, Provkandidaten): arbetsytans fiktiva
verksamhet (arbetsyta_fixtur.py) där kandidat k01 bär den representativa Astro-kandidaten ur kontroller/rokprov/studio/:
en layout, sex komponenter med skopade stilar och tokens ur en designgrund, en bild genom astro:assets med fokuspunkt och
en mediaregel, en lista ur data, samma text i två komponenter, en komponent som används två gånger, en variant som
Props-union och en sektionsordning i sidans main. Bilderna skapas här (bild.mjs), inga binära filer ligger i repot.

    .venv/bin/python -B kontroller/rokprov/revision/studio_fixtur.py <rot> [--slug testdata-studio] [--sajt <mallens sajt>]

Rot är en isolerad katalog, aldrig huvudutcheckningen. Inget här kör en modell; kandidaten byggs och fotograferas först
när provet gör det (kandidater.fotografera med provets rötter).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arbetsyta_fixtur  # noqa: E402

SLUG = 'testdata-studio'
KANDIDAT = Path(__file__).resolve().parents[1] / 'studio' / 'kandidat'
BILD = Path(__file__).resolve().parents[1] / 'studio' / 'bild.mjs'
BILDER = (('verkstad.jpg', 1800, 1200, 196, 150, 98), ('detalj.jpg', 1200, 1500, 120, 140, 150))


def bygg(rot, slug=SLUG, mallsajt=arbetsyta_fixtur.MALLSAJT):
    """Arbetsytans testprojekt med provkandidaten i k01: (underlag, kunder). Kandidatens tidigare sidor och komponenter
    ur mallsajten ersätts; mallens egna sidor och komponenter (förfrågan med flera) står kvar."""
    u, k = arbetsyta_fixtur.bygg(rot, slug, mallsajt, med_sajt=True)
    sajt = k / 'kandidater' / 'k01' / 'sajt'
    for p in (sajt / 'src' / 'pages').iterdir():
        if p.name not in ('404.astro', 'tack.astro', 'fel.astro', 'mottagen.astro', 'robots.txt.ts', 'sitemap.xml.ts'):
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    for p in sorted(KANDIDAT.rglob('*')):
        if p.is_file():
            mal = sajt / p.relative_to(KANDIDAT)
            mal.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, mal)
    for f in ('DESIGN.md',):  # provkandidaten har sin designgrund i src/styles/design.css, utan DESIGN.md (som en skiss)
        if (sajt / f).exists():
            (sajt / f).unlink()
    assets = sajt / 'src' / 'assets' / 'atelje'
    assets.mkdir(parents=True, exist_ok=True)
    nm = (k / 'sajt' / 'node_modules').resolve()
    for namn, b, h, r, g, bl in BILDER:
        subprocess.run(['node', str(BILD), str(nm), str(assets / namn), str(b), str(h), str(r), str(g), str(bl)], check=True,
                       capture_output=True, text=True)
    shutil.rmtree(sajt / 'dist', ignore_errors=True)  # kandidaten byggs om av provet
    return u, k


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('rot')
    a.add_argument('--slug', default=SLUG)
    a.add_argument('--sajt', default=str(arbetsyta_fixtur.MALLSAJT))
    x = a.parse_args()
    if Path(x.rot).resolve() == (Path.home() / 'nortropic-repos' / 'nortropic-webb-pro').resolve():
        raise SystemExit('testprojektet skapas aldrig i huvudutcheckningen')
    print(*bygg(x.rot, x.slug, Path(x.sajt)), sep='\n')
