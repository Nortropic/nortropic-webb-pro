#!/usr/bin/env python3
"""referenskontrakt.py — det obligatoriska referensunderlaget före skapandet (ägarens uppdrag 2026-10-10: branschresearch
och professionella designreferenser obligatoriska och verksamma, och hela referenskedjan från upptäckt till tillämpning).

Kedjan: researchrollen hittar verkliga branschsajter genom webbsökning och professionell inspiration genom gallerierna
(Awwwards i varje ny designomgång) → referenssteget fångar de valda sajterna i en riktig webbläsare (referens.py: bilder i
390 och 1440, tillstånd, SEKTIONER.md, EXTRAKT.md) → planen skriver branschgenomgången, förebilderna och per kandidat
kedjan kundbehov → observerad kvalitet → designbeslut → planerad tillämpning → bedömning, med belägg i paketets bilder →
UPPDRAG.md ger varje skapare sitt urval med bilderna → skaparen jämför referensen och renderingen i samma bredder.

Modulen prövar varje länk mot det som faktiskt finns, aldrig mot vad en session påstår:
- sokningar(): WebSearch och WebFetch ur researchens transkript (fråga eller adress, utfall, adresserna i svaret);
  en adress ur minnet är en kandidat, aldrig en upptäckt.
- researchbrister(): paketets fångade sajter per roll, upptäcktsvägarna och gallerisökningen.
- planbrister() och kandidatbrister(): planens genomgångar och varje kandidats bidrag, med belägg i rätt paketversion.
- skaparunderlag(): kandidatens koncentrerade urval till UPPDRAG.md.
- oversikt(): arbetsytans vy av samma underlag.

Antalen i ARBETSREGEL är Nortropics arbetsregel för täckning, inget krav ur litteraturen och aldrig ett kvalitetsbetyg:
en genomgång som når antalen kan ändå vara svag, och bara bilderna, kritiken och ägaren bedömer kvaliteten.

    .venv/bin/python kontroller/referenskontrakt.py <slug>          (bristerna i nuvarande research och plan; slutkod 0/1)
"""
import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
VERSION = 1  # kontraktets version; en plan utan den är äldre än kontraktet och märks så (historiken skrivs aldrig om)
ARBETSREGEL = {
    'bransch_sajter': 3,        # fångade verkliga branschsajter med lyckad sida i paketet
    'inspiration_sajter': 2,    # fångade sajter ur gallerierna (roll hantverk, upptäckt i ett galleri)
    'webbsokningar': 1,         # lyckade webbsökningar med träffar i den här researchen
    'upptackta_bransch': 1,     # branschsajter vars värd finns i en loggad söknings eller hämtnings svar
    'plan_bransch': 3,          # rader i planens branschgenomgång
    'plan_forebilder': 2,       # visuella förebilder utanför branschen i planen
    'bidrag_per_kandidat': 2,   # minst ett ur branschen och ett ur den visuella inspirationen
}
GALLERIER = {'awwwards': 'awwwards.com', 'siteinspire': 'siteinspire.com', 'land-book': 'land-book.com', 'godly': 'godly.website',
             'fwa': 'thefwa.com', 'cssda': 'cssdesignawards.com', 'httpster': 'httpster.net', 'onepagelove': 'onepagelove.com'}
UPPTACKTSVAGAR = ('websok', 'galleri', 'byra', 'refero', 'mobbin', 'kund', 'kunskap')
UPPGIFTER = ('innehall', 'fortroende', 'navigation', 'kontakt', 'komposition', 'typografi', 'bildregi', 'rytm', 'mobil', 'interaktion', 'rorelse')
BIDRAGSROLLER = ('bransch', 'visuellt', 'ux', 'implementation')
BESLUT = ('infor', 'anpassar', 'undviker')
URL = re.compile(r'https?://[^\s"\'<>)\]}]+')
BILD = re.compile(r'\.(png|jpe?g|webp)$', re.I)
# en observation som bara är värdeord är ingen observation (ägarens exempel: "premium och modernt")
VARDEORD = re.compile(r'\b(premium|modern[at]?|clean|ren|elegant|snygg[at]?|stilren|fräsch|lyxig|exklusiv|professionell[at]?|minimalistisk[at]?|'
                      r'framgångsrik[at]?|ledande|branschledande|världsledande|bäst[ae]?|best|leading|successful)\b', re.I)
# omdömen, betyg och företagsstorlek är anseende och sammanhang (fråga B och C), aldrig designbelägg (fråga D)
ANSEENDEORD = re.compile(r'(\b\d[.,]\d\s*(av 5|/5|stjärn)|\bstjärn|\bomdöm|\brecension|\breview|\brating|\bbetyg|\bomsättning|\banställd|'
                         r'\bstort företag|\bmarknadsandel|\bmarknadsledande|\bförst i sök|\bsökträff|\brankning)', re.I)
