#!/usr/bin/env python3
"""sandlada.py — inställningarna för Claude Codes inbyggda sandlåda i en byggkörning (kor.sh, NWP_SANDLADA=pa).

    .venv/bin/python kontroller/sandlada.py <slug> [--doman exempel.se ...] [--gh-dir DIR] [--av] [--root R] [--hem H]

Skriver JSON för `claude --settings`: med sandlådan på (standard) får Bash bara skriva i kunder/<slug>, underlag/<slug>,
backlog/ och tmp; mekaniken (kontroller, kritik, kunskap, mall, .claude, dashboard, kor.sh, .git …) är skrivskyddad;
hemligheter (~/.nortropic-hemligheter, ~/.ssh, .env …) är olästa; nätet går bara till verksamhetens domän,
NWP_NAT_DOMANER och listan i kontroller/sandlada-domaner.txt; REFERO_MCP_TOKEN syns inte för Bash. --av ger bara
env-delen (GH_CONFIG_DIR). Backlogposten om gräns på processnivå (Codex-revisionen 2026-10-03, F1); docs:
code.claude.com/docs/en/sandboxing. Sandlådan gäller Bash och dess barn, inte Read/Write/Edit, MCP eller krokar:
tillåtelselistorna i kor.sh behövs fortfarande.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKYDDAT = ('kontroller', 'kritik', 'kunskap', 'mall', '.claude', 'dashboard', 'kor.sh', 'dashboard.sh', 'CLAUDE.md', 'BESLUT.md',
           'LARDOMAR.md', '.gitignore', '.git')
HEMLIGT = ('~/.nortropic-hemligheter', '~/.ssh', '~/.aws', '~/.config/gh', '~/.claude.json', '**/.env', '**/.env.*', '**/*.pem', '**/*.key')


def domanlista(root, extra=()):
    fil = Path(root) / 'kontroller' / 'sandlada-domaner.txt'
    rader = [r.strip() for r in fil.read_text(encoding='utf-8').splitlines()] if fil.is_file() else []
    ut = []
    for d in [r for r in rader if r and not r.startswith('#')] + [x for x in extra if x]:
        d = d.strip().lower().rstrip('/')
        d = d.split('//', 1)[1] if '//' in d else d
        d = d.split('/', 1)[0]
        if not d or d in ut:
            continue
        ut.append(d)
        if d.startswith('www.') and d[4:] not in ut:  # www och bar domän är samma verksamhet
            ut.append(d[4:])
        elif not d.startswith('*.') and d.count('.') == 1 and 'www.' + d not in ut:
            ut.append('www.' + d)
    return ut


def installningar(slug, domaner=(), gh_dir=None, sandlada=True, root=None, hem=None):
    root = Path(root or ROOT)
    hem = hem or os.path.expanduser('~')
    rot = str(root)
    ut = {}
    if gh_dir:
        ut['env'] = {'GH_CONFIG_DIR': gh_dir}
    if sandlada:
        ut['sandbox'] = {
            'enabled': True, 'failIfUnavailable': True, 'allowUnsandboxedCommands': False, 'autoAllowBashIfSandboxed': False,
            'filesystem': {
                'denyWrite': ['%s/%s' % (rot, p) for p in SKYDDAT],
                'allowWrite': ['%s/kunder/%s' % (rot, slug), '%s/underlag/%s' % (rot, slug), '%s/backlog' % rot, '/tmp/nwp-bygge-%s' % slug,
                               '%s/.npm' % hem, '%s/.cache' % hem, '%s/Library/Caches' % hem],
                'denyRead': [p.replace('~', hem, 1) if p.startswith('~') else p for p in HEMLIGT]},
            'network': {'allowedDomains': domanlista(root, domaner), 'allowLocalBinding': True},
            'credentials': {'envVars': [{'name': 'REFERO_MCP_TOKEN', 'mode': 'deny'}]}}
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='sandlada', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--doman', action='append', default=[])
    p.add_argument('--gh-dir', default=None)
    p.add_argument('--av', action='store_true', help='bara env-delen, ingen sandlåda')
    p.add_argument('--root', default=None)
    p.add_argument('--hem', default=None)
    a = p.parse_args(argv)
    print(json.dumps(installningar(a.slug, a.doman, a.gh_dir, not a.av, a.root, a.hem), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
