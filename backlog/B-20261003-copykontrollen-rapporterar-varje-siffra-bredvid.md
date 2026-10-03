---
id: B-20261003-copykontrollen-rapporterar-varje-siffra-bredvid
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Jack Roberts, Opus 5.5 Just 10X'd Claude Design (YouTube HOXrLsVqinY) + ItsssssJack/SlopMonster
skapad: 2026-10-03
prio: normal
steg: steg 4 (innehåll före form), kontroller/copy_kontroll.py
---
# Copykontrollen rapporterar varje siffra bredvid kunder, år, jobb, omdömen och procent med rad, så att det redaktionella passet kan kräva kvitto

**Varför:** Videon dömdes nej, men SlopMonsters enda regel utan motsvarighet hos oss är att lista tal intill substantiv som kunder och projekt som möjligt påhittat bevis, med motiveringen att en påhittad siffra är det enda felet utan återväg. Vår copykontroll har fraser och strukturer men ingen rad för tal, och bygg-sajt förbjuder påhittade siffror utan att något verktyg visar var de står.

**Förslag:** kontroller/copy_kontroll.py: en ny fyndtyp 'siffra' som rapporterar varje tal (inklusive +, procent och 'över') inom fem ord från kunder, uppdrag, jobb, projekt, år, omdömen, stjärnor, procent eller timmar, med riktningen 'kvitto i VERKSAMHET.json, omdömessidan eller källfilen; annars stryk'. En rad i tabellen i kunskap/copy-kontroll.md. Ingen poäng, ingen grind, som övriga fynd. Egna ord, ingen kod ur SlopMonster.

**Klart när:** copy_kontroll.py på en INNEHALL.md med 'över 500 nöjda kunder' och 'sedan 2012' ger två fynd av typen siffra med rad; kontroller/rokprov.sh grönt; raden finns i copy-kontroll.md
