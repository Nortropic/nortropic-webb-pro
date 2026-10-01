#!/usr/bin/env python3
"""Dashboard för nortropic-webb-pro. Lokal, läser repot och skriver bara ägarens domar.

    .venv/bin/python dashboard/server.py [--port 4771]     (eller ./dashboard.sh)

Visar byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag, körningens senaste händelser),
lärdomarna, kirurgens register och kommandona. Skriver bara när ägaren skickar frågeformuläret efter ett bygge:
kunder/<slug>/DOM.json (strukturerat, privat) och en post i LARDOMAR.md (ordagrant, i git).
Lyssnar bara på 127.0.0.1. POST kräver samma ursprung.
"""
import argparse
import html
import json
import mimetypes
import re
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
sys.path.insert(0, str(ROOT / 'kontroller'))
from prova import Server  # noqa: E402  (samma statiska server som provet använder)
import backlog as bl  # noqa: E402  (samma backlog-format som kirurgen och byggena skriver)

STEG = [
    ('Underlag', lambda s: (UNDERLAG / s / 'RESEARCH.md').is_file()),
    ('Diagnos', lambda s: (UNDERLAG / s / 'DIAGNOS.md').is_file()),
    ('Brief och referenser', lambda s: (UNDERLAG / s / 'BRIEF.md').is_file()),
    ('Innehåll', lambda s: (UNDERLAG / s / 'INNEHALL.md').is_file()),
    ('Bygge', lambda s: (KUNDER / s / 'sajt' / 'package.json').is_file()),
    ('Prov', lambda s: (KUNDER / s / 'prov' / 'STATUS.json').is_file()),
    ('Rapport', lambda s: (KUNDER / s / 'RAPPORT.md').is_file()),
    ('Dom', lambda s: (KUNDER / s / 'DOM.json').is_file()),
]

DIMENSIONER = ['Hållning', 'Typografi', 'Färg', 'Luft och hierarki', 'Substans', 'Förtroende', 'Mobil ergonomi', 'Konsekvens']

# Kärnfrågorna är desamma för varje bygge, så att svaren går att jämföra över tid (träningsdata).
KARNFRAGOR = [
    {'id': 'namn', 'fraga': 'Skulle du sätta ditt namn på sajten och visa den för verksamheten?', 'typ': 'val',
     'alternativ': ['Ja, som den är', 'Ja, efter små ändringar', 'Nej, inte utan större ändringar', 'Nej']},
    {'id': 'battre', 'fraga': 'Jämfört med verksamhetens nuvarande sajt är vår …', 'typ': 'val',
     'alternativ': ['Mycket bättre', 'Bättre', 'Ungefär lika', 'Sämre', 'Kan inte jämföra']},
    {'id': 'specifik', 'fraga': 'Känns den gjord för just den här verksamheten, eller som en mall?', 'typ': 'skala',
     'min': 'Mall', 'max': 'Bara de', 'steg': 5},
    {'id': 'mall_tecken', 'fraga': 'Om något känns som mall eller AI: peka på det. Var på sidan, och vad?', 'typ': 'fritext'},
    {'id': 'forsta_intryck', 'fraga': 'Efter fem sekunder på startsidan i mobilen: vad säger sajten till dig?', 'typ': 'fritext'},
    {'id': 'basta', 'fraga': 'Det bästa med sajten. Ett konkret ställe.', 'typ': 'fritext'},
    {'id': 'samsta', 'fraga': 'Det sämsta med sajten. Ett konkret ställe.', 'typ': 'fritext'},
    {'id': 'rost', 'fraga': 'Låter texten som verksamheten?', 'typ': 'val', 'alternativ': ['Ja', 'Delvis', 'Nej'],
     'foljd': 'Klistra gärna in en mening som inte håller.'},
    {'id': 'dimensioner', 'fraga': 'De åtta dimensionerna (kunskap/referenser-professionella.md)', 'typ': 'matris',
     'rader': DIMENSIONER, 'alternativ': ['Bra', 'Okej', 'Dålig']},
    {'id': 'referenser', 'fraga': 'Hur nära referenserna som bygget valde är den?', 'typ': 'skala', 'min': 'Långt ifrån', 'max': 'I nivå', 'steg': 5},
    {'id': 'referensval', 'fraga': 'Var referenserna rätt valda? Vilken skulle du ha valt i stället?', 'typ': 'fritext'},
    {'id': 'en_andring', 'fraga': 'Om du fick ändra en sak i hur vi bygger, vad skulle det vara?', 'typ': 'fritext'},
]


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def las_text(p):
    try:
        return Path(p).read_text(encoding='utf-8')
    except OSError:
        return None


