#!/usr/bin/env python3
"""Glappen mellan metod, utförande och kvalitetskontroll (GR-20261009-metod-till-resultat-codex; ägarens uppdrag
2026-10-09 om metod → utförande → kvalitet och om ett källförankrat arbetssätt). Varje fall går genom den verkliga lokala
ingången med attrapper bara vid modellsessionerna, fotograferingen och nätet:

- F01: planprövningen stämplar bara de uppdrag som svaret giltigt bedömt; tom lista, partiellt svar, dubbla och okända
  id:n, en ogiltig bedömning och ett saknat svar lämnar uppdraget oprövat och stoppat före skaparen med skälet, och en
  omprövning bevarar de oförändrade uppdragens bedömningar.
- F02: helgranskningens metodidentitet omfattar designreglerna och kundens domlogg (beroendelistan i granska.py); en
  ändring gör en tidigare dom inaktuell för cachen, omgången och slutposten (samma aktuell_metod), en oförändrad metod
  kan återanvändas, och granskarens uppdrag får designreglerna och kundens aktuella domar uttryckligen.
- F03: ett avslutat specialistförsök är inte ett uppfyllt pass. Brister kärnkravet också i sista försöket återställs
  dess ändringar, misslyckandet (och en återställning som faller) syns i kandidatens besked, återupptagningen gör inte
  om passet av sig självt och räknar det aldrig som uppfyllt, och ett uttryckligt nytt försök går inom budgeten.
- T01: uppgiften väljer skärm eller flöde; ett flödes ordnade steg med bildvägar och förklaring och ursprungsrapporten
  når skaparens uppdrag, ett flöde utan omslagsbild redovisas inte som tomt, och en saknad stegbild står med skälet.
- T02: jämförelsen mot den godkända prototypen är ett eget besked, skilt från designnivån: saknat underlag, fel
  version, uttryckligt ej bedömt, observationsfel, oläst underlag och en komplett jämförelse hålls isär; prototypens
  och byggets bilder är läskrav i observationen; domen och slutposten visar beskedet bredvid godkännandet.
- Blindvakten (ett verkligt prov av en parallell session: dontAsk nekar inte Read i arbetskatalogen, och en krok vars
  tidsgräns slår till blockerar inte): krokens tidsgräns i den blinda sessionens inställningar ligger klart över vaktens
  egen frist, så att en långsam vakt själv hinner stoppa läsningen.
- H01 som avgränsad variant: med NWP_METODVARIANT=h01 skriver skaparen ett preliminärt visuellt mål före kod, knutet
  till referensbilderna, och prövar det efter renderingen; grundvarianten är oförändrad; en okänd variant stoppar.
- Kompetensens användning i sex nivåer i specialistpassets post, okänt som okänt.
- Kvalitetsprovets mekanik: ab.py forbered-skiss --variabel metodvariant lottar grund och h01 på två armar med samma
  uppdrag, effort och metod i övrigt, och varje arms skiss får sin variant.
"""
import contextlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import blindvakt  # noqa: E402
import granska  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import korregister  # noqa: E402
import skapande  # noqa: E402
import stadning  # noqa: E402
import ab  # noqa: E402
import ab_skiss  # noqa: E402
import prov_ab_skiss  # noqa: E402  fixturen för metodförsöket
import prov_omgranskning  # noqa: E402  fixturen för planversionen (N01)
import referenstjanster  # noqa: E402

GILTIG = 'uppdraget bär kundens material och referensens kvalitet'


