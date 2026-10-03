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
# två granskare: lägsta betyget, varje blockerande fynd och visa från båda gäller
kv = {n: {'betyg': 8, 'motivering': '', 'visa': True} for n in g.KRITERIER}
ja = {'kriterier': kv, 'blockerande': []}
assert g.godkand(g.sla_ihop([ja, ja]))
assert not g.godkand(g.sla_ihop([ja, {'kriterier': kv, 'blockerande': [{'kriterium': 'text', 'allvarlighet': 3}]}]))
assert not g.godkand(g.sla_ihop([ja, {'kriterier': dict(kv, text={'betyg': 6, 'motivering': '', 'visa': True}), 'blockerande': []}]))
assert not g.godkand(g.sla_ihop([ja, {'kriterier': dict(kv, text={'betyg': 9, 'motivering': '', 'visa': False}), 'blockerande': []}]))
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
sida('/', '<header><img src=\"/logga.png\" alt=\"\"></header><a href=\"/om/#x\">Om</a><a href=\"/s/?q=1\">Sök</a><a href=\"https://www.facebook.com/f\">Fb</a><a href=\"tel:+4670\">R</a><h1>Rubrik</h1><img data-src=\"/lat.jpg\" srcset=\"/s-480.jpg 480w, /s-1200.jpg 1200w\" alt=\"Bil\"><div style=\"background:url(/bg.webp)\"></div>')
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
assert md.index('/s-1200.jpg | foto') < md.index('/logga.png | logga/ikon'), 'bildlistan: foto före logga'
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

echo "   byggposter: tom alt, mellanslag efter punkt, filfältets knapp"
"$ROOT/.venv/bin/python" -B -c "
import sys, shutil, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import seo_kontroll as seo, standard_kontroll as sk
assert seo.attrs('<img alt src=\"/a.webp\">').get('alt') == '' and 'alt' not in seo.attrs('<img src=\"/a b.webp\">')
kontakt = pathlib.Path('$S/dist/kontakt/index.html').read_text()
assert 'förfrågan. <a' in kontakt and 'Välj bild' in kontakt, 'mallens förfrågan: mellanslag eller filknapp saknas'
d = pathlib.Path(tempfile.mkdtemp()) / 'dist'; shutil.copytree('$S/dist', d)
(d / 'om' / 'index.html').write_text((d / 'om' / 'index.html').read_text().replace('<h1>Om provet</h1>', '<h1>Om provet</h1><p>Läst i oktober.<a href=\"/\">Läs</a> mer.</p>'))
assert [f for f in sk.granska(d)[0] if f['punkt'] == '9.4' and f['sida'] == '/om/']
" || { echo "FEL: byggposternas kontroller"; exit 1; }
echo "   byggposterna ok"

echo "   bilddatum ur EXIF och filnamn, och GPS i en publicerad bild"
"$ROOT/.venv/bin/python" -B -c "
import sys, struct, shutil, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import bilddatum as bd, standard_kontroll as sk
datum = b'2021:08:24 07:25:00\x00'
# TIFF: IFD0 med pekare till Exif-IFD och GPS-IFD; Exif-IFD med DateTimeOriginal
ifd0 = struct.pack('<H', 2) + struct.pack('<HHII', 0x8769, 4, 1, 38) + struct.pack('<HHII', 0x8825, 4, 1, 56) + struct.pack('<I', 0)
exififd = struct.pack('<H', 1) + struct.pack('<HHII', 0x9003, 2, len(datum), 62) + struct.pack('<I', 0)
tiff = b'II*\x00' + struct.pack('<I', 8) + ifd0 + exififd + struct.pack('<H', 0) + struct.pack('<I', 0) + datum
app1 = b'Exif\x00\x00' + tiff
jpg = b'\xff\xd8' + b'\xff\xe1' + struct.pack('>H', len(app1) + 2) + app1 + b'\xff\xd9'
tmp = pathlib.Path(tempfile.mkdtemp()); (tmp / 'jobb.jpg').write_bytes(jpg); (tmp / 'IMG_20210902_144500.jpg').write_bytes(b'\xff\xd8\xff\xd9')
r = {x['fil']: x for x in (bd.datum(f) for f in sorted(tmp.iterdir()))}
assert r['jobb.jpg']['datum'] == '2021-08-24 07:25' and r['jobb.jpg']['gps'], r
assert r['IMG_20210902_144500.jpg']['datum'] == '2021-09-02 14:45' and r['IMG_20210902_144500.jpg']['kalla'] == 'filnamn (tolkning)', r
d = tmp / 'dist'; shutil.copytree('$S/dist', d)
assert not [f for f in sk.granska(d)[0] if f['punkt'] == '4.2' and 'GPS' in f['text']]
(d / 'jobb.jpg').write_bytes(jpg)
assert [f for f in sk.granska(d)[0] if f['punkt'] == '4.2' and 'GPS' in f['text']]
" || { echo "FEL: bilddatum eller GPS-vakten"; exit 1; }
echo "   bilddatum ok"

