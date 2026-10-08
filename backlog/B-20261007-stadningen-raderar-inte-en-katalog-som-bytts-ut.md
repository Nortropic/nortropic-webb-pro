---
id: B-20261007-stadningen-raderar-inte-en-katalog-som-bytts-ut
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-C
skapad: 2026-10-07
prio: normal
steg: main: kontroller/stadning.py, kontroller/rokprov/revision/prov_stadning.py
commit: 9852f0a
andrad: 2026-10-08T21:28Z
---
# Städningen raderar inte en katalog som bytts ut mellan prövningen och raderingen

**Varför:** Byts en katalog mot en annan mellan prövningen och raderingen raderas den inbytta (tid från kontroll till användning).

**Förslag:** Öppna katalogen en gång, pröva och radera relativt till samma filbeskrivare, och jämför inod och enhet före raderingen.

**Klart när:** Ett prov som byter katalogen mitt i ger att ingenting raderas.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08: identiteten (st_dev, st_ino) sparas vid prövningen och jämförs i ta_bort_trad före rmtree; provet byter en tempkatalog, en arbetsyta och en kopia mitt i och kräver att inget raderas; rött mot basen, grönt efter; fem mutanter fälls. Inte verifierad.
