#!/usr/bin/env python3
"""extern_granskare.py — en extern granskares väg in i arbetsytans meddelandebuss (ägarens uppdrag 2026-10-09 om den
kompletta arbetsplatsen, punkt 5; kunskap/arbetsyta.md, Extern granskare).

Granskaren (till exempel Codex) skriver aldrig i skaparens filer och når inte dashboarden själv: den läser ett
granskningspaket, lämnar sina fynd som JSON enligt fynd-schema.json, och det här skriptet postar dem med granskarens egen
nyckel. Avsändaren är nyckelns namn (dashboard/samverkan.py), aldrig texten. Återkopplingen (svar, ägarens beslut över
fynden) hämtas på samma sätt och kan ges tillbaka till granskaren.

    extern_granskare.py nyckel <namn>                          skapar granskarnyckeln (0600) om den saknas; skrivs aldrig ut
    extern_granskare.py paket <namn> <kund> <katalog>          granskningspaketet: AGENTS.md, fynd-schema.json, underlag.json, bilder/
    extern_granskare.py posta <namn> <kund> <fynd.json>        postar fynden; samma fynd två gånger blir samma meddelande
    extern_granskare.py aterkoppling <namn> <kund>             svaren och ägarens beslut över granskarens meddelanden

--bas http://127.0.0.1:4771 är dashboarden (förvald). Codex körs av ägaren, skrivskyddat, i paketets katalog (förberett,
inte prövat av motorn; se kunskap/arbetsyta.md):

    codex exec --ignore-user-config -s read-only -C <katalog> --output-schema <katalog>/fynd-schema.json \\
        -o <katalog>/fynd.json "Granska kandidaterna enligt AGENTS.md och svara enligt schemat."
    extern_granskare.py posta codex <kund> <katalog>/fynd.json
"""
import argparse
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

NAMN = re.compile(r'^[a-z][a-z0-9-]{1,30}$')
KUND = re.compile(r'^[a-z0-9-]{2,60}$')
BAS = 'http://127.0.0.1:4771'
SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['fynd'],
    'properties': {'fynd': {'type': 'array', 'items': {
        'type': 'object', 'additionalProperties': False, 'required': ['syfte', 'till', 'kandidat', 'version', 'text', 'belagg'],
        'properties': {
            'syfte': {'type': 'string', 'enum': ['granskningsfynd', 'forslag', 'fraga', 'andringsinstruktion']},
            'till': {'type': 'string', 'enum': ['agare', 'utforande']},
            'kandidat': {'type': 'string', 'pattern': '^k[0-9]{2}$'},
            'version': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
            'text': {'type': 'string', 'minLength': 1, 'maxLength': 8000},
            'belagg': {'type': 'array', 'items': {'type': 'string', 'maxLength': 400}, 'maxItems': 12}}}}}}
AGENTS = """# Uppdrag: extern granskare i Nortropics arbetsyta

Du granskar kandidaterna i det här paketet åt ägaren. Du läser bara; du ändrar inga filer och når ingen tjänst.

- Underlaget står i underlag.json: kunden, körningen, kandidaterna med neutrala etiketter, deras versioner och bilderna
  i bilder/<kandidat>/. Gäller bara den version som står där.
- Lämna fynd som JSON enligt fynd-schema.json. Ett granskningsfynd har belägg: vilken bild, vilken del, mått eller
  kontrast, så att någon annan kan kontrollera det. Utan belägg, skriv ett förslag eller en fråga.
- till: agare, utom när underlag.json visar ett mandat från ägaren för kandidaten; då får du inom mandatets omfattning
  också skicka förslag, granskningsfynd och begäran om rättelse (syfte andringsinstruktion) till kandidatens utförare
  (till utforande), som hanterar dem inom sitt eget uppdrag.
- Inget du skriver är ägarens ord eller ett godkännande. Upprepa inte samma fynd; skicka bara det som tillför något nytt.
"""


def nyckelkatalog():
    return Path(os.environ.get('NWP_GRANSKARE_NYCKLAR') or Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'granskare')


