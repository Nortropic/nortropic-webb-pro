#!/bin/bash
# kor.sh — en obevakad körning: bygger en sajt åt en riktig verksamhet enligt skillen bygg-sajt.
#
#   ./kor.sh <slug> "<verksamhetens namn, ort och gärna webbadress>"
#   ./kor.sh frisor-exempel-umea "Frisör Exempel, Umeå, https://exempel.se"
# Slutkod: 0 grönt prov och godkänd granskning · 1 avslutat utan det · 2 fel i anropet · 3 skyddade filer ändrades under
# körningen · 4 claude föll.
#
# Tre verksamheter över natten = tre rader i ett skript; de körs en i taget.
# Miljö (valfri): NWP_MODELL (opus[1m]), NWP_EFFORT (medium; vann ägarens blinda A/B 2026-10-02), NWP_MAX_TURNS (400), NWP_STOPP_TAK (8),
# NWP_GRANSKARE_MODELL (opus[1m]), NWP_GRANSKARE_ANTAL (2 parallella granskare per omgång), NWP_GRANSKNING_MAX (5 per
# körning), NWP_MCP_CONFIG (av; kontroller/mcp/inspo.json ansluter Inspo i A/B-prövningen), NWP_ATELJE (av; pa = ateljén
# i steg 5.1, med NWP_ATELJE_MODELL, NWP_ATELJE_EFFORT och NWP_ATELJE_ANTAL).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:-}"
VERKSAMHET="${2:-}"
if [[ ! "$SLUG" =~ ^[a-z0-9-]{2,60}$ || -z "$VERKSAMHET" ]]; then
  sed -n '2,11p' "$0"
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
märk den antagande och fortsätt. Avsluta först när .venv/bin/python kontroller/prova.py $SLUG är grönt, rapporten är
skriven och den oberoende granskaren (kontroller/granska.py) har godkänt sajten. Stoppvakten kör provet och
granskningen själv när du försöker avsluta."
# Riktningsateljén (A/B-posten B-20261003-a-b-riktningsatelje-i-steg-5-1-dar-en-orkestrato): av som standard.
if [ "${NWP_ATELJE:-av}" = "pa" ]; then
  PROMPT="$PROMPT

Riktningsateljén är på (NWP_ATELJE=pa): följ ateljévägen i steg 5.1."
fi

# Inspo (A/B-posten B-20261002-a-b-inspo-mcp-hostad-andpunkt-som-sokingang-for): bara när NWP_MCP_CONFIG pekar på en
# fil ansluts den, och bara tre läsande verktyg släpps igenom; annars laddas inga anslutningar alls.
INSPO=()
if [ -n "${NWP_MCP_CONFIG:-}" ] && [ "$NWP_MCP_CONFIG" != "av" ]; then
  [ -f "$NWP_MCP_CONFIG" ] || { echo "NWP_MCP_CONFIG pekar inte på en fil: $NWP_MCP_CONFIG"; exit 2; }
  INSPO=(mcp__inspo__recommend mcp__inspo__search_screens mcp__inspo__get_screen)
fi

ARGS=(-p
  --max-turns "${NWP_MAX_TURNS:-400}"
  --permission-mode dontAsk
  --output-format stream-json --verbose
  --allowedTools Read Write Edit Glob Grep WebFetch WebSearch Skill Task TaskCreate TaskUpdate TaskList TaskGet
  ${INSPO[@]+"${INSPO[@]}"}
  # npm bara mot byggets egen sajt: målarbygget 2026-10-01 installerade först ett typsnitt i repots rot.
  "Bash(npm install --prefix kunder/$SLUG/*)" "Bash(npm ci --prefix kunder/$SLUG/*)" "Bash(npm run build --prefix kunder/$SLUG/*)"
  "Bash(npm --prefix kunder/$SLUG/*)" "Bash(npm view *)" "Bash(npm ls *)" "Bash(npm pack *)"
  # Tolkar och hämtare bara i de former skillen använder och bara mot det egna bygget (revisionen 2026-10-03, F1):
  # verktygen i kontroller/, egna skript under underlag/<slug>/skript/, npx bara för astro, curl bara för att spara en fil
  # under underlag/<slug>/. Ett egenskrivet skript når ändå förbi Edit- och Write-reglerna; gränsen på processnivå
  # (sandlådan) är ett eget steg i backloggen.
  "Bash(npx astro *)" "Bash(node kontroller/*)" "Bash(.venv/bin/python kontroller/*)" "Bash(.venv/bin/python -B kontroller/*)"
  "Bash(.venv/bin/python underlag/$SLUG/skript/*)" "Bash(curl -sSL -o underlag/$SLUG/*)"
  "Bash(cd *)" "Bash(ls *)" "Bash(mkdir *)" "Bash(cp *)" "Bash(mv *)" "Bash(find *)"
  "Bash(file *)" "Bash(sips *)" "Bash(wc *)" "Bash(head *)" "Bash(tail *)" "Bash(cat *)" "Bash(grep *)"
  "Bash(sort *)" "Bash(uniq *)" "Bash(sed *)" "Bash(tr *)" "Bash(cut *)"
  "Bash(git add backlog/*)" "Bash(git commit *)" "Bash(git push origin main)"
  # Det som aldrig behövs i ett bygge nekas uttryckligen; nekande går före tillåtande. Commitvakten
  # (.claude/hooks/commitvakt.py, NWP_COMMIT_TILLATET nedan) släpper bara commits av backlog/.
  --disallowedTools "Bash(rm *)" "Bash(gh pr *)" "Bash(git rebase *)" "Bash(git checkout *)" "Bash(git reset *)"
  "Bash(git worktree *)" "Bash(git config *)" "Bash(git push --force *)" "Bash(git push -f *)"
  "Bash(sed -i*)" "Bash(find * -exec*)" "Bash(find * -ok*)" "Bash(find * -delete*)" "Bash(npx astro add *)"
  # Bygget får inte ändra sina egna acceptansvillkor: provet, granskarens kriterier, kunskapen, mallen, krokarna
  # och ägarens domar. Sökvägarna är relativa till reporoten, där sessionen startar (cd nedan).
  "Edit(./kontroller/**)" "Edit(./kritik/**)" "Edit(./kunskap/**)" "Edit(./mall/**)" "Edit(./.claude/**)"
  "Edit(./LARDOMAR.md)" "Write(./kontroller/**)" "Write(./kritik/**)" "Write(./kunskap/**)" "Write(./mall/**)"
  "Write(./.claude/**)" "Write(./LARDOMAR.md)")
