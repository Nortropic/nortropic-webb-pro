#!/usr/bin/env python3
"""Arbetsytans läsväg, partnersamtal och HTTP-väg (dashboard/arbetsyta.py, dashboard/partner.py, server.py; ägarens uppdrag
2026-10-09) med testprojektet ur arbetsyta_fixtur.py i en isolerad rot, utan modell:

- läget ur testprojektet: testdata, blindningen, neutrala etiketter, ansvaren och förhandsvisningarna;
- sessionernas lägen ur förteckningen, transkripten och svarsfilerna: avslutad, avbruten (fel i svaret, stopp, signal,
  död process), aktiv, väntar på verktyg, start pågår och okänt;
- blindningen på servervägen: aktivitetens sökvägar, körningsloggen, DESIGN.md och föreversionerna i kodvyn före ägarens
  första val, och en arm i en blind jämförelse som inte visas alls; maskerade hemligheter efter valet;
- kodvyn: diffen mot den bevarade versionen, inga länkar och inga vägar ut ur projektet;
- ägarens ändring: bunden till körningen och den hela versionen ägaren såg, egen text och markering (aldrig "det ägaren
  gillade"); inaktuell körning, version och steg nekas; samma ändrings-id ger samma rad;
- partnern: en session per kund (--session-id, sedan --resume), ett meddelande i taget, bara claude-processer räknas, och
  tillåtelselistan; claude startas aldrig (en falsk process står för den);
- HTTP genom den riktiga hanteraren: ramskydd, strömmens ursprung, nyckeln och ursprunget för skrivningar, 409 och 404;
- signaturen och det delade läget som strömmen läser om läget efter.

Fallen ur den oberoende granskningen och omgranskningen (underlag/granskningar/GR-20261009-arbetsyta-oberoende.md och
GR-20261009-arbetsyta-omgranskning.md) står vid sina prov.

    .venv/bin/python -B kontroller/rokprov/revision/prov_arbetsyta.py

Sajtens del av testprojektet kopieras ur rökprovets byggda mallsajt (kunder/rokprov-mall/sajt, som rokprov.sh bygger
tidigare); saknas den hoppas det som kräver sajten över med skälet. I rökprovet finns mallsajten, och där fäller ett
överhoppat prov rökprovet.
"""
import contextlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as dash  # noqa: E402
import arbetsyta  # noqa: E402
import partner  # noqa: E402
import samverkan  # noqa: E402
import extern_granskare  # noqa: E402
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import kandidater  # noqa: E402
import meddelanden  # noqa: E402
import korregister  # noqa: E402
import nastlad  # noqa: E402
import observation  # noqa: E402
import skapande  # noqa: E402
import arbetsyta_fixtur  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MALLSAJT = ROOT / 'kunder' / 'rokprov-mall' / 'sajt'  # rökprovets byggda mallsajt
SLUG = 'testdata-arbetsytans-prov'  # ett eget namn: inget i worktreens egna underlag/ eller kunder/ läses av misstag
TKAT = '-prov-arbetsyta'  # transkriptens katalog under Claude Codes projects/
TILLAGG = '<!-- arbetsytans testdata: ändrad efter fotograferingen -->'  # fixturens rad i arbetsversionen
PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                    '1f15c4890000000d49444154789c6360f8cf00000301010018dd8db00000000049454e44ae426082')
V_NU, V_FORE = 'b' * 64, 'a' * 64  # k02:s fotograferade version och föreversionen före en förbättringsrunda
ORIG_POPEN = subprocess.Popen
ORIG_RUN = subprocess.run


def utan_sajt():
    return 'mallsajten är inte byggd (%s saknas; rokprov.sh bygger den tidigare): det som kräver sajten hoppas över' % (
        MALLSAJT / 'dist' / 'index.html')


def tunn_mallsajt(kalla, mal):
    """Mallsajten utan node_modules (fixturen klonar annars beroendena i varje prov): källan, public/, dist/ och
    projektfilerna. Mallen har ingen DESIGN.md; en med skaparens förklaring läggs till, så att kodvyns blindning prövas."""
    mal.mkdir(parents=True)
    for namn in ('src', 'public', 'dist'):
        if (kalla / namn).is_dir():
            shutil.copytree(kalla / namn, mal / namn, symlinks=False)
        else:
            (mal / namn).mkdir()
    for namn in ('package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json', 'DESIGN.md'):
        if (kalla / namn).is_file():
            shutil.copyfile(kalla / namn, mal / namn)
    if not (mal / 'DESIGN.md').is_file():
        (mal / 'DESIGN.md').write_text('# Design (testdata)\n\nMARKOR-SKAPARENS-FORKLARING\n', encoding='utf-8')
    return mal


def anrop(id_, namn, fil, tid):
    """En rad i transkriptet: assistentens verktygsanrop (som Claude Codes transkript bär det)."""
    return {'type': 'assistant', 'timestamp': tid, 'message': {'model': 'claude-fable-5-1', 'usage': {'input_tokens': 120},
                                                               'content': [{'type': 'tool_use', 'id': id_, 'name': namn, 'input': {'file_path': fil}}]}}


def svar(id_, tid):
    """En rad i transkriptet: verktygets svar på anropet id_."""
    return {'type': 'user', 'timestamp': tid, 'message': {'content': [{'type': 'tool_result', 'tool_use_id': id_, 'content': 'ok'}]}}


def stoppa(p):
    if p.poll() is None:
        p.kill()
    p.wait()


def dod_pid():
    """En pid som inte lever: en process som redan har slutat och tagits om hand."""
    p = ORIG_POPEN(['true'])
    p.wait()
    return p.pid


def vanta_pa_vakter(frist=20):
    """Partnerns vakttrådar (partner._vakta) har skrivit sluttiden; ingen skriver i provets katalog efteråt."""
    for t in threading.enumerate():
        if t.name.endswith('(_vakta)'):
            t.join(frist)


def ingen_editor(argv, *a, **k):
    """subprocess.run under provet: editorn öppnas aldrig, allt annat körs som vanligt."""
    if list(argv)[:1] == ['open']:
        raise AssertionError('editorn får inte öppnas i provet: %s' % list(argv))
    return ORIG_RUN(argv, *a, **k)


class FalskProcess:
    def __init__(self, p):
        self.p, self.pid, self.returncode, self.prompt = p, p.pid, None, None

    def communicate(self, input=None, timeout=None):
        self.prompt = input.decode() if input else self.prompt
        self.returncode = self.p.wait(timeout=timeout)
        return b'', b''


class FalskClaude:
    """claude -p i partnerns ställe: pid:en är en riktig kortlivad process som bär sessionens id i sina argument (som en
    tur gör; partnern prövar det), och svaret skrivs till stdout-filen som Claude Code skriver sin svarsfil. Ingen modell
    anropas, och något annat än claude startas aldrig här."""

    def __init__(self):
        self.anrop, self.processer, self.svara, self.sov = [], [], True, '0.3'

    def __call__(self, args, **kw):
        args = list(args)
        if os.path.basename(str(args[0])) != 'claude':
            raise AssertionError('partnern startade något annat än claude: %s' % args[:3])
        self.anrop.append(args)
        sid = args[args.index('--session-id' if '--session-id' in args else '--resume') + 1]
        p = ORIG_POPEN([sys.executable, '-c', 'import sys, time; time.sleep(float(sys.argv[1]))', self.sov, '--resume', sid],
                       stdin=subprocess.DEVNULL)
        if self.svara:
            kw['stdout'].write(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'Svar (testdata).',
                                           'session_id': sid, 'num_turns': 1, 'usage': {'input_tokens': 12, 'output_tokens': 3}}).encode())
            kw['stdout'].flush()
        fp = FalskProcess(p)
        self.processer.append(fp)
        return fp

    def stada(self):
        for fp in self.processer:
            stoppa(fp.p)
        vanta_pa_vakter()


