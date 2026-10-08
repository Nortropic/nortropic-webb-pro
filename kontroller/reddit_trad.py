#!/usr/bin/env python3
"""reddit_trad.py — en Reddit-tråd som text ur trådens RSS (Atom), som går utan inloggning: inlägget och kommentarerna med
författare och tid, för kirurgens bedömning (backloggen 2026-10-03: sidan spärrar, RSS:en gav 429 vid 10 s och gick vid 20 s,
så spanarens takt per värd gäller). Bara GET mot reddit.com; inget sparas utöver utfilen.

    .venv/bin/python kontroller/reddit_trad.py <trådens adress> [--ut FIL]
"""
import argparse
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

ATOM = '{http://www.w3.org/2005/Atom}'


def till_text(data):
    """Atom-flödet (bytes) som Markdown: rubrik, sedan varje inlägg med författare, tid och text utan HTML."""
    rot = ET.fromstring(data)
    rader = ['# ' + ' '.join((rot.findtext(ATOM + 'title') or 'Reddit-tråd').split()), '']
    for e in rot.findall(ATOM + 'entry'):
        namn = (e.find(ATOM + 'author/' + ATOM + 'name').text if e.find(ATOM + 'author/' + ATOM + 'name') is not None else '') or ''
        tid = (e.findtext(ATOM + 'updated') or e.findtext(ATOM + 'published') or '')[:16]
        innehall = e.findtext(ATOM + 'content') or e.findtext(ATOM + 'summary') or ''
        text = html.unescape(re.sub(r'<[^>]+>', ' ', html.unescape(innehall)))
        text = re.sub(r'\s+', ' ', text).strip()
        lank = next((l.get('href') for l in e.findall(ATOM + 'link') if l.get('href')), '')
        rader += ['## %s (%s)' % (' '.join((e.findtext(ATOM + 'title') or namn or 'inlägg').split()), ', '.join(x for x in (namn, tid) if x)), '', text or '(tomt)', '']
        if lank:
            rader += ['<' + lank + '>', '']
    return '\n'.join(rader).rstrip() + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(prog='reddit_trad', description=__doc__.split('\n\n')[0])
    p.add_argument('adress')
    p.add_argument('--ut')
    a = p.parse_args(argv)
    u = urlsplit(a.adress)
    if u.scheme != 'https' or not (u.hostname or '').lower().removeprefix('www.').endswith('reddit.com'):
        print('adressen ska vara en https-adress hos reddit.com'); return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import spana
    adress = a.adress.split('?', 1)[0].rstrip('/')
    adress = adress if adress.endswith('.rss') else adress + '/.rss'
    data = spana.Hamtare().hamta(adress, spana.BYTE_FLODE)
    text = till_text(data)
    if a.ut:
        Path(a.ut).parent.mkdir(parents=True, exist_ok=True)
        Path(a.ut).write_text(text, encoding='utf-8')
        print('skrev %s (%d tecken)' % (a.ut, len(text)))
    else:
        print(text, end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
