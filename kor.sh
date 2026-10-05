#!/bin/bash
# kor.sh — en obevakad körning: bygger en sajt åt en riktig verksamhet enligt skillen bygg-sajt.
#
#   ./kor.sh <slug> "<verksamhetens namn, ort och gärna webbadress>"
#   ./kor.sh frisor-exempel-umea "Frisör Exempel, Umeå, https://exempel.se"
# Slutkod: 0 grönt prov och godkänd granskning · 1 avslutat utan det · 2 fel i anropet (eller ett bygge pågår redan) ·
# 3 skyddade filer eller gränsen (nya kataloger direkt under kunder/ eller underlag/, lyft flagga) ändrades under
# körningen · 4 claude föll.
#
# Tre verksamheter över natten = tre rader i ett skript; de körs en i taget.
# Miljö (valfri): NWP_MODELL (opus[1m]), NWP_EFFORT (medium; vann ägarens blinda A/B 2026-10-02), NWP_MAX_TURNS (400), NWP_STOPP_TAK (8),
# NWP_GRANSKARE_MODELL (opus[1m]), NWP_GRANSKARE_ANTAL (2 parallella granskare per omgång), NWP_GRANSKNING_MAX (5 per
# körning), NWP_MCP_CONFIG (av; kontroller/mcp/inspo.json, mobbin.json eller refero.json ansluter en referenstjänst i
# A/B-prövningen), NWP_ATELJE (pa: skapandeflödet i steg 5.1, kontroller/atelje.py, med NWP_ATELJE_MODELL,
# NWP_ATELJE_EFFORT och NWP_ATELJE_ANTAL; av = nödvägen utan ateljé). En startsida som ägaren godkänt i dashboardens vy
# Prototyp (underlag/<slug>/atelje/VINNARE.json, fältet godkand) tas över utan ny ateljé; ett sandlådat bygge kräver
# en sådan (skapandeflödet körs utanför sandlådan, före bygget: kunskap/skapandeflodet.md).
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

# Ett bygge i taget, och inga nya kataloger direkt under kunder/ eller underlag/ medan det pågår (Codex 2026-10-04, F1:
# sandlådans skrivförbud räknas upp vid starten, så en katalog som skapades under körningen bredvid byggets vore
# skrivbar). Flaggan uchg på de två katalogerna stoppar varje process (bygget, dashboarden, en kampanj) från att skapa,
# döpa om eller ta bort poster där; byggets kommandolista släpper inte igenom chflags, och är flaggan ändå borta
# efteråt eller en post tillkommen räknar korslut det som ändrad mekanik (slutkod 3). Flaggorna tas bort vid avslut.
LAS="$ROOT/kunder/.bygge-pid"
mkdir -p "$ROOT/kunder" "$ROOT/underlag"
if [ -f "$LAS" ] && kill -0 "$(cat "$LAS" 2>/dev/null)" 2>/dev/null; then
  echo "ett bygge pågår redan (pid $(cat "$LAS")): ett i taget"; exit 2
fi
chflags nouchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || true   # kvarlämnad flagga efter en avbruten körning
echo $$ > "$LAS"
WT_PID=""
# städningen får aldrig ändra slutkoden (set -e gäller också i trapen): varje steg tål att misslyckas
trap 'chflags nouchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || true; rm -f "$LAS"; [ -z "${WT_PID:-}" ] || kill "$WT_PID" 2>/dev/null || true' EXIT
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
# Skapandeflödet (kunskap/skapandeflodet.md; Codex via ägaren 2026-10-05: ett designflöde, inte tre) är standard i
# steg 5.1. En startsida som ägaren godkänt tas över som ateljévinnaren; skapandeflödet körs utanför sandlådan, så ett
# sandlådat bygge kräver en godkänd startsida. NWP_ATELJE=av är nödvägen utan ateljé (byggarens eget KONCEPT.md).
# Godkännandet gäller bara när ägarens senaste dom i domloggen är just det och startsidan och DESIGN.md är oförändrade
# (kontroller/skapande.py godkand_giltig; granskningen av skapandeflödet, punkt 2).
GODKAND="$("$ROOT/.venv/bin/python" -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/kontroller")
import skapande
ok, skal = skapande.godkand_giltig(sys.argv[2])
print("ja" if ok else "")' "$ROOT" "$SLUG" 2>/dev/null || true)"
if [ -n "$GODKAND" ]; then
  PROMPT="$PROMPT

