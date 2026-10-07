# Beslut 2026-10-01: börja om smått

Ägaren godkände planen "med automode mandat" efter en pratstund om Nortropic. Planen i sin helhet:
`~/.claude/plans/vi-beh-ver-en-pratstund-partitioned-kitten.md` (lokal fil).

## Ägarens ord, ordagrant, i ordning

- "Projektet är nog för ambitiöst eller optimistiskt. Du och Codex arbetar hela dagarna med ändringar och detta blir inte bra."
- "Det här är mitt andra projekt att bygga Nortropic, jag har försökt i 6 månader men börjar inse att det inte är rimligt lägga hela dagar på ändringar och så kommer vi aldrig i mål. Däremot har jag lärt mig mycket."
- "Digitalas vision var att göra hela webbutvecklande med allt som hör till ett repeatable system istället för att varje ny hemsida är ett manuel kognitiv långsamt projekt."
- "Jag vill ha kvalité, annat arbete har jag och jag är en big believer att vi kan automatisera allt enligt webbutveckling praxis tillsammas med verktyg, professioner, skills och ja allt."
- "När man har ett sådant flöde som fungerar då kan man börja blicka mot kunder, vi måste ha en produkt klar innan man kan gå till kunder"
- "Min vision är ju att ta hur man bygger en sajt åt en verksamhet som du skriver här ovan och sedan köra detta flöde mot fiktiva företag inom alla branscher och på sådant vis bygga ständig förbättring på riktig data."
- "Jag kommer sist i flödet där jag ser på slutrapporten och hemsidan och säger bra eller dåligt tillsammans med feedback"
- "det är förbättringsagenten som tittar på vad vi har och kommer med förbättringar men det har spårat i storlek då göra förbättringar hela dagen, min tanke var ju kirurgiska ingrepp med skills, professioner osv som saknas för att ta oss från OK till världsklass"
- "norrglänta är historik, den var undermålig, ai slope skit"
- "Alltså, det är ju bara scrapa riktiga verksamheter och testa bygga hemsidor mot de för att se om vi kan bygga kvalitativa sidor"
- "Ska vi bygga om nortropic från grunden och göra det rätt?"
- "Jag vill ha en Kirurg oaka förbättringspartner eller bollplank med innovation som jag kan mata med githubs som tittar på den här kedjan och förbättra den."
- "Det finns massvis med saker som UX UI max pro och andra "skills" som höjer kvalitén eller hur man arbetar med webbutveckling som jag vill kunna skicka och man tittar, är detta nåt för oss för att göra vårat flöde och hur vi arbetar ännu bättre"
- "Youtube är en bra informationskälla också"
- "jag tänker även med playwright så skulle kirurgen kunna se filmen och ta anteckningar också om möjligt på youtube alltså"
- "vi kör på detta, jag godkänner med automode mandat"
- "döp repot till nortropic-webb-pro*"

## Beslutet

Nej till att bygga om från grunden, ja till att börja om smått. Ett nytt, litet repo med:

- litteraturens åtta steg som skillen `bygg-sajt` (upptäckt, definition, innehåll före form, design, bygge, prov,
  rapport, dom);
- Digitalas kunskapstexter och fristående kontroller kopierade in (`kunskap/`, `kontroller/`, `kritik/`);
- en stoppvakt som håller varje körning kvar tills kontrollerna är gröna (loop 1);
- skillen `kirurg` som bedömer det ägaren skickar mot såren i `LARDOMAR.md` (oftast nej);
- en pilot: en bransch, en stad, tre riktiga verksamheter, två veckor. Ägaren ger bransch och stad och dömer varje
  bygge; referenserna hittar bygget själv (se tillägget nedan).

Riktiga verksamheter i stället för fiktiva, eftersom fiktiva företag inte har något specifikt att säga och därför ger
slop. Playwright används inte mot YouTube; transkriptet hämtas med `kontroller/youtube.py`.

## Tillägg samma kväll

Ägarens ord, ordagrant:

- "inte privat repo, public"
- "vi har väl redan en antislop regel och jag vill ha ett dashboard för allt detta"
- "och vadå referens sajter? det tar du ju reda på själv"
- "ja, det skulle hjälpa om jag får ett frågeforumlär efter ett bygge med åsikter som besvarar det du undrar för träningsdata på bästa sätt"
- "är kirurgen med youtube skillen på dashboard också, viist?"
- "Jag vill att den är utformad som förbättringsagenten så det blir en vilande backlog per automatik av allt som upptäcks som är aktuellt för oss så jag kan starta en claude session och peka den på backloggen och säg börja implementera enligt backlog"

Genomfört:

- Repot är publikt (`Nortropic/nortropic-webb-pro`).
- Antislop: utkastet togs bort. Den befintliga regeln, ur den gamla skillen nortropic-antislop, gäller:
  `kunskap/copy-kontroll.md`, `kunskap/redaktionellt-pass.md`, `kunskap/referenser-professionella.md`.
  Copykontrollen är rapport, inte grind, som dess egen text kräver.
- Referenserna hittar bygget själv i steg 3 (`kunskap/referensjakt.md`), öppnar dem och jämför i steg 5.
- Dashboarden (`./dashboard.sh`) med frågeformuläret efter varje bygge: kärnfrågor som går att jämföra över byggen
  plus byggets egna frågor. Svaren blir träningsdata i `kunder/<slug>/DOM.json` och `LARDOMAR.md`.
- Vilande backlog (`backlog/`), automatiskt fylld av kirurgen, domarna och byggena; skillen `backlog` genomför den
  när ägaren säger "implementera enligt backlog". Kirurgen nås från dashboarden.

## Det gamla, fryst (inget raderat)

- Förbättringspartnern stoppad 2026-10-01 17:35Z med `tools/partner.py stopp` (inga pågående turer, inga levande
  startvaktssessioner). Den startar igen vid nästa inloggning genom LaunchAgent `se.nortropic.partner`, om inte ägaren
  kör `launchctl bootout gui/$(id -u)/se.nortropic.partner` i sin egen Terminal.
- Codex-autopiloten var redan avstängd (sedan augusti).
- Runtime-daemonen rörs inte. Kontoret får inga nya poster under piloten. Inga repon, grenar eller worktrees raderade.

**Borttaget 2026-10-02.** Ägarens ord: "jag tänker vi har mycket gammalt nortropic och annat att ta bort och frigöra då
detta är det korrekta projektet"; valet "Gamla repona helt" och "jag ger dig full tillåtelse och mandat att ta bort
det där". Runtime-tjänsten, Temporal och workern stoppades; Nortropic Runtime, nortropic-projektkontor,
nortropic-digitala och kund-demo-norrglanta togs bort lokalt med sina arbetskopior (cirka 21 GB). Hela git-historiken,
också de lokala grenarna, ligger som verifierade bundles i `~/Arkiv/nortropic-gamla-20261002/` med två patchar för
ocommittade ändringar och de tre LaunchAgents som pekade in i repona. GitHub-repona finns kvar. Kundstart står kvar.
**Delvis ersatt 2026-10-06:** bundlarna raderades med resten av `~/Arkiv`, och Kundstart togs bort (ägarens ord under
städregeln nedan). Det som pushades finns kvar i GitHub-repona; bundlarnas lokala grenar och de två patcharna för
ocommittade ändringar finns inte längre. Kundstarts alla grenar var pushade. Övrigt gäller.

## Vad som inte görs

Inga ändringar i Runtime, kontoret eller Digitala. Inga nya mekaniker, kvitton, förseglingar eller granskarprofiler.
Ingen agent som arbetar obevakat på systemet. Inget utskick till verksamheterna. Ingen publicering av demosajterna.

**Ändrat 2026-10-02:** "Inget utskick till verksamheterna" ersätts av tillägget nedan. Demosajterna publiceras
fortfarande inte.

## Tillägg 2026-10-02: prospekt, spanare och utskick

Ägarens ord, ordagrant:

- "Jag vill bygga en scraper som ersätter manuellt söka efter klienter. Systemet ska hitta businesses och checka deras
  hemsidor för vanliga problem som slow speeds, weak SEO, poor mobile design."
- "Jag vill även att systemet kan scrapa internet på ai webbutveckling för att hjälpa mig identifiera och utveckla mitt
  system till att bli så bra som möjligt enligt metoder, litteratur, principer, ja helt enkelt best practices."
- "Jag tänker mig kanske att https://github.com/Panniantong/Agent-Reach och https://github.com/firecrawl/firecrawl kan
  vara bra för oss. Du får givetvis websearcha, söka och omvärldsbevaka ifall det finns andra verktyg eller github
  repos, dokumentation för det."
- "Apollo för leads, swokei för website analys, outreach campaign."
- "Slutprodukten ska landa i min dashboard vi har (Nortropic webb-pro) http://127.0.0.1:4771/"
- "Think hard, iterate, make no mistakes."
- "jag vill bara nämna att vi har i en gammal repo, verkstadsgolvet en slags google business scraping med places"
- Om publicering på Vercel, tidigare samma dag: "Okej, då väntar vi med det"

Ägarens val på fyra frågor i planeringen (alternativen ordagrant):

- Utskick: "Utkast + du godkänner, sänds via Resend".
- Upptäckt och webbadress: "SCB-nyckel + DuckDuckGo + egen crawl".
- Apollo och Swokei: "Förebilder, vi bygger eget".
- Spanaren: "Veckovis automatiskt, du klickar 'ta in'".

Beslutet: ett prospektflöde och en spanare i dashboarden (`kontroller/prospekt.py`, `dashboard/prospekt.py`,
`kontroller/spana.py`, `kontroller/brev.py`, `kontroller/utskick.py`). Reglerna, som också står som referens i
`kunskap/prospekt-och-utskick.md`:

- Upptäckten bygger på SCB:s allmänna företagsregister (avgiftsfri nyckel) och verksamhetens egen webbplats. Innehåll
  från Google Places lagras aldrig (Googles villkor; det var ett av skälen till att verkstadsgolvets leads-modul
  stoppades 2026-08-24). Inga betaltjänster.
- E-post och sms går aldrig till en fysisk person, alltså aldrig till en enskild firma (marknadsföringslagen 19 §).
  Där ringer ägaren eller skriver brev. SCB:s reklam-, e-post- och telefonspärrar respekteras.
