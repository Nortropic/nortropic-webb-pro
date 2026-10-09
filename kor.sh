#!/bin/bash
# kor.sh — helbygget: en obevakad körning som bygger sajten åt en riktig verksamhet enligt skillen bygg-sajt, från den
# startsida som ägaren godkänt i skapandeflödet (dashboardens vy Prototyp; underlag/<slug>/atelje/VINNARE.json, fältet
# godkand). Utan en godkänd startsida, eller när ägarens senaste dom inte tillåter ett bygge, stannar kor.sh före bygget
# med slutkod 2 och pekar på kontroller/prototyp.py. Hela kedjan från kundunderlag till leverans, med vem som startar
# vad: README.md.
#
#   ./kor.sh <slug> "<verksamhetens namn, ort och gärna webbadress>"
#   ./kor.sh frisor-exempel-umea "Frisör Exempel, Umeå, https://exempel.se"
# Slutkod: 0 grönt prov och godkänd granskning · 1 avslutat utan det · 2 fel i anropet, ingen godkänd startsida,
# startkontrollen stoppade, ett bygge pågår redan, eller kor.sh föll före bygget · 3 skyddade filer, kor.sh:s hashlistor
# eller gränsen (nya kataloger direkt under kunder/ eller underlag/, lyft flagga) eller ägarens dom (DOM.json) ändrades
# under körningen · 4 claude föll, också när körningen avbröts (SIGTERM, SIGINT eller SIGHUP till kor.sh eller dess
# grupp; SIGKILL mot kor.sh, då vakten skriver posten) · 5 slutposten uteblev · 6 bygget stannade utan sajt (den äldre
# utforskningens lägen: ateljén förkastade alla riktningar, skaparen lämnade grundidén, eller ägaren dömde startsidan).
# Flera helbyggen körs ett i taget. Varje start efter låset ger en slutpost: kunder/<slug>/korningar/<körning>/SLUT.json
# (korslut.py), också när ett kommando faller under set -e eller en trasig fil läses in. Undantagen: när kunder/<slug>
# eller korningar/ inte går att använda (en fil eller en symlänk) skrivs bara beskedet, och när både kor.sh och vakten
# dödas (SIGKILL mot båda, en omstart) säger nästa start och korslut.py --visa att körningen avbröts utan slutpost.
# Miljö (valfri): NWP_MODELL (opus[1m]), NWP_EFFORT (medium; vann ägarens blinda A/B 2026-10-02), NWP_MAX_TURNS (400),
# NWP_STOPP_TAK (8), NWP_GRANSKARE_MODELL (opus[1m]), NWP_GRANSKARE_ANTAL (2 parallella granskare per omgång),
# NWP_GRANSKNING_MAX (5 per körning), NWP_FRIST (10: sekunder från SIGTERM till SIGKILL när bygget stoppas),
# NWP_MCP_CONFIG (av; kontroller/mcp/inspo.json, mobbin.json eller refero.json ansluter en referenstjänst i
# A/B-prövningen), NWP_ATELJE (pa; av = nödvägen utan godkänd startsida, där byggaren skriver KONCEPT.md och DESIGN.md
# själv), NWP_SANDLADA (av; pa kräver en godkänd startsida, eftersom skapandeflödet körs utanför sandlådan, före bygget:
# kunskap/skapandeflodet.md).
#
# Skyddet av ägarens dom och byggets processer (granskningen GR-20261007-r101-om, BÖR 1 och 2):
# - Vakten (kontroller/korvakt.py) startar när körningen fått sin identitet och lever i en egen session. Den följer
#   varje process som kor.sh och bygget startar, också en som lämnat sin session och bytt förälder, och stoppar byggets
#   processer innan något jämförs eller låsen släpps: SIGTERM, och SIGKILL efter NWP_FRIST. claude startas i en egen
#   processgrupp, och en signal under bygget går till hela gruppen. Dör kor.sh utan avslut gör vakten avslutet.
# - kor.sh håller hashlistornas sha256 och sha256 för DOM.json när den låstes i minnet och ger dem till korslut: en
#   ändrad hashlista är slutkod 3, och ägarens dom prövas mot DOM.json som den var när den låstes.
# - bash läser hela blocket nedan innan något körs: en ändring av kor.sh under ett bygge påverkar inte körningen.
# - Gränsen: ett eget skript i bygget som ändrar kontrollerna (kor.sh, korslut.py, korvakt.py eller Python-miljön; utan
#   sandlådan är de skrivbara) eller dödar vakten, och en process som startas via launchd eller hinner byta förälder två
#   gånger innan vakten sett den mellersta, når förbi skyddet. Gränsen på processnivå är ett eget steg i backloggen.
{
set -Eeuo pipefail   # -E: fällan för ERR gäller också i funktionerna
ROOT="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:-}"
VERKSAMHET="${2:-}"
START_ID="${NWP_FLODE_START_ID:-}"
[[ -z "$START_ID" || "$START_ID" =~ ^[A-Za-z0-9_-]{8,80}$ ]] || { echo "ogiltigt start-id"; exit 2; }
if [[ ! "$SLUG" =~ ^[a-z0-9-]{2,60}$ || -z "$VERKSAMHET" ]]; then
  sed -n '2,26p' "$0"
  exit 2
fi
[ -x "$ROOT/.venv/bin/python" ] || { echo "saknar .venv — se README.md, Installation"; exit 2; }
[ -d "$ROOT/kontroller/node_modules" ] || { echo "saknar kontroller/node_modules — kör: (cd kontroller && npm install)"; exit 2; }
command -v claude >/dev/null || { echo "claude saknas i PATH"; exit 2; }
if { [ -e "$ROOT/underlag/kundstart" ] || [ -L "$ROOT/underlag/kundstart" ]; } && [ "${NWP_SANDLADA:-av}" != pa ]; then
  echo "Kundstarts ärendelager kräver sandlådan: använd NWP_SANDLADA=pa. Inget bygge startat."
  exit 2
fi
FRIST="${NWP_FRIST:-10}"
[[ "$FRIST" =~ ^[0-9]{1,4}$ ]] || { echo "NWP_FRIST ska vara ett antal sekunder"; exit 2; }

# Ett bygge i taget, och inga nya kataloger direkt under kunder/ eller underlag/ medan det pågår (Codex 2026-10-04, F1:
# sandlådans skrivförbud räknas upp vid starten, så en katalog som skapades under körningen bredvid byggets vore
# skrivbar). Flaggan uchg på de två katalogerna stoppar varje process (bygget, dashboarden, en kampanj) från att skapa,
# döpa om eller ta bort poster där; byggets kommandolista släpper inte igenom chflags, och är flaggan ändå borta
# efteråt eller en post tillkommen räknar korslut det som ändrad mekanik (slutkod 3). Flaggorna tas bort vid avslut.
LAS="$ROOT/kunder/.bygge-pid"
mkdir -p "$ROOT/kunder" "$ROOT/underlag"
# Atomisk reservation före PID-filen och all ändring. Samma process exec:as, så körningens pid består.
# Vakten ärver fd 9 och håller låset genom återställningen även när kor.sh dödas.
if ! "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/bygglas.py" --har-las "$ROOT"; then
  exec "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/bygglas.py" "$ROOT" "$SLUG" "$VERKSAMHET"
fi
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/bygglas.py" --har-kund-las "$ROOT" "$SLUG" || { echo "kundens ärvda startlås saknas"; exit 2; }
if "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/bygglas.py" --aldre "$ROOT"; then
  exit 2
fi
chflags nouchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || true   # kvarlämnad flagga efter en avbruten körning
echo $$ > "$LAS"
# körregistret (kontroller/korregister.py): underhållet på maskinen byter inget i den delade miljön medan bygget pågår
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korregister.py" in bygge --slug "$SLUG" --pid $$ >/dev/null 2>&1 || true
WT_PID=""; STAMP=""; FAS=fore; CLAUDE_PID=""; AVBRUTEN=""; AVBROTT_TID=""; VAKT=""; STOPPAT=""; STOPPAD=""; FEL_KOD=""; FEL_KMD=""
# Ett kommando som faller under set -e ger också en post (GR-20261007-r101-om2#KAN-5): fällan sparar kommandot och dess kod
# (radnumret i blocket nedan är blockets sista rad i bash 3.2, så det sparas inte).
trap 'FEL_KOD=$?; FEL_KMD=$BASH_COMMAND' ERR
vakt_skriv() {  # en rad till vakten (kontroller/korvakt.py); en vakt som inte lever stoppar aldrig kor.sh
  [ -z "$VAKT" ] || printf '%s\n' "$1" >&3 2>/dev/null || true
}
vakt_fraga() {  # en rad till vakten och dess svar (en rad), eller tomt när vakten inte svarar
  local svar=""
  { [ -n "$VAKT" ] && kill -0 "$VAKT" 2>/dev/null; } || return 0
  printf '%s\n' "$1" >&3 2>/dev/null || return 0
  IFS= read -r -t "$((FRIST + 120))" svar <&4 || svar=""
  printf '%s' "$svar"
}
# Avslutet vid varje utgång efter låset. Städningen får aldrig ändra slutkoden (set -e gäller också här): varje steg tål
# att misslyckas. Slutade kor.sh före bygget utan att stanna med en post (ett kommando föll under set -e, eller en trasig
# fil lästes in) skrivs en kort post med kommandot, och slutkoden blir 2. Byggets processer stoppas av vakten innan låsen
# släpps.
stada() {
  local kod=$?
  trap '' TERM INT HUP
  if [ -n "$STAMP" ] && [ "$FAS" = fore ] && [ -z "$STOPPAD" ] && [ -f "$ROOT/kunder/$SLUG/korningar/$STAMP/START.json" ] \
     && [ ! -e "$ROOT/kunder/$SLUG/korningar/$STAMP/SLUT.json" ]; then
    local skal="kor.sh avslutades före bygget utan att stanna med en post (kod $kod)"
    [ -z "$FEL_KMD" ] || skal="kor.sh föll före bygget: $FEL_KMD (kod $FEL_KOD)"
    NWP_VERKSAMHET="$VERKSAMHET" "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" --stopp "$ROOT/kunder/$SLUG" "$STAMP" "$skal" \
      2>/dev/null || true
    kod=2
  fi
  [ -n "$STOPPAT" ] || vakt_fraga "slut ${RC:-okänd}" >/dev/null || true
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korregister.py" ut --pid $$ >/dev/null 2>&1 || true
  chflags nouchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || true
  [ -z "${DOMLOGG:-}" ] || chflags nouchg "$DOMLOGG" 2>/dev/null || true
  [ -z "${DOMBELAGG:-}" ] || chflags nouchg "$DOMBELAGG" 2>/dev/null || true
  [ -z "${DOMFIL:-}" ] || chflags nouchg "$DOMFIL" 2>/dev/null || true
  rm -f "$LAS"
  [ -z "${WT_PID:-}" ] || kill "$WT_PID" 2>/dev/null || true
  vakt_skriv klar
  exit "$kod"
}
trap stada EXIT
mkdir -p "$ROOT/kunder/$SLUG" "$ROOT/underlag/$SLUG"
# Körningens identitet (NWP_KORNING), unik för kunden, sätts direkt efter låset: varje start, också en som stannar före
# bygget, får en slutpost i kunder/<slug>/korningar/<körning>/SLUT.json, och terminalens besked skrivs ur posten
# (kontroller/korslut.py; ägarens uppdrag 2026-10-07, punkt 4). En start som nekas före låset (fel i anropet, verktyg
# som saknas, ett bygge pågår redan) skriver ingen post: skrivningen kunde ändra det pågående byggets gräns.
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
while [ -e "$ROOT/kunder/$SLUG/korningar/$STAMP" ] || [ -L "$ROOT/kunder/$SLUG/korningar/$STAMP" ]; do
  sleep 1; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
done
[ -L "$ROOT/kunder/$SLUG/korningar" ] && { echo "kunder/$SLUG/korningar är en symlänk; bygget startas inte"; exit 2; }
stopp() {  # kor.sh stannar före bygget: en kort slutpost och beskedet ur den, slutkod 2
  STOPPAD=1
  NWP_VERKSAMHET="$VERKSAMHET" "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" --stopp "$ROOT/kunder/$SLUG" "$STAMP" "$1" || echo "$1"
  exit 2
}
DOMFIL="$ROOT/kunder/$SLUG/DOM.json"
DOMLOGG="$ROOT/underlag/$SLUG/DESIGNDOMAR.jsonl"
DOMBELAGG="$ROOT/underlag/$SLUG/DESIGNDOMAR-belagg.jsonl"
FORE_FIL="$ROOT/kunder/$SLUG/prov/.skyddat-fore"
EFTER_FIL="$ROOT/kunder/$SLUG/prov/.skyddat-efter"
# Bash når förbi Edit/Write-reglerna nedan (cp, mv, egna skript); därför jämförs de skyddade filernas innehåll före och
# efter, fil för fil, oavsett om en ändring committats under körningen (revisionen 2026-10-03, F10). Funktionerna står
# här, före vakten, som får dem ur kor.sh:s minne och räknar listan efter körningen med dem om kor.sh dör.
SKYDDAT=(kontroller kritik kunskap mall .claude dashboard kor.sh dashboard.sh CLAUDE.md BESLUT.md LARDOMAR.md .gitignore
         "underlag/$SLUG/DESIGNDOMAR.jsonl" "underlag/$SLUG/DESIGNDOMAR-belagg.jsonl" "kunder/$SLUG/DOM.json"
         "kunder/$SLUG/korningar" "kunder/$SLUG/rapporter" "kunder/$SLUG/atelje/korningar")
skyddat() {
  # en post som saknas får inte fälla skriptet; försvinner eller tillkommer den under bygget syns det efteråt
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
  # protokollens kataloger och länkar, som find -type f ovan inte ser: en katalog eller symlänk där en slutpost ska
  # ligga ändrar gränsen (granskningen av r101, BÖR 2)
  for p in "kunder/$SLUG/korningar" "kunder/$SLUG/rapporter" "kunder/$SLUG/atelje/korningar"; do
    { [ -e "$p" ] || [ -L "$p" ]; } || continue
    find "$p" \( -type d -o -type l \) -print 2>/dev/null | sort | while IFS= read -r x; do
      if [ -L "$x" ]; then printf 'lank  protokoll:%s\n' "$x"; else printf 'katalog  protokoll:%s\n' "$x"; fi
    done
  done
  # find -type f ser varken en länk eller en tom katalog i en skyddad fils ställe.
  for p in "underlag/$SLUG/DESIGNDOMAR.jsonl" "underlag/$SLUG/DESIGNDOMAR-belagg.jsonl" "kunder/$SLUG/DOM.json"; do
    if [ -L "$p" ]; then typ=lank
    elif [ -f "$p" ]; then typ=fil
    elif [ -d "$p" ]; then typ=katalog
    elif [ -e "$p" ]; then typ=annan
    else typ=saknas
    fi
    printf '%s  protokoll:%s\n' "$typ" "$p"
  done
}
# Körningen syns från början (granskningen av r101, BÖR 1): korningar/<körning>/START.json med pid, starttid och
# DOM.json:s sha256. En körning som dödas utan slutpost känns igen av nästa start och av korslut.py --visa.
DOMSHA=null
if [ -f "$DOMFIL" ] && [ ! -L "$DOMFIL" ]; then DOMSHA="\"$(shasum -a 256 "$DOMFIL" | cut -d' ' -f1)\""; fi
mkdir -p "$ROOT/kunder/$SLUG/korningar/$STAMP" \
  && printf '{"korning": "%s", "pid": %d, "start": "%s", "dom_sha256": %s, "start_id": "%s"}\n' "$STAMP" $$ "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$DOMSHA" "$START_ID" \
     > "$ROOT/kunder/$SLUG/korningar/$STAMP/START.json" \
  || stopp "körningens katalog kunder/$SLUG/korningar/$STAMP kunde inte skapas; bygget startas inte"
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" --avbrutna "$ROOT/kunder/$SLUG" "$STAMP" || true
# Vakten (kontroller/korvakt.py; granskningen GR-20261007-r101-om, BÖR 1, BÖR 2, KAN 2 och KAN 5) startar nu, före allt som
# låser eller startar något. Den får kor.sh:s funktioner för hashlistan ur minnet. Rören (fd 3 till vakten, fd 4 från den)
# skapas i körningens katalog och tas bort så fort båda ändarna är öppna; kor.sh öppnar dem läs- och skrivbara, så att
# ingen öppning väntar på en vakt som inte startade. Byggets processer får inte rören.
VK="$ROOT/kunder/$SLUG/korningar/$STAMP/.vakt"
mkfifo -m 600 "$VK-in" "$VK-ut" || stopp "vaktens rör kunde inte skapas i kunder/$SLUG/korningar/$STAMP/; bygget startas inte"
NWP_VERKSAMHET="$VERKSAMHET" NWP_FRIST="$FRIST" NWP_VAKT_SKYDDAT="$(declare -p SKYDDAT; declare -f skyddat grans)" \
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korvakt.py" --kor-pid $$ --root "$ROOT" --kund "$ROOT/kunder/$SLUG" --korning "$STAMP" \
  --las "$LAS" --domlogg "$DOMLOGG" --domfil "$DOMFIL" --fore "$FORE_FIL" --efter "$EFTER_FIL" \
  < "$VK-in" > "$VK-ut" 2>> "$ROOT/kunder/$SLUG/korvakt-$STAMP.log" &
exec 3<> "$VK-in" 4<> "$VK-ut"
VAKT_SVAR=""; IFS= read -r -t 30 VAKT_SVAR <&4 || VAKT_SVAR=""
rm -f "$VK-in" "$VK-ut"
case "$VAKT_SVAR" in
  redo\ *) VAKT="${VAKT_SVAR#redo }";;
  *) stopp "vakten (kontroller/korvakt.py) startade inte (logg: kunder/$SLUG/korvakt-$STAMP.log); bygget startas inte";;
