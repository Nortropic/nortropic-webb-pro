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
  prövas; huvudvägen prövar mot det granskaren läste; en äldre rapport rättas med ett daterat block överst;
- skyddet av ägarens dom och byggets processer (omgranskningen GR-20261007-r101-om, BÖR 1, BÖR 2, KAN 1–6 och KAN 8;
  GR-20261007-r101-om2, KAN 5), genom kor.sh med en attrapp: ett eget skript som förfalskar hashlistan, tar bort låset på
  DOM.json eller ändrar mekaniken ger slutkod 3 eller ej belagd, aldrig "ägaren godkänner: ja"; en demon som lämnat sin
  session stoppas innan låset släpps; ägarens verkliga dom räknas, också de äldre domarna när bygget lagt till en;
  ingen process blir kvar efter SIGTERM, SIGINT eller SIGHUP till kor.sh eller gruppen, och claude som inte avslutar på
  SIGTERM får SIGKILL efter fristen; slutkoden vid en stängd terminal är postens; efter SIGKILL skriver vakten posten och
  släpper låsen, och ägarens senare dom räknas; en körning utan post sägs som avbruten eller med en post som uteblev; ett
  kommando som faller under set -e ger en post med skälet; avslutet fullföljs trots en signal till gruppen.

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
import korregister  # noqa: E402
korregister.registrera_tmp(TMP, 'prov_slutpost')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
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


INGA_KVAR = json.dumps({'stoppade': [], 'kvar': []})

# Bara provets egen logg och eget hem. En fullständig syntetisk session behövs
# när fallen prövar rapport/dom/processer; kompetensgrinden körs oförändrad.
from prov_helbygge_fixtur import KOMPETENS_FIXTUR, skapa_bevis


def minne(k, f, e):
    """kor.sh:s minne som korslut får det: hashlistornas sha256, sha256 för DOM.json när den låstes (här ur listan före)
    och vaktens besked om byggets processer."""
    start = korslut.hashlista(f).get('kunder/%s/DOM.json' % Path(k).name)
    return {'NWP_SKYDDAT_SHA256': '%s %s' % (sha(f), sha(e)), 'NWP_DOM_START_SHA256': start or 'saknas', 'NWP_PROCESSER': INGA_KVAR}


def korslut_(k, korning, rc='0', fore=None, efter=None, rot=None, env=None, med_minne=True, **andra):
    hem = TMP / 'korslut-hem'
    skapa_bevis(rot or ROOT, hem, k, korning, PY)
    f, e = listor(k, fore, efter)
    m = dict(os.environ if env is None else env)
    m['HOME'] = str(hem)
    if med_minne:
        m.update(minne(k, f, e))
    m.update(andra)
    p = subprocess.run([PY, '-B', str((rot or ROOT) / 'kontroller' / 'korslut.py'), str(k), rc, str(f), str(e), korning],
                       capture_output=True, text=True, timeout=300, env=m)
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
    # ett ja med villkor är ett eget värde, varken ja eller nej, och inget godkännande för leveransen (GR-20261007-r101-om, KAN-7)
    assert a['tillstand']['agaren_godkanner']['varde'] == 'villkorat' and 'ja med villkor' in a['tillstand']['agaren_godkanner']['text'], a['tillstand']['agaren_godkanner']
    assert korslut.VILLKORAT == 'villkorat'
    assert a['tillstand']['klart_for_leverans']['varde'] is False and 'tolkning' in a['tillstand']['agaren_godkanner']['text'], a['tillstand']['klart_for_leverans']
    assert 'med villkor (efter små ändringar)' in a['tillstand']['klart_for_leverans']['text'], a['tillstand']['klart_for_leverans']
    _, vt_ = visa(k)
    assert rad(vt_, 'ägaren godkänner:').startswith('ägaren godkänner: ja med villkor'), rad(vt_, 'ägaren')
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-07T10:30:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Nej, inte utan större ändringar'}}]})
    assert korslut.aktuell(k)['tillstand']['agaren_godkanner']['varde'] is False, 'ett nej är fortfarande nej'
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


@fall('korslut: en körning som avbröts med en signal får slutkod 4 också när claude hann avsluta med kod 0, och blir aldrig klar för leverans (GR-20261008-r117-claude#C1)')
def _avbruten_med_kod_0():
    ny = stampel(120)
    k, h = bygge('ks-avbruten-0', ny)
    rc, ut, fel = korslut_(k, ny, rc='0', NWP_AVBRUTEN='TERM')
    post = slutpost(k, ny)
    assert rc == 4 and post['slutkod'] == 4 and post.get('avbruten') == 'SIGTERM', (rc, post.get('slutkod'), post.get('avbruten'), ut[-600:], fel[-300:])
    assert varden(post)[0] is False and varden(post)[4] is False, varden(post)
    assert rad(ut, 'Slutkod 4').startswith('Slutkod 4: claude avslutade med kod 0, men körningen avbröts med SIGTERM'), rad(ut, 'Slutkod')
    # ägarens ja efteråt gör inte en avbruten körning leveransklar
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-08T12:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    a = korslut.aktuell(k)
    assert a['tillstand']['agaren_godkanner']['varde'] is True and a['tillstand']['klart_for_leverans']['varde'] is False, a['tillstand']['klart_for_leverans']
    assert 'sessionen avslutades inte normalt' in a['tillstand']['klart_for_leverans']['text'], a['tillstand']['klart_for_leverans']['text']
    _, vt = visa(k)
    assert rad(vt, 'klart för leverans:').startswith('klart för leverans: nej'), rad(vt, 'klart')


