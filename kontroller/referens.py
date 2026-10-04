#!/usr/bin/env python3
"""referens.py — det förberedande referenssteget: avgränsad insamling av referenssajter till ett fryst, versionsstyrt paket
(backlogposten B-20261004-forberedande-referenssteg-fore-sandladat-bygge; ägarbeslut 2026-10-04 med Codex fyra punkter).

    .venv/bin/python kontroller/referens.py <slug> [--uppdrag underlag/<slug>/REFERENSUPPDRAG.json] [--torr]

Uppdraget (JSON, skrivet av byggaren efter research och brief) listar kandidater: namn, adress, roll, varför, sidor och
de tillstånd beslutet gäller (meny, hover, fokus som CSS-väljare). Adressen är sajtens ursprung (https://värd/), ett
riktigt värdnamn (aldrig IP-adresser, lokala namn, användaruppgifter eller sökväg; Codex R32/R33); sidorna är
rotrelativa vägar som löses mot ursprunget; http → https och www-/bartvillingen hör till kandidaten. Varje kandidat inspekteras med
kontroller/webblasare/inspektera.mjs i två pass: först med bara sajtens eget ursprung (resursdomänerna som sajten
behöver syns då som blockerade), sedan med dessa resursdomäner tillåtna (bara för den inspektionen; spårare och lokala
adresser aldrig), så att bilder och typsnitt är laddade i fångsten. Nätet går genom hjälparens proxy: varje värd slås
upp och måste vara publik, omdirigeringar prövas hopp för hopp, bara läsande anrop, ingen skrivning, en färsk
webbläsarprofil per vy. Paketet underlag/<slug>/referenser/paket-vNN/ (skrivmålet förankras före första skrivningen,
också i torrkörning) har PAKET.json (adress, tidpunkt, tillåtna resursursprung, observationer, begränsningar, filer) och
PAKET.md. En sida räknas som fångad bara när båda vyerna finns med status 200, bildfilerna finns, de beställda
tillstånden lyckades och inga egna resurser (bilder, typsnitt, stilar) förblev blockerade eller misslyckades; en kandidat
bara när alla beställda sidor fångades. En komplettering är ett nytt uppdrag (fältet kompletterar = föregående paket)
och ger en ny, komplett version: orörda kandidater och, för en kandidat som kompletteras, dess orörda sidor ärvs från
föregående paket (kopierade utan att följa länkar), så att alla Bildval kan peka på den nya versionen; ersatt: true på
en kandidat betyder fullständig ersättning utan arv.
Med sandlådan på körs steget av webbtjänsten utanför byggsessionen (kontroller/webbtjanst.py, verktyget referens) med
uppdraget och utkatalogen som enda beröringspunkter; byggsessionens eget nät öppnas aldrig. Slutkod 0 när varje kandidat
fångades helt, annars 1 (paketet skrivs ändå, med bristerna i PAKET.json); 2 vid ogiltigt uppdrag eller oförankrat mål.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
INSPEKTERA = ROOT / 'kontroller' / 'webblasare' / 'inspektera.mjs'
NAMN = re.compile(r'^[a-z0-9][a-z0-9-]{1,39}$')
# riktiga värdnamn: etiketter av bokstäver, siffror och bindestreck, minst en punkt, alfabetisk toppdomän; utesluter varje
# IP-form (127.1, 0x7f000001, 2130706433, [::1]) och namn utan punkt (localhost)
DNSNAMN = re.compile(r'^(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:xn--[a-z0-9-]{2,59}|[a-z]{2,63})$')
LOKALA_SUFFIX = ('.local', '.localhost', '.internal', '.lan', '.home', '.arpa', '.test', '.example', '.invalid')
SPARARE = ('google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 'facebook.com', 'facebook.net', 'hotjar.com',
           'clarity.ms', 'segment.io', 'segment.com', 'mixpanel.com', 'linkedin.com', 'twitter.com', 'x.com', 'tiktok.com',
           'snapchat.com', 'pinterest.com', 'bing.com', 'yandex.ru', 'adsrvr.org', 'criteo.com', 'taboola.com', 'outbrain.com')
MAX_KANDIDATER, MAX_SIDOR, MAX_RESURSVARDAR = 12, 6, 15
VYER = ('390', '1440')
EGNA_RESURSER = ('image', 'font', 'stylesheet')  # det jämförelsen behöver; blockerade sidoförfrågningar av annan typ är tillåtna
PAKET = re.compile(r'^paket-v\d{2,}$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sidkatalog(i, vag):
    """Kollisionsfritt katalognamn per beställd sida: löpnummer plus en läsbar form av vägen (Codex R32: /a/b och /a-b gav
    samma katalog). Kopplingen till adressen står i PAKET.json."""
    s = re.sub(r'[^a-z0-9]+', '-', vag.strip('/').lower()).strip('-')[:40]
    return '%02d-%s' % (i + 1, s or 'start')


def lokal_adress(u, lokala_portar):
    """(adress, None) för http://127.0.0.1:<port>/… när porten är ett uttryckligt provundantag, annars (None, skäl)."""
    d = urllib.parse.urlsplit(u)
    if d.scheme == 'http' and d.hostname == '127.0.0.1' and d.port in set(lokala_portar) and not d.username and not d.password:
        if d.path not in ('', '/') or d.query or d.fragment:
            return None, 'adressen ska vara sajtens ursprung; lägg sökvägen under sidor'
        return 'http://127.0.0.1:%d/' % d.port, None
    return None, 'lokal adress utan provundantag'


