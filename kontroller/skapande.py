#!/usr/bin/env python3
"""skapande.py — det gemensamma skapandeflödets delar: ägarens domlogg, riktningshistoriken, metoden per steg och
researchsteget (Codex via ägaren 2026-10-05: tre designflöden där förbättringarna inte följde med; ett skapandeflöde,
beskrivet i kunskap/skapandeflodet.md).

Ateljén (kontroller/atelje.py: utforska och välj) och prototypen (kontroller/prototyp.py: förfina, slutdom, ägaren,
överlämning) använder samma delar, så att ägarens senaste kritik, metoden och referensunderlaget följer med i varje steg.

- Domloggen underlag/<slug>/DESIGNDOMAR.jsonl: en rad per dom eller bedömning över designen, med källan (KALLOR och
  avsändartyperna nedan), beslut godkand | putsa | ny_riktning | valj | jamfor | forkasta och texten ordagrant. Den
  arkiveras aldrig; nästa körning läser den själv. Ett beslut ny_riktning återöppnar alla designbeslut (ATEROPPNAR),
  aldrig verksamhetens fakta. Loggen läses på radslut och inget annat (jsonl_rader), och en rad som inte går att läsa
  står med plats och skäl (domlogg) i stället för att hoppas över tyst.
- Avsändarna (ägarens uppdrag 2026-10-07, punkt 7): AVSANDARTYPER och KALLOR är den enda källan i koden för vem en dom
  kommer från. Bara ägarens egna beslut styr godkännandet, läget, stoppet och slutposterna (ar_agarens); en
  vidarebefordrad AI-bedömning gör det aldrig, och ägaren via Codex räknas bara med ett belägg.
- Historiken underlag/<slug>/RIKTNINGSHISTORIK.json: prövade grundidéer med sina drag och hur de dömdes. Prompterna får
  den som kort text: vad som underkändes och varför, aldrig den gamla lösningen som underlag att bygga vidare på.
- METOD: metodfilerna och skillsen per steg; prompterna räknar upp dem och bildkedja.metodlasning prövar i transkriptet
  att de lästes före första skrivningen.
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
DOMLOGG = 'DESIGNDOMAR.jsonl'
BELAGGFIL = 'DESIGNDOMAR-belagg.jsonl'  # bilagan: ägarens belägg för en befintlig rad, bunden till radens sha256 (GR-20261007-r106#BÖR-2)
HISTORIK = 'RIKTNINGSHISTORIK.json'
BESLUT = ('godkand', 'putsa', 'ny_riktning', 'valj', 'jamfor', 'forkasta', 'uppdrag')
# kandidatflödets beslut (ägarens uppdrag 2026-10-05, punkt 10, och 2026-10-09 ~17:53Z, punkt 8 och 11): valj = en eller
# flera kandidater valda för vidareutveckling (det startar inget), jamfor = några kandidater sida vid sida (inget körs),
# forkasta = alla underkända (flödet väntar på ny riktning), uppdrag = ett av de tre uppdragen nedan för en kandidat i en
# bestämd version; varje sådant beslut bär kandidaterna med sina versioner, och delar = det ägaren gillade i en kandidat.
# Val för vidareutveckling, godkännande för helbygge (godkand) och godkännande för publicering (leveransen, README steg 9)
# är tre olika beslut.
KANDIDATBESLUT = ('valj', 'jamfor', 'forkasta', 'uppdrag')
# De tre uppdragen i körvägen (ägarens uppdrag 2026-10-09, punkt 8). Varje uppdrag anger versionen det gäller, det önskade
# resultatet, omfattningen och det som ska bevaras; benämningarna är de som visas där uppdraget startas.
UPPDRAGSTYPER = {
    'ratta': ('Rätta', 'åtgärda de angivna bristerna inom befintlig omfattning: inga nya sidor, sektioner eller funktioner'),
    'omarbeta': ('Omarbeta designen', 'ändra komposition, bildregi, typografi, rytm och hierarki inom det avtalade innehållet; '
                                      'grundidén får bytas när den inte bär'),
    'bygg_ut': ('Bygg ut', 'skapa de överenskomna sektionerna, undersidorna och funktionerna i kandidatens form'),
}
UPPDRAGSFALT = ('typ', 'resultat', 'omfattning', 'bevara')  # versionen bärs av kandidaterna i beslutet
SPECIALISTLAGEN = ('andra', 'bedom')  # ett specialistpass ändrar, eller bedömer ett fungerande område utan att ändra det
# Återkopplingens form (ägarens uppdrag 2026-10-09, punkt 9): bild, version, element eller område, tillstånd och avvikelse,
# och kodkopplingen (fil:rad) när den finns; samma form i före/efter-bedömningen, specialistpassen och uppdragen.
FYND_SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['bild', 'version', 'element', 'tillstand', 'avvikelse', 'kodkoppling'],
               'properties': {'bild': {'type': 'string'}, 'version': {'type': 'string'}, 'element': {'type': 'string'},
                              'tillstand': {'type': 'string'}, 'avvikelse': {'type': 'string'}, 'kodkoppling': {'type': 'string'}}}
# Avsändartyperna (ägarens uppdrag 2026-10-07, punkt 7), en definition var. Den här tabellen och KALLOR är den enda
# källan i koden för vem en dom eller bedömning kommer från: domloggen, godkännandet, läget, stoppvakten, ateljéns
# slutpost och korslut läser dem (ar_agarens, avsandare). Att ägaren vidarebefordrar en AI-bedömning gör den inte till
# ägarens beslut.
AVSANDARTYPER = {  # typ: (namn, definition)
    'agaren': ('ägarens egna ord och beslut', 'det ägaren själv har sagt eller beslutat; bara det styr godkännandet, läget, '
                                              'stoppet och slutposterna'),
    'codex': ('Codex bedömning', 'en bedömning som Codex har gjort; ett underlag, inget beslut'),
    'claude': ('Claudes eller skaparens bedömning', 'en bedömning av Claude, skaparen eller en annan session i flödet; ett '
                                                    'underlag, inget beslut'),
    'granskare': ('en annan granskares bedömning', 'panelens eller en granskares bedömning, som skisskritiken och helbyggets '
                                                   'granskare; rådgivande, inget beslut'),
    'matning': ('maskinellt mätresultat', 'ett värde som ett verktyg har mätt, som provet, axe eller kontrasten; en mätning, '
                                          'ingen bedömning'),
    'hypotes': ('hypotes', 'ett antagande som inte är prövat; det prövas innan det styr något'),
    'vidarebefordrad': ('vidarebefordrad AI-bedömning', 'en bedömning av Codex, Claude eller en annan modell som ägaren har '
                                                        'skickat vidare; en egen källa och aldrig ägarens beslut, också i första person'),
    'kunden': ('kundens egna ord och beslut', 'det kunden själv har valt, begärt eller underkänt bland förslagen; räknas för '
                                             'kundens val och uppdrag, aldrig för godkännandet för helbygge eller publicering, '
                                             'och en AI-bedömning bokförs aldrig som kundens'),
}
# Domloggens källor (fältet kalla): avsändartypen och definitionen.
KALLOR = {
    'ägaren': ('agaren', 'ägarens egna ord och beslut: skrivna av ägaren i dashboardens vy Prototyp, eller förda in ordagrant '
                         'med skapande.py dom och ett belägg för var ägarens egna ord står'),
    'ägaren via Codex': ('agaren', 'ägarens egna ord, ordagrant förmedlade av Codex; räknas som ägarens bara med ett belägg (fältet '
                                   'belagg: var ägarens egna ord står), annars är avsändaren ej belagd'),
    'vidarebefordrad AI-bedömning': ('vidarebefordrad', 'en bedömning gjord av Codex, Claude eller en annan modell som ägaren har '
                                     'vidarebefordrat; en egen källa och aldrig ägarens beslut, också när den är skriven i första person'),
    'Codex': ('codex', 'Codex bedömning, som Codex själv lämnat den'),
    'skaparen': ('claude', 'Claudes eller skaparens bedömning'),
    'panelen': ('granskare', 'en annan granskares bedömning: panelen eller en granskare i flödet'),
    'mätning': ('matning', 'ett maskinellt mätresultat'),
    'hypotes': ('hypotes', 'en hypotes som inte är prövad'),
    'kunden': ('kunden', 'kundens egna ord och beslut, ordagrant: förda in av ägaren i arbetsytan eller med skapande.py dom, '
                         'med ett belägg för var kundens ord står (samtalet, meddelandet och tiden)'),
}
# Källan som alltid är ägarens egen (dashboardens vy Prototyp). Ägaren via Codex räknas bara med ett belägg: avgör
# ägarens beslut med ar_agarens, inte med den här listan (omgranskningen av skapandeflödet, fynd 2, räknade båda).
AGAREN = ('ägaren',)
BELAGG_KRAVS = ('ägaren via Codex', 'kunden')  # en källa som räknas bara med belägg
KUNDENS_BESLUT = ('valj', 'jamfor', 'forkasta', 'uppdrag', 'ny_riktning')  # kunden väljer, begär ändringar eller underkänner
EJ_BELAGD = 'ej belagd'
# vad en dom återöppnar (Codex 2026-10-05, punkt 2: systemet behöver förstå vilka tidigare beslut ett underkännande
# återöppnar); fakta om verksamheten återöppnas aldrig
ATEROPPNAR = {
    'ny_riktning': ['grundidén', 'referensurvalet och huvudreferensen', 'palett och färgernas roller', 'typografin',
                    'komposition och proportioner', 'bildurval och beskärning', 'rubrikernas form och textens ordning'],
    'putsa': [],
    'godkand': [],
    'valj': [],
    'jamfor': [],
    'forkasta': ['grundidéerna i kandidaterna', 'referensurvalet och huvudreferenserna'],
    'uppdrag': [],  # vad ett uppdrag återöppnar beror på typen (ATEROPPNAR_UPPDRAG)
}
ATEROPPNAR_UPPDRAG = {
    'ratta': [],
    'omarbeta': ['komposition och proportioner', 'bildurval och beskärning', 'typografin', 'rytmen', 'hierarkin',
                 'grundidén när den inte bär'],
    'bygg_ut': [],
}
# metoden per steg: filerna läses med Read, skillsen med Skill eller genom att läsa deras SKILL.md (Codex 2026-10-05,
# glapp 2: prototypens skapare läste ingen av dem; en installerad skill finns inte i kontexten förrän den laddas)
METOD = {
    'forska': {'filer': ['kunskap/referensjakt.md', 'kunskap/referenser-professionella.md',
                         'kunskap/externa/anthropic-frontend-design-SKILL.md'], 'skills': []},
    'utforska': {'filer': ['kunskap/externa/anthropic-frontend-design-SKILL.md', 'kunskap/externa/leonxlnx-taste-SKILL-ce26fc25.md',
                           'kunskap/externa/emil-emil-design-eng-SKILL.md', 'kunskap/bild.md', 'kunskap/referenser-professionella.md'],
               'skills': ['better-layout', 'better-typography']},
    'forfina': {'filer': ['kunskap/referenser-professionella.md', 'kunskap/bild.md', 'kunskap/copy-kontroll.md'],
                'skills': ['better-layout', 'better-typography', 'better-ui', 'better-colors', 'better-writing', 'humanizer']},
}


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def textfil(slug, underlag=None):
    """Sidans text: INNEHALL.md (byggets steg 4) eller TEXTUNDERLAG.md (prototypens utkast). Sakuppgifterna gäller;
    rubriker, ordning och formuleringar får skrivas om tillsammans med formen."""
    u = Path(underlag or UNDERLAG) / slug
    return u / 'INNEHALL.md' if (u / 'INNEHALL.md').is_file() else u / 'TEXTUNDERLAG.md'


UNDERLAGSGRUND = ('VERKSAMHET.json', 'BRIEF.md', 'RESEARCH.md', 'INNEHALL.md', 'TEXTUNDERLAG.md',
                  'BESTALLNING.md', 'UPPDRAG.md', 'REFERENSER.md', 'KUNDSTART.json', 'KUNDFORSTAELSE.md')
# Kundmaterialet och källorna som också ingår i underlagsversionen. Från en godkänd startsida är grunden och katalogerna
# frysta under helbygget: kor.sh nekar Write och Edit där och sandlådan Bash (GR-20261008-r117-claude#A3).
UNDERLAGSKATALOGER = ('bilder', 'kalla', 'referenser')


def underlagsmanifest(slug, underlag=None):
    """Fakta, innehåll och kundmaterial som designen beror på, utan domar eller körutdata.

    Saknad fil är uttrycklig. Läsfel och länkar vägras; en oläsbar källa blir aldrig ett
    oförändrat underlag. Manifestet är privat och sparas i befintliga versionsposter.
    """
    import hashlib
    u = Path(underlag or UNDERLAG) / slug
    if not re.fullmatch(r'[a-z0-9-]{2,60}', slug) or u.is_symlink() or u.parent.is_symlink():
        raise ValueError('ogiltig underlagsrot')
    filer = [u / namn for namn in UNDERLAGSGRUND]
    for namn_ in UNDERLAGSKATALOGER:
        bilder = u / namn_
        if bilder.is_symlink():
            raise ValueError('länkat kundmaterial eller källmaterial')
        if not bilder.exists():
            continue
        def fel(e):
            raise e
        for rot_, kataloger, namn in os.walk(bilder, followlinks=False, onerror=fel):
            if any((Path(rot_) / n).is_symlink() for n in kataloger):
                raise ValueError('länk i kundmaterial')
            filer.extend(Path(rot_) / n for n in namn)
    ut = {}
    for p in sorted(filer):
        if p.is_symlink():
            raise ValueError('länk i underlagsfil')
        ut[p.relative_to(u).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    return ut


def underlagsversion(slug, underlag=None):
    import hashlib
    return hashlib.sha256(json.dumps(underlagsmanifest(slug, underlag), sort_keys=True).encode()).hexdigest()


def kallmanifest(sajt):
    """Källversionen som byggs och exporteras, utan beroendekataloger eller körutdata."""
    sajt = Path(sajt)
    if sajt.is_symlink():
        raise ValueError('sajtkatalogen är en länk')
    filer = [sajt / n for n in ('package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json', 'DESIGN.md')]
    for n in ('src', 'public'):
        rot = sajt / n
        if rot.is_symlink():
            raise ValueError('länk i sajtens källor')
        if not rot.exists():
            continue
        def fel(e):
            raise e
        for katalog, kataloger, namn in os.walk(rot, followlinks=False, onerror=fel):
            if any((Path(katalog) / d).is_symlink() for d in kataloger):
                raise ValueError('kataloglänk i sajtens källor')
            filer.extend(Path(katalog) / f for f in namn if f != '.DS_Store')
    ut = {}
    for p in sorted(filer):
        if p.is_symlink() or (p.exists() and not p.is_file()):
            raise ValueError('källan är inte en vanlig fil')
        ut[p.relative_to(sajt).as_posix()] = sha256_fil(p) if p.exists() else None
    return ut


def kallversion(sajt):
    import hashlib
    return hashlib.sha256(json.dumps(kallmanifest(sajt), sort_keys=True).encode()).hexdigest()


STEG_KARTA = {'utforska': 'skapa', 'forfina': 'forfina', 'forska': 'forska'}  # den äldre vägens steg i metodkartan


def metod_kallor(steg):
    """Stegets källor ur kunskap/metodkarta.md, samma källa som kandidatflödet (synpunkterna på metodkartan 2026-10-05,
    punkt 7): [(väg från repots rot, rader eller rubrik)]. None när kartan saknas eller inte går att läsa."""
    try:
        import metod
        karta = metod.tolka(metod.KARTA.read_text(encoding='utf-8'))
        rubrik = metod.STEG[STEG_KARTA[steg]]
        ut = []
        for r in metod.stegets_rader(karta, rubrik, 'före') + metod.stegets_rader(karta, rubrik, 'varv'):
            m = metod.RAD.match(r)
            if m:
                ut.append((metod.kalla(m.group('vag')).relative_to(metod.ROOT).as_posix(),
                           ('rad ' + m.group('rader').strip()) if m.group('rader') else ('avsnittet ' + m.group('rubrik')) if m.group('rubrik') else ''))
        import kompetens  # kompetensernas filer, hela (ägarens ord 2026-10-05 18:15Z: alla skills används)
        pass_ = {'utforska': 'skapa', 'forfina': 'fordjupa'}.get(steg)
        for v in (kompetens.lasfiler(pass_) if pass_ else []):
            if v not in [x for x, _ in ut]:
                ut.append((v, 'hela, kompetensen'))
        return ut
    except Exception:  # noqa: BLE001 — utan karta gäller listan nedan
        return None


def metodrader(steg):
    k = metod_kallor(steg)
    if k is None:
        m = METOD[steg]
        return ['- ' + f for f in m['filer']] + ['- skillen %s (.claude/skills/%s/SKILL.md med Read)' % (s, s) for s in m['skills']]
    return ['- %s%s' % (v, (' (%s)' % d) if d else '') for v, d in k]


def metod_filer(steg):
    """Filerna metodkvittot prövar läsningen av (kontroller/bildkedja.py metodlasning)."""
    k = metod_kallor(steg)
    if k is None:
        return METOD[steg]['filer'] + ['.claude/skills/%s/SKILL.md' % s for s in METOD[steg]['skills']]
    return list(dict.fromkeys(v for v, _ in k))


# --- JSONL-filerna och domloggen ---

def jsonl_rader(fil):
    """En JSONL-fils rader, lästa på radslut (\\n) och inget annat: [{'rad', 'data', 'post', 'fel'}] med filens radnummer
    (från 1), radens byte utan radslutet, posten och skälet när raden inte går att läsa. str.splitlines() delar också på
    U+2028, U+2029, U+0085 och några styrtecken, som JSON tillåter oskyddade i en sträng (json.dumps med
    ensure_ascii=False skriver dem som de är); en dom med ett sådant tecken blev två rader som inte gick att läsa och
    hoppades över tyst (GR-20261007-r100-om#KAN-A). En tom rad, också den efter filens sista radslut, är ingen rad med
    innehåll och hoppas över. Saknas filen: []; ett läsfel (OSError) går vidare."""
    fil = Path(fil)
    if not fil.is_file():
        return []
    ut = []
    for i, data in enumerate(fil.read_bytes().split(b'\n'), 1):
        if not data.strip():
            continue
        post, fel = None, None
        try:
            post = json.loads(data.decode('utf-8'))
        except UnicodeDecodeError as e:
            fel = 'inte UTF-8 (%s)' % str(e)[:80]
        except ValueError as e:
            fel = 'inte JSON (%s)' % str(e)[:80]
        ut.append({'rad': i, 'data': data, 'post': post, 'fel': fel})
    return ut


def bilagor(slug, underlag=None):
    """Beläggbilagan (BELAGGFIL) rad för rad: {'fil', 'belagg': {sha256: post}, 'olasbara': [{'rad', 'skal'}]}. En giltig rad
    är ägarens eget intyg (kalla ägaren) om att en befintlig rad i domloggen, utpekad med radens sha256, är ägarens egna
    ord, med belägget för var orden står. Den sista raden för en sha gäller. En rad som inte går att läsa, eller inte har
    bilagans form, står i olasbara: den räknas inte, och den domrad den kan gälla förblir ej belagd."""
    f = Path(underlag or UNDERLAG) / slug / BELAGGFIL
    ut = {'fil': 'underlag/%s/%s' % (slug, BELAGGFIL), 'belagg': {}, 'olasbara': []}
    for r in jsonl_rader(f):
        p = r['post']
        if r['fel']:
            ut['olasbara'].append({'rad': r['rad'], 'skal': r['fel']})
        elif isinstance(p, dict) and p.get('kalla') in AGAREN and re.fullmatch(r'[0-9a-f]{64}', str(p.get('sha256') or '')) and belagg(p):
            ut['belagg'][p['sha256']] = dict(p, rad=r['rad'])
        else:
            ut['olasbara'].append({'rad': r['rad'], 'skal': 'raden är JSON men inget belägg i bilagans form (kalla ägaren, sha256 och belagg)'})
    return ut


def domlogg(slug, underlag=None):
    """Domloggen rad för rad: {'fil', 'domar': [(rad, sha256 av radens byte, post)], 'olasbara': [{'rad', 'skal'}],
    'bilaga_olasbara': [...]}. Radnumren och hasharna är filens egna rader (jsonl_rader). En rad som inte går att läsa,
    eller som är JSON men ingen dom i loggens form (beslut och text), står i olasbara med plats och skäl i stället för att
    hoppas över tyst. Ett belägg som ägaren lagt till i efterhand för en rad som kräver det (BELAGG_KRAVS) ligger i bilagan
    (bilagor), bundet till radens sha256, och fästs vid posten här (fälten belagg och belagg_bilaga) utan att loggen skrivs
    om och utan att det blir en ny dom (GR-20261007-r106#BÖR-2)."""
    import hashlib
    f = Path(underlag or UNDERLAG) / slug / DOMLOGG
    ut = {'fil': 'underlag/%s/%s' % (slug, DOMLOGG), 'domar': [], 'olasbara': [], 'bilaga_olasbara': []}
    bil = None
    for r in jsonl_rader(f):
        p = r['post']
        if r['fel']:
            ut['olasbara'].append({'rad': r['rad'], 'skal': r['fel']})
        elif isinstance(p, dict) and p.get('beslut') in BESLUT and isinstance(p.get('text'), str):
            sha = hashlib.sha256(r['data']).hexdigest()
            if p.get('kalla') in BELAGG_KRAVS and belagg(p) is None:
                if bil is None:
                    bil = bilagor(slug, underlag)
                    ut['bilaga_olasbara'] = bil['olasbara']
                b = bil['belagg'].get(sha)
                if b:
                    p = dict(p, belagg=belagg(b), belagg_bilaga={'fil': bil['fil'], 'rad': b['rad'], 'tid': b.get('tid'), 'kalla': b.get('kalla')})
            ut['domar'].append((r['rad'], sha, p))
        else:
            ut['olasbara'].append({'rad': r['rad'], 'skal': 'raden är JSON men ingen dom (beslut eller text saknas eller är okända)'})
    return ut


def lagg_till_belagg(slug, rad, text, underlag=None, tid=None):
    """Ägarens belägg i efterhand för en befintlig rad i domloggen (radnumret): en rad i bilagan (BELAGGFIL) med radens
    sha256, belägget (var ägarens egna ord står), tiden och källan ägaren. Domloggen skrivs inte om, raden får ingen ny
    tid och blir ingen ny dom; den räknas som ägarens från och med nu (ar_agarens genom domlogg). Bara en rad vars källa
    kräver belägg (ägaren via Codex) kan få ett: källan ägaren behöver inget, och en vidarebefordrad AI-bedömning eller en
    annan källa är aldrig ägarens beslut. Ger bilagans post."""
    b = belagg({'belagg': text})
    if b is None:
        raise ValueError('belägget är tomt: skriv var ägarens egna ord står')
    lg = domlogg(slug, underlag)
    tr = next(((r, s, p) for r, s, p in lg['domar'] if r == int(rad)), None)
    if tr is None:
        raise ValueError('rad %s i %s är ingen läsbar dom' % (rad, lg['fil']))
    r, sha, p = tr
    if p.get('kalla') not in BELAGG_KRAVS:
        raise ValueError('rad %d har källan %s: %s' % (r, p.get('kalla'), 'den är redan ägarens egen och behöver inget belägg' if p.get('kalla') in AGAREN
                                                      else 'bara %s kan få ett belägg; en annan källa är aldrig ägarens beslut' % ', '.join(BELAGG_KRAVS)))
    post = {'tid': tid or nu(), 'kalla': AGAREN[0], 'sha256': sha, 'dom_rad': r, 'dom_tid': p.get('tid'), 'belagg': b}
    f = Path(underlag or UNDERLAG) / slug / BELAGGFIL
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, 'ab') as fh:
        if f.stat().st_size > 0:
            with open(f, 'rb') as las_:
                las_.seek(-1, os.SEEK_END)
                slut_ = las_.read(1)
            if slut_ != b'\n':
                fh.write(b'\n')
        fh.write((json.dumps(post, ensure_ascii=False) + '\n').encode('utf-8'))
    return post


def olasbara_text(lg):
    """De oläsbara raderna i domloggen som en mening med antal och plats, eller None."""
    o = (lg or {}).get('olasbara') or []
    if not o:
        return None
    return '%s: %d %s inte att läsa (%s); %s räknas inte, och ingen rad skrivs om' % (
        lg.get('fil') or DOMLOGG, len(o), 'rad går' if len(o) == 1 else 'rader går',
        '; '.join('rad %d: %s' % (x['rad'], x['skal']) for x in o[:6]) + (' …' if len(o) > 6 else ''), 'den' if len(o) == 1 else 'de')


def domar(slug, underlag=None):
    """Domloggens poster i tidsordning; en rad som inte går att läsa står i domlogg(...)['olasbara']."""
    return [p for _r, _s, p in domlogg(slug, underlag)['domar']]


def belagg(d):
    """Domens belägg för att orden är ägarens egna (fältet belagg: var ägarens egna ord står), eller None."""
    b = d.get('belagg') if isinstance(d, dict) else None
    return b.strip()[:1000] if isinstance(b, str) and b.strip() else None


def ar_agarens(d):
    """Är domen ägarens eget beslut? Källan ägaren, eller ägaren via Codex med ett belägg (ägarens uppdrag 2026-10-07,
    punkt 7). En vidarebefordrad AI-bedömning, Codex, skaparen, panelen, en mätning, en hypotes, en okänd källa och
    ägaren via Codex utan belägg är det aldrig, varken för godkännandet, läget, stoppet eller slutposterna. Kundens beslut
    är kundens (ar_kundens), inte ägarens."""
    if not isinstance(d, dict):
        return False
    k = d.get('kalla')
    return k in AGAREN or (k == 'ägaren via Codex' and belagg(d) is not None)


def ar_kundens(d):
    """Är domen kundens eget val, uppdrag eller underkännande (källan kunden med belägg, ett av KUNDENS_BESLUT)? Ägarens
    uppdrag 2026-10-09, punkt 11: kunden kan välja, begära ändringar eller underkänna alla; godkännandet för helbygge och
    publicering är ägarens."""
    return isinstance(d, dict) and d.get('kalla') == 'kunden' and belagg(d) is not None and d.get('beslut') in KUNDENS_BESLUT


def ar_beslut(d):
    """Styr domen flödet? Ägarens beslut, eller kundens inom kundens beslut."""
    return ar_agarens(d) or ar_kundens(d)


def avsandare(d):
    """Domens avsändare: {'kalla', 'typ', 'namn', 'agarens', 'belagg', 'text'}. Ägaren via Codex utan belägg och en okänd
    eller saknad källa står som ej belagd (typ None); en äldre rad skrivs aldrig om för att få ett belägg."""
    k = d.get('kalla') if isinstance(d, dict) else None
    typ = KALLOR[k][0] if k in KALLOR else None
    b = belagg(d)
    if typ is None or (k in BELAGG_KRAVS and b is None):
        return {'kalla': k, 'typ': None, 'namn': EJ_BELAGD, 'agarens': False, 'belagg': b,
                'text': '%s (källan %s%s)' % (EJ_BELAGD, k or 'saknas', ', utan belägg' if k in BELAGG_KRAVS else ', okänd' if k else '')}
    bil = d.get('belagg_bilaga') if isinstance(d.get('belagg_bilaga'), dict) else None
    return {'kalla': k, 'typ': typ, 'namn': AVSANDARTYPER[typ][0], 'agarens': typ == 'agaren', 'belagg': b,
            'text': '%s (%s%s%s)' % (AVSANDARTYPER[typ][0], k, '; belägg: %s' % b[:200] if b else '',
                                    '; belägget i bilagan %s rad %s, %s' % (bil.get('fil'), bil.get('rad'), bil.get('tid') or 'utan tid') if bil else '')}


def lagg_till_dom(slug, kalla, beslut, text, avser='', underlag=None, tid=None, **extra):
    """En dom till loggen (en rad, tillagd i slutet). Ger posten. Ägaren via Codex kräver ett belägg (belagg=…): en
    bedömning som ägaren vidarebefordrat förs in med källan vidarebefordrad AI-bedömning. Slutar loggen utan radslut (en
    skrivning som avbröts) får den ett radslut först, så att den nya domen står på en egen rad och aldrig går förlorad."""
    if kalla not in KALLOR or beslut not in BESLUT or not isinstance(text, str) or not text.strip():
        raise ValueError('domen behöver källa (%s), beslut (%s) och text' % (', '.join(KALLOR), ', '.join(BESLUT)))
    if kalla in BELAGG_KRAVS and belagg(extra) is None:
        raise ValueError('%s kräver ett belägg för att orden är %s egna (var de står); en bedömning som ägaren har '
                         'vidarebefordrat förs in med källan vidarebefordrad AI-bedömning' % (kalla, 'kundens' if kalla == 'kunden' else 'ägarens'))
    if kalla == 'kunden' and beslut not in KUNDENS_BESLUT:
        raise ValueError('kunden väljer, begär uppdrag eller underkänner (%s); godkännandet för helbygge och publicering är '
                         'ägarens' % ', '.join(KUNDENS_BESLUT))
    if beslut == 'uppdrag':
        extra['uppdrag'] = uppdrag_giltigt(extra.get('uppdrag'))
    if 'belagg' in extra:
        extra['belagg'] = belagg(extra)
        if extra['belagg'] is None:
            extra.pop('belagg')
    post = {'tid': tid or nu(), 'kalla': kalla, 'beslut': beslut, 'text': text.strip()[:20000], 'avser': str(avser)[:400],
            'ateroppnar': ATEROPPNAR_UPPDRAG[extra['uppdrag']['typ']] if beslut == 'uppdrag' else ATEROPPNAR[beslut], **extra}
    f = Path(underlag or UNDERLAG) / slug / DOMLOGG
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, 'ab') as fh:
        if f.stat().st_size > 0:
            with open(f, 'rb') as las_:
                las_.seek(-1, os.SEEK_END)
                slut_ = las_.read(1)
            if slut_ != b'\n':
                fh.write(b'\n')
        fh.write((json.dumps(post, ensure_ascii=False) + '\n').encode('utf-8'))
    return post