# --- markdown → html (det som repots egna filer använder; allt annat blir text) ---

def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\w)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r'(?<![">])(https?://[^\s<)]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    return t


def md(text):
    if not text:
        return ''
    ut, rader, i = [], text.splitlines(), 0
    while i < len(rader):
        r = rader[i]
        if r.startswith('```'):
            j = i + 1
            while j < len(rader) and not rader[j].startswith('```'):
                j += 1
            ut.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(rader[i + 1:j])))
            i = j + 1
            continue
        m = re.match(r'^(#{1,4})\s+(.*)', r)
        if m:
            n = len(m.group(1)) + 1
            ut.append('<h%d>%s</h%d>' % (n, _inline(m.group(2)), n))
            i += 1
            continue
        if r.startswith('|') and i + 1 < len(rader) and re.match(r'^\|[\s:|-]+\|?\s*$', rader[i + 1]):
            cell = lambda x: [c.strip() for c in x.strip().strip('|').split('|')]
            head = cell(r)
            j, body = i + 2, []
            while j < len(rader) and rader[j].startswith('|'):
                body.append(cell(rader[j]))
                j += 1
            ut.append('<div class="tabell"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                ''.join('<th>%s</th>' % _inline(c) for c in head),
                ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % _inline(c) for c in row) for row in body)))
            i = j
            continue
        if re.match(r'^\s*([-*]|\d+\.)\s+', r):
            ordnad = bool(re.match(r'^\s*\d+\.', r))
            items = []
            while i < len(rader) and (re.match(r'^\s*([-*]|\d+\.)\s+', rader[i]) or (rader[i].startswith('   ') and items)):
                if re.match(r'^\s*([-*]|\d+\.)\s+', rader[i]):
                    items.append(re.sub(r'^\s*([-*]|\d+\.)\s+', '', rader[i]))
                else:
                    items[-1] += ' ' + rader[i].strip()
                i += 1
            tag = 'ol' if ordnad else 'ul'
            ut.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % _inline(x) for x in items), tag))
            continue
        if r.startswith('>'):
            j, q = i, []
            while j < len(rader) and rader[j].startswith('>'):
                q.append(rader[j].lstrip('> '))
                j += 1
            ut.append('<blockquote>%s</blockquote>' % _inline(' '.join(q)))
            i = j
            continue
        if not r.strip():
            i += 1
            continue
        j, p = i, []
        while j < len(rader) and rader[j].strip() and not re.match(r'^(#{1,4}\s|```|\||>|\s*([-*]|\d+\.)\s)', rader[j]):
            p.append(rader[j].strip())
            j += 1
        if not p:
            p, j = [r.strip()], i + 1
        ut.append('<p>%s</p>' % _inline(' '.join(p)))
        i = j
    return '\n'.join(ut)


# --- läsning av ett bygge ---

def siffror(katalog):
    """Lägsta mobilvärden ur lighthouse.json och allvarliga ur axe.json i en provkatalog."""
    lh = las_json(Path(katalog) / 'lighthouse' / 'lighthouse.json')
    ax = las_json(Path(katalog) / 'axe' / 'axe.json')
    ut = {}
    if lh and lh.get('rader'):
        mob = [r for r in lh['rader'] if r.get('form') == 'mobil'] or lh['rader']
        for k in ('prestanda', 'tillganglighet', 'bastaPraxis', 'seo'):
            ut[k] = min(r[k] for r in mob)
        ut['lcpMs'] = max(r.get('lcpMs', 0) for r in mob)
    if ax:
        ut['axe_allvarliga'] = ax.get('allvarliga')
    return ut


def bilder(slug):
    def lista(bas, monster):
        return sorted(str(p.relative_to(ROOT)) for p in bas.glob(monster)) if bas.is_dir() else []
    var = lista(KUNDER / slug / 'prov' / 'inspektion', '*/vy-*-forsta.png')
    deras = lista(UNDERLAG / slug / 'diagnos' / 'inspektion', 'vy-*-forsta.png')
    ref = lista(UNDERLAG / slug / 'referenser', '*/vy-*-forsta.png')
    return {'var': var, 'deras': deras, 'referenser': ref}