echo "   A/B-mätningens kontextdjup"
"$ROOT/.venv/bin/python" -B -c "
import sys; sys.path.insert(0, '$ROOT/kontroller'); import ab
u = lambda n: {'type': 'assistant', 'message': {'usage': {'input_tokens': 10, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': n}}}
k = ab.kontextdjup([u(100), u(600000), {'type': 'user'}, u(499990)], 1000000)
assert k == {'kontext_max': 600010, 'over_halva': 1, 'meddelanden': 3}, k
" || { echo "FEL: kontextdjupet"; exit 1; }
echo "   kontextdjupet ok"

echo "   grupperingen läser varje omgång"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import gruppera as gr
k = pathlib.Path(tempfile.mkdtemp())
for n, block in ((1, [{'kriterium': 'originalitet', 'standardpunkt': '2.3', 'allvarlighet': 3, 'observation': 'egenritat märke'}]), (2, [])):
    d = k / 'prov-bygge' / 'granskning' / ('runda-%02d' % n); d.mkdir(parents=True)
    (d / 'GRANSKNING.json').write_text(json.dumps({'runda': n, 'blockerande': block}))
gr.KUNDER = k
rader = gr.granskningsfynd()
assert rader == ['- granskning prov-bygge omgång 1 (rättat före sista omgången): [originalitet, grad 3] egenritat märke'], rader
" || { echo "FEL: grupperingen"; exit 1; }
echo "   grupperingen ok"

echo "   prospektpipelinen: SCB-stubb, sajtjakt, mätning av en lokal sajt, poäng (offline)"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/prospekt/prov_prospekt.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/prospekt-prov.log" \
  || { echo "FEL: prospektpipelinen"; tail -20 "$ROOT/kunder/rokprov-mall/prospekt-prov.log"; exit 1; }
echo "   prospektpipelinen ok"

echo "   utskicksgrinden och brevkontrollen (offline)"
"$ROOT/.venv/bin/python" -B -c "
import sys, tempfile, pathlib; sys.path.insert(0, '$ROOT/kontroller'); import utskick as u, prospektfiler as pf, brev as b
post = {'slug': 'x', 'status': 'utkast', 'fysisk_person': False, 'jurform': '49', 'jurform_text': 'Övriga aktiebolag', 'sparr': {'reklam': False, 'epost': False, 'telefon': False}, 'orgNr': '5560001234', 'sajt': {'url': 'https://x.se/'}}
brev = {'utkast': {'amne': 'Hej', 'text': 'Brevet'}, 'godkand': {'text_sha': pf.text_sha('Hej', 'Brevet')}, 'mottagare': {'epost': 'info@x.se', 'typ': 'roll', 'bekraftad_person': False}}
assert u.far_skickas(post, brev, [], False, True) == (True, 'ok')
fall = [(dict(post, status='vald'), brev, [], False, True, 'inte utkast'), (post, dict(brev, godkand={}), [], False, True, 'inte godkänt'),
        (post, dict(brev, redigerat={'amne': 'Hej', 'text': 'ändrad'}), [], False, True, 'ändrad efter'), (dict(post, fysisk_person=True), brev, [], False, True, 'MFL 19'),
        (dict(post, jurform='10', jurform_text='Enskild näringsidkare'), brev, [], False, True, 'juridisk form'), (dict(post, sparr={'reklam': True, 'epost': False}), brev, [], False, True, 'reklamspärr'),
        (dict(post, sparr={'reklam': False, 'epost': True}), brev, [], False, True, 'e-postspärr'), (post, dict(brev, mottagare={'epost': 'nej'}), [], False, True, 'mottagaradress'),
        (post, brev, [{'typ': 'e-post', 'varde': 'INFO@x.se', 'skal': 'bad'}], False, True, 'spärrad'), (post, brev, [{'typ': 'doman', 'varde': 'x.se'}], False, True, 'spärrad'),
        (post, brev, [{'typ': 'orgnr', 'varde': '556000-1234'}], False, True, 'spärrad'), (post, dict(brev, mottagare={'epost': 'anna@x.se', 'typ': 'person', 'bekraftad_person': False}), [], False, True, 'namngiven'),
        (post, brev, [], True, True, 'redan skickat'), (post, brev, [], False, False, 'Resend-nyckeln')]
for p_, b_, s_, uf, hf, vantat in fall:
    ok, skal = u.far_skickas(p_, b_, s_, uf, hf); assert not ok and vantat in skal, (vantat, skal)
assert pf.text_sha(' Ä ', 'b\\n') == pf.text_sha('Ä', 'b')
t = b.tillatna_tal(['- LCP efter 8,4 s [lighthouse.json LCP 8423 ms]', '- Ingen kanonisk adress (7.1) [poäng: canonical_saknas]'])
assert b.siffror_ok('laddar på 8,4 s', t)[0] and not b.siffror_ok('laddar på 7 s', t)[0]
d = pathlib.Path(tempfile.mkdtemp()); f = d / 'resend.env'; f.write_text('RESEND_API_NYCKEL=re_x\\nAVSANDARE=A <a@x.se>\\nSVAR_TILL=a@x.se\\n'); f.chmod(0o644)
assert not u.hemligheter_finns(f); f.chmod(0o600); assert u.hemligheter_finns(f) and 'avregistrera' in u.sidfot(u.las_hemligheter(f), post)
" || { echo "FEL: utskicksgrinden eller brevkontrollen"; exit 1; }
echo "   grinden och brevkontrollen ok"

echo "   spanaren: normalisering, kända källor, flöden, rankning, dedupe (offline)"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/spaning/prov_spaning.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/spaning-prov.log" \
  || { echo "FEL: spanaren"; tail -20 "$ROOT/kunder/rokprov-mall/spaning-prov.log"; exit 1; }
"$ROOT/.venv/bin/python" -B -c "
import sys; sys.path.insert(0, '$ROOT/kontroller'); import kallnyckel as kn
k = kn.kanda_kallor(); assert len(k) >= 20 and any(v['dom'].startswith('ta in') for v in k.values()), 'registret ger inga kända källor'
" || { echo "FEL: kända källor ur registret"; exit 1; }
echo "   spanaren ok"

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
