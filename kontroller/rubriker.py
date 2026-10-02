#!/usr/bin/env python3
"""rubriker.py — sajtens rubriker (h1 och h2) per sida, i ordning, för rubriktestet: går sajten att förstå genom att
bara skanna rubrikerna? (OpenAI, Designing delightful frontends with GPT-5.4; Nielsen 2006 om skanning.)

    .venv/bin/python kontroller/rubriker.py --bygge kunder/<slug>/sajt/dist --ut RUBRIKER.md

Skriver bara rubrikerna, inget annat från sidan, så att en avskärmad läsare inte får mer än en skannande besökare.
"""
import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class Rubriker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rubriker, self._niva, self._buf = [], None, ''

    def handle_starttag(self, tag, attrs):
        if tag in ('h1', 'h2'):
            self._niva, self._buf = int(tag[1]), ''

    def handle_endtag(self, tag):
        if tag in ('h1', 'h2') and self._niva:
            text = ' '.join(self._buf.split())
            if text:
                self.rubriker.append((self._niva, text))
            self._niva = None

    def handle_data(self, data):
        if self._niva:
            self._buf += data + ' '


def main(argv=None):
    p = argparse.ArgumentParser(prog='rubriker', description=__doc__.split('\n\n')[0])
    p.add_argument('--bygge', required=True)
    p.add_argument('--ut', required=True)
    a = p.parse_args(argv)
    dist = Path(a.bygge)
    sidor = sorted((f for f in dist.rglob('index.html')), key=lambda f: (len(f.relative_to(dist).parts), str(f)))
    rad = ['# Rubrikerna, sida för sida', '', 'Bara h1 och h2, i den ordning de står. Inget annat från sidorna.', '']
    for f in sidor:
        rel = f.relative_to(dist).parent.as_posix()
        r = Rubriker()
        r.feed(f.read_text(encoding='utf-8', errors='replace'))
        rad += ['## Sida ' + ('/' if rel == '.' else '/%s/' % rel), '']
        rad += ['%s %s' % ('#' * (n + 1), re.sub(r'\s+', ' ', t)) for n, t in r.rubriker] or ['(inga rubriker)']
        rad.append('')
    Path(a.ut).write_text('\n'.join(rad), encoding='utf-8')
    print('skrev %s (%d sidor)' % (a.ut, len(sidor)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