class Planprovningstackning(unittest.TestCase):
    """F01: täckningen före stämpeln, genom kandidatflödets kor med en falsk planprövning och en falsk skapare."""
    SLUG = 'f01-prov'

    def setUp(self):
        prov_omgranskning.Planversion.setUp(self)  # syntetisk plan med k01 och k02, attrapper vid skaparen och sessionerna
        self.svar_pp = []

        def session(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None):
            if schema is not kd.PLANPROVNING_SCHEMA:
                raise AssertionError('oväntad session: %s' % prompt[:80])
            self.provningar.append(prompt)
            self.handelser.append('planprovning')
            svar = self.svar_pp.pop(0)
            svar['session_id'] = prov_omgranskning.transkript(prov_omgranskning.kompetenssteg('planprovning'))
            Path(ut).write_text(json.dumps(svar))
            return svar
        self.stack.enter_context(patch.object(atelje, 'session', session))

    def kor(self, *svar):
        self.svar_pp[:] = [{'structured_output': s, 'session_id': None} if s is not None else {'session_id': None} for s in svar]
        status = {'startad': '2026-10-09T08:00:00Z', 'lage': 'ny'}
        kd.kor(self.SLUG, status, lambda: None, n=2)
        return json.loads((self.r / 'PLANPROVNING.json').read_text())

    def plan(self):
        return json.loads((self.r / 'KANDIDATPLAN.json').read_text())

    def skapade(self):
        return sorted({h.split(':')[1] for h in self.handelser if h.startswith('skapare:')})

    def obedomt(self, kid, pp, skal):
        st = kd.las_status(self.SLUG, kid)
        self.assertNotIn(kid, pp['provade'], 'ett obedömt uppdrag stämplades som prövat')
        self.assertNotIn(kid, self.skapade(), 'skaparen fick ett oprövat uppdrag')
        self.assertIn(kid, pp['tackning']['obedomda'])
        self.assertIn(skal, pp['tackning']['obedomda'][kid])
        self.assertEqual(st.get('status'), 'fel', st)
        self.assertIn(skal, st.get('skal', ''), 'stoppet säger inte varför')
        self.assertNotIn(kid, self.skapade(), 'skaparen fick ett oprövat uppdrag')

    def test_tom_lista_lamnar_alla_oprovade(self):
        pp = self.kor({'sammanfattning': 'inget', 'kandidater': []})
        self.assertEqual(pp['provade'], {})
        for kid in ('k01', 'k02'):
            self.obedomt(kid, pp, 'saknar en bedömning')
        self.assertIn('Täckning: 0 av 2', (self.r / 'PLANPROVNING.md').read_text())

    def test_partiellt_svar_staplar_bara_det_bedomda(self):
        pp = self.kor({'sammanfattning': 's', 'kandidater': [{'id': 'k01', 'bedomning': GILTIG, 'andringar': []}]})
        self.assertEqual(sorted(pp['provade']), ['k01'])
        self.obedomt('k02', pp, 'saknar en bedömning')
        self.assertEqual(self.skapade(), ['k01'])

    def test_dubbla_och_okanda_id_ar_ingen_tackning(self):
        pp = self.kor({'sammanfattning': 's', 'kandidater': [
            {'id': 'k01', 'bedomning': GILTIG, 'andringar': [{'falt': 'typografi', 'nytt': 'DUBBEL A', 'skill': 'impeccable', 'varfor': 'x'}]},
            {'id': 'k01', 'bedomning': GILTIG, 'andringar': [{'falt': 'typografi', 'nytt': 'DUBBEL B', 'skill': 'impeccable', 'varfor': 'x'}]},
            {'id': 'k09', 'bedomning': GILTIG, 'andringar': []}]})
        self.obedomt('k01', pp, '2 gånger')
        self.obedomt('k02', pp, 'saknar en bedömning')
        self.assertEqual(pp['tackning']['okanda'], ['k09'])
        self.assertNotIn('DUBBEL', json.dumps(self.plan()), 'en dubblerad posts ändring gjordes')

    def test_ogiltig_bedomning_staplar_inte_och_andrar_inte(self):
        pp = self.kor({'sammanfattning': 's', 'kandidater': [
            {'id': 'k01', 'bedomning': GILTIG, 'andringar': []},
            {'id': 'k02', 'bedomning': ' – ', 'andringar': [{'falt': 'typografi', 'nytt': 'OGILTIG ÄNDRING', 'skill': 'impeccable', 'varfor': 'x'}]}]})
        self.obedomt('k02', pp, 'tom eller oanvändbar')
        self.assertNotIn('OGILTIG ÄNDRING', json.dumps(self.plan()))
        self.assertEqual(sorted(pp['provade']), ['k01'])

    def test_inget_giltigt_svar_ar_ingen_passage(self):
        pp = self.kor(None)
        self.assertEqual(pp['provade'], {})
        for kid in ('k01', 'k02'):
            self.obedomt(kid, pp, 'inget giltigt svar')
        self.assertEqual(self.skapade(), [])

    def test_fullstandigt_giltigt_svar_slapper_bada(self):
        pp = self.kor({'sammanfattning': 's', 'kandidater': [{'id': k, 'bedomning': GILTIG, 'andringar': []} for k in ('k01', 'k02')]})
        self.assertEqual(sorted(pp['provade']), ['k01', 'k02'])
        self.assertEqual(pp.get('tackning', {}).get('obedomda'), {})
        self.assertEqual(self.skapade(), ['k01', 'k02'])
        self.assertIn('exakt en post per uppdrag som prövas (k01, k02)', self.provningar[0])

    def test_omprovningen_bevarar_de_oforandrades_bedomning(self):
        self.kor({'sammanfattning': 's', 'kandidater': [{'id': 'k01', 'bedomning': GILTIG, 'andringar': []}]})
        pp = self.kor({'sammanfattning': 's2', 'kandidater': [{'id': 'k02', 'bedomning': 'nu bedömt: ' + GILTIG, 'andringar': []}]})
        self.assertEqual(sorted(pp['provade']), ['k01', 'k02'], 'omprövningen av k02 tappade k01:s stämpel eller stämplade inte k02')
        self.assertEqual(pp.get('omprovning', {}).get('kandidater'), ['k02'], 'k02 prövades inte om')
        self.assertEqual(pp.get('tidigare_bedomningar'), {'k01': GILTIG})
        self.assertEqual(kd.las_status(self.SLUG, 'k02').get('status'), 'klar', 'k02 gick inte vidare efter sin prövning')



