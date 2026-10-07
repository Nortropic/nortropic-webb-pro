#!/usr/bin/env python3
"""prov_slutpost.py — slutbeskedet och rapporternas giltighet (ägarens uppdrag 2026-10-07, punkt 4, 5, 8 och 10):

- stoppvakten: en gammal rapport till ett nytt bygge (en annan körnings identitet, eller utan identitet och skriven före
  körningens start) släpper inte avslutet; en rapport med körningens identitet, eller skriven efter starten, binds med
  sha256 och körning;
- korslut: samma gamla rapport nekas ("gäller körning X" eller "saknar identitet"), liksom en rapport som ändrats efter
  stoppvaktens besked; den bundna godkänns;
- en historisk granskning (ett annat bygge) godkänner inte det slutliga bygget: varken korsluts besked, slutposten eller
  A/B-armens post säger godkänd;
- beständiga slutbesked: kor.sh direkt (en start som stannar före bygget och ett helt bygge med en falsk claude),
  demons väg (dashboardens starta_demo) och ab.py starta skriver slutposten, och terminalens besked är postens text; en
  äldre RAPPORT.md flyttas när bygget startar och ingenting raderas; ett bygge som ändrar en tidigare slutpost får
  slutkod 3;
- de fem tillstånden hålls isär, också när ägarens dom kommer efter körningen (korslut.aktuell);
- kalibreringen: mallen skriver nivåfilens sha och läckageprovet och kallar exemplen undanhållna bara när provet gått
  igenom; en äldre rapport rättas med ett daterat block överst och giltigheten i RAPPORT.json, och ursprungsresultatet
  står kvar.

    .venv/bin/python kontroller/rokprov/revision/prov_slutpost.py <repo>

Allt skrivs i en temporär katalog (nwp-slutpost-*); repots filer läses men ändras inte, och inga privata data läses.
Varje fall redovisas för sig på stderr; slutkod 1 när något fall föll.
"""
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import types
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
PY = str(ROOT / '.venv' / 'bin' / 'python')
TMP = Path(tempfile.mkdtemp(prefix='nwp-slutpost-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit

    def stada():
        subprocess.run(['chflags', '-R', 'nouchg', str(TMP)], capture_output=True)  # kor.sh låser kopians kunder/ och underlag/
        shutil.rmtree(TMP, True)
    atexit.register(stada)
sys.path.insert(0, str(ROOT / 'kontroller'))
import granska  # noqa: E402
import korslut  # noqa: E402
import prova  # noqa: E402

FEL = []


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:1500]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


def skriv(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (dict, list)):
        data = json.dumps(data, ensure_ascii=False)
    p.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
    return p


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stampel(sekunder_sedan=0):
    return (datetime.now(timezone.utc) - timedelta(seconds=sekunder_sedan)).strftime('%Y%m%dT%H%M%SZ')


def rapport(korning=None):
    """En rapport längre än 300 byte, med körningens identitet i huvudet när korning anges."""
    huvud = '---\nid: RAPPORT-prov\nkorning: %s\n---\n' % korning if korning else ''
    return huvud + '# Rapport\n\n' + 'Byggets rapport, skriven för ägaren. ' * 12


def ladda_stoppvakt():
    spec = importlib.util.spec_from_file_location('stoppvakt_slutpost', str(ROOT / '.claude' / 'hooks' / 'stoppvakt.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SV = ladda_stoppvakt()


def stoppvakt(slug, korning):
    """Stoppvakten i provets egen rot, med provet grönt (prova.py ersatt) och granskningen avstängd: utfallet beror bara på
    rapporten. Ger (slutkod, STOPPVAKT.json, stderr)."""
    rot = TMP / 'sv-rot'
    kund = rot / 'kunder' / slug
    skriv(kund / 'prov' / 'STATUS.json', {'ok': True, 'dist_sha256': 'd' * 64})
    (kund / 'prov' / '.stoppvakt-antal').unlink(missing_ok=True)  # varje försök är det första: taket släpper aldrig här
    gammal = {k: os.environ.get(k) for k in ('NWP_SLUG', 'NWP_KORNING', 'NWP_GRANSKNING', 'NWP_SANDLADA', 'NWP_ATELJE')}
    sp, rt, sin = SV.subprocess, SV.ROOT, sys.stdin
    SV.subprocess = types.SimpleNamespace(run=lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='grönt', stderr=''),
                                          TimeoutExpired=subprocess.TimeoutExpired)
    SV.ROOT, sys.stdin = rot, io.StringIO('{}')
    os.environ.update(NWP_SLUG=slug, NWP_KORNING=korning, NWP_GRANSKNING='av')
    os.environ.pop('NWP_SANDLADA', None)
    os.environ.pop('NWP_ATELJE', None)
    fel = io.StringIO()
    try:
        with redirect_stderr(fel):
            rc = SV.main()
    finally:
        SV.subprocess, SV.ROOT, sys.stdin = sp, rt, sin
        for k, v in gammal.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    return rc, json.loads((kund / 'prov' / 'STOPPVAKT.json').read_text()), fel.getvalue()


# ===== punkt 5: rapporten bunden till körningen =====

@fall('stoppvakten: en gammal rapport till ett nytt bygge släpper inte avslutet')
def _stoppvakt_gammal():
    ny, gammal_k = stampel(60), '20261001T080000Z'
    rap = skriv(TMP / 'sv-rot' / 'kunder' / 'sv-gammal' / 'RAPPORT.md', rapport(gammal_k))
    rc, post, fel = stoppvakt('sv-gammal', ny)
    assert rc == 2 and post['slapp'] is False, ('en rapport med en annan körnings identitet släppte avslutet', rc, post)
    assert 'gäller körning %s' % gammal_k in post.get('rapport', '') and not post.get('rapport_sha256'), post
    assert 'RAPPORT.md' in fel and 'korning: %s' % ny in fel, ('beskedet till sessionen säger vad som saknas', fel[-400:])
    # utan identitet och skriven före körningens start: lika gammal
    skriv(rap, rapport())
    fore = time.time() - 3600
    os.utime(rap, (fore, fore))
    rc, post, _ = stoppvakt('sv-gammal', ny)
    assert rc == 2 and post['slapp'] is False and 'saknar identitet' in post.get('rapport', '') and 'före körningens start' in post['rapport'], post


@fall('stoppvakten: en rapport skriven i körningen binds med sha256 och körning')
def _stoppvakt_bunden():
    ny = stampel(60)
    rap = skriv(TMP / 'sv-rot' / 'kunder' / 'sv-bunden' / 'RAPPORT.md', rapport(ny))
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 0 and post['slapp'] is True and post['rapport_sha256'] == sha(rap) and post['rapport_korning'] == ny, post
    assert post['rapport_bunden'] == 'identitet' and str(post['skal']).startswith('kontrollerna gröna'), post
    skriv(rap, rapport())  # utan identitet men skriven nu, efter körningens start
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 0 and post['rapport_bunden'] == 'filtid' and post['rapport_sha256'] == sha(rap), post


def bygge(slug, korning, rapport_korning=None, bunden=True, stopp_skal='kontrollerna gröna, RAPPORT.md skriven i körningen och granskningen är godkänd',
          granskning='runda'):
    """Ett bygge som kor.sh och stoppvakten lämnar det, i provets kunder/: dist, provet grönt, stoppvaktens besked,
    rapporten och en granskning för bygget med dagens metod (runda) eller bara en rotfil för ett äldre bygge (rotfil)."""
    k = TMP / 'kunder' / slug
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>%s %s</p>' % (slug, korning))
    h = prova.dist_hash(k / 'sajt' / 'dist')
    rap = skriv(k / 'RAPPORT.md', rapport(rapport_korning or korning))
    skriv(k / 'prov' / 'STATUS.json', {'ok': True, 'tid': '2026-10-07T08:00:00Z', 'dist_sha256': h, 'grindar': {'bygge': {'ok': True}}})
    sv = {'slapp': True, 'skal': stopp_skal, 'forsok': 1, 'tak': 8, 'korning': korning, 'dist_sha256': h, 'kontroller_grona': True,
          'granskning': 'godkänd'}
    if bunden:
        sv.update(rapport_sha256=sha(rap), rapport_korning=korning, rapport_bunden='identitet', rapport_finns=True)
    skriv(k / 'prov' / 'STOPPVAKT.json', sv)
    metod = granska.aktuell_metod(slug)
    if granskning == 'runda':
        g = dict(metod, godkand=True, runda=1, dist_sha256=h, korning=korning, tid='2026-10-07T08:30:00Z', kriterier={'designkvalitet': {'betyg': 8}})
        skriv(k / 'granskning' / 'runda-01' / 'GRANSKNING.json', g)
        skriv(k / 'granskning' / 'runda-01' / 'UTFALL.json', {'status': 'klar', 'tid': g['tid'], 'skal': ''})
        skriv(k / 'granskning' / 'GRANSKNING.json', g)
    elif granskning == 'rotfil':  # en äldre godkänd granskning av ett annat bygge, utan omgångar
        skriv(k / 'granskning' / 'GRANSKNING.json', dict(metod, godkand=True, runda=1, dist_sha256='e' * 64, korning='20261001T080000Z',
                                                          kriterier={'designkvalitet': {'betyg': 9}}))
    skriv(TMP / 'skyddat.txt', 'aaa  kontroller/prova.py\n')
    return k, h


def korslut_(k, korning, rc='0'):
    p = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'korslut.py'), str(k), rc, str(TMP / 'skyddat.txt'), str(TMP / 'skyddat.txt'), korning],
                       capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout, p.stderr


