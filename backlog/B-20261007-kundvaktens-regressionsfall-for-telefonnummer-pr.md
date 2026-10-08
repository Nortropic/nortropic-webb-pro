---
id: B-20261007-kundvaktens-regressionsfall-for-telefonnummer-pr
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r102-om.md
fynd: GR-20261007-r102-om#B3
skapad: 2026-10-07
prio: normal
steg: main: kontroller/rokprov/revision/prov_revision.py
commit: a4d58aa
andrad: 2026-10-08T14:09Z
---
# Kundvaktens regressionsfall för telefonnummer prövar numret igen

**Varför:** Två fall i prov_revision.py går till search_screens utan mode. Lägesregeln stoppar dem nu innan numret prövas. Utan regeln om telefonnumrets sex sista siffror är prov_revision.py ändå grönt.

**Förslag:** Ge de två fallen 'mode': 'standard'.

**Klart när:** Mutationen som tar bort regeln om de sex sista siffrorna fälls av prov_revision.py.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a4d58aa (om#B3): prov_revision två regressionsfall mode standard
