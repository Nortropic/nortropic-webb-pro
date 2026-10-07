---
id: B-20261007-kundvakten-namnprovningens-luckor-tapps-och-fall
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r102-om.md
fynd: GR-20261007-r102-om#B2
skapad: 2026-10-07
prio: hog
steg: main: kontroller/kundvakt.py, kontroller/rokprov/revision/prov_startkvitto.py, kunskap/metodkarta.md
---
# Kundvakten: namnprövningens luckor täpps, och fall 10 får verkliga datas form

**Varför:** Det här släpps igenom: bara efternamnet eller bara förnamnet, namn i en markdownlänk, två av tre namn, namn i versaler eller gemener, bokstäver utanför åäöéü, hopskrivna bindestrecksnamn (ett fel i hopfogningen) och namn som bara står i Bokadirekts omdömes- och tjänstefiler, som inte läses. Fall 10 lägger personfält i VERKSAMHET.json som schemat avvisar, så skyddet för ett efternamn ensamt finns bara i provet. Felscenario: en skapare skriver ett efternamn ur briefen i en sökning, och frågan når Mobbin.

**Förslag:** Gör fixturen giltig mot schemat, läs Bokadirekts filer och ta bokstäverna med isupper och isalpha. Skala bort länkarnas markdown och rätta hopfogningen. Väg efternamnen mot B1. Kundvaktens beskrivning och metodkartan ska säga vad som faktiskt prövas.

**Klart när:** Varje lucka har ett fall som stoppas, med fixturer i verkliga datas form, och B1:s generiska frågor släpps fortfarande.
