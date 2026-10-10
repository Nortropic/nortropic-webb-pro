#!/usr/bin/env python3
"""Regressionsfall för GR-20261009-natt-omgranskning-codex (Codex omgranskning av nattens e31c156) som går genom de
berörda anroparna: N01 planprövningen bunden till planversionen genom kandidatflödets kor (misslyckad omplanering →
stopp → lyckat omförsök → ny prövning → skapande), N03 läsordningen i specialistpasset genom efter_fordjupning och den
sparade statusen, N04 läckagekontrollen av det som faktiskt pushas (git-historiken, mot ett lokalt bare-repo), blindningens
tillåtelselista vid varje läsning (kontroller/blindvakt.py) och kundrepot som arbetsrot i alla körvägar (R06). N02, N05 och
N06 prövas i prov_material.py, prov_bildstatus.py och prov_dokumentation.py. Syntetiska kunder och transkript, attrapper
vid modell- och tjänstegränserna; inga modeller, inget nät, ingen extern push."""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import korregister  # noqa: E402
from prov_kompetensflode import giltigt_kvitto


def transkript(steg):
    """Ett syntetiskt transkript i Claude Codes radformat under bildkedja.PROJEKT: (verktyg, indata) per anrop, med svar."""
    sid = str(uuid.uuid4())
    rader = [json.dumps({'type': 'user', 'timestamp': '2026-10-09T05:00:00.000Z', 'message': {'role': 'user', 'content': 'uppdraget'}})]
    for i, (namn, inn) in enumerate(steg):
        rader.append(json.dumps({'type': 'assistant', 'timestamp': '2026-10-09T05:00:%02d.000Z' % (i + 1), 'message': {'role': 'assistant', 'content': [
            {'type': 'tool_use', 'id': 'u%d' % i, 'name': namn, 'input': inn}]}}))
        rader.append(json.dumps({'type': 'user', 'timestamp': '2026-10-09T05:00:%02d.500Z' % (i + 1), 'message': {'role': 'user', 'content': [
            {'type': 'tool_result', 'tool_use_id': 'u%d' % i, 'content': 'ok'}]}}))
    p = bildkedja.PROJEKT / 'p'
    p.mkdir(parents=True, exist_ok=True)
    (p / (sid + '.jsonl')).write_text('\n'.join(rader) + '\n')
    return sid


def kompetenssteg(pass_):
    """Det giltiga modellunderlaget i fixturen aktiverar rollen och läser dess filer före arbetet."""
    roller = kompetens.for_pass(pass_)
    skills, _ = kompetens.aktiverbara([f for roll in roller for f in roll['karna']])
    return [('Skill', {'skill': bildkedja.skillkommando(s) or s}) for s in skills] + [
        ('Read', {'file_path': str(atelje.ROOT / f)}) for f in kompetens.lasfiler(pass_)]


class Lasordning(unittest.TestCase):
    """N03: specialistpassets beslut använder läsordningen. Arbete före den obligatoriska kärnläsningen ger ett omförsök
    från versionen före passet och aldrig genomford=true; ett tidigare försök maskerar aldrig det nya försökets brist, och
    en återställning som faller lämnar passet ej genomfört. Läst, observerat använt och bedömt hålls isär i posten."""
    SLUG = 'n03-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'N03 läsordningen'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.d = kd.kdir(self.SLUG, 'k01')
        (self.d / 'bilder' / 'start').mkdir(parents=True)
        for n in kd.PASSBILDER:
            (self.d / 'bilder' / 'start' / n).write_bytes(b'png')
        self.src = kd.ksajt(self.SLUG, 'k01') / 'src'
        (self.src / 'pages').mkdir(parents=True)
        self.version, self.ater, self.prompter, self.ordning = [1], [], [], []
        self.ater_fel = False

        def foto(slug, kid, skiss=None):
            self.version[0] += 1
            return kd.satt_status(slug, kid, 'klar', 'fotograferad', version='v%d' % self.version[0], axe={'allvarliga': 0})

        def ater(slug, kid, v):
            self.ater.append(v)
            if self.ater_fel:
                raise RuntimeError('bygget föll vid återställningen')
            return kd.satt_status(slug, kid, 'klar', 'återställd', version=v, axe={'allvarliga': 0})

        def session(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None):
            self.prompter.append(prompt)
            pass_ = prompt.split()[1]
            steg_ = kompetenssteg(pass_)
            aktivera = [x for x in steg_ if x[0] == 'Skill']
            las = [x for x in steg_ if x[0] == 'Read']
            skriv = [('Write', {'file_path': str(self.src / 'pages' / 'index.astro')})]
            verktyg_ = [('Bash', {'command': '.venv/bin/python -B kontroller/forhandsvisa.py %s --kandidat k01 --meny' % self.SLUG})]
            ordning = self.ordning.pop(0) if self.ordning else 'fore'
            if ordning == 'sen':  # arbetet först, kärnan sedan
                steg = skriv + aktivera + las + verktyg_
            elif ordning == 'saknar':  # en kärnfil saknas helt
                steg = aktivera + las[1:] + skriv + verktyg_
            else:
                steg = aktivera + las + skriv + verktyg_
            # skillen bakom ändringen är en som passet självt laddade (kompetens.redovisade_brister): rörelsens emil-animate,
            # granskningens better-accessibility
            so = {'kod_andrad': [{'skill': 'emil-animate' if pass_ == 'rorelse' else 'better-accessibility', 'vad': 'menyns övergång',
                                  'var': 'sidhuvudet', 'varfor': 'syfte'}],
                  'beteende_provat': [{'vad': 'menyn', 'hur': 'forhandsvisa --meny', 'resultat': 'öppnas',
                                       'bild': kd.rel(self.d / 'bilder' / 'start' / 'vy-390-forsta.png')}],
                  'visuell_bedomning': {'fore': 'a', 'efter': 'b', 'omdome': 'battre', 'skal': 'tydligare'}, 'ingen_andring': '',
                  'valda': [], 'passade_inte': [], 'kvarstar': []}
            svar = {'structured_output': so, 'session_id': transkript(steg)}
            Path(ut).write_text(json.dumps(svar))
            return svar

        self.stack.enter_context(patch.multiple(kd, fotografera=foto, aterstall_och_fotografera=ater, bevara_version=lambda *a, **k: None,
                                                designkontroll=lambda slug, kid: {'ok': True, 'fel': []}, verktyg=lambda *a, **k: [],
                                                pass_prompt=lambda slug, kid, pass_, saknade=None, dom=None: 'PASS %s saknade=%s' % (pass_, saknade)))
        self.stack.enter_context(patch.object(kompetens, 'verktyg', lambda *a, **k: []))
        self.stack.enter_context(patch.object(atelje, 'session', session))
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'förfinad', version='v1', axe={'allvarliga': 0})

    def rec(self, nyckel):
        return kd.las_status(self.SLUG, 'k01')['kompetens'][nyckel]  # den sparade statusen, inte returvärdet

    def test_sen_karna_i_bada_forsoken_ar_aldrig_genomford(self):
        self.ordning[:] = ['sen', 'sen', 'fore', 'fore']  # rörelsepasset läser sent två gånger; granskningspasset i ordning
        kd.efter_fordjupning(self.SLUG, 'k01', {'tid': 'a', 'text': 'x', 'uppdrag': {'typ': 'bygg_ut', 'resultat': 'hela startsidan', 'omfattning': ['/x/'], 'bevara': ['första vyn'], 'specialister': {'rorelse': 'andra', 'granskning': 'andra'}}})  # passen körs bara på uppdragets begäran (2026-10-09)
        r = self.rec('fordjupa:a:rorelse')
        self.assertIs(r['genomford'], False, 'arbete före kärnläsningen godkändes')
        self.assertTrue(r['sen_karna'] and r['kasserade_forsok'], r)
        self.assertTrue(any('läst först efter första ändringen' in x for x in r['kasserade_forsok'][0]['saknade']), r['kasserade_forsok'])
        self.assertTrue((self.d / 'svar-pass-fordjupa-a-rorelse-2.json').is_file(), 'inget omförsök')
        self.assertIn('läst först efter första ändringen', self.prompter[1], 'omförsöket fick inte veta bristen')
        self.assertEqual(self.ater[:1], ['v1'], 'det första försökets ändringar återställdes inte')
        # läst, observerat använt och bedömt hålls isär: läsordningen i kvittot, verktyget observerat, bedömningen redovisad
        karna = {x['roll']: x for x in r['kvitto']['tillstand']}
        self.assertTrue(any('läsordningen' in x['karna']['tillstand'] for x in karna.values()), r['kvitto']['tillstand'])
        self.assertEqual(r['anvanda_verktyg'], ['förhandsvisning'])
        self.assertEqual(r['visuell_bedomning']['omdome'], 'battre')
        self.assertIs(self.rec('fordjupa:a:granskning')['genomford'], True, 'ett pass i rätt ordning är genomfört')

    def test_sen_karna_i_forsta_forsoket_ger_omforsok(self):
        self.ordning[:] = ['sen', 'fore']
        kd.kompetenspass(self.SLUG, 'k01', 'rorelse', 'fordjupa:b', {'tid': 'b', 'text': 'x'})
        r = self.rec('fordjupa:b:rorelse')
        self.assertTrue((self.d / 'svar-pass-fordjupa-b-rorelse-2.json').is_file(), 'ingen ny session efter den sena läsningen')
        self.assertIs(r['genomford'], True, r)
        self.assertEqual((len(r['kvitto']['per_session']), r['sen_karna']), (1, []), 'bara omförsökets session räknas')
        self.assertEqual(r['kasserade_forsok'][0]['aterstalld_till'], 'v1')

    def test_ett_tidigare_forsok_maskerar_inte_det_nya_forsokets_brist(self):
        self.ordning[:] = ['saknar', 'sen']  # det första saknar en fil, omförsöket läser allt men först efter ändringen
        kd.kompetenspass(self.SLUG, 'k01', 'rorelse', 'fordjupa:c', {'tid': 'c', 'text': 'x'})
        r = self.rec('fordjupa:c:rorelse')
        self.assertIs(r['genomford'], False, 'omförsökets sena läsning maskerades')
        self.assertEqual(r['kvitto']['saknas'], [], 'omförsöket läste hela kärnan')
        self.assertTrue(r['sen_karna'])

    def test_aterstallning_som_faller_lamnar_passet_ej_genomfort(self):
        self.ordning[:] = ['sen']
        self.ater_fel = True
        kd.kompetenspass(self.SLUG, 'k01', 'granskning', 'fordjupa:e', {'tid': 'e', 'text': 'x'})
        r = self.rec('fordjupa:e:granskning')
        self.assertIs(r['genomford'], False)
        self.assertTrue(r['kasserade_forsok'] and 'aterstallning_fel' in r['kasserade_forsok'][0], r['kasserade_forsok'])

    def test_avbrutet_pass_tas_upp_och_provas_lika(self):
        kd.satt_status(self.SLUG, 'k01', 'forfinad', 'förfinad', version='v5', pass_pagar={'nyckel': 'fordjupa:f:rorelse', 'fore': 'v5', 'status': 'forfinad'})
        self.ordning[:] = ['sen', 'sen']
        kd.kompetenspass(self.SLUG, 'k01', 'rorelse', 'fordjupa:f', {'tid': 'f', 'text': 'x'})
        r = self.rec('fordjupa:f:rorelse')
        self.assertEqual(self.ater[0], 'v5', 'det avbrutna passet återställdes inte först')
        self.assertIs(r['genomford'], False)


