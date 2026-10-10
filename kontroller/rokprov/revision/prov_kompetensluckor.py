#!/usr/bin/env python3
"""De fyra observationsluckorna i kompetensens kvitton (GR-20261010-kompetens-integration); inga modeller eller nätanrop.

1. Underagenternas egna kontexter: en Task/Agent som ändrar koden prövas som en egen session; en startad underagent
   utan transkript är okänd; en underagents poster i huvudfilen räknas aldrig som huvudsessionens läsning.
2. Fri text om ett valt alternativ eller en lyckad aktivering bevisar ingenting: det redovisade prövas mot det observerade.
3. Bash i läsordningen: en skrivning i koden genom skalet, eller ett okänt program, före kärnan syns.
4. Slutgranskarens frysta kriteriepaket: läsningen av instruktionen och designreglerna observeras, och en granskare som
   bevisligen inte läste dem kan inte godkänna.

--bas kör samma fall mot HEAD:s bildkedja.py, kompetens.py, kandidater.py och granska.py inlästa i minnet (föreprovet:
fallen ska ge fel där luckan fanns).
"""
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import bildkedja  # noqa: E402
import kompetens  # noqa: E402
import korregister  # noqa: E402

if '--bas' in sys.argv:
    sys.argv.remove('--bas')

    def _bas(namn):
        src = subprocess.run(['git', 'show', 'HEAD:kontroller/%s.py' % namn], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        m = types.ModuleType(namn)
        m.__file__ = str(ROOT / 'kontroller' / ('%s.py' % namn))
        sys.modules[namn] = m
        exec(compile(src, m.__file__, 'exec'), m.__dict__)
        return m
    bildkedja = _bas('bildkedja')
    kompetens = _bas('kompetens')
    granska = _bas('granska')
    kandidater = _bas('kandidater')
else:
    import granska  # noqa: E402
    import kandidater  # noqa: E402

SID = '11111111-2222-4333-8444-555555555555'
SLUG = 'kompetensluckor-prov'


def anrop(i, namn, data):
    return {'type': 'tool_use', 'id': i, 'name': namn, 'input': data}


def svar(i, fel=False, text='ok'):
    return {'type': 'tool_result', 'tool_use_id': i, 'content': text, 'is_error': fel}


def rader(handelser, **extra):
    return ''.join(json.dumps(dict({'message': {'content': [h]}}, **extra)) + '\n' for h in handelser)


class Grund(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kompetensluckornas prov')))
        self.projekt = self.tmp / 'projects'
        (self.projekt / 'provprojekt').mkdir(parents=True)
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.projekt))

    def huvud(self, handelser, extra=''):
        f = self.projekt / 'provprojekt' / ('%s.jsonl' % SID)
        f.write_text(rader(handelser) + extra, encoding='utf-8')
        return f

    def underagent(self, agent, handelser):
        f = self.projekt / 'provprojekt' / SID / 'subagents' / ('agent-%s.jsonl' % agent)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(rader(handelser, isSidechain=True, agentId=agent), encoding='utf-8')
        return f

    def karna(self, pass_, prefix='k'):
        """Kärnan läst hel och rollens skills aktiverade: Skill för varje aktiverbar, Read med hela filen för resten."""
        filer = kompetens.lasfiler(pass_)
        skills, _ = kompetens.aktiverbara([f for r in kompetens.for_pass(pass_) for f in r['karna']])
        ut = []
        for n, s in enumerate(skills):
            ut += [anrop('%ss%d' % (prefix, n), 'Skill', {'skill': s}), svar('%ss%d' % (prefix, n))]
        for n, f in enumerate(filer):
            ut += [anrop('%sr%d' % (prefix, n), 'Read', {'file_path': str(ROOT / f), 'offset': 1, 'limit': 100000}), svar('%sr%d' % (prefix, n))]
        return ut


