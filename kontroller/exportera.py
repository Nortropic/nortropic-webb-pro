#!/usr/bin/env python3
"""exportera.py — leveransen: ett självständigt kundrepo ur sajten; att bygget är godkänt prövas inte
(kunskap/lansering.md). Codex via ägaren 2026-10-05, leveransluckorna: exporten saknades, formuläret var en demo.

    .venv/bin/python kontroller/exportera.py <slug> [--kandidat kNN] [--ut KATALOG] [--git] [--inget-bygge]

Kundrepot får sajtens källor (src/, public/, astro.config.mjs, tsconfig.json, DESIGN.md), leveransens låsta beroenden
(`mall/leverans/package.json` och `package-lock.json`: mallens paket, Vercel-adaptern och Vercel Blob, granskade med
`npm audit`), formulärets serverfunktion (`src/pages/api/forfragan.js`), felsidan, README, `.gitignore`,
`.env.example`, `vercel.json` och `LICENSER.md`. Nortropics underlag (referenser, intervjuer, domar, råmaterial) följer
aldrig med. Läckagekontrollen fäller exporten om en fil nämner repots lokala vägar, interna filer eller en nyckel.
Bygget verifieras i en tom katalog utanför Nortropics repo (`npm ci` och `npm run build`) innan exporten räknas som
klar. Med --git blir katalogen ett git-repo med en första commit på `main` (lokalt; inget skickas någonstans).

Utkatalogen är som standard `kunder/<slug>/kundrepo/` (utanför git); en tidigare export flyttas till
`kunder/<slug>/kundrepo-tidigare/<tid>/` (raderas aldrig). Slutkod 0 klar, 1 läckage eller bygget föll, 2 fel i anropet.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
LEVERANS = ROOT / 'mall' / 'leverans'
MALL = ROOT / 'mall' / 'astro'
KALLOR = ('astro.config.mjs', 'tsconfig.json', 'DESIGN.md')
KATALOGER = ('src', 'public')
TEXTFILER = ('.astro', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.css', '.json', '.md', '.html', '.svg', '.txt', '.example', '.yml', '.yaml')
# en fil i kundrepot får aldrig nämna en lokal sökväg, Nortropics privata underlag (referenser, intervjuer, domar,
# råmaterial) eller en nyckel; det fäller exporten. En hänvisning till Nortropics publika verktyg (kontroller/design.py i
# en kommentar) redovisas men fäller inte: repot och verktygen är publika
LACKA = [(re.compile(p), skal) for p, skal in (
    (r'/Users/|/private/tmp/|/home/[a-z]', 'en lokal sökväg'),
    (r'\bunderlag/[a-z0-9-]+/|LARDOMAR-original|DESIGNDOMAR|RIKTNINGSHISTORIK|REFERENSUPPDRAG|TJANSTEUPPDRAG|/kalibrering/', 'Nortropics privata underlag'),
    (r'\bre_[A-Za-z0-9]{6,}_[A-Za-z0-9]{16,}|\bre_[A-Za-z0-9]{16,}|\bsk-[A-Za-z0-9_-]{20,}|\bghp_[A-Za-z0-9]{20,}|\bvercel_blob_rw_[A-Za-z0-9_]{10,}', 'en nyckel'),
    (r'(RESEND_API_KEY|BLOB_READ_WRITE_TOKEN|REFERO_MCP_TOKEN)[ \t]*=[ \t]*[^\s#]', 'ett nyckelvärde'),
)]
HANVISNINGAR = re.compile(r'nortropic-webb-pro|\bkontroller/[a-z_]+\.py')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def kopiera(kalla, mal):
    """Filerna under kalla till mal, utan att följa eller kopiera någon länk."""
    for katalog, kataloger, filer in os.walk(kalla, followlinks=False):
        kataloger[:] = sorted(k for k in kataloger if not (Path(katalog) / k).is_symlink() and k not in ('node_modules', '.astro', 'dist'))
        for fn in sorted(filer):
            p = Path(katalog) / fn
            if p.is_symlink() or not p.is_file() or fn == '.DS_Store':
                continue
            m = Path(mal) / p.relative_to(kalla)
            m.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, m)


def installerade_extra(sajt, bas):
    """Sajtens egna beroenden utöver leveransens (typsnitt ur kontroller/typsnitt.py), med den installerade versionen:
    manifestets och de typsnitt som koden importerar (en kandidats manifest är en ögonblicksbild, och typsnitt som
    installeras under sessionen hamnar i sajtens delade node_modules; den oberoende granskningen 2026-10-05, fynd 12)."""
    try:
        egna = (json.loads((sajt / 'package.json').read_text(encoding='utf-8')).get('dependencies') or {})
    except (OSError, ValueError):
        egna = {}
    importerade = set()
    for f in (sajt / 'src').rglob('*') if (sajt / 'src').is_dir() else []:
        if f.is_file() and f.suffix in ('.astro', '.js', '.mjs', '.ts', '.jsx', '.tsx', '.css'):
            importerade.update(re.findall(r"""['"](@fontsource(?:-variable)?/[a-z0-9-]+)""", f.read_text(encoding='utf-8', errors='replace')))
    ut = {}
    for namn in sorted(set(egna) | importerade):
        if namn in bas:
            continue
        try:
            ut[namn] = json.loads((sajt / 'node_modules' / namn / 'package.json').read_text(encoding='utf-8'))['version']
        except (OSError, ValueError, KeyError):
            if namn in egna:
                ut[namn] = egna[namn]
    return ut


def med_adapter(text):
    """astro.config.mjs med Vercel-adaptern: sidorna förrenderas, formulärets funktion körs på servern."""
    if '@astrojs/vercel' in text:
        return text
    text = text.replace("import { defineConfig", "import vercel from '@astrojs/vercel';\nimport { defineConfig", 1)
    if "output: 'static'," not in text:
        raise RuntimeError("astro.config.mjs saknar raden output: 'static',")
    return text.replace("output: 'static',", "output: 'static',\n  adapter: vercel(),  // formulärets funktion på servern; sidorna förrenderas", 1)


def licenser(slug, sajt, mal):
    rader = ['# Licenser och källor', '', 'Bilderna i `src/assets/` är verksamhetens egna, publicerade med verksamhetens tillstånd, eller '
             'licensierat material; källan och licensen för varje bild som inte är verksamhetens står nedan.']
    lic = UNDERLAG / slug / 'bilder' / 'LICENSER.md'
    if lic.is_file() and not lic.is_symlink():
        rader += ['', lic.read_text(encoding='utf-8').strip()]
    typsnitt = []
    for p in sorted((sajt / 'node_modules' / '@fontsource').glob('*/package.json')) + sorted((sajt / 'node_modules' / '@fontsource-variable').glob('*/package.json')):
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
            typsnitt.append('- %s %s: %s' % (d.get('name'), d.get('version'), d.get('license') or 'se paketet'))
        except (OSError, ValueError):
            continue
    if typsnitt:
        rader += ['', '## Typsnitt', ''] + typsnitt
    (mal / 'LICENSER.md').write_text('\n'.join(rader) + '\n', encoding='utf-8')


def hanvisningar(mal):
    """Filerna som hänvisar till Nortropics publika repo eller verktyg (redovisas, fäller inte)."""
    return sorted({str(p.relative_to(mal)) for p in Path(mal).rglob('*') if p.is_file() and '.git' not in p.parts
                   and 'node_modules' not in p.parts and p.suffix.lower() in TEXTFILER and p.name != 'package-lock.json'
                   and HANVISNINGAR.search(p.read_text(encoding='utf-8', errors='replace'))})


def lackor(mal):
    """[(fil, skäl)] för varje textfil i kundrepot som nämner en lokal sökväg, Nortropics privata underlag eller en nyckel."""
    ut = []
    for p in sorted(Path(mal).rglob('*')):
        if '.git' in p.parts or 'node_modules' in p.parts or not p.is_file() or p.suffix.lower() not in TEXTFILER and p.name not in ('.gitignore', '.env.example'):
            continue
        if p.name == 'package-lock.json':
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        for monster, skal in LACKA:
            if monster.search(text):
                ut.append((str(p.relative_to(mal)), skal))
    return ut


def verifiera_bygge(mal, logg=None):
    """Kundrepot bygger på egen hand: en kopia i en tom katalog utanför Nortropics repo, npm ci utan installationsskript
    (paketens kod körs inte), och bygget innanför processgränsen (kontroller/processgrans.py, kor_i_katalog: skrivning
    bara i kopian, inget nät och en miljö utan nycklar; den oberoende granskningen 2026-10-05, fynd 2). Ger (ok, text)."""
    import processgrans
    import korregister
    tmp = Path(korregister.egen_tmp('nwp-kundrepo-', 'exportera'))  # registrerad som körningens egen (städregeln, 2026-10-07)
    try:
        kopiera(mal, tmp / 'repo')
        repo = tmp / 'repo'
        r = subprocess.run(['npm', 'ci', '--no-audit', '--no-fund', '--ignore-scripts'], cwd=repo, capture_output=True, text=True, timeout=900,
                           env={k: v for k, v in os.environ.items() if not k.startswith(('NWP_', 'CLAUDE'))})
        rader = ['$ npm ci --ignore-scripts → %d' % r.returncode]
        if r.returncode:
            return False, '\n'.join(rader + [(r.stdout + r.stderr)[-1500:]])
        rc, ut = processgrans.kor_i_katalog(repo, [repo / 'node_modules' / '.bin' / 'astro', 'build'])
        rader.append('$ astro build (innanför processgränsen: utan nät, skrivning bara i kopian) → %d' % rc)
        if rc:
            return False, '\n'.join(rader + [ut[-1500:]])
        ut_ = repo / '.vercel' / 'output'
        statiskt = (ut_ / 'static' / 'index.html').is_file()
        funktioner = sorted(str(p.relative_to(ut_)) for p in (ut_ / 'functions').glob('*.func')) if (ut_ / 'functions').is_dir() else []
        rader.append('.vercel/output/static/index.html: %s; funktioner: %s' % ('finns' if statiskt else 'saknas', ', '.join(funktioner) or 'inga'))
        return statiskt and bool(funktioner), '\n'.join(rader)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def exportera(slug, kandidat=None, ut=None, git=False, bygg=True):
    sajt = KUNDER / slug / ('kandidater/%s/sajt' % kandidat if kandidat else 'sajt')
    if not (sajt / 'package.json').is_file() or not (sajt / 'src' / 'pages' / 'index.astro').is_file():
        raise ValueError('%s saknar package.json eller startsidan' % sajt.relative_to(ROOT))
    mal = Path(ut) if ut else KUNDER / slug / 'kundrepo'
    if mal.exists():
        undan = KUNDER / slug / 'kundrepo-tidigare' / nu().replace(':', '')
        undan.parent.mkdir(parents=True, exist_ok=True)
        os.replace(mal, undan)
    mal.mkdir(parents=True)
    for n in KALLOR:
        if (sajt / n).is_file() and not (sajt / n).is_symlink():
            shutil.copyfile(sajt / n, mal / n)
    for k in KATALOGER:
        if (sajt / k).is_dir() and not (sajt / k).is_symlink():
            kopiera(sajt / k, mal / k)
    if not (mal / 'src' / 'pages' / 'fel.astro').is_file():
        shutil.copyfile(MALL / 'src' / 'pages' / 'fel.astro', mal / 'src' / 'pages' / 'fel.astro')
    (mal / 'src' / 'pages' / 'api').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LEVERANS / 'forfragan.js', mal / 'src' / 'pages' / 'api' / 'forfragan.js')
    (mal / 'astro.config.mjs').write_text(med_adapter((mal / 'astro.config.mjs').read_text(encoding='utf-8')), encoding='utf-8')
    paket = json.loads((LEVERANS / 'package.json').read_text(encoding='utf-8'))
    extra = installerade_extra(sajt, paket['dependencies'])
    paket['name'] = 'kund-%s' % slug
    paket['dependencies'] = dict(sorted({**paket['dependencies'], **extra}.items()))
    (mal / 'package.json').write_text(json.dumps(paket, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    shutil.copyfile(LEVERANS / 'package-lock.json', mal / 'package-lock.json')
    if extra:  # sajtens typsnitt läggs in i låset (exakta versioner, inga installationsskript)
        r = subprocess.run(['npm', 'install', '--package-lock-only', '--ignore-scripts', '--no-audit', '--no-fund'], cwd=mal,
                           capture_output=True, text=True, timeout=600)
        if r.returncode:
            raise RuntimeError('låset kunde inte uppdateras med sajtens typsnitt: %s' % (r.stderr or r.stdout)[-500:])
    try:
        namn = json.loads((UNDERLAG / slug / 'VERKSAMHET.json').read_text(encoding='utf-8')).get('namn') or slug
    except (OSError, ValueError):
        namn = slug
    (mal / 'README.md').write_text((LEVERANS / 'README.md').read_text(encoding='utf-8').replace('{{NAMN}}', namn), encoding='utf-8')
    shutil.copyfile(LEVERANS / 'gitignore', mal / '.gitignore')
    shutil.copyfile(LEVERANS / 'env.example', mal / '.env.example')
    shutil.copyfile(LEVERANS / 'vercel.json', mal / 'vercel.json')
    licenser(slug, sajt, mal)
    res = {'slug': slug, 'kandidat': kandidat, 'ut': str(mal), 'tid': nu(), 'extra': extra, 'lackor': lackor(mal),
           'hanvisningar': hanvisningar(mal)}
    if res['lackor']:
        res['ok'] = False
        return res
    if bygg:
        res['bygge_ok'], res['bygge'] = verifiera_bygge(mal)
        if not res['bygge_ok']:
            res['ok'] = False
            return res
    if git:
        for steg in (['git', 'init', '-q', '-b', 'main'], ['git', 'add', '-A'],
                     ['git', 'commit', '-q', '-m', 'Leverans från Nortropic: %s (%s)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' % (slug, res['tid'])]):
            r = subprocess.run(steg, cwd=mal, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('git %s föll: %s' % (steg[1], (r.stderr or r.stdout)[-300:]))
        res['commit'] = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=mal, capture_output=True, text=True).stdout.strip()
    res['ok'] = True
    return res


def main(argv=None):
    p = argparse.ArgumentParser(prog='exportera', description=__doc__.split('\n\n')[0], allow_abbrev=False)
    p.add_argument('slug')
    p.add_argument('--kandidat')
    p.add_argument('--ut')
    p.add_argument('--git', action='store_true')
    p.add_argument('--inget-bygge', action='store_true')
    a = p.parse_args(argv)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug) or (a.kandidat and not re.fullmatch(r'k\d{2}', a.kandidat)):
        print('slug a–z, 0–9, bindestreck; kandidaten som k01–k12', file=sys.stderr)
        return 2
    krav_slug(a.slug)
    try:
        r = exportera(a.slug, a.kandidat, a.ut, a.git, not a.inget_bygge)
    except (ValueError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        return 2
    for f, s in r.get('lackor') or []:
        print('LÄCKAGE: %s nämner %s' % (f, s))
    if r.get('hanvisningar'):
        print('hänvisningar till Nortropics publika repo eller verktyg (fäller inte): %s' % ', '.join(r['hanvisningar']))
    if r.get('bygge'):
        print(r['bygge'])
    besked = ('Exporterat utan verifierat bygge (--inget-bygge)' if a.inget_bygge else 'Klart') if r['ok'] else 'Inte klart'
    print('%s: %s%s' % (besked, r['ut'], (' (commit %s)' % r['commit'][:12]) if r.get('commit') else ''))
    return 0 if r['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
