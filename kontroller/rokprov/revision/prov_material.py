#!/usr/bin/env python3
"""Materialsteget (kontroller/material.py) som mekanik utan konton och utan nät: uppdrag → attrapp eller saknar_konto,
versioner som aldrig skrivs över, import av en färdig tillgång med källa och rättigheter, koncept ur canvas-design, och
den faktiska användningen i en kandidat (bara genererat material; video kräver poster; Egen nej, påstår verksamhet nej)."""
import contextlib
import json
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import kandidater
import korregister
import material


class Material(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'materialstegets prov'))).resolve()
        self.slug = 'prov-material'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.object(material, 'HEM', self.root / 'hem'))
        (self.root / 'underlag' / self.slug).mkdir(parents=True)
        self.sajt = kandidater.ksajt(self.slug, 'k01'); (self.sajt / 'src').mkdir(parents=True)
        (self.root / 'underlag' / self.slug / 'bilder').mkdir()
        (self.root / 'underlag' / self.slug / 'bilder' / 'BILDER.md').write_text('| fil | Egen |\n|---|---|\n| foto.jpg | ja |\n')
        (self.root / 'underlag' / self.slug / 'bilder' / 'foto.jpg').write_bytes(b'jpg')
        def inget_nat(*a, **k):
            raise AssertionError('materialsteget gör inga nätanrop utan konto')
        self.stack.enter_context(patch.object(socket, 'create_connection', inget_nat))

    def test_attrapp_och_versioner(self):
        t = material.bestall(self.slug, 'en varm illustration av verkstadens stämning', 'bild', 'stubb')
        self.assertEqual((t['id'], t['status'], t['roll'], t['pastar_verksamhet']), ('m001', 'stubb', 'illustrativ', False))
        f = self.root / 'underlag' / self.slug / t['versioner'][0]['fil']
        self.assertTrue(f.is_file() and f.name == 'v01.svg' and 'STUBB' in f.read_text())
        t2 = material.bestall(self.slug, 'samma uppdrag, ny version', 'bild', 'stubb', igen='m001')
        self.assertEqual([v['version'] for v in t2['versioner']], [1, 2]); self.assertTrue(f.is_file(), 'v01 skrivs aldrig över')
        self.assertEqual(material.bestall(self.slug, 'nästa', 'bild', 'stubb')['id'], 'm002')
        self.assertFalse(material.anvand(self.slug, 'm001', 'k01', 'hero')['ok'], 'en stubb används aldrig')
        self.assertIn('stubb', material.anvand(self.slug, 'm001', 'k01', 'hero')['hinder'])

    def test_leverantorer_utan_konto_gor_inget_anrop(self):
        for lev, typ in (('higgsfield', 'bild'), ('nano-banana', 'bild'), ('seedance', 'video')):
            t = material.bestall(self.slug, 'uppdrag', typ, lev)
            self.assertEqual(t['status'], 'saknar_konto'); self.assertIsNone(t['versioner'][0]['fil'])
            self.assertIn(material.LEVERANTORER[lev]['env'], t['versioner'][0]['hinder']); self.assertIn('konto', t['versioner'][0]['hinder'])
            self.assertFalse(material.anvand(self.slug, t['id'], 'k01', 'hero')['ok'])
        (self.root / 'hem').mkdir(); (self.root / 'hem' / 'higgsfield.env').write_text('HIGGSFIELD_API_KEY=prov\n')
        t = material.bestall(self.slug, 'uppdrag', 'video', 'higgsfield')
        self.assertEqual(t['status'], 'fel'); self.assertIn('inte infört', t['versioner'][0]['hinder'])
        with self.assertRaises(ValueError):
            material.bestall(self.slug, 'x', 'video', 'nano-banana')

    def test_import_canvas_och_anvandning(self):
        png = self.root / 'koncept.png'; png.write_bytes(b'\x89PNG\r\n\x1a\nprov')
        k = material.canvas(self.slug, png, 'k01', 'kompositionsstudie för hero')
        self.assertEqual((k['status'], k['roll'], k['leverantor'], k['typ']), ('genererad', 'koncept', 'canvas-design', 'bild'))
        self.assertIn('canvas-design @', k['versioner'][0]['kalla']); self.assertIn('k01', k['versioner'][0]['kalla'])
        self.assertTrue(png.is_file(), 'originalet rörs inte')
        r = material.anvand(self.slug, k['id'], 'k01', 'hero')
        self.assertTrue(r['ok'], r); self.assertEqual(r['fil'], 'src/assets/material/hero__%s-v01.png' % k['id'])
        self.assertTrue((self.sajt / r['fil']).is_file())
        md = (kandidater.kdir(self.slug, 'k01') / 'material' / 'MATERIAL.md').read_text()
        self.assertIn('| nej | nej |', md); self.assertIn('koncept', md); self.assertIn('canvas-design', md)
        self.assertEqual(atelje.egna_bilder(self.slug), ['foto.jpg'], 'materialet räknas aldrig som verksamhetens egna bilder')
        self.assertEqual(material.las(self.slug)['tillgangar'][k['id']]['anvand'][0]['plats'], 'hero')
        # en genererad video (importerad ur leverantörens tjänst) kräver posterbild; reducerad rörelse står i raden
        mp4 = self.root / 'klipp.mp4'; mp4.write_bytes(b'mp4')
        v = material.importera(self.slug, mp4, 'higgsfield', 'stämningsklipp', 'Higgsfield, ägarens konto 2026-10-08', 'licens enligt tjänstens villkor')
        self.assertEqual((v['typ'], v['status']), ('video', 'genererad')); self.assertIn('poster', v['webb']['hinder'][0])
        self.assertFalse(material.anvand(self.slug, v['id'], 'k01', 'intro')['ok'])
        self.assertFalse(material.anvand(self.slug, v['id'], 'k01', 'intro', poster='m999')['ok'])
        r2 = material.anvand(self.slug, v['id'], 'k01', 'intro', poster=k['id'])
        self.assertTrue(r2['ok'], r2); self.assertTrue((self.sajt / 'src' / 'assets' / 'material' / ('intro__%s-poster.png' % v['id'])).is_file())
        md = (kandidater.kdir(self.slug, 'k01') / 'material' / 'MATERIAL.md').read_text()
        self.assertIn('posterbilden visas; ingen autouppspelning', md)
        with self.assertRaises(ValueError):
            material.importera(self.slug, mp4, 'nano-banana', 'x', 'k', 'r')
        self.assertFalse(material.anvand(self.slug, k['id'], 'k01', 'Hero Bild')['ok'], 'platsen är en enkel sträng')


if __name__ == '__main__':
    unittest.main()
