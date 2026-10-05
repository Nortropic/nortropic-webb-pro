#!/usr/bin/env python3
"""skapande.py — det gemensamma skapandeflödets delar: ägarens domlogg, riktningshistoriken, metoden per steg och
researchsteget (Codex via ägaren 2026-10-05: tre designflöden där förbättringarna inte följde med; ett skapandeflöde,
beskrivet i kunskap/skapandeflodet.md).

Ateljén (kontroller/atelje.py: utforska och välj) och prototypen (kontroller/prototyp.py: förfina, slutdom, ägaren,
överlämning) använder samma delar, så att ägarens senaste kritik, metoden och referensunderlaget följer med i varje steg.

- Domloggen underlag/<slug>/DESIGNDOMAR.jsonl: en rad per dom över designen (ägaren, ägaren via Codex, panelen), med
  beslut godkand | putsa | ny_riktning och texten ordagrant. Den arkiveras aldrig; nästa körning läser den själv. Ett
  beslut ny_riktning återöppnar alla designbeslut (ATEROPPNAR), aldrig verksamhetens fakta.
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
HISTORIK = 'RIKTNINGSHISTORIK.json'
BESLUT = ('godkand', 'putsa', 'ny_riktning', 'valj', 'jamfor', 'forkasta')
# kandidatflödets beslut (ägarens uppdrag 2026-10-05, punkt 10): valj = en eller flera kandidater vidare till förfining,
# jamfor = några kandidater sida vid sida (inget körs), forkasta = alla förkastade (flödet väntar på ny riktning);
# varje sådant beslut bär kandidaterna med sina versioner, och delar = det ägaren gillade i en kandidat
KANDIDATBESLUT = ('valj', 'jamfor', 'forkasta')
KALLOR = ('ägaren', 'ägaren via Codex', 'panelen', 'skaparen')
# ägarens domar: direkt i dashboarden eller ordagrant via Codex. Godkännandet, läget och stoppet räknar båda
# (omgranskningen av skapandeflödet, fynd 2: en underkännande dom via Codex lämnade godkännandet giltigt)
AGAREN = ('ägaren', 'ägaren via Codex')
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
}
# metoden per steg: filerna läses med Read, skillsen med Skill eller genom att läsa deras SKILL.md (Codex 2026-10-05,
# glapp 2: prototypens skapare läste ingen av dem; en installerad skill finns inte i kontexten förrän den laddas)
METOD = {
    'forska': {'filer': ['kunskap/referensjakt.md', 'kunskap/referenser-professionella.md', 'kunskap/visuell-niva.md',
                         'kunskap/externa/anthropic-frontend-design-SKILL.md'], 'skills': []},
    'utforska': {'filer': ['kunskap/externa/anthropic-frontend-design-SKILL.md', 'kunskap/externa/leonxlnx-taste-SKILL-ce26fc25.md',
                           'kunskap/externa/emil-emil-design-eng-SKILL.md', 'kunskap/bild.md', 'kunskap/referenser-professionella.md',
                           'kunskap/visuell-niva.md'], 'skills': ['better-layout', 'better-typography']},
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


# --- domloggen ---

def domar(slug, underlag=None):
    """Domloggens poster i tidsordning; en rad som inte går att läsa hoppas över och räknas i 'oläsbara'."""
    f = Path(underlag or UNDERLAG) / slug / DOMLOGG
    ut = []
    if f.is_file():
        for rad in f.read_text(encoding='utf-8').splitlines():
            try:
                post = json.loads(rad)
            except ValueError:
                continue
            if isinstance(post, dict) and post.get('beslut') in BESLUT and isinstance(post.get('text'), str):
                ut.append(post)
    return ut


def lagg_till_dom(slug, kalla, beslut, text, avser='', underlag=None, tid=None, **extra):
    """En dom till loggen (en rad, tillagd i slutet). Ger posten."""
    if kalla not in KALLOR or beslut not in BESLUT or not isinstance(text, str) or not text.strip():
        raise ValueError('domen behöver källa (%s), beslut (%s) och text' % (', '.join(KALLOR), ', '.join(BESLUT)))
    post = {'tid': tid or nu(), 'kalla': kalla, 'beslut': beslut, 'text': text.strip()[:20000], 'avser': str(avser)[:400],
            'ateroppnar': ATEROPPNAR[beslut], **extra}
    f = Path(underlag or UNDERLAG) / slug / DOMLOGG
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(post, ensure_ascii=False) + '\n')
    return post


def senaste(slug, kallor=AGAREN, underlag=None):
    """Den senaste domen från ägaren (direkt eller via Codex), eller None."""
    return next((d for d in reversed(domar(slug, underlag)) if d.get('kalla') in kallor), None)


AKTUELL_START = ('ny_riktning',)  # återöppnar designbesluten (ATEROPPNAR); en förkastning bara grundidéerna och referenserna
MAX_AKTUELLA = 6  # den aktuella linjens första dom visas alltid, och de senaste efter den


def aktuella_domar(slug, underlag=None):
    """Kundens aktuella domar: hela linjen från den senaste ägardomen som begärde en ny riktning (den återöppnar
    designbesluten); utan en sådan alla ägarens domar. De äldre är historik som slås upp (ägarens uppdrag 2026-10-05
    16:25Z; granskning 3, S6)."""
    egna = [d for d in domar(slug, underlag) if d.get('kalla') in AGAREN]
    start = max((i for i, d in enumerate(egna) if d.get('beslut') in AKTUELL_START), default=0)
    return egna[start:]


def aldre_domar(slug, underlag=None):
    egna = [d for d in domar(slug, underlag) if d.get('kalla') in AGAREN]
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
        egna = [d for d in domar(slug, underlag) if d.get('kalla') in AGAREN][-antal:]
    if not egna:
        return []
    rader = ['Ägarens %s domar över designen (underlag/%s/%s), nyast först. De väger tyngst av allt du läser; en senare' % (
                 'aktuella' if aktuella else 'senaste', slug, DOMLOGG),
             'dom går före en tidigare, och före äldre lärdomar och tidigare designval:']
    for d in reversed(egna):
        rader.append('- %s, %s, beslut %s%s:' % (d.get('tid', '?'), d.get('kalla'), d['beslut'],
                                                  (' (återöppnar: %s)' % ', '.join(d.get('ateroppnar') or [])) if d.get('ateroppnar') else ''))
        rader += ['  > ' + r for r in d['text'].splitlines() if r.strip()]
        kand = [k for k in d.get('kandidater') or [] if isinstance(k, dict)]
        plan = ' i planen %s' % d['plan'] if d.get('plan') else ''  # kandidat-id (k01–k12) gäller bara inom sin plan
        if kand:
            rader.append('  kandidaterna%s: ' % plan + ', '.join('%s (%s%s, version %s)' % (
                k.get('etikett') or k.get('id'), k.get('id'), (' "%s"' % k['titel']) if k.get('titel') else '', str(k.get('version') or '')[:12]) for k in kand))
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
    """Poster {tid, kalla, namn, drag, utfall, kritik} läggs till; filen skrivs atomiskt."""
    f = Path(underlag or UNDERLAG) / slug / HISTORIK
    allt = historik(slug, underlag) + [dict(p, tid=p.get('tid') or nu()) for p in poster]
    tmp = f.with_name('.%s.tmp%d' % (HISTORIK, os.getpid()))
    tmp.write_text(json.dumps(allt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, f)
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
            'men dess rubriker, ordning och formuleringar är ett utkast som skrivs om tillsammans med formen. %s/BRIEF.md:' % u,
            'toppuppgifterna, den primära handlingen och kraven gäller; sajtkartans bildfördelning är ett förslag. Designbeslut',
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
    """Gemener utan diakritiska tecken (å, ä → a, ö → o, é → e), för jämförelser."""
    return str(s).lower().translate(str.maketrans('åäöéèüáà', 'aaoeeuaa'))


ALLMANNA_EPOSTORD = {'info', 'kontakt', 'mail', 'post', 'order', 'offert', 'support', 'hello', 'kundtjanst', 'noreply'}


def forbjudna_termer(slug, underlag=None):
    """Kundens uppgifter som aldrig får gå till Refero eller Mobbin (BESLUT.md 2026-10-05, punkt 4; granskningen V9 och
    granskning 2, N3): namnet och dess ord (minst fyra tecken), orterna (adress och räckvidd), gatan, webbadressen
    (webb är ett objekt med strängvärden, till exempel doman), e-postadressernas domäner och namnord, och nummer
    (organisationsnummer, postnummer, telefon) som siffersträngar. {'ord': set, 'siffror': set}."""
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
    return {'ord': {o for o in ord_ if len(o) >= 3}, 'siffror': siffror}


def namner_kunden(text, forbjudna):
    """Nämner texten kundens namn, ort, webbadress, e-post eller nummer (forbjudna_termer)? Prövas före och oberoende
    av frågans form, så att ett formfel aldrig döljer kundens uppgifter (granskning 2, N3)."""
    if not forbjudna:
        return False
    vt, st_ = vik(text), re.sub(r'\D', '', text)
    return any(re.search(r'(?<![a-z0-9])%s(?![a-z0-9])' % re.escape(o), vt) for o in forbjudna.get('ord') or ()) \
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


def kor_trad(args, timeout):
    """Ett referenssteg i egen processgrupp; vid tidsgräns avslutas hela trädet, också tjänstesessionernas claude och
    referenssidornas node (granskning 3, S3)."""
    import nastlad
    p = subprocess.Popen(args, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ),
                         start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        nastlad.doda_trad(p.pid)
        p.communicate()
        raise
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


def godkand_giltig(slug, underlag=None, kunder=None):
    """(giltig, skäl): ägarens godkännande i atelje/VINNARE.json gäller bara när ägarens senaste dom i domloggen är just
    det godkännandet och den godkända startsidan och DESIGN.md i atelje/vinnare/ är oförändrade sedan dess. kor.sh tar
    vid först då; bygget skriver sedan om sajtens egna filer utan att godkännandet upphör."""
    u = Path(underlag or UNDERLAG) / slug
    sajt = Path(kunder or (ROOT / 'kunder')) / slug / 'sajt'
    g = (las_json(u / 'atelje' / 'VINNARE.json') or {}).get('godkand')
    if not isinstance(g, dict) or not g.get('tid'):
        return False, 'inget godkännande i VINNARE.json'
    egna = [d for d in domar(slug, u.parent) if d.get('kalla') in AGAREN]
    if not egna or egna[-1].get('beslut') != 'godkand' or egna[-1].get('tid') != g['tid']:
        return False, 'ägarens senaste dom i domloggen (direkt eller via Codex) är inte godkännandet'
    st = las_json(u / 'atelje' / 'STATUS.json') or {}
    if str(st.get('startad') or '') > g['tid']:  # en ny förfining skriver i sajten: dess resultat behöver en ny dom (granskning 5)
        return False, 'en ny körning i skapandeflödet startade efter godkännandet (%s)' % st.get('startad')
    # den dömda versionen, som vinnaren bevarar: bygget skriver om sajtens egna filer (omgranskning 3, fynd 1)
    kod, vd = u / 'atelje' / 'vinnare' / 'kod' / 'index.astro', u / 'atelje' / 'vinnare' / 'DESIGN.md'
    if g.get('sha_kod') and ((u / 'atelje' / 'vinnare' / 'kod').is_symlink() or sha256_katalog(u / 'atelje' / 'vinnare' / 'kod') != g['sha_kod']):
        return False, 'kandidatens godkända sidor (atelje/vinnare/kod/) är ändrade sedan godkännandet'
    if not kod.is_file() or kod.is_symlink() or sha256_fil(kod) != g.get('sha_index'):
        return False, 'den godkända startsidan (atelje/vinnare/kod/index.astro) är ändrad sedan godkännandet'
    if g.get('sha_design') and (not vd.is_file() or vd.is_symlink() or sha256_fil(vd) != g['sha_design']):
        return False, 'den godkända DESIGN.md (atelje/vinnare/DESIGN.md) är ändrad sedan godkännandet'
    if not g.get('sha_design') and (vd.exists() or vd.is_symlink()):  # en DESIGN.md som lagts dit efteråt (granskning 6)
        return False, 'vinnaren har en DESIGN.md som inte ingår i godkännandet'
    return True, 'godkänd %s' % g['tid']


def main(argv=None):
    """Ägarens domar och historiken utanför dashboarden: en dom som kom via Codex eller i en session förs in ordagrant
    (granskningen av skapandeflödet, punkt 1). Aldrig inifrån ett bygge."""
    import argparse
    p = argparse.ArgumentParser(prog='skapande', description='domloggen och riktningshistoriken för skapandeflödet')
    sub = p.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('dom', help='lägg till en dom i underlag/<slug>/DESIGNDOMAR.jsonl')
    d.add_argument('slug')
    d.add_argument('--kalla', required=True, choices=KALLOR)
    d.add_argument('--beslut', required=True, choices=BESLUT)
    d.add_argument('--fil', required=True, help='textfil med domen ordagrant')
    d.add_argument('--avser', default='')
    d.add_argument('--tid', default=None)
    d.add_argument('--kandidater', default='', help='kandidatflödet: kandidaterna domen gäller (kNN eller Förslag X), '
                   'kommaseparerade; versionerna är de som gäller nu')
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
        if a.kandidater:  # en dom via Codex kan namnge förslagen med ägarens etiketter (Förslag C) eller id (k03)
            import kandidater
            omv = {v.split()[-1].upper(): k for k, v in kandidater.etiketter(a.slug, kandidater.lista(a.slug)).items()}
            extra['kandidater'] = []
            for x in (s.strip() for s in a.kandidater.split(',') if s.strip()):
                kid = x if kandidater.ID.fullmatch(x) else omv.get(x.split()[-1].upper())
                if not kid:
                    print('domen skrevs inte: okänd kandidat %r' % x, file=sys.stderr)
                    return 2
                extra['kandidater'].append({'id': kid, 'version': kandidater.las_status(a.slug, kid).get('version')})
        try:
            post = atelje.doma(a.slug, a.kalla, a.beslut, Path(a.fil).read_text(encoding='utf-8'), avser=a.avser, tid=a.tid, **extra)
        except ValueError as e:
            print('domen skrevs inte: %s' % e, file=sys.stderr)
            return 2
        print('domen tillagd: %s, %s, %s%s' % (post['tid'], post['kalla'], post['beslut'], {'godkand': '; startsidan godkänd för bygget'}.get(post['beslut'], '') if post['kalla'] in AGAREN else ''))
    elif a.cmd == 'historik':
        lagg_till_historik(a.slug, [{k: getattr(a, k) for k in ('kalla', 'namn', 'drag', 'utfall', 'kritik')} | ({'tid': a.tid} if a.tid else {})])
        print('historiken har %d poster' % len(historik(a.slug)))
    else:
        aktuella = kritikrader(a.slug, aktuella=True)  # det som gäller; historiken under, som uppslag
        print('\n'.join((aktuella or ['Inga aktuella domar för kunden.']) + ['', 'Historik (slås upp, inga regler):'] + (historikrader(a.slug) or ['tom'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
