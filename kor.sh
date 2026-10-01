#!/bin/bash
# kor.sh — en obevakad körning: bygger en sajt åt en riktig verksamhet enligt skillen bygg-sajt.
#
#   ./kor.sh <slug> "<verksamhetens namn, ort och gärna webbadress>"
#   ./kor.sh frisor-exempel-umea "Frisör Exempel, Umeå, https://exempel.se"
#
# Tre verksamheter över natten = tre rader i ett skript; de körs en i taget.
# Miljö (valfri): NWP_MODELL (opus[1m]), NWP_EFFORT (high), NWP_MAX_TURNS (400), NWP_STOPP_TAK (4).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:-}"
VERKSAMHET="${2:-}"
if [[ ! "$SLUG" =~ ^[a-z0-9-]{2,60}$ || -z "$VERKSAMHET" ]]; then
  sed -n '2,8p' "$0"
  exit 2
fi
[ -x "$ROOT/.venv/bin/python" ] || { echo "saknar .venv — se README.md, Installation"; exit 2; }
[ -d "$ROOT/kontroller/node_modules" ] || { echo "saknar kontroller/node_modules — kör: (cd kontroller && npm install)"; exit 2; }
command -v claude >/dev/null || { echo "claude saknas i PATH"; exit 2; }

mkdir -p "$ROOT/kunder/$SLUG" "$ROOT/underlag/$SLUG"
rm -f "$ROOT/kunder/$SLUG/prov/.stoppvakt-antal"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOGG="$ROOT/kunder/$SLUG/korning-$STAMP.jsonl"

PROMPT="Bygg en webbplats åt verksamheten: $VERKSAMHET
Slug: $SLUG

Följ skillen bygg-sajt (.claude/skills/bygg-sajt/SKILL.md) steg 1–7, i ordning. Underlag i underlag/$SLUG/, bygget i
kunder/$SLUG/sajt/, rapporten i kunder/$SLUG/RAPPORT.md. Ingen människa svarar under körningen: saknas en uppgift,
märk den antagande och fortsätt. Avsluta först när .venv/bin/python kontroller/prova.py $SLUG är grönt och rapporten
är skriven. Stoppvakten kör provet själv när du försöker avsluta."

ARGS=(-p
  --max-turns "${NWP_MAX_TURNS:-400}"
  --permission-mode dontAsk
  --output-format stream-json --verbose
  --allowedTools Read Write Edit Glob Grep WebFetch WebSearch Skill Task TaskCreate TaskUpdate TaskList TaskGet
  "Bash(npm *)" "Bash(npx *)" "Bash(node *)" "Bash(.venv/bin/python *)" "Bash(curl *)"
  "Bash(cd *)" "Bash(ls *)" "Bash(mkdir *)" "Bash(cp *)" "Bash(mv *)" "Bash(find *)"
  "Bash(file *)" "Bash(sips *)" "Bash(wc *)" "Bash(head *)" "Bash(tail *)" "Bash(cat *)" "Bash(grep *)"
  "Bash(sort *)" "Bash(uniq *)" "Bash(sed *)" "Bash(tr *)" "Bash(cut *)"
  "Bash(git add backlog/*)" "Bash(git commit *)" "Bash(git push origin main)"
  # Det som aldrig behövs i ett bygge nekas uttryckligen; nekande går före tillåtande. Commitvakten
  # (.claude/hooks/commitvakt.py, NWP_COMMIT_TILLATET nedan) släpper bara commits av backlog/.
  --disallowedTools "Bash(rm *)" "Bash(gh pr *)" "Bash(git rebase *)" "Bash(git checkout *)" "Bash(git reset *)"
  "Bash(git worktree *)" "Bash(git config *)" "Bash(git push --force *)" "Bash(git push -f *)")
# Bara projektets inställningar: då gäller --allowedTools som vitlista (ägarens egna allow-regler i
# ~/.claude/settings.json läses inte). Modell och effort anges därför uttryckligen; gh får sin konfigurationsmapp.
GH_DIR="$("$ROOT/.venv/bin/python" -c "import json,os; print((json.load(open(os.path.expanduser('~/.claude/settings.json'))).get('env') or {}).get('GH_CONFIG_DIR',''))" 2>/dev/null || true)"
# --strict-mcp-config utan --mcp-config: inga anslutningar (Gmail, Drive, Resend …) laddas i bygget.
ARGS+=(--setting-sources project,local --strict-mcp-config --model "${NWP_MODELL:-opus[1m]}" --effort "${NWP_EFFORT:-high}")
if [ -n "$GH_DIR" ]; then ARGS+=(--settings "{\"env\":{\"GH_CONFIG_DIR\":\"$GH_DIR\"}}"); fi

# Nästlad start (från en annan Claude Code-session) kräver att sessionens egna variabler tas bort.
RENSA=(-u CLAUDECODE)
while IFS='=' read -r namn _; do
  case "$namn" in CLAUDE_CODE_*) RENSA+=(-u "$namn");; esac
done < <(env)

cd "$ROOT"   # projektets Stop-krok laddas bara när sessionen startar i reporoten
echo "Körning $SLUG startad $STAMP. Logg: $LOGG"
set +e
printf '%s' "$PROMPT" | env "${RENSA[@]}" NWP_SLUG="$SLUG" NWP_COMMIT_TILLATET="backlog/" claude "${ARGS[@]}" > "$LOGG" 2>&1
RC=$?
set -e

"$ROOT/.venv/bin/python" - "$ROOT/kunder/$SLUG" "$RC" <<'PY'
import json, sys
from pathlib import Path
k, rc = Path(sys.argv[1]), sys.argv[2]
def las(p):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
s, v = las(k / 'prov' / 'STATUS.json'), las(k / 'prov' / 'STOPPVAKT.json')
print('\nclaude avslutade med kod', rc)
if s:
    print('Provet:', 'GRÖNT' if s.get('ok') else 'RÖTT', '—', ', '.join('%s %s' % (n, 'ok' if g['ok'] else 'RÖD') for n, g in s['grindar'].items()))
else:
    print('Provet: inget STATUS.json (provet kördes aldrig)')
if v:
    print('Stoppvakten:', v.get('skal'), '(försök %s av %s)' % (v.get('forsok'), v.get('tak')))
print('Rapport:', k / 'RAPPORT.md' if (k / 'RAPPORT.md').is_file() else 'saknas')
print('Titta:  cd %s && npx astro preview' % (k / 'sajt'))
PY
