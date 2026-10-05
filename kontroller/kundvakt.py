#!/usr/bin/env python3
"""kundvakt.py — PreToolUse-krok för skapandeflödets sessioner: ett anrop till en extern designtjänst (Refero, Mobbin,
Trybloom) får aldrig bära kundens namn, orter, gata, webbadress, e-post eller nummer (BESLUT.md 2026-10-05, punkt 4;
ägarens ord 2026-10-05 18:15Z: skillsen och MCP:erna ska användas, och kundens uppgifter skyddas som förut).

    .venv/bin/python -B kontroller/kundvakt.py <slug> <underlag-katalog>     (läser krokens JSON på stdin)

Vakten stänger vid fel. Tjänsternas verktyg står inte i sessionens --allowedTools: ett rent anrop öppnas bara av
vaktens uttryckliga tillåtelse (JSON med permissionDecision allow på stdout, slutkod 0). Ett anrop med kundens
uppgifter stoppas med slutkod 2 och skälet på stderr. Kan vakten inte pröva anropet (fel, egen frist), eller startar den
inte alls, får anropet ingen tillåtelse och dontAsk nekar det (kontroller/atelje.py, kundvakt; granskning 4, G3).

Id-fält (style_id, screen_ids, flow_id …) med UUID eller tal och tjänsternas egna adresser prövas inte som "lång
sifferföljd" eller "adress"; fritext prövas alltid, och namnprövningen tål NFD-kodade tecken, URL-kodning,
sammansättningar och telefon i internationell form (granskning 4, G14).
"""
import json
import re
import signal
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

FRIST = 20  # sekunder; krokens egen tidsgräns är 30 (kontroller/atelje.py)
ID_NYCKEL = re.compile(r'(^|_)(id|ids|page|limit|platform|image_size|response_format|mode)$')
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
TAL = re.compile(r'^\d{1,12}$')
TJANSTEVARDAR = ('refero.design', 'mobbin.com')


def falt(x, nyckel=''):
    """(nyckel, sträng) för varje strängvärde i anropets indata, också i listor (en lista ärver sin nyckel)."""
    if isinstance(x, str):
        yield nyckel, x
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield nyckel, str(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from falt(v, str(k))
    elif isinstance(x, list):
        for v in x:
            yield from falt(v, nyckel)


def ar_id(nyckel, varde):
    return bool(ID_NYCKEL.search(nyckel.lower())) and bool(UUID.match(varde.strip()) or TAL.match(varde.strip()))


def tjanstens_adress(varde):
    try:
        d = urllib.parse.urlsplit(varde.strip())
    except ValueError:
        return False
    vard = (d.hostname or '').lower()
    return d.scheme == 'https' and any(vard == v or vard.endswith('.' + v) for v in TJANSTEVARDAR)


def provning(slug, underlag, anrop):
    """None när anropet får gå, annars skälet."""
    import skapande
    forbjudna = skapande.forbjudna_termer(slug, underlag)
    if not forbjudna.get('ord') and not forbjudna.get('siffror'):
        return 'kundens uppgifter gick inte att läsa (underlag/%s/VERKSAMHET.json); anropet stoppas' % slug
    namn = anrop.get('tool_name')
    fritext = []
    for nyckel, varde in falt(anrop.get('tool_input') or {}):
        if ar_id(nyckel, varde):
            continue
        if tjanstens_adress(varde):
            if skapande.namner_kunden(urllib.parse.unquote(varde), forbjudna):
                return 'anropet till %s har en adress som nämner kundens uppgifter' % namn
            continue
        fritext.append(varde)
    text = ' '.join(fritext)
    if skapande.namner_kunden(text, forbjudna):
        return ('anropet till %s nämner kundens namn, ort, webbadress, e-post eller nummer; beskriv bara branschen och '
                'vad sökningen ska ge' % namn)
    if any(skapande.SPARRAD_FORM.search(x) for x in fritext):
        return 'anropet till %s innehåller en adress, en e-postadress eller en lång sifferföljd; skriv frågan utan dem' % namn
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    def frist_ute(*_):
        raise TimeoutError('vaktens frist (%d s) tog slut' % FRIST)
    try:
        signal.signal(signal.SIGALRM, frist_ute)
        signal.alarm(FRIST)
        slug, underlag = argv[0], Path(argv[1])
        anrop = json.loads(sys.stdin.read() or '{}')
        skal = provning(slug, underlag, anrop)
        signal.alarm(0)
    except Exception as e:  # noqa: BLE001 — vakten stänger vid fel
        skal = 'kundvakten kunde inte pröva anropet (%s: %s); anropet stoppas' % (type(e).__name__, str(e)[:200])
    if skal:
        print(skal, file=sys.stderr)
        return 2
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow',
                                             'permissionDecisionReason': 'kundvakten: anropet bär inga uppgifter om kunden'}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
