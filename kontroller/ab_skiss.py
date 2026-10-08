"""Ett avgränsat försök i befintliga A/B-poster och kandidatflödet.

Två ännu inte arbetade kandidater får samma uppdrag. Bara skisskaparens effort
lottas. Förberedelsen startar inga sessioner och ger inget körmandat. Gemensamma
källor versionsbinds före start och kontrolleras också när resultatet tas fram.
Det är ett identitetslås, inte en oföränderlig filsystemkopia eller bevis för att
externa tjänster kommer att svara lika. Ingen kvalitetsvinst antas.
"""
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from pathlib import Path

import atelje
import kandidater as kd
import skapande
import autonomi

PLANFILER = ('KANDIDATPLAN.json', 'KANDIDATPLAN.md', 'FORSKNING.json', 'FORSKNING.md',
             'PLANPROVNING.json', 'PLANPROVNING.md', 'UPPDRAGSMATERIAL.json')
METODROTTER = ('kontroller', 'kunskap', 'kritik', 'mall', '.claude/skills')
IGNORERA = {'node_modules', '__pycache__', '.DS_Store'}
ID = re.compile(r'skiss-[a-z0-9-]{2,60}-[a-f0-9]{12}')


def vanlig(p, root, saknas=False):
    p, root = Path(p), Path(root)
    try:
        delar = p.relative_to(root).parts
    except ValueError as e:
        raise ValueError('försökets sökväg är utanför roten') from e
    q = root
    for n in ('', *delar):
        q = q / n if n else q
        if q.is_symlink():
            raise ValueError('försökets källa eller mål är en länk')
    if not p.exists() and saknas:
        return None
    if not stat.S_ISREG(p.stat().st_mode):
        raise ValueError('försökets källa är inte en vanlig fil')
    return p.read_bytes()


def las(p, root):
    try:
        v = json.loads(vanlig(p, root))
        if not isinstance(v, dict):
            raise ValueError('objekt krävs')
        return v
    except (OSError, ValueError, UnicodeError) as e:
        raise ValueError('metodförsökets underlag kunde inte läsas eller valideras') from e


def sha(b):
    return hashlib.sha256(b).hexdigest() if b is not None else None


def trad(p, root):
    ut = {}
    if p.is_symlink():
        raise ValueError('länk i försökets metod')
    if not p.exists():
        return {p.relative_to(root).as_posix(): None}
    def fel(e):
        raise e
    for d, kataloger, filer in os.walk(p, onerror=fel):
        kataloger[:] = [n for n in kataloger if n not in IGNORERA]
        if any((Path(d) / n).is_symlink() for n in kataloger):
            raise ValueError('kataloglänk i försökets metod')
        for n in sorted(set(filer) - IGNORERA):
            f = Path(d) / n
            ut[f.relative_to(root).as_posix()] = sha(vanlig(f, root))
    return ut