def korning(slug):
    loggar = sorted((KUNDER / slug).glob('korning-*.jsonl'))
    return las_logg(loggar[-1]) if loggar else None


def las_logg(logg):
    """En claude -p-logg i stream-json: modell, senaste handlingar, senaste text, resultat, om den pågår."""
    handlingar, text, resultat, start, modell = [], None, None, None, None
    try:
        for rad in logg.read_text(encoding='utf-8', errors='replace').splitlines():
            if not rad.startswith('{'):
                continue
            try:
                e = json.loads(rad)
            except ValueError:
                continue
            t = e.get('type')
            if t == 'system' and e.get('subtype') == 'init':
                start, modell = logg.stat().st_ctime, e.get('model')
            elif t == 'assistant':
                for c in (e.get('message') or {}).get('content', []):
                    if c.get('type') == 'tool_use':
                        inp = c.get('input') or {}
                        mal = inp.get('file_path') or inp.get('command') or inp.get('url') or inp.get('pattern') or inp.get('subject') or inp.get('description') or ''
                        handlingar.append({'verktyg': c.get('name'), 'mal': str(mal).replace(str(ROOT) + '/', '')[:160]})
                    elif c.get('type') == 'text' and c.get('text', '').strip():
                        text = c['text'].strip()[:600]
            elif t == 'result':
                resultat = {'utfall': e.get('subtype'), 'turer': e.get('num_turns'), 'minuter': round((e.get('duration_ms') or 0) / 60000, 1)}
    except OSError:
        return None
    andrad = logg.stat().st_mtime
    return {'logg': str(logg.relative_to(ROOT)), 'modell': modell, 'pagar': resultat is None and time.time() - andrad < 900,
            'senast': datetime.fromtimestamp(andrad, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'antal_handlingar': len(handlingar), 'handlingar': handlingar[-12:][::-1], 'senaste_text': text, 'resultat': resultat}


def sammanfattning(slug):
    v = las_json(UNDERLAG / slug / 'VERKSAMHET.json') or {}
    s = las_json(KUNDER / slug / 'prov' / 'STATUS.json')
    k = korning(slug)
    steg = [{'namn': n, 'klar': bool(f(slug))} for n, f in STEG]
    return {
        'slug': slug, 'namn': v.get('namn') or slug,
        'ort': ', '.join(((v.get('rackvidd') or {}).get('orter') or [])[:2]) or ((v.get('adress') or {}).get('ort') or ''),
        'doman': (v.get('webb') or {}).get('doman') if isinstance(v.get('webb'), dict) else None,
        'steg': steg, 'steg_klara': sum(x['klar'] for x in steg),
        'prov': {'ok': s.get('ok'), 'tid': s.get('tid'), 'snabb': s.get('snabb'),
                 'grindar': {n: g['ok'] for n, g in s.get('grindar', {}).items()}} if s else None,
        'pagar': bool(k and k['pagar']), 'domd': (KUNDER / slug / 'DOM.json').is_file(),
    }


def byggen():
    if not KUNDER.is_dir():
        return []
    # rokprov-* är kontrollernas regressionsfixtur (kontroller/rokprov.sh), inget bygge att döma
    ut = [sammanfattning(p.name) for p in KUNDER.iterdir() if p.is_dir() and SLUG.match(p.name) and not p.name.startswith('rokprov')]
    return sorted(ut, key=lambda b: (not b['pagar'], b['domd'], b['slug']))


def bygge(slug):
    b = sammanfattning(slug)
    s = las_json(KUNDER / slug / 'prov' / 'STATUS.json')
    egna = las_json(KUNDER / slug / 'FRAGOR.json')
    b.update({
        'status': s, 'stoppvakt': las_json(KUNDER / slug / 'prov' / 'STOPPVAKT.json'),
        'fore': siffror(UNDERLAG / slug / 'diagnos'), 'efter': siffror(KUNDER / slug / 'prov'),
        'bilder': bilder(slug), 'korning': korning(slug),
        'rapport': md(las_text(KUNDER / slug / 'RAPPORT.md')),
        'prov_md': md(las_text(KUNDER / slug / 'prov' / 'PROV.md')),
        'underlag': {namn: md(las_text(UNDERLAG / slug / fil)) for namn, fil in (
            ('Brief', 'BRIEF.md'), ('Referenser', 'REFERENSER.md'), ('Jämförelse', 'JAMFORELSE.md'),
            ('Femsekunderstest', 'FEMSEK.md'), ('Diagnos', 'DIAGNOS.md'), ('Research', 'RESEARCH.md'),
            ('Koncept', 'KONCEPT.md'), ('Innehåll', 'INNEHALL.md')) if (UNDERLAG / slug / fil).is_file()},
        'fragor': {'karna': KARNFRAGOR, 'egna': egna if isinstance(egna, list) else []},
        'domar': (las_json(KUNDER / slug / 'DOM.json') or {}).get('domar', []),
    })
    return b


def register():
    text = las_text(ROOT / 'kunskap' / 'REGISTER.md') or ''
    delar = text.split('\n### ')[1:]
    poster = []
    for d in delar:
        rubrik, _, kropp = d.partition('\n')
        bitar = [x.strip() for x in rubrik.split('·')]
        poster.append({'datum': bitar[0] if bitar else '', 'namn': bitar[1] if len(bitar) > 1 else rubrik,
                       'dom': bitar[2] if len(bitar) > 2 else '', 'html': md(kropp)})
    return poster[::-1]


# --- domen ---

def spara_dom(slug, data):
    if not (KUNDER / slug).is_dir():
        raise ValueError('okänt bygge')
    svar = data.get('svar')
    if not isinstance(svar, dict) or not svar:
        raise ValueError('inga svar')
    text = json.dumps(svar, ensure_ascii=False)
    if len(text) > 40000:
        raise ValueError('för långa svar')
    s = las_json(KUNDER / slug / 'prov' / 'STATUS.json') or {}
    post = {'tid': nu(), 'bygge_dist': (s.get('dist_sha256') or '')[:12], 'svar': svar,
            'fragor': {'karna': KARNFRAGOR, 'egna': las_json(KUNDER / slug / 'FRAGOR.json') or []}}
    fil = KUNDER / slug / 'DOM.json'
    allt = las_json(fil) or {'schema': 1, 'slug': slug, 'domar': []}
    allt['domar'].append(post)
    fil.write_text(json.dumps(allt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    lar = ROOT / 'LARDOMAR.md'
    befintlig = las_text(lar) or '# Lärdomar — ägarens domar\n'
    n = max([int(x) for x in re.findall(r'^## L(\d+) ', befintlig, re.M)] or [-1]) + 1
    alla = {f['id']: f for f in KARNFRAGOR + (post['fragor']['egna'] if isinstance(post['fragor']['egna'], list) else []) if isinstance(f, dict) and 'id' in f}
    rader = ['', '## L%d · %s · %s' % (n, post['tid'][:10], slug), '']
    for fid, v in svar.items():
        if v in (None, '', {}, []):
            continue
        fraga = (alla.get(fid) or {}).get('fraga', fid)
        if isinstance(v, dict):
            v = ', '.join('%s: %s' % (k, x) for k, x in v.items() if x)
        rader.append('- **%s** %s' % (fraga, str(v).replace('\n', ' / ')))
    rader += ['', '**Ändring:** väntar', '']
    # Domen blir automatiskt en vilande post i backloggen (loop 3): en session ägaren startar gör textändringen.
    kort = (svar.get('en_andring') or svar.get('samsta') or svar.get('mall_tecken') or 'se domen').strip().replace('\n', ' ')
    sammandrag = '; '.join('%s: %s' % ((alla.get(k) or {}).get('fraga', k), svar[k]) for k in ('namn', 'battre', 'specifik', 'samsta', 'mall_tecken', 'en_andring')
                           if isinstance(svar.get(k), (str, int)) and str(svar.get(k)).strip())
    pid = bl.ny('dom', 'Dom L%d (%s): %s' % (n, slug, kort[:90]), sammandrag or 'Ägarens dom, se LARDOMAR.md.',
                forslag='Läs domen i LARDOMAR.md (L%d) och kunder/%s/DOM.json. Gör en textändring i skillen bygg-sajt eller en fil i '
                        'kunskap/ som svarar mot det ägaren pekar på. En ändring, liten nog att läsa på fem minuter.' % (n, slug),
                klart='Ändringen är committad och raden Ändring under L%d i LARDOMAR.md pekar på commiten.' % n,
                sar='L%d' % n, kallref='LARDOMAR.md L%d' % n)
    rader[-2] = '**Ändring:** väntar (backlog %s)' % pid
    with open(lar, 'a', encoding='utf-8') as f:
        f.write('\n'.join(rader))
    return {'lardom': 'L%d' % n, 'sparad': str(fil.relative_to(ROOT)), 'backlog': pid}


# --- backloggen och kirurgen ---

def backloggen():
    ut = []
    for p in bl.lista():
        kropp = p.pop('kropp', '')
        p['html'] = md(re.sub(r'^# .+\n', '', kropp, count=1, flags=re.M))
        ut.append(p)
    ordning = {'pagar': 0, 'vilande': 1, 'klar': 2, 'avvisad': 3}
    return sorted(ut, key=lambda p: (ordning.get(p.get('status'), 9), p.get('prio') != 'hog', p.get('skapad', '')))


INTAG = ROOT / 'kirurgen'
INTAG_VERKTYG = ['Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch', 'Skill', 'Edit(kunskap/REGISTER.md)',
                 'Bash(.venv/bin/python kontroller/backlog.py *)', 'Bash(.venv/bin/python kontroller/youtube.py *)',
                 'Bash(gh repo clone *)', 'Bash(gh api repos/*)', 'Bash(cd *)', 'Bash(git add *)', 'Bash(git commit *)', 'Bash(git push origin main)', 'Bash(ls *)', 'Bash(find *)', 'Bash(wc *)', 'Bash(head *)', 'Bash(cat *)', 'Bash(mkdir *)']


def intag_lista():
    if not INTAG.is_dir():
        return []
    ut = []
    for meta in sorted(INTAG.glob('intag-*.json'), reverse=True)[:30]:
        m = las_json(meta) or {}
        logg = meta.with_suffix('.jsonl')
        k = las_logg(logg) if logg.is_file() else None
        ut.append({'id': meta.stem, 'url': m.get('url'), 'not': m.get('not'), 'tid': m.get('tid'),
                   'pagar': bool(k and k['pagar']), 'resultat': k and k['resultat'], 'svar': md(k['senaste_text']) if k and k.get('senaste_text') else '',
                   'handlingar': (k or {}).get('handlingar', [])[:6]})
    return ut


def starta_intag(url, not_):
    import os
    import shutil
    import subprocess
    if not re.fullmatch(r'https?://[^\s]{4,500}', url or ''):
        raise ValueError('ange en http- eller https-adress')
    if sum(1 for x in intag_lista() if x['pagar']) >= 2:
        raise ValueError('två intag pågår redan; vänta tills ett är klart')
    claude = shutil.which('claude') or str(Path.home() / '.local/bin/claude')
    INTAG.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    meta = INTAG / ('intag-%s.json' % stamp)
    meta.write_text(json.dumps({'url': url, 'not': not_ or '', 'tid': nu()}, ensure_ascii=False) + '\n', encoding='utf-8')
    prompt = ('Använd skillen kirurg (.claude/skills/kirurg/SKILL.md) på: %s\n\nÄgarens not: %s\n\nDu startades från dashboarden; '
              'ingen människa svarar under körningen. Följ skillen hela vägen: registret, och vid "ta in" eller "prova A/B" '
              'backloggen. Avsluta med domen och skälet i högst fyra meningar.') % (url, (not_ or '').strip() or 'ingen')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_')}
    # Sessionen ärver ägarens egna allow-regler (git push, rm -f, gh pr …); kirurgen får committa registret och
    # backloggen enligt skillen, men det som aldrig behövs nekas. Nekande går före tillåtande.
    args = [claude, '-p', '--max-turns', '150', '--permission-mode', 'dontAsk', '--output-format', 'stream-json', '--verbose',
            '--allowedTools', *INTAG_VERKTYG,
            '--disallowedTools', 'Bash(rm *)', 'Bash(gh pr *)', 'Bash(git rebase *)', 'Bash(git checkout *)', 'Bash(git reset *)',
            'Bash(git worktree *)', 'Bash(git config *)', 'Bash(git push --force *)', 'Bash(git push -f *)']
    if os.environ.get('NWP_KIRURG_MODELL'):
        args += ['--model', os.environ['NWP_KIRURG_MODELL']]
    with open(meta.with_suffix('.jsonl'), 'wb') as ut:
        p = subprocess.Popen(args, cwd=str(ROOT), env=env, stdin=subprocess.PIPE, stdout=ut, stderr=subprocess.STDOUT, start_new_session=True)
        p.stdin.write(prompt.encode())
        p.stdin.close()
    return {'id': meta.stem}


# --- http ---

VISNING = {}


def visa(slug):
    dist = KUNDER / slug / 'sajt' / 'dist'
    if not (dist / 'index.html').is_file():
        return None
    if slug not in VISNING:
        srv = Server(dist)
        srv.__enter__()
        VISNING[slug] = srv
    return VISNING[slug].url + '/'


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def skicka(self, kod, kropp, typ='application/json; charset=utf-8', extra=None):
        if isinstance(kropp, (dict, list)):
            kropp = json.dumps(kropp, ensure_ascii=False).encode()
        elif isinstance(kropp, str):
            kropp = kropp.encode()
        self.send_response(kod)
        self.send_header('Content-Type', typ)
        self.send_header('Content-Length', str(len(kropp)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(kropp)

    def do_GET(self):
        vag = unquote(urlsplit(self.path).path)
        try:
            if vag in ('/', '/index.html'):
                return self.skicka(200, (Path(__file__).parent / 'index.html').read_bytes(), 'text/html; charset=utf-8')
            if vag == '/api/oversikt':
                bk = backloggen()
                return self.skicka(200, {'byggen': byggen(), 'lardomar': md(las_text(ROOT / 'LARDOMAR.md')),
                                         'backlog_vilande': sum(1 for p in bk if p.get('status') == 'vilande'),
                                         'intag_pagar': sum(1 for x in intag_lista() if x['pagar']), 'tid': nu()})
            if vag == '/api/backlog':
                return self.skicka(200, backloggen())
            if vag == '/api/kirurg':
                return self.skicka(200, {'intag': intag_lista(), 'register': register()})
            m = re.match(r'^/api/bygge/([a-z0-9-]{2,60})$', vag)
            if m and (KUNDER / m.group(1)).is_dir():
                return self.skicka(200, bygge(m.group(1)))
            m = re.match(r'^/visa/([a-z0-9-]{2,60})$', vag)
            if m:
                url = visa(m.group(1))
                if url:
                    return self.skicka(302, '', extra={'Location': url})
                return self.skicka(404, '<p>Sajten är inte byggd än.</p>', 'text/html; charset=utf-8')
            m = re.match(r'^/fil/((?:kunder|underlag)/[a-z0-9-]{2,60}/.+)$', vag)
            if m:
                p = (ROOT / m.group(1)).resolve()
                if (p.is_relative_to(KUNDER.resolve()) or p.is_relative_to(UNDERLAG.resolve())) and p.is_file() \
                        and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.md', '.json', '.txt', '.log'):
                    typ = mimetypes.guess_type(p.name)[0] or 'text/plain'
                    if typ.startswith('text/') or typ.endswith('json'):
                        typ += '; charset=utf-8'
                    return self.skicka(200, p.read_bytes(), typ)
            return self.skicka(404, {'fel': 'finns inte'})
        except Exception as e:  # dashboarden ska visa felet, inte dö
            return self.skicka(500, {'fel': '%s: %s' % (type(e).__name__, e)})

    def do_POST(self):
        vag = urlsplit(self.path).path
        ursprung = self.headers.get('Origin') or ''
        vard = self.headers.get('Host') or ''
        if urlsplit(ursprung).netloc != vard:
            return self.skicka(403, {'fel': 'fel ursprung'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            data = json.loads(self.rfile.read(min(n, 60000)) or b'{}')
            m = re.match(r'^/api/dom/([a-z0-9-]{2,60})$', vag)
            if m:
                return self.skicka(200, spara_dom(m.group(1), data))
            m = re.match(r'^/api/backlog/(B-[a-z0-9-]+)/status$', vag)
            if m:
                if data.get('status') not in ('avvisad', 'vilande'):
                    raise ValueError('från dashboarden går bara avvisad eller vilande')
                meta = bl.satt_status(m.group(1), data['status'], not_=(data.get('not') or 'ändrad av ägaren i dashboarden'))
                return self.skicka(200, {'id': meta['id'], 'status': meta['status']})
            if vag == '/api/kirurg':
                return self.skicka(200, starta_intag((data.get('url') or '').strip(), data.get('not')))
            return self.skicka(404, {'fel': 'finns inte'})
        except (ValueError, json.JSONDecodeError, OSError) as e:
            return self.skicka(400, {'fel': str(e)})


def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('--port', type=int, default=4771)
    a = p.parse_args()
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    print('Dashboard: http://127.0.0.1:%d' % a.port, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
