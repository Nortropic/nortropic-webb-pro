#!/usr/bin/env python3
"""kandidater.py — skapandeflödets utforskning i många kandidater, med ägarens val före förfiningen (ägarens uppdrag via
Codex 2026-10-05: cirka tio genomarbetade prototyper med kundens riktiga information; ägaren väljer vilken eller vilka
som utvecklas vidare; panelen granskar och rekommenderar men utser ingen vinnare).

Skissläget är standard (ägarens uppdrag 2026-10-05 16:25Z, "full verktygslåda, ren arbetsbänk"): första omgången ger
cirka tio skisser (första vyn, den viktigaste innehållssektionen, navigationen och interaktionerna som behövs för att
förstå förslaget, mobil och dator). Varje skapare får en ren arbetskontext: uppdraget, kundens verifierade fakta och
material, referensbilderna och metodens kärna (kvalitetskraven, besluten med räckvidd, avgörandena) med en förteckning
att slå upp i; historiken slås upp vid behov. Högst tre samtidigt, 30 minuter per inledande försök med verktygsväntan,
ett omförsök bara vid ett identifierat tekniskt fel, inget minimiantal varv. Ingen granskningspanel och ingen
förbättringsrunda före ägarens val: snabba objektiva kontroller (bygget, konsolen, spill, axe, siffror utan belägg,
menyn) markerar brister. Fördjupningen (hela startsidan, undersidan och besökarens centrala flöde, DESIGN.md) kommer
efter ägarens val. NWP_KANDIDATLAGE=full är en tillfällig växel till förvalet nedan, för jämförelse och återställning.

Varje kandidat har en stabil identitet (k01–k12) och
- ett eget litet Astro-projekt, kunder/<slug>/kandidater/<id>/sajt, med sajtens nuvarande src/ och public/ utan
  tidigare sidor, kundens bilder och node_modules som länk till sajtens, så att skaparna inte bygger i varandras sidor;
- en egen katalog i ateljén, underlag/<slug>/atelje/kandidater/<id>/: UPPDRAG.md (designuppdraget ur planen),
  RIKTNING.md (skaparens anteckningar), STATUS.json, kod/, DESIGN.md och bilder/ (den version ägaren ser), varv/
  (förhandsvarven), versioner/<v12>/ (bevarade versioner), KRITIK.json (rådgivande, dold vid första presentationen);
- en version: hashen över kod/ och DESIGN.md, det som formger sidan. Bilderna tas ur den; ägarens val binds till den.

Stegen (kor): metoden levereras (kontroller/metod.py: stegens utdrag ur kunskap/metodkarta.md, med hash) → forska
(frågor till Refero och Mobbin, nya sajter och antaganden om besökarna som kan ändra designen) → planera (uppdrag med
hypotes, referensens kvalitet och vad den kräver) → per kandidat, några åt gången: skapa → fotografera (bygge innanför
processgränsen, bilder i 390, 768 och 1440, axe) → granskning i två pass (först bilderna mot besökarens uppgift utan
skaparens motivering, sedan motiveringen) → en förbättringsrunda bara för objektiva fel → granskning igen → jämföra
(falsk variation) → klar för ägarens bedömning. Ett andra skaparförsök ges en ofullständig kandidat. Efter ägarens val
(domloggen, beslut valj): forfina_valda förfinar varje vald kandidat för sig; ägaren godkänner sedan en för helbygget.
Ett avbrott förstör inga klara kandidater: varje halvgjord förbättring eller förfining är märkt med sin föreversion och
återställs vid återupptagningen.

    .venv/bin/python kontroller/kandidater.py <slug> --status
    .venv/bin/python kontroller/kandidater.py <slug> --fotografera kNN     (om, utan session)

Körs annars av kontroller/atelje.py (prototyp.py), som skriver körningens STATUS.json.
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402  session, saker_vag, egna_bilder, NEKAS, ROOT/UNDERLAG/KUNDER
import bildkedja  # noqa: E402
import forhandsvisa  # noqa: E402
import kompetens  # noqa: E402  kompetenserna per pass (kunskap/metodkarta.md, Kompetenserna)
import metod  # noqa: E402
import prova  # noqa: E402
import referensval  # noqa: E402
import skapande  # noqa: E402

KOD = Path(__file__).resolve().parents[1]  # kunskap/ och kritik/ hör till koden, inte till kundens data
ID = re.compile(r'^k\d{2}$')
ANTAL = max(2, min(12, int(os.environ.get('NWP_KANDIDATER') or 10)))
PARALLELLT = max(1, min(5, int(os.environ.get('NWP_KANDIDATER_PARALLELLT') or 3)))
FRIST_SKAPA = int(os.environ.get('NWP_KANDIDAT_FRIST') or 6000)  # en kandidat per session: 100 minuter, varven inräknade
FRIST_FORBATTRA = int(os.environ.get('NWP_KANDIDAT_FRIST_FORBATTRA') or 2700)
FRIST_PLAN = int(os.environ.get('NWP_KANDIDAT_FRIST_PLAN') or 3000)
FRIST_GRANSKA = int(os.environ.get('NWP_KANDIDAT_FRIST_GRANSKA') or 1800)
FRIST_FORSKA = int(os.environ.get('NWP_KANDIDAT_FRIST_FORSKA') or 2400)  # researchpasset (sessionen)
FRIST_HAMTA = int(os.environ.get('NWP_KANDIDAT_FRIST_HAMTA') or 5400)  # referenssteget och tjänsterna, var för sig
FRIST_FORFINA = int(os.environ.get('NWP_KANDIDAT_FRIST_FORFINA') or 5400)
GRANSKARE_MODELL = os.environ.get('NWP_KANDIDAT_GRANSKARE') or 'claude-sonnet-5-5[1m]'
MAX_FORSOK = 2  # skaparsessioner per kandidat i en körning: en ofullständig kandidat får ett andra försök med bristerna
MIN_VARV = 3  # arbetsregel i läget full: varvens antal är ingen kvalitetsbedömning (granskningen och ägaren bedömer kvaliteten)
# skissläget (standard) och en tillfällig växel till förvalet med granskning och förbättringsrunda (läget full), för
# jämförelse och återställning; växeln tas bort när ägaren dömt skissläget (BESLUT.md 2026-10-05, kväll)
LAGE = 'full' if os.environ.get('NWP_KANDIDATLAGE') == 'full' else 'skiss'  # bara skiss och full (granskning 3, S13)
FRIST_SKISS = int(os.environ.get('NWP_KANDIDAT_FRIST_SKISS') or 1800)  # ett inledande skaparförsök, verktygsväntan inräknad
FRIST_SKISS_OMFORSOK = int(os.environ.get('NWP_KANDIDAT_FRIST_OMFORSOK') or 900)  # ett omförsök efter ett identifierat tekniskt fel
FRIST_SKISS_FORSKA = int(os.environ.get('NWP_KANDIDAT_FRIST_SKISS_FORSKA') or 1200)
MAX_FORSOK_SKISS = 2  # det inledande försöket och ett omförsök (tekniskt fel eller avbrott); ingen förlängning för antalets skull
MAX_PARALLELLT_SKISS = 3  # högst tre skisser samtidigt (ägarens försöksbudget 2026-10-05)
EFFORT_SKISS = os.environ.get('NWP_KANDIDAT_EFFORT') or 'high'
MENYKNAPP = 'button[aria-expanded]'  # menyns knapp i skissens snabba kontroll (inspektera.mjs --meny)
FOTO_RESERV = 180  # sekunder av försökets tid för fotograferingen och kontrollerna efter sessionen
KOMPETENSPASS = ('rorelse', 'granskning')  # efter fördjupningen, en gång var och i den ordningen; inga redigerande pass före ägarens val (Codex via ägaren 2026-10-05, punkt 8)
FRIST_PASS = int(os.environ.get('NWP_KANDIDAT_FRIST_PASS') or 720)  # ett kompetenspass: läsningen, en omgång och en bekräftelse
FRIST_PASS_OMFORSOK = 420  # ett pass som inte läste sina filer får ett omförsök
PASSBILDER = ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png')
# kandidatens status, i ägarens ord (uppdraget punkt 9): en prototyp ägaren vill utveckla vidare är inte godkänd för leverans
STATUSTEXT = {'planerad': 'planerad', 'under_arbete': 'under arbete', 'klar': 'klar för ägarens bedömning',
              'ofullstandig': 'ofullständig', 'avbruten': 'avbruten', 'fel': 'föll', 'vald': 'vald för vidareutveckling',
              'jamfors': 'vald för jämförelse', 'forkastad': 'förkastad', 'forfinad': 'förfinad', 'godkand': 'godkänd för helbygge'}
VISBARA = ('klar', 'vald', 'jamfors', 'forkastad', 'forfinad', 'godkand')  # kandidater ägaren kan bedöma
MALLSIDOR = {'404.astro', 'tack.astro', 'fel.astro', 'robots.txt.ts', 'sitemap.xml.ts'}
# flödets sessioner läser skillsen med Read enligt kunskap/metodkarta.md: Skill-verktyget går inte att begränsa till
# namngivna skills, och flera bär processinstruktioner för en interaktiv session (mikroprovet 2026-10-05)
LASVERKTYG = ['Read', 'Glob', 'Grep']
MALL_DESIGN_CSS = KOD / 'mall' / 'astro' / 'src' / 'styles' / 'design.css'


def nu():
    return atelje.nu()


def rot(slug):
    return atelje.UNDERLAG / slug / 'atelje'


def kdir(slug, kid):
    return rot(slug) / 'kandidater' / kid


def ksajt(slug, kid):
    return atelje.KUNDER / slug / 'kandidater' / kid / 'sajt'


def metodkatalog(slug):
    return rot(slug) / 'metod'


def rel(p):
    return atelje.rel(p)


def lista(slug):
    d = rot(slug) / 'kandidater'
    return sorted(p.name for p in d.iterdir() if p.is_dir() and not p.is_symlink() and ID.fullmatch(p.name)) if d.is_dir() else []


def las_status(slug, kid):
    return atelje.las_json(kdir(slug, kid) / 'STATUS.json') or {}


def satt_status(slug, kid, status, skal='', ta_bort=(), **extra):
    """Kandidatens status, atomiskt, med en logg över övergångarna. ta_bort: fält som inte längre gäller."""
    assert status in STATUSTEXT, status
    d = kdir(slug, kid)
    atelje.saker_vag(d, rot(slug))
    d.mkdir(parents=True, exist_ok=True)
    st = las_status(slug, kid)
    for f in ta_bort:
        st.pop(f, None)
    logg = list(st.get('logg') or [])[-40:] + [{'tid': nu(), 'status': status, 'skal': str(skal)[:400]}]
    st.update(extra, id=kid, status=status, skal=str(skal)[:1000], tid=nu(), logg=logg)
    tmp = d / '.STATUS.json.tmp'
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, d / 'STATUS.json')
    return st


KODSRC = 'kod-src'  # projektets src/ utom sidorna och kundens bilder: komponenter, layouter, stilar och egna tillgångar


def src_ovrigt(relp):
    """Hör filen (relativt src/) till kod-src/? Sidorna står i kod/, och kundens bilder (assets/atelje/) kopieras ur
    underlaget och är desamma i varje version (Codex via ägaren 2026-10-05, punkt 5: skaparen arbetar i hela projektets
    källkataloger)."""
    return relp.parts[:1] != ('pages',) and relp.parts[:2] != ('assets', 'atelje')


def version(slug, kid):
    """Hashen över det som formger kandidaten: kod/, kod-src/ och DESIGN.md (inga länkar följs). Bilderna tas ur den, så
    en ny fotografering av samma kod ger samma version. En version utan kod-src/ (före 2026-10-05) får samma hash som förut."""
    h = hashlib.sha256()
    d = kdir(slug, kid)
    if (d / 'DESIGN.md').is_file() and not (d / 'DESIGN.md').is_symlink():
        h.update(b'DESIGN.md\0' + (d / 'DESIGN.md').read_bytes() + b'\0')
    for bas in (d / 'kod', d / KODSRC):
        if not bas.is_dir() or bas.is_symlink():
            continue
        for katalog, kataloger, filer in os.walk(bas, followlinks=False):
            kataloger.sort()
            for fn in sorted(filer):
                p = Path(katalog) / fn
                if p.is_symlink() or not p.is_file():
                    continue
                h.update(str(p.relative_to(d)).encode() + b'\0' + p.read_bytes() + b'\0')
    return h.hexdigest()


def korlage(slug, status=None):
    """Körningens läge: planens (en återupptagning följer körningen, inte miljön), annars statusens, annars LAGE."""
    plan = atelje.las_json(rot(slug) / 'KANDIDATPLAN.json')
    if isinstance(plan, dict):  # en plan utan läge skrevs före skissläget: läget full
        return 'skiss' if plan.get('lage') == 'skiss' else 'full'
    return 'skiss' if ((status or {}).get('kandidatlage') or LAGE) == 'skiss' else 'full'


def plan_tid(slug):
    return str((atelje.las_json(rot(slug) / 'KANDIDATPLAN.json') or {}).get('tid') or '')


def etiketter(slug, ids, fro=None):
    """Neutral märkning för ägaren: bokstäver i en ordning som inte följer planens (ingen ordning som favoriserar).
    Fröet är planens tid, så att en kandidat behåller sin bokstav genom förfiningen."""
    blandade = list(ids)
    random.Random('%s-%s' % (slug, fro if fro is not None else plan_tid(slug))).shuffle(blandade)
    return {kid: 'Förslag %s' % 'ABCDEFGHIJKL'[i] for i, kid in enumerate(blandade)}


def kopiera(kalla, mal, ta_med=None):
    """Filerna under kalla till mal, utan att följa eller kopiera någon länk (en länkad fil eller katalog hoppas över).
    ta_med(relativ väg) avgör vilka som följer med. Ger {relativ väg: sha256}."""
    ut = {}
    kalla, mal = Path(kalla), Path(mal)
    for katalog, kataloger, filer in os.walk(kalla, followlinks=False):
        kataloger[:] = sorted(k for k in kataloger if not (Path(katalog) / k).is_symlink())
        for fn in sorted(filer):
            p_ = Path(katalog) / fn
            relp = p_.relative_to(kalla)
            if p_.is_symlink() or not p_.is_file() or (ta_med and not ta_med(relp)):
                continue
            m = mal / relp
            m.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p_, m)
            ut[relp.as_posix()] = atelje.sha256_fil(m)
    return ut


# --- projektet per kandidat ---

def forbered_projekt(slug, kid):
    """Kandidatens eget Astro-projekt ur sajtens nuvarande src/ och public/ (mallen, och det ett tidigare bygge lagt dit):
    konfigurationen, komponenterna och mallens egna sidor, inga tidigare sidor; kundens bilder i src/assets/atelje/ och
    node_modules som länk till sajtens. Ingen länk följs (en planterad länk blir aldrig en vanlig kopia här). Ett
    befintligt projekt lämnas orört (återupptagning)."""
    huvud = atelje.KUNDER / slug / 'sajt'
    mal = ksajt(slug, kid)
    atelje.saker_vag(mal.parent, atelje.KUNDER / slug)
    if (mal / 'package.json').is_file():
        return mal
    if not (huvud / 'package.json').is_file() or not (huvud / 'node_modules').is_dir():
        raise RuntimeError('kunder/%s/sajt saknas eller saknar node_modules: kör kontroller/ny_sajt.py %s --installera' % (slug, slug))
    atelje.saker_vag(huvud, atelje.KUNDER / slug)
    mal.mkdir(parents=True, exist_ok=True)
    for namn in ('package.json', 'astro.config.mjs', 'tsconfig.json'):
        if (huvud / namn).is_file() and not (huvud / namn).is_symlink():
            shutil.copyfile(huvud / namn, mal / namn)

    def ta_med(relp):  # bara mallens egna sidor, inga ateljésidor eller tidigare startsidor och undersidor
        if relp.parts[:1] == ('pages',):
            return len(relp.parts) == 2 and relp.parts[1] in MALLSIDOR
        return not any(x.startswith('atelje-') for x in relp.parts)
    for under in ('src', 'public'):
        if (huvud / under).is_dir() and not (huvud / under).is_symlink():
            kopiera(huvud / under, mal / under, ta_med if under == 'src' else None)
    assets = mal / 'src' / 'assets' / 'atelje'
    assets.mkdir(parents=True, exist_ok=True)
    for namn in atelje.egna_bilder(slug):
        kalla = atelje.UNDERLAG / slug / 'bilder' / namn
        if not (assets / namn).exists() and kalla.is_file() and not kalla.is_symlink():
            shutil.copyfile(kalla, assets / namn)
    os.symlink(os.path.realpath(huvud / 'node_modules'), mal / 'node_modules')
    return mal


def undersidor(slug, kid):
    """Kandidatens egna sidor utöver startsidan: vägarna (/projekt/dalbo/ …) till index.astro i katalogerna under pages."""
    pages = ksajt(slug, kid) / 'src' / 'pages'
    ut = []
    for p in sorted(pages.rglob('index.astro')) if pages.is_dir() else []:
        relp = p.relative_to(pages)
        if len(relp.parts) > 1 and not p.is_symlink():
            ut.append('/' + '/'.join(relp.parts[:-1]) + '/')
    return ut


def andra_nekas(slug, kid, utom=()):
    """Read-förbud för de andra kandidaternas kataloger: skaparna ser inte varandras kod (förfiningen får läsa dem ägaren
    gillade delar ur). Och skrivförbud för kundens bilder i det egna projektet (src/assets/atelje/): skaparen arbetar i
    hela src/, men kundens original ändras aldrig (kvalitetskravet äkthet)."""
    egna = 'kunder/%s/kandidater/%s/sajt/src/assets/atelje/**' % (slug, kid)
    ut = ['Write(./%s)' % egna, 'Edit(./%s)' % egna]
    for annan in lista(slug):
        if annan != kid and annan not in utom:
            ut += ['Read(./kunder/%s/kandidater/%s/**)' % (slug, annan), 'Read(./underlag/%s/atelje/kandidater/%s/**)' % (slug, annan)]
    return ut


def nekas_utom(katalog, utom):
    """Read-förbud för allt i katalogen utom de namngivna posterna: granskningens första pass ser bilderna men inte
    uppdraget, planen, statusen (hypotesen, huvudreferensen), skaparens svar eller förra granskningens motiveringar
    (granskning 2, N9). Ett förbud går före en tillåtelse, så det som får läsas lämnas utanför förbuden."""
    ut = []
    for p in sorted(katalog.iterdir()) if katalog.is_dir() else []:
        if p.name not in utom:
            ut.append(('Read(./%s/**)' if p.is_dir() and not p.is_symlink() else 'Read(./%s)') % rel(p))
    return ut


# --- metoden: kartans utdrag per steg, levererade och versionsbundna (kontroller/metod.py) ---

METODSTEG = metod.STEG


def leverera_metod(slug):
    """Stegens metodfiler i atelje/metod/ (en gång per körning) och deras hashar. MetodFel stoppar körningen."""
    k = metodkatalog(slug)
    atelje.saker_vag(k, rot(slug))
    ut = {}
    for steg in ('forska', 'plan', 'skapa', 'skiss', 'granska', 'forfina'):
        res = metod.leverera(steg, k)
        ut[steg] = {'sha': res['sha'], 'filer': [rel(f['fil']) for f in res['filer']], 'karta': res['karta'],
                    'delar': {d: [rel(f['fil']) for f in res['filer'] if f['del'] == d] for d in ('före', 'varv', 'text', 'uppslag')}}
    (k / 'METOD.json').write_text(json.dumps({'tid': nu(), 'steg': ut}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return ut


def metodinfo(slug, steg):
    """{'sha', 'filer'} för stegets levererade metod (levereras nu om den saknas)."""
    m = (atelje.las_json(metodkatalog(slug) / 'METOD.json') or {}).get('steg') or {}
    if steg not in m or 'uppslag' not in (m[steg].get('delar') or {}) or not all((atelje.ROOT / f).is_file() for f in m[steg]['filer']):
        m = leverera_metod(slug)
    return m[steg]


def metod_rader(slug, steg):
    """Metoden för steget: de levererade filerna ur metodkartan (kartans text, avgörandena och utdragen med källa och
    hash). Före-filen är kärnan och läses före första ändringen; varv- och textfilerna där kartan har dem; uppslaget
    (utdragen ur skills och kunskapsfiler i förteckningen) slås upp när uppgiften behöver det, inget krav på att allt
    läses (ägarens uppdrag 2026-10-05 16:25Z, punkt 3)."""
    m = metodinfo(slug, steg)
    d = m['delar']
    rader = ['Metoden (kunskap/metodkarta.md, levererad med hash %s): läs %s före första ändringen, varje fil hel i ett Read'
             % (m['sha'][:12], ', '.join(d['före'])), '(utan offset och limit; varje fil ryms i en läsning).']
    if d.get('varv'):
        rader.append('Läs %s när varven börjar, och slå upp i dem i varje varv.' % ', '.join(d['varv']))
    if d.get('text'):
        rader.append('Läs %s när du skriver eller bearbetar rubriker och text.' % ', '.join(d['text']))
    if d.get('uppslag'):
        rader.append('Utdragen ur skills och kunskapsfiler står i förteckningen i %s och i %s; slå upp det uppgiften behöver.'
                     % (Path(d['före'][0]).name, ', '.join(Path(x).name for x in d['uppslag'])))
    rader.append('Där en skill säger emot kartan, ett kvalitetskrav, kundens behov eller ägarens beslut gäller kartan.')
    return rader


def historik_rader(slug):
    """Historiken slås upp, den läses inte i förväg (ägarens uppdrag 2026-10-05 16:25Z, punkt 2): ägarens domar över
    tidigare byggen, kundens äldre domar och riktningshistoriken är exempel och smakdomar, inga regler."""
    u = rel(atelje.UNDERLAG / slug)
    return ['Historiken slås upp, den läses inte i förväg: ägarens domar över tidigare byggen (LARDOMAR.md), kundens äldre',
            'domar (%s/%s) och prövade grundidéer (%s/%s) är exempel och smakdomar, inga regler; de aktuella besluten står' % (
                u, skapande.DOMLOGG, u, skapande.HISTORIK),
            'med räckvidd i kunskap/designregler.md. Öppna historiken när den besvarar en konkret fråga.']


def regel_rader():
    return ['Reglerna i fyra slag med räckvidd (kunskap/designregler.md): gemensamma kvalitetskrav, Nortropics produkt- och',
            'ägarbeslut, kundens behov ur underlaget och designhypoteser som prövas. Läs den.']


# --- researchen ---

FORSKA_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['varfor', 'riktningar', 'antaganden', 'sajter', 'fragor'],
    'properties': {
        'varfor': {'type': 'string'}, 'riktningar': {'type': 'string'},
        'antaganden': {'type': 'array', 'maxItems': 8, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['antagande', 'underlag', 'provning', 'om_fel'],
            'properties': {'antagande': {'type': 'string'}, 'underlag': {'type': 'string'}, 'provning': {'type': 'string'}, 'om_fel': {'type': 'string'}}}},
        'sajter': {'type': 'array', 'maxItems': skapande.MAX_KANDIDATER_BRED, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['namn', 'adress', 'roll', 'varfor', 'sidor'],
            'properties': {'namn': {'type': 'string'}, 'adress': {'type': 'string'}, 'roll': {'type': 'string', 'enum': ['bransch', 'hantverk', 'ux']},
                           'varfor': {'type': 'string'}, 'sidor': {'type': 'array', 'maxItems': skapande.MAX_SIDOR_PER, 'items': {'type': 'string'}}}}},
        'fragor': {'type': 'array', 'minItems': 4, 'maxItems': skapande.MAX_FRAGOR_BRED, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['tjanst', 'fraga', 'syfte', 'typ'],
            'properties': {'tjanst': {'type': 'string', 'enum': ['refero', 'mobbin']}, 'fraga': {'type': 'string'}, 'syfte': {'type': 'string'},
                           'typ': {'type': 'string', 'enum': ['stil', 'skarm', 'flode']}}}}}}


FORSKA_SCHEMA_SKISS = json.loads(json.dumps(FORSKA_SCHEMA))  # skissläget: nytt bara där materialet saknar något
FORSKA_SCHEMA_SKISS['properties']['fragor'].update(minItems=0, maxItems=6)
FORSKA_SCHEMA_SKISS['properties']['sajter']['maxItems'] = 4


def forska_prompt(slug, n, fel=None, skiss=False):
    filer, _refs, _fel = atelje.underlag_rader(slug)
    return '\n'.join([
        'Du planerar researchen före skapandeflödets utforskning för en riktig verksamhet. Ägaren vill se cirka %d verkligt' % n,
        ('olika skisser (första vyn och den viktigaste sektionen, mobil och dator) med kundens riktiga information. Researchen'
         if skiss else 'olika, genomarbetade prototyper med kundens riktiga information. Researchen'),
        'ska ge material för så många skilda grundidéer: hur jämförbara verksamheter och goda webbplatser berättar, prioriterar',
        'och organiserar innehåll, och hur de löser projekt, tjänster, förtroende och kontakt, på mobilen och datorn.', '',
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG, aktuella=True), '',
        *skapande.fakta_rader(slug, atelje.UNDERLAG), '',
        'Läs först: ' + ', '.join(filer) + '.',
        *historik_rader(slug), *regel_rader(), *metod_rader(slug, 'forska'), '',
        *research_rader(slug), '',
        *(['Återanvänd researchen som finns (referenspaketet och tjänsternas rapport ovan). Föreslå sajter och frågor bara',
           'där materialet saknar något som planen behöver för skilda grundidéer: högst 4 sajter och 6 frågor, annars tomma',
           'listor. Varje hämtning förlänger ägarens väntan.', ''] if skiss else []),
        'Svara med tre delar:',
        '- antaganden: 3–6 antaganden om besökarna som kan ändra designbesluten, ur briefens målgrupper, toppuppgifter och',
        '  insiktskällor (BRIEF.md §2 och "Antaganden som behöver bekräftas"). För vart och ett: vilket underlag som stöder det',
        '  (eller "ännu inte observerat"), hur det prövas (en uppgift som beskriver besökarens mål utan att avslöja knappen, eller',
        '  befintliga data), och vad vi ändrar om det inte stämmer. Exempel: besökaren behöver bedöma tidigare arbeten före kontakt.',
        '- fragor: %d–%d frågor till Refero och Mobbin, på engelska, var och en högst %d tecken (fraga och syfte), utan' % (
            ((0, 6) if skiss else (4, skapande.MAX_FRAGOR_BRED)) + (skapande.MAX_FRAGA,)),
        '  adresser, kundens namn, orter eller andra uppgifter ur underlaget, och utan långa sifferföljder. Täck bredden:',
        '  Referos stilar (typ stil) i flera skilda estetiska territorier; skärmar (typ skarm) för startsidans första vy på mobil',
        '  och dator, projekt- och tjänstesidor, förtroende och kontakt; flöden (typ flode) för förfrågan och projektgenomgång;',
        '  Mobbins sektioner, skärmar och flöden.',
        '- sajter: högst %d riktiga sajter att fånga (namn a-z0-9-, adress https://värd/ med små bokstäver, roll bransch,' % (4 if skiss else skapande.MAX_KANDIDATER_BRED),
        '  hantverk eller ux, varför, högst %d sidvägar). Välj sajter som paketet inte redan har, eller skriv varför en' % skapande.MAX_SIDOR_PER,
        '  befintlig behöver fler sidor; en referens som en förkastad riktning redan byggt på väljs bara med ett skäl som svarar',
        '  på kritiken. Domäner med å, ä eller ö skrivs i punycode.',
        'I riktningar: vilka skilda grundidéer researchen ska öppna, och vad i kundens material som bär var och en. Skilj på',
        'observation (vad en referens gör), rekommendation (vad vi föreslår för kunden) och belagd effekt (bara med källa).',
        *(['Förra svaret gick inte att köra: %s. Rätta det.' % fel] if fel else []),
        atelje.MATERIAL])


def forska(slug, n, skiss=False):
    """Researchpasset före planen: en session formulerar antagandena, frågorna och sajterna; referenssteget (referens.py och
    referenstjanster.py, via skapande.komplettera) hämtar sajterna och frågorna med belägg. En sajt eller fråga som går
    utanför kanalens form (eller nämner kundens uppgifter) släpps med skälet, och resten körs. FORSKNING.md säger vad som
    är nytt, vad som återanvänds och vilka antaganden som kan ändra designen."""
    r = rot(slug)
    u = atelje.UNDERLAG / slug
    forbjudna = skapande.forbjudna_termer(slug, atelje.UNDERLAG)
    fore_paket = skapande.senaste_paket(slug, atelje.UNDERLAG)
    fore_tj = (atelje.las_json(u / 'referenser' / 'tjanster' / 'TJANSTER.json') or {}).get('tid')
    fel, plan, res, slappta = None, {}, {}, []
    for forsok in (1, 2):
        svar = atelje.session(forska_prompt(slug, n, fel, skiss), LASVERKTYG, r / ('svar-forska-%d.json' % forsok),
                              FORSKA_SCHEMA_SKISS if skiss else FORSKA_SCHEMA, 150, atelje.MODELL,
                              EFFORT_SKISS if skiss else atelje.EFFORT, FRIST_SKISS_FORSKA if skiss else FRIST_FORSKA, slug=slug)
        plan = svar.get('structured_output') or {}
        sajter, fragor, slappta = [], [], []
        for s in plan.get('sajter') or []:
            f_ = skapande.kanal_fel({'referens': {'kandidater': [s]}}, bred=True)
            (slappta.append('sajten %s: %s' % (str((s or {}).get('adress'))[:80], f_)) if f_ else sajter.append(s))
        for q in plan.get('fragor') or []:
            f_ = skapande.kanal_fel({'tjanster': {'fragor': [q]}}, bred=True, forbjudna=forbjudna)
            (slappta.append('frågan "%s": %s' % (str((q or {}).get('fraga'))[:80], f_)) if f_ else fragor.append(q))
        begaran = {'varfor': str(plan.get('varfor') or 'research före kandidatplanen')[:1000]}
        if sajter:
            begaran['referens'] = {'kandidater': sajter[:skapande.MAX_KANDIDATER_BRED]}
        if fragor:
            begaran['tjanster'] = {'fragor': fragor[:skapande.MAX_FRAGOR_BRED]}
        if len(begaran) == 1:
            if skiss and not slappta:  # skissläget: det befintliga materialet räcker, inget hämtas
                fel = None
                break
            fel = 'varken sajter eller frågor gick att köra (%s)' % '; '.join(slappta[:4])
            continue
        f = r / 'FORSKNING-begaran.json'
        f.write_text(json.dumps(begaran, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        res = skapande.komplettera(slug, f, r, atelje.UNDERLAG, frist=min(FRIST_HAMTA, 1800) if skiss else FRIST_HAMTA, bred=True)
        fel = res.get('fel')
        if not fel:
            break
    efter_paket = skapande.senaste_paket(slug, atelje.UNDERLAG)
    tj = atelje.las_json(u / 'referenser' / 'tjanster' / 'TJANSTER.json') or {}
    nya_sajter = []
    if efter_paket and efter_paket != fore_paket:
        nya_sajter = [k.get('namn') for k in (atelje.las_json(efter_paket / 'PAKET.json') or {}).get('kandidater') or [] if not k.get('arv')]
    post = {'tid': nu(), 'varfor': plan.get('varfor'), 'riktningar': plan.get('riktningar'), 'fel': fel, 'slappta': slappta,
            'antaganden': plan.get('antaganden') or [], 'fragor': plan.get('fragor') or [], 'sajter': plan.get('sajter') or [],
            'nytt': {'paket': efter_paket.name if efter_paket and efter_paket != fore_paket else None, 'sajter': nya_sajter,
                     'tjanster': tj.get('tid') if tj.get('tid') and tj.get('tid') != fore_tj else None},
            'fore': {'paket': fore_paket.name if fore_paket else None, 'tjanster': fore_tj},
            'referens': res.get('referens'), 'tjanster': res.get('tjanster')}
    (r / 'FORSKNING.json').write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    rader = ['# Research före kandidatplanen · %s · %s' % (slug, post['tid']), '',
             'Gjord av kontroller/kandidater.py (forska): en session formulerade antagandena, frågorna och sajterna; referenssteget',
             'hämtade sajterna och frågorna med belägg. Det som mätts på en originalsajt står i paketets EXTRAKT.md, det tjänsterna',
             'beskriver i TJANSTER.md och de hela stildokumenten; vad vi väljer för kunden står i varje kandidats RIKTNING.md.', '',
             '## Antaganden om besökarna som kan ändra designen', '']
    for a in post['antaganden']:
        rader += ['- **%s** Underlag: %s. Prövas: %s. Om det inte stämmer: %s.' % (
            str(a.get('antagande') or '').strip(), str(a.get('underlag') or '').strip(), str(a.get('provning') or '').strip(), str(a.get('om_fel') or '').strip())]
    if not post['antaganden']:
        rader.append('- inga angivna')
    rader += ['', '## Nytt i den här körningen', '']
    if post['nytt']['paket']:
        rader.append('- referenspaketet %s (ärver %s): nyfångade sajter %s' % (post['nytt']['paket'], post['fore']['paket'] or 'inget', ', '.join(nya_sajter) or 'inga'))
    if post['nytt']['tjanster']:
        rader.append('- referenstjänsterna %s: %s' % (post['nytt']['tjanster'], rel(u / 'referenser' / 'tjanster' / 'TJANSTER.md')))
    if not post['nytt']['paket'] and not post['nytt']['tjanster']:
        rader.append('- inget nytt material: %s' % (fel or 'hämtningen gav inget'))
    rader += ['', '## Återanvänt', '', '- referenspaketet före körningen: %s' % (post['fore']['paket'] or 'inget'),
              '- tjänsternas förra undersökning: %s' % (post['fore']['tjanster'] or 'ingen'), '',
              '## Riktningarna researchen ska öppna', '', str(post['riktningar'] or ''), '', '## Frågorna', '']
    rader += ['- [%s · %s] %s — %s' % (f.get('tjanst'), f.get('typ'), f.get('fraga'), f.get('syfte')) for f in post['fragor']]
    rader += ['', '## Sajterna', ''] + ['- %s (%s) %s — %s' % (s.get('namn'), s.get('roll'), s.get('adress'), s.get('varfor')) for s in post['sajter']]
    if slappta:
        rader += ['', '## Släppta (utanför kanalens form)', ''] + ['- ' + x for x in slappta]
    (r / 'FORSKNING.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return post


# --- planen ---

PLANFALT = (('titel', None), ('hypotes', 'Hypotesen: varför lösningen passar verksamheten och besökaren'), ('ide', 'Idén'),
            ('uppgift', 'Den viktiga uppgift besökaren ska klara'), ('beslutsinnehall', 'Innehållet som hjälper besökaren att fatta beslut'),
            ('provning', 'Hur förslaget prövas: en besökaruppgift som beskriver målet utan att avslöja knappen'),
            ('forst', 'Det som möter besökaren först, och varför'),
            ('sektion', 'Den viktigaste innehållssektionen efter första vyn (den skissen visar), och varför'), ('bar_sidan', 'Det som bär sidan'),
            ('ordning', 'Innehållshierarki, informationsordning och rytm'), ('fortroende', 'Hur förtroende byggs'),
            ('bilder', 'Bildstrategin: bildernas uppgifter, storlekar och beskärning'), ('typografi', 'Typografiskt system'),
            ('farg', 'Färgernas funktion'), ('navigation', 'Navigation och interaktioner'), ('huvudreferens', 'Huvudreferens'),
            ('referens_kvalitet', 'Kvaliteten i referensen som återskapas'), ('referens_kraver', 'Vad den kvaliteten kräver'),
            ('material_mot_referens', 'Kundens material mot det referensen kräver'),
            ('antaganden', 'Antagandena om besökarna som uppdraget vilar på'), ('undersida', 'Undersidan eller tillståndet'),
            ('material', 'Material'), ('skillnad', 'Hur den skiljer sig från de andra'), ('fynd', 'Researchens fynd som formade uppdraget'))

PLAN_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['kandidater', 'variation'],
    'properties': {
        'variation': {'type': 'string'},
        'kandidater': {'type': 'array', 'minItems': 2, 'maxItems': 12, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': [f for f, _ in PLANFALT] + ['referensbilder'],
            'properties': {f: {'type': 'string'} for f, _ in PLANFALT} | {'referensbilder': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 6}}}}}}


def material_rader(slug):
    bilder = atelje.egna_bilder(slug)
    u = atelje.UNDERLAG / slug
    return ['Kundens egna bilder (%d st; beskrivning, projekt och kvalitet i %s). Välj och beskär efter bildens uppgift: resultat,' % (
                len(bilder), rel(u / 'bilder' / 'BILDER.md')),
            'detaljkvalitet, arbetsprocess eller personen bakom företaget. Ett foto som inte bär en stor yta får en mindre.',
            'Inga andra bilder: saknas material som riktningen kräver, omarbeta riktningen eller skriv behovet i "Material".']


def research_rader(slug):
    """Researchens material: den här körningens research (antaganden, nytt och återanvänt), referenspaketet och
    tjänsternas rapport."""
    u = atelje.UNDERLAG / slug
    paket = skapande.senaste_paket(slug, atelje.UNDERLAG)
    tj = u / 'referenser' / 'tjanster'
    rader = ['Researchen (läs den, och titta på bilderna med Read):']
    if (rot(slug) / 'FORSKNING.md').is_file():
        rader.append('- den här körningens research, med antagandena om besökarna och vad som är nytt och återanvänt: %s' % rel(rot(slug) / 'FORSKNING.md'))
    if paket:
        rader.append('- referenspaketet %s (fångade sajter: komposition, typografi, bilder, mätvärden i EXTRAKT.md per sida)' % rel(paket / 'PAKET.md'))
    if (tj / 'TJANSTER.md').is_file():
        rader.append('- referenstjänsterna (Refero och Mobbin): %s; varje Refero-stils hela dokument och tjänsternas svar ordagrant' % rel(tj / 'TJANSTER.md'))
        rader.append('  står där rapporten anger (ra-<tid>/)')
    if (u / 'REFERENSER.md').is_file():
        rader.append('- tidigare urval (bara underlag; ett urval som ägarens dom återöppnat är inget beslut): %s' % rel(u / 'REFERENSER.md'))
    if len(rader) == 1:
        rader.append('- ingen research finns än')
    return rader


def plan_prompt(slug, n, skiss=False):
    filer, refs, fel = atelje.underlag_rader(slug)
    return '\n'.join([
        'Du planerar skapandeflödets utforskning för en riktig verksamhet. Ägaren vill ha cirka %d %s med' % (
            n, 'skisser (första vyn och den viktigaste innehållssektionen, mobil och dator)' if skiss else 'genomarbetade prototyper'),
        'kundens riktiga information och väljer sedan själv vilken eller vilka som %s. Ditt arbete är uppdragen:' % (
            'fördjupas till hela startsidan, undersidan och besökarens centrala flöde' if skiss else 'utvecklas vidare'),
        '%d designriktningar som besvarar kundens problem på verkligt olika sätt. Varje uppdrag går till en egen skapare med' % n,
        'samma faktaunderlag; ingen ser de andras kod.', '',
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG, aktuella=True), '',
        *skapande.fakta_rader(slug, atelje.UNDERLAG), '',
        'Läs först: ' + ', '.join(filer) + '.',
        *historik_rader(slug),
        'Läs %s/%s innan du skriver planen, så att ingen underkänd grundidé upprepas utan nytt skäl.' % (rel(atelje.UNDERLAG / slug), skapande.HISTORIK)
        if (atelje.UNDERLAG / slug / skapande.HISTORIK).is_file() else '',
        *regel_rader(), *metod_rader(slug, 'plan'), '',
        *kompetens.prompt_rader('planera', slug), '',
        *research_rader(slug), *(['Bildval som inte gick att läsa: ' + '; '.join(fel)] if fel else []), '',
        *material_rader(slug), '',
        'Låt varje idé uppstå ur researchen och kundens material, aldrig ur fasta mallkategorier: uppdragen är olika sätt att',
        'presentera verksamheten (till exempel börja med dokumenterade projekt, med arbetsprocessen eller med specialistkompetensen),',
        'och variationen gäller hur sidan organiserar kundens information i besökarnas eget språk. Varje uppdrag besvarar: vilken',
        'viktig uppgift ska besökaren klara, vilket innehåll hjälper besökaren att fatta beslut, vad antar vi om besökarens behov',
        '(researchens antaganden), och hur kan vi pröva om förslaget fungerar (en besökaruppgift som "ta reda på om företaget kan',
        'hjälpa dig med ditt projekt och hur du går vidare", utan att avslöja knappen); och en kort hypotes om varför just den här',
        'lösningen passar verksamheten och besökaren (hypotesen visas för ägaren före det första valet: den nämner ingen referens',
        'eller sajt vid namn). Variera det som gör en sida till en egen sida: innehållshierarkin och vad som möter besökaren först;',
        'vad som bär sidan; bildstrategin; det typografiska systemet; navigationen; hur förtroende byggs; färgernas funktion.',
        'Det är verktyg för att upptäcka falsk variation, ingen checklista där allt måste bytas. Tio färgvarianter av samma',
        'struktur är inga tio riktningar, och inget uppdrag får vara avsiktligt svagt.',
        'Huvudreferensen per uppdrag är en namngiven sajt eller skärm ur researchen (referenspaketet eller tjänsternas fynd),',
        'som får vara utgångspunkt för layout, palett och typografi (ägarens beslut); dess identitet, texter och bilder blir',
        'aldrig kundens innehåll. Skriv vilken kvalitet i referensen uppdraget ska återskapa, vad den kvaliteten kräver (till',
        'exempel stora arkitekturfoton, korta rubriker, få produkter), och om kundens faktiska material uppfyller det (små',
        'arbetsbilder, långa svenska rubriker och många tjänster ändrar förutsättningarna); när det inte gör det, hur uppdraget',
        'anpassas (kunskap/bild.md, art direction) och vad som beställs. Ange 1–4 referensbilder (sökvägar under',
        'underlag/%s/referenser/) som visar kvaliteten.' % slug,
        'Ange i "sektion" den viktigaste innehållssektionen efter första vyn för just den idén (den skissen visar), och varför.',
        'En referens som en förkastad eller underkänd riktning redan byggt på (historiken) väljs bara med ett skäl i "skillnad"',
        'som svarar på kritiken. Ange vilken undersida eller vilket tillstånd som visar idén bäst (ett projekt, en tjänst,',
        'ett kontaktförlopp) och vilket material som saknas för riktningen och hur den klarar sig utan det.',
        'Skriv i "fynd" vilka fynd ur researchen (namn och fil) som formade uppdraget och om de är nya i den här körningen',
        'eller återanvända (FORSKNING.md säger vilket).',
        'Skriv i "variation" hur uppdragen skiljer sig längs de dimensionerna och var två ligger nära varandra.',
        'Svara med uppdragen i schemat.', atelje.MATERIAL])


def skriv_uppdrag(slug, kid, k, nr, totalt):
    d = kdir(slug, kid)
    atelje.saker_vag(d, rot(slug))
    d.mkdir(parents=True, exist_ok=True)
    rader = ['# Uppdrag %s · %s' % (kid, k['titel']), '', 'Kandidat %d av %d i skapandeflödet (kontroller/kandidater.py, planen %s).' % (nr, totalt, nu()), '']
    for falt, rubrik in PLANFALT:
        if rubrik:
            rader += ['## %s' % rubrik, '', str(k.get(falt) or '').strip(), '']
    rader += ['## Referensbilder', ''] + ['- ' + str(p) for p in k.get('referensbilder') or []] + ['']
    (d / 'UPPDRAG.md').write_text('\n'.join(rader), encoding='utf-8')


def planera(slug, n, lage=None):
    """Planeringspasset: uppdragen ur researchen och kundens material (ett schema, så att varje uppdrag har sina fält).
    Planen bär körningens läge, så att en återupptagning följer körningen."""
    r = rot(slug)
    lage = lage or LAGE
    svar = atelje.session(plan_prompt(slug, n, lage == 'skiss'), LASVERKTYG + kompetens.verktyg('planera', slug), r / 'svar-plan.json', PLAN_SCHEMA, 200,
                          atelje.MODELL, EFFORT_SKISS if lage == 'skiss' else atelje.EFFORT, FRIST_PLAN, slug=slug)
    plan = svar.get('structured_output') or {}
    kand = [k for k in plan.get('kandidater') or [] if isinstance(k, dict) and str(k.get('titel') or '').strip()][:n]
    if len(kand) < max(2, n // 2):
        raise RuntimeError('planen gav %d användbara uppdrag av %d' % (len(kand), n))
    ids = ['k%02d' % i for i in range(1, len(kand) + 1)]
    for i, (kid, k) in enumerate(zip(ids, kand), 1):
        skriv_uppdrag(slug, kid, k, i, len(kand))
        satt_status(slug, kid, 'planerad', 'uppdraget skrivet', titel=k['titel'], hypotes=k.get('hypotes'), huvudreferens=k.get('huvudreferens'), forsok=0)
    (r / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': nu(), 'antal': len(ids), 'lage': lage, 'variation': plan.get('variation'), 'kandidater': dict(zip(ids, kand))},
                                                   ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (r / 'KANDIDATPLAN.md').write_text('\n'.join(['# Kandidatplan · %s · %s' % (slug, nu()), '', '## Variationen', '', str(plan.get('variation') or ''), '']
                                                 + ['- **%s · %s**: %s' % (kid, k['titel'], re.sub(r'\s+', ' ', k.get('hypotes') or k['ide'])[:300]) for kid, k in zip(ids, kand)]) + '\n',
                                       encoding='utf-8')
    return ids


# --- skaparen ---

def verktyg(slug, kid, komplettering=True):
    """Skaparens verktyg; komplettering: får sessionen begära research (högst en gång per kandidat, granskning 2, N6).
    Skaparen skriver i hela det egna projektets src/ (sidor, komponenter, layouter, stilar, egna tillgångar; Codex via
    ägaren 2026-10-05, punkt 5); kundens bilder och de andra kandidaterna nekas (andra_nekas)."""
    s = 'kunder/%s/kandidater/%s/sajt' % (slug, kid)
    k = 'underlag/%s/atelje/kandidater/%s' % (slug, kid)
    return LASVERKTYG + ['Write(./%s/src/**)' % s, 'Edit(./%s/src/**)' % s,
                         'Write(./%s/RIKTNING.md)' % k, 'Edit(./%s/RIKTNING.md)' % k] \
        + (['Write(./%s/%s)' % (k, skapande.KOMPLETTERING)] if komplettering else []) + [
                         'Bash(.venv/bin/python kontroller/typsnitt.py %s *)' % slug,
                         'Bash(.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s)' % (slug, kid),
                         'Bash(.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s *)' % (slug, kid)]


VISAR = ('grundidén syns i den renderade sidan', 'kundens material bär kompositionen',
         'den viktigaste besökaruppgiften går att genomföra från startsidan', 'mobilversionen håller ihop')


def objektiva(slug, kid, k=None):
    """Det en förbättringsrunda rättar: granskningens avvikelser av slaget krav (bryter ett kvalitetskrav eller hindrar
    besökarens uppgift) med allvar hög eller medel, som inte är avsiktliga och välgrundade, och axe:s allvarliga fynd.
    Smak rättas inte före ägarens val, så att granskningen inte jämnar ut skillnaderna mellan kandidaterna. En granskning
    vars läsning inte kunde prövas (inget transkript) eller som inte läste de första vyerna styr ingenting; axe gör det."""
    k = k if k is not None else (atelje.las_json(kdir(slug, kid) / 'KRITIK.json') or {})
    ut = []
    if k.get('last') is True:  # bara en granskning som bevisligen läst de första vyerna styr (granskning 2, N5)
        for a in k.get('avvikelser') or []:
            if a.get('slag') == 'krav' and a.get('allvar') in ('hog', 'medel') and not (a.get('avsiktlig') and a.get('valgrundad')):
                ut.append('%s (%s): %s → %s' % (a.get('var'), a.get('allvar'), a.get('vad'), a.get('atgard')))
    for r in (las_status(slug, kid).get('axe') or {}).get('regler') or []:
        ut.append('tillgänglighet (axe, allvarlig): %s' % r)
    return ut


def skapar_prompt(slug, kid, kritik=None, komplettering=None, forbattra=None, erbjud=True):
    d, s = kdir(slug, kid), 'kunder/%s/kandidater/%s/sajt' % (slug, kid)
    filer, _refs, _fel = atelje.underlag_rader(slug)
    tel = skapande.telefon(slug, atelje.UNDERLAG)
    forhand = '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s' % (slug, kid)
    return '\n'.join([
        'Du är en av flera skapare i skapandeflödet (kunskap/skapandeflodet.md) för en riktig verksamhet. Du gör EN kandidat,',
        '%s, enligt uppdraget %s. Andra skapare gör andra kandidater med samma faktaunderlag och andra uppdrag; du ser inte' % (kid, rel(d / 'UPPDRAG.md')),
        'deras kod och ska inte efterlikna dem. Ägaren ser alla kandidater sida vid sida och väljer själv vilken eller vilka',
        'som utvecklas vidare: din kandidat ska vara ett seriöst förslag på professionell nivå som skulle kunna väljas.', '',
        *(['Förbättringsrundan: granskningen fann objektiva fel (kvalitetskrav eller hinder för besökarens uppgift). Rätta',
           'just dem, och behåll idén och uttrycket i övrigt: smak rättas inte här, ägaren väljer bland olika uttryck.',
           *['- ' + x for x in objektiva(slug, kid)], ''] if forbattra else []),
        *(['Förra sessionen slutade utan att kandidaten blev klar (%s). Det som finns står kvar i projektet och i RIKTNING.md;' % kritik,
           'fortsätt därifrån och rätta bristerna.', ''] if kritik else []),
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG, aktuella=True), '',
        *skapande.fakta_rader(slug, atelje.UNDERLAG), '',
        'Läs först uppdraget, sedan: ' + ', '.join(filer) + '.',
        *historik_rader(slug),
        *regel_rader(), *metod_rader(slug, 'skapa'), '',
        *material_rader(slug),
        'Bilderna ligger i ditt projekt under %s/src/assets/atelje/; importera dem med sökväg från projektroten' % s,
        '(/src/assets/atelje/<fil>) och visa dem med <Image> från astro:assets, med format, storlek och object-position efter',
        'bildens uppgift.', '',
        *([''] + skapande.kompletteringsrader(komplettering) if komplettering else []),
        'Arbetsgången:',
        '1. Skriv %s INNAN du bygger: överst raden `Huvudreferens: <namn> — <vad den bär i kandidaten>`, sedan' % rel(d / 'RIKTNING.md'),
        '   hypotesen i en mening, vad som möter besökaren först och varför, typsnitten, färgerna med roller, och rubriken',
        '   "Material" med det kunden saknar för riktningen. Arbetet bedöms ur den filen också om tiden tar slut.',
        '2. Tidigt kompositionsprov: bygg första vyn och den viktigaste innehållssektionen i %s/src/pages/index.astro' % s,
        '   och kör `%s` (tidsgräns 600000 ms). Läs med Read mobilens och datorns första vy och hela sida, och' % forhand,
        '   uppdragets referensbilder. Svara under rubriken "Referensens kvalitet" i RIKTNING.md: vilken kvalitet i referensen',
        '   återskapas, vad kräver den, och bär kundens faktiska material den? Om inte: ändra kompositionen nu (mindre',
        '   bildytor, typografin bär, bevis i stället för stämningsbild) och skriv vad som behöver beställas, innan samma',
        '   problem sprids över hela sidan. Skriv där också, för huvudreferensen, de fyra relationerna med en referensbild och',
        '   din egen bild bredvid varandra: hur bildens beskärning samspelar med rubriken, hur de typografiska storlekarna skapar',
        '   hierarki, hur täta och luftiga sektioner skapar rytm, och hur navigation och interaktion stödjer innehållet; vad',
        '   referensen gör och vad kandidaten gör med kundens material. En hämtad bild eller ett läst dokument är bara material.',
        '3. Bygg hela startsidan som en sammanhängande sida: alla sektioner genomarbetade i idéns form, inga ofärdiga',
        '   standardblock efter en välgjord topp. Mobilen först och lika genomtänkt i 1440; komponenter, layouter och stilar',
        '   i projektets src/ där de återanvänds (kunskap/beroenden.md). Rubriker, textlängd och ordning får bearbetas för',
        '   idén; sakuppgifterna ändras aldrig.',
        '4. Bygg undersidan eller tillståndet som uppdraget anger, i %s/src/pages/<väg>/index.astro, i samma riktning.' % s,
        '   Formulär postar till /api/forfragan/ och landar på /tack/ (lokal demonstration, inget skickas). Länka bara till',
        '   sidor som finns i ditt projekt. Inga test-, variant- eller prototypsidor: varje index.astro blir en undersida.',
        '5. Varv: kör `%s` (och `--sida /<väg>/` för undersidan; `--mellan` för att se 768 när' % forhand,
        '   layouten byter form mellan bredderna). Läs med Read i varje varv dina egna bilder och minst en referensbild (de',
        '   äldsta bilderna trängs undan ur kontexten). Skriv i RIKTNING.md under "Varv N" varje konkret avvikelse och åtgärden,',
        '   och vad i metoden som gav åtgärden. Kontrollera bildurval, beskärning, typografiska proportioner, linjering,',
        '   innehållstäthet och sektionsövergångar. Arbetsregeln är minst %d varv; antalet varv är ingen kvalitetsbedömning.' % MIN_VARV,
        '   Fler små justeringar av färg och avstånd är inte alltid svaret: byt grundidé när den inte bär.',
        'Typsnitt: systemtypsnitt, eller `.venv/bin/python kontroller/typsnitt.py %s @fontsource-variable/<namn>` (eller' % slug,
        '@fontsource/<namn>) och importera CSS-filen i sidan. Ringlänken är numret ur VERKSAMHET.json%s.' % ((' (%s)' % tel) if tel else ''),
        *([] if forbattra or not erbjud else [
            'Saknar du referensmaterial för en avgörande egenskap: skriv %s i formatet %s, och avsluta;' % (
                rel(d / skapande.KOMPLETTERING), skapande.KOMPLETTERINGSFORMAT),
            'orkestratorn kör researchen och startar en ny session med resultatet (högst en gång per kandidat).']), '',
        'Du är klar när den renderade sidan visar att %s, att %s, att %s och att %s; skriv under' % VISAR,
        'rubriken "Visar" i RIKTNING.md vilken bild som visar var och en. Sidorna bygger, du har läst bilderna, och RIKTNING.md',
        'har huvudreferensen, hypotesen, referensens kvalitet, varven och materialet.', atelje.MATERIAL])


def skiss_prompt(slug, kid, fel=None, komplettering=None, erbjud=True, minuter=30, forsok_min=None):
    """Skaparens rena arbetskontext i skissläget (ägarens uppdrag 2026-10-05 16:25Z, punkt 2 och 4): uppdraget, kundens
    verifierade fakta och material, referensbilderna, de aktuella besluten och metodens kärna med en förteckning att slå
    upp i. Historiken slås upp vid behov."""
    d, s_ = kdir(slug, kid), rel(ksajt(slug, kid))
    u = atelje.UNDERLAG / slug
    tel = skapande.telefon(slug, atelje.UNDERLAG)
    forhand = '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s' % (slug, kid)
    m = metodinfo(slug, 'skiss')
    aktuella = skapande.kritikrader(slug, underlag=atelje.UNDERLAG, aktuella=True)
    return '\n'.join([
        'Du är en av flera skapare i skapandeflödets skissomgång (kunskap/skapandeflodet.md) för en riktig verksamhet. Du gör',
        'EN skiss, %s, enligt uppdraget %s. Andra skapare gör andra skisser med samma fakta och andra uppdrag; du ser inte' % (kid, rel(d / 'UPPDRAG.md')),
        'deras kod och ska inte efterlikna dem. Ägaren ser alla skisser sida vid sida och väljer vilken eller vilka som',
        'fördjupas: din skiss ska vara ett professionellt, tydligt eget förslag som går att bedöma.', '',
        'Omfattningen: första vyn, den viktigaste innehållssektionen som uppdraget anger, navigationen och de interaktioner som',
        'behövs för att förstå förslaget (till exempel menyn på mobilen och den primära handlingen), genomarbetat i mobil (390)',
        'och dator (1440). Inte hela startsidan och ingen undersida: sidan slutar efter sektionen med en enkel sidfot med',
        'kontaktvägen. Skissen visar verklig komposition, typografi, bildbehandling och innehållshierarki.', '',
        *(['Förra försöket slutade med ett tekniskt fel: %s. Det som finns står kvar i projektet; rätta felet först.' % fel, ''] if fel else []),
        'Ditt underlag, det du behöver läsa:',
        '- uppdraget %s: designuppdraget, besökarens viktigaste uppgift, den viktigaste sektionen, huvudreferensen och' % rel(d / 'UPPDRAG.md'),
        '  referensbilderna med vad de ska lära dig (titta på bilderna med Read);',
        '- kundens verifierade fakta: %s, %s (sakuppgifterna gäller; rubriker och ordning är utkast) och %s' % (
            rel(u / 'VERKSAMHET.json'), rel(skapande.textfil(slug, atelje.UNDERLAG)), rel(u / 'RESEARCH.md')),
        '  (raderna Belägg, listan "Bara de har" och omdömena ordagrant); besökarnas toppuppgifter och den primära handlingen',
        '  står i %s;' % rel(u / 'BRIEF.md'),
        '- materialet: %s; bilderna ligger i ditt projekt under %s/src/assets/atelje/: importera dem från' % (rel(u / 'bilder' / 'BILDER.md'), s_),
        '  /src/assets/atelje/<fil> och visa dem med <Image> från astro:assets, beskurna efter bildens uppgift;',
        '- metoden: %s (kvalitetskraven, besluten som gäller med räckvidd, avgörandena mellan motstridiga råd och en' % ', '.join(m['delar']['före']),
        '  förteckning över utdrag ur skills och kunskapsfiler som du slår upp när uppgiften behöver dem).',
        *([''] + aktuella if aktuella else []), '',
        *historik_rader(slug), '',
        'Sanningen: använd kundens verifierade material. Där material saknas står ett tydligt märkt utkast ("Utkast: …") eller',
        'en platshållare som säger vad som saknas ("Bild saknas: …"). Hitta aldrig på omdömen, meriter, certifieringar,',
        'resultat, siffror eller andra kundfakta: varje siffra i texten finns i underlaget. Bilder som visar verksamheten',
        'är kundens egna; illustrativt material som inte utger sig för att visa verksamheten får användas med källa',
        '(kunskap/bild.md). Ett formulär postar till /api/forfragan/ och landar på /tack/ (lokal demonstration).',
        'Interaktion (menyn och liknande) skrivs i ett <script> i sidan eller komponenten, som Astro ger en hash i sajtens CSP;',
        'inline-händelser som onclick= stoppas av CSP:n och syns som konsolfel (byggstandarden 8.2). Innehållet och',
        'navigationen fungerar utan JavaScript.', '',
        *(skapande.kompletteringsrader(komplettering) + [''] if komplettering else []),
        *kompetens.prompt_rader('skapa', slug, kid), '',
        'Arbetsgången:',
        '0. Läs rollernas kärna hel (eller ladda skillen med skillverktyget) och välj bland alternativen det som passar',
        '   riktningen. Researchens material är redan hämtat åt dig; sök kompletterande förebilder i Refero eller Mobbin när',
        '   underlaget inte räcker för uppdragets viktigaste sektion (branschen och uppgiften, aldrig kundens uppgifter), och kör',
        '   UI UX Pro Max-sökningen när riktningen behöver ett designsystemsförslag. Ett tomt eller misslyckat sökresultat',
        '   skrivs som det är och räknas inte som underlag.',
        '1. Skriv %s INNAN du bygger: överst raden `Huvudreferens: <namn> — <vad den bär i skissen>`, sedan hypotesen i en' % rel(d / 'RIKTNING.md'),
        '   mening; rubriken "Referenslås" (refero-design: huvudreferensen, det som ska bevaras, det som lånas, rollregler för',
        '   färger och komponenter, bildstrategin, det som väljs bort, och de tokens du binder dig till) och en kort',
        '   beslutsliggare (beslut, källa, roll, varför); vad du lär av referensbilderna (bildens beskärning mot rubriken,',
        '   typografins hierarki, rytmen och navigationen); rubriken "Material" med det kunden saknar; och rubriken',
        '   "Kompetenserna" med alternativen du valde och vad varje roll ändrade i skissen, eller var en skill inte passade och',
        '   varför.',
        '2. Bygg skissen med startsidan i %s/src/pages/index.astro och komponenter, layouter och stilar i src/ där det hjälper' % s_,
        '   (mobilen först; de låsta beroendena i kunskap/beroenden.md), och kör `%s` (tidsgräns 600000 ms). Läs med' % forhand,
        '   Read mobilens och datorns första vy och hela sida, och jämför med referensbilderna.',
        '3. Varje nytt varv åtgärdar en konkret brist som du ser i dina bilder eller vid jämförelsen med referensen; skriv i',
        '   RIKTNING.md under "Varv N" bristen och åtgärden. Inget fast antal varv: sluta när du inte ser någon brist som går',
        '   att åtgärda inom tiden.',
        'Tiden: högst %d minuter för din session, bygg- och verktygstid inräknad (försöket högst %d minuter med fotograferingen' % (
            minuter, forsok_min or minuter),
        'efter); sedan stoppas sessionen. Ha en renderad',
        'första version efter ungefär en tredjedel av tiden, så att det alltid finns något för ägaren att bedöma.',
        'Typsnitt: systemtypsnitt, eller `.venv/bin/python kontroller/typsnitt.py %s @fontsource-variable/<namn>` (eller' % slug,
        '@fontsource/<namn>) och importera CSS-filen i sidan. Ringlänken är numret ur VERKSAMHET.json%s.' % ((' (%s)' % tel) if tel else ''),
        *(['Saknar referensmaterialet något som skissen behöver: skriv %s i formatet %s, och avsluta;' % (
            rel(d / skapande.KOMPLETTERING), skapande.KOMPLETTERINGSFORMAT),
           'orkestratorn hämtar det och startar en ny session med resultatet, inom samma tid (högst en gång per kandidat).'] if erbjud else []), '',
        'Du är klar när skissen är byggd och renderad i 390 och 1440, du har tittat på bilderna, och RIKTNING.md har',
        'huvudreferensen, referenslåset, hypotesen, varven, materialet och kompetensernas arbete. Ingen annan session ändrar',
        'skissen före ägarens val.', atelje.MATERIAL])


def anvandning(sessioner):
    """Vad sessionerna använde, ur transkripten: verktygen, metodens delar och referensbilderna som öppnades. Redovisas,
    graderas aldrig (ägarens uppdrag 2026-10-05: antalet lästa filer, anrop eller varv är inget kvalitetsbetyg)."""
    verktyg_, delar, referenser, sedda = set(), set(), set(), 0
    for x in sessioner:
        t = bildkedja.transkript(x.get('session_id'))
        if t is None:
            continue
        sedda += 1
        for h in bildkedja.handelser(t):
            if h[0] != 'anrop':
                continue
            if h[2] == 'Bash':
                c = str((h[3] or {}).get('command') or '')
                verktyg_.add('förhandsvisning' if 'forhandsvisa.py' in c else 'typsnitt' if 'typsnitt.py' in c else 'Bash')
            else:
                verktyg_.add(str(h[2]))
            if h[2] == 'Read':
                v = bildkedja.relativ((h[3] or {}).get('file_path') or '')
                if '/atelje/metod/' in v:
                    delar.add(Path(v).name)
                elif '/referenser/' in v:
                    referenser.add(v)
    return {'transkript': sedda, 'verktyg': sorted(verktyg_), 'metoddelar': sorted(delar), 'referenser': sorted(referenser)[:24]}


def lasningen(slug, kid, svarfil, steg):
    """Läsningen i en skaparsession, ur transkriptet (kontroller/bildkedja.py): metoden före första skrivningen och
    varvens bilder med en referensbild, varv för varv. Redovisas skilt från tillämpningen (varven i RIKTNING.md)."""
    s = atelje.las_json(svarfil) or {}
    sid = s.get('session_id')
    if not sid:
        return {'verifierad': False, 'skal': 'ingen session'}
    src = rel(ksajt(slug, kid) / 'src') + '/'  # kandidatens egna sidor, relativt roten
    m = metodinfo(slug, steg)
    fore = m['delar']['före']
    ml = bildkedja.metodlasning(sid, fore, skrivprefix=src)
    vo = bildkedja.varvordning(sid, slug, uppdragets_bilder(slug, kid), src=src)
    hela = bool(ml.get('verifierad')) and not ml.get('saknas')  # alla före-filer lästa hela, utan fel (granskning 2, N5)
    return {'verifierad': bool(ml.get('verifierad') and vo.get('verifierad')), 'metod_sha': m['sha'],
            'metod_fore_forsta_skrivning': hela and len(ml.get('fore') or []) == len(fore), 'metod_last': hela,
            'metod_delvis': ml.get('delvis') or [], 'metod_saknas': ml.get('saknas') or [],
            'varv': [{'varv': x['varv'], 'lasta': x['lasta'], 'kravda': x['kravda']} for x in vo.get('varv') or []],
            'skal': ml.get('skal') or vo.get('skal')}


def skapa(slug, kid):
    """En skaparsession för kandidaten (och en ny efter en begärd komplettering); sedan fotograferas den."""
    st = las_status(slug, kid)
    forsok = int(st.get('forsok') or 0) + 1
    forbered_projekt(slug, kid)
    tidigare = st.get('skal') if st.get('status') in ('under_arbete', 'avbruten', 'fel', 'ofullstandig') and forsok > 1 else None
    satt_status(slug, kid, 'under_arbete', 'skaparsession %d' % forsok, forsok=forsok, startad=nu(), metod={'skapa': metodinfo(slug, 'skapa')['sha']})
    d = kdir(slug, kid)
    res, sessioner, lasn = None, [], None
    kompletterad = bool(st.get('kompletterad'))  # researchen på begäran körs högst en gång per kandidat (granskning 2, N6)
    for k in range(2):
        ut = d / ('svar-skapa-%d%s.json' % (forsok, '-%d' % k if k else ''))
        try:
            svar = atelje.session(skapar_prompt(slug, kid, tidigare, res, erbjud=not kompletterad), verktyg(slug, kid, komplettering=not kompletterad),
                                  ut, max_turer=500, frist=FRIST_SKAPA, nekas=andra_nekas(slug, kid), slug=slug)
        except (subprocess.TimeoutExpired, RuntimeError) as e:  # det som hann göras fotograferas och bedöms ändå
            svar = {'avbruten': '%s: %s' % (type(e).__name__, str(e)[:300])}
        sessioner.append({'svar': ut.name, **{x: svar.get(x) for x in ('session_id', 'num_turns', 'duration_ms', 'total_cost_usd', 'avbruten')}})
        lasn = lasningen(slug, kid, ut, 'skapa')
        if not (d / skapande.KOMPLETTERING).is_file():
            break
        if svar.get('avbruten') or kompletterad:  # en begäran som inte körs sparas obesvarad, aldrig raderad
            arkiv = d / 'kompletteringar'
            arkiv.mkdir(parents=True, exist_ok=True)
            os.replace(d / skapande.KOMPLETTERING, atelje.ledigt_namn(arkiv, '%s-obesvarad.json' % nu().replace(':', '')))
            break
        res = skapande.komplettera(slug, d / skapande.KOMPLETTERING, d, atelje.UNDERLAG, forbjudna=skapande.forbjudna_termer(slug, atelje.UNDERLAG))
        kompletterad = True
        satt_status(slug, kid, 'under_arbete', 'research på begäran gjord; ny skaparsession med resultatet', kompletterad=True)
    satt_status(slug, kid, 'under_arbete', 'fotograferas', sessioner=(las_status(slug, kid).get('sessioner') or []) + sessioner, lasning=lasn)
    return fotografera(slug, kid)


def arkivera_forsok(slug, kid, st):
    """Ett avbrutet skissförsök sparas (projektet, RIKTNING.md och varven) i kandidatens forsok-<n>/, och nästa försök
    börjar i ett nytt projekt: billiga skisser startas om i stället för att tas upp mitt i (ägarens uppdrag 2026-10-05,
    punkt 6). Inget raderas."""
    d, pr = kdir(slug, kid), ksajt(slug, kid)
    mal = atelje.ledigt_namn(d, 'forsok-%s' % (st.get('forsok') or 0))
    atelje.saker_vag(mal, rot(slug))
    mal.mkdir(parents=True)  # före flyttarna: en fil flyttas aldrig in i en katalog som saknas (granskning 3, S1)
    for n in ('RIKTNING.md', 'varv', 'bilder'):
        if (d / n).exists() and not (d / n).is_symlink():
            shutil.move(str(d / n), str(mal / n))
    if pr.exists() or pr.is_symlink():
        atelje.saker_vag(pr.parent, atelje.KUNDER / slug)
        shutil.move(str(pr), str(mal / 'projekt'))
    return mal


def skissa(slug, kid, fel=None):
    """Ett skaparförsök i skissläget: en session (och en till efter en begärd komplettering) inom försökets tid, räknad
    från försökets start med verktygsväntan inräknad, sedan fotografering och de snabba kontrollerna. fel: ett omförsök
    efter ett identifierat tekniskt fel, med kortare tid. Ingen förlängning."""
    st = las_status(slug, kid)
    forsok = int(st.get('forsok') or 0) + 1
    frist = FRIST_SKISS_OMFORSOK if fel else FRIST_SKISS
    start, startad = time.monotonic(), nu()  # försöket räknas från början, förberedelsen och fotograferingen inräknade (S8)
    forbered_projekt(slug, kid)
    satt_status(slug, kid, 'under_arbete', 'skiss, försök %d' % forsok, forsok=forsok, startad=startad, frist=frist,
                metod=dict(st.get('metod') or {}, skiss=metodinfo(slug, 'skiss')['sha']), ta_bort=('tekniskt_fel',))
    d = kdir(slug, kid)
    res, sessioner, sessionsfel = None, [], []
    kompletterad = bool(st.get('kompletterad'))
    for k in range(2):
        kvar = int(frist - FOTO_RESERV - (time.monotonic() - start))  # fotograferingen efter sessionen ryms i försökets tid
        if kvar < 120:
            break
        ut = d / ('svar-skiss-%d%s.json' % (forsok, '-%d' % k if k else ''))
        try:
            svar = atelje.session(skiss_prompt(slug, kid, fel, res, erbjud=not kompletterad, minuter=max(2, -(-kvar // 60)), forsok_min=frist // 60),
                                  verktyg(slug, kid, komplettering=not kompletterad) + kompetens.verktyg('skapa', slug, kid), ut,
                                  max_turer=500, effort=EFFORT_SKISS, frist=kvar, nekas=andra_nekas(slug, kid), slug=slug,
                                  vid_start=lambda pid: satt_status(slug, kid, 'under_arbete', 'skiss, försök %d' % forsok, session_pid=pid))
        except subprocess.TimeoutExpired:
            svar = {'avbruten': 'försökets tid (%d min) tog slut' % (frist // 60), 'tidsgrans': True}
        except RuntimeError as e:
            svar = {'avbruten': 'RuntimeError: %s' % str(e)[:300]}
            sessionsfel.append(str(e)[:200])
        sessioner.append({'svar': ut.name, **{x: svar.get(x) for x in ('session_id', 'num_turns', 'duration_ms', 'total_cost_usd', 'avbruten')}})
        if atelje.STOPP.is_set():  # arbetaren stoppas: försöket står kvar under arbete och startas om vid återupptagningen
            raise atelje.Stoppad('försöket avbröts av stoppet')
        if not (d / skapande.KOMPLETTERING).is_file():
            break
        kvar = int(frist - (time.monotonic() - start))
        if svar.get('avbruten') or kompletterad or kvar < 600:  # en begäran som inte ryms i tiden sparas obesvarad
            arkiv = d / 'kompletteringar'
            arkiv.mkdir(parents=True, exist_ok=True)
            os.replace(d / skapande.KOMPLETTERING, atelje.ledigt_namn(arkiv, '%s-obesvarad.json' % nu().replace(':', '')))
            break
        res = skapande.komplettera(slug, d / skapande.KOMPLETTERING, d, atelje.UNDERLAG, frist=max(60, (kvar - 300) // 2),
                                   forbjudna=skapande.forbjudna_termer(slug, atelje.UNDERLAG), las_frist=max(0, kvar - 600))
        kompletterad = True
        satt_status(slug, kid, 'under_arbete', 'research på begäran gjord; ny session med resultatet', kompletterad=True)
    tidigare = las_status(slug, kid)
    satt_status(slug, kid, 'under_arbete', 'fotograferas', sessioner=(tidigare.get('sessioner') or []) + sessioner)
    st = fotografera(slug, kid, skiss=True)
    tidsgrans = any('tog slut' in str(x.get('avbruten') or '') for x in sessioner)
    # ett identifierat tekniskt fel: sessionen föll, bygget föll eller bilderna saknas; en tid som tog slut är inget
    # tekniskt fel, och ett nytt försök vore en förlängning (ägarens försöksbudget 2026-10-05)
    tekniskt = st['status'] != 'klar' and not tidsgrans and bool(sessionsfel or any(
        x.startswith('bygget föll') or 'fotograferingen gav inte' in x for x in st.get('hinder') or []))
    sek = int(time.monotonic() - start)
    forsoken = (tidigare.get('forsok_tider') or []) + [{'forsok': forsok, 'startad': startad, 'klar': nu(), 'sekunder': sek,
                                                         'utfall': st['status'], 'omforsok': bool(fel), 'tidsgrans': tidsgrans}]
    kv = kompetens.kvitto(sessioner, 'skapa', skrivprefix=rel(ksajt(slug, kid) / 'src') + '/')
    varv_ = varvnummer(slug, kid)
    fore = kopiera_bilder(d / 'varv' / 'start' / ('varv-%02d' % varv_[0]), d / 'kompetens' / 'skiss-skapa' / 'fore') if varv_ else []
    efter = kopiera_bilder(d / 'bilder' / 'start', d / 'kompetens' / 'skiss-skapa' / 'efter')
    kompetenser = dict(las_status(slug, kid).get('kompetens') or {})
    kompetenser['skiss:skapa'] = {'fas': 'skiss', 'pass': 'skapa', 'klar': nu(), 'sekunder': int(time.monotonic() - start),
                                  'kvitto': {k: kv.get(k) for k in ('verifierad', 'lasta', 'saknas', 'valda', 'skill_anrop', 'mcp_anrop')},
                                  # kärnan läst hel; MCP-anropen redovisas men krävs inte: researchen har redan hämtat
                                  # materialet åt skaparna (ägarens uppdrag 2026-10-05 18:53Z, punkt 3)
                                  'genomford': (not kv.get('saknas')) if kv.get('verifierad') else None,
                                  'varv': len(varv_), 'bilder': {'fore': fore, 'efter': efter}}
    return satt_status(slug, kid, st['status'], st.get('skal', ''), tekniskt_fel=tekniskt, forsok_tider=forsoken,
                       anvandning=anvandning(sessioner), sessionsfel=sessionsfel or None, kompetens=kompetenser)


# --- kompetenserna (kunskap/metodkarta.md, Kompetenserna; ägarens ord 2026-10-05 18:15Z) ---

PASS_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['kod_andrad', 'beteende_provat', 'visuell_bedomning', 'ingen_andring', 'valda', 'passade_inte', 'kvarstar'],
    'properties': {
        'kod_andrad': {'type': 'array', 'maxItems': 24, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['skill', 'vad', 'var', 'varfor'],
            'properties': {k: {'type': 'string'} for k in ('skill', 'vad', 'var', 'varfor')}}},
        'beteende_provat': {'type': 'array', 'maxItems': 24, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['vad', 'hur', 'resultat', 'bild'],
            'properties': {k: {'type': 'string'} for k in ('vad', 'hur', 'resultat', 'bild')}}},
        'visuell_bedomning': {'type': 'object', 'additionalProperties': False, 'required': ['fore', 'efter', 'omdome', 'skal'],
                              'properties': {'fore': {'type': 'string'}, 'efter': {'type': 'string'},
                                             'omdome': {'type': 'string', 'enum': ['battre', 'oforandrad', 'samre', 'ej_bedomd']},
                                             'skal': {'type': 'string'}}},
        'ingen_andring': {'type': 'string'},
        'valda': {'type': 'array', 'maxItems': 16, 'items': {'type': 'string'}},
        'passade_inte': {'type': 'array', 'maxItems': 16, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['skill', 'varfor'],
            'properties': {'skill': {'type': 'string'}, 'varfor': {'type': 'string'}}}},
        'kvarstar': {'type': 'array', 'maxItems': 12, 'items': {'type': 'string'}}}}

PASSUPPGIFT = {
    'rorelse': ('Välj och genomför de beteenden som passar den fördjupade sidan (menyn, hovring och fokus, övergångar, rörelse '
                'i bilder), var och en med ett syfte och med prefers-reduced-motion, eller bestäm med skäl att något ska vara '
                'stilla. Pröva varje beteende med förhandsvisningens interaktionsväg och redovisa det med bilden. Skript står i ett '
                '<script> i sidan eller komponenten (Astro hashar det i sajtens CSP; inline-händelser som onclick= stoppas), '
                'eller i en React-ö när interaktionen kräver tillstånd (kunskap/beroenden.md).'),
    'granskning': ('Inspektera den fördjupade sidan som designchef och tillgänglighetsgranskare (Impeccables critique, polish och '
                   'audit, och Referos visuella kontroll mot referenslåset i RIKTNING.md): de konkreta bristerna i hierarki, '
                   'proportioner, beskärning, linjering, rytm och detaljer, och i tangentbord, fokus, reflow 320, reducerad '
                   'rörelse och axe. Rätta dem i en avgränsad omgång. Kör detektorn och pröva varje fynd mot ägarbesluten och '
                   'kundens domar. Idén och uttrycket står kvar: rätta brister, byt inte stil.'),
}


def nastlad_session(pid):
    import nastlad
    return bool(pid) and nastlad.lever(pid) and nastlad.ar_session(pid)


def kopiera_bilder(fran, till):
    till.mkdir(parents=True, exist_ok=True)
    for n in PASSBILDER:
        if (fran / n).is_file() and not (fran / n).is_symlink():
            shutil.copyfile(fran / n, till / n)
    return [rel(till / n) for n in PASSBILDER if (till / n).is_file()]


def pass_prompt(slug, kid, pass_, saknade=None, dom=None):
    """Passets uppdrag efter fördjupningen: ägarens dom som fördjupningen följer, kundens aktuella domar, designreglerna,
    metoden med Avgörandena (granskning 4, G1), rollens kärna och alternativ, interaktionsvägen och redovisningen i tre
    delar: kod ändrad, beteende prövat, visuell bedömning (Codex via ägaren 2026-10-05, punkt 9)."""
    d, s_ = kdir(slug, kid), rel(ksajt(slug, kid))
    forhand = '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s' % (slug, kid)
    minuter = (FRIST_PASS_OMFORSOK if saknade else FRIST_PASS) // 60
    return '\n'.join([
        'Du är specialisten för %s i skapandeflödet (kunskap/skapandeflodet.md) för en riktig verksamhet. Kandidaten %s' % (kompetens.PASSNAMN[pass_], kid),
        'är vald av ägaren och fördjupad i %s/src/; uppdraget står i %s och skaparens anteckningar, med referenslåset,' % (s_, rel(d / 'UPPDRAG.md')),
        'i %s. Specialisterna arbetar en gång var, efter varandra, på den färdiga sidan.' % rel(d / 'RIKTNING.md'),
        *(['', 'Ägarens dom som fördjupningen följer (%s): %s' % (dom.get('tid'), re.sub(r'\s+', ' ', str(dom.get('text') or '')).strip()[:1500] or '(utan text)')]
          if dom else []), '',
        *(['Förra försöket läste inte: %s. Läs dem hela först.' % ', '.join(saknade), ''] if saknade else []),
        'Din uppgift: ' + PASSUPPGIFT[pass_], '',
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG, aktuella=True), '',
        *regel_rader(), *metod_rader(slug, 'forfina'), '',
        *kompetens.prompt_rader(pass_, slug, kid), '',
        *skapande.fakta_rader(slug, atelje.UNDERLAG), '',
        'Arbetsgången, i avgränsade omgångar:',
        '1. Läs kärnan hel. Kör `%s --mellan --tillstand tangentbord,reflow,reducerad` (lägg till `--meny` med' % forhand,
        '   menyknappens CSS-väljare när sidan har en meny, och `--hover` eller `--fokus` för ett element du prövar; tidsgräns',
        '   600000 ms) och läs med Read bilderna och interaktionsvägen i FORHAND.md.',
        '2. Gör allt passet kräver i en omgång: ändra i %s/src/ (craft-floor.md direkt före ändringen).' % s_,
        '3. Kör förhandsvisningen igen med samma tillstånd och läs bilderna; rätta det som blev fel, högst en omgång till.',
        'Ändra inte riktningen, huvudreferensen, sakuppgifterna eller ett ägarbeslut: ett skillrecept eller ett detektorfynd',
        'som säger emot ägarens dom eller designreglerna följs inte. Tiden: högst %d minuter.' % minuter,
        'Svara i schemat med tre saker var för sig: kod_andrad (varje ändring med skill, vad, var och varför), beteende_provat',
        '(varje beteende du prövade: vad, hur, alltså kommandot och tillståndet, resultatet och bildens väg) och',
        'visuell_bedomning (bilden före och efter som du läst, omdömet battre, oforandrad, samre eller ej_bedomd, och skälet).',
        'Skriv ingen_andring med skälet om du inte ändrade något (annars tom), valda (alternativen du valde och läste), skills',
        'som inte passade och varför, och det som kvarstår.', atelje.MATERIAL])


def kompetenspass(slug, kid, pass_, fas, dom=None):
    """Ett pass efter fördjupningen på kandidatens renderade sida: före (versionen bevaras och bilderna sparas), sessionen
    med rollens kärna, alternativ, verktyg och MCP:er, och efter (fotograferingen). Blir sidan ofullständig, eller får den
    fler allvarliga axe-fynd än före, återställs versionen före; faller återställningen blir kandidaten ofullständig med
    skälet (granskning 4, G5). Kvittot ur transkripten säger vilka filer som lästs hela; läste passet inte hela kärnan får
    det ett omförsök, och båda sessionerna räknas tillsammans (G7). Redovisningen håller isär koden som ändrades,
    beteendet som prövades och den visuella bedömningen (Codex via ägaren 2026-10-05, punkt 9). Återupptagbart: ett klart
    pass görs inte om, och ett avbrutet återställs till versionen före innan det görs om (G4)."""
    nyckel = '%s:%s' % (fas, pass_)
    st = las_status(slug, kid)
    if ((st.get('kompetens') or {}).get(nyckel) or {}).get('klar'):
        return st
    d = kdir(slug, kid)
    pagar = st.get('pass_pagar') or {}
    if pagar.get('nyckel') == nyckel and pagar.get('fore'):  # ett pass som avbröts: versionen före gäller
        if nastlad_session(st.get('session_pid')):  # bara en kvarlevande session, aldrig en främmande process (G6)
            atelje.doda_trad(st.get('session_pid'))
        try:
            aterstall_och_fotografera(slug, kid, pagar['fore'])
        except Exception as e:  # noqa: BLE001
            return satt_status(slug, kid, 'ofullstandig', 'kompetenspasset %s avbröts, och återställningen till versionen före föll: %s'
                               % (pass_, str(e)[:200]), ta_bort=('session_pid',))
        st = satt_status(slug, kid, pagar.get('status') or st.get('status'), 'kompetenspasset %s avbröts; versionen före är återställd' % pass_,
                         ta_bort=('pass_pagar', 'session_pid'))
    status0, v0 = st.get('status'), st.get('version')
    axe0 = (st.get('axe') or {}).get('allvarliga')
    bevara_version(slug, kid, v0, bilder=True)
    satt_status(slug, kid, status0, st.get('skal', ''), pass_pagar={'nyckel': nyckel, 'fore': v0, 'status': status0})
    mal = d / 'kompetens' / re.sub(r'[^a-z0-9-]+', '-', '%s-%s' % (fas, pass_)).strip('-')
    fore = kopiera_bilder(d / 'bilder' / 'start', mal / 'fore')
    start, startad = time.monotonic(), nu()
    svar, saknade, kv, ut, sessioner = {}, None, {}, None, []
    for forsok in (1, 2):
        ut = d / ('svar-pass-%s-%s-%d.json' % (re.sub(r'[^a-z0-9-]+', '-', fas).strip('-'), pass_, forsok))
        try:
            svar = atelje.session(pass_prompt(slug, kid, pass_, saknade, dom), verktyg(slug, kid, komplettering=False) + kompetens.verktyg(pass_, slug, kid),
                                  ut, PASS_SCHEMA, 300, effort=EFFORT_SKISS, frist=FRIST_PASS_OMFORSOK if saknade else FRIST_PASS,
                                  nekas=andra_nekas(slug, kid), slug=slug,
                                  vid_start=lambda pid: satt_status(slug, kid, status0, 'kompetenspass %s' % pass_, session_pid=pid))
        except subprocess.TimeoutExpired:
            svar = {'avbruten': 'passets tid tog slut'}
        except RuntimeError as e:
            svar = {'avbruten': 'sessionen föll: %s' % str(e)[:200]}
        if atelje.STOPP.is_set():
            raise atelje.Stoppad('kompetenspasset avbröts av stoppet')
        sessioner.append(svar)
        kv = kompetens.kvitto(sessioner, pass_, skrivprefix=rel(ksajt(slug, kid) / 'src') + '/')
        if svar.get('avbruten') or not kv.get('verifierad') or not kv.get('saknas'):
            break
        saknade = [Path(f).name for f in kv['saknas']]
    efter_st = fotografera(slug, kid)
    aterstalld = None
    axe1 = (efter_st.get('axe') or {}).get('allvarliga')
    samre = isinstance(axe0, int) and isinstance(axe1, int) and axe1 > axe0
    if efter_st.get('status') != 'klar' or samre:  # passet bröt eller försämrade sidan: versionen före gäller
        orsak = ('fler allvarliga axe-fynd (%d mot %d före)' % (axe1, axe0)) if efter_st.get('status') == 'klar' else str(efter_st.get('skal'))[:200]
        try:
            aterstall_och_fotografera(slug, kid, v0)
            aterstalld = 'passet försämrade sidan (%s); versionen före är återställd' % orsak
        except Exception as e:  # noqa: BLE001 — då är kandidaten ofullständig, aldrig klar med en trasig sida (G5)
            aterstalld = 'passet försämrade sidan (%s) och återställningen föll: %s' % (orsak, str(e)[:200])
            status0 = 'ofullstandig'
    st = las_status(slug, kid)
    efter = kopiera_bilder(d / 'bilder' / 'start', mal / 'efter')
    so = svar.get('structured_output') or {}
    provat = []
    for b in so.get('beteende_provat') or []:
        if isinstance(b, dict):
            bild = str(b.get('bild') or '')
            provat.append(dict(b, bild_finns=bool(bild) and (atelje.ROOT / bild).is_file() and not (atelje.ROOT / bild).is_symlink()))
    andrad = st.get('version') != v0
    rec = {'fas': fas, 'pass': pass_, 'startad': startad, 'klar': nu(), 'sekunder': int(time.monotonic() - start),
           'kod_andrad': {'andrad': andrad, 'version_fore': v0, 'version_efter': st.get('version'), 'andringar': so.get('kod_andrad') or []},
           'beteende_provat': provat, 'visuell_bedomning': so.get('visuell_bedomning') or {},
           'version_fore': v0, 'version_efter': st.get('version'), 'andrad': andrad, 'andringar': so.get('kod_andrad') or [],
           'aterstalld': aterstalld, 'ingen_andring': so.get('ingen_andring') or '', 'valda': kv.get('valda') or [],
           'passade_inte': so.get('passade_inte') or [], 'kvarstar': so.get('kvarstar') or [], 'avbruten': svar.get('avbruten'),
           'svar': ut.name if ut else None,
           'kvitto': {k: kv.get(k) for k in ('verifierad', 'lasta', 'saknas', 'valda', 'skill_anrop', 'mcp_anrop')},
           'genomford': (not svar.get('avbruten') and bool(so) and not kv.get('saknas') and bool(provat)
                         and (andrad or bool(so.get('ingen_andring')))) if kv.get('verifierad') else None,
           'bilder': {'fore': fore, 'efter': efter}}
    kompetenser = dict(st.get('kompetens') or {})
    kompetenser[nyckel] = rec
    ny_status = 'ofullstandig' if status0 == 'ofullstandig' else (status0 if status0 in VISBARA else st.get('status'))
    return satt_status(slug, kid, ny_status, aterstalld if status0 == 'ofullstandig' else st.get('skal', ''), kompetens=kompetenser,
                       ta_bort=('session_pid', 'pass_pagar'))


def efter_fordjupning(slug, kid, dom):
    """Passen efter fördjupningen, en gång var och i ordning (interaktion och rörelse, sedan tillgänglighet och visuell
    granskning), sedan DESIGN.md-kontrollen på den slutliga koden (granskning 4, G11). Återupptagbart: ett avbrutet pass
    återställs och görs om, klara pass görs inte om (G4)."""
    st = las_status(slug, kid)
    for pass_ in KOMPETENSPASS:
        if st.get('status') not in ('forfinad',):
            break
        st = kompetenspass(slug, kid, pass_, 'fordjupa:%s' % dom.get('tid'), dom)
    k = designkontroll(slug, kid)
    skal = st.get('skal', '')
    if not k['ok'] and 'DESIGN.md har brister' not in skal:
        skal = (skal + '; DESIGN.md har brister').strip('; ')
    return satt_status(slug, kid, st.get('status'), skal, design_fel=k['fel'][:8], design_version=st.get('version'))


PLANPROVNING_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['kandidater', 'sammanfattning'],
    'properties': {
        'sammanfattning': {'type': 'string'},
        'kandidater': {'type': 'array', 'maxItems': 12, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['id', 'bedomning', 'andringar'],
            'properties': {'id': {'type': 'string'}, 'bedomning': {'type': 'string'},
                           'andringar': {'type': 'array', 'maxItems': 10, 'items': {
                               'type': 'object', 'additionalProperties': False, 'required': ['falt', 'nytt', 'skill', 'varfor'],
                               'properties': {k: {'type': 'string'} for k in ('falt', 'nytt', 'skill', 'varfor')}}}}}}}}


def planprovning(slug):
    """Specialisterna prövar planerarens designval (art direction och UX, med sina skills fullständiga instruktioner,
    verktyg och MCP:er): varje uppdrag bedöms mot kunden, materialet och referenserna, och ett fält ändras när
    kompetensen kräver det. Ändringarna skrivs in i planen och uppdragen; PLANPROVNING.md säger vad som ändrades och
    varför. Görs en gång per plan."""
    r = rot(slug)
    if (r / 'PLANPROVNING.json').is_file():
        return atelje.las_json(r / 'PLANPROVNING.json') or {}
    plan = atelje.las_json(r / 'KANDIDATPLAN.json') or {}
    ids = sorted(plan.get('kandidater') or {})
    # titel, hypotes och huvudreferens är låsta: hypotesen och titeln visas för ägaren före det blinda valet, och en ny
    # huvudreferens saknar sina referensbilder (granskning 4, G8)
    lasta = ('titel', 'hypotes', 'huvudreferens')
    falt = [f for f, _ in PLANFALT if f not in lasta]
    prompt = '\n'.join([
        'Du är specialisterna för art direction och UX i skapandeflödet (kunskap/skapandeflodet.md) för en riktig verksamhet.',
        'Planeraren har skrivit %d uppdrag; varje uppdrag går sedan till en egen skapare. Pröva planerarens designval i varje' % len(ids),
        'uppdrag mot kunden, kundens material och referenserna, innan någon bygger: bär riktningen, är typografin, bildstrategin,',
        'navigationen och förtroendet genomtänkta för just den idén, och skiljer sig uppdragen verkligen i hur informationen',
        'ordnas? Ändra ett fält bara när kompetensen kräver det, och skriv då fältets nya hela text; annars säg i bedömningen',
        'varför valen håller. Titel, hypotes och huvudreferens är låsta (titeln och hypotesen visas för ägaren före det blinda',
        'valet och nämner ingen referens eller sajt vid namn); en invändning mot dem skrivs i bedömningen.', '',
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG, aktuella=True), '',
        *regel_rader(), *metod_rader(slug, 'plan'), '',
        *kompetens.prompt_rader('planprovning', slug), '',
        'Planen: %s. Uppdragen: %s.' % (rel(r / 'KANDIDATPLAN.json'), ', '.join(rel(kdir(slug, k) / 'UPPDRAG.md') for k in ids)),
        *research_rader(slug), '', *material_rader(slug), '',
        *skapande.fakta_rader(slug, atelje.UNDERLAG), '',
        'Fälten du kan ändra: %s.' % ', '.join(falt),
        'Svara i schemat: per uppdrag (id som k01) bedömningen och ändringarna (fält, ny text, skill, varför); och en kort',
        'sammanfattning av vad specialisterna ändrade i planen.', atelje.MATERIAL])
    start = time.monotonic()
    svar = atelje.session(prompt, LASVERKTYG + kompetens.verktyg('planprovning', slug), r / 'svar-planprovning.json', PLANPROVNING_SCHEMA, 200,
                          atelje.MODELL, EFFORT_SKISS, FRIST_PLAN, slug=slug)
    so = svar.get('structured_output') or {}
    kv = kompetens.kvitto([svar], 'planprovning')
    andrade, ogjorda = [], []
    for x in so.get('kandidater') or []:
        kid = str(x.get('id') or '')
        for a in x.get('andringar') or []:
            if kid not in (plan.get('kandidater') or {}):
                ogjorda.append((kid, a, 'okänt uppdrag'))
            elif a.get('falt') in lasta:
                ogjorda.append((kid, a, 'fältet är låst'))
            elif a.get('falt') not in falt:
                ogjorda.append((kid, a, 'okänt fält'))
            elif not str(a.get('nytt') or '').strip():
                ogjorda.append((kid, a, 'ingen ny text'))
            else:
                plan['kandidater'][kid][a['falt']] = str(a['nytt']).strip()
                andrade.append((kid, a))
    if andrade:
        plan['provad'] = nu()
        (r / 'KANDIDATPLAN.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        for i, kid in enumerate(ids, 1):
            if any(k_ == kid for k_, _ in andrade):
                k = plan['kandidater'][kid]
                skriv_uppdrag(slug, kid, k, i, len(ids))
                satt_status(slug, kid, las_status(slug, kid).get('status') or 'planerad', 'uppdraget prövat av specialisterna',
                            titel=k.get('titel'), hypotes=k.get('hypotes'), huvudreferens=k.get('huvudreferens'))
    post = {'tid': nu(), 'sekunder': int(time.monotonic() - start), 'sammanfattning': so.get('sammanfattning') or '',
            'kandidater': [{'id': x.get('id'), 'bedomning': x.get('bedomning')} for x in so.get('kandidater') or []],
            'andrade': len(andrade), 'gjorda': [{'id': k_, **a} for k_, a in andrade],
            'ogjorda': [{'id': k_, 'falt': a.get('falt'), 'skal': s_} for k_, a, s_ in ogjorda],
            'kvitto': {k: kv.get(k) for k in ('verifierad', 'lasta', 'saknas', 'valda', 'skill_anrop', 'mcp_anrop')}}
    (r / 'PLANPROVNING.json').write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    rader = ['# Planprövningen · %s · %s' % (slug, post['tid']), '',
             'Specialisterna för art direction och UX prövade planerarens designval (kunskap/metodkarta.md, Kompetenserna).',
             'Filer lästa hela: %d av %d%s. Skillverktyget: %s. MCP-anrop: %s.' % (
                 len(kv.get('lasta') or []), len(kv.get('filer') or []), '' if kv.get('verifierad') else ' (ej verifierat)',
                 ', '.join(kv.get('skill_anrop') or []) or 'inga', ', '.join('%s ×%d' % i for i in (kv.get('mcp_anrop') or {}).items()) or 'inga'), '',
             str(post['sammanfattning']), '']
    for x in post['kandidater']:  # bara de ändringar som gjordes; de som inte gjordes står för sig med skälet (G8)
        rader += ['## %s' % x.get('id'), '', str(x.get('bedomning') or '')]
        rader += ['- **%s** (%s): %s — %s' % (a.get('falt'), a.get('skill'), str(a.get('nytt'))[:300], a.get('varfor'))
                  for a in post['gjorda'] if a.get('id') == x.get('id')]
        rader.append('')
    if post['ogjorda']:
        rader += ['## Föreslaget men inte gjort', ''] + ['- %s, %s: %s' % (x['id'], x['falt'], x['skal']) for x in post['ogjorda']] + ['']
    (r / 'PLANPROVNING.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return post


def behandla_skiss(slug, kid):
    """En skiss: det inledande försöket, och ett omförsök bara vid ett identifierat tekniskt fel (bygget föll, skärmbilderna
    saknas, sessionen föll). Ett försök som avbröts med processen sparas och startas om i ett nytt projekt (räknas som
    försök). En skiss som inte blir klar redovisas som ofullständig med skälet och det sparade arbetet."""
    st = las_status(slug, kid)
    if st.get('status') == 'under_arbete':  # processen dog mitt i försöket
        if nastlad_session(st.get('session_pid')):  # en kvarlevande session skriver aldrig i nästa försöks projekt (S3),
            atelje.doda_trad(st.get('session_pid'))  # och ett återanvänt pid tillhör aldrig någon annan (granskning 4, G6)
        mal = arkivera_forsok(slug, kid, st)
        forsoken = (st.get('forsok_tider') or []) + [{'forsok': st.get('forsok'), 'startad': st.get('startad'), 'klar': nu(), 'sekunder': None,
                                                      'utfall': 'avbruten', 'omforsok': False, 'tidsgrans': False, 'sparat': rel(mal)}]
        st = satt_status(slug, kid, 'avbruten', 'försök %s avbröts med processen; arbetet är sparat i %s' % (st.get('forsok'), rel(mal)),
                         sparat=rel(mal), forsok_tider=forsoken, ta_bort=('session_pid',))
    while True:
        s_, f_ = st.get('status'), int(st.get('forsok') or 0)
        if s_ in VISBARA:  # före ägarens val ändrar ingen annan session skissen (Codex via ägaren 2026-10-05, punkt 8)
            return st
        if (s_ == 'planerad' or s_ == 'avbruten') and f_ < MAX_FORSOK_SKISS:
            st = skissa(slug, kid)
        elif s_ in ('ofullstandig', 'fel') and st.get('tekniskt_fel') and f_ < MAX_FORSOK_SKISS:
            st = skissa(slug, kid, fel=st.get('skal') or 'okänt fel')
        else:
            if s_ == 'avbruten':
                st = satt_status(slug, kid, 'ofullstandig', 'avbröts i det sista försöket; arbetet är sparat i %s' % st.get('sparat'))
            return st


def siffror_utan_belagg(slug, kid):
    """Siffror i skissens synliga text som inte finns i kundens underlag (sanningskravet: hitta aldrig på siffror). En
    markering för ägaren, inget stopp: årtal och tal i underlaget är tillåtna."""
    import brev
    import copy_kontroll
    html_ = ksajt(slug, kid) / 'dist' / 'index.html'
    if not html_.is_file():
        return []
    text = ' '.join(t for _, t in copy_kontroll.synlig_text(html_, html_.read_text(encoding='utf-8', errors='replace')))
    u = atelje.UNDERLAG / slug
    rader = []
    for f in [u / n for n in ('VERKSAMHET.json', 'BRIEF.md', 'RESEARCH.md', 'BESTALLNING.md')] + [u / 'bilder' / 'BILDER.md', skapande.textfil(slug, atelje.UNDERLAG)]:
        if f.is_file():
            rader += f.read_text(encoding='utf-8', errors='replace').splitlines()
    tillatna = brev.tillatna_tal(rader) | {str(datetime.now(timezone.utc).year)}
    return sorted(set(brev.siffror_ok(text, tillatna)[1]))[:12]


def riktningens_referens(slug, kid):
    f = kdir(slug, kid) / 'RIKTNING.md'
    m = re.search(r'^\s*(?:[-*]\s+)?\**Huvudreferens\**\s*:\**\s*(.+?)\s+[—–-]+\s+(.+?)\s*$', f.read_text(encoding='utf-8'), re.M) if f.is_file() else None
    return {'namn': m.group(1).strip().strip('*`'), 'vad': m.group(2).strip()} if m else None


def i_researchen(slug, namn):
    """Finns huvudreferensens namn i researchen: planen, FORSKNING.md, REFERENSER.md, referenspaketen och tjänsternas
    rapporter? Redovisas per kandidat; en referens utanför researchen fäller inte kandidaten (granskning 2, N13)."""
    n = skapande.vik(namn or '').strip()
    if len(n) < 3:
        return False
    u = atelje.UNDERLAG / slug
    filer = [rot(slug) / 'KANDIDATPLAN.json', rot(slug) / 'FORSKNING.md', u / 'REFERENSER.md'] + sorted((u / 'referenser').glob('*/PAKET.md')) \
        + sorted((u / 'referenser' / 'tjanster').glob('TJANSTER*.md'))
    for f in filer:
        try:
            if f.is_file() and n in skapande.vik(f.read_text(encoding='utf-8', errors='replace')):
                return True
        except OSError:
            continue
    return False


def varvnummer(slug, kid):
    """Numren på startsidans hela förhandsvarv (varv-NN med varvets fyra bilder)."""
    v = kdir(slug, kid) / 'varv' / 'start'
    return sorted(int(p.name.split('-', 1)[1]) for p in v.glob('varv-*') if p.is_dir() and re.fullmatch(r'varv-\d{2,}', p.name) and forhandsvisa.hela(p)) if v.is_dir() else []


def varv_antal(slug, kid, efter=0):
    """Hela förhandsvarv av startsidan, efter varv nummer efter (förfiningens egna varv räknas från dess start)."""
    return len([n for n in varvnummer(slug, kid) if n > efter])


def tillampningen(slug, kid):
    """Hur många av varven i RIKTNING.md som namnger en avvikelse och vad i metoden som gav åtgärden: tillämpningen,
    redovisad skild från läsningen."""
    f = kdir(slug, kid) / 'RIKTNING.md'
    text = f.read_text(encoding='utf-8', errors='replace') if f.is_file() else ''
    varv = re.findall(r'^#{1,4}\s*(?:Förfining, )?[Vv]arv\s*\d+.*?(?=^#{1,4}\s|\Z)', text, re.M | re.S)
    metodord = re.compile(r'frontend-design|taste|impeccable|emil|better-|humanizer|bild\.md|metodkarta|designregler|craft-floor|copy-kontroll', re.I)
    return {'varv': len(varv), 'med_metod': sum(1 for v in varv if metodord.search(v))}


def designlage(slug, kid, design_text=None, css_ocksa=True):
    """Kandidatprojektets designläge: DESIGN.md och design.css som hör ihop (design_text None: ingen DESIGN.md, mallens
    design.css). css_ocksa False: versionen bevarade design.css i kod-src/, så bara DESIGN.md sätts."""
    sajt = ksajt(slug, kid)
    atelje.saker_vag(sajt, atelje.KUNDER / slug)
    css = sajt / 'src' / 'styles' / 'design.css'
    if (sajt / 'DESIGN.md').is_symlink():
        (sajt / 'DESIGN.md').unlink()
    if design_text is None:
        if (sajt / 'DESIGN.md').exists():
            (sajt / 'DESIGN.md').unlink()
        if MALL_DESIGN_CSS.is_file() and css_ocksa:
            css.parent.mkdir(parents=True, exist_ok=True)
            if css.is_symlink():
                css.unlink()
            shutil.copyfile(MALL_DESIGN_CSS, css)
        return
    (sajt / 'DESIGN.md').write_text(design_text, encoding='utf-8')
    if not css_ocksa:
        return
    import design
    v, fel = design.las(design_text)
    if v is not None and not design.validera(v):
        css.parent.mkdir(parents=True, exist_ok=True)
        if css.is_symlink():
            css.unlink()
        css.write_text(design.css(v), encoding='utf-8')


def kor_axe(slug, kid, url, sidor, ut):
    """axe på startsidan och undersidorna (med menyn öppen och formulären skickade tomma): teknisk kvalitet att redovisa
    och objektiva fel för förbättringsrundan. {'allvarliga', 'totalt', 'regler'} eller {'fel'}."""
    rc, out = prova.kor([prova.NODE, str(prova.KONTROLLER / 'axe.mjs'), '--url=' + url, '--sidor=' + ','.join(sidor), '--ut=' + str(ut),
                         '--tillstand=meny,formularfel'], timeout=300)
    a = atelje.las_json(Path(ut) / 'axe.json') or {}
    if not a:
        return {'fel': 'axe gav inget resultat (rc %s)' % rc}
    regler = sorted({'%s: %s' % (v.get('id'), v.get('help')) for r in a.get('rader') or [] for v in r.get('overtradelser') or []
                     if v.get('impact') in ('serious', 'critical')})
    return {'allvarliga': a.get('allvarliga'), 'totalt': a.get('totalt'), 'regler': regler[:12], 'version': a.get('axeVersion')}


def fotografera(slug, kid, skiss=None):
    """Bygg kandidatens projekt, fotografera startsidan i 390, 768 och 1440 och undersidan i 390 och 1440, kör axe,
    bevara koden, DESIGN.md och bilderna, och sätt status: klar för ägarens bedömning, eller ofullständig med skälen.
    skiss: bara startsidan, med menyns knapp klickad; hinder (startsidan saknas, bygget föll, bilderna saknas) gör
    skissen ofullständig, medan brister (konsolfel, spill, axe, siffror utan belägg, menyn, huvudreferensraden) markeras
    och skissen ändå går att bedöma. skiss None: efter versionen, en skiss i skissläget som inte fördjupats får skissens
    kontroller, också vid --fotografera och när en misslyckad fördjupning återställs (granskning 3, S5)."""
    d, sajt = kdir(slug, kid), ksajt(slug, kid)
    brister, markeringar = [], []
    kod = d / 'kod'
    atelje.saker_vag(d, rot(slug))
    if kod.is_symlink():
        kod.unlink()
    shutil.rmtree(kod, ignore_errors=True)
    pages = sajt / 'src' / 'pages'
    if (pages / 'index.astro').is_file():
        kopiera(pages, kod, lambda relp: relp.parts[0] not in MALLSIDOR)
    else:
        brister.append('startsidan saknas (src/pages/index.astro)')
    kodsrc = d / KODSRC  # komponenterna, layouterna, stilarna och de egna tillgångarna hör till versionen
    if kodsrc.is_symlink():
        kodsrc.unlink()
    shutil.rmtree(kodsrc, ignore_errors=True)
    if (sajt / 'src').is_dir() and not (sajt / 'src').is_symlink():
        kopiera(sajt / 'src', kodsrc, src_ovrigt)
    if (d / 'DESIGN.md').is_symlink() or (d / 'DESIGN.md').exists():  # versionens DESIGN.md är projektets, eller ingen
        (d / 'DESIGN.md').unlink()
    if (sajt / 'DESIGN.md').is_file() and not (sajt / 'DESIGN.md').is_symlink():
        shutil.copyfile(sajt / 'DESIGN.md', d / 'DESIGN.md')
    if skiss is None:  # efter versionen: en skissversion får skissens kontroller (granskning 3, S5)
        st0 = las_status(slug, kid)
        skiss = korlage(slug) == 'skiss' and (not st0.get('fordjupad') or version(slug, kid) in (st0.get('skissversioner') or []))
    bilder = d / 'bilder'
    if bilder.is_symlink():
        bilder.unlink()
    shutil.rmtree(bilder, ignore_errors=True)
    bilder.mkdir(parents=True)
    axe = None
    if not brister:
        rc, out = prova.bygg_inom_grans(sajt)
        if rc:
            brister.append('bygget föll: ' + prova.svans(out, 8))
    if not brister:
        insp = str(prova.KONTROLLER / 'webblasare' / 'inspektera.mjs')
        sidor = [('start', '/', '390,768,1440')] + ([] if skiss else [(forhandsvisa.sidnamn(v), v, '390,1440') for v in undersidor(slug, kid)[:2]])
        with prova.Server(sajt / 'dist') as srv:
            for namn, vag, vyer in sidor:
                ut = bilder / namn
                rc, out = prova.kor([prova.NODE, insp, '--adress', srv.url + vag, '--ut', str(ut), '--vyer', vyer, '--tillstand', 'inga']
                                    + (['--meny', MENYKNAPP] if skiss else []), timeout=300)
                saknas = [n for n in forhandsvisa.LAS if not (ut / n).is_file()]
                if saknas:
                    brister.append('%s: fotograferingen gav inte %s (rc %d)' % (vag, ', '.join(saknas), rc))
                ins = atelje.las_json(ut / 'INSPEKTION.json') or {}
                for vy, r in sorted((ins.get('vyer') or {}).items()):
                    fel = [x for x in r.get('konsol') or [] if x.get('typ') == 'error'] + list(r.get('sidfel') or [])
                    if fel:
                        (markeringar if skiss else brister).append('%s %s: konsolfel eller sidfel (%s)' % (vag, vy, str(fel[0].get('text', ''))[:120]))
                    if (r.get('spill') or {}).get('spill'):
                        (markeringar if skiss else brister).append('%s %s: sidled-spill' % (vag, vy))
                    meny = (r.get('tillstand') or {}).get('meny') if skiss and vy == '390' else None
                    if meny and meny.get('klickad') and meny.get('expanded') is None:  # granskning 3, S10
                        markeringar.append('390: menyns läge gick inte att avläsa efter klicket (aria-expanded saknas eller flera knappar)')
                    elif meny and meny.get('klickad') and meny.get('expanded') != 'true':
                        markeringar.append('390: menyns knapp öppnar ingenting (aria-expanded %s efter klick)' % meny.get('expanded'))
            try:
                axe = kor_axe(slug, kid, srv.url, [v for _n, v, _w in sidor], d / 'axe')
            except Exception as e:  # noqa: BLE001 — axe är redovisning, aldrig ett skäl att tappa kandidaten
                axe = {'fel': '%s: %s' % (type(e).__name__, str(e)[:200])}
    if skiss:  # skissläget: undersidan och varven hör till fördjupningen; bristerna markeras, skissen går att bedöma
        if not riktningens_referens(slug, kid):
            markeringar.append('RIKTNING.md saknar raden "Huvudreferens: <namn> — <vad den bär>"')
        if (axe or {}).get('allvarliga'):
            markeringar.append('axe: %s allvarliga fynd (%s)' % (axe['allvarliga'], '; '.join((axe.get('regler') or [])[:4])))
        elif not brister and (axe is None or axe.get('fel') or 'allvarliga' not in axe):  # en kontroll som inte kördes är ingen frånvaro av brister
            markeringar.append('axe kunde inte köras%s' % ((': ' + str(axe.get('fel'))[:160]) if (axe or {}).get('fel') else ''))
        siffror = siffror_utan_belagg(slug, kid) if not brister else []
        if siffror:
            markeringar.append('siffror i texten som inte finns i underlaget: %s' % ', '.join(siffror))
    else:
        if not undersidor(slug, kid):
            brister.append('undersidan eller tillståndet saknas (uppdraget anger vilken)')
        if not riktningens_referens(slug, kid):
            brister.append('RIKTNING.md saknar raden "Huvudreferens: <namn> — <vad den bär>"')
        if korlage(slug) == 'full' and varv_antal(slug, kid) < MIN_VARV:
            brister.append('%d förhandsvarv av minst %d' % (varv_antal(slug, kid), MIN_VARV))
    v = version(slug, kid)
    bevara_version(slug, kid, v, bilder=False)
    status = 'klar' if not brister else 'ofullstandig'
    skal = '; '.join(brister) or ('fotograferad; brister: ' + '; '.join(markeringar) if markeringar else 'fotograferad')
    sv = list(las_status(slug, kid).get('skissversioner') or [])
    if skiss and v not in sv:
        sv.append(v)
    return satt_status(slug, kid, status, skal, version=v, fotograferad=nu(), axe=axe, hinder=brister if skiss else None,
                       brister=markeringar if skiss else None, skissversioner=sv or None,
                       undersidor=undersidor(slug, kid), varv=varv_antal(slug, kid), tillampning=tillampningen(slug, kid),
                       huvudreferens=(riktningens_referens(slug, kid) or {}).get('namn'),
                       huvudreferens_i_researchen=i_researchen(slug, (riktningens_referens(slug, kid) or {}).get('namn')))


def bevara_version(slug, kid, v, bilder=True):
    """versioner/<v12>/: koden och DESIGN.md för varje fotograferad version (litet), och bilderna när en version ska
    kunna visas och jämföras: när ägaren väljer den, och före en förbättringsrunda (disken är knapp). Ger katalogen.
    En version som redan finns lämnas orörd."""
    d = kdir(slug, kid)
    mal = d / 'versioner' / v[:12]
    atelje.saker_vag(d / 'versioner', d)
    for under in ('kod', KODSRC) + (('bilder',) if bilder else ()):
        if (d / under).is_dir() and not (d / under).is_symlink() and not (mal / under).exists():
            mal.mkdir(parents=True, exist_ok=True)
            kopiera(d / under, mal / under)
    if (d / 'DESIGN.md').is_file() and not (d / 'DESIGN.md').is_symlink() and not (mal / 'DESIGN.md').exists():
        mal.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(d / 'DESIGN.md', mal / 'DESIGN.md')
    if mal.is_dir() and not (mal / 'VERSION').exists():
        (mal / 'VERSION').write_text(v + '\n', encoding='utf-8')
    return mal


def bevarad(slug, kid, v):
    """Är versionen bevarad med sin kod (och därmed möjlig att återställa och välja)?"""
    m = kdir(slug, kid) / 'versioner' / str(v or '')[:12]
    return bool(v) and (m / 'kod' / 'index.astro').is_file() and not (m / 'kod').is_symlink()


def aterstall(slug, kid, v):
    """Kandidatens hela designläge ur en bevarad version (versioner/<v12>/): sidorna, komponenterna, layouterna, stilarna
    och de egna tillgångarna (kod-src/), DESIGN.md och design.css; mallens sidor och kundens bilder står kvar. Bilderna
    tas ur versionen när de finns, så att versionen visas som den var. En version utan kod-src/ rör inte resten av src/."""
    m = kdir(slug, kid) / 'versioner' / v[:12]
    kalla = m / 'kod'
    src = ksajt(slug, kid) / 'src'
    pages = src / 'pages'
    atelje.saker_vag(pages, atelje.KUNDER / slug)
    if not kalla.is_dir() or kalla.is_symlink():
        raise RuntimeError('versionen %s av %s är inte bevarad' % (v[:12], kid))
    for p_ in list(pages.iterdir()):
        if p_.name not in MALLSIDOR:
            shutil.rmtree(p_) if p_.is_dir() and not p_.is_symlink() else p_.unlink()
    kopiera(kalla, pages)
    har_kodsrc = (m / KODSRC).is_dir() and not (m / KODSRC).is_symlink()
    if har_kodsrc:
        for katalog, kataloger, filer in os.walk(src, topdown=False, followlinks=False):  # det som tillkommit efter versionen
            for fn in filer:
                p_ = Path(katalog) / fn
                if src_ovrigt(p_.relative_to(src)):
                    p_.unlink()
            if Path(katalog) != src and not any(Path(katalog).iterdir()) and src_ovrigt(Path(katalog).relative_to(src)):
                Path(katalog).rmdir()
        kopiera(m / KODSRC, src)
    design = m / 'DESIGN.md'
    designlage(slug, kid, design.read_text(encoding='utf-8') if design.is_file() and not design.is_symlink() else None,
               css_ocksa=not har_kodsrc)  # versionens design.css står redan i kod-src/


def aterstall_och_fotografera(slug, kid, v):
    """Återställ versionen och fotografera den; versionen (kod och DESIGN.md) är densamma, så id:t består."""
    aterstall(slug, kid, v)
    st = fotografera(slug, kid)
    if st.get('version') != v:
        raise RuntimeError('återställningen gav en annan version (%s, väntat %s)' % (str(st.get('version'))[:12], v[:12]))
    return st


# --- jämförelsen och granskningen (rådgivande) ---

JAMFOR_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['par', 'sammanfattning'],
    'properties': {'sammanfattning': {'type': 'string'}, 'par': {'type': 'array', 'items': {
        'type': 'object', 'additionalProperties': False, 'required': ['a', 'b', 'grad', 'skal'],
        'properties': {'a': {'type': 'string'}, 'b': {'type': 'string'}, 'grad': {'type': 'string', 'enum': ['upprepning', 'nara']},
                       'skal': {'type': 'string'}}}}}}

# första passet: bilderna och interaktionen mot besökarens uppgift, utan skaparens motivering (synpunkterna på
# metodkartan 2026-10-05, punkt 5: granskaren ska bedöma det en besökare uppfattar, inte den förklarade avsikten)
KRITIK_A_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['forsta_intryck', 'uppgift', 'avvikelser', 'styrkor', 'niva', 'material'],
    'properties': {
        'forsta_intryck': {'type': 'object', 'additionalProperties': False, 'required': ['framgar', 'genomarbetat', 'skaver'],
                           'properties': {'framgar': {'type': 'string'}, 'genomarbetat': {'type': 'string'}, 'skaver': {'type': 'string'}}},
        'uppgift': {'type': 'object', 'additionalProperties': False, 'required': ['uppgift', 'kan_genomforas', 'belagg'],
                    'properties': {'uppgift': {'type': 'string'}, 'kan_genomforas': {'type': 'string', 'enum': ['ja', 'delvis', 'nej']},
                                   'belagg': {'type': 'string'}}},
        'styrkor': {'type': 'array', 'items': {'type': 'string'}},
        'niva': {'type': 'string', 'enum': ['over', 'nastan', 'generisk']}, 'material': {'type': 'string'},
        'avvikelser': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['var', 'vad', 'atgard', 'allvar', 'slag'],
            'properties': {'var': {'type': 'string'}, 'vad': {'type': 'string'}, 'atgard': {'type': 'string'},
                           'allvar': {'type': 'string', 'enum': ['hog', 'medel', 'lag']}, 'slag': {'type': 'string', 'enum': ['krav', 'smak']}}}}}}

# andra passet: designmotiveringen, med uppdraget och skaparens anteckningar
KRITIK_B_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['motiveringar', 'referens', 'helhet'],
    'properties': {
        'helhet': {'type': 'string'},
        'referens': {'type': 'object', 'additionalProperties': False, 'required': ['kvaliteten_bar', 'skal'],
                     'properties': {'kvaliteten_bar': {'type': 'string', 'enum': ['ja', 'delvis', 'nej']}, 'skal': {'type': 'string'}}},
        'motiveringar': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['nr', 'avsiktlig', 'valgrundad', 'skal'],
            'properties': {'nr': {'type': 'integer'}, 'avsiktlig': {'type': 'boolean'}, 'valgrundad': {'type': 'boolean'}, 'skal': {'type': 'string'}}}}}}


def uppdragets_bilder(slug, kid):
    """Referensbilderna i kandidatens UPPDRAG.md (rader "- underlag/<slug>/referenser/…"), de som finns."""
    f = kdir(slug, kid) / 'UPPDRAG.md'
    ut = []
    for rad in f.read_text(encoding='utf-8').splitlines() if f.is_file() else []:
        m = re.match(r'^- (underlag/%s/referenser/\S+\.(?:png|jpe?g|webp))$' % re.escape(slug), rad.strip())
        if m and (atelje.UNDERLAG / Path(m.group(1)).relative_to('underlag')).is_file():
            ut.append(m.group(1))
    return ut[:6]


def bilder_for(slug, kid, sida='start', vyer=('390', '1440'), slag=('forsta',)):
    b = kdir(slug, kid) / 'bilder' / sida
    return [b / ('vy-%s-%s.png' % (vy, s)) for vy in vyer for s in slag if (b / ('vy-%s-%s.png' % (vy, s))).is_file()]


def jamfor(slug):
    """Falsk variation: en granskare ser alla kandidaters första vyer och hela sidor och pekar ut upprepningar."""
    klara = [k for k in lista(slug) if las_status(slug, k).get('status') == 'klar']
    if len(klara) < 2:
        return None
    rader = []
    for kid in klara:
        rader += ['%s: %s' % (kid, ', '.join(rel(p) for p in bilder_for(slug, kid, vyer=('390', '1440'), slag=('forsta', 'hela')))),
                  '   idén: %s' % rel(kdir(slug, kid) / 'RIKTNING.md')]
    prompt = '\n'.join(['Du jämför %d kandidater till samma kunds startsida för att upptäcka falsk variation: två kandidater som är samma' % len(klara),
                        'struktur och berättelse med andra färger, typsnitt eller bilder. Titta på varje bild med Read (mobil och dator, första',
                        'vyn och hela sidan) och läs idén i RIKTNING.md. Verklig variation syns i innehållshierarkin och vad som möter',
                        'besökaren först, bildstrategin, det typografiska systemet, navigationen och hur förtroende byggs.', '',
                        *rader, '',
                        'Ange bara par som verkligen liknar varandra: grad "upprepning" när de är samma riktning, "nara" när de delar det mesta.',
                        'Skriv konkret vad som är lika.', atelje.MATERIAL])
    svar = atelje.session(prompt, LASVERKTYG, rot(slug) / 'svar-jamforelse.json', JAMFOR_SCHEMA, 120, GRANSKARE_MODELL, 'high', FRIST_GRANSKA, slug=slug)
    res = svar.get('structured_output') or {}
    res = {'tid': nu(), 'kandidater': klara, 'versioner': {k: las_status(slug, k).get('version') for k in klara},
           'par': [p for p in res.get('par') or [] if p.get('a') in klara and p.get('b') in klara and p.get('a') != p.get('b')],
           'sammanfattning': res.get('sammanfattning', '')}
    (rot(slug) / 'JAMFORELSE.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return res


def kritik(slug, kid, namn='KRITIK.json'):
    """Rådgivande granskning i två pass (synpunkterna på metodkartan 2026-10-05, punkt 5), egna sessioner med en annan
    modell än skaparen: (A) bilderna, tillgänglighetsträdet och axe mot besökarens uppgift i briefen, utan uppdraget och
    skaparens anteckningar (de nekas sessionen); (B) designmotiveringen: vilka avvikelser är avsiktliga och välgrundade,
    och bär kundens material referensens kvalitet. Läste A inte de första vyerna (last False), eller kan läsningen inte
    prövas (last None, inget transkript), styr granskningen ingen förbättringsrunda. Döljs vid ägarens första
    presentation."""
    st = las_status(slug, kid)
    d = kdir(slug, kid)
    n = len(list(d.glob('svar-kritik-a-*.json'))) + 1
    hela = bilder_for(slug, kid, vyer=('390', '768', '1440'), slag=('forsta', 'hela'))
    rutor = sorted((d / 'bilder' / 'start').glob('vy-390-ruta-*.png'))[:6] + sorted((d / 'bilder' / 'start').glob('vy-1440-ruta-*.png'))[:3]
    under = [p for v in st.get('undersidor') or [] for p in bilder_for(slug, kid, forhandsvisa.sidnamn(v), slag=('forsta', 'hela'))]
    aria = [p for p in ((d / 'bilder' / 'start' / 'vy-390-aria.txt'), (d / 'bilder' / 'start' / 'vy-1440-aria.txt')) if p.is_file()]
    axe = st.get('axe') or {}
    brief = atelje.UNDERLAG / slug / 'BRIEF.md'
    blind = nekas_utom(d, ('bilder',)) + nekas_utom(rot(slug), ('kandidater', 'metod')) + andra_nekas(slug, kid)
    prompt_a = '\n'.join([
        'Du granskar en kandidat till en riktig kunds startsida, rådgivande: ägaren dömer själv. Det här är granskningens',
        'första pass: bedöm det en besökare uppfattar, ur bilderna och sidans struktur, mot besökarens uppgift. Uppdraget',
        'och skaparens motivering läser du inte nu (de bedöms i ett andra pass). Ribban: kunskap/visuell-niva.md och',
        'ägarens domar nedan.',
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG), '',
        *regel_rader(), *metod_rader(slug, 'granska'), '',
        'Besökarens uppgifter och den primära handlingen: %s (§2 målgrupper och toppuppgifter, §4 primär handling).' % rel(brief),
        'Titta på varje bild med Read: startsidan i första vyn och hela i 390, 768 och 1440, rutorna och undersidan.',
        *['- ' + rel(p) for p in hela + rutor + under],
        'Sidans tillgänglighetsträd (rubriker, länkar, knappar, formulär; interaktionen): ' + (', '.join(rel(p) for p in aria) or 'saknas'),
        'axe (automatiskt): %s allvarliga av %s fynd%s.' % (axe.get('allvarliga', '?'), axe.get('totalt', '?'),
                                                           ('; ' + '; '.join(axe.get('regler') or [])) if axe.get('regler') else ''), '',
        'Svara: första intrycket (vad framgår, vad känns genomarbetat, vad skaver); den viktigaste besökaruppgiften och om',
        'den går att genomföra från startsidan, med belägg ur bilderna och trädet; och varje avvikelse: var (sektion och',
        'bredd), vad som brister konkret, åtgärden, allvaret (hog: syns direkt och sänker nivån; medel: syns vid läsning;',
        'lag: detalj) och slaget: krav när den bryter ett kvalitetskrav (läsbarhet, kontrast, fungerande interaktion,',
        'spill, sanning) eller hindrar besökarens uppgift; smak när den är ett estetiskt omdöme. Ange nivån (over, nastan,',
        'generisk) mot ribban och vilket material kunden saknar. Inga allmänna råd.', atelje.MATERIAL])
    ut_a = d / ('svar-kritik-a-%d.json' % n)
    svar = atelje.session(prompt_a, LASVERKTYG, ut_a, KRITIK_A_SCHEMA, 120, GRANSKARE_MODELL, 'high', FRIST_GRANSKA, nekas=blind, slug=slug)
    a = svar.get('structured_output')
    if not a:
        raise RuntimeError('granskningens första pass gav inget svar (%s)' % str(svar.get('subtype') or '?')[:200])
    las = bildkedja.lasning(svar.get('session_id'), {'forsta_vyerna': [rel(p) for p in bilder_for(slug, kid, vyer=('390', '1440'))]}) if svar.get('session_id') else {}
    last = (las.get('grupper') or {}).get('forsta_vyerna', {}).get('saknas') == [] if las.get('verifierad') else None
    hr = riktningens_referens(slug, kid)
    refbilder = [p for p, _t in (referensval.referens(slug, atelje.UNDERLAG, hr['namn']).get('bilder') or [])][:4] if hr else []
    for b in uppdragets_bilder(slug, kid):
        if len(refbilder) < 6:
            refbilder.append(atelje.UNDERLAG / Path(b).relative_to('underlag'))
    avv = a.get('avvikelser') or []
    prompt_b = '\n'.join([
        'Granskningens andra pass för samma kandidat: designmotiveringen. Det första passet (bilderna mot besökarens uppgift)',
        'står i %s. Läs nu uppdraget %s och skaparens anteckningar %s, och titta på referensbilderna:' % (rel(ut_a), rel(d / 'UPPDRAG.md'), rel(d / 'RIKTNING.md')),
        *['- ' + rel(p) for p in refbilder],
        'För varje avvikelse i första passet (nr 1–%d i den ordningen): är den avsiktlig (uppdraget eller anteckningarna' % len(avv),
        'säger att den är ett val), och är den välgrundad (valet har skäl i kundens behov, material eller huvudreferensen och',
        'fungerar för besökaren)? En avsiktlig men illa grundad avvikelse står kvar. Bedöm också om kundens material bär den',
        'kvalitet i referensen som uppdraget ville återskapa: jämför kandidatens bilder med referensbilderna i de fyra',
        'relationerna (bildens beskärning mot rubriken, de typografiska storlekarna och hierarkin, täta och luftiga sektioner',
        'och rytmen, navigation och interaktion mot innehållet), och sammanfatta helheten i två meningar.', atelje.MATERIAL])
    svar_b = atelje.session(prompt_b, LASVERKTYG, d / ('svar-kritik-b-%d.json' % n), KRITIK_B_SCHEMA, 80, GRANSKARE_MODELL, 'high', FRIST_GRANSKA,
                            nekas=andra_nekas(slug, kid), slug=slug)
    b = svar_b.get('structured_output') or {}
    mot = {m.get('nr'): m for m in b.get('motiveringar') or [] if isinstance(m, dict)}
    for i, x in enumerate(avv, 1):
        m = mot.get(i) or {}
        x.update(avsiktlig=bool(m.get('avsiktlig')), valgrundad=bool(m.get('valgrundad')), motivering=str(m.get('skal') or ''))
    res = {'forsta_intryck': a.get('forsta_intryck'), 'uppgift': a.get('uppgift'), 'styrkor': a.get('styrkor') or [], 'niva': a.get('niva'),
           'material': a.get('material'), 'avvikelser': avv, 'helhet': b.get('helhet') or '', 'referens': b.get('referens'),
           'andra_passet': bool(b), 'last': last, 'lasning': las.get('grupper'), 'tid': nu(), 'version': st.get('version'),
           'modell': GRANSKARE_MODELL, 'metod': metodinfo(slug, 'granska')['sha']}
    (d / namn).write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return res


def forbattra(slug, kid):
    """En förbättringsrunda för objektiva fel (granskningens krav-avvikelser av allvar hög eller medel som inte är
    välgrundade val, och axe:s allvarliga fynd); smak rättas inte före ägarens val. Föreversionen bevaras med bilderna,
    så att ägaren kan jämföra och välja den. Blir den förbättrade versionen ofullständig återställs föreversionen. Rundan
    märks med föreversionen medan den pågår, så att ett avbrott återställs vid återupptagningen."""
    d = kdir(slug, kid)
    k = atelje.las_json(d / 'KRITIK.json') or {}
    fore = las_status(slug, kid)
    lista_ = objektiva(slug, kid, k)
    if not lista_:
        return satt_status(slug, kid, fore.get('status') or 'klar', fore.get('skal', ''), forbattrad={'tid': nu(), 'behovdes_inte': True,
                                                                                                     'kritikens_version': k.get('version')})
    v_fore = fore['version']
    bevara_version(slug, kid, v_fore, bilder=True)
    satt_status(slug, kid, 'under_arbete', 'förbättringsrunda efter granskningen (%d objektiva fel)' % len(lista_), forbattras={'fore': v_fore, 'tid': nu()})
    ut = d / 'svar-forbattra.json'
    try:
        svar = atelje.session(skapar_prompt(slug, kid, forbattra=True), verktyg(slug, kid, komplettering=False), ut, max_turer=300, frist=FRIST_FORBATTRA,
                              nekas=andra_nekas(slug, kid), slug=slug)
    except (subprocess.TimeoutExpired, RuntimeError) as e:
        svar = {'avbruten': '%s: %s' % (type(e).__name__, str(e)[:300])}
    lasn = lasningen(slug, kid, ut, 'skapa')
    st = fotografera(slug, kid)
    skal = st.get('skal', '')
    if st['status'] != 'klar':
        try:
            st = aterstall_och_fotografera(slug, kid, v_fore)
            skal = 'förbättringsrundan gav en ofullständig version (%s); föreversionen är återställd' % skal[:300]
        except Exception as e:  # noqa: BLE001
            skal = '%s; återställningen föll: %s' % (skal[:300], str(e)[:200])
    return satt_status(slug, kid, st['status'], skal, ta_bort=('forbattras',),
                       forbattrad={'tid': nu(), 'avbruten': svar.get('avbruten'), 'kritikens_version': k.get('version'), 'fore': v_fore,
                                   'efter': st.get('version'), 'atgarder': lista_[:20], 'lasning': lasn})


# --- orkestreringen ---

def arkivera_projekt(slug, status):
    """En ny plan börjar med tomma projekt: förra körningens kunder/<slug>/kandidater flyttas till ateljéns arkiv
    (foregaende/), aldrig raderad, så att ingen ny kandidat ärver en gammal kandidats sidor."""
    k = atelje.KUNDER / slug / 'kandidater'
    if k.is_symlink():
        k.unlink()
        return None
    if not k.exists():
        return None
    mal = (atelje.ROOT / status['foregaende']) if status.get('foregaende') else atelje.ledigt_namn(atelje.foregaende(rot(slug)), nu().replace(':', '') + '-kandidater')
    atelje.saker_vag(mal, rot(slug))
    mal.mkdir(parents=True, exist_ok=True)
    shutil.move(str(k), str(atelje.ledigt_namn(mal, 'kunder-kandidater')))
    return mal


def granska_kandidat(slug, kid):
    """Granskningen av den aktuella versionen; den förra (som en förbättring svarade på) står kvar i KRITIK-fore.json, och
    faller den nya står den förra kvar som KRITIK.json."""
    d = kdir(slug, kid)
    flyttad = False
    if (d / 'KRITIK.json').is_file():
        os.replace(d / 'KRITIK.json', d / 'KRITIK-fore.json')
        flyttad = True
    try:
        return kritik(slug, kid)
    except Exception:
        if flyttad and not (d / 'KRITIK.json').exists():
            shutil.copyfile(d / 'KRITIK-fore.json', d / 'KRITIK.json')
        raise


def behandla(slug, kid):
    """En kandidats hela kedja: skaparsessionen och fotograferingen, granskningen i två pass och en förbättringsrunda för
    objektiva fel, och en ny granskning av den förbättrade versionen. Det som redan är gjort görs inte om; en avbruten
    förbättringsrunda återställs till föreversionen (räknas inte som ett skaparförsök)."""
    st = las_status(slug, kid)
    if st.get('forbattras'):  # förbättringsrundan avbröts: föreversionen gäller
        fore = st['forbattras'].get('fore')
        st = aterstall_och_fotografera(slug, kid, fore)
        st = satt_status(slug, kid, st['status'], 'förbättringsrundan avbröts; föreversionen är återställd', ta_bort=('forbattras',),
                         forbattrad={'tid': nu(), 'avbruten': 'avbrottet under förbättringsrundan', 'fore': fore, 'efter': fore})
    if st.get('status') not in VISBARA:
        if int(st.get('forsok') or 0) >= MAX_FORSOK:
            if st.get('status') != 'under_arbete':
                return st
            st = fotografera(slug, kid)  # den sista sessionen dog med processen: det den gjorde bedöms (granskning 2, N12)
        else:
            st = skapa(slug, kid)
    if st.get('status') != 'klar':
        return st
    d = kdir(slug, kid)
    try:
        if not st.get('forbattrad'):
            if (atelje.las_json(d / 'KRITIK.json') or {}).get('version') != st.get('version'):
                granska_kandidat(slug, kid)
            st = forbattra(slug, kid)
        if st.get('status') == 'klar' and (atelje.las_json(d / 'KRITIK.json') or {}).get('version') != st.get('version'):
            granska_kandidat(slug, kid)
    except Exception as e:  # noqa: BLE001 — en granskning som faller lämnar kandidaten som den är
        st = las_status(slug, kid)
        if st.get('forbattras'):  # förbättringsrundan föll efter sessionen: föreversionen gäller (granskning 2, N10)
            fore = st['forbattras'].get('fore')
            try:
                st = aterstall_och_fotografera(slug, kid, fore)
                satt_status(slug, kid, st['status'], 'förbättringsrundan föll (%s); föreversionen är återställd' % str(e)[:200], ta_bort=('forbattras',),
                            forbattrad={'tid': nu(), 'avbruten': '%s: %s' % (type(e).__name__, str(e)[:200]), 'fore': fore, 'efter': fore})
            except Exception as e2:  # noqa: BLE001 — märkningen står kvar: återupptagningen återställer föreversionen
                satt_status(slug, kid, 'fel', 'förbättringsrundan föll (%s) och återställningen föll (%s); återupptagningen återställer föreversionen'
                            % (str(e)[:200], str(e2)[:200]))
            return las_status(slug, kid)
        st = satt_status(slug, kid, 'klar' if st.get('status') == 'under_arbete' and st.get('version') else st.get('status') or 'klar',
                         'granskningen föll: %s' % str(e)[:200])
    return las_status(slug, kid)


def kor_pool(slug, ids, arbete, status, skriv, parallellt=None):
    kvar, las = list(ids), threading.Lock()

    def arbeta():
        while True:
            with las:
                if not kvar or atelje.STOPP.is_set():  # ett stopp: ingen ny kandidat påbörjas
                    return
                kid = kvar.pop(0)
            try:
                arbete(kid)
            except atelje.Stoppad:  # kandidaten står kvar under arbete: återupptagningen sparar och startar om försöket
                return
            except Exception as e:  # noqa: BLE001 — en kandidat som faller stoppar inte de andra
                satt_status(slug, kid, 'fel', '%s: %s' % (type(e).__name__, str(e)[:300]))
            with las:
                status['kandidater'] = {k: las_status(slug, k).get('status') for k in lista(slug)}
                skriv()

    tradar = [threading.Thread(target=arbeta) for _ in range(min(parallellt or PARALLELLT, len(kvar)))]
    for t_ in tradar:
        t_.start()
    for t_ in tradar:
        t_.join()


def kor(slug, status, skriv, n=None):
    """Hela utforskningen, återupptagbar: metoden, researchen och planen om de saknas, sedan varje kandidats kedja (några
    åt gången), ett andra försök för de ofullständiga, och jämförelsen. Sätter körningens steg; ägaren väljer sedan."""
    n = n or ANTAL
    r = rot(slug)
    r.mkdir(parents=True, exist_ok=True)
    lage = korlage(slug, status)
    status.update(kandidatflode=True, kandidatlage=lage)
    tider = status.setdefault('tider', {})
    tider.setdefault('start', status.get('startad') or nu())
    skriv()  # flaggan på disk före allt som kan falla (granskning 2, N1)
    status['metod'] = {s: m['sha'] for s, m in leverera_metod(slug).items()}
    if not lista(slug):
        arkiverad = arkivera_projekt(slug, status)
        if arkiverad:
            status['kandidater_arkiverade'] = rel(arkiverad)
        if not (r / 'FORSKNING.json').is_file():
            status['steg'] = 'forska'
            skriv()
            post = forska(slug, n, skiss=lage == 'skiss')
            status['forskning'] = {'nytt': post['nytt'], 'fel': post['fel']}
            tider['forskning'] = nu()
        status['steg'] = 'planera'
        skriv()
        planera(slug, n, lage)
        tider['plan'] = nu()
    ids = lista(slug)
    if lage == 'skiss' and not (r / 'PLANPROVNING.json').is_file() and all(las_status(slug, k).get('status') == 'planerad' for k in ids):
        status['steg'] = 'planprovning'  # specialisterna prövar planerarens designval innan någon bygger
        skriv()
        status['planprovning'] = {k: v for k, v in planprovning(slug).items() if k in ('andrade', 'sekunder')}
        tider['planprovning'] = nu()
    status.update(steg='skapa', kandidater={k: las_status(slug, k).get('status') for k in ids})
    skriv()
    if lage == 'skiss':  # ingen granskningspanel, förbättringsrunda eller jämförelse före ägarens val
        kor_pool(slug, ids, lambda kid: behandla_skiss(slug, kid), status, skriv, parallellt=min(PARALLELLT, MAX_PARALLELLT_SKISS))
        klara = [k for k in ids if las_status(slug, k).get('status') == 'klar']
        tider.update(forsta_valbara=forsta_valbara(slug, tider['start']), klar=nu())
        status.update(steg='klar_for_bedomning', klar=nu(), kandidater={k: las_status(slug, k).get('status') for k in ids},
                      skal='%d av %d skisser klara för ägarens bedömning' % (len(klara), len(ids)))
        skriv()
        return klara
    kor_pool(slug, ids, lambda kid: behandla(slug, kid), status, skriv)
    andra = [k for k in ids if las_status(slug, k).get('status') in ('ofullstandig', 'fel', 'avbruten', 'under_arbete')
             and int(las_status(slug, k).get('forsok') or 0) < MAX_FORSOK]
    if andra:  # ett andra skaparförsök med bristerna som kritik
        status.update(steg='skapa', andra_forsok=andra)
        skriv()
        kor_pool(slug, andra, lambda kid: behandla(slug, kid), status, skriv)
    status['steg'] = 'jamfora'
    skriv()
    try:
        jamfor(slug)
    except Exception as e:  # noqa: BLE001
        status['jamforelse_fel'] = '%s: %s' % (type(e).__name__, str(e)[:200])
    klara = [k for k in ids if las_status(slug, k).get('status') == 'klar']
    status.update(steg='klar_for_bedomning', klar=nu(), kandidater={k: las_status(slug, k).get('status') for k in ids},
                  skal='%d av %d kandidater klara för ägarens bedömning' % (len(klara), len(ids)))
    skriv()
    return klara


def forsta_valbara(slug, efter):
    """Tiden då den första kandidaten blev klar för ägarens bedömning i den här körningen (kandidaternas statuslogg)."""
    t = [x.get('tid') for k in lista(slug) for x in las_status(slug, k).get('logg') or [] if x.get('status') == 'klar' and x.get('tid', '') >= efter]
    return min(t) if t else None


# --- ägarens beslut (dashboardens vy Prototyp och kontroller/skapande.py dom, via atelje.doma) ---

def domd(slug):
    """Har ägaren fattat något beslut sedan kandidatplanen? Förklaringarna, granskningen och redovisningen visas först då."""
    pt = plan_tid(slug)
    return bool(pt) and any(d.get('kalla') in skapande.AGAREN and d.get('tid', '') > pt for d in skapande.domar(slug, atelje.UNDERLAG))


def valbara_versioner(st):
    """Versionerna ägaren kan välja: den aktuella, och föreversionen när en förbättringsrunda ändrade kandidaten."""
    ut = [st.get('version')]
    fore = (st.get('forbattrad') or {}).get('fore')
    if fore and fore not in ut:
        ut.append(fore)
    return [v for v in ut if v]


def prova_beslut(slug, beslut, kandidater):
    """Ägarens beslut i kandidatflödet prövat innan domen skrivs: varje kandidat finns, är klar för bedömning och har den
    version ägaren såg (ett val binds till kandidat och version; föreversionen före en förbättringsrunda kan väljas).
    Ger kandidaterna med etikett, titel, plan och metod; ValueError annars."""
    namn = etiketter(slug, lista(slug))
    if beslut in ('forkasta', 'ny_riktning') and not kandidater:
        return []
    if not isinstance(kandidater, list) or not kandidater:
        raise ValueError('välj minst en kandidat')
    ut, sedda = [], set()
    for k in kandidater:
        kid = str((k or {}).get('id') or '') if isinstance(k, dict) else ''
        if not ID.fullmatch(kid) or kid not in namn or kid in sedda:
            raise ValueError('okänd kandidat: %s' % kid[:20])
        sedda.add(kid)
        st = las_status(slug, kid)
        if st.get('status') not in VISBARA:
            raise ValueError('%s är %s, inte klar för bedömning' % (namn[kid], STATUSTEXT.get(st.get('status'), st.get('status'))))
        v = str(k.get('version') or '')
        tillatna = [st.get('version')] if beslut == 'godkand' else valbara_versioner(st)
        if v not in tillatna or (v != st.get('version') and not bevarad(slug, kid, v)):
            raise ValueError('%s har ändrats sedan du såg den (version %s, nu %s); ladda om vyn' % (namn[kid], v[:12], str(st.get('version') or '')[:12]))
        ut.append({'id': kid, 'version': v, 'etikett': namn[kid], 'titel': st.get('titel'), 'plan': plan_tid(slug),
                   'metod': (st.get('metod') or {}).get('forfina') if st.get('fordjupad') else (st.get('metod') or {}).get('skiss') or (st.get('metod') or {}).get('skapa')})
    if beslut == 'jamfor' and len(ut) < 2:
        raise ValueError('välj minst två kandidater att jämföra')
    if beslut == 'godkand':
        st = las_status(slug, ut[0]['id']) if len(ut) == 1 else {}
        if len(ut) != 1 or st.get('status') not in ('forfinad', 'godkand'):
            raise ValueError('godkänn en förfinad kandidat för helbygget; välj den först för vidareutveckling')
        if st.get('design_fel'):
            raise ValueError('%s: DESIGN.md har brister (%s); putsa vidare först' % (ut[0]['etikett'], '; '.join(st['design_fel'])[:300]))
    if beslut == 'putsa' and any(las_status(slug, k['id']).get('status') not in ('forfinad', 'vald', 'godkand') for k in ut):
        raise ValueError('putsa vidare gäller valda, förfinade eller godkända kandidater')
    return ut


def efter_beslut(slug, dom):
    """Kandidaternas status efter ägarens dom (domen är redan skriven). valj och putsa: de valda blir valda, och den valda
    versionens bilder bevaras; godkand: den godkända blir godkänd, en tidigare godkänd förfinad; forkasta och ny_riktning:
    alla synliga förkastas; jamfor ändrar ingen annan status (jämförelsen står i domen). Ett annat beslut än
    godkand, också jamfor, drar tillbaka godkännandet (atelje.aterkalla), och en godkänd kandidat blir då förfinad igen."""
    b = dom.get('beslut')
    kand = {k['id']: k for k in dom.get('kandidater') or [] if isinstance(k, dict) and k.get('id')}
    for kid in lista(slug):
        st = las_status(slug, kid)
        ny = None
        if kid in kand and b in ('valj', 'putsa'):
            ny = 'vald'
            bevara_version(slug, kid, kand[kid]['version'], bilder=kand[kid]['version'] == st.get('version'))
        elif kid in kand and b == 'godkand':
            ny = 'godkand'
            bevara_version(slug, kid, kand[kid]['version'], bilder=True)
        elif b in ('forkasta', 'ny_riktning') and st.get('status') in VISBARA:  # alla, också en godkänd (godkännandet dras tillbaka)
            ny = 'forkastad'
        elif st.get('status') == 'godkand':  # också jamfor: doma drar tillbaka godkännandet (granskning 2, N11)
            ny = 'forfinad'
        if ny and ny != st.get('status'):
            satt_status(slug, kid, ny, 'ägarens dom %s (%s)' % (dom.get('tid'), b), agarens_dom=dom.get('tid'))


def forbered_vinnare(slug, kid, v):
    """Den godkända kandidaten som vinnare, byggd i en tempkatalog i ateljén (inget gällande ändras här): kod/ (alla
    sidor), DESIGN.md, startsidans bilder i bilder/ och undersidornas i undersidor/, och VINNARE.json:s post med hasharna
    (granska.vinnarfel prövar dem). byt_in_vinnare lägger den på plats först när ägarens dom är skriven."""
    r, d = rot(slug), kdir(slug, kid)
    atelje.saker_vag(d, r)
    st = las_status(slug, kid)
    if st.get('version') != v:
        raise ValueError('%s har ändrats sedan ägaren såg den' % kid)
    if not (d / 'kod' / 'index.astro').is_file() or (d / 'kod').is_symlink():
        raise ValueError('%s saknar startsidan i kod/' % kid)
    tmp = Path(tempfile.mkdtemp(prefix='.vinnare-ny-', dir=r))
    filer = {'kod/' + k_: s for k_, s in kopiera(d / 'kod', tmp / 'kod').items()}
    if (d / KODSRC).is_dir() and not (d / KODSRC).is_symlink():  # komponenterna, layouterna och stilarna följer med
        filer.update({KODSRC + '/' + k_: s for k_, s in kopiera(d / KODSRC, tmp / KODSRC).items()})
    if (d / 'DESIGN.md').is_file() and not (d / 'DESIGN.md').is_symlink():
        shutil.copyfile(d / 'DESIGN.md', tmp / 'DESIGN.md')
    for sida in sorted(x for x in (d / 'bilder').iterdir() if x.is_dir() and not x.is_symlink()) if (d / 'bilder').is_dir() else []:
        mal = tmp / 'bilder' if sida.name == 'start' else tmp / 'undersidor' / sida.name
        for b in sorted(sida.glob('vy-*.png')):
            if b.is_symlink() or not b.is_file():
                continue
            mal.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(b, mal / b.name)
            filer[(mal / b.name).relative_to(tmp).as_posix()] = atelje.sha256_fil(mal / b.name)
    hr = riktningens_referens(slug, kid)
    if hr:  # referensbilderna ur uppdraget följer med: granskaren och byggaren jämför mot samma bilder
        hr['bilder'] = [[b, 'ur kandidatens uppdrag'] for b in uppdragets_bilder(slug, kid)]
    post = {'riktning': int(kid[1:]), 'kandidat': kid, 'version': v, 'etikett': etiketter(slug, lista(slug)).get(kid),
            'titel': st.get('titel'), 'huvudreferens': hr, 'tid': nu(), 'filer': filer, 'plan': plan_tid(slug),
            'overford': {'ok': True, 'skal': 'kandidatens sidor läggs i sajten när bygget tar vid (atelje.installera_godkand)'}}
    return tmp, post


def byt_in_vinnare(slug, tmp, post):
    """Den förberedda vinnaren på plats: en tidigare vinnare arkiveras (foregaende/), tempkatalogen blir vinnare/, och
    VINNARE.json skrivs."""
    r = rot(slug)
    atelje.arkivera_vinnare(r)
    vin = r / 'vinnare'
    if vin.exists() or vin.is_symlink():
        raise RuntimeError('underlag/%s/atelje/vinnare gick inte att flytta undan' % slug)
    os.replace(tmp, vin)
    atelje.skriv_vinnare(r, post)


# --- förfiningen efter ägarens val ---

def delar_rader(slug, dom, kid):
    """Det ägaren gillade, i den här och i andra kandidater, med vägarna till deras bilder och kod."""
    namn = etiketter(slug, lista(slug))
    rader = []
    for annan, text in sorted((dom.get('delar') or {}).items()) if isinstance(dom.get('delar'), dict) else []:
        if annan not in namn or not str(text).strip():
            continue
        d = kdir(slug, annan)
        bilder = [rel(p) for p in bilder_for(slug, annan, vyer=('390', '1440'), slag=('forsta', 'hela'))]
        rader.append('- %s (%s)%s: "%s". Bilder: %s; koden: %s' % (namn[annan], annan, ' (din kandidat)' if annan == kid else '',
                                                                 re.sub(r'\s+', ' ', str(text))[:800], ', '.join(bilder) or '–', rel(d / 'kod')))
    return rader


def forfina_prompt(slug, kid, dom):
    d, s = kdir(slug, kid), 'kunder/%s/kandidater/%s/sajt' % (slug, kid)
    forhand = '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s' % (slug, kid)
    tel = skapande.telefon(slug, atelje.UNDERLAG)
    namn = etiketter(slug, lista(slug)).get(kid, kid)
    delar = delar_rader(slug, dom, kid)
    kritiker = [rel(d / n) for n in ('KRITIK.json', 'KRITIK-fore.json') if (d / n).is_file()]
    return '\n'.join([
        'Du förfinar en kandidat i skapandeflödet (kunskap/skapandeflodet.md) för en riktig verksamhet. Ägaren såg',
        'kandidaterna sida vid sida och valde %s (%s) för vidareutveckling. Kandidatens projekt är %s; uppdraget och' % (namn, kid, s),
        'skaparens anteckningar står i %s och %s. Målet: en startsida och undersida som ägaren godkänner' % (rel(d / 'UPPDRAG.md'), rel(d / 'RIKTNING.md')),
        'för helbygget, i mobil, surfplatta och dator.', '',
        *(['Kandidaten är en skiss: första vyn och den viktigaste sektionen. Fördjupningen bygger i skissens form hela',
           'startsidan (de sektioner besökarens uppgifter kräver), den relevanta undersidan (uppdragets "Undersidan eller',
           'tillståndet") och besökarens centrala flöde (till exempel förfrågan: formuläret med felbesked vid fälten och',
           '/tack/), i mobil och dator. Det skissen redan visar ändras bara där ägarens ord eller en brist du ser kräver det.', '']
          if korlage(slug) == 'skiss' else []),
        *skapande.kritikrader(slug, underlag=atelje.UNDERLAG), '',
        *(['Det ägaren gillade (ta in en del ur en annan kandidat bara när den passar idén; anpassa den till kandidatens',
           'typografi, färger och rytm i stället för att klistra in den, och skriv i RIKTNING.md hur och varför):', *delar, '']
          if delar else []),
        *(['Den rådgivande granskningen (ägaren har sett den; den går före ingenting ägaren skrivit): ' + ', '.join(kritiker), ''] if kritiker else []),
        *skapande.fakta_rader(slug, atelje.UNDERLAG), '',
        *regel_rader(), *metod_rader(slug, 'forfina'), '',
        *kompetens.prompt_rader('fordjupa', slug, kid), '',
        'Arbetsgången, varv för varv (arbetsregeln är minst %d varv; antalet är ingen kvalitetsbedömning):' % atelje.MIN_VARV_FORFINA,
        '1. Kör `%s --mellan` (tidsgräns 600000 ms) och för undersidan `--sida /<väg>/`. Läs med Read mobilens,' % forhand,
        '   surfplattans och datorns första vy och hela sida, och huvudreferensens bilder i samma varv.',
        '2. Skriv i RIKTNING.md under "Förfining, varv N" vad du såg, mobilen först: ägarens ord punkt för punkt, bildurval och',
        '   beskärning, typografiska proportioner, linjering, innehållstäthet, sektionsövergångar; vad du rättar, hur, och vad i',
        '   metoden som gav åtgärden.',
        '3. Rätta i %s/src/pages/. Sakuppgifterna ändras aldrig; rubriker och ordning får bearbetas med formen.' % s,
        '4. Nästa varv bygger på det du såg. Sluta när ett varv inte visar något du kan förbättra och varje punkt i ägarens dom',
        '   är åtgärdad eller besvarad med skäl i RIKTNING.md. Bär grundidén inte ägarens kritik: byt det som bär, inte bara detaljer.',
        'DESIGN.md: skriv %s/DESIGN.md ur den förfinade sidan i formatet i kunskap/bygge-referens.md (värdena märkta' % s,
        '`uppmätt:` med var i din kod de står, `uppskattat:` eller `valt:` med skäl; huvudreferensen är den i RIKTNING.md), kör',
        '`.venv/bin/python kontroller/design.py %s --kandidat %s --skriv` och låt sidorna använda variablerna (importera' % (slug, kid),
        '../styles/design.css och använd var(--farg-…) och var(--typ-…)), så att DESIGN.md och koden säger samma sak. Kör',
        'förhandsvisningen igen efter det och läs bilderna.',
        'Typsnitt: `.venv/bin/python kontroller/typsnitt.py %s @fontsource-variable/<namn>`. Ringlänken är numret ur' % slug,
        'VERKSAMHET.json%s. Formulär postar till /api/forfragan/ och landar på /tack/ (lokal demonstration).' % ((' (%s)' % tel) if tel else ''), '',
        'Du är klar när den renderade sidan visar att %s, att %s, att %s och att %s, varje punkt i' % VISAR,
        'ägarens dom är åtgärdad eller besvarad, och DESIGN.md är giltig och används; skriv under "Visar" i RIKTNING.md vilken',
        'bild som visar var och en.', atelje.MATERIAL])


def forfina_verktyg(slug, kid):
    s = 'kunder/%s/kandidater/%s/sajt' % (slug, kid)
    return verktyg(slug, kid, komplettering=False) + kompetens.verktyg('fordjupa', slug, kid) + ['Write(./%s/DESIGN.md)' % s, 'Edit(./%s/DESIGN.md)' % s,
                                 'Bash(.venv/bin/python kontroller/design.py %s --kandidat %s --skriv)' % (slug, kid),
                                 'Bash(.venv/bin/python kontroller/design.py %s --kandidat %s)' % (slug, kid)]


def designkontroll(slug, kid):
    import design
    return design.kontroll(slug, kunder=atelje.KUNDER, underlag=atelje.UNDERLAG, kandidat=kid,
                           huvudreferens=(riktningens_referens(slug, kid) or {}).get('namn'))


def forfina_kandidat(slug, kid, v, dom):
    """En vald kandidat förfinas i sitt eget projekt: från den version ägaren valde, med ägarens ord och delar, och
    DESIGN.md i takt med koden. Förfiningen märks medan den pågår; en avbruten förfining tas om från den valda versionen
    vid återupptagningen. Gör förfiningen inget eget varv, eller blir resultatet ofullständigt, står den valda versionen
    kvar (status vald) med skälet; förfiningens egna varv räknas från dess start."""
    st = las_status(slug, kid)
    if st.get('status') == 'forfinad' and (st.get('forfining') or {}).get('dom') == dom.get('tid'):
        return efter_fordjupning(slug, kid, dom)  # redan förfinad efter domen: passen som saknas görs (granskning 4, G4)
    if st.get('forfining_pagar') and nastlad_session(st.get('session_pid')):  # en förfining som överlevde arbetaren (G16)
        atelje.doda_trad(st.get('session_pid'))
    if st.get('version') != v or st.get('forfining_pagar') or st.get('forbattras'):  # projektet är det ägaren valde, inget halvgjort
        aterstall_och_fotografera(slug, kid, v)
    bevara_version(slug, kid, v, bilder=True)
    start_varv = max(varvnummer(slug, kid) or [0])
    satt_status(slug, kid, 'under_arbete', 'förfining efter ägarens dom %s' % dom.get('tid'),
                forfining_pagar={'dom': dom.get('tid'), 'fran': v, 'start_varv': start_varv}, metod=dict(st.get('metod') or {}, forfina=metodinfo(slug, 'forfina')['sha']))
    d = kdir(slug, kid)
    ut = d / ('svar-forfina-%s.json' % nu().replace(':', ''))
    delar = [k for k in (dom.get('delar') or {}) if ID.fullmatch(str(k))] if isinstance(dom.get('delar'), dict) else []
    try:
        svar = atelje.session(forfina_prompt(slug, kid, dom), forfina_verktyg(slug, kid), ut, max_turer=400, frist=FRIST_FORFINA,
                              nekas=andra_nekas(slug, kid, utom=delar), slug=slug,
                              vid_start=lambda pid: satt_status(slug, kid, 'under_arbete', 'förfining efter ägarens dom %s' % dom.get('tid'),
                                                                session_pid=pid))  # --stoppa och återupptagningen hittar sessionen (G16)
    except (subprocess.TimeoutExpired, RuntimeError) as e:
        svar = {'avbruten': '%s: %s' % (type(e).__name__, str(e)[:300])}
    lasn = lasningen(slug, kid, ut, 'forfina')
    nya_varv = varv_antal(slug, kid, efter=start_varv)
    st = fotografera(slug, kid, skiss=False)  # den fördjupade sidan prövas helt: startsidan, undersidan och kontrollerna
    info = {'dom': dom.get('tid'), 'fran': v, 'klar': nu(), 'svar': ut.name, 'avbruten': svar.get('avbruten'), 'varv': nya_varv, 'lasning': lasn}
    if st['status'] != 'klar' or nya_varv == 0:
        skal = st.get('skal', '') if st['status'] != 'klar' else 'förfiningen gjorde inget eget förhandsvarv (%s)' % (svar.get('avbruten') or 'sessionen slutade')
        try:
            aterstall_och_fotografera(slug, kid, v)
        except Exception as e:  # noqa: BLE001
            skal += '; återställningen föll: %s' % str(e)[:200]
        return satt_status(slug, kid, 'vald', 'förfiningen gav ingen användbar version (%s); den valda versionen står kvar' % skal[:400],
                           ta_bort=('forfining_pagar',), forfining=info)
    k = designkontroll(slug, kid)
    skal = 'förfinad efter ägarens dom %s' % dom.get('tid')
    if nya_varv < atelje.MIN_VARV_FORFINA:
        skal += '; %d förfiningsvarv av arbetsregelns %d' % (nya_varv, atelje.MIN_VARV_FORFINA)
    if not k['ok']:
        skal += '; DESIGN.md har brister'
    satt_status(slug, kid, 'forfinad', skal, ta_bort=('forfining_pagar', 'session_pid'), forfining=info, design_fel=k['fel'][:8], fordjupad=True)
    return efter_fordjupning(slug, kid, dom)  # passen på den fördjupade sidan, och DESIGN.md-kontrollen efter dem


def forfina_valda(slug, status, skriv):
    """Läget valda (prototyp.py, efter ägarens beslut valj eller putsa): varje vald kandidat förfinas för sig, några åt
    gången; flera valda hålls isär. Återupptagbar: en klar förfining efter samma dom görs inte om, en avbruten tas om
    från den valda versionen. Sedan väntar flödet på ägarens bedömning igen."""
    status['kandidatflode'] = True  # först: faller något nedan är körningen ändå kandidatflödets (granskning 2, N1)
    dom = skapande.senaste(slug, underlag=atelje.UNDERLAG)
    if not dom or dom.get('beslut') not in ('valj', 'putsa') or not dom.get('kandidater'):
        raise RuntimeError('ägarens senaste dom väljer ingen kandidat att förfina')
    valda = [(k['id'], k['version']) for k in dom['kandidater'] if isinstance(k, dict) and k.get('id') in lista(slug)]
    status.update(steg='forfina', valda=[k for k, _ in valda], dom=dom.get('tid'))
    skriv()
    status['metod'] = {s: m['sha'] for s, m in leverera_metod(slug).items()}
    skriv()
    versioner = dict(valda)
    kor_pool(slug, [k for k, _ in valda], lambda kid: forfina_kandidat(slug, kid, versioner[kid], dom), status, skriv)
    for kid, v in valda:  # en förfining som föll med ett undantag: den valda versionen återställs (granskning 2, N10)
        st = las_status(slug, kid)
        if st.get('status') in ('fel', 'under_arbete'):
            skal = str(st.get('skal'))[:300]
            try:
                aterstall_och_fotografera(slug, kid, v)
                satt_status(slug, kid, 'vald', 'förfiningen föll (%s); den valda versionen är återställd' % skal, ta_bort=('forfining_pagar',))
            except Exception as e:  # noqa: BLE001 — märkningen står kvar: nästa förfining börjar från den valda versionen
                satt_status(slug, kid, 'vald', 'förfiningen föll (%s) och återställningen föll (%s); nästa förfining börjar från den valda versionen'
                            % (skal, str(e)[:200]), forfining_pagar=st.get('forfining_pagar') or {'fran': v})
    klara = [k for k, _ in valda if las_status(slug, k).get('status') == 'forfinad']
    status.update(steg='klar_for_bedomning', fas='forfining', klar=nu(), kandidater={k: las_status(slug, k).get('status') for k in lista(slug)},
                  skal='%d av %d valda kandidater förfinade; ägaren bedömer dem och godkänner en för helbygget' % (len(klara), len(valda)))
    skriv()
    return klara


# --- redovisningen ---

def material(slug, kid):
    """Avsnittet "Material" ur kandidatens RIKTNING.md: vad kunden saknar för riktningen."""
    f = kdir(slug, kid) / 'RIKTNING.md'
    text = f.read_text(encoding='utf-8', errors='replace') if f.is_file() else ''
    m = re.search(r'^#{1,4}\s*Material\b[^\n]*\n(.*?)(?=^#{1,4}\s|\Z)', text, re.M | re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip()[:600] if m else ''


def sessioner(slug, kid):
    ut = []
    for f in sorted(kdir(slug, kid).glob('svar-*.json')):
        s = atelje.las_json(f) or {}
        ut.append({'svar': f.name, 'turer': s.get('num_turns'), 'minuter': round(s['duration_ms'] / 60000) if s.get('duration_ms') else None,
                   'kostnad': s.get('total_cost_usd'), 'session_id': s.get('session_id')})
    return ut


def minuter_mellan(a, b):
    try:
        return round((datetime.fromisoformat(str(b).replace('Z', '+00:00')) - datetime.fromisoformat(str(a).replace('Z', '+00:00'))).total_seconds() / 60)
    except (TypeError, ValueError):
        return None


def utkast_antal(slug, kid):
    """Antalet märkta utkast och platshållare i skissens synliga text (det ägaren eller kunden behöver fylla)."""
    import copy_kontroll
    html_ = ksajt(slug, kid) / 'dist' / 'index.html'
    if not html_.is_file():
        return 0
    rader = [t for _, t in copy_kontroll.synlig_text(html_, html_.read_text(encoding='utf-8', errors='replace'))]
    return sum(1 for t in rader if re.search(r'\butkast\b|\bplatshållare\b|\bsaknas\s*:', t, re.I))


PASSORDNING = ('skapa', 'ux', 'rorelse', 'mobil', 'kritik')


def kompetens_rader(slug, ids, namn):
    """Kompetensernas arbete i redovisningen: planprövningen, och per kandidat och pass om passet genomfördes (filerna
    lästa hela, ändringen synlig eller motiverad), kvittot, ändringarna och före och efter (ägarens ord 2026-10-05
    18:15Z och Codex samma dag: visa förbättringen i sidan, inte bara att en fil öppnades)."""
    r = rot(slug)
    pp = atelje.las_json(r / 'PLANPROVNING.json') or {}
    rader = ['', '## Kompetensernas arbete', '']
    if pp:
        kv = pp.get('kvitto') or {}
        rader += ['**Planprövningen** (art direction och UX prövade planerarens designval): %d fält ändrade; filer lästa hela %d av %d%s; '
                  'skillverktyget %s; MCP %s. %s' % (
                      pp.get('andrade') or 0, len(kv.get('lasta') or []), len(kv.get('lasta') or []) + len(kv.get('saknas') or []),
                      '' if kv.get('verifierad') else ' (ej verifierat)', ', '.join(kv.get('skill_anrop') or []) or 'inte använt',
                      ', '.join('%s ×%s' % i for i in (kv.get('mcp_anrop') or {}).items()) or 'inga anrop', str(pp.get('sammanfattning') or '')[:600]), '']
    rader += ['| Kandidat | Pass | Genomfört | Filer lästa hela | Skill / MCP | Sidan ändrad | Vad kompetensen ändrade | Före → efter |',
              '|---|---|---|---|---|---|---|---|']
    for kid in ids:
        st = las_status(slug, kid)
        recs = st.get('kompetens') or {}
        for pass_ in PASSORDNING:
            for nyckel, rec in sorted(recs.items()):
                if rec.get('pass') != pass_:
                    continue
                kv = rec.get('kvitto') or {}
                lasta, saknas = len(kv.get('lasta') or []), len(kv.get('saknas') or [])
                ändr = rec.get('andringar') or []
                vad = '; '.join('%s: %s' % (a.get('skill'), a.get('vad')) for a in ändr[:3]) + (' (+%d)' % (len(ändr) - 3) if len(ändr) > 3 else '')
                if not ändr:
                    vad = ('ingen ändring: ' + str(rec.get('ingen_andring'))[:160]) if rec.get('ingen_andring') else (
                        'skaparens %d varv' % rec.get('varv') if pass_ == 'skapa' else '–')
                gen = {True: 'ja', False: 'nej', None: 'ej verifierat'}[rec.get('genomford')]
                if rec.get('aterstalld'):
                    gen += ' (återställt: %s)' % str(rec['aterstalld'])[:80]
                if rec.get('avbruten'):
                    gen += ' (%s)' % str(rec['avbruten'])[:60]
                b = rec.get('bilder') or {}
                bild = ('%s → %s' % ((b.get('fore') or ['–'])[0], (b.get('efter') or ['–'])[0])) if b.get('fore') or b.get('efter') else '–'
                rader.append('| %s (%s) | %s%s | %s | %d av %d | %s | %s | %s | %s |' % (
                    namn.get(kid), kid, pass_, '' if nyckel.startswith('skiss:') else ' (%s)' % nyckel.split(':')[0], gen, lasta, lasta + saknas,
                    (', '.join(kv.get('skill_anrop') or []) or '–') + ' / ' + (', '.join('%s ×%s' % (m.split('__')[1], n_) for m, n_ in (kv.get('mcp_anrop') or {}).items()) or '–'),
                    'ja' if rec.get('andrad') else ('nej' if pass_ != 'skapa' else '–'), vad.replace('|', '/')[:400], bild))
    return rader


def redovisa_skiss(slug, status):
    """REDOVISNING.md för skissläget (ägarens uppdrag 2026-10-05 16:25Z, punkt 7 och 8): tiderna, varje kandidat med status,
    minuter, försök, brister ur de snabba kontrollerna, det som tillfördes uppdraget och verktygen som användes, de
    ofullständiga med skäl och sparat arbete, och det som behöver mänsklig bedömning. Inget betyg och ingen vinnare."""
    r = rot(slug)
    ids = lista(slug)
    namn = etiketter(slug, ids)
    t = status.get('tider') or {}
    f = atelje.las_json(r / 'FORSKNING.json') or {}
    m = metodinfo(slug, 'skiss')
    rader = ['# Redovisning · %s · %s' % (slug, nu()), '',
             'Skissläget (kontroller/kandidater.py): skaparna med %s, effort %s; högst %d samtidigt, %d minuter per inledande' % (
                 status.get('modell'), EFFORT_SKISS, min(PARALLELLT, MAX_PARALLELLT_SKISS), FRIST_SKISS // 60),
             'försök med verktygsväntan, ett omförsök på %d minuter bara vid ett identifierat tekniskt fel. Ingen granskningspanel' % (FRIST_SKISS_OMFORSOK // 60),
             'och ingen förbättringsrunda före ägarens val; ingen modell har bedömt skisserna.', '',
             '## Tiderna', '',
             '- startad %s; researchen klar %s; planen klar %s; första valbara skissen %s; klar %s.' % (
                 t.get('start', '–'), t.get('forskning', '–'), t.get('plan', '–'), t.get('forsta_valbara') or '–', t.get('klar') or '–'),
             '- väntan till första valbara skissen: %s minuter; total väntan: %s minuter.' % (
                 minuter_mellan(t.get('start'), t.get('forsta_valbara')) if t.get('forsta_valbara') else '–',
                 minuter_mellan(t.get('start'), t.get('klar')) if t.get('klar') else '–'), '',
             '## Det som tillfördes varje uppdrag', '',
             '- UPPDRAG.md ur planen (designuppdraget, besökarens uppgift, den viktigaste sektionen, huvudreferensen och',
             '  referensbilderna med vad de ska lära), kundens verifierade fakta (VERKSAMHET.json, textunderlaget) och materialet',
             '  (BILDER.md, bilderna i projektet).',
             '- Metoden (hash %s): %s, med kvalitetskraven, besluten med räckvidd och avgörandena; utdragen att slå upp: %s.' % (
                 m['sha'][:12], ', '.join(Path(x).name for x in m['delar']['före']), ', '.join(Path(x).name for x in m['delar'].get('uppslag') or []) or '–'),
             '- Historiken (LARDOMAR.md, kundens äldre domar, riktningshistoriken) som uppslag, inte som obligatorisk läsning.', '',
             '## Kandidaterna', '',
             '| Kandidat | Status | Minuter | Försök | Brister ur de snabba kontrollerna | Referensbilder | Utkast och platshållare | Öppnat ur metoden | Verktyg |',
             '|---|---|---|---|---|---|---|---|---|']
    fallna, behov = [], []
    for kid in ids:
        st = las_status(slug, kid)
        ft = st.get('forsok_tider') or []
        anv = st.get('anvandning') or {}
        rader.append('| %s (%s) | %s | %s | %s | %s | %d | %d | %s | %s |' % (
            namn.get(kid), kid, STATUSTEXT.get(st.get('status'), st.get('status')),
            round(sum(x.get('sekunder') or 0 for x in ft) / 60) if ft else '–',
            ' + '.join('%d%s' % (x.get('forsok') or 0, ' (omförsök)' if x.get('omforsok') else ' (tiden slut)' if x.get('tidsgrans') else '') for x in ft) or '–',
            ('; '.join(st.get('brister') or []) or ('–' if st.get('status') in VISBARA else str(st.get('skal') or '')[:160])).replace('|', '/'),
            len(uppdragets_bilder(slug, kid)), utkast_antal(slug, kid),
            ', '.join(anv.get('metoddelar') or []) or ('–' if anv.get('transkript') else 'ej i transkript'),
            ', '.join(anv.get('verktyg') or []) or '–'))
        if st.get('status') not in VISBARA:
            fallna.append('- %s (%s): %s%s' % (namn.get(kid), kid, st.get('skal'), ('; sparat arbete: ' + st['sparat']) if st.get('sparat') else
                                                ('; arbetet står kvar i %s och %s' % (rel(ksajt(slug, kid)), rel(kdir(slug, kid))))))
        mat = material(slug, kid)
        if mat:
            behov.append('- %s (%s): %s' % (namn.get(kid), kid, mat))
    rader += ['', '## Ofullständiga och fallna', ''] + (fallna or ['Inga.'])
    rader += kompetens_rader(slug, ids, namn)
    rader += ['', '## Det som behöver mänsklig bedömning', '',
              '- Ägarens val: riktning, kvalitet och variation. Ingen modell har bedömt eller rangordnat skisserna.',
              '- Utkast och platshållare (kolumnen ovan): text och bilder som kunden eller ägaren behöver fylla.',
              '- Bristerna ur de snabba kontrollerna rättas i fördjupningen, utan att ändra den valda skissens uttryck.',
              '- Tillgängligheten: axe kör automatiskt på startsidan; skärmläsare, hela flödet med tangentbord och 200–400 % zoom',
              '  prövas av en människa i fördjupningen.',
              '- Besökarprovet: varje uppdrag har en uppgift att pröva med relevanta besökare ("Hur förslaget prövas"); ännu inte',
              '  observerat.', '',
              '## Researchen', '',
              '- %s' % ('ny research i den här körningen: referenspaketet %s (nya sajter: %s), tjänsterna %s; släppta: %d%s' % (
                  (f.get('nytt') or {}).get('paket') or 'inget nytt', ', '.join((f.get('nytt') or {}).get('sajter') or []) or 'inga',
                  (f.get('nytt') or {}).get('tjanster') or 'inget nytt', len(f.get('slappta') or []), ('; fel: %s' % f['fel']) if f.get('fel') else '')
                        if f else 'ingen research i den här körningen'),
              '- återanvänt: referenspaketet %s, tjänsternas undersökning %s' % (
                  (f.get('fore') or {}).get('paket') or '–', (f.get('fore') or {}).get('tjanster') or '–'), '',
              '## Materialbehov', ''] + (behov or ['Inga angivna.'])
    (r / 'REDOVISNING.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return r / 'REDOVISNING.md'


def redovisa(slug, status):
    """REDOVISNING.md för kandidatflödet, med tre bedömningar skilda åt (synpunkterna på metodkartan 2026-10-05): ägarens
    visuella ribba (ägarens domar; granskningens nivå är rådgivande), besökarnas uppgifter (granskningens första pass) och
    den tekniska kvaliteten (bygge, konsol, spill, axe), och tillgänglighetens täckning med det som kräver en människa.
    Dessutom researchen, metoden (läsningen och tillämpningen var för sig), sessionerna, falsk variation och
    materialbehoven. Kostnaden är listpris, inte förbrukad kvot."""
    if korlage(slug, status) == 'skiss':
        return redovisa_skiss(slug, status)
    r = rot(slug)
    namn = etiketter(slug, lista(slug))
    f = atelje.las_json(r / 'FORSKNING.json') or {}
    rader = ['# Redovisning · %s · %s' % (slug, nu()), '',
             'Kandidatflödet (kontroller/kandidater.py). Läge %s · steg %s · modell %s %s · startad %s · metoden %s.' % (
                 status.get('lage'), status.get('steg'), status.get('modell'), status.get('effort'), status.get('startad'),
                 ', '.join('%s %s' % (s, str(h)[:12]) for s, h in sorted((status.get('metod') or {}).items())) or '–'), '',
             '## Researchen', '']
    if f:
        nytt = f.get('nytt') or {}
        rader += ['- antaganden om besökarna: %d (FORSKNING.md)' % len(f.get('antaganden') or []),
                  '- nytt referenspaket: %s (nyfångade sajter: %s)' % (nytt.get('paket') or 'inget', ', '.join(nytt.get('sajter') or []) or 'inga'),
                  '- nya tjänstesökningar: %s; frågor: %d; släppta: %d' % (nytt.get('tjanster') or 'inga', len(f.get('fragor') or []), len(f.get('slappta') or [])),
                  '- fel: %s' % (f.get('fel') or 'inga')]
    else:
        rader.append('Ingen research i den här körningen.')
    rader += ['', '## Tre bedömningar, var för sig', '',
              '**Ägarens visuella ribba** avgör ägaren i dashboarden; granskningens nivå nedan är rådgivande.', '',
              '| Kandidat | Status | Besökarens uppgift (granskningen) | Granskningens nivå | Teknisk kvalitet | axe allvarliga |', '|---|---|---|---|---|---|']
    tot_min, tot_usd, fallna, behov, metodrader, utanfor, fore_granskning = 0, 0.0, [], [], [], [], []
    for kid in lista(slug):
        st = las_status(slug, kid)
        k = atelje.las_json(kdir(slug, kid) / 'KRITIK.json') or {}
        upp = k.get('uppgift') or {}
        axe = st.get('axe') or {}
        teknik = 'bygger, inga konsolfel eller spill' if st.get('status') in VISBARA else str(st.get('skal') or '')[:120]
        rader.append('| %s (%s) %s | %s | %s%s | %s%s | %s | %s |' % (
            namn.get(kid), kid, str(st.get('titel') or '').replace('|', '/'), STATUSTEXT.get(st.get('status'), st.get('status')),
            upp.get('kan_genomforas', '–'), (': ' + str(upp.get('uppgift') or '').replace('|', '/')[:80]) if upp else '',
            k.get('niva') or '–', '' if not k or k.get('last') is True else ' (bilderna olästa)' if k.get('last') is False else ' (läsningen ej prövad)', teknik.replace('|', '/'),
            axe.get('allvarliga', axe.get('fel', '–'))))
        ss = sessioner(slug, kid)
        tot_min += sum(x['minuter'] or 0 for x in ss)
        tot_usd += sum(float(x['kostnad'] or 0) for x in ss)
        lasn, til = st.get('lasning') or {}, st.get('tillampning') or {}
        metodrader.append('| %s (%s) | %s | %s | %s | %s |' % (
            namn.get(kid), kid, ('ja' if lasn.get('metod_fore_forsta_skrivning') else ('efter' if lasn.get('metod_last') else ('nej' if lasn.get('verifierad') else 'ej verifierad')))
            + ((' (bara delar: %s)' % ', '.join(Path(x).name for x in lasn['metod_delvis'])) if lasn.get('metod_delvis') else ''),
            ', '.join('%s %d/%d' % (x['varv'], x['lasta'], x['kravda']) for x in lasn.get('varv') or []) or '–',
            '%s av %s' % (til.get('med_metod', '–'), til.get('varv', '–')), len(ss)))
        if st.get('status') in ('fel', 'ofullstandig', 'avbruten'):
            fallna.append('- %s (%s): %s' % (namn.get(kid), kid, st.get('skal')))
        if st.get('huvudreferens') and st.get('huvudreferens_i_researchen') is False:
            utanfor.append('- %s (%s): %s' % (namn.get(kid), kid, st.get('huvudreferens')))
        if k and k.get('version') and k.get('version') != st.get('version'):
            fore_granskning.append('- %s (%s): granskningen gäller version %s, kandidaten är nu %s%s' % (
                namn.get(kid), kid, str(k.get('version'))[:12], str(st.get('version'))[:12], ' (förfinad)' if st.get('status') in ('forfinad', 'godkand') else ''))
        m = material(slug, kid)
        if m:
            behov.append('- %s (%s): %s' % (namn.get(kid), kid, m))
    rader += ['', '**Tillgänglighetens täckning:** axe (WCAG 2.2 A och AA, best practice) på startsidan och undersidan i mobil och dator,',
              'med menyn öppen och formulären skickade tomma; kontrast, etiketter, landmärken och namn på kontroller prövas där.',
              'En människa behöver fortfarande pröva: skärmläsare (VoiceOver), hela flödet med bara tangentbord, 200 och 400 %',
              'zoom, och att alt-texterna och länktexterna är begripliga i sitt sammanhang (W3C: utvärdering med användare).', '',
              '**Besökarprovet** (skilt från ägarens visuella val): varje kandidat har en uppgift att pröva med relevanta besökare',
              '(UPPDRAG.md, "Hur förslaget prövas"); i en prospektdemo är det ännu inte observerat, och i ett skarpt uppdrag prövas',
              'den valda med några besökare före lansering: var tvekar de, och vilken information saknas.', '',
              '## Metoden: läsningen och tillämpningen var för sig', '',
              '| Kandidat | Metoden läst före första ändringen | Varvens bilder lästa (per varv) | Varv som namnger metoden | Sessioner |', '|---|---|---|---|---|',
              *metodrader, '',
              'Sammanlagt: %d minuter i sessioner, %.2f USD i listpris (förbrukningen räknas i kvot, inte USD).' % (tot_min, tot_usd), '',
              '## Kandidater som föll eller blev ofullständiga', ''] + (fallna or ['Inga.'])
    if utanfor:
        rader += ['', '## Huvudreferens som inte finns i researchen', ''] + utanfor
    if fore_granskning:
        rader += ['', '## Granskningen gäller en tidigare version', '',
                  'Efter förbättringsrundan eller förfiningen körs ingen ny granskning; ägaren bedömer den nya versionen själv.', ''] + fore_granskning
    j = atelje.las_json(r / 'JAMFORELSE.json') or {}
    rader += ['', '## Falsk variation (jämförelsen)', ''] + (['- %s och %s: %s — %s' % (namn.get(p['a'], p['a']), namn.get(p['b'], p['b']), p['grad'], p['skal']) for p in j.get('par') or []]
                                                          or ['Inga par pekades ut.' if j else 'Ingen jämförelse.'])
    rader += ['', '## Materialbehov', ''] + (behov or ['Inga angivna.'])
    (r / 'REDOVISNING.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return r / 'REDOVISNING.md'


def dolj_referens(text, namn):
    """Hypotesen före ägarens första beslut: huvudreferensens namn döljs, som i resten av den blinda vyn (granskning 2,
    N13). Hela namnet och namnet före en parentes eller ett bindestreck byts mot [referensen]."""
    for n in namn:
        for x in {str(n or '').strip(), re.split(r'\s+[(—–-]\s*', str(n or '').strip())[0]}:
            if len(x) >= 3:
                text = re.sub(re.escape(x), '[referensen]', text, flags=re.I)
    return text


def sammanstall(slug):
    """För dashboarden och rapporten: varje kandidat med neutral etikett, status, version, bilder och hypotesen (vyn
    visar den hopfälld, så att bilderna ses först). Titeln, idén, huvudreferensen, granskningen, materialbehovet och
    föreversionen före en förbättringsrunda följer med först när ägaren har fattat sitt första beslut efter planen
    (domd), så att den första bedömningen är blind för förklaringarna och panelens omdöme."""
    ids = lista(slug)
    namn = etiketter(slug, ids)
    blind = not domd(slug)
    ut = []
    for kid in ids:
        st = las_status(slug, kid)
        d = kdir(slug, kid)

        def bilder(bas, under):
            b = lambda sida, vy, s: (lambda p: rel(p) if p.is_file() else None)(bas / sida / ('vy-%s-%s.png' % (vy, s)))  # noqa: E731
            return {'390-forsta': b('start', '390', 'forsta'), '768-forsta': b('start', '768', 'forsta'), '1440-forsta': b('start', '1440', 'forsta'),
                    '390-hela': b('start', '390', 'hela'), '768-hela': b('start', '768', 'hela'), '1440-hela': b('start', '1440', 'hela'),
                    'undersida-390': b(under, '390', 'forsta') if under else None, 'undersida-1440': b(under, '1440', 'forsta') if under else None,
                    'undersida-390-hela': b(under, '390', 'hela') if under else None, 'undersida-1440-hela': b(under, '1440', 'hela') if under else None}
        under = forhandsvisa.sidnamn(st['undersidor'][0]) if st.get('undersidor') else None
        post = {'id': kid, 'etikett': namn.get(kid), 'status': st.get('status'), 'statustext': STATUSTEXT.get(st.get('status'), st.get('status')),
                'skal': st.get('skal'), 'version': st.get('version'), 'varv': st.get('varv'), 'undersidor': st.get('undersidor') or [],
                'bygd': (ksajt(slug, kid) / 'dist' / 'index.html').is_file(), 'design_fel': st.get('design_fel') or [],
                'brister': st.get('brister') or [],
                'kompetenspass': {rec.get('pass'): rec.get('genomford') for k_, rec in sorted((st.get('kompetens') or {}).items()) if k_.startswith('skiss:')},
                'hypotes': dolj_referens(st.get('hypotes') or '', [st.get('huvudreferens')]) if blind else st.get('hypotes') or '',
                'bilder': bilder(d / 'bilder', under)}
        if not blind:
            k = atelje.las_json(d / 'KRITIK.json') or {}
            fore = (st.get('forbattrad') or {}).get('fore')
            post.update(titel=st.get('titel'), huvudreferens=st.get('huvudreferens'), material=material(slug, kid), referensbilder=uppdragets_bilder(slug, kid),
                        riktning=(d / 'RIKTNING.md').read_text(encoding='utf-8', errors='replace')[:30000] if (d / 'RIKTNING.md').is_file() else '',
                        kritik={x: k.get(x) for x in ('forsta_intryck', 'uppgift', 'helhet', 'styrkor', 'avvikelser', 'niva', 'material', 'referens',
                                                      'version', 'modell', 'last')} if k else None,
                        axe=st.get('axe'), lasning=st.get('lasning'), tillampning=st.get('tillampning'),
                        kompetens=[dict(rec, nyckel=k_) for k_, rec in sorted((st.get('kompetens') or {}).items(), key=lambda i: (i[0].split(':')[0],
                                   PASSORDNING.index(i[1].get('pass')) if i[1].get('pass') in PASSORDNING else 9))],
                        forbattring={'fore': fore, 'atgarder': (st.get('forbattrad') or {}).get('atgarder') or [],
                                     'bilder': bilder(d / 'versioner' / fore[:12] / 'bilder', under)}
                        if fore and fore != st.get('version') and bevarad(slug, kid, fore) else None)
        ut.append(post)
    return sorted(ut, key=lambda x: x['etikett'] or x['id'])


def main(argv=None):
    p = argparse.ArgumentParser(prog='kandidater', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--status', action='store_true')
    p.add_argument('--fotografera', default=None, help='fotografera om en kandidat (kNN), utan session')
    a = p.parse_args(argv)
    if not atelje.SLUG.match(a.slug):
        return 2
    if a.fotografera:
        if not ID.fullmatch(a.fotografera) or a.fotografera not in lista(a.slug):
            print('okänd kandidat: %s' % a.fotografera)
            return 2
        st = fotografera(a.slug, a.fotografera)
        print(st['status'], st.get('skal', ''))
        return 0
    for k in sammanstall(a.slug):
        print('%s %-10s %-26s %s' % (k['id'], k['etikett'], k['statustext'], (k.get('version') or '')[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
