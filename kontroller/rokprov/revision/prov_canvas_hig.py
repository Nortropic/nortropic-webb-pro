#!/usr/bin/env python3
"""prov_canvas_hig.py — canvas-design och HIG-principerna i verktygslådan (ägarens uppdrag 2026-10-07, punkt 5D och 5E;
BESLUT.md, tillägget 2026-10-07 om full verktygslåda, gren H5):

1. skillen canvas-design finns med SKILL.md, Apache-2.0-licensen och KALLA.md (källa, commit, datum, licens, det
   utelämnade), och varje typsnittsfil i canvas-fonts/ har sin familjs OFL-fil;
2. metodkartans block komposition ger skillen uppgiften som alternativ, kompetens.py läser den (valbara, prompten),
   och kartans stycke binder resultatet till BILDER.md och materialsteget;
3. kunskap/hig-principer.md finns, är låst i metodkarta.lock.json, är kärna i granskning och kritik med uppgiften
   (återkoppling, fokus, avbrytbar rörelse, begriplighet, textstorlek, tillgänglighet), har emil-apple-design som
   alternativ i granskningen, har källa och lästdatum per princip, och säger att Apples visuella stil inte är ett krav;
   en ändrad eller olåst källa stoppar leveransen;
4. ingen mening i kartan, bild.md, KALLA.md eller hig-principer.md kallar en PNG eller PDF en prototyp utan att neka
   det, och regeln står uttryckligen i kartan och bild.md;
5. atelje.egna_bilder räknar aldrig ett koncept ur canvas-design som verksamhetens egen bild, med eller utan kolumnen
   Egen;
6. formen för registreringen (fil, källa med commit, visar, datum, kvalitet, Egen nej) står i kartans stycke, och bild.md
   bär regeln och hänvisar dit (bild.md ingår i skaparens kärna, som hålls under 160 000 tecken);
7. kvittot (kompetens.kvitto ur bildkedja) på en sessions radformat: en nekad eller misslyckad Skill-aktivering räknas
   inte, en lyckad gör det, en hel Read är läst och en delvis inte, och aktivering, läsning och användning står skilda
   från tillämpningen, som kvittot aldrig ser (ägarens förtydligande 2026-10-07, ~15:20Z).

    .venv/bin/python kontroller/rokprov/revision/prov_canvas_hig.py <repo>

Fallen var röda mot 2b4045e (före grenen) och är gröna efter. Repots egna filer läses men ändras inte; det som skrivs
hamnar i provets registrerade tempkatalog, och inga privata data läses. Varje fall redovisas för sig på stderr;
slutkod 1 när något fall föll.
"""
import os
import re
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
K = ROOT / 'kontroller'
TMP = Path(tempfile.mkdtemp(prefix='nwp-canvashig-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
sys.path.insert(0, str(K))
import korregister  # noqa: E402
korregister.registrera_tmp(TMP, 'prov_canvas_hig')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
os.environ['NWP_STADNING'] = 'av'
import metod  # noqa: E402
import kompetens  # noqa: E402

SKILL = ROOT / '.claude' / 'skills' / 'canvas-design'
HIG = 'kunskap/hig-principer.md'
HIG_ORD = ('återkoppling', 'fokus', 'begriplighet', 'textstorlek', 'tillgänglighet')
SIDOR = ('motion', 'focus-and-selection', 'feedback', 'typography', 'accessibility')
FEL = []


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:900]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


def text(p):
    return Path(p).read_text(encoding='utf-8')


def meningar(t):
    """Meningarna i en text (punkt, semikolon eller radslut efter en tom rad), för att pröva vad varje mening säger."""
    return [m.strip() for m in re.split(r'(?<=[.;])\s+|\n\s*\n', t) if m.strip()]


def nekar(m, ord_='prototyp'):
    """Negationen står inom 70 tecken före varje förekomst av ordet, inte bara någonstans i meningen (mutationen M7 2026-10-07
    överlevde en kontroll över hela meningen: ett "aldrig" längre bak räddade en mening som kallade en PNG en prototyp)."""
    platser = [x.start() for x in re.finditer(ord_, m, re.I)]
    return bool(platser) and all(re.search(r'\b(aldrig|inte|inget|ingen)\b', m[max(0, i - 70):i], re.I) for i in platser)


# ===== 1. skillen =====
@fall('1 skillen canvas-design finns med SKILL.md, Apache-2.0-licensen och KALLA.md med källa, commit, datum, licens och det utelämnade; varje typsnittsfil har sin familjs OFL-fil')
def fall1():
    assert SKILL.is_dir() and not SKILL.is_symlink(), SKILL
    s = text(SKILL / 'SKILL.md')
    assert s.startswith('---\n') and re.search(r'^name:\s*canvas-design\s*$', s, re.M), s[:200]
    lic = text(SKILL / 'LICENSE.txt')
    assert 'Apache License' in lic and 'Version 2.0' in lic and 'TERMS AND CONDITIONS FOR USE' in lic, lic[:300]
    k = text(SKILL / 'KALLA.md')
    assert 'github.com/anthropics/skills' in k and 'skills/canvas-design/' in k, 'KALLA.md saknar källan'
    assert re.search(r'`[0-9a-f]{40}`', k), 'KALLA.md saknar commit-sha'
    assert re.search(r'20\d\d-\d\d-\d\dT\d\d:\d\d', k) and 'Intagen:** 2026-10-07' in k, 'KALLA.md saknar datum'
    assert 'Apache-2.0' in k and 'OFL' in k and 'Utelämnat:' in k, 'KALLA.md saknar licensen eller det utelämnade'
    assert 'prototyp' in k and 'BILDER.md' in k, 'KALLA.md säger inte hur skillen används'
    fonts = SKILL / 'canvas-fonts'
    ttf = sorted(p.name for p in fonts.glob('*.ttf'))
    assert len(ttf) >= 40, ttf
    for namn in ttf:
        fam = re.sub(r'-(Regular|Bold|Italic|BoldItalic|Medium|SemiBold|Light|Black|Thin)\.ttf$', '', namn)
        ofl = fonts / ('%s-OFL.txt' % fam)
        assert ofl.is_file(), 'typsnittet %s saknar licensfil %s' % (namn, ofl.name)
        assert 'SIL OPEN FONT LICENSE' in text(ofl).upper(), ofl
    # de sex som saknar OFL-fil i upstream är utelämnade och nämnda
    for fam in ('IBMPlexSerif', 'InstrumentSerif'):
        assert not list(fonts.glob('%s-*.ttf' % fam)), 'typsnitt utan OFL-fil intaget: %s' % fam
        assert fam in k, 'KALLA.md nämner inte det utelämnade %s' % fam


# ===== 2. uppgiften i komposition =====
@fall('2 metodkartans block komposition ger canvas-design uppgiften som alternativ; kompetens.py läser den i skissen och fördjupningen, prompten bär den, och kartans stycke binder resultatet till BILDER.md och materialsteget')
def fall2():
    karta = text(metod.KARTA)
    k = kompetens.tolka(karta)
    assert 'canvas-design/SKILL.md' in k['komposition']['valj'], k['komposition']['valj']
    for pass_ in ('skapa', 'fordjupa'):
        assert '.claude/skills/canvas-design/SKILL.md' in kompetens.valbara(pass_, k), (pass_, kompetens.valbara(pass_, k))
        assert 'canvas-design/SKILL.md' in '\n'.join(kompetens.prompt_rader(pass_, 'kv-prov', 'k01', k)), pass_
    assert '.claude/skills/canvas-design/SKILL.md' not in kompetens.lasfiler('skapa', k), 'skillen är alternativ, inte kärna'
    assert kompetens.prova(karta) == [], kompetens.prova(karta)
    # skaparens kärna hålls under 160 000 tecken (prov_revision, kompetenskedjan och granskning 3): bild.md ingår i den,
    # så formen för koncept står i kartans stycke och bild.md hänvisar dit (2026-10-07: 2 100 tecken i bild.md bröt taket)
    assert kompetens.storlek(kompetens.lasfiler('skapa', k)) < 160000, kompetens.storlek(kompetens.lasfiler('skapa', k))
    assert 'canvas-design står i BILDER.md' in k['komposition']['visar'] and 'Egen nej' in k['komposition']['visar'], k['komposition']['visar']
    m = re.search(r'\*\*Grafiska koncept ur canvas-design\*\*(.*?)\n\n', karta, re.S)
    assert m, 'kartan saknar stycket Grafiska koncept ur canvas-design'
    st = m.group(1)
    for ord_ in ('koncept', 'BILDER.md', 'materialsteget', '`Egen` nej', 'komposition', 'Skill-verktyget'):
        assert ord_.lower() in st.lower(), 'stycket saknar: %s' % ord_
    # läsningen är verklig: utan raden i blocket försvinner skillen ur alternativen
    utan = kompetens.tolka(karta.replace('; canvas-design/SKILL.md', ''))
    assert 'canvas-design/SKILL.md' not in utan['komposition']['valj']
    assert '.claude/skills/canvas-design/SKILL.md' not in kompetens.valbara('skapa', utan)


# ===== 3. HIG-principerna =====
@fall('3 hig-principer.md finns, är låst och är kärna i granskning och kritik med uppgiften; emil-apple-design är alternativ i granskningen; källa och lästdatum per princip; inget krav på Apples visuella stil; en ändrad eller olåst källa stoppar')
def fall3():
    f = ROOT / HIG
    assert f.is_file() and not f.is_symlink(), f
    t = text(f)
    assert re.search(r'inget krav på Apples visuella stil|inte ett krav (?:att|på) .*Apples visuella stil', t), 'filen säger inte att Apples stil inte är ett krav'
    kallor = [r for r in t.splitlines() if r.startswith('Källa:')]
    assert len(kallor) >= 5, kallor
    for r in kallor:
        assert any(v in r for v in ('developer.apple.com/design/human-interface-guidelines/', 'www.w3.org/WAI/')) and re.search(r'läst 20\d\d-\d\d-\d\d', r), r
    for sida in SIDOR:
        assert any('human-interface-guidelines/%s' % sida in r for r in kallor), 'ingen källa för sidan %s' % sida
    for ord_ in HIG_ORD + ('avbrytbar',):
        assert ord_ in t.lower(), 'filen saknar ordet %s' % ord_
    assert 'emil-apple-design' in t and 'emil-animate' in t, 'filen pekar inte på emil-apple-design och emil-animate'
    # låset: källan är låst med sin nuvarande hash, och kartan håller
    las = metod.las_lasfil()
    assert las.get(HIG) == metod.sha(t), 'hig-principer.md är inte låst med sin nuvarande hash (metod.py --las)'
    fel, kallor_ = metod.prova()
    assert fel == [] and HIG in kallor_, fel
    # rollerna
    karta = text(metod.KARTA)
    k = kompetens.tolka(karta)
    assert HIG in k['granskning']['karna'] and HIG in k['kritik']['karna'], (k['granskning']['karna'], k['kritik']['karna'])
    for pass_ in ('granskning', 'skisskritik', 'kritik_a'):
        assert HIG in kompetens.lasfiler(pass_, k), (pass_, kompetens.lasfiler(pass_, k))
    assert 'emil-apple-design/SKILL.md' in k['granskning']['valj'] and '.claude/skills/emil-apple-design/SKILL.md' in kompetens.valbara('granskning', k)
    g, kr = k['granskning']['uppgift'].lower(), k['kritik']['uppgift'].lower()
    for ord_ in HIG_ORD:
        assert ord_ in g and ord_ in kr, 'uppgiften saknar %s (granskning: %s; kritik: %s)' % (ord_, ord_ in g, ord_ in kr)
    assert 'avbrytbar' in g and 'hig-principer.md' in g and 'hig-principer.md' in kr
    assert 'inget krav på apples visuella stil' in g, g
    assert kompetens.prova(karta) == [], kompetens.prova(karta)
    m = re.search(r'\*\*HIG-principerna i interaktionsgranskningen\*\*(.*?)\n\n', karta, re.S)
    assert m and 'inget krav på Apples visuella stil' in m.group(1) and 'emil-apple-design' in m.group(1), 'kartans stycke om HIG saknas eller säger inte att stilen inte är ett krav'
    # en ändrad källa eller en som saknas i låset stoppar leveransen
    fel2, _ = metod.prova(las=dict(las, **{HIG: 'f' * 64}))
    assert any(HIG in x and 'har ändrats' in x for x in fel2), fel2
    fel3, _ = metod.prova(las={k_: v for k_, v in las.items() if k_ != HIG})
    assert any(HIG in x and 'saknas i låset' in x for x in fel3), fel3
    # kärnan växer med filen, men kritikens kärna håller sig under 70 000 tecken (mätningen 107–109 s gällde 58 850)
    n = kompetens.storlek(kompetens.lasfiler('skisskritik', k))
    assert len(t) <= 12000 and n <= 70000, (len(t), n)


# ===== 4. koncept, aldrig prototyp =====
@fall('4 ingen mening i kartan, bild.md, KALLA.md eller hig-principer.md kallar en PNG eller PDF en prototyp utan att neka det, och regeln står i kartan och bild.md')
def fall4():
    filer = [metod.KARTA, ROOT / 'kunskap' / 'bild.md', SKILL / 'KALLA.md', ROOT / HIG]
    traffar = {}
    for p in filer:
        for m in meningar(text(p)):
            if re.search(r'\b(PNG|PDF)\b', m) and 'prototyp' in m.lower():
                assert nekar(m), '%s: meningen kallar en PNG eller PDF en prototyp: %s' % (p.name, m[:200])
                traffar.setdefault(p.name, []).append(m)
    assert 'metodkarta.md' in traffar and 'bild.md' in traffar, 'regeln saknas i kartan eller bild.md: %s' % sorted(traffar)
    # inget kompetensblock beskriver canvas-design som prototyp
    for x in kompetens.tolka(text(metod.KARTA)).values():
        for falt in ('uppgift', 'visar'):
            if 'canvas-design' in x[falt].lower():
                for m in meningar(x[falt]):
                    assert 'prototyp' not in m.lower() or nekar(m), (x['id'], m)


# ===== 5. egna_bilder =====
@fall('5 atelje.egna_bilder räknar aldrig ett koncept ur canvas-design som verksamhetens egen bild, med eller utan kolumnen Egen, och de egna bilderna står kvar')
def fall5():
    import atelje
    u = TMP / 'underlag' / 'kv-prov' / 'bilder'
    u.mkdir(parents=True)
    for n in ('jobb-1.jpg', 'hero__koncept-morker.png', 'bg__textur.png', 'env__studie.png'):
        (u / n).write_bytes(b'\x89PNG\r\n\x1a\n')
    spara = atelje.UNDERLAG
    atelje.UNDERLAG = TMP / 'underlag'
    try:
        # tabell utan kolumnen Egen: förr räknades varje rad som inte nämnde stock eller genererad som egen
        (u / 'BILDER.md').write_text(
            '# Bilder\n\n| fil | källa | visar | datum | kvalitet |\n|---|---|---|---|---|\n'
            '| jobb-1.jpg | kundens egen kamera | ett jobb | 2026-09-01 | bra |\n'
            '| hero__koncept-morker.png | canvas-design @ 683bc88, filosofi morker.md, k01 v3 | koncept för första vyn | 2026-10-07 | prövad |\n'
            '| bg__textur.png | genererad textur | bakgrund | 2026-10-07 | ok |\n'
            '| env__studie.png | kompositionsstudie, ett koncept ur skillen | miljö | 2026-10-07 | ok |\n', encoding='utf-8')
        assert atelje.egna_bilder('kv-prov') == ['jobb-1.jpg'], atelje.egna_bilder('kv-prov')
        # tabell med kolumnen Egen: ett koncept märkt ja av misstag räknas ändå inte
        (u / 'BILDER.md').write_text(
            '# Bilder\n\n| fil | källa | visar | Egen |\n|---|---|---|---|\n'
            '| jobb-1.jpg | kundens egen kamera | ett jobb | ja |\n'
            '| hero__koncept-morker.png | canvas-design @ 683bc88 | koncept | ja |\n'
            '| env__studie.png | studie | miljö | nej |\n', encoding='utf-8')
        assert atelje.egna_bilder('kv-prov') == ['jobb-1.jpg'], atelje.egna_bilder('kv-prov')
    finally:
        atelje.UNDERLAG = spara


# ===== 6. formen i bild.md =====
@fall('6 registreringens form för koncept (fil, källa med commit, visar, datum, kvalitet, Egen nej, typsnitten) står i kartans stycke, och bild.md bär regeln och hänvisar dit')
def fall6():
    karta = text(metod.KARTA)
    st = re.search(r'\*\*Grafiska koncept ur canvas-design\*\*(.*?)\n\n', karta, re.S).group(1)
    for ord_ in ('`fil`', '`källa`', 'canvas-design @', '`visar`', '`datum`', '`kvalitet`', '`Egen` nej', 'egna_bilder', 'materialsteget', 'OFL', 'TYPSNITT-IKONER.json'):
        assert ord_.lower() in st.lower(), 'kartans stycke saknar: %s' % ord_
    t = text(ROOT / 'kunskap' / 'bild.md')
    m = re.search(r'^## Grafiska koncept ur canvas-design\n(.*?)(?=^## )', t, re.M | re.S)
    assert m, 'bild.md saknar avsnittet Grafiska koncept ur canvas-design'
    a = m.group(1)
    for ord_ in ('illustrative', 'BILDER.md', '`Egen: nej`', 'egna_bilder', 'kunskap/metodkarta.md'):
        assert ord_ in a, 'bild.md:s avsnitt saknar: %s' % ord_


# ===== 7. kvittot: aktivering, läsning, användning och kvalitet var för sig =====
def logg(namn, rader):
    """En strömmad sessionslogg i transkriptets radformat (bildkedja.lasta: samma format), för kvittot."""
    import json
    p = TMP / namn
    with open(p, 'w', encoding='utf-8') as f:
        for i, (verktyg, indata, svar, fel) in enumerate(rader):
            f.write(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't%d' % i, 'name': verktyg, 'input': indata}]}}) + '\n')
            f.write(json.dumps({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 't%d' % i, 'content': svar, **({'is_error': True} if fel else {})}]}}) + '\n')
    return p


