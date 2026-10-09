#!/usr/bin/env python3
"""21st.dev Builder i skaparsessionens körväg (ägarens val 2026-10-07; uppdraget 2026-10-08, 2C): mallen bär platshållaren
och nyckeln sätts in i en 0600-fil ur hemlighetsmappen, ateljéns argument bär den i strikt läge, kundvakten släpper bara
flödets tre verktyg med generiska frågor, metodkartan ger rollen komposition tjänsten med verktygsbeslut för alla 51
verktyg, och startkontrollen visar tjänsten som tilldelad med eller utan åtkomst. Inget nät."""
import contextlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import kompetens
import kundvakt
import korregister
import referenstjanster
import skapande
import startkontroll as sk

ROOT = Path(__file__).resolve().parents[3]
VERKTYG = ['mcp__21st__search', 'mcp__21st__get_component', 'mcp__21st__get_inspiration', 'mcp__21st__get_theme']  # get_theme: tokens ur ett tema (2026-10-09)
ALLA_21ST = ['mcp__21st__' + v for v in ('add_to_list', 'bookmark', 'create_bookmark_list', 'delete_component', 'delete_template', 'delete_theme',
             'edit_component', 'edit_profile', 'edit_take', 'edit_template', 'edit_theme', 'get_bookmark_list', 'get_changes', 'get_component',
             'get_generation', 'get_generation_job', 'get_inspiration', 'get_notes', 'get_profile', 'get_take', 'get_theme', 'get_usage',
             'list_bookmark_lists', 'list_bookmarks', 'list_team_components', 'list_team_libraries', 'list_team_lists', 'list_teams',
             'record_inspiration_feedback', 'record_take_outcome', 'remove_component_from_catalog', 'resubmit_component', 'search', 'search_logo',
             'search_picker', 'send_feedback', 'submit_component', 'update_note', 'upload_profile_media', 'video_apply_ops', 'video_create_project',
             'video_export', 'video_export_status', 'video_finalize_asset', 'video_get_doc', 'video_list_blocks', 'video_propose_variants',
             'video_search_blocks', 'video_snapshot', 'video_upload_asset', 'withdraw_component')]