@fall('korslut: en dom som tillkommer efter en körning vars processer inte stoppades räknas inte i den aktuella läsningen (GR-20261008-r117-claude#C2)')
def _hinder_sen_dom():
    ny = stampel(120)
    k, h = bygge('ks-hinder', ny)
    kvar = json.dumps({'stoppade': [], 'kvar': [{'pid': 4242, 'namn': 'node', 'uid': 'x'}]})
    rc, ut, fel = korslut_(k, ny, NWP_PROCESSER=kvar)
    post = slutpost(k, ny)
    proto = post['kontroller']['agarens_dom']
    assert rc == 0 and proto['hinder'] and post['tillstand']['agaren_godkanner']['varde'] is None, (rc, proto, ut[-400:], fel[-300:])
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-08T12:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
    a = korslut.aktuell(k)
    ag = a['tillstand']['agaren_godkanner']
    assert ag['varde'] is None and ag.get('avsandare') == korslut.EJ_BELAGD and 'processer' in ag['text'], ('en dom skriven efter en körning med hinder räknades', ag)
    assert a['tillstand']['klart_for_leverans']['varde'] is False, a['tillstand']['klart_for_leverans']
    _, vt = visa(k)
    assert rad(vt, 'ägaren godkänner:').startswith('ägaren godkänner: ej bedömt'), rad(vt, 'ägaren godkänner')


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
K=kunder/"$NWP_SLUG"
SID="$(.venv/bin/python -B -c 'import sys; print(sys.argv[sys.argv.index("--session-id")+1])' "$@")"
.venv/bin/python -B "$PROV_KOMPETENS_FIXTUR" "$PWD" "$HOME" "$NWP_SLUG" "$SID"
if [ -n "$PROV_ARGV" ]; then cat > "$K"/PROMPT.txt; else cat > /dev/null; fi
[ -z "$PROV_IGNORERA_TERM" ] || trap '' TERM
[ -z "$PROV_ARGV" ] || printf '%s\n' "$@" > "$K"/ARGV.txt
dist12() { .venv/bin/python -B -c "import sys; from pathlib import Path; sys.path.insert(0, 'kontroller'); import prova; print(prova.dist_hash(Path('$K/sajt/dist'))[:12])"; }
egen_dom() { printf '{"schema": 1, "domar": [{"tid": "2026-10-07T09:00:00Z", "bygge_dist": "%s", "svar": {"namn": "Ja, som den är"}}]}\n' "$(dist12)"; }
if [ -n "$PROV_ANDRA_PROTOKOLL" ]; then for f in "$K"/korningar/*/SLUT.json; do echo " " >> "$f"; done; fi
if [ -n "$PROV_KATALOG_POST" ]; then mkdir -p "$K"/korningar/"$NWP_KORNING"/SLUT.json; fi
if [ -n "$PROV_BYGG" ]; then
  mkdir -p "$K"/sajt/dist; echo "<p>$PROV_BYGG</p>" > "$K"/sajt/dist/index.html
fi
if [ -n "$PROV_RAPPORT" ]; then
  printf -- "---\nkorning: %s\n---\n# Rapport\n%s\n" "$NWP_KORNING" "$(printf 'Rapporten for korningen. %.0s' $(seq 1 30))" > "$K"/RAPPORT.md
fi
if [ -n "$PROV_DOM" ]; then
  { egen_dom > "$K"/DOM.json; } 2> "$K"/DOM-FEL.txt
  echo "rc=$?" > "$K"/DOM-RC.txt
fi
# ett eget skript: en dom kopierad på plats (cp är tillåtet), eller låset borttaget med os.chflags och domen omskriven eller
# tillagd, och hashlistan före körningen omskriven så att DOM.json och kritik/GRANSKARE.md ser oförändrade ut
if [ -n "$PROV_DOM_CP" ]; then egen_dom > "$K"/utkast.json; cp "$K"/utkast.json "$K"/DOM.json; fi
if [ -n "$PROV_DOM_SKRIPT" ]; then
  egen_dom > "$K"/utkast.json
  .venv/bin/python -B -c "
import json, os, stat
p = '$K/DOM.json'
os.chflags(p, 0)
ny = json.load(open('$K/utkast.json'))
if '$PROV_DOM_SKRIPT' == 'lagg_till':
    d = json.load(open(p)); d['domar'] += ny['domar']; ny = d
open(p, 'w').write(json.dumps(ny))
os.chflags(p, stat.UF_IMMUTABLE)
"
fi
if [ -n "$PROV_MEKANIK" ]; then echo "<!-- ändrad av bygget -->" >> kritik/GRANSKARE.md; fi
if [ -n "$PROV_LISTA" ]; then
  .venv/bin/python -B -c "
import hashlib
f = '$K/prov/.skyddat-fore'
rader = open(f).read().splitlines()
for p in ('$K/DOM.json', 'kritik/GRANSKARE.md'):
    try:
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except OSError:
        continue
    rader = [r for r in rader if not r.endswith('  ' + p)] + [h + '  ' + p]
open(f, 'w').write('\n'.join(rader) + '\n')
"
fi
# en process som lever kvar efter sessionen: lämnar sin session (setsid), får en ny förälder när skalet slutar, väntar tills
# låset är borta och skriver då domen
if [ -n "$PROV_DEMON" ]; then
  egen_dom > "$K"/utkast.json
  nohup .venv/bin/python -B -c "
import os, shutil, time
os.setsid()
open('$K/DEMON.pid', 'w').write(str(os.getpid()))
slut = time.time() + 60
while time.time() < slut and os.path.exists('kunder/.bygge-pid'):
    time.sleep(0.1)
time.sleep(0.5)
shutil.copyfile('$K/utkast.json', '$K/DOM.json')
open('$K/DEMON-SKREV', 'w').write('ja')
" > /dev/null 2>&1 &
  for _ in $(seq 1 100); do [ -s "$K"/DEMON.pid ] && break; sleep 0.1; done
fi
if [ -n "$PROV_BARNBARN" ]; then  # ett barnbarn i en egen session, som sover
  nohup .venv/bin/python -B -c "
import os, time
os.setsid()
open('$K/BARNBARN.pid', 'w').write(str(os.getpid()))
time.sleep(120)
" > /dev/null 2>&1 &
  for _ in $(seq 1 100); do [ -s "$K"/BARNBARN.pid ] && break; sleep 0.1; done
fi
if [ -n "$PROV_BARN" ]; then sleep "$PROV_BARN" & echo $! > "$K"/BARN.pid; wait; fi
if [ -n "$PROV_SOV" ]; then exec sleep "$PROV_SOV"; fi
printf '{"type":"result","subtype":"success","is_error":false,"session_id":"%s","num_turns":3,"duration_ms":1000}\n' "$SID"
exit 0
'''


def kor_repo():
    """En repokopia med mekaniken (kor.sh, kontroller, krokarna, kritik, kunskap, dashboarden), länkad körmiljö, git och
    en falsk claude vars beteende styrs med PROV_*-variabler. Lås som ett tidigare fall lämnat (en dödad körning) tas
    bort, så att fallen inte beror av varandra."""
    if KR.is_dir():
        subprocess.run(['chflags', 'nouchg', str(KR / 'kunder'), str(KR / 'underlag')], capture_output=True)
        return
    KR.mkdir()
    for namn in ('kor.sh', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', '.gitignore', 'dashboard.sh'):
        if (ROOT / namn).is_file():
            shutil.copy2(ROOT / namn, KR / namn)
    for mapp in ('kontroller', 'kritik', 'kunskap', 'dashboard'):
        shutil.copytree(ROOT / mapp, KR / mapp, ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'rokprov'), symlinks=True)
    shutil.copytree(ROOT / '.claude' / 'hooks', KR / '.claude' / 'hooks', ignore=shutil.ignore_patterns('__pycache__'))
    for namn in ('bygg-sajt', 'frontend-design', 'modern-web-guidance'):
        shutil.copytree(ROOT / '.claude/skills' / namn, KR / '.claude/skills' / namn)
    for f in (ROOT / '.claude').glob('settings*.json'):
        shutil.copy2(f, KR / '.claude' / f.name)
    (KR / 'backlog').mkdir()
    os.symlink(ROOT / '.venv', KR / '.venv')
    os.symlink(ROOT / 'kontroller' / 'node_modules', KR / 'kontroller' / 'node_modules')
    git = lambda *a: subprocess.run(['git', '-C', str(KR), *a], capture_output=True, text=True)  # noqa: E731
    git('init', '-q')
    git('config', 'user.name', 'prov')
    git('config', 'user.email', 'prov@example.invalid')
    git('add', '-A')
    git('-c', 'user.name=prov', '-c', 'user.email=prov@example.invalid', 'commit', '-q', '-m', 'bas')
    git('branch', '-M', 'main')
    FALSK.mkdir()
    skriv(FALSK / 'claude', FALSK_SKRIPT)
    skriv(FALSK / 'kompetens.py', KOMPETENS_FIXTUR)
    (FALSK / 'claude').chmod(0o755)


def miljo(**extra):
    m = {k: v for k, v in os.environ.items() if not k.startswith(('CLAUDE_CODE_', 'NWP_', 'PROV_')) and k != 'CLAUDECODE'}
    m.update(PATH=str(FALSK) + os.pathsep + m.get('PATH', ''), NWP_STARTKONTROLL='av', NWP_SANDLADA='av', NWP_KORREGISTER=str(TMP / 'korregister'),
             NWP_FRIST='2', NWP_MCP_CONFIG='av', HOME=str(TMP / 'kor-hem'), PROV_KOMPETENS_FIXTUR=str(FALSK / 'kompetens.py'))
    m.update(extra)
    return m


def kor(slug, **extra):
    p = subprocess.run(['bash', str(KR / 'kor.sh'), slug, 'Prov AB, Umeå, https://exempel.se'], capture_output=True, text=True, cwd=str(KR),
                       env=miljo(**extra), timeout=600)
    return p.returncode, p.stdout, p.stderr


def korningar(slug):
    d = KR / 'kunder' / slug / 'korningar'
    return sorted(x.name for x in d.iterdir() if (x / 'SLUT.json').is_file()) if d.is_dir() else []


# hjälparna för skyddet av ägarens dom och byggets processer (omgranskningen GR-20261007-r101-om och -om2)

LAS = KR / 'kunder' / '.bygge-pid'


def flaggor(p):
    return subprocess.run(['stat', '-f', '%Sf', str(p)], capture_output=True, text=True).stdout.strip()


def lever(k, namn):
    """Pid:en i kunder/<slug>/<namn> när processen lever, annars None."""
    try:
        pid = int((Path(k) / namn).read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def doda(k, *namn):
    for x in namn:
        pid = lever(k, x)
        if pid:
            os.kill(pid, signal.SIGKILL)


def stada_grupp(p):
    try:
        os.killpg(p.pid, signal.SIGKILL)  # det som kor.sh lämnat i sin grupp
    except OSError:
        pass


def kor_bakgrund(slug, vanta=('BARN.pid',), **extra):
    """kor.sh i bakgrunden, i en egen session, tills attrappens pid-filer finns. Ger (processen, loggen)."""
    k = KR / 'kunder' / slug
    logg = TMP / ('%s.out' % slug)
    with open(logg, 'w') as ut_:
        p = subprocess.Popen(['bash', str(KR / 'kor.sh'), slug, 'Prov AB, Umeå'], stdout=ut_, stderr=subprocess.STDOUT, cwd=str(KR),
                             env=miljo(**extra), start_new_session=True)
    slut = time.time() + 120
    while time.time() < slut and not all((k / x).is_file() and (k / x).read_text().strip() for x in vanta):
        if p.poll() is not None:
            break
        time.sleep(0.1)
    time.sleep(0.3)
    return p, logg


def dist12(innehall):
    """dist-hashen (12 tecken) för en dist med bara index.html, som attrappen bygger den (PROV_BYGG)."""
    d = TMP / 'disthash' / innehall / 'dist'
    skriv(d / 'index.html', '<p>%s</p>\n' % innehall)
    return prova.dist_hash(d)[:12]


def agardom(k, d12, namn='Ja, som den är', tid='2026-10-06T20:00:00Z'):
    """En dom som dashboardens Din dom skriver den, före körningen."""
    return skriv(Path(k) / 'DOM.json', {'schema': 1, 'domar': [{'tid': tid, 'bygge_dist': d12, 'svar': {'namn': namn}}]})


def agaren(k, korning=None):
    """(raden 'ägaren godkänner:' ur --visa i provrepot, tillståndet ur posten)."""
    _, vt = visa(k, rot=KR, env=miljo())
    post_ = slutpost(k, korning or korningar(Path(k).name)[-1])
    return rad(vt, 'ägaren godkänner:'), post_['tillstand']['agaren_godkanner']


def korningar_alla(slug):
    d = KR / 'kunder' / slug / 'korningar'
    return sorted(x.name for x in d.iterdir() if (x / 'START.json').is_file()) if d.is_dir() else []


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
    # postens status i terminalen och uppdraget i en fullständig post (omgranskningen av r101, KAN 8: N44 och N47)
    assert rad(ut, 'Posten:') == 'Posten: färdig', rad(ut, 'Posten:')
    assert post['uppdrag'] == '%s: Prov AB, Umeå, https://exempel.se' % korslut.UPPDRAG, ('uppdraget bär verksamheten', post['uppdrag'])
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
    skriv(k / 'DOM.json', {'domar': [{'tid': '2026-10-06T20:00:00Z', 'bygge_dist': 'c' * 12, 'svar': {'namn': 'Nej'}}]})
    nu_ = datetime.now(timezone.utc)
    upptagna = [skriv(k / 'rapporter' / ('RAPPORT-fore-%s.md' % (nu_ + timedelta(seconds=s)).strftime('%Y%m%dT%H%M%SZ')), 'en befintlig fil %d\n' % s)
                for s in range(0, 90)]
    rc, ut, _ = kor('krock-prov', NWP_ATELJE='av')
    k_ = korningar('krock-prov')
    assert rc == 2 and k_ and 'kunde inte flyttas' in slutpost(k, k_[-1])['skal'], (rc, ut[-300:])
    assert gammal.read_bytes() == innehall and all(p.read_text().startswith('en befintlig fil') for p in upptagna), 'flytten skrev över något'
    # stoppet kom efter att DOM.json låsts: avslutet tar bort låset (omgranskningen av r101, KAN 8: N08)
    assert 'uchg' not in flaggor(k / 'DOM.json') and 'uchg' not in flaggor(KR / 'kunder'), ('låset ligger kvar efter stoppet', flaggor(k / 'DOM.json'))


# ===== skyddet av ägarens dom och byggets processer (omgranskningen GR-20261007-r101-om och -om2) =====

@fall('ägarens dom genom kor.sh (BÖR 1): ett eget skript som kopierar in en dom, tar bort låset eller ändrar mekaniken och förfalskar hashlistan ger slutkod 3 och aldrig "ägaren godkänner: ja"; ägarens verkliga dom räknas')
def _kor_forfalskning():
    kor_repo()
    d12 = dist12('bygget')
    fel = []
    # c: DOM.json saknas vid start; en dom kopieras in och hashlistan skrivs om
    rc, ut, _ = kor('fa-c', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DOM_CP='1', PROV_LISTA='1')
    vt, ag = agaren(KR / 'kunder' / 'fa-c')
    if not (rc == 3 and 'lista:kunder/fa-c/prov/.skyddat-fore' in rad(ut, 'Slutkod 3') and ag['varde'] is None and ag.get('avsandare') == 'ej belagd'
            and not vt.startswith('ägaren godkänner: ja')):
        fel.append(('c', rc, rad(ut, 'Slutkod'), ag, vt))
    # d: ägarens dom över ett annat bygge, låst; ett eget skript tar bort låset, skriver om filen, låser igen och skriver om listan
    agardom(KR / 'kunder' / 'fa-d', 'a' * 12)
    rc, ut, _ = kor('fa-d', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DOM_SKRIPT='ersatt', PROV_LISTA='1')
    vt, ag = agaren(KR / 'kunder' / 'fa-d')
    if not (rc == 3 and 'kunder/fa-d/DOM.json' in rad(ut, 'Slutkod 3') and ag['varde'] is None and not vt.startswith('ägaren godkänner: ja')):
        fel.append(('d', rc, rad(ut, 'Slutkod'), ag, vt))
    # m: kritik/GRANSKARE.md ändrad, och listan skriven om så att den ser oförändrad ut
    gm = KR / 'kritik' / 'GRANSKARE.md'
    orig = gm.read_bytes()
    try:
        rc, ut, _ = kor('fa-m', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_MEKANIK='1', PROV_LISTA='1')
    finally:
        gm.write_bytes(orig)
    if not (rc == 3 and 'lista:kunder/fa-m/prov/.skyddat-fore' in rad(ut, 'Slutkod 3')):
        fel.append(('m', rc, rad(ut, 'Slutkod')))
    # k: ägarens verkliga dom, skriven före körningen över samma bygge, räknas
    agardom(KR / 'kunder' / 'fa-k', d12)
    rc, ut, _ = kor('fa-k', NWP_ATELJE='av', PROV_BYGG='bygget')
    vt, ag = agaren(KR / 'kunder' / 'fa-k')
    if not (rc == 1 and ag['varde'] is True and rad(ut, 'ägaren godkänner:').startswith('ägaren godkänner: ja') and vt.startswith('ägaren godkänner: ja')):
        fel.append(('k', rc, ag, vt))
    assert not fel, fel


@fall('ägarens dom genom kor.sh (KAN 3): bygget lägger till en dom i en låst DOM.json; ägarens äldre dom räknas fortfarande, aldrig den tillagda')
def _kor_tillagd_dom():
    kor_repo()
    k = KR / 'kunder' / 'tillagd-prov'
    agardom(k, dist12('bygget'), namn='Nej')
    agarens = korslut.dom_nyckel(json.loads((k / 'DOM.json').read_text())['domar'][0])
    rc, ut, _ = kor('tillagd-prov', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DOM_SKRIPT='lagg_till')
    vt, ag = agaren(k)
    proto = slutpost(k, korningar('tillagd-prov')[-1])['kontroller']['agarens_dom']
    assert rc == 3 and len(json.loads((k / 'DOM.json').read_text())['domar']) == 2, (rc, rad(ut, 'Slutkod'))
    assert ag['varde'] is False and vt.startswith('ägaren godkänner: nej'), ('ägarens äldre dom räknas inte', ag, vt)
    assert len(proto['ej_belagda']) == 1 and agarens not in proto['ej_belagda'], proto


@fall('en process som lever kvar efter sessionen (egen session, ny förälder) stoppas innan låset släpps och kan inte skriva ägarens dom (BÖR 1, punkt l)')
def _kor_demon():
    kor_repo()
    k = KR / 'kunder' / 'demon-prov'
    rc, ut, _ = kor('demon-prov', NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DEMON='1')
    slut = time.time() + 5
    while time.time() < slut and not (k / 'DEMON-SKREV').exists():
        time.sleep(0.2)
    kvar = lever(k, 'DEMON.pid')
    doda(k, 'DEMON.pid')
    vt, _ = agaren(k)
    proc = slutpost(k, korningar('demon-prov')[-1])['kontroller'].get('processer') or {}
    assert not (k / 'DEMON-SKREV').exists() and not kvar, ('demonen levde kvar och skrev domen', kvar, vt)
    assert not vt.startswith('ägaren godkänner: ja') and any(x.get('pid') == int((k / 'DEMON.pid').read_text()) for x in proc.get('stoppade') or []), (vt, proc)
    assert rad(ut, 'Byggets processer:').startswith('Byggets processer: ingen process ur bygget kvar; vakten stoppade'), rad(ut, 'Byggets processer:')


@fall('kor.sh: SIGTERM, SIGINT och SIGHUP under bygget, till kor.sh och till gruppen, ger slutkod 4 och lämnar ingen process, inget lås och ingen låst DOM.json (BÖR 2; KAN 8: N19, N20, N08)')
def _kor_signaler():
    kor_repo()
    fel = []
    for sig in ('TERM', 'INT', 'HUP'):
        for grupp in (False, True):
            slug = 'sig-%s-%s' % (sig.lower(), 'grupp' if grupp else 'kor')
            k = KR / 'kunder' / slug
            agardom(k, 'b' * 12, namn='Nej')
            p, logg = kor_bakgrund(slug, ('BARN.pid', 'BARNBARN.pid'), NWP_ATELJE='av', PROV_BYGG='bygget', PROV_BARNBARN='1', PROV_BARN='60')
            try:
                (os.killpg if grupp else os.kill)(p.pid, getattr(signal, 'SIG' + sig))
                rc = p.wait(timeout=90)
            except subprocess.TimeoutExpired:
                rc = 'väntar'
            finally:  # det som lever kvar räknas före provets egen städning
                kvar = [x for x in ('BARN.pid', 'BARNBARN.pid') if lever(k, x)]
                stada_grupp(p)
                doda(k, 'BARN.pid', 'BARNBARN.pid')
            post_ = slutpost(k, korningar(slug)[-1]) if korningar(slug) else {}
            if not (rc == 4 and post_.get('slutkod') == 4 and post_.get('avbruten') == 'SIG' + sig and ('SIG' + sig) in rad(logg.read_text(), 'Slutkod 4')
                    and not kvar and not LAS.exists() and 'uchg' not in flaggor(k / 'DOM.json')):
                fel.append((slug, rc, post_.get('slutkod'), post_.get('avbruten'), kvar, LAS.exists(), flaggor(k / 'DOM.json')))
            subprocess.run(['chflags', 'nouchg', str(KR / 'kunder'), str(KR / 'underlag'), str(k / 'DOM.json')], capture_output=True)
    assert not fel, fel


@fall('kor.sh: byggets Write och Edit nekas för hashlistorna och körningarnas protokoll, och claude får dem i --disallowedTools (BÖR 1)')
def _kor_nekade():
    kor_repo()
    k = KR / 'kunder' / 'nekad-prov'
    rc, ut, _ = kor('nekad-prov', NWP_ATELJE='av', PROV_ARGV='1')
    argv = (k / 'ARGV.txt').read_text().split('\n')
    nekas = argv[argv.index('--disallowedTools') + 1:]
    nekas = nekas[:next((i for i, x in enumerate(nekas) if x.startswith('--')), len(nekas))]
    for verktyg in ('Write', 'Edit'):
        for vag in ('./kunder/nekad-prov/prov/.skyddat-*', './kunder/nekad-prov/korningar/**', './kunder/nekad-prov/rapporter/**', './kunder/nekad-prov/DOM.json'):
            assert '%s(%s)' % (verktyg, vag) in nekas, ('inte nekat', verktyg, vag, nekas[-12:])


GODKANN = r'''
import sys, json
sys.path.insert(0, 'kontroller')
import atelje, skapande
slug = sys.argv[1]
a = atelje.UNDERLAG / slug / 'atelje'
kod = a / 'vinnare' / 'kod'
atelje.skriv_status(a, {'startad': '2026-10-08T00:00:00Z', 'klar': '2026-10-08T00:00:01Z', 'kandidatflode': True, 'lage': 'valda', 'steg': 'klar_for_bedomning'})
dom = skapande.lagg_till_dom(slug, 'ägaren', 'godkand', 'Syntetiskt teknikprov, ingen riktig ägardom.', tid='2026-10-08T00:00:02Z')
atelje.skriv_json_atomiskt(a / 'VINNARE.json', {'godkand': {'tid': dom['tid'], 'sha_index': skapande.sha256_fil(kod / 'index.astro'),
                                                            'sha_kod': skapande.sha256_katalog(kod), 'underlag_sha': skapande.underlagsversion(slug)}})
print(json.dumps([skapande.godkand_giltig(slug), skapande.underlagsversion(slug)]))
'''
GILTIG = "import sys, json; sys.path.insert(0, 'kontroller'); import skapande; print(json.dumps([skapande.godkand_giltig(sys.argv[1]), skapande.underlagsversion(sys.argv[1])]))"


@fall('kor.sh från en godkänd startsida: godkännandets underlag (steg 1–4) är fryst: Write och Edit nekas för underlagsgrunden, sandlådan nekar Bash, '
      'prompten säger det, och godkännandet gäller efteråt (GR-20261008-r117-claude#A3)')
def _kor_fryst_underlag():
    kor_repo()
    slug = 'fryst-prov'
    u, k = KR / 'underlag' / slug, KR / 'kunder' / slug
    skriv(u / 'INNEHALL.md', '# Innehåll\nSyntetisk sidtext.\n')
    skriv(u / 'BRIEF.md', '# Brief\nSyntetisk.\n')
    skriv(u / 'bilder' / 'BILDER.md', 'fil | källa\n')
    skriv(u / 'atelje' / 'vinnare' / 'kod' / 'index.astro', '<h1>Syntetiskt godkänd startsida</h1>\n')
    (k / 'sajt' / 'src' / 'pages').mkdir(parents=True, exist_ok=True)
    g = subprocess.run([PY, '-B', '-c', GODKANN, slug], cwd=str(KR), capture_output=True, text=True, env=miljo())
    assert g.returncode == 0 and json.loads(g.stdout)[0][0] is True, (g.stdout, g.stderr[-600:])
    fore = json.loads(g.stdout)[1]
    rc, ut, fel = kor(slug, PROV_ARGV='1')
    assert (k / 'ARGV.txt').is_file(), ('kor.sh nådde inte claude', rc, ut[-800:], fel[-400:])
    argv = (k / 'ARGV.txt').read_text().split('\n')
    nekas = argv[argv.index('--disallowedTools') + 1:]
    nekas = nekas[:next((i for i, x in enumerate(nekas) if x.startswith('--')), len(nekas))]
    fryst = ['VERKSAMHET.json', 'BRIEF.md', 'RESEARCH.md', 'INNEHALL.md', 'TEXTUNDERLAG.md', 'BESTALLNING.md', 'UPPDRAG.md', 'REFERENSER.md',
             'KUNDSTART.json', 'bilder/**', 'kalla/**', 'referenser/**']
    saknas = ['%s(./underlag/%s/%s)' % (v, slug, f) for v in ('Write', 'Edit') for f in fryst if '%s(./underlag/%s/%s)' % (v, slug, f) not in nekas]
    assert not saknas, ('inte nekat', saknas, nekas[-14:])
    assert not [x for x in nekas if x.endswith(('/KONCEPT.md)', '/FRASER.txt)', '/RESOR.json)'))], 'steg 5–7:s egna arbetsfiler får skrivas'
    prompt = (k / 'PROMPT.txt').read_text(encoding='utf-8')
    assert 'godkännandets underlag är fryst' in prompt and 'INNEHALL.md TEXTUNDERLAG.md' in prompt and 'bilder/** kalla/** referenser/**' in prompt \
        and 'kunder/%s/INNEHALL-BYGGE.md' % slug in prompt, prompt[-1200:]
    efter = json.loads(subprocess.run([PY, '-B', '-c', GILTIG, slug], cwd=str(KR), capture_output=True, text=True, env=miljo()).stdout)
    assert efter[0][0] is True and efter[1] == fore, ('kor.sh självt gjorde godkännandet historiskt', efter[0])
    # sandlådans skrivregler för Bash och barnen: underlagsgrunden nekas bara från en godkänd startsida, resten av
    # underlag/<slug> skrivs som förut (nekande går före tillåtande)
    def sb(*a):
        p = subprocess.run([PY, '-B', str(KR / 'kontroller' / 'sandlada.py'), slug, '--root', str(KR), '--hem', str(TMP / 'hem'), *a],
                           capture_output=True, text=True, cwd=str(KR))
        assert p.returncode == 0, p.stderr[-400:]
        return json.loads(p.stdout)['sandbox']['filesystem']
    med, utan = sb('--fryst-underlag'), sb()
    for f in ('INNEHALL.md', 'KUNDSTART.json', 'bilder', 'kalla', 'referenser'):
        assert str(u / f) in med['denyWrite'] and str(u / f) not in utan['denyWrite'], (f, med['denyWrite'][-14:])
    assert str(u) in med['allowWrite'] and str(u / 'KONCEPT.md') not in med['denyWrite'], med['allowWrite']


@fall('kor.sh utan vakt: dör vakten under bygget stoppar kor.sh själv claudes processgrupp, med SIGKILL efter fristen, och ägarens dom räknas inte (BÖR 2, KAN 5)')
def _kor_utan_vakt():
    kor_repo()
    k = KR / 'kunder' / 'utan-vakt'
    agardom(k, dist12('bygget'))
    p, logg = kor_bakgrund('utan-vakt', ('BARN.pid',), NWP_ATELJE='av', PROV_BYGG='bygget', PROV_BARN='60', PROV_IGNORERA_TERM='1', NWP_FRIST='2')
    start = re.search(r'startad (\d{8}T\d{6}Z)', logg.read_text())
    assert start, logg.read_text()[-300:]
    for pid in subprocess.run(['pgrep', '-f', 'korvakt.py.*%s' % start.group(1)], capture_output=True, text=True).stdout.split():
        os.kill(int(pid), signal.SIGKILL)
    time.sleep(0.5)
    t0 = time.time()
    try:
        os.kill(p.pid, signal.SIGTERM)
        rc = p.wait(timeout=45)
    except subprocess.TimeoutExpired:
        rc = 'väntar'
    finally:  # det som lever kvar räknas före provets egen städning
        sek = time.time() - t0
        kvar = lever(k, 'BARN.pid')
        stada_grupp(p)
        doda(k, 'BARN.pid')
    post_ = slutpost(k, start.group(1))
    ag = post_['tillstand']['agaren_godkanner']
    assert rc == 4 and sek < 30 and not kvar and not LAS.exists(), (rc, round(sek, 1), kvar, LAS.exists())
    assert ag['varde'] is None and ag.get('avsandare') == 'ej belagd' and post_['kontroller']['processer']['varde'] is None, (ag, post_['kontroller']['processer'])

@fall('kor.sh: claude som inte avslutar på SIGTERM, och ett barnbarn i en egen session som inte heller gör det, får SIGKILL efter fristen (KAN 5)')
def _kor_frist():
    kor_repo()
    k = KR / 'kunder' / 'frist-prov'
    p, _ = kor_bakgrund('frist-prov', ('BARN.pid', 'BARNBARN.pid'), NWP_ATELJE='av', PROV_BARN='60', PROV_BARNBARN='1', PROV_IGNORERA_TERM='1',
                        NWP_FRIST='2')
    t0 = time.time()
    try:
        os.kill(p.pid, signal.SIGTERM)
        rc = p.wait(timeout=45)
    except subprocess.TimeoutExpired:
        rc = 'väntar'
    finally:  # det som lever kvar räknas före provets egen städning
        sek = time.time() - t0
        kvar = [x for x in ('BARN.pid', 'BARNBARN.pid') if lever(k, x)]
        stada_grupp(p)
        doda(k, 'BARN.pid', 'BARNBARN.pid')
    assert rc == 4 and sek < 30 and not kvar and slutpost(k, korningar('frist-prov')[-1])['slutkod'] == 4, (rc, round(sek, 1), kvar)


@fall('kor.sh: SIGHUP när terminalen stängs ger samma slutkod i processen som i posten (KAN 1)')
def _kor_terminal():
    import pty
    import select
    kor_repo()
    k = KR / 'kunder' / 'pty-prov'
    master, slav = pty.openpty()
    p = subprocess.Popen(['bash', str(KR / 'kor.sh'), 'pty-prov', 'Prov AB, Umeå'], stdin=slav, stdout=slav, stderr=slav, cwd=str(KR),
                         env=miljo(NWP_ATELJE='av', PROV_BARN='60'), start_new_session=True)
    os.close(slav)
    slut = time.time() + 120
    while time.time() < slut and not lever(k, 'BARN.pid'):
        if select.select([master], [], [], 0.1)[0]:
            try:
                os.read(master, 65536)
            except OSError:
                break
    os.close(master)  # terminalen stängs
    try:
        os.killpg(p.pid, signal.SIGHUP)
        rc = p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        rc = 'väntar'
    finally:  # det som lever kvar räknas före provets egen städning
        kvar = lever(k, 'BARN.pid')
        stada_grupp(p)
        doda(k, 'BARN.pid')
    post_ = slutpost(k, korningar('pty-prov')[-1])
    assert rc == post_['slutkod'] == 4 and post_.get('avbruten') == 'SIGHUP' and not kvar, (rc, post_['slutkod'], post_.get('avbruten'), kvar)


@fall('kor.sh: efter SIGKILL stoppar vakten bygget, skriver posten och släpper låsen; ägarens dom kan sparas utan en ny körning, och den senare domen räknas (BÖR 2, KAN 2, KAN 4)')
def _kor_sigkill():
    kor_repo()
    slug = 'kill-prov'
    metod = json.loads(subprocess.run([PY, '-B', '-c', 'import sys, json; sys.path.insert(0, %r); import granska; print(json.dumps(granska.aktuell_metod(%r)))'
                                       % (str(KR / 'kontroller'), slug)], capture_output=True, text=True, cwd=str(KR), env=miljo()).stdout)
    ny = stampel(300)
    k, h = bygge(slug, ny, rot=KR, metod=metod)  # ett godkänt bygge med sin post
    rc, _, fel_ = korslut_(k, ny, rot=KR, env=miljo())
    assert rc == 0, (rc, fel_[-300:])
    agardom(k, 'c' * 12, namn='Nej')  # en äldre dom över ett annat bygge: DOM.json finns och låses
    p, logg = kor_bakgrund(slug, ('BARN.pid', 'BARNBARN.pid'), NWP_ATELJE='av', PROV_BARN='60', PROV_BARNBARN='1')
    start = re.search(r'startad (\d{8}T\d{6}Z)', logg.read_text())
    try:
        os.kill(p.pid, signal.SIGKILL)
        p.wait(timeout=30)
        slut = time.time() + 60
        while time.time() < slut and LAS.exists():
            time.sleep(0.2)
    finally:  # det som lever kvar räknas före provets egen städning
        kvar = [x for x in ('BARN.pid', 'BARNBARN.pid') if lever(k, x)]
        stada_grupp(p)
        doda(k, 'BARN.pid', 'BARNBARN.pid')
    assert start, logg.read_text()[-300:]
    lasen = (LAS.exists(), flaggor(KR / 'kunder'), flaggor(k / 'DOM.json'))
    try:  # dashboardens Din dom, som den skriver: utan en ny körning
        d = json.loads((k / 'DOM.json').read_text())
        d['domar'].append({'tid': '2026-10-07T12:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}})
        (k / 'DOM.json').write_text(json.dumps(d))
        sparad = True
    except OSError as e:
        sparad = str(e)
    post_ = slutpost(k, start.group(1)) if (k / 'korningar' / start.group(1) / 'SLUT.json').is_file() else {}
    assert not kvar and lasen == (False, '-', '-') and sparad is True, ('processer eller lås kvar efter SIGKILL', kvar, lasen, sparad)
    assert post_.get('slutkod') == 4 and post_.get('avbruten') == korslut.AVBROTT_KORSH and 'korvakt' in post_.get('forfattare', ''), post_.get('slutkod')
    _, vt = visa(k, rot=KR, env=miljo())
    assert rad(vt, 'ägaren godkänner:').startswith('ägaren godkänner: ja') and rad(vt, 'klart för leverans:') == 'klart för leverans: ja — inom omfattningen', (
        'ägarens senare dom räknas inte efter körningen som dödades', rad(vt, 'ägaren godkänner:'), rad(vt, 'klart för leverans:'))
    rc2, ut2, _ = kor(slug, NWP_ATELJE='av')
    assert 'Förra körningen' not in ut2, ut2[-400:]


@fall('Codex: planterad slutpost följd av SIGKILL blir obestyrkt bevis, aldrig körningens giltiga post')
def _codex_planterad_post():
    kor_repo()
    slug = 'prov-planterad-post'
    fake = FALSK / 'claude'
    fore = fake.read_text()
    fake.write_text('''#!/bin/sh
exec .venv/bin/python -B - <<'PY'
import json, os, signal, time
from pathlib import Path
k = Path('kunder') / os.environ['NWP_SLUG']
p = k / 'korningar' / os.environ['NWP_KORNING'] / 'SLUT.json'
p.write_text(json.dumps({'markor': 'syntetisk-obestyrkt', 'slutkod': 0}))
os.kill(int(Path('kunder/.bygge-pid').read_text()), signal.SIGKILL)
time.sleep(30)
PY
''')
    try:
        p, logg = kor_bakgrund(slug, ('finns-inte',), NWP_ATELJE='av')
        p.wait(timeout=40)
        slut = time.monotonic() + 60
        while LAS.exists() and time.monotonic() < slut:
            time.sleep(.1)
        d = KR / 'kunder' / slug / 'korningar' / korningar_alla(slug)[-1]
        post = json.loads((d / 'SLUT.json').read_text())
        assert post.get('slutkod') == 3 and 'markor' not in post, post
        gamla = [json.loads(f.read_text()) for f in d.glob('SLUT-obestyrkt-*.json')]
        assert any(x.get('markor') == 'syntetisk-obestyrkt' for x in gamla), gamla
        assert not LAS.exists()
    finally:
        fake.write_text(fore)


@fall('Codex: en bekräftad färdig slutpost bevaras när kor.sh dör efter publiceringen')
def _codex_fardig_post():
    kor_repo()
    slug = 'prov-bekraftad-post'
    skript = KR / 'kontroller/backlog_commit.py'
    fore = skript.read_text()
    skript.write_text('''import os, signal, sys
from pathlib import Path
k = Path('kunder') / sys.argv[1]
p = k / 'korningar' / sys.argv[2] / 'SLUT.json'
(k / 'BEKRAFTAD.json').write_bytes(p.read_bytes())
os.kill(int(Path('kunder/.bygge-pid').read_text()), signal.SIGKILL)
''')
    try:
        p, logg = kor_bakgrund(slug, ('BEKRAFTAD.json',), NWP_ATELJE='av', PROV_BYGG='syntetiskt')
        p.wait(timeout=40)
        slut = time.monotonic() + 60
        while LAS.exists() and time.monotonic() < slut:
            time.sleep(.1)
        k = KR / 'kunder' / slug
        post = k / 'korningar' / korningar_alla(slug)[-1] / 'SLUT.json'
        assert post.read_bytes() == (k / 'BEKRAFTAD.json').read_bytes()
        assert json.loads(post.read_text())['slutkod'] == 1
        assert not LAS.exists()
    finally:
        skript.write_text(fore)


@fall('Codex: C1-protokoll och beläggbilaga skyddas också när de inte finns vid starten')
def _codex_c1_skydd():
    kor_repo()
    fake = FALSK / 'claude'
    fore = fake.read_text()
    fake.write_text('''#!/bin/sh
exec .venv/bin/python -B - <<'PY'
import os
from pathlib import Path
slug = os.environ['NWP_SLUG']
p = Path('kunder') / slug / 'atelje/korningar/prov/SLUT.json' if os.environ['PROV_TYP'].startswith('protokoll') else Path('underlag') / slug / 'DESIGNDOMAR-belagg.jsonl'
p.parent.mkdir(parents=True, exist_ok=True)
if os.environ['PROV_TYP'] == 'belagg-lank':
    mal = p.with_name('syntetiskt.jsonl')
    mal.write_text('{"syntetiskt": true}')
    p.symlink_to(mal.name)
elif os.environ['PROV_TYP'] == 'belagg-katalog':
    p.mkdir()
else:
    p.write_text('{"syntetiskt": true}')
PY
''')
    try:
        for typ_ in ('protokoll', 'protokoll-andra', 'belagg', 'belagg-lank', 'belagg-katalog'):
            if typ_ == 'protokoll-andra':
                skriv(KR / 'kunder' / ('prov-c1-' + typ_) / 'atelje/korningar/prov/SLUT.json', {'syntetiskt': 'tidigare'})
            rc, ut, fel = kor('prov-c1-' + typ_, NWP_ATELJE='av', PROV_TYP=typ_)
            assert rc == 3, (typ_, rc, ut[-500:], fel[-200:])
    finally:
        fake.write_text(fore)


@fall('Codex: samtidiga byggstarter reserverar atomiskt, och bara en når START.json')
def _codex_startlas():
    kor_repo()
    skript = KR / 'kor.sh'
    fore = skript.read_text()
    # Gör fönstret mellan den gamla PID-kontrollen och skrivningen deterministiskt synligt i den egna kopian.
    punkt = 'chflags nouchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || true   # kvarlämnad flagga'
    assert punkt in fore
    skript.write_text(fore.replace(punkt, 'sleep 0.4\n' + punkt, 1))
    processer = []
    try:
        for i in range(3):
            slug = 'prov-samtidig-%d' % i
            (KR / 'kunder' / slug).mkdir(parents=True, exist_ok=True)
            (KR / 'underlag' / slug).mkdir(parents=True, exist_ok=True)
        for i in range(3):
            processer.append(subprocess.Popen(['bash', str(skript), 'prov-samtidig-%d' % i, 'Syntetisk verksamhet'],
                                             cwd=KR, env=miljo(NWP_ATELJE='av', PROV_SOV='3'),
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True))
        utfall_ = [p.communicate(timeout=45) for p in processer]
        starter = [f for i in range(3) for f in (KR / 'kunder' / ('prov-samtidig-%d' % i) / 'korningar').glob('*/START.json')]
        assert len(starter) == 1 and sorted(p.returncode for p in processer) == [1, 2, 2], (len(starter), [p.returncode for p in processer], utfall_)
    finally:
        for p in processer:
            if p.poll() is None:
                stada_grupp(p)
                p.wait(timeout=30)
        skript.write_text(fore)


