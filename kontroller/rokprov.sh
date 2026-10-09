#!/bin/bash
# rokprov.sh — regressionsprov för kontrollerna och mallen. Kör efter varje ändring i kontroller/ eller mall/.
# Bygger mallen med två testsidor och kräver (1) grönt prov, (2) rött snabbprov när fem kända fel läggs in.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# körregistret (kontroller/korregister.py): underhållet byter inget i den delade miljön (.venv, node_modules, Homebrew)
# medan provet går; underhållets egna rökprov med en kandidat (NWP_UNDERHALL_PROV=1) anmäls inte
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korregister.py" in rokprov --pid $$ >/dev/null 2>&1 || true
trap '"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korregister.py" ut --pid $$ >/dev/null 2>&1 || true' EXIT
S="$ROOT/kunder/rokprov-mall/sajt"
export NWP_HAMTA_LOKALT=1   # provens sajter ligger på 127.0.0.1; hämtaren nekar annars adresser i det egna nätet
# städregeln (kontroller/stadning.py) städar aldrig det verkliga systemet under provet: startkontrollens diskvakt och
# underhållet i proven hoppar över den; prov_stadning.py prövar den med egna rötter, klocka, diskmått och processlista
export NWP_STADNING=av
mkdir -p "$S"
rsync -a --delete --exclude node_modules --exclude dist --exclude .astro "$ROOT/mall/astro/" "$S/"
rm -f "$S/README.md"
rsync -a "$ROOT/kontroller/rokprov/src/" "$S/src/"
rsync -a "$ROOT/kontroller/rokprov/public/" "$S/public/"
# designkontraktet: testsajtens DESIGN.md genererar CSS-variablerna som testsidorna använder (grinden design)
cp "$ROOT/kontroller/rokprov/DESIGN.md" "$S/DESIGN.md"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/design.py" rokprov-mall --skriv >/dev/null
# apple-touch-icon och delningsbild görs av verktyget varje gång, så att verktyget också prövas
node "$ROOT/kontroller/ikoner.mjs" --sajt "$S" --foto "$ROOT/kontroller/rokprov/foto.svg" --bakgrund '#0b57d0' >/dev/null
echo "   ikoner.mjs --logga: favicon.svg och en genomskinlig logga ur en PNG på vit bakgrund"
"$ROOT/.venv/bin/python" -B -c "
import pathlib, shutil, struct, subprocess, zlib
rot = pathlib.Path('$ROOT/kunder/rokprov-mall/ikonprov'); shutil.rmtree(rot, ignore_errors=True); (rot / 'sajt' / 'public').mkdir(parents=True)
def png(w, h, px):
    raw = b''.join(b'\\x00' + b''.join(bytes(px(x, y)) for x in range(w)) for y in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\\x89PNG\\r\\n\\x1a\\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
(rot / 'logga.png').write_bytes(png(64, 64, lambda x, y: (20, 20, 20) if 16 <= x < 48 and 16 <= y < 48 else (255, 255, 255)))
r = subprocess.run(['node', '$ROOT/kontroller/ikoner.mjs', '--sajt', str(rot / 'sajt'), '--foto', '$ROOT/kontroller/rokprov/foto.svg', '--logga', str(rot / 'logga.png'), '--loggfarg', '#0b57d0'], capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr[-400:]
fav = (rot / 'sajt' / 'public' / 'favicon.svg').read_text(); gen = (rot / 'sajt' / 'public' / 'logga-genomskinlig.png').read_bytes()
assert fav.startswith('<svg') and '<image href=\"data:image/png;base64,' in fav and 'viewBox=\"0 0 64 64\"' in fav, fav[:120]
assert gen[:8] == b'\\x89PNG\\r\\n\\x1a\\n' and (rot / 'sajt' / 'public' / 'apple-touch-icon.png').is_file(), 'den genomskinliga loggan och ikonen ur den'
import re; m = re.search(r'logga: (\\d+) genomskinliga och (\\d+) färgade', r.stdout); assert m and 3000 <= int(m.group(1)) <= 3100 and 1000 <= int(m.group(2)) <= 1100, r.stdout
shutil.rmtree(rot, ignore_errors=True)
" || { echo "FEL: ikoner.mjs --logga"; exit 1; }
echo "   ikoner --logga ok"
sed -i '' 's#https://ERSATT-MED-DOMAN.se#https://exempel-rokprov.se#' "$S/astro.config.mjs"
# beroendena ur mallens låsfil: en ändrad låsfil installeras om (npm ci), så att provet alltid bygger mallens versioner
if [ ! -d "$S/node_modules" ] || ! cmp -s "$ROOT/mall/astro/package-lock.json" "$S/node_modules/.nwp-las.json"; then
  (cd "$S" && npm ci --no-audit --no-fund >/dev/null) && cp "$ROOT/mall/astro/package-lock.json" "$S/node_modules/.nwp-las.json"
fi
rm -f "$ROOT/kunder/rokprov-mall/RAPPORT.md"
# testsajten har inga foton: beställningen finns, så att bildkravet (9.3) är uppfyllt på rätt sätt
mkdir -p "$ROOT/underlag/rokprov-mall"
printf '# Beställning till verksamheten\n\n- Fem foton av jobb, till startsidan och tjänstesidan.\n- Telefontid.\n' > "$ROOT/underlag/rokprov-mall/BESTALLNING.md"
# briefens resor (kunskap/resor.md): ringa, skriva, glömma ett fält och rätta; grinden resor kör dem i webbläsaren
cp "$ROOT/kontroller/rokprov/RESOR.json" "$ROOT/underlag/rokprov-mall/RESOR.json"

echo "1/2 grönt prov"
if ! "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/prova.py" rokprov-mall >/dev/null; then
  echo "FEL: provet blev rött på den rena testsajten"; sed -n '1,20p' "$ROOT/kunder/rokprov-mall/prov/PROV.md"; exit 1
fi
"$ROOT/.venv/bin/python" -c "
import json; s = json.load(open('$ROOT/kunder/rokprov-mall/prov/STATUS.json'))
assert s['ok'] and s['grindar']['design']['ok'] and s['grindar']['resor']['ok'], (s['grindar'].get('design'), s['grindar'].get('resor'))
r = json.load(open('$ROOT/kunder/rokprov-mall/prov/resor/RESOR.json'))
ids = [x['id'] for x in r['resor'] if x['motor'] == 'chromium']
assert ids == ['ring', 'skriv', 'skriv-fel-och-ratta'] and all(x['ok'] for x in r['resor']) and [k['id'] for k in r['kvar']] == ['mottagen-forfragan'], r
assert sorted((x['id'], x['motor']) for x in r['resor']) == sorted((i, m) for i in ids for m in ('chromium', 'webkit')), 'varje resa i båda motorerna'
assert not r['startsida']['webkit']['spill'] and r['startsida']['webkit']['konsolfel'] == 0 and 'WebKit' in s['info'].get('webkit', ''), (r.get('startsida'), s['info'].get('webkit'))
# mätmetoden: Lighthouse med fastställd metod och median på de representativa sidorna; axe också i tillstånd
import pathlib
lh = json.load(open('$ROOT/kunder/rokprov-mall/prov/lighthouse/lighthouse.json'))
assert pathlib.Path('$ROOT/kunder/rokprov-mall/prov/lighthouse/METOD.json').is_file() and lh['metod']['representativa'][:2] == ['/', '/kontakt/'], lh.get('metod')
assert all(len(x['forsok']) == 3 and x['matt'] == 'median' and x['spridning'][0] <= x['prestanda'] <= x['spridning'][1] for x in lh['rader'] if x['representativ']), lh['rader']
assert all(len(x['forsok']) in (1, 3) for x in lh['rader'] if not x['representativ']), lh['rader']
assert all(isinstance(u, dict) and u.get('id') and u.get('titel') and isinstance(u.get('varde'), str) and isinstance(u.get('traffar'), list) for x in lh['rader'] for u in x['underkanda']), 'varje underkänd audit med titel, mätvärde och träffar'
assert any(u.get('titel') and u.get('varde') for x in lh['rader'] for u in x['underkanda']), 'ingen underkänd audit med ifylld titel och mätvärde (den rena sajten har document-latency-insight med värde)'
ax = json.load(open('$ROOT/kunder/rokprov-mall/prov/axe/axe.json'))
assert ax['tillstand'] == ['meny', 'formularfel'] and any(x['tillstand'] == 'formularfel' and x['sida'] == '/kontakt/' and x.get('ogiltiga_falt', 0) > 0 for x in ax['rader']), [(x['vy'], x['sida'], x['tillstand']) for x in ax['rader']]
x = json.load(open('$ROOT/kunder/rokprov-mall/prov/inspektion/hem/vy-1440-extrakt.json'))
assert x.get('element') and any(e.get('typsnitt', {}).get('renderat') for e in x['element']), 'startsidans mätning saknar renderade typsnitt'
assert str(s['info'].get('designavvikelser', '')).startswith('inga'), s['info'].get('designavvikelser')
" || { echo "FEL: designkontraktets grind, startsidans mätning eller jämförelsen med DESIGN.md på testsajten"; exit 1; }
echo "   grönt (designgrinden med)"

echo "   GSAP ur låset (2026-10-07): sidan /rorelse/ bygger utan konsolfel, står stilla vid reducerad rörelse och rör sig annars"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, subprocess; sys.path.insert(0, '$ROOT/kontroller'); import prova
with prova.Server('$S/dist') as srv:
    r = subprocess.run(['node', '$ROOT/kontroller/rokprov/rorelse.mjs', srv.url], cwd='$ROOT/kontroller', capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr
print(r.stdout)
" || { echo "FEL: GSAP-sidan /rorelse/ (konsolfel, reducerad rörelse eller rörelsen)"; exit 1; }
echo "   GSAP-sidan ok"

echo "   granskarens uppdrag (torrt, ingen session) och godkännandets regel"
UPPDRAG=$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/granska.py" rokprov-mall --torr)
for krav in "kritik/GRANSKARE.md" "originalitet ≥ 7" "vy-390-ruta-01.png" "vy-1440-ruta-01.png" "kunskap/referenser-professionella.md" "kunskap/byggstandard.md" "standard.md"; do
  case "$UPPDRAG" in *"$krav"*) ;; *) echo "FEL: granskarens uppdrag saknar: $krav"; exit 1;; esac
done
# torrkörningens katalog (skärmbilderna) behövs inte efter kontrollen: annars en kvar per rökprov
TORR=$(printf '%s\n' "$UPPDRAG" | sed -n 's/^Torrkörning: \(.*\)\/PROMPT\.txt\. Ingen granskare startades\.$/\1/p' | tail -1)
case "$TORR" in */nwp-torr-*) rm -rf "$TORR";; esac
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
    (rot / str(n) / 'undersida').mkdir(parents=True)
    for fil in ('vy-390-ruta-01.png', 'vy-1440-ruta-01.png', 'vy-390-hela.png', 'vy-1440-hela.png', 'undersida/vy-390-ruta-01.png', 'undersida/vy-1440-ruta-01.png'):
        (rot / str(n) / fil).write_bytes(b'x')
