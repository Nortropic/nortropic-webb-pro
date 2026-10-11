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


class Researchvarvet(Grund):
    """Ägarens besked 2026-10-11: researchens andra varv (kandidatprovet: en enda saknad galleriförebild gav en ny session
    och sju nya fångster) hämtar bara det som saknas, och en inspektion faller inte på ett kasserat svar."""

    def test_ett_kasserat_svar_faller_inte_inspektionen(self):
        js = ("import { fullborda } from '%s';\n"
              "const logg = [];\n"
              "const route = { abort: async (r) => { logg.push('abort:' + r); }, fulfill: async () => { logg.push('fulfill'); } };\n"
              "await fullborda(route, { headers: () => ({}), status: () => 200, body: async () => { throw new Error('Response has been disposed'); } });\n"
              "await fullborda({ abort: async () => {}, fulfill: async () => { throw new Error('Target page has been closed'); } },"
              " { headers: () => ({}), status: () => 200, body: async () => Buffer.from('abc') });\n"
              "console.log(JSON.stringify(logg));\n") % (ROOT / 'kontroller' / 'webblasare' / 'gemensamt.mjs')
        r = subprocess.run(['node', '--input-type=module', '-e', js], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertEqual(json.loads(r.stdout.strip().splitlines()[-1]), ['abort:failed'])

    def test_varv_tva_hamtar_bara_den_saknade_rollen(self):
        import bildkedja
        import referenskontrakt as rk
        kd.rot(SLUG).mkdir(parents=True, exist_ok=True)
        svar = {'varfor': 'v', 'riktningar': 'r', 'antaganden': [], 'galleri': {}, 'sallning': [], 'urvalsfragor': {}, 'tackning': {},
                'sajter': [{'namn': 'bransch-a', 'adress': 'https://bransch-a.se/', 'roll': 'bransch', 'varfor': 'x', 'sidor': ['/']},
                           {'namn': 'galleri-a', 'adress': 'https://galleri-a.se/', 'roll': 'hantverk', 'varfor': 'x', 'sidor': ['/']},
                           {'namn': 'ux-a', 'adress': 'https://ux-a.se/', 'roll': 'ux', 'varfor': 'x', 'sidor': ['/']}],
                'fragor': [{'tjanst': 'refero', 'fraga': 'typografisk riktning', 'typ': 'stil', 'syfte': 'x'}]}
        begaranden = []

        def komplettera(slug, f, r, underlag, **k):
            begaranden.append(json.loads(Path(f).read_text()))
            return {'referens': {'rc': 0}, 'tjanster': {'rc': 0}}
        with patch.object(atelje, 'session', return_value={'session_id': None, 'structured_output': svar}), \
                patch.object(skapande, 'komplettera', komplettera), patch.object(skapande, 'kanal_fel', return_value=None), \
                patch.object(skapande, 'senaste_paket', return_value=None), \
                patch.object(kompetens, 'kravbrister', return_value=[]), patch.object(kompetens, 'kvitto', return_value={}), \
                patch.object(kd, 'forska_prompt', lambda *a, **k: 'PROMPT'), patch.object(bildkedja, 'transkript', return_value=None), \
                patch.object(rk, 'sokningar', return_value=[]), patch.object(rk, 'verifiera_upptackt', return_value={'vag': 'galleri', 'kalla': 'x'}), \
                patch.object(rk, 'researchbrister', side_effect=[['inspirationsgenomgången har 1 fångade sajter ur gallerierna (arbetsregeln: minst 2)'], [], []]), \
                patch.object(rk, 'researchluckor', return_value={'bransch': 0, 'inspiration': 1}):
            post = kd.forska(SLUG, 2, skiss=True)
        self.assertEqual(len(begaranden), 2)
        self.assertEqual(sorted(s_['namn'] for s_ in begaranden[0]['referens']['kandidater']), ['bransch-a', 'galleri-a', 'ux-a'])
        self.assertIn('tjanster', begaranden[0])
        self.assertEqual([s_['namn'] for s_ in begaranden[1]['referens']['kandidater']], ['galleri-a'], 'bara den saknade rollen')
        self.assertNotIn('tjanster', begaranden[1], 'tjänsterna frågas inte om')
        self.assertTrue(any('varv 2 hämtar bara det som saknas' in x for x in post['slappta']))
        self.assertEqual(post['tjanster'], {'rc': 0}, 'första varvets utfall står kvar')

    def test_varv_tva_fragar_tjansterna_igen_nar_de_foll(self):
        # granskningen 2026-10-11: tjänsterna som nådde tidsgränsen i första varvet släpptes i det andra med fel skäl
        import bildkedja
        import referenskontrakt as rk
        kd.rot(SLUG).mkdir(parents=True, exist_ok=True)
        svar = {'varfor': 'v', 'riktningar': 'r', 'antaganden': [], 'galleri': {}, 'sallning': [], 'urvalsfragor': {}, 'tackning': {},
                'sajter': [{'namn': 'galleri-a', 'adress': 'https://galleri-a.se/', 'roll': 'hantverk', 'varfor': 'x', 'sidor': ['/']}],
                'fragor': [{'tjanst': 'refero', 'fraga': 'typografisk riktning', 'typ': 'stil', 'syfte': 'x'}]}
        begaranden, utfall = [], [{'referens': {'rc': 0}, 'tjanster': {'rc': None, 'tidsgrans': 600}}, {'referens': {'rc': 0}, 'tjanster': {'rc': 0}}]

        def komplettera(slug, f, r, underlag, **k):
            begaranden.append(json.loads(Path(f).read_text()))
            return utfall[len(begaranden) - 1]
        with patch.object(atelje, 'session', return_value={'session_id': None, 'structured_output': svar}), \
                patch.object(skapande, 'komplettera', komplettera), patch.object(skapande, 'kanal_fel', return_value=None), \
                patch.object(skapande, 'senaste_paket', return_value=None), \
                patch.object(kompetens, 'kravbrister', return_value=[]), patch.object(kompetens, 'kvitto', return_value={}), \
                patch.object(kd, 'forska_prompt', lambda *a, **k: 'PROMPT'), patch.object(bildkedja, 'transkript', return_value=None), \
                patch.object(rk, 'sokningar', return_value=[]), patch.object(rk, 'verifiera_upptackt', return_value={'vag': 'galleri', 'kalla': 'x'}), \
                patch.object(rk, 'researchbrister', side_effect=[['inspirationsgenomgången har 1 fångade sajter ur gallerierna (arbetsregeln: minst 2)'], [], []]), \
                patch.object(rk, 'researchluckor', return_value={'bransch': 0, 'inspiration': 1}):
            post = kd.forska(SLUG, 2, skiss=True)
        self.assertEqual(len(begaranden), 2)
        self.assertIn('tjanster', begaranden[1], 'tjänsterna som inte blev klara frågas igen')
        self.assertEqual(post['tjanster'], {'rc': 0})


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

    def test_samma_sida_med_olika_bildval_profileras_en_gang(self):
        # granskningen 2026-10-10, fynd 6: kandidatens eget bildval gav förr en egen nyckel per kandidat
        a = self.paket('alpha', 'https://alpha.example.com/')
        d = self.ref / 'paket-v01'
        andra = d / 'alpha' / '01-sida' / 'vy-1440-forsta.png'
        andra.write_bytes(b'en annan bild ur samma sida')
        pk = json.loads((d / 'PAKET.json').read_text())
        pk['kandidater'][0]['sidor'][0]['filer'].append('alpha/01-sida/vy-1440-forsta.png')
        (d / 'PAKET.json').write_text(json.dumps(pk))
        b = dict(a, referensbilder=[str(andra)])
        resultat = {}
        tradar = [threading.Thread(target=lambda kid, k: resultat.__setitem__(kid, self.kor({'kandidater': {kid: k}})), args=x) for x in (('k01', a), ('k02', b))]
        for t_ in tradar:
            t_.start()
        for t_ in tradar:
            t_.join()
        self.assertTrue(all(r_['ok'] for r_ in resultat.values()), resultat)
        self.assertEqual(self.calls, ['https://alpha.example.com/'])
        # en ändrad bild på sidan, också en som ingen kandidat valt, ger en ny profil
        andra.write_bytes('ändrad'.encode())
        self.assertTrue(self.kor({'kandidater': {'k01': a}})['ok'])
        self.assertEqual(len(self.calls), 2)

    def ofullstandig(self, namn, adress):
        k = self.paket(namn, adress)
        f = self.ref / 'paket-v01' / 'PAKET.json'
        pk = json.loads(f.read_text())
        for c in pk['kandidater']:
            if c['namn'] == namn:
                c['ok'] = c['sidor'][0]['ok'] = False
        f.write_text(json.dumps(pk))
        return k

    def test_en_annan_referens_ofullstandiga_sida_stoppar_inte_huvudreferensen(self):
        # körprovet 2026-10-11 (k01): huvudreferensen var en Refero-stil, och en annan referens sida med kakdialog i
        # bilderna stoppade profileringen fast bara huvudreferensens sidor profileras
        palet = self.ofullstandig('palet', 'https://palet.example.com/')
        alpha = self.paket('alpha', 'https://alpha.example.com/')
        stil = {'huvudreferens': 'Referos stil FORA – Color-blocked gallery walls', 'utgangspunkt': {'slag': 'refero_stil'},
                'referensbilder': palet['referensbilder'] + alpha['referensbilder']}
        res = self.kor({'kandidater': {'k01': stil}})
        self.assertTrue(res['ok'], res)
        self.assertEqual(res['kandidater']['k01']['profiler'], [])
        self.assertEqual(self.calls, [])
        res = self.kor({'kandidater': {'k01': dict(alpha, referensbilder=palet['referensbilder'] + alpha['referensbilder'])}})
        self.assertTrue(res['ok'], res)
        self.assertEqual(self.calls, ['https://alpha.example.com/'], 'bara huvudreferensens sida profileras')
        res = self.kor({'kandidater': {'k01': palet}})
        self.assertFalse(res['ok'], 'huvudreferensens egen ofullständiga sida stoppar som förut')
        self.assertIn('inte fullständigt fångad', res['kandidater']['k01']['brister'][0])

    def test_huvudreferens_som_ar_en_sajt_kraver_sin_bild_vilket_slag_planen_an_anger(self):
        # granskningen 2026-10-11, fynd 1: andra referensers bilder filtrerades bort och slaget refero_stil släppte igenom
        # en huvudreferens som är en fångad sajt i paketet, utan profil
        self.paket('tekt', 'https://tekt.example.com/')
        cox = self.paket('cox', 'https://cox.example.com/')
        res = self.kor({'kandidater': {'k01': {'huvudreferens': 'Tekt — rubrikerna', 'utgangspunkt': {'slag': 'refero_stil'},
                                               'referensbilder': cox['referensbilder']}}})
        self.assertFalse(res['ok'], res)
        self.assertIn('saknar matchande paketerad bild: tekt', res['kandidater']['k01']['brister'][0])
        self.assertEqual(self.calls, [])

    def test_huvudreferens_med_parentes_och_kolon(self):
        # körprovet 2026-10-11 (k02): "norwegian-crafts (fångad i paket-v05: 01-start och 02-about)" lästes som
        # "norwegian-crafts (fangad i paket-v05", eftersom namnet kapades vid kolonet före parentesen
        alpha = self.paket('alpha', 'https://alpha.example.com/')
        res = self.kor({'kandidater': {'k01': dict(alpha, huvudreferens='alpha (fångad i paket-v01: 01-sida och 02-om)')}})
        self.assertTrue(res['ok'], res)
        self.assertEqual(self.calls, ['https://alpha.example.com/'])
        self.assertEqual(kd.referensens_namn('alpha (fångad i paket-v01: 01-sida och 02-om) — bär typografin'), 'alpha')
        self.assertEqual(kd.referensens_namn('Tekt (tekt.com.au) — rubrikerna'), 'tekt')
        self.assertEqual(kd.referensens_namn('Snick: snickeri i Umeå'), 'snick')

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

    def test_profilbristen_ar_underlag_och_gors_inte_om_i_en_slinga(self):
        # ägarens uppdrag 2026-10-11 om designflödet: en ofullständig profil stoppar inte skaparen; den görs en gång per
        # försök, och bristen står i statusen och skaparens prompt (profil_rader)
        anrop, skissade = [], []

        def falsk(slug, kid):
            anrop.append(kid)
            return {'ok': False, 'brister': ['syntetisk brist']}
        import ab
        with patch.object(kd, 'profilrapport', falsk), patch.object(ab, 'skisskrav', lambda slug: None), \
                patch.object(ab, 'skissavslutad', lambda slug, kid: kd.las_status(slug, kid)):
            self.assertTrue(kd.referensprofil_klar(SLUG, 'k01'))
            st = kd.las_status(SLUG, 'k01')
            self.assertEqual(anrop, ['k01'], 'ett försök')
            self.assertEqual(st['status'], 'planerad', 'statusen står kvar: skaparen får börja')
            self.assertEqual(st['referensprofil']['brister'], ['syntetisk brist'])
            self.assertIsNone(st.get('referensprofil_brister'))
            self.assertTrue(any('syntetisk brist' in r for r in kd.profil_rader(SLUG, 'k01')))

    def test_en_aldre_starts_profilsparr_tas_upp_och_det_tekniska_omforsoket_forblir_ett(self):
        # granskningen 2026-10-10, fynd 1: en profilbrist i ett tekniskt omförsök fick kandidaten att fastna för alltid; en
        # äldre starts spärr (status fel med referensprofil_brister) återställs, och omförsöket görs med sitt skäl
        kd.satt_status(SLUG, 'k01', 'fel', 'referensprofilen är ofullständig, så skaparen startar inte: syntetisk', forsok=1,
                       referensprofil_brister={'tid': kd.nu(), 'brister': ['syntetisk brist'], 'status_fore': 'fel',
                                               'skal_fore': 'bygget föll: syntetiskt', 'tekniskt_fel_fore': True}, tekniskt_fel=False)
        self.assertTrue(kd.ska_skapas(kd.las_status(SLUG, 'k01')))
        skissade = []
        import ab
        with patch.object(kd, 'skissa', side_effect=lambda slug, kid, fel=None: skissade.append(fel) or kd.satt_status(slug, kid, 'klar', 'x')), \
                patch.object(ab, 'skisskrav', lambda slug: None), patch.object(ab, 'skissavslutad', lambda slug, kid: kd.las_status(slug, kid)), \
                patch.object(kd, 'skaparbrister', return_value=[]):
            kd.behandla_skiss(SLUG, 'k01')
        self.assertEqual(skissade, ['bygget föll: syntetiskt'], 'nästa start gör det tekniska omförsöket med sitt skäl')
        self.assertIsNone(kd.las_status(SLUG, 'k01').get('referensprofil_brister'))

    def test_redovisningen_skiljer_korningens_tid_fran_kedjans(self):
        # kandidatprovet 2026-10-11: "väntan till första valbara skissen: 1266 minuter" räknades från kedjans första start
        # genom fyra körningar och uppehåll, och ingen kandidat gick att välja
        status = {'startad': '2026-10-11T21:18:34Z', 'tider': {'start': '2026-10-11T00:21:28Z', 'klar': '2026-10-11T21:33:34Z'}}
        kd.satt_status(SLUG, 'k01', 'ofullstandig', 'syntetiskt')
        rader = kd.denna_korningens_tider(SLUG, status, '2026-10-11T21:27:28Z')
        self.assertIn('9 minuter till första bedömbara version, 15 minuter totalt; 0 av 1 kandidater går att välja', ' '.join(rader))
        self.assertIn('kedjans första start 2026-10-11T00:21:28Z', rader[0])
        self.assertEqual(kd.denna_korningens_tider(SLUG, {'startad': '2026-10-11T00:21:28Z', 'tider': status['tider']}, None), [],
                         'en körning som är kedjans första har inga egna rader')
        self.assertIn('i en tidigare körning', ' '.join(kd.denna_korningens_tider(SLUG, status, '2026-10-11T05:00:00Z')))

    def test_profilsteget_behaller_skalet_och_ett_stopp_ar_ett_avbrott(self):
        kd.satt_status(SLUG, 'k01', 'ofullstandig', 'förra försökets brister: menyn öppnar ingenting', forsok=1)
        with patch.object(kd, 'profilrapport', referensfixtur.profilrapport(kd)):
            self.assertTrue(kd.referensprofil_klar(SLUG, 'k01'))
        self.assertEqual(kd.las_status(SLUG, 'k01')['skal'], 'förra försökets brister: menyn öppnar ingenting', 'läget fulls andra försök läser skälet')
        fore = kd.las_status(SLUG, 'k01')
        atelje.STOPP.set()
        try:
            with patch.object(kd, 'profilrapport', return_value={'ok': False, 'brister': ['slutkod -9']}):
                with self.assertRaises(atelje.Stoppad):
                    kd.referensprofil_klar(SLUG, 'k01')
        finally:
            atelje.STOPP.clear()
        efter = kd.las_status(SLUG, 'k01')
        self.assertEqual((efter['status'], efter.get('referensprofil_brister'), efter.get('referensprofil')),
                         (fore['status'], None, fore.get('referensprofil')), 'ett stopp är ingen profilbrist')

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
            # sajtens bygge är npm run build; en kandidat byggs med studions förhandsbygge (prova.STUDIOBYGGE, DS1)
            if any(str(x) in ('build', str(prova.STUDIOBYGGE)) for x in cmd):
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

    def test_specialfil_eller_oläsbar_fil_ger_ingen_identitet_och_ingen_hangning(self):
        os.mkfifo(self.sajt / 'src' / 'ror')
        self.assertIsNone(prova.kallidentitet(self.sajt, prova.byggkommando(self.sajt)))
        prova.bygg_inom_grans(self.sajt)
        prova.bygg_inom_grans(self.sajt)
        self.assertEqual(self.byggen, 2, 'utan identitet byggs det varje gång')

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

    def test_okand_version_intygar_ingenting_och_en_fallen_forhandsvisning_tar_inte_kandidaten(self):
        kid = 'k01'
        vd = kd.kdir(SLUG, kid) / 'varv' / 'start' / 'varv-01'
        vd.mkdir(parents=True)
        for n_ in forhandsvisa.LAS:
            (vd / n_).write_bytes(referensfixtur.PNG)
        kd.satt_status(SLUG, kid, 'under_arbete', 'skiss')
        with patch.object(forhandsvisa, 'forhandsvisa', side_effect=OSError('försvann under läsningen')), \
                patch.object(prova, 'byggidentitet', return_value=None), \
                patch.object(atelje, 'session', side_effect=AssertionError('ingen kritik på bilder av okänd version')):
            self.assertIsNone(kd.skisskritik(SLUG, kid))
        self.assertEqual(kd.las_status(SLUG, kid)['status'], 'under_arbete')


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
                patch.object(kd, 'planbrist', return_value=None):
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

    def test_en_fallen_komplettering_falller_inte_en_plan_som_racker(self):
        bas = {x: self.plan.get(x) for x in ('bransch', 'forebilder_utanfor')}
        forsta = dict(bas, variation='v', kandidater=[self.uppdrag(i) for i in range(1, 9)])

        def session(prompt, verktyg, ut, schema=None, *a, **k):
            self.anrop.append(prompt)
            if len(self.anrop) == 2:
                raise subprocess.TimeoutExpired(['claude'], 3000)
            return {'session_id': None, 'structured_output': forsta}
        with patch.object(atelje, 'session', session), patch.object(kompetens, 'kravbrister', return_value=[]), \
                patch.object(kd, 'plan_prompt', lambda *a, **k: 'PLAN'), patch.object(kd, 'referenskedjebrist', return_value=None), \
                patch.object(kd, 'referensbrist', return_value=None), patch.object(kd, 'planbrist', return_value=None), \
                patch('referenskontrakt.planbrister', return_value=[]):
            ids = kd.planera(SLUG, 10, 'skiss')
        plan = json.loads((kd.rot(SLUG) / 'KANDIDATPLAN.json').read_text())
        self.assertEqual(len(ids), 8)
        self.assertIn('kompletteringen föll', plan['brist_mot_begart'])

    def test_en_felklassad_rad_i_genomgangen_rensas_och_raknas_inte(self):
        # kandidatprovet 2026-10-11: planen föll två gånger på en enda rad (en inspirationssajt i branschgenomgången) fast
        # arbetsregelns täckning var uppfylld; det giltiga uppdraget gick förlorat
        import referenskontrakt as rk
        fel_rad = dict(referensfixtur.branschrad(SLUG, referensfixtur.GALLERI[0]))
        plan = dict(self.plan, bransch=list(self.plan['bransch']) + [fel_rad])
        self.assertTrue(any('inte en branschsajt' in x for x in rk.planbrister(SLUG, self.u, plan)), 'raden är ogiltig')
        rensad, bort = rk.rensa_genomgangar(SLUG, self.u, plan)
        self.assertEqual([b['sajt'] for b in bort], [referensfixtur.GALLERI[0]])
        self.assertEqual(rk.planbrister(SLUG, self.u, rensad), [], 'täckningen av de giltiga raderna räcker')
        self.assertNotIn(fel_rad, rensad['bransch'])
        # utan tillräckligt många giltiga rader stoppar täckningen planen som förut
        bara_fel = dict(plan, bransch=[fel_rad, self.plan['bransch'][0]])
        rensad2, _bort2 = rk.rensa_genomgangar(SLUG, self.u, bara_fel)
        self.assertTrue(any('branschgenomgången har 1 giltiga rader' in x for x in rk.planbrister(SLUG, self.u, rensad2)))
        # genom planeringen: planen skrivs med de giltiga raderna, den bortrensade redovisas, och försöket bokförs
        bas = {x: plan.get(x) for x in ('bransch', 'forebilder_utanfor')}
        _b, ids = self.kor([dict(bas, variation='v', kandidater=[self.uppdrag(i) for i in range(1, 11)])])
        k = json.loads((kd.rot(SLUG) / 'KANDIDATPLAN.json').read_text())
        self.assertEqual(len(ids), 10)
        self.assertEqual([b['sajt'] for b in k['genomgang_bortrensade']], [referensfixtur.GALLERI[0]])
        self.assertIn('Bortrensade rader i genomgångarna', (kd.rot(SLUG) / 'KANDIDATPLAN.md').read_text())
        rader = [json.loads(x) for x in (kd.rot(SLUG) / 'PLANERING-forsok.jsonl').read_text().splitlines()]
        self.assertEqual([(x['forsok'], x['planfel'], len(x['genomgang_bortrensade'])) for x in rader], [(1, [], 1)])

    def test_tio_giltiga_gor_ingen_komplettering(self):
        bas = {x: self.plan.get(x) for x in ('bransch', 'forebilder_utanfor')}
        _bas, ids = self.kor([dict(bas, variation='v', kandidater=[self.uppdrag(i) for i in range(1, 11)])])
        self.assertEqual((len(self.anrop), len(ids)), (1, 10))


class Aterupptag(Grund):
    """Ägarens godkännande 2026-10-11: skaparens svar på kritiken kan fortsätta skaparens egen konversation (samma kandidat
    och konversation, separat kvitto per fortsättning, bevarad historik, oförändrad kritiker). Prövat mekaniskt med
    syntetiska transkript i Claude Codes radformat; det verkliga provet görs separat."""

    def setUp(self):
        super().setUp()
        import bildkedja
        self.bk = bildkedja
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.prefix = 'kunder/%s/kandidater/k01/sajt/src/' % SLUG

    def skriv(self, sid, handelser, kopia=None, komprimera=False, kontext=90000):
        import uuid as uuid_
        rader = [dict(r, sessionId=sid) for r in (kopia or [])]
        if not kopia:
            rader.append({'type': 'attachment', 'uuid': str(uuid_.uuid4()), 'sessionId': sid,
                          'attachment': {'type': 'deferred_tools_delta', 'addedNames': ['mcp__refero__refero_search_styles']}})
            rader.append({'type': 'attachment', 'uuid': str(uuid_.uuid4()), 'sessionId': sid,
                          'attachment': {'type': 'skill_listing', 'isInitial': True, 'names': ['refero-design']}})
            rader.append({'type': 'user', 'uuid': str(uuid_.uuid4()), 'sessionId': sid, 'message': {'role': 'user', 'content': 'uppdraget'}})
        for i, (namn, inp) in enumerate(handelser, 1):
            tid = '%s-%d' % (sid[:8], i)
            rader.append({'type': 'assistant', 'uuid': str(uuid_.uuid4()), 'sessionId': sid,
                          'message': {'role': 'assistant', 'usage': {'input_tokens': 10, 'cache_read_input_tokens': kontext - 10},
                                      'content': [{'type': 'tool_use', 'id': tid, 'name': namn, 'input': inp}]}})
            rader.append({'type': 'user', 'uuid': str(uuid_.uuid4()), 'sessionId': sid,
                          'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': tid, 'content': [{'type': 'text', 'text': 'ok'}]}]}})
        if komprimera:
            rader.append({'type': 'system', 'subtype': 'compact_boundary', 'uuid': str(uuid_.uuid4()), 'sessionId': sid, 'content': 'Conversation compacted'})
        d = self.bk.PROJEKT / 'p'
        d.mkdir(parents=True, exist_ok=True)
        (d / (sid + '.jsonl')).write_text('\n'.join(json.dumps(r) for r in rader) + '\n')
        return rader

    def kompetens_steg(self):
        roller = kompetens.for_pass('skapa')
        skills, _ = kompetens.aktiverbara([f for roll in roller for f in roll['karna']])
        return [('Skill', {'skill': self.bk.skillkommando(s) or s}) for s in skills] + [
            ('Read', {'file_path': str(atelje.ROOT / f)}) for f in kompetens.lasfiler('skapa')]

    def par(self, komprimera=False, avtryck_lika=True):
        import uuid as uuid_
        a, b = str(uuid_.uuid4()), str(uuid_.uuid4())
        andring = ('Write', {'file_path': str(atelje.ROOT / self.prefix / 'pages' / 'index.astro'), 'content': 'x'})
        ra = self.skriv(a, self.kompetens_steg() + [andring], komprimera=komprimera)
        self.skriv(b, [andring], kopia=ra)
        self.bk.registrera_fortsattning(b, a, avtryck_lika=avtryck_lika, roll='skiss-svar')
        return a, b

    def test_fortsattningens_vy_har_bara_egna_rader_och_historiken_bevaras(self):
        a, b = self.par()
        hel, vy = self.bk.transkript_hel(b), self.bk.transkript(b)
        self.assertNotEqual(hel, vy)
        arvda = self.bk.uuider(vy) & self.bk.uuider(self.bk.transkript_hel(a))
        rader_vy = [json.loads(x) for x in vy.read_text().splitlines()]
        self.assertTrue(arvda and all(r['type'] == 'attachment' for r in rader_vy if r['uuid'] in arvda),
                        'av det ärvda bara lägesbilagorna (sonden 2026-10-11: en fortsättning skriver inga egna)')
        import observation
        self.assertEqual(sorted(observation.las_session(vy).get('mcp') or {}), ['refero'], 'MCP-läget syns i fortsättningens vy')
        self.assertGreater(len(hel.read_text().splitlines()), len(vy.read_text().splitlines()), 'fortsättningens hela fil står kvar')
        ml = self.bk.metodlasning(b, kompetens.lasfiler('skapa'), skrivprefix=self.prefix)
        self.assertEqual((ml.get('fore'), ml.get('efter')), ([], []), 'ursprungets läsningar räknas aldrig som fortsättningens')
        self.assertEqual(self.bk.fortsattning(a), None)
        self.assertEqual(self.bk.fortsattning(b)['ursprung'], a)

    def test_separat_kvitto_med_giltigt_arv(self):
        a, b = self.par()
        kv = kompetens.kvitto([{'session_id': a}, {'session_id': b}], 'skapa', skrivprefix=self.prefix)
        p2 = kv['per_session'][1]
        self.assertTrue(p2['arv']['giltigt'], p2['arv'])
        self.assertEqual(p2['arv']['fran'], a)
        self.assertEqual(sorted(p2['lasta']), sorted(kompetens.lasfiler('skapa')))
        self.assertNotIn('arv', kv['per_session'][0])
        self.assertEqual(kompetens.kravbrister(kv, 'skapa'), [])

    def test_komprimering_eller_andrade_filer_ger_inget_arv(self):
        for kw, ord_ in (({'komprimera': True}, 'komprimerades'), ({'avtryck_lika': False}, 'ändrades')):
            with self.subTest(**kw):
                a, b = self.par(**kw)
                kv = kompetens.kvitto([{'session_id': a}, {'session_id': b}], 'skapa', skrivprefix=self.prefix)
                arv = kv['per_session'][1]['arv']
                self.assertFalse(arv['giltigt'])
                self.assertIn(ord_, arv['skal'])
                self.assertTrue(any(x.startswith('session 2: kärnan saknas') for x in kompetens.kravbrister(kv, 'skapa')))

    def test_villkoren_for_att_ateruppta(self):
        import uuid as uuid_
        a = str(uuid_.uuid4())
        self.skriv(a, self.kompetens_steg())
        avtryck = kompetens.avtryck('skapa')
        self.assertEqual(kd.svar_aterupptag(SLUG, 'k01', [], avtryck)[0], None)
        self.assertIn('avbröts', kd.svar_aterupptag(SLUG, 'k01', [{'session_id': a, 'avbruten': 'tog slut'}], avtryck)[1])
        self.assertIn('ändrats', kd.svar_aterupptag(SLUG, 'k01', [{'session_id': a}], 'annat-avtryck')[1])
        self.assertEqual(kd.svar_aterupptag(SLUG, 'k01', [{'session_id': a}], avtryck), (a, None))
        k_ = str(uuid_.uuid4())
        self.skriv(k_, self.kompetens_steg(), komprimera=True)
        self.assertIn('komprimerats', kd.svar_aterupptag(SLUG, 'k01', [{'session_id': k_}], avtryck)[1])
        stor = str(uuid_.uuid4())
        self.skriv(stor, self.kompetens_steg(), kontext=kd.SVAR_ATERUPPTAG_TAK + 1)
        self.assertIn('taket', kd.svar_aterupptag(SLUG, 'k01', [{'session_id': stor}], avtryck)[1])
        self.assertIn('avtrycket', kd.svar_aterupptag(SLUG, 'k01', [{'session_id': a}], None)[1])
        text = kd.svar_fortsattning_prompt(SLUG, 'k01', {'varv': 2, 'storsta_problem': 'rubriken', 'rekommendation': 'fortsätt'}, 12)
        self.assertIn('Fortsättning av din egen konversation', text)
        self.assertIn('Läs inte om kärnan', text)
        self.assertIn('Komprimeras', text)
        self.assertNotIn('Detta är en ny session', text)
        self.assertFalse(kd.SVAR_ATERUPPTAG, 'avslaget som standard')

    def test_session_far_samma_argument_och_registreras(self):
        import uuid as uuid_
        a = str(uuid_.uuid4())
        self.skriv(a, [])
        with open(self.bk.PROJEKT / 'p' / (a + '.jsonl'), 'a') as f_:
            f_.write(json.dumps({'type': 'cost-state', 'sessionId': a, 'totalCostUSD': 3.0, 'totalAPIDuration': 4000,
                                 'modelUsage': {'claude-opus-5-5': {'costUSD': 3.0, 'outputTokens': 60}}}) + '\n')
        logg = self.tmp / 'args.json'
        falsk = self.tmp / 'claude'
        falsk.write_text('#!/usr/bin/env python3\nimport json, sys, uuid\nargs = sys.argv[1:]\n'
                         'open(%r, "a").write(json.dumps(args) + "\\n")\n'
                         'sid = args[args.index("--session-id") + 1] if "--session-id" in args else str(uuid.uuid4())\n'
                         'print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "session_id": sid, "result": "ok",'
                         ' "total_cost_usd": 5.0, "duration_api_ms": 9000, "num_turns": 3,'
                         ' "modelUsage": {"claude-opus-5-5": {"costUSD": 5.0, "outputTokens": 100}}}))\n' % str(logg))
        falsk.chmod(0o700)
        with patch.object(atelje, 'claude', return_value=str(falsk)), patch.object(atelje, 'observerad', return_value=(None, None)):
            ny = atelje.session('svara', ['Read'], self.tmp / 'svar-ny.json', modell='claude-opus-5-5', effort='high')
            ater = atelje.session('svara', ['Read'], self.tmp / 'svar-ater.json', modell='claude-opus-5-5', effort='high',
                                  aterupptag=a, fortsattning={'avtryck_lika': True, 'roll': 'skiss-svar'})
        args = [json.loads(x) for x in logg.read_text().splitlines()]
        # Claude Code räknar fortsättningens kostnad sammanlagd med ursprungets (sonden 2026-10-11): bara den egna står kvar
        ny_svar, ater_svar = (json.loads((self.tmp / n).read_text()) for n in ('svar-ny.json', 'svar-ater.json'))
        self.assertEqual((ny_svar['total_cost_usd'], 'fortsattning' in ny_svar), (5.0, False), 'en ny session rörs inte')
        self.assertEqual(ater_svar['total_cost_usd'], 2.0)
        self.assertEqual(ater_svar['modelUsage']['claude-opus-5-5'], {'costUSD': 2.0, 'outputTokens': 40})
        self.assertEqual((ater_svar['duration_api_ms'], ater_svar['num_turns']), (5000, 3))
        self.assertEqual(ater_svar['fortsattning']['kumulativt']['total_cost_usd'], 5.0)
        utan = atelje.egen_forbrukning({'total_cost_usd': 5.0, 'num_turns': 1}, str(uuid_.uuid4()))
        self.assertNotIn('total_cost_usd', utan, 'utan ursprungets kostnadsläge är den egna kostnaden okänd')
        i = args[1].index('--resume')
        self.assertEqual(args[1][i:i + 3], ['--resume', a, '--fork-session'])
        self.assertEqual(args[1][:i] + args[1][i + 3:], args[0], 'samma behörigheter, MCP-konfiguration, modell och effort som en ny session')
        self.assertEqual(self.bk.fortsattning(ater['session_id'])['ursprung'], a)
        self.assertIsNone(self.bk.fortsattning(ny['session_id']))
        self.assertTrue((self.tmp / 'svar-ny.json').is_file(), 'ursprungets svar och metadata skrivs aldrig om')
        with self.assertRaises(ValueError):
            atelje.session('x', ['Read'], self.tmp / 'svar-blind.json', aterupptag=a, blind=str(self.tmp / 'tillat.json'))
        # granskningen 2026-10-11, fynd 4: en registrering som faller startar ingen fortsättning och syns som ett fel som
        # anroparen hanterar (svaret räknas som avbrutet), aldrig som ett OSError som lämnar försöket under arbete
        import uuid as uuid_
        for kand_id, startar in ((str(uuid_.uuid4()), False), (None, True)):  # id:t känt före starten (observationen), annars ur svaret
            fore = len(logg.read_text().splitlines())
            with patch.object(atelje, 'claude', return_value=str(falsk)), patch.object(atelje, 'observerad', return_value=(kand_id, None)), \
                    patch.object(self.bk, 'registrera_fortsattning', side_effect=OSError('syntetiskt skrivfel')):
                with self.assertRaisesRegex(RuntimeError, 'kunde inte registreras'):
                    atelje.session('svara', ['Read'], self.tmp / 'svar-fel.json', modell='claude-opus-5-5', effort='high',
                                   aterupptag=a, fortsattning={'avtryck_lika': True})
            self.assertEqual(len(logg.read_text().splitlines()) - fore, int(startar), 'ingen session startar när id:t är känt')


