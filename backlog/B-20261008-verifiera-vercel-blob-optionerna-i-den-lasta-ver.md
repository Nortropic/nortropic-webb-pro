---
id: B-20261008-verifiera-vercel-blob-optionerna-i-den-lasta-ver
status: vilande
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#D8
skapad: 2026-10-08
prio: normal
steg: main: kontroller/exportera.py, kontroller/driftkoll.py
---
# Verifiera @vercel/blob-optionerna i den låsta versionen och säkerhetshuvudenas samspel med vercel.json

**Varför:** forfragan.js använder abortSignal, allowOverwrite, addRandomSuffix och access private; den låsta versionen (2.8.0) kunde inte läsas lokalt (ingen installerad kopia, npm-cachen saknar tarballen), så forfragan.md:s "kontrollerad i källan" vilar på läsning. Funktionens 422/202-sidor sätter no-referrer och en strängare CSP än vercel.json:s huvuden på /(.*); vilket värde plattformen låter gälla är oprövat (GR-20261008-r117-claude D8–D9).

**Förslag:** Låt exportens byggprov (verifiera_bygge) eller underhållet greppa SDK:ns put-typer efter optionsnamnen; pröva huvudena mot en förhandsvisning med driftkoll.py.

**Klart när:** Optionerna är belagda ur den installerade SDK-versionen och huvudena mätta i en förhandsvisning.

## Läge 2026-10-08

D8 genomförd i 2b373ff: optionerna (abortSignal, addRandomSuffix, allowOverwrite, access private, del; adapterns maxDuration) belagda ur de installerade paketens typdefinitioner i exportens byggprov (`exportera.sdk_optioner`, SDK_KRAV) och ur `npm pack` av @vercel/blob 2.8.0 och @astrojs/vercel 11.0.11; verkligt kundrepobygge grönt (rapportkatalogens d3-d8-byggprov.txt). D9 återstår: huvudenas samspel med vercel.json mäts först i en verklig förhandsvisning (driftkoll.py), som kräver Vercel-åtkomst (steg 4 i backlogavstämningen).
