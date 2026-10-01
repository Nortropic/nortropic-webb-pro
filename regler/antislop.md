# Antislop — regeln

> **UTKAST 2026-10-01.** Skrivet ur pratstunden, inte dikterat av ägaren. Ägaren skriver om det med egna ord; det som
> står här gäller tills dess. Ändringar i den här filen är det vanligaste sättet loop 3 förbättrar flödet.

Ägarens dom över Norrglänta: "undermålig, ai slope skit". Slop är det som uppstår när modellen saknar något specifikt
att säga. Regeln finns för att tvinga fram det specifika, inte för att polera ytan.

## Regler (läses i steg 3–5, prövas av ägaren i steg 8)

1. **Varje sektion bär minst en sak som bara den här verksamheten har.** Ett namn, ett tal, en plats, en egen bild, ett
   kundcitat med källa, ett pris, en arbetsgång. Finns inget sådant för en sektion, stryks sektionen.
2. **Varje mening som kunde stå hos en konkurrent stryks eller skrivs om** tills den inte kan det.
3. **Inga bilder som inte är verksamhetens egna eller tydligt tagna för den.** Ingen stockbild, ingen genererad bild som
   låtsas vara verklig. Saknas bilder: bygg sidan på text, typografi och verkliga uppgifter, och skriv det i rapporten.
4. **Inga påhittade siffror, omdömen, certifieringar eller löften.** Allt som påstås har en källa i `underlag/<slug>/`.
5. **Ingen mallstruktur av vana.** Hero med rubrik, underrubrik och två knappar, tre ikonkort, "Varför välja oss",
   en kundcitatkarusell och en avslutande uppmaning är inte förbjudna, men varje sådan del måste motiveras i briefen
   med en toppuppgift. Utan motivering väljs något annat.
6. **Beslut ska synas.** En sida där allt är lika viktigt, lika luftigt och lika stort har inga beslut. Välj vad som är
   viktigast och låt det dominera.
7. **Ton ur deras egna ord.** Plocka formuleringar ur deras nuvarande sajt, sociala kanaler och kundernas omdömen.
   Skriv som verksamheten pratar, inte som en byrå.

## Fraser (prövas mekaniskt i synlig text av `kontroller/prova.py`; en träff = röd grind)

Komplement till fraslistan i `kontroller/copy_kontroll.py`. Gemener eller versaler spelar ingen roll. En rad per fras.

```fraser
# byråspråk
skräddarsydd
skräddarsydda
helhetslösning
i framkant
innovativa lösningar
hållbara lösningar
högsta kvalitet
kvalitet i varje detalj
sätter kunden i fokus
med kunden i fokus
din trygga partner
en partner du kan lita på
ett brett utbud
brett sortiment
allt under ett tak
# tomma verb och utfyllnad
tveka inte att
upptäck vår
upptäck våra
utforska vår
utforska våra
smidigt och enkelt
enkelt och smidigt
sömlös
oslagbar
vi tar hand om resten
ta nästa steg
vi ser fram emot att höra från dig
# AI-ton på svenska
i en värld där
låt oss hjälpa dig
din resa
vår resa
passion för
med passion
```
