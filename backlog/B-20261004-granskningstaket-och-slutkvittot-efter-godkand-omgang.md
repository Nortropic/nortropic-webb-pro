---
id: B-20261004-granskningstaket-och-slutkvittot-efter-godkand-omgang
status: klar
kalla: bevakning
kallref: bygge 1–4 i sandlådat läge 2026-10-04; Codex R37 (kvittot ska knyta prov, granskning, stoppkrok och slutkod till samma dist)
skapad: 2026-10-04
prio: hog
commit: 00b2ef4
andrad: 2026-10-08T14:09Z
---
# Granskningstaket och slutkvittot: bygget ändras efter en godkänd omgång, taket förbrukas, och kvittot pekar på fel omgång

**Varför:** I alla fyra sandlådade helbyggen 2026-10-04 förbrukades granskningstaket (fem omgångar per körning) utan att det slutliga bygget blev granskat: sessionen ändrade bygget (eller underlaget, som ändrar metodhashen) efter en omgång, också efter en godkänd (bygge 1 omgång 5, bygge 4 omgång 4), och stoppvakten släppte sedan utan godkänd granskning med slutkod 1. kor.sh:s slutrad "Granskningen: GODKÄND (omgång 4)" i bygge 4 läste kunder/<slug>/granskning/GRANSKNING.json, som var omgång 4:s dom, fast omgång 5 på samma dist men ny metod underkände och det slutliga bygget (annan dist) aldrig granskades. Kvittot knyter alltså inte prov, granskning, stoppkrok och slutkod till samma dist (Codex R37).

**Förslag:** (1) Slutkvittot i kor.sh och STOPPVAKT.json anger granskningens dist bredvid provets och säger uttryckligen "granskad dist ≠ slutlig dist" när de skiljer sig; GRANSKNING.json i kundkatalogen uppdateras av arbetaren när en omgång blir klar, inte bara av drivaren som väntar, så att den senaste färdiga omgången gäller. (2) Skillens avslut: efter en godkänd omgång får bygget inte ändras utan att en ny omgång beställs, och de sista rättningarna ska göras innan granskningen beställs; stoppvakten bör säga att en ny omgång behövs i stället för att släppa vid taket när den senaste omgången gällde ett annat bygge. (3) Taket räknas per körning; överväg att en omgång som avbröts för att bygget ändrades inte räknas mot taket, eller att taket höjs när omgången före var godkänd, men behåll då ett separat hårt tak för tid eller försök (Codex R38). Att en session får avslutas vid taket är förenligt med slutkod 1; det får aldrig presenteras som en accepterad leverans.

**Klart när:** Kvittot pekar på det slutliga bygget (klart). STOPPVAKT.json bär granskningens dist; skillen säger att inga byggändringar görs efter en beställd granskning utan ny omgång; stoppvakten säger vid taket att en ny omgång behövs; avbrutna omgångar räknas inte mot taket (ett separat hårt tak). Verifieras av nästa sandlådade helbygge: samma dist för prov, granskning, stoppkrok och slutkod 0.

**Pågår (2026-10-04T18:27Z, efter Codex R38):** del 1 och 2 av förslaget byggda: varje omgång har ett enda slutligt utfall (UTFALL.json, atomiskt under lås, första skrivaren vinner); drivarens avbrott och arbetarens dom tävlar om det, så en avbruten omgång kan aldrig senare publicera en giltig dom (en sen dom läggs åt sidan som GRANSKNING-sen.json); arbetaren i tjänsten läser markören före start och vid publiceringen, oberoende av klientens livslängd; sammanfattningen i kunder/<slug>/granskning/GRANSKNING.json publiceras bara av publicera() ur giltiga omgångar och bär omgång, dist, metod och körning; svara() läser bara; korslut härleder domen för det slutliga bygget ur giltiga omgångar och säger uttryckligen när den granskade disten inte är den slutliga. Kvar: del 2:s skilltext (inga byggändringar efter beställd granskning utan ny omgång) och del 3 (taket).

**Vilande (2026-10-05):** Avstämt 2026-10-05: kvittot är klart (UTFALL.json per omgång, korslut härleder domen för det slutliga bygget, regressionsfall). Kvar (paketet före nästa helbygge): granskningens dist i STOPPVAKT.json, skilltexten, stoppvaktens besked vid taket och takräkningen utan avbrutna omgångar; verifieringen delas med sandlådeposten. Färdigkriteriet omskrivet i avstämningen; tidigare: "Ett sandlådat helbygge slutar med prov, granskning, stoppkrok och slutkod 0 på samma dist; kor.sh:s kvitto visar granskad dist = slutlig dist; ett regressionsfall visar att kvittot säger "annan dist" när de skiljer sig."

**Vilande (2026-10-05):** Implementerat (paketet före nästa helbygge): vid taket säger granskningen skälet (ett annat bygge, en annan metod eller ingen giltig omgång i körningen) och stoppvakten att en ny omgång behövs, med skälet i STOPPVAKT.json (tak_skal) bredvid granskningens dist; avbrutna omgångar räknas inte mot NWP_GRANSKNING_MAX men mot ett hårt tak (NWP_GRANSKNING_HART, 2 × taket); skillen säger att de sista rättningarna görs före beställningen. Prov för skälen och stoppvaktens besked. Kvar: verifiering i nästa sandlådade helbygge. (b7bf1c5)

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: commit 00b2ef4 (taket, tak_skal) och 1b7fb37 (avslutsreglerna); stoppvakt.py:194–210 granskning_dist_sha256/samma_dist, korslut.rapport_giltig/vald_granskning
