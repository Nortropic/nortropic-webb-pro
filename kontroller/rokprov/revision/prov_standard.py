#!/usr/bin/env python3
"""Byggstandardens 3.2 i standard_kontroll: flytande typografi med cqi godtas, vw mot ett omslag ger information, bara vw ger information."""
import contextlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister
import standard_kontroll as sk

SIDA = '<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Prov</title><link rel="stylesheet" href="/stil.css"></head><body><main><h1>Prov</h1></main></body></html>'


class Rotskrollaren(unittest.TestCase):
    def info33(self, css):
        with contextlib.ExitStack() as st:
            d = Path(st.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetisk byggstandard 3.3'))) / 'dist'
            d.mkdir(); (d / 'index.html').write_text(SIDA, encoding='utf-8'); (d / 'stil.css').write_text(css, encoding='utf-8')
            _, info, _ = sk.granska(d)
            return [i['text'] for i in info if i['punkt'] == '3.3' and 'rotskrollaren' in i['text']]

    def test_html_eller_body_med_hojd_och_overflow_ger_information(self):
        for css in ('html,body{height:100%;overflow:hidden}', 'body{margin:0;height:100vh;overflow-y:auto}'):
            t = self.info33(css); self.assertEqual(len(t), 1, css); self.assertIn('min-height: 100svh', t[0])
        self.assertEqual(self.info33('body{min-height:100svh;overflow-x:clip}'), [])
        self.assertEqual(self.info33('.panel{height:100%;overflow:auto}'), [], 'bara html och body')


class Typografi(unittest.TestCase):
    def info32(self, css):
        with contextlib.ExitStack() as st:
            d = Path(st.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetisk byggstandard 3.2'))) / 'dist'
            d.mkdir(); (d / 'index.html').write_text(SIDA, encoding='utf-8'); (d / 'stil.css').write_text(css, encoding='utf-8')
            _, info, _ = sk.granska(d)
            return [i['text'] for i in info if i['punkt'] == '3.2']

    def test_cqi_i_en_storleksbehallare_godtas(self):
        self.assertEqual(self.info32('.omslag{container:omslag / inline-size;max-width:72rem}h1{font-size:clamp(1.8rem, 1rem + 3cqi, 3rem)}'), [])

    def test_vw_med_rem_mot_ett_omslag_ger_information_om_cqi(self):
        for css in ('.omslag{max-width:72rem}h1{font-size:clamp(1.8rem, 1rem + 3vw, 3rem)}', '.omslag{width:min(100% - 2rem, 72rem)}h1{font-size:clamp(1.8rem,1rem + 3vw,3rem)}'):
            t = self.info32(css); self.assertEqual(len(t), 1, css); self.assertIn('cqi', t[0]); self.assertIn('omslag', t[0])

    def test_vw_med_rem_utan_omslag_och_bara_vw(self):
        self.assertEqual(self.info32('h1{font-size:clamp(1.8rem, 1rem + 3vw, 3rem)}'), [])
        t = self.info32('.omslag{max-width:72rem}h1{font-size:clamp(1.8rem, 4vw, 3rem)}'); self.assertEqual(len(t), 1); self.assertIn('bara vw', t[0])


if __name__ == '__main__':
    unittest.main()
