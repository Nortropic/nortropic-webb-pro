# nortropic-webb-pro

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg, med Claude Code som utförare och ägaren som
domare. Varför repot finns och vad som beslutades: `BESLUT.md`.

## Tre loopar

| Loop | Vad | Var |
|---|---|---|
| 1. Inne i ett bygge | kontrollera, rätta, kör igen tills grönt | `kontroller/prova.py`, stoppvakten i `.claude/hooks/` |
| 2. Genom stegen | upptäckt → definition → innehåll → design → bygge → prov → rapport | skillen `bygg-sajt` |
| 3. Mellan byggen | ägarens dom blir en textändring | `LARDOMAR.md` → `regler/`, skillen, `kunskap/` |

Kirurgen (skillen `kirurg`) bedömer repon, skills och videor som ägaren skickar, mot såren i `LARDOMAR.md`.
Domarna står i `kunskap/REGISTER.md`.

## En körning

```sh
./kor.sh <slug> "<verksamhetens namn, ort och gärna webbadress>"
```

Körningen går obevakat: hämtar det publika, mäter deras nuvarande sajt, skriver brief och text, bygger en Astro-sajt
i `kunder/<slug>/sajt/`, provar tills grindarna är gröna och skriver `kunder/<slug>/RAPPORT.md`. Titta sedan:

```sh
cd kunder/<slug>/sajt && npx astro preview
```

Skriv domen i `LARDOMAR.md`. Råmaterial (`underlag/`) och byggen (`kunder/`) ligger utanför git.

## Kirurgen

I en Claude Code-session i repots rot: `/kirurg <url>` (GitHub, artikel eller YouTube).

## Provet för hand

```sh
.venv/bin/python kontroller/prova.py <slug>          # alla grindar
.venv/bin/python kontroller/prova.py <slug> --snabb  # utan Lighthouse och utforskning
```

Grindar: bygge, seo, copy, antislop, axe, lighthouse, spill, utan-js. Krav och detaljer överst i `kontroller/prova.py`.

## Installation (en gång per maskin)

```sh
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install yt-dlp youtube-transcript-api
(cd kontroller && npm install)
```

Kräver Node 22.12 eller senare, Google Chrome (eller Playwrights chromium) och Claude Code.

## Vad ägaren fyller i

- `referenser/REFERENSER.md`: tio sajter som är världsklass för branschen.
- `regler/antislop.md`: regeln med egna ord (ett utkast står där nu).
- `LARDOMAR.md`: domen efter varje bygge.
