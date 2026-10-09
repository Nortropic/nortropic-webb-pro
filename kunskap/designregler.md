# Designregler — kvalitetskrav, Nortropics beslut, kundens behov och designhypoteser

Ägarens uppdrag via Codex 2026-10-05, punkt 2, och synpunkterna på metodkartan samma dag, punkt 2: reglerna för
formgivningen delas i fyra slag, och varje regel gäller inom sin räckvidd. Den här filen säger vilket slag en regel är
och vad som går före vad. Källan, vår tolkning och försöken per regel står i `kunskap/metodregler.md`; vilka skills och
avsnitt varje steg använder, och hur deras motsägelser avgörs, i `kunskap/metodkarta.md`. Kundens domar står i domloggen
`underlag/<slug>/DESIGNDOMAR.jsonl`; ägarens domar över tidigare byggen (`LARDOMAR.md`) är historik (avsnittet sist).

## Ordningen

1. **Gemensamma kvalitetskrav** gäller varje förslag och varje bygge, oavsett riktning och kund.
2. **Nortropics produkt- och ägarbeslut** gäller inom sin räckvidd: det erbjudande eller det arbete beslutet avsåg.
3. **Kundens behov** kommer ur verksamheten, med belägg: vad besökarna behöver åstadkomma och vad verksamheten
   behöver av sajten. De bestämmer vad sidan måste klara, inte hur den ser ut.
4. **Designhypoteser och preferenser** prövas mot kundens behov. Ett förslag som löser samma behov på ett annat sätt
   är lika giltigt, och skälet skrivs i dess anteckningar.

En skills standardråd står under alla fyra.

## Källornas slag

Varje regel och metodval hör till ett slag (ägarens uppdrag 2026-10-09), och slaget avgör hur den gäller:

| Slag | Så gäller det |
|---|---|
| Standarder och teknisk dokumentation (WCAG, ramverk, tjänster) | kvalitetskraven och byggstandarden, prövade mot aktuell officiell dokumentation |
| Forskningsbaserade metoder (`kunskap/teoretisk-grund.md`) | arbetssätt med syfte och begränsning; vår tolkning och prövning i `kunskap/metodregler.md` |
| Specialistguider och skills (`KALLA.md`) | tekniker och kriterier inom rollen; aldrig ett krav av sig självt |
| Referenser och inspiration | exempel vars kvaliteter analyseras mot kundens material; aldrig regler |
| Kundens fakta, mål och användarunderlag | förutsättningarna; en AI-genererad målgruppshypotes är ett antagande |
| Ägarbeslut (`BESLUT.md`, tabellen nedan) | med avsändare och räckvidd |
| Lokala hypoteser och processval | med motivering och prövningsstatus; aldrig beskrivna som litteraturens |

Ersatta instruktioner är historik i `BESLUT.md`, och `kontroller/styrning.py` fäller dem i agenternas texter.

## Gemensamma kvalitetskrav

- **Sanning:** namn, nummer, orter, år, tjänster, omdömenas ordalydelse och varje påstående om hur verksamheten
  arbetar har belägg i underlaget; saknas källan stryks eller beställs uppgiften.
- **Läsbarhet:** kontrast för brödtext minst 4,5:1 (WCAG 2.2 AA), radlängd och radhöjd som går att läsa, rubriker i
  ordning med en h1 per sida, `lang="sv"`.
- **Fungerande interaktion:** varje länk och knapp leder dit den säger, formulär har etiketter och felbesked vid
  fältet, synligt tangentbordsfokus, klickytor minst 24×24 px (WCAG 2.2 AA, 2.5.8; byggstandarden 3.3), inget
  sidled-spill i 390, 768 eller 1440, inga konsolfel.
- **Den primära handlingen är tydlig och lätt att hitta** (ägaren 2026-10-09); var och hur den står är riktningens val.
- **Bilder med uppgift och äkthet:** alt-text efter bildens uppgift. En bild som visar verksamheten (dess arbeten,
  personer, lokaler, fordon, resultat och referenser) är verksamhetens egen; ett stockfoto eller en genererad bild utger
  sig aldrig för att visa den. Visuellt material som inte utger sig för att dokumentera verksamheten (licensierade
  illustrationer, texturer, mönster, tydligt illustrativa konceptbilder) är tillåtet med källa och licens i
  `bilder/BILDER.md` eller DESIGN.md.
