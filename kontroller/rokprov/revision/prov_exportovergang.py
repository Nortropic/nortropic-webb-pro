#!/usr/bin/env python3
"""Exportens version och utfall, med syntetisk sajt och utan npm, Git eller nät."""
import contextlib
import json
import os
import signal
from types import SimpleNamespace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exportera
import prova
import korslut
import skapande
import granska
import korregister


class Exportovergang(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'exportens övergångsprov')))
        self.slug = 'prov-export'
        self.k = self.root / 'kunder' / self.slug
        self.sajt = self.k / 'sajt'
        (self.sajt / 'src/pages').mkdir(parents=True)
        (self.sajt / 'public').mkdir()
        (self.sajt / 'src/pages/index.astro').write_text('<h1>Syntetiskt prov</h1>')
        (self.sajt / 'public/markor.txt').write_text('ursprunglig')
        (self.sajt / 'package.json').write_text('{"dependencies":{}}')
        (self.sajt / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });")
        self.stack.enter_context(patch.multiple(exportera, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))

    def test_fallen_export_bevarar_tidigare_kundrepo(self):
        mal = self.k / 'kundrepo'; mal.mkdir()
        (mal / 'tidigare.txt').write_text('behåll vid fel')
        with patch.object(exportera, 'verifiera_bygge', return_value=(False, 'syntetiskt byggfel')):
            res = exportera.exportera(self.slug)
        self.assertFalse(res['ok'])
        self.assertEqual((mal / 'tidigare.txt').read_text(), 'behåll vid fel')
        self.assertFalse((mal / 'src').exists())
        self.assertTrue(res['kvitto'])

    def test_testexport_ar_versionsbunden_och_inte_kundklar(self):
        res = exportera.exportera(self.slug, bygg=False)
        self.assertTrue(res['ok'])
        self.assertFalse(res['klart_for_leverans'])
        self.assertTrue(res['kallor_sha256'])
        self.assertTrue(res['export_sha256'])
        post = json.loads(Path(res['kvitto']).read_text())
        self.assertEqual(post['export_sha256'], res['export_sha256'])
        self.assertEqual(post['kontroller']['exportbygge']['varde'], None)
        self.assertFalse(post['tillstand']['klart_for_leverans']['varde'])
        akt = exportera.aktuell(self.slug)
        self.assertTrue(akt['aktuell'])
        (self.k / 'kundrepo/public/markor.txt').write_text('ändrad efter export')
        self.assertFalse(exportera.aktuell(self.slug)['aktuell'])

    def test_kopiering_av_andrad_kalla_publiceras_inte(self):
        original = exportera.kopiera
        def andrad(src, dst):
            original(src, dst)
            if Path(src).name == 'public':
                (self.sajt / 'public/markor.txt').write_text('ny version medan exporten pågår')
        with patch.object(exportera, 'kopiera', side_effect=andrad):
            res = exportera.exportera(self.slug, bygg=False)
        self.assertFalse(res['ok'])
        self.assertFalse((self.k / 'kundrepo').exists())

    def test_licenstext_pastar_inte_att_tillstand_finns(self):
        res = exportera.exportera(self.slug, bygg=False)
        lic = (Path(res['ut']) / 'LICENSER.md').read_text()
        self.assertNotIn('publicerade med verksamhetens tillstånd', lic)
        self.assertIn('inte verifierat', lic)


    def test_bygget_binds_till_oforandrade_kallor(self):
        (self.sajt / 'node_modules').mkdir()
        def falskt_bygge(*args, **kwargs):
            self.assertFalse((self.sajt / 'dist').exists(), 'provet fortsatte trots att byggprocessen ändrade källorna')
            (self.sajt / 'dist').mkdir()
            (self.sajt / 'dist/index.html').write_text('<h1>syntetiskt</h1>')
            (self.sajt / 'public/markor.txt').write_text('ändrat under bygget')
            return 0, 'syntetisk byggprocess'
        with patch.object(prova, 'ROOT', self.root), patch.object(prova, 'kor', side_effect=falskt_bygge):
            s = prova.prova(self.slug, snabb=True)
        self.assertFalse(s['grindar']['bygge']['ok'])
        self.assertIn('käll', s['grindar']['bygge']['sammanfattning'])

    def test_slutbesked_blir_historik_om_kallorna_andras(self):
        (self.sajt / 'dist').mkdir()
        (self.sajt / 'dist/index.html').write_text('<h1>oförändrat dist</h1>')
        dist = prova.dist_hash(self.sajt / 'dist')
        fil = self.k / 'korningar/prov/SLUT.json'; fil.parent.mkdir(parents=True)
        post = {'typ': korslut.TYP, 'korning': 'prov', 'slutkod': 0, 'dist_sha256': dist,
                'kallor_sha256': skapande.kallversion(self.sajt),
                'tillstand': {n: {'varde': True, 'text': 'syntetiskt prov'} for n, _ in korslut.TILLSTAND}}
        fil.write_text(json.dumps(post))
        (self.sajt / 'public/markor.txt').write_text('ändrade källor utan nytt dist')
        with patch.object(korslut, 'slutposter', return_value=[fil]), patch.object(korslut, 'avbrutna', return_value=[]), \
                patch.object(granska, 'aktuell_metod', return_value={}), patch.object(korslut, 'ej_belagda_domar', return_value=[]):
            s = korslut.aktuell(self.k)
        self.assertIsNone(s['tillstand']['tekniskt_godkant']['varde'])
        self.assertFalse(s['tillstand']['klart_for_leverans']['varde'])
        self.assertIn('käll', ' '.join(s['provad']['andrat']))


    def test_exportmal_faar_inte_ersatta_kvitton_eller_andra_kandidater(self):
        for n in ('exporter', 'kandidater/k02/sajt'):
            with self.subTest(mal=n):
                mal = self.k / n; mal.mkdir(parents=True, exist_ok=True)
                (mal / 'bevara.txt').write_text('syntetiskt tidigare material')
                with self.assertRaises((ValueError, RuntimeError)):
                    exportera.exportera(self.slug, ut=mal, bygg=False)
                self.assertEqual((mal / 'bevara.txt').read_text(), 'syntetiskt tidigare material')
                self.assertFalse((mal / 'src/pages/index.astro').exists())

    def test_sigint_mellan_namnbytena_aterstaller_tidigare_export(self):
        mal = self.k / 'kundrepo'; mal.mkdir()
        (mal / 'bevara.txt').write_text('syntetisk tidigare export')
        riktig = os.replace
        def byt(src, dst):
            riktig(src, dst)
            if Path(src) == mal and Path(dst).parent.name == 'kundrepo-tidigare':
                signal.raise_signal(signal.SIGINT)
        tidigare = signal.signal(signal.SIGINT, signal.default_int_handler)
        try:
            with patch.object(exportera.os, 'replace', side_effect=byt), self.assertRaises(KeyboardInterrupt):
                exportera.exportera(self.slug, bygg=False)
        finally:
            signal.signal(signal.SIGINT, tidigare)
        self.assertEqual((mal / 'bevara.txt').read_text(), 'syntetisk tidigare export')

    def test_exportordning_beror_inte_pa_slump_id_samma_sekund(self):
        with patch.object(exportera, 'nu', return_value='2026-01-01T00:00:00Z'):
            with patch.object(exportera, 'uuid', SimpleNamespace(uuid4=lambda: SimpleNamespace(hex='f' * 32))):
                exportera.exportera(self.slug, bygg=False)
            (self.sajt / 'public/markor.txt').write_text('andra syntetiska exporten')
            with patch.object(exportera, 'uuid', SimpleNamespace(uuid4=lambda: SimpleNamespace(hex='0' * 32))):
                andra = exportera.exportera(self.slug, bygg=False)
        aktuell = exportera.aktuell(self.slug)
        self.assertEqual(aktuell['id'], andra['id'])
        self.assertTrue(aktuell['aktuell'])

    def test_sigterm_efter_publicerat_mal_aterstaller_foregaende_export(self):
        mal = self.k / 'kundrepo'; mal.mkdir()
        (mal / 'bevara.txt').write_text('syntetisk tidigare export')
        riktig = os.replace
        def byt(src, dst):
            riktig(src, dst)
            if Path(src).name == 'repo' and Path(src).parent.name.startswith('nwp-export-') and Path(dst) == mal:
                signal.raise_signal(signal.SIGTERM)
        with patch.object(exportera.os, 'replace', side_effect=byt):
            ut = exportera.exportera(self.slug, bygg=False)
        self.assertFalse(ut['ok'])
        self.assertEqual((mal / 'bevara.txt').read_text(), 'syntetisk tidigare export')
        self.assertFalse((mal / 'src/pages/index.astro').exists())

    def test_gammalt_kvitto_skymmer_inte_nya_och_klockan_kan_ga_bakat(self):
        fore = exportera.exportera(self.slug, bygg=False)
        gammal = Path(fore['kvitto']).parent
        gammal.rename(gammal.parent / '20261007T213000Z-ffffffff')
        (self.sajt / 'public/markor.txt').write_text('nyare syntetisk export')
        with patch.object(exportera, 'nu', return_value='2026-01-01T00:00:00Z'):
            ny = exportera.exportera(self.slug, bygg=False)
        self.assertEqual(exportera.aktuell(self.slug)['id'], ny['id'])
        with patch.object(exportera, 'nu', return_value='2025-01-01T00:00:00Z'):
            nyast = exportera.exportera(self.slug, bygg=False)
        self.assertEqual(exportera.aktuell(self.slug)['id'], nyast['id'])

    def test_signal_nar_signalramen_avslutas_aterstaller_ocksa(self):
        mal = self.k / 'kundrepo'; mal.mkdir()
        (mal / 'bevara.txt').write_text('syntetisk tidigare export')
        riktig = exportera.avbrott_som_fel
        skickad = False
        @contextlib.contextmanager
        def sen_signal():
            nonlocal skickad
            with riktig():
                yield
                if not skickad:
                    skickad = True  # ett sent stopp vid publiceringen, inte ett andra under avslutet
                    signal.raise_signal(signal.SIGTERM)
        with patch.object(exportera, 'avbrott_som_fel', sen_signal):
            ut = exportera.exportera(self.slug, bygg=False)
        self.assertFalse(ut['ok'])
        self.assertEqual((mal / 'bevara.txt').read_text(), 'syntetisk tidigare export')

    def test_exportens_godkannanden_prövas_nu(self):
        post = {'korning': 'prov', 'dist_sha256': 'syntetisk-dist', 'kallor_sha256': skapande.kallversion(self.sajt),
                'tillstand': {n: {'varde': True, 'text': 'syntetiskt prov'} for n, _ in korslut.TILLSTAND}}
        with patch.object(korslut, 'aktuell', return_value=post):
            exportera.exportera(self.slug, bygg=False)
            post['tillstand']['tekniskt_godkant'] = {'varde': None, 'historik': {'varde': True}, 'text': 'dist ändrat'}
            post['tillstand']['agaren_godkanner'] = {'varde': False, 'text': 'ny syntetisk ägardom'}
            aktuell = exportera.aktuell(self.slug)
        self.assertTrue(aktuell['aktuell'], 'exportens filer är oförändrade')
        self.assertIsNone(aktuell['tillstand']['tekniskt_godkant']['varde'])
        self.assertFalse(aktuell['tillstand']['agaren_godkanner']['varde'])
        self.assertFalse(aktuell['klart_for_leverans'])


if __name__ == '__main__':
    unittest.main()