(rot / 'FOTOGRAFERADE.json').write_text(json.dumps({'riktningar': {str(n): ['vy-390-ruta-01.png', 'vy-1440-ruta-01.png'] for n in (1, 2, 3)}}))  # det här försökets riktningar (R11, F34)
a.ROOT = rot.parent; a.UNDERLAG = rot.parent / 'underlag'  # inga kalibreringsankare i provet
sedda = {}
def attrapp(prompt, verktyg, ut, schema=None, max_turer=0, modell=None, effort=None, **kw):  # kw: arbetsslug med flera
    # varje domare rangordnar riktning 2 först, oavsett vilken bokstav den fått
    import re
    karta = {m.group(1): m.group(2) for m in (re.match(r'- riktning ([A-F]): .*?atelje/(\\d)/', rad) for rad in prompt.splitlines()) if m}
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
# brödsmulor följer DESIGN.md:s struktur (en designhypotes, Codex via ägaren 2026-10-05 punkt 2)
om = d / 'om' / 'index.html'; html_om = om.read_text()
utan_nav = re.sub(r'<nav class=\"brodsmulor\".*?</nav>', '', html_om, flags=re.S)
utan_bada = re.sub(r'<script type=\"application/ld\+json\">[^<]*BreadcrumbList[^<]*</script>', '', utan_nav)
assert 'BreadcrumbList' not in utan_bada and 'BreadcrumbList' in utan_nav, 'provet tar bort både den synliga navigeringen och BreadcrumbList'
design_md = pathlib.Path('$S/DESIGN.md').read_text()
(tmp / 'DESIGN.md').write_text(design_md)  # struktur.brodsmulor true: de krävs
om.write_text(utan_bada)
assert any(f['punkt'] == '7.3' and f['sida'] == '/om/' and 'Du är här' in f['text'] for f in sk.granska(d)[0]), 'deklarerade brödsmulor som saknas ska ge fel'
(tmp / 'DESIGN.md').write_text(design_md.replace('\"brodsmulor\": true', '\"brodsmulor\": false'))
assert ('7.3', '/om/') not in punkter(), 'brödsmulor som designen valt bort ska inte fällas'
om.write_text(utan_nav)
assert any(f['punkt'] == '7.3' and 'utan synliga' in f['text'] for f in sk.granska(d)[0]), 'BreadcrumbList utan synliga brödsmulor ska ge fel'
(tmp / 'DESIGN.md').unlink(); om.write_text(html_om)
# kontaktvägarna följer kundens kontaktmodell (BRIEF.md §4): telefonen var som helst på sidan, aldrig en fast plats
brief = tmp / 'BRIEF.md'
brief.write_text('# Brief\n\n## §4 Primär handling\n\n**Ring 070-000 00 00** (tel:+46700000000).\n')
km = sk.kontaktmodell(brief)
assert km and km['telefon'], km
utan_tel = re.sub(r'<a [^>]*href=\"tel:[^\"]*\"[^>]*>.*?</a>', '', html_om, flags=re.S)
assert 'tel:' not in utan_tel, 'provet tar bort varje tel-länk'
om.write_text(utan_tel)
assert any(f['punkt'] == '9.2' and f['sida'] == '/om/' for f in sk.granska(d, km)[0]), 'en kontaktmodell med telefon kräver tel-länk på sidan'
brief.write_text('# Brief\n\n## §4 Primär handling\n\n**Boka tid** i formuläret på /kontakt/.\n')
km2 = sk.kontaktmodell(brief)
assert km2 and not km2['telefon'] and km2['bokning'], km2
assert 'href=\"/kontakt/\"' in utan_tel, 'sidan länkar fortfarande till kontaktsidan'
assert not any(f['punkt'] == '9.2' and f['sida'] == '/om/' for f in sk.granska(d, km2)[0]), 'utan telefon i kontaktmodellen räcker ett nästa steg'
utan_steg = re.sub(r'<a [^>]*href=\"/kontakt/\"[^>]*>.*?</a>', '', utan_tel, flags=re.S)
assert 'href=\"/kontakt/\"' not in utan_steg and '<form' not in utan_steg, 'provet tar bort varje väg vidare'
om.write_text(utan_steg)
assert any(f['punkt'] == '9.2' and f['sida'] == '/om/' and 'nästa steg' in f['text'] for f in sk.granska(d, km2)[0]), 'en sida utan nästa steg ska ge fel'
om.write_text(html_om)
# rörelse utan prefers-reduced-motion blir fel 3.5
sidor = {f: f.read_text() for f in d.rglob('*.html')}
for f, t in sidor.items(): f.write_text(re.sub(r'@media \(prefers-reduced-motion[^{]*\{.*?\}\s*\}', '', t, flags=re.S))
(d / 'rorelse.css').write_text('a{transition:color .2s}')
assert ('3.5', '(alla)') in punkter()
for f, t in sidor.items(): f.write_text(t)
(d / 'rorelse.css').unlink()
# typsnitt: en tung fil är information; fel först när sajtens typsnitt tillsammans går över budgeten (4.3)
(d / 'tung.woff2').write_bytes(b'0' * 92 * 1024)
assert ('4.3', '(alla)') not in punkter()
assert any(i['punkt'] == '4.3' and 'tung.woff2' in i['text'] for i in sk.granska(d)[1]), 'den tunga filen står som information'
(d / 'tyngre.woff2').write_bytes(b'0' * (sk.TYPSNITT_BUDGET_KB + 10) * 1024)
assert ('4.3', '(alla)') in punkter()
(d / 'tyngre.woff2').unlink()
# budgeten gäller summan: två filer som var för sig ryms men tillsammans går över den är fel (den äldre regeln om
# bredd-axeln finns inte längre; den oberoende granskningen 2026-10-05, fynd 13)
(d / 'a.woff2').write_bytes(b'0' * 160 * 1024)
(d / 'b.woff2').write_bytes(b'0' * 160 * 1024)
assert ('4.3', '(alla)') in punkter(), 'typsnittens summa räknas mot budgeten'
(d / 'a.woff2').unlink(); (d / 'b.woff2').unlink()
# publik adress: saknas i sidfot och JSON-LD = fel 7.4
v = tmp / 'VERKSAMHET.json'
v.write_text(json.dumps({'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provby', 'publik': True}}))
assert {f['punkt'] for f in sk.adress(d, v)} == {'7.4'}
assert all(f.get('niva') == 'info' for f in sk.adress(d, v) if 'sidfoten' in f['text']) and any('JSON-LD' in f['text'] and f.get('niva') != 'info' for f in sk.adress(d, v)), \
    'sidfoten är riktningens val (information); kontaktsidan och JSON-LD är fel'
