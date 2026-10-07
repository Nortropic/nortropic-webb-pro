---
id: B-20261007-skisskritiken-gors-om-nar-en-kandidat-aterupptas
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r106.md
fynd: GR-20261007-r106#KAN-3
skapad: 2026-10-07
prio: normal
steg: main: kontroller/kandidater.py
---
# Skisskritiken görs om när en kandidat återupptas efter stopp

**Varför:** Vid återupptagning står skisskritik i statusen och SKISSKRITIK.json kvar från det avbrutna försöket, så det nya försöket granskas inte. Förbefintligt sedan skisskritikens kompetens (r103); funnet i GR-20261007-r106.

**Förslag:** Nollställ skisskritikens status när ett avbrutet försök görs om, och arkivera den gamla SKISSKRITIK.json i försökets katalog.

**Klart när:** Ett prov med stopp, återupptagning och nytt försök visar en ny skisskritik för det nya försöket.
