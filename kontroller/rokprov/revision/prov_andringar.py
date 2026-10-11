#!/usr/bin/env python3
"""Ändringsfliken (ägarens tillägg 2026-10-11; kunskap/andringar.md): webbplatsens ändringsagent i kundrepots arbetskopia,
prövad i en isolerad rot med provprojektet (andringar_fixtur.py) och provagenten (kontroller/rokprov/andringar/fejkclaude.py)
i claudes ställe, utan modell. Fallen står vid ägarens acceptansprov (avsnitt 11 i tillägget):

- rätt webbplats (1): förkontrollen binder arbetskopian, rot och fjärrepo; ett främmande fjärrepo, en saknad arbetskopia
  och en länkad katalog stoppar starten; två webbplatser har var sin session, terminal och privata katalog;
- verklig terminal (2) och återanslutning (4): en PTY med provagenten, svenska tecken, storlek, Ctrl-C som signal,
  en andra start ansluter till samma process, en annan vy skriver inte förrän den tar över, stopp är processkontroll och
  återupptagningen bär samma sessions-id;
- skrivägarskapet och samtidighet (6): krokarna tar kundens lås vid meddelandet och släpper det vid turens slut, ett
  annat arbete med låset stoppar meddelandet, ett verktyg utan låset nekas, och filer som ändrats utanför agenten sägs
  vid nästa meddelande;
- behörigheter (10): startvägen är restricted-läge med motorns inställningar (sandlådan, nekade git- och
  publiceringskommandon, läsning av motorn och ägarens konfiguration nekad), krokens sökvägskontroll, fel token och fel
  webbplats nekas, strömmen kräver en biljett, och bilagor prövas;
- provvägen (3): arbetskopian byggs och fotograferas på riktigt med bedömbarhet och läckagekontroll.

    .venv/bin/python -B kontroller/rokprov/revision/prov_andringar.py
"""
import base64
import contextlib
import http.client
import json
import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as dash  # noqa: E402
import andringar  # noqa: E402
import andringsflik  # noqa: E402
import andringar_fixtur  # noqa: E402
import atelje  # noqa: E402
import exportera  # noqa: E402
import flodesstart  # noqa: E402
import korregister  # noqa: E402
import partner  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FEJK = ROOT / 'kontroller' / 'rokprov' / 'andringar' / 'fejkclaude.py'
SLUG, SLUG2 = andringar_fixtur.WEBBPLATSER[0][0], andringar_fixtur.WEBBPLATSER[1][0]
KLIENT, KLIENT2 = 'klient-ett-0001', 'klient-tva-0002'


class AndringarBas(unittest.TestCase):
    """Provprojektet i en isolerad rot med provagenten i claudes ställe; inga fall här."""
    med_sajt = False

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-andringar-', 'ändringsflikens prov'))).resolve()
        for m in (atelje, exportera):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.multiple(dash, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.dict(os.environ, {'NWP_ANDRINGAR_PROVAGENT': str(FEJK)}))
        self.repon = andringar_fixtur.bygg(self.root, med_sajt=self.med_sajt)
        self.addCleanup(self.stoppa_alla)

    def stoppa_alla(self):
        andringsflik.stang_alla()
        andringsflik.SESSIONER.clear()

    def las_tills(self, slug, text, ms=8000):
        """Utdata ur sessionen tills texten syns (eller tiden går ut): hela texten hittills."""
        off, ut, slut = 0, b'', time.monotonic() + ms / 1000
        while time.monotonic() < slut:
            r = andringsflik.las_fran(slug, off, 0.3)
            if r is None:
                break
            _sid, f, d, s = r
            ut += d
            off = f + len(d)
            if text.encode('utf-8') in ut or s:
                break
        return ut.decode('utf-8', 'replace')

    def startinfo(self, slug):
        """Provagentens första rad (argument, arbetskatalog, terminal), läst tills raden därefter har kommit."""
        text = self.las_tills(slug, 'redo.')
        return json.loads(text.rsplit('fejkclaude:', 1)[1].split('\r\n', 1)[0].strip())

    def server(self):
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_port
        host = '127.0.0.1:%d' % port
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        self.stack.enter_context(patch.dict(dash.NYCKEL, {'varde': 'provnyckel'}))
        self.stack.enter_context(patch.dict(dash.STROMMAR, {'livslangd': 3, 'intervall': 0.2}))

        def anropa(metod, vag, data=None, huvud=None):
            c = http.client.HTTPConnection('127.0.0.1', port, timeout=20)
            try:
                c.request(metod, vag, json.dumps(data) if data is not None else None, huvud or {})
                r = c.getresponse()
                return r.status, r, r.read()
            finally:
                c.close()
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel', 'Content-Type': 'application/json'}
        return port, host, anropa, skriv

