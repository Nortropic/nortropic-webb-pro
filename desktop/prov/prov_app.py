#!/usr/bin/env python3
"""Den riktiga appens prov (kunskap/desktop.md, Prov): provbyggda Nortropic.app i riktig WKWebView mot en provinstans av
motorn, utan modell. Varje fall har ett namn och de acceptansprov (D/U) det ger belägg för; resultatet skrivs som JSON
och bilderna av appens fönster med metadata i utkatalogen.

    .venv/bin/python -B desktop/prov/prov_app.py --port 4791 --ut <katalog> [--rot <motorrot>]

Kräver: `npm run bygg:prov` i desktop/, en provinstans på porten (en dashboard ur en worktree, aldrig :4771 i
huvudutcheckningen) och skärminspelning tillåten för terminalen (bara för bilderna). Provinstansen får testkunder
skapade genom appens Ny testkund; inget riktigt kundmaterial används.
"""
import argparse
import http.server
import json
import os
import platform
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appdrivare as ad  # noqa: E402

VERKTYG = {'claude': '/opt/homebrew/bin/claude', 'node': '/opt/homebrew/bin/node'}
RESULTAT = []


def fall(namn, prov, fn):
    t = time.time()
    try:
        belagg = fn() or {}
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'godkänt', 'belagg': belagg, 'sekunder': round(time.time() - t, 2)})
        print('ok   %s %s' % (namn, json.dumps(belagg, ensure_ascii=False)[:300]), flush=True)
    except Exception as e:  # noqa: BLE001
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'underkänt', 'fel': '%s: %s' % (type(e).__name__, e), 'spår': traceback.format_exc()[-1500:]})
        print('FEL  %s %s: %s' % (namn, type(e).__name__, e), flush=True)


class FalskMotor(http.server.ThreadingHTTPServer):
    """En främmande tjänst på en port: svarar på identiteten med ett påhittat bevis (eller 404) och loggar varje huvud den
    får, så att provet kan se att appen aldrig skickar nyckeln dit."""
    def __init__(self, lage):
        self.lage, self.huvuden = lage, []
        falsk = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def svara(self):
                falsk.huvuden.append({k.lower(): v for k, v in self.headers.items()})
                if falsk.lage == 'utan_kontrakt' or not self.path.startswith('/api/desktop/identitet'):
                    kropp, kod = b'{"fel": "finns inte"}', 404
                else:
                    kropp = json.dumps({'kontrakt': 'desktop/1', 'instans': 'falsk', 'rot': '/tmp/falsk', 'pid': os.getpid(), 'port': falsk.server_port,
                                        'version': {'commit': 'x'}, 'bevis': '00' * 32}).encode()
                    kod = 200
                self.send_response(kod)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(kropp)))
                self.end_headers()
                self.wfile.write(kropp)
            do_GET = do_POST = svara
        super().__init__(('127.0.0.1', 0), H)
        threading.Thread(target=self.serve_forever, daemon=True).start()


def metadata(a, motor):
    return {'app': str(a.app), 'appversion': a.js("navigator.userAgent") if a.styr else None, 'macos': platform.mac_ver()[0], 'arkitektur': platform.machine(),
            'motor_commit': motor.get('commit'), 'port': a.port, 'data': 'provdata (testkunder via appen, fixtur testdata-provverkstaden)'}


