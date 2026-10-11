#!/usr/bin/env python3
"""Repoväljaren (ägarens tillägg 2026-10-11; kunskap/andringar.md, Repoväljaren) prövad i en isolerad rot med provets gh
och lokala nakna repon som organisationens GitHub (repovaljare_fixtur.py); riktiga GitHub nås aldrig. Fallen står vid
ägarens acceptansprov:

- listan (1): organisationens kundrepon och inget annat; främmande organisationer, motorns repo och arkiverade syns inte;
- en arbetskopia (3): Ändringar öppnas för rätt kund och förkontrollen är grön, och valet står i Senast öppnade;
- ingen arbetskopia (4): en bekräftelse först, sedan klonen till kunder/<slug>/kundrepo, kvittot och en grön förkontroll;
- bindningen (5): ett repo kopplat till en kund öppnas inte som en annan; ett okopplat kräver ett aktivt val bland
  befintliga kunder (aldrig en fiktiv, aldrig en med kvitto), och ett repo utan projektets markör binds inte;
- hämta och uppdatera (6): fetch utan sammanfogning med läget före och efter; bara fast-forward på en ren arbetskopia,
  lokala ändringar och egna commits står kvar, och kundens lås gäller;
- inloggningen (7): utgången, saknad och nätfel ger ett tydligt besked med åtgärden, och arbetskopiorna står kvar;
- Senast öppnade (9) överlever att modulen och servern startas om.

    .venv/bin/python -B kontroller/rokprov/revision/prov_repovaljaren.py
"""
import contextlib
import importlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import andringar  # noqa: E402
import atelje  # noqa: E402
import exportera  # noqa: E402
import flodesstart  # noqa: E402
import korregister  # noqa: E402
import kundrepo  # noqa: E402
import repovaljare  # noqa: E402
import repovaljare_fixtur as fixtur  # noqa: E402

URL = 'https://github.com/Nortropic/%s'


class Bas(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-repovaljaren-', 'repoväljarens prov'))).resolve()
        for m in (atelje, exportera):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.dict(os.environ, fixtur.bygg(self.root)))
        repovaljare.CACHE.update(tid=0.0, svar=None)
        self.addCleanup(repovaljare.CACHE.update, tid=0.0, svar=None)

    def post(self, namn, las_om=False):
        return next((p for p in repovaljare.lista(las_om)['repon'] if p['namn'] == namn), None)

    def git(self, slug, *args):
        return subprocess.run(['git', '-c', 'core.fsmonitor=false', *args], cwd=str(kundrepo.repo(slug)), capture_output=True, text=True).stdout.strip()


