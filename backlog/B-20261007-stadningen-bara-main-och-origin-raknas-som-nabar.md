---
id: B-20261007-stadningen-bara-main-och-origin-raknas-som-nabar
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-E
skapad: 2026-10-07
prio: normal
steg: main: kontroller/stadning.py, kontroller/rokprov/revision/prov_stadning.py
commit: c084393
andrad: 2026-10-08T14:09Z
---
# Städningen: bara main och origin räknas som nåbart i git, inte stashen och andra grenar

**Varför:** Stashen och andra grenar än main räknas som nåbara i git, så en arbetsyta vars filer bara finns i en stash eller en sidogren kan tas bort.

**Förslag:** Räkna bara objekt som nås från main och origin/main som nåbara.

**Klart när:** Ett prov med en fil som bara finns i en stash håller arbetsytan kvar.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: c084393 (städningens villkor efter GR-20261007-r100); prov_stadning Ö1 (unik ändring bara i stash@{1} hålls kvar, rad 373–378, 605)
