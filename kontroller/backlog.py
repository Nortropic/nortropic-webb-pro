#!/usr/bin/env python3
"""backlog.py — den vilande backloggen: en markdownfil per post i backlog/.

    .venv/bin/python kontroller/backlog.py ny --kalla kirurg|dom|bygge|bevakning --titel T --varfor V [--forslag F] [--klart K]
        [--steg S] [--sar S] [--kallref R] [--prio hog|normal]
    .venv/bin/python kontroller/backlog.py lista [--status vilande] [--json]
    .venv/bin/python kontroller/backlog.py visa ID
    .venv/bin/python kontroller/backlog.py status ID vilande|pagar|klar|avvisad [--commit SHA] [--not TEXT]

Poster skapas alltid vilande, automatiskt av kirurgen (dom "ta in" eller "prova A/B"), av dashboarden när ägaren
dömer ett bygge, och av en byggkörning som hittar en brist i verktyg, skill eller kunskap. Ingen post genomförs av
sig själv: ägaren startar en session och säger "implementera enligt backlog" (skillen backlog).
Exit 0 = klart; 2 = fel i anropet.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPP = ROOT / 'backlog'
STATUS = ('vilande', 'pagar', 'klar', 'avvisad')
KALLOR = ('kirurg', 'dom', 'bygge', 'bevakning')
FALT = ('id', 'status', 'kalla', 'kallref', 'skapad', 'prio', 'steg', 'sar', 'commit', 'andrad')


def _slug(t):
    t = t.lower().translate(str.maketrans('åäöéü', 'aaoeu'))
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:48].strip('-') or 'post'


def las(p):
    text = Path(p).read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.S)
    meta, kropp = {}, text
    if m:
        for rad in m.group(1).splitlines():
            k, _, v = rad.partition(':')
            if k.strip():
                meta[k.strip()] = v.strip()
        kropp = m.group(2)
    titel = re.search(r'^# (.+)$', kropp, re.M)
    meta['titel'] = titel.group(1).strip() if titel else meta.get('id', Path(p).stem)
    meta['kropp'] = kropp
    meta['fil'] = str(Path(p).relative_to(ROOT))
    return meta


def skriv(meta, kropp):
    rader = ['---'] + ['%s: %s' % (k, meta[k]) for k in FALT if meta.get(k) not in (None, '')] + ['---', '']
    (MAPP / (meta['id'] + '.md')).write_text('\n'.join(rader) + kropp.lstrip('\n'), encoding='utf-8')


def lista(status=None):
    if not MAPP.is_dir():
        return []
    poster = [las(p) for p in sorted(MAPP.glob('B-*.md'))]
    if status:
        poster = [p for p in poster if p.get('status') == status]
    return sorted(poster, key=lambda p: (p.get('prio') != 'hog', p.get('skapad', ''), p['id']))


def ny(kalla, titel, varfor, forslag=None, klart=None, steg=None, sar=None, kallref=None, prio='normal'):
    if kalla not in KALLOR:
        raise ValueError('kalla ska vara en av ' + ', '.join(KALLOR))
    if not titel.strip() or not varfor.strip():
        raise ValueError('titel och varför krävs')
    MAPP.mkdir(exist_ok=True)
    dag = datetime.now(timezone.utc).strftime('%Y%m%d')
    bas = 'B-%s-%s' % (dag, _slug(titel))
    pid, n = bas, 2
    while (MAPP / (pid + '.md')).exists():
        pid, n = '%s-%d' % (bas, n), n + 1
    meta = {'id': pid, 'status': 'vilande', 'kalla': kalla, 'kallref': kallref, 'prio': prio if prio in ('hog', 'normal') else 'normal',
            'skapad': datetime.now(timezone.utc).strftime('%Y-%m-%d'), 'steg': steg, 'sar': sar}
    kropp = '# %s\n\n**Varför:** %s\n' % (titel.strip(), varfor.strip())
    if forslag:
        kropp += '\n**Förslag:** %s\n' % forslag.strip()
    if klart:
        kropp += '\n**Klart när:** %s\n' % klart.strip()
    skriv(meta, kropp)
    return pid


def satt_status(pid, status, commit=None, not_=None):
    if status not in STATUS:
        raise ValueError('status ska vara en av ' + ', '.join(STATUS))
    p = MAPP / (pid + '.md')
    if not re.fullmatch(r'B-[a-z0-9-]+', pid) or not p.is_file():
        raise ValueError('okänd post: ' + pid)
    meta = las(p)
    kropp = meta.pop('kropp')
    meta['status'] = status
    meta['andrad'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    if commit:
        meta['commit'] = commit
    if not_:
        kropp = kropp.rstrip('\n') + '\n\n**%s (%s):** %s\n' % (status.capitalize(), meta['andrad'][:10], not_.strip())
    skriv(meta, kropp)
    return meta


def main(argv=None):
    p = argparse.ArgumentParser(prog='backlog', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    n = sub.add_parser('ny')
    n.add_argument('--kalla', required=True)
    n.add_argument('--titel', required=True)
    n.add_argument('--varfor', required=True)
    for f in ('forslag', 'klart', 'steg', 'sar', 'kallref'):
        n.add_argument('--' + f)
    n.add_argument('--prio', default='normal')
    l = sub.add_parser('lista')
    l.add_argument('--status')
    l.add_argument('--json', action='store_true')
    v = sub.add_parser('visa')
    v.add_argument('id')
    s = sub.add_parser('status')
    s.add_argument('id')
    s.add_argument('status')
    s.add_argument('--commit')
    s.add_argument('--not', dest='not_')
    a = p.parse_args(argv)
    try:
        if a.cmd == 'ny':
            print(ny(a.kalla, a.titel, a.varfor, a.forslag, a.klart, a.steg, a.sar, a.kallref, a.prio))
        elif a.cmd == 'lista':
            poster = lista(a.status)
            if a.json:
                print(json.dumps([{k: v for k, v in x.items() if k != 'kropp'} for x in poster], ensure_ascii=False, indent=1))
            else:
                for x in poster:
                    print('%-9s %-7s %-6s %s  %s' % (x.get('status'), x.get('kalla'), x.get('prio'), x['id'], x['titel']))
                if not poster:
                    print('(inga poster)')
        elif a.cmd == 'visa':
            print((MAPP / (a.id + '.md')).read_text(encoding='utf-8'))
        elif a.cmd == 'status':
            m = satt_status(a.id, a.status, a.commit, a.not_)
            print('%s: %s' % (m['id'], m['status']))
    except (ValueError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