def slutpost(k, korning):
    f = Path(k) / 'korningar' / korning / 'SLUT.json'
    assert f.is_file(), 'ingen slutpost %s' % f.relative_to(TMP)
    return json.loads(f.read_text(encoding='utf-8'))


@fall('korslut: en gammal rapport till ett nytt bygge nekas och sägs som sådan')
def _korslut_gammal():
    ny = stampel(120)
    k, _ = bygge('ks-gammal', ny, rapport_korning='20261001T080000Z', bunden=False)
    rc, ut, fel = korslut_(k, ny)
    assert rc == 1 and 'gäller körning 20261001T080000Z' in ut, ('en rapport från en annan körning godkändes', rc, ut[-800:], fel[-300:])
    skriv(k / 'RAPPORT.md', rapport())  # utan identitet, och stoppvakten band ingen
    rc, ut, _ = korslut_(k, ny)
    assert rc == 1 and 'saknar identitet' in ut, (rc, ut[-600:])


@fall('korslut: en rapport som ändrats efter stoppvaktens besked nekas; den bundna godkänns')
def _korslut_bunden():
    ny = stampel(120)
    k, _ = bygge('ks-bunden', ny)
    rc, ut, fel = korslut_(k, ny)
    assert rc == 0, ('den bundna rapporten godkändes inte', rc, ut[-800:], fel[-300:])
    skriv(k / 'RAPPORT.md', rapport(ny) + '\nTillagt efter stoppvaktens besked.\n')
    rc, ut, _ = korslut_(k, ny)
    assert rc == 1 and 'inte den rapport som stoppvakten släppte' in ut, (rc, ut[-600:])