class Planversion(unittest.TestCase):
    """N01: planprövningen är bunden till den planversion som skaparen får. Hela sekvensen genom kandidatflödets kor: en
    omplanering som misslyckas stoppar kandidaten, återupptagningen gör ett lyckat omförsök, den nya planen prövas, och
    först sedan får skaparen den; ett sparat prövningsdokument för en annan plan godkänner aldrig den nya. Attrapper bara
    vid sessionerna (prövningen och omplaneringen) och vid skaparen (skissa)."""
    SLUG = 'n01-prov'

    def setUp(self):
        import ab
        import skapande
        import urval
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'N01 planversionen'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.r = kd.rot(self.SLUG)
        self.handelser, self.provningar = [], []
        self.omplanering_lyckas, self.provning_faller = [False], [False]
        plan = {'tid': '2026-10-09T05:00:00Z', 'lage': 'skiss', 'kompetens': giltigt_kvitto('planera'), 'kandidater': {
            k: dict({f: '%s %s' % (f, k) for f, _r in kd.PLANFALT}, titel='Förslag %s' % k, hypotes='GAMMAL %s' % k, huvudreferens='egen riktning',
                    referensbilder=[]) for k in ('k01', 'k02')}}
        self.r.mkdir(parents=True)
        import referensfixtur  # referenskontraktet uppfyllt: provet prövar planversionen, inte startvillkoret
        plan = referensfixtur.uppfyll(atelje.UNDERLAG, self.SLUG, plan)
        self.referensbidrag = referensfixtur.bidrag(self.SLUG)
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        (self.r / kd.UPPDRAGSMATERIAL).write_text('{}')
        for i, k in enumerate(('k01', 'k02'), 1):
            kd.skriv_uppdrag(self.SLUG, k, plan['kandidater'][k], i, 2)
            kd.satt_status(self.SLUG, k, 'planerad', 'uppdraget skrivet', titel=plan['kandidater'][k]['titel'], hypotes=plan['kandidater'][k]['hypotes'])

        def session(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None):
            if schema is kd.PLANPROVNING_SCHEMA:
                if self.provning_faller[0]:
                    raise RuntimeError('prövningens session föll')
                self.provningar.append(prompt)
                self.handelser.append('planprovning')
                so = {'sammanfattning': 'prövad', 'kandidater': [
                    {'id': 'k01', 'bedomning': 'hypotesen bär inte', 'andringar': [],
                     'atergang': {'typ': 'ny_hypotes', 'skal': 'hypotesen bär inte kundens material', 'ny_hypotes': 'NY k01'}},
                    {'id': 'k02', 'bedomning': 'bär', 'andringar': [{'falt': 'typografi', 'nytt': 'PRÖVAD TYPOGRAFI k02', 'skill': 'impeccable', 'varfor': 'hierarkin'}]}]}
            elif isinstance(schema, dict) and 'OMPLANERING' in prompt:
                self.handelser.append('omplanering')
                hr = 'egen riktning' if self.omplanering_lyckas[0] else 'Xref'  # utan referensbilder avvisas en namngiven referens
                so = {'variation': 'omplanerad', 'kandidater': [dict({f: '%s omplanerad' % f for f, _r in kd.PLANFALT}, titel='k01 omplanerad',
                                                                     hypotes='NY HYPOTES k01', huvudreferens=hr, referensbilder=[],
                                                                     referensbidrag=self.referensbidrag)]}
            else:
                raise AssertionError('oväntad session: %s' % prompt[:80])
            svar = {'structured_output': so, 'session_id': transkript(kompetenssteg('planprovning' if schema is kd.PLANPROVNING_SCHEMA else 'planera'))}
            Path(ut).write_text(json.dumps(svar))
            return svar

        def skissa(slug, kid, fel=None):
            uppdrag = (kd.kdir(slug, kid) / 'UPPDRAG.md').read_text()
            self.handelser.append('skapare:%s:%s' % (kid, 'NY HYPOTES' if 'NY HYPOTES' in uppdrag else 'GAMMAL'))
            return kd.satt_status(slug, kid, 'klar', 'skiss klar', forsok=1,
                                  kompetens={'skiss:skapa': {'kvitto': giltigt_kvitto('skapa')}})

        self.stack.enter_context(patch.object(atelje, 'session', session))
        self.stack.enter_context(patch.multiple(kd, skissa=skissa, leverera_metod=lambda slug: {'skapa': {'sha': 'syntetisk-skaparmetod'}}, uppdragsmaterial=lambda *a, **k: {},
                                                plan_prompt=lambda *a, **k: 'PLANEN', regel_rader=lambda: [], metod_rader=lambda *a: [],
                                                research_rader=lambda *a: [], material_rader=lambda *a: [], PARALLELLT=1))
        self.stack.enter_context(patch.multiple(skapande, kritikrader=lambda *a, **k: [], fakta_rader=lambda *a, **k: [],
                                                forbjudna_termer=lambda *a, **k: []))
        self.stack.enter_context(patch.multiple(kompetens, prompt_rader=lambda *a, **k: [], verktyg=lambda *a, **k: []))
        self.stack.enter_context(patch.object(urval, 'vid_start', lambda *a, **k: {}))
        self.stack.enter_context(patch.multiple(ab, skisskrav=lambda slug: None, skissavslutad=lambda slug, kid: kd.las_status(slug, kid)))

    def kor(self):
        status = {'startad': '2026-10-09T05:00:00Z', 'lage': 'ny'}
        kd.kor(self.SLUG, status, lambda: None, n=2)
        return status

    def plan(self):
        return json.loads((self.r / 'KANDIDATPLAN.json').read_text())

    def test_misslyckad_omplanering_stopp_omforsok_ny_provning_sedan_skapande(self):
        self.kor()  # första starten: k01:s omplanering misslyckas
        s1 = kd.las_status(self.SLUG, 'k01')
        self.assertEqual((s1['status'], bool(s1.get('atergang_fel'))), ('fel', True), s1)
        self.assertEqual(self.handelser, ['planprovning', 'omplanering', 'skapare:k02:GAMMAL'], 'korrekt stopp: skaparen fick aldrig k01')
        self.omplanering_lyckas[0] = True
        self.handelser.clear()
        status = self.kor()  # återupptagningen: ett lyckat omförsök, och den nya planen prövas före skaparen
        self.assertEqual(self.handelser, ['omplanering', 'planprovning', 'skapare:k01:NY HYPOTES'],
                         'den nya planen gick till skaparen utan planprövning (N01)')
        pp = json.loads((self.r / 'PLANPROVNING.json').read_text())
        plan = self.plan()
        self.assertEqual(pp['provade']['k01'], kd.uppdrag_sha(plan['kandidater']['k01']), 'prövningen är bunden till den nya versionen')
        self.assertEqual(pp['provade']['k02'], kd.uppdrag_sha(plan['kandidater']['k02']), 'k02:s prövning gäller, oförändrad')
        self.assertEqual(pp['omprovning']['kandidater'], ['k01'])
        tidigare = json.loads((self.r / 'PLANPROVNING-tidigare-1.json').read_text())
        self.assertNotIn('k01', tidigare['provade'], 'den gamla prövningen släppte aldrig k01')
        self.assertIn('Omprövning: uppdragen k01', self.provningar[-1])
        self.assertEqual(plan['kandidater']['k02']['typografi'], 'PRÖVAD TYPOGRAFI k02', 'omprövningen ändrar inte ett redan prövat uppdrag')
        self.assertEqual(status['planprovning']['omprovning']['kandidater'], ['k01'])
        self.assertEqual(kd.las_status(self.SLUG, 'k01')['status'], 'klar')

    def test_en_gammal_provning_godkanner_inte_en_annan_plan(self):
        self.omplanering_lyckas[0] = True
        self.kor()  # k01 omplaneras i runda 1 och prövas i runda 2; båda byggs
        self.assertEqual(self.handelser[-2:], ['skapare:k01:NY HYPOTES', 'skapare:k02:GAMMAL'], self.handelser)
        kd.satt_status(self.SLUG, 'k02', 'planerad', 'ett nytt försök')  # k02 ska byggas igen, med en ändrad plan
        plan = self.plan()
        plan['kandidater']['k02']['hypotes'] = 'ÄNDRAD k02'
        (self.r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        self.handelser.clear()
        self.kor()
        self.assertEqual(self.handelser[0], 'planprovning', 'PLANPROVNING.json för den gamla planen släppte den ändrade (N01)')
        self.assertEqual(json.loads((self.r / 'PLANPROVNING.json').read_text())['provade']['k02'], kd.uppdrag_sha(self.plan()['kandidater']['k02']))

    def test_skaparen_far_inget_nar_den_nya_provningen_faller(self):
        self.kor()
        self.omplanering_lyckas[0] = True
        self.provning_faller[0] = True
        self.handelser.clear()
        with self.assertRaises(RuntimeError):
            self.kor()
        self.assertEqual(self.handelser, ['omplanering'], 'skaparen fick den nya planen fast prövningen föll')
        self.assertNotEqual(kd.las_status(self.SLUG, 'k01')['status'], 'klar')
        self.provning_faller[0] = False
        self.handelser.clear()
        self.kor()  # nästa återupptagning prövar planen och bygger först då
        self.assertEqual(self.handelser, ['planprovning', 'skapare:k01:NY HYPOTES'])

    def test_en_provning_som_inte_tacker_uppdraget_stoppar_skaparen(self):
        self.kor()
        self.omplanering_lyckas[0] = True
        verklig = kd.planprovning

        def utan_bindning(slug, bara=None, _foregaende=None):  # en prövning som skriver sitt besked utan den nya versionen
            self.handelser.append('planprovning utan bindning')
            (self.r / 'PLANPROVNING.json').write_text(json.dumps({'tid': 'x', 'andrade': 0, 'provade': {}}))
            return {'andrade': 0}
        self.handelser.clear()
        with patch.object(kd, 'planprovning', utan_bindning):
            self.kor()
        self.assertEqual(self.handelser, ['omplanering', 'planprovning utan bindning'], 'skaparen fick ett oprövat uppdrag')
        st = kd.las_status(self.SLUG, 'k01')
        self.assertEqual((st['status'], st['planprovning_saknas']['status_fore']), ('fel', 'planerad'), st)
        self.handelser.clear()
        with patch.object(kd, 'planprovning', verklig):
            self.kor()
        self.assertEqual(self.handelser, ['planprovning', 'skapare:k01:NY HYPOTES'])
        self.assertNotIn('planprovning_saknas', kd.las_status(self.SLUG, 'k01'))


HEMLIG = 'ghp_' + 'Q7' * 15  # ett syntetiskt nyckelmönster, aldrig en verklig nyckel
PRIVAT = 'underlag/n04-kund/BRIEF.md'


class Githistorik(unittest.TestCase):
    """N04: läckagekontrollen före push gäller det som faktiskt skickas: historiken, också vid den första fjärrskapningen
    och när ett äldre kundrepo återanvänds, och när något förbjudet först lagts till och sedan tagits bort. Granskningen och
    pushen gäller samma commit. Lokala bare-repon som fjärr (attrappen av gh i prov_kundrepo); inget skickas externt,
    ingen historik skrivs om, och beskeden återger aldrig värdet."""

    def setUp(self):
        import types
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import prov_kundrepo
        self.skriv_verksamhet = types.MethodType(prov_kundrepo.Kundrepo.skriv_verksamhet, self)
        self.gh_anrop = types.MethodType(prov_kundrepo.Kundrepo.gh_anrop, self)
        prov_kundrepo.Kundrepo.setUp(self)  # samma kund, attrapp av gh och tempkatalog som kundrepots prov
        import kundrepo
        self.kr = kundrepo
        self.slug = 'prov-kund'
        self.repo = self.k / 'kundrepo'

    def git(self, *a, cwd=None):
        r = subprocess.run(['git', '-c', 'user.name=Prov', '-c', 'user.email=prov@example.invalid', *a], cwd=str(cwd or self.repo),
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def lacka_och_borttagning(self, msg='anteckning'):
        """En syntetisk privat sökväg och en nyckel som läggs till och tas bort igen: arbetsträdet är rent efteråt."""
        (self.repo / 'anteckning.md').write_text('se %s\nnyckel %s\n' % (PRIVAT, HEMLIG))
        self.git('add', 'anteckning.md'); self.git('commit', '-qm', msg)
        lacka = self.git('rev-parse', 'HEAD')
        (self.repo / 'anteckning.md').unlink()
        self.git('add', '-A'); self.git('commit', '-qm', 'rent')
        self.assertEqual(self.kr.lackor_i(self.repo), [], 'arbetsträdet är rent: bara historiken bär läckan')
        return lacka

    def bare(self):
        return self.state / 'kund-prov-kund.git'

    def finns_i_fjarr(self, sha):
        return subprocess.run(['git', 'cat-file', '-e', sha], cwd=str(self.bare()), capture_output=True).returncode == 0

    def utan_varden(self, *texter):
        for t in texter:
            self.assertNotIn(HEMLIG, t, 'beskedet återger nyckeln')
            self.assertNotIn(PRIVAT, t, 'beskedet återger den privata sökvägen')

    def test_tillagd_och_borttagen_lacka_stoppar_pushen(self):
        self.skriv_verksamhet(False)
        kv = self.kr.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'skapat', kv['fjarr'])
        forsta = self.git('rev-parse', 'HEAD')
        lacka = self.lacka_och_borttagning()
        p = self.kr.push(self.slug)
        self.assertFalse(p['ok'], 'en tidigare commit med läckan pushades (N04)')
        self.assertFalse(self.finns_i_fjarr(lacka), 'läckans commit finns i fjärrepot')
        self.assertIn('anteckning.md', p['hinder']); self.assertIn(lacka[:12], p['hinder'])
        self.assertIn('en nyckel', p['hinder']); self.assertIn('Nortropics privata underlag', p['hinder'])
        self.utan_varden(p['hinder'], (self.k / 'KUNDREPO.json').read_text())
        self.assertEqual(self.git('rev-parse', 'main', cwd=self.bare()), forsta, 'fjärrets main är den granskade första pushen')
        self.assertTrue(self.git('cat-file', '-e', lacka) == '', 'historiken skrevs inte om')

    def test_forsta_fjarrskapningen_granskar_historiken(self):
        self.skriv_verksamhet(False)
        self.kr.skapa(self.slug, fjarr=False)
        lacka = self.lacka_och_borttagning()
        kv = self.kr.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'fel', kv['fjarr'])
        self.assertIn('läckagekontrollen', kv['fjarr']['fel'])
        self.assertEqual([a for a in self.gh_anrop() if a[:2] == ['repo', 'create']], [], 'inget fjärrepo skapades')
        self.assertFalse(self.bare().exists() and self.finns_i_fjarr(lacka))
        self.utan_varden(kv['fjarr']['fel'], (self.k / 'KUNDREPO.json').read_text())

    def test_ett_aldre_kundrepo_med_lacka_i_ett_commitmeddelande_ateranvands_inte_utan_granskning(self):
        self.skriv_verksamhet(False)
        self.repo.mkdir(parents=True)
        self.git('init', '-q', '-b', 'main')
        (self.repo / 'README.md').write_text('Äldre kundrepo\n')
        self.git('add', '-A'); self.git('commit', '-qm', 'Export från /Users/fiktiv/nortropic/%s' % PRIVAT)
        kv = self.kr.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'fel', kv['fjarr'])
        self.assertIn('commitmeddelandet', kv['fjarr']['fel'])
        self.utan_varden(kv['fjarr']['fel'])
        self.assertEqual([a for a in self.gh_anrop() if a[:2] == ['repo', 'create']], [])

    def test_granskningen_och_pushen_galler_samma_commit(self):
        self.skriv_verksamhet(False)
        self.kr.skapa(self.slug)
        (self.repo / 'sida.md').write_text('ren ändring\n'); self.git('add', 'sida.md'); self.git('commit', '-qm', 'ren')
        granskad = self.git('rev-parse', 'HEAD')
        verklig = self.kr.lackor_i
        flyttad = []

        def flyttar_main(rot):  # ett annat arbete committar en läcka medan granskningen pågår
            ut = verklig(rot)
            if not flyttad:
                (self.repo / 'sen.md').write_text('se %s\n' % PRIVAT); self.git('add', 'sen.md'); self.git('commit', '-qm', 'sen')
                flyttad.append(self.git('rev-parse', 'HEAD'))
            return ut
        with patch.object(self.kr, 'lackor_i', flyttar_main):
            p = self.kr.push(self.slug)
        self.assertTrue(flyttad)
        self.assertFalse(self.finns_i_fjarr(flyttad[0]), 'en commit som tillkom efter granskningen pushades')
        self.assertTrue(p['ok'], p)
        self.assertEqual((p['commit'], self.git('rev-parse', 'main', cwd=self.bare())), (granskad, granskad))

    def test_projektstarten_committar_bara_sina_egna_filer(self):
        self.kr.skapa(self.slug)
        (self.repo / 'kopierat-underlag.md').write_text('Kundens offert: 12 000 kr, betalas i mars.\n')  # privat, utan mönster
        self.kr.skapa(self.slug)
        self.assertNotIn('kopierat-underlag.md', self.git('ls-files'), 'projektstarten committade en fil den inte skrivit')

    def test_historiken_som_inte_gar_att_lasa_stanger(self):
        self.kr.skapa(self.slug)
        rad = self.kr.historikens_lackor(self.repo, '0' * 40)
        self.assertTrue(rad and 'gick inte att läsa' in rad[0][2], rad)


