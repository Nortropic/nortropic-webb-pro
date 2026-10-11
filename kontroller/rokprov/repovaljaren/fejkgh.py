#!/usr/bin/env python3
"""Repoväljarens provets gh (kunskap/andringar.md, Repoväljaren): svarar som GitHub CLI på de anrop repoväljaren gör,
ur JSON-filen i NWP_FEJKGH: repo list <org> --json …, repo clone <org>/<namn> <mål> och auth git-credential. Läget
utgangen, saknas och natfel ger gh:s egna felutskrifter (gh 2.x). Klonen går till provrotens nakna repon genom gits
url.<…>.insteadOf i provets miljö, så att riktiga GitHub aldrig nås. Varje anrop skrivs i filens logg."""
import json
import os
import subprocess
import sys

FEL = {
    'utgangen': (1, 'HTTP 401: Bad credentials (https://api.github.com/graphql)\nTry authenticating with:  gh auth login\n'),
    'saknas': (4, 'To get started with GitHub CLI, please run:  gh auth login\n'
                  'Alternatively, populate the GH_TOKEN environment variable with a GitHub API authentication token.\n'),
    'natfel': (1, 'error connecting to api.github.com\ncheck your internet connection or https://githubstatus.com\n'),
}


def main(argv):
    with open(os.environ['NWP_FEJKGH'], encoding='utf-8') as f:
        cfg = json.load(f)
    with open(cfg['logg'], 'a', encoding='utf-8') as f:
        f.write(json.dumps(argv, ensure_ascii=False) + '\n')
    lage = cfg.get('lage', 'ok')
    if argv[:2] == ['auth', 'git-credential']:
        return 0  # provets fjärrar är lokala och frågar aldrig efter en inloggning
    if lage in FEL and argv[:1] == ['repo']:
        kod, text = FEL[lage]
        sys.stderr.write(text)
        return kod
    if argv[:2] == ['repo', 'list'] and len(argv) > 2:
        print(json.dumps(cfg['repon'], ensure_ascii=False))
        return 0
    if argv[:2] == ['repo', 'clone'] and len(argv) >= 4:
        return subprocess.run(['git', 'clone', '-q', 'https://github.com/%s' % argv[2], argv[3]]).returncode
    sys.stderr.write('fejkgh: okänt anrop %s\n' % ' '.join(argv))
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
