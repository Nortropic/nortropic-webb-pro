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
de som flödet släpper: för Refero och Mobbin kundvakten (referenstjanster.TJANSTER), för Chrome DevTools MCP
inspektionssessionens lista (devtools.VERKTYG; MCP:n körs aldrig i skaparens eller kritikens session); prova() säger
till när kartan och en lista skiljer sig (tjanstregister).

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
PASS = ('forbered', 'planera', 'planprovning', 'skapa', 'fordjupa', 'rorelse', 'granskning', 'forska', 'skisskritik', 'jamforelse', 'kritik_a', 'kritik_b',
        'fore_efter', 'helbygge')
PASSNAMN = {'helbygge': 'helbygget från godkänd startsida', 'forbered': 'förberedelsen av kundunderlaget', 'planera': 'planeringen', 'planprovning': 'planprövningen', 'skapa': 'skissen', 'fordjupa': 'uppdraget',
            'rorelse': 'interaktion och rörelse', 'granskning': 'tillgänglighet och visuell granskning',
            'forska': 'researchen', 'skisskritik': 'skisskritiken', 'jamforelse': 'jämförelsen',
            'kritik_a': 'granskningens första pass', 'kritik_b': 'granskningens andra pass',
            'fore_efter': 'före/efter-bedömningen'}
GRANSKANDE = ('skisskritik', 'jamforelse', 'kritik_a', 'kritik_b', 'fore_efter')  # bedömer och ändrar aldrig sidan
# blinda för skaparens text, uppdrag, referenspaket och kod; före/efter-bedömningen ser bara de två versionernas bilder
# (ägarens uppdrag 2026-10-09, punkt 10: bilderna bedöms före skaparens förklaring)
BLINDA = ('skisskritik', 'kritik_a', 'fore_efter')
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
    # materialsteget, kandidatavgränsat (R05 i GR-20261008-06af6ff-omgranskning-codex): kommandot börjar alltid med kunden och
    # kandidaten, och material.py vägrar en andra --kandidat och en fil utanför kandidatens katalog
    'material': (['Bash(.venv/bin/python kontroller/material.py <slug> --kandidat <id> *)'],
                 'materialsteget (illustrativt och koncept, aldrig verksamhetens egna bilder): `.venv/bin/python kontroller/material.py <slug> '
                 '--kandidat <id> --canvas <fil i kandidatens koncept/ eller kompetens/skillskript/> --bestall "<vad konceptet visar>"` registrerar ett koncept ur '
                 'canvas-design, `--anvand <m-id> --plats <plats>` lägger en genererad tillgång i src/assets/material/ (en video kräver '
                 '`--poster <bild-id>`), `--visa` visar kandidatens egna tillgångar och det gemensamma kundmaterialet, och '
                 '`--anvandning` säger vad som är kopierat, importerat i källan och renderat i bygget; '
                 'en leverantörsbeställning sparas med --leverantor och --bestall (med --fran <m-id> redigeras en egen bild ur '
                 'registret, eller blir den första rutan i en Seedance-video); den betrodda materialkörningen kräver '
                 'konto, uppdragets hash, uttryckligt kostnadsmandat och rättigheter (kunskap/materialtransport.md). '
                 'En väntande beställning är ingen genererad tillgång'),
    # researchrollens webbupptäckt (ägarens uppdrag 2026-10-10 om hela referenskedjan, punkt 2–4): WebSearch och WebFetch
    # ges sessionen genom atelje.session(webb=True), aldrig som allow-regel; kundvakten prövar varje fråga och adress
    'webbsok': ([], 'webbupptäckten: WebSearch (vanlig webbsökning på svenska och engelska efter verkliga verksamhetssajter, '
                    'byråers dokumenterade kundprojekt och gallerier, till exempel "site:awwwards.com/sites keramik" eller '
                    'en branschkategori) och WebFetch (läs en galleriobjektsida eller en sajt för att hitta den verkliga '
                    'adressen, utmärkelsen och vad sidan visar). Frågorna är generiska: bransch, tjänster och besökarens '
                    'uppgift, aldrig kundens namn, ort, adress eller nummer (kundvakten stoppar dem). Varje sökning och '
                    'hämtning bokförs ur transkriptet; en adress ur minnet är en kandidat, aldrig en upptäckt'),
    'skillskript': (['Bash(.venv/bin/python kontroller/skillskript.py <slug> --kandidat <id> --uppdrag *)',
                    'Write(./underlag/<slug>/atelje/kandidater/<id>/kompetens/skriptuppdrag/*.json)',
                    'Edit(./underlag/<slug>/atelje/kandidater/<id>/kompetens/skriptuppdrag/*.json)',
                    'Write(./underlag/<slug>/atelje/kandidater/<id>/koncept/**)',
                    'Edit(./underlag/<slug>/atelje/kandidater/<id>/koncept/**)'],
                   'skillsens körbara hjälpmedel: `.venv/bin/python kontroller/skillskript.py <slug> --kandidat <id> '
                   '--uppdrag <JSON i kandidatens kompetens/skriptuppdrag/>`. Fasta åtgärder för varumärkespalett, tokenexport, tokenkontroll '
                   'och canvas till PNG/PDF; kontrakt och exempel i kunskap/skillskript.md. Resultaten hamnar i kandidatens '
                   'kompetens/skillskript/, aldrig direkt i sajtkoden. Läs och bedöm resultatet före införande'),
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
# ett körkommando (python … kontroller/<verktyg>.py), aldrig en läsning av skriptet med cat, grep eller sed
# (GR-20261008-r117-claude#C7)
VERKTYGSKOMMANDO = re.compile(r'(?:^|[\s;&|(])(?:\S*/)?python[0-9.]*\s+(?:-[A-Za-z]+\s+)*(?:\S*/)?kontroller/(uxsok|forhandsvisa|detektor|design|material|skillskript)\.py\b')
SKRIPTVERKTYG = {'uxsok': 'uxsok', 'forhandsvisa': 'förhandsvisning', 'detektor': 'detektor', 'design': 'design', 'material': 'material', 'skillskript': 'skillskript'}
MCP = {  # Refero och Mobbin: referenstjänsternas egna verktygslistor (en källa). Trybloom används inte (ägarens ord 2026-10-05)
    'refero': None, 'mobbin': None,
    # Motions fria dokumentations-MCP (kontroller/mcp/motion.json; ägarens uppdrag 2026-10-07, punkt 5C, och beslutet "bara den
    # fria delen"): verktygen vid tools/list 2026-10-07. Ingen referenstjänst (inga bilder, researchen frågar den aldrig), så
    # listan står här och inte i referenstjanster.TJANSTER; kundvakten släpper den genom kundvakt.tillatna (mcp_verktyg)
    'motion': ('mcp__motion__search-motion-docs',),
    # 21st.dev Builder (kontroller/mcp/21st.json; ägarens val 2026-10-07, uppdraget 2026-10-08, 2C): verktygen vid tools/list
    # 2026-10-08 (51 på servern; sessionsprovet i rapporten). Rollen komposition söker komponenter generiskt (search, fritt),
    # hämtar en vald komponents kod med källa, licens och beroenden (get_component; åtkomsten avgörs av kontot) och
    # läser inspirationsflödet (get_inspiration); katalogens publicerings-, konto- och videoverktyg har ingen uppgift
    '21st': ('mcp__21st__search', 'mcp__21st__get_component', 'mcp__21st__get_inspiration', 'mcp__21st__get_theme'),
}
MCPNAMN = {'refero': 'Refero (stilar, skärmar, sajter och flöden)', 'mobbin': 'Mobbin (skärmar, sektioner och flöden)',
           'motion': 'Motion (dokumentation och exempel för motion, motion/react och motion-v; den fria servern)',
           '21st': '21st.dev Builder (komponentsök, en vald komponents kod med källa och licens, ett tema som CSS-variabler, inspiration; koden och temat är material att anpassa)'}
