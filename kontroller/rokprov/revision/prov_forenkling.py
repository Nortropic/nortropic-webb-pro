#!/usr/bin/env python3
"""Förenklingen av skapandeflödet (ägarens uppdrag 2026-10-10 ~19:53Z): mekaniken genom de verkliga ingångarna, med
attrapper bara för det externa (sessionerna, fångsten, tjänsterna, DevTools och bygget). Inga modeller och inget nät.

- A: startkontrollen stoppar ett aktiveringskrav som sessionen inte kan uppfylla, före den första sessionen.
- B/D: fångsten och tjänsterna i samma begäran körs samtidigt, och båda svaren finns kvar.
- C: planprövningen ligger före uppdragens material; materialet hämtas bara för uppdrag vars indata saknas, ändrats eller
  brast, och en återgång hämtar inget själv.
- D: profilen beställs i kandidatens kedja; en annan kandidats brist stoppar den inte, olika sidor profileras samtidigt,
  samma sida en gång; en profilbrist görs om en gång vid nästa start, aldrig i en slinga; underlaget fryses per försök.
- E: ett bygge av exakt samma indata återanvänds; ändrad källa, ändrade beroenden, ett fallerat bygge eller en ändrad
  dist byggs om; kritikern får flödets bilder av exakt den version den bedömer.
- F: planen behåller giltiga uppdrag och kompletterar de saknade en gång.
- Punkt 4: fokus är en av skissens snabba kontroller.

--bas kör fallen mot HEAD:s moduler (föreprovet): de ska vara röda av rätt skäl.
"""
import contextlib
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import korregister  # noqa: E402