class Metodidentitet(unittest.TestCase):
    """F02: designreglerna och kundens domlogg i metodens identitet, och granskaren får dem uttryckligen."""
    SLUG = 'f02-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'F02 metodidentiteten'))).resolve()
        for f in [granska.INSTRUKTION, 'kunskap/designregler.md'] + [f for _n, f in granska.MATTSTOCKAR]:
            (self.tmp / f).parent.mkdir(parents=True, exist_ok=True)
            (self.tmp / f).write_text('# %s\n' % f)
        (self.tmp / 'kunskap' / 'designregler.md').write_text('# Designregler\n- klickytor minst 24 px\n')
        self.u = self.tmp / 'underlag'
        (self.u / self.SLUG / 'atelje').mkdir(parents=True)
        (self.u / self.SLUG / 'BRIEF.md').write_text('# Brief\n')
        (self.tmp / 'kunder').mkdir()
        self.stack.enter_context(patch.multiple(granska, ROOT=self.tmp, UNDERLAG=self.u, KUNDER=self.tmp / 'kunder'))
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.u, KUNDER=self.tmp / 'kunder'))

    def test_andrad_designregel_gor_aldre_dom_inaktuell(self):
        upp = granska.aktuell_metod(self.SLUG)
        self.assertTrue(granska.samma_metod(dict(upp), granska.aktuell_metod(self.SLUG)), 'en oförändrad metod gick inte att återanvända')
        (self.tmp / 'kunskap' / 'designregler.md').write_text('# Designregler\n- klickytor minst 44 px\n')
        self.assertFalse(granska.samma_metod(dict(upp), granska.aktuell_metod(self.SLUG)),
                         'en ändrad designregel lämnade den äldre domen aktuell')

    def test_ny_dom_i_domloggen_ger_ny_identitet(self):
        h0 = granska.metod_sha(self.SLUG)
        skapande.lagg_till_dom(self.SLUG, 'ägaren', 'putsa', 'BEHÅLL DEN LUGNA RYTMEN', underlag=self.u)
        self.assertNotEqual(granska.metod_sha(self.SLUG), h0, 'kundens nya dom ändrade inte metodens identitet')
        self.assertEqual(granska.metod_sha(self.SLUG), granska.metod_sha(self.SLUG))

    def test_beroendelistan_ar_uttrycklig(self):
        vagar = [f for _n, f in granska.METODBEROENDEN]
        self.assertIn('kunskap/designregler.md', vagar)
        self.assertIn('kritik/GRANSKARE.md', vagar)
        self.assertIn('DESIGNDOMAR.jsonl', [f for _n, f in granska.KUNDBEROENDEN])
        self.assertTrue(all(n for n, _f in granska.METODBEROENDEN + granska.KUNDBEROENDEN), 'ett beroende saknar skäl')

    def test_granskaren_far_reglerna_och_de_aktuella_domarna(self):
        skapande.lagg_till_dom(self.SLUG, 'ägaren', 'putsa', 'BEHÅLL DEN LUGNA RYTMEN', underlag=self.u)
        rdir = self.tmp / 'omgang'
        rdir.mkdir()
        text = granska.uppdrag_text(self.SLUG, 'http://x', ['/'], self.tmp / 'ak', [], [], [], None, rdir)
        self.assertIn('kunskap/designregler.md', text)
        self.assertIn('BEHÅLL DEN LUGNA RYTMEN', text, 'kundens aktuella dom når inte granskaren')
        self.assertLess(text.index('BEHÅLL DEN LUGNA RYTMEN'), text.index('Sajtens skärmbilder'), 'domarna kommer efter bilderna')



class Specialistpass(unittest.TestCase):
    """F03: båda försöken, slutversionen, återställningsfel och återupptagningen tillsammans, genom efter_fordjupning."""
    SLUG = 'f03-prov'
    DOM = {'tid': 'a', 'text': 'x', 'uppdrag': {'typ': 'bygg_ut', 'resultat': 'hela startsidan', 'omfattning': ['/x/'], 'bevara': ['första vyn'], 'specialister': {'rorelse': 'andra', 'granskning': 'andra'}}}  # passen körs bara på uppdragets begäran (2026-10-09)
    ROR = 'fordjupa:a:rorelse'

    def setUp(self):
        prov_omgranskning.Lasordning.setUp(self)  # kandidaten k01 förfinad i v1; attrapper vid sessionen, fotograferingen och återställningen

    def rec(self, nyckel=ROR):
        return kd.las_status(self.SLUG, 'k01')['kompetens'][nyckel]

    def fordjupa(self):
        n = len(self.prompter)
        kd.efter_fordjupning(self.SLUG, 'k01', self.DOM)
        return len(self.prompter) - n

    def test_sista_forsokets_andringar_aterstalls_och_passet_ar_inte_uppfyllt(self):
        self.ordning[:] = ['sen', 'sen', 'fore', 'fore']
        self.fordjupa()
        r = self.rec()
        self.assertIs(r['genomford'], False)
        self.assertEqual(self.ater[:2], ['v1', 'v1'], 'sista försökets ändringar återställdes inte')
        self.assertEqual(r['version_efter'], 'v1', 'arbetet utan kärnan blev kvar som slutversion')
        self.assertIs(r.get('uppfyllt'), False, 'ett avslutat men underkänt pass räknas som uppfyllt')
        self.assertIn('kärnkravet uppfylldes inte i sista försöket', r['aterstalld'])
        st = kd.las_status(self.SLUG, 'k01')
        self.assertEqual(st['kompetens_ej_uppfyllda'], [self.ROR])
        self.assertIn('kompetenspass ej uppfyllda: rorelse', st['skal'], 'misslyckandet syns inte i beskedet')
        self.assertIs(self.rec('fordjupa:a:granskning')['uppfyllt'], True, 'nästa pass påverkades av det misslyckade')
        n = r['nivaer']  # de sex nivåerna var för sig: det underkända passet är erbjudet, laddat men inte belagt i artefakten
        self.assertEqual((n['erbjuden']['varde'], n['belagd_i_artefakten']['varde'], n['effekt_bedomd']['varde']), (True, False, None))

    def test_aterupptagningen_gor_inte_om_passet_av_sig_sjalv_men_ett_begart_forsok_gar(self):
        self.ordning[:] = ['sen', 'sen', 'fore', 'fore']
        self.fordjupa()
        self.assertEqual(self.fordjupa(), 0, 'återupptagningen gjorde om passet utan begäran (slinga)')
        self.assertIn('kompetenspass ej uppfyllda: rorelse', kd.las_status(self.SLUG, 'k01')['skal'],
                      'efter återupptagningen står det misslyckade passet inte kvar i beskedet')
        self.assertIs(self.rec().get('uppfyllt'), False, 'återupptagningen räknade det misslyckade passet som uppfyllt')
        kd.begar_nytt_passforsok(self.SLUG, 'k01', self.ROR)
        self.ordning[:] = ['fore']
        self.assertEqual(self.fordjupa(), 1, 'det begärda nya försöket gjordes inte (eller gjorde om det uppfyllda passet)')
        r = self.rec()
        self.assertEqual((r['uppfyllt'], r['omgang']), (True, 2))
        self.assertIs(r['foregaende_omgang']['genomford'], False)
        self.assertNotIn('ej uppfyllda', kd.las_status(self.SLUG, 'k01')['skal'])
        with self.assertRaises(ValueError):
            kd.begar_nytt_passforsok(self.SLUG, 'k01', self.ROR)  # redan uppfyllt

    def test_budgeten_tar_slut(self):
        self.ordning[:] = ['sen', 'sen', 'fore', 'fore']
        self.fordjupa()
        kd.begar_nytt_passforsok(self.SLUG, 'k01', self.ROR)
        self.ordning[:] = ['sen', 'sen']
        self.fordjupa()
        self.assertEqual((self.rec()['uppfyllt'], self.rec()['omgang']), (False, 2))
        with self.assertRaises(ValueError) as fel:
            kd.begar_nytt_passforsok(self.SLUG, 'k01', self.ROR)
        self.assertIn('budgeten är slut', str(fel.exception))
        self.assertEqual(kd.main([self.SLUG, '--nytt-passforsok', 'k01', self.ROR]), 2)
        self.assertEqual(self.fordjupa(), 0)

    def test_aterstallningen_som_faller_syns(self):
        self.ordning[:] = ['sen', 'sen', 'fore', 'fore']
        self.ater_fel = True
        self.fordjupa()
        r = self.rec()
        st = kd.las_status(self.SLUG, 'k01')
        self.assertIn('återställningen föll', str(r.get('aterstalld')), 'att återställningen föll syns inte')
        self.assertIs(r.get('uppfyllt'), False)
        self.assertEqual(st['status'], 'ofullstandig', 'en kandidat med kvarvarande arbete utan kärnan stod kvar som förfinad')

    def test_ett_uppfyllt_pass_gors_inte_om(self):
        self.ordning[:] = ['fore', 'fore']
        self.assertEqual(self.fordjupa(), 2)
        self.assertIs(self.rec()['uppfyllt'], True)
        n = self.rec()['nivaer']
        self.assertEqual({k: v['varde'] for k, v in n.items()}, {'erbjuden': True, 'laddad': True, 'anrop_med_resultat': True, 'redovisad': True,
                                                                 'belagd_i_artefakten': True, 'effekt_bedomd': None})
        self.assertIn('skaparens eget omdöme: battre', n['effekt_bedomd']['kalla'], 'skaparens omdöme räknades som oberoende bedömning')
        self.assertEqual(self.fordjupa(), 0)
        self.assertEqual(kd.main([self.SLUG, '--nytt-passforsok', 'k01', self.ROR]), 2)



