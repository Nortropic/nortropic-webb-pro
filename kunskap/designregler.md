# Designregler — kvalitetskrav, Nortropics beslut, kundens behov och designhypoteser

Ägarens uppdrag via Codex 2026-10-05, punkt 2, och synpunkterna på metodkartan samma dag, punkt 2: reglerna för
formgivningen delas i fyra slag, och varje regel gäller inom sin räckvidd. Den här filen säger vilket slag en regel är
och vad som går före vad. Källan, vår tolkning och försöken per regel står i `kunskap/metodregler.md`; vilka skills och
avsnitt varje steg använder, och hur deras motsägelser avgörs, i `kunskap/metodkarta.md`. Kundens domar står i domloggen
`underlag/<slug>/DESIGNDOMAR.jsonl`. Allt designmaterial från före den rena designstarten 2026-10-09 är borttaget ur den
aktiva miljön och styr ingenting (`kunskap/ren-designstart.md`; avsnittet Historik sist).

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
- **Helhet och hierarki:** en sammanhängande idé genomförd överallt, hierarki och proportioner som bär innehållet, och
  verksamhetens egna bilder och ord. Kvaliteten bedöms i bildval, beskärning, typografiska proportioner, komposition, rytm
  och detaljarbete (ägarens bedömningsgrunder, ur kalibreringen 2026-10-04; exemplen och nivåfilen därifrån är borttagna
  vid den rena designstarten, kraven består).
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
| Tio kundanpassade förslag per omgång, var och en ur en identifierad professionell förebild eller fungerande designgrund och med en faktisk implementationsgrund; skillnaden syns i komposition, bildbehandling, typografi, innehållshierarki eller interaktion, aldrig bara i färg. Går tio inte att göra redovisas bristen, utan kosmetiska dubbletter (ägaren 2026-10-09 ~17:53Z; inte en hypotes) | skapandeflödet |
| Val för vidareutveckling, godkännande för helbygge och godkännande för publicering är tre beslut. Kunden kan välja, begära ett uppdrag (rätta, omarbeta designen, bygg ut) eller underkänna alla; godkännandena är ägarens. En AI-bedömning bokförs aldrig som kundens (ägaren 2026-10-09) | skapandeflödet och leveransen |
| Före och efter styr: en bättre och tekniskt fungerande version förs vidare, en tekniskt nödvändig men visuellt sämre kräver fortsatt lösning, en tidigare bättre version kan väljas, och ett oklart resultat står som oklart; skaparens självbedömning räcker inte för betydande designändringar (ägaren 2026-10-09) | skapandeflödet |

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
| Högst två typsnittsfamiljer | prestanda (byggstandarden 4.3) och läsbarhet | bygget; en godkänd DESIGN.md med fler roller avgör |
| En huvudreferens bär helheten | ägarbeslut 2026-10-04, Codex via ägaren 2026-10-05 | varje kandidat har sin egen |
| Ett motiv ur märket eller "Bara de har" | Anthropic frontend-design | utforskningen |
| Standarddrag bedöms efter användning | frontend-design | panelen och granskningen |
| Synliga menypunkter i stället för en dold meny när punkterna ryms | byggstandarden 5.2 till 2026-10-09 | en lösning bland flera; menyns form är riktningens |

Det finns ingen fast sektionsordning: ordningen är riktningens val och motiveras ur besökarens frågor.

## Historik (borttagen ur den aktiva miljön)

Den rena designstarten 2026-10-09 (ägarens uppdrag ~17:53Z, `kunskap/ren-designstart.md`) tog gamla byggen, prototyper,
kandidater, skärmbilder, designomdömen, kalibreringsankare, riktningar, referenspaket och de regler som härletts ur dem ur
den aktiva miljön, efter ett privat manifest och ett verifierat återställningsarkiv. Ägarens domar över tidigare byggen,
den gamla domloggen, riktningshistoriken och kalibreringen står i git-historiken och arkivet; de läses inte av agenterna
och blir aldrig regler, förebilder eller verifiering av den nya metoden. Ett gammalt färgval, en uppskattad mobilmeny
eller en viss rubrikstil är inget designbeslut för ett nytt förslag. Gamla externa referenser återanvänds bara efter ett
nytt uttryckligt urval för ett aktuellt uppdrag, och gamla kommentarer om hur de ska tillämpas följer inte med. Det som
gäller nu står ovan: ägarbesluten med räckvidd, och kundens aktuella domar efter brytpunkten.

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
