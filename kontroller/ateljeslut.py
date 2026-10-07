#!/usr/bin/env python3
"""ateljeslut.py — skapandeflödets slutpost: ett beständigt, maskinläsbart slutbesked per ateljékörning (ägarens uppdrag
2026-10-07, punkt 4 och 6), i samma form som helbyggets slutpost (kontroller/korslut.py, vars fält och hjälpfunktioner
används här): rapporthuvudets fält (README.md, Var information finns), de fem tillstånden var för sig, slutkoden,
bristerna, nästa steg (atgarder) och länkarna (underlag).

    .venv/bin/python kontroller/ateljeslut.py <slug> [<körning>]     # posten, prövad mot domloggen nu

Posten ligger i kunder/<slug>/atelje/korningar/<körning>/SLUT.json, där körningen är arbetarens starttid i kor.sh:s form
(20261007T120000Z). kunder/<slug>/atelje/ arkiveras inte av en ny körning och tas inte bort av ett omtag. Bredvid posten
ligger körningens STATUS.json och REDOVISNING.md, så att nästa körning aldrig skriver över den förra körningens version.

Posten binder ihop uppdraget och körningen (läge, start, slut), kandidaterna med sina versioner (hash), repots commit,
METOD.json:s sha256 och stegens metodhashar, kandidatplanen, skisskritiken och vem som gjort den (aldrig dess innehåll:
blindningen före ägarens första beslut gäller också här), ägarens beslut med avsändaren (kontroller/skapande.py,
avsandare), domloggens oläsbara rader, stoppet eller felet och var i flödet det hände, tiden till första valbara skiss och
platsen för kompetenskedjan (kompetenskedjan: inte observerat).

Tre slag av poster:
- TYP: arbetaren skriver den i sin finally, vid normalt avslut, fel och stopp (kontroller/atelje.py, arbeta), och när
  startkontrollen stoppar starten. Den ersätter de tidigare posterna (rapportstatus ersatt, ersatt_av).
- TYP_STOPP: en start som stannade före körningen (prototyp.py:s stopp och ateljéns nekade starter): skälet och slutkod 2.
  Den ersätter ingen post.
- TYP_EFTERHAND: en körning som slutade utan slutpost (arbetaren dödades, eller körningen är från före slutposterna)
  skrivs i efterhand, ur dess STATUS.json, innan nästa start skriver över den. Posten säger att den är skriven i efterhand.

Slutkoderna (atelje.py och prototyp.py ger postens slutkod): 0 körningen är klar (klar för ägarens bedömning) · 2 ingen
körning startades (underlaget, läget eller domloggen stoppade starten) · 4 körningen föll, stoppades eller avbröts, eller
startkontrollen stoppade den · 6 ingen startsida att bygga vidare på (den äldre utforskningen). Slutkod 5 (väntan slut,
körningen pågår) har ingen post: arbetaren skriver den när körningen slutar.
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import korslut  # noqa: E402  rapporthuvudets fält, de fem tillstånden och hjälpfunktionerna (en form för alla slutposter)
import skapande  # noqa: E402  domloggen och avsändarna

EJ = korslut.EJ
SLUTPOST = korslut.SLUTPOST
TYP = 'slutpost (ateljén)'
TYP_STOPP = 'slutpost (skapandeflödet stannade före körningen)'
TYP_EFTERHAND = 'slutpost (ateljén, skriven i efterhand)'
UPPDRAG = 'skapandeflödet för startsidan (kunskap/skapandeflodet.md), startat med kontroller/prototyp.py eller kontroller/atelje.py'
MOMENT = {'forberedelse': 'kundunderlag före referensval och design', 'kandidatflodet': 'prototypen: research, plan och skisser (README.md, kedjan steg 2)',
          'forfining': 'förfiningen av de valda (README.md, kedjan steg 4)',
          'aldre': 'den äldre utforskningen med riktningar (nödvägen; kunskap/skapandeflodet.md)'}
KOMPETENSKEDJAN = 'inte observerat'  # kompetenskedjan per steg och kandidat fylls i av gren C2 (ägarens tillägg 2026-10-07)
KLARA = ('klar', 'klar_for_bedomning', 'forberedd')
SLUTKODER = {0: 'körningen är klar', 2: 'ingen körning startades', 4: 'körningen föll, stoppades eller avbröts',
             6: 'ingen startsida att bygga vidare på'}


def _atelje():
    import atelje  # sent: atelje importerar den här modulen
    return atelje


def stampel(tid):
    """Körningens identitet ur en tid (2026-10-07T12:00:00Z → 20261007T120000Z), samma form som kor.sh:s körningar."""
    m = re.fullmatch(r'(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z', str(tid or ''))
    return '%s%s%sT%s%s%sZ' % m.groups() if m else None


def katalog(slug):
    return _atelje().KUNDER / slug / 'atelje' / 'korningar'


def _rel(p):
    return _atelje().privat_rel(p)


def _relpost(slug, korning):
    return 'kunder/%s/atelje/korningar/%s/%s' % (slug, korning, SLUTPOST)


def ledig(slug, stamp):
    """Postens katalognamn: stämpeln, eller stämpeln med -2, -3 … när en post redan ligger där (två poster samma sekund)."""
    namn, i = stamp, 1
    while os.path.lexists(katalog(slug) / namn / SLUTPOST):
        i += 1
        namn = '%s-%d' % (stamp, i)
    return namn


def postkatalog(slug, korning):
    """kunder/<slug>/atelje/korningar/<körning>/, skapad och prövad: ingen symlänk på vägen och en giltig identitet."""
    if not korslut.KORNING_NAMN.fullmatch(str(korning or '')):
        raise ValueError('körningen %r är ingen giltig identitet' % (korning,))
    k = _atelje().KUNDER / slug
    if not k.is_dir():  # kundens katalog skapas av kontroller/ny_sajt.py; en ny post direkt under kunder/ är ett bygges gräns
        raise OSError('kunder/%s/ finns inte än (kontroller/ny_sajt.py skapar den); ingen slutpost skrivs' % slug)
    for d in (k, k / 'atelje', k / 'atelje' / 'korningar', k / 'atelje' / 'korningar' / korning):
        if d.is_symlink():
            raise OSError('%s är en symlänk; slutposten skrivs inte' % d)
    d = katalog(slug) / korning
    d.mkdir(parents=True, exist_ok=True)
    return d


def slutposter(slug):
    """Ateljékörningarnas slutposter för kunden, äldst först."""
    d = katalog(slug)
    if d.is_symlink() or not d.is_dir():
        return []
    return sorted((f for f in d.glob('*/' + SLUTPOST) if f.is_file() and not f.is_symlink() and not f.parent.is_symlink()),
                  key=lambda f: f.parent.name)


def _post_fil(slug, rel):
    """En posts fil ur dess relativa väg (kunder/<slug>/atelje/korningar/<körning>/SLUT.json), eller None."""
    m = re.fullmatch(r'kunder/([a-z0-9-]{2,60})/atelje/korningar/([0-9A-Za-z][0-9A-Za-z_-]{0,63})/SLUT\.json', str(rel or ''))
    if not m or m.group(1) != slug:
        return None
    f = katalog(slug) / m.group(2) / SLUTPOST
    return f if f.is_file() and not f.is_symlink() and not f.parent.is_symlink() else None


def post_for(slug, st):
    """(fil, post) för det läge STATUS.json beskriver, eller (None, None): en start som startkontrollen stoppade efter en
    körning (startkontroll_stopp, den senaste händelsen), annars körningens egen post (fältet slutpost), annars en post
    skriven i efterhand för körningen (samma starttid)."""
    st = st if isinstance(st, dict) else {}
    sks = st.get('startkontroll_stopp') if isinstance(st.get('startkontroll_stopp'), dict) else {}
    for rel in (sks.get('slutpost'), st.get('slutpost')):
        f = _post_fil(slug, rel)
        p = korslut.las(f) if f else None
        if isinstance(p, dict):
            return f, p
    if st.get('startad'):
        for f in reversed(slutposter(slug)):
            p = korslut.las(f)
            if isinstance(p, dict) and (p.get('korning') or {}).get('startad') == st['startad'] and p.get('typ') in (TYP, TYP_EFTERHAND):
                return f, p
    return None, None


# --- postens delar ---

def utfall(status):
    """(slag, slutkod, text): hur körningen slutade, ur statusen. slag är klar, forkastad, tillbaka, stoppad, fel,
    startkontrollen eller avbruten (körningen slutade mitt i ett steg utan avslut)."""
    steg = status.get('steg') or EJ
    av = status.get('avbrott') if isinstance(status.get('avbrott'), dict) else {}
    var = av.get('steg') or EJ
    if av.get('slag') == 'startkontrollen':
        return 'startkontrollen', 4, 'startkontrollen stoppade starten %s: %s' % (av.get('tid') or EJ, av.get('text') or status.get('fel') or EJ)
    if av.get('slag') == 'stopp':
        return 'stoppad', 4, 'stoppad i steg %s, %s: %s' % (var, av.get('tid') or EJ, av.get('text') or 'arbetaren stoppades')
    if av.get('slag') == 'avbruten':
        return 'avbruten', 4, 'avbruten i steg %s, %s: %s' % (var, av.get('tid') or EJ, av.get('text') or EJ)
    if av or steg == 'fel':
        return 'fel', 4, 'föll i steg %s, %s: %s' % (var, av.get('tid') or EJ, str(status.get('fel') or av.get('text') or EJ)[:400])
    if steg in KLARA:
        import kandidater
        kand = status.get('kandidater') if isinstance(status.get('kandidater'), dict) else None
        if kand is not None and not any(v in kandidater.VISBARA for v in kand.values()):  # också en tom kandidatlista (GR-20261007-r106#KAN-5)
            return 'klar', 6, 'klar, men ingen kandidat blev valbar (0 av %d): ägaren har inget att välja bland; %s' % (
                len(kand), status.get('skal') or 'en ny körning behövs')
        return 'klar', 0, (status.get('skal') or ('klar för ägarens bedömning' if steg == 'klar_for_bedomning' else 'klar för ägarens dom'))
    if steg == 'forkastad':
        return 'forkastad', 6, 'ateljén förkastade alla riktningar: %s' % (status.get('skal') or EJ)
    if steg == 'tillbaka':
        return 'tillbaka', 6, 'skaparen fann under förfiningen att grundidén inte bär, och omgångarna är slut: %s' % (status.get('skal') or EJ)
    return 'avbruten', 4, 'körningen slutade i steg %s utan avslut (arbetaren lever inte)' % steg


def fas(status):
    if status.get('fas') == 'forberedelse' or status.get('lage') == 'forbered' or status.get('forra_lage') == 'forbered':
        return 'forberedelse'
    if status.get('kandidatflode') and (status.get('lage') == 'valda' or status.get('forra_lage') == 'valda' or status.get('steg') == 'forfina'
                                        or status.get('fas') == 'forfining'):
        return 'forfining'
    return 'kandidatflodet' if status.get('kandidatflode') else 'aldre'


def kandidaterna(slug, status):
    """Kandidaterna med status, version och försök, och skisskritiken och vem som gjorde den (aldrig dess innehåll)."""
    import kandidater
    if not status.get('kandidatflode'):
        return []
    ids = kandidater.lista(slug)
    namn = kandidater.etiketter(slug, ids)
    ut = []
    for kid in ids:
        st = kandidater.las_status(slug, kid)
        ut.append({'id': kid, 'etikett': namn.get(kid), 'status': st.get('status'), 'statustext': kandidater.statustext(st), 'version': st.get('version'),
                   'forsok': st.get('forsok'), 'valbar': st.get('status') in kandidater.VISBARA, 'skal': str(st.get('skal') or '')[:300],
                   'avbruten_vid': st.get('avbruten_vid'), 'skisskritik': skisskritiken(slug, kid, st)})
    return ut


def skisskritiken(slug, kid, st):
    """Skisskritiken för kandidaten: gjord eller inte (och varför), vem som gjorde den (avsändartypen, rollen, modellen och
    sessionen), vilken version eller vilket varv den bedömde och om kandidaten ändrats efter bedömningen. Inget av
    granskarens omdöme: det visas för ägaren först efter första beslutet."""
    import kandidater
    a = _atelje()
    sk = st.get('skisskritik') if isinstance(st.get('skisskritik'), dict) else {}
    fil = kandidater.kdir(slug, kid) / 'SKISSKRITIK.json'
    so = (a.las_json(fil) or {}) if fil.is_file() and not fil.is_symlink() else {}
    if not sk and not so:
        return None
    sess = so.get('session') if isinstance(so.get('session'), dict) else sk.get('session') if isinstance(sk.get('session'), dict) else {}
    sid = sess.get('session_id')
    modell = None
    try:
        import observation
        modell = (a.las_json(observation.katalog(slug) / ('%s.json' % sid)) or {}).get('modell') if sid else None
    except Exception:  # noqa: BLE001 — modellen ur förteckningen är information
        modell = None
    version, varv = so.get('version'), so.get('varv')
    sista = (kandidater.varvnummer(slug, kid) or [None])[-1]
    andrad = (version != st.get('version')) if version and st.get('version') else (
        (sista > varv) if isinstance(varv, int) and isinstance(sista, int) else None)
    aktuell = kandidater.skisskritik_giltig(slug, kid, so)
    historisk = bool(so.get('rekommendation'))
    andrad = not aktuell if historisk else None
    gjord = aktuell
    return {'gjord': gjord, 'aktuell': aktuell, 'historiskt_gjord': historisk,
            'status': 'aktuell' if aktuell else 'historisk' if historisk else 'okand',
            'identitet': so.get('identitet'),
            'skal': None if aktuell else 'kritiken gäller ett annat försök, underlag eller bygge' if historisk else 'giltigt försöksbevis saknas',
            'tid': so.get('tid') or sk.get('tid'),
            'av': {'typ': 'granskare', 'avsandare': skapande.AVSANDARTYPER['granskare'][0], 'roll': 'den kritiska granskaren (skisskritiken)',
                   'modell': modell or ('%s (koden, inte observerad)' % kandidater.GRANSKARE_MODELL if sid else None), 'session_id': sid},
            'version': version, 'varv': varv, 'sista_varv': sista, 'andrad_efter_bedomningen': andrad,
            'fil': _rel(fil) if so else None}


def agarens_beslut(slug, status):
    """Domloggens rader som hör till körningen: den dom körningen följer (ägarens senaste beslut när den startade) och
    raderna efter starten, var och en med avsändaren (skapande.avsandare); och de oläsbara raderna."""
    lg = skapande.domlogg(slug, _atelje().UNDERLAG)
    start = str(status.get('startad') or '')

    def rad(r, p):
        return {'rad': r, 'tid': p.get('tid'), 'beslut': p.get('beslut'), 'kalla': p.get('kalla'),
                'avsandare': skapande.avsandare(p)['text'], 'agarens': skapande.ar_agarens(p)}
    foljer = next(((r, p) for r, _s, p in reversed(lg['domar']) if skapande.ar_agarens(p) and str(p.get('tid') or '') <= start), None) if start else None
    return {'fil': lg['fil'], 'foljer': rad(*foljer) if foljer else None,
            'efter': [rad(r, p) for r, _s, p in lg['domar'] if start and str(p.get('tid') or '') > start], 'olasbara': lg['olasbara'],
            'bilaga_olasbara': lg.get('bilaga_olasbara') or []}


# Vad ägarens beslut betyder för tillståndet "ägaren godkänner" (GR-20261007-r106#KAN-9): bara godkand är ett ja, bara
# forkasta och ny_riktning är ett nej; valj, jamfor och putsa är varken, så tillståndet är ej bedömt och texten säger vad
# beslutet betyder.
BESLUT_VARDE = {'godkand': True, 'forkasta': False, 'ny_riktning': False, 'valj': None, 'jamfor': None, 'putsa': None}
BESLUT_BETYDER = {'godkand': 'ägaren godkände startsidan för helbygget',
                  'forkasta': 'ägaren förkastade alla kandidater',
                  'ny_riktning': 'ägaren bad om en ny riktning (omtag)',
                  'valj': 'ägaren valde kandidater till förfining; godkännandet kommer efter förfiningen, inget nej',
                  'jamfor': 'ägaren sparade en jämförelse utan att välja eller godkänna',
                  'putsa': 'ägaren vill ha riktningen putsad; inget godkännande än, inget nej'}


def tillstanden(slug, status, slag, kand, beslut_):
    """De fem tillstånden var för sig (korslut.TILLSTAND), för ateljén."""
    ff = fas(status)
    normal = slag in ('klar', 'forkastad', 'tillbaka')
    sess = {'varde': normal, 'text': 'arbetaren avslutade körningen (%s)' % slag if normal else utfall(status)[2]}
    if kand:
        tekn = {'varde': None, 'text': 'skapandeflödet har ingen teknisk godkännandegrind; de snabba kontrollerna markerar brister '
                                       'per kandidat (%d valbara, %d ofullständiga eller fallna, %d avbrutna eller under arbete, %d inte påbörjade)' % (
                                           len([k for k in kand if k['valbar']]), len([k for k in kand if k['status'] in ('ofullstandig', 'fel')]),
                                           len([k for k in kand if k['status'] in ('avbruten', 'under_arbete')]), len([k for k in kand if k['status'] == 'planerad']))}
    else:
        tekn = {'varde': None, 'text': 'skapandeflödet har ingen teknisk godkännandegrind; provet körs i helbygget'}
    if ff == 'forberedelse':
        dg = {'varde': None, 'text': 'förberedelsen innehåller inget designförslag att bedöma'}
    elif ff == 'kandidatflodet':
        dg = {'varde': None, 'text': 'ingen designgranskare godkänner skisser före ägarens val; skisskritiken är rådgivande '
                                     '(%d av %d skisser granskade)' % (len([k for k in kand if (k.get('skisskritik') or {}).get('gjord')]), len(kand))}
    elif ff == 'forfining':
        dg = {'varde': None, 'text': 'ingen ny granskning efter förfiningen; ägaren bedömer de förfinade själv'}
    else:
        sd = (status.get('faser') or {}).get('slutdom') if isinstance(status.get('faser'), dict) else None
        dg = ({'varde': bool(sd.get('over_ribban')), 'text': 'panelens slutdom: håller %sribban (summa %s mot %s)' % (
            '' if sd.get('over_ribban') else 'inte ', (sd.get('poang') or {}).get('efter'), (sd.get('poang') or {}).get('fore'))}
              if isinstance(sd, dict) and 'over_ribban' in sd else
              {'varde': False, 'text': 'panelen förkastade alla riktningar'} if status.get('steg') == 'forkastad' else
              {'varde': None, 'text': 'ingen slutdom av panelen i körningen'})
    egna = [x for x in beslut_['efter'] if x['agarens']]
    andra = [x for x in beslut_['efter'] if not x['agarens']]
    if egna:
        d = egna[-1]
        ag = {'varde': BESLUT_VARDE.get(d['beslut']), 'tid': d['tid'], 'avsandare': d['avsandare'],
              'text': 'ägarens dom %s, beslut %s (rad %d; %s): %s' % (d['tid'], d['beslut'], d['rad'], d['avsandare'],
                                                                     BESLUT_BETYDER.get(d['beslut'], 'okänt beslut'))}
        oklara = [r for r in beslut_.get('olasbara', []) if r['rad'] > d['rad']]
        if oklara:
            ag['varde'] = None
            ag['text'] += '; senare rader är oläsbara: aktuellt ägarbeslut kan inte fastställas (%s)' % ', '.join(
                'rad %d' % r['rad'] for r in oklara)
    elif slag == 'klar' and kand and not any(k['valbar'] for k in kand):
        ag = {'varde': None, 'text': 'ingen kandidat blev valbar: ägaren har inget att bedöma, och en ny körning behövs'}
    else:
        ag = {'varde': None, 'text': 'väntar på ägarens bedömning i dashboardens vy Prototyp' if slag == 'klar' else 'ingen dom från ägaren efter körningen'}
    if ff == 'forberedelse':
        ag = {'varde': None, 'text': 'förberett underlag; inget designgodkännande begärs i detta steg'}
    if andra:
        ag['text'] += '; %d %s efter körningen är inte ägarens och räknas inte (%s)' % (
            len(andra), 'rad' if len(andra) == 1 else 'rader', '; '.join('rad %d: %s' % (x['rad'], x['avsandare']) for x in andra[:4]))
    lev = {'varde': False, 'text': 'skapandeflödet levererar ingen sajt: helbygget (./kor.sh) tar vid från en startsida som ägaren godkänt',
           'omfattning': 'kandidaterna i underlag/%s/atelje/, för ägarens val och godkännande (README.md, kedjan steg 2–5); leveransen är '
                         'helbyggets (steg 6–9)' % slug}
    return {'sessionen_avslutad': sess, 'tekniskt_godkant': tekn, 'designgranskaren_godkanner': dg, 'agaren_godkanner': ag, 'klart_for_leverans': lev}


def _sessionsbrister(slug, status):
    """Sessioner i körningen som saknar utfall i förteckningen (observation.py)."""
    try:
        import observation
        d = observation.katalog(slug)
    except Exception:  # noqa: BLE001
        return []
    a = _atelje()
    start = str(status.get('startad') or '')
    ut = []
    for f in sorted(d.glob('*.json')) if d.is_dir() and not d.is_symlink() else []:
        p = a.las_json(f) or {}
        if start and str(p.get('start') or '') >= start and not p.get('utfall'):
            ut.append('sessionen %s (%s%s) saknar utfall i förteckningen' % (str(p.get('session_id') or f.stem)[:8], p.get('roll') or EJ,
                                                                         ', %s' % p['kandidat'] if p.get('kandidat') else ''))
    return ut


def bygg(slug, status, korning, typ=TYP, efterhand=None):
    """Körningens slutpost ur statusen (i minnet: det arbetaren skriver som STATUS.json). efterhand: när posten skrivs i
    efterhand, och varför."""
    import kandidater
    a = _atelje()
    rot = a.UNDERLAG / slug / 'atelje'
    tid = korslut.nu()
    slag, slutkod, utfallstext = utfall(status)
    ff = fas(status)
    # startkontrollen stoppade starten innan något gjordes: kandidaterna på disk hör till den förra körningen
    kand = kandidaterna(slug, status) if slag != 'startkontrollen' else []
    beslut_ = agarens_beslut(slug, status)
    t = tillstanden(slug, status, slag, kand, beslut_)
    repo = korslut.repo_identitet()
    metodfil = rot / 'metod' / 'METOD.json'
    plan = (a.las_json(rot / 'KANDIDATPLAN.json') or {}) if status.get('kandidatflode') else {}
    tid_fv, kalla_fv = kandidater.forsta_valbara_tid(slug, status) if status.get('kandidatflode') and slag != 'startkontrollen' else (None, None)
    ident = ['repo nortropic-webb-pro commit %s%s' % (repo['commit'], ' (%d ändrade spårade filer)' % repo['andrade_filer'] if repo.get('andrade_filer') else '')
             if repo else 'repo: ' + EJ, 'körning %s (läge %s)' % (status.get('startad') or EJ, status.get('lage') or EJ),
             'METOD.json sha256 %s' % (korslut.sha_fil(metodfil) or EJ)]
    if isinstance(status.get('metod'), dict):
        ident += ['metod %s %s' % (s, korslut._kort(h)) for s, h in sorted(status['metod'].items())]
    if plan.get('tid'):
        ident.append('kandidatplan %s sha256 %s' % (plan['tid'], korslut._kort(korslut.sha_fil(rot / 'KANDIDATPLAN.json'))))
    ident += ['kandidat %s version %s (%s)' % (k['id'], k['version'] or EJ, k['statustext']) for k in kand if k['version'] or k['status'] != 'planerad']
    brister = [] if slag == 'klar' else [utfallstext]
    for k in kand:
        if k['status'] == 'avbruten' and k.get('avbruten_vid'):
            brister.append('%s (%s): %s; arbetet står kvar, och --fortsatt sparar försöket och gör om det' % (k['etikett'], k['id'], k['skal']))
        elif k['status'] == 'under_arbete':
            brister.append('%s (%s): under arbete när posten skrevs (%s)' % (k['etikett'], k['id'], k['skal']))
        elif k['status'] in ('ofullstandig', 'fel'):
            brister.append('%s (%s) %s: %s' % (k['etikett'], k['id'], k['statustext'], k['skal']))
    olas = skapande.olasbara_text(beslut_)
    if olas:
        brister.append(olas)
    brister += _sessionsbrister(slug, status)
    for falt in ('redovisning_fel', 'sparad_kod_fel'):
        if status.get(falt):
            brister.append('%s: %s' % (falt, status[falt]))
    if isinstance(status.get('forskning'), dict) and status['forskning'].get('fel'):
        brister.append('researchen: %s' % status['forskning']['fel'])
    if kalla_fv == kandidater.FRAMRAKNAD:
        brister.append('tiden till första valbara skiss är framräknad ur statusloggen (körningen satte den inte)')
    fortsatt = ['.venv/bin/python kontroller/atelje.py %s --fortsatt tar vid efter den senaste klara fasen; ett avbrutet försök sparas i '
                'forsok-<n>/ och görs om' % slug, 'eller en ny körning: .venv/bin/python kontroller/prototyp.py %s --om' % slug]
    ny = ['ägaren avgör nästa steg: en ny riktning (.venv/bin/python kontroller/prototyp.py %s --ny-riktning) eller nytt underlag' % slug]
    atgarder = {
        'klar': {'forberedelse': ['underlaget är förberett; nästa steg: .venv/bin/python kontroller/prototyp.py %s' % slug], 'kandidatflodet': ['ägaren jämför och väljer i dashboardens vy Prototyp; nästa steg startas med .venv/bin/python kontroller/prototyp.py %s' % slug],
                 'forfining': ['ägaren bedömer de förfinade i vyn Prototyp och godkänner en för helbygget; sedan ./kor.sh %s "<verksamhet>"' % slug],
                 'aldre': ['ägaren dömer startsidan i dashboardens vy Prototyp; panelens val och slutdom visas där efter domen']}[ff],
        'forkastad': ny, 'tillbaka': ny,
        'startkontrollen': ['rätta det startkontrollen stoppade på (%s) och starta igen med .venv/bin/python kontroller/prototyp.py %s' % (
            (status.get('startkontroll') or {}).get('kvitto') or 'underlag/%s/atelje/STARTKVITTO-STOPP.md' % slug, slug)],
    }.get(slag, fortsatt)
    underlag = []
    for namn in ('FORBEREDELSE.json', 'KANDIDATPLAN.json', 'FORSKNING.md', 'PLANPROVNING.md', 'STARTKVITTO.md', 'VAL.md', 'SLUTDOM.md', 'FORFINING.md'):
        if (rot / namn).is_file():
            underlag.append(_rel(rot / namn))
    for p in (metodfil, rot / 'sessioner', rot / 'kandidater', a.UNDERLAG / slug / skapande.DOMLOGG):
        if p.exists():
            underlag.append(_rel(p) + ('/' if p.is_dir() else ''))
    f_ = beslut_['foljer']
    beslut = ([('ägarens dom som körningen följer: %s, beslut %s (rad %d; %s)' % (f_['tid'], f_['beslut'], f_['rad'], f_['avsandare']))] if f_ else []) + [
        '%s %s, beslut %s (rad %d; %s)' % ('ägarens dom' if x['agarens'] else 'inte ägarens', x['tid'], x['beslut'], x['rad'], x['avsandare'])
        for x in beslut_['efter']]
    bedomning = {0: 'ej bedömt av ägaren (slutkod 0): %s' % utfallstext, 4: 'ofullständigt (slutkod 4): %s' % utfallstext,
                 6: ('underkänt av panelen (slutkod 6): %s' if slag == 'forkastad' else 'inget att bedöma (slutkod 6): %s' if slag == 'klar'
                     else 'ofullständigt (slutkod 6): %s') % utfallstext}[slutkod]
    post = {'schema': 1, 'id': 'SLUT-ATELJE-%s-%s' % (slug, korning),
            'titel': 'Slutbesked för skapandeflödet %s, körningen %s' % (slug, status.get('startad') or EJ),
            'typ': typ, 'uppdrag': '%s, läge %s' % (UPPDRAG, status.get('lage') or EJ), 'kund': slug, 'moment': MOMENT[ff],
            'forfattare': 'kontroller/ateljeslut.py (%s)' % ('skriven i efterhand av nästa start' if efterhand else 'arbetarens avslut, kontroller/atelje.py'),
            'datum': tid, 'granskad_identitet': ident, 'rapportstatus': 'färdig', 'bedomningsutfall': bedomning,
            'foregaende': EJ, 'ersatt_av': EJ, 'underlag': underlag, 'beslut': beslut or EJ, 'atgarder': atgarder,
            'korning': {'id': korning, 'startad': status.get('startad'),
                        'slutad': status.get('klar') or (status.get('avbrott') or {}).get('tid') or (None if efterhand else tid),
                        'lage': status.get('lage'), 'forra_lage': status.get('forra_lage'), 'fas': ff, 'steg': status.get('steg'),
                        'modell': status.get('modell'), 'effort': status.get('effort'), 'kandidatlage': status.get('kandidatlage')},
            'utfall': {'slag': slag, 'text': utfallstext, 'steg': (status.get('avbrott') or {}).get('steg') or status.get('steg'),
                       'tid': (status.get('avbrott') or {}).get('tid'), 'fel': status.get('fel')},
            'slutkod': slutkod, 'slutkod_text': 'Slutkod %d: %s; %s' % (slutkod, SLUTKODER[slutkod], utfallstext),
            'tillstand': t, 'kandidater': kand,
            'tider': dict(status.get('tider') or {}, forsta_valbara=tid_fv, forsta_valbara_kalla=kalla_fv) if status.get('kandidatflode') else None,
            'metod': {'repo': repo, 'metod_json': _rel(metodfil) if metodfil.is_file() else None, 'metod_json_sha256': korslut.sha_fil(metodfil),
                      'steg': status.get('metod') if isinstance(status.get('metod'), dict) else None},
            'kandidatplan': {'tid': plan.get('tid'), 'sha256': korslut.sha_fil(rot / 'KANDIDATPLAN.json'), 'lage': plan.get('lage')} if plan else None,
            'startkontroll': {k: status['startkontroll'].get(k) for k in ('status', 'kvitto', 'tid')} if isinstance(status.get('startkontroll'), dict) else None,
            'agarens_beslut': beslut_, 'kompetenskedjan': KOMPETENSKEDJAN, 'brister': brister}
    if efterhand:
        post['efterhand'] = efterhand
    if not status.get('kandidatflode') and status.get('val') is not None:
        post['vald_riktning'] = status.get('val')
    return post


def _kopiera(kalla, mal):
    """Filens byte till mal genom en tempfil och os.replace, som korslut._skriv_json: en länk som råkar ligga på målet följs
    aldrig (shutil.copyfile skriver genom den; GR-20261007-r106#KAN-8)."""
    mal = Path(mal)
    data = Path(kalla).read_bytes()
    fd, namn = tempfile.mkstemp(prefix='.ateljeslut-', suffix='.tmp', dir=mal.parent)
    tmp = Path(namn)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(tmp, mal)
    finally:
        tmp.unlink(missing_ok=True)


def skriv(slug, korning, post, ersatt=True, status=None, redovisning=None):
    """Postens katalog med STATUS.json (statusen som arbetaren skriver den), en kopia av REDOVISNING.md och SLUT.json, och
    de tidigare, ännu gällande posterna märkta ersatta (bara från en körningspost). Ger (fil, post). Ingen länk följs."""
    d = postkatalog(slug, korning)
    tidigare = [f for f in slutposter(slug) if f.parent != d]
    kopior = []
    if status is not None:
        korslut._skriv_json(d / 'STATUS.json', status)
        kopior.append(_rel(d / 'STATUS.json'))
    if redovisning is not None and Path(redovisning).is_file() and not Path(redovisning).is_symlink():
        _kopiera(redovisning, d / 'REDOVISNING.md')
        kopior.append(_rel(d / 'REDOVISNING.md'))
    if kopior:
        bas = post.get('underlag') if isinstance(post.get('underlag'), list) else []
        post['underlag'] = kopior + [u for u in bas if u not in kopior]
    if tidigare:
        p_ = korslut.las(tidigare[-1])
        post['foregaende'] = '%s (%s)' % ((p_ or {}).get('id') or tidigare[-1].parent.name, _rel(tidigare[-1]))
    post['slutpost'] = _relpost(slug, korning)
    korslut._skriv_json(d / SLUTPOST, post)
    if ersatt:
        for f in tidigare:
            p = korslut.las(f)
            if not isinstance(p, dict) or p.get('ersatt_av') not in (None, EJ):
                continue
            p.update(rapportstatus='ersatt', ersatt_av='%s (%s)' % (post['id'], post['slutpost']), ersatt_tid=post['datum'])
            korslut._skriv_json(f, p)
    return d / SLUTPOST, post


def skriv_korning(slug, status, ersatt=True):
    """Arbetarens slutpost (kontroller/atelje.py, arbeta): statusen får postens väg (fältet slutpost) innan posten byggs, och
    postens katalog får statusen och redovisningen som de är när körningen slutar. ersatt=False när posten inte ersätter
    den förra körningens (startkontrollens stopp: ingen körning gjordes). Ger (fil, post)."""
    korning = ledig(slug, stampel(status.get('startad')) or stampel(korslut.nu()))
    status['slutpost'] = _relpost(slug, korning)
    post = bygg(slug, status, korning)
    return skriv(slug, korning, post, ersatt=ersatt, status=status, redovisning=_atelje().UNDERLAG / slug / 'atelje' / 'REDOVISNING.md')


def stopp(slug, skal, kod=2, kalla='kontroller/prototyp.py'):
    """En start som stannade före körningen: en kort post med skälet. Den ersätter ingen post."""
    tid = korslut.nu()
    korning = ledig(slug, stampel(tid))
    domlogg = _atelje().UNDERLAG / slug / skapande.DOMLOGG
    post = {'schema': 1, 'id': 'SLUT-ATELJE-%s-%s' % (slug, korning), 'titel': 'Slutbesked: skapandeflödet %s stannade före körningen, %s' % (slug, tid),
            'typ': TYP_STOPP, 'uppdrag': UPPDRAG, 'kund': slug, 'moment': 'skapandeflödet (README.md, kedjan steg 2–5)',
            'forfattare': 'kontroller/ateljeslut.py (%s)' % kalla, 'datum': tid, 'granskad_identitet': ['start %s' % tid],
            'rapportstatus': 'färdig', 'bedomningsutfall': 'ej bedömt (slutkod %d): ingen körning startades; %s' % (kod, skal),
            'foregaende': EJ, 'ersatt_av': EJ, 'underlag': ['underlag/%s/%s' % (slug, skapande.DOMLOGG)] if domlogg.is_file() else EJ,
            'beslut': EJ, 'atgarder': ['rätta det som stoppade starten (skälet) och starta igen'], 'korning': {'id': korning, 'startad': None, 'slutad': tid},
            'utfall': {'slag': 'stopp före körningen', 'text': skal}, 'skal': skal, 'slutkod': kod,
            'slutkod_text': 'Slutkod %d: %s; %s stannade före körningen' % (kod, SLUTKODER.get(kod, EJ), kalla.rsplit('/', 1)[-1]),
            'tillstand': {'sessionen_avslutad': {'varde': None, 'text': 'ingen körning startades'},
                          'tekniskt_godkant': {'varde': None, 'text': 'ingen ny körning att pröva'},
                          'designgranskaren_godkanner': {'varde': None, 'text': 'ingen ny körning att granska'},
                          'agaren_godkanner': {'varde': None, 'text': 'ingen ny körning att döma; ateljén beskrivs av den föregående posten'},
                          'klart_for_leverans': {'varde': False, 'text': 'ingen körning startades', 'omfattning': EJ}},
            'kompetenskedjan': KOMPETENSKEDJAN, 'brister': [skal]}
    try:
        return skriv(slug, korning, post, ersatt=False)[1]
    except (OSError, ValueError) as e:
        post.update(slutpost=None, slutpost_fel=str(e)[:300])
        return post


def bevara_forra(slug, st):
    """Före en start som skriver över eller tar bort STATUS.json: en körning som slutade utan slutpost (arbetaren dödades,
    eller körningen är från före slutposterna) får en post i efterhand, med sin STATUS.json och, när den skrevs i
    körningen, REDOVISNING.md. En körning som pågår, eller en start som pågår (steg startar), rörs inte. Ger (fil, post)
    eller (None, None)."""
    a = _atelje()
    st = st if isinstance(st, dict) else {}
    if not st.get('startad') or st.get('steg') in (None, 'startar') or (st.get('pid') and a.lever(st['pid'])):
        return None, None
    if post_for(slug, st)[0]:
        return None, None
    red = a.UNDERLAG / slug / 'atelje' / 'REDOVISNING.md'
    try:
        huvud = red.read_text(encoding='utf-8', errors='replace').split('\n', 1)[0] if red.is_file() and not red.is_symlink() else ''
    except OSError:
        huvud = ''
    m = re.search(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\s*$', huvud)
    egen = bool(m) and m.group(1) >= str(st['startad'])
    tid = korslut.nu()
    status = dict(st)
    korning = ledig(slug, stampel(st['startad']) or stampel(tid))
    post = bygg(slug, status, korning, typ=TYP_EFTERHAND,
                efterhand='i efterhand %s, ur körningens STATUS.json; ingen slutpost skrevs när körningen slutade (arbetaren dödades, '
                          'eller körningen är från före slutposterna)' % tid)
    post['brister'].insert(0, 'posten är skriven i efterhand (%s); %s' % (
        tid, 'redovisningen är körningens egen' if egen else 'redovisningen i ateljén är inte körningens och kopierades inte'))
    return skriv(slug, korning, post, status=status, redovisning=red if egen else None)


def aktuell(slug, fil=None):
    """Posten prövad mot domloggen nu, utan att posten på disk ändras: ägarens beslut efter körningen med avsändaren, och
    tillståndet ägaren godkänner ur dem. Utan fil: den senaste posten. Ger None utan post."""
    poster = slutposter(slug)
    f = Path(fil) if fil else (poster[-1] if poster else None)
    p = korslut.las(f) if f else None
    if not isinstance(p, dict):
        return None
    p = json.loads(json.dumps(p))
    k = p.get('korning') if isinstance(p.get('korning'), dict) else {}
    if p.get('typ') in (TYP, TYP_EFTERHAND) and k.get('startad'):
        b = agarens_beslut(slug, {'startad': k['startad']})
        p['agarens_beslut'] = b
        st_ = {'startad': k['startad'], 'kandidatflode': k.get('fas') != 'aldre', 'lage': k.get('lage'), 'steg': k.get('steg')}
        t = p.get('tillstand') if isinstance(p.get('tillstand'), dict) else {}
        t['agaren_godkanner'] = tillstanden(slug, st_, (p.get('utfall') or {}).get('slag'), p.get('kandidater') or [], b)['agaren_godkanner']
        p['tillstand'] = t
    p['provad'] = {'tid': korslut.nu(), 'text': 'ägarens beslut prövade mot domloggen nu'}
    olas = skapande.olasbara_text((p.get('agarens_beslut') or {}) if isinstance(p.get('agarens_beslut'), dict) else {})
    if olas:
        p['provad']['text'] += '; %s' % olas
        p['brister'] = list(p.get('brister') or []) + [olas]
    return p


# --- terminalens besked, skrivet ur posten och ingenting annat ---

def _kandidatrad(x):
    av = x.get('avbruten_vid') if isinstance(x.get('avbruten_vid'), dict) else {}
    if x.get('status') == 'avbruten' and av.get('orsak') in ('stoppet', 'fel'):
        return '%s avbruten %s %s' % (x['id'], 'vid stoppet' if av['orsak'] == 'stoppet' else 'av fel', av.get('tid') or EJ)
    return '%s %s' % (x['id'], x.get('statustext') or x.get('status'))


def text(post):
    """Terminalens besked ur posten (ägarens uppdrag 2026-10-07, punkt 4). Inget av skisskritikens innehåll och inga
    titlar: blindningen före ägarens första beslut gäller också terminalen."""
    if post.get('typ') == TYP_STOPP:
        r = [str(post.get('skal') or EJ)] + ['Brist: %s' % b for b in (post.get('brister') or [])[1:]]
        r += ['Nästa steg: %s' % x for x in post.get('atgarder') or []]
    else:
        k = post.get('korning') or {}
        r = ['Skapandeflödet %s, körningen %s (läge %s; %s): %s' % (post.get('kund'), k.get('startad') or EJ, k.get('lage') or EJ,
                                                                   post.get('moment'), (post.get('utfall') or {}).get('text') or EJ)]
        if post.get('efterhand'):
            r.append('Posten är skriven %s.' % post['efterhand'])
        kand = post.get('kandidater') or []
        if kand:
            r.append('Kandidaterna: %d av %d valbara; %s' % (sum(1 for x in kand if x.get('valbar')), len(kand), ', '.join(_kandidatrad(x) for x in kand)))
            tv = post.get('tider') or {}
            r.append('Första valbara skissen: %s' % ('%s (%s)' % (tv['forsta_valbara'], tv.get('forsta_valbara_kalla')) if tv.get('forsta_valbara') else 'ingen'))
        r.append('Tillstånden, var för sig:')
        t = post.get('tillstand') or {}
        for nyckel, namn in korslut.TILLSTAND:
            x = t.get(nyckel) or {}
            r.append('  %s: %s%s' % (namn, korslut.ORD.get(x.get('varde'), str(x.get('varde'))), (' — ' + x['text']) if x.get('text') else ''))
        if (t.get('klart_for_leverans') or {}).get('omfattning'):
            r.append('  (omfattningen: %s)' % t['klart_for_leverans']['omfattning'])
        r += ['Brist: %s' % b for b in post.get('brister') or []]
        r += ['Nästa steg: %s' % x for x in post.get('atgarder') or []]
        r.append('Kompetenskedjan: %s' % post.get('kompetenskedjan', EJ))
        r.append('Posten: %s%s' % (post.get('rapportstatus') or EJ, ', ersatt av %s' % post['ersatt_av'] if post.get('ersatt_av') not in (None, EJ) else ''))
    r.append('Slutpost: %s' % (post.get('slutpost') or 'skrevs inte: %s' % post.get('slutpost_fel', EJ)))
    r.append(post.get('slutkod_text') or EJ)
    return '\n'.join(r)


def main(argv):
    a = _atelje()
    if len(argv) not in (2, 3) or not a.SLUG.match(argv[1]):
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        return 2
    fil = None
    if len(argv) == 3:
        if not korslut.KORNING_NAMN.fullmatch(argv[2]):
            return 2
        fil = katalog(argv[1]) / argv[2] / SLUTPOST
    p = aktuell(argv[1], fil)
    if not p:
        print('ingen slutpost i kunder/%s/atelje/korningar/' % argv[1])
        return 1
    print(text(p))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
