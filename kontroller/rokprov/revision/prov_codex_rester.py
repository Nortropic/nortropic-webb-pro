#!/usr/bin/env python3
"""Regressionsfall för resterna i GR-20261008-06af6ff-omgranskning-codex som går att pröva utan hela kandidatflödet:
R02 (kompetensläsningen per session: en tidigare sessions läsning döljer aldrig en ny sessions brist eller läsordning;
samma session-id är samma kontext) och R04 (planpromptens förhandsläsning av RIKTNINGSHISTORIK.json bara med ett
uttryckligt aktivt urval). R01 och R03 prövas genom kandidatflödets anropare i prov_revision.py (sk- och gk-scenariot).
Syntetiska transkript; inga modeller, inget nät."""
import contextlib
import json
import os
import re
from pathlib import Path
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import bildkedja
import kandidater as kd
import kompetens
import korregister
import skapande
import urval


class Kvitto(unittest.TestCase):
    """R02: kvittot per session."""
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kvittot per session'))).resolve()
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.filer = kompetens.lasfiler('skapa')
        self.skriv = 'kunder/prov/sajt/src/'

    def transkript(self, steg):
        sid = str(uuid.uuid4())
        rader = [json.dumps({'type': 'user', 'timestamp': '2026-10-08T21:00:00.000Z', 'message': {'role': 'user', 'content': 'uppdraget'}})]
        for i, (namn, inn) in enumerate(steg):
            rader.append(json.dumps({'type': 'assistant', 'timestamp': '2026-10-08T21:00:%02d.000Z' % (i + 1), 'message': {'role': 'assistant', 'content': [
                {'type': 'tool_use', 'id': 'u%d' % i, 'name': namn, 'input': inn}]}}))
            rader.append(json.dumps({'type': 'user', 'timestamp': '2026-10-08T21:00:%02d.500Z' % (i + 1), 'message': {'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': 'u%d' % i, 'content': 'ok'}]}}))
        p = bildkedja.PROJEKT / 'p'; p.mkdir(parents=True, exist_ok=True)
        (p / (sid + '.jsonl')).write_text('\n'.join(rader) + '\n')
        return sid

    def las(self, filer=None):
        return [('Read', {'file_path': str(atelje.ROOT / f)}) for f in (self.filer if filer is None else filer)]

    def skrivning(self):
        return [('Write', {'file_path': str(atelje.ROOT / self.skriv / 'pages' / 'index.astro')})]

    def test_ny_session_utan_karnan_syns(self):
        hel = self.transkript(self.las() + self.skrivning())
        tom = self.transkript(self.skrivning())  # en ny session (fortsättningen) som inte läser kärnan alls
        kv = kompetens.kvitto([{'session_id': hel}, {'session_id': tom}], 'skapa', skrivprefix=self.skriv)
        self.assertTrue(kv['verifierad']); self.assertFalse(kv['ofullstandig'])
        self.assertEqual(kv['saknas'], self.filer, 'en tidigare sessions läsning dolde en ny sessions brist (R02)')
        self.assertEqual(kv['lasta'], []); self.assertEqual(kv['fore_forsta_andring'], [])
        self.assertEqual([p['saknas'] for p in kv['per_session']], [[], self.filer])
        self.assertEqual([p['session'] for p in kv['per_session']], [hel, tom])
        karna = {r['roll']: r for r in kv['tillstand']}['komposition']['karna']
        self.assertNotEqual(karna['tillstand'], kompetens.LASKVITTO, karna)

    def test_las_efter_forsta_andring_i_en_ny_session_syns(self):
        hel = self.transkript(self.las() + self.skrivning())
        sen = self.transkript(self.skrivning() + self.las())  # ändrar först, läser sedan
        kv = kompetens.kvitto([{'session_id': hel}, {'session_id': sen}], 'skapa', skrivprefix=self.skriv)
        self.assertEqual(kv['saknas'], []); self.assertEqual(kv['fore_forsta_andring'], [], 'läsordningen maskerades av en annan session (R02)')
        self.assertEqual(kv['per_session'][1]['fore_forsta_andring'], [])
        self.assertEqual(kv['per_session'][0]['fore_forsta_andring'], self.filer)
        karna = {r['roll']: r for r in kv['tillstand']}['komposition']['karna']
        self.assertIn('läsordningen', karna['tillstand'])

    def test_varje_session_med_hela_karnan_ger_lasekvitto(self):
        a, b = self.transkript(self.las() + self.skrivning()), self.transkript(self.las() + self.skrivning())
        kv = kompetens.kvitto([{'session_id': a}, {'session_id': b}], 'skapa', skrivprefix=self.skriv)
        self.assertEqual((kv['saknas'], kv['fore_forsta_andring']), ([], self.filer))
        self.assertTrue(all(r['karna']['tillstand'] == kompetens.LASKVITTO for r in kv['tillstand'] if r['karna']['filer']))

    def test_samma_session_id_ar_samma_kontext(self):
        a = self.transkript(self.las() + self.skrivning())
        kv = kompetens.kvitto([{'session_id': a}, {'session_id': a}], 'skapa', skrivprefix=self.skriv)
        self.assertEqual(kv['sessioner'], {'forvantade': 1, 'sedda': 1, 'saknade': []})
        self.assertEqual((kv['samma_kontext'], len(kv['per_session'])), (1, 1))
        self.assertEqual(kv['saknas'], [])