Ägaren har godkänt startsidan i skapandeflödet (underlag/$SLUG/atelje/VINNARE.json, fältet godkand): ta vid efter valet
i steg 5.1, som från ateljévinnaren. Kör inte ateljén; startsidan står i kunder/$SLUG/sajt/src/pages/index.astro."
elif [ "${NWP_ATELJE:-pa}" = "pa" ] && [ "${NWP_SANDLADA:-av}" = "pa" ]; then
  echo "skapandeflödet (ateljén) körs utanför sandlådan, före bygget: kör .venv/bin/python kontroller/prototyp.py $SLUG och godkänn startsidan i dashboardens vy Prototyp; NWP_ATELJE=av är nödvägen utan ateljé"; exit 2
elif [ "${NWP_ATELJE:-pa}" = "pa" ]; then
  PROMPT="$PROMPT

Riktningsateljén är på (skapandeflödet, standard): följ ateljévägen i steg 5.1."
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
  "Bash(.venv/bin/python kontroller/referens.py *)" "Bash(.venv/bin/python kontroller/referenstjanster.py *)"
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
  "Write(./.claude/**)" "Write(./LARDOMAR.md)"
  # ägarens domar över designen och godkännandet skrivs bara av ägaren (dashboarden), aldrig av bygget
  "Write(./underlag/$SLUG/DESIGNDOMAR.jsonl)" "Edit(./underlag/$SLUG/DESIGNDOMAR.jsonl)")
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
# låser sandbox.enabled till false (kontroller/sandlada.py). Webbläsarverktygen går via kontroller/webbtjanst.py utanför
# sandlådan (startas nedan). Standard av tills ett helt bygge körts med den på.
SANDLADA=()
if [ "${NWP_SANDLADA:-av}" = "pa" ]; then
  for d in $(printf '%s' "$VERKSAMHET" | tr 'A-Z' 'a-z' | grep -oE '[a-z0-9][a-z0-9.-]*\.[a-z]{2,}' | sort -u) $(printf '%s' "${NWP_NAT_DOMANER:-}" | tr ',' ' '); do
    SANDLADA+=(--doman "$d")
  done
else
  SANDLADA+=(--av)
fi
SETTINGS="$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/sandlada.py" "$SLUG" ${GH_DIR:+--gh-dir "$GH_DIR"} ${SANDLADA[@]+"${SANDLADA[@]}"})" || { echo "inställningarna (kontroller/sandlada.py) kunde inte skapas"; exit 2; }
if [ "$SETTINGS" != "{}" ]; then ARGS+=(--settings "$SETTINGS"); fi

# Nästlad start (från en annan Claude Code-session) kräver att sessionens egna variabler tas bort; bygget skriver
# aldrig i ägarens automatiska minne (CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 nedan, kontroller/nastlad.py).
RENSA=(-u CLAUDECODE)
while IFS='=' read -r namn _; do
  case "$namn" in CLAUDE_CODE_*) RENSA+=(-u "$namn");; esac
done < <(env)

cd "$ROOT"   # projektets Stop-krok laddas bara när sessionen startar i reporoten
# Bash når förbi Edit/Write-reglerna ovan (cp, mv, egna skript); därför jämförs de skyddade filernas innehåll före och
# efter, fil för fil, oavsett om en ändring committats under körningen (revisionen 2026-10-03, F10).
SKYDDAT=(kontroller kritik kunskap mall .claude dashboard kor.sh dashboard.sh CLAUDE.md BESLUT.md LARDOMAR.md .gitignore
         "underlag/$SLUG/DESIGNDOMAR.jsonl")  # ägarens domlogg: en ändring under bygget är ändrad mekanik (slutkod 3)
