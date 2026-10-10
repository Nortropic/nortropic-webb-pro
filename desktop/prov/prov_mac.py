#!/usr/bin/env python3
"""Appens Mac-prov (kunskap/desktop.md, Prov): krasch och utkast, vila (en paus kortare och en längre än låstiden), helskärm,
kopiera och klistra in genom Redigera-menyns åtgärd, en motor som slutar svara och kommer tillbaka, en fientlig
förhandsvisning och resursmätningen i upplåst läge. Provbyggda Nortropic.app i riktig WKWebView mot en provinstans, utan
modell; resultatet som JSON och bilderna av appens fönster i utkatalogen.

    .venv/bin/python -B desktop/prov/prov_mac.py --port 4791 --ut <katalog> --motorpid <provinstansens pid> [--fientlig <slug>]

Vilan prövas med SIGSTOP och SIGCONT på appens process: väggklockan går medan processen står, som när datorn sover (en
riktig vila kan ett skript inte framkalla utan att söva ägarens dator). Motorns avbrott prövas på samma sätt med
provinstansens process (--motorpid), aldrig :4771. Den fientliga förhandsvisningen är en kandidat i provinstansen vars
byggda sida (dist/index.html) är provets fientliga sida (fientlig_sida.html; --fientlig <slug> lägger den där).
"""
import argparse
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appdrivare as ad  # noqa: E402

VERKTYG = {'claude': '/opt/homebrew/bin/claude', 'node': '/opt/homebrew/bin/node'}
RESULTAT = []
UPPLAST = "!!document.querySelector('.pt-primara') || !!document.querySelector('.ay')"


def fall(namn, prov, fn):
    t = time.time()
    try:
        belagg = fn() or {}
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'godkänt', 'belagg': belagg, 'sekunder': round(time.time() - t, 2)})
        print('ok   %s %s' % (namn, json.dumps(belagg, ensure_ascii=False)[:400]), flush=True)
    except Exception as e:  # noqa: BLE001
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'underkänt', 'fel': '%s: %s' % (type(e).__name__, e), 'spår': traceback.format_exc()[-1500:]})
        print('FEL  %s %s: %s' % (namn, type(e).__name__, e), flush=True)


def lasupp(a):
    a.vanta(lambda: a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden && !document.getElementById('las-upp').disabled"),
            text='låsvyn')
    a.js("document.getElementById('las-upp').click(), true")
    a.vanta(lambda: a.js(UPPLAST), text='upplåst')


