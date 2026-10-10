#!/usr/bin/env python3
"""Motorns sida av Nortropic.app (kontraktet desktop/1, dashboard/desktop.py och server.py; kunskap/desktop.md) genom
den riktiga hanteraren på en egen port i en isolerad rot, utan modell och utan appen:

- identiteten: HMAC-SHA256 med nyckeln över appens utmaning, instansen, roten, pid, porten och commit; ogiltig utmaning
  nekas; en webbsida (Origin eller Sec-Fetch-Site) får ingen identitet;
- engångskoden: bara med nyckeln (aldrig med en session), bunden till instansen, en gång och med utgång; inloggningen
  sätter en HttpOnly-kaka med SameSite=Strict per port och leder bara till en vy i portalen;
- sessionens skrivningar: bara med exakt samma ursprung och Sec-Fetch-Site same-origin; en förhandsvisning på en annan
  port, Origin null, same-site, en återkallad, utloggad eller utgången session och en session som försöker skapa en ny
  nekas; strömmen som öppnats med en session slutar när sessionen återkallas;
- Ny kund: genom Kundstarts skapandeväg, testmärkningen ur vägens fält och testslug, ingen modellbudget för en riktig
  kund, samma operation ger samma ärende, samma namn ger 409 med det befintliga ärendet, okända fält och fel typ nekas,
  ägarens anteckningar sparas en gång och märks som hans, inget modelljobb köas;
- översikten: Kundstart och byggprojektet med samma slug är en kund (inte en dubblett), testkunder hålls isär;
- det pågående arbetet: bara motorns egen utcheckning ur körregistret;
- portalens filer serveras och UI-versionen följer filerna.

    .venv/bin/python -B kontroller/rokprov/revision/prov_desktop.py
"""
import contextlib
import hashlib
import hmac
import http.client
import json
import os
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
import server as dash  # noqa: E402
import desktop  # noqa: E402
import korregister  # noqa: E402
import kundstart as ks  # noqa: E402

NYCKEL = 'provnyckel-desktop-0123456789'


