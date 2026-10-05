# nortropic-webb-pro

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg, med Claude Code som utförare och ägaren som
domare. Varför repot finns och vad som beslutades: `BESLUT.md`.

## Dashboarden

```sh
./dashboard.sh        # http://127.0.0.1:4771
```

Allt på ett ställe: byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag, körningens händelser),
frågeformuläret där du dömer ett bygge, backloggen, kirurgen (klistra in en länk) och lärdomarna.

## Tre loopar och en backlog

| Loop | Vad | Var |
|---|---|---|
| 1. Inne i ett bygge | kontrollera, rätta, kör igen tills grönt och granskaren godkänner | `kontroller/prova.py`, `kontroller/granska.py`, stoppvakten i `.claude/hooks/` |
| 2. Genom stegen | upptäckt, definition, innehåll, design, bygge, prov, rapport | skillen `bygg-sajt` |
| 3. Mellan byggen | ägarens dom blir en textändring | frågeformuläret, `LARDOMAR.md`, backloggen |

**Backloggen** (`backlog/`) fylls automatiskt med vilande poster: kirurgens "ta in" och "prova", ägarens domar och
brister som byggena hittar i verktygen. Inget genomförs av sig självt. Starta en Claude Code-session i repot och säg
**"implementera enligt backlog"**.

## En körning

```sh
./kor.sh <slug> "<verksamhetens namn, ort och gärna webbadress>"
```

Körningen går obevakat: hämtar det publika, mäter deras nuvarande sajt, hittar och öppnar referenser, skriver brief
och text, bygger en Astro-sajt i `kunder/<slug>/sajt/`, provar tills grindarna är gröna, skriver
`kunder/<slug>/RAPPORT.md` och sina egna frågor till dig. Råmaterial (`underlag/`) och byggen (`kunder/`) ligger
utanför git.

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

Samma sak med knappar i dashboarden under Prospekt: kampanj, lista, kort per verksamhet, demo, brev. Ett brev skrivs
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

Grindar: bygge, seo, standard, axe, lighthouse, spill, utan-js. Grinden standard prövar byggstandardens
maskinkontrollerbara punkter (`kunskap/byggstandard.md`, `kontroller/standard_kontroll.py`), med giltig HTML via
html-validate lokalt. Copykontrollen är en rapport, inte en grind (`kunskap/copy-kontroll.md`): varje fynd rättas
eller motiveras i rapporten. Apple-touch-icon och delningsbild görs med `node kontroller/ikoner.mjs`.

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
