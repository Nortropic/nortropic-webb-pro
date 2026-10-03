---
id: B-20261003-referensoverforingen-referensbeslutet-pekar-ut-s
status: klar
kalla: bevakning
kallref: Codex kartläggning av referenskällor och byggverktyg, 2026-10-03
skapad: 2026-10-03
prio: hog
commit: 53c034d
andrad: 2026-10-03T22:09Z
---
# Referensöverföringen: referensbeslutet pekar ut sektion och tillstånd, och just de bilderna följer med till ateljén och granskaren

**Varför:** Codex 2026-10-03, verifierat i koden: atelje.underlag_rader och granska.referensbilder väljer bara vy-*-forsta.png, sorterade på sökväg och kapade (16, panelen 8), fast inspektera.mjs redan skriver rutorna (vy-1440-ruta-01.png finns under underlag/<slug>/referenser/). REFERENSER.md säger varför en referens är stark men pekar inte på bilden. Det underlag som faktiskt tilldelas skapare och granskare är alltså sidornas toppar, trots att referensjakten vill jämföra rytm, sektioner och undersidor.

**Förslag:** REFERENSER.md får per referens en strukturerad rad (eller REFERENSER.json): roll, vad som ska jämföras (tjänstesektion, bildserie, mobilmeny, prislista, sidfot …), bildfil (ruta-NN eller tillstånd) och jämförelsefrågan. atelje.py och granska.py läser raderna och skickar just de bilderna med frågan, prioriterade efter relevans när taket nås; första vyn kvar som reserv när raden saknas. Bygg-sajt steg 3 beskriver raden. Land-book, Mobbin (flöden, dimension 7) och Refero läggs till som sökingångar i kunskap/referensjakt.md bredvid Awwwards och Siteinspire.

**Klart när:** En referens vald för en tjänstesektion följer med som just den rutan i domarnas och granskarnas uppdrag (syns i PROMPT.txt); ett rökprovsfall med REFERENSER-rad och rutor; referensjakt.md har de nya sökingångarna med roll.

**Klar (2026-10-03):** kontroller/referensval.py; Bildval-raden i REFERENSER.md (bygg-skillen steg 3); granska och atelje skickar utpekad ruta med fråga; referensjakt.md med Land-book, Mobbin, Refero; rökprovsfall i revisionens block referensöverföringen
