#!/usr/bin/env python3
"""Regressionsfall ur revisionen 2026-10-03 (Codex, nio omgångar): varje skydd prövas genom sin riktiga ingång, med ett
positivt och ett negativt fall, isolerat och syntetiskt. Körs av kontroller/rokprov.sh. Argument: repots rot. Skriver
bara i temporära kataloger och i /tmp/nwp-granskning (granskarens arbetskataloger)."""
import contextlib
import datetime
import functools
import io
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
import types
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(ROOT / 'dashboard'))
PY = sys.executable
def stada_vid_slut(p):
    """Tar bort p när provet slutar, också när det faller: annars fyller kvarlämnade kopior disken (NWP_PROV_BEHALL=1
    behåller dem för felsökning)."""
    if not os.environ.get('NWP_PROV_BEHALL'):
        import atexit
        atexit.register(shutil.rmtree, p, True)
    return p


tmp = stada_vid_slut(Path(tempfile.mkdtemp(prefix='nwp-rev-')))
# startkontrollen prövas för sig i en isolerad kopia (prov_startkontroll.py); här kör arbetaren med falska sessioner och
# får aldrig skriva kvitton i repots underlag/
os.environ['NWP_STARTKONTROLL'] = 'av'
# arbetarna i proven anmäler sig i ett eget körregister, aldrig i maskinens (/tmp/nwp-korningar)
os.environ['NWP_KORREGISTER'] = str(tmp / 'korregister')
import korregister as korregister_  # noqa: E402  (efter registrets miljö)
korregister_.registrera_tmp(tmp, 'prov_revision')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
os.environ['NWP_KANDIDATFLODE'] = 'av'  # de äldre ateljéproven kör utforskningen med tre riktningar; kandidatflödet har eget avsnitt


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
# "ingen når min ribba" (Codex 2026-10-05, ordning 3): ett giltigt val, och LARDOMAR säger det
j2 = dash.AB / 'ab-demo2-20261003T000001Z.json'
p2 = dict(p, id='ab-demo2-20261003T000001Z', val=None, status='klar'); j2.write_text(json.dumps(p2))
try:
    dash.spara_ab(p2['id'], {'val': 'x'}); raise AssertionError('ett okänt val ska nekas')
except ValueError as e:
    assert 'ingen når min ribba' in str(e), e
assert dash.spara_ab(p2['id'], {'val': 'ingen'})['ok'] and '- **Ägarens val (blint):** ingen når min ribba' in (tmp / 'LARDOMAR.md').read_text()
# modell, version och skills per arm ur loggens init-rad och Skill-anrop (avstämningen 2026-10-05)
import ab as ab_m  # noqa: E402
ab_k = tmp / 'ab-kunder' / 'arm'; ab_k.mkdir(parents=True)
(ab_k / 'korning-20261005T000000Z.jsonl').write_text('\n'.join(json.dumps(x_) for x_ in (
    {'type': 'system', 'subtype': 'init', 'model': 'claude-opus-5-5[1m]', 'claude_code_version': '2.1.280'},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'humanizer'}}, {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'better-layout'}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'humanizer'}}]}},
    {'type': 'result', 'num_turns': 3, 'duration_ms': 60000})) + '\n')
ab_kg = ab_m.KUNDER; ab_m.KUNDER = tmp / 'ab-kunder'
try:
    m_ab = ab_m.matt('arm')
finally:
    ab_m.KUNDER = ab_kg
assert m_ab['modell'] == 'claude-opus-5-5[1m]' and m_ab['version'] == '2.1.280' and m_ab['skills'] == {'better-layout': 1, 'humanizer': 2}, m_ab
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
# ägarens domar över tidigare byggen är historik och når inte granskaren (rensningen inför Nortropic 2.0, 2026-10-06)
assert not hasattr(gr, 'lardomar_utan') and 'LARDOMAR' not in gr.uppdrag_text('ett-abx', 'http://x', ['/'], tmp / 'ak0', [], [], [], None, rdir0)
assert 'Read(./LARDOMAR.md)' in gr.nekas_for('ett-abx') and any('ett-aby/DOM.json' in x for x in gr.nekas_for('ett-abx'))
assert 'Read(./underlag/LARDOMAR-original.md)' in gr.nekas_for('ett-abx'), 'granskaren får inte läsa den privata originalfilen'
m1 = gr.metod_sha('ett-abx')
(tmp / 'kritik' / 'GRANSKARE.md').write_text('k2'); m2 = gr.metod_sha('ett-abx'); assert m2 != m1, 'ändrade kriterier ska ge ny metodhash'
(tmp / 'kunskap' / 'byggstandard.md').write_text('standard v2'); m3 = gr.metod_sha('ett-abx'); assert m3 != m2, 'ändrad byggstandard ska ge ny metodhash (F18)'
(tmp / 'underlag' / 'ett-abx' / 'BRIEF.md').write_text('krav'); assert gr.metod_sha('ett-abx') != m3, 'ändrad brief ska ge ny metodhash (F18)'
m4 = gr.metod_sha('ett-abx'); (tmp / 'kunskap' / 'referenser-professionella.md').write_text('dimensioner v1'); m5 = gr.metod_sha('ett-abx'); assert m5 != m4, 'måttstockarna ingår i metodhashen'
(tmp / 'kunskap' / 'referenser-professionella.md').write_text('dimensioner v2'); assert gr.metod_sha('ett-abx') != m5, 'ändrad måttstock ska ge ny metodhash'
assert 'kunskap/visuell-niva.md' not in [f_ for _n, f_ in gr.MATTSTOCKAR], 'nivåfilen ur de gamla ankarna är borttagen (den rena designstarten 2026-10-09)'
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
g2_ = json.loads((r2 / 'GRANSKNING.json').read_text())  # T02/F02: jämförelsens besked och metodens beroenden i den verkliga omgången
assert g2_['visuell_jamforelse']['status'] == 'ej_tillamplig' and 'kunskap/designregler.md' in g2_['metodberoenden'], g2_.get('visuell_jamforelse')
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
# 4.2 mäter den srcset-kandidat webbläsaren hämtar, inte img src (Astros Image lägger originalet i src; avstämningen 2026-10-05)
ss_ = '/_astro/a-400.webp 400w, /_astro/a-800.webp 800w, /_astro/a-1600.webp 1600w'
assert sk.vald_kandidat('/_astro/a.webp', ss_, '100vw', 390, 2) == '/_astro/a-800.webp' and sk.vald_kandidat('/_astro/a.webp', ss_, '(min-width: 1024px) 46vw, 100vw', 1440, 1) == '/_astro/a-800.webp'
assert sk.vald_kandidat('/x.webp', '', None, 390, 2) == '/x.webp' and sk.platsbredd('(max-width: 600px) 100vw, 660px', 1440) == 660 and sk.vald_kandidat('/x.webp', ss_, '3000px', 1440, 1) == '/_astro/a-1600.webp'
d42 = tmp / 'dist42'; (d42 / '_astro').mkdir(parents=True)
(d42 / '_astro' / 'a.webp').write_bytes(b'x' * 300 * 1024); (d42 / '_astro' / 'a-800.webp').write_bytes(b'x' * 60 * 1024); (d42 / '_astro' / 'a-1600.webp').write_bytes(b'x' * 260 * 1024)
sida42 = '<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>x</title></head><body><main><img src="/_astro/a.webp" srcset="/_astro/a-800.webp 800w, /_astro/a-1600.webp 1600w" sizes="%s" alt="" width="10" height="10"></main></body></html>'
(d42 / 'index.html').write_text(sida42 % '(min-width: 1024px) 660px, 100vw')
assert not [x for x in sk.granska(d42)[1] if x['punkt'] == '4.2' and 'första bilden' in x['text']], 'den hämtade kandidaten (800w) är liten: ingen information fast src är stor'
(d42 / 'index.html').write_text(sida42 % '(min-width: 1024px) 1400px, 100vw')
assert [x for x in sk.granska(d42)[1] if x['punkt'] == '4.2' and '1440 px' in x['text'] and 'a-1600.webp' in x['text']], 'i 1440 hämtas 1600w-kandidaten, som är för tung'
# granskningen av steg 2, punkt 4: sizes i rem och calc() som byggena skriver dem, x-deskriptorer och <picture> (fixturerna
# ur lulea-snickaren, holms-konditori och paint-it-black); ett villkor som inte går att tolka mäts inte, och det sägs
for sz_ in ('(min-width: 64rem) 660px, 100vw', '(min-width: 60rem) 38rem, 100vw', '(min-width: 1024px) calc(50vw - 2rem), 100vw'):
    (d42 / 'index.html').write_text(sida42 % sz_)
    assert not [x for x in sk.granska(d42)[1] if x['punkt'] == '4.2' and 'första bilden' in x['text']], sz_
(d42 / 'index.html').write_text(sida42 % '(orientation: landscape) 50vw, 100vw')
assert [x for x in sk.granska(d42)[1] if x['punkt'] == '4.2' and 'går inte att tolka' in x['text']], 'ett villkor som inte går att tolka faller inte igenom till 100vw'
assert sk.platsbredd('(min-width: 60rem) 38rem, 100vw', 1440) == 608 and sk.platsbredd('(min-width: 60rem) 34rem, 100vw', 390) == 390
assert sk.platsbredd('(min-width: 72rem) 72rem, calc(100vw - 2.5rem)', 390) == 350 and sk.platsbredd('min(100vw, 40rem)', 1440) == 640
assert sk.platsbredd('(min-width: 60rem) fit-content, 100vw', 1440) is None and sk.platsbredd('(max-width: 30rem) 100vw, 40rem', 1440) == 640
assert sk.vald_kandidat('/a.webp', '/a-2x.webp 2x', None, 390, 2) == '/a-2x.webp' and sk.vald_kandidat('/a.webp', '/a-2x.webp 2x', None, 1440, 1) == '/a.webp'
(d42 / '_astro' / 'b-400.webp').write_bytes(b'x' * 30 * 1024); (d42 / '_astro' / 'b-1600.webp').write_bytes(b'x' * 260 * 1024)
(d42 / 'index.html').write_text((sida42 % '100vw').replace('<img ', '<picture><source media="(max-width: 47.99rem)" srcset="/_astro/b-400.webp 400w, /_astro/b-1600.webp 1600w" sizes="calc(100vw - 2.5rem)">'
                                                           '<source media="(min-width: 48rem)" srcset="/_astro/b-1600.webp 1600w" sizes="72rem"><img ').replace('></main>', '></picture></main>'))
assert [x for x in sk.granska(d42)[1] if x['punkt'] == '4.2' and '390 px' in x['text'] and 'b-1600.webp' in x['text']], 'i <picture> hämtar 390 px den första källan vars media gäller, inte img'
print('F19–F22 seo/standard ok')
# instruktionerna samordnade (backlogposten B-20261004-instruktionerna-samordnas, textkontrollen): de gamla motsägande
# meningarna om telefonen som primär handling, strykregeln, standarddragen, beställda bilder och stockbilder är borta och
# de nya står kvar. Texten jämförs med blanktecken hopslagna, eftersom en mening kan brytas över rader; varje gammal
# mening stod ordagrant i texten före 6c8c90f (granskningen av steg 2, punkt 5: kontrollen gick igenom av fel skäl)
S_, G_, B_, M_ = '.claude/skills/bygg-sajt/SKILL.md', 'kritik/GRANSKARE.md', 'kunskap/bild.md', 'kunskap/brief-mall.md'
text_ins = {f: ' '.join((ROOT / f).read_text(encoding='utf-8').split()) for f in (S_, G_, B_, M_)}
for f_ins, gammal_ in ((S_, 'Saknas den, stryk sektionen'), (S_, 'deras befintliga bokning.'), (S_, 'telefonen är den primära handlingen'),
                       (S_, 'sidhuvudet på en rad med namn och numret som knapp'), (S_, 'sedan rubriken, ringknappen och ett av verksamhetens egna foton'),
                       (S_, 'bär både Ring och Skriv'), (S_, '"Bara de har": minst tio konkreta saker'), (S_, 'kunde någon mening stå hos en konkurrent? Skriv om den.'),
                       (G_, 'Straffa uttryckligen de drag'), (G_, 'Beställt: en förbättring, inget blockerande fynd'), (G_, 'Bär varje sektion något specifikt ur "Bara de har"?'),
                       (B_, 'verktyg/bild/'), (B_, 'licensierad stock'), (M_, 'Genererade eller köpta bilder framställs aldrig som kundens verkliga'),
                       # bildregeln 2026-10-05 (Codex via ägaren, punkt 3): äkthet i stället för ett förbud mot allt
                       (B_, 'Stockbilder och genererade bilder används inte på sajten, inte heller som stämning'),
                       (M_, 'Stockbilder och genererade bilder används inte'), (G_, 'stockbilder eller genererade bilder (ägarens dom: hellre inga foton än stock)'),
                       (S_, 'sidhuvudet på en rad med namn och den primära handlingen som knapp'), (S_, 'list längst ned på mobil bär den primära handlingen och Skriv')):
    assert gammal_ not in text_ins[f_ins], ('gammal mening kvar', f_ins, gammal_)
for f_ins, ny_ in ((S_, 'Under varje sektion: raden `Fråga:` med den fråga besökaren har som sektionen svarar på'),
                   (S_, 'en primär handling som följer den viktigaste toppuppgiften (ring, boka, begär offert, beställ, hitta hit)'),
                   (S_, 'Telefonen är primär när kunderna ringer; en verksamhet där kunderna bokar eller beställer får bokningen eller beställningen som primär handling'),
                   # rensningen inför Nortropic 2.0 (2026-10-06): mobilens första vy är riktningens, inte A/B-formen
                   (S_, 'Mobilens första vy** är riktningens: den godkända kandidatens kod och DESIGN.md (eller KONCEPT.md) avgör sidhuvud'),
                   (S_, 'Listan är ett researchmål, ingen strykregel'),
                   (S_, 'den primära handlingen får aldrig vara den enda vägen; telefonen och en skriftlig väg finns alltid'),
                   (G_, 'döm användningen och utförandet'), (G_, 'Beställningen ursäktar inte (b)'),
                   (B_, 'en bild som visar verksamheten är verksamhetens egen'),
                   (M_, 'ett stockfoto eller en genererad bild utger sig aldrig för att visa den'),
                   (G_, 'en bild som utger sig för att visa verksamheten (dess arbeten, personer, lokaler eller resultat) men inte är dess egen')):
    assert ny_ in text_ins[f_ins], ('ny mening saknas', f_ins, ny_)
# granskningstaket (avstämningen 2026-10-05): en avbruten omgång räknas inte mot taket, men mot det hårda taket
import granska as gr_tak  # noqa: E402
gtak = tmp / 'gtak'
for i_, st_ in enumerate(('klar', 'avbruten', 'avbruten', 'fel'), 1):
    r_ = gtak / ('runda-%02d' % i_); r_.mkdir(parents=True)
    (r_ / 'UPPDRAG.json').write_text(json.dumps({'korning': 'k1' if i_ < 4 else 'k2'}))
    gr_tak.satt_utfall(r_, 'pagar', 'start')
    gr_tak.satt_utfall(r_, st_, 'prov')
assert gr_tak.taket(gtak, 'k1') == (1, 3) and gr_tak.taket(gtak, 'k2') == (1, 1), (gr_tak.taket(gtak, 'k1'), gr_tak.taket(gtak, 'k2'))
assert gr_tak.MAX_HART == 2 * gr_tak.MAX_RUNDOR or os.environ.get('NWP_GRANSKNING_HART')
# granskningen av steg 2, punkt 3: vid taket säger granskningen varför en ny omgång behövs (bygget, metoden eller ingen giltig)
metod_tak = {'metod_sha': 'm1', 'modell': 'opus[1m]', 'effort': 'high', 'granskare': 2, 'originalitet': 'skugga'}
gtak3 = tmp / 'gtak3'; gtak3.mkdir()
assert gr_tak.takskal(gtak3, 'k1', 'd1', metod_tak).startswith('ingen giltig omgång'), 'alla omgångar föll'
r_ = gtak3 / 'runda-01'; r_.mkdir()
(r_ / 'GRANSKNING.json').write_text(json.dumps({'runda': 1, 'korning': 'k1', 'dist_sha256': 'd1', **metod_tak}))
(r_ / 'UTFALL.json').write_text(json.dumps({'status': 'klar', 'tid': gr_tak.nu(), 'skal': ''}))
sk_tak = gr_tak.takskal(gtak3, 'k1', 'd1', dict(metod_tak, metod_sha='m2'))
assert 'en annan metod' in sk_tak and 'annat bygge' not in sk_tak and 'runda-01' in sk_tak, sk_tak
assert 'ett annat bygge' in gr_tak.takskal(gtak3, 'k1', 'd2', metod_tak) and gr_tak.takskal(gtak3, 'k2', 'd1', metod_tak).startswith('ingen giltig omgång')
# ändringsuppdragen med bild (avstämningen 2026-10-05): varje blockerande fynd med rutan och referensbilden; saknade vägar sägs
bild_ = tmp / 'kunder' / 'x' / 'granskning' / 'runda-01' / 'sajt' / 'hem'; bild_.mkdir(parents=True); (bild_ / 'vy-390-ruta-02.png').write_bytes(b'x')
gr_rot = gr_tak.ROOT; gr_tak.ROOT = tmp
try:
    an_ = gr_tak.andringar({'slug': 'x', 'runda': 1, 'blockerande': [{'kriterium': 'text', 'var': 'hem 390', 'observation': 'o', 'rattning': 'r', 'acceptanskriterium': 'a',
                                                                     'bild': 'kunder/x/granskning/runda-01/sajt/hem/vy-390-ruta-02.png', 'referensbild': 'underlag/x/finns-inte.png'}]})
finally:
    gr_tak.ROOT = gr_rot
assert '- bild: kunder/x/granskning/runda-01/sajt/hem/vy-390-ruta-02.png' in an_ and '- referensbild: saknas (underlag/x/finns-inte.png)' in an_ and '## 1. text · hem 390' in an_, an_
assert 'Inga blockerande fynd.' in gr_tak.andringar({'slug': 'x', 'runda': 2, 'blockerande': []})
# granskningen av steg 2, punkt 1: en väg utanför repot, en ..-väg ut, en symlänk och en dold katalog fäller aldrig
# domen; granskarens egen tillståndsbild i arbetskatalogen kopieras in i omgången så att byggaren kan läsa den
arbrot_ = stada_vid_slut(Path(tempfile.mkdtemp(prefix='nwp-granskning-'))); korregister_.registrera_tmp(arbrot_, 'prov_revision granskning'); arb_ = arbrot_ / 'x' / 'runda-01-1'; arb_.mkdir(parents=True); (arb_ / 'meny-oppen.png').write_bytes(b'png')  # utanför repot, som /tmp/nwp-granskning
(tmp / '.dold').mkdir(); (tmp / '.dold' / 'ref.png').write_bytes(b'x'); (tmp / 'lank.png').symlink_to('/etc/hosts')
r1_ = tmp / 'kunder' / 'x' / 'granskning' / 'runda-01'
gr_rot, gr_arb = gr_tak.ROOT, gr_tak.ARBETSROT; gr_tak.ROOT, gr_tak.ARBETSROT = tmp, arbrot_
try:
    assert gr_tak.bildvag('/etc/hosts') is None and gr_tak.bildvag('kunder/x/../../../../../../../../etc/hosts') is None and gr_tak.bildvag('lank.png') is None
    assert gr_tak.bildvag('./.dold/ref.png') == '.dold/ref.png', gr_tak.bildvag('./.dold/ref.png')
    assert gr_tak.bildvag(str(arb_ / 'meny-oppen.png')) is None, 'utan omgång kopieras inget'
    an2_ = gr_tak.andringar_sakert({'slug': 'x', 'runda': 1, 'blockerande': [{'kriterium': 'navigation', 'var': 'hem 390', 'observation': 'o', 'rattning': 'r',
                                    'acceptanskriterium': 'a', 'bild': str(arb_ / 'meny-oppen.png'), 'referensbild': '/etc/hosts'}]}, r1_)
    assert '- bild: kunder/x/granskning/runda-01/andringar/01-meny-oppen.png' in an2_ and (r1_ / 'andringar' / '01-meny-oppen.png').read_bytes() == b'png', an2_
    assert '- referensbild: saknas (/etc/hosts)' in an2_, an2_
    assert 'Kunde inte skrivas' in gr_tak.andringar_sakert({'runda': 3, 'blockerande': ['inte ett fynd']}), 'ett trasigt fynd blir en text, aldrig ett undantag'
finally:
    gr_tak.ROOT, gr_tak.ARBETSROT = gr_rot, gr_arb
    shutil.rmtree(arbrot_, ignore_errors=True)
# granskningen av steg 2, punkt 6: 768 går till huvudgranskarna, inte till originalitetsdomaren eller jämförelsen, vars
# text säger 390 och 1440; undersidornas urval tappar inte 1440-vyn
rot768_ = tmp / 'rot768'
for sida_ in ('hem', 'kontakt', 'om', 'tjanster'):
    for vy_ in ('390', '768', '1440'):
        for n_ in (1, 2, 3):
            p_ = rot768_ / 'prov' / 'inspektion' / sida_ / ('vy-%s-ruta-%02d.png' % (vy_, n_)); p_.parent.mkdir(parents=True, exist_ok=True); p_.write_bytes(b'x')
bilder768_ = gr_tak.skarmbilder(rot768_, rot768_ / 'ut' / 'sajt')
assert any(b.name.startswith('vy-768-') for b in bilder768_), 'huvudgranskarna får mellanbredden'
hem768_, under768_ = gr_tak.originalitetsbilder(bilder768_)
assert [b.name for b in hem768_] == ['vy-390-ruta-01.png', 'vy-390-ruta-02.png', 'vy-1440-ruta-01.png', 'vy-1440-ruta-02.png'], [b.name for b in hem768_]
assert ['%s/%s' % (b.parent.name, b.name) for b in under768_] == ['kontakt/vy-390-ruta-01.png', 'kontakt/vy-1440-ruta-01.png', 'om/vy-390-ruta-01.png', 'om/vy-1440-ruta-01.png'], under768_
(rot768_ / 'r' / 'sajt').mkdir(parents=True); shutil.copytree(rot768_ / 'ut' / 'sajt' / 'hem', rot768_ / 'r' / 'sajt' / 'hem')
assert not [b for b in gr_tak.jamforbilder(rot768_ / 'r') if '-768-' in b.name] and len(gr_tak.jamforbilder(rot768_ / 'r')) == 4
import prova as pv_lh  # noqa: E402
assert pv_lh.lh_audit({'id': 'a', 'titel': 'T', 'varde': '2 s', 'traffar': ['<img>']}) == 'a "T" 2 s (<img>)' and pv_lh.lh_audit('gammal') == 'gammal', 'Lighthouse-auditen med titel och mätvärde i PROV.md'

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


def attrapp(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None, **kw):
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


def attrapp_las(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None, **kw):
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
# byggets granskare: läsningen bokförs i domen (ännu inget krav)
import granska as gr_bk  # noqa: E402
kg_ = gr_bk.granskarkrav((md_, ank_bilder), [(tmp / 'kunder/x/granskning/runda-01/referenser/01-a-vy-1440-ruta-02.png', 'fråga')],
                         [gr_bk.ROOT / 'kunder/x/granskning/runda-01/sajt/hem/vy-390-ruta-01.png', gr_bk.ROOT / 'kunder/x/granskning/runda-01/sajt/om/vy-390-ruta-01.png'])
assert sorted(kg_) == ['ankare', 'referenser', 'startsidan'] and kg_['startsidan'] == ['kunder/x/granskning/runda-01/sajt/hem/vy-390-ruta-01.png'] and len(kg_['ankare']) == 3, kg_
post_ = {'slug': 'x', 'godkand': True, 'niva': 0, 'runda': 1, 'tid': 't', 'modell': 'm', 'effort': 'e', 'dist_sha256': '0' * 12, 'troskel': gr_bk.TROSKEL,
         'kriterier': {}, 'sessioner': [{'granskare': 1, 'lasning': {'verifierad': True, 'grupper': {'ankare': {'kravda': 3, 'lasta': 1, 'saknas': []}}}},
                                        {'granskare': 2, 'lasning': {'verifierad': False, 'skal': 'transkriptet saknas'}}]}
md_g = gr_bk.markdown(post_)
assert '## Granskarnas läsning' in md_g and 'granskare 1: ankare 1 av 3' in md_g and 'granskare 2: kunde inte verifieras (transkriptet saknas)' in md_g, md_g
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


    def attrapp2(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None, **kw):
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
    # skapandeflödet (Codex via ägaren 2026-10-05): utan kandidater väljer utforskningen ur paketet; utan paket och
    # kandidater startar ingen ateljé
    assert a.krav_referenser('provhr') == [], 'ett paket räcker: skaparen väljer kandidaterna ur det'
    (u / 'referenser').rename(u / 'referenser-undan')
    ut_main = io.StringIO()
    with contextlib.redirect_stdout(ut_main):
        rc_main = a.main(['provhr'])
    (u / 'referenser-undan').rename(u / 'referenser')
    assert rc_main == 2 and 'Huvudreferenskandidat' in ut_main.getvalue() and 'inget referenspaket' in ut_main.getvalue(), ut_main.getvalue()
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
    assert 'färre kandidater än riktningarna (1 av %d)' % a.ANTAL in dp and 'Huvudreferenskandidat: <rubrikens namn>' in dp, dp
    assert 'undersida/index.astro' in dp and 'stiltavla/index.astro' in dp and 'style tile' not in dp and '/src/assets/atelje/' in dp and 'Förra omgången' not in dp, dp
    assert 'olika grundidéer' in dp and 'sin egen huvudreferens' in dp and 'Två riktningar' in dp and 'konsolfel' in dp and 'KOMPLETTERING.json' in dp and 'Huvudreferens N:' in dp, dp
    assert '.claude/skills/better-layout/SKILL.md' in dp and '.claude/skills/frontend-design/SKILL.md' in dp and 'skiljer sig inom huvudreferensen' not in dp, 'metoden i prompten; ingen bindning till en enda referens'
    assert 'Förra omgången förkastades' in a.divergera_prompt('provhr', [], 'kritik: platt') and 'kritik: platt' in a.divergera_prompt('provhr', [], 'kritik: platt')
    # tre kandidater: varje riktning väljer sin, och bilderna står med frågan
    (u / 'REFERENSER.md').write_text(ref_text.replace('Huvudreferens: Snick — komposition, typografi och bildbehandling',
                                                      'Huvudreferenskandidat: Snick — komposition, typografi och bildbehandling\nHuvudreferenskandidat: Annan — typografin bär\nHuvudreferenskandidat: Tredje — fotot bär')
                                     + '\n## Tredje — hantverk\n\nBildval: referenser/paket-v01/annan/01-start/vy-390-ruta-02.png — tredje — Fråga: x?\n')
    dp = a.divergera_prompt('provhr', [])
    assert '- Snick: komposition, typografi och bildbehandling. Bilder: underlag/provhr/referenser/paket-v01/snick/01-start/vy-390-ruta-01.png — första vyn — Fråga: bär vår lika mycket?' in dp and '- Tredje: fotot bär' in dp, dp
    assert rv_hr.huvudreferens('provhr', tmp / 'underlag') is None and [x['namn'] for x in rv_hr.kandidater('provhr', tmp / 'underlag')] == ['Snick', 'Annan', 'Tredje']
    assert rv_hr.HUVUD.match('Huvudreferenskandidat: Snick — x') is None, 'en kandidatrad är ingen huvudreferens'
    # ägarens domlogg och historiken följer med (kontroller/skapande.py)
    import skapande as sk_hr
    sk_hr.lagg_till_dom('provhr', 'ägaren via Codex', 'ny_riktning', 'Rubriken tar över.\nBildvalet bär inte.', avser='prov', underlag=tmp / 'underlag', belagg='prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)')
    sk_hr.lagg_till_historik('provhr', [{'kalla': 'prov', 'namn': 'Stenduken', 'drag': 'varm stenduk, versal serif', 'utfall': 'underkänd av ägaren', 'kritik': 'samma grundidé igen'}], tmp / 'underlag')
    dp = a.divergera_prompt('provhr', [])
    assert '> Rubriken tar över.' in dp and 'återöppnar: grundidén' in dp and 'Stenduken (prov' in dp and 'samma grundidé igen' in dp and 'inget drag är förbjudet i sig' in dp, dp
    (u / 'REFERENSER.md').write_text(ref_text)
    dmp = a.domar_prompt('provhr', 'uppdraget', [('A', 1), ('B', 2)], {1: ['x'], 2: ['y']}, None)
    assert 'Huvudreferenserna' not in dmp and 'kalibreringsankare saknas' in dmp and '> Rubriken tar över.' in dmp and 'upprepar en underkänd grundidé' in dmp, dmp
    sn_ = (u / 'referenser' / 'paket-v01' / 'snick' / '01-start' / 'vy-390-ruta-01.png', 'första vyn')
    dmp = a.domar_prompt('provhr', 'uppdraget', [('A', 1), ('B', 2)], {1: ['x'], 2: ['y']}, None,
                         referenser={1: {'namn': 'Snick', 'vad': 'v', 'bilder': [sn_]}, 2: {'namn': 'Annan', 'vad': 'w', 'bilder': [sn_]}})
    assert '- riktning A bygger på Snick (v); läs dess bilder med Read: underlag/provhr/referenser/paket-v01/snick/01-start/vy-390-ruta-01.png' in dmp and '- riktning B bygger på Annan (w)' in dmp, dmp
    dms = a.domar_prompt('provhr', 'uppdraget', [('A', 2), ('B', 1)], {1: ['x'], 2: ['y']}, None, slut=True, svagheter=['formgivning: platt'],
                         referenser={1: {'namn': 'Snick', 'vad': 'v', 'bilder': [sn_]}, 2: {'namn': 'Snick', 'vad': 'v', 'bilder': [sn_]}})
    assert 'Två versioner' in dms and '- versionerna A, B bygger på Snick' in dms and '- formgivning: platt' in dms and '- version A: y' in dms and 'undersidans början' not in dms, dms
    # divergensomgångar: förkastat → ny omgång med kritiken, sedan stopp (slutkod 6 i vanta)
    gamla = {n: getattr(a, n) for n in ('session', 'fotografera', 'skriv_val', 'bevara_vinnare', 'stada', 'egna_bilder', 'OMGANGAR', 'overfor_startsida', 'bygg', 'forfina', 'slutdom')}
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
    forfinade = []
    forfina_enkel = lambda slug, rot, status, skriv: (forfinade.append(slug), status.setdefault('faser', {}).__setitem__('forfina', {'klar': 'x'}), 'klar')[2]  # noqa: E731
    a.forfina = forfina_enkel
    a.slutdom = lambda slug, rot, status, skriv: status.setdefault('faser', {}).__setitem__('slutdom', {'klar': 'x', 'over_ribban': True})
    (rot2 / 'VINNARE.json').write_text('{"riktning": 1}'); (rot2 / 'vinnare').mkdir(); (rot2 / 'VAL.md').write_text('förra körningens val')
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'klar' and st['val'] == 2 and st['omgangar'] == 2 and bevarade == [2] and st['overford'] is True, st
    assert forfinade == ['provhr'] and st['faser']['slutdom']['over_ribban'] and (rot2 / 'REDOVISNING.md').is_file(), 'efter valet: förfining, slutdom och redovisning'
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
    # förfiningen lämnar grundidén (TILLBAKA.md): en ny utforskning med skälet som kritik, sedan förfining och slutdom
    utfall = iter([1, 2]); prompter.clear(); forfinade.clear()


    def forfina_tillbaka(slug, rot, status, skriv):
        forfinade.append(len(forfinade))
        if len(forfinade) == 1:
            (rot / 'TILLBAKA.md').write_text('kundens foton bär inte en bilddriven riktning')
            return 'tillbaka'
        return 'klar'


    a.forfina = forfina_tillbaka
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'klar' and st['val'] == 2 and len(prompter) == 2 and 'kundens foton bär inte' in prompter[1] and (rot2 / 'omgang-1' / 'TILLBAKA.md').is_file(), st
    assert any(h_['utfall'] == 'lämnad av skaparen under förfiningen' for h_ in sk_hr.historik('provhr', tmp / 'underlag'))
    a.OMGANGAR = 1; utfall = iter([1]); forfinade.clear()  # utan omgångar kvar: steget tillbaka, och vanta ger 6
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'tillbaka' and (rot2 / 'TILLBAKA.md').is_file(), st
    with contextlib.redirect_stdout(io.StringIO()):
        assert a.vanta(rot2, 1) == 6
    a.OMGANGAR = 2; a.forfina = forfina_enkel
    # arbetaren kräver läsbara referenser varje omgång (granskningen av r53, punkt 10): en kandidat utan bilder stoppar
    (u / 'REFERENSER.md').write_text(ref_text.replace('Huvudreferens: Snick — komposition, typografi och bildbehandling', 'Huvudreferenskandidat: Sni — komposition'))
    utfall = iter([2]); prompter.clear()
    a.arbetare('provhr')
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert st['steg'] == 'fel' and 'inga läsbara Bildval-bilder' in st['fel'] and not prompter, st
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
    assert a.FRIST == 1200 + 1400 * a.ANTAL or os.environ.get('NWP_ATELJE_FRIST'), 'gränsen växer med antalet riktningar och förhandsvarven'
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


    vd, hd, ud = tmp / 'atelje-v' / 'vinnare' / 'bilder', tmp / 'insp-v' / 'hem', tmp / 'ut-vinnare'
    vd.mkdir(parents=True); hd.mkdir(parents=True)
    gra = lambda x, y: (200, 200, 200, 255)  # noqa: E731
    png_hr(vd / 'vy-390-ruta-01.png', 40, 20, gra); png_hr(hd / 'vy-390-ruta-01.png', 40, 20, lambda x, y: (200, 200, 200, 255) if x >= 10 else (20, 20, 20, 255))
    png_hr(vd / 'vy-390-hela.png', 40, 20, gra); png_hr(hd / 'vy-390-hela.png', 40, 30, gra)
    png_hr(vd / 'vy-1440-ruta-01.png', 40, 20, gra)
    png_hr(hd / 'vy-1440-hela.png', 40, 20, gra)
    import hashlib as hl_hr
    (tmp / 'atelje-v' / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'filer': {'bilder/' + p.name: hl_hr.sha256(p.read_bytes()).hexdigest() for p in vd.glob('*.png')}}))
    assert pv_hr.vinnarjamforelse(vd, hd, ud).startswith('ingen jämförelse'), 'en vinnare som ägaren inte godkänt jämförs inte'
    (tmp / 'atelje-v' / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'godkand': {'tid': '2026-10-06T00:00:00Z'},
                                                              'filer': {'bilder/' + p.name: hl_hr.sha256(p.read_bytes()).hexdigest() for p in vd.glob('*.png')}}))
    text_v = pv_hr.vinnarjamforelse(vd, hd, ud)
    jv = json.loads((ud / 'VINNARJAMFORELSE.json').read_text())
    assert jv['hashfel'] == [] and 'STÄMMER INTE' not in text_v, jv['hashfel']
    assert jv['par'][0]['andel'] == 0.25 and jv['par'][1]['hojdskillnad'] == 10 and jv['par'][1]['andel'] == 0, jv
    assert 'saknas: byggets bild' in jv['par'][2]['fel'] and 'saknas: prototypens bild' in jv['par'][3]['fel'] and (ud / 'skillnad-vy-390-ruta-01.png').is_file(), jv
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
    assert gr.frysta_vinnare('provhr', rdirv) is None, 'en vinnare som ägaren inte godkänt är ingen måttstock (rensningen inför 2.0)'
    (u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 2, 'filer': {}, 'godkand': {'tid': '2026-10-06T00:00:00Z'}}))
    assert gr.metod_sha('provhr') != h0, 'vinnaren ingår i metodhashen'
    try:
        gr.frysta_vinnare('provhr', rdirv); raise AssertionError('en bild som inte står i VINNARE.json stoppar granskningen')
    except RuntimeError as e:
        assert 'stämmer inte med VINNARE.json' in str(e), e
    (u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 2, 'filer': {'bilder/vy-390-ruta-01.png': hl_hr.sha256(b'x').hexdigest()},
                                                          'godkand': {'tid': '2026-10-06T00:00:00Z'}}))
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
    assert 'Ägarens godkända startsida ur ateljén: riktning 2' in pt and 'blockerande fynd' in pt and 'vinnare/vy-390-ruta-01.png' in pt and 'VINNARJAMFORELSE.md' in pt, pt
    assert 'godkända startsida' not in gr.uppdrag_text('provhr', 'http://x', ['/'], tmp / 'ak', [], [], [], None, rdirv)
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
        # skapandeflödet: skaparen lämnade grundidén och omgångarna är slut; stoppet kräver TILLBAKA.md
        (rot_sv / 'underlag' / 'sv' / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'tillbaka', 'skal': 'grundidén bär inte'}))
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') is None, 'utan TILLBAKA.md inget stopp'
        (rot_sv / 'underlag' / 'sv' / 'atelje' / 'TILLBAKA.md').write_text('x')
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') == 'grundidén bär inte'
        (rot_sv / 'underlag' / 'sv' / 'atelje' / 'TILLBAKA.md').unlink()
        (rot_sv / 'underlag' / 'sv' / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'forkastad', 'skal': 'panelen förkastade alla riktningar i 2 omgångar'}))
        os.environ['NWP_SANDLADA'] = 'pa'
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') is None, 'sandlådat körs ingen ateljé: ett sådant läge är inte ateljéns'
        del os.environ['NWP_SANDLADA']
        (rot_sv / 'underlag' / 'sv' / 'atelje' / 'VAL.json').write_text(json.dumps({'val': 2, 'forkastade': False, 'panel': {'a': {}, 'b': {}}}))
        assert sv_hr.ateljen_forkastad(rot_sv, 'sv') is None, 'ett val är ingen förkastning'
        # granskningen av steg 2, punkt 3: vid taket säger stoppvakten alltid att en ny omgång behövs, med granskningens skäl
        k_tak = rot_sv / 'kunder' / 'sv'; (k_tak / 'prov').mkdir(parents=True)
        (k_tak / 'RAPPORT.md').write_text('---\nkorning: 20261001T000000Z\n---\n' + 'r' * 400); (k_tak / 'prov' / 'STATUS.json').write_text(json.dumps({'dist_sha256': 'd2'}))
        svar_tak = iter([types.SimpleNamespace(returncode=0, stdout='grönt', stderr=''),
                         types.SimpleNamespace(returncode=3, stdout='Taket nått: 2 granskningar\nSkäl till ny omgång: ingen giltig omgång i körningen (alla avbröts eller föll)\n', stderr='')])
        sp_hr, rot_hr, in_hr, miljo_hr = sv_hr.subprocess, sv_hr.ROOT, sys.stdin, {k_: os.environ.get(k_) for k_ in ('NWP_SLUG', 'NWP_GRANSKNING', 'NWP_KORNING')}
        sv_hr.subprocess = types.SimpleNamespace(run=lambda *a_, **k_: next(svar_tak), TimeoutExpired=subprocess.TimeoutExpired)
        sv_hr.ROOT, sys.stdin = rot_sv, io.StringIO('{}')
        os.environ['NWP_SLUG'] = 'sv'; os.environ.pop('NWP_GRANSKNING', None)
        os.environ['NWP_KORNING'] = '20261001T000000Z'  # rapporten bär körningens identitet (ägarens uppdrag 2026-10-07, punkt 5)
        try:
            rc_tak = sv_hr.main()
        finally:
            sv_hr.subprocess, sv_hr.ROOT, sys.stdin = sp_hr, rot_hr, in_hr
            for k_, v_ in miljo_hr.items():
                os.environ.pop(k_, None) if v_ is None else os.environ.__setitem__(k_, v_)
        post_tak = json.loads((k_tak / 'prov' / 'STOPPVAKT.json').read_text())
        assert rc_tak == 0 and post_tak['slapp'] and 'en ny omgång behövs' in post_tak['skal'] and 'ingen giltig omgång i körningen' in post_tak['skal'], post_tak
        assert post_tak['tak_skal'].startswith('ingen giltig omgång') and 'annat bygge' not in post_tak['skal'], post_tak
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
sp.SPANING = (tmp / 'spaning').resolve()  # egen provrot; macOS /var är en systemlänk
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
import hashlib as hl_rapport  # noqa: E402
rsha_ = hl_rapport.sha256((kk2 / 'RAPPORT.md').read_bytes()).hexdigest()  # den rapport stoppvakten band (ägarens uppdrag 2026-10-07, punkt 5)
metod_r3 = json.loads(subprocess.run([PY, '-B', '-c', 'import sys, json; sys.path.insert(0, %r); import granska; print(json.dumps(granska.aktuell_metod(%r)))' % (str(ROOT / 'kontroller'), kk2.name)],
                                     capture_output=True, text=True, cwd=str(ROOT)).stdout)
fore2 = tmp / 'fore2.txt'; fore2.write_text('aaa  kontroller/prova.py\n')


def slut2(rc='0'):
    p = subprocess.run([PY, '-B', str(korslut), str(kk2), rc, str(fore2), str(fore2)], capture_output=True, text=True)
    return p.returncode, p.stdout


(kk2 / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': h2, 'grindar': {'bygge': {'ok': True}}}))
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'dist_sha256': h2, 'rapport_sha256': rsha_}))
(kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': 'gammal', **metod_r3}))
rc, ut = slut2(); assert rc == 1 and 'annat bygge' in ut, (rc, ut)  # äldre godkänd granskning av ett annat bygge
(kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h2, **dict(metod_r3, metod_sha='gammal')}))
rc, ut = slut2(); assert rc == 1 and 'annan metod' in ut, (rc, ut)
(kk2 / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'godkand': True, 'runda': 1, 'kriterier': {}, 'dist_sha256': h2, **metod_r3}))
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'släppt utan godkänd granskning: taket för granskningar i körningen är nått', 'forsok': 3, 'tak': 8, 'dist_sha256': h2, 'rapport_sha256': rsha_}))
rc, ut = slut2(); assert rc == 1 and 'stoppvakten' in ut, (rc, ut)  # stoppvakten släppte vid taket: inte godkänt
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'dist_sha256': h2, 'rapport_sha256': rsha_}))
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


(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h3, 'rapport_sha256': rsha_, 'rapport_korning': 'k1'}))
assert slut3()[0] == 0, slut3()
for over in ({'modell': 'gammal'}, {'effort': 'low'}, {'originalitet': 'avgor'}):
    rc, ut = slut3(**over); assert rc == 1 and 'annan metod' in ut, (over, rc, ut)
rc, ut = slut3(korning='k2'); assert rc == 1 and 'annan körning' in ut, (rc, ut)
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': 'annan', 'rapport_sha256': rsha_, 'rapport_korning': 'k1'}))
rc, ut = slut3(); assert rc == 1 and 'annat bygge' in ut, (rc, ut)
# Codex R38 F11: med omgångar härleds domen ur giltiga omgångar (inte rotfilen), bunden till det slutliga byggets dist
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h3, 'rapport_sha256': rsha_, 'rapport_korning': 'k1'}))
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
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'släppt utan godkänd granskning: taket för granskningar i körningen är nått', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h4, 'rapport_sha256': rsha_, 'rapport_korning': 'k1'}))
p38 = subprocess.run([PY, '-B', str(korslut), str(kk2), '0', str(fore2), str(fore2), 'k1'], capture_output=True, text=True)
assert p38.returncode == 1 and 'inte granskat' in p38.stdout and 'Senaste dom oavsett bygge och metod: underkänd (omgång 2' in p38.stdout and '≠ slutliga bygget' in p38.stdout and 'GODKÄND' not in p38.stdout.split('Rapport:')[0], ('det slutliga bygget är ogranskat: senaste giltiga visas separat som annat bygge, inte den avbrutna godkända', p38.returncode, p38.stdout[-600:])
shutil.rmtree(gdir38); gdir38.mkdir(); (kk2 / 'sajt' / 'dist' / 'index.html').write_text('<p>v3</p>')
(kk2 / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'dist_sha256': h3, 'grindar': {'bygge': {'ok': True}}}))
# Codex R39: sluturvalet med hela identiteten (körning, dist, aktuell metod); senaste dom visas separat; läsfel nekar godkännande
(kk2 / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True, 'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd', 'forsok': 1, 'tak': 8, 'korning': 'k1', 'dist_sha256': h3, 'rapport_sha256': rsha_, 'rapport_korning': 'k1'}))
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
egen_ = 'p%d' % os.getpid()  # egna namn i det delade området: två körningar av provet samtidigt krockar inte
os.symlink(tmp / 'annat-bygge-mapp' / 'artikel.txt', omr / ('artikel%s.txt' % egen_))
try:
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'sida_till_text.py'), 'http://127.0.0.1:1/', str(omr / ('artikel' + egen_))], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'slugvakten' in r.stderr and ('artikel%s.txt' % egen_) in r.stderr, 'artikel.txt som symlänk ut: ' + r.stderr
finally:
    (omr / ('artikel%s.txt' % egen_)).unlink()
os.symlink(tmp / 'annat-bygge-mapp', omr / ('video%s-bilder' % egen_))
try:
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'youtube.py'), 'https://www.youtube.com/watch?v=x', '--ut', str(omr / ('video%s.md' % egen_))], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'slugvakten' in r.stderr and ('video%s-bilder' % egen_) in r.stderr, 'video-bilder som symlänk ut: ' + r.stdout + r.stderr
finally:
    (omr / ('video%s-bilder' % egen_)).unlink()
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
art7 = 'artikel%s' % egen_  # unikt per process: parallella körningar av provet delar området (2026-10-06)
os.symlink(tmp / 'annat-bygge-mapp' / 'artikel.txt', omr7 / (art7 + '.txt'))
try:
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'sida_till_text.py'), 'http://127.0.0.1:1/', str(omr7 / (art7 + '.v1'))], capture_output=True, text=True, env={**os.environ, 'NWP_SLUG': 'eget-bygge'}, cwd=str(ROOT))
    assert r.returncode == 2 and 'slugvakten' in r.stderr and (art7 + '.txt') in r.stderr, 'artikel.v1 skriver artikel.txt, som är en symlänk ut: ' + r.stdout + r.stderr
finally:
    (omr7 / (art7 + '.txt')).unlink()
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
# F02 (motorinventeringen 2026-10-08): kalibreringens aktiva ankare ingår i domens identitet; ett undanhållet exempel gör det inte
m18_fore = gr.metod_sha('ett-abx'); kal18 = tmp / 'underlag' / 'kalibrering'; (kal18 / 'K06' / 'start').mkdir(parents=True, exist_ok=True)
(kal18 / 'K06' / 'start' / 'vy-390-forsta.png').write_bytes(b'ankarbild'); (kal18 / 'DOMAR.json').write_text(json.dumps({'K06': {'niva': 'over', 'skiljer': 'lugnet'}, 'K07': {'niva': 'generisk', 'skiljer': 'x'}}))
assert gr.metod_sha('ett-abx') == m18_fore, 'ett exempel utan ankarrad ändrar inte identiteten (undanhållet)'
(kal18 / 'ANKARE.txt').write_text('K06 · ankare\n'); m18c = gr.metod_sha('ett-abx'); assert m18c != m18_fore, 'ett aktivt ankare ska ingå i metodhashen (F02)'
(kal18 / 'DOMAR.json').write_text(json.dumps({'K06': {'niva': 'over', 'skiljer': 'ljuset'}, 'K07': {'niva': 'generisk', 'skiljer': 'x'}})); m18d = gr.metod_sha('ett-abx'); assert m18d != m18c, 'ägarens ord om ankaret ingår'
(kal18 / 'K06' / 'start' / 'vy-390-forsta.png').write_bytes(b'ankarbild 2'); assert gr.metod_sha('ett-abx') != m18d, 'ankarets bild ingår'
(kal18 / 'ANKARE.txt').unlink(); assert gr.metod_sha('ett-abx') == m18_fore, 'utan ankarraden är identiteten den gamla'
print('R11 F02 ankare ok')

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
# prototypen i skapandeflödet (Codex via ägaren 2026-10-05): före och efter bredvid den valda huvudreferensen; ägarens dom
# med beslut och minuter till domloggen; panelens dom döljs tills ägaren dömt körningen
pr_ = tmp / 'underlag' / 'pr-prov' / 'atelje'
for k_ in ('1', '2'):
    (pr_ / 'slutdom' / k_).mkdir(parents=True)
    for fil_ in ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png', 'vy-1440-hela.png'):
        (pr_ / 'slutdom' / k_ / fil_).write_bytes(b'\x89PNG')
(pr_ / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'lage': 'ny', 'startad': '2026-10-05T09:00:00Z', 'klar': '2026-10-05T10:00:00Z', 'faser': {'valj': {}, 'forfina': {}, 'slutdom': {}}}))
(pr_ / 'FORFINING.md').write_text('# Förfining\n\nRubriken kortades.\n'); (pr_ / 'RIKTNINGAR.md').write_text('## Riktning 1 — Fönstret\n\nHuvudreferens 1: Snick — komposition\n')
(pr_ / 'VAL.md').write_text('# Panelens val'); (pr_ / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'huvudreferens': {'namn': 'Snick', 'vad': 'komposition'}}))
ref_pr = tmp / 'underlag' / 'pr-prov' / 'referenser' / 'p' / 'snick' / '01-start'; ref_pr.mkdir(parents=True); (ref_pr / 'vy-1440-ruta-02.png').write_bytes(b'\x89PNG')
(tmp / 'underlag' / 'pr-prov' / 'REFERENSER.md').write_text('## Snick — snickeri\n\nBildval: referenser/p/snick/01-start/vy-1440-ruta-02.png — hållningen — Fråga: bär vår?\n')
assert 'pr-prov' in json.loads(begar(dport, 'GET', '/api/prototyp')[1]), 'varje körning i skapandeflödet (också byggets ateljé) syns i vyn'
d_ = json.loads(begar(dport, 'GET', '/api/prototyp/pr-prov')[1])
assert d_['steg'] == 'klar' and set(d_['fore']) == set(d_['efter']) == {'390-forsta', '390-hela', '1440-forsta', '1440-hela'} and not d_['domd'], d_
assert d_['efter']['390-forsta'] == 'underlag/pr-prov/atelje/slutdom/2/vy-390-forsta.png' and begar(dport, 'GET', '/fil/' + d_['efter']['390-forsta'])[0] == 200
assert d_['huvudreferens']['namn'] == 'Snick' and d_['forfining_md'] is None and d_['domar'] == [] and d_['val_md'] is None, 'förfiningens logg och panelens val döljs tills ägaren dömt'
assert begar(dport, 'GET', '/api/prototyp/okand')[0] == 404
assert begar(dport, 'POST', '/api/prototyp/pr-prov', huvuden=ok_h, kropp=b'{"beslut":"ja","text":"x"}')[0] >= 400, 'beslutet är godkand, putsa eller ny_riktning'
assert begar(dport, 'POST', '/api/prototyp/pr-prov', huvuden={'Origin': 'http://evil.test:%d' % dport, 'Content-Type': 'application/json'}, kropp=b'{"beslut":"putsa","text":"x"}')[0] == 403
startad_pr = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0) - datetime.timedelta(minutes=6)
assert begar(dport, 'POST', '/api/prototyp/pr-prov', huvuden=ok_h, kropp=json.dumps({'beslut': 'putsa', 'niva': 'nastan', 'text': 'bildvalet', 'startad': startad_pr.isoformat().replace('+00:00', 'Z')}).encode())[0] == 200
dom_pr = [json.loads(r_) for r_ in (tmp / 'underlag' / 'pr-prov' / 'DESIGNDOMAR.jsonl').read_text().splitlines()]
assert len(dom_pr) == 1 and dom_pr[0]['kalla'] == 'ägaren' and dom_pr[0]['beslut'] == 'putsa' and dom_pr[0]['text'] == 'bildvalet' and 5 <= dom_pr[0]['minuter'] <= 7, dom_pr
d_ = json.loads(begar(dport, 'GET', '/api/prototyp/pr-prov')[1])
assert d_['domar'][0]['beslut'] == 'putsa' and d_['domd'] and d_['val_md'] and 'Rubriken kortades' in d_['forfining_md'], 'efter ägarens dom visas panelens val och förfiningens logg'
dsrvd.shutdown()
print('designprovet i dashboarden ok')

# ---------------------------------------------------------------- skapandeflödet och prototypen (Codex via ägaren 2026-10-05: ett designflöde, inte tre)
import prototyp as pt  # noqa: E402
import skapande as sk  # noqa: E402
import bildkedja as bk_pt  # noqa: E402
import atelje as at_pt  # noqa: E402
pt_und = tmp / 'pt-underlag'
gu_at = (at_pt.UNDERLAG, at_pt.KUNDER)
at_pt.UNDERLAG, at_pt.KUNDER = pt_und, tmp / 'pt-kunder'
pt_u = pt_und / 'pt-prov'; (pt_u / 'bilder').mkdir(parents=True)
# läget ur domloggen: ingen körning → ny, ägarens senaste dom avgör efter en körning
assert pt.lage('pt-prov')[0] == 'om', pt.lage('pt-prov')
sk.lagg_till_dom('pt-prov', 'ägaren via Codex', 'ny_riktning', 'Grundidén bär inte.', underlag=pt_und, tid='2026-10-05T04:49:00Z', belagg='prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)')
assert pt.lage('pt-prov')[0] == 'ny-riktning'
(pt_u / 'atelje').mkdir()
(pt_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'startad': '2026-10-05T06:00:00Z', 'klar': '2026-10-05T07:00:00Z', 'lage': 'ny'}))
assert pt.lage('pt-prov')[0] == 'vanta', 'en körning efter domen väntar på ägarens nya dom'
sk.lagg_till_dom('pt-prov', 'ägaren', 'putsa', 'Rubriken för stor i mobilen.', underlag=pt_und, tid='2026-10-05T08:00:00Z')
assert pt.lage('pt-prov')[0] == 'putsa'
sk.lagg_till_dom('pt-prov', 'ägaren', 'godkand', 'Godkänd.', underlag=pt_und, tid='2026-10-05T09:00:00Z')
# omgranskningen, nytt fel 5: en godkänd dom utan giltigt godkännande i VINNARE.json säger inte att bygget tar vid
assert pt.lage('pt-prov')[0] == 'stopp' and 'godkännandet gäller inte' in pt.lage('pt-prov')[1], pt.lage('pt-prov')
with contextlib.redirect_stdout(io.StringIO()):
    assert pt.main(['pt-prov']) == 2, 'ett godkännande som inte gäller stoppar'
os.environ['NWP_SLUG'] = 'pt-prov'
try:
    with contextlib.redirect_stderr(io.StringIO()):
        assert pt.main(['pt-prov']) == 2, 'prototypen startas inte inifrån ett bygge'
finally:
    del os.environ['NWP_SLUG']
# domloggen: okänd källa vägras, oläsbara rader hoppas över, kritiken nyast först med vad den återöppnar
try:
    sk.lagg_till_dom('pt-prov', 'någon', 'putsa', 'x', underlag=pt_und); raise AssertionError('okänd källa vägras')
except ValueError:
    pass
with open(pt_und / 'pt-prov' / sk.DOMLOGG, 'a') as f_:
    f_.write('inte json\n')
assert len(sk.domar('pt-prov', pt_und)) == 3 and sk.senaste('pt-prov', underlag=pt_und)['beslut'] == 'godkand'
# en oläsbar rad hoppas inte över tyst (GR-20261007-r100-om#KAN-A): den syns med plats, och läget gissar inte förbi den;
# sedan rättas raden, och resten av provet går som förut
assert [x_['rad'] for x_ in sk.domlogg('pt-prov', pt_und)['olasbara']] == [4] and 'rad 4' in pt.lage('pt-prov')[1], pt.lage('pt-prov')
dl_pt = pt_und / 'pt-prov' / sk.DOMLOGG
dl_pt.write_bytes(b''.join(r_ + b'\n' for r_ in dl_pt.read_bytes().split(b'\n') if r_ and r_ != b'inte json'))
kr_pt = sk.kritikrader('pt-prov', underlag=pt_und)
assert kr_pt.index('  > Godkänd.') < kr_pt.index('  > Grundidén bär inte.') and any('återöppnar: grundidén' in r for r in kr_pt), kr_pt
sk.lagg_till_historik('pt-prov', [{'kalla': 'k', 'namn': 'A', 'drag': 'd', 'utfall': 'förkastad av panelen', 'kritik': 'platt'}], pt_und)
assert 'A (k, ' in '\n'.join(sk.historikrader('pt-prov', pt_und)) and sk.historik('pt-prov', pt_und)[0]['tid']
(pt_u / 'TEXTUNDERLAG.md').write_text('# text')
assert sk.textfil('pt-prov', pt_und).name == 'TEXTUNDERLAG.md' and 'utkast som skrivs om' in ' '.join(sk.fakta_rader('pt-prov', pt_und))
# förfiningens uppdrag: riktningen, panelens svagheter, huvudreferensen varje varv, metoden, vägarna tillbaka och DESIGN.md
(pt_u / 'VERKSAMHET.json').write_text(json.dumps({'kontaktvagar': [{'typ': 'telefon', 'varde': '070-111 22 33', 'belagg': 'x'}]}))
(pt_u / 'referenser' / 'paket-v01' / 'x' / '01-start').mkdir(parents=True)
(pt_u / 'referenser' / 'paket-v01' / 'x' / '01-start' / 'vy-1440-ruta-02.png').write_bytes(b'x')
(pt_u / 'REFERENSER.md').write_text('Huvudreferenskandidat: Xref — komposition\n\n## Xref — bransch\n\nBildval: referenser/paket-v01/x/01-start/vy-1440-ruta-02.png — paret — Fråga: bär vårt?\n')
(pt_u / 'atelje' / 'RIKTNINGAR.md').write_text('# Riktningar\n\n## Riktning 1 — Fönstret\n\nHuvudreferens 1: Xref — kompositionen\nGrundidé: fönster.\nVarven: två.\n\n## Riktning 2 — Annat\n\nHuvudreferens 2: Saknas — x\n')
(pt_u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'huvudreferens': {'namn': 'Xref', 'vad': 'kompositionen'}}))
(pt_u / 'atelje' / 'VAL.json').write_text(json.dumps({'val': 1, 'panel': {'formgivning': {'rangordning': [{'riktning': 1, 'svagheter': 'luften glesar'}]}}}))
rr_pt = at_pt.riktningsreferenser('pt-prov', pt_u / 'atelje')
assert list(rr_pt) == [1] and rr_pt[1]['namn'] == 'Xref', 'en riktning vars referens saknar bilder räknas inte'
import referensval as rv_pt  # noqa: E402
assert rv_pt.huvudreferens('pt-prov', pt_und)['kalla'].startswith('ateljéns val') and rv_pt.huvudreferens('pt-prov', pt_und)['vad'] == 'kompositionen', 'den valda referensen går före REFERENSER.md'
assert at_pt.riktningsavsnitt(pt_u / 'atelje')[1][0] == 'Fönstret' and at_pt.sammandrag('Grundidé: x\nVarven: y') == 'Grundidé: x'
fp = at_pt.forfina_prompt('pt-prov', pt_u / 'atelje')
assert not hasattr(at_pt, 'MIN_VARV_FORFINA') and 'inget minsta antal varv' in fp, 'minimiantalet varv är borttaget (2026-10-09)'
for krav_ in ('kontroller/forhandsvisa.py pt-prov', 'FORFINING.md', 'TILLBAKA.md', 'KOMPLETTERING.json',
              '070-111 22 33', '600000 ms', 'forhand/start', '.claude/skills/better-layout/SKILL.md', 'humanizer', 'formgivning: luften glesar',
              'Huvudreferensen, som riktningen bär', 'vy-1440-ruta-02.png', 'DESIGN.md', 'design.py pt-prov --skriv', '> Grundidén bär inte.', 'utkast som skrivs om'):
    assert krav_ in fp, krav_
vk_ = at_pt.forfina_verktyg('pt-prov')
assert 'Skill' in vk_ and 'Write(./kunder/pt-prov/sajt/src/**)' in vk_ and 'Write(./underlag/pt-prov/atelje/FORFINING.md)' in vk_ and 'Write(./kunder/pt-prov/sajt/DESIGN.md)' in vk_
assert not any(v.endswith(('/atelje/**)', 'VINNARE.json)', 'STATUS.json)')) for v in vk_) and not any(v.startswith(('Bash(git', 'Bash(rm', 'Bash(curl', 'WebFetch', 'WebSearch')) for v in vk_), vk_
assert 'Skill' in at_pt.utforska_verktyg('pt-prov') and 'Write(./underlag/pt-prov/REFERENSER.md)' in at_pt.utforska_verktyg('pt-prov')
# historiken efter valet: vald och förkastad, med panelens svagheter
at_pt.historik_efter_val('pt-prov', pt_u / 'atelje', dict(json.loads((pt_u / 'atelje' / 'VAL.json').read_text()), poang={1: 3, 2: 1}), 1)
h_pt = sk.historik('pt-prov', pt_und)
assert [x['utfall'] for x in h_pt[-2:]] == ['vald av panelen', 'förkastad av panelen'] and h_pt[-2]['kritik'] == 'formgivning: luften glesar', h_pt[-2:]
# ägarens godkännande lämnar över till bygget
(at_pt.KUNDER / 'pt-prov' / 'sajt' / 'src' / 'pages').mkdir(parents=True, exist_ok=True); (at_pt.KUNDER / 'pt-prov' / 'sajt' / 'src' / 'pages' / 'index.astro').write_text('<p>s</p>')
(pt_u / 'atelje' / 'vinnare' / 'kod').mkdir(parents=True, exist_ok=True); (pt_u / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>s</p>')
at_pt.godkann('pt-prov', sk.domar('pt-prov', pt_und)[-1])
assert json.loads((pt_u / 'atelje' / 'VINNARE.json').read_text())['godkand']['av'] == 'ägaren'
assert pt.lage('pt-prov')[0] == 'godkand', pt.lage('pt-prov')
with contextlib.redirect_stdout(io.StringIO()):
    assert pt.main(['pt-prov']) == 0, 'godkänd och giltig: inget att köra, bygget tar vid'
# research på begäran: begäran till referenssteget (nytt paket ärver det förra), tjänsternas förra rapport sparas
anrop_pt = []


def kor_pt(args, timeout):
    anrop_pt.append(args)
    if Path(args[2]).name == 'referens.py':
        (pt_u / 'referenser' / 'paket-v02').mkdir()
    return subprocess.CompletedProcess(args, 0, 'ok', '')


(pt_u / 'referenser' / 'tjanster').mkdir()
(pt_u / 'referenser' / 'tjanster' / 'TJANSTER.md').write_text('förra')
(pt_u / 'atelje' / 'KOMPLETTERING.json').write_text(json.dumps({'varfor': 'en annan komposition', 'referens': {'kandidater': [{'namn': 'ny', 'adress': 'https://exempel.se/', 'roll': 'hantverk'}]},
                                                                'tjanster': {'fragor': [{'tjanst': 'refero', 'fraga': 'typografisk riktning', 'typ': 'stil'}]}}))
res_pt = sk.komplettera('pt-prov', pt_u / 'atelje' / 'KOMPLETTERING.json', pt_u / 'atelje', pt_und, kor=kor_pt)
upp_ = json.loads(next(pt_u.glob('REFERENSUPPDRAG-*.json')).read_text())
assert upp_['kompletterar'] == 'paket-v01' and res_pt['referens']['paket'].endswith('paket-v02') and res_pt['tjanster']['rc'] == 0, res_pt
assert not (pt_u / 'atelje' / 'KOMPLETTERING.json').exists() and list((pt_u / 'atelje' / 'kompletteringar').glob('*-svar.json'))
assert (pt_u / 'referenser' / 'tjanster' / 'TJANSTER.md').read_text() == 'förra', 'den förra rapporten flyttar referenstjanster.samla själv (en plats), inte kompletteringen'
assert [Path(x[2]).name for x in anrop_pt] == ['referens.py', 'referenstjanster.py'] and 'en annan komposition' in '\n'.join(sk.kompletteringsrader(res_pt))
# förfiningen: research emellan, och TILLBAKA.md ger tillbaka
fr_rot = pt_u / 'atelje-fr'; fr_rot.mkdir()
anrop_fr = []


lamna_fr = []


def sess_fr(prompt, verktyg, ut, **kw):
    anrop_fr.append(prompt)
    if len(anrop_fr) == 1:
        (fr_rot / sk.KOMPLETTERING).write_text('{}')
    if lamna_fr:
        (fr_rot / 'TILLBAKA.md').write_text('grundidén bär inte')
    return {'session_id': None, 'num_turns': 3}


gamla_fr = (at_pt.session, at_pt.komplettera)
at_pt.session = sess_fr
at_pt.komplettera = lambda slug, fil, rot: (Path(fil).unlink(), {'tid': 't', 'varfor': 'mer', 'referens': {'rc': 0, 'paket': 'p'}})[1]
try:
    st_fr = {'faser': {}}
    assert at_pt.forfina('pt-prov', fr_rot, st_fr, lambda: None) == 'klar'
    (fr_rot / 'TILLBAKA.md').write_text('skriven av någon annan')  # en främmande TILLBAKA.md räknas inte; den flyttas undan
    assert at_pt.forfina('pt-prov', fr_rot, {'faser': {}}, lambda: None) == 'klar' and list((fr_rot / 'kompletteringar').glob('TILLBAKA-fore-forfiningen-*.md'))
    lamna_fr.append(1)  # förfiningens egen TILLBAKA.md gäller
    assert at_pt.forfina('pt-prov', fr_rot, {'faser': {}}, lambda: None) == 'tillbaka'
finally:
    at_pt.session, at_pt.komplettera = gamla_fr
assert len(anrop_fr) == 4 and 'Researchen du begärde' in anrop_fr[1] and st_fr['kompletteringar'][0]['fas'] == 'forfina' and st_fr['faser']['forfina']['sessioner'][0]['num_turns'] == 3, st_fr
# slutdomen: före (valets bilder) mot efter (den förfinade startsidan) med samma panel; vinnaren blir den förfinade med DESIGN.md
sd_rot = pt_u / 'atelje-sd'; (sd_rot / '1').mkdir(parents=True); (sd_rot / 'vinnare' / 'bilder').mkdir(parents=True)
for n_ in ('vy-390-ruta-01.png', 'vy-1440-ruta-01.png', 'vy-390-hela.png', 'vy-1440-hela.png'):
    (sd_rot / '1' / n_).write_bytes(b'f')
(sd_rot / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'filer': {}}))
sajt_sd = at_pt.KUNDER / 'pt-prov' / 'sajt'; (sajt_sd / 'src' / 'pages').mkdir(parents=True, exist_ok=True)
(sajt_sd / 'src' / 'pages' / 'index.astro').write_text('<p>förfinad</p>')
(sajt_sd / 'DESIGN.md').write_text('ingen giltig')


class Srv_:
    url = 'http://x'

    def __init__(self, *a):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def kor_sd(args, timeout=0):
    ut_ = Path(args[args.index('--ut') + 1])
    for n_ in ('vy-390-ruta-01.png', 'vy-1440-ruta-01.png', 'vy-390-hela.png', 'vy-1440-hela.png', 'vy-390-forsta.png'):
        (ut_ / n_).write_bytes(b'e')
    return 0, ''


paneler_ = []


def panel_sd(slug, rot, slut=False, svagheter=None):
    paneler_.append((rot.name, slut, svagheter))
    return {'val': 2, 'godkanda': [2], 'poang': {1: 1, 2: 5}, 'nivaer': {1: {'a': 'nastan'}, 2: {'a': 'over'}}, 'ribban': {1: {'a': False}, 2: {'a': True}}, 'panel': {}, 'fel': []}


gamla_sd = (at_pt.bygg, at_pt.prova.kor, at_pt.prova.Server, at_pt.panel)
at_pt.bygg, at_pt.prova.kor, at_pt.prova.Server, at_pt.panel = (lambda slug: (0, '')), kor_sd, Srv_, panel_sd
try:
    u_sd = at_pt.slutdom('pt-prov', sd_rot, {'faser': {}}, lambda: None)
finally:
    at_pt.bygg, at_pt.prova.kor, at_pt.prova.Server, at_pt.panel = gamla_sd
assert u_sd['over_ribban'] and u_sd['battre'] and paneler_ == [('slutdom', True, [])] and 'Synligt bättre efter förfiningen: **ja**' in (sd_rot / 'SLUTDOM.md').read_text(), (u_sd, paneler_)
vj_sd = json.loads((sd_rot / 'VINNARE.json').read_text())
assert (sd_rot / 'vinnare' / 'kod' / 'index.astro').read_text() == '<p>förfinad</p>' and vj_sd['forfinad']['slutdom']['battre'] and not vj_sd['design']['giltig'] and 'DESIGN.md' in vj_sd['filer'], vj_sd
assert sorted(p.name for p in (sd_rot / 'slutdom' / '1').iterdir()) == ['vy-1440-hela.png', 'vy-1440-ruta-01.png', 'vy-390-hela.png', 'vy-390-ruta-01.png']
# läsningen per förhandsvarv i ordning och metodkvittot, ur ett transkript
pt_kat = tmp / 'pt-projekt' / '-x'; pt_kat.mkdir(parents=True); bk_pt.PROJEKT = pt_kat.parent
rot_bk = bk_pt.ROOT; bk_pt.ROOT = tmp
sid_pt = '00000000-0000-4000-8000-000000000055'
v1_, v2_ = 'underlag/pt-prov/forhand/start/varv-01', 'underlag/pt-prov/forhand/start/varv-02'
rad_ = lambda c: json.dumps({'type': 'assistant', 'message': {'content': [c]}})  # noqa: E731
svar_ = lambda i, text: json.dumps({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': i, 'content': text}]}})  # noqa: E731
las_ = lambda i, v: rad_({'type': 'tool_use', 'id': i, 'name': 'Read', 'input': {'file_path': str(tmp / v)}})  # noqa: E731
h_ = [las_('m1', 'kunskap/bild.md'), svar_('m1', 'syntetisk hel läsning'),
      rad_({'type': 'tool_use', 'id': 's1', 'name': 'Skill', 'input': {'skill': 'better-layout'}}), svar_('s1', 'Launching skill: better-layout'),
      rad_({'type': 'tool_use', 'id': 'b1', 'name': 'Bash', 'input': {'command': '.venv/bin/python kontroller/forhandsvisa.py pt-prov'}}), svar_('b1', '- %s/vy-390-forsta.png' % v1_),
      *[las_('r%d' % i, '%s/%s' % (v1_, n)) for i, n in enumerate(bk_pt.VARVBILDER)], las_('rr', 'underlag/pt-prov/referenser/ref.png'),
      rad_({'type': 'tool_use', 'id': 'w1', 'name': 'Edit', 'input': {'file_path': str(tmp / 'kunder/pt-prov/sajt/src/pages/index.astro')}}), las_('m2', 'kunskap/copy-kontroll.md'), svar_('m2', 'syntetisk hel läsning'),
      rad_({'type': 'tool_use', 'id': 'b2', 'name': 'Bash', 'input': {'command': '.venv/bin/python kontroller/forhandsvisa.py pt-prov'}}), svar_('b2', '- %s/vy-390-forsta.png' % v2_),
      las_('r9', '%s/vy-390-forsta.png' % v2_), rad_({'type': 'tool_use', 'id': 'w2', 'name': 'Write', 'input': {'file_path': str(tmp / 'kunder/pt-prov/sajt/src/pages/index.astro')}}),
      las_('r10', '%s/vy-1440-forsta.png' % v2_)]
(pt_kat / (sid_pt + '.jsonl')).write_text('\n'.join(h_) + '\n')
try:
    vo_ = bk_pt.varvordning(sid_pt, 'pt-prov', ['underlag/pt-prov/referenser/ref.png'])
    assert [(x['varv'], x['lasta'], x['kravda']) for x in vo_['varv']] == [('varv-01', 5, 5), ('varv-02', 1, 5)] and vo_['varv'][1]['slutar'].startswith('en ändring'), vo_
    assert 'underlag/pt-prov/forhand/start/varv-02/vy-1440-forsta.png' in vo_['varv'][1]['saknas'], 'en bild läst efter nästa ändring räknas inte i varvet'
    ml_ = bk_pt.metodlasning(sid_pt, ['kunskap/bild.md', 'kunskap/copy-kontroll.md', 'kunskap/byggstandard.md'], ['better-layout', 'better-ui'], 'kunder/pt-prov/sajt/src/')
    assert ml_['fore'] == ['kunskap/bild.md', '.claude/skills/better-layout/SKILL.md'] and ml_['efter'] == ['kunskap/copy-kontroll.md'] \
        and ml_['saknas'] == ['kunskap/byggstandard.md', '.claude/skills/better-ui/SKILL.md'] and ml_['skill_anrop'] == ['better-layout'], ml_
    # redovisningen ur transkriptet
    (fr_rot / 'svar-forfina.json').write_text(json.dumps({'session_id': sid_pt, 'num_turns': 9, 'duration_ms': 120000}))
    red_ = at_pt.redovisa('pt-prov', fr_rot, {'lage': 'ny', 'steg': 'klar', 'faser': {'slutdom': {'over_ribban': True, 'battre': True, 'poang': {'fore': 1, 'efter': 5}}}}).read_text()
    assert '| forfina | svar-forfina.json | 9 | 2 |' in red_ and 'better-layout' in red_ and 'varv-01 ' in red_ and 'Slutdomen' in red_ and 'synligt bättre: ja' in red_, red_
finally:
    bk_pt.ROOT = rot_bk
import hashlib as hashlib_om  # noqa: E402


def hash_om(d):
    """Versionens hash räknad av provet självt, oberoende av koden som prövas (som kandidater.version): sha256 över
    DESIGN.md, kod/, kod-src/ och fryst material i katalogen d, utan länkar."""
    h_ = hashlib_om.sha256()
    d = Path(d)
    if (d / 'DESIGN.md').is_file() and not (d / 'DESIGN.md').is_symlink():
        h_.update(b'DESIGN.md\0' + (d / 'DESIGN.md').read_bytes() + b'\0')
    for bas_ in (d / 'kod', d / 'kod-src'):
        if not bas_.is_dir() or bas_.is_symlink():
            continue
        for kat_, kats_, fns_ in os.walk(bas_, followlinks=False):
            kats_.sort()
            for fn_ in sorted(fns_):
                q_ = Path(kat_) / fn_
                if q_.is_symlink() or not q_.is_file():
                    continue
                h_.update(str(q_.relative_to(d)).encode() + b'\0' + q_.read_bytes() + b'\0')
    for q_ in sorted((d / 'material').rglob('*')):
        assert not q_.is_symlink(), 'arkiverat material får inte innehålla länkar'
        if q_.is_file():
            h_.update(str(q_.relative_to(d)).encode() + b'\0' + q_.read_bytes() + b'\0')
    return h_.hexdigest()


def kandidat_med_version(kdir_, sida, status='klar', titel=None, bilder=True):
    """En fotograferad kandidat: kod/, kod-src/, DESIGN.md och skärmbilderna i fyra bredder, versionen bevarad med koden
    i versioner/<v12>/ (som kandidater.fotografera och bevara_version) och i STATUS.json. Ger versionen."""
    for x_ in ('kod', 'kod-src/styles', 'bilder/start'):
        (kdir_ / x_).mkdir(parents=True, exist_ok=True)
    (kdir_ / 'kod' / 'index.astro').write_text(sida)
    (kdir_ / 'kod-src' / 'styles' / 'design.css').write_text(':root { --sida: "%s"; }\n' % sida)
    (kdir_ / 'DESIGN.md').write_text('# Design\n\n%s\n' % sida)
    if bilder:
        for vy_ in ('390', '768', '1280', '1440'):
            for s_ in ('forsta', 'hela'):
                (kdir_ / 'bilder' / 'start' / ('vy-%s-%s.png' % (vy_, s_))).write_bytes(b'\x89PNG ' + ('%s %s %s' % (sida, vy_, s_)).encode())
        (kdir_ / 'bilder' / 'start' / 'INSPEKTION.json').write_text('{}')  # ingen skärmbild
    v_ = hash_om(kdir_)
    m_ = kdir_ / 'versioner' / v_[:12]
    if not m_.exists():
        shutil.copytree(kdir_ / 'kod', m_ / 'kod')
        shutil.copytree(kdir_ / 'kod-src', m_ / 'kod-src')
        shutil.copy2(kdir_ / 'DESIGN.md', m_ / 'DESIGN.md')
        (m_ / 'VERSION').write_text(v_ + '\n')
    st_ = json.loads((kdir_ / 'STATUS.json').read_text()) if (kdir_ / 'STATUS.json').is_file() else {}
    (kdir_ / 'STATUS.json').write_text(json.dumps(dict(st_, id=kdir_.name, status=status, version=v_, **({'titel': titel} if titel else {}))))
    return v_


# omtaget (ägarens beslut 2026-10-06): designbesluten raderas, inget arkiv; fakta, bilder, texten, referenspaketen,
# domlogg och historik kvar; den dömda riktningen in i historiken först; en länk tas bort som länk, aldrig målet
(at_pt.KUNDER / 'pt-prov' / 'sajt' / 'src').mkdir(parents=True, exist_ok=True)
(pt_u / 'forhand').mkdir()
mal_lank = tmp / 'pt-utanfor-koncept.md'; mal_lank.write_text('ägarens fil utanför')
(pt_u / 'KONCEPT.md').symlink_to(mal_lank)
sk.lagg_till_dom('pt-prov', 'ägaren', 'ny_riktning', 'Fönstret bär inte heller.', underlag=pt_und)
fl_pt = at_pt.ta_bort_beslut('pt-prov')
assert sorted(fl_pt) == sorted(at_pt.rel(p) for p in (pt_u / 'REFERENSER.md', pt_u / 'KONCEPT.md', pt_u / 'atelje', pt_u / 'forhand', at_pt.KUNDER / 'pt-prov' / 'sajt')), fl_pt
assert not any(os.path.lexists(p) for p in (pt_u / 'REFERENSER.md', pt_u / 'KONCEPT.md', pt_u / 'atelje', pt_u / 'forhand', at_pt.KUNDER / 'pt-prov' / 'sajt')), 'designbesluten raderas'
assert mal_lank.read_text() == 'ägarens fil utanför', 'länkens mål rörs aldrig'
assert (pt_u / sk.DOMLOGG).is_file() and (pt_u / 'TEXTUNDERLAG.md').is_file() and (pt_u / 'referenser' / 'paket-v01').is_dir() and (pt_u / 'bilder').is_dir()
assert not hasattr(at_pt, 'ARKIV'), 'omtaget har inget arkiv'
assert sk.historik('pt-prov', pt_und)[-1]['utfall'] == 'underkänd av ägaren' and sk.historik('pt-prov', pt_und)[-1]['namn'] == 'Fönstret', sk.historik('pt-prov', pt_und)[-1]
# granskningarna av r92: utan en dom som gäller körningen raderas inget ägaren sett, och då stoppas inget heller (BÖR 3,
# KAN 1); körningen domen gäller är den som blev klar, eller startade om den föll (r92b, BÖR 1); en körning som redan
# står i historiken får tas bort; rester av ett avbrutet omtag städas (BÖR 2); en sajt som är ett git-repo raderas
# aldrig; en ogiltig slug raderar inget (KAN 9); bara kundens egna pågående flödessessioner avslutas (r92b, KAN 2)
falska = []


def falsk_process(namn):
    p_ = subprocess.Popen(['bash', '-c', 'exec -a "%s" sleep 120' % namn])
    falska.append(p_)
    for _ in range(50):  # tills exec -a har bytt processens namn
        if namn.split()[0] in subprocess.run(['ps', '-o', 'command=', '-p', str(p_.pid)], capture_output=True, text=True).stdout:
            break
        threading.Event().wait(0.1)
    return p_


try:
    arbetare_ud = falsk_process('python -B kontroller/atelje.py pt-utan-dom --arbetare --lage ny')
    for sl_ud, st_ud in (('pt-utan-dom', {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z', 'pid': arbetare_ud.pid}),
                         ('pt-bokford', {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'}),
                         ('pt-foll', {'steg': 'fel', 'startad': '2026-10-06T04:00:00Z'})):
        ud_ = pt_und / sl_ud
        (ud_ / 'atelje' / 'kandidater' / 'k01').mkdir(parents=True)
        (ud_ / 'atelje' / 'STATUS.json').write_text(json.dumps(st_ud))
        (ud_ / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {'k01': {'titel': 'Byggdagboken', 'ide': 'en idé'}}}))
        (ud_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'klar'}))
    sk.lagg_till_dom('pt-utan-dom', 'ägaren', 'valj', 'Jag väljer k01.', underlag=pt_und)
    sk.lagg_till_dom('pt-bokford', 'ägaren', 'valj', 'Jag väljer k01.', underlag=pt_und)
    # pt-foll: körningen föll utan att bli klar; en dom och en historikpost från före dess start gäller inte den
    sk.lagg_till_dom('pt-foll', 'ägaren', 'ny_riktning', 'En gammal dom.', underlag=pt_und, tid='2026-10-06T03:30:00Z')
    sk.lagg_till_historik('pt-foll', [{'tid': '2026-10-05T00:00:00Z', 'kalla': 'x', 'namn': 'Äldre', 'utfall': 'underkänd av ägaren'}], pt_und)
    for sl_ud in ('pt-utan-dom', 'pt-foll'):
        ud_ = pt_und / sl_ud
        h_fore = sk.historik(sl_ud, pt_und)
        try:
            at_pt.ta_bort_beslut(sl_ud)
            raise AssertionError('%s: omtaget raderade utan en dom som gäller körningen' % sl_ud)
        except RuntimeError as e_:
            assert 'ingen dom från ägaren gäller körningen' in str(e_) and 'Byggdagboken' in str(e_) and 'Inget är borttaget' in str(e_), e_
        assert (ud_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').is_file() and sk.historik(sl_ud, pt_und) == h_fore, (sl_ud, 'inget borttaget, ingen ny historik')
    assert arbetare_ud.poll() is None, 'ett omtag som vägras stoppar ingen arbetare'
    sk.lagg_till_dom('pt-utan-dom', 'ägaren', 'ny_riktning', 'Inte den här heller.', underlag=pt_und)
    ud_ = pt_und / 'pt-utan-dom'
    (ud_ / '.borttaget-20261005T000000Z-atelje' / 'kvar').mkdir(parents=True)  # en rest av ett omtag som avbröts
    info_ud = {}
    fl_ud = at_pt.ta_bort_beslut('pt-utan-dom', info_ud)
    assert fl_ud == [at_pt.rel(ud_ / 'atelje')] and not os.path.lexists(ud_ / 'atelje') and not list(ud_.glob('.borttaget-*')), (fl_ud, list(ud_.iterdir()))
    assert info_ud['stoppade'] == [arbetare_ud.pid] and arbetare_ud.wait(10) is not None and info_ud['rester'] == [], info_ud
    assert [h['namn'] for h in sk.historik('pt-utan-dom', pt_und)] == ['Byggdagboken'], sk.historik('pt-utan-dom', pt_und)
    sk.lagg_till_dom('pt-foll', 'ägaren', 'ny_riktning', 'Ny riktning efter körningen som föll.', underlag=pt_und)
    assert at_pt.ta_bort_beslut('pt-foll') == [at_pt.rel(pt_und / 'pt-foll' / 'atelje')]
    assert [h['namn'] for h in sk.historik('pt-foll', pt_und)] == ['Äldre', 'Byggdagboken'], sk.historik('pt-foll', pt_und)
    sk.lagg_till_historik('pt-bokford', [{'kalla': 'för hand ur domen', 'namn': 'Byggdagboken', 'utfall': 'underkänd av ägaren'}], pt_und)
    assert at_pt.ta_bort_beslut('pt-bokford') == [at_pt.rel(pt_und / 'pt-bokford' / 'atelje')], 'en körning som redan står i historiken tas bort'
    (at_pt.KUNDER / 'pt-git' / 'sajt' / '.git').mkdir(parents=True)
    try:
        at_pt.ta_bort_beslut('pt-git')
        raise AssertionError('omtaget raderade en sajt som är ett git-repo')
    except RuntimeError as e_:
        assert 'eget git-repo' in str(e_) and (at_pt.KUNDER / 'pt-git' / 'sajt' / '.git').is_dir(), e_
    for ogiltig in ('../pt-prov', 'PT', ''):
        try:
            at_pt.ta_bort_beslut(ogiltig)
            raise AssertionError('ogiltig slug: %r' % ogiltig)
        except RuntimeError as e_:
            assert 'ogiltig slug' in str(e_), e_
    # omtaget görs helt eller inte alls: går ett namnbyte inte flyttas det redan flyttade tillbaka (r92b, KAN 3)
    ut_, kt_ = pt_und / 'pt-tillbaka', at_pt.KUNDER / 'pt-tillbaka'
    (ut_ / 'atelje').mkdir(parents=True); (ut_ / 'REFERENSER.md').write_text('r'); (kt_ / 'sajt' / 'src').mkdir(parents=True)
    (ut_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-06T03:00:00Z'}))
    sk.lagg_till_dom('pt-tillbaka', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    orig_rename = os.rename

    def nekad_rename(a_, b_, *r_, **k_):
        if Path(a_).name == 'sajt':
            raise PermissionError(13, 'Permission denied')
        return orig_rename(a_, b_, *r_, **k_)

    os.rename = nekad_rename
    try:
        at_pt.ta_bort_beslut('pt-tillbaka')
        raise AssertionError('omtaget gick igenom fast ett namnbyte föll')
    except RuntimeError as e_:
        assert 'omtaget gjordes inte' in str(e_) and 'allt står kvar' in str(e_), e_
    finally:
        os.rename = orig_rename
    assert (ut_ / 'REFERENSER.md').is_file() and (ut_ / 'atelje' / 'STATUS.json').is_file() and (kt_ / 'sajt' / 'src').is_dir(), 'allt tillbaka'
    assert not list(ut_.glob('.borttaget-*')) and not list(kt_.glob('.borttaget-*')), 'inget kvar undan'
    assert sorted(at_pt.ta_bort_beslut('pt-tillbaka')) == sorted(at_pt.rel(p) for p in (ut_ / 'REFERENSER.md', ut_ / 'atelje', kt_ / 'sajt'))
    assert not list(ut_.glob('.borttaget-*')) and not list(kt_.glob('.borttaget-*')) and not (kt_ / 'sajt').exists()
    # en start som pågår (steget startar utan arbetarens pid): omtaget väntar och raderar inget (r92b, BÖR 2)
    sa_ = pt_und / 'pt-start'
    (sa_ / 'atelje').mkdir(parents=True)
    (sa_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'startar', 'startad': at_pt.nu(), 'pid': None}))
    slug_env = os.environ.pop('NWP_SLUG', None)  # omtaget startas utanför ett bygge
    try:
        assert at_pt.main(['pt-start', '--ny-riktning']) == 5 and (sa_ / 'atelje' / 'STATUS.json').is_file(), 'en start pågår'
    finally:
        if slug_env is not None:
            os.environ['NWP_SLUG'] = slug_env
    # r92c: en äldre prototyp bredvid kandidater bokförs också (BÖR 1), ägarens före/efter-omdömen följer inte med
    # ateljén (KAN 7), en vald kandidat under förfining räknas som sedd (BÖR 2), och en historik som inte går att
    # tolka skrivs aldrig över (KAN 6)
    al_ = pt_und / 'pt-aldre'
    (al_ / 'prototyp').mkdir(parents=True); (al_ / 'atelje' / 'kandidater' / 'k01').mkdir(parents=True)
    (al_ / 'prototyp' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-06T02:00:00Z'}))
    (al_ / 'REFERENSER.md').write_text('Huvudreferens: Ashton — stenduk och falurött\n')
    (al_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'}))
    (al_ / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {'k01': {'titel': 'Byggdagboken', 'ide': 'en idé'}}}))
    (al_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'klar'}))
    (al_ / 'atelje' / 'FORBATTRING-AGAREN.json').write_text('[{"omdome": "efter är bättre"}]')
    (al_ / 'atelje' / 'AGARENS-DOM.json').write_text('{"1": "blind dom"}')
    (al_ / 'atelje' / 'omgang-1').mkdir(); (al_ / 'atelje' / 'omgang-1' / 'AGARENS-DOM.json').write_text('{"2": "äldre blind dom"}')
    (al_ / 'prototyp' / 'AGARENS-DOM.json').write_text('{"0": "domen över den äldre prototypen"}')  # dashboarden 2026-10-05 (r93, BÖR 3)
    sk.lagg_till_dom('pt-aldre', 'ägaren', 'ny_riktning', 'Ingen av dem.', underlag=pt_und)
    info_al = {}
    assert sorted(at_pt.ta_bort_beslut('pt-aldre', info_al)) == sorted(at_pt.rel(p) for p in (al_ / 'REFERENSER.md', al_ / 'atelje', al_ / 'prototyp'))
    h_al = sk.historik('pt-aldre', pt_und)
    assert [h['namn'] for h in h_al] == ['Byggdagboken', 'riktningen på huvudreferensen Ashton'], h_al
    assert h_al[1]['utfall'] == 'borttagen vid ett omtag, utan egen dom' and h_al[1]['kritik'] == '', ('ingen lånad dom (r92d, KAN 3)', h_al[1])
    beh_ = {str(f_.relative_to(al_ / 'agarens-omdomen')).split('/', 1)[1]: f_.read_text() for f_ in (al_ / 'agarens-omdomen').glob('*/**/*.json')}
    assert beh_ == {'atelje/FORBATTRING-AGAREN.json': '[{"omdome": "efter är bättre"}]', 'atelje/AGARENS-DOM.json': '{"1": "blind dom"}',
                    'atelje/omgang-1/AGARENS-DOM.json': '{"2": "äldre blind dom"}',
                    'prototyp/AGARENS-DOM.json': '{"0": "domen över den äldre prototypen"}'}, ('ägarens egna omdömen kopierade med sin plats', beh_)
    assert len(info_al['behallna']) == 4 and not (al_ / 'atelje').exists() and not (al_ / 'prototyp').exists(), info_al
    fo_ = pt_und / 'pt-forfining'
    (fo_ / 'atelje' / 'kandidater' / 'k01').mkdir(parents=True)
    (fo_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'startad': '2026-10-06T04:00:00Z'}))
    (fo_ / 'atelje' / 'kandidater' / 'k02').mkdir()
    (fo_ / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': '2026-10-06T03:10:00Z', 'kandidater': {
        'k01': {'titel': 'Den valda', 'ide': 'en idé'}, 'k02': {'titel': 'Den som föll', 'ide': 'en idé'}}}))
    (fo_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'under_arbete', 'fotograferad': '2026-10-06T03:00:00Z'}))
    (fo_ / 'atelje' / 'kandidater' / 'k02' / 'STATUS.json').write_text(json.dumps({'status': 'fel', 'fotograferad': '2026-10-06T03:00:00Z'}))
    # den valda versionen är bevarad (efter_beslut), och kandidaten står under förfining utan version: omtaget sparar den valda
    v_fo = kandidat_med_version(fo_ / 'atelje' / 'kandidater' / 'k01', '<h1>Den valda</h1>')
    shutil.copytree(fo_ / 'atelje' / 'kandidater' / 'k01' / 'bilder', fo_ / 'atelje' / 'kandidater' / 'k01' / 'versioner' / v_fo[:12] / 'bilder')
    (fo_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'under_arbete', 'fotograferad': '2026-10-06T03:00:00Z'}))
    sk.lagg_till_dom('pt-forfining', 'ägaren', 'valj', 'Förfina k01.', underlag=pt_und, tid='2026-10-06T03:50:00Z',
                     kandidater=[{'id': 'k01', 'version': v_fo, 'plan': '2026-10-06T03:10:00Z'}, {'id': 'k02', 'version': 'v1', 'plan': 'en annan plan'}])
    try:
        at_pt.ta_bort_beslut('pt-forfining')
        raise AssertionError('en vald kandidat under förfining raderades utan dom')
    except RuntimeError as e_:
        assert 'Den valda' in str(e_) and 'Den som föll' not in str(e_), ('vald i domen för planen är sedd; en som föll är det inte (r92d, BÖR 1)', e_)
    th_ = pt_und / 'pt-trasig-historik'
    (th_ / 'atelje' / 'kandidater' / 'k01').mkdir(parents=True)
    (th_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'}))
    (th_ / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {'k01': {'titel': 'Byggdagboken', 'ide': 'en idé'}}}))
    (th_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'klar'}))
    (th_ / sk.HISTORIK).write_text('{trasig')
    sk.lagg_till_dom('pt-trasig-historik', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    arbetare_th = falsk_process('python -B kontroller/atelje.py pt-trasig-historik --arbetare --lage ny')
    (th_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z', 'pid': arbetare_th.pid}))
    try:
        at_pt.ta_bort_beslut('pt-trasig-historik')
        raise AssertionError('en historik som inte går att tolka skrevs över')
    except RuntimeError as e_:
        assert 'går inte att tolka' in str(e_) and arbetare_th.poll() is None, ('prövas innan något stoppas (r92d, KAN 4)', e_)
    # namnlösa historikposter står kvar när historiken skrivs om (r92d, KAN 6)
    (pt_und / 'pt-namnlos').mkdir()
    sk.lagg_till_historik('pt-namnlos', [{'kalla': 'x', 'utfall': 'utan namn'}], pt_und)
    sk.lagg_till_historik('pt-namnlos', [{'kalla': 'y', 'namn': 'Med namn', 'utfall': 'u'}], pt_und)
    assert [x_.get('kalla') for x_ in json.loads((pt_und / 'pt-namnlos' / sk.HISTORIK).read_text())] == ['x', 'y']
    assert (th_ / sk.HISTORIK).read_text() == '{trasig' and (th_ / 'atelje' / 'kandidater' / 'k01' / 'STATUS.json').is_file(), 'historiken orörd, inget borttaget'
    # granskningen av r93: läget fulls förbättringsrunda (BÖR 1), rester och kataloger som inte går att lista (BÖR 2), den
    # äldre prototypens ägardom (BÖR 3), en kopia som faller (BÖR 4), bokföringen (BÖR 5), stämpeln (KAN 1), en länkad
    # målkatalog (KAN 3), udda historikposter (KAN 5), poster som inte är dict (KAN 7) och den äldre prototypen när
    # körningen redan bokförts (KAN 9)
    def atelje_med(slug_, kand, st_run=None, plan_tid='2026-10-06T03:10:00Z'):
        d_ = pt_und / slug_
        (d_ / 'atelje' / 'kandidater').mkdir(parents=True, exist_ok=True)
        (d_ / 'atelje' / 'STATUS.json').write_text(json.dumps(st_run or {'steg': 'fel', 'startad': '2026-10-06T04:00:00Z'}))
        (d_ / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': plan_tid, 'kandidater': {k_: {'titel': t_, 'ide': 'en idé'} for k_, (t_, _) in kand.items()}}))
        for k_, (_, s_) in kand.items():
            (d_ / 'atelje' / 'kandidater' / k_).mkdir(exist_ok=True)
            (d_ / 'atelje' / 'kandidater' / k_ / 'STATUS.json').write_text(json.dumps(s_))
        return d_
    fu_ = atelje_med('pt-full', {
        'k01': ('Visad, sedan förbättrad', {'status': 'under_arbete', 'forbattras': {'fore': 'v1'}, 'logg': [{'status': 'klar'}, {'status': 'under_arbete'}]}),
        'k02': ('Förbättras, loggen kapad', {'status': 'under_arbete', 'forbattras': {'fore': 'v1'}, 'logg': [{'status': 'under_arbete'}]}),
        'k03': ('Visad, sedan föll', {'status': 'fel', 'logg': [{'status': 'klar'}, {'status': 'fel'}]}),
        'k04': ('Aldrig visad', {'status': 'fel', 'fotograferad': '2026-10-06T03:30:00Z', 'logg': [{'status': 'under_arbete'}, {'status': 'fel'}]})})
    try:
        at_pt.ta_bort_beslut('pt-full')
        raise AssertionError('läget full: en visad kandidat i förbättringsrundan raderades utan dom')
    except RuntimeError as e_:
        assert all(t_ in str(e_) for t_ in ('Visad, sedan förbättrad', 'Förbättras, loggen kapad', 'Visad, sedan föll')) and 'Aldrig visad' not in str(e_), e_
    sk.lagg_till_dom('pt-full', 'ägaren', 'ny_riktning', 'Ingen av dem.', underlag=pt_und)
    at_pt.ta_bort_beslut('pt-full')
    assert [h['namn'] for h in sk.historik('pt-full', pt_und)] == ['Visad, sedan förbättrad', 'Förbättras, loggen kapad', 'Visad, sedan föll'], sk.historik('pt-full', pt_und)
    # bokföringen: den valda i förfiningen förs in, den som föll inte (BÖR 5)
    sk.lagg_till_dom('pt-forfining', 'ägaren', 'ny_riktning', 'Inte den heller.', underlag=pt_und)
    at_pt.ta_bort_beslut('pt-forfining')
    assert [h['namn'] for h in sk.historik('pt-forfining', pt_und)] == ['Den valda'], sk.historik('pt-forfining', pt_und)
    # en rest efter ett omtag som avbröts mellan namnbyte och radering, med ägarens dom i en omgång, och en fil som rest
    re_ = atelje_med('pt-rest', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (re_ / '.borttaget-20261005T000000Z-1-atelje' / 'omgang-1').mkdir(parents=True)
    (re_ / '.borttaget-20261005T000000Z-1-atelje' / 'omgang-1' / 'AGARENS-DOM.json').write_text('{"1": "dom i en rest"}')
    (re_ / '.borttaget-20261005T000000Z-1-REFERENSER.md').write_text('r')
    (re_ / 'atelje' / '.AGARENS-DOM.json.tmp4242').write_text('{"1": "halv skrivning"}')  # dashboardens temporärfil (KAN 2)
    sk.lagg_till_dom('pt-rest', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    info_re = {}
    at_pt.ta_bort_beslut('pt-rest', info_re)
    beh_re = {str(f_.relative_to(re_ / 'agarens-omdomen')).split('/', 1)[1]: f_.read_text() for f_ in (re_ / 'agarens-omdomen').glob('*/**/*') if f_.is_file()}
    assert beh_re == {'tidigare-omtag/.borttaget-20261005T000000Z-1-atelje/omgang-1/AGARENS-DOM.json': '{"1": "dom i en rest"}',
                      'atelje/.AGARENS-DOM.json.tmp4242': '{"1": "halv skrivning"}'}, beh_re
    assert not list(re_.glob('.borttaget-*')) and info_re['rester'] == [], (list(re_.iterdir()), info_re)
    # en katalog som inte går att lista: inget stoppas och inget flyttas (BÖR 2)
    ol_ = atelje_med('pt-olasbar', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (ol_ / 'atelje' / 'foregaende' / 'x').mkdir(parents=True)
    sk.lagg_till_dom('pt-olasbar', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    arbetare_ol = falsk_process('python -B kontroller/atelje.py pt-olasbar --arbetare --lage ny')
    (ol_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z', 'pid': arbetare_ol.pid}))
    os.chmod(ol_ / 'atelje' / 'foregaende' / 'x', 0)
    try:
        at_pt.ta_bort_beslut('pt-olasbar')
        raise AssertionError('omtaget gick igenom fast en katalog inte gick att lista')
    except RuntimeError as e_:
        assert 'går inte att gå igenom' in str(e_) and arbetare_ol.poll() is None and (ol_ / 'atelje' / 'STATUS.json').is_file(), e_
    finally:
        os.chmod(ol_ / 'atelje' / 'foregaende' / 'x', 0o755)
    # en kopia som faller: allt flyttas tillbaka, inget raderas, inga halva kopior, ingen ny historik (BÖR 4)
    ko_ = atelje_med('pt-kopiefel', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (ko_ / 'atelje' / 'AGARENS-DOM.json').write_text('{"1": "dom"}')
    (ko_ / 'atelje' / 'omgang-1').mkdir(); (ko_ / 'atelje' / 'omgang-1' / 'AGARENS-DOM.json').write_text('{"2": "äldre"}')
    sk.lagg_till_dom('pt-kopiefel', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    orig_copy2 = at_pt.shutil.copy2

    def nekad_copy2(a_, b_, *r_, **k_):
        if 'omgang-1' in str(a_):
            raise PermissionError(13, 'Permission denied')
        return orig_copy2(a_, b_, *r_, **k_)

    at_pt.shutil.copy2 = nekad_copy2
    try:
        at_pt.ta_bort_beslut('pt-kopiefel')
        raise AssertionError('omtaget gick igenom fast en kopia föll')
    except RuntimeError as e_:
        assert 'omtaget gjordes inte' in str(e_) and 'allt annat står kvar' in str(e_), e_
    finally:
        at_pt.shutil.copy2 = orig_copy2
    assert (ko_ / 'atelje' / 'AGARENS-DOM.json').read_text() == '{"1": "dom"}' and (ko_ / 'atelje' / 'omgang-1' / 'AGARENS-DOM.json').is_file()
    assert not list(ko_.glob('.borttaget-*')) and not list((ko_ / 'agarens-omdomen').glob('*')), 'inget borttaget, inga halva kopior'
    assert [h['namn'] for h in sk.historik('pt-kopiefel', pt_und)] == ['En'], 'historiken skrivs före namnbytena (uppföljningen, BÖR 6)'
    # ett avbrott (Ctrl-C) under kopian: allt tillbaka och avbrottet går vidare; ett nytt försök dubblerar inte historiken
    def avbruten_copy2(a_, b_, *r_, **k_):
        raise KeyboardInterrupt()
    at_pt.shutil.copy2 = avbruten_copy2
    try:
        at_pt.ta_bort_beslut('pt-kopiefel')
        raise AssertionError('avbrottet gick inte vidare')
    except KeyboardInterrupt:
        pass
    finally:
        at_pt.shutil.copy2 = orig_copy2
    assert (ko_ / 'atelje' / 'AGARENS-DOM.json').is_file() and not list(ko_.glob('.borttaget-*')) and not list((ko_ / 'agarens-omdomen').glob('*')), 'allt tillbaka efter avbrottet'
    # SIGTERM under kopian: signalen blir ett undantag, allt flyttas tillbaka och processens egen hanterare återställs
    import signal as sig_omtag
    fore_sigterm = sig_omtag.getsignal(sig_omtag.SIGTERM)
    def sigterm_copy2(a_, b_, *r_, **k_):
        os.kill(os.getpid(), sig_omtag.SIGTERM)
        return orig_copy2(a_, b_, *r_, **k_)
    at_pt.shutil.copy2 = sigterm_copy2
    try:
        at_pt.ta_bort_beslut('pt-kopiefel')
        raise AssertionError('SIGTERM avbröt inte omtaget')
    except SystemExit as e_:
        assert e_.code == 128 + sig_omtag.SIGTERM, e_.code
    finally:
        at_pt.shutil.copy2 = orig_copy2
    assert (ko_ / 'atelje' / 'AGARENS-DOM.json').is_file() and not list(ko_.glob('.borttaget-*')) and not list((ko_ / 'agarens-omdomen').glob('*')), 'allt tillbaka efter SIGTERM'
    assert sig_omtag.getsignal(sig_omtag.SIGTERM) == fore_sigterm, 'SIGTERM-hanteraren återställd'
    at_pt.ta_bort_beslut('pt-kopiefel')
    assert [h['namn'] for h in sk.historik('pt-kopiefel', pt_und)] == ['En'] and not (ko_ / 'atelje').exists(), 'ingen dubblett, omtaget gjort'
    assert sorted(f_.read_text() for f_ in (ko_ / 'agarens-omdomen').glob('*/atelje/**/AGARENS-DOM.json')) == ['{"1": "dom"}', '{"2": "äldre"}']
    # en handskriven post med en tid som inte är ISO räknas inte som bokförd (uppföljningen, BÖR 7)
    iso_ = atelje_med('pt-iso', {'k01': ('Sedd', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (iso_ / sk.HISTORIK).write_text(json.dumps([{'namn': 'Förd för hand', 'utfall': 'underkänd av ägaren', 'tid': 5}]))
    try:
        at_pt.ta_bort_beslut('pt-iso')
        raise AssertionError('en tid som inte är ISO släppte igenom omtaget utan dom')
    except RuntimeError as e_:
        assert 'ingen dom från ägaren' in str(e_) and (iso_ / 'atelje').is_dir(), e_
    # namnbytet faller: ägarens filer står kvar i ateljén, ingen kopia (KAN 7, M14)
    (ut_ / 'atelje').mkdir(parents=True, exist_ok=True); (ut_ / 'atelje' / 'AGARENS-DOM.json').write_text('{"1": "x"}')
    (kt_ / 'sajt' / 'src').mkdir(parents=True, exist_ok=True)
    sk.lagg_till_dom('pt-tillbaka', 'ägaren', 'ny_riktning', 'Igen.', underlag=pt_und)
    os.rename = nekad_rename
    try:
        at_pt.ta_bort_beslut('pt-tillbaka')
        raise AssertionError('omtaget gick igenom fast ett namnbyte föll')
    except RuntimeError:
        pass
    finally:
        os.rename = orig_rename
    assert (ut_ / 'atelje' / 'AGARENS-DOM.json').read_text() == '{"1": "x"}' and not (ut_ / 'agarens-omdomen').exists(), 'ägarens fil kvar, ingen kopia'
    # två omtag i samma process och sekund får olika stämplar (KAN 1)
    orig_nu = at_pt.nu
    at_pt.nu = lambda: '2026-10-06T12:00:00Z'
    try:
        for i_ in (1, 2):
            st_ = atelje_med('pt-stampel', {'k01': ('En %d' % i_, {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T0%d:00:00Z' % (i_ + 2)}, plan_tid='plan-%d' % i_)
            (st_ / 'atelje' / 'AGARENS-DOM.json').write_text('{"%d": "dom %d"}' % (i_, i_))
            sk.lagg_till_dom('pt-stampel', 'ägaren', 'ny_riktning', 'Omtag %d.' % i_, underlag=pt_und)
            at_pt.ta_bort_beslut('pt-stampel')
    finally:
        at_pt.nu = orig_nu
    assert sorted(f_.read_text() for f_ in (pt_und / 'pt-stampel' / 'agarens-omdomen').glob('*/atelje/AGARENS-DOM.json')) == ['{"1": "dom 1"}', '{"2": "dom 2"}']
    # agarens-omdomen som länk: inget tas bort (KAN 3)
    la_ = atelje_med('pt-lank', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (tmp / 'pt-lank-mal').mkdir(); (la_ / 'agarens-omdomen').symlink_to(tmp / 'pt-lank-mal')
    sk.lagg_till_dom('pt-lank', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    try:
        at_pt.ta_bort_beslut('pt-lank')
        raise AssertionError('omtaget skrev genom en länk')
    except RuntimeError as e_:
        assert 'länk' in str(e_) and (la_ / 'atelje').is_dir(), e_
    # udda historikposter (förda för hand) fäller inte omtaget med TypeError (KAN 5); poster som inte är dict står kvar (KAN 7, M16)
    ud2_ = atelje_med('pt-udda', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (ud2_ / sk.HISTORIK).write_text(json.dumps([1, 'text', None, {'namn': 'Förd för hand', 'utfall': None, 'tid': 5}]))
    sk.lagg_till_dom('pt-udda', 'ägaren', 'ny_riktning', 'Ny riktning.', underlag=pt_und)
    at_pt.ta_bort_beslut('pt-udda')
    h_ud = json.loads((ud2_ / sk.HISTORIK).read_text())
    assert h_ud[:4] == [1, 'text', None, {'namn': 'Förd för hand', 'utfall': None, 'tid': 5}] and h_ud[4]['namn'] == 'En', h_ud
    # den äldre prototypen när körningen redan bokförts för hand: en post utan lånad dom (KAN 9)
    ab_ = atelje_med('pt-aldre-bokford', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (ab_ / 'prototyp').mkdir(); (ab_ / 'prototyp' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-06T02:00:00Z'}))
    (ab_ / 'REFERENSER.md').write_text('Huvudreferens: Ashton — stenduk och falurött\n')
    sk.lagg_till_historik('pt-aldre-bokford', [{'kalla': 'för hand ur domen', 'namn': 'En', 'utfall': 'underkänd av ägaren', 'tid': '2026-10-06T03:30:00Z'},
                                               {'kalla': 'för hand', 'namn': 'riktningen på huvudreferensen Ashton', 'utfall': 'underkänd av ägaren', 'tid': '2026-10-06T03:30:00Z'}], pt_und)
    at_pt.ta_bort_beslut('pt-aldre-bokford')
    assert [h['namn'] for h in sk.historik('pt-aldre-bokford', pt_und)] == ['En', 'riktningen på huvudreferensen Ashton'], 'redan bokförd, ingen dubblett'
    ab2_ = atelje_med('pt-aldre-bokford2', {'k01': ('En', {'status': 'klar'})}, {'steg': 'klar_for_bedomning', 'klar': '2026-10-06T03:00:00Z'})
    (ab2_ / 'prototyp').mkdir(); (ab2_ / 'prototyp' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-06T02:00:00Z'}))
    (ab2_ / 'REFERENSER.md').write_text('Huvudreferens: Bergman — kalkputs\n')
    sk.lagg_till_historik('pt-aldre-bokford2', [{'kalla': 'för hand ur domen', 'namn': 'En', 'utfall': 'underkänd av ägaren', 'tid': '2026-10-06T03:30:00Z'}], pt_und)
    at_pt.ta_bort_beslut('pt-aldre-bokford2')
    h_ab2 = sk.historik('pt-aldre-bokford2', pt_und)
    assert [h['namn'] for h in h_ab2] == ['En', 'riktningen på huvudreferensen Bergman'] and h_ab2[1]['utfall'] == 'borttagen vid ett omtag, utan egen dom', h_ab2
    # bara kundens egna pågående flödessessioner avslutas: en annan kunds session, en avslutad post och en process som
    # inte är en flödessession lämnas orörda
    sv_rot = tmp / 'sv-atelje'
    for d_ in ('k01', 'k02'):
        (sv_rot / 'kandidater' / d_).mkdir(parents=True)
    (sv_rot / 'sessioner').mkdir()
    egen = falsk_process('claude -p --allowedTools Read --settings kundvakt.py pt-sv /u')
    annan_kund = falsk_process('claude -p --allowedTools Read --settings kundvakt.py pt-annan /u Read(./kunder/pt-sv/**)')
    avslutad = falsk_process('claude -p --allowedTools Read --settings kundvakt.py pt-sv /v')
    vanlig = falsk_process('sleep-utan-namn')
    (sv_rot / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'under_arbete', 'session_pid': egen.pid}))
    (sv_rot / 'kandidater' / 'k02' / 'STATUS.json').write_text(json.dumps({'status': 'under_arbete', 'session_pid': annan_kund.pid}))
    (sv_rot / 'sessioner' / 'a.json').write_text(json.dumps({'pid': avslutad.pid, 'slut': '2026-10-06T10:00:00Z'}))
    (sv_rot / 'sessioner' / 'b.json').write_text(json.dumps({'pid': vanlig.pid}))
    # en session utan slug (startad utan kundvakt) känns igen genom förteckningens start; ett pid vars process startade
    # vid en annan tid (återanvänt) lämnas (r92c, KAN 5)
    utan_slug = falsk_process('claude -p --allowedTools Read --strict-mcp-config')
    ateranvand = falsk_process('claude -p --allowedTools Read --strict-mcp-config x')
    (sv_rot / 'sessioner' / 'c.json').write_text(json.dumps({'pid': utan_slug.pid, 'start': at_pt.nu()}))
    (sv_rot / 'sessioner' / 'd.json').write_text(json.dumps({'pid': ateranvand.pid, 'start': '2026-10-01T00:00:00Z'}))
    st_sv = at_pt.stoppa_kvarvarande('pt-sv', sv_rot, {'pid': vanlig.pid})  # arbetarens pid tillhör någon annan
    assert st_sv == sorted([egen.pid, utan_slug.pid]) and egen.wait(10) is not None and utan_slug.wait(10) is not None, st_sv
    assert annan_kund.poll() is None and avslutad.poll() is None and vanlig.poll() is None and ateranvand.poll() is None, 'bara kundens egna pågående sessioner'
finally:
    for p_ in falska:
        if p_.poll() is None:
            p_.kill()
            p_.wait(10)
# ===== ägarens beslut 2026-10-07: omtaget sparar det bedömda (skärmbilderna, versionshashen, domen, länken till design och
# kod, och underlaget som hashen räknas om ur) och registrerar det innan något raderas; faller sparandet raderas inget.
# Varje fall redovisas för sig: mot 84c6994, som raderade utan att spara, blir vart och ett rött =====
OMTAG_FEL = []


def omtagsfall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: omtaget 2026-10-07: ' + namn, file=sys.stderr)
        except Exception as e_:  # noqa: BLE001 — varje fall redovisas för sig
            OMTAG_FEL.append(namn)
            print('FEL: omtaget 2026-10-07: %s: %s: %s' % (namn, type(e_).__name__, str(e_)[:900]), file=sys.stderr)
        return f
    return kor_fallet


def omtagsplan(slug_, kand, st_run):
    """En körning i kandidatflödet: planen (tid P_OM), kandidaterna med riktiga versioner och kandidaternas projekt."""
    d_ = pt_und / slug_
    (d_ / 'atelje' / 'kandidater').mkdir(parents=True)
    (d_ / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': P_OM, 'kandidater': {k_: {'titel': t_, 'ide': 'en idé'} for k_, t_ in kand.items()}}))
    (d_ / 'atelje' / 'STATUS.json').write_text(json.dumps(dict({'kandidatflode': True}, **st_run)))
    for k_ in kand:
        (at_pt.KUNDER / slug_ / 'kandidater' / k_ / 'sajt' / 'src').mkdir(parents=True)
    return d_


P_OM = '2026-10-06T05:00:00Z'
KLAR_OM = {'steg': 'klar_for_bedomning', 'fas': 'forfining', 'startad': '2026-10-06T07:00:00Z', 'klar': '2026-10-06T08:00:00Z'}
bo_ = omtagsplan('pt-bedomt', {'k01': 'Byggdagboken', 'k02': 'Kartan', 'k03': 'Aldrig visad'}, KLAR_OM)
k1_ = bo_ / 'atelje' / 'kandidater' / 'k01'
v1a_ = kandidat_med_version(k1_, '<h1>Byggdagboken, skissen</h1>', titel='Byggdagboken')
shutil.copytree(k1_ / 'bilder', k1_ / 'versioner' / v1a_[:12] / 'bilder')  # den valda versionen bevaras med bilderna (efter_beslut)
bilder_v1a = {q_.name: q_.read_bytes() for q_ in (k1_ / 'bilder' / 'start').glob('vy-*.png')}
v1b_ = kandidat_med_version(k1_, '<h1>Byggdagboken, förfinad</h1>', status='forfinad')  # förfiningen: ny kod och nya bilder
v2_om = kandidat_med_version(bo_ / 'atelje' / 'kandidater' / 'k02', '<h1>Kartan</h1>', titel='Kartan')
v3_om = kandidat_med_version(bo_ / 'atelje' / 'kandidater' / 'k03', '<h1>Aldrig visad</h1>', status='fel')
sk.lagg_till_dom('pt-bedomt', 'ägaren', 'valj', 'Bygg vidare på dagboken.', underlag=pt_und, tid='2026-10-06T06:10:00Z',
                 kandidater=[{'id': 'k01', 'version': v1a_, 'plan': P_OM}], plan=P_OM)
sk.lagg_till_dom('pt-bedomt', 'ägaren', 'jamfor', 'Kartan bredvid.', underlag=pt_und, tid='2026-10-06T06:20:00Z',
                 kandidater=[{'id': 'k02', 'version': v2_om, 'plan': P_OM}], plan=P_OM)
sk.lagg_till_dom('pt-bedomt', 'ägaren', 'valj', 'En tidigare plan.', underlag=pt_und, tid='2026-10-06T04:00:00Z',
                 kandidater=[{'id': 'k03', 'version': v3_om, 'plan': 'en tidigare plan'}], plan='en tidigare plan')
sk.lagg_till_dom('pt-bedomt', 'panelen', 'valj', 'Panelen väljer.', underlag=pt_und, tid='2026-10-06T06:30:00Z',
                 kandidater=[{'id': 'k03', 'version': v3_om, 'plan': P_OM}])
sk.lagg_till_dom('pt-bedomt', 'ägaren', 'ny_riktning', 'Ingen av dem bär; börja om.', underlag=pt_und)
sk.lagg_till_dom('pt-bedomt', 'panelen', 'valj', 'Panelen efter ägaren.', underlag=pt_und, kandidater=[{'id': 'k02', 'version': v2_om, 'plan': P_OM}])  # inte domloggens sista rad (O5)
info_bo = {}
try:
    fl_bo = at_pt.ta_bort_beslut('pt-bedomt', info_bo)
except Exception as e_:  # noqa: BLE001 — fallen nedan redovisar det
    fl_bo = e_
stamplar_bo = sorted((bo_ / 'omtag').iterdir()) if (bo_ / 'omtag').is_dir() else []


@omtagsfall('det bedömda sparas och registreras i underlag/<slug>/omtag/<stämpel>/<kandidat>/<v12>/, och sedan raderas det som förut')
def _omtag_sparat():
    assert not isinstance(fl_bo, Exception), fl_bo
    assert len(stamplar_bo) == 1 and not stamplar_bo[0].name.startswith('.'), ('inget sparat och registrerat före raderingen', stamplar_bo)
    par_ = sorted((k_.parent.parent.name, k_.parent.name) for k_ in stamplar_bo[0].glob('*/*/KVITTO.json'))
    assert par_ == sorted([('k01', v1a_[:12]), ('k01', v1b_[:12]), ('k02', v2_om[:12])]), par_
    assert not (stamplar_bo[0] / 'k03').exists(), 'en kandidat som ägaren inte dömt sparas inte'
    assert sorted(info_bo['sparade']) == sorted('underlag/pt-bedomt/omtag/%s/%s/%s/KVITTO.json' % (stamplar_bo[0].name, k_, v_) for k_, v_ in par_), info_bo
    assert not (bo_ / 'atelje').exists() and not (at_pt.KUNDER / 'pt-bedomt' / 'kandidater').exists(), 'ateljén och projekten raderas'


@omtagsfall('hashen räknas om ur det sparade underlaget och stämmer, och kvittot har sha256 för varje sparad fil')
def _omtag_hash():
    assert stamplar_bo, 'inget sparat'
    for kv_ in sorted(stamplar_bo[0].glob('*/*/KVITTO.json')):
        k_, d_ = json.loads(kv_.read_text()), kv_.parent
        assert hash_om(d_ / 'underlag') == k_['version'] == k_['version_omraknad'] and k_['version'][:12] == d_.name, (kv_, k_['version'])
        assert k_['kandidat'] == d_.parent.name and k_['id'].endswith('-%s-%s' % (k_['kandidat'], d_.name)) and k_['tid'] and k_['plan'] == P_OM
        sparat_ = {q_.relative_to(d_).as_posix() for q_ in d_.rglob('*') if q_.is_file() and q_.name != 'KVITTO.json'}
        assert sparat_ == set(k_['filer']) and all(hashlib_om.sha256((d_ / f_).read_bytes()).hexdigest() == s_ for f_, s_ in k_['filer'].items()), kv_
        assert {f_ for f_ in k_['filer'] if f_.startswith('underlag/')} == {'underlag/DESIGN.md', 'underlag/kod/index.astro', 'underlag/kod-src/styles/design.css'}


@omtagsfall('bilderna i de bredder som dömdes, domarna med rad och radens sha256, och länken till design och kod')
def _omtag_bilder_domar():
    assert stamplar_bo, 'inget sparat'
    st_ = stamplar_bo[0]
    rader_ = (bo_ / sk.DOMLOGG).read_bytes().split(b'\n')
    beslut_ = {}
    for kv_ in sorted(st_.glob('*/*/KVITTO.json')):
        k_, d_ = json.loads(kv_.read_text()), kv_.parent
        assert sorted(k_['bilder']) == sorted('bilder/start/vy-%s-%s.png' % (b_, s_) for b_ in ('390', '768', '1280', '1440') for s_ in ('forsta', 'hela')), k_['bilder']
        assert 'bilder/start/INSPEKTION.json' not in k_['filer'] and not k_.get('bilder_saknas')
        assert k_['design'] == 'underlag/DESIGN.md' and (d_ / k_['design']).is_file() and 'underlag/kod/' in k_['kod'] and 'underlag/kod-src/' in k_['kod']
        assert k_['kalla']['projekt'] == 'kunder/pt-bedomt/kandidater/%s/sajt' % k_['kandidat'] and k_['kalla']['underlag'].startswith('underlag/pt-bedomt/atelje/kandidater/')
        for dm_ in k_['domar']:
            rad_ = rader_[dm_['rad'] - 1]
            assert json.loads(rad_) == dm_['post'] and hashlib_om.sha256(rad_).hexdigest() == dm_['sha256_rad'] and dm_['fil'] == 'underlag/pt-bedomt/%s' % sk.DOMLOGG
        beslut_[(k_['kandidat'], d_.name)] = [dm_['beslut'] for dm_ in k_['domar']]
    assert beslut_ == {('k01', v1a_[:12]): ['valj'], ('k01', v1b_[:12]): ['ny_riktning'], ('k02', v2_om[:12]): ['jamfor', 'ny_riktning']}, beslut_
    assert {q_.name: q_.read_bytes() for q_ in (st_ / 'k01' / v1a_[:12] / 'bilder' / 'start').glob('vy-*.png')} == bilder_v1a, 'den valda versionens egna bilder, ur versioner/'
    assert {h_['namn']: h_.get('sparat') for h_ in sk.historik('pt-bedomt', pt_und)} == {'Byggdagboken': 'omtag/%s/k01/' % st_.name, 'Kartan': 'omtag/%s/k02/' % st_.name}


@omtagsfall('faller sparandet, eller avbryts det, raderas inget och inget halvt sparat står kvar; när underlaget stämmer görs omtaget')
def _omtag_faller():
    fe_ = omtagsplan('pt-bedomt-fel', {'k01': 'Skissen'}, KLAR_OM)
    kf_ = fe_ / 'atelje' / 'kandidater' / 'k01'
    vf_ = kandidat_med_version(kf_, '<h1>Skissen</h1>', titel='Skissen')
    shutil.rmtree(kf_ / 'versioner')  # den bevarade versionen saknas,
    (kf_ / 'kod' / 'index.astro').write_text('<h1>ändrad efter fotograferingen</h1>')  # och kandidatens kod ger en annan hash
    sk.lagg_till_dom('pt-bedomt-fel', 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    h_fore = sk.historik('pt-bedomt-fel', pt_und)
    try:
        at_pt.ta_bort_beslut('pt-bedomt-fel')
        raise AssertionError('omtaget raderade fast det bedömda inte gick att spara')
    except RuntimeError as e_:
        assert 'det bedömda gick inte att spara' in str(e_) and 'inget är borttaget' in str(e_), e_
    assert (kf_ / 'kod' / 'index.astro').is_file() and (at_pt.KUNDER / 'pt-bedomt-fel' / 'kandidater' / 'k01' / 'sajt').is_dir() and not list(fe_.glob('.borttaget-*'))
    assert not list((fe_ / 'omtag').iterdir()) and sk.historik('pt-bedomt-fel', pt_und) == h_fore, 'inget halvt sparat, ingen historik'
    (kf_ / 'kod' / 'index.astro').write_text('<h1>Skissen</h1>')  # versionen stämmer igen
    orig_cf_ = at_pt.shutil.copyfile
    anrop_ = []

    def avbruten_cf(a_, b_, *r_, **k_):
        anrop_.append(1)
        if len(anrop_) == 2:
            raise KeyboardInterrupt()
        return orig_cf_(a_, b_, *r_, **k_)

    at_pt.shutil.copyfile = avbruten_cf
    try:
        at_pt.ta_bort_beslut('pt-bedomt-fel')
        raise AssertionError('avbrottet gick inte vidare')
    except KeyboardInterrupt:
        pass
    finally:
        at_pt.shutil.copyfile = orig_cf_
    assert (kf_ / 'kod' / 'index.astro').is_file() and not list((fe_ / 'omtag').iterdir()) and sk.historik('pt-bedomt-fel', pt_und) == h_fore, 'efter avbrottet'
    info_fe = {}
    at_pt.ta_bort_beslut('pt-bedomt-fel', info_fe)
    kv_ = list((fe_ / 'omtag').glob('*/k01/%s/KVITTO.json' % vf_[:12]))
    assert len(kv_) == 1 and hash_om(kv_[0].parent / 'underlag') == vf_ and not (fe_ / 'atelje').exists() and len(info_fe['sparade']) == 1, (kv_, info_fe)


@omtagsfall('ett omtag skriver aldrig det bedömda genom en länk: underlag/<slug>/omtag som länk stoppar omtaget')
def _omtag_lank():
    la_ = omtagsplan('pt-bedomt-lank', {'k01': 'Länken'}, KLAR_OM)
    kandidat_med_version(la_ / 'atelje' / 'kandidater' / 'k01', '<h1>Länken</h1>')
    (tmp / 'pt-omtag-utanfor').mkdir()
    (la_ / 'omtag').symlink_to(tmp / 'pt-omtag-utanfor', target_is_directory=True)
    sk.lagg_till_dom('pt-bedomt-lank', 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    try:
        at_pt.ta_bort_beslut('pt-bedomt-lank')
        raise AssertionError('omtaget skrev genom en länk')
    except RuntimeError as e_:
        assert 'länk' in str(e_) and (la_ / 'atelje' / 'kandidater' / 'k01' / 'kod').is_dir() and not list((tmp / 'pt-omtag-utanfor').iterdir()), e_


BARN_OM = '''
import os, sys, signal, shutil
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import atelje as at
at.UNDERLAG, at.KUNDER = Path(sys.argv[2]), Path(sys.argv[3])
slag, n = sys.argv[5], int(sys.argv[6])
orig = shutil.copyfile
anrop = []
def cf(a, b, *r, **k):
    anrop.append(1)
    if len(anrop) == n:
        os.kill(os.getpid(), signal.SIGTERM if slag == 'term' else signal.SIGKILL)
    return orig(a, b, *r, **k)
at.shutil.copyfile = cf
at.ta_bort_beslut(sys.argv[4])
print('KLART')
'''


def tva_kandidater(slug_):
    """En körning med två fotograferade kandidater som ägaren jämfört och sedan sagt ny riktning om."""
    d_ = omtagsplan(slug_, {'k01': 'Ett', 'k02': 'Två'}, KLAR_OM)
    v1 = kandidat_med_version(d_ / 'atelje' / 'kandidater' / 'k01', '<h1>Ett</h1>', titel='Ett')
    v2 = kandidat_med_version(d_ / 'atelje' / 'kandidater' / 'k02', '<h1>Två</h1>', titel='Två')
    sk.lagg_till_dom(slug_, 'ägaren', 'jamfor', 'Jämför.', underlag=pt_und, tid='2026-10-06T06:20:00Z',
                     kandidater=[{'id': 'k01', 'version': v1, 'plan': P_OM}, {'id': 'k02', 'version': v2, 'plan': P_OM}], plan=P_OM)
    sk.lagg_till_dom(slug_, 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    return d_, v1, v2


def barn_om(slug_, slag_, n_):
    """Omtaget i en egen process, med en riktig signal vid den n:te kopian i sparandet."""
    import subprocess as sp_om
    return sp_om.run([sys.executable, '-B', '-c', BARN_OM, str(Path(at_pt.__file__).resolve().parent), str(pt_und), str(at_pt.KUNDER), slug_,
                      slag_, str(n_)], capture_output=True, text=True, timeout=120, env=dict(os.environ, NWP_STARTKONTROLL='av'))


@omtagsfall('en kopia som skiljer sig från källan vid sparandet vägras: hashen räknas om ur det sparade (O3)')
def _omtag_skadad_kopia():
    sa_ = omtagsplan('pt-bedomt-skadad', {'k01': 'Ett'}, KLAR_OM)
    kandidat_med_version(sa_ / 'atelje' / 'kandidater' / 'k01', '<h1>Ett</h1>', titel='Ett')
    sk.lagg_till_dom('pt-bedomt-skadad', 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    orig_cf_ = at_pt.shutil.copyfile

    def skadad_cf(a_, b_, *r_, **k_):
        ut_ = orig_cf_(a_, b_, *r_, **k_)
        if str(b_).endswith('/underlag/kod/index.astro'):
            Path(b_).write_text('<h1>skadad i kopian</h1>')
        return ut_

    at_pt.shutil.copyfile = skadad_cf
    try:
        at_pt.ta_bort_beslut('pt-bedomt-skadad')
        raise AssertionError('omtaget registrerade en kopia som inte är den dömda versionen')
    except RuntimeError as e_:
        assert 'det bedömda gick inte att spara' in str(e_) and 'hashen' in str(e_), e_
    finally:
        at_pt.shutil.copyfile = orig_cf_
    assert (sa_ / 'atelje' / 'kandidater' / 'k01' / 'kod').is_dir() and not list((sa_ / 'omtag').iterdir()), 'inget sparat, inget raderat'


@omtagsfall('en körning som redan bokförts för hand: de kandidater ägaren sett sparas ändå (O6)')
def _omtag_bokford():
    bf_ = omtagsplan('pt-bedomt-bokford', {'k01': 'Ett'}, KLAR_OM)
    vb_ = kandidat_med_version(bf_ / 'atelje' / 'kandidater' / 'k01', '<h1>Ett</h1>', titel='Ett')
    sk.lagg_till_dom('pt-bedomt-bokford', 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    sk.lagg_till_historik('pt-bedomt-bokford', [{'kalla': 'för hand', 'namn': 'Ett', 'utfall': 'underkänd av ägaren', 'tid': '2026-10-06T09:00:00Z'}], pt_und)
    info_ = {}
    at_pt.ta_bort_beslut('pt-bedomt-bokford', info_)
    assert [x.split('/omtag/', 1)[1].split('/', 1)[1] for x in info_.get('sparade') or []] == ['k01/%s/KVITTO.json' % vb_[:12]], info_
    assert not (bf_ / 'atelje').exists()


@omtagsfall('en riktig SIGTERM mitt i sparandet: slutkod 143, inget sparat, ingen dold rest, ingen historik och inget raderat (O7)')
def _omtag_sigterm():
    import signal as sig_om
    te_, v1_, v2_ = tva_kandidater('pt-bedomt-term')
    r_ = barn_om('pt-bedomt-term', 'term', 5)
    assert r_.returncode == 128 + sig_om.SIGTERM, (r_.returncode, r_.stdout[-200:], r_.stderr[-400:])
    om_ = te_ / 'omtag'
    assert not (list(om_.iterdir()) if om_.is_dir() else []), ('inget sparat och ingen dold rest', list(om_.iterdir()))
    assert (te_ / 'atelje' / 'kandidater' / 'k01' / 'kod' / 'index.astro').is_file() and (at_pt.KUNDER / 'pt-bedomt-term' / 'kandidater').is_dir()
    assert not sk.historik('pt-bedomt-term', pt_und) and not list(te_.glob('.borttaget-*')), 'ingen historik, inget flyttat'


@omtagsfall('SIGKILL mitt i sparandet registrerar aldrig något halvt; nästa omtag tar bort den dolda resten och sparar allt (O8, KAN-3)')
def _omtag_sigkill():
    import signal as sig_om
    ki_, v1_, v2_ = tva_kandidater('pt-bedomt-kill')
    r_ = barn_om('pt-bedomt-kill', 'kill', 14)  # under den andra kandidaten
    assert r_.returncode == -sig_om.SIGKILL, (r_.returncode, r_.stderr[-400:])
    om_ = ki_ / 'omtag'
    dolda_ = [x.name for x in om_.iterdir() if x.name.startswith('.')]
    synliga_ = [x.name for x in om_.iterdir() if not x.name.startswith('.')]
    assert dolda_ and not synliga_, ('ett sparande som dog är aldrig registrerat: namnbytet kommer sist', dolda_, synliga_)
    assert (ki_ / 'atelje' / 'kandidater' / 'k02' / 'kod' / 'index.astro').is_file() and not sk.historik('pt-bedomt-kill', pt_und)
    # ett sparande som kan pågå (pid:en lever och startade före stämpeln) rörs inte; en rest vars pid fått en ny process
    # (startad efter stämpeln) är död och tas bort
    pagar_ = om_ / ('.%s-%d-7.tmp' % (at_pt.nu().replace(':', ''), os.getpid()))
    aterbrukad_ = om_ / ('.2026-01-01T000000Z-%d.tmp' % os.getpid())
    for x_ in (pagar_, aterbrukad_):
        (x_ / 'k01').mkdir(parents=True)
        (x_ / 'k01' / 'halv.txt').write_text('halvt sparat')
    info_ = {}
    at_pt.ta_bort_beslut('pt-bedomt-kill', info_)
    assert (pagar_ / 'k01' / 'halv.txt').is_file() and not os.path.lexists(aterbrukad_), sorted(x.name for x in om_.iterdir())
    shutil.rmtree(pagar_)
    efter_ = sorted(x.name for x in om_.iterdir())
    assert len(efter_) == 1 and not efter_[0].startswith('.') and len(info_['sparade']) == 2, (efter_, info_)
    for kv_ in (om_ / efter_[0]).glob('*/*/KVITTO.json'):
        assert hash_om(kv_.parent / 'underlag') == json.loads(kv_.read_text())['version']


@omtagsfall('den äldre utforskningen: vinnaren, slutdomens bilder, tidigare körningar och en äldre prototyp sparas före raderingen (BÖR-3)')
def _omtag_aldre_vagen():
    ae_ = pt_und / 'pt-bedomt-aldre'
    a_ = ae_ / 'atelje'
    filer_ae = {'vinnare/kod/index.astro': b'<h1>Vinnaren</h1>', 'vinnare/bilder/vy-390-forsta.png': b'\x89PNG vinnaren',
                'slutdom/1/vy-390-forsta.png': b'\x89PNG fore', 'slutdom/2/vy-390-forsta.png': b'\x89PNG efter',
                'foregaende/20261005T000000Z/vinnare/kod/index.astro': '<h1>Den förra vinnaren</h1>'.encode(),
                'foregaende/20261005T000000Z/KANDIDATPLAN.json': json.dumps({'tid': '2026-10-04T10:00:00Z', 'kandidater': {}}).encode()}
    for rel_, data_ in filer_ae.items():
        (a_ / rel_).parent.mkdir(parents=True, exist_ok=True)
        (a_ / rel_).write_bytes(data_)
    (a_ / 'vinnare' / 'node_modules' / 'p').mkdir(parents=True)
    (a_ / 'vinnare' / 'node_modules' / 'p' / 'x.js').write_text('härlett')  # följer inte med
    vinnare_filer = {r_[len('vinnare/'):]: hashlib_om.sha256(d_).hexdigest() for r_, d_ in filer_ae.items() if r_.startswith('vinnare/')}
    (a_ / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'filer': vinnare_filer}))
    (a_ / 'RIKTNINGAR.md').write_text('## Riktning 1: Vinnaren\nEn idé.\n')
    (a_ / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-06T08:00:00Z'}))
    (ae_ / 'prototyp').mkdir()
    (ae_ / 'prototyp' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-06T02:00:00Z'}))
    (ae_ / 'prototyp' / 'vy-390-forsta.png').write_bytes(b'\x89PNG prototypen')
    (at_pt.KUNDER / 'pt-bedomt-aldre' / 'sajt' / 'src').mkdir(parents=True)
    sk.lagg_till_dom('pt-bedomt-aldre', 'ägaren', 'valj', 'En dom i den arkiverade planen.', underlag=pt_und, tid='2026-10-04T11:00:00Z',
                     kandidater=[{'id': 'k01', 'version': 'a' * 64, 'plan': '2026-10-04T10:00:00Z'}], plan='2026-10-04T10:00:00Z')
    sk.lagg_till_dom('pt-bedomt-aldre', 'ägaren', 'ny_riktning', 'Vinnaren bär inte; börja om.', underlag=pt_und)
    info_ = {}
    at_pt.ta_bort_beslut('pt-bedomt-aldre', info_)
    (st_,) = list((ae_ / 'omtag').iterdir())
    k_a = json.loads((st_ / 'atelje' / 'KVITTO.json').read_text())
    assert set(k_a['filer']) == set(filer_ae) | {'VINNARE.json'}, sorted(k_a['filer'])
    for rel_, s_ in k_a['filer'].items():
        assert hashlib_om.sha256((st_ / 'atelje' / rel_).read_bytes()).hexdigest() == s_, rel_
    assert k_a['vinnare']['hashar_stammer'] and k_a['vinnare']['riktning'] == 1, k_a['vinnare']
    assert [d_['beslut'] for d_ in k_a['domar']] == ['valj', 'ny_riktning'], k_a['domar']
    k_p = json.loads((st_ / 'prototyp' / 'KVITTO.json').read_text())
    assert set(k_p['filer']) == {'STATUS.json', 'vy-390-forsta.png'} and k_p['utan_dom'], k_p
    assert not (ae_ / 'atelje').exists() and not (ae_ / 'prototyp').exists(), 'sedan raderas det som förut'
    assert {h_['namn']: h_.get('sparat') for h_ in sk.historik('pt-bedomt-aldre', pt_und)} == {'Vinnaren': 'omtag/%s/atelje/' % st_.name}
    assert sorted(info_['sparade']) == sorted('underlag/pt-bedomt-aldre/omtag/%s/%s/KVITTO.json' % (st_.name, x) for x in ('atelje', 'prototyp'))


@omtagsfall('domloggen läses på samma sätt överallt: en länkad domlogg ger kvitton med domen, och en version utan domrad vägras (KAN-4)')
def _omtag_domlogg():
    dl_ = omtagsplan('pt-bedomt-domlogg', {'k01': 'Ett'}, KLAR_OM)
    kandidat_med_version(dl_ / 'atelje' / 'kandidater' / 'k01', '<h1>Ett</h1>', titel='Ett')
    sk.lagg_till_dom('pt-bedomt-domlogg', 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    f_ = dl_ / sk.DOMLOGG
    (dl_ / 'domar-riktig.jsonl').write_bytes(f_.read_bytes())
    f_.unlink()
    f_.symlink_to(dl_ / 'domar-riktig.jsonl')
    orig_dr = at_pt.domrader
    at_pt.domrader = lambda slug_: []
    try:
        at_pt.ta_bort_beslut('pt-bedomt-domlogg')
        raise AssertionError('en version sparades utan domrad')
    except RuntimeError as e_:
        assert 'ingen rad i domloggen' in str(e_), e_
    finally:
        at_pt.domrader = orig_dr
    assert (dl_ / 'atelje' / 'kandidater' / 'k01' / 'kod').is_dir()
    info_ = {}
    at_pt.ta_bort_beslut('pt-bedomt-domlogg', info_)
    (kv_,) = list((dl_ / 'omtag').glob('*/k01/*/KVITTO.json'))
    assert [d_['beslut'] for d_ in json.loads(kv_.read_text())['domar']] == ['ny_riktning'], kv_.read_text()[:400]


@omtagsfall('en dom utan plan som kom efter planen gäller den: den dömda versionen sparas, inte bara den nuvarande (KAN-5)')
def _omtag_utan_plan():
    up_ = omtagsplan('pt-bedomt-utanplan', {'k01': 'Ett'}, KLAR_OM)
    k_ = up_ / 'atelje' / 'kandidater' / 'k01'
    va_ = kandidat_med_version(k_, '<h1>A</h1>', titel='Ett')
    shutil.copytree(k_ / 'bilder', k_ / 'versioner' / va_[:12] / 'bilder')
    sk.lagg_till_dom('pt-bedomt-utanplan', 'ägaren', 'valj', 'En äldre dom utan plan.', underlag=pt_und, tid='2026-10-05T01:00:00Z',
                     kandidater=[{'id': 'k01', 'version': 'f' * 64}])  # före planen: den gäller en äldre plan
    sk.lagg_till_dom('pt-bedomt-utanplan', 'ägaren', 'valj', 'Välj A.', underlag=pt_und, tid='2026-10-06T06:10:00Z', kandidater=[{'id': 'k01', 'version': va_}])
    vb_ = kandidat_med_version(k_, '<h1>B, förfinad</h1>', status='forfinad')
    sk.lagg_till_dom('pt-bedomt-utanplan', 'ägaren', 'ny_riktning', 'Börja om.', underlag=pt_und)
    info_ = {}
    at_pt.ta_bort_beslut('pt-bedomt-utanplan', info_)
    assert sorted(Path(x).parent.name for x in info_['sparade']) == sorted([va_[:12], vb_[:12]]), info_


assert not OMTAG_FEL, 'omtagets fall 2026-10-07 som föll: %s' % OMTAG_FEL
print('omtaget 2026-10-07: det bedömda sparas, registreras och räknas om')
# dashboarden: före och efter, panelens dom dold tills ägaren dömt körningen, domen till domloggen, godkänt till VINNARE.json
gu_d = (dash.UNDERLAG, dash.ROOT)
dash.UNDERLAG, dash.ROOT = pt_und, tmp
ad_ = pt_u / 'atelje'; (ad_ / 'slutdom' / '2').mkdir(parents=True); (ad_ / 'slutdom' / '1').mkdir()
for d_ in ('1', '2'):
    for n_ in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
        (ad_ / 'slutdom' / d_ / n_).write_bytes(b'x')
(ad_ / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'lage': 'ny', 'startad': '2026-10-05T09:30:00Z', 'klar': '2026-10-05T10:00:00Z', 'faser': {'slutdom': {}}}))
(ad_ / 'VAL.md').write_text('# val'); (ad_ / 'SLUTDOM.md').write_text('# slut'); (ad_ / 'REDOVISNING.md').write_text('# red')
(ad_ / 'VINNARE.json').write_text(json.dumps({'riktning': 1}))
(ad_ / '1').mkdir(exist_ok=True); (ad_ / '1' / 'vy-390-forsta.png').write_bytes(b'x')  # en prövad riktning, den valda
(ad_ / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {'1': [], '2': []}}))
try:
    assert dash.prototyp_slugar() == ['pt-prov']
    d_ = dash.prototyp('pt-prov')
    assert d_['efter']['390-forsta'].endswith('slutdom/2/vy-390-forsta.png') and d_['val_md'] is None and d_['slutdom_md'] is None and not d_['domd'], 'panelens dom döljs tills ägaren dömt'
    assert d_['forfining_md'] is None and [r_['vald'] for r_ in d_['riktningar']] == [True], 'förfiningens logg döljs; vilken riktning som förfinades syns (före är panelens val)'
    assert dash.fil_tillaten('underlag/pt-prov/atelje/slutdom/2/vy-390-forsta.png') and not dash.fil_tillaten('underlag/pt-prov/atelje/VAL.md'), 'bilderna visas, panelens dom inte'
    try:
        dash.spara_prototyp('pt-prov', {'beslut': 'putsa', 'text': ''}); raise AssertionError('putsa utan text vägras')
    except ValueError:
        pass
    (at_pt.KUNDER / 'pt-prov' / 'sajt' / 'src' / 'pages').mkdir(parents=True, exist_ok=True); (at_pt.KUNDER / 'pt-prov' / 'sajt' / 'src' / 'pages' / 'index.astro').write_text('<p>ny</p>')
    (ad_ / 'vinnare' / 'kod').mkdir(parents=True, exist_ok=True); (ad_ / 'vinnare' / 'kod' / 'index.astro').write_text('<p>ny</p>')
    r_ = dash.spara_prototyp('pt-prov', {'beslut': 'godkand', 'text': '', 'niva': 'over'}, minuter=3.5)
    assert r_['dom']['text'] == 'Godkänd.' and r_['dom']['minuter'] == 3.5 and json.loads((ad_ / 'VINNARE.json').read_text())['godkand']['tid'] == r_['dom']['tid']
    d_ = dash.prototyp('pt-prov')
    assert d_['domd'] and d_['val_md'] and d_['slutdom_md'] and d_['redovisning_md'] and d_['godkand'] and d_['domar'][0]['beslut'] == 'godkand' and [r_['vald'] for r_ in d_['riktningar']] == [True], d_
    assert dash.spara_prototyp('pt-prov', {'beslut': 'putsa', 'text': 'Rubriken.'})['ok'] and 'godkand' not in json.loads((ad_ / 'VINNARE.json').read_text()), 'en senare dom drar tillbaka godkännandet'
finally:
    dash.UNDERLAG, dash.ROOT = gu_d
# nästlade sessioner skriver aldrig i ägarens automatiska minne
import nastlad as na_  # noqa: E402
os.environ['CLAUDE_CODE_X_PROV'] = '1'
try:
    m_ = na_.miljo()
    assert m_['CLAUDE_CODE_DISABLE_AUTO_MEMORY'] == '1' and 'CLAUDE_CODE_X_PROV' not in m_ and 'CLAUDECODE' not in m_
    import brev as br_na  # noqa: E402
    import referenstjanster as rt_na  # noqa: E402
    assert all(x['CLAUDE_CODE_DISABLE_AUTO_MEMORY'] == '1' for x in (gr.ren_miljo(), at_pt.ren_miljo(), br_na.ren_miljo(), rt_na.miljo_for('mobbin')))
finally:
    del os.environ['CLAUDE_CODE_X_PROV']
assert 'CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 NWP_SLUG=' in (ROOT / 'kor.sh').read_text(), 'byggets session skriver inte i ägarens minne'
import forhandsvisa as fh_pt  # noqa: E402
(pt_u / 'forhand' / 'start' / 'varv-01').mkdir(parents=True); (pt_u / 'forhand' / 'start' / 'varv-100').mkdir()
assert [p.name for p in fh_pt.varv(pt_u / 'forhand' / 'start')][-1] == 'varv-100' and fh_pt.nasta_varv(pt_u / 'forhand' / 'start').name == 'varv-101'
assert fh_pt.sidnamn('/') == 'start' and fh_pt.sidnamn('/atelje-1/undersida/') == 'atelje-1-undersida' and not fh_pt.hela(pt_u / 'forhand' / 'start' / 'varv-01')
# --- granskningen av skapandeflödet (2026-10-05): rättningarna prövas
# (1) prototypen gissar inte läget när gamla designbeslut finns men domloggen är tom
pt_g = pt_und / 'pt-gammal'; (pt_g / 'prototyp').mkdir(parents=True)
assert pt.lage('pt-gammal')[0] == 'stopp' and 'skapande.py dom' in pt.lage('pt-gammal')[1], pt.lage('pt-gammal')
with contextlib.redirect_stdout(io.StringIO()):
    assert pt.main(['pt-gammal']) == 2, 'inget tyst omtag över gamla beslut'
(pt_g / 'dom.txt').write_text('Ashton-systemet bär inte.')
with contextlib.redirect_stdout(io.StringIO()):
    assert sk.main(['dom', 'pt-gammal', '--kalla', 'ägaren via Codex', '--beslut', 'ny_riktning', '--fil', str(pt_g / 'dom.txt'), '--belagg', 'prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)']) == 2, 'okänt underlag i den riktiga roten vägras'
gu_sk = sk.UNDERLAG; sk.UNDERLAG = pt_und
try:
    with contextlib.redirect_stdout(io.StringIO()):
        assert sk.main(['dom', 'pt-gammal', '--kalla', 'ägaren via Codex', '--beslut', 'ny_riktning', '--fil', str(pt_g / 'dom.txt'), '--belagg', 'prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)']) == 0
    os.environ['NWP_SLUG'] = 'pt-gammal'
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            assert sk.main(['dom', 'pt-gammal', '--kalla', 'ägaren', '--beslut', 'godkand', '--fil', str(pt_g / 'dom.txt')]) == 2, 'aldrig inifrån ett bygge'
    finally:
        del os.environ['NWP_SLUG']
finally:
    sk.UNDERLAG = gu_sk
assert pt.lage('pt-gammal')[0] == 'ny-riktning'
# omtaget från prototyp/ utan ateljévinnare: den tidigare huvudreferensens riktning in i historiken, en gång
(pt_g / 'prototyp' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-05T05:00:00Z'}))
(pt_g / 'REFERENSER.md').write_text('Huvudreferens: Ashton — stenduk och falurött\n')
at_pt.ta_bort_beslut('pt-gammal')
h_g = sk.historik('pt-gammal', pt_und)
assert [x['namn'] for x in h_g] == ['riktningen på huvudreferensen Ashton'] and h_g[0]['drag'] == 'stenduk och falurött' and 'bär inte' in h_g[0]['kritik'], h_g
(pt_g / 'REFERENSER.md').write_text('Huvudreferens: Ashton — stenduk och falurött\n')
at_pt.ta_bort_beslut('pt-gammal')
assert len(sk.historik('pt-gammal', pt_und)) == 1, 'samma dom bokför inte samma riktning två gånger'
# (2) godkännandet: bundet till sidans hash och domloggen, dras tillbaka av en senare dom och en ny förfining
ga_ = pt_und / 'pt-godk'; (ga_ / 'atelje' / 'vinnare' / 'bilder').mkdir(parents=True); (ga_ / 'atelje' / 'vinnare' / 'kod').mkdir()
(ga_ / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'filer': {}}))
(ga_ / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>godkänd</p>')
sajt_g = at_pt.KUNDER / 'pt-godk' / 'sajt'; (sajt_g / 'src' / 'pages').mkdir(parents=True); (sajt_g / 'src' / 'pages' / 'index.astro').write_text('<p>skriven av ett bygge</p>')
# granskning 5, fynd 4: godkännandet binds till vinnarens dömda version, också när ett bygge har skrivit om sajtens
assert at_pt.godkannande('pt-godk', {'tid': 'x', 'kalla': 'ägaren', 'text': 't'})['godkand']['sha_index'] == sk.sha256_fil(ga_ / 'atelje' / 'vinnare' / 'kod' / 'index.astro')
assert at_pt.installera_godkand('pt-godk') == [], 'utan godkännande installeras inget'
dg_ = sk.lagg_till_dom('pt-godk', 'ägaren', 'godkand', 'Godkänd.', underlag=pt_und)
at_pt.godkann('pt-godk', dg_)
gk_ = (pt_und, at_pt.KUNDER)
assert sk.godkand_giltig('pt-godk', *gk_) == (True, 'godkänd %s' % dg_['tid'])
ers_g = at_pt.installera_godkand('pt-godk')
assert len(ers_g) == 1 and ers_g[0].endswith('pt-godk/sajt/src/pages/index.astro'), ers_g
assert (sajt_g / 'src' / 'pages' / 'index.astro').read_text() == '<p>godkänd</p>', 'kor.sh lägger den dömda startsidan i sajten före bygget'
assert [p_.read_text() for p_ in (at_pt.KUNDER / 'pt-godk' / 'startsida-ersatt').glob('*/src/pages/index.astro')] == ['<p>skriven av ett bygge</p>'], 'den ersatta flyttas undan, raderas inte'
assert at_pt.installera_godkand('pt-godk') == [], 'samma fil: inget att lägga'
# granskning 6: bara de godkända filerna installeras, och ingen länk följs (byggkod kan ha lagt den)
(ga_ / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>planterad</p>')
try:
    at_pt.installera_godkand('pt-godk'); raise AssertionError('en vinnarfil som inte är den godkända installeras inte')
except RuntimeError as e_:
    assert 'inte den godkända' in str(e_) or 'fil som inte är godkänd' in str(e_), e_
    assert (sajt_g / 'src' / 'pages' / 'index.astro').read_text() == '<p>godkänd</p>', 'nekad förkontroll ändrade sajten'
(ga_ / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>godkänd</p>')
shutil.move(str(at_pt.KUNDER / 'pt-godk' / 'startsida-ersatt'), str(tmp / 'ersatt-sparad')); (tmp / 'ersatt-utanfor').mkdir()
(at_pt.KUNDER / 'pt-godk' / 'startsida-ersatt').symlink_to(tmp / 'ersatt-utanfor')
(sajt_g / 'src' / 'pages' / 'index.astro').write_text('<p>skriven igen</p>')
assert len(at_pt.installera_godkand('pt-godk')) == 1 and not any((tmp / 'ersatt-utanfor').iterdir()), 'inget flyttades genom länken'
assert not (at_pt.KUNDER / 'pt-godk' / 'startsida-ersatt').is_symlink() and [p_.read_text() for p_ in (at_pt.KUNDER / 'pt-godk' / 'startsida-ersatt').glob('*/src/pages/index.astro')] == ['<p>skriven igen</p>']
shutil.move(str(sajt_g / 'src' / 'pages'), str(tmp / 'pages-borta'))  # granskning 7: en borttagen katalog återskapas
assert len(at_pt.installera_godkand('pt-godk')) == 1 and (sajt_g / 'src' / 'pages' / 'index.astro').read_text() == '<p>godkänd</p>'
(ga_ / 'atelje' / 'vinnare' / 'DESIGN.md').write_text('planterad')  # en DESIGN.md som inte ingår i godkännandet
assert 'inte ingår i godkännandet' in sk.godkand_giltig('pt-godk', *gk_)[1], sk.godkand_giltig('pt-godk', *gk_)
(ga_ / 'atelje' / 'vinnare' / 'DESIGN.md').unlink()
assert sk.godkand_giltig('pt-godk', *gk_)[0]
# omgranskning 3, fynd 1: bygget skriver om sajtens startsida; godkännandet gäller den dömda versionen i vinnaren
(sajt_g / 'src' / 'pages' / 'index.astro').write_text('<p>byggd vidare</p>')
assert sk.godkand_giltig('pt-godk', *gk_)[0], 'ett bygge från godkännandet gör det inte ogiltigt för nästa bygge'
(ga_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'startad': '2026-01-01T00:00:00Z', 'klar': '2026-01-01T01:00:00Z', 'lage': 'ny'}))
assert pt.lage('pt-godk')[0] == 'godkand' and pt.bygget_nekas('pt-godk') is None, (pt.lage('pt-godk'), pt.bygget_nekas('pt-godk'))
(ga_ / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>ändrad i vinnaren</p>')
assert 'ändrad sedan godkännandet' in sk.godkand_giltig('pt-godk', *gk_)[1] and pt.bygget_nekas('pt-godk'), 'den dömda versionen ändrad: inget bygge'
(ga_ / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>godkänd</p>'); (sajt_g / 'src' / 'pages' / 'index.astro').write_text('<p>godkänd</p>')
assert sk.godkand_giltig('pt-godk', *gk_)[0]
# granskning 5, fynd 1: en ny körning efter godkännandet (en förfining som skriver i sajten) gör det ogiltigt
(ga_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'forfina', 'startad': '2999-01-01T00:00:00Z', 'lage': 'putsa'}))
ok_g, skal_g = sk.godkand_giltig('pt-godk', *gk_)
assert not ok_g and 'ny körning' in skal_g, (ok_g, skal_g)
(ga_ / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'startad': '2026-01-01T00:00:00Z', 'klar': '2026-01-01T01:00:00Z', 'lage': 'ny'}))
assert sk.godkand_giltig('pt-godk', *gk_)[0]
sk.lagg_till_dom('pt-godk', 'ägaren', 'putsa', 'Rubriken för stor.', underlag=pt_und, tid='2999-01-01T00:00:00Z')
assert 'är inte godkännandet' in sk.godkand_giltig('pt-godk', *gk_)[1], sk.godkand_giltig('pt-godk', *gk_)
assert at_pt.aterkalla('pt-godk') and 'godkand' not in json.loads((ga_ / 'atelje' / 'VINNARE.json').read_text()) and not at_pt.aterkalla('pt-godk')
# (3) metodkvittot räknar en skill som lästs med Read (lstrip tog punkten i .claude)
sid_m = '00000000-0000-4000-8000-000000000056'
(pt_kat / (sid_m + '.jsonl')).write_text('\n'.join([rad_({'type': 'tool_use', 'id': 'q1', 'name': 'Read', 'input': {'file_path': str(tmp / '.claude/skills/better-layout/SKILL.md')}}), svar_('q1', 'syntetisk hel läsning'),
                                                    rad_({'type': 'tool_use', 'id': 'q2', 'name': 'Write', 'input': {'file_path': str(tmp / 'kunder/pt-prov/sajt/src/pages/index.astro')}})]) + '\n')
bk_pt.ROOT = tmp
try:
    ml2_ = bk_pt.metodlasning(sid_m, [], ['better-layout'], 'kunder/pt-prov/sajt/src/')
    assert ml2_['fore'] == ['.claude/skills/better-layout/SKILL.md'] and not ml2_['saknas'], ml2_
    assert bk_pt.last('.claude/skills/better-layout/SKILL.md', [str(tmp / '.claude/skills/better-layout/SKILL.md')]) and bk_pt.utan_punkt('./a/b') == 'a/b'
finally:
    bk_pt.ROOT = rot_bk
# (4) putsning: förra slutdomen och redovisningen arkiveras; FORFINING.md står kvar
pu_ = pt_und / 'pt-puts' / 'atelje'; (pu_ / 'slutdom' / '2').mkdir(parents=True)
for n_ in ('SLUTDOM.md', 'REDOVISNING.md', 'svar-forfina.json', 'FORFINING.md'):
    (pu_ / n_).write_text('x')
ark_pu = at_pt.arkivera_putsning(pu_)
assert (ark_pu / 'slutdom' / '2').is_dir() and (ark_pu / 'SLUTDOM.md').is_file() and (ark_pu / 'svar-forfina.json').is_file() and (pu_ / 'FORFINING.md').is_file() and not (pu_ / 'slutdom').exists()
# (5) TILLBAKA: den lämnade riktningens startsida, DESIGN.md och design.css flyttas ur sajten
(sajt_g / 'DESIGN.md').write_text('d'); (sajt_g / 'src' / 'styles').mkdir(); (sajt_g / 'src' / 'styles' / 'design.css').write_text('c')
fl_l = at_pt.lamna_sajtfiler('pt-godk', tmp / 'lamnad-g')
assert sorted(fl_l) == ['DESIGN.md', 'design.css', 'index.astro'] and not (sajt_g / 'DESIGN.md').exists() and (tmp / 'lamnad-g' / 'index.astro').read_text() == '<p>godkänd</p>'
# (6) två riktningar på samma referens: den andra är ofullständig; en utan referens likaså
assert at_pt.referensbrister({1: {'namn': 'Ashton'}, 2: {'namn': 'ashton'}, 3: {'namn': 'F'}}, {'1': [], '2': [], '3': [], '4': []}) == {
    '2': 'delar huvudreferens (ashton) med riktning 1', '4': 'ingen huvudreferens med Bildval-bilder (raden "Huvudreferens 4:" i RIKTNINGAR.md mot en rubrik i REFERENSER.md)'}
# (7) ett fel startar aldrig en ny hel körning av sig själv; ägarens senare dom stoppar bygget
fe_ = pt_und / 'pt-fel' / 'atelje'; fe_.mkdir(parents=True)
(fe_ / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'fel': 'slutdomen föll', 'klar': '2026-10-05T10:00:00Z'}))
with contextlib.redirect_stdout(io.StringIO()) as ut_fe:
    assert at_pt.main(['pt-fel']) == 4
assert '--fortsatt' in ut_fe.getvalue()
(fe_ / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-05T10:00:00Z', 'slug': 'pt-fel'}))
sk.lagg_till_dom('pt-fel', 'ägaren', 'ny_riktning', 'Inte den här.', underlag=pt_und, tid='2026-10-05T11:00:00Z')
os.environ['NWP_SLUG'] = 'pt-fel'
try:
    with contextlib.redirect_stdout(io.StringIO()) as ut_fe:
        assert at_pt.main(['pt-fel']) == 6 and 'ska inte byggas vidare' in ut_fe.getvalue()
finally:
    del os.environ['NWP_SLUG']
# (8) skrivrätten och nätet: utforskningen skriver inte ateljékatalogen fritt; npm bara typsnittspaket; inga frågesträngar
vu_ = at_pt.utforska_verktyg('pt-prov')
assert not any(v.endswith('/atelje/**)') for v in vu_) and 'Write(./underlag/pt-prov/atelje/RIKTNINGAR.md)' in vu_ and 'Bash(.venv/bin/python kontroller/typsnitt.py pt-prov *)' in vu_, vu_
# omgranskningen, fynd 8: inget npm, npx eller node direkt; paket bara genom typsnitt.py och byggen bara genom förhandsvisningen
for v_ in (vu_, at_pt.forfina_verktyg('pt-prov')):
    assert not any(x.startswith(('Bash(npm', 'Bash(npx', 'Bash(node')) for x in v_) and 'Bash(.venv/bin/python kontroller/forhandsvisa.py pt-prov *)' in v_, v_
assert {'Bash(npm *)', 'Bash(npx *)', 'Bash(node *)'} <= set(at_pt.NEKAS)
# omgranskning 3, fynd 3: skaparens och domarnas sessioner nekas hemligheterna (sandlådans lista; ägarens egna regler läses inte)
hem_ = os.path.expanduser('~').strip('/')
for r_ in ('Read(//%s/.nortropic-hemligheter/**)' % hem_, 'Read(//%s/.ssh/**)' % hem_, 'Read(//%s/.claude.json)' % hem_, 'Read(//**/.env)', 'Read(//**/*.pem)'):
    assert r_ in at_pt.NEKAS, r_  # //**/: överallt, inte bara under sessionens katalog (granskning 5, fynd 2)
assert not [r_ for r_ in at_pt.NEKAS if r_.startswith('Read(**/')], 'ett mönster utan // gäller bara under sessionens katalog'
import typsnitt as ts_  # noqa: E402
assert ts_.PAKET.fullmatch('@fontsource/inter') and not ts_.PAKET.fullmatch('@fontsource/inter\n'), 'en radbrytning sist släpps inte'
with contextlib.redirect_stderr(io.StringIO()):
    assert ts_.main(['pt-prov', '@fontsource/inter\n']) == 2
import typsnitt as ts_  # noqa: E402
for fel_ in (['pt-prov', '@fontsource/x@npm:ondskefull'], ['pt-prov', '@fontsource/x@git+https://e.se/r'], ['pt-prov', '@fontsource/x@file:../..'],
             ['pt-prov', '@fontsource/inter', 'agare/repo'], ['pt-prov', '@fontsource/inter', '--registry=https://e.se/'], ['pt-prov', 'vänster-pad'], ['pt-prov']):
    with contextlib.redirect_stderr(io.StringIO()):
        assert ts_.main(fel_) == 2, fel_
assert ts_.PAKET.fullmatch('@fontsource-variable/inter') and ts_.PAKET.fullmatch('@fontsource/eb-garamond@5.0.1') and not ts_.PAKET.fullmatch('@fontsource/inter@latest')
(pt_u / 'atelje-fr' / 'KOMPLETTERING.json').write_text(json.dumps({'referens': {'kandidater': [{'namn': 'x', 'adress': 'https://exempel.se/', 'roll': 'ux', 'sidor': ['/?q=hemlig']}]}}))
fq_ = sk.komplettera('pt-prov', pt_u / 'atelje-fr' / 'KOMPLETTERING.json', pt_u / 'atelje-fr', pt_und, kor=lambda a_, t_: (_ for _ in ()).throw(AssertionError('ingen körning')))
assert 'frågesträng' in fq_['fel'], fq_
# ---- omgranskningen av skapandeflödet (Opus, 2026-10-05): vägarna rättelsen lämnade oprövade
# (fynd 2, nytt fel 2 och 5) domar via Codex räknas som ägarens: godkännandet prövas före domen skrivs, och en underkännande
# dom via Codex, också genom kontroller/skapande.py dom, drar tillbaka det; i bygget ger den slutkod 6
om_u = pt_und / 'om-prov'; (om_u / 'atelje').mkdir(parents=True)
om_k = at_pt.KUNDER / 'om-prov' / 'sajt'; (om_k / 'src' / 'pages').mkdir(parents=True)
(om_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'startad': '2026-10-05T06:00:00Z', 'klar': '2026-10-05T07:00:00Z'}))
(om_u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 1}))
(om_u / 'atelje' / 'vinnare' / 'kod').mkdir(parents=True); (om_u / 'atelje' / 'vinnare' / 'kod' / 'index.astro').write_text('<p>s</p>')
try:
    at_pt.doma('om-prov', 'ägaren', 'godkand', 'Godkänd.'); raise AssertionError('utan startsida inget godkännande')
except ValueError:
    pass
assert not sk.domar('om-prov', pt_und), 'en dom som inte kan godkännas skrivs inte (domloggen och VINNARE.json säger samma sak)'
(om_k / 'src' / 'pages' / 'index.astro').write_text('<p>s</p>')
at_pt.doma('om-prov', 'ägaren', 'godkand', 'Godkänd.', tid='2026-10-05T09:00:00Z')
assert sk.godkand_giltig('om-prov', pt_und, at_pt.KUNDER)[0] and pt.lage('om-prov')[0] == 'godkand'
(tmp / 'codex-dom.txt').write_text('Grundidén bär inte; pröva en annan.')
gu_sk = sk.UNDERLAG; sk.UNDERLAG = pt_und
try:
    with contextlib.redirect_stdout(io.StringIO()):
        assert sk.main(['dom', 'om-prov', '--kalla', 'ägaren via Codex', '--beslut', 'ny_riktning', '--fil', str(tmp / 'codex-dom.txt'), '--tid', '2026-10-05T10:00:00Z', '--belagg', 'prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)']) == 0
finally:
    sk.UNDERLAG = gu_sk
assert not sk.godkand_giltig('om-prov', pt_und, at_pt.KUNDER)[0] and 'godkand' not in json.loads((om_u / 'atelje' / 'VINNARE.json').read_text()), 'domen via Codex drar tillbaka godkännandet'
assert pt.lage('om-prov')[0] == 'ny-riktning'
os.environ['NWP_SLUG'] = 'om-prov'
try:
    with contextlib.redirect_stdout(io.StringIO()):
        assert at_pt.main(['om-prov']) == 6, 'i bygget: ägarens senare dom via Codex stoppar'
finally:
    del os.environ['NWP_SLUG']
import importlib.util as ilu_om  # noqa: E402
spec_om = ilu_om.spec_from_file_location('stoppvakt_om', str(ROOT / '.claude' / 'hooks' / 'stoppvakt.py'))
sv_om = ilu_om.module_from_spec(spec_om); spec_om.loader.exec_module(sv_om)
rot_om = tmp / 'rot-om'; shutil.copytree(om_u, rot_om / 'underlag' / 'om-prov')
sl_om = os.environ.pop('NWP_SANDLADA', None)
try:
    assert 'ägaren dömde startsidan efter körningen' in (sv_om.ateljen_forkastad(rot_om, 'om-prov') or ''), 'stoppvakten släpper bygget utan sajt (slutkod 6)'
    sk.lagg_till_dom('om-prov', 'ägaren', 'godkand', 'Godkänd igen.', underlag=rot_om / 'underlag', tid='2026-10-05T11:00:00Z')
    assert sv_om.ateljen_forkastad(rot_om, 'om-prov') is None, 'ett senare godkännande stoppar inte'
finally:
    if sl_om is not None:
        os.environ['NWP_SANDLADA'] = sl_om
# omgranskning 2, fynd 4 och 3, fynd 5: på nödvägen (NWP_ATELJE annat än pa, som i kor.sh) stoppar ateljéns lägen inte bygget
sl_om = os.environ.pop('NWP_SANDLADA', None)
try:
    sk.lagg_till_dom('om-prov', 'ägaren', 'putsa', 'Putsa.', underlag=rot_om / 'underlag', tid='2026-10-05T12:00:00Z')
    for v_ in ('av', 'AV', 'off', '0'):
        os.environ['NWP_ATELJE'] = v_
        assert sv_om.ateljen_forkastad(rot_om, 'om-prov') is None, 'nödvägen ger aldrig en falsk slutkod 6: ' + v_
    del os.environ['NWP_ATELJE']
    assert sv_om.ateljen_forkastad(rot_om, 'om-prov'), 'i skapandeflödets väg stoppar samma läge'
finally:
    os.environ.pop('NWP_ATELJE', None)
    if sl_om is not None:
        os.environ['NWP_SANDLADA'] = sl_om
# fynd 2: ägarens domar prövas mot körningens steg också utanför vyn (kontroller/skapande.py dom går genom doma)
st_om = (om_u / 'atelje' / 'STATUS.json').read_text()
(om_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'fel': 'RuntimeError: förfiningen'}))
try:
    at_pt.doma('om-prov', 'ägaren via Codex', 'godkand', 'Godkänd.', belagg='prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)'); raise AssertionError('en körning som föll kan inte godkännas')
except ValueError as e_:
    assert 'klar körning' in str(e_), e_
(om_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'forfina', 'pid': os.getpid()}))
try:
    at_pt.doma('om-prov', 'ägaren', 'putsa', 'Rubriken.'); raise AssertionError('en pågående körning döms inte')
except ValueError as e_:
    assert 'pågår' in str(e_), e_
(om_u / 'atelje' / 'STATUS.json').write_text(st_om)
assert sk.domar('om-prov', pt_und)[-1]['beslut'] == 'ny_riktning', 'de nekade domarna skrevs inte'
# fynd 3: kor.sh vägrar när ägarens dom inte tillåter ett bygge (prototyp.bygget_nekas), inte när domloggen är tom
assert (pt.bygget_nekas('om-prov') or '').startswith('ny-riktning'), pt.bygget_nekas('om-prov')
(pt_und / 'gd-prov').mkdir(); (pt_und / 'gd-prov' / 'REFERENSER.md').write_text('Huvudreferens: Xref — komposition\n')
assert pt.lage('gd-prov')[0] == 'stopp' and pt.bygget_nekas('gd-prov') is None, 'tidigare designbeslut utan dom stoppar inte ett bygge'
assert pt.bygget_nekas('fs-saknas') is None
kor_txt = (ROOT / 'kor.sh').read_text()
assert 'prototyp.bygget_nekas' in kor_txt and '[ -n "$AGARENS_STOPP" ]' in kor_txt, 'kor.sh frågar samma funktion'
# korslut: en ändrad domlogg under bygget är ändrad mekanik (slutkod 3), inte en varning
import korslut as ks_om  # noqa: E402
k_om = tmp / 'kunder-om' / 'om-prov'; (k_om / 'prov').mkdir(parents=True)
(tmp / 'om-fore').write_text('aaa  underlag/om-prov/DESIGNDOMAR.jsonl\n'); (tmp / 'om-efter').write_text('bbb  underlag/om-prov/DESIGNDOMAR.jsonl\n')
ut_om = io.StringIO()
with contextlib.redirect_stdout(ut_om):
    assert ks_om.main(['korslut', str(k_om), '0', str(tmp / 'om-fore'), str(tmp / 'om-fore')]) != 3, 'oförändrad logg är ingen mekanik'
    assert ks_om.main(['korslut', str(k_om), '0', str(tmp / 'om-fore'), str(tmp / 'om-efter')]) == 3
assert 'domlogg' in ut_om.getvalue(), ut_om.getvalue()[-400:]
# prototypens läge: en dom som inte gäller någon körning i skapandeflödet startar ingen
(pt_und / 'lg-prov').mkdir()
sk.lagg_till_dom('lg-prov', 'ägaren via Codex', 'putsa', 'Putsa vidare.', underlag=pt_und, belagg='prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)')
assert pt.lage('lg-prov')[0] == 'stopp' and 'gäller ingen körning' in pt.lage('lg-prov')[1], pt.lage('lg-prov')
assert (pt.bygget_nekas('lg-prov') or '').startswith('stopp'), 'en dom som inte gäller någon körning stoppar också bygget (omgranskning 2, fynd 3)'
# (fynd 4 och 7) --fortsatt: main skriver statusen med det som bär återupptagningen innan arbetaren startar; utan vinnare
# när utforskningen föll; arbetaren tar vid i omgången som föll, och efter en putsning i slutdomen mot samma före
fs_u = pt_und / 'fs-prov'; (fs_u / 'atelje' / 'omgang-1').mkdir(parents=True)
for n_ in ('BRIEF.md', 'RESEARCH.md', 'TEXTUNDERLAG.md'):
    (fs_u / n_).write_text('x')
(at_pt.KUNDER / 'fs-prov' / 'sajt').mkdir(parents=True); (at_pt.KUNDER / 'fs-prov' / 'sajt' / 'package.json').write_text('{}')
(fs_u / 'referenser' / 'paket-v01' / 'x' / '01-start').mkdir(parents=True); (fs_u / 'referenser' / 'paket-v01' / 'x' / '01-start' / 'vy-1440-ruta-02.png').write_bytes(b'x')
(fs_u / 'REFERENSER.md').write_text('Huvudreferenskandidat: Xref — komposition\n\n## Xref — bransch\n\nBildval: referenser/paket-v01/x/01-start/vy-1440-ruta-02.png — paret — Fråga: bär vårt?\n')
(fs_u / 'atelje' / 'omgang-1' / 'VAL.md').write_text('# Val\nKRITIK UR OMGÅNG ETT')
(fs_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'fel': 'RuntimeError: föll', 'omgang': 2, 'faser': {}, 'lage': 'ny', 'kompletteringar': [{'fas': 'utforska'}]}))
sett_fs = {}


class FalskProc_:
    pid = 4242


def popen_fs(args, **kw):
    sett_fs['status'] = json.loads((fs_u / 'atelje' / 'STATUS.json').read_text()); sett_fs['args'] = args
    return FalskProc_()


sp_fs, vanta_fs = at_pt.subprocess, at_pt.vanta
at_pt.subprocess = types.SimpleNamespace(Popen=popen_fs, DEVNULL=subprocess.DEVNULL, STDOUT=subprocess.STDOUT, run=subprocess.run,
                                         TimeoutExpired=subprocess.TimeoutExpired, CompletedProcess=subprocess.CompletedProcess)
at_pt.vanta = lambda rot, s_: 0
try:
    with contextlib.redirect_stdout(io.StringIO()):
        assert at_pt.main(['fs-prov', '--fortsatt']) == 0, '--fortsatt efter en utforskning som föll kräver ingen vinnare'
finally:
    at_pt.subprocess, at_pt.vanta = sp_fs, vanta_fs
assert sett_fs['status']['omgang'] == 2 and sett_fs['status']['lage'] == 'fortsatt' and sett_fs['status']['kompletteringar'] and sett_fs['args'][-1] == 'fortsatt', sett_fs
assert json.loads((fs_u / 'atelje' / 'STATUS.json').read_text())['pid'] == 4242 and json.loads((fs_u / 'atelje' / 'STATUS.json').read_text())['omgang'] == 2
sedda_fs = []
gamla_fs = (at_pt.utforska_och_valj, at_pt.forfina, at_pt.slutdom, at_pt.redovisa)
at_pt.utforska_och_valj = lambda slug, rot, status, skriv, bilder, kritik=None, forsta=1: (sedda_fs.append(('utforska', forsta, kritik)), (None, forsta))[1]
at_pt.redovisa = lambda slug, rot, status: None
try:
    at_pt.arbetare('fs-prov', 'fortsatt')
    assert sedda_fs == [('utforska', 2, '# Val\nKRITIK UR OMGÅNG ETT')], sedda_fs
    # en putsning som föll i slutdomen: --fortsatt putsar vidare mot samma före, ingen ny utforskning; ett godkännande
    # som stod kvar dras tillbaka när arbetaren startar (granskning 5, fynd 1)
    (fs_u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'riktning': 1, 'godkand': {'tid': '2026-10-05T06:30:00Z', 'av': 'ägaren'}}))
    (fs_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'fel': 'RuntimeError: slutdomen', 'lage': 'putsa', 'omgangar': 1,
                                                            'putsning': 'underlag/fs-prov/atelje/foregaende/x-putsa', 'forfina_start': 123.0,
                                                            'faser': {'valj': {'klar': 't', 'arvd': 'putsning'}, 'forfina': {'klar': 't'}}}))
    sedda_fs.clear()
    at_pt.utforska_och_valj = lambda *a_, **k_: (_ for _ in ()).throw(AssertionError('ingen ny utforskning efter en putsning'))
    at_pt.forfina = lambda *a_, **k_: (_ for _ in ()).throw(AssertionError('förfiningen var klar'))
    at_pt.slutdom = lambda slug, rot, status, skriv: sedda_fs.append(('slutdom', status.get('putsning'), status.get('forfina_start')))
    at_pt.arbetare('fs-prov', 'fortsatt')
    assert sedda_fs == [('slutdom', 'underlag/fs-prov/atelje/foregaende/x-putsa', 123.0)], sedda_fs
    assert json.loads((fs_u / 'atelje' / 'STATUS.json').read_text())['steg'] == 'klar'
    assert 'godkand' not in json.loads((fs_u / 'atelje' / 'VINNARE.json').read_text()), 'en ny körning drar tillbaka godkännandet'
    # omgranskning 2, fynd 5: TILLBAKA i omgång 1, omgång 2 föll: återupptagningen får skaparens skäl, inte panelens val
    (fs_u / 'atelje' / 'omgang-1' / 'TILLBAKA.md').write_text('Grundidén bär inte: fotona är för få.')
    (fs_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'fel': 'RuntimeError: föll', 'omgang': 2, 'faser': {}, 'lage': 'ny'}))
    sedda_fs.clear()
    at_pt.utforska_och_valj = lambda slug, rot, status, skriv, bilder, kritik=None, forsta=1: (sedda_fs.append(('utforska', forsta, kritik)), (None, forsta))[1]
    at_pt.arbetare('fs-prov', 'fortsatt')
    assert sedda_fs == [('utforska', 2, at_pt.TILLBAKA_KRITIK + 'Grundidén bär inte: fotona är för få.')], sedda_fs
finally:
    at_pt.utforska_och_valj, at_pt.forfina, at_pt.slutdom, at_pt.redovisa = gamla_fs
# omgranskning 2, fynd 1: --fortsatt tar inte upp en avslutad körning (den stämplades om som klar förbi ägarens dom)
sp_fs = at_pt.subprocess  # en vägran som gått sönder ska fälla provet, aldrig starta en riktig arbetare
at_pt.subprocess = types.SimpleNamespace(Popen=lambda *a_, **k_: (_ for _ in ()).throw(AssertionError('--fortsatt startade en arbetare')),
                                         DEVNULL=subprocess.DEVNULL, STDOUT=subprocess.STDOUT, run=subprocess.run,
                                         TimeoutExpired=subprocess.TimeoutExpired, CompletedProcess=subprocess.CompletedProcess)
try:
    for steg_ in ('klar', 'tillbaka', 'forkastad'):
        (fs_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': steg_, 'klar': '2026-10-05T07:00:00Z', 'faser': {'valj': {'klar': 't'}}}))
        ut_fs = io.StringIO()
        with contextlib.redirect_stdout(ut_fs):
            assert at_pt.main(['fs-prov', '--fortsatt']) == 2, steg_
        assert 'föll' in ut_fs.getvalue() and json.loads((fs_u / 'atelje' / 'STATUS.json').read_text())['steg'] == steg_, ut_fs.getvalue()
finally:
    at_pt.subprocess = sp_fs
# omgranskning 3, fynd 4: --bara-domare och --fortsatt stämplar aldrig om en körning förbi ägarens senare dom
sp_fs = at_pt.subprocess
at_pt.subprocess = types.SimpleNamespace(Popen=lambda *a_, **k_: (_ for _ in ()).throw(AssertionError('en arbetare startades')),
                                         DEVNULL=subprocess.DEVNULL, STDOUT=subprocess.STDOUT, run=subprocess.run,
                                         TimeoutExpired=subprocess.TimeoutExpired, CompletedProcess=subprocess.CompletedProcess)
try:
    sk.lagg_till_dom('fs-prov', 'ägaren via Codex', 'putsa', 'Luften.', underlag=pt_und, tid='2026-10-05T08:00:00Z', belagg='prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)')
    (fs_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'startad': '2026-10-05T06:00:00Z', 'klar': '2026-10-05T07:00:00Z'}))
    with contextlib.redirect_stdout(io.StringIO()):
        assert at_pt.main(['fs-prov', '--bara-domare']) == 2, '--bara-domare efter ägarens dom'
    (fs_u / 'atelje' / 'STATUS.json').unlink()  # utan statusfil går ägarens dom också före (granskning 5, fynd 5)
    with contextlib.redirect_stdout(io.StringIO()):
        assert at_pt.main(['fs-prov', '--bara-domare']) == 2, '--bara-domare utan statusfil efter ägarens dom'
    (fs_u / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'fel': 'x', 'startad': '2026-10-05T07:30:00Z', 'faser': {}}))
    with contextlib.redirect_stdout(io.StringIO()):
        assert at_pt.main(['fs-prov', '--fortsatt']) == 2, '--fortsatt efter ägarens dom'
    assert json.loads((fs_u / 'atelje' / 'STATUS.json').read_text())['startad'] == '2026-10-05T07:30:00Z' and pt.lage('fs-prov')[0] == 'putsa'
finally:
    at_pt.subprocess = sp_fs
# omgranskning 2, fynd 6: föll förra slutdomen innan efter-bilderna fanns, är före vinnarens senast dömda bilder
sf_ = tmp / 'sf-rot'; (sf_ / 'vinnare' / 'bilder').mkdir(parents=True); (sf_ / 'vinnare' / 'bilder' / 'vy-390-forsta.png').write_bytes(b'v')
pu_ = tmp / 'sf-putsa'; (pu_ / 'slutdom' / '2').mkdir(parents=True)
rot_sf = at_pt.ROOT; at_pt.ROOT = tmp
try:
    assert at_pt.slutdomens_fore(sf_, {'putsning': 'sf-putsa'}, 1) == sf_ / 'vinnare' / 'bilder'
    (pu_ / 'slutdom' / '2' / 'vy-390-forsta.png').write_bytes(b'e')  # bara 390: inspektionen i 1440 dog (omgranskning 3, fynd 2)
    assert at_pt.slutdomens_fore(sf_, {'putsning': 'sf-putsa'}, 1) == sf_ / 'vinnare' / 'bilder', 'halva efter-bilder utan panelens dom är inget före'
    (pu_ / 'slutdom' / 'VAL.json').write_text('{}')
    assert at_pt.slutdomens_fore(sf_, {'putsning': 'sf-putsa'}, 1) == pu_ / 'slutdom' / '2', 'en klar slutdom: dess efter är före'
finally:
    at_pt.ROOT = rot_sf
# omgranskning 2, fynd 7: en post med fältet referens jämförs bara mot det, inte mot lånen i dragtexten
sk.lagg_till_historik('pt-prov', [{'kalla': 'k', 'namn': 'Lånaren', 'drag': 'Lån: sidhuvudet ur Aesop', 'referens': 'Zref', 'utfall': 'förkastad av panelen'}], pt_und)
assert not at_pt.provad_referens('pt-prov', 'Aesop') and at_pt.provad_referens('pt-prov', 'Zref')['namn'] == 'Lånaren'
# (fynd 5) efter TILLBAKA: mallens design.css tillbaka (Bas.astro importerar den), riktningens filer i arkivet, en länk tas bort
lk_ = at_pt.KUNDER / 'lm-prov' / 'sajt'; (lk_ / 'src' / 'styles').mkdir(parents=True); (lk_ / 'src' / 'pages').mkdir(parents=True)
(lk_ / 'src' / 'styles' / 'design.css').write_text('/* riktningens */'); (lk_ / 'src' / 'pages' / 'index.astro').write_text('<p>x</p>')
(tmp / 'utanfor.md').write_text('u'); (lk_ / 'DESIGN.md').symlink_to(tmp / 'utanfor.md')
assert at_pt.lamna_sajtfiler('lm-prov', tmp / 'lm-mal') == ['index.astro', 'design.css']
assert (lk_ / 'src' / 'styles' / 'design.css').read_text() == at_pt.MALL_DESIGN_CSS.read_text() and not (lk_ / 'DESIGN.md').exists() and not (lk_ / 'DESIGN.md').is_symlink()
assert (tmp / 'utanfor.md').read_text() == 'u' and (tmp / 'lm-mal' / 'design.css').read_text() == '/* riktningens */'
assert "import '../styles/design.css'" in (ROOT / 'mall' / 'astro' / 'src' / 'layouts' / 'Bas.astro').read_text(), 'mallen importerar filen som TILLBAKA lägger tillbaka'
# (fynd 8) planterade länkar tas bort, aldrig följda: kod-katalogen och föregående-katalogen
sr_ = tmp / 'sk-rot'; (sr_ / '1').mkdir(parents=True); (tmp / 'sk-utanfor').mkdir(); (sr_ / '1' / 'kod').symlink_to(tmp / 'sk-utanfor')
(lk_ / 'src' / 'pages' / 'atelje-1').mkdir(); (lk_ / 'src' / 'pages' / 'atelje-1' / 'index.astro').write_text('<p>1</p>')
assert at_pt.spara_kod('lm-prov', sr_, 1) == sr_ / '1' / 'kod' and not (sr_ / '1' / 'kod').is_symlink() and (sr_ / '1' / 'kod' / 'index.astro').read_text() == '<p>1</p>'
assert not any((tmp / 'sk-utanfor').iterdir()), 'inget skrevs genom länken'
fg_ = tmp / 'fg-rot'; fg_.mkdir(); (tmp / 'fg-utanfor').mkdir(); (fg_ / 'foregaende').symlink_to(tmp / 'fg-utanfor'); (fg_ / 'SLUTDOM.md').write_text('s')
m_fg = at_pt.arkivera_putsning(fg_)
assert not (fg_ / 'foregaende').is_symlink() and (m_fg / 'SLUTDOM.md').is_file() and not any((tmp / 'fg-utanfor').iterdir())
# (fynd 4) en ny vinnare flyttar den gamla till föregående, raderar den inte
bv_ = tmp / 'bv-rot'; (bv_ / 'vinnare' / 'kod').mkdir(parents=True); (bv_ / 'vinnare' / 'kod' / 'index.astro').write_text('gammal')
(bv_ / 'VINNARE.json').write_text(json.dumps({'riktning': 1})); (bv_ / '2' / 'kod').mkdir(parents=True); (bv_ / '2' / 'kod' / 'index.astro').write_text('ny')
(bv_ / '2' / 'vy-390-forsta.png').write_bytes(b'png')
at_pt.bevara_vinnare('lm-prov', bv_, 2)
assert (bv_ / 'vinnare' / 'kod' / 'index.astro').read_text() == 'ny' and json.loads((bv_ / 'VINNARE.json').read_text())['riktning'] == 2
assert [p_.read_text() for p_ in (bv_ / 'foregaende').glob('*-vinnare/vinnare/kod/index.astro')] == ['gammal'], 'den gamla vinnaren står i föregående'
# (fynd 6) en riktning på en referens som en förkastad, underkänd eller lämnad riktning redan byggt på kräver raden Återanvänd
sk.lagg_till_historik('pt-prov', [{'kalla': 'ateljén omgång 1', 'namn': 'Stenduken', 'drag': 'x', 'referens': 'Xref', 'utfall': 'förkastad av panelen'},
                                  {'kalla': 'k', 'namn': 'Gammal', 'drag': 'bunden till huvudreferensen Ashton Bespoke', 'utfall': 'underkänd av ägaren via Codex'}], pt_und)
egna_rb = {1: {'namn': 'Xref'}, 2: {'namn': 'Yref'}}
rb_ = at_pt.referensbrister(egna_rb, {'1': [], '2': []}, 'pt-prov', {1: ('A', 'Grundidé: x'), 2: ('B', 'y')})
assert set(rb_) == {'1'} and 'Återanvänd' in rb_['1'] and 'Stenduken' in rb_['1'], rb_
skal_rb = 'Återanvänd: den stående panelen i kundens foton bär samma raka komposition; kritiken gällde rubriken, inte referensen'
assert not at_pt.referensbrister(egna_rb, {'1': [], '2': []}, 'pt-prov', {1: ('A', skal_rb), 2: ('B', 'y')})
assert at_pt.provad_referens('pt-prov', 'Ashton Bespoke') and not at_pt.provad_referens('pt-prov', 'Bespo') and not at_pt.provad_referens('pt-prov', 'Yref')
(pt_u / 'REFERENSER.md').write_text('Huvudreferenskandidat: Xref — komposition\n\n## Xref — bransch\n\nBildval: referenser/paket-v01/x/01-start/vy-1440-ruta-02.png — paret — Fråga: bär vårt?\n')
antal_rb = at_pt.ANTAL; at_pt.ANTAL = 1
try:
    assert any('Xref (prövad: Stenduken, förkastad av panelen)' in r_ for r_ in at_pt.referensblock('pt-prov')), at_pt.referensblock('pt-prov')
finally:
    at_pt.ANTAL = antal_rb
# (fynd 8) kompletteringens kanal ut: form och mängd
for beg_, ord_ in (({'referens': {'kandidater': [{'adress': 'https://exempel.se/', 'sidor': ['/a/b/c/d/e/']}]}}, 'sidvägarna'),
                   ({'referens': {'kandidater': [{'adress': 'https://aGVtbGlnLWRhdGE.exempel.se/'}]}}, 'adressen'),
                   ({'referens': {'kandidater': [{'adress': 'https://exempel.se/', 'sidor': ['/' + 'x' * 61 + '/']}]}}, 'sidvägarna'),
                   ({'tjanster': {'fragor': [{'fraga': 'se https://ondskefull.se/x'}]}}, 'fråga'),
                   ({'referens': {'kandidater': [{'adress': 'https://e%d.se/' % i} for i in range(4)]}}, 'kandidater')):
    assert ord_ in (sk.kanal_fel(beg_) or ''), (beg_, sk.kanal_fel(beg_))
assert sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://www.ashtonbespoke.co.uk/', 'sidor': ['/', '/projekt/kok/']}]},
                     'tjanster': {'fragor': [{'fraga': 'hantverkare med mörk palett och stor serif', 'syfte': 'typografin'}]}}) is None
# omgranskning 2, fynd 8: legitima former (procentkodning, versaler, fyra led, punycode) släpps, och beskedet säger hur
assert sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://xn--tryckeri-q2a.se/', 'sidor': ['/tj%C3%A4nster/', '/se/r/Kitchen-Range/', '/a/b/c/d/']}]}}) is None
assert 'procentkodade' in sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://exempel.se/', 'sidor': ['/tjänster/']}]}})
assert 'punycode' in sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://tryckeriet-ö.se/'}]}})
assert sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://exempel.se/', 'sidor': ['/../hemligt/']}]}}), 'ett led av bara punkter släpps inte'
# omgranskning 3, fynd 6: långa punycode-etiketter (upp till 63 tecken) släpps; en radbrytning sist gör det inte
assert sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://xn--mlerifirmanibjrkskatan-o5b53b.se/'}]}}) is None
assert sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://exempel.se/\n'}]}}) and sk.kanal_fel({'referens': {'kandidater': [{'adress': 'https://exempel.se/', 'sidor': ['/a/\n']}]}})
# (fynd 9) förkastningen skriver panelens skäl bara i bygget; utanför dömer ägaren först
vr_ = tmp / 'vanta-rot'; vr_.mkdir(); (vr_ / 'STATUS.json').write_text(json.dumps({'steg': 'forkastad', 'skal': 'x', 'slug': 'v'})); (vr_ / 'VAL.md').write_text('PANELENS SKÄL')
ut_v = io.StringIO()
with contextlib.redirect_stdout(ut_v):
    assert at_pt.vanta(vr_, 1) == 6
assert 'PANELENS SKÄL' not in ut_v.getvalue()
os.environ['NWP_SLUG'] = 'v'
try:
    ut_v = io.StringIO()
    with contextlib.redirect_stdout(ut_v):
        at_pt.vanta(vr_, 1)
finally:
    del os.environ['NWP_SLUG']
assert 'PANELENS SKÄL' in ut_v.getvalue(), 'i bygget skriver byggaren rapporten ur panelens kritik'
at_pt.UNDERLAG, at_pt.KUNDER = gu_at
print('skapandeflödet ok')

# ---------------------------------------------------------------- kandidatflödet (ägarens uppdrag via Codex 2026-10-05: cirka tio genomarbetade prototyper; ägaren väljer)
import kandidater as kd  # noqa: E402
import metod as md_kd  # noqa: E402
import granska as gr_kd  # noqa: E402
import forhandsvisa as fv_kd  # noqa: E402
import stat as stat_kd  # noqa: E402
assert not at_pt.kandidatflode_pa()
del os.environ['NWP_KANDIDATFLODE']
assert at_pt.kandidatflode_pa(), 'kandidatflödet är standard för en ny utforskning'
os.environ['NWP_KANDIDATFLODE'] = 'av'
kd_u, kd_k = tmp / 'kd-underlag', tmp / 'kd-kunder'
spara_at_kd = (at_pt.UNDERLAG, at_pt.KUNDER, at_pt.session, at_pt.ROOT)
spara_kd = {n: getattr(kd, n) for n in ('designkontroll', 'PARALLELLT', 'fotografera', 'leverera_metod', 'forfina_valda', 'LAGE')}
kd.LAGE = 'full'  # det här avsnittet prövar förvalet bakom den tillfälliga växeln; skissläget prövas i nästa avsnitt
spara_bk_kd = bk_pt.ROOT
bk_pt.ROOT = tmp  # metodkvittot räknar raderna i de levererade filerna under provets rot
import uuid as uuid_kd  # noqa: E402
spara_prova_kd = (prova.bygg_inom_grans, prova.kor, prova.Server)
spara_sk_kd = (sk.komplettera, sk.lagg_till_dom)
spara_dash_kd = (dash.UNDERLAG, dash.KUNDER, dash.ROOT)
at_pt.UNDERLAG, at_pt.KUNDER, at_pt.ROOT = kd_u, kd_k, tmp
sl_kd = 'kd-prov'
u_kd, huvud_kd = kd_u / sl_kd, kd_k / sl_kd / 'sajt'
BILDER_KD = ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-768-forsta.png', 'vy-768-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png')
try:
    # --- underlaget, en sajt ur mallen med en planterad länk, och metoden ---
    (u_kd / 'bilder').mkdir(parents=True)
    (u_kd / 'bilder' / 'a.jpg').write_bytes(b'jpg')
    (u_kd / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provfirman Snickeri AB', 'adress': {'ort': 'Luleå', 'postnummer': '123 45'},
                                                       'rackvidd': {'orter': ['Luleå', 'Boden']}, 'orgnr': '556677-8899',
                                                       'kontaktvagar': [{'typ': 'telefon', 'varde': '070-111 22 33'}], 'webb': {'doman': 'provfirman-snickeri.se'}, 'e_post': 'info@provfirman.se', 'kategorier': ['Snickare']}))
    (u_kd / 'BRIEF.md').write_text('# Brief\n\n## §2 Målgrupper och toppuppgifter\n\n1. Se liknande jobb\n')
    # Samma källunderlag före fotograferingen och förfiningen. En senare
    # ändring ska ge en ny version, inte pröva återställning av den gamla.
    for namn_ in ('RESEARCH.md', 'TEXTUNDERLAG.md'):
        (u_kd / namn_).write_text('syntetiskt underlag')
    (u_kd / 'referenser' / 'paket-v01' / 'x').mkdir(parents=True)
    (u_kd / 'referenser' / 'paket-v01' / 'x' / 'vy.png').write_bytes(b'png')
    (u_kd / 'referenser' / 'tjanster').mkdir(); (u_kd / 'referenser' / 'tjanster' / 'TJANSTER.md').write_text('# tjänsterna')
    for f_, t_ in (('package.json', '{}'), ('astro.config.mjs', 'export default {}'), ('src/pages/index.astro', 'mallens start'), ('src/pages/404.astro', '404'),
                   ('src/pages/atelje-1/index.astro', 'ateljé'), ('src/pages/om/index.astro', 'om'), ('src/components/X.astro', 'x'), ('public/favicon.svg', '<svg/>')):
        (huvud_kd / f_).parent.mkdir(parents=True, exist_ok=True)
        (huvud_kd / f_).write_text(t_)
    (huvud_kd / 'node_modules').mkdir()
    (tmp / 'kd-hemlig').mkdir(); (tmp / 'kd-hemlig' / 'nyckel.txt').write_text('HEMLIG')
    (huvud_kd / 'src' / 'components' / 'Logga.astro').symlink_to(tmp / 'kd-hemlig' / 'nyckel.txt')
    (huvud_kd / 'public' / 'lankad').symlink_to(tmp / 'kd-hemlig')
    # projektet per kandidat: mallens sidor och komponenter, kundens bilder, node_modules som länk; ingen länk följs (V10)
    pr_kd = kd.forbered_projekt(sl_kd, 'k01')
    assert sorted(p_.name for p_ in (pr_kd / 'src' / 'pages').iterdir()) == ['404.astro'], 'ingen tidigare startsida, ateljésida eller undersida följer med'
    assert (pr_kd / 'src' / 'components' / 'X.astro').is_file() and (pr_kd / 'src' / 'assets' / 'atelje' / 'a.jpg').is_file() and (pr_kd / 'node_modules').is_symlink()
    assert not (pr_kd / 'src' / 'components' / 'Logga.astro').exists() and not (pr_kd / 'public' / 'lankad').exists(), 'en planterad länk följs aldrig in i kandidatens projekt'
    shutil.rmtree(kd_k / sl_kd / 'kandidater')
    # metoden: kartan håller, utdragen levereras med hash, och en ändrad källa eller en rad som inte finns stoppar leveransen
    fel_md, kallor_md = md_kd.prova()
    assert not fel_md and len(kallor_md) >= 30, fel_md[:3]
    karta_md = md_kd.KARTA.read_text(encoding='utf-8')
    assert md_kd.prova(karta_md, las=dict(kallor_md, **{'frontend-design/SKILL.md': '0' * 64}))[0], 'en ändrad källa stoppar'
    assert any('finns inte' in f_ for f_ in md_kd.prova(karta_md.replace('taste/SKILL.md rad 17–23', 'taste/SKILL.md rad 17–99999'), las=kallor_md)[0])
    (tmp / 'kd-metod').mkdir(); (tmp / 'kd-metod' / 'METOD-skapa-9.md').write_text('en gammal del')
    lev_md = md_kd.leverera('skapa', tmp / 'kd-metod')
    assert list(dict.fromkeys(f_['del'] for f_ in lev_md['filer'])) == ['före', 'varv', 'text', 'uppslag'] and len(lev_md['filer']) > 3, [f_['fil'].name for f_ in lev_md['filer']]
    # kalibreringen är uppslag, aldrig före-läsning (ägarens uppdrag 2026-10-06, punkt 3; granskningen av designintegrationen)
    kal_md = 'Ägaren dömde 2026-10-04 tretton externa sajter blint'  # kalibreringens innehåll, inte en hänvisning till filen
    assert not any(kal_md in f_['fil'].read_text() for f_ in lev_md['filer'] if f_['del'] == 'före')
    assert any(kal_md in f_['fil'].read_text() for f_ in lev_md['filer'] if f_['del'] == 'uppslag')
    assert not (tmp / 'kd-metod' / 'METOD-skapa-9.md').exists(), 'en ny leverans lämnar inga gamla delar'
    for s_ in md_kd.STEG:  # varje levererad fil ryms i ett Read utan offset och limit (granskning 2, N5)
        for f_ in md_kd.leverera(s_, tmp / 'kd-metod-alla')['filer']:
            t_ = f_['fil'].read_text()
            assert len(t_) <= md_kd.MAX_TECKEN and t_.count('\n') < md_kd.MAX_RADER and max(map(len, t_.split('\n'))) < 2000, (f_['fil'].name, len(t_))
    fore_md = ''.join(f_['fil'].read_text() for f_ in lev_md['filer'] if f_['del'] == 'före')
    assert '## Avgöranden' in lev_md['filer'][0]['fil'].read_text() and '### frontend-design/SKILL.md' in fore_md
    assert all('## %s\n' % r_ in karta_md for r_ in list(md_kd.STEG.values()) + ['Avgöranden']) and all(r_ in karta_md for r_ in ('**Fråga:**', '**Underlag:**', '**Till nästa steg:**', '**Visar:**'))
    skapande_metod_ = sk.metodrader('forfina')  # den äldre vägen läser samma karta
    # rollernas kärna (better-layout i responsiv implementation, better-writing i innehåll och UX); humanizer är ett
    # alternativ sedan rollerna fick kärna och alternativ (Codex via ägaren 2026-10-05, punkt 7)
    assert any('.claude/skills/better-layout/SKILL.md' in r_ for r_ in skapande_metod_) and any('better-writing' in r_ for r_ in skapande_metod_)

    # --- bygget och webbläsaren ersatta; den riktiga fotograferingen körs (granskningen: proven ersatte fotografera) ---
    class SrvKd:
        url = 'http://127.0.0.1:9'
        def __init__(self, dist): self.dist = dist
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def bygg_kd(sajt, timeout=900):
        pages, dist = Path(sajt) / 'src' / 'pages', Path(sajt) / 'dist'
        if 'TRASIG' in (pages / 'index.astro').read_text():
            return 1, 'bygget föll'
        for p_ in pages.rglob('index.astro'):
            m_ = dist / p_.relative_to(pages).parent / 'index.html'; m_.parent.mkdir(parents=True, exist_ok=True); m_.write_text(p_.read_text())
        return 0, 'byggt'

    def kor_kd(cmd, cwd=None, timeout=900):
        cmd = [str(x) for x in cmd]
        if any(x.endswith('inspektera.mjs') for x in cmd):
            ut_ = Path(cmd[cmd.index('--ut') + 1]); ut_.mkdir(parents=True, exist_ok=True)
            for n_ in BILDER_KD:
                (ut_ / n_).write_bytes(b'png')
            (ut_ / 'vy-390-aria.txt').write_text('länk "Ring"')
            (ut_ / 'INSPEKTION.json').write_text(json.dumps({'vyer': {'390': {'konsol': [], 'spill': {'spill': False}}}, 'tid': nu_kd()}))
            return 0, ''
        if any(x.endswith('axe.mjs') for x in cmd):
            ut_ = Path(next(x for x in cmd if x.startswith('--ut='))[5:]); ut_.mkdir(parents=True, exist_ok=True)
            allv_ = '/k02/' in str(ut_) and 'förbättrad' not in (kd.ksajt(sl_kd, 'k02') / 'src' / 'pages' / 'index.astro').read_text()
            (ut_ / 'axe.json').write_text(json.dumps({'allvarliga': 1 if allv_ else 0, 'totalt': 2, 'axeVersion': 'x',
                                                      'rader': [{'overtradelser': [{'id': 'color-contrast', 'impact': 'serious' if allv_ else 'minor', 'help': 'kontrast'}]}]}))
            return 0, ''
        return spara_prova_kd[1](cmd, cwd=cwd, timeout=timeout)
    nu_kd = at_pt.nu
    prova.bygg_inom_grans, prova.kor, prova.Server = bygg_kd, kor_kd, SrvKd
    kd.designkontroll = lambda slug, kid: {'ok': True, 'fel': []}
    kd.PARALLELLT = 2
    sess_kd = []
    tom_k03 = [True]  # k03:s första försök saknar undersidan: ett andra försök ges med bristerna
    olast_kd = set()  # kandidater vars granskning inte läser de första vyerna

    def transkript_kd(steg):
        """Ett transkript i Claude Codes radformat: (verktyg, indata, fel) per anrop, med svaret efter."""
        sid_ = str(uuid_kd.uuid4())
        rader_ = []
        for i_, (namn_, in_, fel_) in enumerate(steg):
            rader_.append(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'u%d' % i_, 'name': namn_, 'input': in_}]}}))
            rader_.append(json.dumps({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'u%d' % i_, 'content': 'fel' if fel_ else 'ok', 'is_error': fel_}]}}))
        (bk_pt.PROJEKT / 'kd').mkdir(parents=True, exist_ok=True)
        (bk_pt.PROJEKT / 'kd' / (sid_ + '.jsonl')).write_text('\n'.join(rader_) + '\n')
        return sid_

    def varv_kd(kid, n):
        v_ = kd.kdir(sl_kd, kid) / 'varv' / 'start'
        start_ = max(kd.varvnummer(sl_kd, kid) or [0])
        for i_ in range(start_ + 1, start_ + 1 + n):
            (v_ / ('varv-%02d' % i_)).mkdir(parents=True, exist_ok=True)
            for n_ in fv_kd.LAS:
                (v_ / ('varv-%02d' % i_) / n_).write_bytes(b'png')

    def sess_kd_(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), **kw):
        sess_kd.append({'prompt': prompt, 'verktyg': verktyg, 'ut': Path(ut).name, 'schema': schema, 'modell': modell, 'nekas': list(nekas)})
        so = None
        if schema is kd.FORSKA_SCHEMA:
            so = {'varfor': 'bredd före planen', 'riktningar': 'tio skilda grunder',
                  'antaganden': [{'antagande': 'besökaren bedömer tidigare jobb före kontakt', 'underlag': 'ännu inte observerat', 'provning': 'uppgift: hitta ett jobb som liknar ditt', 'om_fel': 'kontakten först'}],
                  'sajter': [{'namn': 'ny', 'adress': 'https://exempel.se/', 'roll': 'hantverk', 'varfor': 'x', 'sidor': ['/']},
                             {'namn': 'trasig', 'adress': 'http://inte-https.se', 'roll': 'ux', 'varfor': 'x', 'sidor': ['/']}],
                  'fragor': [{'tjanst': 'refero', 'fraga': 'warm editorial craft builder', 'syfte': 'stilen', 'typ': 'stil'}] * 4
                  + [{'tjanst': 'mobbin', 'fraga': 'Provfirman Snickeri carpentry homepage', 'syfte': 'x', 'typ': 'skarm'}]}
        elif schema is kd.PLAN_SCHEMA:
            so = {'variation': 'tre grunder', 'kandidater': [dict({f_: '%s %d' % (f_, i_) for f_, _r in kd.PLANFALT}, referensbilder=['underlag/kd-prov/referenser/paket-v01/x/vy.png'])
                                                            for i_ in range(3)]}
        elif schema is kd.KRITIK_A_SCHEMA:
            kid_ = re.search(r'kandidater/(k\d\d)/bilder', prompt).group(1)
            forb_ = 'förbättrad' in (kd.ksajt(sl_kd, kid_) / 'src' / 'pages' / 'index.astro').read_text()
            bilder_ = re.findall(r'^- (\S+\.png)$', prompt, re.M)
            sid_kd = transkript_kd([('Read', {'file_path': b_}, False) for b_ in bilder_ if kid_ not in olast_kd or '-hela' in b_])
            so = {'forsta_intryck': {'framgar': 'f', 'genomarbetat': 'g', 'skaver': 's'}, 'uppgift': {'uppgift': 'se jobb', 'kan_genomforas': 'ja', 'belagg': 'b'},
                  'styrkor': [], 'niva': 'nastan', 'material': 'm',
                  'avvikelser': [{'var': 'topp', 'vad': 'kontrasten', 'atgard': 'mörkare', 'allvar': 'hog', 'slag': 'krav' if kid_ == 'k02' and not forb_ else 'smak'},
                                 {'var': 'mitt', 'vad': 'stor rubrik', 'atgard': 'mindre', 'allvar': 'hog', 'slag': 'krav' if kid_ == 'k01' else 'smak'}]}
        elif schema is kd.KRITIK_B_SCHEMA:
            so = {'helhet': 'h', 'referens': {'kvaliteten_bar': 'delvis', 'skal': 's'},
                  'motiveringar': [{'nr': 1, 'avsiktlig': False, 'valgrundad': False, 'skal': ''}, {'nr': 2, 'avsiktlig': True, 'valgrundad': True, 'skal': 'idén'}]}
        elif schema is kd.JAMFOR_SCHEMA:
            so = {'sammanfattning': 's', 'par': [{'a': 'k01', 'b': 'k03', 'grad': 'nara', 'skal': 'samma ordning'}, {'a': 'k01', 'b': 'k99', 'grad': 'nara', 'skal': 'x'}]}
        elif schema is kd.PASS_SCHEMA:  # kompetenspassen efter fördjupningen (prövas i skisslägets avsnitt)
            so = {'andringar': [], 'ingen_andring': 'provet ändrar inget', 'passade_inte': [], 'kvarstar': []}
        else:  # en skapare (skapa, förbättra eller förfina)
            kid_ = re.search(r'kunder/kd-prov/kandidater/(k\d\d)/sajt', prompt).group(1)
            pages_ = kd.ksajt(sl_kd, kid_) / 'src' / 'pages'
            if 'valde' in prompt and 'INGET-VARV' in (kd.kdir(sl_kd, kid_) / 'RIKTNING.md').read_text():
                svar_ = {'is_error': True}
                Path(ut).write_text(json.dumps(svar_)); raise RuntimeError('sessionen föll direkt')
            (pages_ / 'index.astro').write_text('start %s%s' % (kid_, ' förbättrad' if 'Förbättringsrundan' in prompt else ' förfinad' if 'valde' in prompt else ''))
            if not (kid_ == 'k03' and tom_k03[0]):
                (pages_ / 'projekt' / 'a').mkdir(parents=True, exist_ok=True); (pages_ / 'projekt' / 'a' / 'index.astro').write_text('undersida')
            elif 'Förra sessionen slutade' not in prompt:
                tom_k03[0] = False
            if 'valde' in prompt:
                (kd.ksajt(sl_kd, kid_) / 'DESIGN.md').write_text('# DESIGN.md förfinad\n')
            r_ = kd.kdir(sl_kd, kid_) / 'RIKTNING.md'
            if not r_.exists() or 'Förbättringsrundan' not in prompt:
                r_.write_text('Huvudreferens: Xref — kompositionen\n\n## Material\n\nFler foton av köket.\n\n## Varv 1\n\nrubriken (better-typography)\n')
            varv_kd(kid_, 3)
            fore_ = re.search(r'\): läs (.+?) före första ändringen', prompt).group(1).split(', ')
            las_ = [('Read', {'file_path': f_}, False) for f_ in fore_]
            if kid_ == 'k03':  # ett Read som gav fel och ett som bara läste början räknas inte som lästa (N5)
                las_ = [las_[0], ('Read', {'file_path': fore_[1]}, True), ('Read', {'file_path': fore_[2], 'limit': 20}, False)]
            sid_kd = transkript_kd(las_ + [('Write', {'file_path': kd.rel(pages_ / 'index.astro')}, False)])
        svar_ = {'structured_output': so, 'num_turns': 5, 'duration_ms': 120000, 'total_cost_usd': 1.25, 'session_id': sid_kd if schema is kd.KRITIK_A_SCHEMA or schema is None else 's'}
        Path(ut).write_text(json.dumps(svar_))
        return svar_
    at_pt.session = sess_kd_

    def kompl_kd(slug, fil, rot, underlag=None, frist=3600, kor=None, bred=False, forbjudna=None):
        beg_ = json.loads(Path(fil).read_text())
        assert bred and len(beg_['tjanster']['fragor']) == 4 and [s_['namn'] for s_ in beg_['referens']['kandidater']] == ['ny'], beg_
        Path(fil).unlink()
        (u_kd / 'referenser' / 'paket-v02').mkdir()
        (u_kd / 'referenser' / 'paket-v02' / 'PAKET.json').write_text(json.dumps({'kandidater': [{'namn': 'ny'}, {'namn': 'x', 'arv': 'paket-v01'}]}))
        return {'tid': 't', 'referens': {'rc': 0}, 'tjanster': {'rc': 0}}
    sk.komplettera = kompl_kd

    # --- hela utforskningen ---
    st_kd = {'startad': '2026-10-05T10:00:00Z', 'lage': 'ny', 'modell': 'm', 'effort': 'max'}
    klara_kd = kd.kor(sl_kd, st_kd, lambda: None, n=3)
    # den enda prototypen före uppskalningen (ägarens uppdrag 2026-10-05 18:53Z, punkt 7): planeraren får ett uppdrag
    pp1_kd = kd.plan_prompt(sl_kd, 1)
    assert 'EN genomarbetad' in pp1_kd and 'verkligt olika sätt' not in pp1_kd and 'valdes framför de andra' in pp1_kd, pp1_kd[:400]
    assert 'EN skiss' in kd.plan_prompt(sl_kd, 1, skiss=True) and 'omkring tio uppdrag' in pp1_kd, 'läget och uppskalningen i prompten (A5)'
    assert 'verkligt olika sätt' in kd.plan_prompt(sl_kd, 3) and [kd.minsta_plan(n_) for n_ in (1, 2, 3, 10)] == [1, 2, 2, 5]
    assert 'EN skiss' in kd.forska_prompt(sl_kd, 1, skiss=True) and 'cirka 1 ' not in kd.forska_prompt(sl_kd, 1, skiss=True)
    # planen för den enda prototypen: schemat tar emot och kräver exakt ett uppdrag, och planen skrivs med det (A2)
    sch_kd = []

    def plan_ett_(prompt, verktyg, ut, schema=None, *a, **kw):
        sch_kd.append(schema)
        return {'structured_output': {'variation': 'v', 'kandidater': [dict({f_: '%s 1' % f_ for f_, _r in kd.PLANFALT}, huvudreferens='egen — provets riktning', referensbilder=[])]}}
    spara_sess_kd = at_pt.session
    shutil.copytree(u_kd, kd_u / 'kd-en', ignore=shutil.ignore_patterns('atelje'))  # kundens underlag, utan körningen
    at_pt.session = plan_ett_
    try:
        kd.planera('kd-en', 1, 'skiss')
    finally:
        at_pt.session = spara_sess_kd
    # F06 (motorinventeringen): ett uppdrag vars huvudreferens inte är "egen" och vars referensbilder inte finns är en falsk
    # referensuppgift: avvisat i planen med skälet, och körningen stannar när inget användbart uppdrag återstår
    def plan_brist_(prompt, verktyg, ut, schema=None, *a, **kw):
        return {'structured_output': {'variation': 'v', 'kandidater': [dict({f_: '%s 1' % f_ for f_, _r in kd.PLANFALT}, huvudreferens='Xref',
                                                                            referensbilder=['underlag/kd-tva/referenser/finns-inte.png'])]}}
    shutil.copytree(u_kd, kd_u / 'kd-tva', ignore=shutil.ignore_patterns('atelje'))
    at_pt.session = plan_brist_
    try:
        try:
            kd.planera('kd-tva', 1, 'skiss')
            raise AssertionError('en plan utan referensunderlag gick igenom')
        except RuntimeError as e_:
            assert 'saknar underlag' in str(e_) and 'finns-inte.png' in str(e_) and 'Xref' in str(e_), e_
    finally:
        at_pt.session = spara_sess_kd
    assert kd.referensbrist('kd-en', {'huvudreferens': 'egen — provets', 'referensbilder': []}) is None
    assert kd.referensbrist(sl_kd, {'huvudreferens': 'Xref', 'referensbilder': ['underlag/%s/referenser/paket-v01/x/vy.png' % sl_kd]}) is None
    assert kd.referensbrist(sl_kd, {'huvudreferens': 'Xref', 'referensbilder': ['underlag/%s/VERKSAMHET.json' % sl_kd]}), 'en fil utanför referenser/ är inget referensunderlag'
    assert 'inga referensbilder angivna' in kd.referensbrist(sl_kd, {'huvudreferens': 'Xref', 'referensbilder': []})
    kd.rot('kd-tva').mkdir(parents=True, exist_ok=True)
    (kd.rot('kd-tva') / 'FORSKNING.json').write_text(json.dumps({'referens': {'rc': 1, 'utdrag': 'brist'}, 'tjanster': {'rc': 0}}))
    pp_br = kd.plan_prompt('kd-tva', 1, skiss=True)
    assert 'leverans har brister' in pp_br and 'referenssteget slutkod 1' in pp_br and 'referenstjänsterna' not in pp_br.split('leverans har brister')[1][:60], pp_br[-900:]
    assert 'leverans har brister' not in kd.plan_prompt('kd-en', 1, skiss=True) and 'avvisas av flödet när' in kd.plan_prompt('kd-en', 1, skiss=True)
    assert sch_kd[0]['properties']['kandidater']['minItems'] == 1 and sch_kd[0]['properties']['kandidater']['maxItems'] == 1, sch_kd[0]['properties']['kandidater']
    assert kd.PLAN_SCHEMA['properties']['kandidater']['minItems'] == 2 and kd.lista('kd-en') == ['k01'], kd.lista('kd-en')
    skapare_kd = [s_['prompt'] for s_ in sess_kd if s_['schema'] is None and 'Förbättringsrundan' not in s_['prompt']]
    assert skapare_kd and all('rubriken "%s"' % kd.OVERFORT in p_ for p_ in skapare_kd), 'skaparen redovisar det överförda och avvikelserna'
    plan_kd = json.loads((kd.rot(sl_kd) / 'KANDIDATPLAN.json').read_text())  # planens tid före provets domar (fröet för etiketterna)
    (kd.rot(sl_kd) / 'KANDIDATPLAN.json').write_text(json.dumps(dict(plan_kd, tid='2026-10-05T10:30:00Z')))
    assert set(st_kd['metod']) == {'forska', 'plan', 'skapa', 'skiss', 'granska', 'forfina'} and (kd.metodkatalog(sl_kd) / 'METOD-skapa-varv.md').is_file(), st_kd.get('metod')
    assert json.loads((kd.rot(sl_kd) / 'KANDIDATPLAN.json').read_text())['lage'] == 'full' and st_kd['kandidatlage'] == 'full', 'planen bär körningens läge'
    fo_ = json.loads((kd.rot(sl_kd) / 'FORSKNING.json').read_text())
    assert fo_['nytt']['paket'] == 'paket-v02' and fo_['nytt']['sajter'] == ['ny'] and len(fo_['antaganden']) == 1, fo_
    assert any('nämner kundens' in x_ for x_ in fo_['slappta']) and any('inte-https' in x_ and 'adressen' in x_ for x_ in fo_['slappta']), fo_['slappta']
    fm_ = (kd.rot(sl_kd) / 'FORSKNING.md').read_text()
    assert 'besökaren bedömer tidigare jobb' in fm_ and 'Släppta' in fm_ and 'Nytt i den här körningen' in fm_
    plan_prompt_kd = next(s_['prompt'] for s_ in sess_kd if s_['schema'] is kd.PLAN_SCHEMA)
    assert 'FORSKNING.md' in plan_prompt_kd and 'METOD-plan.md' in plan_prompt_kd and 'hypotes' in plan_prompt_kd
    up2_ = (kd.kdir(sl_kd, 'k02') / 'UPPDRAG.md').read_text()
    assert all(r_ in up2_ for _f, r_ in kd.PLANFALT if r_), 'varje fält ur planen står i uppdraget'
    assert klara_kd == ['k01', 'k02', 'k03'] and st_kd['steg'] == 'klar_for_bedomning' and st_kd['kandidatflode'] and st_kd.get('andra_forsok') == ['k03'], st_kd
    st3_ = kd.las_status(sl_kd, 'k03')
    assert st3_['forsok'] == 2 and st3_['status'] == 'klar', 'en ofullständig kandidat får ett andra försök med bristerna (V6)'
    sk_v_ = [s_ for s_ in sess_kd if s_['schema'] is None]
    # ägarens ord 2026-10-05 18:15Z: skillverktyget i sessionerna; MCP:erna står aldrig i tillåtelselistan, kundvakten
    # öppnar varje rent anrop (granskning 4, G3)
    plan_s_ = next(s_ for s_ in sess_kd if s_['schema'] is kd.PLAN_SCHEMA)
    assert 'Skill' in plan_s_['verktyg'] and not any(str(v_).startswith('mcp__') for s_ in sess_kd for v_ in s_['verktyg']), plan_s_['verktyg']
    assert any('Förra sessionen slutade' in s_['prompt'] and 'undersidan' in s_['prompt'] for s_ in sk_v_ if 'kandidater/k03/sajt' in s_['prompt'])
    k01_ = next(s_ for s_ in sk_v_ if 'kandidater/k01/sajt' in s_['prompt'])
    assert 'Read(./kunder/kd-prov/kandidater/k02/**)' in k01_['nekas'] and 'Read(./underlag/kd-prov/atelje/kandidater/k03/**)' in k01_['nekas'], 'skaparna ser inte varandras kod (M2)'
    assert 'METOD-skapa.md' in k01_['prompt'] and 'METOD-skapa-2.md' in k01_['prompt'] and 'METOD-skapa-text.md' in k01_['prompt'] and 'Visar' in k01_['prompt']
    las1_, las3_ = kd.las_status(sl_kd, 'k01')['lasning'], kd.las_status(sl_kd, 'k03')['lasning']
    assert las1_['verifierad'] and las1_['metod_fore_forsta_skrivning'] and las1_['metod_last'] and not las1_['metod_delvis'], las1_
    assert las3_['verifierad'] and not las3_['metod_fore_forsta_skrivning'] and not las3_['metod_last'] and [Path(x_).name for x_ in las3_['metod_delvis']] == ['METOD-skapa-3.md'] \
        and [Path(x_).name for x_ in las3_['metod_saknas']] == ['METOD-skapa-2.md', 'METOD-skapa-3.md'], las3_
    # granskningen i två pass: det första är blint för uppdraget och anteckningarna, det andra läser dem
    ka_ = [s_ for s_ in sess_kd if s_['schema'] is kd.KRITIK_A_SCHEMA]
    assert ka_ and all(any(n_.endswith('/RIKTNING.md)') for n_ in s_['nekas']) and any(n_.endswith('/UPPDRAG.md)') for n_ in s_['nekas']) for s_ in ka_)
    assert all('RIKTNING.md' not in s_['prompt'] for s_ in ka_) and all(s_['modell'] == kd.GRANSKARE_MODELL for s_ in ka_) and 'BRIEF.md' in ka_[0]['prompt']
    assert all('RIKTNING.md' in s_['prompt'] for s_ in sess_kd if s_['schema'] is kd.KRITIK_B_SCHEMA)
    ka2_ = [s_ for s_ in ka_ if 'kandidater/k02/bilder' in s_['prompt']][-1]  # granskningen efter förbättringsrundan
    for n_ in ('STATUS.json', 'svar-skapa-1.json', 'svar-forbattra.json', 'KRITIK-fore.json', 'svar-kritik-b-1.json', 'versioner/**'):
        assert any(x_.endswith('/kandidater/k02/%s)' % n_) for x_ in ka2_['nekas']), 'första passet ser inte %s (N9)' % n_
    assert all(any(x_.endswith('/atelje/%s)' % n_) for x_ in ka2_['nekas']) for n_ in ('KANDIDATPLAN.json', 'KANDIDATPLAN.md', 'FORSKNING.json', 'svar-plan.json'))
    assert not any('/k02/bilder' in x_ or '/atelje/metod' in x_ for x_ in ka2_['nekas']), 'bilderna och metoden får läsas'
    assert json.loads((kd.kdir(sl_kd, 'k02') / 'KRITIK.json').read_text())['last'] is True and json.loads((kd.kdir(sl_kd, 'k02') / 'KRITIK-fore.json').read_text())['last'] is True
    kr2_ = json.loads((kd.kdir(sl_kd, 'k02') / 'KRITIK.json').read_text())
    assert kr2_['andra_passet'] and kr2_['avvikelser'][1]['avsiktlig'] and kr2_['avvikelser'][1]['valgrundad'] and kr2_['uppgift']['kan_genomforas'] == 'ja'
    # förbättringsrundan: bara objektiva fel (krav, och axe), aldrig smak; föreversionen bevaras med bilderna
    st2_ = kd.las_status(sl_kd, 'k02')
    assert (kd.ksajt(sl_kd, 'k02') / 'src' / 'pages' / 'index.astro').read_text() == 'start k02 förbättrad' and st2_['forbattrad']['fore'] != st2_['version'], st2_
    assert (kd.kdir(sl_kd, 'k02') / 'versioner' / st2_['forbattrad']['fore'][:12] / 'bilder' / 'start' / 'vy-390-forsta.png').is_file(), 'föreversionen bevaras med bilderna'
    assert any('kontrasten' in a_ for a_ in st2_['forbattrad']['atgarder']) and not any('stor rubrik' in a_ for a_ in st2_['forbattrad']['atgarder']), 'smak och välgrundade val rättas inte'
    assert (kd.kdir(sl_kd, 'k02') / 'KRITIK-fore.json').is_file() and json.loads((kd.kdir(sl_kd, 'k02') / 'KRITIK.json').read_text())['version'] == st2_['version']
    fp_ = next(s_['prompt'] for s_ in sess_kd if 'Förbättringsrundan' in s_['prompt'])
    assert 'KOMPLETTERING' not in fp_ and 'kontrasten' in fp_, 'förbättringsrundan lovar ingen research (M3) och listar felen'
    assert any('axe' in a_ and 'color-contrast' in a_ for a_ in st2_['forbattrad']['atgarder']) and kd.las_status(sl_kd, 'k01')['axe']['allvarliga'] == 0
    assert kd.las_status(sl_kd, 'k02')['axe']['allvarliga'] == 0, 'den förbättrade versionen prövas igen'
    assert kd.las_status(sl_kd, 'k01')['tillampning'] == {'varv': 1, 'med_metod': 1}
    assert [(p_['a'], p_['b']) for p_ in json.loads((kd.rot(sl_kd) / 'JAMFORELSE.json').read_text())['par']] == [('k01', 'k03')], 'bara par av riktiga kandidater'
    # versionen är koden och DESIGN.md: en ny fotografering av samma kod ger samma version (V4)
    v1_ = kd.las_status(sl_kd, 'k01')['version']
    assert kd.fotografera(sl_kd, 'k01')['version'] == v1_ and kd.aterstall_och_fotografera(sl_kd, 'k01', v1_)['version'] == v1_
    # ett avbrott i förbättringsrundan: föreversionen återställs, och kandidaten skapas inte om (V1)
    n_kd = len(sess_kd)
    (kd.ksajt(sl_kd, 'k01') / 'src' / 'pages' / 'index.astro').write_text('halvgjord förbättring')
    kd.satt_status(sl_kd, 'k01', 'under_arbete', 'förbättringsrunda', forbattras={'fore': v1_, 'tid': 'x'})
    st1_ = kd.behandla(sl_kd, 'k01')
    assert st1_['status'] == 'klar' and st1_['version'] == v1_ and 'forbattras' not in st1_ and st1_['forbattrad']['avbruten'], st1_
    assert (kd.ksajt(sl_kd, 'k01') / 'src' / 'pages' / 'index.astro').read_text() == 'start k01' and not [s_ for s_ in sess_kd[n_kd:] if s_['schema'] is None], 'ingen ny skaparsession'
    # en förbättring som blir ofullständig: föreversionen står kvar
    v3_ = kd.las_status(sl_kd, 'k03')['version']
    (kd.kdir(sl_kd, 'k03') / 'KRITIK.json').write_text(json.dumps({'avvikelser': [{'allvar': 'hog', 'slag': 'krav', 'var': 'v', 'vad': 'v', 'atgard': 'a'}], 'version': v3_, 'last': True}))
    at_pt.session = lambda prompt, verktyg, ut, **kw: (kd.ksajt(sl_kd, 'k03') / 'src' / 'pages' / 'index.astro').write_text('TRASIG') and {}
    st3b_ = kd.forbattra(sl_kd, 'k03')
    assert st3b_['status'] == 'klar' and 'föreversionen är återställd' in st3b_['skal'] and st3b_['version'] == v3_, st3b_
    # förbättringsrundan faller med ett undantag efter sessionen (N10): föreversionen återställs, och ingen halvgjord blir klar
    kd.satt_status(sl_kd, 'k03', 'klar', 'x', ta_bort=('forbattrad',))
    at_pt.session = lambda prompt, verktyg, ut, **kw: (kd.ksajt(sl_kd, 'k03') / 'src' / 'pages' / 'index.astro').write_text('HALV förbättring') and {}
    kd.fotografera = lambda slug, kid: (_ for _ in ()).throw(RuntimeError('den lokala servern startade inte')) \
        if 'HALV' in (kd.ksajt(slug, kid) / 'src' / 'pages' / 'index.astro').read_text() else spara_kd['fotografera'](slug, kid)
    try:
        st3c_ = kd.behandla(sl_kd, 'k03')
    finally:
        kd.fotografera = spara_kd['fotografera']
    assert st3c_['status'] == 'klar' and st3c_['version'] == v3_ and 'forbattras' not in st3c_ and 'föreversionen är återställd' in st3c_['skal'], st3c_
    assert 'HALV' not in (kd.ksajt(sl_kd, 'k03') / 'src' / 'pages' / 'index.astro').read_text()
    # en granskning som inte läst de första vyerna, eller vars läsning inte kan prövas, styr ingen förbättringsrunda (N5)
    krav_kd = {'avvikelser': [{'allvar': 'hog', 'slag': 'krav', 'var': 'v', 'vad': 'kontrasten', 'atgard': 'a'}]}
    assert kd.objektiva(sl_kd, 'k03', dict(krav_kd, last=True)) and not kd.objektiva(sl_kd, 'k03', dict(krav_kd, last=None)) and not kd.objektiva(sl_kd, 'k03', dict(krav_kd, last=False))
    at_pt.session = sess_kd_
    olast_kd.add('k01')
    kr1_ = kd.granska_kandidat(sl_kd, 'k01')
    olast_kd.discard('k01')
    assert kr1_['last'] is False and kd.objektiva(sl_kd, 'k01') == [], kr1_.get('lasning')
    # en återupptagen körning gör inget klart om
    n_kd = len(sess_kd)
    kd.kor(sl_kd, dict(st_kd), lambda: None, n=3)
    assert [s_['schema'] for s_ in sess_kd[n_kd:]] == [kd.JAMFOR_SCHEMA], 'bara jämförelsen körs om'
    # etiketterna och blindheten
    et_kd = kd.etiketter(sl_kd, kd.lista(sl_kd))
    assert sorted(et_kd.values()) == ['Förslag A', 'Förslag B', 'Förslag C'] and et_kd == kd.etiketter(sl_kd, kd.lista(sl_kd))
    blind_kd = kd.sammanstall(sl_kd)
    assert not any('titel' in k_ or 'kritik' in k_ or 'forbattring' in k_ for k_ in blind_kd) and all(k_['hypotes'] for k_ in blind_kd), 'blint först; hypotesen följer med hopfälld'
    rd_ = kd.redovisa(sl_kd, st_kd).read_text()
    for krav_ in ('Tre bedömningar', 'Tillgänglighetens täckning', 'VoiceOver', 'läsningen och tillämpningen', 'Fler foton av köket', 'listpris',
                  '| %s (k03) | nej (bara delar: METOD-skapa-3.md) |' % et_kd['k03'], '| %s (k01) | ja |' % et_kd['k01'], 'nastan (bilderna olästa)'):
        assert krav_ in rd_, krav_

    # --- ägarens beslut: binds till kandidat och version, prövas innan något skrivs ---
    (kd.rot(sl_kd) / 'STATUS.json').write_text(json.dumps({'kandidatflode': True, 'steg': 'klar_for_bedomning', 'startad': '2026-10-05T10:00:00Z', 'klar': '2026-10-05T11:00:00Z', 'lage': 'ny'}))
    vs_kd = {k_: kd.las_status(sl_kd, k_)['version'] for k_ in kd.lista(sl_kd)}
    for kand_, ord_ in (([{'id': 'k01', 'version': 'fel'}], 'ändrats'), ([{'id': 'k09', 'version': 'x'}], 'okänd'), ([], 'minst en'),
                        ([{'id': 'k01', 'version': vs_kd['k01']}, {'id': 'k01', 'version': vs_kd['k01']}], 'okänd')):
        try:
            at_pt.doma(sl_kd, 'ägaren', 'valj', 'x', kandidater=kand_)
            raise AssertionError('vägras: %s' % kand_)
        except ValueError as e_:
            assert ord_ in str(e_), e_
    for b_, kand_, ord_ in (('jamfor', [{'id': 'k01', 'version': vs_kd['k01']}], 'minst två'), ('godkand', [{'id': 'k01', 'version': vs_kd['k01']}], 'förfinad')):
        try:
            at_pt.doma(sl_kd, 'ägaren', b_, 'x', kandidater=kand_)
            raise AssertionError('vägras: %s' % b_)
        except ValueError as e_:
            assert ord_ in str(e_), e_
    assert len(sk.domar(sl_kd, kd_u)) == 0, 'ett vägrat beslut skrivs inte'
    at_pt.doma(sl_kd, 'ägaren', 'jamfor', '(ägaren skrev ingen text)', kandidater=[{'id': 'k01', 'version': vs_kd['k01']}, {'id': 'k03', 'version': vs_kd['k03']}], tid='2026-10-05T12:00:00Z')
    assert pt.lage(sl_kd)[0] == 'vanta' and kd.las_status(sl_kd, 'k01')['status'] == 'klar' and pt.bygget_nekas(sl_kd), 'jämförelsen ändrar ingen status (V5)'
    # valet av föreversionen före en förbättringsrunda (ägaren kan föredra den)
    fore2_ = kd.las_status(sl_kd, 'k02')['forbattrad']['fore']
    dom_v = at_pt.doma(sl_kd, 'ägaren', 'valj', 'Den här vill jag gå vidare med.', kandidater=[{'id': 'k02', 'version': fore2_}], tid='2026-10-05T12:09:00Z')
    assert kd.las_status(sl_kd, 'k02')['status'] == 'vald' and pt.lage(sl_kd)[0] == 'vanta' and 'nästa steg är ett uppdrag' in pt.lage(sl_kd)[1], 'ett val startade arbete (2026-10-09)'
    # den riktade förbättringen är ett uppdrag (ägarens uppdrag 2026-10-09, punkt 8): här Bygg ut, utan specialistpass
    dom_kd = at_pt.doma(sl_kd, 'ägaren', 'uppdrag', 'Bygg vidare på den.', kandidater=[{'id': 'k02', 'version': fore2_}], delar={'k03': 'tidslinjen', 'x': 'bort'},
                        tid='2026-10-05T12:10:00Z', uppdrag={'typ': 'bygg_ut', 'resultat': 'hela startsidan och projektsidan', 'omfattning': ['startsidans sektioner'],
                                                            'bevara': ['första vyn'], 'specialister': {}})
    assert dom_kd['kandidater'][0]['version'] == fore2_ and dom_kd['delar'] == {'k03': 'tidslinjen'} and dom_kd['delar_titlar'] == {'k03': 'titel 2'} and dom_kd['plan'] == '2026-10-05T10:30:00Z', dom_kd
    assert kd.las_status(sl_kd, 'k02')['status'] == 'vald' and pt.lage(sl_kd)[0] == 'valda' and pt.bygget_nekas(sl_kd).startswith('valda')
    assert pt.valda_text(sl_kd).startswith('Starta uppdraget: Bygg ut'), pt.valda_text(sl_kd)
    kr_kd = '\n'.join(sk.kritikrader(sl_kd, underlag=kd_u))
    assert 'kandidaterna i planen 2026-10-05T10:30:00Z: %s (k02 "titel 1"' % et_kd['k02'] in kr_kd and 'ägaren gillade i k03 "titel 2" i planen' in kr_kd, kr_kd
    sam2_ = next(k_ for k_ in kd.sammanstall(sl_kd) if k_['id'] == 'k02')
    assert all('titel' in k_ for k_ in kd.sammanstall(sl_kd)) and kd.domd(sl_kd) and sam2_['forbattring']['fore'] == fore2_ and sam2_['forbattring']['bilder']['390-forsta'], 'efter första beslutet: före och efter förbättringen'

    # --- en förfining som faller innan metoden levererats (granskning 2, N1): körningen förblir kandidatflödets ---
    (kd.rot(sl_kd) / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'startad': '2026-10-05T10:00:00Z', 'klar': '2026-10-05T11:00:00Z', 'lage': 'ny'}))
    for f_ in ('BRIEF.md', 'RESEARCH.md', 'TEXTUNDERLAG.md'):
        (u_kd / f_).write_text('x') if not (u_kd / f_).exists() else None
    # förfiningen sätter flaggan och de valda innan metoden levereras
    st_n1_ = {}
    kd.leverera_metod = lambda slug: (_ for _ in ()).throw(md_kd.MetodFel('en källa har ändrats sedan låset skrevs'))
    try:
        kd.forfina_valda(sl_kd, st_n1_, lambda: None)
        raise AssertionError('MetodFel stoppar förfiningen')
    except md_kd.MetodFel:
        pass
    finally:
        kd.leverera_metod = spara_kd['leverera_metod']
    assert st_n1_.get('kandidatflode') and st_n1_.get('valda') == ['k02'] and st_n1_.get('dom') == '2026-10-05T12:10:00Z', st_n1_
    # arbetaren känner igen kandidatflödet på ateljén också när statusen saknar flaggan
    (kd.rot(sl_kd) / 'STATUS.json').write_text(json.dumps({'steg': 'fel', 'startad': '2026-10-05T12:15:00Z', 'lage': 'valda'}))
    kd.forfina_valda = lambda slug, status, skriv: (_ for _ in ()).throw(RuntimeError('faller direkt'))
    try:
        at_pt.arbetare(sl_kd, 'valda')
    finally:
        kd.forfina_valda = spara_kd['forfina_valda']
    assert json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())['kandidatflode'] and (kd.rot(sl_kd) / 'REDOVISNING.md').read_text().startswith('# Redovisning · %s' % sl_kd)
    (kd.rot(sl_kd) / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'startad': '2026-10-05T10:00:00Z', 'klar': '2026-10-05T11:00:00Z', 'lage': 'ny'}))
    startat_ = []
    spara_popen_kd, spara_vanta_kd, spara_uov_kd = at_pt.subprocess.Popen, at_pt.vanta, at_pt.utforska_och_valj
    def popen_kd_(args, **kw):
        if '--arbetare' in args and any(str(a_).endswith('/atelje.py') for a_ in args):
            startat_.append(args)
            return type('P', (), {'pid': 999999998})()
        return spara_popen_kd(args, **kw)
    at_pt.subprocess.Popen = popen_kd_
    at_pt.vanta = lambda rot, sek: 0
    at_pt.utforska_och_valj = lambda *a, **k: (_ for _ in ()).throw(AssertionError('den äldre utforskningen startades'))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            assert at_pt.main([sl_kd, '--valda']) == 0 and startat_[-1][-1] == 'valda'
        assert json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())['kandidatflode'], 'kandidatflödet känns igen på ateljén, inte bara på flaggan'
        kd.leverera_metod = lambda slug: (_ for _ in ()).throw(md_kd.MetodFel('en källa har ändrats sedan låset skrevs'))
        at_pt.arbetare(sl_kd, 'valda')
        kd.leverera_metod = spara_kd['leverera_metod']
        stn_ = json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())
        assert stn_['steg'] == 'fel' and stn_['kandidatflode'] and stn_['valda'] == ['k02'] and stn_['dom'] == '2026-10-05T12:10:00Z' and 'MetodFel' in stn_['fel'], stn_
        assert (kd.rot(sl_kd) / 'REDOVISNING.md').read_text().startswith('# Redovisning · %s' % sl_kd) and not (kd.rot(sl_kd) / '1').exists(), 'kandidatflödets redovisning'
        assert pt.lage(sl_kd)[0] == 'vanta' and '--fortsatt' in pt.lage(sl_kd)[1]
        with contextlib.redirect_stdout(io.StringIO()):
            assert at_pt.main([sl_kd, '--fortsatt']) == 0 and startat_[-1][-1] == 'fortsatt'
        stn_ = json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())
        assert stn_['kandidatflode'] and stn_['valda'] == ['k02'] and stn_['forra_lage'] == 'valda', stn_
        # förfiningen faller efter sessionen (N10): den valda versionen återställs med bilderna
        kd.fotografera = lambda slug, kid, **kw: (_ for _ in ()).throw(RuntimeError('den lokala servern startade inte')) \
            if 'förfinad' in (kd.ksajt(slug, kid) / 'src' / 'pages' / 'index.astro').read_text() else spara_kd['fotografera'](slug, kid, **kw)
        n_kd = len(sess_kd)
        at_pt.arbetare(sl_kd, 'fortsatt')
    finally:
        at_pt.subprocess.Popen, at_pt.vanta, at_pt.utforska_och_valj = spara_popen_kd, spara_vanta_kd, spara_uov_kd
        kd.leverera_metod, kd.fotografera = spara_kd['leverera_metod'], spara_kd['fotografera']
    stn_ = json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())
    assert stn_['steg'] == 'klar_for_bedomning' and stn_['fas'] == 'forfining' and [s_['ut'][:13] for s_ in sess_kd[n_kd:]] == ['svar-uppdrag-'], (stn_, sess_kd[n_kd:], kd.las_status(sl_kd, 'k02'))
    st2n_ = kd.las_status(sl_kd, 'k02')
    assert 'den lokala servern startade inte' in st2n_['skal'], st2n_['skal']
    assert st2n_['status'] == 'vald' and 'återställd' in st2n_['skal'] and st2n_['version'] == fore2_ and 'forfining_pagar' not in st2n_, st2n_
    assert 'förfinad' not in (kd.ksajt(sl_kd, 'k02') / 'src' / 'pages' / 'index.astro').read_text() and (kd.kdir(sl_kd, 'k02') / 'bilder' / 'start' / 'vy-390-forsta.png').is_file()

    # --- återupptagningen av en förfining (B1): --fortsatt bär de valda till arbetaren, och arbetaren förfinar ---
    (kd.rot(sl_kd) / 'STATUS.json').write_text(json.dumps({'kandidatflode': True, 'steg': 'forfina', 'startad': '2026-10-05T12:20:00Z', 'lage': 'valda',
                                                          'valda': ['k02'], 'dom': '2026-10-05T12:10:00Z', 'pid': 999999999}))
    assert at_pt.avbruten(json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text()))
    assert pt.lage(sl_kd)[0] == 'stopp' and '--fortsatt' in pt.lage(sl_kd)[1], 'en död arbetare är ett avbrott, aldrig en ny körning (V2)'
    try:
        at_pt.doma(sl_kd, 'ägaren via Codex', 'valj', 'Hellre C.', kandidater=[{'id': 'k03', 'version': kd.las_status(sl_kd, 'k03')['version']}], belagg='prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)')
        raise AssertionError('ingen dom under ett avbrott (N2)')
    except ValueError as e_:
        assert 'avbröts' in str(e_) and '--fortsatt' in str(e_), e_
    for f_ in ('BRIEF.md', 'RESEARCH.md', 'TEXTUNDERLAG.md'):
        (u_kd / f_).write_text('x') if not (u_kd / f_).exists() else None
    with contextlib.redirect_stdout(io.StringIO()):
        assert at_pt.main([sl_kd]) == 4, 'utan flagga startas ingen ny körning över ett avbrott'
    startat_ = []
    spara_popen_kd, spara_vanta_kd = at_pt.subprocess.Popen, at_pt.vanta
    at_pt.subprocess.Popen = popen_kd_
    at_pt.vanta = lambda rot, sek: 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            assert at_pt.main([sl_kd, '--fortsatt']) == 0
    finally:
        at_pt.subprocess.Popen, at_pt.vanta = spara_popen_kd, spara_vanta_kd
    stf_ = json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())
    assert stf_['lage'] == 'fortsatt' and stf_['valda'] == ['k02'] and stf_['forra_lage'] == 'valda' and startat_[0][-1] == 'fortsatt', stf_
    kd.satt_status(sl_kd, 'k02', 'under_arbete', 'förfining', forfining_pagar={'dom': '2026-10-05T12:10:00Z', 'fran': fore2_, 'start_varv': 0})
    (kd.ksajt(sl_kd, 'k02') / 'src' / 'pages' / 'index.astro').write_text('halvgjord förfining')
    n_kd = len(sess_kd)
    at_pt.arbetare(sl_kd, 'fortsatt')
    st2_ = kd.las_status(sl_kd, 'k02')
    fp_kd = [s_ for s_ in sess_kd[n_kd:] if s_['ut'].startswith('svar-uppdrag-')]
    assert len(fp_kd) == 1 and st2_['status'] == 'forfinad' and st2_['forfining']['fran'] == fore2_ and not [s_ for s_ in sess_kd[n_kd:] if s_['ut'].startswith('svar-skapa')], st2_
    assert json.loads((kd.rot(sl_kd) / 'STATUS.json').read_text())['steg'] == 'klar_for_bedomning', 'arbetaren förfinade de valda i stället för att skapa om (B1)'
    for krav_ in (et_kd['k02'], 'tidslinjen', 'kandidater/k03/kod', 'design.py kd-prov --kandidat k02 --skriv', 'Bygg vidare på den.', 'METOD-forfina.md', '--mellan', 'Visar'):
        assert krav_ in fp_kd[0]['prompt'], krav_
    assert 'Read(./underlag/kd-prov/atelje/kandidater/k03/**)' not in fp_kd[0]['nekas'] and 'Read(./underlag/kd-prov/atelje/kandidater/k01/**)' in fp_kd[0]['nekas'], 'förfiningen får läsa den ägaren gillade delar ur'
    assert 'Write(./kunder/kd-prov/kandidater/k02/sajt/DESIGN.md)' in fp_kd[0]['verktyg'] and (kd.kdir(sl_kd, 'k02') / 'DESIGN.md').is_file()
    dk_ = spara_kd['designkontroll'](sl_kd, 'k02')
    assert not dk_['ok'] and dk_['fel'], 'den riktiga designkontrollen vägrar en DESIGN.md utan värden'
    assert not any('KOMPLETTERING' in v_ for v_ in fp_kd[0]['verktyg']), 'förfiningen begär ingen research (N6)'
    # en förfining som inte gör något eget varv blir aldrig "förfinad" (V7)
    (kd.kdir(sl_kd, 'k01') / 'RIKTNING.md').write_text((kd.kdir(sl_kd, 'k01') / 'RIKTNING.md').read_text() + '\nINGET-VARV\n')
    kd.satt_status(sl_kd, 'k01', 'vald', 'vald')
    st1f_ = kd.forfina_kandidat(sl_kd, 'k01', kd.las_status(sl_kd, 'k01')['version'], {'tid': '2026-10-05T12:30:00Z', 'kandidater': [], 'uppdrag': {
        'typ': 'ratta', 'resultat': 'r', 'omfattning': ['o'], 'bevara': ['b'], 'specialister': {}}})
    assert st1f_['status'] == 'vald' and 'inget eget förhandsvarv' in st1f_['skal'], st1f_

    # --- godkännandet: prövas helt innan något gällande ändras (B2) ---
    (kd.rot(sl_kd) / 'STATUS.json').write_text(json.dumps({'kandidatflode': True, 'steg': 'klar_for_bedomning', 'fas': 'forfining', 'startad': '2026-10-05T12:20:00Z', 'klar': '2026-10-05T12:50:00Z', 'lage': 'valda'}))
    v2_ = kd.las_status(sl_kd, 'k02')['version']
    kd.satt_status(sl_kd, 'k02', 'forfinad', 'x', design_fel=['DESIGN.md saknas'])
    try:
        at_pt.doma(sl_kd, 'ägaren', 'godkand', 'Godkänd.', kandidater=[{'id': 'k02', 'version': v2_}])
        raise AssertionError('DESIGN.md med brister godkänns inte')
    except ValueError as e_:
        assert 'DESIGN.md har brister' in str(e_), e_
    kd.satt_status(sl_kd, 'k02', 'forfinad', 'x', design_fel=[])
    at_pt.doma(sl_kd, 'ägaren', 'godkand', 'Godkänd för helbygge.', kandidater=[{'id': 'k02', 'version': v2_}], tid='2026-10-05T13:00:00Z')
    vin_kd = json.loads((kd.rot(sl_kd) / 'VINNARE.json').read_text())
    assert vin_kd['kandidat'] == 'k02' and vin_kd['riktning'] == 2 and vin_kd['godkand']['sha_kod'] and 'kod/projekt/a/index.astro' in vin_kd['filer'] \
        and 'bilder/vy-390-forsta.png' in vin_kd['filer'] and 'undersidor/projekt-a/vy-390-forsta.png' in vin_kd['filer'], vin_kd
    assert not gr_kd.vinnarfel(kd.rot(sl_kd), vin_kd) and kd.las_status(sl_kd, 'k02')['status'] == 'godkand' and not list(kd.rot(sl_kd).glob('.vinnare-ny-*'))
    assert sk.godkand_giltig(sl_kd, kd_u, kd_k)[0] and pt.lage(sl_kd)[0] == 'godkand' and pt.bygget_nekas(sl_kd) is None
    # ett godkännande som vägras under ett bygge (låst domlogg): vinnaren och VINNARE.json är orörda
    fore_vin_ = (kd.rot(sl_kd) / 'VINNARE.json').read_text()
    (kd_k / '.bygge-pid').write_text(str(os.getpid()))
    os.chflags(kd_u / sl_kd / sk.DOMLOGG, stat_kd.UF_IMMUTABLE)
    try:
        at_pt.doma(sl_kd, 'ägaren', 'godkand', 'Godkänd.', kandidater=[{'id': 'k02', 'version': v2_}])
        raise AssertionError('ett låst domlogg vägrar')
    except ValueError as e_:
        assert 'låst' in str(e_), e_
    finally:
        os.chflags(kd_u / sl_kd / sk.DOMLOGG, 0)
        (kd_k / '.bygge-pid').unlink()
    assert (kd.rot(sl_kd) / 'VINNARE.json').read_text() == fore_vin_ and not list(kd.rot(sl_kd).glob('.vinnare-ny-*')) and not list((kd.rot(sl_kd) / 'foregaende').glob('*-vinnare')), 'inget ändrat'
    # och när domen inte går att skriva av något annat skäl: tempkatalogen tas bort, inget gällande ändras
    sk.lagg_till_dom = lambda *a, **k: (_ for _ in ()).throw(ValueError('domen skrevs inte'))
    try:
        at_pt.doma(sl_kd, 'ägaren', 'godkand', 'Godkänd.', kandidater=[{'id': 'k02', 'version': v2_}])
        raise AssertionError('vägras')
    except ValueError:
        pass
    finally:
        sk.lagg_till_dom = spara_sk_kd[1]
    assert (kd.rot(sl_kd) / 'VINNARE.json').read_text() == fore_vin_ and not list(kd.rot(sl_kd).glob('.vinnare-ny-*'))
    # installationen: alla sidor, och de ersatta behåller sin väg (M9)
    ers_kd = at_pt.installera_godkand(sl_kd)
    assert (huvud_kd / 'src' / 'pages' / 'index.astro').read_text() == 'start k02 förfinad' and (huvud_kd / 'src' / 'pages' / 'projekt' / 'a' / 'index.astro').read_text() == 'undersida'
    assert (huvud_kd / 'DESIGN.md').is_file() and list((kd_k / sl_kd / 'startsida-ersatt').glob('*/src/pages/index.astro')), ers_kd
    assert {str(Path(n_).relative_to(huvud_kd.relative_to(tmp))) for n_ in ers_kd} == {
        'src/pages/index.astro', 'src/pages/projekt/a/index.astro', 'DESIGN.md', 'public/favicon.svg'}, ers_kd
    assert (huvud_kd / 'src/assets/atelje/a.jpg').read_bytes() == b'jpg', 'redan identiskt kundmaterial bevaras'
    assert at_pt.installera_godkand(sl_kd) == [], 'en andra installation ändrar inget'
    (kd.rot(sl_kd) / 'vinnare' / 'kod' / 'projekt' / 'a' / 'index.astro').write_text('ändrad efter godkännandet')
    assert not sk.godkand_giltig(sl_kd, kd_u, kd_k)[0] and 'godkända sidor' in sk.godkand_giltig(sl_kd, kd_u, kd_k)[1]
    try:
        at_pt.installera_godkand(sl_kd)
        raise AssertionError('en ändrad undersida installeras inte')
    except RuntimeError:
        pass
    (kd.rot(sl_kd) / 'vinnare' / 'kod' / 'projekt' / 'a' / 'index.astro').write_text('undersida')
    # ett nytt godkännande gör den förra godkända förfinad igen (V5)
    kd.satt_status(sl_kd, 'k03', 'forfinad', 'x', design_fel=[])
    at_pt.doma(sl_kd, 'ägaren', 'godkand', 'Hellre den.', kandidater=[{'id': 'k03', 'version': kd.las_status(sl_kd, 'k03')['version']}], tid='2026-10-05T13:30:00Z')
    assert kd.las_status(sl_kd, 'k02')['status'] == 'forfinad' and kd.las_status(sl_kd, 'k03')['status'] == 'godkand'
    assert list((kd.rot(sl_kd) / 'foregaende').glob('*-vinnare')), 'den förra vinnaren arkiveras'
    at_pt.doma(sl_kd, 'ägaren', 'jamfor', 'Jämför dem igen.', kandidater=[{'id': k_, 'version': kd.las_status(sl_kd, k_)['version']} for k_ in ('k02', 'k03')],
               tid='2026-10-05T13:40:00Z')
    assert kd.las_status(sl_kd, 'k03')['status'] == 'forfinad' and not sk.godkand_giltig(sl_kd, kd_u, kd_k)[0], 'en jämförelse efter godkännandet drar tillbaka det (N11)'

    # --- en dom via Codex med ägarens etiketter, förkastningen och omtaget ---
    (u_kd / 'dom.txt').write_text('Förkasta alla, men tidslinjen i C var bra.')
    gu_sk_kd = sk.UNDERLAG; sk.UNDERLAG = kd_u
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            assert sk.main(['dom', sl_kd, '--kalla', 'ägaren via Codex', '--beslut', 'jamfor', '--fil', str(u_kd / 'dom.txt'), '--kandidater', 'Förslag Q', '--belagg', 'prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)']) == 2
        with contextlib.redirect_stdout(io.StringIO()):
            assert sk.main(['dom', sl_kd, '--kalla', 'ägaren via Codex', '--beslut', 'forkasta', '--fil', str(u_kd / 'dom.txt'), '--tid', '2026-10-05T14:00:00Z', '--belagg', 'prov: ägarens egna ord, ordagrant förmedlade (syntetiskt)']) == 0
    finally:
        sk.UNDERLAG = gu_sk_kd
    assert pt.lage(sl_kd)[0] == 'stopp' and 'ny riktning' in pt.lage(sl_kd)[1] and not sk.godkand_giltig(sl_kd, kd_u, kd_k)[0], 'förkastningen drar tillbaka godkännandet'
    assert {kd.las_status(sl_kd, k_)['status'] for k_ in ('k01', 'k02', 'k03')} == {'forkastad'}, 'alla synliga förkastas (M4)'

    # --- dashboarden: blint först, bilderna tillåtna, körningens filer aldrig före första beslutet (M1) ---
    dash.UNDERLAG, dash.KUNDER, dash.ROOT = kd_u, kd_k, tmp
    try:
        bild_kd = 'underlag/kd-prov/atelje/kandidater/k01/bilder/start/vy-390-forsta.png'
        assert dash.fil_tillaten(bild_kd) and not dash.fil_tillaten('underlag/kd-prov/atelje/kandidater/k01/KRITIK.json')
        assert dash.fil_tillaten('underlag/kd-prov/atelje/REDOVISNING.md'), 'efter första beslutet följer redovisningen'
        plan_nu_ = json.loads((kd.rot(sl_kd) / 'KANDIDATPLAN.json').read_text())
        (kd.rot(sl_kd) / 'KANDIDATPLAN.json').write_text(json.dumps(dict(plan_nu_, tid='2026-10-05T23:00:00Z')))  # en ny plan efter domarna
        assert not kd.domd(sl_kd) and not dash.fil_tillaten('underlag/kd-prov/atelje/REDOVISNING.md') and not dash.fil_tillaten('underlag/kd-prov/atelje/KANDIDATPLAN.json')
        assert dash.fil_tillaten(bild_kd)
        vy_kd = dash.prototyp(sl_kd)
        assert vy_kd['kandidatflode'] and vy_kd['antal'] == 3 and not vy_kd['domd'] and vy_kd['redovisning_md'] is None and vy_kd['avbruten'] is False
        try:
            dash.spara_forbattring(sl_kd, {'kid': 'k02', 'val': 'fore'})
            raise AssertionError('före och efter visas först efter första beslutet')
        except ValueError:
            pass
        (kd.rot(sl_kd) / 'KANDIDATPLAN.json').write_text(json.dumps(plan_nu_))
        assert dash.spara_forbattring(sl_kd, {'kid': 'k02', 'val': 'fore'})['antal'] == 1 and json.loads((kd.rot(sl_kd) / 'FORBATTRING-AGAREN.json').read_text())[0]['val'] == 'fore'
        try:
            dash.spara_prototyp(sl_kd, {'beslut': 'ny_riktning', 'text': ''})
            raise AssertionError('ny riktning utan text vägras')
        except ValueError as e_:
            assert 'nästa körnings kritik' in str(e_), e_
    finally:
        dash.UNDERLAG, dash.KUNDER, dash.ROOT = spara_dash_kd
    # omtaget: varje kandidat ägaren såg in i historiken
    at_pt.ta_bort_beslut(sl_kd)
    h_kd = sk.historik(sl_kd, kd_u)
    assert len(h_kd) == 3 and all(x_['utfall'] == 'underkänd av ägaren via Codex' for x_ in h_kd) and all(x_['referens'] == 'Xref' for x_ in h_kd), h_kd
    assert not (kd_k / sl_kd / 'kandidater').exists() and not (u_kd / 'atelje').exists(), 'kandidaternas projekt och ateljén tas bort'
    # och först sparades det bedömda (ägarens beslut 2026-10-07): varje version ägaren namngett i en dom, och de förkastade i
    # sin senaste version, med hashen omräknad ur det sparade underlaget och skärmbilderna
    kv_kd = sorted((u_kd / 'omtag').glob('*/*/*/KVITTO.json'))
    domda_kd = {(k_['id'], k_['version'][:12]) for d_ in sk.domar(sl_kd, kd_u) if d_.get('kalla') in sk.AGAREN for k_ in d_.get('kandidater') or []}
    assert domda_kd and {(q_.parent.parent.name, q_.parent.name) for q_ in kv_kd} >= domda_kd, (kv_kd, domda_kd)
    for q_ in kv_kd:
        k_ = json.loads(q_.read_text())
        assert hash_om(q_.parent / 'underlag') == k_['version'] and (q_.parent / 'underlag' / 'kod' / 'index.astro').is_file() and k_['domar'], q_
        assert any(b_.startswith('bilder/start/vy-390-') for b_ in k_['bilder']), (q_, k_['bilder'])
    assert {h_.get('sparat', '').split('/')[-2] for h_ in h_kd} == {'k01', 'k02', 'k03'}, h_kd
    (u_kd / 'atelje').mkdir(); (u_kd / 'atelje' / 'STATUS.json').write_text(json.dumps({'steg': 'klar', 'klar': '2026-10-05T15:00:00Z'}))
    try:
        at_pt.doma(sl_kd, 'ägaren', 'valj', 'x', kandidater=[])
        raise AssertionError('valj utan kandidatflöde vägras')
    except ValueError as e_:
        assert 'kandidatflödet' in str(e_), e_
    (kd_k / sl_kd / 'kandidater' / 'k01' / 'sajt').mkdir(parents=True); (kd_k / sl_kd / 'kandidater' / 'k01' / 'sajt' / 'gammal.txt').write_text('g')
    ark_kd = kd.arkivera_projekt(sl_kd, {})
    assert not (kd_k / sl_kd / 'kandidater').exists() and (ark_kd / 'kunder-kandidater' / 'k01' / 'sajt' / 'gammal.txt').is_file()

    # --- kanalen ut: researchen får fler sajter och frågor i samma form, och aldrig kundens uppgifter (V9) ---
    atta_ = {'referens': {'kandidater': [{'adress': 'https://e%d.se/' % i} for i in range(8)]}, 'tjanster': {'fragor': [{'fraga': 'warm craft', 'syfte': 'x'}] * 14}}
    assert sk.kanal_fel(atta_, bred=True) is None and 'kandidater' in sk.kanal_fel(atta_) and 'frågor' in (sk.kanal_fel(dict(atta_, tjanster={'fragor': [{'fraga': 'x', 'syfte': 'y'}] * 15}), bred=True) or '')
    fb_ = sk.forbjudna_termer(sl_kd, kd_u)
    for fraga_ in ('Provfirman carpentry homepage', 'carpenter site in Lulea', 'boden builder', 'snickeri luleå'):
        assert 'kundens' in (sk.kanal_fel({'tjanster': {'fragor': [{'fraga': fraga_, 'syfte': 'x'}]}}, forbjudna=fb_) or ''), fraga_
    for fraga_ in ('contact block 070-111 22 33', 'org 556677-8899 footer'):
        assert 'kundens' in (sk.kanal_fel({'tjanster': {'fragor': [{'fraga': fraga_, 'syfte': 'x'}]}}, forbjudna=fb_) or ''), fraga_
    assert '0701112233' in fb_['siffror'] and 'lulea' in fb_['ord'] and {'provfirman-snickeri.se', 'provfirman-snickeri', 'provfirman.se', 'provfirman'} <= fb_['ord'], 'webb är ett objekt; e-postens domän spärras (N3)'
    lang_kd = ('a long question about a calm carpentry homepage with documented projects, written so that it passes the '
               'form limit of one hundred and sixty characters, for provfirman')
    assert len(lang_kd) > 160 and 'kundens' in (sk.kanal_fel({'tjanster': {'fragor': [{'fraga': lang_kd, 'syfte': 'x'}]}}, forbjudna=fb_) or ''), 'kunden prövas före formen'
    import referenstjanster as rt_kd
    prompter_kd = []
    kor_rt_kd = lambda tjanst, prompt, logg, modell: prompter_kd.append(prompt) or (1, 'ingen session i provet')  # noqa: E731
    upp_kd = {'fragor': [{'tjanst': 'mobbin', 'fraga': lang_kd, 'syfte': '', 'typ': 'skarm'},
                         {'tjanst': 'refero', 'fraga': 'homepage like provfirman', 'syfte': '', 'typ': 'skarm'},
                         {'tjanst': 'refero', 'fraga': 'contact block', 'syfte': 'write to info@exempel.se', 'typ': 'skarm'},
                         {'tjanst': 'refero', 'fraga': 'warm editorial carpenter homepage', 'syfte': 'stilen', 'typ': 'skarm'}]}
    _r, res_kd = rt_kd.samla(sl_kd, upp_kd, kd_u, kor=kor_rt_kd)
    assert len(res_kd['slappta']) == 3 and len(prompter_kd) == 1 and 'provfirman' not in prompter_kd[0].lower() and 'warm editorial' in prompter_kd[0], res_kd['slappta']
    tj_kd = (u_kd / 'referenser' / 'tjanster' / 'TJANSTER.md').read_text()
    assert 'Släppta frågor' in tj_kd and 'provfirman' not in tj_kd.lower() and 'exempel.se' not in tj_kd, 'de släppta frågorna står i rapporten, utan sin text'
    _r, res_kd = rt_kd.samla(sl_kd, {'fragor': upp_kd['fragor'][:3]}, kd_u, kor=kor_rt_kd)
    assert not res_kd['alla_ok'] and res_kd['tjanster'] == {} and len(prompter_kd) == 1, 'allt släppt: ingen tjänst körs och slutkoden är inte grön'
    # två begäranden samma sekund får egna filer (N7)
    svar7_kd = []
    for i_ in range(2):
        f7_ = u_kd / ('begaran-%d.json' % i_)
        f7_.write_text(json.dumps({'varfor': 'x', 'tjanster': {'fragor': [{'fraga': 'warm craft %d' % i_, 'syfte': 'x'}]}}))
        svar7_kd.append(spara_sk_kd[0](sl_kd, f7_, u_kd / 'n7', kd_u, kor=lambda args, timeout: types.SimpleNamespace(returncode=0, stdout='', stderr='')))
    assert svar7_kd[0]['tid'] != svar7_kd[1]['tid'] and svar7_kd[0]['tjanster']['rapport'] != svar7_kd[1]['tjanster']['rapport'], svar7_kd
    assert len(list(u_kd.glob('TJANSTEUPPDRAG-*.json'))) == 2
    assert sk.kanal_fel({'tjanster': {'fragor': [{'fraga': 'warm editorial carpenter homepage', 'syfte': 'stilen'}]}}, forbjudna=fb_) is None
    # forhandsvisa: en skapare kan bara bygga sin egen kandidat (M2)
    with contextlib.redirect_stderr(io.StringIO()):
        assert fv_kd.main([sl_kd, '--kandidat', 'k01', '--kandidat', 'k02']) == 2
        for argv_ in ([sl_kd, '--kandidat', 'k01', '--kand', 'k02'], [sl_kd, '--kandidat', 'k01', '--kandi=k02']):
            try:
                fv_kd.main(argv_)
                raise AssertionError('en förkortad flagga bygger ingen annan kandidat (N8): %s' % argv_)
            except SystemExit as e_:
                assert e_.code == 2
    # researchen på begäran körs högst en gång per kandidat (N6)
    n6_kd, komp_n6_kd = [], []

    def sess_n6_kd(prompt, verktyg, ut, **kw):
        n6_kd.append((prompt, verktyg))
        (kd.kdir(sl_kd, 'k01') / sk.KOMPLETTERING).write_text(json.dumps({'varfor': 'x', 'tjanster': {'fragor': [{'fraga': 'warm craft', 'syfte': 'x'}]}}))
        Path(ut).write_text('{}')
        return {}
    at_pt.session = sess_n6_kd
    sk.komplettera = lambda slug, fil, rot, underlag=None, **kw: komp_n6_kd.append(fil) or Path(fil).unlink() or {'tid': 't', 'varfor': 'x'}
    for f_, t_ in (('package.json', '{}'), ('astro.config.mjs', 'export default {}'), ('src/pages/404.astro', '404')):  # sajten efter omtaget
        (huvud_kd / f_).parent.mkdir(parents=True, exist_ok=True)
        (huvud_kd / f_).write_text(t_) if not (huvud_kd / f_).exists() else None
    (huvud_kd / 'node_modules').mkdir(exist_ok=True)
    kd.satt_status(sl_kd, 'k01', 'planerad', 'x', forsok=0)
    kd.skapa(sl_kd, 'k01')
    assert len(komp_n6_kd) == 1 and len(n6_kd) == 2, (len(komp_n6_kd), len(n6_kd))
    assert 'högst en gång per kandidat' in n6_kd[0][0] and 'högst en gång per kandidat' not in n6_kd[1][0]
    assert any(v_.endswith('/KOMPLETTERING.json)') for v_ in n6_kd[0][1]) and not any('KOMPLETTERING' in v_ for v_ in n6_kd[1][1])
    assert len(list((kd.kdir(sl_kd, 'k01') / 'kompletteringar').glob('*-obesvarad.json'))) == 1 and kd.las_status(sl_kd, 'k01')['kompletterad']
    kd.skapa(sl_kd, 'k01')  # ett andra skaparförsök får ingen ny research
    assert len(komp_n6_kd) == 1 and len(n6_kd) == 3 and 'högst en gång per kandidat' not in n6_kd[2][0]
    # en sista skaparsession som dog med processen fotograferas och bedöms (N12)
    kd.satt_status(sl_kd, 'k01', 'under_arbete', 'skaparsession 2', forsok=2)
    (kd.ksajt(sl_kd, 'k01') / 'src' / 'pages' / 'index.astro').write_text('det sessionen hann')
    st12_kd = kd.behandla(sl_kd, 'k01')
    assert len(n6_kd) == 3 and st12_kd['status'] in ('klar', 'ofullstandig') and st12_kd.get('fotograferad'), st12_kd
finally:
    at_pt.UNDERLAG, at_pt.KUNDER, at_pt.session, at_pt.ROOT = spara_at_kd
    for n_, v_ in spara_kd.items():
        setattr(kd, n_, v_)
    prova.bygg_inom_grans, prova.kor, prova.Server = spara_prova_kd
    sk.komplettera, sk.lagg_till_dom = spara_sk_kd
    dash.UNDERLAG, dash.KUNDER, dash.ROOT = spara_dash_kd
    bk_pt.ROOT = spara_bk_kd
print('kandidatflödet ok')

# ---------------------------------------------------------------- skissläget (ägarens uppdrag 2026-10-05 16:25Z: full verktygslåda, ren arbetsbänk)
import threading as thr_sk  # noqa: E402
import nastlad as nl_sk  # noqa: E402
sk_u, sk_k = tmp / 'sk-underlag', tmp / 'sk-kunder'
spara_at_sk = (at_pt.UNDERLAG, at_pt.KUNDER, at_pt.session, at_pt.ROOT)
spara_sk = {n: getattr(kd, n) for n in ('PARALLELLT', 'LAGE', 'FRIST_SKISS', 'FRIST_SKISS_OMFORSOK')}
spara_prova_sk = (prova.bygg_inom_grans, prova.kor, prova.Server)
spara_komp_sk = sk.komplettera
spara_dash_sk = (dash.UNDERLAG, dash.KUNDER, dash.ROOT)
spara_bk_sk = bk_pt.ROOT
at_pt.UNDERLAG, at_pt.KUNDER, at_pt.ROOT, bk_pt.ROOT = sk_u, sk_k, tmp, tmp
sl_sk = 'sk-prov'
u_sk, huvud_sk = sk_u / sl_sk, sk_k / sl_sk / 'sajt'
try:
    # --- underlaget med befintlig research (ett referenspaket och tjänsternas rapport), och sajten ur mallen ---
    (u_sk / 'bilder').mkdir(parents=True)
    (u_sk / 'bilder' / 'a.jpg').write_bytes(b'jpg')
    (u_sk / 'bilder' / 'BILDER.md').write_text('# Bilder\n\n- a.jpg: ett kök, helbild\n')
    (u_sk / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Skissfirman Bygg AB', 'adress': {'ort': 'Piteå', 'postnummer': '123 45'},
                                                       'kontaktvagar': [{'typ': 'telefon', 'varde': '070-111 22 33'}], 'kategorier': ['Snickare'],
                                                       'oppettider': [{'dag': 'man', 'oppnar': '07:00', 'stanger': '16:00'}]}))
    for f_, t_ in (('BRIEF.md', '# Brief\n\n## §2 Målgrupper och toppuppgifter\n\n1. Se liknande jobb\n'), ('RESEARCH.md', '# Research\n\nGrundat 1998.\n'),
                   ('TEXTUNDERLAG.md', '# Text\n\nVi bygger kök och altaner.\n')):
        (u_sk / f_).write_text(t_)
    (u_sk / 'referenser' / 'paket-v01' / 'x').mkdir(parents=True)
    (u_sk / 'referenser' / 'paket-v01' / 'x' / 'vy.png').write_bytes(b'png')
    (u_sk / 'referenser' / 'paket-v01' / 'PAKET.md').write_text('# Paket\n\n## Xref\n')
    (u_sk / 'referenser' / 'tjanster').mkdir(); (u_sk / 'referenser' / 'tjanster' / 'TJANSTER.md').write_text('# tjänsterna')
    (u_sk / sk.DOMLOGG).write_text('\n'.join(json.dumps(d_) for d_ in (
        {'tid': '2026-10-01T10:00:00Z', 'kalla': 'ägaren', 'beslut': 'putsa', 'text': 'GAMMAL SMAKDOM: mörkgrönt'},
        {'tid': '2026-10-02T10:00:00Z', 'kalla': 'ägaren', 'beslut': 'ny_riktning', 'text': 'AKTUELL: pröva nya grundidéer'})) + '\n')
    for f_, t_ in (('package.json', '{}'), ('astro.config.mjs', 'export default {}'), ('src/pages/index.astro', 'mallens start'), ('src/pages/404.astro', '404')):
        (huvud_sk / f_).parent.mkdir(parents=True, exist_ok=True)
        (huvud_sk / f_).write_text(t_)
    (huvud_sk / 'node_modules').mkdir()

    # --- kundens aktuella domar: från den senaste nya riktningen; det äldre är historik ---
    akt_ = '\n'.join(sk.kritikrader(sl_sk, underlag=sk_u, aktuella=True))
    assert 'AKTUELL' in akt_ and 'GAMMAL SMAKDOM' not in akt_ and 'GAMMAL SMAKDOM' in '\n'.join(sk.kritikrader(sl_sk, underlag=sk_u)), akt_

    # --- metoden: skissens kärna med en förteckning, utdragen att slå upp i egna filer ---
    lev_sk = md_kd.leverera('skiss', tmp / 'sk-metod')
    fore_sk = [f_ for f_ in lev_sk['filer'] if f_['del'] == 'före']
    upp_sk = [f_ for f_ in lev_sk['filer'] if f_['del'] == 'uppslag']
    assert len(fore_sk) == 1 and not upp_sk and '## Att slå upp' not in fore_sk[0]['fil'].read_text(), 'inga frivilliga utdrag: kompetenserna bär skillsen'
    assert '### kunskap/designregler.md' in fore_sk[0]['fil'].read_text() and 'Kompetenserna' in fore_sk[0]['fil'].read_text()

    # --- instruktionsvägarna: CLAUDE.md (laddas i varje nästlad session), helbyggets uppstart och miljön ---
    claude_md_ = (ROOT / 'CLAUDE.md').read_text()
    assert 'gäller före allt annat' not in claude_md_ and 'designregler.md' in claude_md_ and 'slås upp' in claude_md_
    bygg_md_ = (ROOT / '.claude' / 'skills' / 'bygg-sajt' / 'SKILL.md').read_text()
    assert '(varje dom)' not in bygg_md_ and 'gäller före allt annat' not in bygg_md_ and 'kunskap/designregler.md' in bygg_md_
    assert 'ANTHROPIC_API_KEY' not in nl_sk.miljo({'ANTHROPIC_API_KEY': 'x', 'ANTHROPIC_BASE_URL': 'y', 'PATH': '/bin'}) and 'PATH' in nl_sk.miljo({'PATH': '/bin'})
    a_sk = at_pt.session_args(kd.verktyg(sl_sk, 'k01'), None, 10, 'm', 'high', (), sl_sk)  # alla skills (ägarens ord 18:15Z), MCP:erna med kundvakten
    assert a_sk[a_sk.index('--tools') + 1] == 'Bash,Edit,Glob,Grep,Read,Skill,ToolSearch,Write' and '--disable-slash-commands' not in a_sk and '--bare' not in a_sk, a_sk
    a_sk = at_pt.session_args(kd.LASVERKTYG, {'type': 'object'}, 10, 'm', 'high', (), sl_sk)
    assert a_sk[a_sk.index('--tools') + 1] == 'Glob,Grep,Read,Skill,ToolSearch' and '--json-schema' in a_sk and '--settings' in a_sk

    # --- bygget, webbläsaren och sessionerna ersatta; den riktiga fotograferingen och de snabba kontrollerna körs ---
    def bygg_sk(sajt, timeout=900):
        pages, dist = Path(sajt) / 'src' / 'pages', Path(sajt) / 'dist'
        if not (pages / 'index.astro').is_file() or 'TRASIG' in (pages / 'index.astro').read_text():
            return 1, 'bygget föll: TRASIG'
        for p_ in pages.rglob('index.astro'):
            m_ = dist / p_.relative_to(pages).parent / 'index.html'; m_.parent.mkdir(parents=True, exist_ok=True); m_.write_text(p_.read_text())
        return 0, 'byggt'
    inspekterat_sk = []

    def kor_sk(cmd, cwd=None, timeout=900):
        cmd = [str(x) for x in cmd]
        if any(x.endswith('inspektera.mjs') for x in cmd):
            inspekterat_sk.append(cmd)
            ut_ = Path(cmd[cmd.index('--ut') + 1]); ut_.mkdir(parents=True, exist_ok=True)
            for n_ in BILDER_KD:
                (ut_ / n_).write_bytes(b'png')
            k01_ = '/k01/' in str(ut_)
            (ut_ / 'INSPEKTION.json').write_text(json.dumps({'vyer': {'390': {'konsol': [{'typ': 'error', 'text': 'Uncaught X'}] if k01_ else [], 'spill': {'spill': False},
                                                                                 'tillstand': {'meny': {'klickad': True, 'expanded': 'false' if k01_ else 'true'}}}}}))
            return 0, ''
        if any(x.endswith('axe.mjs') for x in cmd):
            ut_ = Path(next(x for x in cmd if x.startswith('--ut='))[5:]); ut_.mkdir(parents=True, exist_ok=True)
            (ut_ / 'axe.json').write_text(json.dumps({'allvarliga': 0, 'totalt': 1, 'axeVersion': 'x', 'rader': []}))
            return 0, ''
        return spara_prova_sk[1](cmd, cwd=cwd, timeout=timeout)
    prova.bygg_inom_grans, prova.kor, prova.Server = bygg_sk, kor_sk, SrvKd
    sess_sk, samtidiga_sk, max_sk, las_sk = [], [0], [0], thr_sk.Lock()
    pp_sk_n, omp_sk_n = [0], [0]  # planprövningens rundor och omplaneringarna (2E: återgången; R01: en misslyckad tas upp igen)
    trasig_k03, dod_k05 = [True], [True]

    def sess_sk_(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), slug=None, vid_start=None):
        sess_sk.append({'prompt': prompt, 'verktyg': verktyg, 'ut': Path(ut).name, 'schema': schema, 'effort': effort, 'frist': frist,
                        'nekas': list(nekas), 'slug': slug})
        so, sid_sk = None, 's'
        if vid_start:
            vid_start(999999990)
        if schema in (kd.FORSKA_SCHEMA_SKISS, kd.FORSKA_SCHEMA_SKISS_BRED):
            so = {'varfor': 'befintligt material räcker', 'riktningar': 'fem grunder', 'sajter': [], 'fragor': [],
                  'antaganden': [{'antagande': 'besökaren vill se jobb', 'underlag': 'ännu inte observerat', 'provning': 'uppgift', 'om_fel': 'kontakt först'}]}
        elif schema is kd.PLAN_SCHEMA:
            so = {'variation': 'fem grunder', 'kandidater': [dict({f_: '%s %d' % (f_, i_) for f_, _r in kd.PLANFALT}, referensbilder=['underlag/sk-prov/referenser/paket-v01/x/vy.png'])
                                                            for i_ in range(5)]}
        elif schema is kd.PLANPROVNING_SCHEMA:  # specialisterna prövar planen och ändrar ett fält; k02 och k03 får en återgång (2E) i båda rundorna
            pp_sk_n[0] += 1
            so = {'sammanfattning': 'typografin i k01 skärptes', 'kandidater': [
                {'id': 'k01', 'bedomning': 'riktningen bär', 'andringar': [{'falt': 'typografi', 'nytt': 'NY TYPOGRAFI ur planprövningen', 'skill': 'impeccable', 'varfor': 'hierarkin'}]},
                {'id': 'k02', 'bedomning': 'hypotesen bär inte kundens material',
                 'andringar': [{'falt': 'typografi', 'nytt': 'PUTS AV DET STOPPADE', 'skill': 'impeccable', 'varfor': 'runda 2'}] if pp_sk_n[0] == 2 else [],
                 'atergang': {'typ': 'ny_hypotes', 'skal': 'hypotesen bär inte kundens material', 'ny_hypotes': 'NY HYPOTES k02'}},
                {'id': 'k03', 'bedomning': 'referensen saknar kvaliteten', 'andringar': [],
                 'atergang': {'typ': 'ny_referens', 'skal': 'referensen saknar kvaliteten', 'ny_huvudreferens': 'Xref'}},
                # F01 (GR-20261009-metod-till-resultat-codex): varje uppdrag som släpps till skaparen har en egen bedömning
                {'id': 'k04', 'bedomning': 'uppdraget bär', 'andringar': []}, {'id': 'k05', 'bedomning': 'uppdraget bär', 'andringar': []},
                {'id': 'k99', 'bedomning': 'finns inte', 'andringar': [{'falt': 'typografi', 'nytt': 'x', 'skill': 'x', 'varfor': 'x'}]}]}
            sid_sk = transkript_kd([('Read', {'file_path': f_}, False) for f_ in kd.kompetens.lasfiler('planprovning')] + [('Skill', {'skill': 'impeccable'}, False)])
        elif isinstance(schema, dict) and 'OMPLANERING' in prompt:  # återgångens omplanering med samma identitet
            omp_sk_n[0] += 1
            n_ = schema['properties']['kandidater']['minItems']
            assert n_ == schema['properties']['kandidater']['maxItems'] and n_ == (2 if omp_sk_n[0] == 1 else 1) and 'k02' in prompt, (omp_sk_n, n_)
            ny_ = lambda kid_, hyp_, ref_: dict({f_: '%s omplanerad' % f_ for f_, _r in kd.PLANFALT}, titel='%s omplanerad' % kid_, hypotes=hyp_, huvudreferens='Xref',
                                                referensbilder=[ref_])
            if omp_sk_n[0] == 1:  # R01: k02:s nya uppdrag saknar referensunderlag (avvisas), k03:s håller
                so = {'variation': 'omplanerad', 'kandidater': [ny_('k02', 'FEL HYPOTES utan referens', 'underlag/sk-prov/referenser/finns-inte.png'),
                                                                ny_('k03', 'NY HYPOTES k03', 'underlag/sk-prov/referenser/paket-v01/x/vy.png')]}
            else:  # återupptagningens nya försök för k02: nu med underlag
                so = {'variation': 'omplanerad', 'kandidater': [ny_('k02', 'NY HYPOTES k02', 'underlag/sk-prov/referenser/paket-v01/x/vy.png')]}
            sid_sk = transkript_kd([('Read', {'file_path': f_}, False) for f_ in kd.kompetens.lasfiler('planera')])
        elif schema is kd.PASS_SCHEMA:  # ett kompetenspass
            kid_ = re.search(r'Kandidaten (k\d\d)', prompt).group(1)
            pass_ = next(k_ for k_, n_ in kd.kompetens.PASSNAMN.items() if 'specialisten för %s' % n_ in prompt)
            index_ = kd.ksajt(sl_sk, kid_) / 'src' / 'pages' / 'index.astro'
            filer_ = kd.kompetens.lasfiler(pass_)
            if kid_ == 'k02' and pass_ == 'mobil' and 'Förra försöket saknade:' not in prompt:
                filer_ = filer_[1:]  # läser inte alla: ett omförsök
            if kid_ == 'k03' and pass_ == 'kritik':
                index_.write_text('TRASIG efter kritiken')  # passet bryter sidan: versionen före återställs
            elif pass_ != 'rorelse':
                index_.write_text(index_.read_text() + '\n<p>%s-pass</p>' % pass_)
            so = {'andringar': [] if pass_ == 'rorelse' else [{'skill': 'impeccable', 'vad': '%s rättat' % pass_, 'var': 'första vyn', 'varfor': 'passet'}],
                  'ingen_andring': 'sidan ska vara stilla' if pass_ == 'rorelse' else '', 'passade_inte': [], 'kvarstar': []}
            sid_sk = transkript_kd([('Read', {'file_path': f_}, False) for f_ in filer_] + [('Write', {'file_path': kd.rel(index_)}, False)])
        elif schema is None:  # en skissare
            kid_ = re.search(r'Du gör\nEN skiss, (k\d\d)|EN skiss, (k\d\d)', prompt)
            kid_ = kid_.group(1) or kid_.group(2)
            with las_sk:
                samtidiga_sk[0] += 1; max_sk[0] = max(max_sk[0], samtidiga_sk[0])
            try:
                time.sleep(0.05)
                pages_ = kd.ksajt(sl_sk, kid_) / 'src' / 'pages'
                if kid_ == 'k04':  # tiden tar slut med en sida som inte bygger: ofullständig, inget omförsök (ingen förlängning)
                    (pages_ / 'index.astro').write_text('TRASIG halvfärdig')
                    raise subprocess.TimeoutExpired('claude', frist)
                if kid_ == 'k05' and dod_k05[0]:  # processen dör mitt i försöket, efter RIKTNING.md och ett varv (S1)
                    dod_k05[0] = False
                    (pages_ / 'index.astro').write_text('<h1>halv skiss</h1>')
                    (kd.kdir(sl_sk, kid_) / 'RIKTNING.md').write_text('Huvudreferens: Xref — halv\n')
                    (kd.kdir(sl_sk, kid_) / 'varv' / 'start' / 'varv-01').mkdir(parents=True, exist_ok=True)
                    raise KeyboardInterrupt('processen dog')
                text_ = {'k02': '<h1>Skiss</h1><p>Med 25 år i branschen. Ring 070-111 22 33, vardagar 07:00–16:00.</p>'}.get(kid_, '<h1>Skiss</h1><p>Kök och altaner. Utkast: om oss.</p>')
                (pages_ / 'index.astro').write_text('TRASIG' if kid_ == 'k03' and trasig_k03[0] else text_)
                if kid_ == 'k03':
                    trasig_k03[0] = False
                (kd.kdir(sl_sk, kid_) / 'RIKTNING.md').write_text('Huvudreferens: Xref — kompositionen\n\n## Varv 1\n\nrubriken för stor\n\n## Material\n\nFler foton.\n')
                sid_sk = transkript_kd([('Read', {'file_path': f_}, False) for f_ in kd.kompetens.lasfiler('skapa')]
                                       + [('mcp__refero__refero_search_screens', {'query': 'carpenter homepage hero'}, False), ('Write', {'file_path': kd.rel(pages_ / 'index.astro')}, False)])
            finally:
                with las_sk:
                    samtidiga_sk[0] -= 1
        svar_ = {'structured_output': so, 'num_turns': 5, 'duration_ms': 60000, 'total_cost_usd': 0.5, 'session_id': sid_sk}
        Path(ut).write_text(json.dumps(svar_))
        return svar_
    at_pt.session = sess_sk_
    sk.komplettera = lambda *a, **k: (_ for _ in ()).throw(AssertionError('skissläget hämtar inget när materialet räcker'))
    kd.PARALLELLT, kd.LAGE = 5, 'skiss'

    # --- hela omgången: k05:s process dör mitt i försöket och körningen tas upp igen ---
    st_sk = {'startad': '2026-10-05T09:00:00Z', 'lage': 'ny', 'modell': 'm', 'effort': 'max'}  # före klockan: tiderna jämförs med loggen
    spara_hook_sk = thr_sk.excepthook
    thr_sk.excepthook = lambda a_: None  # k05:s tråd dör mitt i försöket, som processen skulle
    try:
        kd.kor(sl_sk, st_sk, lambda: None, n=5)
    finally:
        thr_sk.excepthook = spara_hook_sk
    assert kd.las_status(sl_sk, 'k05')['status'] == 'under_arbete'
    # R01 (GR-20261008-06af6ff-omgranskning-codex): k02:s omplanering gav inget användbart uppdrag; kandidaten stoppas med sitt
    # skäl, och ingen skapare startar med det förkastade uppdraget (bara den lyckade k03 omplaneras)
    s2_r01 = kd.las_status(sl_sk, 'k02')
    assert s2_r01['status'] == 'fel' and s2_r01['atergang_fel']['invandning']['ny_hypotes'] == 'NY HYPOTES k02' and 'saknar underlag' in s2_r01['atergang_fel']['fel'], s2_r01
    assert 'förkastade uppdraget byggs inte' in s2_r01['skal'] and s2_r01.get('hypotes') not in ('FEL HYPOTES utan referens', 'NY HYPOTES k02'), s2_r01
    assert not any('EN skiss, k02' in s_['prompt'] for s_ in sess_sk if s_['schema'] is None), 'en skapare startade med det förkastade uppdraget (R01)'
    assert 'FEL HYPOTES' not in (kd.kdir(sl_sk, 'k02') / 'UPPDRAG.md').read_text() and kd.las_status(sl_sk, 'k03')['hypotes'] == 'NY HYPOTES k03'
    pp_r01 = json.loads((kd.rot(sl_sk) / 'PLANPROVNING.json').read_text())
    assert pp_r01['atergang']['misslyckade'] == ['k02'] and pp_r01['atergang']['omplanerade'] == ['k03'] and 'Återgången misslyckades' in (kd.rot(sl_sk) / 'PLANPROVNING.md').read_text(), pp_r01.get('atergang')
    assert any(x['id'] == 'k02' and x['falt'] == 'typografi' and 'återgången misslyckades' in x['skal'] for x in pp_r01['ogjorda']), 'det stoppade uppdraget putsas inte (R01)'
    assert st_sk['planprovning']['atergang']['misslyckade'] == ['k02'], st_sk.get('planprovning')
    kd.LAGE = 'full'  # en återupptagning följer körningens plan, inte miljön
    klara_sk = kd.kor(sl_sk, st_sk, lambda: None, n=5)
    kd.LAGE = 'skiss'
    plan_sk = json.loads((kd.rot(sl_sk) / 'KANDIDATPLAN.json').read_text())
    assert plan_sk['lage'] == 'skiss' and st_sk['kandidatlage'] == 'skiss' and st_sk['steg'] == 'klar_for_bedomning', st_sk
    assert sorted(klara_sk) == ['k01', 'k02', 'k03', 'k05'], klara_sk
    fo_sk = json.loads((kd.rot(sl_sk) / 'FORSKNING.json').read_text())
    assert fo_sk['fel'] is None and fo_sk['fore']['paket'] == 'paket-v01' and not fo_sk['nytt']['paket'], 'det befintliga materialet återanvänds'
    schemor_ = [s_['schema'] for s_ in sess_sk]
    assert kd.KRITIK_A_SCHEMA not in schemor_ and kd.KRITIK_B_SCHEMA not in schemor_ and kd.JAMFOR_SCHEMA not in schemor_, 'ingen panel före ägarens val'
    assert not any('Förbättringsrundan' in s_['prompt'] for s_ in sess_sk), 'ingen förbättringsrunda före ägarens val'
    assert max_sk[0] <= 3, 'högst tre skisser samtidigt (%d)' % max_sk[0]
    skisser_ = [s_['prompt'] for s_ in sess_sk if s_['schema'] is None and 'EN skiss' in s_['prompt']]
    assert skisser_ and all('rubriken "%s"' % kd.OVERFORT in p_ for p_ in skisser_), 'skissens skapare redovisar det överförda och avvikelserna'
    plan_p_ = next(s_['prompt'] for s_ in sess_sk if s_['schema'] is kd.PLAN_SCHEMA)
    assert 'skisser (första vyn' in plan_p_ and 'sektion' in plan_p_ and 'LARDOMAR-original' not in plan_p_ and 'AKTUELL' in plan_p_ and 'GAMMAL SMAKDOM' not in plan_p_
    # flera skisser: hela bredden utan minsta antal, och frågorna föreskriver aldrig formen (ägarens uppdrag 2026-10-06)
    forska_p_ = next(s_['prompt'] for s_ in sess_sk if s_['schema'] is kd.FORSKA_SCHEMA_SKISS_BRED)
    assert 'Återanvänd researchen' in forska_p_ and 'både Refero och Mobbin' in forska_p_ and 'aldrig formen' in forska_p_ and 'högst 4 sajter' not in forska_p_
    assert kd.FORSKA_SCHEMA_SKISS_BRED['properties']['fragor']['minItems'] == 0 and kd.FORSKA_SCHEMA_SKISS_BRED['properties']['sajter']['maxItems'] > 4
    up_sk = (kd.kdir(sl_sk, 'k01') / 'UPPDRAG.md').read_text()
    assert 'Den viktigaste innehållssektionen' in up_sk and 'sektion 0' in up_sk
    # --- skaparens rena arbetskontext ---
    sk_p = [s_ for s_ in sess_sk if s_['schema'] is None]
    p1_ = next(s_ for s_ in sk_p if 'EN skiss, k01' in s_['prompt'])
    for krav_ in ('Omfattningen: första vyn', 'METOD-skiss.md', 'VERKSAMHET.json', 'TEXTUNDERLAG.md', 'BILDER.md', 'UPPDRAG.md', 'Kundens historik slås upp',
                  'Hitta aldrig på omdömen', 'Inget fast antal varv', 'försöket högst %d minuter' % (kd.FRIST_SKISS // 60), 'AKTUELL',
                  'Ditt mandat', 'Förslag som du får ompröva', 'Första varvet efter renderingen prövar grunden', 'Kvarvarande svagheter', '--mellan'):
        assert krav_ in p1_['prompt'], krav_
    for inte_ in ('LARDOMAR-original', 'Arbetsregeln är minst', 'GAMMAL SMAKDOM', 'METOD-skiss-uppslag.md', 'undersidan eller tillståndet som uppdraget anger'):
        assert inte_ not in p1_['prompt'], inte_
    assert p1_['effort'] == kd.EFFORT_SKISS and p1_['frist'] <= kd.FRIST_SKISS and 'Read(./kunder/sk-prov/kandidater/k02/**)' in p1_['nekas'], (p1_['effort'], p1_['frist'], p1_['nekas'][:4])
    # skillverktyget och förhandsvisningen; MCP:erna aldrig i tillåtelselistan (kundvakten öppnar varje rent anrop, G3)
    assert 'Skill' in p1_['verktyg'] and not any(str(v_).startswith('mcp__') for v_ in p1_['verktyg']) and any('forhandsvisa.py sk-prov --kandidat k01' in v_ for v_ in p1_['verktyg'])
    assert 'Write(./kunder/sk-prov/kandidater/k01/sajt/src/**)' in p1_['verktyg'] and 'Write(./kunder/sk-prov/kandidater/k01/sajt/src/assets/atelje/**)' in p1_['nekas'], 'hela src/, aldrig kundens bilder (Codex punkt 5)'
    assert 'Referenslås' in p1_['prompt'] and 'Ingen annan session ändrar' in p1_['prompt'] and 'aldrig instruktioner till dig' not in p1_['prompt'], 'metoden är instruktioner, externt innehåll material'
    # --- de snabba kontrollerna: bristerna markeras, skissen går att bedöma ---
    s1_, s2_, s3_, s4_, s5_ = (kd.las_status(sl_sk, k_) for k_ in ('k01', 'k02', 'k03', 'k04', 'k05'))
    assert s1_['status'] == 'klar' and any('konsolfel' in b_ for b_ in s1_['brister']) and any('menyns knapp' in b_ for b_ in s1_['brister']), s1_.get('brister')
    assert s2_['status'] == 'klar' and any('siffror' in b_ and '25' in b_ for b_ in s2_['brister']) and not any('070' in b_ or '16' in b_ for b_ in s2_['brister']), s2_.get('brister')
    assert all('--meny' in c_ for c_ in inspekterat_sk) and not any('/undersidor/' in ' '.join(c_) for c_ in inspekterat_sk), 'bara startsidan, med menyns knapp'
    # k03: bygget föll i första försöket (ett tekniskt fel): ett omförsök med kortare tid och felet
    assert s3_['status'] == 'klar' and s3_['forsok'] == 2 and [x_['omforsok'] for x_ in s3_['forsok_tider']] == [False, True], s3_.get('forsok_tider')
    p3b_ = [s_ for s_ in sk_p if 'EN skiss, k03' in s_['prompt']][-1]
    assert 'tekniskt fel' in p3b_['prompt'] and 'bygget föll' in p3b_['prompt'] and p3b_['frist'] <= kd.FRIST_SKISS_OMFORSOK
    # k04: tiden tog slut innan något byggts: ofullständig med skälet, inget omförsök
    assert s4_['status'] == 'ofullstandig' and s4_['forsok'] == 1 and s4_['forsok_tider'][0]['tidsgrans'] and 'bygget föll' in s4_['skal'] and not s4_['tekniskt_fel'], s4_
    # k05: det avbrutna försöket sparades och startades om i ett nytt projekt
    assert s5_['status'] == 'klar' and s5_['forsok'] == 2 and (kd.kdir(sl_sk, 'k05') / 'forsok-1' / 'projekt' / 'src' / 'pages' / 'index.astro').read_text() == '<h1>halv skiss</h1>', s5_
    assert 'halv' not in (kd.ksajt(sl_sk, 'k05') / 'src' / 'pages' / 'index.astro').read_text()
    # --- planprövningen: specialisterna ändrade ett fält i k01:s uppdrag; ett okänt id ändrar inget. Runda 2 står i
    # PLANPROVNING-tidigare-1.json sedan återupptagningen prövade k02:s nya uppdrag (N01 i GR-20261009-natt-omgranskning-codex) ---
    pp_sk = json.loads((kd.rot(sl_sk) / 'PLANPROVNING-tidigare-1.json').read_text())
    assert pp_sk['andrade'] == 1 and pp_sk['kvitto']['verifierad'] and not pp_sk['kvitto']['saknas'] and 'impeccable' in pp_sk['kvitto']['skill_anrop'], pp_sk
    assert 'NY TYPOGRAFI ur planprövningen' in (kd.kdir(sl_sk, 'k01') / 'UPPDRAG.md').read_text() and (kd.rot(sl_sk) / 'PLANPROVNING.md').is_file()
    # 2E (uppdraget 2026-10-08): återgången: k03 fick ett nytt uppdrag med samma identitet, planen prövades en andra gång, och en
    # ny återgång i runda 2 bokförs som ogjord; runda 1:s besked bevaras för sig. R01: k02, som stoppades, fick ett nytt
    # omplaneringsförsök när körningen togs upp, och byggdes först då, med det nya uppdraget
    assert pp_sk['runda'] == 2 and pp_sk['atergang']['omplanerade'] == ['k03'] and pp_sk['atergang']['research'] is None and pp_sk['atergang']['misslyckade'] == ['k02'], pp_sk.get('atergang')
    r1_sk = json.loads((kd.rot(sl_sk) / 'PLANPROVNING-runda-1.json').read_text())
    assert r1_sk['runda'] == 1 and [a_['id'] for a_ in r1_sk['atergangar']] == ['k02', 'k03'] and r1_sk['atergangar'][0]['ny_hypotes'] == 'NY HYPOTES k02', r1_sk['atergangar']
    assert (kd.rot(sl_sk) / 'PLANPROVNING-runda-1.md').is_file() and 'Återgången (runda 1)' in (kd.rot(sl_sk) / 'PLANPROVNING.md').read_text()
    assert kd.las_status(sl_sk, 'k02')['hypotes'] == 'NY HYPOTES k02' and 'NY HYPOTES k02' in (kd.kdir(sl_sk, 'k02') / 'UPPDRAG.md').read_text()
    assert 'atergang_fel' not in kd.las_status(sl_sk, 'k02') and any('EN skiss, k02' in s_['prompt'] for s_ in sess_sk if s_['schema'] is None), 'k02 byggdes efter rättelsen'
    assert any(x['falt'] == 'atergang' and 'en återgång per plan' in x['skal'] for x in pp_sk['ogjorda']), pp_sk['ogjorda']
    assert pp_sk_n[0] == 3 and omp_sk_n[0] == 2, 'tre prövningar (runda 1, runda 2 och omprövningen av k02:s nya uppdrag), en omplanering och ett nytt försök (%s, %s)' % (pp_sk_n, omp_sk_n)
    # N01: k02:s nya uppdrag prövades vid återupptagningen innan skaparen fick det, och prövningen är bunden till den versionen
    pp_om_ = json.loads((kd.rot(sl_sk) / 'PLANPROVNING.json').read_text())
    i_pp_ = [i_ for i_, s_ in enumerate(sess_sk) if s_['schema'] is kd.PLANPROVNING_SCHEMA]
    i_k02_ = next(i_ for i_, s_ in enumerate(sess_sk) if s_['schema'] is None and 'EN skiss, k02' in s_['prompt'])
    assert len(i_pp_) == 3 and i_pp_[2] < i_k02_ and 'Omprövning: uppdragen k02' in sess_sk[i_pp_[2]]['prompt'], (i_pp_, i_k02_)
    plan_om_ = json.loads((kd.rot(sl_sk) / 'KANDIDATPLAN.json').read_text())['kandidater']
    assert pp_om_['omprovning']['kandidater'] == ['k02'] and pp_om_['provade']['k02'] == kd.uppdrag_sha(plan_om_['k02']), pp_om_.get('omprovning')
    assert pp_om_['provade']['k01'] == kd.uppdrag_sha(plan_om_['k01']) and pp_om_['atergang']['misslyckade'] == [], pp_om_.get('atergang')
    assert any(x['id'] == 'k01' and 'redan prövat' in x['skal'] for x in pp_om_['ogjorda']), 'omprövningen ändrar inte ett redan prövat uppdrag'
    plan_sk_ = json.loads((kd.rot(sl_sk) / 'KANDIDATPLAN.json').read_text())
    assert plan_sk_['atergang']['omplanerade'] == ['k02', 'k03'] and plan_sk_['atergang']['misslyckade'] == [] and plan_sk_['atergang']['omforsok'][0]['omplanerade'] == ['k02'], plan_sk_['atergang']
    assert plan_sk_['kandidater']['k02']['titel'] == 'k02 omplanerad' and 'Omplanerade efter planprövningens återgång' in (kd.rot(sl_sk) / 'KANDIDATPLAN.md').read_text()
    assert st_sk['planprovning']['runda'] == 2 and st_sk['planprovning']['omprovning']['kandidater'] == ['k02'] and st_sk['atergang_omforsok'] == {'kandidater': ['k02'], 'omplanerade': ['k02'], 'fel': None}, (st_sk.get('planprovning'), st_sk.get('atergang_omforsok'))
    pp_p_ = next(s_ for s_ in sess_sk if s_['schema'] is kd.PLANPROVNING_SCHEMA)
    assert 'refero-design/SKILL.md' in pp_p_['prompt'] and 'impeccable/reference/shape.md' in pp_p_['prompt'] and 'Refero' in pp_p_['prompt'] and 'Skill' in pp_p_['verktyg'] and pp_p_['slug'] == sl_sk
    # granskning 4, G1: planprövningen får kundens aktuella domar, designreglerna och Avgörandena (METOD-plan.md)
    assert 'AKTUELL' in pp_p_['prompt'] and 'kunskap/designregler.md' in pp_p_['prompt'] and 'METOD-plan.md' in pp_p_['prompt'] and 'låsta' in pp_p_['prompt']
    # --- före ägarens val ändrar ingen annan session skissen (Codex punkt 8): bara skaparens kvitto ---
    for k_ in ('k01', 'k02', 'k03', 'k05'):
        rec_ = kd.las_status(sl_sk, k_)['kompetens']
        assert set(rec_) == {'skiss:skapa'}, (k_, sorted(rec_))
        # kärnan läst hel; MCP-anropet räknas eftersom det gav svar (G7), men krävs inte (researchen hämtade materialet)
        assert rec_['skiss:skapa']['karnan_last'] and 'genomford' not in rec_['skiss:skapa'] and rec_['skiss:skapa']['kvitto']['mcp_anrop'] == {'mcp__refero__refero_search_screens': 1}, rec_['skiss:skapa']
    assert not [s_ for s_ in sess_sk if s_['schema'] is kd.PASS_SCHEMA], 'inga pass före ägarens val'
    assert all(s_['slug'] == sl_sk for s_ in sess_sk if s_['schema'] in (None, kd.PLANPROVNING_SCHEMA, kd.PLAN_SCHEMA)), 'varje session får kundens slug: skills, MCP:er och kundvakten'
    sk1_p_ = next(s_ for s_ in sk_p if 'EN skiss, k01' in s_['prompt'])
    assert 'craft-floor.md' in sk1_p_['prompt'] and 'uxsok.py' in sk1_p_['prompt'] and any('kontroller/uxsok.py' in v_ for v_ in sk1_p_['verktyg']) and 'RESEARCH.md' in sk1_p_['prompt'] and 'BRIEF.md' in sk1_p_['prompt']
    assert not any('search.py *' in v_ for v_ in sk1_p_['verktyg']), 'search.py med fritt argument vidgade skrivgränsen (G12)'
    k5f_ = kd.las_status(sl_sk, 'k05')['forsok_tider']
    assert [x_['utfall'] for x_ in k5f_][:1] == ['avbruten'] and (kd.kdir(sl_sk, 'k05') / 'forsok-1' / 'RIKTNING.md').is_file() and (kd.kdir(sl_sk, 'k05') / 'forsok-1' / 'varv').is_dir(), k5f_

    # --- tiderna och redovisningen ---
    t_sk = st_sk['tider']
    assert all(t_sk.get(k_) for k_ in ('start', 'forskning', 'plan', 'forsta_valbara', 'klar')) and t_sk['start'] <= t_sk['forsta_valbara'] <= t_sk['klar'], t_sk
    rd_sk = kd.redovisa(sl_sk, st_sk).read_text()
    for krav_ in ('## Tiderna', 'väntan till första valbara skissen', '## Ofullständiga och fallna', 'k04', 'ingen modell har rangordnat skisserna', 'Utkast och platshållare',
                  'METOD-skiss.md', 'siffror i texten som inte finns i underlag: 25'.replace('underlag: 25', 'underlaget: 25'), '1 + 2 (omförsök)', '1 (tiden slut)',
                  '## Kompetensernas arbete', 'Planprövningen'):
        assert krav_ in rd_sk, krav_
    # --- vyn: neutral, med bristerna; ingen granskning ---
    blind_sk = kd.sammanstall(sl_sk)
    assert all('kritik' not in k_ and 'titel' not in k_ for k_ in blind_sk) and any(k_['brister'] for k_ in blind_sk if k_['id'] == 'k01')
    dash.UNDERLAG, dash.KUNDER, dash.ROOT = sk_u, sk_k, tmp
    (kd.rot(sl_sk) / 'STATUS.json').write_text(json.dumps(dict(st_sk, kandidatflode=True)))
    vy_sk = dash.prototyp(sl_sk)
    assert vy_sk['kandidatlage'] == 'skiss' and vy_sk['tider']['forsta_valbara'] and not vy_sk['domd'] and vy_sk['redovisning_md'] is None
    vytext_ = (ROOT / 'dashboard' / 'index.html').read_text()
    assert 'En intern granskare ser skisserna när tiden räcker' in vytext_ and 'ingen modell har rangordnat förslagen' in vytext_ and 'ingen modell har bedömt' not in vytext_
    # --- den interna granskaren och skaparens svar (granskningen av designintegrationen 2026-10-06), med en falsk klocka ---
    class KlockaGk:
        def __init__(self):
            self.t = 0.0

        def __getattr__(self, n_):
            return getattr(time, n_)

        def monotonic(self):
            return self.t
    kl_gk = KlockaGk()
    spara_gk = (kd.time, at_pt.session, kd.FRIST_SKISS, sk.komplettera)
    GK, sess_gk = {}, []
    RIKT_SVAR = ('Huvudreferens: Xref — kompositionen\n\n## Idén\n\nKöket i centrum.\n\n## Kvarvarande svagheter\n\nRubriken är tung i 390.\n'
                 'Besökaren granskar tidigare arbeten innan kontakt.\nOmdömena från kunderna lyfts in.\n'
                 'Granskaren rekommenderade att förkasta riktningen.\nEfter kritiken behöll jag riktningen.\nBedömningen att riktningen var generisk.\n'
                 '\n### Granskningen\n\nGRANSKNINGENS ORD: generisk\n\n## Svar på granskningen\n\nJag står kvar.\n')

    def sess_gk_(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), slug=None, vid_start=None, blind=None):
        sess_gk.append({'prompt': prompt, 'schema': schema, 'nekas': list(nekas), 'frist': frist, 'ut': Path(ut).name, 'blind': blind})
        pages_ = kd.ksajt(sl_sk, 'k02') / 'src' / 'pages'
        so = None
        if schema is kd.SKISSKRITIK_SCHEMA:
            kl_gk.t += GK['kritik']
            if GK.get('kritik_stopp'):
                at_pt.STOPP.set()
                raise RuntimeError('sessionen föll (kod -9, None): None')
            so = {'storsta_problem': 'rubriken tar över första vyn', 'synliga_problem': ['bilden är liten i 390'], 'generiskt': True,
                  'rekommendation': 'förkasta', 'motivering': 'formen kunde vara vilken hantverkare som helst'}
        elif 'En kritisk granskare har sett' in prompt:  # skaparens svar på granskningen
            kl_gk.t += GK['svar']
            (kd.kdir(sl_sk, 'k02') / 'RIKTNING.md').write_text(RIKT_SVAR)
            (pages_ / 'index.astro').write_text('TRASIG efter svaret' if GK.get('svar_trasig') else '<h1>Skiss</h1><p>Köket halvvägs.</p>'
                                                if GK.get('svar_tidsgrans') else '<h1>Skiss</h1><p>Köket efter svaret.</p>')
            if GK.get('svar_tidsgrans'):
                raise subprocess.TimeoutExpired('claude', frist)
        else:  # skaparen
            kl_gk.t += GK['skapare']
            (pages_ / 'index.astro').write_text('<h1>Skiss</h1><p>Köket före svaret.</p>')
            (kd.kdir(sl_sk, 'k02') / 'RIKTNING.md').write_text('Huvudreferens: Xref — kompositionen\n\n## Idén\n\nKöket i centrum.\n')
            vd_ = kd.kdir(sl_sk, 'k02') / 'varv' / 'start' / 'varv-01'
            vd_.mkdir(parents=True, exist_ok=True)
            for b_ in ('390', '1280', '1440'):  # ett helt varv: första vyn och hela sidan (forhandsvisa.LAS), som hela PNG-huvuden
                for v_ in ('forsta', 'hela'):
                    (vd_ / ('vy-%s-%s.png' % (b_, v_))).write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR' + int(b_).to_bytes(4, 'big') + (844).to_bytes(4, 'big'))
            if GK.get('begar') and 'Researchen du begärde' not in prompt:
                (kd.kdir(sl_sk, 'k02') / sk.KOMPLETTERING).write_text(json.dumps({'varfor': 'saknar kök i närbild'}))
            if GK.get('skapare_tidsgrans') and 'Förra sessionen nådde sin tidsgräns' not in prompt:
                raise subprocess.TimeoutExpired('claude', frist)
        sid_gk = 's'
        if GK.get('kvitto_sid') and schema is None and 'En kritisk granskare har sett' not in prompt:  # R03: skaparen läser hela kärnan
            sid_gk = transkript_kd([('Read', {'file_path': f_}, False) for f_ in kd.kompetens.lasfiler('skapa')]
                                   + [('Write', {'file_path': kd.rel(pages_ / 'index.astro')}, False)])
        elif GK.get('kvitto_sid') and 'En kritisk granskare har sett' in prompt:  # R03: svarets transkript saknas
            sid_gk = str(uuid_kd.uuid4())
        svar_ = {'structured_output': so, 'num_turns': 7, 'duration_ms': 90000, 'total_cost_usd': 0.3, 'session_id': sid_gk}
        Path(ut).write_text(json.dumps(svar_))
        return svar_

    def komplettera_gk(*a, **k_):
        kl_gk.t += GK['research']
        (kd.kdir(sl_sk, 'k02') / sk.KOMPLETTERING).unlink()
        return {'tid': '2026-10-06T12:00:00Z', 'begaran': 'KOMPLETTERING.json', 'varfor': 'RESEARCHENS SVAR: kök i närbild'}

    # skaparens del av försöket: tiden före granskarens reserv (FRIST_SKISSKRITIK och SVAR_MIN), räknad ur konstanterna
    # så att provet följer en uppmätt frist (BESLUT.md, tillägget 2026-10-07)
    BAS_GK = 2700 - kd.FOTO_RESERV - kd.SKISSKRITIK_RESERV

    def omgang_gk(**gk_):
        GK.clear(); GK.update(dict({'skapare': BAS_GK - 120, 'kritik': 300, 'svar': 300, 'research': 0}, **gk_))
        sess_gk.clear()
        kd.satt_status(sl_sk, 'k02', 'klar', 'prov', ta_bort=('skisskritik',))
        kl_gk.t = 0.0
        return kd.skissa(sl_sk, 'k02')

    kd.time, at_pt.session, kd.FRIST_SKISS, sk.komplettera = kl_gk, sess_gk_, 2700, komplettera_gk
    try:
        # (1) granskaren ser bara bilderna, skaparen svarar under en egen rubrik, och vyn visar aldrig granskningen före beslutet
        omgang_gk()
        kr_gk = [x_ for x_ in sess_gk if x_['schema'] is kd.SKISSKRITIK_SCHEMA]
        svar_gk = [x_ for x_ in sess_gk if 'En kritisk granskare har sett' in x_['prompt']]
        assert len(kr_gk) == 1 and len(svar_gk) == 1, [x_['ut'] for x_ in sess_gk]
        assert 'Read(./%s)' % kd.rel(kd.kdir(sl_sk, 'k02') / 'RIKTNING.md') in kr_gk[0]['nekas'], kr_gk[0]['nekas']
        assert 'Read(./%s/**)' % kd.rel(kd.ksajt(sl_sk, 'k02').parent) in kr_gk[0]['nekas'], 'skissens kod och DESIGN.md nekas granskaren'
        assert 'vy-390-forsta.png' in kr_gk[0]['prompt'] and 'Köket i centrum' not in kr_gk[0]['prompt'], 'granskaren får aldrig skaparens text'
        assert 'det största problemet: rubriken tar över första vyn' in svar_gk[0]['prompt'] and 'rubriken "Svar på granskningen"' in svar_gk[0]['prompt']
        assert 'Steg 0 görs i varje session' in svar_gk[0]['prompt'] and 'Detta är en ny session' in svar_gk[0]['prompt'] and svar_gk[0]['frist'] >= kd.SVAR_MIN  # K06
        assert 'i skissens första session' not in svar_gk[0]['prompt'] and 'Rollerna i ' in svar_gk[0]['prompt'], 'svaret på granskningen är en ny session (K06)'
        assert 'Läs varje rolls kärna HEL' not in svar_gk[0]['prompt'], 'svaret läser inte om hela kärnan'
        st_gk = kd.las_status(sl_sk, 'k02')
        assert st_gk['status'] == 'klar' and st_gk['skisskritik']['gjord'] and st_gk['skisskritik']['session']['num_turns'] == 7, st_gk.get('skisskritik')
        assert (kd.kdir(sl_sk, 'k02') / 'SKISSKRITIK.json').is_file()
        sv_gk = {r_['rubrik']: r_['avsnitt'] for r_ in kd.kort_redovisning(sl_sk, 'k02')}['Kvarvarande svagheter']
        assert all(x_ in sv_gk for x_ in ('Rubriken är tung i 390.', 'Besökaren granskar tidigare arbeten', 'Omdömena från kunderna')), sv_gk
        assert not any(x_ in sv_gk for x_ in ('Granskaren', 'GRANSKNINGENS ORD', 'förkasta', 'kritiken', 'generisk', 'Jag står kvar', 'interna granskningen')), sv_gk
        assert not (kd.kdir(sl_sk, 'k02') / 'fore-svaret').exists(), 'kopian av projektet ligger inte kvar'
        # efter ägarens första beslut syns granskarens omdöme; före aldrig
        spara_domd_gk = kd.domd
        kd.domd = lambda s_: True
        try:
            efter_gk = next(k_ for k_ in kd.sammanstall(sl_sk) if k_['id'] == 'k02')['skisskritik']
        finally:
            kd.domd = spara_domd_gk
        # Svaret ändrade koden efter kritiken: historiken visas efter ägarbeslutet,
        # men får inte framställas som en aktuell bedömning av de nya bilderna.
        assert not efter_gk['gjord'] and not efter_gk['aktuell'] and efter_gk['historiskt_gjord'] and efter_gk['status'] == 'historisk', efter_gk
        assert efter_gk['andrad_efter_bedomningen'] and efter_gk['rekommendation'] == 'förkasta' and efter_gk['storsta_problem'] == 'rubriken tar över första vyn', efter_gk
        assert 'skisskritik' not in next(k_ for k_ in kd.sammanstall(sl_sk) if k_['id'] == 'k02')
        blind_gk = next(k_ for k_ in kd.sammanstall(sl_sk) if k_['id'] == 'k02')
        assert 'GRANSKNINGENS ORD' not in json.dumps(blind_gk, ensure_ascii=False) and 'förkasta' not in json.dumps(blind_gk, ensure_ascii=False)
        # (2) skaparen nådde tidsgränsen: ingen granskning och inget svar
        omgang_gk(skapare_tidsgrans=True)
        skapare2_gk = [x_ for x_ in sess_gk if x_['schema'] is None]
        assert len(skapare2_gk) == 2 and 'Förra sessionen nådde sin tidsgräns' in skapare2_gk[1]['prompt'], [x_['ut'] for x_ in sess_gk]
        assert skapare2_gk[1]['frist'] >= kd.SKISSKRITIK_RESERV - 60, 'fortsättningen får granskningens reserv: %s' % skapare2_gk[1]['frist']
        assert not any(x_['schema'] is kd.SKISSKRITIK_SCHEMA for x_ in sess_gk) and 'fortsättning' in kd.las_status(sl_sk, 'k02')['skisskritik']['skal']
        # (3) granskningen görs bara när svaret hinner; efter den står det kvar för lite tid: inget svar
        omgang_gk(skapare=BAS_GK + 200)
        assert not any(x_['schema'] is kd.SKISSKRITIK_SCHEMA for x_ in sess_gk), 'granskningen görs inte när svaret inte hinner'
        omgang_gk(kritik=kd.FRIST_SKISSKRITIK + 220)
        assert [x_['schema'] is kd.SKISSKRITIK_SCHEMA for x_ in sess_gk].count(True) == 1 and not any('En kritisk granskare har sett' in x_['prompt'] for x_ in sess_gk)
        assert kd.las_status(sl_sk, 'k02')['skisskritik']['tid_kvar'] < kd.SVAR_MIN
        # (4) ett stopp under granskningen går igenom: försöket står kvar under arbete
        try:
            omgang_gk(kritik_stopp=True)
            raise AssertionError('stoppet under granskningen skulle gå igenom')
        except at_pt.Stoppad:
            pass
        finally:
            at_pt.STOPP.clear()
        assert kd.las_status(sl_sk, 'k02')['status'] == 'under_arbete'
        # (5) svaret bryter bygget: skissen före svaret återställs och fotograferas, så att ägaren har en skiss att bedöma
        omgang_gk(svar_trasig=True)
        st5_gk = kd.las_status(sl_sk, 'k02')
        assert st5_gk['status'] == 'klar' and st5_gk['skisskritik'].get('svaret_aterstallt'), (st5_gk['status'], st5_gk.get('skisskritik'), st5_gk.get('hinder'))
        assert (kd.ksajt(sl_sk, 'k02') / 'src' / 'pages' / 'index.astro').read_text() == '<h1>Skiss</h1><p>Köket före svaret.</p>'
        assert 'Svar på granskningen' not in (kd.kdir(sl_sk, 'k02') / 'RIKTNING.md').read_text()
        assert (kd.ksajt(sl_sk, 'k02') / 'node_modules').exists(), 'återställningen rör aldrig node_modules'
        omgang_gk(svar_tidsgrans=True)
        st5b_gk = kd.las_status(sl_sk, 'k02')
        assert st5b_gk['status'] == 'klar' and st5b_gk['skisskritik'].get('svaret_aterstallt') and 'räckte inte' in st5b_gk['skisskritik']['svarets_skal'], st5b_gk.get('skisskritik')
        assert (kd.ksajt(sl_sk, 'k02') / 'src' / 'pages' / 'index.astro').read_text() == '<h1>Skiss</h1><p>Köket före svaret.</p>'
        assert not st5b_gk['forsok_tider'][-1]['tidsgrans'], 'svarets tidsgräns gör inte försöket till en tidsgräns: skissen före svaret är hel'
        spara_kor_gk, fall_gk = prova.kor, [True]

        def kor_en_gang_fel(cmd, cwd=None, timeout=900):
            if fall_gk[0] and any(str(x_).endswith('inspektera.mjs') for x_ in cmd):
                fall_gk[0] = False
                return 1, 'webbläsaren föll'  # inga bilder: fotograferingen gav inte bilderna
            return spara_kor_gk(cmd, cwd=cwd, timeout=timeout)
        prova.kor = kor_en_gang_fel
        try:
            omgang_gk()
        finally:
            prova.kor = spara_kor_gk
        st5c_gk = kd.las_status(sl_sk, 'k02')
        assert st5c_gk['status'] == 'klar' and not st5c_gk['skisskritik'].get('svaret_aterstallt'), st5c_gk.get('skisskritik')
        assert (kd.ksajt(sl_sk, 'k02') / 'src' / 'pages' / 'index.astro').read_text() == '<h1>Skiss</h1><p>Köket efter svaret.</p>', 'svaret behålls'
        # (6) research på begäran går före granskningen när båda inte ryms: skaparen får resultatet, ingen granskning
        omgang_gk(skapare=BAS_GK - 620, research=600, begar=True)
        skapare_gk = [x_ for x_ in sess_gk if x_['schema'] is None and 'En kritisk granskare har sett' not in x_['prompt']]
        assert len(skapare_gk) == 2 and 'RESEARCHENS SVAR' in skapare_gk[1]['prompt'], [x_['ut'] for x_ in sess_gk]
        assert not any(x_['schema'] is kd.SKISSKRITIK_SCHEMA for x_ in sess_gk) and 'researchen' in kd.las_status(sl_sk, 'k02')['skisskritik']['skal']
        # (7) R03 (GR-20261008-06af6ff-omgranskning-codex): skapare med hela kärnan och ett svar vars transkript saknas, genom skissens
        # riktiga statusutgång: det sparade kvittot är ofullständigt med den saknade sessionen, kärnan står som inte observerad
        # (aldrig "läst hel"), och sammanställningen som dashboarden läser bär samma fält
        omgang_gk(kvitto_sid=True)
        rec_r03 = kd.las_status(sl_sk, 'k02')['kompetens']['skiss:skapa']
        kv_r03 = rec_r03['kvitto']
        assert kv_r03.get('ofullstandig') is True and kv_r03['sessioner']['forvantade'] == 2 and kv_r03['sessioner']['sedda'] == 1, kv_r03
        assert kv_r03['sessioner']['saknade'][0]['skal'] == 'transkriptet saknas' and len(kv_r03['per_session']) == 1 and kv_r03['per_session'][0]['saknas'] == [], kv_r03
        assert 'fore_forsta_andring' in kv_r03 and 'tillstand' in kv_r03, sorted(kv_r03)
        assert rec_r03['karnan_last'] is None and rec_r03.get('karnan_fore_andring') is None, 'ett saknat transkript gav ett komplett läskvitto (R03): %s' % rec_r03.get('karnan_last')
        spara_domd_r03 = kd.domd
        kd.domd = lambda slug: True  # efter ägarens första beslut visar vyn kompetensens poster (före beslutet bara läget)
        try:
            vy_r03 = next(k_ for k_ in kd.sammanstall(sl_sk) if k_['id'] == 'k02')
        finally:
            kd.domd = spara_domd_r03
        kort_r03 = next(r_ for r_ in vy_r03.get('kompetens') or [] if r_.get('nyckel') == 'skiss:skapa')
        assert kort_r03['kvitto'].get('ofullstandig') is True and kort_r03['kvitto'].get('per_session') is not None, kort_r03.get('kvitto')
        assert vy_r03['kompetenspass'].get('skapa') is None, vy_r03.get('kompetenspass')
        print('R03 skissens sparade kvitto ok')
    finally:
        kd.time, at_pt.session, kd.FRIST_SKISS, sk.komplettera = spara_gk
finally:
    at_pt.UNDERLAG, at_pt.KUNDER, at_pt.session, at_pt.ROOT = spara_at_sk
    for n_, v_ in spara_sk.items():
        setattr(kd, n_, v_)
    prova.bygg_inom_grans, prova.kor, prova.Server = spara_prova_sk
    sk.komplettera = spara_komp_sk
    dash.UNDERLAG, dash.KUNDER, dash.ROOT = spara_dash_sk
    bk_pt.ROOT = spara_bk_sk
print('skissläget ok')

# ---------------------------------------------------------------- kompetenskedjan och granskning 3 (ägarens ord 2026-10-05 18:15Z)
import kompetens as kp_k3  # noqa: E402
import nastlad as nl_k3  # noqa: E402
import signal as sig_k3  # noqa: E402
assert kp_k3.prova() == [], kp_k3.prova()
assert '.claude/skills/impeccable/reference/critique.md' in kp_k3.lasfiler('granskning') and '.claude/skills/impeccable/reference/craft-floor.md' in kp_k3.lasfiler('skapa')
assert set(kp_k3.PASS) == {p_ for x_ in kp_k3.tolka().values() for p_ in x_['pass']}, 'varje pass har en roll'
# Codex punkt 7: kärnan är en sammanhängande metod; stilvarianterna och recepten är alternativ att välja
assert '.claude/skills/taste-soft/SKILL.md' not in kp_k3.lasfiler('skapa') and '.claude/skills/taste-soft/SKILL.md' in kp_k3.valbara('skapa')
assert '.claude/skills/refero-design/SKILL.md' in kp_k3.lasfiler('skapa') and '.claude/skills/hallmark/references/macrostructures.md' in kp_k3.valbara('planera')
assert kp_k3.storlek(kp_k3.lasfiler('skapa')) < 160000, kp_k3.storlek(kp_k3.lasfiler('skapa'))
v_k3 = kp_k3.verktyg('skapa', 'x', 'k01')
assert 'Skill' in v_k3 and not any(x_.startswith('mcp__') for x_ in v_k3) and any('kontroller/uxsok.py' in x_ for x_ in v_k3)
v_gr_k3 = kp_k3.verktyg('granskning', 'x', 'k01')
assert 'Bash(.venv/bin/python kontroller/detektor.py x --kandidat k01)' in v_gr_k3 and not any('detektor' in x_ and x_.endswith('*)') for x_ in v_gr_k3), 'detektorn bara för den egna kandidaten (G12)'
assert not any('design.py' in x_ for x_ in kp_k3.verktyg('fordjupa', 'x')), 'utan kandidat inget designverktyg'
assert any('design.py x --kandidat k01 --skriv' in x_ for x_ in kp_k3.verktyg('fordjupa', 'x', 'k01'))
# Codex punkt 1: Avgörandena förbjuder inte det kompetensblocken ger; samma regel styr dokumentation, uppdrag och behörighet
karta_k3 = (ROOT / 'kunskap' / 'metodkarta.md').read_text()
avg_k3 = md_kd.tolka(karta_k3)['Avgöranden']['prosa']
assert 'Inga skillskript' not in avg_k3 and not re.search(r'\bInga\b[^.]*\bMCP\b', avg_k3) and 'inget Skill-verktyg' not in karta_k3, 'Avgörandena säger emot verktygen'
assert 'läses inte i förväg' not in karta_k3 and 'Minst tre förhandsvarv är en arbetsregel' not in karta_k3, 'inga frivilliga utdrag och inget varvkrav i skissen'
# uxsok: läsande; de skrivande flaggorna nekas (G12)
for x_ in ('--persist', '--force'):
    r_ux = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'uxsok.py'), 'x', x_], capture_output=True, text=True)
    assert r_ux.returncode == 2 and 'unrecognized' in r_ux.stderr, (x_, r_ux.returncode)
# sessionerna: med en slug alla skills och flödets tre MCP:er i strikt läge med kundvakten; utan slug inga MCP:er
a_k3 = at_pt.session_args(['Read', 'Write(./x/**)'], None, 10, 'm', 'high', (), 'sk-prov')
assert '--strict-mcp-config' in a_k3 and '--settings' in a_k3 and 'kundvakt.py' in a_k3[a_k3.index('--settings') + 1] and '--disable-slash-commands' not in a_k3
assert 'Skill' in a_k3[a_k3.index('--tools') + 1].split(',') and 'mcp__refero__.*' in a_k3[a_k3.index('--settings') + 1]
assert 'exit 2' in a_k3[a_k3.index('--settings') + 1], 'en krok som inte kan köras stoppar anropet'
assert '--strict-mcp-config' in at_pt.session_args(['Read'], None, 10, 'm', 'high', ())
spara_ref_k3 = at_pt.REFERO_ENV
(tmp / 'k3-refero.env').write_text('REFERO_MCP_TOKEN=provnyckel\n')
at_pt.REFERO_ENV = tmp / 'k3-refero.env'
spara_miljo_k3 = os.environ.get('REFERO_MCP_TOKEN')
os.environ['REFERO_MCP_TOKEN'] = 'provnyckel'
try:
    assert 'REFERO_MCP_TOKEN' not in at_pt.session_miljo('sk-prov') and 'REFERO_MCP_TOKEN' not in at_pt.session_miljo(None), 'nyckeln når aldrig Bash (G15)'
    # E1: Referos konfiguration till strikt läge bär nyckeln i en fil bredvid nyckelfilen (0600), aldrig i argumenten;
    # mallen kontroller/mcp/refero.json läses ur ateljéns rot, som här är provets
    (at_pt.ROOT / 'kontroller' / 'mcp').mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'kontroller' / 'mcp' / 'refero.json', at_pt.ROOT / 'kontroller' / 'mcp' / 'refero.json')
    f_ref = at_pt.refero_mcp_fil()
    assert f_ref == str(tmp / 'refero-mcp.json') and (os.stat(f_ref).st_mode & 0o777) == 0o600, (f_ref, oct(os.stat(f_ref).st_mode))
    assert json.loads(Path(f_ref).read_text())['mcpServers']['refero']['headers']['Authorization'] == 'Bearer provnyckel'
    a_e1 = at_pt.session_args(['Read'], None, 10, 'm', 'high', (), 'sk-prov')
    assert 'provnyckel' not in ' '.join(a_e1) and a_e1[a_e1.index('--mcp-config') + 1] == f_ref, 'nyckeln står aldrig i argumenten'
    (tmp / 'k3-refero.env').write_text('REFERO_MCP_TOKEN=nynyckel\n')
    assert 'Bearer nynyckel' in Path(at_pt.refero_mcp_fil()).read_text(), 'förnyas när nyckeln ändrats'
    at_pt.REFERO_ENV = tmp / 'k3-saknas' / 'refero.env'
    assert at_pt.refero_mcp_fil() == str(at_pt.ROOT / 'kontroller' / 'mcp' / 'refero.json'), 'utan nyckel ges mallen som den är'
finally:
    at_pt.REFERO_ENV = spara_ref_k3
    os.environ.pop('REFERO_MCP_TOKEN', None) if spara_miljo_k3 is None else os.environ.__setitem__('REFERO_MCP_TOKEN', spara_miljo_k3)
# kundvakten: tillåter ett rent anrop uttryckligen, stoppar kundens uppgifter i alla former, stänger vid fel (G3, G14)
(tmp / 'k3-u' / 'k3-kund').mkdir(parents=True)
(tmp / 'k3-u' / 'k3-kund' / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Vaktfirman Bygg AB', 'adress': {'ort': 'Kalix', 'gata': 'Lärkstigen 12'}, 'rackvidd': {'orter': ['Älvsbyn']},
                                                                     'kategorier': ['Byggfirma'], 'kontaktvagar': [{'typ': 'telefon', 'varde': '070-111 22 33'}]}))
for in_, rc_ in (({'tool_name': 'mcp__refero__refero_search_styles', 'tool_input': {'query': 'Vaktfirman homepage'}}, 2),
                 # Mobbins search_screens med mode standard, så att numret prövas och inte lägesregeln (GR-20261007-r102-om, B3)
                 ({'tool_name': 'mcp__mobbin__search_screens', 'tool_input': {'query': 'builder site', 'task_intent': 'contact 0701112233', 'mode': 'standard'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'kalixföretag hantverk'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'Älvsbyn builders'}}, 2),
                 ({'tool_name': 'mcp__mobbin__search_flows', 'tool_input': {'query': 'ring +46 70 111 22 33'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'V a k t f i r m a n'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'byggfirma portfolio'}}, 0),
                 ({'tool_name': 'mcp__refero__refero_get_style', 'tool_input': {'style_id': '00452350-e8c3-4d5a-9b1c-123456789012'}}, 0),
                 ({'tool_name': 'mcp__refero__refero_get_flow', 'tool_input': {'flow_ids': [1234567, 7654321]}}, 0),
                 ({'tool_name': 'mcp__refero__refero_get_screen_image', 'tool_input': {'image_url': 'https://images.refero.design/s/123456789.jpg'}}, 0),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'see https://annan.exempel/x'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_styles', 'tool_input': {'query': 'warm craft builder site'}}, 0),
                 # den oberoende granskningen 2026-10-05: bara flödets egna verktyg; nycklar, gatan, telefonens slut och id-fält prövas
                 ({'tool_name': 'mcp__claude_ai_Trybloom__delete_brand', 'tool_input': {'brand_id': 'b1'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_delete_everything', 'tool_input': {'query': 'x'}}, 2),
                 ({'tool_name': 'mcp__mobbin__generate_image', 'tool_input': {'prompt': 'warm craft'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_styles', 'tool_input': {'Vaktfirman': 'builder'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'lärkstigen workshop'}}, 2),
                 ({'tool_name': 'mcp__mobbin__search_screens', 'tool_input': {'query': 'ring 11 22 33', 'mode': 'standard'}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'builder', 'limit': 701112233}}, 2),
                 ({'tool_name': 'mcp__refero__refero_get_screen', 'tool_input': {'screen_id': 701112233}}, 2),
                 ({'tool_name': 'mcp__refero__refero_search_screens', 'tool_input': {'query': 'builder', 'limit': 20, 'page': 2}}, 0)):
    r_k3 = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'kundvakt.py'), 'k3-kund', str(tmp / 'k3-u')], input=json.dumps(in_), capture_output=True, text=True)
    assert r_k3.returncode == rc_, (in_, r_k3.returncode, r_k3.stderr)
    if rc_ == 0:
        assert json.loads(r_k3.stdout)['hookSpecificOutput']['permissionDecision'] == 'allow', r_k3.stdout
r_k3 = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'kundvakt.py'), 'k3-kund', str(tmp / 'k3-u')], input='inte json', capture_output=True, text=True)
assert r_k3.returncode == 2 and 'stoppas' in r_k3.stderr and not r_k3.stdout.strip(), 'vakten stänger vid fel och tillåter inget'
r_k3 = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'kundvakt.py'), 'saknas', str(tmp / 'k3-u')], input=json.dumps({'tool_input': {'query': 'x'}}), capture_output=True, text=True)
assert r_k3.returncode == 2, 'utan kundens uppgifter stoppas anropet'
r_k3 = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'kundvakt.py'), 'k3-kund', str(tmp / 'k3-u')], input='', capture_output=True, text=True)
assert r_k3.returncode == 2 and not r_k3.stdout.strip(), 'en tom indata stoppas'
# referenstjänsternas sessioner: kundvakten öppnar tjänstens verktyg, och sessionen kan inte läsa filer (granskningen 2026-10-05, fynd 6)
import referenstjanster as rt_k3
spara_run_k3 = rt_k3.subprocess.run
spara_env_k3 = rt_k3.REFERO_ENV
rt_k3.REFERO_ENV = tmp / 'refero-provnyckel.txt'  # attrappen läser aldrig användarens hemligheter, också med tomt HOME
rt_k3.REFERO_ENV.write_text('REFERO_MCP_TOKEN=syntetisk-provnyckel\n')
fangat_k3 = {}
rt_k3.subprocess.run = lambda args, **kw: (fangat_k3.update(args=args) or subprocess.CompletedProcess(args, 0, b'', b''))
try:
    logg_k3 = tmp / 'k3-u' / 'k3-kund' / 'referenser' / 'tjanster' / 'refero' / 'session-x.jsonl'
    logg_k3.parent.mkdir(parents=True)
    rt_k3.kor_session('refero', 'p', logg_k3, 'm')
    a_rt = fangat_k3['args']
    assert not [x for x in a_rt if x.startswith('mcp__')], 'tjänstens verktyg står aldrig i tillåtelselistan'
    inst_rt = json.loads(a_rt[a_rt.index('--settings') + 1])['hooks']['PreToolUse'][0]
    assert 'k3-kund' in inst_rt['hooks'][0]['command'] and str(tmp / 'k3-u') in inst_rt['hooks'][0]['command'] and 'exit 2' in inst_rt['hooks'][0]['command']
    neka_rt = a_rt[a_rt.index('--disallowedTools') + 1:]
    assert {'Read', 'Glob', 'Grep', 'Bash'} <= set(neka_rt), neka_rt
    try:
        rt_k3.kor_session('refero', 'p', tmp / 'session-utanfor.jsonl', 'm')
        assert False, 'en logg utanför kundens tjänstekatalog ger ingen session'
    except ValueError:
        pass
finally:
    rt_k3.subprocess.run = spara_run_k3
    rt_k3.REFERO_ENV = spara_env_k3
# passen efter fördjupningen (Codex punkt 8–9; granskning 4, G1, G4, G5, G7): tre delar, omförsök, återställning
sl_kp = 'kp-prov'
spara_kp = {n_: getattr(kd, n_) for n_ in ('fotografera', 'aterstall_och_fotografera', 'bevara_version', 'designkontroll')}
spara_at_kp = (at_pt.session, at_pt.UNDERLAG, at_pt.KUNDER)
at_pt.UNDERLAG, at_pt.KUNDER = tmp / 'kp-u', tmp / 'kp-k'
d_kp = kd.kdir(sl_kp, 'k01')
(d_kp / 'bilder' / 'start').mkdir(parents=True)
for n_ in kd.PASSBILDER:
    (d_kp / 'bilder' / 'start' / n_).write_bytes(b'png')
foto_kp, ater_kp, prompt_kp, las_kp = {'status': 'klar', 'version': 'v2', 'axe': {'allvarliga': 0}}, [], [], {'saknas_forsta': False}

def foto_kp_(slug, kid, skiss=None):
    return kd.satt_status(slug, kid, foto_kp['status'], 'bygget föll' if foto_kp['status'] != 'klar' else 'fotograferad', version=foto_kp['version'], axe=foto_kp['axe'])

def ater_kp_(slug, kid, v):
    ater_kp.append(v)
    if foto_kp.get('ater_fel'):
        raise RuntimeError('bygget föll vid återställningen')
    return kd.satt_status(slug, kid, 'klar', 'återställd', version=v, axe={'allvarliga': 0})

def sess_kp_(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None):
    prompt_kp.append(prompt)
    pass_ = next(k_ for k_, n_ in kd.kompetens.PASSNAMN.items() if 'specialisten för %s' % n_ in prompt)
    filer_ = kd.kompetens.lasfiler(pass_)
    if las_kp['saknas_forsta'] and 'Förra försöket saknade:' not in prompt:
        filer_ = filer_[1:]
    elif las_kp['saknas_forsta'] and las_kp.get('bara_saknade'):  # omförsöket läser bara det som saknades: den nya sessionen saknar resten (R02)
        filer_ = filer_[:1]
    so = {'kod_andrad': [{'skill': 'emil-animate', 'vad': 'menyns övergång', 'var': 'sidhuvudet', 'varfor': 'syfte'}],
          'beteende_provat': [{'vad': 'menyn', 'hur': 'forhandsvisa --meny', 'resultat': 'öppnas', 'bild': kd.rel(d_kp / 'bilder' / 'start' / 'vy-390-forsta.png')}],
          'visuell_bedomning': {'fore': 'a', 'efter': 'b', 'omdome': 'battre', 'skal': 'tydligare'}, 'ingen_andring': '', 'valda': [], 'passade_inte': [], 'kvarstar': []}
    # ett observerat verktygsanrop med resultat (förhandsvisningen) krävs för genomfört (C4:s rest); det nekade MCP-anropet räknas inte (G7)
    sid_ = transkript_kd([('Read', {'file_path': f_}, False) for f_ in filer_] + [('mcp__refero__refero_search_screens', {'query': 'x'}, True),
                          ('Bash', {'command': '.venv/bin/python -B kontroller/forhandsvisa.py %s k01 --meny' % sl_kp}, False)])
    svar_ = {'structured_output': so, 'session_id': sid_}
    Path(ut).write_text(json.dumps(svar_))
    return svar_
kd.fotografera, kd.aterstall_och_fotografera, kd.bevara_version = foto_kp_, ater_kp_, (lambda *a_, **k_: None)
kd.designkontroll = lambda slug, kid: {'ok': True, 'fel': []}
at_pt.session = sess_kp_
try:
    dom_kp = {'tid': '2026-10-05T20:00:00Z', 'text': 'BEHÅLL DEN MÖRKA PALETTEN'}
    kd.satt_status(sl_kp, 'k01', 'forfinad', 'förfinad', version='v1', axe={'allvarliga': 0})
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'rorelse', 'fordjupa:a', dom_kp)
    r_kp = st_kp['kompetens']['fordjupa:a:rorelse']
    assert r_kp['genomford'] and r_kp['kod_andrad']['andrad'] and r_kp['beteende_provat'][0]['bild_finns'] and r_kp['visuell_bedomning']['omdome'] == 'battre', r_kp
    assert r_kp['kvitto']['mcp_anrop'] == {}, 'ett nekat MCP-anrop räknas inte (G7)'
    assert st_kp['status'] == 'forfinad' and 'pass_pagar' not in st_kp and not ater_kp
    assert 'BEHÅLL DEN MÖRKA PALETTEN' in prompt_kp[-1] and 'kunskap/designregler.md' in prompt_kp[-1] and 'METOD-forfina.md' in prompt_kp[-1], 'passet får domen, reglerna och metoden (G1)'
    assert '--tillstand tangentbord,reflow,reducerad' in prompt_kp[-1] and 'beteende_provat' in prompt_kp[-1]
    # ett pass som bryter sidan återställs till versionen före, och kandidaten står kvar som förfinad
    foto_kp.update(status='ofullstandig', version='v3')
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'granskning', 'fordjupa:a', dom_kp)
    assert ater_kp == ['v2'] and st_kp['kompetens']['fordjupa:a:granskning']['aterstalld'] and kd.las_status(sl_kp, 'k01')['status'] == 'forfinad', st_kp
    # fler allvarliga axe-fynd än före: återställs också
    foto_kp.update(status='klar', version='v4', axe={'allvarliga': 3})
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'rorelse', 'fordjupa:b', dom_kp)
    assert ater_kp[-1] == 'v2' and 'axe' in st_kp['kompetens']['fordjupa:b:rorelse']['aterstalld'], st_kp['kompetens']['fordjupa:b:rorelse']
    # en återställning som faller: kandidaten blir ofullständig, aldrig klar med en trasig sida (G5)
    foto_kp.update(status='ofullstandig', version='v5', ater_fel=True)
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'granskning', 'fordjupa:b', dom_kp)
    assert st_kp['status'] == 'ofullstandig' and 'återställningen föll' in st_kp['skal'], st_kp
    # ett avbrutet pass tas upp igen: versionen före återställs först (G4); en främmande pid avslutas aldrig (G6)
    foto_kp.update(status='klar', version='v6', axe={'allvarliga': 0}, ater_fel=False)
    kd.satt_status(sl_kp, 'k01', 'forfinad', 'förfinad', version='v5b', pass_pagar={'nyckel': 'fordjupa:c:rorelse', 'fore': 'v5b', 'status': 'forfinad'},
                   session_pid=os.getpid())
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'rorelse', 'fordjupa:c', dom_kp)
    assert ater_kp[-1] == 'v5b' and st_kp['kompetens']['fordjupa:c:rorelse']['genomford'] and 'pass_pagar' not in st_kp, st_kp
    # ett pass som inte läste hela kärnan får ett omförsök från versionen före passet (R02 i GR-20261008-06af6ff-omgranskning-codex):
    # det första försökets ändringar återställs, och bara omförsökets session räknas; den nya sessionen läser hela kärnan
    las_kp['saknas_forsta'] = True
    v_fore_d = kd.las_status(sl_kp, 'k01')['version']
    foto_kp.update(version='v8')  # passet ändrade koden: en ny version (samma version och en tom ingen_andring vore ej genomfört)
    n_ater_d = len(ater_kp)
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'granskning', 'fordjupa:d', dom_kp)
    r_d = st_kp['kompetens']['fordjupa:d:granskning']
    assert (d_kp / 'svar-pass-fordjupa-d-granskning-2.json').is_file() and r_d['genomford'], r_d['kvitto']
    assert ater_kp[n_ater_d:n_ater_d + 1] == [v_fore_d] and r_d['kasserade_forsok'][0]['aterstalld_till'] == v_fore_d and r_d['kasserade_forsok'][0]['saknade'], r_d.get('kasserade_forsok')
    assert len(r_d['kvitto']['per_session']) == 1 and 'Dess ändringar är återställda' in prompt_kp[-1] and 'hela rollens kärna' in prompt_kp[-1], r_d['kvitto'].get('per_session')
    # omförsöket som bara läser det som saknades: den nya sessionen saknar resten av kärnan, och passet är inte genomfört (R02)
    las_kp['bara_saknade'] = True
    foto_kp.update(version='v8b')
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'granskning', 'fordjupa:d2', dom_kp)
    r_d2 = st_kp['kompetens']['fordjupa:d2:granskning']
    assert r_d2['genomford'] is False and r_d2['kvitto']['saknas'] and r_d2['kvitto']['per_session'][0]['saknas'], r_d2['kvitto']
    las_kp['bara_saknade'] = False
    kd.satt_status(sl_kp, 'k01', 'forfinad', 'förfinad', version='v8')  # läget före nästa fall, som före omförsöksfallen
    las_kp['saknas_forsta'] = False
    foto_kp.update(version='v8')
    st_kp = kd.kompetenspass(sl_kp, 'k01', 'rorelse', 'fordjupa:f', dom_kp)
    assert st_kp['kompetens']['fordjupa:f:rorelse']['genomford'] is False, 'kod ändrad utan ny version och utan skäl: ej genomfört'
    # efter fördjupningen: passen i ordning, sedan DESIGN.md-kontrollen på den slutliga koden (G11)
    foto_kp.update(version='v9')
    kd.satt_status(sl_kp, 'k01', 'forfinad', 'förfinad', version='v7', ta_bort=('kompetens',))
    st_kp = kd.efter_fordjupning(sl_kp, 'k01', {'tid': 'e', 'text': 'x', 'uppdrag': {'typ': 'bygg_ut', 'resultat': 'hela startsidan', 'omfattning': ['/x/'], 'bevara': ['första vyn'], 'specialister': {'rorelse': 'andra', 'granskning': 'andra'}}})
    assert set(st_kp['kompetens']) == {'fordjupa:e:rorelse', 'fordjupa:e:granskning'} and st_kp['design_fel'] == [] and st_kp.get('design_version'), st_kp
finally:
    for n_, v_ in spara_kp.items():
        setattr(kd, n_, v_)
    at_pt.session, at_pt.UNDERLAG, at_pt.KUNDER = spara_at_kp
# S3: tidsgränsen och stoppet når hela processträdet, också en underprocess i en egen processgrupp
skript_k3 = tmp / 'k3-trad.sh'
# ett barn i en egen processgrupp (perl setpgrp; macOS saknar setsid) och ett vanligt barn
skript_k3.write_text('#!/bin/bash\n/usr/bin/perl -e "setpgrp(0,0); sleep 300" &\nsleep 300\n')
skript_k3.chmod(0o755)
p_k3 = subprocess.Popen([str(skript_k3)], start_new_session=True)
barn_k3, egen_k3 = [], False


def egen_grupp_k3(x_):
    try:
        return os.getpgid(x_) == x_
    except OSError:
        return False
for _ in range(100):  # båda barnen har startat och perl har bytt processgrupp: under last tar det mer än en halv sekund
    barn_k3 = [x_ for x_ in nl_k3.efterkommande(p_k3.pid) if nl_k3.lever(x_)]
    egen_k3 = any(egen_grupp_k3(x_) for x_ in barn_k3)
    if len(barn_k3) >= 2 and egen_k3:
        break
    time.sleep(0.1)
assert len(barn_k3) >= 2, ('trädet syns via ppid', barn_k3)
assert egen_k3, 'ett av barnen ligger i en egen processgrupp'
dodade_k3 = nl_k3.doda_trad(p_k3.pid)
p_k3.wait(timeout=10)
time.sleep(0.3)
assert all(not nl_k3.lever(x_) for x_ in barn_k3) and set(barn_k3) <= set(dodade_k3), (barn_k3, dodade_k3)
assert nl_k3.doda_trad(None) == [] and nl_k3.ar_session(os.getpid()) is False, 'ett pid som inte är en flödessession avslutas aldrig vid återupptagning'
# S6: den aktuella linjen börjar vid den senaste nya riktningen; äldre domar pekas ut, deras text följer inte med
(tmp / 'k3-u' / 'k3-kund' / sk.DOMLOGG).write_text('\n'.join(json.dumps({'tid': t_, 'kalla': 'ägaren', 'beslut': b_, 'text': x_}) for t_, b_, x_ in (
    ('2026-10-01T10:00:00Z', 'putsa', 'KUNDBESLUT: ingen e-post på sidan'), ('2026-10-02T10:00:00Z', 'ny_riktning', 'LINJESTART'),
    ('2026-10-03T10:00:00Z', 'forkasta', 'FORKASTAD'), *[('2026-10-0%dT10:00:00Z' % (4 + i_), 'jamfor', 'J%d' % i_) for i_ in range(6)])) + '\n')
akt_k3 = '\n'.join(sk.kritikrader('k3-kund', underlag=tmp / 'k3-u', aktuella=True))
assert 'LINJESTART' in akt_k3 and 'KUNDBESLUT' not in akt_k3 and 'Äldre domar (1' in akt_k3 and 'domar i samma linje' in akt_k3, akt_k3
# S13: läget prövas; en plan utan läge är läget full (skriven före skissläget)
assert kd.LAGE in ('skiss', 'full')
spara_u_k3 = at_pt.UNDERLAG
at_pt.UNDERLAG = tmp / 'k3-u'
try:
    assert kd.korlage('k3-kund', {'kandidatlage': 'skiss'}) == 'skiss' and kd.korlage('k3-kund', {'kandidatlage': 'fullt'}) == 'full'
    (tmp / 'k3-u' / 'k3-kund' / 'atelje').mkdir(parents=True)
    (tmp / 'k3-u' / 'k3-kund' / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': 'x', 'kandidater': {}}))
    assert kd.korlage('k3-kund', {'kandidatlage': 'skiss'}) == 'full', 'en plan utan läge är läget full'
finally:
    at_pt.UNDERLAG = spara_u_k3
# S14: metodens rader kräver inte att allt läses
import inspect as insp_k3  # noqa: E402
assert 'En skill som inte lästs' not in insp_k3.getsource(kd.metod_rader)
# S15: helbygget går på prenumerationen
assert '-u ANTHROPIC_API_KEY' in (ROOT / 'kor.sh').read_text()
# S7, skärpt i rensningen inför Nortropic 2.0: ägarens domar över andra byggen når inte granskarna alls
assert 'ägarens skäl väger tyngst' not in (ROOT / 'kritik' / 'GRANSKARE.md').read_text() and 'aldrig en måttstock' in (ROOT / 'kontroller' / 'granska.py').read_text()
assert 'gäller före allt' not in (ROOT / 'kontroller' / 'atelje.py').read_text()
# S16: förteckningen pekar på alla filer ett långt utdrag fortsätter i
lev_k3 = md_kd.leverera('forska', tmp / 'k3-metod')
assert all('→' in r_ for r_ in (lev_k3['filer'][0]['fil'].read_text().split('## Att slå upp')[-1].split('## Utdragen')[0].strip().splitlines()[2:]) if r_.startswith('- '))
# Codex punkt 6: DESIGN.md-kontraktet bär importerade stilvärden och valda tillstånd; bara odeklarerade omdefinitioner fälls
import design as ds_k3  # noqa: E402
import hashlib as hl_k3  # noqa: E402
sajt_ds = tmp / 'ds-k' / 'ds-kund' / 'sajt'
(sajt_ds / 'src' / 'styles' / 'stil').mkdir(parents=True); (sajt_ds / 'dist').mkdir()
orig_ds = ':root {\n  --color-inkwell: #062d32;\n  --color-parchment: #e9e9e2;\n  --font-caslon: "Caslon", Georgia, serif;\n}\n'
(sajt_ds / 'src' / 'styles' / 'stil' / 'prov.css').write_text(orig_ds)
v_ds = {'schema': 1, 'farger': {'text': {'varde': '#062d32', 'token': '--color-inkwell', 'roll': 'text', 'kalla': 'importerat: refero prov'},
                                'yta': {'varde': '#e9e9e2', 'token': '--color-parchment', 'roll': 'yta', 'kalla': 'importerat: refero prov'}},
        'typsnitt': {'rubrik': {'familj': 'Libre Caslon Text', 'reserv': 'Georgia, serif', 'vikt': 400, 'storlek': '3rem', 'radavstand': '1.1', 'token': '--font-caslon', 'kalla': 'importerat: refero'},
                     'brodtext': {'familj': 'system-ui', 'vikt': 400, 'storlek': '1rem', 'radavstand': '1.5', 'kalla': 'valt: läsbarhet'}},
        'kontrast': [['text', 'yta', 4.5]], 'struktur': {'brodsmulor': False},
        'import': [{'fil': 'src/styles/stil/prov.css', 'kalla': 'refero: prov', 'sha256': hl_k3.sha256(orig_ds.encode()).hexdigest()}],
        'tillstand': {'mork': {'villkor': '@media (prefers-color-scheme: dark)', 'farger': {'yta': '#0f1416', 'text': '#e9e9e2'}, 'kalla': 'valt: kvällsläge'}}}
assert ds_k3.validera(v_ds) == [], ds_k3.validera(v_ds)
(sajt_ds / 'DESIGN.md').write_text('```json design\n%s\n```\n' % json.dumps(v_ds))
(sajt_ds / 'src' / 'styles' / 'design.css').write_text(ds_k3.css(v_ds))
byggd_ds = ds_k3.css(v_ds) + orig_ds + 'h1{color:var(--color-inkwell);font-family:var(--font-caslon)} body{background:var(--farg-yta)}'
(sajt_ds / 'dist' / 'index.html').write_text('<html><head><style>%s</style></head><body></body></html>' % byggd_ds)
k_ds = ds_k3.kontroll('ds-kund', kunder=tmp / 'ds-k')
assert k_ds['ok'], k_ds['fel']
(sajt_ds / 'dist' / 'index.html').write_text('<html><head><style>%s .x{--farg-yta:#ff0000}</style></head><body></body></html>' % byggd_ds)
assert any('#ff0000' in f_ for f_ in ds_k3.kontroll('ds-kund', kunder=tmp / 'ds-k')['fel']), 'en odeklarerad omdefinition fälls'
(sajt_ds / 'src' / 'styles' / 'stil' / 'prov.css').write_text(orig_ds.replace('#062d32', '#000000'))
assert any('ändrad sedan stilexporten' in f_ for f_ in ds_k3.kontroll('ds-kund', kunder=tmp / 'ds-k')['fel']), 'originalexporten står orörd'
v2_ds = json.loads(json.dumps(v_ds)); v2_ds['tillstand']['mork']['farger'] = {'text': '#777777', 'yta': '#888888'}
assert any('tillstand.mork: kontrast' in f_ for f_ in ds_k3.validera(v2_ds)), 'kontrasten prövas i tillståndet'
# leveransen (Codex leveransluckorna): adaptern läggs in, läckor fälls, en publik hänvisning redovisas
import exportera as ex_k3  # noqa: E402
konf_ex = "import { defineConfig } from 'astro/config';\nexport default defineConfig({\n  site: 'https://x.se',\n  output: 'static',\n});\n"
ut_ex = ex_k3.med_adapter(konf_ex)
assert "import vercel from '@astrojs/vercel';" in ut_ex and 'adapter: vercel({ maxDuration: 30 })' in ut_ex and ex_k3.med_adapter(ut_ex) == ut_ex, 'körtiden (D3)'
lk_ex = tmp / 'lk-ex'; (lk_ex / 'src').mkdir(parents=True)
(lk_ex / 'src' / 'a.astro').write_text('<!-- underlag/kund-x/BRIEF.md -->')
(lk_ex / 'src' / 'b.astro').write_text('<!-- byggd med kontroller/design.py -->')
(lk_ex / '.env.example').write_text('RESEND_API_KEY=\n# kommentar\n')
(lk_ex / 'src' / 'c.js').write_text("const k = 're_Ab12Cd34_Ef56Gh78Ij90Kl12Mn34Op56';")  # Resends form: re_ + 8 + _ + 24
assert sorted(f_ for f_, _s in ex_k3.lackor(lk_ex)) == ['src/a.astro', 'src/c.js'] and ex_k3.hanvisningar(lk_ex) == ['src/b.astro'], (ex_k3.lackor(lk_ex), ex_k3.hanvisningar(lk_ex))
lev_ex = json.loads((ROOT / 'mall' / 'leverans' / 'package.json').read_text())
assert lev_ex['dependencies']['@astrojs/vercel'] and lev_ex['overrides']['path-to-regexp'] == '6.3.0' and (ROOT / 'mall' / 'leverans' / 'package-lock.json').is_file()
assert json.loads((ROOT / 'mall' / 'leverans' / 'vercel.json').read_text())['regions'] == ['arn1'], 'formulärets funktion i Stockholm'
# serverfunktionen: varje väg i kontraktet, utan nät (Node)
nod_ex = tmp / 'forfragan-prov'; nod_ex.mkdir()
shutil.copyfile(ROOT / 'mall' / 'leverans' / 'forfragan.js', nod_ex / 'forfragan.mjs')
# en ersättare för @vercel/blob utan nät: lagringen prövas på riktigt (den oberoende granskningen 2026-10-05, fynd 13)
(nod_ex / 'node_modules' / '@vercel' / 'blob').mkdir(parents=True)
(nod_ex / 'node_modules' / '@vercel' / 'blob' / 'package.json').write_text('{"name": "@vercel/blob", "type": "module", "main": "index.js"}')
(nod_ex / 'node_modules' / '@vercel' / 'blob' / 'index.js').write_text('export async function put(vag, kropp, opt) { globalThis.__blob.push([vag.split("/").pop(), opt.access, opt.contentType]); return { pathname: vag }; }')
(nod_ex / 'prov.mjs').write_text('''import { POST } from './forfragan.mjs';
const ut = [];
const form = (f, bild) => { const fd = new FormData(); for (const [k, v] of Object.entries(f)) fd.append(k, v); if (bild) fd.append('bild', bild, 'b.jpg');
  return new Request('https://x.se/api/forfragan/', { method: 'POST', body: fd }); };
const g = { namn: 'Prov', telefon: '0700000000', meddelande: 'Hej', fylltid: '9000' };
globalThis.__blob = [];
async function kor(req, env = {}, svar = null) {
  for (const k of ['RESEND_API_KEY', 'FORFRAGAN_TILL', 'FORFRAGAN_FRAN', 'VERCEL_ENV', 'BLOB_STORE_ID']) delete process.env[k];
  Object.assign(process.env, env);
  globalThis.fetch = svar ? async () => svar() : async () => { throw new Error('inget nät'); };
  const r = await POST({ request: req }); ut.push([r.status, r.headers.get('location'), r.headers.get('x-forfragan')]); }
await kor(form({ ...g, webbplats: 'x' }));
await kor(form({ ...g, telefon: '' }));
await kor(new Request('https://x.se/api/forfragan/', { method: 'POST', headers: { 'content-length': '5000000' }, body: 'x' }));
await kor(form(g), { VERCEL_ENV: 'preview' });
await kor(form(g), { VERCEL_ENV: 'production' });
const konf = { VERCEL_ENV: 'production', RESEND_API_KEY: 'k', FORFRAGAN_TILL: 'a@x.se', FORFRAGAN_FRAN: 'w@x.se' };
await kor(form(g, new Blob([new Uint8Array([255, 216, 255, 217])], { type: 'image/jpeg' })), konf, () => new Response('{}', { status: 200 }));
await kor(form(g), konf, () => new Response('fel', { status: 500 }));
await kor(form(g, new Blob([new Uint8Array(4200000)], { type: 'image/jpeg' })));
await kor(form(g, new Blob(['text'], { type: 'text/plain' })));
await kor(form(g, new Blob([new Uint8Array([255, 216, 255, 217])], { type: 'image/jpeg' })), { VERCEL_ENV: 'production', BLOB_STORE_ID: 's' });
await kor(form(g), { ...konf, BLOB_STORE_ID: 's' }, () => new Response('fel', { status: 500 }));
console.log(JSON.stringify(ut));
console.log(JSON.stringify(globalThis.__blob));
''')
r_nod = subprocess.run(['node', 'prov.mjs'], cwd=nod_ex, capture_output=True, text=True, timeout=60)
assert r_nod.returncode == 0, r_nod.stderr[-500:]
ut_nod, blob_nod = [json.loads(x) for x in r_nod.stdout.strip().splitlines()[-2:]]
assert ut_nod == [[303, '/tack/', 'honeypot'], [422, None, 'ofullstandig'], [413, None, 'for-stor'],
                  [303, '/tack/', 'demo'], [503, None, 'fel'], [503, None, 'fel'], [503, None, 'fel'],
                  [413, None, 'for-stor'], [422, None, 'ofullstandig'],
                  [303, '/mottagen/', 'sparad'], [303, '/mottagen/', 'sparad']], ut_nod  # sparad men ej aviserad: 303 till /mottagen/ (D1)
assert blob_nod == [['bild', 'private', 'image/jpeg'], ['forfragan.json', 'private', 'application/json'], ['forfragan.json', 'private', 'application/json']], blob_nod
# förhandsvisningens interaktionsväg: bara kända tillstånd och en enkel CSS-väljare (Codex punkt 9)
import forhandsvisa as fv_k3  # noqa: E402
assert fv_k3.main(['sk-prov', '--kandidat', 'k01', '--tillstand', 'tangentbord,okant']) == 2 and fv_k3.main(['sk-prov', '--meny', 'a;b{}']) == 2
# metodlåset omfattar rollernas alla filer, och metodens hash binder dem (Codex; G20)
fel_las, kallor_las = md_kd.prova()
assert not fel_las and all(f_ in kallor_las for x_ in kp_k3.tolka().values() for f_ in x_['karna'] + x_['valj']), [f_ for x_ in kp_k3.tolka().values() for f_ in x_['karna'] + x_['valj'] if f_ not in kallor_las][:5]
print('kompetenskedjan och granskning 3 ok')

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
assert {x: bb_['bygget'][x] for x in ('sessioner', 'turer', 'minuter', 'listpris_usd')} == {'sessioner': 1, 'turer': 100, 'minuter': 10.0, 'listpris_usd': 10.5}, bb_
assert {x: bb_['totalt'][x] for x in ('minuter', 'turer', 'listpris_usd')} == {'minuter': 16.0, 'turer': 185, 'listpris_usd': 18.0} and bb_['totalt']['fullstandigt'], bb_
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
utan_sb = sl.installningar('p', sandlada=False)
# hemlighetsmappen nekas Read också utan sandlåda (dashboardnyckeln ligger där; b075827)
assert 'sandbox' not in utan_sb and utan_sb['permissions']['deny'] == ['Read(//%s/**)' % str(ROOT / 'underlag/kundstart').strip('/'), *__import__('kompetens').skill_nekas(),
                                                                       'Read(//%s/.nortropic-hemligheter/**)' % os.path.expanduser('~').strip('/')] and json.dumps(inst)
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
# utan godkänd startsida stannar kor.sh före bygget (skapandeflödet körs före bygget och slutar i ägarens godkännande)
rk = subprocess.run(['bash', str(kr / 'kor.sh'), 'prov-bygge', 'Prov AB, https://exempel.se'], capture_output=True, text=True, cwd=str(kr), env=miljo_k, timeout=300)
assert rk.returncode == 2 and 'ingen godkänd startsida' in rk.stdout and not (kr / 'backlog' / 'B-20261003-prov-fran-bygget.md').exists(), (rk.returncode, rk.stdout[-300:])
miljo_k['NWP_ATELJE'] = 'av'  # nödvägen utan ateljé: provet gäller backlogcommiten
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
(kr / 'kunder' / '.bygge-pid').write_text('%d\n' % os.getpid())
# Reservationen är flock, inte en godtycklig levande PID. Håll den på riktigt medan nästa kor.sh försöker starta.
import fcntl
with open(kr / 'kunder' / '.bygge.las', 'a') as bygglas_prov:
    fcntl.flock(bygglas_prov.fileno(), fcntl.LOCK_EX)
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
    rot_pg = Path(tempfile.mkdtemp(prefix='nwp-pg-', dir='/tmp')); egna_pg.append(rot_pg); korregister_.registrera_tmp(rot_pg, 'prov_revision processgräns')  # exklusivt skapad; utanför sessionens temp och körningens egna kataloger, annars prövas inget
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
    # --utan-nat (byggen av skaparens sidor, prova.bygg_inom_grans): inte heller localhost, där dashboarden tar emot ägarens
    # domar (omgranskning 3); utan flaggan når byggsteget localhost som förut
    srv_pg, _ = server(tmp)
    try:
        kod_pg = 'import urllib.request\ntry:\n urllib.request.urlopen("http://127.0.0.1:%d/", timeout=5); print("NÅDDE")\nexcept Exception as e:\n print("NEKAD")' % srv_pg.server_port
        for fl_, vantat_ in (([], 'NÅDDE'), (['--utan-nat'], 'NEKAD')):
            r_pg = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg), *fl_, '--', PY, '-c', kod_pg], capture_output=True, text=True, timeout=60)
            assert r_pg.stdout.strip() == vantat_, (fl_, r_pg.stdout, r_pg.stderr[-300:])
        # inte heller namnuppslag (mDNSResponders unix-sockel), som annars bär data ut i DNS-namn (granskning 5, fynd 3)
        dns_pg = 'import socket\ntry:\n socket.getaddrinfo("example.com", 80); print("LÖSTES")\nexcept Exception:\n print("NEKAD")'
        r_pg = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg), '--utan-nat', '--', PY, '-c', dns_pg], capture_output=True, text=True, timeout=60)
        assert r_pg.stdout.strip() == 'NEKAD', (r_pg.stdout, r_pg.stderr[-300:])
    finally:
        srv_pg.shutdown()
    import inspect as inspect_pg  # noqa: E402
    assert '--utan-nat' in inspect_pg.getsource(prova.bygg_inom_grans) and "'--skrivbar', str(sajt)" in inspect_pg.getsource(prova.bygg_inom_grans), 'skaparens byggen går utan nät och skriver bara i projektet de bygger'
    # --bara-sajt: skrivning bara i sajten och tempkatalogen, aldrig i underlag/<slug> (domloggen, VINNARE.json) eller
    # kunder/<slug> utanför sajten (granskning 6)
    (rot_pg / 'kunder' / sl_pg / 'sajt').mkdir(parents=True, exist_ok=True)
    skriv_pg = ('import sys\nfor p in sys.argv[1:]:\n try:\n  open(p, "w").write("x"); print("SKREV", p.rsplit("/", 2)[-2])\n except Exception:\n  print("NEKAD", p.rsplit("/", 2)[-2])')
    mal_pg = [str(rot_pg / 'kunder' / sl_pg / 'sajt' / 'x.txt'), str(rot_pg / 'kunder' / sl_pg / 'x.txt'), str(rot_pg / 'underlag' / sl_pg / 'DESIGNDOMAR.jsonl')]
    r_pg = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg), '--utan-nat', '--bara-sajt', '--', PY, '-c', skriv_pg, *mal_pg],
                          capture_output=True, text=True, timeout=60)
    assert r_pg.stdout.split('\n')[:3] == ['SKREV sajt', 'NEKAD %s' % sl_pg, 'NEKAD %s' % sl_pg], (r_pg.stdout, r_pg.stderr[-300:])
    # --skrivbar (kandidatflödet): en kandidats projekt under kunder/<slug>/kandidater/ är skrivbart, sajten och underlaget inte;
    # en väg utanför kunder/<slug> vägras. Barnet kör Homebrews tolk direkt: kandidatens läsgräns släpper inte repots .venv
    # (byggets läsgräns, 2026-10-07; prov_lasgrans.py prövar läsningen)
    kp_pg = rot_pg / 'kunder' / sl_pg / 'kandidater' / 'k01' / 'sajt'; kp_pg.mkdir(parents=True, exist_ok=True)
    mal_k_pg = [str(kp_pg / 'x.txt'), str(rot_pg / 'kunder' / sl_pg / 'sajt' / 'y.txt'), str(rot_pg / 'underlag' / sl_pg / 'DESIGNDOMAR.jsonl')]
    r_pg = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg), '--utan-nat', '--skrivbar', str(kp_pg), '--', os.path.realpath(PY), '-c', skriv_pg, *mal_k_pg],
                          capture_output=True, text=True, timeout=60)
    assert r_pg.stdout.split('\n')[:3] == ['SKREV sajt', 'NEKAD sajt', 'NEKAD %s' % sl_pg], (r_pg.stdout, r_pg.stderr[-300:])
    r_pg = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), sl_pg, '--root', str(rot_pg), '--skrivbar', str(rot_pg / 'underlag' / sl_pg), '--', PY, '-c', 'print(1)'],
                          capture_output=True, text=True, timeout=60)
    assert r_pg.returncode != 0 and '1' not in r_pg.stdout, 'skrivbart utanför kunder/<slug> vägras'
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
# efter den rena designstarten 2026-10-09 finns ingen nivåfil (den byggs ur nya ankare); mekaniken prövas med designreglerna i dess ställe
assert not (ROOT / kf_.NIVAFIL).exists()
kf_.NIVAFIL = 'kunskap/designregler.md'
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
helt_ = {'kriterier': krit_ok, 'kognitiv_genomgang': [], 'blockerande': [], 'forbattringar': [], 'styrkor': [], 'likhet_tidigare': '', 'sett': [], 'ej_bedomt': [], 'sammanfattning': '', 'prototypjamforelse': {'status': 'ingen_prototyp', 'jamforda': [], 'ej_bedomt': [], 'skal': ''}}
schema_ = kf_.las_schema(ROOT / 'kritik' / 'SCHEMA-granskning.json')
block_ok = {'kriterium': 'text', 'allvarlighet': 3, 'var': 'x', 'observation': 'x', 'konsekvens': 'x', 'standardpunkt': 'x', 'heuristik': 'x', 'omfattning': 'detalj', 'rattning': 'x', 'acceptanskriterium': 'x', 'bild': 'x', 'referensbild': ''}
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
assert (fryst_ / 'kritik' / 'GRANSKARE.md').is_file() and (fryst_ / 'kritik' / 'SCHEMA-granskning.json').is_file() and (fryst_ / kf_.NIVAFIL).is_file() and (fryst_ / 'kunskap' / 'teoretisk-grund.md').is_file()
man_ = json.loads((ut_kf / 'K02' / 'MANIFEST.json').read_text())
assert man_['regler']['kritik/GRANSKARE.md'] == kf_.hash_fil(fryst_ / 'kritik' / 'GRANSKARE.md') and kf_.NIVAFIL in man_['regler'] and 'kritik/SCHEMA-granskning.json' in man_['regler']
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
gr_text_ = (ROOT / 'kritik' / 'GRANSKARE.md').read_text()
assert 'visuell-niva.md' not in gr_text_ and 'Kalibreringen:' in gr_text_ and 'inga kalibreringsankare' in gr_text_ and 'Bildankarna' not in gr_text_
assert not (ROOT / 'kunskap' / 'visuell-niva.md').exists(), 'nivåfilen ur de gamla ankarna är borttagen (den rena designstarten)'
assert all(x_ not in gr_text_.lower() for x_ in ('oatly', 'koto', 'dinesen', 'belvia', 'blue tit', 'sparky', 'vardehaugen', 'snickaren', 'paint it', 'sundbom', 'salong kreativ', 'grilli')), 'den publika granskartexten namnger inga sajter'
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
                # menyn öppnas på riktigt: menybilden tas bara när menyn öppnades (ägaren 2026-10-06, inspektera.mjs)
                '<nav><button id="meny" aria-expanded="false" onclick="this.setAttribute(\'aria-expanded\', \'true\'); this.nextElementSibling.hidden = false">'
                'Meny</button><ul hidden><li>Tjänster</li></ul></nav>%s<p>%s</p></body></html>' % (self.path, img, 'text ' * 200)).encode()
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
def kor_utan_rapport_(adress, ut, tillat, tillstand, miljo, extrahera=None, bredder=rf_.BREDDER_STANDARD):
    if adress.endswith('/a-b'):
        return 1, {}, 'simulerad: ingen rapport'
    return kor_orig_(adress, ut, tillat, tillstand, miljo, extrahera, bredder)
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
def kor_pass1_faller_(adress, ut, tillat, tillstand, miljo, extrahera=None, bredder=rf_.BREDDER_STANDARD):
    if str(ut).endswith('.pass1') and ('/a-b' in adress or '/egen' in adress):
        raise subprocess.TimeoutExpired(['node'], 1)
    return kor_orig_(adress, ut, tillat, tillstand, miljo, extrahera, bredder)
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
def obs_tar_bort_bild_(rapport, ut, bestallda=(), bredder=rf_.BREDDER_STANDARD):
    o_ = obs_orig_(rapport, ut, bestallda, bredder)
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
(u_rt / 'prov-rt' / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provfirman', 'kategorier': ['snickare']}))
stilar_rt_ = []
def logg_rt_(logg, anrop, traffar, subtype='success'):
    rader = [json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': n, 'input': {}}]}}) for n in anrop]
    rader.append(json.dumps({'type': 'result', 'subtype': subtype, 'is_error': subtype != 'success', 'num_turns': len(anrop) + 1, 'structured_output': {'anrop': [{'verktyg': 'påstått', 'argument': 'x', 'resultat_typ': 'json'}] * 9, 'traffar': traffar, 'stilar': stilar_rt_, 'anmarkning': 'prov'}}))
    Path(logg).write_text('\n'.join(rader) + '\n')
def kor_rt_ok_(tjanst, prompt, logg, modell):
    assert 'Provfirman' not in prompt and 'snickare' in prompt and 'task_intent' in prompt and tjanst in ('refero', 'mobbin'), 'bara branschen följer med till tjänsten'
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
# Mobbins egna svar som reserv: sessionens strukturerade svar saknar bildadresser (den riktiga körningen 2026-10-06: en
# tom post och anmärkningen "x", fast svaren hade tio skärmar var); skärmarna läses ur svaren och laddas ner
def kor_rt_ra_(tjanst, prompt, logg, modell):
    svar_ = json.dumps({'query': 'contact form page', 'screens': [
        {'id': 'S1', 'image_url': rt_bild, 'mobbin_url': 'https://mobbin.com/screens/S1', 'app_name': 'Appen', 'platform': 'web'},
        {'id': 'S2', 'image_url': rt_bild + '?andra', 'mobbin_url': 'https://mobbin.com/screens/S2', 'app_name': 'Appen två', 'platform': 'web'},
        {'id': 'S1', 'image_url': rt_bild, 'mobbin_url': 'https://mobbin.com/screens/S1', 'app_name': 'Appen', 'platform': 'web'}]})
    rader_ = [json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'u1', 'name': 'mcp__mobbin__search_screens',
                                                                         'input': {'query': 'contact form page'}}]}}),
              json.dumps({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'u1',
                                                                    'content': [{'type': 'text', 'text': '[Image: source: /x/blob.webp]' + svar_}]}]}}),
              json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 2, 'structured_output': {
                  'anrop': [], 'traffar': [{'id': 'c9-skip', 'titel': '', 'sida_url': '', 'bild_url': '', 'beskrivning': '', 'fraga': ''}],
                  'stilar': [], 'anmarkning': 'x'}})]
    Path(logg).write_text('\n'.join(rader_) + '\n')
    return 0, ''
rot_rt, res_rt = rt_.samla('prov-rt', {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form', 'syfte': ''}]}, u_rt, lokala_portar=(rt_port,), kor=kor_rt_ra_)
m_ = res_rt['tjanster']['mobbin']
assert m_['ok'] and m_['bilder'] == 2 and [t_['id'] for t_ in m_['traffar']] == ['S1', 'S2'], m_
assert all(t_['fil'] and t_['fraga'] == 'contact form' and t_['titel'] for t_ in m_['traffar']) and any('lästes ur Mobbins egna svar' in a_ for a_ in m_['anmarkningar']), m_
# reserven slår bara till när sessionen inte gav något giltigt svar eller gav träffar utan en enda bildadress, läser bara
# Mobbins egna sökverktyg och aldrig ett felsvar, har ett totaltak, och två id med samma filnamn skriver inte över
# varandra (granskningen av r77, M3, L8, L9 och L11)
def logg_ra_(logg, svar_lista, traffar, giltigt=True):
    rader_ = []
    for i_, (verktyg_, text_, fel_) in enumerate(svar_lista):
        rader_.append(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'u%d' % i_, 'name': verktyg_,
                                                                                 'input': {'query': 'q'}}]}}))
        rader_.append(json.dumps({'type': 'user', 'message': {'content': [dict({'type': 'tool_result', 'tool_use_id': 'u%d' % i_,
                                                                               'content': [{'type': 'text', 'text': text_}]}, **({'is_error': True} if fel_ else {}))]}}))
    if giltigt:
        rader_.append(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 2, 'structured_output': {
            'anrop': [], 'traffar': traffar, 'stilar': [], 'anmarkning': 'x'}}))
    Path(logg).write_text('\n'.join(rader_) + '\n')
def skarmar_(fraga_, *ids):
    return json.dumps({'query': fraga_, 'screens': [{'id': i_, 'image_url': rt_bild + '?' + i_, 'mobbin_url': 'https://mobbin.com/screens/' + i_,
                                                    'app_name': 'App ' + i_, 'platform': 'web'} for i_ in ids]})
upp_m1 = {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form', 'syfte': ''}]}
SKRAP_ = [{'id': 'c9-skip', 'titel': '', 'sida_url': '', 'bild_url': '', 'beskrivning': '', 'fraga': ''}]
FALL_RA = {  # namn: (svaren, sessionens träffar, giltigt svar, väntade id, reserven använd)
    'valde bort allt': ([('mcp__mobbin__search_screens', skarmar_('contact form', 'S1'), False)], [], True, [], False),
    'flöde med stegbilder': ([('mcp__mobbin__search_screens', skarmar_('contact form', 'S1'), False)],
                             [{'id': 'F1', 'titel': 'Flöde', 'bild_url': '', 'steg': [{'bild_url': rt_bild, 'beskrivning': 's1'}]}], True, ['F1'], False),
    'nedladdning som föll': ([('mcp__mobbin__search_screens', skarmar_('contact form', 'S1'), False)],
                             [{'id': 'N1', 'titel': 'n', 'bild_url': 'https://evil.example/x.png'}], True, ['N1'], False),
    'inget giltigt svar': ([('mcp__mobbin__search_screens', skarmar_('contact form', 'S1', 'S2'), False)], [], False, ['S1', 'S2'], True),
    'annat verktyg och felsvar': ([('mcp__annan__search_screens', skarmar_('contact form', 'A1'), False),
                                   ('mcp__mobbin__search_screens', skarmar_('contact form', 'E1'), True)], SKRAP_, True, ['c9-skip'], False),
}
for namn_ra, (svar_ra, traffar_ra, giltigt_ra, vantat_ra, reserv_ra) in FALL_RA.items():
    def kor_fall_(tjanst, prompt, logg, modell, s_=svar_ra, t_=traffar_ra, g_=giltigt_ra):
        logg_ra_(logg, s_, t_, g_)
        return (0, '') if g_ else (1, 'sessionen föll')
    m_ = rt_.samla('prov-rt', upp_m1, u_rt, lokala_portar=(rt_port,), kor=kor_fall_)[1]['tjanster']['mobbin']
    anv_ = [a_ for a_ in m_['anmarkningar'] if 'lästes ur Mobbins egna svar' in a_]
    assert [t_['id'] for t_ in m_['traffar']] == vantat_ra and bool(anv_) == reserv_ra, (namn_ra, m_['traffar'], m_['anmarkningar'])
    assert m_['bilder'] == sum(1 for t_ in m_['traffar'] if t_.get('fil')) + sum(1 for t_ in m_['traffar'] for x_ in t_.get('steg') or [] if x_.get('fil')), (namn_ra, m_)
    if reserv_ra:
        assert 'sessionen gav inget giltigt svar' in anv_[0] and m_['ok'], (namn_ra, anv_)
# totaltaket: fem frågor med elva skärmar och en sjätte med tolv ger högst MAX_TRAFFAR; taket nås mitt i det sjätte svaret
upp_m6 = {'fragor': [{'tjanst': 'mobbin', 'fraga': 'fraga %s sida' % o_, 'syfte': ''} for o_ in ('alfa', 'beta', 'gamma', 'delta', 'epsilon', 'zeta')]}
def kor_tak_(tjanst, prompt, logg, modell):
    logg_ra_(logg, [('mcp__mobbin__search_screens', skarmar_('fraga %s sida' % o_, *['%s%02d' % (o_, n_) for n_ in range(12 if o_ == 'zeta' else 11)]), False)
                    for o_ in ('alfa', 'beta', 'gamma', 'delta', 'epsilon', 'zeta')], [], False)
    return 1, 'sessionen föll'
m_ = rt_.samla('prov-rt', upp_m6, u_rt, lokala_portar=(rt_port,), kor=kor_tak_)[1]['tjanster']['mobbin']
assert len(m_['traffar']) == rt_.MAX_TRAFFAR == 60 and m_['bilder'] == 60 and sum(1 for t_ in m_['traffar'] if t_['fraga'] == 'fraga zeta sida') == 5, \
    (len(m_['traffar']), m_['bilder'])
# två id med samma filnamn
def kor_namn_(tjanst, prompt, logg, modell):
    logg_ra_(logg, [('mcp__mobbin__search_screens', '{}', False)], [{'id': 'a b', 'titel': 't', 'bild_url': rt_bild}, {'id': 'a-b', 'titel': 't', 'bild_url': rt_bild + '?2'}])
    return 0, ''
m_ = rt_.samla('prov-rt', upp_m1, u_rt, lokala_portar=(rt_port,), kor=kor_namn_)[1]['tjanster']['mobbin']
assert [t_['id'] for t_ in m_['traffar']] == ['a-b', 'a-b-2'] and len({t_['fil'] for t_ in m_['traffar']}) == 2 and all(t_['fil'] for t_ in m_['traffar']), m_['traffar']
# en omdirigering följs bara till en tillåten adress: provets egen server, aldrig en annan lokal port (L10)
class Omdir_(hs_.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(302); self.send_header('Location', 'http://127.0.0.1:%d/skarm.png' % (rt_port if self.path == '/tillaten' else 1))
        self.send_header('Content-Length', '0'); self.end_headers()
    def log_message(self, *a): pass
srv_od = hs_.HTTPServer(('127.0.0.1', 0), Omdir_); th_.Thread(target=srv_od.serve_forever, daemon=True).start()
od_ = 'http://127.0.0.1:%d' % srv_od.server_address[1]
f_od, fel_od = rt_.ladda_bild(od_ + '/tillaten', tmp / 'od-1', lokala_portar=(rt_port, srv_od.server_address[1]))
assert f_od and f_od.read_bytes() == png_ref, fel_od
f_od, fel_od = rt_.ladda_bild(od_ + '/annan', tmp / 'od-2', lokala_portar=(rt_port, srv_od.server_address[1]))
assert f_od is None and 'inte tillåten' in fel_od, fel_od
assert not rt_.offentlig_adress('https://127.0.0.1/x') and not rt_.offentlig_adress('https://10.1.2.3/x') and not rt_.offentlig_adress('http://93.184.215.14/x')
# en IPv4-adress inbäddad i IPv6 prövas för sig, och filnamnen skiljer inte på stora och små bokstäver (r79, J och K)
assert [rt_.offentlig_ip(a_) for a_ in ('::ffff:127.0.0.1', '64:ff9b::7f00:1', '2002:7f00:1::', '::7f00:1', '::ffff:93.184.215.14', '2606:4700::1111',
                                         '::ffff:0:7f00:1', '2002:5db8:d70e::')] == [False, False, False, False, True, True, False, False]
anv_ = set(); assert [rt_.unikt('skarm-a1', anv_), rt_.unikt('Skarm-A1', anv_)] == ['skarm-a1', 'Skarm-A1-2']
srv_od.shutdown()
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
# tjänstens svar i sessionsloggen, som verkliga anrop och svar (tool_use och tool_result parade på id): get_style tar
# style_ids i klump och svarar med hela dokumenten i en annan ordning; sökningens "## Style: <id>" binder titeln till id:t
def logg_rt2_(logg, par, traffar=(), stilar=()):
    rader = []
    for i_, (n_, ind_, txt_) in enumerate(par):
        rader.append(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't%d' % i_, 'name': n_, 'input': ind_}]}}))
        rader.append(json.dumps({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 't%d' % i_, 'content': [{'type': 'text', 'text': txt_}]}]}}))
    rader.append(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 4,
                             'structured_output': {'anrop': [], 'traffar': list(traffar), 'stilar': list(stilar), 'anmarkning': ''}}))
    Path(logg).write_text('\n'.join(rader) + '\n')
doc_gte_ = "# GTE — Style Reference\n> Carbon\n\n**Theme:** dark\n\n## Tokens — Colors\n\n| Name | Value |\n|---|---|\n| Carbon | `#111` |\n\n## Do's and Don'ts\n\n- Do: hairlines\n\n## Imagery\n\nDocumentary photos, full bleed.\n\n## Layout\n\nCentered hero.\n"
sok_rt_ = '*Page 1*\n\n## Style: S 1\n\n- **Title**: GTE\n- **Preview URL**: %s\n\n## Style: S2\n\n- **Title**: Annan Stil\n' % rt_bild
skarm_rt_ = '## Screen: SC1\n\n- **Platform**: web\n- **Preview URL**: %s\n- **Thumbnail URL**: https://images.refero.design/screenshots/x/SC1_thumb.jpg\n' % rt_bild
def kor_rt_stil_(tjanst, prompt, logg, modell):
    logg_rt2_(logg, [('mcp__refero__refero_search_styles', {'query': 'warm editorial craft'}, sok_rt_),
                     ('mcp__refero__refero_get_style', {'style_ids': ['S2', 'S 1']}, '# Annan Stil — Style Reference\n\nAnnat.\n\n' + doc_gte_),
                     ('mcp__refero__refero_get_screen', {'screen_id': 'SC1'}, skarm_rt_)],
              traffar=[{'id': 'SC1', 'titel': 'Skärmen', 'sida_url': 'https://x.se/', 'bild_url': 'https://images.refero.design/screenshots/x/SC1_thumb.jpg', 'beskrivning': 'b', 'fraga': 'f',
                        'steg': [{'bild_url': rt_bild, 'beskrivning': 'steg ett: formuläret'}]}], stilar=stilar_rt_)
    return 0, ''
(rot_rt / 'TJANSTER.md').write_text('förra undersökningen')
rot_rt, res_rt = rt_.samla('prov-rt', upp_stil, u_rt, lokala_portar=(rt_port,), kor=kor_rt_stil_)
st_ = res_rt['tjanster']['refero']
assert st_['ok'] and st_['stilar'][0]['typografi'].startswith('serif display') and st_['stilar'][0]['fil'] and not st_['stilar'][0]['fel'] and st_['stilar'][0]['belagd'], st_
dok_rt_ = u_rt / 'prov-rt' / st_['stilar'][0]['dokument']
assert dok_rt_.name == 'stil-gte.md' and dok_rt_.read_text().startswith('# GTE — Style Reference') and 'Documentary photos, full bleed.' in dok_rt_.read_text() and 'Annat.' not in dok_rt_.read_text(), 'hela stildokumentet ordagrant, bundet till rätt stil'
assert st_['traffar'][0]['bild_url'] == rt_bild and st_['traffar'][0]['fil'], 'Referos tumnagel byts mot skärmens Preview URL ur tjänstens eget svar'
assert st_['traffar'][0]['steg'][0]['fil'] and st_['traffar'][0]['steg'][0]['beskrivning'].startswith('steg ett'), 'flödets steg med egna bilder'
assert st_['logg'].startswith('referenser/tjanster/refero/session-') and len(list((u_rt / 'prov-rt' / st_['ra']).glob('[0-9][0-9]-*.md'))) == 3, st_
assert '/bilder-' in st_['traffar'][0]['fil'] and st_['ra'] in st_['stilar'][0]['dokument'], 'bilderna och stildokumenten ligger per körning: en senare körning skriver aldrig över dem'
md_rt_ = (rot_rt / 'TJANSTER.md').read_text()
assert '### Stil: GTE' in md_rt_ and '- färger: carbon #111' in md_rt_ and 'stil-gte.md' in md_rt_ and 'steg 1:' in md_rt_ and res_rt['tidigare'] in md_rt_
assert (u_rt / 'prov-rt' / res_rt['tidigare']).read_text() == 'förra undersökningen', 'den förra undersökningen arkiveras, aldrig överskriven'
rot_rt, res_rt2 = rt_.samla('prov-rt', upp_stil, u_rt, lokala_portar=(rt_port,), kor=kor_rt_stil_)
assert res_rt2['tidigare'] != res_rt['tidigare'] and res_rt2['tjanster']['refero']['logg'] != st_['logg'], 'två körningar samma sekund får egna namn'
svar_rt_ = []
assert rt_.las_logg(u_rt / 'prov-rt' / st_['logg'], svar_rt_)[0]['mcp__refero__refero_get_style'] == 1 and [n_.split('__')[-1] for n_, _i, _t in svar_rt_] == ['refero_search_styles', 'refero_get_style', 'refero_get_screen']
assert rt_.stiltitlar(svar_rt_) == {'S2': 'Annan Stil'}, 'id:n med mellanslag finns inte hos Refero; titeln binder då via modellens titel'
def kor_rt_stil_utan_(tjanst, prompt, logg, modell):
    logg_rt2_(logg, [('mcp__refero__refero_search_styles', {'query': 'q'}, sok_rt_)], stilar=stilar_rt_); return 0, ''
rot_rt, res_rt = rt_.samla('prov-rt', upp_stil, u_rt, lokala_portar=(rt_port,), kor=kor_rt_stil_utan_)
st_ = res_rt['tjanster']['refero']
assert not st_['ok'] and 'hämtades inte med get_style' in st_['stilar'][0]['fel'] and any('utan refero_get_style' in a_ for a_ in st_['anmarkningar']), 'påstådda stilvärden utan get_style är inte belagda'
assert 'aldrig Thumbnail URL' in rt_.prompt_for('refero', [{'tjanst': 'refero', 'fraga': 'x', 'syfte': '', 'typ': 'skarm'}], 'P') and 'ingen platform-' in rt_.prompt_for('mobbin', [{'tjanst': 'mobbin', 'fraga': 'x', 'syfte': '', 'typ': 'skarm'}], 'P')
stilar_rt_[:] = []
# uppdragens material i en egen katalog: researchens rapport står orörd (ägarens uppdrag 2026-10-05 18:53Z, Mobbin per uppgift)
fore_rt_ = (rot_rt / 'TJANSTER.json').read_bytes()
rot_up_, res_up_ = rt_.samla('prov-rt', {'fragor': [{'tjanst': 'mobbin', 'fraga': 'contact form', 'syfte': ''}]}, u_rt, lokala_portar=(rt_port,),
                             kor=kor_rt_tom_, katalog='uppdrag')
assert rot_up_ == u_rt / 'prov-rt' / 'referenser' / 'uppdrag' and (rot_up_ / 'TJANSTER.json').is_file() and (rot_rt / 'TJANSTER.json').read_bytes() == fore_rt_
assert res_up_['tjanster']['mobbin']['logg'].startswith('referenser/uppdrag/mobbin/session-'), res_up_['tjanster']['mobbin']['logg']
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
        # granskning 6: design.css skrivs aldrig genom en länk som byggkod kan ha lagt; en länkad katalog vägras
        (tmp / 'offer-dz.txt').write_text('orörd'); (sajt_dz / 'src' / 'styles' / 'design.css').unlink()
        (sajt_dz / 'src' / 'styles' / 'design.css').symlink_to(tmp / 'offer-dz.txt')
        with contextlib.redirect_stdout(io.StringIO()):
            assert dz.main(['dz', '--skriv']) == 0
        assert (tmp / 'offer-dz.txt').read_text() == 'orörd' and not (sajt_dz / 'src' / 'styles' / 'design.css').is_symlink()
        shutil.move(str(sajt_dz / 'src' / 'styles'), str(tmp / 'styles-dz')); (sajt_dz / 'src' / 'styles').symlink_to(tmp / 'styles-dz')
        with contextlib.redirect_stdout(io.StringIO()):
            assert dz.main(['dz', '--skriv']) == 1, 'en länkad styles-katalog vägras'
        (sajt_dz / 'src' / 'styles').unlink(); shutil.move(str(tmp / 'styles-dz'), str(sajt_dz / 'src' / 'styles'))
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


def stilpaketet():
    """Referos stilpaket (ägarens uppdrag 2026-10-05 18:53Z, punkt 2): originalet orört och för sig, variablerna i
    Referos namn, Tailwind-temat, DESIGN.md:s import, och bara stilens id och titel till tjänsten."""
    import stilpaket as sp_
    import refero_mcp as rm_
    import design as dz_
    anrop_ = []
    export_ = {'title': 'Provstil', 'northStar': 'Lugn verkstad.', 'description': 'Varm yta.', 'theme': 'light',
               'colors': [{'hex': '#FFF3E7', 'name': 'Canvas', 'role': 'bakgrund'}, {'hex': '#030302', 'name': 'Ink', 'role': 'text'}],
               'components': [{'html': '<style>:root { --color-canvas: #fff3e7; --font-serif: \'Lora\', Georgia, serif; }</style>'}],
               'typography': [{'family': 'EgenSerif', 'source': 'custom', 'substitute': 'Lora', 'role': 'rubriker', 'sizes': '56px', 'weight': '400', 'lineHeight': '1.1'}],
               'typeScale': [{'role': 'body', 'size': 16, 'lineHeight': 1.5, 'letterSpacing': -0.24}],
               'spacing': {'radius': {'cards': '16-24px'}, 'sectionGap': '96-120px', 'pageMaxWidth': '1280px'},
               'elevation': [{'style': 'rgba(0,0,0,.1) 0 4px 8px', 'element': 'kort'}], 'layout': 'Centrerad.', 'imagery': 'Papper.',
               'dos': ['Använd Ink.'], 'donts': ['Ingen svart.']}

    class Klient_:
        def json(self, namn, args):
            anrop_.append((namn, dict(args)))
            if namn == 'refero_search_styles':
                return {'records': [{'uuid': SID, 'preview_url': 'https://images.refero.design/styles/x/%s/preview_0.jpg' % SID, 'url': 'https://exempel.se'}]}
            return json.loads(json.dumps(export_))

        def kalla(self, namn, args):
            anrop_.append((namn, dict(args)))
            return '# Provstil — Style Reference\n'
    SID = '00000000-1111-2222-3333-444444444444'
    spara_bild = rm_.ladda_bild

    def bild_(url, mal, max_byte=0):
        f = Path(str(mal) + '.jpg')
        f.write_bytes(b'\xff\xd8\xff' + url.encode())
        return f
    rm_.ladda_bild = bild_
    try:
        sajt_ = tmp / 'sp-k' / 'sp-kund' / 'sajt'
        sajt_.mkdir(parents=True)
        (sajt_ / 'package.json').write_text('{}')
        r_ = sp_.hamta('sp-kund', SID, klient=Klient_(), underlag=tmp / 'sp-u', sajt=sajt_)
        css_ = Path(r_['css']).read_text()
        assert '--color-canvas: #fff3e7;' in css_ and "--font-serif: 'Lora', Georgia, serif;" in css_ and '--color-ink: #030302;' in css_, css_
        assert '--text-body: 16px;' in css_ and '--text-body--line-height: 1.5;' in css_ and '--radius-cards: 16px;' in css_ and '--width-page: 1280px;' in css_
        assert Path(r_['tema']).read_text().count('@theme {') == 1 and 'fri ersättare: Lora' in Path(r_['beskrivning']).read_text()
        orig_ = Path(r_['original'])
        assert sorted(p_.name for p_ in orig_.iterdir()) == ['ORIGINAL.json', 'STIL.json', 'STIL.md', 'preview_0.jpg', 'preview_1.jpg', 'preview_2.jpg']
        fore_ = {p_.name: p_.read_bytes() for p_ in orig_.iterdir()}
        sp_.hamta('sp-kund', SID, klient=Klient_(), underlag=tmp / 'sp-u', sajt=sajt_)
        assert {p_.name: p_.read_bytes() for p_ in orig_.iterdir()} == fore_, 'samma export: originalet orört'
        export_['colors'][1]['hex'] = '#111111'
        sp_.hamta('sp-kund', SID, klient=Klient_(), underlag=tmp / 'sp-u', sajt=sajt_)
        assert (orig_ / 'tidigare').is_dir() and len(list((orig_ / 'tidigare').iterdir())) == 1, 'en ändrad export: den förra sparas undan'
        assert all(a_ in ({'style_id': SID}, {'style_id': SID, 'response_format': 'md'}, {'query': 'Provstil'}) for _n, a_ in anrop_), anrop_
        v_, fel_ = dz_.las((ROOT / 'kontroller' / 'rokprov' / 'DESIGN.md').read_text())
        v_['import'] = [r_['import']]
        assert not fel_ and not [e_ for e_ in dz_.validera(v_) if 'import' in e_], dz_.validera(v_)
    finally:
        rm_.ladda_bild = spara_bild
    print('stilpaketet ok')


def uppdragsmaterialet():
    """Huvudreferensens stilpaket och Mobbins skärmar per uppdrag (ägarens uppdrag 2026-10-05 18:53Z): ett felaktigt
    stil-id redovisas, samma sökfras blir en fråga, svaren knyts till uppdragen, researchens rapport står kvar, och paketet
    hamnar i kandidatens projekt och i skaparens uppdrag."""
    import inspect
    import kandidater as kd_
    import atelje as at_
    import referenstjanster as rt2_
    import refero_mcp as rm2_
    SID = '00000000-1111-2222-3333-555555555555'
    SID2 = '00000000-1111-2222-3333-666666666666'
    spara_ = (at_.UNDERLAG, at_.KUNDER, rt2_.samla, rm2_.ladda_bild)
    at_.UNDERLAG, at_.KUNDER = tmp / 'um-u', tmp / 'um-k'
    try:
        slug_ = 'um-kund'
        r_ = kd_.rot(slug_)
        r_.mkdir(parents=True)
        (r_ / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {
            'k01': {'titel': 'Ett', 'refero_stil': 'stil-' + SID, 'mobbin_fraga': 'Quote request form'},
            'k02': {'titel': 'Två', 'refero_stil': 'abc', 'mobbin_fraga': 'quote  request FORM'},
            'k03': {'titel': 'Tre', 'refero_stil': '', 'mobbin_fraga': ''},
            'k04': {'titel': 'Fyra', 'refero_stil': SID2, 'mobbin_fraga': ''}}}))
        anrop_ = []

        def samla_(slug, uppdrag, underlag=None, katalog='tjanster', **kw):
            anrop_.append((slug, uppdrag, katalog))
            return None, {'slappta': [], 'tjanster': {'mobbin': {'ok': True, 'bilder': 2, 'anmarkningar': [], 'traffar': [
                {'fraga': 'quote request form', 'fil': 'referenser/uppdrag/mobbin/bilder-x/a.png', 'titel': 'Formulär', 'beskrivning': 'Tre steg.'},
                {'fraga': 'Quote request form, mobile', 'fil': 'referenser/uppdrag/mobbin/bilder-x/c.png', 'titel': 'Mobilen', 'beskrivning': 'y'},
                {'fraga': 'något annat', 'fil': 'referenser/uppdrag/mobbin/bilder-x/b.png', 'titel': 'Annat', 'beskrivning': 'x'}]}}}
        rt2_.samla = samla_

        def bild_(url, mal, max_byte=0):
            f_ = Path(str(mal) + '.jpg')
            f_.write_bytes(b'\xff\xd8\xff')
            return f_
        rm2_.ladda_bild = bild_

        class Klient_:
            def json(self, namn, args):
                if SID2 in json.dumps(args):
                    raise RuntimeError('anslutningen bröts mitt i')
                if namn == 'refero_search_styles':
                    return {'records': [{'uuid': SID, 'preview_url': 'https://images.refero.design/styles/x/%s/preview_0.jpg' % SID}]}
                return {'title': 'Provstil', 'colors': [{'hex': '#fff3e7', 'name': 'Canvas', 'role': 'yta'}],
                        'components': [{'html': '<style>:root { --color-canvas: #fff3e7; }</style>'}]}

            def kalla(self, namn, args):
                return '# Provstil\n'
        sammanf_ = kd_.uppdragsmaterial(slug_, klient=Klient_())
        # svaret som inte ekar frasen ordagrant knyts ändå (ordöverlapp), en stil som faller stoppar inte de andra (fynd 12)
        assert sammanf_ == {'k01': {'stil': True, 'mobbin': 2}, 'k02': {'stil': False, 'mobbin': 2}, 'k03': {'stil': False, 'mobbin': 0},
                            'k04': {'stil': False, 'mobbin': 0}}, sammanf_
        assert len(anrop_) == 1 and anrop_[0][2] == 'uppdrag' and [f_['fraga'] for f_ in anrop_[0][1]['fragor']] == ['Quote request form'], anrop_
        assert 'Ett' not in json.dumps(anrop_) and all(f_['syfte'] == 'uppdragens uppgifter' for f_ in anrop_[0][1]['fragor']), 'bara frasen går till Mobbin'
        mat_ = json.loads((r_ / kd_.UPPDRAGSMATERIAL).read_text())['kandidater']
        assert mat_['k01']['stil']['id'] == SID and mat_['k02']['stil']['fel'] and mat_['k02']['mobbin'][0]['fil'] == 'underlag/um-kund/referenser/uppdrag/mobbin/bilder-x/a.png'
        assert mat_['k04']['stil']['fel'].startswith('RuntimeError: anslutningen bröts'), mat_['k04']
        assert not any(x_['fil'].endswith('b.png') for k_ in mat_.values() for x_ in k_.get('mobbin') or []), 'en annan fras knyts inte'
        (kd_.ksajt(slug_, 'k01')).mkdir(parents=True)
        (kd_.ksajt(slug_, 'k01') / 'package.json').write_text('{}')
        paket_ = kd_.stilpaket_i_projekt(slug_, 'k01')
        assert paket_ and Path(paket_['css']).is_file() and '--color-canvas: #fff3e7;' in Path(paket_['css']).read_text()
        assert kd_.stilpaket_i_projekt(slug_, 'k02') is None and kd_.stilpaket_i_projekt(slug_, 'k03') is None
        rad1_, rad2_, rad3_ = (kd_.uppdragsmaterial_rader(slug_, k_) for k_ in ('k01', 'k02', 'k03'))
        assert any('stilpaket ur Refero (Provstil)' in x_ for x_ in rad1_) and any('a.png: Formulär. Tre steg.' in x_ for x_ in rad1_) \
            and any('rubriken "Mobbin"' in x_ for x_ in rad1_), rad1_
        assert any('kunde inte hämtas' in x_ for x_ in rad2_) and rad3_ == [], (rad2_, rad3_)
        assert {'refero_stil', 'mobbin_fraga'} <= set(kd_.PLAN_SCHEMA['properties']['kandidater']['items']['required'])
        assert 'uppdragsmaterial_rader(slug, kid)' in inspect.getsource(kd_.skiss_prompt) and 'uppdragsmaterial_rader(slug, kid)' in inspect.getsource(kd_.skapar_prompt)
        assert "'refero_stil', 'mobbin_fraga')" in inspect.getsource(kd_.planprovning), 'stilen och den sökta frasen är låsta'
        assert kd_.stilid('STIL-' + SID.upper()) == SID and kd_.stilid('abc') is None
    finally:
        at_.UNDERLAG, at_.KUNDER, rt2_.samla, rm2_.ladda_bild = spara_
    print('uppdragsmaterialet ok')


def gammal_styrning():
    """Rensningen inför Nortropic 2.0 (ägarens uppdrag 2026-10-05 ~21:11Z): ersatta beslut och gamla kundsmakdomar når
    inga agenter, inte heller genom metodens utdrag, mallen eller en körnings cache; en återinförd regel fångas."""
    import styrning as sty_
    fynd_ = sty_.prova()
    assert not fynd_, ['%s:%s %s' % (x['kalla'], x['rad'], x['vad']) for x in fynd_[:8]]
    for rad_ in ('- Värdena är startpunkter. Ägarens domar i `LARDOMAR.md` gäller före allt.', 'Sidhuvud på en rad (ägarens A/B 2026-10-02).',
                 'Ägarens domar över tidigare byggen är exempel på vad ägaren värderar.', 'Typsnittet godtogs (ägarens dom L2).',
                 'Använd inga andra bilder.', 'Telefonnumret som tel-länk i sidhuvudet på varje sida.'):
        assert sty_.fynd_i(rad_, 'prov'), rad_
    assert not sty_.fynd_i('Ersatt 2026-10-05: "Telefonnumret som tel-länk i sidhuvudet på varje sida"', 'prov'), 'märkt historik räknas inte'
    rot_ = tmp / 'sty-rot'
    (rot_ / 'underlag' / 'sty-kund' / 'atelje' / 'metod').mkdir(parents=True)
    (rot_ / 'underlag' / 'sty-kund' / 'atelje' / 'metod' / 'METOD-skiss.md').write_text('Ägarens domar i LARDOMAR.md gäller före allt.\n')
    (rot_ / 'underlag' / 'sty-kund' / 'UPPTAGNA-VAL.md').write_text('Ägaren godtog Archivo för målaren i dom L2.\n')
    cache_ = sty_.prova('sty-kund', root=rot_, med_metod=False)
    # en äldre UPPTAGNA-VAL.md (utan versionen) läses aldrig av agenterna och räknas inte (granskningen av r73, N1)
    assert {Path(x['kalla']).name for x in cache_} == {'METOD-skiss.md'} and all(x.get('cache') and 'cache' in x['vad'] for x in cache_), cache_
    import upptagna_val as uv_sty
    (rot_ / 'underlag' / 'sty-kund' / 'UPPTAGNA-VAL.md').write_text('<!-- %s -->\nÄgaren godtog Archivo för målaren i dom L2.\n' % uv_sty.VERSION)
    cache_ = sty_.prova('sty-kund', root=rot_, med_metod=False)
    assert {Path(x['kalla']).name for x in cache_} == {'METOD-skiss.md'}, 'utan ett uttryckligt urval läses UPPTAGNA-VAL.md inte (ren start 2026-10-08): %s' % cache_
    import urval as uv_urval
    uv_urval.fil('sty-kund', rot_ / 'underlag').write_text(json.dumps({'schema': 1, 'historik': {'upptagna_val': True}}))
    cache_ = sty_.prova('sty-kund', root=rot_, med_metod=False)
    # den aktuella läses av agenterna som den står: dess fynd är inte cache och stoppar en start (granskningen av r74, L4)
    assert {Path(x['kalla']).name for x in cache_ if x.get('cache')} == {'METOD-skiss.md'}, cache_
    assert {Path(x['kalla']).name for x in cache_ if not x.get('cache')} == {'UPPTAGNA-VAL.md'}, cache_
    # agenterna får inte läsa ägarens domar över tidigare byggen eller andra kunders mappar
    import atelje as at_s
    assert {'Read(./LARDOMAR.md)', 'Read(./underlag/LARDOMAR-original.md)'} <= set(at_s.NEKAS)
    spara_s = (at_s.KUNDER, at_s.UNDERLAG)
    at_s.KUNDER, at_s.UNDERLAG = tmp / 'sty-k', tmp / 'sty-u'
    try:
        for d_ in ('sty-k/egen', 'sty-k/annan', 'sty-u/egen', 'sty-u/annan', 'sty-u/startkontroll'):
            (tmp / d_).mkdir(parents=True)
        assert at_s.andra_kunder_nekas('egen') == [
            'Read(//%s/**)' % str(at_s.UNDERLAG / 'kundstart').strip('/'),
            'Read(./kunder/annan/**)', 'Read(./underlag/annan/**)'], at_s.andra_kunder_nekas('egen')
        assert at_s.andra_kunder_nekas(None) == []
        args_s = at_s.session_args(['Read'], None, 10, 'm', 'high', (), 'egen')
        assert 'Read(./kunder/annan/**)' in args_s and 'Read(./LARDOMAR.md)' in args_s
    finally:
        at_s.KUNDER, at_s.UNDERLAG = spara_s
    # en upptagna-val-fil från före rensningen läses inte
    import upptagna_val as uv_s
    assert uv_s.VERSION and 'Archivo' not in Path(uv_s.__file__).read_text()
    print('gammal styrning ok')


gammal_styrning()


uppdragsmaterialet()


def referensjamforelsen():
    """Huvudreferensen bredvid förslaget (ägarens uppdrag 2026-10-05 18:53Z, punkt 7): referensens fångade startsida hittas
    genom Bildval-raderna (startsidan 01-… före den utpekade undersidan), annars genom uppdragets bilder i referensens
    katalog. Skaparens korta redovisning (ägarens uppdrag 2026-10-06, punkt 8) är RIKTNING.md:s fyra rubriker, och en
    rubrik som saknas eller är tom sägs; jämförelsen och redovisningen följer med för varje förslag från början, panelens
    granskning och titlarna först efter ägarens första beslut; mellanbredden 1280 visas när den finns."""
    import kandidater as kd_
    import atelje as at_
    import skapande as sk_
    spara_ = (at_.UNDERLAG, at_.KUNDER)
    at_.UNDERLAG, at_.KUNDER = tmp / 'rj-u', tmp / 'rj-k'
    try:
        slug_ = 'rj-kund'
        u_ = at_.UNDERLAG / slug_
        ref_ = u_ / 'referenser' / 'paket-v05'
        for kat_ in ('tekt/01-start', 'tekt/02-process', 'cox/01-start'):
            (ref_ / kat_).mkdir(parents=True)
            for v_ in ('vy-390-forsta', 'vy-1440-forsta', 'vy-390-hela', 'vy-1440-hela', 'vy-1440-ruta-04'):
                (ref_ / kat_ / (v_ + '.png')).write_bytes(b'png')
        (ref_ / 'cox' / '01-start' / 'vy-390-hela.png').unlink()
        (u_ / 'REFERENSER.md').write_text('# Referenser\n\n## Tekt — bransch\n\nBildval: referenser/paket-v05/tekt/02-process/vy-1440-ruta-04.png — '
                                          'skedena — Fråga: läses skedena?\n\n## Cox — hantverk\n\nIngen bildvalsrad.\n')
        kd_.satt_status(slug_, 'k01', 'klar', 'prov', huvudreferens='Tekt — bygget i skeden', hypotes='Tekts skeden visar besökaren hur jobbet går till.')
        (kd_.kdir(slug_, 'k01') / 'RIKTNING.md').write_text(
            'Huvudreferens: Tekt — bygget i skeden\n\n## Idén\n\nBygget i skeden: besökaren ser hur jobbet går till.\n\n## Referenslås\n\n'
            'Bevaras: ramarna.\n\n## Referenser\n\n- referenser/paket-v05/tekt/01-start (öppnad)\n\n## Överfört och avvikelser\n\n### Överfört\n\n'
            '- etiketten till vänster\n\n### Medvetna avvikelser\n\n- mörkare text: kontrasten\n\n## Kvarvarande svagheter\n\n## Varv 1\n\nrubriken\n')
        j_ = kd_.referensjamforelse(slug_, 'k01')
        start_ = ref_ / 'tekt' / '01-start'
        assert j_['referens']['sida'] == kd_.rel(start_) and j_['referens']['390-forsta'] == kd_.rel(start_ / 'vy-390-forsta.png'), j_['referens']
        assert j_['referens']['1440-hela'] == kd_.rel(start_ / 'vy-1440-hela.png') and set(j_) == {'referens', 'saknas', 'egen'} and j_['egen'] is False, j_
        # den korta redovisningen: rubrikerna i ägarens ordning, utan rubrikraden; en tom rubrik är '', aldrig ifylld
        red_ = kd_.kort_redovisning(slug_, 'k01')
        assert [x_['rubrik'] for x_ in red_] == list(kd_.REDOVISNINGSRUBRIKER) == ['Idén', 'Referenser', 'Överfört och avvikelser', 'Kvarvarande svagheter'], red_
        red_ = {x_['rubrik']: x_['avsnitt'] for x_ in red_}
        assert red_['Idén'] == 'Bygget i skeden: besökaren ser hur jobbet går till.' and red_['Referenser'] == '- referenser/paket-v05/tekt/01-start (öppnad)', red_
        assert red_['Överfört och avvikelser'].startswith('### Överfört') and '### Medvetna avvikelser' in red_['Överfört och avvikelser'], red_
        assert 'Varv 1' not in red_['Överfört och avvikelser'] and 'Bevaras' not in red_['Referenser'] and red_['Kvarvarande svagheter'] == '', red_
        # utan bildvalsrader: uppdragets bilder i referensens katalog; en saknad vy är None, aldrig en annan bild
        kd_.satt_status(slug_, 'k02', 'klar', 'prov', huvudreferens='Cox')
        (kd_.kdir(slug_, 'k02') / 'UPPDRAG.md').write_text('# Uppdrag\n\n## Referensbilder\n\n- underlag/rj-kund/referenser/paket-v05/cox/01-start/vy-1440-ruta-04.png\n'
                                                          '- underlag/rj-kund/referenser/paket-v05/tekt/02-process/vy-1440-ruta-04.png\n')
        (kd_.kdir(slug_, 'k02') / 'RIKTNING.md').write_text('## Referenslås\n\nBevaras: väggen.\n')
        j2_ = kd_.referensjamforelse(slug_, 'k02')
        assert j2_['referens']['sida'] == kd_.rel(ref_ / 'cox' / '01-start') and j2_['referens']['390-hela'] is None, j2_['referens']
        # referenslåset är ingen redovisning: utan de fyra rubrikerna saknas alla, och inget fylls i
        assert [x_['avsnitt'] for x_ in kd_.kort_redovisning(slug_, 'k02')] == [None] * 4
        kd_.satt_status(slug_, 'k03', 'klar', 'prov', huvudreferens='Okänd sajt (okand.se)')
        j3_ = kd_.referensjamforelse(slug_, 'k03')
        assert j3_['referens'] is None and 'ingen fångad sida' in j3_['saknas'], 'en referens utan fångad sida säger varför jämförelsen fattas'
        # namnen som skaparna faktiskt skriver (domänen i parentes), en referens utan bildvalsrader, och ett äldre paket utan
        # numrerade sidor där adressen avgör vilken sida som är startsidan (granskningen av r73, A1 och A3)
        for kat_, adr_ in (('sebastian-cox/01-start', 'https://sebastiancox.co.uk/'), ('gammal/projects', 'https://gammal.se/projects/'),
                           ('gammal/start', 'https://gammal.se/')):
            (ref_ / kat_).mkdir(parents=True, exist_ok=True)
            for v_ in ('vy-390-forsta', 'vy-1440-forsta', 'vy-1440-ruta-02'):
                (ref_ / kat_ / (v_ + '.png')).write_bytes(b'png')
            (ref_ / kat_ / 'INSPEKTION.json').write_text(json.dumps({'adress': adr_}))
        (u_ / 'REFERENSER.md').write_text((u_ / 'REFERENSER.md').read_text() + '\n## Gammal — bransch\n\nBildval: referenser/paket-v05/gammal/projects/'
                                          'vy-1440-ruta-02.png — projekten — Fråga: bär projekten?\n')
        # diakriter, en parentes också i rubriken, den platta layouten från byggena före paketen, och en sida utan
        # INSPEKTION.json som aldrig blir startsida (granskningen av r74, M2 och L2)
        for kat_ in ('ostra-snickeriet/01-start', 'tekt-arch/01-start', 'tekt-arch/02-process', 'gammal2/projects', 'gammal2/start'):
            (ref_ / kat_).mkdir(parents=True, exist_ok=True)
            for v_ in ('vy-390-forsta', 'vy-1440-forsta', 'vy-1440-ruta-02'):
                (ref_ / kat_ / (v_ + '.png')).write_bytes(b'png')
        (ref_ / 'gammal2' / 'start' / 'INSPEKTION.json').write_text(json.dumps({'adress': 'https://gammal2.se/'}))
        platt_ = u_ / 'referenser' / 'platt'
        platt_.mkdir(parents=True)
        for v_ in ('vy-390-forsta', 'vy-1440-forsta', 'vy-390-hela'):
            (platt_ / (v_ + '.png')).write_bytes(b'png')
        (u_ / 'REFERENSER.md').write_text((u_ / 'REFERENSER.md').read_text()
                                          + '\n## Tekt Architects (tekt.com.au) — bransch\n\nBildval: referenser/paket-v05/tekt-arch/02-process/vy-1440-ruta-02.png — '
                                            'skedena — Fråga: läses de?\n\n## Gammal2 — bransch\n\nBildval: referenser/paket-v05/gammal2/projects/vy-1440-ruta-02.png — '
                                            'projekten — Fråga: bär de?\n\n## Platt — hantverk\n\nBildval: referenser/platt/vy-390-forsta.png — första vyn — Fråga: bär den?\n')
        for kid_, namn_, sida_ in (('k05', 'Tekt (tekt.com.au)', 'paket-v05/tekt/01-start'), ('k06', 'Sebastian Cox (sebastiancox.co.uk)', 'paket-v05/sebastian-cox/01-start'),
                                   ('k07', 'Gammal — projekten först', 'paket-v05/gammal/start'), ('k08', 'Östra Snickeriet (ostrasnickeriet.se)', 'paket-v05/ostra-snickeriet/01-start'),
                                   ('k09', 'Tekt Architects (tekt.com.au)', 'paket-v05/tekt-arch/01-start'), ('k10', 'Gammal2', 'paket-v05/gammal2/start'),
                                   ('k11', 'Platt (platt.se)', 'platt')):
            kd_.satt_status(slug_, kid_, 'klar', 'prov', huvudreferens=namn_)
            jx_ = kd_.referensjamforelse(slug_, kid_)
            assert jx_['referens'] and jx_['referens']['sida'] == kd_.rel(u_ / 'referenser' / sida_), (namn_, jx_)
            shutil.rmtree(kd_.kdir(slug_, kid_))
        # synligheten bland flera förslag före ägarens första beslut: jämförelsen, redovisningen och hypotesen som den
        # skrevs för varje förslag; titeln, granskningen och hela anteckningarna inte (BESLUT.md 2026-10-05, punkt 1)
        (kd_.rot(slug_) / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': '2026-10-06T00:00:00Z', 'antal': 3, 'kandidater': {}}))
        (kd_.rot(slug_) / 'STATUS.json').write_text(json.dumps({'kandidatflode': True, 'steg': 'klar_for_bedomning', 'lage': 'ny'}))
        (kd_.kdir(slug_, 'k01') / 'KRITIK.json').write_text(json.dumps({'niva': 'over', 'helhet': 'internt betyg'}))
        (kd_.kdir(slug_, 'k01') / 'bilder' / 'start').mkdir(parents=True)
        (kd_.kdir(slug_, 'k01') / 'bilder' / 'start' / 'vy-1280-forsta.png').write_bytes(b'png')
        blind_ = {k_['id']: k_ for k_ in kd_.sammanstall(slug_)}
        assert {k_: bool(v_['referensjamforelse']['referens']) for k_, v_ in blind_.items()} == {'k01': True, 'k02': True, 'k03': False}, 'jämförelsen för varje förslag'
        assert all(len(v_['redovisning']) == 4 and not {'titel', 'kritik', 'riktning'} & set(v_) for v_ in blind_.values()), 'redovisningen från början; titeln, granskningen och anteckningarna inte'
        assert blind_['k01']['hypotes'].startswith('Tekts skeden'), 'referensen är synlig för varje förslag: hypotesen visas som den skrevs'
        # mellanbredden 1280 när den fotograferats, och dashboardens filfilter släpper fram den före första beslutet
        assert blind_['k01']['bilder']['1280-forsta'] == kd_.rel(kd_.kdir(slug_, 'k01') / 'bilder' / 'start' / 'vy-1280-forsta.png') and blind_['k02']['bilder']['1280-forsta'] is None
        spara_dash_ = (dash.UNDERLAG, dash.KUNDER, dash.ROOT)
        dash.UNDERLAG, dash.KUNDER, dash.ROOT = at_.UNDERLAG, at_.KUNDER, tmp
        try:
            k1280_ = 'underlag/%s/atelje/kandidater/k01/bilder/start/vy-1280-%s.png'
            assert dash.fil_tillaten(k1280_ % (slug_, 'forsta')) and dash.fil_tillaten(k1280_ % (slug_, 'hela')) and not dash.fil_tillaten(k1280_.replace('1280', '1366') % (slug_, 'forsta'))
            assert not dash.fil_tillaten('underlag/%s/atelje/kandidater/k01/RIKTNING.md' % slug_), 'anteckningarna som fil först efter första beslutet'
            # vyns data: rubrikerna som finns, saknas eller är tomma, i HTML; granskningen döljs fortfarande
            vy_ = {k_['id']: k_ for k_ in dash.prototyp(slug_)['kandidater']}
            r1_ = {x_['rubrik']: x_ for x_ in vy_['k01']['redovisning']}
            assert r1_['Idén']['finns'] and 'Bygget i skeden' in r1_['Idén']['html'] and 'avsnitt' not in r1_['Idén'], r1_['Idén']
            assert r1_['Kvarvarande svagheter'] == {'rubrik': 'Kvarvarande svagheter', 'finns': True, 'html': ''}, r1_['Kvarvarande svagheter']
            assert '<h4>Medvetna avvikelser</h4>' in r1_['Överfört och avvikelser']['html'] and 'kritik' not in vy_['k01'], r1_['Överfört och avvikelser']
            assert [x_['finns'] for x_ in vy_['k02']['redovisning']] == [False] * 4 and vy_['k03']['referensjamforelse']['saknas'], vy_['k02']
            # efter ägarens första beslut följer titeln och granskningen; jämförelsen och redovisningen står kvar
            (u_ / 'DESIGNDOMAR.jsonl').write_text(json.dumps({'tid': '2026-10-06T01:00:00Z', 'kalla': sk_.AGAREN[0], 'beslut': 'valj', 'text': 'x'}) + '\n')
            efter_ = {k_['id']: k_ for k_ in dash.prototyp(slug_)['kandidater']}
            assert efter_['k01']['kritik']['niva'] == 'over' and all('titel' in v_ and len(v_['redovisning']) == 4 and 'referensjamforelse' in v_ for v_ in efter_.values())
            (u_ / 'DESIGNDOMAR.jsonl').unlink()
        finally:
            dash.UNDERLAG, dash.KUNDER, dash.ROOT = spara_dash_
        # vyn: rubrikerna som skaparen skriver är de vyn känner, de tekniska kontrollerna står under en egen rubrik som
        # säger att de inte är ett godkännande, och mobil och dator är förvalet
        vyn_ = (ROOT / 'dashboard' / 'index.html').read_text()
        for r_ in kd_.REDOVISNINGSRUBRIKER:
            assert "'%s': '" % r_ in vyn_, r_
        for krav_ in ('Tekniska kontroller, inget godkännande av designen', 'saknar rubriken', "|| 'par'", 'class="kpar"', 'Kombinera kvaliteter', 'Mellanbredd 1280'):
            assert krav_ in vyn_, krav_
    finally:
        at_.UNDERLAG, at_.KUNDER = spara_
    print('referensjämförelsen och redovisningen ok')


referensjamforelsen()


stilpaketet()


def skisskontrollerna():
    """Ägarens underkännande av skissen 2026-10-06: menyn prövas i verkligt tillstånd (details/summary och aria-expanded,
    elementet hålls före klicket, menybilden bara när menyn öppnades), startsidan fotograferas också i mellanbredden 1280
    där spill markeras, raden Huvudreferens godtar "egen" och flera namn, tal ur kundens bilders filnamn och EXIF-datum är
    belägg, och en kärnfil som metodfilen levererat hel med samma sha räknas som läst i kvittot."""
    import hashlib as hl_s
    import struct as st_s
    import atelje as at_s
    import bildkedja as bk_s
    import forhandsvisa as fh_s
    import kandidater as kd_s
    import kompetens as kp_s
    import metod as md_s
    import prova as pv_s
    spara_ = (at_s.UNDERLAG, at_s.KUNDER, pv_s.bygg_inom_grans, pv_s.kor, pv_s.Server, bk_s.ROOT, bk_s.PROJEKT, fh_s.KUNDER)
    at_s.UNDERLAG, at_s.KUNDER = tmp / 'skk-u', tmp / 'skk-k'
    slug_ = 'skk-kund'
    u_ = at_s.UNDERLAG / slug_
    try:
        # --- (a, b) i webbläsaren: en details-meny öppnas och fotograferas; en knapp som inte öppnar något ger ingen
        # menybild och säger varför; en mobil utan menyknapp där alla länkar syns räknas; en fast datorlayout
        # (412 + 908 px med kanter, som k01) spiller i 1280 men inte i 390 eller 1440
        sajt_ = tmp / 'skk-sajt'
        huvud_ = ('<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>p</title>'
                  '<style>body{margin:0;font:16px sans-serif}.dator{display:none}@media (min-width:1100px){.mobil{display:none}'
                  '.dator{display:flex;gap:20px}.rad{display:grid;grid-template-columns:412px 908px;padding:0 40px 0 80px}}</style></head><body>')
        for sida_, kropp_ in (('details', '<header><a href="/">Firman</a><nav class="dator"><a href="/a/">A</a><a href="/b/">B</a></nav>'
                                          '<details class="mobil"><summary>Meny</summary><nav><a href="/a/">A</a><a href="/b/">B</a></nav></details>'
                                          '</header><main><h1>Rubrik</h1><div class="rad"><p>Etikett</p><p>Innehåll</p></div></main>'),
                              ('dod', '<header><a href="/">Firman</a><button aria-expanded="false" aria-controls="m">Meny</button>'
                                      '<nav id="m" hidden><a href="/a/">A</a><a href="/b/">B</a></nav></header><main><h1>Död meny</h1></main>'),
                              ('alla', '<a href="#i" style="position:absolute;top:-100px">Hoppa till innehållet</a><header><a href="/">Firman</a>'
                                       '<nav><a href="/a/">A</a> <a href="/b/">B</a> <a href="/c/">C</a></nav></header><main id="i"><h1>Alla syns</h1>'
                                       '</main><footer><nav><a href="/d/" hidden>D</a></nav></footer>')):
            (sajt_ / sida_).mkdir(parents=True)
            (sajt_ / sida_ / 'index.html').write_text(huvud_ + kropp_ + '</body></html>')
        srv_, bas_ = server(sajt_)
        try:
            def insp_(sida, vyer):
                ut_ = tmp / ('skk-ut-' + sida)
                r_ = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'inspektera.mjs'), '--adress', bas_ + '/' + sida + '/', '--ut', str(ut_),
                                     '--vyer', vyer, '--tillstand', 'inga', '--meny', kd_s.MENYKNAPP], capture_output=True, text=True, cwd=str(ROOT),
                                    env={k_: v_ for k_, v_ in os.environ.items() if k_ not in ('NWP_SLUG', 'NWP_WEBBTJANST')}, timeout=300)
                assert (ut_ / 'INSPEKTION.json').is_file(), (sida, r_.returncode, r_.stderr[-500:])
                return ut_, json.loads((ut_ / 'INSPEKTION.json').read_text())['vyer']
            ut_d, v_d = insp_('details', '390,1280,1440')
            m_d = v_d['390']['tillstand']['meny']
            assert m_d['knapp'] and m_d['klickad'] and m_d['expanded'] == 'true' and m_d['bild'].endswith('vy-390-meny.png'), m_d
            assert (ut_d / 'vy-390-meny.png').read_bytes() != (ut_d / 'vy-390-forsta.png').read_bytes(), 'menybilden visar den öppna menyn, inte första vyn'
            assert v_d['1280']['spill']['spill'] and not v_d['1440']['spill']['spill'] and not v_d['390']['spill']['spill'], {k_: x_['spill'] for k_, x_ in v_d.items()}
            assert (ut_d / 'vy-1280-forsta.png').is_file() and not (ut_d / 'vy-1280-meny.png').exists() and v_d['1280']['tillstand']['meny']['knapp'] is False
            ut_x, v_x = insp_('dod', '390')
            m_x = v_x['390']['tillstand']['meny']
            assert m_x['klickad'] and m_x['expanded'] == 'false' and 'öppnades inte' in m_x['skal'] and 'bild' not in m_x and not list(ut_x.glob('vy-*-meny.png')), m_x
            assert 'ingen bild: menyn öppnades inte' in (ut_x / 'INSPEKTION.md').read_text()
            ut_a, v_a = insp_('alla', '390')
            m_a = v_a['390']['tillstand']['meny']
            assert m_a['knapp'] is False and m_a['lankar'] == {'totalt': 3, 'synliga': 3, 'dolda': []} and not list(ut_a.glob('vy-*-meny.png')), m_a
        finally:
            srv_.shutdown()
        # skissens snabba kontroll av menyn: en knapp som inte öppnar menyn är en brist; utan knapp med alla länkar synliga
        # är det en upplysning; ett prov som inte kördes eller dolda länkar utan knapp är brister
        assert 'button[aria-expanded="false"]' in kd_s.MENYKNAPP and 'details:not([open]) > summary' in kd_s.MENYKNAPP
        assert kd_s.menyprovet(m_d) == ([], []) and kd_s.menyprovet(m_a) == ([], ['390: ingen menyknapp; navigationens alla 3 länkar syns utan meny'])
        assert 'öppnar ingenting' in kd_s.menyprovet(m_x)[0][0] and 'gick inte att klicka' in kd_s.menyprovet({'knapp': True, 'klickad': False, 'skal': 'täckt'})[0][0]
        assert 'gick inte att avläsa' in kd_s.menyprovet({'knapp': True, 'klickad': True, 'expanded': None})[0][0]
        assert '1 av navigationens 3 länkar syns inte (/c/)' in kd_s.menyprovet({'knapp': False, 'lankar': {'totalt': 3, 'synliga': 2, 'dolda': ['/c/']}})[0][0]
        assert 'prövades inte (Timeout)' in kd_s.menyprovet(None, 'Timeout')[0][0]

        # --- fotograferingen: startsidan i fyra bredder med menyns knapp; spill i 1280 och menyn markeras; datumen ur
        # bildernas filnamn och EXIF är belagda; "Huvudreferens: egen — …" godtas ---
        (u_ / 'bilder').mkdir(parents=True)
        (u_ / 'bilder' / 'se-20210628_110636.jpg').write_bytes(b'jpg')
        datum_ = b'2021:07:07 10:00:00\x00'
        tiff_ = (b'II*\x00' + st_s.pack('<I', 8) + st_s.pack('<H', 1) + st_s.pack('<HHII', 0x8769, 4, 1, 26) + st_s.pack('<I', 0)
                 + st_s.pack('<H', 1) + st_s.pack('<HHII', 0x9003, 2, len(datum_), 44) + st_s.pack('<I', 0) + datum_)
        app1_ = b'Exif\x00\x00' + tiff_
        (u_ / 'bilder' / 'tak.jpg').write_bytes(b'\xff\xd8\xff\xe1' + st_s.pack('>H', 2 + len(app1_)) + app1_ + b'\xff\xd9')
        import bilddatum as bd_s
        assert bd_s.datum(u_ / 'bilder' / 'tak.jpg')['datum'] == '2021-07-07 10:00', bd_s.datum(u_ / 'bilder' / 'tak.jpg')
        kid_ = 'k01'
        pages_ = kd_s.ksajt(slug_, kid_) / 'src' / 'pages'
        pages_.mkdir(parents=True)
        (pages_ / 'index.astro').write_text('<h1>Skiss</h1><p>Bygget 28 juni och 7 juli. Med 25 år i branschen och 7 snickare.</p>')
        kd_s.kdir(slug_, kid_).mkdir(parents=True)
        (kd_s.kdir(slug_, kid_) / 'RIKTNING.md').write_text('Huvudreferens: egen — kundens egna foton bär sidan\n')
        meny_, inspekterat_ = [m_x], []

        def bygg_(sajt, timeout=900):
            (Path(sajt) / 'dist').mkdir(parents=True, exist_ok=True)
            (Path(sajt) / 'dist' / 'index.html').write_text((Path(sajt) / 'src' / 'pages' / 'index.astro').read_text())
            return 0, 'byggt'

        def kor_(cmd, cwd=None, timeout=900):
            cmd = [str(x_) for x_ in cmd]
            if cmd[1].endswith('inspektera.mjs'):
                inspekterat_.append(cmd)
                ut_ = Path(cmd[cmd.index('--ut') + 1])
                ut_.mkdir(parents=True, exist_ok=True)
                vyer_ = {}
                for vy_ in cmd[cmd.index('--vyer') + 1].split(','):
                    for s_ in ('forsta', 'hela'):
                        (ut_ / ('vy-%s-%s.png' % (vy_, s_))).write_bytes(b'png')
                    vyer_[vy_] = {'konsol': [], 'spill': {'spill': vy_ == '1280'}, 'tillstand': {}}
                if meny_[0] is not None and '--meny' in cmd:
                    for vy_m in ('390', '768'):  # inspektionen prövar menyn i varje bredd; kontrollen läser 390 och 768
                        if vy_m in vyer_:
                            vyer_[vy_m]['tillstand']['meny'] = meny_[0]
                (ut_ / 'INSPEKTION.json').write_text(json.dumps({'vyer': vyer_}))
                return 0, ''
            if cmd[1].endswith('axe.mjs'):
                ut_ = Path(next(x_ for x_ in cmd if x_.startswith('--ut='))[5:])
                ut_.mkdir(parents=True, exist_ok=True)
                (ut_ / 'axe.json').write_text(json.dumps({'allvarliga': 0, 'totalt': 0, 'axeVersion': 'x', 'rader': []}))
                return 0, ''
            raise AssertionError(cmd)

        class Srv_:
            url = 'http://127.0.0.1:9'

            def __init__(self, dist):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass
        pv_s.bygg_inom_grans, pv_s.kor, pv_s.Server = bygg_, kor_, Srv_
        st_ = kd_s.fotografera(slug_, kid_, skiss=True)
        k_ = inspekterat_[0]
        assert k_[k_.index('--vyer') + 1] == '390,768,1280,1440' and k_[k_.index('--meny') + 1] == kd_s.MENYKNAPP, k_
        assert st_['status'] == 'klar' and '/ 1280: sidled-spill' in st_['brister'] and any('menyns knapp öppnar ingenting' in b_ for b_ in st_['brister']), st_['brister']
        # datumen ur bildernas filnamn (28 juni) och EXIF (7 juli) är belagda som datum; 25 och ett 7 utan datum är det inte
        assert 'siffror i texten som inte finns i underlaget: 25, 7' in st_['brister'], st_['brister']
        assert not any('Huvudreferens' in b_ for b_ in st_['brister']) and st_['huvudreferens'] == 'egen' and st_['huvudreferens_i_researchen'] is None, st_
        assert st_['upplysningar'] == [] and not (kd_s.kdir(slug_, kid_) / 'bilder' / 'start' / 'vy-390-meny.png').exists()
        meny_[0] = m_a
        st_ = kd_s.fotografera(slug_, kid_, skiss=True)
        assert not any('meny' in b_ for b_ in st_['brister']) and st_['upplysningar'] == ['%s: ingen menyknapp; navigationens alla 3 länkar syns utan meny' % v_m
                                                                                         for v_m in ('390', '768')], st_
        meny_[0] = None  # inspektionen gav inget menyprov: ingen frånvaro av brister
        assert any('menyn prövades inte' in b_ for b_ in kd_s.fotografera(slug_, kid_, skiss=True)['brister'])
        meny_[0] = m_a
        kd_s.fotografera(slug_, kid_, skiss=True)
        # underlaget till dashboarden (sammanstall; vyn själv görs i ett annat spår) och rapporten: mellanbredden och upplysningen
        post_ = next(k_ for k_ in kd_s.sammanstall(slug_) if k_['id'] == kid_)
        assert str(post_['bilder']['1280-forsta']).endswith('bilder/start/vy-1280-forsta.png') and post_['upplysningar'], post_
        rd_ = kd_s.redovisa_skiss(slug_, {}).read_text()
        assert '## Upplysningar ur de snabba kontrollerna' in rd_ and 'navigationens alla 3 länkar syns utan meny' in rd_, rd_[:600]

        # --- (c) raden Huvudreferens: "egen" och flera namn; namnen prövas var för sig mot researchen och referenserna ---
        d2_ = kd_s.kdir(slug_, 'k02')
        d2_.mkdir(parents=True)
        for rad_, vant_ in (('Huvudreferens: egen — kundens egna foton bär sidan', ('egen', True, [])),
                            ('Huvudreferens: Tekt (tekt.com.au, paket-v01/tekt/01-start) och Cox — rytmen',
                             ('Tekt (tekt.com.au, paket-v01/tekt/01-start) och Cox', False, ['Tekt (tekt.com.au, paket-v01/tekt/01-start)', 'Cox'])),
                            ('- **Huvudreferens:** Påhittad, Cox — x', ('Påhittad, Cox', False, ['Påhittad', 'Cox']))):
            (d2_ / 'RIKTNING.md').write_text(rad_ + '\n\nHypotes: x\n')
            hr_ = kd_s.riktningens_referens(slug_, 'k02')
            assert hr_ and (hr_['namn'], hr_['egen'], hr_['namnen']) == vant_, (rad_, hr_)
        (u_ / 'REFERENSER.md').write_text('# Referenser\n\n## Tekt — bransch\n\n## Cox — hantverk\n')
        for rad_, vant_ in (('Tekt (tekt.com.au, paket-v01/tekt/01-start) och Cox', True), ('Påhittad, Cox', False), ('egen', None)):
            (d2_ / 'RIKTNING.md').write_text('Huvudreferens: %s — x\n' % rad_)
            assert kd_s.huvudreferenserna_i_researchen(slug_, kd_s.riktningens_referens(slug_, 'k02')) is vant_, rad_
        ref_ = u_ / 'referenser' / 'paket-v01' / 'cox' / '01-start'
        ref_.mkdir(parents=True)
        for v_ in ('vy-390-forsta', 'vy-1440-forsta'):
            (ref_ / (v_ + '.png')).write_bytes(b'png')
        kd_s.satt_status(slug_, 'k02', 'klar', 'prov', huvudreferens='Påhittad, Cox', hypotes='En egen tidslinje, egentligen bara foton, som Cox')
        r2_, s2_ = kd_s.referenssida(slug_, 'k02')
        assert r2_ and r2_['sida'] == kd_s.rel(ref_) and r2_['namn'] == 'Påhittad, Cox', (r2_, s2_)
        # hypotesen visas som den skrevs: referenserna syns per förslag, hopfällda efter bilderna (ägarens uppdrag 2026-10-06, punkt 8)
        assert next(k_ for k_ in kd_s.sammanstall(slug_) if k_['id'] == 'k02')['hypotes'] == 'En egen tidslinje, egentligen bara foton, som Cox'
        kd_s.satt_status(slug_, 'k02', 'klar', 'prov', huvudreferens='egen')
        j2_ = kd_s.referensjamforelse(slug_, 'k02')
        assert j2_['referens'] is None and j2_['egen'] and 'egen riktning' in j2_['saknas'], j2_
        assert next(k_ for k_ in kd_s.sammanstall(slug_) if k_['id'] == 'k02')['hypotes'] == 'En egen tidslinje, egentligen bara foton, som Cox'

        # --- förhandsvisningen säger varför menybilden saknas ---
        fh_s.KUNDER = tmp / 'skk-fh'
        fs_ = fh_s.KUNDER / slug_ / 'sajt'
        (fs_ / 'dist').mkdir(parents=True)
        (fs_ / 'package.json').write_text('{}')
        (fs_ / 'dist' / 'index.html').write_text('<h1>x</h1>')
        pv_s.bygg_inom_grans = lambda sajt, timeout=900: (0, 'byggt')
        meny_[0] = m_x
        rc_, text_, _ = fh_s.forhandsvisa(slug_, ut=tmp / 'skk-fh-ut', meny=kd_s.MENYKNAPP)
        assert rc_ == 0 and '390 px meny: klickad True, expanded false; ingen bild: menyn öppnades inte' in text_, text_

        # --- (e) kvittot: en kärnfil som metodfilen levererat hel, med samma sha, är läst när metodfilen lästs hel ---
        bk_s.ROOT = ROOT
        proj_ = tmp / 'skk-projekt' / '-x'
        proj_.mkdir(parents=True)
        bk_s.PROJEKT = proj_.parent
        fore_ = next(f_['fil'] for f_ in md_s.leverera('skiss', tmp / 'skk-metod')['filer'] if f_['del'] == 'före')
        rubrik_ = re.search(r'^### kunskap/bild\.md · rad 1–\d+ · sha [0-9a-f]{12}$', fore_.read_text(), re.M)
        assert rubrik_ and 'kunskap/bild.md' in kp_s.lasfiler('skapa'), 'METOD-skiss.md bär kunskap/bild.md hel, och den är skaparens kärna'
        src_ = 'kunder/%s/kandidater/k01/sajt/src/' % slug_
        n_ = [0]

        def transkript_(steg):
            sid_ = '00000000-0000-4000-8000-%012d' % (9000 + n_[0])
            n_[0] += 1
            rader_ = []
            for i_, (namn_, in_) in enumerate(steg):
                rader_.append(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'u%d' % i_, 'name': namn_, 'input': in_}]}}))
                rader_.append(json.dumps({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'u%d' % i_, 'content': 'ok'}]}}))
            (proj_ / (sid_ + '.jsonl')).write_text('\n'.join(rader_) + '\n')
            return sid_
        ovriga_ = [('Read', {'file_path': str(ROOT / f_)}) for f_ in kp_s.lasfiler('skapa') if f_ != 'kunskap/bild.md']
        skriv_ = ('Write', {'file_path': str(ROOT / src_ / 'pages' / 'index.astro')})

        def kvitto_(*metodlasning):
            return kp_s.kvitto([transkript_(list(metodlasning) + ovriga_ + [skriv_])], 'skapa', skrivprefix=src_)
        kv_ = kvitto_(('Read', {'file_path': str(fore_)}))
        assert kv_['verifierad'] and not kv_['saknas'] and 'kunskap/bild.md' in kv_['fore_forsta_andring'], kv_
        assert kvitto_(('Read', {'file_path': str(fore_), 'limit': 50}))['saknas'] == ['kunskap/bild.md'], 'en del av metodfilen räcker inte'
        bild_ = (ROOT / 'kunskap' / 'bild.md').read_text(encoding='utf-8')
        for namn_, andra_ in (('sha', lambda t: t.replace(rubrik_.group(0), rubrik_.group(0)[:-12] + '000000000000')),  # en äldre leverans
                              ('rader', lambda t: t.replace(rubrik_.group(0), rubrik_.group(0).replace('rad 1–', 'rad 2–')))):  # inte hela filen
            k_ = tmp / ('skk-metod-' + namn_)
            k_.mkdir()
            assert andra_(fore_.read_text()) != fore_.read_text()
            (k_ / 'METOD-skiss.md').write_text(andra_(fore_.read_text()))
            assert kvitto_(('Read', {'file_path': str(k_ / 'METOD-skiss.md')}))['saknas'] == ['kunskap/bild.md'], namn_
        # ett utdrag som fortsätter i nästa fil räknas först när båda lästs hela
        k_ = tmp / 'skk-metod-delad'
        k_.mkdir()
        (k_ / 'METOD-skiss.md').write_text('# Metoden: Skiss (fil 1 av 2)\n\n%s\n\n%s\n' % (rubrik_.group(0), '\n'.join(bild_.splitlines()[:40])))
        (k_ / 'METOD-skiss-2.md').write_text('# Metoden: Skiss (fil 2 av 2)\n\n%s (fortsättning)\n%s\n' % (rubrik_.group(0), '\n'.join(bild_.splitlines()[40:])))
        assert kvitto_(('Read', {'file_path': str(k_ / 'METOD-skiss.md')}))['saknas'] == ['kunskap/bild.md'], 'bara första delen'
        assert not kvitto_(('Read', {'file_path': str(k_ / 'METOD-skiss.md')}), ('Read', {'file_path': str(k_ / 'METOD-skiss-2.md')}))['saknas']
        # ett alternativ som bara stod i metodfilen är inte valt: valet är sessionens egen läsning
        alt_ = kp_s.valbara('skapa')[0]
        alt_text_ = (ROOT / alt_).read_text(encoding='utf-8')
        k_ = tmp / 'skk-metod-alt'
        k_.mkdir()
        (k_ / 'METOD-skiss.md').write_text('### %s · rad 1–%d · sha %s\n\n%s\n' % (alt_.replace('.claude/skills/', '', 1), len(alt_text_.splitlines()),
                                                                                hl_s.sha256(alt_text_.encode('utf-8')).hexdigest()[:12], alt_text_))
        ml_ = bk_s.metodlasning(transkript_([('Read', {'file_path': str(k_ / 'METOD-skiss.md')})]), [alt_])
        assert ml_['fore'] == [alt_] and ml_['via_metod'] == [alt_], ml_
        assert kvitto_(('Read', {'file_path': str(k_ / 'METOD-skiss.md')}))['valda'] == [], 'ett levererat alternativ är inget val'
        assert kvitto_(('Read', {'file_path': str(ROOT / alt_)}))['valda'] == [alt_]
    finally:
        at_s.UNDERLAG, at_s.KUNDER, pv_s.bygg_inom_grans, pv_s.kor, pv_s.Server, bk_s.ROOT, bk_s.PROJEKT, fh_s.KUNDER = spara_
    print('skissens kontroller (2026-10-06) ok')


skisskontrollerna()


shutil.rmtree(tmp, ignore_errors=True)
print('revisionens regressionsfall: alla ok')