v.write_text(json.dumps({'adress': {'gata': 'Provgatan 1', 'postnummer': '123 45', 'ort': 'Provby', 'publik': False}}))
assert sk.adress(d, v) == []
# dold (obekräftad) adress som ändå står på en sida = fel 7.4 där
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
om_ = (d / 'om' / 'index.html').read_text().replace('<p>Läst i oktober.<a href=\"/\">Läs</a> mer.</p>', '<p>Ring oss på<a href=\"/\">numret</a>eller skriv.</p>')
(d / 'om' / 'index.html').write_text(om_)
assert [f for f in sk.granska(d)[0] if f['punkt'] == '9.4' and f['sida'] == '/om/' and 'mellan text och länk' in f['text']], 'ord mot länk utan mellanslag (9.4)'
(d / 'om' / 'index.html').write_text(om_.replace('på<a href=\"/\">numret</a>eller', 'på <a href=\"/\">numret</a> eller'))
assert not [f for f in sk.granska(d)[0] if f['punkt'] == '9.4' and f['sida'] == '/om/'], 'med mellanslagen inget 9.4'
for ok_ in ('Ring&nbsp;<a href=\"/\">numret</a> eller skriv.', 'Ring&#160;<a href=\"/\">numret</a>&#xA0;eller skriv.',
            '<span class=\"typ\">Telefon</span><a href=\"/\">numret</a><span class=\"alt\">eller skriv</span>'):
    (d / 'om' / 'index.html').write_text(om_.replace('Ring oss på<a href=\"/\">numret</a>eller skriv.', ok_))
    assert not [f for f in sk.granska(d)[0] if f['punkt'] == '9.4' and f['sida'] == '/om/'], 'hårt mellanslag och span som egen post i flex är inget 9.4: ' + ok_
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
assert k == {'kontext_max': 600010, 'over_halva': 1, 'meddelanden': 3, 'observerad_kontext_max': 600010}, k
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