def png(w=4, h=3):
    import struct
    import zlib
    bit = lambda typ, d: struct.pack('>I', len(d)) + typ + d + struct.pack('>I', zlib.crc32(typ + d) & 0xffffffff)  # noqa: E731
    rad = b'\x00' + b'\x80\x80\x80' * w
    return b'\x89PNG\r\n\x1a\n' + bit(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + bit(b'IDAT', zlib.compress(rad * h)) + bit(b'IEND', b'')


# En attrapp av claude som gör det Claude Code gör med en läsning: kör varje PreToolUse-krok vars matcher passar
# verktyget, med krokens JSON på stdin och CLAUDE_PROJECT_DIR satt, och räknar läsningen som tillåten bara när ett
# verktyg står i --allowedTools eller en krok gav permissionDecision allow (dontAsk nekar resten). Det är provets modell
# av Claude Code, inte ett belägg för hur Claude Code faktiskt beter sig; det kräver ett verkligt sessionsprov.
FALSK_BLIND = r"""#!/usr/bin/env python3
import json, os, re, subprocess, sys
from pathlib import Path
a = sys.argv[1:]
logg = Path(os.environ['PROV_BLIND_LOGG'])
plan = json.loads(Path(os.environ['PROV_BLIND_PLAN']).read_text())
def lista(flagga):
    i = a.index(flagga) + 1; ut = []
    while i < len(a) and not a[i].startswith('--'):
        ut.append(a[i]); i += 1
    return ut
tillatna = lista('--allowedTools'); verktyg = a[a.index('--tools') + 1].split(',')
def regex(m):  # en regelväg i gitignore-form som reguljärt uttryck (** över kataloger, * inom en del)
    ut, i = '', 0
    while i < len(m):
        if m.startswith('**', i):
            ut, i = ut + '.*', i + 2
        else:
            ut, i = ut + {'*': '[^/]*', '?': '[^/]'}.get(m[i], re.escape(m[i])), i + 1
    return ut
nekade = []
for r_ in lista('--disallowedTools'):
    m_ = re.fullmatch(r'Read\((.*)\)', r_)
    if m_:
        v_ = m_.group(1)
        nekade.append(regex(os.getcwd() + '/' + v_[2:] if v_.startswith('./') else v_[1:] if v_.startswith('//') else v_))
def nekad(las):  # Read-förbuden gäller också Globs och Greps väg; ett förbud går före en tillåtelse
    v_ = (las['tool_input'].get('file_path') or las['tool_input'].get('path') or '')
    v_ = os.path.realpath(v_) if v_ else ''
    return bool(v_) and any(re.fullmatch(n_, v_) or re.fullmatch(n_, v_ + '/x') for n_ in nekade)
inst = json.loads(a[a.index('--settings') + 1]) if '--settings' in a else {}
for steg in plan['fore']:  # det som uppstår efter att sessionen startat och listan skrivits
    p = Path(steg['skapa']); p.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(steg['lank'], p) if steg.get('lank') else p.write_text(steg.get('text', 'SEN TEXT'))
beslut = []
for las in plan['lasningar']:
    tillat, skal = las['tool_name'] in tillatna, []
    for post in (inst.get('hooks') or {}).get('PreToolUse') or []:
        if not re.fullmatch(post.get('matcher') or '.*', las['tool_name']):
            continue
        for k in post['hooks']:
            r = subprocess.run(['/bin/sh', '-c', k['command']], input=json.dumps(dict(las, cwd=os.getcwd(), hook_event_name='PreToolUse')),
                               capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=os.environ['PROV_PROJEKT']))
            if r.returncode == 0 and '"allow"' in r.stdout:
                tillat = True
            elif r.returncode == 2:
                tillat = False; skal.append(r.stderr.strip())
    if nekad(las):
        tillat = False; skal.append('nekad av --disallowedTools')
    beslut.append({'las': las, 'tillat': tillat, 'skal': skal})
logg.write_text(json.dumps({'argv': a, 'cwd': os.getcwd(), 'tillatna': tillatna, 'verktyg': verktyg, 'beslut': beslut}))
so = {'storsta_problem': 'x', 'synliga_problem': [], 'generiskt': False, 'rekommendation': 'fortsätt', 'motivering': 'x',
      'bredder': [], 'tillstand': [], 'forebilder': [], 'valda': []}
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'structured_output': so, 'session_id': None}))
"""


class Blindning(unittest.TestCase):
    """Blindningens lokala mekanik (B-20261007-blindningen-listan-i-kundens-underlag-galler-ock, GR-20261009-natt-
    omgranskning-codex): den blinda sessionens läsningar prövas mot en tillåtelselista när de görs. En okänd fil som
    tillkommer efter starten blir inte läsbar, tillåtet underlag går att läsa, skaparens redovisning och andra
    kandidaters bedömningar nås inte, och ett fel i skyddet öppnar ingenting. Genom skisskritiken till processgränsen."""
    SLUG = 'blind-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'blindningens tillåtelselista'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder',
                                                REFERO_ENV=self.tmp / 'saknas' / 'refero.env', TJUGOFORSTA_ENV=self.tmp / 'saknas' / '21st.env'))
        self.stack.enter_context(patch.object(atelje, 'observerad', return_value=(None, None)))
        self.stack.enter_context(patch.object(kompetens, 'kvitto', side_effect=lambda _s, pass_, **_kw: giltigt_kvitto(pass_)))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.stack.enter_context(patch.object(tempfile, 'tempdir', str(self.tmp)))  # den blinda arbetskatalogen i provets katalog
        self.u = self.tmp / 'underlag' / self.SLUG
        self.u.mkdir(parents=True)
        (self.u / 'BRIEF.md').write_text('# Brief\n')
        (self.u / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Fiktiv Blind AB', 'fiktiv': True, 'kontaktvagar': []}))
        (self.u / 'bilder').mkdir(); (self.u / 'bilder' / 'foto.png').write_bytes(png())
        self.d1, self.d2 = kd.kdir(self.SLUG, 'k01'), kd.kdir(self.SLUG, 'k02')
        varv = self.d1 / 'varv' / 'start' / 'varv-01'
        varv.mkdir(parents=True)
        for b in ('390', '768', '1280', '1440'):
            for slag in ('forsta', 'hela'):
                (varv / ('vy-%s-%s.png' % (b, slag))).write_bytes(png())
        (self.d1 / 'RIKTNING.md').write_text('SKAPARENS REDOVISNING\n')
        self.d2.mkdir(parents=True); (self.d2 / 'SKISSKRITIK.json').write_text('{"rekommendation": "förkasta"}')
        (kd.metodkatalog(self.SLUG)).mkdir(parents=True); (kd.metodkatalog(self.SLUG) / 'METOD-skiss.md').write_text('metod\n')
        (kd.rot(self.SLUG) / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {'k01': {'uppgift': 'ringa'}, 'k02': {}}}))
        for k in ('k01', 'k02'):
            kd.ksajt(self.SLUG, k).mkdir(parents=True)
        falsk = self.tmp / 'claude'; falsk.write_text(FALSK_BLIND); falsk.chmod(0o700)
        self.stack.enter_context(patch.object(atelje, 'claude', return_value=str(falsk)))
        self.logg, self.plan = self.tmp / 'session.json', self.tmp / 'plan.json'
        self.stack.enter_context(patch.dict(os.environ, {'PROV_BLIND_LOGG': str(self.logg), 'PROV_BLIND_PLAN': str(self.plan),
                                                         'PROV_PROJEKT': str(atelje.ROOT), 'NWP_ARBETSROT': ''}))
        self.stack.enter_context(patch.multiple(kd, skisskritik_prompt=lambda *a, **k: 'KRITIKEN', bedomt=lambda *a, **k: {}))

    def kritik(self, fore, lasningar):
        self.plan.write_text(json.dumps({'fore': fore, 'lasningar': lasningar}))
        post = kd.skisskritik(self.SLUG, 'k01')
        self.assertIsNotNone(post, 'skisskritiken gav ingen post')
        return post, json.loads(self.logg.read_text())

    def test_en_fil_som_tillkommer_efter_starten_blir_inte_lasbar(self):
        g = self.d1 / 'granskare'
        sen, ny_bild, lank = self.u / 'SEN-ANTECKNING.md', g / 'vy-390-forsta.png', g / 'lank.md'
        karna = str(atelje.ROOT / kompetens.lasfiler('skisskritik')[0])
        fall = [('tillåtet underlag', {'tool_name': 'Read', 'tool_input': {'file_path': str(self.u / 'BRIEF.md')}}, True),
                ('en fil som tillkom i underlaget efter starten', {'tool_name': 'Read', 'tool_input': {'file_path': str(sen)}}, False),
                ('skaparens redovisning', {'tool_name': 'Read', 'tool_input': {'file_path': str(self.d1 / 'RIKTNING.md')}}, False),
                ('en annan kandidats bedömning', {'tool_name': 'Read', 'tool_input': {'file_path': str(self.d2 / 'SKISSKRITIK.json')}}, False),
                ('skaparens bilder', {'tool_name': 'Read', 'tool_input': {'file_path': str(self.d1 / 'varv' / 'start' / 'varv-01' / 'vy-390-forsta.png')}}, True),
                ('granskarens egen bild, tillkommen efter starten', {'tool_name': 'Read', 'tool_input': {'file_path': str(ny_bild)}}, True),
                ('en länk i granskarens katalog till redovisningen', {'tool_name': 'Read', 'tool_input': {'file_path': str(lank)}}, False),
                ('ateljéns plan', {'tool_name': 'Read', 'tool_input': {'file_path': str(kd.rot(self.SLUG) / 'KANDIDATPLAN.json')}}, False),
                ('den levererade metoden', {'tool_name': 'Read', 'tool_input': {'file_path': str(kd.metodkatalog(self.SLUG) / 'METOD-skiss.md')}}, True),
                ('rollens kärna', {'tool_name': 'Read', 'tool_input': {'file_path': karna}}, True),
                ('kundens bilder', {'tool_name': 'Read', 'tool_input': {'file_path': str(self.u / 'bilder' / 'foto.png')}}, True),
                ('Glob utan väg', {'tool_name': 'Glob', 'tool_input': {'pattern': '**/*'}}, False),
                ('Glob i varven', {'tool_name': 'Glob', 'tool_input': {'pattern': '**/*.png', 'path': str(self.d1 / 'varv')}}, True),
                ('Glob uppåt ur varven', {'tool_name': 'Glob', 'tool_input': {'pattern': '../*', 'path': str(self.d1 / 'varv')}}, False),
                ('Grep i underlaget', {'tool_name': 'Grep', 'tool_input': {'pattern': 'SEN', 'path': str(self.u)}}, False),
                ('Grep i kunskapen', {'tool_name': 'Grep', 'tool_input': {'pattern': 'x', 'path': str(atelje.ROOT / 'kunskap')}}, True)]
        post, s = self.kritik([{'skapa': str(sen)}, {'skapa': str(ny_bild)}, {'skapa': str(lank), 'lank': str(self.d1 / 'RIKTNING.md')}],
                              [f[1] for f in fall])
        for (namn, _las, vantat), b in zip(fall, s['beslut']):
            self.assertEqual(b['tillat'], vantat, '%s: %s' % (namn, b))
        self.assertFalse(set(s['tillatna']) & {'Read', 'Glob', 'Grep'}, 'läsverktygen står i --allowedTools: listan prövas aldrig')
        self.assertTrue({'Read', 'Glob', 'Grep'} <= set(s['verktyg']), 'läsverktygen finns i sessionen')
        lista = json.loads((atelje.ROOT / post['blind']).read_text() if not Path(post['blind']).is_absolute() else Path(post['blind']).read_text())
        self.assertNotIn(str(self.d1 / 'RIKTNING.md'), lista['filer'])

    def test_den_blinda_sessionen_startar_i_en_egen_tom_katalog(self):
        """Också när växeln står på kundrepo: aldrig i motorns rot eller kundrepot, aldrig --add-dir, reglerna absoluta."""
        kundrepo = self.tmp / 'kunder' / self.SLUG / 'kundrepo'
        kundrepo.mkdir(parents=True)
        with patch.dict(os.environ, {'NWP_ARBETSROT': 'kundrepo'}), patch.object(atelje, 'arbetsrot', return_value=(kundrepo, True)):
            _post, s = self.kritik([], [])
        cwd = Path(s['cwd'])
        self.assertTrue(cwd.name.startswith('nwp-blind-'), cwd)
        self.assertEqual(cwd.parent, self.tmp, 'arbetskatalogen skapas i tempkatalogen, registrerad')
        self.assertFalse(cwd.is_relative_to(atelje.ROOT.resolve()) or cwd.is_relative_to(kundrepo), cwd)
        self.assertEqual(sorted(p.name for p in cwd.iterdir()), ['.claude', korregister.AGARFIL])
        self.assertEqual([p.name for p in (cwd / '.claude').iterdir()], ['skills'])
        self.assertTrue((cwd / '.claude' / 'skills').is_symlink())
        self.assertEqual((cwd / '.claude' / 'skills').resolve(), (atelje.ROOT / '.claude' / 'skills').resolve())
        self.assertNotIn('--add-dir', s['argv'], 'motorns rot vore läsbar utan vakten')
        regler = s['argv'][s['argv'].index('--disallowedTools') + 1:]
        self.assertFalse([r for r in regler if r.startswith(('Read(./', 'Edit(./', 'Write(./'))], 'en relativ regel gäller den tomma katalogen, inte motorn')
        self.assertTrue(any(r.startswith('Read(//') and '/kandidater/k02' in r for r in regler), regler[:5])
        vakt = [h for k in json.loads(s['argv'][s['argv'].index('--settings') + 1])['hooks']['PreToolUse'] for h in k['hooks']
                if 'blindvakt.py' in h['command']]
        self.assertEqual(len(vakt), 1)
        self.assertIn(str(atelje.ROOT) + '/kontroller/blindvakt.py', vakt[0]['command'])
        self.assertNotIn('$CLAUDE_PROJECT_DIR', vakt[0]['command'])

    def vakt(self, lista, anrop, rot=None):
        k = __import__('blindvakt').krok(lista, rot=rot)
        return subprocess.run(['/bin/sh', '-c', k['hooks'][0]['command']], input=anrop if isinstance(anrop, str) else json.dumps(anrop),
                              capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(atelje.ROOT)))

    def test_fel_i_skyddet_oppnar_ingenting(self):
        lista = self.tmp / 'lista.json'
        lista.write_text(json.dumps({'filer': [str(self.u / 'BRIEF.md')], 'kataloger': []}))
        las = {'tool_name': 'Read', 'tool_input': {'file_path': str(self.u / 'BRIEF.md')}, 'cwd': str(atelje.ROOT)}
        self.assertEqual(self.vakt(lista, las).returncode, 0, 'tillåtet underlag')
        trasig = self.tmp / 'trasig.json'; trasig.write_text('{inte json')
        relativ = self.tmp / 'relativ.json'; relativ.write_text(json.dumps({'filer': ['BRIEF.md'], 'kataloger': []}))
        for namn, l_, a_, rot in (('listan saknas', self.tmp / 'saknas.json', las, None), ('listan är trasig', trasig, las, None),
                                  ('listan har en relativ väg', relativ, las, None), ('tom indata', lista, '', None),
                                  ('indata är ingen JSON', lista, '{x', None), ('ett annat verktyg', lista, dict(las, tool_name='Bash'), None),
                                  ('vakten startar inte', lista, las, self.tmp / 'ingen-rot')):
            r = self.vakt(l_, a_, rot)
            self.assertEqual(r.returncode, 2, namn)
            self.assertNotIn('"allow"', r.stdout, namn)

    def test_granskningens_forsta_pass_far_samma_skydd(self):
        fangat = {}

        def session(prompt, verktyg, ut, schema=None, *a, **k):
            fangat.update(k, verktyg=verktyg)
            raise RuntimeError('provet stannar efter starten')
        (self.d1 / 'bilder' / 'start').mkdir(parents=True)
        with patch.object(atelje, 'session', session), patch.multiple(kd, regel_rader=lambda: [], metod_rader=lambda *a: []), \
                patch.object(kompetens, 'prompt_rader', lambda *a, **k: []):
            with self.assertRaises(RuntimeError):
                kd.kritik(self.SLUG, 'k01')
        lista = json.loads(Path(fangat['blind']).read_text())
        self.assertIn(str(self.d1 / 'bilder'), lista['kataloger'])
        self.assertFalse(any('RIKTNING' in f for f in lista['filer']))


