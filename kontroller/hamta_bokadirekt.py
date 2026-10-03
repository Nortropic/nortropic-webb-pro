#!/usr/bin/env python3
"""Hämtar en verksamhets Bokadirekt-profil till underlag/<slug>/kalla/extern/ i steg 1.

Profilsidan bär hela salongens tillstånd i window.__PRELOADED_STATE__ (prislistor, personal, öppettider, kontakt,
avbokningsvillkor), och omdömena finns i Bokadirekts API /api/places/getReviews/<id>. Bokadirekts robots.txt tillåter
allt (Allow: /, läst 2026-10-03). Bara GET, en sekund mellan omdömessidorna.

  .venv/bin/python kontroller/hamta_bokadirekt.py <slug> https://www.bokadirekt.se/places/<namn>-<id>

Skriver:
  bokadirekt.html            profilsidan som den hämtades
  bokadirekt-state.json      platsens tillstånd, utan personalens kontaktuppgifter och lösenordsfält
  bokadirekt-tjanster.txt    varje tjänst med pris och tid per prislista, vem som gör den, beskrivningen ordagrant
  bokadirekt-omdomen.txt     alla omdömen med text: datum, betyg, namn, frisör, tjänst, texten ordagrant
"""
import argparse
import datetime
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

ROOT = Path(__file__).resolve().parent.parent
UA = 'Mozilla/5.0 (compatible; nortropic-webb-pro/1; +https://github.com/Nortropic/nortropic-webb-pro)'
STATE = re.compile(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});?\s*(?:window\.|</script>)', re.S)
API = 'https://www.bokadirekt.se/api/places/getReviews/%s?page=%d&limit=100&mp-reviews=true&rating=0'


