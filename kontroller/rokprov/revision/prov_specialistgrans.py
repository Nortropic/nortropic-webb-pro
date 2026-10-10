#!/usr/bin/env python3
"""Specialistens läsgräns och versionsbundet före/efter-återbruk.

Bara syntetiska filer och observationskvitton. Modell, fotografering och bildläsning är attrapper;
produktionskodens verktygsval, versionsjämförelse, återställningsbeslut och kravgrindar körs.
"""
import contextlib
import copy
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('NWP_PROV_ROOT') or Path(__file__).resolve().parents[3])
sys.path.insert(0, str(ROOT / 'kontroller'))
import atelje
import kandidater as kd
import kompetens
import korregister


def kvitto(pass_, andrade=False):
    filer = kompetens.lasfiler(pass_)
    roller = kompetens.for_pass(pass_)
    skills, _ = kompetens.aktiverbara([f for r in roller for f in r['karna']])
    per = {'session': 'syntetisk', 'lasta': filer, 'saknas': [], 'fore_forsta_andring': filer,
           'skill_anrop': skills, 'skill_fore': skills, 'andrade': andrade, 'valda': []}
    return {'verifierad': True, 'ofullstandig': False, 'filer': filer, 'lasta': filer, 'saknas': [],
            'fore_forsta_andring': filer, 'skill_anrop': skills, 'skill_fel': [], 'per_session': [per],
            'sessioner': {'forvantade': 1, 'sedda': 1, 'saknade': []}, 'valda': [],
            'verktyg_anrop': {'förhandsvisning': {'anrop': 1, 'ok': 1}},
            'mcp_utfall': {'mcp__%s__syntetiskt_prov' % m: {'anrop lyckades': 1}
                          for r in roller for m in r.get('mcp_krav', [])}}


def bildlasning():
    return {'verifierad': True, 'grupper': {b: {'kravda': 4, 'lasta': 4, 'saknas': []} for b in ('X', 'Y')}}


def bedomning(fore='fore', efter='efter', utfall='likvardig'):
    return {'fore': fore, 'efter': efter, 'utfall': utfall, 'sett': True, 'bilder_per_version': 4,
            'lasning': bildlasning(), 'kompetens': kvitto('fore_efter'), 'kompetenskravbrister': [], 'skal': 'syntetiskt'}


