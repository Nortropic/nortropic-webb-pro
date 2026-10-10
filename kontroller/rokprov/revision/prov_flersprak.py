#!/usr/bin/env python3
"""Flerspråkigheten i mallen (katalogens k18-flersprak: Bas.astro med sprak och alternativ, Sprakvaxlare.astro) byggd med
mallens Astro: sidans lang, hreflang för varje version och x-default till standardspråket som absoluta adresser,
og:locale och skiplänken på sidans språk, språkväxlaren med språkets eget namn, lang och aria-current; båda versionerna i
sitemap.xml; en sida utan språkval är oförändrad (svensk, inga alternate-länkar); en noindex-sida får inga
alternate-länkar; bygget faller på en ogiltig språkkod. Kräver mallens installerade paket (kunder/rokprov-mall/sajt)."""
import os
from pathlib import Path
import re
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402
import processgrans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PAKET = ROOT / 'kunder' / 'rokprov-mall' / 'sajt' / 'node_modules'
MALL = ROOT / 'mall' / 'astro' / 'src'
ALT = "[{ sprak: 'sv', href: '/' }, { sprak: 'en', href: '/en/' }]"
VAXLARE = "[{ sprak: 'sv', namn: 'Svenska', href: '/' }, { sprak: 'en', namn: 'English', href: '/en/' }]"


def sida(bas, extra, kropp):
    return ("---\nimport Bas from '%s/layouts/Bas.astro';\nimport Sprakvaxlare from '%s/components/Sprakvaxlare.astro';\n---\n"
            '<Bas titel="Prov" beskrivning="Prov" tema="#123456" %s><main id="innehall">%s</main></Bas>\n' % (bas, bas, extra, kropp))


@unittest.skipUnless((PAKET / '.bin' / 'astro').exists(), 'mallens paket saknas: kör rökprovet (kunder/rokprov-mall/sajt)')
class Flersprak(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'flerspråkighetens bygge')).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.n = 0

    def bygg(self, sidor):
        self.n += 1
        s = self.tmp / ('sajt%d' % self.n)
        for rel in ('layouts/Bas.astro', 'styles/design.css', 'components/Sprakvaxlare.astro', 'pages/sitemap.xml.ts'):
            (s / 'src' / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(MALL / rel, s / 'src' / rel)
        for rel, text in sidor.items():
            (s / 'src' / 'pages' / rel).parent.mkdir(parents=True, exist_ok=True)
            (s / 'src' / 'pages' / rel).write_text(text)
        (s / 'package.json').write_text('{"type": "module", "private": true}')
        (s / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', site: 'https://exempel.invalid', vite: { cacheDir: './.vite-cache' } });\n")
        os.symlink(PAKET, s / 'node_modules')
        rc, logg = processgrans.kor_i_katalog(s, [s / 'node_modules' / '.bin' / 'astro', 'build'])
        return rc, logg, s / 'dist'

    def test_tva_sprak_och_en_oforandrad_sida(self):
        rc, logg, dist = self.bygg({
            'index.astro': sida('..', 'sprak="sv" alternativ={%s}' % ALT, '<Sprakvaxlare aktuellt="sv" alternativ={%s} />' % VAXLARE),
            'en/index.astro': sida('../..', 'sprak="en" alternativ={%s}' % ALT, '<Sprakvaxlare aktuellt="en" alternativ={%s} />' % VAXLARE),
            'om.astro': sida('..', '', '<p>Bara svenska</p>'),
            'tack.astro': sida('..', 'noindex sprak="sv" alternativ={%s}' % ALT, '<p>Tack</p>')})
        self.assertEqual(rc, 0, logg[-800:])
        sv = (dist / 'index.html').read_text(encoding='utf-8')
        en = (dist / 'en' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<html lang="sv"', sv); self.assertIn('<html lang="en"', en)
        for html in (sv, en):
            self.assertIn('<link rel="alternate" hreflang="sv" href="https://exempel.invalid/">', html)
            self.assertIn('<link rel="alternate" hreflang="en" href="https://exempel.invalid/en/">', html)
            self.assertIn('<link rel="alternate" hreflang="x-default" href="https://exempel.invalid/">', html)
        self.assertIn('content="en_GB"', en); self.assertIn('Skip to content', en); self.assertIn('Hoppa till innehållet', sv)
        self.assertRegex(en, r'<a href="/en/" lang="en" hreflang="en" aria-current="page"[^>]*>English</a>')
        self.assertRegex(en, r'<a href="/" lang="sv" hreflang="sv"[^>]*>Svenska</a>')
        self.assertNotRegex(en, r'<a href="/" [^>]*aria-current')
        om = (dist / 'om' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<html lang="sv"', om); self.assertNotIn('hreflang', om); self.assertIn('content="sv_SE"', om)
        self.assertNotIn('hreflang', (dist / 'tack' / 'index.html').read_text(encoding='utf-8'), 'en noindex-sida får inga alternate-länkar')
        karta = (dist / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('https://exempel.invalid/en/', karta); self.assertIn('https://exempel.invalid/', karta)
        for f in (sv, en):
            self.assertNotIn('<script', f)

    def test_bygget_faller_pa_fel_sprak(self):
        for extra, fel in (('sprak="svenska"', 'ogiltig språkkod'), ('sprak="en" alternativ={%s}' % "[{ sprak: 'sv', href: '/' }]", 'sidans eget språk')):
            with self.subTest(extra=extra):
                rc, logg, _ = self.bygg({'index.astro': sida('..', extra, '<p>x</p>')})
                self.assertNotEqual(rc, 0); self.assertIn(fel, logg)


if __name__ == '__main__':
    unittest.main()
