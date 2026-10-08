---
id: B-20261003-andringsuppdrag-med-bild-varje-blockerande-fynd
status: klar
kalla: bevakning
kallref: Codex kartläggning av referenskällor och byggverktyg, 2026-10-03
skapad: 2026-10-03
prio: normal
commit: 1b7fb37
andrad: 2026-10-08T14:09Z
---
# Ändringsuppdrag med bild: varje blockerande fynd får aktuell ruta, relevant referensbild och den konkreta avvikelsen

**Varför:** Codex 2026-10-03: fynden har sida, var, observation, rättning och acceptanskriterium i text, men byggaren får kritiken som text via stoppvakten och måste själv hitta stället och referensen igen. v0 bifogar bilden av det utpekade elementet vid ett ändringsuppdrag; Lovable stödjer utpekade element och annoteringar.

**Förslag:** kritik/SCHEMA-granskning.json får fälten bild (rutans fil ur provet) och referensbild per blockerande fynd; stoppvakten skriver kunder/<slug>/granskning/ANDRINGAR.md med en post per fynd: bild, referens, avvikelse (konkurrerande blickpunkter, fel beskärning, för tät text …), acceptanskriterium; byggaren läser den före rättningen. Mät antalet granskningsomgångar per bygge före och efter.

**Klart när:** Kod: varje blockerande fynd i GRANSKNING.json har aktuell ruta och referensbild; granska.py skriver ANDRINGAR.md med bilderna; stoppvaktens besked och SKILL.md pekar dit; rökprovet täcker det. Effekt (verifieras av helbyggen): omgångar per godkänt bygge före och efter.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord (kritik/SCHEMA-granskning.json saknar bildfält, stoppvakten lämnar kritiken som text). Ingår i paketet före nästa helbygge. Kodkriteriet skiljs från effektmåttet, som först helbyggen ger. Färdigkriteriet omskrivet i avstämningen; tidigare: "ANDRINGAR.md skrivs och läses (syns i körningsloggen); granskningsomgångarna per godkänt bygge sjunker eller rättningarna försämrar inte andra delar oftare än förut; rökprovet täcker filen."

**Vilande (2026-10-05):** Kodkriteriet uppfyllt (paketet före nästa helbygge): schemat kräver bild och referensbild per blockerande fynd, granska.py skriver ANDRINGAR.md per omgång och i granskningskatalogen (saknade vägar sägs), stoppvaktens besked och SKILL.md steg 5.6 pekar dit. Bildvägarna stannar i repot; granskarens egna tillståndsbilder i arbetskatalogen kopieras in i omgången, och ett fel i ändringsuppdragen fäller aldrig domen. Prov för ANDRINGAR.md, vägar utanför repot, symlänkar och arbetskatalogen. Kvar: effektmåttet (omgångar per godkänt bygge) i helbyggen. (b7bf1c5)

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: commit 1b7fb37; kontroller/granska.py:777 (ANDRINGAR.md med rutan och referensbilden), :1108 skrivs per omgång
