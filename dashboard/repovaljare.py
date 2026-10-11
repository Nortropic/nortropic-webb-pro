#!/usr/bin/env python3
"""repovaljare.py — repoväljaren i fliken Ändringar (ägarens tillägg 2026-10-11; kunskap/andringar.md, Repoväljaren).

Nortropics kundrepon i organisationen på GitHub (kundrepo.ORG) i en sökbar lista som öppnas i ändringsfliken, ungefär
som VS Codes Clone Repository och Open Recent men bara för kundrepona. Det betrodda lagret hämtar listan med gh som det
är inloggat (ägarens konto) och klonar, hämtar och uppdaterar; agenten får aldrig inloggningen, och här frågas aldrig
efter en token:

- bindningen repo–kund kommer ur kundernas kvitton: det bundna fjärrepot (kundrepo.bunden_adress) och projekt-id, som
  repots beskrivning bär som markör (kundrepo.MARKOR). Ett repo gissas aldrig ur namnet; ett namnförslag kräver Johnnys
  val, och ett repo utan markör binds inte (samma regel som när kundrepot skapas, kundrepo.fjarr_skapa);
- klonen går med gh till kunder/<slug>/kundrepo och ingen annanstans, och förkontrollen i Ändringar prövar den efteråt;
- hämta är git fetch utan sammanfogning, med läget före och efter; uppdatera är bara fast-forward till standardgrenen, på
  en ren arbetskopia som står på standardgrenen, under kundens lås (flodesstart.las). Inget reset, stash, rebase,
  tvingad pull eller rensning, och ingen annan gren väljs;
- "Senast öppnade" står i underlag/repovaljaren/SENAST.json och överlever en omstart.

Inget nytt kundregister: listan är organisationens repon och kundernas befintliga kvitton. En fiktiv verksamhet får
aldrig ett fjärrepo. Ändringsflikens sandlåda, krokar och lås gäller oförändrade för varje valt repo.
"""
import json
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kontroller'))

SENAST_MAX = 12
LISTTID = 120          # sekunder som organisationens lista återanvänds; "Läs om" hämtar den direkt
FELTID = 10            # ett misslyckat försök återanvänds kort, så att en vy som läser om inte hamrar på GitHub
FALT = 'name,nameWithOwner,description,pushedAt,defaultBranchRef,isPrivate,isArchived,url'
NAMN = re.compile(r'^[A-Za-z0-9._-]{1,100}$')
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
MARKOR = re.compile(r'nortropic-projekt:([0-9a-f]{32})\b')
LAS = threading.Lock()
CACHE = {'tid': 0.0, 'svar': None}


def _m():
    import andringar
    import atelje
    import kundrepo
    return atelje, kundrepo, andringar


def _nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def _git(r, *args, frist=60):
    atelje, kundrepo, andringar = _m()
    return kundrepo.git(r, *andringar.SAKER_GIT, *args, frist=frist)


def _ut(res):
    return res.stdout.strip() if res.returncode == 0 else None


def normaliserad(url):
    """En fjärradress i https-form utan .git och snedstreck, så att ssh- och https-kloner jämförs lika. Adressen läses
    ur konfigurationen (remote.origin.url), inte med get-url, som skriver om den med gits insteadOf-regler."""
    u = re.sub(r'^git@github\.com:', 'https://github.com/', str(url or '').strip())
    return re.sub(r'\.git$', '', u).rstrip('/')


# --- inloggningen ---

GH_LOGIN = 'Kör `gh auth login` i Terminal (GitHub.com, logga in med webbläsaren) och läs sedan om listan här. Appen frågar aldrig efter en token.'


