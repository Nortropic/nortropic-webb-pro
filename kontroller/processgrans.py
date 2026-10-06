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

    .venv/bin/python kontroller/processgrans.py <slug> [--root R] [--hem H] [--skriv-profil] [--utan-nat] [--bara-sajt | --skrivbar DIR] -- <kommando …>
Slutkoden är kommandots. Utan sandbox-exec (annat system) vägras körningen (slutkod 2): gränsen får aldrig tyst saknas.
"""
import argparse
import os
import re
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


def tempkatalog(slug):
    """Körningens egen tempkatalog innanför gränsen: under byggets eget tempområde, aldrig systemets (Codex R26, F1)."""
    return '/tmp/nwp-bygge-%s/tmp' % slug


def ren_miljo(miljo=None, slug=None, root=None, hem=None):
    """Miljön innanför gränsen: samma skydd som den vanliga sandlådans credentials-policy (sandlada.py, REFERO_MCP_TOKEN)
    plus proxyvariablerna, som inte gäller härinne (nätet är localhost; en proxyvariabel utifrån skulle bara vilseleda
    hamta_sajt), och markören NWP_PROCESSGRANS=1 samt TMPDIR i körningens egen tempkatalog (Codex R26, F1/F27)."""
    import sandlada
    miljo = dict(os.environ if miljo is None else miljo)
    policy = sandlada.installningar(slug or 'x', root=root, hem=hem)['sandbox'].get('credentials', {}).get('envVars', [])
    nekade = {p['name'] for p in policy if p.get('mode') == 'deny'} | {'REFERO_MCP_TOKEN'}
    for k in list(miljo):
        if k in nekade or k.upper().endswith('_PROXY'):
            del miljo[k]
    miljo['NWP_PROCESSGRANS'] = '1'
    if slug:
        miljo['TMPDIR'] = tempkatalog(slug)
    return miljo


def profil(slug, root=None, hem=None, tmp=None, nat=True, bara_sajt=False, skrivbar=None):
    import sandlada
    root = Path(root or ROOT)
    hem = hem or os.path.expanduser('~')
    fs = sandlada.installningar(slug, root=root, hem=hem)['sandbox']['filesystem']
    if bara_sajt or skrivbar:  # byggen av skaparens sidor: bara projektet och tempkatalogen, aldrig underlag/<slug> med
        # ägarens domlogg, VINNARE.json och statusen, eller kunder/<slug> utanför projektet (granskning 6)
        projekt = Path(skrivbar) if skrivbar else root / 'kunder' / slug / 'sajt'
        kund = os.path.realpath(root / 'kunder' / slug)
        if not os.path.realpath(projekt).startswith(kund + os.sep):  # en kandidats projekt ligger i kunder/<slug>/kandidater/
            raise SystemExit('processgräns: %s ligger inte under kunder/%s/' % (projekt, slug))
        skriv = [str(projekt), tmp or tempkatalog(slug)]
    else:
        projekt = root / 'kunder' / slug / 'sajt'
        skriv = list(fs['allowWrite']) + ['/tmp/nwp-granskning/%s' % slug, tmp or tempkatalog(slug)]
    nm = Path(projekt) / 'node_modules'
    if nm.is_symlink():  # en worktree eller en kandidat delar sajtens beroenden: bara byggets cacher (.vite, .astro) skrivs
        # där, aldrig paketen som de andra kandidaterna och sajtens eget bygge kör (den oberoende granskningen 2026-10-05, fynd 3)
        delad = os.path.realpath(nm)
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
    rader += lasforbud(fs, verkliga)
    if nat:
        rader += ['(deny network-outbound)', '(allow network-outbound (remote ip "localhost:*"))', '(allow network-outbound (remote unix-socket))',
                  '(allow network-bind (local ip "localhost:*"))', '(allow network-inbound (local ip "localhost:*"))']
    else:  # --utan-nat: ett bygge behöver inget nät; localhost når dashboardens API och unix-sockeln namnuppslagen (granskning 4 och 5)
        rader += ['(deny network-outbound)', '(deny network-bind)', '(deny network-inbound)']
    return '\n'.join(rader) + '\n'


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
SKYDDADE_HEMKATALOGER = ('.ssh', '.claude', '.local/bin', '.nortropic-hemligheter', 'Library/LaunchAgents', '.config/gh')


def profil_underhallsprov(root, wt, hem=None):
    """Profilen för underhållets prov med en kandidat i en worktree (rökprovet, regressionsfallen, testsajtens npm ci):
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
    p.add_argument('--skrivbar', default=None, help='skrivning bara i den här projektkatalogen under kunder/<slug>/ (en kandidats sajt) och tempkatalogen')
    a = p.parse_args(egna)
    prof = profil(a.slug, a.root, a.hem, nat=not a.utan_nat, bara_sajt=a.bara_sajt, skrivbar=a.skrivbar)
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
    miljo = ren_miljo(slug=a.slug, root=a.root, hem=a.hem)
    os.makedirs(miljo['TMPDIR'], exist_ok=True)
    os.execve(SANDBOX_EXEC, ['sandbox-exec', '-p', prof, *kmd], miljo)
    return 2


if __name__ == '__main__':
    sys.exit(main())
