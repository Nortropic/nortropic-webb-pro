---
id: B-20261001-copy-kontroll-i-prova-py-rapporterar-saknat-tele
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
---
# copy_kontroll i prova.py rapporterar saknat telefonnummer när numret kommer ur en datafil

**Varför:** Luleå-Snickaren: telefon, org.nr och adress kommer ur src/data/verksamhet.ts och står på alla sex byggda sidor, men prov/copy.md gav 8 fynd 'saknat element' eftersom kontrollen läser källfilerna.

**Förslag:** kontroller/prova.py: kör kravkontrollen (saknat element) mot den byggda HTML:en i dist/ i stället för mot src/; fras- och strukturfynden kan fortsatt läsa källan.