def uppdrag_giltigt(u):
    """Uppdraget i ett beslut, prövat och normaliserat: typ (UPPDRAGSTYPER), resultat (text), omfattning och bevara
    (listor med minst en rad; bevara får vara tom bara när inget särskilt ska bevaras och det sägs), specialister (rollen
    rorelse eller granskning med läget andra eller bedom). ValueError med skälet."""
    if not isinstance(u, dict):
        raise ValueError('uppdraget saknas: typ (%s), resultat, omfattning och bevara' % ', '.join(UPPDRAGSTYPER))
    typ = u.get('typ')
    if typ not in UPPDRAGSTYPER:
        raise ValueError('okänd uppdragstyp %r; välj %s' % (typ, ', '.join(UPPDRAGSTYPER)))
    lista = lambda x: [str(r).strip()[:600] for r in (x if isinstance(x, list) else [x] if isinstance(x, str) else []) if str(r).strip()][:20]  # noqa: E731
    resultat = str(u.get('resultat') or '').strip()[:2000]
    omfattning, bevara = lista(u.get('omfattning')), lista(u.get('bevara'))
    if not resultat:
        raise ValueError('uppdraget saknar det önskade resultatet')
    if not omfattning:
        raise ValueError('uppdraget saknar omfattningen (bristerna att rätta, områdena att omarbeta eller det som ska byggas ut)')
    if not bevara:
        raise ValueError('uppdraget saknar vad som ska bevaras (skriv "inget särskilt" när inget ska bevaras)')
    spec = u.get('specialister') or {}
    if not isinstance(spec, dict) or any(k not in ('rorelse', 'granskning') or v not in SPECIALISTLAGEN for k, v in spec.items()):
        raise ValueError('specialisterna anges som rorelse/granskning med läget andra eller bedom')
    return {'typ': typ, 'namn': UPPDRAGSTYPER[typ][0], 'resultat': resultat, 'omfattning': omfattning, 'bevara': bevara,
            # utan uttryckliga specialister får uppdraget typens standard (kandidater.STANDARD_SPECIALISTER); {} betyder inga
            'specialister': dict(spec) if u.get('specialister') is not None else None,
            **({'omrade': u['omrade']} if isinstance(u.get('omrade'), dict) else {})}


