---
id: B-20261003-andringsuppdrag-med-bild-varje-blockerande-fynd
status: vilande
kalla: bevakning
kallref: Codex kartläggning av referenskällor och byggverktyg, 2026-10-03
skapad: 2026-10-03
prio: normal
andrad: 2026-10-05T06:55Z
---
# Ändringsuppdrag med bild: varje blockerande fynd får aktuell ruta, relevant referensbild och den konkreta avvikelsen

**Varför:** Codex 2026-10-03: fynden har sida, var, observation, rättning och acceptanskriterium i text, men byggaren får kritiken som text via stoppvakten och måste själv hitta stället och referensen igen. v0 bifogar bilden av det utpekade elementet vid ett ändringsuppdrag; Lovable stödjer utpekade element och annoteringar.

**Förslag:** kritik/SCHEMA-granskning.json får fälten bild (rutans fil ur provet) och referensbild per blockerande fynd; stoppvakten skriver kunder/<slug>/granskning/ANDRINGAR.md med en post per fynd: bild, referens, avvikelse (konkurrerande blickpunkter, fel beskärning, för tät text …), acceptanskriterium; byggaren läser den före rättningen. Mät antalet granskningsomgångar per bygge före och efter.

**Klart när:** Kod: varje blockerande fynd i GRANSKNING.json har aktuell ruta och referensbild; granska.py skriver ANDRINGAR.md med bilderna; stoppvaktens besked och SKILL.md pekar dit; rökprovet täcker det. Effekt (verifieras av helbyggen): omgångar per godkänt bygge före och efter.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord (kritik/SCHEMA-granskning.json saknar bildfält, stoppvakten lämnar kritiken som text). Ingår i paketet före nästa helbygge. Kodkriteriet skiljs från effektmåttet, som först helbyggen ger. Färdigkriteriet omskrivet i avstämningen; tidigare: "ANDRINGAR.md skrivs och läses (syns i körningsloggen); granskningsomgångarna per godkänt bygge sjunker eller rättningarna försämrar inte andra delar oftare än förut; rökprovet täcker filen."