- Ägaren godkänner varje brev i dashboarden. Grinden i `utskick.py` släpper inget annat, och ingen miljövariabel
  öppnar den. Ingen automatisk utskickning, någonsin.
- Varje iakttagelse i ett brev bygger på det vi mätt och sett (`PROSPEKT.json` och skärmbilderna). En siffra som
  inte finns i faktalistan stoppar utkastet. Inga påhittade förevändningar.
- Prospektdata ligger i `underlag/`, utanför git. Gallring tolv månader efter sista kontakt om verksamheten inte
  blivit kund. Den som svarar "avregistrera" stryks samma dag (`underlag/prospekt/SPARR.json` och Resends spärrlista).
- Spanaren körs av dashboarden en gång i veckan utan modell och visar kandidater; varje kirurgintag startar ägaren.
- Demosajterna publiceras fortfarande inte: ett brev länkar inte till en demo utan bjuder in till femton minuter.

## Tillägg 2026-10-03: kopiera gärna referensen, lägg sedan vårt på det

Ägarens ord, ordagrant, efter att Refero och Mobbin anslutits: "ta bort att vi aldrig ska kopiera palett, layout
eller typsnitt, det är helt okej men sedan lägga våra touch och verksamhetens material på det".

Beslutet: förbudet mot att kopiera layout, palett och typsnitt är borttaget. En referens (Refero, Mobbin, en verklig
sajt) får bära formen som utgångspunkt; det som gör sajten verksamhetens är vår touch och deras eget material
(bilder, ord, plats, "Bara de har") ovanpå. Referensen namnges i KONCEPT.md eller JAMFORELSE.md; identitet, texter
och bilder kopieras fortfarande inte; `UPPTAGNA-VAL.md` visar vad tidigare byggen redan lånat, så att två kunder
inte får samma riktning av vana. Ändrade texter: `kunskap/referenser-professionella.md`, `kunskap/referensjakt.md`,
`kunskap/brief-mall.md`, `kritik/GRANSKARE.md` (originalitet), `kritik/BEDOMNING-v2.md`,
`.claude/skills/bygg-sajt/SKILL.md` (steg 5, punkt 1 och 5) och ateljéns prompt i `kontroller/atelje.py`. Kirurgens
register (`kunskap/REGISTER.md`) citerar den gamla regeln i daterade bedömningar; de står kvar som historik.

## Tillägg 2026-10-03, kväll: tre svar på Codex ägarfrågor

Ägarens ord, ordagrant: "Ja enligt dina rkeommendationer till alla tre, vänta med nästa steg då vi fortsätter
revisioner med codex". De tre rekommendationerna är därmed beslut:

1. **Personuppgifter i det publika LARDOMAR.md.** Originaldomen sparas ordagrant i `underlag/LARDOMAR-original.md`
   (privat, utanför git) och i `kunder/<slug>/DOM.json`. Den publika `LARDOMAR.md` behåller betygen, valen, lärdomen
   och ändringen, med företagsnamn men utan privatpersoners namn, telefonnummer, adresser och hälsa; det borttagna
   står i hakparentes. Dashboarden skriver nya domar så (`dashboard/server.py`), backlogposten citerar ingen fritext,
   och sessionen som gör textändringen skriver lärdomen. Byggare, ateljé, granskare och gruppering läser den privata
   filen när den finns; granskaren får fortfarande bara utdraget utan domen om det egna bygget. De befintliga posterna
   L0–L6, domposterna i backloggen, `kontroller/granskarforsok/facit.json`, `kunskap/GRUPPERING.md` och exempeltexterna
   är avidentifierade i samma commit. Git-historiken på GitHub innehåller fortfarande de gamla versionerna; att skriva
   om den är ett eget beslut.
2. **Oberoende belägg för granskarna.** Ägarens blinda val i dashboardens jämförelser är måttet på om byggena blir
   bättre, loggade över byggena i AB-posterna i `LARDOMAR.md`. Ingen granskarpanel ur en annan modellfamilj förrän en
   riktig kund är på väg (vilande backlogpost).
3. **Mikroprovens räckvidd.** Backlog-skillens mikroprov belägger bara den lokala rättningen. Generell förbättring döms
   enbart i blind A/B av hela byggen (`.claude/skills/backlog/SKILL.md` steg 4).

Nästa steg, omstarten av A/B-kedjan, väntar: revisionen med Codex fortsätter först.

## Tillägg 2026-10-04: referenssteget, designprovet, ägarmandatet

1. **Referenssteget** (efter Codex R31). Ägarens ord: "Kör referenssteget enligt backloggen, med avgränsad
   inspektion, verifierat fullständiga fångster och möjlighet till versionsstyrda kompletteringar. Referensvalet ska
   utgå från kundresearchen. Byggare, ateljé och granskare ska få samma frysta paket. Därefter prövar vi designnyttan
   under fryst metod." Gallerierna som sökingångar: Awwwards, SiteInspire, Godly, Land-book, Mobbin och Refero (de två
   sista via MCP). Byggt som `kontroller/referens.py` och `kontroller/referenstjanster.py`.
2. **Designprovet.** Ägaren såg bygge 4 och underkände utseendet kraftigt (förmedlat i Codex R40). Uppdraget före
   nästa helbygge, i sex punkter: verifiera referenstjänsternas anrop och bildleverans; välj en sammanhängande
   huvudreferens för komposition, typografi, proportioner och bildbehandling; ta fram tre renderade startsideförslag
   med kundens verkliga material på mobil och dator och bedöm hela sidan; urvalet får förkasta samtliga, och bäst av
   tre undermåliga förslag blir aldrig godkänt; bevara vinnarkoden och jämför fortsatt implementation visuellt mot
   den; använd ägarens befintliga ankare, och frånvaro av gradienter, ikoner eller kort är inget kvalitetsbevis.
   Byggt i ateljén (`kontroller/atelje.py`), provet (`kontroller/prova.py`, vinnarjämförelsen), granskaren och
   dashboardens designprovsvy.
3. **Ägarmandatet.** Ägarens ord: "Du har fullt autonomt mandat nu att arbeta med nuvarande och Codex verbatims saves
   som du gör. Du behöver inte skicka till codex fram och tillbaka." Codex genomgångar 2026-10-04 (överföringen
   referens → gestaltning, helhetsbedömningen i tio punkter, intagen, skillkandidaterna) är programmet och står som
   backlogposter; varje sammanslagning föregås av en oberoende granskning (en granskande session som läser ändringen
   mot färdigkriteriet) i stället för ett Codex-varv. Det som kräver ägarens omdöme (blinda domar över designförslag
   och kalibreringsexempel) förbereds i dashboarden.

## Tillägg 2026-10-05: designen börjar om med en startsidesprototyp

Ägaren förmedlade Codex dom över designprovets andra omgång: alla tre förslagen underkänns mot den beställda nivån.
Rubriken tog över, bildvalet bar mer än det klarade, luft och hierarki samverkade svagt, och förslagen varierade för
lite i grundidén. Orsaken låg i arbetsflödet: formgivaren kunde inte se sina egna sidor innan panelen dömde dem, så
loopen rendera, titta, rätta och titta igen saknades. Huvudrubriken var dessutom föreskriven i innehållsunderlaget.

1. **Försöksbyggena arkiveras, inget raderas.** Alla byggen före prototypen flyttas ut ur arbetsytan till
   `~/Arkiv/nortropic-webb-pro-forsok-20261005/`. De är felsökningsunderlag, aldrig designankare eller mallar.
   (Raderade 2026-10-06 med resten av `~/Arkiv`, ägarens beslut i städregeln nedan.)
   Verksamhetens verifierade fakta, originalbilder, logga och ägarens domar behålls, liksom infrastrukturen och
   kontrollerna. Tidigare rubriker, layout och designbeslut får omprövas.
2. **Skaparen ser sitt arbete.** `kontroller/forhandsvisa.py` bygger sajten och fotograferar en sida i 390 och 1440
   med mätningen; skaparen kör den själv, läser bilderna och rättar inom samma session. Ateljéns skapare och
   prototypens skapare har det steget.
3. **En startsidesprototyp före fler hela byggen.** `kontroller/prototyp.py` gör en startsida i varv, med verifierade
   fakta och originalmaterial men utan ärvd layout eller låst rubrik; text och form bearbetas tillsammans och
   sakuppgifterna ändras inte. Före och efter visas bredvid huvudreferensen i dashboardens vy Prototyp. Ägaren dömer
   prototypen innan något helt bygge startas.

## Tillägg 2026-10-05: ett skapandeflöde i stället för tre

Ägaren förmedlade tre Codex-texter samma morgon, efter den första startsidesprototypen. Det fanns tre designflöden:
det ordinarie bygget, ateljén och prototypen. Förbättringarna följde inte med mellan dem, och gamla designbeslut låstes
tidigt. Prototypens omtag matades med förra försökets huvudreferens, inklusive "oxblod som här blir falurött". Skaparen
läste inga designskills, ingen oberoende kritik kunde förkasta grundidén, och ägarens dom fördes inte vidare.
Bildkvittot räknade läsningar över hela sessionen. Rådet om en huvudreferens korrigerades: sammanhållningen ska följa
ett välgrundat val, och iterationen ska kunna ändra grundidén.

1. **Ett skapandeflöde** (`kunskap/skapandeflodet.md`): ateljén är orkestratorn för både byggets steg 5.1 och ägarens
   prototyp. Flödet utforskar skilda grundidéer, var och en på sin egen huvudreferenskandidat. Panelen väljer eller
   förkastar alla. Den valda förfinas med designskillsen i förhandsvarv och döms före mot efter av samma panel.
   `kontroller/prototyp.py` är ett alias, och ateljén är standard i `kor.sh`. **Delvis ersatt av:** tillägget
   2026-10-05, eftermiddag (kandidatflödet är standard, och ägaren väljer och godkänner); kor.sh kör ingen ateljé utan
   tar vid från en godkänd startsida (`kunskap/skapandeflodet.md`). Övrigt gäller.
