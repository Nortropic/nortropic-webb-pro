#!/usr/bin/env python3
"""Flödets verkliga kopplingar med syntetisk extern inspektion; inga nät- eller modellkonton."""
import contextlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('NWP_PROV_ROOT') or Path(__file__).resolve().parents[3])
sys.path.insert(0, str(ROOT / 'kontroller'))
import atelje
import kandidater as kd
import kompetens
import korregister
import skapande
import urval
import webbtjanst


class Kopplingar(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kompetenskopplingarnas prov'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        self.slug = 'koppling-prov'
        self.r = kd.rot(self.slug); self.r.mkdir(parents=True)
        self.k = {f: 'Syntetiskt' for f, _ in kd.PLANFALT}
        self.k.update(titel='Egen komposition', huvudreferens='egen riktning', referensbilder=[])
        # referenskontraktet: planen och UPPDRAG.md uppfyller det, så att provet prövar profileringen och inte startvillkoret
        import referensfixtur
        plan = referensfixtur.uppfyll(atelje.UNDERLAG, self.slug, {'kandidater': {'k01': self.k}})
        self.k = plan['kandidater']['k01']
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        kd.skriv_uppdrag(self.slug, 'k01', self.k, 1, 1)
        (self.r / kd.UPPDRAGSMATERIAL).write_text('{}')

    def test_inspektionen_ligger_i_kandidatens_kedja_och_en_brist_ar_underlag(self):
        # Ägarens förenklingsuppdrag 2026-10-10, D: profilen beställs i kandidatens kedja, inte i ett gemensamt steg före
        # alla skapare. Ägarens uppdrag 2026-10-11 om designflödet: en ofullständig profil är underlag, inte en spärr; skaparen
        # startar och får bristen i sin prompt. Bara den externa inspektionen ersätts.
        kd.satt_status(self.slug, 'k01', 'planerad', 'uppdraget skrivet', forsok=0)
        with patch.object(kd, 'profilrapport', return_value={'ok': False, 'brister': ['k01: syntetisk profilbrist']}) as profil:
            self.assertTrue(kd.referensprofil_klar(self.slug, 'k01'))
        profil.assert_called_once_with(self.slug, 'k01')
        st = kd.las_status(self.slug, 'k01')
        self.assertEqual((st['status'], st['skal']), ('planerad', 'uppdraget skrivet'), 'skaparen får börja; statusen står kvar')
        self.assertEqual(st['referensprofil']['brister'], ['k01: syntetisk profilbrist'])
        self.assertEqual(st['referensprofil']['tillstand'], 'ofullstandig')
        self.assertIsNone(st.get('referensprofil_brister'), 'ingen spärr sparas')
        self.assertFalse(kd.ska_skapas(dict(st, status='fel')), 'en profilbrist gör inget fel till ett omförsök')
        with patch.multiple(kd, metodinfo=lambda *a: {'sha': 'metod', 'delar': {'före': ['METOD-skiss.md']}},
                            uppdragsmaterial_rader=lambda *a: [], historik_rader=lambda *a: [], metodvariant=lambda *a: 'grund'), \
             patch.object(skapande, 'kritikrader', lambda *a, **k: []), patch.object(kompetens, 'prompt_rader', lambda *a, **k: []):
            prompt = kd.skiss_prompt(self.slug, 'k01')
        self.assertIn('DevTools-profilen för huvudreferensen blev ofullständig (k01: syntetisk profilbrist)', prompt)
        self.assertIn('SEKTIONER.md', prompt)
        # körningen har inget gemensamt profilsteg före poolen: poolen startar, och brister stannar i kandidaterna
        with patch.multiple(kd, STOPP_EFTER='', lista=lambda _: ['k01'], leverera_metod=lambda _: {},
                            planprovning_behov=lambda *a: [], korlage=lambda *a: 'skiss', material_behov=lambda *a: [],
                            las_status=lambda *a: {'status': 'planerad'}, forsta_valbara=lambda *a: None), \
             patch.object(kompetens, 'kravbrister', return_value=[]), \
             patch.object(urval, 'vid_start', return_value={}), \
             patch.object(kd, 'profilrapport') as profil2, patch.object(kd, 'kor_pool') as pool:
            kd.kor(self.slug, {}, lambda: None, n=1)
            profil2.assert_not_called()
            pool.assert_called_once()

    def test_brist_sparas_och_blir_inte_bara_ett_undantag(self):
        import referensprofil
        with patch.object(referensprofil, 'forbered', return_value={'ok': False, 'brister': ['syntetisk brist'], 'kandidater': {}}):
            rapport = referensprofil.for_kandidat(self.slug, 'k01', 'metod', underlag=atelje.UNDERLAG)
        sparad = json.loads(referensprofil.kandidatrapport(self.slug, 'k01', atelje.UNDERLAG).read_text())
        self.assertFalse(sparad['ok'])
        self.assertEqual(sparad, rapport)
        self.assertEqual(sparad['uppdrag']['k01'], kd.uppdrag_sha(self.k))
        self.assertEqual(referensprofil.kandidatrapport(self.slug, 'k01', atelje.UNDERLAG).parent, kd.kdir(self.slug, 'k01'))

    def test_redan_klar_skapares_aterupptagning_bestaller_inget(self):
        with patch.multiple(kd, STOPP_EFTER='', lista=lambda _: ['k01'], leverera_metod=lambda _: {},
                            planprovning_behov=lambda *a: [], korlage=lambda *a: 'skiss',
                            las_status=lambda *a: {'status': 'klar'}, forsta_valbara=lambda *a: None), \
             patch.object(kompetens, 'kravbrister', return_value=[]), \
             patch.object(urval, 'vid_start', return_value={}), \
             patch.object(kd, 'profilrapport') as profil, patch.object(kd, 'kor_pool'):
            self.assertEqual(kd.kor(self.slug, {}, lambda: None, n=1), ['k01'])
            profil.assert_not_called()

    def test_uppdraget_far_bara_sin_bundna_profil(self):
        rapport = {'ok': True, 'uppdrag': {'k01': kd.uppdrag_sha(self.k)}, 'kandidater': {
            'k01': {'tillstand': 'genomford', 'profiler': [{'namn': 'Egen', 'adress': 'https://referens.example/',
                     'paket': 'paket-v01', 'fil': 'BUNDEN-PROFIL.md'}], 'brister': []}}}
        (self.r / 'REFERENSPROFILER.json').write_text(json.dumps(rapport))
        kd.skriv_uppdrag(self.slug, 'k01', self.k, 1, 1)
        self.assertIn('BUNDEN-PROFIL.md', (kd.kdir(self.slug, 'k01') / 'UPPDRAG.md').read_text())
        kd.skriv_uppdrag(self.slug, 'k01', dict(self.k, ide='Ändrat uppdrag'), 1, 1)
        self.assertNotIn('BUNDEN-PROFIL.md', (kd.kdir(self.slug, 'k01') / 'UPPDRAG.md').read_text())
        # kandidatens egen rapport (kedjan per kandidat) når skaparen i prompten, bunden till uppdraget; UPPDRAG.md ändras inte
        (self.r / 'REFERENSPROFILER.json').unlink()
        kd.skriv_uppdrag(self.slug, 'k01', self.k, 1, 1)
        fore = (kd.kdir(self.slug, 'k01') / 'UPPDRAG.md').read_bytes()
        egen = json.loads(json.dumps(rapport))
        egen['kandidater']['k01']['profiler'][0]['fil'] = 'EGEN-PROFIL.md'
        (kd.kdir(self.slug, 'k01') / 'REFERENSPROFIL.json').write_text(json.dumps(egen))
        self.assertIn('EGEN-PROFIL.md', '\n'.join(kd.profil_rader(self.slug, 'k01')))
        import inspect
        self.assertIn('profil_rader(slug, kid)', inspect.getsource(kd.skiss_prompt))
        self.assertIn('profil_rader(slug, kid)', inspect.getsource(kd.skapar_prompt))
        kd.skriv_uppdrag(self.slug, 'k01', self.k, 1, 1)
        self.assertEqual((kd.kdir(self.slug, 'k01') / 'UPPDRAG.md').read_bytes(), fore, 'samma uppdrag skrivs inte om')
        plan = json.loads((self.r / 'KANDIDATPLAN.json').read_text())
        plan['kandidater']['k01']['ide'] = 'ett ändrat uppdrag'
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        self.assertEqual(kd.profil_rader(self.slug, 'k01'), [], 'en profil för ett äldre uppdrag ges inte')

    def test_gamla_obundna_profiler_injiceras_inte_i_researchen(self):
        with patch.object(kd, 'devtools_profiler', return_value=[{'vard': 'GAMMAL-PROFIL', 'fil': self.r / 'gammal.md'}]), \
             patch.object(skapande, 'senaste_paket', return_value=None):
            self.assertNotIn('GAMMAL-PROFIL', '\n'.join(kd.research_rader(self.slug)))

    def test_skillskript_nar_skaparen_men_inte_blind_kritik(self):
        self.assertTrue(any('skillskript.py ' + self.slug + ' --kandidat k01 --uppdrag' in s
                            for s in kompetens.verktyg('skapa', self.slug, 'k01')))
        for roll in ('skisskritik', 'kritik_a', 'fore_efter'):
            self.assertFalse(any('skillskript' in s for s in kompetens.verktyg(roll, self.slug, 'k01')))

    def test_canvas_tjansten_tar_bara_eget_uppdrag(self):
        argv = [self.slug, '--kandidat', 'k01', '--uppdrag', 'underlag/' + self.slug + '/atelje/kandidater/k01/uppdrag.json']
        kmd, fel = webbtjanst.granska_anrop('skillskript-canvas', argv, self.slug, (), root=self.tmp)
        self.assertIsNone(fel)
        self.assertIn('--bara-canvas', kmd)
        argv[-1] = 'underlag/annan-kund/uppdrag.json'
        kmd, fel = webbtjanst.granska_anrop('skillskript-canvas', argv, self.slug, (), root=self.tmp)
        self.assertIsNone(kmd)
        self.assertTrue(fel)


if __name__ == '__main__':
    unittest.main()
