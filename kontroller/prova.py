#!/usr/bin/env python3
"""prova.py — kör kontrollerna på en kunds sajt och skriver kunder/<slug>/prov/STATUS.json och PROV.md.

Bygger sajten själv (npm run build i kunder/<slug>/sajt), serverar dist/ på 127.0.0.1 och kör:

Grindar (röd grind = sajten är inte klar):
  bygge        npm run build lyckas och dist/ har minst en sida
  seo          seo_kontroll.py i lanseringsläge: 0 fynd
  standard     standard_kontroll.py: byggstandardens maskinkontrollerbara D-punkter (kunskap/byggstandard.md), 0 fel
  axe          0 överträdelser med påverkan serious/critical, mobil och desktop
  lighthouse   prestanda ≥ 90, tillgänglighet ≥ 95, bästa praxis ≥ 95, SEO ≥ 90, mobil och desktop
  spill        inget horisontellt spill i 390, 768 och 1440 px på någon sida
  utan-js      sidorna läsbara utan JavaScript och förfrågan skickad till demomottagaren (bara PASS är grönt)

Information (visas, blockerar inte):
  copy         copy_kontroll.py på sajtens källtexter. Enligt kunskap/copy-kontroll.md är rapporten aldrig en grind:
               varje fynd rättas eller motiveras i RAPPORT.md (en fras kan vara rätt i kundens röst).
  utforska     utforska.mjs-fynd
  prelaunch    prelaunch.py-grindarna (juridik avgörs av människa)

    .venv/bin/python kontroller/prova.py <slug> [--snabb]

--snabb hoppar över lighthouse och utforska, för snabb iteration under bygget. Stop-kroken kör alltid hela provet.
Exit 0 = alla grindar gröna; 1 = minst en röd; 2 = fel i anropet.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from email import policy as email_policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

ROOT = Path(__file__).resolve().parents[1]
KONTROLLER = ROOT / 'kontroller'
PY = sys.executable
NODE = shutil.which('node') or 'node'
NPM = shutil.which('npm') or 'npm'
SIPS = shutil.which('sips')
MAX_RUTOR = 12
MAX_SIDOR = 12


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def kor(cmd, cwd=None, timeout=900):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired as e:
        return 124, 'tidsgräns %ds: %s' % (timeout, ' '.join(map(str, cmd)))
    except OSError as e:
        return 127, str(e)


def svans(text, n=25):
    return '\n'.join(text.strip().splitlines()[-n:])


def dist_hash(dist):
    h = hashlib.sha256()
    for f in sorted(p for p in dist.rglob('*') if p.is_file()):
        h.update(str(f.relative_to(dist)).encode())
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def bildmatt(p):
    rc, out = kor([SIPS, '-g', 'pixelWidth', '-g', 'pixelHeight', str(p)], timeout=30)
    m = dict(re.findall(r'pixel(Width|Height):\s*(\d+)', out))
    return (int(m['Width']), int(m['Height'])) if rc == 0 and len(m) == 2 else (0, 0)


def rutor(mapp, vy):
    """Helsidesbilden delad i skärmhöga rutor, vy-<bredd>-ruta-NN.png, uppifrån och ned. En helsida på över 8000 px
    skalas ned så mycket när en modell läser den att text och detaljer försvinner (fynd 2026-10-02: startsidan i 390
    var 780×10164 px). Rutans höjd är förstavyns. Returnerar (antal rutor, antal skärmar)."""
    hela, forsta = mapp / ('vy-%s-hela.png' % vy), mapp / ('vy-%s-forsta.png' % vy)
    if not (SIPS and hela.is_file() and forsta.is_file()):
        return 0, 0
    (b, h), (_, steg) = bildmatt(hela), bildmatt(forsta)
    if not (b and h and steg):
        return 0, 0
    skarmar = list(range(0, h, steg))
    gjorda = 0
    for i, y in enumerate(skarmar[:MAX_RUTOR], 1):
        # sips beskär inte när rutan slutar exakt vid bildens nederkant (ger hela bilden); sluta en pixel ovanför.
        hojd = min(steg, h - y - 1)
        ut = mapp / ('vy-%s-ruta-%02d.png' % (vy, i))
        if hojd < 1:
            continue
        rc, _ = kor([SIPS, '-c', str(hojd), str(b), '--cropOffset', str(y), '0', str(hela), '--out', str(ut)], timeout=60)
        if rc == 0 and bildmatt(ut) == (b, hojd):
            gjorda += 1
        else:
            ut.unlink(missing_ok=True)
    return gjorda, len(skarmar)


def sidor_i(dist):
    rutter = []
    for f in sorted(dist.rglob('index.html')):
        rel = f.parent.relative_to(dist).as_posix()
        rutter.append('/' if rel == '.' else '/' + rel + '/')
    rutter.sort(key=lambda r: (r != '/', r.count('/'), r))
    return rutter


def las_formular(ctype, kropp):
    """Textfälten ur ett inskickat formulär (multipart eller urlencoded). Filer läses inte."""
    if ctype.startswith('multipart/form-data'):
        msg = BytesParser(policy=email_policy.default).parsebytes(b'Content-Type: ' + ctype.encode() + b'\r\n\r\n' + kropp)
        ut = {}
        for del_ in msg.iter_parts():
            namn = del_.get_param('name', header='content-disposition')
            if namn and not del_.get_filename():
                ut[namn] = del_.get_content() if isinstance(del_.get_content(), str) else ''
        return ut
    return {k: v[0] for k, v in parse_qs(kropp.decode('utf-8', 'replace')).items()}


class TystServer(ThreadingHTTPServer):
    """Webbläsare som stänger anslutningen i förtid ska inte ge tracebacks i provets utdata (fynd 2026-10-01)."""

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class Server:
    """Statisk server för dist/ på 127.0.0.1 (eller en given adress). Saknad sida ger 404.html med status 404."""

    def __init__(self, dist, vard='127.0.0.1'):
        dist = str(dist)

        rot = os.path.realpath(dist)

        class H(SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=dist, **k)

            def log_message(self, *a):
                pass

            def send_head(self):
                """Bara filer som verkligen ligger under dist/: SimpleHTTPRequestHandler följer symlänkar ut ur katalogen,
                och visningen i telefonen lyssnar på nätverket (revisionen 2026-10-03, F4). Den fil som faktiskt skulle
                öppnas (också en katalogs index.html) prövas mot den upplösta roten; annat får ett riktigt 404-svar före
                öppningen, aldrig en ersättningssökväg."""
                p = self.translate_path(self.path)
                if os.path.isdir(p):
                    for index in ('index.html', 'index.htm'):
                        if os.path.isfile(os.path.join(p, index)):
                            p = os.path.join(p, index)
                            break
                verklig = os.path.realpath(p)
                if verklig != rot and not verklig.startswith(rot + os.sep):
                    self.send_error(404)
                    return None
                return super().send_head()

            def do_POST(self):
                """Demomottagare för förfrågningsformuläret (kunskap/forfragan.md): läser fälten, kontrollerar dem och
                skickar besökaren vidare med 303. Sparar, loggar och skickar ingenting; vid lansering tar en
                serverfunktion med samma kontrakt över."""
                if urlsplit(self.path).path != '/api/forfragan':
                    return self.send_error(405)
                n = int(self.headers.get('Content-Length') or 0)
                if n > 26 * 1024 * 1024:
                    return self.send_error(413)
                falt = las_formular(self.headers.get('Content-Type') or '', self.rfile.read(n))
                if falt.get('webbplats'):
                    mal = '/tack/'  # honeypoten ifylld: tyst, som om det gick bra
                elif all(falt.get(k, '').strip() for k in ('namn', 'telefon', 'meddelande')):
                    mal = '/tack/'
                else:
                    mal = '/kontakt/?saknas=1#forfragan-saknas'
                self.send_response(303)
                self.send_header('Location', mal)
                self.send_header('Content-Length', '0')
                self.end_headers()

            def send_error(self, code, message=None, explain=None):
                sida = Path(dist) / '404.html'
                # felsidan prövas som alla andra filer: en symlänk ut ur dist får inte lämna ut målet (revisionen, F4)
                if code == 404 and sida.is_file() and os.path.realpath(sida).startswith(rot + os.sep):
                    body = sida.read_bytes()
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    if self.command != 'HEAD':
                        self.wfile.write(body)
                    return
                super().send_error(code, message, explain)

        self.httpd = TystServer((vard, 0), H)
        self.url = 'http://%s:%d' % (vard, self.httpd.server_address[1])
        self.trad = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.trad.start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()


def seo_rader(sj):
    """Fyndraderna ur seo.json: sajtfynden är en lista (ett sajtövergripande fynd kraschade provet; revisionen 2026-10-03,
    F19), äldre form med {'fynd': [...]} läses också."""
    sajtfynd = sj.get('sajt') or []
    sajtfynd = sajtfynd.get('fynd', []) if isinstance(sajtfynd, dict) else sajtfynd
    rader = ['sajt: %s %s' % (f.get('typ'), f.get('text', '')) for f in sajtfynd]
    rader += ['%s: %s %s' % (x.get('sida'), f.get('typ'), f.get('text', '')) for x in sj.get('per_sida') or [] for f in x.get('fynd', [])]
    return rader


def spillfynd(ins, r):
    """Spillraderna för en sida ur INSPEKTION.json: varje ordinarie vy ska vara mätt och fri från spill, och 320-vyn
    (tillstand.reflow_320 i 390-vyn, WCAG 1.4.10 Reflow) likaså; en saknad 320-mätning är inte grön (omgång elva, F9)."""
    ut = []
    vyer = ins.get('vyer') or {}
    for vy in ('390', '768', '1440'):  # varje vy ska vara mätt; en vy som föll eller saknar mätning är inte grön
        d = vyer.get(vy)
        if not d or d.get('fel') or not isinstance(d.get('spill'), dict) or 'spill' not in d['spill']:
            ut.append('%s @%s: inte mätt (%s)' % (r, vy, (d or {}).get('fel') or 'ingen spillmätning'))
    for vy, d in vyer.items():
        if (d.get('spill') or {}).get('spill'):
            ut.append('%s @%s (%s > %s px)' % (r, vy, d['spill'].get('scrollWidth'), d['spill'].get('clientWidth')))
    r320 = ((vyer.get('390') or {}).get('tillstand') or {}).get('reflow_320')
    if not isinstance(r320, dict) or 'spill' not in r320:
        ut.append('%s @320: inte mätt (reflow_320 saknas i 390-vyn)' % r)
    elif r320.get('spill'):
        ut.append('%s @320 (%s > %s px)' % (r, r320.get('scrollWidth'), r320.get('clientWidth')))
    return ut


def utan_js_grind(u):
    """(ok, sammanfattning, detalj) för utan-js: bara PASS är grönt. EJ_MATT betyder att formulären aldrig skickades till
    demomottagaren, och ej mätt är inte grönt (omgång elva, F31); FAIL är rött."""
    st, fynd = u.get('status'), u.get('fynd') or []
    detalj = '; '.join(str(f.get('vad') or f)[:120] for f in fynd[:8]) or None
    if st == 'PASS':
        return True, 'PASS, %d fynd' % len(fynd), detalj
    if st == 'EJ_MATT':
        return False, 'EJ_MATT: formulären skickades inte till demomottagaren; ej mätt är inte grönt', detalj
    return False, '%s, %d fynd' % (st, len(fynd)), detalj


def grind(ok, sammanfattning, fil=None, detalj=None):
    return {'ok': bool(ok), 'sammanfattning': sammanfattning, 'fil': fil, 'detalj': detalj}


def prova(slug, snabb=False):
    kund = ROOT / 'kunder' / slug
    sajt = kund / 'sajt'
    dist = sajt / 'dist'
    underlag = ROOT / 'underlag' / slug
    verksamhet = underlag / 'VERKSAMHET.json'
    prov = kund / 'prov'
    if prov.exists():
        for barn in prov.iterdir():
            if barn.name.startswith('.') or barn.name == 'historik.jsonl':
                continue
            shutil.rmtree(barn) if barn.is_dir() else barn.unlink()
    prov.mkdir(parents=True, exist_ok=True)
    g, info = {}, {}
    status = {'schema': 1, 'slug': slug, 'tid': nu(), 'snabb': snabb, 'grindar': g, 'info': info}

    # bygge
    if not (sajt / 'package.json').is_file():
        g['bygge'] = grind(False, 'kunder/%s/sajt/package.json saknas' % slug)
        return status
    if not (sajt / 'node_modules').is_dir():
        rc, out = kor([NPM, 'install', '--no-audit', '--no-fund'], cwd=sajt, timeout=600)
        if rc:
            g['bygge'] = grind(False, 'npm install misslyckades', detalj=svans(out))
            return status
    rc, out = kor([NPM, 'run', 'build'], cwd=sajt, timeout=600)
    (prov / 'bygge.log').write_text(out, encoding='utf-8')
    rutter = sidor_i(dist) if dist.is_dir() else []
    if rc or not rutter:
        g['bygge'] = grind(False, 'npm run build misslyckades' if rc else 'dist/ saknar sidor', 'prov/bygge.log', svans(out))
        return status
    g['bygge'] = grind(True, '%d sidor: %s' % (len(rutter), ', '.join(rutter)), 'prov/bygge.log')
    status['dist_sha256'] = dist_hash(dist)
    status['sidor'] = rutter
    provsidor = rutter[:MAX_SIDOR]
    if len(rutter) > MAX_SIDOR:
        info['sidurval'] = 'mätt %d av %d sidor (de första i ordning hem, nivå, namn)' % (MAX_SIDOR, len(rutter))

    doman = None
    if verksamhet.is_file():
        try:
            v = json.loads(verksamhet.read_text(encoding='utf-8'))
            webb = ((v.get('webb') or {}).get('doman') if isinstance(v.get('webb'), dict) else '') or ''
            doman = re.sub(r'^https?://(www\.)?', '', webb).strip('/').split('/')[0] or None
        except ValueError:
            pass

    # seo
    cmd = [PY, '-B', str(KONTROLLER / 'seo_kontroll.py'), '--bygge', str(dist), '--lage', 'lansering', '--ut', str(prov / 'seo.json'), '--md', str(prov / 'seo.md')]
    if verksamhet.is_file():
        cmd += ['--verksamhet', str(verksamhet)]
    if doman:
        cmd += ['--doman', doman]
    rc, out = kor(cmd)
    try:
        sj = json.loads((prov / 'seo.json').read_text(encoding='utf-8'))
        n = sj['fynd_totalt']
        rader = seo_rader(sj)
        g['seo'] = grind(n == 0, '%d fynd' % n, 'prov/seo.md', '\n'.join(r[:160] for r in rader[:15]) or None)
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        g['seo'] = grind(False, 'seo_kontroll kördes inte (rc %d)' % rc, detalj=svans(out))

    # copy: läses i den byggda HTML:en, sida för sida. Där syns texten som besökaren ser den: uppgifter ur datafiler
    # finns med, utropstecken räknas per sida och kundcitat (blockquote, q) räknas inte (fynd från Luleå-Snickaren och
    # Sundboms 2026-10-01). Fynden pekar på sidan; rätta i källan.
    sidfiler = [str(f) for f in sorted(dist.rglob('*.html')) if f.name != '404.html']
    cmd = [PY, '-B', str(KONTROLLER / 'copy_kontroll.py'), '--kalla', *sidfiler, '--ut', str(prov / 'copy.json'), '--md', str(prov / 'copy.md')]
    fraser = underlag / 'FRASER.txt'
    if fraser.is_file():
        cmd += ['--fraser', str(fraser)]
    if verksamhet.is_file():
        rc_k, _ = kor([PY, '-B', str(KONTROLLER / 'verksamhetsuppgifter.py'), 'krav', str(verksamhet), '--ut', str(prov / 'krav.json')])
        if rc_k == 0 and (prov / 'krav.json').is_file():
            cmd += ['--krav', str(prov / 'krav.json')]
        else:
            info['verksamhet'] = 'VERKSAMHET.json är ogiltig enligt verksamhetsuppgifter.py; kör kontrollera'
    rc, out = kor(cmd)
    def sida(fil):
        try:
            rel = Path(fil).relative_to(dist).parent.as_posix()
        except ValueError:
            return Path(str(fil)).name
        return '/' if rel == '.' else '/' + rel + '/'
    try:
        cf = json.loads((prov / 'copy.json').read_text(encoding='utf-8'))['fynd']
        rader = ['%s %s "%s" (%s)' % (sida(f.get('fil', '')), f.get('typ'), f.get('text', ''), f.get('riktning', '')) for f in cf]
        info['copy'] = '%d fynd (prov/copy.md); rätta eller motivera varje fynd i RAPPORT.md' % len(cf) + (''.join('\n  - ' + r[:200] for r in rader[:15]))
        status['copy_fynd'] = len(cf)
    except (OSError, ValueError, KeyError):
        info['copy'] = 'copy_kontroll kördes inte (rc %d): %s' % (rc, svans(out, 3))

    with Server(dist) as srv:
        lista = ','.join(provsidor)
        # axe
        rc, out = kor([NODE, str(KONTROLLER / 'axe.mjs'), '--url=' + srv.url, '--sidor=' + lista, '--ut=' + str(prov / 'axe')], timeout=600)
        try:
            a = json.loads((prov / 'axe' / 'axe.json').read_text(encoding='utf-8'))
            # ej mätt är inte godkänt: varje sida och vy måste ha mätts utan fel (revisionen 2026-10-03, F9)
            matfel = int(a.get('fel') or 0) + sum(1 for r in a.get('rader') or [] if r.get('fel'))
            vantade = 2 * len(provsidor)
            ok = a['allvarliga'] == 0 and matfel == 0 and len(a.get('rader') or []) >= vantade
            text = '%d allvarliga av %d överträdelser' % (a['allvarliga'], a['totalt'])
            if matfel or len(a.get('rader') or []) < vantade:
                text += '; %d mätfel, %d av %d lägen mätta' % (matfel, len(a.get('rader') or []), vantade)
            g['axe'] = grind(ok, text, 'prov/axe/axe.json', svans(out, 15) if a['totalt'] or not ok else None)
        except (OSError, ValueError, KeyError):
            g['axe'] = grind(False, 'axe kördes inte (rc %d)' % rc, detalj=svans(out))

        # lighthouse
        if snabb:
            info['lighthouse'] = 'hoppades över (--snabb)'
        else:
            # sidor med noindex med avsikt (tacksidan) mäts inte: Lighthouse sänker SEO för noindex
            lh = [r for r in provsidor if not re.search(r'<meta[^>]+name="robots"[^>]+noindex', (dist / r.strip('/') / 'index.html').read_text(encoding='utf-8', errors='replace') if (dist / r.strip('/') / 'index.html').is_file() else '')]
            rc, out = kor([NODE, str(KONTROLLER / 'lighthouse.mjs'), '--url=' + srv.url, '--sidor=' + ','.join(lh), '--ut=' + str(prov / 'lighthouse')], timeout=900)
            try:
                lh = json.loads((prov / 'lighthouse' / 'lighthouse.json').read_text(encoding='utf-8'))
                rader = lh['rader']
                lag = lambda k: min(r[k] for r in rader)
                text = 'lägst P %d, A %d, BP %d, SEO %d (%d mätningar)' % (lag('prestanda'), lag('tillganglighet'), lag('bastaPraxis'), lag('seo'), len(rader))
                under = ['%s %s: %s' % (r['form'], r['sida'], ','.join(r['underkanda'][:8])) for r in rader if not r['ok']]
                g['lighthouse'] = grind(lh['ok'], text, 'prov/lighthouse/lighthouse.json', '\n'.join(under) or None)
            except (OSError, ValueError, KeyError):
                g['lighthouse'] = grind(False, 'lighthouse kördes inte (rc %d)' % rc, detalj=svans(out))

        # spill och skärmbilder
        spill = []
        bilder = []
        rutinfo = []
        for r in provsidor:
            namn = 'hem' if r == '/' else r.strip('/').replace('/', '-')
            ut = prov / 'inspektion' / namn
            rc, out = kor([NODE, str(KONTROLLER / 'webblasare' / 'inspektera.mjs'), '--adress', srv.url + r, '--ut', str(ut), '--vyer', '390,768,1440'], timeout=300)
            for vy in ('390', '1440'):
                if (ut / ('vy-%s-ruta-01.png' % vy)).is_file():
                    continue  # inspektionen har skrollat fram rutorna själv
                gjorda, skarmar = rutor(ut, vy)
                if skarmar > gjorda:
                    rutinfo.append('%s @%s: %d av %d skärmar som rutor' % (r, vy, gjorda, skarmar))
            try:
                ins = json.loads((ut / 'INSPEKTION.json').read_text(encoding='utf-8'))
                spill += spillfynd(ins, r)
                for vy, d in (ins.get('vyer') or {}).items():
                    if r == '/' and d.get('h1_i_forsta_vyn') is False:
                        rutinfo.append('startsidans h1 syns inte i första vyn @%s' % vy)
                    if d.get('forsta_vyn'):
                        bilder.append(str(Path(d['forsta_vyn']).relative_to(kund)) if Path(d['forsta_vyn']).is_absolute() else d['forsta_vyn'])
            except (OSError, ValueError):
                spill.append('%s: inspektionen kördes inte (rc %d) %s' % (r, rc, svans(out, 3)))
        g['spill'] = grind(not spill, 'inget spill på %d sidor × 4 vyer (390, 768, 1440 och 320)' % len(provsidor) if not spill else '%d fall' % len(spill), 'prov/inspektion/', '; '.join(spill[:12]) or None)
        if rutinfo:
            info['rutor'] = '; '.join(rutinfo)
        info['skarmbilder'] = ('prov/inspektion/<sida>/vy-<bredd>-forsta.png och vy-<bredd>-ruta-NN.png, helsidan i skärmhöga '
                               'rutor (titta på dem; ett textträd är inte bildseende). -hela.png är nedskalad och visar bara rytmen.')

        # stil (info): typsnitt, färgfamiljer, kort, nästa sektion, klickytor, modellernas standardval
        rc, out = kor([NODE, str(KONTROLLER / 'stil.mjs'), '--url=' + srv.url, '--sidor=' + lista, '--ut=' + str(prov / 'stil')], timeout=300)
        try:
            sj = json.loads((prov / 'stil' / 'STIL.json').read_text(encoding='utf-8'))
            info['stil'] = 'rubriker i %s, bakgrund %s; %d varningar, %d små klickytor (prov/stil/STIL.md)' % (
                ', '.join(sj['sammanfattning']['rubriktypsnitt']) or '-', ', '.join(sj['sammanfattning']['familjer']['bakgrund']),
                len(sj['varningar']), len(sj['smaYtor'])) + ''.join('\n  - ' + v for v in sj['varningar'][:8])
        except (OSError, ValueError, KeyError):
            info['stil'] = 'kördes inte (rc %d): %s' % (rc, svans(out, 3))

        # utan js
        rc, out = kor([NODE, str(KONTROLLER / 'webblasare' / 'utan-js.mjs'), '--adress', srv.url + '/', '--sidor', ';'.join(provsidor), '--ut', str(prov / 'utan-js'),
                       '--formular-far-skickas', '--testmarkering', 'NWP-PROV'], timeout=300)
        try:
            u = json.loads((prov / 'utan-js' / 'UTAN-JS.json').read_text(encoding='utf-8'))
            ok_u, text_u, detalj_u = utan_js_grind(u)  # inskicket går till provets demomottagare på 127.0.0.1 (omgång elva, F31)
            g['utan-js'] = grind(ok_u, text_u, 'prov/utan-js/UTAN-JS.json', detalj_u)
        except (OSError, ValueError):
            g['utan-js'] = grind(False, 'utan-js kördes inte (rc %d)' % rc, detalj=svans(out))

        # utforska (info)
        if snabb:
            info['utforska'] = 'hoppades över (--snabb)'
        else:
            rc, out = kor([NODE, str(KONTROLLER / 'webblasare' / 'utforska.mjs'), '--adress', srv.url + '/', '--ut', str(prov / 'utforska'), '--max-sidor', '12'], timeout=600)
            try:
                uf = json.loads((prov / 'utforska' / 'UTFORSKNING.json').read_text(encoding='utf-8'))
                fynd = [f for f in uf.get('fynd', []) if f.get('typ') != 'observation']
                info['utforska'] = '%d fynd (prov/utforska/UTFORSKNING.md); läs och rätta det som är verkligt' % len(fynd)
            except (OSError, ValueError):
                info['utforska'] = 'kördes inte (rc %d): %s' % (rc, svans(out, 3))

    # byggstandarden (kunskap/byggstandard.md): de maskinkontrollerbara D-punkterna som ingen annan grind prövar;
    # klickytorna (3.3) kommer ur stilrapporten, som mäter i webbläsaren
    cmd = [PY, '-B', str(KONTROLLER / 'standard_kontroll.py'), '--bygge', str(dist), '--ut', str(prov / 'standard.json'),
           '--md', str(prov / 'standard.md')]
    cmd += ['--stil', str(prov / 'stil' / 'STIL.json')]  # alltid: saknad eller fallen stilmätning är ett fel i 3.3, inte grönt
    cmd += ['--bestallning', str(underlag / 'BESTALLNING.md'), '--verksamhet', str(verksamhet)]
    rc, out = kor(cmd)
    try:
        st = json.loads((prov / 'standard.json').read_text(encoding='utf-8'))
        status['utgaende_lankar'] = st.get('utgaende') or []
        rader = ['%s %s: %s' % (x['punkt'], x['sida'], x['text']) for x in st['fel']]
        g['standard'] = grind(not st['fel'], '%d fel, %d info' % (len(st['fel']), len(st['info'])), 'prov/standard.md',
                              '\n'.join(r[:160] for r in rader[:15]) or None)
    except (OSError, ValueError, KeyError):
        g['standard'] = grind(False, 'standard_kontroll kördes inte (rc %d)' % rc, detalj=svans(out))

    # rubriker (info): underlag till det avskärmade rubriktestet i steg 6.4
    rc, out = kor([PY, '-B', str(KONTROLLER / 'rubriker.py'), '--bygge', str(dist), '--ut', str(prov / 'RUBRIKER.md')])
    info['rubriker'] = 'prov/RUBRIKER.md: sajtens h1 och h2 per sida, till rubriktestet' if rc == 0 else 'kördes inte: ' + svans(out, 3)

    # prelaunch (info)
    cmd = [PY, '-B', str(KONTROLLER / 'prelaunch.py'), '--bygge', str(dist), '--lage', 'lansering', '--ut', str(prov / 'prelaunch.json'), '--md', str(prov / 'prelaunch.md')]
    if verksamhet.is_file():
        cmd += ['--verksamhet', str(verksamhet)]
    if (sajt / 'src').is_dir():
        cmd += ['--repo', str(sajt)]
    rc, out = kor(cmd)
    try:
        pl = json.loads((prov / 'prelaunch.json').read_text(encoding='utf-8'))
        info['prelaunch'] = ', '.join('%s %s' % (x['grind'], x['status']) for x in pl['grindar']) + ' (prov/prelaunch.md; juridik avgörs av människa; mätgrindarna ersätts av axe/lighthouse ovan)'
    except (OSError, ValueError, KeyError):
        info['prelaunch'] = 'kördes inte (rc %d)' % rc
    return status


def markdown(s):
    rad = ['# Prov — %s — %s' % (s['slug'], 'GRÖNT' if s.get('ok') else 'RÖTT'), '', 'Tid %s%s. Bygge %s.' % (s['tid'], ' (snabbprov)' if s.get('snabb') else '', (s.get('dist_sha256') or '-')[:12]), '',
           '| Grind | Status | Sammanfattning | Fil |', '|---|---|---|---|']
    for namn, x in s['grindar'].items():
        rad.append('| %s | %s | %s | %s |' % (namn, 'grön' if x['ok'] else 'RÖD', x['sammanfattning'].replace('|', '/'), x.get('fil') or ''))
    for namn, x in s['grindar'].items():
        if not x['ok'] and x.get('detalj'):
            rad += ['', '## %s — detalj' % namn, '', '```', x['detalj'], '```']
    if s['info']:
        rad += ['', '## Information (blockerar inte)', '']
        rad += ['- **%s**: %s' % (k, v) for k, v in s['info'].items()]
    return '\n'.join(rad) + '\n'


GRINDAR = ('bygge', 'seo', 'standard', 'axe', 'lighthouse', 'spill', 'utan-js')


def main(argv=None):
    p = argparse.ArgumentParser(prog='prova', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--snabb', action='store_true')
    a = p.parse_args(argv)
    krav_slug(a.slug)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug):
        print('slug: a-z, 0-9 och bindestreck', file=sys.stderr)
        return 2
    t0 = time.time()
    s = prova(a.slug, a.snabb)
    krav = [x for x in GRINDAR if not (a.snabb and x == 'lighthouse')]
    s['ok'] = all(x in s['grindar'] and s['grindar'][x]['ok'] for x in krav)
    s['sekunder'] = round(time.time() - t0)
    prov = ROOT / 'kunder' / a.slug / 'prov'
    prov.mkdir(parents=True, exist_ok=True)
    (prov / 'STATUS.json').write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (prov / 'PROV.md').write_text(markdown(s), encoding='utf-8')
    with open(prov / 'historik.jsonl', 'a', encoding='utf-8') as h:
        h.write(json.dumps({'tid': s['tid'], 'ok': s['ok'], 'snabb': a.snabb, 'grindar': {k: v['ok'] for k, v in s['grindar'].items()}, 'dist': (s.get('dist_sha256') or '')[:12]}) + '\n')
    print(markdown(s))
    return 0 if s['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
