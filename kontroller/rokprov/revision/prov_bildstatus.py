#!/usr/bin/env python3
"""Leveransens visuella status ur beställningen (kontroller/bildstatus.py; backloggen
B-20261003-bildernas-uppgift-och-leveransens-visuella-statu, och GR-20261009-natt-omgranskning-codex#N05): en rad om en
saknad bild gör leveransen visuellt begränsad av saknat material, också i förberedelsens format; bildmaterialet är
komplett bara med beställningens uttryckliga besked; tomt, ofullständigt eller okänt är okänt, aldrig komplett. Proven
går genom statusfunktionen, kommandoraden och det dashboardens bygge bär och visar."""
import contextlib
import json
import os
import re
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

# statusorden bokstavligt, så att ett prov fälls av beteendet och inte av en saknad konstant; det första fallet binder dem
BEGRANSAD = 'visuellt begränsad av saknat material'
KOMPLETT_ORD = 'bildmaterialet komplett'
OKAND = 'bildmaterialets status okänd'
BESKED_K, BESKED_S = 'Bildmaterial: komplett', 'Bildmaterial: saknas'

TABELL = """# Beställning till Provfirman

Bildmaterial: saknas

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
# förberedelsens dokumenterade format (kontroller/forberedelse.py: uppdelat i vad som hindrar design respektive leverans),
# utan beskedet: Codex reproduktion gav "visuellt färdig"
FORBEREDELSE = """# Beställning

## Hindrar design

- Huvudbild saknas och behöver levereras
- Tre meningar i ägarens egna ord om arbetssättet

## Hindrar leverans

- Telefontid
- F-skatt
"""
KOMPLETT = """# Beställning

Bildmaterial: komplett

## Hindrar leverans

