#!/usr/bin/env python3
"""korslut.py — kor.sh:s avslut: sammanfattar provet, stoppvakten och granskningen, jämför de skyddade filernas
hashlistor före och efter körningen, sätter slutkoden (revisionen 2026-10-03, F10 och F11) och skriver körningens
slutpost (ägarens uppdrag 2026-10-07, punkt 4 och 5).

    .venv/bin/python kontroller/korslut.py <kunder/slug> <claude-kod> <hashlista-fore> <hashlista-efter> <korning>
    .venv/bin/python kontroller/korslut.py --stopp <kunder/slug> <korning> <skäl>   # kor.sh stannade före bygget
    .venv/bin/python kontroller/korslut.py --visa <kunder/slug> [<korning>]         # posten med ägarens dom i dag

Slutkod: 0 provet grönt för just det bygge som ligger i dist/, RAPPORT.md skriven i körningen (samma sha256 som
stoppvakten band och släppte), stoppvakten själv släppte med gröna kontroller och godkänd granskning, och granskningen
gäller samma bygge och samma metod som nu · 1 avslutat utan det (också när en äldre godkänd granskningsfil ligger kvar;
omgång tre, F11) · 3 mekaniken (provet, kriterierna, mallen, krokarna, kor.sh, dashboarden) eller gränsen (en post
tillkom eller försvann direkt under kunder/ eller underlag/, eller flaggan uchg lyftes; kor.sh:s grans(), Codex
2026-10-04 F1), ägarens domlogg, eller körningarnas protokoll (kunder/<slug>/korningar/ och rapporter/) ändrades under
körningen · 4 claude avslutade med annan kod än 0 · 6 bygget stannade utan sajt (ateljén förkastade alla riktningar,
skaparen lämnade grundidén, eller ägaren dömde startsidan efter körningen).
Texterna (kunskap/, LARDOMAR.md, skills) skrivs också av kirurgens intag och ägarens domar i dashboarden medan ett
bygge pågår; ändringar där ger bara en varning. Hela fillistan klassificeras; bara utskriften kapas.

Slutposten kunder/<slug>/korningar/<körning>/SLUT.json binder ihop körningen (NWP_KORNING), bygget (dist_sha256),
metoden (granskningens metod_sha, modell, effort, antal granskare och originalitetsläge; byggets inställningar; repots
commit), den godkända startsidan (kandidat och version ur VINNARE.json), de tekniska kontrollerna, designgranskningen
och vem som gjorde den, ägarens beslut, slutkoden, bristerna, nästa steg (atgarder) och länkarna till rapporter och
bevis (underlag). Rapporthuvudets fält (README.md, Var information finns) står överst i posten, så att den läses som ett
huvud. Fem tillstånd hålls isär: sessionen avslutad, tekniskt godkänt, designgranskaren godkänner, ägaren godkänner och
klart för leverans inom angiven omfattning. Terminalens besked skrivs ur posten (text). Utan körning skrivs ingen post.
En ny post från ett bygge ersätter de tidigare (rapportstatus ersatt, ersatt_av); en kort post från en start som
stannade före bygget ersätter ingen. Ägarens dom kommer efter körningen: aktuell() och --visa prövar den mot posten.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
MEKANIK = ('kontroller/', 'kritik/', 'mall/', '.claude/hooks/', '.claude/settings', 'kor.sh', 'dashboard/', 'dashboard.sh',
           'CLAUDE.md', 'BESLUT.md', '.gitignore', 'syskon:', 'flagga:')
EJ = 'ej angivet'  # ett saknat värde gissas aldrig (README.md, rapporthuvudet)
SLUTPOST = 'SLUT.json'
KORNING_ID = re.compile(r'(?<![0-9A-Za-z])(\d{8}T\d{6}Z)(?![0-9A-Za-z])')  # kor.sh: date -u +%Y%m%dT%H%M%SZ
KORNING_NAMN = re.compile(r'[0-9A-Za-z][0-9A-Za-z_-]{0,63}')  # körningen som katalognamn, aldrig en sökväg
TYP = 'slutpost (kor.sh)'
TYP_STOPP = 'slutpost (kor.sh stannade före bygget)'
UPPDRAG = 'helbygget enligt skillen bygg-sajt, startat med kor.sh'
MOMENT = 'helbygget (README.md, kedjan steg 6)'
AGAREN_JA = 'Ja, som den är'  # kärnfrågan namn i dashboardens Din dom (dashboard/server.py, KARNFRAGOR)
ORD = {True: 'ja', False: 'nej', None: 'ej bedömt'}  # ett tillstånds värde i klartext
TILLSTAND = (('sessionen_avslutad', 'sessionen avslutad'), ('tekniskt_godkant', 'tekniskt godkänt'),
             ('designgranskaren_godkanner', 'designgranskaren godkänner'), ('agaren_godkanner', 'ägaren godkänner'),
             ('klart_for_leverans', 'klart för leverans'))


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def sha_fil(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
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


def korning_start(korning):
    """Körningens start i epoksekunder ur identiteten, eller None när den inte har kor.sh:s form."""
    try:
        return datetime.strptime(str(korning), '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def _iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def rapport_identitet(rapport, korning):
    """Är RAPPORT.md skriven i den här körningen? Ja när rapportens huvud bär körningens identitet (raden korning: i
    rapporthuvudet; bygg-sajt steg 7), eller, utan identitet i huvudet, när filen skrevs efter körningens start. En rapport
    som bär en annan körnings identitet gäller den körningen, och utan körning (NWP_KORNING) går ingen rapport att binda.
    Stoppvakten sparar sha256 och körning för en bunden rapport, och korslut kräver samma sha256 (rapport_giltig).
    Ger {'bunden', 'skal', 'sha256', 'satt' (identitet eller filtid), 'korningar'}."""
    rapport = Path(rapport)
    ut = {'bunden': False, 'sha256': None, 'satt': None, 'korningar': []}
    if rapport.is_symlink():
        return dict(ut, skal='är en symlänk')
    try:
        data = rapport.read_bytes() if rapport.is_file() else None
        mtime = rapport.stat().st_mtime if data is not None else None
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
    start = korning_start(korning)
    if start is None:
        return dict(ut, skal='saknar identitet, och körningens start går inte att läsa ur %s' % korning)
    if mtime >= start:
        return dict(ut, bunden=True, satt='filtid', skal='saknar identitet men skrevs %s, efter körningens start' % _iso(mtime))
    return dict(ut, skal='saknar identitet och skrevs %s, före körningens start %s' % (_iso(mtime), korning))


def rapport_giltig(k, v, korning=None):
    """(ok, skäl): RAPPORT.md är den rapport som stoppvakten band till körningen och släppte (samma sha256, samma körning).
    Saknar stoppvaktens besked en bunden rapport sägs det om rapporten gäller en annan körning eller saknar identitet."""
    rapport = Path(k) / 'RAPPORT.md'
    if not rapport.is_file():
        return False, 'RAPPORT.md saknas'
    v = v if isinstance(v, dict) else {}
    sha = sha_fil(rapport)
    if not v.get('rapport_sha256'):
        try:
            ids = rapport_korningar(rapport.read_text(encoding='utf-8', errors='replace'))
        except OSError:
            ids = []
        andra = [x for x in ids if x != korning]
        if andra and korning not in ids:
            return False, 'RAPPORT.md gäller körning %s, inte %s' % (', '.join(andra), korning or 'den här körningen')
        return False, 'RAPPORT.md saknar identitet: stoppvakten band ingen rapport till körningen (%s)' % (
            v.get('rapport') or ('ingen STOPPVAKT.json' if not v else 'ett besked utan rapportens sha256'))
    if korning and v.get('rapport_korning') != korning:
        return False, 'RAPPORT.md gäller körning %s, inte %s' % (v.get('rapport_korning') or EJ, korning)
    if sha != v['rapport_sha256']:
        return False, 'RAPPORT.md är inte den rapport som stoppvakten släppte (sha256 %s, nu %s)' % (str(v['rapport_sha256'])[:12], str(sha)[:12])
    return True, 'skriven i körningen %s, bunden genom %s, sha256 %s' % (
        v.get('rapport_korning') or EJ, {'identitet': 'identiteten i huvudet', 'filtid': 'filtiden'}.get(v.get('rapport_bunden'), EJ), sha[:12])


def ar_godkant(k, s, v, g, korning=None):
    """Godkänt bara när allt gäller det bygge som ligger i dist/ nu: provet grönt med samma dist-hash som dist/, rapporten
    skriven i körningen (samma sha256 som stoppvakten band och släppte), stoppvakten släppte med gröna kontroller och
    godkänd granskning (inte vid sitt tak), och granskningen är godkänd för samma dist-hash och samma metod som nu (omgång
    tre, F11)."""
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
        return las(gdir / 'GRANSKNING.json'), nu_hash, None, None  # inga omgångar (manuellt underlag): rotfilen är det enda som finns
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


def sessionen(k, korning, rc):
    """Claude-sessionens slut ur körningens logg (kunder/<slug>/korning-<körning>.jsonl): resultat, turer, tid, modell."""
    try:
        kod = int(rc)
    except (TypeError, ValueError):
        kod = rc
    ut = {'varde': kod == 0, 'kod': kod, 'text': 'claude avslutade med kod %s%s' % (kod, '' if kod == 0 else ' (föll)')}
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


def agarens_dom(k, dist):
    """Ägarens senaste dom över just det här bygget ur kunder/<slug>/DOM.json (dashboardens Din dom, bunden med bygge_dist
    till byggets dist_sha256). Godkänner betyder svaret "Ja, som den är" på kärnfrågan namn ("Skulle du sätta ditt namn på
    sajten och visa den för verksamheten?"); "Ja, efter små ändringar" är ett ja med villkor och inget godkännande. Utan
    dom över bygget: ej bedömt."""
    kalla = _rel(k, 'DOM.json')
    if not dist:
        return {'varde': None, 'text': 'inget bygge i dist/ att döma', 'kalla': kalla}
    domar = [d for d in ((las(Path(k) / 'DOM.json') or {}).get('domar') or []) if isinstance(d, dict) and d.get('bygge_dist') == str(dist)[:12]]
    if not domar:
        return {'varde': None, 'kalla': kalla,
                'text': 'ägarens dom skrivs i dashboarden (bygget, fliken Din dom) och binds till dist %s' % str(dist)[:12]}
    d = domar[-1]
    namn = (d.get('svar') or {}).get('namn') if isinstance(d.get('svar'), dict) else None
    varde = None if not namn else namn == AGAREN_JA
    return {'varde': varde, 'kalla': kalla, 'tid': d.get('tid'), 'avsandare': 'ägaren (dashboardens Din dom)',
            'text': 'dom %s, kärnfrågan namn: %s' % (d.get('tid') or EJ, namn or 'obesvarad')}


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


def startsidan(k):
    """Den godkända startsida bygget utgick från: kandidat och version ur underlag/<slug>/atelje/VINNARE.json (fältet
    godkand) och om godkännandet gäller nu (skapande.godkand_giltig). På nödvägen (NWP_ATELJE annat än pa) byggde
    byggaren sitt eget koncept."""
    k = Path(k)
    lage = os.environ.get('NWP_ATELJE') or 'pa'
    if lage != 'pa':
        return {'lage': 'nödvägen (NWP_ATELJE=%s)' % lage, 'text': 'nödvägen utan skapandeflödet: byggarens egen KONCEPT.md och DESIGN.md'}
    rot = k.resolve().parent.parent
    vin = rot / 'underlag' / k.name / 'atelje' / 'VINNARE.json'
    g = (las(vin) or {}).get('godkand')
    if not isinstance(g, dict) or not g.get('tid'):
        return {'lage': 'skapandeflödet', 'text': 'inget godkännande i underlag/%s/atelje/VINNARE.json' % k.name}
    ut = {'lage': 'skapandeflödet', 'vinnare': 'underlag/%s/atelje/VINNARE.json' % k.name, 'godkand': g.get('tid'), 'av': g.get('av'),
          'kandidat': g.get('kandidat'), 'version': g.get('version'), 'sha_index': g.get('sha_index'), 'sha_design': g.get('sha_design')}
    try:
        import skapande
        ok, skal = skapande.godkand_giltig(k.name, underlag=rot / 'underlag', kunder=rot / 'kunder')
        ut['giltig_nu'] = {'varde': bool(ok), 'text': skal}
    except Exception as e:  # noqa: BLE001 — prövningen är information, aldrig ett fel i avslutet
        ut['giltig_nu'] = {'varde': None, 'text': 'kunde inte prövas: %s' % str(e)[:160]}
    ut['text'] = 'godkänd startsida %s (%s%s)' % (g.get('tid'), ('kandidat %s, version %s' % (g.get('kandidat'), _kort(g.get('version'))))
                                                 if g.get('kandidat') else 'startsidan sha256 %s' % _kort(g.get('sha_index')),
                                                 ', ägaren via %s' % g.get('av') if g.get('av') and g.get('av') != 'ägaren' else '')
    return ut


def foregaende(k, korning):
    """Den senaste tidigare slutposten, som text för rapporthuvudets fält foregaende."""
    tidigare = [f for f in slutposter(k) if f.parent.name < korning]
    if not tidigare:
        return EJ
    p = las(tidigare[-1]) or {}
    return '%s (%s)' % (p.get('id') or tidigare[-1].parent.name, _rel(k, 'korningar', tidigare[-1].parent.name, SLUTPOST))


def _granskningsrad(g, nu_hash):
    return {'godkand': bool(g.get('godkand')), 'omgang': g.get('runda'), 'korning': g.get('korning'), 'dist_sha256': g.get('dist_sha256'),
            'samma_bygge': bool(nu_hash) and g.get('dist_sha256') == nu_hash, 'metod_sha': g.get('metod_sha'), 'modell': g.get('modell'),
            'effort': g.get('effort'), 'granskare': g.get('granskare'), 'originalitet': g.get('originalitet'), 'tid': g.get('tid'),
            'betyg': {n: (x or {}).get('betyg') for n, x in (g.get('kriterier') or {}).items() if isinstance(x, dict)}}


def slutpost(k, rc, korning, s, v, g, nu_hash, senaste, gfel, skydd, mekanik, domlogg, skal_ej, slutkod, slutkod_text):
    """Körningens slutpost: rapporthuvudets fält, de fem tillstånden var för sig, kontrollerna, granskningen, metoden,
    startsidan, bristerna, nästa steg och länkarna. Bara uppgifter som avslutet har; det som saknas står som ej angivet."""
    k = Path(k)
    slug = k.name
    tid = nu()
    # tekniska kontroller: provet, stoppvakten, rapporten och mekaniken
    grindar = {n: bool((x or {}).get('ok') if isinstance(x, dict) else x) for n, x in ((s or {}).get('grindar') or {}).items()}
    provet = {'finns': bool(s), 'gront': bool(s and s.get('ok')), 'grindar': grindar, 'dist_sha256': (s or {}).get('dist_sha256'),
              'tid': (s or {}).get('tid'), 'vinnare': ((s or {}).get('info') or {}).get('vinnare')}
    provet['varde'] = provet['gront'] and bool(nu_hash) and provet['dist_sha256'] == nu_hash
    provet['text'] = ('kördes aldrig (inget STATUS.json)' if not s else 'RÖTT' if not s.get('ok') else 'GRÖNT, men inget bygge i dist/'
                      if not nu_hash else 'GRÖNT för bygget i dist/' if provet['varde'] else 'GRÖNT men för ett annat bygge än det i dist/')
    sv = v if isinstance(v, dict) else {}
    stopp_ok = bool(sv.get('slapp')) and (sv.get('kontroller_grona') is True or str(sv.get('skal') or '').startswith('kontrollerna gröna'))
    stoppvakten = {'finns': bool(v), 'skal': sv.get('skal'), 'forsok': sv.get('forsok'), 'tak': sv.get('tak'), 'korning': sv.get('korning'),
                   'dist_sha256': sv.get('dist_sha256'), 'slapp': sv.get('slapp'), 'granskning': sv.get('granskning')}
    stoppvakten['varde'] = stopp_ok and (not korning or sv.get('korning') == korning) and bool(nu_hash) and sv.get('dist_sha256') == nu_hash
    stoppvakten['text'] = ('inget besked (STOPPVAKT.json saknas)' if not v else
                           'besked från en annan körning (%s)' % sv.get('korning') if korning and sv.get('korning') != korning else
                           'inget bygge i dist/' if not nu_hash else
                           'besked om ett annat bygge än det i dist/' if sv.get('dist_sha256') != nu_hash else
                           'släppte med gröna kontroller' if stopp_ok else 'släppte inte med gröna kontroller (%s)' % (sv.get('skal') or EJ))
    r_ok, r_skal = rapport_giltig(k, v, korning)
    rapporten = {'fil': _rel(k, 'RAPPORT.md'), 'finns': (k / 'RAPPORT.md').is_file(), 'varde': r_ok, 'text': r_skal,
                 'sha256': sv.get('rapport_sha256'), 'korning': sv.get('rapport_korning'), 'satt': sv.get('rapport_bunden')}
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
        aktuell_g = g if (g and not gfel and nu_hash and g.get('dist_sha256') == nu_hash and granska.samma_metod(g, metod)) else None
    except Exception as e:  # noqa: BLE001
        metod, aktuell_g = {'fel': str(e)[:200]}, None
    historisk = senaste if senaste and (not aktuell_g or senaste.get('runda') != aktuell_g.get('runda')) else (
        g if g and not gfel and not aktuell_g else None)
    if not aktuell_g and not historisk and not gfel and (k / 'granskning').is_dir():
        try:  # en giltig omgång i en tidigare körning är också historik, aldrig en dom över körningens bygge
            alla = granska.valj_sammanfattning(k / 'granskning', None, None)
            historisk = alla[1] if alla else None
        except Exception:  # noqa: BLE001 — historiken är information; en oläsbar omgång nekar redan ovan
            historisk = None
    design = {'fel': gfel, 'aktuell': _granskningsrad(aktuell_g, nu_hash) if aktuell_g else None,
              'historisk': _granskningsrad(historisk, nu_hash) if historisk else None, 'dist_nu': nu_hash,
              'avstangd': sv.get('granskning') == 'avstängd'}
    if aktuell_g:
        a = design['aktuell']
        design['vem'] = '%s granskare, %s %s, originalitet %s' % (a['granskare'] or EJ, a['modell'] or EJ, a['effort'] or EJ, a['originalitet'] or EJ)
    if gfel:
        dg = {'varde': False, 'text': 'omgångarna kunde inte läsas eller valideras: %s' % gfel}
    elif aktuell_g:
        dg = {'varde': bool(aktuell_g.get('godkand')), 'vem': design['vem'], 'omgang': aktuell_g.get('runda'),
              'text': 'omgång %s, dist %s = slutliga bygget, aktuell metod; %s' % (aktuell_g.get('runda'), _kort(aktuell_g.get('dist_sha256')), design['vem'])}
    else:
        dg = {'varde': None, 'text': 'granskningen var avstängd (NWP_GRANSKNING=av)' if design['avstangd'] else
              'ingen giltig omgång för det slutliga bygget %s med aktuell metod' % _kort(nu_hash)}
        if historisk:
            dg['historisk'] = 'omgång %s, dist %s%s, %s: historik, gäller inte det slutliga bygget och den aktuella metoden' % (
                historisk.get('runda'), _kort(historisk.get('dist_sha256')), '' if design['historisk']['samma_bygge'] else ' ≠ slutliga bygget',
                'godkänd' if historisk.get('godkand') else 'underkänd')
            dg['text'] += '; senaste dom är historik (%s)' % dg['historisk']
    tillstand = {'sessionen_avslutad': sessionen(k, korning, rc), 'tekniskt_godkant': tekniskt, 'designgranskaren_godkanner': dg,
                 'agaren_godkanner': agarens_dom(k, nu_hash)}
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
    utfall = {0: 'godkänt av korslut (slutkod 0): tekniskt godkänt och designgranskaren godkänner; ägaren godkänner: %s (%s)' % (
        ORD[tillstand['agaren_godkanner']['varde']], tillstand['agaren_godkanner']['text']),
              1: '%s av korslut (slutkod 1): %s' % ('underkänt' if underkant else 'ofullständigt', skal_ej or EJ),
              3: 'ofullständigt (slutkod 3): mekaniken eller gränsen ändrades under körningen; inget av proven gäller',
              4: 'ofullständigt (slutkod 4): claude avslutade med kod %s' % rc,
              6: 'ofullständigt (slutkod 6): bygget stannade utan sajt (%s)' % (sv.get('skal') or EJ)}[slutkod]
    brister = [x for x in [
        None if tillstand['sessionen_avslutad']['varde'] else tillstand['sessionen_avslutad']['text'],
        None if tekniskt['varde'] else 'tekniskt: %s' % tekniskt['text'],
        None if dg['varde'] is True else 'designgranskningen: %s' % dg['text'],
        'skyddade texter ändrades under körningen: %s' % ', '.join(x for x in skydd[:10] if x not in mekanik) if [x for x in skydd if x not in mekanik] else None,
        ('inte godkänt: %s' % skal_ej) if skal_ej else None] if x]
    atgarder = {0: ['ägaren dömer bygget i dashboarden (bygget, fliken Din dom); domen binds till dist %s' % _kort(nu_hash),
                    'efter ägarens godkännande: exporten, .venv/bin/python kontroller/exportera.py %s (kunskap/lansering.md)' % slug],
                1: ['läs bristerna, rapporten och provets PROV.md; rätta och kör ./kor.sh %s "<verksamhet>" igen' % slug],
                3: ['granska ändringarna i mekaniken (listan i posten) innan något av byggets resultat används'],
                4: ['läs körningens logg %s och starta om ./kor.sh %s "<verksamhet>"' % (_rel(k, 'korning-%s.jsonl' % korning), slug)],
                6: ['skapandeflödet före ett nytt bygge: .venv/bin/python kontroller/prototyp.py %s (underlag/%s/atelje/)' % (slug, slug)]}[slutkod]
    if slutkod == 1 and dg['varde'] is None and sv.get('tak_skal'):
        atgarder.append('en ny granskningsomgång behövs: %s' % sv['tak_skal'])
    underlag = [x for x in [_rel(k, 'korning-%s.jsonl' % korning) if korning and (k / ('korning-%s.jsonl' % korning)).is_file() else None,
                            _rel(k, 'prov', 'STATUS.json') if s else None, _rel(k, 'prov', 'PROV.md') if (k / 'prov' / 'PROV.md').is_file() else None,
                            _rel(k, 'prov', 'STOPPVAKT.json') if v else None,
                            _rel(k, 'granskning', 'runda-%02d' % int(aktuell_g['runda']), 'GRANSKNING.json')
                            if aktuell_g and str(aktuell_g.get('runda') or '').isdigit() and (k / 'granskning' / ('runda-%02d' % int(aktuell_g['runda']))).is_dir() else None,
                            _rel(k, 'RAPPORT.md') if rapporten['finns'] else None, _rel(k, 'FRAGOR.json') if (k / 'FRAGOR.json').is_file() else None,
                            sida.get('vinnare'), 'underlag/%s/atelje/STARTKVITTO-BYGGE.md' % slug
                            if (k.resolve().parent.parent / 'underlag' / slug / 'atelje' / 'STARTKVITTO-BYGGE.md').is_file() else None] if x]
    beslut = [x for x in [('ägarens godkännande av startsidan %s (%s)' % (sida['godkand'], sida['vinnare'])) if sida.get('godkand') else None,
                          ('ägarens dom över bygget %s (%s)' % (tillstand['agaren_godkanner'].get('tid'), tillstand['agaren_godkanner']['kalla']))
                          if tillstand['agaren_godkanner'].get('tid') else None] if x]
    post = {'schema': 1, 'id': 'SLUT-%s-%s' % (slug, korning or EJ), 'titel': 'Slutbesked för helbygget %s, körningen %s' % (slug, korning or EJ),
            'typ': TYP, 'uppdrag': UPPDRAG, 'kund': slug, 'moment': MOMENT, 'forfattare': 'kontroller/korslut.py (kor.sh:s avslut)',
            'datum': tid, 'granskad_identitet': ident, 'rapportstatus': 'färdig', 'bedomningsutfall': utfall,
            'foregaende': foregaende(k, korning) if korning else EJ, 'ersatt_av': EJ, 'underlag': underlag, 'beslut': beslut or EJ,
            'atgarder': atgarder, 'korning': korning, 'dist_sha256': nu_hash, 'slutkod': slutkod, 'slutkod_text': slutkod_text,
            'tillstand': tillstand, 'kontroller': {'provet': provet, 'stoppvakten': stoppvakten, 'rapporten': rapporten, 'mekaniken': mek},
            'designgranskning': design, 'metod': {'granskning': metod, 'bygget': bygget, 'repo': repo}, 'startsida': sida,
            'brister': brister, 'inte_godkant': skal_ej or None, 'titta': 'cd %s && npx astro preview' % _rel(k, 'sajt')}
    return post


def _granskningstext(post):
    d = post['designgranskning']
    r = []
    if d.get('fel'):
        r.append('Granskningen: omgångarna kunde inte läsas eller valideras, inget godkännande: %s' % d['fel'])
    elif d.get('aktuell'):
        a = d['aktuell']
        r.append('Granskningen: %s (omgång %s, dist %s = slutliga bygget, aktuell metod) — %s' % (
            'GODKÄND' if a['godkand'] else 'UNDERKÄND', a['omgang'], _kort(a['dist_sha256']),
            ', '.join('%s %s' % (n, b) for n, b in (a.get('betyg') or {}).items())))
    else:
        r.append('Granskningen: %s; slutliga bygget är inte granskat' % (
            'avstängd (NWP_GRANSKNING=av)' if d.get('avstangd') else 'ingen giltig omgång för det slutliga bygget %s med aktuell metod' % _kort(d.get('dist_nu'))))
    h = d.get('historisk')
    if h:
        r.append('Senaste dom oavsett bygge och metod: %s (omgång %s, dist %s%s)' % ('godkänd' if h['godkand'] else 'underkänd', h['omgang'],
                                                                                 _kort(h['dist_sha256']), '' if h['samma_bygge'] else ' ≠ slutliga bygget'))
    return r


def text(post):
    """Terminalens besked, skrivet ur slutposten och ingenting annat (ägarens uppdrag 2026-10-07, punkt 4)."""
    if post.get('typ') == TYP_STOPP:
        return '\n'.join([str(post.get('skal') or EJ), 'Slutpost: %s' % (post.get('slutpost') or 'skrevs inte: %s' % post.get('slutpost_fel', EJ)), post['slutkod_text']])
    t, kn = post['tillstand'], post['kontroller']
    r = ['claude avslutade med kod %s' % t['sessionen_avslutad'].get('kod')]
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
    for a in post.get('atgarder') or []:
        r.append('Nästa steg: %s' % a)
    r.append('Slutpost: %s' % (post.get('slutpost') or ('skrevs inte: %s' % post['slutpost_fel'] if post.get('slutpost_fel')
                                                     else 'skrevs inte (ingen körning angiven)')))
    r.append(post['slutkod_text'])
    return '\n'.join(r)


def slutposter(k):
    """Körningarnas slutposter för kunden, äldst först (körningens identitet sorterar som tid)."""
    d = Path(k) / 'korningar'
    if d.is_symlink() or not d.is_dir():
        return []
    return sorted((f for f in d.glob('*/' + SLUTPOST) if not f.is_symlink() and not f.parent.is_symlink()), key=lambda f: f.parent.name)


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
    tmp = fil.with_name('.%s.tmp%d' % (fil.name, os.getpid()))
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, fil)


def skriv_slutpost(k, korning, post, ersatt=True):
    """Skriver kunder/<slug>/korningar/<körning>/SLUT.json atomiskt och ger filen. En post från ett bygge (ersatt) märker
    de tidigare, ännu gällande posterna som ersatta; deras uppgifter i övrigt ändras inte. Ingen länk följs."""
    k = Path(k)
    if not KORNING_NAMN.fullmatch(str(korning or '')):
        raise ValueError('körningen %r är ingen giltig identitet' % (korning,))
    for d in (k, k / 'korningar', k / 'korningar' / korning):
        if d.is_symlink():
            raise OSError('%s är en symlänk; slutposten skrivs inte' % d)
    d = k / 'korningar' / korning
    d.mkdir(parents=True, exist_ok=True)
    post['slutpost'] = _rel(k, 'korningar', korning, SLUTPOST)
    _skriv_json(d / SLUTPOST, post)
    if ersatt:
        for f in slutposter(k):
            if f.parent.name >= korning:
                continue
            p = las(f)
            if isinstance(p, dict) and p.get('ersatt_av') in (None, EJ):
                p.update(rapportstatus='ersatt', ersatt_av='%s (%s)' % (post['id'], post['slutpost']), ersatt_tid=post['datum'])
                _skriv_json(f, p)
    return d / SLUTPOST


def stopp(k, korning, skal):
    """kor.sh stannade före bygget (slutkod 2): en kort post med skälet. Den ersätter ingen post, eftersom bygget i dist/
    inte ändrades; den föregående posten beskriver det."""
    k = Path(k)
    tid = nu()
    post = {'schema': 1, 'id': 'SLUT-%s-%s' % (k.name, korning), 'titel': 'Slutbesked: kor.sh stannade före bygget, körningen %s' % korning,
            'typ': TYP_STOPP, 'uppdrag': UPPDRAG, 'kund': k.name, 'moment': MOMENT, 'forfattare': 'kontroller/korslut.py (kor.sh)', 'datum': tid,
            'granskad_identitet': ['körning %s' % korning], 'rapportstatus': 'färdig',
            'bedomningsutfall': 'ej bedömt (slutkod 2): bygget startade inte; %s' % skal, 'foregaende': foregaende(k, korning), 'ersatt_av': EJ,
            'underlag': [x for x in [_rel(k, 'startkontroll.log') if 'startkontroll' in skal and (k / 'startkontroll.log').is_file() else None,
                                     'underlag/%s/atelje/STARTKVITTO-BYGGE-STOPP.md' % k.name if 'startkontroll' in skal else None] if x] or EJ,
            'beslut': EJ, 'atgarder': ['rätta det som stoppade starten (skälet) och starta ./kor.sh %s "<verksamhet>" igen' % k.name],
            'korning': korning, 'slutkod': 2, 'slutkod_text': 'Slutkod 2: bygget startade inte; kor.sh stannade före bygget', 'skal': skal,
            'tillstand': {'sessionen_avslutad': {'varde': None, 'text': 'ingen session startades'},
                          'tekniskt_godkant': {'varde': None, 'text': 'inget nytt bygge att pröva'},
                          'designgranskaren_godkanner': {'varde': None, 'text': 'inget nytt bygge att granska'},
                          'agaren_godkanner': {'varde': None, 'text': 'inget nytt bygge att döma; bygget i dist/ beskrivs av föregående post'},
                          'klart_for_leverans': {'varde': False, 'text': 'bygget startade inte', 'omfattning': EJ}},
            'brister': [skal]}
    try:
        skriv_slutpost(k, korning, post, ersatt=False)
    except (OSError, ValueError) as e:
        post.update(slutpost=None, slutpost_fel=str(e)[:300])
    return post


def aktuell(k, korning=None):
    """Slutposten prövad nu, utan att posten på disk ändras: ägarens dom över postens bygge (DOM.json), klart för
    leverans, om dist/ fortfarande är postens bygge och om en senare post finns. Ger None utan post."""
    k = Path(k)
    if korning:
        if not KORNING_NAMN.fullmatch(korning):
            return None
        fil = k / 'korningar' / korning / SLUTPOST
        post = las(fil) if not fil.is_symlink() else None
    else:
        fil, post = senaste_slutpost(k)
    if not isinstance(post, dict):
        return None
    post = json.loads(json.dumps(post))
    dist = k / 'sajt' / 'dist'
    try:
        import prova
        nu_hash = prova.dist_hash(dist) if (dist / 'index.html').is_file() else None
    except Exception:  # noqa: BLE001
        nu_hash = None
    senare = [f.parent.name for f in slutposter(k) if f.parent.name > str(post.get('korning'))]
    post['provad'] = {'tid': nu(), 'dist_nu': nu_hash, 'samma_bygge': bool(nu_hash) and nu_hash == post.get('dist_sha256'),
                      'senare_poster': senare}
    t = post.get('tillstand') or {}
    if post.get('typ') == TYP and all(n in t for n, _ in TILLSTAND):
        t['agaren_godkanner'] = agarens_dom(k, post.get('dist_sha256'))
        if not post['provad']['samma_bygge']:
            t['agaren_godkanner']['text'] += '; bygget i dist/ är inte längre postens (dist %s)' % _kort(nu_hash)
        t['klart_for_leverans'] = leverans(t, post.get('slutkod'), k.name)
        if not post['provad']['samma_bygge']:
            t['klart_for_leverans'].update(varde=False, text='bygget i dist/ har ändrats efter körningen')
    return post


def main(argv):
    if len(argv) >= 5 and argv[1] == '--stopp':
        post = stopp(argv[2], argv[3], ' '.join(argv[4:]))
        print(text(post))
        return 0
    if len(argv) in (3, 4) and argv[1] == '--visa':
        post = aktuell(argv[2], argv[3] if len(argv) > 3 else None)
        if not post:
            print('ingen slutpost i %s/korningar/' % argv[2])
            return 1
        print(text(post))
        return 0
    k, rc, fore, efter = Path(argv[1]), argv[2], argv[3], argv[4]
    korning = argv[5] if len(argv) > 5 else None
    s, v = las(k / 'prov' / 'STATUS.json'), las(k / 'prov' / 'STOPPVAKT.json')
    g, nu_hash, senaste, gfel = vald_granskning(k, korning)
    skydd = andrade(fore, efter)
    # ägarens domlogg är låst under bygget (kor.sh, chflags uchg): en ändring kom inte från dashboarden (omgranskningen,
    # fynd 2: loggen räknades som text och gav bara en varning). Körningarnas slutposter och de flyttade rapporterna är
    # körningarnas protokoll: bygget ändrar dem aldrig (ägarens uppdrag 2026-10-07, punkt 4 och 5)
    domlogg = [f for f in skydd if f.startswith('underlag/') and f.endswith('/DESIGNDOMAR.jsonl')]
    protokoll = [f for f in skydd if f.startswith(('kunder/%s/korningar/' % k.name, 'kunder/%s/rapporter/' % k.name))]
    mekanik = [f for f in skydd if f.startswith(MEKANIK)] + domlogg + protokoll
    godkant, skal = ar_godkant(k, s, v, g, korning)
    if mekanik:
        slutkod, slutkod_text = 3, 'Slutkod 3: mekaniken eller gränsen ändrades under körningen: %s' % ', '.join(mekanik[:20])
    elif rc != '0':
        slutkod, slutkod_text = 4, 'Slutkod 4: claude avslutade med kod %s' % rc
    elif v and v.get('ateljen_forkastad') and v.get('slapp'):
        slutkod, slutkod_text = 6, 'Slutkod 6: bygget stannade utan sajt (ägarbeslut 2026-10-04): %s; underlaget i underlag/%s/atelje/' % (
            v.get('skal') or 'ateljén förkastade alla riktningar', k.name)
    else:
        slutkod = 0 if godkant else 1
        slutkod_text = 'Slutkod %d : %s' % (slutkod, 'godkänt bygge' if godkant else 'avslutat utan grönt prov och godkänd granskning')
    post = slutpost(k, rc, korning, s, v, g, nu_hash, senaste, gfel, skydd, mekanik, domlogg, '' if godkant else skal, slutkod, slutkod_text)
    if korning:
        try:
            skriv_slutpost(k, korning, post)
        except (OSError, ValueError) as e:  # en post som inte går att skriva ändrar aldrig slutkoden; det sägs högt
            post.update(slutpost=None, slutpost_fel=str(e)[:300])
    print('\n' + text(post))
    return slutkod


if __name__ == '__main__':
    if not ((len(sys.argv) >= 5 and sys.argv[1] == '--stopp') or (len(sys.argv) in (3, 4) and sys.argv[1] == '--visa') or len(sys.argv) in (5, 6)):
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv))
