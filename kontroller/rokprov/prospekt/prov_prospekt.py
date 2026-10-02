#!/usr/bin/env python3
"""Rökprov för prospektpipelinen: SCB-stubb med två sidor, /full och ett 429; nyckel- och STOPP-vakter; sajtjakt med
DuckDuckGo ersatt av en stubb; mätning av en lokal fixtursajt med de riktiga verktygen; poäng, omräkning och gallring (torr).

    .venv/bin/python -B kontroller/rokprov/prospekt/prov_prospekt.py <repots rot>
"""
import functools, http.server, json, os, pathlib, sys, tempfile, threading, urllib.parse

ROOT = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'kontroller'))
tmp = pathlib.Path(tempfile.mkdtemp())
nyckelfil = tmp / 'scb.env'; nyckelfil.write_text('SCB_API_NYCKEL=provnyckel-0123456789\n'); nyckelfil.chmod(0o600)
os.environ['NWP_PROSPEKT_NYCKELFIL'] = str(nyckelfil)

# --- SCB-stubb ---
JE = lambda pe, namn, sni, jur='49', ftg='1', reklam=1, tel=3, epost=1, ort='LULEÅ': {
    'peOrgNr': pe, 'orgNr': pe[2:], 'namn': namn, 'postAdress': {'gatuAdress': 'Hemlig gata 1', 'coAdress': 'c/o X', 'postNr': '97231', 'postOrt': ort},
    'primarNaringsgren': {'naringsgren': sni, 'rangordning': 1}, 'kommunSate': '2580', 'lanSate': '25', 'anstKl': '2', 'ftgStat': ftg, 'jurform': jur,
    'reklamSparrTyp': reklam, 'telefonSparrTyp': tel, 'epostSparrTyp': epost}
SIDA1 = [JE('165560001234', 'Norrsnickarn AB', '43320'), JE('165560005678', 'Luleå Bygg AB', '41200', ftg='9'), JE('165560009999', 'Spärrad El AB', '43210', reklam=2)]
SIDA2 = [JE('195001011234', 'Anders Målare', '43341', jur='10'), JE('165560002222', 'Frisör Fin AB', '96021'), JE('165560003333', 'Norrsnickarn AB', '43320', ort='PITEÅ')]
FULL = {'165560001234': {'tel': '0920-12345', 'epost': 'info@norrsnickarn.se', 'startDat': '2001-05-01', 'naringsgrenar': [{'naringsgren': '43320', 'rangordning': 1}, {'naringsgren': '43341', 'rangordning': 2}]},
        '195001011234': {'tel': '070-1234567', 'epost': 'anders@gmail.com', 'startDat': '2015-01-01', 'naringsgrenar': [{'naringsgren': '43341', 'rangordning': 1}]},
        '165560003333': {'tel': '0921-99999', 'epost': 'kontakt@norrsnickarn-pitea.se', 'startDat': '2019-01-01', 'naringsgrenar': [{'naringsgren': '43320', 'rangordning': 1}]}}
KODER = {'jurformkoder': [{'kod': '10', 'klartext': 'Enskild näringsidkare'}, {'kod': '49', 'klartext': 'Övriga aktiebolag'}],
         'ftgstatkoder': [{'kod': '0', 'klartext': 'Aldrig verksam'}, {'kod': '1', 'klartext': 'Verksam'}, {'kod': '9', 'klartext': 'Ej längre verksam'}],
         'reklamsparrtypkoder': [{'kod': 1, 'klartext': 'Accepterar reklam'}, {'kod': 2, 'klartext': 'Avböjer reklam'}],
         'epostsparrtypkoder': [{'kod': 1, 'klartext': 'Accepterar e-post'}, {'kod': 2, 'klartext': 'Avböjer e-post'}],
         'telefonsparrtypkoder': [{'kod': 3, 'klartext': 'Ingen spärr'}, {'kod': 2, 'klartext': 'Spärr mot telefonreklam'}],
         'anstklkoder': [{'kod': '2', 'klartext': '1-4 anställda'}], 'naringsgrenkoder': [{'kod': '43320', 'klartext': 'Byggnadssnickeriarbeten'}, {'kod': '41200', 'klartext': 'Byggande av bostadshus'}, {'kod': '43210', 'klartext': 'Elinstallationer'}, {'kod': '43341', 'klartext': 'Måleriarbeten'}, {'kod': '96021', 'klartext': 'Hårvård'}],
         'kommunkoder': [{'kod': '2580', 'klartext': 'Luleå'}]}
