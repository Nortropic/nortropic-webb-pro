#!/usr/bin/env python3
"""Designfasen i Claude Design (ägarens uppdrag 2026-10-12; kunskap/claude-design.md): mekaniken genom de verkliga
ingångarna, med attrapper bara för det externa (Design-typens körmiljö, sessionerna och kvittot). Inga modeller och inget nät.

- A: en aktiv designfas stoppar kandidatflödet efter researchen (ingen plan och inga skapare i Code), ateljén nekar
  förfining och uppdrag, och NWP_KANDIDAT_STOPP_EFTER=forskning stannar på samma ställe utan designfas.
- B: en version ur dukens återlästa filer: kopierad oförändrad, hashad, renderad i 390/768/1440 och med menyn öppen;
  samma artefaktversion två gånger vägras, en saknad ritning vägras, en okänd tillgång redovisas.
- C: beställning → svar → införd i en ny version, med projekt, duk, version, ritning, uppgift, material och resultat.
- D: specialistpasset: rollens kompetensblock och verktyg, svaret i schemat, kvittot ur transkriptet; kritiken får inte
  källan.
- E: ägarens godkännande i domloggen, bundet till versionens filer och bilder; överlämningen krävs komplett; en ändrad bild
  eller en senare dom gör det ogiltigt; kor.sh tar vid från ett giltigt designgodkännande.
- F: kompetensplaceringen (designfas-karta) har en rad per skill, tjänst och specialistpass.
- G: startkommandot: kundvakten, flödets tjänster med --strict-mcp-config och godkännandet nekat för sessionen.
- H: produktionsbandet: stationerna i processmodellens ordning med metod, versioner med stationen, insatsen synlig,
  hoppade stationer, kritikens återgång, bandets läge och kvittot som redovisar utan att fälla.
"""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister  # noqa: E402
import atelje  # noqa: E402
import designfas as df  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import skapande  # noqa: E402

SLUG = 'designfas-prov'
KANVAS = 'https://claude.ai/artifact/ProvKanvas0123456789'
BLOBB = '0c71b2aef889d50acbb8ddc9a36ab2a1'
# Attrappen av Design-typens körmiljö: visar <x-dc>, döljer <helmet> och låter en menyknapp med aria-expanded växla.
RUNTIME = ('/* attrapp av dc-runtime.js för provet */\n' + '/' * 12000 + '\n'
           "document.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('helmet').forEach(h=>h.style.display='none');"
           "document.querySelectorAll('button[aria-expanded]').forEach(b=>b.addEventListener('click',()=>{const o=b.getAttribute('aria-expanded')!=='true';"
           "b.setAttribute('aria-expanded',o?'true':'false');const m=document.getElementById(b.getAttribute('aria-controls'));if(m)m.hidden=!o;}));});\n")
RITNING = '''<!doctype html>
<html lang="sv">
<head><meta charset="utf-8"><title>Provriktning</title><script src="./support.js"></script></head>
<body>
<x-dc>
<helmet><style>body{margin:0} .meny{display:none} @media (max-width:760px){.lankar{display:none}.meny{display:inline-flex}}</style></helmet>
<div style="font-family: system-ui; padding: 16px; max-width: 1200px; margin: 0 auto">
<header style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px">
<a href="#top">Provverkstan</a>
<nav class="lankar" aria-label="Huvudmeny" style="gap:16px"><a href="#a">Service</a> <a href="tel:0701740642">Ring</a></nav>
<button type="button" class="meny" aria-expanded="false" aria-controls="m" style="min-height:44px">Meny</button>
<nav id="m" hidden aria-label="Mobilmeny"><a href="#a">Service</a></nav>
</header>
<main id="top"><h1>Provrubrik</h1><img src="/_blob/%s" alt="Verkstaden" style="width:100%%;max-width:600px;display:block"></main>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":1440,"height":900}}'>
class Component extends DCLogic { renderVals() { return {}; } }
</script>
</body>
</html>
''' % BLOBB
PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                    '1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')


