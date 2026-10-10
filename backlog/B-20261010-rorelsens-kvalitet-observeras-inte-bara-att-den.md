---
id: B-20261010-rorelsens-kvalitet-observeras-inte-bara-att-den
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F7
skapad: 2026-10-10
prio: normal
steg: referenser (inspektera.mjs), skisskritiken
---
# Rörelsens kvalitet observeras inte, bara att den finns

**Varför:** inspektera.mjs räknar requestAnimationFrame, canvas, video och Web Animations och tar en kort bildsekvens (2026-10-10). Ingen bedömer sekvensen: att rörelse finns är inte en bedömning av dess kvalitet, och ett tomt getAnimations betyder inte att sidan saknar rörelse.

**Förslag:** Låt planprövningen eller skisskritiken jämföra referensens sekvens med kandidatens när rörelse ingår i ett referensbidrag; annars står rörelsen som ej bedömd i redovisningen.

**Klart när:** Ett referensbidrag med rörelse som uppgift får en bedömning som pekar på sekvensbilderna, och redovisningen skiljer ej bedömd från bedömd rörelse.
