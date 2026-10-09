---
id: B-20261005-observation-bildkedjan-matning-rorelse-dokument-ljud
status: klar
kalla: bevakning
kallref: Codex tillägg 3 (natten 2026-10-04/05): observationsverktyg; ägarmandat 2026-10-04
skapad: 2026-10-05
prio: hog
commit: 91f70a5
andrad: 2026-10-09T08:16Z
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

**Vilande (2026-10-05):** Steg 1 påbörjat 2026-10-05: kontroller/bildkedja.py ställer erbjudna bilder mot Read i sessionernas transkript (rapport per bygge, kunder/<slug>/BILDKEDJA.md), och ateljéns panel kräver och prövar läsningen av ägarens ord, ankarnas första vyer, huvudreferensens bildval och varje riktnings första ruta (omdom en gång, sedan räknas rösten inte). Fynd: i designprovet läste domarna 0–5 av 21 ankarbilder; i holms-konditori-abx lämnade varje granskare ett tiotal erbjudna referensbilder oläst per omgång. Kvar: samma krav för byggets granskare (granska.py), steg 2–5.

**Vilande (2026-10-05):** Avstämt 2026-10-05: steg 1 levererat för ateljén, granskaren och prototypen; skapandeflödet lägger till läsningen per förhandsvarv i ordning och metodkvittot (bildkedja.varvordning och metodlasning, atelje/REDOVISNING.md), och Claude Codes medietak är uppmätt (de äldsta bilderna trängs undan). Kvar: upplösning, tillstånd och källa per läst bild i rapporten; steg 2 genom förfiningens DESIGN.md, verifierat; steg 3 rörelse (inflyttad från referenssteget); steg 4 dokument och ljud; steg 5 facitprovet.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: commit cba65bb (observationen, BESLUT 2026-10-06), kontroller/bildkedja.py, H1 referensinspektion (r110) och H2 rörelse (r112) i a108560; nyttan mot facit är ägarens designbedömning, ingen backlogpost

**Pagar (2026-10-09):** Återöppnad 2026-10-09: GR-20261009-metod-till-resultat-codex#T02 (verifierad avgränsning): prototypens bilder ingick inte i läsobservationen, och ett grönt helbyggebesked skiljde inte designnivån från om den föreskrivna jämförelsen gjorts.

**Klar (2026-10-09):** T02 rättad (91f70a5): prototypens och byggets motsvarande bilder är läskrav, granskaren svarar strukturerat i prototypjamforelse, och domen bär visuell_jamforelse skilt från godkännandet: underlaget saknas eller fel version, ej bedömd, oläst, ej observerbar, verifierad. Ingen generell läsregel. prov_metodglapp Jamforelsebesked (8 fall) och prov_revision (verklig omgång med falsk claude). Verklig granskares svar är oprövat.
