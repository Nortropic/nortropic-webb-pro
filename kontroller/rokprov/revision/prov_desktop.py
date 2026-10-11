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

    def test_material_ur_finder_samma_provning_som_kundens_bilaga(self):
        import base64
        (_, _, t), _ = self.ny()
        d = self.arende(t['arende'])
        png = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')
        op = str(uuid.uuid4())
        data = {'revision': d['revision'], 'operation': op, 'namn': 'skylt.png', 'typ': 'image/png', 'data': base64.b64encode(png).decode()}
        s, _, j = self.intervju(t['arende'], 'material', data)
        self.assertEqual(s, 200, j)
        self.assertEqual((j['material']['person'], j['material']['lasning'], j['material']['rattighet']), ('agaren', 'inte_last', 'okand'))
        self.assertEqual(self.intervju(t['arende'], 'material', data)[2], j, 'samma operation: samma svar')
        d = self.arende(t['arende'])
        for fel, namn in (({'typ': 'image/png', 'data': base64.b64encode(b'GIF89a...').decode()}, 'signaturen stämmer inte'),
                          ({'typ': 'text/html', 'data': base64.b64encode(b'<script>').decode()}, 'html är ingen tillåten typ'),
                          ({'namn': '../x.png'}, 'sökväg i namnet'), ({'data': 'inte base64!'}, 'trasig överföring')):
            with self.subTest(namn):
                s, _, _ = self.intervju(t['arende'], 'material', dict(data, revision=d['revision'], operation=str(uuid.uuid4()), **fel))
                self.assertEqual(s, 400)
        self.assertEqual(len(self.arende(t['arende'])['material']), 1)

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
            self.assertEqual(startade[0][startade[0].index('--arende') + 1], t['arende'], 'arbetaren tar bara det här ärendets jobb')
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

    def test_leveransen_sager_inte_publicerad_utan_observerad_trafik(self):
        u = self.root / 'underlag' / 'testdata-lev'
        u.mkdir(parents=True)
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Leveransprovet (testdata)', 'fiktiv': True}), encoding='utf-8')
        lev = self.root / 'kunder' / 'testdata-lev' / 'leverans'
        lev.mkdir(parents=True)
        (lev / 'PREVIEW-1.json').write_text(json.dumps({'status': 'klar', 'tid': '2026-10-10T10:00:00Z', 'version_id': 'v1'}), encoding='utf-8')
        s, _, d = self.anropa('GET', '/api/desktop/leverans/testdata-lev')
        self.assertEqual(s, 200, d)
        self.assertTrue(d['test'])
        self.assertFalse(d['publicerad'], 'en förhandsvisning är ingen publicering')
        self.assertEqual(d['forvaltning']['analys']['lage'], 'ej_ansluten')
        self.assertEqual([k['slag'] for k in d['kvitton']], ['PREVIEW'])
        self.assertEqual(self.anropa('GET', '/api/desktop/leverans/x--forhandsvisning')[0], 400)

    # --- granskningens rättelser (separat granskning 2026-10-10) ---

    def test_skuggad_kaka_och_utloggningssidan(self):
        kaka, _ = self.session()
        vag = '/api/finns-inte-efter-sparren'
        namn = 'nwp_session_%d' % self.port
        skuggad = '%s=forhandsvisningens-varde; %s' % (namn, kaka)  # en längre sökväg från en förhandsvisning skickas först
        self.assertNotEqual(self.anropa('POST', vag, {}, {'Cookie': skuggad, 'Origin': self.ursprung})[0], 403, 'varje värde prövas')
        s, r, _ = self.anropa('GET', '/desktop/last', huvud={'Cookie': kaka})
        self.assertEqual(s, 200)
        self.assertIsNone(r.getheader('Set-Cookie'), 'ett GET (en bild, en iframe) raderar aldrig sessionen')
        self.assertNotEqual(self.anropa('POST', vag, {}, {'Cookie': kaka, 'Origin': self.ursprung})[0], 403)
        andra, _ = self.session()
        self.assertEqual(self.anropa('POST', '/api/desktop/utloggning', {}, {'X-Nyckel': NYCKEL, 'Origin': self.ursprung})[0], 200)
        self.assertNotEqual(self.anropa('POST', vag, {}, {'Cookie': andra, 'Origin': self.ursprung})[0], 403,
                            'en utloggning utan giltig kaka återkallar ingen annan session')
        self.assertNotIn('Max-Age=', self.session()[1], 'en sessionskaka utan Max-Age')

    def test_appens_bevis_i_stallet_for_nyckeln(self):
        import hashlib as hl, hmac as hm
        _, _, j = self.anropa('GET', '/api/desktop/identitet?utmaning=' + 'ab' * 16)
        kropp = json.dumps({'instans': j['instans']}).encode()

        def bevis(vag, kropp, ts=None, nonce=None):
            ts = str(int(ts if ts is not None else time.time()))
            nonce = nonce or os.urandom(16).hex()
            msg = 'nwp-desktop/1 skriv\n%s\n%s\n%s\n%s' % (ts, nonce, vag, hl.sha256(kropp).hexdigest())
            return '%s.%s.%s' % (ts, nonce, hm.new(NYCKEL.encode(), msg.encode(), hl.sha256).hexdigest())

        def post(vag, b, kropp_=kropp):
            c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
            try:
                c.request('POST', vag, kropp_, {'Origin': self.ursprung, 'X-Desktop-Bevis': b, 'Content-Type': 'application/json'})
                r = c.getresponse()
                return r.status, json.loads(r.read() or b'{}')
            finally:
                c.close()
        b = bevis('/api/desktop/session', kropp)
        s, k = post('/api/desktop/session', b)
        self.assertEqual(s, 200, k)
        self.assertIn('kod', k)
        self.assertEqual(post('/api/desktop/session', b)[0], 403, 'samma nonce en gång')
        self.assertEqual(post('/api/desktop/session', bevis('/api/desktop/session', b'{}'))[0], 403, 'beviset gäller kroppen')
        self.assertEqual(post('/api/desktop/session', bevis('/api/desktop/las', kropp))[0], 403, 'beviset gäller vägen')
        self.assertEqual(post('/api/desktop/session', bevis('/api/desktop/session', kropp, ts=time.time() - 600))[0], 403, 'för gammal tid')
        self.assertEqual(post('/api/desktop/session', 'skrap')[0], 403)
        self.assertEqual(post('/api/kalibrering/x', bevis('/api/kalibrering/x', kropp))[0], 403, 'beviset gäller bara appens två vägar')
        self.assertEqual(post('/api/desktop/las', bevis('/api/desktop/las', b'{}'), b'{}')[0], 200)

    def test_testslug_och_riktig_slug_krockar_aldrig(self):
        (s, _, r), _ = self.ny(test=False, foretag='Test Bageriet AB')
        self.assertEqual((s, r['slug']), (200, 'k-test-bageriet-ab'), r)
        (s, _, t), _ = self.ny(test=True, foretag='Bageriet AB')
        self.assertEqual((s, t['slug']), (200, 'test-bageriet-ab'))
        self.assertIs(self.arende(r['arende'])['fiktiv'], False)
        self.assertIs(self.arende(t['arende'])['fiktiv'], True)
        (s, _, j), _ = self.ny(foretag='Hemlig ' + 'sk-ant-' + 'a' * 40)
        self.assertEqual(s, 400, 'en text som ser ut som en hemlighet nekas före skapandet, inte efter')
        self.assertEqual(len(dash_lista(self.root)), 2)

    def test_ai_jobbet_tas_bara_ur_sitt_arende(self):
        db = ks.Lager(self.root / 'underlag' / 'kundstart')
        (_, _, a), _ = self.ny(foretag='Kund A')
        (_, _, b), _ = self.ny(foretag='Kund B')
        for eid in (a['arende'], b['arende']):
            d = db.internt(eid)
            self.intervju(eid, 'svar', {'revision': d['revision'], 'operation': str(uuid.uuid4()), 'text': 'Svar för ' + eid})
        jobb = db.ta_jobb('prov', lease=60, modell='attrapp', arende=b['arende'])
        self.assertEqual(jobb['arende'], b['arende'])
        self.assertEqual(db.internt(a['arende'])['modell']['status'], 'ko', 'det andra ärendets jobb rörs inte')
        self.assertEqual(db.internt(a['arende'])['budget']['anrop'], 0)

    def test_ovantat_fel_blir_ett_svar(self):
        import kundstart_agare
        (_, _, t), _ = self.ny()
        with patch.object(kundstart_agare, 'intervju', side_effect=RuntimeError('provfel')):
            s, _, j = self.intervju(t['arende'], 'svar', {'revision': 1, 'operation': str(uuid.uuid4()), 'text': 'x'})
        self.assertEqual((s, j['fel']), (500, 'RuntimeError: provfel'))
        self.assertEqual(self.nyckelpost('/api/desktop/session', [1, 2])[0], 400, 'en lista i stället för ett objekt')

    def test_kommentarer_binds_till_version_och_bild_och_bestalls_som_uppdrag(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import arbetsyta_fixtur
        import atelje
        import observation
        import meddelanden
        slug = 'testdata-kommentarer'
        for m in (atelje,):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.multiple(observation, ROOT=self.root, UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.object(meddelanden, 'UNDERLAG', self.root / 'underlag'))
        self.stack.enter_context(patch.object(dash, 'ab_oavgjord', return_value=False))
        arbetsyta_fixtur.bygg(self.root, slug, None, med_sajt=False)
        # utan mallsajten har fixturen ingen bevarad version: kandidaten får en, som fotograferingen skulle ha gett
        stf = self.root / 'underlag' / slug / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json'
        st = json.loads(stf.read_text(encoding='utf-8'))
        st.update(version='ab' * 32, fotograferad='2026-10-09T05:30:00Z')
        stf.write_text(json.dumps(st), encoding='utf-8')
        b = self.root / 'underlag' / slug / 'atelje' / 'kandidater' / 'k01' / 'bilder' / 'start' / 'vy-390-forsta.png'
        b.parent.mkdir(parents=True, exist_ok=True)
        b.write_bytes(bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                                    '1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082'))
        s, _, d = self.anropa('GET', '/api/desktop/kommentarer/' + slug)
        self.assertEqual(s, 200, d)
        k = next(x for x in d['kandidater'] if x['id'] == 'k01')
        self.assertIn('390', k['bilder'])
        vag = '/api/desktop/kommentarer/' + slug
        cid = str(uuid.uuid4())
        ny = {'handling': 'ny', 'id': cid, 'kandidat': 'k01', 'version': k['version'], 'bredd': '390', 'bild': k['bilder']['390'], 'bild_sha': k['sha']['390'],
              'x': 0.25, 'y': 0.5, 'text': 'Rubriken bryts fel i mobilen.'}
        self.assertEqual(self.nyckelpost(vag, dict(ny, version='0' * 64))[0], 409, 'en annan version än kandidatens')
        self.assertEqual(self.nyckelpost(vag, dict(ny, bild_sha='0' * 64))[0], 409, 'en annan bild än ögonblicksbilden')
        for fel in ({'x': 0.3, 'y': None}, {'x': 1.5}, {'x': True, 'y': 0.2}, {'bredd': '768'}, {'text': ''}, {'id': 'x'}):
            with self.subTest(fel=fel):
                self.assertEqual(self.nyckelpost(vag, dict(ny, **fel))[0], 400)
        s, _, j = self.nyckelpost(vag, ny)
        self.assertEqual((s, j['upprepat'], j['kommentar']['status']), (200, False, 'oppen'))
        self.assertEqual(self.nyckelpost(vag, ny)[2]['upprepat'], True, 'samma id och innehåll: samma kommentar')
        self.assertEqual(self.nyckelpost(vag, dict(ny, text='annat'))[0], 409, 'samma id med annan text')
        hela = dict(ny, id=str(uuid.uuid4()), x=None, y=None, text='Kontaktvägen syns för sent.')
        self.assertEqual(self.nyckelpost(vag, hela)[0], 200, 'en kommentar på hela sidan utan punkt (alternativ till att peka)')
        self.assertEqual(self.nyckelpost(vag, {'handling': 'svara', 'id': cid, 'text': 'Gäller bara 390.'})[0], 200)
        self.assertEqual(self.nyckelpost(vag, {'handling': 'status', 'id': cid, 'status': 'lost_verifierad'})[0], 409,
                         'verifierat löst kräver en nyare version än den kommenterade')
        self.assertEqual(self.nyckelpost(vag, {'handling': 'bestall', 'ids': [cid, hela['id']], 'andring_id': 'x'})[0], 400)
        s, _, j = self.nyckelpost(vag, {'handling': 'bestall', 'ids': [cid, hela['id']], 'andring_id': 'p' + 'a' * 40})
        self.assertEqual((s, sorted(j['bestallda'])), (200, sorted([cid, hela['id']])))
        s, _, d = self.anropa('GET', vag)
        c = {x['id']: x for x in d['kommentarer']}
        self.assertEqual((c[cid]['status'], c[cid]['andring_id'], c[cid]['svar'][0]['text']), ('bestalld', 'p' + 'a' * 40, 'Gäller bara 390.'))
        self.assertFalse(c[cid]['inaktuell'])
        self.assertEqual(self.nyckelpost(vag, {'handling': 'bestall', 'ids': [cid], 'andring_id': 'p' + 'b' * 40})[0], 409, 'redan beställd i ett annat uppdrag')
        self.assertEqual(self.anropa('POST', vag, ny, {'Origin': self.ursprung})[0], 403, 'utan nyckel och session')
        self.assertEqual(self.anropa('GET', '/api/desktop/kommentarer/finns-inte')[0], 404)

    def test_utgavan_serveras_bara_nar_den_finns(self):
        self.assertEqual(self.anropa('GET', '/desktop/uppdatering/utgava')[0], 404)
        kat = self.root / 'desktop' / 'utgava'
        kat.mkdir(parents=True)
        (kat / 'Nortropic.app.tar.gz').write_bytes(b'\x1f\x8b provartefakt')
        (kat / 'Nortropic.app.tar.gz.sig').write_text('c2lnbmF0dXI=\n', encoding='utf-8')
        (kat / 'utgava.json').write_text(json.dumps({'version': '0.2.0', 'kontrakt': 'desktop/1', 'noter': 'prov'}), encoding='utf-8')
        s, _, j = self.anropa('GET', '/desktop/uppdatering/utgava')
        self.assertEqual((s, j['version'], j['kontrakt'], j['signatur']), (200, '0.2.0', 'desktop/1', 'c2lnbmF0dXI='))
        s, r, _ = self.anropa('GET', '/desktop/uppdatering/artefakt')
        self.assertEqual((s, r.getheader('Content-Type')), (200, 'application/gzip'))

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
        v2 = desktop.ui_version(kat)
        self.assertNotEqual(v1, v2, 'en ändrad portalfil ger en ny UI-version')
        (kat / 'studio.js').write_text('c', encoding='utf-8')
        self.assertNotEqual(v2, desktop.ui_version(kat), 'en ändrad studiofil ger en ny UI-version (designstudion 2026-10-11)')
        self.assertIn('<script src="/studio.js"></script>', index)
        self.assertEqual(self.anropa('GET', '/studio.js')[0], 200)
        self.assertEqual(self.anropa('GET', '/studio.css')[0], 200)