# ===== punkt 5 och 4: en historisk granskning gäller inte det aktuella bygget =====

@fall('korslut: en historisk godkänd granskning är historik i beskedet och i slutposten')
def _korslut_historisk():
    ny = stampel(120)
    k, h = bygge('ks-historisk', ny, stopp_skal='släppt utan godkänd granskning: taket för granskningar i körningen är nått och ingen giltig '
                                                'granskning gäller det slutliga bygget', granskning='rotfil')
    rc, ut, fel = korslut_(k, ny)
    fore = ut.split('Rapport:')[0]
    assert rc == 1 and 'GODKÄND' not in fore, ('en granskning av ett annat bygge visas som godkänd för det slutliga', rc, fore[-600:], fel[-300:])
    assert 'Senaste dom oavsett bygge och metod: godkänd' in ut and '≠ slutliga bygget' in ut, ut[-800:]
    post = slutpost(k, ny)
    dg = post['tillstand']['designgranskaren_godkanner']
    assert dg['varde'] is None and 'historik' in dg.get('historisk', '') and post['designgranskning']['historisk']['samma_bygge'] is False, dg
    assert not post['bedomningsutfall'].startswith('godkänt') and post['tillstand']['klart_for_leverans']['varde'] is False, post['bedomningsutfall']
    # en godkänd omgång i en tidigare körning är också historik, inte en dom över körningens bygge
    k2, h2 = bygge('ks-historisk2', ny, granskning=None)
    g = dict(granska.aktuell_metod('ks-historisk2'), godkand=True, runda=1, dist_sha256='f' * 64, korning='20261001T080000Z', tid='2026-10-01T09:00:00Z')
    skriv(k2 / 'granskning' / 'runda-01' / 'GRANSKNING.json', g)
    skriv(k2 / 'granskning' / 'runda-01' / 'UTFALL.json', {'status': 'klar', 'tid': g['tid'], 'skal': ''})
    rc, ut, _ = korslut_(k2, ny)
    post = slutpost(k2, ny)
    assert rc == 1 and post['tillstand']['designgranskaren_godkanner']['varde'] is None and post['designgranskning']['historisk']['korning'] == '20261001T080000Z', (rc, post['designgranskning'])


