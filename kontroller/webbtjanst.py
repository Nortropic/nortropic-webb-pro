#!/usr/bin/env python3
"""webbtjanst.py — byggets webbläsarverktyg utanför sandlådan, bundna till bygget.

Chromium (Playwright) kan inte starta inne i Claude Codes sandlåda: dess processer registrerar en Mach-tjänst
(bootstrap_check_in av org.chromium.Chromium.MachPortRendezvousServer.<pid>) och sandlådeprofilen avger aldrig
(allow mach-register …); mätt 2026-10-04 med seatbelt-profiler som nekar en operation i taget, och i källan
anthropic-experimental/sandbox-runtime. Därför startar kor.sh, med NWP_SANDLADA=pa, den här tjänsten utanför
sandlådan på 127.0.0.1. Bara avgränsade webbläsaroperationer delegeras (Codex R23): de fyra webbläsarskripten,
lighthouse och granskarnas sessioner (granska.py --arbetare, --jamfor), som körs med egen sandlåda. Byggsteg (npm
install, npm run build, servering av dist/) och byggets egen modellprocess stannar i sandlådan: prova.py körs därinne
och bara dess webbläsarsteg går via tjänsten; ateljén stöds inte i sandlådat läge än. Verktygen delegerar själva när de
körs sandlådade (NWP_WEBBTJANST satt, HTTP_PROXY satt av sandlådan, NWP_I_TJANSTEN inte satt). Krokarna (stoppvakten)
körs utanför sandlådan och delegerar inte.

Gränsen i tjänsten: bara verktygen i VERKTYG med kända flaggor; sluggen måste vara byggets (slugvakten binder dessutom
utkatalogerna via NWP_SLUG); varje adress och tillåtet ursprung kanoniseras strikt (bara http(s), inget användarnamn,
inga omvända snedstreck eller blanktecken, värdnamn i IDNA-form) och måste ligga på localhost eller i byggets domänlista
(samma lista som sandlådans proxy); verktygen får samma lista i NWP_NAT_TILLATNA och webbläsarhjälparen verkställer den
per anrop, också vid omdirigering. --tillat-alla vägras; --formular-far-skickas bara mot provets lokala mottagare;
sökvägar under kunder/<slug>, underlag/<slug>, /tmp/nwp-bygge-<slug> eller granskarnas /tmp/nwp-granskning/<slug>-*.
Nyckeln (X-Nyckel) skiljer tjänsten från annan lokal programvara; proxyvariablerna tas bort ur verktygens miljö.

    .venv/bin/python kontroller/webbtjanst.py serve --slug <slug> --kvitto <fil> [--doman d …] [--korning K] [--root R]
    .venv/bin/python kontroller/webbtjanst.py kor <verktyg> [argument …]      (manuell klient via NWP_WEBBTJANST)
"""
import argparse
import hmac
import re
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
GRANSKNINGSROT = Path('/tmp/nwp-granskning')  # granska.ARBETSROT: granskarnas arbetskataloger <slug>-runda-NN-n
VERKTYG = {
    # granska: bara arbetaren (granskarnas sessioner, egen sandlåda) och jämförelsen; drivaren körs i byggets sandlåda
    'granska': {'kmd': (PY, '-B', 'kontroller/granska.py'), 'slug': 'granska',
                'flaggor': {'arbetare': 'granskningsvag', 'jamfor': 'flagga'}},
    'lighthouse': {'kmd': ('node', 'kontroller/lighthouse.mjs'), 'slug': False,
                   'flaggor': {'url': 'url', 'sidor': 'text', 'ut': 'vag', 'omgangar': 'tal', 'enheter': 'text'}},
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


def idna(vard):
    """Värdnamn i IDNA-form (små bokstäver, punycode), eller None när det inte går."""
    v = (vard or '').strip().rstrip('.').lower()
    try:
        return v.encode('idna').decode('ascii') if v else None
    except UnicodeError:
        return None


def tillatna_varden(domaner):
    """Domänlistan i IDNA-form; '*.x' täcker varje underdomän till x."""
    ut = set()
    for d in domaner:
        d = (d or '').strip().lower()
        if d.startswith('*.'):
            k = idna(d[2:])
            if k:
                ut.add('*.' + k)
        else:
            k = idna(d)
            if k:
                ut.add(k)
    return ut


def tillaten_vard(vard, tillatna):
    v = idna(vard)
    if not v:
        return False
    if v in LOKALA or v in tillatna:
        return True
    return any(v.endswith('.' + m[2:]) or v == m[2:] for m in tillatna if m.startswith('*.'))


VARDNAMN = re.compile(r'^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?)*$')


def kanon_url(u, tillatna):
    """(kanonisk adress, None) eller (None, skäl). Strikt: bara http(s), inget användarnamn eller lösenord, inga
    omvända snedstreck, blanktecken eller styrtecken, värdnamn i IDNA-form; Python och Node ska läsa samma värd
    (Codex R23, F5: http://reference.example\\@localhost/ tolkas olika av urlsplit och WHATWG)."""
    if not isinstance(u, str) or not u or len(u) > 2000:
        return None, 'tom eller för lång adress'
    if any(c in u for c in '\\\t\r\n') or any(ord(c) < 0x20 or c == ' ' for c in u):
        return None, 'adressen innehåller omvänt snedstreck, blanktecken eller styrtecken'
    try:
        s = urllib.parse.urlsplit(u)
    except ValueError:
        return None, 'ogiltig adress'
    if s.scheme not in ('http', 'https'):
        return None, 'adressen måste vara http eller https'
    if s.username is not None or s.password is not None or '@' in s.netloc:
        return None, 'adressen får inte bära användarnamn eller lösenord'
    vard = idna(s.hostname)
    if not vard or (vard not in LOKALA and not VARDNAMN.match(vard) and not re.fullmatch(r'\[[0-9a-f:]+\]', vard)):
        return None, 'adressen måste ha ett giltigt värdnamn'
    try:
        port = s.port
    except ValueError:
        return None, 'ogiltig port'
    if not tillaten_vard(vard, tillatna):
        return None, 'värden %s ligger inte i byggets domänlista' % vard
    netloc = vard + (':%d' % port if port else '')
    return urllib.parse.urlunsplit((s.scheme, netloc, s.path or '/', s.query, '')), None


def granska_vag(v, slug, root, granskning=False):
    """None när sökvägen ligger under byggets kataloger (eller, för granskarna, under /tmp/nwp-granskning/<slug>-*)."""
    if not v or '\x00' in v:
        return 'tom sökväg'
    p = Path(v) if os.path.isabs(v) else Path(root) / v
    try:
        p = p.resolve()
    except (OSError, RuntimeError):
        return 'sökvägen %s går inte att lösa upp' % v
    tillatna = [(Path(root) / 'kunder' / slug).resolve(), (Path(root) / 'underlag' / slug).resolve(), Path('/tmp/nwp-bygge-' + slug).resolve()]
    if any(p == t or t in p.parents for t in tillatna):
        return None
    try:
        g = GRANSKNINGSROT.resolve()
        if (p.parent == g and p.name.startswith(slug + '-')) or any(x.parent == g and x.name.startswith(slug + '-') for x in p.parents):
            return None
        if granskning and p.parent.parent == (Path(root) / 'kunder').resolve() and p.parent.name == slug and p.name == 'granskning':
            return None
    except (OSError, RuntimeError):
        pass
    return 'sökvägen %s ligger utanför byggets kataloger' % v


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
    if spec['slug'] == 'granska':
        # bara arbetaren (ingen slug, --arbetare <kunder/slug/granskning/runda-NN>) eller jämförelsen (slug --jamfor)
        if 'arbetare' in fl and not pos and set(fl) == {'arbetare'}:
            pass
        elif 'jamfor' in fl and pos == [slug] and set(fl) == {'jamfor'}:
            pass
        else:
            return None, 'granska via tjänsten tar bara --arbetare <katalog under kunder/%s/granskning/> eller %s --jamfor' % (slug, slug)
    elif spec['slug']:
        if pos != [slug]:
            return None, 'sluggen måste vara byggets (%s), fick %r' % (slug, pos)
    elif pos:
        return None, 'inga positionella argument för %s: %r' % (verktyg, pos)
    kanon = {}  # flagga → kanoniskt värde som ersätter modellens
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
            delar = []
            for u in ([v] if typ == 'url' else [x for x in v.split(';') if x]):
                ku, fel = kanon_url(u, tillatna)
                if fel:
                    return None, '--%s: %s' % (k, fel)
                delar.append(ku)
            if not delar:
                return None, '--%s är tom' % k
            kanon[k] = delar[0] if typ == 'url' else ';'.join(delar)
        if typ in ('vag', 'vagar'):
            for x in ([v] if typ == 'vag' else [x for x in v.split(',') if x]):
                fel = granska_vag(x, slug, root)
                if fel:
                    return None, '--%s: %s' % (k, fel)
        if typ == 'granskningsvag':
            p = Path(v) if os.path.isabs(v) else Path(root) / v
            try:
                p = p.resolve()
            except (OSError, RuntimeError):
                return None, '--%s: sökvägen går inte att lösa upp' % k
            if p.parent != (Path(root) / 'kunder' / slug / 'granskning').resolve() or not re.fullmatch(r'runda-\d{2,}', p.name):
                return None, '--%s måste vara en omgång under kunder/%s/granskning/' % (k, slug)
    if 'formular-far-skickas' in fl:
        adress = kanon.get('adress', '')
        if not adress or idna(urllib.parse.urlsplit(adress).hostname) not in LOKALA:
            return None, '--formular-far-skickas bara mot provets lokala mottagare (127.0.0.1), inte %s' % (adress or 'utan adress')
    return list(spec['kmd']) + kanonisera_argv(argv, kanon), None


def kanonisera_argv(argv, kanon):
    """Samma argument, med url-flaggornas värden ersatta av de kanoniska formerna (samma värd i Python och Node)."""
    ut, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            k, sep, v = a[2:].partition('=')
            if k in kanon:
                if sep:
                    ut.append('--%s=%s' % (k, kanon[k]))
                else:
                    ut.append(a)
                    if i + 1 < len(argv) and not argv[i + 1].startswith('--'):
                        ut.append(kanon[k])
                        i += 1
                i += 1
                continue
        ut.append(a)
        i += 1
    return ut


def verktygsmiljo(slug, korning=None, tillatna=(), adress=None, nyckel=None):
    """Verktygens miljö: tjänstens egen utan proxyvariabler och Refero-nyckeln, med NWP_I_TJANSTEN, sluggen, körningen,
    domänlistan (NWP_NAT_TILLATNA, verkställs i webbläsarhjälparen) och tjänstens adress (så att granskarnas egna
    sandlådade sessioner kan delegera sina webbläsarsteg)."""
    miljo = {k: v for k, v in os.environ.items() if not k.upper().endswith('_PROXY') and k != 'REFERO_MCP_TOKEN'}
    miljo['NWP_I_TJANSTEN'] = '1'
    miljo['NWP_SLUG'] = slug
    miljo['NWP_NAT_TILLATNA'] = ','.join(sorted(tillatna))
    if korning:
        miljo['NWP_KORNING'] = korning
    if adress:
        miljo['NWP_WEBBTJANST'] = adress
    if nyckel:
        miljo['NWP_WEBBTJANST_NYCKEL'] = nyckel
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
    tillatna = tillatna_varden(sandlada.domanlista(root, domaner))
    nyckel = secrets.token_hex(16)
    adress = {'v': None}

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
            rc, ut = kor_verktyg(kmd, verktygsmiljo(slug, korning, tillatna, adress['v'], nyckel), root)
            print('%s KLART %s rc=%s %.0f s' % (nu(), verktyg, rc, time.time() - t0), flush=True)
            self.svar(200, {'rc': rc, 'ut': ut})

    srv = Tjanst(('127.0.0.1', port), Hanterare)
    adress['v'] = 'http://127.0.0.1:%d' % srv.server_address[1]
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