REDOVISAT = 'redovisat av sessionen, inte observerat'  # passets egen redovisning (teknikval), skild från observationen
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
VERKTYGSBLOCK = re.compile(r'^```tjanstverktyg[ \t]+(?P<tjanst>[a-z0-9][a-z0-9-]*)[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)  # tjänstnamn med bindestreck (chrome-devtools) eller siffra först (21st)
BESLUTSRAD = re.compile(r'^(?P<verktyg>[a-z][a-z0-9_-]*):\s*(?P<beslut>uppgift|ingen uppgift)\s+—\s+(?P<text>.+?)\s*$')  # bindestreck: search-motion-docs
PROVDATUM = re.compile(r'prövat (20\d\d-\d\d-\d\d)')


def mcp_verktyg(namn):
    if MCP.get(namn) is None:
        import referenstjanster
        return list(referenstjanster.TJANSTER[namn]['verktyg'])
    return list(MCP[namn])


def slappta():
    """{tjänst: [verktyg utan tjänstens prefix]} för varje tjänst kundvakten kan släppa: referenstjänsterna
    (referenstjanster.TJANSTER) och MCP:erna med egen lista här (MCP). En källa för kundvakten (kundvakt.tillatna),
    kartans verktygsbeslut (tjanstverktyg_fel) och startkvittot (startkontroll.tjanstverktyg_rader)."""
    import referenstjanster
    return {t: [v.split('__')[-1] for v in mcp_verktyg(t)] for t in dict.fromkeys(list(MCP) + list(referenstjanster.TJANSTER))}


def teknikval_text(val):
    """Valet CSS, Motion, GSAP eller stilla per beteende ur passets egen redovisning (teknikval i kandidater.PASS_SCHEMA),
    som en rad i kvittot. Det är sessionens redovisning, inte en observation (ägarens uppdrag 2026-10-07, punkt 6 och
    11: observerat arbete skilt från agentens egen redovisning), så raden säger det."""
    rader = ['%s → %s (%s)' % (str(v.get('beteende') or '?')[:60], str(v.get('teknik') or '?'), str(v.get('skal') or '')[:120])
             for v in val if isinstance(v, dict)]
    return '%s: %s' % (REDOVISAT, '; '.join(rader) if rader else 'inget teknikval redovisat')


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
                       'verktyg': lista(k.get('verktyg'), ','), 'mcp': lista(k.get('mcp'), ','),
                       'mcp_krav': lista(k.get('mcp-krav'), ','), 'visar': k.get('visar', '')}
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


def tjanstregister():
    """Tjänsterna med listan över de verktyg flödet släpper, per tjänst: Refero och Mobbin genom kundvakten
    (referenstjanster.TJANSTER) och Chrome DevTools MCP genom inspektionssessionens tillåtelselista (devtools.VERKTYG;
    aldrig i skaparens eller kritikens session). {tjänst: (verktyg utan prefix, var listan står)}."""
    import devtools
    import referenstjanster
    ut = {t: (verktyg, 'kundvakten (referenstjanster.TJANSTER och kompetens.MCP)') for t, verktyg in slappta().items()}
    ut[devtools.TJANST] = ([v.split('__')[-1] for v in devtools.VERKTYG], 'inspektionssessionen (devtools.VERKTYG)')
    return ut