class Mobbinflode(unittest.TestCase):
    """T01: överföringen från referenstjänsten till skaparens uppdrag, med en attrapp bara vid tjänstens session (samla)."""
    SLUG = 't01-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'T01 Mobbins flöden'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        r = kd.rot(self.SLUG)
        r.mkdir(parents=True)
        plan = {'kandidater': {'k01': {'mobbin_fraga': 'salon booking flow', 'mobbin_typ': 'flode'},
                               'k02': {'mobbin_fraga': 'project gallery grid', 'mobbin_typ': 'skarm'}}}
        (r / 'KANDIDATPLAN.json').write_text(json.dumps(plan))
        self.fragor, self.traffar = [], []

        def samla(slug, uppdrag, underlag=None, katalog='tjanster', **kw):
            self.fragor.extend(uppdrag['fragor'])
            rot_t = Path(underlag) / slug / 'referenser' / katalog
            rot_t.mkdir(parents=True, exist_ok=True)
            return rot_t, {'tjanster': {'mobbin': {'ok': True, 'bilder': 3, 'anmarkningar': [], 'traffar': self.traffar}}, 'slappta': []}
        self.stack.enter_context(patch.object(referenstjanster, 'samla', samla))

    def steg(self, n, fil=True, fel=None):
        return {'nr': n, 'fil': 'referenser/uppdrag/mobbin/f-steg-%02d.png' % n if fil else None, 'beskrivning': 'steg %d visar valet' % n, 'fel': fel}

    def material(self):
        kd.uppdragsmaterial(self.SLUG)
        um = json.loads((kd.rot(self.SLUG) / kd.UPPDRAGSMATERIAL).read_text())
        return um['kandidater'], {k: '\n'.join(kd.uppdragsmaterial_rader(self.SLUG, k)) for k in ('k01', 'k02')}

    def test_uppgiften_valjer_skarm_eller_flode(self):
        self.material()
        self.assertEqual({f['fraga']: f['typ'] for f in self.fragor}, {'salon booking flow': 'flode', 'project gallery grid': 'skarm'})

    def test_flode_utan_omslag_nar_skaparen_med_stegen_i_ordning(self):
        self.traffar[:] = [{'titel': 'Bokning', 'fraga': 'salon booking flow', 'fil': None, 'beskrivning': 'tre steg',
                            'steg': [self.steg(1), self.steg(2)]}]
        kand, rader = self.material()
        self.assertNotIn('mobbin_fel', kand['k01'], 'ett flöde utan omslagsbild redovisades som tomt')
        m = kand['k01']['mobbin'][0]
        self.assertEqual((m['typ'], m['fil'], [s['nr'] for s in m['steg']]), ('flode', None, [1, 2]))
        self.assertTrue(m['rapport'].endswith('referenser/uppdrag/TJANSTER.md'), m['rapport'])
        self.assertLess(rader['k01'].index('f-steg-01.png'), rader['k01'].index('f-steg-02.png'), 'stegen kom inte i ordning')
        self.assertIn('steg 2 visar valet', rader['k01'])
        self.assertIn('Ursprunget', rader['k01'])

    def test_flode_med_omslag_behaller_bade_omslag_och_steg(self):
        self.traffar[:] = [{'titel': 'Bokning', 'fraga': 'salon booking flow', 'fil': 'referenser/uppdrag/mobbin/omslag.png', 'beskrivning': 'b',
                            'steg': [self.steg(1)]}]
        kand, rader = self.material()
        m = kand['k01']['mobbin'][0]
        self.assertTrue(m['fil'].endswith('omslag.png'))
        self.assertEqual(len(m.get('steg') or []), 1, 'flödets steg följde inte med omslaget')
        self.assertIn('omslag.png', rader['k01'])

    def test_enskild_skarm_utan_steg(self):
        self.traffar[:] = [{'titel': 'Galleri', 'fraga': 'project gallery grid', 'fil': 'referenser/uppdrag/mobbin/galleri.png', 'beskrivning': 'g',
                            'steg': []}]
        kand, rader = self.material()
        m = kand['k02']['mobbin'][0]
        self.assertEqual((m.get('typ'), m.get('steg')), ('skarm', []))
        self.assertIn('Mobbins skärmar', rader['k02'])

    def test_saknad_stegbild_star_med_skalet(self):
        self.traffar[:] = [{'titel': 'Bokning', 'fraga': 'salon booking flow', 'fil': None, 'beskrivning': 'b',
                            'steg': [self.steg(1), self.steg(2, fil=False, fel='nedladdningen föll')]}]
        kand, rader = self.material()
        self.assertEqual(len(((kand['k01'].get('mobbin') or [{}])[0]).get('steg') or []), 2, 'flödet med en saknad stegbild föll bort')
        self.assertIn('2. ingen bild (nedladdningen föll)', rader['k01'])

    def test_tomt_resultat_redovisas_som_tomt(self):
        kand, rader = self.material()
        self.assertIn('inga flöden', kand['k01']['mobbin_fel'])
        self.assertIn('Mobbin gav inga flöden', rader['k01'])
        self.assertIn('Mobbin gav inga skärmar', rader['k02'])



