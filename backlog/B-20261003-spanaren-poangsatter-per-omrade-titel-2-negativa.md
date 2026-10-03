---
id: B-20261003-spanaren-poangsatter-per-omrade-titel-2-negativa
status: vilande
kalla: bevakning
kallref: kirurgen/spaning/korning.log 2026-10-02 och 2026-10-03
skapad: 2026-10-03
prio: hog
steg: spaningen (kirurgens intag)
---
# Spanaren poängsätter per område: titel ×2, negativa ord, claude code eller skill räcker inte ensamt, och ord ur ägarens domar

**Varför:** Första körningen 2026-10-02 hade brus överst (en schackskill, en spelstudio, en kylskåpsmagnet, en Whiteboard-IDE) eftersom claude code, skill och mcp ger höga poäng i alla sammanhang. Ordlistan i spana.py är fast och vet inget om LARDOMAR.md eller grupperingen. Källtabellen har sedan 76d846f kolumnen område.

**Förslag:** Efter A/B-kedjan (kontroller/ kräver rökprovet). kontroller/spana.py: läs kolumn 6 (område) och märk kandidaten; termer per område på svenska och engelska; titelträffar väger dubbelt; negativa ord (spel, krypto, jobb, schack, iOS, Kubernetes …); claude code, skill, mcp och agent räknas bara tillsammans med en träff i ett av våra områden eller från en källa med vikt 1,5. Domstyrda ord vid varje körning: senaste svaren på Om du fick ändra en sak i LARDOMAR.md, grupperingens största kategorier, de standardpunkter som oftast faller i kunder/*/prov/standard.json och granskarnas blockerande fynd, mappade till sökord (belägg → fact-checking, claims; 7.4 → NAP, Google Business Profile; mobilmeny → navigation, mobile menu); träff ger påslag och märket svarar mot <dom>. GitHub-källor var tredje dygn; Hacker News från 50 poäng; rensa() kapar vid ett ord med … i stället för mitt i ett ord.

**Klart när:** En torrkörning har inget av brusexemplen (schack, spelstudio, kylskåpsmagnet, Whiteboard) bland de 20 översta, varje kandidat har ett område, och rokprov.sh är grönt med prov för negativa ord, områdesmärkning och domstyrda ord.
