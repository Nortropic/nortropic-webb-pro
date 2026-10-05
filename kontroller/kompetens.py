#!/usr/bin/env python3
"""kompetens.py — rollerna i skapandeflödet (kunskap/metodkarta.md, avsnittet Kompetenserna): vilken roll som arbetar i
vilket pass, med vilken kärna (läses hel), vilka alternativ (väljs efter riktningen och läses hela), vilka verktyg och
vilka MCP:er. Samma block ger sessionens behörigheter och raderna i passets uppdrag: en källa.

Ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA". Ägarens uppdrag 18:53Z, punkt 5:
varje roll läser de fullständiga relevanta delarna, utan tunna sammanfattningar och utan att varje metodtext läggs i
varje uppdrag. Codex via ägaren 19:04Z, punkt 7: en sammanhängande tillämpning per riktning, full tillgång till
alternativen och fullständig läsning av den valda metoden.

    .venv/bin/python kontroller/kompetens.py --prova       (varje block går att läsa och varje fil finns; slutkod 0/1)
    .venv/bin/python kontroller/kompetens.py --visa skapa   (passets roller, filer, verktyg och storlek)

Blocken i kartan, ett per roll:

    ```kompetens <id>
    namn: …
    uppgift: …
    pass: skapa, fordjupa
    kärna: refero-design/SKILL.md; impeccable/reference/craft-floor.md; kunskap/bild.md
    välj: taste-minimalist/SKILL.md; hallmark/references/macrostructures.md
    verktyg: uxsok, förhandsvisning, detektor, design
    mcp: refero, mobbin, trybloom
    visar: …
    ```

MCP:erna står aldrig i --allowedTools: kundvakten (kontroller/kundvakt.py) öppnar varje rent anrop uttryckligen, och en
vakt som inte kan pröva lämnar anropet åt dontAsk, som nekar det (granskning 4, G3).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metod  # noqa: E402  kalla(): repots kunskap/ eller en skills fil

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r'^```kompetens[ \t]+(?P<id>[a-z]+)[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)
PASS = ('planera', 'planprovning', 'skapa', 'fordjupa', 'rorelse', 'granskning')
PASSNAMN = {'planera': 'planeringen', 'planprovning': 'planprövningen', 'skapa': 'skissen', 'fordjupa': 'fördjupningen',
            'rorelse': 'interaktion och rörelse', 'granskning': 'tillgänglighet och visuell granskning'}
FORHAND = '.venv/bin/python kontroller/forhandsvisa.py <slug> --kandidat <id>'

# verktygen per namn: allowedTools-mönster (slug och kandidat fylls i, aldrig ett fritt *-argument som kan skriva utanför
# den egna kandidaten; granskning 4, G12) och raden i prompten
VERKTYG = {
    'uxsok': (['Bash(.venv/bin/python -B kontroller/uxsok.py *)'],
              'UI UX Pro Max sökning och designsystem (läsande, sparar inget): `.venv/bin/python -B kontroller/uxsok.py "<bransch och '
              'stil>" --design-system` och `--domain <style|color|typography|ux|landing>` (databasen är engelsk; sök med flera ord)'),
    'förhandsvisning': ([], 'förhandsvisningen: `%s` (mobil och dator), `--mellan` för 768, `--sida /<väg>/` för en undersida, och '
                            'interaktionsvägen `--tillstand tangentbord,reflow,reducerad` med `--meny`, `--hover` eller `--fokus` och en '
                            'CSS-väljare' % FORHAND),
    'detektor': (['Bash(.venv/bin/python kontroller/detektor.py <slug> --kandidat <id>)', 'Bash(.venv/bin/python kontroller/detektor.py <slug> --kandidat <id> --json)'],
                 'Impeccables detektor: `.venv/bin/python kontroller/detektor.py <slug> --kandidat <id>` (antimönster och designbrister i den '
                 'byggda sidan); varje fynd prövas mot ägarbesluten och kundens domar innan det rättas'),
    'design': (['Bash(.venv/bin/python kontroller/design.py <slug> --kandidat <id>)', 'Bash(.venv/bin/python kontroller/design.py <slug> --kandidat <id> --skriv)'],
               'DESIGN.md-kontrollen: `.venv/bin/python kontroller/design.py <slug> --kandidat <id> [--skriv]`'),
}
MCP = {  # Refero och Mobbin: referenstjänsternas egna verktygslistor (en källa); Trybloom: bara sökningen
    'refero': None, 'mobbin': None,
    'trybloom': ['mcp__claude_ai_Trybloom__find_reference_ads', 'mcp__claude_ai_Trybloom__search_docs'],
}
MCPNAMN = {'refero': 'Refero (stilar, skärmar, sajter och flöden)', 'mobbin': 'Mobbin (skärmar, sektioner och flöden)',
           'trybloom': 'Trybloom (referensannonser)'}


def mcp_verktyg(namn):
    if MCP.get(namn) is None:
        import referenstjanster
        return list(referenstjanster.TJANSTER[namn]['verktyg'])
    return list(MCP[namn])


class KompetensFel(Exception):
    pass


def tolka(text=None):
    """{id: {'id', 'namn', 'uppgift', 'pass', 'karna', 'valj', 'verktyg', 'mcp', 'visar'}} ur kartans block. 'läs' är
    det äldre namnet på kärnan."""
    text = metod.KARTA.read_text(encoding='utf-8') if text is None else text
    ut = {}
    for m in BLOCK.finditer(text):
        k = {'id': m.group('id')}
        for rad in m.group('rader').splitlines():
            nyckel, _, varde = rad.partition(':')
            k[nyckel.strip()] = varde.strip()
        lista = lambda s, sep: [x.strip() for x in str(s or '').split(sep) if x.strip()]  # noqa: E731
        karna = lista(k.get('kärna') or k.get('läs'), ';')
        ut[k['id']] = {'id': k['id'], 'namn': k.get('namn', k['id']), 'uppgift': k.get('uppgift', ''),
                       'pass': lista(k.get('pass'), ','), 'karna': karna,
                       'valj': [f for f in lista(k.get('välj'), ';') if f not in karna],
                       'verktyg': lista(k.get('verktyg'), ','), 'mcp': lista(k.get('mcp'), ','), 'visar': k.get('visar', '')}
    return ut


def vag(fil):
    """Filens väg relativt repots rot (en skills fil ligger under .claude/skills/)."""
    return metod.kalla(fil).relative_to(metod.ROOT).as_posix()


def storlek(filer):
    """Tecknen i filerna, för redovisningen (räknat källmaterial, inte uppmätt kontext)."""
    n = 0
    for f in filer:
        try:
            n += len((metod.ROOT / f).read_text(encoding='utf-8', errors='replace'))
        except OSError:
            pass
    return n


def prova(text=None):
    """Fel i kompetensblocken: varje fil finns, varje pass, verktyg och MCP är känt, varje pass har en roll, och varje
    roll har en uppgift och en kärna."""
    fel = []
    k = tolka(text)
    if not k:
        return ['metodkartan saknar kompetensblock']
    for kid, x in k.items():
        for f in x['karna'] + x['valj']:
            p = metod.kalla(f)
            if not p.is_file() or p.is_symlink():
                fel.append('%s: %s finns inte' % (kid, f))
        fel += ['%s: okänt pass %s' % (kid, p_) for p_ in x['pass'] if p_ not in PASS]
        fel += ['%s: okänt verktyg %s' % (kid, v) for v in x['verktyg'] if v not in VERKTYG]
        fel += ['%s: okänd MCP %s' % (kid, m) for m in x['mcp'] if m not in MCP]
        if not x['uppgift'] or not x['karna']:
            fel.append('%s: uppgiften eller kärnan saknas' % kid)
    fel += ['passet %s har ingen roll' % p_ for p_ in PASS if not for_pass(p_, k)]
    return fel


def for_pass(pass_, k=None):
    k = tolka() if k is None else k
    return [x for x in k.values() if pass_ in x['pass']]


def lasfiler(pass_, k=None):
    """Kärnan som passet läser hel, i rollernas ordning, utan dubletter (vägar relativt roten)."""
    ut = []
    for x in for_pass(pass_, k):
        for f in x['karna']:
            v = vag(f)
            if v not in ut:
                ut.append(v)
    return ut


def valbara(pass_, k=None):
    """Alternativen i passet (vägar relativt roten), utom det som redan är kärna."""
    karna, ut = set(lasfiler(pass_, k)), []
    for x in for_pass(pass_, k):
        for f in x['valj']:
            v = vag(f)
            if v not in karna and v not in ut:
                ut.append(v)
    return ut


def verktyg(pass_, slug, kid=None, k=None):
    """allowedTools-mönster för passets verktyg (utöver passets egna skriv- och byggverktyg). Skillverktyget och
    verktygssökningen alltid; MCP:erna aldrig (kundvakten öppnar dem anrop för anrop). Ett verktyg som gäller en
    kandidat ges bara med kandidaten."""
    ut = ['Skill', 'ToolSearch']
    for x in for_pass(pass_, k):
        for v in x['verktyg']:
            for m in VERKTYG[v][0]:
                if '<id>' in m and not kid:
                    continue
                ut.append(m.replace('<slug>', slug).replace('<id>', kid or ''))
    return list(dict.fromkeys(ut))


def mcp_for_pass(pass_, k=None):
    """MCP-verktygen passet har tillgång till genom kundvakten (för kvittot och prompten)."""
    ut = []
    for x in for_pass(pass_, k):
        for m in x['mcp']:
            ut += mcp_verktyg(m)
    return list(dict.fromkeys(ut))


def prompt_rader(pass_, slug, kid=None, k=None):
    """Raderna i passets uppdrag: varje roll med sin uppgift, kärnan som läses hel, alternativen att välja bland,
    verktygen, MCP:erna och vad passet visar."""
    k = tolka() if k is None else k
    roller = for_pass(pass_, k)
    rader = ['Rollerna i %s (kunskap/metodkarta.md, Kompetenserna) är dina arbetsinstruktioner. Läs varje rolls kärna HEL med' % PASSNAMN[pass_],
             'Read innan du ändrar något (en fil större än en läsning läses i delar med offset och limit tills alla rader är lästa),',
             'eller ladda skillen med skillverktyget. Välj sedan bland alternativen de som passar riktningen, läs dem hela, och skriv',
             'valet med skäl, eller varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller kundens behov',
             'avgörs av Avgörandena i metoden, designreglerna och kundens aktuella domar ovan. Följ arbetsflödet: rätt metod för',
             'uppgiften, craft-floor.md direkt före ändringar i gränssnittet, och kontroll i avgränsade omgångar (bygg, inspektera',
             'mobil och dator tillsammans, rätta allt i en omgång, bekräfta högst en gång till).']
    for x in roller:
        rader += ['', '%s: %s' % (x['namn'], x['uppgift'])]
        rader.append('- kärnan, läs hel: ' + ', '.join(vag(f) for f in x['karna']))
        if x['valj']:
            rader.append('- alternativen, välj efter riktningen: ' + ', '.join(vag(f) for f in x['valj']))
        for v in x['verktyg']:
            if v == 'design' and not kid:
                continue
            rader.append('- verktyg: ' + VERKTYG[v][1].replace('<slug>', slug).replace('<id>', kid or '<id>'))
        if x['mcp']:
            rader.append('- MCP: ' + ', '.join(MCPNAMN[m] for m in x['mcp']) + '; sök med branschen och uppgiften, aldrig kundens namn, ort,'
                         ' webbadress eller nummer (kundvakten prövar varje anrop och stoppar sådana)')
        rader.append('- passet visar: ' + x['visar'])
    return rader


def kvitto(sessioner, pass_, skrivprefix=None, k=None):
    """Kvittot ur transkripten: kärnan som lästs hel före första ändringen (eller alls), alternativen som lästs,
    skillverktygets lyckade anrop och MCP-anropen som gav svar (ett nekat eller stoppat anrop räknas inte; granskning 4,
    G7). Flera sessioner (ett omförsök) räknas tillsammans. Ett transkript som saknas gör kvittot ej verifierat."""
    import bildkedja
    filer, val = lasfiler(pass_, k), valbara(pass_, k)
    lasta, fore, skill, mcp, sedda = set(), set(), [], [], 0
    for s in sessioner:
        sid = s.get('session_id') if isinstance(s, dict) else s
        ml = bildkedja.metodlasning(sid, filer + val, skrivprefix=skrivprefix)
        if not ml.get('verifierad'):
            continue
        sedda += 1
        fore.update(ml.get('fore') or [])
        lasta.update((ml.get('fore') or []) + (ml.get('efter') or []))
        skill += ml.get('skill_anrop') or []
        t = bildkedja.transkript(sid)
        h = bildkedja.handelser(t) if t else []
        felade = {x[1] for x in h if x[0] == 'svar' and x[3]}
        for x in h:
            if x[0] == 'anrop' and str(x[2]).startswith('mcp__') and x[1] not in felade:
                mcp.append(str(x[2]))
    return {'verifierad': sedda > 0, 'filer': filer, 'lasta': [f for f in filer if f in lasta], 'saknas': [f for f in filer if f not in lasta],
            'fore_forsta_andring': [f for f in filer if f in fore], 'valda': [f for f in val if f in lasta],
            'skill_anrop': sorted(set(skill)), 'mcp_anrop': {m: mcp.count(m) for m in sorted(set(mcp))}}


def main(argv=None):
    p = argparse.ArgumentParser(prog='kompetens', description=__doc__.split('\n\n')[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prova', action='store_true')
    g.add_argument('--visa', choices=PASS)
    a = p.parse_args(argv)
    if a.prova:
        fel = prova()
        print('\n'.join('- ' + f for f in fel) if fel else 'kompetenserna håller: %d roller, %d pass' % (len(tolka()), len(PASS)))
        return 1 if fel else 0
    print('\n'.join(prompt_rader(a.visa, '<slug>', '<id>')))
    print('\nverktyg: ' + ', '.join(verktyg(a.visa, '<slug>', '<id>')))
    print('MCP genom kundvakten: ' + ', '.join(mcp_for_pass(a.visa)))
    print('kärnan: %d filer, %d tecken; alternativen: %d filer' % (len(lasfiler(a.visa)), storlek(lasfiler(a.visa)), len(valbara(a.visa))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
