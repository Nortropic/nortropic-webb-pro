# nortropic-webb-pro

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg, med Claude Code som utförare och ägaren som
domare. Varför repot finns och vad som beslutades: `BESLUT.md`.

## Dashboarden

```sh
./dashboard.sh        # http://127.0.0.1:4771
```

Allt på ett ställe: vyn Prototyp, där du väljer bland förslagen och godkänner en startsida (besluten skrivs i
domloggen `underlag/<slug>/DESIGNDOMAR.jsonl`), byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag,
körningens händelser), frågeformuläret där du dömer ett bygge, Starta, de blinda jämförelserna, kalibreringen,
designprovet, backloggen, kirurgen (klistra in en länk) och lärdomarna. Vyn Dokumentation och rapporter börjar med en
sammanfattning och visar sedan hur Nortropic fungerar, pågående uppdrag, granskningarna och besluten, lästa ur de platser
som avsnittet Var information finns anger.

## Tre loopar och en backlog

| Loop | Vad | Var |
|---|---|---|
| 1. Inne i ett bygge | kontrollera, rätta, kör igen tills grönt och granskaren godkänner | `kontroller/prova.py`, `kontroller/granska.py`, stoppvakten i `.claude/hooks/` |
| 2. Genom stegen | upptäckt, definition, innehåll, design, bygge, prov, rapport | skillen `bygg-sajt` |
| 3. Mellan byggen | ägarens dom blir en textändring | frågeformuläret, `LARDOMAR.md`, backloggen |

**Backloggen** (`backlog/`) fylls automatiskt med vilande poster: kirurgens "ta in" och "prova", ägarens domar och
brister som byggena hittar i verktygen. Inget genomförs av sig självt. Starta en Claude Code-session i repot och säg
**"implementera enligt backlog"**.

## Kedjan från kundunderlag till leverans

Den här tabellen är grundkällan för vem som startar vad, med vilket kommando. Kommandona körs från repots rot.
Designflödet i detalj: `kunskap/skapandeflodet.md`; helbygget: skillen `bygg-sajt`; exporten och leveransen:
`kunskap/lansering.md`. Inget bygge har lanserats än.

| Steg | Vem startar, med vilket kommando | Resultat | Saknas i dag |
|---|---|---|---|
| 1. Kundunderlaget: fakta, research, brief, text, bilder, referenser och sajten ur mallen | en interaktiv Claude Code-session i repot som följer `bygg-sajt` steg 1–4 och kör `.venv/bin/python kontroller/ny_sajt.py <slug> --installera`; eller nödvägen `NWP_ATELJE=av ./kor.sh <slug> "<verksamhet>"`, ett helt bygge utan skapandeflödet | `underlag/<slug>/` (VERKSAMHET.json, RESEARCH.md, BRIEF.md, INNEHALL.md, bilder/BILDER.md, referenser/) och `kunder/<slug>/sajt/` | ett eget kommando: i standardläget körs steg 1–4 bara inne i kor.sh, som kräver en godkänd startsida |
| 2. Prototypen: research, plan och cirka tio skisser | ägaren eller en session i terminalen: `.venv/bin/python kontroller/prototyp.py <slug>` (läget följer domloggen) | förslagen i vyn Prototyp | – |
| 3. Ägarens val | ägaren i vyn Prototyp; en dom som kommit på annat sätt förs in med `.venv/bin/python kontroller/skapande.py dom` | en dom i domloggen, bunden till kandidat och version | dashboarden startar ingen körning: nästa steg startas i terminalen |
| 4. Förfiningen av de valda | ägaren kör `prototyp.py <slug>` igen (läget valda) | förfinade kandidater med DESIGN.md | – |
| 5. Godkännandet | ägaren i vyn Prototyp: en förfinad kandidat godkänd för helbygge | `underlag/<slug>/atelje/vinnare/` och VINNARE.json | vyn visar inget kommando för helbygget; det står i prototyp.py:s utskrift |
| 6. Helbygget | ägaren i terminalen: `./kor.sh <slug> "<verksamhet>"`; utan godkänd startsida stannar kor.sh med slutkod 2 | `kunder/<slug>/` (sajt, prov, granskning, RAPPORT.md, FRAGOR.json) och slutposten `kunder/<slug>/korningar/<körning>/SLUT.json`, också när kor.sh stannar före bygget | uppdraget säger både "steg 1–7, i ordning" och "ta vid efter valet i steg 5.1"; att underlaget som den godkända startsidan byggdes på står kvar är inte prövat. Dashboarden visar inte slutposten än |
| 7. Ägarens dom över bygget | ägaren i dashboarden: bygget, fliken Din dom | `kunder/<slug>/DOM.json`, lärdomarna och en backlogpost | – |
| 8. Exporten till kundrepo | ägaren eller en session: `.venv/bin/python kontroller/exportera.py <slug> [--git]` | `kunder/<slug>/kundrepo/`, byggt och prövat i en tom katalog; `--git` gör en lokal commit | exporten prövar inte att bygget är godkänt och sparar inget besked |
| 9. Leveransen: GitHub, Vercel, skydd och DNS | GitHub, Vercel och skyddet: människa, eller en session med ägarens ja; DNS: bara en behörig människa | – | inget verktyg i repot för GitHub och Vercel; `kontroller/driftkoll.py` prövar en driftsatt adress och skriver bara ut |

