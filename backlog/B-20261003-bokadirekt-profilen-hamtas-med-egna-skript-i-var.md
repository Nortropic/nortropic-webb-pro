---
id: B-20261003-bokadirekt-profilen-hamtas-med-egna-skript-i-var
status: klar
kalla: bygge
kallref: kunder/salong-kreativ/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 1
commit: ff49398
andrad: 2026-10-03T09:50Z
---
# Bokadirekt-profilen hämtas med egna skript i varje bygge

**Varför:** Salong Kreativ bokas via Bokadirekt, där prislistan (36 behandlingar, mästare- och elevpris), personalen, avbokningsvillkoret och 2 781 betyg finns. Den egna sajten hade nästan inget. Fyra skript i underlag/salong-kreativ/skript/ (bokadirekt.py, bokadirekt_state.py, bokadirekt_tjanster.py, omdomen.py) läste window.__PRELOADED_STATE__ och Bokadirekts API /api/places/getReviews/<id>. Inget av det är knutet till salongen.

**Förslag:** Ny kontroll kontroller/hamta_bokadirekt.py <slug> <bokadirekt-url>: skriver kalla/extern/bokadirekt-state.json, bokadirekt-tjanster.txt (pris och tid per prislista och vem som gör vad) och bokadirekt-omdomen.txt (alla omdömen med text, datum, betyg, namn, frisör). Nämn den i bygg-sajt steg 1 för verksamheter som bokas via Bokadirekt.

**Klar (2026-10-03):** kontroller/hamta_bokadirekt.py
