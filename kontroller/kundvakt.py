#!/usr/bin/env python3
"""kundvakt.py — PreToolUse-krok för skapandeflödets sessioner: ett anrop till en extern designtjänst (Refero, Mobbin,
Trybloom) får aldrig bära kundens namn, orter, gata, webbadress, e-post eller nummer (BESLUT.md 2026-10-05, punkt 4;
ägarens ord 2026-10-05 18:15Z: skillsen och MCP:erna ska användas, och kundens uppgifter skyddas som förut).

    .venv/bin/python -B kontroller/kundvakt.py <slug> <underlag-katalog>     (läser krokens JSON på stdin)

Slutkod 0 släpper igenom anropet; slutkod 2 stoppar det, och meddelandet på stderr går till sessionen. Vakten stänger
vid fel: kan den inte läsa anropet eller kundens uppgifter stoppas anropet (en krok som dör får aldrig släppa igenom).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def strangar(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strangar(v)
    elif isinstance(x, list):
        for v in x:
            yield from strangar(v)


def provning(slug, underlag, anrop):
    """None när anropet får gå, annars skälet."""
    import skapande
    forbjudna = skapande.forbjudna_termer(slug, underlag)
    if not forbjudna.get('ord') and not forbjudna.get('siffror'):
        return 'kundens uppgifter gick inte att läsa (underlag/%s/VERKSAMHET.json); anropet stoppas' % slug
    text = ' '.join(strangar(anrop.get('tool_input') or {}))
    if skapande.namner_kunden(text, forbjudna):
        return ('anropet till %s nämner kundens namn, ort, webbadress, e-post eller nummer; beskriv bara branschen och '
                'vad sökningen ska ge' % anrop.get('tool_name'))
    if skapande.SPARRAD_FORM.search(text):
        return 'anropet till %s innehåller en adress, en e-postadress eller en lång sifferföljd; skriv frågan utan dem' % anrop.get('tool_name')
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        slug, underlag = argv[0], Path(argv[1])
        anrop = json.loads(sys.stdin.read() or '{}')
        skal = provning(slug, underlag, anrop)
    except Exception as e:  # noqa: BLE001 — vakten stänger vid fel
        skal = 'kundvakten kunde inte pröva anropet (%s: %s); anropet stoppas' % (type(e).__name__, str(e)[:200])
    if skal:
        print(skal, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
