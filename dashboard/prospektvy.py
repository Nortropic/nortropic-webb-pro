#!/usr/bin/env python3
"""prospektvy.py — dashboardens läsning och handtag för prospekten: kampanjer, register, kort per verksamhet, jobb,
demobygge, brev och sändning. Importeras av dashboard/server.py, som kopplar in sina egna läsare (siffror, bilder,
korning, byggen) med koppla(). Skriver bara privata filer under underlag/; inget committas.

Modulen heter prospektvy, inte prospekt, eftersom kontroller/prospekt.py (pipelinen) ligger först på sys.path i servern.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'kontroller'))
import prospektfiler as pf  # noqa: E402
import utskick  # noqa: E402

UNDERLAG = ROOT / 'underlag'
KUNDER = ROOT / 'kunder'
SLUG = pf.SLUG
KAMPANJ_ID = pf.KAMPANJ_ID
KOMMUNER_RESERV = [('2580', 'Luleå'), ('2581', 'Piteå'), ('2582', 'Boden'), ('2583', 'Haparanda'), ('2584', 'Kiruna'), ('2514', 'Kalix'),
                   ('2560', 'Älvsbyn'), ('2523', 'Gällivare'), ('2480', 'Umeå'), ('2482', 'Skellefteå')]
AGARENS_STATUSAR = ('vald', 'avvisad', 'svar', 'kund', 'nej')
H = {}  # serverns läsare: siffror, bilder, korning, byggen


def koppla(**fn):
    H.update(fn)


def nu():
    return pf.nu()


def ren_miljo():
    return {k: v for k, v in os.environ.items() if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_') and not k.startswith('NWP_')}


def las_json(p):
    return pf.las_json(p)


def jobb_lage(kdir):
    j = las_json(kdir / 'JOBB.json') or {}
    lever = bool(j.get('pid')) and pf.lever(j.get('pid')) and not j.get('slut')
    return {'pagar': lever, 'steg': j.get('steg') if lever else None, 'start': j.get('start'), 'slut': j.get('slut'), 'rc': j.get('rc') or {},
            'fel': j.get('fel'), 'logg': j.get('logg'), 'pid_pipeline': pf.pagar_pid(kdir)}


def logg_svans(kdir, n=10):
    p = kdir / 'logg.jsonl'
    try:
        with open(p, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 16000))
            rader = f.read().decode('utf-8', errors='replace').splitlines()
    except OSError:
        return []
    ut = []
    for rad in rader[-n:][::-1]:
        try:
            ut.append(json.loads(rad))
        except ValueError:
            continue
    return ut


def antal_per_status(poster):
    ut = {}
    for p in poster:
        ut[p.get('status') or '?'] = ut.get(p.get('status') or '?', 0) + 1
    return ut


def raknare():
    """Billig räknare till /api/oversikt: prospekt som väntar på ägaren (vald eller utkast)."""
    n = 0
    for k in pf.kampanjer():
        n += sum(1 for p in pf.las_register(k['id']) if p.get('status') in ('vald', 'utkast'))
    return n


def branscher():
    d = las_json(ROOT / 'kunskap' / 'prospekt-branscher.json') or {}
    return [{'id': k, 'namn': v.get('namn') or k} for k, v in sorted((d.get('branscher') or {}).items())]


def kommuner():
    k = las_json(pf.PROSPEKT / 'KODER.json') or {}
    tab = (k.get('tabeller') or {}).get('kommunkoder') or []
    if tab:
        return sorted(({'kod': x['kod'], 'namn': x['klartext']} for x in tab if x.get('kod')), key=lambda x: x['namn'])
    return [{'kod': kod, 'namn': namn} for kod, namn in KOMMUNER_RESERV]


def kampanjer():
    ut = []
    for k in pf.kampanjer():
        kdir = pf.kampanjkatalog(k['id'])
        poster = pf.las_register(k['id'])
        ut.append({**k, 'antal': antal_per_status(poster), 'totalt': len(poster), 'jobb': jobb_lage(kdir)})
    return {'kampanjer': ut, 'branscher': branscher(), 'kommuner': kommuner(), 'nyckel_finns': (Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'scb.env').is_file(),
            'stopp': (pf.PROSPEKT / 'STOPP').is_file()}


def kampanj(k):
    kdir = pf.kampanjkatalog(k)
    meta = las_json(kdir / 'KAMPANJ.json')
    if not meta:
        raise ValueError('ingen kampanj %s' % k)
    poster = pf.las_register(k)
    rad = [{kk: p.get(kk) for kk in ('slug', 'namn', 'postort', 'jurform_text', 'fysisk_person', 'sajt', 'sajt_kandidat', 'status', 'poang', 'anstKl_text', 'startDat', 'sparr', 'avvisad_skal', 'analys_tid')} for p in poster]
    return {**meta, 'id': k, 'poster': rad, 'antal': antal_per_status(poster), 'jobb': jobb_lage(kdir), 'logg': logg_svans(kdir)}


def brev_lage(bas):
    bdir = bas / 'brev'
    pid = pf.pagar_pid(bdir)
    fel = None
    try:
        fel = (bdir / 'FEL.txt').read_text(encoding='utf-8').strip()
    except OSError:
        pass
    return {'pagar': bool(pid), 'fel': fel if not pid else None, 'uppdrag': las_json(bdir / 'UPPDRAG.json')}


def prospekt(k, slug):
    poster = pf.las_register(k)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post %s i %s' % (slug, k))
    bas = UNDERLAG / slug
    pro = las_json(bas / 'PROSPEKT.json') or {}
    brev = las_json(bas / 'BREV.json')
    uts = las_json(bas / 'UTSKICK.json')
    sparr = utskick.las_sparr()
    ok, skal = utskick.far_skickas(post, brev, sparr, bool(uts), utskick.hemligheter_finns())
    sidfot = None
    try:
        sidfot = utskick.sidfot(utskick.las_hemligheter(), post)
    except utskick.Nekad as e:
        sidfot = '(sidfoten visas när hemligheterna finns: %s)' % e
    dagar = None
    if uts and uts.get('tid'):
        try:
            dagar = (datetime.now(timezone.utc) - datetime.strptime(uts['tid'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)).days
        except ValueError:
            dagar = None
    ut = {'post': post, 'kampanj': k, 'prospekt': {kk: pro.get(kk) for kk in ('poang', 'varfor', 'underlag', 'tider', 'verktygsfel', 'analys_tid', 'sajt')},
          'siffror': H['siffror'](bas / 'diagnos') if 'siffror' in H else {}, 'bilder': (H['bilder'](slug) if 'bilder' in H else {}).get('deras', []),
          'filer': [str(p.relative_to(ROOT)) for p in sorted((bas / 'diagnos').rglob('*')) if p.is_file() and p.suffix in ('.json', '.md') and p.name not in ('hem-mobil.json',)][:30],
          'brev': brev, 'brev_lage': brev_lage(bas), 'utskick': uts, 'skickat_dagar': dagar, 'grind': {'ok': ok, 'skal': skal}, 'sidfot': sidfot,
          'bygge': {'finns': (KUNDER / slug).is_dir(), 'korning': H['korning'](slug) if 'korning' in H and (KUNDER / slug).is_dir() else None},
          'bygge_pagar_annat': any(b.get('pagar') for b in (H['byggen']() if 'byggen' in H else [])),
          'sparrad': utskick.i_sparrlista(sparr, ((brev or {}).get('mottagare') or {}).get('epost') or post.get('epost'), post)}
    return ut


# --- jobb ---

def starta_jobb(kdir, args, namn):
    if jobb_lage(kdir)['pagar'] or pf.pagar_pid(kdir):
        raise ValueError('ett jobb pågår redan i kampanjen')
    kdir.mkdir(parents=True, exist_ok=True)
    with open(kdir / ('%s-start.log' % namn), 'ab') as ut:
        subprocess.Popen([sys.executable, '-B', str(ROOT / 'kontroller' / 'prospekt_jobb.py'), *args], cwd=str(ROOT), env=ren_miljo(),
                         stdin=subprocess.DEVNULL, stdout=ut, stderr=subprocess.STDOUT, start_new_session=True)


def starta_kampanj(data):
    bransch = str(data.get('bransch') or '').strip()
    kommun = str(data.get('kommun') or '').strip()
    if bransch not in {b['id'] for b in branscher()}:
        raise ValueError('okänd bransch')
    if not re.fullmatch(r'\d{4}', kommun):
        raise ValueError('kommunkod med fyra siffror')
    mx = max(1, min(50, int(data.get('max') or 10)))
    kid = str(data.get('id') or '').strip() or '%s-%s-%s' % (bransch, kommun, datetime.now(timezone.utc).strftime('%Y%m%d'))
    if not KAMPANJ_ID.match(kid):
        raise ValueError('kampanj-id: små bokstäver, siffror och bindestreck')
    kdir = pf.kampanjkatalog(kid)
    starta_jobb(kdir, ['kampanj', kid, '--kommun', kommun, '--bransch', bransch, '--max', str(mx)], 'jobb')
    pf.logga(kid, 'jobb_start', lage='kampanj', kommun=kommun, bransch=bransch, max=mx, av='dashboarden')
    return {'id': kid}


def starta_analys(k, data):
    kdir = pf.kampanjkatalog(k)
    if not (kdir / 'KAMPANJ.json').is_file():
        raise ValueError('ingen kampanj %s' % k)
    mx = max(1, min(50, int(data.get('max') or 10)))
    starta_jobb(kdir, ['analysera', k, '--max', str(mx)], 'jobb')
    pf.logga(k, 'jobb_start', lage='analysera', max=mx, av='dashboarden')
    return {'id': k, 'max': mx}


def satt_status(k, slug, data):
    status = str(data.get('status') or '')
    if status not in AGARENS_STATUSAR:
        raise ValueError('från dashboarden går bara %s' % ', '.join(AGARENS_STATUSAR))
    falt = {}
    if status == 'avvisad':
        skal = str(data.get('skal') or '').strip()[:500]
        if not skal:
            raise ValueError('ange ett skäl')
        falt['avvisad_skal'] = skal
    if status in ('svar', 'kund', 'nej'):
        falt['svar'] = {'status': status, 'tid': nu(), 'not': str(data.get('not') or '')[:1000]}
    post = pf.satt_status(k, slug, status, **falt)
    if not post:
        raise ValueError('ingen post %s' % slug)
    pf.logga(k, 'status', slug=slug, status=status, av='agaren')
    return {'slug': slug, 'status': status}


def satt_sajt(k, slug, data):
    """Bekräfta sajt_kandidat eller ange en adress själv: kör prospekt.py sajter --slug --url."""
    url = str(data.get('url') or '').strip()
    poster = pf.las_register(k)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post %s' % slug)
    if not url and post.get('sajt_kandidat'):
        url = post['sajt_kandidat']['url']
    if not re.match(r'^https?://[^\s]{4,500}$', url):
        raise ValueError('ange en http- eller https-adress')
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'prospekt.py'), 'sajter', '--kampanj', k, '--slug', slug, '--url', url],
                       cwd=str(ROOT), env=ren_miljo(), capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise ValueError((r.stderr or r.stdout or 'kunde inte sätta sajten')[-300:].strip())
    return {'slug': slug, 'url': url}


def starta_demo(k, slug):
    poster = pf.las_register(k)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post %s' % slug)
    if post.get('status') not in ('vald', 'demo'):
        raise ValueError('välj verksamheten först')
    if any(b.get('pagar') for b in (H['byggen']() if 'byggen' in H else [])):
        raise ValueError('ett bygge pågår redan; en demo i taget')
    url = (post.get('sajt') or {}).get('url') or ''
    bransch = (post.get('sni') or [{}])[0].get('text') or post.get('bransch') or ''
    verksamhet = '%s, %s i %s%s' % (post.get('namn'), bransch.lower() or 'verksamhet', post.get('postort') or post.get('kommun') or '', (', ' + url) if url else '')
    (KUNDER / slug).mkdir(parents=True, exist_ok=True)
    logg = KUNDER / slug / ('kor-%s.log' % datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    with open(logg, 'ab') as ut:
        subprocess.Popen([str(ROOT / 'kor.sh'), slug, verksamhet], cwd=str(ROOT), env=ren_miljo(), stdin=subprocess.DEVNULL, stdout=ut,
                         stderr=subprocess.STDOUT, start_new_session=True)
    pf.satt_status(k, slug, 'demo', demo_start=nu())
    pf.logga(k, 'demo_start', slug=slug, verksamhet=verksamhet, av='agaren')
    return {'slug': slug, 'verksamhet': verksamhet, 'logg': str(logg.relative_to(ROOT))}


def starta_brev(k, slug):
    poster = pf.las_register(k)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post %s' % slug)
    if post.get('status') not in ('vald', 'demo', 'utkast'):
        raise ValueError('välj verksamheten först')
    bas = UNDERLAG / slug
    if not (bas / 'PROSPEKT.json').is_file():
        raise ValueError('ingen mätning (PROSPEKT.json) att skriva ur; analysera först')
    bdir = bas / 'brev'
    if pf.pagar_pid(bdir):
        raise ValueError('ett brev skrivs redan')
    bdir.mkdir(parents=True, exist_ok=True)
    if (bas / 'BREV.json').is_file():
        (bas / 'BREV.json').rename(bdir / ('BREV-%s.json' % datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    with open(bdir / 'arbetare.log', 'ab') as ut:
        proc = subprocess.Popen([sys.executable, '-B', str(ROOT / 'kontroller' / 'brev.py'), slug, '--kampanj', k], cwd=str(ROOT), env=ren_miljo(),
                                stdin=subprocess.DEVNULL, stdout=ut, stderr=subprocess.STDOUT, start_new_session=True)
    (bdir / 'PAGAR').write_text(str(proc.pid))  # före barnet hinner: ett andra klick ser att ett brev skrivs
    pf.logga(k, 'brev_start', slug=slug, av='agaren')
    return {'slug': slug}


def godkann(k, slug, data):
    bas = UNDERLAG / slug
    brev = las_json(bas / 'BREV.json')
    if not brev:
        raise ValueError('inget utkast att godkänna')
    if data.get('aterkalla'):
        brev.pop('godkand', None)
        pf.skriv_json(bas / 'BREV.json', brev)
        return {'slug': slug, 'godkand': False}
    amne = str(data.get('amne') or '').strip()[:120]
    text = str(data.get('text') or '').strip()[:2000]
    if not amne or not text:
        raise ValueError('ämne och text behövs')
    if len(re.findall(r'\S+', text)) > 160:
        raise ValueError('brevet är över 160 ord; korta det')
    u = brev.get('utkast') or {}
    if amne != u.get('amne') or text != u.get('text'):
        brev['redigerat'] = {'amne': amne, 'text': text, 'tid': nu()}
    else:
        brev.pop('redigerat', None)
    m = data.get('mottagare') or {}
    epost = str(m.get('epost') or '').strip()
    import brev as brevmod
    brev['mottagare'] = {'epost': epost, 'typ': brevmod.mottagartyp(epost) if epost else None, 'bekraftad_person': bool(m.get('bekraftad_person'))}
    fakta = ((brev.get('utkast') or {}).get('fakta') or [])
    upp = las_json(bas / 'brev' / 'UPPDRAG.json') or {}
    kontroll = brevmod.kontrollera({'amne': amne, 'text': text}, upp.get('fakta') or [x.get('pastaende', '') for x in fakta])
    brev['kontroll'] = {'copy_fynd': kontroll['copy_fynd'], 'siffror_ok': kontroll['siffror_ok'], 'siffror_fel': kontroll['siffror_fel'], 'ord': kontroll['ord']}
    # godkännandet binder text, mottagare, verksamhet och bekräftelsen av en namngiven adress (utskick.far_skickas)
    brev['godkand'] = {'tid': nu(), 'text_sha': pf.text_sha(amne, text), 'mottagare': epost.lower(), 'slug': slug,
                       'bekraftad_person': bool(m.get('bekraftad_person'))}
    pf.skriv_json(bas / 'BREV.json', brev)
    pf.logga(k, 'brev_godkant', slug=slug, ord=kontroll['ord'], siffror_ok=kontroll['siffror_ok'], av='agaren')
    return {'slug': slug, 'godkand': True, 'kontroll': brev['kontroll']}


def skicka(k, slug):
    poster = pf.las_register(k)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post %s' % slug)
    bas = UNDERLAG / slug
    ok, skal = utskick.far_skickas(post, las_json(bas / 'BREV.json'), utskick.las_sparr(), (bas / 'UTSKICK.json').is_file(), utskick.hemligheter_finns())
    if not ok:
        raise ValueError(skal)
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'kontroller' / 'utskick.py'), 'skicka', slug, '--kampanj', k], cwd=str(ROOT),
                       env={**ren_miljo(), **{k: v for k, v in os.environ.items() if k.startswith('NWP_UTSKICK')}}, capture_output=True, text=True, timeout=60)  # torrkörning och nyckelfil följer med; inget av dem öppnar grinden
    try:
        svar = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        svar = {'ok': False, 'skal': (r.stderr or r.stdout or 'inget svar')[-300:]}
    if not svar.get('ok'):
        raise ValueError(svar.get('skal') or 'sändningen föll')
    return svar


def stryk(k, slug, data):
    poster = pf.las_register(k)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post %s' % slug)
    skal = str(data.get('skal') or '').strip()[:300] or 'bad om det'
    brev = las_json(UNDERLAG / slug / 'BREV.json') or {}
    epost = ((brev.get('mottagare') or {}).get('epost') or post.get('epost') or '').strip()
    poster_sparr = []
    if epost:
        poster_sparr.append(utskick.sparr_lagg(epost, skal, kalla='manuell', typ='e-post', post=post))
    if post.get('orgNr'):
        poster_sparr.append(utskick.sparr_lagg(post['orgNr'], skal, kalla='manuell', typ='orgnr', spegla=False, post=post))
    pf.satt_status(k, slug, 'nej', svar={'status': 'nej', 'tid': nu(), 'not': skal})
    pf.logga(k, 'struken', slug=slug, skal=skal, av='agaren')
    return {'slug': slug, 'sparr': poster_sparr}