# Bara projektets inställningar: då gäller --allowedTools som vitlista (ägarens egna allow-regler i
# ~/.claude/settings.json läses inte). Modell och effort anges därför uttryckligen; gh får sin konfigurationsmapp.
GH_DIR="$("$ROOT/.venv/bin/python" -c "import json,os; print((json.load(open(os.path.expanduser('~/.claude/settings.json'))).get('env') or {}).get('GH_CONFIG_DIR',''))" 2>/dev/null || true)"
# --strict-mcp-config utan --mcp-config: inga anslutningar (Gmail, Drive, Resend …) laddas i bygget.
ARGS+=(--setting-sources project,local --strict-mcp-config --model "${NWP_MODELL:-opus[1m]}" --effort "${NWP_EFFORT:-medium}")
if [ ${#INSPO[@]} -gt 0 ]; then ARGS+=(--mcp-config "$NWP_MCP_CONFIG"); fi
if [ -n "$GH_DIR" ]; then ARGS+=(--settings "{\"env\":{\"GH_CONFIG_DIR\":\"$GH_DIR\"}}"); fi

# Nästlad start (från en annan Claude Code-session) kräver att sessionens egna variabler tas bort.
RENSA=(-u CLAUDECODE)
while IFS='=' read -r namn _; do
  case "$namn" in CLAUDE_CODE_*) RENSA+=(-u "$namn");; esac
done < <(env)

cd "$ROOT"   # projektets Stop-krok laddas bara när sessionen startar i reporoten
# Bash når förbi Edit/Write-reglerna ovan (cp, mv, egna skript); därför jämförs de skyddade filernas innehåll före och
# efter, fil för fil, oavsett om en ändring committats under körningen (revisionen 2026-10-03, F10).
SKYDDAT=(kontroller kritik kunskap mall .claude dashboard kor.sh dashboard.sh CLAUDE.md BESLUT.md LARDOMAR.md .gitignore)
skyddat() {
  find "${SKYDDAT[@]}" -type f ! -path '*/node_modules/*' ! -path '*/__pycache__/*' ! -name '.DS_Store' -print0 2>/dev/null \
    | sort -z | xargs -0 shasum -a 256
}
mkdir -p "$ROOT/kunder/$SLUG/prov"
FORE_FIL="$ROOT/kunder/$SLUG/prov/.skyddat-fore"
EFTER_FIL="$ROOT/kunder/$SLUG/prov/.skyddat-efter"
skyddat > "$FORE_FIL"
echo "Körning $SLUG startad $STAMP. Logg: $LOGG"
set +e
printf '%s' "$PROMPT" | env "${RENSA[@]}" NWP_SLUG="$SLUG" NWP_KORNING="$STAMP" NWP_COMMIT_TILLATET="backlog/" claude "${ARGS[@]}" > "$LOGG" 2>&1
RC=$?
set -e
skyddat > "$EFTER_FIL"
# Avslutet och slutkoden räknas av kontroller/korslut.py (revisionen 2026-10-03, F10 och F11): 0 godkänt, 1 avslutat utan
# godkännande, 3 mekaniken ändrades under körningen, 4 claude föll. exec: skriptets slutkod är korsluts.
exec "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" "$ROOT/kunder/$SLUG" "$RC" "$FORE_FIL" "$EFTER_FIL"