echo "   stilrapporten: bruten klickbar text, fem mönster ur impeccable, dolda menylänkar, dubbla handlingar och text som inte ryms i sin ruta"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, subprocess, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import prova
d = pathlib.Path(tempfile.mkdtemp())
(d / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>P</title><style>body{margin:0;font:16px sans-serif}nav a{display:inline-block;width:90px}h1{font-size:18px}h2{font-size:17px;margin:0 0 40px}.kant{border-left:4px solid #d00}.liten{font-size:11px}</style></head><body><header><nav><a href=\"/\">Start</a> <a href=\"/a/\">Våra tjänster inom el och data</a></nav></header><main><h1>Rubrik</h1><p>Inledning som är lång nog att räknas här.</p><h2>Andra</h2><p>Text efter rubriken som är lång nog.</p><h2>Tredje</h2><p>Mer text efter rubriken, lång nog.</p><div class=\"kant\">Citat med färgad kant.</div><p class=\"liten\">Mycket liten brödtext, längre än tjugo tecken.</p></main></body></html>')
(d / 'platt').mkdir(); (d / 'platt' / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><title>P</title><style>h1{font-size:18px}h2{font-size:17px}p{font-size:16px}main div{margin:16px 0;padding:16px 0}</style></head><body><main><h1>Platt</h1><p>Brödtext som är lång nog att räknas.</p><h2>Under</h2><p>Mer brödtext som är lång nog.</p><div>a</div><div>b</div><div>c</div><div>d</div></main></body></html>')
# fast list längst ned (60 px) som täcker en tredjedel av en 320×180-vy (400 % zoom; byggstandarden 3.3)
(d / 'fast').mkdir(); (d / 'fast' / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>P</title><style>body{margin:0;font:16px sans-serif}.list{position:fixed;bottom:0;left:0;right:0;height:60px;background:#eee}</style></head><body><main><h1>Fast</h1><p>Text.</p></main><div class=\"list\" id=\"ring\"><a href=\"tel:+46700000000\">Ring</a></div></body></html>')
# text som inte ryms i sin ruta: ett 28 tecken långt ord i en 160 px knapp och i en 120 px spalt (backloggen 2026-10-03)
(d / 'ryms').mkdir(); (d / 'ryms' / 'index.html').write_text('<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>P</title><style>body{margin:0;font:16px sans-serif}</style></head><body><main><h1>Ryms</h1><p>Vanlig text som ryms.</p><button style=\"width:160px;overflow:hidden;white-space:nowrap\">Trädgårdsmästarutbildningen</button><div style=\"width:120px\"><p>Ett ord: Kvalitetssäkringsavdelningen</p></div></main></body></html>')
with prova.Server(d) as srv:
    subprocess.run(['node', '$ROOT/kontroller/stil.mjs', '--url=' + srv.url, '--sidor=/,/platt/,/ryms/,/fast/', '--ut=' + str(d / 'ut')], check=True, capture_output=True)
v = ' '.join(json.loads((d / 'ut' / 'STIL.json').read_text())['varningar'])
assert 'täcker 33 % av en 320×180-vy' in v and 'div#ring 60 px' in v and '/fast/' in v, v
assert 'text som inte ryms i sin ruta' in v and 'Trädgårdsmästarutbildningen' in v and 'Kvalitetssäkringsavdelningen' in v and '/ryms/ @390' in v, v
assert not any('inte ryms' in w and ('/platt/' in w or '(/ @' in w) for w in json.loads((d / 'ut' / 'STIL.json').read_text())['varningar']), 'sidorna utan överskjutande text ska inte varnas'
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
assert not ren['varningar'] or not any('utanför skärmen' in v or 'gånger i startsidans' in v or 'två gånger' in v or 'inte ryms' in v or '320×180-vy' in v for v in ren['varningar']), ren['varningar']
" || { echo "FEL: stilrapportens nya mätningar"; exit 1; }
echo "   stilrapporten ok"

echo "   resor som inte håller: fel steg, skärmbild per steg, ingen skrivning utanför provets server"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, subprocess, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import prova
d = pathlib.Path(tempfile.mkdtemp())
(d / 'RESOR.json').write_text(json.dumps({'resor': [
    {'id': 'fel-text', 'uppgift': 'texten finns inte', 'start': '/', 'forvantat': [{'text': 'Det här står ingenstans'}]},
    {'id': 'fel-lank', 'uppgift': 'fel nummer', 'start': '/', 'forvantat': [{'lank': {'valjare': 'a[href^=\"tel:\"]', 'borjar': 'tel:+4699'}}]},
    {'id': 'tomt-formular', 'uppgift': 'tomt formulär stoppas med besked', 'start': '/kontakt/', 'steg': [{'skicka': '#forfragan'}], 'forvantat': [{'fel_vid_falt': '#ff-namn'}]},
    {'id': 'fel-url', 'uppgift': 'startsidan väntas men resan står på kontaktsidan', 'start': '/kontakt/', 'forvantat': [{'url': '/'}]},
    {'id': 'falt-utan-inskick', 'uppgift': 'kontrollen framkallar inget fel själv', 'start': '/kontakt/', 'forvantat': [{'fel_vid_falt': '#ff-namn'}]},
    {'id': 'klicka-tel', 'uppgift': 'en tel-länk klickas', 'start': '/', 'steg': [{'klicka': 'a[href^=\"tel:\"]'}]},
    {'id': 'Versal', 'uppgift': 'okänd nivå', 'niva': 'Testintegration'},
    {'id': 'fel-vy', 'uppgift': 'okänd vy', 'vy': '1024', 'start': '/'}]}))
with prova.Server(pathlib.Path('$S') / 'dist') as srv:
    p = subprocess.run(['node', '$ROOT/kontroller/webblasare/resor.mjs', '--adress', srv.url + '/', '--resor', str(d / 'RESOR.json'), '--ut', str(d / 'ut')], capture_output=True, text=True)
    p2 = subprocess.run(['node', '$ROOT/kontroller/webblasare/resor.mjs', '--adress', 'https://example.com/', '--resor', str(d / 'RESOR.json'), '--ut', str(d / 'ut2')], capture_output=True, text=True)
r = json.loads((d / 'ut' / 'RESOR.json').read_text())
o = {x['id']: x for x in r['resor']}
assert p.returncode == 1 and not r['ok'] and not o['fel-text']['ok'] and 'syns inte' in o['fel-text']['skal'] and not o['fel-lank']['ok'] and 'länken går till tel:+46701234567' in o['fel-lank']['skal'], r
assert o['tomt-formular']['ok'], o['tomt-formular']
assert not o['fel-url']['ok'] and 'adressen är /kontakt/, väntade /' in o['fel-url']['skal'], o['fel-url']
assert not o['falt-utan-inskick']['ok'] and 'inte markerat' in o['falt-utan-inskick']['skal'], o['falt-utan-inskick']
assert not o['klicka-tel']['ok'] and 'förväntan lank' in o['klicka-tel']['skal'] and 'klicka' in o['klicka-tel']['skal'], o['klicka-tel']
assert any(x.startswith('versal: okänd nivå') for x in r['fel']) and any(x.startswith('fel-vy: okänd vy') for x in r['fel']) and 'fel-vy' not in o, r['fel']
assert all(pathlib.Path(s['bild']).is_file() for x in r['resor'] for s in x['steg'] if s.get('bild')) and 'HÖLL INTE' in (d / 'ut' / 'RESOR.md').read_text()
assert p2.returncode == 2 and 'lokala server' in p2.stderr, p2.stderr
" || { echo "FEL: resorna som inte håller"; exit 1; }
echo "   resorna ok"

echo "   mätmetoden och motorerna: axe i tillstånd, Lighthouse-metoden, WebKit-spill och JavaScript-fel"
"$ROOT/.venv/bin/python" -B -c "
import sys, json, subprocess, tempfile, pathlib
sys.path.insert(0, '$ROOT/kontroller'); import prova
d = pathlib.Path(tempfile.mkdtemp())
sajt = d / 'sajt'
for n in ('meny', 'fel', 'tung', 'kontakt', 'skriv', 'tack', 'nyhetsbrev'): (sajt / n).mkdir(parents=True)
huvud = '<!doctype html><html lang=\"sv\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>P</title></head><body>'
(sajt / 'index.html').write_text(huvud + '<main><h1>Bred</h1><div style=\"width:600px\">Bred rad</div></main></body></html>')
(sajt / 'meny' / 'index.html').write_text(huvud + '<header><nav><details><summary>Meny</summary><a href=\"/\">Start</a></details></nav></header><main><h1>Meny</h1></main></body></html>')
(sajt / 'fel' / 'index.html').write_text(huvud + '<main><h1>Fel</h1></main><script>throw new Error(\"provfel\")</script></body></html>')
(sajt / 'tung' / 'index.html').write_text(huvud + '<main><h1>Tung</h1>' + '<img src=\"/x.png\" alt=\"\">' * 3 + '</main></body></html>')
(sajt / 'kontakt' / 'index.html').write_text(huvud + '<main><h1>Kontakt</h1></main></body></html>')
(sajt / 'skriv' / 'index.html').write_text(huvud + '<main><h1>Skriv</h1><form id=\"f\" method=\"post\" action=\"/api/forfragan\"><input name=\"namn\" value=\"A\" aria-label=\"Namn\"><input name=\"telefon\" value=\"070\" aria-label=\"Telefon\"><textarea name=\"meddelande\" aria-label=\"Meddelande\">m</textarea><button type=\"submit\">Skicka</button></form></main></body></html>')
(sajt / 'tack' / 'index.html').write_text(huvud + '<main><h1>Tack för din förfrågan</h1></main></body></html>')
(sajt / 'nyhetsbrev' / 'index.html').write_text(huvud + '<main><h1>Nyhetsbrev</h1><form method=\"post\" action=\"/api/forfragan\"><input name=\"epost\" aria-label=\"E-post\"><button type=\"submit\">Prenumerera</button></form></main></body></html>')
assert prova.representativa_sidor(sajt, ['/', '/fel/', '/kontakt/', '/meny/', '/tung/']) == ['/', '/kontakt/', '/tung/']
(d / 'RESOR.json').write_text(json.dumps({'resor': [
    {'id': 'bred', 'uppgift': 'startsidan spiller i sidled', 'start': '/', 'forvantat': [{'text': 'Bred'}]},
    {'id': 'jsfel', 'uppgift': 'sidan kastar ett fel', 'start': '/fel/', 'forvantat': [{'text': 'Fel'}]},
    {'id': 'snedstreck', 'uppgift': 'en adress utan snedstreck omdirigeras', 'start': '/kontakt', 'forvantat': [{'text': 'Kontakt'}]},
    {'id': 'skicka', 'uppgift': 'inskicket landar på tacksidan', 'start': '/skriv/', 'steg': [{'skicka': '#f'}], 'forvantat': [{'text': 'Tack för din förfrågan'}, {'url': '/tack/'}]}]}))
with prova.Server(sajt) as srv:
    p = subprocess.run(['node', '$ROOT/kontroller/webblasare/resor.mjs', '--adress', srv.url + '/', '--resor', str(d / 'RESOR.json'), '--ut', str(d / 'ut'), '--motorer', 'chromium,webkit'], capture_output=True, text=True)
    ax = subprocess.run(['node', '$ROOT/kontroller/axe.mjs', '--url=' + srv.url, '--sidor=/meny/,/nyhetsbrev/', '--ut=' + str(d / 'axe'), '--tillstand=meny,formularfel'], capture_output=True, text=True)
    lh = subprocess.run(['node', '$ROOT/kontroller/lighthouse.mjs', '--url=' + srv.url, '--sidor=/', '--representativa=/finns-inte/', '--ut=' + str(d / 'lh')], capture_output=True, text=True)
ax2 = subprocess.run(['node', '$ROOT/kontroller/axe.mjs', '--url=https://example.com', '--sidor=/', '--ut=' + str(d / 'axe2'), '--tillstand=meny'], capture_output=True, text=True)
ax3 = subprocess.run(['node', '$ROOT/kontroller/axe.mjs', '--url=http://127.0.0.1:1', '--sidor=/', '--ut=' + str(d / 'axe3'), '--tillstand=hover'], capture_output=True, text=True)
r = json.loads((d / 'ut' / 'RESOR.json').read_text())
o = {(x['id'], x['motor']): x for x in r['resor']}
assert p.returncode == 1 and o[('bred', 'chromium')]['ok'] and not o[('bred', 'webkit')]['ok'] and 'spiller i sidled i WebKit' in o[('bred', 'webkit')]['skal'], r['resor']
assert all(not o[('jsfel', m)]['ok'] and 'JavaScript-fel' in o[('jsfel', m)]['skal'] and 'provfel' in o[('jsfel', m)]['skal'] for m in ('chromium', 'webkit')), r['resor']
# WebKit: vaktens omdirigeringssida väntas förbi (301 för /kontakt, 303 efter inskicket), som i Chromium
assert all(o[(i, m)]['ok'] for i in ('snedstreck', 'skicka') for m in ('chromium', 'webkit')), [(k, v['skal']) for k, v in o.items() if k[0] in ('snedstreck', 'skicka')]
assert r['startsida']['webkit']['spill'] and any('startsidan spiller i sidled i WebKit' in f for f in r['fel']) and pathlib.Path(r['startsida']['webkit']['bild']).is_file(), r.get('startsida')
a = json.loads((d / 'axe' / 'axe.json').read_text())
assert any(x['tillstand'] == 'meny' and x.get('oppen') and x.get('knapp') == 'Meny' for x in a['rader']), [(x['vy'], x['tillstand'], x.get('oppen'), x.get('fel')) for x in a['rader']]
# ett formulär utan fält som stoppar ett tomt inskick: inget feltillstånd att mäta, och webbläsarens felsida mäts inte
nb = [x for x in a['rader'] if x['sida'] == '/nyhetsbrev/' and x['tillstand'] == 'formularfel']
assert nb and all(x.get('matt') is False and not x.get('fel') and not x['overtradelser'] for x in nb) and a['allvarliga'] == sum(1 for x in a['rader'] for v in x['overtradelser'] if v['impact'] in ('serious', 'critical')), nb
assert ax2.returncode == 2 and 'lokala server' in ax2.stderr, ax2.stderr
assert ax3.returncode == 2 and 'okänt tillstånd' in ax3.stderr, ax3.stderr
assert lh.returncode == 2 and 'representativa' in lh.stderr, lh.stderr
" || { echo "FEL: mätmetoden och motorerna"; exit 1; }
echo "   mätmetoden och motorerna ok"

echo "   förhandsvisningen: skaparen bygger och fotograferar sin egen sida"
rm -rf "$ROOT/underlag/rokprov-mall/forhand"
FH=$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/forhandsvisa.py" rokprov-mall) || { echo "FEL: förhandsvisningen föll: $FH"; exit 1; }
for f in vy-390-forsta.png vy-390-hela.png vy-1440-forsta.png vy-1440-hela.png EXTRAKT.md FORHAND.md; do
  [ -s "$ROOT/underlag/rokprov-mall/forhand/start/varv-01/$f" ] || { echo "FEL: förhandsvisningen saknar $f"; exit 1; }
done
case "$FH" in *"underlag/rokprov-mall/forhand/start/varv-01/vy-390-forsta.png"*"Konsolfel: inga"*) ;; *) echo "FEL: förhandsvisningens utskrift: $FH"; exit 1;; esac
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/forhandsvisa.py" rokprov-mall --sida /finns-inte/ >/dev/null 2>&1 && { echo "FEL: en sida som inte finns ska ge rc 2"; exit 1; }
# efter TILLBAKA (skaparen lämnade grundidén): sajten bygger, innanför processgränsen, med mallens design.css tillbaka
# (omgranskningen av skapandeflödet, fynd 5: den flyttades, och nästa omgång kunde aldrig bygga)
"$ROOT/.venv/bin/python" -B -c "
import sys, shutil, tempfile, pathlib, os
sys.path.insert(0, '$ROOT/kontroller'); import atelje, prova, korregister
t = pathlib.Path(korregister.egen_tmp('nwp-tillbaka-', 'rokprov tillbaka'))  # registrerad: städningen raderar den bara när provet slutat
sajt = t / 'kunder' / 'tillbaka-prov' / 'sajt'
shutil.copytree('$S', sajt, symlinks=True, ignore=shutil.ignore_patterns('node_modules', 'dist', '.astro'))
os.symlink(os.path.realpath('$S/node_modules'), sajt / 'node_modules')
assert (sajt / 'src' / 'styles' / 'design.css').read_text() != atelje.MALL_DESIGN_CSS.read_text(), 'provsajtens design.css är genererad ur DESIGN.md'
atelje.KUNDER = t / 'kunder'
flyttade = atelje.lamna_sajtfiler('tillbaka-prov', t / 'lamnad')
assert 'design.css' in flyttade and (sajt / 'src' / 'styles' / 'design.css').read_text() == atelje.MALL_DESIGN_CSS.read_text(), flyttade
rc, ut = prova.bygg_inom_grans(sajt)
assert rc == 0 and (sajt / 'dist' / 'kontakt' / 'index.html').is_file(), ut[-1500:]
shutil.rmtree(t)
" || { echo "FEL: sajten bygger inte efter TILLBAKA"; exit 1; }
echo "   förhandsvisningen ok"

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
  const synlig = (sel) => p.\$eval(sel, (e) => getComputedStyle(e).display !== \"none\");
  const r = { besked: await p.\$eval(\"#ff-namn\", (e) => e.validationMessage), adress: p.url(),
    vid: await p.textContent(\"#ff-namn-fel\"), vidSynlig: await synlig(\"#ff-namn-fel\"), fokus: await p.evaluate(() => document.activeElement?.id) };
  await p.fill(\"#ff-namn\", \"Prov\"); await p.fill(\"#ff-telefon\", \"abc\"); await p.fill(\"#ff-meddelande\", \"Hej\");
  await p.click(\"form.forfragan button[type=submit]\");
  r.format = await p.\$eval(\"#ff-telefon\", (e) => e.validity.patternMismatch); r.tel = await p.textContent(\"#ff-telefon-fel\");
  r.telFormat = await p.textContent(\"#ff-telefon-format\"); r.telFormatSynlig = await synlig(\"#ff-telefon-format\"); r.telSaknasSynlig = await synlig(\"#ff-telefon-fel\");
  r.namnSynlig = await synlig(\"#ff-namn-fel\");
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
# utan JavaScript: det svenska beskedet står vid fältet och visas av CSS (:user-invalid) efter inskicksförsöket; telefonfältet
# visar formatbeskedet, inte saknas-beskedet, när det har bokstäver (backloggen 2026-10-03, :user-invalid)
assert ut['utan']['vid'] == 'Skriv ditt namn.' and ut['utan']['vidSynlig'] and not ut['utan']['namnSynlig'], ut['utan']
assert ut['utan']['telFormat'].startswith('Skriv numret med siffror') and ut['utan']['telFormatSynlig'] and not ut['utan']['telSaknasSynlig'], ut['utan']
assert ut['med']['telFormat'] == '' and not ut['med']['namnSynlig'], 'med JavaScript töms de statiska beskeden och fylls bara vid fel'
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
(d / 'up' / 'insta1.jpg').write_bytes(b'\\xff\\xd8\\xff' + b'1' * 64)
(d / 'index.html').write_text('<html><head><title>Prov</title></head><body><main><h1>Prov</h1><img src=\"/up/k1.jpg\" alt=\"Fasad\" width=\"800\" height=\"600\"><img src=\"/up/k3.jpg\" alt=\"Tak\" width=\"800\" height=\"600\"><div id=\"sb_instagram\"><img src=\"/up/plats.gif\" data-full-res=\"/up/insta1.jpg\" data-img-src-set=\"{&quot;d&quot;:&quot;/up/insta1.jpg&quot;,&quot;320&quot;:&quot;/up/insta1-320.jpg&quot;}\" alt=\"Kanelbullar på disken\"></div></main></body></html>')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Tyst, directory=str(d)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
bas = 'http://127.0.0.1:%d' % srv.server_port; ut = pathlib.Path(tempfile.mkdtemp())
r = hs.hamta_sajt(bas, ut / 'kalla', 3, paus=0)
rader = hs.ladda_bilder(r['bildlista'], ut / 'bilder', paus=0)
assert {x['fil'] for x in rader if x['fil']} >= {'k1.jpg', 'k2.jpg', 'k3.jpg'} and any(x['fil'] == 'k2.jpg' and x['gissad'] for x in rader), rader
# ett inbäddat Instagramflöde: bilden i full upplösning (data-full-res, inte platshållaren) till bilder/instagram/ med inläggets text som alt
insta = [x for x in rader if x['fil'] == 'instagram/insta1.jpg']
assert insta and insta[0]['alt'] == 'Kanelbullar på disken' and (ut / 'bilder' / 'instagram' / 'insta1.jpg').is_file() and not any('plats.gif' in x['url'] for x in rader), rader
hs.lagg_till_i_sidor(ut / 'kalla', rader, [])
sidor_md = (ut / 'kalla' / 'SIDOR.md').read_text()
assert '## Nedladdade bilder' in sidor_md and '| instagram/insta1.jpg |' in sidor_md and 'Kanelbullar på disken' in sidor_md and '| instagram |' in sidor_md, sidor_md[-800:]
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
echo "   startkontrollen och underhållet (2026-10-05): de åtta fallen, Python-låset, Homebrew, en avvisad huvudversion och ett intag"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_startkontroll.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/startkontroll-prov.log" \
  || { echo "FEL: startkontrollens och underhållets prov"; tail -20 "$ROOT/kunder/rokprov-mall/startkontroll-prov.log"; exit 1; }
echo "   startkontrollens prov ok"
echo "   dokumentationen (2026-10-06): platsregeln och dess sökvägar, hänvisningarna, arbetsregeln på ett ställe, beslutens status, backloggens spårbarhet och förteckningen"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_dokumentation.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/dokumentation-prov.log" \
  || { echo "FEL: dokumentationens prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/dokumentation-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/dokumentation-prov.log"; exit 1; }
echo "   dokumentationens prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/dokumentation-prov.log") fall)"
echo "   observationen (2026-10-06): sessionens start oförändrad, fel som inte blockerar, etiketter, känsliga strängar, två sessioner"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_observation.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/observation-prov.log" \
  || { echo "FEL: observationens prov"; tail -20 "$ROOT/kunder/rokprov-mall/observation-prov.log"; exit 1; }
echo "   observationens prov ok ($(grep '^mätning' "$ROOT/kunder/rokprov-mall/observation-prov.log" | cut -c1-160))"
echo "   städregeln (2026-10-06): worktrees, kopior, processer, tillfälliga kataloger, npm-cachen, diskvakten och redovisningen"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_stadning.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/stadning-prov.log" \
  || { echo "FEL: städningens prov"; tail -20 "$ROOT/kunder/rokprov-mall/stadning-prov.log"; exit 1; }
echo "   städningens prov ok ($(grep '^städningens prov' "$ROOT/kunder/rokprov-mall/stadning-prov.log" | cut -c1-160))"
echo "   flödesvyn (2026-10-06): kedjan ur README, blindningen före första valet, statusarna, pilotens poster"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_flode.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/flode-prov.log" \
  || { echo "FEL: flödesvyns prov"; tail -20 "$ROOT/kunder/rokprov-mall/flode-prov.log"; exit 1; }
echo "   flödesvyns prov ok"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_flodeshandling.py" >"$ROOT/kunder/rokprov-mall/flodeshandling-prov.log" 2>&1 \
  || { echo "FEL: flödeshandlingens prov"; tail -20 "$ROOT/kunder/rokprov-mall/flodeshandling-prov.log"; exit 1; }
node "$ROOT/kontroller/rokprov/revision/prov_flodeshandling_webb.mjs" "$ROOT" >"$ROOT/kunder/rokprov-mall/flodeshandling-webb-prov.log" 2>&1 \
  || { echo "FEL: flödeshandlingens webbläsarprov"; tail -20 "$ROOT/kunder/rokprov-mall/flodeshandling-webb-prov.log"; exit 1; }
echo "   flödeshandlingens API och webbläsarprov ok"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_flodesstart.py" >"$ROOT/kunder/rokprov-mall/flodesstart-prov.log" 2>&1 \
  || { echo "FEL: flödesstartens processprov"; tail -25 "$ROOT/kunder/rokprov-mall/flodesstart-prov.log"; exit 1; }
echo "   flödesstartens processprov ok"
echo "   dokumentationsvyn (2026-10-07): de fyra delarna, filtren, huvudena, besluten, blindningen, länkarna, saknade rapporter och avsändaren"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_dokumentationsvy.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/dokumentationsvy-prov.log" \
  || { echo "FEL: dokumentationsvyns prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/dokumentationsvy-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/dokumentationsvy-prov.log"; exit 1; }
echo "   dokumentationsvyns prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/dokumentationsvy-prov.log") fall)"
echo "   startkvittots betydelse (2026-10-07): körväg och fas, referensunderlaget, upptäckta verktyg, åtkomsten i ateljéns session och rollerna"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_startkvitto.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/startkvitto-prov.log" \
  || { echo "FEL: startkvittots prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/startkvitto-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/startkvitto-prov.log"; exit 1; }
echo "   startkvittots prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/startkvitto-prov.log") fall)"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_kundvakt_rest.py" >"$ROOT/kunder/rokprov-mall/kundvakt-rest.log" 2>&1 \
  || { echo "FEL: kundvaktens restprov"; tail -25 "$ROOT/kunder/rokprov-mall/kundvakt-rest.log"; exit 1; }
echo "   slutbeskedet (2026-10-07): slutposten per körning, rapporten bunden till körningen, historisk granskning, kor.sh, demon och ab, kalibreringens rättelse"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_slutpost.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/slutpost-prov.log" \
  || { echo "FEL: slutbeskedets prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/slutpost-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/slutpost-prov.log"; exit 1; }
echo "   slutbeskedets prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/slutpost-prov.log") fall)"
echo "   skisskritikens kompetens (2026-10-07): blocket, kritikens egen katalog, blindningen, kvittot, tiden, de andra sessionerna, en tom 768-bild, låset, kandidaternas oberoende och kritikens uttryckliga lista"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_skisskritik.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/skisskritik-prov.log" \
  || { echo "FEL: skisskritikens prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/skisskritik-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/skisskritik-prov.log"; exit 1; }
echo "   skisskritikens prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/skisskritik-prov.log") fall)"
echo "   metodens villkor och semantiska besökarresor"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_metodtillampning.py" >"$ROOT/kunder/rokprov-mall/metodtillampning-prov.log" 2>&1 \
  || { echo "FEL: metodtillämpningens prov"; tail -20 "$ROOT/kunder/rokprov-mall/metodtillampning-prov.log"; exit 1; }
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_resor_semantik.py" >"$ROOT/kunder/rokprov-mall/resor-semantik-prov.log" 2>&1 \
  || { echo "FEL: semantiska resors prov"; tail -20 "$ROOT/kunder/rokprov-mall/resor-semantik-prov.log"; exit 1; }
echo "   källgrundade krav och flödets ingångar"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_kallgap.py" >/dev/null 2>"$ROOT/kunder/rokprov-mall/kallgap-prov.log" \
  || { echo "FEL: källgapets prov"; tail -20 "$ROOT/kunder/rokprov-mall/kallgap-prov.log"; exit 1; }
echo "   exportens version och bevarade tidigare leverans"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_exportovergang.py" >/dev/null 2>"$ROOT/kunder/rokprov-mall/exportovergang-prov.log" \
  || { echo "FEL: exportens övergångsprov"; tail -20 "$ROOT/kunder/rokprov-mall/exportovergang-prov.log"; exit 1; }
echo "   formulärfel: bevarad text utan JS, varaktig mottagning och separat mejlavisering"
NWP_FORMULAR_WEBB=1 "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_formularfel.py" >"$ROOT/kunder/rokprov-mall/formularfel-prov.log" 2>&1 \
  || { echo "FEL: formulärets felvägar"; tail -30 "$ROOT/kunder/rokprov-mall/formularfel-prov.log"; exit 1; }
echo "   resursmåttens råvärden, okända värden och identifierade kopior"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_autonomi.py" >"$ROOT/kunder/rokprov-mall/autonomi-prov.log" 2>&1 \
  || { echo "FEL: resursmåttens prov"; tail -20 "$ROOT/kunder/rokprov-mall/autonomi-prov.log"; exit 1; }
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_abpass.py" >"$ROOT/kunder/rokprov-mall/abpass-prov.log" 2>&1 \
  || { echo "FEL: A/B-måttens prov"; tail -20 "$ROOT/kunder/rokprov-mall/abpass-prov.log"; exit 1; }
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_ab_skiss.py" >"$ROOT/kunder/rokprov-mall/ab-skiss-prov.log" 2>&1 \
  || { echo "FEL: skissens metodförsök"; tail -20 "$ROOT/kunder/rokprov-mall/ab-skiss-prov.log"; exit 1; }
echo "   ateljéns slutpost (2026-10-07): stopp och fel, återupptagningen, startvägarna, avsändarna och domloggens radslut"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_ateljeslut.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/ateljeslut-prov.log" \
  || { echo "FEL: ateljéns slutpost"; grep '^FEL' "$ROOT/kunder/rokprov-mall/ateljeslut-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/ateljeslut-prov.log"; exit 1; }
echo "   ateljéns slutpost ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/ateljeslut-prov.log") fall)"