class Grund(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'designfasens prov'))).resolve()
        self.u, self.k = self.tmp / 'underlag', self.tmp / 'kunder'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.u, KUNDER=self.k))
        self.stack.enter_context(patch.object(df, 'UNDERLAG', self.u))
        self.stack.enter_context(patch.object(skapande, 'UNDERLAG', self.u))
        (self.u / SLUG / 'bilder').mkdir(parents=True)
        (self.u / SLUG / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provverkstan', 'fiktiv': True}))
        (self.u / SLUG / 'BRIEF.md').write_text('# Brief\n')
        self.bild = self.u / SLUG / 'bilder' / 'verkstad.png'
        self.bild.write_bytes(PNG)

    def duk(self, rel='prov-release-1'):
        df.ny(SLUG, KANVAS)
        rt = self.tmp / 'dc-runtime.js'
        rt.write_text(RUNTIME)
        df.runtime(SLUG, rt, rel)
        df.tillgang(SLUG, BLOBB, self.bild, kalla='bilder/verkstad.png, verksamhetens egen (fiktiv i provet)')

    def las_tillbaka(self, namn='fran', ritning=RITNING, extra=None, notes=None):
        p = self.tmp / namn / 'project'
        p.mkdir(parents=True)
        boards = {'Main.dc.html': {'x': 0, 'y': 0, 'w': 1440, 'h': 900, 'expand': 'fill', 'title': 'Riktning A'}}
        boards.update(extra or {})
        (p / 'canvas.json').write_text(json.dumps({'v': 3, 'title': 'Prov', 'boards': boards, 'order': list(boards), 'notes': notes or {}}))
        (p / 'Main.dc.html').write_text(ritning)
        return p.parent


class A_Sparr(Grund):
    def test_aktiv_designfas_stannar_efter_researchen(self):
        df.ny(SLUG)
        anrop = []
        st = {}
        with patch.multiple(kd, leverera_metod=lambda _: {}, korlage=lambda *a: 'skiss',
                            forska=lambda slug, n, skiss=False: anrop.append('forska') or {'nytt': [], 'fel': None},
                            planera=lambda *a, **k: anrop.append('planera')):
            import urval
            with patch.object(urval, 'vid_start', return_value={}):
                ut = kd.kor(SLUG, st, lambda: None, n=2)
        self.assertEqual(ut, [])
        self.assertEqual(anrop, ['forska'], 'researchen körs, planen aldrig')
        self.assertEqual(st['steg'], 'forskad')
        self.assertIn('Claude Design', st['skal'])

    def test_stoppunkten_forskning_utan_designfas(self):
        anrop = []
        st = {}
        with patch.multiple(kd, STOPP_EFTER='forskning', leverera_metod=lambda _: {}, korlage=lambda *a: 'skiss',
                            forska=lambda slug, n, skiss=False: anrop.append('forska') or {'nytt': [], 'fel': None},
                            planera=lambda *a, **k: anrop.append('planera')):
            import urval
            with patch.object(urval, 'vid_start', return_value={}):
                kd.kor(SLUG, st, lambda: None, n=2)
        self.assertEqual((anrop, st['steg']), (['forska'], 'forskad'))
        self.assertNotIn('Claude Design', st['skal'])
        self.assertIsNone(atelje.fortsatt_nekas({'steg': 'forskad'}, SLUG), 'utan designfas tar --fortsatt vid i planeringen')
        df.ny(SLUG)
        self.assertIn('Claude Design', atelje.fortsatt_nekas({'steg': 'forskad'}, SLUG))

    def test_en_plan_fran_fore_designfasen_ger_inga_skapare(self):
        df.ny(SLUG)
        st = {}
        with patch.multiple(kd, leverera_metod=lambda _: {}, korlage=lambda *a: 'skiss', lista=lambda slug: ['k01'],
                            kor_pool=lambda *a, **k: self.fail('skaparna startade')):
            import urval
            with patch.object(urval, 'vid_start', return_value={}):
                kd.kor(SLUG, st, lambda: None, n=2)
        self.assertEqual(st['steg'], 'forskad')

    def test_ateljen_nekar_forfining_och_aldre_utforskning(self):
        import inspect
        k = inspect.getsource(atelje.arbeta)
        self.assertLess(k.index('forberedelse.kor(slug, status, skriv)'), k.index('designfas.aktiv(slug, UNDERLAG)'),
                        'förberedelsen går, allt efter den prövas')
        self.assertLess(k.index('designfas.aktiv(slug, UNDERLAG)'), k.index('kandidater.forfina_valda'))
        self.assertIn("lage in ('ny', 'fortsatt')", k)


class B_Version(Grund):
    def test_version_kopieras_hashas_och_renderas(self):
        self.duk()
        # en attrapp av impeccables motor (detektor.motor läser IMPECCABLE_BIN): fynden med kodutdrag och sidtext, och
        # --scope type/layout som ger området per regel (valideringen 2026-10-12)
        motor = self.tmp / 'motor' / 'impeccable'
        motor.parent.mkdir(parents=True, exist_ok=True)
        logg = self.tmp / 'motor' / 'anrop.log'
        motor.write_text('#!%s\nimport json, sys\na = sys.argv[1:]\nopen(%r, "a").write(" ".join(a) + "\\n")\n'
                         'sc = a[a.index("--scope") + 1] if "--scope" in a else None\n'
                         'alla = [{"antipattern": "flat-type-hierarchy", "name": "Flat", "description": "d", "severity": "warning", '
                         '"category": "quality", "snippet": "SIDTEXT-SOM-INTE-FAR-NA-KRITIKEN", "file": "/x", "line": 3},\n'
                         '        {"antipattern": "cramped-padding", "name": "Tight", "description": "d", "severity": "warning", "category": "quality"},\n'
                         '        {"antipattern": "em-dash-overuse", "name": "Dash", "description": "d", "severity": "info", "category": "slop", "advisory": True}]\n'
                         'dom = {"type": ["flat-type-hierarchy"], "layout": ["cramped-padding"]}\n'
                         'print(json.dumps([f for f in alla if sc is None or f["antipattern"] in dom.get(sc, [])]))\nsys.exit(2)\n'
                         % (sys.executable, str(logg)))
        motor.chmod(0o755)
        with patch.dict(os.environ, IMPECCABLE_BIN=str(motor)):
            post = df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första riktningen')
        vk = self.u / SLUG / 'design' / 'versioner' / 'v01'
        for w in ('390', '1440'):
            fynd = json.loads((vk / 'kontroll' / 'detektor' / ('Main.dc.html-%s.json' % w)).read_text())
            self.assertEqual({f['antipattern']: f.get('omrade') for f in fynd},
                             {'flat-type-hierarchy': 'typografi', 'cramped-padding': 'layout', 'em-dash-overuse': None}, w)
            self.assertFalse([f for f in fynd if {'snippet', 'file', 'line'} & set(f)], 'kodutdrag och sidtext når aldrig kritiken')
        anrop = logg.read_text().splitlines()
        self.assertTrue(any('--viewport 390x844' in a and '--scope' not in a for a in anrop)
                        and any('--viewport 1440x900' in a and '--scope type' in a for a in anrop), anrop)
        self.assertIn('Station typografi', df.station_brief(SLUG, 'typografi', 'Main.dc.html', self.u))
        self.assertIn('flat-type-hierarchy', df.station_brief(SLUG, 'typografi', 'Main.dc.html', self.u))
        self.assertNotIn('cramped-padding', df.station_brief(SLUG, 'typografi', 'Main.dc.html', self.u))
        self.assertIn('cramped-padding', df.station_brief(SLUG, 'komposition', 'Main.dc.html', self.u))
        self.assertNotIn('detektorns fynd', df.station_brief(SLUG, 'innehall', 'Main.dc.html', self.u))
        self.assertEqual(post['version'], 'v01')
        self.assertEqual((vk / 'kanvas' / 'Main.dc.html').read_text(), RITNING)
        self.assertIn('name="viewport"', (vk / 'sida' / 'Main.dc.html').read_text(), 'den renderade kopian mäts i 390, inte i 980')
        self.assertNotIn('name="viewport"', RITNING)
        self.assertEqual(post['filer']['Main.dc.html'], df.sha(vk / 'kanvas' / 'Main.dc.html'))
        self.assertEqual(post['tillgangar'], [BLOBB])
        self.assertEqual(post['okanda_tillgangar'], [])
        self.assertEqual(post['rendering']['slutkod'], 0, post['rendering'])
        b = json.loads((vk / 'BILDER.json').read_text())
        r = b['ritningar']['Main.dc.html']
        for w in ('390', '768', '1440'):
            self.assertTrue((vk / r['bilder'][w]['fil']).is_file(), w)
            self.assertFalse(r['bilder'][w]['sidled'], w)
        self.assertEqual(r['bilder']['390-meny']['aria_expanded_efter_klick'], 'true')
        self.assertNotIn('768-meny', r['bilder'], 'menyknappen syns bara i mobilen')
        self.assertEqual(b['tillgangar_begarda'], [BLOBB])
        self.assertIn('inte en skärmbild', b['kalla'])
        self.assertEqual(b['runtime']['release'], 'prov-release-1')
        self.assertIn('axe', b['kontroll'])
        # tilläggets kontroller (punkt 5): LCP-kandidat, bildstorlekar, rörelse med och utan reducerad rörelse, reflow, fokus, stillhet
        m = r['matt']['390']
        self.assertEqual(m['lcp']['tagg'], 'h1', 'den största ytan i provritningen är rubriken')
        self.assertTrue(any(x['kvot'] == 0 or x['kvot'] < 0.9 for x in m['bildstorlekar']))
        self.assertTrue(any('suddig' in v for v in r['varningar']), 'en bild på 1 px som visas stort flaggas')
        self.assertEqual(r['reflow_320']['sidledsspill_px'], 0)
        self.assertTrue(r['stillhet']['390']['lika_6_och_7_s'])
        self.assertIn('reducerad', r['reducerad_rorelse']['1440'])
        self.assertTrue(r['fokus']['1440'] and all(x['synlig'] for x in r['fokus']['1440']), r['fokus'])

    def test_dubblett_saknad_ritning_och_okand_tillgang(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False)
        with self.assertRaisesRegex(df.Fel, 'redan v01'):
            df.version(SLUG, self.las_tillbaka('fran2'), '1791822460-0589', 'igen', bilder=False)
        with self.assertRaisesRegex(df.Fel, 'saknas'):
            df.version(SLUG, self.las_tillbaka('fran3', extra={'B.dc.html': {'w': 10, 'h': 10}}), '1791822461-0590', 'b', bilder=False)
        okand = RITNING.replace(BLOBB, 'f' * 32)
        post = df.version(SLUG, self.las_tillbaka('fran4', ritning=okand), '1791822462-0591', 'ny bild', bilder=False)
        self.assertEqual(post['okanda_tillgangar'], ['f' * 32])
        with self.assertRaisesRegex(df.Fel, 'orsaken'):
            df.version(SLUG, self.las_tillbaka('fran5'), '1791822463-0592', '  ', bilder=False)

    def test_utan_duk_ingen_version(self):
        df.ny(SLUG)
        with self.assertRaisesRegex(df.Fel, 'duken är inte registrerad'):
            df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'x', bilder=False)