def uppdragstext(u):
    """Uppdraget i ord, som det visas och bokförs."""
    return '%s: %s. Omfattning: %s. Bevara: %s.' % (u.get('namn') or UPPDRAGSTYPER.get(u.get('typ'), ('?',))[0], u.get('resultat'),
                                                 '; '.join(u.get('omfattning') or []), '; '.join(u.get('bevara') or []))


def agarens_senaste(slug, underlag=None):
    """Ägarens senaste beslut (ar_agarens) med plats: {'dom', 'rad', 'oklara', 'fil'}. oklara är de rader efter den domen
    (eller i hela loggen, utan någon dom från ägaren) som inte går att läsa: där kan ägarens senare beslut stå, så ett
    beslut som bygger på den senaste domen kan inte fattas förrän raden är rättad (ingen dom försvinner tyst)."""
    lg = domlogg(slug, underlag)
    rad, dom = next(((r, p) for r, _s, p in reversed(lg['domar']) if ar_beslut(p)), (0, None))
    return {'dom': dom, 'rad': rad or None, 'oklara': [x for x in lg['olasbara'] if x['rad'] > rad], 'fil': lg['fil']}


def oklara_text(ag):
    o = (ag or {}).get('oklara') or []
    if not o:
        return None
    return ('%s: %s efter ägarens senaste läsbara dom%s går inte att läsa (%s); där kan ägarens senare beslut stå, så det '
            'senaste beslutet går inte att avgöra. Vägen vidare är ett nytt beslut från ägaren efter raden (vyn Prototyp, eller '
            'skapande.py dom med belägg), som gäller från sin rad; raden skrivs inte om av sig själv' % (
                ag.get('fil') or DOMLOGG, 'rad %d' % o[0]['rad'] if len(o) == 1 else 'raderna %s' % ', '.join(str(x['rad']) for x in o[:8]),
                ' (rad %d)' % ag['rad'] if ag.get('rad') else '', '; '.join(x['skal'] for x in o[:3])))


