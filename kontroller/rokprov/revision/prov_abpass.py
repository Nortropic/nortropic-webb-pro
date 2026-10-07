#!/usr/bin/env python3
"""A/B-mått knutna till rätt körning; inga riktiga sessioner."""
import contextlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import ab
import korregister


class Abpass(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetiskt A/B-mått')))
        self.stack.enter_context(patch.object(ab, 'KUNDER', self.root / 'kunder'))
        self.k = ab.KUNDER / 'prov-arm'; self.k.mkdir(parents=True)

    def logg(self, stampel, modell, **varden):
        p = self.k / ('korning-%s.jsonl' % stampel)
        p.write_text('\n'.join(json.dumps(x) for x in [
            {'type':'system','subtype':'init','model':modell}, {'type':'result', **varden}]))

    def test_slutposten_valjer_sin_egen_logg(self):
        self.logg('20260101T000000Z', 'syntetisk-a', num_turns=3, duration_ms=60000)
        self.logg('20260102T000000Z', 'syntetisk-b', num_turns=7, duration_ms=120000)
        post = {'korning':'20260101T000000Z','tillstand':{}}
        fil = self.k / 'korningar/20260101T000000Z/SLUT.json'
        with patch.object(ab.korslut, 'senaste_slutpost', return_value=(fil, post)):
            m = ab.matt('prov-arm')
        self.assertEqual(m['modell'], 'syntetisk-a')
        self.assertEqual(m['turer'], 3)
        self.assertEqual(m['minuter'], 1)

    def test_saknad_logg_lanar_inte_annan_korning(self):
        self.logg('20260102T000000Z', 'syntetisk-b', num_turns=7, duration_ms=120000)
        post = {'korning':'20260101T000000Z','tillstand':{}}
        fil = self.k / 'korningar/20260101T000000Z/SLUT.json'
        with patch.object(ab.korslut, 'senaste_slutpost', return_value=(fil, post)):
            m = ab.matt('prov-arm')
        self.assertIsNone(m['modell'])
        self.assertIsNone(m['minuter'])

    def test_okanda_matt_och_eftergrans(self):
        self.logg('20260101T000000Z', 'syntetisk-a', num_turns=3)
        with patch.object(ab.korslut, 'senaste_slutpost', return_value=(None, None)):
            m = ab.matt('prov-arm')
            self.assertIsNone(m['minuter'])
            self.assertIsNone(m['kontext_max'])
            self.assertIsNone(m['over_halva'])
            self.assertIsNone(ab.matt('prov-arm', efter='20260102T000000Z')['modell'])
        self.assertEqual(ab.kontextdjup([{'type':'assistant','message':{'usage':{'input_tokens':0,
                         'cache_creation_input_tokens':0,'cache_read_input_tokens':0}}}], 100)['kontext_max'], 0)
        self.assertEqual(ab.skillanrop([{'type':'assistant','message':{'content':[
            {'type':'tool_use','name':'Skill','input':['ogiltigt']}]}}]), {})

    def test_delvis_kontext_ar_inte_noll(self):
        m = ab.kontextdjup([{'type':'assistant','message':{}},
                           {'type':'assistant','message':{'usage':{'input_tokens':12}}}], None)
        self.assertIsNone(m['kontext_max'])
        self.assertEqual(m['observerad_kontext_max'], 12)
        self.assertIsNone(m['over_halva'])

    def test_fonstret_antas_inte_ur_modellnamnet(self):
        self.logg('20260101T000000Z', 'syntetisk-a', duration_ms=60000, num_turns=1)
        fil = self.k / 'korning-20260101T000000Z.jsonl'
        with fil.open('a') as f:
            f.write('\n' + json.dumps({'type':'assistant','message':{'usage':{
                'input_tokens':600000,'cache_creation_input_tokens':0,'cache_read_input_tokens':0}}}))
        with patch.object(ab.korslut, 'senaste_slutpost', return_value=(None, None)):
            m = ab.matt('prov-arm')
        self.assertEqual(m['kontext_max'], 600000)
        self.assertIsNone(m['over_halva'])

    def test_trasig_terminalrad_och_meddelande(self):
        self.logg('20260101T000000Z', 'syntetisk-a', duration_ms=60000, num_turns=1,
                  modelUsage={'syntetisk-a':{'contextWindow':100}})
        fil = self.k / 'korning-20260101T000000Z.jsonl'
        with fil.open('a') as f:
            f.write('\n' + json.dumps({'type':'assistant','message':{'usage':{
                'input_tokens':90,'cache_creation_input_tokens':0,'cache_read_input_tokens':0}}}))
            f.write('\n{"type":"result",')
        with patch.object(ab.korslut, 'senaste_slutpost', return_value=(None, None)):
            m = ab.matt('prov-arm')
            self.assertIsNone(m['minuter'])
            self.assertIsNone(m['over_halva'])
            fil.write_text('{"type":"assistant","message":["ogiltigt"]}\n')
            m = ab.matt('prov-arm')
            self.assertIsNone(m['minuter'])

    def test_trasig_assistantrad_gor_kontextens_max_okant(self):
        self.logg('20260101T000000Z', 'syntetisk-a', duration_ms=60000, num_turns=1,
                  modelUsage={'syntetisk-a':{'contextWindow':100}})
        fil = self.k / 'korning-20260101T000000Z.jsonl'
        with fil.open('a') as f:
            f.write('\n' + json.dumps({'type':'assistant','message':{'usage':{
                'input_tokens':70,'cache_creation_input_tokens':0,'cache_read_input_tokens':0}}}))
            f.write('\n{"type":"assistant",')
        with patch.object(ab.korslut, 'senaste_slutpost', return_value=(None, None)):
            m = ab.matt('prov-arm')
        self.assertIsNone(m['kontext_max'])
        self.assertEqual(m['observerad_kontext_max'], 70)
        self.assertTrue(m['logg_lasfel'])


if __name__ == '__main__':
    unittest.main()
