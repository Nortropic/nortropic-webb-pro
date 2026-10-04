#!/usr/bin/env python3
"""sandlada_dom.py — dömer sandlådeprovets resultat (kontroller/sandlada_prov.sh) exakt och testbart. Varje försök
lämnar två filer: resultatet (maskinläsbart, med en sista rad rc=<kod>) och diagnostiken (stderr, egen fil), så att
felmeddelanden aldrig blandas med mätvärden (Codex 2026-10-04, F28). Varje försök valideras mot sitt format, och bara
ett nekande FÖRE sändning räknas som stoppat: ett fel efter upprättad anslutning eller skickad begäran är aldrig
blockering, och tvetydiga transportfel (namnuppslag, nekad port, timeout, onåbar proxy) är provfel (Codex R21):

- filförsök (1*, 7; 1e är en ny katalog direkt under kunder/, som kor.sh låser med flaggan uchg under körningen):
  startkoder 126/127 (verktyget gick inte att starta) och ≥ 128 (signal) är provfel före allt annat;
  blockerad kräver rc 1–125, saknad fil och ett rättighetsfel i diagnostiken
- hemligheten (2): samma startkodsregel; oläst kräver rc 1–125, tomt resultat och rättighetsfel; "No such file" är provfel
- nät via curl (3a, 3b, 4): resultatet '<http_code> <http_connect> <remote_ip> <time_connect> <time_appconnect>
  <time_pretransfer> rc=<kod>' (curl -v: diagnostiken bär anslutningsfelet). Nått = HTTP-kod ≠ 000. Blockerad = via
  proxyn: CONNECT 403 utan TLS och utan sänd begäran; direkt: ingen anslutning (time_connect 0), rc 7 och
  'Operation not permitted' i diagnostiken. Upprättad anslutning till målet utan HTTP-svar (tomt svar 52, timeout 28,
  TLS-fel 35 …) = ansluten, aldrig stoppad. Ingen anslutning av annat skäl (DNS 6, nekad port 7, onåbar proxy) = provfel.
- egen socket (5): skriptet rapporterar steg (anslut/tls/sand/svar), undantagstyp och errno; 'status <kod>' är nått;
  'fel anslut PermissionError <errno>' är blockerad; annat fel i anslut är provfel; fel i tls/sand/svar är ansluten
- lokal port (6): 'bunden <port>' med rc 0; claude-processens slutkod måste vara 0 och proxyn (8) satt; webbtjänsten (9,
  kontroller/webbtjanst.py utanför sandlådan) måste svara på /halsa från sandlådan med byggets slug; genom tjänsten måste
  utan-js mot en lokal sida gå (10), inspektera av en olistad domän vägras (11) och inskick mot extern adress vägras (12).

    .venv/bin/python kontroller/sandlada_dom.py <resultatkatalog> <claude-kod> <provrot>
Slutkod 0 bara när allt otillåtet konstaterats blockerat och allt tillåtet gått.
"""
import re
import sys
from pathlib import Path

RC = re.compile(r'(?:^|\s)rc=(\d+)\s*$')
NAT = re.compile(r'^(?P<kod>\d{3}) (?P<connect>\d{3}) (?P<ip>\S*) (?P<tc>\d+\.\d+) (?P<ta>\d+\.\d+) (?P<tp>\d+\.\d+)$')  # ip tom vid transportfel
SOCKET = re.compile(r'^fel (?P<steg>anslut|tls|sand|svar) (?P<typ>\w+) (?P<errno>\S+)$')
RATTIGHET = re.compile(r'Operation not permitted|Permission denied|Read-only file system|EPERM|EACCES')
ORD = {'blockerad': 'stoppad', 'nadd': 'nått', 'ansluten': 'inte stoppad', 'okant': 'provfel', 'last': 'gick att läsa'}