class Lucka3Bash(Grund):
    """Läsordningen omfattar skalet."""
    prefix = 'kunder/%s/sajt/' % SLUG

    def lasning(self, fore):
        self.huvud(fore + self.karna('helbygge'))
        return bildkedja.metodlasning(SID, kompetens.lasfiler('helbygge'), skrivprefix=self.prefix)

    def test_skalskrivning_fore_karnan_syns(self):
        ml = self.lasning([anrop('b1', 'Bash', {'command': 'cat > %ssrc/pages/index.astro <<EOF\n<h1>x</h1>\nEOF' % self.prefix}), svar('b1')])
        self.assertTrue(ml['forsta_skrivning'], 'en heredoc till sajtens källa är en ändring')
        self.assertEqual(ml['fore'], [], 'kärnan lästes först efter skalets skrivning')

    def test_okant_program_fore_karnan_ar_mojlig_andring(self):
        ml = self.lasning([anrop('b1', 'Bash', {'command': '.venv/bin/python underlag/%s/skript/bygg.py' % SLUG}), svar('b1')])
        self.assertTrue(ml['forsta_skrivning'])
        self.assertEqual(ml['fore'], [])

    def test_materialets_anvandning_ar_en_andring(self):
        ml = self.lasning([anrop('b1', 'Bash', {'command': '.venv/bin/python kontroller/material.py %s --kandidat k01 --anvand m-01 --plats hero' % SLUG}), svar('b1')])
        self.assertEqual(ml['fore'], [])

    def test_lasande_kommandon_och_nekade_anrop_ar_ingen_andring(self):
        ml = self.lasning([anrop('b1', 'Bash', {'command': 'ls %ssrc && grep -rn hero %ssrc 2>/dev/null | head' % (self.prefix, self.prefix)}), svar('b1'),
                           anrop('b2', 'Bash', {'command': 'cp /tmp/x %ssrc/a.astro' % self.prefix}),
                           svar('b2', True, 'Permission to use Bash with command cp /tmp/x has been denied.'),
                           anrop('b3', 'Bash', {'command': 'npm run build --prefix %s' % self.prefix}), svar('b3')])
        self.assertFalse(ml['forsta_skrivning'])
        self.assertEqual(sorted(ml['fore']), sorted(kompetens.lasfiler('helbygge')))

    def test_kravet_faller_pa_sen_karna_efter_skalet(self):
        self.huvud([anrop('b1', 'Bash', {'command': 'cp /tmp/x %ssrc/a.astro' % self.prefix}), svar('b1')] + self.karna('helbygge'))
        kv = kompetens.kvitto([SID], 'helbygge', skrivprefix=self.prefix)
        self.assertTrue(any('läst först efter första ändringen' in b for b in kompetens.kravbrister(kv, 'helbygge')))


class Lucka1Underagenter(Grund):
    prefix = 'kunder/%s/sajt/' % SLUG

    def kvitto(self):
        kv = kompetens.kvitto([SID], 'helbygge', skrivprefix=self.prefix)
        return kv, [b for b in kompetens.kravbrister(kv, 'helbygge') if 'underagent' in b]

    def test_skrivande_underagent_utan_karna_ger_brist(self):
        self.huvud(self.karna('helbygge') + [anrop('t1', 'Task', {'prompt': 'bygg undersidan'}), svar('t1')])
        self.underagent('a1', [anrop('w1', 'Write', {'file_path': str(ROOT / self.prefix / 'src/pages/om.astro'), 'content': 'x'}), svar('w1')])
        _kv, brister = self.kvitto()
        self.assertTrue(any('ändrade utan kärnan' in b for b in brister), brister)
        self.assertTrue(any('Skill aktiverades inte' in b for b in brister), brister)

    def test_skrivande_underagent_med_egen_karna_godkanns(self):
        self.huvud(self.karna('helbygge') + [anrop('t1', 'Task', {'prompt': 'bygg undersidan'}), svar('t1')])
        self.underagent('a1', self.karna('helbygge', 'u') + [anrop('w1', 'Write', {'file_path': str(ROOT / self.prefix / 'src/pages/om.astro'), 'content': 'x'}), svar('w1')])
        kv, brister = self.kvitto()
        self.assertEqual(brister, [])
        self.assertEqual(len(kv['per_session'][0]['underagenter']), 1)

    def test_lasande_underagent_har_inga_krav(self):
        self.huvud(self.karna('helbygge') + [anrop('t1', 'Task', {'prompt': 'läs rubrikerna'}), svar('t1')])
        self.underagent('a1', [anrop('r1', 'Read', {'file_path': str(ROOT / 'README.md')}), svar('r1')])
        _kv, brister = self.kvitto()
        self.assertEqual(brister, [])

    def test_underagent_utan_transkript_ar_okand(self):
        self.huvud(self.karna('helbygge') + [anrop('t1', 'Agent', {'prompt': 'bygg'}), svar('t1')])
        _kv, brister = self.kvitto()
        self.assertTrue(any('utan observerat transkript' in b for b in brister), brister)

    def test_underagentens_poster_i_huvudfilen_ar_inte_huvudsessionens(self):
        # äldre format: underagentens läsning står i huvudfilen med isSidechain; huvudsessionen läste inget själv
        self.huvud([anrop('t1', 'Task', {'prompt': 'läs'}), svar('t1')], extra=rader(self.karna('helbygge', 'u'), isSidechain=True, agentId='a9'))
        kv = kompetens.kvitto([SID], 'helbygge', skrivprefix=self.prefix)
        self.assertEqual(kv['per_session'][0]['lasta'], [], 'underagentens läsning är inte huvudsessionens')