def tjanstverktyg_fel(text=None):
    """Kartans verktygsbeslut mot listorna över vad flödet släpper (tjanstregister): varje verktyg som släpps har
    beslutet uppgift, inget verktyg med uppgift saknas i listan, och varje "ingen uppgift" har skäl och provdatum."""
    b, fel = tjanstverktyg(text), []
    register = tjanstregister()
    for t, (kort, var) in register.items():
        bt = b.get(t) or {}
        fel += ['%s: %s släpps av %s men har inte beslutet uppgift i metodkartan' % (t, v, var)
                for v in kort if (bt.get(v) or {}).get('beslut') != 'uppgift']
        for v, x in bt.items():
            if x['beslut'] is None:
                fel.append('%s: raden "%s" går inte att läsa (<verktyg>: uppgift — … eller <verktyg>: ingen uppgift — <skäl>; prövat <datum>)' % (t, x['text'][:80]))
            elif x['beslut'] == 'uppgift' and v not in kort:
                fel.append('%s: metodkartan ger %s en uppgift, men %s släpper det inte' % (t, v, var))
            elif x['beslut'] == 'ingen uppgift' and (not x['provat'] or len(x['text']) < 40):
                fel.append('%s: %s har ingen uppgift men saknar skäl eller provdatum ("prövat ÅÅÅÅ-MM-DD")' % (t, v))
    fel += ['metodkartans verktygsbeslut gäller en okänd tjänst: %s' % t for t in b if t not in register]
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
        fel += ['%s: MCP-kravet %s saknar tilldelad tjänst' % (kid, m) for m in x.get('mcp_krav', []) if m not in x['mcp']]
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
    eller genom en hjälpfunktion i samma fil (som forfina_verktyg). Ett alias (atelje.session som värde, argument eller
    import) ger en post med 'alias': True, som sessionsfel alltid fäller (GR-20261007-r103#K2)."""
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
    ut, anropade = {}, set()
    for namn, fn in funktioner.items():
        for x in ast.walk(fn):
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'session' \
                    and isinstance(x.func.value, ast.Name) and x.func.value.id == 'atelje':
                anropade.add(id(x.func))
                arg = x.args[1] if len(x.args) > 1 else next((k_.value for k_ in x.keywords if k_.arg == 'verktyg'), None)
                ut.setdefault(namn, []).append({'rad': x.lineno, 'kompetens': arg is not None and bar(arg)})
    # ett alias (s = atelje.session, ett argument eller from atelje import session) startar en session som jämförelsen
    # inte kan följa: det räknas som en session utan block och fälls alltid (GR-20261007-r103#K2)
    omslutande = {}
    for namn, fn in funktioner.items():
        for x in ast.walk(fn):
            omslutande.setdefault(id(x), namn)
    for x in ast.walk(trad):
        alias = (isinstance(x, ast.Attribute) and x.attr == 'session' and isinstance(x.value, ast.Name) and x.value.id == 'atelje'
                 and id(x) not in anropade) or (isinstance(x, ast.ImportFrom) and x.module == 'atelje' and any(a_.name in ('session', '*') for a_ in x.names))
        if alias:
            ut.setdefault(omslutande.get(id(x), '<modulen>'), []).append({'rad': x.lineno, 'kompetens': False, 'alias': True})
    return ut


def sessionsfel(text=None, fil=None):
    """Kartans lista över sessioner utan block mot koden: en session utan block står i listan med ett prövbart skäl (inte
    "ingen tilldelning"), och listan nämner bara sessioner som finns och saknar block (ägarens ord 2026-10-07)."""
    lista_, kod = utan_block(text), sessioner_i_koden(fil)
    fel = []
    for f, anrop in sorted(kod.items()):
        fel += ['sessionen startas genom ett alias för atelje.session i %s (kandidater.py rad %s): jämförelsen med metodkartan kräver '
                'ett direkt anrop' % (f, a['rad']) for a in anrop if a.get('alias')]
        anrop = [a for a in anrop if not a.get('alias')]
        if not anrop:
            continue
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


def aktiverbara(filer):
    """(skills som aktiveras med skillverktyget, filer som läses med Read) för rollens filer: en skill är aktiverbar när
    filen är dess SKILL.md i skillmappens rot (Claude Code känner bara den); referensfiler, nästlade SKILL.md (gsap/gsap-core/)
    och kunskap/, kritik/ läses med Read enligt skillens egna instruktioner. K46:s väntande
    Initial Response-skills läses också med Read, samma klassificering som sessionsnekandet."""
    skills, las = [], []
    vantande = vantande_skills()
    for f in filer:
        delar = f.split('/')
        if len(delar) == 2 and delar[1] == 'SKILL.md' and delar[0] not in ('kunskap', 'kritik', 'mall') and delar[0] not in vantande:
            skills.append(delar[0])
        else:
            las.append(f)
    return list(dict.fromkeys(skills)), las


def aktiveringstext(filer):
    """Raden i uppdraget för en lista filer: vad som aktiveras med Skill (namnet och filen aktiveringen laddar) och vad
    som läses med Read."""
    skills, las = aktiverbara(filer)
    delar = []
    if skills:
        import bildkedja
        delar.append('aktivera med skillverktyget: ' + ', '.join('%s (%s)' % (
            bildkedja.skillkommando(s) or ('OKÄNT SKILLNAMN: ' + s), vag(s + '/SKILL.md')) for s in skills))
    if las:
        delar.append('läs hela med Read: ' + ', '.join(vag(f) for f in las))
    return '; '.join(delar)


def prompt_rader(pass_, slug, kid=None, k=None):
    """Raderna i passets uppdrag: varje roll med sin uppgift, kärnan som läses hel, alternativen att välja bland,
    verktygen, MCP:erna och vad passet visar."""
    k = tolka() if k is None else k
    roller = for_pass(pass_, k)
    if pass_ in GRANSKANDE + FORSKANDE:  # passet ändrar aldrig sidan: läs före bedömningen eller frågorna, inget om att rätta
        rader = ['Rollerna i %s (kunskap/metodkarta.md, Kompetenserna) är dina arbetsinstruktioner. Aktivera varje rolls skills' % PASSNAMN[pass_],
                 'med skillverktyget (Skill) och läs rollens referensfiler HELA med Read innan du %s (en fil' % (
                     'bedömer något' if pass_ in GRANSKANDE else 'skriver frågorna och antagandena'),
                 'större än en läsning läses i delar med offset och limit tills alla rader är lästa); en aktivering eller läsning som',
                 'misslyckas skriver du i svaret innan beroende arbete fortsätter. Välj sedan bland alternativen de som passar %s,' % (
                     'det du bedömer' if pass_ in GRANSKANDE else 'kunden och riktningarna'),
                 'aktivera eller läs dem hela, och skriv valet med skäl, eller varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller',
                 'kundens behov avgörs av metodkartans Avgöranden, designreglerna och kundens aktuella domar: en skills lista över',
                 'förbjudna drag (paletter, typsnitt, centrering, etiketter över rubriker, gradienter) är granskningsfrågan "valt av',
                 'vana utan skäl?", aldrig ensam grund för ett fynd. Beskriver en skill ett eget arbetsflöde (underagenter, källkod,',
                 'frågor till användaren, sparade rapporter) gäller dess bedömning, inte flödet: du arbetar i den här sessionen med',
                 'verktygen nedan och svarar i schemat.']
    else:
        rader = ['Rollerna i %s (kunskap/metodkarta.md, Kompetenserna) är dina arbetsinstruktioner. Aktivera varje rolls skills' % PASSNAMN[pass_],
                 'med skillverktyget (Skill) och läs rollens referensfiler HELA med Read innan du ändrar något (en fil större än en',
                 'läsning läses i delar med offset och limit tills alla rader är lästa); en aktivering eller läsning som misslyckas',
                 'skriver du i svaret innan beroende arbete fortsätter. Välj sedan bland alternativen de som passar riktningen, aktivera',
                 'eller läs dem hela, och skriv valet med skäl, eller varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller kundens behov',
                 'avgörs av Avgörandena i metoden, designreglerna och kundens aktuella domar ovan. Följ arbetsflödet: rätt metod för',
                 'uppgiften, craft-floor.md direkt före ändringar i gränssnittet, och kontroll i avgränsade omgångar (bygg, inspektera',
                 'mobil och dator tillsammans, rätta allt i en omgång).']
    rader += ['Lokala processvillkor gäller även när en skill laddas: ingen svarar i denna session; uppdraget är svaret.',
              'Skills med rubriken Initial Response läses bara med Read, aldrig med Skill. Deras kunskap används,',
              'men det inledande väntesvaret och krav på nya användarsvar utförs inte.']
    if pass_ in ('skapa', 'fordjupa'):
        rader += ['Varven: inget minsta antal i något läge (ägarens uppdrag 2026-10-09). Varje varv är en observerad brist, en ändring',
                  'och en efterkontroll; två varv i rad utan synlig förbättring är rundgång och ett skäl att sluta eller byta grundidé.',
                  'En extern skills varvtak ersätter inte detta, och antal varv bevisar inte kvalitet.']
    elif pass_ in ('rorelse', 'granskning'):
        rader += ['Detta avgränsade specialistpass: rätta i en samlad omgång, bekräfta högst en gång till.']
    rader += ['En aktiverbar SKILL.md aktiverar du med Skill-verktyget, med undantaget för Initial Response ovan; varje referensfil läses HEL med Read.',
              'En aktivering som nekas eller misslyckas redovisas innan beroende arbete fortsätter.',
              'Ett lyckat anrop eller en hel läsning visar laddningen, aldrig tillämpningen eller designkvaliteten.']
    for x in roller:
        rader += ['', '%s: %s' % (x['namn'], x['uppgift'])]
        rader.append('- kärnan, hel före arbetet: ' + aktiveringstext(x['karna']))
        if x['valj']:
            rader.append('- alternativen, välj efter %s: ' % ('det du bedömer' if pass_ in GRANSKANDE else 'riktningen') + aktiveringstext(x['valj']))
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
                          ' krediter)' if 'mobbin' in x['mcp'] else '') +
                         ('; Motions search-motion-docs söker mönstret du bygger (inView, stagger, spring, layout) med platform js'
                          ' eller react, och träffar märkta Motion+ (betalda) används inte' if 'motion' in x['mcp'] else ''))
        if x.get('mcp_krav'):
            rader.append('- obligatorisk undersökning före nästa steg: ' + ', '.join(x['mcp_krav']) +
                         '. Gör generiska sökningar, inspektera resultaten och redovisa vad som valdes eller förkastades och varför.'
                         ' Saknad åtkomst, tomma eller misslyckade resultat är en uppgiftsbrist, aldrig ett genomfört steg.')
        if '21st' in x['mcp']:
            rader.append('- 21st: sök användbara implementationsgrunder innan formen låses; jämför förhandsvisningarna, hämta vald'
                         ' komponent med get_component eller temat med get_theme och kontrollera kod, licens och beroenden.'
                         ' För vidare id, källa, hämtad fil och avsedd användningsplats. Bygg vidare på den hämtade koden och'
                         ' pröva resultatet i mobil och dator. En referensbild är ingen kodmall. Följ projektets befintliga'
                         ' beroendeprocess; kontoåtgärder och extern AI-generering ingår inte.')
        rader.append('- passet visar: ' + x['visar'])
    return rader


