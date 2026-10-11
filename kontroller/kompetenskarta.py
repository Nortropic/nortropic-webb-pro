#!/usr/bin/env python3
"""kompetenskarta.py — kompetenskartan (ägarens tillägg 2026-10-11 om specialkompetensen som AI:ns "steroider": var den
används och var luckorna finns, så att AI:ns förståelse kan förstärkas där det behövs). Kartan räknar inte fram något
nytt om kompetensen; den ställer samman det motorn redan har, med källan för varje del:

- tilldelningen: metodkartans kompetensblock (kompetens.tolka), stegen i flödets ordning, och varje roll med kärna,
  alternativ, verktyg, MCP:er och MCP-krav;
- skillsen: varje installerad skill med sin plats (kompetens.skillstatus: roll, process, skäl eller utan);
- tjänsterna: varje MCP-tjänst med rollerna som har den och besluten per verktyg (kompetens.tjanstverktyg);
- det observerade: kompetenskvittona som körningarna sparat (förberedelsens KOMPETENS.json, FORSKNING.json,
  PLANERING.json, KANDIDATPLAN.json:s komplettering, OMPLANERING-kompetens.json, PLANPROVNING.json, kandidaternas
  STATUS.json med fördjupningens uppdrag och förbättringsrundan, SKISSKRITIK.json, JAMFORELSE.json, KRITIK.json,
  FORE-EFTER.json och helbyggets slutpost SLUT.json), per roll med kvittots egna tillståndsord (kompetens.tillstand). Ett kvitto är belägg för läsning och
  anrop, aldrig för tillämpning eller kvalitet;
- agenterna utanför kartan: sessioner som motorn startar utan kompetensblock, med den kunskap de faktiskt får;
- luckorna: det som går att belägga ur delarna ovan, var och en med källa och förslag. Det som inte observerats står
  som inte observerat, aldrig som inte gjort.

    .venv/bin/python -B kontroller/kompetenskarta.py [--json]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kompetens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# flödets ordning (kunskap/skapandeflodet.md): underlaget, researchen, planen, skissen med kritiken, jämförelsen och
# granskningens två pass före ägarens val, sedan fördjupningen, passen efter den och helbygget
FLODE = ('forbered', 'forska', 'planera', 'planprovning', 'skapa', 'skisskritik', 'jamforelse', 'kritik_a', 'kritik_b', 'fordjupa',
         'rorelse', 'granskning', 'fore_efter', 'helbygge')
# kvittofilerna utanför kandidaternas STATUS.json: (mönster under underlag/<slug>/atelje, pass, vägen till kvittot), som
# kandidater.py och forberedelse.py skriver dem. Planeringens och omplaneringens kvitton läses ur PLANERING.json och
# OMPLANERING-kompetens.json, som skrivs också när planen stoppas; KANDIDATPLAN.json bär samma kvitton och läses bara för
# kompletteringen. Granskningens två pass står i samma KRITIK.json, under a och b; förberedelsens KOMPETENS.json är kvittot.
KVITTOFILER = (('forberedelse/*/KOMPETENS.json', 'forbered', ()), ('FORSKNING.json', 'forska', ('kompetens',)),
               ('PLANERING.json', 'planera', ('kompetens',)), ('KANDIDATPLAN.json', 'planera', ('komplettering', 'kompetens')),
               ('OMPLANERING-kompetens.json', 'planera', ('kompetens',)), ('PLANPROVNING.json', 'planprovning', ('kvitto',)),
               ('kandidater/*/SKISSKRITIK.json', 'skisskritik', ('kompetens',)), ('JAMFORELSE.json', 'jamforelse', ('kompetens',)),
               ('kandidater/*/KRITIK.json', 'kritik_a', ('kompetens', 'a')), ('kandidater/*/KRITIK.json', 'kritik_b', ('kompetens', 'b')),
               ('kandidater/*/fore-efter/*/FORE-EFTER.json', 'fore_efter', ('kompetens',)))
# sessioner som motorn startar utan kompetensblock, med den kunskap de får (ur koden; ändras koden ändras raden)
AGENTER = (
    {'id': 'andringar', 'namn': 'Ändringsagenten (fliken Ändringar)', 'kalla': 'kontroller/andringar.py',
     'kunskap': ['kunskap/andringsmetod.md (i startinstruktionen)', "kundrepots CLAUDE.md och DESIGN.md", 'webbplatsens privata KUNSKAP.md och ANDRINGAR.md',
                 'kopior av VERKSAMHET.json och DESIGNDOMAR.jsonl', 'motorns regler som versionerade kopior: copy-kontroll, redaktionellt pass och byggstandarden'],
     'verktyg': ['Bash i sandlådan, Read, Edit, Write, Glob, Grep', 'provvägen (bygge och foto)', 'commitvägen'], 'mcp': [], 'skills': [],
     'lucka': None, 'not': 'Restricted-läge: inga skills eller MCP:er laddas, och motorns kunskap/ går inte att läsa i sandlådan; reglerna '
                         'som gäller en ändring får agenten därför som kopior (andringar.MOTORNS_REGLER).'},
    {'id': 'partner', 'namn': 'Partnern i arbetsytan', 'kalla': 'dashboard/partner.py',
     'kunskap': ['README.md, CLAUDE.md, BESLUT.md', 'kunskap/, kritik/ och backlog/', 'kundens underlag i urvalet'],
     'verktyg': ['Read'], 'mcp': [], 'skills': [], 'lucka': None},
    {'id': 'granskare', 'namn': 'Helbyggets två granskare', 'kalla': 'kontroller/granska.py',
     'kunskap': ['kritik/GRANSKARE.md och de frysta kriteriefilerna (metod_sha)', 'designreglerna och kundens domlogg'],
     'verktyg': ['förhandsvisningen'], 'mcp': [], 'skills': [], 'lucka': None},
    {'id': 'intervju', 'namn': 'Kundstartens intervju', 'kalla': 'kontroller/kundstart_modell.py',
     'kunskap': ['kunskap/kundintervju.md', 'ärendet (data, inte instruktioner)'], 'verktyg': [], 'mcp': [], 'skills': [], 'lucka': None},
)


def _las(p):
    try:
        if p.is_symlink() or not p.is_file():
            return None
        d = json.loads(p.read_text(encoding='utf-8'))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _fordjupningar(d):
    """Fördjupningens kvitton ur en STATUS.json: varje uppdrag i uppdragen, och forfining bara när den inte redan är ett
    av dem (forfining är det senaste uppdraget; äldre status saknar uppdragen). Förbättringsrundans kvitto efter
    kritiken (forbattrad, skaparens pass) läses i kvitton."""
    uppdragen = [u for u in d.get('uppdragen') or [] if isinstance(u, dict)] if isinstance(d.get('uppdragen'), list) else []
    f = d.get('forfining')
    if isinstance(f, dict) and not any(u.get('klar') == f.get('klar') and u.get('dom') == f.get('dom') for u in uppdragen):
        uppdragen.append(f)
    return [u['kompetens'] for u in uppdragen if isinstance(u.get('kompetens'), dict) and u['kompetens']]


def kvitton(underlag, kunder=None):
    """Alla sparade kompetenskvitton under underlag/ och, med kunder, helbyggenas i slutposterna
    (kunder/<slug>/korningar/<körning>/SLUT.json): [{pass, slug, kalla, tid, kvitto}], äldst först."""
    underlag = Path(underlag)
    ut = []
    for u in sorted(underlag.iterdir()) if underlag.is_dir() else []:
        a = u / 'atelje'
        if u.is_symlink() or not a.is_dir() or a.is_symlink():
            continue
        for st in sorted(a.glob('kandidater/*/STATUS.json')):
            d = _las(st) or {}
            for rec in (d.get('kompetens') or {}).values() if isinstance(d.get('kompetens'), dict) else []:
                if isinstance(rec, dict) and rec.get('pass') in kompetens.PASS and isinstance(rec.get('kvitto'), dict):
                    ut.append({'pass': rec['pass'], 'slug': u.name, 'kalla': str(st.relative_to(underlag)), 'tid': st.stat().st_mtime, 'kvitto': rec['kvitto']})
            for kv in _fordjupningar(d):
                ut.append({'pass': 'fordjupa', 'slug': u.name, 'kalla': str(st.relative_to(underlag)), 'tid': st.stat().st_mtime, 'kvitto': kv})
            kv = (d.get('forbattrad') or {}).get('kompetens') if isinstance(d.get('forbattrad'), dict) else None
            if isinstance(kv, dict) and kv:
                ut.append({'pass': 'skapa', 'slug': u.name, 'kalla': str(st.relative_to(underlag)), 'tid': st.stat().st_mtime, 'kvitto': kv})
        for monster, pass_, vag in KVITTOFILER:
            for f in sorted(a.glob(monster)):
                kv = _las(f) or {}
                for nyckel in vag:
                    kv = kv.get(nyckel) if isinstance(kv, dict) else None
                if isinstance(kv, dict) and kv:
                    ut.append({'pass': pass_, 'slug': u.name, 'kalla': str(f.relative_to(underlag)), 'tid': f.stat().st_mtime, 'kvitto': kv})
    kunder = Path(kunder) if kunder else None
    for k in sorted(kunder.iterdir()) if kunder and kunder.is_dir() else []:
        if k.is_symlink() or not (k / 'korningar').is_dir() or (k / 'korningar').is_symlink():
            continue
        for f in sorted((k / 'korningar').glob('*/SLUT.json')):
            if f.parent.is_symlink():
                continue
            kv = (((_las(f) or {}).get('kontroller') or {}).get('kompetens') or {})
            kv = kv.get('kvitto') if isinstance(kv, dict) else None
            if isinstance(kv, dict) and kv:
                ut.append({'pass': 'helbygge', 'slug': k.name, 'kalla': str(f.relative_to(kunder.parent)), 'tid': f.stat().st_mtime, 'kvitto': kv})
    return sorted(ut, key=lambda x: x['tid'])


def observerat(underlag, k, kunder=None):
    """Per roll ur kvittona: antal kvitton, kärnan läst hel (av sedda), skillverktygets aktiveringar, och tillståndet per
    MCP-tjänst och verktyg som räkneverk över kvittona, med kvittots egna ord. Senaste tid och kunderna (bara slug)."""
    T = kompetens.TILLSTAND
    roller = {}
    for kv_ in kvitton(underlag, kunder):
        try:
            rader = kv_['kvitto'].get('tillstand') if isinstance(kv_['kvitto'].get('tillstand'), list) else kompetens.tillstand(kv_['kvitto'], kv_['pass'], k)
        except (KeyError, TypeError, ValueError):
            continue
        for r in rader:
            if not isinstance(r, dict) or r.get('roll') not in k:
                continue
            o = roller.setdefault(r['roll'], {'kvitton': 0, 'karna_hel': 0, 'karna_sedd': 0, 'aktiverade': {}, 'mcp': {}, 'verktyg': {}, 'senast': 0, 'kunder': set()})
            o['kvitton'] += 1
            o['senast'] = max(o['senast'], kv_['tid'])
            o['kunder'].add(kv_['slug'])
            karna = r.get('karna') or {}
            if karna.get('tillstand') not in (T['ej_observerat'], None):
                o['karna_sedd'] += 1
                o['karna_hel'] += int(bool(karna.get('filer')) and karna.get('lasta') == karna.get('filer'))
            for s in ((r.get('skillverktyget') or {}).get('anrop') or []):
                o['aktiverade'][s] = o['aktiverade'].get(s, 0) + 1
            for m, x in (r.get('mcp') or {}).items():
                t = (x or {}).get('tillstand') if isinstance(x, dict) else x
                o['mcp'].setdefault(m, {})[str(t)] = o['mcp'].setdefault(m, {}).get(str(t), 0) + 1
            for v, t in (r.get('verktyg') or {}).items():
                o['verktyg'].setdefault(v, {})[str(t)] = o['verktyg'].setdefault(v, {}).get(str(t), 0) + 1
    for o in roller.values():
        o['kunder'] = len(o['kunder'])
        o['senast'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(o['senast'])) if o['senast'] else None
    return roller


def _typ(f):
    if f.startswith('kunskap/'):
        return 'kunskap'
    if f.startswith('kritik/'):
        return 'kritik'
    return 'skill' if f.endswith('/SKILL.md') and f.count('/') == 1 else 'skillreferens'


def karta(root=None, underlag=None, kunder=None):
    """Kartan som data: steg, roller, kompetenser (fil → roller), skills, tjänster, agenter utanför kartan, det
    observerade och luckorna."""
    root = Path(root or ROOT)
    underlag = Path(underlag) if underlag else root / 'underlag'
    kunder = Path(kunder) if kunder else root / 'kunder'
    k = kompetens.tolka()
    T = kompetens.TILLSTAND
    steg = [{'pass': p, 'namn': kompetens.PASSNAMN.get(p, p), 'roller': [x['id'] for x in kompetens.for_pass(p, k)]} for p in FLODE]
    roller = {kid: {'id': kid, 'namn': x['namn'], 'uppgift': x['uppgift'], 'pass': x['pass'], 'karna': x['karna'], 'valj': x['valj'],
                    'verktyg': x['verktyg'], 'mcp': x['mcp'], 'mcp_krav': x['mcp_krav']} for kid, x in k.items()}
    filer = {}
    for kid, x in k.items():
        for f in x['karna'] + x['valj']:
            e = filer.setdefault(f, {'fil': f, 'typ': _typ(f), 'skill': None if f.startswith(('kunskap/', 'kritik/')) else f.split('/')[0], 'roller': {}})
            e['roller'][kid] = 'karna' if f in x['karna'] else 'valj'
    skills = kompetens.skillstatus(root / '.claude' / 'skills', k)
    beslut = kompetens.tjanstverktyg()
    tjanster = []
    for m in sorted(set(kompetens.MCP) | set(beslut)):
        b = beslut.get(m) or {}
        tjanster.append({'id': m, 'namn': kompetens.MCPNAMN.get(m, m), 'roller': sorted(kid for kid, x in k.items() if m in x['mcp']),
                         'krav': sorted(kid for kid, x in k.items() if m in x['mcp_krav']),
                         'verktyg_med_uppgift': sorted(v for v, x in b.items() if x.get('beslut') == 'uppgift'),
                         'verktyg_utan_uppgift': sorted(v for v, x in b.items() if x.get('beslut') == 'ingen uppgift')})
    verktyg = [{'id': v, 'roller': sorted(kid for kid, x in k.items() if v in x['verktyg']), 'beskrivning': kompetens.VERKTYG[v][1]} for v in kompetens.VERKTYG]
    obs = observerat(underlag, k, kunder)
    return {'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'steg': steg, 'roller': roller, 'filer': sorted(filer.values(), key=lambda e: (e['typ'], e['fil'])),
            'skills': skills, 'tjanster': tjanster, 'verktyg': verktyg, 'agenter': list(AGENTER), 'observerat': obs,
            'luckor': luckor(k, skills, tjanster, verktyg, obs, steg, T),
            'kallor': {'tilldelning': 'kunskap/metodkarta.md (kompetensblocken)', 'skills': '.claude/skills och metodkartan, Ingen uppgift i flödet',
                       'tjanster': 'metodkartan, Tjänsternas verktyg', 'observerat': 'kompetenskvittona under underlag/ (läsning och anrop, inte kvalitet)'}}


def luckor(k, skills, tjanster, verktyg, obs, steg, T):
    """Det som går att belägga: [{slag, rubrik, detalj, kalla, forslag}] med det tyngsta först."""
    ut = []
    for n, x in sorted(skills.items()):
        if x['plats'] == 'utan':
            ut.append({'slag': 'skill_utan_plats', 'rubrik': '%s har varken roll eller skäl' % n,
                       'detalj': 'Skillen är installerad men står inte i något kompetensblock och inte under "Ingen uppgift i flödet".',
                       'kalla': '.claude/skills/%s' % n, 'forslag': 'Ge den en roll i ett kompetensblock, eller skriv skälet i metodkartan.'})
    for kid, x in k.items():
        o = obs.get(kid)
        if not o:
            continue
        if o['karna_sedd'] and o['karna_hel'] < o['karna_sedd']:
            ut.append({'slag': 'karna', 'rubrik': '%s: kärnan lästes inte hel i %d av %d observerade kvitton' % (x['namn'], o['karna_sedd'] - o['karna_hel'], o['karna_sedd']),
                       'detalj': 'Rollens metod lästes bara delvis; det som inte lästs kan inte ha styrt arbetet.', 'kalla': 'kompetenskvittona (kärnan)',
                       'forslag': 'Se kvittona per kund i kandidatens redovisning; minska kärnan eller dela den om den inte ryms.'})
        for m in x['mcp_krav']:
            s = o['mcp'].get(m) or {}
            if not s.get(T['anvant']):
                ut.append({'slag': 'mcp_krav', 'rubrik': '%s: MCP-kravet %s har inget observerat anrop med resultat' % (x['namn'], m),
                           'detalj': 'Tillstånd i kvittona: %s.' % (', '.join('%s ×%d' % i for i in sorted(s.items())) or 'inget'),
                           'kalla': 'kompetenskvittona (mcp)', 'forslag': 'Kontrollera tjänstens anslutning och nyckel i startkvittot.'})
        for m, s in sorted(o['mcp'].items()):
            if s.get(T['blockerat']):
                ut.append({'slag': 'mcp_blockerat', 'rubrik': '%s: %s blockerades eller misslyckades %d gånger' % (x['namn'], m, s[T['blockerat']]),
                           'detalj': 'Ett misslyckat anrop är en faktisk begränsning, inte ett oanvänt verktyg.', 'kalla': 'kompetenskvittona (mcp)',
                           'forslag': 'Se tjänstens rad i startkvittot och kundvaktens beslut.'})
        for m in x['mcp']:
            s = o['mcp'].get(m) or {}
            if m not in x['mcp_krav'] and s and not s.get(T['anvant']) and not s.get(T['blockerat']) and s.get(T['ej_gjort']):
                ut.append({'slag': 'mcp_oanvant', 'rubrik': '%s: %s tilldelad men inte anropad i någon observerad session' % (x['namn'], m),
                           'detalj': 'Inte gjort (observerat) i %d kvitton.' % s[T['ej_gjort']], 'kalla': 'kompetenskvittona (mcp)',
                           'forslag': 'Pröva om rollen behöver tjänsten här, eller skriv i metodkartan när den inte ska användas.'})
        for v in x['verktyg']:
            s = o['verktyg'].get(v) or {}
            if s and not s.get(T['anvant']) and s.get(T['ej_gjort']):
                ut.append({'slag': 'verktyg_oanvant', 'rubrik': '%s: verktyget %s användes inte i någon observerad session' % (x['namn'], v),
                           'detalj': 'Tilldelat men inte gjort (observerat) i %d kvitton.' % s[T['ej_gjort']], 'kalla': 'kompetenskvittona (verktyg)',
                           'forslag': 'Pröva om uppgiften behöver verktyget, eller ta bort tilldelningen med skäl.'})
    sedda = {kid for kid in obs}
    tomma = [s['namn'] for s in steg if s['roller'] and not any(r in sedda for r in s['roller'])]
    if tomma:
        ut.append({'slag': 'ej_observerat', 'rubrik': 'Inga sparade kvitton för %d steg' % len(tomma),
                   'detalj': 'Steg utan observerade kvitton: %s. Inte observerat, inte inte gjort: flödet har inte körts där sedan kvittona infördes '
                             'eller sedan den rena designstarten.' % ', '.join(tomma),
                   'kalla': 'underlag/*/atelje', 'forslag': 'Nästa körning av skapandeflödet ger kvittona.'})
    for a in AGENTER:
        if a['lucka']:
            ut.append({'slag': 'agent', 'rubrik': '%s har ingen kompetensroll' % a['namn'], 'detalj': a['lucka'], 'kalla': a['kalla'],
                       'forslag': 'Ge agenten verifierade kopior av de texter den behöver i sin privata kunskap (versionerade, som underlaget), eller en roll i metodkartan.'})
    ordning = {'skill_utan_plats': 0, 'mcp_krav': 1, 'mcp_blockerat': 2, 'karna': 3, 'agent': 4, 'mcp_oanvant': 5, 'verktyg_oanvant': 6, 'ej_observerat': 7}
    return sorted(ut, key=lambda x: ordning.get(x['slag'], 9))


def main(argv=None):
    a = argparse.ArgumentParser(prog='kompetenskarta', description=__doc__.split('\n\n')[0])
    a.add_argument('--json', action='store_true')
    x = a.parse_args(argv)
    d = karta()
    if x.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    print('%d steg, %d roller, %d filer, %d skills, %d tjänster; %d roller observerade; %d luckor' % (
        len(d['steg']), len(d['roller']), len(d['filer']), len(d['skills']), len(d['tjanster']), len(d['observerat']), len(d['luckor'])))
    for l in d['luckor']:
        print('- %s: %s' % (l['slag'], l['rubrik']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
