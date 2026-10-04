#!/bin/bash
# rokprov.sh — regressionsprov för kontrollerna och mallen. Kör efter varje ändring i kontroller/ eller mall/.
# Bygger mallen med två testsidor och kräver (1) grönt prov, (2) rött snabbprov när fem kända fel läggs in.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/kunder/rokprov-mall/sajt"
export NWP_HAMTA_LOKALT=1   # provens sajter ligger på 127.0.0.1; hämtaren nekar annars adresser i det egna nätet
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
(d / 'atelje-2').mkdir(); shutil.copy(d / 'index.html', d / 'atelje-2' / 'index.html')
assert [f for f in sk.granska(d)[0] if f['sida'] == '/atelje-2/' and f['punkt'] == '9.4']
import subprocess
r = subprocess.run([sys.executable, '-B', '$ROOT/kontroller/atelje.py', 'saknas-helt-prov'], capture_output=True, text=True)
assert r.returncode == 2 and 'Saknas' in r.stdout, r.stdout
" || { echo "FEL: standarden fångar inte en kvarlämnad kastbar sida, eller ateljén vägrar inte utan underlag"; exit 1; }
echo "   tvåan-regeln ok"

echo "   ateljéns domarpanel: egen ordning per domare, ribbdom per riktning, summan avgör bland de godkända"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, pathlib, tempfile
sys.path.insert(0, '$ROOT/kontroller'); import atelje as a
rot = pathlib.Path(tempfile.mkdtemp()) / 'atelje'
for n in (1, 2, 3):
    (rot / str(n)).mkdir(parents=True); (rot / str(n) / 'vy-390-ruta-01.png').write_bytes(b'x'); (rot / str(n) / 'vy-1440-ruta-01.png').write_bytes(b'x')
(rot / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): ['vy-390-ruta-01.png', 'vy-1440-ruta-01.png'] for n in (1, 2, 3)}}))  # det här försökets riktningar (R11, F34)
a.ROOT = rot.parent; a.UNDERLAG = rot.parent / 'underlag'  # inga kalibreringsankare i provet
sedda = {}
def attrapp(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None):
    # varje domare rangordnar riktning 2 först, oavsett vilken bokstav den fått
    karta = {rad.split(':')[0].split()[-1]: rad.split('/')[-2] for rad in prompt.splitlines() if rad.startswith('- riktning ')}
    sedda[modell + str(len(sedda))] = karta
    plats = sorted(karta, key=lambda b: {'2': 0, '1': 1, '3': 2}[karta[b]])
    return {'structured_output': {'rangordning': [{'riktning': b, 'plats': i + 1, 'styrkor': '', 'svagheter': '', 'haller_ribban': True, 'niva': 'over'} for i, b in enumerate(plats)],
                                  'lana': [{'fran': plats[1], 'vad': 'typsnittet'}], 'motivering': 'prov'}}
a.session = attrapp
v = a.panel('prov', rot)
assert v['val'] == 2 and v['poang'] == {1: 3, 2: 6, 3: 0}, v
assert len({tuple(sorted(k.items())) for k in sedda.values()}) >= 2, 'domarna ska få olika ordning'
assert all(x['fran'] == 1 for x in v['lana']), v['lana']
assert v['godkanda'] == [1, 2, 3] and not v['forkastade'] and v['ankare'] is False, v
" || { echo "FEL: ateljéns domarpanel"; exit 1; }
echo "   domarpanelen ok"

