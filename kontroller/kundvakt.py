#!/usr/bin/env python3
"""kundvakt.py — PreToolUse-krok för skapandeflödets sessioner: ett anrop till en extern designtjänst (Refero eller
Mobbin) får aldrig bära kundens namn, orter, gata, webbadress, e-post eller nummer (BESLUT.md 2026-10-05, punkt 4;
ägarens ord 2026-10-05 18:15Z: skillsen och MCP:erna ska användas, och kundens uppgifter skyddas som förut).

    .venv/bin/python -B kontroller/kundvakt.py <slug> <underlag-katalog>     (läser krokens JSON på stdin)

Vakten stänger vid fel. Tjänsternas verktyg står inte i sessionens --allowedTools: ett rent anrop öppnas bara av
vaktens uttryckliga tillåtelse (JSON med permissionDecision allow på stdout, slutkod 0). Ett anrop med kundens
uppgifter stoppas med slutkod 2 och skälet på stderr. Kan vakten inte pröva anropet (fel, egen frist), eller startar den
inte alls, får anropet ingen tillåtelse och dontAsk nekar det (kontroller/atelje.py, kundvakt; granskning 4, G3).

Bara flödets egna verktyg hos Refero och Mobbin kan tillåtas (referenstjanster.TJANSTER, exakta namn), och sedan
2026-10-07 Motions fria dokumentations-MCP (kompetens.MCP, samma regel: generiska frågor utan kunduppgifter); ett annat
verktyg hos samma tjänst stoppas (den oberoende granskningen 2026-10-05, fynd 1). Id-fält (style_id, screen_ids,
flow_id …) med UUID, korta tal i sidnummer och gränser och tjänsternas egna adresser prövas inte som "lång sifferföljd"
eller "adress"; fritext och JSON-nycklar prövas alltid, och namnprövningen tål NFD-kodade tecken, URL-kodning (också
dubbel), sammansättningar, gatans namn utan nummer och telefonnumrets sista siffror (granskning 4, G14; granskningen
2026-10-05, fynd 8). En tom indata stoppas. Mobbins search_screens söker i läget deep när mode saknas, och det kostar
krediter: ett anrop utan uttryckligt mode som inte är deep stoppas (granskningen GR-20261007-r102, B6).

Personnamn, orter och adresser ur kundens underlag (granskningen GR-20261007-r102, B5; omgranskningen
GR-20261007-r102-om, B1 och B2; omgranskningen GR-20261007-r104, B1 och B2). Ägarens regel: Refero och Mobbin ska
fortsatt få generiska researchfrågor utan kunduppgifter. Vakten läser BRIEF.md och sidans text (INNEHALL.md,
TEXTUNDERLAG.md), fritexten i VERKSAMHET.json (not och kontaktvägarnas belägg; schemat har inga personfält) och
Bokadirekts filer (kalla/extern/bokadirekt-omdomen.txt: namn- och frisörkolumnen; bokadirekt-tjanster.txt: personalen i
prislistorna och i kolumnen vem). Namn i markdown (länkar, fetstil) läses som text, en rad i versaler som vanlig text,
sidtextens "- h3: …" som en rubrik, och alla alfabetens bokstäver räknas (ł, ñ, ś).
- Säkra personnamn, som också stoppas ord för ord (bara förnamnet, bara efternamnet): namnet efter ett personord
  ("Ägaren Anna Svensson", "ägaren, Olle Berg", "Kontakt: Erik Lund", tabellraden "| Kontakt | Erik Lund |",
  "Konsulterna A B och C D", "tillsammans med", "Hälsningar, Kalle", "Tack till nils holm", "Möt Kim Wong", "Träffa …",
  "Enligt …", och "Om" först i en rubrik: "## Om Pål Ödegård"), före en roll ("Olle Berg, snickare", "Anna Ek är
  snickare", "| Kim Wong | Snickare |", "Kim Wong (ägare)") eller före ett personverb efter två ord ("Pål Ödegård svarar
  …"; "Sidan svarar" är ingen person); attributionen efter ett citat ("”…” – Pelle Svensson, kund", "(Ture valfrid Ö,
  Reco)"), efter en mening och ett tankstreck ("Bra jobb! — Lisa") och på en rad som börjar med tankstreck; genitiv
  efter en initial ("Ture valfrid Ö:s omdöme"); texten i en mailto- eller tel-länk; namn som börjar med ett vanligt
  förnamn (FORNAMN) eller har ett vanligt efternamnsled (-sson, -berg, -qvist …); ett vanligt förnamn med stor bokstav
  inne i en mening; en rubrik som bara är ett par med stor bokstav ("## Pål Ödegård"); under en rubrik om personer (Om
  oss, Team, Omdömen, Kontakt …) ett par i en rubrik, i en listpunkt eller rad som bara är paret och först i en mening;
  och Bokadirekts namn.
- Övriga par av ord med stor bokstav ("Primär Handling"), också först i en mening, stoppas bara som hela paret, och
  varje par ur tre ord; så också ett par med ett förnamn som är ett vanligt ord (ORDNAMN: "Per Ek", men "price per hour"
  går).
- Inget namn: ord ur EJ_NAMN (tjänster och märken, webbens och designens termer också på engelska, regionerna, vanliga
  ord) och typsnittsord (Sans, Serif, Display, Medium …) delar paren, och ett typsnitt ur Google Fonts ("Bodoni Moda";
  TYPSNITTSLISTA) är inget par; ett ensamt ord som bara har stor bokstav för att det inleder en mening räknas inte, om
  det inte är ett vanligt förnamn eller står före en roll; en del av en rubrik ger inga osäkra par ("### Featured Before
  After"); och briefens §7 (Designriktning), där förlagorna och typografin står, läses bara för orter efter ett
  platsverb och mailto-länkar.
- Orter stoppas som hela namn: efter ett platsverb ("Vi verkar i Upplands Väsby", "Kunderna bor i …"), också i §7, och
  utanför §7 efter varje platspreposition (i, på, vid, från, inom, runt, kring, omkring, utanför, nära, mellan). En ort
  med ett märke, en term eller ett typsnitt räknas inte, inte heller en ur bara regionernas ord ("Norra Sverige"); ett
  ortsled hör till namnet ("Stora Mellösa"), och ett vanligt ord kan vara en ort ("Vara").
- Adresser (skapande.adresser_i_text) i briefen, sidans text och RESEARCH.md: gatan ("Exempelgatan 3", "Östra
  Hamngatan", "Drottning Kristinas väg"), orten efter postnumret och orten i en mening med en adress stoppas som orter,
  och postnumren och de långa numren som kundens nummer. Fritexten i VERKSAMHET.json läses på samma sätt av
  skapande.forbjudna_termer, och övriga orter kommer ur dess fält.
Ett namn stoppas som hela ord, också i genitiv, med annat än mellanslag mellan delarna och hopskrivet från sex bokstäver
("AsaObergLind", "JonasEk"). Där precisionen och täckningen krockar går felet åt det säkra hållet: ett okänt par med
stor bokstav stoppas som par, också en förlaga som briefen nämner utanför §7; en rubrik som bara är ett par stoppas ord
för ord; ett säkert namn som också är ett vanligt ord stoppas ord för ord; och en ort som också är ett vanligt ord
("Mark", "Vara") stoppas som ord.
Inställningarna med kroken (installningar) används av skaparsessionerna (kontroller/atelje.py) och av
referenstjänsternas sessioner (kontroller/referenstjanster.py).
"""
import json
import os
import re
import signal
import sys
import unicodedata
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skapande  # noqa: E402

