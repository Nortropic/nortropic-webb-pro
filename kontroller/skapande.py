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
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
DOMLOGG = 'DESIGNDOMAR.jsonl'
HISTORIK = 'RIKTNINGSHISTORIK.json'
BESLUT = ('godkand', 'putsa', 'ny_riktning')
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


def metodrader(steg):
    m = METOD[steg]
    return ['- ' + f for f in m['filer']] + ['- skillen %s (Skill-verktyget, eller .claude/skills/%s/SKILL.md med Read)' % (s, s) for s in m['skills']]


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


def kritikrader(slug, antal=3, underlag=None):
    """Ägarens senaste domar ordagrant, nyast först, med vad de återöppnar: prompternas första underlag."""
    egna = [d for d in domar(slug, underlag) if d.get('kalla') in AGAREN][-antal:]
    if not egna:
        return []
    rader = ['Ägarens senaste domar över designen (underlag/%s/%s), nyast först. De väger tyngst av allt du läser; en senare' % (slug, DOMLOGG),
             'dom går före en tidigare, och före äldre lärdomar och tidigare designval:']
    for d in reversed(egna):
        rader.append('- %s, %s, beslut %s%s:' % (d.get('tid', '?'), d.get('kalla'), d['beslut'],
                                                  (' (återöppnar: %s)' % ', '.join(d.get('ateroppnar') or [])) if d.get('ateroppnar') else ''))
        rader += ['  > ' + r for r in d['text'].splitlines() if r.strip()]
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
VARD = re.compile(r'https://(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.){1,3}[a-z]{2,12}/')  # fullmatch; etiketter upp till 63 tecken
LED = r'(?!\.+(?:/|$))(?:[A-Za-z0-9._~-]|%[0-9A-Fa-f]{2}){1,60}'  # å, ä, ö procentkodade; inte bara punkter
SIDVAG = re.compile(r'/(?:%s(?:/%s){0,3}/?)?' % (LED, LED))  # fullmatch; högst fyra led med snedstreck emellan


def kanal_fel(begaran):
    """Skälet när en begäran går utanför kanalens form, annars None."""
    ref = begaran.get('referens')
    kand = (ref or {}).get('kandidater') if isinstance(ref, dict) else None
    if ref is not None and (not isinstance(kand, list) or not 1 <= len(kand) <= MAX_KANDIDATER):
        return 'referens.kandidater ska vara 1–%d kandidater' % MAX_KANDIDATER
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
        if not isinstance(fr, list) or not 1 <= len(fr) <= MAX_FRAGOR:
            return 'tjanster.fragor ska vara 1–%d frågor' % MAX_FRAGOR
        for f in fr:
            text = ' '.join(str((f or {}).get(x) or '') for x in ('fraga', 'syfte')) if isinstance(f, dict) else ''
            if not isinstance(f, dict) or not text.strip() or len(str(f.get('fraga') or '')) > MAX_FRAGA or len(str(f.get('syfte') or '')) > MAX_FRAGA \
                    or re.search(r'https?:|www\.|@|\d{5,}', text):
                return 'en fråga till tjänsterna är högst %d tecken, utan adresser eller långa sifferföljder' % MAX_FRAGA
    return None


def komplettera(slug, fil, rot, underlag=None, frist=3600, kor=None):
    """Research på begäran (Codex 2026-10-05, punkt 3 och 4): skaparens KOMPLETTERING.json blir uppdrag till det befintliga
    referenssteget (referens.py ger en ny komplett paketversion som ärver det förra; referenstjanster.py söker i Refero och
    Mobbin). Begäran flyttas till <rot>/kompletteringar/, tjänsternas förra rapport sparas under tjanster/tidigare/ innan
    den skrivs om. Ger en sammanfattning: {'tid', 'varfor', 'referens': {...}, 'tjanster': {...}}."""
    import shutil
    underlag = Path(underlag or UNDERLAG)
    u = underlag / slug
    kor = kor or (lambda args, timeout: subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=dict(os.environ)))
    tid = nu().replace(':', '')
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
    fel = kanal_fel(begaran)
    if fel:  # adresserna och frågorna är sessionens enda väg ut; de begränsas i form och mängd
        ut['fel'] = fel
        return ut
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
        t = u / 'referenser' / 'tjanster'
        if (t / 'TJANSTER.md').is_file():  # den förra rapporten skrivs om av körningen: spara den först (radera inget)
            (t / 'tidigare').mkdir(parents=True, exist_ok=True)
            for n in ('TJANSTER.md', 'TJANSTER.json'):
                if (t / n).is_file():
                    shutil.copy2(t / n, t / 'tidigare' / ('%s-%s' % (tid, n)))
        f = u / ('TJANSTEUPPDRAG-%s.json' % tid)
        f.write_text(json.dumps(begaran['tjanster'], ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        try:
            r = kor([sys.executable, '-B', str(ROOT / 'kontroller' / 'referenstjanster.py'), slug, '--uppdrag', rel(f)], frist)
            ut['tjanster'] = {'rc': r.returncode, 'rapport': rel(t / 'TJANSTER.md'), 'utdrag': (r.stdout + r.stderr)[-1500:]}
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
        try:
            post = atelje.doma(a.slug, a.kalla, a.beslut, Path(a.fil).read_text(encoding='utf-8'), avser=a.avser, tid=a.tid)
        except ValueError as e:
            print('domen skrevs inte: %s' % e, file=sys.stderr)
            return 2
        print('domen tillagd: %s, %s, %s%s' % (post['tid'], post['kalla'], post['beslut'], {'godkand': '; startsidan godkänd för bygget'}.get(post['beslut'], '') if post['kalla'] in AGAREN else ''))
    elif a.cmd == 'historik':
        lagg_till_historik(a.slug, [{k: getattr(a, k) for k in ('kalla', 'namn', 'drag', 'utfall', 'kritik')} | ({'tid': a.tid} if a.tid else {})])
        print('historiken har %d poster' % len(historik(a.slug)))
    else:
        print('\n'.join(kritikrader(a.slug) + [''] + historikrader(a.slug)) or 'tomt')
    return 0


if __name__ == '__main__':
    sys.exit(main())