class Tjugoforsta(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', '21st-provet'))).resolve()
        self.env = self.tmp / '21st.env'; self.env.write_text('# provets nyckel\nTWENTYFIRST_API_KEY=prov-nyckel-123\n'); self.env.chmod(0o600)
        self.stack.enter_context(patch.object(atelje, 'TJUGOFORSTA_ENV', self.env))
        self.stack.enter_context(patch.object(atelje, 'REFERO_ENV', self.tmp / 'refero.env'))  # saknas: mallen ges som den är
        self.slug = 'prov-21st'
        u = self.tmp / 'underlag' / self.slug; u.mkdir(parents=True)
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provfirman Trä AB', 'adress': {'ort': 'Exempelby'},
                                                       'kontaktvagar': [{'typ': 'telefon', 'varde': '000-111 22 33'}]}))
        (u / 'BRIEF.md').write_text('# Brief\n\n## §4 Primär handling\n\nRing. Ägaren Anna Svensson svarar.\n')
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))

    def test_mallen_och_nyckelfilen(self):
        cfg = json.loads((ROOT / 'kontroller' / 'mcp' / '21st.json').read_text())
        self.assertEqual(list(cfg['mcpServers']), ['21st'])
        self.assertEqual(cfg['mcpServers']['21st']['url'], 'https://21st.dev/api/mcp')
        self.assertEqual(cfg['mcpServers']['21st']['headers']['x-api-key'], '${TWENTYFIRST_API_KEY}', 'mallen bär aldrig nyckeln')
        f = atelje.tjugoforsta_mcp_fil()
        self.assertEqual(f, str(self.tmp / '21st-mcp.json')); self.assertEqual(os.stat(f).st_mode & 0o777, 0o600)
        self.assertIn('prov-nyckel-123', Path(f).read_text()); self.assertNotIn('${', Path(f).read_text())
        self.assertEqual(atelje.tjugoforsta_mcp_fil(), f, 'oförändrad nyckel skriver inte om')
        self.env.write_text('TWENTYFIRST_API_KEY=ny-nyckel\n')
        self.assertIn('ny-nyckel', Path(atelje.tjugoforsta_mcp_fil()).read_text(), 'en bytt nyckel förnyar filen')
        self.env.unlink()
        self.assertEqual(atelje.tjugoforsta_mcp_fil(), str(ROOT / 'kontroller' / 'mcp' / '21st.json'), 'utan nyckel ges mallen')
        self.assertEqual(atelje.refero_mcp_fil(), str(ROOT / 'kontroller' / 'mcp' / 'refero.json'), 'Refero utan nyckel: mallen')

    def test_sessionens_argument_bar_21st_sist_i_strikt_lage(self):
        a = atelje.session_args(['Read'], None, 10, 'm', 'high', (), self.slug)
        i = a.index('--mcp-config')
        self.assertIn('--strict-mcp-config', a)
        self.assertEqual([Path(x).name for x in a[i + 1:i + 5]], ['refero.json', 'mobbin.json', 'motion.json', '21st-mcp.json'])
        self.assertNotIn('prov-nyckel-123', ' '.join(a), 'nyckeln står aldrig i argumenten')
        self.assertNotIn('21st', ' '.join(atelje.session_args(['Read'], None, 10, 'm', 'high', ())), 'utan slug inga MCP:er')
        self.assertIn('mcp__21st__.*', json.loads(atelje.kundvakt(self.slug))['hooks']['PreToolUse'][0]['matcher'])

    def vakt(self, verktyg, indata):
        return kundvakt.provning(self.slug, atelje.UNDERLAG, {'tool_name': verktyg, 'tool_input': indata})

    def test_kundvakten_slapper_generiska_fragor_och_stoppar_kunduppgifter_och_andra_verktyg(self):
        self.assertTrue(skapande.forbjudna_termer(self.slug, atelje.UNDERLAG).get('ord'), 'fixturen ger kundens ord')
        self.assertIsNone(self.vakt('mcp__21st__search', {'query': 'hero section for a local service company', 'type': 'component', 'limit': 5}))
        self.assertIsNone(self.vakt('mcp__21st__get_component', {'id': 31460}))
        self.assertIsNone(self.vakt('mcp__21st__get_inspiration', {}))
        self.assertIsNone(self.vakt('mcp__21st__get_theme', {'id': '017e937d-377c-4f24-ba4a-dad5d75eb9e4'}))
        self.assertIn('kundens namn', self.vakt('mcp__21st__search', {'query': 'hero for Provfirman Trä'}) or '')
        self.assertIn('ort', self.vakt('mcp__21st__search', {'query': 'gallery Exempelby carpentry'}) or '')
        self.assertIn('personnamn', self.vakt('mcp__21st__search', {'query': 'testimonial Anna Svensson'}) or '')
        for v in ('mcp__21st__submit_component', 'mcp__21st__search_logo', 'mcp__21st__video_export', 'mcp__21st__get_usage'):
            self.assertIn('inte ett av flödets verktyg', self.vakt(v, {'query': 'x'}) or '', v)
        self.assertEqual(sorted(x for x in kundvakt.tillatna() if x.startswith('mcp__21st__')), sorted(VERKTYG))

    def test_metodkartan_ger_komposition_tjansten_med_beslut_for_alla_verktyg(self):
        k = kompetens.tolka()
        self.assertEqual(k['komposition']['mcp'], ['refero', 'mobbin', '21st'])
        self.assertEqual(kompetens.mcp_verktyg('21st'), VERKTYG)
        self.assertEqual(kompetens.slappta()['21st'], ['search', 'get_component', 'get_inspiration', 'get_theme'])
        self.assertEqual(kompetens.tjanstverktyg_fel(), [])
        self.assertEqual(kompetens.prova(), [])
        beslut = kompetens.tjanstverktyg()['21st']
        self.assertEqual(sorted(beslut), sorted(v.split('__')[-1] for v in ALLA_21ST), 'varje verktyg på servern (tools/list 2026-10-08) har ett beslut')
        self.assertEqual({v for v, x in beslut.items() if x['beslut'] == 'uppgift'}, {'search', 'get_component', 'get_inspiration', 'get_theme'})
        self.assertTrue(all(x['provat'] for v, x in beslut.items() if x['beslut'] == 'ingen uppgift'))
        p = '\n'.join(kompetens.prompt_rader('skapa', self.slug, 'k01'))
        self.assertIn('21st.dev Builder', p); self.assertIn('generiska', p)
        self.assertIn('21st.dev', p)

    def test_startkontrollen_visar_21st_som_tilldelad_med_och_utan_atkomst(self):
        alla = ALLA_21ST + ['mcp__motion__search-motion-docs'] + [v for t in referenstjanster.TJANSTER.values() for v in t['verktyg']]
        med = {'resultat': 'ok', 'tid': '2026-10-08T18:00:00Z', 'flaggor': ['--setting-sources', '--settings', '--strict-mcp-config', '--mcp-config'],
               'servrar': {'refero': 'connected', 'mobbin': 'connected', 'motion': 'connected', '21st': 'connected'}, 'verktyg': alla, 'skills': []}
        self.assertEqual(sk.mcp_atkomst(med, '21st'), ('provat', None))
        rader = {r['namn']: r for r in sk.atkomstrader(med, True)}
        self.assertEqual(rader['21st.dev i ateljéns session']['resultat'], 'ok'); self.assertIn('komposition', rader['21st.dev i ateljéns session']['detalj'])
        self.assertNotIn('övriga MCP i ateljéns session', rader, '21st står aldrig bland de övriga')
        utan = dict(med, servrar={'refero': 'connected', 'mobbin': 'connected', 'motion': 'connected'}, verktyg=[v for v in alla if not v.startswith('mcp__21st__')])
        r = {x['namn']: x for x in sk.atkomstrader(utan, True)}['21st.dev i ateljéns session']
        self.assertEqual(r['resultat'], 'fel'); self.assertIn('tilldelad men åtkomst saknas', r['detalj']); self.assertIn('stoppar inte starten', r['detalj'])
        self.assertIn('21st.json', r['detalj']); self.assertIn('komponenter', r['detalj'])
        roll = {x['roll']: x for x in sk.roller(med, [], True)}['komposition']
        self.assertEqual(roll['atkomst']['mcp']['21st']['tillstand'], 'provat')


if __name__ == '__main__':
    unittest.main()