anrop = {'429': 0, 'alla': []}
class Stubb(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        anrop['alla'].append(self.path)
        if self.headers.get('X-API-Key') != 'provnyckel-0123456789':
            self.send_response(401); self.end_headers(); return
        u = urllib.parse.urlsplit(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path.startswith('/v1/kodtabeller/'):
            svar = KODER.get(u.path.rsplit('/', 1)[1], [])
        elif u.path == '/v1/juridiskaenheter/kommun/2580':
            if q.get('cursorId') == ['c2'] and anrop['429'] == 0:
                anrop['429'] += 1; self.send_response(429); self.send_header('Retry-After', '0'); self.end_headers(); return
            svar = {'jes': SIDA2, 'pagination': {'hasMore': False, 'nextCursorId': None, 'limit': 5000}} if q.get('cursorId') == ['c2'] else {'jes': SIDA1, 'pagination': {'hasMore': True, 'nextCursorId': 'c2', 'limit': 5000}}
        elif u.path.startswith('/v1/juridiskaenheter/') and u.path.endswith('/full'):
            pe = u.path.split('/')[3]; je = next((j for j in SIDA1 + SIDA2 if j['peOrgNr'] == pe), None)
            svar = dict(je, **FULL.get(pe, {})) if je else None
            if svar is None: self.send_response(404); self.end_headers(); return
        else:
            self.send_response(404); self.end_headers(); return
        body = json.dumps(svar).encode(); self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Stubb); threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ['NWP_PROSPEKT_SCB_BAS'] = 'http://127.0.0.1:%d/v1/' % srv.server_port
import prospektfiler as pf, prospekt as pr, prospekt_poang as pp
pf.PROSPEKT = tmp / 'prospekt'; pr.PROSPEKT = pf.PROSPEKT; pr.KODER = pf.PROSPEKT / 'KODER.json'; pr.STOPP = pf.PROSPEKT / 'STOPP'; pr.SCB_BAS = os.environ['NWP_PROSPEKT_SCB_BAS']
pr.ROOT = tmp; (tmp / 'underlag').mkdir(); (tmp / 'kunder').mkdir()
pr.NYCKELFIL = nyckelfil

# nyckel: fel rättigheter → 3; STOPP → 4 före nät
rc = pr.main(['svep', '--kampanj', 'prov-lulea', '--kommun', '2580', '--bransch', 'hantverkare']) if False else None
nyckelfil.chmod(0o644); assert pr.main(['svep', '--kampanj', 'prov-lulea', '--kommun', '2580', '--bransch', 'hantverkare']) == 3; nyckelfil.chmod(0o600)
pr.STOPP.parent.mkdir(parents=True, exist_ok=True); pr.STOPP.write_text(''); n0 = len(anrop['alla'])
assert pr.main(['svep', '--kampanj', 'prov-lulea', '--kommun', '2580', '--bransch', 'hantverkare']) == 4 and len(anrop['alla']) == n0, 'STOPP ska stoppa före nät'
pr.STOPP.unlink()
assert pr.main(['svep', '--kampanj', 'prov-lulea', '--kommun', '2580', '--bransch', 'okand']) == 2
# svep
assert pr.main(['svep', '--kampanj', 'prov-lulea', '--kommun', '2580', '--bransch', 'hantverkare']) == 0
reg = pf.las_register('prov-lulea'); k = pf.las_json(pf.PROSPEKT / 'prov-lulea' / 'KAMPANJ.json')
assert anrop['429'] == 1 and k['svep']['klar'] and k['kommun'] == 'Luleå', (anrop, k)
assert sorted(p['status'] for p in reg) == ['avvisad', 'ny', 'ny', 'ny'], [(p['slug'], p['status']) for p in reg]
slugs = sorted(p['slug'] for p in reg); assert slugs == ['anders-malare', 'norrsnickarn', 'norrsnickarn-pitea', 'sparrad-el'], slugs
n = pf.hitta_post(reg, peOrgNr='165560001234'); a = pf.hitta_post(reg, peOrgNr='195001011234'); s = pf.hitta_post(reg, peOrgNr='165560009999')
assert n['epost'] == 'info@norrsnickarn.se' and n['epost_doman'] == 'norrsnickarn.se' and n['tel'] == '0920-12345' and not n['fysisk_person'] and n['sparr'] == {'reklam': False, 'telefon': False, 'epost': False}
assert a['fysisk_person'] and a['epost'] is None and a['epost_doman'] == 'gmail.com' and a['jurform_text'] == 'Enskild näringsidkare'
assert s['status'] == 'avvisad' and s['avvisad_skal'] == 'reklamsparr' and s['sparr']['reklam'] is True
assert all('gatuAdress' not in json.dumps(p) and 'coAdress' not in json.dumps(p) and 'Hemlig' not in json.dumps(p) for p in reg)
assert n['sni'][0]['text'] == 'Byggnadssnickeriarbeten' and n['postort'] == 'Luleå' and n['anstKl_text'] == '1-4 anställda'
assert pr.main(['svep', '--kampanj', 'prov-lulea', '--kommun', '2580', '--bransch', 'hantverkare']) == 0  # klart → inget nytt
assert len(pf.las_register('prov-lulea')) == 4
print('svep ok: %d poster, 429 hanterad, cursor återupptagen' % len(reg))

# --- lokal sajt att verifiera och mäta ---
rot = tmp / 'sajt'; rot.mkdir()
(rot / 'index.html').write_text('<html><head><title>Välkommen till Norrsnickarn - snickare i Luleå och Boden, kök, trappor, altaner, fönster och mycket mer hos oss</title><meta name="viewport" content="width=device-width"><meta name="generator" content="WordPress 5.4"></head><body><h1>Välkommen till oss</h1><div class="swiper"></div><p>Norrsnickarn bygger kök i Luleå. Ring <a href="tel:092012345">0920-12345</a>. Org.nr 556000-1234.</p><form><input name="n"></form><footer>© 2019 Norrsnickarn AB</footer></body></html>', encoding='utf-8')
(rot / 'kontakt').mkdir(); (rot / 'kontakt' / 'index.html').write_text('<html lang="sv"><head><title>Kontakt</title></head><body><h1>Kontakt</h1><p>Lorem ipsum dolor.</p></body></html>')
class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
s2 = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Tyst, directory=str(rot))); threading.Thread(target=s2.serve_forever, daemon=True).start()
bas = 'http://127.0.0.1:%d/' % s2.server_port
v = pr.verifiera(bas, n); assert v and v['sakerhet'] >= 0.5, v
v2 = pr.verifiera(bas, {'namn': 'Frisör Fin AB', 'orgNr': '5560002222', 'tel': '0920-00000', 'postort': 'Luleå'}); assert v2 and v2['sakerhet'] < 0.5, v2
# sajter: e-postdomänen ger inget (fejkad domän), DuckDuckGo ersatt med stubb
pr.sok_ddgs = lambda post, kampanj, sokta, kanaler: (sokta.append('"Norrsnickarn" Luleå'), kanaler.setdefault('facebook', 'https://facebook.com/norrsnickarn'), [bas])[2]
pr.verifiera_orig = pr.verifiera
assert pr.main(['sajter', '--kampanj', 'prov-lulea', '--max', '10']) == 0
reg = pf.las_register('prov-lulea'); n = pf.hitta_post(reg, peOrgNr='165560001234'); f = pf.hitta_post(reg, slug='anders-malare'); b = pf.hitta_post(reg, slug='norrsnickarn-pitea')
assert n['sajt'] and n['sajt']['url'] == bas and n['sajt']['kalla'] == 'ddgs' and n['kanaler'].get('facebook'), n['sajt']
assert f['status'] == 'utan-sajt' and f['sajt']['kalla'] == 'ingen', f
assert b['status'] == 'ny' and not b['sajt'] and b['sajt_kandidat'] and 0.3 <= b['sajt_kandidat']['sakerhet'] < 0.5, b
assert pr.main(['sajter', '--kampanj', 'prov-lulea', '--slug', 'anders-malare', '--url', bas]) == 0
assert pf.hitta_post(pf.las_register('prov-lulea'), slug='anders-malare')['sajt']['kalla'] == 'manuell'
print('sajter ok')
# signaler ur sparad HTML + sondering
kalla = tmp / 'underlag' / 'norrsnickarn' / 'kalla'; kalla.mkdir(parents=True); (kalla / 'start.html').write_text((rot / 'index.html').read_text(encoding='utf-8'), encoding='utf-8')
sig = pp.signaler(tmp / 'underlag' / 'norrsnickarn' / 'diagnos', kalla, pr.sondera(bas), {'sidor': 2, 'bilder': 0, 'sidkarta': [], 'robots': 'ingen', 'sidlista': [{'fil': 'start', 'url': bas, 'status': 200, 'titel': 'A'}, {'fil': 'kontakt', 'url': bas + 'kontakt/', 'status': 200, 'titel': 'A'}]})
for k, vv in {'karusell': True, 'valkommen_rubrik': True, 'copyright_ar': 2019, 'copyright_gammal': True, 'tel_lank_start': True, 'formular_antal': 1, 'viewport_meta': True, 'orgnr_pa_sajt': True, 'wordpress_gammal': True, 'title_generisk': False, 'lang_saknas': True, 'canonical_saknas': True, 'description_saknas': True, 'h1_antal': 1, 'titlar_dubbla': True, 'sidkarta_saknas': True, 'https': False, 'http_till_https': False}.items():
    assert sig.get(k) == vv, (k, sig.get(k))