class Jamforelsebesked(unittest.TestCase):
    """T02: granska.jamforelsebesked och granskarkrav som arbetaren använder dem, med frysta bilder och syntetiska svar."""

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'T02 jämförelsen'))).resolve()
        self.rdir = self.tmp / 'omgang'
        v = self.rdir / 'vinnare'
        self.proto = [v / 'vy-390-ruta-01.png', v / 'vy-1440-ruta-01.png', v / 'vy-390-meny.png', v / 'undersidor' / 'tjanster' / 'vy-390-ruta-01.png']
        s = self.rdir / 'sajt'
        self.bygg = [s / 'hem' / 'vy-390-ruta-01.png', s / 'hem' / 'vy-1440-ruta-01.png', s / 'hem' / 'vy-390-meny.png', s / 'tjanster' / 'vy-390-ruta-01.png',
                     s / 'hem' / 'vy-768-ruta-01.png']
        for f in self.proto + self.bygg:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b'png')
        self.vinnare = ({'kandidat': 'k03', 'version': 'v7', 'godkand': {'tid': 't'}}, self.proto)
        self.alla = [{'sida': s_, 'vy': v_, 'klass': 'godkand_anpassning', 'skal': 'riktningen genomförd'}
                     for s_, v_ in (('start', '390'), ('start', '1440'), ('tjanster', '390'))]

    def svar(self, status='genomford', jamforda=None):
        return {'prototypjamforelse': {'status': status, 'jamforda': self.alla if jamforda is None else jamforda, 'ej_bedomt': [], 'skal': 's'}}

    def lasning(self, saknas=()):
        return {'verifierad': True, 'grupper': {'prototyp': {'kravda': 4, 'lasta': 4 - len(saknas), 'saknas': list(saknas)},
                                                'bygget_jamfort': {'kravda': 4, 'lasta': 4, 'saknas': []}}}

    def besked(self, delar, lasningar, vinnare='ja', dist='d' * 64):
        return granska.jamforelsebesked(self.vinnare if vinnare == 'ja' else vinnare, self.bygg, delar, lasningar, self.rdir, dist)

    def test_komplett_jamforelse_ar_verifierad(self):
        b = self.besked([self.svar()], [self.lasning()])
        self.assertEqual(b['status'], 'verifierad', b)
        self.assertEqual(b['tackning']['par'], 4)
        self.assertEqual(b['granskare'][0]['klasser'], {'godkand_anpassning': 3})

    def test_saknade_prototypbilder_och_ingen_prototyp(self):
        self.assertEqual(self.besked([self.svar()], [self.lasning()], vinnare=(self.vinnare[0], []))['status'], 'underlag_saknas')
        self.assertEqual(self.besked([self.svar()], [self.lasning()], vinnare=None)['status'], 'ej_tillamplig')

    def test_uttryckligt_ej_bedomt_ar_aldrig_verifierat(self):
        self.assertEqual(self.besked([self.svar('ej_bedomd', [])], [self.lasning()])['status'], 'ej_bedomd')
        b = self.besked([self.svar(jamforda=self.alla[:1])], [self.lasning()])
        self.assertEqual(b['status'], 'ej_bedomd', 'en jämförelse med obedömda par blev verifierad')
        self.assertIn('tjanster 390', b['granskare'][0]['obedomda'])
        self.assertEqual(self.besked([{}], [self.lasning()])['status'], 'ej_bedomd', 'ett svar utan besked blev verifierat')

    def test_observationsfel_skils_fran_ej_bedomt(self):
        self.assertEqual(self.besked([self.svar()], [{'verifierad': False, 'skal': 'transkriptet saknas'}])['status'], 'ej_observerbar')
        self.assertEqual(self.besked([self.svar()], [None])['status'], 'ej_observerbar')
        self.assertEqual(self.besked([self.svar()], [self.lasning(saknas=['omgang/vinnare/vy-390-meny.png'])])['status'], 'ej_last')

    def test_fel_version(self):
        (self.rdir / 'VINNARJAMFORELSE.json').write_text(json.dumps({'bindning': {'vinnare': {'kandidat': 'k03', 'version': 'v7'},
                                                                                 'bygget': {'dist_sha256': 'a' * 64}}}))
        b = self.besked([self.svar()], [self.lasning()], dist='b' * 64)
        self.assertEqual(b['status'], 'fel_version', b)
        (self.rdir / 'VINNARJAMFORELSE.json').write_text(json.dumps({'bindning': {'vinnare': {'kandidat': 'k03', 'version': 'v6'},
                                                                                 'bygget': {'dist_sha256': 'b' * 64}}}))
        self.assertEqual(self.besked([self.svar()], [self.lasning()], dist='b' * 64)['status'], 'fel_version')

    def test_tva_granskare_det_samsta_galler(self):
        b = self.besked([self.svar(), self.svar('ej_bedomd', [])], [self.lasning(), self.lasning()])
        self.assertEqual(b['status'], 'ej_bedomd')

    def test_prototypens_och_byggets_bilder_ar_laskrav(self):
        krav = granska.granskarkrav(None, [], self.bygg, self.vinnare)
        self.assertEqual(len(krav['prototyp']), 4)
        self.assertEqual(len(krav['bygget_jamfort']), 4, 'byggets motsvarande bilder saknas i kraven')
        self.assertNotIn('prototyp', granska.granskarkrav(None, [], self.bygg, None))

    def test_domen_visar_beskedet_skilt_fran_godkannandet(self):
        jam = self.besked([self.svar('ej_bedomd', [])], [self.lasning()])
        post = {'slug': 's', 'godkand': True, 'niva': None, 'runda': 1, 'tid': 't', 'modell': 'm', 'effort': 'e', 'dist_sha256': 'd' * 64,
                'troskel': granska.TROSKEL, 'kriterier': {k: {'betyg': 9, 'motivering': '', 'visa': True} for k in granska.KRITERIER},
                'blockerande': [], 'visuell_jamforelse': jam}
        md = granska.markdown(post)
        self.assertIn('GODKÄND', md)
        self.assertIn('## Jämförelsen mot den godkända prototypen', md)
        self.assertIn('**ej_bedomd**', md)
        self.assertIn('visar inte att jämförelsen är gjord', md)