class C_Bestallning(Grund):
    def test_livscykeln(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False)
        b = df.bestall(SLUG, 'referenser', 'v01', 'Main.dc.html', 'Bättre förebilder för mobilmenyn i en lokal verkstad', ['bilder/verkstad.png'])
        self.assertEqual({k: b[k] for k in ('id', 'projekt', 'kanvas', 'version', 'ritning', 'typ', 'pass', 'status')},
                         {'id': 'B001', 'projekt': SLUG, 'kanvas': KANVAS, 'version': 'v01', 'ritning': 'Main.dc.html', 'typ': 'referenser',
                          'pass': 'ds_research', 'status': 'bestalld'})
        svarfil = self.tmp / 'svar.md'
        svarfil.write_text('# Svar\nTre förebilder ur Refero med skäl.\n')
        df.svar(SLUG, 'B001', svarfil, 'manuell överlämning i provet')
        self.assertEqual(df.bestallning(SLUG, 'B001')['status'], 'levererad')
        post = df.version(SLUG, self.las_tillbaka('fran2'), '1791822470-0600', 'mobilmenyn efter B001', ['B001'], bilder=False)
        self.assertEqual(post['bestallningar'], ['B001'])
        b = df.bestallning(SLUG, 'B001')
        self.assertEqual((b['status'], b['inford_i']), ('inford', 'v02'))
        df.infor(SLUG, 'B001', 'v02', 'Menyn i 390 visar nu fyra mål i en lista; före/efter i bilderna v01 och v02.')
        self.assertEqual(df.bestallning(SLUG, 'B001')['bedomning']['efter'], 'v02')
        with self.assertRaisesRegex(df.Fel, 'okänd typ'):
            df.bestall(SLUG, 'smak', 'v01', 'Main.dc.html', 'en uppgift som är lång nog att godtas')
        with self.assertRaisesRegex(df.Fel, 'finns inte'):
            df.bestall(SLUG, 'typografi', 'v09', 'Main.dc.html', 'en uppgift som är lång nog att godtas')