@fall('7 kvittot ur en verklig sessions radformat: en nekad eller misslyckad Skill-aktivering räknas inte, en lyckad gör det, hig-principer.md hel med Read är läst och en delvis läst fil är det inte; aktivering, läsning och användning står skilda från tillämpningen, som kvittot aldrig ser')
def fall7():
    import bildkedja
    hig = str(ROOT / HIG)
    emil = str(ROOT / '.claude' / 'skills' / 'emil-apple-design' / 'SKILL.md')
    misslyckad = logg('misslyckad.jsonl', [
        ('Skill', {'skill': 'canvas-design'}, 'Launching skill: canvas-design', False),
        ('Skill', {'skill': 'emil-apple-design'}, '<tool_use_error>Unknown skill: emil-apple-design</tool_use_error>', True),
        ('Read', {'file_path': hig}, text(hig), False),
        ('Read', {'file_path': emil, 'offset': 1, 'limit': 20}, 'början', False)])
    lyckad = logg('lyckad.jsonl', [
        ('Read', {'file_path': emil}, text(emil), False),
        ('Read', {'file_path': hig}, text(hig), False)])
    loggar = {'11111111-1111-4111-8111-111111111111': misslyckad, '22222222-2222-4222-8222-222222222222': lyckad}
    spara = bildkedja.transkript
    bildkedja.transkript = lambda s: loggar.get(s)
    try:
        kv = kompetens.kvitto(['11111111-1111-4111-8111-111111111111'], 'granskning')
        assert kv['verifierad'] and kv['lasta'] == [HIG], kv
        assert kv['skill_anrop'] == ['canvas-design'], 'en misslyckad aktivering räknas som anrop: %s' % kv['skill_anrop']
        assert '.claude/skills/emil-apple-design/SKILL.md' not in kv['valda'], 'en misslyckad aktivering och en delvis läsning gör alternativet valt: %s' % kv['valda']
        g = next(r for r in kv['tillstand'] if r['roll'] == 'granskning')
        assert g['karna']['lasta'] == 1 and g['karna']['filer'] == len(kompetens.lasfiler('granskning')), g['karna']
        assert g['skillverktyget']['anrop'] == [] and g['alternativ']['valda'] == [], (g['skillverktyget'], g['alternativ'])
        assert g['tillampning'] == kompetens.TILLSTAND['ej_observerat'], g['tillampning']
        ml = bildkedja.metodlasning('11111111-1111-4111-8111-111111111111', kompetens.lasfiler('granskning') + kompetens.valbara('granskning'))
        assert ml['delvis'] == ['.claude/skills/emil-apple-design/SKILL.md'] and ml['skill_anrop'] == ['canvas-design'], ml
        # komposition i skissen: canvas-design är ett valt alternativ (läst via aktiveringen), kärnan oläst, tillämpningen aldrig i kvittot
        kv2 = kompetens.kvitto(['11111111-1111-4111-8111-111111111111'], 'skapa')
        ko = next(r for r in kv2['tillstand'] if r['roll'] == 'komposition')
        assert kv2['valda'] == ['.claude/skills/canvas-design/SKILL.md'] and ko['skillverktyget']['anrop'] == ['canvas-design'], (kv2['valda'], ko['skillverktyget'])
        assert ko['alternativ']['tillstand'] == kompetens.LASKVITTO and ko['tillampning'] == kompetens.TILLSTAND['ej_observerat'], ko
        # K46: hela Read av den väntande skillen väljer alternativet utan Skill-aktivering
        kv3 = kompetens.kvitto(['22222222-2222-4222-8222-222222222222'], 'granskning')
        g3 = next(r for r in kv3['tillstand'] if r['roll'] == 'granskning')
        assert kv3['valda'] == ['.claude/skills/emil-apple-design/SKILL.md'] and g3['skillverktyget']['anrop'] == [], (kv3['valda'], g3['skillverktyget'])
        assert g3['alternativ']['tillstand'] == kompetens.LASKVITTO and g3['tillampning'] == kompetens.TILLSTAND['ej_observerat'], g3
    finally:
        bildkedja.transkript = spara
    # prompten säger samma sak till varje pass: en skill aktiveras med Skill-verktyget, en referensfil läses hel med Read, en
    # nekad eller misslyckad laddning skrivs i svaret, och kvittot visar aldrig tillämpningen (ägarens förtydligande)
    for pass_ in ('skapa', 'fordjupa', 'granskning', 'skisskritik', 'forska'):
        p = ' '.join(kompetens.prompt_rader(pass_, 'kv-prov', 'k01'))
        for fras in ('aktiverar du med Skill-verktyget', 'HEL med Read', 'nekas eller misslyckas', 'aldrig tillämpningen'):
            assert fras in p, '%s: prompten saknar "%s"' % (pass_, fras)