echo "   ägarens A/B-omdöme och L4–L6: adress, brödsmulor, sitemap, telefonfältet, rörelse, typsnittsvikt, intern text"
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
# publik adress: saknas i sidfot och JSON-LD = fel 7.4
v = tmp / 'VERKSAMHET.json'
v.write_text(json.dumps({'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provby', 'publik': True}}))
assert {f['punkt'] for f in sk.adress(d, v)} == {'7.4'}
v.write_text(json.dumps({'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provby', 'publik': False}}))
assert sk.adress(d, v) == []
# dold (obekräftad) adress som ändå står på en sida = fel 7.4 där (domarna L5 och L6)
om.write_text(html_om.replace('<h1>Om provet</h1>', '<h1>Om provet</h1><p>Provgatan 1, Provby</p>'))
assert [f['sida'] for f in sk.adress(d, v)] == ['/om/'], sk.adress(d, v); om.write_text(html_om)
# dom L4: mallens sitemap har inte /tack/; står en noindex-sida där blir det fel 7.2
sm = d / 'sitemap.xml'; xml = sm.read_text()
assert '/tack/' not in xml and '/om/' in xml, xml
assert not {p for p in ren if p[0] in ('7.2', '6.2')}, ren
sm.write_text(xml.replace('</urlset>', '<url><loc>https://exempel.se/tack/</loc></url></urlset>'))
assert ('7.2', '/tack/') in punkter(); sm.write_text(xml)
# dom L4: brödsmulor inne i main ger information, telefonfält utan pattern och fält utan felbesked ger fel 6.2
om.write_text(re.sub(r'(<nav class=\"brodsmulor\".*?</nav>)(.*?<main[^>]*>)', r'\2\1', html_om, flags=re.S))
assert any(i['punkt'] == '7.3' and 'main' in i['text'] for i in sk.granska(d)[1]); om.write_text(html_om)
kf = d / 'kontakt' / 'index.html'; html_k = kf.read_text()
kf.write_text(re.sub(r'\spattern=\"[^\"]*\"', '', html_k)); assert ('6.2', '/kontakt/') in punkter()
kf.write_text(html_k.replace('aria-describedby=\"ff-namn-fel\"', '')); assert ('6.2', '/kontakt/') in punkter(); kf.write_text(html_k)
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

echo "   reservtypsnitt med size-adjust (4.3)"
"$ROOT/.venv/bin/python" -B -c "
import sys, shutil, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import standard_kontroll as sk
d = pathlib.Path(tempfile.mkdtemp()) / 'dist'; shutil.copytree('$S/dist', d)
typ = '@font-face{font-family:Provsans;src:url(/fonts/p.woff2)format(\"woff2\");font-display:swap}'
fel = lambda: [f for f in sk.granska(d)[0] if f['punkt'] == '4.3' and 'reserv' in f['text']]
(d / 't.css').write_text(typ + 'body{font-family:Provsans,sans-serif}')
assert fel(), 'utan reserv ska ge fel'
(d / 't.css').write_text(typ + '@font-face{font-family:Prov reserv;src:local(Arial);size-adjust:102%}body{font-family:Provsans,\"Prov reserv\",sans-serif}')
assert not fel(), 'handskriven reserv ska gå igenom'
(d / 't.css').write_text(typ + '@font-face{font-family:\"Provsans fallback: Arial\";src:local(\"Arial\");size-adjust:101%;ascent-override:95%}:root{--typsnitt:\"Provsans\",\"Provsans fallback: Arial\",sans-serif}')
assert not fel(), 'Astros variabelstack ska gå igenom'
" || { echo "FEL: reservtypsnittet"; exit 1; }
echo "   reservtypsnittet ok"