def kanon_adress(u, lokala_portar=()):
    """(kanonisk adress, None) eller (None, skäl): http(s) till ett riktigt värdnamn utan användaruppgifter; aldrig en
    IP-adress i någon form, aldrig lokala eller reserverade namn. Lokala provundantag bara för uttryckliga portar."""
    if not isinstance(u, str) or len(u) > 500 or any(c in u for c in '\\\n\r\t\x00 '):
        return None, 'ogiltig adress'
    try:
        d = urllib.parse.urlsplit(u.strip())
    except ValueError:
        return None, 'ogiltig adress'
    if d.scheme not in ('http', 'https') or not d.hostname or d.username or d.password:
        return None, 'adressen måste vara http(s) utan användaruppgifter'
    if lokala_portar and d.hostname == '127.0.0.1':
        return lokal_adress(u.strip(), lokala_portar)
    vard = d.hostname.lower().rstrip('.')
    if not DNSNAMN.match(vard) or vard.endswith(LOKALA_SUFFIX):
        return None, 'adressen måste gå till ett riktigt värdnamn (inte IP-adress, localhost eller reserverat namn)'
    try:
        port = d.port
    except ValueError:
        return None, 'ogiltig port'
    if port is not None and port not in (80, 443):
        return None, 'bara standardportar (80, 443)'
    if d.path not in ('', '/') or d.query or d.fragment:
        return None, 'adressen ska vara sajtens ursprung (https://värd/); lägg sökvägen under sidor (Codex R33: tvetydiga uppdrag vägras)'
    return urllib.parse.urlunsplit((d.scheme, vard + (':%d' % port if port else ''), '/', '', '')), None