def skapa_nyckel(namn):
    if not NAMN.fullmatch(namn):
        raise SystemExit('ogiltigt namn: %s' % namn)
    k = nyckelkatalog()
    k.mkdir(parents=True, exist_ok=True)
    os.chmod(k, 0o700)
    f = k / ('%s.nyckel' % namn)
    if f.is_symlink():
        raise SystemExit('%s är en länk' % f)
    if not f.exists():
        fd = os.open(str(f), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as fh:
            fh.write(secrets.token_urlsafe(32) + '\n')
    return f


def nyckel(namn):
    f = nyckelkatalog() / ('%s.nyckel' % namn)
    try:
        return f.read_text(encoding='utf-8').strip()
    except OSError:
        raise SystemExit('ingen granskarnyckel för %s (%s); skapa den med: extern_granskare.py nyckel %s' % (namn, f, namn))


def anrop(bas, namn, metod, vag, data=None, binart=False):
    """Ett anrop till dashboardens externa väg, med granskarnyckeln och utan Origin (ingen webbläsare)."""
    req = urllib.request.Request(bas.rstrip('/') + vag, method=metod, data=json.dumps(data).encode() if data is not None else None,
                                 headers={'Authorization': 'Bearer ' + nyckel(namn), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            kropp = r.read()
            return kropp if binart else json.loads(kropp or b'{}')
    except urllib.error.HTTPError as e:
        try:
            fel = json.loads(e.read() or b'{}').get('fel')
        except ValueError:
            fel = None
        raise RuntimeError('HTTP %d: %s' % (e.code, fel or e.reason))


def paket(bas, namn, kund, katalog):
    """Granskningspaketet: underlaget, bilderna, schemat och uppdraget. Ingen nyckel och inga andra filer i paketet."""
    d = Path(katalog)
    d.mkdir(parents=True, exist_ok=True)
    if (d / '.codex').exists():
        raise SystemExit('%s har en .codex/; paketet får inte bära egna Codex-inställningar' % d)
    u = anrop(bas, namn, 'GET', '/api/extern/%s/underlag' % kund)
    bilder = {}
    for k in u.get('kandidater') or []:
        for bredd, rel in (k.get('bilder') or {}).items():
            if not rel:
                continue
            mal = d / 'bilder' / k['id'] / ('%s.png' % bredd)
            mal.parent.mkdir(parents=True, exist_ok=True)
            mal.write_bytes(anrop(bas, namn, 'GET', '/api/extern/%s/bild?fil=%s' % (kund, urllib.parse.quote(rel)), binart=True))
            bilder.setdefault(k['id'], {})[bredd] = str(mal.relative_to(d))
    u['paketets_bilder'] = bilder
    (d / 'underlag.json').write_text(json.dumps(u, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (d / 'fynd-schema.json').write_text(json.dumps(SCHEMA, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (d / 'AGENTS.md').write_text(AGENTS, encoding='utf-8')
    return {'katalog': str(d), 'kandidater': [k['id'] for k in u.get('kandidater') or []], 'bilder': sum(len(v) for v in bilder.values()),
            'mandat': len(u.get('mandat') or [])}


def posta(bas, namn, kund, fil):
    """Fynden ur granskarens svar (fynd-schema.json), ett i taget. Ett fynd som nekas står med skälet; resten postas."""
    d = json.loads(Path(fil).read_text(encoding='utf-8'))
    fynd = d.get('fynd') if isinstance(d, dict) else None
    if not isinstance(fynd, list):
        raise SystemExit('%s följer inte fynd-schema.json (fältet fynd saknas)' % fil)
    ut = []
    for f in fynd:
        try:
            ut.append(dict(anrop(bas, namn, 'POST', '/api/extern/%s/fynd' % kund, f), ok=True))
        except RuntimeError as e:
            ut.append({'ok': False, 'fel': str(e), 'fynd': (f.get('text') or '')[:80]})
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='extern_granskare', description=__doc__.split('\n\n')[0])
    p.add_argument('--bas', default=os.environ.get('NWP_DASHBOARD_BAS') or BAS)
    sub = p.add_subparsers(dest='kommando', required=True)
    n = sub.add_parser('nyckel')
    n.add_argument('namn')
    for k_ in ('paket', 'posta', 'aterkoppling'):
        s = sub.add_parser(k_)
        s.add_argument('namn')
        s.add_argument('kund')
        if k_ == 'paket':
            s.add_argument('katalog')
        if k_ == 'posta':
            s.add_argument('fil')
    a = p.parse_args(argv)
    if a.kommando == 'nyckel':
        print('granskarnyckeln finns i %s (0600); den skrivs aldrig ut' % skapa_nyckel(a.namn))
        return 0
    if not NAMN.fullmatch(a.namn) or not KUND.fullmatch(a.kund):
        print('ogiltigt namn eller kund')
        return 2
    try:
        if a.kommando == 'paket':
            print(json.dumps(paket(a.bas, a.namn, a.kund, a.katalog), ensure_ascii=False))
        elif a.kommando == 'posta':
            ut = posta(a.bas, a.namn, a.kund, a.fil)
            print(json.dumps(ut, ensure_ascii=False, indent=1))
            return 0 if all(x['ok'] for x in ut) else 1
        else:
            print(json.dumps(anrop(a.bas, a.namn, 'GET', '/api/extern/%s/aterkoppling' % a.kund), ensure_ascii=False, indent=1))
    except RuntimeError as e:
        print('fel: %s' % e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
