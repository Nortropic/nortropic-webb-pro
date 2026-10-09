#!/usr/bin/env python3
"""Funktioner och anslutningar i Kundstarts ärende: ägarens val av paket ur integrationskatalogen
(kontroller/integrationer/katalog.json) för kundens integrationsbehov, och integrationsplanen ur valen (uppdraget
2026-10-09, etapp 3).

Kundens önskemål och ägarens paketval hålls isär. Ett val som pekar på ett av kundens behov får behovets
beställningsläge (onskemal, kundval, framtida, avstatt, okant, inte_relevant), aldrig ett eget: ägaren kan inte göra ett
önskemål till en beställning. Ett val utan behov är ett förslag (onskemal), utom för grundleveransens paket (katalogens
grund: true), som ingår utan att kunden kryssar i dem (hosting, formulär och dess avisering). Ändras behovet efter valet
blir valet inaktuellt och står utanför planen tills ägaren väljer igen. Planen räknas fram ur valen utan modell och
utan sidoeffekter (integrationskatalog.planera)."""
import time

import integrationskatalog as ik
import kundstart as ks


def _paket(k, pid):
    p = next((x for x in k['paket'] if x['id'] == pid), None)
    if not p:
        raise ks.Vagrad('Paketet finns inte i katalogen. Utred behovet i stället för att välja en okänd leverantör.')
    return p


def valj(lager, eid, revision, data, katalog=None):
    """Ägarens val av ett paket, med eller utan koppling till ett av kundens behov. Ger ärendets vy."""
    ks.falt(data, ('id', 'omrade', 'paket', 'behov', 'instans', 'motivering'), ('id', 'omrade', 'paket', 'motivering'))
    vid = ks.nyckel(data['id'])
    k = katalog or ik.las()
    p = _paket(k, data['paket'])
    if p['omrade'] != data['omrade']:
        raise ks.Vagrad('Paketet hör till %s, inte %s.' % (p['omrade'], data['omrade']))
    behov = data.get('behov')
    if behov is not None:
        ks.nyckel(behov)
    instans = data.get('instans')
    if instans is not None:
        ks.nyckel(instans)
    motivering = ks.text(data['motivering'], 2000)
    with lager.trans() as c:
        d = lager._doc(c, eid)
        if type(revision) is not int or d['revision'] != revision:
            raise ks.Konflikt('Ärendet har ändrats. Läs det aktuella läget innan du väljer.')
        b = d.get('integrationer', {}).get(behov) if behov else None
        if behov and not b:
            raise ks.Vagrad('Kundens behov finns inte i ärendet.')
        post = {'id': vid, 'omrade': p['omrade'], 'paket': p['id'], 'paketversion': p['version'], 'katalog': k['version'],
                'behov': behov, 'behov_sha256': b['behov_sha256'] if b else None, 'instans': instans,
                'motivering': motivering, 'avsandare': 'agare'}
        val = d.setdefault('integrationsval', {})
        fore = val.get(vid)
        if fore and {n: v for n, v in fore.items() if n != 'tid'} == post:
            return lager._vy(c, d)
        if fore:
            d['historik'].append({'slag': 'ersatt_integrationsval', 'val': fore, 'tid': time.time()})
        val[vid] = dict(post, tid=time.time())
        lager._spara(c, d)
        return lager._vy(c, d)


def avmarkera(lager, eid, revision, vid):
    ks.nyckel(vid)
    with lager.trans() as c:
        d = lager._doc(c, eid)
        if type(revision) is not int or d['revision'] != revision:
            raise ks.Konflikt('Ärendet har ändrats. Läs det aktuella läget innan du avmarkerar.')
        val = d.get('integrationsval', {})
        if vid not in val:
            raise ks.Vagrad('Valet finns inte.')
        d['historik'].append({'slag': 'avmarkerat_integrationsval', 'val': val.pop(vid), 'tid': time.time()})
        lager._spara(c, d)
        return lager._vy(c, d)


def lage(d, v, p):
    """(läge, besked) för ett val: behovets beställningsläge, grund, eller förslag; None när valet är inaktuellt."""
    if v.get('behov'):
        b = d.get('integrationer', {}).get(v['behov'])
        if not b:
            return None, 'kundens behov finns inte längre'
        if b['behov_sha256'] != v['behov_sha256']:
            return None, 'kundens behov har ändrats efter valet'
        return b['bestallning'], None
    return ('grund', None) if p and p.get('grund') else ('onskemal', None)


def plan(d, katalog=None):
    """Integrationsplanen för ärendet, med de inaktuella valen och ändrade paketversioner redovisade för sig."""
    k = katalog or ik.las()
    paket = {p['id']: p for p in k['paket']}
    val, inaktuella, versioner = [], [], []
    for v in sorted(d.get('integrationsval', {}).values(), key=lambda x: x['id']):
        p = paket.get(v['paket'])
        if not p:
            inaktuella.append({'val': v['id'], 'paket': v['paket'], 'skal': 'paketet finns inte längre i katalogen'})
            continue
        l, skal = lage(d, v, p)
        if l is None:
            inaktuella.append({'val': v['id'], 'paket': v['paket'], 'skal': skal})
            continue
        if p['version'] != v['paketversion']:
            versioner.append({'val': v['id'], 'paket': p['id'], 'vald': v['paketversion'], 'nu': p['version']})
        val.append({'omrade': v['omrade'], 'paket': v['paket'], 'lage': l, 'instans': v.get('instans')})
    pl = ik.planera(val, k, arende={'id': d['id'], 'revision': d['revision']})
    pl['inaktuella_val'] = inaktuella
    pl['andrade_paketversioner'] = versioner
    if inaktuella or versioner:
        pl['klar_for_bygge'] = False
    return pl


def vy(d, katalog=None):
    """Katalogens områden med paketen, ärendets val och kundens behov, för ägarens vy. Läser bara."""
    k = katalog or ik.las()
    behov = d.get('integrationer', {})
    return {
        'katalog': k['version'],
        'omraden': [{'id': o['id'], 'namn': o['namn'],
                     'paket': [{n: p[n] for n in ('id', 'version', 'niva', 'funktion', 'fardighet', 'fardighet_omfattning', 'grund')}
                               for p in k['paket'] if p['omrade'] == o['id']]} for o in k['omraden']],
        'val': sorted(d.get('integrationsval', {}).values(), key=lambda x: (x['omrade'], x['id'])),
        'behov': [{'id': i, 'behov': b['behov'], 'bestallning': b['bestallning'],
                   'anslutning': {'utredning': b['utredning'].get('status'), 'konto': b['utredning'].get('konto', {}).get('status'),
                                  'prov': b['utredning'].get('prov', {}).get('status')}} for i, b in sorted(behov.items())],
        'plan': plan(d, k),
    }
