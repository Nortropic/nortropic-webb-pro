#!/usr/bin/env python3
"""Regressionsfall ur revisionen 2026-10-03 (Codex, nio omgångar): varje skydd prövas genom sin riktiga ingång, med ett
positivt och ett negativt fall, isolerat och syntetiskt. Körs av kontroller/rokprov.sh. Argument: repots rot. Skriver
bara i temporära kataloger och i /tmp/nwp-granskning (granskarens arbetskataloger)."""
import functools
import http.client
import http.server
import json
import os
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
upp = {'metod_sha': m1, 'modell': 'opus[1m]', 'effort': 'high', 'granskare': 2, 'originalitet': 'skugga'}
assert gr.samma_metod(dict(upp), upp) and not gr.samma_metod(dict(upp, granskare=1), upp) and not gr.samma_metod({}, upp)
# falsk claude: svarar som granskare; PROV_FALL styr vem som faller
bin_ = tmp / 'bin'; bin_.mkdir()
krit = json.dumps({n: {'betyg': 8, 'motivering': '', 'visa': True} for n in gr.KRITERIER})
(bin_ / 'claude').write_text('''#!/bin/bash
cat >/dev/null
alla="$*"
case "$PROV_FALL" in
  granskare2) [[ "$alla" == *"-runda-01-2 "* ]] && { echo '{"is_error": true, "result": "föll"}'; exit 1; };;
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
    (arot / str(n)).mkdir(parents=True); (arot / str(n) / 'vy-390-ruta-01.png').write_bytes(b'x'); (arot / str(n) / 'vy-1440-ruta-01.png').write_bytes(b'x')
(arot / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): ['vy-390-ruta-01.png', 'vy-1440-ruta-01.png'] for n in (1, 2, 3)}}))  # det här försökets riktningar (omgång elva, F34)
a.ROOT = tmp; a.KUNDER = k; a.UNDERLAG = tmp / 'underlag'
svar_per_domare = {}


def attrapp(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None):
    karta = {rad.split(':')[0].split()[-1]: rad.split('/')[-2] for rad in prompt.splitlines() if rad.startswith('- riktning ')}
    namn = ut.name.replace('svar-domare-', '').replace('.json', '')
    return {'structured_output': svar_per_domare[namn]({v: b for b, v in karta.items()})}


a.session = attrapp
full = lambda bok: {'rangordning': [{'riktning': bok['2'], 'plats': 1, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['1'], 'plats': 2, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['3'], 'plats': 3, 'styrkor': '', 'svagheter': ''}], 'lana': [], 'motivering': ''}  # noqa: E731
tom = lambda bok: {'rangordning': [], 'lana': [], 'motivering': ''}  # noqa: E731
dubbel = lambda bok: {'rangordning': [{'riktning': bok['1'], 'plats': 1, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['1'], 'plats': 1, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['3'], 'plats': 2, 'styrkor': '', 'svagheter': ''}], 'lana': [], 'motivering': ''}  # noqa: E731
svar_per_domare.update(formgivning=full, funktion=full, kunden=dubbel)
v = a.panel('prov', arot)
assert v['val'] == 2 and v['poang'] == {1: 2, 2: 4, 3: 0} and v['panel']['kunden'].get('ogiltig'), v
svar_per_domare.update(formgivning=full, funktion=tom, kunden=dubbel)
try:
    a.panel('prov', arot); raise AssertionError('en giltig domare ska inte räcka')
except RuntimeError as e:
    assert 'giltiga domare' in str(e), e
print('F23 ateljén ok')

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
fr18 = gr.frysta_referenser('ett-abx', tmp / 'runda18'); assert fr18 and fr18[0].read_bytes() == b'bild B' and str(fr18[0]).startswith(str(tmp / 'runda18')), fr18
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
    assert 'saknar bilder' in str(e), e
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
    pf11.skriv_register(kid, lambda p_: list(poster))


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

shutil.rmtree(tmp, ignore_errors=True)
print('revisionens regressionsfall: alla ok')
