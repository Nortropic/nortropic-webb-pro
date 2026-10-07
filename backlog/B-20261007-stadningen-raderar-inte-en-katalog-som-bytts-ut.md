---
id: B-20261007-stadningen-raderar-inte-en-katalog-som-bytts-ut
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-C
skapad: 2026-10-07
prio: normal
steg: main: kontroller/stadning.py, kontroller/rokprov/revision/prov_stadning.py
---
# Städningen raderar inte en katalog som bytts ut mellan prövningen och raderingen

**Varför:** Byts en katalog mot en annan mellan prövningen och raderingen raderas den inbytta (tid från kontroll till användning).

**Förslag:** Öppna katalogen en gång, pröva och radera relativt till samma filbeskrivare, och jämför inod och enhet före raderingen.

**Klart när:** Ett prov som byter katalogen mitt i ger att ingenting raderas.
