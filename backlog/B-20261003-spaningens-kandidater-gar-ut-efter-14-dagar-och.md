---
id: B-20261003-spaningens-kandidater-gar-ut-efter-14-dagar-och
status: ersatt
kalla: bevakning
kallref: kirurgen/spaning/KANDIDATER.json 2026-10-03 (taket 200 nått)
skapad: 2026-10-03
prio: hog
steg: spaningen, dashboarden
andrad: 2026-10-08T14:09Z
---
# Spaningens kandidater går ut efter 14 dagar, och dashboarden visar Nytt sedan i går, de bästa per område och träffsäkerhet per källa

**Varför:** Med daglig spaning ligger obehandlade kandidater kvar som ny i 90 dagar; listan nådde taket 200 redan 2026-10-03. Dashboarden visar 20 i en lista utan område, och ingen ser vilka källor som ger intag som blir ändringar.

**Förslag:** Efter A/B-kedjan. kontroller/spana.py: en kandidat med status ny som inte hanterats på 14 dagar blir utgången. Dashboardens spaningsvy: överst Nytt sedan i går, sedan de två bästa per område, sedan Svarar mot dina domar; en ruta Träffsäkerhet per källa ur intagens not (Hittad av spanaren … via <källa>) och REGISTER.md:s dom och Utfall: skickade, ta in eller prova, ändringar gjorda. Vikterna ändras efter beslut, inte automatiskt.

**Klart när:** KANDIDATER.json har inga kandidater med status ny äldre än 14 dagar, spaningsvyn har de tre delarna och träffsäkerheten, och rokprov.sh är grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord, beroende av poängposten (område-fältet). Utgången ska vara en status, inte dagens tysta bortfall vid 90 dagar; belägget är ett prov med fixtur, eftersom kriteriet håller tomt i dag.

**Ersatt (2026-10-08):** Backlogavstämningen 2026-10-08: sammanförd i B-20261003-spanaren-poangsatter-per-omrade-titel-2-negativa (utgången efter 14 dagar finns (spana.py:298, 5252e27); dashboardens delar och träffsäkerhet per källa tas i bäraren)