echo "   Kundstarts privata ärenden, källor, roller, återhämtning, överlämning och lagring"
for kundprov in prov_kundstart prov_kundstart_http prov_kundstart_beredning prov_kundstart_fortsatt prov_kundstart_lagring prov_kundstart_behorighet prov_kundstart_agare prov_kundstart_matgrans prov_kundstart_flode prov_kundstart_flertur; do
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/$kundprov.py" >"$ROOT/kunder/rokprov-mall/$kundprov.log" 2>&1 \
    || { echo "FEL: $kundprov"; tail -20 "$ROOT/kunder/rokprov-mall/$kundprov.log"; exit 1; }
done
for kundvy in prov_kundstart_webb prov_kundstart_agare_webb; do
  node "$ROOT/kontroller/rokprov/revision/$kundvy.mjs" "$ROOT" >"$ROOT/kunder/rokprov-mall/$kundvy.log" 2>&1 \
    || { echo "FEL: $kundvy"; tail -20 "$ROOT/kunder/rokprov-mall/$kundvy.log"; exit 1; }
done
echo "   Kundstarts lokala prov och webbläsare ok (syntetiska ärenden; ingen riktig AI)"

echo "   Kirurgens källhälsa, överlämningssignaler, avgränsade försök och ägaryta"
for kirurgprov in prov_kirurg_loop prov_kirurg_uppfoljning prov_kirurg_kallor prov_kirurg_signaler prov_kirurg_drift prov_kirurg_forbattring; do
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/$kirurgprov.py" >"$ROOT/kunder/rokprov-mall/$kirurgprov.log" 2>&1 \
    || { echo "FEL: $kirurgprov"; tail -20 "$ROOT/kunder/rokprov-mall/$kirurgprov.log"; exit 1; }
