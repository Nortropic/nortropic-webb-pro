#!/usr/bin/env python3
"""prototyp.py — ägarens ingång till skapandeflödet för startsidan (kunskap/skapandeflodet.md), startad av ägaren eller
en session utanför bygget: den startar kontroller/atelje.py med läget ur ägarens senaste dom i domloggen
(underlag/<slug>/DESIGNDOMAR.jsonl). Var steget står i hela kedjan, från kundunderlag till leverans, och vem som
startar vad: README.md. Codex via ägaren 2026-10-05: tre designflöden, där förbättringarna inte följde med mellan dem,
blev ett; prototypen är inget eget flöde längre.

    .venv/bin/python kontroller/prototyp.py <slug> [--ny-riktning | --putsa | --om | --valda] [--vanta SEK]

Utan flagga avgör domloggen: ägarens senaste dom (efter den senaste körningen; ägaren, eller ägaren via Codex med belägg,
aldrig en vidarebefordrad AI-bedömning: kontroller/skapande.py, ar_agarens) säger ny_riktning → omtag (designbesluten tas
bort, utforskningen börjar om ur mallen); putsa → förfina den valda riktningen vidare; godkand → inget att göra, bygget
tar vid från vinnaren (kor.sh), om godkännandet gäller. I kandidatflödet (kontroller/kandidater.py): valj, eller putsa
efter en förfining → valda (de valda kandidaterna förfinas, var för sig); jamfor → inget körs (ägaren jämför); forkasta
→ stopp tills ägaren begär en ny riktning. Ingen körning än → en ny, som omtag om domloggen redan säger ny_riktning; en
annan dom, eller tidigare designbeslut utan dom, stoppar tills --ny-riktning eller --om väljs. Går en rad i domloggen
efter ägarens senaste dom inte att läsa stoppar läget också: där kan ägarens senare beslut stå. En körning som pågår
väntas in. Ägaren dömer i dashboardens vy Prototyp.

Beskedet och slutkoden när en körning har slutat kommer ur körningens slutpost (kunder/<slug>/atelje/korningar/
<körning>/SLUT.json, kontroller/ateljeslut.py); ett stopp före körningen får en kort post. Slutkoderna: 0 klar (eller
godkänd, inget att köra) · 2 ingen körning startades · 4 körningen föll, stoppades eller avbröts · 5 väntan slut, körningen
pågår (kör samma kommando igen) · 6 ingen startsida att bygga vidare på (atelje.py:s docstring).
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import skapande  # noqa: E402


def lage(slug):
    """(läge, skäl): 'ny-riktning', 'putsa', 'valda', 'om', 'godkand', 'stopp' eller 'vanta' ur domloggen och ateljéns status."""
    st = atelje.las_json(atelje.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    dom = skapande.senaste(slug, underlag=atelje.UNDERLAG)
    if st.get('pid') and atelje.lever(st['pid']) and st.get('steg') not in atelje.AVSLUTADE + ('fel',):
        return 'vanta', 'en körning pågår (steg %s)' % st.get('steg')
    if atelje.avbruten(st):  # arbetaren dog mitt i ett steg: ta vid där den slutade, aldrig en ny körning (granskningen V2)
        return 'stopp', ('körningen avbröts i steg %s (arbetaren lever inte): kör .venv/bin/python kontroller/atelje.py %s --fortsatt, '
                         'som tar vid utan att något klart görs om' % (st.get('steg'), slug))
    ag = skapande.agarens_senaste(slug, underlag=atelje.UNDERLAG)
    if ag['oklara']:  # ingen dom försvinner tyst (GR-20261007-r100-om#KAN-A): läget gissas inte förbi en oläsbar rad
        return 'stopp', ('%s. Vägen vidare: ett nytt beslut från ägaren efter raden (vyn Prototyp, eller skapande.py dom med belägg) gäller '
                         'från sin rad, eller välj läget uttryckligen (--ny-riktning, --putsa, --om eller --valda); raden skrivs inte om av sig '
                         'själv' % skapande.oklara_text(ag))
    if not st.get('steg'):
        if dom and dom['beslut'] == 'ny_riktning':
            return 'ny-riktning', 'ingen körning i skapandeflödet än, och ägarens senaste dom (%s) säger ny riktning' % dom['tid']
        if dom:  # putsa eller godkand utan körning: det finns ingen vald riktning i skapandeflödet att putsa eller bygga från
            return 'stopp', ('ägarens senaste dom (%s, %s, beslut %s) gäller ingen körning i skapandeflödet: det finns ingen vald '
                             'riktning att putsa eller bygga från. Välj --ny-riktning (designbesluten tas bort) eller --om (en ny '
                             'utforskning med dem kvar) uttryckligen' % (dom['tid'], dom['kalla'], dom['beslut']))
        u = atelje.UNDERLAG / slug
        gamla = [n for n, p in (('prototyp/', u / 'prototyp'), ('REFERENSER.md med huvudreferens', u / 'REFERENSER.md'),
                                ('startsidan', atelje.KUNDER / slug / 'sajt' / 'src' / 'pages' / 'index.astro'))
                 if p.exists() and (n != 'REFERENSER.md med huvudreferens' or atelje.referensval.huvudreferensrader(slug, atelje.UNDERLAG))]
        if gamla and not dom:  # granskningen av skapandeflödet, punkt 1: inget tyst omtag över gamla designbeslut
            return 'stopp', ('tidigare designbeslut finns (%s) men ingen dom i domloggen: lägg in ägarens dom med '
                             '.venv/bin/python kontroller/skapande.py dom %s --kalla ägaren --belagg ... --beslut ... --fil ... (belägget: '
                             'var ägarens egna ord står), eller välj --ny-riktning eller --om uttryckligen' % (', '.join(gamla), slug))
        return 'om', 'ingen körning än'
    if st.get('steg') == 'forberedd':
        import forberedelse
        return ('om', 'underlaget är förberett; designarbetet kan starta') if forberedelse.giltig(slug) else ('stopp', 'förberedelsen är inaktuell; kör --forbered igen')
    efter = dom if dom and dom.get('tid', '') > (st.get('klar') or st.get('startad') or '') else None
    if efter:
        if efter['beslut'] == 'godkand':  # samma prövning som kor.sh gör innan bygget tar vid (skapande.godkand_giltig)
            ok, skal = skapande.godkand_giltig(slug, atelje.UNDERLAG, atelje.KUNDER)
            if not ok:
                return 'stopp', 'ägarens senaste dom (%s) godkänner startsidan, men godkännandet gäller inte: %s' % (efter['tid'], skal)
        skal = 'ägarens dom %s (%s)' % (efter['tid'], efter['kalla'])
        if efter['beslut'] == 'valj' or (efter['beslut'] == 'putsa' and atelje.kandidatkorning(atelje.UNDERLAG / slug / 'atelje', st)):
            return 'valda', skal + ': förfina de valda kandidaterna'
        if efter['beslut'] == 'jamfor':
            return 'vanta', skal + ': ägaren jämför kandidater; inget körs förrän ägaren väljer'
        if efter['beslut'] == 'forkasta':
            return 'stopp', skal + ': ägaren förkastade kandidaterna; nästa steg är en ny riktning (--ny-riktning)'
        return {'ny_riktning': 'ny-riktning', 'putsa': 'putsa', 'godkand': 'godkand'}[efter['beslut']], skal
    if st.get('steg') == 'fel':
        return 'vanta', 'förra körningen föll (%s); --fortsatt i kontroller/atelje.py tar vid efter den senaste klara fasen' % str(st.get('fel'))[:200]
    return 'vanta', 'körningen är %s och väntar på ägarens dom i dashboardens vy Prototyp' % st.get('steg')


def bygget_nekas(slug):
    """Skälet när ägarens domlogg inte tillåter ett bygge i skapandeflödets väg, annars None (kor.sh): ägarens senaste dom
    säger putsa eller ny riktning efter körningen, eller läget stoppar med en dom i loggen (en dom som inte gäller någon
    körning, ett godkännande som inte gäller). Tidigare designbeslut utan någon dom stoppar inte ett bygge; det tar
    skapandeflödet i steg 5.1 (omgranskning 2, fynd 3)."""
    vald, skal = lage(slug)
    if vald in ('putsa', 'ny-riktning', 'valda') or (vald == 'stopp' and skapande.senaste(slug, underlag=atelje.UNDERLAG)):
        return '%s: %s' % (vald, skal)
    st = atelje.las_json(atelje.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    if atelje.kandidatkorning(atelje.UNDERLAG / slug / 'atelje', st) and vald != 'godkand':  # kandidaterna väntar på ägarens val och godkännande
        return 'kandidatflödet: %s' % skal
    return None



HANDLINGAR = {'forbered': 'Förbered kundunderlaget', 'fortsatt': 'Återuppta arbetet', 'stoppa': 'Stoppa arbetet',
              'om': 'Starta referensjakt och skiss', 'valda': 'Förfina de valda förslagen', 'putsa': 'Förfina riktningen',
              'ny-riktning': 'Arkivera försöket och sök en ny riktning'}


def handlingar(slug):
    """Nästa uttryckliga handling; läsning får aldrig starta ett arbete eller spara en dom."""
    st = atelje.las_json(atelje.UNDERLAG / slug / 'atelje/STATUS.json') or {}
    if st.get('pid') and atelje.lever(st['pid']) and st.get('steg') not in atelje.AVSLUTADE + ('fel',):
        val = ['stoppa']
    elif atelje.avbruten(st) or st.get('steg') == 'fel':
        val = ['fortsatt', 'forbered']
    else:
        lage_, _ = lage(slug)
        val = [lage_] if lage_ in HANDLINGAR else []
        if not st or st.get('steg') == 'forberedd':
            import forberedelse
            if not forberedelse.giltig(slug):
                val = ['forbered']
        dom = skapande.senaste(slug, underlag=atelje.UNDERLAG)
        if dom and dom.get('beslut') == 'forkasta':
            val = ['ny-riktning']
    return [{'id': n, 'text': HANDLINGAR[n]} for n in val]


def fran_dashboard(slug, handling, start_id):
    """Samma main/startlås som CLI. Start-id gör ett osäkert HTTP-omförsök idempotent."""
    import re
    if handling not in HANDLINGAR or not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', str(start_id or '')):
        raise ValueError('en känd handling och ett start-id behövs')
    if not atelje.SLUG.fullmatch(slug):
        raise ValueError('ogiltig slug')
    # En redan bokförd start får alltid läsas om; i övrigt behövs ett möjligt nästa steg.
    finns = atelje.startfil(atelje.UNDERLAG / slug / 'atelje', start_id)
    if handling != 'stoppa' and not finns.is_file() and handling not in {x['id'] for x in handlingar(slug)}:
        raise ValueError('handlingen är inte nästa steg; läs aktuellt läge igen')
    return main([slug, '--' + handling, '--start-id', start_id, '--vanta', '0'])


def main(argv=None):
    p = argparse.ArgumentParser(prog='prototyp', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--vanta', type=int, default=540)
    p.add_argument('--start-id', help='samma id återanvänder samma startbegäran')
    grupp = p.add_mutually_exclusive_group()
    grupp.add_argument('--forbered', action='store_true', help='förbered verifierat kundunderlag före referensval och design')
    grupp.add_argument('--fortsatt', action='store_true', help='återuppta avbrutet arbete utan att göra om klara steg')
    grupp.add_argument('--stoppa', action='store_true', help='stoppa arbetaren och dess sessioner')
    grupp.add_argument('--ny-riktning', action='store_true', help='omtag: designbesluten tas bort, ny utforskning ur mallen')
    grupp.add_argument('--putsa', action='store_true', help='förfina den valda riktningen vidare med ägarens senaste dom')
    grupp.add_argument('--om', action='store_true', help='en ny körning utan att ta bort designbesluten')
    grupp.add_argument('--valda', action='store_true', help='förfina kandidaterna i ägarens senaste val (kandidatflödet)')
    a = p.parse_args(argv)
    if not atelje.SLUG.match(a.slug):
        p.print_usage()
        return 2
    if os.environ.get('NWP_SLUG'):
        print('prototypen startas av ägaren eller en session utanför bygget, inte inifrån ett bygge', file=sys.stderr)
        return 2
    extra = ['--start-id', a.start_id] if a.start_id else []
    if a.forbered or a.fortsatt or a.stoppa:
        handling = 'forbered' if a.forbered else 'fortsatt' if a.fortsatt else 'stoppa'
        return atelje.main([a.slug, '--' + handling, '--vanta', str(a.vanta)] + extra)
    vald, skal = ('ny-riktning', 'flaggan') if a.ny_riktning else ('putsa', 'flaggan') if a.putsa else ('om', 'flaggan') if a.om \
        else ('valda', 'flaggan') if a.valda else lage(a.slug)
    print('Prototyp %s: %s (%s).' % (a.slug, vald, skal), flush=True)
    if vald == 'stopp':  # en kort slutpost med skälet, och beskedet ur den (ägarens uppdrag 2026-10-07, punkt 4)
        st = atelje.las_json(atelje.UNDERLAG / a.slug / 'atelje' / 'STATUS.json') or {}
        if atelje.avbruten(st):  # en körning vars arbetare dog får sin slutpost i efterhand
            atelje.bevara_forra(a.slug, st, 'Den avbrutna körningen fick sin slutpost i efterhand')
        return atelje.avsluta_fore(a.slug, skal, 2, 'kontroller/prototyp.py')
    if vald == 'godkand':
        print('Ägaren har godkänt startsidan; bygget tar vid från underlag/%s/atelje/vinnare/ (./kor.sh %s "<verksamhet>").' % (a.slug, a.slug))
        return 0
    return atelje.main([a.slug, '--vanta', str(a.vanta)] + ([] if vald == 'vanta' else ['--' + vald]) + extra)


if __name__ == '__main__':
    sys.exit(main())