Helbygget går obevakat från den godkända startsidan: byggaren bygger resten av sajten i `kunder/<slug>/sajt/`, provar
tills grindarna är gröna och två oberoende granskare godkänt, eller tills taket nås (slutkod 1), och skriver `kunder/<slug>/RAPPORT.md` och sina egna
frågor till dig. Rapporten gäller bara när den skrivits i körningen; ett tidigare bygges rapport flyttas till
`kunder/<slug>/rapporter/` när bygget startar. Körningens slutbesked sparas i slutposten (Var information finns, nedan).
Alternativa lägen och återupptagning: `kunskap/skapandeflodet.md` och `./kor.sh` utan argument.
Råmaterial (`underlag/`) och byggen (`kunder/`) ligger utanför git.

## Var information finns

Tabellen bestämmer var varje slag av information hör hemma (ägarens uppdrag 2026-10-06 om dokumentations- och
rapportstrukturen, `BESLUT.md`). Andra dokument länkar hit i stället för att upprepa den.

| Slag | Plats och namn | Skrivs av |
|---|---|---|
| Start och överblick | den här filen; `CLAUDE.md` för sessioner | agenten |
| Gällande arbetssätt: guider, krav, referens och förklaringar | `kunskap/<ämne>.md`, ett ämne per fil; skills i `.claude/skills/<namn>/SKILL.md`; granskarens kriterier i `kritik/`. En fil som inte gäller fullt ut börjar med raden `Status: historik, ersatt av …` eller `Status: vilande till …` | agenten, i samma commit som beteendet ändras |
| Beslut | `BESLUT.md`: ett `## Tillägg ÅÅÅÅ-MM-DD: <titel>` per beslut (rubriken är beslutets id), med raden `**Status:**` (gäller, delvis ersatt av … eller ersatt av …) direkt under rubriken, och sedan ägarens ord ordagrant, skälen och räckvidden. Ett ersatt beslut ligger kvar och märks. Kundbeslut: `underlag/<slug>/DESIGNDOMAR.jsonl` | agenten med ägarens ord |
| Förbättringsarbete | `backlog/B-ÅÅÅÅMMDD-<namn>.md` (`backlog/README.md`). `klar` betyder genomförd och committad; verifierad är posten först när en senare granskning säger det | `kontroller/backlog.py`, agenten |
| Projekt- och körningsrapporter | i flödet där verktygen skriver: `underlag/<slug>/atelje/` och `kunder/<slug>/`; helbyggets slutpost per körning: `kunder/<slug>/korningar/<körning>/SLUT.json` (`kontroller/korslut.py`), och ett tidigare bygges rapport: `kunder/<slug>/rapporter/`; utanför flödet: `underlag/<uppdrag>/` (som `underlag/figma-pilot/BESLUTSUNDERLAG.md`); lägesrapporter till ägaren: `underlag/rapporter/RAPPORT-ÅÅÅÅ-MM-DD-<namn>.md` | agenten, verktygen |
| Systemgranskningar | `underlag/granskningar/GR-ÅÅÅÅMMDD-<ämne>.md`, en fil per granskning, med bevisen i katalogen `underlag/granskningar/GR-ÅÅÅÅMMDD-<ämne>/`; en omgranskning är en ny fil som anger den föregående, och fynden heter `<rapportens id>#<fynd>`. Äldre rapporter ur sessioners arbetsytor ligger i `underlag/granskningar/sessioner/`. `FORTECKNING.jsonl` har en rad per fil, med ursprung och sha256 | den granskande sessionen |
| Bevismaterial: bilder, mätningar, loggar och kvitton | där verktyget skriver (`prov/`, startkvitton, `VERSION.json`, `bilder/`, `matning/`). Frysta kvitton skrivs aldrig över; ett mätskript som ett kvitto hänvisar till kopieras till uppdragets `matning/` | verktygen |
| Historik och tillfälligt | git-historiken och filer märkta `Status: historik`. Tillfälliga anteckningar i sessionens arbetsyta och `/tmp` gallras (städregeln, `BESLUT.md`); det som en rapport, ett beslut eller en commit citerar kopieras först till `underlag/granskningar/` | agenten |

