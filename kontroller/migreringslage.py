#!/usr/bin/env python3
"""migreringslage.py — kundens läge i övergången till Cloudflare Workers (uppdraget 2026-10-09, M18 och avsnitt 11),
räknat ur observationer och kvitton, aldrig ur att normalprofilen bytts.

Fem skilda besked, vart och ett med sitt belägg:
- förberedd: en aktuell export för Workers (exportera.aktuell);
- måltestad: en klar förhandsvisning på Cloudflare av exportens commit (kundrepo.preview_aktuell), med skyddet prövat;
- trafik flyttad: en klar release till produktionens Worker och, efter den, en observation av kundens egen adress som
  svarar från Cloudflare-Workern (observera_trafik). En förhandsadress, workers.dev eller vercel.app räknas aldrig;
- data avstämd: bara när kunden har äldre data på Vercel (beståndet); utan sådan är steget inte tillämpligt;
- legacy avvecklad: bara när kunden har ett äldre Vercel-projekt; avvecklingen är ett eget ägarbeslut.

"Migrerad" sägs bara när kunden hade en äldre drift och alla fem är uppfyllda. En ny kund utan äldre drift blir
"i drift på Cloudflare", aldrig migrerad. Läsningen har inga sidoeffekter; bara observera_trafik skriver, och då ett
kvitto (kunder/<slug>/leverans/TRAFIK-*.json) efter två GET-anrop.

Beståndet av äldre Vercel-projekt är privat: underlag/leverans/VERCEL-BESTAND.json (inventerat 2026-10-09 med läsande
anrop; ägarens besked ~21:22Z: sajterna på Vercel stannar), {"schema": 1, "inventerat": "<datum>", "projekt": [{"projekt",
"slug" (eller null), "adress", "data" (eller null), "status": "kvar"|"avvecklad", "belagg"}]}.

    .venv/bin/python kontroller/migreringslage.py <slug>                    # läget, utan sidoeffekter
    .venv/bin/python kontroller/migreringslage.py <slug> --observera <url>  # observera kundens adress (två GET)
    .venv/bin/python kontroller/migreringslage.py --oversikt                # alla kunder och de äldre Vercel-projekten
"""
import argparse
import ipaddress
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import kundrepo  # noqa: E402

STEG = (('forberedd', 'Förberedd'), ('maltestad', 'Måltestad'), ('trafik_flyttad', 'Trafik flyttad'),
        ('data_avstamd', 'Data avstämd'), ('legacy_avvecklad', 'Legacy avvecklad'))
STATUS = ('ja', 'nej', 'inte_tillampligt')
EJ_KUNDADRESS = ('.workers.dev', '.vercel.app', '.pages.dev', '.cloudflareaccess.com')
UA = 'nortropic-migreringslage'  # Cloudflare spärrar Python-urllibs standardidentitet (1010) före Workern


def bestandsfil():
    return atelje.UNDERLAG / 'leverans' / 'VERCEL-BESTAND.json'


def bestand():
    """De äldre Vercel-projekten ur det privata beståndet: (lista, fel). Saknas filen är listan tom och felet None."""
    f = bestandsfil()
    if not f.is_file() or f.is_symlink():
        return [], None
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return [], 'beståndet kan inte läsas: %s' % type(e).__name__
    poster = d.get('projekt') if isinstance(d, dict) else None
    if not isinstance(poster, list):
        return [], 'beståndet saknar listan projekt'
    ut = []
    for p in poster:
        if not isinstance(p, dict) or not isinstance(p.get('projekt'), str) or p.get('status') not in ('kvar', 'avvecklad'):
            return [], 'beståndet har en ogiltig post'
        if p['status'] == 'avvecklad' and not p.get('belagg'):
            return [], '%s står som avvecklad utan belägg' % p['projekt']
        ut.append(p)
    return ut, None


def _steg(sid, status, belagg, **extra):
    assert status in STATUS
    return dict({'id': sid, 'namn': dict(STEG)[sid], 'status': status, 'belagg': belagg}, **extra)


def _senaste(slug, slag, villkor=lambda k: True):
    for k in reversed(kundrepo._kvitton(slug, slag)):
        if villkor(k):
            return k
    return None


