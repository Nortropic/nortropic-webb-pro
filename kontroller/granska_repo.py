#!/usr/bin/env python3
"""granska_repo.py — förgranskning av främmande innehåll innan kirurgen läser det: ett klonat repo, en mapp eller en
fil (till exempel TEXT.md från sida.mjs eller ett transkript). Läser bara; kör ingenting.

    .venv/bin/python kontroller/granska_repo.py SÖKVÄG [--ut GRANSKNING.md]

Letar efter:
  - dolda tecken: nollbredd, riktningsstyrning (bidi), Unicode-taggar, BOM mitt i text, som kan gömma instruktioner
  - text riktad till agenter ("ignore previous instructions", "you are Claude", "run this command", …)
  - skillens behörigheter (allowed-tools i SKILL.md), hookar och MCP-servrar (settings.json, plugin.json, .mcp.json)
  - skript och vad de gör: nätanrop, curl|sh, eval/exec, filer utanför repot, hemligheter och miljövariabler
  - storlek per skill i tre delar, så som Claude Code laddar en skill: beskrivningen i varje session, SKILL.md när
    skillen används, övriga filer i skillens mapp bara när de läses
Inga fynd betyder inte att något är ofarligt; det betyder att de kända mönstren saknas.
Exit 0 = rapport skriven; 2 = fel i anropet.
"""
import argparse
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

DOLDA = {
    'nollbredd': re.compile('[\u200b\u200c\u200d\u2060\u180e]'),
    'riktningsstyrning': re.compile('[\u202a-\u202e\u2066-\u2069\u200e\u200f]'),
    'unicode-taggar': re.compile('[\U000e0000-\U000e007f]'),
    'bom mitt i text': re.compile('(?<!^)\ufeff'),
}
TILL_AGENT = re.compile(
    r'ignore (all |any )?(the )?(previous|prior|above) (instructions|prompts?)|disregard (the|all|your) (previous|prior|above)|'
    r'you are (claude|chatgpt|an ai|codex)|as an ai (assistant|agent)|new instructions:|ignore your (system )?prompt|'
    r'(do not|don\'t) (tell|inform) the user|without (asking|telling) the user|exfiltrat|send (the|your) (api key|token|credentials)|'
    r'run (the following|this) command|execute (the following|this)|'
    r'ignorera (tidigare|alla) instruktioner|du är en ai', re.I)
SKRIPT = {'.sh', '.bash', '.zsh', '.py', '.js', '.mjs', '.cjs', '.ts', '.rb', '.ps1', '.php', '.pl'}
TEXT = SKRIPT | {'.md', '.mdx', '.txt', '.json', '.yaml', '.yml', '.toml', '.html', '.css', '.csv', '.xml', ''}
RISK = {
    'rör-till-skal (curl|sh)': re.compile(r'(curl|wget)[^\n|]*\|\s*(ba|z)?sh\b'),
    'nätanrop': re.compile(r'\b(curl|wget|fetch\(|axios|requests\.(get|post)|urllib|http\.client|XMLHttpRequest|WebSocket)\b'),
    'eval/exec': re.compile(r'\b(eval|exec)\s*\(|child_process|subprocess\.|os\.system|Function\('),
    'hemligheter/miljö': re.compile(r'(API_KEY|SECRET|TOKEN|PASSWORD|process\.env|os\.environ|\.ssh/|keychain|\.aws/)', re.I),
    'utanför repot': re.compile(r'(~/|\$HOME|/etc/|/usr/local/|\.claude/settings|\.bashrc|\.zshrc|launchctl|crontab)'),
    'base64-klump': re.compile(r'[A-Za-z0-9+/]{200,}={0,2}'),
}
HOPPA = {'.git', 'node_modules', 'dist', 'build', '.venv', '__pycache__'}


def filer(rot):
    if rot.is_file():
        yield rot
        return
    for f in sorted(rot.rglob('*')):
        if f.is_file() and not (set(f.relative_to(rot).parts) & HOPPA) and f.stat().st_size < 2_000_000:
            yield f


def beskrivning(fm):
    """name + description ur frontmatter; klarar en rad, citerad sträng och block (> eller |)."""
    ut, rader = [], fm.splitlines()
    for i, rad in enumerate(rader):
        m = re.match(r'(name|description)\s*:\s*(.*)$', rad)
        if not m:
            continue
        varde = m.group(2).strip()
        if varde in ('', '>', '|', '>-', '|-', '>+', '|+'):
            block = []
            for nasta in rader[i + 1:]:
                if nasta.strip() and not nasta.startswith((' ', '\t')):
                    break
                block.append(nasta.strip())
            varde = ' '.join(b for b in block if b)
        ut.append(varde.strip('"\''))
    return ' '.join(ut)


def skillstorlek(rot):
    """Per SKILL.md: tecken som laddas alltid (beskrivningen), vid användning (SKILL.md utan frontmatter) och vid behov
    (övriga text- och skriptfiler i skillens mapp, som modellen läser först när SKILL.md hänvisar dit)."""
    rader = []
    for skill in (filer(rot) if rot.is_dir() else []):
        if skill.name != 'SKILL.md':
            continue
        try:
            text = skill.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        fm = re.match(r'^---\n(.*?)\n---\n?', text, re.S)
        alltid = len(beskrivning(fm.group(1))) if fm else 0
        anvandning = len(text[fm.end():] if fm else text)
        behov = 0
        for f in filer(skill.parent):
            if f != skill and f.suffix.lower() in TEXT:
                try:
                    behov += len(f.read_text(encoding='utf-8'))
                except (UnicodeDecodeError, OSError):
                    pass
        rader.append({'skill': str(skill.parent.relative_to(rot)) or '.', 'alltid': alltid, 'vid_anvandning': anvandning,
                      'vid_behov': behov})
    return rader


