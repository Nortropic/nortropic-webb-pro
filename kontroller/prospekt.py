#!/usr/bin/env python3
"""prospekt.py — hittar verksamheter i en bransch och kommun (SCB:s allmänna företagsregister), letar upp deras
webbplats och mäter den med repots egna verktyg. Registret ligger i underlag/prospekt/<kampanj>/REGISTER.json,
mätningen i underlag/<slug>/diagnos/ (samma layout som bygg-sajt steg 2) och poängen i underlag/<slug>/PROSPEKT.json.

    .venv/bin/python kontroller/prospekt.py svep --kampanj hantverkare-lulea --kommun 2580 --bransch hantverkare [--om]
    .venv/bin/python kontroller/prospekt.py sajter --kampanj X [--max 40] [--slug s [--url https://…]] [--om]
    .venv/bin/python kontroller/prospekt.py analysera --kampanj X [--max 10] [--slug s] [--om]
    .venv/bin/python kontroller/prospekt.py poangsatt --kampanj X [--slug s]
    .venv/bin/python kontroller/prospekt.py lista --kampanj X
    .venv/bin/python kontroller/prospekt.py gallra [--kampanj X] [--manader 12] [--torr]

Exit: 0 ok · 2 fel i anropet eller en körning pågår redan · 3 nyckel saknas eller ogiltig · 4 yttre fel eller budget slut.
Miljö: NWP_PROSPEKT_NYCKELFIL (~/.nortropic-hemligheter/webb-pro/scb.env med SCB_API_NYCKEL=…), NWP_PROSPEKT_SCB_BAS
(https://apiafr.scb.se/v1/), NWP_PROSPEKT_SCB_TAK (400 SCB-anrop per dygn), NWP_PROSPEKT_SOK_TAK (300 sökningar per
dygn), NWP_PROSPEKT_PAUS (20 s mellan sajter), NWP_PROSPEKT_GALLRING_MANADER (12).
Dödsknapp: filen underlag/prospekt/STOPP stoppar varje körning före nästa nätanrop. Reglerna och vad som lagras:
kunskap/prospekt-och-utskick.md.
"""
import argparse
import json
import os
import random
import re
import shutil
import stat
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prospektfiler as pf  # noqa: E402
import hamta_sajt as hs  # noqa: E402
import prospekt_poang as pp  # noqa: E402
import prova  # noqa: E402
import copy_kontroll as ck  # noqa: E402
import seo_kontroll as seo  # noqa: E402

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

ROOT = pf.ROOT
PROSPEKT = pf.PROSPEKT
STOPP = PROSPEKT / 'STOPP'
KODER = PROSPEKT / 'KODER.json'
BRANSCHER = ROOT / 'kunskap' / 'prospekt-branscher.json'
SCB_BAS = os.environ.get('NWP_PROSPEKT_SCB_BAS') or 'https://apiafr.scb.se/v1/'
NYCKELFIL = Path(os.environ.get('NWP_PROSPEKT_NYCKELFIL') or (Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'scb.env'))
SCB_TAK = int(os.environ.get('NWP_PROSPEKT_SCB_TAK') or 400)
SOK_TAK = int(os.environ.get('NWP_PROSPEKT_SOK_TAK') or 300)
PAUS = float(os.environ.get('NWP_PROSPEKT_PAUS') or 20)
GALLRING = int(os.environ.get('NWP_PROSPEKT_GALLRING_MANADER') or 12)
KODTABELLER = ('jurformkoder', 'ftgstatkoder', 'reklamsparrtypkoder', 'epostsparrtypkoder', 'telefonsparrtypkoder',
               'anstklkoder', 'naringsgrenkoder', 'kommunkoder')
KODER_GILTIGA_DAGAR = 30
GENERISKA = {'gmail.com', 'hotmail.com', 'hotmail.se', 'outlook.com', 'live.se', 'live.com', 'msn.com', 'icloud.com', 'me.com',
             'yahoo.com', 'yahoo.se', 'telia.com', 'tele2.se', 'comhem.se', 'bredband.net', 'bahnhof.se', 'spray.se', 'passagen.se',
             'home.se', 'swipnet.se', 'protonmail.com', 'proton.me', 'googlemail.com', 'ownit.nu', 'bredband2.com', 'telenor.se', 'tre.se'}
KATALOGER = re.compile(r'(^|\.)(hitta|eniro|allabolag|ratsit|merinfo|bolagsfakta|proff|reco|118100|foretagsfakta|kompass|cylex|yelp|'
                       r'trustpilot|linkedin|hantverkskollen|offerta|byggvalet|scb|bolagsverket|solidinfo|uc|creditsafe|mrkoll|'
                       r'foretagande|allakompaniet|kreditrapporten|lokaldelen|gulasidorna|servicefinder|dinbyggare|branschregistret)\.(se|com|nu|net|org)$', re.I)
SOCIALA = re.compile(r'(^|\.)(facebook|instagram|fb|linkedin|youtube|tiktok|x|twitter)\.(com|se)$', re.I)
GOOGLE = re.compile(r'(^|\.)google\.[a-z.]+$|(^|\.)maps\.app\.goo\.gl$', re.I)
PARKERAD = re.compile(r'(parkerad|parked|till salu|domain is for sale|domänen är ledig|under uppbyggnad|under construction|coming soon|'
                      r'kommer snart|this domain|köp dom[äa]nen)', re.I)
STOPPORD = {'och', 'för', 'med', 'the', 'and', 'från', 'norr', 'nord', 'syd', 'väst', 'öst'}
BOLAGSTOKEN = re.compile(r'\b(ab|aktiebolag|hb|kb|handelsbolag|kommanditbolag|ek|för|ekonomisk|förening|enskild|firma|f:a|i|och)\b', re.I)
RESERVERADE = {'ab', 'prospekt', 'rokprov', 'rokprov-mall'}
SIDA_VIKTIG = re.compile(r'(kontakt|contact)', re.I)


class Avbrott(Exception):
    def __init__(self, kod, text):
        super().__init__(text)
        self.kod, self.text = kod, text


def stopp():
    if STOPP.is_file():
        raise Avbrott(4, 'dödsknappen är nedtryckt: %s finns; ta bort filen för att köra igen' % STOPP)