- Telefontid
- Inga nya bilder behövs: de egna fotona räcker
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

    def status(self, slug, text=None):
        if text is not None:
            self.skriv(slug, text)
        return bildstatus.visuell_status(slug, self.u)

    def test_orden_i_modulen(self):
        self.assertEqual((bildstatus.BEGRANSAD, bildstatus.FARDIG, bildstatus.OKAND), (BEGRANSAD, KOMPLETT_ORD, OKAND))
        self.assertEqual((bildstatus.BESKED_KOMPLETT, bildstatus.BESKED_SAKNAS), (BESKED_K, BESKED_S))

    def test_tabellens_kropp_ar_det_som_saknas(self):
        s = self.status('a', TABELL)
        self.assertEqual(s['status'], BEGRANSAD)
        self.assertEqual(len(s['bestallda']), 2, s['bestallda'])  # rubrikraden och avskiljaren räknas inte, inte heller Bekräfta
        self.assertTrue(s['bestallda'][0].startswith('| Ett porträtt'), s['bestallda'])
        self.assertIn('2 bilder saknas', s['text'])

    def test_en_lista_raknas_och_avsnittet_slutar_vid_nasta_rubrik(self):
        s = self.status('b', '# B\n\n## Bilder\n\n1. Ett fönsterbyte före och efter\n- Verkstaden\n\n## Bekräfta\n\n- Telefonnumret\n')
        self.assertEqual((s['status'], s['bestallda']), (BEGRANSAD, ['1. Ett fönsterbyte före och efter', '- Verkstaden']))

    def test_forberedelsens_format_med_saknad_huvudbild_ar_begransad(self):
        s = self.status('n05', FORBEREDELSE)
        self.assertEqual(s['status'], BEGRANSAD, s)
        self.assertEqual(s['bestallda'], ['- Huvudbild saknas och behöver levereras'], s['bestallda'])

    def test_komplett_kraver_ett_uttryckligt_besked(self):
        s = self.status('k', KOMPLETT)
        self.assertEqual((s['status'], s['bestallda'], s['besked']), (KOMPLETT_ORD, [], 'komplett'), s)
        self.assertIn('säger inget om formgivningen', s['text'], 'ett komplett material är inget godkännande av formgivningen')
        for fetstil in ('**Bildmaterial:** komplett', '- Bildmaterial: komplett'):
            self.assertEqual(self.status('k2', '# K\n\n%s\n\n## Uppgifter\n\n- Telefontid\n' % fetstil)['status'], KOMPLETT_ORD, fetstil)

    def test_en_saknad_bild_gar_fore_beskedet_komplett(self):
        s = self.status('m', KOMPLETT + '\n## Hindrar design\n\n- Ett foto av verkstaden saknas\n')
        self.assertEqual(s['status'], BEGRANSAD, s)
        self.assertIn('motsägs', s['text'])

    def test_beskedet_saknas_utan_rader_ar_begransat(self):
        self.assertEqual(self.status('s', '# S\n\nBildmaterial: saknas\n')['status'], BEGRANSAD)

    def test_tomt_ofullstandigt_eller_okant_ar_okant_aldrig_komplett(self):
        fall = {'utan-besked': '# C\n\n## Uppgifter\n\n- Telefontid\n',
                'bara-text': '# D\n\n## Bilder\n\nInga: de egna fotona räcker.\n',
                'tom': '', 'blanksteg': '   \n\n',
                'ogiltigt': '# E\n\nBildmaterial: kanske\n',
                'motstridigt': '# F\n\nBildmaterial: komplett\n\nBildmaterial: saknas\n'}
        for slug, text in fall.items():
            s = self.status(slug, text)
            self.assertEqual((s['status'], s['bestallda']), (OKAND, []), (slug, s))
            self.assertNotEqual(s['status'], KOMPLETT_ORD, slug)

    def test_ingen_eller_en_lankad_bestallning_ar_okand(self):
        self.assertEqual(self.status('saknas')['status'], OKAND)
        (self.u / 'e').mkdir(parents=True)
        (self.root / 'utanfor.md').write_text(KOMPLETT, encoding='utf-8')
        os.symlink(self.root / 'utanfor.md', self.u / 'e' / 'BESTALLNING.md')
        self.assertEqual(self.status('e')['status'], OKAND, 'en länk följs inte')

    def test_skrivaren_far_kontraktet(self):
        """Förberedelsens prompt bär båda beskeden ur bildstatus (en källa), och en beställning i dess form med beskedet läses rätt."""
        import forberedelse
        with patch.object(forberedelse.kompetens, 'prompt_rader', return_value=[]):
            p = forberedelse.prompt('prov', self.root / 'paket')
        self.assertIn(BESKED_K, p)
        self.assertIn(BESKED_S, p)
        self.assertEqual(self.status('f', BESKED_S + '\n\n' + FORBEREDELSE)['status'], BEGRANSAD)

    def dashboarden(self, slug):
        """Bygget som dashboarden får (server.sammanfattning) och chipet som index.html ritar ur det."""
        (self.root / 'kunder' / slug).mkdir(parents=True, exist_ok=True)
        with patch.multiple(dash, UNDERLAG=self.u, KUNDER=self.root / 'kunder'):
            b = dash.sammanfattning(slug)
        rader = (Path(dash.__file__).parent / 'index.html').read_text(encoding='utf-8').split('\n')
        kod = [next(r for r in rader if r.startswith(x)) for x in ('const esc = ', 'const visuellchip = ')]
        js = '\n'.join(kod) + '\nprocess.stdout.write(visuellchip(JSON.parse(process.argv[1])));'
        r = subprocess.run(['node', '-e', js, json.dumps(b, ensure_ascii=False)], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        m = re.fullmatch(r'<span class="chip ?([a-z]*)" title="([^"]*)">([^<]*)</span>', r.stdout)
        self.assertTrue(m, r.stdout)
        return b, m.group(1), m.group(3)

    def test_dashboarden_bar_och_visar_statusen(self):
        self.skriv('g', TABELL); self.skriv('h', FORBEREDELSE); self.skriv('i', ''); self.skriv('j', KOMPLETT)
        b, klass, text = self.dashboarden('g')
        self.assertEqual((b['visuell']['status'], len(b['visuell']['bestallda']), klass, text), (BEGRANSAD, 2, 'gul', BEGRANSAD))
        self.assertEqual(self.dashboarden('h')[1:], ('gul', BEGRANSAD), 'den saknade huvudbilden i förberedelsens format')
        self.assertEqual(self.dashboarden('i')[1:], ('gul', OKAND), 'en tom beställning visas som okänd, aldrig komplett')
        self.assertEqual(self.dashboarden('utan-bestallning')[1:], ('gul', OKAND))
        self.assertEqual(self.dashboarden('j')[1:], ('', KOMPLETT_ORD), 'komplett bara med beskedet')

    def test_kommandoraden_skriver_statusen_och_raderna(self):
        self.skriv('g', TABELL)
        kod = ('import sys; sys.path.insert(0, %r); import bildstatus; from pathlib import Path; bildstatus.UNDERLAG = Path(%r); '
               'sys.exit(bildstatus.main(sys.argv[1:]))' % (str(Path(bildstatus.__file__).parent), str(self.u)))
        r = subprocess.run([sys.executable, '-B', '-c', kod, 'g'], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        rader = r.stdout.splitlines()
        self.assertTrue(rader[0].startswith('visuellt begränsad av saknat material: 2 bilder'), rader)
        self.assertEqual(len(rader), 3, rader)
        r = subprocess.run([sys.executable, '-B', '-c', kod, 'saknas-helt'], capture_output=True, text=True, timeout=60)
        self.assertTrue(r.stdout.startswith(OKAND), r.stdout)


if __name__ == '__main__':
    unittest.main()