esac
# En signal före bygget ger en kort post. Under bygget går SIGTERM till claudes hela processgrupp, vakten stoppar resten
# av byggets processer, och claude får SIGKILL efter NWP_FRIST sekunder; korslut skriver posten med slutkoden. Under
# avslutet ignoreras signalen, så att posten blir skriven. SIGKILL går inte att fånga: då gör vakten avslutet.
avbryt() {
  AVBRUTEN="$1"
  case "$FAS" in
    fore) stopp "kor.sh avbröts med SIG$1 före bygget";;
    bygge)
      [ -n "$AVBROTT_TID" ] || AVBROTT_TID=$SECONDS
      [ -z "$CLAUDE_PID" ] || kill -TERM -- "-$CLAUDE_PID" 2>/dev/null || kill -TERM "$CLAUDE_PID" 2>/dev/null || true
      vakt_skriv stoppa;;
  esac
}
trap 'avbryt TERM' TERM
trap 'avbryt INT' INT
trap 'avbryt HUP' HUP
# Ägarens domlogg låses under bygget (chflags uchg nedan): bygget når den annars med cp och mv, och dashboarden skriver
# ägarens domar först när bygget är klart. En ändring under körningen är då inte ägarens: korslut ger slutkod 3
# (omgranskningen av skapandeflödet, fynd 2). Saknas loggen skapas den tom, så att den kan låsas.
[ -L "$DOMLOGG" ] && stopp "domloggen underlag/$SLUG/DESIGNDOMAR.jsonl är en länk; bygget startas inte"
chflags nouchg "$DOMLOGG" 2>/dev/null || true   # kvarlämnad flagga efter en avbruten körning
[ -e "$DOMLOGG" ] || : > "$DOMLOGG"
[ -L "$DOMBELAGG" ] && stopp "domarnas beläggbilaga är en länk; bygget startas inte"
chflags nouchg "$DOMBELAGG" 2>/dev/null || true
# Ägarens dom över bygget (DOM.json, dashboardens Din dom) hör också till de skyddade filerna och låses när den finns:
# bygget får aldrig kunna skriva "ägaren godkänner" (granskningen av r101, B1). Den skapas inte här, eftersom
# dashboarden räknar en befintlig DOM.json som en dom; tillkommer den under körningen är det slutkod 3.
[ -L "$DOMFIL" ] && stopp "kunder/$SLUG/DOM.json är en länk; bygget startas inte"
chflags nouchg "$DOMFIL" 2>/dev/null || true   # kvarlämnad flagga efter en avbruten körning
rm -f "$ROOT/kunder/$SLUG/prov/.stoppvakt-antal"
LOGG="$ROOT/kunder/$SLUG/korning-$STAMP.jsonl"

