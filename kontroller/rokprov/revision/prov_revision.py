#!/usr/bin/env python3
"""Regressionsfall ur revisionen 2026-10-03 (Codex, sju omgångar): varje skydd prövas genom sin riktiga ingång, med ett
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
rdir0 = tmp / 'runda0'; rdir0.mkdir()
text = gr.lardomar_utan('ett-abx', rdir0).read_text()
assert 'facit' not in text and 'ett-aby' not in text and '## L1' in text, text
assert 'effort: A=medium' not in text, 'omärkt A/B-avsnitt ska bort (F17)'
assert 'atelje: A=av' in text, 'märkt A/B-avsnitt om andra byggen ska vara kvar'
assert 'atelje: A=av' not in gr.lardomar_utan('tva-abx', rdir0).read_text(), 'märkt A/B-avsnitt om bygget ska bort'
assert 'Read(./LARDOMAR.md)' in gr.nekas_for('ett-abx') and any('ett-aby/DOM.json' in x for x in gr.nekas_for('ett-abx'))
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
                                                   'modell': 'm', 'effort': 'e', 'frist': 60, 'granskare': 2, 'originalitet': originalitet, 'metod_sha': m1}))
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
g5 = json.loads((r5 / 'GRANSKNING.json').read_text()); assert g5['godkand'] is True and g5['originalitet'] == 'avgor' and g5['metod_sha'] == m1
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
    (arot / str(n)).mkdir(parents=True); (arot / str(n) / 'vy-390-ruta-01.png').write_bytes(b'x')
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

shutil.rmtree(tmp, ignore_errors=True)
print('revisionens regressionsfall: alla ok')
