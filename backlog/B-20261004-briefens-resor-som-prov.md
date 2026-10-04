---
id: B-20261004-briefens-resor-som-prov
status: klar
kalla: bevakning
kallref: Codex helhetsbedömning 2026-10-04 punkt 6; rekommenderad ordning 4
skapad: 2026-10-04
prio: mellan
commit: 8a13786
andrad: 2026-10-04T23:25Z
---
# Briefens viktigaste resor blir uttryckliga prov: startläge, handling, synligt resultat, inmatningsfel och återhämtning, nivå

**Varför:** Formulärprovet verifierar inskick utan JavaScript mot en lokal demomottagare, JavaScript-utforskningen blockerar inte godkännande och prelaunch är information (prova.py:440): en tydlig demoomfattning som inte täcker kundresan. För bokning skiljer vi inte mellan att länken öppnas och att rätt tjänst går att boka; för kontakt inte mellan formulärets godkännande och mottagen förfrågan.

**Förslag:** Briefen listar de viktigaste uppgifterna; varje uppgift blir ett prov i `underlag/<slug>/RESOR.json` med startläge och avsedd handling, förväntat synligt resultat, relevant inmatningsfel och återhämtning, kontrollerat serverfel eller avbrutet flöde där det behövs, och nivå (lokalt prov, testintegration, verklig leverans). `kontroller/webblasare/resor.mjs` kör dem i Chromium på det slutliga bygget och provet redovisar per resa; granskaren får resultatet. Normans principer om begriplig handling och återkoppling som bedömningsfrågor.

**Klart när:** Ett bygge med bokning och kontakt har resor i RESOR.json som körs grönt på den slutliga versionen, med fel och återhämtning, och nivån står i kvittot.

**Klar (2026-10-04):** Grinden resor: kontroller/webblasare/resor.mjs, kunskap/resor.md; oberoende granskning, 18 fynd rättade