@fall('Codex: en återanvänd orelaterad PID är status, inte ett aktivt bygglås')
def _codex_ateranvand_pid():
    kor_repo()
    LAS.parent.mkdir(parents=True, exist_ok=True)
    LAS.write_text(str(os.getpid()))
    try:
        rc, ut, fel = kor('prov-gammal-pid', NWP_ATELJE='av')
        assert rc == 1 and korningar_alla('prov-gammal-pid'), (rc, ut[-500:], fel[-300:])
        os.kill(os.getpid(), 0)  # inget stopp skickas till den orelaterade processen
    finally:
        if LAS.exists():
            LAS.unlink()


@fall('Codex: ett relativt äldre kor.sh hör till sin egen utcheckning')
def _codex_aldre_cwd():
    kor_repo()
    annan = TMP / 'aldre-utcheckning'
    (annan / 'kunder').mkdir(parents=True, exist_ok=True)
    skriv(annan / 'kor.sh', '#!/bin/bash\nsleep 30 &\nwait\nexit 0\n')
    p = subprocess.Popen(['bash', './kor.sh'], cwd=annan, start_new_session=True)
    try:
        time.sleep(.1)
        LAS.parent.mkdir(parents=True, exist_ok=True)
        LAS.write_text(str(p.pid))
        (annan / 'kunder/.bygge-pid').write_text(str(p.pid))
        args = [str(KR / '.venv/bin/python'), '-B', str(KR / 'kontroller/bygglas.py'), '--aldre']
        fel_rot = subprocess.run(args + [str(KR)], env=miljo(), capture_output=True, text=True, timeout=15)
        ratt_rot = subprocess.run(args + [str(annan)], env=miljo(), capture_output=True, text=True, timeout=15)
        assert fel_rot.returncode == 1 and ratt_rot.returncode == 0, (fel_rot.returncode, fel_rot.stdout, ratt_rot.returncode, ratt_rot.stdout)
    finally:
        stada_grupp(p)
        p.wait(timeout=10)
        if LAS.exists():
            LAS.unlink()