@fall('8 HIG översätts till webb: fokusmönster, CSS-mått, förstoring och provens räckvidd')
def fall8():
    t = text(ROOT / HIG)
    fel = []
    for gammalt in ('WCAG 2.2 AA genom axe', 'markeringen döljs', 'en öppen\n  meny håller fokus',
                    'motsvarar en punkt i stort en CSS-pixel', 'reflow 320 visar förstoringen',
                    '4,5:1 för text upp till 17 pt', 'Inget rör sig av sig självt utan paus'):
        if gammalt in t: fel.append(gammalt)
    for krav in ('disclosure', 'modal dialog', '200 %', '1.4.4', '1.4.10', '24 CSS-px', '14 pt',
                 'fem sekunder', 'parallellt', 'automatisk uppdatering', 'mänsklig'):
        if krav not in t: fel.append('saknar avgränsning: '+krav)
    assert not fel,fel


@fall('9 laddning kräver matchat lyckat svar före ändringen, inte bara anropet; samma regel för Read')
def fall9():
    import json
    import bildkedja
    p = TMP / 'ordning.jsonl'
    skillfil = '.claude/skills/canvas-design/SKILL.md'
    prefix = 'kunder/kv-prov/kandidater/k01/sajt/src/'
    def use(namn, data, id_='s1'):
        return {'type': 'tool_use', 'id': id_, 'name': namn, 'input': data}
    svar = {'type': 'tool_result', 'tool_use_id': 's1', 'content': 'ok'}
    skriv = use('Write', {'file_path': prefix + 'index.astro'}, 'w1')
    spara = bildkedja.transkript
    bildkedja.transkript = lambda _: p
    fel = []
    try:
        for namn, data, fil in (('Skill', {'skill': 'canvas-design'}, skillfil), ('Read', {'file_path': HIG}, HIG)):
            anrop = use(namn, data)
            for lage, sekvens in (('saknas', [anrop]), ('efter', [anrop, skriv, svar]), ('fore', [anrop, svar, skriv])):
                p.write_text(''.join(json.dumps({'type': 'assistant' if x['type'] == 'tool_use' else 'user', 'message': {'content': [x]}}) + '\n' for x in sekvens))
                m = bildkedja.metodlasning('syntetisk', [fil], skrivprefix=prefix)
                if m[lage] != [fil] or (lage == 'saknas' and m['skill_anrop']):
                    fel.append((namn, lage, m))
                kv = kompetens.kvitto(['syntetisk'], 'skapa', skrivprefix=prefix)
                if namn == 'Skill' and lage == 'saknas' and skillfil in kv['valda']:
                    fel.append('obesvarad laddning blev valt alternativ')
    finally:
        bildkedja.transkript = spara
    assert not fel, fel