class Arbetsyta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.klass = contextlib.ExitStack()
        cls.sajt = None
        try:
            if (MALLSAJT / 'dist' / 'index.html').is_file():
                d = Path(cls.klass.enter_context(korregister.egen_tmp_med('nwp-arbetsyta-', 'arbetsytans prov: mallsajten utan beroenden')))
                cls.sajt = tunn_mallsajt(MALLSAJT, d / 'sajt')
        except BaseException:
            cls.klass.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.klass.close()

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-arbetsyta-', 'arbetsytans syntetiska testprojekt'))).resolve()
        self.u, self.k = self.root / 'underlag' / SLUG, self.root / 'kunder' / SLUG
        self.projekt = self.root / 'claude-konfig' / 'projects'
        (self.projekt / TKAT).mkdir(parents=True)
        for m in (dash, atelje):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.multiple(observation, ROOT=self.root, UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.object(meddelanden, 'UNDERLAG', self.root / 'underlag'))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.projekt))
        if hasattr(arbetsyta, '_DELAT'):  # strömmarnas delade läge gäller provets egen rot
            self.stack.enter_context(patch.dict(arbetsyta._DELAT, clear=True))
        # ingen riktig claude kan startas ur provet, inte heller om en attrapp skulle missas
        self.stack.enter_context(patch.object(atelje, 'claude', return_value=str(self.root / 'saknas' / 'claude')))
        arbetsyta_fixtur.bygg(self.root, SLUG, self.sajt, med_sajt=self.sajt is not None)
        # den bevarade ögonblicksbilden av k01 (fixturen fotograferar inte)
        b = self.u / 'atelje' / 'kandidater' / 'k01' / 'bilder' / 'start' / 'vy-390-forsta.png'
        b.parent.mkdir(parents=True)
        b.write_bytes(PNG)
        self.status = self.las(self.u / 'atelje' / 'STATUS.json')

    # --- hjälpare ---

    @staticmethod
    def las(p):
        return json.loads(Path(p).read_text(encoding='utf-8'))

    @staticmethod
    def skriv(p, d):
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')

    def skriv_status(self, **falt):
        f = self.u / 'atelje' / 'STATUS.json'
        st = dict(self.las(f), **falt)
        self.skriv(f, st)
        return st

    def lage(self):
        return arbetsyta.lage(dash, SLUG)

    def levande(self):
        p = ORIG_POPEN(['sleep', '60'], stdin=subprocess.DEVNULL)
        self.addCleanup(stoppa, p)
        return p.pid

    def session(self, roll, rader=None, kandidat='k01', slut=None, utfall=None, pid=None, start='2026-10-09T05:10:00Z'):
        """En post i ateljéns sessionsförteckning (som atelje.session skriver den) och, med rader, sessionens transkript."""
        sid = str(uuid.uuid4())
        self.skriv(self.u / 'atelje' / 'sessioner' / (sid + '.json'),
                   {'session_id': sid, 'roll': roll, 'kandidat': kandidat, 'svar': 'svar-%s.json' % roll, 'start': start,
                    'modell': 'claude-fable-5-1', 'pid': pid, 'slut': slut, 'utfall': utfall})
        if rader is not None:
            (self.projekt / TKAT / (sid + '.jsonl')).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rader), encoding='utf-8')
        return sid

    def agarens_val(self, tid='2026-10-09T06:00:00Z'):
        """Ägarens första val efter planen, som atelje.doma skriver det i kandidatflödet (prov_flode.py, dom)."""
        p = kandidater.plan_tid(SLUG)
        namn = kandidater.etiketter(SLUG, kandidater.lista(SLUG))
        return skapande.lagg_till_dom(SLUG, 'ägaren', 'valj', 'Ägarens ord: valj.', avser='skapandeflödet, kandidatplanen %s' % p,
                                      underlag=self.root / 'underlag', tid=tid, plan=p,
                                      kandidater=[{'id': 'k01', 'version': kandidater.las_status(SLUG, 'k01').get('version'),
                                                   'etikett': namn.get('k01'), 'plan': p, 'metod': None}])

    def domrader(self):
        f = self.u / skapande.DOMLOGG
        return [json.loads(x) for x in f.read_text(encoding='utf-8').splitlines() if x.strip()] if f.is_file() else []

    def bevarad_version(self, kid, v, text, mtid):
        """versioner/<v12>/ med koden, som kandidater.bevara_version lämnar den."""
        d = self.u / 'atelje' / 'kandidater' / kid / 'versioner' / v[:12]
        (d / 'kod').mkdir(parents=True)
        (d / 'kod' / 'index.astro').write_text(text, encoding='utf-8')
        (d / 'VERSION').write_text(v + '\n', encoding='utf-8')
        os.utime(d, (mtid, mtid))

    def k02_fotograferad(self, fore=False):
        """k02 fotograferad med en egen bevarad version (utan sajt, så att ändringens väg inte kräver mallsajten), och med
        fore en bevarad föreversion före en förbättringsrunda (kandidater.forbattra)."""
        nu = time.time()
        if fore:
            self.bevarad_version('k02', V_FORE, '<h1>Rubrik</h1>\n<img src="x.jpg">\n', nu - 600)
        self.bevarad_version('k02', V_NU, '<h1>Rubrik</h1>\n<img src="x.jpg" alt="Verkstaden">\n', nu - 60)
        f = self.u / 'atelje' / 'kandidater' / 'k02' / 'STATUS.json'
        self.skriv(f, dict(self.las(f), version=V_NU, fotograferad='2026-10-09T05:31:00Z',
                           **({'forbattrad': {'fore': V_FORE, 'atgarder': ['alt-text på bilden']}} if fore else {})))
        return V_NU

    def andring(self, **falt):
        return dict({'andring_id': 'andring-prov-0001', 'text': 'Rubriken ska vara större.', 'kandidat': 'k02', 'version': V_NU,
                     'korning': self.status['startad'], 'vy': 'Arbetsyta', 'sida': '/', 'del': 'rubriken'}, **falt)

    def falsk_partner(self):
        """Partnerns claude ersatt av FalskClaude (bara i partner-modulen) och processlistan tom."""
        falsk = FalskClaude()
        self.addCleanup(falsk.stada)
        self.stack.enter_context(patch.object(partner, 'subprocess', SimpleNamespace(
            Popen=falsk, PIPE=subprocess.PIPE, run=subprocess.run, TimeoutExpired=subprocess.TimeoutExpired, SubprocessError=subprocess.SubprocessError)))
        ps = self.stack.enter_context(patch.object(partner, '_ps', return_value=''))
        return falsk, ps

    def partnerpost(self, sid, pid, tid):
        """PARTNER.json med ett meddelande vars tur har processen pid och startade tid, utan svar."""
        self.skriv(self.u / 'arbetsyta' / 'PARTNER.json', {'schema': 'partner/1', 'slug': SLUG, 'session_id': sid, 'korning': self.status['startad'], 'blind_vid_start': True, 'skapad': tid,
                                                           'meddelanden': [{'id': 'meddelande-n4-0001', 'tid': tid, 'avsikt': 'fraga', 'text': 'Hej?',
                                                                            'svarsfil': 'svar-meddelande-n4-0001.json', 'pid': pid}]})

    def server(self):
        """Den riktiga hanteraren på en egen port, med nyckel, värd och en kort strömlivslängd."""
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
        return port, host, anropa

    def vanta_pa_strommar(self, fore):
        slut = time.time() + 15
        while dash.STROMMAR['antal'] != fore and time.time() < slut:
            time.sleep(0.1)
        self.assertEqual(dash.STROMMAR['antal'], fore, 'strömmen slutar och släpper sin plats')

    # --- läget ---

    def test_laget_ur_testprojektet_ar_blint_med_neutrala_etiketter(self):
        l = self.lage()
        self.assertEqual(l['ofullstandig'], [], l['ofullstandig'])
        self.assertEqual((l['projekt']['slug'], l['projekt']['testdata']), (SLUG, True))
        self.assertTrue(l['blind'])
        self.assertFalse(l['ab_dold'])
        self.assertEqual([x['slug'] for x in arbetsyta.projekt(dash)], [SLUG])
        self.assertEqual(sorted(x['etikett'] for x in l['kandidater']), ['Förslag A', 'Förslag B'])
        self.assertEqual(sorted(x['id'] for x in l['kandidater']), ['k01', 'k02'])
        text = json.dumps(l, ensure_ascii=False)
        for dolt in ('Testdata: verkstaden i arbete', 'Testdata: lugn lista', 'Testdata k01'):  # planens och kandidaternas titlar
            self.assertNotIn(dolt, text, 'titeln syns före ägarens första val')
        self.assertEqual({n: r['lage'] for n, r in l['roller'].items()}, {'arbetsledning': 'vantar', 'utforande': 'beslut', 'granskning': 'vantar'})
        self.assertTrue(all(r['sessioner'] == [] for r in l['roller'].values()), l['roller'])
        self.assertIn('ingen session för granskning har startat', l['roller']['granskning']['lage_text'])
        self.assertTrue(l['korning']['vantar_pa_agaren'], l['korning'])
        pv = l['preview']
        snap = [x for x in pv if x['typ'] == 'snapshot' and x.get('kandidat') == 'k01']
        self.assertEqual(len(snap), 1, pv)
        self.assertEqual(snap[0]['aldre'], self.sajt is None, snap)
        if self.sajt is None:
            self.skipTest(utan_sajt())
        arb = [x for x in pv if x['typ'] == 'arbetsversion' and x.get('kandidat') == 'k01']
        self.assertEqual(len(arb), 1, pv)
        self.assertEqual(arb[0]['url'], '/visa/%s/k01' % SLUG)
        k01 = next(x for x in l['kandidater'] if x['id'] == 'k01')
        self.assertTrue(k01['preview']['finns'])
        self.assertEqual(k01['version'], kandidater.las_status(SLUG, 'k01')['version'][:12])
        self.assertEqual(k01['versioner'], [k01['version']])
        self.assertEqual(snap[0]['version'], k01['version'])

    def test_rollerna_beslut_ur_korningen_och_partnern_avslutad_efter_svar(self):
        # GR-20261009-arbetsyta-oberoende#A2: ditt beslut härleds ur körningen, inte ur att partnern svarat
        r = self.lage()['roller']
        self.assertEqual((r['utforande']['lage'], r['granskning']['lage'], r['arbetsledning']['lage']), ('beslut', 'vantar', 'vantar'), r)
        self.assertIn('väntar på ditt beslut', r['utforande']['lage_text'])
        sid = str(uuid.uuid4())
        self.skriv(self.u / 'arbetsyta' / 'PARTNER.json', {'schema': 'partner/1', 'slug': SLUG, 'session_id': sid, 'korning': self.status['startad'], 'blind_vid_start': True, 'skapad': '2026-10-09T06:00:00Z',
                                                           'meddelanden': [{'id': 'meddelande-0001', 'tid': '2026-10-09T06:00:00Z', 'avsikt': 'fraga',
                                                                            'text': 'Var står vi?', 'svarsfil': 'svar-meddelande-0001.json', 'pid': None,
                                                                            'slut': '2026-10-09T06:01:00Z', 'rc': 0}]})
        self.skriv(self.u / 'arbetsyta' / 'partner' / 'svar-meddelande-0001.json', {'type': 'result', 'is_error': False, 'result': 'Svar.', 'session_id': sid})
        with patch.object(partner, '_ps', return_value=''):
            p = partner.lage(dash, SLUG)
            r = self.lage()['roller']
        self.assertEqual(p['lage'], 'avslutad', p['lage_text'])
        self.assertEqual(r['arbetsledning']['lage'], 'avslutad', r['arbetsledning'])
        self.assertEqual(r['utforande']['lage'], 'beslut')
        # en levande utförare: utförandet arbetar, inget beslut väntar där
        pid = self.levande()
        self.session('forfina-k01', pid=pid, rader=[anrop('f1', 'Read', str(self.u / 'BRIEF.md'), '2026-10-09T05:11:00Z'),
                                                    svar('f1', '2026-10-09T05:12:00Z')])
        with patch.object(nastlad, 'ar_session', side_effect=lambda x: int(x) == pid), patch.object(partner, '_ps', return_value=''):
            r = self.lage()['roller']
        self.assertEqual(r['utforande']['lage'], 'aktiv', r['utforande'])
        self.assertEqual(r['granskning']['lage'], 'vantar')

    # --- sessionernas lägen ---

    def test_sessionernas_lagen_ur_forteckningen_och_transkripten(self):
        flode_pid, annan_pid = self.levande(), self.levande()
        t = '2026-10-09T05:1%d:00Z'
        rot = str(self.root)
        sid = {
            'avslutad': self.session('skiss-k01', slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0'),
            'stoppet': self.session('skiss-k02', kandidat='k02', slut='2026-10-09T05:22:00Z', utfall='avbruten vid stoppet'),
            'signal': self.session('skisskritik-k01', slut='2026-10-09T05:23:00Z', utfall='avslutad, kod -9'),
            'dod': self.session('forfina-k01', pid=dod_pid()),
            'aktiv': self.session('skiss-k01', pid=flode_pid, rader=[anrop('b1', 'Read', rot + '/underlag/%s/BRIEF.md' % SLUG, t % 1), svar('b1', t % 2)]),
            'verktyg': self.session('skiss-k02', kandidat='k02', pid=flode_pid,
                                    rader=[anrop('c1', 'Read', rot + '/underlag/%s/BRIEF.md' % SLUG, t % 1), svar('c1', t % 2),
                                           anrop('c2', 'Edit', rot + '/kunder/%s/kandidater/k02/sajt/src/pages/index.astro' % SLUG, t % 3)]),
            'startar': self.session('forfina-k02', kandidat='k02', pid=flode_pid),
            'okant': self.session('forfina-k01', pid=annan_pid),
        }
        self.session('skiss-k01', start='2026-10-09T04:00:00Z', slut='2026-10-09T04:30:00Z', utfall='avslutad, kod 0')  # förra körningens
        with patch.object(nastlad, 'ar_session', side_effect=lambda pid: int(pid) == flode_pid):
            l = self.lage()
        self.assertEqual(l['ofullstandig'], [], l['ofullstandig'])
        s = {x['session_id']: x for x in l['sessioner'] if x.get('kalla') == 'ateljén'}
        self.assertEqual(set(s), set(sid.values()), 'bara den aktuella körningens sessioner')
        lagen = {namn: (s[i]['lage'], s[i]['lage_text']) for namn, i in sid.items()}
        self.assertEqual(lagen['avslutad'], ('avslutad', 'avslutad 2026-10-09T05:20:00Z'))
        self.assertEqual(lagen['stoppet'], ('avbruten', 'avbruten vid stoppet'))
        self.assertEqual(lagen['signal'][0], 'avbruten')
        self.assertIn('signal 9', lagen['signal'][1])
        self.assertEqual(lagen['dod'][0], 'avbruten')
        self.assertIn('processen lever inte', lagen['dod'][1])
        self.assertEqual(lagen['aktiv'][0], 'aktiv', lagen)
        self.assertEqual(lagen['verktyg'], ('verktyg', 'väntar på Edit'))
        self.assertEqual(lagen['startar'][0], 'startar', lagen)
        self.assertEqual(lagen['okant'][0], 'okant', lagen)
        self.assertIn('inte en session ur flödet', lagen['okant'][1])
        self.assertEqual(s[sid['verktyg']]['aktivitet']['pagaende'], ['Edit'])
        self.assertEqual([h['utfall'] for h in s[sid['verktyg']]['aktivitet']['handelser']], ['fil läst (omfång inte observerat)', 'pågår'])
        self.assertEqual(s[sid['signal']]['ansvar'], 'granskning')
        self.assertEqual(s[sid['aktiv']]['ansvar'], 'utforande')
        r = l['roller']
        self.assertIn(r['utforande']['lage'], ('aktiv', 'verktyg', 'startar'), r['utforande'])
        self.assertIn('3 lever', r['utforande']['lage_text'])
        self.assertEqual((r['granskning']['lage'], r['granskning']['sessioner']), ('avbruten', [sid['signal']]))
        self.assertEqual(r['arbetsledning']['lage'], 'vantar')

    def test_fel_i_svarsfilen_ger_avbruten_utan_resultatrad_i_transkriptet(self):
        # GR-20261009-arbetsyta-oberoende#A1: Claude Codes transkript har ingen result-rad; felet står i sessionens svarsfil
        t = '2026-10-09T05:1%d:00Z'
        rader = [anrop('e1', 'Read', str(self.u / 'BRIEF.md'), t % 1), svar('e1', t % 2)]
        fel = self.session('skiss-k02', kandidat='k02', slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0', rader=rader)
        ok_ = self.session('skiss-k01', slut='2026-10-09T05:21:00Z', utfall='avslutad, kod 0', rader=rader)
        plan = self.session('plan', kandidat=None, slut='2026-10-09T05:22:00Z', utfall='avslutad, kod 0')
        k = self.u / 'atelje' / 'kandidater'
        # svarsfilen bär sessionens id, som --output-format json skriver den (det verkliga provets svarsfiler)
        self.skriv(k / 'k02' / 'svar-skiss-k02.json', {'type': 'result', 'subtype': 'error_max_turns', 'is_error': True, 'num_turns': 400, 'session_id': fel})
        self.skriv(k / 'k01' / 'svar-skiss-k01.json', {'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 12, 'session_id': ok_})
        self.skriv(self.u / 'atelje' / 'svar-plan.json', {'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'session_id': plan})
        s = {x['session_id']: x for x in self.lage()['sessioner'] if x.get('kalla') == 'ateljén'}
        self.assertEqual((s[fel]['lage'], s[fel]['lage_text']), ('avbruten', 'avslutad med fel i sessionens svar'))
        self.assertEqual(s[ok_]['lage'], 'avslutad')
        self.assertEqual(s[plan]['lage'], 'avbruten', s[plan])
        # samma roll skriver om samma filnamn: en svarsfil från en senare session med fel dömer inte en tidigare
        self.skriv(self.u / 'atelje' / 'svar-plan.json', {'type': 'result', 'subtype': 'error_during_execution', 'is_error': True,
                                                          'session_id': '00000000-0000-4000-8000-000000000000'})
        s = {x['session_id']: x for x in self.lage()['sessioner'] if x.get('kalla') == 'ateljén'}
        self.assertEqual(s[plan]['lage'], 'avslutad', 'en annan sessions svarsfil får inte döma den här (GR-20261009-arbetsyta-oberoende, provskrivarens not 2)')

    # --- blindningen ---

    def test_blindningen_galler_pa_servervagen_och_hemligheter_maskeras(self):
        rot, t = str(self.root), '2026-10-09T05:1%d:00Z'
        dold = rot + '/underlag/%s/atelje/kandidater/k01/MARKOR-SOKVAG.md' % SLUG
        self.session('skiss-k01', slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0',
                     rader=[anrop('d1', 'Read', dold, t % 1), svar('d1', t % 2),
                            anrop('d2', 'Edit', rot + '/kunder/%s/kandidater/k01/sajt/src/pages/index.astro' % SLUG, t % 3), svar('d2', t % 4)])
        (self.u / 'atelje' / 'arbetare.log').write_text('steg skiss\nANTHROPIC token=abcdef123456\nnyckel: hemligtvarde99\n', encoding='utf-8')
        (self.u / 'ateljestarter').mkdir()
        (self.u / 'ateljestarter' / ('%s.log' % self.status['start_id'])).write_text('start mottagen\n', encoding='utf-8')
        l = self.lage()
        self.assertTrue(l['blind'])
        handelser = [h for x in l['sessioner'] for h in ((x.get('aktivitet') or {}).get('handelser') or [])]
        self.assertEqual(len(handelser), 2, l['sessioner'])
        self.assertTrue(all('fil' not in h for h in handelser), handelser)
        self.assertNotIn('MARKOR-SOKVAG', json.dumps(l, ensure_ascii=False))
        kl = arbetsyta.korningslogg(dash, SLUG)
        self.assertTrue(kl['blind'])
        self.assertEqual(len(kl['loggar']), 2, kl)
        self.assertTrue(all(x.get('dold') and x['rader'] == [] for x in kl['loggar']), kl)
        self.assertNotIn('abcdef123456', json.dumps(kl, ensure_ascii=False))
        if self.sajt is not None:
            filer = [f['fil'] for f in arbetsyta.kod(dash, SLUG, 'k01')['filer']]
            self.assertIn('kod/index.astro', filer)
            self.assertNotIn('DESIGN.md', filer)
            with self.assertRaises(ValueError):
                arbetsyta.kod(dash, SLUG, 'k01', 'DESIGN.md')
        # ägarens första val efter planen lyfter blindningen
        self.agarens_val()
        l = self.lage()
        self.assertFalse(l['blind'], l['ofullstandig'])
        handelser = [h for x in l['sessioner'] for h in ((x.get('aktivitet') or {}).get('handelser') or [])]
        self.assertEqual([h.get('fil') for h in handelser],
                         ['underlag/%s/atelje/kandidater/k01/MARKOR-SOKVAG.md' % SLUG, 'kunder/%s/kandidater/k01/sajt/src/pages/index.astro' % SLUG])
        kl = arbetsyta.korningslogg(dash, SLUG)
        self.assertFalse(kl['blind'])
        rader = [r for x in kl['loggar'] for r in x['rader']]
        self.assertTrue(all(not x.get('dold') for x in kl['loggar']), kl)
        self.assertIn('ANTHROPIC token=•••', rader)
        self.assertIn('nyckel: •••', rader)
        self.assertIn('start mottagen', rader)
        self.assertNotIn('abcdef123456', json.dumps(kl, ensure_ascii=False))
        self.assertNotIn('hemligtvarde99', json.dumps(kl, ensure_ascii=False))
        if self.sajt is None:
            self.skipTest(utan_sajt())
        k = arbetsyta.kod(dash, SLUG, 'k01', 'DESIGN.md')
        self.assertIn('DESIGN.md', [f['fil'] for f in k['filer']])
        self.assertEqual(k['fil']['text'], (kandidater.ksajt(SLUG, 'k01') / 'DESIGN.md').read_text(encoding='utf-8'))

    def test_en_arm_i_en_blind_jamforelse_visas_inte_pa_nagon_vag(self):
        # GR-20261009-arbetsyta-oberoende#B1: armen avslöjar inte sin ateljékörning (läget, strömmen, partnern, koden, loggen, ändringen)
        self.k02_fotograferad()
        sid = self.session('skiss-k01', slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0')
        self.skriv(self.u / 'ateljestarter' / 'testdata-start-0001.json', {'handling': 'om', 'tid': '2026-10-09T05:00:00Z', 'status': 'slut', 'slutkod': 0})
        (self.u / 'atelje' / 'arbetare.log').write_text('steg skiss\n', encoding='utf-8')
        fore = self.lage()  # utan jämförelsen syns körningen: proven nedan är inte tomma av sig själva
        self.assertTrue(fore['korning'] and fore['startjournal'] and fore['kandidater'] and sid in [x['session_id'] for x in fore['sessioner']])
        self.assertTrue(arbetsyta.korningslogg(dash, SLUG)['loggar'])
        for namn, ab in (('oavgjord', {'return_value': True}), ('trasig', {'side_effect': RuntimeError('jämförelsen kunde inte läsas')})):
            with self.subTest(jamforelse=namn), patch.object(dash, 'ab_oavgjord', **ab), patch.object(subprocess, 'run', ingen_editor):
                l = self.lage()
                self.assertTrue(l['ab_dold'] and l['blind'], l)
                self.assertEqual(l['korning'], {})
                for falt in ('sessioner', 'kandidater', 'startjournal', 'helbygge', 'overlamningar'):
                    self.assertEqual(l[falt], [], falt)
                self.assertTrue(l.get('dold'), 'läget säger varför det är tomt')
                text = json.dumps(l, ensure_ascii=False)
                for spar in (self.status['startad'], self.status['start_id'], sid, 'arbetare.log'):
                    self.assertNotIn(spar, text)
                if namn == 'trasig':
                    self.assertTrue(any('jämförelsen' in x for x in l['ofullstandig']), l['ofullstandig'])
                kl = arbetsyta.korningslogg(dash, SLUG)
                self.assertEqual(kl['loggar'], [])
                self.assertTrue(kl.get('dold'), kl)
                for kid in ('k01', 'k02'):
                    with self.assertRaises(ValueError):
                        arbetsyta.kod(dash, SLUG, kid)
                    with self.assertRaises(ValueError):
                        arbetsyta.oppna_i_editor(dash, SLUG, {'kandidat': kid, 'fil': 'kod/index.astro'})
                with self.assertRaises(Exception):  # oavgjord: ValueError; en jämförelse som inte går att läsa: dess fel, och inget skrivs
                    arbetsyta.skicka_andring(dash, SLUG, self.andring())
                self.assertEqual(self.domrader(), [])
        with patch.object(dash, 'ab_oavgjord', return_value=True):
            with self.assertRaises(ValueError):
                arbetsyta.skicka_andring(dash, SLUG, self.andring())

    def test_foreversionen_visas_forst_efter_agarens_forsta_val(self):
        # GR-20261009-arbetsyta-oberoende#B2: föreversionen före förbättringsrundan och diffen mot den håller sammanstall tillbaka
        self.k02_fotograferad(fore=True)
        k02 = next(x for x in self.lage()['kandidater'] if x['id'] == 'k02')
        self.assertEqual(k02['versioner'], [V_NU[:12]])
        self.assertEqual(arbetsyta.kod(dash, SLUG, 'k02')['versioner'], [V_NU[:12]])
        with self.assertRaises(ValueError):
            arbetsyta.kod(dash, SLUG, 'k02', mot=V_FORE[:12])
        with self.assertRaises(ValueError):
            arbetsyta.kod(dash, SLUG, 'k02', 'kod/index.astro', mot=V_FORE[:12])
        self.agarens_val()
        k02 = next(x for x in self.lage()['kandidater'] if x['id'] == 'k02')
        self.assertEqual(k02['versioner'], [V_FORE[:12], V_NU[:12]])
        k = arbetsyta.kod(dash, SLUG, 'k02', 'kod/index.astro', mot=V_FORE[:12])
        self.assertEqual((k['mot'], k['versioner']), (V_FORE[:12], [V_FORE[:12], V_NU[:12]]))
        self.assertIn('-<img src="x.jpg">', k['fil']['diff'])

    def test_maskeringen_tar_vanliga_tokenformer(self):
        # GR-20261009-arbetsyta-oberoende#A7
        for rad, hemligt in (('Authorization: Bearer abc12345678', 'abc12345678'), ('anrop med sk-ant-api03-ABCDEFGHIJ klart', 'ABCDEFGHIJ'),
                             ('GET https://x/?key=hemligt123 200', 'hemligt123'), ('lösenord: hunter2222', 'hunter2222'),
                             ('using sk-ant-api03-QQQQQQQQ for call', 'QQQQQQQQ'), ('Bearer eyJhbGciOiJIUzI1NiJ9.abc', 'eyJhbGciOiJIUzI1NiJ9')):
            m = arbetsyta.maskera(rad)
            self.assertNotIn(hemligt, m, rad)
            self.assertIn('•••', m, rad)
        for vanlig in ('steg skiss klar: 2 kandidater, 12 bilder', 'kandidaten k01 fotograferad 2026-10-09T05:30:00Z'):
            self.assertEqual(arbetsyta.maskera(vanlig), vanlig)

    # --- koden ---

    def test_koden_visar_diffen_och_foljer_inga_lankar(self):
        if self.sajt is None:
            self.skipTest(utan_sajt())
        k = arbetsyta.kod(dash, SLUG, 'k01', 'kod/index.astro')
        v12 = kandidater.las_status(SLUG, 'k01')['version'][:12]
        self.assertEqual((k['mot'], k['versioner'], k['fotograferad']), (v12, [v12], v12))
        self.assertIn('+' + TILLAGG, k['fil']['diff'], k['fil']['diff'][:20])
        self.assertFalse([x for x in k['fil']['diff'] if x.startswith('-') and not x.startswith('---')], 'inget togs bort')
        f = {x['fil']: x for x in k['filer']}
        self.assertTrue(f['kod/index.astro']['andrad'])
        self.assertFalse([x for x, y in f.items() if y['andrad'] and x != 'kod/index.astro'], 'bara startsidan ändrades efter fotograferingen')
        self.assertFalse([x for x in f if x.split('/')[-1] in kandidater.MALLSIDOR], 'mallens sidor hör inte till kandidatens kod')
        # länkar ut ur projektet: en fil i sidorna, en i src och en katalog
        sajt = kandidater.ksajt(SLUG, 'k01')
        (self.root / 'utanfor').mkdir()
        (self.root / 'utanfor' / 'hemlig.astro').write_text('MARKOR-UTANFOR\n', encoding='utf-8')
        os.symlink(self.root / 'utanfor' / 'hemlig.astro', sajt / 'src' / 'pages' / 'lank.astro')
        os.symlink(self.root / 'utanfor' / 'hemlig.astro', sajt / 'src' / 'lank.css')
        os.symlink(self.root / 'utanfor', sajt / 'src' / 'lankkatalog')
        k = arbetsyta.kod(dash, SLUG, 'k01')
        filer = [x['fil'] for x in k['filer']]
        for lank in ('kod/lank.astro', 'kod-src/lank.css', 'kod-src/lankkatalog/hemlig.astro'):
            self.assertNotIn(lank, filer)
            with self.assertRaises(ValueError, msg=lank):
                arbetsyta.kod(dash, SLUG, 'k01', lank)
        self.assertNotIn('MARKOR-UTANFOR', json.dumps(k, ensure_ascii=False))
        for fel in ('../x', '/etc/passwd', 'kod/../../../../etc/passwd', 'kod/index.astro\x00'):
            with self.assertRaises(ValueError, msg=fel):
                arbetsyta.kod(dash, SLUG, 'k01', fel)
        for kid in ('k99', '../k01', None):
            with self.assertRaises(ValueError, msg=kid):
                arbetsyta.kod(dash, SLUG, kid)

    def test_en_lank_i_stallet_for_kandidatens_projekt_foljs_inte(self):
        # GR-20261009-arbetsyta-oberoende#A6: kandidatens katalog eller sajt som byts mot en länk ut ur projektet
        ute = self.root / 'utanfor'
        (ute / 'sajt' / 'src' / 'pages').mkdir(parents=True)
        (ute / 'sajt' / 'src' / 'pages' / 'index.astro').write_text('MARKOR-UTANFOR\n', encoding='utf-8')
        (ute / 'sajt' / 'DESIGN.md').write_text('MARKOR-UTANFOR\n', encoding='utf-8')
        # k02:s hela katalog under kunder/ är en länk
        (self.k / 'kandidater').mkdir(parents=True, exist_ok=True)
        os.symlink(ute, self.k / 'kandidater' / 'k02')
        # k01:s sajt är en länk (den byggda sajten flyttas ut när den finns)
        sajt = kandidater.ksajt(SLUG, 'k01')
        if sajt.exists():
            shutil.move(str(sajt), str(ute / 'k01-sajt'))
            (ute / 'k01-sajt' / 'src' / 'pages' / 'index.astro').write_text('MARKOR-UTANFOR\n', encoding='utf-8')
            os.symlink(ute / 'k01-sajt', sajt)
        else:
            sajt.parent.mkdir(parents=True)
            os.symlink(ute / 'sajt', sajt)
        self.agarens_val()  # inte blint: inget hålls tillbaka av blindningen, bara av länken
        with patch.object(subprocess, 'run', ingen_editor):
            for kid in ('k01', 'k02'):
                with self.assertRaises(ValueError, msg=kid):
                    arbetsyta.kod(dash, SLUG, kid)
                with self.assertRaises(ValueError, msg=kid):
                    arbetsyta.kod(dash, SLUG, kid, 'kod/index.astro')
                with self.assertRaises(ValueError, msg=kid):
                    arbetsyta.oppna_i_editor(dash, SLUG, {'kandidat': kid, 'fil': 'kod/index.astro'})
        vanlig = self.k / 'vanlig.astro'
        vanlig.write_text('x\n', encoding='utf-8')
        os.symlink(ute / 'sajt' / 'DESIGN.md', self.k / 'lank.astro')
        self.assertTrue(arbetsyta._inom(self.k, vanlig))
        self.assertFalse(arbetsyta._inom(self.k, self.k / 'lank.astro'))
        self.assertFalse(arbetsyta._inom(self.k, self.k / 'kandidater' / 'k02' / 'sajt' / 'src' / 'pages' / 'index.astro'))
        self.assertFalse(arbetsyta._inom(self.k, ute / 'sajt' / 'DESIGN.md'))

    # --- ägarens ändring ---

    def test_andringen_binds_till_korning_version_och_steg(self):
        self.k02_fotograferad()
        bas = self.andring()
        with self.assertRaises(arbetsyta.Inaktuell) as e:
            arbetsyta.skicka_andring(dash, SLUG, dict(bas, version='0' * 64))
        self.assertIn('ny version', str(e.exception))
        with self.assertRaises(arbetsyta.Inaktuell) as e:
            arbetsyta.skicka_andring(dash, SLUG, dict(bas, korning='2026-10-01T00:00:00Z'))
        self.assertIn('körningen har bytts', str(e.exception))
        self.skriv_status(steg='forfina')
        with self.assertRaises(arbetsyta.Inaktuell) as e:
            arbetsyta.skicka_andring(dash, SLUG, bas)
        self.assertIn('väntar inte på ditt beslut', str(e.exception))
        self.skriv_status(steg='klar_for_bedomning')
        for fel in ({}, dict(bas, andring_id='x'), dict(bas, text=' '), dict(bas, beslut='godkand'), dict(bas, kandidat='k99')):
            with self.assertRaises(ValueError):
                arbetsyta.skicka_andring(dash, SLUG, fel)
        self.assertEqual(self.domrader(), [], 'inget nekat skrevs i domloggen')
        r = arbetsyta.skicka_andring(dash, SLUG, bas)
        self.assertTrue(r['ok'])
        self.assertFalse(r['upprepat'])
        rader = self.domrader()
        self.assertEqual(len(rader), 1, rader)
        d = rader[-1]
        self.assertEqual((d['kalla'], d['beslut']), ('ägaren', 'valj'))
        self.assertEqual({k: d['arbetsyta'].get(k) for k in ('andring_id', 'kandidat', 'version', 'korning')},
                         {'andring_id': 'andring-prov-0001', 'kandidat': 'k02', 'version': V_NU[:12], 'korning': self.status['startad']})
        self.assertEqual([(x['id'], x['version']) for x in d['kandidater']], [('k02', V_NU)])
        r = arbetsyta.skicka_andring(dash, SLUG, bas)
        self.assertTrue(r['upprepat'])
        self.assertEqual(len(self.domrader()), 1, 'samma ändrings-id ger samma rad')
        l = self.lage()
        self.assertEqual(l['ofullstandig'], [], l['ofullstandig'])
        self.assertFalse(l['blind'])
        self.assertIn('valda', [h['id'] for h in l['handlingar']], l['handlingar'])
        self.assertEqual(len(l['overlamningar']), 1, l['overlamningar'])
        o = l['overlamningar'][0]
        self.assertEqual((o['id'], o['kandidat'], o['version'], o['avsandare']), ('andring-prov-0001', 'k02', V_NU[:12], 'ägaren'))
        self.assertEqual(set(o['steg']), {'skickad'}, 'inget steg efter skickad sätts av arbetsytan själv')

    def test_andringen_kraver_korningen_och_hela_versionen(self):
        # GR-20261009-arbetsyta-oberoende#B3: utan körning eller hel version finns inget att stämma av mot; ett formfel, inte Inaktuell
        self.k02_fotograferad()
        utan_version = self.andring()
        del utan_version['version']
        for namn, data in (('utan version', utan_version), ('kort version', self.andring(version=V_NU[:12])),
                           ('utan körning', self.andring(korning='')), ('version med versaler', self.andring(version=V_NU.upper()))):
            with self.subTest(namn):
                with self.assertRaises(ValueError) as e:
                    arbetsyta.skicka_andring(dash, SLUG, data)
                self.assertNotIsInstance(e.exception, arbetsyta.Inaktuell)
        self.assertEqual(self.domrader(), [], 'inget skrevs')

    def test_andringen_ar_agarens_text_och_markering_inte_det_agaren_gillade(self):
        # GR-20261009-arbetsyta-oberoende#B4: ändringen når skaparen som ändring med sin markering, aldrig under "gillade"
        self.k02_fotograferad()
        text = 'Rubriken ska bli större och bära ortnamnet.'
        mark = {'vy': 'Arbetsyta', 'sida': '/', 'del': 'första vyn', 'fil': 'kod/index.astro'}
        arbetsyta.skicka_andring(dash, SLUG, self.andring(andring_id='andring-b4-0001', text=text, **mark))
        d = self.domrader()[-1]
        self.assertNotIn('delar', d)
        self.assertEqual(d['text'], text)
        self.assertEqual({k: d['arbetsyta'].get(k) for k in mark}, mark)
        rader = '\n'.join(skapande.kritikrader(SLUG, underlag=self.root / 'underlag', aktuella=True))
        self.assertIn('ändringen gäller (ägarens markering i arbetsytan', rader)
        self.assertIn('  > ' + text, rader)
        self.assertNotIn('ägaren gillade', rader)
        self.assertEqual(kandidater.delar_rader(SLUG, d, 'k02'), [], 'förfiningens "Det ägaren gillade" är tomt')

    # --- partnern ---

    def test_partnern_en_session_per_kund_och_ett_meddelande_i_taget(self):
        falsk, ps = self.falsk_partner()
        fil = self.u / 'arbetsyta' / 'PARTNER.json'
        m1 = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-0001', 'text': 'Var står vi?', 'avsikt': 'fraga',
                                          'kontext': {'kandidat': 'k01', 'vy': 'telefon', 'okant_falt': 'x'}})
        d = self.las(fil)
        sid = d['session_id']
        self.assertRegex(sid, partner.SESSION)
        self.assertEqual(len(falsk.anrop), 1)
        a = falsk.anrop[0]
        self.assertEqual(a[a.index('--session-id') + 1], sid)
        self.assertNotIn('--resume', a)
        self.assertEqual(m1['lage'], 'svarat')
        self.assertEqual(d['meddelanden'][0]['kontext'], {'kandidat': 'k01', 'vy': 'telefon'})
        vanta_pa_vakter()
        prompt = falsk.processer[0].prompt
        self.assertIn('TESTDATA', prompt)
        self.assertIn('Blind: ja', prompt)
        self.assertIn('Var står vi?', prompt)
        for dolt in ('Testdata: verkstaden i arbete', 'Testdata k01'):
            self.assertNotIn(dolt, prompt, 'partnerns läge är blindat som vyns')
        self.assertEqual(partner.lage(dash, SLUG)['lage'], 'avslutad')
        # nästa meddelande fortsätter samma session
        m2 = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-0002', 'text': 'Och sedan?'})
        self.assertEqual(len(falsk.anrop), 2)
        a = falsk.anrop[1]
        self.assertEqual(a[a.index('--resume') + 1], sid)
        self.assertNotIn('--session-id', a)
        self.assertEqual(self.las(fil)['session_id'], sid)
        self.assertFalse(m2.get('upprepat'))
        vanta_pa_vakter()
        # samma meddelande-id ger samma post och ingen ny process
        m1b = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-0001', 'text': 'Var står vi?'})
        self.assertTrue(m1b['upprepat'])
        self.assertEqual(len(falsk.anrop), 2)
        self.assertEqual(len(self.las(fil)['meddelanden']), 2)
        # en tur som pågår utan svar: nästa meddelande nekas
        falsk.svara, falsk.sov = False, '60'
        m3 = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-0003', 'text': 'En fråga till.'})
        self.assertEqual(m3['lage'], 'arbetar')
        self.assertEqual(partner.lage(dash, SLUG)['lage'], 'aktiv')
        with self.assertRaises(partner.Upptagen):
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-0004', 'text': 'Hallå?'})
        self.assertEqual(len(falsk.anrop), 3)
        stoppa(falsk.processer[-1].p)
        vanta_pa_vakter()
        self.assertEqual(partner.lage(dash, SLUG)['lage'], 'avbruten')
        self.assertTrue(self.las(fil)['meddelanden'][-1].get('slut'))
        # en interaktiv claude --resume i en terminal räknas, ett skal som nämner id:t gör det inte
        ps.return_value = '123 /bin/zsh -c echo claude --resume %s\n124 /opt/homebrew/bin/claude --resume %s\n' % (sid, sid)
        self.assertEqual([x['pid'] for x in partner.andra_processer(sid)], [124])
        self.assertEqual(partner.andra_processer(sid, utom={124}), [])
        self.assertEqual(partner.andra_processer('inte-ett-id'), [])
        with self.assertRaises(partner.Upptagen):
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-0005', 'text': 'Är du där?'})
        self.assertEqual(len(falsk.anrop), 3)
        # tillåtelselistan och argumenten
        regler = partner.tillatet(dash, SLUG)
        self.assertTrue(all(r.startswith('Read(//') for r in regler), regler)
        self.assertFalse([r for r in regler if '/atelje' in r or '/kunder/' in r], regler)
        self.assertIn('Read(/%s/underlag/%s/BRIEF.md)' % (self.root, SLUG), regler)
        self.assertIn('Read(/%s/kunskap/**)' % self.root, regler)
        args = partner.args(dash, SLUG, sid, True, partner.profil())
        for par in (('--permission-mode', 'dontAsk'), ('--tools', 'Read'), ('--session-id', sid)):
            self.assertEqual(args[args.index(par[0]) + 1], par[1], args)
        self.assertIn('--strict-mcp-config', args)
        self.assertEqual(args[args.index('--allowedTools') + 1:args.index('--append-system-prompt')], regler)

    # --- partnerns blindning (ägarens kontrollpunkter 2026-10-09: server.py:2950 och partner.py:296 på b20ae3a) ---

    def test_partnerns_egna_vagar_sparras_for_en_arm_i_en_blind_jamforelse(self):
        # partnerns GET och POST gick förbi A/B-spärren som arbetsytans samlade läsväg har
        sid = str(uuid.uuid4())
        self.skriv(self.u / 'arbetsyta' / 'PARTNER.json', {
            'schema': 'partner/1', 'slug': SLUG, 'session_id': sid, 'skapad': '2026-10-09T05:00:00Z', 'korning': self.status['startad'],
            'blind_vid_start': True, 'meddelanden': [{'id': 'meddelande-ab-0001', 'tid': '2026-10-09T05:01:00Z', 'avsikt': 'fraga', 'text': 'Vilken arm är detta?',
                             'svarsfil': 'svar-meddelande-ab-0001.json', 'pid': None}]})
        self.skriv(self.u / 'arbetsyta' / 'partner' / 'svar-meddelande-ab-0001.json',
                   {'type': 'result', 'is_error': False, 'result': 'Detta är arm B, metodvarianten.', 'session_id': sid})
        falsk, _ps = self.falsk_partner()
        port, host, anropa = self.server()
        fore = json.dumps(partner.lage(dash, SLUG, samtal=True), ensure_ascii=False)
        self.assertIn('arm B', fore, 'utan jämförelsen syns samtalet: provet nedan är inte tomt av sig självt')
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'}
        for namn, ab in (('oavgjord', {'return_value': True}), ('trasig', {'side_effect': RuntimeError('jämförelsen kunde inte läsas')})):
            with self.subTest(jamforelse=namn), patch.object(dash, 'ab_oavgjord', **ab):
                l = partner.lage(dash, SLUG, samtal=True)
                self.assertTrue(l.get('dold'), l)
                status, _r, kropp = anropa('GET', '/api/arbetsyta/%s/partner' % SLUG)
                self.assertEqual(status, 200)
                for text in (json.dumps(l, ensure_ascii=False), kropp.decode()):
                    for spar in (sid, 'arm B', 'Vilken arm', 'meddelande-ab-0001'):
                        self.assertNotIn(spar, text)
                with self.assertRaises(Exception):
                    partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-ab-0002', 'text': 'Och nu?'})
                with self.assertRaises(Exception):  # samma id som det dolda meddelandet ger inte heller dess svar
                    partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-ab-0001', 'text': 'Vilken arm är detta?'})
                status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/partner' % SLUG, {'meddelande_id': 'meddelande-ab-0003', 'text': 'Och nu?'}, skriv)
                self.assertEqual(status, 409, kropp)
                self.assertNotIn('arm B', kropp.decode())
        self.assertEqual(falsk.anrop, [], 'ingen partnertur startades för armen')
        self.assertEqual([m['id'] for m in self.las(self.u / 'arbetsyta' / 'PARTNER.json')['meddelanden']], ['meddelande-ab-0001'])

    def test_en_ny_blind_korning_far_en_ny_partnersession_utan_gammalt_minne(self):
        # partnern återupptog samma session (--resume) i varje körning: en ny blind körning ärvde samtalet där tidigare
        # bedömningar stod; att dölja det senaste meddelandet rensar inte sessionens minne
        falsk, _ps = self.falsk_partner()
        fil = self.u / 'arbetsyta' / 'PARTNER.json'
        seende, blind = (False, False), (True, False)
        with patch.object(arbetsyta, 'dold', return_value=seende):
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k1-0001', 'text': 'Vilken kandidat bedömdes bäst?'})
            vanta_pa_vakter()
            s1 = self.las(fil)['session_id']
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k1-0002', 'text': 'Och varför?'})
            vanta_pa_vakter()
            a = falsk.anrop[-1]
            self.assertEqual(a[a.index('--resume') + 1], s1, 'samma körning och samma blindläge: samma session')
        self.skriv_status(startad='2026-10-09T08:00:00Z', start_id='testdata-start-0002')
        with patch.object(arbetsyta, 'dold', return_value=blind):
            l = partner.lage(dash, SLUG, samtal=True)
            self.assertEqual(l['meddelanden'], [], 'den nya blinda körningen visar inte det förra samtalet')
            m = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k2-0001', 'text': 'Var står vi?'})
            vanta_pa_vakter()
            a = falsk.anrop[-1]
            self.assertIn('--session-id', a)
            self.assertNotIn('--resume', a)
            s2 = a[a.index('--session-id') + 1]
            self.assertNotEqual(s2, s1, 'en ny blind körning startar en ny session')
            self.assertEqual(self.las(fil)['session_id'], s2)
            l = partner.lage(dash, SLUG, samtal=True)
            text = json.dumps([l, m], ensure_ascii=False)
            for spar in (s1, 'Vilken kandidat bedömdes bäst', 'meddelande-k1-0001', 'meddelande-k1-0002'):
                self.assertNotIn(spar, text)
            self.assertEqual([x['id'] for x in l['meddelanden']], ['meddelande-k2-0001'])
            self.assertEqual(l.get('tidigare'), 1, 'det förra samtalet räknas men visas inte')
            # ett gammalt meddelande-id (en flik från förra körningen) startar ingen tur och ger inget av det gamla svaret
            n = len(falsk.anrop)
            gammal = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k1-0001', 'text': 'Vilken kandidat bedömdes bäst?'})
            self.assertEqual(len(falsk.anrop), n)
            self.assertNotIn('Svar (testdata)', json.dumps(gammal, ensure_ascii=False))
            self.assertTrue(gammal.get('upprepat'))
            # nästa meddelande i samma blinda körning fortsätter den nya sessionen
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k2-0002', 'text': 'Och sedan?'})
            vanta_pa_vakter()
            a = falsk.anrop[-1]
            self.assertEqual(a[a.index('--resume') + 1], s2)
        # efter ägarens val i körningen: den blinda sessionen har bara sett blint läge och får fortsätta; historiken syns
        with patch.object(arbetsyta, 'dold', return_value=seende):
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k2-0003', 'text': 'Nu har jag valt.'})
            vanta_pa_vakter()
            a = falsk.anrop[-1]
            self.assertEqual(a[a.index('--resume') + 1], s2)
            l = partner.lage(dash, SLUG, samtal=True)
            self.assertEqual([x['id'] for x in l['tidigare_samtal'][0]['meddelanden']], ['meddelande-k1-0001', 'meddelande-k1-0002'])
        # samma körning men blind igen (en ny plan): sessionen som sett seende läge återupptas inte
        with patch.object(arbetsyta, 'dold', return_value=blind):
            d = self.las(fil)
            d['blind_vid_start'] = False  # som om sessionen startats seende
            self.skriv(fil, d)
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-k2-0004', 'text': 'Ny plan?'})
            vanta_pa_vakter()
            a = falsk.anrop[-1]
            self.assertIn('--session-id', a)
            self.assertNotIn(a[a.index('--session-id') + 1], (s1, s2))

    # --- samverkan: meddelanden, extern granskare, mandat, paus, historik, följdfrågor och beslut (2026-10-09) ---

    def granskarsession(self, ansvar='granskning', kid='k01'):
        """En granskande session med löpare (som lopare.Lopare skriver läget), utan process: avsändare i bussen."""
        sid = str(uuid.uuid4())
        meddelanden._skriv(meddelanden.styrfil(SLUG, sid), {'session_id': sid, 'roll': 'skisskritik-%s' % kid, 'ansvar': ansvar, 'kandidat': kid,
                                                            'blind': False, 'korning': meddelanden.korning(SLUG), 'pid': os.getpid(),
                                                            'lopare_pid': os.getpid(), 'slut': None, 'lage': 'arbetar'})
        return {'typ': 'session', 'session_id': sid}

    def test_agarens_meddelanden_och_agenternas_text_blindas_fore_valet(self):
        if self.sajt is None:  # kandidatens fotograferade version kommer ur mallsajten (fixturen)
            self.skipTest(utan_sajt())
        port, host, anropa = self.server()
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'}
        mot = {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': 'k01'}
        data = {'id': 'agare-http-0001', 'syfte': 'fraga', 'text': 'Hur ser rubriken ut i mobil?', 'mottagare': mot, 'korning': self.status['startad']}
        self.assertEqual(anropa('POST', '/api/arbetsyta/%s/meddelande' % SLUG, data, {'Origin': 'http://' + host})[0], 403)
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/meddelande' % SLUG, data, skriv)
        self.assertEqual(status, 200, kropp)
        m = json.loads(kropp)
        self.assertEqual((m['avsandare']['typ'], m['lage'], m['upprepat']), ('agare', 'sparat', False))
        self.assertTrue(json.loads(anropa('POST', '/api/arbetsyta/%s/meddelande' % SLUG, data, skriv)[2])['upprepat'], 'dubbelklick: samma meddelande')
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/meddelande' % SLUG, dict(data, id='agare-http-0002', korning='2026-10-01T00:00:00Z'), skriv)
        self.assertEqual((status, json.loads(kropp)['slag']), (409, 'Inaktuell'))
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/meddelande' % SLUG, dict(data, id='agare-http-0003', syfte='agarbeslut'), skriv)
        self.assertEqual(status, 400, 'ett ägarbeslut skickas inte som meddelande')
        g = self.granskarsession()
        fynd = meddelanden.skapa(SLUG, g, {'typ': 'agare'}, 'granskningsfynd', 'Rubriken bryts på fyra rader.', kandidat='k01', belagg=['vy-390-forsta'])
        l = json.loads(anropa('GET', '/api/arbetsyta/%s/meddelanden' % SLUG)[2])
        self.assertTrue(l['blind'])
        f = [x for x in l['meddelanden'] if x['id'] == fynd['id']][0]
        self.assertEqual((f['text'], f['belagg'], f['agent']), (samverkan.DOLT, [], True))
        self.assertNotIn('fyra rader', json.dumps(l, ensure_ascii=False))
        self.assertNotIn('roll', f['avsandare'], 'rollen döljs före valet, som i sessionskorten')
        self.assertIn(fynd['id'], l['oppna'])
        self.assertEqual([x['text'] for x in l['meddelanden'] if x['id'] == 'agare-http-0001'], ['Hur ser rubriken ut i mobil?'], 'ägarens egna ord syns')
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/meddelande/%s/beslut' % (SLUG, fynd['id']), {'val': 'godta'}, skriv)
        self.assertEqual(status, 409, 'beslut över agenternas förslag först efter valet')
        self.agarens_val()
        l = json.loads(anropa('GET', '/api/arbetsyta/%s/meddelanden' % SLUG)[2])
        self.assertFalse(l['blind'])
        self.assertEqual([x['text'] for x in l['meddelanden'] if x['id'] == fynd['id']], ['Rubriken bryts på fyra rader.'])
        v1 = kandidater.las_status(SLUG, 'k01')['version']
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/meddelande/%s/beslut' % (SLUG, fynd['id']),
                                   {'val': 'godta', 'version': v1, 'korning': self.status['startad'], 'nytt_id': 'agare-godta-0001'}, skriv)
        self.assertEqual(status, 200, kropp)
        ny = meddelanden.hamta(SLUG, 'agare-godta-0001')
        self.assertEqual((ny['avsandare']['typ'], ny['syfte'], ny['svar_pa'], ny['mottagare']['kandidat']), ('agare', 'andringsinstruktion', fynd['id'], 'k01'))
        self.assertEqual(meddelanden.hamta(SLUG, fynd['id'])['beslut']['val'], 'godta')
        with patch.object(dash, 'ab_oavgjord', return_value=True):
            l = json.loads(anropa('GET', '/api/arbetsyta/%s/meddelanden' % SLUG)[2])
            self.assertEqual((l.get('dold'), l['meddelanden']), (True, []))
            self.assertEqual(anropa('POST', '/api/arbetsyta/%s/meddelande' % SLUG, dict(data, id='agare-http-0004'), skriv)[0], 409)

    def test_den_externa_granskarens_vag_med_egen_nyckel_och_mandat(self):
        if self.sajt is None:  # kandidatens fotograferade version kommer ur mallsajten (fixturen)
            self.skipTest(utan_sajt())
        nycklar = self.root / 'granskarnycklar'
        nycklar.mkdir()
        (nycklar / 'codex.nyckel').write_text('granskar-provnyckel-0123456789\n')
        self.stack.enter_context(patch.dict(os.environ, {'NWP_GRANSKARE_NYCKLAR': str(nycklar)}))
        port, host, anropa = self.server()
        b = {'Authorization': 'Bearer granskar-provnyckel-0123456789'}
        bas = '/api/extern/%s' % SLUG
        self.assertEqual(anropa('GET', bas + '/underlag')[0], 401)
        self.assertEqual(anropa('GET', bas + '/underlag', huvud={'Authorization': 'Bearer fel'})[0], 401)
        self.assertEqual(anropa('GET', bas + '/underlag', huvud=dict(b, Origin='http://' + host))[0], 403)
        self.assertEqual(anropa('GET', bas + '/underlag', huvud=dict(b, **{'Sec-Fetch-Site': 'same-origin'}))[0], 403)
        self.assertEqual(anropa('GET', '/api/extern/okand-kund/underlag', huvud=b)[0], 404)
        status, _r, kropp = anropa('GET', bas + '/underlag', huvud=b)
        u = json.loads(kropp)
        self.assertEqual((status, u['granskare'], u['blind']), (200, 'codex', True))
        self.assertIn('k01', [k['id'] for k in u['kandidater']])
        for dolt in ('Testdata k01', 'ägaren'):
            self.assertNotIn('"%s"' % dolt, kropp.decode())
        bild = 'underlag/%s/atelje/kandidater/k01/bilder/start/vy-390-forsta.png' % SLUG
        status, r, kropp = anropa('GET', bas + '/bild?fil=' + bild, huvud=b)
        self.assertEqual((status, r.getheader('Content-Type'), kropp), (200, 'image/png', PNG))
        for fel in ('underlag/%s/arbetsyta/PARTNER.json' % SLUG, '../../etc/passwd', 'underlag/%s/DESIGNDOMAR.jsonl' % SLUG):
            self.assertEqual(anropa('GET', bas + '/bild?fil=' + fel, huvud=b)[0], 400, fel)
        v1 = kandidater.las_status(SLUG, 'k01')['version']
        fynd = {'syfte': 'granskningsfynd', 'kandidat': 'k01', 'version': v1, 'text': 'Kontrasten i rubriken är 3,1:1.'}
        self.assertEqual(anropa('POST', bas + '/fynd', fynd, b)[0], 400, 'fynd utan belägg')
        status, _r, kropp = anropa('POST', bas + '/fynd', dict(fynd, belagg=['vy-1440-forsta: rubriken #9aa mot #fff']), b)
        self.assertEqual(status, 200, kropp)
        mid = json.loads(kropp)['id']
        self.assertEqual(meddelanden.hamta(SLUG, mid)['avsandare'], {'typ': 'extern', 'namn': 'codex'})
        self.assertEqual(anropa('POST', bas + '/fynd', dict(fynd, belagg=['x']), dict(b, Origin='http://' + host))[0], 403)
        ratt = {'syfte': 'andringsinstruktion', 'till': 'utforande', 'kandidat': 'k01', 'version': v1, 'text': 'Mörka rubriken till minst 4,5:1.'}
        self.assertEqual(anropa('POST', bas + '/fynd', ratt, b)[0], 409, 'ingen rättelse utan ägarens mandat')
        self.assertEqual(anropa('POST', bas + '/fynd', {'syfte': 'agarbeslut', 'text': 'Godkänt.'}, b)[0], 409)
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'}
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/mandat' % SLUG, {'id': 'mandat-codex-0001', 'kandidat': 'k01', 'granskare': {'typ': 'extern', 'namn': 'codex'},
                                                                             'omfattning': 'kontrast och läsbarhet i rubriken', 'korning': self.status['startad']}, skriv)
        self.assertEqual(status, 200, kropp)
        self.assertEqual(anropa('POST', '/api/arbetsyta/%s/mandat' % SLUG, {'id': 'mandat-codex-0002', 'kandidat': 'k01', 'granskare': {'typ': 'extern', 'namn': 'codex'},
                                                                          'omfattning': 'x'}, b)[0], 403, 'granskaren ger sig inte själv mandat')
        status, _r, kropp = anropa('POST', bas + '/fynd', ratt, b)
        self.assertEqual(status, 200, kropp)
        r_ = meddelanden.hamta(SLUG, json.loads(kropp)['id'])
        self.assertEqual((r_['mandat']['id'], r_['mottagare']), ('mandat-codex-0001', {'typ': 'adress', 'ansvar': 'utforande', 'kandidat': 'k01'}))
        self.assertIn('kontrast och läsbarhet', meddelanden.ramtext(r_))
        a = json.loads(anropa('GET', bas + '/aterkoppling', huvud=b)[2])['aterkoppling']
        self.assertEqual({x['id'] for x in a if x.get('eget')}, {mid, r_['id']})
        # kommandoradsverktyget (kontroller/extern_granskare.py): paketet, schemat och postningen med samma nyckel
        paket = self.root / 'granskningspaket'
        u_ = extern_granskare.paket('http://' + host, 'codex', SLUG, paket)
        self.assertEqual((u_['mandat'], sorted(p_.name for p_ in paket.iterdir())), (1, ['AGENTS.md', 'bilder', 'fynd-schema.json', 'underlag.json']))
        self.assertEqual((paket / 'bilder' / 'k01' / '390.png').read_bytes(), PNG)
        self.assertNotIn('granskar-provnyckel', ''.join(p_.read_text(errors='replace') for p_ in paket.rglob('*') if p_.is_file() and p_.suffix != '.png'))
        svar_ = self.root / 'fynd.json'
        svar_.write_text(json.dumps({'fynd': [dict(fynd, till='agare', belagg=['390.png: rubriken bryts på fyra rader'], text='Rubriken bryts på fyra rader i 390 px.'),
                                              dict(fynd, till='agare', belagg=[], text='Utan belägg.')]}), encoding='utf-8')
        ut_ = extern_granskare.posta('http://' + host, 'codex', SLUG, svar_)
        self.assertEqual([x['ok'] for x in ut_], [True, False], ut_)
        self.assertTrue(extern_granskare.posta('http://' + host, 'codex', SLUG, svar_)[0]['upprepat'], 'samma fynd igen: samma meddelande')
        with patch.object(dash, 'ab_oavgjord', return_value=True):
            self.assertEqual(anropa('GET', bas + '/underlag', huvud=b)[0], 409)
            self.assertEqual(anropa('POST', bas + '/fynd', dict(fynd, belagg=['y']), b)[0], 409)

    def test_paus_via_arbetsytan_med_omfattning(self):
        port, host, anropa = self.server()
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'}
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/paus' % SLUG, {'omfattning': 'projekt', 'korning': self.status['startad']}, skriv)
        self.assertEqual(status, 200, kropp)
        p = json.loads(kropp)['styrning']['projekt']
        self.assertEqual(p['lage'], 'pausad', 'inga sessioner arbetar: pausen gäller direkt')
        # arbetarens eget steg utanför sessionerna (här en sleep under arbetaren) pausas inte men redovisas
        arb = ORIG_POPEN(['/bin/sh', '-c', 'sleep 60 & wait'], stdin=subprocess.DEVNULL, start_new_session=True)
        self.addCleanup(lambda: (os.killpg(arb.pid, 9), arb.wait()))
        self.skriv_status(pid=arb.pid, steg='forfina')
        tj = []
        for _ in range(50):
            tj = json.loads(anropa('GET', '/api/arbetsyta/%s/meddelanden' % SLUG)[2])['styrning']['projekt']['tjanster']
            if tj:
                break
            time.sleep(0.1)
        self.assertTrue(any('sleep 60' in x['kommando'] for x in tj), tj)
        self.assertTrue(meddelanden.paus_galler(SLUG))
        self.assertEqual(anropa('POST', '/api/arbetsyta/%s/paus' % SLUG, {'omfattning': 'session', 'session_id': str(uuid.uuid4())}, skriv)[0], 400,
                         'en session utan löpare kan inte pausas')
        self.assertEqual(anropa('POST', '/api/arbetsyta/%s/paus' % SLUG, {'omfattning': 'projekt', 'korning': '2026-10-01T00:00:00Z'}, skriv)[0], 409)
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/paus' % SLUG, {'omfattning': 'projekt', 'aterta': True}, skriv)
        self.assertEqual((status, json.loads(kropp)['styrning']['projekt']), (200, None))
        self.assertIsNone(meddelanden.paus_galler(SLUG))

    def test_historik_och_foljdfraga_stangda_fore_valet_och_skrivskyddade_efter(self):
        if self.sajt is None:  # kandidatens fotograferade version kommer ur mallsajten (fixturen)
            self.skipTest(utan_sajt())
        rader = [{'type': 'user', 'timestamp': '2026-10-09T05:10:00Z', 'message': {'role': 'user', 'content': 'Uppgiften: skissa startsidan.'}},
                 {'type': 'assistant', 'timestamp': '2026-10-09T05:11:00Z', 'message': {'content': [
                     {'type': 'text', 'text': 'Jag väljer en mörk rubrik. Nyckeln sk-ant-api03-ABCDEFGHIJ syns inte.'},
                     {'type': 'tool_use', 'id': 't1', 'name': 'Edit', 'input': {'file_path': 'x'}}]}}]
        sid = self.session('skiss-k01', rader=rader, slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0')
        port, host, anropa = self.server()
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'}
        self.assertEqual(anropa('GET', '/api/arbetsyta/%s/historik/%s' % (SLUG, sid))[0], 409, 'historiken visas efter valet')
        fraga = {'id': 'gren-prov-0001', 'session_id': sid, 'text': 'Varför valde du den mörka rubriken?'}
        self.assertEqual(anropa('POST', '/api/arbetsyta/%s/foljdfraga' % SLUG, fraga, skriv)[0], 409)
        self.agarens_val()
        status, _r, kropp = anropa('GET', '/api/arbetsyta/%s/historik/%s' % (SLUG, sid))
        h = json.loads(kropp)
        self.assertEqual(status, 200, kropp)
        self.assertEqual([r['typ'] for r in h['rader']], ['in', 'ut', 'verktyg'])
        self.assertNotIn('ABCDEFGHIJ', kropp.decode())
        falsk = FalskClaude()
        self.addCleanup(falsk.stada)
        self.stack.enter_context(patch.object(samverkan, 'subprocess', SimpleNamespace(
            Popen=falsk, PIPE=subprocess.PIPE, TimeoutExpired=subprocess.TimeoutExpired)))
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/foljdfraga' % SLUG, fraga, skriv)
        self.assertEqual(status, 200, kropp)
        g = json.loads(kropp)
        self.assertEqual((g['foralder'], g['ansvar']), (sid, 'följdfråga, skrivskyddad'))
        a = falsk.anrop[-1]
        self.assertEqual(a[a.index('--resume') + 1], sid)
        self.assertIn('--fork-session', a)
        self.assertEqual(a[a.index('--tools') + 1], 'Read,Glob,Grep')
        self.assertNotIn('Edit', ' '.join(a[a.index('--allowedTools') + 1:]))
        for t in threading.enumerate():
            if t.name.startswith('gren-'):
                t.join(20)
        status, _r, kropp = anropa('GET', '/api/arbetsyta/%s/grenar' % SLUG)
        self.assertEqual(status, 200, kropp)
        gr = json.loads(kropp)['grenar']
        self.assertEqual([(x['id'], x['lage'], x['foralder']) for x in gr], [('gren-prov-0001', 'besvarad', sid)])
        self.assertTrue(json.loads(anropa('POST', '/api/arbetsyta/%s/foljdfraga' % SLUG, fraga, skriv)[2])['upprepat'])
        self.assertEqual(len(falsk.anrop), 1)
        levande = self.session('skiss-k02', kandidat='k02', pid=self.levande())
        meddelanden._skriv(meddelanden.styrfil(SLUG, levande), {'session_id': levande, 'roll': 'skiss-k02', 'kandidat': 'k02', 'ansvar': 'utforande',
                                                               'korning': meddelanden.korning(SLUG), 'pid': self.levande(), 'lopare_pid': os.getpid(), 'slut': None})
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/foljdfraga' % SLUG, dict(fraga, id='gren-prov-0002', session_id=levande), skriv)
        self.assertEqual(status, 409, 'en session som arbetar förgrenas inte: föräldern får aldrig en andra process')

    def test_beslutet_binds_till_den_version_och_bild_agaren_sett(self):
        if self.sajt is None:  # kandidatens fotograferade version kommer ur mallsajten (fixturen)
            self.skipTest(utan_sajt())
        port, host, anropa = self.server()
        skriv = {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'}
        v1 = kandidater.las_status(SLUG, 'k01')['version']
        bild = 'underlag/%s/atelje/kandidater/k01/bilder/start/vy-390-forsta.png' % SLUG
        import hashlib
        sha = hashlib.sha256(PNG).hexdigest()
        bas = {'beslut': 'godkand', 'kandidater': [{'id': 'k01', 'version': v1}], 'korning': self.status['startad']}
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/beslut' % SLUG, bas, skriv)
        self.assertEqual(status, 400, kropp)
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/beslut' % SLUG, dict(bas, sedd=[{'kandidat': 'k01', 'version': v1, 'bild': bild, 'bild_sha': '0' * 64}]), skriv)
        self.assertEqual((status, json.loads(kropp)['slag']), (409, 'Inaktuell'))
        # rätt bild, men arbetsversionen har ändrats efter fotograferingen (fixturen): inget tyst godkännande
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/beslut' % SLUG, dict(bas, sedd=[{'kandidat': 'k01', 'version': v1, 'bild': bild, 'bild_sha': sha}]), skriv)
        self.assertEqual(status, 400, kropp)
        self.assertFalse((self.las(self.u / 'atelje' / 'VINNARE.json') if (self.u / 'atelje' / 'VINNARE.json').is_file() else {}).get('godkand'))
        self.assertEqual(self.domrader(), [])
        val = {'beslut': 'valj', 'kandidater': [{'id': 'k01', 'version': v1}], 'korning': self.status['startad'],
               'sedd': [{'kandidat': 'k01', 'version': v1, 'bild': bild, 'bild_sha': sha}], 'text': 'Den här vidare.'}
        status, _r, kropp = anropa('POST', '/api/arbetsyta/%s/beslut' % SLUG, val, skriv)
        self.assertEqual(status, 200, kropp)
        d = self.domrader()[-1]
        self.assertEqual((d['kalla'], d['beslut'], d['arbetsyta']['vy']), ('ägaren', 'valj', 'Arbetsyta, beslut'))
        self.assertEqual(d['arbetsyta']['sedd'][0]['bild_sha'], sha)
        b = [m for m in meddelanden.alla(SLUG) if m['syfte'] == 'agarbeslut']
        self.assertEqual([(m['avsandare']['typ'], m['kandidat'], m['dom']['beslut']) for m in b], [('agare', 'k01', 'valj')])

    # --- HTTP genom den riktiga hanteraren ---

    def test_http_vagen_genom_den_riktiga_hanteraren(self):
        port, host, anropa = self.server()
        status, r, _ = anropa('GET', '/')
        self.assertEqual(status, 200)
        self.assertEqual(r.getheader('X-Frame-Options'), 'DENY')
        self.assertIn("frame-ancestors 'none'", r.getheader('Content-Security-Policy') or '')
        status, _, kropp = anropa('GET', '/api/arbetsyta/%s' % SLUG)
        self.assertEqual((status, json.loads(kropp)['slug']), (200, SLUG))
        self.assertEqual(anropa('GET', '/api/arbetsyta/okand-kund')[0], 404)
        self.assertEqual(anropa('GET', '/api/arbetsyta/%s/kod?kandidat=k01&fil=../x' % SLUG)[0], 404)
        # strömmen: bara dashboardens egen sida
        for huvud in ({'Sec-Fetch-Site': 'cross-site'}, {'Origin': 'http://annan.example'}):
            self.assertEqual(anropa('GET', '/api/arbetsyta/%s/strom' % SLUG, huvud=huvud)[0], 403, huvud)
        fore = dash.STROMMAR['antal']
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=20)
        try:
            c.request('GET', '/api/arbetsyta/%s/strom' % SLUG, headers={'Sec-Fetch-Site': 'same-origin'})
            r = c.getresponse()
            self.assertEqual(r.status, 200)
            self.assertTrue(r.getheader('Content-Type').startswith('text/event-stream'))
            rader = []
            while 'event: lage' not in rader and len(rader) < 20:
                rader.append(r.readline().decode().rstrip('\n'))
            data = r.readline().decode()
        finally:
            c.close()
        self.assertEqual(rader[0], 'retry: 3000', rader)
        self.assertIn('event: lage', rader)
        self.assertTrue(data.startswith('data: '), data[:80])
        lage_ = json.loads(data[len('data: '):])
        self.assertEqual((lage_['slug'], lage_['blind']), (SLUG, True))
        self.vanta_pa_strommar(fore)
        # skrivningar: nyckeln och ursprunget krävs, och inget startas utan dem
        with patch.object(partner, 'skicka') as sk:
            meddelande = {'meddelande_id': 'meddelande-http-01', 'text': 'Hej'}
            self.assertEqual(anropa('POST', '/api/arbetsyta/%s/partner' % SLUG, meddelande, {'Origin': 'http://' + host})[0], 403)
            self.assertEqual(anropa('POST', '/api/arbetsyta/%s/partner' % SLUG, meddelande,
                                    {'Origin': 'http://' + host, 'X-Nyckel': 'fel-nyckel'})[0], 403)
            self.assertEqual(anropa('POST', '/api/arbetsyta/%s/partner' % SLUG, meddelande,
                                    {'Origin': 'http://annan.example:%d' % port, 'X-Nyckel': 'provnyckel'})[0], 403)
            sk.assert_not_called()
        self.assertFalse((self.u / 'arbetsyta').exists())
        self.k02_fotograferad()
        status, _, kropp = anropa('POST', '/api/arbetsyta/%s/andring' % SLUG, self.andring(andring_id='andring-http-0001', version='0' * 64),
                                  {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'})
        svar_ = json.loads(kropp)
        self.assertEqual((status, svar_.get('slag')), (409, 'Inaktuell'), svar_)
        self.assertEqual(self.domrader(), [])
        self.assertEqual(anropa('POST', '/api/arbetsyta/okand-kund/andring', {}, {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'})[0], 404)

    def test_strommen_nekar_ursprunget_null(self):
        # GR-20261009-arbetsyta-oberoende#K1: en sida i en sandlåda (Origin: null) prenumererar inte
        port, host, anropa = self.server()
        fore = dash.STROMMAR['antal']
        for huvud in ({'Origin': 'null'}, {'Origin': 'null', 'Sec-Fetch-Site': 'same-origin'}):
            self.assertEqual(anropa('GET', '/api/arbetsyta/%s/strom' % SLUG, huvud=huvud)[0], 403, huvud)
        self.vanta_pa_strommar(fore)

    # --- startjournalen, signaturen och det delade läget ---

    def test_startjournalens_stopp_syns(self):
        # GR-20261009-arbetsyta-oberoende#K2: atelje.stoppa skriver 'stoppad', flodesstart 'stoppbegard'
        j = self.u / 'ateljestarter'
        self.skriv(j / 'prov-stoppad-0001.json', {'handling': 'valda', 'tid': '2026-10-09T05:40:00Z', 'status': 'slut', 'slutkod': 4,
                                                  'stoppad': '2026-10-09T05:41:00Z'})
        self.skriv(j / 'prov-stoppbegard-0002.json', {'handling': 'valda', 'tid': '2026-10-09T05:42:00Z', 'status': 'slut', 'slutkod': 4,
                                                      'stoppbegard': '2026-10-09T05:43:00Z'})
        self.skriv(j / 'prov-utan-stopp-0003.json', {'handling': 'om', 'tid': '2026-10-09T05:00:00Z', 'status': 'slut', 'slutkod': 0})
        s = {x['start_id']: x['stopp_begart'] for x in arbetsyta.startjournal(dash, SLUG)}
        self.assertEqual(s, {'prov-stoppad-0001': True, 'prov-stoppbegard-0002': True, 'prov-utan-stopp-0003': False})

    def test_signaturen_foljer_statusfilen(self):
        a = arbetsyta.signatur(dash, SLUG)
        self.assertEqual(arbetsyta.signatur(dash, SLUG), a, 'inget har ändrats')
        f = self.u / 'atelje' / 'STATUS.json'
        fore = os.stat(f).st_mtime_ns
        self.skriv_status(lage='valda')
        os.utime(f, ns=(fore + 2_000_000_000, fore + 2_000_000_000))
        b = arbetsyta.signatur(dash, SLUG)
        self.assertNotEqual(b, a)
        self.assertEqual(arbetsyta.signatur(dash, SLUG), b)

    # --- omgranskningen (GR-20261009-arbetsyta-omgranskning) ---

    def test_partnerns_arbetskatalog_provas_innan_nagot_journalfors(self):
        # N1: en arbetskatalog som är en länk nekas innan meddelandet eller ett sessions-id sparas; en vanlig fil stoppar inte
        falsk, _ps = self.falsk_partner()
        fil = self.u / 'arbetsyta' / 'PARTNER.json'
        rum = self.u / 'arbetsyta' / 'partner' / 'rum'
        ute = self.root / 'utanfor-rum'
        ute.mkdir()
        rum.parent.mkdir(parents=True)
        os.symlink(ute, rum)
        with self.assertRaises(ValueError):
            partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-n1-0001', 'text': 'Var står vi?'})
        self.assertFalse(fil.exists(), 'inget sessions-id och ingen post för ett nekat meddelande')
        self.assertEqual(falsk.anrop, [])
        self.assertEqual(list(ute.iterdir()), [])
        self.assertEqual(partner.lage(dash, SLUG)['lage'], 'vantar')
        os.unlink(rum)
        rum.mkdir()
        # det Claude Code läser in ur arbetskatalogen (projektets inställningar, CLAUDE.md) stoppar turen innan något journalförs
        for namn in ('.claude', 'CLAUDE.md'):
            (rum / namn).mkdir() if namn == '.claude' else (rum / namn).write_text('vidga läsrätten', encoding='utf-8')
            with self.assertRaises(ValueError):
                partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-n1-0001', 'text': 'Var står vi?'})
            self.assertFalse(fil.exists(), namn)
            self.assertEqual(falsk.anrop, [], namn)
            (rum / namn).rmdir() if namn == '.claude' else (rum / namn).unlink()
        (rum / '.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1')  # Finder lägger den där när katalogen öppnas
        m = partner.skicka(dash, SLUG, {'meddelande_id': 'meddelande-n1-0001', 'text': 'Var står vi?'})
        self.assertFalse(m.get('upprepat'), 'det nekade meddelandet journalfördes aldrig')
        self.assertEqual(m['lage'], 'svarat')
        a = falsk.anrop[0]
        self.assertEqual(a[a.index('--session-id') + 1], self.las(fil)['session_id'], 'första turen skapar sessionen')
        self.assertNotIn('--resume', a)

    def test_samma_andring_med_nytt_id_ger_samma_rad_aven_efter_statusbytet(self):
        # N3: ett omförsök eller en andra flik som räknat ett nytt id (och beslut) ur kandidatens nya status skriver ingen ny rad
        self.k02_fotograferad()
        r = arbetsyta.skicka_andring(dash, SLUG, self.andring(andring_id='andring-n3-0001'))
        self.assertFalse(r['upprepat'])
        self.assertEqual(kandidater.las_status(SLUG, 'k02')['status'], 'vald', 'kandidatens status har ändrats efter första raden')
        for beslut, aid in (('valj', 'andring-n3-0002'), ('putsa', 'andring-n3-0003')):
            r = arbetsyta.skicka_andring(dash, SLUG, self.andring(andring_id=aid, beslut=beslut))
            self.assertTrue(r['upprepat'], beslut)
            self.assertEqual(r['dom']['arbetsyta']['andring_id'], 'andring-n3-0001')
        self.assertEqual(len(self.domrader()), 1)
        r = arbetsyta.skicka_andring(dash, SLUG, self.andring(andring_id='andring-n3-0004', beslut='putsa', text='Knappen ska stå under rubriken.'))
        self.assertFalse(r['upprepat'], 'en annan text är en ny ändring')
        self.assertEqual([d['beslut'] for d in self.domrader()], ['valj', 'putsa'])
        # samma text riktad mot en annan del av samma version är en ny ändring (omgranskningens N3, provskrivarens not 3)
        r = arbetsyta.skicka_andring(dash, SLUG, self.andring(andring_id='andring-n3-0005', beslut='putsa', text='Knappen ska stå under rubriken.', **{'del': 'sidfoten'}))
        self.assertFalse(r['upprepat'], 'samma text för en annan del')

    def test_partnerns_tur_arbetar_bara_med_sessionens_id_och_inom_fristen(self):
        # N4: en levande pid utan sessionens id i kommandot (återanvänd), eller en tur äldre än fristen, arbetar inte
        sid = str(uuid.uuid4())
        tur = ORIG_POPEN([sys.executable, '-c', 'import sys, time; time.sleep(float(sys.argv[1]))', '60', '--resume', sid], stdin=subprocess.DEVNULL)
        self.addCleanup(stoppa, tur)
        annan = self.levande()
        nu = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        gammal = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - partner.profil()['frist'] - 120))
        with patch.object(partner, '_ps', return_value=''):
            for namn, pid, tid, vantat in (('turen', tur.pid, nu, 'arbetar'), ('återanvänd pid', annan, nu, 'avbrutet'),
                                           ('över fristen', tur.pid, gammal, 'avbrutet')):
                with self.subTest(namn):
                    self.partnerpost(sid, pid, tid)
                    p = partner.lage(dash, SLUG, samtal=True)
                    self.assertEqual(p['meddelanden'][0]['lage'], vantat)
                    self.assertEqual(p['lage'], 'aktiv' if vantat == 'arbetar' else 'avbruten')

    def test_signaturen_och_det_delade_laget_foljer_jamforelsen(self):
        # N5: en kund som blir en oavgjord arm får en ny signatur, så att det delade läget räknas om och döljs
        a = arbetsyta.signatur(dash, SLUG)
        self.assertFalse(arbetsyta.lage_delat(dash, SLUG, a)['ab_dold'])
        with patch.object(dash, 'ab_oavgjord', return_value=True):
            b = arbetsyta.signatur(dash, SLUG)
            self.assertNotEqual(b, a)
            l = arbetsyta.lage_delat(dash, SLUG, b)
            self.assertTrue(l['ab_dold'])
            self.assertEqual(l['korning'], {})
        with patch.object(dash, 'ab_oavgjord', side_effect=RuntimeError('jämförelsen kunde inte läsas')):
            self.assertNotEqual(arbetsyta.signatur(dash, SLUG), a)
        self.assertEqual(arbetsyta.signatur(dash, SLUG), a)

    def test_rollerna_doljs_fore_agarens_val_och_armens_tid_visas_inte(self):
        # blindningens rest (B1, B2): rollnamnet (forbattra, skisskritik) säger vad granskningen ledde till; armens tid skiljer armarna
        utf = self.session('forbattra-k01', slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0')
        gr = self.session('skisskritik-k02', kandidat='k02', slut='2026-10-09T05:21:00Z', utfall='avslutad, kod 0')
        with patch.object(partner, '_ps', return_value=''):
            l = self.lage()
            text, _ = partner.kontexttext(dash, SLUG, {})
        s = {x['session_id']: x for x in l['sessioner'] if x.get('kalla') == 'ateljén'}
        self.assertEqual(set(s), {utf, gr})
        for i, ansvar in ((utf, 'utforande'), (gr, 'granskning')):
            self.assertEqual((s[i]['roll'], s[i]['roll_dold'], s[i]['ansvar']), (None, True, ansvar))
        for roll in ('forbattra', 'skisskritik'):
            self.assertNotIn(roll, text)
            self.assertNotIn(roll, json.dumps(l['sessioner'], ensure_ascii=False))
        self.assertIn('roll dold före ägarens val', text)
        self.agarens_val()
        s = {x['session_id']: x for x in self.lage()['sessioner'] if x.get('kalla') == 'ateljén'}
        self.assertEqual((s[utf]['roll'], s[utf]['roll_dold']), ('forbattra-k01', False))
        self.assertTrue({x['slug']: x for x in arbetsyta.projekt(dash)}[SLUG]['senast_andrad'])
        with patch.object(dash, 'ab_oavgjord', return_value=True):
            self.assertIsNone({x['slug']: x for x in arbetsyta.projekt(dash)}[SLUG]['senast_andrad'])

    def test_maskeringen_tar_leverantorsnycklar_utan_nyckelord(self):
        # A7:s rest: Resends nycklar (re_…) står utan något nyckelord framför
        for rad in ('re_AbCdEf1234567890xyz', 'skickar med re_AbCdEf1234567890xyz till mottagaren'):
            m = arbetsyta.maskera(rad)
            self.assertNotIn('AbCdEf1234567890xyz', m, rad)
            self.assertIn('•••', m)

    def test_skaparens_markeringsrad_utan_dashboardens_vynamn(self):
        # N7: "i vyn Arbetsyta" säger skaparen ingenting; sida, del och fil gör det
        self.k02_fotograferad()
        arbetsyta.skicka_andring(dash, SLUG, self.andring(andring_id='andring-n7-0001', **{'vy': 'Arbetsyta', 'sida': '/', 'del': 'rubriken',
                                                                                          'fil': 'kod/index.astro'}))
        rad = [r for r in skapande.kritikrader(SLUG, underlag=self.root / 'underlag', aktuella=True) if 'ändringen gäller' in r]
        self.assertEqual(len(rad), 1)
        self.assertNotIn('i vyn', rad[0])
        for del_ in ('sida /', 'del rubriken', 'fil kod/index.astro'):
            self.assertIn(del_, rad[0])

    def test_strommarna_delar_laget_per_signatur(self):
        # GR-20261009-arbetsyta-oberoende#K7: en ström per flik räknar inte fram läget var för sig
        with patch.object(arbetsyta, 'lage', wraps=arbetsyta.lage) as raknat:
            a = arbetsyta.lage_delat(dash, SLUG, 'signatur-1')
            b = arbetsyta.lage_delat(dash, SLUG, 'signatur-1')
            self.assertIs(a, b)
            self.assertEqual(raknat.call_count, 1)
            c = arbetsyta.lage_delat(dash, SLUG, 'signatur-2')
            self.assertIsNot(c, a)
            self.assertEqual(raknat.call_count, 2)
            d = arbetsyta.lage_delat(dash, SLUG, 'signatur-2', max_alder=0)  # äldre än 30 s (här 0): räknas om
            self.assertIsNot(d, c)
            self.assertEqual(raknat.call_count, 3)
        self.assertEqual(a['slug'], SLUG)


if __name__ == '__main__':
    unittest.main()
