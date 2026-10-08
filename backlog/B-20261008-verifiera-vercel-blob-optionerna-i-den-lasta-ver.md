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
