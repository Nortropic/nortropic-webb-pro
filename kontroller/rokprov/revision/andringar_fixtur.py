#!/usr/bin/env python3
"""Ändringsflikens provprojekt (kunskap/andringar.md, Proven): två fiktiva webbplatser med var sin arbetskopia av
kundrepot (ett riktigt git-repo med en exportcommit och kvittot KUNDREPO.json), verksamhetens underlag och ägarens
designbeslut, i en isolerad rot. med_sajt: arbetskopian bär rökprovets mallsajt (src, public, astro-konfigurationen,
paketfilerna och mallens node_modules som länk), så att provvägen kan bygga och fotografera den på riktigt.

    .venv/bin/python -B kontroller/rokprov/revision/andringar_fixtur.py <rot> [--med-sajt]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MALLSAJT = ROOT / 'kunder' / 'rokprov-mall' / 'sajt'
WEBBPLATSER = (('testdata-andring', 'Snickeriet Provbygget (testdata)'), ('testdata-andring-tva', 'Provfirman Två (testdata)'))
GIT = ['git', '-c', 'user.name=Nortropic', '-c', 'user.email=noreply@nortropic.se']

INDEX = """---
import Bas from '../layouts/Bas.astro';
---
<Bas titel="%s">
  <main>
    <h1>Snickeri som håller</h1>
    <p class="ingress">Vi bygger kök, trappor och fönster i Provby.</p>
    <section aria-labelledby="oppet"><h2 id="oppet">Öppettider</h2><p>Vardagar 07–17</p></section>
  </main>
</Bas>
"""


def git(rot, *args):
    return subprocess.run([*GIT, *args], cwd=str(rot), capture_output=True, text=True, check=True).stdout.strip()


def bygg(rot, med_sajt=False):
    """Skapar provprojektet under rot: ger {slug: arbetskopia}."""
    rot = Path(rot)
    if rot.resolve() == ROOT.resolve():
        raise SystemExit('provprojektet skapas aldrig i repots rot')
    ut = {}
    for slug, namn in WEBBPLATSER:
        u = rot / 'underlag' / slug
        u.mkdir(parents=True, exist_ok=True)
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': namn, 'fiktiv': True, 'ort': 'Provby', 'tjanster': ['kök', 'trappor', 'fönster'],
                                                        'oppettider': 'vardagar 07–17'}, ensure_ascii=False), encoding='utf-8')
        (u / 'DESIGNDOMAR.jsonl').write_text(json.dumps({'tid': '2026-10-01T10:00:00Z', 'kalla': 'ägaren', 'beslut': 'godkand',
                                                          'text': 'Behåll den lugna typografin och det mörka sidhuvudet.'}, ensure_ascii=False) + '\n', encoding='utf-8')
        r = rot / 'kunder' / slug / 'kundrepo'
        r.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main'], cwd=str(r), check=True)
        if med_sajt and slug == WEBBPLATSER[0][0]:
            for namn_ in ('src', 'public'):
                shutil.copytree(MALLSAJT / namn_, r / namn_, symlinks=True)
            for namn_ in ('astro.config.mjs', 'package.json', 'package-lock.json', 'tsconfig.json'):
                if (MALLSAJT / namn_).is_file():
                    shutil.copyfile(MALLSAJT / namn_, r / namn_)
            # en egen node_modules med en länk per paket till mallens: npm kan bara ta bort länkarna, aldrig mallens filer, och
            # stämpeln (låsfilen) säger provvägen att inget behöver installeras. Byggets cachar (.vite, .astro) länkas inte:
            # bygget skriver i dem, och sandlådan nekar skrivningar genom en länk ut ur arbetskopian
            nm, mall_nm = r / 'node_modules', Path(os.path.realpath(MALLSAJT / 'node_modules'))
            nm.mkdir()
            for e in sorted(mall_nm.iterdir()):
                if not e.name.startswith('.') or e.name in ('.bin', '.package-lock.json'):
                    os.symlink(e, nm / e.name)
            (nm / '.nwp-las.json').write_bytes((r / 'package-lock.json').read_bytes())
        else:
            (r / 'src' / 'pages').mkdir(parents=True, exist_ok=True)
            (r / 'src' / 'pages' / 'index.astro').write_text(INDEX % namn, encoding='utf-8')
        # node_modules utan snedstreck: med sajten är det en länk till mallens, och en länk matchar inte ett katalogmönster
        (r / '.gitignore').write_text('node_modules\ndist/\n.astro/\n', encoding='utf-8')
        (r / 'CLAUDE.md').write_text('# kund-%s\n\nProvprojektets instruktioner: `npm run build` bygger dist/. DESIGN.md beskriver designen.\n' % slug, encoding='utf-8')
        (r / 'DESIGN.md').write_text('# Designen\n\nLugn typografi, mörkt sidhuvud, öppettiderna synliga på startsidan.\n', encoding='utf-8')
        # sajten som exporten kom ifrån: samma källor som repot (src, DESIGN.md), så att intaget och exportens skydd kan prövas
        sajt = rot / 'kunder' / slug / 'sajt'
        shutil.copytree(r / 'src', sajt / 'src', symlinks=True)
        shutil.copyfile(r / 'DESIGN.md', sajt / 'DESIGN.md')
        (sajt / 'package.json').write_text('{"name": "sajt", "private": true}\n', encoding='utf-8')
        git(r, 'add', '-A')
        git(r, 'commit', '-q', '-m', 'Export 000000000001-prov\n\nLeverans från Nortropic (provprojektet).')
        sha = git(r, 'rev-parse', 'HEAD')
        sys.path.insert(0, str(ROOT / 'kontroller'))
        import exportera
        import skapande
        e = rot / 'kunder' / slug / 'exporter' / '000000000001-prov'
        e.mkdir(parents=True, exist_ok=True)
        (e / 'EXPORT.json').write_text(json.dumps({'schema': 1, 'id': 'EXPORT-000000000001-prov', 'typ': 'exportkvitto', 'slug': slug, 'ok': True,
                                                   'commit': sha, 'ut': str(r), 'kallor_sha256': skapande.kallversion(sajt),
                                                   'export_sha256': exportera.manifest_sha(exportera.exportmanifest(r)), 'tillstand': {}},
                                                  ensure_ascii=False), encoding='utf-8')
        (rot / 'kunder' / slug / 'KUNDREPO.json').write_text(json.dumps({'schema': 1, 'slug': slug, 'projekt_id': 'prov-' + slug, 'fjarr': {'status': 'fiktiv'},
                                                                        'commit': sha, 'senaste_export': {'id': '000000000001-prov', 'commit': sha}},
                                                                       ensure_ascii=False), encoding='utf-8')
        ut[slug] = r
    return ut


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('rot')
    a.add_argument('--med-sajt', action='store_true')
    x = a.parse_args()
    for slug, r in bygg(x.rot, x.med_sajt).items():
        print(slug, r)
