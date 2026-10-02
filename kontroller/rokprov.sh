#!/bin/bash
# rokprov.sh — regressionsprov för kontrollerna och mallen. Kör efter varje ändring i kontroller/ eller mall/.
# Bygger mallen med två testsidor och kräver (1) grönt prov, (2) rött snabbprov när fem kända fel läggs in.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/kunder/rokprov-mall/sajt"
mkdir -p "$S"
rsync -a --delete --exclude node_modules --exclude dist --exclude .astro "$ROOT/mall/astro/" "$S/"
rm -f "$S/README.md"
rsync -a "$ROOT/kontroller/rokprov/src/" "$S/src/"
rsync -a "$ROOT/kontroller/rokprov/public/" "$S/public/"
# apple-touch-icon och delningsbild görs av verktyget varje gång, så att verktyget också prövas
node "$ROOT/kontroller/ikoner.mjs" --sajt "$S" --foto "$ROOT/kontroller/rokprov/foto.svg" --bakgrund '#0b57d0' >/dev/null
sed -i '' 's#https://ERSATT-MED-DOMAN.se#https://exempel-rokprov.se#' "$S/astro.config.mjs"
[ -d "$S/node_modules" ] || (cd "$S" && npm install --no-audit --no-fund >/dev/null)
rm -f "$ROOT/kunder/rokprov-mall/RAPPORT.md"
# testsajten har inga foton: beställningen finns, så att bildkravet (9.3) är uppfyllt på rätt sätt
mkdir -p "$ROOT/underlag/rokprov-mall"
printf '# Beställning till verksamheten\n\n- Fem foton av jobb, till startsidan och tjänstesidan.\n- Telefontid.\n' > "$ROOT/underlag/rokprov-mall/BESTALLNING.md"

echo "1/2 grönt prov"
if ! "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/prova.py" rokprov-mall >/dev/null; then
  echo "FEL: provet blev rött på den rena testsajten"; sed -n '1,20p' "$ROOT/kunder/rokprov-mall/prov/PROV.md"; exit 1
fi
echo "   grönt"

echo "   granskarens uppdrag (torrt, ingen session) och godkännandets regel"
UPPDRAG=$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/granska.py" rokprov-mall --torr)
for krav in "kritik/GRANSKARE.md" "originalitet ≥ 7" "vy-390-ruta-01.png" "vy-1440-ruta-01.png" "kunskap/referenser-professionella.md" "kunskap/byggstandard.md" "standard.md"; do
  case "$UPPDRAG" in *"$krav"*) ;; *) echo "FEL: granskarens uppdrag saknar: $krav"; exit 1;; esac
done
"$ROOT/.venv/bin/python" -B -c "
import sys; sys.path.insert(0, '$ROOT/kontroller'); import granska as g
k = {n: {'betyg': 8, 'motivering': ''} for n in g.KRITERIER}
assert g.godkand({'kriterier': k, 'blockerande': []})
assert not g.godkand({'kriterier': dict(k, originalitet={'betyg': 6, 'motivering': ''}), 'blockerande': []})
assert not g.godkand({'kriterier': k, 'blockerande': [{'kriterium': 'text'}]})
assert not g.godkand({'kriterier': {}, 'blockerande': []})
assert g.niva({'kriterier': k, 'blockerande': []}) == 0
assert g.niva({'kriterier': k, 'blockerande': [{'omfattning': 'detalj'}]}) == 1
assert g.niva({'kriterier': k, 'blockerande': [{'omfattning': 'detalj'}, {'omfattning': 'riktning'}]}) == 2
" || { echo "FEL: godkännandets regel"; exit 1; }
echo "   granskaren ok"

