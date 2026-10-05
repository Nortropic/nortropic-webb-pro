#!/usr/bin/env python3
"""korslut.py — kor.sh:s avslut: sammanfattar provet, stoppvakten och granskningen, jämför de skyddade filernas
hashlistor före och efter körningen, och sätter slutkoden (revisionen 2026-10-03, F10 och F11).

    .venv/bin/python kontroller/korslut.py <kunder/slug> <claude-kod> <hashlista-fore> <hashlista-efter> <korning>

Slutkod: 0 provet grönt för just det bygge som ligger i dist/, RAPPORT.md finns, stoppvakten själv släppte med gröna
kontroller och godkänd granskning, och granskningen gäller samma bygge och samma metod som nu · 1 avslutat utan det
(också när en äldre godkänd granskningsfil ligger kvar; omgång tre, F11) · 3 mekaniken (provet, kriterierna, mallen,
krokarna, kor.sh, dashboarden) eller gränsen (en post tillkom eller försvann direkt under kunder/ eller underlag/, eller
flaggan uchg lyftes; kor.sh:s grans(), Codex 2026-10-04 F1), eller ägarens domlogg, ändrades under körningen · 4 claude
avslutade med annan kod än 0 · 6 bygget stannade utan sajt (ateljén förkastade alla riktningar, skaparen lämnade grundidén,
eller ägaren dömde startsidan efter körningen).
Texterna (kunskap/, LARDOMAR.md, skills) skrivs också av kirurgens intag och ägarens domar i dashboarden medan ett
bygge pågår; ändringar där ger bara en varning. Hela fillistan klassificeras; bara utskriften kapas.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MEKANIK = ('kontroller/', 'kritik/', 'mall/', '.claude/hooks/', '.claude/settings', 'kor.sh', 'dashboard/', 'dashboard.sh',
           'CLAUDE.md', 'BESLUT.md', '.gitignore', 'syskon:', 'flagga:')


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


def ar_godkant(k, s, v, g, korning=None):
    """Godkänt bara när allt gäller det bygge som ligger i dist/ nu: provet grönt med samma dist-hash som dist/, rapporten
    finns, stoppvakten släppte med gröna kontroller och godkänd granskning (inte vid sitt tak), och granskningen är
    godkänd för samma dist-hash och samma metod som nu (omgång tre, F11)."""
    if not (s and s.get('ok')):
        return False, 'provet är inte grönt'
    if not (k / 'RAPPORT.md').is_file():
        return False, 'RAPPORT.md saknas'
    dist = k / 'sajt' / 'dist'
    try:
        import prova
        nu_hash = prova.dist_hash(dist) if (dist / 'index.html').is_file() else None
    except Exception as e:  # noqa: BLE001 — kan hashen inte räknas är bygget inte verifierat
        return False, 'kunde inte hasha dist/: %s' % e
    if not nu_hash or s.get('dist_sha256') != nu_hash:
        return False, 'provet gäller inte det bygge som ligger i dist/ nu'
    if not (v and v.get('slapp') and str(v.get('skal') or '').startswith('kontrollerna gröna')):
        return False, 'stoppvakten släppte inte med gröna kontroller och godkänd granskning (%s)' % ((v or {}).get('skal') or 'ingen STOPPVAKT.json')
    if korning and v.get('korning') != korning:
        return False, 'stoppvaktens besked gäller en annan körning (%s, inte %s)' % (v.get('korning'), korning)
    if v.get('dist_sha256') != nu_hash:
        return False, 'stoppvaktens besked gäller ett annat bygge än det i dist/'
    if not (g and g.get('godkand')):
        return False, 'ingen godkänd granskning'
    if g.get('dist_sha256') != nu_hash:
        return False, 'granskningen gäller ett annat bygge än det i dist/'
    try:
        import granska
        if not granska.samma_metod(g, granska.aktuell_metod(k.name)):  # samma jämförelse som granskningen själv gör
            return False, 'granskningen gjordes med en annan metod (underlag, modell, effort, antal eller originalitetsläge) än den som gäller nu'
    except Exception as e:  # noqa: BLE001
        return False, 'kunde inte jämföra granskningsmetoden: %s' % e
    return True, ''


def vald_granskning(k, korning):
    """(dom, slutlig dist, senaste giltiga dom oavsett bygge och metod, fel): domen för det slutliga bygget härledd ur
    giltiga omgångar med hela identiteten (körning, dist, aktuell metod; kontroller/granska.py valj_sammanfattning), aldrig
    ur rotfilen när omgångar finns. Kan omgångarna inte läsas eller valideras är det ett fel som nekar godkännande; rotfilen
    är reserv bara när inga omgångar finns (Codex R38/R39, F11)."""
    dist = k / 'sajt' / 'dist'
    try:
        import prova
        nu_hash = prova.dist_hash(dist) if (dist / 'index.html').is_file() else None
    except Exception:  # noqa: BLE001
        nu_hash = None
    gdir = k / 'granskning'
    try:
        import granska
        finns = gdir.is_dir() and bool(granska.rundor(gdir))
    except Exception as e:  # noqa: BLE001
        return None, nu_hash, None, 'omgångarna kunde inte listas: %s' % e
    if not finns:
        return las(gdir / 'GRANSKNING.json'), nu_hash, None, None  # inga omgångar (manuellt underlag): rotfilen är det enda som finns
    try:
        metod = granska.aktuell_metod(k.name)
        val = granska.valj_sammanfattning(gdir, korning, nu_hash, metod, strikt=True)  # en overifierbar omgång i körningen nekar (Codex R40)
        alla = granska.valj_sammanfattning(gdir, None, None)
    except Exception as e:  # noqa: BLE001
        return None, nu_hash, None, 'omgångarna kunde inte läsas eller valideras: %s' % e
    g = val[1] if val else None
    if g and not (g.get('dist_sha256') == nu_hash and granska.samma_metod(g, metod)):
        g_hel = None  # ingen giltig omgång med hela identiteten: visas som senaste, men godkänner inget
    else:
        g_hel = g
    return g_hel, nu_hash, (val[1] if val else None) if g_hel is None else (alla[1] if alla and alla[0] != val[0] else None), None


def main(argv):
    k, rc, fore, efter = Path(argv[1]), argv[2], argv[3], argv[4]
    korning = argv[5] if len(argv) > 5 else None
    s, v = las(k / 'prov' / 'STATUS.json'), las(k / 'prov' / 'STOPPVAKT.json')
    g, nu_hash, senaste, gfel = vald_granskning(k, korning)
    skydd = andrade(fore, efter)
    # ägarens domlogg är låst under bygget (kor.sh, chflags uchg): en ändring kom inte från dashboarden (omgranskningen,
    # fynd 2: loggen räknades som text och gav bara en varning)
    domlogg = [f for f in skydd if f.startswith('underlag/') and f.endswith('/DESIGNDOMAR.jsonl')]
    mekanik = [f for f in skydd if f.startswith(MEKANIK)] + domlogg
    print('\nclaude avslutade med kod', rc)
    if skydd:
        print('VARNING: skyddade filer ändrades under körningen, av bygget eller någon annan (kirurgen, ägarens dom):\n'
              + '\n'.join(skydd[:40]) + ('\n… %d till' % (len(skydd) - 40) if len(skydd) > 40 else ''))
    if s:
        print('Provet:', 'GRÖNT' if s.get('ok') else 'RÖTT', '—', ', '.join('%s %s' % (n, 'ok' if x['ok'] else 'RÖD') for n, x in s['grindar'].items()))
        if (s.get('info') or {}).get('vinnare'):
            print('Ateljéns vinnare mot bygget:', s['info']['vinnare'])
    else:
        print('Provet: inget STATUS.json (provet kördes aldrig)')
    if v:
        print('Stoppvakten:', v.get('skal'), '(försök %s av %s)' % (v.get('forsok'), v.get('tak')))
    if gfel:
        print('Granskningen: omgångarna kunde inte läsas eller valideras, inget godkännande:', gfel)
    elif g:
        # domen med hela identiteten (körning, slutlig dist, aktuell metod); en dom om ett annat bygge sägs som sådan (Codex R38/R39, F11)
        print('Granskningen:', 'GODKÄND' if g.get('godkand') else 'UNDERKÄND', '(omgång %s, dist %s = slutliga bygget, aktuell metod)' % (
            g.get('runda'), (g.get('dist_sha256') or '')[:12]), '—', ', '.join('%s %s' % (n, x.get('betyg')) for n, x in (g.get('kriterier') or {}).items()))
    else:
        print('Granskningen: ingen giltig omgång för det slutliga bygget %s med aktuell metod; slutliga bygget är inte granskat' % (nu_hash or '?')[:12])
    if senaste and (not g or senaste.get('runda') != g.get('runda')):
        print('Senaste dom oavsett bygge och metod: %s (omgång %s, dist %s%s)' % ('godkänd' if senaste.get('godkand') else 'underkänd', senaste.get('runda'), (senaste.get('dist_sha256') or '')[:12],
              '' if senaste.get('dist_sha256') == nu_hash else ' ≠ slutliga bygget'))
    print('Rapport:', k / 'RAPPORT.md' if (k / 'RAPPORT.md').is_file() else 'saknas')
    print('Titta:  cd %s && npx astro preview' % (k / 'sajt'))
    godkant, skal = ar_godkant(k, s, v, g, korning)
    if not godkant and skal:
        print('Inte godkänt:', skal)
    if mekanik:
        if domlogg:
            print('Ägarens domlogg ändrades under körningen fast den var låst; ägarens domar skrivs bara av dashboarden när inget bygge pågår.')
        print('Slutkod 3: mekaniken eller gränsen ändrades under körningen:', ', '.join(mekanik[:20]))
        return 3
    if rc != '0':
        print('Slutkod 4: claude avslutade med kod', rc)
        return 4
    if v and v.get('ateljen_forkastad') and v.get('slapp'):
        print('Slutkod 6: bygget stannade utan sajt (ägarbeslut 2026-10-04): %s; underlaget i underlag/%s/atelje/' % (v.get('skal') or 'ateljén förkastade alla riktningar', k.name))
        return 6
    print('Slutkod', 0 if godkant else 1, ':', 'godkänt bygge' if godkant else 'avslutat utan grönt prov och godkänd granskning')
    return 0 if godkant else 1


if __name__ == '__main__':
    if len(sys.argv) not in (5, 6):
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv))
