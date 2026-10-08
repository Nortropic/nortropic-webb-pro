---
id: B-20261007-dokumentprovet-ordningen-mellan-tva-rapporter-sa
status: ersatt
kalla: granskning
kallref: granskningar/GR-20261007-r99-om.md
fynd: GR-20261007-r99-om#KAN-2
skapad: 2026-10-07
prio: normal
steg: main: kontroller/rokprov/revision/prov_dokumentation.py
andrad: 2026-10-08T14:09Z
---
# Dokumentprovet: ordningen mellan två rapporter samma dag prövas

**Varför:** Mutationen N08 (_tidpunkt med bara datumet) överlever: prov_dokumentation.py prövar ingen ordning inom samma dag, som r97 → r97-om eller r99 → r100. Granskarens bl_prov2.py prövar den, och koden fungerar.

**Förslag:** Ett fall i prov_dokumentation.py med två rapporter samma dag, efter granskarens bl_prov2.py.

**Klart när:** N08 blir röd.

**Ersatt (2026-10-08):** Backlogavstämningen 2026-10-08: sammanförd i B-20261007-dokumentprovet-saknar-fallet-med-kontrolltecken (tre överlevande mutationer i samma prov (G03, G07, N08))