Allt under `underlag/` och `kunder/` är privat. Inget innehåll därifrån står i det publika repot, inte heller titlar ur
rapporter eller förteckningar; sökvägar och id:n får stå, i dokumentationen, commits och backlogposter, så länge de inte
bär privata uppgifter. Dashboardens vy Dokumentation och rapporter läser platserna och rapporthuvudena här vid varje
visning, utan egen förteckning, och visar det som ligger under `underlag/` och `kunder/` bara lokalt och inom flödesvyns
gränser, också blindningen före ägarens första val.

**Arbetsregeln** (ägaren 2026-10-06): ”Varje förändring i Nortropic ska hålla berörd dokumentation och spårbarhet
aktuell som en del av samma uppdrag. Ägaren ska inte behöva påminna om dokumentationen. Ett arbete redovisas inte som
färdigt förrän berörda instruktioner, rapportkopplingar och statusuppgifter är uppdaterade, eller en konkret
kvarstående begränsning har redovisats.” Ett skrivskyddat uppdrag ändrar inga filer och redovisar
dokumentationsbehovet i stället.

**Rapporthuvudet.** En bestående rapport börjar med ett huvud (YAML mellan `---`) med de fält som är relevanta:
- **Identitet och typ:** `id` (stabilt), `titel`, `typ`, `uppdrag`, `kund` eller `systemdel` och `moment`.
- **Vem och när:** `forfattare` (roll eller session) och `datum`.
- **Vad som granskats:** `granskad_identitet`, alltså repo och commit, körning, kandidatversion, designversion eller
  annat exakt underlag.
- **Status och utfall:** `rapportstatus` (utkast, färdig eller ersatt) och `bedomningsutfall` (godkänt, underkänt,
  ofullständigt eller ej bedömt).
- **Länkar:** `underlag`, `foregaende`, `ersatt_av`, `beslut` och `atgarder`.
- **Rättelser och giltighet** (valfria): `rattelser`, en lista med "datum: vad som rättats, var", och `giltighet`, till
  exempel utvecklingsdata eller historik, med skäl; en rättad slutsats skrivs inte om i texten, och dashboarden visar
  rättelserna vid rapporten och i översikten.

Ett värde som saknas skrivs "ej angivet". Rapportstatus och utfall är olika saker: en färdig rapport kan underkänna
resultatet. Ett exempel är `underlag/figma-pilot/BESLUTSUNDERLAG.md`.

**Helbyggets slutpost** (`kunder/<slug>/korningar/<körning>/SLUT.json`, skriven av `kontroller/korslut.py`; ägarens
uppdrag 2026-10-07) bär rapporthuvudets fält i JSON, så att den läses som ett huvud. `underlag` är länkarna till
rapporter och bevis, och `atgarder` är nästa steg. Därtill:
- körningen, bygget (`dist_sha256`), metoden och slutkoden;
- de fem tillstånden var för sig: sessionen avslutad normalt, tekniskt godkänt, designgranskaren godkänner, ägaren
  godkänner och klart för leverans inom angiven omfattning;
- bristerna.

Terminalens besked skrivs ur posten. Ägarens dom räknas bara ur en `kunder/<slug>/DOM.json` som bygget inte kan ha
skrivit: den är låst och skyddad under körningen, och en dom som tillkom under en körning räknas aldrig. `.venv/bin/python
kontroller/korslut.py --visa kunder/<slug>` prövar posten mot läget nu. Har bygget i `kunder/<slug>/sajt/dist/`,
granskningens metod eller startsidans godkännande ändrats sedan körningen står postens godkännanden som historik, och
klart för leverans är nej.
En körning som avbröts utan slutpost (SIGKILL) syns där och i nästa körnings post. Slutkod 5 betyder att posten
uteblev.

**Läsordningen:**
1. slutsatsen och vad den gäller;
2. de viktigaste fynden;
3. underlag och jämförelser;
4. begränsningar och det som inte prövats;
5. nästa åtgärd och de beslut som behövs.

