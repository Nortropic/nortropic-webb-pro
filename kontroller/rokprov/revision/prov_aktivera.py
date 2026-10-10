#!/usr/bin/env python3
"""Aktiveringen (kontroller/aktivera.py; ägarens tillägg 2026-10-10, punkt 2) mot en märkt attrapp av Wrangler, enbart
syntetiska uppgifter och inget nät: torrkörningen listar stegen och vad som saknas utan sidoeffekter; körningen kräver
ägarens mandat för just den planen, och mandatet gäller en körning; D1 och R2 skapas med EU-jurisdiktion bara under
kundens egna namn och bara om de saknas; driftvärdena skrivs ur nyckelintaget med avsändaren på routing-domänen; en ny
export och D1-schemat; nycklarna läggs först när produktionens Worker finns, med nyckeln bara på Wranglers stdin, och
rotation och återkallelse blir nya steg; ett okänt utfall stoppar och stäms av före ett nytt försök; fel kund (en databas
som inte är kundens, ett mandat för en annan kund) och en fiktiv verksamhet nekas; dubbelstart nekas av kundens lås; och
nyckeln syns aldrig i kvitto, mandat, torrkörning eller utskrift."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import aktivera  # noqa: E402
import atelje  # noqa: E402
import exportera  # noqa: E402
import korregister  # noqa: E402
import kundrepo  # noqa: E402
import nyckelintag as ni  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SLUG = 'prov-aktiv'
NYCKEL = 'xkeysib-SYNTETISK-AKTIVERINGSNYCKEL-0001'
NYCKEL2 = 'xkeysib-SYNTETISK-AKTIVERINGSNYCKEL-0002'
UUID = '0f0e0d0c-0b0a-4908-8706-050403020100'
ANNAN = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
START = 'prov-start-0001'


class Wrangler:
    """Märkt attrapp: protokollför varje anrop (utan stdin) och svarar som Wrangler för just de här kommandona."""
    def __init__(self):
        self.anrop, self.stdin, self.d1, self.r2, self.hemligheter, self.fel = [], [], {}, set(), set(), {}
        self.fore = None  # anropas med argumenten före svaret (provet läser då kvittot på disken)

    def fabrik(self, slug, konto, tmp):
        return self

    def __call__(self, args, stdin=None):
        self.anrop.append(list(args)); self.stdin.append(stdin)
        if self.fore:
            self.fore(args)
        nyckel = ' '.join(args[:3])
        if nyckel in self.fel:
            return self.fel[nyckel]
        if args[:2] == ['d1', 'list']:
            return 0, json.dumps([{'name': n, 'uuid': u} for n, u in self.d1.items()])
        if args[:2] == ['d1', 'create']:
            self.d1[args[2]] = UUID
            return 0, '✅ Successfully created DB "%s"\n{"d1_databases": [{"binding": "DB", "database_name": "%s", "database_id": "%s"}]}' % (args[2], args[2], UUID)
        if args[:3] == ['r2', 'bucket', 'list']:
            return 0, '\n'.join('name: %s' % b for b in sorted(self.r2))
        if args[:3] == ['r2', 'bucket', 'create']:
            self.r2.add(args[3]); return 0, 'Created bucket %s with default storage class' % args[3]
        if args[:2] == ['d1', 'migrations']:
            return 0, 'Migrations applied'
        if args[:2] == ['secret', 'put']:
            self.hemligheter.add(args[2]); return 0, 'Success! Uploaded secret %s' % args[2]
        if args[:2] == ['secret', 'delete']:
            self.hemligheter.discard(args[2]); return 0, 'Success! Deleted secret %s' % args[2]
        if args[:2] == ['secret', 'list']:
            return 0, json.dumps([{'name': h, 'type': 'secret_text'} for h in sorted(self.hemligheter)])
        return 1, 'okänt kommando i attrappen'


class Aktivera(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-aktivering-', 'aktiveringens prov'))).resolve()
        self.root = self.tmp / 'repo'
        for d in ('underlag/%s' % SLUG, 'kunder/%s/kundrepo' % SLUG, 'mall/leverans/migrations'):
            (self.root / d).mkdir(parents=True)
        for m in ('0001_forfragningar.sql', '0002_kundregister.sql'):
            (self.root / 'mall/leverans/migrations' / m).write_text('-- prov\n')
        self.verksamhet(fiktiv=False)
        (self.root / 'kunder' / SLUG / 'KUNDREPO.json').write_text(json.dumps({'schema': 1, 'slug': SLUG}))
        (self.root / 'kunder' / SLUG / 'kundrepo' / 'wrangler.jsonc').write_text('{"name": "kund-%s", "database_id": "AKTIVERAS-VID-LANSERING"}' % SLUG)
        konto = self.tmp / 'cloudflare.env'
        konto.write_text('CLOUDFLARE_API_TOKEN=SYNTETISK-KONTOTOKEN-0000\nCLOUDFLARE_ACCOUNT_ID=%s\nCLOUDFLARE_WORKERS_UNDERDOMAN=prov\n' % ('c' * 32))
        konto.chmod(0o600)
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.multiple(exportera, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.dict(os.environ, {'NWP_NYCKELINTAG': str(self.tmp / 'intag'), 'NWP_CLOUDFLARE_FIL': str(konto),
                                                         'NWP_FLODE_START_ID': START}))
        self.valda = ['k02-cloudflare-workers', 'k03-formular-worker', 'k04-cloudflare-epost', 'k14-brevo-dubbel']
        self.stack.enter_context(patch.object(aktivera, 'valda_paket', lambda slug: self.valda))
        self.export = None
        self.stack.enter_context(patch.object(exportera, 'aktuell', lambda slug: self.export))
        self.w = Wrangler()

    def verksamhet(self, **v):
        (self.root / 'underlag' / SLUG / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Prov', **v}))

    def intag(self):
        ni.lamna(SLUG, 'epost', None, {'mottagare': 'post@kund.example.invalid'}, 'dashboard')
        ni.lamna(SLUG, 'brevo', NYCKEL, {'lista': '12', 'mall': '7'}, 'kund')

    def exportera_fn(self, slug):
        # exportens wrangler.jsonc: mallens, med driftvärdena (exportera.wrangler_namn, som den riktiga exporten)
        drift = json.loads((self.root / 'underlag' / slug / 'CLOUDFLARE.json').read_text())
        (self.root / 'kunder' / slug / 'kundrepo' / 'wrangler.jsonc').write_text(
            exportera.wrangler_namn((exportera.LEVERANS / 'wrangler.jsonc').read_text(encoding='utf-8'), slug, drift))
        self.export = {'ok': True, 'aktuell': True, 'id': 'E2'}
        return {'ok': True, 'id': 'E2'}

    def mandat(self, start=START):
        return aktivera.aktiveringsmandat(SLUG, 'dashboard', aktivera.torr(SLUG)['plan_sha256'], start)

    def release(self):
        (kundrepo.leveransdir(SLUG) / 'RELEASE-20261010T120000Z-0000.json').write_text(json.dumps({'status': 'klar', 'id': 'RELEASE-x', 'tid': '2026-10-10T12:00:00Z'}))

    def kor(self):
        return aktivera.kor(SLUG, wrangler=self.w.fabrik, exportera_fn=self.exportera_fn)

    def status(self, t):
        return {s['id']: s['status'] for s in t['steg']}

    def filer(self):
        return sorted((str(p.relative_to(self.tmp)), p.read_bytes()) for p in self.tmp.rglob('*') if p.is_file())

    def test_torrkorningen_listar_och_saknar_utan_sidoeffekter(self):
        fore = self.filer()
        t = aktivera.torr(SLUG)
        self.assertEqual(self.filer(), fore, 'torrkörningen skriver ingenting')
        self.assertEqual(self.status(t), {'konto': 'klar', 'd1': 'gors', 'r2': 'gors', 'driftvarden': 'saknas', 'export': 'gors',
                                          'migreringar': 'gors', 'hemlighet:BREVO_API_NYCKEL': 'saknas'})
        self.assertFalse(t['kan_koras'])
        self.assertTrue(any('mottagare' in x for x in t['saknas']) and any('Brevo' in x for x in t['saknas']), t['saknas'])
        self.assertIn('wrangler d1 create kund-%s-forfragningar --jurisdiction eu' % SLUG, [s['kommando'] for s in t['steg']])
        self.assertEqual(self.w.anrop, [], 'inget nät')
        self.intag()
        t = aktivera.torr(SLUG)
        self.assertEqual(self.status(t)['hemlighet:BREVO_API_NYCKEL'], 'vantar', 'före första releasen läggs ingen nyckel')
        self.assertTrue(t['kan_koras'], (t['hinder'], t['saknas']))

    def test_mandatet_kravs_och_galler_en_korning(self):
        self.intag()
        r = self.kor()
        self.assertEqual(r['status'], 'vantar_pa_mandat'); self.assertEqual(self.w.anrop, [])
        with self.assertRaises(aktivera.Fel):
            aktivera.aktiveringsmandat(SLUG, 'session', aktivera.torr(SLUG)['plan_sha256'], START)
        with self.assertRaises(aktivera.Fel):
            aktivera.aktiveringsmandat(SLUG, 'dashboard', '0' * 64, START)
        with self.assertRaises(aktivera.Fel):
            aktivera.aktiveringsmandat(SLUG, 'dashboard', aktivera.torr(SLUG)['plan_sha256'], None)
        # mandatet gäller klickets start och en kort tid: en annan start eller ett gammalt klick kör ingenting
        self.mandat('en-annan-start-0002')
        self.assertEqual(self.kor()['status'], 'vantar_pa_mandat'); self.assertEqual(self.w.anrop, [])
        m = self.mandat(); m['giltig_till'] = 1; aktivera.mandatfil(SLUG).write_text(json.dumps(m))
        self.assertEqual(self.kor()['status'], 'vantar_pa_mandat'); self.assertEqual(self.w.anrop, [])
        self.mandat()
        r = self.kor()
        self.assertEqual(r['status'], 'klar', r)
        self.assertEqual([a[:3] for a in self.w.anrop], [['d1', 'list', '--json'], ['d1', 'create', 'kund-%s-forfragningar' % SLUG], ['r2', 'bucket', 'list'],
                                                         ['r2', 'bucket', 'create'], ['d1', 'list', '--json'], ['d1', 'migrations', 'apply']])
        self.assertIn(['d1', 'create', 'kund-%s-forfragningar' % SLUG, '--jurisdiction', 'eu'], self.w.anrop)
        self.assertIn(['r2', 'bucket', 'create', 'kund-%s-bilagor' % SLUG, '--jurisdiction', 'eu'], self.w.anrop)
        drift = json.loads((self.root / 'underlag' / SLUG / 'CLOUDFLARE.json').read_text())
        self.assertEqual(drift, {'database_id': UUID, 'forfragan_till': 'post@kund.example.invalid', 'forfragan_fran': '%s@notis.nortropic.se' % SLUG,
                                 'nyhetsbrev_lista': '12', 'nyhetsbrev_mall': '7'})
        self.assertEqual(json.loads(aktivera.mandatfil(SLUG).read_text())['anvant_av'], r['id'])
        self.w.anrop.clear(); self.w.stdin.clear()
        self.assertEqual(self.kor()['status'], 'inget_att_gora', 'allt gjort; mandatet är förbrukat')
        self.assertEqual(self.w.anrop, [])
        t = aktivera.torr(SLUG)
        self.assertEqual(self.status(t), {'konto': 'klar', 'd1': 'klar', 'r2': 'klar', 'driftvarden': 'klar', 'export': 'klar',
                                          'migreringar': 'klar', 'hemlighet:BREVO_API_NYCKEL': 'vantar'})

    def test_nycklar_efter_releasen_rotation_och_aterkallelse(self):
        self.intag(); self.mandat(); self.kor()
        self.release()
        t = aktivera.torr(SLUG)
        self.assertEqual(self.status(t)['hemlighet:BREVO_API_NYCKEL'], 'gors')
        self.mandat(); self.w.anrop.clear(); self.w.stdin.clear()
        r = self.kor()
        self.assertEqual(r['status'], 'klar', r)
        i = self.w.anrop.index(['secret', 'put', 'BREVO_API_NYCKEL', '--name', 'kund-%s' % SLUG])
        self.assertEqual(self.w.stdin[i], NYCKEL, 'nyckeln går bara på stdin')
        self.assertEqual(self.status(aktivera.torr(SLUG))['hemlighet:BREVO_API_NYCKEL'], 'klar')
        ni.lamna(SLUG, 'brevo', NYCKEL2)
        self.assertEqual(self.status(aktivera.torr(SLUG))['hemlighet:BREVO_API_NYCKEL'], 'gors', 'en ny nyckel är ett nytt steg')
        self.mandat(); self.kor()
        self.assertEqual(self.w.stdin[-1], NYCKEL2)
        ni.aterkalla(SLUG, 'brevo')
        t = aktivera.torr(SLUG)
        self.assertEqual(self.status(t)['hemlighet:BREVO_API_NYCKEL'], 'gors')
        self.assertIn('wrangler secret delete BREVO_API_NYCKEL', ' '.join(s['kommando'] or '' for s in t['steg']))
        # en borttagning som faller är inte gjord: steget står kvar
        self.mandat(); self.w.fel['secret delete BREVO_API_NYCKEL'] = (1, 'Error: Authentication error [code: 10000]')
        self.assertEqual(self.kor()['status'], 'fel')
        self.assertEqual(self.status(aktivera.torr(SLUG))['hemlighet:BREVO_API_NYCKEL'], 'gors', 'en misslyckad borttagning visas aldrig som klar')
        del self.w.fel['secret delete BREVO_API_NYCKEL']
        self.mandat(); self.kor()
        self.assertNotIn('BREVO_API_NYCKEL', self.w.hemligheter)
        self.assertEqual(self.status(aktivera.torr(SLUG))['hemlighet:BREVO_API_NYCKEL'], 'klar')
        # nyckeln syns aldrig utanför intaget och Wranglers stdin
        for f in self.root.rglob('*'):
            if f.is_file():
                self.assertNotIn(NYCKEL, f.read_text(errors='replace')); self.assertNotIn(NYCKEL2, f.read_text(errors='replace'))
        with contextlib.redirect_stdout(io.StringIO()) as ut:
            aktivera.main([SLUG])
        self.assertNotIn(NYCKEL2, ut.getvalue())
        self.assertNotIn('SYNTETISK-KONTOTOKEN', json.dumps([json.loads(f.read_text()) for f in kundrepo.leveransdir(SLUG).glob('*.json')]))

    def test_avvalt_paket_tar_bort_nyckeln_och_driftvardena(self):
        self.intag(); self.mandat(); self.kor(); self.release()
        self.mandat(); self.assertEqual(self.kor()['status'], 'klar')
        self.assertIn('BREVO_API_NYCKEL', self.w.hemligheter)
        self.valda = [p for p in self.valda if p != 'k14-brevo-dubbel']  # kunden har valt bort nyhetsbrevet
        t = aktivera.torr(SLUG)
        self.assertEqual({k: v for k, v in self.status(t).items() if v != 'klar'},
                         {'driftvarden': 'gors', 'export': 'gors', 'hemlighet:BREVO_API_NYCKEL': 'gors'}, t['steg'])
        self.assertIn('wrangler secret delete BREVO_API_NYCKEL', ' '.join(s['kommando'] or '' for s in t['steg']))
        self.mandat(); self.assertEqual(self.kor()['status'], 'klar')
        self.assertNotIn('BREVO_API_NYCKEL', self.w.hemligheter)
        drift = json.loads((self.root / 'underlag' / SLUG / 'CLOUDFLARE.json').read_text())
        self.assertNotIn('nyhetsbrev_lista', drift); self.assertNotIn('nyhetsbrev_mall', drift)
        self.assertNotIn('"NYHETSBREV_LISTA": "12"', (self.root / 'kunder' / SLUG / 'kundrepo' / 'wrangler.jsonc').read_text())
        t = aktivera.torr(SLUG)
        self.assertNotIn('hemlighet:BREVO_API_NYCKEL', self.status(t)); self.assertEqual(t['att_gora'], 0)

    def test_avbruten_korning_ar_okand_och_ompaket_skickas_om(self):
        self.intag(); self.mandat()
        pa_disken = []

        def las_kvittot(args):
            if args[:3] == ['r2', 'bucket', 'create']:
                k = json.loads(max(kundrepo.leveransdir(SLUG).glob('AKTIVERING-*.json'), key=lambda f: f.stat().st_mtime_ns).read_text())
                pa_disken.append((k['status'], k['steg'][-1]['id'], k['steg'][-1]['status']))
        self.w.fore = las_kvittot
        self.kor()
        self.assertEqual(pa_disken, [('osaker', 'r2', 'pagar')], 'under operationen säger kvittot okänt utfall')
        # en process som dör mitt i en put lämnar kvittot så; avstämningen ser steget som okänt och skickar om nyckeln
        self.release()
        krasch = {'schema': 1, 'id': 'AKTIVERING-20261010T130000Z-dead', 'typ': 'aktivering', 'slug': SLUG, 'tid': '2026-10-10T13:00:00Z',
                  'status': 'osaker', 'steg': [{'id': 'hemlighet:BREVO_API_NYCKEL', 'status': 'pagar', 'detalj': None}]}
        (kundrepo.leveransdir(SLUG) / (krasch['id'] + '.json')).write_text(json.dumps(krasch))
        self.assertTrue(any('okänt utfall' in h for h in aktivera.torr(SLUG)['hinder']))
        self.w.hemligheter.add('BREVO_API_NYCKEL')  # en äldre version finns: namnet i listan bevisar inte versionen
        self.w.fel['d1 list --json'] = (1, 'Error: 504 Gateway Timeout')
        a = aktivera.stam_av(SLUG, wrangler=self.w.fabrik)
        self.assertEqual(a['status'], 'klar', 'hemligheten stäms av utan D1-listan')
        self.assertEqual([(s['id'], s['status']) for s in a['steg']], [('hemlighet:BREVO_API_NYCKEL', 'avstamd_ingen')])
        self.assertIsNone(aktivera.osaker(SLUG))
        self.assertEqual(self.status(aktivera.torr(SLUG))['hemlighet:BREVO_API_NYCKEL'], 'gors', 'nyckeln skickas om')

    def test_avstamning_som_faller_stanger_inget(self):
        self.intag(); self.mandat()
        self.w.fel['r2 bucket create'] = (1, 'Error: 504 Gateway Timeout')
        self.assertEqual(self.kor()['status'], 'osaker', '504 är ett okänt utfall')
        self.w.fel['r2 bucket list'] = (1, 'Error: fetch failed')
        a = aktivera.stam_av(SLUG, wrangler=self.w.fabrik)
        self.assertEqual(a['status'], 'osaker'); self.assertEqual(a['steg'], [], 'en lista som faller är ingen slutsats')
        self.assertIsNotNone(aktivera.osaker(SLUG), 'en misslyckad avstämning lämnar utfallet okänt')
        # ett annat kvitto med samma id som avstämningen pekar på stänger inget: bara en lyckad avstämning gör det
        falsk = {'schema': 1, 'id': 'AKTIVERING-20261010T140000Z-beef', 'typ': 'aktivering', 'slug': SLUG, 'tid': '2026-10-10T14:00:00Z',
                 'status': 'hinder', 'avstammer': aktivera.osaker(SLUG)['id'], 'steg': []}
        (kundrepo.leveransdir(SLUG) / (falsk['id'] + '.json')).write_text(json.dumps(falsk))
        self.assertIsNotNone(aktivera.osaker(SLUG))
        del self.w.fel['r2 bucket list']
        self.assertEqual(aktivera.stam_av(SLUG, wrangler=self.w.fabrik)['status'], 'klar')
        self.assertIsNone(aktivera.osaker(SLUG))

    def test_exporten_i_korningen_under_kundens_las(self):
        import flodesstart
        with patch.object(exportera, '_exportera', return_value={'ok': True, 'id': 'E9'}) as ex:
            with flodesstart.las(atelje.ROOT, SLUG):  # kor håller låset; exporten tar det inte en gång till
                self.assertEqual(aktivera._exportera(SLUG), {'ok': True, 'id': 'E9'})
        ex.assert_called_once_with(SLUG, git=True)

    def test_kundstart_lases_i_lasläge_och_planens_hinder_stoppar(self):
        import sqlite3
        with patch.object(aktivera, 'planens_hinder', return_value=['ett val saknar accepterat erbjudande: k14-brevo-dubbel']):
            self.intag()
            t = aktivera.torr(SLUG)
            self.assertFalse(t['kan_koras']); self.assertIn('ett val saknar accepterat erbjudande: k14-brevo-dubbel', t['hinder'])
        with patch.object(aktivera, '_kundstart_plan', side_effect=sqlite3.OperationalError('database is locked')):
            t = aktivera.torr(SLUG, valda=None)
            self.assertFalse(t['kan_koras']); self.assertTrue(any('kunde inte läsas' in h for h in t['hinder']), t['hinder'])

    def test_slug_som_ar_en_forhandsvisning_nekas(self):
        with self.assertRaises(ValueError):
            kundrepo.identitet('kund-x-forhandsvisning'.replace('kund-', ''))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(aktivera.main(['x-forhandsvisning']), 2)

    def test_okant_utfall_stoppar_och_stams_av(self):
        self.intag(); self.mandat()
        self.w.fel['r2 bucket create'] = (124, 'tidsgränsen 300 s nåddes')
        r = self.kor()
        self.assertEqual(r['status'], 'osaker')
        self.assertEqual([s['id'] for s in r['steg']], ['d1', 'r2'], 'körningen stannar vid det okända utfallet')
        t = aktivera.torr(SLUG)
        self.assertFalse(t['kan_koras']); self.assertTrue(any('okänt utfall' in h for h in t['hinder']))
        with self.assertRaises(aktivera.Fel):
            self.mandat()
        self.w.r2.add('kund-%s-bilagor' % SLUG)  # bucketen skapades trots att svaret tappades
        a = aktivera.stam_av(SLUG, wrangler=self.w.fabrik)
        self.assertEqual((a['status'], [(s['id'], s['status']) for s in a['steg']]), ('klar', [('r2', 'klar')]))
        t = aktivera.torr(SLUG)
        self.assertEqual(self.status(t)['r2'], 'klar'); self.assertTrue(t['kan_koras'])
        self.assertEqual(aktivera.stam_av(SLUG, wrangler=self.w.fabrik)['status'], 'inget_att_stamma_av')

    def test_fel_kund_och_fiktiv_verksamhet_nekas(self):
        self.intag()
        (self.root / 'underlag' / SLUG / 'CLOUDFLARE.json').write_text(json.dumps({'database_id': ANNAN}))
        self.w.d1['kund-%s-forfragningar' % SLUG] = UUID  # kundens riktiga databas har ett annat id
        self.mandat()
        r = self.kor()
        self.assertEqual(r['status'], 'fel')
        self.assertTrue(any('inte kundens databas' in (s.get('fel') or '') for s in r['steg']), r['steg'])
        self.assertNotIn(['d1', 'migrations', 'apply', 'DB', '--remote'], self.w.anrop)
        m = json.loads(aktivera.mandatfil(SLUG).read_text()); m.pop('anvant_av', None); m['slug'] = 'annan-kund'
        aktivera.mandatfil(SLUG).write_text(json.dumps(m))
        self.assertEqual(self.kor()['status'], 'vantar_pa_mandat', 'ett mandat för en annan kund')
        self.verksamhet(fiktiv=True)
        t = aktivera.torr(SLUG)
        self.assertFalse(t['kan_koras']); self.assertTrue(any('fiktiv' in h for h in t['hinder']))
        with self.assertRaises(aktivera.Fel):
            self.mandat()

    def test_byggflodets_knapp_och_kravet(self):
        import flodesstart
        import prototyp
        with patch.object(flodesstart, 'pagande', return_value=False), patch.object(prototyp, 'lage', return_value=('valda', None)):
            with self.assertRaises(ValueError):
                flodesstart.krav(SLUG, 'aktivera')  # inget intag: driftvärdena saknas
            self.assertNotIn('aktivera', [h['id'] for h in prototyp.handlingar(SLUG)])
            self.intag()
            flodesstart.krav(SLUG, 'aktivera')
            h = next(h for h in prototyp.handlingar(SLUG) if h['id'] == 'aktivera')
            self.assertEqual(h['bindning'], {'plan_sha256': aktivera.torr(SLUG)['plan_sha256']}, 'mandatet binds till planen som knappen visar')
        self.assertIn('aktivera', flodesstart.HANDLINGAR)
        self.assertIn('ditt beslut', prototyp.HANDLINGAR['aktivera'])

    def test_dubbelstart_nekas_av_kundens_las(self):
        self.intag(); self.mandat()
        hallare = subprocess.Popen([sys.executable, '-c', (
            'import sys,time; sys.path.insert(0, %r); import flodesstart\n'
            'with flodesstart.las(%r, %r): print("hall", flush=True); time.sleep(20)') % (str(ROOT / 'kontroller'), str(self.root), SLUG)],
            stdout=subprocess.PIPE, text=True)
        self.addCleanup(hallare.kill)
        self.assertEqual(hallare.stdout.readline().strip(), 'hall')
        with self.assertRaises(ValueError):
            self.kor()
        self.assertEqual(self.w.anrop, [])
        self.assertNotIn('anvant_av', json.loads(aktivera.mandatfil(SLUG).read_text()), 'mandatet är oförbrukat')


if __name__ == '__main__':
    unittest.main()