def vantande_skills(root=None):
    """K46: väntande skillflöden läses som kunskap, de anropas inte i en obevakad session.

    Både mappens och frontmatterns namn nekas, med och utan argument. Inga upstream-
    filer ändras och Read förblir tillgängligt. Detta prövar argumenten, inte en verklig
    Claude-process; den senare kontrollen ingår i nästa tillåtna sessionsprov.
    """
    ut = {}
    for f in sorted((Path(root or ROOT) / '.claude/skills').glob('*/SKILL.md')):
        text = f.read_text(encoding='utf-8')
        if not re.search(r'^##[ \t]+Initial Response[ \t]*$', text, re.M):
            continue
        namn = {f.parent.name}
        huvud = text.split('---', 2)[1] if text.startswith('---\n') else ''
        m = re.search(r'^name:[ \t]*(.+?)\s*$', huvud, re.M)
        if m:
            namn.add(m.group(1).strip('\"\''))
        for n in namn:
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', n):
                raise ValueError('ogiltigt skillnamn i väntande skill')
        ut[f.parent.name] = sorted(namn)
    return ut


def skill_nekas(root=None):
    """Samma väntande skills som rollraderna och kvittot; båda namnformerna nekas."""
    return sorted({regel for namn in vantande_skills(root).values() for n in namn
                   for regel in ('Skill(%s)' % n, 'Skill(%s *)' % n)})


MED_INNEHALL = ('bild returnerad', 'anrop lyckades')  # observatörens utfall för ett MCP-svar med innehåll (observation.svar)
UTAN_FORM = 'svar utan känd form'  # ett textsvar som varken är fel, tomt eller en läsbar lista: innehållet är inte observerat (C6:s rest)