class Andringar(AndringarBas):
    # --- rätt webbplats ---

    def test_01_forkontrollen_binder_ratt_arbetskopia(self):
        k = andringar.forkontroll(SLUG)
        self.assertEqual(k['hinder'], [], k)
        self.assertTrue(any(f.startswith('arbetsgren: main') for f in k['fakta']), k['fakta'])
        self.assertTrue(any('fiktiv verksamhet' in f for f in k['fakta']), k['fakta'])
        self.assertEqual(k['webbplats']['arbetskopia'], str(self.repon[SLUG]))
        # ett främmande fjärrepo, en saknad arbetskopia och ett saknat kvitto stoppar; repot gissas aldrig ur namnet
        subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/Nortropic/kund-annan-kund.git'], cwd=self.repon[SLUG], check=True)
        self.assertTrue(any('fjärrepo' in h for h in andringar.forkontroll(SLUG)['hinder']))
        subprocess.run(['git', 'remote', 'set-url', 'origin', 'git@github.com:Nortropic/kund-%s.git' % SLUG], cwd=self.repon[SLUG], check=True)
        self.assertEqual(andringar.forkontroll(SLUG)['hinder'], [], 'samma repo i ssh-form')
        (self.root / 'kunder' / SLUG2 / 'KUNDREPO.json').unlink()
        self.assertTrue(any('kvitto' in h for h in andringar.forkontroll(SLUG2)['hinder']))
        self.assertTrue(any('ingen arbetskopia' in h for h in andringar.forkontroll('testdata-finns-inte')['hinder']))
        with self.assertRaises(ValueError):
            andringar.forkontroll('../annan')
        with self.assertRaises(ValueError):
            andringar.kommando(SLUG2, andringar.nytt_session_id(), True, 4771)

    def test_02_startvagen_ar_restricted_med_motorns_installningar(self):
        sid = andringar.nytt_session_id()
        with patch.dict(os.environ, {'NWP_ANDRINGAR_PROVAGENT': ''}):
            argv = andringar.kommando(SLUG, sid, True, 4771)
        self.assertEqual(argv[1:5], ['--restricted', '--strict-mcp-config', '--tools', andringar.VERKTYG])
        self.assertIn('Bash', argv[4].split(','))
        self.assertEqual(argv[-2:], ['--session-id', sid])
        self.assertEqual(argv[argv.index('--add-dir') + 1], str(andringar.privat(SLUG)))
        s = json.loads(argv[argv.index('--settings') + 1])
        self.assertIs(s['disableRemoteControl'], True, 'terminalen i appen är sessionens enda ingång')
        sb = s['sandbox']
        self.assertEqual((sb['enabled'], sb['failIfUnavailable'], sb['allowUnsandboxedCommands']), (True, True, False))
        self.assertIn(str(self.root), sb['filesystem']['denyRead'], 'motorns rot (och andra kunder) går inte att läsa för kommandona')
        self.assertIn(str(Path.home() / '.claude'), sb['filesystem']['denyRead'])
        self.assertEqual(sb['filesystem']['allowRead'], [str(self.repon[SLUG]), str(andringar.privat(SLUG))])
        self.assertEqual(sb['network'], {'allowedDomains': [], 'deniedDomains': ['*']}, 'inget nät för agentens kommandon')
        for regel in ('Bash(git push*)', 'Bash(git reset*)', 'Bash(git stash*)', 'Bash(wrangler*)', 'Bash(gh *)', 'Edit(./.claude/**)', 'Edit(./.git/**)'):
            self.assertIn(regel, s['permissions']['deny'])
        # de betrodda kommandona (provvägen och commitvägen) körs utanför sandlådan utan fråga; .git och motorns poster i den
        # privata katalogen går inte att skriva för agentens kommandon
        self.assertEqual(sb['excludedCommands'], andringar.betrodda(SLUG))
        self.assertEqual(s['permissions']['allow'], ['Bash(%s)' % k for k in andringar.betrodda(SLUG)])
        self.assertTrue(any(' committa %s *' % SLUG in k for k in andringar.betrodda(SLUG)))
        for n in andringar.MOTORNS:
            self.assertIn(str(andringar.privat(SLUG) / n), sb['filesystem']['denyWrite'])
        self.assertIn(str(self.repon[SLUG] / '.git' / 'hooks'), sb['filesystem']['denyWrite'])
        self.assertEqual(set(s['hooks']), {'SessionStart', 'UserPromptSubmit', 'PreToolUse', 'Stop', 'StopFailure', 'SessionEnd'})
        self.assertIn('andringar.py krok prova', s['hooks']['PreToolUse'][0]['hooks'][0]['command'])
        # en tur som slutar på ett API-fel släpper låset som en vanlig tur (granskningen 2026-10-11)
        self.assertEqual(s['hooks']['StopFailure'][0]['hooks'][0]['command'], s['hooks']['Stop'][0]['hooks'][0]['command'])
        # startinstruktionen: rollen ordagrant, metodens version, första introduktionen och sedan återupptagningen
        text = argv[argv.index('--append-system-prompt') + 1]
        self.assertIn('Du är ansvarig webbutvecklare och teknisk förvaltare för den här webbplatsen och dess repo.', text)
        self.assertIn('Ändra aldrig skydden för att godkänna ditt eget arbete.', text)
        self.assertIn('version %s' % andringar.metodtext()[1], text)
        self.assertIn('KUNSKAP.md finns inte än', text)
        self.assertIn('kontrollera %s' % SLUG, text)
        self.assertIn('committa %s -m' % SLUG, text)
        (andringar.privat(SLUG) / 'KUNSKAP.md').write_text('# Kunskap\n', encoding='utf-8')
        self.assertIn('Läs KUNSKAP.md', andringar.startinstruktion(SLUG))
        # verksamhetens underlag kopieras färskt vid varje start: en ändring syns för nästa session
        v = json.loads((self.root / 'underlag' / SLUG / 'VERKSAMHET.json').read_text(encoding='utf-8'))
        v['oppettider'] = 'vardagar 07–16'
        (self.root / 'underlag' / SLUG / 'VERKSAMHET.json').write_text(json.dumps(v, ensure_ascii=False), encoding='utf-8')
        andringar.forbered_privat(SLUG)
        self.assertIn('07–16', (andringar.privat(SLUG) / 'underlag' / 'VERKSAMHET.json').read_text(encoding='utf-8'))
        # motorns regler för text och bygge som versionerade kopior (agentens sandlåda kan inte läsa motorns kunskap/)
        m = andringar.privat(SLUG) / 'underlag' / 'motorn'
        v = json.loads((m / 'VERSIONER.json').read_text(encoding='utf-8'))
        for f in andringar.MOTORNS_REGLER:
            self.assertEqual((m / Path(f).name).read_text(encoding='utf-8'), (ROOT / f).read_text(encoding='utf-8'))
            self.assertEqual(v[Path(f).name]['kalla'], f)
        self.assertIn('underlag/motorn/', andringar.startinstruktion(SLUG))
        self.assertFalse((andringar.privat(SLUG2) / 'underlag' / 'VERKSAMHET.json').exists() and '07–16' in (andringar.privat(SLUG2) / 'underlag' / 'VERKSAMHET.json').read_text(encoding='utf-8'),
                         'den andra webbplatsen lär sig inte den första kundens uppgift')
        # miljön: inga NWP_-variabler från dashboarden utom krokarnas egna, inget automatiskt minne, ingen API-nyckel
        with patch.dict(os.environ, {'NWP_SLUG': 'fel', 'ANTHROPIC_API_KEY': 'sk-x', 'CLAUDECODE': '1'}):
            env = andringar.miljo(SLUG, 'token', 4771)
        self.assertNotIn('NWP_SLUG', env)
        self.assertNotIn('ANTHROPIC_API_KEY', env)
        self.assertEqual(env['CLAUDE_CODE_DISABLE_AUTO_MEMORY'], '1')
        self.assertEqual((env['NWP_ANDRINGAR_SLUG'], env['NWP_ANDRINGAR_REPO']), (SLUG, str(self.repon[SLUG])))

    def test_03_krokens_sokvagskontroll(self):
        env = {'NWP_ANDRINGAR_SLUG': SLUG, 'NWP_ANDRINGAR_REPO': str(self.repon[SLUG]), 'NWP_ANDRINGAR_PRIVAT': str(andringar.privat(SLUG)),
               'NWP_ANDRINGAR_PORT': '1', 'NWP_ANDRINGAR_TOKEN': 'x'}
        with patch.dict(os.environ, env):
            for p in ('/etc/passwd', str(self.root / 'kunder' / SLUG2 / 'kundrepo' / 'src' / 'x.astro'), str(ROOT / 'kontroller' / 'atelje.py'),
                      str(self.repon[SLUG] / '.git' / 'config'), str(self.repon[SLUG] / '.claude' / 'settings.json'),
                      str(self.repon[SLUG] / 'src' / '..' / '..' / '..' / SLUG2 / 'kundrepo' / 'CLAUDE.md'),
                      # motorns poster i den privata katalogen: kvittot litar på kontrollernas logg
                      str(andringar.privat(SLUG) / 'KONTROLLER.jsonl'), str(andringar.privat(SLUG) / 'kontroller' / 'x' / 'KONTROLL.json'),
                      str(andringar.privat(SLUG) / 'SESSION.json'), str(andringar.privat(SLUG) / 'bilagor' / 'bild.png'),
                      # APFS skiljer normalt inte på versaler: .GIT är .git (granskningen 2026-10-11)
                      str(self.repon[SLUG] / '.GIT' / 'config'), str(self.repon[SLUG] / 'src' / '.Git' / 'x'),
                      str(self.repon[SLUG] / '.CLAUDE' / 'settings.json'), str(andringar.privat(SLUG) / 'kontroller.JSONL')):
                rc, _ut, fel = andringar.krok('prova', json.dumps({'tool_name': 'Write', 'tool_input': {'file_path': p}}))
                self.assertEqual(rc, 2, p)
                self.assertIn('nekas', fel)
            rc, _ut, fel = andringar.krok('prova', json.dumps({'tool_name': 'Write', 'tool_input': {'file_path': str(andringar.privat(SLUG) / 'KONTROLLER.jsonl')}}))
            self.assertIn('bara KUNSKAP.md och ANDRINGAR.md', fel)
            for namn in andringar.AGENTENS:  # agentens två filer går vidare till dashboardens låskontroll
                fel = andringar.krok('prova', json.dumps({'tool_name': 'Write', 'tool_input': {'file_path': str(andringar.privat(SLUG) / namn)}}))[2]
                self.assertIn('dashboarden svarar inte', fel, namn)
            # inom arbetskopian når kroken dashboarden; utan svar stänger den (meddelandet och verktyget stoppas)
            rc, _ut, fel = andringar.krok('prova', json.dumps({'tool_name': 'Edit', 'tool_input': {'file_path': str(self.repon[SLUG] / 'src' / 'pages' / 'index.astro')}}))
            self.assertEqual(rc, 2)
            self.assertIn('dashboarden svarar inte', fel)
            self.assertEqual(andringar.krok('ta', '{}')[0], 2)
            self.assertEqual(andringar.krok('slapp', '{}')[0], 0, 'turens slut stoppar aldrig agenten')

    # --- terminalen, återanslutningen och stoppet ---

    def test_04_pty_sessionen_med_provagenten(self):
        l = andringsflik.starta(SLUG, 4771, KLIENT, cols=100, rows=30)
        s = l['session']
        self.assertTrue(s['lever'])
        info = self.startinfo(SLUG)
        self.assertEqual(info['cwd'], str(self.repon[SLUG].resolve()))
        self.assertTrue(info['tty'] and info['styrande'] and info['token'])
        self.assertIn('--restricted', info['argv'])
        self.assertEqual(info['argv'][-2:], ['--session-id', s['sid']])
        # dubbelöppning: en andra start (en annan vy, en återöppnad app) ansluter till samma process
        l2 = andringsflik.starta(SLUG, 4771, KLIENT2)
        self.assertEqual((l2['session']['sid'], l2['session']['pid']), (s['sid'], s['pid']))
        self.assertEqual(l2['session']['agare'], KLIENT, 'ägarskapet står kvar hos den första vyn')
        with self.assertRaises(andringsflik.Upptagen):
            andringsflik.skriv(SLUG, s['sid'], KLIENT2, 'hej\r')
        with self.assertRaises(andringsflik.Inaktuell):
            andringsflik.skriv(SLUG, '00000000-0000-4000-8000-000000000000', KLIENT, 'hej\r')
        andringsflik.skriv(SLUG, s['sid'], KLIENT, 'byt till 07–16 på vardagar, åäö ÅÄÖ\r')
        self.assertIn('fick: byt till 07–16 på vardagar, åäö ÅÄÖ', self.las_tills(SLUG, 'fick: byt'))
        andringsflik.ta_over(SLUG, s['sid'], KLIENT2)
        andringsflik.storlek(SLUG, s['sid'], KLIENT2, 88, 22)
        self.assertIn('storlek: 88x22', self.las_tills(SLUG, 'storlek: 88x22'))
        andringsflik.skriv(SLUG, s['sid'], KLIENT2, '\x03')
        self.assertIn('avbrott mottaget', self.las_tills(SLUG, 'avbrott mottaget'), 'Ctrl-C når agenten som en signal genom terminalen')
        # en andra webbplats har en egen process och påverkas inte av den första
        l3 = andringsflik.starta(SLUG2, 4771, KLIENT)
        self.assertNotEqual(l3['session']['pid'], s['pid'])
        self.assertTrue(andringsflik.lage(SLUG2)['session']['lever'])
        # stoppet är processkontroll; efteråt finns ingen terminal att skriva i, och samma samtal kan återupptas
        self.assertTrue(andringsflik.stoppa(SLUG, s['sid'], KLIENT2)['ok'])
        slut = time.monotonic() + 10
        while andringsflik.lage(SLUG)['session']['lever'] and time.monotonic() < slut:
            time.sleep(0.1)
        l4 = andringsflik.lage(SLUG)
        self.assertFalse(l4['session']['lever'])
        self.assertTrue(l4['session']['stoppad'])
        self.assertTrue(andringsflik.lage(SLUG2)['session']['lever'], 'den andra webbplatsens agent arbetar vidare')
        with self.assertRaises(andringsflik.Inaktuell):
            andringsflik.skriv(SLUG, s['sid'], KLIENT2, 'ls\r')
        self.assertEqual(atelje.las_json(andringsflik.sessionsfil(SLUG))['lage'], 'avslutad')
        l5 = andringsflik.starta(SLUG, 4771, KLIENT, ateruppta=True)
        info = self.startinfo(SLUG)
        self.assertEqual(info['argv'][-2:], ['--resume', s['sid']], 'återupptagningen bär samma sessions-id')
        self.assertEqual(l5['session']['sid'], s['sid'])
        # en annan process med samma sessions-id (en terminal utanför appen): ingen andra skrivare
        andringsflik.stang_alla()
        with patch.object(partner, 'andra_processer', return_value=[{'pid': 4242, 'kommando': 'claude (interaktiv)'}]):
            with self.assertRaises(andringsflik.Upptagen):
                andringsflik.starta(SLUG, 4771, KLIENT, ateruppta=True)
        logg = [json.loads(x) for x in (andringar.privat(SLUG) / 'LOGG.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual([x['handelse'] for x in logg if x['handelse'] in ('start', 'stopp', 'slut')][:3], ['start', 'stopp', 'slut'])

    # --- skrivägarskapet genom krokarna ---

    def test_05_skrivlaset_via_krokarna_och_http(self):
        port, host, anropa, skriv = self.server()
        l = andringsflik.starta(SLUG, port, KLIENT)
        token = andringsflik.SESSIONER[SLUG]['token']
        env = dict(os.environ, NWP_ANDRINGAR_SLUG=SLUG, NWP_ANDRINGAR_TOKEN=token, NWP_ANDRINGAR_PORT=str(port),
                   NWP_ANDRINGAR_REPO=str(self.repon[SLUG]), NWP_ANDRINGAR_PRIVAT=str(andringar.privat(SLUG)))

        def krok(h, data):  # kroken som Claude Code kör den: skriptet, JSON på stdin, slutkoden och utdata
            r = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'kontroller' / 'andringar.py'), 'krok', h], input=json.dumps(data),
                               capture_output=True, text=True, env=env, timeout=60)
            return r.returncode, r.stdout, r.stderr
        rc, ut, _fel = krok('start', {'session_id': l['session']['sid'], 'source': 'startup'})
        self.assertEqual(rc, 0)
        self.assertIn('arbetsgren: main', ut)
        rc, ut, _fel = krok('ta', {'session_id': l['session']['sid']})
        self.assertEqual(rc, 0, ut)
        self.assertIn('Skrivlåset för webbplatsen är ditt', ut)
        with self.assertRaises(ValueError):  # en export, förhandsvisning eller release väntar nu på agentens tur
            with flodesstart.las(atelje.ROOT, SLUG):
                pass
        fil = self.repon[SLUG] / 'src' / 'pages' / 'index.astro'
        self.assertEqual(krok('prova', {'tool_name': 'Edit', 'tool_input': {'file_path': str(fil)}})[0], 0)
        self.assertEqual(krok('slapp', {'session_id': l['session']['sid']})[0], 0)
        with flodesstart.las(atelje.ROOT, SLUG):  # turen är slut: låset är fritt mellan turerna
            rc, _ut, fel = krok('prova', {'tool_name': 'Edit', 'tool_input': {'file_path': str(fil)}})
            self.assertEqual(rc, 2)
            self.assertIn('skrivlåset', fel)
            with patch.object(andringsflik, 'TA_VANTA', 1):  # väntan på kundens lås, kort i provet
                rc, _ut, fel = krok('ta', {'session_id': l['session']['sid']})
            self.assertEqual(rc, 2, 'ett annat arbete håller kundens lås hela väntan: meddelandet stoppas')
            self.assertIn('håller kundens lås', fel)
        # ett lås som släpps medan meddelandet väntar (kvitteringen efter förra turen): meddelandet tar det då, och väntan
        # håller inte flikens lås, så att andra krokar svarar under tiden (granskningen 2026-10-11)
        slapp, svar = threading.Event(), {}

        def hall():
            with flodesstart.las(atelje.ROOT, SLUG):
                slapp.wait(15)
        t = threading.Thread(target=hall)
        t.start()
        time.sleep(0.3)
        tt = threading.Thread(target=lambda: svar.update(r=krok('ta', {'session_id': l['session']['sid']})))
        tt.start()
        time.sleep(1.2)
        start = time.monotonic()
        status, _r, _k = anropa('POST', '/api/andringar/%s/krok' % SLUG2, {'handling': 'ta', 'data': {}}, {'Origin': 'http://' + host, 'X-Andringar-Token': token})
        self.assertEqual(status, 403)
        self.assertLess(time.monotonic() - start, 1.0, 'en annan krok väntar inte medan meddelandet väntar på kundens lås')
        self.assertNotIn('r', svar, 'meddelandet väntar fortfarande på kundens lås')
        slapp.set()
        t.join(15)
        tt.join(40)
        self.assertEqual(svar['r'][0], 0, svar['r'])
        self.assertIn('Skrivlåset för webbplatsen är ditt', svar['r'][1])
        krok('slapp', {'session_id': l['session']['sid']})
        # en manuell redigerare ändrar källan mellan turerna: nästa meddelande säger det
        fil.write_text(fil.read_text(encoding='utf-8').replace('Vardagar 07–17', 'Vardagar 06–17'), encoding='utf-8')
        rc, ut, _fel = krok('ta', {'session_id': l['session']['sid']})
        self.assertEqual(rc, 0)
        self.assertIn('src/pages/index.astro', ut)
        krok('slapp', {'session_id': l['session']['sid']})
        # fel token, fel webbplats och en kropp utan token nekas
        status, _r, kropp = anropa('POST', '/api/andringar/%s/krok' % SLUG, {'handling': 'ta', 'data': {}}, {'Origin': 'http://' + host, 'X-Andringar-Token': 'fel'})
        self.assertEqual(status, 403, kropp)
        status, _r, _k = anropa('POST', '/api/andringar/%s/krok' % SLUG2, {'handling': 'ta', 'data': {}}, {'Origin': 'http://' + host, 'X-Andringar-Token': token})
        self.assertEqual(status, 403, 'token gäller bara sin egen webbplats')
        # processens slut släpper ett lås som fortfarande hålls (ett avbrutet svar)
        krok('ta', {'session_id': l['session']['sid']})
        andringsflik.stoppa(SLUG, l['session']['sid'], KLIENT)
        slut = time.monotonic() + 10
        while SLUG in andringsflik.SKRIVLAS and time.monotonic() < slut:
            time.sleep(0.1)
        with flodesstart.las(atelje.ROOT, SLUG):
            pass

    def test_06_http_vagarna_och_strommen(self):
        port, host, anropa, skriv = self.server()
        bas = '/api/andringar/%s' % SLUG
        status, _r, kropp = anropa('GET', bas)
        self.assertEqual(status, 200, kropp)
        l = json.loads(kropp)
        self.assertEqual((l['slug'], l['repo'], l['session']['lever']), (SLUG, 'kund-%s' % SLUG, False))
        self.assertEqual(anropa('GET', '/api/andringar/finns-inte')[0], 404)
        self.assertEqual(anropa('POST', bas + '/terminal', {'handling': 'starta', 'klient': KLIENT}, {'Origin': 'http://' + host})[0], 403, 'utan nyckel')
        status, _r, kropp = anropa('POST', bas + '/terminal', {'handling': 'starta', 'klient': KLIENT}, skriv)
        self.assertEqual(status, 200, kropp)
        sid = json.loads(kropp)['session']['sid']
        self.assertEqual(anropa('GET', bas + '/terminal?fran=0')[0], 403, 'strömmen kräver en biljett')
        b = json.loads(anropa('POST', bas + '/terminal', {'handling': 'biljett'}, skriv)[2])['biljett']
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=20)
        c.request('GET', bas + '/terminal?biljett=%s&fran=0' % b)
        r = c.getresponse()
        self.assertEqual(r.status, 200)
        data, utdata, slut = b'', b'', time.monotonic() + 10
        while b'redo.' not in utdata and time.monotonic() < slut:
            data += r.read1(4096)
            utdata = b''
            for h in data.split(b'\n\n')[:-1]:  # bara hela händelser
                rader = dict(x.split(b': ', 1) for x in h.split(b'\n') if b': ' in x)
                if rader.get(b'event') == b'ut':
                    utdata += base64.b64decode(json.loads(rader[b'data'])['d'])
        c.close()
        self.assertIn(b'fejkclaude', utdata, 'strömmen bär terminalens bytes')
        status, _r, kropp = anropa('POST', bas + '/terminal', {'handling': 'in', 'sid': sid, 'klient': KLIENT2, 'data': 'x'}, skriv)
        self.assertEqual((status, json.loads(kropp)['slag']), (409, 'Upptagen'))
        status, _r, kropp = anropa('POST', bas + '/terminal', {'handling': 'in', 'sid': sid, 'klient': KLIENT, 'data': 'hej från http\r'}, skriv)
        self.assertEqual(status, 200, kropp)
        self.assertIn('fick: hej från http', self.las_tills(SLUG, 'fick: hej från http'))
        # bilagor: en bild och text tas emot privat; en SVG med skript och okända binärer nekas
        png = base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\0' * 32).decode()
        status, _r, kropp = anropa('POST', bas + '/bilaga', {'namn': 'ny huvudbild.png', 'data': png}, skriv)
        self.assertEqual(status, 200, kropp)
        p = Path(json.loads(kropp)['sokvag'])
        self.assertEqual(p.parent, andringar.privat(SLUG) / 'bilagor')
        self.assertTrue(p.is_file() and not str(p).startswith(str(self.repon[SLUG])), 'bilagan ligger privat, inte i repot')
        svg = base64.b64encode(b'<svg><script>alert(1)</script></svg>').decode()
        self.assertEqual(anropa('POST', bas + '/bilaga', {'namn': 'x.svg', 'data': svg}, skriv)[0], 400)
        self.assertEqual(anropa('POST', bas + '/bilaga', {'namn': 'x.bin', 'data': base64.b64encode(b'\xff\xfe\x00\x01').decode()}, skriv)[0], 400)
        status, _r, kropp = anropa('GET', bas + '/diff')
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(kropp)['finns'])
        self.assertEqual(anropa('POST', bas + '/terminal', {'handling': 'stoppa', 'sid': sid, 'klient': KLIENT}, skriv)[0], 200)

    # --- commitvägen ---

    def test_11_commitvagen(self):
        """Agentens kommandon kan inte skriva i .git; motorn committar de namngivna filerna och bara dem, utan repots
        krokar och fsmonitor, och vägrar sökvägar utanför arbetskopian, i .git och ett meddelande utan "Ändring: "."""
        r = self.repon[SLUG]
        spar = self.root / 'kod-korde'
        krokar = r / '.git' / 'hooks'
        krokar.mkdir(exist_ok=True)
        for namn in ('pre-commit', 'post-commit'):
            (krokar / namn).write_text('#!/bin/sh\necho %s >> %s\n' % (namn, spar), encoding='utf-8')
            os.chmod(krokar / namn, 0o755)
        sida = r / 'src' / 'pages' / 'index.astro'
        sida.write_text(sida.read_text(encoding='utf-8').replace('07–17', '07–16'), encoding='utf-8')
        (r / 'src' / 'pages' / 'altaner.astro').write_text('<h1>Altaner</h1>\n', encoding='utf-8')
        (r / 'CLAUDE.md').write_text((r / 'CLAUDE.md').read_text(encoding='utf-8') + 'Främmande rad.\n', encoding='utf-8')
        fore = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=r, capture_output=True, text=True).stdout.strip()
        svar = andringar.committa(SLUG, ['src/pages/index.astro', str(r / 'src' / 'pages' / 'altaner.astro')], 'Ändring: öppettider och altaner')
        self.assertEqual(svar['filer'], ['src/pages/index.astro', 'src/pages/altaner.astro'])
        # provets egna git-anrop med fsmonitor av (status kör den annars), så att spåret bara kan komma från motorn
        logg = lambda *a: subprocess.run(['git', '-c', 'core.fsmonitor=false', *a], cwd=r, capture_output=True, text=True).stdout  # noqa: E731
        self.assertEqual(logg('log', '-1', '--format=%s%n%P').split(), ['Ändring:', 'öppettider', 'och', 'altaner', fore])
        self.assertEqual(sorted(logg('show', '--name-only', '--format=', 'HEAD').split()), ['src/pages/altaner.astro', 'src/pages/index.astro'])
        self.assertEqual(logg('status', '--short').split(), ['M', 'CLAUDE.md'], 'den främmande ändringen står kvar utanför commiten')
        self.assertFalse(spar.exists(), 'repots krokar körs aldrig av motorns commit: %s' % (spar.read_text() if spar.exists() else ''))
        # fsmonitor (konfigurationen kör den vid add och status) prövas för sig, så att ett fel i den ena inte döljer den andra
        fs = self.root / 'fsmonitor.sh'
        fs.write_text('#!/bin/sh\necho fsmonitor >> %s\nexit 1\n' % spar, encoding='utf-8')
        os.chmod(fs, 0o755)
        subprocess.run(['git', 'config', 'core.fsmonitor', str(fs)], cwd=r, check=True)
        # en borttagen fil prövas genom sin katalog och committas som borttagning
        (r / 'src' / 'pages' / 'altaner.astro').unlink()
        andringar.committa(SLUG, ['src/pages/altaner.astro'], 'Ändring: altanerna tas bort')
        self.assertFalse(spar.exists(), 'fsmonitor körs aldrig av motorns commit: %s' % (spar.read_text() if spar.exists() else ''))
        self.assertEqual(logg('show', '--name-status', '--format=', 'HEAD').split(), ['D', 'src/pages/altaner.astro'])
        for filer, medd in ((['src/pages/index.astro'], 'öppettider'), (['../%s/kundrepo/CLAUDE.md' % SLUG2], 'Ändring: x'),
                            (['/etc/passwd'], 'Ändring: x'), (['.git/config'], 'Ändring: x'), (['src/.git/x'], 'Ändring: x'),
                            (['.claude/settings.json'], 'Ändring: x'), ([], 'Ändring: x'), (['.'], 'Ändring: x'),
                            (['src/pages'], 'Ändring: x'), (['.GIT/config'], 'Ändring: x'), (['src/.Git/x'], 'Ändring: x')):
            with self.assertRaises(ValueError, msg=(filer, medd)):
                andringar.committa(SLUG, filer, medd)
        # ett mönster är en bokstavlig sökväg: det tar aldrig med en främmande ändring i commiten (granskningen 2026-10-11)
        (r / 'src' / 'pages' / 'om.astro').write_text('<h1>Om (främmande)</h1>\n', encoding='utf-8')
        huvud = logg('rev-parse', 'HEAD').strip()
        for monster in ('src/pages/*.astro', ':(glob)src/**', ':/src/pages/om.astro', 'src/pages/om.ast?o'):
            with self.assertRaises(ValueError, msg=monster):
                andringar.committa(SLUG, [monster], 'Ändring: x')
        self.assertEqual(logg('rev-parse', 'HEAD').strip(), huvud)
        (r / 'src' / 'pages' / 'om.astro').unlink()
        # kommandoraden, som agenten kör den (motorns rot ur miljön): inget att committa är ett besked, inte ett fel i motorn
        sida.write_text(sida.read_text(encoding='utf-8') + '<!-- x -->\n', encoding='utf-8')
        kor = lambda *a: subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'andringar.py'), 'committa', SLUG, *a],  # noqa: E731
                                        capture_output=True, text=True, env=dict(os.environ, NWP_ANDRINGAR_ROT=str(self.root)))
        k = kor('-m', 'Ändring: en kommentar', 'src/pages/index.astro')
        self.assertEqual(k.returncode, 0, k.stderr)
        self.assertIn('Committat', k.stdout)
        k = kor('-m', 'Ändring: inget', 'src/pages/index.astro')
        self.assertEqual(k.returncode, 2)
        self.assertIn('Ingen commit', k.stderr)
        self.assertFalse(spar.exists())