FRAMGANGSORD = re.compile(r'(framgångsrik|tillväxt|lönsam|växer|marknadsledande|branschledande|ledande aktör|omsätter)', re.I)
FUNKTIONSUPPGIFTER = ('kontakt', 'navigation', 'interaktion', 'rorelse')  # kräver fångade funktionsbelägg, inte bara en bild
MIN_OBSERVATION = 40


def vard(url):
    try:
        h = (urllib.parse.urlsplit(str(url)).hostname or '').lower()
    except ValueError:
        return ''
    return h[4:] if h.startswith('www.') else h


def galleri_for(url_eller_text):
    t = str(url_eller_text or '').lower()
    return next((g for g, d in GALLERIER.items() if d in t), None)


# --- webbupptäckten ur transkriptet ---

def sokningar(fil):
    """Researchens WebSearch- och WebFetch-anrop ur ett transkript: [{'verktyg', 'fraga', 'url', 'fel', 'traffar'}]. Ett
    anrop utan svar står med fel 'inget svar'; ett nekat eller misslyckat anrop har fel och räknas aldrig som sökning."""
    import bildkedja
    h = bildkedja.handelser(fil) if fil else []
    svar = {x[1]: x for x in h if x[0] == 'svar'}
    ut = []
    for x in h:
        if x[0] != 'anrop' or x[2] not in ('WebSearch', 'WebFetch'):
            continue
        inp = x[3] or {}
        s = svar.get(x[1])
        text = (s[2] or '') if s else ''
        fel = ('inget svar' if s is None else (text[:200] or 'fel') if s[3] else None)
        traffar = [] if fel else list(dict.fromkeys(u.rstrip('.,;') for u in URL.findall(text)))[:60]
        ut.append({'verktyg': x[2], 'fraga': str(inp.get('query') or '')[:300] if x[2] == 'WebSearch' else None,
                   'url': str(inp.get('url') or '')[:500] if x[2] == 'WebFetch' else None, 'fel': fel, 'traffar': traffar})
    return ut


def sokta_vardar(logg):
    """Värdarna som en lyckad sökning eller hämtning faktiskt visade, och de hämtade adresserna själva."""
    v = set()
    for s in logg or []:
        if s.get('fel'):
            continue
        v.update(vard(u) for u in s.get('traffar') or [])
        if s.get('url'):
            v.add(vard(s['url']))
    return {x for x in v if x}


def verifiera_upptackt(sajt, logg):
    """Den observerade upptäcktsvägen för en föreslagen sajt: websok/galleri/byra bara när loggen visar dess värd (eller
    galleriobjektet) i en lyckad sökning eller hämtning; refero, mobbin och kund står som de anges (deras belägg finns
    i tjänsternas rapport och kundens underlag); annars kunskap, med den påstådda vägen kvar som påstående."""
    u = sajt.get('upptackt') if isinstance(sajt.get('upptackt'), dict) else {}
    vag, kalla = str(u.get('vag') or 'kunskap'), str(u.get('kalla') or '')
    sett = sokta_vardar(logg)
    if vag in ('websok', 'galleri', 'byra'):
        ok = vard(sajt.get('adress')) in sett or (vag == 'galleri' and any(kalla and kalla in (s.get('url') or '') for s in logg or [] if not s.get('fel')))
        if not ok:
            return {'vag': 'kunskap', 'kalla': kalla, 'pastadd': vag, 'not': 'den påstådda sökvägen syns inte i loggen'}
    elif vag not in UPPTACKTSVAGAR:
        vag = 'kunskap'
    return {'vag': vag, 'kalla': kalla}


# --- paketet ---

def senaste_paket(slug, underlag):
    import skapande
    return skapande.senaste_paket(slug, underlag)


