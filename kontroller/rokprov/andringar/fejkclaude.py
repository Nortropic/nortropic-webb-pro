#!/usr/bin/env python3
"""Ändringsflikens provagent (kunskap/andringar.md, Proven): står i stället för claude i PTY-proven, utan modell. Den
skriver sina argument och sin arbetskatalog, ekar varje rad den får (också svenska tecken och inklistrade rader), säger
sin terminalstorlek vid SIGWINCH, svarar på SIGINT utan att avsluta, och avslutar vid raden "avsluta" eller SIGTERM."""
import json
import os
import shutil
import signal
import sys

def storlek(*_):
    s = shutil.get_terminal_size()
    print('storlek: %dx%d' % (s.columns, s.lines), flush=True)

signal.signal(signal.SIGWINCH, storlek)
signal.signal(signal.SIGINT, lambda *_: print('avbrott mottaget', flush=True))
signal.signal(signal.SIGTERM, lambda *_: (print('stoppad', flush=True), os._exit(143)))
print('fejkclaude:', json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'tty': os.isatty(0), 'term': os.environ.get('TERM'),
                                  'styrande': os.getsid(0) == os.getpid(), 'token': bool(os.environ.get('NWP_ANDRINGAR_TOKEN'))}, ensure_ascii=False), flush=True)
print('redo.', flush=True)
for rad in sys.stdin:
    rad = rad.rstrip('\n')
    if rad == 'avsluta':
        print('hej då', flush=True)
        break
    print('fick: %s' % rad, flush=True)
