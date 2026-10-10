#!/usr/bin/env python3
"""Sökkonsolens verifiering (katalogens k05-search-console): exporten skriver src/verifiering.json ur VERKSAMHET.json
(webb.sokkonsol_verifiering) bara för en verklig verksamhet och stoppar på ett värde med fel form; mallens Bas renderar
META-taggen när filen finns och ingen tagg annars (byggt med mallens Astro, som kräver kunder/rokprov-mall/sajt)."""
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exportera  # noqa: E402
import korregister  # noqa: E402
import processgrans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PAKET = ROOT / 'kunder' / 'rokprov-mall' / 'sajt' / 'node_modules'
MALL = ROOT / 'mall' / 'astro' / 'src'
TOKEN = 'AbCdEf0123456789_provtoken-XYZ'


class Exporten(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'sökkonsolens exportprov')).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / 'underlag' / 'prov').mkdir(parents=True)
        self.mal = self.tmp / 'export'

    def verksamhet(self, **v):
        (self.tmp / 'underlag' / 'prov' / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Prov', **v}))
        with patch.object(exportera, 'UNDERLAG', self.tmp / 'underlag'):
            return exportera.verifieringsfil('prov', self.mal)

    def test_bara_en_verklig_verksamhet_med_giltigt_varde(self):
        self.assertIsNone(self.verksamhet())
        self.assertFalse((self.mal / 'src' / 'verifiering.json').exists())
        self.assertIsNone(self.verksamhet(fiktiv=True, webb={'sokkonsol_verifiering': TOKEN}), 'en fiktiv verksamhet får ingen egenskap')
        self.assertEqual(self.verksamhet(webb={'sokkonsol_verifiering': TOKEN}), TOKEN)
        self.assertEqual(json.loads((self.mal / 'src' / 'verifiering.json').read_text()), {'google': TOKEN})
        for fel in ('"><script>', 'kort', 'x' * 101):
            with self.assertRaises(ValueError):
                self.verksamhet(webb={'sokkonsol_verifiering': fel})


@unittest.skipUnless((PAKET / '.bin' / 'astro').exists(), 'mallens paket saknas: kör rökprovet (kunder/rokprov-mall/sajt)')
class Taggen(unittest.TestCase):
    def test_taggen_med_och_utan_verifieringen(self):
        tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'sökkonsolens bygge')).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        ut = {}
        for namn, varde in (('med', {'google': TOKEN}), ('utan', None), ('fel', {'google': '"><script>x</script>'})):
            s = tmp / namn
            for rel in ('layouts/Bas.astro', 'styles/design.css'):
                (s / 'src' / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(MALL / rel, s / 'src' / rel)
            if varde:
                (s / 'src' / 'verifiering.json').write_text(json.dumps(varde))
            (s / 'src' / 'pages').mkdir(parents=True, exist_ok=True)
            (s / 'src' / 'pages' / 'index.astro').write_text("---\nimport Bas from '../layouts/Bas.astro';\n---\n"
                                                             '<Bas titel="Prov" beskrivning="Prov" tema="#123456"><main id="innehall"><p>x</p></main></Bas>\n')
            (s / 'package.json').write_text('{"type": "module", "private": true}')
            (s / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', site: 'https://exempel.invalid', vite: { cacheDir: './.vite-cache' } });\n")
            os.symlink(PAKET, s / 'node_modules')
            rc, logg = processgrans.kor_i_katalog(s, [s / 'node_modules' / '.bin' / 'astro', 'build'])
            self.assertEqual(rc, 0, logg[-800:])
            ut[namn] = (s / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<meta name="google-site-verification" content="%s">' % TOKEN, ut['med'])
        self.assertNotIn('google-site-verification', ut['utan'])
        self.assertNotIn('google-site-verification', ut['fel'], 'ett ogiltigt värde renderas aldrig')
        self.assertNotIn('<script>x', ut['fel'])


if __name__ == '__main__':
    unittest.main()