2. **Ägarens dom följer med och återöppnar beslut.** Domloggen `underlag/<slug>/DESIGNDOMAR.jsonl` och
   riktningshistoriken går in i varje prompt. Ny riktning arkiverar designbesluten (urval, koncept, presentationsfiler)
   ur arbetsytan, utan att radera något; fakta står kvar. Inget färgförbud: ett drag ur en underkänd grundidé behöver
   skäl. **Delvis ersatt 2026-10-06:** ny riktning raderar designbesluten i stället för att arkivera dem, efter att
   historiken fått domen (ägarens ord under städregeln nedan). Övrigt gäller.
3. **Research på begäran** genom det befintliga referenssteget (KOMPLETTERING.json), och körspåret redovisas ur
   transkripten: metoden före första skrivningen och läsningen per varv i ordning.
4. **Överlämningen:** ägarens godkännande i vyn Prototyp skrivs i VINNARE.json, och bygget tar vid därifrån som från
   ateljévinnaren. Ett sandlådat bygge kräver en godkänd startsida, eftersom skapandeflödet körs utanför sandlådan.
5. **Nästlade sessioner** skriver aldrig i ägarens automatiska minne (`kontroller/nastlad.py`). Prototypens skapare
   hade skrivit om minnesindexet.
6. **Inga helbyggen** medan backloggen stäms av mot koden och det sammanhängande paketet för designflödet och
   byggvägen färdigställs (Codex via ägaren, tredje texten).
7. **Efter omgranskningen** (Opus, samma dag): ägarens domar via Codex väger som domarna i vyn, och båda vägarna
   prövar godkännandet innan domen skrivs. Domloggen låses under bygget, och en ändring där ger slutkod 3. Säger
   ägarens senaste dom putsa eller ny riktning, startar inget bygge. Ateljéns byggen av skaparens sidor körs innanför
   processgränsen, och paket installeras bara med `kontroller/typsnitt.py`, eftersom sidorna är kod som körs vid
   bygget. Inget i ateljén raderas vid en återupptagning; det flyttas till `atelje/foregaende/`.

## Tillägg 2026-10-05, eftermiddag: cirka tio prototyper, ägaren väljer

Ägaren stoppade den skarpa körningen i Luleå ("Stopp, detta duger inte") och förmedlade Codex samlade uppdrag: flödet
ska ge ägaren flera trovärdiga, genomarbetade alternativ med kundens riktiga information att välja bland, i stället för
att en panel väljer en riktning åt ägaren. Samma eftermiddag tillade ägaren att alla skills ska installeras fullt, också
UI UX Pro Max, och att krockarna mellan dem ska identifieras och avgöras så att helheten följer best practice. Ägarens
ord står ordagrant i minnet; Codex text är det samlade uppdraget.

1. **Kandidatflödet är standard** (`kontroller/kandidater.py`, `kunskap/skapandeflodet.md`): research, plan, cirka tio
   kandidater i egna projekt och egna skaparsessioner, granskning med en förbättringsrunda, jämförelse mot falsk
   variation, och sedan ägarens val. Panelen granskar och rekommenderar men utser ingen vinnare, och dess omdöme visas
   för ägaren först efter ägarens första beslut. Den äldre utforskningen med tre riktningar finns kvar som nödväg
   (`NWP_KANDIDATFLODE=av`). **Delvis ersatt av:** tillägget 2026-10-05, kväll (skissläget): före ägarens val ingen
   granskningspanel, förbättringsrunda eller jämförelse; det förvalet finns kvar som läget full. Övrigt gäller.
2. **Ägarens val binds till kandidat och version** i domloggen (valj, jamfor, forkasta, ny_riktning, putsa, godkand,
   och det ägaren gillade per kandidat). Valda kandidater förfinas var för sig med DESIGN.md i takt med koden; ägaren
   godkänner en för helbygget, och alla dess sidor blir vinnaren som bygget tar vid från.
3. **Reglerna i fyra slag** (`kunskap/designregler.md`): kvalitetskrav binder, ägarens och Nortropics beslut gäller inom
   sin räckvidd, kundens behov ur underlaget bestämmer vad sidan måste klara, och designhypoteser (bland dem mobilens första vy ur
   A/B 2026-10-02) är utgångspunkter som en riktning får lösa annorlunda med skäl. Ingen fast sektionsordning.
4. **Referenstjänsterna förs vidare utan förlust:** varje Refero-stils hela dokument, skärmarnas hela bilder (inte
   tumnageln), flödenas steg och tjänsternas svar ordagrant sparas i underlaget, och den förra undersökningen arkiveras.
   Tjänsterna får bara branschen, aldrig kundens namn eller andra uppgifter (förra körningen skickade namnet i Mobbins
   task_intent).
5. **Skillsen installerade fullt** (40 nya mappar, KALLA.md och licens i varje, kontrollerade mot källan): krockarna
   avgörs i en metodkarta (`kunskap/metodkarta.md`) efter ordningen i designregler.md; skillsens standardråd står
   sist.
6. **Öppet för ägaren:** tjänsternas villkor (Mobbin om cachning och arkivering, Refero om dataset och
   modellutvärdering) mot att vi sparar deras bilder och svar lokalt som arbetsmaterial. Ingenting av det ligger i git
   eller publiceras.

## Tillägg 2026-10-05, kväll: full verktygslåda, ren arbetsbänk (skissläget)

Ägarens uppdrag 2026-10-05 16:25Z (ordagrant i minnet): förenkla skapandeflödet så att vägen till professionella,
tydligt olika kundanpassade förslag blir kortare, med kvalitetsribban kvar, och kör ett första avgränsat skissprov.

1. **Skissläget är standard** i kandidatmotorn (`kontroller/kandidater.py`, `kunskap/skapandeflodet.md`): cirka tio
   skisser (första vyn, den viktigaste sektionen, navigationen, mobil och dator), högst tre samtidigt, 30 minuter per
   inledande försök med verktygsväntan, ett omförsök bara vid ett identifierat tekniskt fel, inget fast antal varv.
   Ingen granskningspanel och ingen förbättringsrunda före ägarens val; snabba objektiva kontroller markerar brister.
   Fördjupningen (hela startsidan, undersidan, besökarens centrala flöde, DESIGN.md) kommer efter ägarens val.
   **Delvis ersatt av:** tillägget 2026-10-06 om kreativ frihet (punkt 5; commit `a593ada`): ett inledande försök har
   45 minuter, med den kritiska granskaren och skaparens svar inräknade. Övrigt gäller.
2. **Ren arbetskontext:** varje skapare får uppdraget, kundens verifierade fakta och material, referensbilderna,
   kundens aktuella domar och metodens kärna med en förteckning att slå upp i. `LARDOMAR.md`, det privata originalet,
   riktningshistoriken och beslutshistoriken bevaras och slås upp när de besvarar en konkret fråga
   (`kunskap/designregler.md`, historik och smakdomar). `CLAUDE.md`, som laddas i varje nästlad session, och
   helbyggets uppstart (bygg-sajt) säger detsamma.
3. **De nästlade sessionerna går på prenumerationen:** API-nyckel, token och bas-URL följer aldrig med till dem
   (`kontroller/nastlad.py`).
4. **Tillfällig växel:** `NWP_KANDIDATLAGE=full` ger det tidigare förvalet med granskning och förbättringsrunda, för
   jämförelse och återställning. Den tas bort när ägaren dömt skissläget; blir skissläget kvar ersätter det förvalet.

## Tillägg 2026-10-05, kväll: kompetensen aktiv, alla skills och MCP:er

Ägarens ord 2026-10-05 18:15Z (ordagrant i minnet): "GUD FÖRBANNAT, du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA,
SE TILL ATT ALLA ÄR UPPDATERADE, CLAUDE OCKSÅ". Strax före hade ägaren förmedlat Codex iakttagelse att skissprovets
skapare hoppat över specialistkunskapen, eftersom flödet stängt av skillupptäckten och gjort utdragen frivilliga.

**Delvis ersatt av:** tillägget 2026-10-05, sen kväll (punkt 1 och 3 nedan: rollerna har en kärna och alternativ,
passen före ägarens val togs bort, och bildregeln skiljer dokumenterande bilder från illustrativt material). Övrigt
gäller.

1. **Varje kompetens har en obligatorisk uppgift** (`kunskap/metodkarta.md`, Kompetenserna; `kontroller/kompetens.py`):
   art direction, typografi/layout/bild, UX och innehåll, interaktion och rörelse, mobil och tillgänglighet, visuell
   kritik och slutbearbetning, och designsystemet i fördjupningen. Impeccables arbetsflöde är förebilden; varje pass
   läser sina skills hela och visar före och efter i den renderade sidan. Ett pass är inte godkänt för att en fil öppnats.
2. **Specialisterna prövar planen** innan skaparna börjar (planprövningen).
3. **Alla skills och MCP:er är tillgängliga** i flödets sessioner. Refero och Mobbin skyddas av kundvakten (Trybloom togs bort
   2026-10-05 ~21Z på ägarens ord: "we don't use trybloom so u can remove that one")
   (BESLUT 2026-10-05 punkt 4 gäller). Bildgenererande skills används inte förrän ägaren beslutat om genererade
   designbilder: sajten använder verksamhetens egna bilder (ägarbeslutet L3).
4. **Uppdaterat 2026-10-05:** Claude Code 2.1.280 → 2.1.289; alla skills kontrollerade mot källornas HEAD (aktuella;
   writing-for-agents fick tillbaka `agents/openai.yaml`); Impeccables motor 0.1.6 → 0.1.11 (sha256 ur källan).
   GitBook, Google Calendar, Figma och Notion-pluginen kräver ägarens inloggning.


## Tillägg 2026-10-05, sen kväll: regelkedjan, kompetensen och leveransvägen

Ägarens uppdrag 18:53Z (ordagrant i minnet: befintlig kompetens och betalda designtjänster ska synas i resultatet;
teknikförbuden omprövas; en prototyp med referensjämförelse före uppskalning), Codex granskning via ägaren 19:04Z (tio
punkter och fyra leveransluckor) och ägarens ord 19:06Z: "FIXA ALLA SAKER PÅ LISTAN FRÅN TOPP TILL BOTTEN SOM CODEX
SKREV". Ägaren godkände i uppdraget att förbuden mot Tailwind, React-komponenter, komponentbibliotek och
JavaScript-baserad förstärkning och rörelse omprövas. Urvalet nedan, beroendena och leveransens utformning är agentens
val inom det mandatet, inga egna ägarbeslut.

