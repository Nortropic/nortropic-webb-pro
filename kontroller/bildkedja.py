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


def utan_punkt(v):
    """Ett inledande ./ bort, aldrig punkten i .claude/ (granskningen av skapandeflödet, punkt 3: lstrip('./') tog den)."""
    while v.startswith('./'):
        v = v[2:]
    return v


def last(krav, lasta_):
    """Är just den krävda filen läst? Samma fil: samma väg relativt repots rot (en absolut väg under roten räknas om),
    aldrig bara samma slut; en kopia under en annan rot är en annan fil (granskningen av r62, punkt 1)."""
    k = relativ(krav).strip('/')
    return any(utan_punkt(relativ(x)) == k for x in lasta_)


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


def handelser(fil):
    """Transkriptets verktygsanrop och svar i ordning: ('anrop', id, namn, input) och ('svar', tool_use_id, text, fel)."""
    ut = []
    try:
        with open(fil, encoding='utf-8', errors='replace') as f:
            for rad in f:
                if '"tool_use"' not in rad and '"tool_result"' not in rad:
                    continue
                try:
                    r = json.loads(rad)
                except ValueError:
                    continue
                innehall = (r.get('message') or {}).get('content') if isinstance(r, dict) else None
                for c in innehall if isinstance(innehall, list) else []:
                    if not isinstance(c, dict):
                        continue
                    if c.get('type') == 'tool_use':
                        ut.append(('anrop', c.get('id'), c.get('name'), c.get('input') or {}))
                    elif c.get('type') == 'tool_result':
                        x = c.get('content')
                        text = x if isinstance(x, str) else ' '.join(y.get('text', '') for y in x if isinstance(y, dict)) if isinstance(x, list) else ''
                        ut.append(('svar', c.get('tool_use_id'), text, c.get('is_error') is True))
    except OSError:
        return []
    return ut


# prototypens varv (underlag/<slug>/forhand/<sida>/) och kandidatflödets (underlag/<slug>/atelje/kandidater/<id>/varv/<sida>/)
VARVVAG = re.compile(r'(underlag/[a-z0-9-]+/(?:forhand|atelje/kandidater/k\d{2}/varv)/(?:[a-z0-9-]+/)?varv-\d{2,})/vy-390-forsta\.png')
VARVBILDER = ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png')


def varvordning(session_id, slug, referens=(), src=None):
    """Läsningen per förhandsvarv, i ordning (Codex 2026-10-05, glapp 5: ett räknat antal läsningar över hela sessionen
    visar inte att varvet jämfördes). Ett varv börjar när förhandsvisa.py svarat med varvets vägar och slutar vid nästa
    ändring i kunder/<slug>/sajt/src/ eller nästa förhandsvisning. Inom fönstret ska varvets fyra bilder ha lästs, och
    minst en av referensbilderna (huvudreferensen läses om varje varv: Claude Codes medietak tränger undan de äldsta
    bilderna ur kontexten). Ger {'verifierad', 'varv': [{'varv', 'kravda', 'lasta', 'saknas', 'slutar'}]}."""
    t = transkript(session_id)
    if t is None:
        return {'verifierad': False, 'varv': [], 'skal': 'transkriptet saknas'}
    h = handelser(t)
    bash = {i: x[3].get('command', '') for i, x in ((x[1], x) for x in h if x[0] == 'anrop' and x[2] == 'Bash')}
    felade = {x[1] for x in h if x[0] == 'svar' and x[3]}
    src = src or 'kunder/%s/sajt/src/' % slug  # en kandidats egna sidor: kunder/<slug>/kandidater/<id>/sajt/src/
    ut = []
    for k, x in enumerate(h):
        if x[0] != 'svar' or x[3] or 'kontroller/forhandsvisa.py' not in bash.get(x[1], ''):
            continue
        m = VARVVAG.search(x[2])
        if not m:
            continue
        lasta_, slutar = [], 'sessionens slut'
        for y in h[k + 1:]:
            if y[0] != 'anrop':
                continue
            if y[2] in ('Write', 'Edit', 'MultiEdit') and relativ(y[3].get('file_path', '')).startswith(src):
                slutar = 'en ändring i %s' % relativ(y[3].get('file_path', ''))
                break
            if y[2] == 'Bash' and 'kontroller/forhandsvisa.py' in y[3].get('command', ''):
                slutar = 'nästa förhandsvisning'
                break
            if y[2] == 'Read' and y[1] not in felade and isinstance(y[3].get('file_path'), str):
                lasta_.append(y[3]['file_path'])
        krav = [m.group(1) + '/' + n for n in VARVBILDER] + ([[relativ(r) for r in referens]] if referens else [])
        saknas = [relativ(a[0] if isinstance(a, list) else a) for a in krav
                  if not any(last(v, lasta_) for v in (a if isinstance(a, list) else [a]))]
        ut.append({'varv': m.group(1).rsplit('/', 1)[-1], 'kravda': len(krav), 'lasta': len(krav) - len(saknas), 'saknas': saknas, 'slutar': slutar})
    return {'verifierad': True, 'varv': ut, 'transkript': t.name}