def senaste(slug, kallor=None, underlag=None):
    """Det senaste beslutet som styr flödet (ar_beslut: ägarens, eller kundens val, uppdrag och underkännanden), eller
    None. Med kallor (en lista över källor) den senaste från någon av dem."""
    return next((d for d in reversed(domar(slug, underlag)) if (d.get('kalla') in kallor if kallor is not None else ar_beslut(d))), None)


AKTUELL_START = ('ny_riktning',)  # återöppnar designbesluten (ATEROPPNAR); en förkastning bara grundidéerna och referenserna
MAX_AKTUELLA = 6  # den aktuella linjens första dom visas alltid, och de senaste efter den


def aktuella_domar(slug, underlag=None):
    """Kundens aktuella domar: hela linjen från den senaste ägardomen som begärde en ny riktning (den återöppnar
    designbesluten); utan en sådan alla ägarens domar. De äldre är historik som slås upp (ägarens uppdrag 2026-10-05
    16:25Z; granskning 3, S6)."""
    egna = [d for d in domar(slug, underlag) if ar_agarens(d)]
    start = max((i for i, d in enumerate(egna) if d.get('beslut') in AKTUELL_START), default=0)
    return egna[start:]


def aldre_domar(slug, underlag=None):
    egna = [d for d in domar(slug, underlag) if ar_agarens(d)]
    return egna[:len(egna) - len(aktuella_domar(slug, underlag))]


def kritikrader(slug, antal=3, underlag=None, aktuella=False):
    """Ägarens senaste domar ordagrant, nyast först, med vad de återöppnar: prompternas första underlag. aktuella: kundens
    aktuella linje (aktuella_domar), med linjens första dom alltid med, och en rad om de äldre domarna och var de står;
    den äldre utforskningen får annars de senaste oavsett linje."""
    utelamnade, aldre = 0, []
    if aktuella:
        linje = aktuella_domar(slug, underlag)
        egna = linje if len(linje) <= MAX_AKTUELLA else linje[:1] + linje[-(MAX_AKTUELLA - 1):]
        utelamnade, aldre = len(linje) - len(egna), aldre_domar(slug, underlag)
    else:
        egna = [d for d in domar(slug, underlag) if ar_agarens(d)][-antal:]
    if not egna:
        return []
    rader = ['Ägarens %s domar över designen (underlag/%s/%s), nyast först. De väger tyngst av allt du läser; en senare' % (
                 'aktuella' if aktuella else 'senaste', slug, DOMLOGG),
             'dom går före en tidigare, och före äldre lärdomar och tidigare designval. En dom gäller det den uttryckligen',
             'beslutar och förstås i sitt sammanhang: den blir inga allmänna formregler, och att något fungerade dåligt i ett',
             'förslag förbjuder det inte i ett annat (ägaren 2026-10-06: tidigare underkännanden ska inte omvandlas till en allt',
             'smalare uppsättning tillåtna uttryck):']
    for d in reversed(egna):
        rader.append('- %s, %s, beslut %s%s:' % (d.get('tid', '?'), d.get('kalla'), d['beslut'],
                                                  (' (återöppnar: %s)' % ', '.join(d.get('ateroppnar') or [])) if d.get('ateroppnar') else ''))
        rader += ['  > ' + r for r in d['text'].splitlines() if r.strip()]
        kand = [k for k in d.get('kandidater') or [] if isinstance(k, dict)]
        plan = ' i planen %s' % d['plan'] if d.get('plan') else ''  # kandidat-id (k01–k12) gäller bara inom sin plan
        if kand:
            rader.append('  kandidaterna%s: ' % plan + ', '.join('%s (%s%s, version %s)' % (
                k.get('etikett') or k.get('id'), k.get('id'), (' "%s"' % k['titel']) if k.get('titel') else '', str(k.get('version') or '')[:12]) for k in kand))
        ay = d.get('arbetsyta') if isinstance(d.get('arbetsyta'), dict) else {}  # en ändring som ägaren skickat från arbetsytan
        mark = ', '.join('%s %s' % (n, re.sub(r'\s+', ' ', str(ay[k]))[:200]) for k, n in (('sida', 'sida'), ('del', 'del'), ('fil', 'fil'))
                         if ay.get(k))
        if mark:
            rader.append('  ändringen gäller (ägarens markering i arbetsytan, version %s): %s' % (str(ay.get('version') or '?')[:12], mark))
        titlar = d.get('delar_titlar') if isinstance(d.get('delar_titlar'), dict) else {}
        for kid, text in sorted((d.get('delar') or {}).items()) if isinstance(d.get('delar'), dict) else []:
            rader.append('  ägaren gillade i %s%s%s: %s' % (kid, (' "%s"' % titlar[kid]) if titlar.get(kid) else '', plan, re.sub(r'\s+', ' ', str(text))[:600]))
    if utelamnade:
        rader.append('(%d domar i samma linje, mellan den första och de senaste, står i underlag/%s/%s.)' % (utelamnade, slug, DOMLOGG))
    if aldre:
        rader.append('Äldre domar (%d, %s–%s) står i underlag/%s/%s. Den nya riktningen har återöppnat deras designbeslut; ett' % (
            len(aldre), aldre[0].get('tid', '?')[:10], aldre[-1].get('tid', '?')[:10], slug, DOMLOGG))
        rader.append('uttryckligt beslut i dem om annat än designen (till exempel kontaktvägen eller vad som inte ska nämnas) gäller tills en')
        rader.append('senare dom återöppnar det. Slå upp dem när en sådan fråga uppstår.')
    return rader


# --- riktningshistoriken ---

def historik(slug, underlag=None):
    d = las_json(Path(underlag or UNDERLAG) / slug / HISTORIK)
    return [p for p in d if isinstance(p, dict) and p.get('namn')] if isinstance(d, list) else []


def lagg_till_historik(slug, poster, underlag=None):
    """Poster {tid, kalla, namn, drag, utfall, kritik} läggs till; filen skrivs atomiskt. En historikfil som finns men inte
    går att tolka skrivs aldrig över (RuntimeError): den äldre historiken får inte försvinna (granskningen av r92c)."""
    f = Path(underlag or UNDERLAG) / slug / HISTORIK
    befintliga = las_json(f) if (f.exists() or f.is_symlink()) else []
    if not isinstance(befintliga, list):
        raise RuntimeError('%s går inte att tolka som en lista; inget skrivs över (rätta filen först)' % f.name)
    allt = befintliga + [dict(p, tid=p.get('tid') or nu()) for p in poster]  # alla befintliga poster, också namnlösa (r92d)
    tmp = f.with_name('.%s.tmp%d' % (HISTORIK, os.getpid()))
    try:  # till disken före bytet, och ingen halv temporärfil kvar efter ett fel (granskningen av r93, KAN 8)
        with open(tmp, 'w', encoding='utf-8') as ut:
            ut.write(json.dumps(allt, ensure_ascii=False, indent=1) + '\n')
            ut.flush()
            os.fsync(ut.fileno())
        os.replace(tmp, f)
    finally:
        tmp.unlink(missing_ok=True)
    return allt


def historikrader(slug, underlag=None, antal=8):
    h = historik(slug, underlag)[-antal:]
    if not h:
        return []
    rader = ['Prövade grundidéer och hur de dömdes (underlag/%s/%s). De är inte underlag att bygga vidare på: en ny riktning' % (slug, HISTORIK),
             'väljs med eget skäl. Ett drag ur en underkänd grundidé behöver ett skäl ur verksamhetens material som också svarar',
             'på kritiken mot den; inget drag är förbjudet i sig:']
    for p in h:
        rader.append('- %s (%s, %s%s): %s. Utfall: %s%s' % (p['namn'], p.get('kalla', '?'), p.get('tid', '?'),
                                                           ', huvudreferens %s' % p['referens'] if p.get('referens') else '', p.get('drag', '').strip(),
                                                           p.get('utfall', '?'), (': ' + p['kritik'].strip()) if p.get('kritik') else ''))
    return rader


# --- fakta skilda från designbeslut ---

def fakta_rader(slug, underlag=None):
    """Vad som är verksamhetens fakta och vad som är omprövbart utkast (Codex 2026-10-05, punkt 1: skilj verifierade
    företagsfakta från gamla designbeslut)."""
    u = 'underlag/%s' % slug
    return ['Verksamhetens fakta gäller och ändras aldrig: namn, nummer, orter, år, tjänster, omdömenas ordalydelse och varje',
            'uppgift med belägg. De står i %s/VERKSAMHET.json, %s/RESEARCH.md (raderna Belägg och listan "Bara de har"),' % (u, u),
            '%s/kalla/ och verksamhetens egna bilder i %s/bilder/ (BILDER.md beskriver dem). Sakuppgifterna i %s gäller,' % (u, u, rel(textfil(slug, underlag))),
            'men dess rubriker, ordning, blockindelning och formuleringar är ett utkast som skrivs om tillsammans med formen.',
            '%s/BRIEF.md: toppuppgifterna, den primära handlingen och kravens innehåll gäller; den primära handlingen är tydlig' % u,
            'och lätt att hitta, i mobilens första vy när briefens prioriterade uppgift motiverar det (designreglerna); hur den gestaltas och var övriga',
            'handlingar och sajtkartans bilder hamnar är förslag. Designbeslut',
            '(grundidé, referensurval, palett, typografi, komposition, bildurval och beskärning, rubrikernas form) prövas mot',
            'ägarens domar nedan; ett beslut en dom återöppnat fattas på nytt med eget skäl.']


def rel(p):
    p = Path(p)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def telefon(slug, underlag=None):
    v = las_json(Path(underlag or UNDERLAG) / slug / 'VERKSAMHET.json') or {}
    return next((k.get('varde') for k in v.get('kontaktvagar') or [] if isinstance(k, dict) and k.get('typ') == 'telefon'), None)


