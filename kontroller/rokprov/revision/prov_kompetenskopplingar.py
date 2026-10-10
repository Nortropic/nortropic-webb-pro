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

    def test_inspektionen_ligger_fore_skaparpoolen_och_stoppar_vid_brist(self):
        # Bara observations-/inspektionsutfallet ersätts. Drivarens ordning och felväg körs.
        with patch.multiple(kd, STOPP_EFTER='', lista=lambda _: ['k01'], leverera_metod=lambda _: {},
                            planprovning_behov=lambda *a: [], korlage=lambda *a: 'skiss',
                            las_status=lambda *a: {'status': 'planerad'}), \
             patch.object(kompetens, 'kravbrister', return_value=[]), \
             patch.object(urval, 'vid_start', return_value={}), \
             patch.object(kd, 'forbered_referensprofiler', side_effect=RuntimeError('syntetisk profilbrist'), create=True) as profil, \
             patch.object(kd, 'kor_pool') as pool:
            with self.assertRaisesRegex(RuntimeError, 'profilbrist'):
                kd.kor(self.slug, {}, lambda: None, n=1)
            profil.assert_called_once_with(self.slug, ['k01'])
            pool.assert_not_called()

    def test_brist_sparas_och_blir_inte_bara_ett_undantag(self):
        import referensprofil
        with patch.object(referensprofil, 'forbered', return_value={'ok': False, 'brister': ['syntetisk brist']}), \
             patch.object(kd, 'metodinfo', return_value={'sha': 'metod'}):
            with self.assertRaisesRegex(RuntimeError, 'syntetisk brist'):
                kd.forbered_referensprofiler(self.slug, ['k01'])
        rapport = json.loads((self.r / 'REFERENSPROFILER.json').read_text())
        self.assertFalse(rapport['ok'])
        self.assertEqual(rapport['uppdrag']['k01'], kd.uppdrag_sha(self.k))

    def test_redan_klar_skapares_aterupptagning_bestaller_inget(self):
        with patch.multiple(kd, STOPP_EFTER='', lista=lambda _: ['k01'], leverera_metod=lambda _: {},
                            planprovning_behov=lambda *a: [], korlage=lambda *a: 'skiss',
                            las_status=lambda *a: {'status': 'klar'}, forsta_valbara=lambda *a: None), \
             patch.object(kompetens, 'kravbrister', return_value=[]), \
             patch.object(urval, 'vid_start', return_value={}), \
             patch.object(kd, 'forbered_referensprofiler', create=True) as profil, patch.object(kd, 'kor_pool'):
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