@fall('ab: armens post bär slutpostens dom, inte en historisk rotfil')
def _ab_historisk():
    ny = stampel(120)
    k, h = bygge('ab-hist-abx', ny, granskning='rotfil')
    korslut_(k, ny)
    spec = importlib.util.spec_from_file_location('ab_slutpost', str(ROOT / 'kontroller' / 'ab.py'))
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    ab.KUNDER = TMP / 'kunder'
    m = ab.matt('ab-hist-abx')
    assert m.get('granskning_godkand') is not True, ('armen räknas som godkänd av en granskning som gällde ett annat bygge', m.get('granskning_godkand'))
    assert m.get('slutpost') == 'kunder/ab-hist-abx/korningar/%s/SLUT.json' % ny and m.get('slutkod') == 1, m
    assert m.get('dist_sha256') == h and m.get('slutpost_dist_sha256') == h, m


# ===== punkt 4: de fem tillstånden =====

@fall('slutposten: fem tillstånd var för sig, och ägarens dom efter körningen prövas utan att posten skrivs om')
def _tillstanden():
    ny = stampel(120)
    k, h = bygge('ks-tillstand', ny)
    rc, ut, _ = korslut_(k, ny)
    post = slutpost(k, ny)
    t = post['tillstand']
    assert rc == 0 and [t[n]['varde'] for n in ('sessionen_avslutad', 'tekniskt_godkant', 'designgranskaren_godkanner', 'agaren_godkanner',
                                               'klart_for_leverans')] == [True, True, True, None, False], {n: x.get('varde') for n, x in t.items()}
    for falt in ('id', 'titel', 'typ', 'uppdrag', 'kund', 'moment', 'forfattare', 'datum', 'granskad_identitet', 'rapportstatus',
                 'bedomningsutfall', 'foregaende', 'ersatt_av', 'underlag', 'beslut', 'atgarder'):
        assert post.get(falt) not in (None, '', []), ('rapporthuvudets fält saknas', falt)
    ident = ' '.join(post['granskad_identitet'])
    assert ('körning %s' % ny) in ident and h in ident and post['metod']['granskning']['metod_sha'] in ident and 'granskningsomgång 1' in ident, ident
    assert post['bedomningsutfall'].startswith('godkänt') and post['rapportstatus'] == 'färdig' and 'leverans' not in post['bedomningsutfall'], post['bedomningsutfall']
    fore = sha(k / 'korningar' / ny / 'SLUT.json')
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T10:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, efter små ändringar'}}]})
    a = korslut.aktuell(k)
    assert a['tillstand']['agaren_godkanner']['varde'] is False and a['tillstand']['klart_for_leverans']['varde'] is False, a['tillstand']['agaren_godkanner']
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T11:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    a = korslut.aktuell(k)
    assert a['tillstand']['agaren_godkanner']['varde'] is True and a['tillstand']['klart_for_leverans']['varde'] is True, a['tillstand']['klart_for_leverans']
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>ombyggt efter körningen</p>')
    a = korslut.aktuell(k)
    assert a['tillstand']['klart_for_leverans']['varde'] is False and a['provad']['samma_bygge'] is False, a['provad']
    assert sha(k / 'korningar' / ny / 'SLUT.json') == fore, 'aktuell() skrev om slutposten'


# ===== punkt 4 och 10: beständiga slutbesked genom de verkliga startvägarna =====

KR = TMP / 'kor-repo'
FALSK = TMP / 'falsk-claude'