# --- research på begäran ---

KOMPLETTERING = 'KOMPLETTERING.json'
KOMPLETTERINGSFORMAT = ('{"varfor": "vad du saknar och varför, till exempel: den bilddrivna riktningen bär inte med kundens foton; '
                        'hitta och pröva en annan komposition", "referens": {"kandidater": [{"namn": "a-z0-9-", "adress": '
                        '"https://värd/", "roll": "bransch|hantverk|ux", "varfor": "...", "sidor": ["/"]}]}, "tjanster": '
                        '{"fragor": [{"tjanst": "refero|mobbin", "fraga": "...", "syfte": "...", "typ": "stil|skarm|flode"}]}} '
                        '(referens eller tjanster eller båda; referens i formatet för REFERENSUPPDRAG.json i '
                        '.claude/skills/bygg-sajt/SKILL.md steg 3)')


def senaste_paket(slug, underlag=None):
    r = Path(underlag or UNDERLAG) / slug / 'referenser'
    nr = [(int(p.name[7:]), p) for p in r.glob('paket-v*') if re.match(r'^paket-v\d{2,}$', p.name) and p.is_dir()] if r.is_dir() else []
    return max(nr)[1] if nr else None


# Kompletteringen är skaparsessionens enda kanal ut: adresserna hämtas och frågorna går till tjänsterna. Formen och mängden
# begränsas så att den inte kan bära mer än en referensjakt behöver (omgranskningen av skapandeflödet, fynd 8: en spärr
# mot frågesträngar räckte inte, vägsegment bär samma data). Kanalen är smal, inte stängd: värdnamnet och några korta
# vägar går fortfarande ut, och skaparen läser bara underlaget, aldrig hemligheter (kunskap/skapandeflodet.md).
MAX_KANDIDATER, MAX_SIDOR_PER, MAX_FRAGOR, MAX_FRAGA = 3, 4, 3, 160
# researchsteget före kandidatplanen (kontroller/kandidater.py) söker brett: samma form, fler sajter och frågor
MAX_KANDIDATER_BRED, MAX_FRAGOR_BRED = 8, 14
VARD = re.compile(r'https://(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.){1,3}[a-z]{2,12}/')  # fullmatch; etiketter upp till 63 tecken
LED = r'(?!\.+(?:/|$))(?:[A-Za-z0-9._~-]|%[0-9A-Fa-f]{2}){1,60}'  # å, ä, ö procentkodade; inte bara punkter
SIDVAG = re.compile(r'/(?:%s(?:/%s){0,3}/?)?' % (LED, LED))  # fullmatch; högst fyra led med snedstreck emellan


def vik(s):
    """Gemener utan diakritiska tecken (å, ä → a, ö → o, é → e), för jämförelser; också NFD-kodade tecken (ett a följt
    av en kombinerande ring) och andra diakriter (granskning 4, G14)."""
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s).lower())
    return ''.join(c for c in s if not unicodedata.combining(c)).translate(str.maketrans('æøß', 'aos'))


ALLMANNA_EPOSTORD = {'info', 'kontakt', 'mail', 'post', 'order', 'offert', 'support', 'hello', 'kundtjanst', 'noreply'}

# --- adresser i fritext (granskningen GR-20261007-r104, B1): fritexten not och kontaktvägarnas belägg i
# VERKSAMHET.json; kundvakten läser briefen, sidans text och RESEARCH.md med samma regler (kontroller/kundvakt.py) ---
# Ett gatunamn känns igen på sitt led: med stor bokstav ("Exempelgatan", "Kungsvägen 12"), med gemener bara med ett
# husnummer efter ("storgatan 5"). De svaga leden är också vanliga ord ("arbetsplan", "byggplatsen") och räknas bara med
# stor bokstav och ett husnummer efter. Ett eget gatuord efter ett namn med stor bokstav ("Drottning Kristinas väg")
# räknas, utom efter ett ensamt ord som inleder en mening utan husnummer ("Hela vägen …").
GATULED = ('gatan', 'gata', 'vägen', 'väg', 'gränden', 'gränd', 'stigen', 'torget', 'backen', 'allén', 'allé', 'leden',
           'kajen', 'stråket', 'slingan')
GATULED_SVAGA = ('plan', 'platsen', 'plats', 'gången', 'ringen', 'torg', 'backe', 'stig', 'kaj', 'liden', 'höjden',
                 'parken', 'kroken', 'svängen', 'hagen', 'udden', 'viken', 'berget', 'gärdet')
GATUORD = {'väg', 'vägen', 'gata', 'gatan', 'gränd', 'torg', 'torget', 'plan', 'plats', 'platsen', 'allé', 'allén',
           'backe', 'backen', 'stig', 'stigen', 'led', 'leden', 'kaj', 'kajen'}
# ortsled och stora regioner: en ort ur bara dem ("Norra Sverige") pekar inte ut kunden; ett led framför ett ortnamn
# hör till namnet ("Stora Mellösa", "Östra Hamngatan")
REGIONER = set('norra sodra ostra vastra ovre nedre mellersta gamla nya stora lilla sankt st sverige sweden norden '
               'skandinavien norrland svealand gotaland europa'.split())
# tjänster och plattformar som en fritext nämner efter "på" eller "i" ("visas inte på Google")
EJ_ORT = set('google maps facebook instagram linkedin youtube tiktok reco bokadirekt hitta eniro trustpilot allabolag '
             'ratsit merinfo blocket offerta mittanbud servicefinder byggahus houzz'.split())
ADRESSPREP = {'i', 'pa', 'vid', 'utanfor', 'nara', 'inom'}
TEXTORD = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*|\d+|[^\w\s]")
# postnummer, "999 99" eller "99999", inte en del av ett längre nummer ("070-000 11 22")
POSTNUMMER_I_TEXT = re.compile(r'(?<!\d)(?<!\d[ \t-])(\d{3})[ \t]?(\d{2})(?![ \t]?\d)')
# telefon- och organisationsnummer: minst åtta siffror med högst ett mellanslag eller bindestreck mellan grupperna
NUMMER_I_TEXT = re.compile(r'(?<![\d+])\+?\d(?:[ \t-]?\d){7,13}(?![ \t-]?\d)')


