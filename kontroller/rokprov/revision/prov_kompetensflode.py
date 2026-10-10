#!/usr/bin/env python3
"""Kompetenskraven används vid flödets riktiga ingångar, med lokala syntetiska kvitton.

Attrapper vid modell, fotografering och kompetensobservation. Kravtolkarens egna fall ligger i kompetensprovet;
detta prov visar att beroende steg stannar och att kvittot sparas. Ingen extern session eller kundinformation.
"""
import contextlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import kandidater as kd
import kompetens
import korregister
import skapande
import forberedelse


def giltigt_kvitto(pass_):
    """Explicit syntetiskt observationsunderlag för fixturer som prövar andra flödeskontrakt.

Det ersätter bara observerad modellanvändning, aldrig kravtolkaren eller flödets grindar.
"""
    filer = kompetens.lasfiler(pass_)
    roller = kompetens.for_pass(pass_)
    skills, _ = kompetens.aktiverbara([f for r in roller for f in r['karna']])
    per = {'session': 'syntetisk', 'lasta': filer, 'saknas': [], 'fore_forsta_andring': filer,
           'skill_anrop': skills, 'skill_fore': skills, 'andrade': True, 'valda': []}
    return {'verifierad': True, 'ofullstandig': False, 'filer': filer, 'lasta': filer, 'saknas': [],
            'fore_forsta_andring': filer, 'skill_anrop': skills, 'skill_fel': [], 'per_session': [per],
            'sessioner': {'forvantade': 1, 'sedda': 1, 'saknade': []}, 'valda': [],
            'mcp_utfall': {'mcp__%s__syntetiskt_prov' % m: {'anrop lyckades': 1}
                          for r in roller for m in r.get('mcp_krav', [])}}