def kvitto(sessioner, pass_, skrivprefix=None, k=None):
    """Kvittot ur transkripten: kärnan som lästs hel före första ändringen (eller alls), alternativen som lästs,
    skillverktygets lyckade anrop och MCP-anropen som gav svar (ett nekat eller stoppat anrop räknas inte; granskning 4,
    G7). Varje session är en egen kontext (flödet startar varje session på nytt med -p och återupptar aldrig en; R02 i
    GR-20261008-06af6ff-omgranskning-codex): läsningen och läsordningen räknas per session ('per_session'), och kärnan
    står som läst hel, och läst före första ändringen, bara när varje sedd session läste den så. En tidigare sessions
    läsning döljer alltså aldrig att en ny saknar kärnan eller läste den först efter en ändring. Samma session-id två
    gånger är samma kontext och räknas en gång. Alternativen, skillverktyget och MCP-anropen räknas över sessionerna
    (alternativen är valfria; anropen redovisas per session i 'per_session'). Ett transkript som saknas gör kvittot ej verifierat; saknas
    ett av flera står kvittot som ofullständigt ('sessioner': förväntade, sedda och de saknade med skäl), och det som
    inte sågs är då inte observerat, aldrig "inte gjort" (motorinventeringen F04). En
    kärnfil som metodfilen levererade hel med samma sha är läst när metodfilen lästs hel (bildkedja.levererade_hela);
    ett alternativ är valt bara när sessionen själv läste det. Ur observatören (observation.py) också varje MCP-svars
    utfall (bild returnerad, anrop lyckades, tomt resultat, fel, nekat) och sessionens MCP-läge, så att ett tomt svar och
    en tjänst som sessionen aldrig fick inte ser ut som använda (granskningen GR-20261007-r102, B3)."""
    import bildkedja
    filer, val = lasfiler(pass_, k), valbara(pass_, k)
    lasta, fore, skill, skill_fel, mcp, sedda, egna = set(), set(), [], [], [], 0, set()
    utfall, lage, observerad, verktyg_anrop = {}, {}, True, {}
    forvantade, saknade, per, sedda_id, samma = 0, [], [], set(), 0
    for s in sessioner:
        sid = s.get('session_id') if isinstance(s, dict) else s
        if sid and str(sid) in sedda_id:  # samma kontext igen (samma session-id): räknas en gång
            samma += 1
            continue
        forvantade += 1
        if not sid:
            saknade.append({'session': None, 'skal': 'sessionen fick aldrig ett session-id'})
            continue
        sedda_id.add(str(sid))
        ml = bildkedja.metodlasning(sid, filer + val, skrivprefix=skrivprefix)
        if not ml.get('verifierad'):
            saknade.append({'session': str(sid), 'skal': str(ml.get('skal') or 'transkriptet kunde inte läsas')[:200]})
            continue
        sedda += 1
        las_s, fore_s = set((ml.get('fore') or []) + (ml.get('efter') or [])), set(ml.get('fore') or [])
        t = bildkedja.transkript(sid)
        h = bildkedja.handelser(t) if t else []
        # Underagenterna (lucka 1 i GR-20261010-kompetens-integration): varje Task/Agent har en egen kontext som inte
        # ser huvudsessionens skills eller läsningar. Deras egna transkript läses med samma metodkvitto; en underagent
        # som ändrar i koden prövas som en egen session (kravbrister), och en underagent utan transkript är okänd.
        ua = []
        for u in bildkedja.underagenter(sid):
            mu = bildkedja.metodlasning(sid, filer + val, skrivprefix=skrivprefix, fil=u['fil'], kedja=u['kedja'])
            if not mu.get('verifierad'):
                continue
            lu, fu = set((mu.get('fore') or []) + (mu.get('efter') or [])), set(mu.get('fore') or [])
            ua.append({'agent': u['agent'], 'andrade': bool(mu.get('forsta_skrivning')), 'forsta_via': mu.get('forsta_via'),
                       'lasta': [f for f in filer if f in lu], 'fore_forsta_andring': [f for f in filer if f in fu],
                       'skill_anrop': sorted(set(mu.get('skill_anrop') or [])), 'skill_fore': sorted(set(mu.get('skill_fore') or [])),
                       'valda': [f for f in val if f in lu and f not in (mu.get('via_metod') or [])]})
        per.append({'session': str(sid), 'lasta': [f for f in filer if f in las_s], 'saknas': [f for f in filer if f not in las_s],
                    'fore_forsta_andring': [f for f in filer if f in fore_s], 'andrade': bool(ml.get('forsta_skrivning')),
                    'forsta_via': ml.get('forsta_via'), 'bash': ml.get('bash'),
                    'skill_anrop': sorted(set(ml.get('skill_anrop') or [])),
                    'skill_fore': sorted(set(ml.get('skill_fore') or [])),
                    'valda': [f for f in val if f in las_s and f not in (ml.get('via_metod') or [])],
                    'underagenter': ua, 'underagentuppdrag': bildkedja.uppdragsanrop(h)})
        fore.update(ml.get('fore') or [])
        lasta.update((ml.get('fore') or []) + (ml.get('efter') or []))
        egna.update(set((ml.get('fore') or []) + (ml.get('efter') or [])) - set(ml.get('via_metod') or []))
        skill += ml.get('skill_anrop') or []
        skill_fel += ml.get('skill_fel') or []
        felade = {x[1] for x in h if x[0] == 'svar' and x[3]}
        svarade = {x[1] for x in h if x[0] == 'svar'}
        for x in h:
            if x[0] == 'anrop' and str(x[2]).startswith('mcp__') and x[1] not in felade:
                mcp.append(str(x[2]))
            elif x[0] == 'anrop' and x[2] in ('WebSearch', 'WebFetch'):  # researchrollens webbupptäckt, med utfall
                va = verktyg_anrop.setdefault('webbsok', {'anrop': 0, 'ok': 0, 'fel': 0})
                va['anrop'] += 1
                if x[1] in felade:
                    va['fel'] += 1
                elif x[1] in svarade:
                    va['ok'] += 1
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
    alla_lasta = [f for f in filer if per and all(f in p_['lasta'] for p_ in per)]  # läst i varje sedd session (R02)
    alla_fore = [f for f in filer if per and all(f in p_['fore_forsta_andring'] for p_ in per)]
    ut = {'verifierad': sedda > 0, 'filer': filer, 'lasta': alla_lasta, 'saknas': [f for f in filer if f not in alla_lasta],
          'fore_forsta_andring': alla_fore, 'per_session': per, 'samma_kontext': samma, 'valda': [f for f in val if f in egna],
          'skill_anrop': sorted(set(skill)), 'skill_fel': sorted(set(skill_fel)), 'mcp_anrop': {m: mcp.count(m) for m in sorted(set(mcp))},
          'verktyg_anrop': verktyg_anrop, 'sessioner': {'forvantade': forvantade, 'sedda': sedda, 'saknade': saknade},
          'ofullstandig': 0 < sedda < forvantade}
    if sedda and observerad and not saknade:  # bara när varje session sågs och observerades: annars är utfallet och läget inte kända (F04)
        ut['mcp_utfall'], ut['mcp_lage'] = utfall, lage
    ut['tillstand'] = tillstand(ut, pass_, k)
    return ut


def anvandningsnivaer(kv, svar=None, anvanda=None, andrad=None, aterstalld=None):
    """Kompetensens användning i sex nivåer, var och en för sig (ägarens uppdrag 2026-10-09 om ett källförankrat
    arbetssätt, punkt 5): erbjuden (rollens kärna i uppdraget), laddad (kärnan läst hel, ur transkriptet), anrop med
    användbart resultat (verktygs- och MCP-anrop med innehåll; None när rollen inte har något tilldelat), redovisad av
    skaparen (svarets ändringar knutna till en skill), belagd i artefakten (versionen ändrades och står kvar) och effekt
    bedömd (bara av en oberoende bedömning; skaparens eget omdöme står som källa). Värdet är True, False eller None för
    okänt, med källan bredvid. Ett lyckat anrop eller en läst fil visar bara laddningen."""
    so = svar if isinstance(svar, dict) else {}
    verifierad = bool((kv or {}).get('verifierad')) and not (kv or {}).get('ofullstandig')
    skillknutna = [x for x in so.get('kod_andrad') or [] if isinstance(x, dict) and x.get('skill')]
    eget = (so.get('visuell_bedomning') or {}).get('omdome') if isinstance(so.get('visuell_bedomning'), dict) else None
    return {
        'erbjuden': {'varde': bool((kv or {}).get('filer')), 'kalla': 'rollens kärna i passets uppdrag'},
        'laddad': {'varde': (not (kv or {}).get('saknas')) if verifierad else None,
                   'kalla': 'transkriptet: kärnan läst hel' if verifierad else 'transkript saknas eller observationen är ofullständig: okänt'},
        'anrop_med_resultat': {'varde': (bool(anvanda) if anvanda is not None else None) if verifierad else None,
                               'kalla': 'verktygs- och MCP-anrop med innehåll' if anvanda is not None else 'inget verktyg tilldelat eller okänt'},
        'redovisad': {'varde': bool(skillknutna) if so else None, 'kalla': 'svarets ändringar knutna till en skill (skaparens egen redovisning)'},
        'belagd_i_artefakten': {'varde': (bool(andrad) and not aterstalld) if andrad is not None else None,
                                'kalla': 'versionen ändrades och står kvar' + ('; återställd' if aterstalld else '')},
        'effekt_bedomd': {'varde': None, 'kalla': 'ingen oberoende bedömning i passet%s' % (
            ('; skaparens eget omdöme: %s' % eget) if eget else '')},
    }


def sen_karna(kv):
    """Kärnfilerna som en ändrande session läste hela först efter sin första ändring (läsordningen, F05): [] när varje
    session läste kärnan före första ändringen, None när kvittot inte är verifierat (då är ordningen inte observerad).
    Sen läsning är läst kompetens, inte observerad tillämpning; arbete före kärnan godkänns aldrig som genomfört (N03 i
    GR-20261009-natt-omgranskning-codex)."""
    if not isinstance(kv, dict) or not kv.get('verifierad'):
        return None
    fore = set(kv.get('fore_forsta_andring') or [])
    return [f for f in kv.get('lasta') or [] if f not in fore]