def paket_rad(paket):
    """{namn: kandidatposten} ur PAKET.json, med 'sidor_ok' (lyckade sidor vars bilder i 390 och 1440 finns)."""
    if not paket:
        return {}
    try:
        d = json.loads((Path(paket) / 'PAKET.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    ut = {}
    for k in d.get('kandidater') or []:
        if not isinstance(k, dict) or not k.get('namn'):
            continue
        ok_sidor = []
        for s in k.get('sidor') or []:
            kat = Path(paket) / str((s or {}).get('katalog') or '')
            if (s or {}).get('ok') and kat.is_dir() and not kat.is_symlink() and \
                    all((kat / ('vy-%s-forsta.png' % b)).is_file() for b in ('390', '1440')):
                ok_sidor.append({'sida': s.get('sida'), 'katalog': str(kat), 'adress': s.get('adress')})
        ut[k['namn']] = dict(k, sidor_ok=ok_sidor)
    return ut


def belagg_ok(slug, underlag, paket, vag_):
    """Ett belägg är en bild som finns under kundens referenser; en paketbild måste ligga i planens paketversion."""
    try:
        s = str(vag_ or '').strip()
        p = Path(s)
        if not p.is_absolute():
            pre = 'underlag/%s/' % slug
            p = Path(underlag) / slug / s[len(pre):] if s.startswith(pre) else ROOT / s
        p = p.resolve()
        ref = (Path(underlag) / slug / 'referenser').resolve()
    except (OSError, ValueError):
        return 'ogiltig väg'
    if ref not in p.parents:
        return 'ligger utanför kundens referenser'
    if not p.is_file() or not BILD.search(p.name):
        return 'bilden finns inte'
    if '/paket-v' in str(p) and paket and Path(paket).resolve() not in p.parents:
        return 'pekar på en annan paketversion än planens (%s)' % Path(paket).name
    return None


def uppgiftstackning(post, uppgifter):
    """Fångstens fullständighet mot den deklarerade uppgiften: vad som finns och vad som är okänt (aldrig ett påstående om
    kvalitet). En stillbild bevisar ingen rörelse, och en tom getAnimations() bevisar inte att sidan saknar rörelse."""
    ut = {}
    sidor = [Path(s['katalog']) for s in (post or {}).get('sidor_ok') or []]
    for u in uppgifter or []:
        finns, saknas = [], []
        for kat in sidor:
            filer = {f.name for f in kat.iterdir()} if kat.is_dir() else set()
            if u in ('typografi', 'komposition', 'rytm', 'innehall', 'fortroende'):
                (finns if 'SEKTIONER.md' in filer else saknas).append('SEKTIONER.md')
            if u == 'mobil':
                (finns if 'vy-390-hela.png' in filer or any(f.startswith('vy-390-ruta-') for f in filer) else saknas).append('mobilens hela sida')
            if u in ('navigation', 'interaktion'):
                (finns if any(re.match(r'vy-\d+-(meny|hover|fokus)', f) for f in filer) else saknas).append('meny-, hover- eller fokusbild')
            if u == 'rorelse':
                (finns if any(f.endswith('-spar.zip') or '-sekvens-' in f for f in filer) else saknas).append('rörelsespår eller bildsekvens')
            if u == 'bildregi':
                (finns if any(f.endswith('-extrakt.json') for f in filer) else saknas).append('bildmätningen (extrakt)')
            if u == 'kontakt':
                (finns if any(f.endswith('-aria.txt') for f in filer) else saknas).append('tillgänglighetsträdet (formulär och knappar)')
        ut[u] = 'underlag finns' if finns and not saknas else 'delvis' if finns else 'okänt (underlaget saknas)'
    return ut


# --- researchen ---

def researchbrister(slug, underlag, post, paket=None):
    """Bristerna mot kontraktet i en research (FORSKNING.json) och dess paket; tom lista när det obligatoriska finns."""
    if not isinstance(post, dict):
        return ['researchen saknas']
    paket = paket if paket is not None else senaste_paket(slug, underlag)
    if not paket:
        return ['referenspaketet saknas: inga sajter är fångade i webbläsaren']
    rader = paket_rad(paket)
    logg = post.get('sok') or []
    fel = []
    def unika(xs):  # samma värd (med eller utan www, en annan sida) är en förebild, aldrig två oberoende
        sett_, ut_ = set(), []
        for k in xs:
            v_ = vard(k.get('adress'))
            if v_ and v_ not in sett_:
                sett_.add(v_)
                ut_.append(k)
        return ut_
    bransch = unika([k for k in rader.values() if k.get('roll') == 'bransch' and k['sidor_ok']])
    insp = unika([k for k in rader.values() if k.get('roll') == 'hantverk' and k['sidor_ok'] and str((k.get('upptackt') or {}).get('vag')) == 'galleri'])
    if len(bransch) < ARBETSREGEL['bransch_sajter']:
        fel.append('branschgenomgången har %d fångade branschsajter med lyckad sida i 390 och 1440 (arbetsregeln: minst %d)' % (
            len(bransch), ARBETSREGEL['bransch_sajter']))
    if len(insp) < ARBETSREGEL['inspiration_sajter']:
        fel.append('inspirationsgenomgången har %d fångade sajter ur gallerierna (arbetsregeln: minst %d)' % (len(insp), ARBETSREGEL['inspiration_sajter']))
    lyckade = [s for s in logg if s.get('verktyg') == 'WebSearch' and not s.get('fel') and s.get('traffar')]
    if len(lyckade) < ARBETSREGEL['webbsokningar']:
        fel.append('ingen lyckad webbsökning med träffar i den här researchen (bara sökträffar eller minnet räcker inte)')
    if not any(galleri_for(s.get('fraga') or s.get('url')) == 'awwwards' for s in logg):
        fel.append('Awwwards ingick inte i referensjakten i den här designomgången (ingen sökning eller hämtning mot awwwards.com)')
    elif not any(galleri_for(s.get('fraga') or s.get('url')) and not s.get('fel') for s in logg):
        fel.append('ingen gallerisökning lyckades (Awwwards och alternativen var otillgängliga); den visuella inspirationen saknas')
    uf = post.get('urvalsfragor') if isinstance(post.get('urvalsfragor'), dict) else {}
    if not all(isinstance(uf.get(k), list) and any(str(x).strip() for x in uf[k]) for k in ('fragor', 'kundbehov', 'material', 'kvaliteter')):
        fel.append('urvalsfrågorna före sökningen saknas (frågorna, kundbehoven, materialförutsättningarna och kvaliteterna)')
    tk = post.get('tackning') if isinstance(post.get('tackning'), dict) else {}
    if not _text_ok(tk.get('varfor_racker'), 25):
        fel.append('täckningen efter sökningen saknas (varför underlaget räcker och vilka luckor som återstår)')
    sett = sokta_vardar(logg)
    upptackta = [k for k in bransch if vard(k.get('adress')) in sett]
    if len(upptackta) < ARBETSREGEL['upptackta_bransch']:
        fel.append('ingen av de fångade branschsajterna syns i en loggad sökning eller hämtning (adresser ur minnet är kandidater, inga upptäckter)')
    return fel


# --- planen ---

def _text_ok(t, n=MIN_OBSERVATION):
    t = str(t or '').strip()
    if len(t) < n:
        return False
    utan = VARDEORD.sub('', t)
    return len(re.sub(r'[\s,.;:och]+', '', utan)) >= n // 2


def planbrister(slug, underlag, plan, paket=None):
    """Planens genomgångar: branschgenomgången och förebilderna, med sajter ur paketet och belägg i rätt version."""
    if not isinstance(plan, dict):
        return ['planen saknas']
    paket = paket if paket is not None else (Path(underlag) / slug / 'referenser' / plan['paket'] if plan.get('paket') else senaste_paket(slug, underlag))
    if not paket or not Path(paket).is_dir():
        return ['planens referenspaket %s finns inte' % (plan.get('paket') or '(okänt)')]
    rader = paket_rad(paket)
    fel = []
    br = [b for b in plan.get('bransch') or [] if isinstance(b, dict)]
    giltiga_br, sedda_vardar = [], set()
    for b in br:
        post = rader.get(str(b.get('sajt') or ''))
        brist = ('sajten %s finns inte i paketet %s' % (b.get('sajt'), Path(paket).name) if not post else
                 'sajten %s är inte en branschsajt i paketet' % b.get('sajt') if post.get('roll') != 'bransch' else
                 'sajten %s saknar lyckad fångst' % b.get('sajt') if not post['sidor_ok'] else None)
        bel = [x for x in b.get('belagg') or [] if isinstance(x, str)]
        bel_fel = [('%s: %s' % (x, belagg_ok(slug, underlag, paket, x))) for x in bel if belagg_ok(slug, underlag, paket, x)]
        if not brist and not bel:
            brist = 'branschraden för %s har inga belägg' % b.get('sajt')
        if not brist and bel_fel:
            brist = 'branschraden för %s har trasiga belägg (%s)' % (b.get('sajt'), '; '.join(bel_fel[:2]))
        if not brist and not all(_text_ok(b.get(f), 25) for f in ('erbjudande', 'navigation_kontakt', 'mobil', 'styrkor', 'svagheter', 'mojligheter')):
            brist = 'branschraden för %s saknar konkreta bedömningar (erbjudande, navigation och kontakt, mobil, styrkor, svagheter, möjligheter)' % b.get('sajt')
        brist = brist or designgrundbrist(b, post)
        if not brist and vard((post or {}).get('adress')) in sedda_vardar:
            brist = 'branschraden för %s upprepar en sajt som redan står med (samma värd är en förebild)' % b.get('sajt')
        if not brist:
            sedda_vardar.add(vard(post.get('adress')))
        (fel.append(brist) if brist else giltiga_br.append(b))
    if len(giltiga_br) < ARBETSREGEL['plan_bransch']:
        fel.append('branschgenomgången har %d giltiga rader (arbetsregeln: minst %d, var och en med en fångad branschsajt och belägg)' % (
            len(giltiga_br), ARBETSREGEL['plan_bransch']))
    fb = [b for b in plan.get('forebilder_utanfor') or [] if isinstance(b, dict)]
    giltiga_fb = []
    for b in fb:
        post = rader.get(str(b.get('sajt') or ''))
        bel = [x for x in b.get('belagg') or [] if isinstance(x, str)]
        brist = ('förebilden %s finns inte i paketet' % b.get('sajt') if not post else
                 'förebilden %s saknar lyckad fångst' % b.get('sajt') if not post['sidor_ok'] else
                 'förebilden %s har inga belägg' % b.get('sajt') if not bel else
                 'förebilden %s har trasiga belägg' % b.get('sajt') if any(belagg_ok(slug, underlag, paket, x) for x in bel) else
                 'förebilden %s saknar en konkret observerad kvalitet' % b.get('sajt') if not _text_ok(b.get('kvalitet')) else
                 'förebilden %s saknar ett konkret "stark webbplatsreferens för …"' % b.get('sajt') if not _text_ok(b.get('stark_for'), 15) else
                 'förebilden %s bygger designbedömningen på omdömen, betyg, storlek eller sökplacering' % b.get('sajt')
                 if ANSEENDEORD.search(' '.join(str(b.get(f) or '') for f in ('kvalitet', 'stark_for', 'tar_med'))) else None)
        (fel.append(brist) if brist else giltiga_fb.append(b))
    if len(giltiga_fb) < ARBETSREGEL['plan_forebilder']:
        fel.append('inspirationsgenomgången i planen har %d giltiga förebilder (arbetsregeln: minst %d, fångade och med belägg)' % (
            len(giltiga_fb), ARBETSREGEL['plan_forebilder']))
    return fel


def designgrundbrist(b, post):
    """En branschrad som designförebild vilar på fråga D (det granskningen visar), aldrig på A–C: evidensen är egen
    observation, designfälten åberopar inte omdömen, betyg, storlek eller sökplacering, en påstådd affärsframgång har en
    källa (annars "okänt"), och stark_for är en konkret kvalitet eller uppgift, inte värdeord."""
    namn = b.get('sajt')
    if b.get('evidens') != 'egen_observation':
        return 'branschraden för %s vilar på %s, inte på egen observation i webbläsaren; omdömen, sökplacering och utmärkelser är ingen designgrund' % (
            namn, b.get('evidens') or 'okänd evidens')
    design = ' '.join(str(b.get(f) or '') for f in ('stark_for', 'erbjudande', 'tjanster_priser', 'navigation_kontakt', 'bilder_identitet', 'mobil',
                                                   'styrkor', 'tar_med', 'observation'))
    if ANSEENDEORD.search(design):
        return 'branschraden för %s använder omdömen, betyg, storlek eller sökplacering som designbelägg (de hör till anseendet, fråga B)' % namn
    af = str(b.get('affarsframgang') or '').strip()
    if FRAMGANGSORD.search(af) and not re.search(r'https?://|källa|enligt ', af, re.I):
        return 'branschraden för %s påstår affärsframgång utan belägg; skriv "okänt"' % namn
    if not _text_ok(b.get('stark_for'), 15):
        return 'branschraden för %s saknar ett konkret "stark webbplatsreferens för …" (värdeord som premium eller modern räcker inte)' % namn
    return None


def kandidatbrister(slug, underlag, k, paket):
    """Kandidatens kedja kundbehov → observerad kvalitet → designbeslut → tillämpning → bedömning, med belägg i planens
    paket. Egen design kringgår inget: också en egen huvudreferens behöver bidragen."""
    if not isinstance(k, dict):
        return ['uppdraget saknas']
    rader = paket_rad(paket)
    bid = [b for b in k.get('referensbidrag') or [] if isinstance(b, dict)]
    fel, roller = [], set()
    for i, b in enumerate(bid, 1):
        namn = str(b.get('kalla') or '')
        bel = [x for x in b.get('belagg') or [] if isinstance(x, str)]
        if b.get('roll') not in BIDRAGSROLLER or b.get('beslut') not in BESLUT:
            fel.append('bidrag %d: roll eller beslut saknas' % i)
            continue
        if b['roll'] in ('bransch', 'visuellt') and namn not in rader:
            fel.append('bidrag %d: källan %s finns inte i paketet %s' % (i, namn, Path(paket).name if paket else '?'))
            continue
        if not bel or any(belagg_ok(slug, underlag, paket, x) for x in bel):
            fel.append('bidrag %d (%s): beläggen saknas eller pekar fel (%s)' % (i, namn, '; '.join('%s: %s' % (x, belagg_ok(slug, underlag, paket, x))
                                                                                           for x in bel if belagg_ok(slug, underlag, paket, x))[:200] or 'inga'))
            continue
        if not all(_text_ok(b.get(f), n) for f, n in (('kundbehov', 20), ('observerad_kvalitet', MIN_OBSERVATION), ('designbeslut', 25),
                                                        ('tillampning', 25), ('bedomning', 20))):
            fel.append('bidrag %d (%s): kedjan är inte konkret (kundbehov, observerad kvalitet, designbeslut, tillämpning och bedömning)' % (i, namn))
            continue
        if ANSEENDEORD.search(str(b.get('observerad_kvalitet') or '')):
            fel.append('bidrag %d (%s): den observerade kvaliteten åberopar omdömen, betyg, storlek eller sökplacering' % (i, namn))
            continue
        if b.get('uppgift') in FUNKTIONSUPPGIFTER and b['roll'] in ('bransch', 'visuellt'):
            tack = uppgiftstackning(rader.get(namn) or {}, [b['uppgift']])
            if tack.get(b['uppgift'], '').startswith('okänt'):
                fel.append('bidrag %d (%s): funktionsuppgiften %s saknar fångade funktionsbelägg (meny, tillstånd, formulär eller rörelse); '
                           'ett företagsbetyg ersätter dem inte' % (i, namn, b['uppgift']))
                continue
        roller.add('bransch' if b['roll'] == 'bransch' else 'visuellt' if b['roll'] == 'visuellt' else b['roll'])
    if len(bid) < ARBETSREGEL['bidrag_per_kandidat'] or not {'bransch', 'visuellt'} <= roller:
        fel.append('uppdraget saknar spårbara bidrag från både branschresearchen och den visuella inspirationen (har: %s)' % (
            ', '.join(sorted(roller)) or 'inga giltiga'))
    return fel


def kandidatpaket(slug, underlag, plan):
    p = Path(underlag) / slug / 'referenser' / str((plan or {}).get('paket') or '')
    return p if (plan or {}).get('paket') and p.is_dir() else None


def startbrister(slug, underlag, plan, kid):
    """Allt som stoppar en beroende skaparsession för kandidaten: planens kontraktsversion, genomgångarna, kandidatens
    bidrag och att UPPDRAG.md bär underlaget ur samma plan. En plan som är äldre än kontraktet märks som det."""
    if not isinstance(plan, dict) or not plan.get('kandidater'):
        return ['kandidatplanen saknas']
    if (plan.get('referenskontrakt') or {}).get('version') != VERSION:
        return ['kandidatplanen är äldre än referenskontraktet (version %d) och har ingen prövad branschgenomgång, inspiration eller '
                'kedja per kandidat; den står kvar som historik, och en ny designomgång (research och plan) krävs' % VERSION]
    paket = kandidatpaket(slug, underlag, plan)
    if not paket:
        return ['planens referenspaket %s finns inte längre' % plan.get('paket')]
    fel = planbrister(slug, underlag, plan, paket)
    k = (plan.get('kandidater') or {}).get(kid)
    fel += ['%s: %s' % (kid, x) for x in kandidatbrister(slug, underlag, k, paket)]
    upp = Path(underlag) / slug / 'atelje' / 'kandidater' / kid / 'UPPDRAG.md'
    try:
        text = upp.read_text(encoding='utf-8')
    except OSError:
        text = ''
    if MARKOR not in text or ('<!-- referensunderlag %s -->' % kedjans_sha(k)) not in text:
        fel.append('%s: UPPDRAG.md bär inte referensunderlaget ur den nuvarande planen' % kid)
    return fel


MARKOR = '## Referensunderlaget för uppdraget'


def kedjans_sha(k):
    import hashlib
    return hashlib.sha256(json.dumps([(k or {}).get('referensbidrag'), (k or {}).get('titel')], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(p)


def skaparunderlag(slug, underlag, plan, kid):
    """Raderna i UPPDRAG.md: kandidatens bidrag med bilderna och observationerna, de branschrader och förebilder som
    bidragen bygger på, fångstens täckning mot uppgiften och vägen till fördjupningen. Ger (rader, bilder)."""
    k = (plan.get('kandidater') or {}).get(kid) or {}
    paket = kandidatpaket(slug, underlag, plan)
    rader_p = paket_rad(paket)
    bilder = []
    ut = [MARKOR, '', '<!-- referensunderlag %s -->' % kedjans_sha(k),
          'Ditt urval ur det gemensamma referensarbetet (paketet %s; hela underlaget står i %s och paketets PAKET.md). Öppna' % (
              Path(paket).name if paket else '?', _rel(Path(underlag) / slug / 'atelje' / 'KANDIDATPLAN.md')),
          'varje bild med Read: en sökväg är inte bildens innehåll. Jämför referensens utpekade kvaliteter med din rendering i',
          'samma bredder och tillstånd i varje varv. Försvagar kundanpassningen proportioner och hierarki, bildregi och material,',
          'rytm och innehåll, mobilens komposition eller interaktionen: rätta, eller gör ett motiverat omtag av grundkompositionen',
          '(små marginaljusteringar är inget svar när helheten inte bär). Bidragen är underlag, inte en mall: du får välja,',
          'kombinera och anpassa med skäl i RIKTNING.md.', '']
    for i, b in enumerate(k.get('referensbidrag') or [], 1):
        post = rader_p.get(str(b.get('kalla') or '')) or {}
        bel = [x for x in b.get('belagg') or [] if isinstance(x, str)]
        bilder += bel
        tack = uppgiftstackning(post, [b.get('uppgift')] if b.get('uppgift') else post.get('uppgift') or [])
        ut += ['### Bidrag %d · %s · %s (%s)' % (i, b.get('roll'), b.get('kalla'), post.get('adress') or 'adress ur paketet saknas'),
               '- Kundbehov: %s' % str(b.get('kundbehov') or '').strip(),
               '- Observerad kvalitet%s: %s' % (' (mätt i DOM/CSS)' if b.get('matbart') else ' (visuell tolkning)', str(b.get('observerad_kvalitet') or '').strip()),
               '- Designbeslut (%s): %s' % ({'infor': 'vi inför', 'anpassar': 'vi anpassar', 'undviker': 'vi undviker medvetet'}.get(b.get('beslut'), '?'),
                                           str(b.get('designbeslut') or '').strip()),
               '- Planerad tillämpning: %s' % str(b.get('tillampning') or '').strip(),
               '- Så bedöms resultatet: %s' % str(b.get('bedomning') or '').strip(),
               '- Belägg, öppna varje bild med Read:', *['- %s' % x for x in bel],
               *(['- Sektionsunderlag: ' + ', '.join(sorted({_rel(Path(s['katalog']) / 'SEKTIONER.md') for s in post.get('sidor_ok') or []
                                                              if (Path(s['katalog']) / 'SEKTIONER.md').is_file()}))] if post.get('sidor_ok') else []),
               *(['- Fångstens täckning mot uppgiften: ' + '; '.join('%s: %s' % x for x in tack.items())] if tack else []),
               *(['- Upptäckt: %s %s' % ((post.get('upptackt') or {}).get('vag'), (post.get('upptackt') or {}).get('kalla') or '')] if post.get('upptackt') else []),
               '']
    kallor = {str(b.get('kalla')) for b in k.get('referensbidrag') or []}
    br = [b for b in plan.get('bransch') or [] if isinstance(b, dict) and str(b.get('sajt')) in kallor]
    if br:
        ut += ['### Branschgenomgången för dina källor', '']
        for b in br:
            ut += ['- **%s**: erbjudande och hierarki: %s; navigation och kontakt: %s; mobil: %s; styrkor: %s; svagheter: %s; möjlighet för kunden: %s' % (
                b.get('sajt'), b.get('erbjudande'), b.get('navigation_kontakt'), b.get('mobil'), b.get('styrkor'), b.get('svagheter'), b.get('mojligheter'))]
        ut.append('')
    fb = [b for b in plan.get('forebilder_utanfor') or [] if isinstance(b, dict) and str(b.get('sajt')) in kallor]
    if fb:
        ut += ['### Inspirationen för dina källor', ''] + ['- **%s**: %s; kundens material: %s' % (b.get('sajt'), b.get('kvalitet'), b.get('kundens_material'))
                                                         for b in fb] + ['']
    return ut, list(dict.fromkeys(bilder))


# --- överföringen till skaparen ---

def overforing(slug, underlag, plan, kid, sessioner, riktning=''):
    """Per bidrag, var för sig (ägarens uppdrag 2026-10-10 om referenskedjan, punkt 7): insamlat (beläggen finns i
    paketet), tillgängligt för sessionen (UPPDRAG.md bär dem), öppnat (en lyckad Read av bilden i en skaparsession: bilden
    levererades, en sökväg i texten räcker inte), tillämpat enligt skaparens redovisning (källan nämns i RIKTNING.md) och
    jämfört i ett varv (bilden lästes i samma session som varvens egna bilder). Att tillämpningen stöds av implementationen
    kräver bildbedömning och står alltid som ej bedömd här; ett läskvitto bevisar varken förståelse eller kvalitet."""
    import bildkedja
    k = (plan.get('kandidater') or {}).get(kid) or {}
    paket = kandidatpaket(slug, underlag, plan)
    upp = Path(underlag) / slug / 'atelje' / 'kandidater' / kid / 'UPPDRAG.md'
    try:
        upp_text = upp.read_text(encoding='utf-8')
    except OSError:
        upp_text = ''
    lasta, varvlasta = set(), set()
    for sid in sessioner or []:
        t = bildkedja.transkript(sid) if sid else None
        if not t:
            continue
        sett = {bildkedja.utan_punkt(bildkedja.relativ(x)) for x in bildkedja.lasta(t)}
        lasta |= sett
        if any('/varv/' in x or '/forhand/' in x for x in sett):  # sessionen tittade också på sina egna varv
            varvlasta |= sett
    ut = []
    for b in k.get('referensbidrag') or []:
        bel = [x for x in b.get('belagg') or [] if isinstance(x, str)]
        rel_ = [bildkedja.utan_punkt(bildkedja.relativ(x)) for x in bel]
        ut.append({'kalla': b.get('kalla'), 'roll': b.get('roll'),
                   'insamlat': bool(bel) and not any(belagg_ok(slug, underlag, paket, x) for x in bel),
                   'tillgangligt': bool(bel) and all(x in upp_text for x in bel),
                   'oppnat': any(x in lasta for x in rel_) if sessioner else None,
                   'redovisat': bool(b.get('kalla')) and str(b.get('kalla')) in (riktning or ''),
                   'jamfort_i_varv': any(x in varvlasta for x in rel_) if sessioner else None,
                   'stods_av_implementation': 'ej bedömd (kräver bildbedömning)'})
    return ut


# --- arbetsytan ---

def oversikt(slug, underlag, med_kandidater=False):
    """Vad som hittades → undersöktes → valdes → överfördes, för arbetsytans Förslagen. med_kandidater: vilka kandidater
    som bygger på vilka källor (visas efter ägarens första val, som skaparnas övriga förklaringar)."""
    r = Path(underlag) / slug / 'atelje'
    try:
        fo = json.loads((r / 'FORSKNING.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        fo = {}
    try:
        plan = json.loads((r / 'KANDIDATPLAN.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        plan = {}
    paket = kandidatpaket(slug, underlag, plan) or senaste_paket(slug, underlag)
    rader = paket_rad(paket)
    logg = fo.get('sok') or []
    ut = {'paket': Path(paket).name if paket else None, 'kontrakt': (plan.get('referenskontrakt') or {}).get('version'),
          'sokningar': [{'verktyg': s.get('verktyg'), 'fraga': s.get('fraga') or s.get('url'), 'utfall': 'fel: %s' % s['fel'][:80] if s.get('fel') else
                         '%d adresser' % len(s.get('traffar') or [])} for s in logg][:40],
          'galleri': (fo.get('galleri') or {}).get('objekt') or [],
          'sallning': fo.get('sallning') or [],
          'urvalsfragor': fo.get('urvalsfragor') or {}, 'tackning': fo.get('tackning') or {},
          'undersokta': [{'namn': n, 'adress': p.get('adress'), 'roll': p.get('roll'), 'upptackt': p.get('upptackt'), 'uppgift': p.get('uppgift'),
                          'fangad': bool(p.get('sidor_ok')), 'sidor': len(p.get('sidor_ok') or []), 'ateranvand': p.get('arv'),
                          'tid': p.get('tid'), 'bredder': p.get('bredder')} for n, p in sorted(rader.items())],
          'bransch': [{'sajt': b.get('sajt'), 'stark_for': b.get('stark_for'), 'lokal_marknad': b.get('lokal_marknad'), 'anseende': b.get('anseende'),
                       'affarsframgang': b.get('affarsframgang'), 'styrkor': b.get('styrkor'), 'svagheter': b.get('svagheter'), 'tar_med': b.get('tar_med'),
                       'undviker': b.get('undviker'), 'observation': b.get('observation'), 'tolkning': b.get('tolkning'), 'belagg': b.get('belagg')}
                      for b in plan.get('bransch') or [] if isinstance(b, dict)],
          'forebilder': [{'sajt': b.get('sajt'), 'stark_for': b.get('stark_for'), 'kvalitet': b.get('kvalitet'), 'tar_med': b.get('tar_med'),
                          'undviker': b.get('undviker'), 'belagg': b.get('belagg')} for b in plan.get('forebilder_utanfor') or [] if isinstance(b, dict)],
          'brister': (fo.get('referenskontrakt') or {}).get('brister') or [],
          'planbrister': (plan.get('referenskontrakt') or {}).get('brister') or []}
    if med_kandidater:
        ut['kandidater'] = {kid: [{'kalla': b.get('kalla'), 'roll': b.get('roll'), 'beslut': b.get('beslut')} for b in k.get('referensbidrag') or []]
                            for kid, k in (plan.get('kandidater') or {}).items()}
        ut['overforing'] = {}
        for kid in plan.get('kandidater') or {}:
            try:
                st = json.loads((r / 'kandidater' / kid / 'STATUS.json').read_text(encoding='utf-8'))
            except (OSError, ValueError):
                st = {}
            if st.get('referensoverforing'):
                ut['overforing'][kid] = st['referensoverforing']
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('slug')
    a = p.parse_args(argv)
    import atelje
    u = atelje.UNDERLAG
    r = u / a.slug / 'atelje'
    try:
        fo = json.loads((r / 'FORSKNING.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        fo = None
    try:
        plan = json.loads((r / 'KANDIDATPLAN.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        plan = None
    fel = researchbrister(a.slug, u, fo)
    if plan:
        for kid in plan.get('kandidater') or {}:
            fel += startbrister(a.slug, u, plan, kid)
    for f in dict.fromkeys(fel):
        print('- ' + f)
    print('referensunderlaget uppfyller kontraktet' if not fel else '%d brister' % len(set(fel)))
    return 0 if not fel else 1


if __name__ == '__main__':
    sys.exit(main())