FALSK_SESSION = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ['PROV_R06_LOGG']).write_text(json.dumps({'cwd': os.getcwd(), 'argv': sys.argv[1:], 'stdin': sys.stdin.read()}))
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 3, 'duration_ms': 1000, 'result': 'ok',
                  'structured_output': {}, 'session_id': None}))
"""


class Arbetsrot(unittest.TestCase):
    """R06: kundrepot som arbetsrot i alla kundens arbetsvägar, bakom växeln NWP_ARBETSROT=kundrepo (av som standard):
    skapandeflödets sessioner (kandidatskiss och kandidatförfining, med slug), de äldre vägarna (utforskning, förfining och
    panelen, med arbetsslug) och helbygget genom kor.sh. Attrapper av claude tar emot sessionen: provet visar arbetskatalog,
    argument, krokar och prompt, inte vad en verklig session laddar eller tillämpar (kontroller/formagoprov.py)."""
    SLUG = 'r06-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kundrepot som arbetsrot'))).resolve()
        self.addCleanup(lambda: subprocess.run(['chflags', '-R', 'nouchg', str(self.tmp)], capture_output=True))
        self.logg = self.tmp / 'session.json'
        falsk = self.tmp / 'bin' / 'claude'; falsk.parent.mkdir(); falsk.write_text(FALSK_SESSION); falsk.chmod(0o700)
        self.falsk = falsk

    # --- skapandeflödet och de äldre vägarna, genom atelje.session ---

    def kund(self, rot_):
        u = rot_ / 'underlag' / self.SLUG
        u.mkdir(parents=True, exist_ok=True)
        (u / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Fiktiv Rot AB', 'fiktiv': True, 'kontaktvagar': []}))
        (u / 'BRIEF.md').write_text('# Brief\n\nPRIVAT BRIEFTEXT som aldrig ska i kundrepot.\n')
        (rot_ / 'kunder' / self.SLUG).mkdir(parents=True, exist_ok=True)

    def session(self, **kw):
        with patch.multiple(atelje, KUNDER=self.tmp / 'kunder', UNDERLAG=self.tmp / 'underlag', REFERO_ENV=self.tmp / 'x' / 'r.env',
                            TJUGOFORSTA_ENV=self.tmp / 'x' / '21.env'), \
                patch.object(atelje, 'observerad', return_value=(None, None)), patch.object(atelje, 'claude', return_value=str(self.falsk)), \
                patch.dict(os.environ, {'PROV_R06_LOGG': str(self.logg), 'NWP_ARBETSROT': 'kundrepo'}):
            atelje.session('Läs kunder/%s/sajt/ och underlag/%s/BRIEF.md.' % (self.SLUG, self.SLUG), ['Read', 'Write(./kunder/%s/sajt/**)' % self.SLUG],
                           self.tmp / 'svar.json', **kw)
        return json.loads(self.logg.read_text())

    def skapa_kundrepo(self):
        import kundrepo
        self.kund(self.tmp)
        with patch.multiple(atelje, KUNDER=self.tmp / 'kunder', UNDERLAG=self.tmp / 'underlag'):
            kundrepo.skapa(self.SLUG, fjarr=False)
        return self.tmp / 'kunder' / self.SLUG / 'kundrepo'

    def test_aldre_vagar_med_arbetsslug_startar_i_kundrepot_utan_mcp(self):
        kr = self.skapa_kundrepo()
        s = self.session(arbetsslug=self.SLUG)
        self.assertEqual(Path(s['cwd']).resolve(), kr.resolve())
        self.assertIn('--add-dir', s['argv'])
        self.assertNotIn('--mcp-config', s['argv'], 'den äldre vägen får inga MCP:er av arbetsroten')
        self.assertIn('Write(//%s/**)' % str(kr).strip('/'), s['argv'], 'sessionen skriver aldrig i kundrepot')
        self.assertIn('%s/kunder/%s/sajt/' % (atelje.ROOT, self.SLUG), s['stdin'])

    def test_skapandeflodets_session_skriver_aldrig_i_kundrepot(self):
        kr = self.skapa_kundrepo()
        s = self.session(slug=self.SLUG)
        self.assertEqual(Path(s['cwd']).resolve(), kr.resolve())
        self.assertTrue({'Write(//%s/**)' % str(kr).strip('/'), 'Edit(//%s/**)' % str(kr).strip('/')} <= set(s['argv']))

    def test_ett_kundrepo_med_egna_installningar_anvands_inte(self):
        kr = self.skapa_kundrepo()
        (kr / '.claude').mkdir(); (kr / '.claude' / 'settings.json').write_text('{"permissions": {"allow": ["Bash"]}}')
        with self.assertRaises(RuntimeError):
            self.session(slug=self.SLUG)
        self.assertFalse(self.logg.exists(), 'ingen session startade')

    def test_varje_sessionsstart_bar_slug_eller_arbetsslug(self):
        """En flagga som bara påverkar vissa vägar är inte hela införandet: varje anrop till atelje.session i flödets moduler
        anger kunden (slug eller arbetsslug), annars väljer arbetsroten alltid motorns rot."""
        import ast
        saknas = []
        for mod in ('kandidater.py', 'atelje.py', 'forberedelse.py'):
            trad = ast.parse((atelje.ROOT / 'kontroller' / mod).read_text(encoding='utf-8'))
            for n in ast.walk(trad):
                if isinstance(n, ast.Call) and ((isinstance(n.func, ast.Name) and n.func.id == 'session')
                                                or (isinstance(n.func, ast.Attribute) and n.func.attr == 'session'
                                                    and isinstance(n.func.value, ast.Name) and n.func.value.id == 'atelje')):
                    if not {k.arg for k in n.keywords} & {'slug', 'arbetsslug'}:
                        saknas.append('%s:%d' % (mod, n.lineno))
        self.assertEqual(saknas, [], 'sessioner utan kund: arbetsroten blir alltid motorns')

    # --- helbygget genom kor.sh ---

    def kor_repo(self):
        kr = self.tmp / 'kor-repo'
        kr.mkdir()
        for namn in ('kor.sh', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', '.gitignore', 'dashboard.sh'):
            if (atelje.ROOT / namn).is_file():
                import shutil
                shutil.copy2(atelje.ROOT / namn, kr / namn)
        import shutil
        for mapp in ('kontroller', 'kritik', 'kunskap', 'dashboard', 'mall/leverans'):
            shutil.copytree(atelje.ROOT / mapp, kr / mapp, ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'rokprov'), symlinks=True)
        shutil.copytree(atelje.ROOT / '.claude' / 'hooks', kr / '.claude' / 'hooks', ignore=shutil.ignore_patterns('__pycache__'))
        for f in (atelje.ROOT / '.claude').glob('settings*.json'):
            shutil.copy2(f, kr / '.claude' / f.name)
        (kr / 'backlog').mkdir()
        os.symlink(atelje.ROOT / '.venv', kr / '.venv')
        os.symlink(atelje.ROOT / 'kontroller' / 'node_modules', kr / 'kontroller' / 'node_modules')
        g = lambda *a: subprocess.run(['git', '-C', str(kr), '-c', 'user.name=prov', '-c', 'user.email=prov@example.invalid', *a], capture_output=True)  # noqa: E731
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-q', '-m', 'bas')
        self.kund(kr)
        return kr

    def kor(self, kr, **extra):
        m = {k: v for k, v in os.environ.items() if not k.startswith(('CLAUDE_CODE_', 'NWP_', 'PROV_')) and k != 'CLAUDECODE'}
        m.update(PATH=str(self.falsk.parent) + os.pathsep + m.get('PATH', ''), NWP_STARTKONTROLL='av', NWP_SANDLADA='av', NWP_ATELJE='av',
                 NWP_KORREGISTER=str(self.tmp / 'korregister'), NWP_FRIST='2', PROV_R06_LOGG=str(self.logg))
        m.update(extra)
        if self.logg.exists():
            self.logg.unlink()
        p = subprocess.run(['bash', str(kr / 'kor.sh'), self.SLUG, 'Fiktiv Rot AB, Umeå'], capture_output=True, text=True, cwd=str(kr), env=m, timeout=600)
        return p.returncode, p.stdout + p.stderr

    def test_helbygget_startar_i_kundrepot_med_krokarna_och_utan_att_skriva_dit(self):
        kr = self.kor_repo()
        r = subprocess.run([str(kr / '.venv' / 'bin' / 'python'), '-B', str(kr / 'kontroller' / 'kundrepo.py'), self.SLUG, '--utan-fjarr'],
                           cwd=str(kr), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        repo = kr / 'kunder' / self.SLUG / 'kundrepo'
        fore = subprocess.run(['git', 'ls-files'], cwd=str(repo), capture_output=True, text=True).stdout.split()
        self.assertEqual(sorted(fore), ['.gitignore', 'CLAUDE.md'])
        rc, ut = self.kor(kr, NWP_ARBETSROT='kundrepo')
        self.assertTrue(self.logg.exists(), 'bygget startade inte: %s' % ut[-600:])
        s = json.loads(self.logg.read_text())
        a, k = s['argv'], str(kr).strip('/')
        self.assertEqual(Path(s['cwd']).resolve(), repo.resolve(), 'byggsessionen startade inte i kundrepot')
        self.assertEqual(a[a.index('--add-dir') + 1], str(kr))
        self.assertFalse([x for x in a if __import__('re').match(r'^\w+\(\./', x)], 'en relativ regel finns kvar')
        self.assertIn('Edit(//%s/kontroller/**)' % k, a, 'motorns mekanik är fortfarande skrivskyddad')
        self.assertIn('Write(//%s/kunder/%s/kundrepo/**)' % (k, self.SLUG), a, 'bygget skriver aldrig i kundrepot')
        self.assertIn('Bash(%s/.venv/bin/python %s/kontroller/prova.py *)' % (kr, kr), a)
        inst = json.loads(a[a.index('--settings') + 1])
        stopp = inst['hooks']['Stop'][0]['hooks'][0]['command']
        self.assertIn('%s/.claude/hooks/stoppvakt.py' % kr, stopp, 'stoppvakten följer inte med till kundrepot')
        self.assertNotIn('$CLAUDE_PROJECT_DIR', json.dumps(inst['hooks']))
        self.assertTrue(any('commitvakt.py' in h['command'] for p_ in inst['hooks']['PreToolUse'] for h in p_['hooks']))
        self.assertIn('%s/kunder/%s/sajt/' % (kr, self.SLUG), s['stdin'])
        self.assertIn('Arbetskatalogen är kundens eget repo', s['stdin'])
        # inget privat underlag eller hemlighet i kundrepot, och en fortsättning eller ett nytt försök får samma rot
        self.assertNotIn('PRIVAT BRIEFTEXT', ''.join(p.read_text(errors='replace') for p in repo.rglob('*') if p.is_file() and '.git' not in p.parts))
        rc2, ut2 = self.kor(kr, NWP_ARBETSROT='kundrepo')
        self.assertEqual(Path(json.loads(self.logg.read_text())['cwd']).resolve(), repo.resolve(), ut2[-400:])
        self.assertEqual(sorted(subprocess.run(['git', 'ls-files'], cwd=str(repo), capture_output=True, text=True).stdout.split()), ['.gitignore', 'CLAUDE.md'])
        self.assertEqual(subprocess.run(['git', 'status', '--porcelain'], cwd=str(repo), capture_output=True, text=True).stdout, '')
        # utan växeln: motorns rot och relativa regler, som förut
        rc3, ut3 = self.kor(kr)
        s3 = json.loads(self.logg.read_text())
        self.assertEqual(Path(s3['cwd']).resolve(), kr.resolve())
        self.assertNotIn('--add-dir', s3['argv']); self.assertIn('Edit(./kontroller/**)', s3['argv'])
        # ett kundrepo med egna inställningar: bygget startar inte
        (repo / '.claude').mkdir(); (repo / '.claude' / 'settings.json').write_text('{}')
        rc4, ut4 = self.kor(kr, NWP_ARBETSROT='kundrepo')
        self.assertEqual(rc4, 2, ut4[-400:]); self.assertFalse(self.logg.exists(), 'claude startade ändå')
        self.assertIn('egna Claude Code-inställningar', ut4)


FALSK_FORMAGA = r"""#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
with open(os.environ['PROV_FORMAGA_LOGG'], 'a') as f:
    f.write(json.dumps({'cwd': os.getcwd(), 'argv': a}) + '\n')