class Specialistgrans(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'specialistgränsens prov'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.tmp, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder',
                                               STOPP=threading.Event(), SLUTFORD=threading.Event()))
        self.slug, self.kid = 'specialist-prov', 'k01'
        self.d = kd.kdir(self.slug, self.kid)
        self.src = kd.ksajt(self.slug, self.kid) / 'src' / 'pages' / 'index.astro'
        self.src.parent.mkdir(parents=True); self.src.write_text('<main>ursprunglig</main>')
        self.v = kd.projektets_version(self.slug, self.kid)
        self.d.mkdir(parents=True)
        self.bild = self.d / 'fokus.png'; self.bild.write_bytes(b'syntetiskt bildbevis')
        kd.satt_status(self.slug, self.kid, 'forfinad', 'syntetiskt', version=self.v, axe={'allvarliga': 0})
        self.events = []; self.sessioner = []; self.mutera = False; self.observerad_andring = False; self.aterfel = False
        self.stack.enter_context(patch.multiple(kd, pass_prompt=lambda *a, **k: 'syntetiskt bedömningsuppdrag',
                                               bevara_version=lambda *a, **k: None, kopiera_bilder=lambda *a: [],
                                               andra_nekas=lambda *a, **k: [], designkontroll=lambda *a: {'ok': True, 'fel': []}))
        self.stack.enter_context(patch.object(kompetens, 'kvitto', side_effect=lambda svar, p, **kw: kvitto(p, self.observerad_andring)))
        self.stack.enter_context(patch.object(atelje, 'session', side_effect=self.session))
        self.foto = self.stack.enter_context(patch.object(kd, 'fotografera', side_effect=self.fotografera))
        self.ater = self.stack.enter_context(patch.object(kd, 'aterstall_och_fotografera', side_effect=self.aterstall))

    def session(self, prompt, verktyg, *a, **kw):
        self.sessioner.append({'verktyg': verktyg, 'nekas': kw.get('nekas'), 'prompt': prompt})
        if self.mutera:
            self.src.write_text('<main>ändrad trots bedöm</main>')
        return {'session_id': 'syntetisk', 'structured_output': {'ingen_andring': 'bedömning utan redigering',
                'beteende_provat': [{'vad': 'fokus', 'hur': 'syntetiskt', 'resultat': 'synligt', 'bild': kd.rel(self.bild)}],
                'kod_andrad': [], 'visuell_bedomning': {'omdome': 'oforandrad'}, 'teknikval': [], 'fynd': []}}

    def fotografera(self, slug, kid):
        self.events.append('foto')
        return kd.satt_status(slug, kid, 'klar', 'syntetiskt foto', version=kd.projektets_version(slug, kid), axe={'allvarliga': 0})

    def aterstall(self, slug, kid, v):
        self.events.append('aterstall')
        if self.aterfel:
            raise RuntimeError('syntetiskt återställningsfel')
        self.src.write_text('<main>ursprunglig</main>')
        return kd.satt_status(slug, kid, 'klar', 'syntetiskt återställd', version=v, axe={'allvarliga': 0})

    def kor_pass(self, lage='bedom'):
        return kd.kompetenspass(self.slug, self.kid, 'granskning', 'prov', lage=lage)

    def test_bedom_far_lasande_hjalpare_och_nekar_skrivverktygen(self):
        st = self.kor_pass(); anrop = self.sessioner[0]
        self.assertTrue(kd.pass_uppfyllt(st['kompetens']['prov:granskning']))
        self.assertTrue(any('--granskare' in x for x in anrop['verktyg']))
        self.assertFalse(any(x.startswith(('Write', 'Edit', 'NotebookEdit')) or '--skriv' in x or 'typsnitt.py' in x or 'material.py' in x
                             for x in anrop['verktyg']))
        self.assertTrue({'Write', 'Edit', 'MultiEdit', 'NotebookEdit'} <= set(anrop['nekas']))
        self.assertEqual(self.events, ['foto'])

    def test_okand_rollhjalpare_far_inte_skrivbehorighet_i_bedom(self):
        with patch.object(kompetens, 'for_pass', return_value=[{'verktyg': ['material', 'skillskript', 'design', 'förhandsvisning']} ]):
            verktyg = kd.bedomningsverktyg(self.slug, self.kid, 'granskning')
        self.assertFalse(any('material.py' in x or 'skillskript.py' in x or '--skriv' in x for x in verktyg))
        self.assertTrue(any('design.py' in x for x in verktyg))

    def test_faktisk_andring_aterstalls_fore_fotografering_utan_nytt_pass(self):
        self.mutera = True
        st = self.kor_pass(); rec = st['kompetens']['prov:granskning']
        self.assertFalse(rec['genomford']); self.assertTrue(rec['skrivskydd_brist'])
        self.assertEqual(self.events, ['aterstall'])
        self.assertEqual(self.src.read_text(), '<main>ursprunglig</main>')
        self.assertEqual(st['version'], self.v)
        self.assertEqual(len(self.sessioner), 1)

    def test_observerad_skrivning_faller_aven_om_slutfilen_ar_oforandrad(self):
        self.observerad_andring = True
        st = self.kor_pass()
        self.assertFalse(st['kompetens']['prov:granskning']['genomford'])
        self.assertEqual(self.events, ['aterstall'])

    def test_fallande_aterstallning_ar_ofullstandig(self):
        self.mutera = self.aterfel = True
        st = self.kor_pass()
        self.assertEqual(st['status'], 'ofullstandig')
        self.assertFalse(st['kompetens']['prov:granskning']['uppfyllt'])
        self.foto.assert_not_called()

    def test_andralaget_behaller_skrivverktygen_och_andringen(self):
        self.mutera = self.observerad_andring = True
        with patch.object(kd, 'verktyg', return_value=['Write(./egen/src/**)']):
            st = self.kor_pass('andra')
        self.assertIn('Write(./egen/src/**)', self.sessioner[0]['verktyg'])
        self.assertNotIn('Write', self.sessioner[0]['nekas'])
        self.assertTrue(st['kompetens']['prov:granskning']['genomford'])
        self.assertNotEqual(st['version'], self.v)

    def test_gammalt_bedomkvitto_med_skrivning_ar_inte_uppfyllt(self):
        rec = {'lage': 'bedom', 'pass': 'granskning', 'genomford': True, 'uppfyllt': True, 'andrad': False,
               'version_fore': self.v, 'version_efter': self.v, 'kvitto': kvitto('granskning')}
        self.assertTrue(kd.pass_uppfyllt(rec))
        rec['kvitto']['per_session'][0]['andrade'] = True
        self.assertFalse(kd.pass_uppfyllt(rec))
        rec['kvitto']['per_session'][0]['andrade'] = False
        rec['version_efter'] = 'annan'
        self.assertFalse(kd.pass_uppfyllt(rec))

    def test_bildkvittot_kraver_bada_grupperna_med_verkliga_antal(self):
        self.assertTrue(kd.fore_efter_bilder_last(bildlasning(), 4))
        for las in (None, {'verifierad': True, 'grupper': {}}, {'verifierad': True, 'grupper': {'X': {'saknas': []}, 'Y': {'saknas': []}}},
                    {'verifierad': True, 'grupper': {'X': {'kravda': 0, 'lasta': 0, 'saknas': []}, 'Y': {'kravda': 0, 'lasta': 0, 'saknas': []}}}):
            with self.subTest(las=las):
                self.assertFalse(kd.fore_efter_bilder_last(las, 4))
        las = bildlasning(); las['grupper']['Y']['lasta'] = 3
        self.assertFalse(kd.fore_efter_bilder_last(las, 4))

    def test_cache_kraver_versioner_kompetens_och_bildlasning(self):
        post = bedomning()
        self.assertTrue(kd.fore_efter_giltig(post, 'fore', 'efter'))
        self.assertFalse(kd.fore_efter_giltig(post, 'fore', 'ny'))
        for f, v in [('kompetens', {}), ('kompetenskravbrister', ['saknas']), ('lasning', {}), ('sett', False)]:
            p = copy.deepcopy(post); p[f] = v
            with self.subTest(f=f): self.assertFalse(kd.fore_efter_giltig(p, 'fore', 'efter'))
        self.assertTrue(kd.fore_efter_giltig(bedomning(utfall='oklart'), 'fore', 'efter'), 'en ärligt oklar maskindom är fortfarande inget ägarbeslut')

    def forbered_fordjupning(self, post):
        dom = {'tid': 'syntetisk-dom', 'uppdrag': {'typ': 'ratta', 'resultat': 'rätta rubrik',
                'omfattning': ['rubrik'], 'bevara': ['övrigt'], 'specialister': {}}}
        kd.satt_status(self.slug, self.kid, 'forfinad', 'syntetiskt', version='efter',
                       forfining={'dom': dom['tid'], 'fran': 'fore', 'fore_efter': post, 'fortsattning': {'beslut': 'fora_vidare'}})
        return dom

    def test_aterupptagning_gor_om_inaktuell_bedomning_och_bevarar_historiken(self):
        gammal = bedomning(efter='aldre')
        dom = self.forbered_fordjupning(gammal)
        with patch.object(kd, 'fore_efter', return_value=bedomning()) as nytt:
            st = kd.efter_fordjupning(self.slug, self.kid, dom)
        nytt.assert_called_once_with(self.slug, self.kid, 'fore', 'efter')
        self.assertEqual(st['forfining']['fore_efter_historik'][0]['bedomning'], gammal)
        self.assertEqual(st['status'], 'forfinad', 'maskinomdömet får inte sätta ägargodkänd')
        self.assertEqual(dom['uppdrag']['resultat'], 'rätta rubrik')

    def test_aterupptagning_gor_om_bristande_evidens_pa_samma_version(self):
        for falt in ('kompetens', 'lasning'):
            gammal = bedomning(); gammal[falt] = {}
            dom = self.forbered_fordjupning(gammal)
            with patch.object(kd, 'fore_efter', return_value=bedomning()) as nytt:
                kd.efter_fordjupning(self.slug, self.kid, dom)
            self.assertEqual(nytt.call_count, 1)

    def test_giltig_bedomning_ateranvands_utan_session_eller_historikomskrivning(self):
        dom = self.forbered_fordjupning(bedomning())
        with patch.object(kd, 'fore_efter') as nytt:
            st = kd.efter_fordjupning(self.slug, self.kid, dom)
        nytt.assert_not_called()
        self.assertNotIn('fore_efter_historik', st['forfining'])
        self.assertEqual(st['status'], 'forfinad')


if __name__ == '__main__':
    unittest.main()
