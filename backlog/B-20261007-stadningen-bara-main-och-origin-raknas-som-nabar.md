---
id: B-20261007-stadningen-bara-main-och-origin-raknas-som-nabar
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-E
skapad: 2026-10-07
prio: normal
steg: main: kontroller/stadning.py, kontroller/rokprov/revision/prov_stadning.py
---
# Städningen: bara main och origin räknas som nåbart i git, inte stashen och andra grenar

**Varför:** Stashen och andra grenar än main räknas som nåbara i git, så en arbetsyta vars filer bara finns i en stash eller en sidogren kan tas bort.

**Förslag:** Räkna bara objekt som nås från main och origin/main som nåbara.

**Klart när:** Ett prov med en fil som bara finns i en stash håller arbetsytan kvar.