class Blindvaktensfrist(unittest.TestCase):
    """Krokens tidsgräns i de verkliga sessionsargumenten mot vaktens egen frist."""

    def test_krokens_tidsgrans_ar_klart_over_vaktens_frist(self):
        with patch.multiple(atelje, claude=lambda: 'claude', kundvakt=lambda *a, **k: None):
            args = atelje.session_args(['Read', 'Write'], blind='/tmp/lista.json')
        krokar = json.loads(args[args.index('--settings') + 1])['hooks']['PreToolUse']
        vakt = [h for k in krokar for h in k['hooks'] if 'blindvakt.py' in h['command']]
        self.assertEqual(len(vakt), 1)
        self.assertGreaterEqual(vakt[0]['timeout'], blindvakt.FRIST + 15, 'Claude Codes tidsgräns kan slå till före vaktens egen')
        self.assertIn('exit 2', vakt[0]['command'])
        with self.assertRaises(ValueError):
            blindvakt.krok('/tmp/lista.json', timeout=blindvakt.FRIST)



class Blindarbetsyta(unittest.TestCase):
    """Den blinda sessionens tomma arbetskatalog: aldrig i motorns rot, och en läsning genom länken till motorns skills
    räknas som filen den pekar på (kompetensens kvitto), medan en kopia under en annan rot är en annan fil."""

    def setUp(self):
        self.tmp = Path(self.enterContext(korregister.egen_tmp_med('nwp-kallgap-', 'den blinda arbetskatalogen'))).resolve()

    def test_arbetskatalogen_har_bara_lanken_till_skills(self):
        with patch.object(tempfile, 'tempdir', str(self.tmp)):
            d = atelje.blind_arbetsyta('prov')
        self.assertEqual(d.parent, self.tmp)
        self.assertTrue(d.name.startswith('nwp-blind-'))
        self.assertIn('nwp-blind-', stadning.TMP_PREFIX, 'städningen känner inte igen katalogen')
        self.assertEqual((d / '.claude' / 'skills').resolve(), (atelje.ROOT / '.claude' / 'skills').resolve())
        self.assertEqual(sorted(p.name for p in d.iterdir()), ['.claude', korregister.AGARFIL])

    def test_aldrig_i_motorns_rot(self):
        fore = sorted(p.name for p in atelje.ROOT.iterdir())
        with patch.object(tempfile, 'tempdir', str(atelje.ROOT)), self.assertRaises(RuntimeError):
            atelje.blind_arbetsyta('prov')
        self.assertEqual(sorted(p.name for p in atelje.ROOT.iterdir()), fore, 'något skapades i roten')

    def test_lasning_genom_lanken_raknas_som_motorns_fil(self):
        with patch.object(tempfile, 'tempdir', str(self.tmp)):
            d = atelje.blind_arbetsyta('prov')
        skill = sorted((atelje.ROOT / '.claude' / 'skills').glob('*/SKILL.md'))[0]
        rel = skill.relative_to(atelje.ROOT).as_posix()
        self.assertEqual(bildkedja.relativ(str(d / rel)), rel)
        kopia = self.tmp / 'kopia' / rel
        kopia.parent.mkdir(parents=True); kopia.write_bytes(skill.read_bytes())
        self.assertEqual(bildkedja.relativ(str(kopia)), str(kopia), 'en kopia under en annan rot är en annan fil')