def lage(slug):
    """Kundens migreringsläge: {'slug', 'steg': [...fem...], 'besked', 'migrerad', 'i_drift', 'legacy', 'worker', ...}.
    Läser bara kvitton, exportens aktualitet och det privata beståndet."""
    import exportera
    kundrepo.identitet(slug)  # ogiltig slug: ValueError
    i = kundrepo.identitet(slug)
    projekt, bestandsfel = bestand()
    legacy = [p for p in projekt if p.get('slug') == slug]
    steg = []

    e = exportera.aktuell(slug)
    if e and e.get('ok') and e.get('aktuell'):
        steg.append(_steg('forberedd', 'ja', 'export %s (commit %s)' % (e.get('id'), str(e.get('commit') or '')[:12])))
    else:
        steg.append(_steg('forberedd', 'nej', 'ingen aktuell export för Workers' if not e else 'exporten är inaktuell eller föll'))

    pv = kundrepo.preview_aktuell(slug)
    if pv and pv.get('aktuell') and pv.get('plattform') == 'cloudflare-workers':
        steg.append(_steg('maltestad', 'ja', 'förhandsvisning %s, version %s, skydd %s (%s)' % (
            pv.get('url'), pv.get('version_id'), pv.get('skydd') or 'inte prövat', pv.get('tid')), version=pv.get('version_id')))
    elif pv and pv.get('status') == 'klar' and pv.get('plattform') == 'cloudflare-workers':
        steg.append(_steg('maltestad', 'nej', 'förhandsvisningen %s gäller en äldre commit eller export' % pv.get('version_id')))
    else:
        steg.append(_steg('maltestad', 'nej', 'ingen klar förhandsvisning på Cloudflare' + ('' if not pv else ': ' + '; '.join(pv.get('hinder') or [pv.get('status') or '?']))))

    rel = _senaste(slug, 'RELEASE', lambda k: k.get('status') == 'klar')
    obs = _senaste(slug, 'TRAFIK', lambda k: rel is not None and str(k.get('tid') or '') >= str(rel.get('tid') or ''))
    if not rel:
        steg.append(_steg('trafik_flyttad', 'nej', 'ingen release till produktionens Worker'))
    elif not obs:
        steg.append(_steg('trafik_flyttad', 'nej', 'release %s (%s) finns, men kundens adress är inte observerad efter den'
                          % (rel.get('version_id'), rel.get('tid')), version=rel.get('version_id')))
    elif obs.get('dom') != 'cloudflare':
        steg.append(_steg('trafik_flyttad', 'nej', '%s svarade %s efter releasen (%s)' % (
            obs.get('adress'), {'vercel': 'från Vercel', 'okant': 'utan Workerns kännetecken'}.get(obs.get('dom'), '?'), obs.get('tid')),
            version=rel.get('version_id')))
    else:
        steg.append(_steg('trafik_flyttad', 'ja', '%s svarar från Workern %s (observerat %s; release %s)' % (
            obs.get('adress'), i['worker'], obs.get('tid'), rel.get('version_id')), version=rel.get('version_id')))

    med_data = [p for p in legacy if p.get('data')]
    if not med_data:
        steg.append(_steg('data_avstamd', 'inte_tillampligt', 'ingen äldre data på Vercel för kunden'))
    else:
        avst = _senaste(slug, 'DATAAVSTAMNING', lambda k: k.get('status') == 'avstamd')
        steg.append(_steg('data_avstamd', 'ja' if avst else 'nej', ('avstämd %s: %s' % (avst.get('tid'), avst.get('omfattning')))
                          if avst else 'äldre data finns (%s) och är inte avstämd' % ', '.join(p['projekt'] for p in med_data)))

    if not legacy:
        steg.append(_steg('legacy_avvecklad', 'inte_tillampligt', 'inget äldre Vercel-projekt för kunden'))
    else:
        kvar = [p for p in legacy if p['status'] != 'avvecklad']
        steg.append(_steg('legacy_avvecklad', 'nej' if kvar else 'ja',
                          ('kvar på Vercel: %s' % ', '.join(p['projekt'] for p in kvar)) if kvar
                          else 'avvecklat: %s' % '; '.join('%s (%s)' % (p['projekt'], p['belagg']) for p in legacy)))

    uppfyllda = all(s['status'] in ('ja', 'inte_tillampligt') for s in steg)
    migrerad = bool(legacy) and uppfyllda
    i_drift = steg[2]['status'] == 'ja'
    if migrerad:
        besked = 'migrerad: trafiken går till Cloudflare, och den äldre driften är avstämd och avvecklad'
    elif uppfyllda:
        besked = 'i drift på Cloudflare (ny kund, ingen äldre drift att migrera)'
    else:
        forsta = next(s for s in steg if s['status'] == 'nej')
        klara = [s['namn'].lower() for s in steg if s['status'] == 'ja']
        besked = '%s; nästa: %s' % (', '.join(klara) if klara else 'inte påbörjad', forsta['namn'].lower())
        if i_drift and legacy:
            besked += ' (trafiken är flyttad, men kunden är inte migrerad förrän den äldre driften är avstämd och avvecklad)'
    return {'schema': 1, 'slug': slug, 'tid': kundrepo.nu(), 'steg': steg, 'besked': besked, 'migrerad': migrerad,
            'i_drift': i_drift, 'legacy': [{k: p.get(k) for k in ('projekt', 'adress', 'status', 'data')} for p in legacy],
            'bestandsfel': bestandsfel, 'worker': {'produktion': i['worker'], 'forhandsvisning': i['worker_forhandsvisning'],
                                                    'forhandsvisning_version': (pv or {}).get('version_id'),
                                                    'produktion_version': (rel or {}).get('version_id')}}


