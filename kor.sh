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
  "Bash(npm install --prefix kunder/*)" "Bash(npm ci --prefix kunder/*)" "Bash(npm run build --prefix kunder/*)"
  "Bash(npm --prefix kunder/*)" "Bash(npm view *)" "Bash(npm ls *)" "Bash(npm pack *)"
  # Tolkar och hämtare bara i de former skillen använder (revisionen 2026-10-03, F1): verktygen i kontroller/, byggets
  # egna skript under underlag/<slug>/skript/, npx bara för astro, curl bara för att spara en fil under underlag/.
  # Ett generellt python, node eller curl når förbi varje Edit- och Write-regel; gränsen på processnivå är ett eget steg.
  "Bash(npx astro *)" "Bash(node kontroller/*)" "Bash(.venv/bin/python kontroller/*)" "Bash(.venv/bin/python -B kontroller/*)"
  "Bash(.venv/bin/python underlag/*)" "Bash(curl -sSL -o underlag/*)"
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
FORE="$(skyddat)"
echo "Körning $SLUG startad $STAMP. Logg: $LOGG"
set +e
printf '%s' "$PROMPT" | env "${RENSA[@]}" NWP_SLUG="$SLUG" NWP_KORNING="$STAMP" NWP_COMMIT_TILLATET="backlog/" claude "${ARGS[@]}" > "$LOGG" 2>&1
RC=$?
set -e
EFTER="$(skyddat)"
if [ "$EFTER" != "$FORE" ]; then
  # filerna vars hash eller närvaro skiljer sig; (committad eller inte spelar ingen roll, innehållet räknas)
  SKYDD="$(diff <(printf '%s\n' "$FORE") <(printf '%s\n' "$EFTER") | grep '^[<>]' | awk '{print $NF}' | sort -u | head -40)"
  SKYDD="${SKYDD:-(innehållet ändrades under körningen)}"
else
  SKYDD=""
fi

# Slutkod (revisionen 2026-10-03, F11): 0 provet grönt och granskningen godkänd · 1 avslutat utan det (rött, saknad
# rapport, underkänd eller tak) · 3 skyddade filer ändrades · 4 claude föll (kod ≠ 0) · 2 fel i anropet (ovan).
"$ROOT/.venv/bin/python" - "$ROOT/kunder/$SLUG" "$RC" "$SKYDD" <<'PY'
import json, sys
from pathlib import Path
k, rc, skydd = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
def las(p):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
s, v, g = las(k / 'prov' / 'STATUS.json'), las(k / 'prov' / 'STOPPVAKT.json'), las(k / 'granskning' / 'GRANSKNING.json')
print('\nclaude avslutade med kod', rc)
# Mekaniken (provet, kriterierna, mallen, krokarna, kor.sh, dashboarden) får aldrig ändras under en körning: slutkod 3.
# Texterna (kunskap/, LARDOMAR.md, skills) skrivs också av kirurgens intag och ägarens domar i dashboarden: bara varning.
MEKANIK = ('kontroller/', 'kritik/', 'mall/', '.claude/hooks/', '.claude/settings', 'kor.sh', 'dashboard/', 'dashboard.sh',
           'CLAUDE.md', 'BESLUT.md', '.gitignore')
mekanik = [f for f in skydd.splitlines() if f.startswith(MEKANIK)]
if skydd:
    print('VARNING: skyddade filer ändrades under körningen, av bygget eller någon annan (kirurgen, ägarens dom):\n' + skydd)
if s:
    print('Provet:', 'GRÖNT' if s.get('ok') else 'RÖTT', '—', ', '.join('%s %s' % (n, 'ok' if g['ok'] else 'RÖD') for n, g in s['grindar'].items()))
else:
    print('Provet: inget STATUS.json (provet kördes aldrig)')
if v:
    print('Stoppvakten:', v.get('skal'), '(försök %s av %s)' % (v.get('forsok'), v.get('tak')))
if g:
    print('Granskningen:', 'GODKÄND' if g.get('godkand') else 'UNDERKÄND', '(omgång %s)' % g.get('runda'), '—',
          ', '.join('%s %s' % (n, x.get('betyg')) for n, x in (g.get('kriterier') or {}).items()))
else:
    print('Granskningen: ingen')
print('Rapport:', k / 'RAPPORT.md' if (k / 'RAPPORT.md').is_file() else 'saknas')
print('Titta:  cd %s && npx astro preview' % (k / 'sajt'))
godkant = bool(s and s.get('ok')) and (k / 'RAPPORT.md').is_file() and bool(g and g.get('godkand'))
if mekanik:
    print('Slutkod 3: mekaniken ändrades under körningen:', ', '.join(mekanik))
    sys.exit(3)
if rc != '0':
    print('Slutkod 4: claude avslutade med kod', rc)
    sys.exit(4)
print('Slutkod', 0 if godkant else 1, ':', 'godkänt bygge' if godkant else 'avslutat utan grönt prov och godkänd granskning')
sys.exit(0 if godkant else 1)
PY