def kravbrister(kv, pass_, k=None):
    """Observerade arbetskrav för ett pass, aldrig en dom om designkvalitet.

    Varje ny session måste läsa sin kärna och aktivera aktiverbara skills själv.
    Read ersätter bara Skill för dokument och uttryckligen väntande skills. Ett
    saknat transkript är okänt och får inte passera som komplett kompetens.
    MCP-krav kommer ur rollens mcp-krav, inte ur hela listan av möjligheter.
    """
    if not isinstance(kv, dict) or not kv.get('verifierad') or kv.get('ofullstandig'):
        return ['kompetensen är inte fullständigt observerad: transkript saknas']
    import bildkedja
    k = tolka() if k is None else k
    roller = for_pass(pass_, k)
    if not roller:
        return ['passet saknar kompetensroll: %s' % pass_]
    karnafiler = set(lasfiler(pass_, k))
    fel = ['kärnan saknas: %s' % f for f in sorted(karnafiler - set(kv.get('lasta') or []))]
    skrivande = pass_ not in GRANSKANDE + FORSKANDE + ('planera', 'planprovning')
    if skrivande:
        fel += ['%s (läst först efter första ändringen)' % Path(f).name for f in sen_karna(kv) or []]
    per = kv.get('per_session')
    if not isinstance(per, list) or not per:
        fel.append('aktivering per session är inte observerad')
    else:
        antal = kv.get('sessioner') or {}
        if antal.get('saknade') or antal.get('forvantade') != len(per) or antal.get('sedda') != len(per):
            fel.append('sessionernas antal stämmer inte med aktiveringskvittot')
        karna = [f for r in roller for f in r['karna']]
        alternativ = [f for r in roller for f in r['valj']]
        for i, p in enumerate(per, 1):
            if not isinstance(p, dict):
                fel.append('session %d: ogiltigt aktiveringskvitto' % i)
                continue
            fel += ['session %d: kärnan saknas: %s' % (i, f) for f in sorted(karnafiler - set(p.get('lasta') or []))]
            if not isinstance(p.get('andrade'), bool):
                fel.append('session %d: läsordningen är inte observerad' % i)
            if skrivande and p.get('andrade'):
                fel += ['session %d: %s (läst först efter första ändringen)' % (i, f)
                        for f in sorted(karnafiler - set(p.get('fore_forsta_andring') or []))]
            filer = karna + [f for f in alternativ if vag(f) in (p.get('valda') or [])]
            krav, _ = aktiverbara(filer)
            sedda = {bildkedja.skillnamn(n) for n in p.get('skill_anrop') or []}
            tidiga = {bildkedja.skillnamn(n) for n in p.get('skill_fore') or []}
            for namn in krav:
                if namn not in sedda:
                    fel.append('session %d: Skill-aktivering saknas: %s' % (i, namn))
                elif skrivande and p.get('andrade') and namn not in tidiga:
                    fel.append('session %d: Skill aktiverades inte före första ändringen: %s' % (i, namn))
            fel += underagentbrister(p, i, karnafiler, karna, alternativ)
    for m in dict.fromkeys(m for r in roller for m in r.get('mcp_krav', [])):
        utfall = kv.get('mcp_utfall')
        lyckade = sum(n for a, u in (utfall or {}).items() if a.startswith('mcp__%s__' % m)
                      for t, n in u.items() if t in MED_INNEHALL and isinstance(n, int) and n > 0)
        if not lyckade:
            fel.append('obligatorisk MCP-undersökning saknar observerat resultat: %s' % m)
    return list(dict.fromkeys(fel))


def _redovisade(so):
    """Det en session själv redovisar som valt eller lyckat aktiverat, ur svarets schema: valda (text eller {fil}),
    aktivering med lyckades, och skillen bakom en kodändring. passade_inte är inget påstående om aktivering."""
    if not isinstance(so, dict):
        return [], []
    texter, skills = [], []
    for v in so.get('valda') or []:
        if isinstance(v, str):
            texter.append(v)
        elif isinstance(v, dict) and isinstance(v.get('fil'), str):
            texter.append(v['fil'])
    for v in so.get('aktivering') or []:
        if isinstance(v, dict) and v.get('lyckades') is True and isinstance(v.get('skill'), str):
            skills.append(v['skill'])
    for v in so.get('kod_andrad') or []:
        if isinstance(v, dict) and isinstance(v.get('skill'), str) and v['skill'].strip():
            skills.append(v['skill'])
    return texter, skills


def redovisade_brister(kv, pass_, so, k=None):
    """Fri text om ett valt alternativ eller en lyckad aktivering bevisar ingenting (lucka 2 i
    GR-20261010-kompetens-integration): varje alternativ eller skill som svaret redovisar som valt, aktiverat eller som
    grund för en kodändring måste vara observerat i transkriptet, läst helt eller aktiverat med Skill i någon av passets
    sessioner eller underagenter. Ett namn som inte motsvarar en lokal skill eller en fil i rollen (till exempel CSS)
    prövas inte. Ger bristerna; tom lista när allt redovisat också är observerat eller svaret saknar redovisning."""
    import bildkedja
    texter, skills = _redovisade(so)
    if not texter and not skills:
        return []
    if not isinstance(kv, dict) or not kv.get('verifierad'):
        return ['redovisade skills kan inte prövas: kompetensen är inte observerad']
    k = tolka() if k is None else k
    filer = list(dict.fromkeys([f for r in for_pass(pass_, k) for f in r['karna'] + r['valj']]))
    kontexter = [p for p in kv.get('per_session') or [] if isinstance(p, dict)]
    kontexter += [u for p in kontexter for u in (p.get('underagenter') or []) if isinstance(u, dict)]
    lasta = {f for p in kontexter for f in (p.get('lasta') or []) + (p.get('valda') or [])} | set(kv.get('valda') or [])
    aktiverade = {bildkedja.skillnamn(n) or n for p in kontexter for n in p.get('skill_anrop') or []}

    def observerad(f):
        delar = f.split('/')
        if len(delar) == 2 and delar[1] == 'SKILL.md' and (bildkedja.skillnamn(delar[0]) or delar[0]) in aktiverade:
            return True
        return vag(f) in lasta or f in lasta

    def id_for(f):
        delar = f.split('/')
        ids = {f, vag(f)}
        if len(delar) == 2 and delar[1] == 'SKILL.md':
            ids |= {delar[0], bildkedja.skillnamn(delar[0]) or delar[0]}
        elif delar[-1] == 'SKILL.md':
            ids.add(delar[-2])  # en nästlad skill (gsap/gsap-core/SKILL.md) heter som sin mapp
        elif delar[-1] not in ('index.md', 'README.md', 'SKILL.md'):
            ids.add(delar[-1])  # ett eget filnamn (macrostructures.md); index.md och README.md är tvetydiga
        return {i for i in ids if i}

    fel = []
    for text in texter:
        for f in filer:
            if any(re.search(r'(?<![A-Za-z0-9_.-])%s(?![A-Za-z0-9_-])' % re.escape(i), text) for i in id_for(f)) and not observerad(f):
                fel.append('redovisat alternativ utan observerad läsning eller aktivering: %s' % f)
    for namn in skills:
        kanon = bildkedja.skillnamn(namn.strip().split()[0].strip('/:')) if namn.strip() else None
        if kanon and not (bildkedja.ROOT / '.claude' / 'skills' / kanon / 'SKILL.md').is_file():
            continue  # inget lokalt skillnamn (CSS, ett främmande plugin): prövas inte
        if kanon and kanon not in aktiverade and '.claude/skills/%s/SKILL.md' % kanon not in lasta:
            fel.append('redovisad skill utan observerat Skill-anrop eller läsning: %s' % kanon)
    return list(dict.fromkeys(fel))


