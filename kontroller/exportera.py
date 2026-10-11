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
import tarfile
import tempfile
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
GENERERADE_I_KATALOGER = ('public/_headers', 'src/verifiering.json')  # skrivs av exporten fast de ligger i katalogerna


def fran_sajten(rel):
    """Om exporten tar filen ur sajten (källorna och katalogerna) i stället för att skriva den själv (README, CLAUDE.md,
    paketen, Workern, migreringarna, wrangler.jsonc, _headers, verifieringen, licenserna, .gitignore och .env.example).
    Funktionssidorna (felsidan, mottagen-sidan) räknas som sajtens: en sida sajten har skrivs aldrig över."""
    delar = Path(rel).parts
    return bool(delar) and (rel in KALLOR or delar[0] in KATALOGER) and rel not in GENERERADE_I_KATALOGER
TEXTFILER = ('.astro', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.css', '.json', '.md', '.html', '.svg', '.txt', '.example', '.yml', '.yaml')
# en fil i kundrepot får aldrig nämna en lokal sökväg, Nortropics privata underlag (referenser, intervjuer, domar,
# råmaterial) eller en nyckel; det fäller exporten. En hänvisning till Nortropics publika verktyg (kontroller/design.py i
# en kommentar) redovisas men fäller inte: repot och verktygen är publika
LACKA = [(re.compile(p), skal) for p, skal in (
    (r'/Users/|/private/tmp/|/home/[a-z]', 'en lokal sökväg'),
    (r'\bunderlag/[a-z0-9-]+/|LARDOMAR-original|DESIGNDOMAR|RIKTNINGSHISTORIK|REFERENSUPPDRAG|TJANSTEUPPDRAG|/kalibrering/', 'Nortropics privata underlag'),
    (r'\bre_[A-Za-z0-9]{6,}_[A-Za-z0-9]{16,}|\bre_[A-Za-z0-9]{16,}|\bsk-[A-Za-z0-9_-]{20,}|\bghp_[A-Za-z0-9]{20,}|\bvercel_blob_rw_[A-Za-z0-9_]{10,}'
     r'|\bxkeysib-[A-Za-z0-9-]{16,}', 'en nyckel'),
    # också i JSON och YAML: namnet inom citattecken före kolon ("CLOUDFLARE_API_TOKEN": "…")
    (r'(RESEND_API_KEY|BLOB_READ_WRITE_TOKEN|REFERO_MCP_TOKEN|CLOUDFLARE_API_TOKEN|CF_API_TOKEN|BREVO_API_NYCKEL|PIPEDRIVE_TOKEN)'
     r'["\']?[ \t]*[=:][ \t]*["\']?[^\s#"\']', 'ett nyckelvärde'),
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


def verifieringsfil(slug, mal):
    """Sökkonsolens verifiering (K05): skriver src/verifiering.json ur VERKSAMHET.json (webb.sokkonsol_verifiering, den
    del av META-taggen som Search Console ger) för en verklig verksamhet; mallens Bas renderar taggen. Ger värdet eller
    None. Värdet är publikt (det står i sidans head); ett värde med fel form stoppar exporten."""
    try:
        v = json.loads((UNDERLAG / slug / 'VERKSAMHET.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    varde = (v.get('webb') or {}).get('sokkonsol_verifiering') if isinstance(v, dict) and isinstance(v.get('webb'), dict) else None
    if not varde or v.get('fiktiv') is True:  # en fiktiv verksamhet får ingen egenskap (sokkonsol.md)
        return None
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,100}', str(varde)):
        raise ValueError('webb.sokkonsol_verifiering ska vara innehållet i Search Consoles META-tagg (20–100 tecken A–Z, 0–9, _ och -)')
    (mal / 'src').mkdir(parents=True, exist_ok=True)
    (mal / 'src' / 'verifiering.json').write_text(json.dumps({'google': varde}) + '\n', encoding='utf-8')
    return varde


def funktionssidor(mal):
    """Workerns 303-mål i exporten: felsidan och mottagen-sidan i varje export (formuläret, D1), och nyhetsbrevets två
    svarssidor när sajten importerar Nyhetsbrev (K14). En sida sajten redan har skrivs aldrig över. Ger de tillagda."""
    tillagda = []
    sidor = [(MALL / 'src' / 'pages' / s, s) for s in ('fel.astro', 'mottagen.astro')]
    if anvander_komponent(mal / 'src', 'Nyhetsbrev'):  # bara i exporten: ny_sajt kopierar hela mall/astro till varje sajt
        sidor += [(LEVERANS / 'sidor' / s, s) for s in ('nyhetsbrev/skickad.astro', 'nyhetsbrev/bekraftad.astro')]
    for kalla, sida in sidor:
        if not (mal / 'src' / 'pages' / sida).is_file():
            (mal / 'src' / 'pages' / sida).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(kalla, mal / 'src' / 'pages' / sida)
            tillagda.append(sida)
    return tillagda


def anvander_komponent(src, namn):
    """Om någon av sajtens .astro-filer importerar mallens komponent namn (namn.astro)."""
    if not src.is_dir():
        return False
    monster = re.compile(r'import\s+\w+\s+from\s+[\'"][^\'"]*/%s\.astro[\'"]' % re.escape(namn))
    return any(monster.search(f.read_text(encoding='utf-8', errors='replace')) for f in src.rglob('*.astro')
               if f.is_file() and not f.is_symlink() and f.name != namn + '.astro')


def wrangler_namn(text, slug, drift=None):
    """wrangler.jsonc med kundens namn i stället för SLUG och, när driftvärdena finns, kundens D1-id och mejladresser;
    allt annat (kompatibilitetsdatum, bindningar) som i mallen. drift: underlag/<slug>/CLOUDFLARE.json, se driftvarden()."""
    if 'kund-SLUG' not in text:
        raise RuntimeError('mallens wrangler.jsonc saknar platshållaren kund-SLUG')
    text = text.replace('kund-SLUG', 'kund-%s' % slug)
    for nyckel, monster in (('database_id', r'("database_id":\s*")AKTIVERAS-VID-LANSERING(")'),
                            ('forfragan_till', r'("FORFRAGAN_TILL":\s*")(")'), ('forfragan_fran', r'("FORFRAGAN_FRAN":\s*")(")'),
                            ('nyhetsbrev_lista', r'("NYHETSBREV_LISTA":\s*")(")'), ('nyhetsbrev_mall', r'("NYHETSBREV_MALL":\s*")(")'),
                            ('pipedrive_doman', r'("PIPEDRIVE_DOMAN":\s*")(")')):
        if drift and drift.get(nyckel):
            text, n = re.subn(monster, lambda m, v=drift[nyckel]: m.group(1) + v + m.group(2), text, count=1)
            if n != 1:
                raise RuntimeError('mallens wrangler.jsonc saknar platsen för %s' % nyckel)
    # send_email-bindningen låses till kundens mottagare och avsändare (K04)
    for nyckel, falt in (('forfragan_till', 'allowed_destination_addresses'), ('forfragan_fran', 'allowed_sender_addresses')):
        if drift and drift.get(nyckel):
            adresser = json.dumps([x.strip() for x in drift[nyckel].split(',') if x.strip()])
            text, n = re.subn(r'("%s":\s*)\["inte-aktiverad@invalid\.invalid"\]' % falt, lambda m, a=adresser: m.group(1) + a, text, count=1)
            if n != 1:
                raise RuntimeError('mallens wrangler.jsonc saknar send_email-bindningens %s' % falt)
    return text


EPOST = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def driftvarden(slug):
    """Kundens driftvärden för produktionen, privat i underlag/<slug>/CLOUDFLARE.json (skapas vid aktiveringen):
    {"database_id": "<D1-id>", "forfragan_till": "a@x.se[,b@x.se]", "forfragan_fran": "<kund>@notis.nortropic.se"}.
    Mottagarna är verksamhetens brevlådor, verifierade i Nortropics Cloudflare-konto; avsändaren ligger på en
    routing-domän i samma konto (kunskap/forfragan.md, punkt 6). None när filen saknas; ValueError när ett värde har fel
    form (inget hamnar då i kundrepot)."""
    f = UNDERLAG / slug / 'CLOUDFLARE.json'
    if not f.is_file() or f.is_symlink():
        return None
    d = json.loads(f.read_text(encoding='utf-8'))
    if not isinstance(d, dict) or set(d) - {'database_id', 'forfragan_till', 'forfragan_fran', 'nyhetsbrev_lista', 'nyhetsbrev_mall', 'pipedrive_doman'}:
        raise ValueError('CLOUDFLARE.json har okända fält')
    if d.get('database_id') and not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', d['database_id']):
        raise ValueError('database_id ska vara D1-databasens id')
    if d.get('forfragan_till') and not all(EPOST.fullmatch(x.strip()) for x in d['forfragan_till'].split(',')):
        raise ValueError('forfragan_till ska vara en eller flera e-postadresser')
    if d.get('forfragan_fran') and not EPOST.fullmatch(d['forfragan_fran']):
        raise ValueError('forfragan_fran ska vara en e-postadress')
    for n in ('nyhetsbrev_lista', 'nyhetsbrev_mall'):  # Brevos id för listan och bekräftelsemallen (K14)
        if d.get(n) is not None and not re.fullmatch(r'[1-9][0-9]{0,9}', str(d[n])):
            raise ValueError('%s ska vara Brevos numeriska id' % n)
        if d.get(n) is not None:
            d[n] = str(d[n])
    if d.get('pipedrive_doman') is not None and not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', str(d['pipedrive_doman'])):
        raise ValueError('pipedrive_doman ska vara Pipedrive-kontots underdomän (<doman>.pipedrive.com)')
    return d


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


# designstudions förhandsbygge (kontroller/studio/karta.mjs, forhandsbrygga.js): källkartans id, regel-id och bryggans väg
# hör bara till kandidaternas förhandsvisning, aldrig till ett produktionsbygge (designstudion 2026-10-11, DS-U33)
STUDIOSPAR = re.compile(rb'data-nwp-k=|--nwp-r\s*:|/__nortropic/')


def studions_spar(dist):
    """[fil] i dist/ som bär designstudions förhandsbyggesspår; tom lista när bygget är ett rent produktionsbygge."""
    return sorted(str(p.relative_to(dist)) for p in Path(dist).rglob('*')
                  if p.is_file() and p.suffix.lower() in ('.html', '.css', '.js', '.mjs', '.json', '.xml', '.txt') and STUDIOSPAR.search(p.read_bytes()))


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
        brister += ['%s (designstudions förhandsbyggesspår)' % f for f in (studions_spar(dist) if dist.is_dir() else [])]
        rader.append('dist/index.html: %s; dist/_headers: %s; filer som inte får bli publika eller bär studions spår: %s' % (
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
    funktionssidor(mal)
    verifieringsfil(slug, mal)
    # Cloudflare Worker: formulärets mottagning, D1-schemat, konfigurationen och de statiska filernas huvuden; sajten
    # förblir förrenderad (ingen adapter i astro.config.mjs)
    kopiera(LEVERANS / 'worker', mal / 'worker')
    kopiera(LEVERANS / 'migrations', mal / 'migrations')
    (mal / 'wrangler.jsonc').write_text(wrangler_namn((LEVERANS / 'wrangler.jsonc').read_text(encoding='utf-8'), slug, driftvarden(slug)),
                                        encoding='utf-8')
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
        # Git, installerade paket och Astros cache på varje nivå; byggets, Wranglers och processgränsens utdata (.tmp:
        # bland annat Nodes kompileringscache, fjärrprovet 2026-10-10) bara i roten, så att en sida som src/pages/paket/ räknas
        topp = Path(katalog) == Path(rot)
        kataloger[:] = sorted(n for n in kataloger if n not in ('.git', 'node_modules', '.astro')
                              and not (topp and n in ('dist', '.wrangler', 'paket', '.vercel', '.tmp')))
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
                over = andringar_som_skrivs_over(slug, stage, mal) if bestandigt else {'stoppar': [], 'genereras': []}
                if over['genereras']:  # exportens egna filer som agenten ändrat: skrivs över, och det står i kvittot
                    res['genererade_skrivs_over'] = over['genereras'][:40]
                if over['stoppar']:  # kundrepots nyare innehåll skrivs aldrig över (kunskap/andringar.md)
                    res['skrivs_over'], res['vagrad'] = over['stoppar'][:40], True
                    raise ValueError('kundrepot har ändringar som den nya exporten skulle skriva över: %s. Låt agenten committa det '
                                     'som inte är committat, ta in sajtens filer i sajten (Ändringar, fliken Historik) eller gör ändringen '
                                     'i sajten; inget exporterades' % ', '.join(over['stoppar'][:8]))
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
                if res.get('vagrad'):  # ingen export gjordes: inget kvitto som kunde bli det senaste exportförsöket
                    shutil.rmtree(postrot, ignore_errors=True)
                else:
                    atelje.skriv_json_atomiskt(kvitto, res)
        return res
    finally:
        os.close(las)


SAKER_GIT = ('-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false')  # i ett repo som ändringsagenten skriver i


def andringar_som_skrivs_over(slug, stage, repo):
    """Det i kundrepot som en export över det skulle tappa: {'stoppar': [...], 'genereras': [...]}. Stoppar: det som inte
    är committat (synka_export tar bort allt utom .git och node_modules) och filer ur sajten som ändringsflikens commits
    ändrat efter den senaste exporten (KUNDREPO.json:s senaste_export) och som stagen skulle ge ett annat innehåll.
    Genereras: filer som exporten själv skriver (fran_sajten) och som commits ändrat; de skrivs över, med en varning."""
    import kundrepo
    ut = {'stoppar': [], 'genereras': []}
    st = kundrepo.git(repo, *SAKER_GIT, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    if st.returncode:
        ut['stoppar'].append('(arbetskopians läge går inte att läsa)')
        return ut
    poster, i = [x for x in st.stdout.split('\0') if x], 0
    while i < len(poster):
        x = poster[i]
        ut['stoppar'].append('%s (inte committad)' % x[3:])
        i += 2 if x[:1] in 'RC' else 1  # en flytt eller kopia har den gamla sökvägen som nästa post
    kv = kundrepo.las_kvitto(slug, Path(repo).parent) or {}
    bas = (kv.get('senaste_export') or {}).get('commit')
    huvud = kundrepo.huvud(repo)
    if not bas or not huvud or bas == huvud:
        return ut
    r = kundrepo.git(repo, *SAKER_GIT, 'diff', '--name-only', '-z', bas, huvud)
    if r.returncode:
        ut['stoppar'].append('(historiken efter exporten %s går inte att läsa)' % bas[:12])
        return ut
    for rel in [x for x in r.stdout.split('\0') if x]:
        visa = subprocess.run(['git', *SAKER_GIT, 'show', '%s:%s' % (huvud, rel)], cwd=str(repo), capture_output=True, timeout=60)
        i_repo = visa.stdout if visa.returncode == 0 else None
        p = Path(stage) / rel
        i_stage = p.read_bytes() if p.is_file() and not p.is_symlink() else None
        if i_repo != i_stage:
            ut['stoppar' if fran_sajten(rel) else 'genereras'].append(rel)
    return ut


def fran_klon(slug):
    """Kvittot för ett kundrepo som repoväljaren klonat (kunskap/andringar.md, Repoväljaren): den klonade commiten är det
    senast levererade (exporterat och pushat från en annan dator), så den blir grunden som ändringsflikens kvitteringar
    bygger vidare på, med samma frysta manifest som en ändring. Skrivs bara när kunden saknar ett eget exportkvitto.
    Ger kvittot."""
    import atelje
    import korregister
    import kundrepo
    if not re.fullmatch(r'[a-z0-9-]{2,60}', slug):
        raise ValueError('ogiltig slug')
    kund = KUNDER / slug
    r = kund / 'kundrepo'
    atelje.saker_vag(r, kund)
    if not kundrepo.ar_repo(r):
        raise ValueError('kundrepot finns inte')
    if aktuell(slug):
        raise ValueError('kunden har redan ett exportkvitto; klonen blir ingen ny grund')
    huvud = kundrepo.huvud(r)
    if not huvud:
        raise ValueError('klonen har ingen commit')
    rot = kund / 'exporter'
    atelje.saker_vag(rot, kund)
    rot.mkdir(exist_ok=True)
    las = os.open(rot / '.las', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(las, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as ex:
            raise ValueError('en export pågår redan för kunden') from ex
        nummer = 1 + max((int(p.name[:12]) for p in rot.iterdir() if re.match(r'^\d{12}-', p.name)), default=0)
        id_ = '%012d-%s-klon' % (nummer, nu().replace(':', ''))
        with korregister.egen_tmp_med('nwp-andring-', 'klonens frysta commit') as tmp:
            try:
                filer = exportmanifest(kundrepo.fryst_underlag(r, huvud, tmp))
            except tarfile.TarError as ex:
                raise ValueError('klonens filer går inte att frysa säkert: %s' % ex) from ex
        (rot / id_).mkdir()
        res = {'schema': 1, 'id': 'EXPORT-' + id_, 'typ': 'exportkvitto', 'titel': 'Klonat kundrepo', 'kalla': 'klon', 'slug': slug,
               'kandidat': None, 'tid': nu(), 'ut': str(r), 'ok': True, 'commit': huvud, 'kvitto': str(rot / id_ / 'EXPORT.json'),
               'kallor_sha256': None, 'filer': filer, 'export_sha256': manifest_sha(filer), 'klart_for_leverans': False,
               'tillstand': {'klart_for_leverans': {'varde': False, 'text': 'en klon är ingen verifierad driftsättning'}}}
        atelje.skriv_json_atomiskt(rot / id_ / 'EXPORT.json', res)
        return res
    finally:
        os.close(las)


def fran_andring(slug, push=False):
    """En verifierad ändring i kundrepots arbetskopia (ändringsfliken, kunskap/andringar.md) som kundens senaste leverabel:
    HEAD med agentens provväg godkänd för exakt det trädet får ett exportkvitto (kalla andring) med samma manifest som
    förhandsvisningen prövar, så att förhandsvisningen och releasen (kundrepo.preview, release) gäller den som en export.
    Kräver ett rent träd, en commit som bygger på den senaste exporten och ingen läcka i det som skickas. push: commiten
    pushas till det bundna fjärrepot (Johnnys kvittering; den automatiska efter turen pushar aldrig). Ger kvittot."""
    import andringar
    import atelje
    import kundrepo
    if not re.fullmatch(r'[a-z0-9-]{2,60}', slug):
        raise ValueError('ogiltig slug')
    kund = KUNDER / slug
    r = kund / 'kundrepo'
    atelje.saker_vag(r, kund)
    if not kundrepo.ar_repo(r):
        raise ValueError('kundrepot finns inte')
    if kundrepo.git(r, *SAKER_GIT, 'status', '--porcelain').stdout.strip():
        raise ValueError('arbetskopian har ändringar som inte är committade: committa ändringen, eller låt främmande ändringar stå utanför')
    huvud = kundrepo.huvud(r)
    e = aktuell(slug) or {}
    bas = e.get('commit')
    if not bas or not e.get('ok'):
        raise ValueError(e.get('fel') or 'ingen lyckad export finns att bygga vidare på')
    if huvud == bas:
        raise ValueError('ingen ny commit efter den senaste exporten')
    if kundrepo.git(r, 'merge-base', '--is-ancestor', bas, huvud).returncode:
        raise ValueError('HEAD bygger inte på den senaste exporten (%s)' % bas[:12])
    trad = kundrepo.git(r, 'rev-parse', 'HEAD^{tree}').stdout.strip()
    k = andringar.senaste_kontroll(slug) or {}
    if not k.get('ok') or k.get('tillstand') != trad:
        raise ValueError('ingen godkänd kontroll av exakt den här versionen: kör provvägen efter den sista ändringen')
    lackor = kundrepo.historikens_lackor(r, huvud)
    if lackor:
        raise ValueError('läckagekontrollen fäller historiken: %s' % kundrepo.besked(lackor))
    rot = kund / 'exporter'
    rot.mkdir(exist_ok=True)
    las = os.open(rot / '.las', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(las, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as ex:
            raise ValueError('en export pågår redan för kunden') from ex
        nummer = 1 + max((int(p.name[:12]) for p in rot.iterdir() if re.match(r'^\d{12}-', p.name)), default=0)
        id_ = '%012d-%s-andring' % (nummer, nu().replace(':', ''))
        import korregister
        with korregister.egen_tmp_med('nwp-andring-', 'kvitteringens frysta commit') as tmp:
            try:
                fryst = kundrepo.fryst_underlag(r, huvud, tmp)
            except tarfile.TarError as ex:  # till exempel en länk till en absolut sökväg i commiten
                raise ValueError('commitens filer går inte att frysa säkert: %s' % ex) from ex
            filer = exportmanifest(fryst)  # leverabeln är commiten: arbetskopians ignorerade filer (.DS_Store) hör inte dit
        (rot / id_).mkdir()  # först när kvittot kan skrivas: ett avbrutet försök lämnar ingen tom katalog
        commits = kundrepo.git(r, 'log', '--format=%H%x1f%s', '%s..%s' % (bas, huvud)).stdout.splitlines()
        res = {'schema': 1, 'id': 'EXPORT-' + id_, 'typ': 'exportkvitto', 'titel': 'Ändring i kundrepot', 'kalla': 'andring', 'slug': slug,
               'kandidat': None, 'tid': nu(), 'ut': str(r), 'ok': True, 'commit': huvud, 'bas': bas,
               'commits': [dict(zip(('commit', 'text'), x.split('\x1f', 1))) for x in commits][:100],
               'kvitto': str(rot / id_ / 'EXPORT.json'), 'kallor_sha256': None, 'filer': filer, 'export_sha256': manifest_sha(filer),
               'kontroll': {'tid': k.get('tid'), 'katalog': k.get('katalog'), 'tillstand': trad},
               'klart_for_leverans': False, 'kontroller': {'andringskontroll': {'varde': True, 'text': 'agentens provväg godkänd för trädet %s' % trad[:12]}},
               'tillstand': {'klart_for_leverans': {'varde': False, 'text': 'en ändring är ingen verifierad driftsättning'}}}
        atelje.skriv_json_atomiskt(rot / id_ / 'EXPORT.json', res)
        kv = kundrepo.las_kvitto(slug, kund)
        if kv:
            kv['senaste_andring'] = {'id': res['id'], 'commit': huvud, 'tid': res['tid']}
            atelje.skriv_json_atomiskt(kundrepo.kvittofil(slug, kund), kv)
            if push and (kv.get('fjarr') or {}).get('status') == 'skapat':
                res['push'] = kundrepo.pusha_granskad(r, huvud)  # den kvitterade commiten till det bundna fjärrepot (ingen publicering)
                atelje.skriv_json_atomiskt(rot / id_ / 'EXPORT.json', res)
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
        post = None
        for f in poster:  # ett försök som skyddet vägrade (äldre kvitton bär vagrad) exporterade inget och räknas inte
            if f.is_symlink():
                raise ValueError('länkat exportkvitto')
            post = json.loads(f.read_text(encoding='utf-8'))
            if not post.get('vagrad'):
                break
        else:
            return None
        kandidat = post.get('kandidat')
        sajt = KUNDER / slug / ('kandidater/%s/sajt' % kandidat if kandidat else 'sajt')
        mal = Path(post['ut'])
        if post.get('kalla') in ('andring', 'klon'):  # en kvitterad ändring eller en klon: aktuell så länge repot står på commiten
            import kundrepo
            post['aktuell'] = bool(post.get('ok') and mal.is_dir() and not mal.is_symlink() and kundrepo.huvud(mal) == post.get('commit'))
            return post
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