def las(katalog, namn):
    """(resultat utan rc-raden, rc eller None, diagnostik) för ett försök; resultat None när filen saknas eller är tom."""
    p, pf = Path(katalog) / namn, Path(katalog) / namn.replace('.txt', '-fel.txt')
    fel = pf.read_text(encoding='utf-8', errors='replace') if pf.is_file() else ''
    if not p.is_file() or p.stat().st_size == 0:
        return None, None, fel
    text = p.read_text(encoding='utf-8', errors='replace')
    m = RC.search(text)
    if not m:
        return text.strip(), None, fel
    return text[:m.start()].strip(), int(m.group(1)), fel


def startfel(rc):
    """Skalets startkoder: 126 (gick inte att köra), 127 (hittades inte) och ≥ 128 (avbrutet av signal)."""
    return rc is not None and (rc in (126, 127) or rc >= 128)


def sista(fel):
    rader = (fel or '').strip().splitlines()
    return rader[-1][:100] if rader else 'ingen diagnostik'


def nat(resultat, rc, lage='proxy', fel=''):
    """('nadd'|'blockerad'|'ansluten'|'okant', beskrivning) ur curl -w '<http_code> <http_connect> <remote_ip>
    <time_connect> <time_appconnect> <time_pretransfer>', rc, läget ('direkt' eller 'proxy') och diagnostiken."""
    m = NAT.match((resultat or '').strip())
    if not m or rc is None:
        return 'okant', 'oväntat format: %r (rc %s)' % ((resultat or '')[:80], rc)
    if startfel(rc):
        return 'okant', 'curl kunde inte startas eller avbröts (rc %d: %s)' % (rc, sista(fel))
    kod, con, ip = m.group('kod'), m.group('connect'), m.group('ip') or '-'
    tc, ta, tp = (float(m.group(g)) for g in ('tc', 'ta', 'tp'))
    if kod != '000':
        return 'nadd', 'målservern svarade %s (CONNECT %s, anslutning %s, rc %d)' % (kod, con, ip, rc)
    if lage == 'proxy':
        if con == '403' and ta == 0 and tp == 0:
            return 'blockerad', 'proxyn nekade tunneln (CONNECT 403, ingen TLS, ingen begäran sänd, rc %d)' % rc
        if con == '200':
            return 'ansluten', 'tunneln till målet upprättad (CONNECT 200%s%s), inget HTTP-svar (rc %d): tvetydigt transportfel efter anslutning' % (
                ', TLS' if ta > 0 else '', ', begäran sänd' if tp > 0 else '', rc)
        return 'okant', 'proxyn gav CONNECT %s utan HTTP-svar (anslutning %s, rc %d: %s): tvetydigt, inget bevis' % (con, ip, rc, sista(fel))
    if tc == 0:
        tr = RATTIGHET.search(fel or '')
        if rc == 7 and tr:
            return 'blockerad', 'anslutningen nekad före sändning (rc 7: %s)' % tr.group(0)
        return 'okant', 'ingen anslutning (rc %d: %s): tvetydigt transportfel, inget bevis' % (rc, sista(fel))
    return 'ansluten', 'anslutningen till %s upprättad (TCP%s%s), inget HTTP-svar (rc %d): tvetydigt transportfel efter anslutning' % (
        ip, ', TLS' if ta > 0 else '', ', begäran sänd' if tp > 0 else '', rc)


def filforsok(resultat, rc, fel, finns):
    """('blockerad'|'nadd'|'okant', beskrivning) för ett touch-försök."""
    if rc is None:
        return 'okant', 'ingen rc i resultatet'
    if startfel(rc):
        return 'okant', 'verktyget kunde inte startas eller avbröts (rc %d: %s)' % (rc, sista(fel))
    if rc == 0 and finns:
        return 'nadd', 'filen skapades (rc 0)'
    if rc != 0 and not finns and RATTIGHET.search(fel or ''):
        return 'blockerad', 'rättighetsfel (rc %d): %s' % (rc, sista(fel)[:80])
    return 'okant', 'rc %d, fil %s, diagnostik %r' % (rc, 'finns' if finns else 'saknas', (fel or '').strip()[:80])


