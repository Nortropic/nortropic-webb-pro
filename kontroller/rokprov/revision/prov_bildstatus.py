#!/usr/bin/env python3
"""Leveransens visuella status ur beställningen (kontroller/bildstatus.py; backloggen
B-20261003-bildernas-uppgift-och-leveransens-visuella-statu): avsnittet Bilder i BESTALLNING.md gör leveransen visuellt
begränsad av saknat material, och dashboardens bygge bär samma status."""
import contextlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
import bildstatus  # noqa: E402
import korregister  # noqa: E402
import server as dash  # noqa: E402

TABELL = """# Beställning till Provfirman

## Uppgifter

- Telefontid

## Bilder (2 stycken)

| Vad | Varför | Var på sajten |
|---|---|---|
| Ett porträtt vid bilen | Visar vem som kommer | Startsidan |
| Ett färdigt badrum | Beviset | Tjänstesidan |

## Bekräfta

- Att adressen stämmer
"""


class Bildstatus(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'bildstatusens prov')))
        self.u = self.root / 'underlag'

    def skriv(self, slug, text):
        (self.u / slug).mkdir(parents=True, exist_ok=True)
        (self.u / slug / 'BESTALLNING.md').write_text(text, encoding='utf-8')

    def test_tabellens_kropp_ar_det_som_saknas(self):
        self.skriv('a', TABELL)
        s = bildstatus.visuell_status('a', self.u)
        self.assertEqual(s['status'], bildstatus.BEGRANSAD)
        self.assertEqual(len(s['bestallda']), 2, s['bestallda'])  # rubrikraden och avskiljaren räknas inte, inte heller Bekräfta
        self.assertTrue(s['bestallda'][0].startswith('| Ett porträtt'), s['bestallda'])
        self.assertIn('2 bilder beställda', s['text'])

    def test_en_lista_raknas_och_avsnittet_slutar_vid_nasta_rubrik(self):
        self.skriv('b', '# B\n\n## Bilder\n\n1. Ett fönsterbyte före och efter\n- Verkstaden\n\n## Bekräfta\n\n- Telefonnumret\n')
        s = bildstatus.visuell_status('b', self.u)
        self.assertEqual((s['status'], s['bestallda']), (bildstatus.BEGRANSAD, ['1. Ett fönsterbyte före och efter', '- Verkstaden']))

    def test_utan_bildbestallning_ar_leveransen_visuellt_fardig(self):
        for slug, text in (('c', '# C\n\n## Uppgifter\n\n- Telefontid\n'), ('d', '# D\n\n## Bilder\n\nInga: de egna fotona räcker.\n')):
            self.skriv(slug, text)
            s = bildstatus.visuell_status(slug, self.u)
            self.assertEqual((s['status'], s['bestallda']), (bildstatus.FARDIG, []), (slug, s))

    def test_ingen_eller_en_lankad_bestallning_ger_ingen_status(self):
        self.assertIsNone(bildstatus.visuell_status('saknas', self.u)['status'])
        (self.u / 'e').mkdir(parents=True)
        (self.root / 'utanfor.md').write_text(TABELL, encoding='utf-8')
        os.symlink(self.root / 'utanfor.md', self.u / 'e' / 'BESTALLNING.md')
        self.assertIsNone(bildstatus.visuell_status('e', self.u)['status'], 'en länk följs inte')

    def test_dashboardens_bygge_bar_statusen(self):
        self.skriv('f', TABELL)
        (self.root / 'kunder' / 'f').mkdir(parents=True)
        with patch.multiple(dash, UNDERLAG=self.u, KUNDER=self.root / 'kunder'):
            b = dash.sammanfattning('f')
        self.assertEqual((b['visuell']['status'], len(b['visuell']['bestallda'])), (bildstatus.BEGRANSAD, 2), b['visuell'])

    def test_kommandoraden_skriver_statusen_och_raderna(self):
        self.skriv('g', TABELL)
        kod = ('import sys; sys.path.insert(0, %r); import bildstatus; from pathlib import Path; bildstatus.UNDERLAG = Path(%r); '
               'sys.exit(bildstatus.main(["g"]))' % (str(Path(bildstatus.__file__).parent), str(self.u)))
        r = subprocess.run([sys.executable, '-B', '-c', kod], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        rader = r.stdout.splitlines()
        self.assertTrue(rader[0].startswith('visuellt begränsad av saknat material: 2 bilder'), rader)
        self.assertEqual(len(rader), 3, rader)


if __name__ == '__main__':
    unittest.main()
