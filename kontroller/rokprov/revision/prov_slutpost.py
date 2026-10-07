#!/usr/bin/env python3
"""prov_slutpost.py — slutbeskedet och rapporternas giltighet (ägarens uppdrag 2026-10-07, punkt 4, 5, 8 och 10;
granskningen av r101, GR-20261007-r101):

- stoppvakten: en gammal rapport till ett nytt bygge släpper inte avslutet, och inte heller en rapport utan körningens
  identitet (också en som kopierats tillbaka med ny filtid), en symlänk eller en nästan tom rapport; en rapport med
  identiteten binds med sha256 och körning; den förkastade ateljéns väg kräver också en bunden rapport;
- korslut: en gammal rapport nekas ("gäller körning X" eller "saknar identitet"), liksom en rapport som ändrats efter
  stoppvaktens besked och ett besked som band rapporten till en annan körning; beskedet säger om felet är stoppvaktens
  eller rapportens, och ett besked från före 2026-10-07 sägs som sådant;
- en historisk granskning (ett annat bygge, en annan metod, en tidigare körning) godkänner inte det slutliga bygget,
  varken i korsluts besked, i slutposten eller i A/B-armens post;
- de fem tillstånden hålls isär, och varje tillstånd prövas mot det det bygger på: slutkoden, claudes kod, rapportens
  bindning, stoppvaktens egna kontroller (inte om den släppte), granskningens metod och ägarens dom över just bygget;
- ägarens dom (B1): en DOM.json som ändrades under körningen, eller som inte går att pröva mot starten, räknas aldrig;
  kor.sh låser en befintlig DOM.json och ger slutkod 3 när bygget skriver en;
- --visa (B2): en ändrad metod, en annan godkänd startsida eller en ändrad dist gör postens godkännanden till historik;
- --visa utan körning visar posten för bygget i dist/, inte en stopppost, och en senare körning som föll utan att ändra
  bygget ersätter inte den godkända posten;
- slutposten som uteblir: en katalog där posten ska ligga ger slutkod 5 (eller 3 när bygget skapade den), och trasiga
  äldre filer (SLUT.json, DOM.json) fäller inte avslutet;
- beständiga slutbesked genom de verkliga startvägarna: kor.sh direkt (stopp, helt bygge, startkontrollens stopp,
  namnkrock i rapporter/, SIGTERM och SIGKILL), demons väg och ab.py starta; terminalens rader prövas mot förväntade
  rader, inte bara mot postens egen text;
- den äldre postens länk pekar på den flyttade rapporten;
- kalibreringen: läckageprovet går inte igenom utan texter eller utan nivåfilen, och inte när ett exempel inte kunde
  prövas; huvudvägen prövar mot det granskaren läste; en äldre rapport rättas med ett daterat block överst.

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
import signal
import subprocess
import sys
import tempfile
import time
import traceback
import types
from contextlib import redirect_stderr
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


def rad(text, borjan):
    """Den första raden i terminalens text som börjar med borjan (utan inledande blanksteg), eller ''."""
    return next((r.strip() for r in text.split('\n') if r.strip().startswith(borjan)), '')


def ladda(namn, fil):
    spec = importlib.util.spec_from_file_location(namn, str(fil))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SV = ladda('stoppvakt_slutpost', ROOT / '.claude' / 'hooks' / 'stoppvakt.py')


def stoppvakt(slug, korning, atelje=None):
    """Stoppvakten i provets egen rot, med provet grönt (prova.py ersatt) och granskningen avstängd: utfallet beror bara på
    rapporten. atelje: STATUS.json och VAL.json för en förkastad ateljé. Ger (slutkod, STOPPVAKT.json, stderr)."""
    rot = TMP / 'sv-rot'
    kund = rot / 'kunder' / slug
    skriv(kund / 'prov' / 'STATUS.json', {'ok': True, 'dist_sha256': 'd' * 64})
    (kund / 'prov' / '.stoppvakt-antal').unlink(missing_ok=True)  # varje försök är det första: taket släpper aldrig här
    if atelje:
        for namn, data in atelje.items():
            skriv(rot / 'underlag' / slug / 'atelje' / namn, data)
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
    skriv(rap, rapport())  # utan identitet, som ett gammalt bygges rapport
    fore = time.time() - 3600
    os.utime(rap, (fore, fore))
    rc, post, _ = stoppvakt('sv-gammal', ny)
    assert rc == 2 and post['slapp'] is False and 'saknar' in post.get('rapport', '') and 'identitet' in post['rapport'], post


@fall('stoppvakten: bara en rapport med körningens identitet binds; filtiden, en kopia, en symlänk och en nästan tom rapport räcker inte')
def _stoppvakt_bunden():
    ny = stampel(60)
    k = TMP / 'sv-rot' / 'kunder' / 'sv-bunden'
    rap = skriv(k / 'RAPPORT.md', rapport(ny))
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 0 and post['slapp'] is True and post['rapport_sha256'] == sha(rap) and post['rapport_korning'] == ny, post
    assert post['rapport_bunden'] == 'identitet' and str(post['skal']).startswith('kontrollerna gröna'), post
    # utan identitet men skriven nu, efter körningens start: filtiden binder inte (granskningen av r101, BÖR 5)
    skriv(rap, rapport())
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 2 and not post.get('rapport_sha256') and 'saknar körningens identitet' in post['rapport'], ('filtiden band rapporten', post)
    # en äldre rapport utan identitet, kopierad tillbaka med cp (ny filtid, samma innehåll)
    aldre = skriv(k / 'rapporter' / 'RAPPORT-fore-x.md', rapport())
    t = time.time() - 86400
    os.utime(aldre, (t, t))
    rap.unlink()
    subprocess.run(['cp', str(aldre), str(rap)], check=True)
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 2 and not post.get('rapport_sha256'), ('en tillbakakopierad rapport binds', post)
    # en symlänk till en rapport med identiteten binds inte (M19)
    rap.unlink()
    mal = skriv(k / 'annan.md', rapport(ny))
    rap.symlink_to(mal)
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 2 and 'symlänk' in post['rapport'], ('en symlänk binds', post)
    rap.unlink()
    # en nästan tom rapport med identiteten binds inte (M42)
    skriv(rap, '---\nkorning: %s\n---\n# R\n' % ny)
    rc, post, _ = stoppvakt('sv-bunden', ny)
    assert rc == 2 and 'nästan tom' in post['rapport'], ('en nästan tom rapport binds', post)


@fall('stoppvakten: den förkastade ateljén släpps bara med en rapport som bär körningens identitet (M22)')
def _stoppvakt_forkastad():
    ny = stampel(60)
    atelje = {'STATUS.json': {'steg': 'forkastad', 'skal': 'panelen förkastade alla riktningar'},
              'VAL.json': {'val': None, 'forkastade': True, 'panel': {'a': {}, 'b': {}}}}
    rap = skriv(TMP / 'sv-rot' / 'kunder' / 'sv-forkastad' / 'RAPPORT.md', rapport('20261001T080000Z'))
    rc, post, fel = stoppvakt('sv-forkastad', ny, atelje)
    assert rc == 2 and post['slapp'] is False and post.get('ateljen_forkastad') and 'gäller körning' in post['rapport'], ('förkastad väg utan bunden rapport', rc, post)
    skriv(rap, rapport(ny))
    rc, post, _ = stoppvakt('sv-forkastad', ny, atelje)
    assert rc == 0 and post['slapp'] is True and post['rapport_sha256'] == sha(rap), post


def bygge(slug, korning, rapport_korning=None, bunden=True, stopp_skal='kontrollerna gröna, RAPPORT.md skriven i körningen och granskningen är godkänd',
          granskning='runda', rot=None, metod=None, slapp=True, godkand=True):
    """Ett bygge som kor.sh och stoppvakten lämnar det, i provets kunder/ (eller i rot/kunder): dist, provet grönt,
    stoppvaktens besked, rapporten och en granskning för bygget med dagens metod (runda), en rotfil för ett äldre bygge
    (rotfil), en rotfil för samma bygge med en annan metod (rotfil-metod) eller ingen (None)."""
    k = (rot or TMP) / 'kunder' / slug
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>%s %s</p>' % (slug, korning))
    h = prova.dist_hash(k / 'sajt' / 'dist')
    rap = skriv(k / 'RAPPORT.md', rapport(rapport_korning or korning))
    skriv(k / 'prov' / 'STATUS.json', {'ok': True, 'tid': '2026-10-07T08:00:00Z', 'dist_sha256': h, 'grindar': {'bygge': {'ok': True}}})
    sv = {'slapp': slapp, 'skal': stopp_skal if slapp else 'blockerad', 'forsok': 1, 'tak': 8, 'korning': korning, 'dist_sha256': h,
          'kontroller_grona': True, 'granskning': 'godkänd' if godkand else 'underkänd'}
    if bunden:
        sv.update(rapport_sha256=sha(rap), rapport_korning=korning, rapport_bunden='identitet', rapport_finns=True,
                  rapport='bär körningens identitet %s' % korning)
    else:  # som stoppvakten skriver en obunden rapport
        sv.update(rapport_finns=False, rapport=korslut.rapport_identitet(rap, korning)['skal'])
    skriv(k / 'prov' / 'STOPPVAKT.json', sv)
    metod = metod or granska.aktuell_metod(slug)
    if granskning == 'runda':
        g = dict(metod, godkand=godkand, runda=1, dist_sha256=h, korning=korning, tid='2026-10-07T08:30:00Z', kriterier={'designkvalitet': {'betyg': 8}})
        skriv(k / 'granskning' / 'runda-01' / 'GRANSKNING.json', g)
        skriv(k / 'granskning' / 'runda-01' / 'UTFALL.json', {'status': 'klar', 'tid': g['tid'], 'skal': ''})
        skriv(k / 'granskning' / 'GRANSKNING.json', g)
    elif granskning == 'rotfil':  # en äldre godkänd granskning av ett annat bygge, utan omgångar
        skriv(k / 'granskning' / 'GRANSKNING.json', dict(metod, godkand=True, runda=1, dist_sha256='e' * 64, korning='20261001T080000Z',
                                                          kriterier={'designkvalitet': {'betyg': 9}}))
    elif granskning == 'rotfil-metod':  # samma bygge, en annan metod (M07)
        skriv(k / 'granskning' / 'GRANSKNING.json', dict(metod, metod_sha='f' * 64, godkand=True, runda=1, dist_sha256=h, korning=korning,
                                                          kriterier={'designkvalitet': {'betyg': 9}}))
    return k, h


def listor(k, fore=None, efter=None):
    """kor.sh:s hashlistor före och efter körningen. Standard: oförändrade, med DOM.json som den är nu (när den finns)."""
    dom = k / 'DOM.json'
    bas = [('kontroller/prova.py', 'aaa')] + ([('kunder/%s/DOM.json' % k.name, sha(dom))] if dom.is_file() else [])
    f = skriv(TMP / 'listor' / ('%s-fore.txt' % k.name), ''.join('%s  %s\n' % (h, p) for p, h in (bas if fore is None else fore)))
    e = skriv(TMP / 'listor' / ('%s-efter.txt' % k.name), ''.join('%s  %s\n' % (h, p) for p, h in (bas if efter is None else efter)))
    return f, e


def korslut_(k, korning, rc='0', fore=None, efter=None, rot=None, env=None):
    f, e = listor(k, fore, efter)
    p = subprocess.run([PY, '-B', str((rot or ROOT) / 'kontroller' / 'korslut.py'), str(k), rc, str(f), str(e), korning],
                       capture_output=True, text=True, timeout=300, env=env)
    return p.returncode, p.stdout, p.stderr


def visa(k, korning=None, rot=None, env=None):
    p = subprocess.run([PY, '-B', str((rot or ROOT) / 'kontroller' / 'korslut.py'), '--visa', str(k)] + ([korning] if korning else []),
                       capture_output=True, text=True, timeout=300, env=env)
    return p.returncode, p.stdout


def slutpost(k, korning):
    f = Path(k) / 'korningar' / korning / 'SLUT.json'
    assert f.is_file(), 'ingen slutpost %s' % f
    return json.loads(f.read_text(encoding='utf-8'))


def varden(post):
    return [post['tillstand'][n]['varde'] for n in ('sessionen_avslutad', 'tekniskt_godkant', 'designgranskaren_godkanner', 'agaren_godkanner',
                                                    'klart_for_leverans')]


@fall('korslut: en gammal rapport till ett nytt bygge nekas och sägs som sådan')
def _korslut_gammal():
    ny = stampel(120)
    k, _ = bygge('ks-gammal', ny, rapport_korning='20261001T080000Z', bunden=False)
    rc, ut, fel = korslut_(k, ny)
    assert rc == 1 and 'gäller körning 20261001T080000Z' in ut, ('en rapport från en annan körning godkändes', rc, ut[-800:], fel[-300:])
    skriv(k / 'RAPPORT.md', rapport())  # utan identitet, och stoppvakten band ingen
    rc, ut, _ = korslut_(k, ny)
    assert rc == 1 and 'saknar identitet' in ut, (rc, ut[-600:])


@fall('korslut: en ändrad rapport och ett besked som band en annan körning nekas; beskedet säger om felet är stoppvaktens eller rapportens')
def _korslut_bunden():
    ny = stampel(120)
    k, _ = bygge('ks-bunden', ny)
    rc, ut, fel = korslut_(k, ny)
    assert rc == 0, ('den bundna rapporten godkändes inte', rc, ut[-800:], fel[-300:])
    skriv(k / 'RAPPORT.md', rapport(ny) + '\nTillagt efter stoppvaktens besked.\n')
    rc, ut, _ = korslut_(k, ny)
    assert rc == 1 and 'inte den rapport som stoppvakten band' in ut, (rc, ut[-600:])
    # stoppvaktens besked band rapporten till en annan körning än sin egen (M43)
    k, _ = bygge('ks-annan-bindning', ny)
    sv = json.loads((k / 'prov' / 'STOPPVAKT.json').read_text())
    skriv(k / 'prov' / 'STOPPVAKT.json', dict(sv, rapport_korning='20261001T080000Z'))
    rc, ut, _ = korslut_(k, ny)
    assert rc == 1 and 'stoppvakten band rapporten till körning 20261001T080000Z' in ut, (rc, ut[-600:])
    # stoppvaktens besked är från en tidigare körning, rapporten bär den här körningens identitet (BÖR 6)
    k, _ = bygge('ks-stoppvakt-gammal', ny)
    skriv(k / 'prov' / 'STOPPVAKT.json', dict(json.loads((k / 'prov' / 'STOPPVAKT.json').read_text()), korning='20261001T080000Z'))
    rc, ut, _ = korslut_(k, ny)
    inte = rad(ut, 'Inte godkänt:')
    assert rc == 1 and 'stoppvaktens besked gäller en annan körning (20261001T080000Z' in inte and 'RAPPORT.md gäller' not in inte, (rc, inte)
    post = slutpost(k, ny)
    rp, st = post['kontroller']['rapporten'], post['kontroller']['stoppvakten']
    assert rp['varde'] is False and 'ingen rapport bands i den här körningen' in rp['text'], ('rapportens bindning prövas mot stoppvaktens körning (M58)', rp)
    assert st['varde'] is False and 'besked från en annan körning' in st['text'], ('stoppvaktens besked från en annan körning räknas (M05)', st)
    # ett besked från före slutposterna, utan rapportens identitet (KAN 6)
    k, _ = bygge('ks-fore-identitet', ny)
    sv = json.loads((k / 'prov' / 'STOPPVAKT.json').read_text())
    for falt in ('rapport', 'rapport_sha256', 'rapport_korning', 'rapport_bunden'):
        sv.pop(falt, None)
    skriv(k / 'prov' / 'STOPPVAKT.json', sv)
    rc, ut, _ = korslut_(k, ny)
    assert rc == 1 and 'från före 2026-10-07' in rad(ut, 'Inte godkänt:'), (rc, rad(ut, 'Inte godkänt:'))


# ===== en historisk granskning gäller inte det aktuella bygget =====

@fall('korslut: en historisk godkänd granskning är historik i beskedet och i slutposten, med vad som skiljer')
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
    assert 'ett annat bygge' in dg['historisk'] and 'en annan metod' not in dg['historisk'], ('vad som skiljer (KAN 4)', dg['historisk'])
    assert not post['bedomningsutfall'].startswith(('godkänt', 'ej bedömt')) and post['tillstand']['klart_for_leverans']['varde'] is False, post['bedomningsutfall']
    # en godkänd omgång i en tidigare körning är också historik, inte en dom över körningens bygge
    k2, h2 = bygge('ks-historisk2', ny, granskning=None)
    g = dict(granska.aktuell_metod('ks-historisk2'), godkand=True, runda=1, dist_sha256='f' * 64, korning='20261001T080000Z', tid='2026-10-01T09:00:00Z')
    skriv(k2 / 'granskning' / 'runda-01' / 'GRANSKNING.json', g)
    skriv(k2 / 'granskning' / 'runda-01' / 'UTFALL.json', {'status': 'klar', 'tid': g['tid'], 'skal': ''})
    rc, ut, _ = korslut_(k2, ny)
    post = slutpost(k2, ny)
    assert rc == 1 and post['tillstand']['designgranskaren_godkanner']['varde'] is None and post['designgranskning']['historisk']['korning'] == '20261001T080000Z', (rc, post['designgranskning'])
    # samma bygge, en annan metod i rotfilen: ingen aktuell dom (M07)
    k3, _ = bygge('ks-annan-metod', ny, granskning='rotfil-metod')
    rc, ut, _ = korslut_(k3, ny)
    post = slutpost(k3, ny)
    assert rc == 1 and post['tillstand']['designgranskaren_godkanner']['varde'] is None and 'GODKÄND' not in ut.split('Rapport:')[0], (rc, post['tillstand']['designgranskaren_godkanner'])
    assert 'en annan metod' in post['tillstand']['designgranskaren_godkanner'].get('historisk', ''), post['tillstand']['designgranskaren_godkanner']


@fall('ab: armens post bär slutpostens dom, inte en historisk rotfil')
def _ab_historisk():
    ny = stampel(120)
    k, h = bygge('ab-hist-abx', ny, granskning='rotfil')
    korslut_(k, ny)
    ab = ladda('ab_slutpost', ROOT / 'kontroller' / 'ab.py')
    ab.KUNDER = TMP / 'kunder'
    m = ab.matt('ab-hist-abx')
    assert m.get('granskning_godkand') is not True, ('armen räknas som godkänd av en granskning som gällde ett annat bygge', m.get('granskning_godkand'))
    assert m.get('slutpost') == 'kunder/ab-hist-abx/korningar/%s/SLUT.json' % ny and m.get('slutkod') == 1, m
    assert m.get('dist_sha256') == h and m.get('slutpost_dist_sha256') == h, m


# ===== punkt 4: de fem tillstånden, vart och ett mot det det bygger på =====

@fall('slutposten: fem tillstånd var för sig, med förväntade rader i terminalen, och ägarens dom efter körningen prövas utan att posten skrivs om')
def _tillstanden():
    ny = stampel(120)
    k, h = bygge('ks-tillstand', ny)
    rc, ut, _ = korslut_(k, ny)
    post = slutpost(k, ny)
    assert rc == 0 and varden(post) == [True, True, True, None, False], varden(post)
    for falt in ('id', 'titel', 'typ', 'uppdrag', 'kund', 'moment', 'forfattare', 'datum', 'granskad_identitet', 'rapportstatus',
                 'bedomningsutfall', 'foregaende', 'ersatt_av', 'underlag', 'beslut', 'atgarder'):
        assert post.get(falt) not in (None, '', []), ('rapporthuvudets fält saknas', falt)
    ident = ' '.join(post['granskad_identitet'])
    assert ('körning %s' % ny) in ident and h in ident and post['metod']['granskning']['metod_sha'] in ident and 'granskningsomgång 1' in ident, ident
    assert post['bedomningsutfall'].startswith('ej bedömt av ägaren') and post['rapportstatus'] == 'färdig', ('KAN 2: utan ägarens dom är utfallet inte godkänt', post['bedomningsutfall'])
    # terminalens rader, förväntade ur fallet och inte ur text() (M30)
    assert rad(ut, 'sessionen avslutad normalt:').startswith('sessionen avslutad normalt: ja — claude avslutade med kod 0'), rad(ut, 'sessionen')
    assert rad(ut, 'tekniskt godkänt:') == 'tekniskt godkänt: ja', rad(ut, 'tekniskt')
    assert rad(ut, 'designgranskaren godkänner:').startswith('designgranskaren godkänner: ja — godkänd; omgång 1, dist %s' % h[:12]), rad(ut, 'designgranskaren')
    assert rad(ut, 'ägaren godkänner:').startswith('ägaren godkänner: ej bedömt — ägarens dom skrivs i dashboarden'), rad(ut, 'ägaren')
    assert rad(ut, 'klart för leverans:') == 'klart för leverans: nej — väntar på ägarens dom', rad(ut, 'klart')
    assert rad(ut, 'Slutkod 0').startswith('Slutkod 0 : tekniskt godkänt och godkänt av designgranskaren'), rad(ut, 'Slutkod')
    assert (k / 'korningar' / ny / 'prov-STATUS.json').is_file() and any('prov-STOPPVAKT.json' in u for u in post['underlag']), post['underlag']
    fore = sha(k / 'korningar' / ny / 'SLUT.json')
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T10:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, efter små ändringar'}}]})
    a = korslut.aktuell(k)
    assert a['tillstand']['agaren_godkanner']['varde'] is False and 'ja med villkor' in a['tillstand']['agaren_godkanner']['text'], a['tillstand']['agaren_godkanner']
    assert a['tillstand']['klart_for_leverans']['varde'] is False and 'tolkning' in a['tillstand']['agaren_godkanner']['text'], a['tillstand']['klart_for_leverans']
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T11:00:00Z', 'bygge_dist': 'a' * 12, 'svar': {'namn': 'Ja, som den är'}}]})
    assert korslut.aktuell(k)['tillstand']['agaren_godkanner']['varde'] is None, 'en dom över ett annat bygge räknas (M08)'
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T11:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    a = korslut.aktuell(k)
    assert a['tillstand']['agaren_godkanner']['varde'] is True and a['tillstand']['klart_for_leverans']['varde'] is True, a['tillstand']['klart_for_leverans']
    _, vt = visa(k)
    assert rad(vt, 'klart för leverans:') == 'klart för leverans: ja — inom omfattningen' and rad(vt, 'Prövad nu').endswith(
        'samma bygge, metod och startsida som vid körningens slut'), (rad(vt, 'klart'), rad(vt, 'Prövad nu'))
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>ombyggt efter körningen</p>')
    a = korslut.aktuell(k)
    assert a['tillstand']['klart_for_leverans']['varde'] is False and a['provad']['samma_bygge'] is False, a['provad']
    assert sha(k / 'korningar' / ny / 'SLUT.json') == fore, 'aktuell() skrev om slutposten'


@fall('tillstånden: slutkoden, claudes kod, rapportens bindning och stoppvaktens egna kontroller avgör var sitt tillstånd')
def _tillstandens_grund():
    ny = stampel(120)
    # claude föll efter att allt annat godkänts, och ägaren har sagt ja: klart för leverans kräver slutkod 0 (M02, M03)
    k, h = bygge('ks-foll', ny)
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T07:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    rc, ut, _ = korslut_(k, ny, rc='1')
    post = slutpost(k, ny)
    assert rc == 4 and varden(post) == [False, True, True, True, False], varden(post)
    assert 'slutkod 4' in post['tillstand']['klart_for_leverans']['text'], post['tillstand']['klart_for_leverans']
    assert rad(ut, 'sessionen avslutad normalt:').startswith('sessionen avslutad normalt: nej — claude avslutade med kod 1 (föll)'), rad(ut, 'sessionen')
    assert rad(ut, 'klart för leverans:').startswith('klart för leverans: nej — slutkod 4'), rad(ut, 'klart')
    # rapporten är inte bunden: inte tekniskt godkänt, och skälet är rapporten (M04)
    k, _ = bygge('ks-obunden', ny, bunden=False)
    rc, ut, _ = korslut_(k, ny)
    post = slutpost(k, ny)
    assert rc == 1 and post['tillstand']['tekniskt_godkant']['varde'] is False and 'rapporten:' in post['tillstand']['tekniskt_godkant']['text'], post['tillstand']['tekniskt_godkant']
    # stoppvakten höll kvar ett tekniskt grönt bygge för granskarens underkännande: tekniskt godkänt, granskaren underkänner (BÖR 3)
    k, _ = bygge('ks-underkand', ny, slapp=False, godkand=False)
    rc, ut, _ = korslut_(k, ny)
    post = slutpost(k, ny)
    t = post['tillstand']
    assert rc == 1 and t['tekniskt_godkant']['varde'] is True and t['designgranskaren_godkanner']['varde'] is False, varden(post)
    assert 'höll kvar' in post['kontroller']['stoppvakten']['text'] and rad(ut, 'tekniskt godkänt:') == 'tekniskt godkänt: ja', (post['kontroller']['stoppvakten']['text'], rad(ut, 'tekniskt'))
    assert post['bedomningsutfall'].startswith('underkänt'), post['bedomningsutfall']


# ===== B1: ägarens dom får aldrig komma från bygget =====

@fall('ägarens dom (B1): en DOM.json som ändrades under körningen eller inte går att pröva mot starten räknas inte, och inte heller senare')
def _dom_korslut():
    ny = stampel(120)
    k, h = bygge('ks-dom', ny)
    dom = skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T09:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    rel = 'kunder/ks-dom/DOM.json'
    # DOM.json fanns inte när körningen startade (som när bygget skriver den)
    rc, ut, _ = korslut_(k, ny, fore=[('kontroller/prova.py', 'aaa')], efter=[('kontroller/prova.py', 'aaa'), (rel, sha(dom))])
    post = slutpost(k, ny)
    ag = post['tillstand']['agaren_godkanner']
    assert rc == 3 and ag['varde'] is None and ag.get('avsandare') == 'ej belagd', ('en dom skriven under körningen räknas', rc, ag)
    assert rad(ut, 'ägaren godkänner:').startswith('ägaren godkänner: ej bedömt — ej belagd') and rel in rad(ut, 'Slutkod 3'), (rad(ut, 'ägaren'), rad(ut, 'Slutkod'))
    assert post['kontroller']['agarens_dom']['andrad_under_korningen'] is True and post['kontroller']['agarens_dom']['ej_belagda'], post['kontroller']['agarens_dom']
    # samma dom räknas inte heller efteråt; en dom som dashboarden lägger till efter körningen räknas
    assert korslut.aktuell(k, ny)['tillstand']['agaren_godkanner']['varde'] is None, 'domen som bygget kan ha skrivit räknas efteråt'
    d = json.loads(dom.read_text())
    d['domar'].append({'tid': '2026-10-07T12:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Nej'}})
    skriv(dom, d)
    assert korslut.aktuell(k, ny)['tillstand']['agaren_godkanner']['varde'] is False, 'dashboardens senare dom räknas inte'
    # hashlistorna tar inte med DOM.json: den går inte att pröva mot starten
    k2, h2 = bygge('ks-dom-oprovad', ny)
    skriv(k2 / 'DOM.json', {'domar': [{'tid': '2026-10-07T09:00:00Z', 'bygge_dist': h2[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    rc, ut, _ = korslut_(k2, ny, fore=[('kontroller/prova.py', 'aaa')], efter=[('kontroller/prova.py', 'aaa')])
    post = slutpost(k2, ny)
    assert rc == 0 and post['tillstand']['agaren_godkanner']['varde'] is None and post['tillstand']['klart_for_leverans']['varde'] is False, varden(post)
    # oförändrad sedan starten: räknas
    k3, h3 = bygge('ks-dom-ok', ny)
    skriv(k3 / 'DOM.json', {'domar': [{'tid': '2026-10-07T07:00:00Z', 'bygge_dist': h3[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    rc, ut, _ = korslut_(k3, ny)
    post = slutpost(k3, ny)
    assert rc == 0 and varden(post) == [True, True, True, True, True] and post['bedomningsutfall'].startswith('godkänt'), (varden(post), post['bedomningsutfall'])


# ===== punkt 4 och 10: beständiga slutbesked genom de verkliga startvägarna =====

KR = TMP / 'kor-repo'
FALSK = TMP / 'falsk-claude'
FALSK_SKRIPT = r'''#!/bin/sh
cat > /dev/null
if [ -n "$PROV_ANDRA_PROTOKOLL" ]; then for f in kunder/"$NWP_SLUG"/korningar/*/SLUT.json; do echo " " >> "$f"; done; fi
if [ -n "$PROV_KATALOG_POST" ]; then mkdir -p kunder/"$NWP_SLUG"/korningar/"$NWP_KORNING"/SLUT.json; fi
if [ -n "$PROV_BYGG" ]; then
  mkdir -p kunder/"$NWP_SLUG"/sajt/dist; echo "<p>$PROV_BYGG</p>" > kunder/"$NWP_SLUG"/sajt/dist/index.html
fi
if [ -n "$PROV_RAPPORT" ]; then
  printf -- "---\nkorning: %s\n---\n# Rapport\n%s\n" "$NWP_KORNING" "$(printf 'Rapporten for korningen. %.0s' $(seq 1 30))" > kunder/"$NWP_SLUG"/RAPPORT.md
fi
if [ -n "$PROV_DOM" ]; then
  H=$(.venv/bin/python -B -c "import sys; from pathlib import Path; sys.path.insert(0, 'kontroller'); import prova; print(prova.dist_hash(Path('kunder/$NWP_SLUG/sajt/dist'))[:12])")
  { printf '{"schema": 1, "domar": [{"tid": "2026-10-07T09:00:00Z", "bygge_dist": "%s", "svar": {"namn": "Ja, som den är"}}]}' "$H" > kunder/"$NWP_SLUG"/DOM.json; } 2> kunder/"$NWP_SLUG"/DOM-FEL.txt
  echo "rc=$?" > kunder/"$NWP_SLUG"/DOM-RC.txt
fi
if [ -n "$PROV_SOV" ]; then exec sleep "$PROV_SOV"; fi
echo '{"type":"result","subtype":"success","num_turns":3,"duration_ms":1000}'
exit 0
'''


def kor_repo():
    """En repokopia med mekaniken (kor.sh, kontroller, krokarna, kritik, kunskap, dashboarden), länkad körmiljö, git och
    en falsk claude vars beteende styrs med PROV_*-variabler."""
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
    skriv(FALSK / 'claude', FALSK_SKRIPT)
    (FALSK / 'claude').chmod(0o755)


def miljo(**extra):
    m = {k: v for k, v in os.environ.items() if not k.startswith(('CLAUDE_CODE_', 'NWP_', 'PROV_')) and k != 'CLAUDECODE'}
    m.update(PATH=str(FALSK) + os.pathsep + m.get('PATH', ''), NWP_STARTKONTROLL='av', NWP_SANDLADA='av', NWP_KORREGISTER=str(TMP / 'korregister'))
    m.update(extra)
    return m


def kor(slug, **extra):
    p = subprocess.run(['bash', str(KR / 'kor.sh'), slug, 'Prov AB, Umeå, https://exempel.se'], capture_output=True, text=True, cwd=str(KR),
                       env=miljo(**extra), timeout=600)
    return p.returncode, p.stdout, p.stderr


def korningar(slug):
    d = KR / 'kunder' / slug / 'korningar'
    return sorted(x.name for x in d.iterdir() if (x / 'SLUT.json').is_file()) if d.is_dir() else []


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
    assert korslut.text(post) in ut and rad(ut, 'Slutkod 2') == 'Slutkod 2: bygget startade inte; kor.sh stannade före bygget', ('terminalens besked', ut[-600:])
    assert post['uppdrag'].endswith('Prov AB, Umeå, https://exempel.se'), ('uppdraget bär verksamheten (KAN 9)', post['uppdrag'])
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
    assert post['slutkod'] == rc and post['korning'] == m.group(1) and varden(post) == [True, False, None, None, False], varden(post)
    assert korslut.text(post) in ut, ('terminalens besked är inte postens text', ut[-800:])
    assert rad(ut, 'sessionen avslutad normalt:').startswith('sessionen avslutad normalt: ja — claude avslutade med kod 0 (success, 3 turer)'), rad(ut, 'sessionen')
    assert rad(ut, 'klart för leverans:').startswith('klart för leverans: nej — slutkod 1'), rad(ut, 'klart')
    assert rad(ut, 'Slutkod 1') == 'Slutkod 1 : avslutat utan grönt prov och godkänd granskning', rad(ut, 'Slutkod')
    flyttad = k / 'rapporter' / ('RAPPORT-fore-%s.md' % m.group(1))
    assert flyttad.is_file() and flyttad.read_bytes() == innehall and not (k / 'RAPPORT.md').exists(), 'den äldre rapporten flyttades inte orörd'
    assert any(('rapporter/RAPPORT-fore-%s.md' % m.group(1)) in u for u in post['underlag']), ('posten länkar inte den flyttade rapporten', post['underlag'])
    if fore:  # stoppets post är ersatt av byggets, och i övrigt orörd
        aldre = slutpost(k, fore[-1])
        assert aldre['rapportstatus'] == 'ersatt' and post['id'] in aldre['ersatt_av'] and aldre['slutkod'] == 2, aldre
        assert post['foregaende'].startswith(aldre['id']), post['foregaende']


@fall('kor.sh: den äldre postens länk pekar på den flyttade rapporten, inte på nästa körnings RAPPORT.md (BÖR 4)')
def _kor_lank():
    kor_repo()
    rc1, ut1, _ = kor('lank-prov', NWP_ATELJE='av', PROV_BYGG='ett', PROV_RAPPORT='1')
    time.sleep(1.1)
    rc2, ut2, _ = kor('lank-prov', NWP_ATELJE='av', PROV_BYGG='tva', PROV_RAPPORT='1')
    k = KR / 'kunder' / 'lank-prov'
    k1, k2 = korningar('lank-prov')[:2]
    p1, p2 = slutpost(k, k1), slutpost(k, k2)
    flyttad = 'kunder/lank-prov/rapporter/RAPPORT-fore-%s.md' % k2
    assert (rc1, rc2) == (1, 1) and p1.get('rapport_flyttad_till') == flyttad, (rc1, rc2, p1.get('rapport_flyttad_till'))
    assert p1['rapport_flyttad']['samma_som_postens'] in (True, None) and any(u.startswith(flyttad) for u in p1['underlag']), p1['underlag']
    assert 'kunder/lank-prov/RAPPORT.md' not in p1['underlag'] and any(u.startswith(flyttad) for u in p2['underlag']), (p1['underlag'], p2['underlag'])
    assert p1['rapportstatus'] == 'ersatt' and p2['id'] in p1['ersatt_av'], 'ett nytt bygge (annan dist) ersätter den äldre posten'


@fall('kor.sh: ett bygge som ändrar en tidigare slutpost, eller skapar en katalog där slutposten ska ligga, får slutkod 3')
def _kor_protokoll():
    kor_repo()
    k = KR / 'kunder' / 'protokoll-prov'
    rc, ut, _ = kor('protokoll-prov', NWP_ATELJE='av')
    assert rc == 1 and len(korningar('protokoll-prov')) == 1, (rc, ut[-300:])
    rc, ut, fel = kor('protokoll-prov', NWP_ATELJE='av', PROV_ANDRA_PROTOKOLL='1')
    assert rc == 3 and 'kunder/protokoll-prov/korningar/' in ut, ('ändrade slutposter godtogs', rc, ut[-600:], fel[-300:])
    post = slutpost(k, korningar('protokoll-prov')[-1])
    assert post['slutkod'] == 3 and post['kontroller']['mekaniken']['varde'] is False, post['kontroller']['mekaniken']
    rc, ut, fel = kor('protokoll-prov', NWP_ATELJE='av', PROV_KATALOG_POST='1')
    assert rc == 3 and 'protokoll:kunder/protokoll-prov/korningar/' in ut and 'skrevs inte' in rad(ut, 'Slutpost:'), ('en katalog i postens ställe', rc, rad(ut, 'Slutpost:'), rad(ut, 'Slutkod'))


@fall('slutposten som uteblir: en katalog i postens ställe ger slutkod 5; trasiga äldre filer fäller inte avslutet (BÖR 2)')
def _uteblir():
    ny = stampel(120)
    k, h = bygge('ks-katalog', ny)
    (k / 'korningar' / ny / 'SLUT.json').mkdir(parents=True)
    rc, ut, _ = korslut_(k, ny)
    assert rc == 5 and rad(ut, 'Slutkod 5').startswith('Slutkod 5: slutposten uteblev') and 'skrevs inte' in rad(ut, 'Slutpost:'), (rc, rad(ut, 'Slutkod'), rad(ut, 'Slutpost:'))
    k2, h2 = bygge('ks-trasigt', ny)
    skriv(k2 / 'korningar' / '20261001T080000Z' / 'SLUT.json', '"x"')
    skriv(k2 / 'DOM.json', {'domar': 5})
    rc, ut, fel = korslut_(k2, ny)
    post = slutpost(k2, ny)
    assert rc == 0 and 'Traceback' not in fel and 'trasig' in post['foregaende'], (rc, fel[-300:], post['foregaende'])
    assert any('domar är ingen lista' in b for b in post['brister']) and post['tillstand']['agaren_godkanner']['varde'] is None, post['brister']


@fall('ägarens dom genom kor.sh (B1): en befintlig DOM.json är låst under bygget, och en DOM.json som bygget skriver ger slutkod 3 utan "ägaren godkänner"')
def _kor_dom():
    kor_repo()
    k = KR / 'kunder' / 'dom-prov'
    rc, ut, fel = kor('dom-prov', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DOM='1')
    post = slutpost(k, korningar('dom-prov')[-1])
    ag = post['tillstand']['agaren_godkanner']
    assert rc == 3 and ag['varde'] is None and ag.get('avsandare') == 'ej belagd', ('bygget kunde skriva ägarens dom', rc, ag, ut[-400:])
    assert rad(ut, 'ägaren godkänner:').startswith('ägaren godkänner: ej bedömt — ej belagd') and 'kunder/dom-prov/DOM.json' in rad(ut, 'Slutkod 3'), (rad(ut, 'ägaren'), rad(ut, 'Slutkod'))
    # en befintlig dom (ägarens, skriven före körningen) är låst: bygget kan inte ändra den
    fore = (k / 'DOM.json').read_bytes()
    rc, ut, fel = kor('dom-prov', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DOM='1')
    assert 'rc=0' not in (k / 'DOM-RC.txt').read_text() and 'not permitted' in (k / 'DOM-FEL.txt').read_text(), ((k / 'DOM-RC.txt').read_text(), (k / 'DOM-FEL.txt').read_text())
    assert (k / 'DOM.json').read_bytes() == fore and 'uchg' not in subprocess.run(['stat', '-f', '%Sf', str(k / 'DOM.json')], capture_output=True, text=True).stdout, 'låset tas bort efteråt'
    # domen som bygget skrev i förra körningen räknas inte heller nu, fast filen är oförändrad sedan den här körningens start
    ag = slutpost(k, korningar('dom-prov')[-1])['tillstand']['agaren_godkanner']
    assert ag['varde'] is None and 'räknas inte' in ag['text'], ('en dom som bygget skrev räknas i nästa körning', ag)


@fall('kor.sh: startkontrollens stopp och en namnkrock i rapporter/ ger en kort post, och ingenting skrivs över (M28, M26)')
def _kor_stopp_ovriga():
    kor_repo()
    sk = KR / 'kontroller' / 'startkontroll.py'
    orig = sk.read_bytes()
    try:
        sk.write_text('import sys\nprint("startkontrollen: stoppad i provet")\nsys.exit(1)\n')
        rc, ut, _ = kor('skstopp-prov', NWP_ATELJE='av')
    finally:
        sk.write_bytes(orig)
    k_ = korningar('skstopp-prov')
    post = slutpost(KR / 'kunder' / 'skstopp-prov', k_[-1]) if k_ else {}
    assert rc == 2 and 'startkontrollen stoppade bygget' in post.get('skal', '') and any('startkontroll.log' in u for u in post.get('underlag') or []), (rc, post.get('skal'), post.get('underlag'))
    k = KR / 'kunder' / 'krock-prov'
    gammal = skriv(k / 'RAPPORT.md', rapport('20261001T080000Z'))
    innehall = gammal.read_bytes()
    nu_ = datetime.now(timezone.utc)
    upptagna = [skriv(k / 'rapporter' / ('RAPPORT-fore-%s.md' % (nu_ + timedelta(seconds=s)).strftime('%Y%m%dT%H%M%SZ')), 'en befintlig fil %d\n' % s)
                for s in range(0, 90)]
    rc, ut, _ = kor('krock-prov', NWP_ATELJE='av')
    k_ = korningar('krock-prov')
    assert rc == 2 and k_ and 'kunde inte flyttas' in slutpost(k, k_[-1])['skal'], (rc, ut[-300:])
    assert gammal.read_bytes() == innehall and all(p.read_text().startswith('en befintlig fil') for p in upptagna), 'flytten skrev över något'


@fall('kor.sh: SIGTERM ger en post med slutkoden; efter SIGKILL säger nästa start och --visa att körningen avbröts utan slutpost (BÖR 1)')
def _kor_signal():
    kor_repo()
    for slug, sig in (('term-prov', signal.SIGTERM), ('kill-prov', signal.SIGKILL)):
        k = KR / 'kunder' / slug
        skriv(k / 'RAPPORT.md', rapport('20261001T080000Z'))
        logg = TMP / ('%s.out' % slug)
        with open(logg, 'w') as ut_:
            p = subprocess.Popen(['bash', str(KR / 'kor.sh'), slug, 'Prov AB, Umeå'], stdout=ut_, stderr=subprocess.STDOUT, cwd=str(KR),
                                 env=miljo(NWP_ATELJE='av', PROV_SOV='60'), start_new_session=True)
        slut = time.time() + 120
        while time.time() < slut and 'startad' not in logg.read_text():
            time.sleep(0.2)
        time.sleep(1.5)
        start = re.search(r'startad (\d{8}T\d{6}Z)', logg.read_text())
        os.kill(p.pid, sig)
        try:
            rc = p.wait(timeout=90)
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)  # en kvarlämnad falsk claude efter SIGKILL
            except OSError:
                pass
        assert start, ('kor.sh startade inte bygget', logg.read_text()[-300:])
        if sig == signal.SIGTERM:
            post = slutpost(k, start.group(1))
            assert rc == 4 and post['slutkod'] == 4 and post.get('avbruten') == 'SIGTERM' and 'SIGTERM' in rad(logg.read_text(), 'Slutkod 4'), (rc, post.get('avbruten'), logg.read_text()[-400:])
            assert any(('rapporter/RAPPORT-fore-%s.md' % start.group(1)) in u for u in post['underlag']), post['underlag']
            assert not (KR / 'kunder' / '.bygge-pid').exists(), 'låset ligger kvar efter SIGTERM'
        else:
            assert not (k / 'korningar' / start.group(1) / 'SLUT.json').exists() and (k / 'korningar' / start.group(1) / 'START.json').is_file(), 'SIGKILL'
            subprocess.run(['chflags', 'nouchg', str(KR / 'kunder'), str(KR / 'underlag')], capture_output=True)
            _, vt = visa(k)
            assert ('körningen %s' % start.group(1)) in rad(vt, 'Avbruten utan slutpost:') and 'RAPPORT-fore-%s' % start.group(1) in vt, vt[-500:]
            rc2, ut2, _ = kor(slug, NWP_ATELJE='av')
            nasta = slutpost(k, korningar(slug)[-1])
            assert ('Förra körningen: körningen %s' % start.group(1)) in ut2 and any(('körningen %s' % start.group(1)) in b and 'avbröts utan slutpost' in b
                                                                                 for b in nasta['brister']), (ut2[-500:], nasta['brister'])


@fall('--visa: en ändrad metod (GRANSKARE.md), en annan godkänd startsida och en ändrad dist gör godkännandena till historik (B2)')
def _visa_andrat():
    kor_repo()
    slug = 'b2-prov'
    vin = KR / 'underlag' / slug / 'atelje' / 'VINNARE.json'
    skriv(vin, {'godkand': {'tid': '2026-10-07T06:00:00Z', 'av': 'ägaren', 'kandidat': 'k01', 'version': 'v1' * 32, 'sha_index': 'a' * 64}})
    metod = json.loads(subprocess.run([PY, '-B', '-c', 'import sys, json; sys.path.insert(0, %r); import granska; print(json.dumps(granska.aktuell_metod(%r)))'
                                       % (str(KR / 'kontroller'), slug)], capture_output=True, text=True, cwd=str(KR), env=miljo()).stdout)
    ny = stampel(120)
    k, h = bygge(slug, ny, rot=KR, metod=metod)
    env = miljo()
    rc, ut, fel = korslut_(k, ny, rot=KR, env=env)
    assert rc == 0, (rc, ut[-600:], fel[-300:])
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T10:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    _, vt = visa(k, rot=KR, env=env)
    assert rad(vt, 'klart för leverans:') == 'klart för leverans: ja — inom omfattningen' and 'aktuell metod' in rad(vt, 'Granskningen:'), (rad(vt, 'klart'), rad(vt, 'Granskningen'))
    gm = KR / 'kritik' / 'GRANSKARE.md'
    orig = gm.read_bytes()
    try:
        gm.write_bytes(orig + '\n<!-- metoden ändrad efter körningen (provet) -->\n'.encode('utf-8'))
        _, vt = visa(k, rot=KR, env=env)
    finally:
        gm.write_bytes(orig)
    assert 'granskningens metod har ändrats' in rad(vt, 'Prövad nu') and 'aktuell metod' not in vt, ('ändrad metod', rad(vt, 'Prövad nu'), vt[-900:])
    assert rad(vt, 'klart för leverans:').startswith('klart för leverans: nej — granskningens metod har ändrats'), rad(vt, 'klart')
    assert rad(vt, 'designgranskaren godkänner:').startswith('designgranskaren godkänner: ej bedömt — historik') and rad(vt, 'Granskningen:').startswith('Granskningen: historik'), (rad(vt, 'designgranskaren'), rad(vt, 'Granskningen'))
    assert rad(vt, 'tekniskt godkänt:').startswith('tekniskt godkänt: ej bedömt — historik'), rad(vt, 'tekniskt')
    _, vt = visa(k, rot=KR, env=env)
    assert rad(vt, 'klart för leverans:') == 'klart för leverans: ja — inom omfattningen', ('metoden återställd', rad(vt, 'klart'))
    orig_vin = vin.read_bytes()
    try:
        skriv(vin, {'godkand': {'tid': '2026-10-07T09:00:00Z', 'av': 'ägaren', 'kandidat': 'k02', 'version': 'v2' * 32, 'sha_index': 'b' * 64}})
        _, vt = visa(k, rot=KR, env=env)
    finally:
        vin.write_bytes(orig_vin)
    assert 'startsidans godkännande (VINNARE.json) har ändrats' in rad(vt, 'Prövad nu') and 'aktuell metod' not in vt, rad(vt, 'Prövad nu')
    assert rad(vt, 'klart för leverans:').startswith('klart för leverans: nej'), rad(vt, 'klart')
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>ombyggt efter körningen</p>')
    _, vt = visa(k, ny, rot=KR, env=env)
    assert 'bygget i dist/ har ändrats' in rad(vt, 'Prövad nu') and rad(vt, 'tekniskt godkänt:').startswith('tekniskt godkänt: ej bedömt — historik'), (rad(vt, 'Prövad nu'), rad(vt, 'tekniskt'))
    assert 'aktuell metod' not in vt and rad(vt, 'klart för leverans:').startswith('klart för leverans: nej'), vt[-700:]


@fall('--visa utan körning visar posten för bygget i dist/; ett stopp och en senare körning som föll ersätter den inte (BÖR 7, M13)')
def _visa_val():
    ny = stampel(300)
    k, h = bygge('ks-val', ny)
    rc, ut, _ = korslut_(k, ny)
    assert rc == 0, rc
    ny2 = stampel(200)
    subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'korslut.py'), '--stopp', str(k), ny2, 'startkontrollen stoppade bygget: provet'], capture_output=True)
    ny3 = stampel(100)
    skriv(k / 'prov' / 'STOPPVAKT.json', dict(json.loads((k / 'prov' / 'STOPPVAKT.json').read_text()), korning=ny3))
    rc3, _, _ = korslut_(k, ny3, rc='1')
    assert rc3 == 4, rc3
    p1 = slutpost(k, ny)
    assert p1['rapportstatus'] == 'färdig' and p1['ersatt_av'] == 'ej angivet', ('stoppet eller körningen som föll ersatte byggets post', p1['rapportstatus'], p1['ersatt_av'])
    _, vt = visa(k)
    assert rad(vt, 'Slutkod 0').startswith('Slutkod 0') and rad(vt, 'Slutpost:').endswith('%s/SLUT.json' % ny), (rad(vt, 'Slutkod'), rad(vt, 'Slutpost:'))
    assert ny2 in rad(vt, 'Senare start som stannade') and ny3 in rad(vt, 'Senare körning:'), (rad(vt, 'Senare start'), rad(vt, 'Senare körning'))


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
        if logg.is_file() and 'Slutkod' in logg.read_text(encoding='utf-8', errors='replace') and not (KR / 'kunder' / '.bygge-pid').exists():
            break
        time.sleep(0.3)
    time.sleep(0.5)
    text = logg.read_text(encoding='utf-8', errors='replace')
    k_ = korningar('demo-prov')
    assert 'ingen godkänd startsida' in text and len(k_) == 1, ('demons körning saknar slutpost', k_, text[-400:])
    post = slutpost(KR / 'kunder' / 'demo-prov', k_[0])
    assert post['slutkod'] == 2 and korslut.text(post) in text and rad(text, 'Slutkod 2').startswith('Slutkod 2: bygget startade inte'), ('loggen bär inte postens text', text[-500:])


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
    return ladda('kalibrering_slutpost', ROOT / 'kontroller' / 'granskarforsok' / 'kalibrering.py')


RADER = [{'id': 'K02', 'agaren': 'nastan', 'granskaren': 'underkänd', 'niva': 1, 'betyg': {'designkvalitet': 6}, 'blockerande': 5, 'utfall': 'rätt'}]
SUMMA = {'undanhallna': 1, 'svar': 1, 'ofullstandiga': 0, 'falska_godkannanden': 0, 'av_ej_over': 1, 'falska_underkannanden': 0, 'av_over': 0}
DOM = 'Rubrikerna står i samma storlek överallt och bilderna är beskurna utan tanke på vad de visar.'
NIVA = 'kunskap/visuell-niva.md'


@fall('kalibreringen: mallen skriver nivåfilens sha och läckageprovet, och undanhållna bara när provet faktiskt prövat texter (BÖR 8, M36)')
def _kalibrering_mall():
    kf = ladda_kalibrering()
    mal = TMP / 'kal' / 'utan-prov'  # mallen anropad utan läckageprov: exemplen får inte kallas undanhållna
    mal.mkdir(parents=True)
    md = kf.rapport(RADER, dict(SUMMA), mal, 'm', 'e').read_text()
    assert 'ndanhållna' not in md.split('**Giltighet')[0] and 'utvecklingsdata' in md and 'Läckageprovet: inte gjort' in md, md[:500]
    exempel = [{'id': 'K02', 'niva': 'nastan', 'skiljer': DOM}]
    lackt = kf.lackageprov(exempel, {NIVA: '# Nivå\n\n- ' + DOM.lower() + '\n'})
    assert lackt['ok'] is False and lackt['traffar'] and lackt['traffar'][0]['id'] == 'K02', lackt
    assert kf.lackageprov(exempel, {NIVA: 'ren', 'kritik/GRANSKARE.md': 'Se K02 i underlaget.'})['ok'] is False, 'exemplets id i metoden är läckage'
    tomt = kf.lackageprov(exempel, {})
    assert tomt['ok'] is False and tomt['status'].startswith('ej prövat') and 'inga texter' in tomt['status'], ('läckageprovet utan texter gick igenom (M61)', tomt)
    utan_niva = kf.lackageprov(exempel, {'kritik/GRANSKARE.md': 'En annan text.'})
    assert utan_niva['ok'] is False and 'nivåfilen' in utan_niva['status'], utan_niva
    kort = kf.lackageprov([{'id': 'K02', 'niva': 'nastan', 'skiljer': 'För kort dom.'}], {NIVA: 'ren text'})
    assert kort['ok'] is False and kort['ej_provade'] == ['K02'], ('ett exempel som inte kunde prövas fäller provet (M36)', kort)
    rent = kf.lackageprov(exempel, {NIVA: '# Nivå\n\nEn helt annan text om typografi och rytm.\n'})
    assert rent['ok'] is True and rent['status'] == 'inga ordagranna spår' and rent['texter'] == 1, rent
    for namn, lp in (('lackt', lackt), ('tomt', tomt)):
        m = TMP / 'kal' / namn
        m.mkdir(parents=True)
        md = kf.rapport(RADER, dict(SUMMA), m, 'm', 'e', lackage=lp, nivafil={'fil': NIVA, 'sha256': 'ab' * 32}).read_text()
        js = json.loads((m / 'RAPPORT.json').read_text())
        assert 'ndanhållna' not in md.split('**Giltighet')[0] and 'Prövade exempel: 1' in md, (namn, md[:400])
        assert js['giltighet'] == 'utvecklingsdata' and 'undanhallna' not in js['sammanfattning'] and js['sammanfattning']['provade'] == 1, (namn, js)
        assert ('ab' * 32) in md and 'Läckageprovet' in md and 'ordagranna' in md, (namn, md[:700])
    m = TMP / 'kal' / 'rent'
    m.mkdir(parents=True)
    md = kf.rapport(RADER, dict(SUMMA), m, 'm', 'e', lackage=rent, nivafil={'fil': NIVA, 'sha256': 'cd' * 32}).read_text()
    js = json.loads((m / 'RAPPORT.json').read_text())
    assert 'Undanhållna exempel utan ordagranna spår' in md and 'omskriven destillering' in md and js['giltighet'].startswith('undanhållna'), (md[:600], js['giltighet'])


@fall('kalibreringen: huvudvägen prövar läckaget mot det granskaren läste, nivåfilen och ankarna i den frysta katalogen (M37)')
def _kalibrering_huvudvag():
    kf = ladda_kalibrering()
    mal = TMP / 'kal' / 'huvudvag'
    fryst = mal / 'K02'
    skriv(fryst / 'metod' / NIVA, '# Nivå\n\nEn helt annan text om typografi och rytm.\n')
    shutil.copy2(ROOT / 'kritik' / 'SCHEMA-granskning.json', skriv(fryst / 'metod' / 'kritik' / 'SCHEMA-granskning.json', ''))
    skriv(fryst / 'kalibrering.md', '# Ankarna\n\nÄgarens ord om ankarna.\n')
    krit = {n: {'betyg': 5, 'motivering': '', 'visa': False} for n in granska.KRITERIER}
    helt = {'kriterier': krit, 'kognitiv_genomgang': [], 'blockerande': [], 'forbattringar': [], 'styrkor': [], 'likhet_tidigare': '', 'sett': [],
            'ej_bedomt': [], 'sammanfattning': ''}
    skriv(fryst / 'svar.json', {'subtype': 'success', 'structured_output': helt})
    skriv(fryst / 'KORNING.json', {'slutkod': 0})
    exempel = [{'id': 'K02', 'niva': 'nastan', 'skiljer': DOM}]
    md, rader, s = kf.slutrapport(exempel, mal, 'm', 'e')
    js = json.loads((mal / 'RAPPORT.json').read_text())
    assert js['lackageprov']['texter'] >= 2 and NIVA in js['lackageprov']['provat'] and 'kalibrering.md' in js['lackageprov']['provat'], js['lackageprov']
    assert js['giltighet'].startswith('undanhållna') and js['nivafil']['sha256'] == sha(fryst / 'metod' / NIVA), (js['giltighet'], js['nivafil'])
    skriv(fryst / 'metod' / NIVA, '# Nivå\n\n- ' + DOM + '\n')
    kf.slutrapport(exempel, mal, 'm', 'e')
    assert json.loads((mal / 'RAPPORT.json').read_text())['giltighet'] == 'utvecklingsdata', 'läckage i nivåfilen på huvudvägen'


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
    original_json = json.dumps(js0, ensure_ascii=False, indent=1) + '\n'
    skriv(mal / 'RAPPORT.json', original_json)
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
    assert js['rattelse']['original_json'] == original_json, 'den ursprungliga RAPPORT.json sparas ordagrant i rättelsen (KAN 7)'
    assert {k: js[k] for k in js0} == js0, 'siffrorna och raderna ändrades'
    assert ut == {'RAPPORT.md': (fore['RAPPORT.md'], sha(mal / 'RAPPORT.md')), 'RAPPORT.json': (fore['RAPPORT.json'], sha(mal / 'RAPPORT.json'))}, ut
    efter = {n: sha(mal / n) for n in fore}
    ut2 = kf.ratta(mal, '2026-10-07', 'utvecklingsdata', skal, ['LARDOMAR.md rad 190–205'])
    assert {n: sha(mal / n) for n in fore} == efter and ut2 == {n: (efter[n], efter[n]) for n in efter}, 'samma rättelse en gång till ändrade rapporten'


print('slutbeskedets prov: %d fall föll%s' % (len(FEL), (': ' + '; '.join(FEL)) if FEL else ''), file=sys.stderr)
sys.exit(1 if FEL else 0)