FRIST = 20  # sekunder; krokens egen tidsgräns är 30 (installningar nedan)
MATCH = 'mcp__refero__.*|mcp__mobbin__.*|mcp__motion__.*|mcp__21st__.*'  # externa designtjänster, Motions dokumentation och 21st.dev: kroken prövar varje anrop; andra MCP-anrop får ingen tillåtelse
ID_NYCKEL = re.compile(r'(^|_)(id|ids)$')
SMA_NYCKEL = re.compile(r'(^|_)(page|limit)$')  # sidnummer och gränser: bara korta tal
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
TAL = re.compile(r'^\d{1,9}$')  # Referos skärm- och flödes-id är tal; ett telefonnummer (tio siffror) prövas alltid
TJANSTEVARDAR = ('refero.design', 'mobbin.com')
MOBBIN_SKARMAR = 'mcp__mobbin__search_screens'  # verktygets standardläge är deep, som kostar krediter
MOBBIN_LAGEN = ('standard', 'fast')  # fast är verktygets äldre namn på standard

# --- personnamn och orter ur kundens underlag (B5; omgranskningen GR-20261007-r102-om, B1 och B2; GR-20261007-r104) ---
NAMNTEXTER = ('BRIEF.md', 'INNEHALL.md', 'TEXTUNDERLAG.md')
ADRESSTEXTER = NAMNTEXTER + ('RESEARCH.md',)  # gator, postnummer och orter i en adress läses också ur researchen
TYPSNITTSLISTA = Path(__file__).resolve().parents[1] / '.claude' / 'skills' / 'ui-ux-pro-max' / 'data' / \
    'google-fonts.csv'
BOKADIREKT_OMDOMEN = Path('kalla') / 'extern' / 'bokadirekt-omdomen.txt'  # datum | betyg | namn | frisör | tjänst | text
BOKADIREKT_TJANSTER = Path('kalla') / 'extern' / 'bokadirekt-tjanster.txt'  # "# Prislistor: 1 = A, B" och kolumnen vem
HOPGRANS = 6  # ett hopskrivet namn ("JonasEk", "AsaObergLind") prövas från sex bokstäver
ORD = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*")  # ett ord i vilket alfabet som helst, också Öberg-Lind och O'Brien
TOKEN = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*|\d+|\S")
VIK_EXTRA = {ord('ł'): 'l', ord('đ'): 'd', ord('ð'): 'd', ord('ħ'): 'h', ord('ı'): 'i', ord('þ'): 'th'}  # utan diakrit i NFKD
CITAT = set('"”“«»„\'‘’')
STRECK = set('—–-')
# tecken efter vilka ett ord har stor bokstav för att det inleder en mening, ett citat eller ett textstycke
INLEDANDE = set('.!?:;|·•→([{/') | CITAT | STRECK
# väderstreck, ortsled och stora regioner (skapande.REGIONER): en ort ur bara dem ("Norra Sverige") pekar inte ut kunden
REGIONER = skapande.REGIONER
# ord som ofta står med stor bokstav bredvid ett annat utan att vara ett namn: tjänster och märken, webbens och designens
# termer (också engelska rubriker som "Opening Hours" och "Before After"), regionerna, och vanliga ord i början av en
# mening eller i en rubrik med versaler ("Våra Tjänster"), jämförda utan diakriter
EJ_NAMN = set('''
google apple microsoft facebook meta instagram linkedin youtube tiktok pinterest twitter whatsapp messenger snapchat
swish klarna stripe paypal bokadirekt hitta eniro trustpilot reco mobbin refero figma astro react tailwind vercel
netlify wordpress wix squarespace shopify webflow framer canva adobe chrome safari android ios iphone ipad mac windows
allabolag ratsit merinfo blocket offerta mittanbud servicefinder byggahus houzz unsplash pexels shutterstock istock
getty lucide heroicons phosphor fontawesome iconify word excel powerpoint photoshop illustrator lightroom indesign
notion slack zoom gmail outlook dropbox
material design hero section call to action page site web maps map pay store play search console analytics business
profile ads tag manager cookie cookies consent privacy policy terms contact about home start footer header menu button
form landing pricing book booking checkout cart login sign up get started learn more read more social proof trust
testimonial testimonials review reviews case study studies gallery grid card cards banner slider carousel layout style
typography brand logo portfolio project projects service services team studio magazine editorial dark light mode night
opening hours kitchen bathroom renovation remodel before after featured faq blog news story stories values mission
process steps step offer offers estimate price prices plan plans package packages feature features benefits location
locations area areas coverage client clients customer customers partner partners rating ratings badge badges award
awards certification certifications guarantee newsletter navigation nav mobile desktop responsive bento split timeline
tab tabs accordion modal list table photo photos image images video icon icons illustration color colors palette theme
minimal modern classic clean warm art deco craft scandinavian nordic swiss brutalist wireframe mockup prototype
component components dashboard onboarding signup row rows column columns stats numbers counter metrics marquee sticky
mega big small large hover scroll parallax animation motion overlay gradient shadow border pill chip chips toggle switch
dropdown input field fields checkbox label labels tooltip toast alert notification breadcrumb breadcrumbs pagination
sidebar drawer sheet panel cta intro summary details overview highlights highlight showcase spotlight masonry lightbox
slideshow collage mosaic cover full width bleed wide fixed floating centered left right bottom caption captions headline
headlines subheading eyebrow tagline slogan lead body copy text work works recent latest popular meet choose happy
simple premium local
vi jag du ni de det den detta denna dessa en ett i pa for med till om nar som och men hos fran kunden kunderna foretaget
firman verksamheten agaren agarna sidan sajten besokaren besokarna ring boka skriv las se fa ta ge valkommen hej tack
oss er dig mig vara vart mina dina era alla tjanster tjansten tjansterna offert offerter priser prislista galleri
projekt referens referenser omdome omdomen kontakta hem hit fragor vanliga fri gratis begar mer jobb jobben teamet
personal personalen medarbetare medarbetarna oppettider hemsida hemsidan sajt webbplats meny knapp sektion rubrik bild
bilder foto foton sidfot sidhuvud
the a an and or of in on at by with from our your my we us you it is are be get now free quote request send submit view
see more all new best top why how what who where this that here there next back open show join follow share save
download order buy shop try today online
'''.split()) | REGIONER
TYPSNITTSORD = set('sans serif display mono grotesk grotesque slab script gothic condensed rounded neue caps typeface '
                   'font fonts typsnitt thin light regular medium semibold bold extrabold black heavy italic oblique '
                   'variable'.split())  # Work Sans, Playfair Display, Lora Medium: typsnitt, aldrig personer
