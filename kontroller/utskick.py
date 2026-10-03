#!/usr/bin/env python3
"""utskick.py — grinden och sändningen för brev till prospekt. Ett brev går i väg bara när ägaren godkänt exakt den
texten i dashboarden och mottagaren är en juridisk person utan spärr; en enskild firma får aldrig e-post
(marknadsföringslagen 19 §). Reglerna: kunskap/prospekt-och-utskick.md. Sändning via Resend från nortropic.se.

    .venv/bin/python kontroller/utskick.py skicka <slug> --kampanj <k> [--torr]
    .venv/bin/python kontroller/utskick.py prov [--till adress]            # testbrev till dig själv
    .venv/bin/python kontroller/utskick.py sparr <epost> [--skal "…"]       # spegla en spärr till Resend
    .venv/bin/python kontroller/utskick.py sparr --lista                    # Resends manuella spärrar

Exit: 0 skickat eller klart · 2 fel i anropet · 3 grinden nekade eller sändningen föll (ingen UTSKICK.json skrivs) ·
4 hemligheterna saknas eller har fel rättigheter.
Godkännandet (BREV.json godkand) binder ämne och text (text_sha), mottagaradressen, verksamhetens slug och om en namngiven
adress bekräftats; ändras något av det krävs nytt godkännande. En oläsbar spärrlista nekar, den räknas aldrig som tom.
Miljö: NWP_UTSKICK=torr skriver UTSKICK.json med resend_id "torr" utan HTTP (gör bara säkrare; öppnar aldrig grinden);
NWP_UTSKICK_HEMLIGHETER pekar på en annan hemlighetsfil än ~/.nortropic-hemligheter/webb-pro/resend.env.
Hemlighetsfilen (0600): RESEND_API_NYCKEL=…, AVSANDARE=Namn <adress@nortropic.se>, SVAR_TILL=…, FORETAG=…, TELEFON=…
"""
import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prospektfiler as pf  # noqa: E402

ROOT = pf.ROOT
HEMLIGHETER = Path(os.environ.get('NWP_UTSKICK_HEMLIGHETER') or (Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'resend.env'))
SPARR = pf.PROSPEKT / 'SPARR.json'
RESEND = 'https://api.resend.com'
# Juridiska former som får e-post: SCB:s koder med den klartext som ska stå i kodtabellen (okänd kod nekar).
JURIDISKA = {'31': r'handelsbolag|kommanditbolag', '41': r'bankaktiebolag', '42': r'försäkringsaktiebolag',
             '49': r'aktiebolag', '51': r'ekonomisk förening', '53': r'bostadsrättsförening'}
ROLLER = {'info', 'kontakt', 'hej', 'hello', 'mail', 'post', 'office', 'kansli', 'bokning', 'admin', 'reception', 'support',
          'kundtjanst', 'kundtjänst', 'kontor', 'order', 'forsaljning', 'sales', 'faktura', 'ekonomi', 'webb', 'web'}
