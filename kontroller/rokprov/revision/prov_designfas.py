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

    def las_tillbaka(self, namn='fran', ritning=RITNING, extra=None):
        p = self.tmp / namn / 'project'
        p.mkdir(parents=True)
        boards = {'Main.dc.html': {'x': 0, 'y': 0, 'w': 1440, 'h': 900, 'expand': 'fill', 'title': 'Riktning A'}}
        boards.update(extra or {})
        (p / 'canvas.json').write_text(json.dumps({'v': 3, 'title': 'Prov', 'boards': boards, 'order': list(boards)}))
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
        post = df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'första riktningen')
        vk = self.u / SLUG / 'design' / 'versioner' / 'v01'
        self.assertEqual(post['version'], 'v01')
        self.assertEqual((vk / 'kanvas' / 'Main.dc.html').read_text(), RITNING)
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


class F_Karta(unittest.TestCase):
    def test_kartan_har_en_rad_per_kompetens(self):
        self.assertEqual(df.karta_prova(), [])

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