echo "   stilrapporten: bruten klickbar text, fem mönster ur impeccable, dolda menylänkar och dubbla handlingar"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, subprocess, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import prova
d = pathlib.Path(tempfile.mkdtemp())
(d / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>P</title><style>body{margin:0;font:16px sans-serif}nav a{display:inline-block;width:90px}h1{font-size:18px}h2{font-size:17px;margin:0 0 40px}.kant{border-left:4px solid #d00}.liten{font-size:11px}</style></head><body><header><nav><a href=\"/\">Start</a> <a href=\"/a/\">Våra tjänster inom el och data</a></nav></header><main><h1>Rubrik</h1><p>Inledning som är lång nog att räknas här.</p><h2>Andra</h2><p>Text efter rubriken som är lång nog.</p><h2>Tredje</h2><p>Mer text efter rubriken, lång nog.</p><div class=\"kant\">Citat med färgad kant.</div><p class=\"liten\">Mycket liten brödtext, längre än tjugo tecken.</p></main></body></html>')
(d / 'platt').mkdir(); (d / 'platt' / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><title>P</title><style>h1{font-size:18px}h2{font-size:17px}p{font-size:16px}main div{margin:16px 0;padding:16px 0}</style></head><body><main><h1>Platt</h1><p>Brödtext som är lång nog att räknas.</p><h2>Under</h2><p>Mer brödtext som är lång nog.</p><div>a</div><div>b</div><div>c</div><div>d</div></main></body></html>')
with prova.Server(d) as srv:
    subprocess.run(['node', '$ROOT/kontroller/stil.mjs', '--url=' + srv.url, '--sidor=/,/platt/', '--ut=' + str(d / 'ut')], check=True, capture_output=True)
v = ' '.join(json.loads((d / 'ut' / 'STIL.json').read_text())['varningar'])
for krav in ('bryts på två rader: \"Våra tjänster', 'rubriker står närmare', 'färgad sidkant', 'under 12 px', 'platt typskala', 'enformig luft'):
    assert krav in v, krav
ren = json.loads(pathlib.Path('$ROOT/kunder/rokprov-mall/prov/stil/STIL.json').read_text())
assert not [r for r in ren['rader'] if r.get('tvaRader')], 'rökprovets knappar och länkar ska inte räknas som brutna'
# dom L4: menylänkar som rullar dolda i sidled, numret tre gånger och samma knapp två gånger i första vyn
(d / 'meny').mkdir(); (d / 'meny' / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>P</title><style>body{margin:0;font:16px sans-serif}nav ul{display:flex;overflow-x:auto;white-space:nowrap;margin:0;padding:0;list-style:none}nav a{display:inline-block;padding:12px 20px}.fast{position:fixed;bottom:0;left:0;right:0;background:#fff}</style></head><body><header><a href=\"tel:+46701234567\">070-123 45 67</a><nav><ul><li><a href=\"/\">Start</a></li><li><a href=\"/a/\">Klippning</a></li><li><a href=\"/b/\">Färg och slingor</a></li><li><a href=\"/c/\">Permanent</a></li><li><a href=\"/d/\">Bryn och fransar</a></li><li><a href=\"/e/\">Kontakt</a></li></ul></nav></header><main><h1>Rubrik</h1><a href=\"https://boka.example/x\">Boka</a> <a href=\"tel:+46701234567\">Ring</a></main><div class=\"fast\"><a href=\"https://boka.example/x\">Boka</a> <a href=\"tel:+46701234567\">Ring</a> <a href=\"/kontakt/\">Skriv</a></div></body></html>')
with prova.Server(d) as srv:
    subprocess.run(['node', '$ROOT/kontroller/stil.mjs', '--url=' + srv.url, '--sidor=/meny/', '--ut=' + str(d / 'ut2')], check=True, capture_output=True)
m = next(x for x in json.loads((d / 'ut2' / 'STIL.json').read_text())['rader'] if x['vy'] == '390')['mobil']
assert len(m['menyDolda']) >= 2 and m['telIForsta'] == 3 and m['dubbla'] == ['https://boka.example/x'], m
assert not ren['varningar'] or not any('utanför skärmen' in v or 'gånger i startsidans' in v or 'två gånger' in v for v in ren['varningar']), ren['varningar']
" || { echo "FEL: stilrapportens nya mätningar"; exit 1; }
echo "   stilrapporten ok"

echo "   prospektpipelinen: SCB-stubb, sajtjakt, mätning av en lokal sajt, poäng (offline)"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/prospekt/prov_prospekt.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/prospekt-prov.log" \
  || { echo "FEL: prospektpipelinen"; tail -20 "$ROOT/kunder/rokprov-mall/prospekt-prov.log"; exit 1; }
echo "   prospektpipelinen ok"

echo "   utskicksgrinden och brevkontrollen (offline)"
"$ROOT/.venv/bin/python" -B -c "
import sys, tempfile, pathlib; sys.path.insert(0, '$ROOT/kontroller'); import utskick as u, prospektfiler as pf, brev as b
post = {'slug': 'x', 'status': 'utkast', 'fysisk_person': False, 'jurform': '49', 'jurform_text': 'Övriga aktiebolag', 'sparr': {'reklam': False, 'epost': False, 'telefon': False}, 'orgNr': '5560001234', 'sajt': {'url': 'https://x.se/'}}
brev = {'utkast': {'amne': 'Hej', 'text': 'Brevet'}, 'godkand': {'text_sha': pf.text_sha('Hej', 'Brevet'), 'mottagare': 'info@x.se', 'slug': 'x', 'bekraftad_person': False}, 'mottagare': {'epost': 'info@x.se', 'typ': 'roll', 'bekraftad_person': False}}
assert u.far_skickas(post, brev, [], False, True) == (True, 'ok')
fall = [(dict(post, status='vald'), brev, [], False, True, 'inte utkast'), (post, dict(brev, godkand={}), [], False, True, 'inte godkänt'),
        (post, dict(brev, redigerat={'amne': 'Hej', 'text': 'ändrad'}), [], False, True, 'ändrad efter'), (dict(post, fysisk_person=True), brev, [], False, True, 'MFL 19'),
        (dict(post, jurform='10', jurform_text='Enskild näringsidkare'), brev, [], False, True, 'juridisk form'), (dict(post, sparr={'reklam': True, 'epost': False}), brev, [], False, True, 'reklamspärr'),
        (dict(post, sparr={'reklam': False, 'epost': True}), brev, [], False, True, 'e-postspärr'), (post, dict(brev, mottagare={'epost': 'nej'}), [], False, True, 'mottagaradress'),
        (post, brev, [{'typ': 'e-post', 'varde': 'INFO@x.se', 'skal': 'bad'}], False, True, 'spärrad'), (post, brev, [{'typ': 'doman', 'varde': 'x.se'}], False, True, 'spärrad'),
        (post, brev, [{'typ': 'orgnr', 'varde': '556000-1234'}], False, True, 'spärrad'),
        (post, dict(brev, godkand=dict(brev['godkand'], mottagare='anna@x.se'), mottagare={'epost': 'anna@x.se', 'typ': 'person', 'bekraftad_person': False}), [], False, True, 'namngiven'),
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

echo "   utgående länkar: felstavad omdömeslänk ger information, vitlistade prövas inte"
"$ROOT/.venv/bin/python" -B -c "
import os, sys, shutil, tempfile, threading, functools, pathlib, http.server
sys.path.insert(0, '$ROOT/kontroller'); import standard_kontroll as sk
class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
tom = tempfile.mkdtemp(); srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Tyst, directory=tom))
threading.Thread(target=srv.serve_forever, daemon=True).start()
d = pathlib.Path(tempfile.mkdtemp()) / 'dist'; shutil.copytree('$S/dist', d)
om = d / 'om' / 'index.html'
om.write_text(om.read_text().replace('<h1>Om provet</h1>', '<h1>Om provet</h1><p><a href=\"http://127.0.0.1:%d/omdomen-felstavat\">Omdömen</a> <a href=\"https://www.facebook.com/prov\">Facebook</a></p>' % srv.server_port))
r = sk.rapport(d)
svar = {x['url'].split('/')[-1]: x['svar'] for x in r['utgaende']}
assert svar.get('omdomen-felstavat') == '404' and svar.get('prov', '').startswith('ej prövad'), svar
assert [i for i in r['info'] if 'omdomen-felstavat' in i['text']], r['info']
os.environ['PROV_OFFLINE'] = '1'
assert all(x['svar'].startswith('ej prövad') for x in sk.rapport(d)['utgaende'])
assert 'Utgående länkar' in sk.markdown(r)
srv.shutdown()
" || { echo "FEL: utgående länkar"; exit 1; }
echo "   utgående länkar ok"

echo "   formulärets svenska besked vid fältet och telefonfältets mönster (engelsk webbläsare, med och utan JavaScript)"
"$ROOT/.venv/bin/python" -B -c "
import sys, subprocess; sys.path.insert(0, '$ROOT/kontroller'); import prova
js = '''import { chromium } from \"playwright\";
const b = await chromium.launch(); const ut = {};
for (const js of [true, false]) {
  const s = await b.newContext({ locale: \"en-US\", javaScriptEnabled: js }); const p = await s.newPage();
  await p.goto(process.argv[1] + \"/kontakt/\"); await p.click(\"form.forfragan button[type=submit]\");
  const r = { besked: await p.\$eval(\"#ff-namn\", (e) => e.validationMessage), adress: p.url(),
    vid: await p.textContent(\"#ff-namn-fel\"), fokus: await p.evaluate(() => document.activeElement?.id) };
  await p.fill(\"#ff-namn\", \"Prov\"); await p.fill(\"#ff-telefon\", \"abc\"); await p.fill(\"#ff-meddelande\", \"Hej\");
  await p.click(\"form.forfragan button[type=submit]\");
  r.format = await p.\$eval(\"#ff-telefon\", (e) => e.validity.patternMismatch); r.tel = await p.textContent(\"#ff-telefon-fel\");
  r.namnKvar = await p.textContent(\"#ff-namn-fel\"); r.kvar = p.url();
  ut[js ? \"med\" : \"utan\"] = r;
  await s.close();
}
await b.close(); console.log(JSON.stringify(ut));'''
with prova.Server('$S/dist') as srv:
    r = subprocess.run(['node', '--input-type=module', '-e', js, srv.url], cwd='$ROOT/kontroller', capture_output=True, text=True, timeout=120)
import json; ut = json.loads(r.stdout.strip().splitlines()[-1])
assert ut['med']['besked'] == 'Skriv ditt namn.' and ut['med']['vid'] == 'Skriv ditt namn.' and ut['med']['fokus'] == 'ff-namn', ut
assert ut['med']['format'] and ut['med']['tel'].startswith('Skriv numret med siffror') and ut['med']['namnKvar'] == '' and ut['med']['kvar'].endswith('/kontakt/'), ut
assert ut['utan']['besked'] and ut['utan']['besked'] != 'Skriv ditt namn.' and ut['utan']['adress'].endswith('/kontakt/'), ut
assert ut['utan']['format'] and ut['utan']['kvar'].endswith('/kontakt/'), ut
print('   ', ut['med']['besked'], '|', ut['utan']['besked'])
" || { echo "FEL: formulärets svenska besked"; exit 1; }
echo "   formulärets besked ok"

echo "   backloggens verktyg: siffror i copy, schema.org-vokabulären, Bokadirekt, bilder och domäner, sida som text, QR"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, hashlib, pathlib, tempfile, threading, functools, http.server
sys.path.insert(0, '$ROOT/kontroller'); sys.path.insert(0, '$ROOT/dashboard')
import copy_kontroll as ck, seo_kontroll as seo, hamta_bokadirekt as hb, hamta_sajt as hs, sida_till_text as st, qr
# copy: två siffror som behöver kvitto, med rad; telefonnumret är ingen siffra i den meningen
sf = [x for x in ck.kontrollera_fil(pathlib.Path('INNEHALL.md'), 'Över 500 nöjda kunder.\n\nVi har målat sedan 2012.\n\nRing 070-123 45 67.', [])[0] if x['typ'] == 'siffra']
assert [x['rad'] for x in sf] == [1, 3], sf
# schema.org: påhittad egenskap och okänd typ ger fynd, utgången egenskap information, mallens typer passerar
f = seo.granska_schema({'@context': 'https://schema.org', '@type': 'HairSalon', 'telefonnummer': '1', 'serviceArea': 'Luleå'}, None)
assert ('JSON-LD okänd egenskap', 'telefonnummer finns inte i schema.org') in f and any(t == 'JSON-LD utgången egenskap' for t, _ in f), f
assert any(t == 'JSON-LD okänd typ' for t, _ in seo.granska_schema({'@type': 'Frisorsalong'}, None))
assert seo.granska_schema({'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Start', 'item': 'https://x.se/'}]}, None) == []
# Bokadirekt: tillståndet ur sidan, utan personalens kontakt och lösenordsfält; pris per prislista och vem
plats = {'id': 1, 'about': {'name': 'Prov', 'book': {'cancel': 1440}}, 'employees': [
    {'id': 1, 'about': {'name': 'Anna', 'priceListId': 'M'}, 'services': [10], 'contact': {'phone': 'x'}, 'password': 'y'},
    {'id': 2, 'about': {'name': 'Ellen (Elev)', 'priceListId': 'E'}, 'services': [10]}],
    'services': [{'name': 'Klippning', 'services': [{'id': 10, 'name': 'Kort hår', 'about': {'description': 'Rad ett\r\nrad två'},
        'priceType': {'prices': {'M': 520, 'E': 380}, 'durations': {'M': 2700, 'E': 3600}}}]}]}
html_ = '<script>window.__PRELOADED_STATE__ = ' + json.dumps({'place': plats}) + ';</script>'
p_ = hb.las_state(html_)
assert all('contact' not in e and 'password' not in e for e in p_['employees'])
tj = hb.tjanster_text(p_, 'https://www.bokadirekt.se/places/prov-1', '2026-10-03')
assert '- Kort hår | 520 kr / 45 min | 380 kr / 60 min | Anna, Ellen (Elev) | Rad ett / rad två' in tj and 'Avbokning senast 24 timmar' in tj, tj
om = hb.omdomen_text([{'createdAt': '2026-10-01T10:00:00Z', 'review': {'score': 5, 'text': 'Bra'}, 'author': {'name': 'A.'}, 'subject': {'employee': {'name': 'Anna'}}}], 'x', 'd')
assert om.splitlines()[2] == '2026-10-01 | 5 | A. | Anna |  | Bra', om
# hämtverktyget: bilderna laddas ned och k2 hittas genom filnamnsmönstret; sida_till_text ger samma textformat
class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
d = pathlib.Path(tempfile.mkdtemp()); (d / 'up').mkdir()
for n in (1, 2, 3): (d / 'up' / ('k%d.jpg' % n)).write_bytes(b'\xff\xd8\xff' + b'0' * 64)
(d / 'index.html').write_text('<html><head><title>Prov</title></head><body><main><h1>Prov</h1><img src=\"/up/k1.jpg\" alt=\"Fasad\" width=\"800\" height=\"600\"><img src=\"/up/k3.jpg\" alt=\"Tak\" width=\"800\" height=\"600\"></main></body></html>')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Tyst, directory=str(d)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
bas = 'http://127.0.0.1:%d' % srv.server_port; ut = pathlib.Path(tempfile.mkdtemp())
r = hs.hamta_sajt(bas, ut / 'kalla', 3, paus=0)
rader = hs.ladda_bilder(r['bildlista'], ut / 'bilder', paus=0)
assert {x['fil'] for x in rader if x['fil']} >= {'k1.jpg', 'k2.jpg', 'k3.jpg'} and any(x['fil'] == 'k2.jpg' and x['gissad'] for x in rader), rader
hs.lagg_till_i_sidor(ut / 'kalla', rader, [])
assert '## Nedladdade bilder' in (ut / 'kalla' / 'SIDOR.md').read_text()
assert 'salong-kreativ-lulea.se' in hs.domankandidater('Salong Kreativ, Luleå', 'salongkreativ.se')
st.sida_till_text(bas + '/index.html', ut / 'extern' / 'artikel')
assert (ut / 'extern' / 'artikel.txt').read_text().startswith('KÄLLA: ' + bas)
srv.shutdown()
# QR: version 1 jämförd med Project Nayuki:s referens (qrcodegen) 2026-10-03; fingeravtrycket vaktar mot regression
m = qr.matris('x')
assert len(m) == 21 and hashlib.sha256(''.join('1' if v else '0' for r in m for v in r).encode()).hexdigest()[:16] == '38232e7e263ef0ca'
assert qr.svg('http://192.168.1.23:51234/').startswith('<svg')
" || { echo "FEL: backloggens verktyg"; exit 1; }
echo "   backloggens verktyg ok"

echo "   revisionens regressionsfall (2026-10-03): commitvakt, markdown, symlänk, hämtare, utskick, granskare, seo, ateljé, spanare"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_revision.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/revision-prov.log" \
  || { echo "FEL: revisionens regressionsfall"; tail -20 "$ROOT/kunder/rokprov-mall/revision-prov.log"; exit 1; }
echo "   revisionens fall ok"

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
