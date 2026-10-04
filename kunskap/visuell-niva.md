# Visuell nivå — ribban i tre nivåer, ur ägarens kalibrering

Ägaren dömde 2026-10-04 tretton externa sajter blint (utan namn, bara skärmbilder: första vyn på mobil 390 och dator
1440 och hela sidan på mobil, för startsidan och en undersida) i tre nivåer och skrev vad som skiljer. Exemplen,
adresserna och ägarens ord i sin helhet är privata (`underlag/kalibrering/`, utanför git): det är namngivna sajter,
några av dem lokala verksamheters nuvarande. Hälften av exemplen är **ankare** i granskarens uppdrag (bilderna och
ägarens ord ordagrant fryses i varje omgång, `kalibrering.md`); hälften hålls undan och granskaren prövas på dem i
`kontroller/granskarforsok/kalibrering.py`. Här står kännetecknen per nivå, utan sajternas namn, så att byggare,
ateljé och granskare drar samma gräns. Betygen i `kritik/GRANSKARE.md`: tydligt över ribban = 8–9, nästan = 6,
generisk = 5 eller lägre.

Ägaren dömer på sex saker: **bildval, beskärning, typografiska proportioner, komposition, rytm, detaljarbete**, och
skiljer "drar ner" (brister som inte fäller nivån) från "mått" (regeln som avgör).

## Tydligt över ribban

- **En egen idé genomförd överallt.** Lutade färgetiketter som bär rubriker, platser och knappar; ett rutnät med
  tunna ramlinjer där också bilderna sitter som rutor; hårlinjer i stället för kort. Inget är default, inget är
  tillagt för effekt.
- **Egna bilder som innehåll, inte stämning.** Egna platser, egna människor mitt i arbete, egna projekt i konsekvent
  format; beskurna som rutor i ett system, inte som helbildsstämning. Eller nästan inga bilder alls: produkten visar sig
  som text.
- **Typografin är ett system.** Ett typsnitt i två storlekar; rubriken bara något större än brödtexten så att lugnet
  kommer av små skillnader; brödtext som låter som tal; namnet satt i sin egen form. Stor spännvidd är tillåten när
  den är avsiktlig.
- **Hållning i en mening i stället för slagord.** Första vyn kan vara en mening om vad de tror på och en länk; sedan
  bara eget arbete, riktiga namn, riktiga priser, riktiga människor med direktnummer.
- **Mobil och dator är samma sajt i olika bredd.** Samma system på 390 och 1440.
- Brister som inte fäller nivån: en kakvägg som täcker första vyn, liten ljus menytext, en flytande knapp som skymmer
  en rad, en platshållarbild. Identiteten sitter i typografi, ord och val, inte i det som gick fel.

## Nästan

- **Formen över ribban, innehållet om företaget under.** Arbetet visas som likformiga rutor, men inget sägs om vilka,
  var, hur; en tagline är sajtens enda egna röst.
- **Genretrogen perfektion utan eget.** Tunn serif, dämpad palett, helbildsvideo, "Discover more": välgjort och
  utbytbart mot vilket varumärke som helst i genren. Det egna måste synas i ord och val, inte bara i polering.
- **Riktigt material, fel första möte.** Egna foton och återhållsamhet räcker inte när det första intrycket är en
  modal och det första påståendet är en kategorietikett ur katalogen; tunn ljus text på mörkt foto; språkbyte mellan
  sidor.
- **Verklig substans i mallens form.** Exakta priser, namngiven ägare, riktiga omdömen med namn och månad, egna
  oretuscherade jobbfoton i fallstudierna, men hero och tjänstekort med inköpta showroombilder, serif plus sans plus
  guld, centrerade sektioner med samma luft, statistikrad. Byt bilderna i de viktigaste lägena och stryk statistikraden,
  så är den över.
- **En första vy som kräver video är en första vy utan innehåll.** Ett tomt fält med logga, meny och knapp räknas inte.

## Generisk

- **Byt logotyp och det är vilken firma som helst.** Slagordshero, ikonrutnät med tjänster, garantikort, statistik,
  omdömeskarusell, koncernlogotyper, poserade personalfoton i uniform: inget lokalt, ingen namngiven person, inga priser,
  inga egna jobb, ingen adress.
- **Mallens treklang.** "Välkommen till" över fet versal firmarubrik, underrubrik av typen "en hantverkare du kan lita
  på", pillerknapp; egen bild som färgtonad bakgrund med text ovanpå i stället för som innehåll; centrerad standardtext;
  ortssidor skrivna för sökmotorn.
- **Sökfras som rubrik och stock i de viktigaste lägena.** Då finns ingen hållning kvar; det egna (ett fast pris, ett
  eget hus) drunknar.
- **Osynlig logotyp, overlayfoto, "VÄLKOMMEN"-etikett, en tryckt annons inklistrad som webbild.** Generisk även med ett
  riktigt företag bakom.
- **Standardtema utan beslut.** Dekorativ skriptfont som brödtext, boxat innehåll med breda grå marginaler, ett
  visitkort utan uppmaning och utan innehåll att skrolla till. Riktiga namn och riktiga foton räddar inte en sajt utan
  ett enda eget typografiskt eller strukturellt val.

## Hur nivåerna används

- Byggaren och ateljén läser den här filen i steg 4–5 och mäter varje första vy mot kännetecknen: finns en egen idé
  genomförd överallt, är bilderna innehåll, är typografin ett system, är första påståendet en hållning?
- Granskaren får ankarna i uppdraget med ägarens ord bredvid och sätter betygen mot dem; det som är "nästan" får inte 7.
- Granskarförsöket mäter hur ofta granskaren godkänner det ägaren kallade nästan eller generisk (falska godkännanden)
  och underkänner det ägaren kallade tydligt över ribban; siffran står i `LARDOMAR.md`.
- Nya exempel: fånga dem i `underlag/kalibrering/` (kontroller/webblasare/inspektera.mjs, start och undersida), lägg
  raden i `URVAL.txt`, låt ägaren döma i dashboardens Kalibrering, och dela i `ANKARE.txt`.
