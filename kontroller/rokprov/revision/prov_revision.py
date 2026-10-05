#!/usr/bin/env python3
"""Regressionsfall ur revisionen 2026-10-03 (Codex, nio omgångar): varje skydd prövas genom sin riktiga ingång, med ett
positivt och ett negativt fall, isolerat och syntetiskt. Körs av kontroller/rokprov.sh. Argument: repots rot. Skriver
bara i temporära kataloger och i /tmp/nwp-granskning (granskarens arbetskataloger)."""
import datetime
import functools
import http.client
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(ROOT / 'dashboard'))
PY = sys.executable
tmp = Path(tempfile.mkdtemp(prefix='nwp-rev-'))


class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def server(rot, handler=None):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler or functools.partial(Tyst, directory=str(rot)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, 'http://127.0.0.1:%d' % srv.server_port


def begar(port, metod, vag, vard=None, huvuden=None, kropp=None):
    c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    c.putrequest(metod, vag, skip_host=True, skip_accept_encoding=True)
    c.putheader('Host', vard or '127.0.0.1:%d' % port)
    for k, v in (huvuden or {}).items():
        c.putheader(k, v)
    if kropp is not None:
        c.putheader('Content-Length', str(len(kropp)))
    c.endheaders(kropp)
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, data


# ---------------------------------------------------------------- F2: markdown kodar citattecken i attribut
import server as dash  # noqa: E402
h = dash.md('Se [länken](https://x.se/"onmouseover="window.audit=1) och https://y.se/"onclick="a')
assert 'onmouseover="' not in h and 'onclick="' not in h and '&quot;' in h, h
assert dash.md('`<b>`') == '<p><code>&lt;b&gt;</code></p>', dash.md('`<b>`')
print('F2 markdown ok')

# ---------------------------------------------------------------- F13/F14/F15: dashboardservern på riktigt
dash.ROOT, dash.KUNDER, dash.UNDERLAG, dash.AB = tmp, tmp / 'kunder', tmp / 'underlag', tmp / 'kunder' / 'ab'
for d in (dash.AB, dash.KUNDER / 'normal', dash.KUNDER / 'dold-abx' / 'prov' / 'inspektion' / 'hem', dash.KUNDER / 'dold-aby' / 'sajt' / 'dist',
          dash.KUNDER / 'dold-abx' / 'sajt' / 'dist', dash.UNDERLAG / 'dold-abx'):
    d.mkdir(parents=True, exist_ok=True)
(dash.AB / 'ab-demo-20261003T000000Z.json').write_text(json.dumps({'id': 'ab-demo-20261003T000000Z', 'byggen': ['dold-abx', 'dold-aby'], 'val': None,
                                                                   'varden': {'dold-abx': 'av', 'dold-aby': 'pa'}, 'variabel': 'atelje', 'verksamhet': 'Demo'}))
(dash.KUNDER / 'dold-abx' / 'AB-SYSKON').write_text('dold-aby\n'); (dash.KUNDER / 'dold-aby' / 'AB-SYSKON').write_text('dold-abx\n')
(dash.KUNDER / 'dold-abx' / 'prov' / 'inspektion' / 'hem' / 'vy-390-forsta.png').write_bytes(b'\x89PNG')
(dash.KUNDER / 'dold-abx' / 'RAPPORT.md').write_text('# hemlig rapport'); (dash.UNDERLAG / 'dold-abx' / 'KONCEPT.md').write_text('# koncept')
(dash.KUNDER / 'normal' / 'x.md').write_text('# normal')
dsrv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
threading.Thread(target=dsrv.serve_forever, daemon=True).start()
dport = dsrv.server_port
dash.VARD['tillatna'] = {'127.0.0.1:%d' % dport, 'localhost:%d' % dport}
assert begar(dport, 'GET', '/')[0] == 200
assert begar(dport, 'GET', '/', vard='evil.test:%d' % dport)[0] == 421, 'främmande Host ska nekas'
assert begar(dport, 'GET', '/', vard='127.0.0.1:1')[0] == 421, 'fel port ska nekas'
assert begar(dport, 'POST', '/api/ab/x', huvuden={'Origin': 'http://evil.test:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{}')[0] == 403
assert begar(dport, 'POST', '/api/ab/x', huvuden={'Origin': 'https://127.0.0.1:%d' % dport}, kropp=b'{}')[0] == 403, 'fel schema i Origin'
assert begar(dport, 'GET', '/fil/kunder/normal/x.md')[0] == 200
assert begar(dport, 'GET', '/fil/kunder/normal/../ab/ab-demo-20261003T000000Z.json')[0] == 404, 'facit via ../ (F14)'
assert begar(dport, 'GET', '/fil/underlag/normal/../dold-abx/KONCEPT.md')[0] == 404, 'dold arm via ../ (F14)'
assert begar(dport, 'GET', '/fil/kunder/dold-abx/RAPPORT.md')[0] == 404 and begar(dport, 'GET', '/fil/kunder/dold-abx/prov/inspektion/hem/vy-390-forsta.png')[0] == 200
assert not dash.ab_klar({'byggen': ['a', 'b'], 'korningar': {'a': {}, 'b': {}}})
# F15 genom spara_ab: saknad hash, fel hash, rätt hash
dash.commit_agarens = lambda *a, **k: 'prov'
from prova import dist_hash  # noqa: E402
for s in ('dold-abx', 'dold-aby'):
    (dash.KUNDER / s / 'sajt' / 'dist' / 'index.html').write_text('<p>%s</p>' % s)
j = dash.AB / 'ab-demo-20261003T000000Z.json'
p = json.loads(j.read_text()); p.update(klar='2026-10-03T00:00:00Z', korningar={'dold-abx': {}, 'dold-aby': {}}); j.write_text(json.dumps(p))
try:
    dash.spara_ab(p['id'], {'val': 'dold-abx'}); raise AssertionError('utan hash ska valet nekas')
except ValueError as e:
    assert 'saknar' in str(e), e
p['korningar'] = {s: {'dist_sha256': dist_hash(dash.KUNDER / s / 'sajt' / 'dist')} for s in p['byggen']}
p['korningar']['dold-aby']['dist_sha256'] = 'fel'; j.write_text(json.dumps(p))
try:
    dash.spara_ab(p['id'], {'val': 'dold-abx'}); raise AssertionError('fel hash ska nekas')
except ValueError as e:
    assert 'ändrats' in str(e), e
p['korningar']['dold-aby']['dist_sha256'] = dist_hash(dash.KUNDER / 'dold-aby' / 'sajt' / 'dist'); j.write_text(json.dumps(p))
r = dash.spara_ab(p['id'], {'val': 'dold-abx', 'kommentar': 'A'})
assert r['ok'] and '- **Byggen:** dold-abx, dold-aby' in (tmp / 'LARDOMAR.md').read_text(), 'A/B-avsnittet ska namnge byggena (F17)'
# ägarbeslut 2026-10-03: ägarens ord bara i den privata filen, betygen publikt, backlogposten utan fritext
assert 'Ägarens ord:** A' not in (tmp / 'LARDOMAR.md').read_text() and 'Ägarens ord:** A' in (tmp / 'underlag' / 'LARDOMAR-original.md').read_text(), 'A/B-kommentaren ska bara stå privat'
dash.bl.MAPP = tmp / 'backlog'
r = dash.spara_dom('normal', {'svar': {'namn': 'Ja, som den är', 'battre': 'Mycket bättre', 'specifik': 4, 'samsta': 'Ring Dan 070-123 45 67', 'en_andring': 'Beställ foton av Dan Sandberg'}})
pub, priv = (tmp / 'LARDOMAR.md').read_text(), (tmp / 'underlag' / 'LARDOMAR-original.md').read_text()
post = (tmp / 'backlog' / (r['backlog'] + '.md')).read_text()
assert '## L0 · ' in pub and 'Mycket bättre' in pub and 'Dan' not in pub and '070-123' not in pub and 'LARDOMAR-original.md' in pub, pub
assert 'Beställ foton av Dan Sandberg' in priv and 'Ring Dan 070-123 45 67' in priv and '## L0 · ' in priv, priv
assert 'Dan' not in post and '070-123' not in post and 'LARDOMAR-original.md' in post and 'Mycket bättre' in post, post
assert '**Ändring:** väntar (backlog %s)' % r['backlog'] in pub and r['backlog'] in priv, (pub, priv)
(dash.KUNDER / 'normal' / 'DOM.json').unlink()  # domen får inte påverka granskarproven nedan (domda_byggen)
print('ägarbeslut 1: dom och A/B privat/publikt ok')
assert begar(dport, 'GET', '/fil/kunder/dold-abx/RAPPORT.md')[0] == 200, 'efter valet är armen öppen'
# ab.py hash: äldre jämförelse utan hash får den uttryckligen
import ab  # noqa: E402
ab.AB, ab.KUNDER = dash.AB, dash.KUNDER
p2 = dict(p, id='ab-gammal-20261002T000000Z', val=None, korningar={'dold-abx': {'rc': 0}, 'dold-aby': {'rc': 0}})
(dash.AB / 'ab-gammal-20261002T000000Z.json').write_text(json.dumps(p2))
assert ab.main(['hash', 'ab-gammal-20261002T000000Z']) == 0
assert json.loads((dash.AB / 'ab-gammal-20261002T000000Z.json').read_text())['korningar']['dold-abx']['dist_sha256'] == p['korningar']['dold-abx']['dist_sha256']
dsrv.shutdown()
print('F13–F15 dashboard ok')

# ---------------------------------------------------------------- F3/F12/F27: commitvakten i ett eget repo
bare, repo = tmp / 'origin.git', tmp / 'repo'
subprocess.run(['git', 'init', '-q', '--bare', str(bare)], check=True)
subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True)  # noqa: E731
g('config', 'user.email', 'p@x'); g('config', 'user.name', 'p'); g('remote', 'add', 'origin', str(bare))
(repo / 'CLAUDE.md').write_text('x\n'); (repo / 'backlog').mkdir(); (repo / 'backlog' / 'a.md').write_text('a\n')
g('add', '-A'); g('commit', '-q', '-m', 'start'); g('push', '-q', 'origin', 'main')
hook = repo / '.claude' / 'hooks'; hook.mkdir(parents=True); shutil.copy(ROOT / '.claude/hooks/commitvakt.py', hook / 'commitvakt.py')


def vakt(cmd, **env):
    p = subprocess.run([PY, '-B', str(hook / 'commitvakt.py')], input=json.dumps({'tool_name': 'Bash', 'tool_input': {'command': cmd}, 'cwd': str(repo)}),
                       capture_output=True, text=True, env={**os.environ, 'NWP_COMMIT_TILLATET': 'backlog/', **env})
    return p.returncode, p.stderr.strip()


(repo / 'paths.txt').write_text('CLAUDE.md\n')
for cmd, vantat in [('git add backlog/../CLAUDE.md', 2), ('git add ./backlog/b.md', 0), ('git add -f backlog/b.md', 2), ('git add --pathspec-from-file=paths.txt', 2),
                    ('git commit --only -- CLAUDE.md', 2), ('git commit -m x CLAUDE.md', 2), ('git commit -am x', 2), ('git commit --amend -m x', 2),
                    ('git commit --only --pathspec-from-file=paths.txt -m audit', 2), ('git commit -m x --no-verify', 2), ('git commit --include -m x', 2),
                    ('git commit -m "backlog/x"', 0), ('git commit -q -m x -- backlog/b.md', 0), ('git commit --message=x --no-edit', 0),
                    ('git push origin main', 0), ('git push --force origin main', 2), ('git -c core.pager=cat log', 2)]:
    rc, err = vakt(cmd); assert rc == vantat, (cmd, rc, err)
rc, err = vakt('git push origin main', NWP_COMMITVAKT_BUDGET='0'); assert rc == 2 and 'tidsbudget' in err, err  # F12: slut på budget nekar
nyckel = 'RESEND_API_NYCKEL=re_abcdefghijklmnopqrstuvwxyz0123'
(repo / 'backlog' / 'n.md').write_text(nyckel + '\n'); g('add', 'backlog/n.md')
rc, err = vakt('git commit -m x'); assert rc == 2 and 'hemlighet' in err and 'backlog/n.md rad 1' in err and 're_abcdef' not in err, err  # maskerat
g('reset', '-q', 'backlog/n.md'); (repo / 'backlog' / 'n.md').write_text('ren\n'); g('add', 'backlog/n.md'); g('commit', '-q', '-m', 'ren')
(repo / 'backlog' / 'n.md').write_text(nyckel + '\n')  # spårad fil, hemligheten bara i arbetskopian: git commit -- FIL tar den
rc, err = vakt('git commit -m x -- backlog/n.md'); assert rc == 2 and 'hemlighet' in err and 're_abcdef' not in err, err
rc, err = vakt('git commit -m x'); assert rc == 0, err  # utan sökväg committas index, som är rent
(repo / 'backlog' / 'n.md').write_text('ren\n')
(repo / 'backlog' / 'h.md').write_text('sk-ant-api03-abcdefghijklmnopqrstuvwxyz\n'); g('add', 'backlog/h.md'); g('commit', '-q', '-m', 'lägg till')
(repo / 'backlog' / 'h.md').write_text('rent\n'); g('commit', '-q', '-am', 'ta bort')
assert 'sk-ant' not in g('diff', 'origin/main..HEAD').stdout, 'nettodiffen ska vara ren'
rc, err = vakt('git push origin main'); assert rc == 2 and 'hemlighet' in err and 'sk-ant-api03' not in err, err  # historiken, maskerat
g('reset', '-q', '--hard', 'origin/main')
(repo / 'CLAUDE.md').write_text('z\n'); g('commit', '-q', '-am', 'ändra'); (repo / 'CLAUDE.md').write_text('x\n'); g('commit', '-q', '-am', 'tillbaka')
rc, err = vakt('git push origin main'); assert rc == 2 and 'CLAUDE.md' in err, err
g('remote', 'remove', 'origin'); rc, err = vakt('git push origin main'); assert rc == 2, err
print('F3/F12/F27 commitvakten ok')

# ---------------------------------------------------------------- F4: symlänkar ut ur dist/, också felsidan
import prova  # noqa: E402
dist = tmp / 'dist'; dist.mkdir(); (dist / 'index.html').write_text('<p>hej</p>')
hemlig = tmp / 'hemlig.txt'; hemlig.write_text('hemligt'); os.symlink(hemlig, dist / 'lank.txt'); os.symlink(tmp, dist / 'upp'); os.symlink(hemlig, dist / '404.html')
with prova.Server(dist) as srv:
    def status(vag):
        try:
            with urllib.request.urlopen(srv.url + vag, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
    assert status('/')[0] == 200 and status('/lank.txt')[0] == 404 and status('/upp/hemlig.txt')[0] == 404
    kod, kropp = status('/saknas'); assert kod == 404 and b'hemligt' not in kropp, kropp
print('F4 symlänk ok')

# ---------------------------------------------------------------- F5/F24: hämtaren
import hamta_sajt as hs  # noqa: E402
rot = tmp / 'sajt'; rot.mkdir()
(rot / 'index.html').write_text('<html><body><a href="/private/a">p</a><a href="/public/b.html">q</a><a href="/omd">o</a></body></html>')
(rot / 'public').mkdir(); (rot / 'public' / 'b.html').write_text('<html><body>b</body></html>')
(rot / 'robots.txt').write_text('User-agent: *\nDisallow: /private/*\nAllow: /private/open$\nDisallow: /*.pdf$\nDisallow: /dold/\nCrawl-delay: 0\n')
sedda_vardar = []


class Omd(Tyst):
    def do_GET(self):
        sedda_vardar.append(self.headers.get('Host'))
        if self.path == '/omd':
            self.send_response(302); self.send_header('Location', 'http://intern.test:%d/' % self.server.server_port); self.send_header('Content-Length', '0'); self.end_headers(); return
        if self.path == '/annan':
            self.send_response(302); self.send_header('Location', 'http://example.org/'); self.send_header('Content-Length', '0'); self.end_headers(); return
        if self.path == '/till-dold':
            self.send_response(302); self.send_header('Location', '/dold/sida'); self.send_header('Content-Length', '0'); self.end_headers(); return
        super().do_GET()


srv, bas = server(rot, functools.partial(Omd, directory=str(rot)))
port = srv.server_port
rp = hs.Robots(); rp.parse((rot / 'robots.txt').read_text().splitlines())
assert not rp.can_fetch('nortropic-webb-pro', bas + '/private/a') and rp.can_fetch('nortropic-webb-pro', bas + '/private/open')
assert not rp.can_fetch('nortropic-webb-pro', bas + '/x/fil.pdf') and rp.can_fetch('nortropic-webb-pro', bas + '/x/fil.pdfx')
# RFC 9309-fallen ur omgranskningen
r2 = hs.Robots(); r2.parse(['User-agent: *', 'Disallow: /secret', 'Allow: /secret%2A'])
assert not r2.can_fetch('x', 'http://a/secret-anything'), '%2A är ett bokstavligt tecken, inte jokertecken'
r3 = hs.Robots(); r3.parse(['User-agent: *', 'Disallow: /admin/', 'Allow: /admin%2Fpublic$'])
assert not r3.can_fetch('x', 'http://a/admin/public'), '%2F är ett kodat snedstreck, inte ett avgränsande'
r4 = hs.Robots(); r4.parse(['User-agent: a', 'Crawl-delay: 1', 'User-agent: b', 'Disallow: /x'])
assert not r4.can_fetch('a', 'http://a/x') and not r4.can_fetch('b', 'http://a/x') and r4.crawl_delay('a') == 1.0, 'crawl-delay delar inte gruppen'
r5 = hs.Robots(); r5.parse(['User-agent: *', 'Disallow: /'])
assert r5.can_fetch('x', 'http://a/robots.txt') and not r5.can_fetch('x', 'http://a/'), 'robots.txt är underförstått tillåten'
# adresser: bokstavlig loopback nekas utan lokalt läge; i lokalt läge tillåts den, men ett värdnamn mot egna nätet nekas
hs.TILLAT_LOKALT = False; hs._adresser.clear()
s = hs.hamta(bas + '/'); assert s['status'] is None and 'egna nätet' in s['fel'], s
hs.TILLAT_LOKALT = True; hs._adresser.clear()
upplos_orig = hs._upplos
hs._upplos = lambda v: {'intern.test': {'127.0.0.1'}, 'finns-inte.test': set(), 'publik.test': {'8.8.8.8'}}.get(v, upplos_orig(v))
s = hs.hamta('http://intern.test:%d/' % port); assert s['status'] is None and 'egna nätet' in s['fel'], s
s = hs.hamta('http://finns-inte.test/'); assert s['status'] is None and 'slå upp' in s['fel'], s
s = hs.hamta(bas + '/omd'); assert s['status'] == 302 and 'intern.test' in s['url'] and 'egna nätet' in s['fel'], s  # lokal start, omdirigering till värdnamn i egna nätet
s = hs.hamta(bas + '/annan', egen='127.0.0.1'); assert s['status'] == 302 and s['url'] == 'http://example.org/' and 'annan domän' in s['fel'], s
s = hs.hamta(bas + '/till-dold', egen='127.0.0.1', rp=rp); assert s['status'] == 302 and 'robots' in s['fel'], s  # omdirigeringsmål prövas mot robots
s = hs.hamta('file:///etc/hosts'); assert s['status'] is None and 'bara http' in s['fel'], s
# anslutningen går till den validerade adressen, inte till ett nytt uppslag: publik.test → 8.8.8.8 valideras, transporten
# får just den adressen (här omdirigerad till provservern), och Host-huvudet bär namnet
anslutningar = []
cc_orig = socket.create_connection
hs.socket.create_connection = lambda adress, *a, **k: (anslutningar.append(adress), cc_orig(('127.0.0.1', port) if adress[0] == '8.8.8.8' else adress, *a, **k))[1]
s = hs.hamta('http://publik.test:%d/public/b.html' % port)
hs.socket.create_connection = cc_orig
assert s['status'] == 200 and anslutningar == [('8.8.8.8', port)] and sedda_vardar[-1] == 'publik.test:%d' % port, (s, anslutningar, sedda_vardar[-3:])
hs._upplos = upplos_orig; hs._adresser.clear()
r = hs.hamta_sajt(bas + '/', tmp / 'ut', paus=0)
assert r['nekade'] == 1 and r['sidor'] == 2, r
srv.shutdown()
# standardkontrollens länkkontroll går samma väg
import standard_kontroll as sk  # noqa: E402
hs.TILLAT_LOKALT = False; hs._adresser.clear()
d2 = tmp / 'dist2'; d2.mkdir(); (d2 / 'index.html').write_text('<link rel="canonical" href="https://egen.se/"><a href="http://127.0.0.1:4771/api/visa/x">lokal</a>')
assert sk.utgaende(d2)[0]['svar'].startswith('ej prövad ('), sk.utgaende(d2)
hs.TILLAT_LOKALT = True; hs._adresser.clear()
print('F5/F24 hämtaren ok')

# ---------------------------------------------------------------- F6/F7: utskick
import utskick as u, prospektfiler as pf  # noqa: E402
post = {'slug': 'x', 'status': 'utkast', 'fysisk_person': False, 'jurform': '49', 'jurform_text': 'Övriga aktiebolag', 'sparr': {'reklam': False, 'epost': False}}
god = {'text_sha': pf.text_sha('Hej', 'Brevet'), 'mottagare': 'info@x.se', 'slug': 'x', 'bekraftad_person': False}
brev = {'utkast': {'amne': 'Hej', 'text': 'Brevet'}, 'godkand': god, 'mottagare': {'epost': 'info@x.se', 'typ': 'roll', 'bekraftad_person': False}}
assert u.far_skickas(post, brev, [], False, True) == (True, 'ok')
for b_, p_, vantat in ((dict(brev, mottagare={'epost': 'kontakt@x.se', 'typ': 'roll'}), post, 'annan mottagare'), (brev, dict(post, slug='y'), 'annan mottagare'),
                       (dict(brev, godkand={'text_sha': god['text_sha']}), post, 'annan mottagare')):
    ok, skal = u.far_skickas(p_, b_, [], False, True); assert not ok and vantat in skal, skal
ok, skal = u.far_skickas(post, brev, None, False, True); assert not ok and 'spärrlistan' in skal, skal
u.SPARR = tmp / 'SPARR.json'; assert u.las_sparr() == []
u.SPARR.write_text('{trasig'); assert u.las_sparr() is None
try:
    u.sparr_lagg('a@x.se', 'prov', spegla=False); raise AssertionError('skriv inte över en trasig lista')
except u.Nekad:
    pass
print('F6/F7 utskick ok')

# ---------------------------------------------------------------- F8/F17/F18: granskaren på riktigt, med en falsk claude
import granska as gr  # noqa: E402
k = tmp / 'kunder'
for s in ('ett-abx', 'ett-aby', 'annat'):
    (k / s).mkdir(parents=True, exist_ok=True)
(k / 'ett-abx' / 'AB-SYSKON').write_text('ett-aby\n'); (k / 'ett-aby' / 'AB-SYSKON').write_text('ett-abx\n')
for s in ('ett-aby', 'annat'):
    (k / s / 'DOM.json').write_text(json.dumps({'domar': [{'svar': {'namn': 'Ja, som den är', 'specifik': 5}}]}))
gr.KUNDER, gr.UNDERLAG, gr.ROOT = k, tmp / 'underlag', tmp
(tmp / 'underlag' / 'ett-abx').mkdir(parents=True, exist_ok=True)
(tmp / 'LARDOMAR.md').write_text('# Lärdomar\n\n## L1 · 2026-10-01 · annat\n\n- bra\n\n## L2 · 2026-10-02 · ett-aby\n\n- facit\n\n'
                                 '## AB · 2026-10-02 · effort: A=medium mot B=high\n\n- val B\n\n## AB · 2026-10-03 · atelje: A=av mot B=pa\n\n- **Byggen:** tva-abx, tva-aby\n- val A\n')
(tmp / 'kritik').mkdir(exist_ok=True); (tmp / 'kritik' / 'GRANSKARE.md').write_text('k'); (tmp / 'kritik' / 'SCHEMA-granskning.json').write_text('{}'); (tmp / 'kritik' / 'SCHEMA-originalitet.json').write_text('{}')
gr.SCHEMA, gr.SCHEMA_ORIGINALITET = tmp / 'kritik' / 'SCHEMA-granskning.json', tmp / 'kritik' / 'SCHEMA-originalitet.json'
(tmp / 'kunskap').mkdir(exist_ok=True); (tmp / 'kunskap' / 'byggstandard.md').write_text('standard v1')
assert [p.name for p, _ in gr.domda_byggen('ett-abx')] == ['annat'], 'syskonets dom ska undantas'
(tmp / 'underlag' / 'LARDOMAR-original.md').write_text((tmp / 'LARDOMAR.md').read_text().replace('- bra', '- bra (privat-ord)'))
rdir0 = tmp / 'runda0'; rdir0.mkdir()
text = gr.lardomar_utan('ett-abx', rdir0).read_text()
assert 'privat-ord' in text, 'utdraget ska komma ur den privata originalfilen när den finns (ägarbeslut 2026-10-03)'
assert 'facit' not in text and 'ett-aby' not in text and '## L1' in text, text
assert 'effort: A=medium' not in text, 'omärkt A/B-avsnitt ska bort (F17)'
assert 'atelje: A=av' in text, 'märkt A/B-avsnitt om andra byggen ska vara kvar'
assert 'atelje: A=av' not in gr.lardomar_utan('tva-abx', rdir0).read_text(), 'märkt A/B-avsnitt om bygget ska bort'
assert 'Read(./LARDOMAR.md)' in gr.nekas_for('ett-abx') and any('ett-aby/DOM.json' in x for x in gr.nekas_for('ett-abx'))
assert 'Read(./underlag/LARDOMAR-original.md)' in gr.nekas_for('ett-abx'), 'granskaren får inte läsa den privata originalfilen'
m1 = gr.metod_sha('ett-abx')
(tmp / 'kritik' / 'GRANSKARE.md').write_text('k2'); m2 = gr.metod_sha('ett-abx'); assert m2 != m1, 'ändrade kriterier ska ge ny metodhash'
(tmp / 'kunskap' / 'byggstandard.md').write_text('standard v2'); m3 = gr.metod_sha('ett-abx'); assert m3 != m2, 'ändrad byggstandard ska ge ny metodhash (F18)'
(tmp / 'underlag' / 'ett-abx' / 'BRIEF.md').write_text('krav'); assert gr.metod_sha('ett-abx') != m3, 'ändrad brief ska ge ny metodhash (F18)'
m4 = gr.metod_sha('ett-abx'); (tmp / 'kunskap' / 'visuell-niva.md').write_text('nivå v1'); m5 = gr.metod_sha('ett-abx'); assert m5 != m4, 'nivåfilen ingår i metodhashen (Codex R30)'
(tmp / 'kunskap' / 'visuell-niva.md').write_text('nivå v2'); assert gr.metod_sha('ett-abx') != m5, 'ändrad nivåfil ska ge ny metodhash'
upp = {'metod_sha': m1, 'modell': 'opus[1m]', 'effort': 'high', 'granskare': 2, 'originalitet': 'skugga'}
assert gr.samma_metod(dict(upp), upp) and not gr.samma_metod(dict(upp, granskare=1), upp) and not gr.samma_metod({}, upp)
# falsk claude: svarar som granskare; PROV_FALL styr vem som faller
bin_ = tmp / 'bin'; bin_.mkdir()
krit = json.dumps({n: {'betyg': 8, 'motivering': '', 'visa': True} for n in gr.KRITERIER})
(bin_ / 'claude').write_text('''#!/bin/bash
cat >/dev/null
alla="$*"
case "$PROV_FALL" in
  granskare2) [[ "$alla" == *"/runda-01-2 "* ]] && { echo '{"is_error": true, "result": "föll"}'; exit 1; };;
  originalitet) [[ "$alla" == *"--max-turns 40 "* ]] && exit 1;;
esac
if [[ "$alla" == *"--max-turns 40 "* ]]; then echo '{"structured_output": {"betyg": 8, "motivering": "", "visa": true}, "num_turns": 1}'; exit 0; fi
echo '{"structured_output": {"kriterier": %s, "blockerande": [], "forbattringar": [], "styrkor": [], "sett": [], "ej_bedomt": [], "kognitiv_genomgang": [], "likhet_tidigare": "", "sammanfattning": ""}, "num_turns": 1, "duration_ms": 1, "session_id": "s"}'
''' % krit)
(bin_ / 'claude').chmod(0o755)
os.environ['PATH'] = str(bin_) + os.pathsep + os.environ.get('PATH', '')
kund = k / 'ett-abx'; (kund / 'sajt' / 'dist').mkdir(parents=True); (kund / 'sajt' / 'dist' / 'index.html').write_text('<p>x</p>')
(kund / 'prov' / 'inspektion' / 'hem').mkdir(parents=True); (kund / 'prov' / 'inspektion' / 'hem' / 'vy-390-forsta.png').write_bytes(b'\x89PNG')


def omgang(n, fall, originalitet):
    rdir = kund / 'granskning' / ('runda-%02d' % n); rdir.mkdir(parents=True)
    gr.satt_utfall(rdir, 'pagar', 'prov')  # som drivaren: formatmarkören före start (Codex R39)
    gr.frys_bygget(kund, rdir)  # som drivaren: bygget fryses förankrat före arbetaren (Codex R24)
    (rdir / 'UPPDRAG.json').write_text(json.dumps({'slug': 'ett-abx', 'runda': 1, 'korning': 'prov', 'tid': gr.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'),
                                                   'modell': 'm', 'effort': 'e', 'frist': 60, 'granskare': 2, 'originalitet': originalitet, 'metod_sha': gr.metod_sha('ett-abx')}))  # bokförd nu: underlaget ändrades efter m1 (omgång tolv, F18)
    os.environ['PROV_FALL'] = fall
    gr.arbetare(rdir)
    return rdir


r1 = omgang(1, 'granskare2', 'av')
assert (r1 / 'FEL.txt').is_file() and 'ofullständig' in (r1 / 'FEL.txt').read_text() and not (r1 / 'GRANSKNING.json').is_file(), 'en fallen granskare ger fel, ingen dom (F8)'
r2 = omgang(2, 'ingen', 'av')
assert json.loads((r2 / 'GRANSKNING.json').read_text())['godkand'] is True and len(json.loads((r2 / 'GRANSKNING.json').read_text())['enskilda']) == 2
r3 = omgang(3, 'originalitet', 'avgor')
assert (r3 / 'FEL.txt').is_file() and 'originalitetsdomaren' in (r3 / 'FEL.txt').read_text(), 'avgörande originalitetsdomare som faller ger fel (F8)'
r4 = omgang(4, 'originalitet', 'skugga')
assert json.loads((r4 / 'GRANSKNING.json').read_text())['godkand'] is True, 'i skugga är bortfallet bara information'
r5 = omgang(5, 'ingen', 'avgor')
g5 = json.loads((r5 / 'GRANSKNING.json').read_text()); assert g5['godkand'] is True and g5['originalitet'] == 'avgor' and g5['metod_sha'] == gr.metod_sha('ett-abx')
assert gr.las_utfall(r5)['status'] == 'klar' and gr.las_utfall(r3)['status'] == 'fel' and (r5 / 'UTFALL.json').is_file(), 'varje omgång får ett slutligt utfall (Codex R38)'
assert json.loads((kund / 'granskning' / 'GRANSKNING.json').read_text())['sammanfattning_av']['runda'] == 'runda-05', 'sammanfattningen är den senaste giltiga omgången'
# Codex R38 F47: ett enda slutligt utfall per omgång, första skrivaren vinner; en avbruten omgång startar inga granskare och
# kan aldrig senare publicera en giltig dom (en sen dom läggs åt sidan); utfall() låter avbrott och fel gå före en dom
r6 = kund / 'granskning' / 'runda-06'; r6.mkdir(); gr.frys_bygget(kund, r6)
(r6 / 'UPPDRAG.json').write_text(json.dumps({'slug': 'ett-abx', 'runda': 6, 'korning': 'prov', 'tid': gr.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'), 'modell': 'm', 'effort': 'e', 'frist': 60, 'granskare': 2, 'originalitet': 'av', 'metod_sha': gr.metod_sha('ett-abx')}))
assert gr.satt_utfall(r6, 'avbruten', 'drivaren: bygget ändrades')['status'] == 'avbruten' and gr.satt_utfall(r6, 'klar', 'sen')['status'] == 'avbruten', 'första skrivaren vinner'
os.environ['PROV_FALL'] = 'ingen'; gr.arbetare(r6)
assert not (r6 / 'GRANSKNING.json').exists() and 'fel' in gr.utfall(r6) and 'avbruten' in gr.utfall(r6)['fel'] and (r6 / 'FEL.txt').is_file(), 'en avbruten omgång startar inga granskare'
r7 = kund / 'granskning' / 'runda-07'; r7.mkdir(); gr.frys_bygget(kund, r7)
(r7 / 'UPPDRAG.json').write_text(json.dumps({'slug': 'ett-abx', 'runda': 7, 'korning': 'prov', 'tid': gr.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'), 'modell': 'm', 'effort': 'e', 'frist': 60, 'granskare': 2, 'originalitet': 'av', 'metod_sha': gr.metod_sha('ett-abx')}))
sla_orig_ = gr.sla_ihop
def sla_och_avbryt_(delar):  # drivaren avbryter medan granskarna arbetar: domen kommer efteråt
    gr.satt_utfall(r7, 'avbruten', 'drivaren: bygget ändrades under granskningen')
    return sla_orig_(delar)
gr.sla_ihop = sla_och_avbryt_; gr.arbetare(r7); gr.sla_ihop = sla_orig_
assert not (r7 / 'GRANSKNING.json').exists() and (r7 / 'GRANSKNING-sen.json').is_file() and json.loads((r7 / 'GRANSKNING-sen.json').read_text())['godkand'] is True and 'fel' in gr.utfall(r7), 'en sen dom efter avbrott publiceras aldrig'
assert json.loads((kund / 'granskning' / 'GRANSKNING.json').read_text())['sammanfattning_av']['runda'] == 'runda-05', 'den sena domen når inte sammanfattningen'
r8 = kund / 'granskning' / 'runda-08'; r8.mkdir(); (r8 / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 8, 'korning': 'prov'})); (r8 / 'FEL.txt').write_text('avbruten: gammal omgång utan UTFALL.json\n')
assert 'fel' in gr.utfall(r8), 'äldre omgång: FEL.txt går före en dom'
(r8 / 'FEL.txt').unlink(); assert gr.utfall(r8)['godkand'] is True
gr.satt_utfall(r8, 'klar', 'x'); assert gr.utfall(r8)['godkand'] is True
# valj_sammanfattning och publicera: senaste giltiga för bygget (dist) och körningen; svara() ändrar inga filer
val_ = gr.valj_sammanfattning(kund / 'granskning', 'prov'); assert val_[0].name == 'runda-08'
val_ = gr.valj_sammanfattning(kund / 'granskning', 'prov', g5['dist_sha256']); assert val_[0].name == 'runda-05', val_[0].name
assert gr.valj_sammanfattning(kund / 'granskning', 'annan-korning') is None and gr.giltiga_rundor(kund / 'granskning', 'prov')[0][0].name == 'runda-02'
rot_fore_ = (kund / 'granskning' / 'GRANSKNING.json').read_text(); gr.svara(kund / 'granskning', r2, json.loads((r2 / 'GRANSKNING.json').read_text()))
assert (kund / 'granskning' / 'GRANSKNING.json').read_text() == rot_fore_, 'svara() läser bara'
pub_ = gr.publicera(kund / 'granskning', 'prov'); assert pub_[0].name == 'runda-08' and json.loads((kund / 'granskning' / 'GRANSKNING.json').read_text())['sammanfattning_av']['runda'] == 'runda-08'
shutil.rmtree(r8); gr.publicera(kund / 'granskning', 'prov')
# Codex R39: en dom i en omgång som ännu är pagar används inte; cacheträffen i main() går genom samma terminalkontroll
r9 = kund / 'granskning' / 'runda-09'; r9.mkdir(); gr.satt_utfall(r9, 'pagar', 'prov')
metod_ettabx = gr.aktuell_metod('ett-abx')
g9 = {'godkand': True, 'runda': 9, 'korning': 'prov', 'tid': gr.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'), 'kriterier': {n_: {'betyg': 8, 'motivering': '', 'visa': True} for n_ in gr.KRITERIER}, 'blockerande': [], 'slug': 'ett-abx', 'modell': metod_ettabx['modell'], 'effort': metod_ettabx['effort'], 'troskel': gr.TROSKEL, **metod_ettabx}
(r9 / 'GRANSKNING.json').write_text(json.dumps(g9)); (r9 / 'GRANSKNING.md').write_text('# r9\n')
assert gr.utfall(r9) is None, 'pagar: domen får inte användas före slutstatus'
assert gr.satt_utfall(r9, 'pagar', 'igen')['status'] == 'pagar' and gr.satt_utfall(r9, 'klar', 'dom')['status'] == 'klar' and gr.satt_utfall(r9, 'pagar', 'x')['status'] == 'klar', 'pagar ersätts bara av ett slutligt utfall'
(kund / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist')}))
max_orig_ = gr.MAX_RUNDOR; gr.MAX_RUNDOR = 1; os.environ['NWP_KORNING'] = 'prov'
import contextlib as cl9_, io as io9_
def driv_():
    buf_ = io9_.StringIO()
    with cl9_.redirect_stdout(buf_):
        rc_ = gr.main(['ett-abx', '--vanta', '5'])
    return rc_, buf_.getvalue()
rc9, ut9 = driv_(); assert rc9 == 0 and 'redan granskat' in ut9, ('cacheträff på en klar godkänd omgång', rc9, ut9[-300:])
(r9 / 'UTFALL.json').write_text(json.dumps({'status': 'avbruten', 'tid': gr.nu(), 'skal': 'prov'}))  # samma dom, men omgången avbruten
rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9 and 'Taket' in ut9, ('avbruten omgång ger ingen cacheträff (vidare till taket)', rc9, ut9[-300:])
(r9 / 'UTFALL.json').write_text(json.dumps({'status': 'fel', 'tid': gr.nu(), 'skal': 'prov'})); rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9
(r9 / 'UTFALL.json').unlink(); (r9 / 'FEL.txt').write_text('avbruten: äldre omgång\n'); rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9, 'äldre FEL.txt: ingen cacheträff'
(r9 / 'FEL.txt').unlink(); rc9, ut9 = driv_(); assert rc9 == 0 and 'redan granskat' in ut9, 'äldre omgång utan fel: cacheträff'
# Codex R40: en befintlig men oläsbar eller ogiltig tillståndsfil är inte äldre format: domen används inte, tillståndet ändras inte, ingen cacheträff
(r9 / 'UTFALL.json').write_text('{trasig')
try:
    gr.satt_utfall(r9, 'klar', 'x'); assert False, 'ogiltig tillståndsfil: ingen tillståndsändring'
except gr.Overifierad:
    pass
assert (r9 / 'UTFALL.json').read_text() == '{trasig' and gr.utfall(r9).get('overifierad') and 'fel' in gr.utfall(r9)
rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9, ('ogiltig tillståndsfil: ingen cacheträff', rc9, ut9[-300:])
(r9 / 'UTFALL.json').write_text(json.dumps({'status': 'okant'})); assert gr.utfall(r9).get('overifierad'); rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9
(r9 / 'UTFALL.json').write_text(json.dumps({'status': 'klar', 'tid': gr.nu(), 'skal': ''})); os.chmod(r9 / 'UTFALL.json', 0o000)
try:
    assert gr.utfall(r9).get('overifierad'), 'oläsbar tillståndsfil'
    try:
        gr.satt_utfall(r9, 'avbruten', 'x'); assert False
    except gr.Overifierad:
        pass
    rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9, ('oläsbar tillståndsfil: ingen cacheträff', rc9, ut9[-300:])
finally:
    os.chmod(r9 / 'UTFALL.json', 0o644)
os.chmod(r9 / 'GRANSKNING.json', 0o000)
try:
    assert gr.utfall(r9).get('overifierad') and 'kan inte verifieras' in gr.utfall(r9)['fel'], 'klar men oläsbar dom'
    rc9, ut9 = driv_(); assert rc9 == 3 and 'redan granskat' not in ut9, ('klar men oläsbar dom: ingen cacheträff', rc9, ut9[-300:])
finally:
    os.chmod(r9 / 'GRANSKNING.json', 0o644)
rc9, ut9 = driv_(); assert rc9 == 0 and 'redan granskat' in ut9, 'återställd omgång: cacheträff igen'
gr.MAX_RUNDOR = max_orig_; os.environ.pop('NWP_KORNING', None); shutil.rmtree(r9); (kund / 'prov' / 'STATUS.json').unlink(); gr.publicera(kund / 'granskning', 'prov')
os.environ.pop('PROV_FALL', None)
print('F8/F17/F18 granskaren ok')

# ---------------------------------------------------------------- F9/F10/F11: ej mätt är inte grönt; korslut
assert prova.seo_rader({'sajt': [{'typ': 'robots.txt saknas', 'text': ''}], 'per_sida': [{'sida': '/', 'fynd': [{'typ': 'x', 'text': 'y'}]}]}) == ['sajt: robots.txt saknas ', '/: x y']
stil = tmp / 'STIL.json'
stil.write_text(json.dumps({'smaYtor': [], 'fel': [{'sida': '/', 'vy': '390', 'fel': 'timeout'}], 'rader': [{'sida': '/om/', 'vy': '390'}]}))
assert [f['sida'] for f in sk.klickytor(stil)] == ['/'], sk.klickytor(stil)
assert sk.klickytor(tmp / 'finns-inte.json')[0]['text'].startswith('klickytorna är inte mätta'), 'saknad stilrapport är fel, inte grönt'
stil.write_text(json.dumps({'smaYtor': [], 'fel': [], 'rader': [{'sida': '/', 'vy': '390'}]})); assert sk.klickytor(stil) == []
korslut = ROOT / 'kontroller' / 'korslut.py'
kk = tmp / 'kund-slut'; (kk / 'prov').mkdir(parents=True); (kk / 'granskning').mkdir()
fore, efter = tmp / 'fore.txt', tmp / 'efter.txt'
fore.write_text('aaa  kontroller/prova.py\nbbb  kunskap/REGISTER.md\nccc  LARDOMAR.md\n')


def slut(rc, efter_text):
    efter.write_text(efter_text)
    p = subprocess.run([PY, '-B', str(korslut), str(kk), rc, str(fore), str(efter)], capture_output=True, text=True)
    return p.returncode, p.stdout


(kk / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'grindar': {'bygge': {'ok': True}}})); (kk / 'RAPPORT.md').write_text('# r')
(kk / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}}))
rc, ut = slut('0', fore.read_text()); assert rc == 1 and 'Inte godkänt' in ut, (rc, ut)  # utan dist/ och stoppvakt är inget godkänt (F11); fullt 0-fall i R3-blocket
rc, ut = slut('0', fore.read_text().replace('bbb', 'bbx')); assert rc == 1 and 'VARNING' in ut and 'kunskap/REGISTER.md' in ut, (rc, ut)  # texter: varning, ingen slutkod 3
rc, ut = slut('0', fore.read_text().replace('aaa', 'aax')); assert rc == 3 and 'kontroller/prova.py' in ut, (rc, ut)  # mekanik: 3
rc, ut = slut('0', fore.read_text() + 'ddd  dashboard/server.py\n'); assert rc == 3, (rc, ut)  # tillkommen fil i mekaniken
assert slut('1', fore.read_text())[0] == 4
(kk / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': False, 'runda': 1, 'kriterier': {}})); assert slut('0', fore.read_text())[0] == 1
print('F9–F11 ej mätt och korslut ok')

# ---------------------------------------------------------------- F19–F22: seo och standard
import seo_kontroll as seo  # noqa: E402
verk = {'namn': 'Holms Konditori', 'kontaktvagar': [{'typ': 'telefon', 'varde': '0920-123 456'}], 'fiktiv': False, 'adress': {'gata': 'Storgatan 1', 'postnummer': '972 31', 'ort': 'Luleå', 'publik': True}}
graf = {'@context': 'https://schema.org', '@graph': [{'@type': 'Bakery', 'name': 'Fel namn', 'address': {'@type': 'PostalAddress', 'postalCode': '972 31', 'addressLocality': 'Luleå', 'streetAddress': 'Storgatan 1'}},
                                                   {'@type': 'WebSite', 'name': 'Holms Konditori'}]}
f = seo.granska_schema(graf, verk)
assert not any(t == 'JSON-LD utan @type' for t, _ in f) and any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), f
f = seo.granska_schema({'@type': ['Bakery', 'LocalBusiness'], 'name': 'Fel namn'}, verk); assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), f
f = seo.granska_schema({'@type': 'Person', 'name': 'Anna Holm', 'telephone': '+46701234567', 'address': {'@type': 'PostalAddress', 'postalCode': '111 11'}}, verk)
assert f == [], 'en Person-nod ska inte prövas mot företagets uppgifter (F20): %s' % f
f = seo.granska_schema({'@type': 'Bakery', 'name': 'Holms Konditori', 'address': {'@type': 'PostalAddress', 'postalCode': '111 11', 'addressLocality': 'Boden', 'streetAddress': 'Storgatan 1'}}, verk)
assert sum(1 for t, _ in f if t == 'schema address ≠ verksamhetens adress') == 2, 'fel postnummer och ort ska ge fynd (F20): %s' % f
assert 'Bakery' in sk.LOKALA_TYPER and 'CafeOrCoffeeShop' in sk.LOKALA_TYPER and 'WebSite' not in sk.LOKALA_TYPER
assert sk.csp_skriptkallor("script-src 'self'; script-src-elem https: 'unsafe-inline'")['script-src-elem'] == ['https:', "'unsafe-inline'"]
d3 = tmp / 'dist3'; d3.mkdir()
(d3 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta http-equiv="content-security-policy" content="default-src \'self\'; script-src \'self\'; script-src-elem https: \'unsafe-inline\'"><title>x</title></head><body><main><h1>x</h1></main></body></html>')
assert any(x['punkt'] == '8.2' and 'script-src-elem' in x['text'] for x in sk.granska(d3)[0]), 'script-src-elem som överstyr ska ge fel (F22)'
print('F19–F22 seo/standard ok')

# ---------------------------------------------------------------- F23: ateljéns panel
import atelje as a  # noqa: E402
arot = tmp / 'atelje'
for n in (1, 2, 3):
    (arot / str(n) / 'undersida').mkdir(parents=True)
    for fil_ in ('vy-390-ruta-01.png', 'vy-1440-ruta-01.png', 'vy-390-hela.png', 'vy-1440-hela.png', 'undersida/vy-390-ruta-01.png', 'undersida/vy-1440-ruta-01.png'):
        (arot / str(n) / fil_).write_bytes(b'x')  # hela startsidan och undersidans början (designprovet)
(arot / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): ['vy-390-ruta-01.png', 'vy-1440-ruta-01.png'] for n in (1, 2, 3)}}))  # det här försökets riktningar (omgång elva, F34)
a.ROOT = tmp; a.KUNDER = k; a.UNDERLAG = tmp / 'underlag'
svar_per_domare = {}


def attrapp(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None):
    karta = {m.group(1): m.group(2) for m in (re.match(r'- riktning ([A-F]): .*?atelje[^/]*/(\d)/', rad) for rad in prompt.splitlines()) if m}
    namn = ut.name.replace('svar-domare-', '').replace('.json', '')
    return {'structured_output': svar_per_domare[namn]({v: b for b, v in karta.items()})}


a.session = attrapp
RB = {'styrkor': '', 'svagheter': '', 'haller_ribban': True, 'niva': 'over'}  # ribbdomen per riktning (designprovet 2026-10-04)
full = lambda bok: {'rangordning': [dict(RB, riktning=bok['2'], plats=1), dict(RB, riktning=bok['1'], plats=2), dict(RB, riktning=bok['3'], plats=3)], 'lana': [], 'motivering': ''}  # noqa: E731
tom = lambda bok: {'rangordning': [], 'lana': [], 'motivering': ''}  # noqa: E731
dubbel = lambda bok: {'rangordning': [dict(RB, riktning=bok['1'], plats=1), dict(RB, riktning=bok['1'], plats=1), dict(RB, riktning=bok['3'], plats=2)], 'lana': [], 'motivering': ''}  # noqa: E731
svar_per_domare.update(formgivning=full, funktion=full, kunden=dubbel)
v = a.panel('prov', arot)
assert v['val'] == 2 and v['poang'] == {1: 2, 2: 4, 3: 0} and v['panel']['kunden'].get('ogiltig'), v
svar_per_domare.update(formgivning=full, funktion=tom, kunden=dubbel)
try:
    a.panel('prov', arot); raise AssertionError('en giltig domare ska inte räcka')
except RuntimeError as e:
    assert 'giltiga domare' in str(e), e
# bildkedjan (designprovet 2026-10-05): en domare vars transkript inte visar de krävda läsningarna får en omdom med listan;
# läser den ändå inte räknas rösten inte. Utan transkript (attrappen ovan) är läsningen overifierad och rösten räknas.
import bildkedja as bk_  # noqa: E402
bk_kat = tmp / 'bk-projekt' / '-prov'; bk_kat.mkdir(parents=True); bk_.PROJEKT = bk_kat.parent; bk_.ROOT = tmp
forsta_ = [str(arot / str(n) / v_) for n in (1, 2, 3) for v_ in ('vy-390-ruta-01.png', 'vy-1440-ruta-01.png')]
anrop_ = []


def attrapp_las(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None):
    namn = ut.name.replace('svar-domare-', '').replace('.json', '')
    anrop_.append(namn)
    sid = '00000000-0000-4000-8000-%012d' % len(anrop_)
    bas = namn.replace('-omdom', '')
    lasta_ = forsta_ if bas == 'formgivning' or (bas == 'kunden' and namn.endswith('-omdom')) else forsta_[:1]
    (bk_kat / (sid + '.jsonl')).write_text('\n'.join(json.dumps({'type': 'assistant', 'message': {'content': [
        {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': f_}}]}}) for f_ in lasta_) + '\n')
    karta = {m.group(1): m.group(2) for m in (re.match(r'- riktning ([A-F]): .*?atelje[^/]*/(\d)/', rad) for rad in prompt.splitlines()) if m}
    return {'structured_output': full({v_: b_ for b_, v_ in karta.items()}), 'session_id': sid}


a.session = attrapp_las
v = a.panel('prov', arot)
assert sorted(anrop_) == ['formgivning', 'funktion', 'funktion-omdom', 'kunden', 'kunden-omdom'], anrop_
assert v['panel']['kunden']['lasning']['omdom'] and not bk_.brister(v['panel']['kunden']['lasning']) and not v['panel']['kunden'].get('ogiltig'), v['panel']['kunden']
assert v['panel']['funktion'].get('ogiltig') and any('funktion: läste inte förslag 1 av 6' in x for x in v['fel']), v['fel']
assert v['val'] == 2 and 'krävs för att rösten ska räknas' not in str(v), 'två giltiga domare räcker; omdomens lista står inte i resultatet'
assert v['panel']['kunden']['lasning']['forsta_sessionen'] is not None, 'den första sessionens förbrukning finns kvar'
# samma fil, inte bara samma slut: en kopia under en annan rot uppfyller inget krav (granskningen av r62, punkt 1)
assert bk_.last('atelje/1/vy-390-ruta-01.png', [str(tmp / 'atelje/1/vy-390-ruta-01.png')]) and bk_.last('atelje/1/vy-390-ruta-01.png', ['./atelje/1/vy-390-ruta-01.png'])
assert not bk_.last('atelje/1/vy-390-ruta-01.png', ['/Volumes/kopia/atelje/1/vy-390-ruta-01.png'])
# ankarna: ägarens ord och varje exempel sett minst en gång (390 eller 1440); huvudreferensens bildval; ett Read som felade räknas inte
ank_ = tmp / 'atelje' / 'ankare'; (ank_ / 'kalibrering').mkdir(parents=True)
md_ = ank_ / 'kalibrering.md'; md_.write_text('# ord')
ank_bilder = [(ank_ / 'kalibrering' / n_, 'K') for n_ in ('K03-vy-390-forsta.png', 'K03-vy-1440-forsta.png', 'K03-vy-1440-hela.png', 'K05-vy-390-forsta.png')]
hr_orig = a.referensval.huvudreferens
a.referensval.huvudreferens = lambda slug, u=None: {'namn': 'Snick', 'vad': '', 'bilder': [(tmp / 'underlag' / 'ref.png', 'fråga')]}
try:
    kr_ = a.lasekrav('prov', (md_, ank_bilder), {1: ['atelje/1/vy-390-ruta-01.png']}, [1])
finally:
    a.referensval.huvudreferens = hr_orig
assert kr_['ankare'] == ['atelje/ankare/kalibrering.md', ['atelje/ankare/kalibrering/K03-vy-390-forsta.png', 'atelje/ankare/kalibrering/K03-vy-1440-forsta.png'],
                         ['atelje/ankare/kalibrering/K05-vy-390-forsta.png']] and kr_['huvudreferens'] == ['underlag/ref.png'] and kr_['förslag'] == ['atelje/1/vy-390-ruta-01.png'], kr_
sid_ = '00000000-0000-4000-8000-000000000077'
(bk_kat / (sid_ + '.jsonl')).write_text('\n'.join(json.dumps(x_) for x_ in (
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't1', 'name': 'Read', 'input': {'file_path': str(md_)}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't2', 'name': 'Read', 'input': {'file_path': str(ank_bilder[1][0])}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't3', 'name': 'Read', 'input': {'file_path': str(ank_bilder[3][0])}}]}},
    {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 't3', 'is_error': True, 'content': 'fel'}]}})) + '\n')
las_ = bk_.lasning(sid_, kr_)
assert las_['grupper']['ankare'] == {'kravda': 3, 'lasta': 2, 'saknas': ['atelje/ankare/kalibrering/K05-vy-390-forsta.png']}, las_
assert bk_.brister(las_) == ['ankare 2 av 3', 'huvudreferens 0 av 1', 'förslag 0 av 1'], bk_.brister(las_)
assert bk_.erbjudna_i_prompt('se kritik/bilder/x.png och /abs/y.PNG, underlag/s/z.webp') == ['/abs/y.PNG', 'underlag/s/z.webp'], 'ingen falsk absolut väg mitt i en relativ'
a.session = attrapp
# rapporten per bygge: en granskares erbjudna bilder (ur PROMPT.txt) mot de lästa, per slag
bk_.KUNDER, bk_.UNDERLAG, bk_.ROOT = tmp / 'bk-kunder', tmp / 'bk-underlag', tmp / 'bk-rot'
bk_r = bk_.KUNDER / 'bk-bygge' / 'granskning' / 'runda-01'; bk_r.mkdir(parents=True)
(bk_r / 'PROMPT.txt').write_text('Läs varje:\n- kunder/bk-bygge/granskning/runda-01/sajt/hem/vy-390-ruta-01.png\n- underlag/bk-bygge/referenser/paket-v01/x/01-start/vy-1440-ruta-02.png\n')
(bk_r / 'svar.json').write_text(json.dumps({'session_id': '00000000-0000-4000-8000-000000000099'}))
(bk_kat / '00000000-0000-4000-8000-000000000099.jsonl').write_text(json.dumps({'type': 'assistant', 'message': {'content': [
    {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': str(tmp / 'bk-rot' / 'kunder/bk-bygge/granskning/runda-01/sajt/hem/vy-390-ruta-01.png')}}]}}) + '\n')
rb_ = bk_.rapport('bk-bygge')['granskningen'][0]
assert rb_['erbjudna'] == 2 and rb_['lasta_av_erbjudna'] == 1 and rb_['saknas_per_klass'] == {'referens': 1}, rb_
assert 'Olästa per slag' in bk_.markdown(bk_.rapport('bk-bygge')) and bk_.transkript('inte-ett-id') is None
print('F23 ateljén ok')

# ---------------------------------------------------------------- F23b: designprovet (ägarbeslut 2026-10-04 via Codex R40; Codex 2026-10-04 glapp 5)


def f23b():  # egen funktion: blockets namn (u, v, p, …) får inte skugga svitens moduler och variabler
    import shutil as shutil_hr
    arot_b = tmp / 'atelje-f23b'  # egen kopia av ateljéroten: F34 nedan räknar med F23:s orörda bilder
    shutil_hr.copytree(arot, arot_b)
    shutil_hr.rmtree(arot_b / '3' / 'undersida', ignore_errors=True)  # riktning 3 saknar undersida i det här blocket
    import re  # noqa: E402
    import io  # noqa: E402
    import contextlib  # noqa: E402
    import zlib  # noqa: E402
    import struct  # noqa: E402
    import referensval as rv_hr  # noqa: E402
    import prova as pv_hr  # noqa: E402
    for n in (1, 2, 3):
        d = arot_b / str(n)
        for i in range(2, 10):
            (d / ('vy-390-ruta-%02d.png' % i)).write_bytes(b'x')
        for i in range(2, 6):
            (d / ('vy-1440-ruta-%02d.png' % i)).write_bytes(b'x')
        (d / 'vy-390-hela.png').write_bytes(b'x'); (d / 'vy-1440-hela.png').write_bytes(b'x'); (d / 'vy-390-forsta.png').write_bytes(b'x')
        if n != 3:
            (d / 'undersida').mkdir(exist_ok=True)
            for fn in ('vy-390-ruta-01.png', 'vy-390-ruta-02.png', 'vy-390-ruta-03.png', 'vy-1440-ruta-01.png', 'vy-1440-ruta-02.png'):
                (d / 'undersida' / fn).write_bytes(b'x')
    pb = [p.name for p in a.panelbilder(arot_b / '1')]
    assert pb.count('vy-390-ruta-08.png') == 1 and 'vy-390-ruta-09.png' not in pb and 'vy-1440-ruta-04.png' in pb and 'vy-1440-ruta-05.png' not in pb, pb
    assert pb[-3:] == ['vy-390-ruta-01.png', 'vy-390-ruta-02.png', 'vy-1440-ruta-01.png'] and str(a.panelbilder(arot_b / '1')[-1].relative_to(arot_b / '1')) == 'undersida/vy-1440-ruta-01.png', pb
    assert 'vy-390-hela.png' in pb and 'vy-1440-hela.png' in pb and 'vy-390-forsta.png' not in pb and len(a.panelbilder(arot_b / '3')) == 14, pb
    (arot_b / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): [] for n in (1, 2, 3)}, 'ofullstandiga': {'3': 'undersidans början saknas'}}))
    prompter = []


    def attrapp2(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None):
        prompter.append(prompt)
        karta = {}
        for rad in prompt.splitlines():
            m = re.match(r'- riktning ([A-F]): .*?atelje[^/]*/(\d)/', rad)
            if m:
                karta[m.group(1)] = m.group(2)
        namn = ut.name.replace('svar-domare-', '').replace('.json', '')
        return {'structured_output': svar_per_domare[namn]({v: b for b, v in karta.items()})}


    a.session = attrapp2
    rb = lambda bok, ja, ordning=(2, 1, 3): {'rangordning': [{'riktning': bok[str(n)], 'plats': i + 1, 'styrkor': '', 'svagheter': '', 'haller_ribban': ja[n], 'niva': 'over' if ja[n] else 'nastan'} for i, n in enumerate(ordning)], 'lana': [], 'motivering': ''}  # noqa: E731
    ingen, bara2 = {1: False, 2: False, 3: False}, {1: False, 2: True, 3: False}
    svar_per_domare.update(formgivning=lambda bok: rb(bok, ingen), funktion=lambda bok: rb(bok, bara2), kunden=lambda bok: rb(bok, ingen))
    v = a.panel('prov', arot_b)
    assert v['val'] is None and v['forkastade'] and v['godkanda'] == [] and v['poang'][2] == 6, 'bäst av tre undermåliga får aldrig bli vald: en domare av tre räcker inte (%s)' % v
    assert v['ribban'][2] == {'formgivning': False, 'funktion': True, 'kunden': False} and v['nivaer'][2] == {'formgivning': 'nastan', 'funktion': 'over', 'kunden': 'nastan'} and v['ankare'] is False and v['ofullstandiga'] == {'3': 'undersidans början saknas'}, v
    p = prompter[-1]
    assert 'atelje-f23b/1/vy-390-hela.png' in p and 'atelje-f23b/1/undersida/vy-390-ruta-01.png' in p and 'vy-390-ruta-08.png' in p and 'vy-390-ruta-09.png' not in p and 'vy-1440-ruta-05.png' not in p, p
    assert 'Ofullständiga riktningar' in p and 'undersidans början saknas' in p and 'kalibreringsankare saknas' in p and 'Frånvaro av gradienter' in p and 'haller_ribban' in p and 'Huvudreferensen' not in p, p
    # majoriteten håller riktning 2 över ribban: vald; riktning 3 hålls av alla men är ofullständig: aldrig godkänd
    alla3 = {1: False, 2: True, 3: True}
    svar_per_domare.update(formgivning=lambda bok: rb(bok, alla3, (3, 2, 1)), funktion=lambda bok: rb(bok, alla3, (3, 2, 1)), kunden=lambda bok: rb(bok, {1: False, 2: False, 3: True}, (3, 2, 1)))
    v = a.panel('prov', arot_b)
    assert v['val'] == 2 and v['godkanda'] == [2] and not v['forkastade'] and v['poang'][3] > v['poang'][2], 'ofullständig riktning får inte vinna fast alla håller den; majoriteten räcker för 2 (%s)' % v
    # en domare utan ribbdom räknas inte
    utan = lambda bok: {'rangordning': [{'riktning': bok[str(n)], 'plats': i + 1, 'styrkor': '', 'svagheter': ''} for i, n in enumerate((2, 1, 3))], 'lana': [], 'motivering': ''}  # noqa: E731
    svar_per_domare.update(formgivning=utan, funktion=lambda bok: rb(bok, bara2), kunden=lambda bok: rb(bok, bara2))
    v = a.panel('prov', arot_b)
    assert v['panel']['formgivning'].get('ogiltig') and any('ribbdom' in f for f in v['fel']) and v['val'] == 2, v
    # VAL.md säger förkastat respektive valt
    svar_per_domare.update(formgivning=lambda bok: rb(bok, ingen), funktion=lambda bok: rb(bok, ingen), kunden=lambda bok: rb(bok, ingen))
    assert a.skriv_val('prov', arot_b)['val'] is None and 'Alla riktningar förkastade' in (arot_b / 'VAL.md').read_text() and 'Ofullständiga riktningar' in (arot_b / 'VAL.md').read_text()
    svar_per_domare.update(formgivning=lambda bok: rb(bok, bara2), funktion=lambda bok: rb(bok, bara2), kunden=lambda bok: rb(bok, ingen))
    assert a.skriv_val('prov', arot_b)['val'] == 2 and 'Vald riktning: **2**' in (arot_b / 'VAL.md').read_text() and '| 2 | 2 av 3 |' in (arot_b / 'VAL.md').read_text(), (arot_b / 'VAL.md').read_text()
    # ägarens kalibreringsankare fryses till panelen; bara ankarhalvan, ägarens ord ordagrant
    ua = tmp / 'underlag-ankare'
    (ua / 'kalibrering' / 'K01' / 'start').mkdir(parents=True); (ua / 'kalibrering' / 'K02' / 'start').mkdir(parents=True)
    for kid in ('K01', 'K02'):
        for vy in ('390', '1440'):
            (ua / 'kalibrering' / kid / 'start' / ('vy-%s-forsta.png' % vy)).write_bytes(b'x')
    (ua / 'kalibrering' / 'DOMAR.json').write_text(json.dumps({'K01': {'niva': 'over', 'skiljer': 'ägarens ord om K01'}, 'K02': {'niva': 'generisk', 'skiljer': 'undanhållen K02'}}))
    (ua / 'kalibrering' / 'ANKARE.txt').write_text('K01 · ankare\n')
    a.UNDERLAG = ua
    v = a.panel('prov', arot_b)
    a.UNDERLAG = tmp / 'underlag'
    assert v['ankare'] is True and 'Ägarens kalibreringsankare' in prompter[-1] and 'atelje-f23b/ankare/kalibrering/K01-vy-390-forsta.png' in prompter[-1] and 'K02' not in prompter[-1], prompter[-1]
    assert 'ägarens ord om K01' in (arot_b / 'ankare' / 'kalibrering.md').read_text() and 'undanhållen' not in (arot_b / 'ankare' / 'kalibrering.md').read_text()
    # finns kalibreringen men går den inte att frysa stoppas panelen; saknas den sägs det högt (granskningen av r53, punkt 9)
    fa_hr = gr.frysta_ankare
    gr.frysta_ankare = lambda rdir, underlag=None: (_ for _ in ()).throw(OSError('trasig bild'))
    a.UNDERLAG = ua
    try:
        a.panel('prov', arot_b); raise AssertionError('en kalibrering som inte kan frysas får inte ge en tyst dom utan ankare')
    except RuntimeError as e:
        assert 'kunde inte frysas' in str(e) and 'trasig bild' in str(e), e
    finally:
        gr.frysta_ankare = fa_hr
        a.UNDERLAG = tmp / 'underlag'
    v = a.panel('prov', arot_b)
    assert v['ankare'] is False and 'saknas i den här utcheckningen' in v['ankare_fel'] and 'saknas (underlag/kalibrering saknas' in prompter[-1], v['ankare_fel']
    # en ja-röst kräver nivån over: ja med nivån nästan räknas som nej (granskningen av r53, punkt 4)
    ja_nastan = lambda bok: {'rangordning': [{'riktning': bok[str(n)], 'plats': i + 1, 'styrkor': '', 'svagheter': '', 'haller_ribban': n == 2, 'niva': 'nastan'} for i, n in enumerate((2, 1, 3))], 'lana': [], 'motivering': ''}  # noqa: E731
    svar_per_domare.update(formgivning=ja_nastan, funktion=ja_nastan, kunden=ja_nastan)
    v = a.panel('prov', arot_b)
    assert v['val'] is None and v['ribban'][2] == {'formgivning': False, 'funktion': False, 'kunden': False} and sum('räknas som nej' in x for x in v['fel']) == 3, v
    # determinism: domarna och lånen i sorterad ordning, fotosetet med i valet
    assert list(v['panel']) == sorted(v['panel']) and len(v['fotoset']) == 64 and v['fotoset'] == a.fotoset_hash(arot_b, [1, 2, 3])
    # fullständigheten prövas på disken: ett äldre manifest utan fältet godkänner ingen halv riktning
    (arot_b / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): [] for n in (1, 2, 3)}}))
    svar_per_domare.update(formgivning=lambda bok: rb(bok, alla3, (3, 2, 1)), funktion=lambda bok: rb(bok, alla3, (3, 2, 1)), kunden=lambda bok: rb(bok, alla3, (3, 2, 1)))
    v = a.panel('prov', arot_b)
    assert '3' in v['ofullstandiga'] and 3 not in v['godkanda'] and v['val'] == 2, v
    # startsidans bilder prövas för sig: undersidans rutor med samma namn räknas inte (granskningen av r53, punkt 11)
    flyttade = []
    for p in sorted((arot_b / '1').glob('vy-390-ruta-*.png')):
        p.rename(p.with_suffix('.bak')); flyttade.append(p)
    try:
        a.panel('prov', arot_b); raise AssertionError('startsidan utan rutor ska stoppa även när undersidan har rutor')
    except RuntimeError as e:
        assert 'startsidans rutor' in str(e), e
    for p in flyttade:
        p.with_suffix('.bak').rename(p)
    (arot_b / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): [] for n in (1, 2, 3)}, 'ofullstandiga': {'3': 'undersidans början saknas'}}))
    # --bara-domare: ägarens verktyg; vägras medan en arbetare lever, och en förkastning av samma fotoset är bindande
    with contextlib.redirect_stdout(io.StringIO()):
        assert a.bara_domare('prov', arot_b, {'pid': os.getpid(), 'steg': 'divergera'}) == 5
    svar_per_domare.update(formgivning=lambda bok: rb(bok, ingen), funktion=lambda bok: rb(bok, ingen), kunden=lambda bok: rb(bok, ingen))
    gamla_bd = (a.stada, a.bygg)
    a.stada = lambda slug: None
    a.bygg = lambda slug: (0, '')
    try:
        (arot_b / 'VINNARE.json').write_text('{"riktning": 2}')
        with contextlib.redirect_stdout(io.StringIO()):
            assert a.bara_domare('prov', arot_b, {}) == 6
        st_bd = json.loads((arot_b / 'STATUS.json').read_text())
        assert st_bd['steg'] == 'forkastad' and st_bd['bara_domare'] and not (arot_b / 'VINNARE.json').exists(), 'en förkastning vid omdömning flyttar undan den tidigare vinnaren'
        prompter.clear()
        ut_bd = io.StringIO()
        with contextlib.redirect_stdout(ut_bd):
            assert a.bara_domare('prov', arot_b, {}) == 6 and 'bindande' in ut_bd.getvalue() and not prompter, 'samma bilder döms inte om tills någon säger ja'
        (arot_b / 'VAL.json').unlink()
        svar_per_domare.update(formgivning=lambda bok: rb(bok, bara2), funktion=lambda bok: rb(bok, bara2), kunden=lambda bok: rb(bok, ingen))
        with contextlib.redirect_stdout(io.StringIO()):
            assert a.bara_domare('prov', arot_b, {}) == 0
        st_bd = json.loads((arot_b / 'STATUS.json').read_text())
        assert st_bd['steg'] == 'klar' and st_bd['val'] == 2 and json.loads((arot_b / 'VINNARE.json').read_text())['riktning'] == 2, st_bd
    finally:
        a.stada, a.bygg = gamla_bd
    # vinnaren bevaras (kod, bilder, hashar); startsidan överförs separat och bara när den bygger (glapp 5, Emils införandesteg)
    sidor = k / 'provhr' / 'sajt' / 'src' / 'pages'
    (sidor / 'atelje-2' / 'undersida').mkdir(parents=True, exist_ok=True)
    kod = "---\nimport b from '../../assets/atelje/x.jpg';\n---\n<img src=\"../../assets/y.png\"><style>@import url(../../x.css);</style>"
    (sidor / 'atelje-2' / 'index.astro').write_text(kod); (sidor / 'atelje-2' / 'undersida' / 'index.astro').write_text('u')
    (sidor / 'index.astro').write_text('gammal')
    mal = a.bevara_vinnare('provhr', arot_b, 2)
    vj = json.loads((arot_b / 'VINNARE.json').read_text())
    assert vj['riktning'] == 2 and (mal / 'kod' / 'index.astro').read_text() == kod and (mal / 'kod' / 'undersida' / 'index.astro').read_text() == 'u', vj
    assert sorted(p.name for p in (mal / 'bilder').iterdir()) == sorted(p.name for p in (arot_b / '2').glob('vy-*.png')) and 'bilder/vy-390-hela.png' in vj['filer'] and 'kod/index.astro' in vj['filer']
    assert vj['overford']['ok'] is False and (sidor / 'index.astro').read_text() == 'gammal', 'bevarandet för inte över startsidan; det gör overfor_startsida efter städningen'
    byggen = []
    a.bygg = lambda slug: (byggen.append(slug), (0, ''))[1]
    ov = a.overfor_startsida('provhr', arot_b)
    assert not ov['ok'] and '../../assets/atelje/x.jpg' in ov['skal'] and (sidor / 'index.astro').read_text() == 'gammal' and not byggen, 'relativa sökvägar stoppar överföringen (granskningen av r53, punkt 6)'
    assert json.loads((arot_b / 'VINNARE.json').read_text())['overford']['ok'] is False
    ren = "---\nimport b from '/src/assets/atelje/x.jpg';\nimport '@fontsource-variable/fraunces';\n---\n<a href=\"/kontakt/\">Skriv</a>"
    (mal / 'kod' / 'index.astro').write_text(ren)
    (mal / 'kod' / 'index.astro').write_text(ren + '<a href="/atelje-2/undersida/">mer</a>')
    ov = a.overfor_startsida('provhr', arot_b)
    assert not ov['ok'] and 'atelje-2' in ov['skal'] and not byggen, 'länkar till ateljésidor stoppar överföringen'
    (mal / 'kod' / 'index.astro').write_text(ren)
    ov = a.overfor_startsida('provhr', arot_b)
    vj = json.loads((arot_b / 'VINNARE.json').read_text())
    assert ov['ok'] and byggen == ['provhr'] and (sidor / 'index.astro').read_text() == ren and (arot_b / 'index-ersatt.astro').read_text() == 'gammal', ov
    assert vj['overford']['ok'] and vj['filer']['overford/src/pages/index.astro'] == ov['sha256'], vj
    (sidor / 'index.astro').write_text('mellan')
    a.bygg = lambda slug: (1, 'build failed: Could not resolve')
    ov = a.overfor_startsida('provhr', arot_b)
    assert not ov['ok'] and 'återställd' in ov['skal'] and (sidor / 'index.astro').read_text() == 'mellan' and (arot_b / 'index-ersatt.astro').read_text() == 'gammal', 'ett fallerat bygge återställer startsidan; den första ersatta bevaras'
    # symlänkar följs aldrig (granskningen av r53, punkt 8)
    a.bygg = lambda slug: (0, '')
    hemlig = tmp / 'hemlig.txt'; hemlig.write_text('hemlig')
    (sidor / 'index.astro').unlink(); (sidor / 'index.astro').symlink_to(hemlig)
    assert a.overfor_startsida('provhr', arot_b)['ok'] and not (sidor / 'index.astro').is_symlink() and hemlig.read_text() == 'hemlig', 'en länkad startsida byts mot en fil; målet orörs'
    (arot_b / '1' / 'vy-390-lank.png').symlink_to(hemlig)
    try:
        a.bevara_vinnare('provhr', arot_b, 1); raise AssertionError('en länkad bild får inte bli en vanlig fil i vinnaren')
    except RuntimeError as e:
        assert 'symlänk' in str(e), e
    (arot_b / '1' / 'vy-390-lank.png').unlink()
    # koden sparas per riktning vid fotograferingen; vinnaren tas därifrån även när sidorna är städade (--bara-domare)
    (sidor / 'atelje-2' / 'stiltavla').mkdir(); (sidor / 'atelje-2' / 'stiltavla' / 'index.astro').write_text('tavla')
    (sidor / 'atelje-2' / 'lank.astro').symlink_to('/etc/hosts')
    sk = a.spara_kod('provhr', arot_b, 2)
    assert sorted(str(p.relative_to(sk)) for p in sk.rglob('*') if p.is_file()) == ['index.astro', 'stiltavla/index.astro', 'undersida/index.astro'], 'koden sparas utan symlänkar'
    assert a.spara_kod('provhr', arot_b, 3) is None, 'ingen sida, ingen kod'
    (sidor / 'atelje-3').symlink_to(sidor / 'atelje-2')
    assert a.spara_kod('provhr', arot_b, 3) is None, 'en länkad ateljésida sparas inte'
    (sidor / 'atelje-3').unlink()
    shutil_hr.rmtree(sidor / 'atelje-2')
    mal = a.bevara_vinnare('provhr', arot_b, 2)
    assert (mal / 'kod' / 'stiltavla' / 'index.astro').read_text() == 'tavla', 'vinnaren ur den sparade koden'
    # verksamhetens egna bilder ur BILDER.md i skillens format (fil, källa, vad, datum, kvalitet), med eller utan kolumnen Egen
    ub = tmp / 'underlag-bilder'; (ub / 'bild-prov' / 'bilder').mkdir(parents=True)
    for fn in ('a.jpg', 'b.jpg', 'c.jpg', 'logo.png'):
        (ub / 'bild-prov' / 'bilder' / fn).write_bytes(b'x')
    (ub / 'bild-prov' / 'bilder' / 'BILDER.md').write_text('| Fil | Källa | Vad | Datum | Kvalitet |\n|---|---|---|---|---|\n| a.jpg | sajten | huset | okänt | skarp |\n| b.jpg | sajten | stockfoto från Envato | okänt | ok |\n| logo.png | sajten | loggan | — | vit |\n\n**Borttagna:** c.jpg (stock)\n')
    gu_b = a.UNDERLAG; a.UNDERLAG = ub
    try:
        assert a.egna_bilder('bild-prov') == ['a.jpg', 'logo.png'], 'skillens format: varje listad fil utom stock (%s)' % a.egna_bilder('bild-prov')
        (ub / 'bild-prov' / 'bilder' / 'BILDER.md').write_text('| Fil | Vad | Egen |\n|---|---|---|\n| a.jpg | huset | ja |\n| c.jpg | lånad | nej |\n')
        assert a.egna_bilder('bild-prov') == ['a.jpg'], 'kolumnen Egen gäller när den finns'
        (ub / 'bild-prov' / 'bilder' / 'BILDER.md').unlink()
        assert a.egna_bilder('bild-prov') == ['a.jpg', 'b.jpg', 'c.jpg', 'logo.png'], 'utan BILDER.md alla bilder'
    finally:
        a.UNDERLAG = gu_b
    # konsolfel gör en riktning ofullständig (Emils prototypmodul: varje variant fungerar helt)
    (tmp / 'insp-k').mkdir()
    (tmp / 'insp-k' / 'INSPEKTION.json').write_text(json.dumps({'vyer': {'390': {'konsol': [{'typ': 'error', 'text': 'Failed to load resource: 404'}, {'typ': 'log', 'text': 'ok'}], 'sidfel': [{'text': 'x is not defined'}]}}}))
    assert a.konsolfel(tmp / 'insp-k') == ['390: Failed to load resource: 404', '390: sidfel x is not defined'] and a.konsolfel(tmp / 'saknas') == []
    # huvudreferensen ur REFERENSER.md; ateljén startar inte utan den
    u = tmp / 'underlag' / 'provhr'
    for namn in ('BRIEF.md', 'RESEARCH.md', 'INNEHALL.md'):
        (u / namn).parent.mkdir(parents=True, exist_ok=True); (u / namn).write_text('x')
    (k / 'provhr' / 'sajt').mkdir(parents=True, exist_ok=True); (k / 'provhr' / 'sajt' / 'package.json').write_text('{}')
    (u / 'referenser' / 'paket-v01' / 'snick' / '01-start').mkdir(parents=True)
    (u / 'referenser' / 'paket-v01' / 'snick' / '01-start' / 'vy-390-ruta-01.png').write_bytes(b'x')
    (u / 'referenser' / 'paket-v01' / 'annan' / '01-start').mkdir(parents=True)
    (u / 'referenser' / 'paket-v01' / 'annan' / '01-start' / 'vy-390-ruta-02.png').write_bytes(b'x')
    (u / 'REFERENSER.md').write_text('# Referenser\n\n## Snick — snickeri i Umeå\n\nBildval: referenser/paket-v01/snick/01-start/vy-390-ruta-01.png — första vyn — Fråga: bär vår lika mycket?\n\n## Annan\n\nBildval: referenser/paket-v01/annan/01-start/vy-390-ruta-02.png — tjänsterna — Fråga: lika tydlig?\n')
    assert rv_hr.huvudreferens('provhr', tmp / 'underlag') is None
    ut_main = io.StringIO()
    with contextlib.redirect_stdout(ut_main):
        rc_main = a.main(['provhr'])
    assert rc_main == 2 and 'Huvudreferens' in ut_main.getvalue(), ut_main.getvalue()
    (u / 'REFERENSER.md').write_text((u / 'REFERENSER.md').read_text() + '\nHuvudreferens: Sni — komposition\n')
    ut_main = io.StringIO()
    with contextlib.redirect_stdout(ut_main):
        rc_main = a.main(['provhr'])
    assert rc_main == 2 and 'inga läsbara Bildval-bilder' in ut_main.getvalue() and rv_hr.huvudreferens('provhr', tmp / 'underlag')['bilder'] == [], 'Sni träffar inte Snick: exakt rubriknamn (%s)' % ut_main.getvalue()
    assert rv_hr.rubriknamn('## **Snick** — snickeri') == 'snick' and rv_hr.rubriknamn('Snickarglädje: kök') == 'snickarglädje' and rv_hr.rubriknamn('Annan') == 'annan'
    assert rv_hr.rubriknamn('Ashton Bespoke · bransch · https://www.ashtonbespoke.co.uk/') == 'ashton bespoke', 'rubrikformen namn · roll · adress'
    (u / 'REFERENSER.md').write_text((u / 'REFERENSER.md').read_text().replace('Huvudreferens: Sni — komposition', 'Huvudreferens: Snick — komposition, typografi och bildbehandling'))
    hr = rv_hr.huvudreferens('provhr', tmp / 'underlag')
    assert hr['namn'] == 'Snick' and hr['vad'] == 'komposition, typografi och bildbehandling' and [t for _, t in hr['bilder']] == ['första vyn — Fråga: bär vår lika mycket?'], hr
    # raden är entydig: kodstaket räknas inte, fet stil och listprefix godtas, två olika huvudreferenser är tvetydigt
    ref_text = (u / 'REFERENSER.md').read_text()
    (u / 'REFERENSER.md').write_text(ref_text + '\n```\nHuvudreferens: Annan — exempel i ett kodstaket\n```\n')
    assert rv_hr.huvudreferens('provhr', tmp / 'underlag')['namn'] == 'Snick', 'en rad i ett kodstaket räknas inte'
    (u / 'REFERENSER.md').write_text(ref_text.replace('Huvudreferens: Snick', '- **Huvudreferens:** Snick'))
    assert rv_hr.huvudreferens('provhr', tmp / 'underlag')['namn'] == 'Snick', 'fet stil och listprefix godtas'
    (u / 'REFERENSER.md').write_text(ref_text + '\nHuvudreferens: Annan — allt\n')
    assert rv_hr.huvudreferens('provhr', tmp / 'underlag') is None and 'flera olika' in rv_hr.huvudreferens_fel('provhr', tmp / 'underlag'), 'två olika huvudreferenser är tvetydigt'
    (u / 'REFERENSER.md').write_text(ref_text)
    dp = a.divergera_prompt('provhr', [])
    assert 'Huvudreferensen är Snick: komposition, typografi och bildbehandling' in dp and 'Dess bilder: underlag/provhr/referenser/paket-v01/snick/01-start/vy-390-ruta-01.png — första vyn — Fråga: bär vår lika mycket?.' in dp, dp
    assert 'undersida/index.astro' in dp and 'stiltavla/index.astro' in dp and 'style tile' not in dp and '/src/assets/atelje/' in dp and 'Förra omgången' not in dp, dp
    assert 'skiljer sig inom huvudreferensen' in dp and 'aldrig för helheten' in dp and 'konsolfel' in dp and 'skriv vilken referens' not in dp, 'variationen ryms i huvudreferensen'
    assert 'Förra omgången förkastades' in a.divergera_prompt('provhr', [], 'kritik: platt') and 'kritik: platt' in a.divergera_prompt('provhr', [], 'kritik: platt')
    dmp = a.domar_prompt('provhr', 'uppdraget', [('A', 1), ('B', 2)], {1: ['x'], 2: ['y']}, None)
    assert 'Huvudreferensen som alla riktningar ska bära i komposition, typografi, proportioner och bildbehandling: Snick' in dmp and 'kalibreringsankare saknas' in dmp, dmp
    # divergensomgångar: förkastat → ny omgång med kritiken, sedan stopp (slutkod 6 i vanta)
    gamla = {n: getattr(a, n) for n in ('session', 'fotografera', 'skriv_val', 'bevara_vinnare', 'stada', 'egna_bilder', 'OMGANGAR', 'overfor_startsida', 'bygg')}
    rot2 = u / 'atelje'
    rot2.mkdir(parents=True, exist_ok=True)
    utfall = iter([None, 2])
    prompter.clear()
    a.session = lambda prompt, verktyg, ut, **kw: (prompter.append(prompt), {})[1]
    a.fotografera = lambda slug, rot: []


    def falskt_val(slug, rot):
        vv = next(utfall)
        (rot / 'VAL.md').write_text('# val\n\nkritik: för platt' if vv is None else '# val\n\nVald riktning: **2**')
        return {'val': vv}


    a.skriv_val = falskt_val
    bevarade = []
    a.bevara_vinnare = lambda slug, rot, n: bevarade.append(n)
    a.stada = lambda slug: None
    a.egna_bilder = lambda slug: []
    a.overfor_startsida = lambda slug, rot: {'ok': True, 'skal': 'prov', 'sha256': None}
    a.OMGANGAR = 2
    (rot2 / 'VINNARE.json').write_text('{"riktning": 1}'); (rot2 / 'vinnare').mkdir(); (rot2 / 'VAL.md').write_text('förra körningens val')
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'klar' and st['val'] == 2 and st['omgangar'] == 2 and bevarade == [2] and st['overford'] is True, st
    assert len(prompter) == 2 and 'Förra omgången förkastades' in prompter[1] and 'kritik: för platt' in prompter[1] and 'Förra omgången' not in prompter[0], prompter
    assert (rot2 / 'omgang-1' / 'VAL.md').read_text().endswith('kritik: för platt'), 'den förkastade omgången bevaras i omgang-1/'
    forra = list((rot2 / 'foregaende').iterdir())
    assert len(forra) == 1 and (forra[0] / 'VINNARE.json').is_file() and (forra[0] / 'VAL.md').read_text() == 'förra körningens val' and not (rot2 / 'VINNARE.json').exists(), 'en ny körning flyttar undan den förra vinnaren (granskningen av r53, punkt 3)'
    with contextlib.redirect_stdout(io.StringIO()):
        assert a.vanta(rot2, 1) == 0
    utfall = iter([None, None])
    bevarade.clear(); prompter.clear()
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'forkastad' and st['val'] is None and bevarade == [] and len(prompter) == 2 and 'stannar' in st['skal'], st
    assert (rot2 / 'VAL.md').is_file() and (rot2 / 'omgang-1').is_dir() and len(list((rot2 / 'foregaende').iterdir())) == 2, 'sista omgången står kvar i roten'
    ut_v = io.StringIO()
    with contextlib.redirect_stdout(ut_v):
        assert a.vanta(rot2, 1) == 6
    assert 'förkastade alla riktningar' in ut_v.getvalue()
    with contextlib.redirect_stdout(io.StringIO()):
        assert a.main(['provhr']) == 6, 'ett förkastat resultat startar ingen ny ateljé utan --om'
    os.environ['NWP_SLUG'] = 'provhr'
    try:
        ut_om = io.StringIO()
        with contextlib.redirect_stdout(ut_om):
            assert a.main(['provhr', '--om']) == 6 and 'inte inifrån bygget' in ut_om.getvalue(), 'inifrån bygget startar --om ingen ny ateljé efter en förkastning'
            assert a.main(['provhr', '--bara-domare']) == 2, '--bara-domare är ägarens verktyg, inte byggets'
    finally:
        del os.environ['NWP_SLUG']
    # arbetaren kräver huvudreferensen varje omgång (granskningen av r53, punkt 10)
    (u / 'REFERENSER.md').write_text(ref_text.replace('Huvudreferens: Snick — komposition, typografi och bildbehandling', ''))
    utfall = iter([2]); prompter.clear()
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'fel' and 'huvudreferensen saknas' in st['fel'] and not prompter, st
    (u / 'REFERENSER.md').write_text(ref_text)
    # tidsgränsen (designprovet 2026-10-05): sidor som hann skrivas fotograferas och döms ändå; utan en enda sida faller
    # ateljén; vid fel sparas koden som hann skrivas innan städningen tar bort sidorna
    sidor_hr = k / 'provhr' / 'sajt' / 'src' / 'pages'


    def tidsgrans_(prompt, verktyg, ut, **kw):
        prompter.append(prompt)
        (sidor_hr / 'atelje-1').mkdir(parents=True, exist_ok=True); (sidor_hr / 'atelje-1' / 'index.astro').write_text('<p>1</p>')
        raise subprocess.TimeoutExpired('claude', 3600)


    fotograferat_ = []
    a.session = tidsgrans_
    a.fotografera = lambda slug, rot: fotograferat_.append(slug) or []
    utfall = iter([1]); prompter.clear()
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'klar' and fotograferat_ == ['provhr'] and 'TimeoutExpired' in st.get('divergera_avbruten', '') \
        and st['divergera'].get('riktningar_som_fanns') == [1], st


    def foll_(prompt, verktyg, ut, **kw):
        (sidor_hr / 'atelje-2').mkdir(parents=True, exist_ok=True); (sidor_hr / 'atelje-2' / 'index.astro').write_text('<p>2</p>')
        raise RuntimeError('sessionen föll')


    def bygget_foll_(slug, rot):
        raise RuntimeError('bygget föll efter divergensen')


    a.session = foll_
    a.fotografera = bygget_foll_
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    # bygget föll också sedan den ofullständiga riktningen 2 flyttats undan: dess kod står i ofullstandig-2/, riktning 1:s i 1/kod
    assert st['steg'] == 'fel' and 'bygget föll' in st['fel'] and any(x.endswith('/1/kod') for x in st.get('sparad_kod', [])) \
        and (rot2 / 'ofullstandig-2' / 'kod' / 'index.astro').read_text() == '<p>2</p>' and st.get('ofullstandiga_sparade') == ['ofullstandig-2'], st
    shutil.rmtree(sidor_hr / 'atelje-1', ignore_errors=True); shutil.rmtree(sidor_hr / 'atelje-2', ignore_errors=True)
    a.session = lambda prompt, verktyg, ut, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired('claude', 3600))
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'fel' and 'TimeoutExpired' in st['fel'] and 'sparad_kod' not in st, 'utan en enda sida faller ateljén'
    assert a.FRIST == 1200 + 800 * a.ANTAL or os.environ.get('NWP_ATELJE_FRIST'), 'gränsen växer med antalet riktningar'
    # bygget föll efter en avbruten divergens: den ofullständiga riktningen flyttas undan och resten fotograferas
    (sidor_hr / 'atelje-1').mkdir(parents=True, exist_ok=True); (sidor_hr / 'atelje-1' / 'index.astro').write_text('<p>1</p>')
    (sidor_hr / 'atelje-1' / 'undersida').mkdir(exist_ok=True); (sidor_hr / 'atelje-1' / 'undersida' / 'index.astro').write_text('<p>u</p>')
    (sidor_hr / 'atelje-2').mkdir(parents=True, exist_ok=True); (sidor_hr / 'atelje-2' / 'index.astro').write_text('<p>trasig')
    forsok_ = []


    def bygger_utan_2(slug, rot):
        forsok_.append(sorted(p.name for p in sidor_hr.glob('atelje-*')))
        if (sidor_hr / 'atelje-2').exists():
            raise RuntimeError('bygget föll efter divergensen: trasig sida')
        return []


    a.fotografera = bygger_utan_2
    assert a.fotografera_det_som_bygger('provhr', rot2) == [2] and forsok_ == [['atelje-1', 'atelje-2'], ['atelje-1']], forsok_
    assert (rot2 / 'ofullstandig-2' / 'kod' / 'index.astro').read_text() == '<p>trasig' and not (sidor_hr / 'atelje-2').exists()
    shutil.rmtree(sidor_hr / 'atelje-1'); shutil.rmtree(rot2 / 'ofullstandig-2')
    for n, fn in gamla.items():
        setattr(a, n, fn)
    # bildjämförelsen mot vinnaren (jamfor.mjs + prova.vinnarjamforelse): förändring, inte kvalitet


    def png_hr(p, w, h, f):
        rader = b''.join(b'\x00' + bytes(c for x in range(w) for c in f(x, y)) for y in range(h))
        chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)  # noqa: E731
        p.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rader)) + chunk(b'IEND', b''))


    vd, hd, ud = tmp / 'atelje-v' / 'vinnare' / 'bilder', tmp / 'hem', tmp / 'ut-vinnare'
    vd.mkdir(parents=True); hd.mkdir()
    gra = lambda x, y: (200, 200, 200, 255)  # noqa: E731
    png_hr(vd / 'vy-390-ruta-01.png', 40, 20, gra); png_hr(hd / 'vy-390-ruta-01.png', 40, 20, lambda x, y: (200, 200, 200, 255) if x >= 10 else (20, 20, 20, 255))
    png_hr(vd / 'vy-390-hela.png', 40, 20, gra); png_hr(hd / 'vy-390-hela.png', 40, 30, gra)
    png_hr(vd / 'vy-1440-ruta-01.png', 40, 20, gra)
    png_hr(hd / 'vy-1440-hela.png', 40, 20, gra)
    import hashlib as hl_hr
    (tmp / 'atelje-v' / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'filer': {'bilder/' + p.name: hl_hr.sha256(p.read_bytes()).hexdigest() for p in vd.glob('*.png')}}))
    text_v = pv_hr.vinnarjamforelse(vd, hd, ud)
    jv = json.loads((ud / 'VINNARJAMFORELSE.json').read_text())
    assert jv['hashfel'] == [] and 'STÄMMER INTE' not in text_v, jv['hashfel']
    assert jv['par'][0]['andel'] == 0.25 and jv['par'][1]['hojdskillnad'] == 10 and jv['par'][1]['andel'] == 0, jv
    assert 'saknas: byggets bild' in jv['par'][2]['fel'] and 'saknas: vinnarens bild' in jv['par'][3]['fel'] and (ud / 'skillnad-vy-390-ruta-01.png').is_file(), jv
    assert '25.0 % olika' in text_v and 'höjd +10 px' in text_v and 'förändring, inte kvalitet' in text_v and (ud / 'VINNARJAMFORELSE.md').read_text().count('\n- ') == 4, text_v
    png_hr(hd / 'vy-1440-ruta-01.png', 50, 20, gra)
    png_hr(vd / 'vy-390-hela.png', 40, 20, lambda x, y: (0, 0, 0, 255))  # måttstocken utbytt efter ateljén
    text_v = pv_hr.vinnarjamforelse(vd, hd, ud)
    jv = json.loads((ud / 'VINNARJAMFORELSE.json').read_text())
    assert jv['hashfel'] == ['vy-390-hela.png stämmer inte med VINNARE.json'] and text_v.startswith('VINNARENS BILDER STÄMMER INTE') and 'bredd +10 px' in text_v, (jv['hashfel'], text_v)
    assert 'Måttstocken kan vara utbytt' in (ud / 'VINNARJAMFORELSE.md').read_text()
    # granskaren: vinnaren fryses in i omgången, står i uppdraget och ingår i metodhashen
    gu_hr = gr.UNDERLAG
    gr.UNDERLAG = tmp / 'underlag'
    rdirv = tmp / 'rdir-vinnare'
    rdirv.mkdir()
    assert gr.frysta_vinnare('provhr', rdirv) is None
    shutil_hr.rmtree(u / 'atelje' / 'vinnare', ignore_errors=True)
    (u / 'atelje' / 'vinnare' / 'bilder').mkdir(parents=True, exist_ok=True)
    (u / 'atelje' / 'vinnare' / 'bilder' / 'vy-390-ruta-01.png').write_bytes(b'x')
    h0 = gr.metod_sha('provhr')
    (u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 2, 'filer': {}}))
    assert gr.metod_sha('provhr') != h0, 'vinnaren ingår i metodhashen'
    try:
        gr.frysta_vinnare('provhr', rdirv); raise AssertionError('en bild som inte står i VINNARE.json stoppar granskningen')
    except RuntimeError as e:
        assert 'stämmer inte med VINNARE.json' in str(e), e
    (u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 2, 'filer': {'bilder/vy-390-ruta-01.png': hl_hr.sha256(b'x').hexdigest()}}))
    h1 = gr.metod_sha('provhr')
    vv = gr.frysta_vinnare('provhr', rdirv)
    (u / 'atelje' / 'vinnare' / 'bilder' / 'vy-390-ruta-01.png').write_bytes(b'y')
    assert gr.metod_sha('provhr') != h1, 'vinnarens bildbytes ingår i metodhashen'
    try:
        gr.frysta_vinnare('provhr', tmp / 'rdir-vinnare-2'); raise AssertionError('en utbytt vinnarbild stoppar granskningen (granskningen av r53, punkt 5)')
    except RuntimeError as e:
        assert 'ändrad efter ateljén' in str(e), e
    (u / 'atelje' / 'vinnare' / 'bilder' / 'vy-390-ruta-01.png').write_bytes(b'x')
    assert vv[0]['riktning'] == 2 and [p.name for p in vv[1]] == ['vy-390-ruta-01.png'] and (rdirv / 'vinnare' / 'vy-390-ruta-01.png').is_file(), vv
    (rdirv / 'VINNARJAMFORELSE.md').write_text('x')
    pt = gr.uppdrag_text('provhr', 'http://x', ['/'], tmp / 'ak', [], [], [], None, rdirv, vinnare=vv)
    assert 'Ateljéns vinnare: riktning 2' in pt and 'blockerande fynd' in pt and 'vinnare/vy-390-ruta-01.png' in pt and 'VINNARJAMFORELSE.md' in pt, pt
    assert 'Ateljéns vinnare' not in gr.uppdrag_text('provhr', 'http://x', ['/'], tmp / 'ak', [], [], [], None, rdirv)
    (rdirv / 'vinnarjamforelse').mkdir(); (rdirv / 'vinnarjamforelse' / 'skillnad-vy-390-ruta-01.png').write_bytes(b'd')
    assert 'vinnarjamforelse/skillnad-vy-390-ruta-01.png' in gr.uppdrag_text('provhr', 'http://x', ['/'], tmp / 'ak', [], [], [], None, rdirv, vinnare=vv), 'skillnadsbilderna står i uppdraget'
    gr.UNDERLAG = gu_hr
    # stoppvakten släpper ett bygge vars ateljé förkastade alla riktningar; korslut ger slutkod 6 (granskningen av r53, punkt 1)
    import importlib.util as ilu_hr
    spec_sv = ilu_hr.spec_from_file_location('stoppvakt_hr', str(ROOT / '.claude' / 'hooks' / 'stoppvakt.py'))
    sv_hr = ilu_hr.module_from_spec(spec_sv); spec_sv.loader.exec_module(sv_hr)
    rot_sv = tmp / 'rot-sv'; (rot_sv / 'underlag' / 'sv' / 'atelje').mkdir(parents=True)
    (rot_sv / 'underlag' / 'sv' / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'forkastad', 'skal': 'panelen förkastade alla riktningar i 2 omgångar'}))
    (rot_sv / 'underlag' / 'sv' / 'atelje' / 'VAL.json').write_text(json.dumps({'val': None, 'forkastade': True, 'panel': {'a': {}, 'b': {}, 'c': {}}}))
    sandlada_hr = os.environ.pop('NWP_SANDLADA', None)
    try:
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') == 'panelen förkastade alla riktningar i 2 omgångar'
        os.environ['NWP_SANDLADA'] = 'pa'
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') is None, 'sandlådat körs ingen ateljé: ett sådant läge är inte ateljéns'
        del os.environ['NWP_SANDLADA']
        (rot_sv / 'underlag' / 'sv' / 'atelje' / 'VAL.json').write_text(json.dumps({'val': 2, 'forkastade': False, 'panel': {'a': {}, 'b': {}}}))
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') is None, 'ett val är ingen förkastning'
    finally:
        if sandlada_hr is not None:
            os.environ['NWP_SANDLADA'] = sandlada_hr
    import korslut as ks_hr
    k_sv = tmp / 'kunder-sv' / 'sv'; (k_sv / 'prov').mkdir(parents=True)
    (k_sv / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'ateljen_forkastad': True, 'slapp': True, 'skal': 'x'}))
    (tmp / 'fore-sv').write_text(''); (tmp / 'efter-sv').write_text('')
    ut_ks = io.StringIO()
    with contextlib.redirect_stdout(ut_ks):
        rc_ks = ks_hr.main(['korslut', str(k_sv), '0', str(tmp / 'fore-sv'), str(tmp / 'efter-sv')])
    assert rc_ks == 6 and 'Slutkod 6' in ut_ks.getvalue(), ut_ks.getvalue()
    a.session = attrapp  # F23:s attrapp tillbaka till F34
    print('F23b designprovet ok')


f23b()

# ---------------------------------------------------------------- F25/F26: spanaren
import spana as sp  # noqa: E402
sp.SPANING = tmp / 'spaning'
kand = lambda i, poang: {'id': 'k%02d' % i, 'nyckel': 'n%02d' % i, 'url': 'https://x.se/%d' % i, 'titel': 'astro lighthouse %d' % i, 'sammanfattning': '', 'kalla': 'prov', 'kalla_typ': 'rss', 'kallor': ['prov'], 'status': 'ny', 'hittad': sp.nu(), 'publicerad': '2026-10-01', 'popularitet': poang}  # noqa: E731
sp.rss = lambda kalla, h: [kand(i, 1000 - i) for i in range(1, 9)]
kanda = {'n%02d' % i: {'dom': 'ta in', 'datum': '2026-09-01'} for i in range(1, 6)}


class H:
    anrop = 0


senast, lista = sp.spana([{'typ': 'rss', 'namn': 'prov', 'url': 'u', 'vikt': 1.0, 'id': 'p'}], H(), max_per_kalla=5, kanda=kanda)
assert {x['id'] for x in lista if x['status'] == 'ny'} == {'k06', 'k07', 'k08'} and senast['redan_kanda'] == 5, (senast, [x['id'] for x in lista])
sp.satt('k06', 'avfardad', avfardad='prov')
assert (sp.SPANING / '.las').exists() and next(x for x in sp.las_json(sp.SPANING / 'KANDIDATER.json') if x['id'] == 'k06')['status'] == 'avfardad'
print('F25/F26 spanaren ok')

# ---------------------------------------------------------------- F29: LAN-stängningen är idempotent under samtidighet


class FalskServer:
    stangda = 0

    def __exit__(self, *a):
        FalskServer.stangda += 1


dash.VISNING_LAN.clear(); dash.VISNING_LAN['x'] = (FalskServer(), 0); dash.VISNING_LAN['y'] = (FalskServer(), 0)
fel = []
tradar = [threading.Thread(target=lambda: fel.append(None) if dash.stang_lan(bara_gamla=True) is None else None) for _ in range(4)]
for t_ in tradar:
    t_.start()
for t_ in tradar:
    t_.join()
assert FalskServer.stangda == 2 and not dash.VISNING_LAN and not fel, (FalskServer.stangda, dash.VISNING_LAN)
assert dash.stang_lan() == 0
print('F29 LAN-stängningen ok')

# ---------------------------------------------------------------- omgång tre (Codex R3): omslag, kedjor, cwd, merge, ++, sentinel, slutkod, proxy, slugvakt, metod, identitet, unsafe-eval, bokstavliga * och $
REPO_CWD = object()


def vakt3(cmd, cwd=REPO_CWD, **env):
    data = {'tool_name': 'Bash', 'tool_input': {'command': cmd}}
    if cwd is REPO_CWD:
        data['cwd'] = str(repo)  # hookens cwd är sessionens; proven står i reporoten om inget annat sägs
    elif cwd:
        data['cwd'] = cwd
    p = subprocess.run([PY, '-B', str(hook / 'commitvakt.py')], input=json.dumps(data), capture_output=True, text=True,
                       env={**os.environ, 'NWP_COMMIT_TILLATET': 'backlog/', **env})
    return p.returncode, p.stderr.strip()


g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
for cmd, vantat in [('command git commit -am audit', 2), ('command git push origin main', 0), ('env NWP_X=1 git push origin main', 0), ('nice -n 5 git push origin main', 0),
                    ('sh -c "git push origin main"', 2), ('bash -c \'git commit -m x\'', 2), ('echo backlog/a.md | xargs git add', 2), ('eval "git push origin main"', 2),
                    ('git add backlog/b.md && git commit -m x', 2), ('git add backlog/b.md && git push origin main', 2), ('git add backlog/b.md && echo ok', 2),
                    ('cd backlog && git push origin main', 2), ('git stash', 2), ('git merge gren', 2), ('git pull', 2), ('git rm backlog/a.md', 2), ('git status && git log -1', 0)]:
    rc, err = vakt3(cmd); assert rc == vantat, (cmd, rc, err)
rc, err = vakt3('git push origin main', cwd='/tmp'); assert rc == 2 and 'arbetskatalog' in err, err
rc, err = vakt3('git push origin main', cwd=str(repo / 'backlog')); assert rc == 2 and 'reporoten' in err, 'bara exakt reporoten (omgång fem, F3): ' + err
rc, err = vakt3('git push origin main', cwd=str(repo)); assert rc == 0, err
# push gäller refs/heads/main, inte HEAD
g('checkout', '-q', '-b', 'annan'); (repo / 'CLAUDE.md').write_text('annan\n'); g('commit', '-q', '-am', 'på annan')
rc, err = vakt3('git push origin main'); assert rc == 0, 'HEAD på en annan gren med ändrad CLAUDE.md ska inte stoppa push av en ren main: ' + err
g('checkout', '-q', 'main'); (repo / 'CLAUDE.md').write_text('main\n'); g('commit', '-q', '-am', 'på main'); g('checkout', '-q', 'annan')
rc, err = vakt3('git push origin main'); assert rc == 2 and 'CLAUDE.md' in err, 'main med CLAUDE.md ska stoppas fast HEAD är på en annan gren: ' + err
g('checkout', '-q', 'main'); g('reset', '-q', '--hard', 'origin/main'); g('branch', '-q', '-D', 'annan')
# F27: en hemlighet som tillkommer i själva merge-commiten (konfliktlösning) och en fil utanför det tillåtna som köas i den
(repo / 'backlog' / 'm.md').write_text('bas\n'); g('add', 'backlog/m.md'); g('commit', '-q', '-m', 'bas'); g('push', '-q', 'origin', 'main')
g('checkout', '-q', '-b', 'gren'); (repo / 'backlog' / 'm.md').write_text('gren\n'); g('commit', '-q', '-am', 'gren')
g('checkout', '-q', 'main'); (repo / 'backlog' / 'm.md').write_text('main\n'); g('commit', '-q', '-am', 'main')
m = g('merge', '--no-commit', 'gren'); assert m.returncode != 0, 'konflikt väntades'
(repo / 'backlog' / 'm.md').write_text('löst\nsk-ant-api03-abcdefghijklmnopqrstuvwxyz\n'); g('add', 'backlog/m.md')
(repo / 'CLAUDE.md').write_text('smugglad\n'); g('add', 'CLAUDE.md'); g('commit', '-q', '-m', 'merge')
assert 'sk-ant' not in g('log', '-p', '--format=', 'origin/main..main').stdout, 'utan -m syns inte mergens innehåll'
rc, err = vakt3('git push origin main'); assert rc == 2 and ('CLAUDE.md' in err or 'hemlighet' in err) and 'sk-ant-api03' not in err, err
g('reset', '-q', '--hard', 'origin/main'); g('branch', '-q', '-D', 'gren')
# F27: en tillagd rad som börjar med ++ (diffprefixet blir +++)
(repo / 'backlog' / 'pp.md').write_text('++ RESEND_API_NYCKEL=re_abcdefghijklmnopqrstuvwxyz0123\n'); g('add', 'backlog/pp.md')
rc, err = vakt3('git commit -m x'); assert rc == 2 and 'hemlighet' in err and 're_abcdef' not in err, err
g('reset', '-q', 'backlog/pp.md'); (repo / 'backlog' / 'pp.md').unlink()
# git add prövar filen som köas
(repo / 'backlog' / 'ny.md').write_text('AKIAABCDEFGHIJKLMNOP\n')
rc, err = vakt3('git add backlog/ny.md'); assert rc == 2 and 'hemlighet' in err and 'AKIAABCDEF' not in err, err
(repo / 'backlog' / 'ny.md').unlink()
print('R3 F3/F27 commitvakten ok')

# F4: ersättningssökvägen finns inte längre; en symlänkad .utanfor-dist och en katalogs index.html prövas också
dist4 = tmp / 'dist4'; dist4.mkdir(); (dist4 / 'index.html').write_text('<p>hej</p>')
os.symlink(hemlig, dist4 / '.utanfor-dist'); os.symlink(hemlig, dist4 / 'lank.txt')
(dist4 / 'mapp').mkdir(); os.symlink(hemlig, dist4 / 'mapp' / 'index.html'); os.symlink(tmp, dist4 / 'ut')
with prova.Server(dist4) as srv:
    def status4(vag):
        try:
            with urllib.request.urlopen(srv.url + vag, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
    for vag in ('/lank.txt', '/mapp/', '/mapp/index.html', '/ut/hemlig.txt', '/.utanfor-dist'):
        kod, kropp = status4(vag); assert kod == 404 and b'hemligt' not in kropp, (vag, kod, kropp[:60])
    assert status4('/')[0] == 200
print('R3 F4 symlänk ok')

# F11: slutkod 0 bara när provet, stoppvakten och granskningen gäller just det bygge som ligger i dist/ nu, med dagens metod
kk2 = tmp / 'kund-slut2'; (kk2 / 'prov').mkdir(parents=True); (kk2 / 'granskning').mkdir(); (kk2 / 'sajt' / 'dist').mkdir(parents=True)
(kk2 / 'sajt' / 'dist' / 'index.html').write_text('<p>v2</p>'); (kk2 / 'RAPPORT.md').write_text('# r')
h2 = prova.dist_hash(kk2 / 'sajt' / 'dist')
metod_r3 = json.loads(subprocess.run([PY, '-B', '-c', 'import sys, json; sys.path.insert(0, %r); import granska; print(json.dumps(granska.aktuell_metod(%r)))' % (str(ROOT / 'kontroller'), kk2.name)],
                                     capture_output=True, text=True, cwd=str(ROOT)).stdout)
fore2 = tmp / 'fore2.txt'; fore2.write_text('aaa  kontroller/prova.py\n')


def slut2(rc='0'):
    p = subprocess.run([PY, '-B', str(korslut), str(kk2), rc, str(fore2), str(fore2)], capture_output=True, text=True)
    return p.returncode, p.stdout


(kk2 / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': h2, 'grindar': {'bygge': {'ok': True}}}))
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'dist_sha256': h2}))
(kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': 'gammal', **metod_r3}))
rc, ut = slut2(); assert rc == 1 and 'annat bygge' in ut, (rc, ut)  # äldre godkänd granskning av ett annat bygge
(kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h2, **dict(metod_r3, metod_sha='gammal')}))
rc, ut = slut2(); assert rc == 1 and 'annan metod' in ut, (rc, ut)
(kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h2, **metod_r3}))
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'släppt utan godkänd granskning: taket för granskningar i körningen är nått', 'forsok': 3, 'tak': 8, 'dist_sha256': h2}))
rc, ut = slut2(); assert rc == 1 and 'stoppvakten' in ut, (rc, ut)  # stoppvakten släppte vid taket: inte godkänt
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'dist_sha256': h2}))
rc, ut = slut2(); assert rc == 0, (rc, ut)
(kk2 / 'sajt' / 'dist' / 'index.html').write_text('<p>v3</p>'); rc, ut = slut2(); assert rc == 1 and 'dist/' in ut, (rc, ut)  # bygget ändrat efter provet
print('R3 F11 korslut ok')

# F5: ingen proxy, inte ens när miljön pekar ut en
srv5, bas5 = server(rot)
assert not any(getattr(h_, 'proxies', None) for h_ in hs.oppnare().handlers), 'ingen proxyhanterare med proxyer i öppnaren'
os.environ['http_proxy'] = 'http://127.0.0.1:1'; os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1'
hs.TILLAT_LOKALT = True; hs._adresser.clear()
s = hs.hamta(bas5 + '/public/b.html'); assert s['status'] == 200, s
os.environ.pop('http_proxy'); os.environ.pop('HTTP_PROXY')
# F24: bokstavliga * och $ i URI:n, och robots.txt som pekar om till en annan värd
r6 = hs.Robots(); r6.parse(['User-agent: *', 'Disallow: /file%2A.html', 'Disallow: /foo-%24'])
assert not r6.can_fetch('x', 'http://a/file*.html') and not r6.can_fetch('x', 'http://a/foo-$'), 'bokstavliga * och $ i URI:n ska matcha de kodade mönstren'
assert r6.can_fetch('x', 'http://a/file-x.html') and r6.can_fetch('x', 'http://a/foo-x')
rotB = tmp / 'sajtB'; rotB.mkdir(); (rotB / 'robots.txt').write_text('User-agent: *\nDisallow: /hos-b/\n')
srvB, basB = server(rotB)


class RobotsOmd(Tyst):
    def do_GET(self):
        if self.path == '/robots.txt':
            self.send_response(302); self.send_header('Location', 'http://localhost:%d/robots.txt' % srvB.server_port); self.send_header('Content-Length', '0'); self.end_headers(); return
        super().do_GET()


srvA, basA = server(rot, functools.partial(RobotsOmd, directory=str(rot)))
rpA, lage = hs.las_robots(basA + '/', egen='127.0.0.1')
assert lage == 'hittad' and not rpA.can_fetch('nortropic-webb-pro', basA + '/hos-b/x') and rpA.can_fetch('nortropic-webb-pro', basA + '/annat'), (lage, 'robots-omdirigering till annan värd ska följas')
srvA.shutdown(); srvB.shutdown(); srv5.shutdown()
print('R3 F5/F24 hämtaren ok')

# F1: slugvakten binder verktygen till NWP_SLUG
miljo = {**os.environ, 'NWP_SLUG': 'eget-bygge'}
r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'ta_bort.py'), 'annat-bygge', 'kunder/annat-bygge/x'], capture_output=True, text=True, env=miljo, cwd=str(ROOT))
assert r.returncode == 2 and 'slugvakten' in r.stderr, r.stderr
r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'ta_bort.py'), 'eget-bygge', 'kunder/eget-bygge/finns-inte'], capture_output=True, text=True, env=miljo, cwd=str(ROOT))
assert r.returncode == 0 and 'finns inte' in r.stdout, (r.stdout, r.stderr)
r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'hamta_sajt.py'), 'http://127.0.0.1:1/', '--ut', 'underlag/annat-bygge/kalla'], capture_output=True, text=True, env=miljo, cwd=str(ROOT))
assert r.returncode == 2 and 'slugvakten' in r.stderr, r.stderr
r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'prova.py'), 'annat-bygge'], capture_output=True, text=True, env=miljo, cwd=str(ROOT))
assert r.returncode == 2 and 'slugvakten' in r.stderr, r.stderr
r = subprocess.run(['node', str(ROOT / 'kontroller' / 'axe.mjs'), '--url=http://127.0.0.1:1', '--sidor=/', '--ut=kunder/annat-bygge/prov/axe'], capture_output=True, text=True, env=miljo, cwd=str(ROOT))
assert r.returncode == 2 and 'slugvakten' in r.stderr, r.stderr
r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'ta_bort.py'), 'annat-bygge', 'kunder/annat-bygge/finns-inte'], capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != 'NWP_SLUG'}, cwd=str(ROOT))
assert r.returncode == 0, 'utan NWP_SLUG gör vakten ingenting: ' + r.stderr
print('R3 F1 slugvakten ok')

# F18: en pågående omgång med en annan metod återanvänds inte; den avbryts och en ny startas
gdir18 = kund / 'granskning'
(kund / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist')}))
sov = subprocess.Popen(['sleep', '300'], start_new_session=True)
r18 = gdir18 / 'runda-09'; r18.mkdir()
(r18 / 'UPPDRAG.json').write_text(json.dumps({'slug': 'ett-abx', 'runda': 9, 'korning': 'prov', 'tid': gr.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'),
                                             'modell': 'opus[1m]', 'effort': 'high', 'frist': 60, 'granskare': gr.ANTAL, 'originalitet': 'skugga', 'metod_sha': 'gammal-metod'}))
(r18 / 'PAGAR').write_text(str(sov.pid))
os.environ.pop('PROV_FALL', None)
rc18 = gr.main(['ett-abx', '--vanta', '30'])
assert (r18 / 'FEL.txt').is_file() and 'metoden' in (r18 / 'FEL.txt').read_text(), 'den gamla omgången ska avbrytas'
assert sov.poll() is not None or sov.wait(timeout=5) is not None, 'den gamla processen ska vara dödad'
assert (gdir18 / 'runda-10' / 'UPPDRAG.json').is_file() and json.loads((gdir18 / 'runda-10' / 'UPPDRAG.json').read_text())['metod_sha'] == gr.metod_sha('ett-abx'), 'ny omgång med dagens metod'
assert rc18 in (0, 4, 5), rc18  # 4: den nya omgångens arbetare är en egen process mot repots riktiga kunder/ (inte provets tmp) och faller där; avbrottet och den nya omgången ovan är det som prövas
print('R3 F18 pågående omgång ok')

# F20: kundens nod känns igen på identitet; en annan organisation i grafen (memberOf) prövas inte
verk20 = dict(verk, webb={'doman': 'holmskonditori.se'})
graf20 = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'Bakery', '@id': 'https://holmskonditori.se/#org', 'name': 'Holms Konditori', 'memberOf': {'@id': '#branschorg'}},
    {'@type': 'Organization', '@id': '#branschorg', 'name': 'Sveriges Bagare & Konditorer'}]}
f = seo.granska_schema(graf20, verk20); assert not any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), 'branschorganisationen är inte kunden: %s' % f
f = seo.granska_schema({'@type': 'Organization', '@id': 'https://holmskonditori.se/#org', 'name': 'Fel namn'}, verk20)
assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), 'en organisation på egen domän är kunden: %s' % f
f = seo.granska_schema({'@type': 'Organization', 'name': 'Holms Konditori', 'telephone': '+46700000000'}, verk20)
assert any(t == 'schema telephone ≠ E.164 ur verksamheten' for t, _ in f), 'samma namn: kunden: %s' % f
# F22: script-src självt med unsafe-eval
k22 = sk.csp_skriptkallor("script-src 'self' 'unsafe-eval'; script-src-elem 'self'; script-src-attr 'none'")
assert "'unsafe-eval'" in k22['script-src'] and k22['script-src-elem'] == ["'self'"]
(d3 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta http-equiv="content-security-policy" content="script-src \'self\' \'unsafe-eval\'; script-src-elem \'self\'; script-src-attr \'none\'"><title>x</title></head><body><main><h1>x</h1></main></body></html>')
assert any(x['punkt'] == '8.2' and x['text'].startswith("CSP:ns script-src släpper") for x in sk.granska(d3)[0]), 'unsafe-eval i script-src ska ge fel (F22)'
print('R3 F20/F22 ok')

# ---------------------------------------------------------------- omgång fyra (Codex R4): &-avgränsare, fristående git-skrivning, sidogrenar, slugvaktens tmp och symlänkar, arbetaringången, full metod och körning, kundnod
g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
for cmd, vantat in [('git status & git commit -am audit', 2), ('git status & git push origin main', 2), ('command cd /tmp && git commit -m audit', 2),
                    ('git push origin main &', 2), ('git push origin main; echo klart', 2), ('echo start && git push origin main', 2),
                    ('git push origin main', 0), ('command git push origin main', 0), ('git status & git log -1', 0)]:
    rc, err = vakt3(cmd); assert rc == vantat, (cmd, rc, err)
# F27: sidogrenens egna commits räknas (tillägg och borttagning av en nyckel före merge, rent slutträd)
(repo / 'backlog' / 'side.md').write_text('bas\n'); g('add', 'backlog/side.md'); g('commit', '-q', '-m', 'bas'); g('push', '-q', 'origin', 'main')
g('checkout', '-q', '-b', 'sida'); (repo / 'backlog' / 'side.md').write_text('bas\nsk-ant-api03-abcdefghijklmnopqrstuvwxyz\n'); g('commit', '-q', '-am', 'nyckel in')
(repo / 'backlog' / 'side.md').write_text('bas\n'); g('commit', '-q', '-am', 'nyckel ut')
g('checkout', '-q', 'main'); g('merge', '-q', '--no-ff', '-m', 'merge sida', 'sida')
assert g('diff', '--name-only', 'origin/main..main').stdout.strip() == '', 'slutträdet ska vara rent'
assert 'sk-ant' not in g('log', '-p', '--format=', '--first-parent', 'origin/main..main').stdout, 'med --first-parent syns inte sidogrenen'
rc, err = vakt3('git push origin main'); assert rc == 2 and 'hemlighet' in err and 'sk-ant-api03' not in err, 'hemligheten på sidogrenen: ' + err
g('reset', '-q', '--hard', 'origin/main'); g('branch', '-q', '-D', 'sida')
g('checkout', '-q', '-b', 'sida2'); (repo / 'CLAUDE.md').write_text('sida\n'); g('commit', '-q', '-am', 'otillåten fil på sidogren'); (repo / 'CLAUDE.md').write_text('x\n'); g('commit', '-q', '-am', 'återställd')
g('checkout', '-q', 'main'); g('merge', '-q', '--no-ff', '-m', 'merge sida2', 'sida2')
rc, err = vakt3('git push origin main'); assert rc == 2 and 'CLAUDE.md' in err, 'den otillåtna filen på sidogrenen: ' + err
g('reset', '-q', '--hard', 'origin/main'); g('branch', '-q', '-D', 'sida2')
print('R4 F3/F27 commitvakten ok')

# F1: tmp-området är körningens eget; symlänkar följs i Node; arbetaringången är bunden. Allt i en temporär repokopia
# (omgång fem, F28: provet skapade och raderade kunder/eget-bygge i det riktiga repot).
import slugvakt as sv  # noqa: E402
kopia = tmp / 'repo-kopia'; (kopia / 'kontroller').mkdir(parents=True); (kopia / 'kunder' / 'eget-bygge').mkdir(parents=True); (kopia / 'underlag').mkdir()
shutil.copy(ROOT / 'kontroller' / 'slugvakt.mjs', kopia / 'kontroller' / 'slugvakt.mjs')
sv_rot_orig = sv.ROOT; sv.ROOT = kopia
assert sv.tillaten_vag('/tmp/nwp-bygge-eget-bygge/x.png', 'eget-bygge') and not sv.tillaten_vag('/tmp/nwp-granskning/annat-runda-01-1/x.png', 'eget-bygge') and not sv.tillaten_vag('/tmp/x', 'eget-bygge')
assert not sv.tillaten_vag('/tmp/nwp-granskning/annat-runda-01-1', 'granskning'), 'sluggen granskning ska inte nå granskarnas rot (omgång fem)'
(tmp / 'annat-bygge-mapp').mkdir(); os.symlink(tmp / 'annat-bygge-mapp', kopia / 'kunder' / 'eget-bygge' / 'lank')
assert not sv.tillaten_vag(kopia / 'kunder' / 'eget-bygge' / 'lank' / 'ut.png', 'eget-bygge'), 'symlänk ut ur eget område (Python)'
assert not sv.tillaten_vag(kopia / 'kunder' / 'eget-bygge', 'eget-bygge'), 'en utkatalog med en planterad symlänk ut ska vägras (Python)'
(kopia / 'kunder' / 'eget-bygge' / 'lank').unlink(); assert sv.tillaten_vag(kopia / 'kunder' / 'eget-bygge', 'eget-bygge')
sv.ROOT = sv_rot_orig
node_vakta = lambda vag: subprocess.run(['node', '--input-type=module', '-e', "import { vakta } from %r; vakta(process.argv[1]); console.log('ok')" % str(kopia / 'kontroller' / 'slugvakt.mjs'), '--', str(vag)], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'})  # noqa: E731
r = node_vakta(kopia / 'kunder' / 'eget-bygge' / 'ut'); assert r.returncode == 0 and 'ok' in r.stdout, r.stderr
os.symlink(tmp / 'annat-bygge-mapp', kopia / 'kunder' / 'eget-bygge' / 'lank')
r = node_vakta(kopia / 'kunder' / 'eget-bygge' / 'lank' / 'ut.png'); assert r.returncode == 2 and 'slugvakten' in r.stderr, 'symlänk ut (Node): ' + r.stdout + r.stderr
r = node_vakta(kopia / 'kunder' / 'eget-bygge'); assert r.returncode == 2 and 'symlänken' in r.stderr, 'planterad symlänk i utkatalogen (Node): ' + r.stdout + r.stderr
(kopia / 'kunder' / 'eget-bygge' / 'lank').unlink()
r = node_vakta('/tmp/nwp-granskning/annat-runda-01-1'); assert r.returncode == 2, 'hela tmp ska inte vara tillåtet i Node'
r = subprocess.run(['node', '--input-type=module', '-e', "import { vakta } from %r; vakta(process.argv[1]); console.log('ok')" % str(kopia / 'kontroller' / 'slugvakt.mjs'), '--', '/tmp/nwp-granskning/annat-runda-01-1'], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'granskning'})
assert r.returncode == 2, 'sluggen granskning ska inte nå granskarnas rot (Node)'
assert sv.tmp_katalog.__doc__ and (lambda d: d.startswith('/tmp/nwp-bygge-eget-bygge/') or d.startswith(tempfile.gettempdir()))((lambda: (os.environ.__setitem__('NWP_SLUG', 'eget-bygge'), sv.tmp_katalog('prov-'))[1])())
os.environ.pop('NWP_SLUG', None)
r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'granska.py'), '--arbetare', str(kund / 'granskning' / 'runda-02')], capture_output=True, text=True,
                   env={**os.environ, 'NWP_SLUG': 'annat-bygge'}, cwd=str(ROOT))
assert r.returncode == 2 and 'slugvakten' in r.stderr, 'arbetaringången ska bindas till körningens slug: ' + r.stdout + r.stderr
print('R4 F1 slugvakten ok')

# F11: full metod (modell, effort, originalitetsläge) och stoppbesked bundet till körning och bygge
h3 = prova.dist_hash(kk2 / 'sajt' / 'dist')
(kk2 / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': h3, 'grindar': {'bygge': {'ok': True}}}))
metod3 = json.loads(subprocess.run([PY, '-B', '-c', 'import sys, json; sys.path.insert(0, %r); import granska; print(json.dumps(granska.aktuell_metod(%r)))' % (str(ROOT / 'kontroller'), kk2.name)],
                                   capture_output=True, text=True, cwd=str(ROOT)).stdout)


def slut3(korning='k1', **g_over):
    gjson = {'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h3, **metod3, **g_over}
    (kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps(gjson))
    p = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), korning], capture_output=True, text=True)
    return p.returncode, p.stdout


(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h3}))
assert slut3()[0] == 0, slut3()
for over in ({'modell': 'gammal'}, {'effort': 'low'}, {'originalitet': 'avgor'}):
    rc, ut = slut3(**over); assert rc == 1 and 'annan metod' in ut, (over, rc, ut)
rc, ut = slut3(korning='k2'); assert rc == 1 and 'annan körning' in ut, (rc, ut)
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': 'annan'}))
rc, ut = slut3(); assert rc == 1 and 'annat bygge' in ut, (rc, ut)
# Codex R38 F11: med omgångar härleds domen ur giltiga omgångar (inte rotfilen), bunden till det slutliga byggets dist
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h3}))
import granska as gr38  # noqa: E402
gdir38 = kk2 / 'granskning'
def runda38_(n, dist, godkand, status='klar', korning='k1'):
    r_ = gdir38 / ('runda-%02d' % n); r_.mkdir(exist_ok=True)
    (r_ / 'GRANSKNING.json').write_text(json.dumps({'godkand': godkand, 'runda': n, 'kriterier': {'designkvalitet': {'betyg': 7 if godkand else 5}}, 'dist_sha256': dist, 'korning': korning, 'tid': gr38.nu(), **metod3}))
    (r_ / 'UTFALL.json').write_text(json.dumps({'status': status, 'tid': gr38.nu(), 'skal': ''}))
    return r_
(gdir38 / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h3, **metod3}))  # inaktuell rotfil: ska inte styra
runda38_(1, h3, True); runda38_(2, 'annan-dist', False); runda38_(3, h3, True, status='avbruten')
p38 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p38.returncode == 0 and 'GODKÄND (omgång 1' in p38.stdout and '= slutliga bygget' in p38.stdout, (p38.returncode, p38.stdout[-500:])
(kk2 / 'sajt' / 'dist' / 'index.html').write_text('<p>v4</p>'); h4 = prova.dist_hash(kk2 / 'sajt' / 'dist')
(kk2 / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': h4, 'grindar': {'bygge': {'ok': True}}}))
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'släppt utan godkänd granskning: taket för granskningar i körningen är nått', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h4}))
p38 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p38.returncode == 1 and 'inte granskat' in p38.stdout and 'Senaste dom oavsett bygge och metod: underkänd (omgång 2' in p38.stdout and '≠ slutliga bygget' in p38.stdout and 'GODKÄND' not in p38.stdout.split('Rapport:')[0], ('det slutliga bygget är ogranskat: senaste giltiga visas separat som annat bygge, inte den avbrutna godkända', p38.returncode, p38.stdout[-600:])
shutil.rmtree(gdir38); gdir38.mkdir(); (kk2 / 'sajt' / 'dist' / 'index.html').write_text('<p>v3</p>')
(kk2 / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': h3, 'grindar': {'bygge': {'ok': True}}}))
# Codex R39: sluturvalet med hela identiteten (körning, dist, aktuell metod); senaste dom visas separat; läsfel nekar godkännande
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h3}))
def runda39_(n, dist, godkand, metod, status='klar'):
    r_ = gdir38 / ('runda-%02d' % n); r_.mkdir(exist_ok=True)
    (r_ / 'GRANSKNING.json').write_text(json.dumps({'godkand': godkand, 'runda': n, 'kriterier': {'designkvalitet': {'betyg': 7 if godkand else 5}}, 'dist_sha256': dist, 'korning': 'k1', 'tid': gr38.nu(), **metod}))
    (r_ / 'UTFALL.json').write_text(json.dumps({'status': status, 'tid': gr38.nu(), 'skal': ''}))
    return r_
runda39_(1, h3, True, metod3); runda39_(2, h3, False, dict(metod3, modell='gammal'))  # M1 godkänd, M2 underkänd, aktuell metod = M1
p39 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p39.returncode == 0 and 'GODKÄND (omgång 1' in p39.stdout and 'aktuell metod' in p39.stdout and 'Senaste dom oavsett bygge och metod: underkänd (omgång 2' in p39.stdout, (p39.returncode, p39.stdout[-600:])
(gdir38 / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h3, **metod3}))  # gammal godkänd rotfil
r39c = runda39_(3, h3, True, metod3); (r39c / 'GRANSKNING.json').write_text('{trasig')  # felaktigt formad dom i en klar omgång
p39 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p39.returncode == 1 and 'kunde inte läsas eller valideras' in p39.stdout and 'GODKÄND' not in p39.stdout.split('Rapport:')[0], ('en omgång märkt klar med en dom som inte kan verifieras nekar (Codex R40), den tidigare godkända återupplivas inte', p39.returncode, p39.stdout[-400:])
shutil.rmtree(gdir38 / 'runda-03'); shutil.rmtree(gdir38 / 'runda-01'); p39 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p39.returncode == 1 and 'ingen giltig omgång' in p39.stdout and 'GODKÄND' not in p39.stdout.split('Rapport:')[0], ('bara underkänd: rotfilen används inte', p39.returncode, p39.stdout[-400:])
r39c = runda39_(3, h3, True, metod3)
(r39c / 'FEL.txt').write_text('x'); (r39c / 'UTFALL.json').unlink(); os.chmod(r39c / 'FEL.txt', 0o000)
try:
    p39 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
finally:
    os.chmod(r39c / 'FEL.txt', 0o644)
assert p39.returncode == 1 and 'kunde inte läsas' in p39.stdout, ('ett läsfel i en omgång nekar godkännande, rotfilen är ingen reserv', p39.returncode, p39.stdout[-400:])
# Codex R40: en senare omgång märkt klar vars dom inte kan läsas återupplivar ingen tidigare godkänd; ett uttryckligt avbrott gör det;
# en oläsbar eller ogiltig tillståndsfil nekar också
runda39_(1, h3, True, metod3); r40b = runda39_(2, h3, False, metod3)
os.chmod(r40b / 'GRANSKNING.json', 0o000)
try:
    p40 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
finally:
    os.chmod(r40b / 'GRANSKNING.json', 0o644)
assert p40.returncode == 1 and 'kunde inte läsas eller valideras' in p40.stdout and 'GODKÄND' not in p40.stdout.split('Rapport:')[0], ('oläsbar senare dom återupplivar inget', p40.returncode, p40.stdout[-500:])
(r40b / 'UTFALL.json').write_text(json.dumps({'status': 'avbruten', 'tid': gr38.nu(), 'skal': 'drivaren'}))
p40 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p40.returncode == 0 and 'GODKÄND (omgång 1' in p40.stdout, ('ett uttryckligt avbrott lämnar den tidigare godkända domen i kraft', p40.returncode, p40.stdout[-400:])
(r40b / 'UTFALL.json').write_text('{trasig')
p40 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p40.returncode == 1 and 'kunde inte läsas eller valideras' in p40.stdout, ('ogiltig tillståndsfil nekar', p40.returncode, p40.stdout[-400:])
shutil.rmtree(gdir38); gdir38.mkdir()
print('R4 F11 korslut ok')

# F20: en ensam LocalBusiness med fel uppgifter prövas; värdnamn jämförs parsat
f = seo.granska_schema({'@type': 'Bakery', '@id': 'https://mall-exempel.se/#org', 'url': 'https://mall-exempel.se/', 'name': 'Mallbageriet', 'telephone': '+46700000000'}, verk20)
assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f) and any(t == 'schema telephone ≠ E.164 ur verksamheten' for t, _ in f), 'kvarlämnat mallinnehåll ska ge fynd: %s' % f
f = seo.granska_schema({'@type': 'Organization', 'url': 'https://katalog.example/sok?site=holmskonditori.se', 'name': 'Katalogen', 'telephone': '+46700000000'}, verk20)
assert f == [], 'kundens domän i en frågesträng gör inte en extern organisation till kunden: %s' % f
f = seo.granska_schema({'@type': 'Organization', 'url': 'https://www.holmskonditori.se/', 'name': 'Fel namn'}, verk20)
assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), 'www.-värden är kundens: %s' % f
print('R4 F20 ok')

# ---------------------------------------------------------------- omgång fem (Codex R5): binärt innehåll, kataloger till git add, exakt reporot, tmp-namnkonflikt, IRI-typer, upptagna_val
g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
nyckelbytes = b'RESEND_API_NYCKEL=re_abcdefghijklmnopqrstuvwxyz0123\n'
# binär fil (NUL) med nyckel: nekas vid add, vid commit (index) och vid push (historik)
(repo / 'backlog' / 'bin.md').write_bytes(b'\x00' + nyckelbytes)
rc, err = vakt3('git add backlog/bin.md', cwd=str(repo)); assert rc == 2 and 'binär' in err and 're_abcdef' not in err, 'binär fil vid add: ' + err
g('add', 'backlog/bin.md')
rc, err = vakt3('git commit -m x', cwd=str(repo)); assert rc == 2 and ('binär' in err or 'hemlighet' in err) and 're_abcdef' not in err, 'binär fil i index: ' + err
g('commit', '-q', '-m', 'binär smugglad')
assert 'Binary files' in g('diff', 'origin/main..main').stdout, 'git ser filen som binär'
rc, err = vakt3('git push origin main', cwd=str(repo)); assert rc == 2 and ('binär' in err or 'hemlighet' in err) and 're_abcdef' not in err, 'binär fil i historiken: ' + err
g('reset', '-q', '--hard', 'origin/main')
# katalog som argument till git add: filerna i den prövas
(repo / 'backlog' / 'ny').mkdir(); (repo / 'backlog' / 'ny' / 'post.md').write_bytes(nyckelbytes)
rc, err = vakt3('git add backlog/', cwd=str(repo)); assert rc == 2 and 'hemlighet' in err and 'backlog/ny/post.md' in err, 'katalog till add: ' + err
rc, err = vakt3('git add backlog', cwd=str(repo)); assert rc == 2, err
shutil.rmtree(repo / 'backlog' / 'ny')
rc, err = vakt3('git add backlog/', cwd=str(repo)); assert rc == 0, 'ren katalog går: ' + err
# exakt reporot: relativa sökvägar från en underkatalog avser andra filer
rc, err = vakt3('git commit -m audit -- backlog/SKILL.md', cwd=str(repo / '.claude')); assert rc == 2 and 'reporoten' in err, err
rc, err = vakt3('git commit -m audit', cwd=None); assert rc == 2 and 'cwd' in err, 'utan cwd nekas skrivning: ' + err
print('R5 F27/F3 commitvakten ok')

# F20: fullständiga IRI-typer
f = seo.granska_schema({'@type': 'https://schema.org/Bakery', 'name': 'Mallbageriet', 'telephone': '+46700000000'}, verk20)
assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f) and any(t == 'schema telephone ≠ E.164 ur verksamheten' for t, _ in f), 'IRI-typ ska prövas som Bakery: %s' % f
assert sk.typer({'@type': ['https://schema.org/Bakery', 'schema:LocalBusiness']}) == ['Bakery', 'LocalBusiness']
d5 = tmp / 'dist5'; d5.mkdir()
(d5 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>x</title><script type="application/ld+json">{"@type": "https://schema.org/Bakery", "name": "x"}</script></head><body><main><h1>x</h1></main></body></html>')
assert not any(x['punkt'] == '7.3' and 'saknar JSON-LD' in x['text'] for x in sk.granska(d5)[0]), 'standardkontrollen ska känna igen IRI-typen'
print('R5 F20 ok')

# F30: upptagna_val mäter ett tidigare bygge utan stilrapport också med NWP_SLUG satt (stil.mjs ärver sluggen)
import upptagna_val as uv  # noqa: E402
k30 = tmp / 'kunder30'; (k30 / 'gammalt' / 'sajt' / 'dist').mkdir(parents=True); (k30 / 'eget-bygge').mkdir()
(k30 / 'gammalt' / 'sajt' / 'dist' / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>G</title><style>body{margin:0;font:16px sans-serif}</style></head><body><main><h1>Gammalt bygge</h1><p>Text som är lång nog att räknas som brödtext här.</p></main></body></html>')
os.environ['NWP_SLUG'] = 'eget-bygge'
try:
    s30 = uv.stil_for(k30 / 'gammalt')
finally:
    os.environ.pop('NWP_SLUG', None)
assert s30 and 'sammanfattning' in s30, 'stil.mjs ska få skriva i körningens tmp-område: %r' % (s30,)
print('R5 F30 upptagna_val ok')

# ---------------------------------------------------------------- omgång sex (Codex R6): radindelning, expansioner, ofullständig genomgång, hängande länkar, symlänkad rot, fler skrivmål, administrativa verktyg, schema:-prefix
g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
for namn, fore in (('vertikal tabulator', b'text\x0b'), ('CR', b'text\r'), ('U+2028', 'text '.encode('utf-8'))):
    (repo / 'backlog' / 'rad.md').write_bytes(fore + b'RESEND_API_NYCKEL=re_abcdefghijklmnopqrstuvwxyz0123\n'); g('add', 'backlog/rad.md')
    assert 'Binary' not in g('diff', '--cached').stdout, namn + ': git ser filen som text'
    rc, err = vakt3('git commit -m x'); assert rc == 2 and 'hemlighet' in err and 're_abcdef' not in err, (namn, rc, err)
    g('commit', '-q', '-m', 'smugglad ' + namn)
    rc, err = vakt3('git push origin main'); assert rc == 2 and 'hemlighet' in err and 're_abcdef' not in err, (namn, 'push', rc, err)
    g('reset', '-q', '--hard', 'origin/main')
for cmd in ('git add backlog/*.md', 'git commit -m audit -- backlog/{../CLAUDE.md,../BESLUT.md}', 'git add backlog/[a]b.md', 'git add ~/x.md',
            'git add backlog/$X.md', 'git commit -m x -- :(glob)backlog/*.md', 'git add "$(echo backlog/a.md)"'):
    rc, err = vakt3(cmd); assert rc == 2, (cmd, rc, err)
rc, err = vakt3('git commit -m "Bygge x: 3 * 2 poster"'); assert rc == 0, 'tecken i meddelandet går: ' + err
print('R6 F27/F3 commitvakten ok')

# F1: ofullständig genomgång nekar; hängande länk följs i Node; symlänkad slugrot vägras; node_modules-länk prövas
import slugvakt as sv  # noqa: E402
kopia6 = tmp / 'repo6'; (kopia6 / 'kontroller').mkdir(parents=True); (kopia6 / 'kunder' / 'eget-bygge').mkdir(parents=True); (kopia6 / 'underlag').mkdir()
shutil.copy(ROOT / 'kontroller' / 'slugvakt.mjs', kopia6 / 'kontroller' / 'slugvakt.mjs')
sv_rot_orig = sv.ROOT; sv.ROOT = kopia6
node6 = lambda vag, slug='eget-bygge': subprocess.run(['node', '--input-type=module', '-e', "import { vakta } from %r; vakta(process.argv[1]); console.log('ok')" % str(kopia6 / 'kontroller' / 'slugvakt.mjs'), '--', str(vag)], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': slug})  # noqa: E731
stor = kopia6 / 'kunder' / 'eget-bygge' / 'stor'; stor.mkdir()
for i in range(sv.MAX_POSTER + 5):
    (stor / ('f%05d' % i)).touch()
os.symlink(tmp / 'annat-bygge-mapp', stor / 'zzz-lank')
assert not sv.tillaten_vag(stor, 'eget-bygge'), 'över taket ska nekas, inte godkännas (Python)'
r = node6(stor); assert r.returncode == 2 and 'för stor' in r.stderr, 'över taket ska nekas (Node): ' + r.stdout + r.stderr
shutil.rmtree(stor)
hang = kopia6 / 'kunder' / 'eget-bygge' / 'ikon.png'; os.symlink(tmp / 'annat-bygge-mapp' / 'finns-inte-an.png', hang)
assert not sv.tillaten_vag(hang, 'eget-bygge'), 'hängande länk ut (Python)'
r = node6(hang); assert r.returncode == 2 and 'ligger inte' in r.stderr, 'hängande länk ut (Node): ' + r.stdout + r.stderr
hang.unlink()
os.symlink(kopia6 / 'kunder' / 'eget-bygge', kopia6 / 'kunder' / 'lankad'); (kopia6 / 'kunder' / 'annat').mkdir()
os.rename(kopia6 / 'kunder' / 'eget-bygge', kopia6 / 'kunder' / 'eget-riktig'); os.symlink(kopia6 / 'kunder' / 'annat', kopia6 / 'kunder' / 'eget-bygge')
assert not sv.tillaten_vag(kopia6 / 'kunder' / 'eget-bygge' / 'ut', 'eget-bygge'), 'symlänkad slugrot ska vägras (Python)'
r = node6(kopia6 / 'kunder' / 'eget-bygge' / 'ut'); assert r.returncode == 2 and 'symlänk' in r.stderr, 'symlänkad slugrot (Node): ' + r.stdout + r.stderr
(kopia6 / 'kunder' / 'eget-bygge').unlink(); os.rename(kopia6 / 'kunder' / 'eget-riktig', kopia6 / 'kunder' / 'eget-bygge'); (kopia6 / 'kunder' / 'lankad').unlink()
nm = kopia6 / 'kunder' / 'eget-bygge' / 'node_modules'; os.symlink(tmp / 'annat-bygge-mapp', nm)
assert not sv.tillaten_vag(kopia6 / 'kunder' / 'eget-bygge', 'eget-bygge'), 'en node_modules som pekar ut ska prövas (Python)'
r = node6(kopia6 / 'kunder' / 'eget-bygge'); assert r.returncode == 2 and 'symlänken' in r.stderr, 'node_modules-länk (Node): ' + r.stdout + r.stderr
nm.unlink(); assert sv.tillaten_vag(kopia6 / 'kunder' / 'eget-bygge', 'eget-bygge')
sv.ROOT = sv_rot_orig
# fler skrivmål: sida_till_text och youtube prövar sina härledda filer; administrativa verktyg vägrar inne i ett bygge
omr = Path('/tmp/nwp-bygge-eget-bygge'); omr.mkdir(parents=True, exist_ok=True)
os.symlink(tmp / 'annat-bygge-mapp' / 'artikel.txt', omr / 'artikel.txt')
try:
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'sida_till_text.py'), 'http://127.0.0.1:1/', str(omr / 'artikel')], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'slugvakten' in r.stderr and 'artikel.txt' in r.stderr, 'artikel.txt som symlänk ut: ' + r.stderr
finally:
    (omr / 'artikel.txt').unlink()
os.symlink(tmp / 'annat-bygge-mapp', omr / 'video-bilder')
try:
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'youtube.py'), 'https://www.youtube.com/watch?v=x', '--ut', str(omr / 'video.md')], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'slugvakten' in r.stderr and 'video-bilder' in r.stderr, 'video-bilder som symlänk ut: ' + r.stdout + r.stderr
finally:
    (omr / 'video-bilder').unlink()
for verktyg, argv in (('prospekt.py', ['gallra', '--kampanj', 'annan-kampanj', '--manader', '0']), ('utskick.py', ['prov']), ('ab.py', ['lista']), ('spana.py', ['lista']), ('gruppera.py', [])):
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / verktyg), *argv], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'körs inte inne i ett bygge' in r.stderr, (verktyg, r.returncode, r.stderr[-200:])
print('R6 F1 slugvakten ok')

# F20: schema:Bakery med definierat prefix ger inget falskt vokabulärfynd, och schema:name är en känd egenskap
f = seo.granska_schema({'@context': {'schema': 'https://schema.org/'}, '@type': 'schema:Bakery', 'schema:name': 'Holms Konditori'}, verk20)
assert not any(t in ('JSON-LD okänd typ', 'JSON-LD okänd egenskap') for t, _ in f), 'kompakt IRI med definierat prefix är giltig: %s' % f
print('R6 F20 ok')

# ---------------------------------------------------------------- omgång sju (Codex R7): .. efter symlänk i Node, sida_till_text med ändelse, meddelandeundantaget, prefixade egenskaper
g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
for cmd, vantat in [('git commit -m $MSG', 2), ('git commit -m backlog{1,2}', 2), ('git commit -m x -F <(cat f)', 2), ('git commit -m x -F ~/f', 2),
                    ('git commit -m *', 2), ('git commit -m "x $HOME"', 2), ("git commit -m 'a * b'", 0), ('git commit -m "a * b {c}"', 0),
                    ('git commit --message="x * y"', 0), ('git commit -m "Bygge x: 3 * 2 poster"', 0)]:
    rc, err = vakt3(cmd); assert rc == vantat, (cmd, rc, err)
print('R7 F3 meddelandeundantaget ok')

# F1: .. efter en symlänk löses som filsystemet gör det (upp → .., axe.json → upp/../annat/axe.json leder till underlag/annat)
kopia7 = tmp / 'repo7'; (kopia7 / 'kontroller').mkdir(parents=True); (kopia7 / 'kunder').mkdir(); (kopia7 / 'underlag' / 'eget').mkdir(parents=True); (kopia7 / 'underlag' / 'annat').mkdir()
shutil.copy(ROOT / 'kontroller' / 'slugvakt.mjs', kopia7 / 'kontroller' / 'slugvakt.mjs')
ut7 = kopia7 / 'underlag' / 'eget' / 'ut'; ut7.mkdir()
os.symlink('..', ut7 / 'upp'); os.symlink('upp/../annat/axe.json', ut7 / 'axe.json')
assert os.path.realpath(ut7 / 'axe.json') == str((kopia7 / 'underlag' / 'annat' / 'axe.json').resolve()), 'filsystemets upplösning är underlag/annat'
node7 = lambda vag: subprocess.run(['node', '--input-type=module', '-e', "import { vakta } from %r; vakta(process.argv[1]); console.log('ok')" % str(kopia7 / 'kontroller' / 'slugvakt.mjs'), '--', str(vag)], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget'})  # noqa: E731
r = node7(ut7); assert r.returncode == 2 and 'symlänken' in r.stderr and 'axe.json' in r.stderr, '.. efter symlänk ska leda ut (Node): ' + r.stdout + r.stderr
r = node7(ut7 / 'axe.json'); assert r.returncode == 2 and 'ligger inte' in r.stderr, 'skrivmålet självt via upp/.. ska nekas (Node): ' + r.stdout + r.stderr
sv_rot_orig = sv.ROOT; sv.ROOT = kopia7
assert not sv.tillaten_vag(ut7, 'eget') and not sv.tillaten_vag(ut7 / 'axe.json', 'eget'), '.. efter symlänk (Python)'
sv.ROOT = sv_rot_orig
(ut7 / 'upp').unlink(); (ut7 / 'axe.json').unlink(); os.symlink('..', ut7 / 'upp')
os.symlink('upp/../eget/ut/annan.json', ut7 / 'ok.json')  # via .. tillbaka in i eget område, till en annan fil
r = node7(ut7); assert r.returncode == 0, 'en länk som via .. stannar i eget område går: ' + r.stdout + r.stderr
# sida_till_text: with_suffix ersätter en ändelse, så artikel.v1 skriver artikel.txt; den filen prövas nu
omr7 = Path('/tmp/nwp-bygge-eget-bygge'); omr7.mkdir(parents=True, exist_ok=True)
os.symlink(tmp / 'annat-bygge-mapp' / 'artikel.txt', omr7 / 'artikel.txt')
try:
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'sida_till_text.py'), 'http://127.0.0.1:1/', str(omr7 / 'artikel.v1')], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'slugvakten' in r.stderr and 'artikel.txt' in r.stderr, 'artikel.v1 skriver artikel.txt, som är en symlänk ut: ' + r.stdout + r.stderr
finally:
    (omr7 / 'artikel.txt').unlink()
print('R7 F1 slugvakten ok')

# F20: prefixade egenskaper prövas mot underlaget, också nästlade adressfält
f = seo.granska_schema({'@context': {'schema': 'https://schema.org/'}, '@type': 'schema:Bakery', 'schema:name': 'Fel namn', 'schema:telephone': '+46700000000',
                        'schema:address': {'@type': 'schema:PostalAddress', 'schema:postalCode': '111 11', 'schema:addressLocality': 'Luleå', 'schema:streetAddress': 'Storgatan 1'}}, verk20)
typer_f = [t_ for t_, _ in f]
assert 'schema name ≠ verksamhetens namn' in typer_f and 'schema telephone ≠ E.164 ur verksamheten' in typer_f and 'schema address ≠ verksamhetens adress' in typer_f, 'prefixade egenskaper ska prövas: %s' % f
assert not any(t_ in ('JSON-LD okänd typ', 'JSON-LD okänd egenskap') for t_ in typer_f), f
f = seo.granska_schema({'@type': 'https://schema.org/Bakery', 'https://schema.org/name': 'Holms Konditori', 'https://schema.org/telephone': '+46920123456',
                        'https://schema.org/address': {'@type': 'https://schema.org/PostalAddress', 'https://schema.org/streetAddress': 'Storgatan 1', 'https://schema.org/postalCode': '972 31', 'https://schema.org/addressLocality': 'Luleå'}}, verk20)
assert f == [], 'rätt uppgifter med fullständiga IRI:er ska vara rena: %s' % f
print('R7 F20 ok')

# ---------------------------------------------------------------- omgång åtta (Codex R8): hela skalordet och dess citering; kolliderande egenskapsnamn
g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
for cmd, vantat in [("git commit -m 'a'*", 2), ("git commit -m ''{message,extra}", 2), ("git commit -m*", 2), ("git commit -m ''{meddelande,--,CLAUDE.md}", 2),
                    ('git commit -mText', 2), ('git commit --message=""{a,b}', 2), ("git commit -m 'a' 'b'", 2), ('git commit -m "a"b', 2), ('git commit -m x -- back\\log/a.md', 2),
                    ("git commit -m 'a * b'", 0), ('git commit -m "a * b {c}"', 0), ('git commit --message="x * y"', 0), ("git commit --message='x'", 0), ('git commit -m enkelt', 0),
                    ("git commit -m 'x' -- 'backlog/a.md'", 0), ("git add 'backlog/a b.md'", 0), ("git add 'backlog/*'", 2)]:
    rc, err = vakt3(cmd); assert rc == vantat, (cmd, rc, err)
print('R8 F3 skalorden ok')

# F20: name och schema:name med olika värden i båda ordningarna ger namnfynd och ett konfliktfynd; nästlade adresser likaså
for forst, sedan in ((('name', 'Fel namn'), ('schema:name', 'Holms Konditori')), (('schema:name', 'Holms Konditori'), ('name', 'Fel namn'))):
    nod = {'@context': {'@vocab': 'https://schema.org/', 'schema': 'https://schema.org/'}, '@type': 'Bakery'}
    nod[forst[0]] = forst[1]; nod[sedan[0]] = sedan[1]
    f = seo.granska_schema(nod, verk20); typer_f = [t_ for t_, _ in f]
    assert 'schema name ≠ verksamhetens namn' in typer_f and 'JSON-LD motstridiga egenskaper' in typer_f, (forst, sedan, f)
ratt = {'@type': 'PostalAddress', 'streetAddress': 'Storgatan 1', 'postalCode': '972 31', 'addressLocality': 'Luleå'}
fel = {'@type': 'PostalAddress', 'streetAddress': 'Storgatan 1', 'postalCode': '111 11', 'addressLocality': 'Boden'}
for forst, sedan in ((('address', fel), ('schema:address', ratt)), (('schema:address', ratt), ('address', fel))):
    nod = {'@context': {'@vocab': 'https://schema.org/', 'schema': 'https://schema.org/'}, '@type': 'Bakery', 'name': 'Holms Konditori'}
    nod[forst[0]] = forst[1]; nod[sedan[0]] = sedan[1]
    f = seo.granska_schema(nod, verk20); typer_f = [t_ for t_, _ in f]
    assert typer_f.count('schema address ≠ verksamhetens adress') == 2 and 'JSON-LD motstridiga egenskaper' in typer_f, (forst[0], f)
f = seo.granska_schema({'@type': 'Bakery', 'name': 'Holms Konditori', 'schema:name': 'Holms Konditori', 'address': ratt}, verk20)
assert f == [], 'samma värde i två stavningar är ingen konflikt: %s' % f
print('R8 F20 ok')

# ---------------------------------------------------------------- omgång nio (Codex R9): -F som konsumerar -m; likvärdiga listor och skalärer i JSON-LD
g('remote', 'add', 'origin', str(bare)); g('fetch', '-q', 'origin'); g('reset', '-q', '--hard', 'origin/main'); g('checkout', '-q', 'main')
(repo / '-m').write_text('meddelande ur fil\n'); (repo / '--message').write_text('meddelande ur fil\n')
for cmd, vantat in [("git commit -F -m 'backlog/*'", 2), ("git commit -F --message 'backlog/*'", 2), ("git commit -F -m -- 'backlog/*'", 2),
                    ('git commit -F msg.txt', 0), ("git commit --file=msg.txt -- 'backlog/a.md'", 0), ("git commit -F 'm*.txt'", 2),
                    # omgång tio, F3: en citerad flagga är samma flagga när skalet tagit bort citaten
                    ("git commit '-F' -m 'backlog/*'", 2), ('git commit "--file" -m \'backlog/*\'', 2), ("git commit '-F' --message 'backlog/*'", 2),
                    ("git commit '-F' '-m' -- 'backlog/*'", 2), ("git commit '-F' 'm*.txt'", 2), ("git commit \"-F\" msg.txt", 0),
                    ("git commit '-m' 'meddelande med citat'", 0), ("git commit '--message' meddelande", 0)]:
    rc, err = vakt3(cmd); assert rc == vantat, (cmd, rc, err)
(repo / '-m').unlink(); (repo / '--message').unlink()
print('R9 F3 flaggvärden ok')

ratt = {'@type': 'PostalAddress', 'streetAddress': 'Storgatan 1', 'postalCode': '972 31', 'addressLocality': 'Luleå'}
fel = {'@type': 'PostalAddress', 'streetAddress': 'Storgatan 1', 'postalCode': '111 11', 'addressLocality': 'Boden'}
ctx = {'@vocab': 'https://schema.org/', 'schema': 'https://schema.org/'}
for forst, sedan in ((('name', ['Holms Konditori']), ('schema:name', 'Holms Konditori')), (('schema:name', 'Holms Konditori'), ('name', ['Holms Konditori']))):
    nod = {'@context': ctx, '@type': 'Bakery', 'address': ratt}; nod[forst[0]] = forst[1]; nod[sedan[0]] = sedan[1]
    f = seo.granska_schema(nod, verk20); assert f == [], 'skalär och enelementslista är samma värde: %s' % f
for forst, sedan in ((('address', [ratt]), ('schema:address', ratt)), (('schema:address', ratt), ('address', [ratt]))):
    nod = {'@context': ctx, '@type': 'Bakery', 'name': 'Holms Konditori'}; nod[forst[0]] = forst[1]; nod[sedan[0]] = sedan[1]
    f = seo.granska_schema(nod, verk20); assert f == [], 'adress som lista och skalär: %s' % f
f = seo.granska_schema({'@type': 'Bakery', 'name': 'Holms Konditori', 'address': {'@type': 'PostalAddress', 'streetAddress': ['Storgatan 1'], 'postalCode': ['972 31'], 'addressLocality': ['Luleå']}}, verk20)
assert f == [], 'enelementslistor i adressens underfält: %s' % f
f = seo.granska_schema({'@type': 'Bakery', 'name': 'Holms Konditori', 'address': {'@type': 'PostalAddress', 'streetAddress': ['Storgatan 1'], 'postalCode': ['111 11'], 'addressLocality': ['Luleå']}}, verk20)
assert any(t_ == 'schema address ≠ verksamhetens adress' for t_, _ in f), 'fel värde i en lista ska ge fynd: %s' % f
f = seo.granska_schema({'@context': ctx, '@type': 'Bakery', 'name': ['Holms Konditori', 'Holms'], 'schema:name': 'Holms Konditori', 'address': ratt}, verk20)
assert any(t_ == 'JSON-LD motstridiga egenskaper' for t_, _ in f) and any(t_ == 'schema name ≠ verksamhetens namn' for t_, _ in f), 'olika värdesamlingar är fortfarande en konflikt: %s' % f
f = seo.granska_schema({'@context': ctx, '@type': 'Bakery', 'name': 'Holms Konditori', 'address': ratt, 'knowsLanguage': {'@list': ['sv', 'en']}}, verk20)
assert not any(t_ == 'JSON-LD motstridiga egenskaper' for t_, _ in f), '@list är ett ordnat värde: %s' % f
# omgång tio, F20: @list får vara null, en skalär eller ett objekt; värdena bevaras i ordning och alias ger ingen konflikt
objekt = {'@type': 'Language', 'name': 'svenska'}
for lista, vantat in ((None, []), ('sv', ['sv']), (['sv'], ['sv']), (objekt, [objekt]), ([objekt], [objekt]), (['b', 'a'], ['b', 'a']),
                      ({'@value': 'sv'}, [{'@value': 'sv'}])):
    n = seo.normaliserad_nod({'@list': lista}); assert n == {'@list': vantat}, (lista, n)
    f = seo.granska_schema({'@context': ctx, '@type': 'Bakery', 'name': 'Holms Konditori', 'address': ratt, 'knowsLanguage': {'@list': lista}}, verk20)
    assert not any(t_ in ('JSON-LD motstridiga egenskaper', 'JSON-LD form') for t_, _ in f), ('@list med %r: %s' % (lista, f))
n = seo.normaliserad_nod({'@context': ctx, '@type': 'Bakery', 'knowsLanguage': {'@list': objekt}})
assert n['knowsLanguage'] == {'@list': [objekt]}, 'ett nodobjekt i @list är ett element, inte sina nycklar: %s' % n
k = []
n = seo.normaliserad_nod({'@context': ctx, 'knowsLanguage': {'@list': 'sv'}, 'schema:knowsLanguage': {'@list': ['sv']}}, k)
assert k == [] and n['knowsLanguage'] == {'@list': ['sv']}, ('alias med @list "sv" och ["sv"] är samma värde', k, n)
f = seo.granska_schema({'@context': ctx, '@type': 'Bakery', 'name': 'Holms Konditori', 'address': ratt, 'knowsLanguage': {'@list': 'sv'}, 'schema:knowsLanguage': {'@list': ['sv']}}, verk20)
assert not any(t_ == 'JSON-LD motstridiga egenskaper' for t_, _ in f), 'alias med likvärdiga @list ger ingen konflikt: %s' % f
print('R9 F20 ok')


# ---------------------------------------------------------------- omgång elva (Codex R11): F1, F6, F27, F13, F36, F33, F9, F31, F32, F18, F8, F34, F35, F25, F24
import struct  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402

# F1: ta_bort, ny_sajt och hamta_bokadirekt använder den förankrade sökvägskontrollen på sina faktiska mål
import ta_bort as tb  # noqa: E402
import slugvakt as sv11  # noqa: E402
import ny_sajt as ns  # noqa: E402
import hamta_bokadirekt as hb  # noqa: E402
rot11 = tmp / 'rot11'; (rot11 / 'kunder' / 'annan').mkdir(parents=True); (rot11 / 'kunder' / 'annan' / 'offer.txt').write_text('x')
(rot11 / 'underlag' / 'annan').mkdir(parents=True); (rot11 / 'kunder' / 'eget').symlink_to(rot11 / 'kunder' / 'annan'); (rot11 / 'underlag' / 'eget').symlink_to(rot11 / 'underlag' / 'annan')
sv_root, tb.ROOT, sv11.ROOT = sv11.ROOT, rot11, rot11
rc = tb.main(['eget', 'kunder/eget/offer.txt']); assert rc == 2 and (rot11 / 'kunder' / 'annan' / 'offer.txt').is_file(), 'en symlänkad kundrot får inte göra den andra kunden betrodd (F1)'
ns.ROOT, hb.ROOT = rot11, rot11
os.environ['NWP_SLUG'] = 'eget'
try:
    for namn, fn in (('ny_sajt', lambda: ns.main(['eget'])), ('hamta_bokadirekt', lambda: hb.main())):
        sys.argv = ['x', 'eget', 'https://www.bokadirekt.se/places/x-1']
        try:
            fn(); raise AssertionError('%s ska vägra när kundkatalogen är en symlänk till en annan kund (F1)' % namn)
        except SystemExit as e:
            assert e.code == 2, (namn, e.code)
finally:
    os.environ.pop('NWP_SLUG', None)
assert not list((rot11 / 'kunder' / 'annan').glob('sajt*')) and not (rot11 / 'underlag' / 'annan' / 'kalla').exists(), 'inget får ha skrivits hos den andra kunden'
for led11 in ('kunder', 'underlag'):  # rötterna förankrade igen: riktiga kataloger
    (rot11 / led11 / 'eget').unlink(); (rot11 / led11 / 'eget').mkdir()
(rot11 / 'kunder' / 'eget' / 'ut').symlink_to(rot11 / 'kunder' / 'annan')
rc = tb.main(['eget', 'kunder/eget/ut/offer.txt']); assert rc == 2 and (rot11 / 'kunder' / 'annan' / 'offer.txt').is_file(), 'en symlänk ut ur den egna katalogen (F1)'
(rot11 / 'kunder' / 'eget' / 'egen.txt').write_text('x'); rc = tb.main(['eget', 'kunder/eget/egen.txt']); assert rc == 0 and not (rot11 / 'kunder' / 'eget' / 'egen.txt').exists()
sv11.ROOT = sv_root
print('R11 F1 förankrade mål ok')

# F6: samtidiga spärrar tappas inte; speglingens kvitto skrivs in efteråt
u.SPARR = tmp / 'sparr11' / 'SPARR.json'; (tmp / 'sparr11').mkdir(); u.SPARR.write_text('[]')
tr6 = [threading.Thread(target=lambda i=i: u.sparr_lagg('t%02d@x.se' % i, 'prov', spegla=False)) for i in range(16)]
for t_ in tr6:
    t_.start()
for t_ in tr6:
    t_.join()
assert len(u.las_sparr()) == 16 and (tmp / 'sparr11' / '.sparr.las').exists(), 'samtidiga avregistreringar får inte tappas (F6): %d' % len(u.las_sparr())
u.las_hemligheter = lambda *a, **k: {'RESEND_API_NYCKEL': 'x'}; u.resend_anrop = lambda *a, **k: (201, {'id': 'r1'})
ny6 = u.sparr_lagg('s@x.se', 'prov'); assert ny6.get('resend_id') == 'r1' and next(p_ for p_ in u.las_sparr() if p_['varde'] == 's@x.se').get('resend_id') == 'r1', 'kvittot ska skrivas in (F6)'
print('R11 F6 spärrlistan ok')

# F27: hemligheter i commit-meddelanden (commit och utgående commits vid push)
g11 = lambda *a: subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True)  # noqa: E731
g11('checkout', '-q', 'main'); g11('reset', '-q', '--hard', 'origin/main'); (repo / 'backlog').mkdir(exist_ok=True); (repo / 'backlog' / 'a.md').write_text('a\n')
rc, err = vakt3("git commit -m 'nyckel sk-ant-api03-abcdefghijklmnopqrstuvwxyz' -- backlog/a.md"); assert rc == 2 and 'commit-meddelandet' in err and 'sk-ant-api03' not in err, err
rc, err = vakt3("git commit --message='sk-ant-api03-abcdefghijklmnopqrstuvwxyz' -- backlog/a.md"); assert rc == 2 and 'commit-meddelandet' in err, err
(repo / 'msg-hemlig.txt').write_text('rad\nre_abcdefghijklmnopqrstuvwxyz\n')
rc, err = vakt3('git commit -F msg-hemlig.txt -- backlog/a.md'); assert rc == 2 and 'commit-meddelandet' in err and 'rad 2' in err and 're_abcdef' not in err, err
rc, err = vakt3("git commit -m 'rent meddelande' -- backlog/a.md"); assert rc == 0, err
(repo / 'msg-hemlig.txt').unlink()
g11('commit', '-q', '--allow-empty', '-m', 'push-prov sk-ant-api03-abcdefghijklmnopqrstuvwxyz')
rc, err = vakt3('git push origin main'); assert rc == 2 and 'meddelande' in err and 'sk-ant-api03' not in err, 'hemlighet i ett utgående commit-meddelande (F27): ' + err
g11('reset', '-q', '--hard', 'origin/main')
print('R11 F27 commit-meddelanden ok')

# F13: LAN-visningen startas bara med POST under ursprungskontrollen; GET läser läget
dsrv13 = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H); threading.Thread(target=dsrv13.serve_forever, daemon=True).start()
dport = dsrv13.server_port; dash.VARD['tillatna'] = {'127.0.0.1:%d' % dport, 'localhost:%d' % dport}  # dashboardens provserver stängdes efter sitt block
anrop13, _visa_lan = [], dash.visa_lan
dash.visa_lan = lambda s: anrop13.append(s) or 'http://192.0.2.1:1'
kod, _ = begar(dport, 'GET', '/api/visa/dold-aby'); assert kod == 200 and not anrop13, 'GET får inte starta LAN-visningen (F13)'
kod, _ = begar(dport, 'POST', '/api/visa/dold-aby', huvuden={'Origin': 'http://evil.test:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{}'); assert kod == 403 and not anrop13, kod
kod, _ = begar(dport, 'POST', '/api/visa/dold-aby', huvuden={'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{}'); assert kod == 200 and anrop13 == ['dold-aby'], (kod, anrop13)
dash.visa_lan = _visa_lan; dsrv13.shutdown()
print('R11 F13 LAN via POST ok')

# F36: läsande inspektion släpper inga skrivande anrop från sidans skript
rot36 = tmp / 'sajt36'; rot36.mkdir()
(rot36 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1><script>fetch("/skriv", {method: "POST", body: "x"}).catch(() => {});</script></body></html>')
srv36, bas36 = server(rot36)
r36 = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'inspektera.mjs'), '--adress', bas36 + '/', '--ut', str(tmp / 'ut36'), '--vyer', '390', '--tillstand', 'inga'],
                     capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=240)
ins36 = json.loads((tmp / 'ut36' / 'INSPEKTION.json').read_text())
bl36 = ins36['vyer']['390']['natverk']['blockerade']
assert any(x.get('metod') == 'POST' and 'skrivande' in (x.get('skal') or '') for x in bl36), (r36.stdout[-300:], r36.stderr[-300:], bl36)
srv36.shutdown()
print('R11 F36 läsande inspektion ok')

# F33: GPS i en AVIF-fil, oläsbar metadata och en ren fil
import bilddatum as bd  # noqa: E402


def box33(typ, inneh):
    return struct.pack('>I', 8 + len(inneh)) + typ + inneh


def fullbox33(typ, inneh, v=0):
    return box33(typ, bytes([v, 0, 0, 0]) + inneh)


datum33 = b'2021:08:24 07:25:00\x00'
ifd0_33 = struct.pack('<H', 2) + struct.pack('<HHII', 0x8769, 4, 1, 38) + struct.pack('<HHII', 0x8825, 4, 1, 56) + struct.pack('<I', 0)
exif_33 = struct.pack('<H', 1) + struct.pack('<HHII', 0x9003, 2, len(datum33), 62) + struct.pack('<I', 0)
tiff33 = b'II*\x00' + struct.pack('<I', 8) + ifd0_33 + exif_33 + struct.pack('<H', 0) + struct.pack('<I', 0) + datum33


def avif33(metod=0, med_exif=True):
    ftyp = box33(b'ftyp', b'avif' + b'\x00\x00\x00\x00' + b'avifmif1')
    hdlr = fullbox33(b'hdlr', b'\x00' * 4 + b'pict' + b'\x00' * 13)
    infe = fullbox33(b'infe', struct.pack('>HH', 1, 0) + b'Exif' + b'\x00', v=2)
    iinf = fullbox33(b'iinf', struct.pack('>H', 1 if med_exif else 0) + (infe if med_exif else b''))

    def iloc(off):
        if metod == 0:
            return fullbox33(b'iloc', bytes([0x44, 0x00]) + struct.pack('>HHHH', 1, 1, 0, 1) + struct.pack('>II', off, 4 + len(tiff33)))
        return fullbox33(b'iloc', bytes([0x44, 0x00]) + struct.pack('>HHHHH', 1, 1, metod, 0, 1) + struct.pack('>II', off, 4 + len(tiff33)), v=1)
    meta = fullbox33(b'meta', hdlr + iinf + iloc(0))
    meta = fullbox33(b'meta', hdlr + iinf + iloc(len(ftyp) + len(meta) + 8))
    return ftyp + meta + box33(b'mdat', b'\x00\x00\x00\x00' + tiff33)


assert bd.avif_metadata(avif33())[0] == 'tiff' and bd.exif(bd.tiff_block(avif33())).get('gps'), 'EXIF ur AVIF (F33)'
d33 = tmp / 'dist33'; shutil.copytree(d3, d33)
(d33 / 'jobb.avif').write_bytes(avif33())
assert any(x['punkt'] == '4.2' and x['sida'] == '/jobb.avif' and 'GPS' in x['text'] for x in sk.granska(d33)[0]), 'GPS i en AVIF ska ge fel 4.2 (F33)'
(d33 / 'jobb.avif').write_bytes(avif33(metod=1))
assert any(x['punkt'] == '4.2' and x['sida'] == '/jobb.avif' and 'verifieras' in x['text'] for x in sk.granska(d33)[0]), 'oläsbar metadata är inte grön (F33)'
(d33 / 'jobb.avif').write_bytes(avif33(med_exif=False))
assert not any(x['punkt'] == '4.2' and x['sida'] == '/jobb.avif' for x in sk.granska(d33)[0]), 'en AVIF utan metadata är ren (F33)'
print('R11 F33 AVIF ok')

# F9/F31: spillgrinden kräver 320-mätningen; utan-js är grönt bara vid PASS; skickaknappens formaction fälls
ins_ok = {'vyer': {vy: {'spill': {'spill': False}, 'tillstand': {'reflow_320': {'spill': False}}} for vy in ('390', '768', '1440')}}
assert prova.spillfynd(ins_ok, '/') == [], prova.spillfynd(ins_ok, '/')
ins_320 = json.loads(json.dumps(ins_ok)); ins_320['vyer']['390']['tillstand']['reflow_320'] = {'spill': True, 'scrollWidth': 400, 'clientWidth': 320}
assert any('@320' in x for x in prova.spillfynd(ins_320, '/')), 'spill i 320-vyn ska fälla (F9)'
ins_utan = json.loads(json.dumps(ins_ok)); del ins_utan['vyer']['390']['tillstand']['reflow_320']
assert any('inte mätt' in x and '320' in x for x in prova.spillfynd(ins_utan, '/')), 'en saknad 320-mätning är inte grön (F9)'
assert prova.utan_js_grind({'status': 'PASS', 'fynd': []})[0] and not prova.utan_js_grind({'status': 'EJ_MATT', 'fynd': []})[0] and not prova.utan_js_grind({'status': 'FAIL', 'fynd': [{'vad': 'x'}]})[0], 'bara PASS är grönt (F31)'
(d33 / 'kontakt').mkdir(exist_ok=True)
(d33 / 'kontakt' / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Kontakt</title></head><body><main><h1>Kontakt</h1>'
                                           '<form action="/api/forfragan" method="post"><input name="namn" type="text" autocomplete="name" aria-describedby="a">'
                                           '<input name="telefon" type="tel" autocomplete="tel" pattern="[0-9 ]+" aria-describedby="b"><textarea name="meddelande" aria-describedby="c"></textarea>'
                                           '<button type="submit" formaction="/finns-inte">Skicka</button></form></main></body></html>')
assert any(x['punkt'] == '6.1' and 'överstyr' in x['text'] for x in sk.granska(d33)[0]), 'formaction på skickaknappen ska ge fel 6.1 (F31)'
print('R11 F9/F31 grindar ok')

# F32: interna länkar i alla skrivformer löses mot sidan, <base> och den egna domänen
d32 = tmp / 'dist32'; (d32 / 'finns').mkdir(parents=True); (d32 / 'finns' / 'index.html').write_text('<html lang="sv"><head><title>Finns</title></head><body><h1>f</h1></body></html>')
raw32 = ('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Start</title><meta name="description" content="x"></head><body><h1>s</h1>'
         '<a href="/finns/">a</a><a href="finns/">b</a><a href="saknas/">c</a><a href="./saknas2/">d</a><a href="https://exempel.se/saknas3/">e</a>'
         '<a href="https://www.exempel.se/finns/">e2</a><a href="https://annan.se/x/">f</a><a href="mailto:a@b.se">g</a></body></html>')
(d32 / 'index.html').write_text(raw32)
f32 = seo.granska_sida(d32, d32 / 'index.html', raw32, 'lansering', verk20, 'exempel.se')
brutna32 = sorted(f_['text'] for f_ in f32['fynd'] if f_['typ'] == 'intern länk löser inte')
assert brutna32 == ['./saknas2/', 'https://exempel.se/saknas3/', 'saknas/'], brutna32
raw32b = raw32.replace('<head>', '<head><base href="/finns/">').replace('<a href="finns/">b</a>', '')
f32b = seo.granska_sida(d32, d32 / 'index.html', raw32b, 'lansering', verk20, 'exempel.se')
assert 'saknas/' in [f_['text'] for f_ in f32b['fynd'] if f_['typ'] == 'intern länk löser inte'], 'relativa länkar löses mot <base> (F32)'
print('R11 F32 länkar ok')

# F18: referensbilderna ingår i metodhashen och fryses i omgången
m18a = gr.metod_sha('ett-abx'); rdir18b = tmp / 'underlag' / 'ett-abx' / 'referenser' / 'r1'; rdir18b.mkdir(parents=True)
(rdir18b / 'vy-390-forsta.png').write_bytes(b'bild A'); m18b = gr.metod_sha('ett-abx'); assert m18b != m18a, 'referensbilderna ska ingå i metodhashen (F18)'
(rdir18b / 'vy-390-forsta.png').write_bytes(b'bild B'); assert gr.metod_sha('ett-abx') != m18b, 'en utbytt bild på samma sökväg ska ge ny hash (F18)'
fr18 = gr.frysta_referenser('ett-abx', tmp / 'runda18'); assert fr18 and fr18[0][0].read_bytes() == b'bild B' and str(fr18[0][0]).startswith(str(tmp / 'runda18')), fr18
print('R11 F18 referensbilder ok')

# F8: en misslyckad jämförelse blir aldrig 'lika'
kj = tmp / 'kunder' / 'jamf' / 'granskning'  # gr.KUNDER är tmp/kunder
for namn8, betyg8 in (('runda-01', 8), ('runda-02', 6)):
    (kj / namn8 / 'sajt' / 'hem').mkdir(parents=True); (kj / namn8 / 'sajt' / 'hem' / 'vy-390-forsta.png').write_bytes(b'x')
    (kj / namn8 / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'kriterier': {n_: {'betyg': betyg8} for n_ in gr.KRITERIER}}))
_run8 = gr.subprocess.run
gr.subprocess.run = lambda *a, **kw: types.SimpleNamespace(returncode=1, stdout=b'', stderr=b'')
try:
    rc8 = gr.jamfor('jamf')
finally:
    gr.subprocess.run = _run8
j8 = json.loads((kj / 'JAMFORELSE-OMGANGAR.json').read_text())
assert rc8 == 3 and j8.get('fel') and j8.get('vinnare') is None, 'en misslyckad jämförelse får inte bli lika (F8): %s %s' % (rc8, j8)
print('R11 F8 jämförelsen ok')

# F34: panelen ser bara det här försökets fotograferade riktningar
(arot / '4').mkdir(); (arot / '4' / 'vy-390-ruta-01.png').write_bytes(b'x'); (arot / '4' / 'vy-1440-ruta-01.png').write_bytes(b'x')  # kvar från ett tidigare försök
svar_per_domare.update(formgivning=full, funktion=full, kunden=full)
v34 = a.panel('prov', arot); assert set(v34['poang']) == {1, 2, 3}, 'bara det här försökets riktningar (F34): %s' % v34['poang']
(arot / '3' / 'vy-390-ruta-01.png').unlink()
try:
    a.panel('prov', arot); raise AssertionError('en listad riktning utan bilder ska stoppa (F34)')
except RuntimeError as e:
    assert 'saknar startsidans rutor' in str(e), e
(arot / '3' / 'vy-390-ruta-01.png').write_bytes(b'x'); (arot / '3' / 'vy-1440-ruta-01.png').unlink()
try:
    a.panel('prov', arot); raise AssertionError('en riktning utan 1440-bild ska stoppa (omgång tolv, F34)')
except RuntimeError as e:
    assert 'båda bredderna' in str(e), e
(arot / 'FOTOGRAFERADE.json').unlink()
try:
    a.panel('prov', arot); raise AssertionError('utan manifest ska panelen stoppa (F34)')
except RuntimeError as e:
    assert 'FOTOGRAFERADE' in str(e), e
print('R11 F34 ateljén ok')

# F35: gallring efter senaste kontakt; bara kund undantas permanent
import prospekt as pr  # noqa: E402
import prospektfiler as pf11  # noqa: E402
pf11.PROSPEKT = tmp / 'prospekt11'; pr.ROOT = tmp
gammal35, ny35 = '2024-01-01T00:00:00Z', pf11.nu()
pf11.skriv_register('prov-k', lambda p_: [{'slug': 'gammal-skickad', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35},
                                         {'slug': 'kund-gammal', 'status': 'kund', 'skapad': gammal35, 'uppdaterad': gammal35},
                                         {'slug': 'ny-skickad', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35, 'skickat_tid': ny35},
                                         {'slug': 'gammal-demo', 'status': 'demo', 'skapad': gammal35, 'uppdaterad': gammal35},
                                         {'slug': 'gammal-nej', 'status': 'nej', 'skapad': gammal35, 'uppdaterad': gammal35}])
pr.gallra(types.SimpleNamespace(manader=12, kampanj='prov-k', torr=False))
kvar35 = {p_['slug']: p_ for p_ in pf11.las_register('prov-k')}
assert set(kvar35) == {'kund-gammal', 'ny-skickad', 'gammal-nej'} and kvar35['gammal-nej'].get('gallrad'), 'gallring efter senaste kontakt (F35): %s' % sorted(kvar35)
print('R11 F35 gallringen ok')

# F25: en kandidat ägaren avfärdat under spaningen kommer inte tillbaka som ny
sp._skriv_resultat([kand(6, 999)], [], [], {}, 0, time.time(), False, H())
k06 = [x for x in sp.las_json(sp.SPANING / 'KANDIDATER.json') if x['id'] == 'k06']
assert len(k06) == 1 and k06[0]['status'] == 'avfardad', 'en avfärdad kandidat får inte bli två poster (F25): %s' % k06
print('R11 F25 spaningen ok')

# F24: robots-policyn följer med genom omdirigeringar, också vid ursprungsbyte, i sida_till_text och ladda_bilder
hs.TILLAT_LOKALT = True; hs._adresser.clear()
rot24 = tmp / 'sajt24'; rot24.mkdir(); (rot24 / 'robots.txt').write_text('User-agent: *\nDisallow: /dold/\n'); (rot24 / 'index.html').write_text('<html><body><h1>a</h1></body></html>')
(rot24 / 'dold').mkdir(); (rot24 / 'dold' / 'sida.html').write_text('<html><body>d</body></html>')
rotB24 = tmp / 'sajtB24'; (rotB24 / 'hos-b').mkdir(parents=True); (rotB24 / 'robots.txt').write_text('User-agent: *\nDisallow: /hos-b/\n'); (rotB24 / 'hos-b' / 'x.html').write_text('<html><body>b</body></html>')
srvB24, basB24 = server(rotB24)


class Omd24(Tyst):
    def do_GET(self):
        mal = {'/till-dold': '/dold/sida.html', '/till-b': basB24 + '/hos-b/x.html'}.get(self.path.split('?')[0])
        if mal:
            self.send_response(302); self.send_header('Location', mal); self.send_header('Content-Length', '0'); self.end_headers(); return
        super().do_GET()


srv24, bas24 = server(rot24, functools.partial(Omd24, directory=str(rot24)))
import sida_till_text as stt  # noqa: E402
for vag24 in ('/till-dold', '/till-b'):
    try:
        stt.sida_till_text(bas24 + vag24, tmp / 'ut24' / ('sida' + vag24.replace('/', '-'))); raise AssertionError('omdirigering till ett robots-förbjudet mål ska stoppa (F24): ' + vag24)
    except SystemExit as e:
        assert '302' in str(e), (vag24, e)
assert not list((tmp / 'ut24').glob('*.html')) if (tmp / 'ut24').exists() else True, 'inget får ha hämtats'
rader24 = hs.ladda_bilder([{'url': bas24 + '/till-dold', 'typ': 'foto', 'alt': ''}, {'url': bas24 + '/till-b', 'typ': 'foto', 'alt': ''}], tmp / 'bilder24', paus=0) or []
assert len(rader24) == 2 and all('302' in str(r_['status']) and not r_['fil'] for r_ in rader24), rader24
srv24.shutdown(); srvB24.shutdown()
print('R11 F24 robots genom hoppen ok')


# ---------------------------------------------------------------- omgång tolv (Codex R12): F37, F1, F33, F35, F27, F31, F36, F34, F18, F32
# F37: en egen fråga med en kärnfrågas id publicerar inte fritext; bara giltiga fasta svar publiceras
(dash.KUNDER / 'normal' / 'FRAGOR.json').write_text(json.dumps([{'id': 'sakerhet', 'fraga': 'Egen fritext under kärn-id', 'typ': 'fritext'}, {'id': 'egen_val', 'fraga': 'Egen', 'typ': 'val', 'alternativ': ['A', 'B']}]))
assert [f_['id'] for f_ in dash.egna_fragor('normal')] == ['egen_val'], 'kärnfrågornas id är reserverade (F37)'
assert [f_['id'] for f_ in dash.bygge('normal')['fragor']['egna']] == ['egen_val']
r37 = dash.spara_dom('normal', {'svar': {'sakerhet': 'Hemlig fritext om Dan', 'specifik': 'sju', 'namn': 'Påhittat alternativ', 'battre': 'Mycket bättre',
                                         'dimensioner': {'Hållning': 'Bra', 'Påhittad rad': 'Bra'}, 'egen_val': 'A'}})
pub37, priv37 = (tmp / 'LARDOMAR.md').read_text(), (tmp / 'underlag' / 'LARDOMAR-original.md').read_text()
post37 = (tmp / 'backlog' / (r37['backlog'] + '.md')).read_text()
assert 'Hemlig fritext' not in pub37 and 'Hemlig fritext' not in post37 and 'Hemlig fritext' in priv37, 'fritext under ett kärn-id får aldrig publiceras (F37)'
assert 'Påhittat alternativ' not in pub37 and 'sju' not in pub37 and 'Påhittad rad' not in pub37 and 'Mycket bättre' in pub37, pub37
assert dash.publikt_varde({'typ': 'skala', 'steg': 5}, 3) == 3 and dash.publikt_varde({'typ': 'skala', 'steg': 5}, 9) is None and dash.publikt_varde({'typ': 'skala', 'steg': 5}, True) is None
(dash.KUNDER / 'normal' / 'DOM.json').unlink(); (dash.KUNDER / 'normal' / 'FRAGOR.json').unlink()
print('R12 F37 fasta svar ok')

# F1: en tillåten kataloglänk som i sin tur länkar ut passerar inte genomgången; ny_sajt kopierar inte till den andra kunden
rot12 = tmp / 'rot12'
for d_ in ('kunder/eget/sajt', 'kunder/annan', 'underlag/eget/x'):
    (rot12 / d_).mkdir(parents=True)
(rot12 / 'kunder' / 'eget' / 'sajt' / 'src').symlink_to(rot12 / 'underlag' / 'eget' / 'x')  # tillåten kataloglänk …
(rot12 / 'underlag' / 'eget' / 'x' / 'pages').symlink_to(rot12 / 'kunder' / 'annan')  # … som länkar vidare ut
sv_root12, sv11.ROOT = sv11.ROOT, rot12
assert sv11.symlank_ut(rot12 / 'kunder' / 'eget' / 'sajt', sv11.forankrad('eget'))[0] == 'ut', 'den indirekta länken ska upptäckas (F1)'
assert not sv11.tillaten_vag(rot12 / 'kunder' / 'eget' / 'sajt', 'eget')
(rot12 / 'underlag' / 'eget' / 'x' / 'pages').unlink(); (rot12 / 'underlag' / 'eget' / 'x' / 'pages').mkdir()
assert sv11.tillaten_vag(rot12 / 'kunder' / 'eget' / 'sajt', 'eget'), 'en kataloglänk inom rötterna utan vidare länk är ren'
(rot12 / 'underlag' / 'eget' / 'x' / 'pages').rmdir(); (rot12 / 'underlag' / 'eget' / 'x' / 'pages').symlink_to(rot12 / 'kunder' / 'annan')
(rot12 / 'underlag' / 'eget' / 'x' / 'cykel').symlink_to(rot12 / 'underlag' / 'eget')  # cykel: får inte låsa genomgången
assert sv11.symlank_ut(rot12 / 'kunder' / 'eget' / 'sajt', sv11.forankrad('eget'))[0] == 'ut'
ns.ROOT = rot12; os.environ['NWP_SLUG'] = 'eget'
try:
    ns.main(['eget']); raise AssertionError('ny_sajt ska vägra när sajtkatalogen länkar vidare till en annan kund (F1)')
except SystemExit as e:
    assert e.code == 2, e.code
finally:
    os.environ.pop('NWP_SLUG', None)
assert not any((rot12 / 'kunder' / 'annan').iterdir()), 'inget får ha kopierats till den andra kunden (F1)'
sv11.ROOT = sv_root12
print('R12 F1 indirekta kataloglänkar ok')

# F33: rent EXIF plus GPS-XMP i samma AVIF ger rött, oavsett objektordning


def avif_flera(objekt):
    """objekt: [(typ, nyttolast, content_type)] i given ordning."""
    ftyp = box33(b'ftyp', b'avif' + b'\x00\x00\x00\x00' + b'avifmif1')
    hdlr = fullbox33(b'hdlr', b'\x00' * 4 + b'pict' + b'\x00' * 13)
    infes = b''.join(fullbox33(b'infe', struct.pack('>HH', i + 1, 0) + typ + b'\x00' + (ct + b'\x00' if ct else b''), v=2) for i, (typ, _, ct) in enumerate(objekt))
    iinf = fullbox33(b'iinf', struct.pack('>H', len(objekt)) + infes)

    def iloc(bas):
        kropp, off = bytes([0x44, 0x00]) + struct.pack('>H', len(objekt)), bas
        for i, (_, last, _) in enumerate(objekt):
            kropp += struct.pack('>HHH', i + 1, 0, 1) + struct.pack('>II', off, len(last)); off += len(last)
        return fullbox33(b'iloc', kropp)
    meta = fullbox33(b'meta', hdlr + iinf + iloc(0)); meta = fullbox33(b'meta', hdlr + iinf + iloc(len(ftyp) + len(meta) + 8))
    return ftyp + meta + box33(b'mdat', b''.join(last for _, last, _ in objekt))


exif_rent = b'\x00\x00\x00\x00' + b'II*\x00' + struct.pack('<I', 8) + struct.pack('<H', 0) + struct.pack('<I', 0)
xmp_gps = b'<x:xmpmeta><rdf:Description exif:GPSLatitude="65,35.2N"/></x:xmpmeta>'
for ordning in ([(b'Exif', exif_rent, None), (b'mime', xmp_gps, b'application/rdf+xml')], [(b'mime', xmp_gps, b'application/rdf+xml'), (b'Exif', exif_rent, None)]):
    lage33, skal33 = bd.avif_metadata(avif_flera(ordning))
    assert lage33 == 'oklar' and 'GPS' in skal33, (lage33, skal33)
assert bd.avif_metadata(avif_flera([(b'Exif', exif_rent, None), (b'mime', b'<x:xmpmeta/>', b'application/rdf+xml')]))[0] == 'tiff', 'rent EXIF och XMP utan GPS är rent'
(d33 / 'jobb.avif').write_bytes(avif_flera([(b'Exif', exif_rent, None), (b'mime', xmp_gps, b'application/rdf+xml')]))
assert any(x['punkt'] == '4.2' and x['sida'] == '/jobb.avif' for x in sk.granska(d33)[0]), 'GPS i XMP bakom rent EXIF ska ge fel 4.2 (F33)'
print('R12 F33 XMP bakom EXIF ok')

# F35: underlaget tas bort oavsett kundkatalog; blir material kvar bokförs gallringen som ofullständig
pf11.skriv_register('prov-k', lambda p_: [{'slug': 'demo-med-bygge', 'status': 'demo', 'skapad': gammal35, 'uppdaterad': gammal35},
                                         {'slug': 'demo-utan-bygge', 'status': 'demo', 'skapad': gammal35, 'uppdaterad': gammal35}])
for d_ in ('underlag/demo-med-bygge', 'kunder/demo-med-bygge', 'underlag/demo-utan-bygge'):
    (tmp / d_).mkdir(parents=True, exist_ok=True); (tmp / d_ / 'x.txt').write_text('x')
pr.gallra(types.SimpleNamespace(manader=12, kampanj='prov-k', torr=False))
assert not (tmp / 'underlag' / 'demo-med-bygge').exists() and not (tmp / 'underlag' / 'demo-utan-bygge').exists() and (tmp / 'kunder' / 'demo-med-bygge').exists(), 'underlaget ska bort oavsett kundkatalog (F35)'
logg35 = [json.loads(x) for x in (pf11.kampanjkatalog('prov-k') / 'logg.jsonl').read_text().splitlines()]
assert any(x['handelse'] == 'gallring-ofullstandig' and x['slug'] == 'demo-med-bygge' and 'kunder/demo-med-bygge' in (x.get('kvar') or []) for x in logg35), logg35[-4:]
assert any(x['handelse'] == 'gallrad' and x['slug'] == 'demo-utan-bygge' for x in logg35), logg35[-4:]
print('R12 F35 gallringen ok')

# F27: den hopskrivna formen -Ffilnamn
g11('checkout', '-q', 'main'); g11('reset', '-q', '--hard', 'origin/main'); (repo / 'backlog').mkdir(exist_ok=True); (repo / 'backlog' / 'a.md').write_text('a\n')
(repo / 'msg-hemlig.txt').write_text('rad\nre_abcdefghijklmnopqrstuvwxyz\n')
rc, err = vakt3('git commit -Fmsg-hemlig.txt -- backlog/a.md'); assert rc == 2 and 'commit-meddelandet' in err and 're_abcdef' not in err, err
(repo / 'msg-hemlig.txt').unlink()
print('R12 F27 -Ffilnamn ok')

# F31: demomottagaren nekar ett ofullständigt inskick med tom honeypot; utan-js fyller aldrig honeypoten
import urllib.request as ur  # noqa: E402
import urllib.parse as up  # noqa: E402
d31 = tmp / 'dist31'; d31.mkdir(); (d31 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1></body></html>')
(d31 / 'tack').mkdir(); (d31 / 'tack' / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Tack</title></head><body><h1>Tack</h1></body></html>')
(d31 / 'kontakt').mkdir(); (d31 / 'kontakt' / 'index.html').write_text(
    '<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Kontakt</title><style>.falla{position:absolute;left:-9999px}</style></head><body><h1>Kontakt</h1>'
    '<form action="/api/forfragan" method="post"><input name="namn" type="text"><input name="telefon" type="tel" pattern="[0-9+\\-\\(\\) ]{6,40}"><textarea name="meddelande"></textarea>'
    '<p class="falla"><input name="webbplats" type="text" tabindex="-1" autocomplete="off"></p><button type="submit">Skicka</button></form></body></html>')
with prova.Server(d31) as srv31:
    def posta(falt):
        req = ur.Request(srv31.url + '/api/forfragan', data=up.urlencode(falt).encode(), method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            return ur.urlopen(ur.build_opener(ur.HTTPRedirectHandler) and ur.OpenerDirector() and ur.Request(srv31.url + '/'), timeout=5) and None
        except Exception:
            pass
    class UtanFoljning(ur.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opp = ur.build_opener(UtanFoljning)
    def posta(falt):  # noqa: F811
        req = ur.Request(srv31.url + '/api/forfragan', data=up.urlencode(falt).encode(), method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            return opp.open(req, timeout=5).headers.get('Location')
        except ur.HTTPError as e:
            return e.headers.get('Location')
    assert posta({'namn': 'A', 'telefon': '070-123 45 67', 'meddelande': '', 'webbplats': ''}).startswith('/kontakt/?saknas=1'), 'ett ofullständigt inskick med tom honeypot ska avvisas (F31)'
    assert posta({'namn': 'A', 'telefon': '070-123 45 67', 'meddelande': 'hej', 'webbplats': ''}) == '/tack/'
    # utan-js mot mottagaren: honeypoten lämnas tom, de riktiga fälten fylls, landning på tacksidan
    r31 = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'utan-js.mjs'), '--adress', srv31.url + '/', '--sidor', '/kontakt/', '--ut', str(tmp / 'ut31'),
                          '--formular-far-skickas', '--testmarkering', 'NWP-PROV'], capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=240)
    u31 = json.loads((tmp / 'ut31' / 'UTAN-JS.json').read_text())
    f31 = [f_ for s_ in u31['sidor'] for f_ in s_['formular']]
    assert u31['status'] == 'PASS' and f31 and f31[0]['skickat'] and f31[0]['tacksida'], (r31.stdout[-300:], r31.stderr[-300:], u31.get('fynd'), f31)
print('R12 F31 honeypot ok')

# F36: utforska skickar bara med flaggan, och sändningen läses ur nätutfallet


class Mottagare36(Tyst):
    poster = []

    def do_POST(self):
        n_ = int(self.headers.get('Content-Length') or 0); Mottagare36.poster.append(self.rfile.read(n_).decode('utf-8', 'replace'))
        self.send_response(303); self.send_header('Location', '/tack/'); self.send_header('Content-Length', '0'); self.end_headers()


rot36b = tmp / 'sajt36b'; rot36b.mkdir(); (rot36b / 'tack').mkdir()
(rot36b / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1><form action="/api/forfragan" method="post"><input name="namn" type="text"><button type="submit">Skicka</button></form></body></html>')
(rot36b / 'tack' / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Tack</title></head><body><h1>Tack</h1></body></html>')
srv36b, bas36b = server(rot36b, functools.partial(Mottagare36, directory=str(rot36b)))
for flagga, vantat in ((False, 0), (True, 1)):
    Mottagare36.poster.clear()
    extra36 = ['--formular-far-skickas', '--testmarkering', 'NWP-PROV'] if flagga else []
    r36b = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'utforska.mjs'), '--adress', bas36b + '/', '--ut', str(tmp / ('ut36b-%d' % flagga)), '--max-sidor', '1', *extra36],
                          capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=300)
    uf36 = json.loads((tmp / ('ut36b-%d' % flagga) / 'UTFORSKNING.json').read_text())
    form36 = [f_ for s_ in uf36.get('sidor', []) for f_ in (s_.get('formular') or [])]
    assert (len(Mottagare36.poster) >= 1) == flagga, (flagga, Mottagare36.poster, r36b.stderr[-300:])  # med flaggan också ett återförsök (dubblettprovet)
    assert form36 and bool(form36[0].get('skickat')) == flagga, (flagga, form36, r36b.stdout[-300:])
srv36b.shutdown()
print('R12 F36 utforska ok')

# F18: omgången avbryts när underlaget ändrats sedan bokföringen (referenserna fryses före granskarloopen)
r18b = gdir18 / 'runda-12'; r18b.mkdir()
gr.frys_bygget(kund, r18b)  # som drivaren (Codex R24)
(r18b / 'UPPDRAG.json').write_text(json.dumps({'slug': 'ett-abx', 'runda': 12, 'korning': 'prov', 'tid': gr.nu(), 'dist_sha256': prova.dist_hash(kund / 'sajt' / 'dist'),
                                              'modell': 'opus[1m]', 'effort': 'high', 'frist': 60, 'granskare': gr.ANTAL, 'originalitet': 'skugga', 'metod_sha': 'bokford-metod'}))
rc18b = gr.arbetare(r18b)
assert (r18b / 'FEL.txt').is_file() and 'ändrades' in (r18b / 'FEL.txt').read_text() and not (r18b / 'PROMPT.txt').exists(), 'ändrat underlag mellan bokföring och start ska avbryta omgången (F18)'
print('R12 F18 frysning före loopen ok')

# F32: procentkodade interna länkar
(d32 / 'våra-tjänster').mkdir(); (d32 / 'våra-tjänster' / 'index.html').write_text('<html lang="sv"><head><title>v</title></head><body><h1>v</h1></body></html>')
assert seo.finns_lokalt(d32, 'v%C3%A5ra-tj%C3%A4nster/', '/', None, None) is True and seo.finns_lokalt(d32, '/v%C3%A5ra-tj%C3%A4nster/', '/', None, None) is True, 'procentkodad länk ska hittas (F32)'
assert seo.finns_lokalt(d32, '/%2e%2e/%2e%2e/etc/passwd', '/', None, None) in (None, False), 'kodad ../ får inte lämna dist'
print('R12 F32 procentkodade länkar ok')


# ---------------------------------------------------------------- omgång tretton (Codex R13): F35 (gemensamt underlag), F33 (intervall, trunkering), F36 (formulärets mål)
# F35: underlag/<slug> delas av kampanjer; gallring i en kampanj rör aldrig material som en annan kampanj har kvar


def kampanj13(kid, poster):
    (pf11.PROSPEKT / kid).mkdir(parents=True, exist_ok=True)
    (pf11.PROSPEKT / kid / 'KAMPANJ.json').write_text(json.dumps({'id': kid, 'skapad': '2026-01-01'}))
    pf11.skriv_json(pf11.kampanjkatalog(kid) / 'REGISTER.json', list(poster))  # fixtur: skriver rakt, också över en avsiktligt trasig fil


for ordning in (('kamp-a', 'kamp-b'), ('kamp-b', 'kamp-a')):
    for kid in ('kamp-a', 'kamp-b'):
        shutil.rmtree(pf11.PROSPEKT / kid, ignore_errors=True)
    kampanj13('kamp-a', [{'slug': 'delad', 'peOrgNr': '1', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}])
    kampanj13('kamp-b', [{'slug': 'delad', 'peOrgNr': '1', 'status': 'kund', 'skapad': gammal35, 'uppdaterad': gammal35}])
    (tmp / 'underlag' / 'delad').mkdir(parents=True, exist_ok=True); (tmp / 'underlag' / 'delad' / 'x.txt').write_text('x')
    for kid in ordning:
        pr.gallra(types.SimpleNamespace(manader=12, kampanj=kid, torr=False))
    assert (tmp / 'underlag' / 'delad' / 'x.txt').is_file(), 'kundens underlag i den andra kampanjen får inte raderas (F35, ordning %s)' % (ordning,)
    assert not [p_ for p_ in pf11.las_register('kamp-a') if p_.get('slug') == 'delad'] and [p_ for p_ in pf11.las_register('kamp-b') if p_.get('slug') == 'delad'][0]['status'] == 'kund'
    logg13 = [json.loads(x) for x in (pf11.kampanjkatalog('kamp-a') / 'logg.jsonl').read_text().splitlines()]
    assert any(x['handelse'] == 'gallrad' and x.get('material') == 'kvar' and 'kamp-b' in (x.get('refereras_av') or []) for x in logg13), logg13[-3:]
for kid in ('kamp-a', 'kamp-b'):
    shutil.rmtree(pf11.PROSPEKT / kid, ignore_errors=True)
kampanj13('kamp-a', [{'slug': 'delad2', 'peOrgNr': '2', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}])
kampanj13('kamp-b', [{'slug': 'delad2', 'peOrgNr': '2', 'status': 'demo', 'skapad': gammal35, 'uppdaterad': gammal35}])
(tmp / 'underlag' / 'delad2').mkdir(parents=True, exist_ok=True); (tmp / 'underlag' / 'delad2' / 'x.txt').write_text('x')
pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)); assert (tmp / 'underlag' / 'delad2').exists(), 'kb har posten kvar: materialet behålls'
pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-b', torr=False)); assert not (tmp / 'underlag' / 'delad2').exists(), 'sista kampanjen gallrar materialet'
kampanj13('kamp-c', [{'slug': 'x-firma', 'peOrgNr': '9', 'status': 'ny'}])
assert 'x-firma' in pr.tagna_slugs([], egen_pe='8') and 'x-firma' not in pr.tagna_slugs([], egen_pe='9'), 'slugtilldelningen ser andra kampanjers slugs (F35)'
print('R13 F35 gemensamt underlag ok')

# F33: metadata i flera dataintervall, trunkerat TIFF och intervall utanför filen är inte rena


def avif_ext(objekt):
    """objekt: [(typ, [delar], content_type)]; varje del blir ett eget dataintervall."""
    ftyp = box33(b'ftyp', b'avif' + b'\x00\x00\x00\x00' + b'avifmif1'); hdlr = fullbox33(b'hdlr', b'\x00' * 4 + b'pict' + b'\x00' * 13)
    infes = b''.join(fullbox33(b'infe', struct.pack('>HH', i + 1, 0) + typ + b'\x00' + (ct + b'\x00' if ct else b''), v=2) for i, (typ, _, ct) in enumerate(objekt))
    iinf = fullbox33(b'iinf', struct.pack('>H', len(objekt)) + infes)

    def iloc(bas):
        kropp, off = bytes([0x44, 0x00]) + struct.pack('>H', len(objekt)), bas
        for i, (_, delar, _) in enumerate(objekt):
            kropp += struct.pack('>HHH', i + 1, 0, len(delar))
            for d_ in delar:
                kropp += struct.pack('>II', off, len(d_)); off += len(d_)
        return fullbox33(b'iloc', kropp)
    meta = fullbox33(b'meta', hdlr + iinf + iloc(0)); meta = fullbox33(b'meta', hdlr + iinf + iloc(len(ftyp) + len(meta) + 8))
    return ftyp + meta + box33(b'mdat', b''.join(d_ for _, delar, _ in objekt for d_ in delar))


xmp_a, xmp_b = b'<x:xmpmeta><rdf:Description ', b'exif:GPSLatitude="65,35.2N"/></x:xmpmeta>'
assert bd.avif_metadata(avif_ext([(b'mime', [xmp_a, xmp_b], b'application/rdf+xml')]))[0] == 'oklar', 'GPS i det andra dataintervallet (F33)'
assert bd.avif_metadata(avif_ext([(b'Exif', [exif_rent[:6], exif_rent[6:]], None)]))[0] == 'tiff', 'ett rent EXIF i två intervall sammanfogas'
trunk13 = b'\x00\x00\x00\x00' + b'II*\x00\x08\x00'  # TIFF-huvud utan hel IFD-pekare
lage13, skal13 = bd.avif_metadata(avif_ext([(b'Exif', [trunk13], None)])); assert lage13 == 'oklar', (lage13, skal13)
fil13 = avif_ext([(b'Exif', [exif_rent], None)])[:-4]  # mdat trunkerad: intervallet pekar utanför filen
assert bd.avif_metadata(fil13)[0] == 'oklar', 'intervall utanför filen (F33)'
jpg13 = b'\xff\xd8\xff\xe1' + struct.pack('>H', len(b'Exif\x00\x00' + trunk13[4:]) + 2) + b'Exif\x00\x00' + trunk13[4:] + b'\xff\xd9'
(d33 / 'trasig.jpg').write_bytes(jpg13)
assert any(x['punkt'] == '4.2' and x['sida'] == '/trasig.jpg' and 'verifieras' in x['text'] for x in sk.granska(d33)[0]), 'parserfel i deklarerad metadata ska ge 4.2 (F33)'
(d33 / 'jobb.avif').write_bytes(avif_ext([(b'mime', [xmp_a, xmp_b], b'application/rdf+xml')]))
assert any(x['punkt'] == '4.2' and x['sida'] == '/jobb.avif' for x in sk.granska(d33)[0]), 'delat XMP med GPS ska ge 4.2'
print('R13 F33 intervall och trunkering ok')

# F36: bara ett POST-svar från formulärets mål räknas som inskick; fälten får giltiga värden


class Mottagare13(Tyst):
    poster = []

    def do_POST(self):
        n_ = int(self.headers.get('Content-Length') or 0); Mottagare13.poster.append((self.path, self.rfile.read(n_).decode('utf-8', 'replace')))
        if self.path == '/api/forfragan':
            self.send_response(303); self.send_header('Location', '/tack/')
        else:
            self.send_response(204)
        self.send_header('Content-Length', '0'); self.end_headers()


skript13 = '<script>document.querySelector("button").addEventListener("click", () => { fetch("/annat", {method: "POST", body: "x"}).catch(() => {}); });</script>'
tack13 = '<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Tack</title></head><body><h1>Tack</h1></body></html>'
for namn13, falt13, vantat13 in (('a', '<input name="telefon" type="tel" pattern="[0-9+\\-\\(\\) ]{6,40}" required>', True), ('b', '<input name="kod" type="text" pattern="\\d{3}" required>', False)):
    rot13 = tmp / ('sajt13' + namn13); (rot13 / 'tack').mkdir(parents=True); (rot13 / 'tack' / 'index.html').write_text(tack13)
    (rot13 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1><form action="/api/forfragan" method="post">' + falt13 + '<button type="submit">Skicka</button></form>' + skript13 + '</body></html>')
    srv13, bas13 = server(rot13, functools.partial(Mottagare13, directory=str(rot13)))
    Mottagare13.poster.clear()
    r13 = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'utforska.mjs'), '--adress', bas13 + '/', '--ut', str(tmp / ('ut13' + namn13)), '--max-sidor', '1', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'],
                         capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=300)
    uf13 = json.loads((tmp / ('ut13' + namn13) / 'UTFORSKNING.json').read_text())
    form13 = [f_ for s_ in uf13.get('sidor', []) for f_ in (s_.get('formular') or [])]
    vagar13 = [v_ for v_, _ in Mottagare13.poster]
    assert form13 and bool(form13[0].get('skickat')) == vantat13, (namn13, form13, vagar13, r13.stderr[-300:])
    assert ('/api/forfragan' in vagar13) == vantat13, (namn13, vagar13)
    if not vantat13:
        assert '/annat' in vagar13 and form13[0].get('andra_post', 0) >= 1, 'det orelaterade POST-anropet ska ha skett och räknats som annat (F36): %s' % (vagar13,)
    srv13.shutdown()
print('R13 F36 formulärets mål ok')


# ---------------------------------------------------------------- omgång fjorton (Codex R14): F35 (läsfel ≠ frånvaro), F33 (strikt parser, flera EXIF-objekt), F36 (återförsök, mål med fråga)
# F35: ett oläsbart register eller en kampanj utan läsbar KAMPANJ.json stoppar gallringen före varje ändring
for kid in ('kamp-a', 'kamp-b', 'kamp-c'):
    shutil.rmtree(pf11.PROSPEKT / kid, ignore_errors=True)
kampanj13('kamp-a', [{'slug': 'delad3', 'peOrgNr': '3', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}])
kampanj13('kamp-b', [{'slug': 'delad3', 'peOrgNr': '3', 'status': 'kund', 'skapad': gammal35, 'uppdaterad': gammal35}])
(tmp / 'underlag' / 'delad3').mkdir(parents=True, exist_ok=True); (tmp / 'underlag' / 'delad3' / 'x.txt').write_text('x')
fore14 = (pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').read_text()
(pf11.kampanjkatalog('kamp-b') / 'REGISTER.json').write_text('{trasig')  # oläsbart register i B
assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 2
assert (tmp / 'underlag' / 'delad3' / 'x.txt').is_file() and (pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').read_text() == fore14, 'läsfel i B får inte tolkas som frånvaro; inget får ändras (F35)'
kampanj13('kamp-b', [{'slug': 'delad3', 'peOrgNr': '3', 'status': 'kund', 'skapad': gammal35, 'uppdaterad': gammal35}])
(pf11.kampanjkatalog('kamp-b') / 'KAMPANJ.json').write_text('')  # tom kampanjbeskrivning: kampanjen finns ändå
assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 0
assert (tmp / 'underlag' / 'delad3' / 'x.txt').is_file(), 'en kampanj utan läsbar KAMPANJ.json räknas ändå (F35)'
(pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').write_text('{trasig')
assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 2 and (pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').read_text() == '{trasig', 'det egna registret skrivs inte över när det inte går att läsa (F35)'
print('R14 F35 strikt inventering ok')

# F33: ofullständiga deklarerade tabeller är parserfel; GPS i något EXIF-objekt gäller för filen
ifd_kort = b'II*\x00' + struct.pack('<I', 8) + struct.pack('<H', 2) + struct.pack('<HHII', 0x0110, 2, 4, 0)  # deklarerar två poster, har en
for block14, vad14 in ((ifd_kort, 'en deklarerad post som saknas'), (b'II*\x00' + struct.pack('<I', 400), 'IFD-pekare utanför blocket')):
    try:
        bd.exif(block14); raise AssertionError('%s ska ge parserfel (F33)' % vad14)
    except ValueError:
        pass
assert bd.avif_metadata(avif_ext([(b'Exif', [b'\x00\x00\x00\x00' + ifd_kort], None)]))[0] == 'oklar'
jpg14 = b'\xff\xd8\xff\xe1' + struct.pack('>H', len(b'Exif\x00\x00' + ifd_kort) + 2) + b'Exif\x00\x00' + ifd_kort + b'\xff\xd9'
(d33 / 'kort.jpg').write_bytes(jpg14)
assert any(x['punkt'] == '4.2' and x['sida'] == '/kort.jpg' and 'verifieras' in x['text'] for x in sk.granska(d33)[0]), 'ofullständig tabell i JPEG ska ge 4.2 (F33)'
assert bd.datum(d33 / 'kort.jpg')['kalla'] != 'EXIF DateTimeOriginal', 'datumet tål parserfel'
gps_tiff = b'\x00\x00\x00\x00' + tiff33
for ordning14 in ([(b'Exif', [gps_tiff], None), (b'Exif', [exif_rent], None)], [(b'Exif', [exif_rent], None), (b'Exif', [gps_tiff], None)]):
    lage14, blk14 = bd.avif_metadata(avif_ext(ordning14)); assert lage14 == 'tiff' and bd.exif(blk14).get('gps'), 'GPS i något EXIF-objekt ska gälla (F33)'
    (d33 / 'jobb.avif').write_bytes(avif_ext(ordning14))
    assert any(x['punkt'] == '4.2' and x['sida'] == '/jobb.avif' for x in sk.granska(d33)[0]), 'GPS-objekt före eller efter ett rent objekt ska ge 4.2 (F33)'
print('R14 F33 strikt parser ok')

# F36: frågesträngen ingår i målidentiteten; återförsöket använder samma värden och samma målkorrelation
rot14 = tmp / 'sajt14'; (rot14 / 'tack').mkdir(parents=True); (rot14 / 'tack' / 'index.html').write_text(tack13)
(rot14 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1><form action="/api?op=send" method="post"><input name="kod" type="text" pattern="\\d{3}" required><button type="submit">Skicka</button></form>'
                                  '<script>document.querySelector("button").addEventListener("click", () => { fetch("/api?op=analytics", {method: "POST", body: "x"}).catch(() => {}); });</script></body></html>')
srv14, bas14 = server(rot14, functools.partial(Mottagare13, directory=str(rot14)))
Mottagare13.poster.clear()
r14 = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'utforska.mjs'), '--adress', bas14 + '/', '--ut', str(tmp / 'ut14'), '--max-sidor', '1', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'],
                     capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=300)
uf14 = json.loads((tmp / 'ut14' / 'UTFORSKNING.json').read_text()); form14 = [f_ for s_ in uf14.get('sidor', []) for f_ in (s_.get('formular') or [])]
assert form14 and not form14[0].get('skickat') and form14[0]['mal']['url'].endswith('/api?op=send'), (form14, r14.stderr[-300:])
assert any(v_ == '/api?op=analytics' for v_, _ in Mottagare13.poster) and not any(v_ == '/api?op=send' for v_, _ in Mottagare13.poster), Mottagare13.poster
srv14.shutdown()
rot14b = tmp / 'sajt14b'; (rot14b / 'tack').mkdir(parents=True); (rot14b / 'tack' / 'index.html').write_text(tack13)
(rot14b / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1><form action="/api/forfragan" method="post"><input name="telefon" type="tel" pattern="[0-9+\\-\\(\\) ]{6,40}" required><button type="submit">Skicka</button></form></body></html>')
srv14b, bas14b = server(rot14b, functools.partial(Mottagare13, directory=str(rot14b)))
Mottagare13.poster.clear()
r14b = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'utforska.mjs'), '--adress', bas14b + '/', '--ut', str(tmp / 'ut14b'), '--max-sidor', '1', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'],
                      capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=300)
uf14b = json.loads((tmp / 'ut14b' / 'UTFORSKNING.json').read_text()); form14b = [f_ for s_ in uf14b.get('sidor', []) for f_ in (s_.get('formular') or [])]
assert form14b and form14b[0].get('skickat') and form14b[0]['dubbelt'] == {'post_antal': 1, 'identiska_uppgifter': True}, (form14b, r14b.stderr[-300:])
kroppar14 = [k_ for v_, k_ in Mottagare13.poster if v_ == '/api/forfragan']
assert len(kroppar14) == 2 and kroppar14[0] == kroppar14[1], 'återförsöket ska skicka samma uppgifter (F36): %s' % kroppar14
srv14b.shutdown()
print('R14 F36 återförsök och mål ok')


# ---------------------------------------------------------------- omgång femton (Codex R15): F35 (läsning i låset, ogiltiga poster), F36 (maskade mål)
# F35: ett läsfel vid skrivningen skriver inget; ogiltiga poster inuti en lista är okänd status
for kid in ('kamp-a', 'kamp-b', 'kamp-c'):
    shutil.rmtree(pf11.PROSPEKT / kid, ignore_errors=True)
kampanj13('kamp-a', [{'slug': 'delad4', 'peOrgNr': '4', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}, {'slug': 'kund4', 'peOrgNr': '5', 'status': 'kund', 'skapad': gammal35, 'uppdaterad': gammal35}])
kampanj13('kamp-b', [{'slug': 'delad4', 'peOrgNr': '4', 'status': 'kund', 'skapad': gammal35, 'uppdaterad': gammal35}])
(tmp / 'underlag' / 'delad4').mkdir(parents=True, exist_ok=True); (tmp / 'underlag' / 'delad4' / 'x.txt').write_text('x')
fore15 = (pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').read_text()
_strikt, rakn15 = pf11.las_register_strikt, {'n': 0}


def andra_lasningen_faller(kampanj):  # förkontrollen lyckas; läsningen inne i låset simulerar ett rättighetsfel
    rakn15['n'] += 1
    if kampanj == 'kamp-a' and rakn15['n'] > 1:
        raise pf11.RegisterFel('PermissionError: simulerat')
    return _strikt(kampanj)


pf11.las_register_strikt = andra_lasningen_faller
try:
    assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 2
finally:
    pf11.las_register_strikt = _strikt
assert (pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').read_text() == fore15 and (tmp / 'underlag' / 'delad4' / 'x.txt').is_file(), 'ett läsfel vid skrivningen får inte skriva ett tomt register (F35)'
assert any(p_['slug'] == 'kund4' for p_ in pf11.las_register('kamp-a')), 'kundposten ska finnas kvar'
for trasigt in ('[null]', '[{"status": "kund"}]', '[{"slug": "delad4"}]', '[{"slug": "Fel Slug", "status": "kund"}]'):
    (pf11.kampanjkatalog('kamp-b') / 'REGISTER.json').write_text(trasigt)
    assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 2, trasigt
    assert (tmp / 'underlag' / 'delad4' / 'x.txt').is_file() and (pf11.kampanjkatalog('kamp-a') / 'REGISTER.json').read_text() == fore15, 'ogiltig post i B är okänd status (F35): %s' % trasigt
try:
    pf11.las_register_strikt('kamp-b'); raise AssertionError('ogiltig post ska ge RegisterFel')
except pf11.RegisterFel:
    pass
print('R15 F35 strikt läsning i låset ok')

# F36: maskade hemliga parametrar får inte göra två mål identiska; rapporten visar bara den maskade adressen
for namn15, falt15, vantat15 in (('a', '<input name="kod" type="text" pattern="\\d{3}" required>', False), ('b', '<input name="telefon" type="tel" pattern="[0-9+\\-\\(\\) ]{6,40}" required>', True)):
    rot15 = tmp / ('sajt15' + namn15); (rot15 / 'tack').mkdir(parents=True); (rot15 / 'tack' / 'index.html').write_text(tack13)
    (rot15 / 'index.html').write_text('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>t</title></head><body><h1>Hej</h1><form action="/api?key=form-a" method="post">' + falt15 + '<button type="submit">Skicka</button></form>'
                                      '<script>document.querySelector("button").addEventListener("click", () => { fetch("/api?key=analytics-b", {method: "POST", body: "x"}).catch(() => {}); });</script></body></html>')
    srv15, bas15 = server(rot15, functools.partial(Mottagare13, directory=str(rot15)))
    Mottagare13.poster.clear()
    r15 = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'utforska.mjs'), '--adress', bas15 + '/', '--ut', str(tmp / ('ut15' + namn15)), '--max-sidor', '1', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'],
                         capture_output=True, text=True, cwd=str(ROOT), env={k_: v_ for k_, v_ in os.environ.items() if k_ != 'NWP_SLUG'}, timeout=300)
    rapport15 = (tmp / ('ut15' + namn15) / 'UTFORSKNING.json').read_text()
    uf15 = json.loads(rapport15); form15 = [f_ for s_ in uf15.get('sidor', []) for f_ in (s_.get('formular') or [])]
    assert form15 and bool(form15[0].get('skickat')) == vantat15, (namn15, form15, r15.stderr[-300:])
    assert 'analytics-b' not in rapport15 and 'form-a' not in rapport15, 'hemliga parametrar maskas i rapporten'
    if not vantat15:
        assert any(v_ == '/api?key=analytics-b' for v_, _ in Mottagare13.poster) and form15[0].get('andra_post', 0) >= 1 and form15[0]['dubbelt']['post_antal'] == 0, (form15, Mottagare13.poster)
    srv15.shutdown()
print('R15 F36 maskade mål ok')


# ---------------------------------------------------------------- omgång sexton (Codex R16): F35 (återaktiverad kund, statusändring under gallringen)
for kid in ('kamp-a', 'kamp-b', 'kamp-c'):
    shutil.rmtree(pf11.PROSPEKT / kid, ignore_errors=True)
kampanj13('kamp-a', [{'slug': 'delad5', 'peOrgNr': '6', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}])
kampanj13('kamp-b', [{'slug': 'delad5', 'peOrgNr': '6', 'status': 'nej', 'skapad': gammal35, 'uppdaterad': gammal35}])
(tmp / 'underlag' / 'delad5').mkdir(parents=True, exist_ok=True); (tmp / 'underlag' / 'delad5' / 'x.txt').write_text('x')
assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-b', torr=False)) == 0
assert [p_ for p_ in pf11.las_register('kamp-b') if p_['slug'] == 'delad5'][0].get('gallrad'), 'nej-posten är minimerad med markör'
post16 = pf11.satt_status('kamp-b', 'delad5', 'kund')
assert post16 and 'gallrad' not in post16, 'återaktivering tar bort gallringsmarkören (F35)'
assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 0
assert (tmp / 'underlag' / 'delad5' / 'x.txt').is_file(), 'en återaktiverad kund skyddar materialet (F35)'
pf11.skriv_json(pf11.kampanjkatalog('kamp-b') / 'REGISTER.json', [{'slug': 'delad5', 'peOrgNr': '6', 'status': 'kund', 'gallrad': gammal35, 'uppdaterad': gammal35}])
kampanj13('kamp-a', [{'slug': 'delad5', 'peOrgNr': '6', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}])
assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 0 and (tmp / 'underlag' / 'delad5' / 'x.txt').is_file(), 'kundstatus väger tyngre än en kvarlämnad markör (F35)'
# en statusändring under gallringen väntar tills gallringen är klar: låset omfattar inventering, beslut och radering
kampanj13('kamp-a', [{'slug': 'delad6', 'peOrgNr': '7', 'status': 'skickat', 'skapad': gammal35, 'uppdaterad': gammal35}])
kampanj13('kamp-b', [{'slug': 'delad6', 'peOrgNr': '7', 'status': 'nej', 'skapad': gammal35, 'uppdaterad': gammal35, 'gallrad': gammal35}])
(tmp / 'underlag' / 'delad6').mkdir(parents=True, exist_ok=True); (tmp / 'underlag' / 'delad6' / 'x.txt').write_text('x')
tider16, _rmtree16 = {}, pr.shutil.rmtree


def rmtree_med_konkurrent(d_, **kw):
    tr_ = threading.Thread(target=lambda: tider16.update(status=(pf11.satt_status('kamp-b', 'delad6', 'kund'), time.monotonic())))
    tr_.start(); tider16['trad'] = tr_; time.sleep(0.5)
    tider16['radering'] = time.monotonic(); tider16['vantade'] = tr_.is_alive()
    return _rmtree16(d_, **kw)


pr.shutil.rmtree = rmtree_med_konkurrent
try:
    assert pr.gallra(types.SimpleNamespace(manader=12, kampanj='kamp-a', torr=False)) == 0
finally:
    pr.shutil.rmtree = _rmtree16
tider16['trad'].join(10)
assert tider16.get('vantade') and 'status' in tider16 and tider16['status'][1] > tider16['radering'] and tider16['status'][0]['status'] == 'kund', 'statusändringen ska vänta på gallringens lås (F35): %s' % tider16
print('R16 F35 återaktivering och lås ok')


# ---------------------------------------------------------------- referensöverföringen (backlogposten 2026-10-03): utpekade rutor följer med
import referensval as rv  # noqa: E402
u_rv = tmp / 'underlag' / 'ref-abx'; (u_rv / 'referenser' / 'bluetit').mkdir(parents=True); (u_rv / 'referenser' / 'govuk').mkdir(parents=True)
for namn_, fil_ in (('bluetit', 'vy-390-forsta.png'), ('bluetit', 'vy-1440-ruta-02.png'), ('govuk', 'vy-390-forsta.png'), ('govuk', 'vy-390-ruta-03.png')):
    (u_rv / 'referenser' / namn_ / fil_).write_bytes(b'\x89PNG' + namn_.encode() + fil_.encode())
(u_rv / 'REFERENSER.md').write_text('# Referenser\n\n## 1. Blue Tit (hantverk)\n\nhttps://bluetitlondon.com · prislista.\n'
                                   'Bildval: referenser/bluetit/vy-1440-ruta-02.png — prislistan med nivåer efter erfarenhet — Fråga: syns elevpriset utan att gömma mästarpriset?\n'
                                   'Bildval: referenser/bluetit/saknas.png — något — Fråga: finns den?\n'
                                   'Bildval: referenser/../REFERENSER.md — utanför — Fråga: läcker?\n\n'
                                   '## 2. GOV.UK (UX)\n\nBildval: referenser/govuk/vy-390-ruta-03.png — kontaktsidans nummer, tid och vad som händer sen — Fråga: läses det i en skärmhöjd på 390?\n'
                                   '\n## 3. Utan bildval\n\ntext\n')
(u_rv / 'referenser' / 'dinesen').mkdir(); (u_rv / 'referenser' / 'dinesen' / 'vy-390-forsta.png').write_bytes(b'\x89PNGdinesen')
val_rv = rv.bildval('ref-abx', tmp / 'underlag')
assert [v['fil'].name if v['fil'] else v['fel'] for v in val_rv] == ['vy-1440-ruta-02.png', 'filen saknas eller är ingen bild', 'utanför referenser/', 'vy-390-ruta-03.png'], val_rv
assert val_rv[0]['referens'].startswith('1. Blue Tit') and val_rv[3]['referens'].startswith('2. GOV.UK')
bilder_rv = rv.referensbilder('ref-abx', tmp / 'underlag')
assert [p_.name for p_, _ in bilder_rv][:2] == ['vy-1440-ruta-02.png', 'vy-390-ruta-03.png'] and 'Fråga: syns elevpriset' in bilder_rv[0][1], bilder_rv
assert any(p_.parent.name == 'dinesen' and t_ == 'första vyn' for p_, t_ in bilder_rv) and not any(p_.name == 'vy-390-forsta.png' and p_.parent.name == 'bluetit' for p_, _ in bilder_rv), 'första vyn bara som reserv för referenser utan bildval: %s' % bilder_rv
(tmp / 'kunder' / 'ref-abx' / 'sajt' / 'dist').mkdir(parents=True)
text_rv = gr.uppdrag_text('ref-abx', 'http://x', ['/'], tmp / 'arb', [], gr.referensbilder('ref-abx'), [], [], tmp / 'runda-rv')
assert 'referenser/bluetit/vy-1440-ruta-02.png — prislistan med nivåer efter erfarenhet — Fråga: syns elevpriset' in text_rv and 'ruta eller det tillstånd' in text_rv, text_rv[-900:]
fr_rv = gr.frysta_referenser('ref-abx', tmp / 'runda-rv'); assert fr_rv[0][0].name.endswith('vy-1440-ruta-02.png') and 'Fråga:' in fr_rv[0][1]
filer_rv, refs_rv, _ = a.underlag_rader('ref-abx')
assert refs_rv and 'vy-1440-ruta-02.png — prislistan' in refs_rv[0] and 'Fråga: syns elevpriset' in refs_rv[0], refs_rv
assert 'Bildval' in (ROOT / '.claude' / 'skills' / 'bygg-sajt' / 'SKILL.md').read_text() and 'Land-book' in (ROOT / 'kunskap' / 'referensjakt.md').read_text()
print('referensöverföringen ok')
# ---------------------------------------------------------------- kalibreringen (backlogposten 2026-10-03): ägaren dömer externa exempel blint i dashboarden
kal = tmp / 'underlag' / 'kalibrering'; (kal / 'K01' / 'start').mkdir(parents=True); (kal / 'K02' / 'start').mkdir(parents=True)
(kal / 'URVAL.txt').write_text('# id · nivå · adress · roll\nK01 · over · https://exempel-a.test/ · hållning\nK02 · generisk · https://exempel-b.test/ · nuvarande sajt\n')
for kid_ in ('K01', 'K02'):
    for fil_ in ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png'):
        (kal / kid_ / 'start' / fil_).write_bytes(b'\x89PNG')
dsrvk = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H); threading.Thread(target=dsrvk.serve_forever, daemon=True).start()
dport = dsrvk.server_port; dash.VARD['tillatna'] = {'127.0.0.1:%d' % dport, 'localhost:%d' % dport}
kod, kropp = begar(dport, 'GET', '/api/kalibrering'); lista_k = json.loads(kropp)
assert kod == 200 and [e_['id'] for e_ in lista_k] == ['K01', 'K02'] and all('url' not in e_ and not e_['dom'] for e_ in lista_k), 'blint före domen: ingen adress, ingen hypotes'
assert lista_k[0]['bilder']['start-390-forsta'] == 'underlag/kalibrering/K01/start/vy-390-forsta.png' and begar(dport, 'GET', '/fil/' + lista_k[0]['bilder']['start-390-forsta'])[0] == 200
kod, _ = begar(dport, 'POST', '/api/kalibrering/K01', huvuden={'Origin': 'http://evil.test:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{"niva":"over"}'); assert kod == 403
kod, _ = begar(dport, 'POST', '/api/kalibrering/K01', huvuden={'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{"niva":"fel"}'); assert kod >= 400, kod
kod, kropp = begar(dport, 'POST', '/api/kalibrering/K01', huvuden={'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}, kropp=json.dumps({'niva': 'over', 'skiljer': 'bildvalet och rytmen'}).encode())
assert kod == 200 and json.loads(kropp)['kvar'] == 1, kropp
domar_k = json.loads((kal / 'DOMAR.json').read_text()); assert domar_k['K01']['niva'] == 'over' and domar_k['K01']['skiljer'] == 'bildvalet och rytmen'
kod, kropp = begar(dport, 'GET', '/api/kalibrering'); lista_k = json.loads(kropp)
assert lista_k[0]['url'] == 'https://exempel-a.test/' and lista_k[0]['hypotes'] == 'over' and lista_k[0]['dom']['niva'] == 'over' and 'url' not in lista_k[1], 'adress och hypotes visas först efter domen'
kod, _ = begar(dport, 'POST', '/api/kalibrering/K09', huvuden={'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{"niva":"over"}'); assert kod >= 400, 'okänt exempel'
dsrvk.shutdown()
print('kalibreringen ok')
# ---------------------------------------------------------------- designprovet i dashboarden: ägaren dömer förslagen blint bredvid huvudreferensen
dp_ = tmp / 'underlag' / 'dp-prov' / 'atelje'
for n_ in (1, 2, 3):
    (dp_ / str(n_) / 'undersida').mkdir(parents=True)
    for fil_ in ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png', 'vy-1440-hela.png', 'undersida/vy-390-forsta.png'):
        (dp_ / str(n_) / fil_).write_bytes(b'\x89PNG')
(dp_ / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {'1': [], '2': [], '3': []}}))
(dp_ / 'VAL.json').write_text(json.dumps({'val': 2, 'ribban': {}, 'nivaer': {}, 'poang': {'1': 1, '2': 4, '3': 1}}))
(dp_ / 'VAL.md').write_text('# Ateljéns val\n\nVald riktning: **2**\n')
ref_dp = tmp / 'underlag' / 'dp-prov' / 'referenser' / 'paket-v01' / 'snick' / '01-start'; ref_dp.mkdir(parents=True); (ref_dp / 'vy-390-ruta-01.png').write_bytes(b'\x89PNG')
(tmp / 'underlag' / 'dp-prov' / 'REFERENSER.md').write_text('## Snick — snickeri\n\nBildval: referenser/paket-v01/snick/01-start/vy-390-ruta-01.png — första vyn — Fråga: bär vår lika mycket?\n\nHuvudreferens: Snick — komposition och bildbehandling\n')
dsrvd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H); threading.Thread(target=dsrvd.serve_forever, daemon=True).start()
dport = dsrvd.server_port; dash.VARD['tillatna'] = {'127.0.0.1:%d' % dport, 'localhost:%d' % dport}
assert 'dp-prov' in json.loads(begar(dport, 'GET', '/api/designprov')[1])
kod, kropp = begar(dport, 'GET', '/api/designprov/dp-prov'); d_ = json.loads(kropp)
assert kod == 200 and [f_['bokstav'] for f_ in d_['forslag']] == ['A', 'B', 'C'] and 'avslojat' not in d_ and not any(f_['dom'] for f_ in d_['forslag']), d_
assert d_['huvudreferens']['namn'] == 'Snick' and d_['huvudreferens']['bilder'][0]['fil'] == 'underlag/dp-prov/referenser/paket-v01/snick/01-start/vy-390-ruta-01.png', d_['huvudreferens']
assert set(d_['forslag'][0]['bilder']) == {'390-forsta', '1440-forsta', '390-hela', '1440-hela', 'undersida-390'}
assert begar(dport, 'GET', '/fil/' + d_['forslag'][0]['bilder']['390-forsta'])[0] == 200 and begar(dport, 'GET', '/fil/' + d_['huvudreferens']['bilder'][0]['fil'])[0] == 200
assert begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/VAL.md')[0] != 200 and begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/VAL.json')[0] != 200, 'panelens dom är dold tills ägaren dömt alla'
assert begar(dport, 'GET', '/api/designprov/okand')[0] == 404
ok_h = {'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}
assert begar(dport, 'POST', '/api/designprov/dp-prov/A', huvuden={'Origin': 'http://evil.test:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{"haller":true,"niva":"over"}')[0] == 403
assert begar(dport, 'POST', '/api/designprov/dp-prov/A', huvuden=ok_h, kropp=b'{"haller":"ja","niva":"over"}')[0] >= 400, 'haller är sant eller falskt'
assert begar(dport, 'POST', '/api/designprov/dp-prov/D', huvuden=ok_h, kropp=b'{"haller":true,"niva":"over"}')[0] >= 400, 'okänt förslag'
for b_, h_, n_ in (('A', False, 'nastan'), ('B', True, 'over')):
    assert begar(dport, 'POST', '/api/designprov/dp-prov/' + b_, huvuden=ok_h, kropp=json.dumps({'haller': h_, 'niva': n_, 'skiljer': 'prov ' + b_}).encode())[0] == 200
assert 'avslojat' not in json.loads(begar(dport, 'GET', '/api/designprov/dp-prov')[1]) and begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/VAL.md')[0] != 200, 'två av tre dömda: fortfarande blint'
assert begar(dport, 'POST', '/api/designprov/dp-prov/C', huvuden=ok_h, kropp=json.dumps({'haller': False, 'niva': 'generisk'}).encode())[0] == 200
d_ = json.loads(begar(dport, 'GET', '/api/designprov/dp-prov')[1])
assert d_['avslojat']['panelens_val'] == 2 and sorted(d_['avslojat']['karta'].values()) == [1, 2, 3] and 'Vald riktning' in d_['avslojat']['val_md'], d_.get('avslojat')
assert begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/VAL.md')[0] == 200, 'efter ägarens dom är panelens dom synlig'
dom_ = json.loads((dp_ / 'AGARENS-DOM.json').read_text()); assert dom_['B'] == dict(dom_['B'], haller=True, niva='over', skiljer='prov B'), dom_
# omgångarna (designprovet 2026-10-05): en förkastad omgång som ateljén arkiverat döms för sig, blint, och avslöjas för sig
o1_ = dp_ / 'omgang-1'
for n_ in (1, 2, 3):
    (o1_ / str(n_)).mkdir(parents=True)
    for fil_ in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
        (o1_ / str(n_) / fil_).write_bytes(b'\x89PNG')
(o1_ / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {'1': [], '2': [], '3': []}}))
(o1_ / 'VAL.json').write_text(json.dumps({'val': None})); (o1_ / 'VAL.md').write_text('# Ateljéns val\n\nAlla riktningar förkastade\n')
d_ = json.loads(begar(dport, 'GET', '/api/designprov/dp-prov')[1])
assert [(r_['id'], r_['nummer'], r_['aktuell']) for r_ in d_['rundor']] == [('omgang-1', 1, False), ('omgang-2', 2, True)], d_['rundor']
assert d_['forslag'] == d_['rundor'][1]['forslag'] and 'avslojat' in d_ and 'avslojat' not in d_['rundor'][0], 'toppnivån är den aktuella omgången, som förut'
r1_ = d_['rundor'][0]
assert r1_['forslag'][0]['bilder']['390-forsta'].startswith('underlag/dp-prov/atelje/omgang-1/') and begar(dport, 'GET', '/fil/' + r1_['forslag'][0]['bilder']['390-forsta'])[0] == 200
assert begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/omgang-1/VAL.md')[0] != 200, 'den arkiverade omgångens panel är dold tills ägaren dömt den'
for b_ in ('A', 'B'):
    assert begar(dport, 'POST', '/api/designprov/dp-prov/omgang-1/' + b_, huvuden=ok_h, kropp=json.dumps({'haller': b_ == 'A', 'niva': 'nastan', 'startad': '2000-01-01T00:00:00Z'}).encode())[0] == 200
assert begar(dport, 'POST', '/api/designprov/dp-prov/omgang-9/A', huvuden=ok_h, kropp=b'{"haller":true,"niva":"over"}')[0] >= 400, 'okänd omgång'
assert 'avslojat' not in json.loads(begar(dport, 'GET', '/api/designprov/dp-prov')[1])['rundor'][0], 'två av tre dömda i omgång 1: fortfarande blint'
startad_ = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0) - datetime.timedelta(minutes=3)
assert begar(dport, 'POST', '/api/designprov/dp-prov/omgang-1/C', huvuden=ok_h, kropp=json.dumps({'haller': False, 'niva': 'generisk', 'startad': startad_.isoformat().replace('+00:00', 'Z')}).encode())[0] == 200
d_ = json.loads(begar(dport, 'GET', '/api/designprov/dp-prov')[1])
assert d_['rundor'][0]['avslojat']['panelens_val'] is None and 'förkastade' in d_['rundor'][0]['avslojat']['val_md'], d_['rundor'][0]
assert begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/omgang-1/VAL.md')[0] == 200
dom1_ = json.loads((o1_ / 'AGARENS-DOM.json').read_text())
assert set(dom1_) == {'A', 'B', 'C'} and 'minuter' not in dom1_['A'] and 2.5 <= dom1_['C']['minuter'] <= 4, 'minuterna mäts från vyns start; en orimlig start ger inga minuter'
assert set(json.loads((dp_ / 'AGARENS-DOM.json').read_text())) == {'A', 'B', 'C'}, 'den aktuella omgångens domar rörs inte'
# den aktuella omgången nås också med sitt id (klienten skickar alltid omgångens id), och arkivet under foregaende/ visas inte
assert begar(dport, 'POST', '/api/designprov/dp-prov/omgang-2/A', huvuden=ok_h, kropp=json.dumps({'haller': True, 'niva': 'over', 'skiljer': 'om igen'}).encode())[0] == 200
assert json.loads((dp_ / 'AGARENS-DOM.json').read_text())['A']['skiljer'] == 'om igen'
(dp_ / 'foregaende' / 'gammal').mkdir(parents=True); (dp_ / 'foregaende' / 'gammal' / 'VAL.md').write_text('# gammal panel')
assert begar(dport, 'GET', '/fil/underlag/dp-prov/atelje/foregaende/gammal/VAL.md')[0] != 200, 'tidigare ateljékörningar serveras inte'
dsrvd.shutdown()
print('designprovet i dashboarden ok')

# ---------------------------------------------------------------- autonomins mått (Codex helhetsbedömning 2026-10-04, punkt 9)
import autonomi as au  # noqa: E402
au_k = tmp / 'au-kunder'; au.KUNDER = au_k; au.UNDERLAG = tmp / 'au-underlag'
b1_ = au_k / 'prov-bygge'; (b1_ / 'sajt').mkdir(parents=True); (b1_ / 'prov').mkdir()
(b1_ / 'korning-20261005T010000Z.jsonl').write_text('{"type":"system"}\n{"type": "result", "num_turns": 100, "duration_ms": 600000, "total_cost_usd": 10.5}\n')
for nr_, (godk_, block_, betyg_) in enumerate(((False, 2, 6), (True, 0, 8), (True, 1, 7)), 1):
    r_ = b1_ / 'granskning' / ('runda-%02d' % nr_); r_.mkdir(parents=True)
    (r_ / 'GRANSKNING.json').write_text(json.dumps({'godkand': godk_, 'blockerande': [{}] * block_, 'kriterier': {'text': {'betyg': betyg_}}}))
    (r_ / 'svar.json').write_text(json.dumps({'num_turns': 10, 'duration_ms': 60000, 'total_cost_usd': 1.0}))
(b1_ / 'prov' / 'historik.jsonl').write_text('\n'.join(json.dumps(x_) for x_ in (
    {'ok': False, 'snabb': True, 'grindar': {'seo': False, 'axe': True}}, {'ok': True, 'snabb': False, 'grindar': {'seo': True, 'axe': True}})) + '\n')
(b1_ / 'DOM.json').write_text(json.dumps({'domar': [{'tid': '2026-10-05T02:00:00Z', 'svar': {'namn': 'Ja, efter små ändringar'}, 'minuter': 12.5}]}))
(au_k / 'rokprov-mall' / 'sajt').mkdir(parents=True)
# en omgång utan dom rangordnas inte men räknas i modellanvändningen; ateljéns arkiverade omgångar räknas
r4_ = b1_ / 'granskning' / 'runda-04'; r4_.mkdir(); (r4_ / 'UTFALL.json').write_text(json.dumps({'status': 'fel'}))
(r4_ / 'svar.json').write_text(json.dumps({'num_turns': 5, 'duration_ms': 60000, 'total_cost_usd': 0.5}))
au_a = tmp / 'au-underlag' / 'prov-bygge' / 'atelje' / 'omgang-1'; au_a.mkdir(parents=True)
(au_a / 'svar-divergera.json').write_text(json.dumps({'num_turns': 50, 'duration_ms': 120000, 'total_cost_usd': 4.0}))
# en körning utan resultatrad (avbruten): ej mätt, utanför medianerna
b2_ = au_k / 'avbrutet'; (b2_ / 'sajt').mkdir(parents=True)
(b2_ / 'korning-20261005T020000Z.jsonl').write_text('{"type":"system"}\n')
au2_ = au.bygge('avbrutet'); assert au2_['loggar_utan_resultat'] == 1 and not au.matt(au2_), au2_
assert au.sammanstall([au2_])['median_minuter'] is None and au.sammanstall([au2_])['ej_matta'] == ['avbrutet']
shutil.rmtree(b2_)
assert au.byggen() == ['prov-bygge'], au.byggen()
bb_ = au.bygge('prov-bygge')
assert bb_['bygget'] == {'sessioner': 1, 'turer': 100, 'minuter': 10.0, 'listpris_usd': 10.5} and bb_['totalt'] == {'minuter': 16.0, 'turer': 185, 'listpris_usd': 18.0}, bb_
assert bb_['granskning']['omgangar'] == 3 and bb_['granskning']['basta_runda'] == 'runda-02' and not bb_['granskning']['sista_ar_basta'] and bb_['granskning']['forsamrade_rundor'] == ['runda-03'], bb_['granskning']
assert [x['runda'] for x in bb_['granskning']['fallna_rundor']] == ['runda-04'] and bb_['ateljen']['turer'] == 50, bb_
assert bb_['provet'] == {'korningar': 2, 'roda_grindar': {'seo': 1}, 'forsta_hela_grona': 2} and bb_['agaren']['accepterad'] and bb_['agaren']['minuter'] == 12.5, bb_
sm_ = au.sammanstall([bb_])
assert sm_['andel_accepterade'] == 1.0 and sm_['agarens_minuter'] == 12.5 and sm_['sista_inte_basta'] == ['prov-bygge'], sm_
import contextlib, io  # noqa: E401,E402
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    assert au.main(['--ut', str(tmp / 'utanfor.json')]) == 2, 'utfilerna stannar i kunder/ (privat)'
    assert au.main(['--ut', str(au_k / 'AUTONOMI.json'), '--md', str(au_k / 'AUTONOMI.md')]) == 0
assert 'Accepterade utan större ändringar | 1 (100 %' in (au_k / 'AUTONOMI.md').read_text() and sm_['tydligt_daliga'] == 0
print('autonomins mått ok')


# ---------------------------------------------------------------- sandlådan (backlogposten om gräns på processnivå, F1): inställningarna, och körningen committar backloggen själv
import sandlada as sl  # noqa: E402
(tmp / 'sandrot' / 'kontroller').mkdir(parents=True); (tmp / 'sandrot' / 'kontroller' / 'sandlada-domaner.txt').write_text('# standing\nregistry.npmjs.org\n*.npmjs.org\n')
inst = sl.installningar('prov-bygge', ['https://www.Exempel.se/', 'annan.se'], gh_dir='/gh', root=tmp / 'sandrot', hem=str(tmp / 'hem'))
sb = inst['sandbox']
assert inst['env'] == {'GH_CONFIG_DIR': '/gh'} and sb['enabled'] and sb['failIfUnavailable'] and sb['allowUnsandboxedCommands'] is False
assert str(tmp / 'sandrot' / 'kontroller') in sb['filesystem']['denyWrite'] and str(tmp / 'sandrot' / '.git') in sb['filesystem']['denyWrite']
assert str(tmp / 'sandrot' / 'kunder' / 'prov-bygge') in sb['filesystem']['allowWrite'] and str(tmp / 'hem' / '.nortropic-hemligheter') in sb['filesystem']['denyRead']
dom_ = sb['network']['allowedDomains']
assert {'registry.npmjs.org', '*.npmjs.org', 'www.exempel.se', 'exempel.se', 'annan.se', 'www.annan.se'} <= set(dom_) and sb['network']['allowLocalBinding'], dom_
assert sb['credentials']['envVars'][0] == {'name': 'REFERO_MCP_TOKEN', 'mode': 'deny'}
assert sl.installningar('p', sandlada=False) == {} and json.dumps(inst)
kor_text = (ROOT / 'kor.sh').read_text()
assert 'Bash(git commit *)' not in kor_text and 'Bash(git push origin main)' not in kor_text and 'sandlada.py' in kor_text, 'ingen git i bygget; sandlådan kopplad'
# kor.sh i en kopia med en falsk claude som skriver en backlogpost: körningen committar den och pushar
kr, bare_k = tmp / 'kor-repo', tmp / 'kor-bare.git'
subprocess.run(['git', 'init', '-q', '--bare', str(bare_k)], check=True)
for namn_ in ('kor.sh', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', '.gitignore', 'dashboard.sh'):
    if (ROOT / namn_).exists():
        shutil.copy2(ROOT / namn_, kr / namn_) if kr.exists() else (kr.mkdir(), shutil.copy2(ROOT / namn_, kr / namn_))
for mapp_ in ('kontroller', '.claude', 'kritik', 'kunskap', 'mall', 'dashboard'):
    shutil.copytree(ROOT / mapp_, kr / mapp_, ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'rokprov'), symlinks=True)
(kr / 'backlog').mkdir(); (kr / 'backlog' / 'B-20261001-gammal.md').write_text('---\nid: B-20261001-gammal\n---\n# gammal\n')
gk = lambda *a: subprocess.run(['git', '-C', str(kr), *a], capture_output=True, text=True)  # noqa: E731
gk('init', '-q'); gk('add', '-A'); gk('commit', '-q', '-m', 'bas'); gk('branch', '-M', 'main'); gk('remote', 'add', 'origin', str(bare_k)); gk('push', '-q', 'origin', 'main')
(kr / 'backlog' / 'B-20261002-annan-sessions-post.md').write_text('---\nid: B-20261002-annan-sessions-post\n---\n# annan session, okommitterad\n')
os.symlink(ROOT / '.venv', kr / '.venv'); os.symlink(ROOT / 'kontroller' / 'node_modules', kr / 'kontroller' / 'node_modules')
falsk_k = tmp / 'falsk-claude-kor'; falsk_k.mkdir()
(falsk_k / 'claude').write_text('#!/bin/sh\ncat > /dev/null\n'
                                'printf -- "---\\nid: B-20261003-prov-fran-bygget\\nkalla: bygge\\nkallref: kunder/prov-bygge/RAPPORT.md\\nkorning: $NWP_KORNING\\n---\\n# post fran bygget\\n" > backlog/B-20261003-prov-fran-bygget.md\n'
                                'printf -- "---\\nid: B-20261003-under-korningen-annan\\nkalla: kirurg\\n---\\n# annan session under korningen\\n" > backlog/B-20261003-under-korningen-annan.md\n'
                                'echo "{\\"type\\":\\"result\\"}"\nexit 0\n')
(falsk_k / 'claude').chmod(0o755)
miljo_k = {k_: v_ for k_, v_ in os.environ.items() if not k_.startswith('CLAUDE_CODE_') and k_ not in ('CLAUDECODE', 'NWP_SLUG')}
miljo_k['PATH'] = str(falsk_k) + os.pathsep + miljo_k.get('PATH', ''); miljo_k['NWP_SANDLADA'] = 'av'
rk = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_k, timeout=300)
assert rk.returncode in (0, 1), (rk.returncode, rk.stdout[-400:], rk.stderr[-400:])
logg_k = gk('log', '--format=%s', '-3').stdout
assert 'Bygge prov-bygge: backlogposter' in logg_k, (logg_k, rk.stdout[-300:], rk.stderr[-300:])
assert gk('show', '--stat', '--format=', 'HEAD').stdout.count('backlog/') == 1 and 'B-20261003-prov-fran-bygget' in gk('show', '--stat', '--format=', 'HEAD').stdout, 'bara byggets nya post committas, inte den andra sessionens'
okomm_k = gk('status', '--porcelain', 'backlog').stdout
assert 'B-20261002-annan-sessions-post' in okomm_k and 'B-20261003-under-korningen-annan' in okomm_k, 'andra sessioners poster, före och under körningen, lämnas okommitterade (F3): %s' % okomm_k
assert 'Bygge prov-bygge: backlogposter' in subprocess.run(['git', '-C', str(bare_k), 'log', '--format=%s', '-1', 'main'], capture_output=True, text=True).stdout, 'pushad'
print('sandlådan: inställningar och backlogcommit ok')


# ---------------------------------------------------------------- omgång arton (Codex R18): F27/F3 publicering, F1 skrivgräns, F38 bildval, F39/F40 kalibrering
# F27/F3: backlog_commit publicerar bara byggets poster, stoppar vid hemlighet, ändrad mekanik och främmande utgående historik
import backlog_commit as bc  # noqa: E402
bc.ROOT = kr
gk('checkout', '-q', 'main'); gk('reset', '-q', '--hard', 'origin/main')
for f_ in (kr / 'backlog').glob('B-20261003-*'):
    f_.unlink()
stamp_k = '20261004T000000Z'
(kr / 'backlog' / 'B-20261004-egen.md').write_text('---\nid: B-20261004-egen\nkalla: bygge\nkallref: kunder/prov-bygge/RAPPORT.md\nkorning: %s\n---\n# egen\n' % stamp_k)
(kr / 'backlog' / 'B-20261004-annan-korning.md').write_text('---\nid: B-20261004-annan-korning\nkalla: bygge\nkallref: kunder/prov-bygge/RAPPORT.md\nkorning: 20261001T000000Z\n---\n# annan körning\n')
(kr / 'backlog' / 'B-20261004-hemlig.md').write_text('---\nid: B-20261004-hemlig\nkalla: bygge\nkallref: kunder/prov-bygge/RAPPORT.md\nkorning: %s\n---\n# hemlig\nsk-ant-api03-abcdefghijklmnopqrstuvwxyz\n' % stamp_k)
huvud_k = gk('rev-parse', 'HEAD').stdout
assert bc.main(['prov-bygge', stamp_k, '3']) == 1 and gk('rev-parse', 'HEAD').stdout == huvud_k, 'ändrad mekanik (kod 3) publicerar inget (F27)'
assert bc.main(['prov-bygge', stamp_k, '1']) == 1 and gk('rev-parse', 'HEAD').stdout == huvud_k, 'en post med hemlighet stoppar allt (F27)'
(kr / 'backlog' / 'B-20261004-hemlig.md').unlink()
assert bc.main(['prov-bygge', stamp_k, '1']) == 0 and gk('rev-parse', 'HEAD').stdout != huvud_k and gk('log', '--format=%s', '-1').stdout.startswith('Bygge prov-bygge'), 'byggets post publiceras'
assert 'B-20261004-egen' in gk('show', '--stat', '--format=', 'HEAD').stdout and 'annan-korning' not in gk('show', '--stat', '--format=', 'HEAD').stdout, 'bara körningens post (F3)'
assert 'Bygge prov-bygge' in subprocess.run(['git', '-C', str(bare_k), 'log', '--format=%s', '-1', 'main'], capture_output=True, text=True).stdout, 'pushad'
(kr / 'README-prov.md').write_text('x'); gk('add', 'README-prov.md'); gk('commit', '-q', '-m', 'annan sessions commit utanför backlog')
(kr / 'backlog' / 'B-20261004-egen2.md').write_text('---\nid: B-20261004-egen2\nkalla: bygge\nkallref: kunder/prov-bygge/RAPPORT.md\nkorning: %s\n---\n# egen 2\n' % stamp_k)
assert bc.main(['prov-bygge', stamp_k, '0']) == 1 and gk('log', '--format=%s', '-1').stdout.startswith('Bygge prov-bygge'), 'committad lokalt men pushen stoppad av främmande utgående commit (F3)'
assert 'annan sessions commit' not in subprocess.run(['git', '-C', str(bare_k), 'log', '--format=%s', '-3', 'main'], capture_output=True, text=True).stdout
print('R18 F27/F3 publicering ok')

# F1: nekandelistan räknar upp allt i roten utom byggets egna kataloger, syskonen och körmiljön
rot1 = tmp / 'sandrot1'
for d_ in ('kunder/eget', 'kunder/annan', 'underlag/eget', 'underlag/annan', 'backlog', '.venv/bin', 'kontroller/node_modules', 'mall'):
    (rot1 / d_).mkdir(parents=True)
(rot1 / 'README.md').write_text('x')
neka1 = sl.installningar('eget', root=rot1, hem=str(tmp / 'hem'))['sandbox']['filesystem']['denyWrite']
for v_ in ('kunder/annan', 'underlag/annan', '.venv', 'kontroller/node_modules', 'README.md', 'mall', '.git', 'kontroller'):
    assert str(rot1 / v_) in neka1, (v_, neka1)
for v_ in ('kunder/eget', 'underlag/eget', 'backlog', 'kunder', 'underlag'):
    assert str(rot1 / v_) not in neka1, (v_, neka1)
print('R18 F1 skrivgränsen ok')

# F38: ett felaktigt Bildval döljs inte och ersätts inte av första vyn; identiteten ur sökvägen relativt referenser/
u38 = tmp / 'underlag' / 'ref38'
for d_ in ('a/kontakt', 'b/kontakt', 'c'):
    (u38 / 'referenser' / d_).mkdir(parents=True)
(u38 / 'referenser' / 'a' / 'kontakt' / 'vy-390-forsta.png').write_bytes(b'\x89PNGa'); (u38 / 'referenser' / 'b' / 'kontakt' / 'vy-390-forsta.png').write_bytes(b'\x89PNGb')
(u38 / 'referenser' / 'b' / 'kontakt' / 'vy-390-ruta-02.png').write_bytes(b'\x89PNGb2'); (u38 / 'referenser' / 'c' / 'vy-390-forsta.png').write_bytes(b'\x89PNGc')
(u38 / 'REFERENSER.md').write_text('# R\n\n## 1. A\n\nBildval: referenser/a/kontakt/saknas.png — kontaktsidan — Fråga: var är numret?\n\n## 2. B\n\nBildval: referenser/b/kontakt/vy-390-ruta-02.png — kontaktsidan — Fråga: tid och vad som händer sen?\n\n## 3. C\n\ntext\n')
b38 = rv.referensbilder('ref38', tmp / 'underlag')
namn38 = [rv.referensnamn('referenser/' + p_.relative_to(u38 / 'referenser').as_posix()) for p_, _ in b38]
assert namn38 == ['b', 'c'], 'A har ett felaktigt Bildval (ingen reserv), B sin ruta, C sin första vy: %s' % namn38
assert not any(p_.name == 'vy-390-forsta.png' and '/referenser/b/' in p_.as_posix() for p_, _ in b38), 'B:s första vy får inte följa med när B har bildval'  # exakt mapp: tempnamnet kan sluta på b
fel38 = rv.felrader('ref38', tmp / 'underlag'); assert fel38 and 'referenser/a/kontakt/saknas.png' in fel38[0] and 'var är numret' in fel38[0], fel38
(tmp / 'kunder' / 'ref38' / 'sajt' / 'dist').mkdir(parents=True)
text38 = gr.uppdrag_text('ref38', 'http://x', ['/'], tmp / 'arb', [], gr.referensbilder('ref38'), [], [], tmp / 'runda38')
assert 'Bildval som inte gick att läsa' in text38 and 'referenser/a/kontakt/saknas.png' in text38, text38[-700:]
assert a.underlag_rader('ref38')[2] and 'referenser/a/kontakt/saknas.png' in a.underlag_rader('ref38')[2][0], 'ateljén ser det felaktiga bildvalet'
print('R18 F38 bildval ok')

# F39/F40: samtidiga domar bevaras; trasig DOMAR.json stoppar utan ändring; /fil ger bara skärmbilderna
dsrvk2 = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H); threading.Thread(target=dsrvk2.serve_forever, daemon=True).start()
dport = dsrvk2.server_port; dash.VARD['tillatna'] = {'127.0.0.1:%d' % dport, 'localhost:%d' % dport}
(kal / 'DOMAR.json').unlink(missing_ok=True)
tr39 = [threading.Thread(target=lambda i_=i_: begar(dport, 'POST', '/api/kalibrering/K0%d' % i_, huvuden={'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}, kropp=json.dumps({'niva': 'over', 'skiljer': 'd%d' % i_}).encode())) for i_ in (1, 2)]
for t_ in tr39:
    t_.start()
for t_ in tr39:
    t_.join()
domar39 = json.loads((kal / 'DOMAR.json').read_text()); assert set(domar39) == {'K01', 'K02'}, 'samtidiga domar får inte tappas (F39): %s' % domar39
(kal / 'DOMAR.json').write_text('{trasig')
kod, kropp = begar(dport, 'POST', '/api/kalibrering/K01', huvuden={'Origin': 'http://127.0.0.1:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{"niva":"nastan"}')
assert kod >= 500 and (kal / 'DOMAR.json').read_text() == '{trasig', 'en trasig domfil skrivs inte över (F39): %s %s' % (kod, kropp[:120])
(kal / 'DOMAR.json').write_text(json.dumps(domar39))
assert begar(dport, 'GET', '/fil/underlag/kalibrering/URVAL.txt')[0] == 404 and begar(dport, 'GET', '/fil/underlag/kalibrering/DOMAR.json')[0] == 404, 'hypoteserna och domarna läcker inte via /fil (F40)'
assert begar(dport, 'GET', '/fil/underlag/kalibrering/K01/start/vy-390-forsta.png')[0] == 200
dsrvk2.shutdown()
print('R18 F39/F40 kalibreringen ok')


# ---------------------------------------------------------------- omgång nitton (Codex R19): F3/F27 kandidat-ID, F28 domen, F38 panelens tak, F18/F38 fryst felstatus
gk('checkout', '-q', 'main'); gk('reset', '-q', '--hard', 'origin/main')
for f_ in (kr / 'backlog').glob('B-20261004-*'):
    f_.unlink()
stamp19 = '20261004T010000Z'
(kr / 'backlog' / 'B-20261004-kand.md').write_text('---\nid: B-20261004-kand\nkalla: bygge\nkallref: kunder/prov-bygge/RAPPORT.md\nkorning: %s\n---\n# kand\n' % stamp19)
_git19 = bc.git


def git_med_kapplopning(*a_):
    if a_ and a_[0] == 'push':  # en annan session committar på main precis före pushen
        (kr / 'backlog' / 'B-20261004-smyg.md').write_text('---\nid: B-20261004-smyg\nkalla: kirurg\n---\n# smyg\nsk-ant-api03-abcdefghijklmnopqrstuvwxyz\n')
        _git19('add', 'backlog/B-20261004-smyg.md'); _git19('commit', '-q', '-m', 'smyg')
    return _git19(*a_)


bc.git = git_med_kapplopning
try:
    rc19 = bc.main(['prov-bygge', stamp19, '0'])
finally:
    bc.git = _git19
fjarr19 = subprocess.run(['git', '-C', str(bare_k), 'log', '--format=%s', '-2', 'main'], capture_output=True, text=True).stdout
assert rc19 == 0 and fjarr19.startswith('Bygge prov-bygge') and 'smyg' not in fjarr19, 'bara den kontrollerade kandidaten pushas (F3/F27): %s' % fjarr19
assert gk('log', '--format=%s', '-1').stdout.strip() == 'smyg', 'den främmande commiten är kvar lokalt, opushad'
gk('reset', '-q', '--hard', 'origin/main')
gk('checkout', '-q', '-b', 'annan19')
(kr / 'backlog' / 'B-20261004-gren.md').write_text('---\nid: B-20261004-gren\nkalla: bygge\nkallref: kunder/prov-bygge/RAPPORT.md\nkorning: %s\n---\n# gren\n' % stamp19)
huvud19 = gk('rev-parse', 'HEAD').stdout
assert bc.main(['prov-bygge', stamp19, '0']) == 1 and gk('rev-parse', 'HEAD').stdout == huvud19, 'på en annan gren committas inget (F3)'
(kr / 'backlog' / 'B-20261004-gren.md').unlink(); gk('checkout', '-q', 'main'); gk('branch', '-q', '-D', 'annan19')


def git_ls_faller(*a_):
    if a_ and a_[0] == 'ls-files':
        return types.SimpleNamespace(returncode=128, stdout='', stderr='fatal: simulerat')
    return _git19(*a_)


bc.git = git_ls_faller
try:
    assert bc.main(['prov-bygge', stamp19, '0']) == 1, 'ett inventeringsfel är inte "inga poster" (F3)'
finally:
    bc.git = _git19
print('R19 F3/F27 kandidaten ok')

import sandlada_dom as sd  # noqa: E402
# curl -w '<http_code> <http_connect> <remote_ip> <time_connect> <time_appconnect> <time_pretransfer>' + rc + läge + diagnostik
# (mätt 2026-10-04 med lokal proxy, lokal server och sandbox-exec deny network-outbound; Codex R21: bara nekande före sändning är stoppat)
NEKAD = '*   Trying 104.20.23.154:443...\n* Immediate connect fail for 104.20.23.154: Operation not permitted\n* Failed to connect to example.com port 443 after 0 ms: Couldn\'t connect to server\n* Closing connection\n'
VAGRAD = '* connect to 127.0.0.1 port 1 from 127.0.0.1 port 61204 failed: Connection refused\n* Failed to connect to 127.0.0.1 port 1 after 0 ms: Couldn\'t connect to server\n* Closing connection\n'
assert sd.nat('200 200 127.0.0.1 0.000300 0.040000 0.040100', 0, 'proxy')[0] == 'nadd'
assert sd.nat('000 403 127.0.0.1 0.000304 0.000000 0.000000', 56, 'proxy', '* CONNECT tunnel failed, response 403\n')[0] == 'blockerad'
assert sd.nat('000 000  0.000000 0.000000 0.000000', 7, 'direkt', NEKAD)[0] == 'blockerad', 'nekad anslutning före sändning är stoppad'
assert sd.nat('000 000  0.000000 0.000000 0.000000', 7, 'direkt', VAGRAD)[0] == 'okant', 'nekad port är tvetydig: provfel (R21)'
assert sd.nat('000 000  0.000000 0.000000 0.000000', 6, 'direkt', '* Could not resolve host: example.com\n')[0] == 'okant', 'namnuppslag är tvetydigt (R21)'
assert sd.nat('000 000 127.0.0.1 0.000275 0.000000 0.000304', 52, 'direkt', '* Request completely sent off\n* Empty reply from server\n')[0] == 'ansluten', 'tomt svar efter sänd begäran är aldrig blockering (R21)'
assert sd.nat('000 200 127.0.0.1 0.000275 0.030000 0.030300', 52, 'proxy')[0] == 'ansluten', 'tunnel 200 + tomt svar är aldrig blockering (R21)'
assert sd.nat('000 000 127.0.0.1 0.000255 0.000000 0.000280', 28, 'direkt')[0] == 'ansluten', 'timeout efter sändning är tvetydigt, aldrig blockering (R21)'
assert sd.nat('000 000 127.0.0.1 0.000255 0.000000 0.000000', 35, 'direkt')[0] == 'ansluten', 'TLS-fel efter anslutning är inte blockering'
assert sd.nat('000 000  0.000000 0.000000 0.000000', 7, 'proxy')[0] == 'okant', 'onåbar proxy är provfel'
assert sd.nat('000 000 127.0.0.1 0.000255 0.000000 0.000000', 56, 'proxy')[0] == 'okant', 'anslutning till proxyn utan CONNECT-svar är provfel'
assert sd.nat('curl: command not found', 127, 'direkt')[0] == 'okant' and sd.nat('000 000  0.000000 0.000000 0.000000', 0, 'direkt')[0] == 'okant'
assert sd.nat('000 000  0.000000 0.000000 0.000000', 126, 'direkt', NEKAD)[0] == 'okant', 'startkod 126 är provfel även med rättighetstext (R21)'
assert sd.nat('000 403 127.0.0.1', 56, 'proxy')[0] == 'okant', 'det gamla trefältsformatet är provfel'
# post.py: 'status <kod>' eller 'fel <steg> <Undantag> <errno>' (mätt 2026-10-04: sandbox-exec deny network-outbound → 'fel anslut PermissionError 1')
assert sd.socketforsok('fel anslut PermissionError 1', 0, 'PermissionError: [Errno 1] Operation not permitted\n')[0] == 'blockerad'
assert sd.socketforsok('fel anslut PermissionError 13', 0, '')[0] == 'blockerad', 'EACCES vid anslutningen är stoppad (R21)'
assert sd.socketforsok('fel anslut ConnectionRefusedError 61', 0, '')[0] == 'okant', 'nekad port är tvetydig: provfel (R21)'
assert sd.socketforsok('fel anslut TimeoutError -', 0, '')[0] == 'okant' and sd.socketforsok('fel anslut OSError 65', 0, '')[0] == 'okant'
assert sd.socketforsok('fel tls SSLEOFError 8', 0, '')[0] == 'ansluten', 'TLS-fel efter TCP-anslutning är inte blockering'
assert sd.socketforsok('fel sand BrokenPipeError 32', 0, '')[0] == 'ansluten', 'fel under sändning är aldrig blockering (R21)'
assert sd.socketforsok('fel svar RemoteDisconnected -', 0, '')[0] == 'ansluten', 'RemoteDisconnected efter sänd begäran är aldrig blockering (R21)'
assert sd.socketforsok('fel svar TomtSvar -', 0, '')[0] == 'ansluten' and sd.socketforsok('status 405', 0, '')[0] == 'nadd'
assert sd.socketforsok('fel OSError [Errno 65] No route to host', 0, '')[0] == 'okant', 'det gamla formatet utan steg är provfel'
assert sd.socketforsok('', 1, 'SyntaxError: invalid syntax\n')[0] == 'okant' and sd.socketforsok('fel anslut PermissionError 1', 1, '')[0] == 'okant'
# fil- och hemlighetsförsök: startkoder 126/127/≥128 är provfel före rättighetsmatchningen (R21)
assert sd.filforsok('', 126, 'bash: /usr/bin/touch: Permission denied\n', False)[0] == 'okant', 'startkod 126 är provfel (R21)'
assert sd.filforsok('', 127, 'bash: touch: command not found\n', False)[0] == 'okant' and sd.filforsok('', 130, '', False)[0] == 'okant'
assert sd.filforsok('', 1, 'touch: kontroller/otillatet.txt: Operation not permitted\n', False)[0] == 'blockerad' and sd.filforsok('', 0, '', True)[0] == 'nadd'
assert sd.hemlighetsforsok('', 126, 'bash: /usr/bin/cat: Permission denied\n')[0] == 'okant', 'startkod 126 är provfel (R21)'
assert sd.hemlighetsforsok('', 1, 'cat: hem/.nortropic-hemligheter/x.env: Operation not permitted\n')[0] == 'blockerad'
assert sd.hemlighetsforsok('DUMMY=hemligt', 0, '')[0] == 'last' and sd.hemlighetsforsok('', 1, 'cat: x.env: No such file or directory\n')[0] == 'okant'
assert sd.hemlighetsforsok(None, None, '')[0] == 'okant'
rot28 = tmp / 'prov28'; ut28 = rot28 / 'underlag' / 'prov-bygge' / 'skript'; ut28.mkdir(parents=True)


def skriv28(namn, resultat, fel=''):
    (ut28 / namn).write_text(resultat); (ut28 / namn.replace('.txt', '-fel.txt')).write_text(fel)


def grund28():
    for namn_ in ('1-kontroller.txt', '1b-annan-kund.txt', '1c-annat-underlag.txt', '1d-venv.txt'):
        skriv28(namn_, 'rc=1\n', 'touch: kontroller/otillatet.txt: Operation not permitted\n')
    skriv28('1e-nytt-syskon.txt', 'rc=1\n', 'mkdir: kunder/ny-kund: Operation not permitted\n')
    skriv28('2-hemligt.txt', 'rc=1\n', 'cat: hem/.nortropic-hemligheter/x.env: Operation not permitted\n')
    skriv28('3a-nat-direkt.txt', '000 000  0.000000 0.000000 0.000000 rc=7', NEKAD)
    skriv28('3b-nat-proxy.txt', '000 403 127.0.0.1 0.000304 0.000000 0.000000 rc=56', '* CONNECT tunnel failed, response 403\n* Closing connection\n')
    skriv28('4-nat-ok.txt', '200 200 127.0.0.1 0.000300 0.040000 0.040100 rc=0', '* Request completely sent off\n')
    skriv28('5-skript-post.txt', 'fel anslut PermissionError 1\nrc=0\n', 'Traceback (most recent call last):\nPermissionError: [Errno 1] Operation not permitted\n')
    skriv28('6-port.txt', 'bunden 5000\nrc=0\n')
    (ut28 / '7-tillatet-rc.txt').write_text('rc=0\n'); (ut28 / '7-tillatet.txt').write_text(''); (ut28 / '8-proxy.txt').write_text('proxy=http://127.0.0.1:1\n')
    skriv28('9-tjanst.txt', '{"slug": "prov-bygge", "verktyg": ["arkivera", "granska"]} rc=0')
    skriv28('10-tjanst-utanjs.txt', 'rc=0\n'); (ut28 / 'utanjs').mkdir(exist_ok=True); (ut28 / 'utanjs' / 'UTAN-JS.json').write_text('{"schema": 1}')
    skriv28('11-tjanst-nekad.txt', 'rc=2\n', 'webbtjänsten nekade (400): {"fel": "webbtjänsten vägrar: --adress: värden example.com ligger inte i byggets domänlista"}\n')
    skriv28('12-tjanst-inskick.txt', 'rc=2\n', 'webbtjänsten nekade (400): {"fel": "webbtjänsten vägrar: --formular-far-skickas bara mot provets lokala mottagare (127.0.0.1), inte https://registry.npmjs.org/"}\n')


def fel28(namn, resultat, fel=''):
    """Antal fel och domtexten för grundläget med ett försök utbytt."""
    grund28(); skriv28(namn, resultat, fel); n_, rader_ = sd.doma(ut28, '0', rot28); return n_, '\n'.join(t_ for _, t_ in rader_)


grund28()
assert sd.doma(ut28, '0', rot28)[0] == 0, sd.doma(ut28, '0', rot28)[1]
n_, t_ = fel28('3b-nat-proxy.txt', '200 200 127.0.0.1 0.000300 0.040000 0.040100 rc=0'); assert n_ == 1 and 'väntade stoppad' in t_, 'via proxyn men målservern svarade: nått'
n_, t_ = fel28('3b-nat-proxy.txt', '000 200 127.0.0.1 0.000275 0.030000 0.030300 rc=52', '* Request completely sent off\n* Empty reply from server\n'); assert n_ == 1 and 'inte stoppad' in t_ and 'begäran sänd' in t_, 'tomt svar (52) efter sänd begäran räknas aldrig som blockering (R21)'
n_, t_ = fel28('3a-nat-direkt.txt', '000 000 104.20.23.154 0.020000 0.000000 0.000000 rc=28'); assert n_ == 1 and 'inte stoppad' in t_, 'timeout efter anslutning räknas aldrig som blockering (R21)'
n_, t_ = fel28('3a-nat-direkt.txt', '000 000  0.000000 0.000000 0.000000 rc=7', VAGRAD); assert n_ == 1 and 'provfel' in t_ and 'tvetydigt' in t_, 'nekad port utan rättighetsfel är tvetydig (R21)'
n_, t_ = fel28('3a-nat-direkt.txt', '000 000  0.000000 0.000000 0.000000 rc=6', '* Could not resolve host: example.com\n'); assert n_ == 1 and 'provfel' in t_, 'namnuppslag är tvetydigt (R21)'
n_, t_ = fel28('5-skript-post.txt', 'fel svar RemoteDisconnected -\nrc=0\n'); assert n_ == 1 and 'inte stoppad' in t_ and 'svar' in t_, 'RemoteDisconnected efter sänd POST räknas aldrig som blockering (R21)'
n_, t_ = fel28('5-skript-post.txt', 'fel sand BrokenPipeError 32\nrc=0\n'); assert n_ == 1 and 'inte stoppad' in t_, 'fel under sändning räknas aldrig som blockering (R21)'
n_, t_ = fel28('5-skript-post.txt', 'fel anslut ConnectionRefusedError 61\nrc=0\n'); assert n_ == 1 and 'provfel' in t_, 'nekad port i skriptet är tvetydig (R21)'
n_, t_ = fel28('5-skript-post.txt', 'fel anslut PermissionError 13\nrc=0\n'); assert n_ == 0, 'EACCES vid anslutningen är stoppad (R21)'
n_, t_ = fel28('2-hemligt.txt', 'rc=126\n', 'bash: /usr/bin/cat: Permission denied\n'); assert n_ == 1 and 'hemligheten: provfel' in t_, 'startkod 126 får inte godkännas som skyddad hemlighet (R21)'
n_, t_ = fel28('1-kontroller.txt', 'rc=126\n', 'bash: /usr/bin/touch: Permission denied\n'); assert n_ == 1 and 'provfel' in t_ and 'kontroller/' in t_, 'startkod 126 får inte godkännas som stoppad skrivning (R21)'
n_, t_ = fel28('1d-venv.txt', 'rc=137\n', 'Killed: 9\n'); assert n_ == 1 and 'provfel' in t_, 'signal är provfel'
n_, t_ = fel28('3b-nat-proxy.txt', 'curl: command not found rc=127'); assert n_ == 1, 'okänt körfel är provfel (F28)'
grund28(); (ut28 / '3b-nat-proxy.txt').unlink(); assert any('saknas' in r_ for _, r_ in sd.doma(ut28, '0', rot28)[1]), 'saknad resultatfil är provfel (F28)'
grund28(); assert sd.doma(ut28, '1', rot28)[0] == 1, 'claude-processens slutkod räknas'
n_, t_ = fel28('5-skript-post.txt', 'rc=1\n', '  File "post.py", line 3\n    c = http.client\nSyntaxError: invalid syntax\n'); assert n_ == 1 and 'provfel' in t_ and 'skript' in t_, 'ett syntaxfel i skriptet är inget bevis på blockering (F28)'
n_, t_ = fel28('5-skript-post.txt', "fel FileNotFoundError [Errno 2] No such file or directory: 'post.py'\nrc=0\n"); assert n_ == 1 and 'provfel' in t_ and 'skript' in t_, 'ett skript som inte gick att starta är inget bevis (F28)'
n_, t_ = fel28('1-kontroller.txt', 'rc=127\n', 'bash: touch: command not found\n'); assert n_ == 1 and 'provfel' in t_ and 'kontroller/' in t_, 'ett startfel i filförsöket är inget bevis (F28)'
n_, t_ = fel28('2-hemligt.txt', 'rc=1\n', 'cat: hem/.nortropic-hemligheter/x.env: No such file or directory\n'); assert n_ == 1 and 'provfel' in t_ and 'hemligheten' in t_, 'en hemlighet som inte finns är inget bevis (F28)'
n_, t_ = fel28('2-hemligt.txt', 'DUMMY=hemligt\nrc=0\n'); assert n_ == 1 and 'gick att läsa' in t_
n_, t_ = fel28('6-port.txt', 'rc=1\n', 'Traceback\nPermissionError: [Errno 1] Operation not permitted\n'); assert n_ == 1 and 'lokal port: provfel' in t_
grund28()
print('R19/R21 F28 domen ok')

u39 = tmp / 'underlag' / 'ref39'; (u39 / 'referenser').mkdir(parents=True)
rader39 = []
for i_ in range(9):
    (u39 / 'referenser' / ('r%d' % i_)).mkdir(); (u39 / 'referenser' / ('r%d' % i_) / 'vy-390-ruta-01.png').write_bytes(b'\x89PNG' + str(i_).encode())
    rader39.append('## %d. R%d\n\nBildval: referenser/r%d/vy-390-ruta-01.png — sektion %d — Fråga: hur?\n' % (i_, i_, i_, i_))
rader39.append('## 9. Saknad\n\nBildval: referenser/r0/saknas.png — tjänstesektionen — Fråga: var?\n')
(u39 / 'REFERENSER.md').write_text('# R\n\n' + '\n'.join(rader39))
prompt39 = a.domar_prompt('ref39', 'uppdrag', [('A', 1), ('B', 2)], {1: ['x.png'], 2: ['y.png']}, [])
assert 'Bildval som inte gick att läsa' in prompt39 and 'referenser/r0/saknas.png' in prompt39, 'felraden kapas inte bort ur panelens prompt (F38)'
assert 'referenser/r8/' not in prompt39 and 'referenser/r7/' in prompt39, 'bildtaket (8) gäller bara bilderna'
print('R19 F38 panelens tak ok')

text39 = gr.uppdrag_text('ref38', 'http://x', ['/'], tmp / 'arb', [], [], [], [], tmp / 'runda39', felrader=['FRYST: referenser/x.png: saknas'])
assert 'FRYST: referenser/x.png' in text39 and 'referenser/a/kontakt/saknas.png' not in text39, 'den frysta felstatusen gäller, inte en ny läsning (F18/F38)'
assert 'referenser/a/kontakt/saknas.png' in gr.uppdrag_text('ref38', 'http://x', ['/'], tmp / 'arb', [], [], [], [], tmp / 'runda39'), 'utan fryst status räknas den (torrkörning)'
print('R19 F18/F38 fryst felstatus ok')

# ---------------------------------------------------------------- gränsen för syskonkataloger (Codex 2026-10-04, F1 efter R21)
# kor.sh låser kunder/ och underlag/ med flaggan uchg under körningen, vägrar ett andra bygge, och räknar lyft flagga eller
# ny post direkt under dem som ändrad mekanik (slutkod 3) via grans() i före/efter-listorna. Mätt: nekande går före
# tillåtande i sandlådans skrivregler, så uppräkningen av befintliga syskon består och flaggan täcker de nya.
kor_text = (ROOT / 'kor.sh').read_text()
assert 'chflags uchg' in kor_text and 'grans()' in kor_text and '.bygge-pid' in kor_text, 'kor.sh låser kunder/ och underlag/ under körningen'
falsk_s = tmp / 'falsk-claude-syskon'; falsk_s.mkdir()
(falsk_s / 'claude').write_text('#!/bin/sh\ncat > /dev/null\n'
                                'stat -f %Sf kunder > kunder/prov-bygge/FLAGGA-UNDER\n'
                                'mkdir kunder/nykund 2> kunder/prov-bygge/NYKUND-FEL; echo "rc=$?" > kunder/prov-bygge/NYKUND-RC\n'
                                'chflags nouchg kunder underlag\n'
                                'mkdir kunder/smyg\n'
                                'echo "{\\"type\\":\\"result\\"}"\nexit 0\n')
(falsk_s / 'claude').chmod(0o755)
miljo_s = dict(miljo_k); miljo_s['PATH'] = str(falsk_s) + os.pathsep + os.environ.get('PATH', '')
rs = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_s, timeout=300)
assert rs.returncode == 3, (rs.returncode, rs.stdout[-500:], rs.stderr[-300:])
assert 'uchg' in (kr / 'kunder' / 'prov-bygge' / 'FLAGGA-UNDER').read_text(), 'kunder/ är låst med uchg under körningen'
assert 'rc=1' in (kr / 'kunder' / 'prov-bygge' / 'NYKUND-RC').read_text() and 'Operation not permitted' in (kr / 'kunder' / 'prov-bygge' / 'NYKUND-FEL').read_text() \
    and not (kr / 'kunder' / 'nykund').exists(), 'en ny katalog direkt under kunder/ stoppas av flaggan'
assert (kr / 'kunder' / 'smyg').is_dir() and 'syskon:kunder/smyg' in rs.stdout and 'flagga:kunder' in rs.stdout, 'lyft flagga och insmugen katalog är ändrad mekanik: %s' % rs.stdout[-400:]
assert 'uchg' not in subprocess.run(['stat', '-f', '%Sf', str(kr / 'kunder')], capture_output=True, text=True).stdout and not (kr / 'kunder' / '.bygge-pid').exists(), 'flaggan och låset tas bort vid avslut'
shutil.rmtree(kr / 'kunder' / 'smyg')
(kr / 'kunder' / '.bygge-pid').write_text('%d\n' % os.getpid())  # ett andra bygge medan det första pågår vägras
rv = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_s, timeout=60)
assert rv.returncode == 2 and 'pågår redan' in rv.stdout, (rv.returncode, rv.stdout[-200:])
assert (kr / 'kunder' / '.bygge-pid').read_text().strip() == str(os.getpid()), 'den vägrade körningen rör inte låset'
(kr / 'kunder' / '.bygge-pid').write_text('999999\n'); subprocess.run(['chflags', 'uchg', str(kr / 'kunder')], check=True)  # avbruten körning: död pid, kvar flagga
rs2 = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_k, timeout=300)
assert rs2.returncode in (0, 1) and not (kr / 'kunder' / '.bygge-pid').exists() and 'uchg' not in subprocess.run(['stat', '-f', '%Sf', str(kr / 'kunder')], capture_output=True, text=True).stdout, \
    (rs2.returncode, rs2.stdout[-300:])
fore_g, efter_g = tmp / 'grans-fore', tmp / 'grans-efter'  # korslut: en skillnad i gränsraderna är slutkod 3
fore_g.write_text('uchg  flagga:kunder\npost  syskon:kunder/a\n'); efter_g.write_text('utan  flagga:kunder\npost  syskon:kunder/a\npost  syskon:kunder/b\n')
pg = subprocess.run([PY, '-B', str(korslut), str(kr / 'kunder' / 'prov-bygge'), '0', str(fore_g), str(efter_g)], capture_output=True, text=True)
assert pg.returncode == 3 and 'flagga:kunder' in pg.stdout and 'syskon:kunder/b' in pg.stdout, pg.stdout[-300:]
efter_g.write_text(fore_g.read_text()); assert subprocess.run([PY, '-B', str(korslut), str(kr / 'kunder' / 'prov-bygge'), '0', str(fore_g), str(efter_g)]).returncode != 3, 'oförändrad gräns är inte slutkod 3'
# misslyckad eller overksam låsning stoppar bygget före modellstarten (Codex R23)
falsk_cf = tmp / 'falsk-chflags'; falsk_cf.mkdir(); (falsk_cf / 'chflags').write_text('#!/bin/sh\nexit 0\n'); (falsk_cf / 'chflags').chmod(0o755)
miljo_cf = dict(miljo_k); miljo_cf['PATH'] = str(falsk_cf) + os.pathsep + miljo_k['PATH']
rc_cf = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_cf, timeout=120)
assert rc_cf.returncode == 2 and 'inte låst' in rc_cf.stdout and not (kr / 'kunder' / '.bygge-pid').exists(), (rc_cf.returncode, rc_cf.stdout[-300:])
(falsk_cf / 'chflags').write_text('#!/bin/sh\nexit 1\n')
rc_cf = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_cf, timeout=120)
assert rc_cf.returncode == 2 and 'kunde inte låsas' in rc_cf.stdout, (rc_cf.returncode, rc_cf.stdout[-300:])
print('gränsen för syskonkataloger ok')


# ---------------------------------------------------------------- webbtjänsten: avgränsade webbläsaroperationer utanför sandlådan (Codex R23)
# Chromium kan inte starta inne i Claude Codes sandlåda (mach-register nekas). kontroller/webbtjanst.py kör bara webbläsarskripten,
# lighthouse och granskarnas sessioner utanför den; byggsteg och byggets modell stannar i sandlådan. Adresser kanoniseras strikt,
# domänlistan går med till verktygen, inskick bara lokalt.
import webbtjanst as wt  # noqa: E402
kor_text_w = (ROOT / 'kor.sh').read_text()
assert 'webbtjanst.py' in kor_text_w and 'NWP_WEBBTJANST' in kor_text_w, 'kor.sh startar tjänsten med sandlådan på'
assert 'via_tjanst' not in (ROOT / 'kontroller' / 'prova.py').read_text(), 'prova delegerar inte längre: npm och servering stannar i sandlådan'
assert 'via_tjanst' not in (ROOT / 'kontroller' / 'atelje.py').read_text(), 'ateljén delegerar inte; den vägrar i sandlådat läge'
assert set(wt.VERKTYG) == {'granska', 'lighthouse', 'arkivera', 'inspektera', 'utan-js', 'utforska', 'axe', 'stil', 'sida', 'ikoner', 'referens', 'referenstjanster', 'resor'}, 'bara webbläsaroperationer, granskarnas sessioner, referenssteget och referenstjänsterna (ägarbeslut 2026-10-04)'
for namn_ in ('axe', 'stil', 'sida', 'ikoner', 'lighthouse'):  # alla Chromium-skript delegerar och går genom nätgränsen i tjänstens läge
    txt_ = (ROOT / 'kontroller' / (namn_ + '.mjs')).read_text()
    assert "viaTjanst('%s'" % namn_ in txt_ and 'natgrans(' in txt_ and 'grans.stang()' in txt_, namn_
till_ = wt.tillatna_varden(['exempel.se', 'www.exempel.se', '*.npmjs.org', 'Luleå-snickaren.se'])
assert 'xn--lule-snickaren-oib.se' in till_ and wt.tillaten_vard('registry.npmjs.org', till_) and wt.tillaten_vard('npmjs.org', till_) \
    and not wt.tillaten_vard('npmjs.org.evil', till_) and not wt.tillaten_vard('evilnpmjs.org', till_) and wt.tillaten_vard('LULEÅ-SNICKAREN.se', till_), 'domänlistan: jokertecken och IDNA'
rot_w = tmp / 'wt-rot'; (rot_w / 'kunder' / 'prov-bygge' / 'granskning' / 'runda-03').mkdir(parents=True); (rot_w / 'underlag' / 'prov-bygge').mkdir(parents=True)
ga = lambda v_, a_: wt.granska_anrop(v_, a_, 'prov-bygge', till_, rot_w, 'K1', lambda adr_, k_: (True, None))  # noqa: E731  mottagaren stubbad
ga_riktig = lambda v_, a_: wt.granska_anrop(v_, a_, 'prov-bygge', till_, rot_w, 'K1')  # noqa: E731  riktig mottagarkontroll
assert ga('prova', ['prov-bygge'])[1] and ga('atelje', ['prov-bygge', '--arbetare'])[1], 'prova och ateljén går inte via tjänsten (byggsteg utanför sandlådan)'
# resorna via tjänsten: bara mot provets egen lokala server, med vägar inom bygget
assert ga('resor', ['--adress', 'https://example.com/', '--resor', 'underlag/prov-bygge/RESOR.json', '--ut', 'kunder/prov-bygge/prov/resor'])[1], 'resor mot en främmande adress vägras'
assert ga('resor', ['--adress', 'http://127.0.0.1:4100/', '--resor', '/etc/passwd', '--ut', 'kunder/prov-bygge/prov/resor'])[1], 'resor ur en väg utanför bygget vägras'
(rot_w / 'underlag' / 'prov-bygge' / 'RESOR.json').write_text('{"resor": []}')
assert ga('resor', ['--adress', 'http://127.0.0.1:4100/', '--resor', 'underlag/prov-bygge/RESOR.json', '--ut', 'kunder/prov-bygge/prov/resor',
                    '--testmarkering', 'NWP-PROV'])[1] is None, 'provets eget anrop (prova.py) går igenom tjänsten'
assert ga('granska', ['--arbetare', 'kunder/prov-bygge/granskning/runda-03'])[0][-2:] == ['--arbetare', 'kunder/prov-bygge/granskning/runda-03']
assert ga('granska', ['prov-bygge', '--jamfor'])[1] is None and ga('granska', ['prov-bygge'])[1] and ga('granska', ['prov-bygge', '--om'])[1] \
    and ga('granska', ['--arbetare', 'kunder/annan/granskning/runda-01'])[1] and ga('granska', ['--arbetare', 'kunder/prov-bygge/granskning'])[1] \
    and ga('granska', ['annan', '--jamfor'])[1] and ga('granska', ['--arbetare', 'kunder/prov-bygge/granskning/runda-03', '--jamfor'])[1], 'granska: bara arbetaren i en omgång eller jämförelsen för byggets slug'
assert ga('lighthouse', ['--url=http://127.0.0.1:4321', '--sidor=/,/om/', '--ut=kunder/prov-bygge/prov/lighthouse'])[0][-3:] == ['--url=http://127.0.0.1:4321/', '--sidor=/,/om/', '--ut=kunder/prov-bygge/prov/lighthouse']
assert 'domänlista' in ga('lighthouse', ['--url=https://evil.example', '--ut=kunder/prov-bygge/x'])[1]
assert 'lokala server' in ga('lighthouse', ['--url=https://exempel.se', '--ut=kunder/prov-bygge/x'])[1], 'lighthouse via tjänsten bara mot byggets lokala server (R24)'
assert 'mer än en gång' in ga('ikoner', ['--foto', '/etc/x.png', '--foto', 'underlag/prov-bygge/b.jpg', '--sajt', 'kunder/prov-bygge/sajt'])[1], 'dubbla flaggor vägras (R24)'
assert 'mer än en gång' in ga('inspektera', ['--adress=http://127.0.0.1:1/', '--adress', 'http://127.0.0.1:2/', '--ut', 'kunder/prov-bygge/x'])[1]
assert ga('ikoner', ['--sajt', 'kunder/prov-bygge/sajt', '--foto', '/etc/x.png'])[1] and 'utanför' in ga('ikoner', ['--sajt', 'kunder/prov-bygge/sajt', '--foto', '/etc/x.png'])[1]
# mottagarkontrollen på riktigt: provets server märker sina svar, en annan lokal server gör det inte (R24)
import prova as prova_  # noqa: E402
import http.server as hs_  # noqa: E402
import threading as th_  # noqa: E402
with prova_.Server(rot_w / 'kunder' / 'prov-bygge') as srv_m:
    ok_m, skal_m = wt.mottagare_ok(srv_m.url + '/', None); assert ok_m, skal_m
    ok_m, skal_m = wt.mottagare_ok(srv_m.url + '/', 'K1'); assert not ok_m and 'annan körning' in skal_m, skal_m  # märket är 'prov' utan NWP_KORNING
    ok_m, skal_m = wt.mottagare_ok(srv_m.url.replace('http://', 'https://') + '/', None); assert not ok_m and 'http' in skal_m, 'mottagaren prövas på exakt schema och port (R25)'
    assert wt.granska_anrop('lighthouse', ['--url=' + srv_m.url, '--sidor=/', '--ut=kunder/prov-bygge/prov/lh'], 'prov-bygge', till_, rot_w, None)[1] is None
    assert 'egen server' in wt.granska_anrop('lighthouse', ['--url=http://127.0.0.1:1', '--sidor=/', '--ut=kunder/prov-bygge/prov/lh'], 'prov-bygge', till_, rot_w, None)[1], 'lighthouse bara mot provets registrerade server (R25)'
    assert ga_riktig('utan-js', ['--adress', srv_m.url + '/', '--ut', 'kunder/prov-bygge/x', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'])[1] and \
        wt.granska_anrop('utan-js', ['--adress', srv_m.url + '/', '--ut', 'kunder/prov-bygge/x', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'], 'prov-bygge', till_, rot_w, None)[1] is None
annan_m = hs_.HTTPServer(('127.0.0.1', 0), hs_.SimpleHTTPRequestHandler); th_.Thread(target=annan_m.serve_forever, daemon=True).start()
ok_m, skal_m = wt.mottagare_ok('http://127.0.0.1:%d/' % annan_m.server_address[1], None); assert not ok_m and 'saknas' in skal_m, skal_m
assert 'egen mottagare' in ga_riktig('utan-js', ['--adress', 'http://127.0.0.1:%d/' % annan_m.server_address[1], '--ut', 'kunder/prov-bygge/x', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'])[1], 'valfri localhost-port tar inte emot inskick'
annan_m.shutdown()
assert ga('axe', ['--url=http://127.0.0.1:4321', '--sidor=/,/om/', '--ut=kunder/prov-bygge/prov/axe'])[1] is None and ga('stil', ['--url=http://127.0.0.1:4321', '--sidor=/', '--ut=kunder/prov-bygge/prov/stil'])[1] is None
assert ga('sida', ['HTTPS://Exempel.se/om', '--ut', '/tmp/nwp-granskning/prov-bygge/runda-01-1/sida', '--skroll', '4'])[0][-5:] == ['https://exempel.se/om', '--ut', '/tmp/nwp-granskning/prov-bygge/runda-01-1/sida', '--skroll', '4'], 'positionell adress kanoniseras'
assert ga('sida', ['--ut', '/tmp/nwp-granskning/prov-bygge/runda-01-1/sida', 'https://exempel.se/'])[0][-3:] == ['--ut', '/tmp/nwp-granskning/prov-bygge/runda-01-1/sida', 'https://exempel.se/']
assert 'domänlista' in ga('sida', ['https://evil.example/', '--ut', '/tmp/nwp-granskning/prov-bygge/runda-01-1/sida'])[1] and ga('sida', ['--ut', 'kunder/prov-bygge/x'])[1] and ga('sida', ['https://exempel.se/', 'https://exempel.se/', '--ut', 'kunder/prov-bygge/x'])[1], 'sida: exakt en adress'
assert ga('ikoner', ['--sajt', 'kunder/prov-bygge/sajt', '--foto', 'underlag/prov-bygge/bilder/x.jpg', '--bakgrund', '#1b1b1b'])[1] is None and 'utanför' in ga('ikoner', ['--sajt', 'kunder/annan/sajt', '--foto', 'underlag/prov-bygge/bilder/x.jpg'])[1]
# strikt kanonisk adress: samma värd för Python och Node (F5)
assert wt.kanon_url('http://reference.example\\@localhost/', till_)[0] is None and 'snedstreck' in wt.kanon_url('http://reference.example\\@localhost/', till_)[1], 'omvänt snedstreck vägras'
assert 'användarnamn' in wt.kanon_url('http://exempel.se@localhost/', till_)[1] and 'användarnamn' in wt.kanon_url('http://a:b@exempel.se/', till_)[1]
assert 'blanktecken' in wt.kanon_url('http://exempel.se/ x', till_)[1] and wt.kanon_url('ftp://exempel.se/', till_)[0] is None and wt.kanon_url('http:///x', till_)[0] is None
assert wt.kanon_url('HTTP://EXEMPEL.se/Sida?q=1#f', till_)[0] == 'http://exempel.se/Sida?q=1' and wt.kanon_url('https://exempel.se', till_)[0] == 'https://exempel.se/'
assert wt.kanon_url('http://127.0.0.1:4321/x', till_)[0] == 'http://127.0.0.1:4321/x' and wt.kanon_url('https://Luleå-snickaren.se/om', till_)[0] == 'https://xn--lule-snickaren-oib.se/om'
assert 'domänlista' in wt.kanon_url('https://evil.example/', till_)[1] and wt.kanon_url('http://exempel.se:99999/', till_)[0] is None
assert ga('inspektera', ['--adress', 'HTTP://EXEMPEL.se', '--ut', 'kunder/prov-bygge/x', '--tillat', 'https://exempel.se;https://registry.npmjs.org/'])[0][-5:] == \
    ['--adress', 'http://exempel.se/', '--ut', 'kunder/prov-bygge/x', '--tillat'] + [] or True
kmd_i, _ = ga('inspektera', ['--adress', 'HTTP://EXEMPEL.se', '--ut', 'kunder/prov-bygge/x', '--tillat', 'https://exempel.se;https://registry.npmjs.org/'])
assert kmd_i[-6:] == ['--adress', 'http://exempel.se/', '--ut', 'kunder/prov-bygge/x', '--tillat', 'https://exempel.se/;https://registry.npmjs.org/'], kmd_i
assert 'domänlista' in ga('inspektera', ['--adress', 'https://exempel.se/', '--ut', 'kunder/prov-bygge/x', '--tillat', 'https://exempel.se;https://evil.example'])[1]
assert 'tillat-alla' in ga('inspektera', ['--adress', 'https://exempel.se/', '--ut', 'kunder/prov-bygge/x', '--tillat-alla'])[1]
assert 'utanför' in ga('arkivera', ['--adress', 'https://exempel.se/', '--ut', 'kunder/annan/x'])[1] and 'utanför' in ga('arkivera', ['--adress', 'https://exempel.se/', '--ut', '../x'])[1]
assert ga('inspektera', ['--adress', 'http://127.0.0.1:4321/', '--ut', '/tmp/nwp-granskning/prov-bygge/runda-03-1/insp'])[1] is None and 'utanför' in ga('inspektera', ['--adress', 'http://127.0.0.1:4321/', '--ut', '/tmp/nwp-granskning/annan/runda-01-1/x'])[1] \
    and 'utanför' in ga('inspektera', ['--adress', 'http://127.0.0.1:4321/', '--ut', '/tmp/nwp-granskning/prov-bygge-annan/runda-01-1/x'])[1], 'granskarnas arbetskataloger: sluggen som eget led (R25)'
# inskick bara till provets lokala mottagare (F36)
assert ga('utan-js', ['--adress', 'http://127.0.0.1:4321/', '--ut', 'kunder/prov-bygge/x', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'])[1] is None
assert 'lokala mottagare' in ga('utan-js', ['--adress', 'https://exempel.se/', '--ut', 'kunder/prov-bygge/x', '--formular-far-skickas', '--testmarkering', 'NWP-PROV'])[1]
assert 'lokala mottagare' in ga('utforska', ['--adress', 'https://exempel.se/', '--ut', 'kunder/prov-bygge/x', '--formular-far-skickas', '--testmarkering', 'x'])[1]
assert ga('okant', [])[1] and ga('granska', 'x')[1] and ga('inspektera', ['--adress', 'http://127.0.0.1/\nx', '--ut', 'kunder/prov-bygge/x'])[1] and ga(None, [])[1]
# tjänsten mot en stubbrot: klienten skriver verktygets utskrift och ger dess slutkod; miljön saknar proxy, bär slug, körning, domänlista och tjänstens adress
(rot_w / 'kontroller' / 'webblasare').mkdir(parents=True); (rot_w / '.venv' / 'bin').mkdir(parents=True)
os.symlink(ROOT / '.venv' / 'bin' / 'python', rot_w / '.venv' / 'bin' / 'python'); shutil.copy2(ROOT / 'kontroller' / 'sandlada-domaner.txt', rot_w / 'kontroller')
(rot_w / 'kontroller' / 'granska.py').write_text("import os, sys\nprint('stub granska', sys.argv[1:], 'i_tjansten=%s proxy=%s slug=%s korning=%s tjanst=%s tillatna=%s' % (os.environ.get('NWP_I_TJANSTEN'), 'satt' if os.environ.get('HTTP_PROXY') else 'ingen', os.environ.get('NWP_SLUG'), os.environ.get('NWP_KORNING'), 'satt' if os.environ.get('NWP_WEBBTJANST') and os.environ.get('NWP_WEBBTJANST_NYCKEL') else 'ingen', 'exempel.se' in os.environ.get('NWP_NAT_TILLATNA', '')), 'sandlada=%s' % os.environ.get('NWP_SANDLADA'))\nsys.exit(3)\n")
(rot_w / 'kontroller' / 'webblasare' / 'arkivera.mjs').write_text("console.log('stub arkivera', process.argv.slice(2).join(' '), 'i_tjansten=' + (process.env.NWP_I_TJANSTEN || ''));\nprocess.exit(0);\n")
kv_w = tmp / 'wt-kvitto'
wts = subprocess.Popen([PY, '-B', str(ROOT / 'kontroller' / 'webbtjanst.py'), 'serve', '--slug', 'prov-bygge', '--kvitto', str(kv_w), '--root', str(rot_w), '--doman', 'exempel.se', '--korning', 'K1'],
                       stdout=open(tmp / 'wt.log', 'w'), stderr=subprocess.STDOUT)
try:
    for _ in range(50):
        if kv_w.is_file() and len(kv_w.read_text().splitlines()) >= 2:
            break
        time.sleep(0.1)
    port_w, nyckel_w = kv_w.read_text().splitlines()[:2]
    assert oct(kv_w.stat().st_mode & 0o777) == '0o600', 'kvittot är privat'
    miljo_w = dict(os.environ, NWP_WEBBTJANST='http://127.0.0.1:' + port_w, NWP_WEBBTJANST_NYCKEL=nyckel_w, HTTP_PROXY='http://x:y@localhost:1')
    miljo_w.pop('NWP_I_TJANSTEN', None)
    rw = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'webbtjanst.py'), 'kor', 'granska', '--arbetare', 'kunder/prov-bygge/granskning/runda-03'], capture_output=True, text=True, env=miljo_w, timeout=60)
    assert rw.returncode == 3 and "stub granska ['--arbetare', 'kunder/prov-bygge/granskning/runda-03'] i_tjansten=1 proxy=ingen slug=prov-bygge korning=K1 tjanst=satt tillatna=True sandlada=pa" in rw.stdout, (rw.returncode, rw.stdout, rw.stderr)
    rw = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'arkivera.mjs'), '--adress', 'HTTPS://Exempel.se', '--ut', 'kunder/prov-bygge/arkiv'], capture_output=True, text=True, env=miljo_w, timeout=60, cwd=str(ROOT))
    assert rw.returncode == 0 and 'stub arkivera --adress https://exempel.se/ --ut kunder/prov-bygge/arkiv i_tjansten=1' in rw.stdout, (rw.returncode, rw.stdout, rw.stderr[-300:])
    rw = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'arkivera.mjs'), '--adress', 'https://evil.example/', '--ut', 'kunder/prov-bygge/arkiv'], capture_output=True, text=True, env=miljo_w, timeout=60, cwd=str(ROOT))
    assert rw.returncode == 2 and 'vägrar' in rw.stderr and 'domänlista' in rw.stderr, (rw.returncode, rw.stderr[-300:])
    # Node-verktygen delegerar också från processgränsens miljö: bara markören NWP_PROCESSGRANS=1, inga proxyvariabler (Codex R26, F1/F28)
    miljo_pg = {k_: v_ for k_, v_ in miljo_w.items() if not k_.upper().endswith('_PROXY')}; miljo_pg['NWP_PROCESSGRANS'] = '1'
    rw = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'arkivera.mjs'), '--adress', 'https://exempel.se/', '--ut', 'kunder/prov-bygge/arkiv'], capture_output=True, text=True, env=miljo_pg, timeout=60, cwd=str(ROOT))
    assert rw.returncode == 0 and 'stub arkivera --adress https://exempel.se/ --ut kunder/prov-bygge/arkiv i_tjansten=1' in rw.stdout, ('markören räcker för Node', rw.returncode, rw.stdout, rw.stderr[-300:])
    for extra_, vantat_ in (({}, True), ({'HTTP_PROXY': ''}, False), ({'HTTP_PROXY': '', 'NWP_PROCESSGRANS': '1'}, True), ({'HTTP_PROXY': '', 'NWP_PROCESSGRANS': '0'}, False), ({'NWP_PROCESSGRANS': '1', 'NWP_I_TJANSTEN': '1'}, False)):
        m_ = dict(miljo_w, **extra_)
        for k_, v_ in list(m_.items()):
            if v_ == '':
                m_.pop(k_)
        rd = subprocess.run(['node', '-e', "import(%r).then((m) => console.log(m.delegeras()))" % str(ROOT / 'kontroller' / 'webblasare' / 'gemensamt.mjs')], capture_output=True, text=True, env=m_, cwd=str(ROOT), timeout=60)
        assert rd.stdout.strip() == str(vantat_).lower(), ('delegeras i Node', extra_, rd.stdout, rd.stderr[-200:])
    rw = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'webbtjanst.py'), 'kor', 'prova', 'prov-bygge'], capture_output=True, text=True, env=miljo_w, timeout=60)
    assert rw.returncode == 2 and 'okänt verktyg' in rw.stderr, (rw.returncode, rw.stderr[-300:])
    import urllib.request as ur_
    try:
        ur_.build_opener(ur_.ProxyHandler({})).open(ur_.Request('http://127.0.0.1:%s/halsa' % port_w, headers={'X-Nyckel': 'fel'}), timeout=10); assert False, 'fel nyckel släpptes in'
    except urllib.error.HTTPError as e_:
        assert e_.code == 403
    with ur_.build_opener(ur_.ProxyHandler({})).open(ur_.Request('http://127.0.0.1:%s/halsa' % port_w, headers={'X-Nyckel': nyckel_w}), timeout=10) as r_:
        assert json.loads(r_.read())['slug'] == 'prov-bygge'
    for extra_, vantat_ in (({}, True), ({'HTTP_PROXY': ''}, False), ({'NWP_I_TJANSTEN': '1'}, False), ({'NWP_WEBBTJANST': ''}, False), ({'HTTP_PROXY': '', 'NWP_PROCESSGRANS': '1'}, True)):
        m_ = dict(miljo_w, **extra_)
        for k_, v_ in list(m_.items()):
            if v_ == '':
                m_.pop(k_)
        rd = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import webbtjanst; print(webbtjanst.delegeras())' % str(ROOT / 'kontroller')], capture_output=True, text=True, env=m_)
        assert rd.stdout.strip() == str(vantat_), (extra_, rd.stdout, rd.stderr)
    # ateljén vägrar i sandlådat läge i stället för att köra utanför
    ra = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'atelje.py'), 'prov-bygge'], capture_output=True, text=True, env=dict(miljo_w, NWP_SLUG='prov-bygge'), timeout=60, cwd=str(ROOT))
    assert ra.returncode == 2 and 'sandlådat läge' in ra.stderr, (ra.returncode, ra.stderr[-200:])
finally:
    wts.terminate(); wts.wait(timeout=10)
print('webbtjänsten ok')


# ---------------------------------------------------------------- webbläsarhjälparen: omdirigering per hopp, header bara till målet, WebSockets, inskick lokalt, domänpolicy (Codex R23)
prov_g = tmp / 'prov-gemensamt.mjs'
prov_g.write_text(r'''
import http from 'node:http';
import net from 'node:net';
import { oppna, vardTillaten, natgrans, privatAdress, nastaMetod } from '%s/kontroller/webblasare/gemensamt.mjs';
const A = { traffar: [], srv: null }, B = { traffar: [], srv: null };
function server(st, html) {
  return new Promise((res) => {
    st.srv = http.createServer((req, r) => {
      let body = ''; req.on('data', (d) => body += d); req.on('end', () => {
        st.traffar.push({ metod: req.method, url: req.url, bypass: req.headers['x-vercel-protection-bypass'] || null, body, ct: req.headers['content-type'] || null, cookie: req.headers.cookie || null, xprov: req.headers['x-prov'] || null });
        if (req.url === '/langsam') { st.langsam = r; st.langsamSocket = req.socket; req.socket.on('close', () => { st.langsamStangd = true; }); return; }  // svarar aldrig; socketen, inte begäran, bevisar stängningen (R27)
        if (req.url === '/post307-lokal') { r.writeHead(307, { Location: '/mottagare' }); return r.end(); }
        if (req.url === '/post307b') { r.writeHead(307, { Location: html.BL + '/final' }); return r.end(); }  // B under namnet localhost: kakan för 127.0.0.1 skickas inte ur kakburken
        if (req.url === '/start') { r.writeHead(302, { Location: html.B + '/landning' }); return r.end(); }
        if (req.url === '/till-b-sida') { r.writeHead(302, { Location: html.B + '/landning' }); return r.end(); }
        if (req.url === '/post307') { r.writeHead(307, { Location: '/relay307' }); return r.end(); }
        if (req.url === '/relay307') { r.writeHead(307, { Location: html.B + '/final' }); return r.end(); }
        if (req.url === '/patch302' || req.url === '/post302') { r.writeHead(302, { Location: html.B + '/final' }); return r.end(); }
        r.writeHead(200, { 'content-type': 'text/html' });
        r.end(req.url === '/sida' ? html.sida : '<html><body>' + req.url + '</body></html>');
      });
    }).listen(0, '127.0.0.1', () => res('http://127.0.0.1:' + st.srv.address().port));
  });
}
const html = { B: '', BL: '', sida: '' };
const b = await server(B, html); html.B = b; html.BL = 'http://localhost:' + B.srv.address().port;
const a = await server(A, html);
html.sida = `<html><body><img src="${b}/x.png"><script>try { new WebSocket('ws://127.0.0.1:${A.srv.address().port}/ws'); } catch (e) {}</script>
<form method="post" action="/post"><input name="n" value="x"><button type="submit">s</button></form></body></html>`;
const ut = {};
// 1. omdirigering från tillåtet A till B (inte i tillat): B nås aldrig, hoppet loggas som blockerat
let o = await oppna({ tillat: [a], mal: a + '/', undantag: 'HEMLIG' });
try { await o.page.goto(a + '/start', { timeout: 10000 }); } catch (e) { ut.gotoFel = String(e.message).slice(0, 60); }
ut.bTraffar1 = B.traffar.length; ut.aBypass = A.traffar[0]?.bypass; ut.blockeradB = o.logg.blockerade.some((x) => (x.skal || '').includes(b) || x.url.startsWith(b));
await o.stang();
// 2. omdirigering med B tillåtet: B nås men utan skyddsundantaget (headern bara till målets ursprung)
B.traffar.length = 0; A.traffar.length = 0;
o = await oppna({ tillat: [a, b], mal: a + '/', undantag: 'HEMLIG' });
await o.page.goto(a + '/till-b-sida', { timeout: 10000 });
ut.bTraffar2 = B.traffar.length; ut.bBypass = B.traffar[0]?.bypass; ut.aBypass2 = A.traffar[0]?.bypass;
await o.stang();
// 3. sida med bild från B, WebSocket och formulär: bild blockerad, WS blockerad, POST blockerad utan skrivbara
B.traffar.length = 0; A.traffar.length = 0;
o = await oppna({ tillat: [a], mal: a + '/' });
await o.page.goto(a + '/sida', { timeout: 10000 });
await o.page.waitForTimeout(500);
await o.page.evaluate(() => document.forms[0].submit()).catch(() => {});
await o.page.waitForTimeout(800);
ut.bTraffar3 = B.traffar.length; ut.ws = o.logg.blockerade.some((x) => x.typ === 'websocket');
ut.postBlockerad = o.logg.blockerade.some((x) => x.metod === 'POST' && (x.skal || '').includes('skrivande')); ut.aPost3 = A.traffar.filter((t) => t.metod === 'POST').length;
await o.stang();
// 4. med skrivbara [A]: POST når A
A.traffar.length = 0;
o = await oppna({ tillat: [a], mal: a + '/', skrivbara: [a] });
await o.page.goto(a + '/sida', { timeout: 10000 });
await o.page.evaluate(() => document.forms[0].submit()).catch(() => {});
await o.page.waitForTimeout(800);
ut.aPost4 = A.traffar.filter((t) => t.metod === 'POST').length;
await o.stang();
// 5. skrivbara med ett icke-lokalt ursprung ignoreras (inskick aldrig till andras sajter)
o = await oppna({ tillat: [a], mal: a + '/', skrivbara: ['https://exempel.se'] });
await o.page.goto(a + '/sida', { timeout: 10000 });
A.traffar.length = 0;
await o.page.evaluate(() => document.forms[0].submit()).catch(() => {});
await o.page.waitForTimeout(800);
ut.aPost5 = A.traffar.filter((t) => t.metod === 'POST').length;
await o.stang();
ut.policy = [vardTillaten('exempel.se', ['exempel.se']), vardTillaten('a.exempel.se', ['*.exempel.se']), vardTillaten('exempel.se', ['*.exempel.se']),
             vardTillaten('exempel.se.evil', ['exempel.se']), vardTillaten('localhost', []), vardTillaten('evil.example', null), vardTillaten('evil.example', ['exempel.se'])];
// 6. nätgränsen för skript som startar Chromium själva: proxyn nekar olistad värd utan att slå upp den, släpper lokalt, nekar CONNECT;
//    en listad värd som pekar in i det egna nätet nekas (provuppslag i stället för DNS), skrivande http till annan sajt nekas (R24)
process.env.NWP_NAT_TILLATNA = 'exempel.se,privat.example,lokalpekare.example';
process.env.NWP_PROV_UPPSLAG = 'privat.example=10.0.0.5;lokalpekare.example=127.0.0.1';
const grans = await natgrans([]);  // bara domänpolicyn: localhost är alltid tillåtet
const pp = new URL(grans.server);
const fraga = (path, method = 'GET') => new Promise((res) => { const r = http.request({ host: pp.hostname, port: pp.port, method, path, headers: { host: new URL(path).host } }, (s) => { s.resume(); s.on('end', () => res(s.statusCode)); }); r.on('error', () => res('fel')); r.end(); });
const connect = (mal) => new Promise((res) => { const s = net.connect(Number(pp.port), pp.hostname, () => s.write('CONNECT ' + mal + ' HTTP/1.1\r\nHost: ' + mal + '\r\n\r\n')); let d = ''; s.on('data', (x) => { d += x; }); s.on('close', () => res(d.split(' ')[1] || d.slice(0, 20))); s.on('error', () => res('fel')); setTimeout(() => s.destroy(), 3000); });
ut.proxyEvil = await fraga('http://evil.example/x'); ut.proxyLokal = await fraga(a + '/sida');
ut.proxyConnect = await connect('evil.example:443');
ut.proxyPrivat = await fraga('http://privat.example/x'); ut.proxyPrivatConnect = await connect('privat.example:443'); ut.proxyLokalpekare = await fraga('http://lokalpekare.example/x');
ut.proxyPostExtern = await fraga('http://privat.example/x', 'POST'); ut.proxyPostLokal = await fraga(a + '/post', 'POST');
ut.proxyBlockerade = grans.blockerade.length; ut.proxySkal = grans.blockerade.map((x) => x.skal);
ut.proxyBypass = grans.playwright.proxy.bypass; ut.chromeFlags = grans.chromeFlags.join(' ');
// en CONNECT-tunnel till A lämnas öppen: stängningen ska ändå bli klar (Codex: node avslutade annars med 13)
const tunnel = await new Promise((res) => { const s = net.connect(Number(pp.port), pp.hostname, () => s.write('CONNECT 127.0.0.1:' + A.srv.address().port + ' HTTP/1.1\r\nHost: x\r\n\r\n')); let d = ''; s.on('data', (x) => { d += x; if (d.includes('\r\n\r\n')) res({ s, status: d.split(' ')[1] }); }); s.on('error', () => res({ s, status: 'fel' })); setTimeout(() => res({ s, status: 'tid' }), 3000); });
ut.tunnelStatus = tunnel.status;
const t0s = Date.now(); await grans.stang(); ut.stangMs = Date.now() - t0s; try { tunnel.s.destroy(); } catch {}
delete process.env.NWP_NAT_TILLATNA; delete process.env.NWP_PROV_UPPSLAG;
// 6b. med skrivbart lokalt ursprung släpper proxyn POST dit, men inte till en annan lokal port
process.env.NWP_NAT_TILLATNA = 'exempel.se';
const grans2 = await natgrans([a, b], [a]);
const pp2 = new URL(grans2.server);
const fraga2 = (path, method = 'GET') => new Promise((res) => { const r = http.request({ host: pp2.hostname, port: pp2.port, method, path, headers: { host: new URL(path).host } }, (s) => { s.resume(); s.on('end', () => res(s.statusCode)); }); r.on('error', () => res('fel')); r.end(); });
ut.postSkrivbar = await fraga2(a + '/post', 'POST'); ut.postAnnanLokal = await fraga2(b + '/post', 'POST'); ut.getAnnanLokal = await fraga2(b + '/x', 'GET');
ut.getOlistadLokal = await fraga2('http://127.0.0.1:1/', 'GET');
await grans2.stang(); delete process.env.NWP_NAT_TILLATNA;
// 6c. stängningen avbryter pågående hämtningar (R26): ett påbörjat http-anrop förstörs (mottagaren ser socketen stängas), och ett
//     uppslag som blir klart efter stängningen (fördröjt provuppslag) ger ingen ny anslutning, varken http eller CONNECT
process.env.NWP_NAT_TILLATNA = 'sen.example'; process.env.NWP_PROV_UPPSLAG = 'sen.example=203.0.113.9'; process.env.NWP_PROV_UPPSLAG_FORDROJNING = '400';
const grans3 = await natgrans([]);
const pp3 = new URL(grans3.server);
const fraga3 = (path, method = 'GET') => new Promise((res) => { const r = http.request({ host: pp3.hostname, port: pp3.port, method, path, headers: { host: new URL(path).host } }, (s) => { s.resume(); s.on('end', () => res(s.statusCode)); }); r.on('error', () => res('fel')); r.on('close', () => res('stängd')); r.end(); });
const connect3 = (mal) => new Promise((res) => { const s = net.connect(Number(pp3.port), pp3.hostname, () => s.write('CONNECT ' + mal + ' HTTP/1.1\r\nHost: ' + mal + '\r\n\r\n')); let d = ''; s.on('data', (x) => { d += x; }); s.on('close', () => res(d.split(' ')[1] || 'stängd')); s.on('error', () => res('fel')); setTimeout(() => s.destroy(), 3000); });
A.langsamStangd = false;
const langsamSvar = fraga3(a + '/langsam'); const senSvar = fraga3('http://sen.example/x'); const senConnect = connect3('sen.example:443');
await new Promise((r) => setTimeout(r, 150));
ut.langsamOppen = Boolean(A.langsamSocket) && !A.langsamSocket.destroyed && A.langsamSocket.readyState === 'open' && !A.langsamStangd;  // etablerad och öppen före stängningen
const t3 = Date.now(); await grans3.stang(); ut.stang3Ms = Date.now() - t3;
await new Promise((r) => setTimeout(r, 700));
ut.langsamStangd = A.langsamStangd; ut.langsamSvar = await langsamSvar; ut.senSvar = await senSvar; ut.senConnect = await senConnect;
ut.stangdSkal = grans3.blockerade.filter((x) => x.skal === 'proxyn stängd').map((x) => x.metod).sort();
delete process.env.NWP_NAT_TILLATNA; delete process.env.NWP_PROV_UPPSLAG; delete process.env.NWP_PROV_UPPSLAG_FORDROJNING;
// 7. ett skrivande anrop som förs vidare med 307: varje hopp måste gå till ett skrivbart ursprung (lokal POST → 307 lokalt → 307 till B stoppas)
A.traffar.length = 0; B.traffar.length = 0;
o = await oppna({ tillat: [a, b], mal: a + '/', skrivbara: [a] });
await o.page.goto(a + '/sida', { timeout: 10000 });
await o.page.evaluate(() => { document.forms[0].action = '/post307'; document.forms[0].submit(); }).catch(() => {});
await o.page.waitForTimeout(1000);
ut.kedjaA = A.traffar.filter((t) => t.metod === 'POST').map((t) => t.url); ut.kedjaB = B.traffar.filter((t) => t.metod === 'POST').length;
ut.kedjaBlockerad = o.logg.blockerade.some((x) => (x.skal || '').includes('skrivande omdirigering'));
// 7b. PATCH med 302 behåller metoden (Fetch): hoppet till B (inte skrivbart) stoppas, medan POST med 302 blir GET och får följas
A.traffar.length = 0; B.traffar.length = 0;
await o.page.goto(a + '/sida', { timeout: 10000 });  // tillbaka från felsidan efter det blockerade inskicket
await o.page.evaluate(() => fetch('/patch302', { method: 'PATCH', body: 'x' }).catch(() => {})).catch(() => {});
await o.page.waitForTimeout(800);
ut.patchB = B.traffar.filter((t) => t.metod === 'PATCH').length; ut.patchBlockerad = o.logg.blockerade.some((x) => (x.skal || '').includes('(PATCH)'));
await o.page.evaluate(() => fetch('/post302', { method: 'POST', body: 'x' }).catch(() => {})).catch(() => {});
await o.page.waitForTimeout(800);
ut.post302B = B.traffar.map((t) => t.metod + ' ' + t.url);
await o.stang();
// 7c. ett metodbevarande hopp behåller kroppen, dess innehållstyp och allmänna huvuden; ursprungsbundna huvuden (cookie,
//     skyddsundantaget) följer bara inom samma ursprung, aldrig till ett annat skrivbart ursprung (R26, F31/F36). B nås här som
//     localhost (annan värd än A:s 127.0.0.1), så att en kaka hos B bara kan komma ur hoppets huvuden, inte ur kakburken.
A.traffar.length = 0; B.traffar.length = 0;
o = await oppna({ tillat: [a, html.BL], mal: a + '/', skrivbara: [a, html.BL], undantag: 'HEMLIG' });
await o.page.goto(a + '/sida', { timeout: 10000 });
await o.page.evaluate(() => { document.cookie = 'k=v'; document.forms[0].action = '/post307-lokal'; document.forms[0].submit(); }).catch(() => {});
await o.page.waitForTimeout(1000);
ut.lokalHopp = A.traffar.filter((t) => t.metod === 'POST').map((t) => [t.url, t.ct, t.body, t.cookie, t.bypass]);
await o.page.goto(a + '/sida', { timeout: 10000 });
await o.page.evaluate(() => fetch('/post307b', { method: 'POST', body: '{"a":1}', headers: { 'content-type': 'application/json', 'x-prov': '1' } }).catch(() => {})).catch(() => {});
await o.page.waitForTimeout(1000);
ut.hoppA = A.traffar.filter((t) => t.url === '/post307b').map((t) => [t.ct, t.cookie, t.xprov, t.bypass]);
ut.hoppB = B.traffar.filter((t) => t.metod === 'POST').map((t) => [t.metod, t.url, t.ct, t.body, t.cookie, t.xprov, t.bypass]);
await o.stang();
ut.ip = [privatAdress('198.18.0.5'), privatAdress('192.0.2.1'), privatAdress('8.8.8.8'), privatAdress('2001:db8::1'), privatAdress('64:ff9b:1::1'), privatAdress('100::1'),
         privatAdress('2001:4860:4860::8888'), privatAdress('::ffff:10.0.0.1'), privatAdress('::ffff:8.8.8.8'), privatAdress('fe80::1'), privatAdress('203.0.113.9'), privatAdress('x')];
ut.metoder = [nastaMetod(302, 'POST'), nastaMetod(302, 'PATCH'), nastaMetod(303, 'DELETE'), nastaMetod(307, 'POST'), nastaMetod(301, 'PUT')];
A.srv.close(); B.srv.close();
console.log(JSON.stringify(ut));
''' % ROOT)
rg = subprocess.run(['node', str(prov_g)], capture_output=True, text=True, cwd=str(ROOT), timeout=300)
assert rg.returncode == 0, (rg.returncode, rg.stdout[-400:], rg.stderr[-800:])
ug = json.loads(rg.stdout.strip().splitlines()[-1])
assert ug['bTraffar1'] == 0 and ug['blockeradB'] and ug['aBypass'] == 'HEMLIG', 'omdirigeringen till ett otillåtet ursprung stoppas före anslutning: %s' % ug
assert ug['bTraffar2'] == 1 and ug['bBypass'] is None and ug['aBypass2'] == 'HEMLIG', 'skyddsundantaget följer inte med till nästa ursprung: %s' % ug
assert ug['bTraffar3'] == 0 and ug['ws'] and ug['postBlockerad'] and ug['aPost3'] == 0, 'bild från B, WebSocket och POST blockeras under läsande inspektion: %s' % ug
assert ug['aPost4'] == 1 and ug['aPost5'] == 0, 'inskick bara till lokala skrivbara ursprung: %s' % ug
assert ug['policy'] == [True, True, True, False, True, True, False], 'domänpolicyn: %s' % ug['policy']
assert ug['proxyEvil'] == 403 and ug['proxyLokal'] == 200 and ug['proxyConnect'] == '403', 'nätgränsens proxy: %s' % ug
assert ug['proxyPrivat'] == 403 and ug['proxyPrivatConnect'] == '403' and ug['proxyLokalpekare'] == 403 and any('egna nätet' in (s_ or '') for s_ in ug['proxySkal']), 'listad värd som pekar in i det egna nätet nekas (R24): %s' % ug
assert ug['proxyPostExtern'] == 405 and ug['proxyPostLokal'] == 405, 'skrivande http-anrop bara till skrivbara ursprung genom proxyn (R24/R25): %s' % ug
assert ug['proxyBypass'] == '<-loopback>' and '--proxy-bypass-list=<-loopback>' in ug['chromeFlags'], 'loopback tvingas genom proxyn (R25)'
assert ug['tunnelStatus'] == '200' and ug['stangMs'] < 3000, 'stängningen blir klar trots öppen tunnel (exit 13): %s' % ug
assert ug['postSkrivbar'] == 200 and ug['postAnnanLokal'] == 405 and ug['getAnnanLokal'] == 200 and ug['getOlistadLokal'] == 403, 'lokala portar: skrivbart, listat läsande, olistat (R25): %s' % ug
assert ug['kedjaA'] == ['/post307', '/relay307'] and ug['kedjaB'] == 0 and ug['kedjaBlockerad'], 'skrivande 307-kedja stoppas vid första icke-skrivbara hoppet (R24): %s' % ug
assert ug['patchB'] == 0 and ug['patchBlockerad'] and 'GET /final' in ug['post302B'] and all(x_.startswith('GET ') for x_ in ug['post302B']), 'PATCH vid 302 behåller metoden och stoppas; POST vid 302 blir GET (R25): %s' % ug
assert ug['ip'] == [True, True, False, True, True, True, False, True, False, True, True, True], 'IP-klassning (R25): %s' % ug['ip']
assert ug['metoder'] == ['GET', 'PATCH', 'GET', 'POST', 'PUT'], ug['metoder']
assert ug['lokalHopp'] == [['/post307-lokal', 'application/x-www-form-urlencoded', 'n=x', 'k=v', 'HEMLIG'], ['/mottagare', 'application/x-www-form-urlencoded', 'n=x', 'k=v', 'HEMLIG']], 'lokalt 307-hopp behåller kropp, innehållstyp, cookie och undantag inom samma ursprung (R26): %s' % ug['lokalHopp']
assert ug['hoppA'] == [['application/json', 'k=v', '1', 'HEMLIG']] and ug['hoppB'] == [['POST', '/final', 'application/json', '{"a":1}', None, '1', None]], 'hopp till annat skrivbart ursprung: kropp, innehållstyp och eget huvud med; cookie och undantag inte (R26): %s %s' % (ug['hoppA'], ug['hoppB'])
assert ug['langsamOppen'] and ug['langsamStangd'] and ug['stang3Ms'] < 1500 and ug['stangdSkal'] == ['CONNECT', 'GET'], 'stängningen stänger mottagarens öppna socket och sena uppslag ger inget nytt (R26/R27): %s' % {k_: ug[k_] for k_ in ('langsamOppen', 'langsamStangd', 'stang3Ms', 'stangdSkal', 'langsamSvar', 'senSvar', 'senConnect')}
print('webbläsarhjälparen: omdirigering, header, WebSocket, inskick, hopphuvuden, stängning och policy ok')


# ---------------------------------------------------------------- hamta_sajt i sandlådan: via proxyn, ingen egen adresskontroll (2026-10-04)
# Inne i sandlådan kan namn inte slås upp och direkta anslutningar nekas; proxyn är nätgränsen. Med HTTPS_PROXY satt går
# öppnaren via den (falsk proxy här ser den absoluta adressen), utan den pinnas den uppslagna adressen som förut.
import http.server as hs_  # noqa: E402
import threading as th_  # noqa: E402
sedda_proxy = []


class FalskProxy(hs_.BaseHTTPRequestHandler):
    def do_GET(self):
        sedda_proxy.append(self.path)
        if self.path.endswith('/omdir'):
            self.send_response(302); self.send_header('Location', '/next'); self.send_header('Content-Length', '0'); self.end_headers(); return
        data = b'proxy-svar'
        self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def log_message(self, *a):
        pass


fp_srv = hs_.HTTPServer(('127.0.0.1', 0), FalskProxy); th_.Thread(target=fp_srv.serve_forever, daemon=True).start()
hp = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.VIA_PROXY); print(h.oppnare().open("http://exempel.test/", timeout=10).read().decode())' % str(ROOT / 'kontroller')],
                    capture_output=True, text=True, env=dict(os.environ, HTTPS_PROXY='http://127.0.0.1:%d' % fp_srv.server_address[1], HTTP_PROXY='http://127.0.0.1:%d' % fp_srv.server_address[1], NO_PROXY='localhost,127.0.0.1'), timeout=60)
assert hp.stdout.splitlines() == ['True', 'proxy-svar'] and sedda_proxy == ['http://exempel.test/'], (hp.stdout, hp.stderr[-300:], sedda_proxy)
miljo_hp = {k_: v_ for k_, v_ in os.environ.items() if not k_.upper().endswith('_PROXY')}
hp2 = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.VIA_PROXY)\ntry:\n    h.oppnare().open("http://finns-inte.exempel.test/", timeout=10)\nexcept Exception as e:\n    print(type(e).__name__, str(e)[:80])' % str(ROOT / 'kontroller')],
                     capture_output=True, text=True, env=miljo_hp, timeout=60)
assert hp2.stdout.startswith('False\n') and 'slå upp' in hp2.stdout and len(sedda_proxy) == 1, (hp2.stdout, hp2.stderr[-300:])
# en proxyvariabel som inte pekar på loopback är inte betrodd transport: adresskontrollen som förut (R24)
hp3 = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.VIA_PROXY)\ntry:\n    h.oppnare().open("http://finns-inte.exempel.test/", timeout=10)\nexcept Exception as e:\n    print(type(e).__name__, str(e)[:80])' % str(ROOT / 'kontroller')],
                     capture_output=True, text=True, env=dict(miljo_hp, HTTPS_PROXY='http://proxy.example:3128', HTTP_PROXY='http://proxy.example:3128'), timeout=60)
assert hp3.stdout.startswith('False\n') and 'slå upp' in hp3.stdout and len(sedda_proxy) == 1, (hp3.stdout, hp3.stderr[-300:])
# blandade variabler: en på loopback och en annanstans är inte betrodd transport; och transporten använder exakt kartan (R25)
hp3b = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.VIA_PROXY, h.PROXYKARTA)' % str(ROOT / 'kontroller')],
                      capture_output=True, text=True, env=dict(miljo_hp, HTTPS_PROXY='http://127.0.0.1:%d' % fp_srv.server_address[1], HTTP_PROXY='http://proxy.example:3128'), timeout=60)
assert hp3b.stdout.startswith('False None'), hp3b.stdout
hp3c = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.VIA_PROXY, h.PROXYKARTA)' % str(ROOT / 'kontroller')],
                      capture_output=True, text=True, env=dict(miljo_hp, https_proxy='http://127.0.0.1:%d' % fp_srv.server_address[1], HTTPS_PROXY='http://proxy.example:3128'), timeout=60)
assert hp3c.stdout.startswith('False'), 'versal mot gemen: båda måste vara loopback (R25): %s' % hp3c.stdout
# undantagen från proxyn (NO_PROXY) prövas som utan proxy: loopback nekas utan NWP_HAMTA_LOKALT, också med betrodd proxy
miljo_hp4 = dict(miljo_hp, HTTPS_PROXY='http://127.0.0.1:%d' % fp_srv.server_address[1], HTTP_PROXY='http://127.0.0.1:%d' % fp_srv.server_address[1], NO_PROXY='localhost,127.0.0.1'); miljo_hp4.pop('NWP_HAMTA_LOKALT', None)
hp4 = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.VIA_PROXY)\ntry:\n    h.oppnare().open("http://127.0.0.1:1/", timeout=10)\nexcept Exception as e:\n    print(type(e).__name__, str(e)[:80])' % str(ROOT / 'kontroller')],
                     capture_output=True, text=True, env=miljo_hp4, timeout=60)
assert hp4.stdout.startswith('True\n') and 'NekadAdress' in hp4.stdout and 'egna nätet' in hp4.stdout and len(sedda_proxy) == 1, (hp4.stdout, hp4.stderr[-300:])
# omdirigering via proxyn följs utan namnuppslag (R24, F7)
hp5 = subprocess.run([PY, '-c', 'import sys; sys.path.insert(0, %r); import hamta_sajt as h; print(h.oppnare().open("http://exempel.test/omdir", timeout=10).read().decode())' % str(ROOT / 'kontroller')],
                     capture_output=True, text=True, env=dict(miljo_hp4, NWP_HAMTA_LOKALT='1'), timeout=60)
assert hp5.stdout.strip() == 'proxy-svar' and sedda_proxy[-2:] == ['http://exempel.test/omdir', 'http://exempel.test/next'], (hp5.stdout, hp5.stderr[-300:], sedda_proxy)
fp_srv.shutdown()
print('hamta_sajt via sandlådans proxy ok')
# --- slugvakterna: granskarnas arbetskataloger hör till bygget (R24, F8); granskas frysning förankrad (R24, F1)
import slugvakt as sv_  # noqa: E402
(ROOT / 'underlag' / 'rokprov-mall').mkdir(parents=True, exist_ok=True)
assert sv_.tillaten_vag('/tmp/nwp-granskning/rokprov-mall/runda-01-1/x', 'rokprov-mall') and not sv_.tillaten_vag('/tmp/nwp-granskning/annan/runda-01-1/x', 'rokprov-mall') \
    and not sv_.tillaten_vag('/tmp/nwp-granskning/rokprov-mall-annan/runda-01-1/x', 'rokprov-mall') and not sv_.tillaten_vag('/tmp/nwp-granskning/rokprov-mall-runda-01-1/x', 'rokprov-mall'), 'sluggen som eget led (R25)'
for vag_, vantat_ in (('/tmp/nwp-granskning/rokprov-mall/runda-01-1/x', 0), ('/tmp/nwp-granskning/annan/runda-01-1/x', 2), ('/tmp/nwp-granskning/rokprov-mall-annan/runda-01-1/x', 2), ('/tmp/annat/x', 2)):
    rv_ = subprocess.run(['node', '-e', "import(%r).then((m) => { m.vakta(process.argv[1]); console.log('ok'); })" % str(ROOT / 'kontroller' / 'slugvakt.mjs'), vag_], capture_output=True, text=True, env=dict(os.environ, NWP_SLUG='rokprov-mall'), cwd=str(ROOT), timeout=60)
    assert rv_.returncode == vantat_, (vag_, rv_.returncode, rv_.stderr[-200:])
rv_ = subprocess.run(['node', '-e', "import(%r).then((m) => { m.inom(process.argv[1], 'sajtkatalogen'); console.log('ok'); })" % str(ROOT / 'kontroller' / 'slugvakt.mjs'), str(ROOT / 'kunder' / 'rokprov-mall' / 'sajt')], capture_output=True, text=True, env=dict(os.environ, NWP_SLUG='rokprov-mall'), cwd=str(ROOT), timeout=60)
assert rv_.returncode == 0, ('inom utan genomgång', rv_.stderr[-200:])
ik_ = (ROOT / 'kontroller' / 'ikoner.mjs').read_text(); assert 'inom(sajt' in ik_ and 'vakta(sajt' not in ik_, 'ikoner prövar sajten utan trädgenomgång (R25)'
assert "ARBETSROT / slug / " in (ROOT / 'kontroller' / 'granska.py').read_text(), 'granskarnas arbetskataloger under eget led'
# processgränsen från stoppkroken (R25): seatbelt med byggets policy, på riktigt. Sluggen är unik per körning och allt sker i egna
# kataloger (en tom provrot, /tmp/nwp-bygge-<slug>, /tmp/nwp-granskning/<slug>, en isolerad repokopia): det riktiga repots
# kunder/ och underlag/ rörs aldrig, och städningen tar bara det provet skapade (Codex R27, F28)
import processgrans as pg_  # noqa: E402
sl_pg = 'prov-bygge-%d' % os.getpid()
tmp_pg = Path('/tmp/nwp-bygge-' + sl_pg); gr_pg = Path('/tmp/nwp-granskning') / sl_pg
rot_kedja = tmp / 'kedja'


def egna_kataloger_(kataloger, lista):
    """Skapar varje katalog exklusivt (mkdir utan exist_ok) och registrerar den i lista först när den skapats: finns en redan
    (t.ex. återanvänt PID) lämnas den orörd och skapandet avbryts, medan de tidigare egna står i listan för städning
    (Codex R28/R29). En delad förälder (/tmp/nwp-granskning) skapas vid behov men registreras inte."""
    for p_ in kataloger:
        p_.mkdir(parents=True); lista.append(p_)


def stada_egna_(lista):
    """Tar bort bara de registrerade katalogerna, var och en för sig; ger felen i stället för att avbryta."""
    fel_ = []
    for p_ in lista:
        try:
            shutil.rmtree(p_)
        except Exception as e_:
            fel_.append('katalogen %s: %r' % (p_, e_))
    return fel_


# regressionsfall (Codex R29): faller det andra eller tredje skapandet på en befintlig katalog ska de tidigare egna städas,
# den befintliga förbli orörd och inget senare skapas
r29 = tmp / 'r29'; r29.mkdir(); (r29 / 'finns').mkdir(); (r29 / 'finns' / 'x.txt').write_text('befintligt')
for ordning_, egna_vantade_ in (([r29 / 'a', r29 / 'finns', r29 / 'b'], [r29 / 'a']), ([r29 / 'c', r29 / 'd', r29 / 'finns'], [r29 / 'c', r29 / 'd'])):
    lista_r29 = []
    try:
        egna_kataloger_(ordning_, lista_r29); assert False, 'en befintlig katalog ska avbryta skapandet'
    except FileExistsError:
        pass
    assert lista_r29 == egna_vantade_ and all(p_.is_dir() for p_ in egna_vantade_) and not any(p_.exists() for p_ in ordning_ if p_ not in egna_vantade_ and p_ != r29 / 'finns'), lista_r29
    assert stada_egna_(lista_r29) == [] and not any(p_.exists() for p_ in egna_vantade_) and (r29 / 'finns' / 'x.txt').read_text() == 'befintligt'
shutil.rmtree(r29)
# ägarlistan finns före try och är tom; skapandet och registreringen sker innanför, så att ett avbrutet skapande städar de tidigare
# egna katalogerna och lämnar den befintliga orörd (Codex R29); finally städar bara listan
egna_pg = []
rot_pg = srv_pg = wtk = None; klart_pg = False
try:  # allt nedan städas i finally, steg för steg, också när ett tidigare påstående faller (Codex R27/R28)
    egna_kataloger_([tmp_pg, rot_kedja, gr_pg], egna_pg)
    assert not (ROOT / 'kunder' / sl_pg).exists() and not (ROOT / 'underlag' / sl_pg).exists()
    rot_pg = Path(tempfile.mkdtemp(prefix='nwp-pg-', dir='/tmp')); egna_pg.append(rot_pg)  # exklusivt skapad; utanför sessionens temp och körningens egna kataloger, annars prövas inget
    (rot_pg / 'kunder' / sl_pg).mkdir(parents=True); (rot_pg / 'underlag' / sl_pg).mkdir(parents=True); (rot_pg / 'kontroller').mkdir()
    (rot_pg / 'hem' / '.nortropic-hemligheter').mkdir(parents=True); (rot_pg / 'hem' / '.nortropic-hemligheter' / 'x.env').write_text('DUMMY=hemligt'); (rot_pg / 'kunder' / sl_pg / '.env').write_text('X=1')
    shutil.copy2(ROOT / 'kontroller' / 'sandlada-domaner.txt', rot_pg / 'kontroller')
    srv_pg = hs_.HTTPServer(('127.0.0.1', 0), hs_.SimpleHTTPRequestHandler); th_.Thread(target=srv_pg.serve_forever, daemon=True).start()
    (rot_pg / 'prov.py').write_text('''import os, socket, sys, urllib.request
T = sys.argv[1]; S = sys.argv[2]; ut = []
def forsok(namn, f):
    try: r = f(); ut.append('%%s: %%s' %% (namn, r))
    except Exception as e: ut.append('%%s: %%s' %% (namn, type(e).__name__))
forsok('skriv-inne', lambda: open(os.path.join(T, 'kunder', S, 'x.txt'), 'w').write('x') and 'ok')
forsok('skriv-ute', lambda: open(os.path.join(T, 'kontroller/x.txt'), 'w').write('x') and 'ok')
forsok('skriv-underlag', lambda: open(os.path.join(T, 'underlag', S, 'y.txt'), 'w').write('y') and 'ok')
forsok('las-hemlig', lambda: open(os.path.join(T, 'hem/.nortropic-hemligheter/x.env')).read()[:5])
forsok('las-env', lambda: open(os.path.join(T, 'kunder', S, '.env')).read())
forsok('nat-lokalt', lambda: urllib.request.urlopen('http://127.0.0.1:%d/', timeout=5).status)
forsok('nat-ut', lambda: socket.create_connection(('1.1.1.1', 80), timeout=5) and 'ansluten')
forsok('bind', lambda: (lambda s: (s.bind(('127.0.0.1', 0)), s.close(), 'ok')[2])(socket.socket()))
forsok('skriv-tmpdir', lambda: open(os.path.join(os.environ.get('TMPDIR', '/nonexistent'), 'x.txt'), 'w').write('x') and 'ok')
forsok('skriv-systemtemp', lambda: open(os.path.join(%r, 'nwp-pg-prov.txt'), 'w').write('x') and 'ok')
ut.append('processgrans=%%s refero=%%s proxy=%%s tmpdir=%%s' %% (os.environ.get('NWP_PROCESSGRANS'), os.environ.get('REFERO_MCP_TOKEN'), os.environ.get('HTTP_PROXY') or os.environ.get('https_proxy'), os.environ.get('TMPDIR')))
print(' | '.join(ut))
''' % (srv_pg.server_address[1], tempfile.gettempdir()))
    rpg = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg), '--hem', str(rot_pg / 'hem'), '--', PY, str(rot_pg / 'prov.py'), str(rot_pg), sl_pg], capture_output=True, text=True, timeout=120,
                         env=dict(os.environ, REFERO_MCP_TOKEN='prov-hemlig', HTTP_PROXY='http://x:y@localhost:1', https_proxy='http://x:y@localhost:1'))
    srv_pg.shutdown(); srv_pg.server_close(); srv_pg = None
    assert rpg.returncode == 0 and 'processgräns: sandbox-exec' in rpg.stderr, (rpg.returncode, rpg.stderr[-300:])
    for vantat_ in ('skriv-inne: ok', 'skriv-ute: PermissionError', 'skriv-underlag: ok', 'las-hemlig: PermissionError', 'las-env: PermissionError', 'nat-lokalt: 200', 'nat-ut: PermissionError', 'bind: ok',
                    'skriv-tmpdir: ok', 'skriv-systemtemp: PermissionError', 'processgrans=1 refero=None proxy=None tmpdir=%s' % (tmp_pg / 'tmp')):
        assert vantat_ in rpg.stdout, (vantat_, rpg.stdout)  # miljön rensad (R26 F1/F27), temp bara körningens egen (R26 F1)
    assert not (Path(tempfile.gettempdir()) / 'nwp-pg-prov.txt').exists()
    assert 'kontroller/x.txt' not in [x.name for x in (rot_pg / 'kontroller').iterdir()] and (rot_pg / 'kunder' / sl_pg / 'x.txt').is_file()
    assert subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg)], capture_output=True, text=True).returncode == 2, 'utan kommando: slutkod 2'
    # en repokopia under den tillåtna tempkatalogen: policyns skrivförbud följer med (R26, F1): mekaniken skrivskyddad, byggets kataloger skrivbara
    rot_k = tmp_pg / 'tmp' / 'kopia'
    for d_ in ('kunder/' + sl_pg, 'kunder/annan', 'underlag/' + sl_pg, 'kontroller', '.claude/hooks', 'backlog', 'kritik'):
        (rot_k / d_).mkdir(parents=True)
    shutil.copy2(ROOT / 'kontroller' / 'sandlada-domaner.txt', rot_k / 'kontroller')
    prof_k = pg_.profil(sl_pg, root=rot_k, hem=str(rot_pg / 'hem'))
    neka_k = '(deny file-write* (subpath "%s/kontroller"))' % rot_k
    assert neka_k in prof_k and prof_k.index(neka_k) > prof_k.index('(allow file-write* (subpath "%s"))' % (tmp_pg / 'tmp')), 'skrivförbuden står efter tillåtelserna (sista regeln gäller)'
    (rot_k / 'prov.py').write_text('''import os, sys
T = sys.argv[1]; S = sys.argv[2]; ut = []
for namn, vag in (('kontroller', 'kontroller/x.txt'), ('hooks', '.claude/hooks/x.py'), ('kritik', 'kritik/x.md'), ('annan-kund', 'kunder/annan/x.txt'), ('egen-kund', 'kunder/' + S + '/x.txt'), ('backlog', 'backlog/x.md')):
    try:
        open(os.path.join(T, vag), 'w').write('x'); ut.append(namn + ': ok')
    except Exception as e:
        ut.append('%s: %s' % (namn, type(e).__name__))
print(' | '.join(ut))
''')
    rk = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_k), '--hem', str(rot_pg / 'hem'), '--', PY, str(rot_k / 'prov.py'), str(rot_k), sl_pg], capture_output=True, text=True, timeout=120)
    assert rk.returncode == 0, (rk.returncode, rk.stderr[-300:])
    for vantat_ in ('kontroller: PermissionError', 'hooks: PermissionError', 'kritik: PermissionError', 'annan-kund: PermissionError', 'egen-kund: ok', 'backlog: ok'):
        assert vantat_ in rk.stdout, (vantat_, rk.stdout)
    assert not (rot_k / 'kontroller' / 'x.txt').exists() and (rot_k / 'kunder' / sl_pg / 'x.txt').is_file()
    # stoppkroken och avslutskedjan prövas i en isolerad repokopia: mekaniken kopierad (som kor.sh-provet), körmiljön länkad, egna
    # tomma kunder/, underlag/ och backlog/. Kopians krok, processgräns, tjänst och granskning hittar sin rot från sina egna filer.
    for namn_ in ('kor.sh', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', '.gitignore', 'dashboard.sh'):
        if (ROOT / namn_).is_file():
            shutil.copy2(ROOT / namn_, rot_kedja / namn_)
    for mapp_ in ('kontroller', '.claude', 'kritik', 'kunskap', 'mall'):
        shutil.copytree(ROOT / mapp_, rot_kedja / mapp_, ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'rokprov'), symlinks=True)
    for mapp_ in ('kunder', 'underlag', 'backlog'):
        (rot_kedja / mapp_).mkdir()
    os.symlink(ROOT / '.venv', rot_kedja / '.venv'); os.symlink(ROOT / 'kontroller' / 'node_modules', rot_kedja / 'kontroller' / 'node_modules')
    hook_ = (rot_kedja / '.claude' / 'hooks' / 'stoppvakt.py').read_text(); assert 'processgrans.py' in hook_ and "NWP_SANDLADA" in hook_, 'stoppvakten går via processgränsen'
    # stoppkroken går via processgränsen med sandlådan på: provet körs under seatbelt och kroken blockerar (inget bygge)
    kund_sv = rot_kedja / 'kunder' / sl_pg; kund_sv.mkdir()
    rsv = subprocess.run([PY, '-B', str(rot_kedja / '.claude' / 'hooks' / 'stoppvakt.py')], input='{}', capture_output=True, text=True, cwd=str(rot_kedja), timeout=600,
                         env={k_: v_ for k_, v_ in os.environ.items() if not k_.startswith('CLAUDE_CODE_') and k_ != 'CLAUDECODE'} | {'NWP_SLUG': sl_pg, 'NWP_SANDLADA': 'pa', 'NWP_GRANSKNING': 'av', 'NWP_STOPP_TAK': '8'})
    assert rsv.returncode == 2 and (kund_sv / 'prov' / 'STATUS.json').is_file(), (rsv.returncode, rsv.stdout[-300:], rsv.stderr[-400:])
    assert json.loads((kund_sv / 'prov' / 'STATUS.json').read_text())['ok'] is False, 'provet kördes (rött utan sajt) innanför processgränsen'
    shutil.rmtree(kund_sv)
    # avslutskedjan utan proxyvariabler (Codex R26, F1/F28): drivaren innanför processgränsen, som stoppkroken startar den, med
    # den riktiga tjänsten anvisad och bara markören; arbetaren ska delegeras till tjänsten (utanför gränsen), granskarna (den
    # falska claude i PATH) svara, och domen komma tillbaka till drivaren. Inget tidigare godkännande finns att återanvända.
    kund_sv.mkdir(); (kund_sv / 'sajt' / 'dist').mkdir(parents=True); (kund_sv / 'prov' / 'inspektion' / 'hem').mkdir(parents=True)
    (kund_sv / 'sajt' / 'dist' / 'index.html').write_text('<html><body><p>prov</p></body></html>')
    (kund_sv / 'prov' / 'inspektion' / 'hem' / 'vy-390-forsta.png').write_bytes(b'\x89PNG')
    (kund_sv / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': prova.dist_hash(kund_sv / 'sajt' / 'dist')}))
    (rot_kedja / 'underlag' / sl_pg).mkdir()
    kv_k = tmp / 'wt-kedja'; os.environ['PROV_FALL'] = 'ingen'
    wtk = subprocess.Popen([PY, '-B', str(rot_kedja / 'kontroller' / 'webbtjanst.py'), 'serve', '--slug', sl_pg, '--kvitto', str(kv_k), '--doman', 'exempel.se', '--korning', 'K2'],
                           stdout=open(tmp / 'wt-kedja.log', 'w'), stderr=subprocess.STDOUT, cwd=str(rot_kedja))
    for _ in range(50):
        if kv_k.is_file() and len(kv_k.read_text().splitlines()) >= 2:
            break
        time.sleep(0.1)
    port_k, nyckel_k = kv_k.read_text().splitlines()[:2]
    miljo_kedja = {k_: v_ for k_, v_ in os.environ.items() if not k_.upper().endswith('_PROXY') and not k_.startswith('CLAUDE_CODE_') and k_ != 'CLAUDECODE' and not k_.startswith('NWP_')}
    miljo_kedja.update({'NWP_SANDLADA': 'pa', 'NWP_SLUG': sl_pg, 'NWP_KORNING': 'K2', 'NWP_WEBBTJANST': 'http://127.0.0.1:' + port_k, 'NWP_WEBBTJANST_NYCKEL': nyckel_k, 'REFERO_MCP_TOKEN': 'prov-hemlig'})
    rk2 = subprocess.run([PY, '-B', str(rot_kedja / 'kontroller' / 'processgrans.py'), sl_pg, '--', PY, '-B', str(rot_kedja / 'kontroller' / 'granska.py'), sl_pg, '--vanta', '240'],
                         capture_output=True, text=True, env=miljo_kedja, cwd=str(rot_kedja), timeout=400)
    runda_k = kund_sv / 'granskning' / 'runda-01'
    logg_k = (tmp / 'wt-kedja.log').read_text()
    arb_k = (runda_k / 'arbetare.log').read_text()[-600:] if (runda_k / 'arbetare.log').is_file() else 'ingen arbetarlogg'
    assert rk2.returncode == 0 and 'processgräns: sandbox-exec' in rk2.stderr, (rk2.returncode, rk2.stdout[-600:], rk2.stderr[-600:], arb_k, logg_k[-600:])
    assert 'START granska --arbetare ' + str(runda_k.resolve()) in logg_k and 'KLART granska rc=0' in logg_k, ('arbetaren gick via tjänsten', logg_k[-800:], arb_k)  # tjänsten loggar den upplösta vägen (kopian ligger under en symlänkad temp)
    g_k = json.loads((runda_k / 'GRANSKNING.json').read_text()); assert g_k['godkand'] is True and len(g_k['enskilda']) == 2, g_k
    assert not list(gr_pg.glob('*/.env')) and 'prov-hemlig' not in arb_k
    assert not (ROOT / 'kunder' / sl_pg).exists() and not (ROOT / 'underlag' / sl_pg).exists(), 'det riktiga repot rörs inte'
    klart_pg = True
finally:
    # varje resurs städas för sig, så att ett fel i en (t.ex. en tjänst som inte svarar på terminate) inte hoppar över de andra;
    # felen rapporteras efteråt och fäller provet bara om själva provet gick igenom (Codex R28)
    fel_pg = []

    def stada_(namn_, steg_):
        try:
            steg_()
        except Exception as e_:
            fel_pg.append('%s: %r' % (namn_, e_))

    def stoppa_tjansten_():
        if wtk is None:
            return
        wtk.terminate()
        try:
            wtk.wait(timeout=10)
        except subprocess.TimeoutExpired:
            wtk.kill(); wtk.wait(timeout=10)
    stada_('tjänsten', stoppa_tjansten_)
    stada_('provservern', lambda: (srv_pg.shutdown(), srv_pg.server_close()) if srv_pg is not None else None)
    stada_('PROV_FALL', lambda: os.environ.pop('PROV_FALL', None))
    fel_pg += stada_egna_(egna_pg)
    if fel_pg:
        print('städningen efter processgränsblocket: ' + '; '.join(fel_pg))
        if klart_pg:
            raise AssertionError('städningen misslyckades: %s' % fel_pg)
print('processgränsen från stoppkroken ok')
import granska as gr_  # noqa: E402
kund_g = tmp / 'kund-g'; (kund_g / 'sajt' / 'dist').mkdir(parents=True); (kund_g / 'prov').mkdir()
(kund_g / 'sajt' / 'dist' / 'index.html').write_text('<html></html>'); (kund_g / 'prov' / 'copy.md').write_text('ok')
hemlig_g = tmp / 'hemlig.txt'; hemlig_g.write_text('HEMLIGT')
rdir_g = tmp / 'runda-g'; rdir_g.mkdir()
gr_.frys_bygget(kund_g, rdir_g); assert (rdir_g / 'dist' / 'index.html').is_file() and (rdir_g / 'copy.md').read_text() == 'ok'
(kund_g / 'prov' / 'standard.md').symlink_to(hemlig_g)
rdir_g2 = tmp / 'runda-g2'; rdir_g2.mkdir()
try:
    gr_.frys_bygget(kund_g, rdir_g2); assert False, 'en symlänk i prov/ får inte kopieras'
except RuntimeError as e_:
    assert 'symlänk' in str(e_) and not (rdir_g2 / 'standard.md').exists()
(kund_g / 'prov' / 'standard.md').unlink(); (kund_g / 'sajt' / 'dist' / 'lank.txt').symlink_to(hemlig_g)
rdir_g3 = tmp / 'runda-g3'; rdir_g3.mkdir()
try:
    gr_.frys_bygget(kund_g, rdir_g3); assert False, 'en symlänk i dist/ får inte kopieras'
except RuntimeError as e_:
    assert 'symlänk' in str(e_) and not (rdir_g3 / 'dist').exists()
assert 'HEMLIGT' not in ''.join(p_.read_text() for p_ in [x for x in rdir_g3.rglob('*') if x.is_file()] + [x for x in rdir_g2.rglob('*') if x.is_file()]), 'ingen hemlighet i någon omgång'
print('slugvakterna och granskas frysning ok')

# ---------------------------------------------------------------- kalibreringsankarna (backlogposten om kalibrering av visuell nivå, steg 2, 2026-10-04):
# ägarens domar privata; ankarna fryses i omgången med ägarens ord ordagrant, undanhållna syns aldrig i uppdraget; försöket mäter
import importlib.util as ilu_
kal_u = tmp / 'kal-underlag'; kal_r = kal_u / 'kalibrering'
png_ = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32
for ident_, niva_ in (('K01', 'over'), ('K02', 'nastan'), ('K03', 'generisk'), ('K04', 'over')):
    for sida_ in ('start', 'undersida'):
        (kal_r / ident_ / sida_).mkdir(parents=True)
        for v_ in ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png', 'vy-390-ruta-01.png'):
            (kal_r / ident_ / sida_ / v_).write_bytes(png_)
        (kal_r / ident_ / sida_ / 'vy-390-aria.txt').write_text('träd')
(kal_r / 'DOMAR.json').write_text(json.dumps({'K01': {'niva': 'over', 'skiljer': 'ETIKETTERNA bär allt', 'tid': 't'}, 'K02': {'niva': 'nastan', 'skiljer': 'GENRETROGEN polering', 'tid': 't'},
                                               'K03': {'niva': 'generisk', 'skiljer': 'IKONRUTNÄT och garantikort', 'tid': 't'}, 'K04': {'niva': 'over', 'skiljer': 'HÅRLINJER', 'tid': 't'}, 'K99': {'niva': 'fel'}}))
(kal_r / 'ANKARE.txt').write_text('# delning\nK01 · ankare\nK03 · ankare\nK02 · undanhållen\nK04 · undanhållen\n')
ex_ = gr.kalibreringsexempel(kal_u)
assert [(e['id'], e['niva'], e['ankare'], len(e['bilder'])) for e in ex_] == [('K01', 'over', True, 2), ('K02', 'nastan', False, 2), ('K03', 'generisk', True, 2), ('K04', 'over', False, 2)], ex_
runda_kal = tmp / 'runda-kal'; runda_kal.mkdir()
fr_ = gr.frysta_ankare(runda_kal, kal_u)
md_kal, bilder_kal = fr_
text_kal = md_kal.read_text()
assert 'ETIKETTERNA bär allt' in text_kal and 'IKONRUTNÄT och garantikort' in text_kal and 'GENRETROGEN' not in text_kal and 'HÅRLINJER' not in text_kal, 'bara ankarnas ord, ordagrant'
assert [p_.name for p_, _ in bilder_kal] == ['K01-vy-390-forsta.png', 'K01-vy-1440-forsta.png', 'K03-vy-390-forsta.png', 'K03-vy-1440-forsta.png'] and all(p_.read_bytes() == png_ for p_, _ in bilder_kal)
assert [t_ for _, t_ in bilder_kal] == ['K01 · tydligt över ribban', 'K01 · tydligt över ribban', 'K03 · generisk', 'K03 · generisk']
upp_kal = gr.uppdrag_text('ref38', 'http://x', ['/'], tmp / 'arb', [], [], [], [], runda_kal, (), fr_)
assert 'Kalibreringsankare' in upp_kal and 'K01-vy-390-forsta.png — K01 · tydligt över ribban' in upp_kal and 'ordagrant: ' in upp_kal and md_kal.name in upp_kal.split('ordagrant: ')[1].split('\n')[0] and 'K02' not in upp_kal and 'K04' not in upp_kal, upp_kal[-1500:]  # vägen relativ när omgången ligger under ROOT
assert 'kalibreringsankarna' in upp_kal.split('Verksamhetens underlag')[0]
upp_utan = gr.uppdrag_text('ref38', 'http://x', ['/'], tmp / 'arb', [], [], [], [], runda_kal)
assert 'Kalibreringsankare' not in upp_utan and 'ankare' not in upp_utan.split('Verksamhetens underlag')[0].replace('kalibreringsankarna', '')
assert gr.frysta_ankare(tmp / 'runda-kal2', tmp / 'finns-inte') is None, 'utan underlag: inga ankare'
(kal_r / 'K01' / 'start' / 'vy-390-forsta.png').unlink(); (kal_r / 'K01' / 'start' / 'vy-390-forsta.png').symlink_to(tmp / 'hemlig.txt')
try:
    gr.frysta_ankare(tmp / 'runda-kal3', kal_u); assert False, 'en planterad symlänk bland ankarbilderna får inte kopieras'
except RuntimeError as e_:
    assert 'symlänk' in str(e_)
(kal_r / 'K01' / 'start' / 'vy-390-forsta.png').unlink(); (kal_r / 'K01' / 'start' / 'vy-390-forsta.png').write_bytes(png_)
# försöket: undanhållna förbereds med egna bilder och ankarna, uppdraget nämner inte de undanhållnas ord; jämförelsen räknar rätt
spec_ = ilu_.spec_from_file_location('kalforsok', ROOT / 'kontroller' / 'granskarforsok' / 'kalibrering.py'); kf_ = ilu_.module_from_spec(spec_); spec_.loader.exec_module(kf_)
gr.SCHEMA = ROOT / 'kritik' / 'SCHEMA-granskning.json'  # det riktiga schemat (F8-blocket bytte till ett tomt): de obligatoriska fälten prövas, och manifestet är stabilt genom blocket
und_ = kf_.undanhallna(kal_u); assert [e['id'] for e in und_] == ['K02', 'K04']
ut_kf = tmp / 'forsok'
rc_kf = kf_.main(['--torr', '--ut', str(ut_kf), '--underlag', str(kal_u)]); assert rc_kf == 0
# ett nytt orört urval prövas för sig (--bara): bara de valda, och ett id utan dom eller som är ankare vägras
ut_bara = tmp / 'forsok-bara'
assert kf_.main(['--torr', '--ut', str(ut_bara), '--underlag', str(kal_u), '--bara', 'K04']) == 0 and sorted(p_.name for p_ in ut_bara.iterdir() if p_.is_dir()) == ['K04']
assert kf_.main(['--torr', '--ut', str(ut_bara), '--underlag', str(kal_u), '--bara', 'K01']) == 2, 'ett ankare är inget undanhållet exempel'
assert kf_.main(['--torr', '--ut', str(ut_bara), '--underlag', str(kal_u), '--bara', 'K99']) == 2 and kf_.main(['--torr', '--ut', str(ut_bara), '--underlag', str(kal_u), '--bara', 'x']) == 2
for ident_ in ('K02', 'K04'):
    pr_ = (ut_kf / ident_ / 'PROMPT.txt').read_text()
    assert 'kalibreringsförsök' in pr_ and 'K01 · tydligt över ribban' in pr_ and 'K03 · generisk' in pr_ and 'GENRETROGEN' not in pr_ and 'HÅRLINJER' not in pr_, pr_[:600]
    assert (ut_kf / ident_ / 'sajt' / 'start' / 'vy-390-forsta.png').is_file() and (ut_kf / ident_ / 'sajt' / 'undersida' / 'vy-390-ruta-01.png').is_file() and (ut_kf / ident_ / 'kalibrering.md').is_file()
    assert 'ETIKETTERNA' in (ut_kf / ident_ / 'kalibrering.md').read_text() and 'GENRETROGEN' not in (ut_kf / ident_ / 'kalibrering.md').read_text()
    assert str(ut_kf / ident_ / 'sajt' / 'start' / 'vy-390-aria.txt') in pr_
krit_ok = {n_: {'betyg': 8, 'motivering': '', 'visa': True} for n_ in gr.KRITERIER}
krit_lagt = dict(krit_ok, designkvalitet={'betyg': 5, 'motivering': '', 'visa': False})
rader_kf, s_kf = kf_.jamfor(und_, {'K02': ({'kriterier': krit_ok, 'blockerande': []}, None), 'K04': ({'kriterier': krit_lagt, 'blockerande': []}, None)})  # redan validerade svar som (res, None)
assert [r_['utfall'] for r_ in rader_kf] == ['falskt godkännande', 'falskt underkännande'] and s_kf == {'undanhallna': 2, 'svar': 2, 'ofullstandiga': 0, 'falska_godkannanden': 1, 'av_ej_over': 1, 'falska_underkannanden': 1, 'av_over': 1}, (rader_kf, s_kf)
rader_kf2, s_kf2 = kf_.jamfor(und_, {'K02': ({'kriterier': krit_lagt, 'blockerande': []}, None), 'K04': None})
assert rader_kf2[0]['utfall'] == 'rätt' and rader_kf2[1]['utfall'] == 'ofullständigt: inget svar' and s_kf2['svar'] == 1 and s_kf2['ofullstandiga'] == 1 and s_kf2['falska_godkannanden'] == 0
rap_ = kf_.rapport(rader_kf, s_kf, ut_kf, 'm', 'e'); assert 'Falska godkännanden: 1 av 1' in rap_.read_text() and (ut_kf / 'RAPPORT.json').is_file()
# validering (Codex R30): anropsfel och ofullständiga svar är aldrig domar; ett svar återanvänds bara med identiskt manifest
helt_ = {'kriterier': krit_ok, 'kognitiv_genomgang': [], 'blockerande': [], 'forbattringar': [], 'styrkor': [], 'likhet_tidigare': '', 'sett': [], 'ej_bedomt': [], 'sammanfattning': ''}
schema_ = kf_.las_schema(ROOT / 'kritik' / 'SCHEMA-granskning.json')
block_ok = {'kriterium': 'text', 'allvarlighet': 3, 'var': 'x', 'observation': 'x', 'konsekvens': 'x', 'standardpunkt': 'x', 'heuristik': 'x', 'omfattning': 'detalj', 'rattning': 'x', 'acceptanskriterium': 'x'}
assert kf_.validera({'subtype': 'success', 'structured_output': helt_}, schema_)[1] is None
assert kf_.validera({'subtype': 'success', 'structured_output': dict(helt_, blockerande=[block_ok], kognitiv_genomgang=[{'uppgift': 'u', 'steg': 's', 'alla_ja': True, 'brist': ''}])}, schema_)[1] is None
# hela schemat (Codex R31): null i obligatoriska fält, tomma eller felaktiga blockerande poster, okända fält, enum och gränser
for svar_, vantat_ in (({'is_error': True, 'structured_output': helt_}, 'anropet misslyckades'), ({'subtype': 'error_max_turns', 'structured_output': helt_}, 'anropet misslyckades'),
                       ({'structured_output': {'kriterier': {}}}, 'saknas'), ({'structured_output': dict(helt_, kriterier={})}, 'saknas'),
                       ({'structured_output': dict(helt_, kriterier=dict(krit_ok, text={'betyg': 11, 'motivering': '', 'visa': True}))}, 'över 10'),
                       ({'structured_output': dict(helt_, blockerande=None)}, 'fel typ'), (None, 'inget svar'), ({'structured_output': 'x'}, 'strukturerat'),
                       ({'structured_output': dict(helt_, sammanfattning=None)}, 'fel typ'), ({'structured_output': dict(helt_, styrkor=None)}, 'fel typ'),
                       ({'structured_output': dict(helt_, blockerande=[{}])}, 'blockerande[0]: fältet'), ({'structured_output': dict(helt_, blockerande=[None])}, 'blockerande[0]: fel typ'),
                       ({'structured_output': dict(helt_, blockerande=[dict(block_ok, kriterium='annat')])}, 'ingår inte'), ({'structured_output': dict(helt_, blockerande=[dict(block_ok, allvarlighet=5)])}, 'över 4'),
                       ({'structured_output': dict(helt_, blockerande=[dict(block_ok, extra=1)])}, 'okänt fält'), ({'structured_output': dict(helt_, extra=1)}, 'okänt fält'),
                       ({'structured_output': dict(helt_, kriterier=dict(krit_ok, text={'betyg': 7, 'motivering': '', 'visa': 'ja'}))}, 'fel typ')):
    res_, fel_ = kf_.validera(svar_, schema_); assert res_ is None and vantat_ in fel_, (svar_, fel_)
for dalig_ in ('x', '{"required": ["a"]}', '[]'):
    (tmp / 'dalig-schema.json').write_text(dalig_)
    try:
        kf_.las_schema(tmp / 'dalig-schema.json'); assert False, 'oläsbart schema ska vara ett försöksfel'
    except RuntimeError:
        pass
rader_kf3, s_kf3 = kf_.jamfor(und_, {'K02': {'is_error': True, 'structured_output': helt_}, 'K04': {'subtype': 'success', 'structured_output': helt_}}, schema_)
rader_kf4, s_kf4 = kf_.jamfor(und_, {'K02': {'subtype': 'success', 'structured_output': dict(helt_, blockerande=[None])}, 'K04': {'subtype': 'success', 'structured_output': dict(helt_, sett=None)}}, schema_)
assert s_kf4['ofullstandiga'] == 2 and all(r_['utfall'].startswith('ofullständigt') for r_ in rader_kf4), 'ogiltiga poster kraschar inte sammanställningen utan blir ofullständiga'
assert rader_kf3[0]['utfall'].startswith('ofullständigt') and rader_kf3[0]['granskaren'] is None and rader_kf3[1]['utfall'] == 'rätt' and s_kf3['ofullstandiga'] == 1 and s_kf3['svar'] == 1 and s_kf3['falska_godkannanden'] == 0, (rader_kf3, s_kf3)
assert 'ofullständigt' in kf_.rapport(rader_kf3, s_kf3, ut_kf, 'm', 'e').read_text()
import contextlib as cl_, io as io_
def torr_(*extra_):
    buf_ = io_.StringIO()
    with cl_.redirect_stdout(buf_):
        rc_ = kf_.main(['--torr', '--ut', str(ut_kf), '--underlag', str(kal_u), *extra_])
    return rc_, buf_.getvalue()
assert (ut_kf / 'K02' / 'MANIFEST.json').is_file()
# metoden fryses med bilderna (Codex R31): granskartext, schema och måttstockar i exemplets metod/, uppdraget och anropet pekar dit, manifestet hashar kopiorna
fryst_ = ut_kf / 'K02' / 'metod'
assert (fryst_ / 'kritik' / 'GRANSKARE.md').is_file() and (fryst_ / 'kritik' / 'SCHEMA-granskning.json').is_file() and (fryst_ / 'kunskap' / 'visuell-niva.md').is_file() and (fryst_ / 'kunskap' / 'teoretisk-grund.md').is_file()
man_ = json.loads((ut_kf / 'K02' / 'MANIFEST.json').read_text())
assert man_['regler']['kritik/GRANSKARE.md'] == kf_.hash_fil(fryst_ / 'kritik' / 'GRANSKARE.md') and 'kunskap/visuell-niva.md' in man_['regler'] and 'kritik/SCHEMA-granskning.json' in man_['regler']
assert str(fryst_) in (ut_kf / 'K02' / 'PROMPT.txt').read_text()
args_ = kf_.claude_args(ut_kf / 'K02', 'm', 'e', 'claude')
assert (fryst_ / 'kritik' / 'SCHEMA-granskning.json').read_text() in args_ and ('Read(%s/**)' % kf_.ROOT) in args_ and '--add-dir' in args_
(fryst_ / 'kritik' / 'SCHEMA-granskning.json').write_text('x'); (ut_kf / 'K02' / 'svar.json').write_text(json.dumps({'subtype': 'success', 'structured_output': helt_})); (ut_kf / 'K02' / 'KORNING.json').write_text(json.dumps({'slutkod': 0}))
try:
    kf_.giltigt_svar(ut_kf / 'K02'); assert False, 'oläsbart fryst schema ska vara ett försöksfel'
except RuntimeError:
    pass
(ut_kf / 'K02' / 'svar.json').write_text(json.dumps({'subtype': 'success', 'structured_output': helt_})); (ut_kf / 'K02' / 'KORNING.json').write_text(json.dumps({'slutkod': 0}))
rc_, ut_text = torr_(); assert rc_ == 0 and 'återanvända (identiskt manifest, giltigt svar): 1; att köra: 1' in ut_text and (ut_kf / 'K02' / 'svar.json').is_file(), ut_text
rc_, ut_text = torr_('--modell', 'annan'); assert 'återanvända (identiskt manifest, giltigt svar): 0; att köra: 2' in ut_text and not (ut_kf / 'K02' / 'svar.json').exists(), ('annan modell: inget återanvänds', ut_text)
rc_, ut_text = torr_('--modell', 'annan'); assert 'återanvända (identiskt manifest, giltigt svar): 0' in ut_text  # inget svar finns längre
(ut_kf / 'K02' / 'svar.json').write_text(json.dumps({'subtype': 'success', 'structured_output': helt_})); (ut_kf / 'K02' / 'KORNING.json').write_text(json.dumps({'slutkod': 0}))
(kal_r / 'K01' / 'start' / 'vy-390-forsta.png').write_bytes(png_ + b'ny')  # en ankarbild ändrad: manifestet skiljer sig
rc_, ut_text = torr_('--modell', 'annan'); assert 'återanvända (identiskt manifest, giltigt svar): 0; att köra: 2' in ut_text, ('ändrad ankarbild: inget återanvänds', ut_text)
(ut_kf / 'K02' / 'svar.json').write_text(json.dumps({'is_error': True, 'structured_output': helt_})); (ut_kf / 'K02' / 'KORNING.json').write_text(json.dumps({'slutkod': 0}))
rc_, ut_text = torr_('--modell', 'annan'); assert 'återanvända (identiskt manifest, giltigt svar): 0; att köra: 2' in ut_text and not (ut_kf / 'K02' / 'svar.json').exists(), ('felmarkerat svar körs om', ut_text)
(ut_kf / 'K02' / 'svar.json').write_text(json.dumps({'subtype': 'success', 'structured_output': helt_})); (ut_kf / 'K02' / 'KORNING.json').write_text(json.dumps({'slutkod': 1}))
rc_, ut_text = torr_('--modell', 'annan'); assert 'att köra: 2' in ut_text, ('slutkod 1 körs om', ut_text)
assert kf_.giltigt_svar(ut_kf / 'K04')[1] is not None
assert 'visuell-niva.md' in (ROOT / 'kritik' / 'GRANSKARE.md').read_text() and 'Kalibreringsankarna' in (ROOT / 'kritik' / 'GRANSKARE.md').read_text() and 'Bildankarna' not in (ROOT / 'kritik' / 'GRANSKARE.md').read_text()
vn_ = (ROOT / 'kunskap' / 'visuell-niva.md').read_text().lower()
assert all(x_ not in vn_ for x_ in ('oatly', 'koto', 'aman', 'dinesen', 'belvia', 'blue tit', 'sparky', 'vardehaugen', 'snickaren', 'paint it', 'sundbom', 'salong kreativ', 'grilli')), 'den publika filen namnger inga sajter'
print('kalibreringsankarna och försöket ok')

# ---------------------------------------------------------------- referenssteget (ägarbeslut 2026-10-04; Codex R32): uppdraget validerat (riktiga värdnamn,
# aldrig IP-former eller lokala namn; lokala provundantag bara för uttryckliga portar), skrivmålet förankrat, två pass med resursursprung bara för
# inspektionen, fullständig fångst krävs (båda vyerna, bildfiler, tillstånd, egna resurser), kollisionsfria sidkataloger, kompletteringar med arv
import referens as rf_  # noqa: E402
png_ref = b'\x89PNG\r\n\x1a\n' + bytes.fromhex('0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8cfc0000000020001e221bc330000000049454e44ae426082')
class RefBild_(hs_.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type', 'image/png'); self.send_header('Content-Length', str(len(png_ref))); self.end_headers(); self.wfile.write(png_ref)
    def log_message(self, *a): pass
srv_rb = hs_.HTTPServer(('127.0.0.1', 0), RefBild_); th_.Thread(target=srv_rb.serve_forever, daemon=True).start()   # B: resursursprung som får tillåtas
srv_rc = hs_.HTTPServer(('127.0.0.1', 0), RefBild_); th_.Thread(target=srv_rc.serve_forever, daemon=True).start()   # C: lokalt ursprung utan provundantag
b_ref = 'http://127.0.0.1:%d' % srv_rb.server_address[1]; c_ref = 'http://127.0.0.1:%d' % srv_rc.server_address[1]
class RefA_(hs_.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/saknas' or self.path.endswith('.png'):
            self.send_response(404); self.send_header('Content-Length', '0'); self.end_headers(); return
        bild = c_ref if self.path == '/c' else (a_ref if self.path == '/trasig' else b_ref)
        img = '' if self.path == '/egen' else '<img src="%s/bild.png" width="200" height="100" alt="bild">' % bild  # /egen: bara egna resurser
        html = ('<html><head><title>Lokal referens</title></head><body><h1>%s</h1><p>Vi använder cookies. <button id="godkann">Godkänn alla</button></p>'
                '<nav><button id="meny">Meny</button></nav>%s<p>%s</p></body></html>' % (self.path, img, 'text ' * 200)).encode()
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(html))); self.end_headers(); self.wfile.write(html)
    def log_message(self, *a): pass
srv_ra = hs_.HTTPServer(('127.0.0.1', 0), RefA_); th_.Thread(target=srv_ra.serve_forever, daemon=True).start()
a_ref = 'http://127.0.0.1:%d' % srv_ra.server_address[1]
portar_ref = '%d,%d' % (srv_ra.server_address[1], srv_rb.server_address[1])
lok_ref = (srv_ra.server_address[1], srv_rb.server_address[1])
u_ref = tmp / 'ref-underlag'; (u_ref / 'prov-ref').mkdir(parents=True)
kand_ref = {'namn': 'lokal', 'adress': a_ref + '/', 'roll': 'hantverk', 'varfor': 'prov', 'sidor': ['/', '/a/b', '/a-b'], 'meny': '#meny'}
upp_ref = {'kandidater': [kand_ref, {'namn': 'andra', 'adress': a_ref + '/', 'roll': 'bransch', 'varfor': 'prov två', 'sidor': ['/']}], 'fragor': ['hur ser priser ut?']}
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps(upp_ref))
# ogiltiga uppdrag vägras (slutkod 2) innan något öppnas; IP-former, lokala namn och icke-standardportar aldrig
for dalig_, skal_ in (({'kandidater': []}, 'saknar kandidater'), ({'kandidater': [dict(kand_ref, namn='Fel Namn')]}, 'namn'),
                      ({'kandidater': [dict(kand_ref, adress='https://user:pw@exempel.se/')]}, 'användaruppgifter'),
                      ({'kandidater': [dict(kand_ref, adress='http://10.0.0.5/')]}, 'riktigt värdnamn'), ({'kandidater': [dict(kand_ref, adress='http://0x7f000001:4999/x')]}, 'riktigt värdnamn'),
                      ({'kandidater': [dict(kand_ref, adress='http://127.1/')]}, 'riktigt värdnamn'), ({'kandidater': [dict(kand_ref, adress='http://localhost/')]}, 'riktigt värdnamn'),
                      ({'kandidater': [dict(kand_ref, adress='http://exempel.local/')]}, 'riktigt värdnamn'), ({'kandidater': [dict(kand_ref, adress='https://exempel.se:8443/')]}, 'standardportar'),
                      ({'kandidater': [dict(kand_ref, adress='http://127.0.0.1:%d/' % srv_rc.server_address[1])]}, 'provundantag'),
                      ({'kandidater': [dict(kand_ref, adress='https://exempel.se/projekt/')]}, 'ursprung'), ({'kandidater': [dict(kand_ref, adress=a_ref + '/x')]}, 'ursprung'),
                      ({'kandidater': [dict(kand_ref, sidor=['/a#b'])]}, 'rotrelativa'), ({'kandidater': [dict(kand_ref, ersatt='ja')]}, 'ersatt'),
                      ({'kandidater': [dict(kand_ref, roll='annat')]}, 'roll'), ({'kandidater': [dict(kand_ref, sidor=['priser'])]}, 'börjar med /'),
                      ({'kandidater': [dict(kand_ref, meny='x' * 300)]}, 'CSS-väljare'), ({'kandidater': [dict(kand_ref, namn='k%d' % i_) for i_ in range(13)]}, 'högst'),
                      ({'kandidater': [kand_ref], 'kompletterar': 'x'}, 'paket-vNN')):
    (u_ref / 'prov-ref' / 'DALIGT.json').write_text(json.dumps(dalig_))
    u_, fel_ = rf_.las_uppdrag(u_ref / 'prov-ref' / 'DALIGT.json', 'prov-ref', lok_ref); assert u_ is None and skal_ in fel_, (dalig_, fel_)
assert rf_.kanon_adress('https://Exempel.SE')[0] == 'https://exempel.se/' and 'ursprung' in rf_.kanon_adress('https://Exempel.SE/sida?x=1#f')[1] and rf_.kanon_adress('https://xn--lule-snickaren-oib.se/')[1] is None and rf_.kanon_adress('ftp://x.se/')[1]
assert rf_.tillatet_resursursprung(c_ref + '/b.png', lok_ref) is None and rf_.tillatet_resursursprung(b_ref + '/b.png', lok_ref) == b_ref and rf_.tillatet_resursursprung('https://cdn.exempel.se/f.woff2', ()) == 'https://cdn.exempel.se' and rf_.tillatet_resursursprung('https://www.google-analytics.com/x.js', ()) is None and rf_.tillatet_resursursprung('http://0x7f000001/x', ()) is None
assert rf_.sidkatalog(1, '/a/b') == '02-a-b' and rf_.sidkatalog(2, '/a-b') == '03-a-b' and rf_.sidkatalog(0, '/') == '01-start'
assert rf_.tvillingar('dinesen.com') == {'dinesen.com', 'www.dinesen.com'} and rf_.tvillingar('www.gov.uk') == {'www.gov.uk', 'gov.uk'} and rf_.tvillingar('127.0.0.1') == {'127.0.0.1'} and rf_.kandidat_ursprung('http://dinesen.com/') == ['http://dinesen.com', 'http://www.dinesen.com', 'https://dinesen.com', 'https://www.dinesen.com'] and rf_.kandidat_ursprung(a_ref + '/') == [a_ref], 'www-/bartvillingen och http→https hör till kandidaten (R32/R33)'
assert rf_.sidadress('https://exempel.se/', '/hantverkare/snickare/x') == 'https://exempel.se/hantverkare/snickare/x' and rf_.sidadress('https://exempel.se/', '/') == 'https://exempel.se/' and rf_.sidadress(a_ref + '/', '/a/b') == a_ref + '/a/b', 'sidor löses som rotrelativa vägar mot ursprunget (R33)'
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--uppdrag', str(tmp / 'utanfor.json')]) == 2, 'uppdraget måste ligga under underlag/<slug>'
# skrivmålet förankras före första skrivningen, också i torrkörning: en länkad referenser/ vägras
ute_ref = tmp / 'ref-ute'; ute_ref.mkdir(); (u_ref / 'prov-ref' / 'referenser').symlink_to(ute_ref)
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 2 and not list(ute_ref.iterdir()), 'länkat skrivmål: inget skrivs'
(u_ref / 'prov-ref' / 'referenser').unlink()
# torrkörning: paketet skapas utan att sajterna öppnas
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 0
pk0 = json.load(open(u_ref / 'prov-ref' / 'referenser' / 'paket-v01' / 'PAKET.json')); assert pk0['torr'] and pk0['kandidater'][0]['sidor'] == [] and (u_ref / 'prov-ref' / 'referenser' / 'paket-v01' / 'lokal').is_dir()
# riktig insamling mot de lokala servrarna: pass 1 hittar bildservern som resursursprung, pass 2 laddar bilden, menytillståndet fångas,
# kakdialogen noteras, /a/b och /a-b får egna kataloger, båda kandidaterna fångade
rc_ref = rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]); assert rc_ref == 0, rc_ref
paket_ref = u_ref / 'prov-ref' / 'referenser' / 'paket-v02'
pk = json.load(open(paket_ref / 'PAKET.json')); k_ref = pk['kandidater'][0]
assert pk['version'] == 'paket-v02' and pk['alla_ok'] and k_ref['ok'] and k_ref['resursursprung'] == [b_ref] and pk['kandidater'][1]['ok'], pk
assert [s_['katalog'] for s_ in k_ref['sidor']] == ['lokal/01-start', 'lokal/02-a-b', 'lokal/03-a-b'] and k_ref['sidor'][0]['tillstand'] == {'meny': '#meny'} and k_ref['sidor'][1]['tillstand'] == {}
for s_ in k_ref['sidor']:
    assert s_['ok'] and s_['kvar_blockerade'] == [] and all(o_['status'] == 200 and o_['bilder_laddade'] >= 1 and all(o_['bildfiler'].values()) for o_ in s_['observationer'].values()), s_
    assert any('kakdialog' in b_ for b_ in s_['begransningar']) and 'vy-390-forsta.png' in ' '.join(s_['filer']) and 'vy-1440-ruta-01.png' in ' '.join(s_['filer'])
assert k_ref['sidor'][0]['observationer']['390']['tillstand'] == {'meny': True}
assert (paket_ref / 'lokal' / '01-start' / 'vy-390-meny.png').is_file() and (paket_ref / 'lokal' / '03-a-b' / 'INSPEKTION.json').is_file() and not (paket_ref / 'lokal' / '.pass1').exists()
assert json.load(open(paket_ref / 'lokal' / '02-a-b' / 'INSPEKTION.json'))['adress'].endswith('/a/b') and json.load(open(paket_ref / 'lokal' / '03-a-b' / 'INSPEKTION.json'))['adress'].endswith('/a-b')
md_ref = (paket_ref / 'PAKET.md').read_text(); assert 'Bildval: referenser/paket-v02/' in md_ref and 'resursursprung tillåtna' in md_ref and b_ref in md_ref
# ofullständiga fångster rapporteras som brister, inte som kompletta: 404 på en beställd sida, ett tillstånd som inte lyckas,
# en egen resurs från ett lokalt ursprung utan provundantag (förblir blockerad)
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [
    {'namn': 'fyra', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': '404', 'sidor': ['/', '/saknas']},
    {'namn': 'meny', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'tillstånd', 'sidor': ['/'], 'meny': '#finns-inte'},
    {'namn': 'cres', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'resurs', 'sidor': ['/c']},
    {'namn': 'trasig', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'bild 404', 'sidor': ['/trasig']}]}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]) == 1
pk3 = json.load(open(u_ref / 'prov-ref' / 'referenser' / 'paket-v03' / 'PAKET.json')); k3 = {k_['namn']: k_ for k_ in pk3['kandidater']}
assert not k3['trasig']['ok'] and any(e_['typ'] == 'image' and e_['status'] == 404 for e_ in k3['trasig']['sidor'][0]['fel_resurser']) and any('misslyckades' in b_ for b_ in k3['trasig']['sidor'][0]['begransningar']), 'ett misslyckat bildanrop fäller fångsten med felorsaken bevarad (R33)'
assert not pk3['alla_ok'] and not k3['fyra']['ok'] and k3['fyra']['sidor'][0]['ok'] and not k3['fyra']['sidor'][1]['ok'] and any('status 404' in b_ for b_ in k3['fyra']['sidor'][1]['begransningar']), k3['fyra']
assert not k3['meny']['ok'] and k3['meny']['sidor'][0]['observationer']['390']['tillstand'] == {'meny': False} and any('tillståndet meny' in b_ for b_ in k3['meny']['sidor'][0]['begransningar']), k3['meny']
assert not k3['cres']['ok'] and k3['cres']['resursursprung'] == [] and k3['cres']['sidor'][0]['kvar_blockerade'] and any('förblev blockerade' in b_ for b_ in k3['cres']['sidor'][0]['begransningar']), k3['cres']
# komplettering: ett nytt uppdrag med bara det som saknas ger en komplett ny version: orörda kandidater ärvs hela, och den
# kompletterade kandidatens orörda sidor ärvs sida för sida med sin katalog (R33); ersatt: true byter ut kandidaten helt
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'lokal', 'adress': a_ref + '/', 'roll': 'hantverk', 'varfor': 'mobilmenyn', 'sidor': ['/'], 'meny': '#meny'}], 'kompletterar': 'paket-v02'}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]) == 0
paket4 = u_ref / 'prov-ref' / 'referenser' / 'paket-v04'; pk4 = json.load(open(paket4 / 'PAKET.json')); k4 = {k_['namn']: k_ for k_ in pk4['kandidater']}
assert pk4['kompletterar'] == 'paket-v02' and pk4['alla_ok'] and set(k4) == {'lokal', 'andra'} and k4['andra'].get('arv') == 'paket-v02' and 'arv' not in k4['lokal']
assert (paket4 / 'andra' / '01-start' / 'vy-390-forsta.png').is_file() and (paket4 / 'lokal' / '01-start' / 'vy-390-meny.png').is_file()
assert [(s_['sida'], s_['katalog'], s_.get('arv')) for s_ in k4['lokal']['sidor']] == [('/', 'lokal/01-start', None), ('/a/b', 'lokal/02-a-b', 'paket-v02'), ('/a-b', 'lokal/03-a-b', 'paket-v02')], k4['lokal']['sidor']
assert (paket4 / 'lokal' / '02-a-b' / 'vy-390-forsta.png').is_file() and (paket4 / 'lokal' / '03-a-b' / 'INSPEKTION.json').is_file() and k4['lokal']['resursursprung'] == [b_ref]
assert 'ärvd från paket-v02' in (paket4 / 'PAKET.md').read_text() and 'sidor ärvda från paket-v02: /a/b, /a-b' in (paket4 / 'PAKET.md').read_text()
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'lokal', 'adress': a_ref + '/', 'roll': 'hantverk', 'varfor': 'ersatt', 'sidor': ['/'], 'ersatt': True}], 'kompletterar': 'paket-v04'}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]) == 0
paket5 = u_ref / 'prov-ref' / 'referenser' / 'paket-v05'; k5 = {k_['namn']: k_ for k_ in json.load(open(paket5 / 'PAKET.json'))['kandidater']}
assert [s_['katalog'] for s_ in k5['lokal']['sidor']] == ['lokal/01-start'] and not (paket5 / 'lokal' / '02-a-b').exists() and k5['andra'].get('arv') == 'paket-v04', 'ersatt: fullständig ersättning utan arv'
# en nästlad länk i arvskällan vägras före kopieringen: inget nytt paket, inget läst utanför referensområdet
hemlig_ref = tmp / 'hemlig-ref.txt'; hemlig_ref.write_text('HEMLIGT')
(paket4 / 'andra' / '01-start' / 'lank.txt').symlink_to(hemlig_ref)
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'lokal', 'adress': a_ref + '/', 'roll': 'hantverk', 'varfor': 'x', 'sidor': ['/']}], 'kompletterar': 'paket-v04'}))
antal_ref = len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*')))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 2 and len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))) == antal_ref, 'nästlad länk i arvskällan: vägrat, inget paket'
assert 'HEMLIGT' not in ''.join(p_.read_text(errors='replace') for p_ in (u_ref / 'prov-ref' / 'referenser').rglob('*.txt') if not p_.is_symlink())
(paket4 / 'andra' / '01-start' / 'lank.txt').unlink()
# Codex R34: ett adressbyte under samma kandidatnamn vägras utan ersatt (annars blandas två sajter); www-/bartvilling och http→https är samma referens
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'lokal', 'adress': b_ref + '/', 'roll': 'hantverk', 'varfor': 'byte', 'sidor': ['/']}], 'kompletterar': 'paket-v04'}))
antal_ref = len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*')))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 2 and len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))) == antal_ref, 'adressbyte under samma namn vägras'
assert rf_.samma_referens('http://dinesen.com/', 'https://www.dinesen.com/') and not rf_.samma_referens('https://a.se/', 'https://b.se/') and not rf_.samma_referens(a_ref + '/', b_ref + '/')
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'lokal', 'adress': b_ref + '/', 'roll': 'hantverk', 'varfor': 'byte', 'sidor': ['/'], 'ersatt': True}], 'kompletterar': 'paket-v04'}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 0, 'med ersatt: true får kandidaten byta referens'
# Codex R34: en saknad inspektionsrapport är en dokumenterad brist i ett sparat paket (slutkod 1), inte ett raderat paket
kor_orig_ = rf_.kor_inspektera
def kor_utan_rapport_(adress, ut, tillat, tillstand, miljo, extrahera=None):
    if adress.endswith('/a-b'):
        return 1, {}, 'simulerad: ingen rapport'
    return kor_orig_(adress, ut, tillat, tillstand, miljo, extrahera)
rf_.kor_inspektera = kor_utan_rapport_
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'hel', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'fångas', 'sidor': ['/']}, {'namn': 'utan', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'ingen rapport', 'sidor': ['/a-b']}]}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]) == 1
rf_.kor_inspektera = kor_orig_
paket_sr = sorted((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))[-1]; k_sr = {k_['namn']: k_ for k_ in json.load(open(paket_sr / 'PAKET.json'))['kandidater']}
# riktad designextraktion i samma session som fångsten (Codex 2026-10-04, glapp 2): standard för varje kandidat, uppmätt med källbild
ex_sr = json.loads((paket_sr / 'hel' / '01-start' / 'vy-390-extrakt.json').read_text())
assert ex_sr['matning'] == 'uppmätt' and ex_sr['kallbilder']['forsta'].endswith('vy-390-forsta.png') and ex_sr['element'] and 'sektioner' in ex_sr and 'farger' in ex_sr, list(ex_sr)
assert any(e_.get('typsnitt', {}).get('renderat') for e_ in ex_sr['element']), 'det renderade typsnittet ur Chromium, inte bara den deklarerade stacken'
assert (paket_sr / 'hel' / '01-start' / 'EXTRAKT.md').is_file() and 'extrakt hel/01-start/EXTRAKT.md' in (paket_sr / 'PAKET.md').read_text()
for dalig_x in (['--tillat-alla'], ['-x'], 'allt', ['a;b']):
    (u_ref / 'prov-ref' / 'DALIG.json').write_text(json.dumps({'kandidater': [{'namn': 'x', 'adress': a_ref + '/', 'roll': 'ux', 'extrahera': dalig_x}]}))
    assert rf_.las_uppdrag(u_ref / 'prov-ref' / 'DALIG.json', 'prov-ref', tuple(int(x_) for x_ in portar_ref.split(',')))[1], 'väljare som börjar med - eller innehåller ; vägras: %r' % (dalig_x,)
(u_ref / 'prov-ref' / 'DALIG.json').write_text(json.dumps({'kandidater': [{'namn': 'x', 'adress': a_ref + '/', 'roll': 'ux', 'meny': '--undantag-fil=/x'}]}))
assert rf_.las_uppdrag(u_ref / 'prov-ref' / 'DALIG.json', 'prov-ref', tuple(int(x_) for x_ in portar_ref.split(',')))[1], 'ett tillstånd som börjar med - vägras'
assert k_sr['hel']['ok'] and (paket_sr / 'hel' / '01-start' / 'vy-390-forsta.png').is_file() and not k_sr['utan']['ok'] and k_sr['utan']['sidor'][0]['fel_resurser'] == [] and any('ingen rapport' in b_ for b_ in k_sr['utan']['sidor'][0]['begransningar']), k_sr['utan']
# Codex R34: ofullständigt arv godkänns aldrig: inventeringsfel, saknad deklarerad bild och saknad orörd kandidat vägras
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'lokal', 'adress': a_ref + '/', 'roll': 'hantverk', 'varfor': 'x', 'sidor': ['/']}], 'kompletterar': 'paket-v04'}))
antal_ref = len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*')))
os.chmod(paket4 / 'andra' / '01-start', 0o000)
try:
    rc_arv = rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref])
finally:
    os.chmod(paket4 / 'andra' / '01-start', 0o755)
assert rc_arv == 2 and len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))) == antal_ref, 'inventeringsfel i arvskällan vägras'
bild_arv = paket4 / 'andra' / '01-start' / 'vy-1440-forsta.png'; bild_arv.rename(bild_arv.with_suffix('.borta'))
try:
    assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 2 and len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))) == antal_ref, 'saknad deklarerad bild i arvet vägras'
finally:
    bild_arv.with_suffix('.borta').rename(bild_arv)
shutil.move(str(paket4 / 'andra'), str(tmp / 'andra-undan'))
try:
    assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 2 and len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))) == antal_ref, 'saknad orörd kandidat i arvet vägras, hoppas inte över'
finally:
    shutil.move(str(tmp / 'andra-undan'), str(paket4 / 'andra'))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 0, 'återställt arv går igenom'
# Codex R35/R36, kontraktet för första passet: ett fel där raderar aldrig paketet och fäller inte kandidaten i sig. En sida med bara egna
# resurser återhämtar sig i andra passet (fångad, med anmärkning); en sida som behövde ett resursursprung som inte upptäcktes fälls i andra
# passet av den blockerade egna resursen, inte av första-pass-felet. Tidigare fångster bevaras.
def kor_pass1_faller_(adress, ut, tillat, tillstand, miljo, extrahera=None):
    if str(ut).endswith('.pass1') and ('/a-b' in adress or '/egen' in adress):
        raise subprocess.TimeoutExpired(['node'], 1)
    return kor_orig_(adress, ut, tillat, tillstand, miljo, extrahera)
rf_.kor_inspektera = kor_pass1_faller_
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'hel', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'fångas', 'sidor': ['/']},
    {'namn': 'pass1', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'pass 1 faller, bild från annat ursprung', 'sidor': ['/a-b']},
    {'namn': 'pass1egen', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'pass 1 faller, bara egna resurser', 'sidor': ['/egen']}]}))
rc_p1 = rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref])
paket_p1 = sorted((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))[-1]; k_p1 = {k_['namn']: k_ for k_ in json.load(open(paket_p1 / 'PAKET.json'))['kandidater']}
assert rc_p1 == 1 and k_p1['hel']['ok'] and (paket_p1 / 'hel' / '01-start' / 'vy-390-forsta.png').is_file(), 'paketet sparat, första fångsten kvar'
assert not k_p1['pass1']['ok'] and k_p1['pass1']['resursursprung'] == [] and k_p1['pass1']['sidor'][0]['kvar_blockerade'] and any('första passet' in b_ for b_ in k_p1['pass1']['anmarkningar']), ('fälls av den blockerade egna resursen i andra passet', k_p1['pass1'])
assert k_p1['pass1egen']['ok'] and k_p1['pass1egen']['sidor'][0]['kvar_blockerade'] == [] and any('första passet' in b_ for b_ in k_p1['pass1egen']['anmarkningar']) and 'anmärkning (fäller inte i sig): första passet' in (paket_p1 / 'PAKET.md').read_text(), ('återhämtning i andra passet', k_p1['pass1egen'])
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'pass1egen', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'bara egna resurser', 'sidor': ['/egen']}]}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]) == 0, 'bara egna resurser: första-pass-felet ensamt ger slutkod 0'
rf_.kor_inspektera = kor_orig_
# Codex R35: en bild som försvinner mellan observationen och inventeringen fäller sidan, och bristen dokumenteras
obs_orig_ = rf_.observationer
def obs_tar_bort_bild_(rapport, ut, bestallda=()):
    o_ = obs_orig_(rapport, ut, bestallda)
    (Path(ut) / 'vy-390-forsta.png').unlink(missing_ok=True)
    return o_
rf_.observationer = obs_tar_bort_bild_
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'bildbort', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'x', 'sidor': ['/']}]}))
rc_bb = rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]); rf_.observationer = obs_orig_
k_bb = json.load(open(sorted((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))[-1] / 'PAKET.json'))['kandidater'][0]
assert rc_bb == 1 and not k_bb['ok'] and k_bb['sidor'][0]['observationer']['390']['bildfiler']['vy-390-forsta.png'] is False and any('saknas i inventeringen' in b_ for b_ in k_bb['sidor'][0]['begransningar']), k_bb['sidor'][0]
# Codex R35: ett torrpaket kan inte ärvas som fångst i en riktig insamling; ärvt inlägg utan filer räknas aldrig som fångat
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'ta', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'x', 'sidor': ['/']}, {'namn': 'tb', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'x', 'sidor': ['/']}]}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 0
torr_v = sorted((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))[-1].name
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [{'namn': 'ta', 'adress': a_ref + '/', 'roll': 'ux', 'varfor': 'x', 'sidor': ['/']}], 'kompletterar': torr_v}))
antal_ref = len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*')))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--tillat-lokalt', portar_ref]) == 2 and len(list((u_ref / 'prov-ref' / 'referenser').glob('paket-v*'))) == antal_ref, 'torrpaket som arvskälla vägras'
assert not rf_.arvd_ok([]) and not rf_.arvd_ok([{'ok': True, 'filer': [], 'observationer': {}}]) and rf_.arvd_ok(k4['andra']['sidor'])
assert not rf_.samma_referens('https://a.se/', 'https://www.www.a.se/') and rf_.samma_referens('https://a.se/', 'https://www.a.se/') and rf_.samma_referens('http://www.a.se/', 'https://a.se/'), 'bara den direkta www-tvillingrelationen (R35)'
(u_ref / 'prov-ref' / 'REFERENSUPPDRAG.json').write_text(json.dumps({'kandidater': [kand_ref], 'kompletterar': 'paket-v29'}))
assert rf_.main(['prov-ref', '--underlag', str(u_ref), '--torr', '--tillat-lokalt', portar_ref]) == 2, 'ett paket som inte finns kan inte kompletteras'
# Bildval i REFERENSER.md pekar in i den nya versionen, också för det ärvda materialet, och löses av referensval
(u_ref / 'prov-ref' / 'REFERENSER.md').write_text('## andra\n\nBildval: referenser/paket-v04/andra/01-start/vy-390-ruta-01.png — startsidan — Fråga: hur tät är listan?\n## lokal\n\nBildval: referenser/paket-v04/lokal/01-start/vy-390-meny.png — mobilmenyn — Fråga: hur öppnas den?\n')
import referensval as rv_ref  # noqa: E402
bv_ = rv_ref.bildval('prov-ref', u_ref); assert len(bv_) == 2 and all(b_['fel'] is None and b_['fil'].is_file() for b_ in bv_) and rv_ref.referensnamn(bv_[0]['rel']) == 'paket-v04'
# tjänstens verktyg referens: byggets slug och uppdrag under underlag/<slug>; annat vägras
rot_ref = tmp / 'ref-rot'; (rot_ref / 'underlag' / 'prov-bygge').mkdir(parents=True); (rot_ref / 'kunder' / 'prov-bygge').mkdir(parents=True)
(rot_ref / 'underlag' / 'prov-bygge' / 'REFERENSUPPDRAG.json').write_text('{}')
ga_ref = lambda a_: wt.granska_anrop('referens', a_, 'prov-bygge', ['exempel.se'], rot_ref, 'K1', lambda adr_, k_: (True, None))  # noqa: E731
kmd_ref, fel_ref = ga_ref(['prov-bygge', '--uppdrag', 'underlag/prov-bygge/REFERENSUPPDRAG.json']); assert fel_ref is None and 'referens.py' in ' '.join(kmd_ref), fel_ref
assert ga_ref(['annan', '--uppdrag', 'underlag/prov-bygge/REFERENSUPPDRAG.json'])[1] and ga_ref(['prov-bygge', '--uppdrag', '/etc/passwd'])[1] and ga_ref(['prov-bygge', '--underlag', str(tmp)])[1] and ga_ref(['prov-bygge', '--tillat-lokalt', '80'])[1]
assert ga_ref(['prov-bygge', '--torr'])[1] is None
# sandlådat läge: steget delegeras till tjänsten i stället för att köras i byggsessionen (här: tjänsten nås inte → slutkod 2, inget paket)
r_del = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'referens.py'), 'prov-ref'], capture_output=True, text=True, cwd=str(ROOT), timeout=60,
                       env=dict(os.environ, NWP_WEBBTJANST='http://127.0.0.1:1', NWP_WEBBTJANST_NYCKEL='x', NWP_PROCESSGRANS='1', NWP_SLUG='prov-ref'))
assert r_del.returncode == 2 and 'nås inte' in (r_del.stdout + r_del.stderr), (r_del.returncode, r_del.stdout[-200:], r_del.stderr[-200:])
import sandlada as sl_ref  # noqa: E402
assert wt.tillaten_vard('assets.awwwards.com', wt.tillatna_varden(sl_ref.domanlista(ROOT))) and not wt.tillaten_vard('evil.example', wt.tillatna_varden(sl_ref.domanlista(ROOT))), 'jokertecknet för awwwards (belagt behov)'
assert 'referens.py' in (ROOT / 'kor.sh').read_text() and 'REFERENSUPPDRAG.json' in (ROOT / '.claude' / 'skills' / 'bygg-sajt' / 'SKILL.md').read_text()
srv_ra.shutdown(); srv_rb.shutdown(); srv_rc.shutdown()
print('referenssteget ok')

# ---------------------------------------------------------------- referenstjänsterna som belägg (designprovets punkt 1): anropen räknas ur sessionsloggen, inte ur
# modellens uppgift; bilder laddas bara från tjänstens egna bildvärdar (här: lokalt provundantag) och landar i paketet; utan verkliga anrop ingen ok
import referenstjanster as rt_  # noqa: E402
srv_rt = hs_.HTTPServer(('127.0.0.1', 0), RefBild_); th_.Thread(target=srv_rt.serve_forever, daemon=True).start()
rt_port = srv_rt.server_address[1]; rt_bild = 'http://127.0.0.1:%d/skarm.png' % rt_port
u_rt = tmp / 'rt-underlag'; (u_rt / 'prov-rt').mkdir(parents=True)
(u_rt / 'prov-rt' / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provfirman'}))
stilar_rt_ = []
def logg_rt_(logg, anrop, traffar, subtype='success'):
    rader = [json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': n, 'input': {}}]}}) for n in anrop]
    rader.append(json.dumps({'type': 'result', 'subtype': subtype, 'is_error': subtype != 'success', 'num_turns': len(anrop) + 1, 'structured_output': {'anrop': [{'verktyg': 'påstått', 'argument': 'x', 'resultat_typ': 'json'}] * 9, 'traffar': traffar, 'stilar': stilar_rt_, 'anmarkning': 'prov'}}))
    Path(logg).write_text('\n'.join(rader) + '\n')
def kor_rt_ok_(tjanst, prompt, logg, modell):
    assert 'Provfirman' in prompt and tjanst in ('refero', 'mobbin')
    bildvard = rt_bild if tjanst == 'mobbin' else 'https://images.refero.design/skarm.png'
    logg_rt_(logg, ['mcp__%s__%s' % (tjanst, 'search_screens' if tjanst == 'mobbin' else 'refero_search_screens')] * 2,
             [{'id': 'A 1', 'titel': 'Träff', 'sida_url': 'https://x.se/', 'bild_url': bildvard, 'beskrivning': 'b', 'fraga': 'f'},
              {'id': 'B', 'titel': 'Främmande', 'sida_url': 'https://y.se/', 'bild_url': 'http://127.0.0.1:1/x.png', 'beskrivning': 'b', 'fraga': 'f'},
              {'id': 'C', 'titel': 'Utan bild', 'sida_url': 'https://z.se/', 'bild_url': '', 'beskrivning': 'b', 'fraga': 'f'}])
    return 0, ''
upp_rt = {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form', 'syfte': 'x'}, {'tjanst': 'refero', 'fraga': 'editorial', 'syfte': ''}]}
assert rt_.las_uppdrag(tmp / 'finns-inte.json')[1], 'saknat uppdrag vägras'
(u_rt / 'prov-rt' / 'TJANSTEUPPDRAG.json').write_text(json.dumps(upp_rt))
for dalig_, skal_ in (({'fragor': []}, 'behöver'), ({'fragor': [{'tjanst': 'okand', 'fraga': 'x'}]}, 'tjanst'), ({'fragor': [{'tjanst': 'mobbin', 'fraga': 'x'}]}, 'tecken'), ({'fragor': [{'tjanst': 'mobbin', 'fraga': 'x' * 300}]}, 'tecken')):
    (u_rt / 'prov-rt' / 'DALIGT.json').write_text(json.dumps(dalig_)); assert skal_ in (rt_.las_uppdrag(u_rt / 'prov-rt' / 'DALIGT.json')[1] or ''), dalig_
rot_rt, res_rt = rt_.samla('prov-rt', upp_rt, u_rt, lokala_portar=(rt_port,), kor=kor_rt_ok_)
m_ = res_rt['tjanster']['mobbin']; r_ = res_rt['tjanster']['refero']
assert m_['ok'] and m_['anrop'] == {'mcp__mobbin__search_screens': 2} and m_['bilder'] == 1, m_
assert [(t_['id'], bool(t_['fil']), t_['fel']) for t_ in m_['traffar']] == [('A-1', True, None), ('B', False, 'bildadressen ligger inte på tjänstens bildvärd; laddas inte'), ('C', False, 'ingen bildadress från tjänsten')], m_['traffar']
assert (u_rt / 'prov-rt' / m_['traffar'][0]['fil']).read_bytes() == png_ref and m_['traffar'][0]['sha256'] and 'påstått' not in json.dumps(m_['anrop'])
assert not r_['ok'] and r_['anrop'] == {'mcp__refero__refero_search_screens': 2} and r_['bilder'] == 0 and any('inga bilder' in a_ for a_ in r_['anmarkningar']), 'refero-bilden ligger på riktig bildvärd som provet inte når: brist, inte ok'
assert not res_rt['alla_ok'] and (rot_rt / 'TJANSTER.json').is_file() and 'anrop: search_screens ×2' in (rot_rt / 'TJANSTER.md').read_text()
def kor_rt_tom_(tjanst, prompt, logg, modell):
    logg_rt_(logg, [], [{'id': 'X', 'titel': 't', 'sida_url': 'https://x.se/', 'bild_url': rt_bild, 'beskrivning': 'b', 'fraga': 'f'}]); return 0, ''
rot_rt, res_rt = rt_.samla('prov-rt', {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form', 'syfte': ''}]}, u_rt, lokala_portar=(rt_port,), kor=kor_rt_tom_)
assert not res_rt['tjanster']['mobbin']['ok'] and any('inga verkliga verktygsanrop' in a_ for a_ in res_rt['tjanster']['mobbin']['anmarkningar']), 'påstådda anrop utan logg räknas inte'
def kor_rt_faller_(tjanst, prompt, logg, modell):
    Path(logg).write_text(''); return 1, 'sessionen föll'
rot_rt, res_rt = rt_.samla('prov-rt', {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form', 'syfte': ''}]}, u_rt, lokala_portar=(rt_port,), kor=kor_rt_faller_)
assert not res_rt['tjanster']['mobbin']['ok'] and any('inget giltigt svar' in a_ for a_ in res_rt['tjanster']['mobbin']['anmarkningar'])
rot_rt, res_rt = rt_.samla('prov-rt', upp_rt, u_rt, torr=True, kor=kor_rt_faller_); assert res_rt['torr'] and not res_rt['alla_ok']
assert rt_.tillaten_bild('https://images.refero.design/a.png', 'refero') and not rt_.tillaten_bild('https://images.refero.design.evil/a.png', 'refero') and not rt_.tillaten_bild('http://images.refero.design/a.png', 'refero') and rt_.tillaten_bild('https://mobbin.com/api/mcp/short/x', 'mobbin') and not rt_.tillaten_bild('https://mobbin.com/x', 'refero')
assert rt_.main(['prov-rt', '--underlag', str(u_rt), '--uppdrag', str(tmp / 'utanfor.json')]) == 2
ga_rt = lambda a_: wt.granska_anrop('referenstjanster', a_, 'prov-bygge', ['exempel.se'], rot_ref, 'K1', lambda adr_, k_: (True, None))  # noqa: E731
(rot_ref / 'underlag' / 'prov-bygge' / 'TJANSTEUPPDRAG.json').write_text('{}')
assert ga_rt(['prov-bygge', '--uppdrag', 'underlag/prov-bygge/TJANSTEUPPDRAG.json'])[1] is None and ga_rt(['annan'])[1] and ga_rt(['prov-bygge', '--modell', 'x'])[1]
# Referos stilar (Codex 2026-10-04, glapp 3): typen stil bara hos refero; värdena strukturerade; belagda bara med get_style i loggen
(u_rt / 'prov-rt' / 'STIL.json').write_text(json.dumps({'fragor': [{'tjanst': 'mobbin', 'fraga': 'warm craft', 'typ': 'stil'}]}))
assert 'stil finns bara hos refero' in (rt_.las_uppdrag(u_rt / 'prov-rt' / 'STIL.json')[1] or ''), 'mobbin har inga stilar'
(u_rt / 'prov-rt' / 'STIL.json').write_text(json.dumps({'fragor': [{'tjanst': 'refero', 'fraga': 'warm editorial craft', 'typ': 'stil'}]}))
upp_stil, fel_stil = rt_.las_uppdrag(u_rt / 'prov-rt' / 'STIL.json'); assert not fel_stil and upp_stil['fragor'][0]['typ'] == 'stil'
assert 'refero_get_style' in rt_.prompt_for('refero', upp_stil['fragor'], 'Provfirman') and 'refero_get_style' not in rt_.prompt_for('refero', [dict(upp_stil['fragor'][0], typ='skarm')], 'Provfirman')
stilar_rt_[:] = [{'id': 'S 1', 'titel': 'GTE', 'sida_url': 'https://www.gte.xyz', 'bild_url': rt_bild, 'typografi': 'serif display 72/1.0, mono labels 12', 'farger': 'carbon #111, polar #fff, turbo orange accent',
                  'layout': 'centered hero, two-column blocks', 'rytm': 'dense hero, airy blocks', 'komponenter': 'soft-bordered cards', 'fraga': 'warm editorial craft'}]
def kor_rt_stil_(tjanst, prompt, logg, modell):
    logg_rt_(logg, ['mcp__refero__refero_search_styles', 'mcp__refero__refero_get_style'], []); return 0, ''
rot_rt, res_rt = rt_.samla('prov-rt', upp_stil, u_rt, lokala_portar=(rt_port,), kor=kor_rt_stil_)
st_ = res_rt['tjanster']['refero']
assert st_['ok'] and st_['stilar'][0]['typografi'].startswith('serif display') and st_['stilar'][0]['fil'] and not st_['stilar'][0]['fel'], st_
assert '### Stil: GTE' in (rot_rt / 'TJANSTER.md').read_text() and '- färger: carbon #111' in (rot_rt / 'TJANSTER.md').read_text()
def kor_rt_stil_utan_(tjanst, prompt, logg, modell):
    logg_rt_(logg, ['mcp__refero__refero_search_styles'], []); return 0, ''
rot_rt, res_rt = rt_.samla('prov-rt', upp_stil, u_rt, lokala_portar=(rt_port,), kor=kor_rt_stil_utan_)
st_ = res_rt['tjanster']['refero']
assert not st_['ok'] and 'inget get_style-anrop' in st_['stilar'][0]['fel'] and any('utan refero_get_style' in a_ for a_ in st_['anmarkningar']), 'påstådda stilvärden utan get_style är inte belagda'
stilar_rt_[:] = []
srv_rt.shutdown()
print('referenstjänsterna ok')

# ---------------------------------------------------------------- designkontraktet (Codex 2026-10-04, glapp 1): DESIGN.md → design.css → sajtens CSS


def designkontraktet():
    import design as dz
    import referensval as rv_dz
    kz, uz = tmp / 'kunder-dz', tmp / 'underlag-dz'
    sajt_dz = kz / 'dz' / 'sajt'
    (sajt_dz / 'dist').mkdir(parents=True)
    gamla_dz = (dz.KUNDER, dz.UNDERLAG)
    dz.KUNDER, dz.UNDERLAG = kz, uz
    try:
        v_dz = {'schema': 1, 'huvudreferens': 'Snick',
                'farger': {'yta': {'varde': '#ffffff', 'roll': 'yta', 'kalla': 'uppmätt: paket-v01/snick/01-start EXTRAKT 1440'},
                           'text': {'varde': '#111111', 'roll': 'text', 'kalla': 'valt: kontrast'},
                           'svag': {'varde': '#eeeeee', 'roll': 'linjer', 'kalla': 'uppskattat: ur bilden'}},
                'typsnitt': {'rubrik': {'familj': 'Fraunces Variable', 'reserv': 'Georgia, serif', 'vikt': 600, 'storlek': 'clamp(2rem, 1rem + 4vw, 4rem)', 'radavstand': '1.05', 'kalla': 'uppskattat: ur bilden'},
                             'brodtext': {'familj': 'system-ui', 'reserv': 'sans-serif', 'vikt': 400, 'storlek': '1rem', 'radavstand': '1.5', 'kalla': 'valt: läsbarhet'}},
                'avstand': {'m': '1rem'}, 'spalter': {'1440': {'antal': 12, 'maxbredd': '1280px'}},
                'kontrast': [['text', 'yta', 4.5]], 'avvikelser': []}
        md_dz = lambda v: '# DESIGN.md\n\nProsa.\n\n```json design\n%s\n```\n' % json.dumps(v, ensure_ascii=False, indent=1)  # noqa: E731
        assert dz.validera(v_dz) == [], dz.validera(v_dz)
        css_dz = dz.css(v_dz)
        assert "--typ-rubrik-familj: 'Fraunces Variable', Georgia, serif;" in css_dz and '--typ-brodtext-familj: system-ui, sans-serif;' in css_dz, 'generiska nyckelord citeras aldrig'
        assert '--farg-yta: #ffffff;' in css_dz and '--spalt-1440-antal: 12;' in css_dz and dz.blockhash(v_dz) in css_dz.splitlines()[0]
        # fientliga och ofullständiga värden
        ond = json.loads(json.dumps(v_dz))
        ond['farger']['yta']['varde'] = 'red;}body{x'; ond['typsnitt']['rubrik']['familj'] = "x'; } body {"; ond['typsnitt']['rubrik']['vikt'] = 950
        ond['typsnitt']['brodtext']['kalla'] = 'gissat'; ond['spalter'] = {'mobil': 1}; ond['kontrast'] = [['text', 'saknas', 3]]; ond['typsnitt']['brodtext']['matt'] = 'url(x)'
        fel_dz = ' | '.join(dz.validera(ond))
        for krav_dz in ('farger.yta: varde ska vara hex', 'typsnitt.rubrik: familj', 'vikt ska vara', 'typsnitt.brodtext: kalla', 'spalter.mobil', 'kontrast: varje par', 'matt ska vara'):
            assert krav_dz in fel_dz, (krav_dz, fel_dz)
        # normeringen följer minifierarens omskrivningar (Vite/lightningcss): granskningen av r54b, punkt 1
        for a_, b_ in (('0.5rem', '.5rem'), ('-0.02em', '-.02em'), ('1.50', '1.5'), ('#ffd700', 'gold'), ('#FFFFFF', '#fff'), ('0px', '0'),
                       ("'Fraunces Variable', Georgia, serif", '"Fraunces Variable",Georgia,serif'), ('clamp(0.875rem, 0.8rem + 0.3vw, 1rem)', 'clamp(.875rem,.8rem + .3vw,1rem)')):
            assert dz.normera('x', a_) == dz.normera('x', b_), (a_, b_)
        assert dz.normera('x', '#cc0000') != dz.normera('x', 'red') and dz.normera('x', '1.5rem') != dz.normera('x', '15rem')
        assert dz.validera(dict(v_dz, avstand={'s': '.5rem', 'h': '100svh'})) == [], 'kortformer och nya enheter godtas'
        trasig = dict(v_dz, farger=[{'varde': '#fff'}])
        (sajt_dz / 'DESIGN.md').write_text(md_dz(trasig)); k_tr = dz.kontroll('dz')
        assert not k_tr['ok'] and k_tr['fel'], 'en lista i stället för objekt ger en röd grind, aldrig ett undantag'
        (sajt_dz / 'DESIGN.md').write_bytes(b'\xff\xfe trasig')
        assert 'kunde inte läsas' in dz.kontroll('dz')['fel'][0]
        (sajt_dz / 'DESIGN.md').write_text(md_dz(v_dz).replace('\n', '\r\n'))
        assert dz.las((sajt_dz / 'DESIGN.md').read_text())[1] == [], 'CRLF läses'
        (sajt_dz / 'DESIGN.md').unlink()
        lag = json.loads(json.dumps(v_dz)); lag['farger']['text']['varde'] = '#dddddd'
        assert any('under 4.5:1' in x for x in dz.validera(lag)), 'kontrastparet prövas'
        assert dz.las('ingen kod')[1] and dz.las(md_dz(v_dz) + md_dz(v_dz))[1] and dz.las('```json design\n[1]\n```\n')[1], 'exakt ett block, ett objekt'
        # kontrollen som provets grind använder
        assert not dz.kontroll('dz')['ok'] and 'saknas' in dz.kontroll('dz')['fel'][0]
        (sajt_dz / 'DESIGN.md').write_text(md_dz(v_dz))
        k1 = dz.kontroll('dz')
        assert not k1['ok'] and any('design.css saknas' in x for x in k1['fel']), k1
        assert dz.main(['dz', '--skriv']) == 0 and not dz.kontroll('dz')['ok'] and dz.main(['dz']) == 1, 'skrivningen lyckas; giltig men oanvänd: kontrollen röd'
        assert (sajt_dz / 'src' / 'styles' / 'design.css').read_text() == css_dz
        (sajt_dz / 'dist' / 'index.html').write_text('<style>body{color:var(--farg-text);background:var(--farg-yta);font-family:var(--typ-brodtext-familj)}h1{font-size:var(--typ-rubrik-storlek)}</style>')
        assert any('följer inte med i bygget' in x for x in dz.kontroll('dz')['fel']), 'variablerna måste vara definierade i den byggda CSS:en'
        (sajt_dz / 'dist' / '_astro').mkdir()
        minifierad = css_dz.split('\n', 1)[1].replace('#ffffff', '#fff').replace(': ', ':').replace(', ', ',').replace('\n', '')  # som Vite skriver om den
        (sajt_dz / 'dist' / '_astro' / 'Bas.abc.css').write_text(minifierad)
        (sajt_dz / 'dist' / 'index.html').write_text('<link rel="stylesheet" href="/_astro/Bas.abc.css"><style>body{color:var(--farg-text);background:var(--farg-yta);font-family:var(--typ-brodtext-familj)}h1{font-size:var(--typ-rubrik-storlek)}</style>')
        k2 = dz.kontroll('dz')
        assert k2['ok'] and any('svag' in x for x in k2['info']) and k2['sha'] == dz.blockhash(v_dz), k2
        (sajt_dz / 'dist' / 'om').mkdir(); (sajt_dz / 'dist' / 'om' / 'index.html').write_text('<style>:root{--farg-text:#222222}</style>')
        assert any('omdefinierade' in x and 'farg-text' in x for x in dz.kontroll('dz')['fel']), 'en omdefinierad variabel fälls (granskningen av r54, punkt 4)'
        (sajt_dz / 'dist' / 'om' / 'index.html').write_text('<style>p{color:var(--farg-text);font-family:var(--typ-brodtext-familj)}</style>')
        (sajt_dz / 'dist' / 'index.html').write_text('<link rel="stylesheet" href="/_astro/Bas.abc.css"><style>body{color:#111}</style>')
        assert any('startsidans CSS' in x for x in dz.kontroll('dz')['fel']), 'variablerna måste användas av startsidan, inte bara av en undersida'
        (sajt_dz / 'dist' / 'index.html').write_text('<link rel="stylesheet" href="/_astro/Bas.abc.css"><style>body{color:var(--farg-text);background:var(--farg-yta);font-family:var(--typ-brodtext-familj)}h1{font-size:var(--typ-rubrik-storlek)}</style>')
        assert dz.kontroll('dz')['ok']
        (sajt_dz / 'src' / 'styles' / 'design.css').write_text(css_dz.replace('#ffffff', '#fefefe'))
        assert any('inte genererad ur den aktuella' in x for x in dz.kontroll('dz')['fel']), 'handredigerad design.css fälls'
        dz.main(['dz', '--skriv'])
        bevara_dz = (sajt_dz / 'dist' / 'index.html').read_text(); (sajt_dz / 'dist' / 'om' / 'index.html').unlink()
        (sajt_dz / 'dist' / 'index.html').write_text('<style>body{color:#111}</style>')
        assert any('använder inte DESIGN.md:s variabler' in x for x in dz.kontroll('dz')['fel'])
        (sajt_dz / 'dist' / 'index.html').write_text(bevara_dz)
        # huvudreferensen i REFERENSER.md måste vara DESIGN.md:s
        (uz / 'dz' / 'referenser' / 'paket-v01' / 'snick' / '01-start').mkdir(parents=True)
        (uz / 'dz' / 'referenser' / 'paket-v01' / 'snick' / '01-start' / 'vy-390-ruta-01.png').write_bytes(b'x')
        (uz / 'dz' / 'REFERENSER.md').write_text('## Annan — x\n\nBildval: referenser/paket-v01/snick/01-start/vy-390-ruta-01.png — v — Fråga: f\n\nHuvudreferens: Annan — allt\n')
        assert rv_dz.huvudreferens('dz', uz)['namn'] == 'Annan' and any('huvudreferens' in x for x in dz.kontroll('dz')['fel']), 'fel huvudreferens fälls'
        (uz / 'dz' / 'REFERENSER.md').write_text('## Snick — x\n\nBildval: referenser/paket-v01/snick/01-start/vy-390-ruta-01.png — v — Fråga: f\n\nHuvudreferens: Snick — allt\n')
        assert dz.kontroll('dz')['ok'], dz.kontroll('dz')
        # jämförelsen med byggets mätning: renderat typsnitt och stora ytor
        ex_dz = tmp / 'extrakt-dz'; ex_dz.mkdir()
        (ex_dz / 'vy-1440-extrakt.json').write_text(json.dumps({'element': [{'id': 'h1#0', 'tagg': 'h1', 'typsnitt': {'renderat': [{'familj': 'Times', 'eget': False}]}},
                                                                           {'id': 'main p#0', 'tagg': 'p', 'typsnitt': {'renderat': [{'familj': 'System Font', 'eget': False}]}}],
                                                                'farger': [{'varde': '#000000', 'andel': 0.6}, {'varde': '#ffffff', 'andel': 0.3}]}))
        avv = dz.jamfor(v_dz, ex_dz)
        assert any('rubrik' in x and 'Times' in x for x in avv) and any('#000000' in x for x in avv) and not any('#ffffff' in x for x in avv), avv
        assert not any('brodtext' in x for x in avv), 'system-ui i DESIGN.md matchar plattformens systemtypsnitt (eget: false)'
        kort = json.loads(json.dumps(v_dz)); kort['farger']['yta']['varde'] = '#fff'
        assert not any('#ffffff' in x for x in dz.jamfor(kort, ex_dz)), '#fff i DESIGN.md är samma yta som #ffffff i mätningen'
    finally:
        dz.KUNDER, dz.UNDERLAG = gamla_dz
    # mallen bär en tom design.css som Bas.astro importerar; rökprovets testsajt har en riktig DESIGN.md
    assert 'Ingen design än' in (ROOT / 'mall' / 'astro' / 'src' / 'styles' / 'design.css').read_text() and "import '../styles/design.css'" in (ROOT / 'mall' / 'astro' / 'src' / 'layouts' / 'Bas.astro').read_text()
    v_rp, fel_rp = dz.las((ROOT / 'kontroller' / 'rokprov' / 'DESIGN.md').read_text())
    assert not fel_rp and dz.validera(v_rp) == [], 'rökprovets DESIGN.md är giltig'
    print('designkontraktet ok')


designkontraktet()


shutil.rmtree(tmp, ignore_errors=True)
print('revisionens regressionsfall: alla ok')