skyddat() {
  # en post som saknas (domloggen före ägarens första dom) får inte fälla skriptet; skapas den under bygget syns den efteråt
  { find "${SKYDDAT[@]}" -type f ! -path '*/node_modules/*' ! -path '*/__pycache__/*' ! -name '.DS_Store' -print0 2>/dev/null || true; } \
    | sort -z | xargs -0 shasum -a 256
}
# Gränsen i samma listformat (värde, två blanksteg, namn): flaggan på kunder/ och underlag/ och varje post direkt under
# dem; korslut räknar en skillnad här som ändrad mekanik (slutkod 3).
grans() {
  for d in kunder underlag; do
    printf '%s  flagga:%s\n' "$(stat -f %Sf "$ROOT/$d" 2>/dev/null | grep -o uchg || echo utan)" "$d"
    for n in "$ROOT/$d"/* "$ROOT/$d"/.[!.]*; do [ -e "$n" ] || [ -L "$n" ] || continue; printf 'post  syskon:%s/%s\n' "$d" "$(basename "$n")"; done
  done
}
mkdir -p "$ROOT/kunder/$SLUG/prov"
# Webbtjänsten (kontroller/webbtjanst.py): Chromium kan inte starta inne i sandlådan (mach-register nekas; mätt 2026-10-04),
# så med sandlådan på körs bara webbläsarskripten, lighthouse och granskarnas sessioner (med egen sandlåda) av en tjänst
# utanför sandlådan, bunden till sluggen, domänlistan och byggets kataloger; byggsteg (npm, servering) och byggets modell
# stannar i sandlådan. Verktygen delegerar själva när de körs sandlådade (NWP_WEBBTJANST).
WT_ENV=()
if [ "${NWP_SANDLADA:-av}" = "pa" ]; then
  # kvitto och logg utanför prov/, som provet rensar vid varje körning (helbygget 2026-10-04)
  WT_KVITTO="$ROOT/kunder/$SLUG/.webbtjanst-$STAMP"; rm -f "$WT_KVITTO"
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/webbtjanst.py" serve --slug "$SLUG" --kvitto "$WT_KVITTO" --korning "$STAMP" \
    ${SANDLADA[@]+"${SANDLADA[@]}"} > "$ROOT/kunder/$SLUG/webbtjanst-$STAMP.log" 2>&1 &
  WT_PID=$!
  for _ in $(seq 1 50); do [ -s "$WT_KVITTO" ] && break; sleep 0.2; done
  [ -s "$WT_KVITTO" ] || { echo "webbtjänsten startade inte (kunder/$SLUG/webbtjanst-$STAMP.log)"; exit 2; }
  WT_ENV=(NWP_WEBBTJANST="http://127.0.0.1:$(sed -n 1p "$WT_KVITTO")" NWP_WEBBTJANST_NYCKEL="$(sed -n 2p "$WT_KVITTO")")
fi
FORE_FIL="$ROOT/kunder/$SLUG/prov/.skyddat-fore"
EFTER_FIL="$ROOT/kunder/$SLUG/prov/.skyddat-efter"
rm -f "$FORE_FIL" "$EFTER_FIL"   # en planterad symlänk ska inte få styra vart listorna skrivs
# Misslyckad låsning stoppar bygget före modellstarten, och flaggorna verifieras uttryckligen (Codex R23: ett olåst
# tillstånd fick annars bli förebild, och slutkontrollen såg ingen skillnad).
chflags uchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || { echo "kunder/ och underlag/ kunde inte låsas mot nya kataloger (chflags uchg); bygget startas inte"; exit 2; }
for d in kunder underlag; do
  stat -f %Sf "$ROOT/$d" 2>/dev/null | grep -q uchg || { echo "$d/ är inte låst (flaggan uchg saknas efter chflags); bygget startas inte"; exit 2; }
done
{ skyddat; grans; } > "$FORE_FIL"
echo "Körning $SLUG startad $STAMP. Logg: $LOGG"
set +e
printf '%s' "$PROMPT" | env "${RENSA[@]}" CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 NWP_SLUG="$SLUG" NWP_KORNING="$STAMP" NWP_COMMIT_TILLATET="backlog/" NWP_SANDLADA="${NWP_SANDLADA:-av}" ${WT_ENV[@]+"${WT_ENV[@]}"} claude "${ARGS[@]}" > "$LOGG" 2>&1
RC=$?
set -e
rm -f "$EFTER_FIL"
{ skyddat; grans; } > "$EFTER_FIL"
chflags nouchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || true
# Avslutet och slutkoden räknas av kontroller/korslut.py (revisionen 2026-10-03, F10 och F11): 0 godkänt, 1 avslutat utan
# godkännande, 3 mekaniken ändrades under körningen, 4 claude föll, 6 ateljén förkastade alla riktningar och bygget
# stannade utan sajt (designprovet, ägarbeslut 2026-10-04). Skriptets slutkod är korsluts.
set +e
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" "$ROOT/kunder/$SLUG" "$RC" "$FORE_FIL" "$EFTER_FIL" "$STAMP"
KORSLUT=$?
# Bygget skriver backlogposter men har ingen git: efter korsluts bedömning publicerar kontroller/backlog_commit.py bara
# byggets egna poster (märkta med körningen), med commitvaktens kontroller, aldrig vid ändrad mekanik, och pushar bara en
# utgående historik som enbart rör backlog/ (Codex 2026-10-04, F27 och F3). Misslyckad publicering ändrar inte slutkoden.
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/backlog_commit.py" "$SLUG" "$STAMP" "$KORSLUT"
exit $KORSLUT
