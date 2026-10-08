---
id: B-20261007-skisskritiken-gors-om-nar-en-kandidat-aterupptas
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r106.md
fynd: GR-20261007-r106#KAN-3
skapad: 2026-10-07
prio: normal
steg: main: kontroller/kandidater.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Skisskritiken görs om när en kandidat återupptas efter stopp

**Varför:** Vid återupptagning står skisskritik i statusen och SKISSKRITIK.json kvar från det avbrutna försöket, så det nya försöket granskas inte. Förbefintligt sedan skisskritikens kompetens (r103); funnet i GR-20261007-r106.

**Förslag:** Nollställ skisskritikens status när ett avbrutet försök görs om, och arkivera den gamla SKISSKRITIK.json i försökets katalog.

**Klart när:** Ett prov med stopp, återupptagning och nytt försök visar en ny skisskritik för det nya försöket.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (83d8855 Bind förberedelse, kritik, material och export till aktuell version); kunskap/skapandeflodet.md Återupptagning och material; prov_skisskritik stopp/omförsök
