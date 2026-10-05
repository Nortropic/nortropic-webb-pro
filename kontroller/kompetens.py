#!/usr/bin/env python3
"""kompetens.py — kompetenserna i skapandeflödet (kunskap/metodkarta.md, avsnittet Kompetenserna): vilken kompetens som
arbetar i vilket pass, med vilka skills fullständiga instruktioner, vilka verktyg och vilka MCP:er.

Ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA". Codex samma dag via ägaren: varje
kompetens ska ha en obligatorisk uppgift, tillgång till sina fullständiga relevanta instruktioner och fungerande
verktyg; att en fil öppnats räcker inte, förbättringen ska synas i sidan.

    .venv/bin/python kontroller/kompetens.py --prova      (varje block går att läsa och varje fil finns; slutkod 0/1)
    .venv/bin/python kontroller/kompetens.py --visa kritik (passets kompetenser, filer och verktyg)

Blocken i kartan, ett per kompetens:

    ```kompetens <id>
    namn: …
    uppgift: …
    pass: planprovning, skapa, …
    läs: impeccable/SKILL.md; impeccable/reference/new-work.md; kunskap/bild.md
    verktyg: ui-ux-pro-max, förhandsvisning, detektor, design
    mcp: refero, mobbin, trybloom
    visar: …
    ```
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metod  # noqa: E402  kalla(): repots kunskap/ eller en skills fil

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r'^```kompetens[ \t]+(?P<id>[a-z]+)[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)
PASS = ('planprovning', 'skapa', 'ux', 'rorelse', 'mobil', 'kritik', 'fordjupa')
PASSNAMN = {'planprovning': 'planprövningen', 'skapa': 'skissen', 'ux': 'UX och innehåll', 'rorelse': 'interaktion och rörelse',
            'mobil': 'mobil och tillgänglighet', 'kritik': 'visuell kritik och slutbearbetning', 'fordjupa': 'fördjupningen'}

# verktygen per namn: allowedTools-mönster (slug och kandidat fylls i) och raden i prompten
VERKTYG = {
    'ui-ux-pro-max': (['Bash(.venv/bin/python -B .claude/skills/ui-ux-pro-max/scripts/search.py *)'],
                      'UI UX Pro Max sökning och designsystem: `.venv/bin/python -B .claude/skills/ui-ux-pro-max/scripts/search.py "<bransch och '
                      'stil>" --design-system` och `--domain <style|color|typography|ux|landing>` (databasen är engelsk; sök med flera ord)'),
    'förhandsvisning': ([], 'förhandsvisningen (`.venv/bin/python kontroller/forhandsvisa.py <slug> --kandidat <id>`, med `--mellan` för 768)'),
    'detektor': (['Bash(.venv/bin/python kontroller/detektor.py *)'],
                 'Impeccables detektor: `.venv/bin/python kontroller/detektor.py <slug> --kandidat <id>` (antimönster och designbrister i den '
                 'byggda sidan, i 390 och 1440)'),
    'design': (['Bash(.venv/bin/python kontroller/design.py *)'], 'DESIGN.md-kontrollen: `.venv/bin/python kontroller/design.py <slug> --kandidat <id> [--skriv]`'),
}
MCP = {  # Refero och Mobbin: referenstjänsternas egna verktygslistor (en källa); Trybloom: bara sökningen
    'refero': None, 'mobbin': None,
    'trybloom': ['mcp__claude_ai_Trybloom__find_reference_ads', 'mcp__claude_ai_Trybloom__search_docs'],
}


def mcp_verktyg(namn):
    if MCP.get(namn) is None:
        import referenstjanster
        return list(referenstjanster.TJANSTER[namn]['verktyg'])
    return list(MCP[namn])


MCPNAMN = {'refero': 'Refero (stilar, skärmar, sajter och flöden)', 'mobbin': 'Mobbin (skärmar, sektioner och flöden)',
           'trybloom': 'Trybloom (referensannonser)'}


class KompetensFel(Exception):
    pass


def tolka(text=None):
    """{id: {'id', 'namn', 'uppgift', 'pass': [...], 'las': [...], 'verktyg': [...], 'mcp': [...], 'visar'}} ur kartans block."""
    text = metod.KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {}
    for m in BLOCK.finditer(text):
        k = {'id': m.group('id')}
        for rad in m.group('rader').splitlines():
            nyckel, _, varde = rad.partition(':')
            k[nyckel.strip()] = varde.strip()
        ut[k['id']] = {'id': k['id'], 'namn': k.get('namn', k['id']), 'uppgift': k.get('uppgift', ''),
                       'pass': [x.strip() for x in k.get('pass', '').split(',') if x.strip()],
                       'las': [x.strip() for x in k.get('läs', '').split(';') if x.strip()],
                       'verktyg': [x.strip() for x in k.get('verktyg', '').split(',') if x.strip()],
                       'mcp': [x.strip() for x in k.get('mcp', '').split(',') if x.strip()], 'visar': k.get('visar', '')}
    return ut


def vag(fil):
    """Filens väg relativt repots rot (en skills fil ligger under .claude/skills/)."""
    return metod.kalla(fil).relative_to(metod.ROOT).as_posix()


def prova(text=None):
    """Fel i kompetensblocken: varje fil finns, varje pass, verktyg och MCP är känt, och varje pass har en kompetens."""
    fel = []
    k = tolka(text)
    if not k:
        return ['metodkartan saknar kompetensblock']
    for kid, x in k.items():
        for f in x['las']:
            p = metod.kalla(f)
            if not p.is_file() or p.is_symlink():
                fel.append('%s: %s finns inte' % (kid, f))
        fel += ['%s: okänt pass %s' % (kid, p_) for p_ in x['pass'] if p_ not in PASS]
        fel += ['%s: okänt verktyg %s' % (kid, v) for v in x['verktyg'] if v not in VERKTYG]
        fel += ['%s: okänd MCP %s' % (kid, m) for m in x['mcp'] if m not in MCP]
        if not x['uppgift'] or not x['las']:
            fel.append('%s: uppgiften eller filerna saknas' % kid)
    fel += ['passet %s har ingen kompetens' % p_ for p_ in PASS if not for_pass(p_, k)]
    return fel


def for_pass(pass_, k=None):
    k = tolka() if k is None else k
    return [x for x in k.values() if pass_ in x['pass']]


def lasfiler(pass_, k=None):
    """Filerna som passet läser hela, i kompetensernas ordning, utan dubletter (vägar relativt roten)."""
    ut = []
    for x in for_pass(pass_, k):
        for f in x['las']:
            v = vag(f)
            if v not in ut:
                ut.append(v)
    return ut


def verktyg(pass_, slug, kid=None, k=None):
    """allowedTools-mönster för passets verktyg och MCP:er (utöver passets egna skriv- och byggverktyg)."""
    ut = ['Skill', 'ToolSearch']
    for x in for_pass(pass_, k):
        for v in x['verktyg']:
            ut += [m.replace('<slug>', slug).replace('<id>', kid or '') for m in VERKTYG[v][0]]
        for m in x['mcp']:
            ut += mcp_verktyg(m)
    return list(dict.fromkeys(ut))


def prompt_rader(pass_, slug, kid=None, k=None):
    """Raderna i passets prompt: varje kompetens med sin uppgift, filerna som läses hela, verktygen och MCP:erna, och vad
    passets svar ska visa. Obligatoriskt: att en fil öppnats räcker inte."""
    k = tolka() if k is None else k
    kompetenser = for_pass(pass_, k)
    rader = ['Kompetenserna i %s (kunskap/metodkarta.md, Kompetenserna) är obligatoriska. Läs varje fil nedan HEL med Read innan' % PASSNAMN[pass_],
             'du ändrar något (en fil större än en läsning läses i delar med offset och limit tills alla rader är lästa), eller ladda',
             'skillen med skillverktyget. Tillämpa dem med omdöme: där en skills standardrecept säger emot ett annat, ett ägarbeslut',
             'eller kundens behov avgör Avgörandena i metoden; säg i svaret var en skill inte passade och varför. Följ Impeccables',
             'arbetsflöde: rätt arbetsbeskrivning för uppgiften, craft-floor.md direkt före varje ändring i gränssnittet, och',
             'kontroll i avgränsade omgångar (bygg, inspektera mobil och dator tillsammans, rätta allt i en omgång, bekräfta högst en',
             'gång till).']
    for x in kompetenser:
        rader += ['', '%s: %s' % (x['namn'], x['uppgift'])]
        rader += ['- läs hela: ' + ', '.join(vag(f) for f in x['las'])]
        for v in x['verktyg']:
            rader.append('- verktyg: ' + VERKTYG[v][1].replace('<slug>', slug).replace('<id>', kid or '<id>'))
        if x['mcp']:
            rader.append('- MCP: ' + ', '.join(MCPNAMN[m] for m in x['mcp']) + '; sök med branschen och uppgiften, aldrig kundens namn, ort,'
                         ' webbadress eller nummer (en vakt stoppar sådana anrop)')
        rader.append('- passet visar: ' + x['visar'])
    return rader


def kvitto(sessioner, pass_, skrivprefix=None, k=None):
    """Kvittot ur transkripten: filerna som lästs hela före första ändringen (eller alls), skillverktygets anrop och
    MCP-anropen. Ett transkript som saknas gör kvittot ej verifierat."""
    import bildkedja
    filer = lasfiler(pass_, k)
    lasta, fore, skill, mcp, sedda = set(), set(), [], [], 0
    for s in sessioner:
        sid = s.get('session_id') if isinstance(s, dict) else s
        ml = bildkedja.metodlasning(sid, filer, skrivprefix=skrivprefix)
        if not ml.get('verifierad'):
            continue
        sedda += 1
        fore.update(ml.get('fore') or [])
        lasta.update((ml.get('fore') or []) + (ml.get('efter') or []))
        skill += ml.get('skill_anrop') or []
        t = bildkedja.transkript(sid)
        for h in bildkedja.handelser(t) if t else []:
            if h[0] == 'anrop' and str(h[2]).startswith('mcp__'):
                mcp.append(str(h[2]))
    return {'verifierad': sedda > 0, 'filer': filer, 'lasta': [f for f in filer if f in lasta], 'saknas': [f for f in filer if f not in lasta],
            'fore_forsta_andring': [f for f in filer if f in fore], 'skill_anrop': sorted(set(skill)),
            'mcp_anrop': {m: mcp.count(m) for m in sorted(set(mcp))}}


def main(argv=None):
    p = argparse.ArgumentParser(prog='kompetens', description=__doc__.split('\n\n')[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prova', action='store_true')
    g.add_argument('--visa', choices=PASS)
    a = p.parse_args(argv)
    if a.prova:
        fel = prova()
        print('\n'.join('- ' + f for f in fel) if fel else 'kompetenserna håller: %d kompetenser, %d pass' % (len(tolka()), len(PASS)))
        return 1 if fel else 0
    print('\n'.join(prompt_rader(a.visa, '<slug>')))
    print('\nverktyg: ' + ', '.join(verktyg(a.visa, '<slug>', '<id>')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
