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
# körning), NWP_MCP_CONFIG (av; kontroller/mcp/inspo.json, mobbin.json eller refero.json ansluter en referenstjänst i
# A/B-prövningen), NWP_ATELJE (av; pa = ateljén
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

# Referenstjänster via MCP (A/B-posterna om Inspo och om Refero/Mobbin): bara när NWP_MCP_CONFIG pekar på en av filerna i
# kontroller/mcp/ ansluts tjänsten, och bara dess läsande verktyg släpps igenom; annars laddas inga anslutningar alls.
# Alla tre är hostade ändpunkter (ingen lokal kod); inloggningen (OAuth) gör ägaren en gång i en interaktiv session.
INSPO=()
if [ -n "${NWP_MCP_CONFIG:-}" ] && [ "$NWP_MCP_CONFIG" != "av" ]; then
  [ -f "$NWP_MCP_CONFIG" ] || { echo "NWP_MCP_CONFIG pekar inte på en fil: $NWP_MCP_CONFIG"; exit 2; }
  # bara filerna i kontroller/mcp/ (den verkliga sökvägen, inte bara namnet), och bara tjänstens namngivna läsverktyg
  MCP_VERKLIG="$(cd "$(dirname "$NWP_MCP_CONFIG")" && pwd -P)/$(basename "$NWP_MCP_CONFIG")"
  case "$MCP_VERKLIG" in
    "$ROOT/kontroller/mcp/inspo.json")  INSPO=(mcp__inspo__recommend mcp__inspo__search_screens mcp__inspo__get_screen);;
    "$ROOT/kontroller/mcp/mobbin.json") INSPO=(mcp__mobbin__search_screens mcp__mobbin__search_flows mcp__mobbin__search_sections);;
    "$ROOT/kontroller/mcp/refero.json") INSPO=(mcp__refero__refero_search_styles mcp__refero__refero_get_style mcp__refero__refero_search_screens
                                               mcp__refero__refero_get_screen mcp__refero__refero_get_similar_screens mcp__refero__refero_get_screen_image
                                               mcp__refero__refero_search_flows mcp__refero__refero_get_flow)
      # Refero ansluts med en personlig nyckel (ingen webbläsarinloggning): anslutningsfilen bär ${REFERO_MCP_TOKEN},
      # värdet ligger i ägarens hemlighetsmapp och exporteras bara till byggets claude-process. Aldrig i repot.
      REFERO_ENV="$HOME/.nortropic-hemligheter/webb-pro/refero.env"
      [ -f "$REFERO_ENV" ] || { echo "Refero: $REFERO_ENV saknas (REFERO_MCP_TOKEN=…, chmod 600)"; exit 2; }
      set -a; . "$REFERO_ENV"; set +a
      [ -n "${REFERO_MCP_TOKEN:-}" ] || { echo "Refero: REFERO_MCP_TOKEN saknas i $REFERO_ENV"; exit 2; };;
    *) echo "NWP_MCP_CONFIG: okänd anslutning $MCP_VERKLIG; kända: $ROOT/kontroller/mcp/inspo.json, mobbin.json, refero.json"; exit 2;;
  esac
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
  # bara de verktyg ett bygge behöver (omgång sex, F1: prospekt.py gallra och andra administrativa verktyg nådde annat)
  "Bash(npx astro *)" "Bash(node kontroller/*)"
  "Bash(.venv/bin/python kontroller/prova.py *)" "Bash(.venv/bin/python kontroller/granska.py *)" "Bash(.venv/bin/python kontroller/atelje.py *)"
  "Bash(.venv/bin/python kontroller/ny_sajt.py *)" "Bash(.venv/bin/python kontroller/hamta_sajt.py *)" "Bash(.venv/bin/python kontroller/hamta_bokadirekt.py *)"
  "Bash(.venv/bin/python kontroller/sida_till_text.py *)" "Bash(.venv/bin/python kontroller/copy_kontroll.py *)" "Bash(.venv/bin/python kontroller/verksamhetsuppgifter.py *)"
  "Bash(.venv/bin/python kontroller/upptagna_val.py *)" "Bash(.venv/bin/python kontroller/ta_bort.py *)" "Bash(.venv/bin/python kontroller/backlog.py *)"
  "Bash(.venv/bin/python kontroller/rubriker.py *)" "Bash(.venv/bin/python kontroller/bilddatum.py *)" "Bash(.venv/bin/python kontroller/seo_kontroll.py *)"
  "Bash(.venv/bin/python kontroller/standard_kontroll.py *)" "Bash(.venv/bin/python kontroller/prelaunch.py *)" "Bash(.venv/bin/python kontroller/stegbevis.py *)"
  "Bash(.venv/bin/python underlag/$SLUG/skript/*)" "Bash(curl -sSL -o underlag/$SLUG/*)"
  "Bash(cd *)" "Bash(ls *)" "Bash(mkdir *)" "Bash(cp *)" "Bash(mv *)" "Bash(find *)"
  "Bash(file *)" "Bash(sips *)" "Bash(wc *)" "Bash(head *)" "Bash(tail *)" "Bash(cat *)" "Bash(grep *)"
  "Bash(sort *)" "Bash(uniq *)" "Bash(sed *)" "Bash(tr *)" "Bash(cut *)"
  # Ingen git i bygget: backlogposterna committas av körningen efteråt, utanför sandlådan (nedan). Commitvakten
  # (.claude/hooks/commitvakt.py, NWP_COMMIT_TILLATET nedan) står kvar som andra spärr om git ändå nås.
  # Det som aldrig behövs i ett bygge nekas uttryckligen; nekande går före tillåtande.
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
# Sandlådan (backlogposten om gräns på processnivå, F1): NWP_SANDLADA=pa ger claude Claude Codes inbyggda sandlåda för
# Bash och dess barn: skrivning bara i kunder/<slug>, underlag/<slug>, backlog/ och tmp; mekaniken och .git skrivskyddade;
# hemligheter olästa; nätet bara till verksamhetens domän (ur uppdragstexten), NWP_NAT_DOMANER (kommaseparerat) och
# kontroller/sandlada-domaner.txt. Prova först med kontroller/sandlada_prov.sh. Kräver att managed-settings.json inte
# låser sandbox.enabled till false (kontroller/sandlada.py). Standard av tills ett helt bygge körts med den på.
SANDLADA=()
if [ "${NWP_SANDLADA:-av}" = "pa" ]; then
  for d in $(printf '%s' "$VERKSAMHET" | tr 'A-Z' 'a-z' | grep -oE '[a-z0-9][a-z0-9.-]*\.[a-z]{2,}' | sort -u) $(printf '%s' "${NWP_NAT_DOMANER:-}" | tr ',' ' '); do
    SANDLADA+=(--doman "$d")
  done