def kor_repo():
    """En repokopia med mekaniken (kor.sh, kontroller, krokarna, kritik, kunskap, dashboarden), länkad körmiljö, git och
    en falsk claude som svarar som en session utan att bygga något."""
    if KR.is_dir():
        return
    KR.mkdir()
    for namn in ('kor.sh', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', '.gitignore', 'dashboard.sh'):
        if (ROOT / namn).is_file():
            shutil.copy2(ROOT / namn, KR / namn)
    for mapp in ('kontroller', 'kritik', 'kunskap', 'dashboard'):
        shutil.copytree(ROOT / mapp, KR / mapp, ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'rokprov'), symlinks=True)
    shutil.copytree(ROOT / '.claude' / 'hooks', KR / '.claude' / 'hooks', ignore=shutil.ignore_patterns('__pycache__'))
    for f in (ROOT / '.claude').glob('settings*.json'):
        shutil.copy2(f, KR / '.claude' / f.name)
    (KR / 'backlog').mkdir()
    os.symlink(ROOT / '.venv', KR / '.venv')
    os.symlink(ROOT / 'kontroller' / 'node_modules', KR / 'kontroller' / 'node_modules')
    git = lambda *a: subprocess.run(['git', '-C', str(KR), *a], capture_output=True, text=True)  # noqa: E731
    git('init', '-q')
    git('add', '-A')
    git('-c', 'user.name=prov', '-c', 'user.email=prov@example.invalid', 'commit', '-q', '-m', 'bas')
    git('branch', '-M', 'main')
    FALSK.mkdir()
    skriv(FALSK / 'claude', '#!/bin/sh\ncat > /dev/null\n'
                            'if [ -n "$PROV_ANDRA_PROTOKOLL" ]; then for f in kunder/"$NWP_SLUG"/korningar/*/SLUT.json; do echo " " >> "$f"; done; fi\n'
                            'echo \'{"type":"result","subtype":"success","num_turns":3,"duration_ms":1000}\'\nexit 0\n')
    (FALSK / 'claude').chmod(0o755)


def miljo(**extra):
    m = {k: v for k, v in os.environ.items() if not k.startswith(('CLAUDE_CODE_', 'NWP_')) and k != 'CLAUDECODE'}
    m.update(PATH=str(FALSK) + os.pathsep + m.get('PATH', ''), NWP_STARTKONTROLL='av', NWP_SANDLADA='av', NWP_KORREGISTER=str(TMP / 'korregister'))
    m.update(extra)
    return m


def kor(slug, **extra):
    p = subprocess.run(['bash', str(KR / 'kor.sh'), slug, 'Prov AB, Umeå, https://exempel.se'], capture_output=True, text=True, cwd=str(KR),
                       env=miljo(**extra), timeout=600)
    return p.returncode, p.stdout, p.stderr


def korningar(slug):
    d = KR / 'kunder' / slug / 'korningar'
    return sorted(x.name for x in d.iterdir()) if d.is_dir() else []


@fall('kor.sh direkt: en start som stannar före bygget ger en kort slutpost och lämnar den äldre rapporten')
def _kor_stopp():
    kor_repo()
    gammal = skriv(KR / 'kunder' / 'direkt-prov' / 'RAPPORT.md', rapport('20261001T080000Z'))
    innehall = gammal.read_bytes()
    rc, ut, fel = kor('direkt-prov')
    k_ = korningar('direkt-prov')
    assert rc == 2 and 'ingen godkänd startsida' in ut and len(k_) == 1, ('ingen slutpost för stoppet', rc, k_, ut[-400:], fel[-400:])
    post = slutpost(KR / 'kunder' / 'direkt-prov', k_[0])
    assert post['slutkod'] == 2 and 'ingen godkänd startsida' in post['skal'] and post['tillstand']['sessionen_avslutad']['varde'] is None, post
    assert korslut.text(post) in ut, ('terminalens besked är inte postens text', ut[-600:])
    assert gammal.read_bytes() == innehall and not (KR / 'kunder' / 'direkt-prov' / 'rapporter').exists(), 'en start som stannade flyttade rapporten'


