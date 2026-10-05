#!/usr/bin/env python3
"""refero_mcp.py — direkt anslutning till Referos MCP-server (JSON-RPC över HTTP), utan språkmodell: för
startkontrollens funktionsprov och stilpaketets hämtning av en vald stil (kontroller/startkontroll.py,
kontroller/stilpaket.py). Nyckeln läses ur ägarens hemlighetsmapp och skrivs aldrig ut eller loggas; anropen går direkt
till api.refero.design utan proxyvariabler, och bilderna bara från Referos bildvärd.

Bara id:n och allmänna sökfrågor skickas: kundens uppgifter når aldrig tjänsten (BESLUT 2026-10-05, punkt 4).
"""
import json
import urllib.request
from pathlib import Path

URL = 'https://api.refero.design/mcp'
NYCKELFIL = Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'refero.env'
BILDVARD = 'images.refero.design'


class ReferoFel(Exception):
    pass


def nyckel(fil=None):
    fil = Path(fil or NYCKELFIL)
    try:
        for rad in fil.read_text(encoding='utf-8').splitlines():
            if rad.startswith('REFERO_MCP_TOKEN='):
                v = rad.split('=', 1)[1].strip().strip('"\'')
                if v:
                    return v
    except OSError:
        pass
    raise ReferoFel('Referos nyckel saknas (%s)' % fil)


class Klient:
    def __init__(self, fil=None, url=URL, timeout=90):
        self.huvuden = {'Authorization': 'Bearer ' + nyckel(fil), 'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'}
        self.url, self.timeout, self.sid, self.n = url, timeout, None, 0
        self.opp = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _post(self, kropp, svar=True):
        h = dict(self.huvuden)
        if self.sid:
            h['Mcp-Session-Id'] = self.sid
        req = urllib.request.Request(self.url, data=json.dumps(kropp).encode(), headers=h, method='POST')
        try:
            with self.opp.open(req, timeout=self.timeout) as r:
                self.sid = r.headers.get('Mcp-Session-Id') or self.sid
                typ, data = r.headers.get('Content-Type') or '', r.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001 — felet beskrivs utan huvudena (nyckeln)
            raise ReferoFel('%s: %s' % (type(e).__name__, str(e)[:160]))
        if not svar:
            return None
        if 'text/event-stream' in typ:
            ut = None
            for rad in data.splitlines():
                if rad.startswith('data:'):
                    try:
                        d = json.loads(rad[5:].strip())
                    except ValueError:
                        continue
                    if d.get('id') == kropp.get('id'):
                        ut = d
            return ut
        return json.loads(data) if data.strip() else None

    def anrop(self, metod, params=None):
        self.n += 1
        d = self._post({'jsonrpc': '2.0', 'id': self.n, 'method': metod, 'params': params or {}})
        if not isinstance(d, dict) or d.get('error'):
            raise ReferoFel('%s gav fel: %s' % (metod, str((d or {}).get('error'))[:200]))
        return d.get('result') or {}

    def starta(self):
        r = self.anrop('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                      'clientInfo': {'name': 'nortropic-webb-pro', 'version': '1'}})
        self._post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, svar=False)
        return r

    def verktyg(self):
        return [x.get('name') for x in (self.anrop('tools/list').get('tools') or [])]

    def kalla(self, namn, args):
        """Verktygets textsvar (JSON-text när response_format är json); ReferoFel när verktyget svarar med fel."""
        r = self.anrop('tools/call', {'name': namn, 'arguments': args})
        text = ''.join(d.get('text', '') for d in r.get('content') or [] if d.get('type') == 'text')
        if r.get('isError'):
            raise ReferoFel('%s: %s' % (namn, text[:200]))
        return text

    def json(self, namn, args):
        return json.loads(self.kalla(namn, dict(args, response_format='json')))


def ladda_bild(url, mal, max_byte=8 * 1024 * 1024):
    """En bild från Referos bildvärd till mal (filändelsen efter innehållet). Ger filen; ReferoFel annars."""
    import urllib.parse
    d = urllib.parse.urlsplit(url)
    if d.scheme != 'https' or (d.hostname or '').lower() != BILDVARD:
        raise ReferoFel('bilden ligger inte på %s' % BILDVARD)
    opp = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opp.open(urllib.request.Request(url, headers={'User-Agent': 'nortropic-webb-pro'}), timeout=60) as r:
            data = r.read(max_byte + 1)
    except Exception as e:  # noqa: BLE001
        raise ReferoFel('bilden gick inte att hämta: %s' % str(e)[:160])
    if len(data) > max_byte or not data.startswith((b'\xff\xd8\xff', b'\x89PNG', b'RIFF')):
        raise ReferoFel('svaret är ingen bild (eller för stort)')
    andelse = '.jpg' if data.startswith(b'\xff\xd8') else '.png' if data.startswith(b'\x89PNG') else '.webp'
    fil = Path(str(mal) + andelse)
    fil.parent.mkdir(parents=True, exist_ok=True)
    fil.write_bytes(data)
    return fil


if __name__ == '__main__':
    k = Klient()
    k.starta()
    print('\n'.join(k.verktyg()))