def inloggningsfel(text):
    """gh:s felutskrift som ett besked: {slag, besked, atgard}. Ordningen spelar roll: en utgången token nämner också
    gh auth login."""
    t = str(text or '').lower()
    if 'saml' in t:
        return {'slag': 'sso', 'besked': 'GitHub kräver att inloggningen godkänns för organisationen %s (SAML).' % _m()[1].ORG,
                'atgard': 'Kör `gh auth refresh -h github.com` i Terminal och godkänn organisationen i webbläsaren; läs sedan om listan.'}
    if 'http 401' in t or 'bad credentials' in t or ('token' in t and ('invalid' in t or 'expired' in t)):
        return {'slag': 'utgangen', 'besked': 'Inloggningen till GitHub har gått ut eller är ogiltig.', 'atgard': GH_LOGIN}
    if 'gh auth login' in t or 'not logged' in t or 'gh_token' in t:
        return {'slag': 'saknas', 'besked': 'gh är inte inloggat på GitHub.', 'atgard': GH_LOGIN}
    if 'read:org' in t or 'required scopes' in t:
        return {'slag': 'behorighet', 'besked': 'Inloggningen saknar rätten att läsa organisationens repon.',
                'atgard': 'Kör `gh auth refresh -h github.com -s read:org` i Terminal och läs sedan om listan.'}
    if any(x in t for x in ('could not resolve', 'no such host', 'connection refused', 'timed out', 'timeout', 'tidsgränsen',
                            'error connecting', 'dial tcp', 'network is unreachable')):
        return {'slag': 'natfel', 'besked': 'GitHub gick inte att nå.',
                'atgard': 'Kontrollera nätverket och läs om listan. Arbetskopiorna på datorn och Senast öppnade fungerar utan nät.'}
    return {'slag': 'fel', 'besked': 'Listan från GitHub gick inte att hämta: %s' % str(text or '').strip()[-200:],
            'atgard': 'Läs om listan. Står felet kvar: kör `gh auth status` i Terminal.'}


def _org_repon(las_om=False):
    """Organisationens kundrepon ur gh: {ok, repon, hamtad, inloggning, arkiverade}. Bara organisationens egna repon
    (ägaren i nameWithOwner), bara kundrepon (kund-<namn> eller projektets markör), inga förhandsvisningar."""
    atelje, kundrepo, _ = _m()
    with LAS:
        s = CACHE['svar']
        if s and not las_om and time.time() - CACHE['tid'] < (LISTTID if s['ok'] else FELTID):
            return s
    gh = shutil.which('gh')
    if not gh:
        svar = {'ok': False, 'repon': [], 'inloggning': {'slag': 'gh_saknas', 'besked': 'GitHub CLI (gh) finns inte på datorn.',
                                                          'atgard': 'gh hör till verktygslådan (kunskap/beroenden.md); startkontrollen säger vad som saknas.'}}
    else:
        r = kundrepo.kommando([gh, 'repo', 'list', kundrepo.ORG, '--limit', '1000', '--json', FALT], atelje.ROOT, frist=60)
        try:
            data = json.loads(r.stdout) if r.returncode == 0 else None
        except ValueError:
            data = None
        if not isinstance(data, list):
            svar = {'ok': False, 'repon': [], 'inloggning': inloggningsfel((r.stderr or '') + ' ' + (r.stdout or '')[:300])}
        else:
            repon, arkiverade = [], 0
            for x in data:
                if not isinstance(x, dict) or not NAMN.match(str(x.get('name') or '')):
                    continue
                agare = str(x.get('nameWithOwner') or '').split('/')[0]
                if agare.lower() != kundrepo.ORG.lower() or str(x['name']).endswith('-forhandsvisning'):
                    continue  # en främmande organisation syns aldrig, också om källan skulle ge den
                if not (str(x['name']).startswith('kund-') or MARKOR.search(str(x.get('description') or ''))):
                    continue  # motorns egna repon och annat i organisationen är inga kundrepon
                if x.get('isArchived'):
                    arkiverade += 1
                    continue
                repon.append(x)
            # synliga: organisationens repon som inloggningen ser, kundrepon eller inte (en tom lista skiljs från en
            # organisation utan kundrepon än)
            synliga = sum(1 for x in data if isinstance(x, dict) and str(x.get('nameWithOwner') or '').split('/')[0].lower() == kundrepo.ORG.lower())
            svar = {'ok': True, 'repon': repon, 'hamtad': _nu(), 'arkiverade': arkiverade, 'synliga': synliga, 'inloggning': {'slag': 'ok'}}
    with LAS:
        CACHE.update(tid=time.time(), svar=svar)
    return svar