METODFIL = re.compile(r'(?:^|/)(METOD-[a-z]+(?:-varv|-text|-uppslag)?)(?:-\d+)?\.md$')  # kontroller/metod.py, leverera
METODRUBRIK = re.compile(r'^### (\S+) · (rad \d+–\d+(?:, rad \d+–\d+)*) · sha ([0-9a-f]{12})( \(fortsättning\))?$', re.M)


def _fil(v):
    """En läst väg som fil: relativt roten, eller absolut."""
    return Path(v) if Path(v).is_absolute() else ROOT / v


def _stam(v):
    """Metodfilens del utan löpnummer (METOD-skiss för METOD-skiss.md och METOD-skiss-2.md), eller None."""
    m = METODFIL.search(str(v))
    return m.group(1) if m else None


def levererade_hela(metodfiler, krav):
    """De krävda filer som en levererad metodfil (kontroller/metod.py, METOD-<steg>….md) bär hela, och när: rubriken
    "### <väg> · rad a–b · sha <12 tecken>" med samma sha som filen har nu och rader som täcker hela filen, i en metodfil
    som sessionen läst hel. Ett block som fortsätter i nästa fil av samma del (rubriken med "(fortsättning)") räknas först
    när varje sådan fil också lästs hel. metodfiler: {läst väg: händelsens index när filen var läst hel}; ger {krav:
    index}. Granskningen 2026-10-06: kvittot räknade kunskap/bild.md som oläst fast hela filen stod i METOD-skiss.md."""
    import hashlib
    import metod
    ut, texter = {}, {}

    def text(s):
        if s not in texter:
            try:
                texter[s] = _fil(s).read_text(encoding='utf-8')
            except OSError:
                texter[s] = ''
        return texter[s]

    for f in metodfiler:
        stam = _stam(f)
        syskon = [s for s in (utan_punkt(relativ(str(x))) for x in sorted(_fil(f).parent.glob(stam + '*.md'))) if s != f and _stam(s) == stam]
        for m in METODRUBRIK.finditer(text(f)):
            if m.group(4):
                continue  # en fortsättning räknas med blockets början
            try:
                k = metod.kalla(m.group(1)).relative_to(metod.ROOT).as_posix()  # en skills väg står utan .claude/skills/
                innehall = (ROOT / k).read_text(encoding='utf-8')
            except (OSError, ValueError):
                continue
            tackt = set()
            for a, b in re.findall(r'rad (\d+)–(\d+)', m.group(2)):
                tackt.update(range(int(a), int(b) + 1))
            if k not in krav or not tackt >= set(range(1, len(innehall.splitlines()) + 1)) \
                    or hashlib.sha256(innehall.encode('utf-8')).hexdigest()[:12] != m.group(3):
                continue
            delar = [f] + [s for s in syskon if m.group(0) + ' (fortsättning)' in text(s).splitlines()]
            if all(s in metodfiler for s in delar):
                i = max(metodfiler[s] for s in delar)
                ut[k] = min(ut.get(k, i), i)
    return ut


