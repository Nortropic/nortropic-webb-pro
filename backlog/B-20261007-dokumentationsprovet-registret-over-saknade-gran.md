---
id: B-20261007-dokumentationsprovet-registret-over-saknade-gran
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r99-om.md
fynd: GR-20261007-r99-om#KAN-3
skapad: 2026-10-07
prio: normal
steg: main: kontroller/rokprov/revision/prov_dokumentationsvy.py
---
# Dokumentationsprovet: registret över saknade granskningar läses, inte hårdkodas

**Varför:** _saknade_i_repot i prov_dokumentationsvy.py listar registrets id:n. En ny kodhänvisning till en oregistrerad runda till och med r99, också från en parallell gren, gör rökprovet rött tills listan ändras.

**Förslag:** Läs listan ur samma källa som vyn (BESLUT.md, Återstår, och förteckningen), så att provet prövar regeln och inte en avskrift.

**Klart när:** En ny hänvisning till en registrerad runda håller provet grönt, och en till en oregistrerad gör det rött med rundans namn.