- **Säkerhet och kunddata:** kundens namn, orter, nummer och e-post går aldrig till externa tjänster (Refero, Mobbin);
  inga hemligheter i kod, underlag eller rapporter; paket bara ur mallens låsta beroenden (`kunskap/beroenden.md`) och
  genom `kontroller/typsnitt.py`, och byggen innanför processgränsen.
- **Prestanda, robusthet och rörelse:** innehållet och navigationen fungerar utan JavaScript, rörelse respekterar
  `prefers-reduced-motion`, och prestandabudgeten håller (byggstandarden 4), vilken teknik riktningen än valt.
- **Utkast är märkta:** där kundens material saknas står ett tydligt märkt textutkast eller en platshållare som säger vad
  som saknas; omdömen, meriter, certifieringar, resultat och siffror hittas aldrig på.

## Nortropics produkt- och ägarbeslut

| Beslut | Räckvidd |
|---|---|
| Astro med förrenderade sidor; varje riktning väljer en sammanhängande implementation ur de förberedda, granskade och låsta beroendena (egen CSS, Referos CSS-variabler, Tailwind, Astro- och React-komponenter, Motion; `kunskap/beroenden.md`); självhostade typsnitt eller systemtypsnitt; verksamhetens bilder genom `astro:assets`. Nortropics standardval: ägaren godkände 2026-10-05 18:53Z att de tidigare förbuden omprövas, och urvalet av beroenden är agentens | dagens erbjudande: webbplatser för lokala tjänsteföretag. En bokningstjänst, en butik eller en större innehållssajt kan behöva andra lösningar och får då ett eget beslut |
| Inga karuseller, marquees eller sidor som rullar av sig själva (byggstandarden) | dagens erbjudande |
| Inga paketinstallationer i flödets sessioner: beroendena förbereds, granskas och låses i mallen (`kunskap/beroenden.md`), typsnitt genom `kontroller/typsnitt.py`; formulären demonstreras lokalt (`/api/forfragan` → `/tack/`) | skapandeflödet |
| Primära interaktiva kontroller minst 44×44 CSS-pixlar; skilt från WCAG:s minimum (24 px, 2.5.8) och inget krav på alla länkar (ägaren 2026-10-09; byggstandarden 3.3) | dagens erbjudande |
| Kundens kontaktvägar ur briefen (§4) finns på varje sida: har kontaktmodellen telefonen står numret som tel-länk på varje sida; placeringen är riktningens val (byggstandarden 9.2; Codex via ägaren 2026-10-05, punkt 2) | dagens erbjudande |
| En namngiven referens får vara utgångspunkt för layout, palett och typografi (2026-10-03); dess identitet, texter och bilder blir aldrig kundens | allt designarbete |
| Bäst av tre undermåliga godkänns aldrig (2026-10-04) | panelen och granskningen |
| Ägaren dömer blint och först; panelens omdöme visas efter (2026-10-03–04) | dashboardens vyer |
| Den godkända prototypen gäller i bygget; en annan riktning utan nytt godkännande är ett blockerande fynd | byggen efter ett godkännande |
| Domloggens aktuella domar för en kund (från den senaste som begärde en ny riktning; en förkastning återöppnar bara grundidéerna och referenserna); den senaste går före | den kunden |

## Kundens behov

- **Användarbehov** skrivs som vad besökaren behöver åstadkomma och varför ("som villaägare som planerar en
  tillbyggnad behöver jag se liknande jobb för att våga ringa"), med insiktskälla ur briefen (`kunskap/brief-mall.md`
  §2: intervjuer, observationer, data, antaganden eller saknas). Toppuppgifterna och den primära handlingen står i
  `underlag/<slug>/BRIEF.md`; startsidan och undersidan ska låta besökaren göra dem.
- **Antaganden som kan ändra designen** prövas: vilket underlag stöder dem, hur prövas de, och vad ändras om de inte
  stämmer (researchen skriver dem i FORSKNING.md). För en prospektdemo får svaret vara "ännu inte observerat"; i ett
  skarpt uppdrag prövas de viktiga med relevanta användare eller befintliga beteendedata, med testuppgifter som
  beskriver besökarens mål utan att avslöja vilken knapp hen ska trycka på (protokollet: `kunskap/besokarprov.md`).
