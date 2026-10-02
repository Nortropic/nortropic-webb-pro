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
.venv/bin/python -m pip install yt-dlp youtube-transcript-api imageio-ffmpeg
(cd kontroller && npm install)
```

Kräver Node 22.12 eller senare, Google Chrome (eller Playwrights chromium) och Claude Code.
