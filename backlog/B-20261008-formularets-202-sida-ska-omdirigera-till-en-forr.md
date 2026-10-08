---
id: B-20261008-formularets-202-sida-ska-omdirigera-till-en-forr
status: vilande
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#D1
skapad: 2026-10-08
prio: normal
steg: main: mall/leverans/forfragan.js, kontroller/exportera.py, kunskap/forfragan.md
---
# Formulärets 202-sida ska omdirigera till en förrenderad sida i stället för att svara på POST-adressen

**Varför:** Mottagen-men-ej-aviserad (202) renderas direkt på /api/forfragan/. En omladdning eller bakåt/framåt i webbläsaren ger "skicka formuläret igen?" och ett nytt inskick, fast sidan säger att det inte behövs. Reproducerat i Node (prov.mjs mejlfel) i GR-20261008-r117-claude#D1.

**Förslag:** Svara 303 till en förrenderad /mottagen/ (mall + exportera.py, som fel.astro) med samma text, och ge besökaren en referens (tid) att ange vid kontakt. Uppdatera forfragan.md, README, byggstandard 6.6, prov_formularfel och driftkoll.

**Klart när:** Ett 202-utfall slutar i GET på en statisk sida; omladdning skickar inget; proven och dokumenten säger samma sak.
