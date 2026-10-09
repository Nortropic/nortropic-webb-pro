#!/usr/bin/env python3
"""bevakning.py — Nortropics löpande bevakning, också mellan byggen (ägarens tillägg 2026-10-09 ~13:23Z om
kontinuerlig bevakning; BESLUT.md, samma tillägg; kunskap/spaning-kallor.md, Bevakningsfrågor).

Registret är bevakningsfrågorna i kunskap/spaning-kallor.md (blocken ```bevakning <id>```), bredvid spanarens
källtabell. Varje fråga knyter källor till ett område, ett steg, en kompetens, det den berör, en version, ett
intervall, en kontroll, en ansvarig och en eventuell backlogpost. Inget nytt källregister och ingen ny förbättringskö:

- spanaren (spana.py) hämtar källorna och skriver deras hälsa och version (kirurgen/spaning/HALSA.json) och
  kandidaterna per källa (KANDIDATER.json);
- underhållet (underhall.py) prövar verktygslådans versioner (underlag/startkontroll/UNDERHALL.json);
- den här kontrollen läser dem per fråga, kontrollerar att spanaren, underhållet och den själv har körts i tid, och
  för nya fynd vidare som signaler i förbättringsloopen (kirurg_loop.Loop, kirurgen/forbattringar), där de bedöms,
  prövas, införs och verifieras som förut;
- frågor som kräver omdöme (kontroll codex) prövas av Codex i en egen session med `codex --search exec` på
  bevakningspaketet (`codex-paket`), och svaret förs in med `codex-svar` som granskarförslag, aldrig som ägarens beslut.

Utfallet per fråga: inget_nytt (lyckad kontroll utan förändring), fynd, misslyckad (kontrollen gick inte att göra),
ofullstandig (en del av underlaget gick inte att pröva), ej_utford (kontrollen kräver något som inte gjorts, till
exempel Codex) eller inte_dags. "Inget handlingsbart i dag" står bara när kontrollerna lyckats.

Schemat: dashboardens timklocka (server.py, bevakning_vid_behov) kör den dagliga kontrollen en gång per dag efter
KLOCKSLAG Europe/Stockholm. Har datorn eller tjänsten varit avstängd blir det en körning vid nästa timslag, märkt med hur
sent den kom. Veckans och månadens frågor prövas i den dagliga körningen när deras intervall gått, räknat i lokala dagar,
så att en körning som kom sent inte flyttar nästa dags eller veckas prövning. Ett lås hindrar två
körningar samtidigt. Tidigare fynd känns igen på sitt fingeravtryck och rapporteras som kvarstående, inte som nya.

    .venv/bin/python kontroller/bevakning.py kor                 # den dagliga kontrollen nu (manuell)
    .venv/bin/python kontroller/bevakning.py lage                # läget som JSON, som dashboarden läser det
    .venv/bin/python kontroller/bevakning.py codex-paket <katalog>
    .venv/bin/python kontroller/bevakning.py codex-svar <fil>
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
HUVUD = (Path.home() / 'nortropic-repos' / 'nortropic-webb-pro').resolve()
REGISTER = ROOT / 'kunskap' / 'spaning-kallor.md'
TZ = ZoneInfo('Europe/Stockholm')
SCHEMA = 1
INTERVALL = {'dag': 1, 'vecka': 7, 'manad': 30}
KONTROLLER = ('kalla', 'underhall', 'codex', 'forbrukning', 'manuell', 'byggstart')
CODEX_TAK = int(os.environ.get('NWP_BEVAKNING_CODEX_FRIST') or 900)  # sekunder per Codex-granskning
KALLTYPER = {'standard': 'standard', 'regelverk': 'lag, myndighet och regelverk', 'kompatibilitet': 'kompatibilitetsdata (inte kvalitet)',
             'forskning': 'forskning', 'metod': 'etablerad metod', 'leverantor': 'leverantörsdokumentation', 'bransch': 'branscherfarenhet',
             'inspiration': 'inspiration', 'eget_beslut': 'Nortropics eget beslut'}
OMRADEN = {
    'kundintag': 'Kundintag, affärsmål, målgrupper och bransch',
    'ux': 'UX-forskning, informationsarkitektur, innehåll och konvertering',
    'gestaltning': 'Art direction, layout, typografi, färg och detalj',
    'material': 'Bild, video, ljud, rörelse och materialets uppgift',
    'referenser': 'Referensarbete, designverktyg och överföring till kod',
    'tillganglighet': 'Tillgänglighet, responsivitet och webbläsarstöd',
    'frontend': 'Frontend, komponenter, ramverk, prestanda och testning',
    'synlighet': 'SEO, strukturerad data, mätning och uppföljning',
    'juridik': 'Säkerhet, integritet, licenser och regelverk',
    'ai': 'AI-modeller, prompter, kontext, orkestrering, skills och MCP',
    'granskning': 'Granskning, kalibrering, evals, blindning och reproducerbarhet',
    'leverans': 'Kundrepo, förhandsvisning, driftsättning, överlämning och underhåll',
    'larande': 'Dokumentation, lärande, resursförbrukning, väntan och omarbete',
}
BLOCK = re.compile(r'^```bevakning (?P<id>[a-z0-9-]+)[ \t]*\n(?P<rader>.*?)\n```', re.S | re.M)


def kataloger():
    """Var bevakningen läser och skriver; miljön styr dem i en provinstans (kunskap/arbetsyta.md, Prov)."""
    m = os.environ.get
    return {'ut': Path(m('NWP_BEVAKNING_UT') or ROOT / 'kirurgen' / 'bevakning'),
            'spaning': Path(m('NWP_SPANING_KATALOG') or ROOT / 'kirurgen' / 'spaning'),
            'underhall': Path(m('NWP_UNDERHALL_KATALOG') or ROOT / 'underlag' / 'startkontroll'),
            'forbattringar': Path(m('NWP_FORBATTRINGAR') or ROOT / 'kirurgen' / 'forbattringar')}


def klockslag():
    h, _, mi = (os.environ.get('NWP_BEVAKNING_KLOCKSLAG') or '07:00').partition(':')
    return int(h), int(mi or 0)


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def tid(s):
    try:
        return datetime.strptime(str(s)[:20], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def dagar_sedan(nar, t):
    """Hela lokala dagar (Europe/Stockholm) från t till nar. Den dagliga körningen går en gång per lokal dag, så
    intervallen räknas i lokala dagar och inte i timmar: en körning som kom sent (19:04 i stället för 07:00 den
    2026-10-09) gör inte nästa dags frågor för tidiga."""
    return (nar.astimezone(TZ).date() - t.astimezone(TZ).date()).days


def nasta_for(q, post, nar=None):
    """När frågan prövas nästa gång: klockslaget den lokala dag dess intervall gått sedan den senast lyckade
    kontrollen, tidigast nästa schemalagda körning."""
    if q.get('intervall') == 'byggstart':
        return 'nästa byggstart'
    forst = nasta_korning(nar)
    sist = tid((post or {}).get('senast_lyckad'))
    if not sist or q.get('intervall') not in INTERVALL:
        return forst
    d = sist.astimezone(TZ).date() + timedelta(days=INTERVALL[q['intervall']])
    h, m = klockslag()
    return max(datetime(d.year, d.month, d.day, h, m, tzinfo=TZ).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), forst)


def las_json(p, standard=None):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return standard


def skriv_json(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name('.%s.%d.tmp' % (p.name, os.getpid()))
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


# --- registret ---

def register(text=None):
    """({id: fråga}, [fel]) ur blocken i källregistret. En fråga utan fråga, område, kontroll eller intervall, eller med
    ett okänt värde, står bland felen och prövas inte."""
    text = REGISTER.read_text(encoding='utf-8') if text is None else text
    import spana
    kallnamn = {k['namn'] for k in spana.las_kallor()}
    ut, fel = {}, []
    lista = lambda s, sep=';': [x.strip() for x in str(s or '').split(sep) if x.strip()]  # noqa: E731
    for m in BLOCK.finditer(text):
        f = {}
        for rad in m.group('rader').splitlines():
            k, _, v = rad.partition(':')
            f[k.strip()] = v.strip()
        q = {'id': m.group('id'), 'fraga': f.get('fråga', ''), 'omrade': f.get('område', ''), 'steg': f.get('steg', ''),
             'kompetens': lista(f.get('kompetens'), ','), 'beror': lista(f.get('berör')), 'kallor': lista(f.get('källor')),
             'kalltyp': f.get('källtyp', ''), 'version': f.get('version', ''), 'kontroll': lista(f.get('kontroll'), ','),
             'intervall': f.get('intervall', ''), 'ansvar': f.get('ansvar', ''), 'post': f.get('post') or None,
             'lucka': f.get('lucka') or None, 'nasta_atgard': f.get('nästa') or None, 'forutsattning': f.get('förutsättning') or None}
        problem = []
        if not q['fraga']:
            problem.append('frågan saknas')
        if q['omrade'] not in OMRADEN:
            problem.append('okänt område %r' % q['omrade'])
        if not q['kontroll'] or any(x not in KONTROLLER for x in q['kontroll']):
            problem.append('kontrollen ska vara %s' % ', '.join(KONTROLLER))
        if q['intervall'] not in INTERVALL and q['intervall'] != 'byggstart':
            problem.append('intervallet ska vara dag, vecka, manad eller byggstart')
        if q['lucka'] and not (q['post'] and q['nasta_atgard'] and q['forutsattning'] and q['ansvar']):
            problem.append('en lucka anger ansvar, post, nästa åtgärd och förutsättning')
        if q['kalltyp'] and q['kalltyp'] not in KALLTYPER:
            problem.append('okänd källtyp %r' % q['kalltyp'])
        okanda = [k for k in q['kallor'] if not k.startswith('http') and k not in kallnamn]
        if 'kalla' in q['kontroll'] and okanda:
            problem.append('källorna finns inte i källtabellen: %s' % ', '.join(okanda))
        if problem:
            fel.append({'id': q['id'], 'fel': problem})
        else:
            ut[q['id']] = q
    return ut, fel


# --- kontrollerna ---

def fingeravtryck(*delar):
    return hashlib.sha1(json.dumps(delar, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _kalla(q, k, fore, intervall_dagar):
    """Källorna i spanarens hälsa och kandidater: fel, ålder, ny version och nya poster sedan förra kontrollen. Kandidater
    räknas per källa oavsett poäng och status, så att en låg rankning inte döljer en förändring i en källa vi använder;
    spanarens tak (200 nya, 5 per källa) kan ändå hålla en post utanför listan."""
    import spana
    halsa = (las_json(k['spaning'] / 'HALSA.json', {}) or {}).get('kallor') or {}
    kand = las_json(k['spaning'] / 'KANDIDATER.json', []) or []
    rader = {r['namn']: r for r in spana.las_kallor()}
    fynd, problem, versioner, fallna = [], [], dict((fore or {}).get('versioner') or {}), set()
    sedan = (fore or {}).get('senast_lyckad')
    for namn in q['kallor']:
        r = rader.get(namn)
        h = halsa.get(r['id']) if r else None
        if not h:
            problem.append('%s: spanaren har inte hämtat källan än' % namn)
            fallna.add(namn)
            continue
        if h.get('status') != 'ok':
            problem.append('%s: senaste hämtningen föll (%s)' % (namn, str(h.get('fel'))[:120]))
            fallna.add(namn)
        lyckad = h.get('senast_lyckad')
        if not lyckad or time.time() - float(lyckad) > (intervall_dagar + 1) * 86400:
            problem.append('%s: ingen lyckad hämtning inom intervallet' % namn)
            fallna.add(namn)
        v = h.get('version')
        if v and versioner.get(namn) and v != versioner[namn]:
            fynd.append({'typ': 'kalla_andrad', 'text': '%s har ändrats sedan förra kontrollen' % namn,
                         'belagg': 'kirurgen/spaning/snapshot-%s.json (version %s)' % (r['id'], str(v)[:12]), 'nyckel': fingeravtryck(q['id'], namn, v)})
        if v:
            versioner[namn] = v
        nya = [x for x in kand if x.get('kalla') == namn and sedan and (x.get('hittad') or '') > sedan]
        for x in nya[:5]:
            fynd.append({'typ': 'ny_post', 'text': '%s: %s' % (namn, str(x.get('titel'))[:160]), 'belagg': str(x.get('url'))[:300],
                         'nyckel': fingeravtryck(q['id'], x.get('id'))})
    return fynd, problem, {'versioner': versioner, 'fallna_kallor': len(fallna)}


def _underhall(q, k, fore):
    """Underhållets senaste körning: i tid och klar, och för varje beroende frågan berör (namnen i berör utan sökväg):
    finns i underhållets inventering eller förmågeprov, och vad som hänt sedan förra kontrollen. Uppdaterat eller avvisat
    är fynd; fel, tillfälligt fel och ett förmågeprov som inte är ok är problem; ett beroende som saknas i underhållet är
    ett problem (ofullständig), aldrig "inget nytt"."""
    u = las_json(k['underhall'] / 'UNDERHALL.json', {}) or {}
    slut = tid(u.get('slut'))
    problem, fynd = [], []
    if not slut or u.get('status') != 'klart':
        problem.append('underhållet har ingen klar körning (%s)' % (u.get('status') or 'ingen rapport'))
    elif datetime.now(timezone.utc) - slut > timedelta(hours=36):
        problem.append('underhållets senaste körning är äldre än 36 timmar (%s)' % u.get('slut'))
    sedan = (fore or {}).get('senast_lyckad') or ''
    berorda = [b.lower() for b in q['beror'] if '/' not in b and not b.endswith(('.py', '.md', '.sh', '.mjs'))]
    inv = ['%s %s' % (x.get('namn') or '', x.get('id') or '') for x in u.get('inventering') or [] if isinstance(x, dict)]
    prov = {str(n): r for n, r in (u.get('prov') or {}).items() if isinstance(r, dict)}
    for b in berorda:
        rader = [r for r in u.get('rader') or [] if b in ('%s %s' % (r.get('namn') or '', r.get('id') or '')).lower()]
        provrader = {n: r for n, r in prov.items() if b in n.lower()}
        if not rader and not provrader and not any(b in x.lower() for x in inv):
            problem.append('%s finns inte i underhållets inventering eller förmågeprov' % b)
        for n, r in provrader.items():
            if r.get('resultat') != 'ok':
                problem.append('förmågeprovet %s: %s (%s)' % (n, r.get('resultat'), str(r.get('detalj'))[:120]))
        for r in rader:
            if r.get('resultat') == 'fel' or 'tillfälligt fel' in str(r.get('detalj') or ''):
                problem.append('%s: %s i underhållet (%s)' % (r.get('namn'), r.get('resultat'), str(r.get('detalj'))[:120]))
            elif slut and u.get('slut', '') > sedan and r.get('resultat') in ('uppdaterad', 'avvisad'):
                fynd.append({'typ': 'beroende_' + r['resultat'], 'text': '%s: %s %s → %s' % (r.get('namn'), r['resultat'], r.get('fran'), r.get('till')),
                             'belagg': 'underlag/startkontroll/UNDERHALL.md (%s)' % u.get('slut'), 'nyckel': fingeravtryck(q['id'], r.get('id'), r.get('till'), r['resultat'])})
    return fynd, problem, {}


def _svar(q, k, slag, intervall_dagar):
    """Ett registrerat svar (Codex granskning eller en manuell kontroll) inom intervallet, ur bevakningens katalog."""
    filer = sorted((k['ut'] / slag).glob('%s-*.json' % q['id'])) if (k['ut'] / slag).is_dir() else []
    sista = las_json(filer[-1], {}) if filer else None
    t = tid((sista or {}).get('tid'))
    if not t or datetime.now(timezone.utc) - t > timedelta(days=intervall_dagar + 1):
        return None, ['%s har inte gjorts inom intervallet' % ('Codex granskning' if slag == 'codex' else 'den manuella kontrollen')], {}
    if sista.get('fel'):  # granskningen kördes men föll: en misslyckad kontroll, aldrig "inget nytt"
        return [], ['Codex granskning föll %s: %s' % (sista.get('tid'), str(sista['fel'])[:200])], {'svar': str(filer[-1].name)}
    fynd = [{'typ': slag, 'text': str(f.get('text'))[:600], 'belagg': '; '.join(f.get('belagg') or [])[:600],
             'nyckel': fingeravtryck(q['id'], slag, f.get('text')), 'avsandare': sista.get('avsandare')} for f in sista.get('fynd') or []]
    return fynd, [], {'svar': str(filer[-1].name)}


def prova(q, k, fore, nar):
    """Utfallet för en fråga: (utfall, fynd, problem, extra)."""
    if q['intervall'] == 'byggstart':
        return 'inte_dags', [], ['prövas inför nästa byggstart'], {}
    dagar = INTERVALL[q['intervall']]
    sist = tid((fore or {}).get('senast_lyckad'))
    if sist and dagar_sedan(nar, sist) < dagar:
        return 'inte_dags', [], [], {}
    fynd, problem, extra, lagen = [], [], {}, []
    for kontroll in q['kontroll']:
        if kontroll == 'kalla':
            f, p, e = _kalla(q, k, fore, dagar)
            lagen.append('fel' if e.get('fallna_kallor', 0) >= len(q['kallor']) and not f else 'delvis' if p else 'ok')
            e = {x: v for x, v in e.items() if x != 'fallna_kallor'}
        elif kontroll == 'underhall':
            f, p, e = _underhall(q, k, fore)
            lagen.append('fel' if p else 'ok')
        elif kontroll in ('codex', 'manuell'):
            f, p, e = _svar(q, k, kontroll, dagar)
            lagen.append('ej' if f is None else 'fel' if p else 'ok')
            f = f or []
        elif kontroll == 'forbrukning':
            f, p, e = _forbrukning(q, k, nar)
            lagen.append('delvis' if p else 'ok')
        else:
            f, p, e = [], ['prövas inför nästa byggstart'], {}
            lagen.append('ej')
        fynd += f
        problem += p
        extra.update(e)
    # utfallet säger aldrig "inget nytt" när en hämtning föll, underlaget var ofullständigt eller analysen uteblev
    if all(x == 'ej' for x in lagen):
        return 'ej_utford', fynd, problem, extra
    if all(x in ('fel', 'ej') for x in lagen) and not fynd:
        return 'misslyckad', fynd, problem, extra
    if any(x != 'ok' for x in lagen):
        return ('fynd' if fynd else 'ofullstandig'), fynd, problem, extra
    return ('fynd' if fynd else 'inget_nytt'), fynd, problem, extra


def _forbrukning(q, k, nar, dagar=7):
    """Den uppmätta förbrukningen de senaste dagarna: motorns sessioner (svarsfilerna, Claude Codes listpris och tokens,
    costBasis list, aldrig fakturerat belopp) och bevakningens egna Codex-granskningar (tokens ur Codex utdata). Kvoten i
    abonnemangen exponeras inte och mäts inte; den står som saknat mätvärde, så kontrollen blir ofullständig, aldrig
    "inget nytt"."""
    grans = nar - timedelta(days=dagar)
    rot = Path(os.environ.get('NWP_FORBRUKNING_ROT') or ROOT / 'underlag')
    summa = {'sessioner': 0, 'listpris_usd': 0.0, 'turer': 0, 'sekunder': 0, 'tokens_ut': 0, 'per_modell': {}}
    for f in rot.glob('*/atelje/**/svar-*.json'):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) < grans:
                continue
            r = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not isinstance(r, dict) or 'total_cost_usd' not in r:
            summa['utan_kostnad'] = summa.get('utan_kostnad', 0) + 1
            continue
        summa['sessioner'] += 1
        summa['listpris_usd'] += float(r.get('total_cost_usd') or 0)
        summa['turer'] += int(r.get('num_turns') or 0)
        summa['sekunder'] += int((r.get('duration_ms') or 0) / 1000)
        for modell, m in (r.get('modelUsage') or {}).items():
            pm = summa['per_modell'].setdefault(modell, {'sessioner': 0, 'listpris_usd': 0.0, 'tokens_ut': 0})
            pm['sessioner'] += 1
            pm['listpris_usd'] += float(m.get('costUSD') or 0)
            pm['tokens_ut'] += int(m.get('outputTokens') or 0)
            summa['tokens_ut'] += int(m.get('outputTokens') or 0)
    codex = [x for x in (las_jsonl(k['ut'] / 'codex-korningar.jsonl')) if (tid(x.get('tid')) or grans) >= grans]
    summa['codex'] = {'granskningar': len(codex), 'tokens': sum(int(x.get('tokens') or 0) for x in codex),
                      'utan_tokenuppgift': sum(1 for x in codex if not x.get('tokens'))}
    summa['listpris_usd'] = round(summa['listpris_usd'], 2)
    text = ('%d dygn: %d motorsessioner, listpris %.2f USD (inte fakturerat), %d turer, %d min; Codex %d granskningar, %d tokens'
            % (dagar, summa['sessioner'], summa['listpris_usd'], summa['turer'], summa['sekunder'] // 60, summa['codex']['granskningar'], summa['codex']['tokens']))
    problem = ['abonnemangens kvot (Claude och ChatGPT) exponeras inte och mäts inte: förbrukningen ovan är listpris och tokens, inte kvot',
               'helbyggets körningar (kunder/<kund>/korningar), partnern och Claude Code utanför motorn räknas inte']
    if summa.get('utan_kostnad'):
        problem.append('%d svarsfiler utan kostnadsuppgift (tomma, blinda eller avbrutna) räknas inte' % summa['utan_kostnad'])
    if summa['codex']['utan_tokenuppgift']:
        problem.append('%d Codex-granskningar saknar tokenuppgift' % summa['codex']['utan_tokenuppgift'])
    fynd = [{'typ': 'forbrukning', 'text': text, 'belagg': 'underlag/*/atelje/**/svar-*.json; kirurgen/bevakning/codex-korningar.jsonl',
             'nyckel': fingeravtryck(q['id'], nar.astimezone(TZ).strftime('%G-%V'))}]  # en rapport per vecka, inte en ny varje dag
    return fynd, problem, {'forbrukning': summa}


def las_jsonl(p):
    try:
        return [json.loads(r) for r in Path(p).read_text(encoding='utf-8').splitlines() if r.strip()]
    except (OSError, ValueError):
        return []


def meta(k, nar):
    """Bevakningen av bevakningen: spanaren och underhållet i tid, källor som faller, och startkontrollens gräns mot det
    verkliga intervallet. Fynden här är Nortropics egna och går som de andra till förbättringsloopen."""
    ut = []
    sen = las_json(k['spaning'] / 'SENAST.json', {}) or {}
    dagar = float(os.environ.get('NWP_SPANING_INTERVALL_DAGAR') or 1)
    t = tid(sen.get('slut'))
    if not t:
        ut.append({'id': 'spanaren', 'utfall': 'misslyckad', 'text': 'spanaren har ingen körning', 'konsekvens': 'inga källor bevakas'})
    else:
        sen_h = (nar - t).total_seconds() / 3600
        fel = sen.get('fel') or []
        ok = sen_h <= dagar * 24 * 2
        rad = {'id': 'spanaren', 'utfall': 'fynd' if (fel or not ok) else 'inget_nytt', 'senast': sen.get('slut'),
               'text': ('senaste spaningen %s (%.0f h sedan)%s' % (sen.get('slut'), sen_h, '' if ok else ', äldre än två intervall'))
               + ('; %d av %d källor föll' % (len(fel), len(sen.get('kallor') or [])) if fel else ''),
               'konsekvens': 'källor som faller bevakas inte; de frågor som bygger på dem blir ofullständiga' if fel else None,
               'belagg': 'kirurgen/spaning/SENAST.json',
               'nyckel': fingeravtryck('spanaren', sorted((x.get('namn') if isinstance(x, dict) else str(x).split(':', 1)[0]) for x in fel), ok)}
        if fel:
            rad['fel'] = [('%s: %s' % (x.get('namn'), str(x.get('fel'))[:80])) if isinstance(x, dict) else str(x)[:120] for x in fel[:6]]
        ut.append(rad)
    u = las_json(k['underhall'] / 'UNDERHALL.json', {}) or {}
    tu = tid(u.get('slut'))
    ok_u = bool(tu) and (nar - tu) <= timedelta(hours=36) and u.get('status') == 'klart'
    ut.append({'id': 'underhallet', 'utfall': 'inget_nytt' if ok_u else 'fynd', 'senast': u.get('slut'),
               'text': 'underhållet %s: %s' % (u.get('slut') or 'aldrig', u.get('sammanfattning') or u.get('status') or 'ingen rapport'),
               'konsekvens': None if ok_u else 'verktygslådans versioner prövas inte; startkontrollen markerar det först efter 36 timmar',
               'belagg': 'underlag/startkontroll/UNDERHALL.md', 'nyckel': fingeravtryck('underhallet', ok_u)})
    try:
        import verktygslada
        grans = verktygslada.GILTIGHET.get('spaning') / 86400
        if grans > dagar * 2:
            ut.append({'id': 'startkontrollens-grans', 'utfall': 'fynd',
                       'text': 'startkontrollen godtar en spaning som är %.0f dygn gammal, men spanaren ska köra var %g dygn' % (grans, dagar),
                       'konsekvens': 'en stillastående spaning syns först efter en vecka', 'belagg': 'kontroller/verktygslada.py (GILTIGHET spaning)',
                       'nyckel': fingeravtryck('startkontrollens-grans', grans, dagar)})
    except Exception as e:  # noqa: BLE001 — en gräns som inte går att läsa är en ofullständig kontroll, inget fel i bevakningen
        ut.append({'id': 'startkontrollens-grans', 'utfall': 'ofullstandig', 'text': 'gränsen gick inte att läsa: %s' % str(e)[:120]})
    return ut


# --- körningen ---

@contextlib.contextmanager
def last(k):
    k['ut'].mkdir(parents=True, exist_ok=True)
    with open(k['ut'] / '.las', 'w') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def nasta_korning(nar=None):
    """Nästa schemalagda körning: KLOCKSLAG Europe/Stockholm i dag om den inte passerats, annars i morgon."""
    nar = (nar or datetime.now(timezone.utc)).astimezone(TZ)
    h, m = klockslag()
    t = nar.replace(hour=h, minute=m, second=0, microsecond=0)
    if nar >= t:
        t += timedelta(days=1)
    return t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def dags(k=None, nar=None):
    """Ska den dagliga kontrollen köras nu? Efter KLOCKSLAG lokal tid och ingen körning den lokala dagen (en körning som
    missats för att datorn eller tjänsten var avstängd tas vid nästa timslag)."""
    k = k or kataloger()
    nar = (nar or datetime.now(timezone.utc)).astimezone(TZ)
    h, m = klockslag()
    if nar < nar.replace(hour=h, minute=m, second=0, microsecond=0):
        return False
    s = tid(((las_json(k['ut'] / 'LAGE.json', {}) or {}).get('senast') or {}).get('start'))
    return not s or s.astimezone(TZ).date() < nar.date()


def kor(automatisk=False, k=None, nar=None):
    """Den dagliga kontrollen: varje fråga som är dags, metakontrollerna, fynden som signaler och dagens sammanfattning.
    Ger läget, eller {'hoppad': skäl} när en annan körning pågår."""
    k = k or kataloger()
    nar = nar or datetime.now(timezone.utc)
    with last(k) as fick:
        if not fick:
            return {'hoppad': 'en annan bevakningskörning pågår'}
        fore = las_json(k['ut'] / 'LAGE.json', {}) or {}
        start, t0 = nar.strftime('%Y-%m-%dT%H:%M:%SZ'), time.monotonic()
        fragor, regfel = register()
        lage_f = dict(fore.get('fragor') or {})
        kanda = dict(fore.get('kanda') or {})
        nya, kvar, rader = [], [], []
        for qid, q in fragor.items():
            f0 = lage_f.get(qid) or {}
            try:
                utfall, fynd, problem, extra = prova(q, k, f0, nar)
            except Exception as e:  # noqa: BLE001 — en fråga som inte går att pröva fäller inte de andra
                utfall, fynd, problem, extra = 'misslyckad', [], ['%s: %s' % (type(e).__name__, str(e)[:160])], {}
            post = dict(f0, id=qid, utfall=utfall if utfall != 'inte_dags' else f0.get('utfall', 'inte_dags'),
                        problem=problem[:8] if utfall != 'inte_dags' else (f0.get('problem') or problem[:8]),
                        senaste_forsok=start if utfall != 'inte_dags' else f0.get('senaste_forsok'))
            post.update(extra)
            if utfall in ('inget_nytt', 'fynd', 'ofullstandig'):
                post['senast_lyckad'] = start
            post['nasta'] = nasta_for(q, post, nar)
            for f in fynd:
                (kvar if f['nyckel'] in kanda else nya).append(dict(f, fraga=qid))
                kanda[f['nyckel']] = {'forst': (kanda.get(f['nyckel']) or {}).get('forst') or start, 'senast': start,
                                      'antal': int((kanda.get(f['nyckel']) or {}).get('antal') or 0) + 1, 'fraga': qid}
            lage_f[qid] = post
            rader.append(post)
        metarader = meta(k, nar)
        for r in metarader:
            if r['utfall'] == 'fynd' and r.get('nyckel'):
                (kvar if r['nyckel'] in kanda else nya).append({'typ': 'meta', 'fraga': r['id'], 'text': r['text'], 'belagg': r.get('belagg'),
                                                                'konsekvens': r.get('konsekvens'), 'nyckel': r['nyckel']})
                kanda[r['nyckel']] = {'forst': (kanda.get(r['nyckel']) or {}).get('forst') or start, 'senast': start,
                                      'antal': int((kanda.get(r['nyckel']) or {}).get('antal') or 0) + 1, 'fraga': r['id']}
        signaler = _till_loopen(nya, fragor, k)
        utfall = [r['utfall'] for r in rader] + [r['utfall'] for r in metarader]
        sen_h = None
        if automatisk:
            h, m = klockslag()
            lokal = nar.astimezone(TZ)
            sen_h = round((lokal - lokal.replace(hour=h, minute=m, second=0, microsecond=0)).total_seconds() / 3600, 1)
        slut = (nar + timedelta(seconds=time.monotonic() - t0)).strftime('%Y-%m-%dT%H:%M:%SZ')
        senast = {'start': start, 'slut': slut, 'automatisk': bool(automatisk), 'sen_timmar': sen_h,
                  'utfall': 'misslyckad' if regfel and not fragor else 'delvis' if any(x in ('misslyckad', 'ofullstandig', 'ej_utford') for x in utfall) or regfel else 'lyckad',
                  'nasta': nasta_korning(nar), 'tidszon': 'Europe/Stockholm', 'klockslag': '%02d:%02d' % klockslag()}
        lage = {'schema': SCHEMA, 'senast': senast, 'fragor': lage_f, 'meta': metarader, 'registerfel': regfel, 'kanda': kanda,
                'senast_lyckad': start if senast['utfall'] != 'misslyckad' else fore.get('senast_lyckad'), 'signaler': signaler}
        skriv_json(k['ut'] / 'LAGE.json', lage)
        dag = sammanfattning(lage, fragor, nya, kvar, nar)
        datum = nar.astimezone(TZ).strftime('%Y-%m-%d')
        skriv_json(k['ut'] / 'dag' / ('%s.json' % datum), dag)
        (k['ut'] / 'dag' / ('%s.md' % datum)).write_text(dag_md(dag), encoding='utf-8')
        with open(k['ut'] / 'logg.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({'tid': start, 'automatisk': bool(automatisk), 'utfall': senast['utfall'], 'nya': len(nya), 'kvar': len(kvar),
                                'sen_timmar': sen_h}, ensure_ascii=False) + '\n')
        return lage


def _till_loopen(nya, fragor, k):
    """Nya fynd blir signaler i förbättringsloopen: bevakad. Där bedöms, prövas, införs och verifieras de som förut."""
    if not nya:
        return []
    try:
        import kirurg_loop
        loop = kirurg_loop.Loop(k['forbattringar'])
    except Exception as e:  # noqa: BLE001
        return [{'fel': 'förbättringsloopen gick inte att öppna: %s' % str(e)[:160]}]
    ut = []
    for f in nya:
        q = fragor.get(f['fraga']) or {}
        fas = q.get('steg') if q.get('steg') in kirurg_loop.FASER else 'forvaltning'
        try:
            p = loop.signal('bevakning-' + f['fraga'], (q.get('fraga') or f.get('text') or f['fraga'])[:200], fas, 'bevakning:' + f['fraga'],
                            f['nyckel'], f.get('text') or '', f.get('belagg') or '')
            ut.append({'fynd': f['nyckel'], 'post': p.get('id')})
        except Exception as e:  # noqa: BLE001
            ut.append({'fynd': f['nyckel'], 'fel': str(e)[:160]})
    return ut


def tackning(fragor, lage_f):
    """Per område: frågorna, deras senaste utfall och de luckor registret själv anger (lucka: ...)."""
    ut = {}
    for oid, namn in OMRADEN.items():
        qs = [q for q in fragor.values() if q['omrade'] == oid]
        aktiva = qs  # också en fråga med lucka har sin kontroll; luckan redovisas för sig
        utfall = [(lage_f.get(q['id']) or {}).get('utfall') for q in aktiva]
        ut[oid] = {'namn': namn, 'fragor': len(aktiva), 'luckor': [q['lucka'] for q in qs if q.get('lucka')],
                   'lage': 'saknar_tackning' if not aktiva else 'inaktuell' if any(x in ('misslyckad', 'ej_utford', None) for x in utfall)
                   else 'ofullstandig' if 'ofullstandig' in utfall else 'bevakad'}
    return ut


def sammanfattning(lage, fragor, nya, kvar, nar):
    rader = lage['fragor']
    ej = [{'id': q, 'utfall': r['utfall'], 'problem': r.get('problem')} for q, r in rader.items()
          if r.get('utfall') in ('misslyckad', 'ofullstandig', 'ej_utford') or (r.get('problem') and r.get('utfall') == 'fynd')]
    meta_fel = [m for m in lage['meta'] if m['utfall'] in ('misslyckad', 'ofullstandig')]
    handlingsbart = [dict(f, fraga_text=(fragor.get(f['fraga']) or {}).get('fraga'), post=(fragor.get(f['fraga']) or {}).get('post')) for f in nya]
    lyckad = lage['senast']['utfall'] == 'lyckad'
    return {'datum': nar.astimezone(TZ).strftime('%Y-%m-%d'), 'senast': lage['senast'],
            'besked': ('inget handlingsbart i dag' if not handlingsbart and lyckad else
                       'inget nytt, men kontrollerna är inte hela' if not handlingsbart else '%d nya fynd' % len(handlingsbart)),
            'handlingsbart': handlingsbart, 'kvarstaende': len(kvar), 'kontroller_som_inte_lyckades': ej + [{'id': m['id'], 'utfall': m['utfall'], 'problem': [m['text']]} for m in meta_fel],
            'tackning': tackning(fragor, rader), 'registerfel': lage['registerfel'], 'signaler': lage['signaler'],
            'lankar': {'lage': 'kirurgen/bevakning/LAGE.json', 'register': 'kunskap/spaning-kallor.md#bevakningsfrågor',
                       'forbattringar': 'kirurgen/forbattringar/FORBATTRINGAR.json', 'spaning': 'kirurgen/spaning/SENAST.json',
                       'underhall': 'underlag/startkontroll/UNDERHALL.md'}}


def dag_md(d):
    r = ['# Bevakningen %s' % d['datum'], '',
         '**%s.** Körningen %s–%s (%s%s), utfall %s. Nästa: %s (Europe/Stockholm %s).' % (
             d['besked'][0].upper() + d['besked'][1:], d['senast']['start'], d['senast']['slut'], 'schemalagd' if d['senast']['automatisk'] else 'manuell',
             ', %.1f h efter klockslaget' % d['senast']['sen_timmar'] if d['senast'].get('sen_timmar') else '', d['senast']['utfall'], d['senast']['nasta'],
             d['senast']['klockslag']), '']
    if d['handlingsbart']:
        r += ['## Nya fynd', ''] + ['- **%s** (%s): %s. Belägg: %s.%s' % (f['fraga'], f['typ'], f['text'], f.get('belagg') or 'ej angivet',
                                                                       ' Post: %s.' % f['post'] if f.get('post') else '') for f in d['handlingsbart']] + ['']
    if d['kontroller_som_inte_lyckades']:
        r += ['## Kontroller som inte lyckades eller inte gjordes', ''] + ['- %s: %s (%s)' % (x['id'], x['utfall'], '; '.join(x.get('problem') or [])[:300])
                                                                          for x in d['kontroller_som_inte_lyckades']] + ['']
    r += ['## Täckning', ''] + ['- %s: %s (%d frågor)%s' % (t['namn'], t['lage'].replace('_', ' '), t['fragor'], '; lucka: ' + '; '.join(t['luckor']) if t['luckor'] else '')
                               for t in d['tackning'].values()] + ['']
    if d['kvarstaende']:
        r += ['%d tidigare fynd står kvar (rapporteras inte som nya).' % d['kvarstaende'], '']
    return '\n'.join(r)


def lage():
    """Läget för dashboarden: senaste körningen, nästa, frågorna med utfall, täckningen och dagens sammanfattning."""
    k = kataloger()
    d = las_json(k['ut'] / 'LAGE.json', {}) or {}
    fragor, regfel = register()
    datum = sorted((k['ut'] / 'dag').glob('*.json')) if (k['ut'] / 'dag').is_dir() else []
    dag = las_json(datum[-1], {}) if datum else None
    rader = d.get('fragor') or {}
    fb = las_json(k['forbattringar'] / 'FORBATTRINGAR.json', {}) or {}
    poster = [x for x in (fb.get('poster') or {}).values() if str(x.get('problem') or '').startswith('bevakning-')]
    forbattringar = {'bevakade': len(poster), 'bedomda': sum(1 for x in poster if x.get('diagnoser') or x.get('disposition') != 'oppen'),
                     'provade': sum(1 for x in poster if x.get('forsok')), 'inforda': sum(1 for x in poster if x.get('inforande') not in (None, 'inte_infort')),
                     'verifierade': sum(1 for x in poster if x.get('effekt') not in (None, 'inte_observerad')),
                     'register': 'kirurgen/forbattringar/FORBATTRINGAR.json'}
    beslut = [{'id': q['id'], 'fraga': q['fraga'], 'lucka': q.get('lucka'), 'ansvar': q.get('ansvar'), 'post': q.get('post'),
               'nasta_atgard': q.get('nasta_atgard'), 'forutsattning': q.get('forutsattning')} for q in fragor.values() if q.get('lucka')]
    codex = las_jsonl(k['ut'] / 'codex-korningar.jsonl')[-12:]
    forbrukning = next(((rader.get(q['id']) or {}).get('forbrukning') for q in fragor.values() if 'forbrukning' in q['kontroll']), None)
    return {'senast': d.get('senast'), 'nasta': nasta_korning(), 'tidszon': 'Europe/Stockholm', 'klockslag': '%02d:%02d' % klockslag(),
            'forbattringar': forbattringar, 'luckor': beslut, 'beslut': [x for x in beslut if 'ägaren' in (x.get('ansvar') or '')],
            'codex': {'aktiv': codex_pa(), 'korningar': codex, 'dags': codex_dags(k)},
            'forbrukning': forbrukning,
            'aktiv': bool(d.get('senast') and (d['senast'] or {}).get('automatisk')), 'meta': d.get('meta') or [],
            'fragor': [dict(q, **{x: (rader.get(qid) or {}).get(x) for x in ('utfall', 'senast_lyckad', 'problem')}, nasta=nasta_for(q, rader.get(qid)))
                       for qid, q in fragor.items()],
            'registerfel': regfel, 'tackning': tackning(fragor, rader), 'dag': dag}


# --- Codex ---

AGENTS = """# Bevakningen: Codex granskning

