---
id: B-20261002-rendera-tvaan-den-nast-starkaste-riktningens-for
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · mattpocock/skills
skapad: 2026-10-02
prio: normal
steg: 5 Koncept (riktning) och 7 Frågor till ägaren
---
# Rendera tvåan: den näst starkaste riktningens första vy byggs på startsidan med verkligt innehåll, så att ägarens riktningsfråga får en skärmbild per alternativ

**Varför:** Prova A/B, egen innovation ur prototype/UI.md: varianter ska dömas mot verkligt innehåll, inte i vakuum. I alla tre byggen visade riktningsfrågan i FRAGOR.json bara den byggda sajten och beskrev alternativet i ord, och ägaren valde 'som byggd' alla tre gånger (LARDOMAR.md rad 40, 65, 89); svaret är träningsdata men bara ena sidan syntes.

**Förslag:** bygg-sajt steg 5.1 (rad 195–196): de två starkaste riktningarna blir en parvis fråga; den icke valda får sin startsidas första vy byggd som kastbar sida med samma INNEHALL.md, skärmbild 390 och 1440 med inspektera.mjs, och sidan tas bort med ta_bort.py före slutprovet. FRAGOR.json-formen (rad 302–311): 'bild' får vara en lista, en per alternativ. dashboard/index.html rad 255: visa en bild per alternativ när 'bild' är en lista. Prövning: två byggen med och två utan på samma sorts verksamhet; jämför hur ofta ägaren väljer bort den byggda riktningen och vad ägaren skriver i fritext, och redovisa extra tid och tokens per bygge.

**Klart när:** Nästa byggs riktningsfråga visar två skärmbilder i dashboarden, en per alternativ, och den kastbara sidan finns inte kvar i sajten
