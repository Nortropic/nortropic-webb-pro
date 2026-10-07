---
id: B-20261007-ett-fynd-som-anmals-igen-efter-verifiering-lamna
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r97-om.md
fynd: GR-20261007-r97-om#BÖR-1
skapad: 2026-10-07
prio: normal
steg: kontroller/backlog.py ny; backlog/README.md
commit: c4e0e2f
andrad: 2026-10-07T05:25Z
---
# Ett fynd som anmäls igen efter verifiering lämnar inget spår

**Varför:** Efter verifiera ger ny --fynd samma id med slutkod 0, och posten står kvar som "klar, verifierad" utan not; README och skillen säger inte vad sessionen ska göra.

**Förslag:** En mening i backlog/README.md och skillen: öppna posten igen med status <id> vilande --not "<rapport>: fyndet består" (det tar bort verifieringen); eller låt ny göra det för klara poster men inte för avvisade.

**Klart när:** Ett fynd som består efter verifiering syns som öppet igen med rapporten i en not, prövat i prov_dokumentation.py.

**Klar (2026-10-07):** ny --fynd från en senare rapport öppnar en klar post igen (vilande, not om rapporten, verifieringen borttagen); avvisade och ersatta poster och rapporten som hittade fyndet öppnar den inte. Prövat i prov_dokumentation.py. Inte verifierad: en senare granskning gör det.
