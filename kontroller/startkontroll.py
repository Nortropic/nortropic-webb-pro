#!/usr/bin/env python3
"""startkontroll.py — den sammanhållna startkontrollen före varje ny byggstart (ägarens uppdrag 2026-10-05 19:13Z, 20:27Z
och ~20:50Z, ordagrant i minnet). Alla startvägar går genom den: ateljéns arbetare (kontroller/atelje.py, som
prototyp.py och atelje.py startar) före skisser, prototyper och förfiningar, och helbygget (kor.sh) före modellen.

    .venv/bin/python kontroller/startkontroll.py [--slug S] [--start ny|fortsatt|valda|putsa|bygge|prov] [--utan-prov]
        [--json]

Starten ska gå snabbt: uppdateringarna prövas och tas in av det dagliga underhållet (kontroller/underhall.py, som
dashboarden startar), så här bekräftas bara läget. Kontrollen
1. inventerar verktygslådan (kontroller/verktygslada.py): installerad version ur maskinen och senaste version ur
   underhållets uppslag med tiden de gjordes (inga nya uppslag här); en nyare version som underhållet inte hunnit pröva
   står som behållen med skäl, en avvisad med felet;
2. prövar förmågan med små prov som återanvänds medan förutsättningarna är oförändrade (fingeravtryck av version,
   nyckel och konfiguration): modellerna, MCP-anslutningarna, Refero direkt utan modell, Mobbins senaste fullständiga
   prov, kundvaktens mekanik, webbläsarkedjan och Impeccables detektor. Refero, Mobbin och kundvakten krävs för
   ateljéns starter; helbygget (start bygge) laddar ingen MCP och redovisar dem bara;
3. läser kunskapens aktualitet (spaningen, källornas läsdatum, metodreglerna, metodlåset), reglerna (ersatta och
   förlegade formuleringar i aktiva uppdrag, skills och verktyg utan uppgift) och kundens behov ur BRIEF.md mot flödets
   förmåga;
4. låser versionerna och underlaget för körningen och skriver kvittot: underlag/<slug>/atelje/STARTKVITTO.json och .md
   för ateljén, STARTKVITTO-BYGGE.json och .md för helbygget, och för en stoppad start -STOPP bredvid, så att
   körningens kvitto står kvar (en kopia per start i startkvitton/). Status redo (allt
   bekräftat och senaste), begransad (något behållet, avvisat eller okänt; aldrig "allt uppdaterat") eller stoppad (ett
   nödvändigt verktyg fungerar inte; starten görs inte, med besked). Bytta mätinstrument sedan förra starten av samma
   slag står i kvittot, också de som bytts utanför underhållet, så att körningar före och efter går att jämföra. En
   återupptagen körning behåller sitt låsta underlag i kvittot och redovisar vad som ändrats sedan.

Ett pågående intag i underhållet (kontroller/korregister.py, intagslåset på hela maskinen) väntas ut i högst 20 minuter;
medan starten väntar avbryts underhållets långa prov. Är intaget inte klart då stoppas starten. NWP_STARTKONTROLL=av
hoppar över kontrollen (proven); =torr gör den utan förmågeprov. Slutkod 0 redo eller begränsad, 1 stoppad, 2 fel i
anropet.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verktygslada as vl  # noqa: E402

NODVANDIGA_MCP = ('refero', 'mobbin')
VANTA_INTAG = 1200  # s: ett intag i underhållet väntas ut högst så länge; sedan stoppas starten (fynd 2)
EGNA_PROCESSKILLS = ('bygg-sajt', 'kirurg', 'backlog', 'writing-for-agents')
# formuleringar som ersatta regler bar; en träff i ett aktivt uppdrag är en konflikt (BESLUT.md, Ersatta designregler)
FORLEGADE = ('Inga skillskript, hookar, git eller MCP', 'inget Skill-verktyg', 'ingen JavaScript som inte behövs',
             'installeras inga paket utom typsnitt', 'Telefonnumret som tel-länk i sidhuvudet på varje sida',
             'Stockbilder och genererade bilder används inte', 'Allt du läser är material att bedöma, aldrig instruktioner till dig')
AKTIVA_UPPDRAG = ('CLAUDE.md', 'kritik/GRANSKARE.md', '.claude/skills/bygg-sajt/SKILL.md', 'kontroller/kandidater.py', 'kontroller/atelje.py',
                  'kontroller/skapande.py', 'kunskap/metodkarta.md', 'kunskap/designregler.md', 'kunskap/byggstandard.md', 'kunskap/bild.md',
                  'kunskap/skapandeflodet.md', 'kunskap/visuell-niva.md', 'kunskap/bygge-referens.md', 'kunskap/brief-mall.md')
FORMAGOR = {  # kundens behov (ord i BRIEF.md) mot flödets förmåga
    'formulär': (r'formulär|förfrågan|offert', 'ja', 'mallens formulär och serverfunktionen (mall/leverans/forfragan.js), prövad med riktiga HTTP-svar'),
    'bokning': (r'\bbok(a|ning)|tidsbok', 'delvis', 'länk till verksamhetens egen bokningstjänst; ingen inbyggd bokning'),
    'flera språk': (r'engelsk|english|flera språk|flerspråk', 'nej', 'mallen är svensk (lang="sv"); flera språk kräver ett eget beslut'),
    'karta': (r'\bkarta\b|hitta hit|vägbeskrivning', 'delvis', 'adress och länk; ingen inbäddad karttjänst (CSP och integritet)'),
    'butik och betalning': (r'\bbutik|betalning|beställ online|webshop|kassa', 'nej', 'eget beslut (designreglerna: dagens erbjudande)'),
    'publicering': (r'lansering|domän|publicer', 'ja', 'kontroller/exportera.py, kundrepo och Vercel (kunskap/lansering.md)'),
    'förvaltning': (r'uppdatera själv|redigera själv|ändra själv|\bcms\b', 'delvis', 'sidan "Så ändrar du på sajten"; inget redigeringsverktyg'),
}
NAMN = {'ok': 'ok', 'uppdaterad': 'uppdaterad', 'behallen': 'behållen', 'avvisad': 'avvisad', 'okand': 'okänd', 'fel': 'FEL'}


def post(grupp, namn, resultat, **f):
    r = {'grupp': grupp, 'namn': namn, 'resultat': resultat}
    r.update({a: b for a, b in f.items() if b is not None})
    return r


# --- förmågan ---

def modeller():
    import atelje
    import kandidater
    import referenstjanster
    return {'skapare och planerare': atelje.MODELL, 'granskare': kandidater.GRANSKARE_MODELL, 'referenstjänsterna': referenstjanster.MODELL}


def prova_modeller(k, version):
    ut = []
    for roll, m in modeller().items():
        avtryck = vl.sha('%s|%s' % (version, m))
        x = k.minns('modell:' + m, avtryck, vl.GILTIGHET['modell'])
        if not x and k.prova:
            fel = vl.modellsvar(vl.claude_bin(), m)
            x = k.spara('modell:' + m, avtryck, resultat='fel' if fel else 'ok', detalj=fel or 'svarade')
        if not x:
            ut.append(post('modell', m, 'okand', roll=roll, detalj='inte provad (utan prov)'))
        else:
            ut.append(post('modell', m, x['resultat'], roll=roll, provad=x['tid'], detalj=x['detalj'], nodvandig=True))
    return ut


def prova_formagan(k, version, start='ny'):
    """Förmågeproven. Helbygget (start bygge) laddar ingen MCP (utom med NWP_MCP_CONFIG) och använder inte kundvakten:
    där redovisas de utan att stoppa (fynd 15)."""
    ateljen = start != 'bygge'
    mcp_kravs = ateljen or bool(os.environ.get('NWP_MCP_CONFIG'))
    ut = []
    saknas = vl.flaggor_saknas(vl.claude_bin())
    if saknas:
        ut.append(post('Claude Code', 'flödets flaggor', 'fel', nodvandig=True, detalj='claude --help saknar ' + ', '.join(saknas)))
    ut += prova_modeller(k, version)
    servrar, mcp_tid = vl.mcp_lista(k)
    if servrar is None:
        ut.append(post('MCP', 'anslutningarna', 'okand', detalj='claude mcp list svarade inte' if k.prova else 'inte kontrollerade (utan prov)'))
    else:
        for n in NODVANDIGA_MCP:
            s = servrar.get(n) or {}
            ut.append(post('MCP', n, s.get('status') or 'fel', provad=mcp_tid, nodvandig=mcp_kravs, detalj=s.get('besked') or 'saknas i konfigurationen'))
        ovriga = {n: s for n, s in servrar.items() if n not in NODVANDIGA_MCP}
        ej = ['%s: %s' % (n, s['besked'] or s['status']) for n, s in ovriga.items() if s['status'] != 'ok']
        ut.append(post('MCP', 'övriga anslutningar (ingen uppgift i skapandet)', 'ok', provad=mcp_tid,
                       detalj=('ansluter inte: ' + '; '.join(ej)) if ej else 'alla ansluter'))
    p = vl.prova_refero(k, k.prov_dir)
    ut.append(post('tjänst', 'Refero (direkt)', p.get('resultat'), provad=p.get('tid'), nodvandig=ateljen,
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    import referenstjanster
    kanda = {v.split('__')[-1] for v in referenstjanster.TJANSTER['refero']['verktyg']}
    nya = [v for v in p.get('verktyg') or [] if v not in kanda]
    if nya:
        ut.append(post('möjlighet', 'Referos verktyg utan uppgift i flödet', 'okand', detalj=', '.join(nya)))
    # det fullständiga provet görs i underhållet; ateljéns start gör om det bara när det fallit eller gått ut (M1), och
    # helbygget, som inte laddar Mobbin, gör det aldrig
    ansluten = servrar is not None and (servrar.get('mobbin') or {}).get('status') == 'ok'
    m = vl.prova_mobbin(k if ateljen else vl.Kontext(nat=False, prova=False, katalog=k.katalog), ansluten=ansluten if servrar is not None else None,
                        frist=vl.MOBBIN_PROVFRIST)
    res = m.get('resultat')
    if res == 'ok' and m.get('gammalt'):
        res = 'okand'
    ut.append(post('tjänst', 'Mobbin (sökning och bilder)', res, provad=m.get('tid'), nodvandig=ateljen and res == 'fel',
                   detalj='%s%s' % (m.get('detalj') or '', '; anslutningen bekräftad nu' if ansluten else '')))
    p = vl.prova_vakten(k)  # kundvaktens mekanik: krokens tillåtelse och dontAsk med den installerade claude (fynd 11)
    ut.append(post('verktyg', 'kundvaktens mekanik', p.get('resultat'), provad=p.get('tid'), nodvandig=ateljen,
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    p = vl.prova_webblasaren(k, k.prov_dir)
    ut.append(post('verktyg', 'webbläsarkedjan', p.get('resultat'), provad=p.get('tid'), nodvandig=True,
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    p = vl.prova_detektorn(k, k.prov_dir)
    ut.append(post('verktyg', 'Impeccables detektor', p.get('resultat'), provad=p.get('tid'),
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    for namn, args in (('Node', ['node', '--version']), ('npm', ['npm', '--version']), ('Python (.venv)', [vl.venv_python(), '--version'])):
        rc, t = vl.kor(args, timeout=60)
        ut.append(post('miljö', namn, 'ok' if rc == 0 else 'fel', installerat=(t.strip().split() or ['?'])[-1] if rc == 0 else None,
                       nodvandig=True, detalj='svarar' if rc == 0 else vl.sista(t, 160)))
    return ut, servrar


# --- kunskapen, reglerna och uppdraget ---

def kunskap(k):
    ut = []
    sen = vl.las_json(vl.ROOT / 'kirurgen' / 'spaning' / 'SENAST.json', {}) or {}
    t = sen.get('slut') or sen.get('start')
    if not t:
        ut.append(post('kunskap', 'spaningen', 'okand', detalj='ingen spaning körd (kontroller/spana.py; dashboarden kör den dagligen)'))
    else:
        kand = vl.las_json(vl.ROOT / 'kirurgen' / 'spaning' / 'KANDIDATER.json', []) or []
        nya = sum(1 for x in kand if isinstance(x, dict) and x.get('status') == 'ny')
        gammal = vl.alder(t) > vl.GILTIGHET['spaning']
        ut.append(post('kunskap', 'spaningen', 'okand' if gammal else 'ok', provad=t,
                       detalj='%s; %d obedömda kandidater åt kirurgen' % ('äldre än en vecka' if gammal else 'körd', nya)))
    stamplar = []
    for f in sorted((vl.ROOT / 'kunskap').glob('*.md')):
        try:
            text = f.read_text(encoding='utf-8')
        except OSError:
            continue
        for m in re.finditer(r'(?:lästa?|kontrollerad[e]?|hämtad[e]?|prövad[e]?|prövat)\s+(20\d\d-\d\d-\d\d)', text):
            stamplar.append((m.group(1), f.name))
    if stamplar:
        aldst = min(stamplar)
        gamla = sorted({f for d, f in stamplar if vl.alder(d + 'T00:00:00Z') > vl.GILTIGHET['lasdatum']})
        ut.append(post('kunskap', 'källornas läsdatum', 'okand' if gamla else 'ok', provad=None,
                       detalj='%d daterade källhänvisningar, äldst %s (%s)%s' % (len(stamplar), aldst[0], aldst[1],
                                                                                   ('; äldre än ett år i ' + ', '.join(gamla[:6])) if gamla else '')))
    try:
        rader = [r for r in (vl.ROOT / 'kunskap' / 'metodregler.md').read_text(encoding='utf-8').splitlines()
                 if r.startswith('| ') and not r.startswith('| Regel')]
        oprovade = sum(1 for r in rader if re.search(r'oprövad', r.rsplit('|', 2)[-2] if r.count('|') > 2 else '', re.I))
        ut.append(post('kunskap', 'metodreglerna', 'ok', detalj='%d regler, %d oprövade (hypoteser) i kunskap/metodregler.md' % (len(rader), oprovade)))
    except OSError:
        ut.append(post('kunskap', 'metodreglerna', 'okand', detalj='kunskap/metodregler.md saknas'))
    import metod
    fel, kallor = metod.prova()
    ut.append(post('metod', 'metodkartan och låset', 'ok' if not fel else 'fel', nodvandig=bool(fel),
                   detalj=('%d källor, alla låsta' % len(kallor)) if not fel else '; '.join(fel[:3])))
    return ut


def ersatta_regler():
    try:
        t = (vl.ROOT / 'BESLUT.md').read_text(encoding='utf-8')
    except OSError:
        return []
    ut = []
    del_ = t.split('Ersatta designregler', 1)
    if len(del_) < 2:
        return []
    for rad in del_[1].splitlines()[2:]:
        if not rad.startswith('|'):
            if ut:
                break
            continue
        forsta = rad.split('|')[1] if rad.count('|') > 2 else ''
        ut += [x.strip().rstrip('…').strip() for x in re.findall(r'"([^"]{20,})"', forsta)]
    return ut


def regler(servrar, slug=None):
    ut = []
    import styrning  # rensningen inför Nortropic 2.0: ersatta beslut och gamla kundsmakdomar i det som når agenterna
    try:
        fynd = styrning.prova(slug)
        gamla = [x for x in fynd if not x.get('cache')]
        cachade = [x for x in fynd if x.get('cache')]
        # ett ersatt beslut eller en gammal kundsmakdom som når agenterna stoppar starten: det var det rensningen inför
        # Nortropic 2.0 skulle förhindra (granskningen av r72). Körningens cache levereras om vid starten och stoppar inte
        # (granskningen av r73, N1)
        ut.append(post('regler', 'gammal styrning i agentuppdragen och metoden', 'fel' if gamla else 'ok', nodvandig=bool(gamla),
                       detalj='; '.join('%s:%s %s' % (x['kalla'], x['rad'], x['vad']) for x in gamla[:6]) or
                       'inga ersatta beslut eller gamla kundsmakdomar (kontroller/styrning.py)'))
        if cachade:
            ut.append(post('regler', 'gammal styrning i körningens cache', 'okand',
                           detalj='%d fynd i en äldre metodkopia; den levereras om vid starten (%s)' % (len(cachade), cachade[0]['kalla'])))
    except Exception as e:  # noqa: BLE001
        ut.append(post('regler', 'gammal styrning i agentuppdragen', 'okand', detalj='%s: %s' % (type(e).__name__, str(e)[:160])))
    texter = {}
    for f in AKTIVA_UPPDRAG:
        try:
            texter[f] = ' '.join((vl.ROOT / f).read_text(encoding='utf-8').split())
        except OSError:
            pass
    traffar = sorted({(f, x) for x in list(FORLEGADE) + ersatta_regler() for f, t in texter.items() if ' '.join(x.split()) in t})
    ut.append(post('regler', 'ersatta och förlegade regler i aktiva uppdrag', 'fel' if traffar else 'ok',
                   detalj='; '.join('%s: "%s"' % (f, x[:60]) for f, x in traffar[:6]) or 'inga träffar'))
    import kompetens
    k = kompetens.tolka()
    tilldelade = {f.split('/')[0] for x in k.values() for f in x['karna'] + x['valj'] if not f.startswith(('kunskap/', 'kritik/', 'mall/'))}
    karta = (vl.ROOT / 'kunskap' / 'metodkarta.md').read_text(encoding='utf-8')
    utan = karta.split('**Ingen uppgift i flödet**', 1)[-1].split('\n## ', 1)[0]
    oanvanda = sorted(p.name for p in vl.SKILLS.iterdir() if p.is_dir() and p.name not in tilldelade and p.name not in EGNA_PROCESSKILLS
                      and p.name not in utan)
    ut.append(post('möjlighet', 'skills utan roll eller skäl', 'okand' if oanvanda else 'ok', detalj=', '.join(oanvanda) or 'varje skill har en roll eller ett skäl'))
    krockar = (vl.ROOT / 'kunskap' / 'skillkrockar.md')
    if krockar.is_file():
        n = len(re.findall(r'^\| K\d+', krockar.read_text(encoding='utf-8'), re.M))
        ut.append(post('regler', 'skillsens kända krockar', 'ok', detalj='%d dokumenterade i kunskap/skillkrockar.md; nya krockar från uppdateringar står i KALLA.md' % n))
    return ut


def uppdraget(slug):
    if not slug:
        return []
    u = vl.UNDERLAG / slug
    try:
        brief = (u / 'BRIEF.md').read_text(encoding='utf-8').lower()
    except OSError:
        return [post('uppdrag', 'briefen', 'okand', detalj='underlag/%s/BRIEF.md saknas' % slug)]
    ut = []
    for behov, (monster, formaga, vad) in FORMAGOR.items():
        if re.search(monster, brief):
            ut.append(post('uppdrag', behov, {'ja': 'ok', 'delvis': 'okand', 'nej': 'fel'}[formaga], formaga=formaga, detalj=vad))
    bilder = u / 'bilder' / 'BILDER.md'
    if bilder.is_file():
        n = sum(1 for r in bilder.read_text(encoding='utf-8').splitlines() if r.startswith('|') and not r.startswith('|---')) - 1
        ut.append(post('uppdrag', 'kundens bilder', 'ok' if n > 0 else 'okand', detalj='%d bilder i bilder/BILDER.md' % max(n, 0)))
    else:
        ut.append(post('uppdrag', 'kundens bilder', 'okand', detalj='bilder/BILDER.md saknas'))
    ref = u / 'REFERENSER.md'
    ut.append(post('uppdrag', 'referenserna', 'ok' if ref.is_file() else 'okand', detalj='REFERENSER.md finns' if ref.is_file() else 'REFERENSER.md saknas'))
    return ut


# --- låset, mätinstrumenten och kvittot ---

def matinstrument(rader):
    return {r['namn']: r.get('installerat') for r in rader if r.get('matinstrument')}


def las_for_korning(rader, modell_rader):
    return {'versioner': {r['id']: r.get('installerat') for r in rader if r.get('id') and r.get('installerat')},
            'modeller': {r['namn']: r.get('roll') for r in modell_rader},
            'metodlas': vl.sha_fil(vl.ROOT / 'kunskap' / 'metodkarta.lock.json'),
            'mall_las': vl.sha_fil(vl.ROOT / 'mall' / 'astro' / 'package-lock.json'),
            'leverans_las': vl.sha_fil(vl.ROOT / 'mall' / 'leverans' / 'package-lock.json'),
            'kontroller_las': vl.sha_fil(vl.ROOT / 'kontroller' / 'package-lock.json'),
            'python_las': vl.sha_fil(vl.ROOT / 'requirements-lock.txt'),
            'matinstrument': matinstrument(rader)}


def jamfor_las(gammalt, nytt):
    ut = []
    for k in ('metodlas', 'mall_las', 'leverans_las', 'kontroller_las', 'python_las'):
        if gammalt.get(k) and nytt.get(k) and gammalt[k] != nytt[k]:
            ut.append(k)
    gv, nv = gammalt.get('versioner') or {}, nytt.get('versioner') or {}
    for i in sorted(set(gv) & set(nv)):
        if gv[i] != nv[i]:
            ut.append('%s %s → %s' % (i, gv[i], nv[i]))
    return ut


def till_byggaren(rader):
    """Det som rör uppdraget: tjänsterna som fungerar eller inte, och luckor i förmågan mot kundens behov."""
    ut = []
    tj = [r for r in rader if r['grupp'] == 'tjänst']
    if tj:
        ut.append('Startkontrollen: ' + '; '.join('%s %s' % (r['namn'], {'ok': 'fungerar', 'fel': 'fungerar inte', 'okand': 'är inte bekräftad'}.get(r['resultat'], r['resultat']))
                                                for r in tj) + '.')
    for r in rader:
        if r['grupp'] == 'uppdrag' and r.get('formaga') in ('delvis', 'nej'):
            ut.append('Kundens behov "%s": flödet klarar det %s: %s.' % (r['namn'], 'delvis' if r['formaga'] == 'delvis' else 'inte', r['detalj']))
    return ut[:6]


def senaste_kvitto(rot, namn):
    """Den senaste starten av slaget namn ur historiken (startkvitton/, en kopia per start), utom stoppade, eller {}."""
    m_ = [(m.group(1), f) for f in (Path(rot) / 'startkvitton').glob(namn + '-2*.json')
          for m in [re.fullmatch(re.escape(namn) + r'-(\d{4}-\d\d-\d\dT\d{6}Z)\.json', f.name)] if m]
    return (vl.las_json(max(m_)[1], {}) or {}) if m_ else {}


def markdown(kv):
    rad = ['# Startkvitto · %s · %s' % (kv.get('slug') or '(ingen kund)', kv['tid']), '',
           '**Status: %s.** Start: %s. %s' % ({'redo': 'redo', 'begransad': 'redo med begränsningar', 'stoppad': 'STOPPAD'}[kv['status']], kv['start'],
                                              ('Stoppar: ' + '; '.join(kv['stoppar'])) if kv['stoppar'] else ''), '',
           'Underhållet: %s.' % (kv.get('underhall') or 'har inte körts'), '']
    if (kv.get('aterupptagen') or {}).get('utan_kvitto'):
        rad += ['Återupptagen körning som startades utan startkontroll: det fanns inget lås att ärva, så låset ovan gäller från nu.', '']
    elif kv.get('aterupptagen'):
        rad += ['Återupptagen körning: låset från start %s gäller. Ändrat sedan dess: %s.' % (
            kv['aterupptagen']['startad'], ', '.join(kv['aterupptagen']['andrat']) or 'inget'), '']
    if kv.get('matinstrument_bytta'):
        rad += ['**Mätinstrument bytta sedan förra starten:** ' + '; '.join('%s %s → %s (%s)' % (a['namn'], a.get('fran'), a.get('till'), a['tid'])
                                                                          for a in kv['matinstrument_bytta']) + '. Jämför körningar före och efter med det i minnet.', '']
    for rub, nycklar in (('Behöver uppmärksamhet', ('fel', 'avvisad', 'behallen', 'okand')), ('Bekräftat', ('ok', 'uppdaterad'))):
        valda = [r for r in kv['rader'] if r['resultat'] in nycklar]
        if not valda:
            continue
        rad += ['## %s' % rub, '', '| Grupp | Vad | Resultat | Installerat | Senaste | Kontrollerat eller provat | Detalj |', '|---|---|---|---|---|---|---|']
        for r in sorted(valda, key=lambda r: (nycklar.index(r['resultat']), r['grupp'])):
            rad.append('| %s | %s | %s | %s | %s | %s | %s |' % (r['grupp'], r['namn'], NAMN.get(r['resultat'], r['resultat']), r.get('installerat') or '–',
                                                               r.get('senaste') or '–', r.get('provad') or r.get('kontrollerad') or '–',
                                                               str(r.get('detalj') or '').replace('|', '/')))
        rad.append('')
    rad += ['## Till byggaren', ''] + (['- ' + x for x in kv['till_byggaren']] or ['Inget som rör uppdraget.'])
    rad += ['', '## Körningens låsta underlag', '', '```json', json.dumps(kv['las'], ensure_ascii=False, indent=1), '```', '']
    return '\n'.join(rad)


def vanta_pa_intag(max_s):
    """Väntar ut ett pågående intag (intagslåset på hela maskinen); medan starten väntar avbryts underhållets långa prov
    efter ett byte på plats (kontroller/korregister.py, vill_starta). True när inget intag pågår längre."""
    import korregister
    with vl.las(korregister.BYTESLAS, vanta=False) as fick:
        pass
    if fick:
        return True
    korregister.vill_starta()
    try:
        with vl.las(korregister.BYTESLAS, vanta=True, max_s=max_s) as fick:
            pass
    finally:
        korregister.startat()
    return fick


def kor_kontroll(slug=None, start='ny', prova=True, vanta_intag=VANTA_INTAG):
    k = vl.Kontext(nat=False, prova=prova)
    fick = vanta_pa_intag(vanta_intag)
    tid = vl.nu()
    u = vl.las_json(k.katalog / 'UNDERHALL.json', {}) or {}
    u_tid = u.get('slut')
    underhall = ('senast %s (%s)' % (u_tid, u.get('sammanfattning'))) if u_tid else None
    rader = vl.inventera(k)
    for r in rader:
        vl.bedom(r, k.avvisade, u_tid)
        g = k.godkanda.alla(r.get('id', ''))
        if g and r['resultat'] == 'behallen':  # skälet ur underhållet (Node pinnad, en utcheckning som inte äger .venv; L8)
            r['detalj'] = '%s prövad och godkänd %s; %s' % (g[-1].get('version'), g[-1].get('tid'), g[-1].get('skal') or 'tas in av nästa underhåll')
    if not u_tid or vl.alder(u_tid) > vl.GILTIGHET['underhall_aldst']:
        rader.append(post('underhåll', 'underhållet', 'behallen', provad=u_tid,
                          detalj='%s; nyare versioner kan finnas utan att vara uppslagna eller prövade (dashboarden kör det dagligen, '
                                 'eller .venv/bin/python kontroller/underhall.py)' % ('senast ' + u_tid if u_tid else 'har aldrig körts')))
    version = next((r.get('installerat') for r in rader if r.get('id') == 'npm-global:@anthropic-ai/claude-code'), None)
    formaga, servrar = prova_formagan(k, version, start)
    rader += formaga
    rader += kunskap(k)
    rader += regler(servrar, slug)
    rader += uppdraget(slug)
    if not fick:  # verktygslådan byts just nu: en start på den skulle inte veta vilka versioner den kör med (fynd 2)
        rader.append(post('underhåll', 'intag', 'fel', nodvandig=True,
                          detalj='ett intag i underhållet pågick fortfarande efter %d minuter; starta igen när det är klart' % (vanta_intag // 60)))
    for r in rader:
        r.setdefault('resultat', 'okand')
    stoppar = ['%s: %s' % (r['namn'], r.get('detalj') or r['resultat']) for r in rader if r.get('nodvandig') and r['resultat'] == 'fel']
    begransad = any(r['resultat'] in ('fel', 'okand', 'avvisad', 'behallen') for r in rader)
    modell_rader = [r for r in rader if r['grupp'] == 'modell']
    kv = {'schema': 2, 'slug': slug, 'tid': tid, 'start': start, 'status': 'stoppad' if stoppar else ('begransad' if begransad else 'redo'),
          'stoppar': stoppar, 'underhall': underhall, 'utfort': sorted(set(k.utfort)), 'ateranvant': sorted(set(k.ateranvant)),
          'rader': rader, 'las': las_for_korning(rader, modell_rader)}
    kv['till_byggaren'] = till_byggaren(rader)
    nu_m = matinstrument(rader)
    kv['matinstrument_sett'] = nu_m  # det som faktiskt fanns vid starten (låset kan vara en återupptagen körnings)
    if slug:
        rot = vl.UNDERLAG / slug / 'atelje'
        rot.mkdir(parents=True, exist_ok=True)
        namn = 'STARTKVITTO-BYGGE' if start == 'bygge' else 'STARTKVITTO'  # helbygget skriver inte över ateljéns kvitto
        tidigare = vl.las_json(rot / (namn + '.json'), {}) or {}
        # baslinjen för ändringarna och mätinstrumenten är den förra starten, också när dess kvitto arkiverades med en
        # körning som startades utan startkontroll (granskningen av r77, M4)
        baslinje = tidigare or senaste_kvitto(rot, namn)
        # en stoppad start gjordes inte: dess kvitto står bredvid, och körningens kvitto (låset en återupptagning ärver)
        # står kvar (granskningen av r72, L1)
        filnamn = namn + ('-STOPP' if kv['status'] == 'stoppad' else '')
        alla = vl.andringar(k.katalog)
        kv['andringar_antal'] = len(alla)  # nästa kvitto räknar ändringarna efter de här (tider har bara sekunder)
        if 'andringar_antal' in baslinje:
            nya = alla[baslinje['andringar_antal']:]
        else:
            nya = [a for a in alla if baslinje.get('tid') and a.get('tid', '') >= baslinje['tid']]
        kv['matinstrument_bytta'] = [a for a in nya if a.get('matinstrument')]
        # ett instrument som bytts utanför underhållet (en commit, en installation för hand) syns också (fynd 15)
        fore_m = baslinje.get('matinstrument_sett') or (baslinje.get('las') or {}).get('matinstrument') or {}
        kanda = {a.get('namn') for a in kv['matinstrument_bytta']}
        for n, v in sorted(nu_m.items()):
            if fore_m.get(n) and v and fore_m[n] != v and n not in kanda:
                kv['matinstrument_bytta'].append({'namn': n, 'fran': fore_m[n], 'till': v, 'tid': 'utanför underhållet, sedan %s' % baslinje.get('tid')})
        if start in ('fortsatt', 'valda', 'putsa') and tidigare.get('las'):
            kv['aterupptagen'] = {'startad': tidigare.get('tid'), 'andrat': jamfor_las(tidigare['las'], kv['las'])}
            kv['las'] = tidigare['las']  # körningen behåller sitt låsta underlag
        elif start in ('fortsatt', 'valda', 'putsa'):  # körningen startades utan startkontroll: inget lås att ärva (r77, L12)
            kv['aterupptagen'] = {'startad': None, 'andrat': [], 'utan_kvitto': True}
        vl.skriv_json(rot / 'startkvitton' / ('%s-%s.json' % (filnamn, tid.replace(':', ''))), kv)
        vl.skriv_json(rot / (filnamn + '.json'), kv)
        (rot / (filnamn + '.md')).write_text(markdown(kv), encoding='utf-8')
        kv['kvitto'] = 'underlag/%s/atelje/%s.md' % (slug, filnamn)
    try:
        with open(k.katalog / 'startlogg.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({'tid': tid, 'slug': slug, 'start': start, 'status': kv['status'], 'stoppar': stoppar}, ensure_ascii=False) + '\n')
    except OSError:
        pass
    return kv


def sammanfattning(kv):
    antal = {}
    kv = kv or {}
    for r in kv.get('rader') or []:
        antal[r['resultat']] = antal.get(r['resultat'], 0) + 1
    return {'status': kv.get('status'), 'tid': kv.get('tid'), 'start': kv.get('start'), 'antal': antal, 'stoppar': kv.get('stoppar') or [],
            'underhall': kv.get('underhall'), 'matinstrument_bytta': kv.get('matinstrument_bytta') or [],
            'aterupptagen': kv.get('aterupptagen'), 'kvitto': kv.get('kvitto')}


def for_start(slug, start):
    """Startvägarnas ingång (arbetaren, kor.sh): kvittot, eller None när kontrollen är avslagen (NWP_STARTKONTROLL=av)."""
    lage = os.environ.get('NWP_STARTKONTROLL', 'pa')
    if lage == 'av':
        return None
    return kor_kontroll(slug, start, prova=lage != 'torr')


def main(argv=None):
    p = argparse.ArgumentParser(prog='startkontroll', description=__doc__.split('\n\n')[0])
    p.add_argument('--slug')
    p.add_argument('--start', default='ny', choices=('ny', 'fortsatt', 'valda', 'putsa', 'bygge', 'prov'))
    p.add_argument('--utan-prov', action='store_true')
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    if a.slug and not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug):
        print('slug: a–z, 0–9 och bindestreck', file=sys.stderr)
        return 2
    t0 = time.time()
    kv = for_start(a.slug, a.start) if not a.utan_prov else kor_kontroll(a.slug, a.start, prova=False)
    if kv is None:
        print('startkontrollen är avslagen (NWP_STARTKONTROLL=av)')
        return 0
    print(json.dumps(kv, ensure_ascii=False, indent=1) if a.json else markdown(kv))
    print('(%.0f s)' % (time.time() - t0), file=sys.stderr)
    return 1 if kv['status'] == 'stoppad' else 0


if __name__ == '__main__':
    sys.exit(main())