done
node "$ROOT/kontroller/rokprov/revision/prov_kirurg_forbattring_webb.mjs" "$ROOT" >"$ROOT/kunder/rokprov-mall/prov_kirurg_forbattring_webb.log" 2>&1 \
  || { echo "FEL: Kirurgens ägaryta"; tail -20 "$ROOT/kunder/rokprov-mall/prov_kirurg_forbattring_webb.log"; exit 1; }
echo "   Kirurgens lokala prov ok (inga modeller, externa anrop eller aktiva införanden)"
echo "   byggets läsgräns per kandidat (2026-10-07): sidans kod når varken syskonet eller underlaget, bygget, kritikens förhandsvisning och utdata som förut"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_lasgrans.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/lasgrans-prov.log" \
  || { echo "FEL: läsgränsens prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/lasgrans-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/lasgrans-prov.log"; exit 1; }
echo "   läsgränsens prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/lasgrans-prov.log") fall)"
echo "   småverktygen: profilbladet ur VERKSAMHET.json (rapportens punkt 14), byggstandardens 3.2 (cqi), kundrepot, 21st, materialet, urvalet, Codex fynd R01–R08, leveransens visuella status och omgranskningens N01–N06, blindningen och arbetsroten, jämförelsen mot den godkända prototypen, kalibreringens frysning, fångsten av främmande sajter och glappen metod → resultat (F01–F03, T01–T02)"
for litet in prov_profilblad prov_standard prov_kundrepo prov_21st prov_material prov_urval prov_codex_rester prov_bildstatus prov_omgranskning prov_vinnare prov_kalibrering prov_fangst prov_metodglapp; do
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/$litet.py" >"$ROOT/kunder/rokprov-mall/$litet.log" 2>&1 \
    || { echo "FEL: $litet"; tail -20 "$ROOT/kunder/rokprov-mall/$litet.log"; exit 1; }
