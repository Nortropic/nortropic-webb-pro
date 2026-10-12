#!/usr/bin/env python3
"""Kompetenskraven vid flödets riktiga ingångar, med lokala syntetiska kvitton.

Attrapper vid modell, fotografering och kompetensobservation. Kravtolkarens egna fall ligger i kompetensprovet;
detta prov visar att kvittot sparas och redovisas som varning, och att beroende steg ändå fortsätter: ägarens besked
2026-10-12 ("Insatsen räknas, inte läsningen … Det fäller inte en version för oläst material"; kandidater.KVITTOVARNING).
Förberedelsen (forberedelse.py) ligger utanför den ändringen och prövas som förut. Ingen extern session eller kundinformation.
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
import referensfixtur  # referenskontraktets fixtur: paketet, genomgångarna och kedjan per kandidat


def giltigt_kvitto(pass_):
    """Explicit syntetiskt observationsunderlag för fixturer som prövar andra flödeskontrakt.

Det ersätter bara observerad modellanvändning, aldrig kravtolkaren eller flödets grindar.
"""
    eft = kompetens.efterfiler(pass_)  # granskningen efter renderingen (guidens ordning)
    filer = kompetens.lasfiler(pass_) + eft
    roller = kompetens.for_pass(pass_)
    skills, _ = kompetens.aktiverbara([f for r in roller for f in r['karna'] + r['efter']])
    per = {'session': 'syntetisk', 'lasta': filer, 'saknas': [], 'fore_forsta_andring': filer,
           'skill_anrop': skills, 'skill_fore': skills, 'efter_lasta': eft, 'andrade': True, 'valda': []}
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
            designkontroll=lambda *a: {'ok': True, 'fel': []}, lasningen=lambda *a: {}, varv_antal=lambda *a, **k: 1,
            referensprofil_klar=lambda *a: True))  # profilen i kandidatens kedja prövas i prov_forenkling
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
        plan = referensfixtur.uppfyll(atelje.UNDERLAG, self.SLUG, {'kandidater': {'k01': k}, 'lage': 'skiss'})  # startvillkoret släpper skaparen
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        referensfixtur.uppdrag(atelje.UNDERLAG, self.SLUG, plan, 'k01')
        kd.satt_status(self.SLUG, 'k01', 'planerad', 'syntetiskt', version='fore')
        return plan['kandidater']['k01']

    def test_research_med_kvittobrist_fortsatter_och_sparar_kvitto(self):
        self.so = {'varfor': 'syntetisk research', 'sajter': [], 'fragor': []}
        post = kd.forska(self.SLUG, 1, skiss=True)  # varken kvittot eller referenskontraktet stoppar researchen
        self.assertEqual(post['kompetens']['skill_anrop'], ['prov-skill'])
        self.assertEqual(post['kompetenskravbrister'], self.brist)
        self.assertIsNone(post['kompetensomforsok'], 'kvittot ger inget omförsök som kastar svaret')
        sparad = json.loads((self.r / 'FORSKNING.json').read_text())
        self.assertEqual(sparad['kompetenskravbrister'], self.brist)
        md = (self.r / 'FORSKNING.md').read_text()
        self.assertIn(kd.KVITTOVARNING, md)
        self.assertTrue(post['referenskontrakt']['brister'])  # utan paket: kontraktets brister står som varning
        self.assertIn('varning (redovisas, stoppar inte planen)', md)

    def test_research_utan_underlag_alls_stoppar(self):
        self.so = {}  # inget svar och inget referenspaket: där vore fortsatt arbete meningslöst
        with self.assertRaisesRegex(RuntimeError, 'inget underlag'):
            kd.forska(self.SLUG, 1, skiss=True)

    def test_planering_sparar_kvitto_och_planerar_med_brister(self):
        self.so = dict(referensfixtur.planfalt(self.SLUG), variation='syntetisk', kandidater=[self.plan()])
        (self.r / 'KANDIDATPLAN.json').unlink()
        paket = referensfixtur.paket(atelje.UNDERLAG, self.SLUG)  # planen binds till det fångade paketet (referenskontraktet)
        with patch.object(skapande, 'senaste_paket', lambda *a: paket):
            self.assertEqual(kd.planera(self.SLUG, 1, 'skiss'), ['k01'])  # kvittot stoppar inte planen
        self.assertEqual(len(self.calls), 1)
        post = json.loads((self.r / 'KANDIDATPLAN.json').read_text())
        self.assertEqual(post['kompetens']['skill_anrop'], ['prov-skill'])
        self.assertEqual(post['kompetenskravbrister'], self.brist)
        self.assertEqual(json.loads((self.r / 'PLANERING.json').read_text())['kompetenskravbrister'], self.brist)

    def test_planprovning_med_kvittobrist_provar_och_redovisar(self):
        self.plan()
        self.so = {'sammanfattning': 'bedömd', 'kandidater': [{'id': 'k01', 'bedomning': 'uppdraget bär',
                   'andringar': [{'falt': 'typografi', 'nytt': 'specialistens ändring', 'skill': 'prov', 'varfor': 'x'}]}]}
        kd.planprovning(self.SLUG)
        post = json.loads((self.r / 'PLANPROVNING.json').read_text())
        plan = json.loads((self.r / 'KANDIDATPLAN.json').read_text())
        self.assertEqual(post['provade'], {'k01': kd.uppdrag_sha(plan['kandidater']['k01'])}, 'kvittot gör inget uppdrag oprövat')
        self.assertEqual(post['kompetenskravbrister'], self.brist)
        self.assertEqual(plan['kandidater']['k01']['typografi'], 'specialistens ändring')
        self.assertEqual(kd.planprovning_behov(self.SLUG, ['k01']), [])

    def test_skiss_med_kvittobrist_ar_klar_och_valbar(self):
        self.plan()
        st = kd.skissa(self.SLUG, 'k01')
        self.assertEqual(st['status'], 'klar', 'kvittot gör aldrig en skiss ovalbar')
        self.assertIn(st['status'], kd.VISBARA)
        self.assertEqual(st['kompetenskravbrister'], self.brist)
        self.assertIn(kd.KVITTOVARNING, st['skal'])
        self.assertFalse(st['tekniskt_fel'], 'en kompetensbrist ska inte skapa en automatisk omkörningsslinga')

    def test_huvudforfining_sparar_kvitto_och_star_kvar_vid_brist(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'vald', 'syntetiskt', version='fore')
        with patch.object(kd, 'efter_fordjupning') as efter:
            kd.forfina_kandidat(self.SLUG, 'k01', 'fore', {'tid': 'syntetisk-dom', 'uppdrag': {'typ': 'ratta', 'resultat': 'syntetisk rättelse', 'omfattning': ['rubriken'], 'bevara': ['övrigt']}})
        efter.assert_called_once()  # kvittot kastar aldrig förfiningen
        self.ater.assert_not_called()
        st = kd.las_status(self.SLUG, 'k01')
        self.assertEqual(st['status'], 'forfinad')
        self.assertEqual(st['version'], 'efter')
        self.assertIn(kd.KVITTOVARNING, st['skal'])
        self.assertEqual(st['forfining']['kompetenskravbrister'], self.brist)
        self.assertEqual(st['forfining']['kompetens']['skill_anrop'], ['prov-skill'])

    def test_forfining_utan_andring_och_varv_star_inte(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'vald', 'syntetiskt', version='fore')
        self.brist = []
        with patch.object(kd, 'efter_fordjupning') as efter, patch.object(kd, 'varv_antal', return_value=0), \
             patch.object(kd, 'fotografera', side_effect=lambda slug, kid, **kw: kd.satt_status(slug, kid, 'klar', 'fotograferad', version='fore')):
            st = kd.forfina_kandidat(self.SLUG, 'k01', 'fore', {'tid': 'syntetisk-dom', 'uppdrag': {'typ': 'ratta', 'resultat': 'syntetisk rättelse', 'omfattning': ['rubriken'], 'bevara': ['övrigt']}})
        efter.assert_not_called()  # ett uppdrag som varken renderade eller ändrade något blir inte förfinat
        self.assertEqual(st['status'], 'vald')
        self.assertIn('ändrade inte versionen', st['skal'])

    def test_specialistens_saknade_aktivering_redovisas_och_andringen_star(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'syntetiskt', version='fore')
        bild = self.tmp / 'prov.png'; bild.write_bytes(b'png')
        self.so = {'kod_andrad': [{'skill': 'prov-skill', 'vad': 'kontrast'}],
                   'beteende_provat': [{'vad': 'fokus', 'hur': 'syntetiskt', 'resultat': 'synligt', 'bild': str(bild)}],
                   'visuell_bedomning': {'omdome': 'battre'}, 'ingen_andring': ''}
        with patch.object(kd, 'pass_prompt', return_value='specialist'), patch.object(kd, 'anvanda_verktyg', return_value=['förhandsvisning']):
            st = kd.kompetenspass(self.SLUG, 'k01', 'granskning', 'prov')
        rec = st['kompetens']['prov:granskning']
        self.assertEqual(len(self.calls), 1, 'kvittot ger inget omförsök som kastar passets arbete')
        self.ater.assert_not_called()
        self.assertEqual(st['version'], 'efter')
        self.assertTrue(rec['genomford'])
        self.assertTrue(kd.pass_uppfyllt(rec))
        self.assertEqual(rec['kompetenskravbrister'][:1], self.brist)
        self.assertIn(kd.KVITTOVARNING, rec['varning'])

    def test_okant_specialistkvitto_redovisas_och_andringen_star(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'syntetiskt', version='fore')
        self.kv['verifierad'] = False
        self.brist = ['kompetensens observation saknas']
        self.so = {'ingen_andring': '', 'kod_andrad': [{'skill': 'prov-skill', 'vad': 'kontrast'}]}
        with patch.object(kd, 'pass_prompt', return_value='specialist'):
            st = kd.kompetenspass(self.SLUG, 'k01', 'granskning', 'prov')
        self.assertEqual(st['version'], 'efter', 'ett okänt kvitto återställer inte passets arbete')
        self.ater.assert_not_called()
        self.assertIsNone(st['kompetens']['prov:granskning']['genomford'])  # inte observerat står som okänt
        self.assertFalse(st['kompetens']['prov:granskning']['uppfyllt'])

    def test_planprovningens_cache_ateranvands_med_kvittobrist(self):
        self.plan()
        gammal = {'tid': 'före', 'provade': {'k01': 'gammal'}, 'kvitto': {}, 'kandidater': []}
        (self.r / 'PLANPROVNING.json').write_text(json.dumps(gammal))
        self.so = {'kandidater': [], 'sammanfattning': 'nytt försök'}
        post = kd.planprovning(self.SLUG)
        self.assertEqual(len(self.calls), 0, 'en gjord prövning görs inte om för kvittots skull')
        self.assertEqual(post, gammal)
        self.assertFalse((self.r / 'PLANPROVNING-tidigare-1.json').exists())

    def test_forfiningens_cache_med_kvittobrist_fortsatter_till_specialistpassen(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'syntetiskt', version='fore', forfining={'dom': 'a'})
        with patch.object(kd, 'efter_fordjupning') as efter:
            kd.forfina_kandidat(self.SLUG, 'k01', 'fore', {'tid': 'a', 'uppdrag': {'typ': 'ratta', 'resultat': 'syntetisk rättelse', 'omfattning': ['rubriken'], 'bevara': ['övrigt']}})
        efter.assert_called_once()
        self.assertEqual(self.calls, [], 'en sparad förfining görs inte om')

    def test_specialistcache_avgors_av_insatsen_inte_kvittot(self):
        self.assertTrue(kd.pass_uppfyllt({'genomford': True, 'uppfyllt': True, 'pass': 'granskning'}))
        self.assertFalse(kd.pass_uppfyllt({'genomford': False, 'uppfyllt': False, 'pass': 'granskning'}))

    def test_fullskaparens_brist_redovisas_och_kandidaten_ar_klar(self):
        self.plan()
        with patch.object(kd, 'skapar_prompt', return_value='skaparen'):
            st = kd.skapa(self.SLUG, 'k01')
        self.assertEqual(st['status'], 'klar')
        self.assertIn(kd.KVITTOVARNING, st['skal'])
        self.assertEqual(st['kompetens']['full:skapa']['kompetenskravbrister'], self.brist)
        self.assertEqual(len(self.calls), 1)

    def test_objektiv_forbattring_med_kvittobrist_star_kvar(self):
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'klar', 'syntetiskt', version='fore')
        with patch.object(kd, 'skapar_prompt', return_value='rätta en avvikelse'), \
             patch.object(kd, 'objektiva', return_value=['syntetiskt objektivt fel']):
            st = kd.forbattra(self.SLUG, 'k01')
        self.ater.assert_not_called()
        self.assertEqual(st['version'], 'efter')
        self.assertTrue(st['forbattrad']['uppfyllt'])
        self.assertEqual(st['forbattrad']['kompetenskravbrister'], self.brist)
        self.assertIn(kd.KVITTOVARNING, st['skal'])

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

    def test_skisscache_med_kvittobrist_avslutas_utan_ny_skiss(self):
        import ab
        self.plan()
        kd.satt_status(self.SLUG, 'k01', 'klar', 'syntetiskt', version='fore')
        fore = (kd.kdir(self.SLUG, 'k01') / 'STATUS.json').read_bytes()
        with patch.object(ab, 'skisskrav'), patch.object(ab, 'skissavslutad', return_value={}) as avsluta, \
             patch.object(kd, 'skissa') as skapa:
            kd.behandla_skiss(self.SLUG, 'k01')  # den sparade skissen står, med kvittot redovisat
        skapa.assert_not_called()
        avsluta.assert_called_once()
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