Du granskar Nortropics bevakningsfrågor i bevakning.json, var och en för sig, med webbsökning mot primärkällor.
Du läser bara; du ändrar inga filer. Svara med JSON enligt schema.json, en post per fråga du prövat:

- vad som har förändrats eller upptäckts, med källans URL, datum eller version och vad du faktiskt läst (ett
  sökresultat eller referat är inte ett läst original);
- vilket steg i Nortropic det berör (frågans steg och berör);
- vad som är observerat, vad källan stöder och vad som är din tolkning eller hypotes; motsägande belägg;
- nytta eller risk, minsta rimliga försök och hur vi avgör om det hjälper;
- nu, senare eller avfärda. "Inget relevant nytt" är ett giltigt svar när du faktiskt kontrollerat källan.

En fråga med lucka gäller något Nortropic saknar: undersök vad som krävs för att stänga luckan, vilket minsta försök som
ryms utan frågans förutsättning, och om förutsättningen fortfarande gäller.

Ditt svar är ett granskarförslag till ägaren och den ansvariga funktionen, aldrig ett ägarbeslut eller en ny regel.
Kundmaterial finns inte i paketet och ska inte sökas efter.
"""
SVAR_SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['fynd'], 'properties': {'fynd': {'type': 'array', 'items': {
    'type': 'object', 'additionalProperties': False,
    'required': ['fraga', 'forandring', 'steg', 'observerat', 'kallans_stod', 'tolkning', 'nytta_risk', 'minsta_forsok', 'hur_vi_vet', 'beslut', 'kallor'],
    'properties': {'fraga': {'type': 'string'}, 'forandring': {'type': 'string'}, 'steg': {'type': 'string'}, 'observerat': {'type': 'string'},
                   'kallans_stod': {'type': 'string'}, 'tolkning': {'type': 'string'}, 'nytta_risk': {'type': 'string'},
                   'minsta_forsok': {'type': 'string'}, 'hur_vi_vet': {'type': 'string'}, 'beslut': {'type': 'string', 'enum': ['nu', 'senare', 'avfarda', 'inget_nytt']},
                   'kallor': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['url', 'datum_eller_version', 'last'],
                                                         'properties': {'url': {'type': 'string'}, 'datum_eller_version': {'type': 'string'},
                                                                        'last': {'type': 'string', 'enum': ['originalet', 'utdrag', 'sokresultat']}}}}}}}}}


def codex_paket(katalog, bara=None):
    """Bevakningspaketet för Codex: frågorna som ska prövas (kontroll codex, eller de angivna), deras senaste läge,
    källtabellens rader de nämner, instruktionen och svarsschemat. Inget kundmaterial och inga nycklar."""
    import spana
    k = kataloger()
    fragor, _ = register()
    d = las_json(k['ut'] / 'LAGE.json', {}) or {}
    valda = [q for q in fragor.values() if (q['id'] in bara if bara else 'codex' in q['kontroll'])]
    rader = {r['namn']: r for r in spana.las_kallor()}
    kat = Path(katalog)
    kat.mkdir(parents=True, exist_ok=True)
    skriv_json(kat / 'bevakning.json', {'skapad': nu(), 'fragor': [dict(q, lage=(d.get('fragor') or {}).get(q['id']),
                                                                         kalltabell=[rader[n] for n in q['kallor'] if n in rader]) for q in valda]})
    (kat / 'AGENTS.md').write_text(AGENTS, encoding='utf-8')
    skriv_json(kat / 'schema.json', SVAR_SCHEMA)
    return {'katalog': str(kat), 'fragor': [q['id'] for q in valda]}


def codex_svar(fil, avsandare='codex', bara=None):
    """Codex svar in i bevakningen: en fil per fråga och granskning i kirurgen/bevakning/codex/ (som kontrollen codex
    läser), med alla poster för frågan samlade; bara ger bara den granskade frågans poster (en granskning skjuter aldrig
    upp en annan frågas). Fynden blir granskarförslag, aldrig ägarens beslut."""
    k = kataloger()
    svar = las_json(fil, {}) or {}
    fragor, _ = register()
    t, ut, perfraga = nu(), [], {}
    for f in svar.get('fynd') or []:
        qid = f.get('fraga')
        if bara and qid != bara:
            ut.append({'fraga': qid, 'fel': 'gäller inte den granskade frågan'})
            continue
        if qid not in fragor:
            ut.append({'fraga': qid, 'fel': 'okänd fråga'})
            continue
        perfraga.setdefault(qid, []).append(f)
    for qid, poster in perfraga.items():
        fynd, raa = [], []
        for f in poster:
            raa.append(f)
            if f.get('beslut') == 'inget_nytt':
                continue
            text = ('Granskarförslag från %s (inte ägarens beslut): %s. Steg: %s. Observerat: %s. Källans stöd: %s. Tolkning: %s. '
                    'Nytta eller risk: %s. Minsta försök: %s. Hur vi vet: %s. Besked: %s.' % (
                        avsandare, f.get('forandring'), f.get('steg'), f.get('observerat'), f.get('kallans_stod'), f.get('tolkning'),
                        f.get('nytta_risk'), f.get('minsta_forsok'), f.get('hur_vi_vet'), f.get('beslut')))
            fynd.append({'text': text, 'belagg': ['%s (%s; %s)' % (x.get('url'), x.get('datum_eller_version'), x.get('last')) for x in f.get('kallor') or []]})
        skriv_json(k['ut'] / 'codex' / ('%s-%s.json' % (qid, t.replace(':', ''))), {'tid': t, 'avsandare': {'typ': 'extern', 'namn': avsandare},
                                                                                 'fraga': qid, 'fynd': fynd, 'raa': raa})
        ut += [{'fraga': qid, 'beslut': f.get('beslut')} for f in poster]
    return ut


def codex_pa():
    """Automatisk Codex-granskning: på i huvudutcheckningen (ägarbeslutet 2026-10-09 ~14:25Z), av i en worktree, en
    provinstans eller en provkopia om inte NWP_BEVAKNING_CODEX=pa; NWP_BEVAKNING_CODEX=av stänger av den överallt."""
    v = os.environ.get('NWP_BEVAKNING_CODEX')
    return v == 'pa' if v else ROOT.resolve() == HUVUD


def codex_dags(k=None, nar=None):
    """Frågorna vars Codex-granskning är dags: kontrollen codex och ingen granskning (lyckad eller fallen) inom intervallet."""
    k = k or kataloger()
    nar = nar or datetime.now(timezone.utc)
    fragor, _ = register()
    ut = []
    for q in fragor.values():
        if 'codex' not in q['kontroll'] or q['intervall'] not in INTERVALL:
            continue
        filer = sorted((k['ut'] / 'codex').glob('%s-*.json' % q['id'])) if (k['ut'] / 'codex').is_dir() else []
        sista = (las_json(filer[-1], {}) or {}) if filer else {}
        t = tid(sista.get('tid'))
        vanta = 1 if sista.get('fel') else INTERVALL[q['intervall']]  # i lokala dagar; en fallen görs om nästa lokala dags körning
        if not t or dagar_sedan(nar, t) >= vanta:
            ut.append(q['id'])
    return ut


def _kor_codex(katalog, prompt, ut_fil, logg):
    """codex --search exec, skrivskyddat i paketets katalog, med svarsschemat. Ger (returkod, modell, tokens)."""
    import shutil
    import subprocess
    codex = shutil.which('codex')
    if not codex:
        raise FileNotFoundError('codex finns inte i PATH')
    import signal
    with open(logg, 'w', encoding='utf-8') as f:
        # egen processgrupp: codex är ett node-omslag som startar binären som barn; vid tidsgränsen avslutas hela gruppen
        pr = subprocess.Popen([codex, '--search', 'exec', '--ignore-user-config', '-s', 'read-only', '--skip-git-repo-check', '--ephemeral', '-C', str(katalog),
                               '--output-schema', str(Path(katalog) / 'schema.json'), '-o', str(ut_fil), prompt],
                              stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = pr.wait(timeout=CODEX_TAK)
        except subprocess.TimeoutExpired:
            for sig, vant in ((signal.SIGTERM, 10), (signal.SIGKILL, 10)):
                try:
                    os.killpg(pr.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    pr.wait(timeout=vant)
                    break
                except subprocess.TimeoutExpired:
                    continue
            raise TimeoutError('codex svarade inte inom %d s; processgruppen avslutades' % CODEX_TAK)
    text = Path(logg).read_text(encoding='utf-8', errors='replace')
    modell = next((r_.split(':', 1)[1].strip() for r_ in text.splitlines() if r_.startswith('model:')), None)
    rader = text.splitlines()
    tokens = None
    for i, r_ in enumerate(rader):
        if r_.strip() == 'tokens used' and i + 1 < len(rader):
            siffror = re.sub(r'\D', '', rader[i + 1])  # Codex skriver talet med hårt mellanslag (12\u00a0345)
            tokens = int(siffror) if siffror else None
    return rc, modell, tokens


def codex_vid_behov(k=None, nar=None, korare=None):
    """Den automatiska Codex-granskningen (ägarbeslutet 2026-10-09 ~14:25Z): varje fråga med kontrollen codex vars
    intervall gått prövas av Codex med webbsökning, en i taget, och svaret förs in som granskarförslag (codex_svar). En
    granskning som faller registreras som fallen, så att frågan blir misslyckad, aldrig "inget nytt". Varje körning
    loggas med tid, modell och de tokens Codex själv redovisar (codex-korningar.jsonl); kvoten mäts inte."""
    if not codex_pa():
        return []
    k = k or kataloger()
    nar = nar or datetime.now(timezone.utc)
    korare = korare or _kor_codex
    ut = []
    k['ut'].mkdir(parents=True, exist_ok=True)
    with open(k['ut'] / '.codex.las', 'w') as las:
        try:
            fcntl.flock(las, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return [{'hoppad': 'en annan Codex-granskning pågår'}]
        for qid in codex_dags(k, nar):
            t = nu()
            kat = k['ut'] / 'codex-paket' / ('%s-%s' % (qid, t.replace(':', '')))
            codex_paket(kat, [qid])
            svar, logg = kat / 'svar.json', kat / 'codex.log'
            prompt = ('Läs AGENTS.md och bevakning.json. Pröva frågan %s med webbsökning mot primärkällor; för en fråga med lucka: '
                      'undersök vad som krävs för att stänga luckan och vilket minsta försök som ryms. Svara enligt schemat; '
                      '"inget_nytt" bara när du faktiskt kontrollerat källorna.' % qid)
            t0 = time.monotonic()
            rad = {'tid': t, 'fraga': qid}
            try:
                rc, modell, tokens = korare(kat, prompt, svar, logg)
                rad.update(rc=rc, modell=modell, tokens=tokens, sekunder=round(time.monotonic() - t0))
                if rc or not svar.is_file():
                    raise RuntimeError('codex slutade med kod %s utan svar' % rc)
                importerade = codex_svar(svar, bara=qid)
                rad['beslut'] = [x.get('beslut') for x in importerade]
                if not any(x.get('fraga') == qid for x in importerade):
                    raise RuntimeError('svaret gällde inte frågan')
            except Exception as e:  # noqa: BLE001 — en fallen granskning registreras, och nästa fråga prövas
                rad['fel'] = '%s: %s' % (type(e).__name__, str(e)[:200])
                skriv_json(k['ut'] / 'codex' / ('%s-%s.json' % (qid, t.replace(':', ''))), {'tid': t, 'avsandare': {'typ': 'extern', 'namn': 'codex'},
                                                                                         'fraga': qid, 'fynd': [], 'fel': rad['fel']})
            with open(k['ut'] / 'codex-korningar.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(rad, ensure_ascii=False) + '\n')
            ut.append(rad)
    return ut


def byggstart(slug, k=None, nar=None):
    """Kontrollen inför byggstart (startkontrollen): bevakningens senaste körning, fynd som kommit sedan kundens förra
    start, kontroller som inte lyckats och luckorna, som en rad i startkvittot. Stoppar inget; den säger vad som är känt
    och vad som inte är kontrollerat. Registrerar frågan infor-byggstart som kontrollerad."""
    k = k or kataloger()
    nar = nar or datetime.now(timezone.utc)
    fragor, _ = register()
    forra = None
    try:
        forra = (las_json(ROOT / 'underlag' / slug / 'atelje' / 'STARTKVITTO.json', {}) or {}).get('tid')
    except Exception:  # noqa: BLE001
        forra = None
    luckor = [q['id'] for q in fragor.values() if q.get('lucka')]
    with last(k) as fick:
        d = las_json(k['ut'] / 'LAGE.json', {}) or {}  # i låset: en samtidig körning skrivs aldrig över med ett äldre läge
        s_ = d.get('senast') or {}
        nya = [x for x in (d.get('kanda') or {}).values() if (x.get('forst') or '') > (forra or '')]
        ej = [qid for qid, r in (d.get('fragor') or {}).items()
              if r.get('utfall') in ('misslyckad', 'ofullstandig', 'ej_utford') and (fragor.get(qid) or {}).get('intervall') != 'byggstart']
        t = tid(s_.get('start'))
        if not t:
            status, text = 'okand', 'bevakningen har inte körts'
        else:
            alder = (nar - t).total_seconds() / 3600
            status = 'ok' if alder <= 36 and s_.get('utfall') != 'misslyckad' else 'okand'
            text = 'senaste bevakningen %s (%.0f h sedan, %s, %s); %d fynd sedan kundens förra start; kontroller som inte lyckades: %s; luckor: %s' % (
                s_.get('start'), alder, 'schemalagd' if s_.get('automatisk') else 'manuell', s_.get('utfall'), len(nya), ', '.join(ej) or 'inga',
                ', '.join(luckor) or 'inga')
        if fick and d:
            r = (d.get('fragor') or {}).setdefault('infor-byggstart', {'id': 'infor-byggstart'})
            r.update(utfall='inget_nytt' if status == 'ok' and not ej else 'ofullstandig', senast_lyckad=nar.strftime('%Y-%m-%dT%H:%M:%SZ'),
                     problem=([] if status == 'ok' else [text])[:1] + (['kontroller som inte lyckades: ' + ', '.join(ej)] if ej else []), nasta='nästa byggstart',
                     kund=slug)
            skriv_json(k['ut'] / 'LAGE.json', d)
    return {'status': status, 'detalj': text, 'nya_fynd': len(nya), 'ej_lyckade': ej, 'luckor': luckor}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='kommando', required=True)
    sub.add_parser('kor')
    sub.add_parser('lage')
    sub.add_parser('register')
    c = sub.add_parser('codex-paket')
    c.add_argument('katalog')
    c.add_argument('--fraga', action='append')
    s = sub.add_parser('codex-svar')
    s.add_argument('fil')
    sub.add_parser('codex')
    b = sub.add_parser('byggstart')
    b.add_argument('slug')
    a = p.parse_args(argv)
    if a.kommando == 'kor':
        d = kor()
        print(json.dumps(d.get('senast') or d, ensure_ascii=False, indent=1))
    elif a.kommando == 'lage':
        print(json.dumps(lage(), ensure_ascii=False, indent=1))
    elif a.kommando == 'register':
        f, fel = register()
        print(json.dumps({'fragor': len(f), 'fel': fel}, ensure_ascii=False, indent=1))
        return 1 if fel else 0
    elif a.kommando == 'codex-paket':
        print(json.dumps(codex_paket(a.katalog, a.fraga), ensure_ascii=False))
    elif a.kommando == 'codex':
        print(json.dumps(codex_vid_behov(), ensure_ascii=False, indent=1))
    elif a.kommando == 'byggstart':
        print(json.dumps(byggstart(a.slug), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(codex_svar(a.fil), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
