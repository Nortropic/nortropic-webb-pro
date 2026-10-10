#!/usr/bin/env python3
"""Automatisk referensprofil: syntetiska paket och kvitton, inga modell-, nät- eller MCP-anrop.

Den falska profileraren ersätter enbart extern inspektion. Produktionskodens urval, cache och kvittovalidering körs.
"""
import contextlib
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import devtools
import korregister
import referensprofil as rp

PROFILERA = devtools.profilera


class Referensprofil(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'referensprofilens mekanikprov'))).resolve()
        self.u = self.root / 'underlag'; self.slug = 'profil-prov'
        self.ref = self.u / self.slug / 'referenser'; self.ref.mkdir(parents=True)
        self.calls = []
        self.motor = {'version': '1.2.3', 'modell': 'syntetisk', 'filer': {'devtools': 'syntetisk'}}
        self.stack.enter_context(patch.object(rp, 'motoridentitet', side_effect=lambda: copy.deepcopy(self.motor)))
        self.stack.enter_context(patch.object(devtools, 'profilera', side_effect=self.profil))
        self.stack.enter_context(patch.dict(os.environ, {'NWP_SLUG': self.slug}))
        self.k = self.paket('paket-v01', 'alpha', 'https://alpha.example.com/verkstad/')
        self.plan = {'kandidater': {'k01': self.k}}
        self.andring = None

    def paket(self, version, namn, adress):
        d = self.ref / version
        d.mkdir(exist_ok=True)
        bildrel = namn + '/01-sida/vy-390-forsta.png'
        bild = d / bildrel; bild.parent.mkdir(parents=True, exist_ok=True); bild.write_bytes(b'syntetisk bild')
        f = d / 'PAKET.json'
        j = json.loads(f.read_text()) if f.exists() else {'schema': 2, 'slug': self.slug, 'version': version, 'torr': False, 'kandidater': []}
        from urllib.parse import urlsplit
        url = urlsplit(adress)
        j['kandidater'].append({'namn': namn, 'adress': '%s://%s/' % (url.scheme, url.netloc), 'ok': True,
                                'resursursprung': ['https://resurs-' + namn + '.example.com'],
                                'sidor': [{'adress': adress, 'sida': url.path, 'katalog': namn + '/01-sida', 'ok': True, 'filer': [bildrel]}]})
        f.write_text(json.dumps(j))
        return {'huvudreferens': namn, 'referensbilder': [str(bild)], 'utgangspunkt': {'slag': 'referenssajt'}}

    def profil(self, slug, adress, ut, underlag, paket, referensnamn):
        self.calls.append((slug, adress, ut, paket))
        res = {'anrop': [], 'prestanda': {'lcp_ms': None, 'cls': None, 'ttfb_ms': None, 'lcp_element': 'h1', 'insikter': []},
               'lighthouse': {'enhet': 'mobile', 'prestanda': None, 'tillganglighet': None, 'basta_praxis': None, 'seo': None, 'not': ''},
               'natverk': {'antal': 0, 'storsta': []}, 'regler': [], 'anmarkning': 'Syntetiskt kvitto, inget verkligt anrop.'}
        j = {'slug': slug, 'adress': adress, 'paket': paket.name, 'referensnamn': referensnamn, 'version': self.motor['version'], 'torr': False,
             'verklig': True, 'aktivering': {'ansluten': True},
             'anvandning': {'genomford': True, 'grupper': {g: True for g in devtools.KRAVDA_GRUPPER}},
             'session': {'subtype': 'success', 'is_error': False, 'slutkod': 0}, 'svar': res}
        if self.andring:
            self.andring(j)
        ut.mkdir(parents=True, exist_ok=True)
        (ut / 'DEVTOOLS.json').write_text(json.dumps(j))
        (ut / 'DEVTOOLS.md').write_text('Syntetisk profil; inget externt anrop.')
        (ut / 'session.jsonl').write_text('{"syntetisk": true}\n')
        (ut / 'natgrans.json').write_text('{"syntetisk": true}')
        return j, None

    def kor(self, metod='metod-ett'):
        return rp.forbered(self.slug, self.plan, metod, underlag=self.u, root=self.root)

    def test_bestaller_exakt_undersida_och_aldre_valt_paket(self):
        self.paket('paket-v02', 'beta', 'https://beta.example.com/')
        res = self.kor()
        self.assertTrue(res['ok'], res)
        self.assertEqual(self.calls[0][1], 'https://alpha.example.com/verkstad/')
        self.assertEqual(self.calls[0][3], self.ref / 'paket-v01')
        self.assertEqual(devtools.resursursprung(self.slug, self.calls[0][1], self.u, self.calls[0][3]), ['https://resurs-alpha.example.com'])
        self.assertIn('alpha.example.com/verkstad/', '\n'.join(rp.prompt_rader(res, 'k01')))

    def test_aterbruk_identiskt_kvitto_utan_ny_session(self):
        self.assertTrue(self.kor()['ok'])
        res = self.kor()
        self.assertTrue(res['ok'], res)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(res['kandidater']['k01']['profiler'][0]['ateranvand'])

    def test_ny_metod_eller_motor_ger_ny_profil(self):
        self.assertTrue(self.kor()['ok'])
        self.assertTrue(self.kor('metod-tva')['ok'])
        self.motor['version'] = '1.2.4'
        self.assertTrue(self.kor('metod-tva')['ok'])
        self.assertEqual(len(self.calls), 3)

    def test_andrad_bild_eller_manifest_ger_ny_profil(self):
        self.assertTrue(self.kor()['ok'])
        Path(self.k['referensbilder'][0]).write_bytes(b'annan syntetisk bild')
        self.assertTrue(self.kor()['ok'])
        self.paket('paket-v01', 'beta', 'https://beta.example.com/')
        self.assertTrue(self.kor()['ok'])
        self.assertEqual(len(self.calls), 3)

    def test_forandrat_sparat_kvitto_ateranvands_inte(self):
        self.assertTrue(self.kor()['ok'])
        (self.calls[0][2] / 'DEVTOOLS.md').write_text('ändrat underlag')
        self.assertTrue(self.kor()['ok'])
        self.assertEqual(len(self.calls), 2)

    def test_provklient_eller_ofullstandigt_kvitto_stoppar(self):
        for falt, varde in [('verklig', False), ('torr', True), ('version', 'fel-version')]:
            with self.subTest(falt=falt):
                self.andring = lambda j: j.update({falt: varde})
                res = self.kor(falt)
                self.assertFalse(res['ok'], res)
                self.assertTrue(res['kandidater']['k01']['brister'])
        self.assertEqual(len(self.calls), 3)  # ett försök per beställning, ingen intern omförsöksloop

    def test_grupp_eller_slutstatus_eller_schemafel_stoppar(self):
        andra = [lambda j: j['anvandning']['grupper'].update(element=False),
                 lambda j: j['session'].update(slutkod=1), lambda j: j['svar'].pop('regler')]
        for i, andra_ in enumerate(andra):
            self.andring = andra_
            res = self.kor('ofullstandigt-%d' % i)
            self.assertFalse(res['ok'], res)

    def test_andrad_referens_under_profil_far_inte_giltig_bindning(self):
        self.andring = lambda j: Path(self.k['referensbilder'][0]).write_bytes(b'ny bild under inspektionen')
        res = self.kor()
        self.assertFalse(res['ok'], res)
        self.assertIn('ändrades under', str(res))

    def test_fel_referensnamn_nekas_fore_nagon_session(self):
        self.k['huvudreferens'] = 'okand'
        res = self.kor()
        self.assertFalse(res['ok'], res)
        self.assertFalse(self.calls)
        self.assertFalse((self.ref / 'devtools').exists())

    def test_alla_huvudreferenser_kraver_bild_och_profileras(self):
        beta = self.paket('paket-v01', 'beta', 'https://beta.example.com/')
        self.k['huvudreferens'] = 'alpha + beta'
        self.assertFalse(self.kor()['ok'])
        self.assertFalse(self.calls)
        self.k['referensbilder'] += beta['referensbilder']
        res = self.kor()
        self.assertTrue(res['ok'], res)
        self.assertEqual(len(res['kandidater']['k01']['profiler']), 2)

    def test_tva_kandidater_samma_sida_far_en_inspektion(self):
        self.plan['kandidater']['k02'] = copy.deepcopy(self.k)
        res = self.kor()
        self.assertTrue(res['ok'], res)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(res['kandidater']['k01']['profiler'], res['kandidater']['k02']['profiler'])

    def test_tjansteskarm_och_egen_redovisas_som_ej_tillamplig(self):
        for k in ({'huvudreferens': 'egen'}, {'huvudreferens': 'Skärm', 'utgangspunkt': {'slag': 'mobbin_skarm'}, 'referensbilder': []}):
            self.plan['kandidater']['k01'] = k
            res = self.kor()
            self.assertTrue(res['ok'], res)
            self.assertEqual(res['kandidater']['k01']['tillstand'], 'ej_tillampligt')
            self.assertIn('ingen genomförd', '\n'.join(rp.prompt_rader(res, 'k01')))
        self.assertFalse(self.calls)

    def test_saknad_bild_och_odeklarerad_bild_nekas(self):
        p = Path(self.k['referensbilder'][0]); p.unlink()
        self.assertFalse(self.kor()['ok'])
        p.write_bytes(b'bild')
        f = self.ref / 'paket-v01/PAKET.json'; j = json.loads(f.read_text())
        j['kandidater'][0]['sidor'][0]['filer'] = []; f.write_text(json.dumps(j))
        self.assertFalse(self.kor()['ok'])
        self.assertFalse(self.calls)

    def test_lankad_bild_eller_utkatalog_nekas_fore_inspektion(self):
        p = Path(self.k['referensbilder'][0]); p.unlink()
        mal = self.root / 'annan'; mal.write_bytes(b'privat syntetiskt')
        p.symlink_to(mal)
        self.assertFalse(self.kor()['ok'])
        p.unlink(); p.write_bytes(b'bild')
        (self.ref / 'devtools').symlink_to(self.root, target_is_directory=True)
        self.assertFalse(self.kor()['ok'])
        self.assertFalse(self.calls)
        self.assertFalse((self.root / '.profil.las').exists())

    def test_navigering_till_lokal_eller_annan_sajt_nekas(self):
        f = self.ref / 'paket-v01/PAKET.json'; j = json.loads(f.read_text())
        for adress in ('http://127.0.0.1/', 'https://annan.example.com/', 'https://alpha.example.com:4771/'):
            j['kandidater'][0]['sidor'][0]['adress'] = adress; f.write_text(json.dumps(j))
            self.assertFalse(self.kor()['ok'])
        self.assertFalse(self.calls)

    def test_devtools_explicit_paket_reject_fore_mkdir(self):
        with patch.object(devtools, 'konfig', return_value=({}, '1.2.3', None)), patch.object(devtools, 'chrome_sokvag') as chrome:
            ut = self.ref / 'devtools/nekad'
            post, fel = PROFILERA(self.slug, 'https://alpha.example.com/annan/', ut, underlag=self.u, paket=self.ref / 'paket-v01')
            self.assertIsNone(post); self.assertIn('fångad sida', fel)
            self.assertFalse(ut.exists()); chrome.assert_not_called()

    def test_devtools_sid_adress_binder_endast_riktiga_vardnamn(self):
        self.assertEqual(devtools.profiladress('https://alpha.example.com/verkstad/'), 'https://alpha.example.com/verkstad/')
        for url in ('http://127.1/', 'https://localhost/', 'https://alpha.example.com:444/', 'https://u:p@alpha.example.com/', 'https://alpha.example.com/#a'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                devtools.profiladress(url)

    def test_metod_saknas_stoppar_fore_session(self):
        self.assertFalse(self.kor('')['ok'])
        self.assertFalse(self.calls)


if __name__ == '__main__':
    unittest.main()
