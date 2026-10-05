# Designregler — kvalitetskrav, Nortropics beslut, kundens behov och designhypoteser

Ägarens uppdrag via Codex 2026-10-05, punkt 2, och synpunkterna på metodkartan samma dag, punkt 2: reglerna för
formgivningen delas i fyra slag, och varje regel gäller inom sin räckvidd. Den här filen säger vilket slag en regel är
och vad som går före vad. Källan, vår tolkning och försöken per regel står i `kunskap/metodregler.md`; vilka skills och
avsnitt varje steg använder, och hur deras motsägelser avgörs, i `kunskap/metodkarta.md`. Ägarens domar står ordagrant
i `LARDOMAR.md` och domloggen `underlag/<slug>/DESIGNDOMAR.jsonl`.

## Ordningen

1. **Gemensamma kvalitetskrav** gäller varje förslag och varje bygge, oavsett riktning och kund.
2. **Nortropics produkt- och ägarbeslut** gäller inom sin räckvidd: det erbjudande eller det arbete beslutet avsåg.
3. **Kundens behov** kommer ur verksamheten, med belägg: vad besökarna behöver åstadkomma och vad verksamheten
   behöver av sajten. De bestämmer vad sidan måste klara, inte hur den ser ut.
4. **Designhypoteser och preferenser** prövas mot kundens behov. Ett förslag som löser samma behov på ett annat sätt
   är lika giltigt, och skälet skrivs i dess anteckningar.

En skills standardråd står under alla fyra.

## Gemensamma kvalitetskrav

- **Sanning:** namn, nummer, orter, år, tjänster, omdömenas ordalydelse och varje påstående om hur verksamheten
  arbetar har belägg i underlaget; saknas källan stryks eller beställs uppgiften (ägarens domar L1–L6).
- **Läsbarhet:** kontrast för brödtext minst 4,5:1 (WCAG 2.2 AA), radlängd och radhöjd som går att läsa, rubriker i
  ordning med en h1 per sida, `lang="sv"`.
- **Fungerande interaktion:** varje länk och knapp leder dit den säger, formulär har etiketter och felbesked vid
  fältet, synligt tangentbordsfokus, klickytor minst 24 px och primära knappar 44 px i 390 (byggstandarden 3.3),
  inget sidled-spill i 390, 768 eller 1440, inga konsolfel.
- **Den primära handlingen nås:** den syns i första vyn på mobilen och går att nå med tummen. Hur den löses (sidhuvud,
  list, sektion) är riktningens val.
- **Bilder med uppgift:** alt-text efter bildens uppgift, inga bilder som utger sig för att vara något de inte är.

## Nortropics produkt- och ägarbeslut

| Beslut | Räckvidd |
|---|---|
| Statisk Astro med sidans egen CSS, ingen JavaScript som inte behövs, självhostade typsnitt eller systemtypsnitt, verksamhetens bilder genom `astro:assets` | dagens erbjudande: webbplatser för lokala tjänsteföretag. En bokningstjänst, en butik eller en större innehållssajt kan behöva andra lösningar och får då ett eget beslut |
| Inga karuseller, marquees eller sidor som rullar av sig själva (byggstandarden) | dagens erbjudande |
| I skapandeflödet installeras inga paket utom typsnitt (`kontroller/typsnitt.py`), och formulären demonstreras lokalt (`/api/forfragan` → `/tack/`) | skapandeflödet |
| Telefonnumret som tel-länk i sidhuvudet på varje sida (byggstandarden) | dagens erbjudande, för verksamheter där kunderna ringer |
| Verksamhetens egna bilder eller ingen bild; inga stockbilder eller genererade bilder (L3: "hellre inga foton än stock") | alla kunder |
| En namngiven referens får vara utgångspunkt för layout, palett och typografi (2026-10-03); dess identitet, texter och bilder blir aldrig kundens | allt designarbete |
| Bäst av tre undermåliga godkänns aldrig (2026-10-04) | panelen och granskningen |
| Ägaren dömer blint och först; panelens omdöme visas efter (2026-10-03–04) | dashboardens vyer |
| Den godkända prototypen gäller i bygget; en annan riktning utan nytt godkännande är ett blockerande fynd | byggen efter ett godkännande |
| Domloggens domar för en kund; den senaste går före | den kunden |

