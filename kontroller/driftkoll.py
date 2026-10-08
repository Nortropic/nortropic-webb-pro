#!/usr/bin/env python3
"""driftkoll.py — läsande kontroll av en driftsatt sajt med riktiga HTTP-svar (kunskap/lansering.md, "Förhandsvisning,
produktion och skydd"; Codex via ägaren 2026-10-05: välj skyddsmetod uttryckligen och kontrollera de verkliga svaren).

    .venv/bin/python kontroller/driftkoll.py <adress> --lage forhandsvisning|produktion [--bypass-fil FIL] [--formular]

forhandsvisning: utan förbikoppling svarar sajten 302 eller 401 mot Vercels inloggning (skyddet); med förbikopplingen
(hemligheten läses ur --bypass-fil och skrivs aldrig ut) svarar startsidan 200 med `X-Robots-Tag: noindex`.
produktion: startsidan svarar 200 utan noindex (varken huvud eller meta), robots.txt tillåter, sitemap.xml finns.
Båda: säkerhetshuvudena ur kundrepots vercel.json. --formular prövar funktionen /api/forfragan/: honeypot (303 till
/tack/), ofullständigt (422 med bevarad text), en bild över 4 MB och en begäran över 4,4 MB (413 med
bildens besked, X-Forfragan for-stor), annan Origin (403), och i förhandsvisningen ett giltigt inskick
(303 till /tack/ med X-Forfragan demo: Resends variabler gäller bara produktionen, och ett riktigt mejl ur en
förhandsvisning vore ett fel). Ett giltigt inskick skickas aldrig till en produktion: det vore ett riktigt mejl.
Slutkod 0 när allt håller, 1 annars, 2 vid fel i anropet.
"""
import argparse
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SAKERHET = ('x-content-type-options', 'referrer-policy', 'x-frame-options', 'strict-transport-security')


class IngenOmdirigering(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def hamta(url, metod='GET', huvuden=None, kropp=None):
    """(status, huvuden i gemener, kropp) utan att följa omdirigeringar och utan proxyvariabler."""
    opp = urllib.request.build_opener(urllib.request.ProxyHandler({}), IngenOmdirigering)
    req = urllib.request.Request(url, data=kropp, method=metod, headers={'User-Agent': 'nortropic-driftkoll', **(huvuden or {})})
    try:
        with opp.open(req, timeout=60) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(400_000)
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read(20_000) if e.fp else b''


def multipart(falt, fil=None):
    grans = uuid.uuid4().hex
    delar = []
    for k, v in falt.items():
        delar.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (grans, k, v)).encode())
    if fil:
        namn, data, typ = fil
        delar.append(('--%s\r\nContent-Disposition: form-data; name="bild"; filename="%s"\r\nContent-Type: %s\r\n\r\n' % (grans, namn, typ)).encode() + data + b'\r\n')
    delar.append(('--%s--\r\n' % grans).encode())
    return b''.join(delar), 'multipart/form-data; boundary=%s' % grans


def kontroll(adress, lage, bypass=None, formular=False):
    adress = adress.rstrip('/')
    ut = []

    def P(ok, text):
        ut.append((bool(ok), text))
    forbi = {'x-vercel-protection-bypass': bypass} if bypass else {}
    if lage == 'forhandsvisning':
        s, h, _ = hamta(adress + '/')
        P(s in (302, 401) and ('vercel.com/sso' in h.get('location', '') or s == 401),
          'skyddet: utan förbikoppling %d %s' % (s, h.get('location', '')[:60]))
        if not bypass:
            P(False, 'ingen förbikoppling (--bypass-fil): sidan och formuläret prövas inte')
            return ut
    s, h, kropp = hamta(adress + '/', huvuden=forbi)
    P(s == 200, 'startsidan: %d' % s)
    noindex_huvud = 'noindex' in h.get('x-robots-tag', '').lower()
    noindex_meta = bool(re.search(rb'<meta[^>]+name=["\']robots["\'][^>]+noindex', kropp, re.I))
    if lage == 'forhandsvisning':
        P(noindex_huvud, 'X-Robots-Tag i förhandsvisningen: %s' % (h.get('x-robots-tag') or 'saknas'))
    else:
        P(not noindex_huvud and not noindex_meta, 'ingen noindex i produktionen (huvud %s, meta %s)' % (noindex_huvud, noindex_meta))
        rs, _, rt = hamta(adress + '/robots.txt')
        P(rs == 200 and not re.search(rb'(?im)^Disallow:\s*/\s*$', rt), 'robots.txt: %d och tillåter' % rs)
        ss, _, _ = hamta(adress + '/sitemap.xml')
        P(ss == 200, 'sitemap.xml: %d' % ss)
    saknas = [x for x in SAKERHET if x not in h]
    P(not saknas, 'säkerhetshuvuden: %s' % ('alla' if not saknas else 'saknar ' + ', '.join(saknas)))
    if formular:
        mal = adress + '/api/forfragan/'
        origin = {'Origin': adress}
        bas = {'namn': 'Driftkoll', 'telefon': '0700000000', 'meddelande': 'Prov av formuläret', 'fylltid': '9000'}
        fall = [('honeypot', dict(bas, webbplats='spam'), None, origin, 303, '/tack/', None),
                ('ofullständigt', dict(bas, telefon=''), None, origin, 422, None, 'ofullstandig'),
                ('bild på 4,2 MB', bas, ('stor.jpg', os.urandom(4_200_000), 'image/jpeg'), origin, 413, None, 'for-stor'),
                ('begäran över 4,4 MB', bas, ('storre.jpg', os.urandom(4_450_000), 'image/jpeg'), origin, 413, None, 'for-stor'),
                ('annan Origin', bas, None, {'Origin': 'https://angripare.exempel'}, 403, None, None)]
        if lage == 'forhandsvisning':
            fall.append(('giltigt (demo)', bas, None, origin, 303, '/tack/', 'demo'))
        for namn, falt, fil, huv, vantad, plats, utfall in fall:
            data, typ = multipart(falt, fil)
            s, h, kropp = hamta(mal, 'POST', {**forbi, **huv, 'Content-Type': typ}, data)
            ok = s == vantad and (plats is None or h.get('location', '').startswith(plats)) and (utfall is None or h.get('x-forfragan') == utfall)
            if vantad in (422, 413):
                ok = ok and 'text/html' in h.get('content-type','') and h.get('cache-control') == 'no-store' and 'noindex' in h.get('x-robots-tag','')
                if namn != 'begäran över 4,4 MB':
                    import html
                    ok = ok and all(html.escape(falt[k], quote=True).encode() in kropp for k in ('namn','telefon','meddelande'))
            P(ok, 'formuläret, %s: %d %s %s' % (namn, s, h.get('location', ''), h.get('x-forfragan', '')))
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='driftkoll', description=__doc__.split('\n\n')[0])
    p.add_argument('adress')
    p.add_argument('--lage', required=True, choices=('forhandsvisning', 'produktion'))
    p.add_argument('--bypass-fil')
    p.add_argument('--formular', action='store_true')
    a = p.parse_args(argv)
    if not re.match(r'^https://[a-z0-9.-]+(/|$)', a.adress):
        print('adressen ska vara https://värd/', file=sys.stderr)
        return 2
    bypass = Path(a.bypass_fil).read_text(encoding='utf-8').strip() if a.bypass_fil else None
    ut = kontroll(a.adress, a.lage, bypass, a.formular)
    for ok, text in ut:
        print('%s %s' % ('ok ' if ok else 'FEL', text))
    return 0 if all(ok for ok, _ in ut) else 1


if __name__ == '__main__':
    sys.exit(main())
