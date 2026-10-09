#!/usr/bin/env python3
"""Bygget mot ägarens godkända prototyp (prova.vinnarjamforelse och granska.frysta_vinnare; backlogposten
B-20261005-prototyp-mot-helbygge-matt-automatiskt-och-ett-l, ägarens uppdrag 2026-10-09, punkt 4): startsidan och de
godkända undersidorna jämförs i den godkända designens bredder och tillstånd, bara mot en godkänd vinnare, bundet till
vinnarens version och byggets dist; det som inte kunde jämföras står med skälet och räknas aldrig som bevarad design;
granskaren får undersidornas frysta bilder och ska klassa förändringen. Syntetiska bilder; jamfor.mjs kör på riktigt."""
import contextlib
import hashlib
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import granska  # noqa: E402
import korregister  # noqa: E402
import prova  # noqa: E402


def png(p, w, h, farg=(200, 200, 200, 255), rand=None):
    """En PNG w×h; rand: (x0, farg) ger en annan färg från kolumnen x0."""
    rader = b''.join(b'\x00' + b''.join(bytes(rand[1] if rand and x >= rand[0] else farg) for x in range(w)) for _y in range(h))
    bit = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)  # noqa: E731
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b'\x89PNG\r\n\x1a\n' + bit(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + bit(b'IDAT', zlib.compress(rader)) + bit(b'IEND', b''))