PARDELARE = EJ_NAMN | TYPSNITTSORD  # ord som aldrig hör till ett namn och delar ett par
# en ort kan inte ha ett ord ur EJ_NAMN, utom regionernas led ("Stora Mellösa") och de vanliga ord som också är orter
# (Vara); en ort ur bara regionernas ord räknas inte (_ej_plats)
ORTER_SOM_ORD = {'vara'}
EJ_PLATS = (EJ_NAMN - REGIONER - ORTER_SOM_ORD) | TYPSNITTSORD
# personord: ett namn efter dem är en person ("Ägaren Anna Svensson", "Kontakt: Erik Lund", "Hälsningar, Kalle")
ROLLORD = set('''
agare agaren agarna delagare delagaren grundare grundaren grundarna vd kontakt kontakten kontaktperson kontaktpersonen
ansvarig ansvarige teamledare teamledaren arbetsledare arbetsledaren projektledare projektledaren platschef platschefen
snickare snickaren snickarna hantverkare hantverkaren hantverkarna elektriker elektrikern malare malaren frisor frisoren
konsult konsulten konsulterna kollega kollegan kollegor kollegorna medarbetare medarbetaren medarbetarna anstalld
anstallde anstallda larling larlingen fotograf fotografen kund kunden granne grannen
'''.split())
# en roll i singular efter ett namn ("Olle Berg, snickare", "Anna Ek är vår snickare"); en roll i plural står oftare i en
# uppräkning av firmafakta än efter ett namn och räknas inte
ROLL_EFTER = set('''
agare agaren delagare delagaren grundare grundaren vd kontaktperson kontaktpersonen ansvarig teamledare teamledaren
arbetsledare arbetsledaren projektledare projektledaren platschef platschefen snickare snickaren hantverkare hantverkaren
elektriker elektrikern malare malaren frisor frisoren konsult konsulten kollega kollegan medarbetare medarbetaren larling
larlingen fotograf fotografen kund
'''.split())
FORE_ORD = set('kontakta ring ringa fraga mejla maila hej hejsan halsningar mvh halsar tack enligt'.split())
FORE_ORD_EXAKT = {'möt', 'träffa'}  # jämförda med diakriter: "mot" är en preposition
FORE_FRASER = {('tack', 'till'), ('fraga', 'efter'), ('tillsammans', 'med'), ('startades', 'av'), ('grundades', 'av'),
               ('drivs', 'av'), ('ags', 'av'), ('skriv', 'till'), ('vanliga', 'halsningar')}
POSSESSIV = set('var vart vara er ert era firmans foretagets en ett'.split())  # "Kalle, vår snickare"
STOPPORD = set('och samt for som att med pa i om till fran via av har ar var hos nar men eller under efter innan sedan '
               'kund'.split())  # småord som avslutar ett namn ("Ture valfrid Ö på Reco", "nils holm för hjälpen")
# verb som en person gör, efter ett namn i två ord ("Pål Ödegård svarar på offerterna"); efter ett ensamt ord räknas de
# inte ("Sidan svarar", "Rubriken säger"). Jämförda med diakriter: "så" är inget verb.
PERSONVERB = set('''svarar svarade driver drev äger ägde grundade startade jobbar jobbade arbetar arbetade säger sa sade
berättar berättade tycker tyckte skriver skrev ansvarar ansvarade sköter skötte tipsar lovar minns började gillar älskar
tackar rekommenderar hjälper hjälpte'''.split())
# rubriker över ett avsnitt om personer (teamet, ägaren, omdömena, kontakten), jämförda med diakriter
PERSONAVSNITT = re.compile(r'(?<!\w)(om oss|om företaget|om firman|om mig|team|teamet|vårt team|personal|personalen|'
                           r'medarbetare|medarbetarna|vi som jobbar|möt|träffa|omdömen|recensioner|kunderna om|'
                           r'vad kunderna|kontakt|kontakta|kontaktpersoner?|ägare|ägaren|grundare|grundaren)(?!\w)')
PLATSVERB = set('verkar arbetar jobbar finns bygger utgar bor ligger verksam verksamma baserad baserade belagen '
                'belaget'.split())  # "Vi verkar i Upplands Väsby", "Kunderna bor i Rödhamra"
