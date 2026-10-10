#!/usr/bin/env python3
"""Appdrivaren: startar provbyggda Nortropic.app (`npm run bygg:prov`, med provstyrningen) mot en provinstans av motorn
och styr den riktiga WKWebView:n (kunskap/desktop.md, Prov). Bara standardbiblioteket.

Appen startas med en egen datakatalog (NWP_DESKTOP_DATA), så att provet aldrig läser eller skriver ägarens inställningar,
och med upplåsningens attrapp (NWP_DESKTOP_PROV_UPPLAS=1), eftersom Touch ID inte kan tryckas av ett skript. Bilderna
tas med `screencapture -l <fönsternummer>`, bara appens eget fönster.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
ROT = DESKTOP.parent
PROVAPP = DESKTOP / 'src-tauri/target/debug/bundle/macos/Nortropic.app'
RELEASEAPP = DESKTOP / 'src-tauri/target/release/bundle/macos/Nortropic.app'


class App:
    def __init__(self, motorrot, port, app=PROVAPP, data=None, upplas_attrapp=True, miljo=None):
        self.app, self.motorrot, self.port = Path(app), Path(motorrot), port
        self.data = Path(data) if data else Path(tempfile.mkdtemp(prefix='nwp-desktop-prov-'))
        self.egen_data = data is None
        self.upplas = upplas_attrapp
        self.miljo = miljo or {}
        self.proc = None
        self.styr = None

    def registrera(self, verktyg=None):
        """Provets registrering, som första starten skulle ha gjort: motorrot, port och verktyg med absoluta sökvägar."""
        v = verktyg or {'claude': shutil.which('claude') and os.path.realpath(shutil.which('claude')) and '/opt/homebrew/bin/claude',
                        'node': '/opt/homebrew/bin/node'}
        inst = {'rot': str(self.motorrot.resolve()), 'port': self.port, 'verktyg': v, 'avslut': 'fraga', 'fonster': None, 'las_efter_min': 30}
        self.data.mkdir(parents=True, exist_ok=True)
        (self.data / 'installningar.json').write_text(json.dumps(inst), encoding='utf-8')
        os.chmod(self.data / 'installningar.json', 0o600)

    def starta(self, vanta=20):
        (self.data / 'provstyrning.json').unlink(missing_ok=True)
        env = {k: v for k, v in os.environ.items() if k in ('HOME', 'USER', 'LOGNAME', 'TMPDIR', 'LANG')}
        env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'  # som en start från Finder: ingen terminal-PATH
        env['NWP_DESKTOP_DATA'] = str(self.data)
        if self.upplas:
            env['NWP_DESKTOP_PROV_UPPLAS'] = '1'
        env.update(self.miljo)
        self.t0 = time.time()
        self.proc = subprocess.Popen([str(self.app / 'Contents/MacOS/nortropic')], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        slut = time.time() + vanta
        while time.time() < slut:
            f = self.data / 'provstyrning.json'
            if f.exists():
                try:
                    self.styr = json.loads(f.read_text())
                    break
                except ValueError:
                    pass
            time.sleep(0.1)
        if not self.styr:
            raise RuntimeError('provstyrningen startade inte (är appen byggd med --features prov?)')
        return self

    def _anrop(self, metod, vag, kropp=''):
        r = urllib.request.Request('http://127.0.0.1:%d%s' % (self.styr['port'], vag), data=kropp.encode() if metod == 'POST' else None,
                                   method=metod, headers={'X-Prov-Token': self.styr['token']})
        with urllib.request.urlopen(r, timeout=30) as s:
            return json.loads(s.read())

    def lage(self):
        return self._anrop('GET', '/lage')

    def js(self, uttryck):
        """Kör ett JavaScript-uttryck i huvudfönstrets riktiga WKWebView och ger värdet (JSON)."""
        return self._anrop('POST', '/eval', uttryck).get('varde')

    def meny(self, id_):
        return self._anrop('POST', '/meny', id_)

    def navigera(self, url):
        return self._anrop('POST', '/navigera', url)

    def stang(self):
        return self._anrop('POST', '/stang')

    def visa(self):
        return self._anrop('POST', '/visa')

    def fonster(self, **kw):
        return self._anrop('POST', '/fonster', json.dumps(kw))

    def vanta(self, villkor, tid=20, steg=0.25, text='villkoret'):
        slut = time.time() + tid
        senast = None
        while time.time() < slut:
            try:
                senast = villkor()
                if senast:
                    return senast
            except Exception as e:  # noqa: BLE001 — webvyn kan ladda om mitt i
                senast = e
            time.sleep(steg)
        raise TimeoutError('%s uppfylldes inte inom %s s (senast: %r)' % (text, tid, senast))

    def vanta_url(self, borjar, tid=20):
        return self.vanta(lambda: (self.lage().get('url') or '').startswith(borjar) and self.lage(), tid, text='adressen ' + borjar)

    def bild(self, sokvag):
        n = self.lage()['fonsternummer']
        Path(sokvag).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['/usr/sbin/screencapture', '-x', '-o', '-l', str(n), str(sokvag)], check=True)
        return sokvag

    def avsluta(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.egen_data:
            shutil.rmtree(self.data, ignore_errors=True)
