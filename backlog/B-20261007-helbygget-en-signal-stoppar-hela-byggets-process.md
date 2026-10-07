---
id: B-20261007-helbygget-en-signal-stoppar-hela-byggets-process
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#BÖR-2
skapad: 2026-10-07
prio: hog
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
---
# Helbygget: en signal stoppar hela byggets processgrupp

**Varför:** En signal under bygget stoppar bara claudes pid. Attrappens barnprocess levde kvar i 4 av 6 fall: TERM, INT och HUP till kor.sh, och INT till gruppen (Ctrl-C). Kravet att ingen process blir kvar uppfylls inte.

**Förslag:** Bygget i en egen processgrupp, signalen till hela gruppen och KILL efter en frist.

**Klart när:** Ingen process blir kvar i något av de sex fallen.