# --- bindningen och arbetskopiornas läge ---

def _bindningar():
    """Ur kundernas kvitton: {repo-namn (gemener): [slug]} för bundna fjärrepon och {projekt-id: [slug]}."""
    atelje, kundrepo, _ = _m()
    via_namn, via_projekt = {}, {}
    if not atelje.KUNDER.is_dir():
        return via_namn, via_projekt
    for d in sorted(atelje.KUNDER.iterdir()):
        slug = d.name
        if not SLUG.match(slug) or slug.endswith('-forhandsvisning') or d.is_symlink():
            continue
        kv = kundrepo.las_kvitto(slug)
        if not kv:
            continue
        if ((kv.get('fjarr') or {}).get('status')) == 'skapat':
            via_namn.setdefault(kundrepo.bunden_adress(slug, kv).rsplit('/', 1)[1].lower(), []).append(slug)
        if re.fullmatch(r'[0-9a-f]{32}', str(kv.get('projekt_id') or '')):
            via_projekt.setdefault(kv['projekt_id'], []).append(slug)
    return via_namn, via_projekt


def _kundnamn(slug):
    _, kundrepo, _ = _m()
    return str(kundrepo.verksamhet(slug).get('namn') or slug)


def kopplingsbara():
    """Befintliga kunder som ett okopplat repo kan kopplas till: en verksamhet i underlaget, inte fiktiv, utan kvitto
    (då hör kunden ännu inte till något projekt-id) och utan arbetskopia."""
    atelje, kundrepo, _ = _m()
    ut = []
    if not atelje.UNDERLAG.is_dir():
        return ut
    for d in sorted(atelje.UNDERLAG.iterdir()):
        slug = d.name
        if (not SLUG.match(slug) or slug.endswith('-forhandsvisning') or d.is_symlink() or not (d / 'VERKSAMHET.json').is_file()
                or kundrepo.fiktiv(slug) or kundrepo.las_kvitto(slug) or kundrepo.repo(slug).exists()):
            continue
        ut.append({'slug': slug, 'namn': _kundnamn(slug)})
    return ut


