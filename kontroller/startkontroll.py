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
4. låser körningens verktygsunderlag (las_for_korning: verktygens versioner, modellerna, mätinstrumenten och hasharna av
   metodlåset och låsfilerna för mallen, leveransen, kontrollerna och Python; kundens underlag ingår inte) och skriver
   kvittot: underlag/<slug>/atelje/STARTKVITTO.json och .md för ateljén, STARTKVITTO-BYGGE.json och .md för helbygget,
   och för en stoppad start -STOPP bredvid, så att körningens kvitto står kvar (en kopia per start i startkvitton/).
   Status redo (inget som begränsar: det som prövats är bekräftat och senast; ett nytt verktyg eller en ny skill utan
   beslut kan ändå stå under Behöver uppmärksamhet), begransad (något fel som inte stoppar, delvis, behållet, avvisat
   eller okänt; aldrig "allt uppdaterat"; ett nytt verktyg utan beslut, ett beslut om ingen uppgift, underlag som är
   planerat i ett senare steg och det som inte gäller starten begränsar inte) eller stoppad (ett nödvändigt verktyg
   fungerar inte; starten görs inte, med besked). Bytta mätinstrument sedan förra starten av samma slag står i kvittot, också de som bytts utanför
   underhållet, så att körningar före och efter går att jämföra. En återupptagen körning behåller sitt lås i kvittot och
   redovisar vad som ändrats sedan.
5. skriver i kvittot vilken version av repot starten gällde (commit och gren ur git rev-parse, antalet ocommittade filer
   ur git status --porcelain; utan git "ej angivet"; commiten också i startloggen) och en informationsrad om
   dokumentationen (README.md, Var information finns): finns platsregeln, och hur många poster i den privata
   förteckningen underlag/granskningar/FORTECKNING.jsonl vars fil saknas eller har fel sha256. Raden stoppar aldrig en
   start och ändrar inte statusen; det som inte går att kontrollera står som "ej kontrollerad" med felet.

Kvittots betydelse (ägarens uppdrag 2026-10-07, punkt 3, ordagrant i minnet): kvittot säger vilken körväg och fas det
gäller (prototypkörningen i kandidatflödet eller i den äldre utforskningen, eller helbygget; aldrig Figma-piloten), och
det använder tillståndsorden i kontroller/kompetens.py (TILLSTAND) för kompetensen och underlaget. Referensunderlaget
prövas efter körväg och fas: före researchen förutsättningarna, med underlaget som planerat i researchen; efter den
FORSKNING.json, referenspaketet, TJANSTER.json och UPPDRAGSMATERIAL.json; i den äldre utforskningen REFERENSER.md:s rader;
i helbygget och putsningen VINNARE.json. Kontrollen skriver aldrig i underlaget. Vad ateljéns sessioner når prövas med
flödets egna argument (verktygslada.prova_sessionen), och en tilldelad tjänst som sessionen inte når står som
"tilldelad men åtkomst saknas", aldrig som ok. Varje upptäckt verktyg hos Refero och Mobbin har ett beslut i
metodkartan (uppgift, eller ingen uppgift med skäl och provdatum); ett verktyg utan beslut står som "nytt, obedömt" med
åtgärd och gör inte kvittot begränsat. Kvittot visar för varje roll i metodkartan det tilldelade och åtkomsten i
sessionen; användningen observeras i körningen.

Ett pågående intag i underhållet (kontroller/korregister.py, intagslåset på hela maskinen) väntas ut i högst 20 minuter;
medan starten väntar avbryts underhållets långa prov. Är intaget inte klart då stoppas starten. NWP_STARTKONTROLL=av
hoppar över kontrollen (proven); =torr gör den utan förmågeprov. Slutkod 0 redo eller begränsad, 1 stoppad, 2 fel i
anropet.

Diskvakten (punkt 6 i städregeln, BESLUT.md 2026-10-06): har disken under 15 % ledigt körs städningen
(kontroller/stadning.py) före starten, och kvittot redovisar ledigt utrymme före och efter med städningens
redovisning. Städningen stoppar aldrig starten.
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
DISKVAKT = 0.15  # under 15 % ledigt städas det före starten (städregeln, BESLUT.md 2026-10-06, punkt 6)
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
NAMN = {'ok': 'ok', 'uppdaterad': 'uppdaterad', 'behallen': 'behållen', 'avvisad': 'avvisad', 'okand': 'okänd', 'fel': 'FEL',
        'delvis': 'delvis', 'nytt': 'nytt, obedömt', 'ingen_uppgift': 'ingen uppgift (beslut)', 'planerat': 'planerat',
        'ej_tillampligt': 'gäller inte starten'}
# resultaten som gör kvittot begränsat. Ett nytt verktyg utan beslut, ett beslut om ingen uppgift, underlag som hör
# till ett senare steg och det som inte gäller starten gör det aldrig (ägarens uppdrag 2026-10-07, punkt 3)
BEGRANSAR = ('fel', 'delvis', 'okand', 'avvisad', 'behallen')
GRUPPER = (('Behöver uppmärksamhet', ('fel', 'delvis', 'avvisad', 'behallen', 'okand', 'nytt')),
           ('Planerat i ett senare steg', ('planerat',)), ('Bekräftat', ('ok', 'uppdaterad')),
           ('Upptäckt utan uppgift i flödet (beslut i metodkartan)', ('ingen_uppgift',)),
           ('Gäller inte den här starten (inte prövat)', ('ej_tillampligt',)))
TJNAMN = {'refero': 'Refero', 'mobbin': 'Mobbin'}
FIGMA = ('Kvittot gäller inte Figma-piloten: pilotens sessioner startas utanför repots körvägar och prövas inte av '
         'startkontrollen (kunskap/skapandeflodet.md, Figma).')
# vad ägaren eller flödet gör när en tilldelad tjänst inte når ateljéns sessioner
ATGARD = {'mobbin': 'ateljéns sessioner får Mobbin genom --mcp-config kontroller/mcp/mobbin.json (atelje.session_args); '
                    'kontrollera filen och Mobbins inloggning (OAuth, claude mcp list) och kör startkontrollen igen',
          # Referos nyckel ges aldrig till sessionerna (atelje.session_miljo tar bort den; granskning 4, G15)
          'refero': 'Refero når sessionerna bara genom repots lokala MCP-anslutning, som gäller i huvudutcheckningen och dess '
                    'worktrees: kör flödet därifrån, eller låt ägaren lägga tillbaka den lokala anslutningen. Sessionerna får '
                    'aldrig Referos nyckel'}
EJ_ANGIVET = 'ej angivet'  # ett saknat värde gissas aldrig (README.md, Var information finns: rapporthuvudet)
PLATSREGEL = '## Var information finns'  # README.md: var varje slag av information hör hemma (ägarens uppdrag 2026-10-06)
FORTECKNING = Path('underlag') / 'granskningar' / 'FORTECKNING.jsonl'  # privat; sökvägarna i den räknas från underlag/


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


def provtillstand(resultat):
    """Ett förmågeprovs utfall i tillståndsorden: ok är provat och fungerande, fel blockerat eller misslyckat, och ett prov
    som inte gjorts är inte observerat."""
    return 'provat' if resultat == 'ok' else 'blockerat' if resultat == 'fel' else 'ej_observerat'