echo "   formulärets demomottagare"
"$ROOT/.venv/bin/python" -B -c "
import sys, urllib.request, urllib.error
sys.path.insert(0, '$ROOT/kontroller'); import prova
class Ingen(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
op = urllib.request.build_opener(Ingen)
def skicka(url, data):
    req = urllib.request.Request(url + '/api/forfragan', data=data.encode(), headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    try:
        return op.open(req).headers.get('Location')
    except urllib.error.HTTPError as e:
        return e.headers.get('Location')
with prova.Server('$S/dist') as srv:
    assert skicka(srv.url, 'namn=Test&telefon=070&meddelande=hej&webbplats=&fylltid=4200') == '/tack/'
    assert skicka(srv.url, 'namn=Bot&telefon=1&meddelande=x&webbplats=spam') == '/tack/'
    assert skicka(srv.url, 'namn=&telefon=070&meddelande=') == '/kontakt/?saknas=1#forfragan-saknas'
    assert skicka(srv.url, 'namn=+&telefon=+&meddelande=+') == '/kontakt/?saknas=1#forfragan-saknas'
" || { echo "FEL: formulärets demomottagare"; exit 1; }
echo "   demomottagaren ok"

echo "   hämtverktyget mot en lokal sajt (robots.txt, sidkarta, frågesträng, bilder)"
"$ROOT/.venv/bin/python" -B -c "
import sys, tempfile, threading, functools, pathlib, http.server
sys.path.insert(0, '$ROOT/kontroller'); import hamta_sajt as h
rot, ut = pathlib.Path(tempfile.mkdtemp()), pathlib.Path(tempfile.mkdtemp())
class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Tyst, directory=str(rot)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
bas = f'http://127.0.0.1:{srv.server_port}'
def sida(vag, kropp):
    d = rot / vag.strip('/'); d.mkdir(parents=True, exist_ok=True)
    (d / 'index.html').write_text(f'<html lang=\"sv\"><head><title>T {vag}</title></head><body>{kropp}</body></html>')
(rot / 'robots.txt').write_text(f'User-agent: *\nDisallow: /hemlig/\nSitemap: {bas}/sitemap.xml\n')
(rot / 'sitemap.xml').write_text(f'<urlset><url><loc>{bas}/el/</loc></url><url><loc>{bas}/hemlig/</loc></url></urlset>')
sida('/', '<a href=\"/om/#x\">Om</a><a href=\"/s/?q=1\">Sök</a><a href=\"https://www.facebook.com/f\">Fb</a><a href=\"tel:+4670\">R</a><h1>Rubrik</h1><img data-src=\"/lat.jpg\" srcset=\"/s-480.jpg 480w, /s-1200.jpg 1200w\" alt=\"Bil\"><div style=\"background:url(/bg.webp)\"></div>')
sida('/om/', '<p>Om oss.</p><a href=\"/saknas/\">x</a>')
sida('/el/', '<p>Bara i sidkartan.</p>')
sida('/hemlig/', '<p>nej</p>')
r = h.hamta_sajt(bas + '/', ut, paus=0)
srv.shutdown()
assert (r['sidor'], r['nekade'], r['fel']) == (3, 1, 1), r
md, txt = (ut / 'SIDOR.md').read_text(), (ut / 'start.txt').read_text()
for krav in ('/lat.jpg', '/s-1200.jpg', '/bg.webp', 'tel:+4670', 'facebook.com', 'nekad av robots.txt', 'frågesträng'):
    assert krav in md, krav
assert '[h1] Rubrik' in txt and 'T /' not in txt.split('---TEXT---')[1], txt
" || { echo "FEL: hämtverktyget"; exit 1; }
echo "   hämtverktyget ok"

echo "   kvarlämnad kastbar sida (tvåan) ger fel i standarden"
"$ROOT/.venv/bin/python" -B -c "
import sys, shutil, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import standard_kontroll as sk
d = pathlib.Path(tempfile.mkdtemp()) / 'dist'; shutil.copytree('$S/dist', d)
assert not [f for f in sk.granska(d)[0] if f['sida'] == '/tvaan/']
(d / 'tvaan').mkdir(); shutil.copy(d / 'index.html', d / 'tvaan' / 'index.html')
assert [f for f in sk.granska(d)[0] if f['sida'] == '/tvaan/' and f['punkt'] == '9.4']
" || { echo "FEL: standarden fångar inte en kvarlämnad tvåan-sida"; exit 1; }
echo "   tvåan-regeln ok"

echo "   ägarens A/B-omdöme: adress, brödsmulor, rörelse, typsnittsvikt, intern text"
"$ROOT/.venv/bin/python" -B -c "
import sys, re, json, shutil, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import standard_kontroll as sk, copy_kontroll as ck
tmp = pathlib.Path(tempfile.mkdtemp()); d = tmp / 'dist'; shutil.copytree('$S/dist', d)
punkter = lambda: {(f['punkt'], f['sida']) for f in sk.granska(d)[0]}
ren = punkter()
assert not {p for p in ren if p[0] in ('3.5', '4.3', '7.3')}, ren
# brödsmulor: utan nav på /om/ blir det fel 7.3
om = d / 'om' / 'index.html'; html_om = om.read_text()
om.write_text(re.sub(r'<nav class=\"brodsmulor\".*?</nav>', '', html_om, flags=re.S))
assert ('7.3', '/om/') in punkter(); om.write_text(html_om)
# rörelse utan prefers-reduced-motion blir fel 3.5
sidor = {f: f.read_text() for f in d.rglob('*.html')}
for f, t in sidor.items(): f.write_text(re.sub(r'@media \(prefers-reduced-motion[^{]*\{.*?\}\s*\}', '', t, flags=re.S))
(d / 'rorelse.css').write_text('a{transition:color .2s}')
assert ('3.5', '(alla)') in punkter()
for f, t in sidor.items(): f.write_text(t)
(d / 'rorelse.css').unlink()
# typsnitt: 90 kB utan bredd-axel är fel 4.3, med bredd-axel information
(d / 'tung.woff2').write_bytes(b'0' * 92 * 1024)
assert ('4.3', '(alla)') in punkter()
(d / 'bredd.css').write_text('h1{font-stretch:62%}')
assert ('4.3', '(alla)') not in punkter()
# publik adress: saknas i sidfot och JSON-LD = fel 7.4; dold adress prövas inte
v = tmp / 'VERKSAMHET.json'
v.write_text(json.dumps({'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provby', 'publik': True}}))
assert {f['punkt'] for f in sk.adress(d, v)} == {'7.4'}
v.write_text(json.dumps({'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provby', 'publik': False}}))
assert sk.adress(d, v) == []
# intern text: hänvisning till den gamla sajten
assert any(f['typ'] == 'intern information' for f in ck.kontrollera_fil(pathlib.Path('x.html'), '<p>Tillbyggnaden, från vår gamla sajt.</p>', [])[0])
" || { echo "FEL: kontrollerna ur ägarens A/B-omdöme"; exit 1; }
echo "   A/B-omdömets kontroller ok"

echo "2/2 kända fel ska ge rött"
F="$S/src/pages/om/index.astro"
cp "$F" "$F.ren"
sed -i '' 's#<p><a href="/">Tillbaka</a></p>#<p style="color:\#bbb">Ljusgrå text.</p><div style="width:1800px">Bred.</div><img src="/finns-inte.png"><p><a href="/saknas/">Trasig</a></p><p><a href="/">Tillbaka</a></p>#' "$F"
set +e
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/prova.py" rokprov-mall --snabb >/dev/null
RC=$?
set -e
mv "$F.ren" "$F"
SAKNAS=$("$ROOT/.venv/bin/python" -c "
import json,sys; s=json.load(open('$ROOT/kunder/rokprov-mall/prov/STATUS.json'))
print(' '.join(g for g in ('seo','axe','spill','standard') if s['grindar'][g]['ok']))")
if [ "$RC" -ne 1 ] || [ -n "$SAKNAS" ]; then
  echo "FEL: väntade rött i seo, axe, spill och standard; gröna ändå: ${SAKNAS:-inga} (rc $RC)"; exit 1
fi
echo "   rött där det skulle (seo, axe, spill, standard)"
echo "rökprovet OK"