PROMPT="Bygg en webbplats åt verksamheten: $VERKSAMHET
Slug: $SLUG

Följ skillen bygg-sajt (.claude/skills/bygg-sajt/SKILL.md) steg 1–7, i ordning. Underlag i underlag/$SLUG/, bygget i
kunder/$SLUG/sajt/, rapporten i kunder/$SLUG/RAPPORT.md. Körningens identitet är $STAMP: rapportens huvud bär den
(raden korning: $STAMP; steg 7). Ingen människa svarar under körningen: saknas en uppgift, märk den antagande och
fortsätt. Avsluta först när .venv/bin/python kontroller/prova.py $SLUG är grönt, rapporten är
skriven och den oberoende granskaren (kontroller/granska.py) har godkänt sajten. Stoppvakten kör provet och
granskningen själv när du försöker avsluta."
# Skapandeflödet (kunskap/skapandeflodet.md) körs före bygget, utanför sandlådan, och slutar i ägarens val och
# godkännande (kandidatflödet, ägarens uppdrag 2026-10-05). Ett bygge tar vid bara från en godkänd startsida, som
# ateljévinnaren; utan en stannar kor.sh. NWP_ATELJE=av är nödvägen utan ateljé (byggarens eget KONCEPT.md).
# Godkännandet gäller bara när ägarens senaste dom i domloggen är just det och startsidan och DESIGN.md är oförändrade
# (kontroller/skapande.py godkand_giltig; granskningen av skapandeflödet, punkt 2).
GODKAND="$("$ROOT/.venv/bin/python" -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/kontroller")
import skapande
ok, skal = skapande.godkand_giltig(sys.argv[2])
print("ja" if ok else "")' "$ROOT" "$SLUG" 2>/dev/null || true)"
FRYSTA=()   # godkännandets underlagsgrund, fylld nedan från en godkänd startsida
AGARENS_STOPP="$("$ROOT/.venv/bin/python" -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/kontroller")
import prototyp
print(prototyp.bygget_nekas(sys.argv[2]) or "")' "$ROOT" "$SLUG" 2>/dev/null || true)"
# Startkontrollen (kontroller/startkontroll.py; ägarens uppdrag 2026-10-05): verktygslådan bekräftad och versionerna låsta
# före bygget, med kvittot i underlag/$SLUG/atelje/STARTKVITTO-BYGGE.md. Ett nödvändigt verktyg som inte fungerar stoppar
# starten. Uppdateringarna prövas och tas in av det dagliga underhållet (kontroller/underhall.py), aldrig här. Körs bara
# när bygget faktiskt startar (en godkänd startsida eller nödvägen), före allt som skriver i sajten.
if [ -n "$GODKAND" ] || [ "${NWP_ATELJE:-pa}" != "pa" ]; then
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/startkontroll.py" --slug "$SLUG" --start bygge > "$ROOT/kunder/$SLUG/startkontroll.log" 2>&1 \
    || stopp "startkontrollen stoppade bygget: se underlag/$SLUG/atelje/STARTKVITTO-BYGGE-STOPP.md (logg: kunder/$SLUG/startkontroll.log)"