@fall('Codex: vaktens root måste stämma exakt och oläsbar PID-status nekas')
def _codex_aldre_status():
    kor_repo()
    annan = KR.with_name(KR.name + '-annat')
    annan.mkdir(exist_ok=True)
    p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', str(annan / 'kontroller/korvakt.py'), '--root', str(annan)], cwd=annan)
    try:
        LAS.parent.mkdir(parents=True, exist_ok=True)
        LAS.write_text(str(p.pid))
        args = [str(KR / '.venv/bin/python'), '-B', str(KR / 'kontroller/bygglas.py'), '--aldre', str(KR)]
        annan_rot = subprocess.run(args, env=miljo(), capture_output=True, text=True, timeout=15)
        assert annan_rot.returncode == 1, (annan_rot.returncode, annan_rot.stdout)
        LAS.write_bytes(b'\xff\xfe')
        olasbar = subprocess.run(args, env=miljo(), capture_output=True, text=True, timeout=15)
        assert olasbar.returncode == 0 and 'väntar' in olasbar.stdout, (olasbar.returncode, olasbar.stdout)
    finally:
        p.terminate()
        p.wait(timeout=10)
        if LAS.exists():
            LAS.unlink()


@fall('kor.sh: en körning utan post sägs som avbruten när kor.sh och vakten dödats, och som en post som inte kunde skrivas när korslut föll (KAN 6); en dom som tillkom under den avbrutna körningen räknas inte i nästa (KAN 4, BÖR 1)')
def _kor_utan_post():
    kor_repo()
    k = KR / 'kunder' / 'utan-post'
    agardom(k, dist12('bygget'), namn='Nej')  # ägarens dom före körningen; bygget lägger till ett ja och dödar sedan kor.sh och vakten
    p, logg = kor_bakgrund('utan-post', ('BARN.pid',), NWP_ATELJE='av', PROV_BYGG='bygget', PROV_DOM_SKRIPT='lagg_till', PROV_BARN='60')
    start = re.search(r'startad (\d{8}T\d{6}Z)', logg.read_text())
    assert start, logg.read_text()[-300:]
    vakt = subprocess.run(['pgrep', '-f', 'korvakt.py.*%s' % start.group(1)], capture_output=True, text=True).stdout.split()
    try:
        for pid in vakt:
            os.kill(int(pid), signal.SIGKILL)
        os.kill(p.pid, signal.SIGKILL)
        p.wait(timeout=30)
    finally:
        stada_grupp(p)
        doda(k, 'BARN.pid')
        subprocess.run(['chflags', 'nouchg', str(KR / 'kunder'), str(KR / 'underlag')], capture_output=True)
    _, vt = visa(k, rot=KR, env=miljo())
    avbruten = rad(vt, 'Utan slutpost:')
    assert ('körningen %s' % start.group(1)) in avbruten and 'avbröts utan slutpost' in avbruten and 'vakten' in avbruten, (vakt, vt[-500:])
    # nästa körning räknar ägarens dom från före den avbrutna körningen, aldrig domen som tillkom under den
    rc, ut, _ = kor('utan-post', NWP_ATELJE='av', PROV_BYGG='bygget')
    ag = slutpost(k, korningar('utan-post')[-1])['tillstand']['agaren_godkanner']
    assert len(json.loads((k / 'DOM.json').read_text())['domar']) == 2 and ag['varde'] is False and start.group(1) in ag.get('text', ''), (rc, ag)
    # korslut föll: SLUT.json är en katalog som bygget skapade
    rc, ut, _ = kor('utan-post', NWP_ATELJE='av', PROV_KATALOG_POST='1')
    uteblev = korningar_alla('utan-post')[-1]
    nasta = subprocess.run([PY, '-B', str(KR / 'kontroller' / 'korslut.py'), '--avbrutna', str(k), 'ingen'], capture_output=True, text=True, env=miljo()).stdout
    rad_ = next((r for r in nasta.split('\n') if uteblev in r), '')
    assert rc == 3 and (k / 'korningar' / uteblev / 'UTEBLEV.json').is_file() and 'posten kunde inte skrivas' in rad_ and 'avbröts' not in rad_, (rc, nasta)


