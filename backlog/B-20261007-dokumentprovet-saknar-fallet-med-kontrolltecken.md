---
id: B-20261007-dokumentprovet-saknar-fallet-med-kontrolltecken
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r97-om.md
fynd: GR-20261007-r97-om#KAN-1
skapad: 2026-10-07
prio: normal
steg: kontroller/rokprov/revision/prov_dokumentation.py
andrad: 2026-10-08T14:09Z
---
# Dokumentprovet saknar fallet med kontrolltecken i NWP_KORNING

**Varför:** Mutationen G03 överlever: koden avvisar redan värdet, men inget prov håller det.

**Förslag:** Ett fall som sätter NWP_KORNING med radbrytning och kräver att posten inte skrivs.

**Klart när:** G03 blir röd.

**Vilande (2026-10-08):** Backlogavstämningen 2026-10-08: bärare för B-20261007-dokumentprovet-provar-ateranvandningen-av-fyndet, B-20261007-dokumentprovet-ordningen-mellan-tva-rapporter-sa; deras klartkriterier ingår här.
