---
id: B-20261003-korbar-designgrund-ur-den-vinnande-riktningen-to
status: ersatt
kalla: bevakning
kallref: Codex kartläggning av referenskällor och byggverktyg, 2026-10-03
skapad: 2026-10-03
prio: hog
andrad: 2026-10-05T06:55Z
---
# Körbar designgrund ur den vinnande riktningen: tokens och första vyn in i bygget i stället för omtolkning via KONCEPT.md

**Varför:** Codex 2026-10-03: ateljévägen i bygg-sajt steg 5.1 säger läs vinnaren och skriv specifikationen i KONCEPT.md; formgivningen tolkas om på vägen och slutbygget kan tappa det som gjorde riktningen bra. v0 och Lovable förankrar bygget i verkliga komponenter och tokens; Relume applicerar en stil över hela sajten.

**Precisering (Codex 2026-10-03):** färger, typsnitt och avstånd räcker inte; komposition, bildbeskärning, innehållshierarki och beteendet mellan skärmstorlekar ska överleva överlämningen. Bygg vidare på vinnarens faktiska komponenter och jämför slutresultatets rendering med vinnarens; tokenjämförelsen stödjer det men bevisar inte att uttrycket bevarats.

**Förslag:** atelje.py sparar vinnarens stilvariabler som src/styles/riktning.css (färger med roll, typsnitt, typografisk skala, radie, avstånd) och första vyn som komponent src/components/atelje/Forstavy.astro; bygg-sajt steg 5 bygger vidare på dem och får bara ersätta en token med skäl i KONCEPT.md; stilrapporten jämför byggets tokens med riktningens och rapporterar avvikelser. Vinnarens renderade bilder följer med till granskaren (posten om prototyper bortom första vyn).

**Klart när:** En ändring av typografisk skala, bildbehandling eller knappstil slår igenom sammanhängande; stilrapporten visar tokenavvikelser; granskaren jämför slutbygget med vinnarens bilder och tokens; rökprovet täcker tokenjämförelsen.

**Ersatt (2026-10-05):** Sammanförd i B-20261004-designkontrakt-design-md-extraktion-och-refero-styles (avstämningen 2026-10-05): vinnarens kod återanvänds, DESIGN.md genererar variablerna, provet mäter avvikelser och jämför pixlar, granskaren jämför (6c8c90f, 915b85e). Kvar där: verifiering i ett helbygge.
