---
id: B-20261007-kundvakten-namnprovningen-soker-personnamn-bara
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r102-om.md
fynd: GR-20261007-r102-om#B1
skapad: 2026-10-07
prio: hog
steg: main: kontroller/kundvakt.py, kontroller/rokprov/revision/prov_startkvitto.py
---
# Kundvakten: namnprövningen söker personnamn bara där personer står

**Varför:** namnpar gör varje par av ord med stor bokstav i briefen och sidtexten till ett personnamn. I granskarens syntetiska korpus stoppades 7 av 10 generiska frågor: designmönster, typsnittsnamn och namngivna förlagor ur briefens designriktning. Felet går åt det säkra hållet, men referensarbetet blir sämre, och ägarens regel säger att generiska researchfrågor ska gå.

**Förslag:** Sök namnpar bara i personrader (Ägare:, Kontakt), i attribution efter tankstreck eller citat och i omdömen. Hoppa över briefens designriktning (§7) och typsnittsnamn. Lägg falsklarmen som fall i prov_startkvitto.py.

**Klart när:** Granskarens tio generiska frågor släpps, och hela namn i personrader och omdömen stoppas fortfarande. Görs före nästa designkörning.
