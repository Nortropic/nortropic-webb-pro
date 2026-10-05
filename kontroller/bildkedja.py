#!/usr/bin/env python3
"""bildkedja.py — vilka bilder en session faktiskt läste (Codex tillägg 2026-10-05, observationspunkt 1).

Ett lyckat verktygsanrop bevisar inte att rätt bild bedömts. Varje session lämnar ett transkript med sina Read-anrop:
byggets egen logg (kunder/<slug>/korning-*.jsonl) och, för sessionerna som körs med --output-format json (granskarna,
ateljéns divergens och domare), Claude Codes transkript ~/.claude/projects/<katalog>/<session_id>.jsonl, där
session_id står i sessionens svar-*.json. Modulen ställer det som erbjöds eller krävdes mot det som lästes.

Designprovet 2026-10-05 visade varför: panelen fick 21 ankarbilder ur ägarens kalibrering och läste 0–5 av dem.

    .venv/bin/python kontroller/bildkedja.py <slug>    # kunder/<slug>/BILDKEDJA.md och .json (privata)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
PROJEKT = Path(os.environ.get('CLAUDE_CONFIG_DIR') or (Path.home() / '.claude')) / 'projects'
BILDTYPER = r'png|jpe?g|webp|avif|gif'
BILD = re.compile(r'\.(%s)$' % BILDTYPER, re.I)
SESSION = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def transkript(session_id):
    """Sessionens transkript, eller None (okänt id, eller Claude Code sparade inget)."""
    if not isinstance(session_id, str) or not SESSION.match(session_id) or not PROJEKT.is_dir():
        return None
    for p in PROJEKT.glob('*/%s.jsonl' % session_id):
        if p.is_file() and not p.is_symlink():
            return p
    return None


def lasta(fil):
    """Filerna sessionen läste med Read, i ordning, ur ett transkript eller en strömmad logg (samma radformat). Ett
    Read vars svar var ett fel räknas inte som läst."""
    anrop, felade = [], set()
    try:
        with open(fil, encoding='utf-8', errors='replace') as f:
            for rad in f:
                if '"Read"' not in rad and '"is_error"' not in rad:
                    continue
                try:
                    r = json.loads(rad)
                except ValueError:
                    continue
                innehall = (r.get('message') or {}).get('content') if isinstance(r, dict) else None
                for c in innehall if isinstance(innehall, list) else []:
                    if not isinstance(c, dict):
                        continue
                    if c.get('type') == 'tool_use' and c.get('name') == 'Read' and isinstance((c.get('input') or {}).get('file_path'), str):
                        anrop.append((c.get('id'), c['input']['file_path']))
                    elif c.get('type') == 'tool_result' and c.get('is_error') is True:
                        felade.add(c.get('tool_use_id'))
    except OSError:
        return []
    return [v for i, v in anrop if i is None or i not in felade]


def relativ(v):
    """Vägen relativt repots rot när den ligger där, annars som den står; alltid med snedstreck."""
    v = str(v).replace('\\', '/')
    for rot in {str(ROOT), os.path.realpath(ROOT)}:
        if v.startswith(rot + '/'):
            return v[len(rot) + 1:]
    return v


def last(krav, lasta_):
    """Är just den krävda filen läst? Samma fil: samma väg relativt repots rot (en absolut väg under roten räknas om),
    aldrig bara samma slut; en kopia under en annan rot är en annan fil (granskningen av r62, punkt 1)."""
    k = relativ(krav).strip('/')
    return any(relativ(x).lstrip('./') == k for x in lasta_)


def lasning(session_id, krav):
    """{'verifierad': bool, 'grupper': {grupp: {'kravda', 'lasta', 'saknas'}}, 'bilder_lasta'} för en session.
    krav: {grupp: [krav]}, där ett krav är en väg, eller en lista av vägar där en räcker (ett ankare sett i 390 eller
    1440). Utan transkript är läsningen inte verifierad (ingen grupp räknas som läst)."""
    t = transkript(session_id)
    if t is None:
        return {'verifierad': False, 'grupper': {}, 'bilder_lasta': None, 'skal': 'transkriptet saknas'}
    l = lasta(t)
    grupper = {}
    for g, lista in krav.items():
        alternativ = [k if isinstance(k, (list, tuple)) else [k] for k in lista]
        saknas = [relativ(a[0]) for a in alternativ if a and not any(last(v, l) for v in a)]
        grupper[g] = {'kravda': len(alternativ), 'lasta': len(alternativ) - len(saknas), 'saknas': saknas}
    return {'verifierad': True, 'grupper': grupper, 'bilder_lasta': sum(1 for x in l if BILD.search(x)), 'transkript': t.name}


def ankarkrav(ankare, vag):
    """Ägarens kalibreringsankare som läsekrav: ägarens ord, och varje ankare sett minst en gång (första vyn i 390 eller
    1440). ankare = (ordfil, [(bild, text)]) som granska.frysta_ankare ger; vag gör en väg relativ roten."""
    per_ankare = {}
    for p, _ in ankare[1]:
        m = re.match(r'^(.+)-vy-(390|1440)-forsta\.png$', Path(p).name)
        if m:
            per_ankare.setdefault(m.group(1), []).append(vag(p))
    return [vag(ankare[0])] + [per_ankare[k] for k in sorted(per_ankare)]


def brister(las):
    """Kraven som inte uppfylldes, som korta meningar; tom lista när allt lästes eller läsningen inte kunde verifieras."""
    if not las.get('verifierad'):
        return []
    return ['%s %d av %d' % (g, x['lasta'], x['kravda']) for g, x in las['grupper'].items() if x['saknas']]


def klass(v):
    v = relativ(v)
    if '/atelje/ankare/' in v or '/kalibrering/' in v:
        return 'ankare'
    if '/referenser/' in v:
        return 'referens'
    if re.search(r'/atelje/(omgang-\d+/)?\d+/', v):
        return 'ateljéförslag'
    if '/bilder/' in v or '/assets/' in v:
        return 'egna bilder'
    if '/prov/' in v or '/granskning/' in v:
        return 'provets skärmbilder'
    return 'annat'


def erbjudna_i_prompt(text):
    """Bildvägarna en prompt räknar upp (relativa roten eller absoluta), i ordning, en gång var."""
    sedda, ut = set(), []
    # en absolut väg börjar efter blanksteg eller skiljetecken, aldrig mitt i en relativ väg (granskningen av r62, punkt 3)
    for m in re.finditer(r'(?:(?<![\w./-])/[^\s,;:]+|(?<![\w./-])(?:kunder|underlag)/[^\s,;:]+)\.(?:%s)\b' % BILDTYPER, text, re.I):
        v = m.group(0)
        if v not in sedda:
            sedda.add(v)
            ut.append(v)
    return ut


def sessionsrad(namn, session_id, erbjudna=None):
    t = transkript(session_id)
    if t is None:
        return {'session': namn, 'verifierad': False, 'skal': 'transkriptet saknas'}
    l = lasta(t)
    bilder = [x for x in l if BILD.search(x)]
    rad = {'session': namn, 'verifierad': True, 'bilder_lasta': len(bilder),
           'per_klass': {k: sum(1 for x in bilder if klass(x) == k) for k in sorted({klass(x) for x in bilder})}}
    if erbjudna is not None:
        saknas = [relativ(v) for v in erbjudna if not last(v, l)]
        rad.update(erbjudna=len(erbjudna), lasta_av_erbjudna=len(erbjudna) - len(saknas), saknas=saknas,
                   saknas_per_klass={c: sum(1 for x in saknas if klass(x) == c) for c in sorted({klass(x) for x in saknas})})
    return rad


def rapport(slug):
    k, u = KUNDER / slug, UNDERLAG / slug
    ut = {'slug': slug, 'bygget': [], 'granskningen': [], 'ateljen': []}
    for f in sorted(k.glob('korning-*.jsonl')):  # byggets egen strömmade logg bär sina Read-anrop
        l = [x for x in lasta(f) if BILD.search(x)]
        ut['bygget'].append({'session': f.name, 'verifierad': True, 'bilder_lasta': len(l),
                             'per_klass': {c: sum(1 for x in l if klass(x) == c) for c in sorted({klass(x) for x in l})}})
    for r in sorted((k / 'granskning').glob('runda-*')) if (k / 'granskning').is_dir() else []:
        for svar, prompt in (('svar.json', 'PROMPT.txt'), ('svar-2.json', 'PROMPT-2.txt'), ('svar-originalitet.json', None)):
            s = las_json(r / svar)
            if not s:
                continue
            text = (r / prompt).read_text(encoding='utf-8', errors='replace') if prompt and (r / prompt).is_file() else None
            ut['granskningen'].append(dict(sessionsrad('%s/%s' % (r.name, svar), s.get('session_id'), erbjudna_i_prompt(text) if text else None)))
    a = u / 'atelje'
    for kat in ([p for p in sorted(a.glob('omgang-*')) if p.is_dir()] + [a]) if a.is_dir() else []:
        for svar in sorted(kat.glob('svar-*.json')):
            s = las_json(svar) or {}
            ut['ateljen'].append(sessionsrad('%s/%s' % (kat.name, svar.name), s.get('session_id')))
    return ut


def markdown(r):
    def tabell(rubrik, rader):
        if not rader:
            return ['## ' + rubrik, '', 'Inga sessioner.', '']
        ut = ['## ' + rubrik, '', '| Session | Bilder lästa | Per slag | Erbjudna lästa | Olästa per slag |', '|---|---|---|---|---|']
        for x in rader:
            if not x.get('verifierad'):
                ut.append('| %s | ej verifierad: %s | | | |' % (x['session'], x.get('skal', '')))
                continue
            ut.append('| %s | %d | %s | %s | %s |' % (x['session'], x['bilder_lasta'], ', '.join('%s %d' % kv for kv in x['per_klass'].items()) or '–',
                                                    '%d av %d' % (x['lasta_av_erbjudna'], x['erbjudna']) if 'erbjudna' in x else '–',
                                                    ', '.join('%s %d' % kv for kv in (x.get('saknas_per_klass') or {}).items()) or '–'))
        return ut + ['']
    return '\n'.join(['# Bildkedjan · %s' % r['slug'], '',
                      'Vilka bilder varje session faktiskt läste (Read i transkriptet), mot vad prompten erbjöd. Ett lyckat anrop',
                      'bevisar inte att rätt bild bedömts (Codex 2026-10-05). Ej verifierad: transkriptet finns inte kvar.', '',
                      *tabell('Bygget', r['bygget']), *tabell('Granskningen', r['granskningen']), *tabell('Ateljén', r['ateljen'])])


def main(argv=None):
    p = argparse.ArgumentParser(prog='bildkedja', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    a = p.parse_args(argv)
    if not re.match(r'^[a-z0-9-]{2,60}$', a.slug) or not (KUNDER / a.slug).is_dir():  # rapporten skrivs i byggets katalog
        print('okänt bygge: %s' % a.slug, file=sys.stderr)
        return 2
    r = rapport(a.slug)
    (KUNDER / a.slug / 'BILDKEDJA.json').write_text(json.dumps(r, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (KUNDER / a.slug / 'BILDKEDJA.md').write_text(markdown(r), encoding='utf-8')
    print(markdown(r))
    return 0


if __name__ == '__main__':
    sys.exit(main())
