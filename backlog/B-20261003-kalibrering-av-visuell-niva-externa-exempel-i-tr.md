---
id: B-20261003-kalibrering-av-visuell-niva-externa-exempel-i-tr
status: pagar
kalla: bevakning
kallref: Codex bedömning av den visuella nivån, 2026-10-03
skapad: 2026-10-03
prio: hog
andrad: 2026-10-04T14:00Z
---
# Kalibrering av visuell nivå: externa exempel i tre nivåer, granskarna prövade på osedda exempel

**Varför:** Codex 2026-10-03: bildankarna är våra egna tidigare byggen och befäster en nivå ägaren nu säger är otillräcklig; två granskare som håller med varandra visar inte att nivån stämmer med ägarens. Anthropics försök: en separat AI-granskare godkände fortfarande mediokra resultat tills den kalibrerades med exempel.

**Ägarens besked 2026-10-03, ordagrant:** "DETTA FÅR INTE EXISTERA FÖR VÅRA HEMSIDOR ÄR DÅLIGA OCH HÅLLER INTE" (om att ribban förankrats i egna byggen). Samma dag togs egna dömda byggen bort som bildankare och kalibrering ur granskarens och ateljéns uppdrag; tidigare byggen visas bara för likhetskontroll. Urvalet här är en start, inte ett bevis: håll undan hela sajter och kundfall inklusive bilder och domar, och mät också när granskarna underkänner det ägaren godkänner (Anthropic, "Demystifying evals for AI agents", 2026-01-09, läst 2026-10-03: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents. Artikeln säger: kalibrera modellbaserade rubriker ofta mot experters omdöme; balanserade uppsättningar med fall där beteendet ska och inte ska inträffa, så att inte bara ena hållet mäts; döm en dimension i taget i isolerade omdömen; ge domaren en utväg ("Unknown") när underlaget inte räcker; upprepade försök och pass@k eller pass^k i stället för ett enda utfall; börja med 20–50 uppgifter ur verkliga fel.)

**Förslag:** Kartläggningen finns redan och återanvänds: gallerierna i kunskap/referensjakt.md (Awwwards, SiteInspire, Godly, FWA, CSS Design Awards, Httpster, One Page Love) som sökingångar, Inspo-arkivet (832 sajter, A/B pågår) och exemplartabellen i kunskap/referenser-professionella.md; Mobbin läggs till som mönsterbibliotek för dimension 7 (mobil ergonomi), som i dag saknar exempel. Det nya är inte fler källor utan ägarens dom: agenten väljer ur det befintliga 9–12 sajter i tre nivåer (tydligt över ribban, nästan, generisk); ägaren dömer mobil, desktop och en undersida och säger exakt vad som skiljer nivåerna (bildval, beskärning, typografiska proportioner, komposition, rytm, detaljarbete). Hälften blir ankare i kritik/GRANSKARE.md med skälen; hälften hålls undan och granskarna prövas på dem i kontroller/granskarforsok/. Måttet: hur ofta granskarna godkänner det ägaren underkänner.

**Klart när:** kunskap/visuell-niva.md med exemplen och skälen; GRANSKARE.md pekar på ankarna; granskarförsöket rapporterar falska godkännanden på de undanhållna exemplen, och siffran står i LARDOMAR.md.

**Pagar (2026-10-03):** steg 1 klart (dc21ecb): 13 exempel i tre nivåer fångade (underlag/kalibrering, start + undersida, 390/1440), dashboardvyn Kalibrering sparar ägarens dom privat; väntar på ägarens domar, sedan kunskap/visuell-niva.md, ankare i GRANSKARE.md och granskarförsöket på de undanhållna

**Pågår (2026-10-04T13:30Z):** steg 2. Ägaren dömde alla 13 exempel 2026-10-04 (privat: underlag/kalibrering/DOMAR.json och DOMAR-original-20261004.md; fördelning 4 över, 4 nästan, 5 generisk). Delningen i underlag/kalibrering/ANKARE.txt: sju ankare (K03, K05, K06, K07, K08, K09, K12), sex undanhållna (K01, K02, K04, K10, K11, K13). granska.py fryser ankarna i varje omgång (kalibrering/ med första vyn 390 och 1440, kalibrering.md med ägarens ord ordagrant) och uppdraget pekar på dem; kritik/GRANSKARE.md förklarar nivåerna som betyg (över 8–9, nästan 6, generisk ≤ 5); kunskap/visuell-niva.md har kännetecknen per nivå utan sajternas namn; kontroller/granskarforsok/kalibrering.py prövar granskaren på de undanhållna och räknar falska godkännanden och falska underkännanden. Kvar: köra försöket och skriva siffran i LARDOMAR.md; fånga om K03:s undersida (samma sida som startsidan) och de hela-bilder som kakdialogen tömde (K01, K04).

**Pågår (2026-10-04T13:53Z):** försöket kört (opus[1m] high, sex undanhållna): falska godkännanden 0 av 4, falska underkännanden 0 av 2, svar 6 av 6; siffran i LARDOMAR.md (Kalibrering · 2026-10-04), rapporten privat i underlag/kalibrering/FORSOK-20261004/. Färdigkriteriets fyra delar är uppfyllda. Kvar innan posten sätts klar: fånga om K03:s undersida (samma sida som startsidan) och K01/K04:s hela-bilder bakom kakdialogen, så att ankarna är hela; sedan ägarens dom om posten.

**Pågår (2026-10-04T14:00Z, efter Codex R30):** försökets siffra nedgraderad till utvecklingsdata: kunskap/visuell-niva.md var byggd ur alla tretton domarna (testläckage) och är nu byggd enbart ur ankarhalvan; filen ingår i metodhashen; försöket binder varje svar till ett manifest (modell, effort, hashar av uppdrag, regler, bilder, ankare) och validerar hela svaret, anropsfel ger ofullständigt försök. Kvar för ett oberoende slutmått: ett nytt, orört urval (sex sajter i tre nivåer, fångade med inspektera.mjs, start och undersida) som ägaren dömer blint i dashboarden, som hålls undan från nivåfilen och granskartexten, och ett nytt försök på dem; dessutom omfångning av K03/K01/K04.