def gemensamt(slug, ids):
    """Källor och effektiv budget; aldrig hemligheter eller användarens MCP-inställningar."""
    root, u, r = atelje.ROOT, atelje.UNDERLAG / slug, kd.rot(slug)
    metod = {}
    for n in METODROTTER:
        metod.update(trad(root / n, root))
    for n in ('CLAUDE.md', 'README.md', 'BESLUT.md', 'kor.sh'):
        metod[n] = sha(vanlig(root / n, root, saknas=True))
    plan = {n: sha(vanlig(r / n, root, saknas=True)) for n in PLANFILER}
    plan.update({k + '/UPPDRAG.md': sha(vanlig(kd.kdir(slug, k) / 'UPPDRAG.md', root)) for k in ids})
    deklarerat = {}
    def material(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ('fil', 'original') and isinstance(x, str) and x:
                    f = Path(x) if Path(x).is_absolute() else root / x
                    if '..' in f.parts or not f.is_relative_to(u):
                        raise ValueError('deklarerat försöksmaterial ligger utanför kundens underlag')
                    if f.is_dir():
                        deklarerat.update(trad(f, root))
                    else:
                        deklarerat[f.relative_to(root).as_posix()] = sha(vanlig(f, root))
                else:
                    material(x)
        elif isinstance(v, list):
            for x in v:
                material(x)
    material(las(r / 'UPPDRAGSMATERIAL.json', root))
    agarkriterier = {n: sha(vanlig(u / n, root, saknas=True)) for n in
                    (skapande.DOMLOGG, skapande.BELAGGFIL, skapande.HISTORIK)}
    levererat = trad(kd.metodkatalog(slug), root)
    mf = kd.metodkatalog(slug) / 'METOD.json'
    if mf.exists():
        # Leveransens tidsstämpel är inte en metodändring; filval, innehåll och källa är det.
        m = las(mf, root); m.pop('tid', None)
        levererat[mf.relative_to(root).as_posix()] = sha(json.dumps(m, sort_keys=True).encode())
    return {'underlag': skapande.underlagsmanifest(slug, atelje.UNDERLAG), 'plan': plan,
            'levererad_metod': levererat,
            'deklarerat_material': deklarerat, 'agarkriterier': agarkriterier,
            'sajt': skapande.kallmanifest(atelje.KUNDER / slug / 'sajt'), 'metod': metod,
            'installningar': {'skapare': kd.skaparval(), 'granskare': kd.GRANSKARE_MODELL,
                             'atelje_modell': atelje.MODELL, 'atelje_effort': atelje.EFFORT,
                             'lage': kd.LAGE, 'effort_ovriga': kd.EFFORT_SKISS,
                             'kritik': os.environ.get('NWP_SKISSKRITIK'),
                             **{n: getattr(kd, n) for n in ('FRIST_SKISS', 'FRIST_SKISS_OMFORSOK',
                                'FRIST_SKISSKRITIK', 'SKISSKRITIK_RESERV', 'MAX_FORSOK_SKISS', 'PARALLELLT',
                                'MAX_PARALLELLT_SKISS', 'FOTO_RESERV', 'SVAR_MIN', 'FORTSATT_MIN')},
                             'miljo': {k: v for k, v in os.environ.items() if k.startswith(('NWP_KANDIDAT',
                                        'NWP_ATELJE_', 'NWP_SKISS', 'NWP_OBSERVATION', 'NWP_SANDLADA'))}}}


def forbered(ab, slug, kid):
    if not re.fullmatch(r'[a-z0-9-]{2,60}', slug) or not kd.ID.fullmatch(kid):
        raise ValueError('ogiltigt bygge eller kandidat')
    if os.environ.get('CLAUDE_CODE_EFFORT_LEVEL'):
        raise ValueError('metodförsöket kräver en miljö utan CLAUDE_CODE_EFFORT_LEVEL; ändra inte användarinställningarna')
    r, root = kd.rot(slug), atelje.ROOT
    # Pröva alla rötter före låset och första skrivningen.
    vanlig(kd.kdir(slug, kid) / 'UPPDRAG.md', root)
    vanlig(ab.AB / 'kontroll', root, saknas=True)
    with atelje.processlas(r):
        plan = las(r / 'KANDIDATPLAN.json', root)
        st = las(kd.kdir(slug, kid) / 'STATUS.json', root)
        if (plan.get('metodforsok') or kd.lista(slug) != [kid] or set(plan.get('kandidater', {})) != {kid}
                or plan.get('lage') != 'skiss' or kd.LAGE != 'skiss'
                or st.get('status') != 'planerad' or st.get('forsok', 0) != 0 or kd.domd(slug)):
            raise ValueError('kräver en ensam, planerad och ännu inte arbetad skiss utan ägarval')
        if any(p.name not in ('UPPDRAG.md', 'STATUS.json') for p in kd.kdir(slug, kid).iterdir()):
            raise ValueError('kandidaten har redan arbetsmaterial; ett nytt försök behöver en ny plan')
        status = las(r / 'STATUS.json', root) if (r / 'STATUS.json').exists() else {}
        if status.get('steg') in ('startar', 'forska', 'planera', 'material', 'planprovning', 'skapa', 'forfina'):
            raise ValueError('vänta tills den pågående körningen är avslutad')
        for n in ('FORSKNING.json', 'PLANPROVNING.json', 'UPPDRAGSMATERIAL.json'):
            las(r / n, root)
        ids = [kid, next('k%02d' % n for n in range(1, 13) if 'k%02d' % n != kid)]
        if (kd.kdir(slug, ids[1]).exists() or kd.kdir(slug, ids[1]).is_symlink()
                or any(kd.ksajt(slug, k).parent.exists() for k in ids)):
            raise ValueError('kandidatens projekt finns redan')
        gammal_plan = vanlig(r / 'KANDIDATPLAN.json', root)
        material = las(r / 'UPPDRAGSMATERIAL.json', root)
        if not isinstance(material.get('kandidater'), dict) or kid not in material['kandidater']:
            raise ValueError('uppdragsmaterial för kandidaten saknas')
        ursprung = vanlig(kd.kdir(slug, kid) / 'UPPDRAG.md', root).decode('utf-8')
        kd.metodinfo(slug, 'skiss')  # förbered leveransen innan dess identitet låses
        gemensamt(slug, [kid])  # läsfel eller otillåtet material före första ändringen
        # Kandidatnummer är arbetsadresser, inte behandling. Samma designbrief i båda kontexterna.
        uppdrag = re.sub(r'^# Uppdrag k\d{2}.*$', '# Gemensamt designuppdrag', ursprung, count=1, flags=re.M)
        uppdrag = re.sub(r'^Kandidat \d+ av \d+[^\n]*\n?', '', uppdrag, flags=re.M)
        varden = ['medium', 'high']; ab.random.shuffle(varden)
        ident = 'skiss-%s-%s' % (slug, uuid.uuid4().hex[:12])
        post = {'schema': 1, 'id': ident, 'slug': slug, 'pass': 'skisskapare', 'variabel': 'effort',
                'status': 'forbereder', 'tid': ab.nu(), 'kandidater': ids, 'varden': dict(zip(ids, varden)),
                'ursprung': {'plan': json.loads(gammal_plan), 'uppdrag': ursprung, 'material': copy.deepcopy(material)},
                'domlogg_prefix': {'bytes': len(vanlig(atelje.UNDERLAG / slug / skapande.DOMLOGG, root, saknas=True) or b''),
                                  'sha': sha(vanlig(atelje.UNDERLAG / slug / skapande.DOMLOGG, root, saknas=True) or b'')},
                'begransning': 'Identitetslås före och efter. Externa svar och modellutfall varierar. Ingen kvalitetsdom ännu.'}
        # Ingen modell kan starta med halva förberedelsen: markören skrivs före klonen,
        # och tillståndet blir forberedd först efter att alla gemensamma källor hashats.
        ab.AB.mkdir(parents=True, exist_ok=True)
        fil = ab.AB / (ident + '.json')
        atelje.skriv_json_atomiskt(fil, post)
        plan.update(metodforsok=ident, metodforsok_varden_sha=sha(json.dumps(post['varden'], sort_keys=True).encode()), antal=2)
        plan['kandidater'][ids[1]] = copy.deepcopy(plan['kandidater'][kid])
        d, skapad = kd.kdir(slug, ids[1]), False
        try:
            atelje.skriv_json_atomiskt(r / 'KANDIDATPLAN.json', plan)
            d.mkdir(); skapad = True
            for k in ids:
                (kd.kdir(slug, k) / 'UPPDRAG.md').write_text(uppdrag, encoding='utf-8')
            kd.satt_status(slug, ids[1], 'planerad', forsok=0, **{
                k: st.get(k) for k in ('titel', 'hypotes', 'huvudreferens')})
            material['kandidater'][ids[1]] = copy.deepcopy(material['kandidater'][kid])
            atelje.skriv_json_atomiskt(r / 'UPPDRAGSMATERIAL.json', material)
            post.update(status='forberedd', gemensamt=gemensamt(slug, ids))
            atelje.skriv_json_atomiskt(fil, post)
        except Exception:
            # Eget nytt material bevaras åt sidan. Originaluppdraget kan förberedas igen.
            # Vid en oberoende ändring lämnas alla filer orörda med markören forbereder.
            # Det kräver avstämning mot ursprung, aldrig automatisk överskrivning.
            if (vanlig(kd.kdir(slug, kid) / 'UPPDRAG.md', root) not in (ursprung.encode(), uppdrag.encode())
                    or las(r / 'KANDIDATPLAN.json', root) not in (post['ursprung']['plan'], plan)
                    or las(r / 'UPPDRAGSMATERIAL.json', root) not in (post['ursprung']['material'], material)):
                raise ValueError('förberedelsen föll och en fil ändrades oberoende; inget återställs, jämför med försökets ursprung')
            if skapad:
                shutil.move(str(d), str(ab.AB / (ident + '-avbrutet')))
            (kd.kdir(slug, kid) / 'UPPDRAG.md').write_text(ursprung, encoding='utf-8')
            if las(r / 'UPPDRAGSMATERIAL.json', root) != post['ursprung']['material']:
                atelje.skriv_json_atomiskt(r / 'UPPDRAGSMATERIAL.json', post['ursprung']['material'])
            atelje.skriv_json_atomiskt(r / 'KANDIDATPLAN.json', post['ursprung']['plan'])
            post.update(status='forberedelsefel', gemensamt=None)
            atelje.skriv_json_atomiskt(fil, post)
            raise
        return post


def las_post(ab, slug):
    f = kd.rot(slug) / 'KANDIDATPLAN.json'
    if not f.exists() and not f.is_symlink():
        return None
    plan = las(f, atelje.ROOT)
    ident = plan.get('metodforsok')
    if ident is None:
        return None
    if not isinstance(ident, str) or not ID.fullmatch(ident):
        raise ValueError('ogiltig metodförsöksidentitet')
    p = las(ab.AB / (ident + '.json'), atelje.ROOT)
    ids = p.get('kandidater')
    if (p.get('schema') != 1 or p.get('pass') != 'skisskapare' or p.get('variabel') != 'effort'
            or p.get('id') != ident or p.get('slug') != slug or p.get('status') != 'forberedd'
            or not isinstance(ids, list) or len(ids) != 2
            or any(not isinstance(k, str) or not kd.ID.fullmatch(k) for k in ids) or len(set(ids)) != 2
            or set(ids) != set(plan.get('kandidater', {})) or not isinstance(p.get('varden'), dict)
            or set(p['varden']) != set(ids) or sorted(str(v) for v in p['varden'].values()) != ['high', 'medium']
            or not isinstance(p.get('gemensamt'), dict)):
        raise ValueError('metodförsöket är ofullständigt eller ändrat')
    if plan.get('metodforsok_varden_sha') != sha(json.dumps(p['varden'], sort_keys=True).encode()):
        raise ValueError('metodförsökets tilldelning har ändrats')
    for k in ids:
        st = kd.las_status(slug, k)
        begarda = [x.get('begard_installning') for x in st.get('forsok_tider') or [] if isinstance(x, dict)]
        begarda.append((st.get('skaparinstallningar') or {}).get('begart'))
        vantat = dict(p['gemensamt'].get('installningar', {}).get('skapare') or {}, effort=p['varden'][k])
        if any(b is not None and b != vantat for b in begarda):
            raise ValueError('försökets tilldelning motsäger skaparens bokförda inställning')
    return p


def krav(ab, slug):
    p = las_post(ab, slug)
    if p and os.environ.get('CLAUDE_CODE_EFFORT_LEVEL'):
        raise ValueError('CLAUDE_CODE_EFFORT_LEVEL gör försöksinställningen tvetydig')
    if p and p.get('gemensamt') != gemensamt(slug, p['kandidater']):
        raise ValueError('metodförsökets underlag, uppdrag, metod eller budget har ändrats')
    return p


def val(ab, slug, kid, standard):
    p = krav(ab, slug)
    if not p:
        return standard
    if kid not in p['kandidater']:
        raise ValueError('kandidaten ingår inte i metodförsöket')
    return dict(standard, effort=p['varden'][kid])


def avslutad(ab, slug, kid):
    p = krav(ab, slug)
    st = kd.las_status(slug, kid)
    if p:
        kd.satt_status(slug, kid, st.get('status'), st.get('skal', ''), metodforsok={
            'id': p['id'], 'kallor_sha': sha(json.dumps(p['gemensamt'], sort_keys=True).encode()),
            'version': st.get('version')})
    return kd.las_status(slug, kid)


def resultat(ab, slug):
    """Läsande sammanställning, även av avbrutna försök; inga antagna kostnader eller konfigurationer."""
    p = las_post(ab, slug)
    if not p:
        return None
    fel = None
    try:
        aktuell = gemensamt(slug, p['kandidater'])
        # Själva blinda valet får lägga till en dom efter avslutade, kontrollerade armar.
        # Före valet kontrollerar prova_beslut hela källidentiteten, inklusive domloggen.
        if kd.domd(slug) and all(kd.las_status(slug, k).get('metodforsok') == {
                'id': p['id'], 'kallor_sha': sha(json.dumps(p['gemensamt'], sort_keys=True).encode()),
                'version': kd.las_status(slug, k).get('version')} for k in p['kandidater']):
            prefix = p.get('domlogg_prefix') or {}
            b = vanlig(atelje.UNDERLAG / slug / skapande.DOMLOGG, atelje.ROOT, saknas=True) or b''
            n = prefix.get('bytes')
            if isinstance(n, int) and n >= 0 and sha(b[:n]) == prefix.get('sha'):
                nya = [json.loads(x) for x in b[n:].splitlines() if x.strip()]
                if nya and all(isinstance(x, dict) and skapande.ar_agarens(x)
                               and x.get('plan') == kd.plan_tid(slug) and x.get('tid', '') > kd.plan_tid(slug) for x in nya):
                    aktuell['agarkriterier'][skapande.DOMLOGG] = p['gemensamt']['agarkriterier'][skapande.DOMLOGG]
        if os.environ.get('CLAUDE_CODE_EFFORT_LEVEL'):
            raise ValueError('CLAUDE_CODE_EFFORT_LEVEL gör försöksinställningen tvetydig')
        if aktuell != p['gemensamt']:
            raise ValueError('metodförsökets gemensamma förutsättningar har ändrats')
    except (ValueError, OSError) as e:
        fel = str(e)
    armar = {}
    for k in p['kandidater']:
        st = kd.las_status(slug, k)
        if st.get('version') and kd.version(slug, k) != st['version']:
            fel = 'en kandidats artefakt har ändrats efter den bokförda versionen'
        filer = sorted(kd.kdir(slug, k).rglob('svar-*.json'))
        svar = [autonomi.las_json(f) for f in filer]
        saknade = set()
        poster = sorted(kd.kdir(slug, k).rglob('STATUS.json')) + sorted(kd.kdir(slug, k).rglob('SKISSKRITIK.json'))
        for sf in poster:
            s = autonomi.las_json(sf)
            if s is None:
                saknade.add(sf.relative_to(kd.kdir(slug, k)).as_posix())
                continue
            anropen = list(s.get('sessioner') or [])
            krit = s if sf.name == 'SKISSKRITIK.json' else s.get('skisskritik') or {}
            if krit.get('session'):
                anropen.append({'svar': krit.get('svar'), 'session_id': (krit.get('session') or {}).get('session_id')})
            for anrop in anropen:
                if not isinstance(anrop, dict):
                    saknade.add('oläsbar sessionsreferens'); continue
                namn, sid = anrop.get('svar'), anrop.get('session_id')
                namn = namn if isinstance(namn, str) and namn.strip() else None
                sid = sid if isinstance(sid, str) and sid.strip() else None
                if namn is None and sid is None:
                    saknade.add('sessionsreferens utan fil eller identitet')
                    continue
                if not any((not namn or f.name == namn) and (not sid or isinstance(x, dict) and x.get('session_id') == sid)
                           for f, x in zip(filer, svar)):
                    saknade.add(str(namn or ('session:' + str(sid))))
        svar += [None] * len(saknade)
        armar[k] = {'status': st.get('status'), 'version': st.get('version'), 'forsok': st.get('forsok_tider') or [],
                    'fel': st.get('skal'), 'anvandning': autonomi.summa(svar), 'saknade_svar': sorted(saknade),
                    'begard': {'modell': p['gemensamt']['installningar']['skapare']['modell'], 'effort': p['varden'][k]},
                    'observerad_effort': None, 'observerad_modell': None,
                    'observationsskal': 'Ingen oberoende observation av effektiv effort/modell i denna sammanställning.'}
    return {'id': p['id'], 'jamforbara_kallor': not fel, 'fel': fel, 'armar': armar,
            'bedomning': 'ännu inte bedömt' if not kd.domd(slug) else 'se ägarens versionsbundna dom i kandidatflödet',
            'begransning': p['begransning']}