def redovisat_i_text(kv, pass_, text, k=None):
    """Alternativ som en fritext (DESIGN.md, rubriken Kompetenserna) nämner utan att de observerats lästa eller
    aktiverade. Bara en iakttagelse: texten får också säga att en skill inte passade, så ett nämnt namn är inget
    påstående om aktivering, och ingenting här räknas som aktivering (lucka 2)."""
    m = re.search(r'^#+\s*Kompetenserna\s*$(.*?)(?=^#+\s|\Z)', text or '', re.M | re.S)
    if not m:
        return []
    rader = [r for r in m.group(1).splitlines() if r.strip() and not re.search(r'passade inte|valdes bort|inte (?:valt|vald|använd)|avstod', r, re.I)]
    return [f.split(': ', 1)[1] for f in redovisade_brister(kv, pass_, {'valda': rader}, k) if ': ' in f]


def underagentbrister(p, i, karnafiler, karna, alternativ):
    """Underagenternas egna krav (lucka 1 i GR-20261010-kompetens-integration): en underagent ser varken huvudsessionens
    skills eller läsningar, så en underagent som ändrar i koden läser kärnan och aktiverar rollens skills själv före sin
    första ändring. En läsande underagent (till exempel ett blint rubrikprov) har inga krav men står i kvittot. Fler
    startade underagenter än observerade transkript är okänt, aldrig genomfört."""
    import bildkedja
    fel = []
    ua = p.get('underagenter') or []
    if not isinstance(ua, list):
        return ['session %d: underagenternas kvitto är ogiltigt' % i]
    if isinstance(p.get('underagentuppdrag'), int) and p['underagentuppdrag'] > len(ua):
        fel.append('session %d: %d underagent(er) utan observerat transkript; deras kontext är okänd' % (i, p['underagentuppdrag'] - len(ua)))
    for u in ua:
        if not isinstance(u, dict) or not u.get('andrade'):
            continue
        namn_u = 'session %d, underagent %s' % (i, str(u.get('agent') or '?')[:12])
        fel += ['%s: ändrade utan kärnan före första ändringen: %s' % (namn_u, Path(f).name)
                for f in sorted(karnafiler - set(u.get('fore_forsta_andring') or []))]
        krav, _ = aktiverbara(karna + [f for f in alternativ if vag(f) in (u.get('valda') or [])])
        tidiga = {bildkedja.skillnamn(n) for n in u.get('skill_fore') or []}
        fel += ['%s: Skill aktiverades inte före första ändringen: %s' % (namn_u, n) for n in krav if n not in tidiga]
    return fel