class Repovaljaren(Bas):
    def test_01_listan_ar_organisationens_kundrepon(self):
        d = repovaljare.lista()
        self.assertEqual(d['inloggning'], {'slag': 'ok'})
        self.assertEqual(sorted(p['namn'] for p in d['repon']), ['kund-alfa', 'kund-beta', 'kund-gamma', 'kund-utan-markor'],
                         'främmande organisation, motorns repo och det arkiverade syns inte')
        self.assertEqual(d['arkiverade'], 1)
        self.assertTrue(all(p['full'].startswith('Nortropic/') for p in d['repon']))
        alfa, beta, gamma, utan = (self.post(n) for n in ('kund-alfa', 'kund-beta', 'kund-gamma', 'kund-utan-markor'))
        self.assertEqual((alfa['kund']['slug'], alfa['oppnas'], alfa['arbetskopia']['lage']), ('alfa', 'oppna', 'i takt'))
        self.assertEqual((beta['kund']['slug'], beta['oppnas']), ('beta', 'klona'))
        self.assertEqual((gamma['kund'], gamma['oppnas'], gamma['forslag']), (None, 'koppla', 'gamma'), 'ett namnförslag, ingen bindning')
        self.assertEqual(utan['oppnas'], 'nej')
        self.assertIn('markör', utan['skal'])
        self.assertEqual([k['slug'] for k in d['kunder']], ['gamma'], 'bara en befintlig kund utan kvitto, aldrig den fiktiva')
        # listan återanvänds inom listtiden: ett anrop till gh, inte ett per läsning
        n = len((self.root / 'fejkgh.logg').read_text(encoding='utf-8').splitlines())
        repovaljare.lista()
        self.assertEqual(len((self.root / 'fejkgh.logg').read_text(encoding='utf-8').splitlines()), n)

    def test_03_arbetskopian_oppnas_for_ratt_kund(self):
        svar = repovaljare.oppna('kund-alfa')
        self.assertEqual(svar, {'vy': '#/andringar/alfa', 'slug': 'alfa'})
        self.assertEqual(andringar.forkontroll('alfa')['hinder'], [], 'förkontrollen är grön')
        self.assertEqual([x['repo'] for x in repovaljare.senast()], ['kund-alfa'])

    def test_04_klonen_efter_bekraftelse(self):
        self.assertEqual(repovaljare.oppna('kund-beta')['bekrafta'], 'klona')
        self.assertFalse(kundrepo.repo('beta').exists(), 'inget klonas utan bekräftelse')
        svar = repovaljare.oppna('kund-beta', bekraftat=True)
        self.assertEqual((svar['vy'], svar['klonad'], svar['hinder']), ('#/andringar/beta', True, []))
        r = kundrepo.repo('beta')
        self.assertEqual(r.resolve(), (self.root / 'kunder' / 'beta' / 'kundrepo').resolve(), 'klonen ligger på kundens plats')
        self.assertEqual(repovaljare.normaliserad(self.git('beta', 'config', '--get', 'remote.origin.url')), URL % 'kund-beta')
        kv = kundrepo.las_kvitto('beta')
        self.assertEqual((kv['arbetskopia']['fran'], kv['arbetskopia']['commit'], kv['projekt_id']), (URL % 'kund-beta', kundrepo.huvud(r), fixtur.PID['beta']))
        self.assertEqual(self.post('kund-beta')['oppnas'], 'oppna')
        with self.assertRaises(ValueError):
            repovaljare.oppna('kund-beta', slug='../alfa', bekraftat=True)
        # den klonade commiten är grunden som kvitteringarna bygger vidare på (granskningen 2026-10-11: utan ett eget
        # exportkvitto kunde en ändring efter klonen aldrig kvitteras), och en prövad ändring ovanpå den kvitteras
        e = exportera.aktuell('beta')
        self.assertEqual((e['kalla'], e['commit'], e['aktuell']), ('klon', kundrepo.huvud(r), True))
        self.assertEqual(kundrepo.las_kvitto('beta')['senaste_export']['commit'], kundrepo.huvud(r))
        sida = r / 'src' / 'pages' / 'index.astro'
        sida.write_text(sida.read_text(encoding='utf-8') + '<!-- ändringen -->\n', encoding='utf-8')
        andringar.committa('beta', ['src/pages/index.astro'], 'Ändring: efter klonen')
        vy = {'status': 200, 'innehallstyp': 'text/html', 'h1': 1, 'konsol': [], 'sidfel': [], 'spill': {'spill': False},
              'bedombarhet': {'main': True, 'main_text_langd': 200, 'text_langd': 300, 'bilder_forsta_vyn': 0, 'brutna_bilder_forsta_vyn': [],
                              'typsnitt_fel': [], 'felsida': False}}
        post = andringar.kontrollera('beta', bygg=lambda r_: (0, 'byggt'), fotografera=lambda d, s_, u: ({'vyer': {'390': vy, '1440': vy}}, {}))
        self.assertTrue(post['ok'], post['brister'])
        kv2 = exportera.fran_andring('beta')
        self.assertEqual((exportera.aktuell('beta')['kalla'], kv2['commit']), ('andring', kundrepo.huvud(r)))

    def test_05_bindningen_galler(self):
        with self.assertRaisesRegex(ValueError, 'kopplat till alfa'):
            repovaljare.oppna('kund-alfa', slug='beta')
        with self.assertRaisesRegex(ValueError, 'markör'):
            repovaljare.oppna('kund-utan-markor', slug='gamma', bekraftat=True)
        self.assertEqual(repovaljare.oppna('kund-gamma')['bekrafta'], 'koppla', 'ett okopplat repo kräver ett aktivt val')
        self.assertEqual(repovaljare.oppna('kund-gamma', slug='gamma')['bekrafta'], 'koppla', 'och en bekräftelse')
        for fel in ('delta', 'alfa', 'finns-inte'):  # fiktiv, har kvitto, finns inte
            with self.assertRaisesRegex(ValueError, 'kan inte kopplas'):
                repovaljare.oppna('kund-gamma', slug=fel, bekraftat=True)
        self.assertFalse(kundrepo.las_kvitto('delta'), 'den fiktiva verksamheten fick inget fjärrepo')
        svar = repovaljare.oppna('kund-gamma', slug='gamma', bekraftat=True)
        self.assertEqual((svar['vy'], svar['kopplad'], svar['hinder']), ('#/andringar/gamma', True, []))
        kv = kundrepo.las_kvitto('gamma')
        self.assertEqual((kv['projekt_id'], kv['fjarr']['adress'], kv['fjarr']['kopplat']['av']), (fixtur.PID['gamma'], URL % 'kund-gamma', 'repoväljaren'))
        self.assertEqual(kundrepo.bunden_adress('gamma'), URL % 'kund-gamma')
        self.assertEqual(self.post('kund-gamma')['kund']['slug'], 'gamma', 'kopplingen gäller sedan i listan')
        # ett repo som två kvitton pekar ut öppnas inte förrän kvittona rättats
        kv_b = kundrepo.las_kvitto('beta')
        kv_b['fjarr']['adress'] = URL % 'kund-gamma'
        atelje.skriv_json_atomiskt(kundrepo.kvittofil('beta'), kv_b)
        p = self.post('kund-gamma')
        self.assertEqual(p['oppnas'], 'nej')
        self.assertIn('två kunders kvitton', p['skal'])

    def test_06_hamta_och_uppdatera_bara_framat(self):
        fore = self.git('alfa', 'rev-parse', 'HEAD')
        fixtur.ny_commit_pa_fjarren(self.root, 'kund-alfa', 'Ändring från en annan dator')
        fixtur.ny_commit_pa_fjarren(self.root, 'kund-alfa', 'En till')
        self.assertEqual(repovaljare.arbetskopians_lage('alfa')['lage'], 'i takt', 'inget nät utan hämta')
        h = repovaljare.hamta('alfa')
        self.assertEqual((h['fore']['efter'], h['efter']['efter'], h['efter']['lage']), (0, 2, 'efter'))
        self.assertEqual([c['text'] for c in h['inkommande']], ['En till', 'Ändring från en annan dator'])
        self.assertEqual(self.git('alfa', 'rev-parse', 'HEAD'), fore, 'hämta sammanfogar inget')
        # lokala ändringar: ingen uppdatering, och ändringen står kvar
        sida = kundrepo.repo('alfa') / 'src' / 'pages' / 'index.astro'
        original = sida.read_text(encoding='utf-8')
        sida.write_text(original + '<!-- lokal -->\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'lokala ändringar'):
            repovaljare.uppdatera('alfa')
        self.assertIn('<!-- lokal -->', sida.read_text(encoding='utf-8'))
        self.assertEqual(self.git('alfa', 'rev-parse', 'HEAD'), fore)
        sida.write_text(original, encoding='utf-8')
        # kundens lås: inte medan ett annat arbete håller det
        with flodesstart.las(self.root, 'alfa'):
            with self.assertRaises(repovaljare.Upptagen):
                repovaljare.uppdatera('alfa')
        u = repovaljare.uppdatera('alfa')
        self.assertEqual((u['andrat'], u['efter']['lage'], len(u['commits'])), (True, 'i takt', 2))
        # isär: en egen commit och en ny på fjärren; ingen uppdatering, den egna commiten står kvar
        sida.write_text(original + '<!-- egen -->\n', encoding='utf-8')
        subprocess.run(['git', '-c', 'user.name=p', '-c', 'user.email=p@p', 'commit', '-qam', 'Ändring: egen'], cwd=str(kundrepo.repo('alfa')), check=True)
        egen = self.git('alfa', 'rev-parse', 'HEAD')
        fixtur.ny_commit_pa_fjarren(self.root, 'kund-alfa', 'Tredje')
        self.assertEqual(repovaljare.hamta('alfa')['efter']['lage'], 'isär')
        with self.assertRaisesRegex(ValueError, 'gått isär'):
            repovaljare.uppdatera('alfa')
        self.assertEqual(self.git('alfa', 'rev-parse', 'HEAD'), egen)
        # en annan gren: visas, byts inte till och uppdateras inte
        subprocess.run(['git', 'checkout', '-q', '-b', 'utkast'], cwd=str(kundrepo.repo('alfa')), check=True)
        l = repovaljare.arbetskopians_lage('alfa')
        self.assertEqual((l['gren'], l['pa_standardgren']), ('utkast', False))
        with self.assertRaisesRegex(ValueError, 'byter inte gren'):
            repovaljare.uppdatera('alfa')

    def test_07_inloggningen(self):
        for lage, slag, ord_ in (('utgangen', 'utgangen', 'gått ut'), ('saknas', 'saknas', 'inte inloggat'), ('natfel', 'natfel', 'gick inte att nå')):
            fixtur.satt_lage(self.root, lage)
            d = repovaljare.lista(las_om=True)
            self.assertEqual(d['inloggning']['slag'], slag, lage)
            self.assertIn(ord_, d['inloggning']['besked'])
            self.assertNotIn('klistra', d['inloggning']['atgard'].lower())
            if slag != 'natfel':
                self.assertIn('gh auth login', d['inloggning']['atgard'])
                self.assertIn('frågar aldrig efter en token', d['inloggning']['atgard'])
            # inget trasigt läge: den bundna arbetskopian ur kvittot står kvar och går att öppna
            alfa = next(p for p in d['repon'] if p['namn'] == 'kund-alfa')
            self.assertEqual((alfa['oppnas'], alfa.get('ur_kvittot')), ('oppna', True))
        self.assertEqual(repovaljare.oppna('kund-alfa')['vy'], '#/andringar/alfa')
        with self.assertRaisesRegex(ValueError, 'finns inte bland'):
            repovaljare.oppna('kund-beta', bekraftat=True)
        # GitHub svarar men ger inga kundrepon (oftast en inloggning utan åtkomst till organisationen): ett besked i stället
        # för en tom lista, och arbetskopian på datorn står kvar (granskningen 2026-10-11)
        f = self.root / 'fejkgh.json'
        cfg = json.loads(f.read_text(encoding='utf-8'))
        f.write_text(json.dumps(dict(cfg, lage='ok', repon=[]), ensure_ascii=False), encoding='utf-8')
        d = repovaljare.lista(las_om=True)
        self.assertEqual(d['inloggning']['slag'], 'tom')
        self.assertIn('gh auth status', d['inloggning']['atgard'])
        self.assertEqual([(p['namn'], p.get('ur_kvittot')) for p in d['repon']], [('kund-alfa', True)])
        # organisationen syns men har bara motorns repo (läget i Nortropic 2026-10-11): ett läge, inget inloggningsfel
        motorn = [x for x in cfg['repon'] if x['name'] == 'nortropic-webb-pro']
        f.write_text(json.dumps(dict(cfg, lage='ok', repon=motorn), ensure_ascii=False), encoding='utf-8')
        d = repovaljare.lista(las_om=True)
        self.assertEqual(d['inloggning']['slag'], 'inga_kundrepon')
        self.assertIn('inga kundrepon', d['inloggning']['besked'])
        self.assertNotIn('gh auth', d['inloggning']['atgard'])

    def test_09_senast_overlever_en_omstart(self):
        repovaljare.oppna('kund-alfa')
        repovaljare.oppna('kund-beta', bekraftat=True)
        self.assertEqual([x['repo'] for x in repovaljare.senast()], ['kund-beta', 'kund-alfa'])
        self.assertTrue((self.root / 'underlag' / 'repovaljaren' / 'SENAST.json').is_file())
        importlib.reload(repovaljare)  # som en ny serverprocess: inget i minnet
        self.assertEqual([x['repo'] for x in repovaljare.senast()], ['kund-beta', 'kund-alfa'])
        repovaljare.oppna('kund-alfa')
        self.assertEqual([x['repo'] for x in repovaljare.lista()['senast']], ['kund-alfa', 'kund-beta'], 'det senast öppnade först, inga dubbletter')


if __name__ == '__main__':
    unittest.main(verbosity=2)