BAS = '--bas' in sys.argv
if BAS:
    sys.argv.remove('--bas')
    for namn in ('skapande', 'prova', 'forhandsvisa', 'referensprofil', 'atelje', 'kandidater', 'startkontroll'):
        src = subprocess.run(['git', 'show', 'HEAD:kontroller/%s.py' % namn], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        m = types.ModuleType(namn)
        m.__file__ = str(ROOT / 'kontroller' / ('%s.py' % namn))
        sys.modules[namn] = m
        exec(compile(src, m.__file__, 'exec'), m.__dict__)
import atelje  # noqa: E402
import devtools  # noqa: E402
import forhandsvisa  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import prova  # noqa: E402
import referensfixtur  # noqa: E402
import referensprofil as rp  # noqa: E402
import skapande  # noqa: E402
import startkontroll  # noqa: E402

SLUG = 'forenkling-prov'


class Grund(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'förenklingens prov'))).resolve()
        self.u, self.k = self.tmp / 'underlag', self.tmp / 'kunder'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.u, KUNDER=self.k))
        (self.u / SLUG).mkdir(parents=True)
        (self.u / SLUG / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provverkstan', 'fiktiv': True}))


class Research(Grund):
    """B/D: fångsten och tjänsterna i samma begäran, samtidigt."""

    def begaran(self):
        r = self.tmp / 'rot'
        r.mkdir(exist_ok=True)
        f = r / 'begaran.json'
        f.write_text(json.dumps({'varfor': 'prov', 'referens': {'kandidater': [{'namn': 'ny-sajt', 'adress': 'https://ny-sajt.se/', 'roll': 'bransch',
                                                                                'varfor': 'prov', 'sidor': ['/']}]},
                                 'tjanster': {'fragor': [{'tjanst': 'refero', 'fraga': 'typografisk riktning', 'typ': 'stil', 'syfte': 'prov'}]}}))
        return f, r

    def test_fangsten_och_tjansterna_kors_samtidigt(self):
        f, r = self.begaran()
        tider = {}

        def kor(args, frist):
            namn = Path(args[2]).name
            tider[namn] = [time.monotonic()]
            time.sleep(0.8)
            tider[namn].append(time.monotonic())
            return types.SimpleNamespace(returncode=0, stdout='ok', stderr='')
        start = time.monotonic()
        ut = skapande.komplettera(SLUG, f, r, self.u, frist=30, kor=kor, bred=True, forbjudna={'ord': set(), 'siffror': set()})
        vagg = time.monotonic() - start
        self.assertEqual(sorted(tider), ['referens.py', 'referenstjanster.py'])
        self.assertEqual((ut['referens']['rc'], ut['tjanster']['rc']), (0, 0), ut)
        a, b = tider['referens.py'], tider['referenstjanster.py']
        self.assertLess(max(a[0], b[0]), min(a[1], b[1]), 'delarna överlappar i tid')
        self.assertLess(vagg, 1.5, 'väggtiden är den längsta delen, inte summan (%.2f s)' % vagg)
        self.assertIn('sekunder', ut['referens'])

    def test_en_tidsgrans_tar_inte_den_andra_delens_svar(self):
        f, r = self.begaran()

        def kor(args, frist):
            if Path(args[2]).name == 'referens.py':
                raise subprocess.TimeoutExpired(args, frist)
            return types.SimpleNamespace(returncode=0, stdout='', stderr='')
        ut = skapande.komplettera(SLUG, f, r, self.u, frist=7, kor=kor, bred=True, forbjudna={'ord': set(), 'siffror': set()})
        self.assertIsNone(ut['referens']['rc'])
        self.assertEqual(ut['referens']['tidsgrans'], 7)
        self.assertEqual(ut['tjanster']['rc'], 0)

    def test_ett_fel_kastas_vidare_nar_bada_ar_klara(self):
        f, r = self.begaran()
        klara = []

        def kor(args, frist):
            if Path(args[2]).name == 'referenstjanster.py':
                raise OSError('syntetiskt startfel')
            time.sleep(0.3)
            klara.append('referens')
            return types.SimpleNamespace(returncode=0, stdout='', stderr='')
        with self.assertRaisesRegex(OSError, 'syntetiskt startfel'):
            skapande.komplettera(SLUG, f, r, self.u, frist=7, kor=kor, bred=True, forbjudna={'ord': set(), 'siffror': set()})
        self.assertEqual(klara, ['referens'], 'fångsten fick bli klar innan felet kastades vidare')


class Material(Grund):
    """C: materialet efter planprövningen, bundet till sina indata."""

    def setUp(self):
        super().setUp()
        self.r = kd.rot(SLUG)
        self.r.mkdir(parents=True)
        self.plan = {'lage': 'skiss', 'kandidater': {
            'k01': {'titel': 'Ett', 'refero_stil': '', 'mobbin_fraga': 'course booking list', 'mobbin_typ': 'skarm'},
            'k02': {'titel': 'Två', 'refero_stil': '', 'mobbin_fraga': 'contact form with opening hours'}}}
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(self.plan))
        for kid in ('k01', 'k02'):
            kd.satt_status(SLUG, kid, 'planerad', 'uppdraget skrivet', forsok=0)
        self.samlade = []
        self.mobbin_ok = True

        def samla(slug, uppdrag, underlag=None, katalog='tjanster', **kw):
            self.samlade.append([f['fraga'] for f in uppdrag['fragor']])
            return None, {'tjanster': {'mobbin': {'ok': self.mobbin_ok, 'bilder': 0, 'traffar': []}}}
        import referenstjanster
        self.stack.enter_context(patch.object(referenstjanster, 'samla', samla))

    def test_bara_saknat_andrat_eller_ofullstandigt_hamtas(self):
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), ['k01', 'k02'])
        kd.uppdragsmaterial(SLUG, bara=['k01', 'k02'])
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), [], 'oförändrade indata: inget hämtas igen')
        # planprövningen ändrar ett formfält: materialet gäller fortfarande
        self.plan['kandidater']['k01']['typografi'] = 'ny typografi'
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(self.plan))
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), [])
        # Mobbins sökfras ändras för k02: bara k02 hämtas, och k01:s post står kvar
        self.plan['kandidater']['k02']['mobbin_fraga'] = 'contact form'
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(self.plan))
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), ['k02'])
        self.samlade.clear()
        kd.uppdragsmaterial(SLUG, bara=['k02'])
        self.assertEqual(self.samlade, [['contact form']])
        um = json.loads((self.r / kd.UPPDRAGSMATERIAL).read_text())['kandidater']
        self.assertEqual(sorted(um), ['k01', 'k02'])
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), [])

    def test_en_hamtning_som_foll_ar_aldrig_komplett(self):
        self.mobbin_ok = False
        kd.uppdragsmaterial(SLUG, bara=['k01', 'k02'])
        um = json.loads((self.r / kd.UPPDRAGSMATERIAL).read_text())['kandidater']
        self.assertFalse(um['k01']['komplett'])
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), ['k01', 'k02'], 'hämtas igen vid nästa start')

    def test_aldre_material_utan_indata_ateranvands_bara_utan_fel(self):
        (self.r / kd.UPPDRAGSMATERIAL).write_text(json.dumps({'kandidater': {'k01': {'mobbin_fraga': 'x', 'mobbin': [{'fil': 'a'}]},
                                                                             'k02': {'mobbin_fraga': 'y', 'mobbin_fel': 'tjänsten svarade inte'}}}))
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), ['k02'])

    def test_visade_och_stoppade_kandidater_hamtar_inget(self):
        kd.satt_status(SLUG, 'k01', 'klar', 'fotograferad')
        kd.satt_status(SLUG, 'k02', 'fel', 'återgången misslyckades', atergang_fel={'tid': 'x'})
        self.assertEqual(kd.material_behov(SLUG, ['k01', 'k02']), [])

    def test_planprovningen_ligger_fore_materialet_och_atergangen_hamtar_inget(self):
        ordning = []
        import inspect
        kalla = inspect.getsource(kd.kor)
        self.assertLess(kalla.index('planprovning(slug'), kalla.index('uppdragsmaterial(slug'), 'planprövningen före materialet')
        self.assertNotIn('uppdragsmaterial(', inspect.getsource(kd.atergang))
        self.assertNotIn('uppdragsmaterial(', inspect.getsource(kd.atergang_omforsok))
        # och genom körningen: materialet hämtas efter prövningen, för de uppdrag som ska skapas
        with patch.multiple(kd, STOPP_EFTER='planprovning', leverera_metod=lambda _: {}, korlage=lambda *a: 'skiss',
                            planprovning_behov=lambda slug, ids: [] if ordning else list(ids),
                            planprovning=lambda slug, bara=None: ordning.append('planprovning') or {},
                            uppdragsmaterial=lambda slug, bara=None, klient=None: ordning.append(('material', tuple(bara))) or {}), \
                patch.object(kompetens, 'kravbrister', return_value=[]), patch('referenskontrakt.startbrister', return_value=[]):
            import urval
            with patch.object(urval, 'vid_start', return_value={}):
                kd.kor(SLUG, {}, lambda: None, n=2)
        self.assertEqual(ordning, ['planprovning', ('material', ('k01', 'k02'))])

    def test_planprovningen_far_andra_mobbins_sokfras_men_inte_stilen(self):
        import inspect
        kalla = inspect.getsource(kd.planprovning)
        self.assertIn("lasta = ('titel', 'hypotes', 'huvudreferens', 'refero_stil')", kalla)


