#!/usr/bin/env python3
"""Hämtar en enstaka extern sida (en tidningsartikel, en arkiverad sida på web.archive.org, en katalogpost) och sparar
den som <ut>.html och <ut>.txt i samma textformat som hamta_sajt.py: källa, metadata, text med rubrikmarkeringar,
länkar, kontaktvägar, bilder och JSON-LD. Bara GET, robots.txt respekteras.

  .venv/bin/python kontroller/sida_till_text.py <url> underlag/<slug>/kalla/extern/<namn>
"""
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)
from hamta_sajt import UA_NAMN, Sida, avkoda, hamta, las_robots, textfil  # noqa: E402


def sida_till_text(url, ut):
    s = urllib.parse.urlsplit(url)
    if s.scheme not in ('http', 'https'):
        raise SystemExit('väntade en http(s)-adress')
    rp, lage = las_robots(f'{s.scheme}://{s.netloc}')
    if not rp.can_fetch(UA_NAMN, url):
        raise SystemExit(f'nekad av robots.txt ({lage}): {url}')
    svar = hamta(url)
    if svar['status'] != 200:
        raise SystemExit(f"svarade {svar['status'] or svar.get('fel')}: {url}")
    slut = svar['url']
    p = Sida()
    p.feed(avkoda(svar))
    lankar, kontakter = [], []
    for href, ltext in p.lankar:
        if href.lower().startswith(('tel:', 'mailto:', 'sms:')):
            kontakter.append(urllib.parse.unquote(href))
        elif urllib.parse.urlsplit(urllib.parse.urljoin(slut, href)).scheme in ('http', 'https'):
            lankar.append((urllib.parse.urldefrag(urllib.parse.urljoin(slut, href))[0], ltext))
    bilder = [(urllib.parse.urljoin(slut, src.strip()), alt, kalla) for src, alt, kalla in p.bilder
              if src and not src.strip().startswith(('data:', '#'))]
    ut = Path(ut)
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.with_suffix('.html').write_bytes(svar['data'])
    text = p.ren_text()
    ut.with_suffix('.txt').write_text(textfil(slut, svar, p, text, lankar, kontakter, bilder), encoding='utf-8')
    return {'ut': str(ut.with_suffix('.txt')), 'ord': len(text.split()), 'titel': ' '.join(p.titel.split())}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    krav_vag(sys.argv[2], "utkatalogen")
    print(sida_till_text(sys.argv[1], sys.argv[2]))
