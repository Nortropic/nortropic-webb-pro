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
    if p['fardighet'] == 'inaktuellt':
        raise ks.Vagrad('Paketet är inaktuellt: %s' % p['fardighet_omfattning'])
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
        # ett behov bär ett paket: ett annat paket för samma behov kräver ett eget behov från kunden (eller att det
        # tidigare valet avmarkeras), så att kundens läge aldrig sprids till paket kunden inte har bett om
        if behov and any(v['behov'] == behov and v['id'] != vid for v in d.get('integrationsval', {}).values()):
            raise ks.Vagrad('Kundens behov har redan ett paketval. Avmarkera det först, eller be kunden beskriva behovet för sig.')
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


def modellforslag(lista, kallor, revision, katalog=None):
    """Modellens förslag till funktioner, prövade mot katalogen och kundkällorna. Ett okänt paket blir en uttrycklig
    utredning (inget konto, ingen anslutning); ett förslag utan kundkälla fäller hela svaret. Förslagen blir aldrig val."""
    k = katalog or ik.las()
    paket = {p['id']: p for p in k['paket']}
    if not isinstance(lista, list) or len(lista) > 18:
        raise ks.Vagrad('Integrationsförslagen är för många eller ogiltiga.')
    ut, sedda = [], set()
    for f in lista:
        ks.falt(f, ('id', 'omrade', 'paket', 'kallor', 'nytta', 'alternativ', 'konsekvens', 'osakerhet', 'foljdfraga'),
                ('id', 'omrade', 'paket', 'kallor', 'nytta', 'alternativ', 'konsekvens', 'osakerhet', 'foljdfraga'))
        fid = ks.nyckel(f['id'])
        if not all(isinstance(f[n], str) for n in ('omrade', 'paket', 'nytta', 'alternativ', 'konsekvens', 'osakerhet', 'foljdfraga')):
            raise ks.Vagrad('Integrationsförslaget har fält av fel typ.')
        if fid in sedda:
            raise ks.Vagrad('Två integrationsförslag har samma id.')
        sedda.add(fid)
        if f['omrade'] not in ik.OMRADEN:
            raise ks.Vagrad('Integrationsförslaget har ett okänt område.')
        if not isinstance(f['kallor'], list) or not f['kallor'] or any(not isinstance(x, str) or x not in kallor for x in f['kallor']):
            raise ks.Vagrad('Integrationsförslaget saknar giltig kundkälla.')
        for n in ('nytta', 'alternativ', 'konsekvens', 'osakerhet'):
            ks.text(f[n], 1500)
        if not isinstance(f['foljdfraga'], str) or len(f['foljdfraga']) > 1500:
            raise ks.Vagrad('Följdfrågan är ogiltig.')
        p = paket.get(f['paket'])
        post = {**f, 'foljdfraga': f['foljdfraga'].strip() or None, 'utreds': False, 'avvisat_paket': None}
        if f['paket'] != 'utreds' and (not p or p['omrade'] != f['omrade'] or p['grund'] or p['fardighet'] == 'inaktuellt'):
            post.update(paket=None, utreds=True, avvisat_paket=str(f['paket'])[:80])  # T02: aldrig en påhittad anslutning
        elif f['paket'] == 'utreds':
            post.update(paket=None, utreds=True)
        else:
            post['paketversion'] = p['version']
        ut.append(post)
    return {'revision': revision, 'katalog': k['version'], 'avsandare': 'modell', 'forslag': ut}


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
        if p['fardighet'] == 'inaktuellt':
            inaktuella.append({'val': v['id'], 'paket': v['paket'], 'skal': 'paketet är inaktuellt: ' + p['fardighet_omfattning']})
            continue
        l, skal = lage(d, v, p)
        if l is None:
            inaktuella.append({'val': v['id'], 'paket': v['paket'], 'skal': skal})
            continue
        if p['version'] != v['paketversion']:
            versioner.append({'val': v['id'], 'paket': p['id'], 'vald': v['paketversion'], 'nu': p['version']})
        val.append({'omrade': v['omrade'], 'paket': v['paket'], 'lage': l, 'instans': v.get('instans')})
    pl = ik.planera(val, k, arende={'id': d['id'], 'revision': d['revision']})
    if any(x['lage'] == 'kundval' for x in pl['omfattning']) and not ks.vy(d)['bestallning']['aktuell']:
        pl['hinder'].append('kundens val ingår, men inget accepterat erbjudande gäller den aktuella omfattningen')
        pl['klar_for_bygge'] = False
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
        'forslag': d.get('integrationsforslag'),
        'behov': [{'id': i, 'behov': b['behov'], 'bestallning': b['bestallning'],
                   'anslutning': {'utredning': b['utredning'].get('status'), 'konto': b['utredning'].get('konto', {}).get('status'),
                                  'prov': b['utredning'].get('prov', {}).get('status')}} for i, b in sorted(behov.items())],
        'plan': plan(d, k),
    }
