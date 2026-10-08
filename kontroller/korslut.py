#!/usr/bin/env python3
"""korslut.py — kor.sh:s avslut: sammanfattar provet, stoppvakten och granskningen, jämför de skyddade filernas
hashlistor före och efter körningen, sätter slutkoden (revisionen 2026-10-03, F10 och F11) och skriver körningens
slutpost (ägarens uppdrag 2026-10-07, punkt 4 och 5; granskningen av r101).

    .venv/bin/python kontroller/korslut.py <kunder/slug> <claude-kod> <hashlista-fore> <hashlista-efter> <korning>
    .venv/bin/python kontroller/korslut.py --stopp <kunder/slug> <korning> <skäl>   # kor.sh stannade före bygget
    .venv/bin/python kontroller/korslut.py --avbrutna <kunder/slug> <korning>       # tidigare körningar utan slutpost
    .venv/bin/python kontroller/korslut.py --visa <kunder/slug> [<korning>]         # posten prövad mot läget nu

Slutkod: 0 provet grönt för just det bygge som ligger i dist/, RAPPORT.md skriven i körningen (samma sha256 som
stoppvakten band och släppte), stoppvakten själv släppte med gröna kontroller och godkänd granskning, och granskningen
gäller samma bygge och samma metod som nu · 1 avslutat utan det (också när en äldre godkänd granskningsfil ligger kvar;
omgång tre, F11) · 3 mekaniken (provet, kriterierna, mallen, krokarna, kor.sh, dashboarden) eller gränsen (en post
tillkom eller försvann direkt under kunder/ eller underlag/, eller flaggan uchg lyftes; kor.sh:s grans(), Codex
2026-10-04 F1), ägarens domlogg eller dom (DOM.json), eller körningarnas protokoll (kunder/<slug>/korningar/ och
rapporter/) ändrades under körningen · 4 claude avslutade med annan kod än 0, också när körningen avbröts med en signal
· 5 slutposten uteblev (gick inte att bygga eller skriva) för ett bygge som annars fått 0 eller 1; backlog_commit
publicerar inget · 6 bygget stannade utan sajt (ateljén förkastade alla riktningar, skaparen lämnade grundidén, eller
ägaren dömde startsidan efter körningen).
Texterna (kunskap/, LARDOMAR.md, skills) skrivs också av kirurgens intag och ägarens domar i dashboarden medan ett
bygge pågår; ändringar där ger bara en varning. Hela fillistan klassificeras; bara utskriften kapas.

Slutposten kunder/<slug>/korningar/<körning>/SLUT.json binder ihop körningen (NWP_KORNING), bygget (dist_sha256),
metoden (granskningens metod_sha, modell, effort, antal granskare och originalitetsläge; byggets inställningar; repots
commit), den godkända startsidan (kandidat, version och VINNARE.json:s sha256), de tekniska kontrollerna,
designgranskningen och vem som gjorde den, ägarens beslut, slutkoden, bristerna, nästa steg (atgarder) och länkarna till
rapporter och bevis (underlag; provets och stoppvaktens besked kopieras till postens katalog, eftersom nästa körning
skriver över dem). Rapporthuvudets fält (README.md, Var information finns) står överst i posten, så att den läses som
ett huvud. Fem tillstånd hålls isär: sessionen avslutad normalt, tekniskt godkänt, designgranskaren godkänner, ägaren
godkänner och klart för leverans inom angiven omfattning. Terminalens besked skrivs ur posten (text).
- Utan körning skrivs ingen post. En ny post ersätter de tidigare (rapportstatus ersatt, ersatt_av) bara när den gäller
  ett annat bygge eller en annan metod; en kort post från en start som stannade före bygget ersätter ingen.
- kor.sh håller hashlistornas sha256, och sha256 för DOM.json när den låstes, i minnet och ger dem hit
  (NWP_SKYDDAT_SHA256, NWP_DOM_START_SHA256), tillsammans med vaktens besked om byggets processer (NWP_PROCESSER,
  kontroller/korvakt.py). En hashlista som ändrats under körningen är slutkod 3 (granskningen GR-20261007-r101-om, BÖR 1).
- Ägarens dom räknas bara när DOM.json är oförändrad sedan den låstes, enligt kor.sh:s minne och hashlistan efter
  körningen, och när vakten stoppat alla byggets processer. Ändrades den räknas domarna i kopian från starten
  (korningar/<körning>/DOM-START.json, prövad mot sha256 ur minnet), aldrig de som tillkom (KAN 3). Avsändaren är annars
  ej belagd. Efter körningen räknas bara domar som ingen körning kan ha skrivit (protokollens ej_belagda).
- aktuell() och --visa prövar posten mot läget nu: ägarens dom, dist/, granskningens metod och startsidans godkännande.
  Har något ändrats står postens godkännanden som historik och klart för leverans är nej. En körning som startade
  (START.json) men saknar slutpost och inte pågår sägs: avbruten (varken kor.sh eller vakten skrev någon post) eller
  med en post som inte kunde skrivas (UTEBLEV.json, slutkod 5; KAN 6).
- Beskedet skrivs också när terminalen stängts: slutkoden är postens (KAN 1).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skapande  # noqa: E402  domloggens avsändare (startsidan) och konstanten EJ_BELAGD

ROOT = Path(__file__).resolve().parents[1]
MEKANIK = ('kontroller/', 'kritik/', 'mall/', '.claude/hooks/', '.claude/settings', 'kor.sh', 'dashboard/', 'dashboard.sh',
           'CLAUDE.md', 'BESLUT.md', '.gitignore', 'syskon:', 'flagga:', 'protokoll:')
EJ = 'ej angivet'  # ett saknat värde gissas aldrig (README.md, rapporthuvudet)
EJ_BELAGD = skapande.EJ_BELAGD  # avsändarna och "ej belagd" har en källa i koden: kontroller/skapande.py (GR-20261007-r106#KAN-7)
SLUTPOST = 'SLUT.json'
START = 'START.json'  # kor.sh skriver den när körningen får sin identitet: en körning utan SLUT.json syns
UTEBLEV = 'UTEBLEV.json'  # en körning vars slutpost inte kunde skrivas (slutkod 5), skild från en avbruten (KAN 6)
DOMFIL = 'DOM.json'
DOMSTART = 'DOM-START.json'  # kor.sh:s kopia av DOM.json när den låstes, i körningens katalog (KAN 3)
AVBROTT_KORSH = 'kor.sh dog utan avslut (SIGKILL eller krasch); vakten stoppade bygget och skrev posten'
DATUM_IDENTITET = '2026-10-07'  # från den dagen bär stoppvaktens besked rapportens identitet
KORNING_ID = re.compile(r'(?<![0-9A-Za-z])(\d{8}T\d{6}Z)(?![0-9A-Za-z])')  # kor.sh: date -u +%Y%m%dT%H%M%SZ
KORNING_NAMN = re.compile(r'[0-9A-Za-z][0-9A-Za-z_-]{0,63}')  # körningen som katalognamn, aldrig en sökväg
TYP = 'slutpost (kor.sh)'
TYP_STOPP = 'slutpost (kor.sh stannade före bygget)'
UPPDRAG = 'helbygget enligt skillen bygg-sajt, startat med kor.sh'
MOMENT = 'helbygget (README.md, kedjan steg 6)'
AGAREN_JA = 'Ja, som den är'  # kärnfrågan namn i dashboardens Din dom (dashboard/server.py, KARNFRAGOR)
TOLKNING = 'tolkning: bara svaret "%s" räknas som godkännande; inte bekräftad av ägaren' % AGAREN_JA
ORD = {True: 'ja', False: 'nej', None: 'ej bedömt'}  # ett tillstånds värde i klartext
TILLSTAND = (('sessionen_avslutad', 'sessionen avslutad normalt'), ('tekniskt_godkant', 'tekniskt godkänt'),
             ('designgranskaren_godkanner', 'designgranskaren godkänner'), ('agaren_godkanner', 'ägaren godkänner'),
             ('klart_for_leverans', 'klart för leverans'))


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las_objekt(p):
    """(objekt, fel) för en JSON-fil som ska vara ett objekt. Saknas filen är båda None. En symlänk, en fil som inte går
    att läsa eller inte är JSON, och ett värde som inte är ett objekt ger (None, skälet): en trasig fil fäller aldrig
    avslutet och tolkas aldrig som tom (granskningen av r101, BÖR 2)."""
    p = Path(p)
    if p.is_symlink():
        return None, '%s är en symlänk' % p.name
    if not p.exists():
        return None, None
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return None, '%s går inte att läsa: %s' % (p.name, str(e)[:120])
    if not isinstance(d, dict):
        return None, '%s är inget objekt (%s)' % (p.name, type(d).__name__)
    return d, None


def las(p):
    """Ett JSON-objekt, eller None när filen saknas, är trasig eller inte är ett objekt."""
    return las_objekt(p)[0]


def sha_fil(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).is_file() else None
    except OSError:
        return None


def hashlista(p):
    """{fil: hash} ur shasum-utdata (hash, två blanksteg, filnamn)."""
    ut = {}
    try:
        for rad in Path(p).read_text(encoding='utf-8', errors='replace').splitlines():
            if '  ' in rad:
                h, _, fil = rad.partition('  ')
                ut[fil.strip()] = h.strip()
    except OSError:
        pass
    return ut


def andrade(fore, efter):
    """Filer vars hash skiljer sig, saknas efteråt eller tillkommit."""
    f, e = hashlista(fore), hashlista(efter)
    return sorted(x for x in set(f) | set(e) if f.get(x) != e.get(x))


# --- rapporten bunden till körningen (ägarens uppdrag 2026-10-07, punkt 5) ---

def rapport_korningar(text):
    """Körningsidentiteterna (kor.sh: date -u +%Y%m%dT%H%M%SZ) i rapportens huvud: raderna mellan de inledande ---
    (README.md, rapporthuvudet), annars de första 40 raderna."""
    rader = (text or '').split('\n')
    huvud = rader[:40]
    if rader and rader[0].strip() == '---':
        slut = next((i for i, r in enumerate(rader[1:200], 1) if r.strip() == '---'), None)
        if slut:
            huvud = rader[1:slut]
    return sorted(set(KORNING_ID.findall('\n'.join(huvud))))


def rapport_identitet(rapport, korning):
    """Är RAPPORT.md skriven i den här körningen? Bara när rapportens huvud bär körningens identitet (raden korning: i
    rapporthuvudet; uppdraget från kor.sh och bygg-sajt steg 7). Filtiden räcker inte: en äldre rapport som kopieras
    tillbaka får en ny filtid (granskningen av r101, BÖR 5). En rapport som bär en annan körnings identitet gäller den
    körningen, och utan körning (NWP_KORNING) går ingen rapport att binda. Stoppvakten sparar sha256 och körning för en
    bunden rapport, och korslut kräver samma sha256 (rapport_giltig). Ger {'bunden', 'skal', 'sha256', 'satt',
    'korningar'}."""
    rapport = Path(rapport)
    ut = {'bunden': False, 'sha256': None, 'satt': None, 'korningar': []}
    if rapport.is_symlink():
        return dict(ut, skal='är en symlänk')
    try:
        data = rapport.read_bytes() if rapport.is_file() else None
    except OSError:
        data = None
    if data is None or len(data) <= 300:
        return dict(ut, skal='saknas eller är nästan tom')
    ut.update(sha256=hashlib.sha256(data).hexdigest(), korningar=rapport_korningar(data.decode('utf-8', errors='replace')))
    if not korning:
        return dict(ut, skal='kan inte bindas: körningens identitet (NWP_KORNING) saknas')
    if korning in ut['korningar']:
        return dict(ut, bunden=True, satt='identitet', skal='bär körningens identitet %s' % korning)
    if ut['korningar']:
        return dict(ut, skal='gäller körning %s, inte %s' % (', '.join(ut['korningar']), korning))
    return dict(ut, skal='saknar körningens identitet i huvudet (raden korning: %s)' % korning)


def rapport_giltig(k, v, korning=None):
    """(ok, skäl): RAPPORT.md är den rapport som stoppvakten band till körningen och släppte (samma sha256, samma körning).
    Skälet säger vad som gäller vilken körning: stoppvaktens besked eller rapporten (granskningen av r101, BÖR 6)."""
    rapport = Path(k) / 'RAPPORT.md'
    if rapport.is_symlink():
        return False, 'RAPPORT.md är en symlänk'
    if not rapport.is_file():
        return False, 'RAPPORT.md saknas'
    v = v if isinstance(v, dict) else {}
    if not v:
        return False, 'ingen rapport bands i körningen: stoppvaktens besked (prov/STOPPVAKT.json) saknas'
    if korning and v.get('korning') != korning:
        return False, 'stoppvaktens besked gäller en annan körning (%s, inte %s); ingen rapport bands i den här körningen' % (
            v.get('korning') or EJ, korning)
    if not v.get('rapport_sha256'):
        if 'rapport' not in v:
            return False, 'stoppvaktens besked är från före %s: rapportens identitet sparades inte då' % DATUM_IDENTITET
        try:
            ids = rapport_korningar(rapport.read_text(encoding='utf-8', errors='replace'))
        except OSError:
            ids = []
        if korning and korning in ids:
            return False, 'RAPPORT.md bär körningens identitet, men stoppvakten band den inte (%s)' % v.get('rapport')
        if ids:
            return False, 'RAPPORT.md gäller körning %s, inte %s (stoppvakten: %s)' % (', '.join(ids), korning or 'den här körningen', v.get('rapport'))
        return False, 'RAPPORT.md saknar identitet: stoppvakten band ingen rapport till körningen (%s)' % v.get('rapport')
    if korning and v.get('rapport_korning') != korning:
        return False, 'stoppvakten band rapporten till körning %s, inte %s' % (v.get('rapport_korning') or EJ, korning)
    sha = sha_fil(rapport)
    if sha != v['rapport_sha256']:
        return False, 'RAPPORT.md är inte den rapport som stoppvakten band och släppte (sha256 %s, nu %s)' % (str(v['rapport_sha256'])[:12], str(sha)[:12])
    return True, 'skriven i körningen %s, bunden genom identiteten i huvudet, sha256 %s' % (v.get('rapport_korning') or EJ, sha[:12])


def ar_godkant(k, s, v, g, korning=None):
    """Godkänt bara när allt gäller det bygge som ligger i dist/ nu: provet grönt med samma dist-hash som dist/, rapporten
    skriven i körningen (samma sha256 som stoppvakten band och släppte), stoppvakten släppte med gröna kontroller och
    godkänd granskning (inte vid sitt tak), och granskningen är godkänd för samma dist-hash och samma metod som nu (omgång
    tre, F11)."""
    s = s if isinstance(s, dict) else None
    v = v if isinstance(v, dict) else None
    g = g if isinstance(g, dict) else None
    if not (s and s.get('ok')):
        return False, 'provet är inte grönt'
    ok_r, skal_r = rapport_giltig(k, v, korning)
    if not ok_r:
        return False, skal_r
    dist = k / 'sajt' / 'dist'
    try:
        import prova
        nu_hash = prova.dist_hash(dist) if (dist / 'index.html').is_file() else None
    except Exception as e:  # noqa: BLE001 — kan hashen inte räknas är bygget inte verifierat
        return False, 'kunde inte hasha dist/: %s' % e
    if not nu_hash or s.get('dist_sha256') != nu_hash:
        return False, 'provet gäller inte det bygge som ligger i dist/ nu'
    if not (v and v.get('slapp') and str(v.get('skal') or '').startswith('kontrollerna gröna')):
        return False, 'stoppvakten släppte inte med gröna kontroller och godkänd granskning (%s)' % ((v or {}).get('skal') or 'ingen STOPPVAKT.json')
    if korning and v.get('korning') != korning:
        return False, 'stoppvaktens besked gäller en annan körning (%s, inte %s)' % (v.get('korning'), korning)
    if v.get('dist_sha256') != nu_hash:
        return False, 'stoppvaktens besked gäller ett annat bygge än det i dist/'
    if not (g and g.get('godkand')):
        return False, 'ingen godkänd granskning'
    if g.get('dist_sha256') != nu_hash:
        return False, 'granskningen gäller ett annat bygge än det i dist/'
    try:
        import granska
        if not granska.samma_metod(g, granska.aktuell_metod(k.name)):  # samma jämförelse som granskningen själv gör
            return False, 'granskningen gjordes med en annan metod (underlag, modell, effort, antal eller originalitetsläge) än den som gäller nu'
    except Exception as e:  # noqa: BLE001
        return False, 'kunde inte jämföra granskningsmetoden: %s' % e
    return True, ''


def vald_granskning(k, korning):
    """(dom, slutlig dist, senaste giltiga dom oavsett bygge och metod, fel): domen för det slutliga bygget härledd ur
    giltiga omgångar med hela identiteten (körning, dist, aktuell metod; kontroller/granska.py valj_sammanfattning), aldrig
    ur rotfilen när omgångar finns. Kan omgångarna inte läsas eller valideras är det ett fel som nekar godkännande; rotfilen
    är reserv bara när inga omgångar finns (Codex R38/R39, F11)."""
    dist = k / 'sajt' / 'dist'
    try:
        import prova
        nu_hash = prova.dist_hash(dist) if (dist / 'index.html').is_file() else None
    except Exception:  # noqa: BLE001
        nu_hash = None
    gdir = k / 'granskning'
    try:
        import granska
        finns = gdir.is_dir() and bool(granska.rundor(gdir))
    except Exception as e:  # noqa: BLE001
        return None, nu_hash, None, 'omgångarna kunde inte listas: %s' % e
    if not finns:
        rot, fel = las_objekt(gdir / 'GRANSKNING.json')  # inga omgångar (manuellt underlag): rotfilen är det enda som finns
        return rot, nu_hash, None, ('rotfilen %s' % fel) if fel else None
    try:
        metod = granska.aktuell_metod(k.name)
        val = granska.valj_sammanfattning(gdir, korning, nu_hash, metod, strikt=True)  # en overifierbar omgång i körningen nekar (Codex R40)
        alla = granska.valj_sammanfattning(gdir, None, None)
    except Exception as e:  # noqa: BLE001
        return None, nu_hash, None, 'omgångarna kunde inte läsas eller valideras: %s' % e
    g = val[1] if val else None
    if g and not (g.get('dist_sha256') == nu_hash and granska.samma_metod(g, metod)):
        g_hel = None  # ingen giltig omgång med hela identiteten: visas som senaste, men godkänner inget
    else:
        g_hel = g
    return g_hel, nu_hash, (val[1] if val else None) if g_hel is None else (alla[1] if alla and alla[0] != val[0] else None), None


# --- slutposten (ägarens uppdrag 2026-10-07, punkt 4) ---

def _rel(k, *delar):
    return '/'.join(('kunder', Path(k).name) + tuple(delar))


def _kort(h, n=12):
    return str(h)[:n] if h else EJ


def _metod_sha(post):
    return (((post or {}).get('metod') or {}).get('granskning') or {}).get('metod_sha')


def _lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError):
        return False


def _pagar(pid):
    """Kör kor.sh fortfarande med den här pid:en? En återanvänd pid för en annan process räknas inte; svarar ps inte
    antas att den pågår (hellre tyst än en felaktig uppgift om avbrott)."""
    if not _lever(pid):
        return False
    try:
        cmd = subprocess.run(['ps', '-o', 'command=', '-p', str(int(pid))], capture_output=True, text=True, timeout=10,
                             env=dict(os.environ, LC_ALL='C')).stdout
    except Exception:  # noqa: BLE001
        return True
    return not cmd.strip() or 'kor.sh' in cmd


def repo_identitet():
    """Repots commit och antalet ändrade spårade filer (git i repots rot), eller None när git inte svarar."""
    try:
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=20)
        if head.returncode != 0 or not head.stdout.strip():
            return None
        st = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no'], capture_output=True, text=True, timeout=60)
        return {'commit': head.stdout.strip(), 'andrade_filer': len([r for r in st.stdout.splitlines() if r.strip()]) if st.returncode == 0 else None}
    except (OSError, subprocess.SubprocessError):
        return None


def sessionen(k, korning, rc, avbruten=None):
    """Claude-sessionens slut ur körningens logg (kunder/<slug>/korning-<körning>.jsonl): resultat, turer, tid, modell.
    Värdet är ja när sessionen avslutades normalt (kod 0)."""
    try:
        kod = int(rc)
    except (TypeError, ValueError):
        kod = rc
    if isinstance(kod, int):
        text = 'claude avslutade med kod %s%s%s' % (kod, '' if kod == 0 else ' (föll)', ', körningen avbröts med %s' % avbruten if avbruten else '')
    else:  # vakten gjorde avslutet: claude var kor.sh:s barn, och dess slutkod gick förlorad med kor.sh
        text = 'claudes slutkod är okänd%s' % (', körningen avbröts: %s' % avbruten if avbruten else '')
    ut = {'varde': kod == 0 and not avbruten, 'kod': kod, 'text': text}
    if avbruten:
        ut['avbruten'] = avbruten
    logg = Path(k) / ('korning-%s.jsonl' % korning) if korning else None
    if logg and logg.is_file() and not logg.is_symlink():
        slut, init = None, None
        try:
            with open(logg, encoding='utf-8', errors='replace') as f:
                for rad in f:
                    try:
                        d = json.loads(rad)
                    except ValueError:
                        continue
                    if isinstance(d, dict) and d.get('type') == 'result':
                        slut = d
                    elif isinstance(d, dict) and d.get('type') == 'system' and d.get('subtype') == 'init' and init is None:
                        init = d
        except OSError:
            pass
        ut.update(logg=_rel(k, logg.name), resultat=(slut or {}).get('subtype') or EJ, turer=(slut or {}).get('num_turns'),
                  minuter=round(((slut or {}).get('duration_ms') or 0) / 60000, 1) if slut else None,
                  modell=(init or {}).get('model'), claude_code=(init or {}).get('claude_code_version'))
        if slut:
            ut['text'] += ' (%s, %s turer)' % (ut['resultat'], ut['turer'] if ut['turer'] is not None else '?')
    return ut


# --- ägarens dom (granskningen av r101, B1: bygget får aldrig kunna skriva "ägaren godkänner") ---

def dom_nyckel(d):
    """En doms identitet: sha256 av den kanoniska JSON-formen."""
    return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def agarens_domar(k):
    """(domar, fel) ur kunder/<slug>/DOM.json: domarna som objekt, eller ett fel när filen är trasig."""
    d, fel = las_objekt(Path(k) / DOMFIL)
    if fel:
        return [], fel
    domar = (d or {}).get('domar')
    if d is not None and not isinstance(domar, list):
        return [], '%s: fältet domar är ingen lista' % DOMFIL
    return [x for x in domar or [] if isinstance(x, dict)], None


def agarens_dom(k, dist, ej_belagda=()):
    """Ägarens senaste dom över just det här bygget ur kunder/<slug>/DOM.json (dashboardens Din dom, bunden med bygge_dist
    till byggets dist_sha256). Godkänner betyder svaret "Ja, som den är" på kärnfrågan namn ("Skulle du sätta ditt namn på
    sajten och visa den för verksamheten?"); "Ja, efter små ändringar" är ett ja med villkor och inget godkännande. Det
    är Claudes tolkning av kärnfrågan, inte bekräftad av ägaren (TOLKNING). Domar i ej_belagda (de fanns i en DOM.json som
    ändrades under en körning, så bygget kan ha skrivit dem) räknas aldrig. Utan dom över bygget: ej bedömt."""
    kalla = _rel(k, DOMFIL)
    if not dist:
        return {'varde': None, 'text': 'inget bygge i dist/ att döma', 'kalla': kalla}
    domar, fel = agarens_domar(k)
    if fel:
        return {'varde': None, 'kalla': kalla, 'avsandare': EJ_BELAGD, 'text': 'domen går inte att läsa: %s' % fel}
    ej = set(ej_belagda or ())
    ignorerade = [d for d in domar if dom_nyckel(d) in ej]
    aktuella = [d for d in domar if dom_nyckel(d) not in ej and d.get('bygge_dist') == str(dist)[:12]]
    if not aktuella:
        return {'varde': None, 'kalla': kalla, 'text': 'ägarens dom skrivs i dashboarden (bygget, fliken Din dom) och binds till dist %s%s' % (
            str(dist)[:12], '; %d dom(ar) som fanns i en DOM.json som ändrades under en körning räknas inte (avsändaren ej belagd)' % len(ignorerade)
            if ignorerade else '')}
    d = aktuella[-1]
    namn = (d.get('svar') or {}).get('namn') if isinstance(d.get('svar'), dict) else None
    varde = None if not namn else namn == AGAREN_JA
    villkor = ' (ja med villkor: inget godkännande som den är)' if namn and namn != AGAREN_JA and str(namn).startswith('Ja') else ''
    return {'varde': varde, 'kalla': kalla, 'tid': d.get('tid'), 'avsandare': 'ägaren (dashboardens Din dom)', 'tolkning': TOLKNING,
            'text': 'dom %s, kärnfrågan namn: %s%s; %s' % (d.get('tid') or EJ, namn or 'obesvarad', villkor, TOLKNING)}


def startdomar(k, korning, start_sha):
    """Nycklarna för domarna i DOM.json när kor.sh låste den: ur kopian korningar/<körning>/DOM-START.json, bara när dess
    sha256 är den som kor.sh höll i minnet (start_sha). En tom mängd när DOM.json saknades vid starten ('saknas'); None när
    kopian saknas, är en länk eller inte stämmer, och då är ingen dom i filen belagd (KAN 3)."""
    if not start_sha:
        return None
    if start_sha == 'saknas':
        return set()
    kopia = Path(k) / 'korningar' / str(korning or '') / DOMSTART
    if not korning or kopia.is_symlink() or sha_fil(kopia) != start_sha:
        return None
    d, fel = las_objekt(kopia)
    domar = (d or {}).get('domar')
    return {dom_nyckel(x) for x in domar if isinstance(x, dict)} if not fel and isinstance(domar, list) else set()


def hashlistorna(k, fore, efter):
    """(prövning, mekanik) för kor.sh:s hashlistor. kor.sh håller listornas sha256 i minnet (NWP_SKYDDAT_SHA256, "<före>
    <efter>"): en lista som ändrats under körningen, av ett eget skript i bygget, döljer annars en ändrad DOM.json eller
    mekanik (granskningen GR-20261007-r101-om, BÖR 1). En ändrad eller oskriven lista är ändrad mekanik (slutkod 3). Utan
    värdena (korslut kördes utan kor.sh) är listorna inte prövade, och ägarens dom kan då inte beläggas."""
    k = Path(k)
    v = (os.environ.get('NWP_SKYDDAT_SHA256') or '').split()
    fel = os.environ.get('NWP_EFTER_FEL') or ''
    if len(v) != 2:
        return {'varde': None, 'text': 'ej prövade mot kor.sh:s minne (korslut kördes utan kor.sh)'}, []
    fore_ok, efter_ok = sha_fil(fore) == v[0], sha_fil(efter) == v[1] and not fel
    andrade = ['lista:kunder/%s/prov/%s' % (k.name, Path(fil).name) for fil, ok in ((fore, fore_ok), (efter, sha_fil(efter) == v[1])) if not ok]
    if fel:
        andrade.append('lista:efter körningen (%s)' % fel[:160])
    return {'varde': not andrade, 'fore_ok': fore_ok, 'efter_ok': efter_ok, 'andrade': andrade,
            'text': 'oförändrade sedan kor.sh skrev dem' if not andrade else 'ändrade eller oskrivna under körningen: %s' % ', '.join(andrade)}, andrade


def processer_efter():
    """Vaktens besked om byggets processer när claude avslutats (NWP_PROCESSER, JSON från kontroller/korvakt.py): vilka
    den stoppade och vilka som fanns kvar. En process som lever kvar efter körningen kan skriva DOM.json när låset släpps
    (granskningen GR-20261007-r101-om, BÖR 1, punkt l); utan besked är det inte prövat."""
    try:
        d = json.loads(os.environ.get('NWP_PROCESSER') or 'null')
    except ValueError:
        d = None
    if not isinstance(d, dict):
        return {'varde': None, 'stoppade': [], 'kvar': [], 'text': 'ej prövat: inget besked från vakten om byggets processer'}
    stoppade = [x for x in d.get('stoppade') or [] if isinstance(x, dict)]
    kvar = [x for x in d.get('kvar') or [] if isinstance(x, dict)]
    namn = lambda xs: ', '.join('%s (pid %s%s)' % (x.get('namn'), x.get('pid'), ', %s' % x['signal'] if x.get('signal') else '') for x in xs[:8])  # noqa: E731
    text = ('%d process(er) ur bygget fanns kvar efter SIGKILL: %s' % (len(kvar), namn(kvar)) if kvar else 'ingen process ur bygget kvar') + (
        '; vakten stoppade %d: %s' % (len(stoppade), namn(stoppade)) if stoppade else '')
    return {'varde': not kvar, 'stoppade': stoppade, 'kvar': kvar, 'foljda': d.get('foljda'), 'frist': d.get('frist'), 'text': text}


def tillkomna_efter_avbrutna(k, korning, nycklar, start_sha=None):
    """Domar (nycklar, ur DOM.json när den här körningen startade) som inte fanns när en tidigare körning startade, som
    claude hann starta i men som saknar både slutpost och UTEBLEV.json: den avbröts utan att kor.sh eller vakten skrev
    någon post, så dess bygge kan ha skrivit dem (KAN 4). Domarna vid den körningens start kommer ur dess DOM-START.json;
    saknas kopian och är DOM.json oförändrad sedan dess (START.json:s sha256 = start_sha) har inget tillkommit, annars räknas
    alla som tillkomna. Ger (nycklar, körningarna)."""
    k = Path(k)
    ut, vilka = set(), []
    for a in avbrutna(k, efter=_senaste_post_fore(k, korning) if korning else None, utom=korning):
        if a.get('uteblev') is not None or not a.get('logg'):
            continue
        d = k / 'korningar' / a['korning']
        start = None if a.get('dom_sha256_start') else set()
        if (d / DOMSTART).is_file() and not (d / DOMSTART).is_symlink():
            x, fel = las_objekt(d / DOMSTART)
            if not fel and isinstance((x or {}).get('domar'), list):
                start = {dom_nyckel(y) for y in x['domar'] if isinstance(y, dict)}
        if start is None and start_sha and a.get('dom_sha256_start') == start_sha:
            continue  # DOM.json är oförändrad sedan den körningen startade
        nya = set(nycklar) - (start or set())
        if nya:
            ut |= nya
            vilka.append(a['korning'])
    return ut, vilka


def agaren_vid_slut(k, nu_hash, dom_fore, dom_efter, korning=None, start_sha=None, hinder=()):
    """(tillstånd, protokoll) för ägarens dom när körningen slutar.
    - Starten: sha256 för DOM.json när kor.sh låste den, ur kor.sh:s minne (start_sha, NWP_DOM_START_SHA256; 'saknas' när
      filen saknades), annars ur hashlistan före körningen. Slutet: hashlistan efter, skriven när byggets processer stoppats.
    - Ändrades DOM.json räknas domarna i kopian från starten, aldrig de som tillkom; går kopian inte att lita på räknas
      ingen dom i filen (KAN 3). Går filen inte att pröva mot starten räknas inte heller de som tillkommit.
    - Domar som tillkom efter att en tidigare körning avbröts utan post räknas inte (tillkomna_efter_avbrutna).
    - Domarna som inte räknas står i protokollets ej_belagda och räknas aldrig, inte heller senare.
    - hinder: hashlistorna prövades inte mot kor.sh:s minne, eller byggets processer stoppades inte. Domen är då ej belagd
      i den här posten."""
    k = Path(k)
    nu_ = sha_fil(k / DOMFIL)
    domar, _ = agarens_domar(k)
    start = (None if start_sha == 'saknas' else start_sha) if start_sha else dom_fore
    andrad = start != dom_efter
    kanda = startdomar(k, korning, start_sha) if start_sha else (set() if dom_fore is None else None)
    alla = [dom_nyckel(d) for d in domar]
    tillkomna = [n for n in alla if kanda is None or n not in kanda]
    efter_avbrutna, avbrutna_ = tillkomna_efter_avbrutna(k, korning, [n for n in alla if n not in tillkomna], start)
    proto = {'andrad_under_korningen': andrad, 'provad_mot_start': nu_ == dom_efter, 'sha256_start': start, 'sha256_slut': nu_,
             'start_ur': 'kor.sh:s minne' if start_sha else 'hashlistan före körningen', 'startkopian': None if kanda is None else len(kanda),
             'ej_belagda': [], 'hinder': list(hinder)}
    ej = set()
    skal = []
    if andrad or nu_ != dom_efter:
        ej |= set(tillkomna)
        skal.append('%s %s%s' % (DOMFIL, 'ändrades under körningen' if andrad else 'går inte att pröva mot körningens start',
                                 ', så bygget kan ha skrivit den' if kanda is None else ', så bygget kan ha skrivit %d dom(ar) i den' % len(tillkomna)
                                 if tillkomna else ', men ingen dom tillkom'))
    if efter_avbrutna:
        ej |= efter_avbrutna
        proto['efter_avbrutna'] = avbrutna_
        skal.append('%d dom(ar) tillkom efter att körningen %s startade och avbröts utan slutpost' % (len(efter_avbrutna), ', '.join(avbrutna_)))
    proto['ej_belagda'] = [n for n in alla if n in ej]
    t = agarens_dom(k, nu_hash, ej_belagda_domar(k) | ej)
    # en dom över bygget som inte räknas gör tillståndet ej belagt, när ingen belagd dom finns över samma bygge
    uteslutna = [d for d in domar if dom_nyckel(d) in ej and nu_hash and d.get('bygge_dist') == str(nu_hash)[:12]]
    if hinder or (t.get('varde') is None and (uteslutna or ((andrad or nu_ != dom_efter) and kanda is None))):
        orsak = '; '.join(skal + list(hinder))
        return ({'varde': None, 'avsandare': EJ_BELAGD, 'kalla': _rel(k, DOMFIL),
                 'text': '%s: %s; ägarens domar skrivs bara av dashboarden när inget bygge pågår' % (EJ_BELAGD, orsak)}, proto)
    if skal:
        t = dict(t, text='%s (räknas inte: %s)' % (t.get('text'), '; '.join(skal)))
    return t, proto


def ej_belagda_domar(k):
    """Domar som aldrig räknas, eftersom en körning kan ha skrivit dem, ur alla körningars protokoll: slutposterna och
    UTEBLEV.json (en körning vars post inte kunde skrivas)."""
    ut = set()
    d = Path(k) / 'korningar'
    uteblev = sorted(f for f in d.glob('*/' + UTEBLEV) if f.is_file() and not f.is_symlink() and not f.parent.is_symlink()) \
        if d.is_dir() and not d.is_symlink() else []
    for f in slutposter(k):
        p = las(f) or {}
        ut |= set((((p.get('kontroller') or {}).get('agarens_dom') or {}).get('ej_belagda')) or [])
    for f in uteblev:
        p = las(f) or {}
        ut |= set(((p.get('agarens_dom') or {}).get('ej_belagda')) or [])
    return ut


def leverans(t, slutkod, slug):
    """Klart för leverans inom omfattningen: slutkod 0, tekniskt godkänt, designgranskaren och ägaren godkänner."""
    saknas = [x for x, krav in (('slutkod %s' % slutkod, slutkod == 0),
                                ('inte tekniskt godkänt', t['tekniskt_godkant'].get('varde') is True),
                                ('designgranskaren har inte godkänt bygget', t['designgranskaren_godkanner'].get('varde') is True),
                                ('väntar på ägarens dom' if t['agaren_godkanner'].get('varde') is None else 'ägaren har inte godkänt bygget',
                                 t['agaren_godkanner'].get('varde') is True)) if not krav]
    return {'varde': not saknas, 'text': 'inom omfattningen' if not saknas else '; '.join(saknas),
            'omfattning': 'helbygget i kunder/%s/sajt/, att visa för verksamheten (bygg-sajt steg 7, punkt 13); exporten till '
                          'kundrepo och leveransen (GitHub, Vercel, DNS) ingår inte (README.md, kedjan steg 8 och 9; '
                          'kunskap/lansering.md)' % slug}


def _vinnare(k):
    k = Path(k)
    return k.resolve().parent.parent / 'underlag' / k.name / 'atelje' / 'VINNARE.json'


def startsidan(k):
    """Den godkända startsida bygget utgick från: kandidat och version ur underlag/<slug>/atelje/VINNARE.json (fältet
    godkand), filens sha256 (aktuell() prövar om godkännandet ändrats) och om godkännandet gäller nu
    (skapande.godkand_giltig). På nödvägen (NWP_ATELJE annat än pa) byggde byggaren sitt eget koncept."""
    k = Path(k)
    lage = os.environ.get('NWP_ATELJE') or 'pa'
    if lage != 'pa':
        return {'lage': 'nödvägen (NWP_ATELJE=%s)' % lage, 'text': 'nödvägen utan skapandeflödet: byggarens egen KONCEPT.md och DESIGN.md'}
    rot = k.resolve().parent.parent
    vin = _vinnare(k)
    d, fel = las_objekt(vin)
    ut = {'lage': 'skapandeflödet', 'vinnare': 'underlag/%s/atelje/VINNARE.json' % k.name, 'vinnare_sha256': sha_fil(vin)}
    g = (d or {}).get('godkand')
    if fel or not isinstance(g, dict) or not g.get('tid'):
        return dict(ut, fel=fel, text=('VINNARE.json: %s' % fel) if fel else 'inget godkännande i underlag/%s/atelje/VINNARE.json' % k.name)
    ut.update(godkand=g.get('tid'), av=g.get('av'), kandidat=g.get('kandidat'), version=g.get('version'), sha_index=g.get('sha_index'),
              sha_design=g.get('sha_design'))
    try:
        import skapande
        ok, skal = skapande.godkand_giltig(k.name, underlag=rot / 'underlag', kunder=rot / 'kunder')
        ut['giltig_nu'] = {'varde': bool(ok), 'text': skal}
        # godkännandets avsändare ur domlogg-raden med samma tid (skapande.avsandare; ägarens uppdrag 2026-10-07, punkt 7):
        # ägaren via Codex utan belägg, och en rad som saknas, står som ej belagd
        samma_tid = [(r, p) for r, _s, p in skapande.domlogg(k.name, rot / 'underlag')['domar'] if p.get('beslut') == 'godkand' and p.get('tid') == g.get('tid')]
        # två rader samma sekund (en vidarebefordrad bedömning bredvid ägarens, eller en rad skriven med --tid): ägarens egen
        # rad är godkännandets avsändare, aldrig den sista i filordning (GR-20261007-r106#KAN-6)
        rad = next(((r, p) for r, p in reversed(samma_tid) if skapande.ar_agarens(p)), samma_tid[-1] if samma_tid else None)
        avs = skapande.avsandare(rad[1]) if rad else {'text': '%s (ingen rad i domloggen har godkännandets tid)' % EJ_BELAGD, 'agarens': False}
        ut.update(avsandare=avs['text'], avsandare_agarens=bool(avs['agarens']), domrad=rad[0] if rad else None)
    except Exception as e:  # noqa: BLE001 — prövningen är information, aldrig ett fel i avslutet
        ut['giltig_nu'] = {'varde': None, 'text': 'kunde inte prövas: %s' % str(e)[:160]}
    ut['text'] = 'godkänd startsida %s (%s%s)' % (g.get('tid'), ('kandidat %s, version %s' % (g.get('kandidat'), _kort(g.get('version'))))
                                                 if g.get('kandidat') else 'startsidan sha256 %s' % _kort(g.get('sha_index')),
                                                 '; avsändaren: %s' % ut['avsandare'] if ut.get('avsandare') else '')
    return ut


def foregaende(k, korning):
    """Den senaste tidigare slutposten, som text för rapporthuvudets fält foregaende."""
    tidigare = [f for f in slutposter(k) if f.parent.name < korning]
    if not tidigare:
        return EJ
    p, fel = las_objekt(tidigare[-1])
    return '%s (%s%s)' % ((p or {}).get('id') or tidigare[-1].parent.name, _rel(k, 'korningar', tidigare[-1].parent.name, SLUTPOST),
                          '; trasig: %s' % fel if fel else '')


def _vakten_avslutar(pid, korning):
    """Håller korvakten låset för körningen (kor.sh dog, och vakten gör avslutet)?"""
    if not pid or not _lever(pid):
        return False
    try:
        cmd = subprocess.run(['ps', '-o', 'command=', '-p', str(int(pid))], capture_output=True, text=True, timeout=10,
                             env=dict(os.environ, LC_ALL='C')).stdout
    except Exception:  # noqa: BLE001
        return False
    return 'korvakt.py' in cmd and str(korning) in cmd


def avbrutna(k, efter=None, utom=None):
    """Körningar som startade (korningar/<körning>/START.json, skriven av kor.sh) men saknar slutpost och inte pågår (varken
    kor.sh eller dess vakt håller låset för körningen). Två slag (granskningen av r101, BÖR 1 och KAN 6):
    - uteblev: korslut gjorde avslutet men kunde inte skriva posten (UTEBLEV.json, slutkod 5);
    - avbruten: varken kor.sh eller vakten skrev någon post (SIGKILL mot båda, eller en omstart).
    Bara körningar efter efter. Äldre körningar utan START.json är från före slutposterna och räknas inte."""
    k = Path(k)
    d = k / 'korningar'
    if d.is_symlink() or not d.is_dir():
        return []
    try:
        las_pid = int((k.parent / '.bygge-pid').read_text().strip())
    except (OSError, ValueError):
        las_pid = None
    ut = []
    for x in sorted(d.iterdir()):
        if x.is_symlink() or not x.is_dir() or not KORNING_NAMN.fullmatch(x.name) or x.name == utom or (efter and x.name <= efter):
            continue
        if ((x / SLUTPOST).is_file() and not (x / SLUTPOST).is_symlink()) or not (x / START).is_file():
            continue  # en post finns; en katalog eller länk i postens ställe är ingen post
        s, fel = las_objekt(x / START)
        pid = (s or {}).get('pid')
        if (pid and pid == las_pid and _pagar(pid)) or (las_pid and las_pid != pid and _vakten_avslutar(las_pid, x.name)):
            continue  # pågår, eller vakten gör avslutet
        u = las_objekt(x / UTEBLEV)[0] if not (x / UTEBLEV).is_symlink() else None
        flyttad = k / 'rapporter' / ('RAPPORT-fore-%s.md' % x.name)
        a = {'korning': x.name, 'start': (s or {}).get('start'), 'dom_sha256_start': (s or {}).get('dom_sha256'), 'fel': fel,
             'logg': _rel(k, 'korning-%s.jsonl' % x.name) if (k / ('korning-%s.jsonl' % x.name)).is_file() else None,
             'rapport_flyttad': _rel(k, 'rapporter', flyttad.name) if flyttad.is_file() else None}
        if u is not None:
            a.update(uteblev=str(u.get('fel') or EJ), uteblev_slutkod=u.get('slutkod'), uteblev_protokoll=isinstance(u.get('agarens_dom'), dict))
        ut.append(a)
    return ut


def _avbruten_text(a):
    if a.get('uteblev') is not None:
        vad = 'slutade utan slutpost: posten kunde inte skrivas (%s; slutkod %s)' % (a['uteblev'], a.get('uteblev_slutkod') or EJ)
    else:
        vad = 'avbröts utan slutpost: varken kor.sh eller vakten skrev någon (SIGKILL mot båda, eller en omstart)'
    return 'körningen %s (startad %s) %s%s%s' % (
        a['korning'], a.get('start') or EJ, vad, '; logg %s' % a['logg'] if a.get('logg') else '',
        '; den äldre rapporten flyttades till %s' % a['rapport_flyttad'] if a.get('rapport_flyttad') else '')


def _granskningsrad(g, nu_hash, metod_nu=None):
    rad = {'godkand': bool(g.get('godkand')), 'omgang': g.get('runda'), 'korning': g.get('korning'), 'dist_sha256': g.get('dist_sha256'),
           'samma_bygge': bool(nu_hash) and g.get('dist_sha256') == nu_hash, 'metod_sha': g.get('metod_sha'), 'modell': g.get('modell'),
           'effort': g.get('effort'), 'granskare': g.get('granskare'), 'originalitet': g.get('originalitet'), 'tid': g.get('tid'),
           'betyg': {n: (x or {}).get('betyg') for n, x in (g.get('kriterier') or {}).items() if isinstance(x, dict)}}
    if metod_nu is not None:
        try:
            import granska
            rad['samma_metod'] = bool(granska.samma_metod(g, metod_nu))
        except Exception:  # noqa: BLE001
            rad['samma_metod'] = None
    return rad


def _skiljer(h):
    """Vad som skiljer en historisk omgång från det slutliga bygget och metoden (granskningen av r101, KAN 4)."""
    delar = [x for x, galler in (('ett annat bygge (dist %s)' % _kort(h.get('dist_sha256')), not h.get('samma_bygge')),
                                 ('en annan metod (metod %s)' % _kort(h.get('metod_sha')), h.get('samma_metod') is False)) if galler]
    return ' och '.join(delar) or 'en tidigare omgång (samma bygge och metod, men inte den körningens giltiga omgång)'


def slutpost(k, rc, korning, s, v, g, nu_hash, senaste, gfel, skydd, mekanik, domlogg, skal_ej, slutkod, slutkod_text, dom=None, lasfel=(),
             bevis=None, avbruten=None, processer=None, listor=None):
    """Körningens slutpost: rapporthuvudets fält, de fem tillstånden var för sig, kontrollerna, granskningen, metoden,
    startsidan, bristerna, nästa steg och länkarna. Bara uppgifter som avslutet har; det som saknas står som ej angivet.
    dom: (tillstånd, protokoll) för ägarens dom (agaren_vid_slut); bevis: {namn: relativ väg} för provets och stoppvaktens
    besked kopierade till postens katalog; processer: vaktens besked (processer_efter); listor: hashlistornas prövning mot
    kor.sh:s minne (hashlistorna)."""
    k = Path(k)
    slug = k.name
    tid = nu()
    s = s if isinstance(s, dict) else None
    v = v if isinstance(v, dict) else None
    bevis = bevis or {}
    # tekniska kontroller: provet, stoppvaktens egna kontroller, rapporten och mekaniken
    grindar = {n: bool((x or {}).get('ok') if isinstance(x, dict) else x) for n, x in ((s or {}).get('grindar') or {}).items()} \
        if isinstance((s or {}).get('grindar'), dict) else {}
    provet = {'finns': bool(s), 'gront': bool(s and s.get('ok')), 'grindar': grindar, 'dist_sha256': (s or {}).get('dist_sha256'),
              'tid': (s or {}).get('tid'), 'vinnare': ((s or {}).get('info') or {}).get('vinnare') if isinstance((s or {}).get('info'), dict) else None}
    provet['varde'] = provet['gront'] and bool(nu_hash) and provet['dist_sha256'] == nu_hash
    provet['text'] = ('kördes aldrig (inget STATUS.json)' if not s else 'RÖTT' if not s.get('ok') else 'GRÖNT, men inget bygge i dist/'
                      if not nu_hash else 'GRÖNT för bygget i dist/' if provet['varde'] else 'GRÖNT men för ett annat bygge än det i dist/')
    sv = v or {}
    # tekniskt godkänt bygger på stoppvaktens egna kontroller (provet som den körde), inte på om den släppte avslutet:
    # stoppvakten håller kvar ett tekniskt grönt bygge när granskaren underkänner (granskningen av r101, BÖR 3)
    grona = sv.get('kontroller_grona') is True or ('kontroller_grona' not in sv and str(sv.get('skal') or '').startswith('kontrollerna gröna'))
    stoppvakten = {'finns': bool(v), 'skal': sv.get('skal'), 'forsok': sv.get('forsok'), 'tak': sv.get('tak'), 'korning': sv.get('korning'),
                   'dist_sha256': sv.get('dist_sha256'), 'slapp': sv.get('slapp'), 'kontroller_grona': grona, 'granskning': sv.get('granskning')}
    stoppvakten['varde'] = grona and (not korning or sv.get('korning') == korning) and bool(nu_hash) and sv.get('dist_sha256') == nu_hash
    stoppvakten['text'] = ('inget besked (STOPPVAKT.json saknas)' if not v else
                           'besked från en annan körning (%s)' % sv.get('korning') if korning and sv.get('korning') != korning else
                           'inget bygge i dist/' if not nu_hash else
                           'besked om ett annat bygge än det i dist/' if sv.get('dist_sha256') != nu_hash else
                           'kontrollerna gröna%s' % ('' if sv.get('slapp') else '; stoppvakten höll kvar bygget (%s)' % (sv.get('skal') or EJ))
                           if grona else 'kontrollerna inte gröna (%s)' % (sv.get('skal') or EJ))
    r_ok, r_skal = rapport_giltig(k, v, korning)
    flyttad = k / 'rapporter' / ('RAPPORT-fore-%s.md' % korning) if korning else None
    rapporten = {'fil': _rel(k, 'RAPPORT.md'), 'finns': (k / 'RAPPORT.md').is_file(), 'varde': r_ok, 'text': r_skal,
                 'sha256': sv.get('rapport_sha256'), 'korning': sv.get('rapport_korning'), 'satt': sv.get('rapport_bunden'),
                 'aldre_flyttad': _rel(k, 'rapporter', flyttad.name) if flyttad and flyttad.is_file() else None}
    mek = {'varde': not mekanik, 'andrade': skydd[:40], 'antal': len(skydd), 'mekanik': mekanik[:20], 'domlogg': bool(domlogg),
           'text': 'oförändrad' if not mekanik else 'ändrades under körningen: %s' % ', '.join(mekanik[:6])}
    tekniskt = {'varde': bool(provet['varde'] and stoppvakten['varde'] and r_ok and mek['varde'])}
    tekniskt['text'] = 'ja' if tekniskt['varde'] else '; '.join(t for t, ok in (
        ('provet: ' + provet['text'], provet['varde']), ('stoppvakten: ' + stoppvakten['text'], stoppvakten['varde']),
        ('rapporten: ' + r_skal, r_ok), ('mekaniken: ' + mek['text'], mek['varde'])) if not ok)
    # designgranskningen: bara en omgång för det slutliga bygget med aktuell metod gäller; en annan är historik
    try:
        import granska
        metod = granska.aktuell_metod(slug)
        aktuell_g = g if (isinstance(g, dict) and not gfel and nu_hash and g.get('dist_sha256') == nu_hash and granska.samma_metod(g, metod)) else None
    except Exception as e:  # noqa: BLE001
        metod, aktuell_g = {'fel': str(e)[:200]}, None
    historisk = senaste if isinstance(senaste, dict) and (not aktuell_g or senaste.get('runda') != aktuell_g.get('runda')) else (
        g if isinstance(g, dict) and not gfel and not aktuell_g else None)
    if not aktuell_g and not historisk and not gfel and (k / 'granskning').is_dir():
        try:  # en giltig omgång i en tidigare körning är också historik, aldrig en dom över körningens bygge
            alla = granska.valj_sammanfattning(k / 'granskning', None, None)
            historisk = alla[1] if alla else None
        except Exception:  # noqa: BLE001 — historiken är information; en oläsbar omgång nekar redan ovan
            historisk = None
    metod_nu = metod if 'metod_sha' in metod else None
    design = {'fel': gfel, 'aktuell': _granskningsrad(aktuell_g, nu_hash, metod_nu) if aktuell_g else None,
              'historisk': _granskningsrad(historisk, nu_hash, metod_nu) if historisk else None, 'dist_nu': nu_hash,
              'metod_sha': metod.get('metod_sha'), 'avstangd': sv.get('granskning') == 'avstängd'}
    if aktuell_g:
        a = design['aktuell']
        design['vem'] = '%s granskare, %s %s, originalitet %s' % (a['granskare'] or EJ, a['modell'] or EJ, a['effort'] or EJ, a['originalitet'] or EJ)
    if gfel:
        dg = {'varde': False, 'text': 'omgångarna kunde inte läsas eller valideras: %s' % gfel}
    elif aktuell_g:
        dg = {'varde': bool(aktuell_g.get('godkand')), 'vem': design['vem'], 'omgang': aktuell_g.get('runda'),
              'text': '%s; omgång %s, dist %s = slutliga bygget, metod %s vid körningens slut; %s' % (
                  'godkänd' if aktuell_g.get('godkand') else 'underkänd', aktuell_g.get('runda'), _kort(aktuell_g.get('dist_sha256')),
                  _kort(metod.get('metod_sha')), design['vem'])}
    else:
        dg = {'varde': None, 'text': 'granskningen var avstängd (NWP_GRANSKNING=av)' if design['avstangd'] else 'inget bygge i dist/ att granska'
              if not nu_hash else 'ingen giltig omgång för det slutliga bygget %s med metoden vid körningens slut' % _kort(nu_hash)}
        if historisk:
            h = design['historisk']
            dg['historisk'] = 'omgång %s, %s: historik; den gällde %s' % (h['omgang'], 'godkänd' if h['godkand'] else 'underkänd', _skiljer(h))
            dg['text'] += '; senaste dom är historik (%s)' % dg['historisk']
    dom_t, dom_p = dom if dom else (agarens_dom(k, nu_hash), None)
    tillstand = {'sessionen_avslutad': sessionen(k, korning, rc, avbruten), 'tekniskt_godkant': tekniskt, 'designgranskaren_godkanner': dg,
                 'agaren_godkanner': dom_t}
    tillstand['klart_for_leverans'] = leverans(tillstand, slutkod, slug)
    # metod och identitet
    repo = repo_identitet()
    bygget = {'modell': os.environ.get('NWP_MODELL') or 'opus[1m]', 'effort': os.environ.get('NWP_EFFORT') or 'medium',
              'max_turns': os.environ.get('NWP_MAX_TURNS') or '400', 'atelje': os.environ.get('NWP_ATELJE') or 'pa',
              'sandlada': os.environ.get('NWP_SANDLADA') or 'av', 'mcp': os.environ.get('NWP_MCP_CONFIG') or 'av'}
    sida = startsidan(k)
    ident = ['repo nortropic-webb-pro commit %s%s' % (repo['commit'], ' (%d ändrade spårade filer)' % repo['andrade_filer'] if repo.get('andrade_filer') else '')
             if repo else 'repo: ' + EJ, 'körning %s' % (korning or EJ), 'dist %s' % (nu_hash or EJ), 'granskningsmetod %s' % (metod.get('metod_sha') or EJ)]
    if aktuell_g:
        ident.append('granskningsomgång %s' % aktuell_g.get('runda'))
    if sida.get('kandidat'):
        ident.append('kandidat %s version %s' % (sida['kandidat'], sida.get('version') or EJ))
    elif sida.get('sha_index'):
        ident.append('godkänd startsida sha256 %s' % sida['sha_index'])
    # utfall, brister och nästa steg
    underkant = (bool(s) and not s.get('ok')) or (aktuell_g is not None and not aktuell_g.get('godkand'))
    utfall = {0: ('godkänt: tekniskt, av designgranskaren och av ägaren (slutkod 0)' if dom_t.get('varde') is True else
                  'ej bedömt av ägaren: tekniskt godkänt och designgranskaren godkänner (slutkod 0); ägaren godkänner: %s (%s)' % (
                      ORD.get(dom_t.get('varde')), dom_t.get('text'))),
              1: '%s av korslut (slutkod 1): %s' % ('underkänt' if underkant else 'ofullständigt', skal_ej or EJ),
              3: 'ofullständigt (slutkod 3): mekaniken eller gränsen ändrades under körningen; inget av proven gäller',
              4: 'ofullständigt (slutkod 4): %s' % tillstand['sessionen_avslutad']['text'],
              6: 'ofullständigt (slutkod 6): bygget stannade utan sajt (%s)' % (sv.get('skal') or EJ)}[slutkod]
    tidigare_avbrutna = avbrutna(k, efter=_senaste_post_fore(k, korning), utom=korning) if korning else []
    processer = processer if isinstance(processer, dict) else processer_efter()
    brister = [x for x in [
        None if tillstand['sessionen_avslutad']['varde'] else tillstand['sessionen_avslutad']['text'],
        None if tekniskt['varde'] else 'tekniskt: %s' % tekniskt['text'],
        None if dg['varde'] is True else 'designgranskningen: %s' % dg['text'],
        None if dom_t.get('avsandare') != EJ_BELAGD else 'ägarens dom: %s' % dom_t.get('text'),
        None if processer.get('varde') is True else 'byggets processer: %s' % processer['text'],
        'skyddade texter ändrades under körningen: %s' % ', '.join(x for x in skydd[:10] if x not in mekanik) if [x for x in skydd if x not in mekanik] else None,
        ('inte godkänt: %s' % skal_ej) if skal_ej else None] + ['läsfel: %s' % x for x in lasfel if x]
        + [_avbruten_text(a) for a in tidigare_avbrutna] if x]
    atgarder = {0: ['ägaren dömer bygget i dashboarden (bygget, fliken Din dom); domen binds till dist %s' % _kort(nu_hash),
                    'efter ägarens godkännande: exporten, .venv/bin/python kontroller/exportera.py %s (kunskap/lansering.md)' % slug],
                1: ['läs bristerna, rapporten och provets PROV.md; rätta och kör ./kor.sh %s "<verksamhet>" igen' % slug],
                3: ['granska ändringarna i mekaniken (listan i posten) innan något av byggets resultat används'],
                4: ['läs körningens logg %s och starta om ./kor.sh %s "<verksamhet>"' % (_rel(k, 'korning-%s.jsonl' % korning), slug)],
                6: ['skapandeflödet före ett nytt bygge: .venv/bin/python kontroller/prototyp.py %s (underlag/%s/atelje/)' % (slug, slug)]}[slutkod]
    if slutkod == 1 and dg['varde'] is None and sv.get('tak_skal'):
        atgarder.append('en ny granskningsomgång behövs: %s' % sv['tak_skal'])
    underlag = [x for x in [_rel(k, 'korning-%s.jsonl' % korning) if korning and (k / ('korning-%s.jsonl' % korning)).is_file() else None,
                            bevis.get('STATUS.json') or (_rel(k, 'prov', 'STATUS.json') if s else None),
                            _rel(k, 'prov', 'PROV.md') if (k / 'prov' / 'PROV.md').is_file() else None,
                            bevis.get('STOPPVAKT.json') or (_rel(k, 'prov', 'STOPPVAKT.json') if v else None),
                            _rel(k, 'granskning', 'runda-%02d' % int(aktuell_g['runda']), 'GRANSKNING.json')
                            if aktuell_g and str(aktuell_g.get('runda') or '').isdigit() and (k / 'granskning' / ('runda-%02d' % int(aktuell_g['runda']))).is_dir() else None,
                            _rel(k, 'RAPPORT.md') if rapporten['finns'] else None,
                            '%s (den äldre rapporten, flyttad när körningen startade)' % rapporten['aldre_flyttad'] if rapporten['aldre_flyttad'] else None,
                            _rel(k, 'FRAGOR.json') if (k / 'FRAGOR.json').is_file() else None,
                            _rel(k, 'korvakt-%s.log' % korning) if korning and (k / ('korvakt-%s.log' % korning)).is_file() else None,
                            sida.get('vinnare'), 'underlag/%s/atelje/STARTKVITTO-BYGGE.md' % slug
                            if (k.resolve().parent.parent / 'underlag' / slug / 'atelje' / 'STARTKVITTO-BYGGE.md').is_file() else None] if x]
    beslut = [x for x in [('ägarens godkännande av startsidan %s (%s)' % (sida['godkand'], sida['vinnare'])) if sida.get('godkand') else None,
                          ('ägarens dom över bygget %s (%s)' % (dom_t.get('tid'), dom_t.get('kalla'))) if dom_t.get('tid') else None] if x]
    verksamhet = os.environ.get('NWP_VERKSAMHET')
    post = {'schema': 1, 'id': 'SLUT-%s-%s' % (slug, korning or EJ), 'titel': 'Slutbesked för helbygget %s, körningen %s' % (slug, korning or EJ),
            'typ': TYP, 'uppdrag': '%s: %s' % (UPPDRAG, verksamhet) if verksamhet else UPPDRAG, 'kund': slug, 'moment': MOMENT,
            'forfattare': _forfattare('kontroller/korslut.py (kor.sh:s avslut)'),
            'datum': tid, 'granskad_identitet': ident, 'rapportstatus': 'färdig', 'bedomningsutfall': utfall,
            'foregaende': foregaende(k, korning) if korning else EJ, 'ersatt_av': EJ, 'underlag': underlag, 'beslut': beslut or EJ,
            'atgarder': atgarder, 'korning': korning, 'dist_sha256': nu_hash, 'kallor_sha256': (s or {}).get('kallor_sha256'),
            'slutkod': slutkod, 'slutkod_text': slutkod_text,
            'tillstand': tillstand,
            'kontroller': {'provet': provet, 'stoppvakten': stoppvakten, 'rapporten': rapporten, 'mekaniken': mek, 'agarens_dom': dom_p,
                           'processer': processer, 'hashlistorna': listor if isinstance(listor, dict) else
                           {'varde': None, 'text': 'ej prövade mot kor.sh:s minne'}},
            'designgranskning': design, 'metod': {'granskning': metod, 'bygget': bygget, 'repo': repo}, 'startsida': sida,
            'brister': brister, 'inte_godkant': skal_ej or None, 'titta': 'cd %s && npx astro preview' % _rel(k, 'sajt')}
    if avbruten:
        post['avbruten'] = avbruten
    if tidigare_avbrutna:
        post['avbrutna_fore'] = tidigare_avbrutna
    return post


def _senaste_post_fore(k, korning):
    tidigare = [f.parent.name for f in slutposter(k) if f.parent.name < korning]
    return tidigare[-1] if tidigare else None


def _granskningstext(post):
    d = post['designgranskning']
    r = []
    if d.get('fel'):
        r.append('Granskningen: omgångarna kunde inte läsas eller valideras, inget godkännande: %s' % d['fel'])
    elif d.get('andrat') and d.get('historisk'):
        h = d['historisk']
        r.append('Granskningen: historik, gäller inte det som gäller nu (%s): %s, omgång %s, gällde dist %s och metod %s vid körningens slut' % (
            '; '.join(d['andrat']), 'godkänd' if h['godkand'] else 'underkänd', h['omgang'], _kort(h['dist_sha256']), _kort(h.get('metod_sha'))))
        return r
    elif d.get('aktuell'):
        a = d['aktuell']
        r.append('Granskningen: %s (omgång %s, dist %s = slutliga bygget, aktuell metod) — %s' % (
            'GODKÄND' if a['godkand'] else 'UNDERKÄND', a['omgang'], _kort(a['dist_sha256']),
            ', '.join('%s %s' % (n, b) for n, b in (a.get('betyg') or {}).items())))
    elif not d.get('dist_nu') and not d.get('avstangd'):
        r.append('Granskningen: inget bygge i dist/ att granska')
    else:
        r.append('Granskningen: %s; slutliga bygget är inte granskat' % (
            'avstängd (NWP_GRANSKNING=av)' if d.get('avstangd') else 'ingen giltig omgång för det slutliga bygget %s med %s' % (
                _kort(d.get('dist_nu')), 'metoden vid körningens slut' if d.get('andrat') else 'aktuell metod')))
    h = d.get('historisk')
    if h:
        r.append('Senaste dom oavsett bygge och metod: %s (omgång %s, dist %s%s)' % ('godkänd' if h['godkand'] else 'underkänd', h['omgang'],
                                                                                 _kort(h['dist_sha256']), '' if h['samma_bygge'] else ' ≠ slutliga bygget'))
    return r


def _provad_text(p):
    r = ['Prövad nu (%s): %s' % (p.get('tid') or EJ, '; '.join(p.get('andrat') or []) or
                                 'samma bygge, metod och startsida som vid körningens slut')]
    if p.get('andrat'):
        r.append('Postens godkännanden är historik: de gällde dist %s och metod %s vid körningens slut, inte det som gäller nu.' % (
            _kort(p.get('dist_post')), _kort(p.get('metod_post'))))
    for x in p.get('senare_korningar') or []:
        r.append('Senare körning: %s' % x)
    for x in p.get('senare_stopp') or []:
        r.append('Senare start som stannade före bygget: %s' % x)
    for a in p.get('avbrutna') or []:
        r.append('Utan slutpost: %s' % _avbruten_text(a))
    return r


def text(post):
    """Terminalens besked, skrivet ur slutposten och ingenting annat (ägarens uppdrag 2026-10-07, punkt 4)."""
    huvud = _provad_text(post['provad']) if post.get('provad') else []
    if post.get('typ') == TYP_STOPP:
        return '\n'.join(huvud + [str(post.get('skal') or EJ)] + ['Brist: %s' % b for b in (post.get('brister') or [])[1:]]
                         + ['Slutpost: %s' % (post.get('slutpost') or 'skrevs inte: %s' % post.get('slutpost_fel', EJ)), post['slutkod_text']])
    t, kn = post['tillstand'], post['kontroller']
    kod = t['sessionen_avslutad'].get('kod')
    r = huvud + ['claude avslutade med kod %s%s' % (kod, ' (avbruten med %s)' % post['avbruten'] if post.get('avbruten') else '') if isinstance(kod, int)
                 else t['sessionen_avslutad'].get('text') or 'claudes slutkod är okänd']
    if isinstance(kn.get('processer'), dict):
        r.append('Byggets processer: %s' % kn['processer'].get('text'))
    mek = kn['mekaniken']
    if mek['antal']:
        r.append('VARNING: skyddade filer ändrades under körningen, av bygget eller någon annan (kirurgen, ägarens dom):\n' + '\n'.join(mek['andrade'])
                 + ('\n… %d till' % (mek['antal'] - 40) if mek['antal'] > 40 else ''))
    p = kn['provet']
    if p['finns']:
        r.append('Provet: %s — %s' % ('GRÖNT' if p['gront'] else 'RÖTT', ', '.join('%s %s' % (n, 'ok' if ok else 'RÖD') for n, ok in p['grindar'].items())))
        if p.get('vinnare'):
            r.append('Ateljéns vinnare mot bygget: %s' % p['vinnare'])
    else:
        r.append('Provet: inget STATUS.json (provet kördes aldrig)')
    sv = kn['stoppvakten']
    if sv['finns']:
        r.append('Stoppvakten: %s (försök %s av %s)' % (sv['skal'], sv['forsok'], sv['tak']))
    r += _granskningstext(post)
    rp = kn['rapporten']
    r.append('Rapport: %s' % ('%s (%s)' % (rp['fil'], rp['text']) if rp['finns'] else 'saknas'))
    if rp.get('aldre_flyttad'):
        r.append('Den äldre rapporten: %s' % rp['aldre_flyttad'])
    if post.get('rapport_flyttad_till'):
        r.append('Postens rapport flyttades när en senare körning startade: %s' % post['rapport_flyttad_till'])
    r.append('Titta:  %s' % post['titta'])
    if post.get('inte_godkant'):
        r.append('Inte godkänt: %s' % post['inte_godkant'])
    if mek['domlogg']:
        r.append('Ägarens domlogg ändrades under körningen fast den var låst; ägarens domar skrivs bara av dashboarden när inget bygge pågår.')
    r.append('Tillstånden, var för sig:')
    for nyckel, namn in TILLSTAND:
        x = t[nyckel]
        r.append('  %s: %s%s' % (namn, ORD.get(x.get('varde'), str(x.get('varde'))), (' — ' + x['text']) if x.get('text') and x['text'] != 'ja' else ''))
    r.append('  (omfattningen: %s)' % t['klart_for_leverans']['omfattning'])
    for b in [b for b in post.get('brister') or [] if b.startswith(('läsfel:', 'körningen '))]:
        r.append('Brist: %s' % b)
    for a in post.get('atgarder') or []:
        r.append('Nästa steg: %s' % a)
    r.append('Posten: %s%s' % (post.get('rapportstatus') or EJ, ', ersatt av %s' % post['ersatt_av'] if post.get('ersatt_av') not in (None, EJ) else ''))
    r.append('Slutpost: %s' % (post.get('slutpost') or ('skrevs inte: %s' % post['slutpost_fel'] if post.get('slutpost_fel')
                                                     else 'skrevs inte (ingen körning angiven)')))
    r.append(post['slutkod_text'])
    return '\n'.join(r)


def slutposter(k):
    """Körningarnas slutposter för kunden, äldst först (körningens identitet sorterar som tid)."""
    d = Path(k) / 'korningar'
    if d.is_symlink() or not d.is_dir():
        return []
    return sorted((f for f in d.glob('*/' + SLUTPOST) if f.is_file() and not f.is_symlink() and not f.parent.is_symlink()), key=lambda f: f.parent.name)


def senaste_slutpost(k, efter=None):
    """(fil, post) för den senaste slutposten, bara körningar från efter (en körningsidentitet) och framåt; annars (None, None)."""
    for f in reversed(slutposter(k)):
        if efter and f.parent.name < efter:
            break
        p = las(f)
        if isinstance(p, dict):
            return f, p
    return None, None


def _skriv_json(fil, data):
    # Exklusivt skapad fil: ett förutsägbart PID-namn kunde vara en planterad länk.
    fd, namn = tempfile.mkstemp(prefix='.korslut-', suffix='.tmp', dir=fil.parent)
    tmp = Path(namn)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
        os.replace(tmp, fil)
    finally:
        tmp.unlink(missing_ok=True)


def postkatalog(k, korning):
    """kunder/<slug>/korningar/<körning>/, skapad och prövad: ingen symlänk på vägen, ingen ogiltig identitet."""
    k = Path(k)
    if not KORNING_NAMN.fullmatch(str(korning or '')):
        raise ValueError('körningen %r är ingen giltig identitet' % (korning,))
    for d in (k, k / 'korningar', k / 'korningar' / korning):
        if d.is_symlink():
            raise OSError('%s är en symlänk; slutposten skrivs inte' % d)
    d = k / 'korningar' / korning
    d.mkdir(parents=True, exist_ok=True)
    return d


def kopiera_bevis(k, korning):
    """Provets och stoppvaktens besked kopierade till postens katalog, eftersom nästa körning skriver över dem
    (granskningen av r101, BÖR 4). Ger {namn: relativ väg} för det som kopierades."""
    k = Path(k)
    d = postkatalog(k, korning)
    ut = {}
    for namn in ('STATUS.json', 'STOPPVAKT.json'):
        src = k / 'prov' / namn
        if src.is_file() and not src.is_symlink():
            shutil.copyfile(src, d / ('prov-%s' % namn))
            ut[namn] = _rel(k, 'korningar', korning, 'prov-%s' % namn)
    return ut


def skriv_slutpost(k, korning, post, ersatt=True):
    """Skriver kunder/<slug>/korningar/<körning>/SLUT.json atomiskt och ger filen. En post från ett bygge (ersatt) märker
    de tidigare, ännu gällande posterna som ersatta, men bara när den gäller ett annat bygge eller en annan metod: en körning
    som föll utan att ändra dist eller metod ersätter inte den post som beskriver bygget (granskningen av r101, BÖR 7).
    Har körningen flyttat en äldre rapport får posten som rapporten hörde till länken dit (BÖR 4). Uppgifterna i övrigt
    ändras inte. Ingen länk följs."""
    k = Path(k)
    d = postkatalog(k, korning)
    post['slutpost'] = _rel(k, 'korningar', korning, SLUTPOST)
    _skriv_json(d / SLUTPOST, post)
    markera_flyttad_rapport(k, korning)
    if ersatt:
        for f in slutposter(k):
            if f.parent.name >= korning:
                continue
            p = las(f)
            if not isinstance(p, dict) or p.get('ersatt_av') not in (None, EJ):
                continue
            if p.get('typ') == TYP and p.get('dist_sha256') == post.get('dist_sha256') and _metod_sha(p) == _metod_sha(post):
                continue  # samma bygge och samma metod: den tidigare posten beskriver fortfarande bygget
            p.update(rapportstatus='ersatt', ersatt_av='%s (%s)' % (post['id'], post['slutpost']), ersatt_tid=post['datum'])
            _skriv_json(f, p)
    return d / SLUTPOST


def markera_flyttad_rapport(k, korning):
    """kor.sh flyttade den äldre RAPPORT.md till rapporter/RAPPORT-fore-<körning>.md när körningen startade. Den senaste
    tidigare posten som länkade till RAPPORT.md får länken till den flyttade filen (rapport_flyttad_till), och dess
    underlag pekar dit i stället för på nästa körnings RAPPORT.md (granskningen av r101, BÖR 4)."""
    k = Path(k)
    flyttad = k / 'rapporter' / ('RAPPORT-fore-%s.md' % korning)
    if not flyttad.is_file() or flyttad.is_symlink():
        return None
    rel = _rel(k, 'rapporter', flyttad.name)
    sha = sha_fil(flyttad)
    for f in reversed([f for f in slutposter(k) if f.parent.name < korning]):
        p = las(f)
        if not isinstance(p, dict) or p.get('typ') != TYP or not ((p.get('kontroller') or {}).get('rapporten') or {}).get('finns'):
            continue
        if p.get('rapport_flyttad_till'):
            return None  # rapporten som posten länkade till har redan flyttats en gång; den här filen hör till en senare
        egen = ((p.get('kontroller') or {}).get('rapporten') or {}).get('sha256')
        p['rapport_flyttad_till'] = rel
        p['rapport_flyttad'] = {'av_korning': korning, 'sha256': sha, 'samma_som_postens': (egen == sha) if egen else None}
        p['underlag'] = [rel + ' (flyttad hit när körningen %s startade)' % korning if u == _rel(k, 'RAPPORT.md') else u
                         for u in (p.get('underlag') if isinstance(p.get('underlag'), list) else [])]
        _skriv_json(f, p)
        return f
    return None


def stopp(k, korning, skal):
    """kor.sh stannade före bygget (slutkod 2): en kort post med skälet. Den ersätter ingen post, eftersom bygget i dist/
    inte ändrades; den föregående posten beskriver det. Har den äldre rapporten redan flyttats länkas den."""
    k = Path(k)
    tid = nu()
    flyttad = k / 'rapporter' / ('RAPPORT-fore-%s.md' % korning)
    tidigare_avbrutna = avbrutna(k, efter=_senaste_post_fore(k, korning), utom=korning)
    verksamhet = os.environ.get('NWP_VERKSAMHET')
    post = {'schema': 1, 'id': 'SLUT-%s-%s' % (k.name, korning), 'titel': 'Slutbesked: kor.sh stannade före bygget, körningen %s' % korning,
            'typ': TYP_STOPP, 'uppdrag': '%s: %s' % (UPPDRAG, verksamhet) if verksamhet else UPPDRAG, 'kund': k.name, 'moment': MOMENT,
            'forfattare': _forfattare('kontroller/korslut.py (kor.sh)'), 'datum': tid,
            'granskad_identitet': ['körning %s' % korning], 'rapportstatus': 'färdig',
            'bedomningsutfall': 'ej bedömt (slutkod 2): bygget startade inte; %s' % skal, 'foregaende': foregaende(k, korning), 'ersatt_av': EJ,
            'underlag': [x for x in [_rel(k, 'startkontroll.log') if 'startkontroll' in skal and (k / 'startkontroll.log').is_file() else None,
                                     'underlag/%s/atelje/STARTKVITTO-BYGGE-STOPP.md' % k.name if 'startkontroll' in skal else None,
                                     '%s (den äldre rapporten, flyttad när körningen startade)' % _rel(k, 'rapporter', flyttad.name)
                                     if flyttad.is_file() else None,
                                     _rel(k, 'korvakt-%s.log' % korning) if (k / ('korvakt-%s.log' % korning)).is_file() else None] if x] or EJ,
            'beslut': EJ, 'atgarder': ['rätta det som stoppade starten (skälet) och starta ./kor.sh %s "<verksamhet>" igen' % k.name],
            'korning': korning, 'slutkod': 2, 'slutkod_text': 'Slutkod 2: bygget startade inte; kor.sh stannade före bygget', 'skal': skal,
            'tillstand': {'sessionen_avslutad': {'varde': None, 'text': 'ingen session startades'},
                          'tekniskt_godkant': {'varde': None, 'text': 'inget nytt bygge att pröva'},
                          'designgranskaren_godkanner': {'varde': None, 'text': 'inget nytt bygge att granska'},
                          'agaren_godkanner': {'varde': None, 'text': 'inget nytt bygge att döma; bygget i dist/ beskrivs av föregående post'},
                          'klart_for_leverans': {'varde': False, 'text': 'bygget startade inte', 'omfattning': EJ}},
            'brister': [skal] + [_avbruten_text(a) for a in tidigare_avbrutna]}
    if tidigare_avbrutna:
        post['avbrutna_fore'] = tidigare_avbrutna
    try:
        skriv_slutpost(k, korning, post, ersatt=False)
    except (OSError, ValueError) as e:
        post.update(slutpost=None, slutpost_fel=str(e)[:300])
        skriv_uteblev(k, korning, 'den korta posten kunde inte skrivas: %s' % str(e)[:200], 2)
    return post


def _forfattare(standard):
    return 'kontroller/korslut.py (korvaktens avslut, kontroller/korvakt.py: kor.sh dog)' if os.environ.get('NWP_AVBRUTEN') == 'KORSH' else standard


def skriv_uteblev(k, korning, fel, slutkod, dom_p=None):
    """En körning vars slutpost inte kunde skrivas lämnar korningar/<körning>/UTEBLEV.json, när katalogen går att skriva
    utan att följa en länk: nästa start och --visa skiljer den från en körning som avbröts (KAN 6), och domarna som inte
    räknades står kvar (ej_belagda_domar). Ger filen eller None."""
    try:
        if not KORNING_NAMN.fullmatch(str(korning or '')):
            return None
        d = Path(k) / 'korningar' / korning
        if Path(k).is_symlink() or d.parent.is_symlink() or d.is_symlink() or not d.is_dir() or (d / UTEBLEV).is_symlink():
            return None
        data = {'korning': korning, 'tid': nu(), 'fel': fel, 'slutkod': slutkod}
        if isinstance(dom_p, dict):
            data['agarens_dom'] = dom_p
        _skriv_json(d / UTEBLEV, data)
        return d / UTEBLEV
    except (OSError, ValueError):
        return None


def aktuell(k, korning=None):
    """Slutposten prövad nu, utan att posten på disk ändras (granskningen av r101, B2 och BÖR 7).
    - Utan körning väljs den senaste fullständiga posten som gäller bygget i dist/ nu, annars den senaste fullständiga,
      annars den senaste posten; senare starter som stannade och körningar utan slutpost nämns.
    - Har dist/, granskningens metod (metod_sha) eller startsidans godkännande (VINNARE.json) ändrats sedan posten står
      det tekniska godkännandet och granskningen som historik ("gällde dist X och metod Y") och klart för leverans är nej.
    - Ägarens dom prövas mot DOM.json nu, utan domar som en körning kan ha skrivit (ej_belagda, ur slutposterna och
      UTEBLEV.json). En körning som dödas med SIGKILL får sin post av vakten, så ägarens senare dom räknas (KAN 4). Dog
      också vakten (ingen post och inget protokoll) är domen ej belagd så länge DOM.json ändrats sedan den körningen
      startade; nästa körning räknar inte domar som tillkom efter det.
    Ger None utan post."""
    k = Path(k)
    dist = k / 'sajt' / 'dist'
    try:
        import prova
        nu_hash = prova.dist_hash(dist) if (dist / 'index.html').is_file() else None
    except Exception:  # noqa: BLE001
        nu_hash = None
    poster = [(f, las(f)) for f in reversed(slutposter(k))]
    poster = [(f, p) for f, p in poster if isinstance(p, dict)]
    if korning:
        if not KORNING_NAMN.fullmatch(korning):
            return None
        post = next((p for f, p in poster if f.parent.name == korning), None)
    else:  # samma bygge: den senaste godkända posten går före en senare körning som föll utan att ändra bygget
        fulla = [p for f, p in poster if p.get('typ') == TYP]
        samma = [p for p in fulla if nu_hash and p.get('dist_sha256') == nu_hash]
        post = (next((p for p in samma if p.get('slutkod') == 0), None) or (samma[0] if samma else None)
                or (fulla[0] if fulla else (poster[0][1] if poster else None)))
    if not isinstance(post, dict):
        return None
    post = json.loads(json.dumps(post))
    pk = str(post.get('korning') or '')
    senare_stopp = ['%s: %s' % (p.get('korning'), p.get('skal') or EJ) for f, p in reversed(poster) if p.get('typ') == TYP_STOPP and str(p.get('korning')) > pk]
    senare_avbrutna = avbrutna(k, efter=pk)
    provad = {'tid': nu(), 'dist_nu': nu_hash, 'dist_post': post.get('dist_sha256'), 'metod_post': _metod_sha(post),
              'samma_bygge': nu_hash == post.get('dist_sha256'), 'senare_stopp': senare_stopp, 'avbrutna': senare_avbrutna,
              'senare_poster': [f.parent.name for f, p in reversed(poster) if f.parent.name > pk],
              'senare_korningar': ['%s (slutkod %s, dist %s)' % (p.get('korning'), p.get('slutkod'), _kort(p.get('dist_sha256')))
                                   for f, p in reversed(poster) if p.get('typ') == TYP and str(p.get('korning')) > pk], 'andrat': []}
    post['provad'] = provad
    t = post.get('tillstand') or {}
    if post.get('typ') != TYP or not all(n in t for n, _ in TILLSTAND):
        return post
    andrat = provad['andrat']
    if post.get('kallor_sha256'):
        try:
            import skapande
            provad['kallor_nu'] = skapande.kallversion(k / 'sajt')
        except (OSError, ValueError):
            provad['kallor_nu'] = None
        if provad['kallor_nu'] != post['kallor_sha256']:
            andrat.append('källorna har ändrats eller är oläsbara sedan det granskade bygget')
    if not provad['samma_bygge']:
        andrat.append('bygget i dist/ har ändrats (dist %s vid körningens slut, nu %s)' % (_kort(post.get('dist_sha256')), _kort(nu_hash)))
    try:
        import granska
        metod_nu = granska.aktuell_metod(k.name).get('metod_sha')
    except Exception as e:  # noqa: BLE001
        metod_nu = None
        andrat.append('granskningens metod kunde inte prövas nu (%s)' % str(e)[:120])
    provad['metod_nu'] = metod_nu
    if _metod_sha(post) and metod_nu and metod_nu != _metod_sha(post):
        andrat.append('granskningens metod har ändrats (metod %s vid körningens slut, nu %s)' % (_kort(_metod_sha(post)), _kort(metod_nu)))
    sida = post.get('startsida') or {}
    if sida.get('lage') == 'skapandeflödet':
        vin_nu = sha_fil(_vinnare(k))
        provad['vinnare_nu'] = vin_nu
        if vin_nu != sida.get('vinnare_sha256'):
            andrat.append('startsidans godkännande (VINNARE.json) har ändrats sedan körningen')
    # ägarens dom, prövad nu: bara domar som ingen körning kan ha skrivit
    dom_t = agarens_dom(k, post.get('dist_sha256'), ej_belagda_domar(k))
    dom_nu = sha_fil(k / DOMFIL)
    oprovade = [a for a in senare_avbrutna if not a.get('uteblev_protokoll') and a.get('dom_sha256_start') != dom_nu]
    if oprovade and dom_t.get('varde') is not None:
        dom_t = {'varde': None, 'avsandare': EJ_BELAGD, 'kalla': _rel(k, DOMFIL),
                 'text': '%s: DOM.json har ändrats sedan körningen %s startade, och den körningen saknar slutpost (varken kor.sh eller vakten '
                         'skrev någon); bygget kan ha skrivit den. Nästa körning räknar inte domar som tillkom efter att den startade' % (
                             EJ_BELAGD, oprovade[0]['korning'])}
    t['agaren_godkanner'] = dom_t
    if andrat:
        d = post.get('designgranskning') or {}
        if d.get('aktuell'):
            d['historisk'], d['aktuell'] = dict(d['aktuell'], galler_inte_nu=True), None
        d['andrat'] = andrat
        post['designgranskning'] = d
        orsak = '; '.join(andrat)
        for nyckel, vad in (('tekniskt_godkant', 'det tekniska godkännandet'), ('designgranskaren_godkanner', 'granskningen')):
            gammal = t[nyckel]
            t[nyckel] = {'varde': None, 'historik': gammal,
                         'text': 'historik: %s vid körningens slut gällde dist %s och metod %s (%s); %s' % (
                             vad, _kort(post.get('dist_sha256')), _kort(_metod_sha(post)), ORD.get(gammal.get('varde')), orsak)}
        t['klart_for_leverans'] = dict(leverans(t, post.get('slutkod'), k.name), varde=False, text=orsak)
    else:
        t['klart_for_leverans'] = leverans(t, post.get('slutkod'), k.name)
    return post


def _avbruten():
    """Hur körningen avbröts, ur NWP_AVBRUTEN: TERM, INT eller HUP (kor.sh:s fälla) eller KORSH (vakten gjorde avslutet)."""
    x = os.environ.get('NWP_AVBRUTEN')
    return AVBROTT_KORSH if x == 'KORSH' else ('SIG' + x) if x else None


def _slutkod(k, rc, v, mekanik, godkant):
    if mekanik:
        return 3, 'Slutkod 3: mekaniken eller gränsen ändrades under körningen: %s' % ', '.join(mekanik[:20])
    if rc != '0':
        avbruten = _avbruten()
        if avbruten == AVBROTT_KORSH:
            return 4, 'Slutkod 4: körningen avbröts: %s' % avbruten
        return 4, 'Slutkod 4: claude avslutade med kod %s%s' % (rc, ' (körningen avbröts med %s)' % avbruten if avbruten else '')
    if v and v.get('ateljen_forkastad') and v.get('slapp'):
        return 6, 'Slutkod 6: bygget stannade utan sajt (ägarbeslut 2026-10-04): %s; underlaget i underlag/%s/atelje/' % (
            v.get('skal') or 'ateljén förkastade alla riktningar', k.name)
    if godkant:
        return 0, 'Slutkod 0 : tekniskt godkänt och godkänt av designgranskaren; ägarens dom och leveransen återstår'
    return 1, 'Slutkod 1 : avslutat utan grönt prov och godkänd granskning'


def skriv_ut(text_):
    """Skriver beskedet på stdout. En stängd terminal (SIGHUP) eller ett rör utan läsare får aldrig ändra slutkoden: felet
    sväljs, och stdout pekas om till /dev/null, så att Python inte avslutas med kod 120 när bufferten töms (granskningen
    av r101, KAN 1). Ger False när beskedet inte kunde skrivas."""
    try:
        print(text_)
        sys.stdout.flush()
        return True
    except (OSError, ValueError):
        try:
            fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(fd, sys.stdout.fileno())
            os.close(fd)
        except (OSError, ValueError):
            pass
        return False


def main(argv):
    if len(argv) >= 5 and argv[1] == '--stopp':
        post = stopp(argv[2], argv[3], ' '.join(argv[4:]))
        skriv_ut(text(post))
        return 0
    if len(argv) == 4 and argv[1] == '--avbrutna':
        k = Path(argv[2])
        for a in avbrutna(k, utom=argv[3]):
            if not any(f.parent.name > a['korning'] for f in slutposter(k)):  # sagt en gång: en senare post nämner den redan
                skriv_ut('Förra körningen: %s.' % _avbruten_text(a))
        return 0
    if len(argv) in (3, 4) and argv[1] == '--visa':
        post = aktuell(argv[2], argv[3] if len(argv) > 3 else None)
        if not post:
            skriv_ut('\n'.join(['ingen slutpost i %s/korningar/' % argv[2]] + ['Utan slutpost: %s' % _avbruten_text(a) for a in avbrutna(argv[2])]))
            return 1
        skriv_ut(text(post))
        return 0
    k, rc, fore, efter = Path(argv[1]), argv[2], argv[3], argv[4]
    korning = argv[5] if len(argv) > 5 else None
    avbruten = _avbruten()
    s, s_fel = las_objekt(k / 'prov' / 'STATUS.json')
    v, v_fel = las_objekt(k / 'prov' / 'STOPPVAKT.json')
    g, nu_hash, senaste, gfel = vald_granskning(k, korning)
    skydd = andrade(fore, efter)
    f_lista, e_lista = hashlista(fore), hashlista(efter)
    # ägarens domlogg och dom (DOM.json) är låsta under bygget (kor.sh, chflags uchg): en ändring kom inte från dashboarden
    # (omgranskningen, fynd 2; granskningen av r101, B1). Körningarnas slutposter och de flyttade rapporterna är
    # körningarnas protokoll: bygget ändrar dem aldrig (ägarens uppdrag 2026-10-07, punkt 4 och 5). Hashlistorna prövas mot
    # kor.sh:s minne: en lista som ett eget skript skrivit om döljer annars allt detta (GR-20261007-r101-om, BÖR 1)
    dom_rel = 'kunder/%s/%s' % (k.name, DOMFIL)
    listor, lista_fel = hashlistorna(k, fore, efter)
    start_sha = os.environ.get('NWP_DOM_START_SHA256') or None
    domlogg = [f for f in skydd if f.startswith('underlag/') and f.endswith(('/DESIGNDOMAR.jsonl', '/DESIGNDOMAR-belagg.jsonl'))]
    agarfil = [f for f in skydd if f == dom_rel]
    if start_sha and (None if start_sha == 'saknas' else start_sha) != e_lista.get(dom_rel) and dom_rel not in agarfil:
        agarfil.append(dom_rel)  # ändrad enligt kor.sh:s minne, fast hashlistan före säger annat
    protokoll = [f for f in skydd if f.startswith(('kunder/%s/korningar/' % k.name, 'kunder/%s/rapporter/' % k.name,
                                                'kunder/%s/atelje/korningar/' % k.name))]
    mekanik = [f for f in skydd if f.startswith(MEKANIK)] + domlogg + agarfil + protokoll + lista_fel
    godkant, skal = ar_godkant(k, s, v, g, korning)
    slutkod, slutkod_text = _slutkod(k, rc, v, mekanik, godkant)
    processer = processer_efter()
    hinder = [x for x, galler in (
        ('hashlistorna prövades inte mot kor.sh:s minne', listor.get('varde') is None),
        ('hashlistan efter körningen ändrades eller kunde inte skrivas', listor.get('efter_ok') is False),
        ('byggets processer: %s' % processer['text'], processer.get('varde') is not True)) if galler]
    fel, bevis_fel, dom = None, None, None
    try:
        bevis = kopiera_bevis(k, korning) if korning else {}
    except (OSError, ValueError) as e:  # posten skrivs ändå (eller faller nedan med samma skäl); bristen står i den
        bevis, bevis_fel = {}, 'provets och stoppvaktens besked kunde inte kopieras till posten: %s' % str(e)[:200]
    try:
        dom = agaren_vid_slut(k, nu_hash, f_lista.get(dom_rel), e_lista.get(dom_rel), korning=korning, start_sha=start_sha, hinder=hinder)
        _, dom_lasfel = agarens_domar(k)
        vin_fel = las_objekt(_vinnare(k))[1]
        post = slutpost(k, rc, korning, s, v, g, nu_hash, senaste, gfel, skydd, mekanik, domlogg, '' if godkant else skal, slutkod, slutkod_text,
                        dom=dom, lasfel=[s_fel, v_fel, dom_lasfel, ('VINNARE.json: %s' % vin_fel) if vin_fel else None, bevis_fel],
                        bevis=bevis, avbruten=avbruten, processer=processer, listor=listor)
    except Exception as e:  # noqa: BLE001 — slutkoden står kvar; att posten uteblir sägs och får en egen slutkod
        post, fel = None, 'slutposten kunde inte byggas: %s: %s' % (type(e).__name__, str(e)[:300])
    if post is not None and korning:
        try:
            postfil = skriv_slutpost(k, korning, post)
            # Endast kor.sh ger detta privata rör till det betrodda avslutet; byggsessionen ärver det inte.
            # Ingen bekräftelse vid ett skrivfel, och ingen efterhandsbedömning av en fil som bygget kan ha lagt dit.
            if os.environ.get('NWP_VAKT_BEKRAFTA_FD') == '3':
                try:
                    digest = hashlib.sha256(postfil.read_bytes()).hexdigest()
                    os.write(3, ('bekrafta %s\n' % digest).encode('ascii'))
                except OSError:
                    pass  # vakten räknar om ett obekräftat avslut om kor.sh dör
        except (OSError, ValueError) as e:
            post.update(slutpost=None, slutpost_fel=str(e)[:300])
            fel = 'slutposten kunde inte skrivas: %s' % str(e)[:300]
    if fel and korning and slutkod in (0, 1):  # en körning utan post är aldrig godkänd, och backlog_commit publicerar inte
        slutkod, slutkod_text = 5, 'Slutkod 5: slutposten uteblev (%s); körningen räknas inte som avslutad' % fel
        if post is not None:
            post.update(slutkod=slutkod, slutkod_text=slutkod_text)
    if fel and korning:  # nästa start och --visa skiljer en utebliven post från ett avbrott (KAN 6)
        skriv_uteblev(k, korning, fel, slutkod, dom[1] if dom else None)
    if post is not None:
        try:
            ut = '\n' + text(post)
        except Exception as e:  # noqa: BLE001 — beskedet uteblir aldrig helt: skälet och slutkoden skrivs ändå
            ut = '\nbeskedet kunde inte skrivas ur posten: %s: %s\n%s' % (type(e).__name__, str(e)[:200], slutkod_text)
    else:
        ut = '\nclaude avslutade med kod %s\n%s\n%s' % (rc, fel, slutkod_text)
    skriv_ut(ut)
    return slutkod


if __name__ == '__main__':
    if not ((len(sys.argv) >= 5 and sys.argv[1] == '--stopp') or (len(sys.argv) == 4 and sys.argv[1] == '--avbrutna')
            or (len(sys.argv) in (3, 4) and sys.argv[1] == '--visa') or len(sys.argv) in (5, 6)):
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv))
