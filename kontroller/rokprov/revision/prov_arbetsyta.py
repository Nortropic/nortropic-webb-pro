#!/usr/bin/env python3
"""Arbetsytans läsväg, partnersamtal och HTTP-väg (dashboard/arbetsyta.py, dashboard/partner.py, server.py; ägarens uppdrag
2026-10-09) med testprojektet ur arbetsyta_fixtur.py i en isolerad rot, utan modell:

- läget ur testprojektet: testdata, blindningen, neutrala etiketter, de tre ansvaren som väntar och förhandsvisningarna;
- sessionernas lägen ur förteckningen och transkripten: avslutad, avbruten (stopp, signal, död process), aktiv, väntar på
  verktyg, start pågår och okänt;
- blindningen på servervägen: aktivitetens sökvägar, körningsloggen och DESIGN.md i kodvyn före ägarens första val, och
  maskerade hemligheter efter det;
- kodvyn: diffen mot den bevarade versionen, inga länkar och inga vägar ut ur projektet;
- ägarens ändring: inaktuell körning, version och steg nekas; samma ändrings-id ger samma rad;
- partnern: en session per kund (--session-id, sedan --resume), ett meddelande i taget, bara claude-processer räknas, och
  tillåtelselistan; claude startas aldrig (en falsk process står för den);
- HTTP genom den riktiga hanteraren: ramskydd, strömmens ursprung, nyckeln och ursprunget för skrivningar, 409 och 404;
- signaturen som strömmen läser om läget efter.

    .venv/bin/python -B kontroller/rokprov/revision/prov_arbetsyta.py

Sajtens del av testprojektet kopieras ur rökprovets byggda mallsajt (kunder/rokprov-mall/sajt, som rokprov.sh bygger
tidigare); saknas den hoppas det som kräver sajten över med skälet.
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
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import kandidater  # noqa: E402
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
ORIG_POPEN = subprocess.Popen


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


class FalskProcess:
    def __init__(self, p):
        self.p, self.pid, self.returncode, self.prompt = p, p.pid, None, None

    def communicate(self, input=None, timeout=None):
        self.prompt = input.decode() if input else self.prompt
        self.returncode = self.p.wait(timeout=timeout)
        return b'', b''


class FalskClaude:
    """claude -p i partnerns ställe: pid:en är en riktig kortlivad process, och svaret skrivs till stdout-filen som Claude
    Code skriver sin svarsfil. Ingen modell anropas, och något annat än claude startas aldrig här."""

    def __init__(self):
        self.anrop, self.processer, self.svara, self.sov = [], [], True, '0.3'

    def __call__(self, args, **kw):
        args = list(args)
        if os.path.basename(str(args[0])) != 'claude':
            raise AssertionError('partnern startade något annat än claude: %s' % args[:3])
        self.anrop.append(args)
        p = ORIG_POPEN(['sleep', self.sov], stdin=subprocess.DEVNULL)
        if self.svara:
            sid = args[args.index('--session-id' if '--session-id' in args else '--resume') + 1]
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
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.projekt))
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

    def skriv_status(self, **falt):
        f = self.u / 'atelje' / 'STATUS.json'
        st = dict(self.las(f), **falt)
        f.write_text(json.dumps(st, ensure_ascii=False), encoding='utf-8')
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
        k = self.u / 'atelje' / 'sessioner'
        k.mkdir(parents=True, exist_ok=True)
        (k / (sid + '.json')).write_text(json.dumps({'session_id': sid, 'roll': roll, 'kandidat': kandidat, 'svar': 'svar-%s.json' % roll,
                                                     'start': start, 'modell': 'claude-fable-5-1', 'pid': pid, 'slut': slut, 'utfall': utfall}),
                                         encoding='utf-8')
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

    # --- A: läget ---

    def test_laget_ur_testprojektet_ar_blint_med_neutrala_etiketter(self):
        l = self.lage()
        self.assertEqual(l['ofullstandig'], [], l['ofullstandig'])
        self.assertEqual((l['projekt']['slug'], l['projekt']['testdata']), (SLUG, True))
        self.assertTrue(l['blind'])
        self.assertEqual([x['slug'] for x in arbetsyta.projekt(dash)], [SLUG])
        self.assertEqual(sorted(x['etikett'] for x in l['kandidater']), ['Förslag A', 'Förslag B'])
        self.assertEqual(sorted(x['id'] for x in l['kandidater']), ['k01', 'k02'])
        text = json.dumps(l, ensure_ascii=False)
        for dolt in ('Testdata: verkstaden i arbete', 'Testdata: lugn lista', 'Testdata k01'):  # planens och kandidaternas titlar
            self.assertNotIn(dolt, text, 'titeln syns före ägarens första val')
        for nyckel in ('arbetsledning', 'utforande', 'granskning'):
            self.assertEqual(l['roller'][nyckel]['lage'], 'vantar', l['roller'][nyckel])
            self.assertEqual(l['roller'][nyckel]['sessioner'], [])
        g = l['roller']['granskning']['lage_text']
        self.assertIn('ingen session för granskning har startat', g)
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

    # --- B: sessionernas lägen ---

    def test_sessionernas_lagen_ur_forteckningen_och_transkripten(self):
        flode_pid, annan_pid = self.levande(), self.levande()
        t = '2026-10-09T05:1%d:00Z'
        rot = str(self.root)
        sid = {
            'avslutad': self.session('skiss-k01', slut='2026-10-09T05:20:00Z', utfall='avslutad, kod 0'),
            'svarsfel': self.session('skiss-k02', kandidat='k02', slut='2026-10-09T05:21:00Z', utfall='avslutad, kod 0',
                                     rader=[anrop('a1', 'Read', rot + '/underlag/%s/BRIEF.md' % SLUG, t % 1), svar('a1', t % 2),
                                            {'type': 'result', 'subtype': 'error_max_turns', 'is_error': True, 'num_turns': 9, 'timestamp': t % 3}]),
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
        self.assertEqual(lagen['avslutad'][0], 'avslutad', lagen)
        self.assertEqual(lagen['avslutad'][1], 'avslutad 2026-10-09T05:20:00Z')
        self.assertEqual(lagen['svarsfel'], ('avbruten', 'avslutad med fel i sessionens svar'))
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

    # --- C: blindningen på servervägen ---

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

    # --- D: koden ---

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

    # --- E: ägarens ändring ---

    def test_andringen_binds_till_korning_version_och_steg(self):
        v = kandidater.las_status(SLUG, 'k01').get('version') or ''
        bas = {'andring_id': 'andring-prov-0001', 'text': 'Rubriken ska vara större.', 'kandidat': 'k01', 'version': v,
               'korning': self.status['startad'], 'vy': 'telefon', 'sida': '/', 'del': 'rubriken'}
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
        if self.sajt is None:
            self.skipTest(utan_sajt())
        r = arbetsyta.skicka_andring(dash, SLUG, bas)
        self.assertTrue(r['ok'])
        self.assertFalse(r['upprepat'])
        rader = self.domrader()
        self.assertEqual(len(rader), 1, rader)
        d = rader[-1]
        self.assertEqual((d['kalla'], d['beslut']), ('ägaren', 'valj'))
        self.assertEqual({k: d['arbetsyta'].get(k) for k in ('andring_id', 'kandidat', 'version', 'korning')},
                         {'andring_id': 'andring-prov-0001', 'kandidat': 'k01', 'version': v[:12], 'korning': self.status['startad']})
        self.assertEqual([(x['id'], x['version']) for x in d['kandidater']], [('k01', v)])
        self.assertIn('Rubriken ska vara större.', d['delar']['k01'])
        r = arbetsyta.skicka_andring(dash, SLUG, bas)
        self.assertTrue(r['upprepat'])
        self.assertEqual(len(self.domrader()), 1, 'samma ändrings-id ger samma rad')
        l = self.lage()
        self.assertEqual(l['ofullstandig'], [], l['ofullstandig'])
        self.assertFalse(l['blind'])
        self.assertIn('valda', [h['id'] for h in l['handlingar']], l['handlingar'])
        self.assertEqual(len(l['overlamningar']), 1, l['overlamningar'])
        o = l['overlamningar'][0]
        self.assertEqual((o['id'], o['kandidat'], o['version'], o['avsandare']), ('andring-prov-0001', 'k01', v[:12], 'ägaren'))
        self.assertEqual(set(o['steg']), {'skickad'}, 'inget steg efter skickad sätts av arbetsytan själv')

    # --- F: partnern ---

    def test_partnern_en_session_per_kund_och_ett_meddelande_i_taget(self):
        falsk = FalskClaude()
        self.addCleanup(falsk.stada)
        self.stack.enter_context(patch.object(partner, 'subprocess', SimpleNamespace(
            Popen=falsk, PIPE=subprocess.PIPE, run=subprocess.run, TimeoutExpired=subprocess.TimeoutExpired, SubprocessError=subprocess.SubprocessError)))
        ps = self.stack.enter_context(patch.object(partner, '_ps', return_value=''))
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
        self.assertEqual(partner.lage(dash, SLUG)['lage'], 'beslut')
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

    # --- G: HTTP genom den riktiga hanteraren ---

    def test_http_vagen_genom_den_riktiga_hanteraren(self):
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
        slut = time.time() + 15
        while dash.STROMMAR['antal'] != fore and time.time() < slut:
            time.sleep(0.1)
        self.assertEqual(dash.STROMMAR['antal'], fore, 'strömmen slutar och släpper sin plats')
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
        status, _, kropp = anropa('POST', '/api/arbetsyta/%s/andring' % SLUG,
                                  {'andring_id': 'andring-http-0001', 'text': 'Större rubrik.', 'kandidat': 'k01', 'version': '0' * 64,
                                   'korning': self.status['startad']},
                                  {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'})
        svar_ = json.loads(kropp)
        self.assertEqual((status, svar_.get('slag')), (409, 'Inaktuell'), svar_)
        self.assertEqual(self.domrader(), [])
        self.assertEqual(anropa('POST', '/api/arbetsyta/okand-kund/andring', {}, {'Origin': 'http://' + host, 'X-Nyckel': 'provnyckel'})[0], 404)

    # --- H: signaturen ---

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


if __name__ == '__main__':
    unittest.main()