**En senare granskning** säger vad den gör med den föregående: bekräftar fynd, verifierar en rättelse, gäller en ny
version eller rättar en tidigare slutsats. Ett fynd behåller sitt id från upptäckt till rättelse och verifiering, och
består det efter rättelsen öppnas dess post i backloggen igen (`backlog/README.md`).

## Kirurgen

I dashboarden under Kirurgen, eller i en session i repots rot: `/kirurg <url>` (GitHub, artikel eller YouTube).
Bara transkriptet: `.venv/bin/python kontroller/youtube.py URL --ut video.md`.

Spanaren (`kontroller/spana.py`) letar kandidater åt kirurgen utan modell: flöden, leverantörsdokumentation, GitHub,
Hacker News och YouTube-kanaler ur `kunskap/spaning-kallor.md`. Dashboarden kör den en gång i veckan och visar de
rankade kandidaterna under Kirurgen; "Skicka till kirurgen" startar ett vanligt intag. Själv: `.venv/bin/python kontroller/spana.py
spana --torr` visar vad den skulle hitta utan att spara.

## Prospekt

Hittar verksamheter i en bransch och kommun, mäter deras webbplats och rankar dem efter vad de har att vinna.
Reglerna: `kunskap/prospekt-och-utskick.md`; beslutet: `BESLUT.md`, tillägget 2026-10-02.

```sh
.venv/bin/python kontroller/prospekt.py svep --kampanj hantverkare-lulea --kommun 2580 --bransch hantverkare
.venv/bin/python kontroller/prospekt.py sajter --kampanj hantverkare-lulea --max 40
.venv/bin/python kontroller/prospekt.py analysera --kampanj hantverkare-lulea --max 10
.venv/bin/python kontroller/prospekt.py lista --kampanj hantverkare-lulea
.venv/bin/python kontroller/utskick.py prov          # testbrev till din egen adress
```

Samma sak med knappar i dashboarden under Prospekt: kampanj, lista, kort per verksamhet, demo, brev. Knappen demo
startar `./kor.sh` och stannar därför, som helbygget, utan en godkänd startsida (kedjan ovan). Ett brev skrivs
ur det vi mätt, du godkänner det i dashboarden, och det går aldrig till en enskild firma. Allt om verksamheterna
ligger i `underlag/prospekt/` och `underlag/<slug>/`, utanför git.

Nycklar, en gång: `~/.nortropic-hemligheter/webb-pro/scb.env` med `SCB_API_NYCKEL=…` (avgiftsfri, BankID på
registreraafr.scb.se) och `resend.env` med `RESEND_API_NYCKEL`, `AVSANDARE`, `SVAR_TILL`, `FORETAG`, `TELEFON`.
Katalogen 0700, filerna 0600.

## Provet

```sh
.venv/bin/python kontroller/prova.py <slug>          # alla grindar
.venv/bin/python kontroller/prova.py <slug> --snabb  # utan Lighthouse och utforskning
.venv/bin/python kontroller/granska.py <slug>        # oberoende granskning i en egen session (efter provet)
kontroller/rokprov.sh                                 # regressionsprov efter ändringar i kontroller/ eller mall/
```

Grindar (nio): bygge, design, seo, standard, axe, lighthouse, spill, utan-js, resor. Grinden standard prövar
byggstandardens maskinkontrollerbara punkter (`kunskap/byggstandard.md`, `kontroller/standard_kontroll.py`), med giltig
HTML via html-validate lokalt. Grinden design prövar DESIGN.md mot koden (`kunskap/bygge-referens.md`), och grinden
resor kör briefens viktigaste resor i Chromium och WebKit (`kunskap/resor.md`). Copykontrollen är en rapport, inte en
grind (`kunskap/copy-kontroll.md`): varje fynd rättas eller motiveras i rapporten. Apple-touch-icon och delningsbild
görs med `node kontroller/ikoner.mjs`.

## Installation (en gång per maskin)

```sh
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
(cd kontroller && npm ci && npx playwright install chromium chromium-headless-shell webkit)
```

Kräver Node i den senaste LTS-versionen som Vercel stöder (Homebrews `node@NN`), Claude Code och Vercel CLI. Det
dagliga underhållet (`kontroller/underhall.py`, från dashboarden) håller allt detta i den senaste versionen som klarat
proven, och startkontrollen (`kontroller/startkontroll.py`) bekräftar läget före varje start (`kunskap/beroenden.md`,
Underhåll).