done
echo "   referensinspektionen (2026-10-07): bredderna ur prototypens, matchande regler, DOM-utdragets gräns, svepets brytpunkter, flera tillstånd, rörelsesekvensen, det kuraterade underlaget och DevTools-MCP:ns mekanik"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_referensinspektion.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/referensinspektion-prov.log" \
  || { echo "FEL: referensinspektionens prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/referensinspektion-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/referensinspektion-prov.log"; exit 1; }
echo "   referensinspektionens prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/referensinspektion-prov.log") fall)"
echo "   canvas-design och HIG (2026-10-07): skillen med KALLA.md och licenser, uppgiften i komposition, hig-principer.md låst och i granskning och kritik, ett koncept aldrig en prototyp, egna_bilder"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_canvas_hig.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/canvashig-prov.log" \
  || { echo "FEL: canvas-design- och HIG-provet"; grep '^FEL' "$ROOT/kunder/rokprov-mall/canvashig-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/canvashig-prov.log"; exit 1; }
echo "   canvas-design- och HIG-provet ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/canvashig-prov.log") fall)"
echo "   Motion AI Kit och GSAP (2026-10-07): skillarna med KALLA.md, MCP:n till rollen, kundvakten, metodkartans val, kvittots nivåer"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/rokprov/revision/prov_rorelse.py" "$ROOT" >/dev/null 2>"$ROOT/kunder/rokprov-mall/rorelse-prov.log" \
  || { echo "FEL: rörelsens prov"; grep '^FEL' "$ROOT/kunder/rokprov-mall/rorelse-prov.log" | cut -c1-300 || true; tail -3 "$ROOT/kunder/rokprov-mall/rorelse-prov.log"; exit 1; }