@fall('kor.sh: ett kommando som faller under set -e före bygget, eller en trasig fil som läses in, ger en kort post och slutkod 2 (GR-20261007-r101-om2, KAN 5)')
def _kor_set_e():
    kor_repo()
    k = KR / 'kunder' / 'sete-prov'
    skriv(k / 'prov', 'en fil där katalogen prov/ ska ligga\n')
    rc, ut, _ = kor('sete-prov', NWP_ATELJE='av')
    (k / 'prov').unlink()
    post_ = slutpost(k, korningar('sete-prov')[-1]) if korningar('sete-prov') else {}
    assert rc == 2 and post_.get('slutkod') == 2 and str(post_.get('skal', '')).startswith('kor.sh föll före bygget:') and 'prov' in post_.get('skal', ''), (rc, post_.get('skal'), ut[-300:])
    assert korslut.text(post_) in ut, ut[-400:]
    rc2, ut2, _ = kor('sete-prov', NWP_ATELJE='av')
    assert rc2 == 1 and 'Förra körningen' not in ut2, (rc2, ut2[-300:])
    # En otillåten MCP-konfiguration avbryter argumentberedningen: kor.sh stannar med en post.
    # Referos nyckelfil parsas numera som data av byggmcp/atelje, aldrig som skalkod.
    hem = TMP / 'hem-sete'
    skriv(hem / 'okand-mcp.json', '{"mcpServers": {}}\n')
    rc3, ut3, _ = kor('sete-prov', NWP_ATELJE='av', HOME=str(hem), NWP_MCP_CONFIG=str(hem / 'okand-mcp.json'))
    post3 = slutpost(k, korningar('sete-prov')[-1])
    assert rc3 == 2 and post3['slutkod'] == 2 and 'MCP-konfiguration' in str(post3.get('skal', '')), (rc3, post3.get('skal'), ut3[-300:])


