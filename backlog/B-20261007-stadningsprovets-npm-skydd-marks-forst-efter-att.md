---
id: B-20261007-stadningsprovets-npm-skydd-marks-forst-efter-att
status: vilande
kalla: granskning
kallref: granskningar/GR-20261006-r98.md
fynd: GR-20261006-r98#KAN-B
skapad: 2026-10-07
prio: hog
steg: kontroller/rokprov/revision/prov_stadning.py
---
# Städningsprovets npm-skydd märks först efter att npm körts, och NPM_CONFIG_CACHE med versaler tas inte bort

**Varför:** NS1, NS2 och NS6 blir röda först efter att npm cache clean --force körts mot miljöns cache, i en vanlig körning ~/.npm; med NPM_CONFIG_CACHE i versaler i den yttre miljön rensar npm den cachen.

**Förslag:** Pröva varje riktig npm innan den startar (en npm-vakt först i PATH eller en assert att cachen ligger i provets TMP), och ta bort båda skrivsätten.

**Klart när:** NS1, NS2 och NS6 blir röda innan någon npm körs, och ett fall med NPM_CONFIG_CACHE i versaler är grönt utan att ~/.npm rörs.