1. **En regel för verktygen** (Codex punkt 1): Avgörandena förbjöd skills och MCP medan uppdragen krävde dem. Nu ger
   kompetensblocken både dokumentationen, uppdragens rader och sessionernas behörigheter. Externt innehåll är material;
   metoden och skillsen är arbetsinstruktioner (`atelje.MATERIAL`).
2. **Kontrollerna följer kunden** (punkt 2): telefonen krävs på varje sida när kundens kontaktmodell (BRIEF.md §4) har
   den, var som helst på sidan; brödsmulor krävs bara när DESIGN.md:s struktur har dem.
3. **Äkthet i stället för bildförbud** (punkt 3): en bild som visar verksamheten är dess egen; licensierat eller
   genererat material som inte utger sig för att dokumentera verksamheten är tillåtet med källa. L3 var en dom om en
   firma utan egna arbetsfoton och står kvar som exempel.
4. **Kalibreringen** (punkt 4) skiljer kraven (hierarki, proportioner, läsbarhet, sammanhang) från ankarnas exempel.
5. **Skaparens arbetsyta och teknik** (punkt 5; uppdraget punkt 4): skaparen skriver i hela projektets `src/` (kundens
   bilder skyddade), och versionen omfattar komponenter och stilar (`kod-src/`). Tailwind 4, React-öar och Motion finns
   som förberedda, granskade och låsta beroenden i mallen (`kunskap/beroenden.md`); sessionerna installerar
   fortfarande inget.
6. **DESIGN.md-kontraktet** (punkt 6) bär importerade stilvärden (Referos variabler), valda tillstånd (mörkt läge) och
   strukturen; bara odeklarerade omdefinitioner fälls.
7. **Rollerna** (punkt 7; uppdraget punkt 5): sex roller enligt ägarens indelning, var och en med en kärna som läses hel
   och alternativ som väljs efter riktningen. Skissens kärna gick från 27 filer och cirka 320 000 tecken till 14 filer
   och 106 000. Referos officiella skill (`refero-design`, referenslås och beslutsliggare) och Hallmark (makrostrukturer,
   komponentkatalog, slop-test) är intagna med KALLA.md.
8. **Inga redigerande pass före ägarens val** (punkt 8): skaparen tillämpar rollerna i en sammanhängande skiss; efter
   fördjupningen gör interaktion och rörelse samt tillgänglighet och visuell granskning ett pass var.
9. **Passen redovisar tre saker** (punkt 9): koden som ändrades, beteendet som prövades med förhandsvisningens
   interaktionsväg (tangentbord, fokus, hovring, meny, reflow 320, reducerad rörelse) och den visuella bedömningen.
10. **En dom klassas först** (punkt 10): kundbeslut, smakpreferens, metodhypotes eller generell rättelse; bara en
    generell rättelse blir en gemensam regel (backlog-skillen och CLAUDE.md).
11. **Kvarlevorna:** typsnitten mäts mot en budget för hela sajten (300 kB) och Lighthouse, inte mot fasta filgränser;
    beskärningarna i bild.md är utgångspunkter; H1 och nästa sektion prövas mot den godkända designen.
12. **Metodlåset** omfattar rollernas alla filer (87 källor), och metodens hash binder dem.
13. **Leveransvägen** (Codex leveransluckor): `kontroller/exportera.py` gör ett självständigt kundrepo med leveransens
    låsta beroenden (Vercel-adaptern, Blob; en sårbar version av path-to-regexp låst till 6.3.0) och verifierar bygget
    utan Nortropics kataloger. Formulärets serverfunktion (`mall/leverans/forfragan.js`) tar bilder upp till 4 MB, sparar
    privat i Blob före mejlet och mejlar genom Resend. Förhandsvisning och produktion är samma bygge; skyddet är Vercel
    Authentication (lösenordsskyddet är ett betalt tillägg och används inte), för alla driftsättningar före lanseringen
    och Standard Protection efter. Prövat med riktiga HTTP-svar i provprojektet `nortropic-leveransprov` med rökprovets
    fiktiva sajt (`kontroller/driftkoll.py`). Fyndet att produktionsaliaset var publikt under Standard Protection står i
    `kunskap/lansering.md`; aliaset var öppet i cirka tre minuter med den fiktiva sidan innan skyddet ändrades.

## Tillägg 2026-10-05, natt: startkontrollen, det dagliga underhållet och granskningens rättelser

Ägarens uppdrag 19:13Z, 20:27Z och ~20:50Z (ordagrant i minnet) och den oberoende granskningen av regelkedjan och
leveransvägen:

1. **Startkontrollen före varje start** (`kontroller/startkontroll.py`): arbetaren och kor.sh kör den före allt annat;
   den bekräftar verktygslådan, prövar förmågan med små återanvända prov, låser versionerna och skriver startkvittot.
   Ett nödvändigt verktyg som inte fungerar stoppar starten med ett konkret besked.
2. **Det dagliga underhållet** (`kontroller/underhall.py`, från dashboarden): den senaste versionen som klarat våra prov,
   prövad för sig i en isolerad kopia och med hela rökprovet i en egen worktree för huvudversioner och mätinstrument;
   en avvisad version prövas igen först när en nyare kommer; ingenting tas in medan en körning pågår. Python-paketen
   har fått ett versionslås (`requirements.txt`, `requirements-lock.txt`), och Node följer den senaste LTS som Vercel
   stöder. Tabellen per slag står i `kunskap/beroenden.md`, Underhåll.
3. **Trybloom används inte** (ägarens ord ~21:01Z: "we don't use trybloom so u can remove that one"): borta ur
   kompetensblocken och kundvaktens matchning.
4. **Kundvakten tillåter bara flödets egna verktyg** hos Refero och Mobbin (exakta namn), prövar också nycklar, gatans
   namn, telefonnumrets slut och id-fält, och stoppar en tom indata; referenstjänsternas sessioner har samma vakt och
   kan inte läsa filer.
5. **Exportens provbygge** körs innanför processgränsen (inget nät, skrivning bara i kopian, en miljö utan nycklar),
   och en kandidats bygge får skriva bara i den delade node_modules cacher, aldrig i paketen.
6. **Formuläret:** en bild över 4 MB får ett eget besked i formuläret (och prövas redan i webbläsaren), aldrig beskedet
   om saknade fält; driftkollen kräver utfallet demo i förhandsvisningen.
7. **Referos stilpaket** (`kontroller/stilpaket.py`): originalexporten bevaras orörd för sig, variablerna i Referos namn
   och ett Tailwind-tema läggs i sajten, och kundanpassningen skrivs i en egen fil.

## Tillägg 2026-10-06: rensningen inför Nortropic 2.0

Ägarens uppdrag 2026-10-05 ~21:11Z (ordagrant i minnet): en reversibel rensning. Historiken bevaras, men ersatta beslut
och gamla kundspecifika smakdomar styr inte längre automatiskt; verifierade kvalitetskrav står kvar; inget bygge hittills
har varit bra nog, allt har varit generiskt. Inventeringen, klassningen och ändringarna står i
`kunskap/rensning-nortropic-2.md`; vakten `kontroller/styrning.py` prövar vid varje start att gamla regler inte kommit
tillbaka genom instruktioner, utdrag, mallar eller cache. Läget före rensningen är taggen `fore-rensning-nortropic-2`.

Ersatta designregler (ur `kunskap/designregler.md`, bevarade här):

| Ersatt regel | Hade räckvidd | Ersatt av | Varför |
|---|---|---|---|
| "Verksamhetens egna bilder eller ingen bild; inga stockbilder eller genererade bilder (L3: 'hellre inga foton än stock')" | alla kunder | kvalitetskravet Bilder med uppgift och äkthet | L3 var ägarens dom om en firma utan egna arbetsfoton; regeln hade blivit ett förbud mot allt licensierat och illustrativt material |
| "Statisk Astro med sidans egen CSS, ingen JavaScript som inte behövs …" och "I skapandeflödet installeras inga paket utom typsnitt" | dagens erbjudande, skapandeflödet | teknikvalet i tabellen ovan och `kunskap/beroenden.md` | en historisk teknikpreferens utan aktuellt sakskäl; kvalitetskraven (tillgänglighet, prestanda, innehåll utan JavaScript, reducerad rörelse) består |
| "Telefonnumret som tel-länk i sidhuvudet på varje sida" | dagens erbjudande | kundens kontaktvägar ur BRIEF.md §4 | placeringen är riktningens val; en annan fungerande kontaktlösning ska inte underkännas |
| Brödsmulor fälldes av byggstandarden på varje undersida | bygget | DESIGN.md:s struktur avgör | brödsmulor är en designhypotes, inget krav |
| "Sidhuvud på en rad med den primära handlingen som knapp, menylänkarna synliga utan hamburgare, fast list längst ned med den primära handlingen och Skriv, numret högst två gånger i första vyn" (A/B 2026-10-02 och domarna L1, L2, L4, L5) | bygget, som utgångspunkt | riktningens val inom kvalitetskraven (den primära handlingen nås från första vyn, menyn fungerar) | smak ur två byggen; inget bygge hittills var bra nog (rensningen inför Nortropic 2.0, 2026-10-06) |
| "Gatuadressen i sidfoten på varje sida" (7.4; A/B 2026-10-02, L5, L6) | bygget | kontaktsidan och JSON-LD; placeringen i övrigt är riktningens | placeringen var en kunds smak; sanningen och NAP består |
| "Ägarens domar i LARDOMAR.md gäller före allt" (skillsens anpassningar) och LARDOMAR som exempel till skapare, panel och granskare | alla agenter | ägarens aktuella beslut och kundens domar; LARDOMAR är historik med läsförbud | inget bygge hittills var bra nog: domarna över dem är inga förebilder |

## Tillägg 2026-10-06: ägarens fyra beslut (brew update, node@24, Figma, dashboardarna)

Ägarens beslut om de fyra öppna frågorna, 2026-10-06 ~04:52Z, ordagrant (också i minnet). Ordningen är ägarens:
besluten genomförs när granskningen r79, rökprovet och sammanslagningen till main är klara.

