---
id: B-20261010-materialkon-verkstaller-inget-utan-ett-staende-k
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F4
skapad: 2026-10-10
prio: normal
steg: materialet (material.py --ko)
---
# Materialkön verkställer inget utan ett stående kostnadsmandat

**Varför:** --ko lägger beställningar i kön med uppdragshash och kostnadsuppskattning men verkställer dem inte: varje verkligt anrop kräver i dag ett uttryckligt kostnadsmandat per körning (kunskap/materialtransport.md). En automatisk kö behöver ett stående mandat som inte finns.

**Förslag:** Ägaren anger om ett stående mandat ska finnas (tak per kund och dygn, vilka leverantörer, vem som får starta). Vid ja verkställer en betrodd arbetare kön inom taket och stoppar vid taket med kvitto.

**Klart när:** Beslutet står i BESLUT.md; vid ja verkställer kön inom taket med kvitto per beställning och prov för taket, vid nej säger materialtransport.md att kön bara förbereder.
