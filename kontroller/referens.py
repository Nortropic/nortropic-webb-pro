#!/usr/bin/env python3
"""referens.py — det förberedande referenssteget: avgränsad insamling av referenssajter till ett fryst, versionsstyrt paket
(backlogposten B-20261004-forberedande-referenssteg-fore-sandladat-bygge; ägarbeslut 2026-10-04 med Codex fyra punkter).

    .venv/bin/python kontroller/referens.py <slug> [--uppdrag underlag/<slug>/REFERENSUPPDRAG.json] [--torr]

Uppdraget (JSON, skrivet av byggaren efter research och brief) listar kandidater: namn, adress, roll, varför, sidor och
de tillstånd beslutet gäller (meny, hover, fokus som CSS-väljare). Varje kandidat inspekteras med
kontroller/webblasare/inspektera.mjs i två pass: först med bara sajtens eget ursprung (resursdomänerna som sajten
behöver syns då som blockerade), sedan med dessa resursdomäner tillåtna (bara för den inspektionen; spårare släpps aldrig),
så att bilder och typsnitt är laddade i fångsten. Nätet går genom hjälparens proxy: varje värd slås upp och måste vara
publik, omdirigeringar prövas hopp för hopp, bara läsande anrop, ingen skrivning, en färsk webbläsarprofil per vy.
Resultatet är ett paket underlag/<slug>/referenser/paket-vNN/ med PAKET.json (adress, tidpunkt, tillåtna resursdomäner,
observationer, begränsningar, filer) och PAKET.md. En komplettering är ett nytt uppdrag (fältet kompletterar) och ger en ny
version; byggare, ateljé och granskare pekar på filer i ett paket (Bildval i REFERENSER.md) och omgången fryser dem.
Med sandlådan på körs steget av webbtjänsten utanför byggsessionen (kontroller/webbtjanst.py, verktyget referens) med
uppdraget och utkatalogen som enda beröringspunkter; byggsessionens eget nät öppnas aldrig. Slutkod 0 när varje kandidat
fångades med status 200 på första sidan, annars 1 (paketet skrivs ändå, med bristerna i PAKET.json); 2 vid ogiltigt uppdrag.
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
SPARARE = ('google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 'facebook.com', 'facebook.net', 'hotjar.com',
           'clarity.ms', 'segment.io', 'segment.com', 'mixpanel.com', 'linkedin.com', 'twitter.com', 'x.com', 'tiktok.com',
           'snapchat.com', 'pinterest.com', 'bing.com', 'yandex.ru', 'adsrvr.org', 'criteo.com', 'taboola.com', 'outbrain.com')
MAX_KANDIDATER, MAX_SIDOR, MAX_RESURSVARDAR = 12, 6, 15
VYER = ('390', '1440')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sidnamn(vag):
    s = re.sub(r'[^a-z0-9]+', '-', vag.strip('/').lower()).strip('-')
    return s or 'start'


def kanon_adress(u):
    """(kanonisk adress, None) eller (None, skäl): http(s), värdnamn utan användaruppgifter, inte lokal; adresserna
    slås upp och prövas mot det egna nätet i hjälparens proxy när de används."""
    if not isinstance(u, str) or len(u) > 500 or any(c in u for c in '\\\n\r\t\x00 '):
        return None, 'ogiltig adress'
    try:
        d = urllib.parse.urlsplit(u.strip())
    except ValueError:
        return None, 'ogiltig adress'
    if d.scheme not in ('http', 'https') or not d.hostname or d.username or d.password:
        return None, 'adressen måste vara http(s) utan användaruppgifter'
    vard = d.hostname.lower()
    if vard in ('localhost',) or vard.endswith('.local') or re.fullmatch(r'[0-9.]+|\[?[0-9a-f:]+\]?', vard):
        return None, 'adressen får inte vara lokal eller en IP-adress'  # provet använder --tillat-lokalt
    port = ':%d' % d.port if d.port else ''
    return urllib.parse.urlunsplit((d.scheme, vard + port, d.path or '/', d.query, '')), None


def las_uppdrag(fil, slug, lokalt_ok=False):
    """Uppdraget validerat: ger (uppdrag, None) eller (None, skäl)."""
    try:
        u = json.loads(Path(fil).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return None, 'uppdraget går inte att läsa: %s' % e
    if not isinstance(u, dict) or not isinstance(u.get('kandidater'), list) or not u['kandidater']:
        return None, 'uppdraget saknar kandidater'
    if len(u['kandidater']) > MAX_KANDIDATER:
        return None, 'högst %d kandidater per uppdrag' % MAX_KANDIDATER
    if u.get('kompletterar') is not None and not re.fullmatch(r'paket-v\d{2,}', str(u['kompletterar'])):
        return None, 'kompletterar måste peka på ett paket (paket-vNN)'
    namn = set()
    kandidater = []
    for k in u['kandidater']:
        if not isinstance(k, dict) or not NAMN.match(str(k.get('namn', ''))):
            return None, 'varje kandidat behöver ett namn [a-z0-9-]'
        if k['namn'] in namn:
            return None, 'kandidatnamnet %s upprepas' % k['namn']
        namn.add(k['namn'])
        if lokalt_ok and isinstance(k.get('adress'), str) and re.match(r'^https?://(127\.0\.0\.1|localhost)(:\d+)?/', k['adress']):
            adress = k['adress']
        else:
            adress, fel = kanon_adress(k.get('adress'))
            if fel:
                return None, '%s: %s' % (k['namn'], fel)
        if k.get('roll') not in ('bransch', 'hantverk', 'ux'):
            return None, '%s: roll måste vara bransch, hantverk eller ux' % k['namn']
        sidor = k.get('sidor') or ['/']
        if not isinstance(sidor, list) or len(sidor) > MAX_SIDOR or not all(isinstance(s, str) and s.startswith('/') and len(s) < 200 and not any(c in s for c in '\\\n\r\t\x00 ') for s in sidor):
            return None, '%s: sidor är högst %d vägar som börjar med /' % (k['namn'], MAX_SIDOR)
        tillstand = {}
        for t in ('meny', 'hover', 'fokus'):
            v = k.get(t)
            if v is not None:
                if not isinstance(v, str) or not 0 < len(v) <= 200 or '\n' in v:
                    return None, '%s: %s måste vara en CSS-väljare' % (k['namn'], t)
                tillstand[t] = v
        kandidater.append({'namn': k['namn'], 'adress': adress, 'roll': k['roll'], 'varfor': str(k.get('varfor') or '')[:1000],
                           'sidor': list(dict.fromkeys(sidor)), 'tillstand': tillstand})
    return {'kandidater': kandidater, 'fragor': [str(f)[:500] for f in (u.get('fragor') or [])][:20], 'kompletterar': u.get('kompletterar')}, None


def ny_version(rot):
    """Nästa paket-vNN under underlag/<slug>/referenser/, skapad exklusivt."""
    rot = Path(rot)
    rot.mkdir(parents=True, exist_ok=True)
    n = max([int(p.name[7:]) for p in rot.glob('paket-v*') if re.fullmatch(r'paket-v\d{2,}', p.name)] or [0]) + 1
    while True:
        p = rot / ('paket-v%02d' % n)
        try:
            p.mkdir()
            return p
        except FileExistsError:
            n += 1


def ursprung(u):
    d = urllib.parse.urlsplit(u)
    return '%s://%s' % (d.scheme, d.netloc)


def blockerade_ursprung(rapport):
    """Ursprung som sajten försökte nå men som vakten stoppade: resursdomäner (bilder, typsnitt, stilar, skript, xhr).
    Spårare utesluts. Lokala ursprung tas med (provet)."""
    ut = []
    for vy in (rapport.get('vyer') or {}).values():
        for b in (vy.get('natverk') or {}).get('blockerade') or []:
            u = b.get('url') or ''
            try:
                d = urllib.parse.urlsplit(u)
            except ValueError:
                continue
            if d.scheme not in ('http', 'https') or not d.hostname:
                continue
            vard = d.hostname.lower()
            if any(vard == s or vard.endswith('.' + s) for s in SPARARE):
                continue
            if b.get('typ') in ('websocket', 'media', 'other'):
                continue
            o = '%s://%s' % (d.scheme, d.netloc)
            if o not in ut:
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


def observationer(rapport, ut):
    """Det som följer med i paketet per sida: status, titel, laddade bilder och typsnitt, kvarvarande blockeringar,
    tecken på kakdialog, misstänkt tomma bilder."""
    obs = {'vyer': {}, 'kvar_blockerade': [], 'begransningar': []}
    for vy, r in (rapport.get('vyer') or {}).items():
        nat = r.get('natverk') or {}
        laddade = nat.get('laddade') or {}
        obs['vyer'][vy] = {'status': r.get('status'), 'titel': r.get('titel'), 'h1': r.get('h1'), 'skarmar': r.get('skarmar'),
                           'bilder_laddade': int(laddade.get('image') or 0), 'typsnitt_laddade': int(laddade.get('font') or 0),
                           'stilar_laddade': int(laddade.get('stylesheet') or 0),
                           'blockerade': len(nat.get('blockerade') or []), 'fel': r.get('fel')}
        for b in nat.get('blockerade') or []:
            if b.get('typ') in ('image', 'font', 'stylesheet', 'script', 'xhr', 'fetch', 'document'):
                obs['kvar_blockerade'].append({'vy': vy, 'typ': b.get('typ'), 'url': (b.get('url') or '')[:200]})
        aria = Path(ut) / ('vy-%s-aria.txt' % vy)
        if aria.is_file():
            text = aria.read_text(encoding='utf-8', errors='replace').lower()
            if any(ord_ in text for ord_ in ('cookie', 'kakor', 'samtycke', 'consent', 'godkänn alla', 'accept all')):
                obs['begransningar'].append('vy %s: kakdialog syns troligen i bilderna (ordet cookie/kakor/samtycke i tillgänglighetsträdet)' % vy)
        for fil in ('vy-%s-forsta.png' % vy, 'vy-%s-hela.png' % vy):
            p = Path(ut) / fil
            if p.is_file() and p.stat().st_size < 6000:
                obs['begransningar'].append('%s är misstänkt tom (%d byte)' % (fil, p.stat().st_size))
        if r.get('status') not in (200, None):
            obs['begransningar'].append('vy %s: status %s' % (vy, r.get('status')))
        if r.get('fel'):
            obs['begransningar'].append('vy %s: %s' % (vy, str(r.get('fel'))[:200]))
    if obs['kvar_blockerade']:
        obs['begransningar'].append('%d resursanrop förblev blockerade (se kvar_blockerade)' % len(obs['kvar_blockerade']))
    return obs


def samla(slug, uppdrag, underlag=None, torr=False, lokalt_ok=False):
    """Kör uppdraget och skriver paketet. Ger (paketkatalog, resultat)."""
    underlag = Path(underlag or UNDERLAG)
    rot = underlag / slug / 'referenser'
    paket = ny_version(rot)
    res = {'schema': 1, 'slug': slug, 'version': paket.name, 'tid': nu(), 'kompletterar': uppdrag.get('kompletterar'),
           'uppdrag_sha256': hashlib.sha256(json.dumps(uppdrag, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
           'fragor': uppdrag['fragor'], 'kandidater': [], 'torr': torr}
    alla_ok = True
    for k in uppdrag['kandidater']:
        post = {'namn': k['namn'], 'adress': k['adress'], 'roll': k['roll'], 'varfor': k['varfor'], 'sidor': [], 'resursursprung': [], 'ok': False}
        katalog = paket / k['namn']
        katalog.mkdir()
        if torr:
            post['ok'] = True
            res['kandidater'].append(post)
            continue
        eget = ursprung(k['adress'])
        varden = {urllib.parse.urlsplit(eget).hostname}
        if lokalt_ok:
            varden.add('127.0.0.1')
        # pass 1 på första sidan: vilka resursursprung behöver sajten?
        forsta = k['adress'].rstrip('/') + k['sidor'][0] if k['sidor'][0] != '/' else k['adress']
        pass1 = katalog / '.pass1'
        rc1, rapport1, _ = kor_inspektera(forsta, pass1, [eget], {}, miljo_for(varden))
        resurser = blockerade_ursprung(rapport1)
        shutil.rmtree(pass1, ignore_errors=True)
        tillat = [eget] + resurser
        varden |= {urllib.parse.urlsplit(o).hostname for o in resurser}
        post['resursursprung'] = resurser
        # pass 2 på varje sida med resursursprungen tillåtna, bara för den här inspektionen
        for i, sida in enumerate(k['sidor']):
            adress = k['adress'] if sida == '/' else k['adress'].rstrip('/') + sida
            ut = katalog / sidnamn(sida)
            tillstand = k['tillstand'] if i == 0 else {}
            rc, rapport, utskrift = kor_inspektera(adress, ut, tillat, tillstand, miljo_for(varden))
            obs = observationer(rapport, ut) if rapport else {'vyer': {}, 'kvar_blockerade': [], 'begransningar': ['inspektionen gav ingen rapport: ' + utskrift[-300:]]}
            filer = sorted(str(p.relative_to(paket)) for p in ut.rglob('*') if p.is_file() and p.suffix in ('.png', '.txt', '.md', '.json'))
            sida_ok = rc == 0 and all((v.get('status') == 200) for v in obs['vyer'].values()) and bool(obs['vyer'])
            post['sidor'].append({'sida': sida, 'adress': adress, 'katalog': str(ut.relative_to(paket)), 'tillstand': tillstand, 'rc': rc, 'ok': sida_ok,
                                  'observationer': obs['vyer'], 'kvar_blockerade': obs['kvar_blockerade'], 'begransningar': obs['begransningar'], 'filer': filer})
        post['ok'] = bool(post['sidor']) and post['sidor'][0]['ok']
        alla_ok = alla_ok and post['ok']
        res['kandidater'].append(post)
    res['alla_ok'] = alla_ok
    (paket / 'PAKET.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    rader = ['# Referenspaket %s · %s · %s' % (paket.name, slug, res['tid']), '']
    if uppdrag.get('kompletterar'):
        rader.append('Kompletterar %s. ' % uppdrag['kompletterar'])
    rader += ['Fångat med kontroller/referens.py: två pass per kandidat (eget ursprung, sedan sajtens resursursprung tillåtna bara för',
              'inspektionen), läsande, publika adresser, färsk webbläsarprofil. Peka ut bilder i REFERENSER.md som',
              '`Bildval: referenser/%s/<kandidat>/<sida>/<fil>.png — … — Fråga: …`.' % paket.name, '']
    for post in res['kandidater']:
        rader += ['## %s · %s · %s' % (post['namn'], post['roll'], post['adress']), '', post['varfor'] or '(ingen motivering)', '']
        if not post['sidor']:
            rader.append('- torrkörning: inget fångat' if torr else '- inget fångat')
        for s in post['sidor']:
            vy = s['observationer']
            rader.append('- %s (%s): %s · status %s · bilder laddade %s · typsnitt %s · blockerade kvar %d · filer %d' % (
                s['sida'], s['katalog'], 'ok' if s['ok'] else 'brister', ','.join(str(v.get('status')) for v in vy.values()),
                '/'.join(str(v.get('bilder_laddade')) for v in vy.values()), '/'.join(str(v.get('typsnitt_laddade')) for v in vy.values()),
                len(s['kvar_blockerade']), len(s['filer'])))
            for b in s['begransningar']:
                rader.append('  - begränsning: ' + b)
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
    p.add_argument('--tillat-lokalt', action='store_true', help=argparse.SUPPRESS)  # bara rökprovet: lokala kandidater
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
    underlag = Path(a.underlag or UNDERLAG)
    fil = Path(a.uppdrag) if a.uppdrag else underlag / a.slug / 'REFERENSUPPDRAG.json'
    if not fil.is_absolute():
        fil = ROOT / fil
    try:
        verklig = fil.resolve()
    except (OSError, RuntimeError):
        verklig = None
    rot = (underlag / a.slug).resolve()
    if verklig is None or (verklig != rot and rot not in verklig.parents):
        print('uppdraget måste ligga under underlag/%s/' % a.slug, file=sys.stderr)
        return 2
    uppdrag, fel = las_uppdrag(verklig, a.slug, lokalt_ok=a.tillat_lokalt)
    if fel:
        print('uppdraget vägras: %s' % fel, file=sys.stderr)
        return 2
    paket, res = samla(a.slug, uppdrag, underlag, torr=a.torr, lokalt_ok=a.tillat_lokalt)
    rel = paket.relative_to(ROOT) if str(paket).startswith(str(ROOT) + os.sep) else paket
    print('Referenspaket %s: %d kandidater, %s. Översikt: %s' % (rel, len(res['kandidater']), 'allt fångat' if res['alla_ok'] else 'brister finns (PAKET.json)', rel / 'PAKET.md'))
    for post in res['kandidater']:
        print('- %s (%s): %s' % (post['namn'], post['roll'], 'ok' if post['ok'] else 'brister'))
    return 0 if res['alla_ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