> Mina beslut om de fyra öppna frågorna. Spara dem ordagrant i minnet och i BESLUT.md först. Genomför dem när pågående granskning (r79), rökprov och sammanslagning till main är klara. Inget av detta får avbryta det arbetet.
>
> 1. brew update: Ja. Underhållet får köra `brew update` högst en gång per dygn, före versionsuppslagen. Det uppdaterar bara formelindexet och Homebrew självt. `brew upgrade` på allt är fortfarande förbjudet: node, python, git och gh tas in som förut, en i taget och bara efter underhållets prov. Rapporten och startkvittot ska visa Homebrews version före och efter.
>
> 2. node@24: Kör de tunga proven med node@24, med hela rökprovet. Blir det grönt får du ändra rad 6 i ~/.zprofile från node@22 till node@24. Bara den raden. Gör en säkerhetskopia av filen först och visa exakt vad som ändrades. Blir det rött står vi kvar på node@22. Redovisa då felet och låt underhållet pröva igen när en nyare version kommer. Inga andra ändringar i mina skalprofiler.
>
> 3. Figma: Stäng av Figma-pluginen tills vidare, så att startkontrollen slutar rapportera den som otillgänglig. Notera i BESLUT.md att den kan slås på igen om jag loggar in. Detta ändrar inte "använd alla skills och MCP:er" för det som är anslutet.
>
> 4. Dashboards: Stäng de gamla dashboardarna på :4772 och :4773. Rör inte :4771, utan starta om den från main efter sammanslagningen som planerat.
>
> Säg till när allt är gjort, med resultatet av node@24-provet.

Figma-pluginen kan slås på igen när ägaren loggar in i Figma (pluginens MCP kräver inloggning, som en obevakad
session inte kan göra).

**Delvis ersatt av:** tillägget 2026-10-06 om Figma-metodprovet nedan: pilotens sessioner slår på pluginen i sin egen
`--settings`; i användarinställningarna är den fortfarande av. Övrigt gäller.

**Genomfört, punkt 2 (node@24), 2026-10-06 22:25Z:** se tillägget "2026-10-06, kväll: node@24 och flödesvyns rättelse".

## Tillägg 2026-10-06: kreativ frihet och hela kompetensen i designomgången

Ägarens uppdrag 2026-10-06 ~05:37Z (ordagrant i minnet), efter domen över den första prototypen (ny riktning; inget
bygge hittills var bra nog): professionellt gestaltade, kundspecifika förslag som ägaren vill gå vidare med, ur
befintligt flöde med minsta ändringar. Det som ändrades (`kontroller/kandidater.py`, `kontroller/skapande.py`,
`kontroller/referenstjanster.py`, `kontroller/forhandsvisa.py`, `kunskap/metodkarta.md`):

1. **Skaparen har mandat:** huvudreferens och riktning, berättelse och ordning, komposition, bildstorlek och beskärning,
   typografiska kontraster, typsnitt och vikter, färg, detaljer, interaktion och rörelse får skaparen ompröva med skäl.
   "En font, en vikt, inga accentfärger, små bilder eller en viss standardlayout är inte ägarkrav för denna omgång."
   Kundfakta, besökarens uppgift, tillgänglighet, integritet, säkerhet, rättigheter och kundens identitet gäller.
2. **Planen formulerar en idé och vad den prövar,** aldrig exakta typsnitt, vikter, färgkoder, mått eller antal rader;
   formfälten står i uppdraget under "Förslag som du får ompröva". Huvudreferensen är ett förslag.
3. **Tidigare domar och kalibreringen** gäller det de uttryckligen beslutar och blir inga formregler; kalibreringen är
   uppslag, inte före-läsning, och citeras aldrig som riktning.
4. **Forskningen** söker utifrån kunden, besökarnas behov och olika uttryck, aldrig efter en bestämd form; både Refero och
   Mobbin, utan anrop för antalets skull.
5. **Rendera tidigt och pröva grunden:** första varvet efter renderingen prövar kompositionen och får byta grundidé,
   referens eller komposition; mellanbredden 1280 renderas; en kritisk granskare ser bilderna utan skaparens text och kan
   rekommendera att riktningen förkastas, och skaparen svarar i en egen session.
6. **Redovisningen per förslag:** idén och relevansen, de faktiska referenserna, det som synligt förts över, de
   kvarvarande svagheterna och kompetensernas synliga bidrag. Tekniska kontroller är inget godkännande.

## Tillägg 2026-10-06: observationen av designarbetet (Claude Mods prövades, ingen mod)

Ägarens uppdrag 2026-10-06 ~07:50Z (ordagrant i minnet): en liten, observerande integration som under automatiska
körningar visar referenserna, kompetensen, den aktuella prototypen och arbetsläget i dashboarden, med ärliga etiketter och
utan att observatören ändrar något.

- **Ingen mod och inga nya krokar.** Claude Codes transkript bär redan det som behövs: verktygsanropen och deras
  utfall, läsningarnas omfång (radantal mot filens), skillverktyget, skillistan, nekanden, användningen per modellanrop
  och komprimeringarna. En mod körs i den process som laddar den (`--plugin-dir` eller en installerad plugin) och utanför
  sandlådan. Varje `claude -p`-process, som ateljéns sessioner och tjänstesessionerna, ser bara en mod som laddats i just
  den processen.
- **Underagenter** som en session startar körs i samma process. En mod där får `agent.spawn` när de startar och ser
  deras verktygsanrop (`tool.call`) och modellanrop (`turn.step` och `turn.complete` med `agentId`). Observatören läser
  bara sessionens transkript, och underagentens anrop står i ett eget (`<session_id>/subagents/agent-*.jsonl`, prövat i
  Claude Code 2.1.289), så vyn visar bara Agent-anropet och dess utfall. Ateljéns sessioner har inget Agent-verktyg
  (`--tools` listar bara det sessionen använder). En skill som körs i en egen kontext (`context: fork`) kan ändå starta
  en underagent, och då syns bara skillanropet.
- **Kontexten** i vyn är tokenantalet i senaste modellanropets indata (med cache), med tid och märkt som uppskattning.
  Det som tillkommit efter anropet räknas inte, och andelen av fönstret visas inte, eftersom transkriptet inte anger
  fönstrets storlek; efter sessionen står den i svarsfilen (`modelUsage.<modell>.contextWindow`). En mod kan läsa
  Claude Codes egen siffra (`$.session.usage()`: tokens, fönster och procent). Också den är Claude Codes beräkning och
  inget oberoende mått.
- **Läsfel:** ett transkript eller en logg som inte går att läsa om visar det senast lästa läget med felet och tiden
  för den senaste lyckade läsningen, och vyn säger att det är inaktuellt. En fil som aldrig gått att läsa, och ett
  transkript som inte längre finns, heter "inte observerat" (med felet när det finns).
- **Så går det till:** `atelje.session` ger varje nästlad session sitt id från start (`--session-id`, när
  `claude --help` listar flaggan) och skriver en post med nio valda fält i `underlag/<slug>/atelje/sessioner/`.
  `kontroller/observation.py` läser sessionens befintliga transkript och tjänstesessionernas strömmade loggar stegvis och
  sammanfattar bara metadata; promptar, verktygsargument, svar och bilddata kopieras aldrig, och inga modell- eller
  tjänsteanrop görs. Prototypvyn visar det under "Under arbetet, observerat", med senaste förhandsvarvets första vy.
- **Före ägarens första beslut** visar vyn huvudreferensens namn, aldrig planens beskrivning, som korten.
- **Av:** `NWP_OBSERVATION=av` i arbetarens miljö ger sessionerna exakt samma argument som förut och ingen förteckning.
  Säkerhetskrokarna och kundvakten berörs inte.

## Tillägg 2026-10-06: städregel för arbetskopior, processer och cacher

Ägarens beslut 2026-10-06 ~14:35Z, ordagrant:

> Ägarbeslut: städregel för arbetskopior, processer och cacher. Spara beslutet ordagrant i minnet och i BESLUT.md först.
> Avbryt inte pågående arbete (sammanslagningen, underhållet, designomgången); städa när det inte krockar.
>
> Regeln gäller bara det som flödet eller agenten själv har skapat under ~/nortropic-repos, /tmp och scratchpad.
> Rör aldrig huvudutcheckningens underlag/ och kunder/, ~/Arkiv eller något som ägaren skapat.
>
> 1. Worktrees: när en gren är sammanslagen i main och pushad tas dess worktree bort med git worktree remove
>    (inte rm -rf). Grenen och dess commits finns kvar.
> 2. Kopior av repot (kopia* och liknande): de får finnas bara medan provet som skapade dem pågår. Innan en kopia
>    tas bort: jämför dess underlag/ och kunder/ mot huvudutcheckningen. Det som bara finns i kopian arkiveras med
>    datum i ~/Arkiv/, och sedan raderas kopian.
> 3. Processer: förhandsvisningar och servrar som startats för ett prov (astro preview, dashboards på andra portar)
>    stoppas när provet slutar. En sådan process utan levande ägare som gått mer än ett dygn stoppas.
> 4. Tillfälliga filer: testkataloger i /tmp och scratchpad städas när uppgiften är klar.
> 5. Cacher: npm-cachen rensas när disken är fylld över 85 %, och annars en gång i månaden.
> 6. Diskvakt: under 15 % ledigt körs städningen före nästa bygge, och det rapporteras.
> 7. Redovisning: varje städning skrivs i underhållets rapport (vad, sökväg, storlek, tid, och vad som arkiverades
>    och var). Det som arkiverats går att få tillbaka.
>
> Det här är ett stående mandat att städa enligt punkterna ovan, utan att fråga mig varje gång. Är något oklart
> (okänt ursprung, material som inte går att jämföra) arkiveras det i stället för att raderas, och du frågar mig.
>
> Gör nu:
> a) Lista r68, r69, kopia* och övriga gamla worktrees och kopior med storlek och vad som bara finns där. Stoppa
>    astro preview som körs ur kopia4. Städa sedan enligt regeln, och redovisa före/efter-storlek och diskens
>    lediga utrymme.
> b) Lägg in punkterna 3–7 i det dagliga underhållet (kontroller/underhall.py), med prov i rökprovet som visar att
>    en kopia med eget kundmaterial arkiveras före radering och att huvudutcheckningen aldrig rörs. Granska oberoende
>    och slå samman till main enligt arbetssättet.
> c) Uppdatera CLAUDE.md och kunskap/beroenden.md kort med regeln.

