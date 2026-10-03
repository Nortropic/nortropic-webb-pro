---
id: B-20261003-skriv-om-kunskap-lansering-md-for-var-stack-den
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Mikey No Code, The Easiest Way to Build & Host a Website with Claude Code (YouTube 8F953MNwqII)
skapad: 2026-10-03
prio: normal
steg: lanseringen (byggstandarden fas L, kunskap/lansering.md)
commit: da5b58d
andrad: 2026-10-03T09:50Z
---
# Skriv om kunskap/lansering.md för vår stack: den pekar på verktyg som inte finns i repot, och Vercel-steget som byggstandarden hänvisar till saknar egen text

**Varför:** Videons enda poäng är att tutorials slutar vid localhost, och vårt läge är detsamma: inget bygge har lanserats och lansering.md är ärvd från Digitala. Den hänvisar till verktyg/lansering.py, verktyg/sokkonsol.py och MANDAT.md som inte finns här (kontrollerat 2026-10-03), medan byggstandarden 1.4, 4.5, 4.6 och 8.1 pekar på ett Vercel-steg som ingen fil beskriver. Ägaren har sagt 'då väntar vi med det' om Vercel (BESLUT.md rad 102), så posten vilar tills en kund ska ut.

**Förslag:** kunskap/lansering.md: ersätt kommandona mot verktyg/lansering.py och verktyg/sokkonsol.py med det som faktiskt finns i kontroller/ (arkivera.mjs finns) eller skriv 'människa' där inget verktyg finns; lägg till ett avsnitt 'Vercel-steget' som svarar på byggstandardens L-punkter 1.4, 4.5, 4.6 och 8.1 (förhandsvisning per gren, noindex som svarshuvud, cache, HSTS, kanonisk värd, återgång till föregående driftsättning); DNS-rådet står kvar: bara webbposterna hos nuvarande DNS-värd, ingen namnserverflytt, ingen session ändrar DNS.

**Klart när:** lansering.md nämner inga filer som saknas i repot (grep efter verktyg/ och MANDAT.md ger noll träffar), och varje L-punkt i byggstandarden som säger Vercel-steget pekar på ett avsnitt i lansering.md.

**Klar (2026-10-03):** lansering.md utan saknade filer, med Vercel-steget; inget driftsatt
