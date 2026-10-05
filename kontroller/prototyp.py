#!/usr/bin/env python3
"""prototyp.py — ägarens ingång till skapandeflödet för startsidan (kunskap/skapandeflodet.md). Samma kod som byggets
steg 5.1 (kontroller/atelje.py: utforska, välj, förfina, slutdom), startad av ägaren utanför bygget, med läget ur ägarens
senaste dom i domloggen (underlag/<slug>/DESIGNDOMAR.jsonl). Codex via ägaren 2026-10-05: tre designflöden, där
förbättringarna inte följde med mellan dem, blev ett; prototypen är inget eget flöde längre.

    .venv/bin/python kontroller/prototyp.py <slug> [--ny-riktning | --putsa | --om] [--vanta SEK]

Utan flagga avgör domloggen: ägarens senaste dom (efter den senaste körningen) säger ny_riktning → omtag (designbesluten
arkiveras, utforskningen börjar om ur mallen); putsa → förfina den valda riktningen vidare; godkand → inget att göra,
bygget tar vid från vinnaren (kor.sh). Ingen körning än → en ny, som omtag om domloggen redan säger ny_riktning. En
körning som pågår väntas in. Ägaren dömer i dashboardens vy Prototyp.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import skapande  # noqa: E402


def lage(slug):
    """(läge, skäl): 'ny-riktning', 'putsa', 'om', 'godkand' eller 'vanta' ur domloggen och ateljéns status."""
    st = atelje.las_json(atelje.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    dom = skapande.senaste(slug, underlag=atelje.UNDERLAG)
    if st.get('pid') and atelje.lever(st['pid']) and st.get('steg') not in ('klar', 'fel', 'forkastad', 'tillbaka'):
        return 'vanta', 'en körning pågår (steg %s)' % st.get('steg')
    if not st.get('steg'):
        if dom and dom['beslut'] == 'ny_riktning':
            return 'ny-riktning', 'ingen körning i skapandeflödet än, och ägarens senaste dom (%s) säger ny riktning' % dom['tid']
        u = atelje.UNDERLAG / slug
        gamla = [n for n, p in (('prototyp/', u / 'prototyp'), ('REFERENSER.md med huvudreferens', u / 'REFERENSER.md'),
                                ('startsidan', atelje.KUNDER / slug / 'sajt' / 'src' / 'pages' / 'index.astro'))
                 if p.exists() and (n != 'REFERENSER.md med huvudreferens' or atelje.referensval.huvudreferensrader(slug, atelje.UNDERLAG))]
        if gamla and not dom:  # granskningen av skapandeflödet, punkt 1: inget tyst omtag över gamla designbeslut
            return 'stopp', ('tidigare designbeslut finns (%s) men ingen dom i domloggen: lägg in ägarens dom med '
                             '.venv/bin/python kontroller/skapande.py dom %s --kalla ... --beslut ... --fil ..., eller välj '
                             '--ny-riktning eller --om uttryckligen' % (', '.join(gamla), slug))
        return 'om', 'ingen körning än'
    efter = dom if dom and dom.get('tid', '') > (st.get('klar') or st.get('startad') or '') else None
    if efter:
        return {'ny_riktning': 'ny-riktning', 'putsa': 'putsa', 'godkand': 'godkand'}[efter['beslut']], 'ägarens dom %s (%s)' % (efter['tid'], efter['kalla'])
    if st.get('steg') == 'fel':
        return 'vanta', 'förra körningen föll (%s); --fortsatt i kontroller/atelje.py tar vid efter den senaste klara fasen' % str(st.get('fel'))[:200]
    return 'vanta', 'körningen är %s och väntar på ägarens dom i dashboardens vy Prototyp' % st.get('steg')


def main(argv=None):
    p = argparse.ArgumentParser(prog='prototyp', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--vanta', type=int, default=540)
    grupp = p.add_mutually_exclusive_group()
    grupp.add_argument('--ny-riktning', action='store_true', help='omtag: designbesluten till arkivet, ny utforskning ur mallen')
    grupp.add_argument('--putsa', action='store_true', help='förfina den valda riktningen vidare med ägarens senaste dom')
    grupp.add_argument('--om', action='store_true', help='en ny körning utan att arkivera designbesluten')
    a = p.parse_args(argv)
    if not atelje.SLUG.match(a.slug):
        p.print_usage()
        return 2
    if os.environ.get('NWP_SLUG'):
        print('prototypen startas av ägaren eller en session utanför bygget, inte inifrån ett bygge', file=sys.stderr)
        return 2
    vald, skal = ('ny-riktning', 'flaggan') if a.ny_riktning else ('putsa', 'flaggan') if a.putsa else ('om', 'flaggan') if a.om else lage(a.slug)
    print('Prototyp %s: %s (%s).' % (a.slug, vald, skal), flush=True)
    if vald == 'stopp':
        print(skal)
        return 2
    if vald == 'godkand':
        print('Ägaren har godkänt startsidan; bygget tar vid från underlag/%s/atelje/vinnare/ (./kor.sh %s "<verksamhet>").' % (a.slug, a.slug))
        return 0
    return atelje.main([a.slug, '--vanta', str(a.vanta)] + ([] if vald == 'vanta' else ['--' + vald]))


if __name__ == '__main__':
    sys.exit(main())
