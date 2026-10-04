#!/usr/bin/env python3
"""webbtjanst.py — byggets webbläsarverktyg utanför sandlådan, bundna till bygget.

Chromium (Playwright) kan inte starta inne i Claude Codes sandlåda: dess processer registrerar en Mach-tjänst
(bootstrap_check_in av org.chromium.Chromium.MachPortRendezvousServer.<pid>) och sandlådeprofilen avger aldrig
(allow mach-register …); mätt 2026-10-04 med seatbelt-profiler som nekar en operation i taget, och i källan
anthropic-experimental/sandbox-runtime. Därför startar kor.sh, med NWP_SANDLADA=pa, den här tjänsten utanför
sandlådan på 127.0.0.1, och prova.py, granska.py, atelje.py och webbläsarskripten delegerar till den när de körs
sandlådade (NWP_WEBBTJANST satt, HTTP_PROXY satt av sandlådan, NWP_I_TJANSTEN inte satt). Modellen märker inget:
samma kommandon, samma utskrift, samma slutkod. Krokarna (stoppvakten) körs utanför sandlådan och delegerar inte.

Gränsen flyttar till tjänsten: bara de sju verktygen och deras kända flaggor; sluggen måste vara byggets (slugvakten
binder dessutom alla utkataloger till kunder/<slug> och underlag/<slug> via NWP_SLUG); varje adress och varje tillåtet
ursprung måste ligga på localhost eller i byggets domänlista (samma lista som sandlådans proxy, kontroller/sandlada.py);
--tillat-alla och --arbetare vägras; sökvägar måste ligga under kunder/<slug>, underlag/<slug> eller /tmp/nwp-bygge-<slug>.
Nyckeln (X-Nyckel) skiljer tjänsten från annan lokal programvara; proxyvariablerna tas bort ur verktygens miljö.

    .venv/bin/python kontroller/webbtjanst.py serve --slug <slug> --kvitto <fil> [--doman d …] [--korning K] [--root R]
    .venv/bin/python kontroller/webbtjanst.py kor <verktyg> [argument …]      (manuell klient via NWP_WEBBTJANST)
"""
import argparse
import hmac
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
LOKALA = {'localhost', '127.0.0.1', '::1'}
PY = '.venv/bin/python'
VERKTYG = {
    'prova': {'kmd': (PY, '-B', 'kontroller/prova.py'), 'slug': True, 'flaggor': {'snabb': 'flagga'}},
    'granska': {'kmd': (PY, '-B', 'kontroller/granska.py'), 'slug': True,
                'flaggor': {'vanta': 'tal', 'om': 'flagga', 'torr': 'flagga', 'jamfor': 'flagga'}},
    'atelje': {'kmd': (PY, '-B', 'kontroller/atelje.py'), 'slug': True,
               'flaggor': {'vanta': 'tal', 'om': 'flagga', 'bara-domare': 'flagga'}},
    'arkivera': {'kmd': ('node', 'kontroller/webblasare/arkivera.mjs'), 'slug': False,
                 'flaggor': {'adress': 'url', 'ut': 'vag', 'intervju': 'vag', 'kund': 'text', 'sitemap': 'url'}},
    'inspektera': {'kmd': ('node', 'kontroller/webblasare/inspektera.mjs'), 'slug': False,
                   'flaggor': {'adress': 'url', 'ut': 'vag', 'vyer': 'text', 'tillat': 'ursprung', 'hemligheter': 'vag', 'kontext': 'vagar',
                               'hover': 'text', 'fokus': 'text', 'meny': 'text', 'tillstand': 'text', 'undantag-fil': 'vag'}},
    'utan-js': {'kmd': ('node', 'kontroller/webblasare/utan-js.mjs'), 'slug': False,
                'flaggor': {'adress': 'url', 'ut': 'vag', 'formular': 'text', 'sidor': 'text', 'testmarkering': 'text',
                            'formular-far-skickas': 'flagga', 'undantag-fil': 'vag'}},
    'utforska': {'kmd': ('node', 'kontroller/webblasare/utforska.mjs'), 'slug': False,
                 'flaggor': {'adress': 'url', 'ut': 'vag', 'hemligheter': 'vag', 'regression': 'vag', 'testmarkering': 'text',
                             'tillat': 'ursprung', 'vy': 'text', 'max-sidor': 'tal', 'formular-far-skickas': 'flagga', 'undantag-fil': 'vag'}},
}


def nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def tolka(argv):
    """Samma tolkning som webblasare/gemensamt.mjs args(): --k=v, --k v, --k; övrigt positionellt."""
    ut, pos, i = {}, [], 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            k, sep, v = a[2:].partition('=')
            if sep:
                ut[k] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith('--'):
                ut[k] = argv[i + 1]
                i += 1
            else:
                ut[k] = True
        else:
            pos.append(a)
        i += 1
    return ut, pos


