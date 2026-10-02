#!/usr/bin/env python3
"""kallnyckel.py — en källas nyckel: normaliserad adress och ett register över allt kirurgen redan sett, så att
spanaren (kontroller/spana.py) och dashboarden kan avgöra deterministiskt om en länk är bedömd.

    from kallnyckel import normalisera, nyckel, kanda_kallor
    .venv/bin/python kontroller/kallnyckel.py URL [URL …]      # skriv ut normaliserad form och om den är känd

Kända källor hämtas ur kunskap/REGISTER.md och arkivet (Källa-raderna och ursprungstabellen), .claude/skills/*/KALLA.md,
backloggens kallref, kirurgens intag-*.json (även arkiv) och kirurgen/spaning/SEDDA.json. Exit 0.
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
SPARNING = re.compile(r'^(utm_\w+|ref|ref_src|si|feature|fbclid|gclid|mc_\w+|igshid|t|s)$', re.I)
URL = re.compile(r'https?://[^\s<>()\]"\']+')
YT_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
GITHUB_REPO = re.compile(r'^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?$')


def youtube_id(u):
    s = urlsplit(u)
    host = (s.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    if host == 'youtu.be':
        cand = s.path.strip('/').split('/')[0]
        return cand if YT_ID.match(cand) else None
    if host in ('youtube.com', 'youtube-nocookie.com'):
        q = dict(parse_qsl(s.query))
        if s.path == '/watch' and YT_ID.match(q.get('v') or ''):
            return q['v']
        m = re.match(r'^/(shorts|live|embed|v)/([A-Za-z0-9_-]{11})', s.path)
        if m:
            return m.group(2)
    return None


def normalisera(u):
    """Kanonisk form: https, gemener i värden, utan www/m, fragment och spårningsparametrar, sorterad query, utan
    avslutande snedstreck och index.html. YouTube → watch?v=ID; GitHub och raw.githubusercontent → owner/repo."""
    u = (u or '').strip()
    if not u:
        return ''
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', u):
        u = 'https://' + u
    yid = youtube_id(u)
    if yid:
        return 'https://www.youtube.com/watch?v=' + yid
    s = urlsplit(u)
    host = (s.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    if host in ('github.com', 'raw.githubusercontent.com', 'gist.github.com'):
        m = GITHUB_REPO.match(s.path)
        if m and host != 'gist.github.com':
            return 'https://github.com/%s/%s' % (m.group(1).lower(), m.group(2).lower())
    vag = re.sub(r'/+', '/', s.path or '/')
    vag = re.sub(r'/index\.html?$', '/', vag, flags=re.I)
    vag = vag.rstrip('/') or ''
    q = sorted((k, v) for k, v in parse_qsl(s.query, keep_blank_values=False) if not SPARNING.match(k))
    return urlunsplit(('https', host, vag, urlencode(q), ''))


def nyckel(u):
    return hashlib.sha1(normalisera(u).encode('utf-8')).hexdigest()[:12]


def _poster_ur_register(text, var):
    """{normaliserad url: {var, datum, dom, namn}} ur ett register i markdown (### datum · namn · dom + Källa-rader)."""
    ut = {}
    for del_ in text.split('\n### ')[1:]:
        rubrik, _, kropp = del_.partition('\n')
        bitar = [b.strip() for b in rubrik.split('·')]
        datum, namn, dom = (bitar + ['', '', ''])[:3]
        if len(bitar) >= 3:
            dom = bitar[-1]
            namn = ' · '.join(bitar[1:-1])
        kalla = ''
        for rad in kropp.splitlines():
            if rad.startswith('- Källa:'):
                kalla = rad
            elif kalla and rad.startswith('  '):
                kalla += ' ' + rad.strip()
            elif kalla and rad.startswith('- '):
                break
        for url in URL.findall(kalla):
            ut.setdefault(normalisera(url.rstrip('.,;:')), {'var': var, 'datum': datum, 'dom': dom, 'namn': namn})
        m = re.search(r'(?:^|\s)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\s*\(?@', kalla)
        if m and '/' in m.group(1) and not kalla.strip().startswith('- Källa: http'):
            ut.setdefault(normalisera('https://github.com/' + m.group(1)), {'var': var, 'datum': datum, 'dom': dom, 'namn': namn})
    # ursprungstabellen överst (| namn | owner/repo | …)
    for m in re.finditer(r'^\|[^|\n]*\|\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\s*\|', text.split('\n### ')[0], re.M):
        ut.setdefault(normalisera('https://github.com/' + m.group(1)), {'var': var + ' (ursprung)', 'datum': '', 'dom': 'ta in', 'namn': m.group(1)})
    return ut


def kanda_kallor(rot=None):
    rot = Path(rot or ROOT)
    ut = {}

    def las(p):
        try:
            return p.read_text(encoding='utf-8')
        except OSError:
            return ''

    for fil in (rot / 'kunskap' / 'REGISTER.md', *sorted((rot / 'kunskap').glob('REGISTER-arkiv-*.md'))):
        for k, v in _poster_ur_register(las(fil), fil.name).items():
            ut.setdefault(k, v)
    for fil in sorted((rot / '.claude' / 'skills').glob('*/KALLA.md')):
        for url in URL.findall(las(fil)):
            ut.setdefault(normalisera(url.rstrip('.,;:)')), {'var': 'skill ' + fil.parent.name, 'datum': '', 'dom': 'ta in', 'namn': fil.parent.name})
    for fil in sorted((rot / 'backlog').glob('B-*.md')):
        t = las(fil)
        m = re.search(r'^kallref:\s*(.+)$', t, re.M)
        if m:
            ref = m.group(1).strip()
            for url in URL.findall(ref) or ([ref] if re.match(r'^[a-z0-9.-]+\.[a-z]{2,}/', ref) else []):
                ut.setdefault(normalisera(url), {'var': fil.name, 'datum': (re.search(r'^skapad:\s*(\S+)', t, re.M) or [None, ''])[1], 'dom': 'backlog', 'namn': fil.stem})
    for fil in sorted((rot / 'kirurgen').glob('intag-*.json')) + sorted((rot / 'kirurgen').glob('arkiv-*/intag-*.json')):
        try:
            d = json.loads(las(fil) or '{}')
        except ValueError:
            continue
        if d.get('url'):
            ut.setdefault(normalisera(d['url']), {'var': fil.name, 'datum': (d.get('tid') or '')[:10], 'dom': 'intag', 'namn': d['url']})
    try:
        sedda = json.loads(las(rot / 'kirurgen' / 'spaning' / 'SEDDA.json') or '{}')
    except ValueError:
        sedda = {}
    for k, v in (sedda or {}).items():
        ut.setdefault(k, {'var': 'SEDDA.json', 'datum': (v.get('tid') or '')[:10], 'dom': v.get('status') or 'sedd', 'namn': k})
    return ut


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog='kallnyckel', description=__doc__.split('\n\n')[0])
    p.add_argument('url', nargs='+')
    a = p.parse_args(argv)
    kanda = kanda_kallor()
    for u in a.url:
        n = normalisera(u)
        print('%s  %s  %s' % (nyckel(u), n, json.dumps(kanda.get(n), ensure_ascii=False) if kanda.get(n) else 'okänd'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