class D_Specialist(Grund):
    def test_passet_far_rollen_och_svaret_sparas(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False)
        df.bestall(SLUG, 'typografi', 'v01', 'Main.dc.html', 'Typografisk analys av rubrikskalan i mobilen och datorn')
        fangat = {}

        def session(prompt, verktyg, ut, schema=None, *a, **k):
            fangat.update(prompt=prompt, verktyg=verktyg, schema=schema, slug=k.get('slug'), webb=k.get('webb'))
            return {'session_id': '00000000-0000-4000-8000-000000000001', 'total_cost_usd': 0.1,
                    'structured_output': {'sammanfattning': 'Skalan är platt i 390.', 'fynd': [{'plats': 'h1', 'tillstand': '390', 'vad': 'för liten', 'belagg': 'Main-390.png', 'allvar': 2}],
                                          'forslag': [{'vad': 'större h1', 'varfor': 'hierarki', 'kalla': 'better-typography'}], 'referenser': [],
                                          'begransningar': [], 'kompetens': {'aktiverade': ['better-typography'], 'lasta': [], 'valda': []}}}
        with patch.object(atelje, 'session', side_effect=session), \
                patch.object(kompetens, 'kvitto', return_value={'skill_anrop': ['better-typography']}), \
                patch.object(kompetens, 'kravbrister', return_value=[]):
            post = df.specialist(SLUG, 'B001')
        self.assertEqual((post['utfall'], post['pass']), ('levererad', 'ds_typografi'))
        self.assertEqual(fangat['slug'], SLUG)
        self.assertFalse(fangat['webb'])
        self.assertIn('Skill', fangat['verktyg'])
        self.assertIn('impeccable/reference/typeset.md', fangat['prompt'], 'rollens kärna ur metodkartan')
        for falt in ('B001', SLUG, KANVAS, 'v01', 'Main.dc.html'):
            self.assertIn(falt, fangat['prompt'])
        self.assertIn('kanvas', fangat['prompt'])
        sk = self.u / SLUG / 'design' / 'svar' / 'B001'
        self.assertIn('Skalan är platt', (sk / 'SVAR.md').read_text())
        self.assertIn('märkt som sådan', (sk / 'SVAR.md').read_text())
        self.assertEqual(df.bestallning(SLUG, 'B001')['status'], 'levererad')

    def test_kritiken_far_inte_kallan_och_research_far_webben(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False)
        b = df.bestall(SLUG, 'kritik', 'v01', 'Main.dc.html', 'Kritik av versionen som en besökare ser den, före förklaringen')
        p = df.specialist_prompt(SLUG, b)
        self.assertNotIn('Versionens källa', p)
        self.assertIn('läs inte utförarens anteckningar', p)
        self.assertTrue(df.TYPER['referenser'][1])
        for typ, (pass_, _, _) in df.TYPER.items():
            self.assertTrue(kompetens.for_pass(pass_), '%s: passet %s har en roll i metodkartan' % (typ, pass_))