@fall('kor.sh direkt: ett helt bygge skriver slutposten, beskedet ur den, och flyttar den äldre rapporten utan att radera')
def _kor_helt():
    kor_repo()
    k = KR / 'kunder' / 'direkt-prov'
    if not (k / 'RAPPORT.md').is_file():
        skriv(k / 'RAPPORT.md', rapport('20261001T080000Z'))
    innehall = (k / 'RAPPORT.md').read_bytes()
    fore = korningar('direkt-prov')
    rc, ut, fel = kor('direkt-prov', NWP_ATELJE='av')
    m = re.search(r'Körning direkt-prov startad (\d{8}T\d{6}Z)', ut)
    assert rc == 1 and m, ('kor.sh startade inte bygget', rc, ut[-500:], fel[-500:])
    nya = [x for x in korningar('direkt-prov') if x not in fore]
    assert nya == [m.group(1)], ('slutposten hör inte till körningen', nya, m.group(1))
    post = slutpost(k, m.group(1))
    assert post['slutkod'] == rc and post['korning'] == m.group(1) and post['tillstand']['sessionen_avslutad']['varde'] is True, post['tillstand']
    assert post['tillstand']['tekniskt_godkant']['varde'] is False and post['tillstand']['klart_for_leverans']['varde'] is False, post['tillstand']
    assert korslut.text(post) in ut, ('terminalens besked är inte postens text', ut[-800:])
    flyttad = k / 'rapporter' / ('RAPPORT-fore-%s.md' % m.group(1))
    assert flyttad.is_file() and flyttad.read_bytes() == innehall and not (k / 'RAPPORT.md').exists(), 'den äldre rapporten flyttades inte orörd'
    if fore:  # stoppets post är ersatt av byggets, och i övrigt orörd
        aldre = slutpost(k, fore[-1])
        assert aldre['rapportstatus'] == 'ersatt' and post['id'] in aldre['ersatt_av'] and aldre['slutkod'] == 2, aldre
        assert post['foregaende'].startswith(aldre['id']), post['foregaende']


@fall('kor.sh direkt: ett bygge som ändrar en tidigare slutpost får slutkod 3')
def _kor_protokoll():
    kor_repo()
    k = KR / 'kunder' / 'protokoll-prov'
    rc, ut, _ = kor('protokoll-prov', NWP_ATELJE='av')
    assert rc == 1 and len(korningar('protokoll-prov')) == 1, (rc, ut[-300:])
    rc, ut, fel = kor('protokoll-prov', NWP_ATELJE='av', PROV_ANDRA_PROTOKOLL='1')
    assert rc == 3 and 'kunder/protokoll-prov/korningar/' in ut, ('ändrade slutposter godtogs', rc, ut[-600:], fel[-300:])
    post = slutpost(k, korningar('protokoll-prov')[-1])
    assert post['slutkod'] == 3 and post['kontroller']['mekaniken']['varde'] is False, post['kontroller']['mekaniken']


@fall('demons väg (dashboardens starta_demo): kor.sh skriver slutposten och loggen bär postens text')
def _demo():
    kor_repo()
    skriv(KR / 'underlag' / 'prospekt' / 'prov-demo' / 'REGISTER.json',
          [{'slug': 'demo-prov', 'status': 'vald', 'namn': 'Demo AB', 'postort': 'Umeå', 'bransch': 'hantverkare', 'sajt': {'url': 'https://exempel.se'}}])
    kod = ('import sys, json; sys.path.insert(0, %r); import prospektvy as pv; print(json.dumps(pv.starta_demo("prov-demo", "demo-prov")))'
           % str(KR / 'dashboard'))
    p = subprocess.run([PY, '-B', '-c', kod], capture_output=True, text=True, cwd=str(KR), env=miljo(), timeout=120)
    assert p.returncode == 0, ('starta_demo föll', p.stdout[-300:], p.stderr[-600:])
    logg = KR / json.loads(p.stdout.strip().splitlines()[-1])['logg']
    slut = time.time() + 180
    while time.time() < slut:  # demon startar kor.sh frikopplad; vänta tills den skrivit sitt besked och släppt låset
        if logg.is_file() and logg.stat().st_size and not (KR / 'kunder' / '.bygge-pid').exists():
            break
        time.sleep(0.3)
    time.sleep(0.5)
    text = logg.read_text(encoding='utf-8', errors='replace')
    k_ = korningar('demo-prov')
    assert 'ingen godkänd startsida' in text and len(k_) == 1, ('demons körning saknar slutpost', k_, text[-400:])
    post = slutpost(KR / 'kunder' / 'demo-prov', k_[0])
    assert post['slutkod'] == 2 and korslut.text(post) in text, ('loggen bär inte postens text', text[-500:])


