#!/usr/bin/env python3
"""Obligatorisk MCP-åtkomst före start; inga verkliga sessioner, tjänster eller konton.

--bas kör samma fall med HEAD:s startkontroll.py inläst i minnet.
"""
import contextlib
import copy
import inspect
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import kompetens
import korregister
import startkontroll as sk

if '--bas' in sys.argv:
    sys.argv.remove('--bas')
    src = subprocess.run(['git', 'show', 'HEAD:kontroller/startkontroll.py'], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
    bas = types.ModuleType('startkontroll_bas')
    bas.__file__ = str(ROOT / 'kontroller/startkontroll.py')
    exec(compile(src, bas.__file__, 'exec'), bas.__dict__)
    sk = bas


def session():
    return {'resultat': 'ok', 'servrar': {t: 'connected' for t in kompetens.MCP},
            'verktyg': [v for t in kompetens.MCP for v in kompetens.mcp_verktyg(t)],
            'flaggor': [], 'tid': 'syntetiskt-prov'}


class Startkompetens(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.rot = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'startkompetensprovet')))

    def atkomst(self, sess, vag=None):
        # Basen saknar fasparametern. Låt samma sakpåståenden pröva dess gamla beteende,
        # så en TypeError om signaturen aldrig räknas som regressionsbelägg.
        if vag is not None and 'vag' in inspect.signature(sk.atkomstrader).parameters:
            return sk.atkomstrader(sess, True, vag)
        return sk.atkomstrader(sess, True)

    def rad(self, sess, t, vag=None):
        return next(r for r in self.atkomst(sess, vag) if r['namn'] == sk.TJNAMN[t] + ' i ateljéns session')

    def kontroll(self, sess, vag=None, formaga=None):
        # Behåll den riktiga kor_kontroll + atkomstrader + mcp_atkomst + statusprövningen.
        # Ersätt bara oberoende inventering, maskin-/tjänsteprov och rapportdata.
        k = types.SimpleNamespace(katalog=self.rot, utfort=[], ateranvant=[])
        patchar = {
            'vanta_pa_intag': True, 'diskvakt': ({'grupp': 'disk', 'namn': 'diskvakten', 'resultat': 'ok'}, {}),
            'korvag': vag if vag is not None else {'id': 'kandidatflodet', 'namn': 'prov', 'fas': 'fore_research'},
            'prova_formagan': formaga if formaga is not None else ([], {}, sess, {}),
            'tjanstverktyg_rader': [], 'kunskap': [], 'regler': [],
            'uppdraget': [], 'bevakningen': [], 'referensunderlag': [], 'roller': [], 'las_for_korning': {},
            'till_byggaren': '', 'matinstrument': {}, 'repo_identitet': {'commit': 'syntetisk'}, 'dokumentationen': {},
        }
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sk.vl, 'Kontext', return_value=k))
            stack.enter_context(patch.object(sk.vl, 'inventera', return_value=[]))
            stack.enter_context(patch.object(sk.vl, 'las_json', return_value={}))
            for namn, value in patchar.items():
                stack.enter_context(patch.object(sk, namn, return_value=value))
            return sk.kor_kontroll(start='ny')

    def formaga(self, sess, vag, kundvakt='ok', direkt=None, anslutningar='fel', start='ny', maskin_extra=None):
        k = types.SimpleNamespace(prova=False, prov_dir=self.rot, katalog=self.rot)
        servrar = {t: {'status': anslutningar, 'besked': 'syntetiskt anslutningsbesked'} for t in ('refero', 'mobbin')}
        servrar.update(maskin_extra or {})
        direkt = direkt or {'refero': {'resultat': 'fel'}, 'mobbin': {'resultat': 'fel'}}
        vl_patchar = {'claude_bin': 'syntetisk-claude', 'flaggor_saknas': [], 'mcp_lista': (servrar, 'syntetisk'),
                     'prova_refero': direkt['refero'], 'prova_mobbin': direkt['mobbin'],
                     'prova_sessionen': sess, 'prova_vakten': {'resultat': kundvakt},
                     'prova_webblasaren': {'resultat': 'ok'}, 'prova_detektorn': {'resultat': 'ok'},
                     'kor': (0, 'v1'), 'venv_python': 'syntetisk-python'}
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sk, 'prova_modeller', return_value=[]))
            stack.enter_context(patch.object(sk.vl, 'Kontext', return_value=k))
            for namn, value in vl_patchar.items():
                stack.enter_context(patch.object(sk.vl, namn, return_value=value))
            if 'vag' in inspect.signature(sk.prova_formagan).parameters:
                return sk.prova_formagan(k, 'syntetisk', start, vag)
            return sk.prova_formagan(k, 'syntetisk', start)

    def test_varje_obligatorisk_tjanst_nekar_blockerad_atkomst(self):
        for t in ('refero', 'mobbin', '21st'):
            with self.subTest(t=t):
                s = session()
                s['servrar'][t] = 'failed'
                r = self.rad(s, t)
                self.assertTrue(r.get('nodvandig'), r)
                self.assertEqual((r['tillstand'], r['resultat']), ('blockerat', 'fel'))
                k = self.kontroll(s)
                self.assertEqual(k['status'], 'stoppad', k['stoppar'])
                self.assertTrue(any(sk.TJNAMN[t] in f for f in k['stoppar']))

    def test_observerad_anslutning_utan_verktygen_ar_blockerad(self):
        s = session()
        s['verktyg'] = [v for v in s['verktyg'] if not v.startswith('mcp__21st__')]
        r = self.rad(s, '21st')
        self.assertEqual((r['tillstand'], r['resultat']), ('blockerat', 'fel'))
        self.assertTrue(r.get('nodvandig'))
        self.assertEqual(self.kontroll(s)['status'], 'stoppad')

    def test_saknat_eller_felat_sessionsprov_ar_inte_startklart(self):
        for s in (None, {'resultat': 'fel', 'detalj': 'syntetiskt sessionsfel'}, {'resultat': 'okand'}, []):
            with self.subTest(sess=s):
                for t in ('refero', 'mobbin', '21st'):
                    r = self.rad(s, t)
                    self.assertEqual((r['tillstand'], r['resultat']), ('ej_observerat', 'fel'))
                    self.assertTrue(r.get('nodvandig'))
                self.assertEqual(self.kontroll(s)['status'], 'stoppad')

    def test_bara_tilldelad_motion_forblir_valbar(self):
        s = session()
        s['servrar']['motion'] = 'failed'
        r = self.rad(s, 'motion')
        self.assertEqual((r['tillstand'], r['resultat']), ('blockerat', 'fel'))
        self.assertFalse(r.get('nodvandig'))
        self.assertNotEqual(self.kontroll(s)['status'], 'stoppad')

    def test_kravet_kommer_fran_metodkartan_inte_tjanstens_namn(self):
        k = copy.deepcopy(kompetens.tolka())
        for x in k.values():
            x['mcp_krav'] = []
        k['forska']['mcp_krav'] = ['motion']
        k['forska']['mcp'].append('motion')
        s = session()
        s['servrar'].update({'motion': 'failed', '21st': 'failed'})
        with patch.object(kompetens, 'tolka', return_value=k):
            self.assertTrue(self.rad(s, 'motion').get('nodvandig'))
            self.assertFalse(self.rad(s, '21st').get('nodvandig'))
            q = self.kontroll(s)
            self.assertEqual(q['status'], 'stoppad')
            self.assertTrue(any('Motion' in f for f in q['stoppar']))
            self.assertFalse(any('21st.dev' in f for f in q['stoppar']))

    def test_bekraftad_atkomst_till_kraven_tillater_start(self):
        s = session()
        for t in ('refero', 'mobbin', '21st'):
            r = self.rad(s, t)
            self.assertTrue(r.get('nodvandig'))
            self.assertEqual((r['tillstand'], r['resultat']), ('provat', 'ok'))
        self.assertNotEqual(self.kontroll(s)['status'], 'stoppad')

    def test_research_kravs_fore_men_inte_ater_vid_forfining(self):
        s = session()
        s['servrar']['21st'] = 'failed'
        fore = {'id': 'kandidatflodet', 'fas': 'fore_research'}
        efter = {'id': 'kandidatflodet', 'fas': 'efter_research'}
        self.assertEqual(self.kontroll(s, fore)['status'], 'stoppad')
        r = self.rad(s, '21st', efter)
        self.assertEqual(r['tillstand'], 'blockerat')
        self.assertFalse(r.get('nodvandig'))
        self.assertNotEqual(self.kontroll(s, efter)['status'], 'stoppad')
        self.assertNotEqual(self.kontroll(None, efter)['status'], 'stoppad')

    def test_forberedelsen_kraver_bara_sina_egna_tjanster(self):
        vag = {'id': 'forberedelse', 'fas': 'forberedelse'}
        self.assertNotEqual(self.kontroll(None, vag)['status'], 'stoppad')
        k = copy.deepcopy(kompetens.tolka())
        k['forberedelse']['mcp'] = ['motion']
        k['forberedelse']['mcp_krav'] = ['motion']
        with patch.object(kompetens, 'tolka', return_value=k):
            r = self.rad(None, 'motion', vag)
            self.assertEqual(r['tillstand'], 'ej_observerat')
            self.assertTrue(r.get('nodvandig'))
            self.assertFalse(self.rad(None, '21st', vag).get('nodvandig'))
            self.assertEqual(self.kontroll(None, vag)['status'], 'stoppad')

    def test_okand_korvag_ger_inte_bekraftad_kravbedomning(self):
        vag = {'id': 'okand', 'fas': None}
        rader = self.atkomst(session(), vag)
        self.assertTrue(any(r.get('nodvandig') and r['resultat'] == 'fel'
                            and r['tillstand'] == 'ej_observerat' for r in rader), rader)
        self.assertEqual(self.kontroll(session(), vag)['status'], 'stoppad')

    def test_direktprovens_tjanster_foljer_samma_fas(self):
        s = session()
        for fas in ('fore_research', 'efter_research'):
            with self.subTest(fas=fas):
                vag = {'id': 'kandidatflodet', 'fas': fas}
                f = self.formaga(s, vag)
                rader = {r['namn']: r for r in f[0]}
                for n in ('refero', 'mobbin', 'Refero (direkt)', 'Mobbin (sökning och bilder)'):
                    self.assertEqual(rader[n]['tillstand'], 'blockerat')
                    self.assertEqual(bool(rader[n].get('nodvandig')), fas == 'fore_research', rader[n])
                kv = self.kontroll(s, vag, formaga=f)
                self.assertEqual(kv['status'], 'stoppad' if fas == 'fore_research' else 'begransad')

    def test_sakerhetsprovet_forblir_nodvandigt_efter_research(self):
        vag = {'id': 'kandidatflodet', 'fas': 'efter_research'}
        s = session()
        f = self.formaga(s, vag, kundvakt='fel')
        rad = next(r for r in f[0] if r['namn'] == 'kundvaktens mekanik')
        self.assertTrue(rad.get('nodvandig'))
        self.assertEqual(self.kontroll(s, vag, formaga=f)['status'], 'stoppad')

    def test_farsk_anslutning_ersatter_inte_gammalt_eller_saknat_direktprov(self):
        s = session()
        for t, namn in (('refero', 'Refero (direkt)'), ('mobbin', 'Mobbin (sökning och bilder)')):
            for prov in ({'resultat': 'ok', 'gammalt': True}, {'resultat': 'okand'}):
                for fas in ('fore_research', 'efter_research'):
                    with self.subTest(t=t, prov=prov, fas=fas):
                        vag = {'id': 'kandidatflodet', 'fas': fas}
                        direkt = {'refero': {'resultat': 'ok'}, 'mobbin': {'resultat': 'ok'}}
                        direkt[t] = prov
                        f = self.formaga(s, vag, direkt=direkt, anslutningar='ok')
                        rader = {r['namn']: r for r in f[0]}
                        self.assertEqual(rader[t]['resultat'], 'ok', 'anslutningen ska vara färsk och fungerande')
                        r = rader[namn]
                        self.assertEqual(r['tillstand'], 'ej_observerat')
                        self.assertEqual(bool(r.get('nodvandig')), fas == 'fore_research')
                        self.assertEqual(r['resultat'], 'fel' if fas == 'fore_research' else 'okand')
                        kv = self.kontroll(s, vag, formaga=f)
                        if fas == 'fore_research':
                            self.assertEqual(kv['status'], 'stoppad')
                            self.assertEqual(len(kv['stoppar']), 1, kv['stoppar'])
                            self.assertTrue(kv['stoppar'][0].startswith(namn + ':'))
                        else:
                            self.assertEqual(kv['status'], 'begransad')
                            self.assertEqual(kv['stoppar'], [])

    def test_metodkrav_som_inte_kan_lasas_ar_aldrig_valfria(self):
        for fel in (OSError('syntetiskt läsfel'), RuntimeError('syntetiskt tolkningsfel')):
            with self.subTest(fel=type(fel).__name__), patch.object(kompetens, 'tolka', side_effect=fel):
                r = sk.atkomstrader(session(), True)[0]
                self.assertEqual((r['resultat'], r['tillstand']), ('fel', 'ej_observerat'))
                self.assertTrue(r.get('nodvandig'))
                self.assertEqual(self.kontroll(session())['status'], 'stoppad')

    def test_helbygget_antas_inte_provat_med_ateljens_sessionsprov(self):
        self.assertEqual(sk.atkomstrader(None, False), [])

    def test_helbyggets_maskinlista_styr_inte_den_egna_mcp_konfigurationen(self):
        vag = {'id': 'helbygget', 'fas': 'bygge'}
        for lage in ('', 'av', 'kontroller/mcp/refero.json'):
            with self.subTest(lage=lage), patch.dict(os.environ, {'NWP_MCP_CONFIG': lage}):
                f = self.formaga(session(), vag, start='bygge')
                rader = {r['namn']: r for r in f[0]}
                for n in ('refero', 'mobbin', 'Refero (direkt)', 'Mobbin (sökning och bilder)'):
                    self.assertFalse(rader[n].get('nodvandig'), rader[n])
                self.assertIsNone(f[2], 'ateljéns sessionsprov bevisar inte helbyggets åtkomst')

    def test_motion_och_21st_ar_inte_maskinverktyg_utan_uppgift(self):
        extra = {t: {'status': 'fel', 'besked': 'syntetiskt fel'} for t in ('motion', '21st', 'utan-uppgift')}
        f = self.formaga(session(), {'id': 'kandidatflodet', 'fas': 'fore_research'}, maskin_extra=extra)
        r = next(r for r in f[0] if r['namn'] == 'övriga anslutningar (ingen uppgift i skapandet)')
        self.assertIn('utan-uppgift:', r['detalj'])
        self.assertNotIn('motion:', r['detalj'])
        self.assertNotIn('21st:', r['detalj'])


if __name__ == '__main__':
    unittest.main()