fi
if [ -n "$GODKAND" ]; then
  # godkännandet gäller vinnarens dömda filer: har ett tidigare bygge skrivit om sajtens, läggs vinnarens tillbaka
  ERSATT="$("$ROOT/.venv/bin/python" -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/kontroller")
import atelje
print(", ".join(atelje.installera_godkand(sys.argv[2])))' "$ROOT" "$SLUG")" || stopp "den godkända startsidan kunde inte läggas i sajten (atelje.installera_godkand)"
  [ -z "$ERSATT" ] || echo "den godkända startsidan lades i sajten: $ERSATT (de ersatta i kunder/$SLUG/startsida-ersatt/)"
  # Godkännandet gäller en underlagsversion (VINNARE.json: underlag_sha över skapande.UNDERLAGSGRUND och katalogerna i
  # UNDERLAGSKATALOGER): steg 1–4 är gjorda, och skriver bygget om de filerna blir godkännandet historik (godkand_giltig,
  # Flöde steg 5; GR-20261008-r117-claude#A3). Bygget nekas därför Write och Edit där (--disallowedTools nedan) och Bash
  # i sandlådan (sandlada.py --fryst-underlag); prompten säger var byggets eget innehåll skrivs i stället.
  IFS=' ' read -r -a FRYSTA <<< "$("$ROOT/.venv/bin/python" -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/kontroller")