def nu():
    return pf.nu()


def idag():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def budget(kampanj, typ, tak):
    """Antal händelser av typen i dag ur logg.jsonl; över taket avbryts körningen (exit 4)."""
    logg = pf.kampanjkatalog(kampanj) / 'logg.jsonl'
    n = 0
    if logg.is_file():
        dag = idag()
        with open(logg, encoding='utf-8') as f:
            for rad in f:
                if ('"handelse": "%s"' % typ) in rad and ('"tid": "%s' % dag) in rad:
                    n += 1
    if n >= tak:
        raise Avbrott(4, 'dagsbudgeten för %s är slut (%d av %d); fortsätt i morgon eller höj taket' % (typ, n, tak))
    return n


def nyckel():
    try:
        st = NYCKELFIL.stat()
    except OSError:
        raise Avbrott(3, 'SCB-nyckel saknas: skapa %s med raden SCB_API_NYCKEL=… (chmod 600; nyckeln söks med BankID på registreraafr.scb.se)' % NYCKELFIL)
    if stat.S_IMODE(st.st_mode) & 0o077:
        raise Avbrott(3, 'nyckelfilen %s får bara läsas av dig: chmod 600' % NYCKELFIL)
    for rad in NYCKELFIL.read_text(encoding='utf-8').splitlines():
        if rad.startswith('SCB_API_NYCKEL='):
            v = rad.split('=', 1)[1].strip().strip('"\'')
            if len(v) >= 16:
                return v
    raise Avbrott(3, 'ingen giltig rad SCB_API_NYCKEL=… i %s' % NYCKELFIL)


# --- SCB ---

class Scb:
    """SCB:s allmänna företagsregister: X-API-Key, 0,5 s mellan anrop, 429 med Retry-After, nattfönster 04:00–04:30."""

    def __init__(self, nyckel, bas=SCB_BAS, kampanj=None):
        self.nyckel, self.bas, self.kampanj = nyckel, bas.rstrip('/') + '/', kampanj
        self.senast = 0.0

    def nattfonster(self):
        if not ZoneInfo:
            return
        try:
            t = datetime.now(ZoneInfo('Europe/Stockholm'))
        except Exception:
            return
        if (t.hour == 3 and t.minute >= 58) or (t.hour == 4 and t.minute < 35):
            mal = t.replace(hour=4, minute=35, second=0, microsecond=0)
            if mal < t:
                mal += timedelta(days=1)
            s = (mal - t).total_seconds()
            print('SCB uppdaterar registret 04:00–04:30; väntar %d s' % s, flush=True)
            time.sleep(s)

    def hamta(self, vag, params=None):
        stopp()
        if self.kampanj:
            budget(self.kampanj, 'scb_anrop', SCB_TAK)
        self.nattfonster()
        url = self.bas + vag.lstrip('/') + ('?' + urllib.parse.urlencode(params) if params else '')
        vantetider = (5, 15, 45, 45, 45, 45)
        sista = None
        for forsok in range(len(vantetider)):
            time.sleep(max(0.0, 0.5 - (time.time() - self.senast)))
            req = urllib.request.Request(url, headers={'X-API-Key': self.nyckel, 'Accept': 'application/json', 'User-Agent': hs.UA})
            self.senast = time.time()
            if self.kampanj:
                pf.logga(self.kampanj, 'scb_anrop', vag=vag)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise Avbrott(3, 'SCB svarar %d: nyckeln är ogiltig eller saknar behörighet' % e.code)
                if e.code == 404:
                    return None
                if e.code == 429:
                    ra = e.headers.get('Retry-After') or ''
                    time.sleep(min(float(ra) if ra.isdigit() else 30.0, 120.0))
                    sista = e
                    continue
                if e.code >= 500:
                    time.sleep(vantetider[forsok])
                    sista = e
                    continue
                raise Avbrott(4, 'SCB svarar %d på %s' % (e.code, vag))
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
                time.sleep(vantetider[forsok])
                sista = e
        raise Avbrott(4, 'SCB gick inte att nå (%s): %s' % (vag, sista))

    def sidor(self, vag, limit=5000, cursor=None):
        """Ger (poster, nästa cursor eller None) per sida tills hasMore är false."""
        while True:
            params = {'limit': limit}
            if cursor:
                params['cursorId'] = cursor
            d = self.hamta(vag, params) or {}
            poster = d.get('jes') or d.get('aes') or next((v for v in d.values() if isinstance(v, list)), [])
            pag = d.get('pagination') or {}
            cursor = pag.get('nextCursorId') if pag.get('hasMore') else None
            yield poster, cursor
            if not cursor:
                return

    def koder(self):
        """Kodtabellerna ur underlag/prospekt/KODER.json (högst 30 dagar gamla), annars hämtade."""
        k = pf.las_json(KODER) or {}
        hamtad = k.get('hamtad') or ''
        if k.get('tabeller') and hamtad[:10] >= (datetime.now(timezone.utc) - timedelta(days=KODER_GILTIGA_DAGAR)).strftime('%Y-%m-%d'):
            return k['tabeller']
        tabeller = {}
        for t in KODTABELLER:
            d = self.hamta('kodtabeller/' + t)
            lista = d if isinstance(d, list) else next((v for v in (d or {}).values() if isinstance(v, list)), [])
            tabeller[t] = [{'kod': str(x.get('kod')), 'klartext': str(x.get('klartext') or '')} for x in lista if isinstance(x, dict) and x.get('kod') is not None]
        pf.skriv_json(KODER, {'hamtad': nu(), 'kalla': self.bas, 'tabeller': tabeller})
        return tabeller

    def full(self, pe_orgnr):
        return self.hamta('juridiskaenheter/%s/full' % urllib.parse.quote(str(pe_orgnr)))


def kodtext(koder, tabell, kod):
    if kod is None:
        return None
    for k in (koder or {}).get(tabell) or []:
        if str(k.get('kod')) == str(kod):
            return k.get('klartext') or None
    return None