class Metodvariant(unittest.TestCase):
    """H01: skissens uppdrag i grundvarianten och i varianten h01, med attrapper vid metodleveransen och kundens underlag."""

    def prompt(self, variant):
        m = {'sha': 's', 'filer': [], 'delar': {'före': ['METOD-skiss.md'], 'uppslag': ['METOD-skiss-uppslag.md'], 'varv': [], 'text': []}}
        tmp = self.enterContext(korregister.egen_tmp_med('nwp-kallgap-', 'H01 varianten'))
        with patch.multiple(atelje, UNDERLAG=Path(tmp) / 'underlag', KUNDER=Path(tmp) / 'kunder'), \
                patch.multiple(kd, metodinfo=lambda *a, **k: m, uppdragsmaterial_rader=lambda *a: [], METODVARIANT=variant), \
                patch.multiple(skapande, telefon=lambda *a, **k: None, kritikrader=lambda *a, **k: []), \
                patch.object(kompetens, 'prompt_rader', lambda *a, **k: []):
            return kd.skiss_prompt('h01-prov', 'k01')

    def test_grundvarianten_ar_oforandrad(self):
        t = self.prompt('grund')
        self.assertNotIn('Visuellt mål', t)
        self.assertIn('kunden. Bygg sedan en', ' '.join(t.split()))
        self.assertIn('beslutsliggare för de betydande vägvalen', t)

    def test_h01_skriver_malet_fore_kod_och_provar_det_efter_renderingen(self):
        t = ' '.join(self.prompt('h01').split())
        self.assertLess(t.index('Visuellt mål (preliminärt)'), t.index('Bygg sedan en första version'), 'målet kom inte före koden')
        for ord_ in ('huvudkompositionen', 'de typografiska rollerna', 'bildernas uppgift och beskärning', 'kontrast, täthet och rytm',
                     'knuten till en utpekad referensbild', 'Omprövat mål', 'det preliminära visuella målet'):
            self.assertIn(ord_, t)

    def test_okand_variant_stoppar(self):
        with patch.object(kd, 'METODVARIANT', 'h1'):
            with self.assertRaises(ValueError):
                kd.metodvariant()



class Metodforsoket(unittest.TestCase):
    """Kvalitetsprovets H01-jämförelse i det befintliga metodförsöket (ab_skiss), utan modellanrop."""

    def setUp(self):
        prov_ab_skiss.Skissforsok.setUp(self)
        p = kd.rot(self.slug) / 'PLANPROVNING.json'
        post = json.loads(p.read_text()); post['kvitto'] = prov_omgranskning.giltigt_kvitto('planprovning')
        p.write_text(json.dumps(post))

    def test_armarna_far_var_sin_variant_och_samma_ovriga_installningar(self):
        with patch.object(atelje, 'session') as s:
            post = ab.forbered_skiss(self.slug, 'k01', 'metodvariant')
        s.assert_not_called()
        self.assertEqual((post['variabel'], set(post['varden'].values())), ('metodvariant', {'grund', 'h01'}))
        std = kd.skaparval()
        for kid in post['kandidater']:
            self.assertEqual(kd.skaparval(self.slug, kid), std, 'metodvarianten ändrade skaparens modell eller effort')
            self.assertEqual(kd.metodvariant(self.slug, kid), post['varden'][kid])
        self.assertEqual(kd.metodvariant(), 'grund', 'utan arm gäller standarden')
        self.assertEqual((kd.kdir(self.slug, 'k01') / 'UPPDRAG.md').read_bytes(), (kd.kdir(self.slug, 'k02') / 'UPPDRAG.md').read_bytes())

    def test_okand_variabel_nekas(self):
        with self.assertRaises(ValueError):
            ab.forbered_skiss(self.slug, 'k01', 'typsnitt')

    def test_klonen_bar_planprovningen_och_provas_inte_om(self):
        """Den andra armen är det prövade uppdraget byte för byte: --fortsatt prövar ingen arm för sig (N01)."""
        post = ab.forbered_skiss(self.slug, 'k01', 'metodvariant')
        pp = json.loads((kd.rot(self.slug) / 'PLANPROVNING.json').read_text())
        self.assertEqual(pp['provade'].get('k02'), pp['provade']['k01'])
        self.assertEqual((pp.get('klonade') or {}).get('k02'), {'fran': 'k01', 'forsok': post['id']})
        self.assertEqual(kd.planprovning_behov(self.slug, post['kandidater']), [], 'en arm skulle prövas om för sig')

    def test_en_oprovad_plan_ger_inget_forsok(self):
        f = kd.rot(self.slug) / 'PLANPROVNING.json'
        f.write_text(json.dumps({'kandidater': {'k01': {}}, 'provade': {'k01': 'en annan version'}}))
        with self.assertRaises(ValueError):
            ab.forbered_skiss(self.slug, 'k01', 'metodvariant')
        self.assertFalse(kd.kdir(self.slug, 'k02').exists())


class Forsokslaset(unittest.TestCase):
    """Kvalitetsprovet 2026-10-09, försök 1: armarnas typsnitt (typsnitt.py i basprojektet) fällde låset. Låset tål nu
    armarnas tillägg men inte ändrade förutsättningar."""

    def setUp(self):
        prov_ab_skiss.Skissforsok.setUp(self)
        self.pj = atelje.KUNDER / self.slug / 'sajt' / 'package.json'
        self.pj.write_text(json.dumps({'dependencies': {'astro': '7.3.5'}}))
        self.post = ab.forbered_skiss(self.slug, 'k01', 'metodvariant')

    def krav(self):
        return ab_skiss.krav(ab, self.slug)

    def test_armarnas_typsnitt_faller_inte_laset(self):
        self.pj.write_text(json.dumps({'dependencies': {'astro': '7.3.5', '@fontsource-variable/archivo': '^5.3.0'}}))
        (self.pj.parent / 'package-lock.json').write_text('{"lockfileVersion": 3, "ny": true}')
        self.assertEqual(self.krav()['id'], self.post['id'])

    def test_en_andrad_verktygskedja_faller_laset(self):
        self.pj.write_text(json.dumps({'dependencies': {'astro': '8.0.0'}}))
        with self.assertRaises(ValueError):
            self.krav()

    def test_ett_tillagt_referenspaket_redovisas(self):
        ny = self.u / 'referenser' / 'paket-v02' / 'ny.png'
        ny.parent.mkdir(parents=True); ny.write_bytes(b'png')
        (self.u / 'INNEHALL.md').write_text('# saknades vid förberedelsen')
        self.assertEqual(self.krav()['id'], self.post['id'])
        res = ab_skiss.resultat(ab, self.slug)
        self.assertEqual(sorted(res['tillkomna_under_forsoket']['underlag']), ['INNEHALL.md', 'referenser/paket-v02/ny.png'])
        (self.u / 'REFERENSER.md').write_text('# ändrad')  # fanns vid förberedelsen: en ändring, inget tillägg
        with self.assertRaises(ValueError):
            self.krav()

    def test_en_andrad_eller_borttagen_kundfil_faller_laset(self):
        (self.u / 'BRIEF.md').write_text('ändrad')
        with self.assertRaises(ValueError):
            self.krav()
        (self.u / 'BRIEF.md').write_text('syntetiskt BRIEF.md')
        self.krav()
        (self.u / 'referenser' / 'paket-v01' / 'referens.png').unlink()
        with self.assertRaises(ValueError):
            self.krav()