def hamta(url, timeout=30):
    import hamta_sajt as hs  # samma hämtare som resten av repot: validerad publik adress, bara bokadirekt.se (revisionen, F5)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'sv-SE,sv;q=0.9'})
    with hs.oppnare(egen='bokadirekt.se').open(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


def las_state(html):
    """Platsen (place) ur profilsidans __PRELOADED_STATE__. Personalens kontakt- och lösenordsfält tas bort: bygget
    behöver dem inte (GDPR, bara det som behövs)."""
    m = STATE.search(html)
    if not m:
        raise ValueError('window.__PRELOADED_STATE__ saknas på sidan; är det en profilsida (/places/<namn>-<id>)?')
    s = m.group(1)
    try:
        d = json.loads(s)
    except ValueError:
        d = json.loads(s[:s.rfind('}') + 1])
    place = d.get('place') or {}
    for e in place.get('employees') or []:
        e.pop('password', None)
        e.pop('contact', None)
    return place


def en_rad(s):
    return re.sub(r'\s*[\r\n]+\s*', ' / ', str(s or '').strip())


def kr_min(pris, sek):
    return '%s kr / %d min' % (pris, int(sek or 0) // 60) if pris is not None else '–'


def tjanster_text(place, url, datum):
    """En rad per tjänst: namn, pris och tid per prislista (prislistornas namn är personalen som har dem), vem som
    gör tjänsten och beskrivningen ordagrant."""
    listor = {}
    for e in place.get('employees') or []:
        a = e.get('about') or {}
        listor.setdefault(a.get('priceListId'), []).append(a.get('name') or '?')
    per_tjanst = {}
    for e in place.get('employees') or []:
        for sid in e.get('services') or []:
            sid = sid if isinstance(sid, (int, str)) else (sid or {}).get('id')
            per_tjanst.setdefault(sid, []).append((e.get('about') or {}).get('name') or '?')
    ordning = [k for k in listor if k]
    rader = ['# Bokadirekts prislista, hämtad %s ur %s' % (datum, url),
             '# Prislistor: ' + '; '.join('%d = %s' % (i + 1, ', '.join(listor[k])) for i, k in enumerate(ordning)),
             '# tjänst | ' + ' | '.join('prislista %d' % (i + 1) for i in range(len(ordning))) + ' | vem | beskrivning (ordagrant, / = radbrytning)']
    for kat in place.get('services') or []:
        if not isinstance(kat, dict):
            continue
        rader += ['', '## ' + str(kat.get('name') or '').strip()]
        for t in kat.get('services') or []:
            pt = t.get('priceType') or {}
            pr, du = pt.get('prices') or {}, pt.get('durations') or {}
            if pr:
                kolumner = [kr_min(pr.get(k), du.get(k)) for k in ordning]
            else:
                kolumner = [kr_min(t.get('price'), t.get('duration'))] + ['–'] * (len(ordning) - 1)
            besk = en_rad((t.get('about') or {}).get('description'))
            rader.append('- %s | %s | %s | %s' % (str(t.get('name') or '').strip(), ' | '.join(kolumner),
                                                  ', '.join(per_tjanst.get(t.get('id'), [])), besk))
    a = place.get('about') or {}
    book = a.get('book') or {}
    if book.get('cancel'):
        rader += ['', '# Avbokning senast %d timmar före (about.book.cancel %s minuter)' % (book['cancel'] // 60, book['cancel'])]
    return '\n'.join(rader) + '\n'


def omdomen_text(poster, url, datum):
    rader = ['# Bokadirekts omdömen med text, hämtade %s ur %s' % (datum, url),
             '# datum | betyg | namn | frisör | tjänst | text (ordagrant, / = radbrytning)']
    for r in poster:
        text = ((r.get('review') or {}).get('text') or '').strip()
        if not text:
            continue
        sub = r.get('subject') or {}
        emp = (sub.get('employee') or {}).get('name', '') if isinstance(sub.get('employee'), dict) else ''
        svc = (sub.get('service') or {}).get('name', '') if isinstance(sub.get('service'), dict) else ''
        rader.append('%s | %s | %s | %s | %s | %s' % (str(r.get('createdAt', ''))[:10], (r.get('review') or {}).get('score'),
                                                     (r.get('author') or {}).get('name', ''), emp, svc, en_rad(text)))
    return '\n'.join(rader) + '\n'


def hamta_omdomen(place_id, max_sidor=40, paus=1.0):
    alla = []
    for sida in range(1, max_sidor + 1):
        d = json.loads(hamta(API % (place_id, sida)))
        items = d.get('items') if isinstance(d, dict) else None
        if not items:
            break
        alla.extend(items)
        if not d.get('nextPage'):
            break
        time.sleep(paus)
    return alla


def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('url', help='profilsidan, https://www.bokadirekt.se/places/<namn>-<id>')
    p.add_argument('--max-sidor', type=int, default=40, help='omdömessidor om 100 (standard 40)')
    a = p.parse_args()
    krav_slug(a.slug)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug):
        sys.exit('ogiltig slug')
    if not re.match(r'https://(www\.)?bokadirekt\.se/places/', a.url):
        sys.exit('väntade en profilsida: https://www.bokadirekt.se/places/<namn>-<id>')
    ut = ROOT / 'underlag' / a.slug / 'kalla' / 'extern'
    krav_vag(ut, 'utkatalogen')  # före mkdir: en symlänk kalla/ → annan kund skulle annars få katalogen och filerna (omgång elva, F1)
    ut.mkdir(parents=True, exist_ok=True)
    krav_vag(ut, 'utkatalogen')  # efter: en planterad symlänk inne i katalogen får inte leda skrivningen ut
    datum = datetime.date.today().isoformat()
    html = hamta(a.url)
    (ut / 'bokadirekt.html').write_text(html, encoding='utf-8')
    place = las_state(html)
    (ut / 'bokadirekt-state.json').write_text(json.dumps(place, ensure_ascii=False, indent=1), encoding='utf-8')
    (ut / 'bokadirekt-tjanster.txt').write_text(tjanster_text(place, a.url, datum), encoding='utf-8')
    poster = hamta_omdomen(place.get('id'), a.max_sidor) if place.get('id') else []
    api = API.split('?')[0] % place.get('id')
    (ut / 'bokadirekt-omdomen.txt').write_text(omdomen_text(poster, api, datum), encoding='utf-8')
    stats = (place.get('reviews') or {}).get('stats') or {}
    print('%s: %d tjänster, %d personal, %d omdömen hämtade (%s betyg totalt, snitt %s) → %s' % (
        (place.get('about') or {}).get('name'), sum(len(k.get('services') or []) for k in place.get('services') or [] if isinstance(k, dict)),
        len(place.get('employees') or []), len(poster), stats.get('count'),
        round(stats['score'], 2) if stats.get('score') else '?', ut.relative_to(ROOT)))


if __name__ == '__main__':
    main()