class Kompetensflode(unittest.TestCase):
    SLUG = 'kompetens-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kompetensflödets prov'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        self.r = kd.rot(self.SLUG); self.r.mkdir(parents=True)
        self.kv = {'verifierad': True, 'ofullstandig': False, 'filer': ['prov.md'], 'lasta': ['prov.md'],
                   'saknas': [], 'fore_forsta_andring': ['prov.md'], 'skill_anrop': ['prov-skill'],
                   'sessioner': {'forvantade': 1, 'sedda': 1, 'saknade': []}, 'per_session': [], 'tillstand': []}
        self.brist = ['obligatorisk Skill-aktivering saknas']
        self.grind = self.stack.enter_context(patch.object(kompetens, 'kravbrister', side_effect=lambda *a, **k: self.brist[:], create=True))
        self.stack.enter_context(patch.object(kompetens, 'kvitto', side_effect=lambda *a, **k: dict(self.kv)))
        self.stack.enter_context(patch.multiple(kompetens, prompt_rader=lambda *a, **k: [], verktyg=lambda *a, **k: []))
        self.stack.enter_context(patch.multiple(kd, forska_prompt=lambda *a, **k: 'research', plan_prompt=lambda *a, **k: 'plan',
            skiss_prompt=lambda *a, **k: 'skiss', uppdrag_prompt=lambda *a, **k: 'förfina', verktyg=lambda *a, **k: [],
            forfina_verktyg=lambda *a, **k: [], andra_nekas=lambda *a, **k: [], regel_rader=lambda: [],
            metod_rader=lambda *a, **k: [], research_rader=lambda *a: [], material_rader=lambda *a: [],
            metodinfo=lambda *a: {'sha': 'metod'}, skaparval=lambda *a: {}, metodvariant=lambda *a: 'grund',
            forbered_projekt=lambda *a: None, stilpaket_i_projekt=lambda *a: None, varvnummer=lambda *a: [],
            kopiera_bilder=lambda *a: [], material_anvandning=lambda *a: {}, bevara_version=lambda *a, **k: None,
            designkontroll=lambda *a: {'ok': True, 'fel': []}, lasningen=lambda *a: {}, varv_antal=lambda *a, **k: 1))
        self.stack.enter_context(patch.multiple(skapande, fakta_rader=lambda *a, **k: [], kritikrader=lambda *a, **k: [],
                                               forbjudna_termer=lambda *a, **k: {}, senaste_paket=lambda *a: None))
        self.so = {}
        self.calls = []
        def session(*a, **kw):
            self.calls.append(a[0])
            return {'structured_output': self.so, 'session_id': 'syntetisk-session'}
        self.stack.enter_context(patch.object(atelje, 'session', session))
        self.stack.enter_context(patch.dict(os.environ, {'NWP_SKISSKRITIK': 'av'}))
        self.stack.enter_context(patch.object(kd, 'fotografera', side_effect=lambda slug, kid, **kw:
            kd.satt_status(slug, kid, 'klar', 'fotograferad', version='efter', axe={'allvarliga': 0})))
        self.ater = self.stack.enter_context(patch.object(kd, 'aterstall_och_fotografera', side_effect=lambda slug, kid, v:
            kd.satt_status(slug, kid, 'klar', 'återställd', version=v, axe={'allvarliga': 0})))

    def plan(self):
        k = dict({f: 'syntetiskt värde' for f, _ in kd.PLANFALT}, titel='Förslag', huvudreferens='egen riktning', referensbilder=[])
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {'k01': k}, 'lage': 'skiss'}))
        kd.satt_status(self.SLUG, 'k01', 'planerad', 'syntetiskt', version='fore')
        return k

    def test_research_utan_kompetens_stoppar_fore_hamtning_och_sparar_kvitto(self):
        with patch.object(skapande, 'komplettera') as hamta:
            with self.assertRaisesRegex(RuntimeError, 'kompetens'):
                kd.forska(self.SLUG, 1, skiss=True)
        hamta.assert_not_called()
        post = json.loads((self.r / 'FORSKNING.json').read_text())
        self.assertEqual(post['kompetens']['skill_anrop'], ['prov-skill'])
        self.assertEqual(post['kompetenskravbrister'], self.brist)

    def test_planering_sparar_kvitto_och_stoppar_brister(self):
        self.so = {'variation': 'syntetisk', 'kandidater': [self.plan()]}
        (self.r / 'KANDIDATPLAN.json').unlink()
        with self.assertRaisesRegex(RuntimeError, 'kompetens'):
            kd.planera(self.SLUG, 1, 'skiss')
        self.assertFalse((self.r / 'KANDIDATPLAN.json').exists())
        self.brist = []
        self.assertEqual(kd.planera(self.SLUG, 1, 'skiss'), ['k01'])
        post = json.loads((self.r / 'KANDIDATPLAN.json').read_text())
        self.assertEqual(post['kompetens']['skill_anrop'], ['prov-skill'])

    def test_planprovning_utan_kompetens_andrar_eller_godkanner_inte(self):
        self.plan()
        fore = (self.r / 'KANDIDATPLAN.json').read_bytes()
        self.so = {'sammanfattning': 'bedömd', 'kandidater': [{'id': 'k01', 'bedomning': 'uppdraget bär',
                   'andringar': [{'falt': 'typografi', 'nytt': 'otillåten ändring', 'skill': 'prov', 'varfor': 'x'}]}]}
        kd.planprovning(self.SLUG)
        post = json.loads((self.r / 'PLANPROVNING.json').read_text())
        self.assertEqual(post['provade'], {})
        self.assertEqual(post['kompetenskravbrister'], self.brist)
        self.assertEqual((self.r / 'KANDIDATPLAN.json').read_bytes(), fore)

    def test_skiss_utan_kompetens_ar_inte_klar(self):
        self.plan()
        st = kd.skissa(self.SLUG, 'k01')
        self.assertEqual(st['status'], 'ofullstandig')
        self.assertEqual(st['kompetenskravbrister'], self.brist)
        self.assertFalse(st['tekniskt_fel'], 'en kompetensbrist ska inte skapa en automatisk omkörningsslinga')

    def test_huvudforfining_sparar_kvitto_och_aterstaller_vid_brist(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'vald', 'syntetiskt', version='fore')
        with patch.object(kd, 'efter_fordjupning') as efter:
            st = kd.forfina_kandidat(self.SLUG, 'k01', 'fore', {'tid': 'syntetisk-dom', 'uppdrag': {'typ': 'ratta', 'resultat': 'syntetisk rättelse', 'omfattning': ['rubriken'], 'bevara': ['övrigt']}})
        efter.assert_not_called()
        self.assertEqual(st['status'], 'vald')
        self.assertEqual(st['version'], 'fore')
        self.assertEqual(st['forfining']['kompetenskravbrister'], self.brist)
        self.assertEqual(st['forfining']['kompetens']['skill_anrop'], ['prov-skill'])

    def test_specialistens_saknade_aktivering_aterstalls_efter_bada_forsoken(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'syntetiskt', version='fore')
        bild = self.tmp / 'prov.png'; bild.write_bytes(b'png')
        self.so = {'kod_andrad': [{'skill': 'prov-skill', 'vad': 'kontrast'}],
                   'beteende_provat': [{'vad': 'fokus', 'hur': 'syntetiskt', 'resultat': 'synligt', 'bild': str(bild)}],
                   'visuell_bedomning': {'omdome': 'battre'}, 'ingen_andring': ''}
        with patch.object(kd, 'pass_prompt', return_value='specialist'), patch.object(kd, 'anvanda_verktyg', return_value=['förhandsvisning']):
            st = kd.kompetenspass(self.SLUG, 'k01', 'granskning', 'prov')
        rec = st['kompetens']['prov:granskning']
        self.assertEqual(len(self.calls), 2, 'det befintliga avgränsade omförsöket måste pröva kompetensbristen')
        self.assertEqual(st['version'], 'fore')
        self.assertFalse(rec['genomford'])
        self.assertEqual(rec['kompetenskravbrister'], self.brist)

    def test_okant_specialistkvitto_lamnar_inte_andringen_kvar(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'syntetiskt', version='fore')
        self.kv['verifierad'] = False
        self.brist = ['kompetensens observation saknas']
        self.so = {'ingen_andring': '', 'kod_andrad': [{'skill': 'prov-skill', 'vad': 'kontrast'}]}
        with patch.object(kd, 'pass_prompt', return_value='specialist'):
            st = kd.kompetenspass(self.SLUG, 'k01', 'granskning', 'prov')
        self.assertEqual(st['version'], 'fore')
        self.assertIsNone(st['kompetens']['prov:granskning']['genomford'])
        self.assertFalse(st['kompetens']['prov:granskning']['uppfyllt'])

    def test_planprovningens_cache_utan_kompetens_ateranvands_inte(self):
        self.plan()
        gammal = {'tid': 'före', 'provade': {'k01': 'gammal'}, 'kvitto': {}, 'kandidater': []}
        (self.r / 'PLANPROVNING.json').write_text(json.dumps(gammal))
        self.so = {'kandidater': [], 'sammanfattning': 'nytt försök'}
        post = kd.planprovning(self.SLUG)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(post['provade'], {})
        self.assertEqual(json.loads((self.r / 'PLANPROVNING-tidigare-1.json').read_text()), gammal)

    def test_forfiningens_cache_utan_kompetens_startar_inte_specialistpass(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'syntetiskt', version='fore', forfining={'dom': 'a'})
        with patch.object(kd, 'efter_fordjupning') as efter, self.assertRaisesRegex(RuntimeError, 'kompetens'):
            kd.forfina_kandidat(self.SLUG, 'k01', 'fore', {'tid': 'a', 'uppdrag': {'typ': 'ratta', 'resultat': 'syntetisk rättelse', 'omfattning': ['rubriken'], 'bevara': ['övrigt']}})
        efter.assert_not_called()

    def test_specialistcache_saknat_kvitto_ar_inte_uppfylld(self):
        self.assertFalse(kd.pass_uppfyllt({'genomford': True, 'uppfyllt': True, 'pass': 'granskning'}))

    def test_fullskaparens_brist_blir_ofullstandig_med_kvitto(self):
        self.plan()
        with patch.object(kd, 'skapar_prompt', return_value='skaparen'):
            st = kd.skapa(self.SLUG, 'k01')
        self.assertEqual(st['status'], 'ofullstandig')
        self.assertEqual(st['kompetens']['full:skapa']['kompetenskravbrister'], self.brist)
        self.assertEqual(len(self.calls), 1)

    def test_objektiv_forbattring_utan_kompetens_aterstaller(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'klar', 'syntetiskt', version='fore')
        with patch.object(kd, 'skapar_prompt', return_value='rätta en avvikelse'), \
             patch.object(kd, 'objektiva', return_value=['syntetiskt objektivt fel']):
            st = kd.forbattra(self.SLUG, 'k01')
        self.assertEqual(st['version'], 'fore')
        self.assertFalse(st['forbattrad']['uppfyllt'])
        self.assertEqual(st['forbattrad']['kompetenskravbrister'], self.brist)

    def test_kritikcache_utan_bada_passen_styr_inga_atgarder(self):
        self.plan()
        kritik = {'last': True, 'version': 'fore', 'avvikelser': [
            {'slag': 'krav', 'allvar': 'hog', 'var': 'syntetisk', 'vad': 'x', 'atgard': 'y'}]}
        self.assertEqual(kd.objektiva(self.SLUG, 'k01', kritik), [])
        self.assertFalse(kd.kritik_giltig(kritik, 'fore'))
        self.brist = []
        self.assertTrue(kd.kritik_giltig(kritik, 'fore'))
        self.assertEqual(len(kd.objektiva(self.SLUG, 'k01', kritik)), 1)
        self.assertFalse(kd.kritik_giltig(kritik, 'annan'))

    def test_skisscache_utan_kompetens_startar_inget_och_skriver_inte_om(self):
        import ab
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'klar', 'syntetiskt', version='fore')
        fore = (kd.kdir(self.SLUG, 'k01') / 'STATUS.json').read_bytes()
        with patch.object(ab, 'skisskrav'), patch.object(ab, 'skissavslutad', return_value={}) as avsluta, \
             patch.object(kd, 'skissa') as skapa:
            with self.assertRaisesRegex(RuntimeError, 'kompetens'):
                kd.behandla_skiss(self.SLUG, 'k01')
        skapa.assert_not_called()
        avsluta.assert_not_called()
        self.assertEqual((kd.kdir(self.SLUG, 'k01') / 'STATUS.json').read_bytes(), fore)

    def test_forberedelsen_sparar_brister_och_publicerar_inget(self):
        status = {}
        with patch.object(forberedelse, 'krav'), patch.object(forberedelse, 'giltig', return_value=False), \
             patch.object(forberedelse, 'prompt', return_value='förbered'), patch.object(forberedelse, 'publicera') as pub:
            self.so = {'klar': True, 'saknas': []}
            with self.assertRaisesRegex(RuntimeError, 'kompetens'):
                forberedelse.kor(self.SLUG, status, lambda: None)
        pub.assert_not_called()
        self.assertEqual(status['forberedelse']['kompetenskravbrister'], self.brist)
        kvitton = list((self.r / 'forberedelse').glob('*/KOMPETENS.json'))
        self.assertEqual(len(kvitton), 1)
        self.assertEqual(json.loads(kvitton[0].read_text())['kompetenskravbrister'], self.brist)

    def test_forberedelsens_publicering_sjalv_nekar_saknat_kvitto(self):
        paket = self.r / 'paket'; paket.mkdir()
        for namn in forberedelse.FILER:
            (paket / namn).write_text('syntetiskt utkast')
        with self.assertRaisesRegex(ValueError, 'kompetens'):
            forberedelse.publicera(self.SLUG, paket, forberedelse.indata(self.SLUG))
        self.assertFalse((atelje.UNDERLAG / self.SLUG / 'BRIEF.md').exists())


if __name__ == '__main__':
    unittest.main()
