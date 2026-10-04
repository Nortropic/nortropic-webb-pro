---
id: B-20261005-observation-bildkedjan-matning-rorelse-dokument-ljud
status: vilande
kalla: bevakning
kallref: Codex tillägg 3 (natten 2026-10-04/05): observationsverktyg; ägarmandat 2026-10-04
skapad: 2026-10-05
prio: hog
andrad: 2026-10-04T22:17Z
---
# Observation: verifierad bildkedja, bild → mätning → beslut, rörelse, dokument och ljud, nytta mot facit

**Varför:** Codex prioriterar syn, layoutmätning och interaktion, sedan rörelse; ljud och dokument förbättrar främst
kundintaget. Tre delar måste fungera tillsammans: verktyget observerar, modellen får användbart innehåll (bilden,
transkriptet, analysen), skillen styr vad som undersöks, ändras och verifieras. Ett lyckat verktygsanrop bevisar inte
att rätt bild bedömts: Refero `get_screen_image` ger tumnagel som standard, Mobbin har en lågupplöst bild och en separat
högupplöst `image_url` (giltig 30 dagar), och en skärmbild som sparas till fil måste läsas i ett eget steg.
`kontroller/youtube.py` tar en bildruta varannan sekund, för glest för en övergång på 200 ms.

**Förslag (Codex fem steg):** (1) Verifiera bildkedjan hela vägen: en rapport per bygge och omgång över vilka
referensbilder byggaren, ateljén och granskaren faktiskt fick och läste (fil, upplösning, tillstånd, källa; Refero i
full storlek, Mobbin högupplöst), ur sessionsloggarnas Read-anrop. (2) Koppla bilder till mätningar och beslut: för en
vald sektion typografisk hierarki, proportioner, beskärning, mellanrum och responsiv förändring (extrahera.mjs),
beslutet i DESIGN.md, prototypen, och jämförelse av den renderade implementationen (jamfor.mjs och extraktet av
bygget). (3) Rörelse: korta tidsupplösta förlopp kring meny, hover, fokus och sidövergångar (Playwright-video eller
tät skärmbildssekvens, med uppmätt varaktighet), och samma fångst för referenser där rörelse är en fråga. (4) Dokument
och ljud när kundunderlaget kräver det: Docling för PDF, prislistor och kataloger (sidbilder sparas), Whisper.cpp lokalt
för intervjuer och röstanteckningar; Gemini för analys av ljud och video som ett avgränsat verktyg. (5) Nytta mot
facit först, sedan blind designbedömning: ett bildverktyg ska upptäcka en synlig layoutskillnad även när texten är
identisk. Kandidater: Chrome DevTools MCP med officiell skill, Playwright MCP (efter en täckningsgenomgång av våra
Playwright-verktyg), Dembrandt, Vercel dogfood (utan fyndkvot). /voice är diktering, inte ljudanalys; ElevenLabs
hosted MCP är inte hörsel.

**Klart när:** bildkedjerapporten finns för ett bygge och visar upplösning och tillstånd per läst bild; en sektion har
gått hela vägen bild → mätning → DESIGN.md → prototyp → jämförelse; rörelse kan fångas med tidsupplösning under 50 ms;
ett facitprov visar att bildverktyget fångar en layoutskillnad med identisk text.