def tillaten_vard(vard, tillatna):
    v = (vard or '').lower().rstrip('.')
    return bool(v) and (v in LOKALA or v in tillatna)


def granska_url(u, tillatna):
    try:
        s = urllib.parse.urlsplit(u)
    except ValueError:
        return 'ogiltig adress'
    if s.scheme not in ('http', 'https') or not s.hostname:
        return 'adressen måste vara http(s) med värdnamn'
    if not tillaten_vard(s.hostname, tillatna):
        return 'värden %s ligger inte i byggets domänlista' % s.hostname
    return None


def granska_vag(v, slug, root):
    if not v or '\x00' in v:
        return 'tom sökväg'
    p = Path(v) if os.path.isabs(v) else Path(root) / v
    try:
        p = p.resolve()
    except (OSError, RuntimeError):
        return 'sökvägen %s går inte att lösa upp' % v
    tillatna = [(Path(root) / 'kunder' / slug).resolve(), (Path(root) / 'underlag' / slug).resolve(), Path('/tmp/nwp-bygge-' + slug).resolve()]
    if not any(p == t or t in p.parents for t in tillatna):
        return 'sökvägen %s ligger utanför byggets kataloger' % v
    return None


def granska_anrop(verktyg, argv, slug, tillatna, root=ROOT):
    """(kommando, None) när anropet ligger inom gränsen, annars (None, skäl)."""
    spec = VERKTYG.get(verktyg) if isinstance(verktyg, str) else None
    if not spec:
        return None, 'okänt verktyg %r' % (verktyg,)
    if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
        return None, 'argumenten måste vara en lista av strängar'
    if any('\n' in a or '\x00' in a or len(a) > 2000 for a in argv):
        return None, 'argument med radbrytning, nulltecken eller över 2000 tecken'
    fl, pos = tolka(argv)
    if spec['slug']:
        if pos != [slug]:
            return None, 'sluggen måste vara byggets (%s), fick %r' % (slug, pos)
    elif pos:
        return None, 'inga positionella argument för %s: %r' % (verktyg, pos)
    for k, v in fl.items():
        typ = spec['flaggor'].get(k)
        if not typ:
            return None, 'flaggan --%s är inte tillåten för %s' % (k, verktyg)
        if typ == 'flagga':
            if v is not True:
                return None, '--%s tar inget värde' % k
            continue
        if v is True:
            return None, '--%s kräver ett värde' % k
        if typ == 'tal' and not v.isdigit():
            return None, '--%s måste vara ett tal' % k
        if typ == 'text' and len(v) > 500:
            return None, '--%s är för lång' % k
        if typ in ('url', 'ursprung'):
            for u in ([v] if typ == 'url' else [x for x in v.split(';') if x]):
                fel = granska_url(u, tillatna)
                if fel:
                    return None, '--%s: %s' % (k, fel)
        if typ in ('vag', 'vagar'):
            for x in ([v] if typ == 'vag' else [x for x in v.split(',') if x]):
                fel = granska_vag(x, slug, root)
                if fel:
                    return None, '--%s: %s' % (k, fel)
    return list(spec['kmd']) + list(argv), None


def verktygsmiljo(slug, korning=None):
    """Verktygens miljö: tjänstens egen utan proxyvariabler och Refero-nyckeln, med NWP_I_TJANSTEN och sluggen."""
    miljo = {k: v for k, v in os.environ.items() if not k.upper().endswith('_PROXY') and k != 'REFERO_MCP_TOKEN'}
    miljo['NWP_I_TJANSTEN'] = '1'
    miljo['NWP_SLUG'] = slug
    if korning:
        miljo['NWP_KORNING'] = korning
    return miljo