def aktiva_koder(koder):
    ut = set()
    for k in (koder or {}).get('ftgstatkoder') or []:
        kt = k.get('klartext') or ''
        if re.search(r'verksam|aktiv', kt, re.I) and not re.search(r'(^|\s)(ej|inte|aldrig|icke)\b|upphör|avregist|avslut|vilande', kt, re.I):
            ut.add(str(k['kod']))
    return ut or {'1'}


def fysiska_koder(koder):
    ut = set()
    for k in (koder or {}).get('jurformkoder') or []:
        if re.search(r'enskild|fysisk|enkelt bolag|dödsbo|partrederi', k.get('klartext') or '', re.I):
            ut.add(str(k['kod']))
    return ut or {'10'}


def ar_sparr(koder, tabell, kod):
    """True = spärr. Okänd kod räknas som spärr (okänt nekar)."""
    if kod is None:
        return True
    kt = kodtext(koder, tabell, kod)
    if kt is None:
        return str(kod) not in ('0', '1')  # utan tabell: 0/1 brukar betyda "ingen spärr"; allt annat spärr
    if re.search(r'saknas|ingen|accept|tillåt|\bja\b|får', kt, re.I):
        return False
    if re.search(r'spärr|avböj|\bnej\b|vill inte|\bej\b|inte', kt, re.I):
        return True
    return True


def normalisera_sni(kod):
    return re.sub(r'\D', '', str(kod or ''))


def primar_sni(je):
    p = je.get('primarNaringsgren') or {}
    if p.get('naringsgren'):
        return str(p['naringsgren'])
    for n in je.get('naringsgrenar') or []:
        if n.get('rangordning') in (1, '1'):
            return str(n.get('naringsgren') or '')
    return ''


def i_bransch(je, prefixar):
    kod = normalisera_sni(primar_sni(je))
    return bool(kod) and any(kod.startswith(p) for p in prefixar)


def doman(host):
    return hs.doman(host)


def doman_av_epost(epost):
    if not epost or '@' not in epost:
        return None
    d = doman(epost.rsplit('@', 1)[1].strip().lower())
    return d or None


