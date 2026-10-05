---
id: B-20261003-stilrapporten-mater-text-som-inte-ryms-i-sin-ege
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · OpenAI, Frontend prompt instructions
skapad: 2026-10-03
prio: normal
steg: steg 6, stilrapporten (kontroller/stil.mjs)
andrad: 2026-10-05T06:55Z
---
# Stilrapporten mäter text som inte ryms i sin egen ruta i 390 och 320 px, inte bara spill i hela dokumentet

**Varför:** Dom nej: OpenAI:s frontendprompt togs in redan 2026-10-02 via bevakningen (B-20261002-stilrapport, commit 442ed69). En regel ur den återstår omätt: text ska rymmas i sitt eget element på varje vy, med den längsta ordet som mått. Våra prov mäter bara spill på dokumentnivå (gemensamt.mjs rad 120–121, utforska.mjs rad 124); ett svenskt sammansatt ord som sticker ut ur en knapp eller en spalt med overflow hidden eller min-width 0 syns inte där, bara i granskarens ögon.

**Förslag:** kontroller/stil.mjs, i matPaSidan(): för synliga element med egen text (rubriker, knappar, länkar, li, td, figcaption, p) i 390 (och 320 när vyn finns) rapportera dem där scrollWidth > clientWidth + 1 eller där ett enda ord är bredare än elementets clientWidth (mät med Range.getBoundingClientRect per ord i textnoden); en varning per sida med texten och vyn, som information, aldrig grind. Rökprovet får ett fall med ett 28 tecken långt ord i en 160 px knapp.

**Klart när:** STIL.md på rökprovet visar varningen för det inlagda ordet och ingen varning på en sida utan överskjutande text; kontroller/rokprov.sh grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord; mätningen finns varken i stilrapporten eller i inspektionen.