def prova_formagan(k, version, start='ny'):
    """Förmågeproven. Helbygget (start bygge) laddar ingen MCP (utom med NWP_MCP_CONFIG) och använder inte kundvakten:
    där redovisas de utan att stoppa (fynd 15). Ger (raderna, claude mcp list, sessionsprovet, de upptäckta verktygen per
    tjänst eller None när tjänstens lista inte lästes)."""
    ateljen = start != 'bygge'
    mcp_kravs = ateljen or bool(os.environ.get('NWP_MCP_CONFIG'))
    ut = []
    saknas = vl.flaggor_saknas(vl.claude_bin())
    if saknas:
        ut.append(post('Claude Code', 'flödets flaggor', 'fel', nodvandig=True, detalj='claude --help saknar ' + ', '.join(saknas)))
    ut += prova_modeller(k, version)
    servrar, mcp_tid = vl.mcp_lista(k)
    if servrar is None:
        ut.append(post('MCP på maskinen', 'anslutningarna', 'okand', tillstand='ej_observerat',
                       detalj='claude mcp list svarade inte' if k.prova else 'inte kontrollerade (utan prov)'))
    else:
        for n in NODVANDIGA_MCP:
            s = servrar.get(n) or {}
            # claude mcp list läser maskinens konfiguration, också användarnivån som flödets sessioner inte laddar: raden
            # säger att anslutningen finns, inte att sessionerna når den (raden "<tjänst> i ateljéns session")
            ut.append(post('MCP på maskinen', n, s.get('status') or 'fel', provad=mcp_tid, nodvandig=mcp_kravs,
                           tillstand='tillgangligt' if s.get('status') == 'ok' else 'blockerat',
                           detalj='%s (claude mcp list: maskinens konfiguration; vad flödets sessioner når står på raden "%s i ateljéns '
                                  'session")' % (s.get('besked') or 'saknas i konfigurationen', TJNAMN.get(n, n)) if ateljen else
                           '%s (claude mcp list; helbygget laddar ingen MCP)' % (s.get('besked') or 'saknas i konfigurationen')))
        ovriga = {n: s for n, s in servrar.items() if n not in NODVANDIGA_MCP}
        ej = ['%s: %s' % (n, s['besked'] or s['status']) for n, s in ovriga.items() if s['status'] != 'ok']
        ut.append(post('MCP på maskinen', 'övriga anslutningar (ingen uppgift i skapandet)', 'ok', provad=mcp_tid, tillstand='tillgangligt',
                       detalj=('ansluter inte: ' + '; '.join(ej)) if ej else 'alla ansluter; flödets sessioner nekas varje anrop till dem'))
    p = vl.prova_refero(k, k.prov_dir)
    ut.append(post('tjänst', 'Refero (direkt)', p.get('resultat'), provad=p.get('tid'), nodvandig=ateljen, tillstand=provtillstand(p.get('resultat')),
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    upptackta = {'refero': set(p['verktyg']) if p.get('verktyg') else None, 'mobbin': None}
    # det fullständiga provet görs i underhållet; ateljéns start gör om det bara när det fallit eller gått ut (M1), och
    # helbygget, som inte laddar Mobbin, gör det aldrig
    ansluten = servrar is not None and (servrar.get('mobbin') or {}).get('status') == 'ok'
    m = vl.prova_mobbin(k if ateljen else vl.Kontext(nat=False, prova=False, katalog=k.katalog), ansluten=ansluten if servrar is not None else None,
                        frist=vl.MOBBIN_PROVFRIST)
    res = m.get('resultat')
    if res == 'ok' and m.get('gammalt'):
        res = 'okand'
    ut.append(post('tjänst', 'Mobbin (sökning och bilder)', res, provad=m.get('tid'), nodvandig=ateljen and res == 'fel', tillstand=provtillstand(res),
                   detalj='%s%s' % (m.get('detalj') or '', '; anslutningen bekräftad nu' if ansluten else '')))
    # vad ateljéns sessioner når: en kort session med flödets egna argument (ägarens uppdrag 2026-10-07, punkt 3);
    # helbygget har inga ateljésessioner och laddar ingen MCP
    try:
        sess = vl.prova_sessionen(k) if ateljen else None
    except Exception as e:  # noqa: BLE001 — ett prov som inte kan göras blir "inte prövad" på raderna, aldrig ett avbrott
        sess = {'resultat': 'fel', 'detalj': 'sessionsprovet kunde inte göras: %s: %s' % (type(e).__name__, vl.sista(e, 160))}
    if sess and sess.get('resultat') == 'ok':
        for t in upptackta:
            sett = {v.split('__')[-1] for v in sess.get('verktyg') or [] if v.startswith('mcp__%s__' % t)}
            if sett:
                upptackta[t] = (upptackta[t] or set()) | sett
    p = vl.prova_vakten(k)  # kundvaktens mekanik: krokens tillåtelse och dontAsk med den installerade claude (fynd 11)
    ut.append(post('verktyg', 'kundvaktens mekanik', p.get('resultat'), provad=p.get('tid'), nodvandig=ateljen, tillstand=provtillstand(p.get('resultat')),
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    p = vl.prova_webblasaren(k, k.prov_dir)
    ut.append(post('verktyg', 'webbläsarkedjan', p.get('resultat'), provad=p.get('tid'), nodvandig=True, tillstand=provtillstand(p.get('resultat')),
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    p = vl.prova_detektorn(k, k.prov_dir)
    ut.append(post('verktyg', 'Impeccables detektor', p.get('resultat'), provad=p.get('tid'), tillstand=provtillstand(p.get('resultat')),
                   detalj=(p.get('detalj') or '') + (' (återanvänt prov)' if p.get('ateranvant') else '')))
    for namn, args in (('Node', ['node', '--version']), ('npm', ['npm', '--version']), ('Python (.venv)', [vl.venv_python(), '--version'])):
        rc, t = vl.kor(args, timeout=60)
        ut.append(post('miljö', namn, 'ok' if rc == 0 else 'fel', installerat=(t.strip().split() or ['?'])[-1] if rc == 0 else None,
                       nodvandig=True, detalj='svarar' if rc == 0 else vl.sista(t, 160)))
    return ut, servrar, sess, upptackta


# --- åtkomsten i ateljéns session, tjänsternas verktyg och rollerna (ägarens uppdrag 2026-10-07, punkt 2 och 3) ---

def mcp_atkomst(sess, tjanst):
    """(tillstånd, orsak) för en tjänst i ateljéns session ur sessionsprovet: provat och fungerande när sessionen laddar
    tjänsten och flödets alla verktyg hos den syns, blockerat med orsaken annars, och inte observerat utan prov."""
    import referenstjanster
    if not sess or sess.get('resultat') != 'ok':
        return 'ej_observerat', 'åtkomsten är inte prövad: %s' % ((sess or {}).get('detalj') or 'inget sessionsprov')
    status = (sess.get('servrar') or {}).get(tjanst)
    saknas = [v.split('__')[-1] for v in referenstjanster.TJANSTER[tjanst]['verktyg'] if v not in (sess.get('verktyg') or [])]
    if status == 'connected' and not saknas:
        return 'provat', None
    if not status:
        return 'blockerat', 'sessionen laddar inte %s' % TJNAMN.get(tjanst, tjanst)
    if status != 'connected':
        return 'blockerat', '%s har status %s i sessionen' % (TJNAMN.get(tjanst, tjanst), status)
    return 'blockerat', 'flödets verktyg %s syns inte i sessionen' % ', '.join(saknas)


def atkomstrader(sess, ateljen):
    """En rad per tilldelad tjänst om åtkomsten i ateljéns session: ok bara när en session med flödets egna argument når
    den; annars "tilldelad men åtkomst saknas" med konsekvens och åtgärd, aldrig ok (ägarens uppdrag 2026-10-07, punkt
    3). Raden stoppar inte starten: researchens tjänstesessioner når tjänsterna på en egen väg (raderna Refero (direkt)
    och Mobbin (sökning och bilder)), men kvittot blir begränsat."""
    if not ateljen:
        return []
    import kompetens
    import referenstjanster
    roller_k = kompetens.tolka()
    ut = []
    for t in NODVANDIGA_MCP:
        roller = sorted(x['id'] for x in roller_k.values() if t in x['mcp'])
        tilld = ('tilldelad rollerna %s i metodkartan' % ', '.join(roller)) if roller else 'ingen roll i metodkartan'
        tillstand, orsak = mcp_atkomst(sess, t)
        namn = '%s i ateljéns session' % TJNAMN[t]
        if tillstand == 'provat':
            ut.append(post('åtkomst', namn, 'ok', tillstand='provat', provad=sess.get('tid'),
                           detalj='%s; en session med ateljéns egna argument (%s) laddar %s, och flödets %d verktyg hos den syns%s' % (
                               tilld, ', '.join(sess.get('flaggor') or []), TJNAMN[t], len(referenstjanster.TJANSTER[t]['verktyg']),
                               ' (återanvänt prov)' if sess.get('ateranvant') else '')))
        elif tillstand == 'blockerat':
            ut.append(post('åtkomst', namn, 'fel', tillstand='blockerat', provad=sess.get('tid'),
                           detalj='tilldelad men åtkomst saknas: %s. Konsekvens: rollerna %s kan inte göra egna anrop till %s i sina '
                                  'sessioner; researchens och uppdragens material når dem ändå, genom tjänstesessionerna. Raden stoppar '
                                  'inte starten, eftersom den vägen prövas för sig (raden %s). Åtgärd: %s' % (
                                      orsak, ', '.join(roller) or '–', TJNAMN[t],
                                      'Refero (direkt)' if t == 'refero' else 'Mobbin (sökning och bilder)', ATGARD[t])))
        else:
            ut.append(post('åtkomst', namn, 'okand', tillstand='ej_observerat', provad=(sess or {}).get('tid'), detalj='%s; %s' % (tilld, orsak)))
    ovriga = sorted('%s (%s)' % (n, s) for n, s in ((sess or {}).get('servrar') or {}).items() if n not in NODVANDIGA_MCP) \
        if sess and sess.get('resultat') == 'ok' and isinstance(sess.get('servrar'), dict) else []
    if ovriga:  # till exempel claude.ai-kopplingarna: de laddas utan strikt läge, och dontAsk nekar varje anrop till dem
        ut.append(post('åtkomst', 'övriga MCP i ateljéns session', 'ingen_uppgift', tillstand='tillgangligt', provad=sess.get('tid'),
                       detalj='%s: ingen uppgift i skapandet (metodkartan, Ingen uppgift i flödet); kundvakten släpper dem inte, och '
                              'dontAsk nekar varje anrop' % ', '.join(ovriga)))
    return ut


def tjanstverktyg_rader(upptackta):
    """Ett beslut per upptäckt verktyg hos Refero och Mobbin (ägarens uppdrag 2026-10-07, punkt 2 och 3A; Codex fann att
    skillnaden mellan upptäckta och tillåtna verktyg blev "okänd"). Besluten står i metodkartan (kompetens.tjanstverktyg):
    verktygen med uppgift är exakt kundvaktens (referenstjanster.TJANSTER), ett verktyg med beslutet ingen uppgift står
    med skäl och provdatum, och ett verktyg utan beslut står som "nytt, obedömt" med åtgärd. Inget av dem är "okänt", och
    inget gör kvittot begränsat för att det är nytt; ett tilldelat verktyg som tjänsten inte längre har är ett fel."""
    import kompetens
    import referenstjanster
    beslut = kompetens.tjanstverktyg()
    oense = kompetens.tjanstverktyg_fel()
    ut = []
    for t in sorted(referenstjanster.TJANSTER):
        namn = TJNAMN.get(t, t)
        tilldelade = [v.split('__')[-1] for v in referenstjanster.TJANSTER[t]['verktyg']]
        sett = upptackta.get(t)
        fel = [f for f in oense if f.startswith(t + ':')]
        borta = [v for v in tilldelade if sett is not None and v not in sett]
        if borta:
            fel.append('tilldelade men saknas hos %s: %s (researchens och skaparnas anrop till dem går inte; pröva tjänstens '
                       'nuvarande verktyg och skriv besluten i kunskap/metodkarta.md och referenstjanster.TJANSTER)' % (namn, ', '.join(borta)))
        ut.append(post('möjlighet', '%ss verktyg med uppgift' % namn, 'fel' if fel else 'ok', tillstand='blockerat' if fel else 'tilldelat',
                       detalj='; '.join(fel) if fel else '%d verktyg med uppgift i flödet (beslut i metodkartan, släppta av kundvakten)%s' % (
                           len(tilldelade), '' if sett is not None else '; tjänstens verktygslista lästes inte i den här starten')))
        for v in sorted((sett or set()) - set(tilldelade)):
            b = (beslut.get(t) or {}).get(v) or {}
            if b.get('beslut') == 'uppgift':  # beslutet säger uppgift, men kundvakten släpper det inte
                ut.append(post('möjlighet', '%s (%s)' % (v, namn), 'fel', tillstand='blockerat',
                               detalj='metodkartan ger verktyget en uppgift, men kundvakten släpper det inte (referenstjanster.TJANSTER); '
                                      'för in det där eller ändra beslutet'))
            elif b.get('beslut') == 'ingen uppgift':
                skal = re.sub(r'[;,]?\s*prövat 20\d\d-\d\d-\d\d\.?\s*$', '', str(b.get('text') or ''))
                ut.append(post('möjlighet', '%s (%s)' % (v, namn), 'ingen_uppgift', tillstand='tillgangligt',
                               detalj='upptäckt, ingen uppgift (beslut i kunskap/metodkarta.md, prövat %s) %s. Kundvakten nekar anrop till '
                                      'det' % (b.get('provat'), skal)))
            else:
                ut.append(post('möjlighet', '%s (%s)' % (v, namn), 'nytt', tillstand='tillgangligt',
                               detalj='nytt, obedömt: upptäckt hos %s utan beslut i metodkartan; kundvakten nekar anrop till det tills '
                                      'vidare. Åtgärd: pröva vad det tillför referensarbetet och skriv beslutet i kunskap/metodkarta.md '
                                      '(Kompetenserna, tjänsternas verktyg): uppgift, med verktyget i referenstjanster.TJANSTER, eller '
                                      'ingen uppgift med skäl och provdatum' % namn))
    return ut


def roller(sess, rader, ateljen):
    """Kvittot per roll (ägarens uppdrag 2026-10-07, punkt 3): för varje roll i metodkartan det tilldelade (kärnan,
    alternativen, skillsen, verktygen och MCP:erna) och åtkomsten i ateljéns session: skillsen och MCP:erna ur
    sessionsprovet, förhandsvisningen och detektorn ur sina prov, uxsok och design som tillgängliga när skriptet finns.
    Användningen observeras i körningen (kompetenskvittot), aldrig här. Helbygget har inga roller i metodkartan."""
    if not ateljen:
        return []
    import kompetens
    import metod
    radmap = {r['namn']: r for r in rader}
    sess_ok = bool(sess and sess.get('resultat') == 'ok')
    i_sess = set((sess or {}).get('skills') or [])
    skript = {'uxsok': 'uxsok.py', 'design': 'design.py'}
    prov = {'förhandsvisning': 'webbläsarkedjan', 'detektor': 'Impeccables detektor'}
    ordning = ('blockerat', 'ej_observerat', 'tillgangligt', 'provat')
    ut = []
    for kid, x in kompetens.tolka().items():
        filer = x['karna'] + x['valj']
        skills = sorted({f.split('/')[0] for f in filer if not f.startswith(('kunskap/', 'kritik/', 'mall/'))})
        filer_saknas = [f for f in filer if not metod.kalla(f).is_file()]
        ute = [s for s in skills if s not in i_sess] if sess_ok else []
        # en fil som saknas blockerar; en skill som skillverktyget saknar läses ändå med Read (kärnan läses som filer)
        sk_t = 'blockerat' if filer_saknas else 'tillgangligt' if ute else 'provat' if sess_ok else 'ej_observerat'
        mcp = {m: dict(zip(('tillstand', 'orsak'), mcp_atkomst(sess, m))) for m in x['mcp']}
        verktyg = {}
        for v in x['verktyg']:
            if v in prov:
                verktyg[v] = provtillstand((radmap.get(prov[v]) or {}).get('resultat'))
            else:
                verktyg[v] = 'tillgangligt' if (vl.ROOT / 'kontroller' / skript.get(v, v + '.py')).is_file() else 'blockerat'
        alla = [sk_t] + [m['tillstand'] for m in mcp.values()] + list(verktyg.values())
        ut.append({'roll': kid, 'namn': x['namn'], 'pass': x['pass'], 'uppgift': x['uppgift'],
                   'tilldelat': {'tillstand': 'tilldelat', 'karna': len(x['karna']), 'valj': len(x['valj']), 'skills': skills,
                                 'verktyg': x['verktyg'], 'mcp': x['mcp']},
                   'atkomst': {'tillstand': min(alla, key=ordning.index),
                               'skills': {'tillstand': sk_t, 'i_sessionen': len(skills) - len(ute) if sess_ok else None, 'av': len(skills),
                                          'saknas': ute, 'filer_saknas': filer_saknas},
                               'mcp': mcp, 'verktyg': verktyg},
                   'anvandning': 'ej_observerat'})
    return ut


def roll_text(r):
    """En rolls rad i kvittots tabell, i tillståndsorden."""
    import kompetens
    T = kompetens.TILLSTAND
    a, t = r['atkomst'], r['tilldelat']
    sk = a['skills']
    sk_txt = ('skills %d av %d i skillverktyget' % (sk['i_sessionen'], sk['av'])) if sk.get('i_sessionen') is not None else 'skills %s' % T[sk['tillstand']]
    if sk.get('saknas'):
        sk_txt += ' (skillverktyget saknar %s; filerna läses med Read)' % ', '.join(sk['saknas'])
    if sk.get('filer_saknas'):
        sk_txt += ' (filer saknas: %s; rollen kan inte läsa dem, åtgärd: kör kontroller/metod.py --prova)' % ', '.join(sk['filer_saknas'])
    delar = [sk_txt] + ['%s: %s%s' % (m, T[x['tillstand']], ' (tilldelad men åtkomst saknas: %s)' % x['orsak'] if x['tillstand'] == 'blockerat' else '')
                        for m, x in a['mcp'].items()] + ['%s: %s' % (v, T[s]) for v, s in a['verktyg'].items()]
    tilld = '%s: kärna %d och alternativ %d filer (%d skills); verktyg %s; MCP %s' % (
        T['tilldelat'], t['karna'], t['valj'], len(t['skills']), ', '.join(t['verktyg']) or '–', ', '.join(t['mcp']) or '–')
    return '| %s (%s) | %s | %s | %s: %s | %s här; användningen observeras i körningen (kompetenskvittot) |' % (
        r['namn'], r['roll'], ', '.join(r['pass']), tilld, T[a['tillstand']], '; '.join(delar).replace('|', '/'), T[r['anvandning']])


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
    # hela namnet, inte en del av ett ord: "design" i en mening om design räknas inte som ett skäl för skillen design
    oanvanda = sorted(p.name for p in vl.SKILLS.iterdir() if p.is_dir() and p.name not in tilldelade and p.name not in EGNA_PROCESSKILLS
                      and not re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(p.name), utan))
    # en ny skill utan beslut är "nytt, obedömt" med åtgärd, aldrig okänd, och gör inte kvittot begränsat (ägarens uppdrag
    # 2026-10-07, punkt 3)
    ut.append(post('möjlighet', 'skills utan roll eller skäl', 'nytt' if oanvanda else 'ok', tillstand='tillgangligt' if oanvanda else 'tilldelat',
                   detalj=('nytt, obedömt: %s. Åtgärd: ge skillen en roll i ett kompetensblock eller skriv skälet under "Ingen uppgift i '
                           'flödet" i kunskap/metodkarta.md' % ', '.join(oanvanda)) if oanvanda else 'varje skill har en roll eller ett skäl'))
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
    return ut


# --- körvägen, fasen och referensunderlaget (ägarens uppdrag 2026-10-07, punkt 3B) ---

def korvag(slug, start):
    """Körvägen och fasen kvittot gäller: prototypkörningen i kandidatflödet eller i den äldre utforskningen, eller
    helbygget, och för prototypkörningen om researchen (kandidatflödet) eller valet (den äldre utforskningen) är gjort.
    Läget avgörs som ateljén avgör det (atelje.kandidatflode_pa och kandidatkorning; i kandidatflödet blir --putsa --valda
    före arbetaren), ur körningens STATUS.json, som arbetaren skriver före startkontrollen. En ny start arkiverar förra
    körningens research, så den är alltid före researchen. Kvittot gäller aldrig Figma-piloten."""
    if start == 'bygge':
        return {'id': 'helbygget', 'namn': 'helbygget (kor.sh med skillen bygg-sajt)', 'fas': 'bygge', 'fas_namn': 'före bygget'}
    if not slug or start == 'prov':
        return {'id': 'ingen', 'namn': 'ingen körväg (%s)' % ('provstart utan kund' if not slug else 'startslaget prov'), 'fas': None, 'fas_namn': None}
    import atelje
    rot = vl.UNDERLAG / slug / 'atelje'
    st = vl.las_json(rot / 'STATUS.json', {}) or {}
    st = st if isinstance(st, dict) else {}
    if start == 'ny':
        kandidat = atelje.kandidatflode_pa()
    elif start == 'putsa':
        kandidat = False
    else:
        kandidat = start == 'valda' or atelje.kandidatkorning(rot, st)
    if kandidat:
        gjord = start != 'ny' and (rot / 'FORSKNING.json').is_file()
        return {'id': 'kandidatflodet', 'namn': 'prototypkörningen i kandidatflödet (kontroller/prototyp.py eller atelje.py med kandidater.py)',
                'fas': 'efter_research' if gjord else 'fore_research', 'fas_namn': 'efter researchen' if gjord else 'före researchen'}
    valt = start == 'putsa' or (start == 'fortsatt' and bool(((st.get('faser') or {}).get('valj') or {}).get('klar') or st.get('putsning')))
    return {'id': 'aldre', 'namn': 'prototypkörningen i den äldre utforskningen (NWP_KANDIDATFLODE=av)',
            'fas': 'efter_val' if valt else 'fore_utforskning', 'fas_namn': 'efter valet' if valt else 'före utforskningen'}


def bildfil(slug, fil):
    """En bild som underlaget anger: underlag/<slug>/… när vägen börjar med underlag/, annars relativt kundens underlag."""
    f = str(fil)
    return vl.ROOT / f if f.startswith('underlag/') else vl.UNDERLAG / slug / f


def befintligt_material(slug):
    """Referensmaterialet som redan finns och som researchen kan återanvända: tillgängligt, inte prövat för uppdraget."""
    import skapande
    ut = []
    p = skapande.senaste_paket(slug, vl.UNDERLAG)
    if p:
        k_ = [x for x in (vl.las_json(p / 'PAKET.json', {}) or {}).get('kandidater') or [] if isinstance(x, dict)]
        ut.append('referenspaketet %s (%d av %d sajter fångade)' % (p.name, sum(1 for x in k_ if x.get('ok')), len(k_)))
    tj = vl.las_json(vl.UNDERLAG / slug / 'referenser' / 'tjanster' / 'TJANSTER.json', {}) or {}
    if isinstance(tj, dict) and tj.get('tid'):
        ut.append('tjänsternas rapport %s (%s)' % (tj['tid'], ', '.join('%s %d bilder' % (TJNAMN.get(t, t), int(x.get('bilder') or 0))
                                                                         for t, x in sorted((tj.get('tjanster') or {}).items()) if isinstance(x, dict)) or 'inga tjänster'))
    return ('tillgängligt att återanvända: ' + ', '.join(ut)) if ut else 'inget befintligt referensmaterial; researchen hämtar det'


def fore_research(slug, rader):
    """Kandidatflödet före researchen: underlaget är planerat i researchen, och förutsättningarna prövas (underlaget
    researchen läser, att kundvakten kan läsa kundens uppgifter, och tjänsternas och kundvaktens prov ovan). Ett saknat
    underlag gör aldrig kvittot begränsat här: det skrivs av researchen."""
    import skapande
    u = vl.UNDERLAG / slug
    hinder, oklart = [], []
    saknas = [p.name for p in (u / 'BRIEF.md', u / 'RESEARCH.md', skapande.textfil(slug, vl.UNDERLAG)) if not p.is_file()]
    if saknas:
        hinder.append('underlaget som researchen läser saknas (%s)' % ', '.join(saknas))
    f = skapande.forbjudna_termer(slug, vl.UNDERLAG)
    if not f.get('ord') and not f.get('siffror'):
        hinder.append('kundvakten kan inte läsa kundens uppgifter (VERKSAMHET.json), så varje fråga till Refero och Mobbin skulle stoppas')
    radmap = {r['namn']: r for r in rader}
    for n in ('Refero (direkt)', 'Mobbin (sökning och bilder)', 'kundvaktens mekanik'):
        res = (radmap.get(n) or {}).get('resultat')
        if res == 'fel':
            hinder.append('%s fungerar inte' % n)
        elif res != 'ok':
            oklart.append('%s är inte bekräftad' % n)
    info = [befintligt_material(slug)]
    if (u / 'REFERENSER.md').is_file():
        info.append('REFERENSER.md finns från den äldre utforskningen: ett tidigare urval, inte researchens underlag')
    detalj = ('researchen har inte körts i den här körningen: FORSKNING.json, referenspaketet, TJANSTER.json och uppdragens material är '
              'planerade i researchen. Förutsättningarna: %s. %s' % (
                  '; '.join(hinder + oklart) if hinder or oklart else 'underlaget, kundvakten och tjänsterna är bekräftade', '; '.join(info)))
    return post('uppdrag', 'referensunderlaget', 'fel' if hinder else 'planerat', tillstand='blockerat' if hinder else 'planerat', detalj=detalj)


def efter_research(slug):
    """Kandidatflödet efter researchen: det faktiska underlaget och om det går att använda. FORSKNING.json (körningens
    egen, inte en tidigare; researchens fel och släppta frågor), referenspaketet (PAKET.json och PAKET.md, sparade
    bilder), tjänsternas rapport (TJANSTER.json och TJANSTER.md: anrop, bilder på disken, tomma tjänster och träffar
    utan bild) och uppdragens material (UPPDRAGSMATERIAL.json, efter planen). Det som körningen hämtade står som använt
    med resultat. Det som återanvändes ur en tidigare research står som tillgängligt med sin tid. Misslyckade anrop,
    tomma resultat, uteblivna bilder och en tilldelad tjänst som researchen aldrig frågade står som blockerade eller
    misslyckade, aldrig som använda (ägarens uppdrag 2026-10-07, punkt 2 och 3; granskningen GR-20261007-r102, B1)."""
    import kompetens
    u = vl.UNDERLAG / slug
    a = u / 'atelje'
    st = vl.las_json(a / 'STATUS.json', {}) or {}
    f = vl.las_json(a / 'FORSKNING.json', None)
    if not isinstance(f, dict):
        return post('uppdrag', 'referensunderlaget', 'fel', tillstand='blockerat',
                    detalj='FORSKNING.json går inte att läsa: researchens resultat saknas, och skaparnas uppdrag pekar på det')
    fel, brister, anvant, ateranvant, planerat, info = [], [], [], [], [], []
    material = False  # material till skaparna ur researchen, nytt eller återanvänt: sparade bilder eller belagda stilar
    tider = st.get('tider') if isinstance(st, dict) else None
    start = str(tider.get('start') or '') if isinstance(tider, dict) else ''
    if not start:
        info.append('körningens starttid saknas i STATUS.json, så att FORSKNING.json är körningens egen är inte prövat')
    elif str(f.get('tid') or '') < start:
        fel.append('inaktuell: FORSKNING.json (%s) är äldre än körningens start (%s) och gäller en tidigare körning' % (f.get('tid'), start))
    if f.get('fel'):
        fel.append('researchen föll: %s' % vl.sista(f['fel'], 160))
    if not (a / 'FORSKNING.md').is_file():
        fel.append('FORSKNING.md saknas, fast skaparnas uppdrag pekar på den')
    if f.get('slappta'):
        brister.append('%d sajter eller frågor släpptes utanför kanalens form' % len(f['slappta']))
    nytt, fore = (f.get(x) if isinstance(f.get(x), dict) else {} for x in ('nytt', 'fore'))
    paket = nytt.get('paket') or fore.get('paket')
    pk = vl.las_json(u / 'referenser' / str(paket) / 'PAKET.json', None) if re.fullmatch(r'paket-v\d{2,}', str(paket or '')) else None
    if paket and not isinstance(pk, dict):
        fel.append('referenspaketet %s saknar PAKET.json' % vl.sista(paket, 40))
    elif paket:
        pdir = u / 'referenser' / str(paket)
        k_ = [x for x in pk.get('kandidater') or [] if isinstance(x, dict)]
        ok_, med_bilder, borta = sum(1 for x in k_ if x.get('ok')), 0, 0
        for x in k_:  # sajtens sparade bilder (PAKET.json, relativa paketet): materialet, också när fångsten hade brister
            bilder = [str(b) for s in x.get('sidor') or [] if isinstance(s, dict) for b in s.get('filer') or [] if str(b).endswith('.png')]
            finns = sum(1 for b in bilder if (pdir / b).is_file())
            med_bilder, borta = med_bilder + (1 if finns else 0), borta + len(bilder) - finns
        text = 'referenspaketet %s med sparade bilder från %d av %d sajter, %d fångade utan brister' % (paket, med_bilder, len(k_), ok_)
        if not med_bilder:
            fel.append(text + ': inga sparade bilder')
        elif nytt.get('paket'):
            anvant.append(text + ' (%d nya sajter i körningen)' % len(nytt.get('sajter') or []))
        else:
            ateranvant.append(text + ' (återanvänt ur en tidigare research, %s)' % (pk.get('tid') or 'tiden ej angiven'))
        material = material or med_bilder > 0
        if ok_ < len(k_):
            brister.append('%d sajter i %s har brister (blockerade eller felande resurser, PAKET.md)' % (len(k_) - ok_, paket))
        if borta:
            fel.append('%d sparade bilder i %s saknas på disken' % (borta, paket))
        if not (pdir / 'PAKET.md').is_file():
            fel.append('PAKET.md saknas i %s, fast skaparnas uppdrag pekar på den' % paket)
    else:
        info.append('inget referenspaket')
    tjd = u / 'referenser' / 'tjanster'
    tjanster = {}
    if nytt.get('tjanster') or fore.get('tjanster'):
        tj = vl.las_json(tjd / 'TJANSTER.json', None)
        if not isinstance(tj, dict):
            fel.append('TJANSTER.json saknas eller går inte att läsa')
        else:
            aterbruk = not nytt.get('tjanster')  # tjänsternas rapport ur en tidigare research: den här körningen anropade inget
            if tj.get('torr'):
                fel.append('TJANSTER.json är en torrkörning utan riktiga anrop')
            if not (tjd / 'TJANSTER.md').is_file():
                fel.append('TJANSTER.md saknas, fast skaparnas uppdrag pekar på den')
            tjanster = tj.get('tjanster') if isinstance(tj.get('tjanster'), dict) else {}
            for t, x in sorted(tjanster.items()):
                if not isinstance(x, dict):
                    continue
                namn = TJNAMN.get(t, t)
                anrop = sum(int(v or 0) for v in x['anrop'].values()) if isinstance(x.get('anrop'), dict) else 0
                traffar = [y for y in x.get('traffar') or [] if isinstance(y, dict)]
                stilar = [y for y in x.get('stilar') or [] if isinstance(y, dict)]
                utan = sum(1 for y in traffar if not y.get('fil'))
                filer = [y['fil'] for y in traffar + stilar if y.get('fil')]
                finns = sum(1 for b in filer if bildfil(slug, b).is_file())
                belagda = sum(1 for y in stilar if y.get('belagd'))
                if not anrop:
                    fel.append('%s: inga verkliga anrop i sessionsloggen (tom tjänst)' % namn)
                elif not x.get('ok'):
                    fel.append('%s: %d anrop men inget användbart material (%s)' % (namn, anrop, vl.sista('; '.join(map(str, x.get('anmarkningar') or [])), 160) or 'inga bilder'))
                elif not finns and not belagda:
                    fel.append('%s: %d anrop, men tjänstens bilder saknas på disken och inga stilar är belagda' % (namn, anrop))
                else:
                    material = True
                    text = '%s med %d anrop, %d bilder på disken%s' % (namn, anrop, finns, (' och %d belagda stilar' % belagda) if belagda else '')
                    (ateranvant if aterbruk else anvant).append(text + (' (tjänsternas rapport %s, återanvänd)' % (tj.get('tid') or 'utan tid') if aterbruk else ''))
                if utan:
                    brister.append('%s: %d träffar utan bild räknas inte som material' % (namn, utan))
                if len(filer) > finns:
                    fel.append('%s: %d bilder saknas på disken' % (namn, len(filer) - finns))
    roller = kompetens.tolka()
    for t in NODVANDIGA_MCP:  # en tilldelad tjänst som researchen aldrig frågade: båda ska ingå i referensarbetet (punkt 2)
        if t not in tjanster:
            tilld = sorted(x['id'] for x in roller.values() if t in x['mcp'])
            brister.append('researchen frågade aldrig %s, så skaparna får inga förlagor ur %s från researchen, fast metodkartan '
                           'tilldelar %s rollerna %s' % (TJNAMN[t], TJNAMN[t], TJNAMN[t], ', '.join(tilld) or '–'))
    um = vl.las_json(a / 'UPPDRAGSMATERIAL.json', None)
    if isinstance(um, dict):
        kand = {k_: v for k_, v in (um.get('kandidater') or {}).items() if isinstance(v, dict)} if isinstance(um.get('kandidater'), dict) else {}
        stil = {k_ for k_, v in kand.items() if (v.get('stil') or {}).get('id') and not (v.get('stil') or {}).get('fel')}
        mob = {k_: [m for m in v.get('mobbin') or [] if isinstance(m, dict) and m.get('fil')] for k_, v in kand.items()}
        mob_finns = {k_: [m for m in ms if bildfil(slug, m['fil']).is_file()] for k_, ms in mob.items()}
        skarmar = sum(len(ms) for ms in mob_finns.values())
        borta = sum(len(ms) for ms in mob.values()) - skarmar
        if stil or skarmar:
            anvant.append('uppdragens material: stilpaket till %d av %d uppdrag och %d Mobbin-skärmar på disken' % (len(stil), len(kand), skarmar))
        else:
            brister.append('uppdragens material är tomt: inget stilpaket och inga Mobbin-skärmar till %d uppdrag' % len(kand))
        utan_material = sorted(k_ for k_ in kand if k_ not in stil and not mob_finns.get(k_))
        if utan_material and (stil or skarmar):
            brister.append('uppdrag utan eget material (varken stilpaket eller Mobbin-skärmar): %s' % ', '.join(utan_material))
        stilfel = sorted(k_ for k_, v in kand.items() if (v.get('stil') or {}).get('fel'))
        mobfel = sorted(k_ for k_, v in kand.items() if v.get('mobbin_fel'))
        if stilfel:
            brister.append('stilpaketet kunde inte hämtas för %s' % ', '.join(stilfel))
        if mobfel:
            brister.append('Mobbin gav inga skärmar för %s' % ', '.join(mobfel))
        if borta:
            fel.append('%d av uppdragens Mobbin-skärmar saknas på disken' % borta)
        if isinstance(um.get('mobbin'), dict) and um['mobbin'].get('fel'):
            fel.append('Mobbins session för uppdragen föll: %s' % vl.sista(um['mobbin']['fel'], 120))
    else:
        planerat.append('uppdragens material (stilpaketen och Mobbins skärmar) hämtas efter planen')
    if not material:
        fel.append('researchen gav inget användbart material: inga sparade bilder i ett referenspaket och inga tjänstesvar med bilder, '
                   'varken nya eller återanvända')
    delar = ['researchen gjord %s (FORSKNING.json)' % f.get('tid')]
    if anvant:
        delar.append('använt med resultat: ' + '; '.join(anvant))
    if ateranvant:
        delar.append('tillgängligt, återanvänt: ' + '; '.join(ateranvant))
    if fel or brister:
        delar.append('blockerat eller misslyckat: ' + '; '.join(fel + brister))
    if planerat:
        delar.append('planerat i ett senare steg: ' + '; '.join(planerat))
    if info:
        delar.append('; '.join(info))
    if (u / 'REFERENSER.md').is_file():
        delar.append('REFERENSER.md (ett tidigare urval) räknas inte')
    return post('uppdrag', 'referensunderlaget', 'fel' if fel else 'delvis' if brister else 'ok',
                tillstand='blockerat' if fel else 'anvant' if anvant else 'tillgangligt' if ateranvant else 'blockerat',
                detalj='. '.join(delar))


def referensfilen(slug):
    """Den äldre utforskningen: huvudreferenskandidaterna i REFERENSER.md med läsbara Bildval-bilder, eller ett
    referenspaket att välja ur (atelje.krav_referenser). En fil utan kandidater (tom) eller med kandidater vars bilder
    saknas (inaktuell) godtas inte; kontrollen skapar aldrig filen."""
    import referensval
    import skapande
    f = vl.UNDERLAG / slug / 'REFERENSER.md'
    paket = skapande.senaste_paket(slug, vl.UNDERLAG)
    reserv = ('; utforskningen väljer ur referenspaketet %s' % paket.name) if paket else ''
    if not f.is_file():
        if paket:
            return post('uppdrag', 'referensunderlaget', 'ok', tillstand='tillgangligt', detalj='REFERENSER.md saknas' + reserv)
        return post('uppdrag', 'referensunderlaget', 'fel', tillstand='blockerat',
                    detalj='REFERENSER.md saknas och inget referenspaket finns: den äldre utforskningen kräver huvudreferenskandidater med '
                           'Bildval-bilder i REFERENSER.md eller ett referenspaket (kontroller/referens.py)')
    kand = referensval.kandidater(slug, vl.UNDERLAG)
    if not kand:
        text = 'REFERENSER.md saknar raderna "Huvudreferenskandidat: <referens> — <vad den bär>" och godtas inte (tom)'
        return post('uppdrag', 'referensunderlaget', 'ok' if paket else 'fel', tillstand='tillgangligt' if paket else 'blockerat',
                    detalj=text + (reserv or ', och inget referenspaket finns'))
    trasiga = [k_['namn'] for k_ in kand if not k_['bilder']]
    if trasiga:
        return post('uppdrag', 'referensunderlaget', 'fel', tillstand='blockerat',
                    detalj='REFERENSER.md godtas inte (inaktuell): huvudreferenskandidaterna %s har inga läsbara Bildval-bilder under sin '
                           'rubrik, och utforskningen stannar på dem (atelje.krav_referenser)' % ', '.join(trasiga))
    felrader = referensval.felrader(slug, vl.UNDERLAG)
    detalj = 'REFERENSER.md: %d huvudreferenskandidater med %d läsbara Bildval-bilder' % (len(kand), sum(len(k_['bilder']) for k_ in kand))
    if felrader:
        return post('uppdrag', 'referensunderlaget', 'delvis', tillstand='tillgangligt',
                    detalj=detalj + '; inaktuella Bildval-rader (bilden saknas): ' + '; '.join(x.split(' (')[0] for x in felrader[:4]))
    return post('uppdrag', 'referensunderlaget', 'ok', tillstand='tillgangligt', detalj=detalj)


def vinnarens_referens(slug, vad):
    """Helbygget och den äldre putsningen: VINNARE.json med huvudreferensen och dess bilder (granskaren och byggaren
    jämför mot dem), och för helbygget ägarens godkännande (skapande.godkand_giltig)."""
    import referensval
    import skapande
    v = vl.las_json(vl.UNDERLAG / slug / 'atelje' / 'VINNARE.json', None)
    if not isinstance(v, dict):
        if vad == 'helbygget' and os.environ.get('NWP_ATELJE', 'pa') != 'pa':
            return post('uppdrag', 'referensunderlaget', 'ej_tillampligt', tillstand='ej_observerat',
                        detalj='nödvägen utan ateljé (NWP_ATELJE=av): ingen godkänd startsida och ingen huvudreferens ur '
                               'VINNARE.json att pröva; byggaren skriver KONCEPT.md')
        return post('uppdrag', 'referensunderlaget', 'fel', tillstand='blockerat',
                    detalj='VINNARE.json saknas: %s har ingen vald startsida med huvudreferens' % vad)
    h = referensval.huvudreferens(slug, vl.UNDERLAG)
    delar = ['VINNARE.json: %s' % ('kandidat %s' % v['kandidat'] if v.get('kandidat') else 'riktning %s' % v.get('riktning'))]
    if vad == 'helbygget':
        ok_, skal = skapande.godkand_giltig(slug, vl.UNDERLAG)
        delar.append('godkänd för helbygget' if ok_ else 'inte godkänd: %s' % skal)
    if not h:
        return post('uppdrag', 'referensunderlaget', 'fel', tillstand='blockerat', detalj='; '.join(delar + ['huvudreferensen saknas']))
    if not h.get('bilder'):
        return post('uppdrag', 'referensunderlaget', 'fel', tillstand='blockerat',
                    detalj='; '.join(delar + ['huvudreferensen %s har inga läsbara bilder att jämföra mot' % h.get('namn')]))
    return post('uppdrag', 'referensunderlaget', 'ok', tillstand='tillgangligt',
                detalj='; '.join(delar + ['huvudreferensen %s med %d bilder' % (h.get('namn'), len(h['bilder']))]))


def referensunderlag(slug, vag, rader):
    """Referensunderlaget efter körväg och fas (ägarens uppdrag 2026-10-07, punkt 3B: kontrollen såg bara REFERENSER.md,
    och den kördes före researchen). Kontrollen skapar aldrig REFERENSER.md och skriver inget i underlaget."""
    if not slug:
        return []
    if vag['id'] == 'kandidatflodet':
        r = fore_research(slug, rader) if vag['fas'] == 'fore_research' else efter_research(slug)
    elif vag['id'] == 'aldre':
        r = vinnarens_referens(slug, 'putsningen') if vag['fas'] == 'efter_val' else referensfilen(slug)
    elif vag['id'] == 'helbygget':
        r = vinnarens_referens(slug, 'helbygget')
    elif vag['id'] == 'ingen':
        r = post('uppdrag', 'referensunderlaget', 'ej_tillampligt', tillstand='ej_observerat', detalj='%s: underlaget prövas inte' % vag.get('namn'))
    else:
        r = post('uppdrag', 'referensunderlaget', 'okand', tillstand='ej_observerat', detalj='inte prövat: %s' % vag.get('namn'))
    r['fas'] = vag.get('fas_namn')
    return [r]


def skyddat(namn, f, *a):
    """En del av kvittot som kastar blir en rad om att delen inte kunde prövas, aldrig ett avbrott: en oväntad form i
    underlaget eller i metodkartan får inte stoppa starten (stoppen gäller verktyg som inte fungerar)."""
    try:
        return f(*a)
    except Exception as e:  # noqa: BLE001
        return [post('startkontroll', namn, 'okand', tillstand='ej_observerat', detalj='kunde inte prövas: %s: %s' % (type(e).__name__, vl.sista(e, 160)))]


# --- diskvakten (städregeln, punkt 6) ---

def diskvakt(k, ram=None, fick=True, slug=None, start=None):
    """Punkt 6 i städregeln (BESLUT.md, tillägget 2026-10-06): under 15 % ledigt körs städningen (kontroller/stadning.py)
    före starten, och kvittot redovisar ledigt utrymme före och efter. Den hoppas över medan ett intag, ett underhåll
    eller en annan körning pågår (fick False: intagslåset var fortfarande taget; granskningen av r94, Ö4), och
    redovisningen skrivs också i underhållets rapport (Ö6). Städningen stoppar aldrig starten: ett fel blir en rad som
    behöver uppmärksamhet, aldrig ett stopp. NWP_STADNING=av (rökprovet) stänger av städningen mot det verkliga systemet;
    ram är ett provs egen omvärld. Ger (raden, posten till kvittot)."""
    import stadning
    d = {'grans': DISKVAKT}
    try:
        total, ledigt = ram.disk() if ram else stadning.disk_matt(vl.ROOT)
        d['fore'] = stadning.disk_post(total, ledigt)
    except Exception as e:  # noqa: BLE001 — diskvakten stoppar aldrig starten
        d['fel'] = 'diskens lediga utrymme kunde inte mätas: %s' % vl.sista(e, 160)
        return post('underhåll', 'diskvakten', 'okand', detalj=diskvakt_text(d)), d
    if d['fore']['andel_ledig'] is not None and d['fore']['andel_ledig'] >= DISKVAKT:
        return post('underhåll', 'diskvakten', 'ok', detalj=diskvakt_text(d)), d
    if ram is None and stadning.avslagen():
        d['avslagen'] = True
        return post('underhåll', 'diskvakten', 'okand', detalj=diskvakt_text(d)), d
    try:
        hinder = 'ett intag i underhållet pågår fortfarande' if not fick else (ram.upptagen() if ram else stadning.upptaget())
    except Exception as e:  # noqa: BLE001 — går det inte att se vad som pågår städas inget
        hinder = 'det går inte att se vad som pågår (%s: %s)' % (type(e).__name__, vl.sista(e, 120))
    if hinder:
        d['hoppad'] = hinder
        return post('underhåll', 'diskvakten', 'okand', detalj=diskvakt_text(d)), d
    try:
        ram = ram or stadning.Ram.verklig()
        rap = stadning.stada(ram)
    except Exception as e:  # noqa: BLE001
        d['fel'] = 'städningen föll: %s: %s' % (type(e).__name__, vl.sista(e, 200))
        return post('underhåll', 'diskvakten', 'okand', detalj=diskvakt_text(d)), d
    d['stadning'], d['efter'] = rap, rap.get('disk_efter')
    if ram.tillstand and not rap.get('besked'):  # i underhållets rapport (Ö6); utanför huvudutcheckningen städades inget
        import underhall as uh_
        fel = uh_.skriv_stadning(ram.tillstand, rap, 'diskvakten före en start: %s%s' % (start or '?', (', ' + slug) if slug else ''))
        if fel:
            d['rapportfel'] = fel
    nog = (d['efter'] or {}).get('andel_ledig') is not None and d['efter']['andel_ledig'] >= DISKVAKT
    return post('underhåll', 'diskvakten', 'ok' if nog and not (rap.get('antal') or {}).get('fel') else 'okand',
                detalj=diskvakt_text(d)), d


def diskvakt_text(d):
    """Diskvaktens rad i kvittot: ledigt före och, när städningen kördes, efter. En städning som bara redovisade (körd
    utanför huvudutcheckningen, i torrläget eller medan en annan städning pågick) heter inte "kördes" (omgranskningen av
    r94, K-f)."""
    import stadning
    if not d:
        return None
    if not d.get('fore'):
        return d.get('fel') or 'okänt'
    fore, grans = stadning.disk_text(d['fore']), '%d %%' % round(d['grans'] * 100)
    if d.get('stadning'):
        st_ = d['stadning']
        vad = ('städningen redovisade bara, inget städades (%s)' % st_['besked']) if st_.get('besked') else \
            'städningen redovisade bara (torrläge)' if st_.get('torr') else 'städningen kördes'
        return '%s före starten, under %s: %s, %s efter (%s)' % (
            fore, grans, vad, stadning.disk_text(d.get('efter')), stadning.antal_text(st_.get('antal') or {}))
    if d.get('avslagen'):
        return '%s, under %s, men städningen är avslagen (NWP_STADNING=av)' % (fore, grans)
    if d.get('hoppad'):
        return '%s, under %s, men städningen hoppades över: %s' % (fore, grans, d['hoppad'])
    if d.get('fel'):
        return '%s, under %s: %s' % (fore, grans, d['fel'])
    return '%s; över %s, ingen städning före starten' % (fore, grans)


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
    for r in rader:  # en tilldelad tjänst som ateljéns session inte når (ägarens uppdrag 2026-10-07, punkt 3)
        if r['grupp'] == 'åtkomst' and r['resultat'] == 'fel':
            ut.append('%s: tilldelad men åtkomst saknas.' % r['namn'])
    for r in rader:
        if r['grupp'] == 'uppdrag' and r.get('formaga') in ('delvis', 'nej'):
            ut.append('Kundens behov "%s": flödet klarar det %s: %s.' % (r['namn'], 'delvis' if r['formaga'] == 'delvis' else 'inte', r['detalj']))
    return ut[:6]


def senaste_kvitto(rot, namn):
    """Den senaste läsbara starten av slaget namn ur historiken (startkvitton/, en kopia per start), utom stoppade, eller
    {}. Går den senaste inte att läsa väljs den närmast före (granskningen av r79, G)."""
    m_ = [(m.group(1), f) for f in (Path(rot) / 'startkvitton').glob(namn + '-2*.json')
          for m in [re.fullmatch(re.escape(namn) + r'-(\d{4}-\d\d-\d\dT\d{6}Z)\.json', f.name)] if m]
    for _t, f in sorted(m_, reverse=True):
        kv = vl.las_json(f, {}) or {}
        if kv and isinstance(kv, dict):  # granskningen av r80, L4
            return kv
    return {}


# --- repots identitet och dokumentationen (README.md, Var information finns) ---

def repo_identitet(rot=None):
    """Vilken version av repot starten gällde: commit och gren ur git rev-parse, och antalet ocommittade filer (ospårade
    med) ur git status --porcelain. Saknas git, eller är katalogen inget repo, står det "ej angivet". git status körs
    utan valfria lås: kontrollen skriver inte om indexet och krockar inte med en samtidig commit (granskningen av r97,
    KAN 1)."""
    rot = Path(rot or vl.ROOT)
    env = {k: v for k, v in vl.miljo().items() if k not in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')}  # repot är rot

    def git(*a):
        rc, ut = vl.kor(['git', '-C', str(rot), *a], timeout=60, env=env, bara_ut=True)
        return ut.strip() if rc == 0 else None

    commit = git('rev-parse', '--verify', 'HEAD')
    if not commit or not re.fullmatch(r'[0-9a-f]{40}(?:[0-9a-f]{24})?', commit):
        return {'commit': EJ_ANGIVET, 'gren': EJ_ANGIVET, 'ocommittade': EJ_ANGIVET}
    gren = git('rev-parse', '--abbrev-ref', 'HEAD') or EJ_ANGIVET
    status = git('--no-optional-locks', 'status', '--porcelain', '--untracked-files=all')
    return {'commit': commit, 'gren': 'ingen (fristående HEAD)' if gren == 'HEAD' else gren,
            'ocommittade': EJ_ANGIVET if status is None else sum(1 for r in status.splitlines() if r.strip())}


def repo_text(r):
    r = r if isinstance(r, dict) else {}
    return 'commit %s, gren %s, ocommittade filer: %s%s' % (r.get('commit', EJ_ANGIVET), r.get('gren', EJ_ANGIVET), r.get('ocommittade', EJ_ANGIVET),
                                                          (' (ej kontrollerad: %s)' % r['fel']) if r.get('fel') else '')


def informationen(f, vid_fel):
    """Kvittots information om repot och dokumentationen stoppar aldrig en start: ett undantag blir "ej kontrollerad"
    med felet, och statusen och stoppen ändras inte (granskningen av r97, B1)."""
    try:
        return f()
    except Exception as e:  # noqa: BLE001 — informationen stoppar aldrig en start
        return vid_fel('%s: %s' % (type(e).__name__, vl.sista(e, 160)))


def platsregeln(readme):
    """Står rubriken för platsregeln i README.md utanför kodblock (granskningen av r97, KAN 8)."""
    staket = None
    for r in readme.splitlines():
        s = r.strip()
        if staket:
            staket = None if s.startswith(staket) else staket
        elif s.startswith(('```', '~~~')) and len(r) - len(r.lstrip(' ')) <= 3:
            staket = s[:3]
        elif r.rstrip() == PLATSREGEL:
            return True
    return False


def forteckningsrad(rot, rad):
    """En rad i förteckningen: ok, saknas, fel_sha eller ej_kontrollerade. En rad som inte går att tolka, en sökväg utanför
    underlag/ och en fil som inte går att nå (för lång sökväg, en katalog utan läsrätt) är ej kontrollerade, och inget
    undantag lämnar funktionen (granskningen av r97, B1)."""
    try:
        x = json.loads(rad)
        rel, sha = x['fil'], x['sha256']
    except (ValueError, KeyError, TypeError):
        return 'ej_kontrollerade'
    if not (isinstance(rel, str) and isinstance(sha, str) and rel and not Path(rel).is_absolute() and '..' not in Path(rel).parts):
        return 'ej_kontrollerade'
    p = rot / 'underlag' / rel
    try:
        if not p.is_file():
            return 'saknas'
        h = vl.sha(p.read_bytes())
    except (OSError, ValueError):
        return 'ej_kontrollerade'
    return 'ok' if h == sha.strip().lower() else 'fel_sha'


def dokumentationen(rot=None):
    """Informationsraden om dokumentationen: finns platsregeln i README.md, och stämmer den privata förteckningen över
    sparade granskningar (FORTECKNING.jsonl, en JSON-rad per fil med fil och sha256) mot filerna: antal poster, och hur
    många vars fil saknas eller har en annan sha256. En rad som inte går att kontrollera räknas för sig. Stoppar aldrig
    en start och ändrar inte statusen."""
    rot = Path(rot or vl.ROOT)
    try:
        readme = (rot / 'README.md').read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        readme = ''
    d = {'platsregel': platsregeln(readme), 'forteckning': None}
    fil = rot / FORTECKNING
    try:
        if not fil.is_file():
            return d
        rader = fil.read_text(encoding='utf-8').split('\n')
    except (OSError, UnicodeDecodeError) as e:  # också en katalog utan läsrätt (granskningen av r97, B1)
        d['forteckning'] = {'fel': '%s: %s' % (type(e).__name__, vl.sista(e, 120))}
        return d
    f = d['forteckning'] = {'poster': 0, 'saknas': 0, 'fel_sha': 0, 'ej_kontrollerade': 0}
    for rad in rader:
        if rad.strip():
            f['poster'] += 1
            utfall = forteckningsrad(rot, rad)
            if utfall != 'ok':
                f[utfall] += 1
    return d


def dokumentation_text(d):
    if not isinstance(d, dict):
        return EJ_ANGIVET
    if d.get('fel'):  # dokumentationen() föll: raden är information och stoppar aldrig en start (granskningen av r97, B1)
        return 'ej kontrollerad: %s' % d['fel']
    ut = ['platsregeln finns i README.md (Var information finns)' if d.get('platsregel') else
          'platsregeln saknas i README.md (avsnittet Var information finns)']
    f = d.get('forteckning')
    if not f:
        ut.append('ingen privat förteckning över sparade granskningar (underlag/granskningar/FORTECKNING.jsonl)')
    elif f.get('fel'):
        ut.append('förteckningen över sparade granskningar kunde inte läsas (%s)' % f['fel'])
    else:
        ej = f.get('ej_kontrollerade') or 0
        ut.append('förteckningen över sparade granskningar: %d poster, %d filer saknas, %d med fel sha256%s' % (
            f.get('poster') or 0, f.get('saknas') or 0, f.get('fel_sha') or 0, ('; %d poster kunde inte kontrolleras' % ej) if ej else ''))
    return '; '.join(ut)


def markdown(kv):
    import kompetens
    T = kompetens.TILLSTAND
    rad = ['# Startkvitto · %s · %s' % (kv.get('slug') or '(ingen kund)', kv['tid']), '',
           '**Status: %s.** Start: %s. %s' % ({'redo': 'redo', 'begransad': 'redo med begränsningar', 'stoppad': 'STOPPAD'}[kv['status']], kv['start'],
                                              ('Stoppar: ' + '; '.join(kv['stoppar'])) if kv['stoppar'] else ''), '']
    if kv.get('korvag'):  # vilken körväg och fas kvittot gäller (ägarens uppdrag 2026-10-07, punkt 3)
        v = kv['korvag']
        rad += ['**Körväg:** %s%s. %s' % (v.get('namn'), (', ' + v['fas_namn']) if v.get('fas_namn') else '', FIGMA), '',
                'Tillståndsorden: %s; "%s" när observatören såg sessionen men ingen användning. Ett läskvitto är belägg för läsning, '
                'inte för tillämpning.' % (' · '.join(T[x] for x in ('tillgangligt', 'provat', 'tilldelat', 'anvant', 'planerat', 'blockerat', 'ej_observerat')),
                                          T['ej_gjort']), '']
    rad += ['Underhållet: %s.' % (kv.get('underhall') or 'har inte körts'), '']
    if kv.get('diskvakt'):  # städregeln, punkt 6: ledigt före och efter
        rad += ['Diskvakten: %s.' % diskvakt_text(kv['diskvakt']), '']
    import underhall as uh_  # Homebrews version före och efter brew update (ägarens beslut 2026-10-06, punkt 1)
    if uh_.homebrew_rad(kv.get('homebrew')):
        rad += [uh_.homebrew_rad(kv['homebrew']) + '.', '']
    rad += ['Repot: %s.' % repo_text(kv.get('repo')), '']
    if 'dokumentation' in kv:
        rad += ['Dokumentationen (information; stoppar aldrig en start): %s.' % dokumentation_text(kv['dokumentation']), '']
    if (kv.get('aterupptagen') or {}).get('utan_kvitto'):
        rad += ['Återupptagen körning som startades utan startkontroll: det fanns inget lås att ärva, så låset ovan gäller från nu.', '']
    elif kv.get('aterupptagen'):
        rad += ['Återupptagen körning: låset från start %s gäller. Ändrat sedan dess: %s.' % (
            kv['aterupptagen']['startad'], ', '.join(kv['aterupptagen']['andrat']) or 'inget'), '']
    if kv.get('matinstrument_bytta'):
        rad += ['**Mätinstrument bytta sedan förra starten:** ' + '; '.join('%s %s → %s (%s)' % (a['namn'], a.get('fran'), a.get('till'), a['tid'])
                                                                          for a in kv['matinstrument_bytta']) + '. Jämför körningar före och efter med det i minnet.', '']
    for rub, nycklar in GRUPPER:
        valda = [r for r in kv['rader'] if r['resultat'] in nycklar]
        if not valda:
            continue
        rad += ['## %s' % rub, '', '| Grupp | Vad | Resultat | Tillstånd | Installerat | Senaste | Kontrollerat eller provat | Detalj |',
                '|---|---|---|---|---|---|---|---|']
        for r in sorted(valda, key=lambda r: (nycklar.index(r['resultat']), r['grupp'])):
            rad.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
                r['grupp'], r['namn'], NAMN.get(r['resultat'], r['resultat']), T.get(r.get('tillstand'), '–') + (' (%s)' % r['fas'] if r.get('fas') else ''),
                r.get('installerat') or '–', r.get('senaste') or '–', r.get('provad') or r.get('kontrollerad') or '–', str(r.get('detalj') or '').replace('|', '/')))
        rad.append('')
    if 'roller' in kv:  # kvittot per roll: tilldelat och åtkomst i sessionen (ägarens uppdrag 2026-10-07, punkt 3)
        rad += ['## Kompetensen per roll', '']
        if kv.get('roller_fel'):
            rad.append('Kvittot per roll kunde inte göras: %s.' % kv['roller_fel'])
        elif kv['roller']:
            rad += ['Rollerna i kunskap/metodkarta.md (Kompetenserna): det tilldelade och vad ateljéns session når, prövat med flödets egna '
                    'argument. Startkontrollen observerar ingen användning.', '',
                    '| Roll | Pass | Tilldelat | Åtkomst i ateljéns session | Användning |', '|---|---|---|---|---|']
            rad += [roll_text(r) for r in kv['roller']]
        else:
            rad.append('Rollerna gäller skapandeflödets sessioner; %s har inga roller i metodkartan.' % ((kv.get('korvag') or {}).get('namn') or 'den här starten'))
        rad.append('')
    rad += ['## Till byggaren', ''] + (['- ' + x for x in kv['till_byggaren']] or ['Inget som rör uppdraget.'])
    if (kv.get('diskvakt') or {}).get('stadning'):  # städningen före starten, med redovisningen (punkt 7)
        import stadning
        rad += [''] + stadning.markdown(kv['diskvakt']['stadning'], '## Städningen före starten')
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
    disk_rad, disk = diskvakt(k, fick=fick, slug=slug, start=start)  # under 15 % ledigt städas det före starten; stoppar aldrig
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
    try:  # körvägen och fasen före proven: allt nedan gäller dem
        vag = korvag(slug, start)
    except Exception as e:  # noqa: BLE001 — en körväg som inte går att avgöra stoppar inte starten
        vag = {'id': 'okand', 'namn': 'körvägen kunde inte avgöras (%s: %s)' % (type(e).__name__, vl.sista(e, 120)), 'fas': None, 'fas_namn': None}
    ateljen = start != 'bygge'
    formaga, servrar, sess, upptackta = prova_formagan(k, version, start)
    rader += formaga
    rader += skyddat('åtkomsten i ateljéns session', atkomstrader, sess, ateljen)
    rader += skyddat('tjänsternas verktyg', tjanstverktyg_rader, upptackta)
    rader += kunskap(k)
    rader += regler(servrar, slug)
    rader += uppdraget(slug)
    rader += skyddat('referensunderlaget', referensunderlag, slug, vag, rader)
    rader.append(disk_rad)
    if not fick:  # verktygslådan byts just nu: en start på den skulle inte veta vilka versioner den kör med (fynd 2)
        rader.append(post('underhåll', 'intag', 'fel', nodvandig=True,
                          detalj='ett intag i underhållet pågick fortfarande efter %d minuter; starta igen när det är klart' % (vanta_intag // 60)))
    for r in rader:
        r.setdefault('resultat', 'okand')
    stoppar = ['%s: %s' % (r['namn'], r.get('detalj') or r['resultat']) for r in rader if r.get('nodvandig') and r['resultat'] == 'fel']
    begransad = any(r['resultat'] in BEGRANSAR for r in rader)
    modell_rader = [r for r in rader if r['grupp'] == 'modell']
    kv = {'schema': 3, 'slug': slug, 'tid': tid, 'start': start, 'status': 'stoppad' if stoppar else ('begransad' if begransad else 'redo'),
          'stoppar': stoppar, 'underhall': underhall, 'homebrew': u.get('homebrew'), 'utfort': sorted(set(k.utfort)), 'ateranvant': sorted(set(k.ateranvant)),
          'korvag': dict(vag, figma=FIGMA), 'rader': rader,
          'session': {x: sess.get(x) for x in ('resultat', 'detalj', 'tid', 'servrar', 'flaggor', 'ateranvant') if x in sess} if sess else None,
          'las': las_for_korning(rader, modell_rader), 'diskvakt': disk}
    try:  # kvittot per roll är en sammanställning: ett fel i den blir ett besked i kvittot, aldrig ett stopp
        kv['roller'] = roller(sess, rader, ateljen)
    except Exception as e:  # noqa: BLE001
        kv['roller'], kv['roller_fel'] = None, '%s: %s' % (type(e).__name__, vl.sista(e, 160))
    kv['till_byggaren'] = till_byggaren(rader)
    nu_m = matinstrument(rader)
    kv['matinstrument_sett'] = nu_m  # det som faktiskt fanns vid starten (låset kan vara en återupptagen körnings)
    # vilken version av repot starten gällde, och dokumentationen (README.md, Var information finns): information, inte
    # rader i kontrollen, så de ändrar varken status eller stopp, inte heller när de faller (granskningen av r97, B1)
    kv['repo'] = informationen(repo_identitet, lambda fel: {'commit': EJ_ANGIVET, 'gren': EJ_ANGIVET, 'ocommittade': EJ_ANGIVET, 'fel': fel})
    kv['dokumentation'] = informationen(dokumentationen, lambda fel: {'fel': fel})
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
            kv['las'] = tidigare['las']  # körningen behåller sitt lås (verktygen och låsfilerna, inte kundens underlag)
        elif start in ('fortsatt', 'valda', 'putsa'):  # körningen startades utan startkontroll: inget lås att ärva (r77, L12)
            kv['aterupptagen'] = {'startad': None, 'andrat': [], 'utan_kvitto': True}
        vl.skriv_json(rot / 'startkvitton' / ('%s-%s.json' % (filnamn, tid.replace(':', ''))), kv)
        vl.skriv_json(rot / (filnamn + '.json'), kv)
        (rot / (filnamn + '.md')).write_text(markdown(kv), encoding='utf-8')
        kv['kvitto'] = 'underlag/%s/atelje/%s.md' % (slug, filnamn)
    try:
        with open(k.katalog / 'startlogg.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({'tid': tid, 'slug': slug, 'start': start, 'status': kv['status'], 'stoppar': stoppar,
                                'commit': kv['repo']['commit']}, ensure_ascii=False) + '\n')
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
            'aterupptagen': kv.get('aterupptagen'), 'kvitto': kv.get('kvitto'), 'korvag': kv.get('korvag')}


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
