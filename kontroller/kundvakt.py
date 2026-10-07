#!/usr/bin/env python3
"""kundvakt.py — PreToolUse-krok för skapandeflödets sessioner: ett anrop till en extern designtjänst (Refero eller
Mobbin) får aldrig bära kundens namn, orter, gata, webbadress, e-post eller nummer (BESLUT.md 2026-10-05, punkt 4;
ägarens ord 2026-10-05 18:15Z: skillsen och MCP:erna ska användas, och kundens uppgifter skyddas som förut).

    .venv/bin/python -B kontroller/kundvakt.py <slug> <underlag-katalog>     (läser krokens JSON på stdin)

Vakten stänger vid fel. Tjänsternas verktyg står inte i sessionens --allowedTools: ett rent anrop öppnas bara av
vaktens uttryckliga tillåtelse (JSON med permissionDecision allow på stdout, slutkod 0). Ett anrop med kundens
uppgifter stoppas med slutkod 2 och skälet på stderr. Kan vakten inte pröva anropet (fel, egen frist), eller startar den
inte alls, får anropet ingen tillåtelse och dontAsk nekar det (kontroller/atelje.py, kundvakt; granskning 4, G3).

Bara flödets egna verktyg hos Refero och Mobbin kan tillåtas (referenstjanster.TJANSTER, exakta namn); ett annat
verktyg hos samma tjänst stoppas (den oberoende granskningen 2026-10-05, fynd 1). Id-fält (style_id, screen_ids,
flow_id …) med UUID, korta tal i sidnummer och gränser och tjänsternas egna adresser prövas inte som "lång sifferföljd"
eller "adress"; fritext och JSON-nycklar prövas alltid, och namnprövningen tål NFD-kodade tecken, URL-kodning,
sammansättningar, gatans namn utan nummer och telefonnumrets sista siffror (granskning 4, G14; granskningen 2026-10-05,
fynd 8). En tom indata stoppas.

Sedan skaparna når Mobbin och skriver egna frågor (2026-10-07) prövas också personnamn ur kundens underlag: personfälten i
VERKSAMHET.json och namnen i BRIEF.md och sidans text (INNEHALL.md eller TEXTUNDERLAG.md), hittade som två ord efter
varandra med stor bokstav, utom ord som ofta står så utan att vara namn (Google Maps, Call To Action, Norra Sverige). Ägarens
regel: Refero och Mobbin ska fortsatt få generiska researchfrågor utan kunduppgifter. Mobbins search_screens söker i läget
deep när mode saknas, och det kostar krediter: ett anrop utan uttryckligt mode som inte är deep stoppas (granskningen
GR-20261007-r102, B5 och B6).

Inställningarna med kroken (installningar) används av skaparsessionerna (kontroller/atelje.py) och av
referenstjänsternas sessioner (kontroller/referenstjanster.py).
"""
import json
import re
import signal
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

FRIST = 20  # sekunder; krokens egen tidsgräns är 30 (installningar nedan)
MATCH = 'mcp__refero__.*|mcp__mobbin__.*'  # externa designtjänster: kroken prövar varje anrop; andra MCP-anrop får ingen tillåtelse
ID_NYCKEL = re.compile(r'(^|_)(id|ids)$')
SMA_NYCKEL = re.compile(r'(^|_)(page|limit)$')  # sidnummer och gränser: bara korta tal
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
TAL = re.compile(r'^\d{1,9}$')  # Referos skärm- och flödes-id är tal; ett telefonnummer (tio siffror) prövas alltid
TJANSTEVARDAR = ('refero.design', 'mobbin.com')
MOBBIN_SKARMAR = 'mcp__mobbin__search_screens'  # verktygets standardläge är deep, som kostar krediter
MOBBIN_LAGEN = ('standard', 'fast')  # fast är verktygets äldre namn på standard
# personnamn ur kundens underlag (B5): fält i VERKSAMHET.json som bär personer, poster med en persons namn, och texterna
PERSONNYCKLAR = {'agare', 'kontaktperson', 'kontaktpersoner', 'person', 'personer', 'medarbetare', 'team', 'grundare', 'ansvarig',
                 'forfattare', 'hantverkare', 'personal'}
