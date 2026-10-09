#!/usr/bin/env python3
"""falsk_modell.py — en falsk Anthropic Messages-server för Dyad-provet (ägarens uppdrag 2026-10-09: steg 1–3; idén ur
Dyads fake-llm-server, källgenomgången C, avsnitt 5). Bara för prov: flödets sessioner når den genom provläget i
nastlad.py, som aldrig gäller i drift.

Servern tar emot det `claude -p` skickar och sparar varje förfrågan som en dump: modellen, ansträngningen, systemprompten,
meddelandena och verktygen. Bilderna sparas som media_type, antal byte och sha256 av de avkodade byten, aldrig som
base64. Nyckel- och tokenvärden sparas aldrig: bara vilken header som kom och om värdet var provets egen nyckel. Svaren är
skriptade, utan modell: läs först varje bild som uppdraget nämner och de filer provet ber om (las_ocksa), svara sedan med
StructuredOutput när sessionen har ett schema (provets svar eller ett minsta giltigt svar ur schemat), annars med text.
"""
import base64
import hashlib
import json
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PREFIX = 'sk-ant-prov-'  # provnyckelns början; nastlad.provlage släpper bara en sådan
BILD = re.compile(r'(?<![\w/.-])((?:/|[\w.-]+/)[\w./-]*\.(?:png|jpe?g|webp))\b', re.I)


def provnyckel():
    return PREFIX + secrets.token_hex(12)


def minsta(schema):
    """Ett minsta giltigt värde ur ett JSON-schema (de typer flödets scheman använder)."""
    if not isinstance(schema, dict):
        return None
    if 'enum' in schema:
        return schema['enum'][0]
    if 'const' in schema:
        return schema['const']
    for nyckel in ('anyOf', 'oneOf'):
        if schema.get(nyckel):
            return minsta(schema[nyckel][0])
    typ = schema.get('type')
    if isinstance(typ, list):
        typ = next((t for t in typ if t != 'null'), typ[0])
    if typ == 'object':
        props = schema.get('properties') or {}
        return {k: minsta(props.get(k, {})) for k in schema.get('required') or []}
    if typ == 'array':
        return [minsta(schema.get('items') or {}) for _ in range(int(schema.get('minItems') or 0))]
    if typ == 'string':
        return 'prov' + ' ' * max(0, int(schema.get('minLength') or 0) - 4)
    if typ in ('integer', 'number'):
        return schema.get('minimum', 0)
    if typ == 'boolean':
        return False
    return None


def matt(data):
    """(bredd, höjd) ur en PNG:s IHDR eller en JPEG:s SOF, annars None: en bild som Claude Code kodat om (skalat ned)
    har andra byte än filen, och måtten visar hur."""
    try:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return int.from_bytes(data[16:20], 'big'), int.from_bytes(data[20:24], 'big')
        if data[:2] == b'\xff\xd8':
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                m, n = data[i + 1], int.from_bytes(data[i + 2:i + 4], 'big')
                if m in (0xC0, 0xC1, 0xC2):
                    return int.from_bytes(data[i + 7:i + 9], 'big'), int.from_bytes(data[i + 5:i + 7], 'big')
                i += 2 + n
    except (IndexError, TypeError):
        pass
    return None


