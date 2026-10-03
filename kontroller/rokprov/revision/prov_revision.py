#!/usr/bin/env python3
"""Regressionsfall ur revisionen 2026-10-03 (Codex, 27 fynd): varje fall är ett hål som fanns, isolerat och syntetiskt.
Körs av kontroller/rokprov.sh. Argument: repots rot. Skriver bara i temporära kataloger."""
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(ROOT / 'dashboard'))
PY = sys.executable


class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def server(rot, handler=None):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler or functools.partial(Tyst, directory=str(rot)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, 'http://127.0.0.1:%d' % srv.server_port


# --- F2: dashboardens markdown kodar citattecken i attribut ---
import server as dash  # noqa: E402
h = dash.md('Se [länken](https://x.se/"onmouseover="window.audit=1) och https://y.se/"onclick="a')
assert 'onmouseover="' not in h and 'onclick="' not in h and '&quot;' in h, h
assert dash.md('`<b>`') == '<p><code>&lt;b&gt;</code></p>', dash.md('`<b>`')
print('F2 markdown ok')

# --- F13/F14/F15: värdkontroll, /fil/ för dolda armar, A/B-val först när båda är klara ---
dash.VARD['tillatna'] = {'127.0.0.1:4771', 'localhost:4771'}
assert not dash.fil_tillaten('kunder/ab/ab-x-20261003T000000Z.json')
assert dash.fil_tillaten('kunder/nagot-bygge/prov/inspektion/hem/vy-390-forsta.png')
dash.ab_oavgjord = lambda slug: slug == 'dold-abx'
assert dash.fil_tillaten('kunder/dold-abx/prov/inspektion/hem/vy-390-forsta.png')
assert not dash.fil_tillaten('kunder/dold-abx/RAPPORT.md') and not dash.fil_tillaten('underlag/dold-abx/KONCEPT.md')
assert not dash.fil_tillaten('kunder/dold-abx/prov/inspektion/hem/INSPEKTION.json')
assert not dash.ab_klar({'byggen': ['a', 'b'], 'korningar': {'a': {}}}) and not dash.ab_klar({'byggen': ['a', 'b'], 'korningar': {'a': {}, 'b': {}}})
assert dash.ab_klar({'byggen': ['a', 'b'], 'korningar': {'a': {}, 'b': {}}, 'klar': '2026-10-03T00:00:00Z'})
print('F13–F15 dashboard ok')

# --- F3/F12/F27: commitvakten i ett eget repo med egen origin ---
tmp = Path(tempfile.mkdtemp(prefix='nwp-rev-'))
bare, repo = tmp / 'origin.git', tmp / 'repo'
subprocess.run(['git', 'init', '-q', '--bare', str(bare)], check=True)
subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True)  # noqa: E731
g('config', 'user.email', 'p@x'); g('config', 'user.name', 'p'); g('remote', 'add', 'origin', str(bare))
(repo / 'CLAUDE.md').write_text('x\n'); (repo / 'backlog').mkdir(); (repo / 'backlog' / 'a.md').write_text('a\n')
g('add', '-A'); g('commit', '-q', '-m', 'start'); g('push', '-q', 'origin', 'main')
hook = repo / '.claude' / 'hooks'; hook.mkdir(parents=True); shutil.copy(ROOT / '.claude/hooks/commitvakt.py', hook / 'commitvakt.py')


def vakt(cmd):
    p = subprocess.run([PY, '-B', str(hook / 'commitvakt.py')], input=json.dumps({'tool_name': 'Bash', 'tool_input': {'command': cmd}}),
                       capture_output=True, text=True, env={**os.environ, 'NWP_COMMIT_TILLATET': 'backlog/'})
    return p.returncode, p.stderr.strip()


for cmd, vantat in [('git add backlog/../CLAUDE.md', 2), ('git add ./backlog/b.md', 0), ('git commit --only -- CLAUDE.md', 2),
                    ('git commit -m x CLAUDE.md', 2), ('git commit -am x', 2), ('git commit --amend -m x', 2), ('git commit -m "backlog/x"', 0),
                    ('git push origin main', 0), ('git push --force origin main', 2), ('git -c core.pager=cat log', 2)]:
    rc, err = vakt(cmd); assert rc == vantat, (cmd, rc, err)
(repo / 'backlog' / 'n.md').write_text('RESEND_API_NYCKEL=re_abcdefghijklmnopqrstuvwxyz0123\n'); g('add', 'backlog/n.md')
rc, err = vakt('git commit -m x'); assert rc == 2 and 'hemlighet' in err, err
g('reset', '-q', 'backlog/n.md'); (repo / 'backlog' / 'n.md').unlink()
(repo / 'CLAUDE.md').write_text('z\n'); g('commit', '-q', '-am', 'ändra'); (repo / 'CLAUDE.md').write_text('x\n'); g('commit', '-q', '-am', 'tillbaka')
assert g('diff', '--name-only', 'origin/main..HEAD').stdout.strip() == ''
rc, err = vakt('git push origin main'); assert rc == 2 and 'CLAUDE.md' in err, err  # ändrad och återställd i två commits
g('remote', 'remove', 'origin'); rc, err = vakt('git push origin main'); assert rc == 2, err  # git-fel nekar
print('F3/F12/F27 commitvakten ok')

