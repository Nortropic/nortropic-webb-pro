#!/usr/bin/env python3
"""exportera.py — leveransen: ett självständigt kundrepo ur sajten; att bygget är godkänt prövas inte
(kunskap/lansering.md). Codex via ägaren 2026-10-05, leveransluckorna: exporten saknades, formuläret var en demo.

    .venv/bin/python kontroller/exportera.py <slug> [--kandidat kNN] [--ut KATALOG] [--git] [--inget-bygge]

Kundrepot är en Cloudflare Worker (ägarens beslut 2026-10-09: Cloudflare Workers är målplattform, Vercel är det
inte längre): sajtens källor (src/, public/, astro.config.mjs, tsconfig.json, DESIGN.md) byggs till förrenderade sidor i
dist/, som Workern serverar som Static Assets; bara /api/* körs i Workern (`worker/index.js`, formulärets mottagning i
D1 och R2 före aviseringen). Dessutom: leveransens låsta beroenden (`mall/leverans/package.json` och
`package-lock.json`: mallens paket och Wrangler), `wrangler.jsonc` med kundens namn, D1-schemat (`migrations/`),
säkerhetshuvudena för de statiska filerna (`public/_headers`), felsidan, README, `.gitignore`, `.env.example` och
`LICENSER.md`. Nortropics underlag (referenser, intervjuer, domar, råmaterial) följer aldrig med. Läckagekontrollen fäller
exporten om en fil nämner repots lokala vägar, interna filer eller en nyckel. Bygget verifieras i en tom katalog utanför
Nortropics repo (`npm ci`, `astro build` och `wrangler deploy --dry-run`, utan nät och utan konto) innan exporten räknas
som klar, och dist/ prövas negativt: ingen serverfil, konfiguration, miljöfil eller källkarta får bli en publik fil.
Med --git blir katalogen ett git-repo med en första commit på `main` (lokalt; inget skickas någonstans).

Utkatalogen är som standard `kunder/<slug>/kundrepo/` (utanför git); en tidigare export flyttas till
`kunder/<slug>/kundrepo-tidigare/<tid>/` (raderas aldrig). Slutkod 0 klar, 1 läckage eller bygget föll, 2 fel i anropet.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import uuid
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
    # också i JSON och YAML: namnet inom citattecken före kolon ("CLOUDFLARE_API_TOKEN": "…")
    (r'(RESEND_API_KEY|BLOB_READ_WRITE_TOKEN|REFERO_MCP_TOKEN|CLOUDFLARE_API_TOKEN|CF_API_TOKEN)["\']?[ \t]*[=:][ \t]*["\']?[^\s#"\']', 'ett nyckelvärde'),
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


# Det som aldrig får bli en publik fil i dist/ (Workers Static Assets publicerar hela katalogen): Workerns kod och
# konfiguration, D1-schemat, miljö- och hemlighetsfiler, källkartor och Nortropics underlag (uppdraget 2026-10-09, 8.4)
INTE_PUBLIKT = re.compile(r'(^|/)(worker/|migrations/|wrangler\.(jsonc?|toml)$|\.dev\.vars|\.env|package(-lock)?\.json$|CLAUDE\.md$|DESIGN\.md$|LICENSER\.md$|README\.md$)|\.map$')


def publika_brister(dist):
    """[fil] i dist/ som inte får publiceras; tom lista när katalogen bara har sajtens publika filer."""
    return sorted(str(p.relative_to(dist)) for p in Path(dist).rglob('*') if p.is_file() and INTE_PUBLIKT.search(p.relative_to(dist).as_posix()))


def wrangler_namn(text, slug):
    """wrangler.jsonc med kundens namn i stället för SLUG; allt annat (kompatibilitetsdatum, bindningar) som i mallen."""
    if 'kund-SLUG' not in text:
        raise RuntimeError('mallens wrangler.jsonc saknar platshållaren kund-SLUG')
    return text.replace('kund-SLUG', 'kund-%s' % slug)


def licenser(slug, sajt, mal):
    rader = ['# Licenser och källor', '', 'Tillstånd för bilder och annat kundmaterial är inte verifierat av exportverktyget. '
             'Kontrollera varje tillgång och dess användningsrätt före publicering. Nedan återges befintligt licensunderlag, inte ett nytt godkännande.']
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
        dist = repo / 'dist'
        statiskt = (dist / 'index.html').is_file()
        huvuden = (dist / '_headers').is_file()
        brister = publika_brister(dist) if dist.is_dir() else ['dist/ saknas']
        rader.append('dist/index.html: %s; dist/_headers: %s; filer som inte får bli publika: %s' % (
            'finns' if statiskt else 'saknas', 'finns' if huvuden else 'saknas', ', '.join(brister) or 'inga'))
        # Workern paketeras som vid en driftsättning, men inget skickas: --dry-run kräver varken konto eller nät
        rc, ut = processgrans.kor_i_katalog(repo, [repo / 'node_modules' / '.bin' / 'wrangler', 'deploy', '--dry-run', '--outdir', 'paket'],
                                            miljo_extra={'WRANGLER_LOG': 'warn'})
        paketerad = sorted(str(p.relative_to(repo / 'paket')) for p in (repo / 'paket').rglob('*.js')) if (repo / 'paket').is_dir() else []
        rader.append('$ wrangler deploy --dry-run (utan nät och konto) → %d; paketerat: %s' % (rc, ', '.join(paketerad) or 'inget'))
        if rc:
            rader.append(ut[-1500:])
        return statiskt and huvuden and not brister and not rc and bool(paketerad), '\n'.join(rader)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def skapa_export(slug, kandidat, mal, git, bygg, export_id=None):
    import kundrepo
    sajt = KUNDER / slug / ('kandidater/%s/sajt' % kandidat if kandidat else 'sajt')
    if not (sajt / 'package.json').is_file() or not (sajt / 'src' / 'pages' / 'index.astro').is_file():
        raise ValueError('%s saknar package.json eller startsidan' % sajt.relative_to(ROOT))
    for n in KALLOR:
        if (sajt / n).is_file() and not (sajt / n).is_symlink():
            shutil.copyfile(sajt / n, mal / n)
    for k in KATALOGER:
        if (sajt / k).is_dir() and not (sajt / k).is_symlink():
            kopiera(sajt / k, mal / k)
    for sida in ('fel.astro', 'mottagen.astro'):  # funktionens 303-mål (fel, och sparad men ej aviserad; D1) finns i varje export
        if not (mal / 'src' / 'pages' / sida).is_file():
            shutil.copyfile(MALL / 'src' / 'pages' / sida, mal / 'src' / 'pages' / sida)
    # Cloudflare Worker: formulärets mottagning, D1-schemat, konfigurationen och de statiska filernas huvuden; sajten
    # förblir förrenderad (ingen adapter i astro.config.mjs)
    kopiera(LEVERANS / 'worker', mal / 'worker')
    kopiera(LEVERANS / 'migrations', mal / 'migrations')
    (mal / 'wrangler.jsonc').write_text(wrangler_namn((LEVERANS / 'wrangler.jsonc').read_text(encoding='utf-8'), slug), encoding='utf-8')
    (mal / 'public').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LEVERANS / '_headers', mal / 'public' / '_headers')
    paket = json.loads((LEVERANS / 'package.json').read_text(encoding='utf-8'))
    extra = installerade_extra(sajt, paket['dependencies'])
    paket['name'] = 'kund-%s' % slug
    paket['dependencies'] = dict(sorted({**paket['dependencies'], **extra}.items()))  # devDependencies (Wrangler) som i mallen
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
    (mal / 'CLAUDE.md').write_text(kundrepo.claude_md(slug, export_id, underlag=UNDERLAG), encoding='utf-8')  # projektets korta kontext (2A)
    shutil.copyfile(LEVERANS / 'gitignore', mal / '.gitignore')
    shutil.copyfile(LEVERANS / 'env.example', mal / '.env.example')
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



def exportmanifest(rot):
    """Allt som lämnas över, utom Git och installerade/byggda körfiler."""
    ut = {}
    def fel(e):
        raise e
    for katalog, kataloger, filer in os.walk(rot, followlinks=False, onerror=fel):
        # Git, installerade paket och Astros cache på varje nivå; byggets och Wranglers utdata bara i roten, så att en
        # sida som src/pages/paket/ eller src/pages/dist/ räknas
        topp = Path(katalog) == Path(rot)
        kataloger[:] = sorted(n for n in kataloger if n not in ('.git', 'node_modules', '.astro')
                              and not (topp and n in ('dist', '.wrangler', 'paket', '.vercel')))
        if any((Path(katalog) / n).is_symlink() for n in kataloger):
            raise ValueError('exporten innehåller en kataloglänk')
        for n in sorted(filer):
            p = Path(katalog) / n
            if p.is_symlink() or not p.is_file():
                raise ValueError('exporten innehåller något annat än vanliga filer')
            ut[p.relative_to(rot).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return ut


def manifest_sha(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


@contextlib.contextmanager
def avbrott_som_fel():
    """Fångbara stoppsignaler ska gå genom återställningen; SIGKILL kan inte fångas."""
    gamla = {}
    def avbryt(signum, _frame):
        raise InterruptedError('exporten stoppades av signal %s' % signum)
    try:
        for s in (signal.SIGTERM, signal.SIGHUP):
            try:
                gamla[s] = signal.signal(s, avbryt)
            except ValueError:  # ingen signalhanterare får sättas från en HTTP-tråd
                break
        yield
    finally:
        for s, handler in gamla.items():
            signal.signal(s, handler)


def exportera(slug, kandidat=None, ut=None, git=False, bygg=True):
    import flodesstart
    with flodesstart.las(ROOT,slug,arv=True), avbrott_som_fel():
        flodesstart.atelje_ledig(ROOT,slug)
        return _exportera(slug,kandidat,ut,git,bygg)


def _exportera(slug, kandidat=None, ut=None, git=False, bygg=True):
    """Förbered och pröva en ny export innan den tidigare ersätts. Kvittot stannar privat."""
    import atelje
    import korregister
    import korslut
    import skapande
    if not re.fullmatch(r'[a-z0-9-]{2,60}', slug) or kandidat and not re.fullmatch(r'k\d{2}', kandidat):
        raise ValueError('ogiltig slug eller kandidat')
    kund = KUNDER / slug
    atelje.saker_vag(kund, KUNDER)
    sajt = kund / ('kandidater/%s/sajt' % kandidat if kandidat else 'sajt')
    atelje.saker_vag(sajt, kund)
    if not (sajt / 'package.json').is_file() or not (sajt / 'src/pages/index.astro').is_file():
        raise ValueError('sajten saknar package.json eller startsidan')
    mal = Path(ut).absolute() if ut else kund / 'kundrepo'
    # En extern utkatalog är tillåten, men aldrig projektets källor, mekanik eller en annan kund.
    atelje.saker_vag(mal, mal.parent)
    faktisk = mal.resolve()
    if faktisk == sajt.resolve() or faktisk in sajt.resolve().parents or sajt.resolve() in faktisk.parents:
        raise ValueError('exportens mål överlappar sajtens källor')
    if ROOT.resolve() in faktisk.parents and faktisk != (kund / 'kundrepo').resolve():
        raise ValueError('export inom repot får bara ligga i den egna kundens kundrepo; välj annars ett mål utanför repot')
    if mal.exists() and not mal.is_dir():
        raise ValueError('exportens mål är ingen katalog')
    mal.parent.mkdir(parents=True, exist_ok=True)
    rot = kund / 'exporter'
    atelje.saker_vag(rot, kund)
    rot.mkdir(exist_ok=True)
    las = os.open(rot / '.las', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(las, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise ValueError('en export pågår redan för kunden') from e
        # Löpnummer under exportlåset: två försök samma sekund eller en ändrad
        # väggklocka får aldrig vända ordningen på slutbeskeden.
        nummer = 1 + max((int(p.name[:12]) for p in rot.iterdir() if re.match(r'^\d{12}-', p.name)), default=0)
        id_ = '%012d-%s-%s' % (nummer, nu().replace(':', ''), uuid.uuid4().hex[:10])
        postrot = rot / id_
        postrot.mkdir()
        kvitto = postrot / 'EXPORT.json'
        fore = skapande.kallversion(sajt)
        res = {'schema': 1, 'id': 'EXPORT-' + id_, 'typ': 'exportkvitto', 'titel': 'Kundrepots export',
               'slug': slug, 'kandidat': kandidat, 'tid': nu(), 'ut': str(mal), 'ok': False,
               'start_id':os.environ.get('NWP_FLODE_START_ID') if re.fullmatch(r'[A-Za-z0-9_-]{8,80}',os.environ.get('NWP_FLODE_START_ID','')) else None,
               'kvitto': str(kvitto), 'kallor_sha256': fore, 'export_sha256': None,
               'klart_for_leverans': False, 'kontroller': {'exportbygge': {'varde': None}},
               'tillstand': {n: {'varde': None, 'text': 'inget giltigt slutbesked för denna export'} for n, _ in korslut.TILLSTAND}}
        res['tillstand']['klart_for_leverans'] = {'varde': False, 'text': 'export är inte en verifierad driftsättning',
                                               'omfattning': 'kundrepo; domän, riktiga formulär och drift återstår'}
        # På målets filsystem: slutbytet kopierar aldrig över gamla filer. Bara repo/ blir kundrepo.
        tmp = Path(korregister.egen_tmp('nwp-export-', 'export före publicering', dir=mal.parent))
        stage = tmp / 'repo'
        stage.mkdir()
        import kundrepo
        bestandigt = kundrepo.ar_repo(mal)  # kundprojektets eget repo (kundrepo.py): exporten blir en commit där, inget katalogbyte
        try:
            data = skapa_export(slug, kandidat, stage, git and not bestandigt, bygg, export_id=res['id'])
            res.update({n: v for n, v in data.items() if n not in ('ut', 'ok')})
            res['kontroller']['exportbygge'] = {'varde': data.get('bygge_ok'),
                                                'text': data.get('bygge') or 'inte kört (--inget-bygge)'}
            if skapande.kallversion(sajt) != fore:
                res['fel'] = 'källorna ändrades under exporten; ingen ny export publicerad'
            elif data.get('ok'):
                res['filer'] = exportmanifest(stage)
                res['export_sha256'] = manifest_sha(res['filer'])
                slut = korslut.aktuell(kund) if not kandidat else None
                if slut:
                    res['helbygge'] = {'korning': slut.get('korning'), 'dist_sha256': slut.get('dist_sha256'),
                                      'kallor_sha256': slut.get('kallor_sha256'), 'slutpost': slut.get('slutpost')}
                    if slut.get('kallor_sha256') == fore:
                        for n, _ in korslut.TILLSTAND:
                            if n != 'klart_for_leverans':
                                res['tillstand'][n] = (slut.get('tillstand') or {}).get(n) or res['tillstand'][n]
                    else:
                        res['helbygge']['text'] = 'historiskt eller saknar koppling mellan källor och granskat dist'
                undan = None
                staged_id = (stage.stat().st_dev, stage.stat().st_ino)
                if bestandigt:
                    c = kundrepo.synka_export(slug, stage, res['id'], 'kandidat %s' % kandidat if kandidat else 'sajten', rot=mal)
                    res['commit'], res['kundrepo'] = c['commit'], {'lokal': str(mal), 'oforandrad': c['oforandrad']}
                    res['ok'] = True
                    if ((kundrepo.las_kvitto(slug, mal.parent) or {}).get('fjarr') or {}).get('status') == 'skapat':
                        res['push'] = kundrepo.push(slug, rot=mal)  # det bundna privata fjärrepot (ingen publicering)
                if not bestandigt:
                    try:
                        with avbrott_som_fel():
                            if mal.exists():
                                undan = kund / 'kundrepo-tidigare' / id_
                                atelje.saker_vag(undan, kund)
                                undan.parent.mkdir(exist_ok=True)
                                os.replace(mal, undan)
                            os.replace(stage, mal)
                            res['ok'] = True
                            if undan:
                                res['tidigare'] = str(undan)
                    except BaseException:
                        res['ok'] = False
                        # Även signalramens avslut ingår. Signalen kan komma efter att
                        # replace gjort sitt byte; flytta bara tillbaka vår egen inode.
                        if mal.exists() and not mal.is_symlink() and (mal.stat().st_dev, mal.stat().st_ino) == staged_id:
                            os.replace(mal, stage)
                        if undan and undan.exists() and not mal.exists():
                            os.replace(undan, mal)
                        raise
            else:
                res['fel'] = 'exportens läckagekontroll eller byggprov föll'
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as e:
            res.update(ok=False, fel=type(e).__name__ + ': ' + str(e)[:600])
        finally:
            try:
                shutil.rmtree(tmp)
            finally:
                atelje.skriv_json_atomiskt(kvitto, res)
        return res
    finally:
        os.close(las)


def aktuell(slug):
    """Senaste exportförsöket och om dess källor och exporterade filer fortfarande är desamma."""
    import skapande
    import korslut
    rot = KUNDER / slug / 'exporter'
    def ordning(p):
        m = re.match(r'^(\d{12})-', p.parent.name)
        # Formatbytet: alla löpnumrerade försök kommer efter de äldre
        # tidsstämpel-id:na. Inom nya formatet styr numret, inte väggklockan.
        return (1, int(m.group(1)), p.parent.name) if m else (0, 0, p.parent.name)
    poster = sorted(rot.glob('*/EXPORT.json'), key=ordning, reverse=True) if rot.is_dir() and not rot.is_symlink() else []
    if not poster:
        return None
    try:
        if poster[0].is_symlink():
            raise ValueError('länkat exportkvitto')
        post = json.loads(poster[0].read_text(encoding='utf-8'))
        kandidat = post.get('kandidat')
        sajt = KUNDER / slug / ('kandidater/%s/sajt' % kandidat if kandidat else 'sajt')
        mal = Path(post['ut'])
        post['aktuell'] = bool(post.get('ok') and mal.is_dir() and not mal.is_symlink()
                               and skapande.kallversion(sajt) == post.get('kallor_sha256')
                               and manifest_sha(exportmanifest(mal)) == post.get('export_sha256'))
        # Exportfiler kan vara oförändrade medan dist, metod eller ägardom ändrats.
        # Publiceringsögonblickets tillstånd ligger kvar i kvittot på disk; här
        # kommer de aktuella beskeden ur samma prövning som helbyggets vy.
        slut = korslut.aktuell(KUNDER / slug, (post.get('helbygge') or {}).get('korning')) if post.get('helbygge') else None
        for n, _ in korslut.TILLSTAND:
            if n == 'klart_for_leverans':
                continue
            fore = (post.get('tillstand') or {}).get(n) or {}
            p = ((slut or {}).get('tillstand') or {}).get(n)
            if post['aktuell'] and slut and slut.get('kallor_sha256') == post.get('kallor_sha256') and isinstance(p, dict):
                post['tillstand'][n] = p
            else:
                post['tillstand'][n] = {'varde': None, 'historik': fore, 'text': 'inget aktuellt godkännande knutet till exporten'}
        return post
    except (OSError, ValueError, KeyError, TypeError):
        return {'ok': False, 'aktuell': False, 'fel': 'exportkvittot eller dess filer kunde inte verifieras'}


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
    except (OSError, ValueError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        return 2
    for f, s in r.get('lackor') or []:
        print('LÄCKAGE: %s nämner %s' % (f, s))
    if r.get('hanvisningar'):
        print('hänvisningar till Nortropics publika repo eller verktyg (fäller inte): %s' % ', '.join(r['hanvisningar']))
    if r.get('bygge'):
        print(r['bygge'])
    besked = ('Testexport utan verifierat bygge (--inget-bygge)' if a.inget_bygge else 'Exportens bygge verifierat; publicering återstår') if r['ok'] else 'Exporten misslyckades; tidigare export är orörd'
    print('%s: %s%s' % (besked, r['ut'], (' (commit %s)' % r['commit'][:12]) if r.get('commit') else ''))
    return 0 if r['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