**Delvis ersatt samma dag av ägarens ord nedan:** ingenting arkiveras längre i `~/Arkiv`. Kopior och omtagets
designbeslut raderas. Det som verkar värdefullt (till exempel kundmaterial som bara finns i en kopia) raderas inte, och
då frågar agenten ägaren och motiverar varför. `~/Arkiv` är tömt. Övrigt i regeln gäller.

Ägarens ord 2026-10-06, ordagrant:

- ~14:49Z, om Kundstart och `work/` i `~/nortropic-repos`: "allt som inte är vårat i den mappen kan du ta bort, det
  borde finnas mycket gammalt nortropic skräp på datorn du kan ta bort också"
- ~14:56Z: "Ägarbeslut: radera dagens arkiv, det används inte i driften enligt dig. Om nåt du tycker är värdefullt att
  spara så kan du fråga mig och motivera varför i framtiden. Vi ska inte samla på oss skrot och leftover i onödan."
- ~15:00Z, svar på frågorna om de äldre arkiven i `~/Arkiv`, om omtagets flytt av den gamla ateljén till `~/Arkiv` och om
  de gamla Nortropic-filerna utanför repona: "ja, rensa arkivet och radera den gamla. ja lägg in det som städregeln i
  underhållet. jag ger dig behörigheten och ja låt kofigurationen ligga kvar" (konfigurationen är `~/nortropic`, där
  GitHub-verktyget har sin konfiguration).

Därför raderar ett omtag (`--ny-riktning`) den gamla ateljén i stället för att flytta den till `~/Arkiv`, sedan
historiken fått ägarens dom (`kontroller/atelje.py`, `ta_bort_beslut`). Utan en dom som gäller körningen raderas inget
som ägaren sett, och då stoppas inget heller. Annars avslutas först förra körningens kvarlevande processer (arbetaren och
kundens egna claude-sessioner). Hela `kunder/<slug>/sajt` raderas, också en godkänd och helbyggd sajt; leveransen
(`kunder/<slug>/kundrepo` och tidigare exporter) rörs inte, och en sajt som är ett eget git-repo raderas aldrig.

## Tillägg 2026-10-06: Figma-metodprovet, en pilot utanför normalflödet

Ägarens uppdrag 2026-10-06 ~18:05Z, beskedet om arbetsyta och kundmaterial ~18:48Z och tillägget ~18:50Z (ordagrant i
minnet): ett avgränsat metodprov med Figma som möjlig visuell arbetsyta i skapandeflödet. Figma görs inte obligatoriskt
för framtida byggen innan provet visat att det fungerar och tillför kvalitet.

1. **Tre moment, prövade var för sig:** A, en representativ komposition ur en stark, namngiven referens återskapas
   noggrant med material vi får använda; B, kompositionen anpassas
   till kundens verkliga innehåll och material; C, den valda designversionen överförs till fungerande webb och jämförs
   med webbläsarens rendering i samma bredder.
2. **Bara i piloten.** Normalflödet går utan Figma (`kunskap/skapandeflodet.md`, Figma). Piloten är inte avslutad. Dess
   sessioner slår på Figma-pluginen i sin egen `--settings` och kundvakten slås inte av, men körskripten ingår inte i
   repot, och ingen kod prövar vad som laddas upp till Figma (kundvakten gäller Refero och Mobbin).
3. **Kundmaterialet:** privat kundmaterial laddas upp bara till ett nytt projekt i ägarens team (ägarens val ~18:48Z;
   länken given ~20:09Z), bara för den kund som beskedet gäller, med metadata borttagen (foton utan EXIF och GPS),
   texterna som de står i underlaget och inga uppgifter om privatpersoner utöver det som redan står på kundens sajt.
   Uppdraget ger ingen allmän rätt att föra kundmaterial till externa tjänster.
4. **Inget i leveransen är verifierat genom piloten:** helbygget, exporten, kundrepot och driftsättningen prövas inte av
   den, och dokumentationen markerar dem inte som verifierade.
5. **Dokumentationen:** ägarens ord i samma tillägg: "Rätta grundkällorna och låt andra dokument hänvisa till dem."
   Genomförandet, sessionens fördelning: kedjan från kundunderlag till leverans i `README.md`, designflödet i
   `kunskap/skapandeflodet.md`, kompetensen i kompetensblocken i `kunskap/metodkarta.md` och leveransen i
   `kunskap/lansering.md`.

## Tillägg 2026-10-06, kväll: ett hållbart arbetsflöde (leveransprovet A–C)

**Status:** gäller.

Ägarens uppdrag 2026-10-06 21:31Z, inklistrat och ordagrant (också i minnet):

> Uppdrag: gör Nortropics arbetsflöde ekonomiskt och designmässigt hållbart.
>
> Integrera detta i det pågående Figma- och pilotuppdraget. Återanvänd det som redan finns och undvik parallella ombyggnader av systemet.
>
> Problemet är att vår kedja tar mycket tid och arbete samtidigt som resultaten återkommande inte når min visuella ribba. Vi behöver visa att vi kan leverera hög kvalitet med en rimlig arbetsinsats innan vi skalar upp autonomin.
>
> 1. Utgå från dokumenterade arbetssätt
>
> Läs dessa primärkällor och använd relevanta delar:
>
> Clearleft – ett konkret webbprojekt från innehåll och visuellt språk till formgivning i webbläsaren:
> https://clearleft.com/thinking/making-the-patterns-day-website
>
> Clearleft/Sage – tidsbegränsad utforskning, tidigt urval och fungerande prototyper:
> https://clearleft.com/work/sage-new-concepts-for-product-adoption
>
> thoughtbot – designansvar genom implementationen och löpande webbläsarkontroller:
> https://thoughtbot.com/playbook/design-craft/design-implementation
>
> Finsweet – strategi, sidstruktur, visuellt system, byggande och överlämning:
> https://finsweet.com/agency/design-and-strategy
>
> Relume – sammanhängande komponenter från struktur och design till implementation:
> https://www.relume.ai/export
>
> Basecamp – bestäm tidsbudgeten och anpassa omfattningen:
> https://basecamp.com/shapeup/1.2-chapter-03
>
> Anthropic – erfarenheter av designgranskare, långa agentkörningar och förenkling:
> https://www.anthropic.com/engineering/harness-design-long-running-apps
>
> Skilj mellan dokumenterade arbetssätt, marknadsföringspåståenden och egna slutsatser. Kopiera inte företagens hela processer. Deras projektstorlek, bemanning och mål skiljer sig från våra.
>
> Detta är inte ett uppdrag att köpa fler verktyg eller byta plattform. Vi ska först använda och förbättra det vi har.
>
> 2. Kartlägg var arbetet faktiskt går åt
>
> Undersök befintlig kod och ett litet relevant urval av de senaste körningarnas tillgängliga spår.
>
> Skilj på:
> - arbete som producerar kundens webbplats;
> - forskning och utveckling av Nortropics automationssystem;
> - väntetid och verktygsfel;
> - omarbete efter underkända resultat.
>
> Visa vilka steg som:
> - fattar ett nödvändigt beslut;
> - producerar användbart material eller fungerande kod;
> - upptäcker konkreta fel;
> - upprepar tidigare arbete;
> - saknar belägg för att de förbättrar resultatet.
>
> Redovisa faktisk observerad tid och kända kostnader. Markera uppskattningar och saknade uppgifter. Hitta inte på tokenkostnader för prenumerationskörningar. Behåll vår befintliga modellåtkomst; inför inte betalda API-anrop som en följd av uppdraget.
>
> Gör kartläggningen kort och handlingsinriktad. Den ska leda till pilotprovet, inte bli ännu ett stort revisionsprojekt.
>
> 3. Behåll kompetensen och minska onödigt omarbete
>
> Behåll vår verktygslåda, skills, Refero, Mobbin och övriga fungerande resurser.
>
> För varje moment ska det vara tydligt:
> - vilken kompetens som ansvarar för uppgiften;
> - vilka referenser och vilket kundmaterial den arbetar med;
> - vilket konkret resultat den ska åstadkomma;
> - hur resultatet bedöms.
>
> Installerad, läst, anropad, tillämpad och visuellt lyckad är olika saker. Redovisa dem ärligt.
>
> Använd gemensam research och gemensamt verifierat kundunderlag där det går. Gör ny research när en konkret obesvarad fråga motiverar den.
>
> Låt en tydlig designansvarig hålla ihop komposition, typografi, bildhantering och detaljer genom design och implementation. Specialistkritik ska samlas till prioriterade ändringar. Motstridiga granskarförslag ska inte automatiskt utlösa nya ombyggnader.
>
> 4. Genomför ett avgränsat leveransprov
>
> Återanvänd pilotens tre moment:
> A. Visuell förståelse och utförande.
> B. Kundanpassning.
> C. Överföring till fungerande webb.
>
> Om delar redan är klara och jämförbara ska de återanvändas.
>
> Omfattningen ska vara tillräcklig för att bedöma kvaliteten: en representativ startsidesdel med kundens innehåll i mobil och dator samt en viktig kontaktväg. Välj en del som avslöjar hur typografi, bilder, innehåll och responsivitet fungerar tillsammans.
>
> Fastställ och redovisa en motiverad tidsbudget före körningen. Ange vad den omfattar. Budgeten ska begränsa arbetsinsatsen, inte sänka kvalitetskraven.
>
> Varje ny iteration ska ha:
> - ett konkret observerat problem;
> - en föreslagen förändring;
> - en jämförelse som visar om förändringen hjälpte.
>
> Spara tidigare bättre versioner. Ett högre modellbetyg eller en senare iteration betyder inte automatiskt att resultatet är bättre.
>
> När budgeten är förbrukad ska utfallet redovisas som godkänt, underkänt eller ofullständigt. Förläng inte körningen automatiskt och kalla inte ett underkänt resultat färdigt.
>
> 5. Skaffa en trovärdig jämförelsegrund
>
> Jämför pilotresultatet med en stark, namngiven och relevant referens eller en licensierad designgrund som jag bedömer håller.
>
> Skilj på:
> - att förstå och återge referensens visuella kvaliteter;
> - att anpassa dem till kundens material;
> - att bevara dem i fungerande kod.
>
> Jämför vid samma bredder och med tydliga versioner. Säg vilka skillnader som beror på innehåll, material, avsiktliga beslut respektive brister i utförandet.
>
> Om vi saknar en användbar kvalitetsribba eller om modellen återkommande misslyckas trots tydligt underlag: föreslå ett avgränsat jämförelseprov med en senior mänsklig designer. Ange exakt vilken leverabel vi behöver. Boka eller köp inget utan mitt beslut.
>
> 6. Skala först när riktningen håller
>
> Målet om cirka tio förslag får inte automatiskt innebära tio fullständiga produktionskedjor.
>
> Utforska skilda idéer med den detaljnivå som behövs för att bedöma dem. Koncentrera därefter det dyra detalj- och implementationsarbetet till utvalda riktningar.
>
> Bevara det konkreta godkända arbetet genom överlämningen: designversion, tillgängliga tillgångar, komponenter och kod. Undvik att nästa steg fritt återskapar en redan godkänd design från en textsammanfattning.
>
> Figma ska bidra där det hjälper arbetet. Responsivitet och verkligt beteende ska prövas tidigt i webbläsaren. Vi ska kunna återkoppla mellan design och kod.
>
> 7. Förenkla kontrollerat
>
> Behåll säkerhet, integritet, versionsbindning och relevanta tekniska kvalitetskontroller.
>
> Pröva att förenkla skapandets övriga mekanik en del i taget. Återanvänd befintliga möjligheter till återställning. En förenkling ska bedömas mot både resultat och arbetsinsats.
>
> Tidigare uppdrag om korrekt dokumentation och spårbarhet kvarstår. Återanvänd befintliga kvitton och bilder. Lägg inte till nya dokumentlager eller dashboardsystem som inte behövs för att följa och bedöma piloten.
>
> 8. Leverera ett konkret beslutsunderlag
>
> Visa:
> - pilotens bilder och fungerande resultat;
> - jämförelsen med kvalitetsribban;
> - arbetsinsats per huvudmoment;
> - min arbetsinsats och antal omtag;
> - kvarvarande visuella och funktionella brister;
> - vilka befintliga steg som bör behållas, förenklas eller prövas vidare;
> - vad som är observerat och vad som fortfarande är en hypotes.
>
> Bedöm om problemet främst ligger i underlaget, formgivningen, modellens förmåga, verktygsåtkomsten, överlämningen eller implementationen. Påstå inte en säker orsak utan stöd.
>
> Framgång är att vi får ett konkret resultat som når min ribba, fungerar för kundens viktigaste uppgift och har en arbetsinsats vi kan acceptera.
>
> Leverera och utvärdera det exemplet innan du föreslår större utbyggnad av kedjan.