class Stoppefterplanen(unittest.TestCase):
    """NWP_KANDIDAT_STOPP_EFTER=planprovning: skisskörningen stannar efter planprövningen, före skaparna, som ett avslutat
    läge (planprovad) med slutkod 0; prototyp.py utan --fortsatt startar inget nytt omtag därifrån."""

    def test_skaparna_startar_inte_och_laget_ar_avslutat(self):
        import ateljeslut
        import prototyp
        import urval
        tmp = Path(self.enterContext(korregister.egen_tmp_med('nwp-kallgap-', 'stoppet efter planprövningen'))).resolve()
        self.enterContext(patch.multiple(atelje, UNDERLAG=tmp / 'underlag', KUNDER=tmp / 'kunder'))
        (kd.rot('stopp-prov')).mkdir(parents=True)
        (kd.rot('stopp-prov') / kd.UPPDRAGSMATERIAL).write_text('{}')
        import referensfixtur  # referenskontraktet uppfyllt: provet prövar stoppet efter planprövningen
        plan_ = referensfixtur.uppfyll(atelje.UNDERLAG, 'stopp-prov', {'kompetens': prov_omgranskning.giltigt_kvitto('planera'),
                                                                       'kandidater': {'k01': {'titel': 'Syntetiskt uppdrag'}}})
        (kd.rot('stopp-prov') / 'KANDIDATPLAN.json').write_text(json.dumps(plan_))
        referensfixtur.uppdrag(atelje.UNDERLAG, 'stopp-prov', plan_, 'k01', '# Uppdrag\n')
        status, skrivna = {}, []
        with patch.multiple(kd, create=True, STOPP_EFTER='planprovning', lista=lambda slug: ['k01'], leverera_metod=lambda slug: {},
                            planprovning_behov=lambda slug, ids: [], korlage=lambda slug, status: 'skiss',
                            las_status=lambda slug, kid: {'status': 'planerad'},
                            forbered_referensprofiler=lambda slug, ids: {'ok': True, 'syntetisk': True},  # profileringen prövas för sig
                            kor_pool=lambda *a, **k: self.fail('en skapare startade')), \
                patch.object(urval, 'vid_start', return_value={}):
            self.assertEqual(kd.kor('stopp-prov', status, lambda: skrivna.append(status.get('steg'))), [])
        self.assertEqual(status['steg'], 'planprovad')
        self.assertEqual(skrivna[-1], 'planprovad')
        self.assertNotIn('skapa', skrivna, 'skapandet påbörjades')
        self.assertIn('planprovad', atelje.AVSLUTADE)
        self.assertFalse(atelje.avbruten(dict(status, pid=999999999)), 'ett avsiktligt stopp är inget avbrott')
        utfall, kod, _text = ateljeslut.utfall(status)
        self.assertEqual((utfall, kod), ('klar', 0))
        with patch.object(atelje, 'las_json', return_value=dict(status)), patch.object(prototyp.skapande, 'senaste', return_value=None), \
                patch.object(prototyp.skapande, 'agarens_senaste', return_value={'oklara': []}):
            lage, skal = prototyp.lage('stopp-prov')
        self.assertEqual(lage, 'stopp', skal)
        self.assertIn('--fortsatt', skal)

    def test_fortsatt_tar_vid_efter_planprovad_men_inte_efter_avslutad(self):
        nekas = getattr(atelje, 'fortsatt_nekas', None)
        self.assertIsNotNone(nekas, 'spärren går inte att pröva för sig')
        self.assertIsNone(nekas({'steg': 'planprovad'}), 'skaparna nås inte från planprovad')
        self.assertIsNone(nekas({'steg': 'fel'}))
        for steg in ('klar_for_bedomning', 'klar', 'forberedd', None):
            self.assertIsNotNone(nekas({'steg': steg}), steg)

    def test_slutposten_sager_vad_som_finns_att_gora(self):
        import ateljeslut
        st = {'steg': 'planprovad', 'kandidatflode': True, 'kandidater': {'k01': 'planerad'}}
        ag = ateljeslut.tillstanden('stopp-prov', st, 'klar', [{'id': 'k01', 'valbar': False, 'status': 'planerad'}],
                                    {'efter': [], 'olasbara': []})
        text = json.dumps(ag, ensure_ascii=False)
        self.assertNotIn('en ny körning behövs', text)
        self.assertIn('planprövningen', text)

    def test_okant_varde_stoppar_vid_import(self):
        import subprocess
        import sys as sys_
        r = subprocess.run([sys_.executable, '-B', '-c', 'import kandidater'], cwd=str(atelje.ROOT / 'kontroller'), capture_output=True, text=True,
                           env=dict(__import__('os').environ, NWP_KANDIDAT_STOPP_EFTER='skapa'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('NWP_KANDIDAT_STOPP_EFTER', r.stderr)


if __name__ == '__main__':
    unittest.main()