def las_uppdrag(fil, slug, lokala_portar=()):
    """Uppdraget validerat: ger (uppdrag, None) eller (None, skäl)."""
    try:
        u = json.loads(Path(fil).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return None, 'uppdraget går inte att läsa: %s' % e
    if not isinstance(u, dict) or not isinstance(u.get('kandidater'), list) or not u['kandidater']:
        return None, 'uppdraget saknar kandidater'
    if len(u['kandidater']) > MAX_KANDIDATER:
        return None, 'högst %d kandidater per uppdrag' % MAX_KANDIDATER
    if u.get('kompletterar') is not None and not PAKET.match(str(u['kompletterar'])):
        return None, 'kompletterar måste peka på ett paket (paket-vNN)'
    namn = set()
    kandidater = []
    for k in u['kandidater']:
        if not isinstance(k, dict) or not NAMN.match(str(k.get('namn', ''))):
            return None, 'varje kandidat behöver ett namn [a-z0-9-]'
        if k['namn'] in namn:
            return None, 'kandidatnamnet %s upprepas' % k['namn']
        namn.add(k['namn'])
        adress, fel = kanon_adress(k.get('adress'), lokala_portar)
        if fel:
            return None, '%s: %s' % (k['namn'], fel)
        if k.get('roll') not in ('bransch', 'hantverk', 'ux'):
            return None, '%s: roll måste vara bransch, hantverk eller ux' % k['namn']
        sidor = k.get('sidor') or ['/']
        if not isinstance(sidor, list) or len(sidor) > MAX_SIDOR or not all(isinstance(s, str) and s.startswith('/') and not s.startswith('//') and len(s) < 200 and not any(c in s for c in '\\\n\r\t\x00 #') for s in sidor):
            return None, '%s: sidor är högst %d rotrelativa vägar som börjar med / (löses mot ursprunget)' % (k['namn'], MAX_SIDOR)
        if k.get('ersatt') not in (None, True, False):
            return None, '%s: ersatt är sant eller falskt' % k['namn']
        tillstand = {}
        for t in ('meny', 'hover', 'fokus'):
            v = k.get(t)
            if v is not None:
                if not isinstance(v, str) or not 0 < len(v) <= 200 or '\n' in v:
                    return None, '%s: %s måste vara en CSS-väljare' % (k['namn'], t)
                tillstand[t] = v
        kandidater.append({'namn': k['namn'], 'adress': adress, 'roll': k['roll'], 'varfor': str(k.get('varfor') or '')[:1000],
                           'sidor': list(dict.fromkeys(sidor)), 'tillstand': tillstand, 'ersatt': bool(k.get('ersatt'))})
    return {'kandidater': kandidater, 'fragor': [str(f)[:500] for f in (u.get('fragor') or [])][:20], 'kompletterar': u.get('kompletterar')}, None


def inom(p, rot):
    try:
        v, r = Path(p).resolve(), Path(rot).resolve()
    except (OSError, RuntimeError):
        return False
    return v == r or r in v.parents


def forankrad_rot(underlag, slug):
    """Paketets skrivmål före första skrivningen (Codex R32): underlag/<slug> och referenser/ får inte vara länkar som
    pekar utanför underlag/<slug>. Ger (referenskatalog, None) eller (None, skäl)."""
    underlag = Path(underlag)
    kund = underlag / slug
    if not kund.is_dir() or kund.is_symlink() or not inom(kund, underlag):
        return None, 'underlag/%s saknas eller är en länk utanför underlag/' % slug
    rot = kund / 'referenser'
    if rot.is_symlink() or (rot.exists() and not rot.is_dir()) or (rot.exists() and not inom(rot, kund)):
        return None, 'underlag/%s/referenser är en länk eller ingen katalog; paketet skrivs inte' % slug
    return rot, None


def ny_version(rot):
    """Nästa paket-vNN under referenser/, skapad exklusivt och förankrad (ingen länk, rätt förälder)."""
    rot = Path(rot)
    rot.mkdir(parents=True, exist_ok=True)
    if rot.is_symlink():
        raise RuntimeError('referenser/ blev en länk')
    n = max([int(p.name[7:]) for p in rot.glob('paket-v*') if PAKET.match(p.name)] or [0]) + 1
    while True:
        p = rot / ('paket-v%02d' % n)
        try:
            p.mkdir()
        except FileExistsError:
            n += 1
            continue
        if p.is_symlink() or p.resolve().parent != rot.resolve():
            raise RuntimeError('paketkatalogen %s är inte förankrad' % p)
        return p


def ursprung(u):
    d = urllib.parse.urlsplit(u)
    return '%s://%s' % (d.scheme, d.netloc)


def tvillingar(vard):
    """www och bar domän är samma verksamhet (som i sandlada.domanlista): en kandidat som svarar med en omdirigering
    mellan dem får inte stoppas av policyn (bygge 4: dinesen.com → www blockerades)."""
    vard = vard.lower()
    if vard == '127.0.0.1' or vard.count('.') < 1:
        return {vard}
    return {vard, vard[4:] if vard.startswith('www.') else 'www.' + vard}


def kandidat_ursprung(adress):
    """Kandidatens egna ursprung: adressens värd och www-/bartvillingen, i båda scheman med standardport (en accepterad
    http-adress som omdirigerar till https på samma domän får inte stoppas; Codex R33). Lokala provadresser: bara den egna."""
    d = urllib.parse.urlsplit(adress)
    if d.hostname == '127.0.0.1':
        return ['http://127.0.0.1:%d' % d.port]
    varden = sorted(tvillingar(d.hostname), key=lambda v: v != d.hostname)
    scheman = [d.scheme] + [x for x in ('https', 'http') if x != d.scheme]
    return ['%s://%s' % (sch, v) for sch in scheman for v in varden]


def sidadress(adress, sida):
    """Sidans adress: den rotrelativa vägen löst mot ursprunget (Codex R33: ingen strängsammanfogning)."""
    return urllib.parse.urljoin(adress, sida)


def tillatet_resursursprung(u, lokala_portar):
    """Ursprunget för en blockerad resurs, om det får tillåtas i pass 2: riktigt värdnamn (samma regler som kandidater),
    aldrig spårare, lokala bara med uttryckligt provundantag (Codex R32)."""
    try:
        d = urllib.parse.urlsplit(u)
    except ValueError:
        return None
    if d.scheme not in ('http', 'https') or not d.hostname:
        return None
    vard = d.hostname.lower().rstrip('.')
    if any(vard == s or vard.endswith('.' + s) for s in SPARARE):
        return None
    if vard == '127.0.0.1':
        return ('http://127.0.0.1:%d' % d.port) if (d.scheme == 'http' and d.port in set(lokala_portar)) else None
    if not DNSNAMN.match(vard) or vard.endswith(LOKALA_SUFFIX):
        return None
    try:
        port = d.port
    except ValueError:
        return None
    if port is not None and port not in (80, 443):
        return None
    return '%s://%s' % (d.scheme, vard + (':%d' % port if port else ''))


def blockerade_ursprung(rapport, lokala_portar=()):
    """Ursprung som sajten försökte nå men som vakten stoppade: resursdomäner (bilder, typsnitt, stilar, skript, xhr)."""
    ut = []
    for vy in (rapport.get('vyer') or {}).values():
        for b in (vy.get('natverk') or {}).get('blockerade') or []:
            if b.get('typ') in ('websocket', 'media', 'other'):
                continue
            o = tillatet_resursursprung(b.get('url') or '', lokala_portar)
            if o and o not in ut:
                ut.append(o)
    return ut[:MAX_RESURSVARDAR]


def kor_inspektera(adress, ut, tillat, tillstand, miljo):
    args = ['node', str(INSPEKTERA), '--adress', adress, '--ut', str(ut), '--vyer', ','.join(VYER), '--tillstand', 'tangentbord,reflow']
    if tillat:
        args += ['--tillat', ';'.join(tillat)]
    for t, v in tillstand.items():
        args += ['--' + t, v]
    r = subprocess.run(args, cwd=str(ROOT), env=miljo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    rapport = {}
    try:
        rapport = json.loads((Path(ut) / 'INSPEKTION.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    return r.returncode, rapport, r.stdout.decode('utf-8', 'replace')[-2000:]


def miljo_for(varden):
    """Barnprocessens miljö: hjälparens domänpolicy = kandidatens värdar (NWP_NAT_TILLATNA), aldrig proxyvariabler,
    aldrig tjänstens adress (barnet ska inte delegera vidare)."""
    m = {k: v for k, v in os.environ.items() if not k.upper().endswith('_PROXY') and k not in ('REFERO_MCP_TOKEN', 'NWP_WEBBTJANST', 'NWP_WEBBTJANST_NYCKEL')}
    m['NWP_NAT_TILLATNA'] = ','.join(sorted(varden))
    m['NWP_I_TJANSTEN'] = '1'
    return m


def tillstand_utfall(t, bestallda):
    """Vilka beställda tillstånd som lyckades i en vy: meny klickad, hover och fokus utan fel."""
    ut = {}
    for namn in bestallda:
        if namn == 'meny':
            ut[namn] = isinstance(t.get('meny'), dict) and t['meny'].get('klickad') is True
        else:
            ut[namn] = namn in t and (namn + '_fel') not in t
    return ut


def observationer(rapport, ut, bestallda=()):
    """Det som följer med i paketet per sida: status, titel, laddade bilder och typsnitt, kvarvarande blockeringar av
    egna resurser, tillståndens utfall, bildfilerna, tecken på kakdialog, misstänkt tomma bilder; och om sidan är
    fångad: båda vyerna med status 200 utan fel, bildfilerna på plats, tillstånden lyckade, inga egna resurser kvar
    blockerade (Codex R32)."""
    obs = {'vyer': {}, 'kvar_blockerade': [], 'fel_resurser': [], 'begransningar': [], 'ok': False}
    vyer = rapport.get('vyer') or {}
    for vy, r in vyer.items():
        nat = r.get('natverk') or {}
        laddade = nat.get('laddade') or {}
        bilder = {fil: (Path(ut) / fil).is_file() and (Path(ut) / fil).stat().st_size > 0 for fil in ('vy-%s-forsta.png' % vy, 'vy-%s-hela.png' % vy)}
        t_ok = tillstand_utfall(r.get('tillstand') or {}, bestallda)
        obs['vyer'][vy] = {'status': r.get('status'), 'titel': r.get('titel'), 'h1': r.get('h1'), 'skarmar': r.get('skarmar'),
                           'bilder_laddade': int(laddade.get('image') or 0), 'typsnitt_laddade': int(laddade.get('font') or 0),
                           'stilar_laddade': int(laddade.get('stylesheet') or 0), 'blockerade': len(nat.get('blockerade') or []),
                           'bildfiler': bilder, 'tillstand': t_ok, 'fel': r.get('fel')}
        for b in nat.get('blockerade') or []:
            if b.get('typ') in EGNA_RESURSER + ('script', 'xhr', 'fetch', 'document'):
                vard = (urllib.parse.urlsplit(b.get('url') or '').hostname or '').lower()
                if any(vard == s or vard.endswith('.' + s) for s in SPARARE):
                    continue
                obs['kvar_blockerade'].append({'vy': vy, 'typ': b.get('typ'), 'url': (b.get('url') or '')[:200]})
        for e in nat.get('fel') or []:  # misslyckade anrop (status null eller ≥ 400) av egna resurser: felorsaken bevaras (Codex R33)
            if e.get('typ') in EGNA_RESURSER:
                vard = (urllib.parse.urlsplit(e.get('url') or '').hostname or '').lower()
                if any(vard == s or vard.endswith('.' + s) for s in SPARARE):
                    continue
                obs['fel_resurser'].append({'vy': vy, 'typ': e.get('typ'), 'url': (e.get('url') or '')[:200], 'status': e.get('status'), 'fel': (e.get('fel') or '')[:120]})
        aria = Path(ut) / ('vy-%s-aria.txt' % vy)
        if aria.is_file():
            text = aria.read_text(encoding='utf-8', errors='replace').lower()
            if any(ord_ in text for ord_ in ('cookie', 'kakor', 'samtycke', 'consent', 'godkänn alla', 'accept all')):
                obs['begransningar'].append('vy %s: kakdialog syns troligen i bilderna (ordet cookie/kakor/samtycke i tillgänglighetsträdet)' % vy)
        for fil, finns in bilder.items():
            p = Path(ut) / fil
            if not finns:
                obs['begransningar'].append('%s saknas' % fil)
            elif p.stat().st_size < 6000:
                obs['begransningar'].append('%s är misstänkt tom (%d byte)' % (fil, p.stat().st_size))
        for namn, ok in t_ok.items():
            if not ok:
                obs['begransningar'].append('vy %s: tillståndet %s lyckades inte' % (vy, namn))
        if r.get('status') != 200:
            obs['begransningar'].append('vy %s: status %s' % (vy, r.get('status')))
        if r.get('fel'):
            obs['begransningar'].append('vy %s: %s' % (vy, str(r.get('fel'))[:200]))
    for vy in VYER:
        if vy not in vyer:
            obs['begransningar'].append('vy %s saknas i rapporten' % vy)
    egna_kvar = [b for b in obs['kvar_blockerade'] if b['typ'] in EGNA_RESURSER]
    if egna_kvar:
        obs['begransningar'].append('%d egna resurser (bild, typsnitt, stil) förblev blockerade' % len(egna_kvar))
    if obs['fel_resurser']:
        obs['begransningar'].append('%d egna resurser (bild, typsnitt, stil) misslyckades: %s' % (len(obs['fel_resurser']), '; '.join('%s %s %s' % (e['typ'], e['status'] if e['status'] is not None else e['fel'], e['url']) for e in obs['fel_resurser'][:5])))
    obs['ok'] = (all(vy in vyer for vy in VYER) and not egna_kvar and not obs['fel_resurser']
                 and all(o['status'] == 200 and not o['fel'] and all(o['bildfiler'].values()) and all(o['tillstand'].values()) for o in obs['vyer'].values()))
    return obs


def kopiera_sakert(kalla, mal, rot, vantade=()):
    """Kopierar ett träd ur ett tidigare paket utan att följa länkar: varje post måste vara en vanlig fil eller katalog
    (ingen länk, ingenting utanför rot); bryter en post mot det kopieras ingenting (Codex R33: copytree följde nästlade
    länkar och kunde läsa utanför referensområdet). Ett inventeringsfel avbryter, och de förväntade filerna (vantade,
    relativt mal) verifieras i kopian innan arvet godkänns (Codex R34)."""
    kalla, mal, rot = Path(kalla), Path(mal), Path(rot).resolve()
    if kalla.is_symlink() or not kalla.is_dir():
        raise RuntimeError('arvskällan %s är ingen katalog' % kalla)
    poster = []

    def fel(e):
        raise RuntimeError('arvskällan kunde inte inventeras: %s' % e)
    for d, mappar, filer in os.walk(kalla, onerror=fel, followlinks=False):
        for n in mappar + filer:
            p = Path(d) / n
            if p.is_symlink():
                raise RuntimeError('länk i arvskällan: %s' % p)
            v = p.resolve()
            if v != rot and rot not in v.parents:
                raise RuntimeError('arvskällan pekar utanför referensområdet: %s' % p)
            if not (p.is_dir() or p.is_file()):
                raise RuntimeError('oväntad post i arvskällan: %s' % p)
            poster.append(p)
    mal.mkdir(parents=True, exist_ok=False)
    for p in poster:
        m = mal / p.relative_to(kalla)
        if p.is_dir():
            m.mkdir(exist_ok=True)
        else:
            shutil.copyfile(p, m)  # copyfile följer inga länkar här: posten är redan prövad som vanlig fil
    for d, mappar, filer in os.walk(mal, onerror=fel):
        for n in mappar + filer:
            if (Path(d) / n).is_symlink():
                raise RuntimeError('länk i kopian: %s' % (Path(d) / n))
    saknas = [v for v in vantade if not (mal / v).is_file() or (mal / v).stat().st_size == 0]
    if saknas:
        raise RuntimeError('arvet är ofullständigt, filer saknas i %s: %s' % (kalla, ', '.join(saknas[:5])))


def samma_referens(a, b):
    """Två adresser gäller samma referens när värden är densamma eller dess www-/bartvilling (http och https räknas lika);
    en lokal provadress bara med samma port. Ett byte av referens under samma kandidatnamn vägras utan ersatt (Codex R34)."""
    da, db = urllib.parse.urlsplit(a), urllib.parse.urlsplit(b)
    if da.hostname == '127.0.0.1' or db.hostname == '127.0.0.1':
        return da.hostname == db.hostname and da.port == db.port
    va, vb = (da.hostname or '').lower().rstrip('.'), (db.hostname or '').lower().rstrip('.')
    return bool(va) and (va == vb or va == 'www.' + vb or vb == 'www.' + va)  # direkt relation, inte överlapp via en tredje värd (Codex R35)


def arvd_ok(sidor):
    """Ärvt material räknas som fångat bara när varje sida var fångad, har en fillista och deklarerar båda vyernas
    bildfiler som befintliga (Codex R35: ett torrpaket eller ett inlägg utan filer får inte ärvas som färdig fångst)."""
    if not sidor:
        return False
    for fs in sidor:
        if not isinstance(fs, dict) or not fs.get('ok') or not fs.get('filer'):
            return False
        vyer = fs.get('observationer') or {}
        if set(vyer) != set(VYER) or not all(all((o.get('bildfiler') or {}).values()) and (o.get('bildfiler') or {}) for o in vyer.values()):
            return False
    return True


def filer_for(post, sidor=None):
    """De filer ett paketinlägg deklarerar (relativt paketet), för verifiering av arvet."""
    ut = []
    for fs in (post.get('sidor') or []) if sidor is None else sidor:
        if isinstance(fs, dict):
            ut += [x for x in fs.get('filer') or [] if isinstance(x, str) and not x.startswith('/') and '..' not in x]
    return ut


def tom_observation(skal):
    """Observationer för en sida utan rapport: samma fält som vanliga observationer, bristen dokumenterad, aldrig fångad."""
    return {'vyer': {}, 'kvar_blockerade': [], 'fel_resurser': [], 'begransningar': [skal], 'ok': False}


def las_paket(rot, version):
    p = Path(rot) / version
    if not PAKET.match(version) or not p.is_dir() or p.is_symlink() or not inom(p, rot):
        return None, None
    try:
        return p, json.loads((p / 'PAKET.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return p, None


def samla(slug, uppdrag, underlag=None, torr=False, lokala_portar=()):
    """Kör uppdraget och skriver paketet. Ger (paketkatalog, resultat). RuntimeError när målet inte är förankrat eller
    det paket som kompletteras saknas."""
    underlag = Path(underlag or UNDERLAG)
    rot, fel = forankrad_rot(underlag, slug)
    if fel:
        raise RuntimeError(fel)
    arv_fran, arv = None, {}
    if uppdrag.get('kompletterar'):
        arv_fran, forra = las_paket(rot, uppdrag['kompletterar'])
        if arv_fran is None or not isinstance(forra, dict):
            raise RuntimeError('paketet som kompletteras (%s) finns inte eller går inte att läsa' % uppdrag['kompletterar'])
        if forra.get('torr') and not torr:
            raise RuntimeError('paketet som kompletteras (%s) är en torrkörning utan fångster; kör om fullständigt i stället för att ärva' % uppdrag['kompletterar'])
        arv = {k['namn']: k for k in forra.get('kandidater') or [] if isinstance(k, dict) and NAMN.match(str(k.get('namn', '')))}
    paket = ny_version(rot)
    try:
        return _samla(slug, uppdrag, paket, rot, arv_fran, arv, torr, lokala_portar)
    except Exception:
        shutil.rmtree(paket, ignore_errors=True)  # ett vägrat arv lämnar inget halvt paket efter sig
        raise


def _samla(slug, uppdrag, paket, rot, arv_fran, arv, torr, lokala_portar):
    res = {'schema': 2, 'slug': slug, 'version': paket.name, 'tid': nu(), 'kompletterar': uppdrag.get('kompletterar'),
           'uppdrag_sha256': hashlib.sha256(json.dumps(uppdrag, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
           'fragor': uppdrag['fragor'], 'kandidater': [], 'torr': torr}
    alla_ok = True
    nya = {k['namn'] for k in uppdrag['kandidater']}
    for k in uppdrag['kandidater']:
        post = {'namn': k['namn'], 'adress': k['adress'], 'roll': k['roll'], 'varfor': k['varfor'], 'sidor': [], 'resursursprung': [], 'ok': False}
        katalog = paket / k['namn']
        katalog.mkdir()
        # komplettering av samma kandidat: oförändrade sidor ärvs från föregående paket (sida för sida, med sin katalog);
        # ersatt: true betyder fullständig ersättning utan arv (Codex R33)
        forra_k = arv.get(k['namn']) if arv_fran is not None and not k.get('ersatt') else None
        if forra_k and not samma_referens(str(forra_k.get('adress') or ''), k['adress']):
            raise RuntimeError('kandidaten %s byter referens (%s → %s): sätt ersatt: true eller ge den ett nytt namn' % (k['namn'], forra_k.get('adress'), k['adress']))
        arvda_sidor = []
        for fs in (forra_k or {}).get('sidor') or []:
            if isinstance(fs, dict) and fs.get('sida') not in k['sidor'] and isinstance(fs.get('katalog'), str) and fs['katalog'].startswith(k['namn'] + '/') and '..' not in fs['katalog']:
                vantade = [x[len(fs['katalog']) + 1:] for x in filer_for(forra_k, [fs]) if x.startswith(fs['katalog'] + '/')]
                kopiera_sakert(arv_fran / fs['katalog'], paket / fs['katalog'], rot, vantade)
                arvda_sidor.append(dict(fs, arv=arv_fran.name))
        if forra_k:
            post['resursursprung'] = list(forra_k.get('resursursprung') or [])
        if torr:
            post['sidor'] = arvda_sidor
            post['ok'] = True
            res['kandidater'].append(post)
            continue
        egna = kandidat_ursprung(k['adress'])  # adressens ursprung, www-/bartvillingen, båda scheman
        varden = tvillingar(urllib.parse.urlsplit(k['adress']).hostname)
        # pass 1 på första sidan: vilka resursursprung behöver sajten?
        forsta = sidadress(k['adress'], k['sidor'][0])
        pass1 = katalog / '.pass1'
        post['begransningar'] = []
        try:
            rc1, rapport1, _ = kor_inspektera(forsta, pass1, egna, {}, miljo_for(varden))
            resurser = [o for o in blockerade_ursprung(rapport1, lokala_portar) if o not in egna]
        except Exception as e:  # ett fel i första passet är en brist, aldrig ett borttaget paket (Codex R35)
            resurser = []
            post['begransningar'].append('första passet (resursursprung) föll: %s' % str(e)[:300])
        shutil.rmtree(pass1, ignore_errors=True)
        tillat = egna + resurser
        varden |= {urllib.parse.urlsplit(o).hostname for o in resurser}
        post['resursursprung'] = list(dict.fromkeys(post['resursursprung'] + resurser))
        # pass 2 på varje sida med resursursprungen tillåtna, bara för den här inspektionen
        upptagna = {fs['katalog'] for fs in arvda_sidor}
        for i, sida in enumerate(k['sidor']):
            adress = sidadress(k['adress'], sida)
            ut = katalog / sidkatalog(i, sida)
            while str(ut.relative_to(paket)) in upptagna:  # krockar aldrig med en ärvd sidkatalog
                ut = ut.with_name(ut.name + '-ny')
            tillstand = k['tillstand'] if i == 0 else {}
            try:
                rc, rapport, utskrift = kor_inspektera(adress, ut, tillat, tillstand, miljo_for(varden))
                obs = observationer(rapport, ut, tuple(tillstand)) if rapport else tom_observation('inspektionen gav ingen rapport: ' + utskrift[-300:])
            except Exception as e:  # en fallerad inspektion är en brist i paketet, aldrig ett borttaget paket (Codex R34)
                rc, obs = 1, tom_observation('inspektionen föll: %s' % str(e)[:300])
            filer = sorted(str(p.relative_to(paket)) for p in ut.rglob('*') if p.is_file() and p.suffix in ('.png', '.txt', '.md', '.json')) if ut.is_dir() else []
            for vy_, o_ in obs['vyer'].items():  # bildfilerna som inlägget deklarerar ska finnas: annars ingen fångst
                for fil_, finns_ in (o_.get('bildfiler') or {}).items():
                    if finns_ and str((ut / fil_).relative_to(paket)) not in filer:
                        o_['bildfiler'][fil_] = False
                        obs['begransningar'].append('%s saknas i inventeringen' % fil_)
            sida_ok = rc == 0 and obs['ok'] and all(all((o_.get('bildfiler') or {}).values()) for o_ in obs['vyer'].values())  # efter sista bildkontrollen (Codex R35)
            post['sidor'].append({'sida': sida, 'adress': adress, 'katalog': str(ut.relative_to(paket)), 'tillstand': tillstand, 'rc': rc, 'ok': sida_ok,
                                  'observationer': obs['vyer'], 'kvar_blockerade': obs['kvar_blockerade'], 'fel_resurser': obs['fel_resurser'],
                                  'begransningar': obs['begransningar'], 'filer': filer})
        nya_ok = len(post['sidor']) == len(k['sidor']) and all(s['ok'] for s in post['sidor'])
        post['sidor'] += arvda_sidor
        post['ok'] = bool(post['sidor']) and nya_ok and (not arvda_sidor or arvd_ok(arvda_sidor))
        alla_ok = alla_ok and post['ok']
        res['kandidater'].append(post)
    # komplettering: orörda kandidater ärvs hela från föregående paket, så att varje Bildval kan peka på den nya versionen
    for namn, post in arv.items():
        if namn in nya:
            continue
        if not (arv_fran / namn).is_dir() or (arv_fran / namn).is_symlink():
            raise RuntimeError('kandidaten %s saknas i %s; arvet kan inte godkännas' % (namn, arv_fran.name))
        vantade = [x[len(namn) + 1:] for x in filer_for(post) if x.startswith(namn + '/')]
        kopiera_sakert(arv_fran / namn, paket / namn, rot, vantade)
        arvd = dict(post, arv=arv_fran.name, ok=bool(post.get('ok')) and arvd_ok(post.get('sidor')))
        res['kandidater'].append(arvd)
        alla_ok = alla_ok and arvd['ok']
    res['alla_ok'] = alla_ok
    (paket / 'PAKET.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    rader = ['# Referenspaket %s · %s · %s' % (paket.name, slug, res['tid']), '']
    if uppdrag.get('kompletterar'):
        rader.append('Kompletterar %s; oförändrat material är ärvt därifrån, så alla Bildval kan peka på %s.' % (uppdrag['kompletterar'], paket.name))
    rader += ['Fångat med kontroller/referens.py: två pass per kandidat (eget ursprung, sedan sajtens resursursprung tillåtna bara för',
              'inspektionen), läsande, publika adresser, färsk webbläsarprofil. Peka ut bilder i REFERENSER.md som',
              '`Bildval: referenser/%s/<kandidat>/<NN-sida>/<fil>.png — … — Fråga: …`.' % paket.name, '']
    for post in res['kandidater']:
        rader += ['## %s · %s · %s%s' % (post['namn'], post['roll'], post['adress'], ' · ärvd från %s' % post['arv'] if post.get('arv') else ''), '', post['varfor'] or '(ingen motivering)', '']
        if not post.get('arv') and any(s.get('arv') for s in post['sidor']):
            rader.append('- sidor ärvda från %s: %s' % (', '.join(sorted({s['arv'] for s in post['sidor'] if s.get('arv')})), ', '.join(s['sida'] for s in post['sidor'] if s.get('arv'))))
        if not post['sidor']:
            rader.append('- torrkörning: inget fångat' if torr else '- inget fångat')
        for s in post['sidor']:
            vy = s['observationer']
            rader.append('- %s (%s): %s · status %s · bilder laddade %s · typsnitt %s · blockerade kvar %d · filer %d' % (
                s['sida'], s['katalog'], 'fångad' if s['ok'] else 'brister', ','.join(str(v.get('status')) for v in vy.values()),
                '/'.join(str(v.get('bilder_laddade')) for v in vy.values()), '/'.join(str(v.get('typsnitt_laddade')) for v in vy.values()),
                len(s['kvar_blockerade']), len(s['filer'])))
            for b in s['begransningar']:
                rader.append('  - begränsning: ' + b)
        for b in post.get('begransningar') or []:
            rader.append('- begränsning: ' + b)
        if post['resursursprung']:
            rader.append('- resursursprung tillåtna för inspektionen: ' + ', '.join(post['resursursprung']))
        rader.append('')
    (paket / 'PAKET.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return paket, res


def main(argv=None):
    p = argparse.ArgumentParser(prog='referens', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--uppdrag', default=None, help='standard underlag/<slug>/REFERENSUPPDRAG.json')
    p.add_argument('--torr', action='store_true', help='validera uppdraget och skriv ett tomt paket utan att öppna sajterna')
    p.add_argument('--underlag', default=None, help=argparse.SUPPRESS)
    p.add_argument('--tillat-lokalt', default=None, help=argparse.SUPPRESS)  # bara rökprovet: kommaseparerade portar på 127.0.0.1
    a = p.parse_args(argv)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug):
        print('ogiltig slug', file=sys.stderr)
        return 2
    krav_slug(a.slug)
    import webbtjanst
    if webbtjanst.delegeras() and not a.underlag:
        # sandlådat bygge: steget körs av webbtjänsten utanför byggsessionen, med samma uppdrag och samma utkatalog
        argv_ = [a.slug] + (['--uppdrag', a.uppdrag] if a.uppdrag else []) + (['--torr'] if a.torr else [])
        return webbtjanst.via_tjanst('referens', argv_)
    lokala_portar = ()
    if a.tillat_lokalt:
        if not re.fullmatch(r'\d{2,5}(,\d{2,5})*', a.tillat_lokalt):
            print('--tillat-lokalt tar kommaseparerade portar', file=sys.stderr)
            return 2
        lokala_portar = tuple(int(x) for x in a.tillat_lokalt.split(','))
    underlag = Path(a.underlag or UNDERLAG)
    fil = Path(a.uppdrag) if a.uppdrag else underlag / a.slug / 'REFERENSUPPDRAG.json'
    if not fil.is_absolute():
        fil = ROOT / fil
    if not inom(fil, underlag / a.slug) or not fil.is_file():
        print('uppdraget måste ligga under underlag/%s/' % a.slug, file=sys.stderr)
        return 2
    uppdrag, fel = las_uppdrag(fil, a.slug, lokala_portar)
    if fel:
        print('uppdraget vägras: %s' % fel, file=sys.stderr)
        return 2
    try:
        paket, res = samla(a.slug, uppdrag, underlag, torr=a.torr, lokala_portar=lokala_portar)
    except RuntimeError as e:
        print('referenssteget vägrar: %s' % e, file=sys.stderr)
        return 2
    rel = paket.relative_to(ROOT) if str(paket).startswith(str(ROOT) + os.sep) else paket
    print('Referenspaket %s: %d kandidater, %s. Översikt: %s' % (rel, len(res['kandidater']), 'allt fångat' if res['alla_ok'] else 'brister finns (PAKET.json)', rel / 'PAKET.md'))
    for post in res['kandidater']:
        print('- %s (%s): %s%s' % (post['namn'], post['roll'], 'fångad' if post['ok'] else 'brister', ' · ärvd' if post.get('arv') else ''))
    return 0 if res['alla_ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