import skapande
print(" ".join(skapande.UNDERLAGSGRUND + tuple(k + "/**" for k in skapande.UNDERLAGSKATALOGER)))' "$ROOT")" \
    || stopp "underlagsgrunden (kontroller/skapande.py UNDERLAGSGRUND) kunde inte läsas"
  [ ${#FRYSTA[@]} -ge 9 ] || stopp "underlagsgrunden (kontroller/skapande.py UNDERLAGSGRUND) är tom"
  PROMPT="$PROMPT

Ägaren har godkänt startsidan i skapandeflödet (underlag/$SLUG/atelje/VINNARE.json, fältet godkand): ta vid efter valet
i steg 5.1, som från ateljévinnaren. Kör inte ateljén; startsidan står i kunder/$SLUG/sajt/src/pages/index.astro (en
kandidat ur kandidatflödet har också sina undersidor där, och DESIGN.md i kunder/$SLUG/sajt/).
Steg 1–4 är gjorda och godkännandets underlag är fryst: skriv inte om ${FRYSTA[*]} i underlag/$SLUG/ (Write, Edit och
sandlådan nekar det; godkännandet gäller den underlagsversionen, VINNARE.json: underlag_sha, och en ändring gör det
till historik). Saknas INNEHALL.md är TEXTUNDERLAG.md sidans text; innehåll som bygget behöver utöver underlaget
skriver du i kunder/$SLUG/INNEHALL-BYGGE.md. Steg 5–7:s egna arbetsfiler (KONCEPT.md, FRASER.txt, RESOR.json,
JAMFORELSE.md, GRANSKNINGSLOGG.md med flera) skrivs i underlag/$SLUG/ som förut."
elif [ "${NWP_ATELJE:-pa}" = "pa" ] && [ -n "$AGARENS_STOPP" ]; then
  # ägarens dom tillåter inget bygge på startsidan (prototyp.bygget_nekas): nästa steg är skapandeflödet
  stopp "ägarens domlogg tillåter inget bygge på startsidan ($AGARENS_STOPP). Kör .venv/bin/python kontroller/prototyp.py $SLUG före bygget; NWP_ATELJE=av är nödvägen utan ateljé"
elif [ "${NWP_ATELJE:-pa}" = "pa" ] && [ "${NWP_SANDLADA:-av}" = "pa" ]; then
  stopp "skapandeflödet (ateljén) körs utanför sandlådan, före bygget: kör .venv/bin/python kontroller/prototyp.py $SLUG och godkänn startsidan i dashboardens vy Prototyp; NWP_ATELJE=av är nödvägen utan ateljé"
elif [ "${NWP_ATELJE:-pa}" = "pa" ]; then
  # skapandeflödet slutar i ägarens val och godkännande och körs före bygget, aldrig inifrån det (granskningen V3)
  stopp "ingen godkänd startsida: kör .venv/bin/python kontroller/prototyp.py $SLUG, välj bland förslagen och godkänn en i dashboardens vy Prototyp före bygget; NWP_ATELJE=av är nödvägen utan ateljé"
fi

# Referenstjänster via MCP (A/B-posterna om Inspo och om Refero/Mobbin): bara när NWP_MCP_CONFIG pekar på en av filerna i
# kontroller/mcp/ ansluts tjänsten, och bara dess läsande verktyg släpps igenom; annars laddas inga anslutningar alls.
# Alla tre är hostade ändpunkter (ingen lokal kod); inloggningen (OAuth) gör ägaren en gång i en interaktiv session.
# Refero och Mobbin: flödets verktyg ur referenstjanster.TJANSTER, samma lista som kundvakten släpper och metodkartans
# beslut (Tjänsternas verktyg) prövas mot, så att det finns en källa (ägarens uppdrag 2026-10-07, punkt 3A).
tjanstens_verktyg() {
  "$ROOT/.venv/bin/python" -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/kontroller")
import referenstjanster
print(" ".join(referenstjanster.TJANSTER[sys.argv[2]]["verktyg"]))' "$ROOT" "$1"
}
INSPO=()
if [ -n "${NWP_MCP_CONFIG:-}" ] && [ "$NWP_MCP_CONFIG" != "av" ]; then
  [ -f "$NWP_MCP_CONFIG" ] || stopp "NWP_MCP_CONFIG pekar inte på en fil: $NWP_MCP_CONFIG"
  # bara filerna i kontroller/mcp/ (den verkliga sökvägen, inte bara namnet), och bara tjänstens namngivna läsverktyg
  MCP_VERKLIG="$(cd "$(dirname "$NWP_MCP_CONFIG")" && pwd -P)/$(basename "$NWP_MCP_CONFIG")"
  case "$MCP_VERKLIG" in
    "$ROOT/kontroller/mcp/inspo.json")  INSPO=(mcp__inspo__recommend mcp__inspo__search_screens mcp__inspo__get_screen);;
    "$ROOT/kontroller/mcp/mobbin.json")
      TJ="$(tjanstens_verktyg mobbin)" && [ -n "$TJ" ] || stopp "Mobbins verktyg gick inte att läsa ur referenstjanster.TJANSTER"
      INSPO=($TJ);;
    "$ROOT/kontroller/mcp/refero.json")
      TJ="$(tjanstens_verktyg refero)" && [ -n "$TJ" ] || stopp "Referos verktyg gick inte att läsa ur referenstjanster.TJANSTER"
      INSPO=($TJ)
      # Refero ansluts med en personlig nyckel (ingen webbläsarinloggning): anslutningsfilen bär ${REFERO_MCP_TOKEN},
      # värdet ligger i ägarens hemlighetsmapp och exporteras bara till byggets claude-process. Aldrig i repot.
      REFERO_ENV="$HOME/.nortropic-hemligheter/webb-pro/refero.env"
      [ -f "$REFERO_ENV" ] || stopp "Refero: $REFERO_ENV saknas (REFERO_MCP_TOKEN=…, chmod 600)"
      set -a; . "$REFERO_ENV"; set +a
      [ -n "${REFERO_MCP_TOKEN:-}" ] || stopp "Refero: REFERO_MCP_TOKEN saknas i $REFERO_ENV";;
    *) stopp "NWP_MCP_CONFIG: okänd anslutning $MCP_VERKLIG; kända: $ROOT/kontroller/mcp/inspo.json, mobbin.json, refero.json";;
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
  # den rena designstarten 2026-10-09: rapporterna, granskningarna, rensningens register och arkivet är inget byggmaterial
  "Read(./underlag/rapporter/**)" "Read(./underlag/granskningar/**)" "Read(./underlag/rensning/**)" "Read(~/Arkiv/**)"
  # ägarens domar över designen och godkännandet skrivs bara av ägaren (dashboarden), aldrig av bygget
  "Write(./underlag/$SLUG/DESIGNDOMAR.jsonl)" "Edit(./underlag/$SLUG/DESIGNDOMAR.jsonl)"
  "Write(./underlag/$SLUG/DESIGNDOMAR-belagg.jsonl)" "Edit(./underlag/$SLUG/DESIGNDOMAR-belagg.jsonl)"
  "Write(./kunder/$SLUG/atelje/korningar/**)" "Edit(./kunder/$SLUG/atelje/korningar/**)"
  "Write(./kunder/$SLUG/DOM.json)" "Edit(./kunder/$SLUG/DOM.json)"
  # kor.sh:s hashlistor och körningarnas protokoll (START.json, DOM-START.json, slutposterna, de flyttade rapporterna)
  # skrivs bara av kor.sh, vakten och korslut (granskningen GR-20261007-r101-om, BÖR 1)
  "Write(./kunder/$SLUG/prov/.skyddat-*)" "Edit(./kunder/$SLUG/prov/.skyddat-*)"
  "Write(./kunder/$SLUG/korningar/**)" "Edit(./kunder/$SLUG/korningar/**)" "Write(./kunder/$SLUG/rapporter/**)" "Edit(./kunder/$SLUG/rapporter/**)")