EPOST = re.compile(r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$')


class Nekad(Exception):
    pass


def las_hemligheter(fil=None):
    fil = Path(fil or HEMLIGHETER)
    try:
        st = fil.stat()
    except OSError:
        raise Nekad('hemligheterna saknas: skapa %s (chmod 600) med RESEND_API_NYCKEL, AVSANDARE, SVAR_TILL, FORETAG, TELEFON' % fil)
    if stat.S_IMODE(st.st_mode) & 0o077:
        raise Nekad('%s får bara läsas av dig: chmod 600' % fil)
    h = {}
    for rad in fil.read_text(encoding='utf-8').splitlines():
        if '=' in rad and not rad.lstrip().startswith('#'):
            k, v = rad.split('=', 1)
            h[k.strip()] = v.strip().strip('"\'')
    for k in ('RESEND_API_NYCKEL', 'AVSANDARE', 'SVAR_TILL'):
        if not h.get(k):
            raise Nekad('%s saknar %s' % (fil, k))
    return h


def hemligheter_finns(fil=None):
    try:
        las_hemligheter(fil)
        return True
    except Nekad:
        return False


def gallande_text(brev):
    r = (brev or {}).get('redigerat') or {}
    u = (brev or {}).get('utkast') or {}
    return (r.get('amne') if r.get('text') else None) or u.get('amne') or '', r.get('text') or u.get('text') or ''


def rolladress(epost):
    lokal = (epost or '').split('@', 1)[0].lower()
    return lokal in ROLLER or lokal.startswith(('info', 'kontakt', 'kontor'))


def i_sparrlista(sparr, epost, post):
    """Posten i spärrlistan som träffar adressen, domänen eller organisationsnumret, annars None."""
    e = (epost or '').strip().lower()
    dom = e.rsplit('@', 1)[1] if '@' in e else ''
    sajtdom = ''
    url = ((post or {}).get('sajt') or {}).get('url') or ''
    m = re.match(r'https?://([^/]+)', url)
    if m:
        sajtdom = m.group(1).lower().removeprefix('www.')
    orgnr = {re.sub(r'\D', '', str((post or {}).get(k) or '')) for k in ('orgNr', 'peOrgNr')} - {''}
    for s in sparr or []:
        typ, v = s.get('typ'), str(s.get('varde') or '').strip().lower()
        if not v:
            continue
        if typ in ('e-post', 'epost') and v == e:
            return s
        if typ in ('doman', 'domän') and v.removeprefix('www.') in (dom, sajtdom) and v:
            return s
        if typ == 'orgnr' and re.sub(r'\D', '', v) in orgnr:
            return s
    return None


def jurform_tillaten(post):
    kod = str((post or {}).get('jurform') or '')
    text = (post or {}).get('jurform_text') or ''
    return kod in JURIDISKA and bool(re.search(JURIDISKA[kod], text, re.I))


def far_skickas(post, brev, sparr, utskick_finns, hemligheter_finns):
    """(ok, skäl). Första nej vinner. Ren funktion utan nätåtkomst; ingen miljövariabel ändrar utfallet."""
    post, brev = post or {}, brev or {}
    if post.get('status') != 'utkast':
        return False, 'status är %s, inte utkast' % (post.get('status') or 'okänd')
    if sparr is None:  # oläsbar lista är inte en tom lista (revisionen 2026-10-03, F6)
        return False, 'spärrlistan (underlag/prospekt/SPARR.json) gick inte att läsa; inget skickas förrän den är hel'
    g = brev.get('godkand') or {}
    if not g.get('text_sha'):
        return False, 'brevet är inte godkänt'
    amne, text = gallande_text(brev)
    if pf.text_sha(amne, text) != g['text_sha']:
        return False, 'texten är ändrad efter godkännandet; godkänn igen'
    if not text.strip() or not amne.strip():
        return False, 'ämne eller text saknas'
    if post.get('fysisk_person'):
        return False, 'fysisk person (enskild firma): ring eller skriv brev, aldrig e-post (MFL 19 §)'
    if not jurform_tillaten(post):
        return False, 'juridisk form %s (%s) är inte i listan över former som får e-post' % (post.get('jurform') or '?', post.get('jurform_text') or 'okänd')
    sp = post.get('sparr') or {}
    if sp.get('reklam', True):
        return False, 'reklamspärr i SCB:s register'
    if sp.get('epost', True):
        return False, 'e-postspärr i SCB:s register'
    m = brev.get('mottagare') or {}
    epost = (m.get('epost') or '').strip()
    if not EPOST.match(epost):
        return False, 'ingen giltig mottagaradress'
    # godkännandet gäller mottagaren och verksamheten också, inte bara texten (revisionen 2026-10-03, F7)
    if g.get('mottagare') != epost.lower() or g.get('slug') != post.get('slug') or bool(g.get('bekraftad_person')) != bool(m.get('bekraftad_person')):
        return False, 'godkännandet gäller en annan mottagare eller verksamhet; godkänn brevet igen'
    tr = i_sparrlista(sparr, epost, post)
    if tr:
        return False, 'spärrad (%s %s): %s' % (tr.get('typ'), tr.get('varde'), tr.get('skal') or 'utan skäl')
    if not rolladress(epost) and not m.get('bekraftad_person'):
        return False, 'namngiven adress: kryssa i att du bedömer att adressen är verksamhetens'
    if utskick_finns:
        return False, 'redan skickat till den här verksamheten'
    if not hemligheter_finns:
        return False, 'Resend-nyckeln saknas (~/.nortropic-hemligheter/webb-pro/resend.env)'
    return True, 'ok'


def sidfot(h, post):
    """Fast sidfot: avsändare, svar, avregistrering och informationen enligt artikel 13 och 14. Enda källan till den texten."""
    namn = re.sub(r'\s*<.*', '', h.get('AVSANDARE') or '').strip() or 'Nortropic'
    foretag = h.get('FORETAG') or 'Nortropic'
    tel = h.get('TELEFON')
    rader = ['—', '%s, Nortropic, Luleå. Svara på det här mejlet%s.' % (namn, (' eller ring %s' % tel) if tel else ''),
             'Vill ni inte ha fler mejl från oss: svara ”avregistrera”, så stryks adressen samma dag.',
             'Varför ni får det här: %s finns i SCB:s företagsregister som %s i %s; uppgifterna ovan kommer därifrån och från er egen '
             'webbplats. Vi behandlar företagets kontaktuppgifter med stöd av berättigat intresse (dataskyddsförordningen artikel 6.1 f) '
             'för att erbjuda webbtjänster till lokala företag och gallrar dem senast tolv månader efter det här mejlet om vi inte '
             'blivit kunder med varandra. Ni kan invända mot behandlingen (svara ”avregistrera”) och klaga hos '
             'Integritetsskyddsmyndigheten. Personuppgiftsansvarig: %s, %s.' % (
                 (post or {}).get('namn') or 'verksamheten', (post or {}).get('jurform_text') or 'juridisk person',
                 (post or {}).get('postort') or 'kommunen', foretag, h.get('SVAR_TILL'))]
    return '\n'.join(rader)


def las_sparr():
    """Spärrlistan; [] när filen inte finns än, None när den finns men inte är en läsbar lista (då nekar grinden)."""
    if not SPARR.is_file():
        return []
    d = pf.las_json(SPARR)
    return d if isinstance(d, list) else None


def skriv_sparr(poster):
    pf.skriv_json(SPARR, poster)


def resend_anrop(h, vag, data=None, metod='POST', idempotens=None):
    import requests
    huvud = {'Authorization': 'Bearer ' + h['RESEND_API_NYCKEL'], 'Content-Type': 'application/json'}
    if idempotens:
        huvud['Idempotency-Key'] = idempotens
    r = requests.request(metod, RESEND + vag, headers=huvud, json=data, timeout=20)
    try:
        kropp = r.json()
    except ValueError:
        kropp = {'text': r.text[:300]}
    return r.status_code, kropp


def sparr_lagg(epost, skal, kalla='manuell', typ='e-post', spegla=True, post=None):
    """Lägg till i SPARR.json (sanningen) och spegla e-postadresser till Resend. Returnerar posten."""
    poster = las_sparr()
    if poster is None:
        raise Nekad('SPARR.json går inte att läsa; rätta filen innan en spärr läggs till, så att ingen spärr skrivs över')
    ny = {'typ': typ, 'varde': (epost or '').strip().lower(), 'skal': skal or '', 'tid': pf.nu(), 'kalla': kalla}
    if post:
        ny['slug'] = post.get('slug')
    if spegla and typ in ('e-post', 'epost') and ny['varde']:
        try:
            h = las_hemligheter()
            kod, kropp = resend_anrop(h, '/suppressions', {'email': ny['varde']}, idempotens='nwp-sparr-' + re.sub(r'[^a-z0-9]', '-', ny['varde']))
            if 200 <= kod < 300:
                ny['resend_id'] = kropp.get('id')
            else:
                ny['resend_fel'] = '%s %s' % (kod, kropp)
        except Exception as e:
            ny['resend_fel'] = str(e)[:200]
    poster = [p for p in poster if not (p.get('typ') == ny['typ'] and p.get('varde') == ny['varde'])] + [ny]
    skriv_sparr(poster)
    return ny


def skicka(slug, kampanj, torr=False):
    """Grinden, sedan ett brev via Resend. Skriver UTSKICK.json bara när sändningen lyckades (eller vid torrkörning)."""
    poster = pf.las_register(kampanj)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise Nekad('ingen post med slug %s i %s' % (slug, kampanj))
    bas = ROOT / 'underlag' / slug
    brev = pf.las_json(bas / 'BREV.json')
    utskick_finns = (bas / 'UTSKICK.json').is_file()
    torr = torr or os.environ.get('NWP_UTSKICK') == 'torr'
    ok, skal = far_skickas(post, brev, las_sparr(), utskick_finns, hemligheter_finns())
    if not ok:
        raise Nekad(skal)
    h = las_hemligheter()
    amne, text = gallande_text(brev)
    kropp = text.strip() + '\n\n' + sidfot(h, post)
    till = brev['mottagare']['epost'].strip()
    sha = pf.text_sha(amne, text)
    utskick = {'schema': 1, 'slug': slug, 'kampanj': kampanj, 'tid': pf.nu(), 'till': till, 'amne': amne, 'text_sha': sha, 'torr': torr, 'svar': {}}
    if torr:
        utskick['resend_id'] = 'torr'
    else:
        data = {'from': h['AVSANDARE'], 'to': [till], 'reply_to': h['SVAR_TILL'], 'subject': amne, 'text': kropp,
                'headers': {'List-Unsubscribe': '<mailto:%s?subject=avregistrera>' % h['SVAR_TILL']},
                'tags': [{'name': 'kampanj', 'value': re.sub(r'[^a-zA-Z0-9_-]', '-', kampanj)}]}
        try:
            kod, svar = resend_anrop(h, '/emails', data, idempotens='nwp-%s-%s' % (slug, sha[:16]))
        except Exception as e:
            kod, svar = 0, {'fel': str(e)[:300]}
        if not (200 <= kod < 300) or not svar.get('id'):
            with open(bas / 'utskick-fel.log', 'a', encoding='utf-8') as f:
                f.write('%s %s %s\n' % (pf.nu(), kod, json.dumps(svar, ensure_ascii=False)[:500]))
            raise Nekad('Resend svarade %s: %s' % (kod, json.dumps(svar, ensure_ascii=False)[:200]))
        utskick['resend_id'] = svar['id']
    pf.skriv_json(bas / 'UTSKICK.json', utskick)
    pf.satt_status(kampanj, slug, 'skickat', skickat_tid=utskick['tid'])
    pf.logga(kampanj, 'skickat', slug=slug, till=till, resend_id=utskick['resend_id'], torr=torr)
    return utskick


def prov(till=None):
    h = las_hemligheter()
    till = till or h['SVAR_TILL']
    kod, svar = resend_anrop(h, '/emails', {'from': h['AVSANDARE'], 'to': [till], 'reply_to': h['SVAR_TILL'], 'subject': 'Provbrev från nortropic-webb-pro',
                                            'text': 'Det här är ett provbrev från utskick.py. Inget prospekt är inblandat.\n\n' + sidfot(h, {'namn': 'provverksamheten', 'jurform_text': 'juridisk person', 'postort': 'Luleå'})})
    if not (200 <= kod < 300):
        raise Nekad('Resend svarade %s: %s' % (kod, svar))
    return svar


def main(argv=None):
    p = argparse.ArgumentParser(prog='utskick', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='kommando', required=True)
    s = sub.add_parser('skicka')
    s.add_argument('slug')
    s.add_argument('--kampanj', required=True)
    s.add_argument('--torr', action='store_true')
    s = sub.add_parser('prov')
    s.add_argument('--till')
    s = sub.add_parser('sparr')
    s.add_argument('epost', nargs='?')
    s.add_argument('--skal', default='')
    s.add_argument('--lista', action='store_true')
    a = p.parse_args(argv)
    try:
        if a.kommando == 'skicka':
            if not pf.SLUG.match(a.slug):
                raise Nekad('ogiltig slug')
            u = skicka(a.slug, a.kampanj, a.torr)
            print(json.dumps({'ok': True, **u}, ensure_ascii=False))
            return 0
        if a.kommando == 'prov':
            print(json.dumps({'ok': True, 'svar': prov(a.till)}, ensure_ascii=False))
            return 0
        if a.kommando == 'sparr':
            if a.lista:
                kod, svar = resend_anrop(las_hemligheter(), '/suppressions?limit=100', metod='GET')
                print(json.dumps(svar, ensure_ascii=False, indent=1))
                return 0
            if not a.epost:
                raise Nekad('ange en adress eller --lista')
            print(json.dumps(sparr_lagg(a.epost, a.skal), ensure_ascii=False))
            return 0
    except Nekad as e:
        print(json.dumps({'ok': False, 'skal': str(e)}, ensure_ascii=False))
        return 4 if 'hemligheter' in str(e) or 'chmod' in str(e) else 3
    return 2


if __name__ == '__main__':
    sys.exit(main())
