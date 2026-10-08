#!/usr/bin/env python3
"""processgrans.py — kör ett byggsteg innanför en processgräns också från stoppkroken, som Claude Codes sandlåda inte
omfattar (Codex R25, F1: kroken startade prova.py och därmed kundens npm run build med värdprocessens åtkomst).

macOS seatbelt (sandbox-exec) med samma policy som kontroller/sandlada.py: skrivning bara i byggets kataloger,
granskarnas arbetsrot, körningens egen tempkatalog (/tmp/nwp-bygge-<slug>/tmp, TMPDIR därinne) och cacher, med
policyns skrivförbud (denyWrite) bevarade också när de ligger under en tillåten katalog (Codex R26, F1: en repokopia
under temp); hemligheter olästa; nät bara till localhost (webbtjänsten och byggets egen server) och unix-socklar.
Miljön rensas som i den vanliga sandlådan (credentials-policyn: REFERO_MCP_TOKEN; proxyvariabler, som inte gäller
härinne) innan kommandot startas (Codex R26, F1/F27). Chromium och claude kan inte startas härifrån (nät), så
webbläsarsteg och granskarnas sessioner delegerar till webbtjänsten: NWP_PROCESSGRANS=1 räknas som sandlådemarkering
i webbtjanst.delegeras och i webbläsarhjälparens viaTjanst.

Byggets läsgräns per kandidat (GR-20261007-r107#K1; BESLUT.md, tillägget 2026-10-07: byggets läsgräns per kandidat):
när --skrivbar är en kandidats projekt (kunder/<slug>/kandidater/kNN/…) nekas läsning som standard och släpps bara för
det bygget behöver, mätt med ett verkligt bygge (lasgrans, SYSTEMETS): kandidatens projekt, sajtens delade node_modules,
kandidatens egen temp (/tmp/nwp-bygge-<slug>/tmp-kNN), systemets delar och repots .gitignore och .git. De andra
kandidaternas kataloger, underlag/ och allt annat i repot och hemkatalogen förblir olästa, också för kritikens
förhandsvisning, som bygger genom samma väg (prova.bygg_inom_grans). Bygget startar i kandidatens projekt. En
node_modules-länk som pekar bort från sajtens vägras, liksom ett program som läsgränsen inte släpper: det skulle fastna
i kärnan. Sajtens eget bygge har ingen läsgräns.

    .venv/bin/python kontroller/processgrans.py <slug> [--root R] [--hem H] [--skriv-profil] [--utan-nat] [--bara-sajt | --skrivbar DIR] -- <kommando …>
Slutkoden är kommandots. Utan sandbox-exec (annat system) vägras körningen (slutkod 2): gränsen får aldrig tyst saknas.
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
SANDBOX_EXEC = '/usr/bin/sandbox-exec'


def sbpl(p):
    return '"%s"' % str(p).replace('\\', '\\\\').replace('"', '\\"')


def regex_ur_glob(monster):
    """'**/.env.*' → seatbelt-regex som träffar varje sådan fil: komponenten i slutet av sökvägen."""
    namn = monster[3:] if monster.startswith('**/') else monster
    return '/' + re.escape(namn).replace('\\*', '[^/]*') + '$'


def tempkatalog(slug, kid=None):
    """Körningens egen tempkatalog innanför gränsen: under byggets eget tempområde, aldrig systemets (Codex R26, F1). En
    kandidats bygge får en egen, tmp-<id>: två kandidaters byggen delar ingen temp, där Node bland annat lägger sin
    kompileringscache (byggets läsgräns, 2026-10-07)."""
    return '/tmp/nwp-bygge-%s/tmp' % slug + ('-%s' % kid if kid else '')


def ren_miljo(miljo=None, slug=None, root=None, hem=None, kid=None):
    """Miljön innanför gränsen: samma skydd som den vanliga sandlådans credentials-policy (sandlada.py, REFERO_MCP_TOKEN)
    plus proxyvariablerna, som inte gäller härinne (nätet är localhost; en proxyvariabel utifrån skulle bara vilseleda
    hamta_sajt), och markören NWP_PROCESSGRANS=1 samt TMPDIR i körningens egen tempkatalog (Codex R26, F1/F27), för en
    kandidat dess egen (kid). Astros telemetri och npm:s versionskoll är av: telemetrin kör git i repot, läser
    hemkatalogen och försöker nå nätet, och versionskollen frågar registret; inget av det hör till ett bygge (mätt
    2026-10-07)."""
    import sandlada
    miljo = dict(os.environ if miljo is None else miljo)
    policy = sandlada.installningar(slug or 'x', root=root, hem=hem)['sandbox'].get('credentials', {}).get('envVars', [])
    nekade = {p['name'] for p in policy if p.get('mode') == 'deny'} | {'REFERO_MCP_TOKEN'}
    for k in list(miljo):
        if k in nekade or k.upper().endswith('_PROXY'):
            del miljo[k]
    miljo['NWP_PROCESSGRANS'] = '1'
    miljo['ASTRO_TELEMETRY_DISABLED'] = '1'
    miljo['npm_config_update_notifier'] = 'false'
    if slug:
        miljo['TMPDIR'] = tempkatalog(slug, kid)
    return miljo


KANDIDAT = re.compile(r'^k\d{2}$')  # en kandidats id, samma form som kandidater.ID
# Byggets läsgräns per kandidat: det ett bygge läser utanför sitt projekt, de delade node_modules och sin temp. Mätt
# 2026-10-07 med en rapporterande profil ((allow file-read* (with report)) och kärnans logg) under ett verkligt bygge av
# en syntetisk kandidat (Astro, Vite, Tailwind, en React-ö, en bild genom sharp och ett typsnitt ur Fontsource): dyld:s
# delade cache och ramverken, skalet (/bin/sh väljer skal i /private/var/select), /usr/bin/env i paketens skript,
# teckenkodningarna och ICU-data i /usr/share, tidszonen, enheterna, och Node, npm och deras bibliotek i Homebrew.
SYSTEMETS = ('/System/Library', '/System/Cryptexes', '/System/Volumes/Preboot/Cryptexes', '/usr/lib', '/usr/bin', '/usr/share', '/bin',
             '/private/etc', '/private/var/db/timezone', '/private/var/select', '/dev',
             '/opt/homebrew/Cellar', '/opt/homebrew/opt', '/opt/homebrew/lib', '/opt/homebrew/bin', '/opt/homebrew/etc')


def kandidat_i(projekt, root, slug):
    """Bevara den angivna kandidatens identitet före länkupplösning. Bara reporoten får ha ett annat namn
    (exempelvis /tmp i stället för /private/tmp). Länkar inne i kundträdet får varken ta bort läsgränsen eller
    byta kandidat. Avvikande skiftläge vägras även på ett filsystem som annars behandlar namnen som lika."""
    def neka():
        raise SystemExit('processgräns: kandidatens väg måste behålla kunder/%s/kandidater/kNN/ utan alias, .. eller länkar till ett annat projekt: %s' % (slug, projekt))

    if '..' in Path(projekt).parts:
        neka()  # förenkla inte bort kandidatens namn före prövningen
    p = Path(os.path.abspath(projekt))
    rot = Path(os.path.realpath(root))
    # Yttersta föräldern som är reporoten: en länk längre ned får inte tolkas som en ny rot.
    ankare = None
    for a in reversed(p.parents):
        try:
            if a.samefile(rot):
                ankare = a
                break
        except FileNotFoundError:
            continue
        except OSError:
            neka()
    delar = p.relative_to(ankare).parts if ankare else ()
    prefix = ('kunder', slug, 'kandidater')
    kand = rot.joinpath(*prefix)
    for r in (rot / 'kunder', rot / 'kunder' / slug, kand):
        if Path(os.path.realpath(r)) != r:
            neka()  # också ett internt alias måste bedömas mot förankrade rötter
    upplost = Path(os.path.realpath(p))
    angiven_kandidat = tuple(x.casefold() for x in delar[:3]) == tuple(x.casefold() for x in prefix)
    if not angiven_kandidat:
        # Ett internt alias till en kandidat är inte sajtens obegränsade huvudbygge.
        verkliga = upplost.parts
        if tuple(x.casefold() for x in verkliga[:len(kand.parts)]) == tuple(x.casefold() for x in kand.parts):
            neka()
        return None
    if delar[:3] != prefix or len(delar) < 4 or not KANDIDAT.fullmatch(delar[3]):
        neka()
    kid = delar[3]
    egen = kand / kid
    if Path(os.path.realpath(egen)) != egen or not upplost.is_relative_to(egen):
        neka()
    return kid


def profil(slug, root=None, hem=None, tmp=None, nat=True, bara_sajt=False, skrivbar=None):
    import sandlada
    root = Path(root or ROOT)
    hem = hem or os.path.expanduser('~')
    fs = sandlada.installningar(slug, root=root, hem=hem)['sandbox']['filesystem']
    kid = None
    if bara_sajt or skrivbar:  # byggen av skaparens sidor: bara projektet och tempkatalogen, aldrig underlag/<slug> med
        # ägarens domlogg, VINNARE.json och statusen, eller kunder/<slug> utanför projektet (granskning 6)
        angivet = skrivbar if skrivbar else root / 'kunder' / slug / 'sajt'
        kid = kandidat_i(angivet, root, slug)
        projekt = Path(os.path.abspath(angivet))
        kund = os.path.realpath(root / 'kunder' / slug)
        if not os.path.realpath(projekt).startswith(kund + os.sep):  # en kandidats projekt ligger i kunder/<slug>/kandidater/
            raise SystemExit('processgräns: %s ligger inte under kunder/%s/' % (projekt, slug))
        tmp = tmp or tempkatalog(slug, kid)
        skriv = [str(projekt), tmp]
    else:
        projekt = root / 'kunder' / slug / 'sajt'
        tmp = tmp or tempkatalog(slug)
        skriv = list(fs['allowWrite']) + ['/tmp/nwp-granskning/%s' % slug, tmp]
    nm = Path(projekt) / 'node_modules'
    delad = None
    if nm.is_symlink():  # en worktree eller en kandidat delar sajtens beroenden: bara byggets cacher (.vite, .astro) skrivs
        # där, aldrig paketen som de andra kandidaterna och sajtens eget bygge kör (den oberoende granskningen 2026-10-05, fynd 3)
        delad = os.path.realpath(nm)
        if kid and delad != os.path.realpath(root / 'kunder' / slug / 'sajt' / 'node_modules'):
            # länken ligger i kandidatens skrivbara projekt: en sida kan ha bytt den, och läsgränsen släpper det den pekar på
            raise SystemExit('processgräns: %s pekar inte på kunder/%s/sajt/node_modules (%s)' % (nm, slug, delad))
        skriv += [os.path.join(delad, '.vite'), os.path.join(delad, '.astro')]
    # seatbelt matchar subpath mot den verkliga sökvägen: /tmp är en symlänk till /private/tmp på macOS, så varje väg ges
    # både som angiven och upplöst (annars träffar varken skrivtillåtelsen i byggets kataloger eller läsförbudet)
    verkliga = lambda vagar: list(dict.fromkeys(x for p in vagar for x in (str(p), os.path.realpath(p))))  # noqa: E731
    rader = ['(version 1)', '(allow default)', '; processgränsen för byggsteg från stoppkroken (kontroller/processgrans.py)',
             '(deny file-write*)']
    rader += ['(allow file-write* (subpath %s))' % sbpl(p) for p in verkliga(skriv)]
    rader += ['(allow file-write* (literal "/dev/null") (literal "/dev/zero") (regex #"^/dev/tty") (regex #"^/dev/fd/"))']
    # policyns uttryckliga skrivförbud efter tillåtelserna (sista träffande regel gäller): mekaniken i en repokopia under en
    # tillåten katalog förblir skrivskyddad (Codex R26, F1)
    rader += ['(deny file-write* (subpath %s))' % sbpl(p) for p in verkliga(fs['denyWrite'])]
    if kid:
        rader += lasgrans(root, slug, kid, projekt, tmp, delad, verkliga)
    rader += lasforbud(fs, verkliga)  # efter läsgränsen: hemligheterna förblir olästa också i det den släpper
    if nat:
        rader += ['(deny network-outbound)', '(allow network-outbound (remote ip "localhost:*"))', '(allow network-outbound (remote unix-socket))',
                  '(allow network-bind (local ip "localhost:*"))', '(allow network-inbound (local ip "localhost:*"))']
    else:  # --utan-nat: ett bygge behöver inget nät; localhost når dashboardens API och unix-sockeln namnuppslagen (granskning 4 och 5)
        rader += ['(deny network-outbound)', '(deny network-bind)', '(deny network-inbound)']
    return '\n'.join(rader) + '\n'


def lasgrans(root, slug, kid, projekt, tmp, delad, verkliga):
    """Byggets läsgräns för kandidaten kid (GR-20261007-r107#K1): sidans kod körs när den byggs, och utan gränsen läste den
    en annan kandidats källkod och skaparens text i underlaget. Läsning nekas som standard; undantagen är det bygget
    behöver (mätt): kandidatens eget projekt, sajtens delade node_modules (länken prövad i profil), kandidatens egen temp
    och systemets delar (SYSTEMETS), och metadata (stat, inte innehåll eller listning) för katalogerna ovanför dem, som
    vägupplösningen behöver. Sist ett stängsel: underlag/ och kunder/<slug>/kandidater/ nekas också om en tillåtelse ovan
    skulle täcka dem, och bara det egna projektet släpps igen. Sista träffande regel gäller."""
    root = Path(os.path.abspath(root))
    kand = root / 'kunder' / slug / 'kandidater'
    egna = verkliga([projekt, tmp] + ([delad] if delad else []))
    tillatna = verkliga(SYSTEMETS) + egna
    forfader = sorted({str(a) for p in tillatna for a in Path(p).parents} | {'/etc', '/tmp', '/var'})  # och rotens länkar
    # Tailwinds källsökning läser repots .gitignore och .git (filen i en worktree, katalogen i huvudutcheckningen; bara
    # själva posten, inte det som ligger i katalogen). Utan dem blir kandidatens CSS en annan än sajtens bygge ger (mätt:
    # 11 kB mot 46 kB), så de släpps: .gitignore är publik och .git en hänvisning
    git = verkliga([root / '.gitignore', root / '.git'])
    return ['; byggets läsgräns för kandidaten %s (kontroller/processgrans.py, lasgrans)' % kid,
            '(deny file-read*)',
            '(allow file-read-metadata %s)' % ' '.join('(literal %s)' % sbpl(p) for p in forfader),
            '(allow file-read* (literal "/") %s)' % ' '.join('(subpath %s)' % sbpl(p) for p in tillatna),
            '(allow file-read* %s)' % ' '.join('(literal %s)' % sbpl(p) for p in git),
            '(deny file-read* %s)' % ' '.join('(subpath %s)' % sbpl(p) for p in verkliga([root / 'underlag', kand])),
            '(allow file-read* %s)' % ' '.join('(subpath %s)' % sbpl(p) for p in verkliga([projekt])),
            '(allow file-read-metadata %s)' % ' '.join('(literal %s)' % sbpl(p) for p in verkliga([kand, kand / kid]))]


def utanfor_lasgransen(kmd, projekt, root, slug, path):
    """Programmet i kommandot, eller node som npm och paketens skript startar, upplöst, när läsgränsen inte släpper det;
    annars None. Ett sådant program fastnar i kärnan när det startas innanför gränsen (prövat 2026-10-07: processen
    hamnar i tillståndet UE och går inte att döda förrän datorn startas om), så bygget vägras i stället."""
    inom = [os.path.realpath(p) for p in SYSTEMETS + (str(projekt), str(Path(root) / 'kunder' / slug / 'sajt' / 'node_modules'))]
    for namn in (kmd[0], 'node'):
        v = shutil.which(namn, path=path)
        if v and not any(os.path.realpath(v) == p or os.path.realpath(v).startswith(p + os.sep) for p in inom):
            return os.path.realpath(v)
    return None


def lasforbud(fs, verkliga):
    ut = []
    for p in fs['denyRead']:
        if p.startswith('**/'):
            ut.append('(deny file-read* (regex #"%s"))' % regex_ur_glob(p))
        else:
            ut += ['(deny file-read* (subpath %s))' % sbpl(x) for x in verkliga([p])]
    return ut


MILJO_KATALOG = ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TERM', 'SHELL')


def profil_katalog(katalog, root=None, hem=None):
    """Profilen för ett bygge i en egen katalog utanför repot (exportens provbygge, kontroller/exportera.py): skrivning
    bara i katalogen, inget nät, hemligheterna olästa (den oberoende granskningen 2026-10-05, fynd 2)."""
    import sandlada
    fs = sandlada.installningar('x', root=root, hem=hem)['sandbox']['filesystem']
    verkliga = lambda vagar: list(dict.fromkeys(x for p in vagar for x in (str(p), os.path.realpath(p))))  # noqa: E731
    rader = ['(version 1)', '(allow default)', '; processgränsen för ett bygge i en egen katalog (kontroller/processgrans.py)',
             '(deny file-write*)']
    rader += ['(allow file-write* (subpath %s))' % sbpl(p) for p in verkliga([katalog])]
    rader += ['(allow file-write* (literal "/dev/null") (literal "/dev/zero") (regex #"^/dev/tty") (regex #"^/dev/fd/"))']
    rader += lasforbud(fs, verkliga)
    rader += ['(deny network-outbound)', '(deny network-bind)', '(deny network-inbound)']
    return '\n'.join(rader) + '\n'


SKYDDADE_HEMFILER = ('.zprofile', '.zshrc', '.zshenv', '.zlogin', '.bash_profile', '.bashrc', '.profile', '.gitconfig', '.npmrc',
                     '.claude.json')
# också det som kör kod senare utanför gränsen: gits egen konfiguration (core.fsmonitor, krokar), Impeccables motorer och
# Playwrights webbläsare (granskningen av r73, N3)
SKYDDADE_HEMKATALOGER = ('.ssh', '.claude', '.local/bin', '.nortropic-hemligheter', 'Library/LaunchAgents', '.config/gh', '.config/git',
                         '.impeccable', 'Library/Caches/ms-playwright')


def profil_underhallsprov(root, wt, hem=None):
    """Profilen för underhållets installation av testsajtens beroenden i en worktree (testsajtens npm ci; rökprovet
    själv kan inte köras i en sandlåda, eftersom det prövar processgränsen med sandbox-exec):
    hemligheterna olästa, och ingen skrivning i huvudutcheckningen (dess .venv och node_modules, som worktreen länkar
    till; bara worktreens egen git-katalog), i Homebrew, i skalprofilerna eller i Claude Codes filer. Nät och skrivning
    i worktreen, tempkatalogerna och cacherna går (den oberoende granskningen av r72, L4)."""
    hem = Path(hem or Path.home())
    verkliga = lambda vagar: list(dict.fromkeys(x for p in vagar for x in (str(p), os.path.realpath(p))))  # noqa: E731
    rader = ['(version 1)', '(allow default)', '; underhållets prov med en kandidat (kontroller/processgrans.py)']
    import sandlada
    fs = sandlada.installningar('x', root=root, hem=str(hem))['sandbox']['filesystem']
    rader += lasforbud(fs, verkliga)
    # .venv och node_modules också genom sina länkar (en worktree som root länkar dem till huvudutcheckningen)
    neka = [Path(root), Path(root) / '.venv', Path(root) / 'kontroller' / 'node_modules', '/opt/homebrew', '/usr/local']
    try:  # är roten en worktree ligger repots git-katalog (krokar, config) i huvudutcheckningen
        import subprocess
        gemensam = subprocess.run(['git', '-C', str(root), 'rev-parse', '--path-format=absolute', '--git-common-dir'], capture_output=True,
                                  text=True, timeout=30).stdout.strip()
        if gemensam:
            neka.append(Path(gemensam))
    except (OSError, subprocess.SubprocessError):
        pass
    neka += [hem / d for d in SKYDDADE_HEMKATALOGER]
    rader += ['(deny file-write* (subpath %s))' % sbpl(x) for x in verkliga(neka)]
    rader += ['(deny file-write* (literal %s))' % sbpl(x) for x in verkliga([hem / f for f in SKYDDADE_HEMFILER])]
    try:  # worktreens egen git-katalog (index, HEAD), som .git-filen i worktreen pekar på
        gitkat = Path((Path(wt) / '.git').read_text(encoding='utf-8').split('gitdir:', 1)[1].strip())
    except (OSError, IndexError):
        gitkat = Path(root) / '.git' / 'worktrees' / Path(wt).name
    rader += ['(allow file-write* (subpath %s))' % sbpl(x) for x in verkliga([gitkat, wt])]
    return '\n'.join(rader) + '\n'


def kor_i_katalog(katalog, kmd, timeout=900):
    """(slutkod, utdata) för kmd i katalogen innanför gränsen, med en minimal miljö: inga nycklar, inga NWP_- eller
    Claude-variabler, ingen proxy."""
    import subprocess
    katalog = Path(katalog)
    if not os.access(SANDBOX_EXEC, os.X_OK):
        return 2, 'processgräns saknas: %s finns inte; bygget körs inte utan gräns' % SANDBOX_EXEC
    tmp = katalog / '.tmp'
    tmp.mkdir(exist_ok=True)
    miljo = {k: os.environ[k] for k in MILJO_KATALOG if k in os.environ}
    miljo.update(TMPDIR=str(tmp), NWP_PROCESSGRANS='1', ASTRO_TELEMETRY_DISABLED='1')
    try:
        r = subprocess.run([SANDBOX_EXEC, '-p', profil_katalog(katalog), *[str(x) for x in kmd]], cwd=str(katalog), env=miljo,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, 'tidsgränsen %d s nåddes' % timeout
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    egna, kmd = (argv[:argv.index('--')], argv[argv.index('--') + 1:]) if '--' in argv else (argv, [])
    p = argparse.ArgumentParser(prog='processgrans', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--root', default=None)
    p.add_argument('--hem', default=None)
    p.add_argument('--skriv-profil', action='store_true', help='skriv profilen och avsluta')
    p.add_argument('--utan-nat', action='store_true', help='inget nät alls, inte heller localhost (byggen av skaparens sidor)')
    p.add_argument('--bara-sajt', action='store_true', help='skrivning bara i kunder/<slug>/sajt och tempkatalogen (byggen av skaparens sidor)')
    p.add_argument('--skrivbar', default=None, help='skrivning bara i den här projektkatalogen under kunder/<slug>/ och tempkatalogen; '
                                                    'en kandidats projekt (kunder/<slug>/kandidater/kNN/) får dessutom byggets läsgräns')
    a = p.parse_args(egna)
    prof = profil(a.slug, a.root, a.hem, nat=not a.utan_nat, bara_sajt=a.bara_sajt, skrivbar=a.skrivbar)
    kid = kandidat_i(a.skrivbar, a.root or ROOT, a.slug) if a.skrivbar else None  # profil har prövat vägen
    if a.skriv_profil:
        sys.stdout.write(prof)
        return 0
    if not kmd:
        print('inget kommando efter --', file=sys.stderr)
        return 2
    if not os.access(SANDBOX_EXEC, os.X_OK):
        print('processgräns saknas: %s finns inte; byggsteget körs inte utan gräns' % SANDBOX_EXEC, file=sys.stderr)
        return 2
    print('processgräns: sandbox-exec kring %s' % ' '.join(kmd[:3]), file=sys.stderr, flush=True)
    miljo = ren_miljo(slug=a.slug, root=a.root, hem=a.hem, kid=kid)
    if kid and (fel := utanfor_lasgransen(kmd, os.path.abspath(a.skrivbar), a.root or ROOT, a.slug, miljo.get('PATH'))):
        print('processgräns: %s ligger utanför byggets läsgräns (SYSTEMETS); bygget körs inte' % fel, file=sys.stderr)
        return 2
    os.makedirs(miljo['TMPDIR'], exist_ok=True)
    if kid:  # en kandidats bygge startar i sitt projekt: utanför läsgränsen kan processen inte läsa sin arbetskatalog (getcwd ger EPERM)
        os.chdir(os.path.abspath(a.skrivbar))
    os.execve(SANDBOX_EXEC, ['sandbox-exec', '-p', prof, *kmd], miljo)
    return 2


if __name__ == '__main__':
    sys.exit(main())
