#!/usr/bin/env python3
"""Byggstandarden i standard_kontroll: 3.2 flytande typografi med cqi godtas, vw mot ett omslag ger information, bara vw ger
information; 8.2 CSP per sajt (ägarens beslut 2026-10-13, punkt 4): en lättnad mot mallen godtas med skälet på en rad
som börjar med "CSP:" i projektets RIKTNING.md, annars är den ett fel, och ett verkningslöst skriptdirektiv är alltid ett fel."""
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



MALL = "default-src 'self';img-src 'self' data:;object-src 'none';base-uri 'self';form-action 'self';font-src 'self'; script-src 'self' 'sha256-AAAA'; style-src 'self' 'sha256-BBBB'; style-src-attr 'unsafe-inline';"


class CspPerSajt(unittest.TestCase):
    def fynd82(self, policy, riktning=None):
        with contextlib.ExitStack() as st:
            sajt = Path(st.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetisk byggstandard 8.2')))
            d = sajt / 'dist'
            d.mkdir()
            (d / 'index.html').write_text(SIDA.replace('<title>', '<meta http-equiv="content-security-policy" content="%s"><title>' % policy),
                                          encoding='utf-8')
            (d / 'stil.css').write_text('body{margin:0}', encoding='utf-8')
            if riktning is not None:
                (sajt / 'RIKTNING.md').write_text(riktning, encoding='utf-8')
            fel, info, _ = sk.granska(d)
            return [f['text'] for f in fel if f['punkt'] == '8.2'], [i['text'] for i in info if i['punkt'] == '8.2']

    def test_mallens_csp_ar_utan_fynd(self):
        self.assertEqual(self.fynd82(MALL), ([], []))

    def test_en_lattnad_utan_skal_ar_ett_fel(self):
        for lattnad in ("img-src 'self' data: https://bilder.example.se", "style-src-elem 'self' 'unsafe-inline'"):
            fel, _ = self.fynd82(MALL.replace("img-src 'self' data:", lattnad), riktning='# Riktning\n\nInget skäl här.\n')
            self.assertTrue(any('lättad mot mallen' in f and 'utan skäl' in f for f in fel), (lattnad, fel))
        fel, _ = self.fynd82(MALL.replace("script-src 'self'", "script-src 'self' 'wasm-unsafe-eval'"))
        self.assertTrue(any("släpper igenom annat än 'self'" in f for f in fel), fel)

    def test_en_lattnad_med_skal_i_riktning_md_godtas(self):
        skal = '# Riktning\n\nCSP: hjulet ritas med WebGL i WASM, och omdömenas bilder kommer från kundens bildbank\n'
        policy = MALL.replace("img-src 'self' data:", "img-src 'self' data: https://bilder.example.se").replace(
            "script-src 'self'", "script-src 'self' 'wasm-unsafe-eval'")
        fel, info = self.fynd82(policy, riktning=skal)
        self.assertEqual(fel, [])
        self.assertTrue(any('img-src https://bilder.example.se' in i and 'WebGL' in i for i in info), info)
        self.assertTrue(any("'wasm-unsafe-eval'" in i for i in info), info)
        self.assertTrue(self.fynd82(policy, riktning=skal.replace('CSP: ', 'CSP: kort\n'))[0], 'ett skäl under 15 tecken räknas inte')

    def test_ett_verkningslost_skriptdirektiv_ar_ett_fel_aven_med_skal(self):
        fel, _ = self.fynd82(MALL.replace("script-src 'self'", "script-src 'self' 'unsafe-inline'"),
                             riktning='CSP: en inbäddad tjänst kräver inline-skript utan hash\n')
        self.assertTrue(any("'unsafe-inline'" in f for f in fel), fel)


if __name__ == '__main__':
    unittest.main()
