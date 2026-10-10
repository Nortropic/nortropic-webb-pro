#!/usr/bin/env python3
"""aktivera.py — kundens aktivering på Cloudflare, från valda funktioner till aktiverade resurser (ägarens tillägg
2026-10-10 ~10:45Z, punkt 2; BESLUT.md).

Torrkörningen (torr, standard på kommandoraden) listar varje steg och vad som saknas, utan sidoeffekter och utan nät:
kontot, kundens D1 och R2 med EU-jurisdiktion, driftvärdena i underlag/<slug>/CLOUDFLARE.json (ur nyckelintaget och
Kundstarts plan), en ny export, D1-schemat (migreringarna) och nycklarna i produktionens Worker. Planen har en
plan_sha256.

Körningen (kor) kräver ägarens mandat för just den planen: AKTIVERINGSMANDAT.json som dashboarden skriver när ägaren
klickar på aktiveringen i Byggflöde (som releasemandatet). Mandatet gäller en körning. Allt sker under kundens lås;
avsikten skrivs i kvittot (kunder/<slug>/leverans/AKTIVERING-*.json) före varje extern operation och resultatet efter;
ett okänt utfall (tidsgräns, nätfel) stoppar körningen och stäms av mot Cloudflare (stam_av, läsande) före ett nytt
försök. Bara kundens egna resurser (kund-<slug>-forfragningar, kund-<slug>-bilagor, Workern kund-<slug>) och bara det
anslutna kontot; en fiktiv verksamhet torrkörs men aktiveras aldrig.

Nycklar läggs bara i en Worker som redan finns: `wrangler secret put` driftsätter en ny version av Workern direkt
(Cloudflares dokumentation, läst 2026-10-10), så före första releasen väntar steget, och aktiveringen efter releasen
lägger dem. Nyckeln läses ur nyckelintaget (nyckelintag.las_for_aktivering) och går bara till Wranglers stdin.

    .venv/bin/python kontroller/aktivera.py <slug>            # torrkörning
    .venv/bin/python kontroller/aktivera.py <slug> --kor      # körning med ägarens mandat
    .venv/bin/python kontroller/aktivera.py <slug> --stam-av  # stäm av ett okänt utfall (läsande)
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import kundrepo  # noqa: E402
import nyckelintag  # noqa: E402

ROUTINGDOMAN = 'notis.nortropic.se'  # Nortropics routing-domän för formulärets avsändare (K04, BESLUT.md 2026-10-10)
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
NATFEL = re.compile(r'ETIMEDOUT|ECONNRESET|ECONNREFUSED|socket hang up|fetch failed|network|tidsgränsen', re.I)
FRIST = 300


class Fel(ValueError):
    pass


def namn(slug):
    i = kundrepo.identitet(slug)
    return {'worker': i['worker'], 'd1': '%s-forfragningar' % i['worker'], 'r2': '%s-bilagor' % i['worker']}


def driftfil(slug):
    return atelje.UNDERLAG / slug / 'CLOUDFLARE.json'


def mandatfil(slug):
    return kundrepo.leveransdir(slug) / 'AKTIVERINGSMANDAT.json'


def valda_paket(slug):
    """Paketen i omfattningen ur kundens Kundstart-plan (kundval och grund), eller None utan ärende. Läser bara: ett
    ärendelager som inte finns skapas inte."""
    fil = atelje.UNDERLAG / 'kundstart' / 'arenden.sqlite3'
    if not fil.is_file():
        return None
    import kundstart as ks
    import kundstart_integration as ki
    lager = ks.Lager(atelje.UNDERLAG / 'kundstart')
    with lager.trans() as c:
        r = c.execute('SELECT id FROM arenden WHERE slug = ?', (slug,)).fetchone()
    if not r:
        return None
    return sorted({x['paket'] for x in ki.plan(lager.internt(r[0]))['omfattning']})


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _las_json(fil):
    try:
        return json.loads(fil.read_text(encoding='utf-8')) if fil.is_file() and not fil.is_symlink() else None
    except (OSError, ValueError):
        return None


def kvitton(slug):
    return kundrepo._kvitton(slug, 'AKTIVERING')


def senaste_steg(slug):
    """Varje stegs senaste kända utfall ur aktiveringens kvitton: {steg: {'status', 'tid', 'detalj'}}."""
    ut = {}
    for k in kvitton(slug):
        for s in k.get('steg') or []:
            if s.get('status') in ('klar', 'fel', 'osaker', 'avstamd_ingen'):
                ut[s['id']] = {'status': s['status'], 'tid': s.get('klar_tid') or k.get('tid'), 'detalj': s.get('detalj')}
    return ut


def osaker(slug):
    """Det senaste kvittot om det har ett okänt utfall som inte stämts av, annars None."""
    oklar = None
    for k in kvitton(slug):
        if k.get('status') == 'osaker':
            oklar = k
        elif oklar and k.get('avstammer') == oklar.get('id'):
            oklar = None
    return oklar


def onskade_driftvarden(slug, valda, intag, befintliga):
    """(driftvärdena som aktiveringen ska skriva, saknade uppgifter). database_id tas ur befintliga eller D1-steget."""
    d = {}
    saknas = []
    if befintliga and befintliga.get('database_id'):
        d['database_id'] = befintliga['database_id']
    mottagare = (intag.get('epost') or {}).get('falt', {}).get('mottagare')
    if mottagare:
        d['forfragan_till'] = mottagare
    else:
        saknas.append('formulärets mottagare (nyckelintaget: epost, mottagare)')
    d['forfragan_fran'] = '%s@%s' % (slug, ROUTINGDOMAN)
    for lev, info in nyckelintag.LEVERANTORER.items():
        if lev == 'epost' or info['paket'] not in (valda or []):
            continue
        for falt, drift in info['drift'].items():
            v = (intag.get(lev) or {}).get('falt', {}).get(falt)
            if v:
                d[drift] = v
            else:
                saknas.append('%s: %s (nyckelintaget)' % (info['namn'], falt))
    return d, saknas


def torr(slug, valda=None):
    """Torrkörningen: stegen med status klar, gors, saknas eller vantar, och vad som saknas. Inga sidoeffekter, inget nät."""
    import exportera
    n = namn(slug)
    valda = valda_paket(slug) if valda is None else valda
    intag = nyckelintag.status(slug)
    befintliga = _las_json(driftfil(slug)) or {}
    gjort = senaste_steg(slug)
    konto, konto_hinder = kundrepo.cloudflare_konto()
    steg = []

    def lagg(sid, text, status, extern, kommando=None, varfor=None):
        steg.append({'id': sid, 'text': text, 'status': status, 'extern': extern, 'kommando': kommando, 'varfor': varfor})

    lagg('konto', 'Nortropics Cloudflare-konto', 'klar' if konto else 'saknas', False, varfor=konto_hinder)
    if befintliga.get('database_id'):
        lagg('d1', 'D1 %s med EU-jurisdiktion' % n['d1'], 'klar', True, varfor='database_id finns i CLOUDFLARE.json')
    else:
        lagg('d1', 'D1 %s med EU-jurisdiktion' % n['d1'], 'gors', True, 'wrangler d1 create %s --jurisdiction eu' % n['d1'])
    lagg('r2', 'R2 %s med EU-jurisdiktion' % n['r2'], 'klar' if (gjort.get('r2') or {}).get('status') == 'klar' else 'gors', True,
         'wrangler r2 bucket create %s --jurisdiction eu (om den saknas)' % n['r2'])
    onskade, saknas = onskade_driftvarden(slug, valda, intag, befintliga)
    lika = all(befintliga.get(k) == v for k, v in onskade.items())
    if saknas:
        lagg('driftvarden', 'Driftvärdena i CLOUDFLARE.json', 'saknas', False, varfor='saknas: ' + '; '.join(saknas))
    else:
        lagg('driftvarden', 'Driftvärdena i CLOUDFLARE.json', 'klar' if lika and 'database_id' in befintliga else 'gors', False,
             varfor=', '.join(sorted(onskade)))
    e = None
    try:
        e = exportera.aktuell(slug)
    except (OSError, ValueError):
        e = None
    konfig = ''
    try:
        konfig = (kundrepo.repo(slug) / 'wrangler.jsonc').read_text(encoding='utf-8')
    except OSError:
        pass
    i_export = bool(e and e.get('aktuell')) and all(str(v) in konfig for v in onskade.values()) and 'AKTIVERAS-VID-LANSERING' not in konfig
    lagg('export', 'Ny export med driftvärdena', 'klar' if i_export and steg[-1]['status'] == 'klar' else 'gors', False,
         'exportera.py %s --git' % slug)
    migreringar = sorted(f.name for f in (atelje.ROOT / 'mall' / 'leverans' / 'migrations').glob('*.sql'))
    m = gjort.get('migreringar') or {}
    lagg('migreringar', 'D1-schemat (%s)' % ', '.join(migreringar), 'klar' if m.get('status') == 'klar' and m.get('detalj') == migreringar else 'gors',
         True, 'wrangler d1 migrations apply DB --remote')
    releasad = any(k.get('status') == 'klar' for k in kundrepo._kvitton(slug, 'RELEASE'))
    for lev, info in nyckelintag.LEVERANTORER.items():
        if not info['hemlighet'] or info['paket'] not in (valda or []):
            continue
        sid = 'hemlighet:%s' % info['hemlighet']
        s = intag[lev]
        tidigare = gjort.get(sid) or {}
        if s.get('aterkallad'):
            status = 'klar' if tidigare.get('detalj') == 'borttagen' else 'gors'
            lagg(sid, 'Ta bort %s ur Workern (återkallad)' % info['hemlighet'], status if releasad else 'vantar', True,
                 'wrangler secret delete %s --name %s' % (info['hemlighet'], n['worker']))
        elif not s.get('nyckel'):
            lagg(sid, 'Nyckeln %s i Workern' % info['hemlighet'], 'saknas', True, varfor='nyckeln saknas i nyckelintaget (%s)' % info['namn'])
        elif not releasad:
            lagg(sid, 'Nyckeln %s i Workern' % info['hemlighet'], 'vantar', True,
                 varfor='efter första releasen: wrangler secret put driftsätter Workern, och produktionen släpps bara med ditt klick')
        else:
            status = 'klar' if tidigare.get('status') == 'klar' and tidigare.get('detalj') == 'version %s' % s.get('version') else 'gors'
            lagg(sid, 'Nyckeln %s i Workern (version %s)' % (info['hemlighet'], s.get('version')), status, True,
                 'wrangler secret put %s --name %s' % (info['hemlighet'], n['worker']))
    hinder = []
    if kundrepo.fiktiv(slug):
        hinder.append('en fiktiv verksamhet torrkörs men aktiveras aldrig')
    if valda is None:
        hinder.append('inget Kundstart-ärende för kunden: valen styr vilka nycklar och driftvärden som behövs')
    if osaker(slug):
        hinder.append('ett tidigare försök (%s) har okänt utfall: stäm av först (aktivera.py %s --stam-av)' % (osaker(slug)['id'], slug))
    saknade = [s for s in steg if s['status'] == 'saknas']
    att_gora = [s for s in steg if s['status'] == 'gors']
    plan = {'slug': slug, 'konto': konto['konto'] if konto else None, 'steg': [(s['id'], s['status'], s['kommando']) for s in steg],
            'driftvarden': onskade, 'nyckelversioner': {k: v.get('version') for k, v in intag.items() if v.get('nyckel')}}
    return {'schema': 1, 'slug': slug, 'tid': kundrepo.nu(), 'valda': valda, 'steg': steg, 'hinder': hinder,
            'saknas': [s['varfor'] or s['text'] for s in saknade], 'att_gora': len(att_gora),
            'kan_koras': not hinder and not saknade and bool(att_gora), 'plan_sha256': _sha(plan)}


def aktiveringsmandat(slug, kalla, plan_sha256):
    """Ägarens mandat för en aktivering, skrivet av dashboardens skrivande väg vid klicket i Byggflöde och bundet till
    torrkörningens plan_sha256. En session skriver det aldrig."""
    if kalla != 'dashboard':
        raise Fel('mandatet för en aktivering är ägarens klick i dashboarden')
    t = torr(slug)
    if not t['kan_koras']:
        raise Fel('ingen aktivering: ' + '; '.join(t['hinder'] + t['saknas'] or ['inget att göra']))
    if t['plan_sha256'] != plan_sha256:
        raise Fel('planen har ändrats sedan du såg den: läs torrkörningen igen')
    post = {'schema': 1, 'typ': 'aktiveringsmandat', 'slug': slug, 'tid': kundrepo.nu(), 'kalla': kalla, 'plan_sha256': plan_sha256}
    kundrepo.leveransdir(slug).mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(mandatfil(slug), post)
    return post


def standard_wrangler(slug, konto, tmp):
    """Wrangler i en fryst kopia av kundrepots HEAD (npm ci), med bara kontots token: kor(args, stdin=None) → (rc, utdata)."""
    r = kundrepo.repo(slug)
    underlag = kundrepo.fryst_underlag(r, kundrepo.huvud(r), tmp)
    ci = subprocess.run(['npm', 'ci', '--no-audit', '--no-fund', '--ignore-scripts'], cwd=str(underlag), capture_output=True, text=True,
                        timeout=900, env={k: v for k, v in os.environ.items() if not k.startswith(('NWP_', 'CLAUDE', 'CLOUDFLARE', 'ANTHROPIC'))})
    if ci.returncode:
        raise RuntimeError('npm ci föll')
    vem = subprocess.run([str(underlag / 'node_modules' / '.bin' / 'wrangler'), 'whoami'], cwd=str(underlag), capture_output=True, text=True,
                         timeout=120, env=kundrepo.cloudflare_miljo(konto, tmp))
    if vem.returncode or konto['konto'] not in (vem.stdout or '') + (vem.stderr or ''):
        raise RuntimeError('tokenen når inte kontot %s…' % konto['konto'][:6])

    def kor(args, stdin=None):
        try:
            res = subprocess.run([str(underlag / 'node_modules' / '.bin' / 'wrangler'), *args], cwd=str(underlag), capture_output=True,
                                 text=True, timeout=FRIST, input=stdin, env=kundrepo.cloudflare_miljo(konto, tmp))
            return res.returncode, (res.stdout or '') + '\n' + (res.stderr or '')
        except subprocess.TimeoutExpired:
            return 124, 'tidsgränsen %d s nåddes' % FRIST
    return kor


def _utfall(rc, ut):
    if rc == 0:
        return 'klar'
    return 'osaker' if rc == 124 or NATFEL.search(ut or '') else 'fel'


def _d1_id(ut, d1namn):
    """D1-id:t för just kundens databas ur en lista (wrangler d1 list --json) eller ett skapande; None om det saknas."""
    try:
        start = min([i for i in (ut.find('['), ut.find('{')) if i >= 0])
        lista = json.loads(ut[start:])
        for x in lista if isinstance(lista, list) else [lista]:
            if isinstance(x, dict) and x.get('name') == d1namn and UUID.fullmatch(str(x.get('uuid') or '')):
                return x['uuid']
    except (ValueError, json.JSONDecodeError):
        pass
    m = re.search(r'"?database_name"?\s*[:=]\s*"%s".*?"?database_id"?\s*[:=]\s*"(%s)"' % (re.escape(d1namn), UUID.pattern), ut or '', re.S)
    return m.group(1) if m else None


def kor(slug, wrangler=None, exportera_fn=None):
    """Aktiveringen med ägarens mandat, under kundens lås. Ger kvittot."""
    import flodesstart
    import korregister
    with flodesstart.las(atelje.ROOT, slug, arv=True):
        t = torr(slug)
        tid = kundrepo.nu()
        post = {'schema': 1, 'id': 'AKTIVERING-%s-%s' % (tid.replace(':', '').replace('-', ''), os.urandom(2).hex()), 'typ': 'aktivering',
                'slug': slug, 'tid': tid, 'plan_sha256': t['plan_sha256'], 'konto': None, 'mandat': None, 'steg': [], 'status': 'fel',
                'hinder': []}
        d = kundrepo.leveransdir(slug)
        d.mkdir(parents=True, exist_ok=True)
        fil = d / (post['id'] + '.json')

        def spara():
            atelje.skriv_json_atomiskt(fil, post)
        m = _las_json(mandatfil(slug))
        if t['hinder'] or t['saknas']:
            post['hinder'] += t['hinder'] + ['saknas: ' + x for x in t['saknas']]
            post['status'] = 'vantar_pa_avstamning' if osaker(slug) else 'hinder'
        elif not t['att_gora']:
            post['status'] = 'inget_att_gora'
        elif not m or m.get('kalla') != 'dashboard' or m.get('anvant_av') or m.get('slug') != slug or m.get('plan_sha256') != t['plan_sha256']:
            post['hinder'].append('inget mandat från ägaren för den här planen: aktiveringen startas av ägarens klick i Byggflöde')
            post['status'] = 'vantar_pa_mandat'
        if post['hinder'] or post['status'] == 'inget_att_gora':
            post['text'] = 'ingen aktivering: ' + ('; '.join(post['hinder']) or 'inget att göra')
            spara()
            return post
        # mandatet gäller en körning: det förbrukas före första operationen, så att en ny start aldrig återanvänder det
        atelje.skriv_json_atomiskt(mandatfil(slug), dict(m, anvant_av=post['id']))
        post['mandat'] = {k: m.get(k) for k in ('tid', 'kalla', 'plan_sha256')}
        konto, hinder = kundrepo.cloudflare_konto()
        post['konto'] = konto['konto'] if konto else None
        n = namn(slug)
        tmps = [korregister.egen_tmp('nwp-aktivering-', 'aktiveringens Wrangler')]
        try:
            w = wrangler(slug, konto, tmps[0]) if wrangler else standard_wrangler(slug, konto, tmps[0])
            onskade = {}
            for s in t['steg']:
                if s['status'] != 'gors':
                    continue
                rad = {'id': s['id'], 'status': 'pagar', 'avsikt_tid': kundrepo.nu(), 'klar_tid': None, 'detalj': None, 'fel': None}
                post['steg'].append(rad)
                spara()  # avsikten före operationen
                if s['id'] == 'd1':
                    rc, ut = w(['d1', 'list', '--json'])
                    uuid = _d1_id(ut, n['d1']) if rc == 0 else None
                    if rc == 0 and not uuid:
                        rc, ut = w(['d1', 'create', n['d1'], '--jurisdiction', 'eu'])
                        uuid = _d1_id(ut, n['d1']) if rc == 0 else None
                    rad['status'] = _utfall(rc, ut) if rc else ('klar' if uuid else 'fel')
                    rad['detalj'] = uuid
                    if uuid:
                        onskade['database_id'] = uuid
                elif s['id'] == 'r2':
                    rc, ut = w(['r2', 'bucket', 'list', '--jurisdiction', 'eu'])
                    finns = rc == 0 and re.search(r'(^|\s|")%s("|\s|$)' % re.escape(n['r2']), ut or '', re.M)
                    if rc == 0 and not finns:
                        rc, ut = w(['r2', 'bucket', 'create', n['r2'], '--jurisdiction', 'eu'])
                    rad['status'] = _utfall(rc, ut)
                elif s['id'] == 'driftvarden':
                    befintliga = _las_json(driftfil(slug)) or {}
                    vard, _ = onskade_driftvarden(slug, t['valda'], nyckelintag.status(slug), befintliga)
                    vard.update(onskade)
                    if 'database_id' not in vard:
                        rad.update(status='fel', fel='database_id saknas')
                    else:
                        driftfil(slug).parent.mkdir(parents=True, exist_ok=True)
                        atelje.skriv_json_atomiskt(driftfil(slug), vard)
                        rad['status'] = 'klar'; rad['detalj'] = sorted(vard)
                elif s['id'] == 'export':
                    res = (exportera_fn or _exportera)(slug)
                    rad['status'] = 'klar' if res.get('ok') else 'fel'
                    rad['detalj'] = res.get('id') or res.get('fel')
                    if res.get('ok') and wrangler is None:  # Wrangler i den nya exportens commit (med kundens database_id)
                        tmps.append(korregister.egen_tmp('nwp-aktivering-', 'aktiveringens Wrangler efter exporten'))
                        w = standard_wrangler(slug, konto, tmps[-1])
                elif s['id'] == 'migreringar':
                    # fel kund nekas: database_id i CLOUDFLARE.json ska vara just kundens databas hos det anslutna kontot
                    rc, ut = w(['d1', 'list', '--json'])
                    uuid = _d1_id(ut, n['d1']) if rc == 0 else None
                    if rc == 0 and uuid != (_las_json(driftfil(slug)) or {}).get('database_id'):
                        rc, ut = 1, ''
                        rad['fel'] = 'database_id i CLOUDFLARE.json är inte kundens databas %s' % n['d1']
                    elif rc == 0:
                        rc, ut = w(['d1', 'migrations', 'apply', 'DB', '--remote'])
                    rad['status'] = _utfall(rc, ut)
                    rad['detalj'] = sorted(f.name for f in (atelje.ROOT / 'mall' / 'leverans' / 'migrations').glob('*.sql'))
                elif s['id'].startswith('hemlighet:'):
                    namn_ = s['id'].split(':', 1)[1]
                    lev = next(k for k, v in nyckelintag.LEVERANTORER.items() if v['hemlighet'] == namn_)
                    if 'delete' in (s['kommando'] or ''):
                        rc, ut = w(['secret', 'delete', namn_, '--name', n['worker']], 'y\n')
                        rad['detalj'] = 'borttagen'
                    else:
                        nyckel = nyckelintag.las_for_aktivering(slug, lev)
                        if not nyckel:
                            rc, ut = 1, 'nyckeln saknas'
                        else:
                            rc, ut = w(['secret', 'put', namn_, '--name', n['worker']], nyckel)
                        rad['detalj'] = 'version %s' % nyckelintag.status(slug)[lev].get('version')
                    rad['status'] = _utfall(rc, ut)
                rad['klar_tid'] = kundrepo.nu()
                if rad['status'] != 'klar':
                    rad['fel'] = rad.get('fel') or 'steget gav inte ett bekräftat resultat'
                    spara()
                    break
                spara()
            post['status'] = ('klar' if all(r['status'] == 'klar' for r in post['steg'])
                              else 'osaker' if any(r['status'] == 'osaker' for r in post['steg']) else 'fel')
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as e_:
            post['hinder'].append('aktiveringen avbröts: %s' % str(e_)[:200])
            pagar = [r for r in post['steg'] if r['status'] == 'pagar']
            for r in pagar:
                r.update(status='osaker', fel='avbrutet under operationen')
            post['status'] = 'osaker' if pagar else 'fel'
        finally:
            for x in tmps:
                shutil.rmtree(x, ignore_errors=True)
        post['text'] = {'klar': 'aktiveringen klar: %s' % ', '.join(r['id'] for r in post['steg']),
                        'osaker': 'utfallet är okänt: stäm av med aktivera.py %s --stam-av före ett nytt försök' % slug}.get(
            post['status'], 'aktiveringen föll: ' + '; '.join([r['fel'] for r in post['steg'] if r.get('fel')] + post['hinder']))
        spara()
        return post


def _exportera(slug):
    import exportera
    return exportera.exportera(slug, git=True)


def stam_av(slug, wrangler=None):
    """Stämmer av ett okänt utfall mot Cloudflare med läsande anrop: finns kundens D1, R2 och nycklar? Ger kvittot."""
    import flodesstart
    import korregister
    with flodesstart.las(atelje.ROOT, slug, arv=True):
        fore = osaker(slug)
        if not fore:
            return {'status': 'inget_att_stamma_av', 'text': 'inget okänt utfall'}
        tid = kundrepo.nu()
        post = {'schema': 1, 'id': 'AKTIVERING-%s-%s' % (tid.replace(':', '').replace('-', ''), os.urandom(2).hex()), 'typ': 'avstämning',
                'slug': slug, 'tid': tid, 'avstammer': fore['id'], 'steg': [], 'status': 'fel', 'hinder': []}
        konto, hinder = kundrepo.cloudflare_konto()
        n = namn(slug)
        tmp = korregister.egen_tmp('nwp-aktivering-', 'aktiveringens avstämning')
        try:
            if hinder:
                raise RuntimeError(hinder)
            w = wrangler(slug, konto, tmp) if wrangler else standard_wrangler(slug, konto, tmp)
            for s in fore.get('steg') or []:
                if s.get('status') != 'osaker':
                    continue
                rad = {'id': s['id'], 'status': 'fel', 'klar_tid': kundrepo.nu(), 'detalj': None}
                if s['id'] == 'd1':
                    rc, ut = w(['d1', 'list', '--json'])
                    uuid = _d1_id(ut, n['d1']) if rc == 0 else None
                    rad.update(status='klar' if uuid else 'avstamd_ingen', detalj=uuid)
                elif s['id'] == 'r2':
                    rc, ut = w(['r2', 'bucket', 'list', '--jurisdiction', 'eu'])
                    finns = rc == 0 and re.search(r'(^|\s|")%s("|\s|$)' % re.escape(n['r2']), ut or '', re.M)
                    rad['status'] = 'klar' if finns else 'avstamd_ingen'
                elif s['id'].startswith('hemlighet:'):
                    rc, ut = w(['secret', 'list', '--name', n['worker']])
                    if rc:
                        raise RuntimeError('wrangler secret list föll')
                    finns = re.search(r'\b%s\b' % re.escape(s['id'].split(':', 1)[1]), ut or '') is not None
                    gjord = (not finns) if s.get('detalj') == 'borttagen' else finns  # borttagning är gjord när hemligheten saknas
                    rad.update(status='klar' if gjord else 'avstamd_ingen', detalj=s.get('detalj'))
                else:  # migreringar och lokala steg: ett nytt försök är säkert (migreringarna är idempotenta per fil)
                    rad['status'] = 'avstamd_ingen'
                post['steg'].append(rad)
            post['status'] = 'klar'
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as e_:
            post['hinder'].append('avstämningen kunde inte göras: %s' % str(e_)[:200])
            post['status'] = 'osaker'
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        post['text'] = 'avstämd: ' + ', '.join('%s %s' % (r['id'], r['status']) for r in post['steg']) if post['status'] == 'klar' else '; '.join(post['hinder'])
        atelje.skriv_json_atomiskt(kundrepo.leveransdir(slug) / (post['id'] + '.json'), post)
        return post


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    a.add_argument('slug')
    g = a.add_mutually_exclusive_group()
    g.add_argument('--kor', action='store_true', help='körningen, med ägarens mandat (klicket i Byggflöde)')
    g.add_argument('--stam-av', action='store_true', help='stäm av ett okänt utfall mot Cloudflare (läsande)')
    x = a.parse_args(argv)
    try:
        kundrepo.identitet(x.slug)
        ut = kor(x.slug) if x.kor else stam_av(x.slug) if x.stam_av else torr(x.slug)
    except ValueError as e:
        print(json.dumps({'ok': False, 'fel': str(e)}, ensure_ascii=False))
        return 2
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0 if (not (x.kor or x.stam_av) or ut.get('status') in ('klar', 'inget_att_gora', 'inget_att_stamma_av')) else 1


if __name__ == '__main__':
    sys.exit(main())