@fall('kor.sh: en signal till gruppen i avslutet avbryter varken avslutet eller dess barn (KAN 8: N22)')
def _kor_avslutet():
    kor_repo()
    k = KR / 'kunder' / 'avslut-prov'
    bc = KR / 'kontroller' / 'backlog_commit.py'
    orig = bc.read_bytes()
    markor = TMP / 'avslut-prov.markor'
    bc.write_text('import sys, time\nfrom pathlib import Path\nm = Path(%r)\nm.write_text("start")\ntime.sleep(3)\nm.write_text("klar")\n' % str(markor))
    try:
        p, logg = kor_bakgrund('avslut-prov', (), NWP_ATELJE='av', PROV_BYGG='bygget')
        slut = time.time() + 120
        while time.time() < slut and not (markor.is_file() and markor.read_text() == 'start'):
            time.sleep(0.1)
        try:
            os.killpg(p.pid, signal.SIGTERM)
            rc = p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            rc = 'väntar'
        finally:
            stada_grupp(p)
    finally:
        bc.write_bytes(orig)
    post_ = slutpost(k, korningar('avslut-prov')[-1])
    assert rc == post_['slutkod'] == 1 and markor.read_text() == 'klar' and not post_.get('avbruten'), (rc, post_['slutkod'], markor.read_text())