assert sig['title_langd'] > 60
res = pp.poang(sig); print('poäng på fixtursajten:', res['poang']); assert res['poang']['seo'] is not None and res['poang']['design'] is not None and res['poang']['hastighet'] is None
print('signaler ok')
# analysera mot fixtursajten: verktygen körs på riktigt (kontroller/ länkad in i den tillfälliga roten)
import os as _os, time as _t
_os.symlink(ROOT / 'kontroller', tmp / 'kontroller')
pr.PAUS = 0
t0 = _t.time(); assert pr.main(['analysera', '--kampanj', 'prov-lulea', '--slug', 'norrsnickarn', '--max', '1']) == 0
reg = pf.las_register('prov-lulea'); n = pf.hitta_post(reg, slug='norrsnickarn'); pro = pf.las_json(tmp / 'underlag' / 'norrsnickarn' / 'PROSPEKT.json')
print('analys på %d s; status %s; poäng %s; fel %s' % (_t.time() - t0, n['status'], n['poang'], pro.get('verktygsfel')))
assert n['status'] == 'analyserad' and n['poang']['total'] is not None, n
assert not pro['verktygsfel'], pro['verktygsfel']
d = tmp / 'underlag' / 'norrsnickarn' / 'diagnos'
for f_ in ('lighthouse/lighthouse.json', 'inspektion/INSPEKTION.json', 'inspektion/vy-390-forsta.png', 'stil/STIL.json', 'axe/axe.json', 'copy.json', 'seo.json'): assert (d / f_).is_file(), f_
lh = pf.las_json(d / 'lighthouse/lighthouse.json'); assert all(r['form'] == 'mobil' for r in lh['rader']) and all(len(r.get('forsok', [1])) == 1 for r in lh['rader']), 'en omgång, bara mobil'
assert all(x['kategori'] in ('hastighet','seo','mobil','design') for x in pro['varfor']) and pro['signaler']['karusell'] and pro['poang']['version'] == 1
print('varför:', [x['varfor'] for x in pro['varfor']][:8])
assert pr.main(['poangsatt', '--kampanj', 'prov-lulea']) == 0 and pr.main(['lista', '--kampanj', 'prov-lulea']) == 0
assert pr.main(['gallra', '--kampanj', 'prov-lulea', '--manader', '0', '--torr']) == 0
srv.shutdown(); s2.shutdown()
print('PROV OK')
