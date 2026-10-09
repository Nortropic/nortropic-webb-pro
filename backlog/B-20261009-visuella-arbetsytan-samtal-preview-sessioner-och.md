---
id: B-20261009-visuella-arbetsytan-samtal-preview-sessioner-och
status: klar
kalla: dom
kallref: BESLUT.md
skapad: 2026-10-09
prio: hog
steg: BESLUT.md 2026-10-09; kunskap/arbetsyta.md; dashboard/
commit: 9a674bf
andrad: 2026-10-09T09:34Z
---
# Visuella arbetsytan: samtal, preview, sessioner och resultat på ett ställe (ägarens uppdrag 2026-10-09 ~07:24Z)

**Varför:** Ägarens uppdrag 2026-10-09 (ordagrant i BESLUT.md, tillägget om den visuella arbetsytan): starta ett kunduppdrag, följa vilka verkliga sessioner som arbetar, se resultatet växa fram, diskutera med en arbetsledare och ge en avgränsad ändring utan att kopiera meddelanden mellan terminaler. Sex etapper; huvudvägen är den befintliga dashboarden (genomförarens teknikbeslut).

**Förslag:** En gemensam läsväg per kund, körning och session (dashboard/arbetsyta.py) med strömning; tre vyer (Arbetsyta, Byggflöde, Kod och preview); partnerdialog genom claude -p med samma sessions-id; ändringar genom ägarens beslut och flödets befintliga start; en läsande mod i Claude Code; prov, oberoende granskning och dokumentation i kunskap/arbetsyta.md.

**Klart när:** De tolv acceptansfallen har spårbara utfall mot en exakt version, en oberoende granskning är redovisad, arbetsytan är lokalt aktiverad med återgång till de tidigare vyerna, och kvarstående begränsningar står i kunskap/arbetsyta.md och i vyn.

**Pagar (2026-10-09):** Etapp 1 av 6 klar 2026-10-09: huvudväg B (dashboarden), startmiljö, överlappande arbete och första genomgående flöde bestämda (BESLUT.md, tillägget 2026-10-09; kunskap/arbetsyta.md).

## Läge 2026-10-09

Etapp 1–6 genomförda i grenen `claude/arbetsyta-20261009` (huvudväg: dashboarden; BESLUT.md, tillägget 2026-10-09).
Gällande beskrivning, gränser och det som inte är prövat: `kunskap/arbetsyta.md`. Prövat: `prov_arbetsyta.py` och
`prov_arbetsyta_webb.mjs` i rökprovet, moddens prov (`claude plugin test`), ett verkligt partnersamtal i två turer (Fable
5.1, samma session) och det verkliga sessionsprovet (`prov_arbetsyta_verklig_webb.mjs`: Opus 5.5 och Haiku i testprojektet,
med en provdrivrutin i stället för ateljéns orkestrering). Oberoende granskning och omgranskning:
`underlag/granskningar/GR-20261009-arbetsyta-oberoende.md` och `GR-20261009-arbetsyta-omgranskning.md`; fynden rättade
med prov. Inte prövat: en riktig ateljékörning eller ett helbygge genom arbetsytan, arbetsytan i ägarens dagliga bruk,
modellprofilens kvalitet (Fable 5.1 som arbetsledare), moddens ritning i en interaktiv terminal (prövad med Claude Codes
testkit för terminal och Desktop, och laddad i `claude -p`). Uppföljning: `B-20261009-prova-en-lasande-observatorsmod-i-motorns-claude`.

**Klar (2026-10-09):** Etapp 1–6 genomförda; se Läge 2026-10-09 nedan och kunskap/arbetsyta.md. Inte verifierad: verifierad är posten först när en senare granskning säger det.
