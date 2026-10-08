#!/usr/bin/env python3
"""profilblad.py — klistringsfärdigt profilblad för Google-företagsprofilen ur underlag/<slug>/VERKSAMHET.json (rapportens
punkt 14 i bygg-sajt; fälten enligt kunskap/lokal-synlighet.md, Korrekta uppgifter). Avvikelserna står först. En fiktiv
verksamhet, eller en räckvidd utan lokal förankring, får inget blad (lokal-synlighet.md, Tillämplighet först). Läser bara
verksamhetsuppgifterna: skapar ingen profil och gör inga anrop.

    .venv/bin/python kontroller/profilblad.py <slug> [--beskrivning FIL] [--avvikelser FIL] [--bilder FIL] [--underlag KATALOG]

Slutkod 0 med bladet på stdout; 3 när inget blad gäller (skälet på stdout); 2 vid oläsbara uppgifter.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
DAGAR = {'man': 'Måndag', 'tis': 'Tisdag', 'ons': 'Onsdag', 'tor': 'Torsdag', 'fre': 'Fredag', 'lor': 'Lördag', 'son': 'Söndag'}
BESKRIVNING_MAX, BESKRIVNING_FORST = 750, 250


def tillamplig(v):
    """None när bladet gäller, annars skälet (lokal-synlighet.md, Tillämplighet först)."""
    if v.get('fiktiv') is not False:
        return 'fiktiv verksamhet: ingen verklig profil, inga citationer (kunskap/lokal-synlighet.md, Tillämplighet först)'
    rv = v.get('rackvidd') or {}
    if rv.get('typ') not in ('lokal', 'regional') and not v.get('adress'):
        return 'räckvidden %s utan lokal förankring: profilbladet gäller lokal eller regional räckvidd' % (rv.get('typ') or '?')
    return None


def blad(v, beskrivning='', avvikelser=(), bilder=()):
    """Bladet som Markdown, eller None när inget blad gäller."""
    if tillamplig(v):
        return None
    kat = [k for k in v.get('kategorier') or [] if isinstance(k, str) and k.strip()]
    adr = v.get('adress') or {}
    orter = [o for o in (v.get('rackvidd') or {}).get('orter') or [] if isinstance(o, str)]
    tel = [k.get('varde') for k in v.get('kontaktvagar') or [] if isinstance(k, dict) and k.get('typ') == 'telefon' and k.get('varde')]
    webb = (v.get('webb') or {}).get('doman') if isinstance(v.get('webb'), dict) else None
    tider = '; '.join('%s %s–%s' % (DAGAR.get(o.get('dag'), o.get('dag')), o.get('oppnar'), o.get('stanger')) for o in v.get('oppettider') or [] if isinstance(o, dict))
    rader = ['# Profilblad för Google-företagsprofilen: %s' % v['namn'], '',
             'Klistra in fält för fält i business.google.com. Avvikelserna först: rätta dem i profilen, katalogerna eller på sajten',
             'innan resten förs in (byggstandarden 7.4: namn, adress och telefon identiska med sajten).', '', '## Avvikelser först', '']
    rader += ['- ' + a for a in avvikelser if a.strip()] or ['- Inga kända avvikelser mellan sajt, profil och kataloger. Kontrollera namn, adress och telefon mot sajten.']
    rader += ['', '## Fält', '', '| Fält | Värde |', '|---|---|', '| Namn | %s |' % v['namn'],
              '| Primär kategori | %s |' % (kat[0] if kat else '(saknas: ange den exakta branschkategorin)'),
              '| Sekundära kategorier | %s |' % (', '.join(kat[1:]) if len(kat) > 1 else 'inga'),
              '| Adress | %s |' % (('%s, %s %s' % (adr.get('gata'), adr.get('postnummer'), adr.get('ort'))) if adr.get('publik') else 'dold: serviceområde utan gatuadress'),
              '| Serviceområde | %s |' % (', '.join(orter) if orter else (adr.get('ort') or '(saknas)')),
              '| Telefon | %s |' % (tel[0] if tel else '(saknas: samma nummer som på sajten, inget spårningsnummer)'),
              '| Webbplats | %s |' % (('https://%s/' % webb) if webb else '(sajtens adress när den är lanserad)'),
              '| Öppettider | %s |' % (tider or '(saknas: beställ av verksamheten; jour bara om bemannad)'),
              '| Tjänster | %s |' % ', '.join(t for t in v.get('tjanster') or [] if isinstance(t, str))]
    b = ' '.join(str(beskrivning or '').split())
    rader += ['', '## Beskrivning (högst %d tecken; de första %d bär budskapet)' % (BESKRIVNING_MAX, BESKRIVNING_FORST), '']
    if b:
        rader.append(b[:BESKRIVNING_MAX])
        if len(b) > BESKRIVNING_MAX:
            rader.append('')
            rader.append('(förkortad: %d tecken i underlaget, %d får plats; skriv om så att slutet inte klipps)' % (len(b), BESKRIVNING_MAX))
    else:
        rader.append('(skriv ur briefen: vad verksamheten gör, för vem och var; inga nyckelordslistor)')
    rader += ['', '## Bilder att ladda upp', '']
    rader += ['- ' + x for x in bilder if x.strip()] or ['- logotyp, omslag, personer, lokal eller fordon, utfört arbete: verkliga foton med rättigheter (kunskap/bild.md)']
    return '\n'.join(rader) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(prog='profilblad', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--beskrivning', help='fil med beskrivningen ur briefen')
    p.add_argument('--avvikelser', help='fil med en avvikelse per rad (sajt, profil, kataloger)')
    p.add_argument('--bilder', help='fil med en bild per rad att ladda upp')
    p.add_argument('--underlag', default=None, help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug):
        print('ogiltig slug'); return 2
    try:
        v = json.loads((Path(a.underlag or UNDERLAG) / a.slug / 'VERKSAMHET.json').read_text(encoding='utf-8'))
        if not isinstance(v, dict) or not isinstance(v.get('namn'), str):
            raise ValueError('VERKSAMHET.json saknar namn')
    except (OSError, ValueError) as e:
        print('verksamhetsuppgifterna kunde inte läsas: %s' % e); return 2
    las = lambda f: Path(f).read_text(encoding='utf-8') if f else ''  # noqa: E731
    rader = lambda f: [r.strip() for r in las(f).splitlines() if r.strip()]  # noqa: E731
    ut = blad(v, las(a.beskrivning), rader(a.avvikelser), rader(a.bilder))
    if ut is None:
        print('inget profilblad: ' + tillamplig(v)); return 3
    print(ut, end=''); return 0


if __name__ == '__main__':
    sys.exit(main())