def fejkfoto(dist, sida, ut):
    """Fotograferingen utan webbläsare: en bedömbar sida i 390 och 1440 (provvägens resultat, inte dess bilder)."""
    ut.mkdir(parents=True, exist_ok=True)
    vy = {'status': 200, 'innehallstyp': 'text/html', 'h1': 1, 'konsol': [], 'sidfel': [], 'spill': {'spill': False},
          'bedombarhet': {'main': True, 'main_text_langd': 200, 'text_langd': 300, 'bilder_forsta_vyn': 0, 'brutna_bilder_forsta_vyn': [], 'typsnitt_fel': [], 'felsida': False}}
    return {'vyer': {'390': vy, '1440': vy}}, {}


class Leverans(AndringarBas):
    """Ändringen som kundens leverabel (fas 2): kvitteringen, förhandsvisningens krav, exportens skydd och intaget."""

    def git(self, *args, slug=SLUG):
        return subprocess.run(['git', '-c', 'user.name=Agenten', '-c', 'user.email=a@a', *args], cwd=self.repon[slug], capture_output=True, text=True, check=True).stdout.strip()

    def andra(self, gammal, ny, commit=True, kontroll=True):
        fil = self.repon[SLUG] / 'src' / 'pages' / 'index.astro'
        fil.write_text(fil.read_text(encoding='utf-8').replace(gammal, ny), encoding='utf-8')
        if kontroll:
            post = andringar.kontrollera(SLUG, bygg=lambda r: (0, 'byggt'), fotografera=fejkfoto)
            self.assertTrue(post['ok'], post['brister'])
        if commit:
            self.git('add', 'src/pages/index.astro')
            self.git('commit', '-qm', 'Ändring: %s' % ny)

    def test_08_kvitteringen_gor_andringen_till_leverabel(self):
        import kundrepo
        self.assertEqual(andringsflik.kan_kvitteras(SLUG), (False, 'samma som exporten'))
        self.assertIsNone(kundrepo.preview_krav(SLUG), 'exporten själv kan förhandsvisas')
        self.andra('Vardagar 07–17', 'Vardagar 07–16', commit=False)
        self.assertEqual(kundrepo.preview_krav(SLUG), 'exporten är inaktuell (källorna eller filerna har ändrats): exportera igen',
                         'en ändring i arbetskopian är ingen leverabel förrän den kvitterats')
        self.assertEqual(andringsflik.kan_kvitteras(SLUG)[1], 'arbetskopian har ändringar som inte är committade')
        self.git('add', 'src/pages/index.astro')
        self.git('commit', '-qm', 'Ändring: öppettiderna 07–16')
        self.assertEqual(andringsflik.kan_kvitteras(SLUG), (True, None))
        r = andringsflik.kvittera(SLUG)
        e = exportera.aktuell(SLUG)
        self.assertEqual((e['kalla'], e['commit'], e['aktuell'], e['id']), ('andring', self.git('rev-parse', 'HEAD'), True, r['export']))
        self.assertEqual([c['text'] for c in e['commits']], ['Ändring: öppettiderna 07–16'])
        self.assertIsNone(kundrepo.preview_krav(SLUG), 'den kvitterade ändringen förhandsvisas som en export')
        self.assertEqual(andringsflik.kan_kvitteras(SLUG), (False, 'kvitterad'))
        # en commit som provvägen inte godkänt (ändrad efter kontrollen) kvitteras inte, och kvittot blir inaktuellt
        self.andra('07–16', '07–15', kontroll=False)
        self.assertEqual(andringsflik.kan_kvitteras(SLUG), (False, 'provvägen har inte godkänt exakt den här versionen'))
        self.assertFalse(exportera.aktuell(SLUG)['aktuell'], 'kvittot gäller sin commit, inte en senare')
        with self.assertRaises(ValueError):
            exportera.fran_andring(SLUG)

    def test_12_bara_den_manuella_kvitteringen_pushar(self):
        # granskningen 2026-10-11: kvitteringen efter turen gör ändringen leverabel men pushar aldrig; Johnnys kvittering
        # pushar den kvitterade commiten till det bundna fjärrepot
        import kundrepo
        f = self.root / 'kunder' / SLUG / 'KUNDREPO.json'
        f.write_text(json.dumps(dict(json.loads(f.read_text(encoding='utf-8')), fjarr={'status': 'skapat'})), encoding='utf-8')
        puttar = []

        def pusha(r, kandidat):
            puttar.append(kandidat)
            return {'ok': True, 'commit': kandidat}
        with patch.object(kundrepo, 'pusha_granskad', side_effect=pusha):
            self.andra('Vardagar 07–17', 'Vardagar 07–16')
            andringsflik._kvittera_tyst(SLUG)
            self.assertEqual(puttar, [], 'den automatiska kvitteringen pushar aldrig')
            self.assertEqual((exportera.aktuell(SLUG)['kalla'], exportera.aktuell(SLUG)['commit']), ('andring', self.git('rev-parse', 'HEAD')))
            self.andra('07–16', '07–15')
            svar = andringsflik.kvittera(SLUG)
        self.assertEqual(puttar, [self.git('rev-parse', 'HEAD')])
        self.assertEqual(svar['push'], {'ok': True, 'fel': None})

    def test_11_kvittot_fryser_inte_en_lank_ut(self):
        """En commit med en länk till en absolut sökväg (fångat i en riktig körning 2026-10-11: provprojektets node_modules)
        kvitteras inte: ett tydligt besked i stället för ett tarfile-fel i kvitteringens tråd, ingen tom kvittokatalog, och
        skälet står i flikens läge tills något kvitterats."""
        # node_modules hoppas över av exportens manifest men följer med i git archive: kvittot fryser commiten
        os.symlink(str(self.root), self.repon[SLUG] / 'node_modules')
        self.git('add', '-f', 'node_modules')
        self.git('commit', '-qm', 'Ändring: en länk')
        self.assertTrue(andringar.kontrollera(SLUG, bygg=lambda r: (0, 'byggt'), fotografera=fejkfoto)['ok'])
        self.assertEqual(andringsflik.kan_kvitteras(SLUG), (True, None))
        kvitton = lambda: sorted(p.name for p in (self.root / 'kunder' / SLUG / 'exporter').iterdir() if p.is_dir())  # noqa: E731
        fore = kvitton()
        with self.assertRaisesRegex(ValueError, 'går inte att frysa säkert'):
            exportera.fran_andring(SLUG)
        self.assertEqual(kvitton(), fore, 'ingen tom kvittokatalog')
        andringsflik._kvittera_tyst(SLUG)  # den automatiska kvitteringen efter turen: skälet i loggen och läget
        self.assertIn('går inte att frysa säkert', andringsflik.kvittoforsok(SLUG)['skal'])
        self.assertIn('går inte att frysa säkert', andringsflik.lage(SLUG)['kvittering']['forsok']['skal'])

    def test_09_exporten_skriver_inte_over_och_intaget(self):
        import shutil
        sajt = self.root / 'kunder' / SLUG / 'sajt'
        self.andra('Vardagar 07–17', 'Vardagar 07–16')
        (self.repon[SLUG] / 'CLAUDE.md').write_text('# ändrad av agenten\n', encoding='utf-8')
        self.git('add', 'CLAUDE.md')
        self.git('commit', '-qm', 'Ändring: instruktionen')
        stage = self.root / 'stage'

        def ny_stage():  # det en export från sajten skulle lämna över (src och DESIGN.md ur sajten, CLAUDE.md ur mallen)
            shutil.rmtree(stage, ignore_errors=True)
            shutil.copytree(sajt / 'src', stage / 'src')
            shutil.copyfile(sajt / 'DESIGN.md', stage / 'DESIGN.md')
            (stage / 'CLAUDE.md').write_text((self.root / 'kunder' / SLUG / 'kundrepo' / 'CLAUDE.md').read_text(encoding='utf-8')
                                             if False else '# kund-%s\n\nProvprojektets instruktioner: `npm run build` bygger dist/. DESIGN.md beskriver designen.\n' % SLUG, encoding='utf-8')
            return stage
        # sajtens fil stoppar exporten; CLAUDE.md genereras av exporten och skrivs över med en varning (granskningen 2026-10-11)
        self.assertEqual(exportera.andringar_som_skrivs_over(SLUG, ny_stage(), self.repon[SLUG]),
                         {'stoppar': ['src/pages/index.astro'], 'genereras': ['CLAUDE.md']}, 'en export från sajten skulle tappa ändringen')
        # ocommittat arbete stoppar alltid, också en ny fil
        (self.repon[SLUG] / 'src' / 'pages' / 'utkast.astro').write_text('<h1>Utkast</h1>\n', encoding='utf-8')
        self.assertIn('src/pages/utkast.astro (inte committad)', exportera.andringar_som_skrivs_over(SLUG, ny_stage(), self.repon[SLUG])['stoppar'])
        (self.repon[SLUG] / 'src' / 'pages' / 'utkast.astro').unlink()
        # intaget: källan som exporten kopierar tas in i sajten; det exporten genererar redovisas
        ut = andringsflik.ta_in(SLUG)
        self.assertEqual((ut['intaget'], ut['genereras'], ut['konflikter']), (['src/pages/index.astro'], ['CLAUDE.md'], []))
        self.assertIn('Vardagar 07–16', (sajt / 'src' / 'pages' / 'index.astro').read_text(encoding='utf-8'))
        self.assertEqual(exportera.andringar_som_skrivs_over(SLUG, ny_stage(), self.repon[SLUG]), {'stoppar': [], 'genereras': ['CLAUDE.md']},
                         'efter intaget bär sajten ändringen; bara den genererade filen återstår, och den stoppar inte')
        # en sajt som ändrats på samma ställe sedan exporten är en konflikt, aldrig en tyst överskrivning
        self.andra('Vardagar 07–16', 'Vardagar 08–16')
        (sajt / 'src' / 'pages' / 'index.astro').write_text('<!-- designarbete i sajten -->\n', encoding='utf-8')
        ut = andringsflik.ta_in(SLUG)
        self.assertEqual(ut['konflikter'], ['src/pages/index.astro'])
        self.assertEqual((sajt / 'src' / 'pages' / 'index.astro').read_text(encoding='utf-8'), '<!-- designarbete i sajten -->\n')

    def test_13_intaget_tar_in_exportens_funktionssidor(self):
        # granskningen 2026-10-11: en sida som exporten lade till och som sajten saknar (funktionssidorna) tas in när
        # agenten ändrat den, och ett andra intag före nästa export står som redan intaget, inte som en konflikt
        sajt = self.root / 'kunder' / SLUG / 'sajt'
        api = self.repon[SLUG] / 'src' / 'pages' / 'api' / 'forfragan.ts'
        api.parent.mkdir(parents=True)
        api.write_text('export const POST = () => new Response("v1");\n', encoding='utf-8')
        self.git('add', 'src/pages/api/forfragan.ts')
        self.git('commit', '-qm', 'Export: funktionssidan')  # som om exporten lagt till den
        f = self.root / 'kunder' / SLUG / 'KUNDREPO.json'
        kv = json.loads(f.read_text(encoding='utf-8'))
        kv['senaste_export']['commit'] = self.git('rev-parse', 'HEAD')
        f.write_text(json.dumps(kv), encoding='utf-8')
        api.write_text('export const POST = () => new Response("v2");\n', encoding='utf-8')
        self.git('add', 'src/pages/api/forfragan.ts')
        self.git('commit', '-qm', 'Ändring: funktionssidan')
        self.assertFalse((sajt / 'src' / 'pages' / 'api' / 'forfragan.ts').exists())
        ut = andringsflik.ta_in(SLUG)
        self.assertEqual((ut['intaget'], ut['konflikter']), (['src/pages/api/forfragan.ts'], []))
        self.assertIn('"v2"', (sajt / 'src' / 'pages' / 'api' / 'forfragan.ts').read_text(encoding='utf-8'))
        ut = andringsflik.ta_in(SLUG)
        self.assertEqual((ut['intaget'], ut.get('redan'), ut['konflikter']), ([], ['src/pages/api/forfragan.ts'], []))

    def test_10_orelaterat_arbete_foljer_inte_med(self):
        # en främmande, ocommittad ändring (en annan redigerare): agentens commit kvitteras inte förrän den är löst, och
        # inget städas bort
        (self.repon[SLUG] / 'src' / 'pages' / 'om.astro').write_text('<h1>Om oss (utkast)</h1>\n', encoding='utf-8')
        self.andra('Vardagar 07–17', 'Vardagar 07–16')
        self.assertEqual(andringsflik.kan_kvitteras(SLUG)[1], 'arbetskopian har ändringar som inte är committade')
        self.assertEqual(andringsflik.diff(SLUG)['nya_filer'], ['src/pages/om.astro'], 'en ny fil syns i diffen, inte bara ändrade')
        with self.assertRaises(ValueError):
            exportera.fran_andring(SLUG)
        self.assertTrue((self.repon[SLUG] / 'src' / 'pages' / 'om.astro').is_file(), 'den främmande ändringen står kvar')
        # sidopanelen visar varje commit sedan produktionen (eller exporten): en release tar med allt i listan
        self.git('add', 'src/pages/om.astro')
        self.git('commit', '-qm', 'Främmande: om oss-utkastet')
        d = andringsflik.diff(SLUG)
        self.assertEqual([x.split(' ', 2)[2] for x in d['commits_sedan_bas']], ['Främmande: om oss-utkastet', 'Ändring: Vardagar 07–16'])
        self.assertEqual(d['bas_slag'], 'exporten')


