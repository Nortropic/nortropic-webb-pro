# Visuell nivå — ribban i tre nivåer, ur ägarens kalibrering (ankarhalvan)

Ägaren dömde 2026-10-04 tretton externa sajter blint (utan namn, bara skärmbilder: första vyn på mobil 390 och dator
1440 och hela sidan på mobil, för startsidan och en undersida) i tre nivåer och skrev vad som skiljer. Exemplen,
adresserna och ägarens ord i sin helhet är privata (`underlag/kalibrering/`, utanför git): det är namngivna sajter,
några av dem lokala verksamheters nuvarande. Hälften av exemplen är **ankare** i granskarens uppdrag (bilderna och
ägarens ord ordagrant fryses i varje omgång, `kalibrering.md`); hälften hålls undan och granskaren prövas på dem i
`kontroller/granskarforsok/kalibrering.py`. **Den här filen är byggd enbart ur ankarhalvan** (sju exempel): de
undanhållna domarna får aldrig forma reglerna som försöket utvärderar (Codex R30, testläckage). När ett nytt urval
döms läggs det undanhållna åt sidan innan den här filen uppdateras. Betygen i `kritik/GRANSKARE.md`: tydligt över
ribban = 8–9, nästan = 6, generisk = 5 eller lägre. Filen ingår i granskningens metodhash: en ändring här ogiltigförklarar
tidigare domar.

Ägaren dömer på sex saker: **bildval, beskärning, typografiska proportioner, komposition, rytm, detaljarbete**, och
skiljer "drar ner" (brister som inte fäller nivån) från "mått" (regeln som avgör).

## Tydligt över ribban

- **En enda egen idé genomförd överallt.** Lätt lutade färgetiketter som enda dekoration bär rubriker, platser och
  knappar; ett stort kort mot två små; runda ikonknappar i sidhuvudet. Eller inget alls: två färger, pilar i länkar,
  små piller för kategorier, inget tillagt för effekt, inga tjänstekort, inga ikoner, inga påståenden om kvalitet.
- **Egna människor och egna projekt som innehåll.** Egna lokaler och egna människor, ofta mitt i arbete, beskurna till
  kort med etikett; egna projektfoton professionellt tagna i konsekvent liggande format, människor i stående; inga
  stämningsbilder utan projekt.
- **Typografin låter som tal eller vilar i små skillnader.** En grotesk där brödtexten på mobil är nära rubrikstorlek och
  blandar fet och mager så att den låter som tal; eller en serif i läsbar storlek där rubriken är bara något större än
  brödtexten, så att lugnet kommer av små skillnader.
- **Hållning i en mening i stället för hero.** Första vyn kan vara en mening om vad de tror på och en länk; sedan jämn
  takt bild–namn–länk, ibland en rad vardagsspråk om huset; kontakt som två namngivna personer med porträtt,
  direktnummer och e-post i ett eget block.
- **Riktiga priser och riktiga människor.** En prislista som dragspel med nivåerna förklarade, avboknings- och
  försäkringsvillkor; "Boka" alltid synlig; ett arkiv med filter i samma system som startsidan.
- Brister som inte fäller nivån: en flytande knapp som skymmer en rad, blandade språk på en undersida, en platshållarbild,
  ett långt arkiv, liten ljus menytext på dator, tomma bildytor där inget hunnit laddas. Identiteten sitter i idén,
  orden och valen.

## Nästan

- **Genretrogen perfektion utan eget.** Egna foton av egna platser, redaktionellt beskurna och folktomma; tunn serif,
  små spärrade överrubriker, generös radhöjd; hero-video och växelvis en- och tvåspaltiga rutor med "Discover more";
  fast "Reserve"-knapp på mobil. Allt följer genrens mönster och kunde vara vilket varumärke som helst i den. Det egna
  måste synas i ord och val, inte bara i polering.
- **En första vy som kräver video är en första vy utan innehåll.** Ett tomt fält med logga, meny och knapp (video utan
  stillbild) räknas inte; en kakdialog ovanpå gör det värre.
- **Verklig substans i mallens form.** Exakta priser och tider, namngiven ägare, riktiga omdömen med namn och månad,
  egna oretuscherade jobbfoton i fallstudierna och en lång artikel om ett verkligt bygge med författare och datum, men
  hero och tjänstekort med inköpta showroombilder, serif plus sans plus guld, centrerade sektioner med samma luft,
  statistikrad ("5★", "100+ nöjda kunder", "100 % försäkrade"), fraser som "exceptionell kvalitet" och "anpassat efter
  dina behov". Byt bilderna i de viktigaste lägena och stryk statistikraden, så är den över.

## Generisk

- **Byt logotyp och det är vilken firma som helst.** Slagordshero ("Get the job done right!"), postnummersök, ikonrutnät
  med tjänster, garantikort, omdömeskarusell med hundratusentals omdömen, "tips från experterna", koncernlogotyper;
  poserade personalfoton i uniform, friställda. Inget lokalt, ingen namngiven person, inga priser, inga egna jobb,
  ingen adress; texten är allmän trygghetsretorik. Ikonrutnät + garantikort + statistik = generisk, oavsett hur stark
  färgen är.
- **Mallens treklang.** "Välkommen till" över fet versal firmarubrik, underrubrik av typen "en hantverkare du kan lita
  på", pillerknapp; den egna bilden (firmabilen) färgtonad som bakgrund med text ovanpå i stället för som innehåll;
  centrerad standardtext ("det trygga valet", "vi utför alla typer av …", "kontakta oss för en kostnadsfri offert");
  tjänstekarusell med pilar; ortssidor skrivna för sökmotorn. Inga namn, inga priser, inga datum.
- **Standardtema utan beslut.** All text i en dekorativ skriptfont, liten och grå; boxat tema med smal innehållsruta
  och breda grå marginaler; startsidan ett visitkort (logotyp, menylist, ett foto, adress, telefon) utan uppmaning och
  utan innehåll att skrolla till. Riktiga namn och riktiga foton räddar inte en sajt utan ett enda eget typografiskt
  eller strukturellt val.

## Hur nivåerna används

- Byggaren och ateljén läser den här filen i steg 4–5 och mäter varje första vy mot kännetecknen: finns en egen idé
  genomförd överallt, är bilderna innehåll, låter typografin som tal eller vilar den i små skillnader, är första
  påståendet en hållning?
- Granskaren får ankarna i uppdraget med ägarens ord bredvid och sätter betygen mot dem; det som är "nästan" får inte 7.
- Granskarförsöket mäter hur ofta granskaren godkänner det ägaren kallade nästan eller generisk (falska godkännanden)
  och underkänner det ägaren kallade tydligt över ribban; siffran står i `LARDOMAR.md`. Ett oberoende mått kräver ett
  urval som varken den här filen eller granskartexten har sett.
- Nya exempel: fånga dem i `underlag/kalibrering/` (kontroller/webblasare/inspektera.mjs, start och undersida), lägg
  raden i `URVAL.txt`, låt ägaren döma i dashboardens Kalibrering, dela i `ANKARE.txt`, och uppdatera den här filen
  bara ur ankarna.
