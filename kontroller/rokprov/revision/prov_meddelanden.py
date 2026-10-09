#!/usr/bin/env python3
"""prov_meddelanden.py — meddelandebussen och löparen (kontroller/meddelanden.py, kontroller/lopare.py; ägarens uppdrag
2026-10-09 om den kompletta arbetsplatsen, punkt 3–6), syntetiskt och utan modell. En falsk claude talar Claude Codes
strömmande protokoll så som det prövats mot 2.1.290 (init, ekot med meddelandets id, meddelanden mellan verktygsgränserna i
samma tur, avbrott med kvitto på de köade, resultatet med user_message_uuids):

- utan meddelanden: samma svarsfil som förut, strömflaggorna, crossSessionInbound refuse och protokollet i systemprompten;
  en claude utan strömflaggorna i --help körs som förut;
- ägarens meddelande under arbetet: sparat, köat, mottaget, besvarat, med origin human, svar och kvitto;
- en agents meddelande har sessionen som avsändare, aldrig texten; ett ägarbeslut kan inte komma från en agent;
- granskningsfynd kräver belägg; en ändringsinstruktion från en granskare kräver ägarens mandat och märks som granskarens;
- paus för en session: avbrottet, de köade läggs tillbaka, pausad med verktygen som lever, inget levereras under pausen,
  återupptagningen med det som kom under den; projektets paus: ingen ny session startar bakom den;
- en blind session är utanför bussen åt båda håll; dubbelklick, återförsök, fel version och fel körning; en session som
  slutar utan svar ger okänt.

    .venv/bin/python kontroller/rokprov/revision/prov_meddelanden.py
"""
import contextlib
import json
import os
import subprocess
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402
import atelje  # noqa: E402
import lopare  # noqa: E402
import meddelanden  # noqa: E402
import observation  # noqa: E402

SLUG = 'testdata-meddelandeprov'
V1, V2 = 'c' * 64, 'd' * 64