@fall('korslut utan kor.sh:s minne, och med en process ur bygget kvar: ägarens dom är ej belagd (BÖR 1)')
def _minnet():
    ny = stampel(120)
    k, h = bygge('ks-minne', ny)
    agardom(k, h[:12])
    rc, ut, _ = korslut_(k, ny, med_minne=False)
    ag = slutpost(k, ny)['tillstand']['agaren_godkanner']
    assert rc == 0 and ag['varde'] is None and 'hashlistorna prövades inte' in ag['text'], ag
    rc, ut, _ = korslut_(k, ny, NWP_PROCESSER=json.dumps({'stoppade': [], 'kvar': [{'pid': 1234, 'namn': 'demon'}]}))
    post_ = slutpost(k, ny)
    assert post_['tillstand']['agaren_godkanner']['varde'] is None and any('demon (pid 1234' in b for b in post_['brister']), post_['brister']
    rc, ut, _ = korslut_(k, ny)
    assert slutpost(k, ny)['tillstand']['agaren_godkanner']['varde'] is True, 'ägarens dom räknas med kor.sh:s minne och inga processer kvar'


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
            'ej_bedomt': [], 'sammanfattning': '', 'prototypjamforelse': {'status': 'ingen_prototyp', 'jamforda': [], 'ej_bedomt': [], 'skal': ''}}
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