def rss_cpu(pid):
    ut = subprocess.run(['/bin/ps', '-o', 'rss=,%cpu=', '-p', str(pid)], capture_output=True, text=True, env=dict(os.environ, LC_ALL='C')).stdout.split()
    return (int(ut[0]) // 1024, float(ut[1])) if len(ut) == 2 else (None, None)


def barn(pid):
    """Appens webbprocesser (WebKit-tjänsterna startas av launchd, inte som barn): räknas för sig, med sina namn."""
    ut = subprocess.run(['/bin/ps', '-A', '-o', 'pid=,rss=,%cpu=,comm='], capture_output=True, text=True, env=dict(os.environ, LC_ALL='C')).stdout
    return [r.split(None, 3) for r in ut.splitlines() if 'com.apple.WebKit' in r]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--rot', default=str(ad.ROT))
    ap.add_argument('--ut', required=True)
    ap.add_argument('--motorpid', type=int, help='provinstansens pid (motorns avbrott prövas med SIGSTOP/SIGCONT)')
    ap.add_argument('--fientlig', help='en kund i provinstansen vars kandidat k01 får den fientliga sidan')
    ap.add_argument('--bara', help='kommaseparerade fall: krasch,vila,helskarm,klistra,motor,fientlig,matning')
    a_ = ap.parse_args()
    if a_.port == 4771:
        raise SystemExit('provet körs mot en provinstans, aldrig mot huvudutcheckningens :4771')
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    rot = Path(a_.rot).resolve()
    bara = set((a_.bara or 'krasch,vila,helskarm,klistra,motor,fientlig,matning').split(','))
    ident = lambda: json.loads(subprocess.run(['/usr/bin/curl', '-s', '-m', '5', 'http://127.0.0.1:%d/api/desktop/identitet?utmaning=%s' % (a_.port, 'ab' * 16)],  # noqa: E731
                                              capture_output=True, text=True).stdout or '{}')
    motor = ident()
    data = Path(tempfile.mkdtemp(prefix='nwp-desktop-mac-'))

    def ny_app(**inst):
        a = ad.App(rot, a_.port, data=data)
        a.registrera(VERKTYG)
        if inst:
            f = data / 'installningar.json'
            f.write_text(json.dumps(dict(json.loads(f.read_text()), **inst)))
        return a.starta()

    try:
        if 'krasch' in bara:
            def krasch():
                a = ny_app()
                try:
                    lasupp(a)
                    a.js("location.hash = '#/ny-testkund', true")
                    a.vanta(lambda: a.js("!!document.getElementById('pt-foretag')"), text='formuläret')
                    a.js("(function(){var f=document.getElementById('pt-foretag');f.value='Kraschprovet AB (test)';f.dispatchEvent(new Event('input',{bubbles:true}));return 1})()")
                    a.vanta(lambda: 'Kraschprovet' in (a.js("JSON.stringify(Object.keys(localStorage).map(function(k){return localStorage.getItem(k)}))") or ''), text='utkastet sparat')
                    pid, motorpid = a.proc.pid, motor.get('pid')
                    a.proc.send_signal(signal.SIGKILL)  # en krasch: ingen avslutsväg körs
                    a.proc.wait(10)
                finally:
                    a.proc = None
                assert ident().get('pid') == motorpid, 'motorn påverkas inte av att appen kraschar'
                b = ny_app()
                try:
                    lasupp(b)
                    b.js("location.hash = '#/ny-testkund', true")
                    v = b.vanta(lambda: b.js("(document.getElementById('pt-foretag')||{}).value"), text='utkastet tillbaka')
                    assert v == 'Kraschprovet AB (test)', v
                    return {'kraschad_pid': pid, 'signal': 'SIGKILL', 'ny_pid': b.proc.pid, 'motorns_pid_samma': True, 'utkastet_efter_omstart': v,
                            'bild': (ut / 'mac-krasch-utkast.png').name if b.bild(ut / 'mac-krasch-utkast.png') else None}
                finally:
                    b.avsluta()
            fall('krasch: appen dödas med SIGKILL; motorn lever, och utkastet står kvar efter omstarten', 'D17 U29 U37', krasch)

        if 'vila' in bara:
            def vila():
                a = ny_app(las_efter_min=1)
                try:
                    lasupp(a)
                    a.visa()
                    pid = a.proc.pid
                    os.kill(pid, signal.SIGSTOP)
                    time.sleep(20)
                    os.kill(pid, signal.SIGCONT)
                    time.sleep(17)
                    kort = a.lage()
                    assert kort['upplast'], 'en paus kortare än låstiden låser inte'
                    os.kill(pid, signal.SIGSTOP)
                    time.sleep(75)
                    os.kill(pid, signal.SIGCONT)
                    l = a.vanta(lambda: (lambda x: x if not x['upplast'] else None)(a.lage()), tid=25, text='låset efter vilan')
                    orsak = l['url'].split('#last=')[-1] if '#last=' in (l.get('url') or '') else None
                    sessionen = json.loads(subprocess.run(['/usr/bin/curl', '-s', 'http://127.0.0.1:%d/api/desktop/lage' % a_.port], capture_output=True, text=True).stdout or '{}')
                    return {'kort_paus_s': 20, 'upplast_efter_kort_paus': True, 'lang_paus_s': 75, 'last_efter_lang_paus': True, 'orsak': orsak,
                            'fokus_fore': kort.get('fokus'), 'motorns_lage_utan_kaka': sessionen.get('session'), 'bild': a.bild(ut / 'mac-vila-last.png').name}
                finally:
                    a.avsluta()
            fall('vila: en paus kortare än låstiden behåller sessionen, en längre låser appen', 'D18 U02', vila)

        if 'helskarm' in bara:
            def helskarm():
                a = ny_app()
                try:
                    lasupp(a)
                    fore = a.lage()
                    a.fonster(helskarm=True)
                    l = a.vanta(lambda: (lambda x: x if x['helskarm'] else None)(a.lage()), tid=10, text='helskärm')
                    time.sleep(1.2)
                    spill = a.js("document.documentElement.scrollWidth > innerWidth + 1")
                    bild = a.bild(ut / 'mac-helskarm.png').name
                    a.fonster(helskarm=False)
                    e = a.vanta(lambda: (lambda x: x if not x['helskarm'] else None)(a.lage()), tid=10, text='ur helskärm')
                    time.sleep(1)
                    e = a.lage()
                    assert not spill
                    return {'fore': fore['storlek'], 'helskarm': l['storlek'], 'efter': e['storlek'], 'sidled_spill': spill, 'bild': bild, 'skarmar': len(fore.get('skarmar') or [])}
                finally:
                    a.avsluta()
            fall('helskärm: fönstret fyller skärmen utan spill och går tillbaka till sin storlek', 'D12 D19', helskarm)

        if 'klistra' in bara:
            def klistra():
                a = ny_app()
                try:
                    lasupp(a)
                    a.js("location.hash = '#/ny-testkund', true")
                    a.vanta(lambda: a.js("!!document.getElementById('pt-foretag')"), text='formuläret')
                    subprocess.run(['/usr/bin/pbcopy'], input='Klistrat från urklipp AB'.encode(), check=True, env={'LANG': 'en_US.UTF-8'})
                    a.visa()
                    a.js("(function(){var f=document.getElementById('pt-foretag');f.value='';f.focus();return document.activeElement.id})()")
                    s = a._anrop('POST', '/redigera', 'klistra')
                    v = a.vanta(lambda: a.js("document.getElementById('pt-foretag').value"), tid=5, text='det inklistrade')
                    a.js("(function(){var f=document.getElementById('pt-foretag');f.value='Kopierat ur appen';f.focus();f.select();return 1})()")
                    a._anrop('POST', '/redigera', 'kopiera')
                    time.sleep(0.4)
                    urklipp = subprocess.run(['/usr/bin/pbpaste'], capture_output=True, env={'LANG': 'en_US.UTF-8'}).stdout.decode()
                    assert v == 'Klistrat från urklipp AB', v
                    assert urklipp == 'Kopierat ur appen', urklipp
                    return {'paste_skickad': s.get('skickad'), 'inklistrat': v, 'kopierat_till_urklipp': urklipp,
                            'vag': 'Redigera-menyns åtgärder paste: och copy: genom svarskedjan; tangenttrycket själv kräver tillgänglighetsbehörighet'}
                finally:
                    a.avsluta()
            fall('kopiera och klistra in genom Redigera-menyns åtgärder i webvyn', 'D19 U37', klistra)

        if 'motor' in bara and a_.motorpid:
            def motoravbrott():
                a = ny_app()
                try:
                    lasupp(a)
                    os.kill(a_.motorpid, signal.SIGSTOP)
                    try:
                        l = a.vanta(lambda: (lambda x: x if 'franKopplad' in (x.get('url') or '') else None)(a.lage()), tid=60, text='frånkopplat läge')
                        text = a.vanta(lambda: a.js("document.body.innerText"), text='skalets text')
                        bild = a.bild(ut / 'mac-motor-borta.png').name
                    finally:
                        os.kill(a_.motorpid, signal.SIGCONT)
                    a.js("location.hash = '#'; location.reload(); true")
                    a.vanta(lambda: a.js(UPPLAST) or a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), tid=40, text='tillbaka')
                    tillbaka = a.lage()
                    return {'frankopplad_url': l['url'], 'skalets_besked': ' '.join(text.split())[:300], 'efter_sigcont': tillbaka['url'], 'upplast_efter': tillbaka['upplast'],
                            'motorns_pid_samma': ident().get('pid') == a_.motorpid, 'bild': bild}
                finally:
                    a.avsluta()
            fall('motorn slutar svara: appen visar frånkopplat läge; när motorn svarar igen nås den på nytt', 'D20 J11', motoravbrott)

        if 'fientlig' in bara and a_.fientlig:
            def fientlig():
                dist = rot / 'kunder' / a_.fientlig / 'kandidater' / 'k01' / 'sajt' / 'dist'
                dist.mkdir(parents=True, exist_ok=True)
                (dist / 'index.html').write_text(Path(__file__).with_name('fientlig_sida.html').read_text(encoding='utf-8').replace('__MOTORPORT__', str(a_.port)),
                                                 encoding='utf-8')
                a = ny_app()
                try:
                    lasupp(a)
                    a.js("window.__fientlig=null;window.addEventListener('message',function(e){if(e.data&&e.data.fientlig)window.__fientlig=e.data.fientlig});true")
                    a.js("location.hash = '#/arbetsyta/%s', true" % a_.fientlig)
                    r = a.vanta(lambda: a.js("window.__fientlig && window.__fientlig.klar ? window.__fientlig : null"), tid=40, text='den fientliga sidans rapport')
                    time.sleep(2)
                    l = a.lage()
                    session = a.js("""(function(){var x=new XMLHttpRequest();x.open('GET','/api/desktop/lage',false);x.send();return JSON.parse(x.responseText).session})()""")
                    panel = a.js("(document.getElementById('ay-redigering')||{}).innerText||''")
                    assert l['url'].startswith('http://127.0.0.1:%d/' % a_.port), l['url']
                    assert l['upplast'] and session is True, (l['upplast'], session)
                    assert 'nwp_session' not in (r.get('kakor') or ''), r.get('kakor')
                    assert r.get('tauri') in ('saknas', None) or str(r.get('invoke', '')).startswith('nekat'), r
                    assert r.get('popup') in ('null', 'blockerad'), r.get('popup')
                    assert 'Ändra i källan' not in panel, 'en förfalskad redigering ger ingen panel'
                    return {'rapport': r, 'huvudramen': l['url'], 'upplast': l['upplast'], 'sessionen_giltig': session, 'redigeringspanel': panel[:120],
                            'bild': a.bild(ut / 'mac-fientlig.png').name}
                finally:
                    a.avsluta()
            fall('fientlig förhandsvisning: ingen toppnavigering, popup, native-anrop, kaka eller skrivning når appen eller motorn', 'D07 D21 U04', fientlig)

        if 'matning' in bara:
            def matning():
                a = ny_app()
                try:
                    lasupp(a)
                    vyer = ['#/start', '#/kunder', '#/testkunder', '#/ny-testkund', '#/start']
                    for v in vyer:
                        a.js("location.hash = %s, true" % json.dumps(v))
                        time.sleep(1.5)
                    time.sleep(20)
                    prov = []
                    for _ in range(10):
                        prov.append(rss_cpu(a.proc.pid))
                        time.sleep(3)
                    rss = sorted(x[0] for x in prov if x[0] is not None)
                    cpu = sorted(x[1] for x in prov if x[1] is not None)
                    webb = barn(a.proc.pid)
                    return {'vyer': vyer, 'app_rss_mb_median': rss[len(rss) // 2], 'app_cpu_procent_median': cpu[len(cpu) // 2], 'app_cpu_max': cpu[-1],
                            'webkit_processer_i_systemet': [{'pid': w[0], 'rss_mb': int(w[1]) // 1024, 'cpu': w[2], 'namn': w[3].split('/')[-1]} for w in webb][:8],
                            'not': 'WebKit-processerna delas av alla appar med WKWebView och startas av launchd; de är inte appens egna barn'}
                finally:
                    a.avsluta()
            fall('resurser i upplåst läge efter vybyten (appens process, i vila)', 'D26', matning)
    finally:
        shutil.rmtree(data, ignore_errors=True)
    meta = {'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'macos': platform.mac_ver()[0], 'arkitektur': platform.machine(), 'motor': motor.get('version'),
            'port': a_.port, 'resultat': RESULTAT}
    (ut / 'prov_mac.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    print('%d av %d godkända' % (sum(r['utfall'] == 'godkänt' for r in RESULTAT), len(RESULTAT)))
    return 0 if all(r['utfall'] == 'godkänt' for r in RESULTAT) else 1


if __name__ == '__main__':
    sys.exit(main())