class Planprompt(unittest.TestCase):
    """R04: riktningshistoriken läses inte i förväg utan ett uttryckligt urval."""
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'planpromptens urval'))).resolve()
        self.slug = 'prov-r04'
        self.u = self.root / 'underlag' / self.slug
        (self.u / 'atelje').mkdir(parents=True)
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        (self.u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Prov AB', 'kontaktvagar': []}))
        (self.u / 'BRIEF.md').write_text('# Brief\n')
        (self.u / skapande.HISTORIK).write_text(json.dumps({'riktningar': [{'namn': 'GAMMAL GRUNDIDÉ', 'utfall': 'underkänd'}]}))

    def prompt(self):
        with patch.object(kd, 'metod_rader', return_value=[]), patch.object(kd.kompetens, 'prompt_rader', return_value=[]), \
                patch.object(kd, 'research_rader', return_value=[]), patch.object(kd, 'material_rader', return_value=[]):
            return kd.plan_prompt(self.slug, 3, skiss=True)

    def test_historiken_pa_disk_men_urvalet_av(self):
        self.assertTrue((self.u / skapande.HISTORIK).is_file())
        p = self.prompt()
        self.assertNotIn('innan du skriver planen', p, 'planen läser riktningshistoriken i förväg utan urval (R04)')
        self.assertIn('slås upp', p)  # historiken bevaras och slås upp vid en konkret fråga (historik_rader)
        self.assertTrue((self.u / skapande.HISTORIK).is_file(), 'historiken raderas aldrig')

    def test_historiken_med_uttryckligt_urval(self):
        urval.skriv(self.slug, riktningshistorik=True)
        self.assertIn('%s innan du skriver planen' % skapande.HISTORIK, self.prompt())
        urval.skriv(self.slug, riktningshistorik=False)
        self.assertNotIn('innan du skriver planen', self.prompt())


FALSK_CLAUDE = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
d = Path(os.environ['PROV_R06_LOGG'])
d.write_text(json.dumps({'cwd': os.getcwd(), 'argv': sys.argv[1:], 'stdin': sys.stdin.read(),
                         'env': sorted(k for k in os.environ if k.startswith(('CLAUDE_CODE_ADDITIONAL', 'ANTHROPIC', 'REFERO')))}))
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'ok', 'session_id': '00000000-0000-4000-8000-000000000006'}))
"""


class Arbetsrot(unittest.TestCase):
    """R06: med växeln NWP_ARBETSROT=kundrepo startar skaparens session i kundprojektets eget repo, får motorns kompetens
    genom --add-dir och absoluta vägar, och behåller datagränserna; utan växeln är allt som förut. En attrapp av claude
    tar emot sessionen: det bevisar argumenten, arbetskatalogen och prompten, inte vad en verklig session laddar."""
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'arbetsroten i kundrepot'))).resolve()
        self.slug = 'prov-r06'
        self.u, self.k = self.tmp / 'underlag' / self.slug, self.tmp / 'kunder' / self.slug
        for d in (self.u, self.k, self.tmp / 'underlag' / 'annan-kund', self.tmp / 'kunder' / 'annan-kund'):
            d.mkdir(parents=True)
        (self.u / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Fiktiv Prov AB', 'fiktiv': True, 'kontaktvagar': []}))
        self.stack.enter_context(patch.multiple(atelje, KUNDER=self.tmp / 'kunder', UNDERLAG=self.tmp / 'underlag',
                                                REFERO_ENV=self.tmp / 'saknas' / 'refero.env', TJUGOFORSTA_ENV=self.tmp / 'saknas' / '21st.env'))
        self.stack.enter_context(patch.object(atelje, 'observerad', return_value=(None, None)))
        falsk = self.tmp / 'claude'; falsk.write_text(FALSK_CLAUDE); falsk.chmod(0o700)
        self.stack.enter_context(patch.object(atelje, 'claude', return_value=str(falsk)))
        self.logg = self.tmp / 'session.json'
        self.stack.enter_context(patch.dict(os.environ, {'PROV_R06_LOGG': str(self.logg), 'CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD': '1'}))
        for k_ in ('k01', 'k02'):  # två kandidater: den andra nekas den första
            kd.kdir(self.slug, k_).mkdir(parents=True, exist_ok=True); kd.ksajt(self.slug, k_).mkdir(parents=True, exist_ok=True)
        import kundrepo
        kundrepo.skapa(self.slug)  # fiktiv verksamhet: lokalt repo med kort CLAUDE.md, inget fjärrepo
        self.kundrepo = self.k / 'kundrepo'

    def kor(self):
        v = kd.verktyg(self.slug, 'k01') + kompetens.verktyg('skapa', self.slug, 'k01')
        prompt = '\n'.join(['Uppdraget: kunder/%s/kandidater/k01/sajt/src/pages/index.astro och underlag/%s/BRIEF.md.' % (self.slug, self.slug),
                             *kompetens.prompt_rader('skapa', self.slug, 'k01')])
        atelje.session(prompt, v, self.tmp / 'svar.json', nekas=kd.andra_nekas(self.slug, 'k01'), slug=self.slug)
        return json.loads(self.logg.read_text())

    def test_utan_vaxeln_ar_sessionen_som_forut(self):
        with patch.dict(os.environ, {'NWP_ARBETSROT': ''}):
            s = self.kor()
        self.assertEqual(Path(s['cwd']).resolve(), atelje.ROOT.resolve())
        self.assertNotIn('--add-dir', s['argv'])
        self.assertTrue(any(x.startswith('Write(./kunder/%s/kandidater/k01/sajt/src/' % self.slug) for x in s['argv']))
        self.assertEqual(s['env'], [], 'inga nycklar och inget CLAUDE.md-arv i miljön')

    def test_kundrepot_ar_arbetsroten_med_absoluta_regler_och_datagranserna_kvar(self):
        with patch.dict(os.environ, {'NWP_ARBETSROT': 'kundrepo'}):
            s = self.kor()
        rot, a = str(atelje.ROOT), s['argv']
        self.assertEqual(Path(s['cwd']).resolve(), self.kundrepo.resolve(), 'sessionen startar i kundrepots rot')
        self.assertTrue((self.kundrepo / '.git').is_dir() and (self.kundrepo / 'CLAUDE.md').is_file(), 'kundrepot är ett eget repo med kundens CLAUDE.md')
        self.assertIn('Fiktiv Prov AB', (self.kundrepo / 'CLAUDE.md').read_text())
        self.assertEqual(a[a.index('--add-dir') + 1], rot, 'motorns skills och filer nås genom --add-dir')
        self.assertEqual(s['env'], [], 'CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD följer aldrig med: motorns CLAUDE.md laddas inte')
        regler = a[a.index('--allowedTools') + 1:]
        self.assertFalse([x for x in regler if re.match(r'^\w+\(\./', x)], 'ingen relativ regel finns kvar')
        self.assertIn('Write(//%s/kunder/%s/kandidater/k01/sajt/src/**)' % (rot.strip('/'), self.slug), regler)
        self.assertIn('Bash(%s/.venv/bin/python %s/kontroller/forhandsvisa.py %s --kandidat k01 *)' % (rot, rot, self.slug), regler)
        self.assertIn('Bash(%s/.venv/bin/python %s/kontroller/material.py %s --kandidat k01 *)' % (rot, rot, self.slug), regler)
        self.assertIn('Read(//%s/underlag/annan-kund/**)' % rot.strip('/'), regler, 'en annan kunds underlag nekas fortfarande')
        self.assertIn('Read(//%s/kunder/%s/kandidater/k02/**)' % (rot.strip('/'), self.slug), regler, 'en annan kandidat nekas fortfarande')
        self.assertIn('Write(//%s/kontroller/**)' % rot.strip('/'), regler, 'motorns mekanik är fortfarande skrivskyddad')
        self.assertTrue(any(x.startswith('Read(//') and '.nortropic-hemligheter' in x for x in regler), 'hemlighetsmappen nekas')
        inst = json.loads(a[a.index('--settings') + 1])
        krok = inst['hooks']['PreToolUse'][0]['hooks'][0]['command']
        self.assertIn('"%s/kontroller/kundvakt.py"' % rot, krok); self.assertNotIn('$CLAUDE_PROJECT_DIR', krok)
        p = s['stdin']
        self.assertIn('%s/kunder/%s/kandidater/k01/sajt/src/pages/index.astro' % (rot, self.slug), p)
        self.assertFalse(re.search(r'(?<![\w/.~$-])(?:kunder|underlag|kunskap|kontroller|\.claude)/', p), 'ingen relativ motorväg finns kvar i prompten')
        karna = [Path(x) for x in re.findall(r'(%s/\.claude/skills/[\w./-]+\.md)' % re.escape(rot), p)]
        self.assertTrue(karna and all(x.is_file() for x in karna), 'kompetensens filer pekas ut med absoluta vägar som finns')
        mcp = a[a.index('--mcp-config') + 1:a.index('--mcp-config') + 5]
        self.assertEqual([Path(x).name for x in mcp], ['refero.json', 'mobbin.json', 'motion.json', '21st.json'], 'samma fyra MCP:er i strikt läge')

    def test_utan_kundrepo_stannar_sessionen_i_motorns_rot(self):
        import shutil as sh
        sh.rmtree(self.kundrepo)
        with patch.dict(os.environ, {'NWP_ARBETSROT': 'kundrepo'}):
            s = self.kor()
        self.assertEqual(Path(s['cwd']).resolve(), atelje.ROOT.resolve())
        self.assertNotIn('--add-dir', s['argv'])


if __name__ == '__main__':
    unittest.main()