class Kontrollerna(unittest.TestCase):
    """A och punkt 4."""

    def test_motsagelsefullt_aktiveringskrav_stoppar_fore_forsta_sessionen(self):
        # sessionens init-lista bär mapparnas namn, också de användaranropade (sessionsprovet 2026-10-10, 76 skills)
        c = {'resultat': 'ok', 'tid': 'nu', 'skills': sorted(f.parent.name for f in (ROOT / '.claude' / 'skills').glob('*/SKILL.md'))}
        vag = {'id': 'kandidatflodet', 'fas': 'fore_research'}
        ok = startkontroll.aktiveringsrader(c, True, vag)
        self.assertEqual(ok[0]['resultat'], 'ok', ok)
        self.assertIn('användaranropade, läses hela', ok[0]['detalj'])
        # skillverktyget i sessionen saknar en skill som kvittot kräver aktiverad
        fel = startkontroll.aktiveringsrader(dict(c, skills=[x for x in c['skills'] if x != 'refero-design']), True, vag)
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
        # en ny körning prövar också rollerna efter researchen (granskningen 2026-10-10, fynd 8): en skill som bara
        # skaparen eller kritiken har saknas i sessionen och stoppar ändå före researchen
        _r, efter = startkontroll.fasens_roller({'id': 'kandidatflodet', 'fas': 'efter_research'})
        _r, fore = startkontroll.fasens_roller(vag)
        bara_efter = sorted({s_ for x in efter for s_ in kompetens.aktiverbara(x['karna'] + x['valj'])[0]}
                            - {s_ for x in fore for s_ in kompetens.aktiverbara(x['karna'] + x['valj'])[0]})
        self.assertTrue(bara_efter)
        alla = sorted({s_ for x in efter + fore for s_ in kompetens.aktiverbara(x['karna'] + x['valj'])[0]})
        fel = startkontroll.aktiveringsrader(dict(c, skills=[s_ for s_ in alla if s_ != bara_efter[0]]), True, vag)
        self.assertEqual(fel[0]['resultat'], 'fel', fel)
        self.assertIn(bara_efter[0], fel[0]['detalj'])
        self.assertEqual(startkontroll.aktiveringsrader(dict(c, skills=alla), True, vag)[0]['resultat'], 'ok')

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
