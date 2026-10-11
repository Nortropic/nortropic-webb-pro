#!/usr/bin/env python3
"""Repoväljaren i den riktiga appen (ägarens tillägg 2026-10-11, acceptansprov 10; kunskap/andringar.md, Repoväljaren):
provbyggda Nortropic.app i riktig WKWebView mot en provinstans ur den här worktreen med repoväljarens provprojekt
(repovaljare_fixtur.py med prefixet rvprov-: provets gh och lokala nakna repon som organisationens GitHub) och
provagenten i claudes ställe. Fallen: knappen i Ändringar och listan, ⌘O med en verklig tangent (System Events, när
terminalen får styra datorn; annars en syntetisk tangent, och det sägs), klonen efter bekräftelse med appens session
(ingen nyckel i sidan), byte av repo under en levande agent med stopp (processen finns inte kvar) och utgången
inloggning. Riktiga GitHub nås aldrig, och ingen modell startas.

    .venv/bin/python -B desktop/prov/prov_repovaljaren_app.py --ut <katalog> [--app <Nortropic.app>] [--port 4793]

Kräver ett provbygge (`npm run bygg:prov` i desktop/), och skärminspelning tillåten för terminalen för bilderna.
"""
import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'kontroller'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'kontroller' / 'rokprov' / 'revision'))
import appdrivare as ad  # noqa: E402
import atelje  # noqa: E402
import korregister  # noqa: E402
import repovaljare_fixtur as fixtur  # noqa: E402

ROT = ad.ROT
PREFIX = 'rvprov-'
FEJK = ROT / 'kontroller' / 'rokprov' / 'andringar' / 'fejkclaude.py'
VERKTYG = {'claude': '/opt/homebrew/bin/claude', 'node': '/opt/homebrew/bin/node'}
RESULTAT = []


def fall(namn, prov, fn):
    t = time.time()
    try:
        belagg = fn() or {}
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'godkänt', 'belagg': belagg, 'sekunder': round(time.time() - t, 2)})
        print('ok   %s %s' % (namn, json.dumps(belagg, ensure_ascii=False)[:400]), flush=True)
    except Exception as e:  # noqa: BLE001
        RESULTAT.append({'fall': namn, 'prov': prov, 'utfall': 'underkänt', 'fel': '%s: %s' % (type(e).__name__, e), 'spår': traceback.format_exc()[-1500:]})
        print('FEL  %s %s: %s' % (namn, type(e).__name__, e), flush=True)