# --- F4: symlänk ut ur dist/ serveras inte ---
import prova  # noqa: E402
dist = tmp / 'dist'; dist.mkdir(); (dist / 'index.html').write_text('<p>hej</p>'); (dist / '404.html').write_text('<p>404</p>')
hemlig = tmp / 'hemlig.txt'; hemlig.write_text('hemligt'); os.symlink(hemlig, dist / 'lank.txt'); os.symlink(tmp, dist / 'upp')
import urllib.request  # noqa: E402
with prova.Server(dist) as srv:
    def status(vag):
        try:
            with urllib.request.urlopen(srv.url + vag, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b''
    assert status('/')[0] == 200 and status('/lank.txt')[0] == 404 and status('/upp/hemlig.txt')[0] == 404, 'symlänkar ut ur dist'
print('F4 symlänk ok')

# --- F5/F24: hämtaren följer inte omdirigeringar in i det egna nätet eller till en annan domän; robots med * och $ ---
import hamta_sajt as hs  # noqa: E402
rot = tmp / 'sajt'; rot.mkdir()
(rot / 'index.html').write_text('<html><body><a href="/private/a">p</a><a href="/public/b.html">q</a><a href="/omd">o</a></body></html>')
(rot / 'public').mkdir(); (rot / 'public' / 'b.html').write_text('<html><body>b</body></html>')
(rot / 'robots.txt').write_text('User-agent: *\nDisallow: /private/*\nAllow: /private/open$\nDisallow: /*.pdf$\nCrawl-delay: 0\n')


class Omd(Tyst):
    def do_GET(self):
        if self.path == '/omd':
            self.send_response(302); self.send_header('Location', 'http://127.0.0.1:1/dashboard'); self.send_header('Content-Length', '0'); self.end_headers(); return
        if self.path == '/annan':
            self.send_response(302); self.send_header('Location', 'http://example.org/'); self.send_header('Content-Length', '0'); self.end_headers(); return
        super().do_GET()


srv, bas = server(rot, functools.partial(Omd, directory=str(rot)))
rp = hs.Robots(); rp.parse((rot / 'robots.txt').read_text().splitlines())
assert not rp.can_fetch('nortropic-webb-pro', bas + '/private/a') and rp.can_fetch('nortropic-webb-pro', bas + '/private/open')
assert not rp.can_fetch('nortropic-webb-pro', bas + '/x/fil.pdf') and rp.can_fetch('nortropic-webb-pro', bas + '/x/fil.pdfx') and rp.can_fetch('nortropic-webb-pro', bas + '/public/b.html')
hs.TILLAT_LOKALT = False; hs._adresser.clear()
s = hs.hamta(bas + '/omd')
assert s['status'] is None and 'egna nätet' in (s.get('fel') or ''), s  # 127.0.0.1 nekas redan som startadress utan lokalt läge
hs.TILLAT_LOKALT = True
s = hs.hamta(bas + '/annan', egen='127.0.0.1')
assert s['status'] == 302 and s['url'] == 'http://example.org/' and 'annan domän' in s['fel'], s
s = hs.hamta('file:///etc/hosts')
assert s['status'] is None and 'bara http' in s['fel'], s
r = hs.hamta_sajt(bas + '/', tmp / 'ut', paus=0)
assert r['nekade'] == 1 and r['sidor'] == 2, r
srv.shutdown()
print('F5/F24 hämtaren ok')

# --- F6/F7: oläsbar spärrlista nekar; godkännandet binder mottagaren ---
import utskick as u, prospektfiler as pf  # noqa: E402
post = {'slug': 'x', 'status': 'utkast', 'fysisk_person': False, 'jurform': '49', 'jurform_text': 'Övriga aktiebolag', 'sparr': {'reklam': False, 'epost': False}}
god = {'text_sha': pf.text_sha('Hej', 'Brevet'), 'mottagare': 'info@x.se', 'slug': 'x', 'bekraftad_person': False}
brev = {'utkast': {'amne': 'Hej', 'text': 'Brevet'}, 'godkand': god, 'mottagare': {'epost': 'info@x.se', 'typ': 'roll', 'bekraftad_person': False}}
assert u.far_skickas(post, brev, [], False, True) == (True, 'ok')
ok, skal = u.far_skickas(post, dict(brev, mottagare={'epost': 'kontakt@x.se', 'typ': 'roll'}), [], False, True); assert not ok and 'annan mottagare' in skal, skal
ok, skal = u.far_skickas(dict(post, slug='y'), brev, [], False, True); assert not ok and 'annan mottagare' in skal, skal
ok, skal = u.far_skickas(post, dict(brev, godkand={'text_sha': god['text_sha']}), [], False, True); assert not ok and 'annan mottagare' in skal, skal
ok, skal = u.far_skickas(post, brev, None, False, True); assert not ok and 'spärrlistan' in skal, skal
u.SPARR = tmp / 'SPARR.json'; assert u.las_sparr() == []
u.SPARR.write_text('{trasig'); assert u.las_sparr() is None
try:
    u.sparr_lagg('a@x.se', 'prov', spegla=False); raise AssertionError('skriv inte över en trasig lista')
except u.Nekad:
    pass
u.SPARR.write_text('[]'); assert u.las_sparr() == []
print('F6/F7 utskick ok')

# --- F8/F17/F18: granskaren utan facit, samma metod för cachen ---
import granska as gr  # noqa: E402
k = tmp / 'kunder'; (k / 'ett-abx').mkdir(parents=True); (k / 'ett-aby').mkdir(); (k / 'annat').mkdir()
(k / 'ett-abx' / 'AB-SYSKON').write_text('ett-aby\n'); (k / 'ett-aby' / 'AB-SYSKON').write_text('ett-abx\n')
for s in ('ett-aby', 'annat'):
    (k / s / 'DOM.json').write_text(json.dumps({'domar': [{'svar': {'namn': 'Ja, som den är', 'specifik': 5}}]}))
gr.KUNDER = k; gr.ROOT = tmp
(tmp / 'LARDOMAR.md').write_text('# Lärdomar\n\n## L1 · 2026-10-01 · annat\n\n- bra\n\n## L2 · 2026-10-02 · ett-aby\n\n- facit\n\n## AB · 2026-10-02 · effort: A=medium mot B=high\n\n- val B\n')
(tmp / 'kritik').mkdir(); (tmp / 'kritik' / 'GRANSKARE.md').write_text('k'); (tmp / 'kritik' / 'SCHEMA-granskning.json').write_text('{}'); (tmp / 'kritik' / 'SCHEMA-originalitet.json').write_text('{}')
gr.SCHEMA, gr.SCHEMA_ORIGINALITET = tmp / 'kritik' / 'SCHEMA-granskning.json', tmp / 'kritik' / 'SCHEMA-originalitet.json'
assert [p.name for p, _ in gr.domda_byggen('ett-abx')] == ['annat'], 'syskonets dom ska undantas'
rdir = tmp / 'runda'; rdir.mkdir()
f = gr.lardomar_utan('ett-abx', rdir); text = f.read_text()
assert 'facit' not in text and 'ett-aby' not in text and '## L1' in text and '## AB' in text, text
assert 'Read(./LARDOMAR.md)' in gr.nekas_for('ett-abx') and any('ett-aby/DOM.json' in x for x in gr.nekas_for('ett-abx'))
m1 = gr.metod_sha(); (tmp / 'kritik' / 'GRANSKARE.md').write_text('k2'); assert gr.metod_sha() != m1, 'ändrade kriterier ska ge ny metodhash'
upp = {'metod_sha': m1, 'modell': 'opus[1m]', 'effort': 'high', 'granskare': 2, 'originalitet': 'skugga'}
assert gr.samma_metod(dict(upp), upp) and not gr.samma_metod(dict(upp, granskare=1), upp) and not gr.samma_metod({}, upp)
print('F8/F17/F18 granskaren ok')

# --- F19/F20/F21: sajtfynd som lista, @graph och typlistor, undertyper av LocalBusiness ---
assert prova.seo_rader({'sajt': [{'typ': 'robots.txt saknas', 'text': ''}], 'per_sida': [{'sida': '/', 'fynd': [{'typ': 'x', 'text': 'y'}]}]}) == ['sajt: robots.txt saknas ', '/: x y']
assert prova.seo_rader({'sajt': {'fynd': [{'typ': 'a', 'text': 'b'}]}}) == ['sajt: a b']
import seo_kontroll as seo, standard_kontroll as sk  # noqa: E402
verk = {'namn': 'Holms Konditori', 'telefon': '0920-12345', 'fiktiv': False, 'adress': {'gata': 'Storgatan 1', 'postnummer': '972 31', 'ort': 'Luleå', 'publik': True}}
graf = {'@context': 'https://schema.org', '@graph': [{'@type': 'Bakery', 'name': 'Fel namn', 'telephone': '+46920123450', 'address': {'@type': 'PostalAddress', 'postalCode': '972 31'}},
                                                   {'@type': 'WebSite', 'name': 'Holms Konditori'}]}
f = seo.granska_schema(graf, verk)
assert not any(t == 'JSON-LD utan @type' for t, _ in f), f  # behållaren är giltig
assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), f  # noden i grafen prövas
f = seo.granska_schema({'@type': ['Bakery', 'LocalBusiness'], 'name': 'Fel namn'}, verk)
assert any(t == 'schema name ≠ verksamhetens namn' for t, _ in f), f  # listtyp prövas också
assert 'Bakery' in sk.LOKALA_TYPER and 'CafeOrCoffeeShop' in sk.LOKALA_TYPER and 'WebSite' not in sk.LOKALA_TYPER
assert sk.CSP_SKRIPT_OK.match("'sha256-abc+/='") and not sk.CSP_SKRIPT_OK.match('*') and not sk.CSP_SKRIPT_OK.match('https:') and not sk.CSP_SKRIPT_OK.match("'unsafe-inline'")
print('F19–F22 seo/standard ok')

