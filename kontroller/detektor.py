#!/usr/bin/env python3
"""detektor.py — Impeccables detektor (motorn `impeccable detect`) på en kandidats byggda sida: antimönster och
designbrister i typografi, layout och färg. Ett verktyg för kompetensen visuell kritik och slutbearbetning
(kunskap/metodkarta.md, Kompetenserna); fynden prövas med omdöme, och ett fynd som strider mot ett ägarbeslut eller
kundens behov (till exempel en palett ägaren valt) motiveras i stället för att rättas.

    .venv/bin/python kontroller/detektor.py <slug> --kandidat kNN [--json]
    .venv/bin/python kontroller/detektor.py <slug> --kandidat kNN --granskare

Motorn: IMPECCABLE_BIN, annars den version skillens scripts/VERSION anger under ~/.impeccable/bin/, annars den nyaste
som finns där. Inget nät: finns ingen motor säger verktyget det (slutkod 3).

--granskare är den blinda kritikens form (kunskap/metodkarta.md, Kompetenserna): regeln, dess namn och beskrivning,
allvaret, kategorin och hur många gånger den slog till, aldrig motorns utdrag, fil, rad eller meddelande, som bär sidans
kod, klassnamn och text (ett verktyg som ger kod till kritiken är ett läckage; ägarens ord 2026-10-07).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.claude' / 'skills' / 'impeccable'
HEM = Path.home() / '.impeccable' / 'bin'


def motor():
    if os.environ.get('IMPECCABLE_BIN') and os.access(os.environ['IMPECCABLE_BIN'], os.X_OK):
        return Path(os.environ['IMPECCABLE_BIN'])
    try:
        v = (SKILL / 'scripts' / 'VERSION').read_text().strip()
    except OSError:
        v = ''
    if v and os.access(HEM / v / 'impeccable', os.X_OK):
        return HEM / v / 'impeccable'
    alla = sorted((p for p in HEM.glob('*/impeccable') if os.access(p, os.X_OK)),
                  key=lambda p: [int(x) if x.isdigit() else 0 for x in re.split(r'[.]', p.parent.name)])
    return alla[-1] if alla else None


def detektera(fil):
    m = motor()
    if m is None:
        return None, 'Impeccables motor finns inte (IMPECCABLE_BIN eller ~/.impeccable/bin/<version>/impeccable)'
    r = subprocess.run([str(m), 'detect', '--json', '--no-config', str(fil)], capture_output=True, text=True, timeout=180,
                       env=dict(os.environ, IMPECCABLE_SKILL_DIR=str(SKILL)))
    try:
        d = json.loads(r.stdout or '[]')
    except ValueError:
        return None, 'motorn gav inget läsbart svar (kod %s): %s' % (r.returncode, (r.stderr or r.stdout)[-300:])
    fynd = d if isinstance(d, list) else d.get('findings') or d.get('results') or []
    return [x for x in fynd if isinstance(x, dict)], None


GRANSKARFALT = ('antipattern', 'name', 'description', 'severity', 'category')  # regelkatalogens fält, aldrig sidans


def for_granskaren(fynd):
    """Fynden utan sidans innehåll: en post per regel med katalogens fält och antalet träffar. Allt annat (snippet, file,
    line, message och fält som en ny motor lägger till) utelämnas, eftersom det kan bära kod eller sidans text."""
    ut = {}
    for x in fynd:
        regel = str(x.get('antipattern') or x.get('rule') or x.get('name') or '?')[:80]
        post = ut.setdefault(regel, dict({f: str(x.get(f))[:600] for f in GRANSKARFALT if isinstance(x.get(f), (str, int, float))}, antal=0))
        post['antal'] += 1
    return list(ut.values())


def main(argv=None):
    p = argparse.ArgumentParser(prog='detektor', description=__doc__.split('\n\n')[0], allow_abbrev=False)
    p.add_argument('slug')
    p.add_argument('--kandidat', required=True)
    p.add_argument('--json', action='store_true')
    p.add_argument('--granskare', action='store_true', help='kritikens form: regeln och antalet, aldrig kodutdrag')
    a = p.parse_args(argv)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug) or not re.fullmatch(r'k\d{2}', a.kandidat):
        print('slug a–z, 0–9, bindestreck; kandidaten som k01–k12', file=sys.stderr)
        return 2
    fil = ROOT / 'kunder' / a.slug / 'kandidater' / a.kandidat / 'sajt' / 'dist' / 'index.html'
    if not fil.is_file():
        print('den byggda sidan saknas (%s): kör förhandsvisningen först' % fil.relative_to(ROOT), file=sys.stderr)
        return 2
    fynd, fel = detektera(fil)
    if fel:
        # motorns egen utskrift vid fel kan bära sidans innehåll: granskaren får bara vad som gick fel
        print(fel if not a.granskare else 'Impeccables motor finns inte' if 'finns inte' in fel else 'Impeccables motor gav inget läsbart svar',
              file=sys.stderr)
        return 3
    if a.granskare:
        regler = for_granskaren(fynd)
        print('Impeccables detektor på kandidatens byggda sida: %d fynd i %d regler (utan kodutdrag; pröva varje regel mot '
              'det du ser i bilderna och mot ägarbesluten)' % (len(fynd), len(regler)))
        for x in regler:
            print('- %s %s (%s) ×%d: %s' % (x.get('severity', '?'), x.get('antipattern') or '', x.get('name') or '', x['antal'], x.get('description') or ''))
        return 0
    if a.json:
        print(json.dumps(fynd, ensure_ascii=False, indent=1))
        return 0
    print('Impeccables detektor på %s: %d fynd' % (fil.relative_to(ROOT), len(fynd)))
    for x in fynd:
        print('- %s %s (%s): %s' % (x.get('severity', '?'), x.get('antipattern') or x.get('rule') or '', x.get('name') or '', str(x.get('snippet') or x.get('message') or '')[:300]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