def metodlasning(session_id, filer, skills=(), skrivprefix=None):
    """Metodkvittot (Codex 2026-10-05, glapp 2: prototypens skapare läste inga designskills): vilka av metodfilerna
    sessionen fick ett matchat lyckat svar från Read eller Skill, och om svaret kom före första skrivningen under
    skrivprefix (en väg relativt roten, till exempel kunder/<slug>/sajt/src/). En skill räknas också som läst när dess
    SKILL.md lästes. Ett Read vars svar var ett fel räknas inte, och en fil räknas som läst först när läsningarna täckt
    alla dess rader (ett Read utan offset och limit täcker 2 000 rader); en fil som bara lästs i delar står i 'delvis'
    (granskning 2, N5). En fil som en helt läst metodfil bär hel, med samma sha, räknas som läst när metodfilen lästs
    (levererade_hela); de som bara lästs så står också i 'via_metod'. Ger {'verifierad', 'fore': [...], 'efter': [...], 'saknas': [...],
    'delvis': [...], 'via_metod': [...], 'skill_anrop': [...], 'skill_fel': [...]}; saknas omfattar de delvis lästa."""
    t = transkript(session_id)
    if t is None:
        return {'verifierad': False, 'skal': 'transkriptet saknas'}
    h = handelser(t)
    felade = {x[1] for x in h if x[0] == 'svar' and x[3]}
    skill_fel = sorted({x[3]['skill'] for x in h if x[0] == 'anrop' and x[1] in felade
                        and x[2] == 'Skill' and isinstance(x[3].get('skill'), str)})
    krav = [relativ(f).strip('/') for f in filer] + ['.claude/skills/%s/SKILL.md' % s for s in skills]
    radantal = {}
    for k in krav:
        try:
            radantal[k] = len((ROOT / k).read_text(encoding='utf-8', errors='replace').splitlines())
        except OSError:
            radantal[k] = None
    forsta, sedda, anrop, tackt, metodhel, metodrader = None, {}, [], {}, {}, {}
    vantar = {}
    for i, x in enumerate(h):
        if x[0] == 'anrop':
            if forsta is None and skrivprefix and x[2] in ('Write', 'Edit', 'MultiEdit') and relativ(x[3].get('file_path', '')).startswith(skrivprefix):
                forsta = i
            if x[1] and x[1] not in felade:
                vantar[x[1]] = x
            continue
        if x[0] != 'svar' or x[3] or x[1] not in vantar:
            continue
        # Tidpunkten är det matchade svarets; inget kvitto för ett obesvarat anrop.
        x = vantar.pop(x[1])
        if x[2] == 'Read' and isinstance(x[3].get('file_path'), str) and x[1] not in felade:
            v = utan_punkt(relativ(x[3]['file_path']))
            try:
                a, n = max(1, int(x[3].get('offset') or 1)), int(x[3].get('limit') or 2000)
            except (TypeError, ValueError):
                a, n = 1, 2000
            tackt.setdefault(v, set()).update(range(a, a + max(0, n)))
            total = radantal.get(v)
            hel = (not x[3].get('offset') and not x[3].get('limit')) if total is None else all(r in tackt[v] for r in range(1, total + 1))
            if hel:
                sedda.setdefault(v, i)
            if _stam(v):  # en levererad metodfil: hel när alla dess rader lästs (levererade_hela)
                if v not in metodrader:
                    try:
                        metodrader[v] = len(_fil(v).read_text(encoding='utf-8', errors='replace').splitlines())
                    except OSError:
                        metodrader[v] = None
                if metodrader[v] and all(r in tackt[v] for r in range(1, metodrader[v] + 1)):
                    metodhel.setdefault(v, i)
        elif x[2] == 'Skill' and isinstance(x[3].get('skill'), str) and x[1] not in felade:
            # Aktivering/läsning är observerad mekanik, aldrig bevis för tillämpning eller designkvalitet.
            anrop.append(x[3]['skill'])
            sedda.setdefault('.claude/skills/%s/SKILL.md' % x[3]['skill'].split(':')[-1], i)
    via, direkt = (levererade_hela(metodhel, set(krav)) if metodhel else {}), set(sedda)
    for k, i in via.items():
        sedda[k] = min(sedda.get(k, i), i)
    fore = [k for k in krav if k in sedda and (forsta is None or sedda[k] < forsta)]
    efter = [k for k in krav if k in sedda and k not in fore]
    return {'verifierad': True, 'fore': fore, 'efter': efter, 'saknas': [k for k in krav if k not in sedda],
            'delvis': [k for k in krav if k not in sedda and k in tackt], 'via_metod': [k for k in krav if k in via and k not in direkt],
            'skill_anrop': anrop, 'skill_fel': skill_fel, 'forsta_skrivning': forsta is not None}


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