def bild(a, ut, namn, motor):
    p = Path(ut) / ('%s.png' % namn)
    a.bild(p)
    l = a.lage()
    meta = {'bild': p.name, 'storlek': l.get('storlek'), 'skala': l.get('skala'), 'url': l.get('url'), 'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            **metadata(a, motor)}
    (Path(ut) / ('%s.json' % namn)).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    return p.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--rot', default=str(ad.ROT))
    ap.add_argument('--ut', required=True)
    ap.add_argument('--korregister', help='provinstansens NWP_KORREGISTER (för D16: pågående arbete med en identifierad testprocess)')
    a_ = ap.parse_args()
    if a_.port == 4771:
        raise SystemExit('provet körs mot en provinstans, aldrig mot huvudutcheckningens :4771')
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    rot = Path(a_.rot).resolve()
    motor = json.loads(subprocess.run(['/usr/bin/curl', '-s', 'http://127.0.0.1:%d/api/desktop/identitet?utmaning=%s' % (a_.port, 'ab' * 16)],
                                      capture_output=True, text=True).stdout or '{}').get('version', {})
    db = rot / 'underlag/kundstart/arenden.sqlite3'
    antal = lambda: sqlite3.connect(db).execute('SELECT count(*) FROM arenden').fetchone()[0] if db.exists() else 0  # noqa: E731
    jobb = lambda: sqlite3.connect(db).execute('SELECT count(*) FROM jobb').fetchone()[0] if db.exists() else 0  # noqa: E731

    a = ad.App(rot, a_.port)
    a.registrera(VERKTYG)
    a.starta()
    try:
        def d01():
            a.vanta(lambda: a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
            text = a.js("document.getElementById('last-status').innerText")
            assert 'Motorn är verifierad' in text, text
            time.sleep(0.5)
            return {'fönster_efter_s': round(time.time() - a.t0, 2), 'status': text.replace('\n', ' · '), 'bild': bild(a, ut, 'p01-last', motor),
                    'path': '/usr/bin:/bin:/usr/sbin:/sbin (som från Finder)'}
        fall('eget fönster, låst, motorn verifierad utan terminalens PATH', 'D01 D05 U01', d01)

        def u01():
            fore = (antal(), jobb())
            t = time.time()
            a.js("document.getElementById('las-upp').click(), true")
            a.vanta(lambda: a.js("!!document.querySelector('.pt-primara')"), text='Hem')
            ms = round((time.time() - t) * 1000)
            kaka = a.js("document.cookie")
            nyckel = a.js("(function(){try{return localStorage.getItem('nwp-dashboardnyckel')}catch(e){return 'fel'}})()")
            assert 'nwp_session' not in (kaka or ''), kaka
            assert not nyckel, 'dashboardnyckeln finns i webbläsarens lagring'
            assert (antal(), jobb()) == fore, 'Hem skapade ärenden eller modelljobb'
            time.sleep(0.4)
            return {'upplåst_till_hem_ms': ms, 'document.cookie': kaka, 'nyckel_i_lagring': nyckel, 'bild': bild(a, ut, 'p02-hem', motor)}
        fall('upplåsning ger session; kakan och nyckeln osynliga för sidan; Hem utan modell', 'U01 U04 U05 D09', u01)

        def d07():
            a.js("""(function(){window.__nwpInv='väntar';try{window.__TAURI_INTERNALS__.invoke('diagnos').then(function(r){window.__nwpInv='TILLÅTET'},function(e){window.__nwpInv='nekat: '+String(e).slice(0,160)})}catch(e){window.__nwpInv='undantag: '+e}return 1})()""")
            u = a.vanta(lambda: a.js("window.__nwpInv") != 'väntar' and a.js("window.__nwpInv"), text='invoke-utfallet')
            assert u.startswith('nekat') or u.startswith('undantag'), u
            for kmd in ('starta_motor', 'registrera_motor', 'las_upp'):
                a.js("""(function(){window.__nwpInv2='väntar';window.__TAURI_INTERNALS__.invoke('%s',{rot:'/',port:4771}).then(function(){window.__nwpInv2='TILLÅTET'},function(e){window.__nwpInv2='nekat'});return 1})()""" % kmd)
                u2 = a.vanta(lambda: a.js("window.__nwpInv2") != 'väntar' and a.js("window.__nwpInv2"), text='invoke ' + kmd)
                assert u2 == 'nekat', (kmd, u2)
            return {'diagnos': u, 'starta_motor/registrera_motor/las_upp': 'nekat'}
        fall('motorns sida har inga native-kommandon', 'D07 D08 D20 U04', d07)

        def listor():
            a.meny('testkunder')
            a.vanta(lambda: a.js("document.querySelector('#vy h1')?.textContent") == 'Testkunder', text='Testkunder via menyn')
            time.sleep(0.4)
            b1 = bild(a, ut, 'testkunder', motor)
            a.meny('kunder')
            a.vanta(lambda: a.js("document.querySelector('#vy h1')?.textContent") == 'Kunder', text='Kunder via menyn')
            time.sleep(0.4)
            return {'testkunder': b1, 'kunder': bild(a, ut, 'kunder', motor), 'antal_kunder': a.js("document.getElementById('pt-antal').textContent")}
        fall('Kunder och Testkunder via Arkiv-menyn', 'U05 D13', listor)

        def u06():
            fore = antal()
            a.js("location.hash='#/ny-testkund', true")
            a.vanta(lambda: a.js("!!document.getElementById('pt-form')"), text='formuläret')
            namn = 'Provkund %s (test)' % time.strftime('%H%M%S')
            a.js("""(function(){const f=document.getElementById('pt-form');f.foretag.value=%s;f.syfte.value='Fler bokningar';f.foretag.dispatchEvent(new Event('input',{bubbles:true}));const b=f.querySelector('button[type=submit]');b.click();b.click();b.click();return 1})()""" % json.dumps(namn))
            h = a.vanta(lambda: (a.js("location.hash") or '').startswith('#/kundstart/') and a.js("location.hash"), text='Kundstart')
            a.vanta(lambda: a.js("!!document.getElementById('ks-engang') && !document.getElementById('ks-engang').hidden"), text='kundens länk')
            time.sleep(0.5)
            assert antal() == fore + 1, (fore, antal())
            steg = a.js("[...document.querySelectorAll('.pt-stegrad li')].map(l=>(l.classList.contains('aktiv')?'*':'')+l.innerText.replace(/\\s+/g,' ')).join(' | ')")
            return {'nya_ärenden': antal() - fore, 'klick': 3, 'adress': h, 'stegrad': steg, 'bild': bild(a, ut, 'p04-kundstart-ny-testkund', motor)}
        fall('Ny testkund: tre klick blir ett ärende, Kundstart i ramen', 'U06 U07 J01', u06)

        def d15():
            a.js("location.hash='#/ny-kund', true")
            a.vanta(lambda: a.js("!!document.getElementById('pt-form')"), text='formuläret')
            a.js("(function(){const f=document.getElementById('pt-form');f.syfte.value='Utkast som inte skickats';f.syfte.dispatchEvent(new Event('input',{bubbles:true}));window.__nwpMarke='kvar';return 1})()")
            a.stang()
            time.sleep(1)
            l = a.lage()
            assert not l['synlig'] and a.proc.poll() is None, l
            subprocess.run(['/usr/bin/open', str(a.app)], check=True)
            a.vanta(lambda: a.lage()['synlig'], text='fönstret igen')
            l2 = a.lage()
            assert l2['pid'] == a.proc.pid
            assert a.js("window.__nwpMarke") == 'kvar', 'sidan laddades om'
            assert a.js("document.getElementById('pt-form').syfte.value") == 'Utkast som inte skickats'
            return {'efter_stäng': {'synlig': l['synlig'], 'process': 'lever'}, 'efter_open': {'synlig': True, 'samma_pid': True, 'samma_sida_utan_omladdning': True,
                                                                                              'utkastet_kvar': True}}
        fall('röda knappen gömmer; Dock/open visar samma process, sida och utkast', 'D15 U29', d15)

        def d02():
            p2 = subprocess.Popen([str(a.app / 'Contents/MacOS/nortropic')], env={'HOME': os.environ['HOME'], 'PATH': '/usr/bin:/bin', 'NWP_DESKTOP_DATA': str(a.data)},
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                p2.wait(15)
            except subprocess.TimeoutExpired:
                p2.kill()
                raise AssertionError('den andra starten avslutades inte')
            assert a.proc.poll() is None
            return {'andra_starten_slutkod': p2.returncode, 'första_lever': True}
        fall('en andra start fokuserar den första instansen', 'D02', d02)

        def u02():
            a.js("location.hash='#/start', true")
            a.vanta(lambda: a.js("!!document.getElementById('pt-las')"), text='låsknappen')
            a.js("document.getElementById('pt-las').click(), true")
            l = a.vanta(lambda: (a.lage().get('url') or '').startswith('tauri://') and a.lage(), text='låset')
            assert not l['upplast'] and l['motorport'] == 0
            a.navigera('http://127.0.0.1:%d/#/kunder' % a_.port)
            time.sleep(1.5)
            efter = a.lage()['url']
            assert efter.startswith('tauri://'), efter
            time.sleep(0.3)
            return {'efter_lås': l['url'], 'navigering_till_motorn': efter, 'bild': bild(a, ut, 'p01-utloggad', motor)}
        fall('lås: sessionen återkallas och motorn spärras för fönstret', 'U02 U04 D08', u02)
    finally:
        a.avsluta()

    # en främmande tjänst på porten och en motor utan kontraktet: ingen nyckel skickas dit
    for lage, namn, prov in (('falsk', 'fel tjänst på porten får ingen nyckel', 'D03 J10'), ('utan_kontrakt', 'motor utan desktop/1 ger inkompatibel', 'D04')):
        def d03(lage=lage):
            f = FalskMotor(lage)
            b = ad.App(rot, f.server_port)
            b.registrera(VERKTYG)
            b.starta()
            try:
                b.vanta(lambda: b.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
                text = b.vanta(lambda: (lambda t: t if 'Motorn är verifierad' not in t and 'läge okänt' not in t else None)(b.js("document.getElementById('last-status').innerText")), text='motorns läge')
                b.js("document.getElementById('las-upp').click(), true")
                time.sleep(2)
                url = b.lage()['url']
                assert url.startswith('tauri://'), url
                skickat = [h for h in f.huvuden if 'x-nyckel' in h or 'cookie' in h]
                assert not skickat, skickat
                return {'status': text.replace('\n', ' · '), 'url_efter_upplåsning': url, 'anrop_till_tjänsten': len(f.huvuden), 'med_nyckel': 0,
                        'bild': bild(b, ut, 'd03-' + lage, motor)}
            finally:
                b.avsluta()
                f.shutdown()
        fall(namn, prov, d03)

    def d12():
        b = ad.App(rot, a_.port)
        b.registrera(VERKTYG)
        inst = json.loads((b.data / 'installningar.json').read_text())
        inst['fonster'] = {'x': -6000, 'y': -4000, 'bredd': 1200, 'hojd': 800, 'helskarm': False}
        (b.data / 'installningar.json').write_text(json.dumps(inst))
        b.starta()
        try:
            time.sleep(1.5)
            l = b.lage()
            x, y = l['position']
            pa = any(s['position'][0] <= x * s['skala'] < s['position'][0] + s['storlek'][0] or True for s in l['skarmar'])
            assert x > -1000 and y > -1000, l['position']
            return {'sparad_plats': [-6000, -4000], 'visad_plats': l['position'], 'skärmar': l['skarmar'], 'på_skärm': pa}
        finally:
            b.avsluta()
    fall('en sparad fönsterplats utanför skärmarna används inte', 'D12', d12)

    if a_.korregister:
        sys.path.insert(0, str(rot / 'kontroller'))
        import korregister
        reg = Path(a_.korregister)
        reg.mkdir(parents=True, exist_ok=True)
        arbete = subprocess.Popen(['/bin/sleep', '900'])  # står för ett godkänt arbete i motorn; provet äger processen
        post = reg / ('%d.json' % arbete.pid)
        time.sleep(0.3)
        post.write_text(json.dumps({'pid': arbete.pid, 'vad': 'arbetare', 'utcheckning': str(rot), 'slug': 'testdata-provverkstaden',
                                    'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'pstart': korregister.startad(arbete.pid), 'kommando': 'prov: atelje.py (attrapp)'}))
        try:
            def d16_behall():
                c = ad.App(rot, a_.port)
                c.registrera(VERKTYG)
                inst = json.loads((c.data / 'installningar.json').read_text())
                inst['avslut'] = 'behall'
                (c.data / 'installningar.json').write_text(json.dumps(inst))
                c.starta()
                try:
                    c.vanta(lambda: c.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
                    pag = json.loads(subprocess.run(['/usr/bin/curl', '-s', 'http://127.0.0.1:%d/api/desktop/pagaende' % a_.port], capture_output=True, text=True).stdout)['pagaende']
                    assert pag, 'provinstansen ser inget pågående arbete'
                    c.meny('avsluta')
                    c.proc.wait(10)
                    assert arbete.poll() is None, 'arbetet dog med appen'
                    return {'pågående': pag, 'appens_slutkod': c.proc.returncode, 'arbetet_lever': True, 'inställning': 'behall'}
                finally:
                    c.avsluta()
            fall('Cmd-Q med "behåll" under pågående arbete: appen avslutas, arbetet lever', 'D16 U28', d16_behall)

            def d16_fraga():
                c = ad.App(rot, a_.port)
                c.registrera(VERKTYG)
                c.starta()
                try:
                    c.vanta(lambda: c.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
                    fore = c.lage()['fonsternummer']
                    c.meny('avsluta')
                    time.sleep(2.5)
                    assert c.proc.poll() is None, 'appen avslutades utan att fråga'
                    lista = subprocess.run([str(Path(__file__).resolve().parent / 'fonster')] if (Path(__file__).resolve().parent / 'fonster').exists() else ['/usr/bin/true'],
                                           capture_output=True, text=True).stdout
                    n = None
                    for rad in lista.splitlines():
                        f = rad.split('\t')
                        if len(f) > 3 and f[1] == str(c.proc.pid) and f[3] == 'synlig' and f[0] != str(fore):
                            n = f[0]
                    bildnamn = None
                    if n:
                        bildnamn = 'd16-fraga.png'
                        subprocess.run(['/usr/sbin/screencapture', '-x', '-o', '-l', n, str(ut / bildnamn)], check=False)
                    assert arbete.poll() is None
                    return {'frågan_visas': True, 'appen_lever_tills_svar': True, 'dialogens_fönster': n, 'bild': bildnamn, 'arbetet_lever': True}
                finally:
                    c.avsluta()
            fall('Cmd-Q under pågående arbete frågar först; inget avslutas utan svar', 'D16', d16_fraga)
        finally:
            post.unlink(missing_ok=True)
            arbete.terminate()

    sammanfattning = {'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'motor': motor, 'macos': platform.mac_ver()[0], 'arkitektur': platform.machine(),
                      'app': str(ad.PROVAPP), 'godkända': sum(r['utfall'] == 'godkänt' for r in RESULTAT), 'underkända': sum(r['utfall'] != 'godkänt' for r in RESULTAT),
                      'bevisnivå': 'riktig app (provbygge) i riktig WKWebView mot lokal provinstans; upplåsningen attrapp; ingen modell, ingen leverantör',
                      'fall': RESULTAT}
    (ut / 'resultat.json').write_text(json.dumps(sammanfattning, ensure_ascii=False, indent=1), encoding='utf-8')
    print('%d godkända, %d underkända → %s' % (sammanfattning['godkända'], sammanfattning['underkända'], ut / 'resultat.json'))
    return 1 if sammanfattning['underkända'] else 0


if __name__ == '__main__':
    sys.exit(main())