class Lucka2Redovisning(Grund):
    def kv(self, skill_anrop=(), valda=()):
        return {'verifierad': True, 'valda': list(valda),
                'per_session': [{'session': SID, 'lasta': [], 'valda': list(valda), 'skill_anrop': list(skill_anrop)}]}

    def test_redovisat_alternativ_utan_aktivering_ger_brist(self):
        so = {'valda': ['motion/SKILL.md: rörelsens stagger'], 'teknikval': []}
        self.assertTrue(kandidater.passbrister('rorelse', so, self.kv()), 'fri text är ingen aktivering')

    def test_redovisat_och_observerat_godkanns(self):
        so = {'valda': ['motion/SKILL.md: rörelsens stagger'], 'teknikval': []}
        self.assertEqual(kandidater.passbrister('rorelse', so, self.kv(skill_anrop=['motion'])), [])

    def test_redovisad_lyckad_aktivering_och_kodandring_provas(self):
        so = {'aktivering': [{'skill': 'emil-design-eng', 'lyckades': True, 'fel': ''}],
              'kod_andrad': [{'skill': 'better-layout', 'vad': 'v', 'var': 'v', 'varfor': 'v'}], 'teknikval': []}
        brister = kandidater.passbrister('granskning', so, self.kv())
        self.assertTrue(any('emil-design-eng' in b for b in brister) and any('better-layout' in b for b in brister), brister)

    def test_passade_inte_och_okanda_namn_provas_inte(self):
        so = {'passade_inte': [{'skill': 'motion', 'varfor': 'stilla sida'}], 'kod_andrad': [{'skill': 'CSS', 'vad': '', 'var': '', 'varfor': ''}],
              'teknikval': []}
        self.assertEqual(kandidater.passbrister('rorelse', so, self.kv()), [])

    def test_skisskritikens_val_provas(self):
        brister = kompetens.redovisade_brister(self.kv(), 'skisskritik', {'valda': [{'fil': 'impeccable/reference/critique.md', 'varfor': 'x'}]}) \
            if hasattr(kompetens, 'redovisade_brister') else []
        roll = [f for r in kompetens.for_pass('skisskritik') for f in r['karna'] + r['valj']]
        if 'impeccable/reference/critique.md' in roll:
            self.assertTrue(brister)


class Lucka4Granskaren(Grund):
    def lasning(self, lasta):
        h = []
        for n, f in enumerate(lasta):
            h += [anrop('r%d' % n, 'Read', {'file_path': str(ROOT / f)}), svar('r%d' % n)]
        self.huvud(h)
        return bildkedja.lasning(SID, granska.granskarkrav(None, [], []))

    def test_kriterierna_ar_ett_lasekrav(self):
        self.assertIn('kriterier', granska.granskarkrav(None, [], []))

    def test_granskare_som_inte_last_kriterierna_kan_inte_godkanna(self):
        s = [{'granskare': 1, 'lasning': self.lasning(['kritik/GRANSKARE.md'])}]
        brister = granska.kriteriebrister(s) if hasattr(granska, 'kriteriebrister') else []
        self.assertTrue(brister)
        self.assertFalse(s[0]['kriterier_lasta'])
        res = {'kriterier': {k: {'betyg': 9, 'visa': True} for k in granska.KRITERIER}, 'blockerande': [], 'metodbrister': brister}
        self.assertFalse(granska.godkand(res))

    def test_last_kriteriepaket_och_saknat_transkript(self):
        s = [{'granskare': 1, 'lasning': self.lasning(list(granska.KRITERIEFILER))},
             {'granskare': 2, 'lasning': {'verifierad': False, 'grupper': {}}}]
        self.assertEqual(granska.kriteriebrister(s), [])
        self.assertEqual([x['kriterier_lasta'] for x in s], [True, None])


if __name__ == '__main__':
    unittest.main(verbosity=1)
