#!/usr/bin/env python3
"""Det aktiva urvalet (kontroller/urval.py; ren start 2026-10-08, del 2): historiken är av tills den väljs uttryckligen —
andra kunders byggbilder når inte granskaren, UPPTAGNA-VAL.md når inte agenterna, och körningens start skriver urvalet med
referenspaketet och ankarnas hash utan att ändra ett uttryckligt val."""
import contextlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import granska
import korregister
import upptagna_val
import urval


class Urval(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'urvalets prov'))).resolve()
        self.slug = 'prov-urval'
        self.u, self.k = self.root / 'underlag' / self.slug, self.root / 'kunder' / self.slug
        (self.u / 'atelje').mkdir(parents=True); (self.k / 'sajt').mkdir(parents=True)
        for m in (atelje, granska):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        annan = self.root / 'kunder' / 'annan-kund' / 'prov'
        (annan / 'inspektion' / 'hem').mkdir(parents=True); (annan / 'STATUS.json').write_text('{}')
        (annan / 'inspektion' / 'hem' / 'vy-390-forsta.png').write_bytes(b'png')
        (self.u / 'UPPTAGNA-VAL.md').write_text('<!-- %s -->\n# Upptagna val\n\nArchivo för målaren.\n' % upptagna_val.VERSION)
        (self.u / 'BRIEF.md').write_text('# Brief\n'); (self.u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Prov'}))

    def test_historiken_ar_av_tills_den_valts(self):
        self.assertEqual(urval.las(self.slug)['historik'], {'tidigare_byggbilder': False, 'upptagna_val': False, 'riktningshistorik': False})
        self.assertEqual(granska.tidigare_byggen(self.slug), [], 'andra kunders bilder når inte granskaren av vana')
        filer, _, _ = atelje.underlag_rader(self.slug)
        self.assertFalse(any(f.endswith('UPPTAGNA-VAL.md') for f in filer), filer)
        urval.skriv(self.slug, tidigare_byggbilder=True, upptagna_val=True)
        self.assertEqual([p.name for p in granska.tidigare_byggen(self.slug)], ['vy-390-forsta.png'])
        filer, _, _ = atelje.underlag_rader(self.slug)
        self.assertTrue(any(f.endswith('UPPTAGNA-VAL.md') for f in filer), filer)
        (self.u / 'UPPTAGNA-VAL.md').write_text('# Upptagna val utan version\n')
        self.assertFalse(any(f.endswith('UPPTAGNA-VAL.md') for f in atelje.underlag_rader(self.slug)[0]), 'en äldre fil läses aldrig')
        urval.skriv(self.slug, tidigare_byggbilder=False)
        self.assertEqual(granska.tidigare_byggen(self.slug), [])
        with self.assertRaises(ValueError):
            urval.aktivt(self.slug, 'domar')

    def test_korningens_start_skriver_kvittot_utan_att_andra_ett_val(self):
        (self.u / 'referenser' / 'paket-v02').mkdir(parents=True); (self.u / 'referenser' / 'paket-v02' / 'PAKET.json').write_text('{"kandidater": []}')
        (self.root / 'underlag' / 'kalibrering').mkdir(); (self.root / 'underlag' / 'kalibrering' / 'ANKARE.txt').write_text('K06 · ankare\n')
        d = urval.vid_start(self.slug, korning='2026-10-08T18:00:00Z')
        self.assertEqual((d['referenspaket'], d['korning'], d['historik']), ('paket-v02', '2026-10-08T18:00:00Z', {'tidigare_byggbilder': False, 'upptagna_val': False, 'riktningshistorik': False}))
        self.assertEqual(len(d['ankare']), 12); self.assertIn('standard', d['skal'])
        self.assertTrue(urval.fil(self.slug).is_file())
        urval.skriv(self.slug, upptagna_val=True)
        d2 = urval.vid_start(self.slug, korning='2026-10-08T19:00:00Z')
        self.assertTrue(d2['historik']['upptagna_val'], 'ett uttryckligt val står kvar vid nästa start')
        self.assertEqual(d2['korning'], '2026-10-08T19:00:00Z')
        urval.fil(self.slug).write_text('{trasig')
        self.assertEqual(urval.las(self.slug)['historik'], {'tidigare_byggbilder': False, 'upptagna_val': False, 'riktningshistorik': False}, 'en oläsbar fil är standard, aldrig på')
        self.assertEqual(urval.main([self.slug, '--upptagna-val', 'av', '--tidigare-byggbilder', 'pa', '--skal', 'provets skäl']), 0)
        self.assertEqual(urval.las(self.slug)['historik'], {'tidigare_byggbilder': True, 'upptagna_val': False, 'riktningshistorik': False})


if __name__ == '__main__':
    unittest.main()