Genomfört samma kväll. Leveransprovet fick en tidsbudget före körningen (21:35Z–00:35Z) och återanvände pilotens
moment A och B. Moment C, den fungerande webben, fick en kontaktväg och prövades i tio iterationer, var och en med
problem, ändring och jämförelse. En bildförst granskare dömde varje version. Utfallet blev godkänt mot budgetens mätbara
kriterier; ägarens visuella dom återstår. Beslutsunderlaget med bilder, arbetsinsats, källor och kartläggning ligger i
`underlag/figma-pilot/BESLUTSUNDERLAG.md` (privat).

Designomgången med cirka tio förslag körs inte som tio fulla kedjor. Den väntar på ägarens dom över provet.

## Tillägg 2026-10-06, kväll: node@24 och flödesvyns rättelse

**Status:** gäller.

Ägarens två uppdrag 2026-10-06 21:51Z ("När du kan"), inklistrade och ordagranna (också i minnet):

> När leveransprovet är redovisat: genomför mitt beslut från 10-06 ~04:52Z om node@24.
>
> Kör underhållets tunga prov med node@24 från main i en egen worktree, enligt repots underhållsmodell. Kom ihåg att intaget 10-06 ~09:02Z bröt node@22 via simdjson 5. Se till att node@22 fortsatt fungerar under hela provet, och avbryt om Homebrew-uppdateringen bryter befintlig Node.
>
> Om allt är grönt:
> - ta en säkerhetskopia av ~/.zprofile;
> - byt rad 6 från node@22 till node@24;
> - visa exakt diff;
> - kontrollera i ett nytt inloggningsskal att node, npm och rökprovet fungerar.
>
> Om något är rött: ändra ingenting, och redovisa vad som föll och varför.
>
> Rör inte dashboarden på :4771, pilotens sajt eller pågående körningar. Redovisa resultatet i morgonens rapport.

> Rätta flödesvyn i grenen flodesvy-20261006 (worktree r96) utifrån granskningen i scratchpad/GRANSKNING-r96.md. Slå inte ihop och pusha inte.
>
> Rätta B1–B3 och R1–R4, alltså det som gör att vyn kan visa fel status eller bryta blindningen:
> - B1/R1: återanvänd skapande.godkand_giltig och korslut.ar_godkant i stället för egna, svagare kontroller.
> - B2: bind stegen till den aktuella körningen. Tidigare körningars resultat visas som inaktuella, aldrig som kontrollerade eller beslutade.
> - B3: bind pilotens status till version. "Kontrollerat" gäller bara den version som faktiskt granskats, och bilderna märks med version.
> - R2: visa en misslyckad eller pågående förfining rätt.
> - R3: blinda också före det blinda A/B-valet.
> - R4: gör blindningsprovet verkligt, så att det fångar en läcka.
>
> Hoppa över R5–R7. De är nya funktioner och väntar tills piloten är utvärderad.
>
> Är något osäkert ska vyn visa "inte observerat" hellre än att gissa. Bygg ingen ny mekanik där befintliga funktioner räcker.
>
> Kör prov_flode.py och hela rökprovet. Låt sedan en oberoende granskare pröva rättelsen med mutationer. Redovisa i morgonens rapport: vad som rättats, granskningens fynd, och om grenen är klar för min sammanslagning.

**Genomfört, node@24 (beslut 2 i ägarens fyra beslut ~04:52Z):** efter att leveransprovet redovisats, alla tider UTC.

| Steg | Resultat | Belägg (privat) |
|---|---|---|
| Underhållets tunga prov, `underhall.py --bara brew:node`, från main b1348d0, 22:12–22:24 | node@24 24.21.0_1 "prövad och godkänd"; hela rökprovet grönt i en egen worktree med node@24 först i PATH | `underlag/startkontroll/underhall/rokprov-brew-node-node-24-2026-10-06T222350Z.log` |
| Homebrew under provet | ingen ändring: `brew update` kördes inte (senast 08:36), och `brew install` installerade inget | – |
| node@22 under provet | hel genom alla 24 kontroller, var 30:e sekund: alla /opt/homebrew-bibliotek som den länkar mot fanns, utan att node startades | `node24-vakt-2026-10-06T221222Z.log` |
| ~/.zprofile | säkerhetskopia `~/.zprofile.fore-node24-20261006T222532Z`; bara rad 6 ändrad: `export PATH="/opt/homebrew/opt/node@22/bin:$PATH"` → `export PATH="/opt/homebrew/opt/node@24/bin:$PATH"` | – |
| Ett nytt inloggningsskal (`env -i … zsh -l`) | node v24.21.0, npm 11.19.0 | – |
| Hela rökprovet från inloggningsskalet, med underhållets egen worktree-funktion, 22:36–22:46 | grönt | `rokprov-node24-inloggningsskal-2026-10-06T224647Z.log` |

node@22 22.23.2 ligger kvar installerad. Länken som lagade node@22 efter intaget 09:02
(`Cellar/simdjson/5.0.2/lib/libsimdjson.33.dylib` → 4.6.6) ligger kvar.

**Flödesvyn:** rättas i grenen `flodesvy-20261006` (B1–B3, R1–R4) och granskas sedan oberoende med mutationer. Ägaren
slår själv ihop den.

## Tillägg 2026-10-06, kväll: dokumentations- och rapportstrukturen

**Status:** gäller.

Ägarens uppdrag 2026-10-06 22:02Z ("när du har tid"), inklistrat och ordagrant (också i minnet):

