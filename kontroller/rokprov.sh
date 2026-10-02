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