OMDOMESNYCKLAR = {'omdomen', 'recensioner', 'citat', 'kundcitat', 'referenskunder'}
NAMNFALT = ('namn', 'name', 'forfattare', 'author', 'fornamn', 'efternamn')
NAMNTEXTER = ('BRIEF.md', 'INNEHALL.md', 'TEXTUNDERLAG.md')
OMSLUTER = '*_`"\'“”‘’„»«()[]{}<>.,;:!?'  # tecken runt ett ord som inte hör till det
NAMNORD = re.compile(r'[A-ZÅÄÖÉÜ][a-zåäöéüß]+(?:-[A-ZÅÄÖÉÜ][a-zåäöéüß]+)?')
# ord som ofta står med stor bokstav bredvid ett annat utan att vara ett namn: tjänster och märken, webbens och designens
# termer, väderstreck och ortsled, och vanliga ord i början av en mening (jämförda utan diakriter, som vik ger dem)
EJ_NAMN = set('''
google apple microsoft facebook meta instagram linkedin youtube tiktok pinterest twitter whatsapp messenger snapchat
swish klarna stripe paypal bokadirekt hitta eniro trustpilot reco mobbin refero figma astro react tailwind vercel netlify
wordpress wix squarespace shopify webflow framer canva adobe chrome safari android ios iphone ipad mac windows
material design hero section call to action page site web maps map pay store play search console analytics business
profile ads tag manager cookie cookies consent privacy policy terms contact about home start footer header menu button
form landing pricing book booking checkout cart login sign up get started learn more read more
norra sodra ostra vastra ovre nedre gamla nya stora lilla sankt st
vi jag du ni de det den detta denna dessa en ett i pa for med till om nar som och men hos fran kunden kunderna foretaget
firman verksamheten agaren agarna sidan sajten besokaren besokarna ring boka skriv las se fa ta ge valkommen hej tack
the a an and or of in on at by with from our your my we us you it is are be get now free quote request send submit
view see more all new best top why how what who where this that here there next back open show join follow share save
download order buy shop try today online
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
    """De exakta verktygsnamn flödet använder hos Refero och Mobbin."""
    import referenstjanster
    return {v for t in ('refero', 'mobbin') for v in referenstjanster.TJANSTER[t]['verktyg']}


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


def _strangar(x):
    """Namnen i ett personfält: en sträng, en lista av strängar eller poster med ett namnfält."""
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for v in x:
            yield from _strangar(v)
    elif isinstance(x, dict):
        for f in NAMNFALT:
            if isinstance(x.get(f), str):
                yield x[f]


def _personfalt(x):
    """Personernas namn i VERKSAMHET.json: personfälten var de än står, och namnfälten i poster med omdömen och citat."""
    import skapande
    if isinstance(x, dict):
        for k, v in x.items():
            k_ = skapande.vik(k)
            if k_ in PERSONNYCKLAR:
                yield from _strangar(v)
            elif k_ in OMDOMESNYCKLAR and isinstance(v, list):
                for post in v:
                    if isinstance(post, dict):
                        yield from (post[f] for f in NAMNFALT if isinstance(post.get(f), str))
            else:
                yield from _personfalt(v)
    elif isinstance(x, list):
        for v in x:
            yield from _personfalt(v)


def namnpar(text):
    """Två ord efter varandra med stor bokstav i en text, utom rubriker och par där ett ord ofta står så utan att vara
    ett namn (EJ_NAMN): kandidaterna till "Förnamn Efternamn", jämförda utan diakriter."""
    import skapande
    ut = set()
    for rad in str(text).splitlines():
        if rad.lstrip().startswith('#'):
            continue
        forra, bryt = None, True
        for m in re.finditer(r'\S+', rad):
            tok = m.group(0)
            ren = tok.strip(OMSLUTER)
            namnlikt = bool(NAMNORD.fullmatch(ren))
            if namnlikt and forra and not bryt and skapande.vik(forra) not in EJ_NAMN and skapande.vik(ren) not in EJ_NAMN:
                ut.add('%s %s' % (skapande.vik(forra), skapande.vik(ren)))
            # ett skiljetecken efter ordet (punkt, komma, kolon …) bryter paret; fetstil och citattecken gör det inte
            forra, bryt = (ren if namnlikt else None), (not namnlikt or any(c in '.,;:!?' for c in tok[len(tok.rstrip(OMSLUTER)):]))
    return ut


def personnamn(slug, underlag):
    """Personnamnen ur kundens underlag som aldrig får gå till tjänsterna: hela namnen, och efternamnet ur ett personfält."""
    import skapande
    u = Path(underlag) / slug
    ut = set()
    v = skapande.las_json(u / 'VERKSAMHET.json') or {}
    for namn in _personfalt(v):
        ord_ = [w for w in re.split(r'\s+', skapande.vik(namn).strip()) if w]
        if not 1 <= len(ord_) <= 4 or not all(re.fullmatch(r'[a-z][a-z-]*', w) for w in ord_):
            continue
        if len(ord_) > 1 or len(ord_[0]) >= 4:  # ett ensamt kort förnamn ger för många falsklarm
            ut.add(' '.join(ord_))
        if len(ord_) > 1 and len(ord_[-1]) >= 4:
            ut.add(ord_[-1])
    for fil in NAMNTEXTER:
        try:
            ut |= namnpar((u / fil).read_text(encoding='utf-8', errors='replace'))
        except OSError:
            continue
    return ut


def namner_person(text, namn):
    """Nämner texten ett av personnamnen: som hela ord (också med genitiv-s och med annat än mellanslag emellan), och
    hopskrivet ("AnnaSvensson"); URL-kodning och diakriter döljer inget."""
    import skapande
    vt = skapande.vik(urllib.parse.unquote(str(text)))
    hop = re.sub(r'[^a-z0-9]+', '', vt)
    for n in namn:
        delar = n.split()
        if re.search(r'(?<![a-z0-9])%s(?:s)?(?![a-z0-9])' % r'[^a-z0-9]+'.join(map(re.escape, delar)), vt):
            return True
        if len(delar) > 1 and len(''.join(delar)) >= 8 and ''.join(delar) in hop:
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
        return 'verktyget %s är inte ett av flödets verktyg hos Refero och Mobbin; anropet stoppas' % namn
    if namn == MOBBIN_SKARMAR and str((anrop.get('tool_input') or {}).get('mode') or '').strip().lower() not in MOBBIN_LAGEN:
        return ('%s kräver mode "standard": verktygets standardläge deep kostar krediter, och flödet söker i standardläget; '
                'anropet stoppas' % namn)
    personer = personnamn(slug, underlag)
    fritext = list(nycklar(anrop.get('tool_input') or {}))
    for nyckel, varde in falt(anrop.get('tool_input') or {}):
        if ar_id(nyckel, varde):
            if skapande.namner_kunden(varde, {'siffror': forbjudna.get('siffror') or set()}):  # ett id bär aldrig kundens nummer
                return 'anropet till %s har kundens nummer i fältet %s' % (namn, nyckel)
            continue
        if tjanstens_adress(varde):
            if skapande.namner_kunden(urllib.parse.unquote(varde), forbjudna) or namner_person(varde, personer):
                return 'anropet till %s har en adress som nämner kundens uppgifter' % namn
            continue
        fritext.append(varde)
    text = ' '.join(fritext)
    if skapande.namner_kunden(text, forbjudna):
        return ('anropet till %s nämner kundens namn, ort, webbadress, e-post eller nummer; beskriv bara branschen och '
                'vad sökningen ska ge' % namn)
    if namner_person(text, personer):
        return ('anropet till %s nämner ett personnamn ur kundens underlag; frågorna är generiska, utan namn, citat eller '
                'kundens egna texter' % namn)
    if any(skapande.SPARRAD_FORM.search(x) for x in fritext):
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
