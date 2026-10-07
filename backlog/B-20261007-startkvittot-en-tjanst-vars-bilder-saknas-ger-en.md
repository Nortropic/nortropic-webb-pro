---
id: B-20261007-startkvittot-en-tjanst-vars-bilder-saknas-ger-en
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r102-om.md
fynd: GR-20261007-r102-om#K1
skapad: 2026-10-07
prio: normal
steg: main: kontroller/startkontroll.py, kontroller/rokprov/revision/prov_startkvitto.py
---
# Startkvittot: en tjänst vars bilder saknas ger en felrad, inte två

**Varför:** En tjänst vars alla bilder saknas på disken ger både "anrop, men tjänstens bilder saknas på disken" och "N bilder saknas på disken" (startkontroll.efter_research).

**Förslag:** Slå ihop raderna till en, med antalet.

**Klart när:** Ett prov visar en enda rad för fallet.
