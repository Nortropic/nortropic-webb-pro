#!/usr/bin/env python3
"""Före/efter-domen kräver observerad rollkompetens och bilder; helt syntetiska sessioner."""
import contextlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('NWP_PROV_ROOT') or Path(__file__).resolve().parents[3])
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje
import bildkedja
import kandidater as kd
import kompetens
import korregister

def giltigt_kvitto(pass_):
    filer = kompetens.lasfiler(pass_)
    roller = kompetens.for_pass(pass_)
    skills, _ = kompetens.aktiverbara([f for r in roller for f in r['karna']])
    per = {'session': 'syntetisk', 'lasta': filer, 'saknas': [], 'fore_forsta_andring': filer,
           'skill_anrop': skills, 'skill_fore': skills, 'andrade': False, 'valda': []}
    return {'verifierad': True, 'ofullstandig': False, 'filer': filer, 'lasta': filer, 'saknas': [],
            'fore_forsta_andring': filer, 'skill_anrop': skills, 'skill_fel': [], 'per_session': [per],
            'sessioner': {'forvantade': 1, 'sedda': 1, 'saknade': []}, 'valda': [], 'mcp_utfall': {}}


def png(tagg):
    import struct
    import zlib
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0))
            + chunk(b'tEXt', b'tagg\0' + tagg.encode()) + chunk(b'IDAT', zlib.compress(b'\0\0')) + chunk(b'IEND', b''))


class ForeEfterKompetens(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'före efter kompetensprov')))
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        self.slug, self.kid = 'fore-efter-prov', 'k01'
        self.d = kd.kdir(self.slug, self.kid)
        for katalog in ('bilder/start', 'versioner/fore/bilder/start'):
            p = self.d / katalog
            p.mkdir(parents=True)
            for bredd in (390, 1440):
                for vy in ('forsta', 'hela'):
                    (p / ('vy-%s-%s.png' % (bredd, vy))).write_bytes(png(katalog))
        self.stack.enter_context(patch.multiple(kd, fore_efter_prompt=lambda *a: 'syntetiskt',
            blind_nekas=lambda *a: [], blind_tillatet=lambda *a: self.tmp / 'blind.json'))
        self.stack.enter_context(patch.object(atelje, 'session', return_value={
            'session_id': 'syntetisk', 'structured_output': {'totalt': 'likvardiga', 'skal': 'syntetiskt', 'fynd': [], 'omraden': []}}))
        self.lasning = self.stack.enter_context(patch.object(bildkedja, 'lasning', return_value={
            'verifierad': True, 'grupper': {g: {'saknas': [], 'kravda': 4, 'lasta': 4} for g in ('X', 'Y')}}))
        self.kvitto = self.stack.enter_context(patch.object(kompetens, 'kvitto', return_value=giltigt_kvitto('fore_efter')))

    def kor(self):
        return kd.fore_efter(self.slug, self.kid, 'fore', 'efter')

    def test_saknad_kompetens_ger_ingen_styrande_dom(self):
        self.kvitto.return_value = {'verifierad': False}
        post = self.kor()
        self.assertEqual(post['utfall'], 'oklart')
        self.assertTrue(post['kompetenskravbrister'])
        self.assertEqual(kd.fore_efter_regel({}, post, {})[0], 'oklart')

    def test_saknad_bildobservation_ger_ingen_styrande_dom(self):
        self.lasning.return_value = None
        self.assertEqual(self.kor()['utfall'], 'oklart')

    def test_giltig_kompetens_och_bilder_sparas_med_domen(self):
        post = self.kor()
        self.assertEqual(post['utfall'], 'likvardig')
        self.assertEqual(post['kompetenskravbrister'], [])
        self.assertTrue(post['kompetens']['verifierad'])
        self.assertEqual(json.loads(next((self.d / 'fore-efter').glob('*/FORE-EFTER.json')).read_text())['kompetens'], post['kompetens'])


if __name__ == '__main__':
    unittest.main()