# --- F23: ateljéns panel räknar bara fullständiga rangordningar ---
import atelje as a  # noqa: E402
arot = tmp / 'atelje'
for n in (1, 2, 3):
    (arot / str(n)).mkdir(parents=True); (arot / str(n) / 'vy-390-ruta-01.png').write_bytes(b'x')
a.ROOT = tmp; a.KUNDER = k; a.UNDERLAG = tmp / 'underlag'
svar_per_domare = {}


def attrapp(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None):
    karta = {rad.split(':')[0].split()[-1]: rad.split('/')[-2] for rad in prompt.splitlines() if rad.startswith('- riktning ')}
    namn = ut.name.replace('svar-domare-', '').replace('.json', '')
    bok = {v: b for b, v in karta.items()}
    return {'structured_output': svar_per_domare[namn](bok)}


a.session = attrapp
full = lambda bok: {'rangordning': [{'riktning': bok['2'], 'plats': 1, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['1'], 'plats': 2, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['3'], 'plats': 3, 'styrkor': '', 'svagheter': ''}], 'lana': [], 'motivering': ''}  # noqa: E731
tom = lambda bok: {'rangordning': [], 'lana': [], 'motivering': ''}  # noqa: E731
dubbel = lambda bok: {'rangordning': [{'riktning': bok['1'], 'plats': 1, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['1'], 'plats': 1, 'styrkor': '', 'svagheter': ''}, {'riktning': bok['3'], 'plats': 2, 'styrkor': '', 'svagheter': ''}], 'lana': [], 'motivering': ''}  # noqa: E731
svar_per_domare.update(formgivning=full, funktion=full, kunden=dubbel)
v = a.panel('prov', arot)
assert v['val'] == 2 and v['poang'] == {1: 2, 2: 4, 3: 0} and v['panel']['kunden'].get('ogiltig') and any('kunden' in x for x in v['fel']), v
svar_per_domare.update(formgivning=full, funktion=tom, kunden=dubbel)
try:
    a.panel('prov', arot); raise AssertionError('en giltig domare ska inte räcka')