PLATSPREP = set('i pa inom fran runt kring omkring'.split())
# utanför briefens §7 räknas orten efter en preposition också utan platsverb ("kunder i Rödhamra", "jobb på Eköholm")
PLATSPREP_BRED = PLATSPREP | set('vid utanfor nara mellan'.split())
EFTERNAMNSLED = ('sson', 'gren', 'qvist', 'kvist', 'strom', 'berg', 'lund', 'holm', 'dahl', 'lind', 'stedt', 'blad', 'blom',
                 'ski', 'cki', 'wicz', 'ez')
# förnamn som också är vanliga ord eller orter: de håller ihop ett par i början av en mening ("Per Ek"), men ett par med
# dem stoppas bara som par, aldrig ord för ord ("price per hour", "max width" går)
ORDNAMN = set('per bo dag max liv sol rut love inga milan kim'.split())
# vanliga förnamn i Sverige (utan diakriter)
FORNAMN = set('''
anna eva maria karin kristina lena sara kerstin emma ingrid marie malin jenny annika hanna linnea elin johanna sofia sofie
ida elsa julia alice maja ella wilma vilma ebba astrid agnes saga olivia freja alva klara clara signe selma vera stella
ellen moa felicia matilda amanda louise lovisa frida josefin josefine camilla helena susanne ulla birgitta inger
margareta elisabeth elisabet gunilla monica monika ann anne anneli annelie carina karina asa lisa linda therese jessica
caroline karolina sandra emelie emilia erika ylva pia petra lotta charlotte charlotta cecilia viktoria victoria siv
britt barbro marianne agneta marta ingela yvonne katarina catarina jeanette madeleine nathalie natalie rebecka rebecca
tove tilda lova nova thea tyra ines lea leah iris nellie edith lilly mila sigrid ronja tuva majken greta cajsa kajsa
hedvig elvira isabelle isabella nora alexandra angelica angelika anette annette mona kristin birgit gunnel berit solveig
gudrun irene ingegerd ingeborg viola ulrika veronica veronika sanna hillevi mikaela michaela fanny tindra minna alma
ellie lina nicole linn emilie evelina amelia ester esther hilda hilma svea hedda tora jasmine yasmin amira
lars karl erik anders johan nils carl mikael michael jan hans peter olof olov gunnar sven fredrik bengt daniel gustav
gustaf goran alexander magnus ake thomas tomas stefan leif mats jonas henrik ulf bertil bjorn ingemar kjell christer
krister andreas martin mattias matthias hakan rolf kent roger tommy patrik patrick niklas nicklas marcus markus robert
joakim tobias sebastian simon oscar oskar william lucas lukas liam elias hugo noah adam viktor victor filip philip isak
axel emil ludvig albin anton melvin leo vincent theo elton arvid olle kalle pelle stig lennart ingvar tord torbjorn
kenneth jorgen jens claes klas kristoffer christoffer jimmy johnny ola ove lasse janne micke jocke tore arne rune kurt
gosta allan conny jesper linus rasmus jacob jakob david samuel benjamin gabriel adrian alvin charlie edvin melker valter
walter harry eddie folke sixten otto ivar malte wilmer vilmer sigge frans sune birger evert harald helge holger ivan
josef joel jonathan kevin pontus hampus ronny glenn egon emanuel erland ragnar sture tage yngve vidar
mohammed mohammad muhammad mohamed ahmed ahmad ali omar hassan hussein yusuf mustafa ibrahim abdullah mehmet amir reza
hamid khaled mahmoud jose juan carlos luis pablo miguel antonio manuel ana piotr tomasz lukasz krzysztof pawel michal
marek andrzej katarzyna agnieszka magdalena joanna ewa olga natalia irina elena svetlana dmitri sergei aleksandr
nikola dragan zoran mirza emir fatima aisha maryam zainab layla leila amina nour noor
'''.split())