def slugga(text):
    s = unicodedata.normalize('NFKD', (text or '').lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = BOLAGSTOKEN.sub(' ', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:50].strip('-')


def slug_for(namn, postort, orgnr, tagna):
    bas = slugga(namn) or 'verksamhet'
    if len(bas) < 2:
        bas = bas + '-x'
    kandidater = [bas, (bas + '-' + slugga(postort))[:60].strip('-') if postort else None, (bas + '-' + str(orgnr or '')[-4:])[:60].strip('-')]
    for k in kandidater:
        if k and pf.SLUG.match(k) and k not in tagna and k not in RESERVERADE and not k.startswith('rokprov') and not k.endswith(('-abx', '-aby')):
            return k
    i = 2
    while True:
        k = ('%s-%d' % (bas[:55], i))
        if k not in tagna:
            return k
        i += 1


def tagna_slugs(poster, egen_pe=None):
    ut = {p['slug'] for p in poster if p.get('slug') and p.get('peOrgNr') != egen_pe}
    for d in (ROOT / 'underlag', ROOT / 'kunder'):
        if d.is_dir():
            ut |= {x.name for x in d.iterdir() if x.is_dir()}
    return ut


def las_branscher():
    d = pf.las_json(BRANSCHER) or {}
    return d.get('branscher') or {}


def post_av(je, full, koder, bransch, kommun_namn, slug, fysiska, kampanj_id):
    """En registerpost ur SCB:s delpost + /full. Minimering: ingen gatuadress, ingen c/o, e-post bara för juridiska personer."""
    f = full or {}
    adr = f.get('postAdress') or je.get('postAdress') or {}
    jur = str(f.get('jurform') or je.get('jurform') or '')
    fys = jur in fysiska
    sp = {'reklam': ar_sparr(koder, 'reklamsparrtypkoder', je.get('reklamSparrTyp', f.get('reklamSparrTyp'))),
          'telefon': ar_sparr(koder, 'telefonsparrtypkoder', je.get('telefonSparrTyp', f.get('telefonSparrTyp'))),
          'epost': ar_sparr(koder, 'epostsparrtypkoder', je.get('epostSparrTyp', f.get('epostSparrTyp')))}
    tel = (f.get('tel') or '').strip() or None
    epost = (f.get('epost') or '').strip() or None
    epost_doman = doman_av_epost(epost)
    if sp['telefon']:
        tel = None
    if fys or sp['epost']:
        epost = None
    sni = []
    for n in (f.get('naringsgrenar') or [je.get('primarNaringsgren')]):
        if n and n.get('naringsgren'):
            sni.append({'kod': str(n['naringsgren']), 'text': kodtext(koder, 'naringsgrenkoder', n['naringsgren']), 'rangordning': n.get('rangordning')})
    sni.sort(key=lambda x: (x['rangordning'] is None, x['rangordning'] if isinstance(x['rangordning'], int) else 9))
    anst = f.get('anstKl') or je.get('anstKl')
    post = {
        'slug': slug, 'peOrgNr': str(je.get('peOrgNr') or f.get('peOrgNr') or ''), 'orgNr': str(je.get('orgNr') or f.get('orgNr') or ''),
        'namn': (je.get('namn') or f.get('namn') or '').strip(), 'jurform': jur, 'jurform_text': kodtext(koder, 'jurformkoder', jur),
        'fysisk_person': fys, 'postort': (adr.get('postOrt') or '').strip().title() or None, 'postnr': (adr.get('postNr') or '').strip() or None,
        'kommun': kommun_namn, 'kommunKod': str(je.get('kommunSate') or f.get('kommunSate') or ''),
        'sni': sni, 'anstKl': str(anst) if anst is not None else None, 'anstKl_text': kodtext(koder, 'anstklkoder', anst),
        'ftgStat': str(f.get('ftgStat') or je.get('ftgStat') or ''), 'startDat': (f.get('startDat') or None),
        'tel': tel, 'epost': epost, 'epost_doman': epost_doman, 'sparr': sp, 'sajt': None, 'sajt_kandidat': None, 'kanaler': {},
        'status': 'ny', 'poang': None, 'analys_tid': None, 'avvisad_skal': None, 'bransch': bransch,
        'kalla': 'SCB AFR %s' % idag(), 'skapad': nu(), 'uppdaterad': nu(),
    }
    if sp['reklam']:
        post['status'], post['avvisad_skal'] = 'avvisad', 'reklamsparr'
    return post


SCB_FALT = ('orgNr', 'namn', 'jurform', 'jurform_text', 'fysisk_person', 'postort', 'postnr', 'kommun', 'kommunKod', 'sni', 'anstKl',
            'anstKl_text', 'ftgStat', 'startDat', 'tel', 'epost', 'epost_doman', 'sparr', 'kalla')


def svep(a):
    stopp()
    kdir = pf.kampanjkatalog(a.kampanj)
    kdir.mkdir(parents=True, exist_ok=True)
    pf.pagar_ta(kdir)
    try:
        branscher = las_branscher()
        b = branscher.get(a.bransch)
        if not b:
            raise Avbrott(2, 'okänd bransch %r; välj bland %s (kunskap/prospekt-branscher.json)' % (a.bransch, ', '.join(sorted(branscher))))
        prefixar = [normalisera_sni(p) for p in b.get('sni_prefix') or []]
        if not re.fullmatch(r'\d{4}', a.kommun or ''):
            raise Avbrott(2, 'kommunkod med fyra siffror, t.ex. 2580 för Luleå')
        scb = Scb(nyckel(), kampanj=a.kampanj)
        koder = scb.koder()
        traff = [k for k in koder.get('naringsgrenkoder') or [] if any(normalisera_sni(k['kod']).startswith(p) for p in prefixar)]
        if koder.get('naringsgrenkoder') and not traff:
            raise Avbrott(2, 'inga SNI-koder träffas av %s; rätta kunskap/prospekt-branscher.json' % b.get('sni_prefix'))
        print('SNI-koder som träffas av %s (%d st):' % (a.bransch, len(traff)))
        for k in traff[:80]:
            print('  %s  %s' % (k['kod'], k['klartext']))
        kampanj = {} if a.om else (pf.las_json(kdir / 'KAMPANJ.json') or {})
        sv = kampanj.get('svep') or {}
        if sv.get('klar') and not a.om:
            print('svepet är redan klart (%s); kör med --om för att svepa igen' % sv.get('tid'))
            return 0
        kommun_namn = a.kommun_namn or kodtext(koder, 'kommunkoder', a.kommun) or kampanj.get('kommun')
        kampanj.update({'bransch': a.bransch, 'bransch_namn': b.get('namn'), 'kommunKod': a.kommun, 'kommun': kommun_namn,
                        'sni_prefix': b.get('sni_prefix'), 'sni_traffade': [k['kod'] for k in traff][:200],
                        'andamal': 'urval av verksamheter för demonstration av webbplats; rättslig grund berättigat intresse; gallras efter %d månader' % GALLRING,
                        'skapad': kampanj.get('skapad') or nu(), 'status': 'sveper', 'svep': sv})
        pf.skriv_json(kdir / 'KAMPANJ.json', kampanj)
        aktiva, fysiska = aktiva_koder(koder), fysiska_koder(koder)
        pf.logga(a.kampanj, 'svep_start', kommun=a.kommun, bransch=a.bransch, cursor=sv.get('cursorId'))
        antal_scb, antal_traff, nya, uppdaterade = sv.get('antal_scb', 0), sv.get('antal_traff', 0), 0, 0
        cursor = sv.get('cursorId')
        for poster_scb, nasta in scb.sidor('juridiskaenheter/kommun/%s' % a.kommun, cursor=cursor):
            sidans = []
            for je in poster_scb:
                antal_scb += 1
                if str(je.get('ftgStat')) not in aktiva or not i_bransch(je, prefixar) or not je.get('peOrgNr'):
                    continue
                antal_traff += 1
                full = scb.full(je['peOrgNr']) or {}
                sidans.append((je, full))

            def mut(poster, sidans=sidans):
                nonlocal nya, uppdaterade
                for je, full in sidans:
                    pe = str(je['peOrgNr'])
                    p = pf.hitta_post(poster, peOrgNr=pe)
                    tagna = tagna_slugs(poster, egen_pe=pe)
                    ny = post_av(je, full, koder, a.bransch, kommun_namn, (p or {}).get('slug') or slug_for(je.get('namn') or '', (full.get('postAdress') or je.get('postAdress') or {}).get('postOrt'), je.get('orgNr'), tagna), fysiska, a.kampanj)
                    if p:
                        for k in SCB_FALT:
                            p[k] = ny[k]
                        if ny['status'] == 'avvisad' and p['status'] in ('ny', 'utan-sajt', 'analyserad'):
                            p['status'], p['avvisad_skal'] = 'avvisad', 'reklamsparr'
                        p['uppdaterad'] = nu()
                        uppdaterade += 1
                    else:
                        poster.append(ny)
                        nya += 1
            pf.skriv_register(a.kampanj, mut)
            sv.update({'cursorId': nasta, 'antal_scb': antal_scb, 'antal_traff': antal_traff, 'tid': nu(), 'klar': nasta is None})
            kampanj['svep'] = sv
            kampanj['status'] = 'svept' if nasta is None else 'sveper'
            pf.skriv_json(kdir / 'KAMPANJ.json', kampanj)
            print('  sida klar: %d poster i registret hittills, %d träffar, nästa cursor %s' % (antal_scb, antal_traff, 'ingen' if nasta is None else 'finns'), flush=True)
        pf.logga(a.kampanj, 'svep_klar', antal_scb=antal_scb, antal_traff=antal_traff, nya=nya, uppdaterade=uppdaterade)
        print('svep klart: %d juridiska enheter i kommunen, %d i branschen, %d nya, %d uppdaterade → %s' % (antal_scb, antal_traff, nya, uppdaterade, kdir / 'REGISTER.json'))
        return 0
    finally:
        pf.pagar_slapp(kdir)


# --- sajter ---

def namntoken(namn):
    s = BOLAGSTOKEN.sub(' ', (namn or '').lower())
    tok = [t for t in re.findall(r'[a-zåäö0-9]{4,}', s) if t not in STOPPORD]
    return tok or [t for t in re.findall(r'[a-zåäö0-9]{3,}', s)]


def slutdoman_ok(host):
    return bool(host) and not KATALOGER.search(host) and not SOCIALA.search(host) and not GOOGLE.search(host)


def verifiera(url, post):
    """Är det här verksamhetens egen sajt? Säkerhet 0–1 ur namntoken, organisationsnummer, telefon och postort."""
    svar = hs.hamta(url, timeout=20)
    if not svar.get('status') or svar['status'] >= 400:
        return None
    slut = svar['url']
    host = doman(urllib.parse.urlsplit(slut).hostname)
    if not slutdoman_ok(host):
        return {'url': slut, 'sakerhet': 0.0, 'titel': '', 'skal': 'katalog eller kanal'}
    rå = hs.avkoda(svar)
    p = hs.Sida()
    try:
        p.feed(rå)
    except Exception:
        pass
    text = p.ren_text() if hasattr(p, 'ren_text') else ''
    titel = ' '.join((p.titel or '').split())
    ord_ = len(re.findall(r'\w+', text))
    if PARKERAD.search(rå[:60000]) and ord_ < 60:
        return {'url': slut, 'sakerhet': 0.0, 'titel': titel, 'parkerad': True}
    hay = (titel + ' ' + text[:30000] + ' ' + host).lower()
    tok = namntoken(post.get('namn'))
    traff = sum(1 for t in tok if t in hay)
    s = 0.0
    if tok and (traff >= 2 or (len(tok) == 1 and traff == 1)):
        s += 0.4
    elif traff:
        s += 0.2
    orgnr = re.sub(r'\D', '', post.get('orgNr') or '')
    if len(orgnr) == 10 and (orgnr in re.sub(r'\D', '', rå) or ('%s-%s' % (orgnr[:6], orgnr[6:])) in rå):
        s += 0.3
    tel = re.sub(r'\D', '', post.get('tel') or '')
    if len(tel) >= 7 and tel[-7:] in re.sub(r'\D', '', rå):
        s += 0.2
    if post.get('postort') and post['postort'].lower() in hay:
        s += 0.1
    return {'url': slut, 'sakerhet': round(min(1.0, s), 2), 'titel': titel, 'ord': ord_}


def sok_ddgs(post, kampanj, sokta, kanaler):
    """Upp till tre kandidatadresser ur DuckDuckGo; kataloger bort, kanaler (Facebook, Instagram) sparas."""
    budget(kampanj, 'sok_anrop', SOK_TAK)
    try:
        from ddgs import DDGS
        from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException
    except ImportError:
        raise Avbrott(4, 'paketet ddgs saknas: .venv/bin/python -m pip install ddgs')
    fraga = '"%s" %s' % (BOLAGSTOKEN.sub(' ', post.get('namn') or '').strip(), post.get('postort') or '')
    fraga = ' '.join(fraga.split())
    sokta.append(fraga)
    pf.logga(kampanj, 'sok_anrop', fraga=fraga, slug=post.get('slug'))
    time.sleep(3 + random.uniform(0, 2))
    res = None
    for vantan in (60, 120, 300):
        try:
            res = DDGS(timeout=10).text(fraga, region='se-sv', max_results=8)
            break
        except RatelimitException:
            print('  DuckDuckGo begränsar: väntar %d s' % vantan, flush=True)
            time.sleep(vantan)
        except (TimeoutException, DDGSException, Exception) as e:
            pf.logga(kampanj, 'sok_fel', fraga=fraga, fel=str(e)[:200])
            res = []
            break
    if res is None:
        raise Avbrott(4, 'DuckDuckGo begränsar sökningarna; försök senare')
    tok = namntoken(post.get('namn'))
    kandidater = []
    for r in res or []:
        href = r.get('href') or r.get('url') or ''
        host = doman(urllib.parse.urlsplit(href).hostname)
        if not host:
            continue
        if SOCIALA.search(host):
            k = 'facebook' if 'facebook' in host or host.startswith('fb.') else 'instagram' if 'instagram' in host else host
            kanaler.setdefault(k, href)
            continue
        if not slutdoman_ok(host):
            continue
        hay = (host + ' ' + (r.get('title') or '')).lower()
        kandidater.append((-sum(1 for t in tok if t in hay), href))
    kandidater.sort()
    ut = []
    for _, href in kandidater:
        if href not in ut:
            ut.append(href)
    return ut[:3]


def hitta_sajt(post, kampanj):
    """(bästa verifierade sajt eller None, näst bästa kandidat eller None, sökta frågor, kanaler)."""
    sokta, kanaler, basta, nast = [], dict(post.get('kanaler') or {}), None, None
    kandidater = []
    d = post.get('epost_doman')
    if d and d not in GENERISKA:
        kandidater += [('https://%s/' % d, 'epost'), ('https://www.%s/' % d, 'epost')]
    for url, kalla in kandidater:
        v = verifiera(url, post)
        if v and v['sakerhet'] >= 0.5:
            basta = dict(v, kalla=kalla)
            break
        if v and v['sakerhet'] >= 0.3 and not nast:
            nast = dict(v, kalla=kalla)
    if not basta:
        for url in sok_ddgs(post, kampanj, sokta, kanaler):
            v = verifiera(url, post)
            if not v:
                continue
            if v['sakerhet'] >= 0.5 and (not basta or v['sakerhet'] > basta['sakerhet']):
                basta = dict(v, kalla='ddgs')
            elif v['sakerhet'] >= 0.3 and (not nast or v['sakerhet'] > nast['sakerhet']):
                nast = dict(v, kalla='ddgs')
    return basta, nast, sokta, kanaler


def sajter(a):
    stopp()
    kdir = pf.kampanjkatalog(a.kampanj)
    pf.pagar_ta(kdir)
    try:
        poster = pf.las_register(a.kampanj)
        if a.slug and a.url:
            p = pf.hitta_post(poster, slug=a.slug)
            if not p:
                raise Avbrott(2, 'ingen post med slug %s' % a.slug)
            v = verifiera(a.url, p) or {'url': a.url, 'sakerhet': 0.0, 'titel': ''}
            sajt = {'url': v['url'], 'kalla': 'manuell', 'sakerhet': 1.0, 'verifierad_tid': nu(), 'titel': v.get('titel'), 'kontroll': v['sakerhet']}
            pf.satt_status(a.kampanj, a.slug, 'ny', sajt=sajt, sajt_kandidat=None)
            pf.logga(a.kampanj, 'sajt', slug=a.slug, url=v['url'], kalla='manuell')
            print('sajt satt för %s: %s' % (a.slug, v['url']))
            return 0
        urval = [p for p in poster if (p['status'] == 'ny' or (a.om and p['status'] == 'utan-sajt')) and not p.get('sajt')
                 and (not a.slug or p['slug'] == a.slug)]
        if not urval:
            print('inga poster att leta sajt åt (status ny utan sajt)')
            return 0
        n, hittade = 0, 0
        for p in urval[:a.max]:
            stopp()
            basta, nast, sokta, kanaler = hitta_sajt(p, a.kampanj)
            n += 1
            if basta:
                hittade += 1
                sajt = {'url': basta['url'], 'kalla': basta['kalla'], 'sakerhet': basta['sakerhet'], 'verifierad_tid': nu(), 'titel': basta.get('titel')}
                pf.satt_status(a.kampanj, p['slug'], 'ny', sajt=sajt, sajt_kandidat=None, kanaler=kanaler)
                pf.logga(a.kampanj, 'sajt', slug=p['slug'], url=sajt['url'], kalla=sajt['kalla'], sakerhet=sajt['sakerhet'])
                print('  %-40s %s (%s, %.2f)' % (p['slug'][:40], sajt['url'], sajt['kalla'], sajt['sakerhet']))
            elif nast:
                kand = {'url': nast['url'], 'kalla': nast['kalla'], 'sakerhet': nast['sakerhet'], 'titel': nast.get('titel'), 'sokt': sokta}
                pf.satt_status(a.kampanj, p['slug'], 'ny', sajt_kandidat=kand, kanaler=kanaler)
                pf.logga(a.kampanj, 'sajt_kandidat', slug=p['slug'], url=nast['url'], sakerhet=nast['sakerhet'])
                print('  %-40s kandidat att bekräfta: %s (%.2f)' % (p['slug'][:40], nast['url'], nast['sakerhet']))
            else:
                pf.satt_status(a.kampanj, p['slug'], 'utan-sajt', sajt={'url': None, 'kalla': 'ingen', 'sokt': sokta, 'tid': nu()}, kanaler=kanaler)
                pf.logga(a.kampanj, 'utan_sajt', slug=p['slug'], sokt=sokta)
                print('  %-40s ingen sajt hittad' % p['slug'][:40])
        print('sajter: %d prövade, %d hittade' % (n, hittade))
        return 0
    finally:
        pf.pagar_slapp(kdir)


# --- analysera ---

def sista_json(text):
    for rad in reversed((text or '').splitlines()):
        rad = rad.strip()
        if rad.startswith('{') and rad.endswith('}'):
            try:
                return json.loads(rad)
            except ValueError:
                continue
    return None


def sondera(url):
    """http→https, HSTS, server, senast ändrad, certifikatfel. Egna GET utan omdirigering först."""
    ut = {'https': None, 'http_till_https': None, 'hsts': None, 'cert_fel': None, 'server': None, 'x_powered_by': None, 'last_modified': None}
    host = urllib.parse.urlsplit(url).netloc

    class Ingen(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    try:
        r = urllib.request.build_opener(Ingen).open(urllib.request.Request('http://%s/' % host, headers={'User-Agent': hs.UA}), timeout=20)
        ut['http_till_https'] = False
        r.close()
    except urllib.error.HTTPError as e:
        loc = e.headers.get('Location') or ''
        ut['http_till_https'] = loc.lower().startswith('https://') if 300 <= e.code < 400 else False
    except Exception:
        ut['http_till_https'] = None
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': hs.UA}), timeout=20)
        ut['https'] = r.geturl().lower().startswith('https://')
        ut['hsts'] = bool(r.headers.get('Strict-Transport-Security'))
        ut['server'] = (r.headers.get('Server') or None)
        ut['x_powered_by'] = (r.headers.get('X-Powered-By') or None)
        ut['last_modified'] = (r.headers.get('Last-Modified') or None)
        ut['cert_fel'] = False
        r.close()
    except urllib.error.URLError as e:
        skal = str(getattr(e, 'reason', e)).upper()
        if 'CERTIFICATE' in skal or 'SSL' in skal:
            ut['cert_fel'], ut['https'] = True, False
    except Exception:
        pass
    return ut


def analysera_en(post, kampanj, vikter):
    slug, url = post['slug'], post['sajt']['url']
    bas = ROOT / 'underlag' / slug
    diagnos, kalla = bas / 'diagnos', bas / 'kalla'
    s = urllib.parse.urlsplit(url)
    origin = '%s://%s' % (s.scheme, s.netloc)
    startvag = s.path if s.path and s.path != '/' else '/'
    tider, fel = {}, {}
    pf.logga(kampanj, 'analys_start', slug=slug, url=url)
    t_alla = time.time()

    def steg(namn, cmd, timeout, krav=None):
        t = time.time()
        rc, out = prova.kor(cmd, cwd=str(ROOT), timeout=timeout)
        tider[namn] = round(time.time() - t)
        if rc in (2, 124, 127) or (krav and not Path(krav).is_file()):
            fel[namn] = ('rc %s: ' % rc) + (out or '')[-300:].strip()
        return rc, out

    sondering = sondera(url)
    rc, out = steg('hamta', [prova.PY, '-B', 'kontroller/hamta_sajt.py', url, '--ut', str(kalla), '--max', '8'], 120)
    hamtning = sista_json(out) or {}
    if not hamtning.get('sidor'):
        blockerad = hamtning.get('fel') and not hamtning.get('sidor')
        skal = 'blockerar hämtning' if blockerad else 'ingen sida kunde hämtas'
        pf.logga(kampanj, 'avvisad', slug=slug, skal=skal, fel=fel.get('hamta'))
        return {'status': 'avvisad', 'avvisad_skal': skal, 'tider': tider, 'verktygsfel': fel}
    sidor = [startvag]
    for x in hamtning.get('sidlista') or []:
        vag = urllib.parse.urlsplit(x.get('url') or '').path
        if vag and vag != startvag and SIDA_VIKTIG.search(vag):
            sidor.append(vag)
            break
    sidor_arg = ','.join(sidor)
    steg('lighthouse', [prova.NODE, 'kontroller/lighthouse.mjs', '--url=' + origin, '--sidor=' + sidor_arg, '--ut=' + str(diagnos / 'lighthouse'),
                        '--omgangar=1', '--enheter=mobil'], 240, krav=diagnos / 'lighthouse' / 'lighthouse.json')
    steg('inspektera', [prova.NODE, 'kontroller/webblasare/inspektera.mjs', '--adress', url, '--ut', str(diagnos / 'inspektion'), '--vyer', '390,1440',
                        '--tillat-alla'], 150, krav=diagnos / 'inspektion' / 'INSPEKTION.json')
    steg('stil', [prova.NODE, 'kontroller/stil.mjs', '--url=' + origin, '--sidor=' + startvag, '--ut=' + str(diagnos / 'stil')], 90, krav=diagnos / 'stil' / 'STIL.json')
    steg('axe', [prova.NODE, 'kontroller/axe.mjs', '--url=' + origin, '--sidor=' + sidor_arg, '--ut=' + str(diagnos / 'axe')], 150, krav=diagnos / 'axe' / 'axe.json')
    copy, seof = [], []
    dom = doman(s.hostname)
    for f in sorted(kalla.glob('*.html')):
        rå = f.read_text(encoding='utf-8', errors='replace')
        try:
            fynd, _ = ck.kontrollera_fil(f, rå, [])
            copy.append({'sida': f.name, 'fynd': fynd})
        except Exception as e:
            fel['copy'] = str(e)[:200]
        try:
            r = seo.granska_sida(kalla, f, rå, 'lansering', None, dom)
            r['fynd'] = [x for x in r.get('fynd') or [] if not str(x.get('typ', '')).startswith(('intern länk', 'noindex kvar'))]
            seof.append(r)
        except Exception as e:
            fel['seo'] = str(e)[:200]
    diagnos.mkdir(parents=True, exist_ok=True)
    pf.skriv_json(diagnos / 'copy.json', {'schema': 1, 'verktyg': 'copy_kontroll', 'tid': nu(), 'sidor': copy})
    pf.skriv_json(diagnos / 'seo.json', {'schema': 1, 'verktyg': 'seo_kontroll', 'tid': nu(), 'lage': 'lansering', 'sidor': seof})
    hamtning_sparad = {k: hamtning.get(k) for k in ('sidor', 'bilder', 'kvar', 'nekade', 'fel', 'robots', 'sidkarta', 'generator', 'sidlista')}
    sig = pp.signaler(diagnos, kalla, sondering, hamtning_sparad)
    res = pp.poang(sig, vikter)
    underlag = {k: sig.get(k) for k in ('bilder_antal', 'orgnr_pa_sajt', 'generator', 'stackpack', 'jquery_version', 'copyright_ar', 'https',
                                        'http_till_https', 'hsts', 'cert_fel', 'server', 'last_modified', 'viewport_meta', 'karusell', 'cookie_banner',
                                        'formular_antal', 'soft_404', 'sidor_hamtade', 'sprak', 'konsolfel', 'natverksfel', 'tredjeparter', 'sidkarta_saknas')}
    underlag['tel_scb'] = post.get('tel')
    underlag['kanaler'] = post.get('kanaler') or {}
    underlag['sidor'] = sidor
    tider['totalt'] = round(time.time() - t_alla)
    prospekt = {'schema': 1, 'slug': slug, 'peOrgNr': post.get('peOrgNr'), 'namn': post.get('namn'), 'sajt': post['sajt'], 'poang': res['poang'],
                'varfor': res['varfor'], 'signaler': sig, 'underlag': underlag, 'tider': tider, 'verktygsfel': fel, 'sondering': sondering,
                'hamtning': hamtning_sparad, 'analys_tid': nu()}
    pf.skriv_json(bas / 'PROSPEKT.json', prospekt)
    pf.logga(kampanj, 'analys_klar', slug=slug, sekunder=tider['totalt'], total=res['poang'].get('total'), fel=sorted(fel))
    return {'status': 'analyserad', 'poang': res['poang'], 'analys_tid': prospekt['analys_tid'], 'tider': tider, 'verktygsfel': fel}


def analysera(a):
    stopp()
    kdir = pf.kampanjkatalog(a.kampanj)
    pf.pagar_ta(kdir)
    try:
        poster = pf.las_register(a.kampanj)
        urval = [p for p in poster if (p['status'] == 'ny' or (a.om and p['status'] == 'analyserad')) and (p.get('sajt') or {}).get('url')
                 and (not a.slug or p['slug'] == a.slug)]
        if not urval:
            print('inga poster att analysera (status ny med sajt)')
            return 0
        vikter = pf.las_json(pp.VIKTER) or {}
        for i, p in enumerate(urval[:a.max]):
            if i:
                time.sleep(PAUS)
            stopp()
            print('%s %s' % (p['slug'], p['sajt']['url']), flush=True)
            r = analysera_en(p, a.kampanj, vikter)
            falt = {k: v for k, v in r.items() if k in ('poang', 'analys_tid', 'avvisad_skal')}
            pf.satt_status(a.kampanj, p['slug'], r['status'], **falt)
            if r['status'] == 'analyserad':
                po = r['poang']
                print('  H %s  S %s  M %s  D %s  → att vinna %s (%d s%s)' % (po.get('hastighet'), po.get('seo'), po.get('mobil'), po.get('design'),
                      po.get('total'), r['tider'].get('totalt', 0), '; fel: ' + ', '.join(sorted(r['verktygsfel'])) if r['verktygsfel'] else ''))
            else:
                print('  avvisad: %s' % r.get('avvisad_skal'))
        return 0
    finally:
        pf.pagar_slapp(kdir)


def poangsatt(a):
    vikter = pf.las_json(pp.VIKTER) or {}
    poster = pf.las_register(a.kampanj)
    n = 0
    for p in poster:
        if not p.get('analys_tid') or (a.slug and p['slug'] != a.slug):
            continue
        bas = ROOT / 'underlag' / p['slug']
        pr = pf.las_json(bas / 'PROSPEKT.json') or {}
        sig = pp.signaler(bas / 'diagnos', bas / 'kalla', pr.get('sondering'), pr.get('hamtning'))
        res = pp.poang(sig, vikter)
        pr.update({'poang': res['poang'], 'varfor': res['varfor'], 'signaler': sig, 'poang_tid': nu()})
        pf.skriv_json(bas / 'PROSPEKT.json', pr)
        pf.satt_status(a.kampanj, p['slug'], p['status'], poang=res['poang'])
        n += 1
    print('poäng räknade om för %d prospekt (vikter version %s)' % (n, vikter.get('version')))
    return 0


def lista(a):
    poster = pf.las_register(a.kampanj)
    if not poster:
        print('tomt register')
        return 0
    med = [p for p in poster if (p.get('poang') or {}).get('total') is not None]
    med.sort(key=lambda p: -(p['poang']['total']))
    print('%-32s %-14s %-6s %-6s %-6s %-6s %-6s %-10s %s' % ('slug', 'ort', 'H', 'S', 'M', 'D', 'vinna', 'status', 'sajt'))
    for p in med:
        po = p['poang']
        print('%-32s %-14s %-6s %-6s %-6s %-6s %-6s %-10s %s' % (p['slug'][:32], (p.get('postort') or '')[:14], po.get('hastighet'), po.get('seo'),
                                                              po.get('mobil'), po.get('design'), po.get('total'), p['status'], (p.get('sajt') or {}).get('url') or ''))
    ovriga = [p for p in poster if p not in med]
    grupp = {}
    for p in ovriga:
        grupp.setdefault(p['status'], []).append(p)
    for st, g in sorted(grupp.items()):
        print('\n%s (%d):' % (st, len(g)))
        for p in sorted(g, key=lambda p: (-(int(p.get('anstKl') or 0) if str(p.get('anstKl') or '').isdigit() else 0), p.get('startDat') or ''))[:40]:
            print('  %-32s %-14s %-24s %s' % (p['slug'][:32], (p.get('postort') or '')[:14], (p.get('jurform_text') or '')[:24], (p.get('sajt') or {}).get('url') or (p.get('sajt_kandidat') or {}).get('url', '') or ''))
    return 0


def gallra(a):
    grans = (datetime.now(timezone.utc) - timedelta(days=30 * a.manader)).strftime('%Y-%m-%dT%H:%M:%SZ')
    behall = {'vald', 'demo', 'utkast', 'skickat', 'svar', 'kund'}
    kampanjer = [a.kampanj] if a.kampanj else [k['id'] for k in pf.kampanjer()]
    for kid in kampanjer:
        bort, krympta = [], []

        def mut(poster):
            kvar = []
            for p in poster:
                if (p.get('uppdaterad') or p.get('skapad') or '') < grans and p.get('status') not in behall:
                    if p.get('status') in ('nej', 'avvisad'):
                        krympta.append(p['slug'])
                        kvar.append({'slug': p['slug'], 'peOrgNr': p.get('peOrgNr'), 'status': p['status'], 'uppdaterad': p.get('uppdaterad'), 'gallrad': nu()})
                    else:
                        bort.append(p['slug'])
                else:
                    kvar.append(p)
            return kvar
        if a.torr:
            poster = pf.las_register(kid)
            mut(poster)
        else:
            pf.skriv_register(kid, mut)
        for slug in bort + krympta:
            d = ROOT / 'underlag' / slug
            if d.is_dir() and not (ROOT / 'kunder' / slug).exists():
                if not a.torr:
                    shutil.rmtree(d, ignore_errors=True)
            if not a.torr:
                pf.logga(kid, 'gallrad', slug=slug)
        print('%s: %d borttagna, %d krympta%s' % (kid, len(bort), len(krympta), ' (torrkörning)' if a.torr else ''))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog='prospekt', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='kommando', required=True)
    s = sub.add_parser('svep', help='hämta verksamheter i kommun och bransch ur SCB')
    s.add_argument('--kampanj', required=True)
    s.add_argument('--kommun', required=True, help='kommunkod, t.ex. 2580')
    s.add_argument('--bransch', required=True, help='nyckel i kunskap/prospekt-branscher.json')
    s.add_argument('--kommun-namn', dest='kommun_namn')
    s.add_argument('--om', action='store_true', help='svep om från början')
    s = sub.add_parser('sajter', help='leta upp verksamheternas webbplatser')
    s.add_argument('--kampanj', required=True)
    s.add_argument('--max', type=int, default=40)
    s.add_argument('--slug')
    s.add_argument('--url', help='sätt sajten för --slug manuellt')
    s.add_argument('--om', action='store_true', help='pröva också poster utan sajt igen')
    s = sub.add_parser('analysera', help='mät sajterna och sätt poäng')
    s.add_argument('--kampanj', required=True)
    s.add_argument('--max', type=int, default=10)
    s.add_argument('--slug')
    s.add_argument('--om', action='store_true', help='mät om redan analyserade')
    s = sub.add_parser('poangsatt', help='räkna om poängen ur sparade mätningar')
    s.add_argument('--kampanj', required=True)
    s.add_argument('--slug')
    s = sub.add_parser('lista', help='visa registret')
    s.add_argument('--kampanj', required=True)
    s = sub.add_parser('gallra', help='ta bort gamla poster')
    s.add_argument('--kampanj')
    s.add_argument('--manader', type=int, default=GALLRING)
    s.add_argument('--torr', action='store_true')
    a = p.parse_args(argv)
    try:
        return {'svep': svep, 'sajter': sajter, 'analysera': analysera, 'poangsatt': poangsatt, 'lista': lista, 'gallra': gallra}[a.kommando](a)
    except Avbrott as e:
        print('avbrutet: %s' % e.text, file=sys.stderr)
        return e.kod
    except ValueError as e:
        print('fel: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