class Profiler(unittest.TestCase):
    """D: profilen per kandidat, lås per sida, en brist stoppar bara sin kandidat."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'förenklingens profilprov'))).resolve()
        self.u = self.root / 'underlag'
        self.ref = self.u / SLUG / 'referenser'
        self.ref.mkdir(parents=True)
        self.calls, self.aktiva, self.max_aktiva = [], [0], [0]
        self.las = threading.Lock()
        self.stack.enter_context(patch.object(rp, 'motoridentitet', return_value={'version': '1', 'modell': 'syntetisk', 'filer': {}}))
        self.stack.enter_context(patch.object(devtools, 'profilera', side_effect=self.profil))
        self.stack.enter_context(patch.object(devtools, 'resursursprung', return_value=[]))

    def paket(self, namn, adress, version='paket-v01'):
        d = self.ref / version
        d.mkdir(exist_ok=True)
        bildrel = namn + '/01-sida/vy-390-forsta.png'
        (d / bildrel).parent.mkdir(parents=True, exist_ok=True)
        (d / bildrel).write_bytes(b'syntetisk bild ' + namn.encode())
        f = d / 'PAKET.json'
        j = json.loads(f.read_text()) if f.exists() else {'schema': 2, 'slug': SLUG, 'version': version, 'torr': False, 'kandidater': []}
        from urllib.parse import urlsplit
        u_ = urlsplit(adress)
        j['kandidater'].append({'namn': namn, 'adress': '%s://%s/' % (u_.scheme, u_.netloc), 'ok': True,
                                'sidor': [{'adress': adress, 'sida': u_.path, 'katalog': namn + '/01-sida', 'ok': True, 'filer': [bildrel]}]})
        f.write_text(json.dumps(j))
        return {'huvudreferens': namn, 'referensbilder': [str(d / bildrel)], 'utgangspunkt': {'slag': 'referenssajt'}}

    def profil(self, slug, adress, ut, underlag, paket, referensnamn):
        with self.las:
            self.calls.append(adress)
            self.aktiva[0] += 1
            self.max_aktiva[0] = max(self.max_aktiva[0], self.aktiva[0])
        time.sleep(0.4)
        j = {'slug': slug, 'adress': adress, 'paket': paket.name, 'referensnamn': referensnamn, 'version': '1', 'torr': False, 'verklig': True,
             'aktivering': {'ansluten': True}, 'anvandning': {'genomford': True, 'grupper': {g: True for g in devtools.KRAVDA_GRUPPER}},
             'session': {'subtype': 'success', 'is_error': False, 'slutkod': 0},
             'svar': {'anrop': [], 'prestanda': {'lcp_ms': None, 'cls': None, 'ttfb_ms': None, 'lcp_element': 'h1', 'insikter': []},
                      'lighthouse': {'enhet': 'mobile', 'prestanda': None, 'tillganglighet': None, 'basta_praxis': None, 'seo': None, 'not': ''},
                      'natverk': {'antal': 0, 'storsta': []}, 'regler': [], 'anmarkning': 'syntetiskt'}}
        ut.mkdir(parents=True, exist_ok=True)
        for n_, v_ in (('DEVTOOLS.json', json.dumps(j)), ('DEVTOOLS.md', 'syntetisk'), ('session.jsonl', '{}\n'), ('natgrans.json', '{}')):
            (ut / n_).write_text(v_)
        with self.las:
            self.aktiva[0] -= 1
        return j, None

    def kor(self, plan):
        return rp.forbered(SLUG, plan, 'metod', underlag=self.u, root=self.root)

    def test_en_kandidats_brist_stoppar_inte_den_andra(self):
        bra = self.paket('alpha', 'https://alpha.example.com/')
        res = self.kor({'kandidater': {'k01': {'huvudreferens': 'okand', 'referensbilder': bra['referensbilder'], 'utgangspunkt': {'slag': 'referenssajt'}},
                                       'k02': bra}})
        self.assertTrue(res['kandidater']['k01']['brister'])
        self.assertEqual(len(res['kandidater']['k02']['profiler']), 1, res)
        self.assertEqual(res['kandidater']['k02']['tillstand'], 'genomford')
        self.assertFalse(res['ok'], 'rapporten för båda bär k01:s brist')

    def test_olika_sidor_profileras_samtidigt_och_samma_sida_en_gang(self):
        a = self.paket('alpha', 'https://alpha.example.com/')
        b = self.paket('beta', 'https://beta.example.com/')
        resultat = {}

        def kedja(kid, k):
            resultat[kid] = self.kor({'kandidater': {kid: k}})
        tradar = [threading.Thread(target=kedja, args=x) for x in (('k01', a), ('k02', b), ('k03', copy.deepcopy(a)))]
        for t_ in tradar:
            t_.start()
        for t_ in tradar:
            t_.join()
        self.assertTrue(all(r_['ok'] for r_ in resultat.values()), resultat)
        self.assertEqual(sorted(self.calls), ['https://alpha.example.com/', 'https://beta.example.com/'], 'samma sida beställs en gång')
        self.assertEqual(self.max_aktiva[0], 2, 'olika sidor profileras samtidigt')
        ater = [p_['ateranvand'] for kid in ('k01', 'k03') for p_ in resultat[kid]['kandidater'][kid]['profiler']]
        self.assertEqual(sorted(ater), [False, True], 'den som väntade återanvände profilen')

    def test_kandidatens_rapport_ar_isolerad_och_bunden(self):
        a = self.paket('alpha', 'https://alpha.example.com/')
        (self.u / SLUG / 'atelje').mkdir(parents=True)
        (self.u / SLUG / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {'k01': a}}))
        res = rp.for_kandidat(SLUG, 'k01', 'metod', underlag=self.u, root=self.root)
        fil = rp.kandidatrapport(SLUG, 'k01', self.u)
        self.assertEqual(fil, self.u / SLUG / 'atelje' / 'kandidater' / 'k01' / 'REFERENSPROFIL.json')
        self.assertEqual(json.loads(fil.read_text()), res)
        self.assertEqual(res['uppdrag']['k01'], kd.uppdrag_sha(a))


class Kedjan(Grund):
    """D: profilen i kandidatens kedja; återupptagningen gör om den en gång; underlaget fryses."""

    def setUp(self):
        super().setUp()
        self.r = kd.rot(SLUG)
        self.r.mkdir(parents=True)
        k = {f: 'Syntetiskt' for f, _ in kd.PLANFALT}
        k.update(titel='Egen', huvudreferens='egen riktning', referensbilder=[])
        plan = referensfixtur.uppfyll(self.u, SLUG, {'kandidater': {'k01': k}})
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        kd.skriv_uppdrag(SLUG, 'k01', plan['kandidater']['k01'], 1, 1)
        kd.satt_status(SLUG, 'k01', 'planerad', 'uppdraget skrivet', forsok=0)
        self.stack.enter_context(patch.object(atelje, 'session', side_effect=AssertionError('ingen skaparsession i provet')))

    def test_profilbristen_gors_om_en_gang_per_start_aldrig_i_en_slinga(self):
        anrop = []

        def falsk(slug, kid):
            anrop.append(kid)
            return {'ok': False, 'brister': ['syntetisk brist']}
        import ab
        with patch.object(kd, 'profilrapport', falsk), patch.object(ab, 'skisskrav', lambda slug: None), \
                patch.object(ab, 'skissavslutad', lambda slug, kid: kd.las_status(slug, kid)):
            st = kd.behandla_skiss(SLUG, 'k01')
            self.assertEqual(anrop, ['k01'], 'ett försök i den här starten')
            self.assertEqual(st['status'], 'fel')
            self.assertTrue(kd.ska_skapas(st))
            st = kd.behandla_skiss(SLUG, 'k01')  # nästa start
            self.assertEqual(anrop, ['k01', 'k01'])
            self.assertEqual(st['referensprofil_brister']['brister'], ['syntetisk brist'])
            self.assertEqual(int(st.get('forsok') or 0), 0)

    def test_provunderlag_startar_aldrig_en_verklig_profilering(self):
        with patch.object(skapande, 'kor_trad', side_effect=AssertionError('ingen process mot provunderlaget')):
            res = kd.profilrapport(SLUG, 'k01')
        self.assertFalse(res['ok'])
        self.assertIn('motorns eget underlag', res['brister'][0])

    def test_underlaget_fryses_och_en_andring_syns_i_nasta_forsok(self):
        f1 = kd.fryst_underlag(SLUG, 'k01')
        self.assertEqual(f1, kd.fryst_underlag(SLUG, 'k01'), 'samma underlag ger samma frysning')
        # en annan kandidats komplettering (ett nytt paket) ändrar inte k01:s frysning
        referensfixtur.komplettera_paket(self.u, SLUG, 'paket-v02', arv='paket-v01')
        self.assertEqual(f1, kd.fryst_underlag(SLUG, 'k01'))
        plan = json.loads((self.r / 'KANDIDATPLAN.json').read_text())
        plan['kandidater']['k01']['ide'] = 'en ändrad idé'
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        self.assertNotEqual(f1['uppdrag'], kd.fryst_underlag(SLUG, 'k01')['uppdrag'])


class Bygget(Grund):
    """E: ett bygge av exakt samma indata återanvänds."""

    def setUp(self):
        super().setUp()
        self.sajt = self.k / SLUG / 'kandidater' / 'k01' / 'sajt'
        (self.sajt / 'src' / 'pages').mkdir(parents=True)
        (self.sajt / 'src' / 'pages' / 'index.astro').write_text('<h1>Ett</h1>')
        (self.sajt / 'package.json').write_text('{}')
        nm = self.k / SLUG / 'sajt' / 'node_modules'
        nm.mkdir(parents=True)
        (nm / '.package-lock.json').write_text('{"a": 1}')
        os.symlink(nm, self.sajt / 'node_modules')
        self.byggen = 0
        self.rc = 0

        def kor(cmd, cwd=None, timeout=900):
            if any('build' == str(x) for x in cmd):
                self.byggen += 1
                (self.sajt / 'dist').mkdir(exist_ok=True)
                (self.sajt / 'dist' / 'index.html').write_text((self.sajt / 'src' / 'pages' / 'index.astro').read_text())
                return self.rc, 'byggt'
            return 0, 'v22.0.0'
        self.stack.enter_context(patch.object(prova, 'kor', kor))

    def test_samma_indata_ateranvands_och_en_andring_bygger(self):
        self.assertEqual(prova.bygg_inom_grans(self.sajt)[0], 0)
        self.assertEqual(self.byggen, 1)
        rc, text = prova.bygg_inom_grans(self.sajt)
        self.assertEqual((rc, self.byggen), (0, 1), text)
        self.assertIn('återanvänt', text)
        (self.sajt / 'src' / 'pages' / 'index.astro').write_text('<h1>Två</h1>')
        prova.bygg_inom_grans(self.sajt)
        self.assertEqual(self.byggen, 2, 'ändrad källa byggs')
        (self.k / SLUG / 'sajt' / 'node_modules' / '.package-lock.json').write_text('{"a": 2}')
        prova.bygg_inom_grans(self.sajt)
        self.assertEqual(self.byggen, 3, 'ändrade beroenden (en typsnittsinstallation) byggs')
        (self.sajt / 'dist' / 'index.html').write_text('ändrad efter bygget')
        prova.bygg_inom_grans(self.sajt)
        self.assertEqual(self.byggen, 4, 'en dist som inte är byggets byggs om')
        logg = [json.loads(x) for x in (self.k / SLUG / 'kandidater' / 'k01' / 'BYGGEN.jsonl').read_text().splitlines()]
        self.assertEqual([x['ateranvant'] for x in logg], [False, True, False, False, False])
        self.assertTrue(all('vantade' in x for x in logg if not x['ateranvant']), 'väntan på bygglåset mäts')

    def test_fallerat_bygge_ger_ingen_stampel(self):
        self.rc = 1
        prova.bygg_inom_grans(self.sajt)
        prova.bygg_inom_grans(self.sajt)
        self.assertEqual(self.byggen, 2)
        self.assertFalse((self.k / SLUG / 'kandidater' / 'k01' / 'BYGGE.json').exists())

    def test_planterad_lank_eller_sajtens_eget_bygge_ateranvands_aldrig(self):
        os.symlink('/etc/hosts', self.sajt / 'src' / 'lank.txt')
        prova.bygg_inom_grans(self.sajt)
        prova.bygg_inom_grans(self.sajt)
        self.assertEqual(self.byggen, 2)
        huvud = self.k / SLUG / 'sajt'
        (huvud / 'src').mkdir(parents=True, exist_ok=True)
        self.byggen = 0
        with patch.object(prova, 'kor', lambda cmd, cwd=None, timeout=900: (setattr(self, 'byggen', self.byggen + 1) or (0, '')) if 'build' in cmd else (0, 'v22')):
            prova.bygg_inom_grans(huvud)
            prova.bygg_inom_grans(huvud)
        self.assertEqual(self.byggen, 2, 'bara en kandidats projekt återanvänds')

    def test_varvet_bar_sin_version(self):
        kalla = prova.kallidentitet(self.sajt, prova.byggkommando(self.sajt))
        vd = self.tmp / 'varv-01'
        vd.mkdir()
        (vd / 'KALLA.json').write_text(json.dumps({'kalla': kalla}))
        self.assertEqual(forhandsvisa.varvets_version(vd), kalla)
        (self.sajt / 'src' / 'pages' / 'index.astro').write_text('<h1>Ny</h1>')
        self.assertNotEqual(forhandsvisa.varvets_version(vd), prova.kallidentitet(self.sajt, prova.byggkommando(self.sajt)))


class Kritiken(Grund):
    """E: kritikern får flödets neutrala bilder av exakt den version den bedömer."""

    def test_kritikern_far_flodets_bilder_av_versionen(self):
        kid = 'k01'
        d = kd.kdir(SLUG, kid)
        vd = d / 'varv' / 'start' / 'varv-01'
        vd.mkdir(parents=True)
        for n_ in forhandsvisa.LAS:
            (vd / n_).write_bytes(referensfixtur.PNG)
        g = d / 'granskare' / 'start' / 'varv-01'
        g.mkdir(parents=True)
        for b_ in forhandsvisa.BREDDER:
            for s_ in ('forsta', 'hela'):
                (g / ('vy-%s-%s.png' % (b_, s_))).write_bytes(referensfixtur.PNG)
        (g / 'FORHAND.md').write_text('390 px tangentbord: 3 steg')
        prompter = []
        with patch.object(forhandsvisa, 'forhandsvisa', return_value=(0, 'ok', g)) as fv, \
                patch.object(kd, 'projektets_version', return_value='v1'), \
                patch.object(atelje, 'session', side_effect=lambda prompt, *a, **k: prompter.append(prompt) or {}):
            self.assertIsNone(kd.skisskritik(SLUG, kid))  # sessionen svarade inget: ingen post
        fv.assert_called_once_with(SLUG, '/', kandidat=kid, granskare=True)
        text = prompter[0]
        self.assertIn('granskare/start/varv-01/vy-768-forsta.png', text)
        self.assertNotIn('varv/start/varv-01/vy-390-forsta.png', text, 'skaparens varv ges inte när flödets bilder finns')
        self.assertIn('bara när bedömningen kräver', text, 'egen interaktionskontroll finns kvar vid behov')


class Planen(Grund):
    """F: giltiga uppdrag behålls och de saknade kompletteras en gång."""

    def setUp(self):
        super().setUp()
        kd.rot(SLUG).mkdir(parents=True)
        self.plan = referensfixtur.uppfyll(self.u, SLUG, {'kandidater': {}})
        self.anrop = []

    def uppdrag(self, i, giltigt=True):
        k = {f: 'Syntetiskt %d' % i for f, _ in kd.PLANFALT}
        k.update(titel='Uppdrag %d' % i, huvudreferens='egen riktning %d' % i, referensbilder=[])
        return k if giltigt else dict(k, titel='Ogiltigt %d' % i)

    def kor(self, svar):
        def session(prompt, verktyg, ut, schema=None, *a, **k):
            self.anrop.append((prompt, schema))
            return {'session_id': None, 'structured_output': svar[len(self.anrop) - 1]}
        bas = {x: self.plan.get(x) for x in ('bransch', 'forebilder_utanfor')}
        with patch.object(atelje, 'session', session), patch.object(kompetens, 'kravbrister', return_value=[]), \
                patch.object(kd, 'plan_prompt', lambda *a, **k: 'PLAN'), patch.object(kd, 'referenskedjebrist', return_value=None), \
                patch.object(kd, 'referensbrist', lambda slug, k: 'ogiltigt i provet' if k['titel'].startswith('Ogiltigt') else None), \
                patch.object(kd, 'planbrist', return_value=None), patch('referenskontrakt.planbrister', return_value=[]):
            return bas, kd.planera(SLUG, 10, 'skiss')

    def test_sex_giltiga_far_fyra_till_i_en_komplettering(self):
        bas = {x: self.plan.get(x) for x in ('bransch', 'forebilder_utanfor')}
        forsta = dict(bas, variation='v', kandidater=[self.uppdrag(i) for i in range(1, 7)] + [self.uppdrag(i, False) for i in range(7, 9)])
        andra = {'variation': 'v2', 'kandidater': [self.uppdrag(i) for i in range(11, 14)] + [self.uppdrag(14, False)]}
        _bas, ids = self.kor([forsta, andra])
        self.assertEqual(len(self.anrop), 2, 'en komplettering, ingen slinga')
        self.assertIn('KOMPLETTERING', self.anrop[1][0])
        self.assertIn('Uppdrag 1', self.anrop[1][0], 'de giltiga står fast och nämns')
        self.assertEqual(self.anrop[1][1]['properties']['kandidater']['minItems'], 4)
        plan = json.loads((kd.rot(SLUG) / 'KANDIDATPLAN.json').read_text())
        self.assertEqual(len(ids), 9)
        self.assertEqual([plan['kandidater'][k]['titel'] for k in ids[:6]], ['Uppdrag %d' % i for i in range(1, 7)], 'de giltiga behålls i ordning')
        self.assertIn('9 av 10', plan['brist_mot_begart'])
        self.assertIn('kompletteringen: 3 av 4', plan['brist_mot_begart'])

    def test_tio_giltiga_gor_ingen_komplettering(self):
        bas = {x: self.plan.get(x) for x in ('bransch', 'forebilder_utanfor')}
        _bas, ids = self.kor([dict(bas, variation='v', kandidater=[self.uppdrag(i) for i in range(1, 11)])])
        self.assertEqual((len(self.anrop), len(ids)), (1, 10))


class Kontrollerna(unittest.TestCase):
    """A och punkt 4."""

    def test_motsagelsefullt_aktiveringskrav_stoppar_fore_forsta_sessionen(self):
        c = {'resultat': 'ok', 'tid': 'nu', 'skills': ['refero-design', 'ui-ux-pro-max', 'better-explain-interface', 'hallmark', 'impeccable']}
        vag = {'id': 'kandidatflodet', 'fas': 'fore_research'}
        ok = startkontroll.aktiveringsrader(c, True, vag)
        self.assertEqual(ok[0]['resultat'], 'ok', ok)
        self.assertIn('användaranropade, läses hela', ok[0]['detalj'])
        # skillverktyget i sessionen saknar en skill som kvittot kräver aktiverad
        fel = startkontroll.aktiveringsrader(dict(c, skills=['ui-ux-pro-max']), True, vag)
        self.assertEqual((fel[0]['resultat'], fel[0]['nodvandig']), ('fel', True))
        self.assertIn('refero-design', fel[0]['detalj'])
        # en klassning som kräver aktivering av en användaranropad skill (kandidatprovet 2026-10-10) stoppas också
        aktiverbara = kompetens.aktiverbara

        def gammal(filer):
            s_, l_ = aktiverbara(filer)
            return s_ + [f.split('/')[0] for f in l_ if f.split('/')[0] in kompetens.anvandaranropade() and f.endswith('/SKILL.md')], l_
        with patch.object(kompetens, 'aktiverbara', gammal):
            fel = startkontroll.aktiveringsrader(c, True, vag)
        self.assertEqual(fel[0]['resultat'], 'fel')
        self.assertIn('better-explain-interface', fel[0]['detalj'])
        self.assertIn('användaranropad', fel[0]['detalj'])
        self.assertEqual(startkontroll.aktiveringsrader(c, False, vag), [], 'helbygget har egen startväg')

    def test_fokus_ar_en_snabb_kontroll(self):
        self.assertEqual(kd.fokusprovet({'tangentbord': [{'tagg': 'a', 'text': 'Boka', 'synligFokus': True}]}, '390'), [])
        m = kd.fokusprovet({'tangentbord': [{'tagg': 'a', 'text': 'Boka', 'synligFokus': False}, {'tagg': 'button', 'text': 'Meny', 'synligFokus': True}]}, '1440')
        self.assertEqual(len(m), 1)
        self.assertIn('1 av 2 tangentbordssteg utan synlig fokus', m[0])
        self.assertIn('inget fokuserbart', kd.fokusprovet({'tangentbord': []}, '390')[0])
        self.assertIn('prövades inte', kd.fokusprovet({}, '390')[0])
        import inspect
        self.assertIn("'tangentbord' if skiss", inspect.getsource(kd.fotografera))


if __name__ == '__main__':
    unittest.main()