def _versal(w):
    """Ett ord med stor begynnelsebokstav som inte är en förkortning i versaler (AB, SE)."""
    return len(w) > 1 and w[0].isupper() and not re.sub(r"[-'’]", '', w).isupper() \
        and bool(re.fullmatch(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", w))


def adresser_i_text(text, ej=None, regioner=None):
    """Gatorna, postnumren, orterna, namnen efter c/o och de långa numren i en fritext: {'gator', 'orter', 'namn',
    'siffror'}. Gator, orter och namn i vik-form, ord med mellanslag emellan; siffror som siffersträngar (ett
    telefonnummer också utan nollan och med de sex sista siffrorna, som i forbjudna_termer).
    - Gatan: ett ord med ett gatuled (GATULED, GATULED_SVAGA), med ortsled framför ("Östra Hamngatan" ger också
      "hamngatan"), eller ett namn med stor bokstav följt av ett gatuord (GATUORD; också utan sina första ord).
    - Postnumret och orten efter det ("999 99 Fiktivby"), och orten efter gatan, husnumret och ett komma sist i en sats
      ("Exempelgatan 3, Fiktivby").
    - Namnet efter c/o ("c/o Anna Ek").
    - Orten efter i, på, vid, utanför, nära eller inom i en adressmening: en mening med en gata, ett postnummer eller
      ordet adress. En ort med ett ord ur ej (tjänster och plattformar) eller bara ur regioner räknas inte."""
    ej = EJ_ORT if ej is None else ej
    regioner = REGIONER if regioner is None else regioner
    import unicodedata
    gator, orter, namn, siffror = set(), set(), set(), set()

    def fras(ord_):
        return ' '.join(w for w in (re.sub(r'[^a-z0-9]+', ' ', vik(x)).strip() for x in ord_) if w)
    rader = unicodedata.normalize('NFC', str(text or '')).splitlines()
    # Ett sammanhängande postadressblock får ha orten på nästa rad. Gå
    # aldrig över ett tomt stycke eller en Markdown-rubrik till nästa ämne.
    extra = []
    for i, (rad, nasta) in enumerate(zip(rader, rader[1:])):
        if i + 2 < len(rader) and re.fullmatch(r'\s*(?:=+|-+)\s*', rader[i + 2]):
            continue  # nästa rad hör till en setext-rubrik, inte postadressen
        fore = rad.rstrip(' \t|')
        post = list(POSTNUMMER_I_TEXT.finditer(fore))
        if not post or post[-1].end() != len(fore):
            continue
        ort = nasta.strip().strip('|').strip()
        ort = re.sub(r'^(?:[-+*]|\d+[.)])\s+', '', ort)
        ort = re.sub(r'^(?:postort|ort)\s*[:|]\s*', '', ort, flags=re.I)
        ort = ort.rstrip('.')
        if ort and not any(c.islower() for c in ort):
            ort = re.sub(r"[^\W\d_]+", lambda m: m.group(0).capitalize(), ort)
        if not re.fullmatch(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*(?:[ \t]+[^\W\d_]+(?:[-'’][^\W\d_]+)*){0,3}", ort):
            continue
        ord_ = ort.split()
        if all(_versal(w) or w.isupper() for w in ord_) and not any(vik(w) in ej for w in ord_) \
                and not all(vik(w) in regioner for w in ord_):
            extra.append(fore + ' ' + ort)
    for rad in rader + extra:
        rad = unicodedata.normalize('NFC', rad)
        if not any(c.islower() for c in rad):  # en rad i versaler läses som vanlig text
            rad = re.sub(r"[^\W\d_]+", lambda m: m.group(0).capitalize(), rad)
        post = []
        for m in POSTNUMMER_I_TEXT.finditer(rad):
            siffror.add(m.group(1) + m.group(2))
            post.append((m.start(), m.end()))
        for m in NUMMER_I_TEXT.finditer(rad):
            d = re.sub(r'\D', '', m.group(0))
            siffror.update({d, d[-6:]} | ({d[1:]} if d.startswith('0') and len(d) >= 9 else set()))
        tm = list(TEXTORD.finditer(rad))
        t = [m.group(0) for m in tm]
        stor = [_versal(w) for w in t]
        # meningarna; en punkt efter ett tal eller ett kort ord ("St.", "ca.") avslutar ingen mening
        meningar, a = [], 0
        for i, w in enumerate(t):
            if w in ('!', '?', ';') or (w == '.' and not (i and (t[i - 1].isdigit() or len(t[i - 1]) <= 3))):
                meningar.append((a, i))
                a = i + 1
        meningar.append((a, len(t)))
        def versalt(i, b, hogst):  # ord med stor bokstav från t[i], högst hogst stycken: index efter dem
            k = i
            while k < b and stor[k] and k - i < hogst:
                k += 1
            return k

        def ort_ok(i, k):
            ort = [vik(x) for x in t[i:k]]
            return k > i and not any(o in ej for o in ort) and not all(o in regioner for o in ort)
        for a, b in meningar:
            if b <= a:
                continue
            gata_idx, gata_slut = set(), []
            for i in range(a, b):
                w, wl = t[i], t[i].lower()
                nummer = i + 1 < b and t[i + 1].isdigit()
                if not re.fullmatch(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", w):
                    continue
                stark = any(wl.endswith(s) and len(wl) >= len(s) + 2 for s in GATULED) and (stor[i] or nummer)
                svag = any(wl.endswith(s) and len(wl) >= len(s) + 2 for s in GATULED_SVAGA) and stor[i] and nummer
                if stark or svag:
                    s = i
                    while s > a and stor[s - 1] and vik(t[s - 1]) in regioner:
                        s -= 1
                    gator.add(fras([w]))
                    gator.add(fras(t[s:i + 1]))
                    gata_idx.update(range(s, i + 1))
                    gata_slut.append(i)
                elif wl in GATUORD and i > a and stor[i - 1]:
                    s = i - 1
                    while s > a and stor[s - 1]:
                        s -= 1
                    if i - s >= 2 or s > a or nummer:
                        gator.update(fras(t[k:i + 1]) for k in range(s, i))
                        gata_idx.update(range(s, i + 1))
                        gata_slut.append(i)
            # namnet efter c/o
            for i in range(a, b - 3):
                if t[i].lower() == 'c' and t[i + 1] == '/' and t[i + 2].lower() == 'o' and stor[i + 3]:
                    namn.add(fras(t[i + 3:versalt(i + 3, b, 3)]))
            # orten efter postnumret
            postnr = [p for p in post if tm[a].start() <= p[0] < tm[b - 1].end()]
            for _, slut in postnr:
                i = next((k for k in range(a, b) if tm[k].start() >= slut), None)
                if i is not None and stor[i]:
                    orter.add(fras(t[i:versalt(i, b, 3)]))
            # orten efter gatan, husnumret och ett komma, sist i satsen ("Exempelgatan 3, Fiktivby.")
            for g in gata_slut:
                i = g + 1
                while i < b and (t[i].isdigit() or (len(t[i]) == 1 and t[i].isalpha() and t[i].isupper())):
                    i += 1
                if i > g + 1 and i + 1 < b and t[i] == ',' and stor[i + 1]:
                    k = versalt(i + 1, b, 3)
                    if (k == b or not re.fullmatch(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", t[k])) and ort_ok(i + 1, k):
                        orter.add(fras(t[i + 1:k]))
            # orten efter en preposition i en adressmening
            if gata_idx or postnr or any('adress' in vik(t[k]) for k in range(a, b)):
                for i in range(a + 1, b):
                    if vik(t[i - 1]) in ADRESSPREP and stor[i] and i not in gata_idx:
                        k = i
                        while k < b and stor[k] and k not in gata_idx and k - i < 4:
                            k += 1
                        if ort_ok(i, k):
                            orter.add(fras(t[i:k]))
    return {'gator': {g for g in gator if g}, 'orter': {o for o in orter if o}, 'namn': {n for n in namn if n},
            'siffror': {s for s in siffror if len(s) >= 5}}


def forbjudna_termer(slug, underlag=None):
    """Kundens uppgifter som aldrig får gå till Refero eller Mobbin (BESLUT.md 2026-10-05, punkt 4; granskningen V9 och
    granskning 2, N3): namnet och dess ord (minst fyra tecken), orterna (adress och räckvidd), gatan, webbadressen
    (webb är ett objekt med strängvärden, till exempel doman), e-postadressernas domäner och namnord, och nummer
    (organisationsnummer, postnummer, telefon) som siffersträngar. Fritexten not och kontaktvägarnas belägg läses för
    gator, postnummer, orten efter postnumret eller gatan, orter i en adressmening, namnet efter c/o och långa nummer
    (adresser_i_text; granskningen GR-20261007-r104, B1). {'ord': set, 'siffror': set, 'bransch': set}."""
    v = las_json(Path(underlag or UNDERLAG) / slug / 'VERKSAMHET.json') or {}
    ord_, siffror = set(), set()
    namn = vik(v.get('namn') or '').strip()
    if namn:
        ord_.add(namn)
        ord_.update(w for w in re.split(r'[^a-z0-9]+', namn) if len(w) >= 4)
    adress = v.get('adress') if isinstance(v.get('adress'), dict) else {}
    orter = list((v.get('rackvidd') or {}).get('orter') or []) if isinstance(v.get('rackvidd'), dict) else []
    for x in [adress.get('ort'), adress.get('gata'), adress.get('gatuadress')] + orter:
        if isinstance(x, str) and len(x.strip()) >= 3:
            ord_.add(vik(x.strip()))
    for x in (adress.get('gata'), adress.get('gatuadress')):  # gatans namn utan nummer ("Storgatan"; granskningen 2026-10-05, fynd 8)
        if isinstance(x, str):
            ord_.update(w for w in re.split(r'[^a-z0-9]+', vik(x)) if len(w) >= 5 and not w.isdigit())
    webb = v.get('webb')
    webbar = [x for x in (webb.values() if isinstance(webb, dict) else [webb]) if isinstance(x, str)]
    kontakter = [k.get('varde') for k in v.get('kontaktvagar') or [] if isinstance(k, dict) and isinstance(k.get('varde'), str)]
    epost = [x for x in [v.get('e_post')] + kontakter + list(v.get('sokkonsol_agare') or []) if isinstance(x, str) and '@' in x]
    for e in epost:
        lokal, _, doman = vik(e).strip().partition('@')
        webbar.append(doman)
        ord_.update(w for w in re.split(r'[^a-z0-9]+', lokal) if len(w) >= 4 and w not in ALLMANNA_EPOSTORD)
    for w in webbar:
        d = re.sub(r'^https?://(www\.)?', '', vik(w).strip()).split('/')[0]
        if d:
            ord_.update({d, d.split('.')[0]})
    nummer = [v.get('orgnr'), adress.get('postnummer')] + kontakter
    siffror.update(d for d in (re.sub(r'\D', '', str(x or '')) for x in nummer) if len(d) >= 5)
    # ett svenskt nummer känns igen också i internationell form (+46 utan nollan): de sista siffrorna efter nollan
    siffror.update(d[1:] for d in list(siffror) if d.startswith('0') and len(d) >= 9)
    # telefonnumrets sista sex siffror ("11 22 33" utan riktnummer; granskningen 2026-10-05, fynd 8)
    siffror.update(re.sub(r'\D', '', k)[-6:] for k in kontakter if len(re.sub(r'\D', '', k)) >= 8)
    # fritexten: en andra adress, ett postnummer eller ett nummer som inte står i fälten (GR-20261007-r104, B1)
    fritext = [v.get('not')] + [k.get('belagg') for k in v.get('kontaktvagar') or [] if isinstance(k, dict)]
    for x in fritext:
        if isinstance(x, str):
            a = adresser_i_text(x)
            ord_.update(a['gator'] | a['orter'] | a['namn'])
            siffror.update(a['siffror'])
    # branschens ord (kategorierna) ingår i ett namn som "Snickaren": de prövas bara som hela ord, aldrig som delsträng
    bransch = {w for k in (v.get('kategorier') or []) if isinstance(k, str) for w in re.split(r'[^a-z0-9]+', vik(k)) if len(w) >= 4}
    return {'ord': {o for o in ord_ if len(o) >= 3}, 'siffror': siffror, 'bransch': bransch}


def namner_kunden(text, forbjudna):
    """Nämner texten kundens namn, ort, webbadress, e-post eller nummer (forbjudna_termer)? Prövas före och oberoende
    av frågans form, så att ett formfel aldrig döljer kundens uppgifter (granskning 2, N3)."""
    if not forbjudna:
        return False
    import urllib.parse
    text = urllib.parse.unquote(str(text))  # URL-kodning (%C3%A5) döljer aldrig ett namn
    vt, st_ = vik(text), re.sub(r'\D', '', text)
    hopskrivet = re.sub(r'[^a-z0-9]+', '', vt)  # bokstäver med mellanrum och sammansättningar ("ortnamnsforetag")
    return any(re.search(r'(?<![a-z0-9])%s(?![a-z0-9])' % re.escape(o), vt) for o in forbjudna.get('ord') or ()) \
        or any(len(o) >= 5 and not any(b in o for b in forbjudna.get('bransch') or ()) and re.sub(r'[^a-z0-9]+', '', o) in hopskrivet
               for o in forbjudna.get('ord') or ()) \
        or any(x in st_ for x in forbjudna.get('siffror') or ())


SPARRAD_FORM = re.compile(r'https?:|www\.|@|\d{5,}')  # adresser, e-post och långa sifferföljder går aldrig till tjänsterna


def kanal_fel(begaran, bred=False, forbjudna=None):
    """Skälet när en begäran går utanför kanalens form, annars None. bred: researchsteget (fler sajter och frågor).
    forbjudna (forbjudna_termer): frågorna till tjänsterna får aldrig nämna kundens namn, orter eller nummer."""
    max_k, max_f = (MAX_KANDIDATER_BRED, MAX_FRAGOR_BRED) if bred else (MAX_KANDIDATER, MAX_FRAGOR)
    ref = begaran.get('referens')
    kand = (ref or {}).get('kandidater') if isinstance(ref, dict) else None
    if ref is not None and (not isinstance(kand, list) or not 1 <= len(kand) <= max_k):
        return 'referens.kandidater ska vara 1–%d kandidater' % max_k
    for k in kand or []:
        if not isinstance(k, dict) or not VARD.fullmatch(str(k.get('adress') or '')):
            return ('adressen ska vara en sajts ursprung, https://värd/ med små bokstäver och korta etiketter i a–z, 0–9 och '
                    'bindestreck; en domän med å, ä eller ö skrivs i punycode (xn--…)')
        sidor = k.get('sidor') or ['/']
        if not isinstance(sidor, list) or len(sidor) > MAX_SIDOR_PER or any(not isinstance(s, str) or len(s) > 160 or not SIDVAG.fullmatch(s) for s in sidor):
            return ('sidvägarna ska vara högst %d vägar med högst fyra led om högst 60 tecken (bokstäver a–z, siffror, punkt, '
                    'bindestreck; å, ä, ö och andra tecken procentkodade, till exempel /tj%%C3%%A4nster/), utan frågesträng '
                    'eller fragment' % MAX_SIDOR_PER)
    tj = begaran.get('tjanster')
    if tj is not None:
        fr = tj.get('fragor') if isinstance(tj, dict) else None
        if not isinstance(fr, list) or not 1 <= len(fr) <= max_f:
            return 'tjanster.fragor ska vara 1–%d frågor' % max_f
        for f in fr:
            text = ' '.join(str((f or {}).get(x) or '') for x in ('fraga', 'syfte')) if isinstance(f, dict) else ''
            if namner_kunden(text, forbjudna):  # före formen: ett formfel får aldrig dölja kundens uppgifter
                return 'en fråga till tjänsterna nämner kundens namn, ort eller nummer; beskriv bara branschen och vad sökningen ska ge'
            if not isinstance(f, dict) or not text.strip() or len(str(f.get('fraga') or '')) > MAX_FRAGA or len(str(f.get('syfte') or '')) > MAX_FRAGA \
                    or SPARRAD_FORM.search(text):
                return 'en fråga till tjänsterna är högst %d tecken, utan adresser eller långa sifferföljder' % MAX_FRAGA
    return None


TRAD = set()  # referenssteg som pågår i den här processen (kor_trad): stoppet avslutar dem med sina träd


def avsluta_trad():
    """Avslutar varje pågående referenssteg med hela dess träd (tjänstesessionernas claude, referenssidornas node). Kallas
    av arbetarens stopp, så att en komplettering aldrig lever kvar efter --stoppa (kvällens stopp 2026-10-05 lämnade en
    Refero-session kvar)."""
    import nastlad
    ut = []
    for pid in list(TRAD):
        ut += nastlad.doda_trad(pid)
        TRAD.discard(pid)
    return ut


def kor_trad(args, timeout):
    """Ett referenssteg i egen processgrupp; vid tidsgräns avslutas hela trädet, också tjänstesessionernas claude och
    referenssidornas node (granskning 3, S3). Steget registreras i TRAD medan det pågår (stoppet når det)."""
    import nastlad
    p = subprocess.Popen(args, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ),
                         start_new_session=True)
    TRAD.add(p.pid)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        nastlad.doda_trad(p.pid)
        p.communicate()
        raise
    finally:
        TRAD.discard(p.pid)
    return subprocess.CompletedProcess(args, p.returncode, out, err)


def komplettera(slug, fil, rot, underlag=None, frist=3600, kor=None, bred=False, forbjudna=None, las_frist=None):
    """Research på begäran (Codex 2026-10-05, punkt 3 och 4): skaparens KOMPLETTERING.json blir uppdrag till det befintliga
    referenssteget (referens.py ger en ny komplett paketversion som ärver det förra; referenstjanster.py söker i Refero och
    Mobbin). Begäran flyttas till <rot>/kompletteringar/, tjänsternas förra rapport sparas under tjanster/tidigare/ innan
    den skrivs om. Ger en sammanfattning: {'tid', 'varfor', 'referens': {...}, 'tjanster': {...}}."""
    import shutil
    underlag = Path(underlag or UNDERLAG)
    u = underlag / slug
    kor = kor or kor_trad
    tid = '%s-%s' % (nu().replace(':', ''), os.urandom(3).hex())  # två begäranden samma sekund får egna filer (granskning 2, N7)
    try:
        begaran = json.loads(Path(fil).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        begaran = {'fel': 'begäran gick inte att läsa: %s' % e}
    arkiv = Path(rot) / 'kompletteringar'
    arkiv.mkdir(parents=True, exist_ok=True)
    shutil.move(str(fil), str(arkiv / ('%s.json' % tid)))
    ut = {'tid': tid, 'varfor': str(begaran.get('varfor') or '')[:1000] if isinstance(begaran, dict) else '', 'begaran': rel(arkiv / ('%s.json' % tid))}
    if not isinstance(begaran, dict) or begaran.get('fel'):
        ut['fel'] = (begaran or {}).get('fel') if isinstance(begaran, dict) else 'begäran är inget JSON-objekt'
        return ut
    fel = kanal_fel(begaran, bred=bred, forbjudna=forbjudna if forbjudna is not None else forbjudna_termer(slug, underlag))
    if fel:  # adresserna och frågorna är sessionens enda väg ut; de begränsas i form och mängd
        ut['fel'] = fel
        return ut
    # en begäran åt gången per kund (granskningen V8): samtidiga skapare skriver annars över varandras paket och rapport
    import fcntl
    (u / 'referenser').mkdir(parents=True, exist_ok=True)
    with open(u / 'referenser' / '.forskningslas', 'w') as las_:
        if las_frist is None:
            fcntl.flock(las_, fcntl.LOCK_EX)
        else:  # en skiss väntar bara så länge dess försök räcker (granskning 3, S8)
            slut = time.time() + max(0, las_frist)
            while True:
                try:
                    fcntl.flock(las_, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.time() >= slut:
                        ut['fel'] = 'researchlåset var upptaget av en annan kandidats begäran under hela väntetiden'
                        return ut
                    time.sleep(2)
        if isinstance(begaran.get('referens'), dict):
            upp = dict(begaran['referens'])
            forra = senaste_paket(slug, underlag)
            if forra and not upp.get('kompletterar'):
                upp['kompletterar'] = forra.name  # den nya versionen ärver allt oförändrat, så att alla Bildval kan peka dit
            f = u / ('REFERENSUPPDRAG-%s.json' % tid)
            f.write_text(json.dumps(upp, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            try:
                r = kor([sys.executable, '-B', str(ROOT / 'kontroller' / 'referens.py'), slug, '--uppdrag', rel(f)], frist)
                ut['referens'] = {'rc': r.returncode, 'paket': rel(senaste_paket(slug, underlag) or u), 'utdrag': (r.stdout + r.stderr)[-1500:]}
            except subprocess.TimeoutExpired:
                ut['referens'] = {'rc': None, 'utdrag': 'referenssteget nådde tidsgränsen %d s' % frist}
        if isinstance(begaran.get('tjanster'), dict):
            t = u / 'referenser' / 'tjanster'  # referenstjanster.samla flyttar den förra rapporten till tidigare/ (radera inget)
            f = u / ('TJANSTEUPPDRAG-%s.json' % tid)
            f.write_text(json.dumps(begaran['tjanster'], ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            try:
                r = kor([sys.executable, '-B', str(ROOT / 'kontroller' / 'referenstjanster.py'), slug, '--uppdrag', rel(f)], frist)
                rapport = t / 'TJANSTER.md'
                if rapport.is_file() and not rapport.is_symlink():  # den här begärans rapport, kvar när nästa skriver om TJANSTER.md
                    shutil.copyfile(rapport, t / ('TJANSTER-%s.md' % tid))
                    rapport = t / ('TJANSTER-%s.md' % tid)
                ut['tjanster'] = {'rc': r.returncode, 'rapport': rel(rapport), 'utdrag': (r.stdout + r.stderr)[-1500:]}
            except subprocess.TimeoutExpired:
                ut['tjanster'] = {'rc': None, 'utdrag': 'tjänsterna nådde tidsgränsen %d s' % frist}
    if not ut.get('referens') and not ut.get('tjanster'):
        ut['fel'] = 'begäran har varken referens eller tjanster'
    with open(arkiv / ('%s-svar.json' % tid), 'w', encoding='utf-8') as fh:
        json.dump(ut, fh, ensure_ascii=False, indent=1)
    return ut


def kompletteringsrader(svar):
    """Resultatet av en begäran, för nästa sessions prompt."""
    if not svar:
        return []
    rader = ['Researchen du begärde (%s, %s) är gjord:' % (svar.get('tid'), svar.get('begaran'))]
    if svar.get('varfor'):
        rader.append('- varför: ' + svar['varfor'])
    if svar.get('fel'):
        rader.append('- den kunde inte köras: ' + svar['fel'])
    if svar.get('referens'):
        r = svar['referens']
        rader.append('- referenssteget (slutkod %s; 0 = alla fångade, 1 = brister står i PAKET.md): %s/PAKET.md och bilderna där' % (r.get('rc'), r.get('paket', '?')))
    if svar.get('tjanster'):
        r = svar['tjanster']
        rader.append('- referenstjänsterna (slutkod %s): %s med träffarnas bilder' % (r.get('rc'), r.get('rapport', '?')))
    rader.append('Läs resultatet med Read och bedöm bilderna, inte bara beskrivningarna, innan du använder det.')
    return rader


# --- godkännandet (granskningen av skapandeflödet, punkt 2) ---

def sha256_fil(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_katalog(p):
    """Hashen över en katalogs filer (relativa vägar och innehåll, i ordning); en länk i katalogen räknas med som länk, så
    att en utbytt fil aldrig får samma hash."""
    import hashlib
    h = hashlib.sha256()
    bas = Path(p)
    for katalog, kataloger, filer in os.walk(bas, followlinks=False):
        kataloger.sort()
        for fn in sorted(filer + [k for k in kataloger if (Path(katalog) / k).is_symlink()]):
            f = Path(katalog) / fn
            h.update(f.relative_to(bas).as_posix().encode() + b'\0')
            h.update(b'LANK' if f.is_symlink() else f.read_bytes() if f.is_file() else b'')
            h.update(b'\0')
    return h.hexdigest()


def sha256_katalog_strikt(p):
    """Manifest för en fryst katalog: läsfel och utelämnade länkar ger inget kvitto."""
    import stat
    import hashlib
    bas = Path(p)
    if bas.is_symlink() or not bas.is_dir():
        raise ValueError('fryst katalog saknas eller är länkad')
    def fel(e):
        raise e
    filer = []
    for rot_, kataloger, namn in os.walk(bas, followlinks=False, onerror=fel):
        if any((Path(rot_) / n).is_symlink() for n in kataloger):
            raise ValueError('länk i fryst katalog')
        for n in namn:
            f = Path(rot_) / n
            if not stat.S_ISREG(f.lstat().st_mode):
                raise ValueError('länk eller specialfil i fryst katalog')
            filer.append(f)
    h = hashlib.sha256()
    for f in sorted(filer):
        h.update(f.relative_to(bas).as_posix().encode() + b'\0' + f.read_bytes() + b'\0')
    return h.hexdigest()


def godkand_giltig(slug, underlag=None, kunder=None):
    """(giltig, skäl): ägarens godkännande i atelje/VINNARE.json gäller bara när ägarens senaste dom i domloggen
    (ar_agarens: ägaren, eller ägaren via Codex med belägg) är just det godkännandet och den godkända startsidan och
    DESIGN.md i atelje/vinnare/ är oförändrade sedan dess. En vidarebefordrad AI-bedömning varken godkänner eller drar
    tillbaka något. Går en rad efter godkännandet inte att läsa gäller det inte: där kan ägarens senare beslut stå. kor.sh
    tar vid först när det gäller; bygget skriver sedan om sajtens egna filer utan att godkännandet upphör, och nekas
    underlagsgrunden (UNDERLAGSGRUND och UNDERLAGSKATALOGER; kor.sh och sandlada.py --fryst-underlag)."""
    u = Path(underlag or UNDERLAG) / slug
    sajt = Path(kunder or (ROOT / 'kunder')) / slug / 'sajt'
    import kundstart_kalla
    if not kundstart_kalla.giltig(u):
        return False, kundstart_kalla.SKAL
    g = (las_json(u / 'atelje' / 'VINNARE.json') or {}).get('godkand')
    if not isinstance(g, dict) or not g.get('tid'):
        return False, 'inget godkännande i VINNARE.json'
    ag = agarens_senaste(slug, u.parent)
    if ag['oklara']:
        return False, oklara_text(ag)
    d_ = ag['dom']
    if not d_ or d_.get('beslut') != 'godkand' or d_.get('tid') != g['tid']:
        return False, 'ägarens senaste dom i domloggen (ägaren, eller ägaren via Codex med belägg) är inte godkännandet'
    st = las_json(u / 'atelje' / 'STATUS.json') or {}
    if str(st.get('startad') or '') > g['tid']:  # en ny förfining skriver i sajten: dess resultat behöver en ny dom (granskning 5)
        return False, 'en ny körning i skapandeflödet startade efter godkännandet (%s)' % st.get('startad')
    try:
        if g.get('underlag_sha') and underlagsversion(slug, u.parent) != g['underlag_sha']:
            return False, 'underlaget ändrades sedan godkännandet; en ny bedömning behövs'
        if g.get('sha_material') and sha256_katalog_strikt(u / 'atelje/vinnare/material') != g['sha_material']:
            return False, 'kandidatens godkända material är ändrat sedan godkännandet'
    except (OSError, ValueError):
        return False, 'underlaget eller det godkända materialet kunde inte verifieras'
    # den dömda versionen, som vinnaren bevarar: bygget skriver om sajtens egna filer (omgranskning 3, fynd 1)
    kod, vd = u / 'atelje' / 'vinnare' / 'kod' / 'index.astro', u / 'atelje' / 'vinnare' / 'DESIGN.md'
    if g.get('sha_kod') and ((u / 'atelje' / 'vinnare' / 'kod').is_symlink() or sha256_katalog(u / 'atelje' / 'vinnare' / 'kod') != g['sha_kod']):
        return False, 'kandidatens godkända sidor (atelje/vinnare/kod/) är ändrade sedan godkännandet'
    if g.get('sha_kodsrc') and ((u / 'atelje' / 'vinnare' / 'kod-src').is_symlink() or sha256_katalog(u / 'atelje' / 'vinnare' / 'kod-src') != g['sha_kodsrc']):
        return False, 'kandidatens godkända komponenter och stilar (atelje/vinnare/kod-src/) är ändrade sedan godkännandet'
    if not kod.is_file() or kod.is_symlink() or sha256_fil(kod) != g.get('sha_index'):
        return False, 'den godkända startsidan (atelje/vinnare/kod/index.astro) är ändrad sedan godkännandet'
    if g.get('sha_design') and (not vd.is_file() or vd.is_symlink() or sha256_fil(vd) != g['sha_design']):
        return False, 'den godkända DESIGN.md (atelje/vinnare/DESIGN.md) är ändrad sedan godkännandet'
    if not g.get('sha_design') and (vd.exists() or vd.is_symlink()):  # en DESIGN.md som lagts dit efteråt (granskning 6)
        return False, 'vinnaren har en DESIGN.md som inte ingår i godkännandet'
    return True, 'godkänd %s' % g['tid']


def main(argv=None):
    """Domar och historiken utanför dashboarden: en dom som kom via Codex eller i en session förs in ordagrant
    (granskningen av skapandeflödet, punkt 1), med rätt avsändare (KALLOR; ägarens uppdrag 2026-10-07, punkt 7): ägarens
    egna ord med ett belägg (--belagg), en bedömning som ägaren vidarebefordrat som "vidarebefordrad AI-bedömning".
    Aldrig inifrån ett bygge."""
    import argparse
    p = argparse.ArgumentParser(prog='skapande', description='domloggen och riktningshistoriken för skapandeflödet')
    sub = p.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('dom', help='lägg till en dom i underlag/<slug>/DESIGNDOMAR.jsonl')
    d.add_argument('slug')
    d.add_argument('--kalla', required=True, choices=list(KALLOR), help='avsändaren (KALLOR): en bedömning som ägaren vidarebefordrat '
                   'förs in med källan "vidarebefordrad AI-bedömning", aldrig som ägarens')
    d.add_argument('--beslut', required=True, choices=BESLUT)
    d.add_argument('--fil', required=True, help='textfil med domen ordagrant')
    d.add_argument('--belagg', default='', help='för ägaren och ägaren via Codex (krävs): var ägarens egna ord står, till exempel '
                   'meddelandet och tiden')
    d.add_argument('--avser', default='')
    d.add_argument('--tid', default=None)
    d.add_argument('--kandidater', default='', help='kandidatflödet: kandidaterna domen gäller (kNN eller Förslag X, och kNN@<version> '
                   'för en tidigare bevarad version), kommaseparerade; utan @ gäller versionen som är aktuell nu')
    d.add_argument('--uppdrag', choices=list(UPPDRAGSTYPER), help='beslutet uppdrag: ratta, omarbeta eller bygg_ut')
    d.add_argument('--resultat', default='', help='beslutet uppdrag: det önskade resultatet')
    d.add_argument('--omfattning', action='append', default=[], help='beslutet uppdrag: en rad i omfattningen (upprepas)')
    d.add_argument('--bevara', action='append', default=[], help='beslutet uppdrag: det som ska bevaras (upprepas)')
    d.add_argument('--specialist', action='append', default=[], help='beslutet uppdrag: rorelse=andra|bedom eller granskning=andra|bedom; '
                   'utan flaggan typens standard, med "inga" inga pass')
    b = sub.add_parser('belagg', help='ägarens belägg i efterhand för en befintlig rad "ägaren via Codex" i domloggen: en rad i '
                                      'underlag/<slug>/%s bunden till radens sha256; loggen skrivs inte om och raden blir ingen ny dom' % BELAGGFIL)
    b.add_argument('slug')
    b.add_argument('--rad', required=True, type=int, help='radnumret i domloggen (skapande.py visa)')
    b.add_argument('--belagg', required=True, help='var ägarens egna ord står, till exempel meddelandet och tiden')
    b.add_argument('--tid', default=None)
    h = sub.add_parser('historik', help='lägg till en prövad grundidé i underlag/<slug>/RIKTNINGSHISTORIK.json')
    h.add_argument('slug')
    for f in ('kalla', 'namn', 'drag', 'utfall', 'kritik'):
        h.add_argument('--' + f, required=f != 'kritik', default='')
    h.add_argument('--tid', default=None)
    l = sub.add_parser('visa', help='domloggen och historiken som prompterna ser dem')
    l.add_argument('slug')
    a = p.parse_args(argv)
    if os.environ.get('NWP_SLUG'):
        print('domloggen och historiken skrivs av ägaren eller en session utanför bygget, aldrig inifrån ett bygge', file=sys.stderr)
        return 2
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug) or not (UNDERLAG / a.slug).is_dir():
        print('okänt underlag: underlag/%s' % a.slug, file=sys.stderr)
        return 2
    if a.cmd == 'dom':
        import atelje  # samma väg som dashboarden: godkännandet prövas före domen, en annan dom från ägaren drar tillbaka det
        extra = {}
        # ägarens ord utanför dashboarden (ägarens uppdrag 2026-10-07, punkt 7): belägget säger var ägarens egna ord står;
        # en bedömning som ägaren vidarebefordrat är källan "vidarebefordrad AI-bedömning", aldrig ägarens
        if KALLOR[a.kalla][0] in ('agaren', 'kunden') and not a.belagg.strip():
            print('domen skrevs inte: källan %s kräver --belagg (var %s egna ord står); en bedömning som ägaren '
                  'vidarebefordrat förs in med --kalla "vidarebefordrad AI-bedömning"' % (a.kalla, 'kundens' if a.kalla == 'kunden' else 'ägarens'),
                  file=sys.stderr)
            return 2
        if a.beslut == 'uppdrag':
            spec = None
            if a.specialist:
                spec = {}
                for x in a.specialist:
                    if x == 'inga':
                        continue
                    k_, _, v_ = x.partition('=')
                    spec[k_.strip()] = v_.strip()
            extra['uppdrag'] = {'typ': a.uppdrag, 'resultat': a.resultat, 'omfattning': a.omfattning, 'bevara': a.bevara,
                                **({'specialister': spec} if spec is not None else {})}
        if a.belagg.strip():
            extra['belagg'] = a.belagg.strip()
        if a.kandidater:  # en dom via Codex kan namnge förslagen med ägarens etiketter (Förslag C) eller id (k03)
            import kandidater
            omv = {v.split()[-1].upper(): k for k, v in kandidater.etiketter(a.slug, kandidater.lista(a.slug)).items()}
            extra['kandidater'] = []
            for x in (s.strip() for s in a.kandidater.split(',') if s.strip()):
                x, _, ver = x.partition('@')
                kid = x if kandidater.ID.fullmatch(x) else omv.get(x.split()[-1].upper())
                if not kid:
                    print('domen skrevs inte: okänd kandidat %r' % x, file=sys.stderr)
                    return 2
                aktuell = kandidater.las_status(a.slug, kid).get('version') or ''
                full = next((v_ for v_ in kandidater.valbara_versioner(kandidater.las_status(a.slug, kid)) if ver and v_.startswith(ver)), None)
                extra['kandidater'].append({'id': kid, 'version': full or (ver if ver else aktuell)})
        try:
            post = atelje.doma(a.slug, a.kalla, a.beslut, Path(a.fil).read_text(encoding='utf-8'), avser=a.avser, tid=a.tid, **extra)
        except ValueError as e:
            print('domen skrevs inte: %s' % e, file=sys.stderr)
            return 2
        print('domen tillagd: %s, %s, %s%s; avsändaren: %s' % (post['tid'], post['kalla'], post['beslut'],
                                                                {'godkand': '; startsidan godkänd för bygget'}.get(post['beslut'], '') if ar_agarens(post) else '',
                                                                avsandare(post)['text']))
    elif a.cmd == 'belagg':
        try:
            post = lagg_till_belagg(a.slug, a.rad, a.belagg, tid=a.tid)
        except ValueError as e:
            print('belägget skrevs inte: %s' % e, file=sys.stderr)
            return 2
        d_ = next(p_ for r_, _s, p_ in domlogg(a.slug)['domar'] if r_ == a.rad)
        print('belägget tillagt för rad %d (dom %s, sha256 %s…): avsändaren nu %s' % (a.rad, post['dom_tid'], post['sha256'][:12], avsandare(d_)['text']))
    elif a.cmd == 'historik':
        lagg_till_historik(a.slug, [{k: getattr(a, k) for k in ('kalla', 'namn', 'drag', 'utfall', 'kritik')} | ({'tid': a.tid} if a.tid else {})])
        print('historiken har %d poster' % len(historik(a.slug)))
    else:
        aktuella = kritikrader(a.slug, aktuella=True)  # det som gäller; historiken under, som uppslag
        lg = domlogg(a.slug)
        andra = [(r, avsandare(p)) for r, _s, p in lg['domar'] if not ar_agarens(p)]
        bil_o = lg.get('bilaga_olasbara') or []
        print('\n'.join((aktuella or ['Inga aktuella domar för kunden.'])
                        + (['', 'Rader som inte är ägarens beslut (räknas aldrig som ägarens): '
                            + '; '.join('rad %d: %s' % (r, x['text']) for r, x in andra)] if andra else [])
                        + (['', olasbara_text(lg)] if lg['olasbara'] else [])
                        + (['', 'underlag/%s/%s: %d rad(er) går inte att läsa och räknas inte (%s)' % (
                            a.slug, BELAGGFIL, len(bil_o), '; '.join('rad %d: %s' % (x['rad'], x['skal']) for x in bil_o[:6]))] if bil_o else [])
                        + ['', 'Historik (slås upp, inga regler):'] + (historikrader(a.slug) or ['tom'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