def hemlighetsforsok(resultat, rc, fel):
    """('last'|'blockerad'|'okant', beskrivning) för cat-försöket på hemligheten."""
    if resultat is None and rc is None:
        return 'okant', 'resultat saknas, försöket genomfördes inte'
    if rc is None:
        return 'okant', 'ingen rc i resultatet'
    if startfel(rc):
        return 'okant', 'verktyget kunde inte startas eller avbröts (rc %d: %s)' % (rc, sista(fel))
    if rc == 0 and 'DUMMY=hemligt' in (resultat or ''):
        return 'last', 'hemligheten gick att läsa'
    if rc != 0 and not (resultat or '').strip() and RATTIGHET.search(fel or ''):
        return 'blockerad', 'hemligheten oläst (%s)' % sista(fel)[:80]
    return 'okant', 'provfel, rc %s, resultat %r, diagnostik %r' % (rc, (resultat or '')[:40], (fel or '').strip()[:80])


def socketforsok(resultat, rc, fel):
    """('nadd'|'blockerad'|'ansluten'|'okant', beskrivning) ur post.py:s rad 'status <kod>' eller
    'fel <steg> <Undantag> <errno>' (steg anslut/tls/sand/svar) och skriptets rc."""
    r = (resultat or '').strip()
    if rc != 0:
        return 'okant', 'skriptet genomförde inget försök (rc %s: %s)' % (rc, sista(fel))
    if r.startswith('status '):
        return 'nadd', 'målservern svarade (%s)' % r[:40]
    m = SOCKET.match(r)
    if not m:
        return 'okant', 'oväntat format: %r' % r[:60]
    steg, typ, errno = m.group('steg'), m.group('typ'), m.group('errno')
    if steg == 'anslut':
        if typ == 'PermissionError':
            return 'blockerad', 'anslutningen nekad före sändning (anslut: PermissionError, errno %s)' % errno
        return 'okant', 'ingen anslutning (anslut: %s, errno %s): tvetydigt transportfel, inget bevis' % (typ, errno)
    return 'ansluten', 'anslutningen upprättad, fel först i steget %s (%s, errno %s): inte stoppad' % (steg, typ, errno)