def kor_verktyg(kmd, miljo, root, timeout=3600):
    try:
        r = subprocess.run(kmd, cwd=str(root), env=miljo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        ut, rc = r.stdout.decode('utf-8', 'replace'), r.returncode
    except subprocess.TimeoutExpired as e:
        ut, rc = (e.stdout or b'').decode('utf-8', 'replace') + '\nwebbtjänsten: verktyget avbröts efter %d s\n' % timeout, 124
    except OSError as e:
        ut, rc = 'webbtjänsten kunde inte starta verktyget: %s\n' % e, 2
    if len(ut) > 400000:
        ut = ut[:200000] + '\n… [kapat av webbtjänsten] …\n' + ut[-200000:]
    return rc, ut


class Tjanst(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def servera(slug, kvitto, domaner=(), root=ROOT, korning=None, port=0):
    import sandlada
    root = Path(root)
    tillatna = set(sandlada.domanlista(root, domaner))
    nyckel = secrets.token_hex(16)

    class Hanterare(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def svar(self, kod, obj):
            data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
            self.send_response(kod)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def nyckel_ok(self):
            return hmac.compare_digest(self.headers.get('X-Nyckel', ''), nyckel)

        def do_GET(self):
            if not self.nyckel_ok():
                return self.svar(403, {'fel': 'fel nyckel'})
            if self.path == '/halsa':
                return self.svar(200, {'slug': slug, 'verktyg': sorted(VERKTYG)})
            self.svar(404, {'fel': 'finns inte'})

        def do_POST(self):
            if not self.nyckel_ok():
                return self.svar(403, {'fel': 'fel nyckel'})
            if self.path != '/kor':
                return self.svar(404, {'fel': 'finns inte'})
            try:
                n = int(self.headers.get('Content-Length') or 0)
                if n > 65536:
                    return self.svar(413, {'fel': 'för stor begäran'})
                b = json.loads(self.rfile.read(n).decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                return self.svar(400, {'fel': 'ogiltig JSON'})
            verktyg, argv = (b.get('verktyg'), b.get('args')) if isinstance(b, dict) else (None, None)
            kmd, fel = granska_anrop(verktyg, argv, slug, tillatna, root)
            if fel:
                print('%s NEKAT %r %r: %s' % (nu(), verktyg, argv, fel), flush=True)
                return self.svar(400, {'fel': 'webbtjänsten vägrar: ' + fel})
            t0 = time.time()
            print('%s START %s %s' % (nu(), verktyg, ' '.join(argv)), flush=True)
            rc, ut = kor_verktyg(kmd, verktygsmiljo(slug, korning), root)
            print('%s KLART %s rc=%s %.0f s' % (nu(), verktyg, rc, time.time() - t0), flush=True)
            self.svar(200, {'rc': rc, 'ut': ut})

    srv = Tjanst(('127.0.0.1', port), Hanterare)
    p = Path(kvitto)
    p.write_text('%d\n%s\n' % (srv.server_address[1], nyckel), encoding='utf-8')
    os.chmod(p, 0o600)
    print('%s webbtjänsten lyssnar på 127.0.0.1:%d för %s (domäner: %s)' % (nu(), srv.server_address[1], slug, ', '.join(sorted(tillatna)) or 'bara localhost'), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


def delegeras():
    """Sant inne i ett sandlådat bygge: tjänsten anvisad, sandlådans proxy satt, och inte redan inne i tjänsten."""
    return bool(os.environ.get('NWP_WEBBTJANST')) and not os.environ.get('NWP_I_TJANSTEN') \
        and bool(os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY'))


def via_tjanst(verktyg, argv, timeout=3600):
    """Kör verktyget genom tjänsten, skriver dess utskrift och ger dess slutkod."""
    bas = os.environ.get('NWP_WEBBTJANST', '').rstrip('/')
    data = json.dumps({'verktyg': verktyg, 'args': list(argv)}).encode('utf-8')
    req = urllib.request.Request(bas + '/kor', data=data, headers={'Content-Type': 'application/json', 'X-Nyckel': os.environ.get('NWP_WEBBTJANST_NYCKEL', '')})
    oppnare = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # localhost, aldrig via proxyn
    try:
        with oppnare.open(req, timeout=timeout) as r:
            svar = json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print('webbtjänsten nekade (%s): %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]), file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print('webbtjänsten nås inte (%s): %s' % (bas, e), file=sys.stderr)
        return 2
    sys.stdout.write(svar.get('ut', ''))
    sys.stdout.flush()
    return int(svar.get('rc', 1))


def main(argv=None):
    p = argparse.ArgumentParser(prog='webbtjanst', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='kmd', required=True)
    s = sub.add_parser('serve')
    s.add_argument('--slug', required=True)
    s.add_argument('--kvitto', required=True, help='fil som får port och nyckel (0600)')
    s.add_argument('--doman', action='append', default=[])
    s.add_argument('--korning', default=None)
    s.add_argument('--root', default=None)
    s.add_argument('--port', type=int, default=0)
    k = sub.add_parser('kor')
    k.add_argument('verktyg')
    k.add_argument('argument', nargs=argparse.REMAINDER)
    a = p.parse_args(argv)
    if a.kmd == 'serve':
        servera(a.slug, a.kvitto, a.doman, Path(a.root) if a.root else ROOT, a.korning, a.port)
        return 0
    return via_tjanst(a.verktyg, a.argument)


if __name__ == '__main__':
    sys.exit(main())
