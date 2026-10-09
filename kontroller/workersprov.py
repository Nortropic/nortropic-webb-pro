#!/usr/bin/env python3
"""workersprov.py — kundrepots Worker i Cloudflares riktiga runtime (workerd), lokalt: Wrangler startar Workern med de
byggda sidorna, en lokal D1 med kundrepots schema och en lokal R2, och provet skickar riktiga HTTP-begäranden.
Mejltjänsten är en attrapp på 127.0.0.1 (märkt som sådan), aldrig Resend. Inget konto, ingen nyckel och inget nät utåt.

Prövar (uppdraget 2026-10-09: M02, M04 lokalt, M05, M13, M15, T14, T15, T16):
- statiska sidor, säkerhetshuvudena ur _headers och 404-sidan;
- att Workerns kod, konfiguration, D1-schemat och miljöfiler inte kan hämtas som publika filer;
- förfrågan: validering (422, 413), skräpfälla, annan Origin (403), lagring i D1 och bilaga i R2 före aviseringen,
  mejlkvittot i utkorgen, ett fallet mejl som sparad och följbar (fel i utkorgen), dubbelt inskick som ett ärende;
- förhandsvisningen (miljön forhandsvisning): inget sparas och inget skickas.

Det här är ett lokalt runtimeprov. Det bevisar inte drift hos Cloudflare (konto, domän, Access, verkliga D1/R2), som
redovisas som väntande fjärrprov (M16).

    .venv/bin/python kontroller/workersprov.py <kundrepo> [--json]
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korregister  # noqa: E402

FORBJUDNA = ('/worker/index.js', '/wrangler.jsonc', '/migrations/0001_forfragningar.sql', '/.dev.vars', '/package.json', '/package-lock.json',
             '/_headers', '/README.md', '/CLAUDE.md')


def ledig_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Mejlattrapp:
    """Resend-attrapp på 127.0.0.1: tar emot e-postanropet och svarar med ett kvitto, eller nekar (422) när fel=True."""
    def __init__(self):
        self.anrop, self.fel = [], False
        attrapp = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                kropp = self.rfile.read(int(self.headers.get('content-length') or 0))
                attrapp.anrop.append({'auth': self.headers.get('authorization'), 'kropp': json.loads(kropp or b'{}')})
                if attrapp.fel:
                    self.send_response(422)  # nekat av mejltjänsten: utkorgen visar fel (ett serverfel vore okänt utfall)
                    self.end_headers()
                    return
                ut = json.dumps({'id': 'attrapp-%d' % len(attrapp.anrop)}).encode()
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(ut)
        self.srv = ThreadingHTTPServer(('127.0.0.1', 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = 'http://127.0.0.1:%d/emails' % self.srv.server_port

    def stang(self):
        self.srv.shutdown()
        self.srv.server_close()


def miljo(tmp):
    """Wrangler utan ägarens inloggning, konto, nycklar eller mätdata: konfiguration och logg i provets katalog."""
    m = {k: os.environ[k] for k in ('PATH', 'HOME', 'USER', 'LANG', 'TMPDIR') if k in os.environ}
    m.update(WRANGLER_SEND_METRICS='false', XDG_CONFIG_HOME=str(tmp / 'xdg'), WRANGLER_LOG_PATH=str(tmp / 'wrangler-logg'),
             CI='1', NO_COLOR='1')  # loggnivån lämnas: d1 execute --json skriver svaret på loggens vanliga nivå
    return m


def wrangler(repo, args, tmp, timeout=180, bara_stdout=False):
    r = subprocess.run([str(repo / 'node_modules' / '.bin' / 'wrangler'), *args], cwd=repo, env=miljo(tmp),
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or '') if bara_stdout else (r.stdout or '') + (r.stderr or '')


def d1(repo, tmp, sql):
    rc, ut = wrangler(repo, ['d1', 'execute', 'DB', '--local', '--persist-to', str(tmp / 'tillstand'), '--json', '--command', sql], tmp, bara_stdout=True)
    start = min([i for i in (ut.find('['), ut.find('{')) if i >= 0] or [-1])
    if rc or start < 0:
        raise RuntimeError('d1 execute föll (%d): %s' % (rc, ut[-400:]))
    data = json.loads(ut[start:])
    data = data if isinstance(data, list) else [data]
    return data[0].get('results') or []


class Worker:
    """wrangler dev --local: Workern i workerd med de byggda sidorna och lokala D1/R2 i provets katalog."""
    def __init__(self, repo, tmp, env=None, vars_=None):
        self.port = ledig_port()
        args = ['dev', '--local', '--ip', '127.0.0.1', '--port', str(self.port), '--persist-to', str(tmp / 'tillstand'),
                '--inspector-port', str(ledig_port()), '--show-interactive-dev-session=false']
        if env:
            args += ['--env', env]
        for k, v in (vars_ or {}).items():
            args += ['--var', '%s:%s' % (k, v)]
        self.logg = open(tmp / ('wrangler-dev-%s.log' % (env or 'produktion')), 'w')
        self.p = subprocess.Popen([str(repo / 'node_modules' / '.bin' / 'wrangler'), *args], cwd=repo, env=miljo(tmp),
                                  stdout=self.logg, stderr=subprocess.STDOUT, start_new_session=True)
        self.bas = 'http://127.0.0.1:%d' % self.port
        for _ in range(120):
            if self.p.poll() is not None:
                raise RuntimeError('wrangler dev slutade (kod %s); se %s' % (self.p.returncode, self.logg.name))
            try:
                urllib.request.urlopen(self.bas + '/', timeout=2).read()
                return
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.5)
        raise RuntimeError('wrangler dev svarade inte inom 60 s')

    def stang(self):
        import signal
        try:
            os.killpg(self.p.pid, signal.SIGTERM)
            self.p.wait(timeout=15)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(self.p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.logg.close()


class IngenOmdirigering(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPPNA = urllib.request.build_opener(IngenOmdirigering)


def begar(url, metod='GET', data=None, rubriker=None):
    req = urllib.request.Request(url, data=data, method=metod, headers=rubriker or {})
    try:
        r = OPPNA.open(req, timeout=20)
        return r.status, r.headers, r.read()  # HTTPMessage: huvudenas namn jämförs utan skiftläge, som HTTP kräver
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def multipart(falt, filer=None):
    grans = '----nwp%d' % int(time.time() * 1000)
    delar = []
    for k, v in falt.items():
        delar.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (grans, k, v)).encode())
    for k, (namn, typ, innehall) in (filer or {}).items():
        delar.append(('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\nContent-Type: %s\r\n\r\n' % (grans, k, namn, typ)).encode()
                     + innehall + b'\r\n')
    delar.append(('--%s--\r\n' % grans).encode())
    return b''.join(delar), {'Content-Type': 'multipart/form-data; boundary=%s' % grans}


PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
       b'\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')


def prova(kundrepo):
    """{fall: (ok, detalj)} för kundrepot (en export med installerade beroenden och byggd dist/)."""
    kundrepo = Path(kundrepo).resolve()
    ut, fall = {}, lambda namn, ok, detalj='': ut.__setitem__(namn, (bool(ok), str(detalj)[:300]))
    tmp = Path(korregister.egen_tmp('nwp-workersprov-', 'workersprov'))
    repo = tmp / 'repo'
    shutil.copytree(kundrepo, repo, symlinks=True, ignore=shutil.ignore_patterns('.wrangler', '.git'))
    if not (repo / 'node_modules' / '.bin' / 'wrangler').exists():
        r = subprocess.run(['npm', 'ci', '--no-audit', '--no-fund', '--ignore-scripts'], cwd=repo, capture_output=True, text=True, timeout=900)
        if r.returncode:
            raise RuntimeError('npm ci föll: %s' % (r.stdout + r.stderr)[-500:])
    if not (repo / 'dist' / 'index.html').is_file():
        import processgrans  # sajtens kod byggs bara innanför processgränsen: utan nät, skrivning bara i kopian
        rc, logg = processgrans.kor_i_katalog(repo, [repo / 'node_modules' / '.bin' / 'astro', 'build'])
        if rc or not (repo / 'dist' / 'index.html').is_file():
            raise RuntimeError('astro build föll (%d): %s' % (rc, logg[-500:]))
    attrapp = Mejlattrapp()
    workers = []
    try:
        rc, logg = wrangler(repo, ['d1', 'migrations', 'apply', 'DB', '--local', '--persist-to', str(tmp / 'tillstand')], tmp)
        fall('D1-schemat tillämpat lokalt', rc == 0, logg[-200:] if rc else 'migrations/0001_forfragningar.sql')
        w = Worker(repo, tmp, vars_={'MILJO': 'produktion', 'FORFRAGAN_TILL': 'mottagare@example.invalid',
                                     'FORFRAGAN_FRAN': 'webbplats@example.invalid', 'RESEND_API_KEY': 'attrappnyckel',
                                     'RESEND_API_URL': attrapp.url})
        workers.append(w)
        s, h, b = begar(w.bas + '/')
        fall('startsidan som statisk fil', s == 200 and 'text/html' in h.get('Content-Type', ''), s)
        fall('produktionen är inte märkt noindex', 'noindex' not in (h.get('X-Robots-Tag') or ''), h.get('X-Robots-Tag'))
        fall('säkerhetshuvudena på statiska svar (_headers)', h.get('X-Frame-Options') == 'DENY' and h.get('X-Content-Type-Options') == 'nosniff'
             and 'max-age' in h.get('Strict-Transport-Security', ''), dict(h))
        s, h, b = begar(w.bas + '/finns-inte-alls/')
        fall('404-sidan för en okänd väg', s == 404 and b'<html' in b.lower(), s)
        hamtade = [(v, begar(w.bas + v)[0]) for v in FORBJUDNA]
        fall('serverfiler och konfiguration kan inte hämtas', all(st == 404 for _, st in hamtade), hamtade)
        s, h, b = begar(w.bas + '/api/forfragan/')
        fall('GET mot mottagaren ger 405', s == 405 and h.get('Allow') == 'POST', s)
        s, h, b = begar(w.bas + '/api/okand')
        fall('okänd API-väg ger 404 från Workern', s == 404, s)
        giltig = {'namn': 'Prov Provsson', 'telefon': '070-000 00 00', 'meddelande': 'Syntetisk förfrågan för runtimeprovet.', 'fylltid': '5000'}
        data, rub = multipart(giltig)
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, {**rub, 'Origin': 'https://annan.example'})
        fall('annan Origin nekas (403) och inget sparas', s == 403 and not d1(repo, tmp, 'SELECT id FROM forfragningar'), s)
        data, rub = multipart({**giltig, 'telefon': 'abc'})
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, rub)
        fall('valideringsfel ger 422 med texten kvar', s == 422 and 'Syntetisk förfrågan' in b.decode('utf-8', 'replace')
             and 'no-store' in h.get('Cache-Control', ''), s)
        data, rub = multipart({**giltig, 'webbplats': 'robot'})
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, rub)
        fall('skräpfällan svarar som lyckat men sparar inget', s == 303 and h.get('X-Forfragan') == 'honeypot'
             and not d1(repo, tmp, 'SELECT id FROM forfragningar'), h.get('X-Forfragan'))
        stor = b'\0' * 4_500_000
        data, rub = multipart(giltig, {'bild': ('stor.png', 'image/png', stor)})
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, rub)
        fall('för stor begäran ger 413', s == 413, s)
        inskick = 'prov-inskick-0000000001'
        data, rub = multipart({**giltig, 'inskick': inskick}, {'bild': ('bild.png', 'image/png', PNG)})
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, rub)
        rader = d1(repo, tmp, "SELECT f.id, f.bilaga, f.bilaga_typ, u.status, u.mejl_id, u.forsok FROM forfragningar f JOIN utkorg u ON u.forfragan = f.id")
        fall('förfrågan sparas i D1 och aviseras: 303 /tack/', s == 303 and h.get('Location') == '/tack/' and h.get('X-Forfragan') == 'skickad'
             and len(rader) == 1 and rader[0]['status'] == 'accepterad' and rader[0]['mejl_id'] == 'attrapp-1', (s, h.get('X-Forfragan'), rader))
        mejl = attrapp.anrop[0]['kropp'] if attrapp.anrop else {}
        fall('mejlet bär bilagan och mottagaren, och nyckeln går i Authorization', mejl.get('to') == ['mottagare@example.invalid']
             and mejl.get('attachments') and attrapp.anrop[0]['auth'] == 'Bearer attrappnyckel', sorted(mejl))
        if rader and rader[0]['bilaga']:
            bucket = re.search(r'"bucket_name":\s*"([^"]+)"', (repo / 'wrangler.jsonc').read_text(encoding='utf-8')).group(1)
            rc, objlogg = wrangler(repo, ['r2', 'object', 'get', '%s/%s' % (bucket, rader[0]['bilaga']), '--local', '--persist-to', str(tmp / 'tillstand'),
                                          '--file', str(tmp / 'bilaga.bin')], tmp)
            fall('bilagan ligger privat i R2 med originalets bytes', rc == 0 and (tmp / 'bilaga.bin').read_bytes() == PNG, objlogg[-200:] if rc else rader[0]['bilaga'])
        else:
            fall('bilagan ligger privat i R2 med originalets bytes', False, 'ingen bilaga i D1')
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, rub)
        antal = d1(repo, tmp, 'SELECT count(*) AS n FROM forfragningar')[0]['n']
        fall('samma inskick igen blir ett ärende och inget nytt mejl', s == 303 and h.get('X-Forfragan') == 'dubblett' and antal == 1
             and len(attrapp.anrop) == 1, (h.get('X-Forfragan'), antal, len(attrapp.anrop)))
        attrapp.fel = True
        data, rub = multipart({**giltig, 'meddelande': 'Andra förfrågan; mejltjänsten svarar fel.'})
        s, h, b = begar(w.bas + '/api/forfragan/', 'POST', data, rub)
        fel = d1(repo, tmp, "SELECT u.status, u.forsok, u.fel FROM utkorg u JOIN forfragningar f ON f.id = u.forfragan WHERE f.meddelande LIKE 'Andra%'")
        fall('fallet mejl: sparad, 303 /mottagen/, och utkorgen visar felet för uppföljning', s == 303 and h.get('Location') == '/mottagen/'
             and fel and fel[0]['status'] == 'fel' and fel[0]['forsok'] == 1, (s, h.get('Location'), fel))
        attrapp.fel = False
        # driftens verktyg (kontroller/forfragningar.py) mot samma lokala D1 och R2 genom Wrangler: läget utan
        # personuppgifter, torrkörd gallring, och gallring när gallringsdatumet har passerat
        import forfragningar
        kor, ta_bort = forfragningar.wrangler_kor(repo, tmp / 'tillstand')
        lage = forfragningar.lage(kor)
        offentligt = json.dumps({k: v for k, v in lage.items() if not k.startswith('_')}, ensure_ascii=False)
        fall('driftens läge: per status och fallna aviseringar, utan personuppgifter', lage['status'] == {'accepterad': 1, 'fel': 1}
             and len(lage['fel']) == 1 and not lage['utgangna'] and 'Provsson' not in offentligt and 'Syntetisk förfrågan' not in offentligt, lage['status'])
        framtid = datetime.now(timezone.utc) + timedelta(days=400)
        torr = forfragningar.gallra(kor, ta_bort, nu=framtid)
        fall('gallringen är en torrkörning utan --utfor', torr == dict(torr, antal=2, bilagor=1, utfort=False)
             and d1(repo, tmp, 'SELECT count(*) AS n FROM forfragningar')[0]['n'] == 2, torr)
        gjord = forfragningar.gallra(kor, ta_bort, nu=framtid, utfor=True)
        kvar = d1(repo, tmp, 'SELECT count(*) AS n FROM forfragningar')[0]['n']
        rc_obj, _ = wrangler(repo, ['r2', 'object', 'get', '%s/%s' % (bucket, rader[0]['bilaga']), '--local', '--persist-to', str(tmp / 'tillstand'),
                                    '--file', str(tmp / 'bilaga-efter.bin')], tmp) if rader and rader[0]['bilaga'] else (0, '')
        fall('gallringen tar bort utgångna ärenden ur D1 och bilagan ur R2', gjord['utfort'] and kvar == 0
             and d1(repo, tmp, 'SELECT count(*) AS n FROM utkorg')[0]['n'] == 0 and (rc_obj != 0 or not (tmp / 'bilaga-efter.bin').exists()), (gjord, kvar, rc_obj))
        w.stang()
        workers.pop()
        fore = d1(repo, tmp, 'SELECT count(*) AS n FROM forfragningar')[0]['n']
        anrop_fore = len(attrapp.anrop)
        f = Worker(repo, tmp, env='forhandsvisning', vars_={'RESEND_API_URL': attrapp.url})
        workers.append(f)
        data, rub = multipart({**giltig, 'meddelande': 'Förfrågan i förhandsvisningen.'})
        s, h, b = begar(f.bas + '/api/forfragan/', 'POST', data, rub)
        efter = d1(repo, tmp, 'SELECT count(*) AS n FROM forfragningar')[0]['n']
        fall('förhandsvisningen sparar och skickar inget (demo)', s == 303 and h.get('X-Forfragan') == 'demo' and efter == fore
             and len(attrapp.anrop) == anrop_fore, (h.get('X-Forfragan'), efter, len(attrapp.anrop)))
        s, h, b = begar(f.bas + '/')
        fall('förhandsvisningens sidor är märkta noindex', s == 200 and 'noindex' in (h.get('X-Robots-Tag') or ''), (s, h.get('X-Robots-Tag')))
        s, h, b = begar(f.bas + '/wrangler.jsonc')
        fall('förhandsvisningen serverar inte heller konfigurationen', s == 404, s)
    finally:
        for w in workers:
            w.stang()
        attrapp.stang()
        shutil.rmtree(tmp, ignore_errors=True)
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('kundrepo')
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    ut = prova(a.kundrepo)
    if a.json:
        print(json.dumps({k: {'ok': v[0], 'detalj': v[1]} for k, v in ut.items()}, ensure_ascii=False, indent=1))
    else:
        for k, (ok, detalj) in ut.items():
            print('%s %s%s' % ('ok ' if ok else 'FEL', k, '' if ok else ': ' + detalj))
    return 0 if all(ok for ok, _ in ut.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
