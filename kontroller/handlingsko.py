#!/usr/bin/env python3
"""handlingsko.py — "Detta behöver vi från kunden": handlingskön ur ett Kundstart-ärendes integrationsplan (ägarens
tillägg 2026-10-10 ~10:45Z, punkt 1; BESLUT.md).

Kön räknas fram vid varje läsning, aldrig skriven för hand: varje paket i planens omfattning ger sina människors
handlingar ur katalogen (handling, ansvarig, skäl, vad som kan fortsätta under väntan och belägg), planens hinder och
saknade beroenden blir ägarens poster, och val som kunden gjort inaktuella ger inaktuella poster. En post är klar bara
när varje belägg finns: ett kvitto eller en observation (kontot, förhandsvisningen, releasen, trafiken, nyckelintaget,
VERKSAMHET.json, aktiveringens kvitton) eller, där inget verktyg kan observera handlingen, ägarens intyg med en
referens till vad som visar att den är gjord (intyga) — aldrig ett kryss. Läsningen har inga sidoeffekter.

Kundens vy (kundvy) visar samma poster med status och ansvarig, utan beläggens detaljer och utan ägarens handlingar.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

ANSVARIG_TEXT = {'kund': 'verksamheten', 'agare': 'ägaren', 'nortropic': 'Nortropic'}


def post_id(paket, handling):
    return hashlib.sha256(('%s\n%s' % (paket, handling)).encode()).hexdigest()[:16]


def _verksamhet(slug, vag):
    import atelje
    try:
        v = json.loads((atelje.UNDERLAG / slug / 'VERKSAMHET.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    for del_ in vag.split('.'):
        v = v.get(del_) if isinstance(v, dict) else None
    return v


def belagg(slug, d, typ, pid):
    """(finns, text) för ett belägg. Läser bara."""
    import kundrepo
    if typ == 'intyg':
        i = (d.get('intyg') or {}).get(pid)
        return (bool(i), 'ägarens intyg %s: %s' % (time.strftime('%Y-%m-%d', time.gmtime(i['tid'])), i['referens']) if i else 'inget intyg')
    if typ == 'konto':
        konto, hinder = kundrepo.cloudflare_konto()
        return (bool(konto), 'kontot är anslutet' if konto else 'kontot är inte anslutet')
    if typ == 'forhandsvisning':
        pv = kundrepo.preview_aktuell(slug)
        ok = bool(pv and pv.get('aktuell') and pv.get('plattform') == 'cloudflare-workers' and not str(pv.get('skydd') or '').startswith('öppen'))
        return ok, ('förhandsvisning %s bakom Access (%s)' % (pv.get('version_id'), pv.get('skydd')) if ok else 'ingen aktuell skyddad förhandsvisning')
    if typ == 'release':
        rel = [k for k in kundrepo._kvitton(slug, 'RELEASE') if k.get('status') == 'klar']
        return (bool(rel), 'release %s (%s)' % (rel[-1].get('version_id'), rel[-1].get('tid')) if rel else 'ingen release')
    if typ == 'trafik':
        import migreringslage
        s = migreringslage.lage(slug)['steg'][2]
        return s['status'] == 'ja', s['belagg']
    if typ.startswith('nyckel:'):
        import nyckelintag
        s = nyckelintag.status(slug).get(typ.split(':', 1)[1]) or {}
        return (bool(s.get('nyckel')), 'nyckeln lämnad %s (version %s)' % (s.get('nyckel_lagd'), s.get('version')) if s.get('nyckel') else 'ingen nyckel i intaget')
    if typ.startswith('intag:'):
        import nyckelintag
        lev, falt = typ.split(':', 1)[1].split('.', 1)
        v = ((nyckelintag.status(slug).get(lev) or {}).get('falt') or {}).get(falt)
        return (bool(v), '%s lämnad i intaget' % falt if v else '%s saknas i intaget' % falt)
    if typ.startswith('verksamhet:'):
        v = _verksamhet(slug, typ.split(':', 1)[1])
        return (bool(v), '%s finns i VERKSAMHET.json' % typ.split(':', 1)[1] if v else '%s saknas i VERKSAMHET.json' % typ.split(':', 1)[1])
    if typ.startswith('aktivering:'):
        import aktivera
        s = aktivera.senaste_steg(slug).get(typ.split(':', 1)[1]) or {}
        return (s.get('status') == 'klar', 'aktiveringen %s (%s)' % (s.get('status'), s.get('tid')) if s else 'inte aktiverat')
    return False, 'okänt belägg'


def ko(d, katalog=None):
    """Handlingskön för ärendet d (Kundstarts interna dokument): {'poster', 'sammanfattning', 'katalog'}."""
    import integrationskatalog as ik
    import kundstart_integration as ki
    k = katalog or ik.las()
    paket = {p['id']: p for p in k['paket']}
    pl = ki.plan(d, k)
    slug = d['slug']
    poster = []

    def lagg(paket_id, m, status=None, varfor=None):
        pid = post_id(paket_id, m['handling'])
        b = [] if status else [dict(zip(('typ', 'finns', 'text'), (t, *belagg(slug, d, t, pid)))) for t in m['belagg']]
        poster.append({'id': pid, 'paket': paket_id, 'handling': m['handling'], 'ansvarig': m['ansvarig'],
                       'ansvarig_text': ANSVARIG_TEXT.get(m['ansvarig'], m['ansvarig']), 'skal': m['skal'],
                       'under_vantan': m['under_vantan'], 'belagg': b, 'intyg_kan': 'intyg' in m.get('belagg', []),
                       'status': status or ('klar' if b and all(x['finns'] for x in b) else 'vantar'), 'varfor': varfor})
    for m in pl['manniska']:
        lagg(m['paket'], m)
    for h in pl['hinder']:
        lagg('plan', {'handling': 'Lös hindret i planen: %s' % h, 'ansvarig': 'agare', 'skal': 'planen är inte klar för bygge',
                      'under_vantan': 'allt som inte beror på hindret', 'belagg': []}, status='vantar')
    for sb in pl['saknade_beroenden']:
        lagg('plan', {'handling': 'Välj ett paket som ger %s (krävs av %s)' % (sb['kraver'], sb['paket']), 'ansvarig': 'agare',
                      'skal': 'ett valt paket kräver det', 'under_vantan': 'allt utom det paketet', 'belagg': []}, status='vantar')
    sedda = {p['id'] for p in poster}
    for ia in pl.get('inaktuella_val') or []:
        for m in (paket.get(ia['paket']) or {}).get('manniska') or []:
            if post_id(ia['paket'], m['handling']) not in sedda:
                lagg(ia['paket'], m, status='inaktuell', varfor=ia['skal'])
    ordning = {'vantar': 0, 'klar': 1, 'inaktuell': 2}
    poster.sort(key=lambda p: (ordning[p['status']], ('kund', 'agare', 'nortropic').index(p['ansvarig']) if p['ansvarig'] in ('kund', 'agare', 'nortropic') else 9, p['paket']))
    summa = {s: sum(1 for p in poster if p['status'] == s) for s in ordning}
    summa['vantar_pa_kunden'] = sum(1 for p in poster if p['status'] == 'vantar' and p['ansvarig'] == 'kund')
    return {'katalog': k['version'], 'plan_sha256': pl['plan_sha256'], 'poster': poster, 'sammanfattning': summa}


def kundvy(k):
    """Kundens vy av kön: handling, skäl, ansvarig, vad som kan fortsätta och status, utan beläggens detaljer."""
    if 'poster' not in k:
        return {'fel': 'Kön kunde inte läsas.'}
    return {'poster': [{n: p[n] for n in ('id', 'handling', 'ansvarig', 'ansvarig_text', 'skal', 'under_vantan', 'status')}
                       | {'nyckel': next((b['typ'].split(':', 1)[1] for b in p['belagg'] if b['typ'].startswith('nyckel:')), None)}
                       for p in k['poster']], 'sammanfattning': k['sammanfattning']}


def intyga(lager, eid, revision, data):
    """Ägarens intyg för en post vars belägg är ett intyg: en referens till vad som visar att handlingen är gjord."""
    import kundstart as ks
    ks.falt(data, ('post', 'referens'), ('post', 'referens'))
    pid = ks.nyckel(data['post'])
    referens = ks.text(data['referens'], 500)
    if len(referens.strip()) < 12:
        raise ks.Vagrad('Ange vad som visar att handlingen är gjord (till exempel datum och bekräftelsens id), inte bara ett kryss.')
    with lager.trans() as c:
        d = lager._doc(c, eid)
        if type(revision) is not int or d['revision'] != revision:
            raise ks.Konflikt('Ärendet har ändrats. Läs det aktuella läget först.')
        post = next((p for p in ko(d)['poster'] if p['id'] == pid), None)
        if not post or not post['intyg_kan'] or post['status'] == 'inaktuell':
            raise ks.Vagrad('Posten finns inte i den aktuella kön eller kan inte intygas.')
        d.setdefault('intyg', {})[pid] = {'referens': referens, 'tid': time.time(), 'handling': post['handling'], 'paket': post['paket']}
        lager._spara(c, d)
        return lager._vy(c, d)


def lamna_nyckel(lager, eid, data, kalla):
    """En nyckel och/eller uppgifter till nyckelintaget för ärendets kund. Svaret och ärendet bär aldrig nyckeln, bara
    att den lämnades; ärendet får en händelse utan värden så att revisionen följer."""
    import kundstart as ks
    import nyckelintag
    ks.falt(data, ('leverantor', 'nyckel', 'falt'), ('leverantor',))
    if data.get('falt') is not None and not isinstance(data['falt'], dict):
        raise ks.Vagrad('Uppgifterna ska vara ett objekt.')
    with lager.trans() as c:
        d = lager._doc(c, eid)
    try:
        s = nyckelintag.lamna(d['slug'], data['leverantor'], data.get('nyckel') or None, data.get('falt') or {}, kalla)
    except nyckelintag.Fel as e:
        raise ks.Vagrad(str(e))
    return s