def mcp_tillstand(m, anrop, utfall, lage, sett):
    """En tilldelad MCP-tjänsts tillstånd i en roll: blockerat när sessionen inte hade tjänsten (tilldelad men åtkomst
    saknas), använt med resultat bara när ett svar hade innehåll, blockerat när anropen bara gav tomma svar eller fel,
    inte gjort när sessionen sågs utan anrop, och inte observerat när svarens innehåll eller sessionen inte observerades
    (också ett svar i en form observatören inte läser, UTAN_FORM).
    Ett lyckat anrop säger inte att svaret blev användbart material (metodkartan, Tillståndsorden)."""
    ut = {'anrop': anrop}
    if isinstance(lage, dict) and lage.get(m) != 'ansluten':
        return dict(ut, tillstand=TILLSTAND['blockerat'],
                    orsak='tilldelad men åtkomst saknas: sessionen %s, så rollens egna anrop till tjänsten gick inte' % (
                        'hade inte %s' % m if m not in lage else 'hade %s med status %s' % (m, lage[m])))
    if isinstance(utfall, dict):
        egna = {}
        for a, uf in utfall.items():
            if str(a).startswith('mcp__%s__' % m):
                for u, n in uf.items():
                    egna[u] = egna.get(u, 0) + n
        med = sum(n for u, n in egna.items() if u in MED_INNEHALL)
        if med:
            return dict(ut, med_innehall=med, tillstand=TILLSTAND['anvant'])
        okanda = sum(n for u, n in egna.items() if u == UTAN_FORM)
        if okanda:  # svaren kom, men i en form observatören inte läser: varken använt med resultat eller blockerat (C6:s rest)
            return dict(ut, med_innehall=0, tillstand=TILLSTAND['ej_observerat'],
                        orsak='%d anrop med svar utan känd form; innehållet är inte observerat' % okanda)
        if egna:
            return dict(ut, med_innehall=0, tillstand=TILLSTAND['blockerat'],
                        orsak='anrop utan material: %s' % ', '.join('%s %d' % (u, n) for u, n in sorted(egna.items())))
        return dict(ut, tillstand=TILLSTAND['ej_gjort'] if sett else TILLSTAND['ej_observerat'])
    if anrop:  # ett sparat kvitto utan utfallet: svaren kom, men deras innehåll observerades inte
        return dict(ut, tillstand=TILLSTAND['ej_observerat'], orsak='%d anrop med svar; svarens innehåll är inte observerat' % anrop)
    return dict(ut, tillstand=TILLSTAND['ej_observerat'])


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
    tillämpningen som inte observerat, eftersom kvittot bara ser läsning och anrop, utom i passet rörelse, där
    sessionens egen redovisning av valet CSS, Motion, GSAP eller stilla per beteende (kvittots teknikval, ur
    kandidater.PASS_SCHEMA) står som just redovisad, inte observerad (ägarens uppdrag 2026-10-07, punkt 5C). Fungerar
    på hela kvittot och på urvalet kandidaternas status sparar (verifierad, lasta, saknas, valda, skill_anrop,
    mcp_anrop, teknikval)."""
    k = tolka() if k is None else k
    kv = kv if isinstance(kv, dict) else {}
    sett = bool(kv.get('verifierad'))
    helt = sett and not kv.get('ofullstandig')  # varje session observerad: först då är ett uteblivet anrop "inte gjort" (F04)
    teknikval = kv.get('teknikval') if pass_ == 'rorelse' and isinstance(kv.get('teknikval'), list) else None
    inget = TILLSTAND['ej_gjort'] if helt else TILLSTAND['ej_observerat']
    fore = set(kv['fore_forsta_andring']) if isinstance(kv.get('fore_forsta_andring'), list) else None  # läsordningen (F05)
    lasta, valda, skill = set(kv.get('lasta') or []), set(kv.get('valda') or []), set(kv.get('skill_anrop') or [])
    skill_fel = set(kv.get('skill_fel') or [])
    vb = kv.get('visuell_bedomning') if isinstance(kv.get('visuell_bedomning'), dict) else None
    mcp = kv.get('mcp_anrop') if isinstance(kv.get('mcp_anrop'), dict) else {}
    lage = mcp_lage if isinstance(mcp_lage, dict) else kv.get('mcp_lage') if isinstance(kv.get('mcp_lage'), dict) else None
    utfall = kv.get('mcp_utfall') if isinstance(kv.get('mcp_utfall'), dict) else None
    va = kv.get('verktyg_anrop') if isinstance(kv.get('verktyg_anrop'), dict) else None
    ut = []
    for x in for_pass(pass_, k):
        karna = [vag(f) for f in x['karna']]
        n = sum(1 for f in karna if f in lasta)
        erbjudna, _ = aktiverbara(x['karna'] + x['valj'])
        skills, _ = aktiverbara(x['karna'] + [f for f in x['valj'] if vag(f) in valda])
        anrop = {m: sum(v for a, v in mcp.items() if str(a).startswith('mcp__%s__' % m)) for m in x['mcp']}
        valt = [f for f in (vag(f) for f in x['valj']) if f in valda]
        mcp_rader = {m: mcp_tillstand(m, a, utfall, lage, helt) for m, a in anrop.items()}
        verktyg_rader = {v: verktygstillstand(v, va, helt) for v in x['verktyg']}
        aktiverade, misslyckade = sorted(s for s in skill if s in erbjudna), sorted(s for s in skill_fel if s in erbjudna)
        n_fore = sum(1 for f in karna if f in fore) if fore is not None else None
        if not helt:  # kärnan för hela passet är okänd när någon session inte observerats
            karna_t = TILLSTAND['ej_observerat']
        elif n == len(karna):  # hel läsning; i ett ändrande pass också ordningen: kärnan före första ändringen (F05)
            karna_t = LASKVITTO if n_fore is None or n_fore == n or pass_ in GRANSKANDE + FORSKANDE else \
                'läst hel, men %d av %d filer först efter första kodändringen (läsordningen; %s)' % (n - n_fore, n, LASBELAGG)
        else:
            karna_t = inget if not n else 'läst %d av %d filer (%s)' % (n, len(karna), LASBELAGG)
        ut.append({
            'roll': x['id'], 'namn': x['namn'], 'tilldelat': TILLSTAND['tilldelat'],
            'karna': {'filer': len(karna), 'lasta': n, 'tillstand': karna_t, **({'fore_forsta_andring': n_fore} if n_fore is not None else {})},
            'alternativ': {'valda': valt, 'tillstand': LASKVITTO if valt else inget},
            'skillverktyget': {'anrop': aktiverade, 'misslyckade': misslyckade, 'tillstand': LASKVITTO if aktiverade else inget},
            'mcp': mcp_rader,
            'verktyg': verktyg_rader,
            'tillampning': teknikval_text(teknikval) if teknikval is not None else TILLSTAND['ej_observerat'],
            **({'teknikval': teknikval} if teknikval is not None else {}),
            'nivaer': nivaer(skills, aktiverade, misslyckade, [s for s in skills if ('.claude/skills/%s/SKILL.md' % s) in lasta],
                             mcp_rader, verktyg_rader, vb, sett, helt=helt)})
    return ut


def nivaer(skills, aktiverade, misslyckade, lasta_skillmd, mcp_rader, verktyg_rader, vb, sett, helt=None):
    """De tre nivåerna i ägarens förtydligande 2026-10-07, var för sig: aktivering (skillverktygets lyckade och misslyckade
    anrop ur transkriptet, och SKILL.md-filer lästa med Read i stället), lyckad användning (verktyg och MCP:er som gav ett
    svar med innehåll) och bedömd kvalitet (sessionens egen visuella bedömning, redovisad, aldrig observerad; kvaliteten
    bedöms av passet granskning, skisskritiken och ägarens dom). Ingen nivå står för en annan."""
    T = TILLSTAND
    helt = sett if helt is None else helt  # ett saknat transkript: det som inte sågs är inte observerat (F04)
    inget = T['ej_gjort'] if helt else T['ej_observerat']
    utan = [s for s in skills if s not in aktiverade and s not in misslyckade]
    if not sett:
        akt = T['ej_observerat']
    elif not skills and not aktiverade and not misslyckade:
        akt = 'inga Skill-aktiveringar tilldelade rollen; Read redovisas separat'
    elif misslyckade:
        akt = 'misslyckad aktivering: %s%s' % (', '.join(misslyckade), ('; aktiverade: ' + ', '.join(aktiverade)) if aktiverade else '')
    elif aktiverade and not utan:
        akt = 'aktiverad med skillverktyget: ' + ', '.join(aktiverade)
    elif aktiverade or lasta_skillmd:
        akt = 'delvis: %s%s%s' % (('aktiverade ' + ', '.join(aktiverade)) if aktiverade else '',
                                  ('; SKILL.md läst med Read i stället: ' + ', '.join(s for s in lasta_skillmd if s not in aktiverade)) if lasta_skillmd else '',
                                  ('; utan aktivering: ' + ', '.join(utan)) if utan else '')
    else:
        akt = inget
    anvanda = [m for m, r in mcp_rader.items() if r.get('tillstand') == T['anvant']] + [v for v, s in verktyg_rader.items() if s == T['anvant']]
    blockerade = [m for m, r in mcp_rader.items() if r.get('tillstand') == T['blockerat']] + [v for v, s in verktyg_rader.items() if s == T['blockerat']]
    okanda = [m for m, r in mcp_rader.items() if r.get('tillstand') == T['ej_observerat']] + [v for v, s in verktyg_rader.items() if s == T['ej_observerat']]
    if anvanda:
        anv = '%s: %s%s' % (T['anvant'], ', '.join(anvanda), ('; %s: %s' % (T['blockerat'], ', '.join(blockerade))) if blockerade else '')
    elif blockerade:
        anv = '%s: %s' % (T['blockerat'], ', '.join(blockerade))
    elif not mcp_rader and not verktyg_rader:
        anv = 'inga verktyg eller MCP:er tilldelade rollen'
    else:
        anv = inget
    if okanda:
        anv = (anv + '; ' if anvanda or blockerade else '') + T['ej_observerat'] + ': ' + ', '.join(okanda)
    kval = ('%s: %s (%s)' % (REDOVISAT, vb.get('omdome') or '?', str(vb.get('skal') or '')[:160])) if vb else T['ej_observerat']
    return {'aktivering': akt, 'anvandning': anv,
            'bedomd_kvalitet': {'av_sessionen': kval, 'av_granskningen': 'bedöms av passet granskning, skisskritiken och ägarens dom, inte av kvittot'}}


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
