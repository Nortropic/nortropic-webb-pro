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

    .venv/bin/python kontroller/processgrans.py <slug> [--root R] [--hem H] [--skriv-profil] -- <kommando …>
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


def profil(slug, root=None, hem=None, tmp=None):
    import sandlada
    root = Path(root or ROOT)
    hem = hem or os.path.expanduser('~')
    fs = sandlada.installningar(slug, root=root, hem=hem)['sandbox']['filesystem']
    skriv = list(fs['allowWrite']) + ['/tmp/nwp-granskning/%s' % slug, tmp or tempkatalog(slug)]
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
    for p in fs['denyRead']:
        if p.startswith('**/'):
            rader.append('(deny file-read* (regex #"%s"))' % regex_ur_glob(p))
        else:
            rader += ['(deny file-read* (subpath %s))' % sbpl(x) for x in verkliga([p])]
    rader += ['(deny network-outbound)', '(allow network-outbound (remote ip "localhost:*"))', '(allow network-outbound (remote unix-socket))',
              '(allow network-bind (local ip "localhost:*"))', '(allow network-inbound (local ip "localhost:*"))']
    return '\n'.join(rader) + '\n'


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    egna, kmd = (argv[:argv.index('--')], argv[argv.index('--') + 1:]) if '--' in argv else (argv, [])
    p = argparse.ArgumentParser(prog='processgrans', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--root', default=None)
    p.add_argument('--hem', default=None)
    p.add_argument('--skriv-profil', action='store_true', help='skriv profilen och avsluta')
    a = p.parse_args(egna)
    prof = profil(a.slug, a.root, a.hem)
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