def hamta(port, vag):
    with urllib.request.urlopen('http://127.0.0.1:%d%s' % (port, vag), timeout=10) as s:
        return json.loads(s.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ut', required=True)
    ap.add_argument('--app', default=str(ad.PROVAPP))
    ap.add_argument('--port', type=int, default=4793)
    a_ = ap.parse_args()
    if a_.port == 4771 or (ROT / '.git').is_dir():
        raise SystemExit('provet körs i en worktrees provinstans, aldrig i huvudutcheckningen eller mot :4771')
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    slug = lambda bas: PREFIX + bas  # noqa: E731
    with korregister.egen_tmp_med('nwp-repovaljaren-app-', 'repoväljarens appprov') as hjalp_:
        hjalp = Path(hjalp_).resolve()
        # en tidigare körnings provkunder (bara provets prefix, i worktreens privata kataloger) tas bort före den nya
        for d in (ROT / 'underlag', ROT / 'kunder'):
            for p in sorted(d.glob(PREFIX + '*')) if d.is_dir() else []:
                atelje.saker_vag(p, d)
                shutil.rmtree(p)
        miljo = fixtur.bygg(ROT, hjalp, prefix=PREFIX)
        env = dict(os.environ, **miljo, NWP_ANDRINGAR_PROVAGENT=str(FEJK), NWP_KORREGISTER=str(hjalp / 'korregister'),
                   NWP_DASHBOARD_NYCKEL=secrets.token_urlsafe(24))
        logg = open(hjalp / 'motor.logg', 'w')
        motor = subprocess.Popen([str(ROT / '.venv/bin/python'), '-B', 'dashboard/server.py', '--port', str(a_.port), '--utan-lan', '--klockor', 'av'],
                                 cwd=str(ROT), env=env, stdout=logg, stderr=subprocess.STDOUT)
        try:
            slut = time.time() + 30
            while time.time() < slut:
                try:
                    hamta(a_.port, '/api/desktop/identitet?utmaning=' + 'ab' * 16)
                    break
                except OSError:
                    time.sleep(0.3)
            a = ad.App(ROT, a_.port, app=a_.app)
            a.registrera(VERKTYG)
            a.starta()
            try:
                kor(a, a_.port, ut, hjalp, slug)
            finally:
                a.avsluta()
        finally:
            motor.terminate()
            try:
                motor.wait(15)
            except subprocess.TimeoutExpired:
                motor.kill()
            logg.close()
    (ut / 'resultat.json').write_text(json.dumps(RESULTAT, ensure_ascii=False, indent=1), encoding='utf-8')
    fel = [r for r in RESULTAT if r['utfall'] != 'godkänt']
    print('%d av %d fall godkända' % (len(RESULTAT) - len(fel), len(RESULTAT)))
    return 1 if fel else 0


def kor(a, port, ut, hjalp, slug):
    j = a.js
    bilder = []

    def bild(namn):
        try:
            a.bild(ut / ('%s.png' % namn))
            bilder.append(namn)
            return namn
        except (subprocess.CalledProcessError, OSError, KeyError) as e:
            return 'ingen bild (%s)' % type(e).__name__

    def skriv(text):  # sökrutan som en användare fyller den: värdet och input-händelsen
        return j("(()=>{const i=document.getElementById('rv-sok'); i.value=%s; i.dispatchEvent(new Event('input',{bubbles:true})); return true})()" % json.dumps(text))

    def enter():
        return j("(()=>{document.getElementById('rv-sok').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); return true})()")

    def lista_klar():
        return a.vanta(lambda: j("!!document.querySelector('#rv:not([aria-busy]) .rv-alt')"), text='väljarens lista')

    def etiketter():
        return j("[...document.querySelectorAll('#rv .rv-etikett')].map(e=>e.textContent)")

    def u01():
        a.vanta(lambda: j("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
        j("document.getElementById('las-upp').click(), true")
        a.vanta(lambda: j("!!document.querySelector('.pt-primara')"), text='Hem')
        return {'nyckel_i_sidan': j("(function(){try{return localStorage.getItem('nwp-dashboardnyckel')}catch(e){return 'fel'}})()")}
    fall('upplåst mot provinstansen', 'A10', u01)

    def lista():
        j("location.hash = '#/andringar/%s', true" % slug('alfa'))
        a.vanta(lambda: j("document.getElementById('an-lage')?.textContent.includes('Repo kund-%s')" % slug('alfa')), text='Ändringar för alfa')
        j("document.querySelector('.an-id [data-rv-oppna]').click(), true")
        lista_klar()
        e = etiketter()
        assert sorted(e) == sorted('kund-%s' % slug(x) for x in ('alfa', 'beta', 'gamma', 'utan-markor')), e
        return {'etiketter': e, 'bild': bild('r01-lista')}
    fall('knappen i Ändringar öppnar väljaren med organisationens kundrepon', 'A1 A10', lista)

    def genvag():
        j("window.repovaljaren.stang(), true")
        a.visa()
        time.sleep(0.8)
        # en verklig tangent går till det program som ligger främst: bara när det är provappen, aldrig ägarens program
        front = subprocess.run(['/usr/bin/lsappinfo', 'info', '-only', 'bundleid', subprocess.run(['/usr/bin/lsappinfo', 'front'], capture_output=True,
                               text=True).stdout.strip()], capture_output=True, text=True).stdout
        if 'se.nortropic.desktop.prov' in front:
            r = subprocess.run(['/usr/bin/osascript', '-e', 'tell application "System Events" to keystroke "o" using {command down}'],
                               capture_output=True, text=True, timeout=20)
            skal = r.stderr.strip()[-160:] or 'osascript vägrade'
        else:
            r, skal = None, 'provappen låg inte främst (%s)' % front.strip()[-80:]
        verklig = bool(r) and r.returncode == 0
        if not verklig:  # ingen verklig tangent: en syntetisk i sidan, och provet säger det
            j("window.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyO',key:'o',metaKey:true,bubbles:true})), true")
        a.vanta(lambda: j("!!document.getElementById('rv')"), text='väljaren efter ⌘O')
        lista_klar()
        return {'tangent': 'verklig (System Events)' if verklig else 'syntetisk: ' + skal,
                'bild': bild('r02-genvag')}
    fall('⌘O öppnar väljaren i appen', 'A10', genvag)

    def klon():
        skriv('beta')
        assert etiketter() == ['kund-%s' % slug('beta')], etiketter()
        enter()
        a.vanta(lambda: j("!!document.querySelector('[data-rv-ja=klona]')"), text='klonens bekräftelse')
        steg = j("document.querySelector('#rv .rv-steg').textContent")
        bild('r03-klona')
        j("document.querySelector('[data-rv-ja=klona]').click(), true")
        a.vanta(lambda: j("location.hash") == '#/andringar/%s' % slug('beta'), tid=60, text='Ändringar för beta')
        a.vanta(lambda: j("document.getElementById('an-lage')?.textContent.includes('Repo kund-%s')" % slug('beta')), text='beta i huvudet')
        a.vanta(lambda: j("!!document.querySelector('[data-an-starta]')"), text='förkontrollen grön')
        assert not j("!!document.querySelector('.an-hinder')")
        kv = json.loads((ROT / 'kunder' / slug('beta') / 'KUNDREPO.json').read_text(encoding='utf-8'))
        assert kv['arbetskopia']['fran'] == 'https://github.com/Nortropic/kund-%s' % slug('beta'), kv
        return {'bekraftelse': steg.strip()[:160], 'kvitto_fran': kv['arbetskopia']['fran'],
                'nyckel_i_sidan': j("(function(){try{return localStorage.getItem('nwp-dashboardnyckel')}catch(e){return 'fel'}})()"), 'bild': bild('r04-beta')}
    fall('klonen efter bekräftelse, skriven med appens session', 'A4 A10', klon)

    def byte():
        j("location.hash = '#/andringar/%s', true" % slug('alfa'))
        # vyn byts asynkront: först när huvudet säger rätt repo hör knappen till rätt webbplats
        a.vanta(lambda: j("document.getElementById('an-lage')?.textContent.includes('Repo kund-%s') && !!document.querySelector('[data-an-starta]')" % slug('alfa')),
                text='Starta agenten för alfa')
        j("document.querySelector('[data-an-starta]').click(), true")
        l = a.vanta(lambda: (lambda x: x if x['session'].get('lever') else None)(hamta(port, '/api/andringar/%s' % slug('alfa'))), text='agenten lever')
        pid = l['session']['pid']
        j("window.repovaljaren.oppna(), true")
        lista_klar()
        skriv('beta')
        enter()
        a.vanta(lambda: j("!!document.querySelector('[data-rv-ja=stoppa]')"), text='frågan om agenten')
        bild('r05-byte')
        j("document.querySelector('[data-rv-ja=stoppa]').click(), true")
        a.vanta(lambda: j("location.hash") == '#/andringar/%s' % slug('beta'), tid=40, text='beta efter stoppet')
        assert hamta(port, '/api/andringar/%s' % slug('alfa'))['session']['lever'] is False
        try:
            os.kill(pid, 0)
            raise AssertionError('agentprocessen %s lever efter stoppet' % pid)
        except ProcessLookupError:
            pass
        return {'stoppad_pid': pid, 'process_finns': False}
    fall('byte under levande agent: stoppet är processkontroll', 'A8 A10', byte)

    def utgangen():
        fixtur.satt_lage(hjalp, 'utgangen')
        try:
            j("window.repovaljaren.oppna(), true")
            lista_klar()
            j("document.querySelector('[data-rv-las-om]').click(), true")
            a.vanta(lambda: 'gått ut' in (j("document.getElementById('rv-besked').textContent") or ''), text='beskedet om inloggningen')
            text = j("document.getElementById('rv-besked').textContent")
            assert 'gh auth login' in text, text
            assert j("document.querySelectorAll('#rv input').length") == 1, 'ingen tokenruta'
            return {'besked': text.strip()[:220], 'bild': bild('r06-utgangen')}
        finally:
            fixtur.satt_lage(hjalp, 'ok')
            j("window.repovaljaren.stang(), true")
    fall('utgången inloggning i appen: besked och åtgärd, ingen tokenruta', 'A7 A10', utgangen)

    TEXT = ("(() => { const t = window.__andringar?.term; if (!t) return ''; const b = t.buffer.active, ut = []; for (let i = 0; i < b.length; i++) {"
            " const l = b.getLine(i); if (!l) continue; const s = l.translateToString(true); if (l.isWrapped && ut.length) ut[ut.length - 1] += s; else ut.push(s); }"
            " return ut.join('\\n'); })()")

    def framst():
        asn = subprocess.run(['/usr/bin/lsappinfo', 'front'], capture_output=True, text=True).stdout.strip()
        return 'se.nortropic.desktop.prov' in subprocess.run(['/usr/bin/lsappinfo', 'info', '-only', 'bundleid', asn], capture_output=True, text=True).stdout

    def tangent(skript):  # en verklig tangent bara när provappen ligger främst; annars None
        if not framst():
            return None
        return subprocess.run(['/usr/bin/osascript', '-e', 'tell application "System Events" to ' + skript], capture_output=True, text=True, timeout=20).returncode == 0

    def terminal():
        # Ändringar i appen (Ändringars acceptansprov 2): svenska tecken med verkliga tangenter, inklistring, storlek och avbrott
        j("location.hash = '#/andringar/%s', true" % slug('alfa'))
        # vyn byts asynkront: först när huvudet säger rätt repo hör knappen till rätt webbplats
        a.vanta(lambda: j("document.getElementById('an-lage')?.textContent.includes('Repo kund-%s') && !!document.querySelector('[data-an-starta]')" % slug('alfa')),
                text='Starta agenten för alfa')
        j("document.querySelector('[data-an-starta]').click(), true")
        try:
            a.vanta(lambda: 'redo.' in (j(TEXT) or ''), text='agenten redo')
        except TimeoutError as e:
            raise TimeoutError('%s; notisen: %r; lever: %r; terminalen finns: %r; text: %r; sidan: %r' % (
                e, j("document.getElementById('an-notis')?.textContent"), hamta(port, '/api/andringar/%s' % slug('alfa'))['session'].get('lever'),
                j("!!window.__andringar?.term"), (j(TEXT) or '')[-300:],
                j("JSON.stringify({Terminal: typeof window.Terminal, FitAddon: typeof window.FitAddon, define: typeof window.define, "
                  "skript: [...document.querySelectorAll('script[src*=xterm]')].map(s => s.src), xterm: !!document.querySelector('#an-xterm .xterm'), "
                  "slug: window.__andringar?.slug, gen: window.__andringar?.gen, hash: location.hash})"))) from e
        a.visa()
        time.sleep(0.8)
        j("window.__andringar.term.focus(), true")
        rad = 'byt öppettider 07–16 åäö ÅÄÖ @ [ ]'  # – @ [ ] kräver Option på ett svenskt tangentbord
        verkliga = tangent('keystroke "%s"' % rad) and tangent('key code 36')
        if not verkliga:
            j("window.__andringar.term.paste(%s), true" % json.dumps(rad + '\r'))
        try:
            a.vanta(lambda: ('fick: ' + rad) in (j(TEXT) or ''), text='svenska tecken')
        except TimeoutError as e:
            raise TimeoutError('%s; verkliga tangenter: %r; främst: %r; aktivt element: %r; terminalens slut: %r' % (
                e, verkliga, framst(), j("document.activeElement?.className"), (j(TEXT) or '')[-400:])) from e
        j("window.__andringar.term.paste('rad ett\\nrad två'), true")
        if not tangent('key code 36'):
            j("window.__andringar.term.paste('\\r'), true")
        a.vanta(lambda: 'fick: rad två' in (j(TEXT) or ''), text='inklistringen')
        a.fonster(bredd=1100, hojd=760)
        a.vanta(lambda: ('storlek: %sx' % j("window.__andringar.term.cols")) in (j(TEXT) or ''), text='storleken till agenten')
        # navigeringen i ett lågt fönster: en spalt (varje del börjar vid samma vänsterkant), inte två
        vanster = j("[...new Set([...document.querySelectorAll('.pt-nav > *')].map(e => Math.round(e.getBoundingClientRect().left)))]")
        assert len(vanster) == 1, 'navigeringen delas i flera spalter: %r' % vanster
        ok_c = tangent('keystroke "c" using control down')
        if not ok_c:
            j("window.__andringar.term.paste('\\u0003'), true")
        a.vanta(lambda: 'avbrott mottaget' in (j(TEXT) or ''), text='avbrottet')
        b_ = bild('r07-terminal')
        j("document.querySelector('[data-an-stoppa]').click(), true")
        a.vanta(lambda: j("!!document.querySelector('[data-an-stoppa-ja]')"), text='stoppfrågan')
        j("document.querySelector('[data-an-stoppa-ja]').click(), true")
        a.vanta(lambda: '[agenten har avslutats]' in (j(TEXT) or ''), text='stoppet')
        return {'tangenter': 'verkliga (System Events)' if verkliga else 'syntetiska (provappen låg inte främst eller fick inte styras)',
                'avbrott': 'Ctrl+C verklig' if ok_c else 'ETX genom terminalen', 'kolumner': j("window.__andringar.term.cols"), 'bild': b_}
    fall('terminalen i appen: svenska tecken, inklistring, storlek och avbrott', 'Ä2 A10', terminal)

    def karta():
        a.fonster(bredd=1440, hojd=900)
        j("location.hash = '#/kompetens', true")
        a.vanta(lambda: j("document.querySelector('.kk h1')?.textContent") == 'Kompetenskartan', text='kompetenskartan')
        luckor = j("document.querySelectorAll('.kk-lucka').length")
        return {'luckor': luckor, 'bild': bild('r08-kompetenskarta')}
    fall('kompetenskartan i appens ram', 'K A10', karta)

    def studion():
        if not (ROT / 'kunder' / 'testdata-studio' / 'kandidater').is_dir():
            return {'hoppat': 'provinstansen har ingen testdata-studio (studio_fixtur.py)'}
        j("location.hash = '#/studio/testdata-studio', true")
        a.vanta(lambda: j("!!document.getElementById('st-remsa')"), tid=30, text='designstudion')
        a.vanta(lambda: j("document.querySelectorAll('#st-remsa li').length") > 0, tid=30, text='riktningarna')
        return {'riktningar': j("document.querySelectorAll('#st-remsa li').length"), 'bild': bild('r09-studio')}
    fall('designstudion i appens ram', 'DS5 A10', studion)


if __name__ == '__main__':
    sys.exit(main())