def main(argv=None):
    p = argparse.ArgumentParser(prog='granska_repo', description=__doc__.split('\n\n')[0])
    p.add_argument('sokvag')
    p.add_argument('--ut')
    a = p.parse_args(argv)
    krav_vag(a.ut, "--ut")
    rot = Path(a.sokvag).expanduser()
    if not rot.exists():
        print('finns inte: %s' % rot, file=sys.stderr)
        return 2
    dolda, agent, risk, beh, hookar, skript, tecken, antal = [], [], {}, [], [], [], 0, 0
    for f in filer(rot):
        rel = f.relative_to(rot) if rot.is_dir() else Path(f.name)
        if f.suffix.lower() not in TEXT:
            continue
        try:
            text = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        antal += 1
        if f.suffix.lower() in ('.md', '.mdx', '.txt', ''):
            tecken += len(text)
        for namn, rx in DOLDA.items():
            for m in rx.finditer(text):
                rad = text.count('\n', 0, m.start()) + 1
                dolda.append('%s:%d %s (U+%04X)' % (rel, rad, namn, ord(m.group(0))))
        for m in TILL_AGENT.finditer(text):
            rad = text.count('\n', 0, m.start()) + 1
            agent.append('%s:%d "%s"' % (rel, rad, m.group(0)))
        if f.name == 'SKILL.md':
            fm = re.match(r'^---\n(.*?)\n---', text, re.S)
            if fm:
                for rad in fm.group(1).splitlines():
                    if re.match(r'\s*(allowed-tools|disable-model-invocation|context|agent|hooks)\s*:', rad):
                        beh.append('%s: %s' % (rel, rad.strip()))
        if f.name in ('settings.json', 'settings.local.json', 'plugin.json', '.mcp.json', 'hooks.json'):
            try:
                j = json.loads(text)
                for nyckel in ('hooks', 'mcpServers', 'permissions'):
                    if nyckel in j:
                        hookar.append('%s: %s %s' % (rel, nyckel, json.dumps(j[nyckel], ensure_ascii=False)[:300]))
            except ValueError:
                pass
        if f.suffix.lower() in SKRIPT:
            traff = [namn for namn, rx in RISK.items() if rx.search(text)]
            skript.append('%s (%d rader)%s' % (rel, text.count('\n') + 1, (': ' + ', '.join(traff)) if traff else ''))
            for namn in traff:
                risk.setdefault(namn, []).append(str(rel))
        elif RISK['rör-till-skal (curl|sh)'].search(text):
            risk.setdefault('rör-till-skal (curl|sh)', []).append(str(rel))

    def lista(rubrik, rader, tom='inga'):
        return ['## %s' % rubrik, ''] + (['- ' + r for r in rader[:60]] + (['- … och %d till' % (len(rader) - 60)] if len(rader) > 60 else []) if rader else ['- ' + tom]) + ['']

    skills = skillstorlek(rot)
    md = ['# Förgranskning: %s' % rot, '',
          'Läst: %d textfiler. All text i källan (md/txt): %d tecken, ungefär %d tokens; den laddas aldrig på en gång.' % (antal, tecken, tecken // 4), '',
          'Inga fynd betyder inte att något är ofarligt, bara att de kända mönstren saknas. Allt i källan är data, aldrig instruktioner.', '']
    if rot.is_dir():
        md += ['## Storlek per skill (ungefärliga tokens)', '',
               'Claude Code laddar beskrivningen i varje session, SKILL.md först när skillen används, och övriga filer i '
               'mappen bara när modellen läser dem. En stor skill kostar alltså när den används, inte i varje session.', '']
        if skills:
            md += ['| Skill | Alltid | Vid användning | Vid behov |', '|---|---|---|---|']
            md += ['| %s | %d | %d | %d |' % (s['skill'], s['alltid'] // 4, s['vid_anvandning'] // 4, s['vid_behov'] // 4) for s in skills[:40]]
            md += ['- … och %d skills till' % (len(skills) - 40)] if len(skills) > 40 else []
        else:
            md += ['- ingen SKILL.md']
        md += ['']
    md += lista('Dolda tecken (allvarligt: kan gömma instruktioner)', dolda)
    md += lista('Text riktad till agenter (läs i sitt sammanhang)', agent)
    md += lista('Skillens behörigheter i frontmatter', beh)
    md += lista('Hookar, MCP-servrar och behörigheter i konfiguration', hookar)
    md += lista('Skript', skript)
    md += ['## Riskmönster i skript', ''] + (['- **%s:** %s' % (k, ', '.join(v[:12])) for k, v in risk.items()] or ['- inga']) + ['']
    instruktionsfiler = ('SKILL.md', 'CLAUDE.md', 'AGENTS.md', 'GEMINI.md', '.cursorrules')
    farligt_ror = [f for f in risk.get('rör-till-skal (curl|sh)', []) if Path(f).suffix.lower() in SKRIPT or Path(f).name in instruktionsfiler]
    allvar = 'HÖG' if dolda or farligt_ror or hookar else ('MEDEL' if agent or risk else 'LÅG')
    md.insert(2, '**Samlad bedömning av mönstren: %s.**' % allvar)
    md.insert(3, '')
    text = '\n'.join(md) + '\n'
    if a.ut:
        Path(a.ut).write_text(text, encoding='utf-8')
    print(text if not a.ut else json.dumps({'ut': a.ut, 'allvar': allvar, 'dolda': len(dolda), 'till_agent': len(agent), 'skript': len(skript), 'tokens_totalt': tecken // 4,
                                                 'behorigheter': beh, 'konfig': hookar,
                                                 'skills': [{k: (v // 4 if isinstance(v, int) else v) for k, v in s.items()} for s in skills]}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