def falt(x, nyckel=''):
    """(nyckel, sträng) för varje strängvärde i anropets indata, också i listor (en lista ärver sin nyckel)."""
    if isinstance(x, str):
        yield nyckel, x
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield nyckel, str(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from falt(v, str(k))
    elif isinstance(x, list):
        for v in x:
            yield from falt(v, nyckel)


def tillatna():
    """De exakta verktygsnamn flödet använder hos Refero och Mobbin (referenstjanster.TJANSTER) och hos Motions
    dokumentations-MCP (kompetens.MCP; ägarens uppdrag 2026-10-07, punkt 5C): en källa, kompetens.mcp_verktyg."""
    import kompetens
    return {v for t in kompetens.MCP for v in kompetens.mcp_verktyg(t)}


def installningar(slug, underlag, timeout=30):
    """--settings med kundvakten som PreToolUse-krok för Refero och Mobbin. Tjänsternas verktyg står inte i sessionens
    --allowedTools: bara vaktens uttryckliga tillåtelse öppnar ett rent anrop, och en krok som inte startar, dör eller
    når sin tidsgräns lämnar anropet åt dontAsk, som nekar det (prövat i en riktig session 2026-10-05; granskning 4, G3)."""
    kommando = ('"$CLAUDE_PROJECT_DIR/.venv/bin/python" -B "$CLAUDE_PROJECT_DIR/kontroller/kundvakt.py" %s "%s" '
                "|| { echo 'kundvakten kunde inte pröva anropet' >&2; exit 2; }") % (slug, underlag)
    return json.dumps({'hooks': {'PreToolUse': [{'matcher': MATCH, 'hooks': [{'type': 'command', 'timeout': timeout, 'command': kommando}]}]}})


def nycklar(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield str(k)
            yield from nycklar(v)
    elif isinstance(x, list):
        for v in x:
            yield from nycklar(v)


def ar_id(nyckel, varde):
    n, v = nyckel.lower(), varde.strip()
    return (bool(ID_NYCKEL.search(n)) and bool(UUID.match(v) or TAL.match(v))) or (bool(SMA_NYCKEL.search(n)) and bool(re.fullmatch(r'\d{1,4}', v)))


def tjanstens_adress(varde):
    try:
        d = urllib.parse.urlsplit(varde.strip())
    except ValueError:
        return False
    vard = (d.hostname or '').lower()
    return d.scheme == 'https' and any(vard == v or vard.endswith('.' + v) for v in TJANSTEVARDAR)


def avkoda(text):
    """URL-kodningen borttagen, också dubbel ("%2520"): kodningen döljer aldrig ett namn."""
    t = str(text)
    for _ in range(4):
        u = urllib.parse.unquote(t)
        if u == t:
            break
        t = u
    return t


def vik(s):
    """skapande.vik (gemener utan diakriter) och bokstäverna som saknar diakrit i Unicode (ł → l, đ → d)."""
    import skapande
    return skapande.vik(s).translate(VIK_EXTRA)


def _ord(t):
    return bool(ORD.fullmatch(t))


def _initial(t):
    return len(t) == 1 and t.isupper()


def _namnord(t):
    """Ett ord med stor begynnelsebokstav som kan vara ett namn: inte en förkortning i versaler (AB, SEO)."""
    return len(t) > 1 and _ord(t) and t[0].isupper() and not re.sub(r"[-'’]", '', t).isupper()


def _efternamnslikt(t):
    v = vik(t)
    v = v[:-1] if v.endswith('s') and v[:-1].endswith(EFTERNAMNSLED) else v  # genitiv: "Svenssons"
    return any(v.endswith(s) and len(v) >= len(s) + 2 for s in EFTERNAMNSLED)


def _forbered(rad):
    """(raden som text utan markdown, rubriknivån, texterna i mailto- och tel-länkar, pseudorubrik). En rad i versaler
    läses som vanlig text ("TEAMLEDARE: ANNA KARLSSON" → "Teamledare: Anna Karlsson"). Sidtextens "- h3: Kim Wong" är
    sidans rubrik och läses som en rubrik (pseudorubrik), men öppnar och stänger inga avsnitt."""
    rad = re.sub(r'^\s*>+\s?', '', unicodedata.normalize('NFC', rad))
    m = re.match(r'\s*(#+)\s*', rad)
    rubrik, pseudo = (len(m.group(1)) if m else 0), False
    rad = rad[m.end():] if m else re.sub(r'^\s*(?:[-*+]|\d+[.)])\s+', '', rad)
    m = None if rubrik else re.match(r'(?i)h([1-6])\s*:\s*', rad)
    if m:
        rubrik, pseudo, rad = int(m.group(1)), True, rad[m.end():]
    lankar = []

    def lank(m_):
        if re.match(r'(?i)\s*(?:mailto|tel):', m_.group(2)):
            lankar.append(m_.group(1))
        return m_.group(1)
    rad = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', lank, rad)
    rad = re.sub(r'(?<!\w)[*_`]+|[*_`]+(?!\w)', '', rad)  # fetstil, kursiv och kod
    if not any(c.islower() for c in rad):
        rad = ORD.sub(lambda w: '-'.join(x.capitalize() for x in w.group(0).split('-')), rad)
    return rad, rubrik, lankar, pseudo


def _namnet(tok, j, attribution=False):
    """Namnet som börjar vid tok[j] efter ett personord eller i en attribution: (orden, index efter namnet). Det första
    ordet har stor bokstav eller är ett vanligt förnamn i gemener ("nils holm"); en attribution kan ha mellannamn i
    gemener och en initial ("Ture valfrid Ö", Recos form)."""
    ut, k, gemen = [], j, False
    while k < len(tok) and len(ut) < 4 and _ord(tok[k]):
        t, v = tok[k], vik(tok[k])
        if v in EJ_NAMN or v in STOPPORD or v in TYPSNITTSORD:
            break
        if _initial(t):
            if not ut:
                break
        elif t[0].isupper():
            if not _namnord(t):
                break
        elif not ut and v in FORNAMN:
            gemen = True
        elif not (ut and (gemen or attribution)):
            break
        ut.append(t)
        k += 1
    if attribution and ut and not gemen and vik(ut[0]) not in FORNAMN and not _initial(ut[-1]):
        i = next((i for i, t in enumerate(ut) if not t[0].isupper()), len(ut))  # gemener utan Recos form: prosa
        ut, k = ut[:i], j + i
    if attribution and len(ut) == 1 and vik(ut[0]) not in FORNAMN and k < len(tok) and _ord(tok[k]) \
            and not tok[k][0].isupper() and vik(tok[k]) not in STOPPORD:
        return [], j  # ett ord som flyter in i en mening ("— Riktiga jobb"): ingen attribution
    return ut, k


def _personord_fore(tok, j, rubrik=0):
    """Står ett personord, en hälsning eller en fras som "tack till" direkt före tok[j] (med högst ett komma, kolon eller
    en tabellkant emellan)? "Möt", "Träffa" och "Enligt" räknas också, och "Om" först i en rubrik ("## Om Pål
    Ödegård")."""
    i = j - 1
    if i >= 0 and tok[i] in (',', ':', '|'):
        i -= 1
    if i < 0 or not _ord(tok[i]):
        return False
    v1 = vik(tok[i])
    v2 = vik(tok[i - 1]) if i >= 1 and _ord(tok[i - 1]) else ''
    forst_i_rubrik = rubrik and not any(_ord(t) for t in tok[:i])
    return v1 in ROLLORD or v1 in FORE_ORD or (v2, v1) in FORE_FRASER or tok[i].lower() in FORE_ORD_EXAKT \
        or bool(forst_i_rubrik and v1 == 'om')


def _roll_efter(tok, k):
    """Följs namnet av en roll ("Olle Berg, snickare", "Kalle, vår snickare", "Anna Ek är snickare", "| Kim Wong |
    Snickare |", "Kim Wong – snickare", "Kim Wong (ägare)")?"""
    if k < len(tok) and tok[k] in {',', '|', ':', '('} | STRECK:
        k += 1
    elif k < len(tok) and vik(tok[k]) in ('ar', 'var', 'blir'):
        k += 1
    else:
        return False
    if k < len(tok) and vik(tok[k]) in POSSESSIV:
        k += 1
    return k < len(tok) and vik(tok[k]) in ROLL_EFTER


def _personverb_efter(tok, k):
    """Följs namnet av ett verb som en person gör ("Pål Ödegård svarar …", "Kim Wong driver firman")?"""
    return k < len(tok) and tok[k].lower() in PERSONVERB


_TYPSNITT = []


def _typsnitt(run):
    """Är orden ett typsnitt i Google Fonts ("Bodoni Moda", "Libre Baskerville"; ui-ux-pro-max: data/google-fonts.csv)?
    Saknas listan räknas inget som typsnitt, och felet går åt det säkra hållet."""
    if not _TYPSNITT:
        familjer = set()
        try:
            import csv
            with open(TYPSNITTSLISTA, encoding='utf-8', newline='') as f:
                familjer = {' '.join(re.findall(r'[a-z0-9]+', vik(r.get('Family') or ''))) for r in csv.DictReader(f)}
        except (OSError, ValueError, csv.Error):
            pass
        _TYPSNITT.append(familjer - {''})
    return ' '.join(re.findall(r'[a-z0-9]+', ' '.join(vik(t) for t in run))) in _TYPSNITT[0]


def _ej_plats(run):
    """Är orden efter en preposition inget ortnamn: ett märke, en term, ett typsnitt eller bara regionernas ord?"""
    v = [vik(t) for t in run]
    return any(w in EJ_PLATS for w in v) or all(w in REGIONER for w in v) or _typsnitt(run)


def _orter_fran(tok, j):
    """Orterna som börjar vid tok[j] efter en preposition: "i Rödhamra, Västerbyn och Upplands Väsby" (en lista med
    komma eller "och"); varje ortnamn som en lista av ord, utan dem som _ej_plats avvisar. (orterna, index efter
    dem)."""
    ut, k = [], j
    while k < len(tok) and _namnord(tok[k]):
        start = k
        while k < len(tok) and _namnord(tok[k]) and k - start < 4:
            k += 1
        if not _ej_plats(tok[start:k]):
            ut.append(tok[start:k])
        if k < len(tok) and (tok[k] == ',' or vik(tok[k]) == 'och') and k + 1 < len(tok) and _namnord(tok[k + 1]):
            k += 1
        else:
            break
    return ut, k


def _rad(rad, sektion7, rubrik, lankar, person=False):
    """Namnen i en rad: ([säkra personnamn], [osäkra par], [orter]), var och en som en lista av ord. person: raden står
    under en rubrik om personer (_text)."""
    saker, osaker, orter = [], [], []
    for lank_ in lankar:  # texten i en mailto- eller tel-länk är en person, när hela texten är ett namn
        lt = [m.group(0) for m in TOKEN.finditer(lank_)]
        namn, k = _namnet(lt, 0)
        if namn and k == len(lt) and (len(namn) > 1 or vik(namn[0]) in FORNAMN):
            saker.append(namn)
    tok = [m.group(0) for m in TOKEN.finditer(rad)]
    tagna = set()  # ord som redan hör till ett namn efter ett personord eller i en attribution
    if not sektion7:
        for i in range(len(tok) - 2):  # genitiv efter en initial, Recos form: "Ture valfrid Ö:s omdöme"
            if _initial(tok[i]) and tok[i + 1] == ':' and tok[i + 2] == 's':
                s = i  # förnamnet med stor bokstav och högst två mellannamn i gemener före initialen
                while s > 0 and i - s < 2 and _ord(tok[s - 1]) and tok[s - 1].islower() \
                        and vik(tok[s - 1]) not in PARDELARE | STOPPORD:
                    s -= 1
                if s > 0 and _namnord(tok[s - 1]) and vik(tok[s - 1]) not in PARDELARE | STOPPORD:
                    saker.append(tok[s - 1:i + 1])
                    tagna.update(range(s - 1, i + 1))
    for j in range(len(tok)):
        if not _ord(tok[j]):
            continue
        # orten efter ett platsverb ("verkar i Upplands Väsby och Norra Sverige"), utanför §7 efter varje
        # platspreposition ("kunder i Rödhamra", "bor på Eköholm")
        if j >= 1 and _namnord(tok[j]) and ((j >= 2 and vik(tok[j - 1]) in PLATSPREP and vik(tok[j - 2]) in PLATSVERB)
                                            or (not sektion7 and vik(tok[j - 1]) in PLATSPREP_BRED)):
            orter += _orter_fran(tok, j)[0]
        if sektion7 or j in tagna:
            continue
        attribution = (j >= 2 and tok[j - 1] in STRECK | {'('} and tok[j - 2] in CITAT) or (j == 1 and tok[0] in ('—', '–')) \
            or (j >= 2 and tok[j - 1] in ('—', '–') and tok[j - 2] in ('.', '!', '?'))
        if not (attribution or _personord_fore(tok, j, rubrik)):
            continue
        k = j
        while True:  # namnet, och fler namn efter "och", "samt" eller komma: "Konsulterna A B och C D"
            namn, k2 = _namnet(tok, k, attribution)
            if not namn:
                break
            saker.append(namn)
            tagna.update(range(k, k2))
            if k2 + 1 < len(tok) and (tok[k2] in (',', '&') or vik(tok[k2]) in ('och', 'samt')):
                k = k2 + 1
                continue
            break
    if sektion7:
        return saker, osaker, orter
    # par och ord med stor bokstav, delade av ord ur EJ_NAMN och typsnittsord
    ord_idx = [i for i, t in enumerate(tok) if _ord(t)]
    j = 0
    while j < len(tok):
        if not (_namnord(tok[j]) and vik(tok[j]) not in PARDELARE) or j in tagna:
            j += 1
            continue
        k = j
        while k < len(tok) and _namnord(tok[k]) and vik(tok[k]) not in PARDELARE and k not in tagna:
            k += 1
        run, inledande = tok[j:k], j == 0 or tok[j - 1] in INLEDANDE
        # ett personverb räknas bara efter två ord: "Sidan svarar på frågan" och "Rubriken säger" är inga personer
        roll = _roll_efter(tok, k) or (k - j > 1 and _personverb_efter(tok, k))
        hel = ord_idx[0] >= j and ord_idx[-1] < k  # rubriken, listpunkten eller raden är bara namnet ("## Pål Ödegård")
        j = k
        if len(run) > 1 and _typsnitt(run):
            continue  # ett typsnitt ur Google Fonts ("Bodoni Moda"), aldrig en person
        if len(run) == 1:
            if roll or (vik(run[0]) in FORNAMN and not inledande):
                saker.append(run)  # ett vanligt förnamn inne i en mening, eller ett namn före en roll
        elif roll or vik(run[0]) in FORNAMN or any(_efternamnslikt(t) for t in run) or (hel and rubrik) \
                or (person and (rubrik or hel or inledande)):
            saker.append(run)
        elif not rubrik:
            osaker.append(run)  # också först i en mening: "Pål Ödegård har …" stoppas som helt par
    return saker, osaker, orter


def _text(text, saker, osaker, orter):
    """Namnen och orterna i en text, rad för rad. Briefens §7 läses bara för orter och mailto-länkar. Under en rubrik om
    personer (PERSONAVSNITT: Om oss, Team, Omdömen, Kontakt …) är ett par med stor bokstav i en rubrik, en listpunkt
    eller en rad som bara är paret, och ett par först i en mening, ett säkert namn; avsnittet slutar vid nästa rubrik på
    samma eller högre nivå, och sidtextens pseudorubrik ("- h2: Möt teamet") gäller till nästa riktiga rubrik."""
    sektion7, niva7, person, nivap = False, 0, False, 0
    for rad in str(text).splitlines():
        rad_, rubrik, lankar, pseudo = _forbered(rad)
        if rubrik and not pseudo:
            if sektion7 and rubrik <= niva7:
                sektion7 = False
            if person and rubrik <= nivap:
                person = False
            if not sektion7 and (re.search(r'§\s*7(?!\d)', rad_) or 'designriktning' in vik(rad_)):
                sektion7, niva7 = True, rubrik
        s, o, t = _rad(rad_, sektion7, rubrik, lankar, person)
        saker += s
        osaker += o
        orter += t
        if rubrik and not person and PERSONAVSNITT.search(rad_.lower()):
            person, nivap = True, 7 if pseudo else rubrik


def _valfri_text(p):
    """Bara en frånvarande fil är valfri; okänd lässtatus får aldrig öppna kroken."""
    try:
        return Path(p).read_text(encoding='utf-8')
    except FileNotFoundError:
        if os.path.lexists(p):
            raise ValueError('en befintlig underlagslänk kunde inte läsas')
        return None


def _bokadirekt(u):
    """Namnen i Bokadirekts filer (kontroller/hamta_bokadirekt.py): omdömenas namn och frisör, prislistornas personal
    och kolumnen vem i tjänsterna."""
    namn = []
    rader = (_valfri_text(u / BOKADIREKT_OMDOMEN) or '').splitlines()
    for rad in rader:
        delar = [d.strip() for d in rad.split('|')]
        if not rad.startswith('#') and len(delar) >= 4:
            namn += delar[2:4]
    rader = (_valfri_text(u / BOKADIREKT_TJANSTER) or '').splitlines()
    vem = None
    for rad in rader:
        if rad.startswith('# Prislistor:'):
            namn += [n for lista in rad.split(':', 1)[1].split(';') for n in lista.split('=', 1)[-1].split(',')]
        elif rad.startswith('# tjänst |'):
            kol = [d.strip() for d in rad[1:].split('|')]
            vem = kol.index('vem') if 'vem' in kol else None
        elif rad.startswith('- ') and vem is not None:
            delar = [d.strip() for d in rad[2:].split('|')]
            namn += delar[vem].split(',') if len(delar) > vem else []
    ut = []
    for n in namn:
        ord_ = [w for w in ORD.findall(n) if vik(w) not in EJ_NAMN | STOPPORD | {'anonym', 'anonymous', 'valfri', 'ingen'}]
        if ord_:
            ut.append(ord_)
    return ut


def _strangar(namn, niva):
    """Strängarna som prövas för ett namn: hela namnet, och för säkra och osäkra namn varje kombination av två ord ur
    namnet (två av tre namn); för säkra namn också varje ord för sig (utom initialer och ord ur EJ_NAMN)."""
    ord_ = [re.sub(r"['’]s$", '', w) for w in (vik(t) for t in namn) if re.search('[a-z]', w)]
    ord_ = [w[:-1] if w.endswith('s') and w[:-1].endswith(EFTERNAMNSLED) and _efternamnslikt(w[:-1]) else w for w in ord_]
    if not ord_:
        return set()
    ut = {' '.join(ord_)}
    hela = [w for w in ord_ if len(re.sub('[^a-z]', '', w)) > 1]
    if niva != 'ort':
        ut.update('%s %s' % (a, b) for i, a in enumerate(hela) for b in hela[i + 1:])
    if niva == 'saker':
        ut.update(w for w in hela if w not in EJ_NAMN)
    return ut


def underlagets_uppgifter(slug, underlag):
    """{'personer', 'orter', 'siffror'} ur kundens underlag: personnamnen och orterna som strängar att pröva med
    namner_person (gatorna och orterna i en adress räknas som orter), och postnumren och de långa numren i texterna som
    siffersträngar. Briefen, sidans text och fritexten i VERKSAMHET.json läses för namn och orter; de och RESEARCH.md
    läses för adresser (skapande.adresser_i_text). Ett namn vars alla ord redan är kundens förbjudna termer
    (verksamhetens namn, orterna i VERKSAMHET.json) tas inte med: det stoppas ändå."""
    u = Path(underlag) / slug
    saker, osaker, orter = [], [], []
    v = json.loads((u / 'VERKSAMHET.json').read_text(encoding='utf-8'))
    if not isinstance(v, dict):
        raise ValueError('verksamhetsunderlaget är inte ett objekt')
    fritext = [v.get('not')] + [k.get('belagg') for k in v.get('kontaktvagar') or [] if isinstance(k, dict)] if isinstance(v, dict) else []
    _text('\n'.join(x for x in fritext if isinstance(x, str)), saker, osaker, orter)
    texter = {}
    for fil in ADRESSTEXTER:
        text = _valfri_text(u / fil)
        if text is not None:
            texter[fil] = text
    for fil in NAMNTEXTER:
        if fil in texter:
            _text(texter[fil], saker, osaker, orter)
    saker += _bokadirekt(u)
    kunden = skapande.forbjudna_termer(slug, underlag).get('ord') or set()

    def eget(namn):  # verksamhetens eget namn eller dess orter: namner_kunden prövar dem redan
        return all(w in kunden for w in re.findall(r'[a-z0-9]+', ' '.join(vik(t) for t in namn)))
    personer, ortnamn, siffror = set(), set(), set()
    for namn, niva in [(n, 'saker') for n in saker] + [(n, 'osaker') for n in osaker]:
        personer |= set() if eget(namn) else _strangar(namn, niva)
    for namn in orter:
        ortnamn |= set() if eget(namn) else _strangar(namn, 'ort')
    for t in texter.values():  # gator, postnummer, orter och c/o-namn i en adress (granskningen GR-20261007-r104, B1)
        a = skapande.adresser_i_text(t, ej=EJ_PLATS, regioner=REGIONER)
        ortnamn |= {x for x in a['gator'] | a['orter'] if not eget(x.split())}
        for x in a['namn']:
            personer |= set() if eget(x.split()) else _strangar(x.split(), 'osaker')
        siffror |= a['siffror']
    return {'personer': personer, 'orter': ortnamn, 'siffror': siffror}


def namn_i_underlaget(slug, underlag):
    """(personnamnen, orterna) ur kundens underlag (underlagets_uppgifter)."""
    u = underlagets_uppgifter(slug, underlag)
    return u['personer'], u['orter']


def personnamn(slug, underlag):
    """Personnamnen ur kundens underlag som aldrig får gå till tjänsterna (namn_i_underlaget)."""
    return namn_i_underlaget(slug, underlag)[0]


def namner_person(text, namn):
    """Nämner texten ett av namnen: som hela ord (också med genitiv-s och med annat än mellanslag mellan delarna), och
    hopskrivet från HOPGRANS bokstäver ("AnnaSvensson", "JonasEk"); URL-kodning (också dubbel) och diakriter döljer
    inget."""
    vt = vik(avkoda(text))
    hop = re.sub(r'[^a-z0-9]+', '', vt)
    for n in namn:
        delar = re.findall(r'[a-z0-9]+', n)
        if not delar:
            continue
        if re.search(r'(?<![a-z0-9])%s(?:s)?(?![a-z0-9])' % r'[^a-z0-9]+'.join(map(re.escape, delar)), vt):
            return True
        if len(delar) > 1 and len(''.join(delar)) >= HOPGRANS and ''.join(delar) in hop:
            return True
    return False


def provning(slug, underlag, anrop):
    """None när anropet får gå, annars skälet."""
    import skapande
    forbjudna = skapande.forbjudna_termer(slug, underlag)
    if not forbjudna.get('ord') and not forbjudna.get('siffror'):
        return 'kundens uppgifter gick inte att läsa (underlag/%s/VERKSAMHET.json); anropet stoppas' % slug
    namn = anrop.get('tool_name')
    if namn not in tillatna():
        return 'verktyget %s är inte ett av flödets verktyg hos Refero, Mobbin, Motion eller 21st.dev (metodkartans verktygsbeslut); anropet stoppas' % namn
    if namn == MOBBIN_SKARMAR and str((anrop.get('tool_input') or {}).get('mode') or '').strip().lower() not in MOBBIN_LAGEN:
        return ('%s kräver mode "standard": verktygets standardläge deep kostar krediter, och flödet söker i standardläget; '
                'anropet stoppas' % namn)
    uppgifter = underlagets_uppgifter(slug, underlag)
    # Samma fulla nummermängd i alla parametergrenar; ett tjänste-ID är
    # undantaget från talformatregeln, aldrig från redan kända kunduppgifter.
    forbjudna['siffror'] = set(forbjudna.get('siffror') or ()) | uppgifter['siffror']
    personer, orter = uppgifter['personer'], uppgifter['orter']
    fritext = list(nycklar(anrop.get('tool_input') or {}))
    for nyckel, varde in falt(anrop.get('tool_input') or {}):
        if ar_id(nyckel, varde):
            if skapande.namner_kunden(varde, {'siffror': forbjudna.get('siffror') or set()}):  # ett id bär aldrig kundens nummer
                return 'anropet till %s har kundens nummer i fältet %s' % (namn, nyckel)
            continue
        if tjanstens_adress(varde):
            if skapande.namner_kunden(avkoda(varde), forbjudna) or namner_person(varde, personer) or namner_person(varde, orter):
                return 'anropet till %s har en adress som nämner kundens uppgifter' % namn
            continue
        fritext.append(varde)
    text = ' '.join(fritext)
    if skapande.namner_kunden(avkoda(text), forbjudna):
        return ('anropet till %s nämner kundens namn, ort, webbadress, e-post eller nummer; beskriv bara branschen och '
                'vad sökningen ska ge' % namn)
    if namner_person(text, personer):
        return ('anropet till %s nämner ett personnamn ur kundens underlag; frågorna är generiska, utan namn, citat eller '
                'kundens egna texter' % namn)
    if namner_person(text, orter) or skapande.namner_kunden(avkoda(text), {'siffror': uppgifter['siffror']}):
        return ('anropet till %s nämner en ort ur kundens underlag, en gata eller ett nummer därifrån; beskriv bara '
                'branschen och vad sökningen ska ge' % namn)
    if any(skapande.SPARRAD_FORM.search(avkoda(x)) for x in fritext):
        return 'anropet till %s innehåller en adress, en e-postadress eller en lång sifferföljd; skriv frågan utan dem' % namn
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    def frist_ute(*_):
        raise TimeoutError('vaktens frist (%d s) tog slut' % FRIST)
    try:
        signal.signal(signal.SIGALRM, frist_ute)
        signal.alarm(FRIST)
        slug, underlag = argv[0], Path(argv[1])
        data = sys.stdin.read()
        if not data.strip():
            raise ValueError('tom indata')
        anrop = json.loads(data)
        skal = provning(slug, underlag, anrop)
        signal.alarm(0)
    except Exception as e:  # noqa: BLE001 — vakten stänger vid fel
        skal = 'kundvakten kunde inte pröva anropet (%s: %s); anropet stoppas' % (type(e).__name__, str(e)[:200])
    if skal:
        print(skal, file=sys.stderr)
        return 2
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow',
                                             'permissionDecisionReason': 'kundvakten: anropet bär inga uppgifter om kunden'}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
