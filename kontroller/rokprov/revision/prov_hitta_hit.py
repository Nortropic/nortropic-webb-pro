#!/usr/bin/env python3
"""Mallens Hitta hit (mall/astro/src/components/HittaHit.astro, katalogens k06-hitta-hit) byggd med mallens Astro:
adressen som text, en länk till vägbeskrivningen med adressen kodad, och inget skript, ingen iframe och ingen
förhandshämtning hos kartleverantören. Kräver mallens installerade paket (rökprovets sajt, kunder/rokprov-mall/sajt)."""
import os
from pathlib import Path
import re
import shutil
import sys
import unittest
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402
import processgrans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PAKET = ROOT / 'kunder' / 'rokprov-mall' / 'sajt' / 'node_modules'


@unittest.skipUnless((PAKET / '.bin' / 'astro').exists(), 'mallens paket saknas: kör rökprovet (kunder/rokprov-mall/sajt)')
class HittaHit(unittest.TestCase):
    def test_adress_och_lank_utan_skript_eller_forhandshamtning(self):
        tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'Hitta hit-komponentens bygge')).resolve()
        try:
            s = tmp / 'sajt'
            (s / 'src' / 'pages').mkdir(parents=True); (s / 'src' / 'components').mkdir()
            shutil.copyfile(ROOT / 'mall' / 'astro' / 'src' / 'components' / 'HittaHit.astro', s / 'src' / 'components' / 'HittaHit.astro')
            (s / 'package.json').write_text('{"type": "module", "private": true}')
            (s / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', site: 'https://exempel.invalid', vite: { cacheDir: './.vite-cache' } });\n")
            (s / 'src' / 'pages' / 'index.astro').write_text(
                "---\nimport HittaHit from '../components/HittaHit.astro';\n---\n<html lang=\"sv\"><head><title>Prov</title></head><body><main>"
                "<HittaHit namn=\"Provfirman & Co\" gata=\"Storgatan 1\" postnummer=\"123 45\" ort=\"Åre\" /></main></body></html>\n")
            os.symlink(PAKET, s / 'node_modules')  # mallens paket; Vites cache i provsajten (vite.cacheDir), aldrig i mallen
            rc, logg = processgrans.kor_i_katalog(s, [s / 'node_modules' / '.bin' / 'astro', 'build'])
            self.assertEqual(rc, 0, logg[-800:])
            html = (s / 'dist' / 'index.html').read_text(encoding='utf-8')
            self.assertIn('<address', html); self.assertIn('Storgatan 1', html); self.assertIn('123 45 Åre', html)
            href = re.search(r'href="(https://www\.google\.com/maps/dir/[^"]+)"', html)
            self.assertIsNotNone(href, html[:500])
            self.assertEqual(href.group(1).replace('&amp;', '&'),
                             'https://www.google.com/maps/dir/?api=1&destination=' + quote('Provfirman & Co, Storgatan 1, 123 45 Åre', safe="-_.!~*'()"))
            for forbjudet in ('<script', '<iframe', 'rel="preconnect"', 'rel="prefetch"', 'rel="dns-prefetch"', 'maps.googleapis.com'):
                self.assertNotIn(forbjudet, html)
            self.assertIn('Visa vägbeskrivning', html)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
