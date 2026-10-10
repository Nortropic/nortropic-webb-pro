#!/usr/bin/env python3
"""Lokala skills: faktisk aktivering, entydiga namn och ordning. Inga modellanrop."""
import contextlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bildkedja
import korregister


class Skillnamn(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.rot = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'skillnamnsprovet')))
        self.stack.enter_context(patch.object(bildkedja, 'ROOT', self.rot))
        self.skill('form-variant', 'variant')
        self.skill('frontend', 'frontend')

    def skill(self, mapp, namn):
        f = self.rot / '.claude' / 'skills' / mapp / 'SKILL.md'
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('---\nname: %s\n---\n# Metod\nLokal provmetod.\n' % namn)
        return f

    def kvitto(self, handelser):
        f = self.rot / 'transkript.jsonl'
        f.write_text(''.join(json.dumps({'message': {'content': [h]}}) + '\n' for h in handelser))
        with patch.object(bildkedja, 'transkript', return_value=f):
            return bildkedja.metodlasning('prov', ['.claude/skills/form-variant/SKILL.md'], skrivprefix='sajt/src/')

    def anrop(self, i, namn, data):
        return {'type': 'tool_use', 'id': i, 'name': namn, 'input': data}

    def svar(self, i, fel=False):
        return {'type': 'tool_result', 'tool_use_id': i, 'content': 'prov', 'is_error': fel}

    def test_metadata_namn_och_mapp_ar_samma_lokala_skill(self):
        self.assertEqual(bildkedja.skillnamn('variant'), 'form-variant')
        self.assertEqual(bildkedja.skillnamn('form-variant'), 'form-variant')
        self.assertEqual(bildkedja.skillkommando('form-variant'), 'variant')
        self.assertEqual(bildkedja.skillkommando('frontend'), 'frontend')

    def test_okant_och_plugin_prefix_blir_inte_lokal_skill(self):
        self.assertEqual(bildkedja.skillnamn('okand'), 'okand')
        self.assertEqual(bildkedja.skillnamn('annan:variant'), 'annan:variant')
        q = self.kvitto([self.anrop('s', 'Skill', {'skill': 'annan:form-variant'}), self.svar('s')])
        self.assertTrue(q['saknas'], 'ett främmande plugins suffix bevisar inte den lokala skillen')

    def test_namnkrock_kan_aldrig_ge_laskredit(self):
        self.skill('annan', 'form-variant')
        self.assertIsNone(bildkedja.skillnamn('form-variant'))
        self.assertEqual(bildkedja.skillkommando('form-variant'), 'variant')
        q = self.kvitto([self.anrop('s', 'Skill', {'skill': 'form-variant'}), self.svar('s')])
        self.assertTrue(q['saknas'])
        self.assertNotIn('form-variant', q['skill_anrop'])

    def test_alias_krock_nekas_och_entydigt_mappnamn_finns_kvar(self):
        self.skill('annan', 'variant')
        self.assertIsNone(bildkedja.skillnamn('variant'))
        self.assertEqual(bildkedja.skillkommando('form-variant'), 'form-variant')

    def test_inventoryfel_ar_okant_inte_en_entydig_aktivering(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError('provets läsfel')):
            self.assertIsNone(bildkedja.skillnamn('variant'))
            self.assertIsNone(bildkedja.skillkommando('form-variant'))

    def test_citerat_metadatanamn_lases_ur_frontmatter(self):
        self.skill('annan', '"annan-metod"')
        self.assertEqual(bildkedja.skillnamn('annan-metod'), 'annan')
        self.assertEqual(bildkedja.skillkommando('annan'), 'annan-metod')

    def test_lyckat_aliasfore_svar_ger_ratt_lasning_och_ordning(self):
        q = self.kvitto([self.anrop('s', 'Skill', {'skill': 'variant'}), self.svar('s'),
                        self.anrop('w', 'Write', {'file_path': 'sajt/src/sida.astro'}), self.svar('w')])
        self.assertEqual(q['saknas'], [])
        self.assertEqual(q['skill_anrop'], ['form-variant'])
        self.assertEqual(q['skill_fore'], ['form-variant'])
        self.assertEqual(q['skill_efter'], [])

    def test_aktiveringssvaret_maste_komma_fore_andringen(self):
        q = self.kvitto([self.anrop('s', 'Skill', {'skill': 'variant'}),
                        self.anrop('w', 'Write', {'file_path': 'sajt/src/sida.astro'}), self.svar('w'), self.svar('s')])
        self.assertEqual(q['skill_fore'], [])
        self.assertEqual(q['skill_efter'], ['form-variant'])

    def test_read_ger_lasning_men_ingen_aktivering(self):
        q = self.kvitto([self.anrop('r', 'Read', {'file_path': '.claude/skills/form-variant/SKILL.md'}), self.svar('r')])
        self.assertEqual(q['saknas'], [])
        self.assertEqual(q['skill_anrop'], [])
        self.assertEqual(q['skill_fore'], [])

    def test_fel_och_obesvarat_anrop_ger_inte_aktivering(self):
        q = self.kvitto([self.anrop('s', 'Skill', {'skill': 'variant'}), self.svar('s', fel=True),
                        self.anrop('u', 'Skill', {'skill': 'form-variant'})])
        self.assertTrue(q['saknas'])
        self.assertEqual(q['skill_anrop'], [])
        self.assertEqual(q['skill_fel'], ['form-variant'])
        self.assertEqual(q['skill_fore'], [])


if __name__ == '__main__':
    unittest.main()
