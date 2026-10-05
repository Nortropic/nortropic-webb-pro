#!/usr/bin/env python3
"""gruppera.py — ägarens domar och granskarens blockerande fynd från varje omgång grupperade i kategorier med antal; den största
kategorin blir en vilande backlogpost (OpenAI Cookbook, evaluation flywheel: fria etiketter först, sedan kategorier
med antal, och den största styr nästa ändring).

    .venv/bin/python kontroller/gruppera.py [--torr] [--prov]

Startas av dashboarden efter var femte dom, eller för hand. --torr skriver bara uppdraget; --prov kör sessionen men
skriver varken kunskap/GRUPPERING.md, backlogpost eller commit.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
sys.path.insert(0, str(ROOT / 'kontroller'))
from slugvakt import inte_i_bygge  # noqa: E402  (revisionen 2026-10-03, F1: körs aldrig inne i ett bygge)
import backlog as bl  # noqa: E402
import nastlad  # noqa: E402  (nästlade sessioner: inget automatiskt minne)

SCHEMA = ROOT / 'kritik' / 'SCHEMA-gruppering.json'
UT = ROOT / 'kunskap' / 'GRUPPERING.md'


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def lardomar_fil():
    """Ägarens domar: ordagrant i underlag/LARDOMAR-original.md när den finns (privat), annars den publika LARDOMAR.md."""
    p = ROOT / 'underlag' / 'LARDOMAR-original.md'
    return p if p.is_file() else ROOT / 'LARDOMAR.md'


def antal_domar():
    return len(re.findall(r'^## L\d+ ', lardomar_fil().read_text(encoding='utf-8'), re.M))


def granskningsfynd():
    """Varje omgångs blockerande fynd, inte bara slutfilens: ett fel som byggaren rättar i varje bygge men gör om i
    nästa syns först när omgångarna läses (AI LABS, loop engineering: läs resultatet av varje varv)."""
    rader = []
    for p in sorted(KUNDER.iterdir()) if KUNDER.is_dir() else []:
        if not p.is_dir() or p.name.startswith('rokprov'):
            continue
        rundor = sorted((p / 'granskning').glob('runda-*/GRANSKNING.json')) if (p / 'granskning').is_dir() else []
        if not rundor and (p / 'granskning' / 'GRANSKNING.json').is_file():
            rundor = [p / 'granskning' / 'GRANSKNING.json']
        sista = las(rundor[-1]) if rundor else None
        kvar = {(f.get('kriterium'), f.get('standardpunkt')) for f in (sista or {}).get('blockerande') or []}
        for fil in rundor:
            g = las(fil) or {}
            omgang = g.get('runda') or fil.parent.name.replace('runda-', '')
            for f in g.get('blockerande') or []:
                if fil == rundor[-1]:
                    lage = 'sista omgången'
                else:
                    lage = 'kvar i sista omgången' if (f.get('kriterium'), f.get('standardpunkt')) in kvar else 'rättat före sista omgången'
                rader.append('- granskning %s omgång %s (%s): [%s%s] %s' % (
                    p.name, omgang, lage, f.get('kriterium'), ', grad %s' % f['allvarlighet'] if f.get('allvarlighet') else '',
                    ' '.join(str(f.get('observation', '')).split())[:400]))
    return rader


def uppdrag():
    return '\n'.join([
        'Gruppera fynden nedan i kategorier. Arbeta i två steg: sätt först en fri etikett på varje fynd (vad gick fel, med',
        'egna ord), samla sedan etiketterna i 4–10 kategorier med antal. En kategori är ett återkommande problem i hur vi',
        'bygger, inte ett enskilt bygge. Källorna är ägarens domar i %s (läs hela filen, varje L-post och AB-post)' % lardomar_fil().relative_to(ROOT),
        'och granskarens blockerande fynd nedan, från varje omgång. Ägarens domar väger tyngst. Ett fel som rättas inom',
        'ett bygge men återkommer i nästa bygge är en kategori, inte ett löst problem.', '',
        'Resultatet blir publikt (kunskap/GRUPPERING.md): skriv inga personuppgifter ur domarna. Företagsnamn får stå, inte',
        'privatpersoners namn, nummer, adresser eller hälsa (BESLUT.md 2026-10-03).', '',
        'Föreslå en enda ändring mot den största kategorin: vilken fil (helst .claude/skills/bygg-sajt/SKILL.md, en fil i',
        'kunskap/ eller kritik/GRANSKARE.md), vad som ändras, varför och hur man ser att det är gjort. Liten nog att läsa',
        'på fem minuter. Läs gärna kunskap/byggstandard.md och kunskap/teoretisk-grund.md för att knyta förslaget till en',
        'punkt eller princip. Du ändrar inga filer.', '',
        'Granskarens blockerande fynd:', *(granskningsfynd() or ['- inga']), ''])


def main(argv=None):
    p = argparse.ArgumentParser(prog='gruppera', description=__doc__.split('\n\n')[0])
    p.add_argument('--torr', action='store_true')
    p.add_argument('--prov', action='store_true')
    a = p.parse_args(argv)
    inte_i_bygge('gruppera.py')
    text = uppdrag()
    if a.torr:
        print(text)
        return 0
    claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
    miljo = nastlad.miljo()
    r = subprocess.run([claude, '-p', '--max-turns', '40', '--permission-mode', 'dontAsk', '--output-format', 'json',
                        '--setting-sources', 'project,local', '--strict-mcp-config', '--model', 'opus[1m]', '--effort', 'high',
                        '--json-schema', SCHEMA.read_text(encoding='utf-8'), '--allowedTools', 'Read', 'Glob', 'Grep',
                        '--disallowedTools', 'Write', 'Edit', 'Bash'],
                       input=text.encode(), capture_output=True, cwd=str(ROOT), env=miljo, timeout=1200)
    try:
        res = json.loads(r.stdout or b'{}').get('structured_output')
    except ValueError:
        res = None
    if not isinstance(res, dict):
        print('ingen giltig gruppering (kod %s): %s' % (r.returncode, (r.stderr or b'').decode(errors='replace')[-300:]))
        return 1
    n = antal_domar()
    tid = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    md = ['# Gruppering av domar och granskningar', '', '%s, efter %d domar. Största kategorin: **%s**.' % (tid, n, res['storsta']), '',
          '| Kategori | Antal | Källor |', '|---|---|---|']
    md += ['| %s | %d | %s |' % (k['namn'], k['antal'], ', '.join(k['kallor'])) for k in sorted(res['kategorier'], key=lambda k: -k['antal'])]
    md += ['', '## Förslag mot den största kategorin', '', '- Fil: %s' % res['forslag']['fil'], '- Ändring: %s' % res['forslag']['andring'],
           '- Varför: %s' % res['forslag']['varfor'], '- Klart när: %s' % res['forslag']['klart'], '']
    print('\n'.join(md))
    if a.prov:
        return 0
    UT.write_text('\n'.join(md), encoding='utf-8')
    pid = bl.ny('dom', 'Gruppering efter %d domar: %s' % (n, res['storsta'][:80]),
                'Den största kategorin i ägarens domar och granskarens fynd (kunskap/GRUPPERING.md).',
                forslag='%s: %s' % (res['forslag']['fil'], res['forslag']['andring']), klart=res['forslag']['klart'],
                kallref='kunskap/GRUPPERING.md %s' % tid, prio='hog')
    g = lambda *x: subprocess.run(['git', '-C', str(ROOT), *x], capture_output=True, text=True, timeout=60)  # noqa: E731
    filer = ['kunskap/GRUPPERING.md', 'backlog/']
    if g('add', *filer).returncode == 0 and g('commit', '-q', '-m', 'Gruppering efter %d domar: %s (%s)' % (n, res['storsta'][:60], pid), '--', *filer).returncode == 0:
        g('push', '-q', 'origin', 'main')
    print('backlogpost %s' % pid)
    return 0


if __name__ == '__main__':
    sys.exit(main())