def _bilder(innehall):
    """Bildblocken i ett innehåll (också inne i verktygsresultat), ersatta av sha256 av de avkodade byten."""
    ut = []
    if isinstance(innehall, list):
        for b in innehall:
            if not isinstance(b, dict):
                continue
            if b.get('type') == 'image' and isinstance(b.get('source'), dict):
                src = b['source']
                data = base64.b64decode(src.get('data') or '') if src.get('type') == 'base64' else b''
                ut.append({'media_type': src.get('media_type'), 'byte': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            elif b.get('type') == 'tool_result':
                ut += _bilder(b.get('content'))
    return ut


def _utan_bilddata(x):
    """Kroppen som den sparas: bildernas base64 ersatt av sha256, och enhetens id ur metadata borta."""
    if isinstance(x, dict):
        if x.get('type') == 'image' and isinstance(x.get('source'), dict) and x['source'].get('type') == 'base64':
            data = base64.b64decode(x['source'].get('data') or '')
            return {'type': 'image', 'source': {'type': 'base64', 'media_type': x['source'].get('media_type'), 'byte': len(data),
                                                 'sha256': hashlib.sha256(data).hexdigest(), 'matt': matt(data)}}
        return {k: _utan_bilddata(v) for k, v in x.items() if k != 'metadata'}
    if isinstance(x, list):
        return [_utan_bilddata(v) for v in x]
    return x


def _text(innehall):
    if isinstance(innehall, str):
        return innehall
    if isinstance(innehall, list):
        return '\n'.join(_text(b.get('text') if b.get('type') == 'text' else b.get('content') if b.get('type') == 'tool_result' else '')
                         for b in innehall if isinstance(b, dict))
    return ''


class Server:
    """Med Server(ut, rot) som s: s.url och s.nyckel till provläget (NWP_FALSK_MODELL, NWP_FALSK_NYCKEL). svar: ett
    StructuredOutput-svar per sessionens schema-titel eller '*'; las_ocksa: filer (relativt rot) som modellen också
    försöker läsa, för de negativa proven."""

    def __init__(self, ut, rot, svar=None, las_ocksa=()):
        self.ut, self.rot = Path(ut), Path(rot)
        self.svar, self.las_ocksa = dict(svar or {}), list(las_ocksa)
        self.nyckel = provnyckel()
        self.nr, self.las = 0, threading.Lock()
        self.ut.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        server = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                server.dumpa(self, None)
                self.send_response(404)
                self.end_headers()

            def do_POST(self):
                n = int(self.headers.get('Content-Length') or 0)
                try:
                    body = json.loads(self.rfile.read(n) or b'{}')
                except ValueError:
                    body = {}
                server.dumpa(self, body)
                if self.path.startswith('/v1/messages/count_tokens'):
                    return server.json(self, {'input_tokens': 12})
                if not self.path.startswith('/v1/messages'):
                    self.send_response(404)
                    self.end_headers()
                    return
                server.svara(self, body)

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.url = 'http://127.0.0.1:%d' % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()
        self.httpd.server_close()

    def dumpa(self, h, body):
        with self.las:
            self.nr += 1
            nr = self.nr
        huvuden = {}
        for k, v in h.headers.items():
            k = k.lower()
            if k in ('authorization', 'x-api-key', 'cookie'):  # värdet sparas aldrig, bara vad det var
                huvuden[k] = 'provets nyckel' if self.nyckel in v else 'ett annat värde (inte sparat)'
            elif k.startswith(('x-claude-code-session-id', 'anthropic-', 'x-app', 'user-agent')):
                huvuden[k] = v
        (self.ut / ('%04d.json' % nr)).write_text(json.dumps({'nr': nr, 'tid': time.time(), 'metod': h.command, 'vag': h.path,
                                                              'huvuden': huvuden, 'body': _utan_bilddata(body)},
                                                             ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    @staticmethod
    def json(h, d):
        b = json.dumps(d).encode()
        h.send_response(200)
        h.send_header('Content-Type', 'application/json')
        h.send_header('Content-Length', str(len(b)))
        h.end_headers()
        h.wfile.write(b)

    def drag(self, body):
        """Nästa skriptade drag: ('las', [vägar]), ('svar', {...}) eller ('text', '...')."""
        meddelanden = body.get('messages') or []
        verktyg = {t.get('name'): t for t in body.get('tools') or [] if isinstance(t, dict)}
        assistent = [m for m in meddelanden if m.get('role') == 'assistant']
        anrop = [b for m in assistent for b in (m.get('content') or []) if isinstance(b, dict) and b.get('type') == 'tool_use']
        if not assistent and 'Read' in verktyg:
            forsta = next((_text(m.get('content')) for m in meddelanden if m.get('role') == 'user'), '')
            sagda = [m.group(1) for m in BILD.finditer(forsta)]
            vagar = []
            for v in sagda + self.las_ocksa:
                p = Path(v) if v.startswith('/') else self.rot / v
                if str(p) not in vagar:
                    vagar.append(str(p))
            if vagar:
                return 'las', vagar
        if 'StructuredOutput' in verktyg and not any(a.get('name') == 'StructuredOutput' for a in anrop):
            schema = verktyg['StructuredOutput'].get('input_schema') or {}
            return 'svar', self.svar.get(schema.get('title') or '', self.svar.get('*')) or minsta(schema)
        return 'text', 'PROV-SVAR'

    def svara(self, h, body):
        typ, varde = self.drag(body)
        if typ == 'las':
            block = [{'type': 'tool_use', 'id': 'toolu_prov_%02d' % i, 'name': 'Read', 'input': {'file_path': v}} for i, v in enumerate(varde)]
        elif typ == 'svar':
            block = [{'type': 'tool_use', 'id': 'toolu_prov_svar', 'name': 'StructuredOutput', 'input': varde}]
        else:
            block = [{'type': 'text', 'text': varde}]
        stopp = 'end_turn' if typ == 'text' else 'tool_use'
        modell = body.get('model') or 'okand'
        if not body.get('stream'):
            return self.json(h, {'id': 'msg_prov', 'type': 'message', 'role': 'assistant', 'model': modell, 'content': block,
                                 'stop_reason': stopp, 'stop_sequence': None, 'usage': {'input_tokens': 12, 'output_tokens': 2}})
        h.send_response(200)
        h.send_header('Content-Type', 'text/event-stream')
        h.send_header('Cache-Control', 'no-cache')
        h.end_headers()

        def sse(typ_, data):
            h.wfile.write(('event: %s\ndata: %s\n\n' % (typ_, json.dumps(data, ensure_ascii=False))).encode())

        sse('message_start', {'type': 'message_start', 'message': {'id': 'msg_prov', 'type': 'message', 'role': 'assistant', 'model': modell,
                                                                   'content': [], 'stop_reason': None, 'stop_sequence': None,
                                                                   'usage': {'input_tokens': 12, 'output_tokens': 1}}})
        for i, b in enumerate(block):
            if b['type'] == 'text':
                sse('content_block_start', {'type': 'content_block_start', 'index': i, 'content_block': {'type': 'text', 'text': ''}})
                sse('content_block_delta', {'type': 'content_block_delta', 'index': i, 'delta': {'type': 'text_delta', 'text': b['text']}})
            else:
                sse('content_block_start', {'type': 'content_block_start', 'index': i,
                                            'content_block': {'type': 'tool_use', 'id': b['id'], 'name': b['name'], 'input': {}}})
                sse('content_block_delta', {'type': 'content_block_delta', 'index': i,
                                            'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(b['input'], ensure_ascii=False)}})
            sse('content_block_stop', {'type': 'content_block_stop', 'index': i})
        sse('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': stopp, 'stop_sequence': None}, 'usage': {'output_tokens': 2}})
        sse('message_stop', {'type': 'message_stop'})
        h.wfile.flush()


def dumpar(ut, session_id=None):
    """Förfrågningarna till /v1/messages i ordning (för en session när session_id anges), sammanfattade per förfrågan:
    modellen, ansträngningen, systemprompten och användarens text som text, bilderna (sha256) och verktygsresultaten med
    fel. 'ra' är hela den sparade texten, för de negativa proven."""
    ut_ = []
    for f in sorted(Path(ut).glob('[0-9]*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        b = d.get('body') or {}
        if not str(d.get('vag', '')).startswith('/v1/messages') or 'count_tokens' in d.get('vag', ''):
            continue
        sid = d['huvuden'].get('x-claude-code-session-id')
        if session_id and sid != session_id:
            continue
        system = b.get('system')
        system = '\n'.join(x.get('text', '') for x in system if isinstance(x, dict)) if isinstance(system, list) else str(system or '')
        anvandare = [m for m in b.get('messages') or [] if m.get('role') == 'user']
        resultat = [x for m in anvandare for x in (m.get('content') or []) if isinstance(x, dict) and x.get('type') == 'tool_result']
        lasta = {x.get('id'): (x.get('input') or {}).get('file_path') for m in b.get('messages') or [] if m.get('role') == 'assistant'
                 for x in (m.get('content') or []) if isinstance(x, dict) and x.get('type') == 'tool_use' and x.get('name') == 'Read'}
        ut_.append({'nr': d['nr'], 'session': sid, 'modell': b.get('model'), 'effort': (b.get('output_config') or {}).get('effort'),
                    'system': system, 'text': '\n'.join(_text(m.get('content')) for m in anvandare),
                    'bilder': [x['source']['sha256'] for m in anvandare for x in _bildblock(m.get('content'))],
                    'resultat_fel': [x.get('is_error', False) for x in resultat], 'verktyg': [t.get('name') for t in b.get('tools') or []],
                    # varje läsning: filen, om den nekades, och bilderna den gav (sha256, mått)
                    'lasningar': [{'fil': lasta.get(x.get('tool_use_id')), 'nekad': bool(x.get('is_error')),
                                   'bilder': [{'sha256': y['source']['sha256'], 'matt': y['source'].get('matt'), 'byte': y['source'].get('byte')}
                                              for y in _bildblock(x.get('content'))]} for x in resultat if x.get('tool_use_id') in lasta],
                    'huvuden': d['huvuden'], 'ra': f.read_text(encoding='utf-8')})
    return ut_


def _bildblock(innehall):
    ut = []
    if isinstance(innehall, list):
        for b in innehall:
            if isinstance(b, dict) and b.get('type') == 'image':
                ut.append(b)
            elif isinstance(b, dict) and b.get('type') == 'tool_result':
                ut += _bildblock(b.get('content'))
    return ut