echo "   rörelsens prov ok ($(grep -c '^ok: ' "$ROOT/kunder/rokprov-mall/rorelse-prov.log") fall)"

echo "2/2 kända fel ska ge rött"
F="$S/src/pages/om/index.astro"
cp "$F" "$F.ren"
mv "$S/DESIGN.md" "$S/DESIGN.md.ren"  # designkontraktet brutet: grinden design ska bli röd
mv "$ROOT/underlag/rokprov-mall/RESOR.json" "$ROOT/underlag/rokprov-mall/RESOR.json.ren"  # inga resor: grinden resor ska bli röd
sed -i '' 's#<p><a href="/">Tillbaka</a></p>#<p style="color:\#bbb">Ljusgrå text.</p><div style="width:1800px">Bred.</div><img src="/finns-inte.png"><p><a href="/saknas/">Trasig</a></p><p><a href="/">Tillbaka</a></p>#' "$F"
set +e
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/prova.py" rokprov-mall --snabb >/dev/null
RC=$?
set -e
mv "$F.ren" "$F"
mv "$S/DESIGN.md.ren" "$S/DESIGN.md"
mv "$ROOT/underlag/rokprov-mall/RESOR.json.ren" "$ROOT/underlag/rokprov-mall/RESOR.json"
SAKNAS=$("$ROOT/.venv/bin/python" -c "
import json,sys; s=json.load(open('$ROOT/kunder/rokprov-mall/prov/STATUS.json'))
print(' '.join(g for g in ('seo','axe','spill','standard','design','resor') if s['grindar'][g]['ok']))")
if [ "$RC" -ne 1 ] || [ -n "$SAKNAS" ]; then
  echo "FEL: väntade rött i seo, axe, spill, standard, design och resor; gröna ändå: ${SAKNAS:-inga} (rc $RC)"; exit 1
fi
"$ROOT/.venv/bin/python" -c "
import json; st = json.load(open('$ROOT/kunder/rokprov-mall/prov/standard.json'))
k = [x for x in st['fel'] if x['punkt'] == '8.7']
assert any(x['sida'] == '/om/' and '404' in x['text'] for x in k) and not any(x['sida'] != '/om/' for x in k), k
" || { echo "FEL: konsolens fel (8.7) syns inte i standarden för den trasiga bilden på /om/"; exit 1; }
echo "   rött där det skulle (seo, axe, spill, standard, design, resor; konsolen 8.7 på /om/)"
echo "rökprovet OK"
