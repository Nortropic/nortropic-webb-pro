# nortropic-webb-pro

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg, med Claude Code som utförare och ägaren som
domare. Varför repot finns och vad som beslutades: `BESLUT.md`.

## Dashboarden

```sh
./dashboard.sh        # http://127.0.0.1:4771
```

Allt på ett ställe: vyn Prototyp, där du väljer bland förslagen och godkänner en startsida (besluten skrivs i
domloggen `underlag/<slug>/DESIGNDOMAR.jsonl`), byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag,
körningens händelser), frågeformuläret där du dömer ett bygge, backloggen, kirurgen (klistra in en länk) och lärdomarna.

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
| 6. Helbygget | ägaren i terminalen: `./kor.sh <slug> "<verksamhet>"`; utan godkänd startsida stannar kor.sh med slutkod 2 | `kunder/<slug>/` (sajt, prov, granskning, RAPPORT.md, FRAGOR.json) | uppdraget säger både "steg 1–7, i ordning" och "ta vid efter valet i steg 5.1"; att underlaget som den godkända startsidan byggdes på står kvar är inte prövat. Korsluts slutkod skrivs bara ut |
| 7. Ägarens dom över bygget | ägaren i dashboarden: bygget, fliken Din dom | `kunder/<slug>/DOM.json`, lärdomarna och en backlogpost | – |
| 8. Exporten till kundrepo | ägaren eller en session: `.venv/bin/python kontroller/exportera.py <slug> [--git]` | `kunder/<slug>/kundrepo/`, byggt och prövat i en tom katalog; `--git` gör en lokal commit | exporten prövar inte att bygget är godkänt och sparar inget besked |
| 9. Leveransen: GitHub, Vercel, skydd och DNS | GitHub, Vercel och skyddet: människa, eller en session med ägarens ja; DNS: bara en behörig människa | – | inget verktyg i repot för GitHub och Vercel; `kontroller/driftkoll.py` prövar en driftsatt adress och skriver bara ut |

Helbygget går obevakat från den godkända startsidan: byggaren bygger resten av sajten i `kunder/<slug>/sajt/`, provar
tills grindarna är gröna och två oberoende granskare godkänt, eller tills taket nås (slutkod 1), och skriver `kunder/<slug>/RAPPORT.md` och sina egna
frågor till dig. Alternativa lägen och återupptagning: `kunskap/skapandeflodet.md` och `./kor.sh` utan argument.
Råmaterial (`underlag/`) och byggen (`kunder/`) ligger utanför git.

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
