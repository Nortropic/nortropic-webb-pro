#!/usr/bin/env python3
"""Täckningen av integrationsuppdragets acceptansprov (kontroller/integrationer/tackning.json; uppdraget 2026-10-09,
avsnitt 13): varje T01–T32, M01–M20 och S1–S8 finns en gång, varje namngivet prov finns och körs av rökprovet, ett krav
utan prov har nivån ingen och ett exakt återstående, och varje område K01–K18 har ett prövat paket eller ett paket vars
färdighet anger hindret. Provet bevisar kopplingen, inte att proven är tillräckliga."""
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import integrationskatalog as ik  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
T = json.loads((ROOT / 'kontroller' / 'integrationer' / 'tackning.json').read_text(encoding='utf-8'))
ROKPROV = (ROOT / 'kontroller' / 'rokprov.sh').read_text(encoding='utf-8')


class Tackning(unittest.TestCase):
    def test_varje_krav_finns_en_gang(self):
        ids = [k['id'] for k in T['krav']]
        vantat = ['T%02d' % i for i in range(1, 33)] + ['M%02d' % i for i in range(1, 21)] + ['S%d' % i for i in range(1, 9)]
        self.assertEqual(sorted(ids), sorted(vantat))
        self.assertEqual(len(ids), len(set(ids)))

    def test_proven_finns_och_kors_av_rokprovet(self):
        for k in T['krav']:
            with self.subTest(id=k['id']):
                self.assertIn(k['niva'], T['nivaer'])
                for p in k['prov']:
                    self.assertTrue((ROOT / p).is_file(), p)
                    namn = Path(p).stem
                    self.assertRegex(ROKPROV, r'(^|[\s/"])%s(\.py|\.mjs|\s|;|")' % re.escape(namn), '%s körs inte av rokprov.sh' % namn)
                if not k['prov']:
                    self.assertEqual(k['niva'], 'ingen', 'ett krav utan prov kan inte ha en prövad nivå')
                if k['niva'] == 'ingen':
                    self.assertTrue(k['aterstar'] and len(k['aterstar']) > 20, 'ett oprövat krav anger exakt vad som återstår')

    def test_varje_omrade_har_prov_eller_hinder(self):
        K = ik.las()
        for o in ik.OMRADEN:
            with self.subTest(omrade=o):
                paket = [p for p in K['paket'] if p['omrade'] == o]
                provade = [p for p in paket if p['fardighet'] in ('kontraktsprovat', 'leverantorsprovat') and p['prov']]
                for p in provade:
                    for f in p['prov']:
                        self.assertRegex(ROKPROV, r'(^|[\s/"])%s(\.py|\.mjs|\s|;|")' % re.escape(Path(f).stem), f)
                if not provade:
                    self.assertTrue(all(p['fardighet_omfattning'].strip() for p in paket), o)


if __name__ == '__main__':
    unittest.main()