def dash_lista(root):
    import kundstart_agare
    return kundstart_agare.lista(root)['arenden']


# en 400 × 300 px PNG (ljusgrå yta med en mörk rubrikrad), som en bevarad ögonblicksbild att peka i
def _provbild():
    import struct
    import zlib
    b, h = 400, 300
    rader = b''.join(b'\x00' + (b'\x2a\x2e\x48' * b if y < 40 else b'\xf0\xf1\xf5' * b) for y in range(h))
    def bit(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + bit(b'IHDR', struct.pack('>IIBBBBB', b, h, 8, 2, 0, 0, 0)) + bit(b'IDAT', zlib.compress(rader)) + bit(b'IEND', b'')


PROVBILD = _provbild()


def provserver():
    """Motorns riktiga hanterare i en provrot för portalens webbläsarprov (prov_portal_webb.mjs): ingen nyckel krävs, ingen
    modell, aldrig repots underlag eller kunder."""
    import signal

    def stopp(*_):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stopp)
    with korregister.egen_tmp_med('nwp-desktop-', 'portalens webbläsarprov') as tmp:
        rot = Path(tmp).resolve()
        (rot / 'underlag').mkdir()
        (rot / 'kunder').mkdir()
        import atelje
        import exportera
        dash.ROOT, dash.UNDERLAG, dash.KUNDER = rot, rot / 'underlag', rot / 'kunder'
        atelje.ROOT, atelje.UNDERLAG, atelje.KUNDER = rot, rot / 'underlag', rot / 'kunder'
        exportera.ROOT, exportera.UNDERLAG, exportera.KUNDER = rot, rot / 'underlag', rot / 'kunder'
        os.environ['NWP_NYCKELINTAG'] = str(rot / 'nyckelintag')
        os.environ['NWP_CLOUDFLARE_FIL'] = str(rot / 'saknas' / 'cloudflare.env')
        # en fiktiv kund i skapandeflödet med en bevarad ögonblicksbild, för Förfiningens kommentarer
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import arbetsyta_fixtur
        import observation
        import meddelanden
        observation.ROOT, observation.UNDERLAG = rot, rot / 'underlag'
        meddelanden.UNDERLAG = rot / 'underlag'
        dash.ab_oavgjord = lambda slug: False
        arbetsyta_fixtur.bygg(rot, 'testdata-kommentarer', None, med_sajt=False)
        k01 = rot / 'underlag' / 'testdata-kommentarer' / 'atelje' / 'kandidater' / 'k01'
        st = json.loads((k01 / 'STATUS.json').read_text(encoding='utf-8'))
        st.update(version='ab' * 32, fotograferad='2026-10-09T05:30:00Z')
        (k01 / 'STATUS.json').write_text(json.dumps(st), encoding='utf-8')
        bild = k01 / 'bilder' / 'start' / 'vy-1440-forsta.png'
        bild.parent.mkdir(parents=True, exist_ok=True)
        bild.write_bytes(PROVBILD)
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        dash.VARD['tillatna'] = {'127.0.0.1:%d' % srv.server_address[1]}
        desktop.konfigurera(rot, srv.server_address[1])
        print(json.dumps({'port': srv.server_address[1]}), flush=True)
        try:
            srv.serve_forever()
        finally:
            srv.server_close()


if __name__ == '__main__':
    if '--provserver' in sys.argv:
        provserver()
    else:
        unittest.main(verbosity=1)
