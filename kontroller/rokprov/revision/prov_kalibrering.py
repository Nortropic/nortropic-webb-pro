#!/usr/bin/env python3
"""Kalibreringsförsökets frysning och underlag (kontroller/granskarforsok/kalibrering.py; backlogposten
B-20261003-kalibrering-av-visuell-niva-externa-exempel-i-tr, ägarens uppdrag 2026-10-09, punkt 2): modellen, granskarens
metod, ankarna och exemplens bilder fryses före ägarens domar och ett försök efter en ändring är aldrig ett oberoende mått;
en ensidig sajt beskrivs som ensidig för både granskaren och ägaren, och ägarens domar över de prövade exemplen ingår
aldrig i frysningen. Syntetiska exempel; ingen granskare startas."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'granskarforsok'))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
import granska as gr  # noqa: E402
import kalibrering as kf  # noqa: E402
import korregister  # noqa: E402

PNG = b'\x89PNG\r\n\x1a\n' + b'prov'


class Kalibrering(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.u = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kalibreringens frysning'))).resolve() / 'underlag'

        def ingen_granskare(*a, **k):  # provet startar aldrig en verklig granskare, inte heller om skyddet regredierar
            raise AssertionError('provet försökte starta en granskarsession (kor_en)')
        self.stack.enter_context(patch.object(kf, 'kor_en', ingen_granskare))
        self.stack.enter_context(patch.object(kf.shutil, 'which', lambda *_a, **_k: '/usr/bin/false'))
        self.k = self.u / 'kalibrering'
        for ident, sidor in (('K01', ('start',)), ('K02', ('start', 'undersida')), ('K14', ('start', 'undersida')), ('K17', ('start',))):
            for sida in sidor:
                (self.k / ident / sida).mkdir(parents=True)
                for n in ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-1440-hela.png', 'vy-390-hela.png', 'vy-390-ruta-01.png'):
                    (self.k / ident / sida / n).write_bytes(PNG + ident.encode() + sida.encode() + n.encode())
                (self.k / ident / sida / 'vy-390-aria.txt').write_text('- link "x"\n')
        (self.k / 'K14' / 'UNDERSIDA.txt').write_text('https://exempel.invalid/tjanster\n')
        (self.k / 'K17' / 'UNDERSIDA.txt').write_text('ingen: ensidig sajt; navigationen är ankare på startsidan\n')
        (self.k / 'ANKARE.txt').write_text('K01 · ankare\n')
        (self.k / 'URVAL.txt').write_text('K01 · over · https://a.invalid/ · ankare\nK02 · nastan · https://b.invalid/ · x\n'
                                          'K14 · nastan · https://c.invalid/ · x\nK17 · generisk · https://d.invalid/ · x\n')
        self.domar({'K01': {'niva': 'over', 'skiljer': 'ANKARETS ORD'}, 'K02': {'niva': 'nastan', 'skiljer': 'utvecklingsexempel'}})

    def domar(self, d):
        (self.k / 'DOMAR.json').write_text(json.dumps(d))

    def test_ett_historiskt_ankare_ar_varken_ankare_eller_provat(self):
        # ägarens beslut 2026-10-09 om K03: bilderna och domen bevaras som historik
        (self.k / 'ANKARE.txt').write_text('K01 · ankare\nK02 · historik · ankare till 2026-10-09\n')
        ex = {e['id']: e for e in gr.kalibreringsexempel(self.u)}
        self.assertEqual((ex['K02']['ankare'], ex['K02']['historik']), (False, True))
        self.assertEqual([e['id'] for e in kf.undanhallna(self.u)], [], 'det historiska ankaret prövades som undanhållet')
        rdir = self.u.parent / 'omgang'
        rdir.mkdir()
        md, bilder = gr.frysta_ankare(rdir, self.u)
        self.assertNotIn('K02', ' '.join(str(b) for b, _t in bilder), 'det historiska ankaret frystes som ankare')

    def test_frysningen_fore_domarna_och_brotten(self):
        ids = ['K14', 'K17']
        f = kf.frys(ids, 'opus[1m]', 'high', self.u)
        self.assertTrue(f.is_file())
        self.assertNotIn('ANKARETS ORD', f.read_text(), 'ankarnas ord står bara som hash')
        self.assertIsNone(kf.frysningsbrott(ids, 'opus[1m]', 'high', self.u))
        with self.assertRaises(ValueError):
            kf.frys(ids, 'opus[1m]', 'high', self.u)  # en frysning skrivs aldrig om
        self.assertTrue(any(b.startswith('modell') for b in kf.frysningsbrott(ids, 'sonnet', 'high', self.u)))
        (self.k / 'K14' / 'undersida' / 'vy-390-forsta.png').write_bytes(PNG + b'utbytt')
        self.assertTrue(any(b.startswith('exempel: K14') for b in kf.frysningsbrott(ids, 'opus[1m]', 'high', self.u)))
        self.domar({'K01': {'niva': 'over', 'skiljer': 'ÄNDRADE ORD'}, 'K02': {'niva': 'nastan', 'skiljer': 'x'}})
        self.assertTrue(any(b.startswith('ankare: K01') for b in kf.frysningsbrott(ids, 'opus[1m]', 'high', self.u)))
        with patch.object(gr, 'TROSKEL', dict(gr.TROSKEL, **{next(iter(gr.TROSKEL)): 1})):
            self.assertTrue(any(b.startswith('kod') for b in kf.frysningsbrott(ids, 'opus[1m]', 'high', self.u)), 'en sänkt tröskel efter frysningen')

    def test_agarens_domar_over_de_provade_ingar_inte_och_en_sen_frysning_syns(self):
        self.domar({'K01': {'niva': 'over', 'skiljer': 'x'}, 'K14': {'niva': 'over', 'skiljer': 'ÄGARENS DOM K14'}})
        f = kf.frys(['K14'], 'm', 'e', self.u)
        self.assertNotIn('ÄGARENS DOM K14', f.read_text())
        self.assertIn('frysningen gjordes efter domar över K14', kf.frysningsbrott(['K14'], 'm', 'e', self.u))

    def test_forsoket_kraver_frysningen_utom_i_torrkorning(self):
        self.domar({'K01': {'niva': 'over', 'skiljer': 'x'}, 'K14': {'niva': 'nastan', 'skiljer': 'y'}})
        ut = self.u.parent / 'forsok'
        with contextlib.redirect_stdout(io.StringIO()) as t:
            rc = kf.main(['--ut', str(ut), '--underlag', str(self.u), '--bara', 'K14'])
        self.assertEqual(rc, 2, 'utan frysning kördes ett "oberoende" försök')
        self.assertIn('ingen frysning före domarna', t.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(kf.main(['--torr', '--ut', str(ut), '--underlag', str(self.u), '--bara', 'K14']), 0)
        rap = kf.rapport([], {'undanhallna': 0, 'svar': 0, 'ofullstandiga': 0, 'falska_godkannanden': 0, 'av_ej_over': 0,
                              'falska_underkannanden': 0, 'av_over': 0}, ut, 'm', 'e', frysning=['modell: x fryst, y nu'])
        j = json.loads((ut / 'RAPPORT.json').read_text())
        self.assertEqual((j['giltighet'], j['frysning']), ('utvecklingsdata', ['modell: x fryst, y nu']))
        self.assertIn('frysningen före domarna höll inte', rap.read_text())

    def test_en_ensidig_sajt_beskrivs_som_ensidig(self):
        ut = self.u.parent / 'u17'
        for ident, ensidig in (('K17', True), ('K14', False)):
            e = {'id': ident, 'niva': 'generisk', 'skiljer': '', 'bilder': [], 'ankare': False}
            bilder, aria, ankare = kf.forbered(e, ut / ident, self.u)
            with patch.object(gr, 'UNDERLAG', self.u):  # uppdraget läser anteckningen ur kundens underlag, som försöket
                p = kf.uppdrag(e, ut / ident, bilder, aria, ankare)
            if ensidig:
                self.assertNotIn('startsidan och en undersida', p, 'uppdraget påstod en undersida som inte finns')
                self.assertIn('Sajten har ingen undersida att döma (ensidig sajt', p)
            else:
                self.assertIn('startsidan och en undersida', p)
        import server as dash
        with patch.object(dash, 'UNDERLAG', self.u):
            lista = {e['id']: e for e in dash.kalibrering_lista()}
        self.assertTrue((lista['K17'].get('undersida_saknas') or '').startswith('ensidig sajt'), 'dashboarden säger inte att K17 är ensidig')
        self.assertIsNone(lista['K14'].get('undersida_saknas'))


if __name__ == '__main__':
    unittest.main()
