#!/usr/bin/env python3
"""Designfasens band (ägarens beslut 2026-10-13 i BESLUT.md: formgivningen lokalt i Astro; läget duk i Claude Design
pausat): mekaniken genom de verkliga ingångarna, med attrapper bara för det externa (bygget med Astro, Design-typens
körmiljö, sessionerna, kvittot och impeccables motor). Inga modeller och inget nät.

- A: med en designfas ger kandidatflödet researchen, planen och planprövningen och lämnar sedan riktningarna till bandet
  (steget band, projekten förberedda, riktningarna registrerade, inga skapare); NWP_KANDIDAT_STOPP_EFTER=forskning
  stannar efter researchen utan designfas; en dom eller ett uppdrag på en riktning i bandet nekas (en skrivare).
- B: läget astro: en version ur riktningens projekt med källan, den byggda sidan, startsidan och undersidan renderade
  med den riktiga rendera.mjs (lata bilder laddade, srcset utan falskt larm, katalogen ger index.html), kontrollerna och
  insatsen mot förra versionen; läget duk prövas kvar med NWP_DESIGNLAGE=duk och är annars pausat.
- C: beställning → svar → införd i en ny version, med projekt, duk, version, ritning, uppgift, material och resultat.
- D: specialistpasset: rollens kompetensblock och verktyg, svaret i schemat, kvittot ur transkriptet; kritiken får inte
  källan; jämförelsen ser alla riktningarnas senaste version.
- E: ägarens godkännande i domloggen, bundet till versionens filer och bilder; överlämningen krävs komplett (med kalla/
  i läget astro); installationen lägger källan, package.json, låset och .npmrc i sajten; kor.sh tar vid.
- F: kompetensplaceringen (designfas-karta) har en rad per skill, tjänst och specialistpass.
- G: startkommandot: kundvakten, flödets tjänster med --strict-mcp-config och godkännandet nekat för sessionen.
- H: produktionsbandet på riktningen k01: stationerna i processmodellens ordning med metod, versioner med stationen,
  hoppade stationer, kritikens återgång, bandets läge, stationens instruktion före och efter riktningens första version.
- J: artefakten: paketet per riktning med relativa vägar, utan CSP-meta, FILER.json och publiceringen i ARTEFAKT.json.
- K, L: paketen följer riktningen till helbygget (låsets rot, npm-registret); versionsnumret reserveras atomiskt.
- M: drivaren (ägarens beslut 2026-10-13, "Autonomous to build"): från tre riktningar till en startad byggbegäran med en
  attrapp för claude; publiceringen anropas aldrig, ett avbrott tas upp, och ägarens val går före jämförelsens.
"""
import contextlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import types
import unittest
import zlib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister  # noqa: E402
import atelje  # noqa: E402
import designfas as df  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import prototyp  # noqa: E402
import skapande  # noqa: E402

SLUG = 'designfas-prov'
KANVAS = 'https://claude.ai/artifact/ProvKanvas0123456789'
ARTEFAKTEN = 'https://claude.ai/artifact/ProvArtefakt0123456789'
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