else
  SANDLADA+=(--av)
fi
SETTINGS="$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/sandlada.py" "$SLUG" ${GH_DIR:+--gh-dir "$GH_DIR"} "${SANDLADA[@]}")" || { echo "inställningarna (kontroller/sandlada.py) kunde inte skapas"; exit 2; }
if [ "$SETTINGS" != "{}" ]; then ARGS+=(--settings "$SETTINGS"); fi

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
rm -f "$FORE_FIL" "$EFTER_FIL"   # en planterad symlänk ska inte få styra vart listorna skrivs
skyddat > "$FORE_FIL"
BACKLOG_FORE="$ROOT/kunder/$SLUG/prov/.backlog-fore"
git -C "$ROOT" ls-files --others --exclude-standard backlog | sort > "$BACKLOG_FORE"
echo "Körning $SLUG startad $STAMP. Logg: $LOGG"
set +e
printf '%s' "$PROMPT" | env "${RENSA[@]}" NWP_SLUG="$SLUG" NWP_KORNING="$STAMP" NWP_COMMIT_TILLATET="backlog/" claude "${ARGS[@]}" > "$LOGG" 2>&1
RC=$?
set -e
rm -f "$EFTER_FIL"
skyddat > "$EFTER_FIL"
# Bygget skriver backlogposter men har ingen git: körningen committar de nya filerna i backlog/ efteråt, bara dem
# (inte andra sessioners okommitterade poster), och pushar. Misslyckad push stoppar inte avslutet.
NYA_BACKLOG="$(comm -13 "$BACKLOG_FORE" <(git -C "$ROOT" ls-files --others --exclude-standard backlog | sort) | grep -E '^backlog/B-[a-z0-9-]+\.md$' || true)"
if [ -n "$NYA_BACKLOG" ]; then
  echo "$NYA_BACKLOG" | xargs git -C "$ROOT" add -- \
    && git -C "$ROOT" commit -q -m "Bygge $SLUG: backlogposter" -- $(echo "$NYA_BACKLOG") \
    && { git -C "$ROOT" push -q origin main || echo "backlogposterna committade lokalt; push misslyckades"; } \
    || echo "backlogposterna kunde inte committas: $NYA_BACKLOG"
fi
# Avslutet och slutkoden räknas av kontroller/korslut.py (revisionen 2026-10-03, F10 och F11): 0 godkänt, 1 avslutat utan
# godkännande, 3 mekaniken ändrades under körningen, 4 claude föll. exec: skriptets slutkod är korsluts.
exec "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" "$ROOT/kunder/$SLUG" "$RC" "$FORE_FIL" "$EFTER_FIL" "$STAMP"