def kundadress(adress):
    """Felet om adressen inte kan vara kundens egen produktionsadress, annars None."""
    try:
        u = urllib.parse.urlsplit(adress)
    except ValueError:
        return 'ogiltig adress'
    host = (u.hostname or '').lower().rstrip('.')
    if u.scheme != 'https' or not host or u.username or u.password:
        return 'adressen ska vara https://<kundens domän>'
    if u.path not in ('', '/') or u.query or u.fragment:
        return 'ange bara domänen'
    try:
        ipaddress.ip_address(host)
        return 'en IP-adress är inte kundens domän'
    except ValueError:
        pass
    if '.' not in host or host == 'localhost' or host.endswith('.localhost') or host.endswith('.local'):
        return 'en lokal adress är inte kundens domän'
    if host.endswith(EJ_KUNDADRESS) or '-forhandsvisning' in host:
        return 'en förhands- eller plattformsadress (%s) är inte kundens domän: trafiken räknas bara på kundens egen adress' % host
    return None


def hamta(url, frist=15):
    """(status, huvuden med gemena namn) för en GET utan att följa omdirigeringar."""
    class Stopp(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html'})
    try:
        r = urllib.request.build_opener(Stopp).open(req, timeout=frist)
        return r.status, {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}


def dom(start, api):
    """'cloudflare' när kundens adress svarar från Cloudflare och Workerns API-väg svarar som Workern (405, Allow: POST),
    'vercel' när Vercel svarar, annars 'okant'."""
    (s1, h1), (s2, h2) = start, api
    if any('x-vercel-id' in h for h in (h1, h2)) or any(str(h.get('server', '')).lower() == 'vercel' for h in (h1, h2)):
        return 'vercel'
    if (str(h1.get('server', '')).lower() == 'cloudflare' and 'cf-ray' in h1 and s2 == 405
            and 'POST' in str(h2.get('allow', '')).upper()):
        return 'cloudflare'
    return 'okant'


def observera_trafik(slug, adress, hamtare=None):
    """Observerar kundens adress (GET / och GET /api/forfragan/) och skriver kvittot TRAFIK-*.json. Ger kvittot."""
    kundrepo.identitet(slug)
    fel = kundadress(adress)
    if fel:
        raise ValueError(fel)
    hamtare = hamtare or hamta
    bas = adress.rstrip('/')
    tid = kundrepo.nu()
    post = {'schema': 1, 'id': 'TRAFIK-%s-%s' % (tid.replace(':', '').replace('-', ''), os.urandom(2).hex()),
            'typ': 'trafikobservation', 'slug': slug, 'tid': tid, 'adress': bas, 'dom': 'okant', 'svar': None, 'fel': None}
    try:
        start, api = hamtare(bas + '/'), hamtare(bas + '/api/forfragan/')
        post['dom'] = dom(start, api)
        post['svar'] = {'start': start[0], 'api': api[0], 'server': start[1].get('server'), 'cf_ray': 'cf-ray' in start[1],
                        'vercel': any('x-vercel-id' in h for h in (start[1], api[1])), 'allow': api[1].get('allow')}
    except (OSError, urllib.error.URLError, ValueError) as e:
        post['fel'] = 'adressen kunde inte hämtas: %s' % type(e).__name__
    d = kundrepo.leveransdir(slug)
    d.mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(d / (post['id'] + '.json'), post)
    return post


def oversikt():
    """Varje kund med kundrepo och varje äldre Vercel-projekt, utan sidoeffekter."""
    kunder = []
    if atelje.KUNDER.is_dir():
        for f in sorted(atelje.KUNDER.glob('*/KUNDREPO.json')):
            slug = f.parent.name
            if kundrepo.SLUG.match(slug):
                lg = lage(slug)
                kunder.append({'slug': slug, 'besked': lg['besked'], 'migrerad': lg['migrerad'], 'i_drift': lg['i_drift'],
                               'steg': {s['id']: s['status'] for s in lg['steg']}})
    projekt, fel = bestand()
    kopplade = {k['slug'] for k in kunder}
    return {'schema': 1, 'kunder': kunder, 'bestandsfel': fel,
            'legacy_utan_kund': [{k: p.get(k) for k in ('projekt', 'adress', 'status', 'data')} for p in projekt
                                 if not p.get('slug') or p.get('slug') not in kopplade],
            'besked': '%d kunder; %d äldre Vercel-projekt kvar' % (len(kunder), sum(1 for p in projekt if p['status'] == 'kvar'))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('slug', nargs='?')
    ap.add_argument('--observera', metavar='URL')
    ap.add_argument('--oversikt', action='store_true')
    a = ap.parse_args(argv)
    if a.oversikt == bool(a.slug):
        ap.error('ange en slug eller --oversikt')
    try:
        if a.oversikt:
            ut = oversikt()
        elif a.observera:
            ut = observera_trafik(a.slug, a.observera)
        else:
            ut = lage(a.slug)
    except ValueError as e:
        print(json.dumps({'fel': str(e)}, ensure_ascii=False))
        return 2
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