@fall('ab.py starta: varje arm pekar på sin slutpost, med samma slutkod som kor.sh')
def _ab_starta():
    kor_repo()
    p = subprocess.run([PY, '-B', str(KR / 'kontroller' / 'ab.py'), 'starta', 'abprov', 'Prov AB, Umeå, https://exempel.se', '--variabel', 'atelje',
                        '--a', 'av', '--b', 'pa'], capture_output=True, text=True, cwd=str(KR), env=miljo(), timeout=900)
    assert p.returncode == 0, ('ab.py starta föll', p.stdout[-500:], p.stderr[-500:])
    poster = sorted((KR / 'kunder' / 'ab').glob('ab-abprov-*.json'))
    assert len(poster) == 1, poster
    ab = json.loads(poster[0].read_text())
    rcs = set()
    for arm in ab['byggen']:
        x = ab['korningar'][arm]
        assert x.get('slutpost'), ('armen pekar inte på någon slutpost', arm, x)
        post = json.loads((KR / x['slutpost']).read_text())
        assert post['slutkod'] == x['rc'] == x['slutkod'] and post['korning'] == x['korning'], (arm, x, post['slutkod'])
        assert x['granskning_godkand'] is post['tillstand']['designgranskaren_godkanner']['varde'], (arm, x)
        rcs.add(x['rc'])
    assert rcs == {1, 2}, ('en arm byggde (nödvägen), den andra stannade före bygget', rcs)


# ===== punkt 8: kalibreringens slutsats =====