def png(w, h, farg=(40, 90, 160)):
    """En riktig PNG i bredden w, så att renderingen kan pröva filens bredd mot den visade."""
    def bit(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    rader = (b'\x00' + bytes(farg) * w) * h
    return (b'\x89PNG\r\n\x1a\n' + bit(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + bit(b'IDAT', zlib.compress(rader))
            + bit(b'IEND', b''))


# Astro-projektets startsida i attrappen: index.astro är sidans kropp, och bygget (bygg_attrapp) lägger den i dist/
# med Astros form: absoluta /_astro/-vägar, en srcset-bild med täthet 2, en lat bild långt ner, sajtens CSP-meta och ett
# skript som frågar servern efter katalogen /om/ (en katalog ger sin index.html)
SNURR = '<div class="snurr" style="width:24px;height:24px;background:#2a5;animation:snurra 1.5s linear infinite"></div>'
STARTSIDA = ('<h1 id="r">Provrubrik</h1>' + SNURR +
             '<button type="button" aria-label="Pausa rörelsen" style="min-height:44px;min-width:44px">Paus</button>')
DIST = '''<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="content-security-policy" content="default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'">
<title>Provverkstan</title><link rel="stylesheet" href="/_astro/x.css"></head>
<body><header><a href="/">Provverkstan</a> <a href="/om/">Om verkstaden</a></header>
<main>__KROPP__
<img src="/_astro/bild-600.png" srcset="/_astro/bild-600.png 600w" sizes="300px" width="300" height="4" alt="Verkstaden" style="width:300px;height:auto;display:block">
<p style="margin-top:6000px">Längre ner</p>
<img src="/_astro/lat.png" loading="lazy" width="200" height="4" alt="Ett verktyg" style="width:200px;height:auto;display:block">
</main>
<script>fetch('/om/').then(function (r) { return r.text().then(function () { document.getElementById('r').textContent += ' ' + r.status; }); });</script>
</body></html>
'''
OM = '<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Om</title><link rel="stylesheet" href="/_astro/x.css"></head><body><main><h1>Om verkstaden</h1></main></body></html>'
CSS = ('@font-face{font-family:Prov;src:url(/_astro/fonts/prov.woff2) format("woff2")} body{margin:0;padding:16px;font-family:system-ui}'
       '@keyframes snurra{to{transform:rotate(360deg)}}')


def bygg_attrapp(sajt):
    """Attrappen av bygget (designfas.bygg): dist/ ur projektets src/pages/index.astro, med Astros form."""
    sajt = Path(sajt)
    d = sajt / 'dist'
    shutil.rmtree(d, ignore_errors=True)
    (d / '_astro' / 'fonts').mkdir(parents=True)
    (d / 'tack').mkdir()
    (d / 'index.html').write_text(DIST.replace('__KROPP__', (sajt / 'src' / 'pages' / 'index.astro').read_text()))
    if (sajt / 'src' / 'pages' / 'om').is_dir():  # en undersida bara när projektet har den
        (d / 'om').mkdir()
        (d / 'om' / 'index.html').write_text(OM)
    if (sajt / 'src' / 'pages' / 'tjänster').is_dir():  # ett svenskt sidnamn (granskningens fynd 4)
        (d / 'tjänster').mkdir()
        (d / 'tjänster' / 'index.html').write_text(OM.replace('Om verkstaden', 'Våra tjänster'))
    (d / 'tack' / 'index.html').write_text(OM.replace('Om verkstaden', 'Tack'))
    (d / '404.html').write_text(OM.replace('Om verkstaden', 'Hittas inte'))
    (d / '_astro' / 'x.css').write_text(CSS)
    (d / '_astro' / 'fonts' / 'prov.woff2').write_bytes(b'wOF2' + b'\x00' * 60)
    (d / '_astro' / 'bild-600.png').write_bytes(png(600, 4))
    (d / '_astro' / 'lat.png').write_bytes(png(400, 4, (200, 120, 40)))
    return 0, 'byggt (attrapp)'


def motor_attrapp(tmp):
    """impeccables motor som en attrapp utan fynd (detektor.motor läser IMPECCABLE_BIN)."""
    m = Path(tmp) / 'motor' / 'impeccable'
    m.parent.mkdir(parents=True, exist_ok=True)
    m.write_text('#!%s\nprint("[]")\n' % sys.executable)
    m.chmod(0o755)
    return m


class Grund(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'designfasens prov'))).resolve()
        self.u, self.k = self.tmp / 'underlag', self.tmp / 'kunder'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.u, KUNDER=self.k))
        self.stack.enter_context(patch.object(df, 'UNDERLAG', self.u))
        self.stack.enter_context(patch.object(skapande, 'UNDERLAG', self.u))
        self.stack.enter_context(patch.dict(os.environ))
        os.environ.pop('NWP_DESIGNLAGE', None)
        os.environ['NWP_DESIGNFAS_AUTONOM'] = 'av'  # drivaren startas bara av proven som prövar den (M_Drivaren)
        (self.u / SLUG / 'bilder').mkdir(parents=True)
        (self.u / SLUG / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provverkstan', 'fiktiv': True}))
        (self.u / SLUG / 'BRIEF.md').write_text('# Brief\n')
        self.bild = self.u / SLUG / 'bilder' / 'verkstad.png'
        self.bild.write_bytes(PNG)

    # ---- läget duk, pausat: prövas med NWP_DESIGNLAGE=duk ----
    def duk(self, rel='prov-release-1'):
        os.environ['NWP_DESIGNLAGE'] = 'duk'
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

    # ---- läget astro: riktningarna som Astro-projekt i kunder/<slug>/kandidater/kNN/sajt ----
    def projekt(self, kid, startsida=STARTSIDA, las=True):
        p = self.k / SLUG / 'kandidater' / kid / 'sajt'
        (p / 'src' / 'pages').mkdir(parents=True, exist_ok=True)
        (p / 'public').mkdir(exist_ok=True)
        (p / 'package.json').write_text(json.dumps({'name': 'prov-%s' % kid, 'private': True}))
        if las:
            (p / 'package-lock.json').write_text(json.dumps({'name': 'prov-%s' % kid, 'lockfileVersion': 3, 'packages': {}}))
        (p / 'astro.config.mjs').write_text('export default {};\n')
        (p / 'src' / 'pages' / 'index.astro').write_text(startsida)
        (p / 'src' / 'pages' / 'om').mkdir(exist_ok=True)
        (p / 'src' / 'pages' / 'om' / 'index.astro').write_text('<h1>Om verkstaden</h1>')
        (p / 'public' / 'robots.txt').write_text('User-agent: *\n')
        (p / 'RIKTNING.md').write_text('# Riktning %s\n\nReferenslåset och språket står här.\n' % kid)
        return p

    def astro(self, ids=('k01',)):
        df.ny(SLUG)
        for kid in ids:
            self.projekt(kid)
        df.riktningar(SLUG, list(ids), titlar={k: 'Riktningen %s' % k for k in ids})
        self.stack.enter_context(patch.object(df, 'bygg', side_effect=bygg_attrapp))

    def fejkbilder(self, v, sidor=('index.html',)):
        """Bilder och BILDER.json för en version som sparats utan rendering (bilder=False)."""
        vk = self.u / SLUG / 'design' / 'versioner' / v
        (vk / 'bilder').mkdir(parents=True, exist_ok=True)
        rit = {}
        for s in sidor:
            st = df.stam(s)
            rit[s] = {'bilder': {}}
            for w in (390, 768, 1440):
                (vk / 'bilder' / ('%s-%d.png' % (st, w))).write_bytes(PNG)
                rit[s]['bilder'][str(w)] = {'fil': 'bilder/%s-%d.png' % (st, w)}
        (vk / 'BILDER.json').write_text(json.dumps({'ritningar': rit}))
        return vk


class A_Bandet(Grund):
    """Spärren är borta (beslutet 2026-10-13, punkt 1): med en designfas går kandidatflödet till och med plan och
    projekt, och designfas.py är därefter enda skrivaren av riktningarna."""

    def sajt(self):
        s = self.k / SLUG / 'sajt'
        (s / 'src' / 'pages').mkdir(parents=True)
        (s / 'node_modules').mkdir()
        (s / 'package.json').write_text(json.dumps({'name': 'sajt', 'private': True}))
        (s / 'package-lock.json').write_text('{}')
        (s / 'astro.config.mjs').write_text('export default {};\n')
        (s / 'src' / 'pages' / 'index.astro').write_text('<h1>Mallen</h1>')
        return s

    def kor(self, plan_finns=False, stopp=''):
        """Kandidatflödet med attrapper för researchen, planen och planprövningen; skaparna får aldrig starta."""
        anrop, st, ids = [], {}, ['k01', 'k02', 'k03']
        planerad = {'ja': plan_finns}

        def planera(slug, n, lage=None):
            anrop.append('planera')
            planerad['ja'] = True
            for kid in ids:
                kd.satt_status(slug, kid, 'planerad', 'uppdraget skrivet', titel='Titel %s' % kid)
        if plan_finns:
            for kid in ids:
                kd.satt_status(SLUG, kid, 'planerad', 'uppdraget skrivet', titel='Titel %s' % kid)
        provad = {'ja': False}

        def planprovning(slug, bara=None, _foregaende=None):
            anrop.append('planprovning')
            provad['ja'] = True
            return {}
        import urval
        with patch.multiple(kd, STOPP_EFTER=stopp, leverera_metod=lambda _: {}, korlage=lambda *a: 'skiss', arkivera_projekt=lambda *a: None,
                            forska=lambda slug, n, skiss=False: anrop.append('forska') or {'nytt': [], 'fel': None},
                            planera=planera, lista=lambda slug: list(ids) if planerad['ja'] else [],
                            planprovning_behov=lambda slug, ids_: [] if provad['ja'] else list(ids_), planprovning=planprovning,
                            referensvarning=lambda *a, **k: (False, []), material_behov=lambda *a, **k: [],
                            kor_pool=lambda *a, **k: self.fail('skaparna startade'), skissa=lambda *a, **k: self.fail('skissen startade')), \
                patch.object(urval, 'vid_start', return_value={}):
            ut = kd.kor(SLUG, st, lambda: None, n=3)
        return ut, anrop, st, ids

    def test_designfasen_ger_plan_och_projekt_och_lamnar_till_bandet(self):
        self.sajt()
        df.ny(SLUG)
        ut, anrop, st, ids = self.kor()
        self.assertEqual(ut, [])
        self.assertEqual(anrop, ['forska', 'planera', 'planprovning'], 'researchen, planen och planprövningen körs; inga skapare')
        self.assertEqual(st['steg'], 'band')
        self.assertIn('./design.sh %s' % SLUG, st['skal'])
        rk = json.loads((self.u / SLUG / 'design' / 'DESIGNFAS.json').read_text())['riktningar']
        self.assertEqual(sorted(rk), ids)
        for kid in ids:
            p = self.k / SLUG / 'kandidater' / kid / 'sajt'
            self.assertTrue((p / 'package.json').is_file() and (p / 'node_modules').is_symlink(), 'forbered_projekt gav projektet')
            self.assertEqual(df.projekt(SLUG, kid), p)
            self.assertEqual(rk[kid]['titel'], 'Titel %s' % kid)
            s = kd.las_status(SLUG, kid)
            self.assertEqual(s['status'], 'planerad')
            self.assertIn('i bandet', s['skal'])
        self.assertEqual(df.status(SLUG)['band']['k01'][-1], {'station': 'artefakt', 'lage': 'inte publicerad', 'url': None,
                                                               'version': None, 'tid': None})
        # fler riktningar på ägarens begäran, två åt gången: projekten ur sajten, i bandet
        df.riktningar(SLUG, ['k04', 'k05'], nya=True)
        for kid in ('k04', 'k05'):
            self.assertTrue((self.k / SLUG / 'kandidater' / kid / 'sajt' / 'node_modules').is_symlink())
            self.assertIn('i bandet', kd.las_status(SLUG, kid)['skal'])
        self.assertEqual(list(df.band(SLUG)), ['k01', 'k02', 'k03', 'k04', 'k05'])
        with self.assertRaisesRegex(df.Fel, 'finns redan'):
            df.riktningar(SLUG, ['k04'], nya=True)

    def test_en_plan_fran_fore_designfasen_lamnas_till_bandet(self):
        self.sajt()
        df.ny(SLUG)
        _, anrop, st, _ = self.kor(plan_finns=True)
        self.assertEqual((anrop, st['steg']), (['planprovning'], 'band'))

    def test_stoppunkten_forskning_utan_designfas(self):
        _, anrop, st, _ = self.kor(stopp='forskning')
        self.assertEqual((anrop, st['steg']), (['forska'], 'forskad'))
        self.assertIsNone(atelje.fortsatt_nekas({'steg': 'forskad'}, SLUG), 'utan designfas tar --fortsatt vid i planeringen')
        df.ny(SLUG)
        self.assertIsNone(atelje.fortsatt_nekas({'steg': 'forskad'}, SLUG), 'spärren är borta: forskad är bara stoppunkten')
        self.assertIn('enda skrivaren', atelje.fortsatt_nekas({'steg': 'band'}, SLUG))

    def test_duken_pausad_stoppar_kandidatflodet_fore_researchen(self):
        os.environ['NWP_DESIGNLAGE'] = 'duk'
        df.ny(SLUG, KANVAS)
        del os.environ['NWP_DESIGNLAGE']
        with self.assertRaisesRegex(RuntimeError, 'pausat'):
            self.kor()

    def test_ateljens_sparr_ar_borta(self):
        import inspect
        self.assertNotIn('designfas.aktiv(slug, UNDERLAG)', inspect.getsource(atelje.arbeta), 'kandidatflödet nekas inte av en aktiv designfas')

    def test_en_ny_korning_nekas_medan_riktningarna_ar_i_bandet(self):
        """--om, --ny-riktning, --valda, --putsa och en ny körning utan flagga nekas i starten, innan statusen skrivs och
        innan något arkiveras, när körningen står i steget band eller designfasen har riktningar i arbete
        (granskningens fynd 5: --om flyttade annars riktningarnas projekt till arkivet medan utföraren arbetade i dem).
        Provet kör vägen genom atelje.main; arbetaren och en ny sajt får aldrig startas."""
        import io
        self.sajt()
        for n in ('RESEARCH.md', 'TEXTUNDERLAG.md'):
            (self.u / SLUG / n).write_text('# %s\n' % n)
        df.ny(SLUG)
        p = self.projekt('k01')
        df.riktningar(SLUG, ['k01'])
        kd.satt_status(SLUG, 'k01', 'planerad', 'i bandet')
        status = self.u / SLUG / 'atelje' / 'STATUS.json'
        for steg in ('band', 'klar_for_bedomning'):  # också när statusen säger annat har designfasen riktningar i arbete
            status.write_text(json.dumps({'slug': SLUG, 'steg': steg, 'kandidatflode': True, 'klar': '2026-10-13T08:00:00Z',
                                          'kandidater': {'k01': 'planerad'}}))
            for flagga in ('--om', '--ny-riktning', '--valda', '--putsa', None):
                ut = io.StringIO()
                with patch.object(atelje.subprocess, 'Popen', side_effect=AssertionError('arbetaren startades')), \
                        patch.object(atelje, 'ny_sajt', side_effect=AssertionError('sajten gjordes om')), contextlib.redirect_stdout(ut):
                    rc = atelje.main([SLUG] + ([flagga] if flagga else []) + ['--vanta', '0'])
                self.assertEqual(rc, 2, (steg, flagga, ut.getvalue()[-300:]))
                self.assertIn('enda skrivaren', ut.getvalue(), (steg, flagga))
                self.assertEqual(json.loads(status.read_text())['steg'], steg, 'statusen skrevs inte om')
                self.assertTrue((p / 'src' / 'pages' / 'index.astro').is_file(), 'riktningens projekt står kvar')

    def test_dom_och_uppdrag_pa_en_riktning_i_bandet_nekas(self):
        """En skrivare per riktning: en dom eller ett uppdrag i Code på en riktning i bandet nekas, med hänvisning till
        designfasen; prototyp.py stannar och säger vem som skriver."""
        df.ny(SLUG)
        for kid in ('k01', 'k02'):
            kd.satt_status(SLUG, kid, 'planerad', 'i bandet', version='v' * 12)
        (self.u / SLUG / 'atelje' / 'STATUS.json').write_text(json.dumps({'slug': SLUG, 'steg': 'band', 'kandidatflode': True, 'klar': '2026-10-13T08:00:00Z',
                                                                          'kandidater': {'k01': 'planerad', 'k02': 'planerad'}}))
        for beslut, extra in (('valj', {}), ('uppdrag', {'uppdrag': {'typ': 'ratta', 'resultat': 'r', 'omfattning': 'o', 'bevara': 'b'}}),
                              ('jamfor', {})):
            with self.assertRaisesRegex(ValueError, 'enda skrivaren'):
                atelje.doma(SLUG, 'ägaren', beslut, 'en dom i provet', kandidater=[{'id': 'k01', 'version': 'v' * 12}], **extra)
        self.assertFalse((self.u / SLUG / skapande.DOMLOGG).exists(), 'ingen dom skrevs')
        vald, skal = prototyp.lage(SLUG)
        self.assertEqual(vald, 'stopp')
        self.assertIn('enda skrivaren', skal)


class B_Version(Grund):
    def test_astro_version_byggs_renderas_och_provas(self):
        """Läget astro: en version ur riktningens projekt med källan (kalla/), den byggda sidan (sida/), startsidan och
        undersidan renderade med den riktiga rendera.mjs, kontrollerna och insatsen mot förra versionen av riktningen."""
        self.astro()
        (df.projekt(SLUG, 'k01') / 'src' / 'pages' / 'tjänster').mkdir()
        (df.projekt(SLUG, 'k01') / 'src' / 'pages' / 'tjänster' / 'index.astro').write_text('<h1>Våra tjänster</h1>')
        with patch.dict(os.environ, IMPECCABLE_BIN=str(motor_attrapp(self.tmp))):
            v1 = df.version(SLUG, None, None, 'strukturen med det verkliga innehållet', station_='innehall', ritning='k01')
            p = df.projekt(SLUG, 'k01')
            (p / 'src' / 'pages' / 'index.astro').write_text('<h1 id="r" style="font-size:72px;line-height:1">Provrubrik i ny skala</h1>' + SNURR)
            for u in ('om', 'tjänster'):  # bara startsidan i v2: renderingen tar en sida i stället för tre
                shutil.rmtree(p / 'src' / 'pages' / u)
            v2 = df.version(SLUG, None, None, 'typskalan', station_='typografi', ritning='k01',
                            hoppade=['art=provets riktning prövar bara mekaniken, inget språk'])
        vk = self.u / SLUG / 'design' / 'versioner' / 'v01'
        self.assertEqual((v1['version'], v1['lage'], v1['ritning'], v1['station']), ('v01', 'astro', 'k01', 'innehall'))
        self.assertEqual(v1['sidor'], ['index.html', 'om/index.html', 'tjänster/index.html'], 'startsidan först, mallens sidor (tack, 404) inte')
        for n in ('src/pages/index.astro', 'package.json', 'package-lock.json', 'astro.config.mjs', 'RIKTNING.md', 'public/robots.txt'):
            self.assertEqual(v1['filer'][n], df.sha(vk / 'kalla' / n), n)
        self.assertEqual(v1['las'], 'projektets')
        self.assertEqual(v1['varningar'], [])
        self.assertTrue((vk / 'sida' / 'index.html').is_file() and (vk / 'sida' / '_astro' / 'x.css').is_file(), 'dist i sida/')
        self.assertEqual(v1['rendering']['slutkod'], 0, v1['rendering'])
        b = json.loads((vk / 'BILDER.json').read_text())
        self.assertIn('Astro', b['kalla'])
        self.assertIn('inte en skärmbild', b['kalla'])
        self.assertNotIn('runtime', b, 'ingen körmiljö i läget astro')
        r = b['ritningar']['index.html']
        for w in ('390', '768', '1440'):
            self.assertTrue((vk / r['bilder'][w]['fil']).is_file(), w)
            self.assertEqual(r['bilder'][w]['fil'], 'bilder/index-%s.png' % w)
        self.assertTrue((vk / 'bilder' / 'om-index-390.png').is_file(), 'undersidans stam: om/index.html → om-index')
        # ett svenskt sidnamn renderas, med ett säkert filnamn för bilderna (granskningens fynd 4)
        tj = b['ritningar']['tjänster/index.html']
        self.assertEqual(tj['bilder']['390']['fil'], 'bilder/%s-390.png' % df.stam('tjänster/index.html'))
        self.assertTrue((vk / tj['bilder']['390']['fil']).is_file())
        self.assertEqual(tj['bilder']['390']['h1'], ['Våra tjänster'])
        self.assertTrue((vk / 'kontroll' / 'detektor' / ('%s-390.json' % df.sakert('tjänster-index.html'))).is_file())
        self.assertEqual(r['bilder']['390']['h1'], ['Provrubrik 200'], 'katalogen /om/ ger sin index.html')
        self.assertEqual(r['fel'], [], 'den lata bilden långt ner laddades före mätningen')
        lat = next(x for x in r['matt']['390']['bildstorlekar'] if x['src'].endswith('lat.png'))
        self.assertTrue(lat['lazy'], 'loading=lazy redovisas fortfarande')
        srcset = next(x for x in r['matt']['390']['bildstorlekar'] if x['src'].endswith('bild-600.png'))
        self.assertEqual((srcset['naturlig'], srcset['css_bredd'], srcset['kvot']), (600, 300, 1.0), srcset)
        self.assertFalse([v for v in r['varningar'] if 'suddig' in v], 'srcset-bilden med täthet 2 är inte suddig')
        # rörelse som pågår mer än 5 s är tillåten när den kan pausas (stationen detaljer, ägarens beslut 2026-10-13)
        self.assertEqual(r['stillhet']['390']['paus'], ['Pausa rörelsen'])
        self.assertFalse([v for v in r['varningar'] if 'paus- eller stoppkontroll' in v], 'en synlig pausknapp: ingen varning')
        r2 = json.loads((self.u / SLUG / 'design' / 'versioner' / 'v02' / 'BILDER.json').read_text())['ritningar']['index.html']
        self.assertTrue([v for v in r2['varningar'] if 'paus- eller stoppkontroll' in v], 'rörelsen utan pausknapp varnas')
        self.assertIn('axe', b['kontroll'])
        self.assertTrue(all(x.get('slutkod') == 0 for x in b['kontroll']['detektor'].values()), b['kontroll']['detektor'])
        self.assertTrue((vk / 'kontroll' / 'detektor' / 'om-index.html-390.json').is_file(), 'undersidans detektorfil i samma katalog')
        self.assertEqual(v1['insats']['skal'], 'riktningens första version')
        self.assertTrue(v2['insats']['synlig'], v2['insats'])
        self.assertEqual(v2['insats']['jamfort_med'], 'v01')
        self.assertEqual(v2['sidor'], ['index.html'], 'undersidan togs bort i projektet')
        self.assertTrue(v2['insats']['bredder']['390']['fore'].endswith('versioner/v01/bilder/index-390.png'), 'bilderna före och efter')
        self.assertEqual(v2['hoppade'], {'art': 'provets riktning prövar bara mekaniken, inget språk'})
        rader = [json.loads(x) for x in (self.u / SLUG / 'design' / 'VERSIONER.jsonl').read_text().splitlines()]
        self.assertEqual([(x['version'], x['ritning'], x['station']) for x in rader], [('v01', 'k01', 'innehall'), ('v02', 'k01', 'typografi')])

    def test_bildernas_stam_ar_saker_och_krockar_inte(self):
        self.assertEqual((df.stam('index.html'), df.stam('om/index.html'), df.stam('Main.dc.html')), ('index', 'om-index', 'Main'))
        for namn in ('tjänster/index.html', 'öppettider/index.html', 'vår-ö.html'):
            self.assertRegex(df.stam(namn), r'^[A-Za-z0-9_.-]+$', namn)
        self.assertNotEqual(df.stam('tjänster/index.html'), df.stam('tjanster/index.html'), 'translitterationen krockar inte')
        self.assertEqual(df.stam('tjänster/index.html'), df.stam('tja\u0308nster/index.html'), 'NFC och NFD är samma sida')

    def test_astro_utan_las_och_ett_bygge_som_faller(self):
        self.astro()
        shutil.rmtree(self.k / SLUG / 'kandidater' / 'k02', ignore_errors=True)
        p = self.projekt('k02', las=False)
        (p / 'RIKTNING.md').unlink()
        df.riktningar(SLUG, ['k02'])
        with self.assertRaisesRegex(df.ByggFel, 'låset'):
            df.version(SLUG, None, None, 'utan lås', ritning='k02', bilder=False)
        self.assertEqual(df.versioner(SLUG), [], 'utan lås kan helbygget inte installera paketen: ingen version')
        (p / 'package-lock.json').write_text(json.dumps({'lockfileVersion': 3, 'packages': {'': {'name': 'prov-k02'}}}))
        post = df.version(SLUG, None, None, 'första', ritning='k02', bilder=False)
        self.assertEqual(post['las'], 'projektets')
        self.assertTrue(any('RIKTNING.md saknas' in x for x in post['varningar']))
        with patch.object(df, 'bygg', return_value=(1, 'astro build: ett fel i sidan')):
            with self.assertRaisesRegex(df.ByggFel, 'ett fel i sidan'):
                df.version(SLUG, None, None, 'andra', ritning='k02', bilder=False)
        self.assertEqual(df.versioner(SLUG), ['v01'], 'ett bygge som faller ger ingen version')
        with self.assertRaisesRegex(df.Fel, 'finns inte i bandet'):
            df.version(SLUG, None, None, 'x', ritning='k09', bilder=False)
        with self.assertRaisesRegex(df.Fel, 'ange --ritning'):
            df.version(SLUG, None, None, 'x', bilder=False)

    def test_duken_ar_pausad(self):
        """Läget duk står kvar men pausat: ny --kanvas, runtime, tillgang och version --fran nekas utom med
        NWP_DESIGNLAGE=duk, och startkommandot nekas för en designfas i läget duk."""
        with self.assertRaisesRegex(df.Fel, 'pausat'):
            df.ny(SLUG, KANVAS)
        df.ny(SLUG)
        self.assertEqual(df.lage(SLUG), 'astro')
        rt = self.tmp / 'dc-runtime.js'
        rt.write_text(RUNTIME)
        for f in (lambda: df.runtime(SLUG, rt, 'r1'), lambda: df.tillgang(SLUG, BLOBB, self.bild),
                  lambda: df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'x', bilder=False)):
            with self.assertRaisesRegex(df.Fel, 'pausat'):
                f()
        os.environ['NWP_DESIGNLAGE'] = 'duk'
        with self.assertRaisesRegex(df.Fel, 'läget astro'):
            df.ny(SLUG, KANVAS)
        shutil.rmtree(self.u / SLUG / 'design')
        df.ny(SLUG, KANVAS)
        self.assertEqual(df.lage(SLUG), 'duk')
        del os.environ['NWP_DESIGNLAGE']
        with self.assertRaisesRegex(df.Fel, 'pausat'):
            df.start(SLUG, skriv_bara=True)
        # en designfas från före beslutet utan fältet lage är duk när den har en duk
        d = json.loads((self.u / SLUG / 'design' / 'DESIGNFAS.json').read_text())
        d.pop('lage')
        (self.u / SLUG / 'design' / 'DESIGNFAS.json').write_text(json.dumps(d))
        self.assertEqual(df.lage(SLUG), 'duk')

    def test_version_kopieras_hashas_och_renderas(self):
        self.duk()
        # en attrapp av impeccables motor (detektor.motor läser IMPECCABLE_BIN): fynden med kodutdrag och sidtext, och
        # --scope type/layout som ger området per regel (valideringen 2026-10-12)
        motor = self.tmp / 'motor' / 'impeccable'
        motor.parent.mkdir(parents=True, exist_ok=True)
        logg = self.tmp / 'motor' / 'anrop.log'
        motor.write_text('#!%s\nimport json, sys\na = sys.argv[1:]\nopen(%r, "a").write(" ".join(a) + "\\n")\n'
                         'import urllib.request\n'
                         'try:\n    urllib.request.urlopen(a[-1], timeout=20).read()\n'
                         'except Exception:\n    sys.exit(1)  # som motorn: sidan kunde inte skannas\n'
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
        # kontrollerna når sidan: renderingens server betjänar barnen medan de kör (ett synkront barn blockerade den, och
        # axe, stilen och detektorn fick ERR_FAILED; upptäckt 2026-10-13). Motorns attrapp hämtar sidan över HTTP och
        # svarar 1 utan den; axe och stilen vägras här av slugvakten (provets rot ligger utanför repot), aldrig ERR_FAILED
        k = json.loads((vk / 'BILDER.json').read_text())['kontroll']
        for n in ('axe', 'stil'):
            self.assertNotIn('ERR_FAILED', k[n]['utdata'] + k[n]['fel'], n)
        self.assertTrue(all(x.get('slutkod') == 2 and x.get('fynd') == 3 for x in k['detektor'].values()), k['detektor'])
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
        self.assertTrue(all(x in df.station_brief(SLUG, 'detaljer', 'Main.dc.html', self.u) for x in ('flat-type-hierarchy', 'cramped-padding')),
                        'detaljerna läser alla detektorns fynd')
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
        self.assertIn('Design-typens körmiljö', b['kalla'])
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

    def test_kommandot_ny_genom_main(self):
        # design.sh kör `designfas.py ny <slug>` för en ny kund; ett lokalt namn ny i main() gav UnboundLocalError
        # (utförarens fynd 2026-10-13, infört i 8e22e52)
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc = df.main(['ny', SLUG])
        self.assertIn(rc, (0, None))
        self.assertTrue(df.aktiv(SLUG), 'designfasen registrerad genom kommandot')
        self.assertEqual(df.lage(SLUG), 'astro', 'läget astro är standard')

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
        os.environ['NWP_DESIGNLAGE'] = 'duk'
        df.ny(SLUG, lage_='duk')
        with self.assertRaisesRegex(df.Fel, 'duken är inte registrerad'):
            df.version(SLUG, self.las_tillbaka(), '1791822460-0589', 'x', bilder=False)



class K_Paketen(Grund):
    """Paketen följer riktningen in i helbygget (granskningens fynd 2): paketbehovet avgörs av package.json mot låsets
    rot, inte av vad som råkar finnas i node_modules; källans package.json och lås ska höra ihop och varje paket komma ur
    npm-registret, annars skrivs ingen version."""

    def delad_sajt(self, rot_dep):
        s = self.k / SLUG / 'sajt'
        (s / 'node_modules' / 'clsx').mkdir(parents=True)  # clsx finns transitivt i sajtens node_modules
        (s / 'node_modules' / 'clsx' / 'package.json').write_text(json.dumps({'name': 'clsx', 'version': '2.1.1'}))
        (s / 'package.json').write_text(json.dumps({'name': 'sajt', 'dependencies': rot_dep}))
        (s / 'package-lock.json').write_text(json.dumps({'lockfileVersion': 3, 'packages': {'': {'name': 'sajt', 'dependencies': rot_dep},
                                                         'node_modules/astro': {'version': '5.0.0', 'resolved': 'https://registry.npmjs.org/astro/-/astro-5.0.0.tgz'}}}))
        return s

    def riktning_med_lank(self, beroenden):
        s = self.delad_sajt({'astro': '5.0.0'})
        df.ny(SLUG)
        p = self.projekt('k01', las=False)
        os.symlink(s / 'node_modules', p / 'node_modules')
        (p / 'package.json').write_text(json.dumps({'name': 'prov-k01', 'dependencies': beroenden}))
        df.riktningar(SLUG, ['k01'])
        self.stack.enter_context(patch.object(df, 'bygg', side_effect=bygg_attrapp))
        return p

    def test_paketbehovet_las_mot_package_json(self):
        p = self.riktning_med_lank({'astro': '5.0.0', 'clsx': '2.1.1'})
        self.assertTrue(kd.paketbehov(SLUG, 'k01'), 'clsx finns i node_modules men inte i låsets rot: npm install behövs')
        (p / 'package.json').write_text(json.dumps({'name': 'prov-k01', 'dependencies': {'astro': '5.0.0'}}))
        self.assertFalse(kd.paketbehov(SLUG, 'k01'), 'samma beroenden som låsets rot: inget behov')

    def test_kallans_paket_och_las_hor_ihop(self):
        p = self.riktning_med_lank({'astro': '5.0.0', 'clsx': '2.1.1'})
        with patch.object(kd, 'egna_paket', return_value=(0, 'ingenting installerades')):
            with self.assertRaisesRegex(df.ByggFel, 'hör inte ihop'):
                df.version(SLUG, None, None, 'clsx i riktningen', ritning='k01', bilder=False)
        self.assertEqual(df.versioner(SLUG), [], 'ingen version med ett lås som npm ci vägrar')

        def installera(slug, kid, paket=(), frist=None):  # som npm install: projektets eget lås med rotens beroenden
            (p / 'node_modules').unlink()
            (p / 'node_modules').mkdir()
            pj = json.loads((p / 'package.json').read_text())
            (p / 'package-lock.json').write_text(json.dumps({'lockfileVersion': 3, 'packages': {
                '': {'name': 'prov-k01', 'dependencies': pj['dependencies']},
                'node_modules/clsx': {'version': '2.1.1', 'resolved': 'https://registry.npmjs.org/clsx/-/clsx-2.1.1.tgz'}}}))
            return 0, 'installerat'
        with patch.object(kd, 'egna_paket', side_effect=installera):
            post = df.version(SLUG, None, None, 'clsx i riktningen', ritning='k01', bilder=False)
        kalla = self.u / SLUG / 'design' / 'versioner' / post['version'] / 'kalla'
        self.assertEqual(json.loads((kalla / 'package-lock.json').read_text())['packages']['']['dependencies'],
                         json.loads((kalla / 'package.json').read_text())['dependencies'])

    def test_ett_paket_utanfor_npm_registret_falls(self):
        df.ny(SLUG)
        p = self.projekt('k01')
        df.riktningar(SLUG, ['k01'])
        self.stack.enter_context(patch.object(df, 'bygg', side_effect=bygg_attrapp))
        for kalla, falt in (('git+https://github.com/exempel/paket.git', {'resolved': 'git+https://github.com/exempel/paket.git'}),
                            ('lokal länk', {'link': True, 'resolved': '../paket'})):
            (p / 'package-lock.json').write_text(json.dumps({'lockfileVersion': 3, 'packages': {
                '': {'name': 'prov-k01'}, 'node_modules/paket': dict({'version': '1.0.0'}, **falt)}}))
            with self.assertRaisesRegex(df.ByggFel, 'npm-registret'):
                df.version(SLUG, None, None, 'ett paket ur %s' % kalla, ritning='k01', bilder=False)
        self.assertEqual(df.versioner(SLUG), [])



class L_Versionsnumret(Grund):
    """Versionsnumret gäller hela designfasen men skrivlåset en riktning (granskningens fynd 6): numret reserveras
    atomiskt, och en version som avbröts innan VERSION.json skrevs är ingen version."""

    def test_samma_nasta_nummer_i_tva_riktningar_krockar_inte(self):
        self.astro(('k01', 'k02'))
        with patch.object(df, 'nasta', return_value='v01'):  # två sessioner som räknade fram samma nästa nummer
            a = df.version(SLUG, None, None, 'första riktningen', ritning='k01', bilder=False)
            b = df.version(SLUG, None, None, 'andra riktningen', ritning='k02', bilder=False)
        self.assertEqual((a['version'], b['version']), ('v01', 'v02'))

    def test_tre_riktningar_samtidigt(self):
        import threading
        self.astro(('k01', 'k02', 'k03'))
        hinder = threading.Barrier(3)

        def bygg_samtidigt(sajt):
            hinder.wait(timeout=30)  # alla tre byggen klara samtidigt, så att numren tilldelas på en gång
            return bygg_attrapp(sajt)
        ut, fel = {}, []

        def kor(kid):
            try:
                ut[kid] = df.version(SLUG, None, None, 'samtidigt', ritning=kid, bilder=False)['version']
            except Exception as e:  # noqa: BLE001
                fel.append(repr(e))
        with patch.object(df, 'bygg', side_effect=bygg_samtidigt):
            tradar = [threading.Thread(target=kor, args=(k,)) for k in ('k01', 'k02', 'k03')]
            for x in tradar:
                x.start()
            for x in tradar:
                x.join(60)
        self.assertEqual(fel, [])
        self.assertEqual(sorted(ut.values()), ['v01', 'v02', 'v03'])
        self.assertEqual({json.loads((self.u / SLUG / 'design' / 'versioner' / v / 'VERSION.json').read_text())['ritning'] for v in ut.values()},
                         {'k01', 'k02', 'k03'})

    def test_en_avbruten_version_ar_ingen_version(self):
        self.astro()
        with patch.object(df, 'kopiera_kalla', side_effect=RuntimeError('kraschen mitt i versionen')):
            with self.assertRaisesRegex(RuntimeError, 'kraschen'):
                df.version(SLUG, None, None, 'avbryts', ritning='k01', bilder=False)
        self.assertTrue((self.u / SLUG / 'design' / 'versioner' / 'v01').is_dir(), 'katalogen står kvar efter kraschen')
        self.assertEqual(df.versioner(SLUG), [])
        self.assertEqual(df.status(SLUG)['versioner'], [])
        with self.assertRaisesRegex(df.Fel, 'finns inte'):
            df.godkann(SLUG, 'v01', 'k01')
        with self.assertRaisesRegex(df.Fel, 'finns inte'):
            df.bestall(SLUG, 'kritik', 'v01', 'k01', 'Kritik av en version som aldrig blev klar, för provet')
        post = df.version(SLUG, None, None, 'nästa', ritning='k01', bilder=False)
        self.assertEqual(post['version'], 'v02', 'numret återanvänds inte')


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

    def test_livscykeln_i_projekten(self):
        self.astro(('k01', 'k02'))
        df.version(SLUG, None, None, 'första', ritning='k01', bilder=False)
        b = df.bestall(SLUG, 'referenser', 'v01', 'k01', 'Bättre förebilder för prislistan i en lokal verkstad')
        self.assertEqual((b['lage'], b['kanvas'], b['ritning']), ('astro', None, 'k01'))
        with self.assertRaisesRegex(df.Fel, 'gäller riktningen k01'):
            df.bestall(SLUG, 'typografi', 'v01', 'k02', 'en uppgift som är lång nog att godtas')
        post = df.version(SLUG, None, None, 'prislistan efter B001', ['B001'], ritning='k01', bilder=False)
        self.assertEqual((df.bestallning(SLUG, 'B001')['status'], post['version']), ('inford', 'v02'))


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

    def test_jamforelsen_ser_alla_riktningarnas_senaste_version(self):
        """Kritiken och jämförelsen före valet körs samlat: med --ritning * får passet varje riktnings senaste version, och
        en riktnings pass får projektets källa (kalla/), aldrig kritiken."""
        self.astro(('k01', 'k02', 'k03'))
        for i, kid in enumerate(('k01', 'k02', 'k03', 'k01')):
            df.version(SLUG, None, None, 'version %d' % i, ritning=kid, bilder=False)
            self.fejkbilder('v%02d' % (i + 1))
        b = df.bestall(SLUG, 'jamforelse', 'v04', '*', 'Falsk variation mellan de tre riktningarna före ägarens val')
        p = df.specialist_prompt(SLUG, b)
        for kid, v in (('k01', 'v04'), ('k02', 'v02'), ('k03', 'v03')):
            self.assertIn('riktningen %s, %s, sidan index.html, 390: ' % (kid, v), p)
        self.assertNotIn('riktningen k01, v01', p, 'bara riktningens senaste version')
        self.assertIn('Versionens källa (projektets src/', p)
        self.assertIn('Astro-sida', p)
        k = df.bestall(SLUG, 'kritik', 'v04', 'k01', 'Kritik av riktningen som en besökare ser den, före förklaringen')
        self.assertNotIn('Versionens källa', df.specialist_prompt(SLUG, k))


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
        self.assertEqual(df.installera_godkand(SLUG), [], 'läget duk installerar inget: bygget implementerar förlagan')
        # en senare dom från ägaren tar över
        skapande.lagg_till_dom(SLUG, 'ägaren', 'ny_riktning', 'börja om', underlag=self.u, tid='2099-01-01T00:00:00Z')
        self.assertFalse(df.godkand_giltig(SLUG)[0])

    def test_overlamningen_och_installationen_i_projekten(self):
        """Läget astro: överlämningen har källan (kalla/) med package.json och låset, och installationen lägger den
        godkända versionens källa i kunder/<slug>/sajt med samma prövning som en godkänd kandidat; paketen följer med, och
        sajtens .npmrc låser installationen (beslutet 2026-10-13, punkt 5)."""
        self.astro()
        df.version(SLUG, None, None, 'första', station_='innehall', ritning='k01', bilder=False)
        self.fejkbilder('v01')
        with self.assertRaisesRegex(df.Fel, 'gäller riktningen k01'):
            df.godkann(SLUG, 'v01', 'k02')
        g = df.godkann(SLUG, 'v01', 'k01')
        self.assertEqual((g['lage'], g['ritning'], g['kanvas']), ('astro', 'k01', None))
        k = df.overlamna(SLUG)
        for n in ('kalla/package.json', 'kalla/package-lock.json', 'kalla/src/pages/index.astro', 'kalla/RIKTNING.md', 'bilder/index-390.png'):
            self.assertTrue((k / n).is_file(), n)
        self.assertTrue(any('Designvärden' in b for b in df.overlamning_brister(SLUG)))
        self.fyll(k)
        self.assertEqual(df.overlamning_brister(SLUG), [])
        (k / 'kalla' / 'package-lock.json').unlink()
        self.assertTrue(any('package-lock.json saknas' in b for b in df.overlamning_brister(SLUG)), 'låset krävs i paketet')
        df.overlamna(SLUG)
        self.assertTrue(df.godkand_giltig(SLUG)[0])
        sajt = self.k / SLUG / 'sajt'
        (sajt / 'src' / 'pages').mkdir(parents=True)
        (sajt / 'package.json').write_text('{"name": "mallen"}')
        (sajt / 'src' / 'pages' / 'index.astro').write_text('<h1>Mallen</h1>')
        (sajt / 'src' / 'pages' / 'tjanster.astro').write_text('<h1>En sida som riktningen tog bort</h1>')
        (sajt / 'public').mkdir()
        (sajt / 'public' / 'gammal.svg').write_text('<svg/>')
        (sajt / 'node_modules').mkdir()
        (sajt / 'node_modules' / 'kvar.txt').write_text('sajtens installation rörs inte')
        (sajt / '.npmrc').write_text('save-exact=true\nfund=false\n')
        ersatta = df.installera_godkand(SLUG)
        # exakt den godkända källan: src/ och public/ ersätts som helheter (granskningens fynd 3)
        self.assertEqual(sorted(x.relative_to(sajt).as_posix() for x in (sajt / 'src').rglob('*') if x.is_file()),
                         sorted(n for n in json.loads((self.u / SLUG / 'design' / 'versioner' / 'v01' / 'VERSION.json').read_text())['filer']
                                if n.startswith('src/')))
        self.assertEqual(sorted(x.name for x in (sajt / 'public').iterdir()), ['robots.txt'], 'public/ är källans')
        self.assertTrue((sajt / 'node_modules' / 'kvar.txt').is_file())
        for borta in ('tjanster.astro', 'gammal.svg'):
            self.assertTrue(list((self.k / SLUG / 'startsida-ersatt').rglob(borta)), '%s flyttades undan, inget raderades' % borta)
        kalla = self.u / SLUG / 'design' / 'versioner' / 'v01' / 'kalla'
        for n in ('package.json', 'package-lock.json', 'src/pages/index.astro', 'RIKTNING.md', 'astro.config.mjs'):
            self.assertEqual((sajt / n).read_bytes(), (kalla / n).read_bytes(), n)
        npmrc = (sajt / '.npmrc').read_text().splitlines()
        self.assertEqual(sorted(npmrc), sorted(['fund=false', 'ignore-scripts=true', 'save-exact=true', 'registry=https://registry.npmjs.org/']))
        self.assertTrue(any(x.endswith('kunder/%s/sajt/.npmrc' % SLUG) or x.endswith('sajt/.npmrc') for x in ersatta), ersatta)
        undan = list((self.k / SLUG / 'startsida-ersatt').rglob('index.astro'))
        self.assertEqual([x.read_text() for x in undan], ['<h1>Mallen</h1>'], 'den ersatta startsidan flyttades, inget raderades')
        self.assertEqual(df.installera_godkand(SLUG), [], 'en andra installation ändrar inget')
        (kalla / 'package.json').write_text('{"name": "ändrad"}')
        with self.assertRaisesRegex(df.Fel, 'giltigt'):
            df.installera_godkand(SLUG)

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
        self.assertIn('designfas.installera_godkand', k, 'den godkända källan läggs i sajten före bygget')
        self.assertIn('npm ci --prefix kunder/$SLUG/sajt', k, 'paketen installeras ur låset')
        self.assertLess(k.index('kontroller/startkontroll.py'), k.index('designfas.installera_godkand'), 'startkontrollen först')
        self.assertLess(k.index('designfas.installera_godkand'), k.index('chflags uchg "$ROOT/kunder"'))
        s = (ROOT / '.claude' / 'skills' / 'bygg-sajt' / 'SKILL.md').read_text()
        self.assertIn('ur designfasen', s)


class H_Band(Grund):
    """Produktionsbandet (ägarens uppdrag 2026-10-12, version 2) på riktningen k01 i läget astro: stationerna ur
    metodkartans tabell i processmodellens ordning, varje station med en metod, versioner som bär stationen, överhoppade
    stationer med skäl, kritikens återgång, bandets läge per riktning och ett kvitto som redovisar utan att fälla."""

    def test_tabellen_i_litteraturens_ordning(self):
        st = df.stationer()
        ordning = list(st)
        self.assertEqual(ordning[:5], ['underlag', 'innehall', 'art', 'komposition', 'detaljer'],
                         'content first, art direction före kompositionen, detaljerna före valet (ägarens beslut 2026-10-13)')
        self.assertIn('rorelse', st['detaljer']['metoder'])
        self.assertIn('21st', st['detaljer']['mcp'])
        self.assertIn('emil-animate/SKILL.md', st['detaljer']['karna'])
        self.assertIn('ds_rorelse', st['detaljer']['pass'])
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
        self.assertIn('RIKTNING.md', st['underlag']['utdata'], 'dukens sida Underlag är RIKTNING.md i projektet')
        with self.assertRaisesRegex(df.Fel, 'okänd station'):
            df.station('smak')

    def test_bandet_pa_en_riktning(self):
        self.astro(('k01', 'k02'))
        v1 = df.version(SLUG, None, None, 'struktur med verkligt innehåll', station_='innehall', ritning='k01', bilder=False)
        self.fejkbilder('v01')
        v2 = df.version(SLUG, None, None, 'typskalan', station_='typografi', ritning='k01', bilder=False,
                        hoppade=['art=provets riktning prövar bara mekaniken, inget språk'])
        self.fejkbilder('v02')
        self.assertEqual((v1['station'], v2['station'], v2['ritning']), ('innehall', 'typografi', 'k01'))
        self.assertEqual(df.forra_med(SLUG, 'v02', 'k01'), 'v01')
        self.assertIsNone(df.forra_med(SLUG, 'v02', 'k02'), 'riktningen k02 har ingen version')
        band = df.band(SLUG)
        self.assertEqual(sorted(band), ['k01', 'k02'], 'riktningarna ur DESIGNFAS.json, också före sin första version')
        lage = {x['station']: x['lage'] for x in band['k01']}
        self.assertEqual((lage['innehall'], lage['typografi'], lage['art']), ('gjord', 'gjord', 'hoppad'))
        self.assertEqual(lage['formular'], 'ej tillämplig', 'riktningen har inget formulär')
        self.assertEqual(lage['jamforelse'], 'återstår', 'två riktningar i bandet')
        self.assertEqual(lage['overlamning'], 'väntar')
        self.assertEqual(lage['kritik'], 'återstår')
        self.assertEqual({x['station']: x['lage'] for x in band['k02']}['innehall'], 'återstår')
        s = df.status(SLUG)
        self.assertEqual((s['lage'], s['riktningar']['k01']['senaste'], s['riktningar']['k02']['senaste']), ('astro', 'v02', None))

    def test_kritik_och_tillganglighet_hoppas_inte_over(self):
        self.astro()
        for sid in df.ALLTID:
            with self.assertRaisesRegex(df.Fel, 'körs alltid'):
                df.version(SLUG, None, None, 'x', bilder=False, ritning='k01', hoppade=[sid + '=ett skäl som är långt nog att godtas'])
        with self.assertRaisesRegex(df.Fel, 'skäl'):
            df.version(SLUG, None, None, 'x', bilder=False, ritning='k01', hoppade=['polish=nej'])
        with self.assertRaisesRegex(df.Fel, 'ritning'):
            df.version(SLUG, None, None, 'x', bilder=False, station_='art')
        self.assertEqual(df.versioner(SLUG), [], 'inget byggdes för ett anrop som nekades')

    def test_stationens_instruktion_och_bestallning(self):
        self.astro()
        forsta = df.station_brief(SLUG, 'innehall', 'k01')
        for del_ in ('Station innehall på riktningen k01 (Riktningen k01)', 'riktningens första version', 'v01 blir nästa',
                     '--station innehall --ritning k01', str(df.projekt(SLUG, 'k01'))[-30:], 'inte publicerad'):
            self.assertIn(del_, forsta)
        self.assertNotIn('--fran', forsta)
        df.version(SLUG, None, None, 'första', ritning='k01', bilder=False)
        self.fejkbilder('v01')
        t = df.station_brief(SLUG, 'typografi', 'k01')
        for del_ in ('Station typografi', 'impeccable/reference/typeset.md', 'better-typography/SKILL.md (aktivera med Skill)',
                     'Stationens metod', '--station typografi --ritning k01', 'v02 blir nästa', 'senaste version v01', 'index-390.png',
                     'designfas.py artefakt %s k01' % SLUG):
            self.assertIn(del_, t)
        self.assertNotIn('--fran', t)
        b = df.bestall(SLUG, 'komponent', 'v01', 'k01', 'En tjänstelista ur 21st som implementationsgrund för huvudsektionen')
        self.assertEqual(b['station'], 'komposition')
        with self.assertRaisesRegex(df.Fel, 'har inte passet'):
            df.bestall(SLUG, 'typografi', 'v01', 'k01', 'En typografisk analys som är lång nog att godtas', station_='komposition')

    def test_kvittot_faller_inte_och_kritiken_kan_skicka_tillbaka(self):
        self.astro()
        df.version(SLUG, None, None, 'första', bilder=False, station_='innehall', ritning='k01')
        df.bestall(SLUG, 'kritik', 'v01', 'k01', 'Kritik av versionen som en besökare ser den, före förklaringen')
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
        kritik = next(x for x in df.band(SLUG)['k01'] if x['station'] == 'kritik')
        self.assertEqual((kritik['lage'], kritik['atergang']['till']), ('svar', 'komposition'))


class J_Artefakt(Grund):
    """Ägarens visning (beslutet 2026-10-13, punkt 2): en privat artefakt per riktning med den byggda sidan, prövad på en
    version med Artifact-verktyget. Paketet byggs här; publiceringen gör sessionen och registrerar den."""

    def test_paketet_med_relativa_vagar_och_utan_csp(self):
        self.astro(('k01', 'k02'))
        df.version(SLUG, None, None, 'strukturen', station_='innehall', ritning='k01', bilder=False)
        df.version(SLUG, None, None, 'den andra riktningen', station_='innehall', ritning='k02', bilder=False)
        df.version(SLUG, None, None, 'språket', station_='art', ritning='k01', bilder=False)
        r = df.artefakt(SLUG, 'k01')
        ut = self.u / SLUG / 'design' / 'artefakt' / 'k01'
        self.assertEqual((r['versioner'], r['varningar']), (['v01', 'v03'], []), 'bara riktningens versioner')
        sida = (ut / 'index.html').read_text()
        self.assertNotIn('<html', sida.lower(), 'artefakten lindar in sidan i sitt eget skelett')
        self.assertNotIn('<head', sida.lower())
        self.assertTrue(sida.startswith('<title>'))
        for del_ in ('prefers-color-scheme: dark', ':root[data-theme="dark"]', 'data-w="390"', 'data-w="768"', 'data-w="1440"',
                     'v01 · Innehåll och struktur', 'v03 · Art direction', 'Öppna versionen som hel sida', 'href="v03/index.html"'):
            self.assertIn(del_, sida)
        v1 = (ut / 'v01' / 'index.html').read_text()
        self.assertNotIn('/_astro/', v1.replace('../_astro/', ''), 'inga absoluta /_astro/-vägar')
        self.assertIn('href="_astro/x.css"', v1)
        self.assertIn('srcset="_astro/bild-600.png 600w"', v1)
        self.assertNotIn('content-security-policy', v1.lower(), 'CSP-metan borttagen i förhandsvisningens kopia')
        self.assertIn('content-security-policy', (self.u / SLUG / 'design' / 'versioner' / 'v01' / 'sida' / 'index.html').read_text(),
                      'versionens egen sida är orörd')
        self.assertIn('url(../_astro/fonts/prov.woff2)', (ut / 'v01' / '_astro' / 'x.css').read_text())
        filer = [x['path'] for x in json.loads((ut / 'FILER.json').read_text())]
        self.assertIn('v01/index.html', filer)
        self.assertIn('v03/_astro/bild-600.png', filer)
        self.assertNotIn('index.html', filer, 'sidan själv publiceras som file_path')
        self.assertFalse([f for f in filer if f.startswith('v02/')])
        self.assertTrue(all((ut / f).is_file() for f in filer))
        self.assertEqual(r['omgangar'], [df.rel(ut / 'FILER.json')])
        # publiceringen registreras; samma artefakt per riktning; status och bandet visar adressen
        with self.assertRaisesRegex(df.Fel, 'gäller inte riktningen'):
            df.registrera_artefakt(SLUG, 'k01', ARTEFAKTEN, 'v02')
        a = df.registrera_artefakt(SLUG, 'k01', ARTEFAKTEN, 'v03', '1791900000-0001')
        self.assertEqual((a['url'], a['version']), (ARTEFAKTEN, 'v03'))
        self.assertTrue((self.u / SLUG / 'design' / 'riktningar' / 'k01' / 'ARTEFAKT.json').is_file())
        with self.assertRaisesRegex(df.Fel, 'samma artefakt'):
            df.registrera_artefakt(SLUG, 'k01', 'https://claude.ai/artifact/EnAnnanArtefakt012345', 'v03')
        self.assertEqual(df.status(SLUG)['riktningar']['k01']['artefakt'], ARTEFAKTEN)
        self.assertEqual(df.band(SLUG)['k01'][-1]['url'], ARTEFAKTEN)
        self.assertIsNone(df.band(SLUG)['k02'][-1]['url'])

    def test_over_255_filer_delas_i_omgangar(self):
        self.astro()
        df.version(SLUG, None, None, 'strukturen', ritning='k01', bilder=False)
        a_ = self.u / SLUG / 'design' / 'versioner' / 'v01' / 'sida' / '_astro'
        for i in range(300):
            (a_ / ('del-%03d.js' % i)).write_text('export const x = %d;\n' % i)
        r = df.artefakt(SLUG, 'k01')
        self.assertEqual(len(r['omgangar']), 2)
        delar = [json.loads((df.ROOT / x).read_text()) if not Path(x).is_absolute() else json.loads(Path(x).read_text()) for x in r['omgangar']]
        self.assertEqual([len(d) for d in delar], [255, r['filer'] - 255])



# Attrappen av claude för drivaren (fejkclaude-mönstret i kontroller/rokprov/andringar/): svarar som claude -p med
# --output-format json. En station gör en synlig ändring i riktningens projekt och svarar i stationens schema; ett
# specialistpass svarar i SVAR_SCHEMA (jämförelsen med fältet val); överlämningen fyller DESIGN.md. Inställningarna
# (vilket val, vilka anrop som faller) står i en JSON-fil bredvid skriptet, och varje anrop skrivs i en logg.
FEJKCLAUDE = r'''#!%(python)s
import json, re, sys, uuid
from pathlib import Path
conf = json.loads(Path(__file__).with_suffix('.json').read_text())
if '--help' in sys.argv:
    print('fejkclaude: ingen hjälp')
    sys.exit(0)
prompt = sys.stdin.read()
logg = Path(conf['logg'])
def svar(so):
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': str(uuid.uuid4()), 'num_turns': 3,
                      'duration_ms': 1200, 'total_cost_usd': 0.01, 'structured_output': so}))
    sys.exit(0)
m = re.search(r'Station (\w+) på riktningen (k\d\d)', prompt)
if m:
    sid, rid = m.groups()
    with logg.open('a') as f:
        f.write('station %%s %%s\n' %% (rid, sid))
    if [rid, sid] in conf.get('falla', []):
        print(json.dumps({'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'result': 'attrappen faller'}))
        sys.exit(1)
    projekt = Path(re.search(r'Projektet: (\S+) \(', prompt).group(1))
    sida = projekt / 'src' / 'pages' / 'index.astro'
    sida.write_text(sida.read_text() + '<p>stationen %%s</p>' %% sid)
    svar({'orsak': 'attrappen: stationen %%s gjorde en synlig insats på %%s' %% (sid, rid), 'paket': [], 'hoppa': None})
m = re.search(r'Fyll i (\S+DESIGN\.md) ur den godkända versionen', prompt)
if m:
    with logg.open('a') as f:
        f.write('overlamning\n')
    rubriker = conf['rubriker']
    Path(m.group(1)).write_text('# DESIGN\n\n' + '\n'.join('## %%s\n\nuppmätt: ett värde ur renderingen, tillräckligt långt för provet.\n' %% r for r in rubriker))
    svar({'orsak': 'DESIGN.md ifylld', 'paket': [], 'hoppa': None})
m = re.search(r'Beställning (B\d+) .* typ (\w+) ', prompt)
typ = m.group(2) if m else '?'
with logg.open('a') as f:
    f.write('pass %%s\n' %% typ)
so = {'sammanfattning': 'attrappens %%s' %% typ, 'fynd': [], 'forslag': [], 'referenser': [], 'begransningar': [],
      'kompetens': {'aktiverade': [], 'lasta': [], 'valda': []}}
if typ == 'jamforelse':  # valsvar: attrappens svar i tur och ordning (null: svaret saknar val)
    nr = logg.read_text().splitlines().count('pass jamforelse') - 1
    lista = conf.get('valsvar') or [conf['val']]
    if lista[min(nr, len(lista) - 1)]:
        so['val'] = {'riktning': lista[min(nr, len(lista) - 1)], 'skal': 'attrappens val: riktningen bär besökarens uppgift bäst'}
svar(so)
'''


class M_Drivaren(Grund):
    """Drivaren (ägarens beslut 2026-10-13: "Autonomous to build (Recommended)"): bandet utan ägaren från tre riktningar
    till en startad byggbegäran, med en attrapp för claude, bygget, renderingen och helbyggets start. Publiceringen anropas
    aldrig, ett avbrott tas upp, och ägarens eget val går före jämförelsens."""

    def setUp(self):
        super().setUp()
        self.fejk = self.tmp / 'fejk' / 'claude'
        self.fejk.parent.mkdir(parents=True)
        self.fejk.write_text(FEJKCLAUDE % {'python': sys.executable})
        self.fejk.chmod(0o755)
        self.logg = self.tmp / 'fejk' / 'anrop.log'
        self.conf(val='k02')
        os.environ.update(NWP_OBSERVATION='av', NWP_MEDDELANDEN='av', NWP_SKAPARWEBB='av')
        self.stack.enter_context(patch.object(atelje, 'claude', return_value=str(self.fejk)))
        self.stack.enter_context(patch.object(df, 'rendera', side_effect=self.rendera))
        self.stack.enter_context(patch.object(df, 'insats', return_value={'synlig': True, 'jamfort_med': None}))
        self.byggen = []
        import flodesstart
        self.stack.enter_context(patch.object(flodesstart, 'starta', side_effect=lambda slug, handling, start_id=None:
                                              self.byggen.append((slug, handling, start_id)) or 5))
        self.register = []  # körregistret på maskinen skrivs aldrig av provet
        self.stack.enter_context(patch.object(korregister, 'registrera', side_effect=lambda vad, slug=None, **k: self.register.append(('in', vad, slug))))
        self.stack.enter_context(patch.object(korregister, 'avregistrera', side_effect=lambda pid=None: self.register.append(('ut',))))
        self.astro(('k01', 'k02', 'k03'))

    def conf(self, **falt):
        c = {'logg': str(self.logg), 'val': 'k02', 'falla': [], 'rubriker': list(df.OVERLAMNING_RUBRIKER)}
        c.update(falt)
        self.fejk.with_suffix('.json').write_text(json.dumps(c))

    def rendera(self, slug, v, kontroll=False, underlag=None):
        self.fejkbilder(v)
        return {'slutkod': 0, 'saknade_tillgangar': [], 'besked': 'attrappens rendering'}

    def anrop(self):
        return self.logg.read_text().splitlines() if self.logg.is_file() else []

    def test_hela_vagen_till_en_startad_byggbegaran(self):
        def autogodkann(slug, v, ritning, underlag=None):  # sigillets attrapp (den riktiga finns i en annan gren)
            return df.godkann(slug, v, ritning, text='sigillets attrapp i provet')
        with patch.object(df, 'autogodkann', autogodkann, create=True):
            k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'klar', k.get('skal'))
        self.assertEqual([(h, s) for s, h, _ in self.byggen], [('helbygge', SLUG)], 'en byggbegäran, genom helbyggets väg')
        self.assertFalse([b for b in self.byggen if b[1] in ('release', 'aktivera')], 'publiceringen anropas aldrig')
        rader = self.anrop()
        for rid in ('k01', 'k02', 'k03'):
            for sid in df.FORE_VALET:
                self.assertEqual(rader.count('station %s %s' % (rid, sid)), 1, (rid, sid))
                self.assertTrue(df.station_klar(SLUG, rid, sid))
        for sid in df.efter_valet():
            self.assertEqual(rader.count('station k02 %s' % sid), 1, sid)
            self.assertEqual(rader.count('station k01 %s' % sid), 0, 'bara den valda går vidare')
        self.assertEqual((rader.count('pass kritik'), rader.count('pass jamforelse'), rader.count('overlamning')), (4, 1, 1))
        val = df.designfas(SLUG)['val']
        self.assertEqual((val['riktning'], val['kalla']), ('k02', 'jämförelsen'))
        domar = [json.loads(x) for x in (self.u / SLUG / skapande.DOMLOGG).read_text().splitlines()]
        jmf = [x for x in domar if x['kalla'] == 'jämförelsen']
        self.assertEqual([(x['beslut'], x['designfas']['riktning']) for x in jmf], [('valj', 'k02')])
        self.assertFalse(skapande.ar_agarens(jmf[0]) or skapande.ar_beslut(jmf[0]), 'jämförelsens val är aldrig ägarens')
        self.assertEqual(df.overlamning_brister(SLUG), [])
        kn = df.korning(SLUG)
        self.assertTrue(all(x.get('session') and x.get('forbrukning') for r in kn['stationer'].values() for x in r.values()))
        self.assertEqual(kn['bygge']['handling'], 'helbygge')
        self.assertEqual(df.kor(SLUG)['steg'], 'klar', 'en klar körning görs inte om')
        self.assertEqual(len(self.byggen), 1)

    def test_utan_sigillet_stannar_drivaren_fore_godkannandet(self):
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'vantar_pa_sigillet', k.get('skal'))
        self.assertIn('autogodkann', k['skal'])
        self.assertEqual(self.byggen, [])
        self.assertFalse((self.u / SLUG / 'design' / 'GODKANNANDE.json').exists())

    def test_ett_avbrott_tas_upp_utan_att_det_klara_gors_om(self):
        self.conf(falla=[['k03', 'art']])
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'stoppad')
        self.assertIn('art', k['skal'])
        self.assertIn('k03', k['skal'])
        forsta = self.anrop()
        self.assertEqual(forsta.count('station k03 art'), df.MAX_FORSOK_STATION, 'ett nytt försök inom taket')
        self.conf()
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'vantar_pa_sigillet', k.get('skal'))
        andra = self.anrop()[len(forsta):]
        for rid in ('k01', 'k02'):
            for sid in df.FORE_VALET:
                self.assertNotIn('station %s %s' % (rid, sid), andra, 'det klara görs inte om')
        self.assertIn('station k03 art', andra)
        self.assertNotIn('station k03 innehall', andra)

    def test_texterna_sager_vad_stationssessionerna_har(self):
        """Andra granskningens fynd 5: stationssessionerna har Bash med rollen skapas skript, så texterna säger det och
        nämner varje skript som verktygslistan släpper fram."""
        regler = df.station_verktyg(SLUG, 'k01')
        skript = sorted({re.search(r'kontroller/(\w+\.py)', r).group(1) for r in regler if r.startswith('Bash(')})
        self.assertTrue(skript, regler)
        texter = {'skillen': (ROOT / '.claude' / 'skills' / 'designfas' / 'SKILL.md').read_text(),
                  'skapandeflodet': (ROOT / 'kunskap' / 'skapandeflodet.md').read_text(), 'station_verktyg': df.station_verktyg.__doc__}
        for namn, text in texter.items():
            self.assertIsNone(re.search(r'inget Bash|utan Bash', text), namn)
            for s in skript:
                self.assertTrue(s in text, (namn, s))

    def test_drivaren_anmaler_sig_i_korregistret(self):
        """Andra granskningens fynd 4: drivaren anmäler sig i körregistret som arbetaren och kor.sh, så att underhållet
        inte byter verktyg mitt i ett band, och avanmäler sig vid slut och vid stopp."""
        df.kor(SLUG)
        self.assertEqual(self.register, [('in', 'designfas', SLUG), ('ut',)])

    def test_drivaren_avanmaler_sig_vid_stopp(self):
        self.conf(falla=[['k01', 'art']])
        self.assertEqual(df.kor(SLUG)['steg'], 'stoppad')
        self.assertEqual(self.register, [('in', 'designfas', SLUG), ('ut',)], 'avanmäld också vid stopp')

    def test_ett_svar_utan_giltigt_val_ger_en_ny_jamforelse(self):
        """Granskningens fynd 1 (andra granskningen): ett jämförelsesvar utan val, eller med ett val som inte är en
        riktning, ger en ny beställning, högst två försök; skiftläget normaliseras, och en levererad beställning utan
        giltigt val återanvänds aldrig, så att en återupptagning inte fastnar på samma svar."""
        self.conf(valsvar=[None, 'K02'])
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'vantar_pa_sigillet', k.get('skal'))
        self.assertEqual(self.anrop().count('pass jamforelse'), 2)
        self.assertEqual(df.designfas(SLUG)['val']['riktning'], 'k02', 'K02 normaliseras')

    def test_inget_giltigt_val_stoppar_och_aterupptagningen_fastnar_inte(self):
        self.conf(valsvar=[None, 'k09'])
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'stoppad')
        self.assertIn('giltigt val', k['skal'])
        self.assertEqual(self.anrop().count('pass jamforelse'), 2)
        self.conf(valsvar=['k01'])
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'vantar_pa_sigillet', k.get('skal'))
        self.assertEqual(self.anrop().count('pass jamforelse'), 3, 'den levererade beställningen utan val återanvändes inte')
        self.assertEqual(df.designfas(SLUG)['val']['riktning'], 'k01')

    def test_jamforelsens_schema_kraver_ett_val_bland_riktningarna(self):
        s = df.jamforelse_schema(SLUG)
        self.assertIn('val', s['required'])
        self.assertEqual(s['properties']['val']['properties']['riktning']['enum'], ['k01', 'k02', 'k03'])
        self.assertNotIn('val', df.SVAR_SCHEMA['required'], 'de andra passens schema är oförändrat')

    def test_agarens_val_efter_starten_gar_fore(self):
        df.logga(SLUG, start='2026-01-01T00:00:00Z')
        skapande.lagg_till_dom(SLUG, 'ägaren', 'valj', 'Jag väljer riktningen k03.', underlag=self.u,
                               kandidater=[{'id': 'k03', 'version': 'v' * 12}])
        k = df.kor(SLUG)
        self.assertEqual(k['steg'], 'vantar_pa_sigillet', k.get('skal'))
        val = df.designfas(SLUG)['val']
        self.assertEqual((val['riktning'], val['kalla']), ('k03', 'ägaren'))
        self.assertIn('station k03 typografi', self.anrop())
        self.assertFalse([x for x in (self.u / SLUG / skapande.DOMLOGG).read_text().splitlines() if 'jämförelsen' in x])

    def test_kandidatflodet_och_prototyp_startar_drivaren(self):
        startade = []
        self.stack.enter_context(patch.object(df, 'starta_drivaren', side_effect=lambda slug, underlag=None: startade.append(slug) or (4711, 'startad')))
        os.environ['NWP_DESIGNFAS_AUTONOM'] = 'pa'
        (self.u / SLUG / 'atelje').mkdir(parents=True, exist_ok=True)
        (self.u / SLUG / 'atelje' / 'STATUS.json').write_text(json.dumps({'slug': SLUG, 'steg': 'band', 'kandidatflode': True}))
        import io
        for argv in ([SLUG], [SLUG, '--fortsatt']):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(prototyp.main(argv), 0)
        self.assertEqual(startade, [SLUG, SLUG])
        st = {}
        with patch.multiple(kd, forbered_projekt=lambda slug, kid: None, stilpaket_i_projekt=lambda slug, kid: None):
            kd.lamna_till_bandet(SLUG, st, lambda: None, ['k01'])
        self.assertEqual(st['bandet']['drivare']['pid'], 4711)
        self.assertEqual(startade, [SLUG, SLUG, SLUG], 'kandidatflödet startar drivaren efter lamna_till_bandet')

    def test_helbyggets_start_godtar_designgodkannandet(self):
        import flodesstart
        with patch.object(flodesstart, 'startmiljo', return_value={'hinder': None}), patch.object(flodesstart, 'atelje_ledig'), \
                patch.object(skapande, 'godkand_giltig', return_value=(False, 'ingen kandidat godkänd')):
            with patch.object(df, 'godkand_giltig', return_value=(True, 'designen godkänd', {'version': 'v01'})):
                flodesstart.krav(SLUG, 'helbygge')
            with patch.object(df, 'godkand_giltig', return_value=(False, 'inget designgodkännande', None)):
                with self.assertRaisesRegex(ValueError, 'inget designgodkännande'):
                    flodesstart.krav(SLUG, 'helbygge')


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
        self.assertIn('detaljer', df.SVAR_SCHEMA['properties']['atergang']['properties']['till']['enum'], 'kritiken kan begära omtag av detaljerna')
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
        ensam2 = ensam.replace('| `rorelse`, `detalj`, `wai` | ny version med före och efter; RIKTNING.md', '| `rorelse`, `wai` | ny version med före och efter; RIKTNING.md')
        self.assertNotEqual(ensam2, ensam, 'detaljernas metodcell finns')
        self.assertFalse(any('metoden detalj har ingen station' in x for x in df.karta_prova(ensam)), 'detaljerna har metoden kvar')
        ensam = ensam2
        self.assertTrue(any('metoden detalj har ingen station' in x for x in df.karta_prova(ensam)))

    def test_en_saknad_skill_falls(self):
        text = df.KARTA.read_text(encoding='utf-8')
        m = df.KARTBLOCK.search(text)
        rad = next(r for r in m.group('rader').splitlines() if r.startswith('skill:taste |'))
        self.assertIn('skillen taste saknar rad', '\n'.join(df.karta_prova(text.replace(rad + '\n', ''))))


class G_Start(Grund):
    def test_startkommandot(self):
        df.ny(SLUG)
        args = df.start(SLUG, skriv_bara=True)
        self.assertIn('--strict-mcp-config', args)
        self.assertEqual(args[-1], '/designfas %s' % SLUG)
        inst = json.loads(Path(args[args.index('--settings') + 1]).read_text())
        self.assertIn('kundvakt.py', json.dumps(inst['hooks']))
        self.assertIn('Bash(*designfas.py godkann*)', inst['permissions']['deny'])
        self.assertTrue(any(a.endswith('mobbin.json') for a in args))


if __name__ == '__main__':
    unittest.main(verbosity=1)
