#!/usr/bin/env python3
"""Nyckelintaget (kontroller/nyckelintag.py; ägarens tillägg 2026-10-10, punkt 3): nyckeln sparas privat (0600, katalogerna
0700) per kund och leverantör utanför repot, läget visar aldrig nyckeln, en ny nyckel ersätter den gamla, återkallelsen
tar bort den och markerar Workerns hemlighet för borttagning, fel form, fel kund, okänd leverantör och symlänkar nekas,
kommandoraden tar aldrig emot en nyckel som argument, och bara aktiveringen läser nyckeln."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402
import nyckelintag as ni  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
NYCKEL1 = 'xkeysib-SYNTETISK-PROVNYCKEL-AAAA-0001'
NYCKEL2 = 'xkeysib-SYNTETISK-PROVNYCKEL-BBBB-0002'


class Nyckelintag(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(korregister.egen_tmp('nwp-nyckelintag-', 'nyckelintagets prov')).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.rot = self.tmp / 'kunder'
        p = patch.dict(os.environ, {'NWP_NYCKELINTAG': str(self.rot)}); p.start(); self.addCleanup(p.stop)

    def allt_text(self):
        return ''.join(f.read_text(encoding='utf-8', errors='replace') for f in self.rot.rglob('*') if f.is_file() and not f.name.endswith('.nyckel'))

    def test_nyckeln_sparas_privat_och_visas_aldrig(self):
        s = ni.lamna('prov-kund', 'brevo', NYCKEL1, {'lista': '12', 'mall': '7'}, 'dashboard')
        self.assertEqual((s['nyckel'], s['version'], s['kalla'], s['falt']), (True, 1, 'dashboard', {'lista': '12', 'mall': '7'}))
        self.assertTrue(s['nyckel_lagd'])
        k = self.rot / 'prov-kund'
        self.assertEqual(stat.S_IMODE((k / 'brevo.nyckel').stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(k.stat().st_mode), 0o700); self.assertEqual(stat.S_IMODE(self.rot.stat().st_mode), 0o700)
        self.assertNotIn(NYCKEL1, json.dumps(ni.status('prov-kund')))
        self.assertNotIn(NYCKEL1, self.allt_text(), 'nyckeln står bara i sin egen fil')
        self.assertEqual(ni.las_for_aktivering('prov-kund', 'brevo'), NYCKEL1)
        self.assertFalse(ROOT in self.rot.parents, 'intaget ligger utanför repot')

    def test_ny_nyckel_ersatter_och_aterkallelse_tar_bort(self):
        ni.lamna('prov-kund', 'brevo', NYCKEL1, {'lista': '12'})
        s = ni.lamna('prov-kund', 'brevo', NYCKEL2)
        self.assertEqual((s['version'], s['falt']), (2, {'lista': '12'}), 'uppgifterna står kvar när bara nyckeln byts')
        self.assertEqual(ni.las_for_aktivering('prov-kund', 'brevo'), NYCKEL2)
        self.assertNotIn(NYCKEL1, ''.join(f.read_text(errors='replace') for f in self.rot.rglob('*') if f.is_file()))
        s = ni.aterkalla('prov-kund', 'brevo')
        self.assertEqual(s['nyckel'], False); self.assertTrue(s['aterkallad'])
        self.assertIsNone(ni.las_for_aktivering('prov-kund', 'brevo'))
        s = ni.lamna('prov-kund', 'brevo', NYCKEL1)
        self.assertEqual((s['nyckel'], s['aterkallad'], s['version']), (True, None, 3), 'en ny nyckel efter återkallelsen')

    def test_fel_form_kund_och_leverantor_nekas(self):
        for args in (('prov-kund', 'brevo', 'kort'), ('prov-kund', 'brevo', 'xkeysib med blanksteg i nyckeln'), ('prov-kund', 'brevo', 'xkeysib-\nny-rad-i-nyckeln-0000'),
                     ('../annan', 'brevo', NYCKEL1), ('Prov', 'brevo', NYCKEL1), ('prov-kund', 'hubspot', NYCKEL1), ('prov-kund', 'epost', NYCKEL1)):
            with self.subTest(args=args[:2]):
                with self.assertRaises(ni.Fel):
                    ni.lamna(*args)
        for falt in ({'lista': 'abc'}, {'okand': '1'}, {'lista': '0'}):
            with self.assertRaises(ni.Fel):
                ni.lamna('prov-kund', 'brevo', None, falt)
        with self.assertRaises(ni.Fel):
            ni.lamna('prov-kund', 'pipedrive', None, {'doman': 'evil.example/x'})
        self.assertEqual(ni.lamna('prov-kund', 'epost', None, {'mottagare': 'a@kund.example.invalid,b@kund.example.invalid'})['falt'],
                         {'mottagare': 'a@kund.example.invalid,b@kund.example.invalid'})
        with self.assertRaises(ni.Fel):
            ni.lamna('prov-kund', 'brevo')

    def test_symlankar_nekas(self):
        self.rot.mkdir(mode=0o700)
        mal = self.tmp / 'annanstans'; mal.mkdir()
        os.symlink(mal, self.rot / 'prov-kund')
        with self.assertRaises(ni.Fel):
            ni.lamna('prov-kund', 'brevo', NYCKEL1)
        self.assertEqual(list(mal.iterdir()), [])
        os.unlink(self.rot / 'prov-kund')
        ni.lamna('prov-kund', 'brevo', NYCKEL1)
        f = self.rot / 'prov-kund' / 'pipedrive.nyckel'
        os.symlink(mal / 'stulen', f)
        with self.assertRaises(ni.Fel):
            ni.lamna('prov-kund', 'pipedrive', NYCKEL2)
        self.assertFalse((mal / 'stulen').exists())

    def test_kommandoraden_tar_aldrig_emot_nyckeln_som_argument(self):
        with contextlib.redirect_stdout(io.StringIO()) as ut, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                ni.main(['prov-kund', 'brevo', '--nyckel', NYCKEL1])
            with patch('getpass.getpass', return_value=NYCKEL1):
                self.assertEqual(ni.main(['prov-kund', 'brevo', '--falt', 'lista=12']), 0)
            self.assertEqual(ni.main(['prov-kund', '--visa']), 0)
            self.assertEqual(ni.main(['../x', '--visa']), 2)
        self.assertNotIn(NYCKEL1, ut.getvalue())
        self.assertEqual(ni.las_for_aktivering('prov-kund', 'brevo'), NYCKEL1)

    def test_bara_aktiveringen_laser_nyckeln(self):
        anv = sorted(str(f.relative_to(ROOT)) for d in ('kontroller', 'dashboard', 'kundstart', 'mall') for f in (ROOT / d).rglob('*')
                     if f.suffix in ('.py', '.js', '.mjs', '.html', '.astro') and 'node_modules' not in f.parts and 'rokprov' not in f.parts
                     and f.is_file() and 'las_for_aktivering' in f.read_text(encoding='utf-8', errors='replace'))
        self.assertEqual(anv, ['kontroller/aktivera.py', 'kontroller/nyckelintag.py'] if 'kontroller/aktivera.py' in anv else ['kontroller/nyckelintag.py'], anv)


if __name__ == '__main__':
    unittest.main()