def ladda_kalibrering():
    spec = importlib.util.spec_from_file_location('kalibrering_slutpost', str(ROOT / 'kontroller' / 'granskarforsok' / 'kalibrering.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RADER = [{'id': 'K02', 'agaren': 'nastan', 'granskaren': 'underkänd', 'niva': 1, 'betyg': {'designkvalitet': 6}, 'blockerande': 5, 'utfall': 'rätt'}]
SUMMA = {'undanhallna': 1, 'svar': 1, 'ofullstandiga': 0, 'falska_godkannanden': 0, 'av_ej_over': 1, 'falska_underkannanden': 0, 'av_over': 0}
DOM = 'Rubrikerna står i samma storlek överallt och bilderna är beskurna utan tanke på vad de visar.'


@fall('kalibreringen: mallen skriver nivåfilens sha och läckageprovet, och undanhållna bara när provet gått igenom')
def _kalibrering_mall():
    kf = ladda_kalibrering()
    # mallen anropad som försöket alltid anropat den, utan läckageprov: exemplen får inte kallas undanhållna
    mal = TMP / 'kal' / 'utan-prov'
    mal.mkdir(parents=True)
    md = kf.rapport(RADER, dict(SUMMA), mal, 'm', 'e').read_text()
    assert 'ndanhållna' not in md.split('**Giltighet')[0] and 'utvecklingsdata' in md and 'Läckageprovet: inte gjort' in md, md[:500]
    exempel = [{'id': 'K02', 'niva': 'nastan', 'skiljer': DOM}]
    lackt = kf.lackageprov(exempel, {'kunskap/visuell-niva.md': '# Nivå\n\n- ' + DOM.lower() + '\n'})
    assert lackt['ok'] is False and lackt['traffar'] and lackt['traffar'][0]['id'] == 'K02', lackt
    assert kf.lackageprov(exempel, {'kritik/GRANSKARE.md': 'Se K02 i underlaget.'})['ok'] is False, 'exemplets id i metoden är läckage'
    rent = kf.lackageprov(exempel, {'kunskap/visuell-niva.md': '# Nivå\n\nEn helt annan text om typografi och rytm.\n'})
    assert rent['ok'] is True and rent['begransning'], rent
    for namn, lp in (('lackt', lackt), ('utan', None)):
        mal = TMP / 'kal' / namn
        mal.mkdir(parents=True)
        md = kf.rapport(RADER, dict(SUMMA), mal, 'm', 'e', lackage=lp, nivafil={'fil': 'kunskap/visuell-niva.md', 'sha256': 'ab' * 32}).read_text()
        js = json.loads((mal / 'RAPPORT.json').read_text())
        assert 'ndanhållna' not in md.split('**Giltighet')[0] and 'Prövade exempel: 1' in md, (namn, md[:400])
        assert js['giltighet'] == 'utvecklingsdata' and 'undanhallna' not in js['sammanfattning'] and js['sammanfattning']['provade'] == 1, (namn, js)
        assert ('ab' * 32) in md and js['nivafil']['sha256'] == 'ab' * 32 and 'Läckageprovet' in md, (namn, md[:600])
    mal = TMP / 'kal' / 'rent'
    mal.mkdir(parents=True)
    md = kf.rapport(RADER, dict(SUMMA), mal, 'm', 'e', lackage=rent, nivafil={'fil': 'kunskap/visuell-niva.md', 'sha256': 'cd' * 32}).read_text()
    js = json.loads((mal / 'RAPPORT.json').read_text())
    assert 'Undanhållna exempel: 1' in md and js['giltighet'].startswith('undanhållna') and js['sammanfattning']['undanhallna'] == 1, (md[:500], js)


def huvud(text):
    """Rapporthuvudet som README.md beskriver det (nyckel: värde mellan ---), tolkat strikt nog för provet."""
    rader = text.split('\n')
    assert rader[0] == '---', 'rapporten börjar inte med ett huvud'
    falt = {}
    for r in rader[1:]:
        if r == '---':
            return falt
        m = re.match(r'^([A-Za-z_][\w-]*):(?:[ \t]+(.*?))?[ \t]*$', r)
        if m:
            falt[m.group(1)] = m.group(2) or ''
    raise AssertionError('huvudet slutar aldrig')


@fall('kalibreringen: en korrigerad slutsats syns från den äldre rapporten, och ursprungsresultatet står kvar')
def _kalibrering_rattelse():
    kf = ladda_kalibrering()
    mal = TMP / 'kal' / 'FORSOK-PROV'
    mal.mkdir(parents=True)
    # den äldre rapporten i den äldre mallens form, syntetisk (aldrig den privata)
    aldre = ('# Kalibreringsförsöket 2026-10-04T13:52:30Z · opus[1m] high\n\nUndanhållna exempel: 1, svar: 1. Falska godkännanden: 0 av 1 '
             '(ägaren: nästan eller generisk). Falska underkännanden: 0 av 0 (ägaren: tydligt över ribban).\n\n| id | ägaren | granskaren | nivå | '
             'betyg | blockerande | utfall |\n|---|---|---|---|---|---|---|\n| K02 | nästan | underkänd | 1 | 6 | 5 | rätt |\n')
    skriv(mal / 'RAPPORT.md', aldre)
    js0 = {'tid': '2026-10-04T13:52:30Z', 'modell': 'opus[1m]', 'effort': 'high', 'rader': RADER, 'sammanfattning': SUMMA}
    skriv(mal / 'RAPPORT.json', json.dumps(js0, ensure_ascii=False, indent=1) + '\n')
    fore = {'RAPPORT.md': sha(mal / 'RAPPORT.md'), 'RAPPORT.json': sha(mal / 'RAPPORT.json')}
    skal = 'Exemplen var inte undanhållna från det granskaren läste (testläckage).'
    ut = kf.ratta(mal, '2026-10-07', 'utvecklingsdata', skal, ['LARDOMAR.md rad 190–205', 'backlogposten om kalibreringen'],
                  uppdrag='kalibrering av visuell nivå', atgarder=['ett nytt, orört urval'])
    md = (mal / 'RAPPORT.md').read_text(encoding='utf-8')
    f = huvud(md)
    assert md.endswith(aldre), 'ursprungsrapporten står inte kvar byte för byte under rättelsen'
    assert f['rapportstatus'].startswith('färdig') and '2026-10-07' in f['rapportstatus'] and f['bedomningsutfall'].startswith('ofullständigt'), f
    assert f['giltighet'] == 'utvecklingsdata' and f['id'] == 'KAL-FORSOK-PROV' and 'K02' in f['granskad_identitet'], f
    forsta = md.split(aldre)[0]
    assert '**Rättelse 2026-10-07: utvecklingsdata, inte ett oberoende mått.**' in forsta and skal in forsta and 'LARDOMAR.md rad 190–205' in forsta, forsta[-600:]
    js = json.loads((mal / 'RAPPORT.json').read_text())
    assert js['giltighet'] == 'utvecklingsdata' and js['giltighet_skal'] == skal and js['rattelse']['sha256_fore'] == fore, js
    assert {k: js[k] for k in js0} == js0, 'siffrorna och raderna ändrades'
    assert ut == {'RAPPORT.md': (fore['RAPPORT.md'], sha(mal / 'RAPPORT.md')), 'RAPPORT.json': (fore['RAPPORT.json'], sha(mal / 'RAPPORT.json'))}, ut
    efter = {n: sha(mal / n) for n in fore}
    ut2 = kf.ratta(mal, '2026-10-07', 'utvecklingsdata', skal, ['LARDOMAR.md rad 190–205'])
    assert {n: sha(mal / n) for n in fore} == efter and ut2 == {n: (efter[n], efter[n]) for n in efter}, 'samma rättelse en gång till ändrade rapporten'


print('slutbeskedets prov: %d fall föll%s' % (len(FEL), (': ' + '; '.join(FEL)) if FEL else ''), file=sys.stderr)
sys.exit(1 if FEL else 0)