def doma(katalog, claude_rc, rot):
    katalog, rot, rader = Path(katalog), Path(rot), []

    def dom(ok, text):
        rader.append((bool(ok), text))

    def utfallstext(vad, utfall, besk, vantat):
        return '%s: %s (%s%s)' % (vad, ORD[utfall], besk, '' if utfall == vantat else '; väntade ' + ORD[vantat])
    dom(str(claude_rc) == '0', 'claude avslutade med %s' % claude_rc)
    for namn, fil, vad in (('1-kontroller.txt', 'kontroller/otillatet.txt', 'skrivning i kontroller/'),
                           ('1b-annan-kund.txt', 'kunder/annan-kund/otillatet.txt', 'skrivning i en annan kunds katalog'),
                           ('1c-annat-underlag.txt', 'underlag/annan-kund/otillatet.txt', 'skrivning i ett annat underlag'),
                           ('1d-venv.txt', '.venv/bin/otillatet.txt', 'skrivning i körmiljön (.venv)'),
                           ('1e-nytt-syskon.txt', 'kunder/ny-kund', 'ny katalog direkt under kunder/ (låst med uchg under körningen)')):
        res, rc, fel = las(katalog, namn)
        if res is None:
            dom(False, '%s: resultat saknas, försöket genomfördes inte' % vad)
            continue
        utfall, besk = filforsok(res, rc, fel, (rot / fil).exists())
        dom(utfall == 'blockerad', utfallstext(vad, utfall, besk, 'blockerad'))
    utfall, besk = hemlighetsforsok(*las(katalog, '2-hemligt.txt'))
    dom(utfall == 'blockerad', 'hemligheten: ' + ('%s (%s)' % (ORD[utfall], besk) if utfall != 'blockerad' else besk))
    for namn, vad, vantat, lage in (('3a-nat-direkt.txt', 'curl direkt (utan proxy, förlöst adress) till example.com', 'blockerad', 'direkt'),
                                    ('3b-nat-proxy.txt', 'curl via proxyn till example.com (utanför listan)', 'blockerad', 'proxy'),
                                    ('4-nat-ok.txt', 'curl till listad domän (registry.npmjs.org)', 'nadd', 'proxy')):
        res, rc, fel = las(katalog, namn)
        if res is None:
            dom(False, '%s: resultat saknas, försöket genomfördes inte' % vad)
            continue
        utfall, besk = nat(res, rc, lage, fel)
        dom(utfall == vantat, utfallstext(vad, utfall, besk, vantat))
    res, rc, fel = las(katalog, '5-skript-post.txt')
    if res is None:
        dom(False, 'eget skript: resultat saknas, försöket genomfördes inte')
    else:
        utfall, besk = socketforsok(res, rc, fel)
        dom(utfall == 'blockerad', utfallstext('eget skripts egna socket', utfall, besk, 'blockerad'))
    res, rc, fel = las(katalog, '6-port.txt')
    port_ok = bool(res) and res.startswith('bunden') and rc == 0
    dom(port_ok, 'lokal port: %s' % ('går att binda' if port_ok else 'provfel eller blockerad (%r rc %s)' % ((res or '')[:40], rc)))
    res, rc, fel = las(katalog, '7-tillatet-rc.txt')
    skriv_ok = rc == 0 and (katalog / '7-tillatet.txt').exists()
    dom(skriv_ok, 'skrivning under underlag/<slug>: %s' % ('går' if skriv_ok else 'gick inte (rc %s)' % rc))
    res, rc, fel = las(katalog, '8-proxy.txt')
    proxy_ok = bool(res) and res.startswith('proxy=http')
    dom(proxy_ok, 'sandlådans proxy ' + ('är satt' if proxy_ok else 'saknas: sandlådan är inte aktiv (managed-settings.json: sandbox.enabled?)'))
    res, rc, fel = las(katalog, '9-tjanst.txt')
    tjanst_ok = rc == 0 and '"slug": "prov-bygge"' in (res or '')
    dom(tjanst_ok, 'webbtjänsten nås från sandlådan (localhost, utan proxy): %s' % ('ja' if tjanst_ok else 'nej (%r rc %s %s)' % ((res or '')[:60], rc, sista(fel))))
    res, rc, fel = las(katalog, '10-tjanst-utanjs.txt')
    kedja_ok = rc == 0 and (katalog / 'utanjs' / 'UTAN-JS.json').is_file()
    dom(kedja_ok, 'utan-js genom tjänsten mot en lokal sida (sandlåda → tjänst → Chromium → localhost): %s' % ('gick' if kedja_ok else 'gick inte (rc %s: %s)' % (rc, sista(fel))))
    res, rc, fel = las(katalog, '11-tjanst-nekad.txt')
    nekad_ok = rc == 2 and 'domänlista' in (fel or '')
    dom(nekad_ok, 'inspektera av olistad domän genom tjänsten: %s' % ('vägrad' if nekad_ok else 'inte vägrad (rc %s: %s)' % (rc, sista(fel))))
    res, rc, fel = las(katalog, '12-tjanst-inskick.txt')
    inskick_ok = rc == 2 and 'lokala mottagare' in (fel or '')
    dom(inskick_ok, 'inskick mot extern adress genom tjänsten: %s' % ('vägrat' if inskick_ok else 'inte vägrat (rc %s: %s)' % (rc, sista(fel))))
    return sum(1 for ok, _ in rader if not ok), rader


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        print('användning: sandlada_dom.py <resultatkatalog> <claude-kod> <provrot>', file=sys.stderr)
        return 2
    fel, rader = doma(argv[0], argv[1], argv[2])
    for ok, text in rader:
        print('  %s  %s' % ('OK ' if ok else 'FEL', text))
    print('utfall: %d fel' % fel)
    return 1 if fel else 0


if __name__ == '__main__':
    sys.exit(main())
