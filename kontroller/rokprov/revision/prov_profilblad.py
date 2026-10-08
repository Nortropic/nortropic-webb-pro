#!/usr/bin/env python3
"""Profilbladet ur VERKSAMHET.json (rapportens punkt 14): fälten, avvikelserna först, fiktivt och nationellt utan blad, CLI."""
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister
import profilblad

ROOT = Path(__file__).resolve().parents[3]
V = {'schema': 1, 'namn': 'Syntetiska Snickeriet AB', 'fiktiv': False, 'rackvidd': {'typ': 'lokal', 'orter': ['Provstad', 'Grannby']},
     'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provstad', 'publik': True, 'roll': 'verkstad'},
     'kontaktvagar': [{'typ': 'telefon', 'varde': '070-000 00 00', 'belagg': 'syntetiskt'}, {'typ': 'e-post', 'varde': 'prov@example.invalid', 'belagg': 'syntetiskt'}],
     'oppettider': [{'dag': 'man', 'oppnar': '07:00', 'stanger': '16:00'}], 'kategorier': ['Snickare', 'Byggfirma'],
     'tjanster': ['Altaner', 'Kök'], 'webb': {'doman': 'example.invalid'}}


class Profilblad(unittest.TestCase):
    def test_bladet_bar_falten_med_avvikelserna_forst(self):
        b = profilblad.blad(V, beskrivning='Snickeri i Provstad. ' * 60, avvikelser=['Telefonnumret i Hitta.se är gammalt'], bilder=['verkstaden.jpg'])
        self.assertTrue(b.startswith('# Profilblad för Google-företagsprofilen: Syntetiska Snickeriet AB'))
        self.assertLess(b.index('## Avvikelser först'), b.index('## Fält')); self.assertIn('- Telefonnumret i Hitta.se är gammalt', b)
        for rad in ('| Primär kategori | Snickare |', '| Sekundära kategorier | Byggfirma |', '| Adress | Provgatan 1, 123 45 Provstad |',
                    '| Serviceområde | Provstad, Grannby |', '| Telefon | 070-000 00 00 |', '| Webbplats | https://example.invalid/ |',
                    '| Öppettider | Måndag 07:00–16:00 |', '| Tjänster | Altaner, Kök |', '- verkstaden.jpg'):
            self.assertIn(rad, b, rad)
        self.assertIn('(förkortad: ', b)
        self.assertLessEqual(len(b.split('## Beskrivning', 1)[1].split('\n\n')[1]), profilblad.BESKRIVNING_MAX)

    def test_dold_adress_saknade_falt_och_tom_beskrivning(self):
        v = dict(V, adress=dict(V['adress'], publik=False, gata=None), oppettider=[], kategorier=[], kontaktvagar=[], webb=None)
        b = profilblad.blad(v)
        self.assertIn('| Adress | dold: serviceområde utan gatuadress |', b); self.assertIn('(saknas: ange den exakta branschkategorin)', b)
        self.assertIn('(saknas: beställ av verksamheten', b); self.assertIn('(saknas: samma nummer som på sajten', b)
        self.assertIn('(skriv ur briefen', b); self.assertIn('- Inga kända avvikelser', b)

    def test_fiktiv_och_nationell_utan_forankring_far_inget_blad(self):
        self.assertIsNone(profilblad.blad(dict(V, fiktiv=True))); self.assertIn('fiktiv', profilblad.tillamplig(dict(V, fiktiv=True)))
        self.assertIsNone(profilblad.blad(dict(V, adress=None, rackvidd={'typ': 'nationell'})))
        self.assertIsNotNone(profilblad.blad(dict(V, rackvidd={'typ': 'nationell'})), 'nationell räckvidd med adress är lokalt förankrad')

    def test_cli(self):
        with contextlib.ExitStack() as st:
            tmp = Path(st.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetiskt profilblad')))
            (tmp / 'prov-blad').mkdir(); (tmp / 'prov-blad' / 'VERKSAMHET.json').write_text(json.dumps(V), encoding='utf-8')
            (tmp / 'beskrivning.txt').write_text('Syntetisk beskrivning.', encoding='utf-8')
            kor = lambda *a: subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'profilblad.py'), *a, '--underlag', str(tmp)], capture_output=True, text=True, timeout=30)  # noqa: E731
            r = kor('prov-blad', '--beskrivning', str(tmp / 'beskrivning.txt'))
            self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('Syntetisk beskrivning.', r.stdout); self.assertIn('| Telefon | 070-000 00 00 |', r.stdout)
            (tmp / 'prov-blad' / 'VERKSAMHET.json').write_text(json.dumps(dict(V, fiktiv=True)), encoding='utf-8')
            r = kor('prov-blad'); self.assertEqual(r.returncode, 3); self.assertIn('inget profilblad: fiktiv', r.stdout)
            self.assertEqual(kor('Prov Blad').returncode, 2); self.assertEqual(kor('finns-inte').returncode, 2)


if __name__ == '__main__':
    unittest.main()
