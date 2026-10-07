#!/usr/bin/env python3
"""kompetens.py — rollerna i skapandeflödet (kunskap/metodkarta.md, avsnittet Kompetenserna): vilken roll som arbetar i
vilket pass, med vilken kärna (läses hel), vilka alternativ (väljs efter riktningen och läses hela), vilka verktyg och
vilka MCP:er. Samma block ger sessionens behörigheter och raderna i passets uppdrag: en källa.

Ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA". Ägarens uppdrag 18:53Z, punkt 5:
varje roll läser de fullständiga relevanta delarna, utan tunna sammanfattningar och utan att varje metodtext läggs i
varje uppdrag. Codex via ägaren 19:04Z, punkt 7: en sammanhängande tillämpning per riktning, full tillgång till
alternativen och fullständig läsning av den valda metoden.

    .venv/bin/python kontroller/kompetens.py --prova       (varje block går att läsa och varje fil finns; slutkod 0/1)
    .venv/bin/python kontroller/kompetens.py --visa skapa   (passets roller, filer, verktyg och storlek)

Blocken i kartan, ett per roll:

    ```kompetens <id>
    namn: …
    uppgift: …
    pass: skapa, fordjupa
    kärna: refero-design/SKILL.md; impeccable/reference/craft-floor.md; kunskap/bild.md
    välj: taste-minimalist/SKILL.md; hallmark/references/macrostructures.md
    verktyg: uxsok, förhandsvisning, detektor, design
    mcp: refero, mobbin
    visar: …
    ```

MCP:erna står aldrig i --allowedTools: kundvakten (kontroller/kundvakt.py) öppnar varje rent anrop uttryckligen, och en
vakt som inte kan pröva lämnar anropet åt dontAsk, som nekar det (granskning 4, G3).

Besluten om tjänsternas upptäckta verktyg står i samma avsnitt, ett block per tjänst och en rad per verktyg (ägarens
uppdrag 2026-10-07, punkt 2 och 3): uppgift, eller ingen uppgift med skäl och provdatum. Verktygen med uppgift är exakt
de som kundvakten släpper (referenstjanster.TJANSTER); prova() säger till när kartan och listan skiljer sig.

    ```tjanstverktyg refero
    refero_search_styles: uppgift — …
    refero_search_apps: ingen uppgift — <skäl>; prövat 2026-10-07
    ```

Tillståndsorden (TILLSTAND) är en källa för startkvittot och kompetensens kvitton; tillstand() ger kompetenskvittot i
dem. Ett läskvitto är belägg för läsning, inte för tillämpning.

Sessionerna som bedömer eller forskar (ägarens ord 2026-10-07: "Du behöver ju fixa luckan där med de verktyg vi har
tillgängliga"): researchen (forska), skisskritiken, jämförelsen och granskningens två pass i läget full (kritik_a,
kritik_b) har egna pass. I de granskande passen (GRANSKANDE) är förhandsvisningen och detektorn granskarens form
(GRANSKARVERKTYG: egen katalog, ingen kod), och ett blint pass (BLINDA) får bara verktyg som aldrig ger kod eller
skaparens text (BLINDSAKRA); prova() fäller ett annat. Kvittot räknar verktygsanropen ur transkriptet med utfall
(verktyg_anrop). Varje session i kandidatflödet (kandidater.py, atelje.session) har ett block eller ett skäl i kartans
lista över sessioner utan block; prova() jämför listan med koden (sessionsfel):

    ```sessioner-utan-block
    <funktionen i kandidater.py>: <skälet, prövbart>
    ```
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metod  # noqa: E402  kalla(): repots kunskap/ eller en skills fil

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r'^```kompetens[ \t]+(?P<id>[a-z]+)[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)
PASS = ('forbered', 'planera', 'planprovning', 'skapa', 'fordjupa', 'rorelse', 'granskning', 'forska', 'skisskritik', 'jamforelse', 'kritik_a', 'kritik_b')
PASSNAMN = {'forbered': 'förberedelsen av kundunderlaget', 'planera': 'planeringen', 'planprovning': 'planprövningen', 'skapa': 'skissen', 'fordjupa': 'fördjupningen',
            'rorelse': 'interaktion och rörelse', 'granskning': 'tillgänglighet och visuell granskning',
            'forska': 'researchen', 'skisskritik': 'skisskritiken', 'jamforelse': 'jämförelsen',
            'kritik_a': 'granskningens första pass', 'kritik_b': 'granskningens andra pass'}
GRANSKANDE = ('skisskritik', 'jamforelse', 'kritik_a', 'kritik_b')  # bedömer och ändrar aldrig sidan
BLINDA = ('skisskritik', 'kritik_a')  # blinda för skaparens text, uppdrag, referenspaket och kod
FORSKANDE = ('forska', 'forbered')  # forskar och ändrar aldrig sidan
FORHAND = '.venv/bin/python kontroller/forhandsvisa.py <slug> --kandidat <id>'

# verktygen per namn: allowedTools-mönster (slug och kandidat fylls i, aldrig ett fritt *-argument som kan skriva utanför
# den egna kandidaten; granskning 4, G12) och raden i prompten
VERKTYG = {
    'uxsok': (['Bash(.venv/bin/python -B kontroller/uxsok.py *)'],
              'UI UX Pro Max sökning och designsystem (läsande, sparar inget): `.venv/bin/python -B kontroller/uxsok.py "<bransch och '
              'stil>" --design-system` och `--domain <style|color|typography|ux|landing>` (databasen är engelsk; sök med flera ord)'),
    'förhandsvisning': ([], 'förhandsvisningen: `%s` (mobil och dator), `--mellan` för 768, `--sida /<väg>/` för en undersida, och '
                            'interaktionsvägen `--tillstand tangentbord,reflow,reducerad` med `--meny`, `--hover` eller `--fokus` och en '
                            'CSS-väljare' % FORHAND),
    'detektor': (['Bash(.venv/bin/python kontroller/detektor.py <slug> --kandidat <id>)', 'Bash(.venv/bin/python kontroller/detektor.py <slug> --kandidat <id> --json)'],
                 'Impeccables detektor: `.venv/bin/python kontroller/detektor.py <slug> --kandidat <id>` (antimönster och designbrister i den '
                 'byggda sidan); varje fynd prövas mot ägarbesluten och kundens domar innan det rättas'),
    'design': (['Bash(.venv/bin/python kontroller/design.py <slug> --kandidat <id>)', 'Bash(.venv/bin/python kontroller/design.py <slug> --kandidat <id> --skriv)'],
               'DESIGN.md-kontrollen: `.venv/bin/python kontroller/design.py <slug> --kandidat <id> [--skriv]`'),
}
# granskarens form av förhandsvisningen och detektorn, i de granskande passen: bilderna i kandidatens granskare/ (aldrig
# skaparens varv/), alla fyra bredderna med menyn, tangentbordet och reflow, och ingen kod i det som ges tillbaka
GRANSKARVERKTYG = {
    'förhandsvisning': (['Bash(%s --granskare)' % FORHAND, 'Bash(%s --granskare *)' % FORHAND],
                        'förhandsvisningen, granskarens egen: `%s --granskare` (tidsgräns 600000 ms) bygger sidan och fotograferar den i 390, '
                        '768, 1280 och 1440, med menyn klickad i verkligt tillstånd, tangentbordet och reflow 320; bilderna hamnar i kandidatens '
                        'granskare/ och aldrig i skaparens varv, och verktyget ger ingen kod. Lägg till `--sida /<väg>/` för en undersida, eller '
                        '`--hover` och `--fokus` med en CSS-väljare ur det du ser (till exempel \'a[href^="tel:"]\')' % FORHAND),
    'detektor': (['Bash(.venv/bin/python kontroller/detektor.py <slug> --kandidat <id> --granskare)'],
                 'Impeccables detektor, granskarens form: `.venv/bin/python kontroller/detektor.py <slug> --kandidat <id> --granskare` '
                 '(regel, beskrivning och antal i den byggda sidan, utan kodutdrag; kör förhandsvisningen först). Pröva varje regel mot det '
                 'du ser i bilderna och mot ägarbesluten: en regel ur en skills lista är en fråga, aldrig ensam grund för ett problem'),
}
BLINDSAKRA = ('förhandsvisning', 'detektor', 'uxsok')  # i granskarens form ger de aldrig kod eller skaparens text
VERKTYGSKOMMANDO = re.compile(r'(?:^|[\s/])kontroller/(uxsok|forhandsvisa|detektor|design)\.py\b')
SKRIPTVERKTYG = {'uxsok': 'uxsok', 'forhandsvisa': 'förhandsvisning', 'detektor': 'detektor', 'design': 'design'}
MCP = {  # Refero och Mobbin: referenstjänsternas egna verktygslistor (en källa). Trybloom används inte (ägarens ord 2026-10-05)
    'refero': None, 'mobbin': None,
}
MCPNAMN = {'refero': 'Refero (stilar, skärmar, sajter och flöden)', 'mobbin': 'Mobbin (skärmar, sektioner och flöden)'}
# Tillståndsorden (ägarens uppdrag 2026-10-07, punkt 3, ordagrant i minnet; inte observerat skilt från inte gjort enligt
# ägarens tillägg samma dag). Startkvittot och kompetensens kvitton använder bara de här orden för kompetensen och
# underlaget, och inget av dem står för ett annat: en anslutning som finns är inte provad, en provad tjänst är inte
# tilldelad, och ett lyckat anrop är inte en tillämpning.
TILLSTAND = {
    'tillgangligt': 'tillgängligt',               # installerat, anslutet eller upptäckt; inget prov säger att det fungerar i flödet
    'provat': 'provat och fungerande',            # ett prov visade att det fungerar, med tid
    'tilldelat': 'tilldelat en uppgift',          # metodkartan ger det en roll och en uppgift
    'anvant': 'använt med resultat',              # observerat använt, och användningen gav ett svar eller material
    'planerat': 'planerat i ett senare steg',     # hör till ett steg som inte körts än, till exempel researchen
    'blockerat': 'blockerat eller misslyckat',    # ett prov eller en körning visade att det inte fungerar eller inte når fram
    'ej_observerat': 'inte observerat',           # ingen observation finns; säger inte att det inte gjorts
    'ej_gjort': 'inte gjort (observerat)',        # observatören såg sessionen och ingen användning
}
LASBELAGG = 'belägg för läsning, inte för tillämpning'
LASKVITTO = 'läst (%s)' % LASBELAGG
VERKTYGSBLOCK = re.compile(r'^```tjanstverktyg[ \t]+(?P<tjanst>[a-z]+)[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)
BESLUTSRAD = re.compile(r'^(?P<verktyg>[a-z][a-z0-9_]*):\s*(?P<beslut>uppgift|ingen uppgift)\s+—\s+(?P<text>.+?)\s*$')
PROVDATUM = re.compile(r'prövat (20\d\d-\d\d-\d\d)')


def mcp_verktyg(namn):
    if MCP.get(namn) is None:
        import referenstjanster
        return list(referenstjanster.TJANSTER[namn]['verktyg'])
    return list(MCP[namn])


class KompetensFel(Exception):
    pass


def tolka(text=None):
    """{id: {'id', 'namn', 'uppgift', 'pass', 'karna', 'valj', 'verktyg', 'mcp', 'visar'}} ur kartans block. 'läs' är
    det äldre namnet på kärnan."""
    text = metod.KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {}
    for m in BLOCK.finditer(text):
        k = {'id': m.group('id')}
        for rad in m.group('rader').splitlines():
            nyckel, _, varde = rad.partition(':')
            k[nyckel.strip()] = varde.strip()
        lista = lambda s, sep: [x.strip() for x in str(s or '').split(sep) if x.strip()]  # noqa: E731
        karna = lista(k.get('kärna') or k.get('läs'), ';')
        ut[k['id']] = {'id': k['id'], 'namn': k.get('namn', k['id']), 'uppgift': k.get('uppgift', ''),
                       'pass': lista(k.get('pass'), ','), 'karna': karna,
                       'valj': [f for f in lista(k.get('välj'), ';') if f not in karna],
                       'verktyg': lista(k.get('verktyg'), ','), 'mcp': lista(k.get('mcp'), ','), 'visar': k.get('visar', '')}
    return ut


def tjanstverktyg(text=None):
    """Besluten om tjänsternas upptäckta verktyg ur kartans block ```tjanstverktyg <tjänst>```: {tjänst: {verktyg:
    {'beslut': 'uppgift' eller 'ingen uppgift', 'text', 'provat'}}}, verktyget utan tjänstens prefix (refero_search_apps,
    search_screens) och provat som datumet efter "prövat" eller None. En rad som inte går att läsa ger 'beslut' None, så
    att prova() kan säga vilken."""
    text = metod.KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {}
    for m in VERKTYGSBLOCK.finditer(text):
        t = ut.setdefault(m.group('tjanst'), {})
        for rad in m.group('rader').splitlines():
            if not rad.strip():
                continue
            b = BESLUTSRAD.match(rad.strip())
            if not b:
                t[rad.strip().split(':', 1)[0].strip() or rad.strip()] = {'beslut': None, 'text': rad.strip(), 'provat': None}
                continue
            d = PROVDATUM.search(b.group('text'))
            t[b.group('verktyg')] = {'beslut': b.group('beslut'), 'text': b.group('text'), 'provat': d.group(1) if d else None}
    return ut


def tjanstverktyg_fel(text=None):
    """Kartans verktygsbeslut mot kundvaktens lista (referenstjanster.TJANSTER): varje verktyg flödet släpper har beslutet
    uppgift, inget verktyg med uppgift saknas i listan, och varje "ingen uppgift" har skäl och provdatum."""
    import referenstjanster
    b, fel = tjanstverktyg(text), []
    for t, d in referenstjanster.TJANSTER.items():
        kort = [v.split('__')[-1] for v in d['verktyg']]
        bt = b.get(t) or {}
        fel += ['%s: %s släpps av kundvakten (referenstjanster.TJANSTER) men har inte beslutet uppgift i metodkartan' % (t, v)
                for v in kort if (bt.get(v) or {}).get('beslut') != 'uppgift']
        for v, x in bt.items():
            if x['beslut'] is None:
                fel.append('%s: raden "%s" går inte att läsa (<verktyg>: uppgift — … eller <verktyg>: ingen uppgift — <skäl>; prövat <datum>)' % (t, x['text'][:80]))
            elif x['beslut'] == 'uppgift' and v not in kort:
                fel.append('%s: metodkartan ger %s en uppgift, men kundvakten släpper det inte (referenstjanster.TJANSTER)' % (t, v))
            elif x['beslut'] == 'ingen uppgift' and (not x['provat'] or len(x['text']) < 40):
                fel.append('%s: %s har ingen uppgift men saknar skäl eller provdatum ("prövat ÅÅÅÅ-MM-DD")' % (t, v))
    fel += ['metodkartans verktygsbeslut gäller en okänd tjänst: %s' % t for t in b if t not in referenstjanster.TJANSTER]
    return fel


def vag(fil):
    """Filens väg relativt repots rot (en skills fil ligger under .claude/skills/)."""
    return metod.kalla(fil).relative_to(metod.ROOT).as_posix()


def storlek(filer):
    """Tecknen i filerna, för redovisningen (räknat källmaterial, inte uppmätt kontext)."""
    n = 0
    for f in filer:
        try:
            n += len((metod.ROOT / f).read_text(encoding='utf-8', errors='replace'))
        except OSError:
            pass
    return n


def prova(text=None):
    """Fel i kompetensblocken: varje fil finns, varje pass, verktyg och MCP är känt, varje pass har en roll, varje
    roll har en uppgift och en kärna, ett blint pass får bara verktyg som aldrig ger kod eller skaparens text, varje
    session i kandidatflödet har ett block eller ett skäl (sessionsfel), och tjänsternas verktygsbeslut stämmer med
    kundvaktens lista."""
    fel = []
    k = tolka(text)
    if not k:
        return ['metodkartan saknar kompetensblock']
    for kid, x in k.items():
        for f in x['karna'] + x['valj']:
            p = metod.kalla(f)
            if not p.is_file() or p.is_symlink():
                fel.append('%s: %s finns inte' % (kid, f))
        fel += ['%s: okänt pass %s' % (kid, p_) for p_ in x['pass'] if p_ not in PASS]
        fel += ['%s: okänt verktyg %s' % (kid, v) for v in x['verktyg'] if v not in VERKTYG]
        fel += ['%s: okänd MCP %s' % (kid, m) for m in x['mcp'] if m not in MCP]
        if not x['uppgift'] or not x['karna']:
            fel.append('%s: uppgiften eller kärnan saknas' % kid)
        for p_ in (p_ for p_ in x['pass'] if p_ in BLINDA):  # ett verktyg som ger kod eller skaparens text är ett läckage
            fel += ['%s: verktyget %s ger den blinda granskaren i %s kod eller skaparens text (blindsäkra: %s)' % (kid, v, p_, ', '.join(BLINDSAKRA))
                    for v in x['verktyg'] if v not in BLINDSAKRA]
    fel += ['passet %s har ingen roll' % p_ for p_ in PASS if not for_pass(p_, k)]
    return fel + sessionsfel(text) + tjanstverktyg_fel(text)


UTANBLOCK = re.compile(r'^```sessioner-utan-block[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)
UTANRAD = re.compile(r'^(?P<sess>[a-z_][a-z0-9_]*):\s*(?P<skal>.*?)\s*$')
TOMT_SKAL = re.compile(r'(?i)^\W*(ingen|saknar|utan)\s+(tilldelning|roll|block|kompetens)\W*$')


def utan_block(text=None):
    """Kartans lista över kandidatflödets sessioner utan kompetensblock: {funktionen i kandidater.py: skälet}."""
    text = metod.KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {}
    for m in UTANBLOCK.finditer(text):
        for rad in m.group('rader').splitlines():
            if rad.strip():
                r = UTANRAD.match(rad.strip())
                ut[r.group('sess') if r else rad.strip()[:60]] = r.group('skal') if r else ''
    return ut


def sessioner_i_koden(fil=None):
    """Varje session i kandidatflödet, ur koden (ast, ingen import): {funktionen i kandidater.py: [{'rad', 'kompetens'}]}
    för varje anrop atelje.session(...), där kompetens säger om verktygsargumentet bär kompetens.verktyg(...), direkt
    eller genom en hjälpfunktion i samma fil (som forfina_verktyg)."""
    import ast
    fil = Path(fil) if fil else Path(__file__).resolve().parent / 'kandidater.py'
    trad = ast.parse(fil.read_text(encoding='utf-8'))
    funktioner = {n.name: n for n in ast.walk(trad) if isinstance(n, ast.FunctionDef)}

    def bar(nod, sett=()):
        for x in ast.walk(nod):
            if not isinstance(x, ast.Call):
                continue
            f = x.func
            if isinstance(f, ast.Attribute) and f.attr == 'verktyg' and isinstance(f.value, ast.Name) and f.value.id == 'kompetens':
                return True
            if isinstance(f, ast.Name) and f.id in funktioner and f.id not in sett and bar(funktioner[f.id], sett + (f.id,)):
                return True
        return False
    ut = {}
    for namn, fn in funktioner.items():
        for x in ast.walk(fn):
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'session' \
                    and isinstance(x.func.value, ast.Name) and x.func.value.id == 'atelje':
                arg = x.args[1] if len(x.args) > 1 else next((k_.value for k_ in x.keywords if k_.arg == 'verktyg'), None)
                ut.setdefault(namn, []).append({'rad': x.lineno, 'kompetens': arg is not None and bar(arg)})
    return ut


def sessionsfel(text=None, fil=None):
    """Kartans lista över sessioner utan block mot koden: en session utan block står i listan med ett prövbart skäl (inte
    "ingen tilldelning"), och listan nämner bara sessioner som finns och saknar block (ägarens ord 2026-10-07)."""
    lista_, kod = utan_block(text), sessioner_i_koden(fil)
    fel = []
    for f, anrop in sorted(kod.items()):
        utan = [a for a in anrop if not a['kompetens']]
        if utan and f not in lista_:
            fel.append('sessionen %s (kandidater.py rad %s) har inget kompetensblock och inget skäl i metodkartans lista över sessioner '
                       'utan block' % (f, ', '.join(str(a['rad']) for a in utan)))
        elif f in lista_ and not utan:
            fel.append('sessionen %s står i listan över sessioner utan block men får ett kompetensblock i koden' % f)
    for f, skal in sorted(lista_.items()):
        if f not in kod:
            fel.append('listan över sessioner utan block nämner %s, som inte startar någon session i kandidater.py' % f)
        elif len(skal) < 60 or TOMT_SKAL.match(skal):
            fel.append('sessionen %s saknar ett prövbart skäl i listan över sessioner utan block ("%s"); "ingen tilldelning" är inget skäl' % (f, skal[:60]))
    return fel


def for_pass(pass_, k=None):
    k = tolka() if k is None else k
    return [x for x in k.values() if pass_ in x['pass']]


def lasfiler(pass_, k=None):
    """Kärnan som passet läser hel, i rollernas ordning, utan dubletter (vägar relativt roten)."""
    ut = []
    for x in for_pass(pass_, k):
        for f in x['karna']:
            v = vag(f)
            if v not in ut:
                ut.append(v)
    return ut


def valbara(pass_, k=None):
    """Alternativen i passet (vägar relativt roten), utom det som redan är kärna."""
    karna, ut = set(lasfiler(pass_, k)), []
    for x in for_pass(pass_, k):
        for f in x['valj']:
            v = vag(f)
            if v not in karna and v not in ut:
                ut.append(v)
    return ut


def verktygsform(pass_, v):
    """(allowedTools-mönster, raden i uppdraget) för verktyget i passet: granskarens form i de granskande passen."""
    return GRANSKARVERKTYG.get(v, VERKTYG[v]) if pass_ in GRANSKANDE else VERKTYG[v]


def verktyg(pass_, slug, kid=None, k=None):
    """allowedTools-mönster för passets verktyg (utöver passets egna skriv- och byggverktyg). Skillverktyget och
    verktygssökningen alltid; MCP:erna aldrig (kundvakten öppnar dem anrop för anrop). Ett verktyg som gäller en
    kandidat ges bara med kandidaten. I de granskande passen är förhandsvisningen och detektorn granskarens form."""
    ut = ['Skill', 'ToolSearch']
    for x in for_pass(pass_, k):
        for v in x['verktyg']:
            for m in verktygsform(pass_, v)[0]:
                if '<id>' in m and not kid:
                    continue
                ut.append(m.replace('<slug>', slug).replace('<id>', kid or ''))
    return list(dict.fromkeys(ut))


def mcp_for_pass(pass_, k=None):
    """MCP-verktygen passet har tillgång till genom kundvakten (för kvittot och prompten)."""
    ut = []
    for x in for_pass(pass_, k):
        for m in x['mcp']:
            ut += mcp_verktyg(m)
    return list(dict.fromkeys(ut))


def prompt_rader(pass_, slug, kid=None, k=None):
    """Raderna i passets uppdrag: varje roll med sin uppgift, kärnan som läses hel, alternativen att välja bland,
    verktygen, MCP:erna och vad passet visar."""
    k = tolka() if k is None else k
    roller = for_pass(pass_, k)
    if pass_ in GRANSKANDE + FORSKANDE:  # passet ändrar aldrig sidan: läs före bedömningen eller frågorna, inget om att rätta
        rader = ['Rollerna i %s (kunskap/metodkarta.md, Kompetenserna) är dina arbetsinstruktioner. Läs varje rolls kärna HEL med' % PASSNAMN[pass_],
                 'Read innan du %s (en fil större än en läsning läses i delar med offset och limit tills alla rader är' % (
                     'bedömer något' if pass_ in GRANSKANDE else 'skriver frågorna och antagandena'),
                 'lästa), eller ladda skillen med skillverktyget. Välj sedan bland alternativen de som passar %s, läs dem hela,' % (
                     'det du bedömer' if pass_ in GRANSKANDE else 'kunden och riktningarna'),
                 'och skriv valet med skäl, eller varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller',
                 'kundens behov avgörs av metodkartans Avgöranden, designreglerna och kundens aktuella domar: en skills lista över',
                 'förbjudna drag (paletter, typsnitt, centrering, etiketter över rubriker, gradienter) är granskningsfrågan "valt av',
                 'vana utan skäl?", aldrig ensam grund för ett fynd. Beskriver en skill ett eget arbetsflöde (underagenter, källkod,',
                 'frågor till användaren, sparade rapporter) gäller dess bedömning, inte flödet: du arbetar i den här sessionen med',
                 'verktygen nedan och svarar i schemat.']
    else:
        rader = ['Rollerna i %s (kunskap/metodkarta.md, Kompetenserna) är dina arbetsinstruktioner. Läs varje rolls kärna HEL med' % PASSNAMN[pass_],
                 'Read innan du ändrar något (en fil större än en läsning läses i delar med offset och limit tills alla rader är lästa),',
                 'eller ladda skillen med skillverktyget. Välj sedan bland alternativen de som passar riktningen, läs dem hela, och skriv',
                 'valet med skäl, eller varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller kundens behov',
                 'avgörs av Avgörandena i metoden, designreglerna och kundens aktuella domar ovan. Följ arbetsflödet: rätt metod för',
                 'uppgiften, craft-floor.md direkt före ändringar i gränssnittet, och kontroll i avgränsade omgångar (bygg, inspektera',
                 'mobil och dator tillsammans, rätta allt i en omgång, bekräfta högst en gång till).']
    for x in roller:
        rader += ['', '%s: %s' % (x['namn'], x['uppgift'])]
        rader.append('- kärnan, läs hel: ' + ', '.join(vag(f) for f in x['karna']))
        if x['valj']:
            rader.append('- alternativen, välj efter %s: ' % ('det du bedömer' if pass_ in GRANSKANDE else 'riktningen') + ', '.join(vag(f) for f in x['valj']))
        for v in x['verktyg']:
            if v == 'design' and not kid:
                continue
            rader.append('- verktyg: ' + verktygsform(pass_, v)[1].replace('<slug>', slug).replace('<id>', kid or '<id>'))
        if not x['verktyg'] and pass_ in GRANSKANDE + FORSKANDE:
            rader.append('- verktyg: inga utöver läsningen (metodkartan säger varför)')
        if x['mcp']:
            # frågorna är alltid generiska (ägarens regel: Refero och Mobbin ska fortsatt få generiska researchfrågor utan
            # kunduppgifter); skaparna når Mobbin sedan 2026-10-07 (atelje.session_args), och kundvakten håller båda reglerna
            rader.append('- MCP: ' + ', '.join(MCPNAMN[m] for m in x['mcp']) + '; frågorna är alltid generiska: bransch och uppgift, aldrig'
                         ' kundens namn, ort, webbadress eller nummer, personnamn, citat eller kundens egna texter, och task_intent'
                         ' bara bransch och uppgift (kundvakten prövar varje anrop och stoppar sådana)' +
                         ('; Mobbins search_screens kräver mode "standard": ett anrop utan mode eller med deep stoppas (deep kostar'
                          ' krediter)' if 'mobbin' in x['mcp'] else ''))
        rader.append('- passet visar: ' + x['visar'])
    return rader


MED_INNEHALL = ('bild returnerad', 'anrop lyckades')  # observatörens utfall för ett MCP-svar med innehåll (observation.svar)


def kvitto(sessioner, pass_, skrivprefix=None, k=None):
    """Kvittot ur transkripten: kärnan som lästs hel före första ändringen (eller alls), alternativen som lästs,
    skillverktygets lyckade anrop och MCP-anropen som gav svar (ett nekat eller stoppat anrop räknas inte; granskning 4,
    G7). Flera sessioner (ett omförsök) räknas tillsammans. Ett transkript som saknas gör kvittot ej verifierat. En
    kärnfil som metodfilen levererade hel med samma sha är läst när metodfilen lästs hel (bildkedja.levererade_hela);
    ett alternativ är valt bara när sessionen själv läste det. Ur observatören (observation.py) också varje MCP-svars
    utfall (bild returnerad, anrop lyckades, tomt resultat, fel, nekat) och sessionens MCP-läge, så att ett tomt svar och
    en tjänst som sessionen aldrig fick inte ser ut som använda (granskningen GR-20261007-r102, B3)."""
    import bildkedja
    filer, val = lasfiler(pass_, k), valbara(pass_, k)
    lasta, fore, skill, mcp, sedda, egna = set(), set(), [], [], 0, set()
    utfall, lage, observerad, verktyg_anrop = {}, {}, True, {}
    for s in sessioner:
        sid = s.get('session_id') if isinstance(s, dict) else s
        ml = bildkedja.metodlasning(sid, filer + val, skrivprefix=skrivprefix)
        if not ml.get('verifierad'):
            continue
        sedda += 1
        fore.update(ml.get('fore') or [])
        lasta.update((ml.get('fore') or []) + (ml.get('efter') or []))
        egna.update(set((ml.get('fore') or []) + (ml.get('efter') or [])) - set(ml.get('via_metod') or []))
        skill += ml.get('skill_anrop') or []
        t = bildkedja.transkript(sid)
        h = bildkedja.handelser(t) if t else []
        felade = {x[1] for x in h if x[0] == 'svar' and x[3]}
        svarade = {x[1] for x in h if x[0] == 'svar'}
        for x in h:
            if x[0] == 'anrop' and str(x[2]).startswith('mcp__') and x[1] not in felade:
                mcp.append(str(x[2]))
            elif x[0] == 'anrop' and x[2] == 'Bash':  # flödets verktyg, med utfall: ett svar utan fel, ett fel eller inget svar
                m_ = VERKTYGSKOMMANDO.search(str((x[3] or {}).get('command') or ''))
                if m_:
                    va = verktyg_anrop.setdefault(SKRIPTVERKTYG[m_.group(1)], {'anrop': 0, 'ok': 0, 'fel': 0})
                    va['anrop'] += 1
                    if x[1] in felade:
                        va['fel'] += 1
                    elif x[1] in svarade:
                        va['ok'] += 1
        ob = None
        try:
            import observation
            ob, _skal = observation.observerad(t, None, 'transkriptet') if t else (None, None)
        except Exception:  # noqa: BLE001 — utan observatören står utfallet och läget som inte observerade
            ob = None
        if not ob:
            observerad = False
            continue
        for a_ in ob.get('mcp') or []:
            namn_ = 'mcp__%s__%s' % (a_.get('tjanst'), a_.get('verktyg'))
            utfall.setdefault(namn_, {})[a_.get('utfall')] = utfall.get(namn_, {}).get(a_.get('utfall'), 0) + 1
        if ob.get('mcp_lage') is None:
            observerad = False
        for s_, st_ in (ob.get('mcp_lage') or {}).items():  # ansluten i någon av sessionerna räcker
            lage[s_] = st_ if lage.get(s_) != 'ansluten' else 'ansluten'
    ut = {'verifierad': sedda > 0, 'filer': filer, 'lasta': [f for f in filer if f in lasta], 'saknas': [f for f in filer if f not in lasta],
          'fore_forsta_andring': [f for f in filer if f in fore], 'valda': [f for f in val if f in egna],
          'skill_anrop': sorted(set(skill)), 'mcp_anrop': {m: mcp.count(m) for m in sorted(set(mcp))}, 'verktyg_anrop': verktyg_anrop}
    if sedda and observerad:  # bara när varje sedd session observerades: annars är utfallet och läget inte kända
        ut['mcp_utfall'], ut['mcp_lage'] = utfall, lage
    ut['tillstand'] = tillstand(ut, pass_, k)
    return ut


def mcp_tillstand(m, anrop, utfall, lage, sett):
    """En tilldelad MCP-tjänsts tillstånd i en roll: blockerat när sessionen inte hade tjänsten (tilldelad men åtkomst
    saknas), använt med resultat bara när ett svar hade innehåll, blockerat när anropen bara gav tomma svar eller fel,
    inte gjort när sessionen sågs utan anrop, och inte observerat när svarens innehåll eller sessionen inte observerades.
    Ett lyckat anrop säger inte att svaret blev användbart material (metodkartan, Tillståndsorden)."""
    ut = {'anrop': anrop}
    if isinstance(lage, dict) and lage.get(m) != 'ansluten':
        return dict(ut, tillstand=TILLSTAND['blockerat'],
                    orsak='tilldelad men åtkomst saknas: sessionen %s, så rollens egna anrop till tjänsten gick inte' % (
                        'hade inte %s' % m if m not in lage else 'hade %s med status %s' % (m, lage[m])))
    if isinstance(utfall, dict):
        egna = {u: n for a, uf in utfall.items() if str(a).startswith('mcp__%s__' % m) for u, n in uf.items()}
        med = sum(n for u, n in egna.items() if u in MED_INNEHALL)
        if med:
            return dict(ut, med_innehall=med, tillstand=TILLSTAND['anvant'])
        if egna:
            return dict(ut, med_innehall=0, tillstand=TILLSTAND['blockerat'],
                        orsak='anrop utan material: %s' % ', '.join('%s %d' % (u, n) for u, n in sorted(egna.items())))
        return dict(ut, tillstand=TILLSTAND['ej_gjort'] if sett else TILLSTAND['ej_observerat'])
    if anrop:  # ett sparat kvitto utan utfallet: svaren kom, men deras innehåll observerades inte
        return dict(ut, tillstand=TILLSTAND['ej_observerat'], orsak='%d anrop med svar; svarens innehåll är inte observerat' % anrop)
    return dict(ut, tillstand=TILLSTAND['ej_gjort'] if sett else TILLSTAND['ej_observerat'])


def verktygstillstand(v, anrop, sett):
    """Ett verktygs tillstånd i en roll ur kvittots verktygsanrop: använt med resultat när ett anrop svarade utan fel,
    blockerat när anropen bara gav fel eller inget svar, inte gjort när sessionen sågs utan anrop, och inte observerat
    när kvittot saknar anropen (ett sparat kvitto från före 2026-10-07) eller sessionen inte sågs."""
    if not isinstance(anrop, dict):
        return TILLSTAND['ej_observerat']
    a = anrop.get(v) or {}
    if a.get('ok'):
        return TILLSTAND['anvant']
    if a.get('anrop'):
        return TILLSTAND['blockerat']
    return TILLSTAND['ej_gjort'] if sett else TILLSTAND['ej_observerat']


def tillstand(kv, pass_, k=None, mcp_lage=None):
    """Kompetenskvittot i tillståndsorden, per roll i passet (ägarens uppdrag 2026-10-07, punkt 3): tilldelat ur
    metodkartan; kärnan, alternativen och skillverktyget som läsning (ett läskvitto är belägg för läsning, inte för
    tillämpning); MCP-tjänsterna enligt mcp_tillstand, med sessionens MCP-läge (mcp_lage, eller kvittots eget) när det
    finns; verktygen i Bash enligt verktygstillstand ur kvittots verktygsanrop (inte observerat i ett kvitto utan dem);
    tillämpningen som inte observerat, eftersom kvittot bara ser läsning och anrop. Fungerar på hela kvittot och på
    urvalet kandidaternas status sparar (verifierad, lasta, saknas, valda, skill_anrop, mcp_anrop)."""
    k = tolka() if k is None else k
    kv = kv if isinstance(kv, dict) else {}
    sett = bool(kv.get('verifierad'))
    inget = TILLSTAND['ej_gjort'] if sett else TILLSTAND['ej_observerat']
    lasta, valda, skill = set(kv.get('lasta') or []), set(kv.get('valda') or []), set(kv.get('skill_anrop') or [])
    mcp = kv.get('mcp_anrop') if isinstance(kv.get('mcp_anrop'), dict) else {}
    lage = mcp_lage if isinstance(mcp_lage, dict) else kv.get('mcp_lage') if isinstance(kv.get('mcp_lage'), dict) else None
    utfall = kv.get('mcp_utfall') if isinstance(kv.get('mcp_utfall'), dict) else None
    va = kv.get('verktyg_anrop') if isinstance(kv.get('verktyg_anrop'), dict) else None
    ut = []
    for x in for_pass(pass_, k):
        karna = [vag(f) for f in x['karna']]
        n = sum(1 for f in karna if f in lasta)
        skills = sorted({f.split('/')[0] for f in x['karna'] + x['valj'] if not f.startswith(('kunskap/', 'kritik/', 'mall/'))})
        anrop = {m: sum(v for a, v in mcp.items() if str(a).startswith('mcp__%s__' % m)) for m in x['mcp']}
        valt = [f for f in (vag(f) for f in x['valj']) if f in valda]
        ut.append({
            'roll': x['id'], 'namn': x['namn'], 'tilldelat': TILLSTAND['tilldelat'],
            'karna': {'filer': len(karna), 'lasta': n, 'tillstand': (LASKVITTO if n == len(karna) else inget if not n else 'läst %d av %d filer (%s)' % (
                n, len(karna), LASBELAGG)) if sett else TILLSTAND['ej_observerat']},
            'alternativ': {'valda': valt, 'tillstand': LASKVITTO if valt else inget},
            'skillverktyget': {'anrop': sorted(s for s in skill if s in skills), 'tillstand': LASKVITTO if skill & set(skills) else inget},
            'mcp': {m: mcp_tillstand(m, a, utfall, lage, sett) for m, a in anrop.items()},
            'verktyg': {v: verktygstillstand(v, va, sett) for v in x['verktyg']},
            'tillampning': TILLSTAND['ej_observerat']})
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='kompetens', description=__doc__.split('\n\n')[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prova', action='store_true')
    g.add_argument('--visa', choices=PASS)
    a = p.parse_args(argv)
    if a.prova:
        fel = prova()
        print('\n'.join('- ' + f for f in fel) if fel else 'kompetenserna håller: %d roller, %d pass' % (len(tolka()), len(PASS)))
        return 1 if fel else 0
    print('\n'.join(prompt_rader(a.visa, '<slug>', '<id>')))
    print('\nverktyg: ' + ', '.join(verktyg(a.visa, '<slug>', '<id>')))
    print('MCP genom kundvakten: ' + ', '.join(mcp_for_pass(a.visa)))
    print('kärnan: %d filer, %d tecken; alternativen: %d filer' % (len(lasfiler(a.visa)), storlek(lasfiler(a.visa)), len(valbara(a.visa))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