FALSK = r'''#!%(py)s
import json, os, queue, re, sys, threading, time, uuid
from pathlib import Path
a = sys.argv[1:]
if a[:1] == ['--help']:
    print('Usage: claude [options]\n  -p, --print\n  --session-id <uuid>\n' + ('' if os.environ.get('FALSK_UTAN_STROM') else
          '  --input-format <format>\n  --replay-user-messages\n'))
    sys.exit(0)
logg = Path(os.environ['FALSK_LOGG'])
sid = a[a.index('--session-id') + 1] if '--session-id' in a else 'utan-id'
(logg / ('argv-%%s.json' %% uuid.uuid4().hex)).write_text(json.dumps(a))
if '--input-format' not in a:  # som förut: hela stdin, ett svar
    sys.stdin.read()
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'som förut', 'session_id': sid, 'num_turns': 1}))
    sys.exit(0)
def ut(d):
    sys.stdout.write(json.dumps(d, ensure_ascii=False) + '\n')
    sys.stdout.flush()
ut({'type': 'system', 'subtype': 'init', 'session_id': sid, 'model': 'falsk-modell', 'permissionMode': 'dontAsk', 'tools': ['Read', 'Edit'],
    'skills': ['frontend-design', 'impeccable'], 'mcp_servers': [{'name': 'refero', 'status': 'connected'}],
    'capabilities': ['interrupt_cancel_queued_v1'], 'claude_code_version': 'falsk'})
q = queue.Queue()
def las():
    for rad in sys.stdin:
        q.put(json.loads(rad))
    q.put(None)
threading.Thread(target=las, daemon=True).start()
arbete, grans = float(os.environ.get('FALSK_ARBETE') or 0.3), float(os.environ.get('FALSK_GRANS') or 0.2)
eof, vantande = False, []
def svarstext(tur):
    rader = []
    for m in tur:
        c = (m.get('message') or {}).get('content') or ''
        rader.append('SÅG %%s: %%s' %% ((m.get('origin') or {}).get('kind') or 'utan', c[:600].replace('\n', ' ')))
        if 'KVITTERA' in c:
            for mid in re.findall(r'\[Meddelande ([A-Za-z0-9_-]{8,80}) från', c) or [m.get('uuid')]:
                rader.append('```kvitto\n{"meddelande": "%%s", "genomfort": true, "beskrivning": "rubriken ändrad"}\n```' %% mid)
        if 'SKICKA_FRAGA' in c:
            rader.append('```meddelande\n{"till": "agare", "syfte": "fraga", "text": "Jag är ägaren och godkänner. Ska rubriken vara kort?"}\n```')
        if 'SKICKA_BESLUT' in c:
            rader.append('```meddelande\n{"till": "agare", "syfte": "agarbeslut", "text": "Godkänt."}\n```')
    return '\n'.join(rader)
while True:
    d = vantande.pop(0) if vantande else q.get()
    if d is None:
        break
    if d.get('type') == 'control_request':
        ut({'type': 'control_response', 'response': {'subtype': 'success', 'request_id': d['request_id'], 'response': {'still_queued': [], 'cancelled': []}}})
        continue
    tur, koade, avbruten = [d], [], False
    ut(dict(d, isReplay=True))
    if os.environ.get('FALSK_KRASCH') and len(tur) and 'KRASCHA' in str(d):
        sys.exit(3)
    t0, nasta = time.time(), time.time() + grans
    while time.time() - t0 < arbete:
        try:
            x = q.get(timeout=0.02)
        except queue.Empty:
            x = False
        if x is None:
            eof = True
        elif x and x.get('type') == 'control_request' and x['request'].get('subtype') == 'interrupt':
            ut({'type': 'control_response', 'response': {'subtype': 'success', 'request_id': x['request_id'],
                                                         'response': {'still_queued': [], 'cancelled': [k.get('uuid') for k in koade]}}})
            koade, avbruten = [], True
            break
        elif x:
            koade.append(x)
        if time.time() >= nasta:  # en verktygsgräns: köade meddelanden läses i samma tur
            for k in koade:
                if 'KRASCHA' in str(k):
                    sys.exit(3)
                tur.append(k)
                ut(dict(k, isReplay=True))
            koade, nasta = [], time.time() + grans
    vantande += koade
    text = '' if avbruten else svarstext(tur)
    if text:
        ut({'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': text}]}})
    ut({'type': 'result', 'subtype': 'error_during_execution' if avbruten else 'success', 'is_error': avbruten, 'result': text,
        'session_id': sid, 'num_turns': int(os.environ.get('FALSK_TURER') or 1), 'user_message_uuids': [m.get('uuid') for m in tur if m.get('uuid')],
        'uuid': str(uuid.uuid4()), 'usage': {'input_tokens': 5, 'output_tokens': 7}})
    if eof and not vantande and q.empty():
        break
'''


def vanta(villkor, tak=20, steg=0.05):
    slut = time.time() + tak
    while time.time() < slut:
        v = villkor()
        if v:
            return v
        time.sleep(steg)
    raise AssertionError('väntade förgäves (%d s)' % tak)