class E_Godkannande(Grund):
    def forbered(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första')

    def fyll(self, k):
        text = '# DESIGN\n\n' + '\n'.join('## %s\n\n%s\n' % (r, 'uppmätt: ett värde ur renderingen med tillräckligt mycket text för provet.')
                                          for r in df.OVERLAMNING_RUBRIKER)
        (k / 'DESIGN.md').write_text(text)

    def test_godkannandet_och_overlamningen(self):
        self.forbered()
        g = df.godkann(SLUG, 'v01', 'Main.dc.html')
        dom = skapande.agarens_senaste(SLUG, self.u)['dom']
        self.assertEqual((dom['kalla'], dom['beslut'], dom['tid']), ('ägaren', 'godkand', g['dom_tid']))
        self.assertEqual(dom['designfas']['version'], 'v01')
        ok, skal, _ = df.godkand_giltig(SLUG)
        self.assertFalse(ok)
        self.assertIn('överlämningen', skal)
        k = df.overlamna(SLUG)
        self.assertTrue(any('Designvärden' in b for b in df.overlamning_brister(SLUG)), 'mallen är inte ifylld')
        self.fyll(k)
        self.assertEqual(df.overlamning_brister(SLUG), [])
        ok, skal, _ = df.godkand_giltig(SLUG)
        self.assertTrue(ok, skal)
        for w in (390, 768, 1440):
            self.assertTrue((k / 'bilder' / ('Main-%d.png' % w)).is_file())
        # en ändrad bild i den godkända versionen gör godkännandet ogiltigt
        b = self.u / SLUG / 'design' / 'versioner' / 'v01' / 'bilder' / 'Main-390.png'
        orig = b.read_bytes()
        b.write_bytes(orig + b'x')
        self.assertFalse(df.godkand_giltig(SLUG)[0])
        b.write_bytes(orig)
        self.assertTrue(df.godkand_giltig(SLUG)[0])
        # en senare dom från ägaren tar över
        skapande.lagg_till_dom(SLUG, 'ägaren', 'ny_riktning', 'börja om', underlag=self.u, tid='2099-01-01T00:00:00Z')
        self.assertFalse(df.godkand_giltig(SLUG)[0])

    def test_bygget_jamfors_med_forlagan(self):
        self.forbered()
        df.godkann(SLUG, 'v01', 'Main.dc.html')
        self.fyll(df.overlamna(SLUG))
        insp = self.tmp / 'inspektion' / 'hem'
        insp.mkdir(parents=True)
        bilder = self.u / SLUG / 'design' / 'versioner' / 'v01' / 'bilder'
        for w in (390, 768, 1440):
            (insp / ('vy-%d-hela.png' % w)).write_bytes((bilder / ('Main-%d.png' % w)).read_bytes())
        text = df.jamfor_bygget(SLUG, insp, self.tmp / 'ut', dist_sha='a' * 64)
        d = json.loads((self.tmp / 'ut' / 'DESIGNJAMFORELSE.json').read_text())
        self.assertTrue(d['giltigt_godkannande'])
        self.assertEqual(d['bindning']['version'], 'v01')
        lika = [x for x in d['par'] if not x.get('fel')]
        self.assertEqual(len(lika), 3, d['par'])
        self.assertTrue(all((x.get('andel') or 0) == 0 for x in lika), 'samma bild ger ingen skillnad')
        meny = next(x for x in d['par'] if x['slag'] == 'menyn öppen')
        self.assertIn('byggets bild', meny['fel'], 'ett par som saknas står med skälet')
        self.assertIn('3 av 4 par', text)

    def test_godkannandet_kraver_bilderna(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False)
        with self.assertRaisesRegex(df.Fel, 'saknar bilder'):
            df.godkann(SLUG, 'v01', 'Main.dc.html')

    def test_kor_sh_tar_vid_fran_designgodkannandet(self):
        k = (ROOT / 'kor.sh').read_text()
        self.assertIn('designfas.godkand_giltig', k)
        self.assertIn('design/overlamning', k)
        s = (ROOT / '.claude' / 'skills' / 'bygg-sajt' / 'SKILL.md').read_text()
        self.assertIn('Claude Design', s)


class H_Band(Grund):
    """Produktionsbandet (ägarens uppdrag 2026-10-12, version 2): stationerna ur metodkartans tabell i processmodellens
    ordning, varje station med en metod, versioner som bär stationen, insatsen prövad i renderingen, överhoppade stationer
    med skäl, kritikens återgång, bandets läge per riktning och ett kvitto som redovisar utan att fälla."""

    def test_tabellen_i_litteraturens_ordning(self):
        st = df.stationer()
        ordning = list(st)
        self.assertEqual(ordning[:4], ['underlag', 'innehall', 'art', 'komposition'], 'content first, art direction före kompositionen')
        self.assertLess(ordning.index('komposition'), ordning.index('typografi'))
        self.assertLess(ordning.index('rorelse'), ordning.index('kritik'))
        self.assertIn('taste/SKILL.md', [df.filen(f) for f in st['art']['karna']])
        self.assertIn('ds_kritik', st['kritik']['pass'])
        self.assertIn('motion', df.station('rorelse')['mcp'])
        met = df.metoder()
        self.assertIn('process', met)
        for sid, x in st.items():
            self.assertTrue(x['metoder'] and all(m in met for m in x['metoder']), sid)
        self.assertTrue(any('W3C WAI' in r for r in df.station_rader(st['typografi'])), 'tillgängligheten är ett krav i stationen')
        inn = df.station_rader(st['innehall'])
        self.assertTrue(any('rubrikordningen' in r for r in inn), 'tillgängligheten i innehållet (granskningen mot WAI)')
        self.assertFalse(any('kontrast 4,5:1' in r for r in inn), 'de visuella kraven börjar vid art direction')
        with self.assertRaisesRegex(df.Fel, 'okänd station'):
            df.station('smak')

    def test_bandet_pa_en_riktning(self):
        self.duk()
        v1 = df.version(SLUG, self.las_tillbaka('f1', notes={'v01': {'x': 0, 'y': -200, 'text': 'v01 · Innehåll och struktur: sektionerna'}}),
                        '1791822460-0589', 'struktur med verkligt innehåll', station_='innehall', ritning='Main.dc.html')
        self.assertEqual((v1['station'], v1['notering'], v1['varningar']), ('innehall', 'v01 · Innehåll och struktur: sektionerna', []))
        self.assertEqual(v1['insats']['skal'], 'riktningens första version')
        ny = RITNING.replace('<h1>Provrubrik</h1>', '<h1 style="font-size:72px;line-height:1">Provrubrik i ny skala</h1>')
        v2 = df.version(SLUG, self.las_tillbaka('f2', ritning=ny), '1791822470-0600', 'typskalan', station_='typografi',
                        ritning='Main.dc.html', hoppade=['art=provets ritning prövar bara mekaniken, inget språk'])
        self.assertTrue(v2['insats']['synlig'], v2['insats'])
        self.assertEqual(v2['insats']['jamfort_med'], 'v01')
        self.assertTrue(any('notering' in x for x in v2['varningar']), 'utan anteckning på duken varnar versionen')
        band = df.band(SLUG)['Main.dc.html']
        lage = {x['station']: x['lage'] for x in band}
        self.assertEqual((lage['innehall'], lage['typografi'], lage['art']), ('gjord', 'gjord', 'hoppad'))
        self.assertEqual(lage['formular'], 'ej tillämplig', 'provritningen har inget formulär')
        self.assertEqual(lage['jamforelse'], 'ej tillämplig')
        self.assertEqual(lage['overlamning'], 'väntar')
        self.assertEqual(lage['kritik'], 'återstår')
        self.assertTrue(next(x for x in band if x['station'] == 'typografi')['synlig'])
        self.assertIn('band', df.status(SLUG))

    def test_kritik_och_tillganglighet_hoppas_inte_over(self):
        self.duk()
        for sid in df.ALLTID:
            with self.assertRaisesRegex(df.Fel, 'körs alltid'):
                df.version(SLUG, self.las_tillbaka('f-' + sid), '1791822460-0589', 'x', bilder=False, ritning='Main.dc.html',
                           hoppade=[sid + '=ett skäl som är långt nog att godtas'])
        with self.assertRaisesRegex(df.Fel, 'skäl'):
            df.version(SLUG, self.las_tillbaka('f-kort'), '1791822460-0589', 'x', bilder=False, ritning='Main.dc.html', hoppade=['polish=nej'])
        with self.assertRaisesRegex(df.Fel, 'ritning'):
            df.version(SLUG, self.las_tillbaka('f-utan'), '1791822460-0589', 'x', bilder=False, station_='art')

    def test_stationens_instruktion_och_bestallning(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False)
        (self.u / SLUG / 'design' / 'versioner' / 'v01' / 'BILDER.json').write_text(json.dumps(
            {'ritningar': {'Main.dc.html': {'bilder': {'390': {'fil': 'bilder/Main-390.png'}}}}}))
        t = df.station_brief(SLUG, 'typografi', 'Main.dc.html')
        for del_ in ('Station typografi', 'impeccable/reference/typeset.md', 'better-typography/SKILL.md (aktivera med Skill)',
                     'Stationens metod', '--station typografi --ritning Main.dc.html', 'v02'):
            self.assertIn(del_, t)
        b = df.bestall(SLUG, 'komponent', 'v01', 'Main.dc.html', 'En tjänstelista ur 21st som implementationsgrund för huvudsektionen')
        self.assertEqual(b['station'], 'komposition')
        with self.assertRaisesRegex(df.Fel, 'har inte passet'):
            df.bestall(SLUG, 'typografi', 'v01', 'Main.dc.html', 'En typografisk analys som är lång nog att godtas', station_='komposition')

    def test_kvittot_faller_inte_och_kritiken_kan_skicka_tillbaka(self):
        self.duk()
        df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första', bilder=False, station_='innehall', ritning='Main.dc.html')
        df.bestall(SLUG, 'kritik', 'v01', 'Main.dc.html', 'Kritik av versionen som en besökare ser den, före förklaringen')
        so = {'sammanfattning': 's', 'fynd': [], 'forslag': [], 'referenser': [], 'begransningar': [],
              'kompetens': {'aktiverade': [], 'lasta': [], 'valda': []}, 'atergang': {'till': 'komposition', 'skal': 'hierarkin bär inte'}}
        with patch.object(atelje, 'session', return_value={'session_id': '00000000-0000-4000-8000-000000000002', 'structured_output': so}), \
                patch.object(kompetens, 'kvitto', return_value={}), \
                patch.object(kompetens, 'kravbrister', return_value=['kärnan lästes inte hel']):
            post = df.specialist(SLUG, 'B001')
        self.assertEqual((post['utfall'], post['station'], post['ej_observerat']), ('levererad', 'kritik', ['kärnan lästes inte hel']))
        self.assertEqual(df.bestallning(SLUG, 'B001')['status'], 'levererad', 'oläst material fäller inte svaret')
        md = (self.u / SLUG / 'design' / 'svar' / 'B001' / 'SVAR.md').read_text()
        self.assertIn('fäller ingenting', md)
        self.assertIn('omtag av kompositionen', md)
        kritik = next(x for x in df.band(SLUG)['Main.dc.html'] if x['station'] == 'kritik')
        self.assertEqual((kritik['lage'], kritik['atergang']['till']), ('svar', 'komposition'))


class I_Inventering(unittest.TestCase):
    """Inventeringen 2026-10-12 (ordagrant i underlag/uppdrag/PROMPT-Nortropic-Full-inventering-formagor-20261012.md, med
    ägarens tillägg om automatik): radutdrag i stationerna, flödena härledda ur tabellerna, en plats eller ett skäl för
    varje fil, inventera --placera och bandets filer i metodlåset."""

    def test_radutdrag_i_stationen(self):
        import metod
        art = df.station('art')
        # taste som rubrikutdrag, ett per avsnitt (§0, §1, §2.B, §7): ett radutdrag fällde nästa uppdatering (valideringen 2026-10-12)
        tok = [f for f in art['karna'] if df.filen(f) == 'taste/SKILL.md']
        self.assertEqual(len(tok), 4, tok)
        self.assertTrue(all(' # ' in f and len(metod.utdrag(f)['intervall']) == 1 for f in tok), 'taste avgränsad till sina avsnitt')
        self.assertTrue(any('läs bara utdraget' in r for r in df.station_rader(art)))
        trasig = df.KARTA.read_text(encoding='utf-8').replace('`taste/SKILL.md # 7. DIAL DEFINITIONS (Technical Reference)`',
                                                              '`taste/SKILL.md # 7. FINNS INTE`', 1)
        self.assertTrue(any('7. FINNS INTE' in f and 'finns inte' in f for f in df.karta_prova(trasig)), 'ett utdrag med en rubrik som saknas fälls')
        trasig = df.KARTA.read_text(encoding='utf-8').replace('`refero-design/references/visual-workflow.md rad 81–105`',
                                                              '`refero-design/references/visual-workflow.md rad 81–99999`', 1)
        self.assertTrue(any('rad 81–99999' in f for f in df.karta_prova(trasig)), 'ett utdrag utanför filen fälls')

    def test_floden_harleds_och_ett_fel_falls(self):
        h = df.harledda_floden()
        self.assertTrue({'band', 'helbygge'} <= h['skill:frontend-design'], h['skill:frontend-design'])
        self.assertIn('research', h['skill:refero-design'])
        self.assertIn('overlamning', h['skill:design-system'])
        text = df.KARTA.read_text(encoding='utf-8')
        rad = next(r for r in text.splitlines() if r.startswith('skill:frontend-design |'))
        utan = text.replace(rad, rad.replace('helbygge, ', '', 1).replace(', helbygge', '', 1), 1)
        self.assertTrue(any('skill:frontend-design: raden säger flödena' in f for f in df.karta_prova(utan)))
        okand = text.replace(rad, rad.replace('flöden: ', 'flöden: smak, ', 1), 1)
        self.assertTrue(any('okänt flöde smak' in f for f in df.karta_prova(okand)))

    def test_varje_fil_har_en_plats_eller_ett_skal(self):
        text = df.KARTA.read_text(encoding='utf-8')
        self.assertEqual(df.karta_prova(text), [])
        rad = next(r for r in text.splitlines() if r.startswith('fil:design/* |'))
        fel = df.karta_prova(text.replace(rad + '\n', '', 1))
        self.assertTrue(any(f.startswith('filen design/') for f in fel), fel[:3])
        med_station = text.replace(rad, rad.replace('| skäl: ', '| stationer: polish; skäl: ', 1), 1)
        self.assertTrue(any('en filrad har inga egna stationer' in f for f in df.karta_prova(med_station)))
        tom = text.replace(rad, rad + '\nfil:finns-inte/* | x | ingen | skäl: en rad utan fil, för provet | ingen uppgift', 1)
        self.assertTrue(any('fil:finns-inte/* matchar ingen fil' in f for f in df.karta_prova(tom)))
        via = text.replace(rad, rad + '\nfil:slides/* | x | ingen | flöden: helbygge; en plats som skillen inte har | prov', 1)
        self.assertTrue(any('fil:slides/*: flödet helbygge når filen bara genom skillen' in f for f in df.karta_prova(via)))

    def test_inventera_placerar_och_kartan_haller(self):
        text = df.KARTA.read_text(encoding='utf-8')
        rapport, ny = df.inventera(placera=True, text=text, idag='2026-10-12')
        self.assertIsNone(ny, rapport)
        rad_skill = next(r for r in text.splitlines() if r.startswith('skill:canvas-design |'))
        rad_fil = next(r for r in text.splitlines() if r.startswith('fil:design/* |'))
        gles = text.replace(rad_skill + '\n', '', 1).replace(rad_fil + '\n', '', 1)
        gles = gles.replace('stationer: art; flöden: band, specialistpass; D5, D8 kärna', 'stationer: polish; D5, D8 kärna', 1)
        self.assertTrue(df.karta_prova(gles))
        rapport, ny = df.inventera(placera=True, text=gles, idag='2026-10-12')
        self.assertIsNotNone(ny)
        self.assertEqual(df.karta_prova(ny), [], 'kartan håller efter placeringen')
        self.assertTrue(any(r.startswith('ny rad: skill:canvas-design') for r in rapport), rapport[:5])
        self.assertTrue(any(r.startswith('ny rad: fil:design/') for r in rapport), rapport[:5])
        self.assertTrue(any(r.startswith('väntar på en verklig placering') and 'skill:canvas-design' in r for r in rapport))
        ny_rad = next(r for r in ny.splitlines() if r.startswith('skill:canvas-design |'))
        self.assertIn('stationer: komposition; flöden: band, specialistpass; skäl: automatiskt placerad 2026-10-12', ny_rad)
        self.assertIn('skill:taste | Leonxlnx/taste-skill | båda | stationer: art; flöden: band, specialistpass;', ny)

    def test_metodlaset_och_underhallet_omfattar_bandet(self):
        import metod
        import underhall
        fel, kallor = metod.prova()
        self.assertEqual(fel, [])
        self.assertIn('modern-web-guidance/guides/css/fluid-scaling.md', kallor, 'en fil som bara bandet namnger')
        import inspect
        self.assertIn('designfas.stationer()', inspect.getsource(underhall.utdrag_som_andras), 'bandets radutdrag skyddas vid intaget')
        self.assertIn("'inventera', '--placera'", inspect.getsource(underhall.prova_metod_i))
        self.assertIn("'inventera', '--placera'", inspect.getsource(underhall.ta_in_skill))

    def test_atergang_till_underlaget(self):
        self.assertIn('underlag', df.SVAR_SCHEMA['properties']['atergang']['properties']['till']['enum'])
        md = df.svar_md({'id': 'B001', 'typ': 'kritik', 'version': 'v01', 'ritning': 'Main.dc.html', 'station': 'kritik',
                         'projekt': SLUG, 'uppgift': 'kritik av helheten'},
                        {'svar': {'atergang': {'till': 'underlag', 'skal': 'förebilderna bär inte'}}})
        self.assertIn('omtag av underlaget', md)


class F_Karta(unittest.TestCase):
    def test_kartan_har_en_rad_per_kompetens(self):
        self.assertEqual(df.karta_prova(), [])

    def test_raden_tabellen_och_metoderna_sager_samma_sak(self):
        text = df.KARTA.read_text(encoding='utf-8')
        fel_ = df.karta_prova(text.replace('skill:taste | Leonxlnx/taste-skill | båda | stationer: art;',
                                           'skill:taste | Leonxlnx/taste-skill | båda | stationer: polish;'))
        self.assertTrue(any('skill:taste' in x and 'tabellen' in x for x in fel_), fel_)
        utan = text.replace('skill:slides | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl:', 'skill:slides | nextlevelbuilder/ui-ux-pro-max-skill | ingen | ')
        self.assertTrue(any('skill:slides har varken en station' in x for x in df.karta_prova(utan)))
        ensam = text.replace('| `detalj`, `varv`, `wai` | ny version med före och efter |', '| `varv`, `wai` | ny version med före och efter |')
        self.assertNotEqual(ensam, text, 'polishens metodcell finns')
        self.assertTrue(any('metoden detalj har ingen station' in x for x in df.karta_prova(ensam)))

    def test_en_saknad_skill_falls(self):
        text = df.KARTA.read_text(encoding='utf-8')
        m = df.KARTBLOCK.search(text)
        rad = next(r for r in m.group('rader').splitlines() if r.startswith('skill:taste |'))
        self.assertIn('skillen taste saknar rad', '\n'.join(df.karta_prova(text.replace(rad + '\n', ''))))


class G_Start(Grund):
    def test_startkommandot(self):
        df.ny(SLUG, KANVAS)
        args = df.start(SLUG, skriv_bara=True)
        self.assertIn('--strict-mcp-config', args)
        self.assertEqual(args[-1], '/designfas %s' % SLUG)
        inst = json.loads(Path(args[args.index('--settings') + 1]).read_text())
        self.assertIn('kundvakt.py', json.dumps(inst['hooks']))
        self.assertIn('Bash(*designfas.py godkann*)', inst['permissions']['deny'])
        self.assertTrue(any(a.endswith('mobbin.json') for a in args))


if __name__ == '__main__':
    unittest.main(verbosity=1)