## Kundens behov

- **Användarbehov** skrivs som vad besökaren behöver åstadkomma och varför ("som villaägare som planerar en
  tillbyggnad behöver jag se liknande jobb för att våga ringa"), med insiktskälla ur briefen (`kunskap/brief-mall.md`
  §2: intervjuer, observationer, data, antaganden eller saknas). Toppuppgifterna och den primära handlingen står i
  `underlag/<slug>/BRIEF.md`; startsidan och undersidan ska låta besökaren göra dem.
- **Antaganden som kan ändra designen** prövas: vilket underlag stöder dem, hur prövas de, och vad ändras om de inte
  stämmer (researchen skriver dem i FORSKNING.md). För en prospektdemo får svaret vara "ännu inte observerat"; i ett
  skarpt uppdrag prövas de viktiga med relevanta användare eller befintliga beteendedata, med testuppgifter som
  beskriver besökarens mål utan att avslöja vilken knapp hen ska trycka på.
- **"Bara de har"** i `RESEARCH.md`: det som skiljer verksamheten från andra bär positioneringen.
- **Materialet** i `bilder/BILDER.md`: vad fotona visar och håller för (resultat, detalj, arbete, person). En riktning
  som kräver material kunden inte har skriver behovet under "Material".
- För en lokal tjänsteverksamhet brukar orten och kontaktvägen höra till första vyn; det avgörs av briefens
  toppuppgifter och belägg, inte av en allmän regel.

## Designhypoteser och preferenser (prövas, aldrig krav)

| Hypotes | Ursprung | Som utgångspunkt i |
|---|---|---|
| Sidhuvud på en rad med den primära handlingen som knapp, menylänkarna synliga utan hamburgare, fast list längst ned med den primära handlingen och Skriv, numret högst två gånger i första vyn | ägarens A/B 2026-10-02 och domarna L1, L2, L4, L5 (två hantverks- och salongsbyggen) | bygget (stilrapporten mäter, varnar, fäller inte); i kandidatflödet en lösning bland flera |
| Brödsmulor på varje undersida | ägarens A/B-omdöme 2026-10-02 | bygget (byggstandarden 7.3) |
| Högst två typsnittsfamiljer | prestanda (byggstandarden 4.3) och läsbarhet | bygget; en godkänd DESIGN.md med fler roller avgör |
| En huvudreferens bär helheten | ägarbeslut 2026-10-04, Codex via ägaren 2026-10-05 | varje kandidat har sin egen |
| Ett motiv ur märket eller "Bara de har" | Anthropic frontend-design | utforskningen |
| Undvik de upptagna valen (`UPPTAGNA-VAL.md`) om inte verksamhetens material motiverar dem | våra egna byggens mönster | utforskningen |
| Standarddrag bedöms efter användning | frontend-design | panelen och granskningen |

Det finns ingen fast sektionsordning: ordningen är riktningens val och motiveras ur besökarens frågor.

## Research: observation, rekommendation, belagd effekt

Som i GOV.UK:s tjänstemanual hålls tre saker isär i research, riktningar och anteckningar:

- **Observation:** vad en referens gör, med var det syns (sajt, sida, bild, mått i `EXTRAKT.md` eller tjänstens
  beskrivning i `TJANSTER.md`; uppmätt och beskrivet skiljs åt).
- **Rekommendation:** vad vi föreslår för kunden och varför, ur kundens behov och material.
- **Belagd effekt:** bara med en källa som visar effekten (en studie, en mätning). Att en känd sajt gör något är en
  observation, inte en belagd effekt.