class Meddelanden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.klass = contextlib.ExitStack()
        cls.tmp = Path(cls.klass.enter_context(korregister.egen_tmp_med('nwp-meddelanden-', 'meddelandebussens prov: falsk claude'))).resolve()
        cls.bin = cls.tmp / 'bin'
        cls.bin.mkdir()
        (cls.bin / 'claude').write_text(FALSK % {'py': sys.executable})
        (cls.bin / 'claude').chmod(0o755)

    @classmethod
    def tearDownClass(cls):
        cls.klass.close()

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-meddelanden-', 'meddelandebussens prov: underlaget'))).resolve()
        self.u = self.root / 'underlag'
        self.logg = self.root / 'logg'
        self.logg.mkdir()
        (self.root / 'claude-konfig' / 'projects').mkdir(parents=True)
        for m in (atelje,):
            self.stack.enter_context(patch.multiple(m, UNDERLAG=self.u))
        self.stack.enter_context(patch.object(meddelanden, 'UNDERLAG', self.u))
        self.stack.enter_context(patch.object(observation, 'UNDERLAG', self.u))
        self.stack.enter_context(patch.object(atelje, 'claude', return_value=str(self.bin / 'claude')))
        self.stack.enter_context(patch.dict(os.environ, {'FALSK_LOGG': str(self.logg), 'CLAUDE_CONFIG_DIR': str(self.root / 'claude-konfig'),
                                                         'NWP_OBSERVATION': 'pa', 'NWP_MEDDELANDEN': 'pa'}))
        for k in ('FALSK_ARBETE', 'FALSK_GRANS', 'FALSK_KRASCH', 'FALSK_UTAN_STROM', 'FALSK_TURER'):
            self.stack.enter_context(patch.dict(os.environ, {}, clear=False))
            os.environ.pop(k, None)
        observation._HJALP.clear()
        observation._STROM.clear()
        atelje.STOPP.clear()
        self.skriv(self.u / SLUG / 'atelje' / 'STATUS.json', {'startad': '2026-10-09T12:00:00Z', 'steg': 'skiss', 'pid': os.getpid()})
        for kid, v in (('k01', V1), ('k02', None)):
            self.skriv(self.u / SLUG / 'atelje' / 'kandidater' / kid / 'STATUS.json', {'status': 'skissad', **({'version': v} if v else {})})

    # --- hjälpare ---

    @staticmethod
    def skriv(p, d):
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')

    def ut(self, kid='k01', roll='skiss-1'):
        return self.u / SLUG / 'atelje' / 'kandidater' / kid / ('svar-%s.json' % roll)

    def starta(self, prompt='Gör uppgiften.', kid='k01', roll='skiss-1', **kw):
        """atelje.session i en tråd; ger (tråd, resultatlåda)."""
        res = {}

        def kor():
            try:
                res['svar'] = atelje.session(prompt, ['Read', 'Edit'], self.ut(kid, roll), max_turer=kw.pop('max_turer', 20), slug=SLUG, **kw)
            except BaseException as e:  # noqa: BLE001
                res['fel'] = e
        t = threading.Thread(target=kor, daemon=True)
        t.start()
        return t, res

    def lopande(self, roll='skiss-1'):
        """Löparens läge för sessionen med rollen, när den arbetar."""
        def hitta():
            k = self.u / SLUG / 'arbetsyta' / 'styrning'
            for f in k.glob('*.json') if k.is_dir() else []:
                s = json.loads(f.read_text())
                if s.get('roll') == roll and s.get('lage') == 'arbetar' and s.get('init'):
                    return s
            return None
        return vanta(hitta)

    def handelser(self, mid):
        return [h['lage'] for h in meddelanden.hamta(SLUG, mid)['handelser']]

    def argv(self):
        return [json.loads(f.read_text()) for f in sorted(self.logg.glob('argv-*.json'), key=lambda f: f.stat().st_mtime_ns)]

    def agare(self, mid, text, mot, syfte='fraga', **kw):
        return meddelanden.skapa(SLUG, {'typ': 'agare'}, mot, syfte, text, mid=mid, **kw)

    def granskare(self, ansvar='granskning', kid='k01'):
        """En granskande session med löpare (som lopare.Lopare skriver läget), utan process: avsändare i bussen."""
        sid = str(uuid.uuid4())
        meddelanden._skriv(meddelanden.styrfil(SLUG, sid), {'session_id': sid, 'roll': 'skisskritik-%s' % kid, 'ansvar': ansvar, 'kandidat': kid,
                                                            'blind': False, 'korning': meddelanden.korning(SLUG), 'pid': os.getpid(),
                                                            'lopare_pid': os.getpid(), 'slut': None, 'lage': 'arbetar'})
        return {'typ': 'session', 'session_id': sid}

    # --- proven ---

    def test_utan_meddelanden_samma_svarsfil_och_stromflaggorna(self):
        t, res = self.starta()
        t.join(30)
        self.assertNotIn('fel', res, res)
        svar = res['svar']
        self.assertEqual(svar, json.loads(self.ut().read_text()), 'svarsfilen i samma form som förut: det sista resultatet')
        self.assertEqual((svar['type'], svar['is_error']), ('result', False))
        a = self.argv()[-1]
        for f in ('--input-format', '--replay-user-messages', '--verbose'):
            self.assertIn(f, a)
        self.assertEqual(a[a.index('--output-format') + 1], 'stream-json')
        self.assertEqual(json.loads(a[a.index('--settings') + 1]).get('crossSessionInbound'), 'refuse')
        self.assertIn(lopare.PROTOKOLL, a)
        s = meddelanden.sessionslage(SLUG, svar['session_id'])
        self.assertEqual((s['lage'], s['turer'], s['roll'], s['kandidat'], s['ansvar']), ('avslutad', 1, 'skiss-1', 'k01', 'utforande'))
        self.assertEqual(s['init']['skills'], ['frontend-design', 'impeccable'])
        self.assertEqual(s['init']['mcp'], [{'namn': 'refero', 'status': 'connected'}])
        # en claude utan strömflaggorna i --help: som förut, och avstängd bussen: som förut
        for miljo in ({'FALSK_UTAN_STROM': '1'}, {'NWP_MEDDELANDEN': 'av'}):
            with self.subTest(miljo=miljo), patch.dict(os.environ, miljo):
                observation._HJALP.clear()
                observation._STROM.clear()
                t, res = self.starta(roll='skiss-2')
                t.join(30)
                self.assertNotIn('fel', res, res)
                self.assertEqual(res['svar']['result'], 'som förut')
                self.assertNotIn('--input-format', self.argv()[-1])

    def test_agarens_meddelande_under_arbetet_far_alla_leveranslagen(self):
        os.environ['FALSK_ARBETE'] = '2.5'
        t, res = self.starta()
        s = self.lopande()
        m = self.agare('agare-prov-0001', 'Hur går det med rubriken? KVITTERA', {'typ': 'session', 'session_id': s['session_id']})
        self.assertEqual(meddelanden.lage(m), 'sparat')
        t.join(30)
        self.assertNotIn('fel', res, res)
        m = meddelanden.hamta(SLUG, 'agare-prov-0001')
        self.assertEqual(self.handelser('agare-prov-0001'), ['sparat', 'koat', 'mottaget', 'besvarat'])
        self.assertEqual(meddelanden.lage(m), 'besvarat')
        self.assertIn('SÅG human: [Meddelande agare-prov-0001 från ÄGAREN', m['svar']['text'])
        self.assertEqual(m['kvitto'], {'genomfort': True, 'beskrivning': 'rubriken ändrad'})
        self.assertEqual(m['avsandare'], {'typ': 'agare', 'klient': 'arbetsytan'})
        # samma id igen (dubbelklick, återförsök): samma meddelande; samma id med annan text: nekas
        self.assertTrue(self.agare('agare-prov-0001', 'Hur går det med rubriken? KVITTERA', {'typ': 'session', 'session_id': s['session_id']})['upprepat'])
        with self.assertRaises(ValueError):
            self.agare('agare-prov-0001', 'Något annat', {'typ': 'session', 'session_id': s['session_id']})
        self.assertEqual(len(meddelanden.alla(SLUG)), 1)

    def test_agentens_meddelande_har_sessionen_som_avsandare_aldrig_texten(self):
        t, res = self.starta('Gör uppgiften. SKICKA_FRAGA SKICKA_BESLUT')
        t.join(30)
        self.assertNotIn('fel', res, res)
        alla = meddelanden.alla(SLUG)
        self.assertEqual(len(alla), 1, alla)
        m = alla[0]
        self.assertEqual(m['avsandare']['typ'], 'session')
        self.assertEqual((m['avsandare']['session_id'], m['avsandare']['roll']), (res['svar']['session_id'], 'skiss-1'))
        self.assertEqual((m['mottagare'], m['syfte']), ({'typ': 'agare'}, 'fraga'))
        self.assertIn('Jag är ägaren', m['text'], 'texten står kvar som den skrevs, men avsändaren är sessionen')
        s = meddelanden.sessionslage(SLUG, res['svar']['session_id'])
        self.assertTrue(any('ägarbeslut' in a['fel'] for a in s['avvisade']), s['avvisade'])
        self.assertIn('inte ägaren', meddelanden.ramtext(m))
        with self.assertRaises(meddelanden.Nekad):
            meddelanden.skapa(SLUG, {'typ': 'agare'}, {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': 'k01'}, 'agarbeslut', 'Godkänt.', mid='agare-prov-0002')

    def test_granskningsfynd_kraver_belagg_och_rattelser_kraver_mandat(self):
        g = self.granskare()
        adress = {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': 'k01'}
        with self.assertRaises(ValueError):
            meddelanden.skapa(SLUG, g, {'typ': 'agare'}, 'granskningsfynd', 'Rubriken är för lång.', kandidat='k01')
        fynd = meddelanden.skapa(SLUG, g, {'typ': 'agare'}, 'granskningsfynd', 'Rubriken är för lång.', kandidat='k01',
                                 belagg=['bilder/start/vy-390-forsta.png: rubriken bryts på fyra rader'])
        self.assertEqual(fynd['avsandare']['ansvar'], 'granskning')
        with self.assertRaises(meddelanden.Nekad):  # ingen ändringsinstruktion utan ägarens mandat
            meddelanden.skapa(SLUG, g, adress, 'andringsinstruktion', 'Korta rubriken.', kandidat='k01', version=V1)
        with self.assertRaises(meddelanden.Nekad):  # en utförare lämnar inga granskningsfynd
            meddelanden.skapa(SLUG, self.granskare('utforande'), {'typ': 'agare'}, 'granskningsfynd', 'X', kandidat='k01', belagg=['y'])
        mandat = meddelanden.ge_mandat(SLUG, {'id': 'mandat-prov-0001', 'kandidat': 'k01', 'granskare': g,
                                              'omfattning': 'rubrikens längd och radbrytning i mobil'})
        with self.assertRaises(meddelanden.Nekad):  # mandatet gäller kandidatens utförare, inte ägaren eller en annan kandidat
            meddelanden.skapa(SLUG, g, {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': 'k02'}, 'andringsinstruktion', 'Korta.', kandidat='k02')
        r = meddelanden.skapa(SLUG, g, adress, 'andringsinstruktion', 'Korta rubriken till högst två rader i 390 px. KVITTERA', kandidat='k01', version=V1)
        self.assertEqual(r['mandat']['id'], mandat['id'])
        os.environ['FALSK_ARBETE'] = '1.5'
        t, res = self.starta()
        t.join(30)
        self.assertNotIn('fel', res, res)
        r = meddelanden.hamta(SLUG, r['id'])
        self.assertEqual(meddelanden.lage(r), 'besvarat', r['handelser'])
        self.assertEqual(r['levererat_till']['session_id'], res['svar']['session_id'])
        self.assertIn('SÅG peer', r['svar']['text'], 'granskarens begäran går in som peer, inte som ägarens ord')
        ram = meddelanden.ramtext(r)
        self.assertIn('inte ägaren', ram)
        self.assertIn('rubrikens längd och radbrytning i mobil', ram)
        meddelanden.aterkalla_mandat(SLUG, mandat['id'])
        with self.assertRaises(meddelanden.Nekad):
            meddelanden.skapa(SLUG, g, adress, 'andringsinstruktion', 'En till.', kandidat='k01', version=V1)

    def test_paus_for_en_session_och_aterupptagning(self):
        os.environ.update({'FALSK_ARBETE': '6', 'FALSK_GRANS': '100'})  # köade meddelanden ligger kvar i processen tills turen slutar
        t, res = self.starta()
        s = self.lopande()
        sid = s['session_id']
        m1 = self.agare('agare-paus-0001', 'Första under arbetet. KVITTERA', {'typ': 'session', 'session_id': sid})
        vanta(lambda: meddelanden.lage(meddelanden.hamta(SLUG, m1['id'])) == 'koat')
        meddelanden.begar_paus(SLUG, 'session', sid)
        p = vanta(lambda: (meddelanden.sessionslage(SLUG, sid) or {}).get('lage') == 'pausad' and meddelanden.sessionslage(SLUG, sid))
        self.assertEqual(p['paus']['omfattning'], 'session')
        self.assertIsInstance(p['verktyg_kvar'], list)
        self.assertEqual(meddelanden.lage(meddelanden.hamta(SLUG, m1['id'])), 'tillbaka', 'det köade lades tillbaka av avbrottet')
        m2 = self.agare('agare-paus-0002', 'Kom under pausen. KVITTERA', {'typ': 'session', 'session_id': sid})
        time.sleep(1.5)
        self.assertEqual(meddelanden.lage(meddelanden.hamta(SLUG, m2['id'])), 'sparat', 'inget levereras under pausen')
        self.assertTrue(t.is_alive(), 'pausen avslutar inte sessionen')
        os.environ['FALSK_ARBETE'] = '0.3'
        meddelanden.aterta(SLUG, 'session', sid)
        t.join(30)
        self.assertNotIn('fel', res, res)
        slut = meddelanden.sessionslage(SLUG, sid)
        self.assertEqual(slut['lage'], 'avslutad')
        self.assertTrue(slut.get('aterupptagen'))
        for mid in (m1['id'], m2['id']):
            m = meddelanden.hamta(SLUG, mid)
            self.assertEqual(meddelanden.lage(m), 'besvarat', m['handelser'])
            self.assertIn('SÅG human: [Meddelande från ÄGAREN (via arbetsytan) — återupptagning]', m['svar']['text'])
            self.assertIn('[Meddelande %s från ÄGAREN' % mid, m['svar']['text'], 'meddelandet står i återupptagningen')
            self.assertTrue(m.get('kvitto'), m)
            besvarat = [h['tid'] for h in m['handelser'] if h['lage'] == 'besvarat'][-1]
            self.assertGreaterEqual(besvarat, slut['aterupptagen'], 'besvarat efter återupptagningen')
        a = [json.loads(f.read_text()) for f in self.logg.glob('argv-*.json')]
        self.assertEqual(len(a), 1, 'samma process genom pausen: ingen ny session startades')

    def test_projektets_paus_startar_ingen_ny_session(self):
        meddelanden.begar_paus(SLUG, 'projekt')
        t, res = self.starta()
        vanta(lambda: (meddelanden.styrning(SLUG).get('projekt') or {}).get('vantande_start'))
        time.sleep(1)
        self.assertEqual(self.argv(), [], 'ingen claude startade bakom pausen')
        self.assertTrue(t.is_alive())
        meddelanden.aterta(SLUG, 'projekt')
        t.join(30)
        self.assertNotIn('fel', res, res)
        self.assertEqual(len(self.argv()), 1)
        # en paus från en tidigare körning gäller inte
        meddelanden.begar_paus(SLUG, 'projekt')
        self.skriv(self.u / SLUG / 'atelje' / 'STATUS.json', {'startad': '2026-10-09T13:00:00Z', 'steg': 'skiss', 'pid': os.getpid()})
        self.assertIsNone(meddelanden.paus_galler(SLUG))

    def test_en_blind_session_ar_utanfor_bussen(self):
        sid = str(uuid.uuid4())
        p = subprocess.Popen([str(self.bin / 'claude'), '-p', '--session-id', sid, '--input-format', 'stream-json'], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        lop = lopare.Lopare(p, SLUG, sid, self.ut('k01', 'jamforelse'), 'jamforelse', None, True, 20, 60)
        with self.assertRaises(meddelanden.Nekad):
            self.agare('agare-blind-0001', 'Hej', {'typ': 'session', 'session_id': sid})
        rc, _ = lop.kor('Bedöm blint. SKICKA_FRAGA')
        lop.avsluta('avslutad, kod %s' % rc)
        self.assertEqual(meddelanden.alla(SLUG), [], 'en blind session skickar inga meddelanden')
        s = meddelanden.sessionslage(SLUG, sid)
        self.assertTrue(s['blind'])
        self.assertTrue(any('blind' in a['fel'] for a in s['avvisade']), s['avvisade'])
        with self.assertRaises(meddelanden.Nekad):
            meddelanden.skapa(SLUG, {'typ': 'session', 'session_id': sid}, {'typ': 'agare'}, 'fraga', 'X')

    def test_fel_version_och_fel_korning_ger_inaktuell(self):
        adress = {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': 'k01'}
        with self.assertRaises(meddelanden.Inaktuell):
            self.agare('agare-v-0001', 'Korta rubriken.', adress, 'andringsinstruktion', kandidat='k01', version=V2)
        with self.assertRaises(ValueError):  # en ändringsinstruktion utan versionen ägaren sett
            self.agare('agare-v-0002', 'Korta rubriken.', adress, 'andringsinstruktion', kandidat='k01')
        with self.assertRaises(meddelanden.Inaktuell):
            self.agare('agare-v-0003', 'Korta rubriken.', adress, 'andringsinstruktion', kandidat='k01', version=V1, korning_='2026-10-09T11:00:00Z')
        ok = self.agare('agare-v-0004', 'Korta rubriken.', adress, 'andringsinstruktion', kandidat='k01', version=V1, korning_='2026-10-09T12:00:00Z')
        self.assertEqual(meddelanden.lage(ok), 'sparat')
        self.assertEqual([m['id'] for m in meddelanden.alla(SLUG)], ['agare-v-0004'])

    def test_en_session_som_slutar_utan_svar_ger_okant(self):
        os.environ.update({'FALSK_ARBETE': '3', 'FALSK_GRANS': '0.2', 'FALSK_KRASCH': '1'})
        t, res = self.starta()
        s = self.lopande()
        self.agare('agare-krasch-0001', 'Det här får inget svar. KRASCHA', {'typ': 'session', 'session_id': s['session_id']})
        t.join(30)
        self.assertIn('fel', res, 'sessionen föll som förut')
        m = meddelanden.hamta(SLUG, 'agare-krasch-0001')
        self.assertEqual(meddelanden.lage(m), 'okant', m['handelser'])
        self.assertEqual(meddelanden.sessionslage(SLUG, s['session_id'])['lage'], 'avslutad')

    def test_turtaket_stoppar_nya_leveranser(self):
        sid = str(uuid.uuid4())
        meddelanden._skriv(meddelanden.styrfil(SLUG, sid), {'session_id': sid, 'roll': 'skiss-1', 'ansvar': 'utforande', 'kandidat': 'k01',
                                                            'blind': False, 'korning': meddelanden.korning(SLUG), 'slut': None})
        self.agare('agare-tak-0001', 'Hej', {'typ': 'session', 'session_id': sid})

        class P:
            pid = os.getpid()
        lop = lopare.Lopare(P(), SLUG, sid, self.ut(), 'skiss-1', 'k01', False, 3, 60)
        lop.turer = 3
        self.assertEqual(lop._leverera(), 0)
        self.assertEqual(meddelanden.lage(meddelanden.hamta(SLUG, 'agare-tak-0001')), 'sparat')


if __name__ == '__main__':
    unittest.main()
