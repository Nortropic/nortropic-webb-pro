---
id: B-20261002-granskaren-satter-originalitetsbetyget-innan-hen
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · pbakaus/impeccable (egen innovation)
skapad: 2026-10-02
prio: normal
steg: 5.6 (den oberoende granskningen)
commit: a612831
andrad: 2026-10-03T01:47Z
---
# Granskaren sätter originalitetsbetyget innan hen läser stilrapporten och copykontrollen, så att mätningarna inte förankrar omdömet

**Varför:** Egen innovation ur impeccables critique.md (rad 8–10): designbedömningen avslutas innan detektorns fynd får nå den, eftersom en deterministisk mätning förankrar omdömet. Vår granskare får stilrapporten och copykontrollen i uppdraget från början (kritik/GRANSKARE.md rad 30–32) och sätter originalitetsbetyget med dem i hand; det kan göra betyget till en avläsning av varningslistan i stället för ett eget omdöme om sajten.

**Förslag:** kritik/GRANSKARE.md, 'Så granskar du': ett nytt steg efter 8: 'Sätt betygen på designkvalitet och originalitet innan du öppnar stilrapporten och copykontrollens rapport. Läs dem sedan och lägg bara till fynd; ändra inte ett betyg nedåt för något du inte själv såg.' Raden under 'Provets maskinella fynd' (rad 30–32) får tillägget 'läs dem sist, efter betygen'. Ingen ändring i granska.py.

**Klart när:** GRANSKARE.md har steget; nästa byggs GRANSKNING.md visar betyg satta före mätningarna (granskarens 'sett'-lista nämner stilrapporten efter skärmbilderna); rökprovet grönt.

## Protokoll 2026-10-03

**Metod.** Granskarförsöket (`kontroller/granskarforsok/`) med nya kopior från main 20c0157: arm A med dagens
kritik/GRANSKARE.md och arm forankring med samma text där stilrapporten och copykontrollen läses efter betygen på
designkvalitet och originalitet (nytt steg 9, tillägg under Provets maskinella fynd, stilrapportens mobilavsnitt
flyttat från steg 3 till steg 9). Tre granskningar per arm och bygge, en granskare per session, Opus 5.5 (1M), high.
Sonnet 5 dömde blint två gånger per granskning; bara eniga matchningar räknas (en dom gick om efter att ha nått sitt
turtak). 18 granskningar och 36 domar. Beslutsregel satt före resultatet: införs om omdömesträffarna inte blir mer än
0,3 färre per bygge och inga fler falska blockerande.

| Arm | n | Omdömesfel funna per bygge (av 7,0) | Alla fel (av 13,3) | Omdömesfel som blockerande | Falska blockerande | Blockerande per omgång | Originalitet, snitt | Designkvalitet, snitt | Tokens | Tid |
|---|---|---|---|---|---|---|---|---|---|---|
| A, dagens text | 9 | 4,1 | 10,2 | 2,8 | 0 | 4,7 | 6,4 | 6,8 | 3,8 M | 475 s |
| forankring | 9 | 4,3 | 10,4 | 3,0 | 0 | 4,2 | 6,6 | 7,1 | 4,6 M | 540 s |

Per bygge, omdömesfel: lulea-snickaren 3,7 → 4,3; paint-it-black-maleri 4,0 → 4,3; sundboms-el 4,7 → 4,3. Alla
granskningar i båda armarna landade på nivå 1 (detaljrättning), som ägarens "Ja, efter små ändringar" för alla tre.
Betygen blev något högre när mätningarna inte förankrade dem, vilket är avsikten; kostnaden är ungefär en femtedel
fler tokens och en minut längre per granskning.

**Beslut:** regeln håller; texten står i kritik/GRANSKARE.md.

**Klar (2026-10-03):** prövad i granskarförsöket (4,1 -> 4,3 omdömesfel, 0 falska); införd i GRANSKARE.md