@fall('10 dokumenterad konceptkatalog håller studier och skapartext utanför blindkritiken, kundmaterial är läsbart')
def fall10():
    import fnmatch
    import kandidater
    import atelje
    karta = text(metod.KARTA)
    stycke = re.search(r'\*\*Grafiska koncept ur canvas-design\*\*(.*?)\n\n', karta, re.S).group(1)
    m = re.search(r'registreras i `([^`]*BILDER\.md)`', stycke)
    assert m, 'lagringsvägen saknas'
    # Följ dokumentationens faktiska väg; den gamla delade bilder/ faller genom samma blindningsfunktion.
    vag = m.group(1).replace('underlag/<slug>/', '').replace('<id>', 'k02')
    spara = atelje.ROOT, atelje.UNDERLAG, atelje.KUNDER
    egen = TMP / 'blindrot'
    atelje.ROOT, atelje.UNDERLAG, atelje.KUNDER = egen, egen / 'underlag', egen / 'kunder'
    try:
        u = atelje.UNDERLAG / 'kv-prov'
        for kid in ('k01', 'k02'):
            (kandidater.kdir('kv-prov', kid) / 'bilder').mkdir(parents=True)
        register = u / vag
        register.parent.mkdir(parents=True, exist_ok=True)
        register.write_text('Syntetisk avsikt från annan kandidat, inte kundfakta.')
        studie = register.with_name('hero__koncept-prov.png')
        studie.write_bytes(b'prov')
        (u / 'bilder').mkdir(exist_ok=True)
        kundbild = u / 'bilder' / 'egen-prov.png'
        kundbild.write_bytes(b'prov')
        regler = kandidater.blind_nekas('kv-prov', 'k01', ('bilder',))
        def nekad(p):
            rel = p.relative_to(egen).as_posix()
            return any(fnmatch.fnmatchcase(rel, r[len('Read(./'):-1]) for r in regler if r.startswith('Read(./'))
        assert nekad(register) and nekad(studie), (vag, regler)
        assert not nekad(kundbild), 'kundens verifierade material stängdes av'
        assert nekad(u / 'atelje/kandidater/k03/koncept/ny-studie.png'), 'framtida studie saknar förbud'
        assert nekad(u / 'atelje/kandidater/k01/koncept/BILDER.md'), 'skaparens egna förklaringar saknar förbud'
        for f in (ROOT / 'kunskap/bild.md', SKILL / 'KALLA.md'):
            assert 'koncept/BILDER.md' in text(f), f
    finally:
        atelje.ROOT, atelje.UNDERLAG, atelje.KUNDER = spara


print('canvas-design och HIG: %d fall, %d föll' % (10, len(FEL)), file=sys.stderr)
sys.exit(1 if FEL else 0)
