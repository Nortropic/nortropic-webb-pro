#!/usr/bin/env python3
"""Mallens länkkomponenter för K09 och K11 (mall/astro/src/components/Bokning.astro och Betallank.astro, katalogens
k09-bokningslank och k11-stripe-betallank) byggda med mallens Astro: en vanlig länk till tjänsten, inget skript, ingen
iframe och ingen förhandshämtning; bygget faller på en adress som inte är https, på inloggningsuppgifter i adressen, på
en betallänk utanför Stripe och på en testlänk utan testläge (och tvärtom). Kräver mallens installerade paket
(rökprovets sajt, kunder/rokprov-mall/sajt)."""
import os
from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402
import processgrans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PAKET = ROOT / 'kunder' / 'rokprov-mall' / 'sajt' / 'node_modules'
KOMPONENTER = ROOT / 'mall' / 'astro' / 'src' / 'components'
FORBJUDET = ('<script', '<iframe', 'rel="preconnect"', 'rel="prefetch"', 'rel="dns-prefetch"', 'js.stripe.com', 'embed')


@unittest.skipUnless((PAKET / '.bin' / 'astro').exists(), 'mallens paket saknas: kör rökprovet (kunder/rokprov-mall/sajt)')
class Lankkomponenter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'länkkomponenternas bygge')).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.n = 0

    def bygg(self, kropp):
        """(rc, logg, html) för en sida med kroppen, byggd i en egen provsajt med mallens paket."""
        self.n += 1
        s = self.tmp / ('sajt%d' % self.n)
        (s / 'src' / 'pages').mkdir(parents=True); (s / 'src' / 'components').mkdir()
        for k in ('Bokning.astro', 'Betallank.astro'):
            shutil.copyfile(KOMPONENTER / k, s / 'src' / 'components' / k)
        (s / 'package.json').write_text('{"type": "module", "private": true}')
        (s / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', site: 'https://exempel.invalid', vite: { cacheDir: './.vite-cache' } });\n")
        (s / 'src' / 'pages' / 'index.astro').write_text(
            "---\nimport Bokning from '../components/Bokning.astro';\nimport Betallank from '../components/Betallank.astro';\n---\n"
            "<html lang=\"sv\"><head><title>Prov</title></head><body><main>%s</main></body></html>\n" % kropp)
        os.symlink(PAKET, s / 'node_modules')  # mallens paket; Vites cache i provsajten, aldrig i mallen
        rc, logg = processgrans.kor_i_katalog(s, [s / 'node_modules' / '.bin' / 'astro', 'build'])
        f = s / 'dist' / 'index.html'
        return rc, logg, f.read_text(encoding='utf-8') if rc == 0 and f.is_file() else ''

    def test_lankarna_utan_skript_eller_forhandshamtning(self):
        rc, logg, html = self.bygg('<Bokning adress="https://cal.com/provfirman/besok?tid=30" tjanst="Cal.com" text="Välj en tid som passar." />'
                                   '<Betallank lank="https://buy.stripe.com/abc123XYZ" vad="Deposition för bokad tid" />')
        self.assertEqual(rc, 0, logg[-800:])
        self.assertIn('href="https://cal.com/provfirman/besok?tid=30"', html)
        self.assertIn('(öppnas hos Cal.com)', html); self.assertIn('Välj en tid som passar.', html)
        self.assertIn('href="https://buy.stripe.com/abc123XYZ"', html)
        self.assertIn('Deposition för bokad tid', html); self.assertIn('ser aldrig dina kortuppgifter', html)
        self.assertNotIn('Testläge', html)
        for f in FORBJUDET:
            self.assertNotIn(f, html)

    def test_testlage_syns_och_galler_bara_testlankar(self):
        rc, logg, html = self.bygg('<Betallank lank="https://buy.stripe.com/test_abc123" vad="Provbetalning" testlage />')
        self.assertEqual(rc, 0, logg[-800:])
        self.assertIn('ingen verklig betalning görs', html)
        for kropp, fel in (('<Betallank lank="https://buy.stripe.com/test_abc123" vad="X" />', 'testlage'),
                           ('<Betallank lank="https://buy.stripe.com/abc123XYZ" vad="X" testlage />', 'riktig betallänk')):
            rc, logg, _ = self.bygg(kropp)
            self.assertNotEqual(rc, 0); self.assertIn(fel, logg)

    def test_bygget_faller_pa_fel_adress(self):
        for kropp, fel in (
                ('<Bokning adress="http://cal.com/provfirman" tjanst="Cal.com" />', 'https://'),
                ('<Bokning adress="javascript:alert(1)" tjanst="Cal.com" />', 'https://'),
                ('<Bokning adress="https://u:p@cal.com/x" tjanst="Cal.com" />', 'inloggningsuppgifter'),
                ('<Bokning adress="https://cal.com/x" tjanst=" " />', 'tjänstens namn'),
                ('<Betallank lank="https://buy.stripe.com.evil.example/abc123" vad="X" />', 'betallänk hos Stripe'),
                ('<Betallank lank="https://checkout.stripe.com/c/pay/abc123" vad="X" />', 'betallänk hos Stripe'),
                ('<Betallank lank="https://buy.stripe.com/abc123?prefilled_email=a@b.se" vad="X" />', 'betallänk hos Stripe'),
                ('<Betallank lank="https://buy.stripe.com/abc123XYZ" vad="" />', 'vad betalningen gäller')):
            with self.subTest(kropp=kropp):
                rc, logg, _ = self.bygg(kropp)
                self.assertNotEqual(rc, 0, kropp); self.assertIn(fel, logg)


if __name__ == '__main__':
    unittest.main()
