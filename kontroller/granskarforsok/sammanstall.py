"""Sammanställer granskarförsöket per arm: träffar mot ägarens facit (alla fynd och blockerande), falska blockerande,
nivå, överensstämmelse i arm B, tokens och tid. En matchning räknas bara när båda domarbedömningarna är eniga.

Arm A = dagens text, en granskare (A-1..A-3). Arm B = två isolerade granskare med dagens text, unionen
(A-1+A-4, A-2+A-5, A-3+A-6). Arm persona och arm c = de nya texterna, en granskare.
"""
import json
import os
import statistics as st
from pathlib import Path

G = Path(os.environ.get('NWP_FORSOK') or '/tmp/nwp-granskarforsok')  # utdata, utanför repot
KOD = Path(__file__).resolve().parent
FACIT = json.loads((KOD / 'facit.json').read_text(encoding='utf-8'))
OMDOME = {s: {f['id'] for f in fl if not f['maskin']} for s, fl in FACIT.items()}
ALLA = {s: {f['id'] for f in fl} for s, fl in FACIT.items()}


def las(p):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def granskning(slug, namn):
    rdir = G / slug / 'rot' / 'kunder' / slug / 'ab-granskare' / namn
    g, d1, d2, svar = (las(rdir / f) for f in ('GRANSKNING.json', 'DOM-1.json', 'DOM-2.json', 'svar.json'))
    if not (g and d1 and d2):
        return None
    fynd = [{'typ': f['typ'], 'facit': [], 'verkligt': None} for f in d1['fynd']]
    domar = []
    for d in (d1, d2):
        per = {}
        for b in d['bedomningar']:
            j = d['karta'].get(b['fynd'])
            if j is not None:
                per[j] = b
        domar.append(per)
    for j, f in enumerate(fynd):
        a, b = domar[0].get(j), domar[1].get(j)
        if a and b:
            f['facit'] = sorted(set(a['facit']) & set(b['facit']) & ALLA[slug])
            f['verkligt'] = a['verkligt'] if a['verkligt'] == b['verkligt'] else None
    u = (svar or {}).get('usage') or {}
    tokens = sum(u.get(k, 0) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'))
    return {
        'traff': set().union(*[f['facit'] for f in fynd]) if fynd else set(),
        'traff_block': set().union(*[f['facit'] for f in fynd if f['typ'] == 'blockerande']) if fynd else set(),
        'falska_block': sum(1 for f in fynd if f['typ'] == 'blockerande' and f['verkligt'] is False),
        'block': sum(1 for f in fynd if f['typ'] == 'blockerande'),
        'verkliga_utanfor': sum(1 for f in fynd if not f['facit'] and f['verkligt'] is True),
        'niva': g.get('niva'), 'tokens': tokens, 'usd': (svar or {}).get('total_cost_usd') or 0,
        'sek': ((svar or {}).get('duration_ms') or 0) / 1000,
        'oeniga': sum(1 for j in range(len(fynd)) if (domar[0].get(j) or {}).get('facit') != (domar[1].get(j) or {}).get('facit')),
    }


ARMAR_I_LOPET = set()


def arm_rader(arm):
    rader = []
    for slug in FACIT:
        if arm == 'B':
            for i, j in ((1, 4), (2, 5), (3, 6)):
                a, b = granskning(slug, 'A-%d' % i), granskning(slug, 'A-%d' % j)
                if a and b:
                    rader.append((slug, {
                        'traff': a['traff'] | b['traff'], 'traff_block': a['traff_block'] | b['traff_block'],
                        'falska_block': a['falska_block'] + b['falska_block'], 'block': a['block'] + b['block'],
                        'verkliga_utanfor': a['verkliga_utanfor'] + b['verkliga_utanfor'],
                        'niva': max(a['niva'] or 0, b['niva'] or 0), 'tokens': a['tokens'] + b['tokens'],
                        'usd': a['usd'] + b['usd'], 'sek': max(a['sek'], b['sek']),
                        'jaccard': len(a['traff'] & b['traff']) / len(a['traff'] | b['traff']) if a['traff'] | b['traff'] else 1.0,
                        'oeniga': a['oeniga'] + b['oeniga']}))
        else:
            for n in range(1, 7 if arm == 'A' and 'B' not in ARMAR_I_LOPET else 4):
                r = granskning(slug, '%s-%d' % (arm, n))
                if r:
                    rader.append((slug, r))
    return rader


def main():
    ut = ['| Arm | n | Träffar omdöme, snitt per bygge | Träffar alla, snitt per bygge | Träffar med blockerande, omdöme | '
          'Falska blockerande | Blockerande | Verkliga utanför facit | Nivå 0/1/2 | Överensstämmelse | Tokens | Tid s |',
          '|' + '---|' * 12]
    per_fel = {}
    namn = sorted({r.name.rsplit('-', 1)[0] for s in FACIT for r in (G / s / 'rot' / 'kunder' / s / 'ab-granskare').glob('*-*')})
    armar = ['A'] + (['B'] if all((G / s / 'rot' / 'kunder' / s / 'ab-granskare' / 'A-6').is_dir() for s in FACIT) else []) + [a for a in namn if a != 'A']
    ARMAR_I_LOPET.update(armar)
    for arm in armar:
        rader = arm_rader(arm)
        if not rader:
            continue
        m = lambda f: st.mean(f(s, r) for s, r in rader)  # noqa: E731
        niv = [r['niva'] for _, r in rader]
        jac = [r['jaccard'] for _, r in rader if 'jaccard' in r]
        ut.append('| %s | %d | %.1f av %.1f | %.1f av %.1f | %.1f | %.1f | %.1f | %.1f | %d/%d/%d | %s | %.0f k | %.0f |' % (
            arm, len(rader), m(lambda s, r: len(r['traff'] & OMDOME[s])), m(lambda s, r: len(OMDOME[s])),
            m(lambda s, r: len(r['traff'])), m(lambda s, r: len(ALLA[s])), m(lambda s, r: len(r['traff_block'] & OMDOME[s])),
            m(lambda s, r: r['falska_block']), m(lambda s, r: r['block']), m(lambda s, r: r['verkliga_utanfor']),
            niv.count(0), niv.count(1), niv.count(2), '%.2f' % st.mean(jac) if jac else '–',
            m(lambda s, r: r['tokens']) / 1000, m(lambda s, r: r['sek'])))
        for s, r in rader:
            for fid in r['traff']:
                per_fel.setdefault(fid, {}).setdefault(arm, 0)
                per_fel[fid][arm] += 1
    antal = {arm: len(arm_rader(arm)) // len(FACIT) for arm in armar}
    ut += ['', '| Facitfel | Maskin | ' + ' | '.join('%s (av %d)' % (a, antal[a]) for a in armar) + ' |', '|---|---|' + '---|' * len(armar)]
    for s, fl in FACIT.items():
        for f in fl:
            p = per_fel.get(f['id'], {})
            ut.append('| %s | %s | ' % (f['id'], 'ja' if f['maskin'] else '') + ' | '.join(str(p.get(a, 0)) for a in armar) + ' |')
    (G / 'RESULTAT.md').write_text('\n'.join(ut) + '\n', encoding='utf-8')
    print('\n'.join(ut))


if __name__ == '__main__':
    main()