# Från en godkänd startsida: godkännandets underlagsgrund (FRYSTA ovan) nekas sessionens Write och Edit här, och Bash
# i sandlådan (sandlada.py --fryst-underlag nedan). Steg 5–7:s egna arbetsfiler i underlag/$SLUG/ berörs inte.
for f in ${FRYSTA[@]+"${FRYSTA[@]}"}; do ARGS+=("Write(./underlag/$SLUG/$f)" "Edit(./underlag/$SLUG/$f)"); done
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
SETTINGS="$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/sandlada.py" "$SLUG" ${GH_DIR:+--gh-dir "$GH_DIR"} ${GODKAND:+--fryst-underlag} ${SANDLADA[@]+"${SANDLADA[@]}"})" || stopp "inställningarna (kontroller/sandlada.py) kunde inte skapas"
if [ "$SETTINGS" != "{}" ]; then ARGS+=(--settings "$SETTINGS"); fi
# R06: med NWP_ARBETSROT=kundrepo och ett kundrepo startar byggsessionen i kunder/$SLUG/kundrepo (kontroller/arbetsrot.py),
# som skapandeflödets sessioner: absoluta regler, motorns rot genom --add-dir, projektets krokar i --settings och inget
# skrivande i kundrepot. Standard är motorns rot tills det verkliga sessionsprovet gett belägg (kontroller/formagoprov.py).
ARBETSROT="$("$ROOT/.venv/bin/python" -B "$ROOT/kontroller/arbetsrot.py" rot "$SLUG")" || stopp "arbetsroten kunde inte bestämmas (kontroller/arbetsrot.py rot)"
if [ "$ARBETSROT" != "$ROOT" ]; then
  AR="$ROOT/kunder/$SLUG/korningar/$STAMP"
  printf '%s\0' "${ARGS[@]}" > "$AR/arbetsrot-fore.args"
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/arbetsrot.py" bygge "$SLUG" < "$AR/arbetsrot-fore.args" > "$AR/arbetsrot.args" \
    || stopp "byggsessionens argument i kundrepot kunde inte skapas (kontroller/arbetsrot.py bygge)"
  ARGS=()
  while IFS= read -r -d '' x_; do ARGS+=("$x_"); done < "$AR/arbetsrot.args"
  [ ${#ARGS[@]} -gt 10 ] || stopp "byggsessionens argument i kundrepot är tomma (kontroller/arbetsrot.py bygge)"
  PROMPT="$(printf '%s' "$PROMPT" | "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/arbetsrot.py" prompt "$SLUG")" \
    || stopp "byggets uppdrag i kundrepot kunde inte skapas (kontroller/arbetsrot.py prompt)"
  echo "arbetsroten är kundrepot: $ARBETSROT (NWP_ARBETSROT=kundrepo)"
fi

# Nästlad start (från en annan Claude Code-session) kräver att sessionens egna variabler tas bort; bygget skriver
# aldrig i ägarens automatiska minne (CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 nedan, kontroller/nastlad.py).
# Bygget går på prenumerationen: API-nyckel, token och bas-URL följer aldrig med (som kontroller/nastlad.py API).
RENSA=(-u CLAUDECODE -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u ANTHROPIC_BASE_URL)
while IFS='=' read -r namn _; do
  case "$namn" in CLAUDE_CODE_*) RENSA+=(-u "$namn");; esac
done < <(env)

cd "$ROOT"   # projektets Stop-krok laddas bara när sessionen startar i reporoten
mkdir -p "$ROOT/kunder/$SLUG/prov"
# Webbtjänsten (kontroller/webbtjanst.py): Chromium kan inte starta inne i sandlådan (mach-register nekas; mätt 2026-10-04),
# så med sandlådan på körs bara webbläsarskripten, lighthouse och granskarnas sessioner (med egen sandlåda) av en tjänst
# utanför sandlådan, bunden till sluggen, domänlistan och byggets kataloger; byggsteg (npm, servering) och byggets modell
# stannar i sandlådan. Verktygen delegerar själva när de körs sandlådade (NWP_WEBBTJANST). Vakten stoppar tjänsten och
# det den startat när bygget är slut.
WT_ENV=()
if [ "${NWP_SANDLADA:-av}" = "pa" ]; then
  # kvitto och logg utanför prov/, som provet rensar vid varje körning (helbygget 2026-10-04)
  WT_KVITTO="$ROOT/kunder/$SLUG/.webbtjanst-$STAMP"; rm -f "$WT_KVITTO"
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/webbtjanst.py" serve --slug "$SLUG" --kvitto "$WT_KVITTO" --korning "$STAMP" \
    ${SANDLADA[@]+"${SANDLADA[@]}"} > "$ROOT/kunder/$SLUG/webbtjanst-$STAMP.log" 2>&1 3>&- 4>&- 8>&- 9>&- &
  WT_PID=$!
  vakt_skriv "wt $WT_PID"
  for _ in $(seq 1 50); do [ -s "$WT_KVITTO" ] && break; sleep 0.2; done
  [ -s "$WT_KVITTO" ] || stopp "webbtjänsten startade inte (kunder/$SLUG/webbtjanst-$STAMP.log)"
  WT_ENV=(NWP_WEBBTJANST="http://127.0.0.1:$(sed -n 1p "$WT_KVITTO")" NWP_WEBBTJANST_NYCKEL="$(sed -n 2p "$WT_KVITTO")")
fi
rm -f "$FORE_FIL" "$EFTER_FIL"   # en planterad symlänk ska inte få styra vart listorna skrivs
# Misslyckad låsning stoppar bygget före modellstarten, och flaggorna verifieras uttryckligen (Codex R23: ett olåst
# tillstånd fick annars bli förebild, och slutkontrollen såg ingen skillnad).
chflags uchg "$ROOT/kunder" "$ROOT/underlag" 2>/dev/null || stopp "kunder/ och underlag/ kunde inte låsas mot nya kataloger (chflags uchg); bygget startas inte"
for d in kunder underlag; do
  stat -f %Sf "$ROOT/$d" 2>/dev/null | grep -q uchg || stopp "$d/ är inte låst (flaggan uchg saknas efter chflags); bygget startas inte"
done
chflags uchg "$DOMLOGG" 2>/dev/null && stat -f %Sf "$DOMLOGG" 2>/dev/null | grep -q uchg || stopp "domloggen underlag/$SLUG/DESIGNDOMAR.jsonl kunde inte låsas (chflags uchg); bygget startas inte"
if [ -e "$DOMBELAGG" ]; then
  chflags uchg "$DOMBELAGG" 2>/dev/null && stat -f %Sf "$DOMBELAGG" 2>/dev/null | grep -q uchg || stopp "domarnas beläggbilaga kunde inte låsas; bygget startas inte"
fi
DOMSTART=saknas
if [ -e "$DOMFIL" ]; then
  chflags uchg "$DOMFIL" 2>/dev/null && stat -f %Sf "$DOMFIL" 2>/dev/null | grep -q uchg || stopp "kunder/$SLUG/DOM.json kunde inte låsas (chflags uchg); bygget startas inte"
  # Ägarens dom som den var när den låstes: en kopia i körningens katalog och dess sha256 i kor.sh:s minne. Ändrar
  # bygget DOM.json räknas domarna i kopian fortfarande, aldrig de som tillkom (granskningen av r101, KAN 3).
  cat "$DOMFIL" > "$ROOT/kunder/$SLUG/korningar/$STAMP/DOM-START.json" || stopp "kunder/$SLUG/DOM.json kunde inte kopieras till körningens katalog; bygget startas inte"
  DOMSTART="$(shasum -a 256 < "$ROOT/kunder/$SLUG/korningar/$STAMP/DOM-START.json" | cut -d' ' -f1)"
fi
vakt_skriv "domstart $DOMSTART"
# En äldre RAPPORT.md (ett tidigare bygges) flyttas till kunder/<slug>/rapporter/RAPPORT-fore-<körning>.md när bygget
# startar, och inget raderas: den uppfyller aldrig rapportkravet för det här bygget, och stoppvakten kräver en rapport
# skriven i körningen (ägarens uppdrag 2026-10-07, punkt 5). En start som stannar ovan lämnar den på sin plats.
if [ -e "$ROOT/kunder/$SLUG/RAPPORT.md" ] || [ -L "$ROOT/kunder/$SLUG/RAPPORT.md" ]; then
  [ ! -L "$ROOT/kunder/$SLUG/rapporter" ] && mkdir -p "$ROOT/kunder/$SLUG/rapporter" \
    && mv -n "$ROOT/kunder/$SLUG/RAPPORT.md" "$ROOT/kunder/$SLUG/rapporter/RAPPORT-fore-$STAMP.md" \
    && [ ! -e "$ROOT/kunder/$SLUG/RAPPORT.md" ] && [ ! -L "$ROOT/kunder/$SLUG/RAPPORT.md" ] \
    || stopp "den äldre kunder/$SLUG/RAPPORT.md kunde inte flyttas till kunder/$SLUG/rapporter/; bygget startas inte"
fi
# Hashlistan före körningen och dess sha256 i kor.sh:s minne: ett eget skript i bygget kan skriva om filen, men inte
# minnet, så en förfalskad lista är slutkod 3 (granskningen GR-20261007-r101-om, BÖR 1).
{ skyddat; grans; } > "$FORE_FIL"
FORE_SHA="$(shasum -a 256 < "$FORE_FIL" | cut -d' ' -f1)"
vakt_skriv "fore $FORE_SHA"
echo "Körning $SLUG startad $STAMP. Logg: $LOGG"
set +e
# claude körs i bakgrunden och väntas in, så att en signal till kor.sh når fällan direkt (avbryt ovan) och inte först
# när sessionen är klar. Den startas i en egen session och processgrupp (os.setsid), med SIGPIPE i grundläge, så att
# signalen kan gå till hela gruppen; vakten följer det som lämnar gruppen.
SESSION='import os, signal, sys
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
try:
    os.setsid()
except OSError:
    pass
os.execvp(sys.argv[1], sys.argv[1:])'
FAS=bygge
cd "$ARBETSROT"   # R06: sessionens arbetskatalog; kor.sh själv arbetar vidare i motorns rot (nedan)
printf '%s' "$PROMPT" | env "${RENSA[@]}" CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 NWP_SLUG="$SLUG" NWP_KORNING="$STAMP" NWP_COMMIT_TILLATET="backlog/" NWP_SANDLADA="${NWP_SANDLADA:-av}" ${WT_ENV[@]+"${WT_ENV[@]}"} "$ROOT/.venv/bin/python" -B -c "$SESSION" claude "${ARGS[@]}" > "$LOGG" 2>&1 3>&- 4>&- 8>&- 9>&- &
CLAUDE_PID=$!
cd "$ROOT"
vakt_skriv "claude $CLAUDE_PID"
if [ -n "$AVBRUTEN" ]; then  # en signal innan pid:en var känd
  kill -TERM -- "-$CLAUDE_PID" 2>/dev/null || kill -TERM "$CLAUDE_PID" 2>/dev/null || true
  vakt_skriv stoppa
fi
wait "$CLAUDE_PID"; RC=$?
# en fångad signal avbryter wait: claude får NWP_FRIST sekunder efter SIGTERM, sedan SIGKILL till hela gruppen (KAN 5)
while [ -n "$AVBRUTEN" ]; do
  if ! kill -0 "$CLAUDE_PID" 2>/dev/null; then
    wait "$CLAUDE_PID" 2>/dev/null; R2=$?
    [ "$R2" = 127 ] || RC=$R2   # 127: wait har redan gett claudes kod
    break
  fi
  [ $((SECONDS - AVBROTT_TID)) -lt "$FRIST" ] || kill -KILL -- "-$CLAUDE_PID" 2>/dev/null || kill -KILL "$CLAUDE_PID" 2>/dev/null || true
  sleep 1
done
FAS=slut
trap '' TERM INT HUP   # avslutet skriver posten och avbryts inte (barnen ärver det)
# Byggets processer stoppas innan något jämförs eller släpps: vakten stoppar claudes och webbtjänstens träd, också
# processer som lämnat sin session (granskningen GR-20261007-r101-om, BÖR 1, punkt l, och BÖR 2), och svarar med vad den
# stoppade och vad som finns kvar. Svarar den inte stoppas åtminstone claudes processgrupp, och korslut räknar då inte
# ägarens dom.
PROCESSER="$(vakt_fraga "slut $RC")"; STOPPAT=1
if [ -z "$PROCESSER" ]; then
  kill -TERM -- "-$CLAUDE_PID" 2>/dev/null; sleep 1; kill -KILL -- "-$CLAUDE_PID" 2>/dev/null
fi
# Hashlistan efter körningen, också när något i den faller: korslut får då veta det och ger slutkod 3 i stället för att
# kor.sh avslutas utan post (GR-20261007-r101-om2#KAN-5).
EFTER_FEL=""
rm -rf "$EFTER_FIL" 2>/dev/null
{ skyddat; grans; } > "$EFTER_FIL" 2>/dev/null || EFTER_FEL="skyddat/grans gav kod $?"
EFTER_SHA="$(shasum -a 256 < "$EFTER_FIL" 2>/dev/null | cut -d' ' -f1)"
vakt_skriv "efter ${EFTER_SHA:-saknas}"
# Avslutet och slutkoden räknas av kontroller/korslut.py (revisionen 2026-10-03, F10 och F11): 0 godkänt, 1 avslutat utan
# godkännande, 3 mekaniken eller hashlistorna ändrades under körningen, 4 claude föll eller körningen avbröts, 5
# slutposten uteblev, 6 ateljén förkastade alla riktningar och bygget stannade utan sajt (designprovet, ägarbeslut
# 2026-10-04). Skriptets slutkod är korsluts. Korslut skriver slutposten kunder/<slug>/korningar/<körning>/SLUT.json och
# beskedet ur den (ägarens uppdrag 2026-10-07, punkt 4). Låsen släpps först när posten är skriven.
NWP_AVBRUTEN="$AVBRUTEN" NWP_VERKSAMHET="$VERKSAMHET" NWP_SKYDDAT_SHA256="$FORE_SHA ${EFTER_SHA:-saknas}" NWP_PROCESSER="$PROCESSER" \
  NWP_DOM_START_SHA256="$DOMSTART" NWP_EFTER_FEL="$EFTER_FEL" NWP_VAKT_BEKRAFTA_FD=3 \
  "$ROOT/.venv/bin/python" -B "$ROOT/kontroller/korslut.py" "$ROOT/kunder/$SLUG" "$RC" "$FORE_FIL" "$EFTER_FIL" "$STAMP"
KORSLUT=$?
BEKRAFTELSE="$(vakt_fraga bekraftad)"
case "$BEKRAFTELSE" in bekraftad\ *) ;; *) echo "Vakten har ingen bekräftelse för slutposten; ett avbrott räknas om.";; esac
chflags nouchg "$ROOT/kunder" "$ROOT/underlag" "$DOMLOGG" 2>/dev/null
chflags nouchg "$DOMBELAGG" 2>/dev/null
chflags nouchg "$DOMFIL" 2>/dev/null
# Bygget skriver backlogposter men har ingen git: efter korsluts bedömning publicerar kontroller/backlog_commit.py bara
# byggets egna poster (märkta med körningen), med commitvaktens kontroller, aldrig vid ändrad mekanik, och pushar bara en
# utgående historik som enbart rör backlog/ (Codex 2026-10-04, F27 och F3). Misslyckad publicering ändrar inte slutkoden.
"$ROOT/.venv/bin/python" -B "$ROOT/kontroller/backlog_commit.py" "$SLUG" "$STAMP" "$KORSLUT"
exit $KORSLUT
}
