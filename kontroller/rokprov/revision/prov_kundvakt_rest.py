#!/usr/bin/env python3
"""R108-restfynd genom riktiga PreToolUse-ingången; enbart syntetiska filer."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister


class KundvaktRest(unittest.TestCase):
    def setUp(self):
        self.tmp = korregister.egen_tmp_med('nwp-startkvitto-', 'kundvaktens restprov')
        self.u = Path(self.tmp.__enter__())
        self.addCleanup(self.tmp.__exit__, None, None, None)
        self.slug = 'syntetiskt-restprov'
        self.kund = self.u / self.slug
        self.kund.mkdir()
        self.skriv('VERKSAMHET.json', json.dumps({'schema': 1, 'namn': 'Syntetiskt Provbolag',
                   'fiktiv': True, 'kontaktvagar': [], 'kategorier': ['Byggfirma'],
                   'tjanster': ['Reparation'], 'rackvidd': {'typ': 'lokal', 'orter': ['Provdalen']}}))
        self.skriv('RESEARCH.md', 'Adress: Testgränden 47, 943 27 Syntetbyn.\n')

    def skriv(self, namn, text):
        p = self.kund / namn
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def krok(self, verktyg='refero_search_screens', **inp):
        r = subprocess.run([str(ROOT / '.venv/bin/python'), '-B', str(ROOT / 'kontroller/kundvakt.py'),
                            self.slug, str(self.u)], input=json.dumps({'tool_name': 'mcp__refero__'+verktyg,
                            'tool_input': inp or {'query': 'contact page with clear typography'}}),
                           text=True, capture_output=True, timeout=30, cwd=ROOT)
        return r

    def neka(self, r):
        self.assertEqual(r.returncode, 2, r.stdout+r.stderr)
        self.assertNotIn('"permissionDecision": "allow"', r.stdout)

    def test_kanda_nummer_i_alla_parametergrenar(self):
        for verktyg, inp in [
            ('refero_get_screen', {'screen_id': 94327}),
            ('refero_get_screen', {'screen_ids': [43, 94327]}),
            ('refero_get_screen', {'screen_id': '94327000-abcd-1234-abcd-123456789abc'}),
            ('refero_get_screen_image', {'image_url': 'https://images.refero.design/screenshots/94327.jpg'}),
            ('refero_get_screen_image', {'image_url': 'https://images.refero.design/%2539%2534%2533%2532%2537.jpg'}),
        ]:
            with self.subTest(inp=inp): self.neka(self.krok(verktyg, **inp))

    def test_neutrala_id_adresser_och_generisk_fraga_gar(self):
        for verktyg, inp in [
            ('refero_get_screen', {'screen_id': 12345}),
            ('refero_get_screen', {'screen_id': 'd122da11-abcd-1234-abcd-112233445566'}),
            ('refero_get_screen_image', {'image_url': 'https://images.refero.design/screenshots/12345.jpg'}),
            ('refero_search_screens', {'query': 'contact page with clear typography'}),
        ]:
            with self.subTest(inp=inp):
                r=self.krok(verktyg, **inp)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                self.assertIn('"permissionDecision": "allow"',r.stdout)

    def test_lasfel_i_varje_kundtext_nekar_aven_generisk_fraga(self):
        for namn in ('BRIEF.md','INNEHALL.md','TEXTUNDERLAG.md','RESEARCH.md',
                     'kalla/extern/bokadirekt-omdomen.txt','kalla/extern/bokadirekt-tjanster.txt'):
            with self.subTest(namn=namn):
                p=self.skriv(namn,'## Team\n## Zyntor Feklun\n')
                p.chmod(0)
                try: self.neka(self.krok())
                finally: p.chmod(0o600)

    def test_frivillig_saknad_fil_gar_men_hangande_lank_nekas(self):
        self.assertEqual(self.krok().returncode,0)
        (self.kund/'BRIEF.md').symlink_to(self.kund/'saknas.md')
        self.neka(self.krok())

    def test_trasig_utf8_nekas(self):
        (self.kund/'BRIEF.md').write_bytes(b'Kontakt: Zyn\xfftor Feklun')
        self.neka(self.krok())

    def test_adressblock_med_ort_pa_nasta_rad(self):
        for text in ('Adress: Testgränden 47\n943 27\nSyntetbyn\n',
                     'Testgränden 47\n94327\nSYNTETBYN\n',
                     'Postnummer: 943 27\nSYNTETBYN\n',
                     'Testgränden 47\n943 27\nSyntetbyn.\n',
                     '- Gata: Testgränden 47\n- Postnummer: 943 27\n- Ort: Syntetbyn\n',
                     '| Postnummer | 943 27 |\n| Ort | Syntetbyn |\n'):
            with self.subTest(text=text):
                self.skriv('RESEARCH.md',text)
                self.neka(self.krok(query='builders Syntetbyn'))

    def test_ny_rubrik_eller_stycke_ar_inte_postort(self):
        for text in ('Testgränden 47\n943 27\n\nTypografiskt Uttryck\n',
                     'Testgränden 47\n943 27\n## Typografiskt Uttryck\n',
                     '943 27\nTypografiskt Uttryck\n-------------------\n',
                     '943 27\nTypografiskt Uttryck\n=\n',
                     '943 27\nTypografiskt Uttryck\n--\n'):
            with self.subTest(text=text):
                self.skriv('RESEARCH.md',text)
                r=self.krok(query='Typografiskt Uttryck')
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_ogiltig_eller_olasbar_verksamhet_nekar(self):
        p=self.kund/'VERKSAMHET.json';ursprung=p.read_bytes()
        for data in (b'{',b'null',b'[]'):
            p.write_bytes(data);self.neka(self.krok())
        p.write_bytes(ursprung);p.chmod(0)
        try:self.neka(self.krok())
        finally:p.chmod(0o600)


if __name__ == '__main__': unittest.main()