def standardgren(r):
    g = _ut(_git(r, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD'))
    return g.split('/', 1)[1] if g and '/' in g else 'main'


def arbetskopians_lage(slug, std=None):
    """Arbetskopians läge utan nät, ur det senast hämtade: gren, standardgren, lokala ändringar, före och efter
    origin/<standardgren> och när fjärren senast hämtades. lage: i takt, före, efter, isär, ej hämtat eller lokala
    ändringar (som står före de andra, med siffrorna bredvid)."""
    _, kundrepo, _ = _m()
    r = kundrepo.repo(slug)
    if not kundrepo.ar_repo(r):
        return {'finns': False}
    std = std or standardgren(r)
    gren = _ut(_git(r, 'rev-parse', '--abbrev-ref', 'HEAD'))
    lokala = len([z for z in _git(r, 'status', '--porcelain').stdout.splitlines() if z.strip()])
    ref = 'refs/remotes/origin/%s' % std
    fore = efter = None
    if _git(r, 'rev-parse', '--verify', '-q', ref).returncode == 0 and kundrepo.huvud(r):
        delar = (_ut(_git(r, 'rev-list', '--left-right', '--count', 'HEAD...%s' % ref)) or '').split()
        if len(delar) == 2:
            fore, efter = int(delar[0]), int(delar[1])
    fh = r / '.git' / 'FETCH_HEAD'
    lage = ('lokala ändringar' if lokala else 'ej hämtat' if efter is None else 'i takt' if fore == efter == 0
            else 'före' if efter == 0 else 'efter' if fore == 0 else 'isär')
    return {'finns': True, 'gren': gren, 'standardgren': std, 'pa_standardgren': gren == std, 'lokala': lokala, 'fore': fore,
            'efter': efter, 'lage': lage, 'origin': normaliserad(_ut(_git(r, 'config', '--get', 'remote.origin.url'))) or None,
            'hamtad': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(fh.stat().st_mtime)) if fh.is_file() else None}


def _post(x, via_namn, via_projekt, valbara):
    """En rad i listan: repot, kunden när kvittona binder den, arbetskopian och vad ett val gör (oppna, klona, koppla
    eller nej med skälet)."""
    _, kundrepo, _ = _m()
    namn = str(x['name'])
    m = MARKOR.search(str(x.get('description') or ''))
    pid = m.group(1) if m else None
    slugs = sorted(set(via_namn.get(namn.lower(), [])) | set(via_projekt.get(pid, []) if pid else []))
    std = ((x.get('defaultBranchRef') or {}).get('name')) or None  # okänd utan listan: arbetskopians origin/HEAD avgör
    p = {'namn': namn, 'full': '%s/%s' % (kundrepo.ORG, namn), 'url': 'https://github.com/%s/%s' % (kundrepo.ORG, namn),
         'privat': bool(x.get('isPrivate', True)), 'standardgren': std, 'senast_push': x.get('pushedAt'), 'markor': bool(pid),
         'kund': None, 'forslag': None, 'arbetskopia': {'finns': False}, 'oppnas': 'nej', 'skal': None}
    if len(slugs) > 1:
        p['skal'] = 'två kunders kvitton pekar ut repot (%s); rätta kvittona innan det öppnas' % ', '.join(slugs)
        p['kort'] = 'två kunders kvitton pekar ut repot'
        return p
    if slugs:
        slug = slugs[0]
        p['kund'] = {'slug': slug, 'namn': _kundnamn(slug), 'fiktiv': kundrepo.fiktiv(slug)}
        if p['kund']['fiktiv']:
            p['skal'] = 'kunden är en fiktiv verksamhet, och en sådan får aldrig ett fjärrepo'
            p['kort'] = 'fiktiv verksamhet'
            return p
        p['arbetskopia'] = arbetskopians_lage(slug, std)
        p['standardgren'] = p['arbetskopia'].get('standardgren') or std or 'main'
        p['oppnas'] = 'oppna' if p['arbetskopia']['finns'] else 'klona'
        if p['arbetskopia'].get('origin') and p['arbetskopia']['origin'] != p['url']:
            p['varning'] = 'arbetskopians origin är %s, inte repot; förkontrollen stoppar ändringar tills det är rättat' % p['arbetskopia']['origin']
        return p
    if not pid:
        p['skal'] = ('repots beskrivning saknar Nortropics projektmarkör, och ett sådant repo binds aldrig till en kund (samma regel '
                     'som när kundrepon skapas); hör repot till en kund, använd flödet för ny kund eller lägg till markören på GitHub')
        p['kort'] = 'saknar Nortropics projektmarkör'
        return p
    p['oppnas'] = 'koppla'
    gissning = namn[5:] if namn.startswith('kund-') else None
    if gissning and any(k['slug'] == gissning for k in valbara):
        p['forslag'] = gissning  # ett namnförslag, aldrig en bindning: det kräver Johnnys val
    return p


# --- Senast öppnade ---

def _senastfil():
    atelje, _, _ = _m()
    return atelje.UNDERLAG / 'repovaljaren' / 'SENAST.json'


def senast():
    p = _senastfil()
    try:
        d = json.loads(p.read_text(encoding='utf-8')) if p.is_file() and not p.is_symlink() else []
    except (OSError, ValueError):
        d = []
    return [x for x in d if isinstance(x, dict) and NAMN.match(str(x.get('repo') or '')) and SLUG.match(str(x.get('slug') or ''))][:SENAST_MAX] \
        if isinstance(d, list) else []


def spara_senast(namn, slug):
    atelje, _, _ = _m()
    if not NAMN.match(str(namn or '')) or not SLUG.match(str(slug or '')):
        return
    p = _senastfil()
    with LAS:
        lista_ = [x for x in senast() if x['repo'] != namn and x['slug'] != slug]
        lista_.insert(0, {'repo': namn, 'slug': slug, 'tid': _nu()})
        atelje.saker_vag(p, atelje.UNDERLAG)
        p.parent.mkdir(parents=True, exist_ok=True)
        atelje.skriv_json_atomiskt(p, lista_[:SENAST_MAX])


def spara_senast_for(slug):
    """En webbplats som öppnats i Ändringar på annat sätt (agenten startad) räknas också som öppnad, med sitt bundna repo."""
    _, kundrepo, _ = _m()
    try:
        if kundrepo.las_kvitto(slug):
            spara_senast(kundrepo.bunden_adress(slug).rsplit('/', 1)[1], slug)
    except (OSError, ValueError, RuntimeError):
        pass


# --- listan ---

def _levande():
    try:
        import andringsflik
    except ImportError:
        return []
    with andringsflik.LAS:
        return [{'slug': s, 'sid': v['sid'], 'pid': v['session'].pid} for s, v in andringsflik.SESSIONER.items() if v['session'].lever]


def lista(las_om=False):
    """Väljarens data: inloggningen, organisationens kundrepon med kund, arbetskopia och val, Senast öppnade, levande
    agentsessioner och kunderna ett okopplat repo kan kopplas till. Fungerar utan GitHub: då står bundna arbetskopior
    kvar ur kvittona, med beskedet om inloggningen."""
    _, kundrepo, _ = _m()
    org = _org_repon(las_om)
    via_namn, via_projekt = _bindningar()
    valbara = kopplingsbara()
    poster = [_post(x, via_namn, via_projekt, valbara) for x in org['repon']]
    # de bundna arbetskopiorna ur kvittona som listan inte har (GitHub svarade inte, eller inloggningen ser inte repot):
    # arbetet kan fortsätta i dem
    i_listan = {p['namn'].lower() for p in poster}
    for namn, slugs in sorted(via_namn.items()):
        if namn not in i_listan and len(slugs) == 1 and kundrepo.ar_repo(kundrepo.repo(slugs[0])) and not kundrepo.fiktiv(slugs[0]):
            x = {'name': kundrepo.bunden_adress(slugs[0]).rsplit('/', 1)[1], 'description': '', 'isPrivate': True}
            p = _post(x, via_namn, via_projekt, valbara)
            p['ur_kvittot'] = True
            poster.append(p)
    inloggning = org['inloggning']
    if org['ok'] and not org['repon'] and org.get('synliga'):  # inloggningen ser organisationen, som inte har några kundrepon än
        inloggning = {'slag': 'inga_kundrepon', 'besked': '%s har inga kundrepon på GitHub än.' % kundrepo.ORG,
                      'atgard': 'En verklig kunds repo skapas när kundens projekt startar; testkunder och fiktiva kunder får aldrig '
                                'något. Arbetskopiorna på datorn visas ändå.'}
    elif org['ok'] and not org['repon']:  # GitHub svarade utan ett enda repo i organisationen: oftast en inloggning utan åtkomst
        inloggning = {'slag': 'tom', 'besked': 'GitHub gav inga repon i %s.' % kundrepo.ORG,
                      'atgard': 'Har inloggningen åtkomst till organisationens privata repon? Kör `gh auth status` i Terminal; '
                                'arbetskopiorna på datorn visas ändå.'}
    return {'org': kundrepo.ORG, 'inloggning': inloggning, 'hamtad': org.get('hamtad'), 'arkiverade': org.get('arkiverade', 0),
            'repon': poster, 'senast': senast(), 'levande': _levande(), 'kunder': valbara}


# --- handlingarna ---

class Upptagen(Exception):
    """Kundens lås hålls av ett annat arbete (agentens tur, en export, en förhandsvisning)."""


class _Kundlas:
    def __init__(self, slug):
        self.slug, self.cm = slug, None

    def __enter__(self):
        atelje, _, _ = _m()
        import flodesstart
        try:
            import andringsflik
            with andringsflik.LAS:
                if self.slug in andringsflik.SKRIVLAS:
                    raise Upptagen('agenten arbetar just nu; försök igen när turen är klar')
        except ImportError:
            pass
        self.cm = flodesstart.las(atelje.ROOT, self.slug)
        try:
            self.cm.__enter__()
        except ValueError as e:
            if 'Ett arbete pågår' in str(e):
                raise Upptagen('ett annat arbete håller kundens lås; försök igen strax') from e
            raise
        return self

    def __exit__(self, *a):
        return self.cm.__exit__(*a)


def _hitta(namn):
    if not NAMN.match(str(namn or '')):
        raise ValueError('ogiltigt reponamn')
    d = lista()
    p = next((x for x in d['repon'] if x['namn'] == namn), None)
    if not p:
        raise ValueError('%s finns inte bland %s kundrepon (läs om listan)' % (namn, _m()[1].ORG))
    return p, d


def _kvitto_skriv(slug, andra):
    """Ändrar kundens kvitto under kundrepots eget lås (samma som kundrepo.skapa)."""
    import fcntl
    atelje, kundrepo, _ = _m()
    with open(kundrepo._lasfil(slug), 'w') as las:
        fcntl.flock(las, fcntl.LOCK_EX)
        kv = kundrepo.las_kvitto(slug) or {}
        andra(kv)
        atelje.skriv_json_atomiskt(kundrepo.kvittofil(slug), kv)
        return kv


def koppla(p, slug):
    """Ett okopplat repo med projektets markör till en befintlig kund utan kvitto: kvittot får repots projekt-id och
    fjärrepot som återanvänt (som kundrepo.fjarr_skapa gör med ett repo som bär markören)."""
    _, kundrepo, _ = _m()
    if not any(k['slug'] == slug for k in kopplingsbara()):
        raise ValueError('%s kan inte kopplas här: kunden finns inte, är fiktiv, har redan ett kvitto eller en arbetskopia' % slug)
    pid = MARKOR.search(_markortext(p)).group(1)

    def andra(kv):
        if kv:
            raise ValueError('kunden fick ett kvitto under tiden; inget kopplat')
        kv.update({'schema': 1, 'projekt_id': pid, 'skapad': _nu(), 'skapad_med': kundrepo.motorversion(), 'slug': slug, 'namn': p['namn'],
                   'org': kundrepo.ORG, 'lokal': 'kunder/%s/kundrepo' % slug,
                   'fjarr': {'status': 'skapat', 'tid': _nu(), 'fel': None, 'adress': p['url'], 'privat': p['privat'], 'ateranvant': True,
                             'kopplat': {'av': 'repoväljaren', 'tid': _nu()}}})
    return _kvitto_skriv(slug, andra)


def _markortext(p):
    with LAS:
        s = CACHE['svar'] or {}
    x = next((x for x in s.get('repon') or [] if x.get('name') == p['namn']), {})
    return str(x.get('description') or '')


def klona(p, slug):
    """Repot till kunder/<slug>/kundrepo med gh (ägarens inloggning), under kundens lås; origin ska vara repots adress.
    Kvittot får arbetskopians ursprung. Ger förkontrollens hinder (tomma när allt stämmer)."""
    atelje, kundrepo, andringar = _m()
    mal = kundrepo.repo(slug)
    atelje.saker_vag(mal, atelje.KUNDER)
    if mal.exists() or mal.is_symlink():
        raise ValueError('kunder/%s/kundrepo finns redan; inget klonat' % slug)
    gh = shutil.which('gh')
    if not gh:
        raise ValueError('GitHub CLI (gh) finns inte på datorn')
    with _Kundlas(slug):
        mal.parent.mkdir(parents=True, exist_ok=True)
        r = kundrepo.kommando([gh, 'repo', 'clone', p['full'], str(mal)], atelje.KUNDER, frist=900)
        if r.returncode or not kundrepo.ar_repo(mal):
            f = inloggningsfel(r.stderr or r.stdout)
            raise ValueError('klonen gick inte: %s %s' % (f['besked'], f['atgard'] if f['slag'] != 'fel' else ''))
        origin = normaliserad(_ut(_git(mal, 'config', '--get', 'remote.origin.url')))
        if origin != p['url']:
            raise ValueError('klonens origin (%s) är inte repots adress (%s); arbetskopian står kvar för granskning' % (origin, p['url']))
        huvud = kundrepo.huvud(mal)

        import exportera
        grund = None if exportera.aktuell(slug) else exportera.fran_klon(slug)  # grunden för ändringsflikens kvitteringar

        def andra(kv):
            if not kv:
                raise ValueError('kundens kvitto saknas; inget registrerat')
            kv['lokal'] = 'kunder/%s/kundrepo' % slug
            kv['arbetskopia'] = {'klonad': _nu(), 'fran': p['url'], 'commit': huvud, 'av': 'repoväljaren'}
            if grund:
                kv['senaste_export'] = {'id': grund['id'][len('EXPORT-'):], 'commit': huvud, 'klon': True}
            if (kv.get('fjarr') or {}).get('status') != 'skapat':  # bundet genom projekt-id: fjärrepot bär markören
                kv['fjarr'] = {'status': 'skapat', 'tid': _nu(), 'fel': None, 'adress': p['url'], 'privat': p['privat'], 'ateranvant': True}
        _kvitto_skriv(slug, andra)
    return andringar.forkontroll(slug)['hinder']


def oppna(namn, slug=None, bekraftat=False):
    """Ett val i listan: {vy} när Ändringar kan öppnas, annars {bekrafta: klona|koppla, ...} som Johnny svarar på.
    Ett repo kopplat till en kund öppnas aldrig som en annan; ett okopplat kräver ett aktivt val."""
    p, d = _hitta(namn)
    if p['oppnas'] == 'nej':
        raise ValueError(p['skal'])
    if slug is not None and not SLUG.match(str(slug)):
        raise ValueError('ogiltig kund')
    if p['kund']:
        if slug and slug != p['kund']['slug']:
            raise ValueError('%s är kopplat till %s och öppnas inte som %s' % (namn, p['kund']['slug'], slug))
        slug = p['kund']['slug']
        if p['oppnas'] == 'klona':
            if not bekraftat:
                return {'bekrafta': 'klona', 'repo': namn, 'slug': slug, 'kund': p['kund'], 'mal': 'kunder/%s/kundrepo' % slug}
            hinder = klona(p, slug)
            spara_senast(namn, slug)
            return {'vy': '#/andringar/%s' % slug, 'slug': slug, 'klonad': True, 'hinder': hinder}
        spara_senast(namn, slug)
        return {'vy': '#/andringar/%s' % slug, 'slug': slug}
    if not slug or not bekraftat:
        return {'bekrafta': 'koppla', 'repo': namn, 'forslag': p['forslag'], 'kunder': d['kunder']}
    koppla(p, slug)
    hinder = klona(p, slug)
    spara_senast(namn, slug)
    return {'vy': '#/andringar/%s' % slug, 'slug': slug, 'kopplad': True, 'klonad': True, 'hinder': hinder}


def _logg(r, intervall):
    return [dict(zip(('commit', 'text'), z.split('\x1f', 1))) for z in (_ut(_git(r, 'log', '--format=%h%x1f%s', '-20', intervall)) or '').splitlines() if '\x1f' in z]


def _bunden_arbetskopia(slug):
    atelje, kundrepo, _ = _m()
    if not SLUG.match(str(slug or '')):
        raise ValueError('ogiltig kund')
    r = kundrepo.repo(slug)
    if not kundrepo.ar_repo(r):
        raise ValueError('kunden har ingen arbetskopia')
    if kundrepo.fiktiv(slug):
        raise ValueError('en fiktiv verksamhet har inget fjärrepo att hämta från')
    origin = normaliserad(_ut(_git(r, 'config', '--get', 'remote.origin.url')))
    if not origin or origin != kundrepo.bunden_adress(slug):
        raise ValueError('arbetskopians origin (%s) är inte kundens repo (%s)' % (origin or 'saknas', kundrepo.bunden_adress(slug)))
    return r


def hamta(slug):
    """git fetch utan sammanfogning, under kundens lås: läget före och efter, och vad som kommit in och väntar på att gå ut."""
    _, kundrepo, _ = _m()
    r = _bunden_arbetskopia(slug)
    with _Kundlas(slug):
        std = standardgren(r)
        fore = arbetskopians_lage(slug, std)
        # samma inloggning som klonen: gh som gits inloggningshjälp för github.com, och ingen fråga i en terminal
        gh = shutil.which('gh')
        hjalp = ['-c', 'credential.https://github.com.helper=', '-c', 'credential.https://github.com.helper=!%s auth git-credential' % gh] if gh else []
        res = kundrepo.kommando(['git', *_m()[2].SAKER_GIT, *hjalp, 'fetch', 'origin'], r, frist=300, env=dict(os.environ, GIT_TERMINAL_PROMPT='0'))
        if res.returncode:
            f = inloggningsfel(res.stderr or res.stdout)
            raise ValueError('hämtningen gick inte: %s %s' % (f['besked'], f['atgard'] if f['slag'] != 'fel' else ''))
        std = standardgren(r)
        efter = arbetskopians_lage(slug, std)
        ref = 'refs/remotes/origin/%s' % std
        return {'fore': fore, 'efter': efter, 'inkommande': _logg(r, 'HEAD..%s' % ref), 'utgaende': _logg(r, '%s..HEAD' % ref)}


def uppdatera(slug):
    """Bara fast-forward till origin/<standardgren>, på en ren arbetskopia på standardgrenen, under kundens lås. Annars
    ett besked om läget och inget ändrat; lokala ändringar står kvar."""
    r = _bunden_arbetskopia(slug)
    with _Kundlas(slug):
        std = standardgren(r)
        l = arbetskopians_lage(slug, std)
        if l['lokala']:
            raise ValueError('arbetskopian har %d lokala ändringar som inte är committade, så inget uppdaterades och de står kvar. '
                             'Låt agenten committa dem i Ändringar, eller uppdatera senare.' % l['lokala'])
        if not l['pa_standardgren']:
            raise ValueError('arbetskopian står på grenen %s, inte standardgrenen %s; den här versionen byter inte gren' % (l['gren'], std))
        if l['efter'] is None:
            raise ValueError('fjärrens läge är inte hämtat än: hämta först')
        if not l['efter']:
            return {'andrat': False, 'fore': l, 'efter': l, 'commits': [], 'text': 'inget att uppdatera: arbetskopian är %s' % l['lage']}
        if l['fore']:
            raise ValueError('arbetskopian och fjärren har gått isär (%d före, %d efter). Bara fast-forward är tillåtet här, så inget '
                             'uppdaterades; arbetskopians commits står kvar.' % (l['fore'], l['efter']))
        ref = 'refs/remotes/origin/%s' % std
        commits = _logg(r, 'HEAD..%s' % ref)
        res = _git(r, 'merge', '--ff-only', '--no-edit', ref, frist=300)
        if res.returncode:
            raise ValueError('uppdateringen gick inte bara framåt, så inget uppdaterades: %s' % (res.stderr or res.stdout).strip()[-300:])
        return {'andrat': True, 'fore': l, 'efter': arbetskopians_lage(slug, std), 'commits': commits}
