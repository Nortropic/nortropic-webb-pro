#!/usr/bin/env python3
"""Arbetskrav ur observerade kvitton; inga modeller, konton eller nätanrop.

--bas prövar samma fall mot HEAD:s kompetens.py inläst i minnet.
"""
import copy
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import kompetens

if '--bas' in sys.argv:
    sys.argv.remove('--bas')
    src = subprocess.run(['git', 'show', 'HEAD:kontroller/kompetens.py'], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
    bas = types.ModuleType('kompetens_bas')
    bas.__file__ = str(ROOT / 'kontroller/kompetens.py')
    exec(compile(src, bas.__file__, 'exec'), bas.__dict__)
    kompetens = bas


def kvitto(pass_):
    filer = kompetens.lasfiler(pass_)
    skills, _ = kompetens.aktiverbara([f for r in kompetens.for_pass(pass_) for f in r['karna']])
    return {'verifierad': True, 'ofullstandig': False, 'filer': filer, 'lasta': filer[:], 'saknas': [],
            'fore_forsta_andring': filer[:], 'skill_anrop': skills[:],
            'sessioner': {'forvantade': 1, 'sedda': 1, 'saknade': []},
            'per_session': [{'session': 'syntetisk-session', 'lasta': filer[:], 'fore_forsta_andring': filer[:],
                             'skill_anrop': skills[:], 'skill_fore': skills[:], 'andrade': True, 'valda': []}],
            'mcp_utfall': {f'mcp__{m}__search': {'anrop lyckades': 1} for m in ('refero', 'mobbin', '21st')}}


class Krav(unittest.TestCase):
    def test_hela_kedjans_pass_har_prövbara_krav(self):
        for pass_ in kompetens.PASS:
            with self.subTest(pass_=pass_):
                self.assertEqual(kompetens.kravbrister(kvitto(pass_), pass_), [])

    def test_read_ersatter_inte_skill(self):
        kv = kvitto('skapa')
        kv['per_session'][0]['skill_anrop'] = []
        self.assertTrue(any('Skill-aktivering' in s for s in kompetens.kravbrister(kv, 'skapa')))

    def test_ny_session_arver_inte_aktivering(self):
        kv = kvitto('skapa')
        p = copy.deepcopy(kv['per_session'][0]); p['session'] = 'andra'; p['skill_anrop'] = []
        kv['per_session'].append(p)
        kv['sessioner'].update(forvantade=2, sedda=2)
        self.assertTrue(any('session 2: Skill' in s for s in kompetens.kravbrister(kv, 'skapa')))

    def test_sen_aktivering_ger_inte_godkant(self):
        kv = kvitto('skapa'); kv['per_session'][0]['skill_fore'] = []
        self.assertTrue(any('före första' in s for s in kompetens.kravbrister(kv, 'skapa')))

    def test_namn_alias_stammer_med_skillfilen(self):
        kv = kvitto('jamforelse')
        kv['per_session'][0]['skill_anrop'] = ['variant']
        self.assertEqual(kompetens.kravbrister(kv, 'jamforelse'), [])

    def test_brist_i_lasning_syns_aven_med_tomt_saknas(self):
        kv = kvitto('kritik_b'); kv['per_session'][0]['lasta'] = []
        self.assertTrue(kompetens.kravbrister(kv, 'kritik_b'))

    def test_ofullstandig_observation_ar_aldrig_genomford(self):
        for change in ({'verifierad': False}, {'ofullstandig': True}, {'per_session': []},
                       {'sessioner': {'forvantade': 2, 'sedda': 1, 'saknade': []}}):
            kv = kvitto('skapa'); kv.update(change)
            self.assertTrue(kompetens.kravbrister(kv, 'skapa'))

    def test_varje_obligatorisk_tjanst_behover_sitt_resultat(self):
        for m in ('refero', 'mobbin', '21st'):
            kv = kvitto('forska'); kv['mcp_utfall'][f'mcp__{m}__search'] = {'tomt resultat': 1}
            self.assertTrue(any(m in s for s in kompetens.kravbrister(kv, 'forska')))

    def test_skaparen_far_anvanda_redan_hamtat_material(self):
        kv = kvitto('skapa'); kv['mcp_utfall'] = {}
        self.assertEqual(kompetens.kravbrister(kv, 'skapa'), [])

    def test_21st_undersoks_fore_planen(self):
        k = kompetens.tolka()
        for p in ('forska', 'planera', 'planprovning', 'skapa', 'fordjupa'):
            self.assertIn('mcp__21st__get_component', kompetens.mcp_for_pass(p, k))
        self.assertIn('21st', k['forska'].get('mcp_krav', []))
        prompt = '\n'.join(kompetens.prompt_rader('forska', 'syntetiskt-prov'))
        self.assertIn('get_component', prompt)
        self.assertIn('licens', prompt)
        self.assertIn('beroenden', prompt)

    def test_obligatoriskt_mcp_maste_ha_tillgang(self):
        text = kompetens.metod.KARTA.read_text()
        text = text.replace('mcp-krav: refero, mobbin, 21st', 'mcp-krav: refero, mobbin, 21st, okand')
        self.assertTrue(any('MCP-kravet okand' in f for f in kompetens.prova(text)))

    def test_partiell_observation_ger_inte_globalt_laddad(self):
        kv = kvitto('skapa')
        kv['ofullstandig'] = True
        kv['sessioner'].update(forvantade=2, saknade=[{'session': 'saknad'}])
        self.assertIsNone(kompetens.anvandningsnivaer(kv)['laddad']['varde'])
        kv['ofullstandig'] = False
        kv['sessioner'].update(forvantade=1, saknade=[])
        self.assertIs(kompetens.anvandningsnivaer(kv)['laddad']['varde'], True)

    def test_partiell_observation_ger_inte_karna_last_hel(self):
        kv = kvitto('skapa')
        kv['ofullstandig'] = True
        kv['sessioner'].update(forvantade=2, saknade=[{'session': 'saknad'}])
        roller = kompetens.tillstand(kv, 'skapa')
        self.assertTrue(roller)
        self.assertTrue(all(r['karna']['tillstand'] == kompetens.TILLSTAND['ej_observerat'] for r in roller))
        self.assertTrue(all(r['karna']['lasta'] for r in roller), 'det som observerats får stå som antal')
        kv['ofullstandig'] = False
        kv['sessioner'].update(forvantade=1, saknade=[])
        self.assertTrue(all(r['karna']['tillstand'] == kompetens.LASKVITTO for r in kompetens.tillstand(kv, 'skapa')))

    def test_mcp_resultat_raknas_over_alla_verktyg(self):
        ut = kompetens.mcp_tillstand('21st', 5, {
            'mcp__21st__search': {'anrop lyckades': 3},
            'mcp__21st__get_component': {'anrop lyckades': 2},
        }, {'21st': 'ansluten'}, True)
        self.assertEqual(ut.get('med_innehall'), 5)


if __name__ == '__main__':
    unittest.main()
