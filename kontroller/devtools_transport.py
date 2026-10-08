#!/usr/bin/env python3
"""Liten stdio-vakt framför den låsta DevTools-MCP:n, inte en generell MCP-proxy.

Chromes tillägg gäller den vanliga profilen. new_page.isolatedContext skulle öppna
en inkognitokontext utan tillägget och nekas därför före servern. Endast profilens
nio verktyg släpps. Klient-/servermeddelanden sparas inte och vanliga anrop ändras
inte. Klientvalda skrivmål nekas; verktygens normala svar och egna temporära
artefakter påverkas inte. JSON-RPC enligt MCP:s newline-avgränsade stdio-transport; fel stänger vägen.
Startas bara genom konfigurationen som devtools.konfig() prövar.
"""
import json
from contextlib import contextmanager
import os
import selectors
import signal
import subprocess
import sys
import time
from urllib.parse import urlsplit

import nastlad

VERKTYG = frozenset(('new_page', 'emulate', 'performance_start_trace', 'performance_stop_trace',
                     'performance_analyze_insight', 'take_snapshot', 'get_css_styles',
                     'list_network_requests', 'lighthouse_audit'))
PROTOKOLL = frozenset(('initialize', 'ping', 'tools/list', 'logging/setLevel',
                       'notifications/initialized', 'notifications/cancelled'))


@contextmanager
def startskydd():
    """CLI: uppskjut avbrottet tills Popen-objektet kan städas av anroparens finally.

    Signaler blockeras inte i operativsystemet: barnet får inga ärvda blockerade
    signaler. Inga processer startas i trådar i den här startvägen.
    """
    vantande = []
    gamla = {n: signal.getsignal(n) for n in (signal.SIGTERM, signal.SIGINT)}
    try:
        for n in gamla:
            signal.signal(n, lambda signum, _frame: vantande.append(signum))
        yield
    finally:
        for n, handler in gamla.items():
            signal.signal(n, handler)
        if vantande:
            raise SystemExit(128 + vantande[0])


def nekande(d):
    if not isinstance(d, dict) or d.get('jsonrpc') != '2.0':
        raise ValueError('ogiltigt protokoll')
    method = d.get('method')
    if method != 'tools/call':
        if method is None and 'id' in d and ('result' in d or 'error' in d):
            return None  # svar på serverns protokollfråga
        return None if isinstance(method, str) and method in PROTOKOLL else 'Protokollmetoden stöds inte av inspektionsprofilen.'
    if 'id' not in d:
        raise ValueError('verktygsanrop saknar id')
    p = d.get('params')
    if not isinstance(p, dict) or not isinstance(p.get('name'), str) or p['name'] not in VERKTYG:
        return 'Verktyget ingår inte i den läsande inspektionsprofilen.'
    args = p.get('arguments', {})
    if not isinstance(args, dict):
        return 'Verktygets argument måste vara ett objekt.'
    if 'isolatedContext' in args:
        return 'Extra webbläsarkontext nekas: den saknar profilens läsande skydd.'
    if any(key in args for key in ('filePath', 'outputDirPath')):
        return 'Valda skrivmål ingår inte i den läsande inspektionsprofilen.'
    if p['name'] == 'new_page':
        url = args.get('url')
        try:
            valid = isinstance(url, str) and urlsplit(url).scheme in ('http', 'https') and bool(urlsplit(url).hostname)
        except ValueError:
            valid = False
        if not valid:
            return 'Endast http- och https-sidor kan inspekteras.'
    return None


def kor(args):
    # Ärver sessionens processgrupp; devtools.py äger och stänger hela den gruppen.
    p = None
    buffers = {'klient': b'', 'server': b''}
    slutfrist = None
    try:
        with startskydd():
            p = subprocess.Popen(['npx', *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        with selectors.DefaultSelector() as sel:
            sel.register(sys.stdin.buffer, selectors.EVENT_READ, 'klient')
            sel.register(p.stdout, selectors.EVENT_READ, 'server')
            while sel.get_map():
                if slutfrist is not None and time.monotonic() > slutfrist:
                    raise TimeoutError('servern avslutade inte')
                for key, _ in sel.select(0.2):
                    namn = key.data
                    bit = os.read(key.fd, 65536)
                    if not bit:
                        sel.unregister(key.fileobj)
                        if buffers[namn]:
                            raise ValueError('ofullständig protokollrad')
                        if namn == 'klient':
                            p.stdin.close()
                            slutfrist = time.monotonic() + 10
                        else:
                            return p.wait(timeout=10)
                        continue
                    buffers[namn] += bit
                    # Begränsat minne även vid felaktig/avbruten transport.
                    if len(buffers[namn]) > (1024 * 1024 if namn == 'klient' else 64 * 1024 * 1024):
                        raise ValueError('för stor protokollrad')
                    while b'\n' in buffers[namn]:
                        rad, buffers[namn] = buffers[namn].split(b'\n', 1)
                        d = json.loads(rad)
                        if namn == 'server':
                            sys.stdout.buffer.write(rad + b'\n'); sys.stdout.buffer.flush()
                            continue
                        fel = nekande(d)
                        if fel:
                            if 'id' not in d:
                                raise ValueError('nekat meddelande saknar id')
                            svar = {'jsonrpc': '2.0', 'id': d['id'],
                                    'result': {'isError': True, 'content': [{'type': 'text', 'text': fel}]}}
                            sys.stdout.buffer.write(json.dumps(svar).encode() + b'\n'); sys.stdout.buffer.flush()
                        else:
                            p.stdin.write(rad + b'\n'); p.stdin.flush()
            return p.wait(timeout=10)
    finally:
        if p is not None:
            if p.poll() is None:
                nastlad.doda_trad(p.pid)
            p.wait(timeout=10)
            for stream in (p.stdin, p.stdout):
                if not stream.closed:
                    stream.close()


if __name__ == '__main__':
    def avbryt(n, _frame):
        raise SystemExit(128 + n)
    signal.signal(signal.SIGTERM, avbryt)
    signal.signal(signal.SIGINT, avbryt)
    try:
        sys.exit(kor(sys.argv[1:]))
    except (OSError, ValueError, subprocess.SubprocessError):
        # Inga argument eller serverutdata får läcka till diagnostiken.
        print('DevTools-transporten avbröts: protokoll-, start- eller transportfel.', file=sys.stderr)
        sys.exit(2)