> Uppdrag: inför en sammanhängande dokumentations- och rapportstruktur i Nortropic, med automatisk uppdatering som en del av det ordinarie arbetet.
>
> Det ska vara enkelt för mig och agenterna att förstå flödet, hitta aktuella instruktioner, läsa granskningar, följa beslut och se vad som återstår. Bestående information ska inte vara beroende av att någon hittar rätt chatt, temporär katalog eller gammal worktree.
>
> Integrera detta med pågående arbete. Inventera först och återanvänd befintliga dokument, kvitton, register och dashboardfunktioner. Vissa delar kan redan vara genomförda.
>
> 1. Utgå från dessa principer
>
> Läs och använd relevanta delar av:
>
> Diátaxis – dokumentation efter läsarens behov:
> https://www.diataxis.fr/start-here/
>
> GitLab – informationsarkitektur, tydligt ansvar och en auktoritativ källa:
> https://handbook.gitlab.com/handbook/about/handbook-usage/
>
> Michael Nygard – bestående beslut med sammanhang, status och ersättare:
> https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
>
> Write the Docs – dokumentation i samma förändringsflöde som koden:
> https://www.writethedocs.org/guide/docs-as-code/
>
> Tillämpa principerna proportionerligt. Vi behöver inte köpa en dokumentationsplattform eller bygga ett omfattande nytt ramverk.
>
> 2. Inventera och fastställ var information hör hemma
>
> Kartlägg befintliga dokument och rapporttyper. Skilj mellan:
>
> - Start och överblick: hur Nortropic fungerar och var information finns.
> - Gällande arbetssätt: guider, krav, teknisk referens och förklaringar.
> - Beslut: vad som beslutats, varför, räckvidd och om beslutet fortfarande gäller.
> - Förbättringsarbete: uppgifter, ansvar, status och färdigkriterier.
> - Projekt- och körningsrapporter: vad som hände i ett visst uppdrag.
> - Systemgranskningar: vad som granskades i Nortropic och fyndens fortsatta hantering.
> - Bevismaterial: bilder, mätningar, loggar och versionskvitton.
> - Historik och tillfälliga arbetsanteckningar.
>
> Återanvänd README.md, kunskap/, BESLUT.md, backlog/ och befintliga privata projektstrukturer där de passar.
>
> Fastställ en bestämd plats och namngivning för varje informationsslag. Dokumentera regeln på ett ställe och länka till den från relevanta ingångar.
>
> Börja med förteckningar och länkar. Flytta inte frysta underlag eller filer som verktyg använder innan beroenden och versionsbevis har kontrollerats.
>
> 3. Ge varje ämne en tydlig auktoritativ källa
>
> Aktuella instruktioner ska beskriva hur systemet fungerar nu.
>
> Historiska rapporter ska beskriva vad som undersöktes vid en viss tidpunkt. De ska inte automatiskt bli nya gemensamma regler.
>
> När en rapport leder till en förändring ska den länkas till:
> - uppgiften som genomför förändringen;
> - eventuellt beslut;
> - den aktuella instruktion som uppdaterats;
> - verifieringen av rättelsen.
>
> Undvik konkurrerande sammanfattningar som måste uppdateras för hand på flera ställen.
>
> Äldre instruktioner ska märkas med giltighet och eventuell ersättare. Bevara beslutens sammanhang. Radera eller skriv inte om historiska slutsatser för att få dem att stämma med dagens läge; dokumentera rättelser och ersättare.
>
> 4. Inför ett enhetligt rapportformat
>
> Varje bestående rapport ska ha ett stabilt ID och följande uppgifter, där de är relevanta:
>
> - Titel och rapporttyp.
> - Uppdrag, kund eller systemdel och moment.
> - Författare eller granskande roll/session.
> - Datum.
> - Granskad identitet: repo och commit, körning, kandidatversion, designversion eller annat exakt underlag.
> - Rapportstatus: exempelvis utkast, färdig eller ersatt.
> - Bedömningsutfall: exempelvis godkänt, underkänt, ofullständigt eller ej bedömt.
> - Länkar till underlag och bevis.
> - Länkar till föregående rapport, rättelse eller ersättare.
> - Länkar till beslut och kvarvarande åtgärder.
>
> Rapportstatus och bedömningsutfall är olika saker. En färdig rapport kan underkänna resultatet.
>
> Datum och filnamn räcker inte för att avgöra vilken version som granskats. ”Senaste rapport” ska alltid ha ett tydligt sammanhang.
>
> Återanvänd befintlig metadata. Lägg bara till det som saknas.
>
> Rapportens läsordning ska vara:
> 1. Slutsats och vad den gäller.
> 2. Viktigaste fynden.
> 3. Underlag och jämförelser.
> 4. Begränsningar och sådant som inte prövats.
> 5. Nästa åtgärd och eventuellt beslut som behövs.
>
> 5. Gör bestående granskningar beständiga
>
> Inventera relevanta rapporter som ligger i temporära arbetsytor eller worktrees. Anta inte att allt där ska arkiveras.
>
> En rapport som används för ett bestående beslut eller en rättelse ska ha en registrerad, beständig plats innan arbetsytan städas.
>
> Tillfälliga anteckningar får förbli tillfälliga. Dokumentera vad som sparas och vad som gallras enligt befintliga beslut.
>
> Bevara kopplingen till det som faktiskt granskades. Flytta inte privat material till det publika repot. Även titlar, filnamn och registerposter kan innehålla privata uppgifter.
>
> 6. Inför följande arbetsregel
>
> ”Varje förändring i Nortropic ska hålla berörd dokumentation och spårbarhet aktuell som en del av samma uppdrag. Ägaren ska inte behöva påminna om dokumentationen. Ett arbete redovisas inte som färdigt förrän berörda instruktioner, rapportkopplingar och statusuppgifter är uppdaterade, eller en konkret kvarstående begränsning har redovisats.”
>
> Förankra regeln i CLAUDE.md och relevanta arbetsflöden och skills genom hänvisning till den gemensamma regeln. Duplicera inte hela texten överallt.
>
> Regeln ska även få praktiskt stöd i befintliga verktyg och start-/avslutsvägar. Det räcker inte med en formulering som agenter förväntas minnas.
>
> Respektera uttryckligen skrivskyddade uppdrag. Då rapporteras dokumentationsbehovet utan att filer ändras.
>
> 7. Automatisera det som kan avgöras säkert
>
> Vid relevanta händelser ska befintliga mekanismer automatiskt registrera eller uppdatera exempelvis:
>
> - körningens start, slut och identitet;
> - skapade rapporter och deras beständiga länkar;
> - vilken version ett prov eller en granskning gäller;
> - färdigställande, avbrott och fel;
> - kopplingar mellan granskning, rättelse och omprövning;
> - dokumentförteckningar och dashboardens visning.
>
> Den ansvariga agenten ska samtidigt uppdatera betydelsen i berörda instruktioner när beteendet ändras.
>
> Automatik får inte:
> - hitta på beslut eller godkännanden;
> - markera ett fynd verifierat rättat enbart för att kod ändrats;
> - göra en gammal rapport aktuell genom att bara byta datum;
> - skriva över frysta bevis;
> - ersätta saknade uppgifter med antaganden.
>
> Skilj på skapad, ändrad och senast verifierad. Om något inte har kontrollerats ska det stå det.
>
> Uppdatering ska utlösas av relevanta förändringar. Starta inte full omvärldsbevakning eller nya AI-sammanfattningar vid varje liten filändring.
>
> 8. Samla läsningen i dashboarden
>
> Återanvänd eller komplettera befintlig vy med ”Dokumentation och rapporter”.
>
> Jag ska kunna hitta:
>
> - Så fungerar Nortropic: aktuella instruktioner och flödeskartan.
> - Pågående uppdrag: läge, relevanta rapporter och beslut som väntar.
> - Granskningar och resultat: sökbart efter uppdrag, typ, version, datum och utfall.
> - Beslut och historik: vad som gäller och vad som ersatts.
>
> Visa först en begriplig sammanfattning med länkar till detaljerna.
>
> Dashboarden ska läsa samma källor och metadata som filstrukturen använder. Skapa inte en separat manuellt underhållen sanning.
>
> Bevara befintliga integritetsgränser och blindningen inför ägarens första designbedömning. En dokumentförteckning får inte kringgå dessa begränsningar.
>
> 9. Hantera parallellt arbete och rättelser
>
> Använd stabila identifierare och befintlig säker skrivning så att samtidiga sessioner inte skriver över varandras rapporter eller registerposter.
>
> Ett fynd ska kunna följas från upptäckt till åtgärd och verifiering. Återanvänd fyndets identitet i stället för att skapa nya frikopplade poster för samma problem.
>
> En senare granskning ska tydligt visa om den:
> - bekräftar tidigare fynd;
> - verifierar en rättelse;
> - gäller en ny version;
> - eller rättar en tidigare felaktig slutsats.
>
> 10. Genomför och verifiera proportionerligt
>
> Inför strukturen stegvis och låt den fungera med pågående arbete.
>
> Verifiera med verkliga exempel att jag kan:
> - hitta gällande instruktion;
> - öppna en granskning och se exakt vad den gäller;
> - följa ett fynd till rättelse och verifiering;
> - skilja en färdig rapport från ett godkänt resultat;
> - se vad som ersatts;
> - hitta rapporten efter att en tillfällig arbetsyta försvunnit;
> - se en automatisk uppdatering efter en relevant förändring.
>
> Följ repots krav på kontroller för ändrad kod. Lägg inte till omfattande mekanik utan ett konkret behov.
>
> Redovisa vad som återanvänts, vad som ändrats, vad som uppdateras automatiskt och vad som fortfarande kräver agentens eller ägarens bedömning.
>
> Färdigkriteriet är att jag och en ny agent kan hitta vad som gäller, vad som granskats, vad som återstår och vilket underlag slutsatserna bygger på — utan att leta i chatthistorik och temporära mappar.
>
> Detta ska fortsätta fungera när Nortropic förändras. Dokumentationens uppdatering ska vara en del av arbetet, inte ett separat städprojekt som jag behöver beställa igen.

Genomförs i steg, och varje steg redovisar vad som återstår:
1. **Rapporterna från arbetsytan** sparades oförändrade i `underlag/granskningar/` (privat) 2026-10-06 22:41Z. Det
   gällde 84 filer ur sessionens arbetsyta:
   - 54 rapporter: 30 systemgranskningar med omgranskningar och en fyndlista, 9 svar från Codex, 7 inventeringar och 8
     andra arbetsdokument (källsammanställningar, planer, en kartläggning, en utredning, ett referensunderlag och ett
     granskningsuppdrag);
   - 30 bevisfiler: 17 ur omgranskningen av r94 och 13 ur kandidatprovet.
   Därtill sparades de 8 mätskript som pilotens frysta kvitton hänvisar till, i pilotens `matning/`. `FORTECKNING.jsonl`
   anger ursprung och sha256 för varje fil. Rapporterna för granskningarna r53–r62 hittades inte.
2. **Regler och pekare (textsteget).** Platsregeln, arbetsregeln, rapporthuvudet och läsordningen står i `README.md`,
   Var information finns. `CLAUDE.md`, `backlog/README.md`, skillsen backlog, bygg-sajt och kirurg och
   `kunskap/skapandeflodet.md` hänvisar dit.
3. **Verktygen (kodsteget).**
   - Backloggen tar källan granskning med fälten fynd och verifierad. Ett fynd får en post. Bara kommandot verifiera
     sätter verifierad, och då med en annan rapport än den som hittade fyndet. Posterna skrivs under lås.
   - Startkvittot anger repots commit, gren och ocommittade filer, och en informationsrad om dokumentationen som aldrig
     stoppar en start.
   - Dokumentprovet i rökprovet prövar platsregeln, hänvisningarna, att arbetsregeln står en gång, beslutens statusrader
     och backloggens spårbarhet.
   - Dashboardens backlogg visar om en klar post är verifierad.
4. **Granskningarna registreras** med rapporthuvud och bevis på den plats som platsregeln anger. Under natten
   2026-10-06–07 registrerades GR-20261006-r94-slut, GR-20261006-r96-om, GR-20261006-r98 och GR-20261007-r97.
5. **Återstår:**
   - vyn "Dokumentation och rapporter" i dashboarden. Den bygger på flödesvyn och kommer efter att ägaren slagit ihop
     den;
   - att föra in de äldre granskningarnas fynd i backloggen. Vilka som fortfarande gäller kräver bedömning;
   - raden "Dokumentation:" i commitmeddelandena prövas inte av något verktyg;
   - rapporthuvudet i de registrerade rapporterna prövas inte heller av något verktyg.
