---
id: B-20261007-startkvittot-en-tjanst-vars-bilder-saknas-ger-en
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r102-om.md
fynd: GR-20261007-r102-om#K1
skapad: 2026-10-07
prio: normal
steg: main: kontroller/startkontroll.py, kontroller/rokprov/revision/prov_startkvitto.py
commit: a4d58aa
andrad: 2026-10-08T14:09Z
---
# Startkvittot: en tjänst vars bilder saknas ger en felrad, inte två

**Varför:** En tjänst vars alla bilder saknas på disken ger både "anrop, men tjänstens bilder saknas på disken" och "N bilder saknas på disken" (startkontroll.efter_research).

**Förslag:** Slå ihop raderna till en, med antalet.

**Klart när:** Ett prov visar en enda rad för fallet.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a4d58aa (om#K1): en felrad; prov_startkvitto 2b