p = sys.stdin.read()
with open(os.environ['PROV_FORMAGA_LOGG'] + '.prompt', 'a') as f:
    f.write(json.dumps(p) + '\n')
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'structured_output': {}, 'session_id': None}))
"""


class Formagoprov(unittest.TestCase):
    """Det förberedda verkliga förmågeprovet (kontroller/formagoprov.py) mekaniskt, utan modell: planen ändrar inget, utan
    klartecken körs inget, bedömningen ger godkänt bara när varje kriterium är observerat, och en attrapp av claude ger
    aldrig godkänt."""

    def setUp(self):
        import formagoprov
        self.fp = formagoprov
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'förmågeprovets mekanik'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder',
                                                REFERO_ENV=self.tmp / 'x' / 'r.env', TJUGOFORSTA_ENV=self.tmp / 'x' / '21.env'))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.stack.enter_context(patch.object(tempfile, 'tempdir', str(self.tmp)))  # de blinda arbetskatalogerna i provets katalog
        (self.tmp / 'underlag').mkdir(); (self.tmp / 'kunder').mkdir()

    def test_planen_och_utan_klartecken_andrar_ingenting(self):
        import io
        with contextlib.redirect_stdout(io.StringIO()) as ut:
            self.assertEqual(self.fp.main(['plan']), 0)
        self.assertIn('kor --ja', ut.getvalue())
        for n in self.fp.KRITERIER:
            self.assertIn(n, ut.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.fp.main(['kor']), 2)
        self.assertEqual(list((self.tmp / 'underlag').iterdir()) + list((self.tmp / 'kunder').iterdir()), [], 'något skapades utan klartecken')

    def katalog(self, **andra):
        """En sparad körning där varje kriterium är uppfyllt; andra ändrar delar av den."""
        k = self.tmp / 'resultat'
        k.mkdir(exist_ok=True)
        kr = '/fiktiv/kunder/formagoprov-x/kundrepo'
        m = {'slug': 'formagoprov-x', 'modell': 'm', 'kundrepo': kr, 'motor': '/fiktiv/motor', 'brief': '/fiktiv/underlag/x/BRIEF.md', 'k02_sida': '/fiktiv/k02/index.astro',
             'riktning': '/fiktiv/k01/RIKTNING.md', 'sen_vag': '/fiktiv/underlag/x/SEN-ANTECKNING.md', 'kundrepo_forsta_rad': '# kund-x — webbplatsen för X',
             'motorns_forsta_rad': '# nortropic-webb-pro — för sessioner i det här repot', 'kundrepo_fore': {'sparade': 'a', 'provfil': False},
             'egen_fil': '/fiktiv/k01/sajt/src/FORMAGOPROV.txt', 'egen_fil_finns': True,
             'kundrepo_efter': {'sparade': 'a', 'provfil': False}, 'S2_start': 100.0, 'sen_fil': {'skapad': 200.0}}
        K = self.fp.KONTROLL
        s1 = [('Skill', {'skill': 'impeccable'}, 'ok', False), ('Read', {'file_path': m['brief']}, 'Kontrollord: ' + K['brief'], False),
              ('Read', {'file_path': m['k02_sida']}, 'nekad', True), ('Write', {'file_path': kr + '/PROVFIL.md'}, 'nekad', True),
              ('Write', {'file_path': m['egen_fil']}, 'ok', False)]
        s2 = [('Skill', {'skill': 'impeccable'}, 'ok', False),
              ('Read', {'file_path': m['brief']}, 'Kontrollord: ' + K['brief'], False), ('Bash', {'command': 'sen-fil'}, 'skapad', False),
              ('Read', {'file_path': m['sen_vag']}, 'blindvakten nekade', True), ('Glob', {'pattern': '*.md', 'path': '/fiktiv/underlag/x'}, 'nekad', True),
              ('Grep', {'pattern': 'SENFIL', 'path': '/fiktiv/underlag/x'}, 'nekad', True), ('Read', {'file_path': m['riktning']}, 'nekad', True)]
        s3 = [('Read', {'file_path': m['brief']}, 'nekad', True), ('Read', {'file_path': m['riktning']}, 'nekad', True)]
        svar = {'S1': {'claude_md_forsta_rader': [m['kundrepo_forsta_rad']], 'brief_kontrollord': K['brief']},
                'S2': {'brief_kontrollord': K['brief']}, 'S3': {}}
        steg = {'S1': s1, 'S2': s2, 'S3': s3}
        m.update(andra.get('manifest') or {})
        for s_, f in (andra.get('steg') or {}).items():
            steg[s_] = f(steg[s_])
        for s_, f in (andra.get('svar') or {}).items():
            svar[s_] = f(svar[s_])
        (k / 'MANIFEST.json').write_text(json.dumps(m))
        for s_ in ('S1', 'S2', 'S3'):
            (k / ('%s-svar.json' % s_)).write_text(json.dumps({'structured_output': svar[s_]}))
            if s_ in andra.get('utan_transkript', ()):
                (k / ('%s-transkript.jsonl' % s_)).unlink(missing_ok=True)
                continue
            rader = []
            cwd = (andra.get('cwd') or {}).get(s_) or (kr if s_ == 'S1' else '/fiktiv/tmp/nwp-blind-%s' % s_.lower())
            for i, (namn, inn, text, fel) in enumerate(steg[s_]):
                rader.append(json.dumps({'cwd': cwd, 'message': {'content': [{'type': 'tool_use', 'id': 'u%d' % i, 'name': namn, 'input': inn}]}}))
                rader.append(json.dumps({'cwd': cwd, 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'u%d' % i, 'content': text, 'is_error': fel}]}}))
            (k / ('%s-transkript.jsonl' % s_)).write_text('\n'.join(rader) + '\n')
        return k

    def utfall(self, res):
        return {n: v['utfall'] for n, v in res['kriterier'].items()}

    def test_bedomningen_godkanner_bara_det_observerade(self):
        res = self.fp.bedom(self.katalog())
        self.assertTrue(res['godkant'], self.utfall(res))
        motor = lambda s_: dict(s_, claude_md_forsta_rader=s_['claude_md_forsta_rader'] + ['# nortropic-webb-pro — för sessioner i det här repot'])  # noqa: E731
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(svar={'S1': motor})))['S1.motorns_claude_md'], 'underkänt')
        las_md = lambda st: st + [('Read', {'file_path': '/fiktiv/kunder/formagoprov-x/kundrepo/CLAUDE.md'}, 'innehåll', False)]  # noqa: E731
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(steg={'S1': las_md})))['S1.kundens_claude_md'], 'underkänt', 'citatet efter en Read bevisar ingen kontext')
        lacka = lambda st: [x if x[1].get('file_path') != '/fiktiv/underlag/x/SEN-ANTECKNING.md' else (x[0], x[1], 'Kontrollord: SENFIL-KONTROLL-9931', False) for x in st]  # noqa: E731
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(steg={'S2': lacka})))['S2.sen_fil_nekad'], 'underkänt')
        oppen = lambda st: [(x[0], x[1], 'Kontrollord: BRIEF-KONTROLL-7720', False) if x[1].get('file_path', '').endswith('BRIEF.md') else x for x in st]  # noqa: E731
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(steg={'S3': oppen})))['S3.krokdod'], 'underkänt', 'en läsning lyckades när kroken dog')
        for s_, cwd in (('S2', '/fiktiv/motor'), ('S3', '/fiktiv/motor/underlag'), ('S2', '/fiktiv/kunder/formagoprov-x/kundrepo'), ('S3', '/fiktiv/tmp/annan')):
            self.assertEqual(self.utfall(self.fp.bedom(self.katalog(cwd={s_: cwd})))['%s.arbetsyta' % s_], 'underkänt', (s_, cwd))
        skill_fel = lambda st: [(x[0], x[1], 'okänd skill', True) if x[0] == 'Skill' else x for x in st]  # noqa: E731
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(steg={'S2': skill_fel})))['S2.skill'], 'underkänt')
        res = self.fp.bedom(self.katalog(utan_transkript=('S3',)))
        self.assertFalse(res['godkant']); self.assertEqual(self.utfall(res)['S3.krokdod'], 'ej observerat')
        self.assertEqual(self.utfall(res)['S3.arbetsyta'], 'ej observerat')
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(manifest={'kundrepo_efter': {'sparade': 'b', 'provfil': False}})))['S1.kundrepo_skrivs_inte'], 'underkänt')
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(manifest={'egen_fil_finns': False})))['S1.egen_skrivning'], 'underkänt', 'filen finns inte efteråt')
        nekad = lambda st: [(x[0], x[1], 'nekad', True) if x[1].get('file_path', '').endswith('FORMAGOPROV.txt') else x for x in st]  # noqa: E731
        self.assertEqual(self.utfall(self.fp.bedom(self.katalog(steg={'S1': nekad})))['S1.egen_skrivning'], 'underkänt', 'skaparen kunde inte skriva')

    def test_en_attrapp_av_claude_ger_aldrig_godkant(self):
        falsk = self.tmp / 'claude'; falsk.write_text(FALSK_FORMAGA); falsk.chmod(0o700)
        logg = self.tmp / 'anrop.jsonl'
        with patch.object(atelje, 'claude', return_value=str(falsk)), patch.object(atelje, 'observerad', return_value=(None, None)), \
                patch.dict(os.environ, {'PROV_FORMAGA_LOGG': str(logg)}):
            res = self.fp.kor('attrapp', 'low', ut_rot=self.tmp / 'ut')
        self.assertFalse(res['godkant'], 'en attrapp visar inte vad Claude laddar')
        self.assertTrue(all(v['utfall'] == 'ej observerat' for n, v in res['kriterier'].items() if n != 'S1.kundrepo_skrivs_inte'), self.utfall(res))
        anrop = [json.loads(r) for r in logg.read_text().splitlines()]
        self.assertEqual(len(anrop), 3)
        slug = json.loads((Path(res['katalog']) / 'MANIFEST.json').read_text())['slug']
        self.assertEqual(Path(anrop[0]['cwd']).resolve(), (self.tmp / 'kunder' / slug / 'kundrepo').resolve(), 'S1 startar i kundrepot')
        for a in anrop[1:]:
            inst = json.loads(a['argv'][a['argv'].index('--settings') + 1])
            self.assertEqual([p_['matcher'] for p_ in inst['hooks']['PreToolUse']], ['Read|Glob|Grep'])
            self.assertNotIn('--mcp-config', a['argv'], 'förmågeprovet ansluter inga MCP-tjänster')
        self.assertIn('blindvakt.py', json.dumps(json.loads(anrop[1]['argv'][anrop[1]['argv'].index('--settings') + 1])))
        prompter = [json.loads(r) for r in Path(str(logg) + '.prompt').read_text().splitlines()]
        for a, p_ in zip(anrop[1:], prompter[1:]):  # S2 och S3: den blinda arbetskatalogen, absoluta regler och kommandon
            cwd = Path(a['cwd'])
            self.assertTrue(cwd.name.startswith('nwp-blind-') and cwd.parent == self.tmp, cwd)
            self.assertNotIn('--add-dir', a['argv'])
            self.assertIn('Bash(%s/.venv/bin/python %s/kontroller/formagoprov.py sen-fil)' % (atelje.ROOT, atelje.ROOT), a['argv']) if a is anrop[1] else None
            self.assertIn(str(atelje.ROOT) + '/kontroller/formagoprov.py', p_)
            self.assertNotIn('`.venv/bin/python', p_)
        self.assertNotEqual(anrop[1]['cwd'], anrop[2]['cwd'], 'varje blind session får en egen katalog')
        self.assertEqual(json.loads(anrop[2]['argv'][anrop[2]['argv'].index('--settings') + 1])['hooks']['PreToolUse'][0]['hooks'][0]['command'], 'sleep 30')
        self.assertNotIn('--mcp-config', anrop[0]['argv'])

    def test_sen_fil_skriver_bara_pa_provets_kund(self):
        import io
        with patch.dict(os.environ, {self.fp.SEN_VAXEL: str(self.tmp / 'underlag' / 'en-riktig-kund' / 'SEN-ANTECKNING.md')}), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.fp.main(['sen-fil']), 2)
        self.assertFalse((self.tmp / 'underlag' / 'en-riktig-kund').exists())


if __name__ == '__main__':
    unittest.main()