class Provvagen(unittest.TestCase):
    """Agentens provväg på riktigt: arbetskopian med rökprovets mallsajt byggs innanför processgränsen och fotograferas."""

    def setUp(self):
        if not (andringar_fixtur.MALLSAJT / 'node_modules').is_dir():
            raise unittest.SkipTest('mallsajten saknar node_modules (rokprov.sh bygger den tidigare)')
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-andringar-', 'ändringsflikens provväg'))).resolve()
        for m in (atelje, exportera):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.repon = andringar_fixtur.bygg(self.root, med_sajt=True)

    def test_07_kontrollen_bygger_och_fotograferar(self):
        post = andringar.kontrollera(SLUG)
        self.assertTrue(post['ok'], post['brister'])
        self.assertEqual(set(post['bilder']['/']), {'390', '1440'})
        self.assertTrue(all(Path(p).is_file() for p in post['bilder']['/'].values()))
        self.assertEqual(post['tillstand'], andringar.tradtillstand(self.repon[SLUG]))
        self.assertEqual(andringar.senaste_kontroll(SLUG)['tillstand'], post['tillstand'])
        # en ändring i arbetskopian ger ett nytt tillstånd, och en commit av det har samma träd
        r = self.repon[SLUG]
        sida = next((r / 'src' / 'pages').glob('index.astro'))
        sida.write_text(sida.read_text(encoding='utf-8') + '\n<!-- provändring -->\n', encoding='utf-8')
        nytt = andringar.tradtillstand(r)
        self.assertNotEqual(nytt, post['tillstand'])
        subprocess.run(['git', '-c', 'user.name=p', '-c', 'user.email=p@p', 'commit', '-qam', 'Ändring: prov'], cwd=r, check=True)
        self.assertEqual(subprocess.run(['git', 'rev-parse', 'HEAD^{tree}'], cwd=r, capture_output=True, text=True).stdout.strip(), nytt)
        # en läcka i arbetskopian (en lokal sökväg) underkänner kontrollen
        (r / 'src' / 'lacka.txt').write_text('se /Users/nagon/nortropic-webb-pro/underlag/x\n', encoding='utf-8')
        post2 = andringar.kontrollera(SLUG)
        self.assertFalse(post2['ok'])
        self.assertTrue(any('läckage' in b for b in post2['brister']), post2['brister'])
        # provvägen installerar och bygger aldrig genom en länkad node_modules: npm ci skulle radera det länken pekar på
        # (granskningen 2026-10-11)
        (r / 'src' / 'lacka.txt').unlink()
        flyttad = self.root / 'node_modules-utanfor'
        os.rename(r / 'node_modules', flyttad)
        os.symlink(flyttad, r / 'node_modules')
        post3 = andringar.kontrollera(SLUG)
        self.assertFalse(post3['ok'])
        self.assertTrue(any('node_modules är en länk' in b for b in post3['brister']), post3['brister'])
        self.assertTrue((flyttad / '.nwp-las.json').is_file() and (flyttad / 'astro').exists(), 'inget togs bort genom länken')


if __name__ == '__main__':
    unittest.main(verbosity=2)
