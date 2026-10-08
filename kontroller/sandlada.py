#!/usr/bin/env python3
"""sandlada.py — inställningarna för Claude Codes inbyggda sandlåda i en byggkörning (kor.sh, NWP_SANDLADA=pa).

    .venv/bin/python kontroller/sandlada.py <slug> [--doman exempel.se ...] [--gh-dir DIR] [--av] [--root R] [--hem H]

Skriver JSON för `claude --settings`: med sandlådan på (standard) får Bash bara skriva i kunder/<slug>, underlag/<slug>,
backlog/ och tmp; mekaniken (kontroller, kritik, kunskap, mall, .claude, dashboard, kor.sh, .git …) är skrivskyddad;
hemligheter (~/.nortropic-hemligheter, ~/.ssh, .env …) är olästa; nätet går bara till verksamhetens domän,
NWP_NAT_DOMANER och listan i kontroller/sandlada-domaner.txt; REFERO_MCP_TOKEN syns inte för Bash. --av lämnar
sandlådan avstängd men behåller sessionens nekanden och eventuell GH_CONFIG_DIR. Backlogposten om gräns på processnivå (Codex-revisionen 2026-10-03, F1); docs:
code.claude.com/docs/en/sandboxing. Sandlådan gäller Bash och dess barn, inte Read/Write/Edit, MCP eller krokar:
tillåtelselistorna i kor.sh behövs fortfarande. Chromium kan inte starta inne i sandlådan (mach-register nekas), så
webbläsarverktygen körs av kontroller/webbtjanst.py utanför den, med samma domänlista (domanlista) som proxyn.
"""
import argparse
import json
import os
import sys
from pathlib import Path
import kompetens

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


TILLATNA_I_ROTEN = ('kunder', 'underlag', 'backlog')


def nekade_skrivvagar(root, slug):
    """Sandlådans standard är att hela arbetskatalogen får skrivas, och allowWrite bara utökar den. Därför nekas allt i
    reporoten utom kunder/, underlag/ och backlog/, och under kunder/ och underlag/ varje syskon till byggets egen
    katalog, plus körmiljön (.venv, kontroller/node_modules) och den fasta listan (Codex 2026-10-04, F1). Listan räknas
    upp vid starten; att inga nya kataloger kan tillkomma bredvid byggets under körningen sköter kor.sh (flaggan uchg
    på kunder/ och underlag/, lyft flagga eller ny post = slutkod 3). Nekande går före tillåtande i sandlådans
    skrivregler (mätt 2026-10-04), så kunder/ och underlag/ kan inte nekas som helhet med byggets katalog undantagen.
    Slugvakten prövar symlänkar när de används."""
    root = Path(root)
    namn = {p.name for p in root.iterdir()} if root.is_dir() else set()
    ut = ['%s/%s' % (root, p) for p in SKYDDAT] + ['%s/.venv' % root, '%s/kontroller/node_modules' % root]
    ut += sorted('%s/%s' % (root, n) for n in namn if n not in TILLATNA_I_ROTEN and n not in SKYDDAT and n != '.venv')
    for mapp in ('kunder', 'underlag'):
        d = root / mapp
        if d.is_dir():
            ut += sorted('%s/%s' % (d, p.name) for p in d.iterdir() if p.name != slug)
    return ut


def fryst_underlagsvagar(root, slug):
    """Godkännandets underlagsgrund under underlag/<slug>: filerna i skapande.UNDERLAGSGRUND och katalogerna i
    UNDERLAGSKATALOGER. Från en godkänd startsida nekas bygget skrivning där (kor.sh: --fryst-underlag hit, Write och Edit
    i --disallowedTools), eftersom en ändring ger en annan underlagsversion och gör godkännandet till historik
    (skapande.godkand_giltig; GR-20261008-r117-claude#A3). Nekande går före tillåtande, så resten av underlag/<slug>
    skrivs som förut."""
    import skapande
    u = Path(root) / 'underlag' / slug
    return [str(u / n) for n in skapande.UNDERLAGSGRUND + skapande.UNDERLAGSKATALOGER]


def installningar(slug, domaner=(), gh_dir=None, sandlada=True, root=None, hem=None, extra_skriv=(), fryst_underlag=False):
    """extra_skriv: ytterligare skrivbara kataloger, till exempel en granskares arbetskatalog under /tmp/nwp-granskning.
    fryst_underlag: från en godkänd startsida nekas Bash och barnen godkännandets underlagsgrund (fryst_underlagsvagar)."""
    root = Path(root or ROOT)
    hem = hem or os.path.expanduser('~')
    rot = str(root)
    # Lagret samlar andra kunders råsvar och åtkomsttoken. Bara Kundstarts
    # värdprocess får läsa det, inte byggsessionen eller dess Bash-barn.
    kundstart = str(root / 'underlag/kundstart')
    ut = {'permissions': {'deny': ['Read(//%s/**)' % kundstart.strip('/'), *kompetens.skill_nekas(root)]}}
    if gh_dir:
        ut['env'] = {'GH_CONFIG_DIR': gh_dir}
    if sandlada:
        ut['sandbox'] = {
            'enabled': True, 'failIfUnavailable': True, 'allowUnsandboxedCommands': False, 'autoAllowBashIfSandboxed': False,
            'filesystem': {
                'denyWrite': nekade_skrivvagar(root, slug) + (fryst_underlagsvagar(root, slug) if fryst_underlag else []),
                'allowWrite': ['%s/kunder/%s' % (rot, slug), '%s/underlag/%s' % (rot, slug), '%s/backlog' % rot, '/tmp/nwp-bygge-%s' % slug,
                               '%s/.npm' % hem, '%s/.cache' % hem, '%s/Library/Caches' % hem] + [str(x) for x in extra_skriv],
                'denyRead': [p.replace('~', hem, 1) if p.startswith('~') else p for p in HEMLIGT] + [kundstart]},
            'network': {'allowedDomains': domanlista(root, domaner), 'allowLocalBinding': True},
            'credentials': {'envVars': [{'name': 'REFERO_MCP_TOKEN', 'mode': 'deny'}]}}
    # Sessionens egna filverktyg (Read) nekas hemlighetsmappen med en vanlig regel, med eller utan sandlåda (Codex R24; där
    # ligger också dashboardnyckeln, dashboard/server.py NYCKELFIL)
    ut['permissions']['deny'].append('Read(//%s/.nortropic-hemligheter/**)' % hem.strip('/'))
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='sandlada', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--doman', action='append', default=[])
    p.add_argument('--gh-dir', default=None)
    p.add_argument('--av', action='store_true', help='ingen sandlåda, behåll sessionens nekanden och eventuell env-del')
    p.add_argument('--root', default=None)
    p.add_argument('--hem', default=None)
    p.add_argument('--fryst-underlag', action='store_true', help='från en godkänd startsida: godkännandets underlagsgrund nekas skrivning')
    a = p.parse_args(argv)
    print(json.dumps(installningar(a.slug, a.doman, a.gh_dir, not a.av, a.root, a.hem, fryst_underlag=a.fryst_underlag), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
