#!/usr/bin/env python3
"""Helbyggets verkliga argumentberedning, med falsk claude och eget hem. Inga nätanrop.

Provet kör kor.sh:s argumentblock oförändrat i en isolerad kopia, aldrig kor.sh:s byggstart.
Det visar transport, vakt och hemlighetsgräns, inte extern åtkomst eller designkvalitet.
"""
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister
import bildkedja
import byggmcp
import kompetens
import korslut

ROOT = Path(__file__).resolve().parents[3]


class ByggMcp(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'helbyggets MCP-prov'))).resolve()
        self.rot = self.tmp / 'repo'; self.rot.mkdir()
        self.hem = self.tmp / 'hem'; self.hem.mkdir()
        self.k = self.rot / 'kontroller'; self.k.mkdir()
        for p in (ROOT / 'kontroller').glob('*.py'):
            shutil.copyfile(p, self.k / p.name)
        shutil.copytree(ROOT / 'kontroller/mcp', self.k / 'mcp')
        shutil.copytree(ROOT / 'kunskap', self.rot / 'kunskap')
        for namn in ('bygg-sajt', 'frontend-design', 'modern-web-guidance'):
            shutil.copytree(ROOT / '.claude/skills' / namn, self.rot / '.claude/skills' / namn)
        (self.rot / '.venv').symlink_to(ROOT / '.venv', target_is_directory=True)
        self.slug = 'prov-mcp-bygge'
        self.run = self.rot / 'kunder' / self.slug / 'korningar/prov'; self.run.mkdir(parents=True)
        u = self.rot / 'underlag' / self.slug; u.mkdir(parents=True)
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Syntetisk Provfirma', 'adress': {'ort': 'Provort'}, 'kontaktvagar': []}))
        secret = self.hem / '.nortropic-hemligheter/webb-pro'; secret.mkdir(parents=True)
        (secret / 'refero.env').write_text('REFERO_MCP_TOKEN=syntetisk-refero-nyckel\n')
        (secret / '21st.env').write_text('TWENTYFIRST_API_KEY=syntetisk-21st-nyckel\n')
        self.capture = self.tmp / 'capture.json'
        self.fake = self.tmp / 'claude'
        self.fake.write_text('#!' + sys.executable + '\nimport json,os,sys\njson.dump({"args":sys.argv[1:],"prompt":sys.stdin.read(),"tokens":{k: k in os.environ for k in ("REFERO_MCP_TOKEN","TWENTYFIRST_API_KEY")}},open(os.environ["CAPTURE"],"w"))\n')
        self.fake.chmod(0o755)
        text = (ROOT / 'kor.sh').read_text()
        start = text.index('# Referenstjänster via MCP')
        end = text.index('# R06: med NWP_ARBETSROT', start)
        # Dessa är produktionskodens två delar: argumenten, och miljöns rensningslista.
        rensa = text[text.index('RENSA=('):text.index('\nwhile IFS=', text.index('RENSA=('))]
        self.script = self.tmp / 'argument.sh'
        self.sid = str(uuid.uuid4())
        self.script.write_text('set -euo pipefail\nROOT="$PROV_ROT"\nSLUG=prov-mcp-bygge\nSTAMP=prov\nPROMPT="Syntetiskt uppdrag"\nSESSION_ID="' + self.sid + '"\nVERKSAMHET=""\nFRYSTA=()\nGODKAND=""\nstopp(){ echo "$1" >&2; exit 2; }\n' + text[start:end] + '\n' + rensa + '\nprintf "%s" "$PROMPT" | env "${RENSA[@]}" "$FALSK_CLAUDE" "${ARGS[@]}"\n')

    def run_block(self, val='', sandlada='pa'):
        env = dict(os.environ, HOME=str(self.hem), PROV_ROT=str(self.rot), CAPTURE=str(self.capture), FALSK_CLAUDE=str(self.fake),
                   NWP_MCP_CONFIG=val, NWP_SANDLADA=sandlada,
                   REFERO_MCP_TOKEN='far-inte-folja-med', TWENTYFIRST_API_KEY='far-inte-folja-med')
        env.pop('NWP_SLUG', None)
        return subprocess.run(['bash', str(self.script)], cwd=self.rot, env=env, capture_output=True, text=True, timeout=30)

    def test_fyra_tjanster_med_vakt_och_sandlada_utan_nycklar_i_argument_eller_miljo(self):
        p = self.run_block()
        self.assertEqual(p.returncode, 0, p.stderr)
        d = json.loads(self.capture.read_text()); args = d['args']
        self.assertIn('--mcp-config', args, 'helbygget saknar sina tilldelade MCP-tjänster')
        i = args.index('--mcp-config')
        self.assertEqual([Path(x).name for x in args[i+1:i+5]], ['refero-mcp.json', 'mobbin.json', 'motion.json', '21st-mcp.json'])
        self.assertIn('--strict-mcp-config', args)
        self.assertEqual(args.count('--settings'), 1)
        settings = json.loads(args[args.index('--settings')+1])
        self.assertTrue(settings['sandbox']['enabled'])
        self.assertIn('kundvakt.py', json.dumps(settings['hooks']))
        self.assertIn('mcp__21st__.*', json.dumps(settings['hooks']))
        allow = args[args.index('--allowedTools')+1:args.index('--disallowedTools')]
        self.assertIn('ToolSearch', allow)
        self.assertEqual(args[args.index('--session-id')+1], self.sid)
        self.assertIn('Bash(.venv/bin/python -B kontroller/uxsok.py *)', allow)
        self.assertIn('Bash(.venv/bin/python kontroller/design.py %s --skriv)' % self.slug, allow)
        self.assertNotIn('Bash(.venv/bin/python kontroller/design.py *)', allow)
        self.assertIn('helbyggets obligatoriska skills', d['prompt'])
        self.assertIn('bygg-sajt/SKILL.md', d['prompt'])
        self.assertFalse(any(x.startswith('mcp__') for x in allow), 'vakten får aldrig kringgås av allowedTools')
        self.assertEqual(d['tokens'], {'REFERO_MCP_TOKEN': False, 'TWENTYFIRST_API_KEY': False})
        self.assertNotIn('syntetisk-', json.dumps(args))
        self.assertTrue(any('.nortropic-hemligheter' in x for x in settings['permissions']['deny']))
        # Samma krok som argumenten startar: generisk läsning går, kunduppgifter och
        # publicering stoppas. Attrappen ovan kör aldrig själva MCP-servern.
        for verktyg, indata, kod in (
                ('mcp__21st__search', {'query': 'service business gallery'}, 0),
                ('mcp__21st__search', {'query': 'Syntetisk Provfirma gallery'}, 2),
                ('mcp__21st__submit_component', {'query': 'gallery'}, 2)):
            r = subprocess.run([sys.executable, '-B', str(self.k / 'kundvakt.py'), self.slug, str(self.rot / 'underlag')],
                               input=json.dumps({'tool_name': verktyg, 'tool_input': indata}), capture_output=True, text=True,
                               cwd=self.rot, env=dict(os.environ, HOME=str(self.hem)), timeout=30)
            self.assertEqual(r.returncode, kod, (verktyg, r.stderr))

    def test_av_och_explicit_tjanst_och_okand_konfiguration(self):
        p = self.run_block('av', 'av'); self.assertEqual(p.returncode, 0, p.stderr)
        args = json.loads(self.capture.read_text())['args']
        self.assertNotIn('--mcp-config', args)
        p = self.run_block(str(self.k / 'mcp/mobbin.json'), 'av'); self.assertEqual(p.returncode, 0, p.stderr)
        args = json.loads(self.capture.read_text())['args']; i = args.index('--mcp-config')
        self.assertEqual(args[i+1], str(self.k / 'mcp/mobbin.json'))
        settings = json.loads(args[args.index('--settings')+1])
        self.assertIn('kundvakt.py', json.dumps(settings['hooks']))
        self.capture.unlink()
        p = self.run_block(str(self.tmp / 'mobbin.json'))
        self.assertEqual(p.returncode, 2)
        self.assertFalse(self.capture.exists(), 'okänd konfiguration startar inte sessionen')

    def bevisdata(self):
        k = self.rot / 'kunder' / self.slug
        start = {'korning': 'prov', 'session_id': self.sid}
        (self.run / 'START.json').write_text(json.dumps(start))
        (k / 'korning-prov.jsonl').write_text('\n'.join(json.dumps(d) for d in [
            {'type': 'system', 'subtype': 'init', 'session_id': self.sid},
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': self.sid}]) + '\n')
        return k, start

    def test_kvitto_ur_egen_sessions_transkript_och_ingen_kredit_for_bara_read(self):
        k, _ = self.bevisdata()
        pr = self.tmp / 'transkript' / 'p'; pr.mkdir(parents=True)
        f = pr / (self.sid + '.jsonl')
        skills, _ = kompetens.aktiverbara([f for r in kompetens.for_pass('helbygge') for f in r['karna']])
        steg = [('Skill', {'skill': bildkedja.skillkommando(s) or s}) for s in skills]
        steg += [('Read', {'file_path': str(ROOT / p)}) for p in kompetens.lasfiler('helbygge')]
        steg += [('Write', {'file_path': str(ROOT / 'kunder' / self.slug / 'sajt/src/pages/index.astro')})]
        def transkript(steg_):
            rader = []
            for i, (namn, inp) in enumerate(steg_):
                rader.append({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': str(i), 'name': namn, 'input': inp}]}})
                rader.append({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': str(i), 'content': 'syntetiskt svar'}]}})
            f.write_text('\n'.join(json.dumps(r) for r in rader) + '\n')
        with patch.object(bildkedja, 'PROJEKT', pr.parent):
            transkript(steg)
            kv = byggmcp.kompetensbevis(k, 'prov')
            self.assertTrue(kv['uppfyllt'], kv['brister'])
            self.assertEqual(kv['session_id'], self.sid)
            self.assertEqual(kv['kvitto']['sessioner']['sedda'], 1)
            transkript([s for s in steg if s[0] != 'Skill'])
            kv = byggmcp.kompetensbevis(k, 'prov')
            self.assertFalse(kv['uppfyllt'])
            self.assertTrue(any('Skill-aktivering' in b for b in kv['brister']))
            transkript([steg[-1]] + steg[:-1])
            kv = byggmcp.kompetensbevis(k, 'prov')
            self.assertFalse(kv['uppfyllt'], 'sen läsning/aktivering räknades som uppfylld')
            transkript([('Write', {'file_path': str(ROOT / 'kunder' / self.slug / 'sajt/astro.config.mjs')})] + steg)
            kv = byggmcp.kompetensbevis(k, 'prov')
            self.assertFalse(kv['uppfyllt'], 'tidig konfigurationsändring utanför src fick försvinna ur ordningen')

    def test_typfel_annan_session_och_saknat_transkript_nekar(self):
        k, start = self.bevisdata()
        native = self.tmp / 'giltigt-syntetiskt-transkript.jsonl'
        native.write_text('{"type":"assistant"}\n')
        for sid in (None, 1, {}, [], str(uuid.uuid4())):
            (self.run / 'START.json').write_text(json.dumps(dict(start, session_id=sid)))
            # Ett tillgängligt transkript får inte maskera en trasig bindning genom
            # att nästa skydd ändå nekar för saknad fil (mutationsprovet prövar detta).
            with patch.object(bildkedja, 'transkript', return_value=native), \
                 patch.object(kompetens, 'kvitto', side_effect=AssertionError('främmande session får inte läsas')) as observera:
                self.assertFalse(byggmcp.kompetensbevis(k, 'prov')['uppfyllt'])
                observera.assert_not_called()
        (self.run / 'START.json').write_text(json.dumps(start))
        with patch.object(bildkedja, 'PROJEKT', self.tmp / 'saknas'):
            self.assertFalse(byggmcp.kompetensbevis(k, 'prov')['uppfyllt'])
        for korning in (None, [], '../annan'):
            self.assertFalse(byggmcp.kompetensbevis(k, korning)['uppfyllt'])

    def test_saknat_felmarkerat_eller_trunkerat_slutresultat_nekar(self):
        k, _ = self.bevisdata()
        native = self.tmp / 'giltigt-syntetiskt-transkript.jsonl'
        native.write_text('{"type":"assistant"}\n')
        logg = k / 'korning-prov.jsonl'
        hel = logg.read_text()
        rader = [json.loads(x) for x in hel.splitlines()]
        fel = [json.dumps(rader[0]) + '\n',
               json.dumps(rader[0]) + '\n{"type":"result"',
               '\n'.join(json.dumps(x) for x in [rader[0], dict(rader[1], is_error=True)]) + '\n',
               '\n'.join(json.dumps(x) for x in [rader[0], dict(rader[1], subtype='error_max_turns')]) + '\n',
               '\n'.join(json.dumps(x) for x in [rader[0], rader[0], rader[1]]) + '\n']
        for text in fel:
            logg.write_text(text)
            with patch.object(bildkedja, 'transkript', return_value=native), patch.object(kompetens, 'kvitto') as kvitto:
                self.assertFalse(byggmcp.kompetensbevis(k, 'prov')['uppfyllt'])
                kvitto.assert_not_called()
        logg.write_text(hel)
        pr = self.tmp / 'transkript' / 'p'; pr.mkdir(parents=True)
        f = pr / (self.sid + '.jsonl')
        for innehall in ('', '{"type":"assistant"', '[]\n', '{"type":"assistant"}\n{'):
            f.write_text(innehall)
            with patch.object(bildkedja, 'PROJEKT', pr.parent), patch.object(kompetens, 'kvitto') as kvitto:
                self.assertFalse(byggmcp.kompetensbevis(k, 'prov')['uppfyllt'])
                kvitto.assert_not_called()

    def test_korsluts_riktiga_ingang_nekar_utan_kvitto_och_bevarar_felkoder(self):
        k, _ = self.bevisdata()
        bevis = {'uppfyllt': False, 'brister': ['syntetisk saknad aktivering'], 'korning': 'prov'}
        sparade = []
        def post(*a, **kw):
            d = {'slutkod': a[13], 'kontroller': {'kompetens': kw.get('kompetensbevis')}}
            sparade.append(d); return d
        with contextlib.ExitStack() as st:
            st.enter_context(patch.object(byggmcp, 'kompetensbevis', side_effect=lambda *a: dict(bevis)))
            st.enter_context(patch.multiple(korslut, las_objekt=lambda *a: (None, None),
                vald_granskning=lambda *a: (None, None, None, None), andrade=lambda *a: [], hashlista=lambda *a: {},
                hashlistorna=lambda *a: ({'varde': True}, []), ar_godkant=lambda *a: (True, None),
                processer_efter=lambda: {'varde': True, 'text': 'syntetiskt stoppade'}, kopiera_bevis=lambda *a: {},
                agaren_vid_slut=lambda *a, **kw: ({'varde': None}, {}), agarens_domar=lambda *a: ([], None),
                slutpost=post, skriv_slutpost=lambda *a: self.tmp / 'post', text=lambda *a: 'syntetiskt slutbesked', skriv_ut=lambda *a: None))
            args = ['korslut', str(k), '0', 'fore', 'efter', 'prov']
            self.assertEqual(korslut.main(args), 1)
            self.assertEqual(sparade[-1]['kontroller']['kompetens'], bevis)
            bevis.update(uppfyllt=True, brister=[])
            self.assertEqual(korslut.main(args), 0)
            bevis.update(uppfyllt=False, brister=['syntetisk brist'])
            self.assertEqual(korslut.main(args[:2] + ['7'] + args[3:]), 4)
            with patch.object(korslut, 'andrade', return_value=['kontroller/fel.py']):
                self.assertEqual(korslut.main(args), 3)


    def test_aldre_slutpost_utan_kompetens_blir_inte_aktuellt_leveransklar(self):
        import granska
        import kundstart_kalla
        import prova
        k, _ = self.bevisdata()
        dist = k / 'sajt/dist'; dist.mkdir(parents=True)
        (dist / 'index.html').write_text('<p>Syntetiskt prov</p>')
        post = {'typ': korslut.TYP, 'korning': 'prov', 'slutkod': 0,
                'dist_sha256': prova.dist_hash(dist), 'metod': {}, 'startsida': {},
                'tillstand': {n: {'varde': True, 'text': 'syntetiskt godkänt'} for n, _ in korslut.TILLSTAND},
                'kontroller': {}}
        f = self.run / 'SLUT.json'
        with patch.object(kundstart_kalla, 'giltig', return_value=True), \
             patch.object(granska, 'aktuell_metod', return_value={}), \
             patch.object(korslut, 'agarens_dom', return_value={'varde': True}), \
             patch.object(korslut, 'avbrutna', return_value=[]):
            for bevis, vantat in ((None, False), ({'uppfyllt': False, 'brister': ['syntetisk brist']}, False),
                                   ({'uppfyllt': True, 'korning': 'prov', 'session_id': self.sid}, True)):
                post['kontroller'] = {} if bevis is None else {'kompetens': bevis}
                f.write_text(json.dumps(post))
                fore = f.read_bytes()
                nu = korslut.aktuell(k)
                self.assertIs(nu['tillstand']['klart_for_leverans']['varde'], vantat)
                self.assertEqual(nu['slutkod'], 0, 'en äldre råslutkod ska inte skrivas om')
                self.assertEqual(nu['tillstand']['designgranskaren_godkanner'], post['tillstand']['designgranskaren_godkanner'])
                if not vantat:
                    self.assertIn('kompetens', nu['tillstand']['klart_for_leverans']['text'])
                self.assertEqual(f.read_bytes(), fore, 'aktuell() får inte ändra historikfilen')


if __name__ == '__main__':
    unittest.main()