class Desktop(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-desktop-', 'desktopkontraktets prov'))).resolve()
        (self.root / 'underlag').mkdir()
        (self.root / 'kunder').mkdir()
        self.stack.enter_context(patch.multiple(dash, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.dict(desktop._KODER, clear=True))
        self.stack.enter_context(patch.dict(desktop._SESSIONER, clear=True))
        self.stack.enter_context(patch.dict(desktop._CACHE, clear=True))
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.port = srv.server_port
        self.host = '127.0.0.1:%d' % self.port
        self.ursprung = 'http://' + self.host
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {self.host}}))
        self.stack.enter_context(patch.dict(dash.NYCKEL, {'varde': NYCKEL}))
        self.stack.enter_context(patch.dict(dash.STROMMAR, {'livslangd': 20, 'intervall': 0.2}))
        self.stack.enter_context(patch.dict(desktop._KONF, {}))
        desktop.konfigurera(self.root, self.port)

    def anropa(self, metod, vag, data=None, huvud=None, tid=20):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=tid)
        try:
            c.request(metod, vag, json.dumps(data) if data is not None else None, huvud or {})
            r = c.getresponse()
            kropp = r.read()
            try:
                j = json.loads(kropp)
            except ValueError:
                j = None
            return r.status, r, j
        finally:
            c.close()

    def nyckelpost(self, vag, data):
        return self.anropa('POST', vag, data, {'Origin': self.ursprung, 'X-Nyckel': NYCKEL, 'Content-Type': 'application/json'})

    def session(self):
        s, _, j = self.anropa('GET', '/api/desktop/identitet?utmaning=' + 'ab' * 16)
        self.assertEqual(s, 200)
        s, _, k = self.nyckelpost('/api/desktop/session', {'instans': j['instans']})
        self.assertEqual(s, 200, k)
        s, r, _ = self.anropa('GET', '/desktop/inloggning?kod=' + k['kod'])
        self.assertEqual(s, 303)
        kaka = r.getheader('Set-Cookie')
        return kaka.split(';', 1)[0], kaka

    # --- identiteten ---

    def test_identiteten_bevisar_nyckeln_utan_att_lamna_ut_den(self):
        utmaning = os.urandom(32).hex()
        s, _, j = self.anropa('GET', '/api/desktop/identitet?utmaning=' + utmaning)
        self.assertEqual(s, 200)
        self.assertEqual(j['kontrakt'], 'desktop/1')
        self.assertEqual(j['rot'], str(self.root))
        self.assertEqual(j['pid'], os.getpid())
        self.assertEqual(j['port'], self.port)
        meddelande = 'nwp-desktop/1\n%s\n%s\n%s\n%d\n%d\n%s' % (utmaning, j['instans'], j['rot'], j['pid'], j['port'], j['version']['commit'])
        self.assertTrue(hmac.compare_digest(j['bevis'], hmac.new(NYCKEL.encode(), meddelande.encode(), hashlib.sha256).hexdigest()))
        fel = hmac.new(b'en annan nyckel', meddelande.encode(), hashlib.sha256).hexdigest()
        self.assertNotEqual(j['bevis'], fel, 'en främmande nyckel ger ett annat bevis')
        self.assertNotIn(NYCKEL, json.dumps(j))

    def test_identiteten_nekar_ogiltig_utmaning_och_webbsidor(self):
        for u in ('', 'zz' * 20, 'ab', 'ab' * 80):
            with self.subTest(utmaning=u):
                self.assertEqual(self.anropa('GET', '/api/desktop/identitet?utmaning=' + u)[0], 400)
        u = 'ab' * 16
        self.assertEqual(self.anropa('GET', '/api/desktop/identitet?utmaning=' + u, huvud={'Origin': 'http://angripare.test'})[0], 403)
        self.assertEqual(self.anropa('GET', '/api/desktop/identitet?utmaning=' + u, huvud={'Origin': self.ursprung})[0], 403)
        self.assertEqual(self.anropa('GET', '/api/desktop/identitet?utmaning=' + u, huvud={'Sec-Fetch-Site': 'cross-site'})[0], 403)
        self.assertEqual(self.anropa('GET', '/api/desktop/identitet?utmaning=' + u, huvud={'Host': 'angripare.test:%d' % self.port})[0], 421)

    # --- engångskoden och inloggningen ---

    def test_engangskoden_kraver_nyckeln_och_instansen_och_galler_en_gang(self):
        _, _, j = self.anropa('GET', '/api/desktop/identitet?utmaning=' + 'cd' * 16)
        self.assertEqual(self.anropa('POST', '/api/desktop/session', {'instans': j['instans']}, {'Origin': self.ursprung})[0], 403)
        self.assertEqual(self.nyckelpost('/api/desktop/session', {'instans': 'fel'})[0], 409)
        s, _, k = self.nyckelpost('/api/desktop/session', {'instans': j['instans']})
        self.assertEqual(s, 200)
        s, r, _ = self.anropa('GET', '/desktop/inloggning?kod=%s&till=kunder' % k['kod'])
        self.assertEqual(s, 303)
        self.assertEqual(r.getheader('Location'), '/#/kunder')
        kaka = r.getheader('Set-Cookie')
        self.assertIn('nwp_session_%d=' % self.port, kaka)
        for del_ in ('HttpOnly', 'SameSite=Strict', 'Path=/'):
            self.assertIn(del_, kaka)
        self.assertEqual(self.anropa('GET', '/desktop/inloggning?kod=' + k['kod'])[0], 403, 'en använd kod gäller inte igen')
        self.assertEqual(self.anropa('GET', '/desktop/inloggning?kod=pahittad')[0], 403)

    def test_engangskoden_gar_ut_och_malet_ar_bara_en_vy(self):
        _, _, j = self.anropa('GET', '/api/desktop/identitet?utmaning=' + 'ef' * 16)
        _, _, k = self.nyckelpost('/api/desktop/session', {'instans': j['instans']})
        with patch.object(desktop.time, 'time', return_value=time.time() + desktop.KOD_TID + 1):
            self.assertEqual(self.anropa('GET', '/desktop/inloggning?kod=' + k['kod'])[0], 403)
        _, _, k = self.nyckelpost('/api/desktop/session', {'instans': j['instans']})
        s, r, _ = self.anropa('GET', '/desktop/inloggning?kod=%s&till=//angripare.test/x' % k['kod'])
        self.assertEqual((s, r.getheader('Location')), (303, '/#/start'))

    # --- sessionens skrivningar ---

    def test_sessionen_skriver_bara_med_exakt_samma_ursprung(self):
        kaka, _ = self.session()
        vag = '/api/finns-inte-efter-sparren'
        bas = {'Cookie': kaka, 'Content-Type': 'application/json'}
        s, _, j = self.anropa('POST', vag, {}, {**bas, 'Origin': self.ursprung, 'Sec-Fetch-Site': 'same-origin'})
        self.assertNotEqual(s, 403, 'rätt ursprung med sessionen passerar nyckelspärren (%s)' % j)
        for namn, h in (('förhandsvisningens port', {'Origin': 'http://127.0.0.1:%d' % (self.port + 1)}),
                        ('Origin null', {'Origin': 'null'}),
                        ('utan Origin', {}),
                        ('same-site', {'Origin': self.ursprung, 'Sec-Fetch-Site': 'same-site'}),
                        ('cross-site', {'Origin': self.ursprung, 'Sec-Fetch-Site': 'cross-site'}),
                        ('främmande värd', {'Origin': 'http://angripare.test'})):
            with self.subTest(namn):
                self.assertEqual(self.anropa('POST', vag, {}, {**bas, **h})[0], 403)
        self.assertEqual(self.anropa('POST', vag, {}, {'Cookie': 'nwp_session_%d=pahittad' % self.port, 'Origin': self.ursprung})[0], 403)
        self.assertEqual(self.anropa('POST', '/api/desktop/session', {'instans': desktop.INSTANS}, {**bas, 'Origin': self.ursprung})[0], 403,
                         'en session skapar aldrig en ny session')
        self.assertEqual(self.anropa('POST', '/api/desktop/las', {}, {**bas, 'Origin': self.ursprung})[0], 403, 'en session låser inte åt appen')

    def test_las_utloggning_och_tomgang_aterkallar(self):
        kaka, _ = self.session()
        ok = {'Cookie': kaka, 'Origin': self.ursprung, 'Content-Type': 'application/json'}
        vag = '/api/finns-inte-efter-sparren'
        self.assertNotEqual(self.anropa('POST', vag, {}, ok)[0], 403)
        self.assertEqual(self.nyckelpost('/api/desktop/las', {})[0], 200)
        self.assertEqual(self.anropa('POST', vag, {}, ok)[0], 403, 'appens lås återkallar sessionen')
        kaka, _ = self.session()
        ok['Cookie'] = kaka
        s, r, _ = self.anropa('POST', '/api/desktop/utloggning', {}, ok)
        self.assertEqual(s, 200)
        self.assertIn('Max-Age=0', r.getheader('Set-Cookie'))
        self.assertEqual(self.anropa('POST', vag, {}, ok)[0], 403, 'utloggningen återkallar den egna sessionen')
        kaka, _ = self.session()
        ok['Cookie'] = kaka
        with patch.object(desktop.time, 'time', return_value=time.time() + desktop.SESSION_TOMGANG + 5):
            self.assertEqual(self.anropa('POST', vag, {}, ok)[0], 403, 'en session utan aktivitet går ut')
        s, _, j = self.anropa('GET', '/api/desktop/lage', huvud={'Cookie': kaka})
        self.assertEqual((s, j['session']), (200, False))

    def test_strommen_slutar_nar_sessionen_aterkallas(self):
        import arbetsyta
        kaka, _ = self.session()
        with patch.object(arbetsyta, 'projekt', return_value=[{'slug': 'testdata-strom'}]), \
                patch.object(arbetsyta, 'signatur', return_value='s'), patch.object(arbetsyta, 'lage_delat', return_value={'tid': 't'}):
            klar = {}

            def lyssna():
                t = time.time()
                c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=30)
                c.request('GET', '/api/arbetsyta/testdata-strom/strom', headers={'Cookie': kaka})
                r = c.getresponse()
                klar['status'] = r.status
                r.read()  # till slutet
                klar['tid'] = time.time() - t
                c.close()
            tr = threading.Thread(target=lyssna, daemon=True)
            tr.start()
            time.sleep(1.0)
            self.nyckelpost('/api/desktop/las', {})
            tr.join(10)
        self.assertEqual(klar.get('status'), 200)
        self.assertLess(klar.get('tid', 99), 6, 'strömmen stängs efter låset, inte först vid sin livslängd (20 s)')

    # --- Ny kund ---

    def ny(self, **kw):
        data = {'foretag': 'Provbageriet Ånge', 'webbplats': 'https://exempel.se', 'syfte': 'Fler förfrågningar', 'kontakt': '', 'test': True,
                'operation': str(uuid.uuid4())}
        data.update(kw)
        return self.nyckelpost('/api/desktop/ny-kund', data), data

    def arende(self, eid):
        return ks.Lager(self.root / 'underlag' / 'kundstart').internt(eid)

    def test_ny_testkund_genom_kundstart_en_gang(self):
        (s, _, j), data = self.ny()
        self.assertEqual(s, 200, j)
        self.assertEqual(j['slug'], 'test-provbageriet-ange')
        self.assertTrue(j['nyckel'])
        d = self.arende(j['arende'])
        self.assertIs(d['fiktiv'], True)
        self.assertEqual(d['budget']['max_anrop'], 10)
        self.assertEqual(d['modell']['status'], 'inte_startad', 'att skapa kunden köar inget modelljobb')
        self.assertEqual(sorted(a['slag'] for a in d['anteckningar']), ['foretag', 'syfte', 'webbplats'])
        self.assertTrue(all(a['kunskap'] == 'agarens_anteckning' for a in d['anteckningar']))
        self.assertEqual(d['uppgifter'], {}, 'ägarens anteckningar blir aldrig kundens uppgifter')
        (s2, _, j2), _ = self.ny(operation=data['operation'])
        self.assertEqual((s2, j2['arende'], j2['nyckel']), (200, j['arende'], None), 'samma operation: samma ärende, ingen ny nyckel')
        self.assertEqual(len(self.arende(j['arende'])['anteckningar']), 3, 'omförsöket lägger inte till anteckningarna igen')
        (s3, _, j3), _ = self.ny()
        self.assertEqual((s3, j3.get('arende')), (409, j['arende']), 'samma namn i ett andra fönster: den befintliga kunden')
        self.assertEqual(len(dash_lista(self.root)), 1)

    def test_riktig_kund_far_ingen_modellbudget_och_testflaggan_ar_vagens(self):
        (s, _, j), _ = self.ny(test=False, foretag='Bergs Elfirma')
        self.assertEqual((s, j['slug']), (200, 'bergs-elfirma'))
        d = self.arende(j['arende'])
        self.assertIs(d['fiktiv'], False)
        self.assertEqual(d['budget']['max_anrop'], 0)
        for kw, namn in (({'test': 'true'}, 'testflaggan som sträng'), ({'fiktiv': True}, 'okänt fält'), ({'foretag': ''}, 'tomt namn'),
                         ({'webbplats': 'javascript:alert(1)'}, 'fel schema'), ({'operation': 'x'}, 'operationen'), ({'syfte': 'x' * 2001}, 'för långt')):
            with self.subTest(namn):
                (s, _, _), _ = self.ny(**kw)
                self.assertEqual(s, 400)
        self.assertEqual(self.anropa('POST', '/api/desktop/ny-kund', {'foretag': 'X', 'test': True, 'operation': str(uuid.uuid4())},
                                     {'Origin': self.ursprung})[0], 403, 'utan nyckel och session')

    # --- intervjun ---

    def intervju(self, eid, handling, data):
        return self.nyckelpost('/api/desktop/intervju/%s/%s' % (eid, handling), data)

    def test_intervjun_antecknar_kundens_svar_och_koar_ai_bara_for_testkund(self):
        (_, _, t), _ = self.ny()
        d = self.arende(t['arende'])
        op = str(uuid.uuid4())
        s, _, j = self.intervju(t['arende'], 'svar', {'revision': d['revision'], 'operation': op, 'text': 'Vi bakar tårtor på beställning.'})
        self.assertEqual(s, 200, j)
        d2 = self.arende(t['arende'])
        m = d2['meddelanden'][-1]
        self.assertEqual((m['roll'], m['via'], m['person']), ('kund', 'agaren', 'agaren'), 'kundens ord, antecknade av ägaren')
        self.assertIn(m['id'], ks.kundkallor(d2), 'svaret är en kundkälla som AI:s förslag får bindas till')
        self.assertEqual(d2['modell']['status'], 'ko', 'testkunden med budget får ett köat AI-jobb')
        s, _, j2 = self.intervju(t['arende'], 'svar', {'revision': d['revision'], 'operation': op, 'text': 'Vi bakar tårtor på beställning.'})
        self.assertEqual((s, j2), (200, j), 'samma operation: samma svar, inget nytt meddelande')
        self.assertEqual(len(self.arende(t['arende'])['meddelanden']), 1)
        s, _, _ = self.intervju(t['arende'], 'svar', {'revision': d['revision'], 'operation': str(uuid.uuid4()), 'text': 'Annat'})
        self.assertEqual(s, 409, 'en äldre revision än ärendets nekas')
        (_, _, r), _ = self.ny(test=False, foretag='Bergs Elfirma')
        dr = self.arende(r['arende'])
        s, _, j = self.intervju(r['arende'], 'svar', {'revision': dr['revision'], 'operation': str(uuid.uuid4()), 'text': 'Vi installerar laddboxar.'})
        self.assertEqual(s, 200, j)
        self.assertEqual(self.arende(r['arende'])['modell']['status'], 'avstangd', 'en verklig kund får ingen kö som aldrig töms')

    def test_rattelse_av_ai_antagande_och_sent_ai_svar(self):
        (_, _, t), _ = self.ny()
        db = ks.Lager(self.root / 'underlag' / 'kundstart')
        d = db.internt(t['arende'])
        self.intervju(t['arende'], 'svar', {'revision': d['revision'], 'operation': str(uuid.uuid4()), 'text': 'Kunderna är mest privatpersoner.'})
        jobb = db.ta_jobb('prov', lease=60, modell='attrapp')
        kalla = next(x['id'] for x in db.internt(t['arende'])['meddelanden'] if x['roll'] == 'kund')
        svar = {'text': 'Vilka beställer oftast?', 'forslag': [{'id': 'f' * 32, 'amne': 'B', 'text': 'Kunderna är företag.', 'kunskap': 'tolkning', 'kallor': [kalla]}],
                'fragor': []}
        self.assertTrue(db.modellsvar(jobb, svar))
        d = db.internt(t['arende'])
        s, _, j = self.intervju(t['arende'], 'rattelse', {'revision': d['revision'], 'operation': str(uuid.uuid4()), 'text': 'Kunderna är privatpersoner.', 'amne': 'B',
                                                          'forslag': 'f' * 32})
        self.assertEqual(s, 200, j)
        d = db.internt(t['arende'])
        self.assertEqual(d['forslag']['f' * 32]['bestallning'], 'rattat')
        u = [x for x in d['uppgifter'].values() if x.get('ersatter_forslag') == 'f' * 32]
        self.assertEqual([(x['kunskap'], x['text']) for x in u], [('agarens_rattelse', 'Kunderna är privatpersoner.')])
        # ett AI-svar som tagits före rättelsen skriver aldrig över den: jobbets revision är äldre än ärendets
        gammalt = db.ta_jobb('prov', lease=60, modell='attrapp')
        self.intervju(t['arende'], 'rattelse', {'revision': d['revision'], 'operation': str(uuid.uuid4()), 'text': 'Privatpersoner och några bostadsrättsföreningar.',
                                               'amne': 'B', 'uppgift': u[0]['id']})
        self.assertFalse(db.modellsvar(gammalt, {'text': 'sent', 'forslag': [], 'fragor': []}), 'det sena svaret ersätts')
        self.assertEqual(db.internt(t['arende'])['uppgifter'][u[0]['id']]['text'], 'Privatpersoner och några bostadsrättsföreningar.')
        s, _, _ = self.intervju(t['arende'], 'rattelse', {'revision': db.internt(t['arende'])['revision'], 'operation': str(uuid.uuid4()), 'text': 'x', 'amne': 'Z'})
        self.assertEqual(s, 400, 'okänt ämne')

    def test_ai_turen_startar_bara_for_testkund_med_kat_svar(self):
        import subprocess
        (_, _, t), _ = self.ny()
        (_, _, r), _ = self.ny(test=False, foretag='Bergs Elfirma')
        startade = []

        class Falsk:
            pid = 4242

            def poll(self):
                return None
        with patch.object(subprocess, 'Popen', lambda *a, **k: startade.append(a[0]) or Falsk()), patch.dict(desktop._AI, clear=True):
            self.assertEqual(self.intervju(t['arende'], 'ai', {})[0], 400, 'inget svar väntar')
            d = self.arende(t['arende'])
            self.intervju(t['arende'], 'svar', {'revision': d['revision'], 'operation': str(uuid.uuid4()), 'text': 'Hej'})
            s, _, j = self.intervju(t['arende'], 'ai', {})
            self.assertEqual((s, j['startad']), (200, True), j)
            self.assertIn('--live-cli', startade[0])
            self.assertTrue(startade[0][2].endswith('kontroller/kundstart_modell.py'))
            s, _, j = self.intervju(t['arende'], 'ai', {})
            self.assertEqual((s, j['startad'], j['pagar']), (200, False, True), 'en tur åt gången per ärende')
            self.assertEqual(self.intervju(r['arende'], 'ai', {})[0], 400, 'en verklig kund startar ingen AI-tur')
        self.assertEqual(len(startade), 1)

    def test_oversikten_samlar_en_kund_och_haller_isar_testkunder(self):
        (_, _, t), _ = self.ny()
        (_, _, r), _ = self.ny(test=False, foretag='Bergs Elfirma')
        # ett byggprojekt med samma slug som den riktiga kundens ärende: samma företag, inte en dubblett
        u = self.root / 'underlag' / 'bergs-elfirma'
        u.mkdir(parents=True)
        (u / 'BRIEF.md').write_text('# Brief\n', encoding='utf-8')
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Bergs Elfirma AB', 'fiktiv': False}), encoding='utf-8')
        with patch.object(dash, 'ab_oavgjord', return_value=False):
            s, _, d = self.anropa('GET', '/api/desktop/oversikt')
        self.assertEqual(s, 200, d)
        slugar = [k['slug'] for k in d['kunder']]
        self.assertEqual(sorted(slugar), ['bergs-elfirma', 'test-provbageriet-ange'])
        b = next(k for k in d['kunder'] if k['slug'] == 'bergs-elfirma')
        self.assertFalse(b['test'])
        self.assertEqual([a['id'] for a in b['arenden']], [r['arende']])
        self.assertIsNotNone(b['projekt'])
        self.assertEqual(b['namn'], 'Bergs Elfirma AB')
        tk = next(k for k in d['kunder'] if k['slug'] == 'test-provbageriet-ange')
        self.assertTrue(tk['test'])
        self.assertEqual(tk['namn'], 'Provbageriet Ånge', 'namnet ur ägarens anteckning när ingen VERKSAMHET.json finns')
        self.assertTrue(all(isinstance(k['senast'], str) for k in d['kunder']), 'tiderna jämförs som ISO')

    def test_pagaende_bara_motorns_egen_utcheckning(self):
        reg = self.root / 'korregister'
        reg.mkdir()
        egen = {'pid': os.getpid(), 'vad': 'arbetare', 'utcheckning': str(self.root), 'slug': 'kund-a', 'pstart': korregister.startad(os.getpid())}
        annan = dict(egen, utcheckning='/tmp/en-annan-utcheckning', slug='kund-b')
        prov = dict(egen, vad='rokprov', slug=None)
        for i, p in enumerate((egen, annan, prov)):
            (reg / ('%d-%d.json' % (os.getpid(), i))).write_text(json.dumps(p), encoding='utf-8')
        with patch.object(korregister, 'KATALOG', reg):
            s, _, j = self.anropa('GET', '/api/desktop/pagaende')
        self.assertEqual(s, 200)
        self.assertEqual([p['slug'] for p in j['pagaende']], ['kund-a'])

    def test_portalens_filer_och_ui_versionen(self):
        s, r, _ = self.anropa('GET', '/portal.js')
        self.assertEqual((s, r.getheader('Content-Type').split(';')[0]), (200, 'text/javascript'))
        self.assertEqual(self.anropa('GET', '/portal.css')[0], 200)
        index = (Path(dash.__file__).parent / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<script src="/portal.js"></script>', index)
        kat = self.root / 'ui'
        kat.mkdir()
        (kat / 'index.html').write_text('a', encoding='utf-8')
        v1 = desktop.ui_version(kat)
        (kat / 'portal.js').write_text('b', encoding='utf-8')
        self.assertNotEqual(v1, desktop.ui_version(kat), 'en ändrad portalfil ger en ny UI-version')


def dash_lista(root):
    import kundstart_agare
    return kundstart_agare.lista(root)['arenden']


if __name__ == '__main__':
    unittest.main(verbosity=1)