except RuntimeError as e:
    assert 'giltiga domare' in str(e), e
print('F23 ateljén ok')

# --- F25/F26: spanaren filtrerar kända före antalsbegränsningen och låser status ---
import spana as sp  # noqa: E402
sp.SPANING = tmp / 'spaning'
kand = lambda i, poang: {'id': 'k%02d' % i, 'nyckel': 'n%02d' % i, 'url': 'https://x.se/%d' % i, 'titel': 'astro lighthouse %d' % i, 'sammanfattning': '', 'kalla': 'prov', 'kalla_typ': 'rss', 'kallor': ['prov'], 'status': 'ny', 'hittad': sp.nu(), 'publicerad': '2026-10-01', 'popularitet': poang}  # noqa: E731
sp.rss = lambda kalla, h: [kand(i, 1000 - i) for i in range(1, 9)]
kanda = {'n%02d' % i: {'dom': 'ta in', 'datum': '2026-09-01'} for i in range(1, 6)}  # de fem bästa är redan kända


class H:
    anrop = 0


senast, lista = sp.spana([{'typ': 'rss', 'namn': 'prov', 'url': 'u', 'vikt': 1.0, 'id': 'p'}], H(), max_per_kalla=5, kanda=kanda)
assert {x['id'] for x in lista if x['status'] == 'ny'} == {'k06', 'k07', 'k08'} and senast['redan_kanda'] == 5, (senast, [x['id'] for x in lista])
sp.satt('k06', 'avfardad', avfardad='prov')
assert (sp.SPANING / '.las').exists() and next(x for x in sp.las_json(sp.SPANING / 'KANDIDATER.json') if x['id'] == 'k06')['status'] == 'avfardad'
print('F25/F26 spanaren ok')

shutil.rmtree(tmp, ignore_errors=True)
print('revisionens regressionsfall: alla ok')
