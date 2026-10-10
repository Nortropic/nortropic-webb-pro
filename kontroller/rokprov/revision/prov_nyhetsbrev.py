#!/usr/bin/env python3
"""Nyhetsbrevet i mallens Worker (mall/leverans/worker/index.js, POST /api/nyhetsbrev/, katalogens k14-brevo-dubbel) mot en
märkt attrapp av Brevos API i Node (prov_nyhetsbrev_node.mjs): anropet till dubbel bekräftelse med kundens lista, mall,
återkomstadress och utan spårning; ingen väg när kunden inte valt nyhetsbrevet; ingen begäran till Brevo utanför
produktionen, utan samtycke, med fel adress, från en annan webbplats, ur skräpfällan eller med ofullständig
konfiguration; leverantörens fel, nätfel och frist ger ett synligt 503 utan leverantörens text; nyckeln syns aldrig i
svar eller logg. Dessutom exportens koppling: sidorna läggs in bara när sajten använder komponenten, och driftvärdena
fyller listans och mallens id."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exportera  # noqa: E402
import korregister  # noqa: E402
import processgrans  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / 'mall' / 'leverans' / 'worker' / 'index.js'
NODE = Path(__file__).with_name('prov_nyhetsbrev_node.mjs')
NYCKEL = 'xkeysib-SYNTETISKT-HEMLIG-NYCKEL-0000'
PAKET = ROOT / 'kunder' / 'rokprov-mall' / 'sajt' / 'node_modules'
MALL = ROOT / 'mall' / 'astro' / 'src'


class Nyhetsbrev(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run(['node', '--no-warnings', str(NODE), str(WORKER)], capture_output=True, text=True, timeout=120)
        if r.returncode:
            raise AssertionError(r.stderr[-1500:])
        cls.f = {x['namn']: x for x in json.loads(r.stdout)}

    def test_anropet_till_brevo_ar_dubbel_bekraftelse_utan_sparning(self):
        f = self.f['skickad']
        self.assertEqual((f['status'], f['location'], f['utfall']), (303, '/nyhetsbrev/skickad/', 'skickad'))
        self.assertEqual(len(f['anrop']), 1)
        a = f['anrop'][0]
        self.assertEqual((a['url'], a['metod'], a['nyckel']), ('https://api.brevo.com/v3/contacts/doubleOptinConfirmation', 'POST', True))
        self.assertEqual(a['kropp'], {'email': 'prov@example.invalid', 'includeListIds': [12], 'templateId': 7,
                                      'redirectionUrl': 'https://kund.example/nyhetsbrev/bekraftad/', 'contactPixelTrackingConsent': False})
        self.assertEqual(self.f['skickad-204']['utfall'], 'skickad')

    def test_ingen_vag_nar_kunden_inte_valt_nyhetsbrevet(self):
        for n in ('ej-valt', 'ej-valt-get'):
            self.assertEqual(self.f[n]['status'], 404, n)
            self.assertEqual(self.f[n]['anrop'], [])
        self.assertEqual((self.f['valt-get']['status'], self.f['valt-get']['allow']), (405, 'POST'))

    def test_inget_anrop_utanfor_produktionen_eller_utan_giltig_anmalan(self):
        for n, status, utfall in (('demo', 303, 'demo'), ('demo-utan-val', 303, 'demo'), ('utan-samtycke', 422, 'ofullstandig'),
                                  ('fel-epost', 422, 'ofullstandig'), ('honeypot', 303, 'honeypot'), ('frammande', 403, None),
                                  ('frammande-origin', 403, None), ('for-stor', 413, 'for-stor'),
                                  ('halvt-konfigurerat', 503, 'inte-aktiverat'), ('ogiltigt-id', 503, 'inte-aktiverat')):
            with self.subTest(n=n):
                self.assertEqual((self.f[n]['status'], self.f[n]['utfall']), (status, utfall))
                self.assertEqual(self.f[n]['anrop'], [], 'ingen begäran till Brevo')
        u = self.f['utan-samtycke']
        self.assertIn('Kryssa i rutan', u['text']); self.assertIn('value="prov@example.invalid"', u['text'])
        self.assertIn('aria-invalid="true" aria-describedby="samtycke-fel"', u['text'])
        self.assertNotIn('<script>x', self.f['fel-epost']['text'], 'adressen escapas i felvyn')
        self.assertIn("script-src 'none'", u['csp']); self.assertEqual(u['robots'], 'noindex, nofollow')
        self.assertTrue(any('saknas eller är ogiltigt' in x for x in self.f['halvt-konfigurerat']['logg']))

    def test_leverantorens_fel_ar_synliga_utan_leverantorens_text(self):
        for n, logg in (('nekad', 'HTTP 400'), ('serverfel', 'HTTP 502'), ('natfel', 'fel hos leverantören (TypeError)'),
                        ('langsam', 'ingen bekräftelse inom fristen')):
            with self.subTest(n=n):
                f = self.f[n]
                self.assertEqual((f['status'], f['utfall']), (503, 'fel'))
                self.assertIn('Vi kunde inte bekräfta anmälan', f['text'])
                self.assertTrue(any(logg in x for x in f['logg']), f['logg'])
                for x in [f['text'], f['huvuden']] + f['logg']:
                    self.assertNotIn('SYNTETISKT-HEMLIGT', x)

    def test_nyckeln_syns_aldrig(self):
        for n, f in self.f.items():
            for x in [f['text'], f['huvuden'], f['location'] or ''] + f['logg']:
                self.assertNotIn(NYCKEL, x, n)


class Export(unittest.TestCase):
    def test_sidorna_foljer_komponenten_och_driftvardena_fyller_id(self):
        self.assertFalse((MALL / 'pages' / 'nyhetsbrev').exists(), 'svarssidorna ligger utanför mall/astro, så att varje ny sajt inte får dem')
        with korregister.egen_tmp_med('nwp-workersprov-', 'nyhetsbrevets exportprov') as d:
            src = Path(d) / 'src'
            (src / 'pages').mkdir(parents=True); (src / 'components').mkdir()
            (src / 'components' / 'Nyhetsbrev.astro').write_text('---\n---\n<form></form>\n')
            (src / 'pages' / 'index.astro').write_text("---\nimport Bas from '../layouts/Bas.astro';\n---\n<p>Nyhetsbrev nämns men importeras inte</p>\n")
            self.assertFalse(exportera.anvander_komponent(src, 'Nyhetsbrev'), 'bara en import räknas')
            self.assertEqual(exportera.funktionssidor(Path(d)), ['fel.astro', 'mottagen.astro'], 'utan komponenten: inga nyhetsbrevssidor')
            (src / 'pages' / 'om.astro').write_text("---\nimport Nyhetsbrev from '../components/Nyhetsbrev.astro';\n---\n<Nyhetsbrev />\n")
            self.assertTrue(exportera.anvander_komponent(src, 'Nyhetsbrev'))
            (src / 'pages' / 'nyhetsbrev').mkdir()
            (src / 'pages' / 'nyhetsbrev' / 'skickad.astro').write_text('<p>sajtens egen</p>\n')
            self.assertEqual(exportera.funktionssidor(Path(d)), ['nyhetsbrev/bekraftad.astro'], 'en egen sida skrivs inte över')
            self.assertEqual((src / 'pages' / 'nyhetsbrev' / 'skickad.astro').read_text(), '<p>sajtens egen</p>\n')
            self.assertIn('noindex', (src / 'pages' / 'nyhetsbrev' / 'bekraftad.astro').read_text())
        mall = (ROOT / 'mall' / 'leverans' / 'wrangler.jsonc').read_text(encoding='utf-8')
        ut = exportera.wrangler_namn(mall, 'prov', {'nyhetsbrev_lista': '12', 'nyhetsbrev_mall': '7'})
        self.assertIn('"NYHETSBREV_LISTA": "12"', ut); self.assertIn('"NYHETSBREV_MALL": "7"', ut)
        self.assertIn('"NYHETSBREV_LISTA": ""', exportera.wrangler_namn(mall, 'prov', None), 'utan val är vägen avstängd')
        self.assertNotRegex(mall, r'"BREVO_API_NYCKEL"\s*:', 'nyckeln är en hemlighet, aldrig en variabel i konfigurationen')


@unittest.skipUnless((PAKET / '.bin' / 'astro').exists(), 'mallens paket saknas: kör rökprovet (kunder/rokprov-mall/sajt)')
class Bygge(unittest.TestCase):
    def test_komponenten_och_sidorna_med_mallens_astro(self):
        tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'nyhetsbrevets bygge')).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        s = tmp / 'sajt'
        for rel in ('layouts/Bas.astro', 'styles/design.css', 'components/Nyhetsbrev.astro', 'pages/sitemap.xml.ts'):
            (s / 'src' / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(MALL / rel, s / 'src' / rel)
        for sida in ('skickad', 'bekraftad'):  # sidorna som exporten lägger in (mall/leverans/sidor), inte mallens egna
            (s / 'src' / 'pages' / 'nyhetsbrev').mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'mall' / 'leverans' / 'sidor' / 'nyhetsbrev' / (sida + '.astro'), s / 'src' / 'pages' / 'nyhetsbrev' / (sida + '.astro'))
        (s / 'src' / 'pages' / 'index.astro').write_text(
            "---\nimport Bas from '../layouts/Bas.astro';\nimport Nyhetsbrev from '../components/Nyhetsbrev.astro';\n---\n"
            "<Bas titel=\"Prov\" beskrivning=\"Prov\" tema=\"#123456\"><main id=\"innehall\"><Nyhetsbrev text=\"Ett mejl i månaden.\" /></main></Bas>\n")
        (s / 'package.json').write_text('{"type": "module", "private": true}')
        (s / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', site: 'https://exempel.invalid', vite: { cacheDir: './.vite-cache' } });\n")
        os.symlink(PAKET, s / 'node_modules')
        rc, logg = processgrans.kor_i_katalog(s, [s / 'node_modules' / '.bin' / 'astro', 'build'])
        self.assertEqual(rc, 0, logg[-800:])
        html = (s / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('action="/api/nyhetsbrev/" method="post"', html)
        self.assertRegex(html, r'<input[^>]*name="samtycke"[^>]*required')
        self.assertNotRegex(html, r'<input[^>]*name="samtycke"[^>]*checked', 'kryssrutan är aldrig förifylld')
        self.assertIn('href="/integritet/"', html)
        for f in ('<script', '<iframe', 'brevo', 'sibforms', 'rel="preconnect"'):
            self.assertNotIn(f, html.lower() if f == 'brevo' else html)
        for sida in ('skickad', 'bekraftad'):
            t = (s / 'dist' / 'nyhetsbrev' / sida / 'index.html').read_text(encoding='utf-8')
            self.assertIn('noindex', t)
        karta = (s / 'dist' / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertNotIn('nyhetsbrev', karta, 'svarssidorna står aldrig i sitemap.xml')


if __name__ == '__main__':
    unittest.main()
