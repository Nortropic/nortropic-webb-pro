#!/usr/bin/env python3
"""designfas.py — designfasens band (ägarens beslut 2026-10-13 i BESLUT.md: formgivningen görs lokalt i Astro; bandet i
kunskap/metodkarta.md, Bandet: stationerna). Kandidatflödet gör researchen, planen med tre riktningar, planprövningen
och uppdragsmaterialet och lämnar varje riktning som ett Astro-projekt i kunder/<slug>/kandidater/kNN/sajt
(kandidater.lamna_till_bandet). Därefter är det här verktyget enda skrivaren av riktningarnas versioner: en utsedd
utförare, en interaktiv Claude Code-session i repots rot (./design.sh <slug>, skillen designfas), arbetar i projekten och
sparar varje stations insats som en version. Code gör research, material, specialistbedömningar och kontroller som
lämnar underlag. Spåret står privat i underlag/<slug>/design/:

    ny <slug>                                   designfasen startar i läget astro: DESIGNFAS.json
    riktningar <slug> kNN …                     riktningarna registrerade i bandet (kandidatflödet gör det själv)
    version <slug> --ritning kNN --orsak TEXT [--station S] [--hoppa S="skäl" …] [--paket namn@version …]
            [--bestallning B001 …] [--av utforaren|agaren]   vNN ur riktningens projekt: paketen vid behov, bygget, källan
                                                i kalla/, dist i sida/, startsidan och undersidorna renderade i 390/768/1440
                                                med kontrollerna, och stationens insats prövad mot förra versionen av riktningen
    rendera <slug> vNN [--kontroll]             om renderingen (och axe med meny och formulärfel, stilrapporten, detektorn)
    station <slug> <station> --ritning kNN      stationens arbetsinstruktion ur metodkartans band (en station i taget)
    artefakt <slug> kNN [--url URL --version vNN]   ägarens visning: paketet för riktningens privata artefakt
                                                (design/artefakt/kNN/ med FILER.json); med --url registreras publiceringen
    bestall <slug> --typ T --version vNN --ritning kNN|* --uppgift TEXT [--station S] [--material …]   en specialistbeställning
    specialist <slug> BNNN                      kör beställningen som ett pass i repot (rollens kompetensblock, kvitto)
    svar <slug> BNNN --fil SVAR.md --utforare TEXT       ett svar som gjorts på annat sätt (manuell överlämning)
    infor <slug> BNNN --version vNN --bedomning TEXT     beställningens resultat infört i en version, med bedömningen
    godkann <slug> vNN --ritning kNN [--text TEXT]   ÄGARENS designgodkännande (nekas sessionerna; ägaren kör det själv)
    overlamna <slug> [--prova]                  överlämningspaketet till helbygget ur den godkända versionen, med kalla/
    status <slug> · kvitto <slug> --session ID [--pass skapa] · karta --prova · start <slug> [--skriv-bara]
    inventera [--placera]                       förmågorna mot kartan; --placera skriver stationerna, flödena och preliminära
                                                rader för nya skills och filer (underhållet kör det vid varje skillintag)

Läget duk (Claude Design, kunskap/claude-design.md) står kvar men är pausat: ny --kanvas, runtime, tillgang och
version --fran nekas utom med NWP_DESIGNLAGE=duk. Designgodkännande, byggstart och publicering är tre beslut: godkann
startar inget, kor.sh tar vid först när ägaren startar bygget (och lägger den godkända källan i kunder/<slug>/sajt med
installera_godkand), och publiceringen är lanseringens eget steg (kunskap/lansering.md). Slutkoder: 0 klart, 1 en kontroll
eller ett bygge föll eller något saknas, 2 fel i anropet.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
SKILLS = ROOT / '.claude' / 'skills'
KARTA = ROOT / 'kunskap' / 'metodkarta.md'
DESIGNTYP = 'https://claude.ai/artifact/QKN21svewxgyPb6SYRqWnd'  # Design-typen (kanvas med ritningar), prövad 2026-10-12
SYSTEMTYP = 'https://claude.ai/artifact/5M7UeXXcx16TP3vzVFNDzd'  # Design System-typen
NAMN = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.-]{0,200}\.dc\.html$')
BLOB = re.compile(r'/_blob/([0-9a-f]{32})')
VERSION = re.compile(r'^v(\d{2,3})$')
BEST = re.compile(r'^B(\d{3})$')
KANVAS = re.compile(r'^https://claude\.ai/(?:code/)?artifact/[A-Za-z0-9-]{10,64}$')
BREDDER = (390, 768, 1440)
MATTSTOCK = UNDERLAG / 'niva' / 'MATTSTOCK.md'  # ägarens kvalitetsribba, satt genom Apple/Nike-beskedet (ägarens besked 2026-10-12)
LAGEN = ('astro', 'duk')  # astro: riktningarna i kundens Astro-projekt (ägarens beslut 2026-10-13); duk: Claude Design, pausat
PAUSAT = ('%s hör till läget duk (Claude Design), som är pausat sedan ägarens beslut 2026-10-13 (BESLUT.md, tillägget '
          '2026-10-13: formgivningen lokalt i Astro): riktningarna görs i kundens Astro-projekt. NWP_DESIGNLAGE=duk släpper '
          'läget för ett undantag som ägaren beslutat')
BANDET = ('riktningarna för %s är i designfasens band (underlag/%s/design/DESIGNFAS.json): designfas.py är enda skrivaren av '
          'deras versioner, och utföraren startas med ./design.sh %s. Ett val, en förfining eller ett uppdrag i Code väntar tills '
          'bandet är klart; ägaren kommenterar i riktningens artefakt och godkänner med designfas.py godkann')
KALLFILER = ('package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json', 'components.json', '.npmrc', 'DESIGN.md', 'RIKTNING.md')
KALLKATALOGER = ('src', 'public')
MALLSIDOR = ('404.html', 'tack/index.html', 'fel/index.html', 'mottagen/index.html')  # mallens egna sidor (kandidater.MALLSIDOR)
MAX_SIDOR = 4  # startsidan och högst tre undersidor renderas per version; resten står i versionens ej_renderade
NPMRC_SAJT = {'ignore-scripts': 'true', 'save-exact': 'true', 'registry': 'https://registry.npmjs.org/'}  # punkt 5, beslutet 2026-10-13
ARTEFAKT_FILER = 255  # Artifact-verktyget: högst 255 filer per publicering (prövat 2026-10-13)
ARTEFAKT_BYTE = 15 * 1024 * 1024  # och högst 15 MB per binärfil, 16 MB per sida
# beställningens typ → specialistpasset (metodkartans kompetensblock: rollen som har passet) och om passet söker på webben
TYPER = {
    'referenser': ('ds_research', True, 'referenser och förebilder för en uppgift (bransch, visuell inspiration eller implementationsgrund) ur Refero, Mobbin, 21st och webben'),
    'komponent': ('ds_komponent', False, 'en komponent eller ett tema ur 21st som implementationsgrund, sökt, vald och hämtad med kod, licens och beroenden'),
    'typografi': ('ds_typografi', False, 'typografisk analys: typskala, hierarki, radlängd, kontraster och färgroller i versionen'),
    'innehall': ('ds_innehall', False, 'texten och besökarens uppgift: rubriker, knappar och etiketter i verksamhetens ord, med belägg'),
    'responsiv': ('ds_responsiv', False, 'responsiv granskning: mobilens omställning, mellanbredden och brytpunkterna'),
    'rorelse': ('ds_rorelse', False, 'interaktion och rörelse: beteenden med syfte, teknikval, reducerad rörelse'),
    'granskning': ('ds_granskning', False, 'tillgänglighet och visuell granskning i tillstånden (meny, fokus, formulärfel), axe och heuristikerna'),
    'kritik': ('ds_kritik', False, 'kritik av den renderade versionen som en besökare ser den, före skaparens förklaring'),
    'bild': ('ds_bild', False, 'bildregi och bildurval: kundens bilder, beskärning och bildernas uppgift mot referensens kvalitet'),
    'jamforelse': ('ds_jamforelse', False, 'falsk variation mellan riktningarna: par som bara skiljer sig i färg, typsnitt eller bilder'),
}
# beställningstypens station i bandet när ingen anges (metodkartan, Bandet: stationerna)
STATION_FOR_TYP = {'referenser': 'underlag', 'komponent': 'komposition', 'bild': 'komposition', 'typografi': 'typografi',
                   'innehall': 'innehall', 'responsiv': 'responsiv', 'rorelse': 'rorelse', 'granskning': 'tillganglighet',
                   'kritik': 'kritik', 'jamforelse': 'jamforelse'}
SVAR_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['sammanfattning', 'fynd', 'forslag', 'referenser', 'begransningar', 'kompetens'],
    'properties': {
        'sammanfattning': {'type': 'string', 'maxLength': 2400},
        'fynd': {'type': 'array', 'maxItems': 24, 'items': {'type': 'object', 'additionalProperties': False,
                 'required': ['plats', 'tillstand', 'vad', 'belagg', 'allvar'],
                 'properties': {'plats': {'type': 'string'}, 'tillstand': {'type': 'string'}, 'vad': {'type': 'string'},
                                'belagg': {'type': 'string'}, 'allvar': {'type': 'integer', 'minimum': 0, 'maximum': 4}}}},
        'forslag': {'type': 'array', 'maxItems': 16, 'items': {'type': 'object', 'additionalProperties': False,
                    'required': ['vad', 'varfor', 'kalla'],
                    'properties': {'vad': {'type': 'string'}, 'varfor': {'type': 'string'}, 'kalla': {'type': 'string'},
                                   'varden': {'type': 'string'}}}},
        'referenser': {'type': 'array', 'maxItems': 24, 'items': {'type': 'object', 'additionalProperties': False,
                       'required': ['kalla', 'id', 'visar', 'anvandning'],
                       'properties': {'kalla': {'type': 'string'}, 'id': {'type': 'string'}, 'adress': {'type': 'string'},
                                      'bild_url': {'type': 'string'}, 'visar': {'type': 'string'}, 'anvandning': {'type': 'string'},
                                      'licens': {'type': 'string'}, 'kod': {'type': 'string'}}}},
        'begransningar': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 12},
        'atergang': {'type': 'object', 'additionalProperties': False, 'required': ['till', 'skal'],
                     'properties': {'till': {'type': 'string', 'enum': ['fortsatt', 'underlag', 'innehall', 'art', 'komposition', 'detaljer']},
                                    'skal': {'type': 'string', 'maxLength': 800}}},
        'kompetens': {'type': 'object', 'additionalProperties': False, 'required': ['aktiverade', 'lasta', 'valda'],
                      'properties': {'aktiverade': {'type': 'array', 'items': {'type': 'string'}},
                                     'lasta': {'type': 'array', 'items': {'type': 'string'}},
                                     'valda': {'type': 'array', 'items': {'type': 'string'}},
                                     'misslyckade': {'type': 'array', 'items': {'type': 'string'}}}},
    },
}
# byggstandardens avsnitt som varje specialistpass bedömer mot (tillägget 2026-10-12, punkt 5), utöver rollens kärna
STANDARD = {
    'ds_granskning': '2 (HTML och semantik), 3.3 och 3.4 (träffytor, kontrast, fokus), 5 (tillgänglighet) och 6 (formulär)',
    'ds_rorelse': '3.5 (rörelse) och 3.8 (webbläsarstöd)',
    'ds_responsiv': '3.2 och 3.3 (mobilen först, sidledsspill, träffytor), 3.8 och 4.2 och 4.7 (bilder och laddning) och 5.8 (reflow)',
    'ds_typografi': '3.1 (tokens och skala), 3.4 (kontrast) och 4.3 (typsnitt)',
    'ds_kritik': '0 (principer), 9 (innehåll och konvertering) och 3.3–3.5, 5.2 och 5.7 så långt bilderna visar dem',
    'ds_innehall': '9 (innehåll och konvertering) och 7.5 (en sida per tjänst)',
    'ds_bild': '2.4 och 4.2 (bilder) och 9.3 (förtroende, egna bilder)',
}
OVERLAMNING_RUBRIKER = ('Designvärden', 'Komponenter', 'Responsiva regler', 'Interaktionstillstånd och beteenden',
                        'Innehåll, bilder och typsnitt med ursprung', 'Prototypkod som kan återanvändas', 'Öppna frågor',
                        'Endast simulerat')


class Fel(Exception):
    pass


FLODEN = ('research', 'band', 'specialistpass', 'overlamning', 'helbygge', 'granskning', 'leverans', 'underhall', 'systemarbete')
HARLEDDA = ('research', 'band', 'specialistpass', 'overlamning', 'helbygge')  # följer av bandets tabell och kompetensblocken
FORMAGOR = ('.md', '.py', '.mjs', '.js', '.cjs', '.sh', '.csv', '.json', '.yaml')  # en skills filer som är förmågor (inte typsnitt, licenser)
ALLTID = ('kritik', 'tillganglighet')  # körs alltid och kan inte hoppas över (ägarens uppdrag 2026-10-12 ~17:35Z, punkt 3)
TOKEN = re.compile(r'`([^`]+)`')


def stationer(text=None):
    """Bandets stationer i ordning ur metodkartans tabell (avsnittet Designfasen i Claude Design, Bandet: stationerna):
    {id: {namn, indata, fraga, karna, alternativ, mcp, pass, utdata, kontroll, kors}}. Tabellen är den enda definitionen."""
    text = KARTA.read_text(encoding='utf-8') if text is None else text
    del_ = text.split('### Bandet: stationerna', 1)
    if len(del_) < 2:
        return {}
    ut = {}
    for rad in del_[1].split('\n### ', 1)[0].splitlines():
        m = re.match(r'^\| `([a-z]+)` ([^|]+)\|', rad)
        if not m:
            continue
        celler = [c.strip() for c in rad.strip().strip('|').split('|')]
        if len(celler) != 8:
            raise Fel('stationen %s har inte åtta kolumner i metodkartan' % m.group(1))
        karna_t, _, alt_t = celler[3].partition('alternativ:')
        def dela(t):
            toks = TOKEN.findall(t)
            return ([x for x in toks if not x.startswith(('mcp:', 'pass:'))], [x[4:] for x in toks if x.startswith('mcp:')],
                    [x[5:] for x in toks if x.startswith('pass:')])
        kf, km, kp = dela(karna_t)
        af, am, ap = dela(alt_t)
        ut[m.group(1)] = {'id': m.group(1), 'namn': m.group(2).strip(), 'indata': celler[1], 'fraga': celler[2], 'karna': kf,
                          'alternativ': af, 'mcp': km + am, 'pass': kp + ap, 'metoder': TOKEN.findall(celler[4]), 'utdata': celler[5],
                          'kontroll': celler[6], 'kors': celler[7]}
    return ut


def filen(f):
    """Filen ur en token i bandets tabell: `väg`, `väg rad a–b, c–d` eller `väg # rubrik` (samma form som metodkartans
    utdrag, metod.utdrag), så att ett radutdrag i en station prövas och låses som utdragen (inventeringen 2026-10-12)."""
    return re.split(r' (?:rad |# )', f, 1)[0].strip()


def metoder(text=None):
    """Metodtabellen i samma avsnitt (Metoderna i arbetet): {id: {'kalla': första kolumnen, 'princip'}}."""
    text = KARTA.read_text(encoding='utf-8') if text is None else text
    del_ = text.split('### Metoderna i arbetet', 1)
    if len(del_) < 2:
        return {}
    ut = {}
    for rad in del_[1].split('\n### ', 1)[0].splitlines():
        m = re.match(r'^\| `([a-z]+)` ([^|]+)\| ([^|]+)\|', rad)
        if m:
            ut[m.group(1)] = {'id': m.group(1), 'kalla': m.group(2).strip(), 'princip': m.group(3).strip()}
    return ut


def station(sid, text=None):
    st = stationer(text)
    if sid not in st:
        raise Fel('okänd station %r; bandet har %s' % (sid, ', '.join(st)))
    return st[sid]


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def skriv(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name('.%s.tmp' % p.name)
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rot(slug, underlag=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,80}', slug or ''):
        raise Fel('ogiltig slug: %r' % slug)
    return Path(underlag or UNDERLAG) / slug / 'design'


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def aktiv(slug, underlag=None):
    """Sant när kunden har en designfas: kandidatflödet lämnar då riktningarna till bandet efter planprövningen
    (kandidater.lamna_till_bandet), och skaparna i Code startar inte."""
    try:
        d = las(rot(slug, underlag) / 'DESIGNFAS.json')
    except Fel:
        return False
    return bool(isinstance(d, dict) and d.get('aktiv'))


def i_bandet(slug):
    """Beskedet när ett val, en förfining eller ett uppdrag i Code möter riktningar i bandet (ateljén, prototyp, domen)."""
    return BANDET % (slug, slug, slug)


def designfas(slug, underlag=None):
    d = las(rot(slug, underlag) / 'DESIGNFAS.json')
    if not isinstance(d, dict):
        raise Fel('ingen designfas för %s: starta med designfas.py ny %s' % (slug, slug))
    return d


def lage(slug, underlag=None):
    """Designfasens läge: 'astro' (riktningarna i kundens Astro-projekt) eller 'duk', det pausade läget i Claude Design.
    En designfas från före beslutet 2026-10-13 saknar fältet och är 'duk' när den har en registrerad duk."""
    d = designfas(slug, underlag)
    return d.get('lage') if d.get('lage') in LAGEN else ('duk' if (d.get('kanvas') or {}).get('url') else 'astro')


def duk_pausad(vad):
    """Läget duk är pausat: vad nekas utom med NWP_DESIGNLAGE=duk."""
    if os.environ.get('NWP_DESIGNLAGE') != 'duk':
        raise Fel(PAUSAT % vad)


def kanvas_url(d):
    return (d.get('kanvas') or {}).get('url')


# ---- start och körmiljö -------------------------------------------------------------------------------------------

def ny(slug, kanvas=None, release=None, underlag=None, lage_=None):
    """Designfasen startar för kunden, i läget astro (standard): kandidatflödet lämnar sedan riktningarna till bandet
    efter planprövningen. Läget duk (en registrerad duk, eller lage_='duk') är pausat och kräver NWP_DESIGNLAGE=duk. En
    befintlig designfas behåller sitt läge; ett annat läge är ett nytt beslut, och design/ flyttas till historik först."""
    lage_ = 'duk' if kanvas is not None or lage_ == 'duk' else 'astro'
    if lage_ == 'duk':
        duk_pausad('ny --kanvas')
    if kanvas is not None and not KANVAS.match(kanvas):
        raise Fel('dukens adress ska vara en claude.ai-artefakt (https://claude.ai/artifact/<id>): %r' % kanvas)
    u = Path(underlag or UNDERLAG) / slug
    if not (u / 'VERKSAMHET.json').is_file():
        raise Fel('underlag/%s/VERKSAMHET.json saknas: kundunderlaget kommer först (prototyp.py %s --forbered)' % (slug, slug))
    r = rot(slug, underlag)
    f = r / 'DESIGNFAS.json'
    gammal = las(f) or {}
    if gammal and lage(slug, underlag) != lage_:
        raise Fel('designfasen för %s är i läget %s; ett annat läge är ett nytt beslut: flytta underlag/%s/design/ till historik först'
                  % (slug, lage(slug, underlag), slug))
    d = {'schema': 1, 'slug': slug, 'aktiv': True, 'lage': lage_, 'skapad': gammal.get('skapad') or nu(),
         'fiktiv': bool((las(u / 'VERKSAMHET.json') or {}).get('fiktiv'))}
    if lage_ == 'duk':
        kanvas = kanvas or kanvas_url(gammal)
        if kanvas_url(gammal) not in (None, kanvas):
            raise Fel('designfasen har redan en duk (%s); en ny duk är ett nytt beslut: flytta DESIGNFAS.json till historik först' % gammal['kanvas']['url'])
        d['kanvas'] = {'url': kanvas, 'typ': DESIGNTYP, 'typ_release': release or gammal.get('kanvas', {}).get('typ_release')}
        d['utforare'] = 'en interaktiv Claude Code-session i repots rot med skillen designfas (./design.sh %s)' % slug
    else:
        d['riktningar'] = gammal.get('riktningar') or {}
        d['utforare'] = ('en interaktiv Claude Code-session i repots rot med skillen designfas (./design.sh %s), som arbetar i '
                         'riktningarnas Astro-projekt' % slug)
    skriv(f, d)
    for k in ('versioner', 'bestallningar', 'svar') + (('runtime',) if lage_ == 'duk' else ('riktningar',)):
        (r / k).mkdir(parents=True, exist_ok=True)
    return d


def riktningar(slug, ids, underlag=None, titlar=None):
    """Riktningarna registrerade i bandet (kandidater.lamna_till_bandet efter planprövningen): kNN och projektets väg
    kunder/<slug>/kandidater/kNN/sajt i DESIGNFAS.json, och ett spår per riktning i design/riktningar/kNN/. Därefter är
    designfas.py enda skrivaren av riktningarnas versioner."""
    import atelje
    d = designfas(slug, underlag)
    if lage(slug, underlag) != 'astro':
        raise Fel('riktningar registreras i läget astro; designfasen för %s är i läget %s' % (slug, lage(slug, underlag)))
    rk = d.setdefault('riktningar', {})
    for kid in ids:
        if not re.fullmatch(r'k\d{2}', str(kid)):
            raise Fel('en riktning heter kNN (kandidatens id): %r' % kid)
        try:
            p = atelje.saker_vag(atelje.KUNDER / slug / 'kandidater' / kid / 'sajt', atelje.KUNDER / slug)
        except RuntimeError as e:
            raise Fel('riktningens projekt: %s' % e)
        if not (p / 'package.json').is_file():
            raise Fel('riktningens projekt saknas: %s (kandidater.forbered_projekt)' % rel(p))
        forr = rk.get(kid) or {}
        rk[kid] = {'projekt': rel(p), 'titel': (titlar or {}).get(kid) or forr.get('titel'), 'registrerad': forr.get('registrerad') or nu()}
        (rot(slug, underlag) / 'riktningar' / kid).mkdir(parents=True, exist_ok=True)
    skriv(rot(slug, underlag) / 'DESIGNFAS.json', d)
    return rk


def projekt(slug, rid, underlag=None):
    """Riktningens Astro-projekt ur DESIGNFAS.json, prövat utan länk i vägen under kunder/<slug>/."""
    import atelje
    rk = designfas(slug, underlag).get('riktningar') or {}
    if rid not in rk:
        raise Fel('riktningen %s finns inte i bandet (riktningarna: %s); kandidatflödet lämnar dem (prototyp.py %s)' % (
            rid, ', '.join(rk) or 'inga', slug))
    p = Path(rk[rid]['projekt'])
    p = p if p.is_absolute() else ROOT / p
    try:
        return atelje.saker_vag(p, atelje.KUNDER / slug)
    except RuntimeError as e:
        raise Fel('riktningens projekt: %s' % e)


def runtime(slug, fil, release, underlag=None):
    duk_pausad('runtime')
    p = Path(fil)
    if not p.is_file() or p.stat().st_size < 10000:
        raise Fel('körmiljön saknas eller är för liten: %s' % fil)
    if not re.fullmatch(r'[0-9a-z-]{4,40}', release or ''):
        raise Fel('ogiltig release: %r' % release)
    m = rot(slug, underlag) / 'runtime' / release
    m.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, m / 'dc-runtime.js')
    post = {'release': release, 'sha256': sha(m / 'dc-runtime.js'), 'byte': p.stat().st_size, 'tid': nu(),
            'kalla': 'Design-typens artifact-type/dc-runtime.js, läst ur duken med Artifact read; Anthropics kod, aldrig i git'}
    skriv(m / 'RUNTIME.json', post)
    d = designfas(slug, underlag)
    d['kanvas']['typ_release'] = release
    skriv(rot(slug, underlag) / 'DESIGNFAS.json', d)
    return post


def aktuell_runtime(slug, underlag=None):
    d = designfas(slug, underlag)
    rel_ = (d.get('kanvas') or {}).get('typ_release')
    p = rot(slug, underlag) / 'runtime' / str(rel_) / 'dc-runtime.js'
    post = las(p.parent / 'RUNTIME.json') or {}
    if not rel_ or not p.is_file() or post.get('sha256') != sha(p):
        raise Fel('körmiljön för release %s saknas eller är ändrad: läs artifact-type/dc-runtime.js ur duken och kör designfas.py runtime' % rel_)
    return p, post


MEDIA = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif',
         '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf',
         '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json'}


def tillgang(slug, blob, fil, kalla='', underlag=None):
    duk_pausad('tillgang')
    if not re.fullmatch(r'[0-9a-f]{32}', blob or ''):
        raise Fel('ogiltigt blob-id: %r' % blob)
    p = Path(fil).resolve()
    if not p.is_file() or p.suffix.lower() not in MEDIA:
        raise Fel('filen saknas eller har en typ som duken inte tar: %s' % fil)
    f = rot(slug, underlag) / 'TILLGANGAR.json'
    d = las(f) or {'schema': 1, 'blobs': {}}
    d['blobs'][blob] = {'fil': rel(p), 'sha256': sha(p), 'byte': p.stat().st_size, 'media': MEDIA[p.suffix.lower()],
                        'kalla': kalla[:600], 'tid': nu()}
    skriv(f, d)
    return d['blobs'][blob]


# ---- versioner och rendering --------------------------------------------------------------------------------------

def versioner(slug, underlag=None):
    v = rot(slug, underlag) / 'versioner'
    return sorted((p.name for p in v.iterdir() if p.is_dir() and VERSION.match(p.name)), key=lambda n: int(n[1:])) if v.is_dir() else []


def nasta(slug, underlag=None):
    vs = versioner(slug, underlag)
    return 'v%02d' % (int(vs[-1][1:]) + 1 if vs else 1)


def version(slug, fran=None, artifact_version=None, orsak='', bestallningar=(), av='utforaren', bilder=True, underlag=None,
            station_=None, ritning=None, hoppade=(), paket=()):
    """En ny version i bandet. Läget astro: ur riktningens Astro-projekt (ritning = riktningens id, kNN), med paketen vid
    behov, bygget, källan i kalla/ och dist i sida/ (_version_projekt). Läget duk, pausat: ur dukens återlästa filer
    (fran, artifact_version; _version_duk). Versionen kan inte skrivas om (en ändring blir nästa version). En version från
    utföraren bär bandets station och riktningen (vilken station gjorde vad) och hoppade stationer med skäl; insatsen prövas
    i renderingen mot förra versionen av samma riktning."""
    d = designfas(slug, underlag)
    if station_:
        station(station_)
        if not ritning:
            raise Fel('en station gäller en riktning: ange --ritning')
    hopp = {}
    for h in hoppade:
        sid, _, skal = str(h).partition('=')
        station(sid)
        if sid in ALLTID:
            raise Fel('stationen %s körs alltid och kan inte hoppas över' % sid)
        if len(skal.strip()) < 15:
            raise Fel('en överhoppad station behöver sitt skäl (--hoppa %s="varför sidan inte har det stationen gäller")' % sid)
        hopp[sid] = skal.strip()[:400]
    if hopp and not ritning:
        raise Fel('en överhoppad station gäller en riktning: ange --ritning')
    if av not in ('utforaren', 'agaren', 'okand'):
        raise Fel('--av är utforaren, agaren eller okand')
    if not (orsak or '').strip():
        raise Fel('orsaken saknas: vilken återkoppling eller beställning versionen svarar på')
    for b in bestallningar:
        if not (rot(slug, underlag) / 'bestallningar' / ('%s.json' % b)).is_file():
            raise Fel('beställningen %s finns inte' % b)
    if lage(slug, underlag) == 'duk' or fran is not None:
        duk_pausad('version --fran')
        if lage(slug, underlag) != 'duk':
            raise Fel('--fran läser en återläst duk; designfasen för %s är i läget astro, där versionen byggs ur riktningens projekt' % slug)
        return _version_duk(slug, d, fran, artifact_version, orsak, bestallningar, av, bilder, underlag, station_, ritning, hopp)
    if not ritning:
        raise Fel('en version gäller en riktning: ange --ritning kNN (riktningarna: %s)' % (', '.join(d.get('riktningar') or {}) or 'inga'))
    return _version_projekt(slug, d, orsak, bestallningar, av, bilder, underlag, station_, ritning, hopp, paket)


def _version_duk(slug, d, fran, artifact_version, orsak, bestallningar, av, bilder, underlag, station_, ritning, hopp):
    """En version ur dukens återlästa filer (Artifact read med out_dir: KATALOG/project/canvas.json och ritningarna).
    Filerna kopieras oförändrade, hashas och renderas, och dukens notering för versionen läses."""
    if not re.fullmatch(r'[0-9]{6,16}-[0-9a-f]{3,8}', str(artifact_version or '')):
        raise Fel('artifact-version ska vara dukens versions-id ur publiceringen (t.ex. 1791822460-0589): %r' % artifact_version)
    if not (orsak or '').strip():
        raise Fel('orsaken saknas: vilken återkoppling eller beställning versionen svarar på')
    if not d['kanvas'].get('url'):
        raise Fel('duken är inte registrerad: designfas.py ny %s --kanvas <url>' % slug)
    proj = Path(fran) / 'project'
    index = las(proj / 'canvas.json')
    if not isinstance(index, dict) or not isinstance(index.get('boards'), dict):
        raise Fel('%s/canvas.json saknas eller är inte dukens index' % proj)
    ritningar = sorted(p.name for p in proj.glob('*.dc.html') if p.is_file() and not p.is_symlink())
    saknas = [b for b in index['boards'] if b not in ritningar]
    if saknas or any(not NAMN.match(r) for r in ritningar):
        raise Fel('ritningar som indexet nämner saknas (%s), eller ett filnamn duger inte' % ', '.join(saknas))
    if ritning and ritning not in ritningar:
        raise Fel('ritningen %s finns inte på duken' % ritning)
    vs = versioner(slug, underlag)
    for v_ in vs:  # samma artefaktversion två gånger är samma version: ingen dubblett
        if (las(rot(slug, underlag) / 'versioner' / v_ / 'VERSION.json') or {}).get('artifact_version') == artifact_version:
            raise Fel('artefaktversionen %s är redan %s' % (artifact_version, v_))
    v = nasta(slug, underlag)
    vk = rot(slug, underlag) / 'versioner' / v
    (vk / 'kanvas').mkdir(parents=True)
    filer = {}
    for n in ['canvas.json'] + ritningar:
        shutil.copy2(proj / n, vk / 'kanvas' / n)
        filer[n] = sha(vk / 'kanvas' / n)
    refs = sorted({m for r in ritningar for m in BLOB.findall((proj / r).read_text(encoding='utf-8', errors='replace'))})
    kanda = (las(rot(slug, underlag) / 'TILLGANGAR.json') or {}).get('blobs') or {}
    post = {'schema': 1, 'version': v, 'tid': nu(), 'kanvas': d['kanvas']['url'], 'artifact_version': artifact_version,
            'typ_release': d['kanvas'].get('typ_release'), 'av': av, 'orsak': orsak.strip()[:2000],
            'bestallningar': list(bestallningar), 'foregaende': vs[-1] if vs else None, 'filer': filer,
            'ritningar': [{'fil': b, 'titel': (index['boards'][b] or {}).get('title'), 'w': (index['boards'][b] or {}).get('w'),
                           'h': (index['boards'][b] or {}).get('h'), 'sida': (index['boards'][b] or {}).get('expand') == 'fill',
                           'interaktiv': bool((index['boards'][b] or {}).get('is_interactive'))} for b in index['boards']],
            'tillgangar': refs, 'okanda_tillgangar': [b for b in refs if b not in kanda],
            'station': station_, 'ritning': ritning, 'hoppade': hopp, 'notering': notering(index, v),
            'sekunder_sedan_forra': sekunder_mellan((las(rot(slug, underlag) / 'versioner' / vs[-1] / 'VERSION.json') or {}).get('tid') if vs else None, None)}
    post['varningar'] = [] if post['notering'] or av != 'utforaren' else [
        'dukens notering för %s saknas: lägg en anteckning med id "%s" (station, vad som ändrades) i canvas.json' % (v, v)]
    skriv(vk / 'VERSION.json', post)
    with open(rot(slug, underlag) / 'VERSIONER.jsonl', 'a', encoding='utf-8') as fh:
        fh.write(json.dumps({k: post[k] for k in ('version', 'tid', 'artifact_version', 'av', 'orsak', 'bestallningar', 'station', 'ritning', 'hoppade')},
                            ensure_ascii=False) + '\n')
    for b in bestallningar:
        uppdatera_bestallning(slug, b, underlag, status='inford', inford_i=v)
    if bilder:
        post['rendering'] = rendera(slug, v, kontroll=True, underlag=underlag)
        if ritning:
            post['insats'] = insats(slug, v, ritning, underlag)
            skriv(vk / 'VERSION.json', post)
    return post



class ByggFel(Fel):
    """Riktningens projekt gick inte att bygga eller paketen inte att installera: ingen version skrivs (slutkod 1)."""


def bygg(sajt):
    """npm run build i riktningens projekt innanför processgränsen (prova.bygg_inom_grans, kandidatflödets byggväg med
    bygglås och återanvändning av samma indata). Ger (rc, text)."""
    import prova
    return prova.bygg_inom_grans(sajt)


def sidor_i(dist):
    """De byggda sidorna i dist/ som renderas: startsidan först, sedan undersidorna (högst tre kataloger ner, i ordning
    efter djup och namn), utan mallens egna sidor (404, tack, fel, mottagen). Länkar följs inte."""
    dist = Path(dist)
    ut = []
    for f in dist.rglob('*.html'):
        r = f.relative_to(dist)
        if f.is_symlink() or not f.is_file() or len(r.parts) > 4 or r.as_posix() in MALLSIDOR or r.parts[0] == '_astro':
            continue
        if any((dist / Path(*r.parts[:i])).is_symlink() for i in range(1, len(r.parts))):
            continue
        ut.append(r.as_posix())
    return sorted(ut, key=lambda x: (x != 'index.html', x.count('/'), x))


def sidor(post):
    """Versionens renderade sidor: läget astro har sidorna (index.html, om/index.html), läget duk ritningarna."""
    if post.get('lage') == 'astro':
        return list(post.get('sidor') or [])
    return [r['fil'] for r in post.get('ritningar') or []]


def stam(namn):
    """Bildernas stam för en sida eller ritning: utan .dc.html eller .html, med / som - (rendera.mjs gör samma)."""
    return re.sub(r'\.dc\.html$|\.html$', '', namn).replace('/', '-')


def bildsida(post_eller_lage, ritning=None):
    """Sidan vars bilder bär en riktning: startsidan (index.html) i läget astro, ritningen själv i läget duk."""
    lage_ = post_eller_lage.get('lage') if isinstance(post_eller_lage, dict) else post_eller_lage
    return 'index.html' if lage_ == 'astro' else ritning


def kopiera_kalla(slug, p, mal):
    """Projektets källa till versionens kalla/: src/, public/, package.json, låset, astro.config.mjs, tsconfig.json,
    components.json, .npmrc, DESIGN.md och RIKTNING.md, utan länkar. Delar projektet sajtens node_modules (länken ur
    kandidater.forbered_projekt) och saknar eget lås, byggs det ur sajtens package-lock.json, och det låset följer med.
    Ger ({relativ väg: sha256}, låsets ursprung)."""
    import atelje
    import kandidater
    filer = {}
    for k in KALLKATALOGER:
        if (p / k).is_dir() and not (p / k).is_symlink():
            filer.update({'%s/%s' % (k, x): s for x, s in kandidater.kopiera(p / k, mal / k).items()})
    for n in KALLFILER:
        if (p / n).is_file() and not (p / n).is_symlink():
            mal.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p / n, mal / n)
            filer[n] = sha(mal / n)
    las_ = 'projektets'
    if 'package-lock.json' not in filer:
        delad = atelje.KUNDER / slug / 'sajt' / 'package-lock.json'
        if (p / 'node_modules').is_symlink() and delad.is_file() and not delad.is_symlink():
            shutil.copyfile(delad, mal / 'package-lock.json')
            filer['package-lock.json'] = sha(mal / 'package-lock.json')
            las_ = 'sajtens (projektet delar sajtens node_modules)'
        else:
            las_ = None
    return filer, las_


def _version_projekt(slug, d, orsak, bestallningar, av, bilder, underlag, station_, rid, hopp, paket):
    """En version ur riktningens Astro-projekt: paketen (--paket, eller kandidater.paketbehov), bygget, källan i
    kalla/ och dist i sida/, och renderingen av startsidan och undersidorna med kontrollerna. Kandidatens skrivlås hålls
    under arbetet (en skrivare per projekt). Ett bygge som faller ger ingen version."""
    import kandidater
    p = projekt(slug, rid, underlag)
    if not (p / 'package.json').is_file() or not (p / 'src' / 'pages' / 'index.astro').is_file():
        raise Fel('riktningens projekt saknar package.json eller startsidan (src/pages/index.astro): %s' % rel(p))
    titel = ((d.get('riktningar') or {}).get(rid) or {}).get('titel')
    with kandidater.skrivlas(slug, rid, vanta=120, vem='designfasens version'):
        paket_ = None
        if paket or kandidater.paketbehov(slug, rid):
            rc_p, text_p = kandidater.egna_paket(slug, rid, list(paket))
            paket_ = {'begarda': list(paket), 'rc': rc_p, 'text': ' '.join(text_p.split())[-600:]}
            if rc_p:
                raise ByggFel('paketen kunde inte installeras i %s (rc %s): %s' % (rel(p), rc_p, ' '.join(text_p.split())[-400:]))
        rc, text = bygg(p)
        if rc:
            raise ByggFel('bygget av %s föll; ingen version skrevs: %s' % (rel(p), ' '.join(str(text).split())[-600:]))
        dist = p / 'dist'
        alla = sidor_i(dist)
        if 'index.html' not in alla:
            raise ByggFel('bygget gav ingen startsida (%s/dist/index.html)' % rel(p))
        vs = versioner(slug, underlag)
        v = nasta(slug, underlag)
        vk = rot(slug, underlag) / 'versioner' / v
        vk.mkdir(parents=True)
        filer, las_ = kopiera_kalla(slug, p, vk / 'kalla')
        kandidater.kopiera(dist, vk / 'sida')
    forra = [x for x in vs if (las(rot(slug, underlag) / 'versioner' / x / 'VERSION.json') or {}).get('ritning') == rid]
    post = {'schema': 1, 'lage': 'astro', 'version': v, 'tid': nu(), 'av': av, 'orsak': orsak.strip()[:2000],
            'bestallningar': list(bestallningar), 'foregaende': vs[-1] if vs else None, 'forra_i_riktningen': forra[-1] if forra else None,
            'ritning': rid, 'riktning': {'id': rid, 'titel': titel, 'projekt': rel(p)}, 'station': station_, 'hoppade': hopp,
            'filer': filer, 'las': las_, 'paket': paket_, 'sidor': alla[:MAX_SIDOR], 'ej_renderade': alla[MAX_SIDOR:],
            'sekunder_sedan_forra': sekunder_mellan((las(rot(slug, underlag) / 'versioner' / vs[-1] / 'VERSION.json') or {}).get('tid') if vs else None, None)}
    post['varningar'] = [x for x, ok in (
        ('RIKTNING.md saknas i projektet: riktningens underlag (referenslåset, språket, skälen för en lättad CSP) står där',
         'RIKTNING.md' in filer),
        ('låset saknas: varken projektet eller sajten har package-lock.json, så paketen följer inte med till helbygget', las_)) if not ok]
    skriv(vk / 'VERSION.json', post)
    with open(rot(slug, underlag) / 'VERSIONER.jsonl', 'a', encoding='utf-8') as fh:
        fh.write(json.dumps({k: post.get(k) for k in ('version', 'tid', 'av', 'orsak', 'bestallningar', 'station', 'ritning', 'hoppade')},
                            ensure_ascii=False) + '\n')
    for b in bestallningar:
        uppdatera_bestallning(slug, b, underlag, status='inford', inford_i=v)
    if bilder:
        post['rendering'] = rendera(slug, v, kontroll=True, underlag=underlag)
        post['insats'] = insats(slug, v, rid, underlag)
        skriv(vk / 'VERSION.json', post)
    return post


def notering(index, v):
    """Dukens anteckning för versionen (canvas.json notes med id v eller en text som börjar med v), eller None."""
    notes = (index or {}).get('notes') or {}
    if not isinstance(notes, dict):
        return None
    n = notes.get(v)
    if not isinstance(n, dict):
        n = next((x for x in notes.values() if isinstance(x, dict) and str(x.get('text') or '').strip().startswith(v + ' ')), None)
    return str(n.get('text'))[:600] if isinstance(n, dict) and n.get('text') else None


def sekunder_mellan(a, b):
    try:
        t0 = datetime.strptime(a, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        t1 = datetime.strptime(b, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) if b else datetime.now(timezone.utc)
        return int((t1 - t0).total_seconds())
    except (TypeError, ValueError):
        return None


def forra_med(slug, v, ritning, underlag=None):
    """Den senaste versionen före v av samma riktning med bilder av den: i läget astro en version vars ritning är
    riktningen (kNN) och som har startsidans bilder, i läget duk en version som har ritningen."""
    vs = versioner(slug, underlag)
    for v_ in reversed(vs[:vs.index(v)] if v in vs else vs):
        vk = rot(slug, underlag) / 'versioner' / v_
        post = las(vk / 'VERSION.json') or {}
        b = (las(vk / 'BILDER.json') or {}).get('ritningar') or {}
        if post.get('lage') == 'astro':
            if post.get('ritning') == ritning and 'index.html' in b:
                return v_
        elif ritning in b:
            return v_
    return None


def insats(slug, v, ritning, underlag=None):
    """Syns stationens insats? Helsidan i 390 och 1440 (startsidan i läget astro, ritningen i läget duk) mot förra
    versionen av samma riktning (jamfor.mjs): andelen pixlar som skiljer sig och höjdskillnaden, med bilderna före och
    efter. Mäter förändring, inte kvalitet."""
    f = forra_med(slug, v, ritning, underlag)
    if not f:
        return {'jamfort_med': None, 'synlig': None, 'skal': 'riktningens första version'}
    s = stam(bildsida(las(rot(slug, underlag) / 'versioner' / v / 'VERSION.json') or {}, ritning))
    ut, synlig = {'jamfort_med': f, 'bredder': {}}, False
    for w in (390, 1440):
        a_ = rot(slug, underlag) / 'versioner' / f / 'bilder' / ('%s-%d.png' % (s, w))
        b_ = rot(slug, underlag) / 'versioner' / v / 'bilder' / ('%s-%d.png' % (s, w))
        if not a_.is_file() or not b_.is_file():
            ut['bredder'][str(w)] = {'fel': 'bild saknas'}
            continue
        r = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'jamfor.mjs'), '--a', str(a_), '--b', str(b_)],
                           capture_output=True, text=True, timeout=120)
        rad = next((x for x in reversed((r.stdout or '').strip().splitlines()) if x.startswith('{')), '')
        try:
            res = json.loads(rad)
            ut['bredder'][str(w)] = dict({k: res.get(k) for k in ('andel', 'hojdskillnad', 'breddskillnad')}, fore=rel(a_), efter=rel(b_))
            synlig = synlig or (res.get('andel') or 0) > 0.0005 or bool(res.get('hojdskillnad'))
        except ValueError:
            ut['bredder'][str(w)] = {'fel': (r.stderr or r.stdout or 'inget svar')[-200:]}
    ut['synlig'] = synlig
    return ut


def bygg_sida(slug, v, underlag=None):
    """Katalogen som renderas. Läget astro: versionens sida/ (projektets dist), utan körmiljö. Läget duk: en lokal
    katalog som Design-typens körmiljö kan köra, med ritningarna, support.js och dukens tillgångar."""
    vk = rot(slug, underlag) / 'versioner' / v
    post = las(vk / 'VERSION.json')
    if not post:
        raise Fel('versionen %s finns inte' % v)
    if post.get('lage') == 'astro':
        if not (vk / 'sida' / 'index.html').is_file():
            raise Fel('versionen %s saknar sin byggda sida (sida/index.html)' % v)
        return vk / 'sida', [], {}
    rt, rtpost = aktuell_runtime(slug, underlag)
    s = vk / 'sida'
    if s.exists():
        shutil.rmtree(s)
    (s / '_blob').mkdir(parents=True)
    shutil.copy2(rt, s / 'support.js')
    for r in post['ritningar']:  # dukens fil oförändrad i kanvas/; den renderade kopian får en viewport-meta, som duken ger
        # genom ramens bredd, så att axe och stilrapporten med mobilemulering mäter 390 och inte en layout på 980 px
        t = (vk / 'kanvas' / r['fil']).read_text(encoding='utf-8', errors='replace')
        if 'name="viewport"' not in t:
            t = re.sub(r'(<head[^>]*>)', r'\1\n<meta name="viewport" content="width=device-width, initial-scale=1">', t, count=1, flags=re.I)
        (s / r['fil']).write_text(t, encoding='utf-8')
    kanda = (las(rot(slug, underlag) / 'TILLGANGAR.json') or {}).get('blobs') or {}
    index, saknade = {}, []
    for b in post['tillgangar']:
        k = kanda.get(b)
        p = ROOT / k['fil'] if k else None
        if not k or not p.is_file() or sha(p) != k['sha256']:
            saknade.append(b)
            continue
        shutil.copy2(p, s / '_blob' / b)
        index[b] = k['media']
    (s / '_blob' / 'index.json').write_text(json.dumps(index), encoding='utf-8')
    return s, saknade, rtpost


def rendera(slug, v, kontroll=False, underlag=None):
    vk = rot(slug, underlag) / 'versioner' / v
    s, saknade, rtpost = bygg_sida(slug, v, underlag)
    post = las(vk / 'VERSION.json')
    env = dict(os.environ, NWP_SLUG=slug)
    if kontroll:  # impeccables detektor i kontrollen (valideringen 2026-10-12); utan motor körs resten som förut
        import detektor
        m = detektor.motor()
        if m:
            env.update(IMPECCABLE_MOTOR=str(m), IMPECCABLE_SKILL_DIR=str(detektor.SKILL))
    r = subprocess.run(['node', str(ROOT / 'kontroller' / 'designfas' / 'rendera.mjs'), '--sida', str(s), '--ut', str(vk),
                        '--ritningar', ','.join(sidor(post))] + (['--kontroll'] if kontroll else []),
                       capture_output=True, text=True, timeout=900, env=env, cwd=str(ROOT))
    b = las(vk / 'BILDER.json') or {}
    ax = las(vk / 'kontroll' / 'axe' / 'axe.json') if kontroll else None
    if isinstance(ax, dict):  # axe:s "incomplete" för kontrast (t.ex. color-mix()) släpps av grinden: här blir det en varning
        ofull = ['%s %s%s' % (r.get('vy'), r.get('sida'), (' [%s]' % r['tillstand']) if r.get('tillstand') not in (None, 'sida') else '')
                 for r in ax.get('rader') or [] for v in r.get('ofullstandiga') or [] if v.get('id') == 'color-contrast']
        b['axe'] = {'allvarliga': ax.get('allvarliga'), 'totalt': ax.get('totalt'), 'fel': ax.get('fel'), 'ofullstandig_kontrast': ofull,
                    'version': ax.get('axeVersion')}
        for r_, rp_ in (b.get('ritningar') or {}).items():
            if any(('/' + r_) in x for x in ofull):
                rp_.setdefault('varningar', []).append('axe kunde inte avgöra textkontrasten (incomplete) i %s; ge text och bakgrund färdiga '
                                                      'färgvärden (byggstandarden 3.4)' % ', '.join(x for x in ofull if ('/' + r_) in x)[:300])
    b.update({'saknade_tillgangar': saknade, 'slutkod': r.returncode, 'utdata': (r.stdout or '')[-800:], 'fel': (r.stderr or '')[-800:]})
    if rtpost:
        b['runtime'] = {'release': rtpost.get('release'), 'sha256': rtpost.get('sha256')}
    skriv(vk / 'BILDER.json', b)
    return {'slutkod': r.returncode, 'saknade_tillgangar': saknade, 'besked': (r.stdout or r.stderr or '').strip()[-400:]}


# ---- beställningar och specialistpass ------------------------------------------------------------------------------

def bestallningar(slug, underlag=None):
    b = rot(slug, underlag) / 'bestallningar'
    return sorted(p.stem for p in b.glob('B*.json') if BEST.match(p.stem)) if b.is_dir() else []


def bestallning(slug, bid, underlag=None):
    d = las(rot(slug, underlag) / 'bestallningar' / ('%s.json' % bid)) if BEST.match(bid or '') else None
    if not isinstance(d, dict):
        raise Fel('beställningen %s finns inte' % bid)
    return d


def uppdatera_bestallning(slug, bid, underlag=None, **falt):
    d = bestallning(slug, bid, underlag)
    d.setdefault('historik', []).append({'tid': nu(), **{k: v for k, v in falt.items() if k in ('status', 'inford_i', 'utforare')}})
    d.update(falt)
    skriv(rot(slug, underlag) / 'bestallningar' / ('%s.json' % bid), d)
    return d


def bestall(slug, typ, v, ritning, uppgift, material=(), underlag=None, station_=None):
    d = designfas(slug, underlag)
    if typ not in TYPER:
        raise Fel('okänd typ %r; välj %s' % (typ, ', '.join(TYPER)))
    st = station(station_ or STATION_FOR_TYP[typ])
    if TYPER[typ][0] not in st['pass']:
        raise Fel('stationen %s har inte passet %s (typen %s); stationens pass: %s' % (st['id'], TYPER[typ][0], typ, ', '.join(st['pass']) or 'inga'))
    if v not in versioner(slug, underlag):
        raise Fel('versionen %s finns inte; beställningen gäller en sparad version' % v)
    vpost = las(rot(slug, underlag) / 'versioner' / v / 'VERSION.json')
    if vpost.get('lage') == 'astro':
        if ritning not in (vpost.get('ritning'), '*'):
            raise Fel('versionen %s gäller riktningen %s, inte %s (eller * för alla riktningarnas senaste version)' % (v, vpost.get('ritning'), ritning))
    elif ritning not in [r['fil'] for r in vpost['ritningar']] and ritning != '*':
        raise Fel('ritningen %s finns inte i %s (eller * för alla)' % (ritning, v))
    if len((uppgift or '').strip()) < 20:
        raise Fel('uppgiften behöver säga vad som ska undersökas och varför (minst en mening)')
    bs = bestallningar(slug, underlag)
    bid = 'B%03d' % (int(bs[-1][1:]) + 1 if bs else 1)
    if lage(slug, underlag) == 'duk' and not kanvas_url(d):
        raise Fel('duken är inte registrerad: designfas.py ny %s --kanvas <url>' % slug)
    post = {'schema': 1, 'id': bid, 'projekt': slug, 'kanvas': kanvas_url(d), 'lage': lage(slug, underlag), 'version': v, 'ritning': ritning,
            'typ': typ, 'pass': TYPER[typ][0], 'station': st['id'], 'uppgift': uppgift.strip()[:3000], 'material': [str(m)[:300] for m in material][:20],
            'tid': nu(), 'status': 'bestalld', 'resultat': None}
    skriv(rot(slug, underlag) / 'bestallningar' / ('%s.json' % bid), post)
    return post


def senaste_per_riktning(slug, underlag=None):
    """{riktning: senaste version med bilder} i läget astro, i riktningarnas ordning."""
    ut = {}
    for v in versioner(slug, underlag):
        post = las(rot(slug, underlag) / 'versioner' / v / 'VERSION.json') or {}
        if post.get('lage') == 'astro' and post.get('ritning') and (rot(slug, underlag) / 'versioner' / v / 'BILDER.json').is_file():
            ut[post['ritning']] = v
    ordning = list(designfas(slug, underlag).get('riktningar') or {})
    return {r: ut[r] for r in sorted(ut, key=lambda x: (ordning.index(x) if x in ordning else 99, x))}


def specialist_prompt(slug, b, underlag=None):
    vk = rot(slug, underlag) / 'versioner' / b['version']
    astro = b.get('lage') == 'astro' or (las(vk / 'VERSION.json') or {}).get('lage') == 'astro'
    bild = las(vk / 'BILDER.json') or {}
    rader = []
    if astro:  # en riktnings version, eller (*) varje riktnings senaste version sida vid sida för jämförelsen
        versionerna = senaste_per_riktning(slug, underlag) if b['ritning'] == '*' else {b['ritning']: b['version']}
        for rid, v_ in versionerna.items():
            vk_ = rot(slug, underlag) / 'versioner' / v_
            for r, rp in ((las(vk_ / 'BILDER.json') or {}).get('ritningar') or {}).items():
                rader += ['- riktningen %s, %s, sidan %s, %s: %s' % (rid, v_, r, k, rel(vk_ / x['fil'])) for k, x in (rp.get('bilder') or {}).items()]
    else:
        for r, rp in (bild.get('ritningar') or {}).items():
            if b['ritning'] in ('*', r):
                rader += ['- %s, %s: %s' % (r, k, rel(vk / x['fil'])) for k, x in (rp.get('bilder') or {}).items()]
    kritik = b['pass'] == 'ds_kritik'
    u = 'underlag/%s' % slug
    return '\n'.join([
        'Du är ett specialistpass i Nortropics designfas (skillen designfas, bandet i kunskap/metodkarta.md). Designen formges %s'
        ' av en' % ('i riktningarnas Astro-projekt' if astro else 'i Claude Design'),
        'utsedd utförare; du ändrar aldrig designen och skriver inga filer. Du lämnar underlag och förslag i svarsschemat, och',
        'utföraren avgör vad som förs in i nästa version.',
        '',
        'Beställning %s · projekt %s · %s · version %s · %s %s · typ %s (%s)' % (
            b['id'], slug, 'läget astro' if astro else 'duk %s' % b.get('kanvas'), b['version'], 'riktning' if astro else 'ritning',
            b['ritning'], b['typ'], TYPER[b['typ']][2]),
        'Uppgift: ' + b['uppgift'],
        'Berört material: ' + ('; '.join(b['material']) or 'inget utöver versionen'),
        '',
        ('Versionens bilder (lokal rendering av riktningens byggda Astro-sida i Chromium; inte skärmbilder ur en förhandsvisning).'
         ' Läs dem med Read innan du bedömer något; en bredd eller ett tillstånd räknas som bedömt bara ur en bild') if astro else
        ('Versionens bilder (lokal rendering av dukens källa med Design-typens körmiljö, release %s; inte skärmbilder ur Designs'
         ' gränssnitt). Läs dem med Read innan du bedömer något; en bredd eller ett tillstånd räknas som bedömt bara ur en bild' % (
             (bild.get('runtime') or {}).get('release'))),
        'du läst:',
        *rader,
        '' if kritik else ('Versionens källa (projektets src/, public/, package.json och RIKTNING.md): %s/' % rel(vk / 'kalla') if astro else
                           'Versionens källa (ritningarnas .dc.html, dukens format): %s/' % rel(vk / 'kanvas')),
        'Kontrollerna mot samma rendering (axe med menyn öppen och formulären skickade tomma, stilrapporten och impeccables'
        ' detektor i 390 och 1440 under detektor/, med regel, allvar och kategori men utan kodutdrag): %s/. Pröva varje'
        ' detektorfynd mot bilderna och ägarbesluten; ett fynd rättas eller motiveras med namngivet belägg.' % rel(vk / 'kontroll'),
        'Mätningarna och varningarna per ritning och bredd i %s: LCP-kandidaten, layoutskiften, bildernas storlek mot visad storlek,'
        ' rörelsen vid laddningen, efter 5,5 s och med reducerad rörelse, reflow i 320, synlig fokus för de tio första tabbstegen och'
        ' om sidan förändras mellan 6 och 7 s. Varningarna är underlag att pröva i bilderna, inte domar.' % rel(vk / 'BILDER.json'),
        *(['Bedöm mot kunskap/byggstandard.md, avsnitten %s: läs dem innan du bedömer, och ange punktens nummer i varje fynd som gäller'
           ' den.' % STANDARD[b['pass']]] if b['pass'] in STANDARD else []),
        '',
        'Kundens underlag: %s/KUNDFORSTAELSE.md först, sedan BRIEF.md, VERKSAMHET.json, bilder/BILDER.md och vid behov RESEARCH.md'
        ' och TEXTUNDERLAG.md. Sanning: varje namn, tal och påstående om verksamheten har belägg där. Designreglerna:' % u,
        'kunskap/designregler.md (företrädet: kvalitetskrav, ägarbeslut, kundens behov, hypoteser; en skills standardråd sist).',
        *(['Du bedömer som en besökare: läs inte utförarens anteckningar, beställningens historik eller andra versioner.',
           ('Ägarens måttstock: %s, läs den hel. Nivån är satt genom ägarens besked: Apple och Nike är ledtrådar till '
            'kvalitetsribban, inte mallar; bedöm precisionen på den nivån, inte ägarens stil, och om designen själv visar varför '
            'riktningen passar kunden. Säg vad i bilderna bedömningen bygger på.' % rel(MATTSTOCK))
           if MATTSTOCK.is_file() else
           'Ägarens måttstock (underlag/niva/MATTSTOCK.md) saknas i den här miljön: din ribba är kvalitetskraven, standarden och litteraturen; säg det i sammanfattningen.',
           'Besvara granskningsfrågorna i kunskap/granskningsfragor.md (läs filen hel), var och en med bredden och bilden svaret bygger på.',
           'Din dom är en AI-bedömning: skriv den som din, aldrig som ägarens, och ändra ingenting.'] if kritik else []),
        '',
        *station_rader(station(b.get('station') or STATION_FOR_TYP[b['typ']])),
        '',
        'Externa tjänster (Refero, Mobbin, 21st, Motion, webben) får bara generiska frågor: bransch, uppgift och stil, aldrig kundens'
        ' namn, orter, nummer eller citat (kundvakten stoppar annat). En referens är en observation med plats, aldrig belägg för en'
        ' sajts affärsmässiga framgång; sökrankning, omdömen och utmärkelser är inget sådant belägg.',
        'Svara i schemat: fynden med plats, tillstånd och belägg (allvar 0–4 enligt Nielsen), förslagen med skäl och källa'
        ' (skill, tjänst eller verktyg), referenserna med id, adress, bild_url när tjänsten gav en, vad de visar och hur de kan'
        ' användas (kod och licens för en komponent), begränsningarna, och i kompetens det du faktiskt aktiverade, läste och valde.'])


def station_rader(st):
    """Stationens arbetsinstruktion: frågan, skills och tjänster bara för stationen, utdata och kontroll (en station i taget;
    ägarens uppdrag 2026-10-12 ~17:35Z, punkt 2)."""
    import kompetens
    anrop = set(kompetens.anvandaranropade(ROOT)) | set(kompetens.vantande_skills(ROOT))  # användaranropade och Initial Response: Read
    def visa(f):
        namn = f.split('/')[0]
        if filen(f) != f:  # ett rad- eller rubrikutdrag: bara de raderna, aldrig hela skillen
            import metod
            try:  # rubrikutdraget upplöst till rader, så att Read får offset och limit direkt
                rader = ', '.join('%d–%d' % ab for ab in metod.utdrag(f)['intervall'])
            except metod.MetodFel:
                rader = ''
            return '%s (läs bara utdraget med Read, offset och limit%s)' % (f, (': rad ' + rader) if rader and ' # ' in f else '')
        return '%s (%s)' % (f, 'läs hel med Read' if f.startswith(('kunskap/', 'kritik/')) or '/reference' in f or namn in anrop
                            or not f.endswith('SKILL.md') else 'aktivera med Skill')
    ordning = list(stationer())
    met = metoder()
    a11y = st['id'] in ordning and 'art' in ordning and ordning.index(st['id']) >= ordning.index('art') and st['id'] not in ('jamforelse', 'overlamning')
    return ['Stationen %s, %s (kunskap/metodkarta.md, Bandet: stationerna).' % (st['id'], st['namn']),
            'Stationens fråga: ' + st['fraga'],
            'Stationens metod (metodtabellen, källa och princip): ' + '; '.join(
                '%s: %s, %s' % (x, met[x]['kalla'], met[x]['princip']) for x in st.get('metoder') or [] if x in met) + '.',
            *(['Tillgängligheten är ett krav också i den här stationen (W3C WAI, under utformningen; WCAG 2.2 AA): riktiga knappar, '
               'länkar och fält, kontrast 4,5:1 för text och 3:1 för kontroller och fokus (1.4.11), färg aldrig ensam (1.4.1), synlig '
               'fokus som inte döljs av fasta sidhuvuden (2.4.11), träffytor minst 24 px (2.5.8) och reflow i 320; ägarens golv: '
               'primära kontroller minst 44 px och reducerad rörelse. Renderingen prövar det axe och mätningarna når vid varje '
               'version. Rita och pröva 390 först.'] if a11y else []),
            *(['Tillgängligheten i innehållet (W3C WAI): rubrikordningen, länktexter som säger vart de leder och textalternativ per '
               'bildplats bestäms här. Rita 390 först: besökarens toppuppgift och den primära handlingen ska synas i första skärmen.']
              if st['id'] == 'innehall' else []),
            'Stationens skills, bara för den här frågan: ' + '; '.join(visa(f) for f in st['karna']) + '.',
            *(['Alternativ efter riktningen: ' + '; '.join(visa(f) for f in st['alternativ']) + '.'] if st['alternativ'] else []),
            *(['Tjänster (bakom kundvakten, generiska frågor): ' + ', '.join(st['mcp']) + '.'] if st['mcp'] else []),
            'Andra skills är inte stationens auktoritet här; säger stationens skills emot en annan regel avgör metodkartans Avgöranden och'
            ' kunskap/designregler.md. En aktivering eller läsning som misslyckas skriver du i svaret.',
            'Stationens utdata: ' + st['utdata'] + '. Kontrollen i renderingen: ' + st['kontroll'] + '.']


def kvitto_station(sessioner, pass_, st):
    """Kvittot mot stationens skills (inte rollens hela kärna): tillgång, aktivering och läsning, anrop och utfall var för
    sig. Det fäller ingenting; läsning är ingen insats (ägarens uppdrag 2026-10-12 ~17:35Z, punkt 4)."""
    import kompetens
    karna = list(dict.fromkeys(filen(f) for f in st['karna']))
    valj = [f for f in dict.fromkeys(filen(f) for f in st['alternativ']) if f not in karna]
    k = {st['id']: {'id': st['id'], 'namn': st['namn'], 'uppgift': st['fraga'], 'pass': [pass_], 'karna': karna, 'efter': [],
                    'efter_i_karna': [], 'valj': valj, 'verktyg': [], 'mcp': st['mcp'], 'mcp_krav': [], 'visar': st['kontroll']}}
    kv = kompetens.kvitto(sessioner, pass_, k=k)
    return kv, kompetens.kravbrister(kv, pass_, k=k)


def specialist(slug, bid, underlag=None, modell=None, frist=None):
    """Beställningen som ett pass i repot: atelje.session med rollens kompetensblock (kompetens.verktyg), kundvakten och
    MCP-konfigurationen för slug, svaret i SVAR_SCHEMA och kvittot ur transkriptet (kompetens.kvitto, kravbrister)."""
    import atelje
    import kompetens
    b = bestallning(slug, bid, underlag)
    if b['status'] not in ('bestalld', 'fel'):
        raise Fel('beställningen %s är %s' % (bid, b['status']))
    pass_, webb, _ = TYPER[b['typ']]
    sk = rot(slug, underlag) / 'svar' / bid
    sk.mkdir(parents=True, exist_ok=True)
    uppdatera_bestallning(slug, bid, underlag, status='pagar', utforare='specialistpass %s (claude -p i repot)' % pass_)
    t0 = nu()
    svar = atelje.session(specialist_prompt(slug, b, underlag), ['Read', 'Glob', 'Grep'] + kompetens.verktyg(pass_, slug),
                          sk / 'svar-session.json', SVAR_SCHEMA, 120, modell or atelje.MODELL, atelje.EFFORT,
                          frist or 2400, slug=slug, webb=webb)
    so = svar.get('structured_output') if isinstance(svar, dict) else None
    st = station(b.get('station') or STATION_FOR_TYP[b['typ']])
    kv, ej_observerat = kvitto_station([svar], pass_, st)
    post = {'schema': 1, 'id': bid, 'pass': pass_, 'station': st['id'], 'session_id': svar.get('session_id'), 'start': t0, 'slut': nu(),
            'sekunder': sekunder_mellan(t0, nu()), 'utfall': 'levererad' if isinstance(so, dict) else 'fel', 'svar': so, 'kvitto': kv,
            'ej_observerat': ej_observerat,
            'nivaer': 'tillgång, aktivering och läsning, verktygsanrop och resultat står i kvittot; tillämpning i designen och '
                      'kvalitet bedöms först i versionen som för in svaret, av utföraren och ägaren',
            'kostnad_listpris_usd': svar.get('total_cost_usd')}
    if isinstance(so, dict):
        post['bilder'] = ladda_referensbilder(sk, so.get('referenser') or [])
    skriv(sk / 'SVAR.json', post)
    (sk / 'SVAR.md').write_text(svar_md(b, post), encoding='utf-8')
    uppdatera_bestallning(slug, bid, underlag, status='levererad' if isinstance(so, dict) else 'fel',
                          resultat={'fil': rel(sk / 'SVAR.md'), 'ej_observerat': ej_observerat, 'session': svar.get('session_id')})
    return post


def ladda_referensbilder(sk, refs):
    """Tjänsternas bilder till svaret, bara från deras egna bildvärdar (referenstjanster.tillaten_bild och ladda_bild)."""
    import referenstjanster as rt
    ut = []
    for i, r in enumerate(refs[:24]):
        u = str(r.get('bild_url') or '')
        if not u:
            continue
        tj = 'refero' if 'refero' in u else 'mobbin' if 'mobbin' in u else ''
        if not tj or not rt.tillaten_bild(u, tj):
            ut.append({'ref': i, 'url': u[:200], 'utfall': 'inte hämtad: värden är inte tjänstens egen bildvärd'})
            continue
        mal = sk / 'bilder' / ('ref-%02d%s' % (i + 1, Path(u.split('?')[0]).suffix[:5] or '.jpg'))
        mal.parent.mkdir(exist_ok=True)
        try:
            rt.ladda_bild(u, mal)
            ut.append({'ref': i, 'fil': rel(mal), 'sha256': sha(mal)})
        except Exception as e:  # en bild som inte går att hämta är inget material
            ut.append({'ref': i, 'url': u[:200], 'utfall': 'fel: %s' % str(e)[:160]})
    return ut


def svar_md(b, post):
    so = post.get('svar') or {}
    kv = post.get('kvitto') or {}
    rader = ['# Svar %s · station %s · %s (%s)' % (b['id'], post.get('station') or b.get('station'), b['typ'], post.get('pass')), '',
             'Beställning: %s, version %s, ritning %s. Uppgift: %s' % (b['projekt'], b['version'], b['ritning'], b['uppgift']), '',
             'Utfört av: %s · session %s · %s–%s · utfall %s' % (b.get('utforare') or post.get('pass'), post.get('session_id'),
                                                                post.get('start'), post.get('slut'), post.get('utfall')), '',
             '## Sammanfattning', '', so.get('sammanfattning') or '(inget svar)', '', '## Fynd', '']
    rader += ['- **%s · %s** (allvar %s): %s — belägg: %s' % (f['plats'], f['tillstand'], f['allvar'], f['vad'], f['belagg'])
              for f in so.get('fynd') or []] or ['- inga']
    rader += ['', '## Förslag', '']
    rader += ['- %s — %s (källa: %s)%s' % (f['vad'], f['varfor'], f['kalla'], (' · värden: ' + f['varden']) if f.get('varden') else '')
              for f in so.get('forslag') or []] or ['- inga']
    rader += ['', '## Referenser', '']
    rader += ['- %s `%s`%s: %s → %s%s' % (r['kalla'], r['id'], (' ' + r['adress']) if r.get('adress') else '', r['visar'], r['anvandning'],
                                          (' · licens ' + r['licens']) if r.get('licens') else '') for r in so.get('referenser') or []] or ['- inga']
    if so.get('atergang'):
        rader += ['', '## Återgång', '', '- %s: %s' % ({'fortsatt': 'fortsätt bandet', 'underlag': 'omtag av underlaget (ny research eller nya förebilder)', 'innehall': 'omtag av innehåll och struktur',
                                                        'art': 'omtag av art direction', 'komposition': 'omtag av kompositionen',
                                                        'detaljer': 'omtag av detaljerna'}
                                                       .get(so['atergang'].get('till'), so['atergang'].get('till')), so['atergang'].get('skal'))]
    rader += ['', '## Begränsningar', ''] + (['- ' + x for x in so.get('begransningar') or []] or ['- inga redovisade'])
    rader += ['', '## Kompetens (kvittot ur transkriptet, inte passets egen uppgift)', '',
              '- Skill-aktiveringar: %s' % ', '.join(kv.get('skill_anrop') or []) if isinstance(kv, dict) else '- kvitto saknas',
              '- Inte observerat i transkriptet (information, fäller ingenting): %s' % ('; '.join(post.get('ej_observerat') or []) or 'inget'),
              '- Passets egen redovisning (märkt som sådan): aktiverade %s; lästa %s; valda %s' % (
                  ', '.join((so.get('kompetens') or {}).get('aktiverade') or []) or '–', ', '.join((so.get('kompetens') or {}).get('lasta') or []) or '–',
                  ', '.join((so.get('kompetens') or {}).get('valda') or []) or '–'), '']
    return '\n'.join(rader) + '\n'


def svar(slug, bid, fil, utforare, underlag=None):
    """Ett svar som gjorts utanför specialistpasset (en manuell överlämning): filen kopieras, och svaret märks så."""
    b = bestallning(slug, bid, underlag)
    p = Path(fil)
    if not p.is_file():
        raise Fel('svarsfilen saknas: %s' % fil)
    sk = rot(slug, underlag) / 'svar' / bid
    sk.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, sk / 'SVAR.md')
    skriv(sk / 'SVAR.json', {'schema': 1, 'id': bid, 'utfall': 'levererad', 'manuell': True, 'utforare': utforare[:300], 'tid': nu(),
                             'sha256': sha(sk / 'SVAR.md')})
    return uppdatera_bestallning(slug, bid, underlag, status='levererad', utforare=utforare[:300],
                                 resultat={'fil': rel(sk / 'SVAR.md'), 'manuell': True})


def infor(slug, bid, v, bedomning, underlag=None):
    b = bestallning(slug, bid, underlag)
    if v not in versioner(slug, underlag):
        raise Fel('versionen %s finns inte' % v)
    if len((bedomning or '').strip()) < 20:
        raise Fel('bedömningen behöver säga vad som ändrades synligt och om det blev bättre, med bilderna före och efter')
    return uppdatera_bestallning(slug, bid, underlag, status='inford', inford_i=v,
                                 bedomning={'text': bedomning.strip()[:3000], 'tid': nu(), 'fore': b['version'], 'efter': v,
                                            'av': 'utföraren (egen bedömning, märkt som sådan)'})


# ---- godkännande och överlämning ---------------------------------------------------------------------------------

def versionens_avtryck(slug, v, underlag=None):
    vk = rot(slug, underlag) / 'versioner' / v
    post = las(vk / 'VERSION.json') or {}
    bilder = {}
    for r, rp in ((las(vk / 'BILDER.json') or {}).get('ritningar') or {}).items():
        for k, x in (rp.get('bilder') or {}).items():
            p = vk / x['fil']
            bilder['%s@%s' % (r, k)] = sha(p) if p.is_file() else None
    filer = post.get('filer') or {}
    if post.get('lage') == 'astro':  # källan som den ligger på disken: en ändrad fil i kalla/ gör godkännandet ogiltigt
        filer = {n: sha(vk / 'kalla' / n) if (vk / 'kalla' / n).is_file() and not (vk / 'kalla' / n).is_symlink() else None for n in filer}
    return {'filer': filer, 'bilder': bilder}


def godkann(slug, v, ritning, text='', underlag=None):
    """ÄGARENS designgodkännande: en rad i domloggen (källa ägaren, beslut godkand) och GODKANNANDE.json bundna till
    versionens filer och bilder och till underlagets version. Sessionerna nekas kommandot (design.sh och projektets
    inställningar); ägaren kör det själv, i terminalen eller med !-prefixet i sin session. Startar inget bygge."""
    import skapande
    d = designfas(slug, underlag)
    if v not in versioner(slug, underlag):
        raise Fel('versionen %s finns inte' % v)
    vk = rot(slug, underlag) / 'versioner' / v
    post = las(vk / 'VERSION.json')
    astro = post.get('lage') == 'astro'
    if astro and ritning != post.get('ritning'):
        raise Fel('versionen %s gäller riktningen %s, inte %s' % (v, post.get('ritning'), ritning))
    if not astro and ritning not in [r['fil'] for r in post['ritningar']]:
        raise Fel('ritningen %s finns inte i %s' % (ritning, v))
    bild = (las(vk / 'BILDER.json') or {}).get('ritningar', {}).get(bildsida(post, ritning), {}).get('bilder') or {}
    saknas = [w for w in BREDDER if str(w) not in {str(k) for k in bild}]
    if saknas:
        raise Fel('%s saknar bilder i %s: kör designfas.py rendera %s %s först' % (
            'startsidan' if astro else 'ritningen', ', '.join(map(str, saknas)), slug, v))
    u = Path(underlag or UNDERLAG)
    tid = nu()
    text = text.strip() or ('Designen godkänd: %s, riktningen %s (%s).' % (v, ritning, (post.get('riktning') or {}).get('projekt')) if astro else
                            'Designen godkänd i Claude Design: %s, ritningen %s (artefaktversion %s).' % (v, ritning, post['artifact_version']))
    dom = skapande.lagg_till_dom(slug, 'ägaren', 'godkand', text, avser='designfas %s %s' % (v, ritning), underlag=u, tid=tid,
                                 belagg='ägarens eget kommando: designfas.py godkann %s %s --ritning %s, %s' % (slug, v, ritning, tid),
                                 designfas={'version': v, 'ritning': ritning, 'lage': post.get('lage') or 'duk', 'kanvas': kanvas_url(d),
                                            'artifact_version': post.get('artifact_version')})
    g = {'schema': 1, 'slug': slug, 'tid': tid, 'kalla': 'ägaren', 'version': v, 'ritning': ritning, 'lage': post.get('lage') or 'duk',
         'kanvas': kanvas_url(d), 'artifact_version': post.get('artifact_version'), 'avtryck': versionens_avtryck(slug, v, underlag),
         'underlag_sha': skapande.underlagsversion(slug, u), 'dom_tid': dom['tid'],
         'betyder': 'designen är godkänd; byggstart och publicering är egna beslut (kor.sh startar bygget, lanseringen publicerar)'}
    skriv(rot(slug, underlag) / 'GODKANNANDE.json', g)
    return g


def godkand_giltig(slug, underlag=None):
    """(giltig, skäl, godkännandet): ägarens designgodkännande gäller när domloggens senaste ägarbeslut är just det,
    versionens filer och bilder är oförändrade, underlaget är oförändrat och överlämningen är komplett och bunden."""
    import skapande
    u = Path(underlag or UNDERLAG)
    try:
        g = las(rot(slug, underlag) / 'GODKANNANDE.json')
    except Fel as e:
        return False, str(e), None
    if not isinstance(g, dict) or g.get('kalla') != 'ägaren':
        return False, 'inget designgodkännande från ägaren (design/GODKANNANDE.json)', None
    ag = skapande.agarens_senaste(slug, u)
    if ag['oklara']:
        return False, skapande.oklara_text(ag), g
    dom = ag['dom']
    if not dom or dom.get('beslut') != 'godkand' or dom.get('tid') != g.get('dom_tid'):
        return False, 'ägarens senaste dom i domloggen är inte designgodkännandet', g
    if versionens_avtryck(slug, g['version'], underlag) != g.get('avtryck'):
        return False, 'den godkända versionens filer eller bilder är ändrade sedan godkännandet', g
    try:
        if skapande.underlagsversion(slug, u) != g.get('underlag_sha'):
            return False, 'underlaget ändrades sedan godkännandet; en ny bedömning behövs', g
    except (OSError, ValueError):
        return False, 'underlaget kunde inte verifieras', g
    brister = overlamning_brister(slug, underlag)
    if brister:
        return False, 'överlämningen är inte komplett: ' + '; '.join(brister), g
    return True, 'designen godkänd %s (%s, %s)' % (g['tid'], g['version'], g['ritning']), g


def overlamning_katalog(slug, underlag=None):
    g = las(rot(slug, underlag) / 'GODKANNANDE.json') or {}
    return rot(slug, underlag) / 'overlamning' / str(g.get('version')), g


def overlamna(slug, underlag=None):
    """Paketet ur den godkända versionen: källan (kalla/, läget astro: projektets src/, public/, package.json och låset)
    eller ritningarna (kanvas/, läget duk), bilderna, kontrollerna, tillgångarna med ursprung och en DESIGN.md-mall med
    rubrikerna som utföraren fyller i ur versionen. Paketet skrivs inte över när det finns: det som utföraren skrivit står
    kvar, och bara de kopierade delarna och OVERLAMNING.json förnyas."""
    k, g = overlamning_katalog(slug, underlag)
    if not g:
        raise Fel('inget designgodkännande: ägaren godkänner en version först (designfas.py godkann)')
    vk = rot(slug, underlag) / 'versioner' / g['version']
    for n in ('kanvas', 'kalla', 'bilder', 'kontroll'):
        if (k / n).exists():
            shutil.rmtree(k / n)
        if (vk / n).is_dir():
            shutil.copytree(vk / n, k / n)
    for n in ('VERSION.json', 'BILDER.json'):
        shutil.copy2(vk / n, k / n)
    kanda = (las(rot(slug, underlag) / 'TILLGANGAR.json') or {}).get('blobs') or {}
    post = las(vk / 'VERSION.json')
    tillg = {b: kanda.get(b) for b in post.get('tillgangar') or []}
    dm = k / 'DESIGN.md'
    if not dm.is_file():
        dm.write_text('\n'.join(['# DESIGN · %s · %s (%s)' % (slug, g['version'], g['ritning']), '',
                                 'Fylls i av utföraren ur den godkända versionen (skillen designfas, Överlämningen). Varje värde är '
                                 '`uppmätt:` (ur renderingen), `valt:` (beslut i designen) eller `uppskattat:`; inget hittas på.' +
                                 (' Projektets egen DESIGN.md, den som bygget läser, står i kalla/DESIGN.md.' if (vk / 'kalla').is_dir() else ''), ''] +
                                sum((['## ' + r, '', '<!-- fyll i -->', ''] for r in OVERLAMNING_RUBRIKER), [])) + '\n', encoding='utf-8')
    skriv(k / 'OVERLAMNING.json', {'schema': 1, 'slug': slug, 'tid': nu(), 'godkannande': {x: g.get(x) for x in ('tid', 'version', 'ritning', 'lage', 'kanvas', 'artifact_version', 'dom_tid')},
                                    'tillgangar': tillg, 'filer': {str(p.relative_to(k)): sha(p) for p in sorted(k.rglob('*'))
                                                                   if p.is_file() and p.name != 'OVERLAMNING.json'}})
    return k


def overlamning_brister(slug, underlag=None):
    k, g = overlamning_katalog(slug, underlag)
    if not g:
        return ['inget designgodkännande']
    o = las(k / 'OVERLAMNING.json')
    if not o:
        return ['OVERLAMNING.json saknas: kör designfas.py overlamna %s' % slug]
    brister = []
    if (o.get('godkannande') or {}).get('dom_tid') != g.get('dom_tid'):
        brister.append('överlämningen gäller ett annat godkännande')
    text = (k / 'DESIGN.md').read_text(encoding='utf-8') if (k / 'DESIGN.md').is_file() else ''
    for r in OVERLAMNING_RUBRIKER:
        m = re.search(r'^## %s[ \t]*\n(.*?)(?=^## |\Z)' % re.escape(r), text, re.M | re.S)
        innehall = re.sub(r'<!--.*?-->', '', m.group(1), flags=re.S).strip() if m else ''
        if len(innehall) < 40:
            brister.append('DESIGN.md: avsnittet "%s" saknas eller är tomt' % r)
    for w in BREDDER:
        if not (k / 'bilder' / ('%s-%d.png' % (stam(bildsida(g, g['ritning'])), w))).is_file():
            brister.append('jämförelsebilden i %d saknas' % w)
    if g.get('lage') == 'astro':  # källan med paketen följer med till helbygget (punkt 5 i beslutet 2026-10-13)
        for n, varfor in (('package.json', 'paketen'), ('package-lock.json', 'låset, som npm ci installerar ur'), ('src/pages/index.astro', 'startsidan')):
            if not (k / 'kalla' / n).is_file():
                brister.append('kalla/%s saknas (%s)' % (n, varfor))
    for b, t in (o.get('tillgangar') or {}).items():
        if not t or not (t.get('kalla') or '').strip():
            brister.append('tillgången %s saknar ursprung (designfas.py tillgang --kalla)' % b)
    for n, s in (o.get('filer') or {}).items():
        p = k / n
        if n != 'DESIGN.md' and (not p.is_file() or sha(p) != s):
            brister.append('%s är ändrad sedan paketet skrevs' % n)
    return brister


def jamfor_bygget(slug, insp, ut, dist_sha=None, underlag=None):
    """Bygget mot den godkända förlagan ur designfasen, pixel för pixel (kontroller/webblasare/jamfor.mjs): förlagans
    helsida i 390, 768 och 1440 mot byggets vy-<bredd>-hela.png, och menyn öppen i 390 mot vy-390-meny.png. Mäter
    förändring, inte kvalitet; ett par som inte kunde jämföras visar inte att designen är bevarad. Resultatet binds till
    godkännandet (version, ritning, domens tid) och till bygget (dist). Skriver ut/DESIGNJAMFORELSE.json och .md."""
    ok, skal, g = godkand_giltig(slug, underlag)
    insp, ut = Path(insp), Path(ut)
    ut.mkdir(parents=True, exist_ok=True)
    par = []
    if g:
        k = rot(slug, underlag) / 'overlamning' / g['version'] / 'bilder'
        s = stam(bildsida(g, g['ritning']))
        for vy, slag, a_, b_ in [(str(w), 'helsidan', '%s-%d.png' % (s, w), 'vy-%d-hela.png' % w) for w in BREDDER] + \
                                [('390', 'menyn öppen', '%s-390-meny.png' % s, 'vy-390-meny.png')]:
            fa, fb = k / a_, insp / b_
            post = {'vy': vy, 'slag': slag, 'forlaga': rel(fa), 'bygget': rel(fb)}
            saknas = [x for x, q in (('förlagans bild', fa), ('byggets bild', fb)) if not q.is_file()]
            if saknas:
                post['fel'] = 'saknas: ' + ' och '.join(saknas)
            else:
                r = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'jamfor.mjs'), '--a', str(fa), '--b', str(fb),
                                    '--ut', str(ut / ('skillnad-%s' % b_))], capture_output=True, text=True, timeout=120)
                rad = next((x for x in reversed((r.stdout or '').strip().splitlines()) if x.startswith('{')), '')
                try:
                    res = json.loads(rad) if rad else {'fel': 'inget svar'}
                    if r.returncode != 0 or 'fel' in res:
                        raise ValueError(res.get('fel') or 'rc %d' % r.returncode)
                    post.update(res)
                except ValueError as e:
                    post['fel'] = 'jämförelsen kördes inte: %s' % e
            par.append(post)
    d = {'tid': nu(), 'giltigt_godkannande': ok, 'skal': skal, 'bindning': {k_: (g or {}).get(k_) for k_ in ('version', 'ritning', 'dom_tid', 'artifact_version')},
         'dist_sha256': dist_sha, 'par': par, 'jamforda': sum(1 for x in par if not x.get('fel'))}
    skriv(ut / 'DESIGNJAMFORELSE.json', d)
    rader = ['# Bygget mot förlagan ur designfasen', '',
             'Pixeljämförelse (kontroller/webblasare/jamfor.mjs) av den godkända ritningens bilder mot byggets startsida i samma',
             'bredder och med menyn öppen. Måttet är förändring, inte kvalitet; granskaren avgör med båda bildserierna om en',
             'förändring är en försämring, en godkänd anpassning eller en förbättring. Ett par som inte kunde jämföras visar inte',
             'att designen är bevarad.', '',
             'Förlagan: %s, ritningen %s, godkänd %s (giltigt: %s). Bygget: dist %s.' % (
                 (g or {}).get('version') or '–', (g or {}).get('ritning') or '–', (g or {}).get('dom_tid') or 'nej', 'ja' if ok else 'nej, ' + skal,
                 (dist_sha or '–')[:12]), '']
    rader += ['- %s %s: %s' % (x['vy'], x['slag'], x['fel'] if x.get('fel') else '%.1f %% olika pixlar över gemensam yta' % (100 * (x.get('andel') or 0)))
              for x in par] or ['- inget jämfört: inget designgodkännande']
    (ut / 'DESIGNJAMFORELSE.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return '%d av %d par jämförda mot förlagan%s (prov/designforlaga/DESIGNJAMFORELSE.md)' % (
        d['jamforda'], len(par), '' if ok else '; godkännandet gäller inte: ' + skal)


# ---- ägarens visning: en privat artefakt per riktning (beslutet 2026-10-13, punkt 2) --------------------------------

ASTRO_VAG = re.compile(r'(["\'(]|, )/_astro/')  # "/_astro/, '/_astro/, url(/_astro/ och srcset-ledet , /_astro/
CSP_META = re.compile(r'<meta\b[^>]*http-equiv\s*=\s*["\']?content-security-policy["\']?[^>]*>', re.I)
ROTVAG = re.compile(r'(?:src|srcset|poster)\s*=\s*["\']/(?!_astro/|/)', re.I)


def relativa_vagar(text, djup=0):
    """Astros absoluta /_astro/-vägar relativa till en fil djup kataloger under versionens katalog (sidan 0, _astro/x.css 1)."""
    return ASTRO_VAG.sub(lambda m: m.group(1) + '../' * djup + '_astro/', text)


def artefakt_post(slug, rid, underlag=None):
    """Riktningens publicerade artefakt (design/riktningar/<riktning>/ARTEFAKT.json), eller {}."""
    try:
        return las(rot(slug, underlag) / 'riktningar' / rid / 'ARTEFAKT.json') or {}
    except Fel:
        return {}


def artefakt(slug, rid, underlag=None):
    """Paketet för ägarens visning av en riktning: en privat artefakt per riktning, som sessionen publicerar med
    Artifact-verktyget (inget kommando når det; skillen designfas säger när och hur) och uppdaterar efter varje sparad
    version. I underlag/<slug>/design/artefakt/<riktning>/: index.html är visningssidan (artefakten lindar in den i ett eget
    skelett, så den har ingen egen <html> eller <head>), och vNN/ per version har den byggda startsidan och _astro/, med
    Astros absoluta /_astro/-vägar relativa och sidans CSP-meta borttagen (hasharna stämmer inte efter omskrivningen;
    sajtens CSP prövas i den lokala renderingen). Andra HTML-filer serveras som de är. FILER.json listar {path} för
    verktygets files, med root = katalogen; över 255 filer delas listan i FILER-1.json, FILER-2.json … för flera
    publiceringar till samma adress. Artefaktens CSP släpper bara egna filer: en extern bild syns inte där."""
    d = designfas(slug, underlag)
    if lage(slug, underlag) != 'astro':
        raise Fel('artefakten visar riktningarna i läget astro; designfasen för %s är i läget %s' % (slug, lage(slug, underlag)))
    if rid not in (d.get('riktningar') or {}):
        raise Fel('riktningen %s finns inte i bandet (riktningarna: %s)' % (rid, ', '.join(d.get('riktningar') or {}) or 'inga'))
    vs = []
    for v in versioner(slug, underlag):
        vk = rot(slug, underlag) / 'versioner' / v
        post = las(vk / 'VERSION.json') or {}
        if post.get('lage') == 'astro' and post.get('ritning') == rid and (vk / 'sida' / 'index.html').is_file():
            vs.append((v, post))
    if not vs:
        raise Fel('riktningen %s har ingen sparad version än: designfas.py version %s --ritning %s först' % (rid, slug, rid))
    ut = rot(slug, underlag) / 'artefakt' / rid
    if ut.is_symlink():
        raise Fel('%s är en länk; paketet skrivs inte' % rel(ut))
    if ut.exists():
        shutil.rmtree(ut)
    filer, varningar = [], []
    for v, post in vs:
        sida, mal = rot(slug, underlag) / 'versioner' / v / 'sida', ut / v
        mal.mkdir(parents=True)
        text = CSP_META.sub('', relativa_vagar((sida / 'index.html').read_text(encoding='utf-8', errors='replace'), 0))
        (mal / 'index.html').write_text(text, encoding='utf-8')
        filer.append('%s/index.html' % v)
        if ROTVAG.search(text):
            varningar.append('%s: startsidan laddar filer utanför _astro/ (public/), som förhandsvisningen inte har' % v)
        a_ = sida / '_astro'
        for f in sorted(a_.rglob('*')) if a_.is_dir() and not a_.is_symlink() else []:
            r = f.relative_to(sida)
            if f.is_symlink() or not f.is_file() or any((sida / Path(*r.parts[:i])).is_symlink() for i in range(1, len(r.parts))):
                continue
            m = mal / r
            m.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix == '.css':
                m.write_text(relativa_vagar(f.read_text(encoding='utf-8', errors='replace'), len(r.parts) - 1), encoding='utf-8')
            else:
                shutil.copyfile(f, m)
                if f.suffix in ('.js', '.mjs') and '/_astro/' in f.read_text(encoding='utf-8', errors='replace'):
                    varningar.append('%s: skriptet %s har absoluta /_astro/-vägar, som förhandsvisningen inte når' % (v, r.as_posix()))
            if m.stat().st_size > ARTEFAKT_BYTE:
                varningar.append('%s: %s är större än 15 MB, som en artefakt inte tar' % (v, r.as_posix()))
            filer.append(m.relative_to(ut).as_posix())
    (ut / 'index.html').write_text(visningssida(slug, rid, d, vs, underlag), encoding='utf-8')
    (ut / 'FILER.json').write_text(json.dumps([{'path': f} for f in filer], ensure_ascii=False) + '\n', encoding='utf-8')
    omgangar = [rel(ut / 'FILER.json')]
    if len(filer) > ARTEFAKT_FILER:
        omgangar = []
        for i in range(0, len(filer), ARTEFAKT_FILER):
            f_ = ut / ('FILER-%d.json' % (i // ARTEFAKT_FILER + 1))
            f_.write_text(json.dumps([{'path': f} for f in filer[i:i + ARTEFAKT_FILER]], ensure_ascii=False) + '\n', encoding='utf-8')
            omgangar.append(rel(f_))
    if len(filer) + 1 > 511:
        varningar.append('%d filer: en artefaktversion rymmer högst 511; visa färre versioner (äldre versioner står kvar i spåret)' % (len(filer) + 1))
    return {'riktning': rid, 'katalog': rel(ut), 'sida': rel(ut / 'index.html'), 'root': rel(ut), 'filer': len(filer),
            'omgangar': omgangar, 'versioner': [v for v, _ in vs], 'url': artefakt_post(slug, rid, underlag).get('url'),
            'varningar': varningar}


VISNING = """<title>__TITEL__</title>
<style>
/* Visningen av en riktning: versionerna i en rad, den valda versionens byggda sida i en ram med tre bredder */
:root {
  --bg: #f4f4f1; --yta: #ffffff; --fg: #1e1e1c; --dim: #5b5853; --linje: #d9dad6; --accent: #1f5fbf;
  --text: system-ui, -apple-system, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161615; --yta: #1f1f1d; --fg: #eeede8; --dim: #b0ada6; --linje: #3a3a37; --accent: #8db4f0; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #161615; --yta: #1f1f1d; --fg: #eeede8; --dim: #b0ada6; --linje: #3a3a37; --accent: #8db4f0; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.5 var(--text); margin: 0; padding: 16px 16px 32px; }
.huvud, .versioner, .bredder, .ram, .orsak { max-width: 1480px; margin-inline: auto; }
.huvud { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: baseline; justify-content: space-between; }
h1 { font-size: 20px; margin: 0; text-wrap: balance; }
.not, .orsak { color: var(--dim); margin: 4px auto 0; max-width: 70ch; }
.orsak { max-width: 1480px; margin-block: 0 12px; }
.versioner { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; margin-block: 12px; }
.versioner a { display: inline-flex; align-items: center; padding: 8px 12px; min-height: 44px; box-sizing: border-box; border: 1px solid var(--linje);
  border-radius: 6px; color: var(--fg); text-decoration: none; background: var(--yta); }
.versioner a[aria-current="page"] { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
.versioner a:focus-visible, .bredder button:focus-visible, .oppna:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.bredder { display: flex; flex-wrap: wrap; gap: 8px; margin-block: 0 12px; }
.bredder button { font: inherit; padding: 8px 12px; min-height: 44px; border: 1px solid var(--linje); border-radius: 6px; background: var(--yta);
  color: var(--fg); cursor: pointer; }
.bredder button[aria-pressed="true"] { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
.ram { overflow-x: auto; }
iframe { display: block; border: 1px solid var(--linje); background: #fff; height: 80vh; width: 100%; max-width: 100%; margin: 0 auto; }
.oppna { color: var(--fg); min-height: 44px; display: inline-flex; align-items: center; }
</style>

<div class="huvud">
  <div>
    <h1>__RUBRIK__</h1>
    <p class="not">Den byggda Astro-sidan i varje version av riktningen, privat. Kommentera med artefaktens kommentarer och nämn versionen. Externa bilder visas inte här (artefaktens skydd); sajtens eget skydd prövas i den lokala renderingen.</p>
  </div>
  <a class="oppna" id="oppna" href="__SENASTE__/index.html">Öppna versionen som hel sida</a>
</div>
<ul class="versioner" id="versioner">
__VERSIONER__
</ul>
<p class="orsak" id="orsak"></p>
<div class="bredder" role="group" aria-label="Bredd">
  <button type="button" data-w="390" aria-pressed="false">390</button>
  <button type="button" data-w="768" aria-pressed="false">768</button>
  <button type="button" data-w="1440" aria-pressed="true">1440</button>
</div>
<div class="ram"><iframe id="sida" title="__RUBRIK__, __SENASTE__" src="__SENASTE__/index.html"></iframe></div>

<script>
  const ram = document.getElementById('sida');
  for (const b of document.querySelectorAll('.bredder button')) {
    b.addEventListener('click', () => {
      for (const x of document.querySelectorAll('.bredder button')) x.setAttribute('aria-pressed', String(x === b));
      ram.style.width = b.dataset.w === '1440' ? '100%' : b.dataset.w + 'px';
    });
  }
  const valj = (v) => {
    let funnen = null;
    for (const a of document.querySelectorAll('#versioner a')) {
      if (a.dataset.v === v) { a.setAttribute('aria-current', 'page'); funnen = a; } else a.removeAttribute('aria-current');
    }
    if (!funnen) return;
    ram.src = v + '/index.html';
    ram.title = funnen.textContent;
    document.getElementById('oppna').href = v + '/index.html';
    document.getElementById('orsak').textContent = funnen.dataset.orsak || '';
  };
  const h = (location.hash || '').slice(1);
  valj(/^v\\d{2,3}$/.test(h) ? h : '__SENASTE__');
  for (const a of document.querySelectorAll('#versioner a')) a.addEventListener('click', () => valj(a.dataset.v));
</script>
"""


def visningssida(slug, rid, d, vs, underlag=None):
    """Visningssidan: titel, färgtokens för ljust och mörkt, en rad med versionerna (station och orsak), en ram med
    bredderna 390, 768 och 1440 och en länk till hela sidan; den nyaste versionen är vald."""
    import html as h
    namn = (las(Path(underlag or UNDERLAG) / slug / 'VERKSAMHET.json') or {}).get('namn') or slug
    titel = ((d.get('riktningar') or {}).get(rid) or {}).get('titel')
    st = stationer()
    rader = []
    for v, post in vs:
        sid = post.get('station')
        etikett = '%s · %s' % (v, st[sid]['namn'] if sid in st else (sid or 'utan station'))
        rader.append('  <li><a href="#%s" data-v="%s" data-orsak="%s">%s</a></li>' % (
            v, v, h.escape('%s: %s' % (v, post.get('orsak') or ''), quote=True), h.escape(etikett)))
    rubrik = '%s · riktning %s%s' % (namn, rid, (' · %s' % titel) if titel else '')
    return (VISNING.replace('__TITEL__', h.escape('%s %s' % (namn, rid))).replace('__RUBRIK__', h.escape(rubrik))
            .replace('__VERSIONER__', '\n'.join(rader)).replace('__SENASTE__', vs[-1][0]))


def registrera_artefakt(slug, rid, url, v, artifact_version=None, underlag=None):
    """Publiceringen av riktningens artefakt (sessionen gjorde den med Artifact-verktyget): adressen och den version som
    visas i ARTEFAKT.json i riktningens spår. Samma artefakt per riktning: en annan adress nekas."""
    if not KANVAS.match(url or ''):
        raise Fel('adressen ska vara en claude.ai-artefakt (https://claude.ai/artifact/<id>): %r' % url)
    if artifact_version and not re.fullmatch(r'[0-9A-Za-z._-]{1,64}', artifact_version):
        raise Fel('ogiltig artefaktversion: %r' % artifact_version)
    post = las(rot(slug, underlag) / 'versioner' / str(v) / 'VERSION.json') if VERSION.match(str(v or '')) else None
    if not post or post.get('ritning') != rid:
        raise Fel('versionen %s finns inte eller gäller inte riktningen %s' % (v, rid))
    f = rot(slug, underlag) / 'riktningar' / rid / 'ARTEFAKT.json'
    gammal = las(f) or {}
    if gammal.get('url') not in (None, url):
        raise Fel('riktningen %s har redan artefakten %s: samma artefakt uppdateras för varje version; en ny adress är ett nytt '
                  'beslut (flytta ARTEFAKT.json till historik först)' % (rid, gammal['url']))
    tid = nu()
    ny_ = {'schema': 1, 'riktning': rid, 'url': url, 'version': v, 'artifact_version': artifact_version, 'tid': tid,
           'synlighet': 'privat: publicerad av sessionen med Artifact-verktyget; ingen offentlig publicering av kundmaterial',
           'historik': ((gammal.get('historik') or []) + [{'version': v, 'tid': tid, 'artifact_version': artifact_version}])[-100:]}
    skriv(f, ny_)
    return ny_


def sajtens_npmrc(sajt):
    """Sajtens .npmrc låser helbyggets installation (beslutet 2026-10-13, punkt 5): inga paketskript, exakta versioner
    och bara npm-registret. Andra rader står kvar. Ger True när filen skrevs."""
    f = Path(sajt) / '.npmrc'
    if f.is_symlink():
        f.unlink()
    gammal = f.read_text(encoding='utf-8') if f.is_file() else ''
    behall = [r for r in gammal.splitlines() if r.strip() and r.split('=', 1)[0].strip() not in NPMRC_SAJT]
    ny_ = '\n'.join(behall + ['%s=%s' % kv for kv in NPMRC_SAJT.items()]) + '\n'
    if ny_ == gammal:
        return False
    f.write_text(ny_, encoding='utf-8')
    return True


def installera_godkand(slug, underlag=None):
    """Före ett bygge från ägarens designgodkännande i läget astro (kor.sh): den godkända versionens källa (kalla/: src/,
    public/, package.json, låset, astro.config.mjs, DESIGN.md och RIKTNING.md) läggs i kunder/<slug>/sajt med samma
    prövning som en godkänd kandidat (atelje.prova_overforing och overfor_godkanda: allt prövas mot versionens hashar
    innan något ersätts, och det ersatta flyttas till kunder/<slug>/startsida-ersatt/). Paketen följer med i package.json
    och låset, och sajtens .npmrc låser installationen (sajtens_npmrc). Läget duk installerar inget här: bygget
    implementerar förlagan. Ger vägarna som ersattes eller skrevs."""
    import atelje
    ok, skal, g = godkand_giltig(slug, underlag)
    if not ok:
        raise Fel('inget giltigt designgodkännande: %s' % skal)
    if g.get('lage') != 'astro':
        return []
    vk = rot(slug, underlag) / 'versioner' / g['version']
    kalla = vk / 'kalla'
    sajt = atelje.KUNDER / slug / 'sajt'
    filer = (las(vk / 'VERSION.json') or {}).get('filer') or {}
    par = [(kalla / n, sajt / n, s) for n, s in sorted(filer.items()) if n != '.npmrc']  # .npmrc skrivs av sajtens_npmrc
    try:
        atelje.saker_vag(sajt, atelje.KUNDER / slug)
        atelje.prova_overforing(slug, par, kalla, 'den godkända versionen')
        ersatta = atelje.overfor_godkanda(slug, par, kalla, 'underlag/%s/design/versioner/%s/kalla' % (slug, g['version']))
    except RuntimeError as e:
        raise Fel(str(e))
    if sajtens_npmrc(sajt):
        ersatta.append(rel(sajt / '.npmrc'))
    return ersatta


# ---- status, kvitto, karta och start --------------------------------------------------------------------------------

def band(slug, underlag=None):
    """Bandets läge per riktning: varje station i ordning som gjord (version, synlig ändring, tid), svar (beställning),
    hoppad (skäl), ej tillämplig (formulär utan formulär, jämförelse med en riktning, överlämning före godkännandet) eller
    återstår (ägarens uppdrag 2026-10-12 ~17:35Z, punkt 5). Läget astro: riktningarna ur DESIGNFAS.json, och sist raden
    artefakt med adressen till riktningens privata artefakt när den är publicerad. Läget duk: ritningarna i senaste
    versionen."""
    r = rot(slug, underlag)
    vs = [las(r / 'versioner' / v / 'VERSION.json') or {'version': v} for v in versioner(slug, underlag)]
    astro = lage(slug, underlag) == 'astro'
    if not vs and not astro:
        return {}
    bs = [bestallning(slug, b, underlag) for b in bestallningar(slug, underlag)]
    godkand = (las(r / 'GODKANNANDE.json') or {}).get('version')
    if astro:
        ritningar = list(designfas(slug, underlag).get('riktningar') or {})
    else:
        ritningar = [x['fil'] for x in vs[-1].get('ritningar') or []]
        bild_duk = (las(r / 'versioner' / vs[-1]['version'] / 'BILDER.json') or {}).get('ritningar') or {}
    ut = {}
    for rit in ritningar:
        if astro:  # formulären på riktningens senaste version, alla dess sidor
            egna = [x for x in vs if x.get('ritning') == rit]
            bilder_ = ((las(r / 'versioner' / egna[-1]['version'] / 'BILDER.json') or {}).get('ritningar') or {}) if egna else {}
            formular = any((b_ or {}).get('formular') for rp in bilder_.values() for b_ in ((rp or {}).get('bilder') or {}).values())
        else:
            formular = any((x or {}).get('formular') for x in ((bild_duk.get(rit) or {}).get('bilder') or {}).values())
        rad = []
        for sid in stationer():
            post = {'station': sid}
            gjorda = [x for x in vs if x.get('station') == sid and x.get('ritning') == rit]
            svar_ = [b for b in bs if b.get('station') == sid and b.get('ritning') in (rit, '*') and b.get('status') in ('levererad', 'inford')]
            hopp = [x for x in vs if sid in (x.get('hoppade') or {}) and x.get('ritning') == rit]
            if gjorda:
                g = gjorda[-1]
                post.update(lage='gjord', version=g['version'], synlig=(g.get('insats') or {}).get('synlig'),
                            sekunder=g.get('sekunder_sedan_forra'), notering=bool(g.get('notering')))
            elif svar_:
                post.update(lage='svar', bestallning=svar_[-1]['id'], inford_i=svar_[-1].get('inford_i'))
                ag = ((las(r / 'svar' / svar_[-1]['id'] / 'SVAR.json') or {}).get('svar') or {}).get('atergang')
                if ag:
                    post['atergang'] = ag
            elif hopp:
                post.update(lage='hoppad', skal=hopp[-1]['hoppade'][sid], version=hopp[-1]['version'])
            elif sid == 'formular' and not formular:
                post.update(lage='ej tillämplig', skal='riktningen har inget formulär' if astro else 'ritningen har inget formulär')
            elif sid == 'jamforelse' and len(ritningar) < 2:
                post.update(lage='ej tillämplig', skal='bara en riktning i bandet' if astro else 'bara en riktning på duken')
            elif sid == 'overlamning' and not godkand:
                post.update(lage='väntar', skal='efter ägarens godkännande')
            else:
                post['lage'] = 'återstår'
            rad.append(post)
        if astro:
            a_ = artefakt_post(slug, rit, underlag)
            rad.append({'station': 'artefakt', 'lage': 'publicerad' if a_.get('url') else 'inte publicerad', 'url': a_.get('url'),
                        'version': a_.get('version'), 'tid': a_.get('tid')})
        ut[rit] = rad
    return ut


def status(slug, underlag=None):
    d = designfas(slug, underlag)
    r = rot(slug, underlag)
    vs = [las(r / 'versioner' / v / 'VERSION.json') or {'version': v} for v in versioner(slug, underlag)]
    ok, skal, g = godkand_giltig(slug, underlag)
    astro = lage(slug, underlag) == 'astro'
    return {'designfas': d, 'lage': lage(slug, underlag), 'nasta_version': nasta(slug, underlag),
            'riktningar': {rid: dict(x, artefakt=artefakt_post(slug, rid, underlag).get('url'),
                                     senaste=(senaste_per_riktning(slug, underlag).get(rid)))
                           for rid, x in (d.get('riktningar') or {}).items()} if astro else None,
            'versioner': [{k: x.get(k) for k in ('version', 'tid', 'artifact_version', 'av', 'station', 'ritning', 'orsak', 'bestallningar', 'hoppade')}
                          for x in vs],
            'bestallningar': [{k: bestallning(slug, b, underlag).get(k) for k in ('id', 'station', 'typ', 'version', 'status', 'inford_i')}
                              for b in bestallningar(slug, underlag)],
            'band': band(slug, underlag),
            'godkannande': {'giltigt': ok, 'skal': skal, 'version': (g or {}).get('version')}}


# Detektorns område per station (renderingens fält omrade ur motorns --scope; valideringen 2026-10-12, skills del 1
# åtgärd 4): typografi läser typfynden, komposition och responsiv layoutfynden, detaljer, kritiken och polish alla
DETEKTOR_OMRADE = {'typografi': ('typografi',), 'komposition': ('layout',), 'responsiv': ('layout',), 'detaljer': None, 'kritik': None,
                   'polish': None}


def detektor_rader(vk, ritning, sid):
    """Detektorns fynd för stationens område ur versionens kontroll (renderingen med --kontroll), som regel, allvar och
    bredd utan kodutdrag; tom lista när stationen inte läser detektorn eller fynden saknas."""
    if sid not in DETEKTOR_OMRADE:
        return []
    omr = DETEKTOR_OMRADE[sid]
    fynd = {}
    for w in ('390', '1440'):
        for f in las(vk / 'kontroll' / 'detektor' / ('%s-%s.json' % (ritning.replace('/', '-'), w))) or []:
            if isinstance(f, dict) and f.get('antipattern') and (omr is None or f.get('omrade') in omr):
                x = fynd.setdefault(f['antipattern'], {'namn': f.get('name') or f['antipattern'], 'allvar': f.get('severity'),
                                                        'bredder': [], 'rad': f.get('advisory')})
                x['bredder'].append(w)
    if not fynd:
        return []
    return ['Impeccables detektorns fynd för stationen (%s; kontroll/detektor/ i versionen, regelkatalogens fält): %s. Pröva varje'
            ' fynd mot bilderna och ägarbesluten; ett fynd rättas eller motiveras med namngivet belägg i versionens orsak.' % (
                'området ' + ' och '.join(omr) if omr else 'alla områden',
                '; '.join('%s (%s, %s%s, %s)' % (k, x['namn'], x['allvar'] or 'okänt allvar', ', råd' if x['rad'] else '',
                                                 '/'.join(x['bredder'])) for k, x in sorted(fynd.items())))]


def station_brief(slug, sid, ritning, underlag=None):
    """Arbetsinstruktionen för en station på en riktning: frågan och skills ur metodkartans tabell, riktningens senaste
    version (bilder, mätningar, detektorns fynd) eller, före riktningens första version, projektet och indata, och hur
    insatsen sparas. Till utföraren eller till den underagent som gör stationen."""
    st = station(sid)
    if lage(slug, underlag) == 'duk':
        return _station_brief_duk(slug, st, ritning, underlag)
    p = projekt(slug, ritning, underlag)
    titel = ((designfas(slug, underlag).get('riktningar') or {}).get(ritning) or {}).get('titel')
    v = senaste_per_riktning(slug, underlag).get(ritning)
    vk = rot(slug, underlag) / 'versioner' / v if v else None
    bild = (((las(vk / 'BILDER.json') or {}).get('ritningar') or {}) if vk else {})
    a_ = artefakt_post(slug, ritning, underlag)
    return '\n'.join([
        'Station %s på riktningen %s%s, %s (%s blir nästa version).' % (
            st['id'], ritning, (' (%s)' % titel) if titel else '', ('senaste version %s' % v) if v else 'riktningens första version',
            nasta(slug, underlag)),
        *station_rader(st),
        'Indata: ' + st['indata'] + '.',
        'Projektet: %s (src/, public/ och RIKTNING.md med referenslåset, språket och skälen; package.json med paketen). Arbeta '
        'bara i det projektet. Riktningens uppdrag ur planen: underlag/%s/atelje/kandidater/%s/UPPDRAG.md.' % (rel(p), slug, ritning),
        *(['Bilderna i %s: ' % v + '; '.join('%s: %s' % (s_, ', '.join('%s %s' % (k, rel(vk / x['fil'])) for k, x in (rp.get('bilder') or {}).items()))
                                            for s_, rp in bild.items()),
           'Mätningar och varningar: %s; kontrollerna (axe, stilrapporten, detektorn): %s/' % (rel(vk / 'BILDER.json'), rel(vk / 'kontroll'))]
          if v else ['Riktningen har ingen version än: stationens insats blir dess första, med bilder och kontroller.']),
        *(detektor_rader(vk, 'index.html', st['id']) if v else []),
        'Underlaget: underlag/%s/KUNDFORSTAELSE.md och kunskap/designregler.md.' % slug,
        'Insatsen: ändra bara det stationen gäller i projektet och lämna resten orört. Spara den som '
        '`designfas.py version %s --station %s --ritning %s --orsak "<vad stationen ändrade och varför>"` (ett nytt paket: '
        '`--paket namn@version`); versionen byggs, renderas med kontrollerna och jämförs med förra versionen av riktningen. '
        'Hoppas stationen över: `--hoppa %s="<skäl>"` på nästa version.' % (slug, st['id'], ritning, st['id']),
        'Visningen för ägaren efter versionen: `designfas.py artefakt %s %s` och riktningens privata artefakt (%s).' % (
            slug, ritning, a_.get('url') or 'inte publicerad än')])


def _station_brief_duk(slug, st, ritning, underlag=None):
    vs = versioner(slug, underlag)
    if not vs:
        raise Fel('ingen version än: stationen gäller en sparad version')
    v = vs[-1]
    vk = rot(slug, underlag) / 'versioner' / v
    bild = ((las(vk / 'BILDER.json') or {}).get('ritningar') or {}).get(ritning)
    if not bild:
        raise Fel('ritningen %s finns inte i %s' % (ritning, v))
    return '\n'.join([
        'Station %s på %s, version %s (%s).' % (st['id'], ritning, v, nasta(slug, underlag) + ' blir nästa'),
        *station_rader(st),
        'Indata: ' + st['indata'] + '.',
        'Ritningens källa: %s' % rel(vk / 'kanvas' / ritning),
        'Bilderna: ' + ', '.join('%s %s' % (k, rel(vk / x['fil'])) for k, x in (bild.get('bilder') or {}).items()),
        'Mätningar och varningar: %s (ritningen %s)' % (rel(vk / 'BILDER.json'), ritning),
        *detektor_rader(vk, ritning, st['id']),
        'Underlaget: underlag/%s/KUNDFORSTAELSE.md och kunskap/designregler.md.' % slug,
        'Insatsen: ändra bara det stationen gäller och lämna resten orört. Efter publiceringen sparas den som '
        '`designfas.py version %s --station %s --ritning %s --fran <återläst katalog> --artifact-version <id> --orsak "<vad stationen '
        'ändrade och varför>"`, med dukens anteckning "%s · %s: <vad som ändrades>" (id %s). Hoppas stationen över: `--hoppa %s="<skäl>"` '
        'på nästa version.' % (slug, st['id'], ritning, nasta(slug, underlag), st['namn'], nasta(slug, underlag), st['id'])])


def kvitto(sid, pass_='skapa', station_=None):
    """Utförarens eller ett pass kvitto ur transkriptet: mot stationens skills när station anges, annars mot rollernas block
    i passet. Redovisning, inte en grind."""
    import kompetens
    if station_:
        kv, ej = kvitto_station([{'session_id': sid}], pass_, station(station_))
    else:
        kv = kompetens.kvitto([{'session_id': sid}], pass_)
        ej = kompetens.kravbrister(kv, pass_)
    return {'pass': pass_, 'station': station_, 'kvitto': kv, 'ej_observerat': ej}


KARTBLOCK = re.compile(r'^```designfas-karta[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)


def karta_prova(text=None):
    """Kompetensplaceringen i metodkartan (blocket designfas-karta: en rad per skill, tjänst och lokalt verktyg) mot
    verktygslådan: varje skillmapp och varje tjänst har en rad, och raden säger plats, steg och status."""
    import kompetens
    text = KARTA.read_text(encoding='utf-8') if text is None else text
    m = KARTBLOCK.search(text)
    if not m:
        return ['metodkartan saknar blocket designfas-karta']
    rader, fel = {}, []
    for rad in m.group('rader').splitlines():
        if not rad.strip():
            continue
        delar = [x.strip() for x in rad.split(' | ')]
        if len(delar) != 5 or not delar[0]:
            fel.append('raden har inte formen namn | källa | plats | steg och uppgift | status: %s' % rad[:80])
            continue
        if delar[2] not in ('Design', 'Code', 'båda', 'ingen'):
            fel.append('%s: platsen ska vara Design, Code, båda eller ingen' % delar[0])
        if not delar[1] or len(delar[3]) < 20 or len(delar[4]) < 6:
            fel.append('%s: källan, steget och uppgiften eller statusen saknas' % delar[0])
        rader[delar[0]] = delar
    for s in sorted(p.name for p in SKILLS.iterdir() if p.is_dir() and (p / 'SKILL.md').is_file()):
        if 'skill:' + s not in rader:
            fel.append('skillen %s saknar rad i designfas-karta' % s)
    for t in sorted(set(kompetens.MCP) | {'chrome-devtools'}):
        if 'mcp:' + t not in rader:
            fel.append('tjänsten %s saknar rad i designfas-karta' % t)
    for p_ in sorted(x for x in rader if x.startswith('pass:')):
        if p_[5:] not in kompetens.PASS:
            fel.append('%s är inget känt pass' % p_)
    for t, (p_, _, _) in TYPER.items():
        if 'pass:' + p_ not in rader:
            fel.append('specialistpasset %s (typen %s) saknar rad i designfas-karta' % (p_, t))
    # bandet: varje skill har en station eller ett skrivet skäl, och raden och tabellen säger samma sak
    import metod
    try:
        st = stationer(text)
    except Fel as e:
        return fel + [str(e)]
    if not st:
        return fel + ['metodkartan saknar bandets tabell (Bandet: stationerna)']
    per = {}
    for sid, x in st.items():
        for f in x['karna'] + x['alternativ']:
            try:
                metod.utdrag(f)
            except metod.MetodFel as e:
                fel.append('stationen %s: %s' % (sid, e))
            if not f.startswith(('kunskap/', 'kritik/')):
                per.setdefault('skill:' + f.split('/')[0], set()).add(sid)
        for m_ in x['mcp']:
            if m_ not in set(kompetens.MCP) | {'chrome-devtools'}:
                fel.append('stationen %s: okänd tjänst %s' % (sid, m_))
            per.setdefault('mcp:' + m_, set()).add(sid)
        for p_ in x['pass']:
            if p_ not in kompetens.DESIGNSTOD:
                fel.append('stationen %s: okänt pass %s' % (sid, p_))
            per.setdefault('pass:' + p_, set()).add(sid)
        if not x['karna']:
            fel.append('stationen %s saknar kärna' % sid)
    met = metoder(text)
    for sid, x in st.items():  # varje station har sin källa i metodtabellen, och varje metod har en station (bandet v2, punkt 1)
        if not x['metoder']:
            fel.append('stationen %s saknar metod i metodtabellen' % sid)
        fel += ['stationen %s: metoden %s finns inte i metodtabellen' % (sid, m_) for m_ in x['metoder'] if m_ not in met]
    anvanda = {m_ for x in st.values() for m_ in x['metoder']}
    fel += ['metoden %s har ingen station i bandet' % m_ for m_ in met if m_ not in anvanda]
    harl = harledda_floden(text)
    for namn, delar in rader.items():
        angivna_f = floden_i(delar[3])
        fel += ['%s: okänt flöde %s (flödena: %s)' % (namn, f_, ', '.join(FLODEN)) for f_ in sorted(angivna_f - set(FLODEN))]
        if namn.startswith('skill:') and (angivna_f & set(HARLEDDA)) != harl.get(namn, set()):
            fel.append('%s: raden säger flödena %s men tabellerna och kompetensblocken %s (designfas.py inventera --placera)' % (
                namn, ', '.join(sorted(angivna_f & set(HARLEDDA))) or 'inga', ', '.join(sorted(harl.get(namn, set()))) or 'inga'))
        if namn.startswith('fil:'):
            if delar[3].startswith('stationer:'):
                fel.append('%s: en filrad har inga egna stationer; stationerna står i bandets tabell' % namn)
            elif not delar[3].startswith(('skäl:', 'flöden:')):
                fel.append('%s: en filrad börjar med flöden: eller skäl:' % namn)
            via = harl.get('skill:' + namn[4:].split('/')[0], set())
            fel += ['%s: flödet %s når filen bara genom skillen, och skillen har inte flödet' % (namn, f_)
                    for f_ in sorted((angivna_f & set(HARLEDDA)) - via)]
            continue
        m_ = re.match(r'^stationer: ([a-z, ]+);', delar[3])
        angivna = {x.strip() for x in m_.group(1).split(',')} if m_ else set()
        if angivna - set(st):
            fel.append('%s: okänd station %s' % (namn, ', '.join(sorted(angivna - set(st)))))
        if namn in per and angivna != per[namn]:
            fel.append('%s: raden säger stationerna %s men tabellen %s' % (namn, ', '.join(sorted(angivna)) or 'inga', ', '.join(sorted(per[namn]))))
        if namn.startswith('skill:') and namn not in per and not re.search(r'(?:^|; )skäl:', delar[3]):
            fel.append('%s har varken en station eller ett skrivet skäl' % namn)
    filrader = [x[4:] for x in rader if x.startswith('fil:')]
    placerade = placerade_filer(text)
    for f in formagofiler():
        if f not in placerade and not any(fnmatch.fnmatchcase(f, g) for g in filrader):
            fel.append('filen %s har varken en plats i tabellerna eller en filrad (designfas.py inventera)' % f)
    alla = formagofiler()
    fel += ['fil:%s matchar ingen fil' % g for g in filrader if not any(fnmatch.fnmatchcase(f, g) for f in alla)]
    return fel


def formagofiler():
    """Skillsens filer som är förmågor, relativt .claude/skills (inte KALLA.md, licenser eller typsnitt)."""
    return sorted(p.relative_to(SKILLS).as_posix() for p in SKILLS.rglob('*')
                  if p.is_file() and p.suffix in FORMAGOR and p.name != 'KALLA.md' and not p.name.upper().startswith('LICENSE'))


def placerade_filer(text=None):
    """Filerna som bandets tabell eller ett kompetensblock namnger, och varje skills SKILL.md (skillens egen rad)."""
    import kompetens
    text = KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {filen(f) for x in stationer(text).values() for f in x['karna'] + x['alternativ']}
    ut |= {f for x in kompetens.tolka(text).values() for f in x['karna'] + x['efter'] + x['valj']}
    ut |= {p.relative_to(SKILLS).as_posix() for p in SKILLS.glob('*/SKILL.md')}
    return ut


def floden_i(cell):
    m = re.search(r'(?:^|; )flöden: ([a-z, ]+);', cell)
    return {x.strip() for x in m.group(1).split(',') if x.strip()} if m else set()


def harledda_floden(text=None):
    """{'skill:<namn>': {flöden}} som följer av tabellerna: band ur bandets tabell, research ur blocken forska och
    forberedelse, specialistpass ur block med ett ds-pass, overlamning ur stationen och blocket leverans, helbygge ur
    blocket helbygge (inventeringen 2026-10-12, punkt 4: kartan och blocken säger samma sak)."""
    import kompetens
    text = KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {}
    def lagg(f, flode):
        if not f.startswith(('kunskap/', 'kritik/', 'mall/')):
            ut.setdefault('skill:' + filen(f).split('/')[0], set()).add(flode)
    for sid, x in stationer(text).items():
        for f in x['karna'] + x['alternativ']:
            lagg(f, 'band')
            if sid == 'overlamning':
                lagg(f, 'overlamning')
    for bid, x in kompetens.tolka(text).items():
        floden = ({'research'} if bid in ('forska', 'forberedelse') else set()) | ({'helbygge'} if bid == 'helbygge' else set()) \
            | ({'overlamning'} if bid == 'leverans' else set()) | ({'specialistpass'} if set(x['pass']) & set(kompetens.DESIGNSTOD) else set())
        for f in x['karna'] + x['efter'] + x['valj']:
            for fl in floden:
                lagg(f, fl)
    return ut


def inventera(placera=False, text=None, idag=None):
    """Inventeringen som håller kartan aktuell (ägarens tillägg 2026-10-12 17:50Z: "uppdateras löpande också per
    automatik"): skills och filer utan plats, kartrader vars stationer eller härledda flöden inte följer tabellerna, och
    tjänsternas verktyg utan beslut. Med placera får en ny skill eller fil en preliminär rad märkt "automatiskt placerad
    <datum>, oprövad", som väntar på en verklig placering, och stationerna och flödena skrivs om ur tabellerna. Ger
    (rapportrader, ny text eller None)."""
    import kompetens
    text = KARTA.read_text(encoding='utf-8') if text is None else text
    idag = idag or nu()[:10]
    m = KARTBLOCK.search(text)
    if not m:
        return ['metodkartan saknar blocket designfas-karta'], None
    st, harl = stationer(text), harledda_floden(text)
    per = {}
    for sid, x in st.items():
        for f in x['karna'] + x['alternativ']:
            if not f.startswith(('kunskap/', 'kritik/')):
                per.setdefault('skill:' + filen(f).split('/')[0], set()).add(sid)
        for m_ in x['mcp']:
            per.setdefault('mcp:' + m_, set()).add(sid)
        for p_ in x['pass']:
            per.setdefault('pass:' + p_, set()).add(sid)
    ordning = list(st)
    rader = [r for r in m.group('rader').splitlines()]
    namn_i = {r.split(' | ')[0].strip() for r in rader if r.strip()}
    rapport, nya = [], []
    for s in sorted(p.name for p in SKILLS.iterdir() if p.is_dir() and (p / 'SKILL.md').is_file()):
        if 'skill:' + s not in namn_i:
            km = SKILLS / s / 'KALLA.md'
            kalla_ = re.search(r'github\.com/([\w.-]+/[\w.-]+)', km.read_text(encoding='utf-8')) if km.is_file() else None
            nya.append('skill:%s | %s | ingen | skäl: automatiskt placerad %s, oprövad: ny skill; läs SKILL.md och placera den '
                       'i bandets tabell, ett kompetensblock eller med ett skrivet skäl | väntar på placering' % (
                           s, kalla_.group(1) if kalla_ else 'okänd källa', idag))
    filrader = [x[4:] for x in namn_i if x.startswith('fil:')]
    placerade = placerade_filer(text)
    utan = [f for f in formagofiler() if f not in placerade and not any(fnmatch.fnmatchcase(f, g) for g in filrader)]
    for mapp in sorted({f.rsplit('/', 1)[0] for f in utan}, key=lambda x: (x.count('/'), x)):  # föräldern före barnet
        antal = sum(1 for f in utan if f.rsplit('/', 1)[0] == mapp)
        if not antal:
            continue
        nya.append('fil:%s/* | %s | ingen | skäl: automatiskt placerad %s, oprövad: %d filer utan plats; läs och placera dem i '
                   'en station, ett block eller med ett skäl | väntar på placering' % (mapp, mapp.split('/')[0], idag, antal))
        utan = [f for f in utan if not fnmatch.fnmatchcase(f, mapp + '/*')]  # fnmatch låter * gå över /: underkatalogerna med
    rapport += ['ny rad: ' + r[:110] for r in nya]
    rader = [r for r in rader if r.strip()] + nya
    for i, rad in enumerate(rader):  # stationerna och de härledda flödena ur tabellerna, också på de nya raderna
        delar = [x.strip() for x in rad.split(' | ')]
        if len(delar) != 5:
            continue
        namn, cell = delar[0], delar[3]
        ny = cell
        if not namn.startswith('fil:'):
            ratt = sorted(per.get(namn, set()), key=ordning.index)
            sm = re.match(r'^stationer: ([a-z, ]+); ', ny)
            if ratt and (not sm or [x.strip() for x in sm.group(1).split(',')] != ratt):
                ny = 'stationer: %s; %s' % (', '.join(ratt), ny[sm.end():] if sm else ny)
            elif not ratt and sm:
                ny = 'skäl: inte längre i bandets tabell, automatiskt %s; %s' % (idag, ny[sm.end():])
        if namn.startswith('skill:'):
            ratt_f = sorted(harl.get(namn, set()) | (floden_i(ny) - set(HARLEDDA)), key=FLODEN.index)
            if sorted(floden_i(ny), key=FLODEN.index) != ratt_f:
                fm = re.search(r'(?:^|; )flöden: [a-z, ]+;', ny)
                utan_f = (ny[:fm.start()] + ('; ' if fm.start() else '') + ny[fm.end():].lstrip()) if fm else ny
                sm = re.match(r'^stationer: [^;]*; ', utan_f)
                flod = 'flöden: %s; ' % ', '.join(ratt_f) if ratt_f else ''
                ny = (utan_f[:sm.end()] + flod + utan_f[sm.end():]) if sm else flod + utan_f
                ny = ny.replace(';; ', '; ').strip()
        if ny != cell:
            if namn not in {r.split(' | ')[0] for r in nya}:
                rapport.append('%s: %s → %s' % (namn, cell[:70], ny[:70]))
            delar[3] = ny
            rader[i] = ' | '.join(delar)
    vantar = [r.split(' | ')[0] for r in rader if 'automatiskt placerad' in r]
    andrat = [r for r in rapport]
    rapport += ['väntar på en verklig placering: %s' % ', '.join(vantar)] if vantar else []
    rapport += ['tjänsternas verktyg: ' + x for x in kompetens.tjanstverktyg_fel(text)]
    if not placera or not andrat:
        return rapport, None
    return rapport, text[:m.start('rader')] + '\n'.join(rader) + '\n' + text[m.end('rader'):]


def start(slug, skriv_bara=False, underlag=None):
    """Kommandot som startar utföraren: en interaktiv session i repots rot med kundvakten för slug, tjänsterna ur
    kontroller/mcp/ (nyckelfilerna privat), --strict-mcp-config, godkännandet nekat, och skillen designfas som första
    meddelande. Ägaren kör det (./design.sh <slug>); det startar inget annat."""
    import atelje
    import kundvakt
    designfas(slug, underlag)
    if lage(slug, underlag) == 'duk':
        duk_pausad('./design.sh för en designfas i läget duk')
    inst = json.loads(kundvakt.installningar(slug, Path(underlag or UNDERLAG)))
    inst.setdefault('permissions', {}).setdefault('deny', []).extend(['Bash(*designfas.py godkann*)', 'Bash(*skapande.py dom*)'])
    f = rot(slug, underlag) / 'session' / 'installningar.json'
    skriv(f, inst)
    mcp = [atelje.refero_mcp_fil(), str(ROOT / 'kontroller' / 'mcp' / 'mobbin.json'), str(ROOT / 'kontroller' / 'mcp' / 'motion.json'),
           atelje.tjugoforsta_mcp_fil()]
    args = [atelje.claude(), '--settings', str(f), '--strict-mcp-config', '--mcp-config', *mcp, '--', '/designfas %s' % slug]
    if skriv_bara:
        return args
    os.chdir(ROOT)
    os.execvp(args[0], args)


def main(argv=None):
    p = argparse.ArgumentParser(prog='designfas', description=__doc__.split('\n\n')[0], allow_abbrev=False)
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('ny'); a.add_argument('slug'); a.add_argument('--kanvas'); a.add_argument('--release')
    a.add_argument('--lage', choices=LAGEN)
    a = s.add_parser('riktningar'); a.add_argument('slug'); a.add_argument('riktningar', nargs='+')
    a = s.add_parser('artefakt'); a.add_argument('slug'); a.add_argument('riktning'); a.add_argument('--url')
    a.add_argument('--version'); a.add_argument('--artifact-version')
    a = s.add_parser('runtime'); a.add_argument('slug'); a.add_argument('--fil', required=True); a.add_argument('--release', required=True)
    a = s.add_parser('tillgang'); a.add_argument('slug'); a.add_argument('--blob', required=True); a.add_argument('--fil', required=True)
    a.add_argument('--kalla', default='')
    a = s.add_parser('version'); a.add_argument('slug'); a.add_argument('--fran')
    a.add_argument('--artifact-version'); a.add_argument('--orsak', required=True); a.add_argument('--paket', action='append', default=[])
    a.add_argument('--bestallning', action='append', default=[]); a.add_argument('--av', default='utforaren')
    a.add_argument('--utan-bilder', action='store_true')
    a.add_argument('--station'); a.add_argument('--ritning'); a.add_argument('--hoppa', action='append', default=[])
    a = s.add_parser('rendera'); a.add_argument('slug'); a.add_argument('version'); a.add_argument('--kontroll', action='store_true')
    a = s.add_parser('bestall'); a.add_argument('slug'); a.add_argument('--typ', required=True, choices=list(TYPER))
    a.add_argument('--version', required=True); a.add_argument('--ritning', required=True); a.add_argument('--uppgift', required=True)
    a.add_argument('--material', action='append', default=[]); a.add_argument('--station')
    a = s.add_parser('specialist'); a.add_argument('slug'); a.add_argument('bestallning'); a.add_argument('--modell')
    a = s.add_parser('svar'); a.add_argument('slug'); a.add_argument('bestallning'); a.add_argument('--fil', required=True)
    a.add_argument('--utforare', required=True)
    a = s.add_parser('infor'); a.add_argument('slug'); a.add_argument('bestallning'); a.add_argument('--version', required=True)
    a.add_argument('--bedomning', required=True)
    a = s.add_parser('godkann'); a.add_argument('slug'); a.add_argument('version'); a.add_argument('--ritning', required=True)
    a.add_argument('--text', default='')
    a = s.add_parser('overlamna'); a.add_argument('slug'); a.add_argument('--prova', action='store_true')
    a = s.add_parser('status'); a.add_argument('slug')
    a = s.add_parser('kvitto'); a.add_argument('slug'); a.add_argument('--session', required=True); a.add_argument('--pass', default='skapa')
    a.add_argument('--station')
    a = s.add_parser('station'); a.add_argument('slug'); a.add_argument('station'); a.add_argument('--ritning', required=True)
    a = s.add_parser('karta'); a.add_argument('--prova', action='store_true')
    a = s.add_parser('inventera'); a.add_argument('--placera', action='store_true')
    a = s.add_parser('start'); a.add_argument('slug'); a.add_argument('--skriv-bara', action='store_true')
    x = p.parse_args(argv)
    ut = lambda d: print(json.dumps(d, ensure_ascii=False, indent=1))  # noqa: E731
    try:
        if x.cmd == 'ny':
            ut(ny(x.slug, x.kanvas, x.release, lage_=x.lage))
        elif x.cmd == 'riktningar':
            ut(riktningar(x.slug, x.riktningar))
        elif x.cmd == 'artefakt':
            if x.url or x.version:
                if not (x.url and x.version):
                    raise Fel('publiceringen registreras med både --url och --version')
                ut(registrera_artefakt(x.slug, x.riktning, x.url, x.version, x.artifact_version))
            else:
                r = artefakt(x.slug, x.riktning)
                ut(r)
                return 1 if r['varningar'] and any('15 MB' in v or '511' in v for v in r['varningar']) else 0
        elif x.cmd == 'runtime':
            ut(runtime(x.slug, x.fil, x.release))
        elif x.cmd == 'tillgang':
            ut(tillgang(x.slug, x.blob, x.fil, x.kalla))
        elif x.cmd == 'version':
            try:
                post = version(x.slug, x.fran, x.artifact_version, x.orsak, x.bestallning, x.av, not x.utan_bilder, station_=x.station,
                               ritning=x.ritning, hoppade=x.hoppa, paket=x.paket)
            except ByggFel as e:
                print('designfas: %s' % e, file=sys.stderr)
                return 1
            ut({k: post.get(k) for k in ('version', 'station', 'ritning', 'hoppade', 'artifact_version', 'sidor', 'ej_renderade', 'paket',
                                         'okanda_tillgangar', 'rendering', 'insats', 'notering', 'varningar')})
            return 0 if (post.get('rendering') or {}).get('slutkod', 0) == 0 and not post.get('okanda_tillgangar') else 1
        elif x.cmd == 'rendera':
            r = rendera(x.slug, x.version, x.kontroll)
            ut(r)
            return 0 if r['slutkod'] == 0 and not r['saknade_tillgangar'] else 1
        elif x.cmd == 'bestall':
            ut(bestall(x.slug, x.typ, x.version, x.ritning, x.uppgift, x.material, station_=x.station))
        elif x.cmd == 'specialist':
            post = specialist(x.slug, x.bestallning, modell=x.modell)
            ut({k: post.get(k) for k in ('id', 'station', 'pass', 'session_id', 'utfall', 'sekunder', 'ej_observerat')})
            return 0 if post['utfall'] == 'levererad' else 1
        elif x.cmd == 'svar':
            ut(svar(x.slug, x.bestallning, x.fil, x.utforare))
        elif x.cmd == 'infor':
            ut(infor(x.slug, x.bestallning, x.version, x.bedomning))
        elif x.cmd == 'godkann':
            ut(godkann(x.slug, x.version, x.ritning, x.text))
            print('Designen är godkänd. Bygget startar inte av det: nästa steg är överlämningen (designfas.py overlamna) och '
                  'sedan ditt beslut om byggstart (./kor.sh %s "<verksamhet>").' % x.slug)
        elif x.cmd == 'overlamna':
            if not x.prova:
                print('paketet: %s' % rel(overlamna(x.slug)))
            b = overlamning_brister(x.slug)
            print('\n'.join(['brister i överlämningen:'] + ['- ' + y for y in b]) if b else 'överlämningen är komplett')
            return 1 if b else 0
        elif x.cmd == 'status':
            ut(status(x.slug))
        elif x.cmd == 'kvitto':
            ut(kvitto(x.session, getattr(x, 'pass'), x.station))
        elif x.cmd == 'station':
            print(station_brief(x.slug, x.station, x.ritning))
        elif x.cmd == 'inventera':
            rapport, ny_karta = inventera(placera=x.placera)  # inte "ny": det namnet är kommandot ny i hela main()
            if ny_karta is not None:
                KARTA.write_text(ny_karta, encoding='utf-8')
            print('\n'.join(rapport) if rapport else 'inventeringen: varje skill, fil och tjänst har sin plats, och kartan följer tabellerna')
            if x.placera:  # underhållet läser slutkoden: kartan ska hålla efter placeringen, också när inget skrevs
                f = karta_prova()
                print('\n'.join(['kartan efter placeringen:'] + f) if f else 'kartan %s och prövad (karta --prova utan fel)' % (
                    'skriven' if ny_karta is not None else 'oförändrad'))
                return 1 if f else 0
            return 0
        elif x.cmd == 'karta':
            f = karta_prova()
            print('\n'.join(f) if f else 'designfas-karta: varje skill, tjänst och specialistpass har sin rad')
            return 1 if f else 0
        elif x.cmd == 'start':
            print(' '.join(start(x.slug, skriv_bara=x.skriv_bara) or []))
    except Fel as e:
        print('designfas: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
