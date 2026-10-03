#!/usr/bin/env python3
"""korslut.py — kor.sh:s avslut: sammanfattar provet, stoppvakten och granskningen, jämför de skyddade filernas
hashlistor före och efter körningen, och sätter slutkoden (revisionen 2026-10-03, F10 och F11).

    .venv/bin/python kontroller/korslut.py <kunder/slug> <claude-kod> <hashlista-fore> <hashlista-efter>

Slutkod: 0 provet grönt, RAPPORT.md finns och granskningen godkänd · 1 avslutat utan det · 3 mekaniken (provet,
kriterierna, mallen, krokarna, kor.sh, dashboarden) ändrades under körningen · 4 claude avslutade med annan kod än 0.
Texterna (kunskap/, LARDOMAR.md, skills) skrivs också av kirurgens intag och ägarens domar i dashboarden medan ett
bygge pågår; ändringar där ger bara en varning. Hela fillistan klassificeras; bara utskriften kapas.
"""
import json
import sys
from pathlib import Path

MEKANIK = ('kontroller/', 'kritik/', 'mall/', '.claude/hooks/', '.claude/settings', 'kor.sh', 'dashboard/', 'dashboard.sh',
           'CLAUDE.md', 'BESLUT.md', '.gitignore')


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def hashlista(p):
    """{fil: hash} ur shasum-utdata (hash, två blanksteg, filnamn)."""
    ut = {}
    try:
        for rad in Path(p).read_text(encoding='utf-8', errors='replace').splitlines():
            if '  ' in rad:
                h, _, fil = rad.partition('  ')
                ut[fil.strip()] = h.strip()
    except OSError:
        pass
    return ut


def andrade(fore, efter):
    """Filer vars hash skiljer sig, saknas efteråt eller tillkommit."""
    f, e = hashlista(fore), hashlista(efter)
    return sorted(x for x in set(f) | set(e) if f.get(x) != e.get(x))


def main(argv):
    k, rc, fore, efter = Path(argv[1]), argv[2], argv[3], argv[4]
    s, v, g = las(k / 'prov' / 'STATUS.json'), las(k / 'prov' / 'STOPPVAKT.json'), las(k / 'granskning' / 'GRANSKNING.json')
    skydd = andrade(fore, efter)
    mekanik = [f for f in skydd if f.startswith(MEKANIK)]
    print('\nclaude avslutade med kod', rc)
    if skydd:
        print('VARNING: skyddade filer ändrades under körningen, av bygget eller någon annan (kirurgen, ägarens dom):\n'
              + '\n'.join(skydd[:40]) + ('\n… %d till' % (len(skydd) - 40) if len(skydd) > 40 else ''))
    if s:
        print('Provet:', 'GRÖNT' if s.get('ok') else 'RÖTT', '—', ', '.join('%s %s' % (n, 'ok' if x['ok'] else 'RÖD') for n, x in s['grindar'].items()))
    else:
        print('Provet: inget STATUS.json (provet kördes aldrig)')
    if v:
        print('Stoppvakten:', v.get('skal'), '(försök %s av %s)' % (v.get('forsok'), v.get('tak')))
    if g:
        print('Granskningen:', 'GODKÄND' if g.get('godkand') else 'UNDERKÄND', '(omgång %s)' % g.get('runda'), '—',
              ', '.join('%s %s' % (n, x.get('betyg')) for n, x in (g.get('kriterier') or {}).items()))
    else:
        print('Granskningen: ingen')
    print('Rapport:', k / 'RAPPORT.md' if (k / 'RAPPORT.md').is_file() else 'saknas')
    print('Titta:  cd %s && npx astro preview' % (k / 'sajt'))
    godkant = bool(s and s.get('ok')) and (k / 'RAPPORT.md').is_file() and bool(g and g.get('godkand'))
    if mekanik:
        print('Slutkod 3: mekaniken ändrades under körningen:', ', '.join(mekanik[:20]))
        return 3
    if rc != '0':
        print('Slutkod 4: claude avslutade med kod', rc)
        return 4
    print('Slutkod', 0 if godkant else 1, ':', 'godkänt bygge' if godkant else 'avslutat utan grönt prov och godkänd granskning')
    return 0 if godkant else 1


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv))