- **"Bara de har"** i `RESEARCH.md`: det som skiljer verksamheten från andra bär positioneringen.
- **Materialet** i `bilder/BILDER.md`: vad fotona visar och håller för (resultat, detalj, arbete, person). En riktning
  som kräver material kunden inte har skriver behovet under "Material".
- **Mobilens första vy:** den primära handlingen står där när briefens prioriterade besökaruppgift motiverar det (för
  en lokal tjänsteverksamhet ofta också orten och kontaktvägen), ur kundunderlag och research; utan direkt
  användarbevis är motiveringen en hypotes att pröva. Funktion och visuell kvalitet bedöms var för sig (ägaren 2026-10-09).

## Designhypoteser och preferenser (prövas, aldrig krav)

| Hypotes | Ursprung | Som utgångspunkt i |
|---|---|---|
| Brödsmulor på varje undersida | ett omdöme över ett tidigare bygge (historik) | en lösning bland flera; DESIGN.md:s struktur säger om sajten har dem, och då prövar byggstandarden 7.3 att de finns |
| Högst två typsnittsfamiljer | prestanda (byggstandarden 4.3) och läsbarhet | bygget; en godkänd DESIGN.md med fler roller avgör |
| En huvudreferens bär helheten | ägarbeslut 2026-10-04, Codex via ägaren 2026-10-05 | varje kandidat har sin egen |
| Ett motiv ur märket eller "Bara de har" | Anthropic frontend-design | utforskningen |
| Undvik de upptagna valen (`UPPTAGNA-VAL.md`) om inte verksamhetens material motiverar dem | våra egna byggens generiska mönster (inget bygge hittills har varit bra nog) | utforskningen |
| Standarddrag bedöms efter användning | frontend-design | panelen och granskningen |
| Den primära handlingen inom tummens räckvidd, eller i en fast nederlist | kvalitetskravet till 2026-10-09 (historik) | en lösning bland flera, aldrig ett generellt layoutkrav (ägaren 2026-10-09) |
| Synliga menypunkter i stället för en dold meny när punkterna ryms | byggstandarden 5.2 till 2026-10-09 | en lösning bland flera; menyns form är riktningens |

Det finns ingen fast sektionsordning: ordningen är riktningens val och motiveras ur besökarens frågor.

## Historik och smakdomar (slås upp, gäller inte automatiskt)

Ägarens domar över tidigare byggen (`LARDOMAR.md`, ordagrant i det privata `underlag/LARDOMAR-original.md`) är
historik: inget bygge hittills har varit bra nog, allt har varit generiskt (ägaren 2026-10-05). De bevaras men läses
inte av agenterna (läsförbud i sessionerna, rensningen inför Nortropic 2.0) och blir aldrig regler eller förebilder.
Kundens äldre domar i domloggen, riktningshistoriken (`underlag/<slug>/RIKTNINGSHISTORIK.json`), kalibreringen och
beslutshistoriken i `BESLUT.md` bevaras och slås upp när de besvarar en konkret fråga; de läses inte i förväg och blir
aldrig regler för en ny kund. Ett gammalt färgval, en uppskattad
mobilmeny eller en viss rubrikstil är ett exempel ur ett bygge, ingen designregel. Det som gäller nu står ovan: ett
uttryckligt ägarbeslut med sin räckvidd i tabellen, och kundens aktuella domar (från den senaste domen som begärde en ny
riktning, och de efter den) i domloggen; ett uttryckligt beslut i en äldre dom om annat än designen gäller tills en
senare dom återöppnar det.

## Ersatt

Regler som ersatts står med vad som ersatte dem och varför i `BESLUT.md` (senast tillägget 2026-10-05, sen
kväll); de gäller inte längre.

## Research: observation, rekommendation, belagd effekt

Som i GOV.UK:s tjänstemanual hålls tre saker isär i research, riktningar och anteckningar:

- **Observation:** vad en referens gör, med var det syns (sajt, sida, bild, mått i `EXTRAKT.md` eller tjänstens
  beskrivning i `TJANSTER.md`; uppmätt och beskrivet skiljs åt).
- **Rekommendation:** vad vi föreslår för kunden och varför, ur kundens behov och material.
- **Belagd effekt:** bara med en källa som visar effekten (en studie, en mätning). Att en känd sajt gör något är en
  observation, inte en belagd effekt.