class Vinnarjamforelse(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'prototyp mot helbygge'))).resolve()
        self.atelje = self.tmp / 'underlag' / 'v-prov' / 'atelje'
        self.vinnare = self.atelje / 'vinnare'
        self.insp = self.tmp / 'kunder' / 'v-prov' / 'prov' / 'inspektion'
        self.ut = self.tmp / 'kunder' / 'v-prov' / 'prov' / 'vinnare'
        for vy in ('390', '768', '1280', '1440'):  # startsidan som kandidaten fotograferades (kandidater.STARTVYER), menyn i 390
            png(self.vinnare / 'bilder' / ('vy-%s-ruta-01.png' % vy), 40, 20)
            png(self.vinnare / 'bilder' / ('vy-%s-hela.png' % vy), 40, 40)
        png(self.vinnare / 'bilder' / 'vy-390-meny.png', 40, 20)
        for vy in ('390', '1440'):  # undersidan i 390 och 1440
            png(self.vinnare / 'undersidor' / 'tjanster' / ('vy-%s-ruta-01.png' % vy), 40, 20)
            png(self.vinnare / 'undersidor' / 'tjanster' / ('vy-%s-hela.png' % vy), 40, 40)
        self.vinnarpost(godkand=True)
        for vy in ('390', '768', '1440'):  # bygget: 1280 saknas, och menyn är inte fotograferad
            png(self.insp / 'hem' / ('vy-%s-ruta-01.png' % vy), 40, 20)
            png(self.insp / 'hem' / ('vy-%s-hela.png' % vy), 40, 40)
        png(self.insp / 'tjanster' / 'vy-390-ruta-01.png', 40, 20, rand=(30, (10, 10, 10, 255)))  # en fjärdedel ändrad
        png(self.insp / 'tjanster' / 'vy-390-hela.png', 40, 50)
        png(self.insp / 'tjanster' / 'vy-1440-ruta-01.png', 40, 20)
        png(self.insp / 'om' / 'vy-390-ruta-01.png', 40, 20)  # en sida som bara finns i bygget

    def vinnarpost(self, godkand):
        filer = {('bilder/' if p.parent.name == 'bilder' else 'undersidor/%s/' % p.parent.name) + p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in list(self.vinnare.glob('bilder/*.png')) + list(self.vinnare.glob('undersidor/*/*.png'))}
        post = {'riktning': 3, 'kandidat': 'k03', 'version': 'v7', 'filer': filer, **({'godkand': {'tid': '2026-10-09T05:00:00Z'}} if godkand else {})}
        (self.atelje / 'VINNARE.json').write_text(json.dumps(post))

    def jamfor(self, **kw):
        text = prova.vinnarjamforelse(self.vinnare / 'bilder', self.insp / 'hem', self.ut, **kw)
        return text, json.loads((self.ut / 'VINNARJAMFORELSE.json').read_text())

    def par(self, j, sida, vy, slag):
        return next(p for p in j['par'] if (p['sida'], p['vy'], p['slag']) == (sida, vy, slag))

    def test_undersidorna_jamfors_i_den_godkanda_designens_bredder(self):
        text, j = self.jamfor()
        self.assertTrue((self.ut / 'skillnad-tjanster-vy-390-ruta-01.png').is_file(), 'undersidan jämfördes inte')
        t = self.par(j, 'tjanster', '390', 'första vyn')
        self.assertEqual(t['andel'], 0.25, t)
        self.assertTrue(Path(t['skillnadsbild']).is_file())
        self.assertEqual(self.par(j, 'tjanster', '390', 'helsidan')['hojdskillnad'], 10)
        self.assertEqual({(p['sida'], p['vy']) for p in j['par']},
                         {('start', v) for v in ('390', '768', '1280', '1440')} | {('tjanster', '390'), ('tjanster', '1440')})
        self.assertIn('tjanster 390 första vyn: 25.0 % olika', text)

    def test_det_som_inte_kunde_jamforas_star_med_skalet(self):
        text, j = self.jamfor()
        self.assertIn('## Inte jämfört', (self.ut / 'VINNARJAMFORELSE.md').read_text(), 'det som inte jämfördes redovisas inte')
        self.assertEqual(self.par(j, 'start', '1280', 'första vyn')['fel'], 'saknas: byggets bild')
        self.assertEqual(self.par(j, 'start', '390', 'menyn öppen')['fel'], 'saknas: byggets bild')
        self.assertEqual(self.par(j, 'tjanster', '1440', 'helsidan')['fel'], 'saknas: byggets bild')
        self.assertEqual(j['bara_i_bygget'], ['om'])
        self.assertGreater(j['ej_jamforda'], 0)
        md = (self.ut / 'VINNARJAMFORELSE.md').read_text()
        self.assertIn('## Inte jämfört', md); self.assertIn('om: bara i bygget', md)
        self.assertIn('visar inte att designen är bevarad', md)
        self.assertIn('inte jämförda', text)
        (self.insp / 'tjanster').rename(self.insp / 'tjanster-undan')
        text, j = self.jamfor()
        self.assertTrue(any('tjanster: sidan finns inte i byggets inspektion' in x for x in j['saknade']), j['saknade'])

    def test_bara_en_godkand_vinnare_ar_mattstock(self):
        self.vinnarpost(godkand=False)
        text, j = self.jamfor()
        self.assertTrue(text.startswith('ingen jämförelse'), 'en vinnare utan ägarens godkännande blev måttstock: ' + text[:120])
        self.assertEqual((j['godkand'], j['par'], j['jamforda']), (False, [], 0))
        self.assertEqual(prova.vinnarens_vyer(self.vinnare / 'bilder'), ((), False))

    def test_jamforelsen_ar_bunden_till_vinnaren_och_bygget(self):
        _t, j = self.jamfor(dist_sha='d' * 64)
        b = j['bindning']
        self.assertEqual((b['vinnare']['kandidat'], b['vinnare']['version'], b['vinnare']['godkand_tid']), ('k03', 'v7', '2026-10-09T05:00:00Z'))
        self.assertEqual(b['vinnare']['vinnare_sha256'], hashlib.sha256((self.atelje / 'VINNARE.json').read_bytes()).hexdigest())
        self.assertEqual(b['bygget']['dist_sha256'], 'd' * 64)
        png(self.vinnare / 'undersidor' / 'tjanster' / 'vy-390-hela.png', 40, 41)  # måttstocken utbytt efter godkännandet
        text, j = self.jamfor(dist_sha='d' * 64)
        self.assertIn('undersidor/tjanster/vy-390-hela.png stämmer inte med VINNARE.json', j['hashfel'])
        self.assertTrue(text.startswith('VINNARENS BILDER STÄMMER INTE'))

    def test_bygget_fotograferas_i_prototypens_bredder_och_med_menyn(self):
        self.assertEqual(prova.vinnarens_vyer(self.vinnare / 'bilder'), (('390', '768', '1280', '1440'), True))

    def test_granskaren_far_undersidorna_och_ska_klassa_forandringen(self):
        rdir = self.tmp / 'omgang'
        rdir.mkdir()
        with patch.object(granska, 'UNDERLAG', self.tmp / 'underlag'):
            h0 = granska.metod_sha('v-prov')
            v = granska.frysta_vinnare('v-prov', rdir)
            self.assertTrue((rdir / 'vinnare' / 'undersidor' / 'tjanster' / 'vy-390-ruta-01.png').is_file(), 'granskaren fick inte undersidan')
            self.assertIn('vy-390-ruta-01.png', [p.name for p in v[1] if p.parent.name == 'tjanster'])
            text = granska.uppdrag_text('v-prov', 'http://x', ['/'], self.tmp / 'ak', [], [], [], None, rdir, vinnare=v)
            self.assertIn('vinnare/undersidor/tjanster/vy-390-ruta-01.png', text)
            for ord_ in ('en försämring', 'en godkänd anpassning', 'förbättring', 'aldrig att designen är bevarad'):
                self.assertIn(ord_, text)
            png(self.vinnare / 'undersidor' / 'tjanster' / 'vy-1440-hela.png', 40, 42)
            self.assertNotEqual(granska.metod_sha('v-prov'), h0, 'undersidornas bilder ingår i metodhashen')
            with self.assertRaises(RuntimeError):
                granska.frysta_vinnare('v-prov', self.tmp / 'omgang-2')  # en utbytt undersidebild stoppar granskningen


if __name__ == '__main__':
    unittest.main()
