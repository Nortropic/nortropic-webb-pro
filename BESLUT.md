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
    **Delvis ersatt av:** ägarens beslut 2026-10-09 ~21:17Z (Workers i stället för Vercel för nya leveranser) och
    2026-10-10 ~06:05Z (formulärets mejl genom Cloudflares e-post i stället för Resend). Övrigt gäller.

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
| "Minst tre förhandsvarv i läget full och i förfiningen" (arbetsregeln H02, `MIN_VARV`, `MIN_VARV_FORFINA`) | skaparen i läget full, förfiningen, ateljéns förfining | inget minsta antal varv: observerad brist, ändring och efterkontroll, rundgångsspärr vid två varv utan synlig förbättring, resursgränserna fristerna och turerna | ägarens uppdrag 2026-10-09 ~17:53Z, punkt 10: "Ta bort minimiantalet tre förfiningsvarv" |
| "de du väljer fördjupas till hela startsidan, undersidan och besökarens flöde" (valj och putsa startade samma fördjupning) | kandidatflödet | ett val startar inget; uppdragen Rätta, Omarbeta designen och Bygg ut med version, resultat, omfattning och det som ska bevaras | punkt 8: "En begäran om putsning ska inte automatiskt beställa hela startsidan, en undersida och nya funktioner" |
| "Ribban i tre nivåer ur ägarens kalibrering" (`kunskap/visuell-niva.md`) | granskaren, kritiken, ateljéns panel, metodens utdrag | kvalitetskravet Helhet och hierarki i `kunskap/designregler.md`; granskaren okalibrerad tills ägaren dömt nya exempel | punkt 3: kalibreringsankare och visuella lärdomar ur gamla bedömningar ska sluta påverka; "Kvalitetskraven består" |

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

**Status:** delvis ersatt av ägarens ord samma dag (nedan) och av tillägget 2026-10-07 om omtagens jämförelsepunkter och
städningens villkor.

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

**Delvis ersatt av:** tillägget 2026-10-07 om omtagens jämförelsepunkter och städningens villkor (sist i den här filen),
i fråga om punkt 4 och omtaget: en tempkatalog i /tmp och $TMPDIR raderas bara när den är registrerad som en körnings
egen och körningen är avslutad, inte på namnprefixet; äldre rester redovisas för sig och raderas inte; ingen symlänk
följs och ingen gemensam förälder raderas; en sessions arbetsyta tas bort först när varje fil i den är registrerad
eller går att återskapa; och ett omtag sparar och registrerar det ägaren bedömt innan något raderas. Övrigt gäller.

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
5. **Vyn Dokumentation och rapporter** (2026-10-07, punkt 8 här och punkt 9 i ägarens uppdrag 2026-10-07 om
   kompetens och rapportering). Fliken Dokumentation i dashboarden visar först en sammanfattning och sedan fyra delar:
   - **Så fungerar Nortropic:** platsregeln, flödeskartan och filerna som platsregeln och `CLAUDE.md` pekar på.
   - **Pågående uppdrag:** körregistret, kundernas körningar som i flödesvyn, pilotens moment med avsändaren ur fältet
     `avsandare`, lägesrapporternas beslut och uppdragen i BESLUT.md med sin senaste rapport.
   - **Granskningar och resultat:** rapporthuvudena och förteckningens äldre rapporter, sökbara efter uppdrag eller
     systemdel, typ, version, datum, utfall och rapportstatus.
   - **Beslut och historik:** tilläggens status, ersättare och det som återstår.

   Allt läses ur filerna vid varje visning:
   - ett utfall visas med versionen det gällde, och ett sammansatt utfall visar ägarens dom som en egen rad;
   - rapporthuvudets valfria fält `rattelser` och `giltighet` visas vid rapporten och i översikten;
   - förteckningens sha256 visas som integritet, inte som verifiering;
   - rapporter som koden hänvisar till men som saknas visas ur koden;
   - fynden och rättelserna kommer ur backloggen;
   - varje fil prövas som den verkliga filen, med symlänkar, `./`, `..` och skiftläge lösta, både i vyn och i `/fil/`; en
     fil med flera hårda länkar visas inte, och `/api/dokument` visar bara filer som git följer.

   `ny --fynd` från en senare rapport öppnar en klar post igen (GR-20261007-r97-om#BÖR-1), bara en gång och bara när
   rapporten är senare än varje rapport som posten nämner (GR-20261007-r99#BÖR-5). Granskningen GR-20261007-r99
   underkände den första versionen; B1, BÖR-1–7 och KAN 1, 2, 4, 7, 8 och 10 är rättade. Prövas av
   `prov_dokumentationsvy.py` och `prov_dokumentation.py` i rökprovet.
6. **Återstår:**
   - kompetenskedjan per steg och kandidat och körningens slutpost: vyn har en plats för dem, men datakällorna byggs i
     andra grenar;
   - rapporterna för granskningarna r53–r62, som koden hänvisar till, saknas och återskapas inte;
   - de äldre rapporterna i `underlag/granskningar/sessioner/` saknar rapporthuvud, så deras fält visas som ej angivet. Ett
     huvud läggs bara till där underlaget belägger värdena;
   - att föra in de äldre granskningarnas fynd i backloggen. Vilka som fortfarande gäller kräver bedömning;
   - GR-20261007-r99#KAN-3, -5, -6, -9 och -11–14 är inte rättade (commitmeddelandet räknar upp dem);
   - kalibreringsförsöket, omklassat till utvecklingsdata, syns inte i översikten. fil_tillaten döljer det, och att visa
     det kräver först en bedömning av blindningen (GR-20261007-r99#BÖR-7, GR-20261007-r99-om#KAN-5);
   - omgranskningens BÖR-1 och KAN-1–4 är backlogposter (`fynd: GR-20261007-r99-om#…`);
   - raden "Dokumentation:" i commitmeddelandena prövas inte av något verktyg;
   - ingenting prövar rapporthuvudet när en rapport skrivs. Vyn visar ett trasigt huvud och saknade fält under Saknat
     underlag.

## Tillägg 2026-10-07: kompetensens användning och tillförlitlig rapportering

**Status:** gäller.

Ägarens uppdrag 2026-10-07, mottaget cirka 05:08Z (sparat i minnet 05:08:36Z): ett inklistrat block, formulerat av Codex
efter granskningen av main ee73c36, och efter det ägarens egen text (Tillägg). Båda ordagrant:

> Uppdrag: säkerställ faktisk användning av Nortropics kompetens och gör rapporteringen tillförlitlig genom hela flödet.
>
> Arbeta i nortropic-webb-pro. Målet är professionella, kundanpassade webbplatser som når min visuella ribba, med ett flöde där jag kan förstå vad som gjorts, vad som brustit och vad som gäller nu.
>
> Det här är ett genomförandeuppdrag. Återanvänd befintlig mekanik, metodkarta, observation, rapportstruktur och dashboard. Kontrollera först vad som redan är rättat eller pågår i andra arbetsgrenar. Gör inte samma arbete igen och stör inte pågående arbete.
>
> Codex granskade main ee73c36. Fynden nedan beskriver den versionen och ska verifieras mot aktuell kod före rättning.
>
> 1. Ägarens krav: kompetensen ska användas
>
> Våra valda skills, MCP-tjänster och verktyg ska användas genom hela kedjan. Att något är installerat, ansluter eller listas i ett kvitto uppfyller inte kravet.
>
> För varje vald kompetens ska det framgå:
> - vilket arbete den ansvarar för;
> - i vilket steg den används;
> - att den utförande sessionen faktiskt får tillgång till den;
> - vilket underlag den tillför;
> - vilka beslut eller förändringar den leder till;
> - hur resultatet bedöms.
>
> Använd metodkartan för ansvarsfördelningen. Fördela kompetensen mellan stegen med tydliga uppdrag, så att relevant kunskap faktiskt kommer till användning och motstridiga instruktioner hanteras. Behåll de fullständiga källorna tillgängliga.
>
> Ingen vald kompetens får tyst falla bort. Om en förmåga är blockerad eller inte fungerar ska det synas som en konkret brist med konsekvens och åtgärd.
>
> Gör inga meningslösa verktygsanrop för att fylla ett kvitto. Kravet är meningsfull användning och tillämpning. Ett läskvitto är belägg för läsning, inte för designkvalitet.
>
> 2. Refero och Mobbin ska bidra till designen
>
> Båda tjänsterna ska ingå i referensarbetet med faktisk undersökning av relevanta förlagor.
>
> Säkerställ att:
> - sökningarna utgår från kundens uppgifter och flera möjliga designriktningar;
> - relevanta bilder, stilar och flöden öppnas och granskas;
> - det valda materialet når skaparen, ateljén och granskningen;
> - referensernas viktiga kompositioner och tillstånd bevaras;
> - skaparen kan begära kompletteringar när underlaget inte räcker;
> - misslyckade anrop, tomma resultat och uteblivna bilder inte redovisas som genomfört referensarbete.
>
> Skilj mellan tjänsteanrop i researchen, material som skaparen faktiskt läst och egna kompletterande anrop från skaparen.
>
> Frysta referenspaket är användbara. De ska ha tydligt ursprung, version och bilder, och deras existens får inte tas som bevis för att skaparen har granskat eller tillämpat dem.
>
> Pröva vad refero_search_apps tillför vårt referensarbete och ge verktyget en uttrycklig roll om det är relevant. Kontrollera verklig tillgång och tillåtelse i de sessioner som ska använda det. Lämna inte en upptäckt förmåga oklart hanterad under etiketten ”okänd”.
>
> 3. Rätta startkvittots betydelse
>
> Codex fann två olika saker:
>
> A. ”Referos verktyg utan uppgift i flödet: refero_search_apps”
> Detta kom från skillnaden mellan upptäckta och tillåtna verktyg. Det var inte belägg för ett trasigt Refero-anrop.
>
> B. ”REFERENSER.md saknas”
> Kontrollen tittade bara på om underlag/<slug>/REFERENSER.md fanns. Den kände inte igen det aktuella kandidatflödets FORSKNING.md, referenspaket och tjänstematerial. Den kördes dessutom före researchen.
>
> Gör kontrollen medveten om flödesläge och fas. Före researchen ska den kontrollera förutsättningarna för research. Efteråt ska den kontrollera det faktiska underlaget och dess användbarhet.
>
> Skapa inte en tom REFERENSER.md för att få grönt.
>
> Skilj tydligt mellan:
> - tillgängligt;
> - provat och fungerande;
> - tilldelat en uppgift;
> - använt med resultat;
> - planerat i ett senare steg;
> - blockerat eller misslyckat;
> - inte observerat.
>
> Skilj också den vanliga prototypkörningen från Figma-piloten. Ett kvitto för den ena får inte uppfattas som verifiering av den andra.
>
> 4. Ge varje körning ett tillförlitligt slutbesked
>
> Återanvänd befintliga identiteter och versionshashar. Inför eller komplettera en beständig, maskinläsbar slutpost som binder samman:
> - uppdrag och körning;
> - aktuell kandidat/designversion och byggversion;
> - relevant metodversion;
> - tekniska kontroller;
> - designgranskning och vem som gjort den;
> - ägarens eventuella beslut;
> - slutkod, återstående brister och nästa steg;
> - länkar till rapporter och bevis.
>
> Låt terminalens besked, rapportöversikten och dashboarden härledas från samma aktuella uppgifter.
>
> Kontrollera alla befintliga startvägar. Codex fann att vissa yttre anropare sparar logg eller slutkod, medan direkt kor.sh saknar en egen beständig slutpost. Bevara fungerande delar och fyll luckan.
>
> Håll isär:
> - sessionen avslutad;
> - tekniskt godkänt;
> - designgranskaren godkänner;
> - ägaren godkänner;
> - klart för leverans inom angiven omfattning.
>
> 5. Bind slutrapporten till rätt version
>
> Codex fann att rapportvillkoret i stoppvakten bara kontrollerade existens och storlek, medan korslut bara kontrollerade existens.
>
> En gammal RAPPORT.md får inte uppfylla rapportkravet för ett nytt bygge.
>
> Bind rapporten till den aktuella körningen och det granskade underlaget. Saknad eller avvikande identitet ska redovisas tydligt.
>
> Behåll slutgrindens befintliga kontroller av prov, stoppvakt, granskning och metod. Fyndet gäller rapportens aktualitet; det är inte belägg för att de andra versionskontrollerna saknas.
>
> Dashboardens granskningsdom ska tydligt visa om den gäller det aktuella bygget och aktuell metod. En historisk godkänd omgång ska kunna läsas som historik utan att uppfattas som ett aktuellt leveransgodkännande.
>
> 6. Håll rapporter och status aktuella automatiskt
>
> Codex fann bland annat:
> - pilotrapporten säger både att domen saknas och att en dom har kommit;
> - skissredovisningen säger ”under arbete” efter att körningen stoppats;
> - tiden till första valbara skiss saknas trots att en kandidat anges vara klar.
>
> Rätta orsaken till dessa motsägelser.
>
> Berörda statusuppgifter och sammanställningar ska uppdateras vid normala övergångar, fel, stopp, återupptagning, nya domar och ersatta versioner. Jag ska inte behöva påminna om dokumentationen.
>
> Bevara frysta bevis och historiska rapporter. Använd en aktuell sammanställning och tydliga kopplingar till korrigeringar eller efterföljande rapporter. Skriv inte om historiska observationer så att det ser ut som om senare kunskap fanns från början.
>
> Ett arbete är inte färdigt förrän berörd dokumentation och spårbarhet är uppdaterad, eller en konkret kvarstående begränsning är redovisad.
>
> 7. Säkerställ rätt avsändare för beslut och bedömningar
>
> Skilj uttryckligen mellan:
> - ägarens egna ord och beslut;
> - Codex bedömning;
> - Claude/skaparens bedömning;
> - en annan granskares bedömning;
> - maskinellt mätresultat;
> - hypotes.
>
> Att jag vidarebefordrar en AI-bedömning betyder inte automatiskt att jag själv har gjort den bedömningen eller antagit alla dess preferenser som ägarbeslut.
>
> Granska särskilt AGARENS-DOM-C5.md och dess användning i VERSION.json och beslutsunderlaget. Bevara citatet och versionskopplingen, men säkerställ korrekt avsändare och beslutstyp. Om avsändaren inte går att belägga ska det framgå.
>
> Detta ska förhindra att framtida design låses av preferenser som felaktigt tillskrivits mig.
>
> 8. Rätta missvisande slutsatser och mätpåståenden
>
> Kalibreringen:
> Försöksrapporten visar fortfarande sex ”undanhållna” exempel och noll fel, medan resultatet senare omklassades till utvecklingsdata efter testläckage.
>
> Gör korrigeringen synlig från själva rapporten och översikten. Bevara ursprungsresultatet som historik. Presentera det inte som ett oberoende mått på granskarens träffsäkerhet.
>
> Kontrast:
> Pilotens percentilmätning är ett hjälpmedel. Den bevisar inte ensam att texten klarar kontrastkraven.
>
> Skilj mellan uppskattad kontrast, verifierad kontrast vid texten och vad som inte har prövats. Använd rätt krav för textens storlek och vikt. Påstå inte heller att sidan har ett WCAG-fel enbart utifrån ett enskilt bakgrundsvärde.
>
> Designens orsaker:
> Formuleringen ”materialet sätter taket” är inte tillräckligt styrkt av piloten. Skilj den från den observerade kvalitetsförlusten i kundanpassningen.
>
> Pröva bättre bildval, beskärning, hierarki och komposition med befintligt material innan ni behandlar materialet som en fast kvalitetsgräns. Även modellförmåga och behov av mänsklig art direction får vara prövbara förklaringar.
>
> 9. Gör dokumentationen lätt att följa
>
> Återanvänd den nya rapportstrukturen och förteckningen. Codex verifierade att de 650 registrerade filerna fanns och stämde med sina hashar på ee73c36. Det arbetet ska bevaras.
>
> Förteckningens integritet är inte samma sak som fullständig historik eller verifierade slutsatser.
>
> Översikten ska hjälpa mig att hitta:
> - aktuellt läge per uppdrag;
> - senaste relevanta slutrapport;
> - vad som är godkänt, underkänt, ofullständigt eller ännu inte bedömt;
> - öppna fynd och deras åtgärder;
> - vilka rättelser som har verifierats;
> - historik och ersatta slutsatser;
> - saknat underlag.
>
> Kontrollera kvarstående arbete med dokumentationsvyn, äldre fynd och rapporthuvuden. Markera saknade rapporter, exempelvis r53–r62 om de fortfarande saknas. Återskapa inte deras innehåll ur gissningar.
>
> Fynd ska kunna följas från upptäckt till rättelse och verifiering. Ett återkommet fynd får inte försvinna bakom en tidigare ”klar”-markering.
>
> Allt under underlag/ och kunder/ förblir privat. Lägg inte privat rapportinnehåll, kundmaterial eller identifierande utdrag i det publika repot.
>
> 10. Verifiera genom verkliga ingångar
>
> Gör avgränsade regressionsprov för rättelserna, bland annat:
> - research som ännu inte körts;
> - giltigt referensunderlag utan rotfilen REFERENSER.md;
> - tom eller inaktuell referensfil;
> - upptäckt men otillåtet verktyg;
> - stoppad kandidat som tidigare var under arbete;
> - gammal rapport till nytt bygge;
> - historisk granskning som inte gäller aktuell version;
> - olika startvägars beständiga slutbesked;
> - skillnaden mellan vidarebefordrad AI-bedömning och ägarbeslut;
> - en korrigerad slutsats som ska synas från den äldre rapporten.
>
> Prov ska kontrollera beteendet, inte bara att en ny text eller ett fält finns.
>
> Samordna med pågående grenar, gör nödvändiga kontroller och följ repots etablerade rutin för commit och sammanslagning.
>
> 11. Leverera ett begripligt resultat
>
> Redovisa kort:
> - vad som redan fungerade;
> - vilka fynd som bekräftades och rättades;
> - vad som fortfarande är öppet;
> - vilka kompetenser som nu har en fungerande plats i flödet;
> - var jag ser aktuellt läge och slutresultat i dashboarden;
> - vad som ännu inte är verifierat i en verklig designkörning.
>
> Visa därefter användningen i nästa avtalade, avgränsade designexempel. Det ska gå att följa:
> kompetens → faktiskt arbete → designbeslut → renderat resultat → bedömning.
>
> Ett grönt systemprov avslutar systemrättelsen. Ett visuellt resultat som når min ribba visar om designarbetet lyckats. Båda behövs och ska redovisas separat.
>
> Skapa inte ännu ett fristående rapportlager. Gör den befintliga kedjan sammanhängande, aktuell och begriplig.

> Tillägg: visa hur kompetensen används och var kedjan brister
>
> Komplettera befintlig metodkarta, observation och rapportering så att jag per steg och kandidat kan följa:
>
> uppgift → tillgång → observerad användning → tillämpning → resultat → bedömning.
>
> Visa för varje tilldelad kompetens:
> - dess konkreta uppgift;
> - tillgängliga skills, verktyg och behörigheter;
> - observerade läsningar och anrop med utfall;
> - relevanta resultat eller referenser som nådde skaparen;
> - vilket designbeslut eller vilken ändring skaparen kopplar till dem;
> - länk till motsvarande version, bilder, kod eller beteendeprov;
> - bedömningen av resultatet och vem som gjorde den.
>
> Märk observerade fakta, skaparens egen förklaring och granskarens bedömning separat. Dra inte slutsatsen att ett verktyg orsakade en förbättring enbart för att det anropades före ändringen.
>
> Jämför metodkartans förväntade arbete med det observerade. Synliggör exempelvis:
> - kompetens tilldelad men åtkomst saknas;
> - obligatoriskt arbete utan observerad användning;
> - lyckat anrop men uteblivet användbart material;
> - material hämtat men ingen observerad läsning;
> - påstådd tillämpning utan koppling till resultat;
> - genomförd ändring som ännu inte bedömts.
>
> Skilj ”inte observerat” från ”inte gjort”. Redovisa observatörens täckning, inklusive underagenter, shellverktyg, övriga MCP-tjänster och separata körvägar.
>
> Bevara en versionsbunden sammanställning vid avslut, stopp och fel så att spåret går att granska även senare. Återanvänd befintliga rapporter och bevis; duplicera inte känsliga råloggar.
>
> Visa detta samlat i dashboarden med möjlighet att öppna beläggen. Målet är att hitta luckor, söka efter skills, mcps eller litteratur, metoder, principer, best practices och förbättra designarbetet, inte att belöna flest anrop eller flest lästa filer.

Uppdraget genomförs i fyra grenar, fördelade efter en läsande inventering mot main 84c6994. Fynden verifierades mot den
koden före rättningen.

**Gren A: slutbesked och rapporters giltighet (punkt 4, 5, 8 och 10), 2026-10-07, grenen `slutbesked-20261007`:**
1. **Slutposten.** `kontroller/korslut.py` skriver `kunder/<slug>/korningar/<körning>/SLUT.json` för varje
   kor.sh-körning. Posten bär rapporthuvudets fält (`README.md`, Var information finns) och binder ihop körningen,
   bygget (dist_sha256), granskningsmetoden, byggets inställningar, repots commit och den godkända startsidan (kandidat,
   version och VINNARE.json:s sha256). Därtill de tekniska kontrollerna, designgranskningen och vem som gjorde den,
   ägarens beslut, slutkoden, bristerna, nästa steg och länkarna till rapporter och bevis. Provets och stoppvaktens
   besked kopieras till postens katalog, eftersom nästa körning skriver över dem.
   - Fem tillstånd hålls isär: sessionen avslutad normalt, tekniskt godkänt, designgranskaren godkänner, ägaren godkänner
     och klart för leverans inom angiven omfattning. Tekniskt godkänt bygger på provet, stoppvaktens egna kontroller och
     rapportens bindning, inte på om stoppvakten släppte avslutet.
   - Terminalens besked skrivs ur posten. En start som stannar före bygget (slutkod 2) får en kort post. SIGTERM, SIGINT
     och SIGHUP under bygget stoppar claude, och korslut skriver posten (slutkod 4). En körning som dödas med SIGKILL
     lämnar `START.json` utan slutpost; nästa start och `--visa` säger att den avbröts. **Delvis ersatt av:** tillägget
     2026-10-07 om skyddet av ägarens dom och byggets processer: signalen går till claudes hela processgrupp, och efter
     SIGKILL mot kor.sh skriver vakten posten och släpper låsen. Posten saknas bara när både kor.sh och vakten dödas.
     Övrigt gäller.
   - En ny post ersätter de tidigare (`rapportstatus: ersatt` och `ersatt_av`) bara när den gäller ett annat bygge eller
     en annan metod. Den äldre postens länk till rapporten pekar på den flyttade filen.
   - Ägarens dom räknas bara ur en `DOM.json` som är oförändrad sedan körningens start. Byggets Write och Edit nekas för
     filen under körningen. Finns den vid starten låses den, och en DOM.json som ändras eller tillkommer under
     körningen ger slutkod 3. Skyddet var ofullständigt när grenen slogs ihop (omgranskningen GR-20261007-r101-om):
     - #BÖR-1: ett eget skript i bygget kunde ta bort låset och förfalska hashlistan `prov/.skyddat-fore`, och en
       process som levde kvar efter sessionen kunde skriva filen efteråt. Samma lucka dolde en ändrad
       `kritik/GRANSKARE.md`, så den gällde hela skyddet från F10.
     - #BÖR-2: barnprocesser kunde leva kvar efter en signal under bygget.

     **Delvis ersatt av:** tillägget 2026-10-07 om skyddet av ägarens dom och byggets processer, där #BÖR-1 och #BÖR-2
     är rättade och gränsen som återstår står. Övrigt gäller.

     Att svaret "Ja, som den är" räknas som godkännande är Claudes tolkning, inte bekräftad av ägaren.
   - `korslut.py --visa` prövar posten mot läget nu. Har bygget, granskningens metod eller startsidans godkännande ändrats
     står postens godkännanden som historik, och klart för leverans är nej.
   - Posten som uteblir (en katalog i dess ställe, ett skrivfel) ger slutkod 5, och backlog_commit publicerar då inget.
     Trasiga äldre filer (SLUT.json, DOM.json, VINNARE.json) fäller inte avslutet och står som brister.
   - A/B-armarna (`kontroller/ab.py`) pekar på armens slutpost i stället för granskningens rotfil, och demon i
     dashboarden får samma post genom kor.sh.
2. **Rapporten bunden till körningen.** kor.sh flyttar ett tidigare bygges RAPPORT.md till
   `kunder/<slug>/rapporter/RAPPORT-fore-<körning>.md` när bygget startar, och inget raderas.
   - Stoppvakten godtar bara en rapport med körningens identitet i huvudet och sparar dess sha256 och körning. Filtiden
     räcker inte, eftersom en äldre rapport som kopieras tillbaka får en ny filtid.
   - Korslut kräver samma sha256 och körning. Beskedet säger om felet är stoppvaktens (ett besked från en annan körning)
     eller rapportens ("saknar identitet", "gäller körning X"). Slutgrindens prov av provet, stoppvakten, granskningen och
     metoden står kvar.
   - Uppdraget från kor.sh och steg 7 i skillen bygg-sajt bär identiteten. Ändrar bygget en tidigare slutpost, en flyttad
     rapport eller ägarens dom blir slutkoden 3.
3. **Kalibreringen.** Mallen för försöksrapporten (`kontroller/granskarforsok/kalibrering.py`) anger nivåfilens sha256
   och ett läckageprov. Exemplen kallas undanhållna bara när provet faktiskt prövat texter, nivåfilen bland dem, och inte
   funnit några ordagranna spår; annars är siffran utvecklingsdata. Provet fångar inte en omskriven destillering, och
   rapporten säger det. Den privata rapporten i `underlag/kalibrering/FORSOK-20261004/` har fått ett daterat
   rättelseblock överst och `giltighet: utvecklingsdata` med skäl, med hänvisning till `LARDOMAR.md` (rad 190–205) och
   backlogposten om kalibreringen. Siffrorna står kvar som historik. Rapporten är registrerad i förteckningen med sha256
   före och efter rättelsen.
4. **Proven.** `kontroller/rokprov/revision/prov_slutpost.py` (i rökprovet) prövar beteendet genom de verkliga
   ingångarna och vad varje tillstånd bygger på, med förväntade rader i terminalen. Fallen för de nya rättelserna var
   röda mot 84c6994 respektive 38f5538.
5. **Granskningen GR-20261007-r101** (2 blockerande, 9 BÖR, 10 KAN; 15 av 42 mutationer överlevde) är rättad: B1
   (ägarens dom), B2 (`--visa` och aktuell metod), BÖR 1–9 och KAN 1–9 (KAN 7 för kommande rättelser). Granskarens
   mutationer kördes om mot rättelsen.

**Gren C1: ateljéns slutpost, status vid stopp och fel, och avsändarna (punkt 4, 6, 7 och 10), 2026-10-07, grenen
`ateljeslut-20261007`:**
1. **Slutposten per ateljékörning.** `kontroller/ateljeslut.py` skriver `kunder/<slug>/atelje/korningar/<körning>/SLUT.json`
   i helbyggets form, med korsluts fält och hjälpfunktioner: rapporthuvudets fält, de fem tillstånden var för sig,
   slutkoden, bristerna, nästa steg och länkarna. Körningen är arbetarens starttid i kor.sh:s form.
   - Arbetaren skriver posten i sin finally, vid normalt avslut, fel och stopp, och när startkontrollen stoppar starten.
   - Posten binder ihop körningen (läge, start och slut), kandidaterna med sina versioner och repots commit. Den binder
     också METOD.json:s sha256 och stegens metodhashar, kandidatplanen och skisskritiken med vem som gjorde den (rollen,
     modellen och sessionen, aldrig omdömet), ägarens beslut med avsändaren och stoppet eller felet med steget.
   - Platsen för kompetenskedjan står som "inte observerat"; gren C2 fyller den.
   - Körningens STATUS.json och REDOVISNING.md ligger i postens katalog, så att nästa körning aldrig skriver över den
     förra körningens version. En körning utan post (en dödad arbetare, eller en från före posterna) får en post i
     efterhand, ur sin STATUS.json, innan nästa start skriver över den. En start som stannar före körningen
     (prototyp.py:s stopp och ateljéns nekade starter) får en kort post med skälet och slutkod 2, men bara när
     `kunder/<slug>/` redan finns, eftersom en ny post direkt under `kunder/` hör till ett bygges gräns.
   - `atelje.py` och `prototyp.py` skriver beskedet ur posten och ger dess slutkod. Slutkoderna:
     - 0: klar för ägarens bedömning;
     - 2: ingen körning startades;
     - 4: föll, stoppades eller avbröts, också när startkontrollen stoppade starten;
     - 5: väntan slut medan körningen pågår, och då finns ingen post än;
     - 6: ingen startsida att bygga vidare på.

     Inventeringen fann att prototyp.py oftast ger 5. Det beror på att väntan är 540 sekunder, medan en körning med
     skisser tar timmar. Nästa anrop ger postens besked när körningen har slutat.
2. **Status vid stopp och fel (punkt 6).** En kandidat som körningen satte under arbete märks "avbruten vid stoppet" eller
   "avbruten av fel", med tiden (`avbruten_vid`). Återupptagningen sparar försöket i `forsok-<n>/` och gör om det, som
   förut. En session som stoppet avslutade får sluttid och utfall i sessionsförteckningen; i provet 10-06 hade k02
   `utfall: null`.
   - Efter stoppet skriver ingen kvarlevande tråd i kandidaternas status, och trådarna håller inte kvar processen.
   - Skissredovisningens huvud säger körningens utfall: klar, eller steget och stoppet eller felet.
3. **Första valbara skiss (punkt 6).** Tiden sätts när den första kandidaten blir valbar, också om körningen stoppas
   före resten. I en äldre körning utan fältet räknas den fram ur statusloggen och märks som framräknad.
4. **Avsändarna (punkt 7).** `kontroller/skapande.py` har avsändartyperna med en definition var (`AVSANDARTYPER`,
   `KALLOR`), den enda källan i koden. Typerna är ägarens egna ord och beslut, Codex bedömning, Claudes eller skaparens
   bedömning, en annan granskares bedömning, maskinellt mätresultat, hypotes och vidarebefordrad AI-bedömning.
   - Bara ägarens egna beslut (`ar_agarens`) räknas: av godkännandet, läget, stoppvakten, blindningen, omtaget, ateljéns
     slutkod 6 i bygget och slutposterna.
   - En vidarebefordrad AI-bedömning är en egen källa. "Ägaren via Codex" räknas bara med ett belägg (fältet `belagg`),
     och `skapande.py dom` kräver `--belagg` för ägarens ord utanför dashboarden.
   - Befintliga domloggar skrivs inte om: en äldre rad utan belägg står som "ej belagd". Kundernas riktiga domloggar
     (en logg, tre rader): två rader "ägaren via Codex" utan belägg står nu som ej belagda och räknas inte, och den
     tredje, ägarens egen ur dashboarden, gäller. Ägarens senaste beslut är detsamma som förut, och prompternas aktuella
     domar likaså; raden om två äldre domar i prompterna faller bort. Ingen VINNARE.json har ett godkännande.
   - Bekräftar ägaren de två raderna kan en ny rad med belägg läggas till; de gamla skrivs inte om.
   - Korslut visar godkännandets avsändare ur domloggen, i stället för texten "ägaren via ägaren via Codex".
5. **Ingen dom försvinner tyst (GR-20261007-r100-om#KAN-A).** Domloggen läses på radslut och inget annat
   (`skapande.jsonl_rader`), av skapande, stoppvakten, ateljéns domrader (omtagets kvitto) och dashboardens domläsning
   genom `skapande.domar`.
   - En dom med U+2028, U+2029 eller U+0085 räknas, och kvittots radnummer och radens hash är filens egna.
   - En rad som inte går att läsa står med antal, plats och skäl (`skapande.domlogg`), i ateljéns slutpost och i
     `skapande.py visa`.
   - Står en oläsbar rad efter ägarens senaste läsbara dom gissar ingen förbi den: läget stannar, godkännandet gäller
     inte och stoppvakten stannar bygget, tills raden är rättad.
   - En ny dom efter en avbruten skrivning hamnar på en egen rad.
   - Tjänstesessionernas loggar, underhållets ändringar, provets historik, A/B-loggen och förteckningen läses också på
     radslut. Korsluts läsning av byggets logg gick redan på radslut och är oförändrad.
6. **Proven.** `kontroller/rokprov/revision/prov_ateljeslut.py` (i rökprovet) prövar beteendet i 15 fall. Fallen gäller
   en stoppad kandidat, en arbetare som slutar efter stoppet fast en sessions tråd aldrig svarar, fel mitt i en körning,
   återupptagningen, prototyp.py:s stopp, den verkliga startvägen (i en repokopia med en falsk claude), en
   vidarebefordrad AI-bedömning mot ett ägarbeslut, en äldre rad utan belägg, första valbara skiss och domloggens
   radslut. Fallen var röda mot f1529c5 och är gröna här, och 31 mutationer av grenens kod, var och en i en egen kopia,
   fälldes alla av proven. Revisionsprovets domar "ägaren via Codex" bär nu ett belägg, så att de prövar samma vägar som
   förut.

**Återstår:**
- Gren B: startkvittot och åtkomsten (punkt 1–3).
- Gren C2: kompetenskedjan per steg och kandidat i ateljéns slutpost (fältet `kompetenskedjan`, nu "inte observerat").
- Gren D: dashboarden.
  - Ateljéns slutpost ska visas, med de fem tillstånden, stoppet och felet med steget, kandidaterna "avbruten vid
    stoppet" och första valbara skiss med sin källa. Skisskritiken i posten visas först efter ägarens första beslut.
  - Avsändaren ska visas per dom (`skapande.avsandare`), och "ej belagd" och vidarebefordrade bedömningar skiljas från
    ägarens.
  - Dashboarden avgör ägarens dom med `kalla in skapande.AGAREN`, där AGAREN nu bara är källan "ägaren". En
    vidarebefordrad bedömning visas därför aldrig som ägarens, men en belagd "ägaren via Codex" räknas inte heller förrän
    vyn använder `skapande.ar_agarens`. Det gäller prototyp_domd och flödesvyns steg 3.
  - Domloggens oläsbara rader ska visas (`skapande.domlogg`).
  - Dashboardens egna JSONL-läsningar delar fortfarande på U+2028 (`str.splitlines`): byggets logg (las_logg),
    underhållets ANDRINGAR.jsonl och prospektvyns logg.jsonl.
- Gren C1:s begränsningar:
  - Den äldre utforskningens `--bara-domare` skriver ingen egen post. Förra körningen får sin i efterhand.
  - En start som nekas före `kunder/<slug>/` finns skriver ingen post, och ett fel i anropet skriver ingen post.
  - En arbetare som dödas med SIGKILL skriver ingen post; den skrivs i efterhand vid nästa start eller vid prototyp.py:s
    besked om avbrottet.
  - De fem tillstånden ur slutposten i stället för "Klar: success", och granskningsdomen som aktuell eller historisk.
  - Demoposten och A/B-vyn mot slutposten. A/B-vyn visar i dag en arm utan granskning ("ej bedömt") som "underkände".
  - Kalibreringens rättelse i översikten.
  - Dashboardens Din dom bör vägra en dom medan kundens bygge pågår; i dag misslyckas skrivningen mot den låsta filen,
    eller räknas inte när filen saknades vid starten.
- Uppdraget står här ordagrant; de andra grenarna lägger inte in det igen.
- En start som nekas före låset skriver ingen slutpost: fel i anropet, verktyg som saknas eller ett bygge som redan
  pågår. Skrivningen kunde ändra det pågående byggets gräns, så skälet står bara i terminalen. En körning som dödas med
  SIGKILL får ingen post; den syns bara som avbruten. **Delvis ersatt av:** tillägget 2026-10-07 om skyddet av ägarens
  dom och byggets processer: efter SIGKILL mot kor.sh skriver vakten posten. Övrigt gäller.
- Byggen från före den här ändringen saknar rapportens identitet i STOPPVAKT.json. Korslut och flödesvyn godkänner dem
  inte längre, och beskedet säger att stoppvaktens besked är från före 2026-10-07.
- Läckageprovet hittar ordagranna spår av de prövade exemplen, inte en omskriven destillering av domarna.
- Den privata kalibreringsrapportens ursprungliga RAPPORT.json sparades inte ordagrant vid rättelsen. Den återskapades
  2026-10-07T10:04Z och kontrollerades mot `sha256_fore`, liksom RAPPORT.md:s original. Båda ligger skrivskyddade i
  `underlag/kalibrering/FORSOK-20261004/ursprung/` (privat) och är förda i förteckningen (GR-20261007-r101-om#KAN-7).
  Senare rättelser sparar originalet i rättelsen.
- Punkt 11 och designexemplet: ingen verklig designkörning har ännu gått med slutposten.

## Tillägg 2026-10-07: ägarens beslut om omtagens jämförelsepunkter och städningens villkor

**Status:** gäller.

Ägarens svar 2026-10-07 på frågorna efter morgonrapporten (sparat 04:49Z, också i minnet), ordagrant. Om omtagen:

> Ja till att spara det bedömda: bilder och versionshash, tillsammans med domen och länken till motsvarande design/kod. Hashen behöver ett bevarat underlag för att jämförelsen ska kunna återskapas.

Om städningen:

> Ja, städningen får omfatta både /tmp och $TMPDIR.
>
> Den ska bara radera kataloger som vi kan identifiera som skapade och ägda av den aktuella körningen, med befintlig registrering av egna kataloger. Namnprefix ensamt räcker inte. Äldre rester behöver identifieras separat innan de rensas.
>
> Städningen får inte följa symlänkar utanför det egna området eller radera gemensamma föräldrakataloger. Rapporter, bedömda bilder och tillhörande versionsunderlag ska ligga beständigt och vara registrerade innan en tillfällig arbetsyta tas bort.

Skälen: ett omtag raderade det ägaren bedömt utan ett bevarat underlag, så en senare jämförelse gick inte att återskapa.
Städningen raderade tempkataloger på namnprefixet ensamt (städregeln ovan, punkt 4).

Så gäller det sedan grenen `stadvillkor-omtag-20261007`, med rättelserna efter granskningen GR-20261007-r100:

1. **Omtaget sparar det bedömda före raderingen** (`kontroller/atelje.py`, `ta_bort_beslut`). För varje kandidat som
   ägaren dömt i körningen sparas `underlag/<slug>/omtag/<stämpel>/<kandidat>/<v12>/` med tre delar:
   - `underlag/`: exakt de filer versionen räknas över (`DESIGN.md`, `kod/` och `kod-src/`; `kontroller/kandidater.py`,
     `version_filer`). Hashen räknas om ur det sparade och ska bli versionen.
   - `bilder/`: skärmbilderna i de bredder som versionen fotograferades och dömdes i.
   - `KVITTO.json`: id, tid, kandidat, version och den omräknade hashen, sha256 per fil och länkarna till design och kod.
     Där står också domarna, med fil, rad och radens sha256 i `DESIGNDOMAR.jsonl`, och posten själv.

   En version är dömd när en dom från ägaren i planen namnger den. En dom utan plan, förd för hand, gäller planen när den
   kom efter att planen skrevs. När ägarens senaste dom (ny riktning eller förkasta) gäller körningen är dessutom varje
   kandidat som ägaren sett dömd, i den version kandidaten har; det gäller också när körningen redan bokförts för hand.
   En version som ingen rad i domloggen pekar på sparas inte, och då görs inget omtag. Domloggen läses på samma sätt
   som överallt annars.

   Detta sparas innan något raderas, i `omtag/<stämpel>/atelje/` och `omtag/<stämpel>/prototyp/`, med sha256 per fil
   och domarna som gäller dem:
   - vinnaren: `atelje/vinnare/` och `VINNARE.json`, med en jämförelse mot hasharna där;
   - slutdomens bilder: `atelje/slutdom/`;
   - tidigare körningars arkiv: `atelje/foregaende/`;
   - en äldre `prototyp/`.

   Ett undantag står kvar (GR-20261007-r100-om#BÖR-3, i backloggen). I den äldre utforskningen med riktningar
   (`NWP_KANDIDATFLODE=av`) raderas omgångarnas bilder som ägaren dömt blint i dashboarden utan att sparas. Ingen kund
   använder den vägen i dag.

   Det sparade registreras med ett namnbyte från en dold katalog innan något raderas, och historikens post pekar på det
   (`sparat`). Faller sparandet, eller avbryts det, raderas inget och ingen historik skrivs. En dold rest efter ett
   sparande som dödades tas bort vid nästa omtag, när processen i dess namn inte längre finns. Kandidater som ägaren
   inte dömt sparas inte.
2. **Tempkatalogerna i /tmp och $TMPDIR** (`kontroller/stadning.py`, punkt 4). Registreringen är ägarfilen
   `.nwp-agare.json` i katalogen, med körningens pid, starttid, vad och katalogens egen sökväg. Den skrivs av
   `korregister.egen_tmp` i `kontroller/korregister.py`, som verktygen med repots prefix nu använder. Kommandot
   `korregister.py tmp` kräver `--pid`.

   Bara en katalog med en giltig registrering och en avslutad körning raderas. En pid räknas som levande också när
   signalen nekas (EPERM), och starttiden jämförs som en tidpunkt. En katalog med prefixet men utan giltig
   registrering är en äldre rest: den raderas aldrig och redovisas för sig med sökväg, storlek och ålder.

   "Den aktuella körningen" i ägarens ord är körningen som katalogen är registrerad på, alltså den som skapade den, och
   inte bara den körning som städar. Granskningen GR-20261007-r100 (BÖR-4) frågade vilken läsning som gäller, och ägaren
   bekräftade den byggda 2026-10-07, ~08:15Z, i frågeverktyget. Ägaren valde alternativet "Körningen katalogen hör
   till (Recommended)". Alternativets text, som ägaren såg den:

   > Så är det byggt i r100. En registrerad katalog raderas när körningen som skapade den har slutat och katalogen varit orörd i ett dygn. Exempel: underhållet kraschar i natt och lämnar en registrerad tempkatalog; nästa natts underhåll raderar den. Oregistrerade rester raderas aldrig, de listas bara med sökväg, storlek och ålder.

   Det andra alternativet, "Bara körningen som städar", valdes inte. Med det hade en registrerad katalog efter ett
   underhåll som kraschat stått kvar som äldre rest tills ägaren avgjort den. Koden är oförändrad.
3. **Symlänkar och föräldrar.** Ingen symlänk följs. Städningen prövar med lstat och `os.walk` med `followlinks=False`
   och raderar med `shutil.rmtree`, som går med filbeskrivare: en länk som byts in mellan provet och raderingen följs
   inte, och en länk i en registrerad katalog tas bort som länk. Bara katalogen själv raderas, och bara när den är en
   riktig katalog direkt under /tmp eller $TMPDIR. /tmp, $TMPDIR, scratchpads rot och andra gemensamma föräldrar
   raderas aldrig. En scratchpad-rot som är en symlänk följs inte alls.
4. **Sessionernas arbetsytor.** En arbetsyta tas bort först när varje vanlig fil i den, oavsett ändelse, är registrerad
   eller går att återskapa. Det gäller rapporter, bilder och versionsunderlag. Bara det bevisligen härledda undantas:
   `node_modules/`, `__pycache__/` och, i en riktig venv med `pyvenv.cfg` i roten, venvens egna kataloger.
   Skärpt 2026-10-08 (granskningen GR-20261007-r100-om, KAN-B): en riktig venv har också `bin/python` och
   `lib/python3.*/site-packages`, och bara venvens egna delar undantas (`lib/python*/`, `include/site/`, tolken,
   aktiveringsskripten och de ingångar som ett pakets `RECORD` listar med samma sha256). Projektets egna `lib/`,
   `bin/` och `include/` prövas, också när venven ligger i projektets rot.

   Registrerad är en fil vars sha256 står i `underlag/granskningar/FORTECKNING.jsonl`, i ett `VERSION.json` eller i ett
   omtags `KVITTO.json` (aldrig i en dold katalog), med den registrerade filen kvar i `underlag/`. En sökväg i en
   förteckning eller ett kvitto godtas bara när den är relativ, utan `..`, och ligger i `underlag/`. Att gå att
   återskapa betyder att filen finns byte för byte som en blob som nås från en ref i huvudutcheckningens git (`git
   rev-list --objects --all`); ett löst objekt eller ett som bara nås ur en reflogg räknas inte.

   Annars väntar arbetsytan på ägaren, med listan över filerna. Skyddet för levande sessioner står kvar.

Räckvidd:
- Punkt 3 i städregeln (processerna) är oförändrad.
- De tempkataloger med repots prefix som finns på maskinen från före ändringen saknar registrering. De redovisas som
  äldre rester och väntar på identifiering.
- Eftersom varje fil i en arbetsyta nu prövas kommer de flesta gamla arbetsytor att vänta på ägaren i underhållets
  rapport, med listan över sina filer.

Efter sammanslagningen (2026-10-07):
- Städningen är påslagen igen. Dashboarden startades om från f652b63 utan `NWP_STADNING=av`.
- En torrkörning före omstarten (10:57Z) skulle radera nio tomma arbetsytor från avslutade sessioner (20–29 september)
  och rensa npm-cachen. Alla worktrees står kvar, eftersom inget är pushat.
- Rättelse av en anteckning härifrån: en nyskapad worktree vars gren står på main tas inte bort. Städregeln tar bara
  bort en worktree vars gren fått egna commits; en gren utan egna commits räknas som okänd och väntar på ägaren
  efter ett dygn. En worktree med ändringar det senaste dygnet eller en levande process står också kvar.
  Prövat med en torrkörning efter pushen 2026-10-07 ~13:55Z: alla worktrees står kvar, de aktiva med
  ocommittade ändringar.
- Granskningens återstående fynd står i backloggen: GR-20261007-r100-om#BÖR-3 och KAN-A–E. KAN-A, att en dom med
  U+2028 försvinner tyst ur domloggen, görs i gren C1.

## Tillägg 2026-10-07: skisskritikens kompetens och sessionerna som bedömer eller forskar

**Status:** gäller.

Hör till ägarens uppdrag 2026-10-07 om kompetensens användning och tillförlitlig rapportering, punkt 1 och tillägget.
Uppdraget står ordagrant i tillägget ovan, "kompetensens användning och tillförlitlig rapportering".

Claude hade skrivit att skisskritiken "har ingen tilldelning i metodkartan, så tjänsterna ska nekas där". Ägaren frågade:
"Vadå saknar tilldelning i metodkartan?" Claude förklarade luckan och att slutsatsen var fel. Då svarade ägaren,
ordagrant:

> Du behöver ju fixa luckan där med de verktyg vi har tillgängliga

Gjort (grenen `skisskritik-kompetens-20261007`, ovanpå gren B):

1. **Rollen kritik** i metodkartan (Kompetenserna) gäller skisskritiken och granskningens första pass i läget full.
   - Kärnan: `visuell-niva.md`, `referenser-professionella.md`, Impeccables `critique.md` och `craft-floor.md`. Skälen
     står i kartan.
   - Verktygen är granskarens form av förhandsvisningen och detektorn (`--granskare`). Förhandsvisningen lägger sina
     bilder i kandidatens `granskare/`, aldrig i skaparens varv. Den tar 390, 768, 1280 och 1440, menyn öppen,
     tangentbordet och reflow 320, och ger ingen byggkod, inga loggar och inga spårfiler.
   - Refero och Mobbin nås genom kundvakten, för egna jämförelser med förebilder av samma slag.
   - uxsok tillförde inget i provet och har ingen uppgift i rollen; skälet står i kartan.
   - Prompten pekar på blocket i stället för att bära egna kriterier.
2. **Blindningen** är skärpt. Skaparens text, uppdrag, referenspaket och kod nekas, och dessutom spårfilerna och
   sessionernas transkript. Ett blint pass får bara verktyg som aldrig ger kod; `kompetens.py --prova` fäller ett annat.
   - En verklig session med kritikens egna argument visade en läcka: `forhandsvisa.py … --granskare | grep -r <ord>
     underlag/<slug>` släpptes igenom och gav skaparens RIKTNING.md. `tail` och `head` med en nekad sökväg och Read
     nekades.
   - De läsande skalkommandona nekas nu i de blinda sessionerna. Samma prov därefter: alla fem försöken nekades.
3. **SKISSKRITIK.json** bär kandidatens version när kritiken började, med samma hash som fotograferingen ger. Den bär
   också bilderna kritiken fick, det den bevisligen såg och kompetenskvittot.
   - Det belagda räknas ur transkriptet: en bredd eller ett tillstånd räknas bara ur en bild som lästes och är hel. En
     tom eller saknad 768-bild står som inte bedömd, också när svaret nämner den, och skaparens uppdrag säger det.
   - Kvittot visar kärnan, de valda alternativen, verktygsanropen och tjänsternas anrop med utfall.
4. **Tiden är mätt.** Två verkliga sessioner med granskarens modell (`claude-sonnet-5-5[1m]`) körde på en syntetisk
   skiss utan kunduppgifter, med kärnan, fyra bredder, menyn, detektorn, Refero och Mobbin.
   - Mätningarna tog 107 s och 109 s väggtid, med 31 och 33 turer. Den andra startade medan en annan worktrees rökprov
     körde.
   - Den äldre kritiken, som bara såg bilderna, tog 49 s på en verklig skiss (2026-10-06).
   - `FRIST_SKISSKRITIK` står kvar på 480 s, 4,4 gånger den längsta mätningen. Marginalen gäller det mätningen inte
     prövade: riktiga foton, byggkön när tre skisser bygger samtidigt och tjänsternas svarstid.
   - `SKISSKRITIK_RESERV` är fristen plus skaparens svar, 900 s.
   - Skaparens del av försöket är oförändrad: 27 av 45 minuter. Den totala tiden per kandidat ändras inte.
5. **De andra sessionerna har roller:** researchen (forska), jämförelsen (jamforelse) och granskningens andra pass
   (motivering).
   - Kvittona står i FORSKNING.json, JAMFORELSE.json och KRITIK.json.
   - Metodkartans lista över sessioner utan block har skaparen och förbättringsrundan i läget full, med prövbara skäl.
     `kompetens.py --prova` jämför listan med koden.
6. **Metodlåset:** tre nya källor låstes med `metod.py --las`. `metod.py --prova` och `kompetens.py --prova` är gröna.
7. **Proven:** `kontroller/rokprov/revision/prov_skisskritik.py` har åtta fall och ingår i rökprovet. Fallen var röda
   mot 63c09c5 och är gröna här.

**Återstår:**
- Ingen verklig skissomgång med kundmaterial har gått med rollen kritik. Mätningen gällde en syntetisk skiss.
- Researchens egna prov i Refero och Mobbin, jämförelsen och granskningens två pass är inte körda i en verklig session.
- Skaparens sessioner har samma lucka i skalet mot de andra kandidaternas kod (`… | grep -r` förbi andra_nekas). Den
  är inte stängd här, eftersom skaparens behörigheter inte ingår i uppdraget.
- Dashboardens text säger att den interna granskningen "såg bara bilderna". Den ska säga den renderade sidan och
  verktygens mätningar (gren D). Kritikens kvitto syns ännu inte i kompetenskedjan i vyn (gren C och D).
- Ägaren avgör om kritikens frist ska kortas för att ge skaparen mer tid. Med 300 s skulle skaparen få tre minuter till.

## Tillägg 2026-10-07: kundvaktens namnprövning efter GR-20261007-r102-om

**Status:** gäller.

**Delvis ersatt av:** tillägget 2026-10-07 om kundvaktens adresser, rubriker och orter (sist i den här filen), i fråga
om punkt 1: ett par först i en mening stoppas som helt par, och en rubrik som bara är ett par är ett säkert namn.
Övrigt gäller.

Omgranskningen GR-20261007-r102-om (privat, `underlag/granskningar/`) godkände gren B men fann tre BÖR i kundvaktens
namnprövning och proven. Grenen `kundvakt-namn-20261007` rättar om#B1–B3, K1, K3 och K4. Ägarens regel gäller som
förut: Refero och Mobbin ska fortsatt få generiska researchfrågor utan kunduppgifter. Vad som prövas i detalj står i
beskrivningen i `kontroller/kundvakt.py`.

1. **Generiska frågor går (om#B1).** Ett par med stor bokstav blir inte längre ett personnamn bara för att det står i
   briefen. Briefens §7, där förlagorna och typsnitten står, läses bara för kundens orter och mailto-länkar.
   Typsnittsord och fler webb- och designtermer i EJ_NAMN delar paren, ett ord som bara har stor bokstav för att det
   inleder en mening räknas inte, och rubrikerna ger inga osäkra par. Granskarens sju falsklarm släpps.
2. **Namnen stoppas i fler former (om#B2).** Ett namn efter ett personord eller före en roll, i en attribution efter ett
   citat (också Recos form), i en mailto-länk eller med ett vanligt förnamn eller efternamnsled stoppas också ord för
   ord. Två av tre namn, versaler, gemener, alla alfabetens bokstäver, hopskrivna namn (bindestrecket tas bort, från sex
   bokstäver), genitiv och dubbel URL-kodning stoppas. Vakten läser Bokadirekts omdömes- och tjänstefiler och
   fritexten i VERKSAMHET.json. De döda personfälten är borta, eftersom schemat inte har några.
3. **Där precisionen och täckningen krockar** går felet åt det säkra hållet:
   - ett par med stor bokstav utan personsammanhang, som inte är ett typsnitt, en förlaga i §7 eller ett ord ur EJ_NAMN,
     stoppas som helt par;
   - kundens ort efter ett platsverb ("Vi verkar i …") stoppas som ort, också i §7. Förut stoppades den av en slump, som
     ett personnamn;
   - ett säkert namn stoppas ord för ord, också när ordet är vanligt;
   - ett förnamn som också är ett vanligt ord (Per, Bo, Max) håller ihop ett par och stoppar paret, men inte ordet: annars
     stoppades frågor som "price per hour".
4. **Proven.** prov_startkvitto.py:
   - fall 10 och 10a–10c, med en fixtur i verkliga datas form som är giltig mot schemat;
   - 2b (K1), 2c (N06), 4 (N29), 6 (N10) och 12 (N26 och N27).

   prov_revision.py ger två regressionsfall mode standard (om#B3). En tjänst vars alla bilder saknas ger en felrad (K1),
   och beskrivningen av status i startkontroll.py är ombruten (K3).
5. **Mot verkliga data**, prövat utan nät och skrivningar. Den enda kunden med underlag gav 4 personnamn; förut gav den 3
   par, varav ett inte var ett namn. Granskarens 21 frågor släpps. Av 92 verkliga tjänsteanrop i sessionsloggarna stoppas
   samma 2 som förut, för kundens namn, och inget av namn- eller ortprövningen.
6. **Återstår:**
   - Recos omdömesfil och RESEARCH.md läses inte. Ett namn som bara står där skyddas inte; hos den verkliga kunden citerar
     sidtexten alla omdömen.
   - Fritexten `not` i den verkliga kundens VERKSAMHET.json har en gatuadress och en ort som inte står i adressfälten.
     `skapande.forbjudna_termer` läser dem inte, och namnprövningen tar bara orter efter ett platsverb.
   - Ett namn utan personord, vanligt förnamn och efternamnsled, först i en mening, räknas inte. Ett osäkert par i en
     rubrik räknas inte heller.
   - Ingen verklig designkörning har observerats med rättelsen.
   - Posterna om#B1–B3, K1 och K4 verifieras av granskningen. om#K2 hör till gren C.

## Tillägg 2026-10-07: kandidaternas oberoende och kritikens blindning

**Status:** gäller.

Två BÖR ur granskningen GR-20261007-r103 (privat, `underlag/granskningar/`), båda förbefintliga, rättade på grenen
`kandidatskydd-20261007`. Behörigheterna står i `kontroller/kandidater.py`; proven i
`kontroller/rokprov/revision/prov_skisskritik.py` (fall 9 och 10, och fall 3 för domloggen, röda mot 13743c9, gröna
efter). Punkt 1 stänger skaparens skallucka, som tillägget om skisskritikens kompetens ovan lämnade kvar.

1. **Kandidaternas oberoende (r103#B1).** Läsförbuden för de andra kandidaternas kataloger gällde Read, Grep och Glob
   men inte skalets egna läsare: en skaparsession kunde läsa en syskonkandidats kod med `grep`, `cat`, `find` m.fl.,
   ensamt eller i en pipe efter ett tillåtet kommando. Nu nekar `andra_nekas` också de läsande skalkommandona
   (`LASANDE_SKAL`, `skal_nekas`), så förslagen förblir verkligt olika (ägarens uppdrag 2026-10-06, punkt 5). Skaparens
   egna verktyg (förhandsvisningen, typsnitten, design, detektorn, uxsok) och Write, Edit och Read i det egna projektet
   går som förut; prövat i en verklig session utan kunddata. Samma förbud bär varje session som arbetar med en kandidat.
2. **Kritikens blindning (r103#B2).** `blind_nekas` räknade upp vad som nekades i `underlag/<slug>` och släppte
   `REFERENSUPPDRAG-*.json`, `TJANSTEUPPDRAG-*.json` (skaparens referensskäl) och `RESEARCH.md`. Regeln är vänd: bara
   en uttrycklig lista är läsbar (`BLIND_LASBART`: briefen, kundens fakta, research, texten, beställningen, bilderna,
   metoden och kandidatens egna bilder), och research på begäran och referensbeslutet nekas med mönster också när de
   uppstår medan sessionen pågår. Kritikens kärna, bilder, besökaruppgift och verktygens utdata är oförändrade; prövat
   i en verklig session.

**K4-beslutet (r103#K4; först Claudes, bekräftat av ägaren 2026-10-07 ~13:50Z).** De blinda sessionerna nekas `RIKTNINGSHISTORIK.json` och
`DESIGNDOMAR.jsonl` som filer. Ägarens aktuella domar får kritiken som förut genom prompten
(`skapande.kritikrader(..., aktuella=True)`), där urvalet är avsiktligt. Skälet är ägarens ord 2026-10-06: "Mina
tidigare underkännanden ska inte omvandlas till en allt smalare uppsättning tillåtna uttryck" — kritiken dömer skissen
mot ribban och ägarens aktuella domar, inte mot tidigare riktningar. Beslutet är lätt att ändra: en tom
`kandidater.BLIND_HISTORIK` öppnar filerna igen, och raden `blind` i metodkartans block kritik säger var. Ägaren
svarade i frågeverktyget "Ja, neka historiken (Recommended)" på frågan om kritiken ska nekas historiken.

**Återstår:**
- Ingen verklig skissomgång med kundmaterial har gått med de skärpta behörigheterna; proven gäller en syntetisk kund.
- Förbuden gäller sessionens verktyg, inte byggena. En sidas kod körs när den byggs, innanför processgränsen, som
  begränsar skrivning och nät men inte läsning (Sandlådan i `kunskap/skapandeflodet.md`). Där vilar kandidaternas
  oberoende på att skaparna inte läser via bygget; en läsgräns per kandidat i processgränsen vore nästa steg.
- Glob visar namnen på de nekade filerna i `underlag/<slug>` (innehållet nekas). Namnen bär inga skäl.
- r103#K1–K3 (provtäckning, den syntaktiska kart-mot-kod-jämförelsen, kundvakten) står kvar som KAN.


## Tillägg 2026-10-07: C1:s stoppväg, beläggbilaga och slutbesked efter granskning

**Status:** gäller på grenen ateljeslut-20261007 som genomförande av det redan beslutade uppdraget; sammanslagning återstår.

Detta är rättelser efter GR-20261007-r106 och Codex övertagande, inte nya smak- eller ägarbeslut. Det tidigare
C1-avsnittet bevaras som historik. Dess anvisning att bekräfta en äldre dom med en ny domrad ersätts här av bilagan.

- Arbetarens CLI och importer använder samma modulinstans. Stoppet når därmed kandidatflödets sessioner, även
  skisskritik utan session_pid. Stopp avslutar sessionerna och ger dem sluttid och utfall; läget full prövar stoppet
  efter varje session. SIGINT hanteras som SIGTERM, och andra avbrott ger felstatus och avslutar sessionerna.
- Startkontrollens nekande ger besked och slutkod direkt, med en egen post som lämnar den förra körningens post
  gällande. En status som bara säger startar arkiveras inte som ett tidigare resultat.
- Ett efterhandsbelägg binds till en befintlig domrads sha256 i DESIGNDOMAR-belagg.jsonl. Domloggen, domens tid och
  ordningen ändras inte. En vidarebefordrad AI-bedömning blir aldrig ägarens beslut. Inga verkliga domrader eller
  belägg ändras i rättelsearbetet. Avsändarnas kontrakt finns i README och kunskap/skapandeflodet.md.
- Efter en oläsbar domrad är vägen vidare ett nytt uttryckligt beslut från ägaren eller ett uttryckligt körläge.
  Historiska rader skrivs inte om. Belägg som bara innehåller blanktecken räknas inte.
- Kandidatflödet utan valbara kandidater, även med tom kandidatlista, ger slutkod 6. Val, jämförelse och putsning
  visas som ej bedömt; avslag och godkännande visas för sig. Vid två domar samma sekund väljs ägarens avsändare.
- Redovisningen kopieras atomiskt via en exklusivt skapad tempfil. Varken en länk på målet eller ett planterat
  förutsägbart tempnamn följs. Två poster samma sekund får olika kataloger.

**Kontroll:** prov_ateljeslut.py prövar den verkliga CLI- och stoppvägen med attrapper samt posternas och domloggens
kontrakt. Röda basprov, gröna rättelseprov, mutationer och rökprov redovisas i överlämningsspåret; en attrapp visar
lokal mekanik, aldrig fungerande modellåtkomst eller designkvalitet.

**Lämnat:** dashboardens användning av avsändartyper och slutposter hör till gren D (KAN-1). Skisskritik vid
återupptagning är separat arbete (KAN-3). Helbyggets skydd av ateljéprotokollet och DOM.json:s avsändarnamn måste
samordnas med r105; omgranskningen av r105 fann kvarstående fel, så integrationen är inte verifierad (KAN-4 och
KAN-7:s andra del). Verklig återupptagning med --resume och kontexten i nästlade Claude-sessioner lämnas till Claude.

Rökprovets stubb för referenstjänstens session läser en egen syntetisk nyckelfil. Den ska gå med tomt HOME och
aldrig behöva användarens verkliga hemligheter; det fulla provet i en isolerad kopia avslöjade beroendet.

Den separata Codex-granskningens motfall ingår också: sessionsstarten och pid-registreringen hålls ihop mot stoppet,
och en signal i huvudtrådens start skjuts upp tills barnet finns i registret. Stopp under städning eller redovisning
bokförs i slutposten utan att avbryta avslutet. JSON-posternas temporära filer skapas exklusivt, och en oläsbar
rad efter ägarens senaste dom ger inget aktuellt godkännande i slutposten. Proven använder bara syntetiskt underlag
och sovande attrapper; verklig återupptagning och nästlad modellkontext återstår till Claude.

## Tillägg 2026-10-07: versionsbundna övergångar i det befintliga flödet

**Status:** gäller på grenen flodesovergangar-codex-20261007; sammanslagning och driftaktivering återstår.

Genomförande av ägarens tillägg om befintliga flödet under Codex övertagande. Ingen ny smakregel, skisskvot,
publiceringsrätt eller orkestreringsplattform införs. De tidigare gränserna för privat material och externa anrop gäller.

- Förberedelsen körs i ateljéns befintliga arbetare före designgodkännande och före installation av webbprojektet.
  Ett privat förslagspaket publiceras till samma arbetsfiler som flödet läser, med innehållsbundet kvitto, bevarat
  äldre underlag och ett synligt avbrottsläge. Kundens önskemål blir inte automatiskt avtal eller bekräftade fakta.
- Kritik och kandidatversion binder körning, försök, kod, tillgångar och kundunderlag. Gamla försök arkiveras och
  räknas inte som aktuell kritik. Vinnaren för över den fotograferade versionens material; borttagna filer återkommer
  inte ur äldre projekt. Konflikter i målvägar prövas innan installationen ändrar filer.
- Flödesvyn använder samma CLI-ingång, start-id och lås som terminalen. Läsning och kandidatval beställer ingen
  körning; nästa handling kräver ett eget klick. Stopp går förbi startlåset. Samma start-id återanvänder beställningen.
- Flödesvyn visar fem separata besked: session, teknik, designgranskning, ägardom och leverans inom sin omfattning.
  Historiskt och saknat är inte grönt. Skisskritik döljs före ägarens första val; helbyggets designgranskning döljs
  före ägarens dom på samma bygge. Exportens filer och dess godkännanden har var sin aktualitetskontroll.
- Exporten byggs först i en registrerad egen katalog och byter mål först när kontrollerna lyckats. Tidigare export
  bevaras; fångbara signaler under bytet återställer den. SIGKILL kan kräva återställning ur det bevarade arkivet.
  EXPORT.json är ett privat versionskvitto, inte kundmaterial i det publika repot. Testexport innebär aldrig
  verifierad driftsättning eller kundklar leverans.
- Titel- och beskrivningslängd är information. Saknade metadata och sakfel är fortfarande fel; en godtycklig
  teckengräns används inte som kvalitetsbevis. Källorna och gränserna står i berörd kunskapstext.

**Verifiering:** syntetiska prov genom CLI, arbetare, HTTP-ingång, export och webbläsare; separata granskningar,
röda basfall, gröna rättelser och mutationer i egna kopior. Slutligt rökprov, commit och återstående integration
redovisas i överlämningsspåret. Verklig modellåtkomst och designkvalitet är inte bevisade av dessa prov.

**Kvar i denna etapp:** helbyggets processvakt och start från flödesvyn, passbundna A/B-parametrar och ett förberett
metodförsök, sammanhängande förloppsprov samt Kundstart och Kirurgens särskilda tillägg. Dashboarden på 4771 ändras
inte under Codex övertagande. Inget pushas eller slås ihop till main.

## Tillägg 2026-10-08: mätbara resursmått och namngivet skisspass

**Status:** gäller på grenen flodesovergangar-codex-20261007; integration och verkligt metodförsök återstår.

Genomförande av uppdragets femte etapp, utan ändrade modellstandarder eller nytt kostnadsmandat. Resursrapporten
summerar råvärden, särredovisar ofullständig observation och räknar identifierade kopior en gång. Rapporterat
listpris är inte faktura eller abonnemangskvot; tid från öppnad vy till dom är inte aktiv arbetstid. A/B-mått binds
till slutpostens egen sessionslogg och använder inte ett antaget kontextfönster.

NWP_SKISSSKAPARE_EFFORT och NWP_SKISSSKAPARE_MODELL kan pröva bara skaparen och dess svar på kritik inom
skissförsöket. Research, plan och granskare behåller sina inställningar. Begärd konfiguration skiljs från faktisk
observation. Mekaniken prövas med syntetiska svar; inget verkligt modellförsök eller generell kvalitetsvinst hävdas.
## Tillägg 2026-10-07: skyddet av ägarens dom och byggets processer

**Status:** gäller.

**Varför:** omgranskningen av gren A (GR-20261007-r101-om, och -om2 för integrationen med gren B) fann luckor som är
äldre än grenen. Ett eget skript i bygget kunde få "ägaren godkänner: ja" räknat, och byggets processer kunde leva kvar
efter en signal. Ägarens uppdrag samma dag (tillägget ovan, punkt 4, 5 och 7) håller ägarens beslut isär från allt
annat, och enligt uppdraget om dokumentations- och rapportstrukturen (tillägget 2026-10-06, punkt 7) får automatik inte
"hitta på beslut eller godkännanden".

**Rättelsen:**
1. **Hashlistorna och DOM.json prövas mot kor.sh:s minne** (#BÖR-1, #KAN-3).
   - kor.sh håller listornas sha256, och sha256 för DOM.json när den låstes, i minnet och ger dem till korslut.
   - En omskriven lista ger slutkod 3, och en ändrad DOM.json ger slutkod 3 även när listan förfalskats.
   - Kopian `korningar/<körning>/DOM-START.json` gör att ägarens äldre domar räknas, aldrig de som tillkom.
   - Byggets Write och Edit nekas för listorna och körningarnas protokoll.
2. **Vakten** (`kontroller/korvakt.py`; #BÖR-1 punkt l, #BÖR-2, #KAN-2, #KAN-5).
   - Vakten lever i en egen session. Den följer byggets processer genom deras unika id, också dem som lämnat sin
     session och bytt förälder, och stoppar dem innan något jämförs eller låsen släpps.
   - claude startas i en egen processgrupp. En signal går till hela gruppen, och SIGKILL följer efter `NWP_FRIST`
     sekunder.
   - Dör kor.sh gör vakten avslutet och skriver posten (slutkod 4, eller en kort post när kor.sh dog före bygget), så
     att ägarens dom kan sparas direkt.
3. **Slutbeskedet** (#KAN-1, #KAN-4, #KAN-6; GR-20261007-r101-om2#KAN-5).
   - Slutkoden är postens också när terminalen stängts.
   - Ägarens senare dom räknas efter en körning som dödats.
   - En körning utan post sägs som avbruten, eller som en post som inte kunde skrivas (`UTEBLEV.json`).
   - En utgång före bygget utan post (ett kommando som faller under set -e, eller en trasig fil som läses in) ger en
     kort post med skälet.
4. **kor.sh läses i sin helhet** innan något körs: en ändring av filen under ett bygge påverkar inte körningen.

**Gränsen** (`README.md`, Helbyggets slutpost):
- Ett eget skript kan fortfarande nå förbi skyddet på tre sätt: genom att ändra kontrollerna (kor.sh, korslut.py,
  korvakt.py eller Python-miljön, som är skrivbara när sandlådan är av), genom att döda vakten, eller genom att starta
  en process via launchd eller byta förälder två gånger innan vakten sett den mellersta.
- Dödas både kor.sh och vakten saknas posten.
- Gränsen på processnivå är ett eget steg i backloggen.
- Att svaret "Ja, som den är" räknas som godkännande är fortfarande Claudes tolkning.

**Prövat:** `kontroller/rokprov/revision/prov_slutpost.py` i rökprovet; fallen för rättelserna var röda mot 1f0b035.
Granskarens scenarier kördes före och efter, och mutationer i egna kopior. Vakten är prövad med en attrapp i stället för
claude, inte med claudes egna verktygsskal; ingen verklig körning har gått med vakten.

**Kvar:** gren D (dashboarden), där också GR-20261007-r101-om#KAN-7 hör hemma (ett eget ägarvärde för "Ja, efter små
ändringar"). Backlogposterna markeras inte här: klar sätts med commit när rättelsen slagits ihop, och verifierad först
när en senare granskning säger det.

## Tillägg 2026-10-08: bekräftat avslut och atomisk byggreservation

**Status:** gäller på rättelsegrenen; sammanslagning och driftsättning återstår.

Genomförande inom ägarens övertagandeuppdrag och tillägget om befintliga flödets övergångar. R105:s blockerande motfall rättas: vakten bevarar en befintlig slutpost efter kor.sh:s död bara när korslut bekräftat exakt dess hash genom körningens privata rör. En obekräftad post bevaras separat, skyddet mäts och avslutet räknas om. Bekräftelsen är intern processkommunikation, inte ett påstående i postens JSON.

Helbyggets reservation sker med ett beständigt flock-lås som kor.sh och vakten håller genom avslutet. PID-filen är status. C1:s ateljéprotokoll och domarnas beläggbilaga omfattas av innehålls- och typkontrollen samt Write/Edit-nekanden. Dessa rättelser bygger på isolerade prov med syntetiska sessioner och innebär ingen verifiering av verkliga Claude-verktygsskal, extern åtkomst eller designkvalitet. README beskriver skyddets kvarvarande processgräns.

## Tillägg 2026-10-08: uttryckliga övergångar till helbygge och kundrepo

**Status:** gäller på flödesgrenen; sammanslagning och drift återstår.

Ägarens beställda övergångar återanvänder ateljéns startjournal, den befintliga byggvakten och exporten. En aktuell
ägardom krävs före helbygge. Export är en teknisk förberedelse och innebär inget publiceringsmandat. Samma start-id
beställer aldrig två arbeten; ett stopp före processstart består. Kundens lås hålls från reservation tills arbetets
processer avslutats. Processbeskedet och det versionsbundna resultatkvittot hålls isär. Inga nya köer, schemalagda
starter, designregler eller externa rättigheter införs. De lokala proven använder syntetiska processer; verkliga
modellsessioner lämnas till Claude enligt övertagandets gränser.
## Tillägg 2026-10-08: Kundstarts lokala ärende och överlämning

**Status:** gäller på grenen kundstart-kirurg-codex-20261008; inte sammanslaget eller driftaktiverat.

Genomförande av ägarens beställda Kundstart inom befintligt repo. Ingen ny kommersiell regel, publiceringsrätt,
lagringsperiod eller modellkostnad godkänns här. Kirurgens förbättringsloop är nästa separata genomförandedel.

Kundens ord, uppgifter och rättelser lagras före AI-bearbetningen i ett privat revisionshanterat ärende. Kund-API:t
har personliga roller och saknar administrativa modell-/kommandoingångar. Kundens fakta, förfrågan och acceptans av
ett faktiskt definierat erbjudande är skilda handlingar. Sen modellutdata får inte skriva över nyare kundval.
Överlämningen prövar källrevision, exakt målrot och skrivna filhashar, och kan återupptas eller återställas utan
överskrivning av främmande ändringar. Mottagna kompletteringssvar blir inte automatiskt lösta kritiska frågor.

Den befintliga dashboarden får en Kundstart-vy på grenen. Sena svar binds till rätt vy och ärende; privata lokala
utkast behåller sin grundrevision. Ingen server, modell, kontakt eller återkommande process startas av en läsning.
Gallring kräver ett verkligt lagringsbeslut och ger ett bestående spärrat läge vid avbrott. Egna backupkopior hanteras
med SQLite onlinebackup; återställning gäller ny rot med aktuell gallringsjournal och återkallade gamla länkar.

Professionsstödet i kunskap/kundintervju.md är omskrivet för verkliga ingångar här och läses till modelladaptern.
Kunskapstextens äldre Runtime-väg finns i Git-historiken. Mått skiljer begärd från observerad modell, bevarar misslyckade
försök och anger saknad kostnad som okänd. Läsning, schemagiltighet och anropsmetadata bevisar inte yrkeskvalitet.

**Prov och begränsning:** syntetiska transportdubblar, riktig lokal SQLite/HTTP/Chromium, negativa behörighetsfall,
avbrott och separata granskningar. Inga riktiga AI-, MCP- eller kundanrop. Slutprov och commit redovisas i uppdragets
rapport. Live-AI, offentlig drift, databehandlingsbeslut, verklig intervju-/designkvalitet och mänsklig användningsprövning
återstår. Det privata CLI-abonnemanget används inte som antagen serverlicens. Inget pushas eller slås ihop till main.

## Tillägg 2026-10-08: Kirurgens avgränsade observationer och försök
**Status:** gäller för den lokala förbättringsvägen; ingen skarp aktivering eller nytt ägarmandat.

Ägarens ord: ”Bygg två sammanhängande förmågor inom dagens system” och ”Skilj ditt byggmandat från den framtida agentens rättigheter.”

Kirurgens befintliga vy får versionsbundna signaler, diagnos, plan, disposition, stickprov och paus. Befintlig spaning
redovisar källhälsa; Kundstart observerar aktuell överlämning utan att kopiera kundsvar till förbättringsregistret.
Avgränsade lokala regressionsförsök behöver separat giltigt klassmandat, fryst facit, processgräns, totalbudget och
oberoende granskning. Registrerat kundarbete har företräde. Aktiva införanden, publicering och eftereffekt är inte
självauktoriserade. Ingen ny modell, extern anslutning eller återkommande drift har startats genom implementationen.

Räckvidd och kvarstående live-/införandeprov: `kunskap/kirurg-forbattring.md`. Äldre beslut och rapporter bevaras.

## Tillägg 2026-10-08: Kundstarts källa genom skapandeflödet

**Status:** gäller på integrationsgrenen; ingen sammanslagning eller driftaktivering.

Genomförande inom ägarens beställda sammanhängande kundförlopp. En senare kundändring ska upphäva gammalt underlag
också när snapshotfilerna ligger kvar. Start, kort publicering och godkännandets aktualitet prövar därför den levande
källan och hela överlämningsmanifestet. Saknad markör, trasig databas eller manifest innebär aldrig återgång till ett
äldre godkännande. Den läsande kontrollen skapar inga SQLite-sidofiler och släpper sina lås även när den faller.

Ärendelagret får inte vara läsbart för byggets egna skript. Ett helbygge i en rot med Kundstarts lager kräver den
befintliga sandlådan; det överlämnade kundmaterialet är fortfarande åtkomligt. Detta inför ingen ny ägargrind eller
rätt att starta modeller. Ingen riktig modell-/MCP-session eller kundkontakt har körts under övertagandet.

Förloppsprovet använder ordinarie kodvägar med lokala transport-, modell- och renderingsdubblar. Fem syntetiska
flertursfall visar bevarade källor, omfattning och ändringars följder. Dessa prov är utvecklingsbevis, aldrig ett
oberoende kvalitetsmått, ägarens verkliga godkännande eller belägg för en bra autonom intervju.


## Tillägg 2026-10-08 — formulärens felvägar, G04/G05

**Status:** gäller som avgränsad rättelse på arbetsgrenen; ingen driftaktivering eller extern sändning.

Ägarens käll- och professionsuppdrag rättar mottagaren som tappade text vid fel och kunde avisera utan lagringskvitto.
Validering ger 422 med texten kvar och fältnära fel; en läsbar för stor bild ger 413 med texten kvar. Oläsbar eller
helt för stor kropp lovar inte återställning. Utan bekräftad lagring försöks inget mejl och 503 visar osäker
mottagning med texten kvar. Bekräftad lagring men utebliven mejlacceptans ger 202 och eget mottaget-besked utan
uppmaning att skicka igen. Lyckad lagring och mejlacceptans ger 303 till tacksidan. Uppgifterna hamnar inte i URL
eller felloggen. Demomottagaren är fortsatt en osparande provstubb, inte detta produktionskontrakt.

G05-R kvarstår uttryckligen: det statiska formuläret saknar en individuell identitet före första POST; ett helt
tappat lyckat svar kan därför ge en dubblett vid omförsök. Det kräver ett sammanhängande idempotenskontrakt, inte
bara annan statuskod eller slumpnyckel på servern. Lokala dubbelprov bevisar inte Blob/Resend i drift.

I samma rättelse skyddas metadatafiler från bilagans klientnamn. Lagring, mejl och aviseringskvitto har lokala tidsgränser med avbrottssignal; sena svar fortsätter inte kedjan. Detta är en implementerad felgräns, inte ett nytt leverans- eller idempotenslöfte.
## Tillägg 2026-10-07: byggets läsgräns per kandidat

**Status:** gäller på grenen.

Omgranskningen GR-20261007-r107 (privat, `underlag/granskningar/`) bekräftade den sista kända luckan i kandidaternas
oberoende (r107#K1): byggets profil tillät all läsning utom hemligheterna, så en sidas kod kunde läsa en annan
kandidats källkod och skaparens text i underlaget när sidan byggdes. Grenen `byggets-lasgrans-20261007` stänger luckan
i `kontroller/processgrans.py` (backlogposten B-20261007-kandidaternas-oberoende-byggets-processgrans-hin); modulens
beskrivning och Sandlådan i `kunskap/skapandeflodet.md` säger hur.

1. **Läsgränsen.** Ett bygge av en kandidats projekt nekar läsning som standard. Undantagen är det bygget behöver, mätt
   med en rapporterande profil och kärnans logg under ett verkligt bygge: kandidatens projekt, sajtens delade
   node_modules, kandidatens egen temp, systemets delar, metadata för katalogerna ovanför dem och repots .gitignore och
   .git, som Tailwind läser. Ett stängsel sist nekar `underlag/` och `kunder/<slug>/kandidater/` också om ett undantag
   skulle täcka dem. Kritikens förhandsvisning bygger genom samma väg och har samma gräns.
2. **Det som följer med.** Varje kandidat har en egen temp (`/tmp/nwp-bygge-<slug>/tmp-kNN`), och bygget startar i
   projektet. En node_modules-länk som pekar bort från sajtens vägras, liksom en väg i `kandidater/` utan id och ett
   program som läsgränsen inte släpper: ett sådant program fastnade i kärnan (tillståndet UE, går inte att döda före en
   omstart) när det startades innanför gränsen. Astros telemetri och npm:s versionskoll är av; de körde git i repot,
   läste hemkatalogen och försökte nå nätet.
3. **Samma utdata.** Samma kandidat byggd med 8cc786c och med läsgränsen gav samma filer byte för byte, i worktreen och i
   repokopior där .git är en katalog, en fil eller saknas.
4. **Proven.** `kontroller/rokprov/revision/prov_lasgrans.py` bygger en syntetisk kund på riktigt. Fall 1 och 3–5 var
   röda mot 8cc786c och är gröna efter; fall 2, att ett vanligt bygge ger samma utdata som sajtens eget, är grönt före
   och efter. Codex omprov och mutationer redovisas i den privata genomföranderapporten, med respektive revisionsidentitet.

**Återstår:**
- De delade node_modules är läsbara för varje kandidats bygge och cacherna där (.vite, .astro) skrivbara, så det ett
  bygge lämnar där kan nästa kandidats bygge läsa. Vite kräver att cachen går att skriva. En egen cache per kandidat,
  i projektets astro.config.mjs, stänger det.
- En nekad väg ger EPERM om den finns och ENOENT annars. Namnen går inte att lista, men en gissad väg kan prövas.
- Sajtens eget bygge har ingen läsgräns.
- Tailwinds källsökning ger i repots läge omkring 35 kB fler klasser än sidan använder, i kandidatens och sajtens bygge.
  Det är oförändrat.
- Ingen verklig skissomgång med kundmaterial har gått med läsgränsen. Posten verifieras av en granskning.

**Rättelse i Codex övertagande:** kandidatens identitet prövas före länkupplösningen. En länk till huvudbygget eller
en annan kandidat, skiftlägesalias inne i kundträdet och `..` får inte avaktivera eller byta läsgränsen. Ett annat namn
på själva reporoten, exempelvis `/tmp` i stället för `/private/tmp`, behåller gränsen. Motprov genom riktiga CLI:n
visade läsning av en syntetisk syskonfil i tre sådana fall före rättelsen. Provets nya fall täcker även huvudrotens
alias och säkra ordinarie körningar. Städningen registrerar bara exklusivt skapade kataloger och redovisar fel.
Den äldre Refero-fixturen använder egen syntetisk nyckeltext; inga verkliga nycklar eller MCP-anrop ingår.

Den separata granskningen GR-20261007-r109-codex-oberoende fann en kvarvarande aliasväg när kund- eller
kandidatroten var länkad. Båda vägarna reproducerades genom CLI:n med syntetisk syskonfil. Rötterna förankras nu
före klassificeringen, och fall 7 kräver nekande före barnstart. Det är en rättelse inom samma läsgräns.
## Tillägg 2026-10-07: referensinspektionen och Chrome DevTools MCP (gren H1)

**Status:** gäller.

Gren H1 (`referensinspektion-20261007`) i ägarens uppdrag 2026-10-07 ~14:05Z om full verktygslåda och kundrepon, punkt 7 och
punkt 5 (MCP-delen); uppdraget står ordagrant i tillägget från gren H5 (`canvas-hig-20261007`) och i minnet
`nortropic-agaren-full-verktygslada-kundrepo-uppdrag-20261007`. Ägarens förtydligande samma dag, mottaget via
samordnaren, ordagrant:

> Varje arbetssteg ska uttryckligen aktivera sina tilldelade skills genom skillsystemet där det stöds. Referensfiler som
> saknar egen aktivering ska läsas enligt skillens instruktioner. Saknad aktivering eller misslyckad laddning ska synas och
> hanteras innan beroende arbete fortsätter. Varje tilldelad verktygs-/MCP-uppgift ska genomföras genom ett faktiskt anrop
> och ge ett kontrollerat resultat. Att verktyget finns installerat räcker inte. Dokumentera därefter hur resultatet
> användes. Verifiera detta i den riktiga skaparsessionen. Skilj aktivering, lyckad användning och bedömd kvalitet åt.

**Infört** (proven i `kontroller/rokprov/revision/prov_referensinspektion.py`, tio fall, röda mot 2b4045e och gröna efter;
en rad i `kontroller/rokprov.sh`):

1. Referensens vyer tas ur prototypens källa (`forhandsvisa.BREDDER`): 390 och 1440 alltid, 768 och 1280 per uppdrag
   (`referens.py`, fältet `bredder`; researchen får beställa dem, `kandidater.FORSKA_SCHEMA`).
2. Per mätt element de CSS-regler som träffar (CDP `CSS.getMatchedStylesForNode`), och per sektion sektionens och
   layoutbehållarens regler: bara regeltexten med mediefrågan, högst åtta, aldrig stilmallen (`extrahera.mjs`).
3. Ett DOM-utdrag per sektion utan skript, händelse- och data-attribut, högst 1 500 tecken med markör (`MAX_UTDRAG`).
4. Svepet över bredderna 320–1600 (`--svep`, `SVEP.json`): kolumner, menyknapp, rubrikens rader, bildandel, spill och
   sajtens egna mediefrågor; brytpunkterna står i EXTRAKT.md och PAKET.md.
5. Flera hover- och fokusväljare per uppdrag (högst sex, en bild var, utfall per väljare) och de interaktiva elementen ur
   tillgänglighetsträdet; ingen menyknapp där alla länkar syns är ingen brist (som `kandidater.menyprovet`).
6. Rörelsesekvensen: sidans animationer med namn, längd och trigger (laddning, skroll, hovring, fokus, meny) och spårets
   steg i EXTRAKT.md; spårfilen förblir privat och nekad kritiken.
7. Det kuraterade underlaget `SEKTIONER.md` per sida (bild, mått, typsnitt, regler, utdrag), med materialnoten (samma ord
   som `atelje.MATERIAL`); `research_rader`, `forska_prompt`, FORSKNING.md, PAKET.md och UPPDRAG.md ("Referensunderlag")
   pekar på det i stället för hela EXTRAKT.md.
8. Chrome DevTools MCP 1.10.1 (npm 2026-09-23, Apache-2.0) i `kontroller/mcp/chrome-devtools.json` (`npx` med låst version,
   `--isolated --headless --no-usage-statistics --no-performance-crux`, inmatning, minne och skriptkörning avstängda,
   Playwrights Chromium, nätgränsen `natproxy.mjs` med webbtjänstens regler) i en egen inspektionssession
   (`kontroller/devtools.py`, `--strict-mcp-config`, bara verktygen med uppgift); aldrig i skaparens eller kritikens
   session (kundvakten släpper den inte, `atelje.session_args` bär den inte) och inget på användarnivån. Beslutet per
   verktyg i `kunskap/metodkarta.md` (Tjänsternas verktyg): nio med uppgift, 23 utan med skäl och provdatum;
   `kompetens.tjanstregister` prövar blocket mot `devtools.VERKTYG`. K51 i `kunskap/skillkrockar.md` omprövad.
9. Metodkartans Research-avsnitt beskriver underlaget och profilen; `kunskap/referensjakt.md` (låst källa, `metod.py --las`),
   `kunskap/beroenden.md`, README-kedjans steg 2.
10. Granskarens form: kritikens förhandsvisning (`forhandsvisa --granskare`) mäter med `inspektera.mjs --extrakt-utan-kod`,
    utan CSS-regler, DOM-utdrag, SEKTIONER.md eller klasser i animationsmålen, så att den blinda kritiken aldrig får
    skaparens kod (luckan uppstod med punkt 2 och 3 och stängdes i samma gren).

**Det verkliga provet** (två sessioner 2026-10-07 15:44Z och 15:47Z, modellen claude-sonnet-5-5, mot provets syntetiska
sajt på 127.0.0.1, utan kunddata): aktivering — MCP:n `connected`, 19 verktyg listade, inget utan beslut; lyckad
användning — 13 respektive 14 anrop, alla med kontrollerat resultat i form och innehåll (new_page, emulate 390×844 Slow 4G,
performance_start_trace med LCP 1 322/1 297 ms, CLS 0, TTFB 5/27 ms, fem insikter analyserade, take_snapshot,
get_css_styles för LCP-elementet, list_network_requests, lighthouse_audit: tillgänglighet 95, bästa praxis 100, seo 91;
prestandakategorin utesluter verktyget självt), uppgiften genomförd i alla grupper, 17 turer, 75 s; bedömd kvalitet —
`ej_bedomt`, kritikens och ägarens. Nätgränsen nekade 16 anrop per session: Chromes egen trafik till Google (update,
accounts, clients2, android.clients) och blockprovets `http://blockerad.example/` (två anrop); i den andra sessionen
visade modellens snapshot av den sidan bara proxyns text "blockerad". Mutationer i egna kopior, tolv, alla dödade (se
grenens slutrapport).

**Återstår:**
- DevTools-profilen startas för hand (`devtools.py`); prototyp.py tar den inte själv för huvudreferensen, och ingen
  verklig kundkörning har läst `SEKTIONER.md` eller en profil än. Hur skaparen använde resultatet redovisas i RIKTNING.md
  enligt prompten, men observeras inte maskinellt.
- `list_network_requests` ger inga storlekar; byte står som null. Lighthouse-rapportens underkända granskningar namnges
  inte i verktygets svar.
- Underhållet slår inte upp chrome-devtools-mcp: versionen byts för hand enligt `kunskap/beroenden.md`.
- Svepet mäts i en datorkontext som bara byter bredd: mediefrågor om pekare och hovring slår inte om.
- En hover- eller fokusväljare som bara finns i en bredd fäller fångsten i de andra; regeln står i referensjakt.md.


**Rättelse i Codex övertagande 2026-10-07:** de tidigare tio lokala fallen gick igenom, men fyra nya motfall visade
gröna kvitton för ogiltiga sessioner, länkade skrivmål, skiftande sektionsidentitet och skrivande HTTPS-anrop.
Rättelsen prövar hela konfigurationen och skrivmålen, slutstatus och schema samt slutförda verktygsuppgifter.
Sektionsidentiteten sätts före synlighetsfiltreringen; mobila sektioner får också följa med i kurateringen.
Ett lokalt Chromium-tillägg begränsar metoder även inuti HTTPS och blockerar WebSocket/WebTransport; proxyn ensam
gör inte detta. Sessionens tidsgräns avslutar även barnen. Dessa rättelser ändrar inte ägarens verktygsuppdrag.
De äldre uppgifterna om verkliga sessioner ovan är tidigare agentens redovisning, inte prov av den här rättelsen.
Codex kör inga verkliga Claude- eller MCP-sessioner under övertagandet. Den samlade konfigurationen och modellens
användning av resultatet lämnas uttryckligen till Claude. Se genomföranderapporten för slutligt lokalt provutfall.

Den separata Codex-granskningen fann även ett tomt spåranalyssvar som räknades som lyckat, utebliven barnstädning vid
SIGTERM och breddsvepets jämförelse av olika sektioner. Alla tre reproducerades före rättelse. Ett lokalt Chromium-prov
bekräftade dessutom att en extra isolerad kontext saknade tilläggets skydd. `devtools_transport.py` nekar därför
`isolatedContext` och verktyg utanför profilen före MCP-servern; konfigurationen kräver denna startväg.
Spåranalysen måste följa ett avslutat spår och får inte vara ett besked om saknad inspelning. SIGTERM/SIGINT städar
sessionens processer och proxy. Breddsvepet jämför stabila sektionsidentiteter, med separat besked om synlighet.
Kravet på ett verkligt samlat MCP-prov hos Claude kvarstår; lokal protokollattrapp bevisar inte det.
Avbrott under själva Popen-starten skjuts upp tills processobjektet är registrerat för städning; signalerna blockeras
inte hos barnet. Barriärprovet lägger SIGTERM efter verklig barnstart men före Popen-returen, både för sessionen och
transporten. Båda städas före slutkod 143.


## Tillägg 2026-10-07: DevTools utan klientvalda skrivmål

**Status:** gäller.

Den avslutande tekniska omgranskningen fann att fyra av de läsande verktygen också kan skriva till ett valt mål.
Stdio-vakten nekar därför `filePath` och `outputDirPath` före vidarebefordran. Normala verktygssvar och deras egna
temporära artefakter påverkas inte. Det riktiga transportprovet visar nekande för alla fyra vägar och oförändrade
tillåtna anrop. Provet använder en lokal attrapp; verklig nästlad MCP-åtkomst är fortfarande oprövad.
## Tillägg 2026-10-07: full verktygslåda, promptkedjan och automatiska kundrepon

**Status:** gäller.

Ägarens uppdrag kom ~14:05Z den 7 oktober som ett inklistrat block, mitt i arbetet med uppdraget om kompetensens
användning och tillförlitlig rapportering (tillägget ovan), medan grenarna r105, r106, r108 och r109 byggdes och main
stod på df4091b, som Codex granskat. Sparat ordagrant i minnet 14:18:50Z, här med kundspecifikt namnexempel utelämnat enligt överlämningens publiceringsgräns. Nulägeskontrollen delade
arbetet i grenar (E–O och H1–H6); varje gren hänvisar hit och skriver sitt eget avsnitt nedan.

```text
Genomför detta i nortropic-webb-pro: fullt införande av den förstärkta verktygslådan, sammanhängande promptar och överlämningar samt automatisk skapning av separata kundrepon.

Detta är ett implementationsuppdrag. Leverera fungerande integrationer i det ordinarie flödet, med dokumentation och verifiering. Stanna inte vid en plan, rekommendation, ny metodtext eller backlogposter.

Målet är att Nortropic ska kunna gå från kundunderlag till en visuellt genomarbetad, fungerande webbplats i ett eget kundrepo, med spårbar användning av vår kompetens och en fungerande leveransväg till Vercel.

Behåll principen ”full verktygslåda, ren arbetsbänk”: kompetensen ska användas konkret i rätt arbetsmoment, medan varje session får ett tydligt uppdrag och rätt aktuellt underlag.

1. Utgå från verkligt nuläge

Läs aktuell kod, dokumentation, ägarbeslut och pågående arbete innan du ändrar något. Codex granskade df4091b; kontrollera vilka fynd som fortfarande gäller.

Återanvänd sådant som redan fungerar. Undvik parallella register, rapportformat, observationssystem och orkestrerare för samma uppgift.

Arbeta isolerat från pågående kundkörningar. Bevara befintliga prototyper, domar, bilder, versionshashar och historiska rapporter.

Kontrollera aktuella officiella källor för de produkter och integrationer som införs. Lås prövade versioner per körning. Uppdatera inte verktyg eller metod mitt under en pågående körning.

2. Rätta promptkedjan och sessionernas överlämningar

Verifiera och rätta följande fynd:

- Svaret på skisskritiken startar en ny Claude-session, men prompten säger att kärnkompetensen redan lästs i föregående session.
- Kompetenstexten föreskriver högst ett rättningsvarv och en bekräftelse, skissen säger inget fast antal varv och fördjupningen kräver minst tre.
- Byggprompten säger både att börja med steg 1–7 och att ta vid efter ett redan godkänt val i steg 5.1.
- Planprövningen kan invända mot hypotes och huvudreferens utan en tydlig väg att få dessa omprövade och referensmaterialet uppdaterat.

En ny session ska uttryckligen behandlas som en ny session. Ge den en kort överlämning med:
- uppgiften och aktuell version;
- vad som är godkänt respektive fortfarande öppet;
- relevanta kundfakta och designunderlag;
- vilka kompetenser den ska ladda och tillämpa;
- senaste kritik och kvarstående frågor;
- hur resultatet ska verifieras.

Använd faktisk återupptagning endast när det är avsikten och när den gamla kontexten fortfarande är lämplig.

Ge varje arbetsmoment ett entydigt stoppvillkor. Behåll konfigurerbara tids-, användnings- och försöksgränser, men använd inte ett visst antal varv som kvalitetsbevis. Vid utebliven förbättring ska arbetet kunna återgå till hypotes, komposition eller materialval.

Granska de färdigsammansatta promptarna, inklusive infogade rolltexter och projektinstruktioner. Det räcker inte att varje mall ser rimlig ut för sig.

3. Skapa ett eget kundrepo automatiskt

Varje nytt kundprojekt ska automatiskt få:
- ett separat lokalt Git-repo;
- ett privat GitHub-repo i vår befintliga avsedda organisation eller vårt konto;
- en stabil koppling mellan projektidentitet, slug, lokal sökväg och fjärrrepo;
- ett eget kort CLAUDE.md;
- projektets kod, låsta beroenden och nödvändig projektkonfiguration.

Exempel på namn: kund-exempel.

Ett nytt kundprojekt betyder en ny självständig webbplats eller leverans. En ny kandidat, rättning, omstart eller byggkörning inom samma projekt ska återanvända samma repo, med isolerade arbetsgrenar eller worktrees där det behövs.

Skapandet ska vara återupptagbart och tåla upprepade eller samtidiga starter:
- inga dubbletter;
- inga överskrivna befintliga projekt;
- ingen koppling till fel kund vid namnkonflikt;
- tydligt tillstånd om lokal skapning lyckats men fjärrskapning misslyckats.

Använd befintlig autentisering och konfiguration. Härled inte ett GitHub-konto eller Vercel-team genom gissning. Om en nödvändig uppgift inte går att fastställa, fråga om just den och fortsätt övrigt oberoende arbete.

Nortropic ska förbli den gemensamma motorn. Kopiera inte hela motorn, dess historik och alla administrativa instruktioner till varje kundrepo. Bind i stället varje körning till den motor-, metod- och verktygsversion som användes.

Ett privat GitHub-repo innebär inte att allt kundunderlag får laddas upp. Definiera uttryckligen vilka filer som är levererbara. Råunderlag, hemligheter, interna transkript, privata bedömningar och referensmaterial som inte får distribueras ska ligga utanför den publicerade projektmängden.

4. Flytta kontext och skydd tillsammans med projektet

Starta kundens skaparsessioner med korrekt projektkontext. Kontrollera faktisk arbetskatalog, CLAUDE.md-laddning, skills och MCP-konfiguration i den nästlade sessionen.

Kundens CLAUDE.md ska vara kort och projektspecifik:
- projektets syfte och viktigaste besökaruppgift;
- teknik och verifierade kommandon;
- kodstruktur;
- aktuell designkälla och faktakälla;
- projektets begränsningar;
- hur arbetet provas och levereras.

Länka till större underlag i stället för att stoppa in hela historiken. En ny kund ska inte ärva en tidigare kunds färgval, smakdomar eller misslyckade designriktning.

Skilj instruktionerna för underhåll av Nortropic från instruktionerna för kundskapande och granskning.

Anpassa sandlåda, hooks, kundvakt, sökvägskontroller, processregistrering och tillåtelselistor till den nya repostrukturen. Gamla relativa sökvägsregler får inte antas fungera efter flytten.

Kundsessionen ska fortsatt vara avgränsad från andra kunder och från ändringar i motorn. Bevara skyddet mot symlänkar och felaktigt upplösta sökvägar.

Behåll prenumerationsbaserad Claude Code-körning. Inför inte ett API-baserat beroende som ändrar kostnadsmodellen utan mitt beslut.

5. Inför och koppla verktygslådan till riktiga arbetsuppgifter

Inventera först vad som redan är installerat, autentiserat, tillgängligt och fungerande i respektive nästlad session. Installation i huvudsessionen är inte bevis på åtkomst i skaparsessionen.

Inför följande förmågor i det ordinarie flödet:

A. 21st MCP
Använd aktuell officiell integration, inte en föråldrad Magic-konfiguration.
Koppla komponentinventering och komponentutförande till designarbetet.
Valda komponenter ska anpassas till projektets komposition, tokens, tillstånd och beroenden.
Skilj komponentåtkomst från AI-generering och dess eventuella krediter.
Bevara källa och licens för faktiskt använda komponenter.

B. Higgsfield och bild-/videoproduktion
Inför ett fungerande materialsteg för bilder och video.
Stöd Nano Banana för bildgenerering/redigering och Seedance för videoproduktion, utifrån aktuellt tillgängliga modeller.
Behandla Nano Banana → bild → Seedance som en möjlig kedja, inte som att Nano Banana självt är en videomodell.

Materialsteget ska få ett konkret visuellt uppdrag: användningsplats, uttryck, format, beskärning och vad materialet ska bidra med.
Leverera webboptimerade tillgångar med spårbar källa och vald version.
För video ingår lämplig stillbild, mobilanpassning och beteende vid reducerad rörelse.

Genererat material får inte framställas som dokumentation av kundens verkliga personal, arbeten eller resultat.
Tillåtna uppladdningar till medietjänster måste definieras separat från generiska Refero-/Mobbin-sökningar. Skicka inte privat material bara för att tjänsten tekniskt kan ta emot det.

C. Motion AI Kit och GSAP
Inför officiell Motion-kompetens och relevanta MCP-funktioner.
Inför GSAP och dess officiella skills som en prövad möjlighet i verktygslådan och beroendehanteringen.
Använd ett medvetet val mellan CSS, Motion och GSAP för respektive beteende.
Valet ska följa designen och implementationens behov. Animationer ska inte läggas till för att fylla en användningskvot.

D. Canvas-design
Gör skillen tillgänglig för grafiska koncept, illustrationer och statiska kompositionsstudier.
Koppla dess resultat till det faktiska material- och designarbetet.
Beskriv inte en PNG/PDF som en fungerande responsiv prototyp.

E. Apple-design och befintlig designkompetens
Använd den befintliga Apple-inspirerade kompetensen tillsammans med relevanta officiella HIG-principer i interaktionsgranskningen.
Bedöm återkoppling, fokus, avbrytbar rörelse, begriplighet, textstorlek och tillgänglighet.
Detta är inte ett krav att alla kunder ska få Apples visuella stil.

F. MotionSites och promptbaserade referenspaket
Bekräfta vilken tjänst som avses innan en produktspecifik integration görs. MotionSites är inte samma produkt som Motion.dev.
Inför stöd för att använda ett tillåtet paket med förhandsvisning, prompt och tillgångar som sammanhängande designunderlag.
Bevara kopplingen mellan det synliga målet, instruktionen och rätt materialversion.
Lita inte på leverantörens ”pixel-perfect”-påstående utan att jämföra faktisk rendering.
Använd tillgängligt/licensierat material; köp inte åtkomst utan mitt beslut.

G. Refero och Mobbin
Behåll och verifiera båda genom hela kedjan.
Materialet ska kunna användas och kompletteras i de steg som tilldelats tjänsterna.
Tomma resultat, nekad åtkomst och saknade bilder ska synas tydligt och hanteras, inte räknas som genomfört referensarbete.

För alla tjänster: återanvänd befintliga konton där det går. Redovisa saknad autentisering eller åtkomst separat. Gör inga nya köp eller obegränsade kostnadsåtaganden utan mitt beslut.

6. Säkerställ faktisk användning av kompetensen

All kärnkompetens som metodkartan tilldelar ett steg ska laddas och användas i det steget. Den får inte reduceras till en frivillig lista som modellen kan ignorera.

Använd uttrycklig skillaktivering eller förladdning där det stöds. För referensfiler som inte är fristående skills ska korrekt fullständig läsning användas och redovisas som just läsning.

Kontrollera att externa resurser och referensfiler som skillen behöver faktiskt är tillgängliga.

Följ kedjan:
kompetens → uppgift → beslut → implementation/material → verifierat resultat.

Skilj på:
- tillgänglig;
- laddad eller läst;
- verktyg anropat;
- användbart resultat mottaget;
- resultat använt;
- effekten granskad.

Ett lyckat anrop eller läskvitto är inget kvalitetsbevis.
En utebliven observation är inte heller automatiskt bevis på att arbetet inte gjorts.

Alla relevanta kompetensområden ska få en tydlig uppgift. Kräv inte meningslösa anrop till varje endpoint eller betald generation i varje projekt för att få en grön ruta.

7. Fördjupa referensinspektionen

Utöka befintlig extraktion och webbtjänst. Bygg inte en separat konkurrerande inspektionskedja.

För utvalda sektioner och tillstånd ska underlaget kunna innehålla:
- skärmbilder vid samma bredder som prototypen;
- relevant DOM och semantisk struktur;
- beräknade stilar och matchande CSS-regler;
- faktiskt renderade typsnitt;
- proportioner, radbrytningar och bildbeskärning;
- responsiva omställningar;
- meny, hover, fokus och tangentbordsbeteende;
- rörelsesekvens eller trace när rörelsen bär designen.

Pröva Chrome DevTools MCP och Playwrights befintliga möjligheter. Integrera dem inom nuvarande datagräns och webbläsaravgränsning.

Ge skaparen relevant, undersökningsbart underlag. Stoppa inte in hela sajtens minifierade JavaScript och CSS i varje prompt.
Externt sidinnehåll ska behandlas som underlag, inte som instruktioner till agenten.

Inspektionen ska leda till en användbar förståelse av varför referensen fungerar och hur dessa kvaliteter kan bevaras med kundens innehåll.

8. Gör designunderlaget konkret och sammanhängande

Återanvänd UPPDRAG.md, RIKTNING.md och DESIGN.md.

De ska tillsammans klargöra:
- besökarens uppgift och kundens erbjudande;
- komposition och visuell hierarki;
- bildstrategi och namngivna tillgångar;
- typografi och färgernas roller;
- responsiva principer;
- komponenttillstånd och rörelse;
- öppna hypoteser;
- vad ägaren faktiskt har godkänt;
- vad nästa granskning ska jämföra.

Tidiga planer får inte låsa svaga designbeslut. Skaparen ska kunna ändra grundkompositionen när renderingen visar att den inte håller.

Granskningen börjar med resultatet före skaparens förklaring.
När helheten är svag ska rättningen kunna ändra helheten.
Undvik långa serier av marginaljusteringar kring en misslyckad grundidé.

Bevara befintliga ägarval och urvalsflöden. Ett tekniskt grönt resultat ersätter inte min designbedömning.

9. Stabilisera orkestrering, context management och code review

Behåll en tydlig yttre kedja med versionsbundna övergångar och kreativa arbetssteg innanför den.

Varje steg ska ha:
- identifierad input;
- aktuell uppgift och behörighet;
- förväntad leverabel;
- verifiering;
- definierad hantering av fel, avbrott och återförsök.

Återanvänd befintlig mekanik för identiteter, lås, utfall och godkännanden.
Godkännanden ska gälla rätt körning, projektversion och metod.

Utvärdera Claude Codes aktuella Dynamic Workflows för avgränsade delar där de ersätter egen specialkod eller förbättrar parallellt arbete. Kontrollera faktisk CLI-version, aktivering, behörigheter och observation av underagenter.
Anta inte att ett nyckelord i en -p-prompt aktiverar funktionen.

Inför inte samtidigt LangGraph, Spec Kit och ytterligare en egen orkestrerare.
Använd spec-driven-principer i vår befintliga kedja: begripligt uppdrag, plan, implementation och granskning mot samma underlag.
Om ett separat ramverk behövs ska det ersätta ansvar som annars skulle dubbleras.

Planera före nya riktningar, större funktioner och osäkra ändringar. Undvik en ny tung planeringsfas före varje liten visuell rättning.

Code review ska pröva diffen mot aktuell specifikation, korrekthet och tydliga krav.
Visuell granskning ska separat bedöma komposition, utförande och interaktion.
Ingen granskare ska behöva hitta ett visst antal fel.

10. Koppla kundrepo till Vercel

Koppla automatiskt det nya kundrepot till rätt Vercel-team och projekt, med verifierad byggkonfiguration och preview-flöde.

Nya körningar ska återanvända projektet.
Preview ska kunna knytas till rätt commit och visas i Nortropics dashboard.
Bevara befintliga beslut och gränser för produktionspublicering.

Astro och Vercel är inte konkurrerande alternativ.
Behåll lämplig stack per projekt och gör React-komponenter, Motion och GSAP möjliga där projektet använder dem.
Överge inte en fungerande stack bara för att ett nytt verktyg demonstrerar en annan.

11. Uppdatera dashboard och dokumentation som del av leveransen

Dashboarden ska visa:
- kundprojektets repo och aktuell arbetsversion;
- GitHub- och preview-länkar;
- aktuellt steg och ansvarig session;
- vilka kompetenser och verktyg som används;
- vilket material och vilka referenser arbetet bygger på;
- observerat arbete separat från agentens egen redovisning;
- aktuell granskning, ägarbeslut och kvarstående hinder.

Återanvänd befintlig observation och dokumentationsstruktur.
Gör aktuell status härledd ur körningens verkliga data där det går.
Undvik manuella sammanfattningar som kan fortsätta visa ett gammalt godkännande.

Uppdatera metodkarta, flödesvy, projektinstruktioner och relevanta guider tillsammans med implementationen.
Markera ersatta instruktioner så att de inte fortsätter laddas som gällande.
Bevara historiska rapporter som historik.

12. Verifiera hela införandet

Gör ändringarna stegvis och genomför relevanta regressions- och integrationsprov.

Verifiera särskilt:
- en ny kund får rätt lokalt och privat fjärrrepo;
- en upprepad start återanvänder samma repo;
- samtidiga starter inte skapar dubbletter;
- två kundprojekt är avgränsade från varandra;
- nya sessioner får korrekt överlämning;
- obligatorisk kompetens finns i den session som ska använda den;
- nya MCP-integrationer fungerar genom den riktiga ingången;
- privat material inte följer med i commit, push eller otillåtna tjänsteanrop;
- avbrott och återupptagning bevarar rätt tillstånd;
- dashboard, rapport och godkännande pekar på samma version;
- preview fungerar från kundrepot.

Stubbar får verifiera mekanik, men får inte redovisas som bevis på fungerande extern åtkomst eller verklig designkvalitet.

Genomför därefter ett avgränsat verkligt kundexempel genom kedjan, med befintliga kostnadsgränser och nödvändiga ägarsteg.
Visa att en sammanhängande design, mobilanpassning och viktig interaktionsväg överlever hela vägen till kundrepo och preview.

Migrera äldre projekt kontrollerat när den nya vägen är verifierad. Radera inte ursprung eller historiska bevis som del av införandet.

Leverera en samlad slutrapport i vår ordinarie dokumentationsstruktur:
- infört och verifierat;
- befintligt som återanvändes;
- exakt vad som ändrats;
- verkliga prov och deras resultat;
- eventuella kvarstående åtkomst- eller ägarhinder;
- länkar till kundrepo, preview, designunderlag och aktuellt slutkvitto.

Kalla inte införandet färdigt om verktygen bara är installerade eller dokumentationen uppdaterad. Det ska fungera i den faktiska kundkedjan.

Börja med nulägeskontrollen och genomför arbetet. Be bara om sådant som faktiskt saknas och inte går att fastställa ur befintlig konfiguration eller tidigare beslut.
```

### Ägarens förtydligande 2026-10-07 (~15:20Z)

Mottaget via samordnaren medan gren H5 byggdes; gäller varje gren från och med då. Ordagrant:

> Varje arbetssteg ska uttryckligen aktivera sina tilldelade skills genom skillsystemet där det stöds. Referensfiler som saknar egen aktivering ska läsas enligt skillens instruktioner. Saknad aktivering eller misslyckad laddning ska synas och hanteras innan beroende arbete fortsätter. Varje tilldelad verktygs-/MCP-uppgift ska genomföras genom ett faktiskt anrop och ge ett kontrollerat resultat. Att verktyget finns installerat räcker inte. Dokumentera därefter hur resultatet användes. Verifiera detta i den riktiga skaparsessionen. Skilj aktivering, lyckad användning och bedömd kvalitet åt.

### Gren H5: canvas-design och Apple-design med HIG-principerna (punkt 5D och 5E)

Grenen `canvas-hig-20261007` ovanpå 2b4045e, byggd i worktreen r111 medan r105, r106, r108, r109, r110 och r112 arbetade
med andra grenar. Inget ur `underlag/` eller `kunder/`, inga MCP-anrop, inga köp.

1. **canvas-design är intagen** (punkt 5D): `.claude/skills/canvas-design/` ur anthropics/skills @ 683bc88e, Apache-2.0
   ur upstreams `LICENSE.txt`, 77 filer kontrollerade byte för byte mot upstreams blobbar: SKILL.md, LICENSE.txt och
   48 typsnittsfiler med 27 OFL-filer. Sex typsnittsfiler utelämnade (IBM Plex Serif, Instrument Serif) eftersom
   deras OFL-fil saknas i upstream; `KALLA.md` säger varför och när de kan tas in. Förgranskningen gav LÅG. Rollen
   komposition har skillen som alternativ, och metodkartans stycke Grafiska koncept ur canvas-design ger uppgiften:
   grafiska koncept, illustrationer och statiska kompositionsstudier som material- och designunderlag. En PNG eller
   PDF ur skillen är ett koncept, aldrig en fungerande responsiv prototyp: kandidaten är den byggda sidan i 390, 768,
   1280 och 1440. Resultatet registreras i `bilder/BILDER.md` med källa (`canvas-design @ <commit>`) och version och
   får `Egen: nej`; `atelje.egna_bilder` tar aldrig med en rad som nämner koncept eller canvas-design bland
   verksamhetens egna bilder. Formen står i metodkartans stycke Grafiska koncept ur canvas-design, och
   `kunskap/bild.md` bär regeln och hänvisar dit: bild.md ingår i skaparens kärna, som rökprovet håller under 160 000
   tecken (baslinjen låg 362 tecken under taket; en första version med formen i bild.md bröt det). Materialsteget (gren H4) har uppdraget
   att ta koncepten som ingång till ett konkret visuellt uppdrag. Beroenden: skillen namnger inga bibliotek; Pillow och
   reportlab saknas i `.venv` och låses inte här (intag enligt `kunskap/beroenden.md`); utan nya paket går SVG/HTML
   renderad till PNG med Playwrights Chromium. Kirurgens register: ursprungsnoten "utelämnad för att licensfil saknas"
   och posten 2026-10-02 står kvar med utfallet 2026-10-07.
2. **HIG-principerna i interaktionsgranskningen** (punkt 5E): `kunskap/hig-principer.md` (under 10 000 tecken) med
   principerna för rörelse, fokus och val, återkoppling, begriplighet, typografi och textstorlek samt tillgänglighet i
   våra ord, en källa per princip (developer.apple.com/design/human-interface-guidelines/motion, focus-and-selection,
   feedback, typography och accessibility, lästa 2026-10-07 ur Apples sidor), ingen kopierad Apple-text. Filen är
   kärna i rollerna granskning och kritik, vars uppgift nu är att bedöma återkoppling, fokus, avbrytbar rörelse,
   begriplighet, textstorlek och tillgänglighet mot principerna; emil-apple-design är alternativ i granskningen. Det
   är inget krav på Apples visuella stil: principerna gäller hur sidan beter sig och läses, huvudreferensen bär
   fortsatt utseendet, och kvalitetskraven förblir kraven medan principerna är frågor. Källan är låst med
   `metod.py --las` (92 källor, förut 90). Kritikens kärna växte från 58 850 till 68 083 tecken (mätningen 107–109 s
   gällde den mindre kärnan; fristen 480 s har marginal); granskningens från 89 286 till 98 519.
3. **Ägarens förtydligande ~15:20Z** är infört där grenens block når sessionerna: `kompetens.prompt_rader` säger till
   varje pass att en skill aktiveras med Skill-verktyget (dess SKILL.md), att en referensfil som inte är en skill
   läses hel med Read som skillen anger, att en aktivering eller läsning som nekas eller misslyckas skrivs i svaret
   innan beroende arbete fortsätter, och att kvittot visar aktiveringen och läsningen, aldrig tillämpningen.
   Metodkartans stycke Aktivering, användning och bedömning säger vad kvittot skiljer (aktivering och läsning,
   användning med utfall, bedömd kvalitet som kvittot aldrig ser) och hur en saknad laddning hanteras i dag (omförsök
   i passen rörelse och granskning, `genomford` i skissen, kvittot i SKISSKRITIK.json). En lucka rättades:
   `bildkedja.metodlasning` räknade ett Skill-anrop som gav fel (okänd skill) som en aktivering och dess SKILL.md som
   läst; nu räknas, som för Read, bara anrop utan fel. Skissprompten i `kandidater.py` (rad "0. Använd hela
   kompetensen") säger fortfarande "eller ladda skillen" och rörs inte här (gren E; r106 och r108 ändrar filen).
4. **Prövat i verklig nästlad session** (flödets argument, utan kund, haiku): init-beskedet listade canvas-design och
   emil-apple-design bland 73 skills; en session aktiverade canvas-design med Skill-verktyget (8 turer, 29 s); en
   andra session (6 turer, 17 s) gav kvittot: `skill_anrop` canvas-design och alternativet valt för rollen
   komposition, `kunskap/hig-principer.md` läst hel för granskning och kritik, en delvis läst fil inte vald,
   `tillampning` inte observerat, och den misslyckade aktiveringen av en skill som inte finns borta ur kvittot efter
   rättelsen. Samma session läste skillens injicerade instruktioner ("Output only .md … .pdf … .png") som ett nytt
   uppdrag och stannade: kvittot visade aktiveringen ändå, vilket är varför aktivering, användning och kvalitet hålls
   isär, och metodkartan säger nu att skillens arbetsgång gäller konceptet, inte sessionen.
5. **Proven:** `kontroller/rokprov/revision/prov_canvas_hig.py`, sju fall i rökprovet (skillen med licenser, uppgiften
   i komposition med skaparens kärna under 160 000 tecken, hig-principer.md låst och i rollerna, ett koncept aldrig en
   prototyp, `egna_bilder`, formen i kartan med bild.md:s hänvisning, kvittot på en sessions radformat). Alla sju röda
   mot 2b4045e, gröna här. Mutationer i egna kopior, en i
   taget: licensfilen, en OFL-fil, blockraden i komposition, kärnraden i kritik, en ändrad källa utan lås, ett
   uppgiftsord, negationen vid prototyp, `egna_bilder`, låsets hash, KALLA.md:s licensrad, meningen om Apples stil,
   bild.md:s Egen-rad, emil-apple-design i granskningens välj, bildkedjans Skill-filter och prompttexten; var och en
   fälldes av sitt fall sedan två luckor i provet rättats (negationen prövades över hela meningen, prompttexten
   prövades inte alls). `metod.py --prova` och `kompetens.py --prova` är gröna.

**Återstår:**
- Ingen verklig skissomgång med kundmaterial har gått med blocken; proven gäller flödets argument, syntetiska loggar och
  en haiku-session utan kund. Att skaparen tillämpar HIG-frågorna och canvas-design i en riktig körning är inte
  observerat.
- Materialsteget (gren H4) bygger körvägen från koncept till tillgång; tills dess är en PNG eller PDF ur skillen
  något som tas fram utanför flödets sessioner (Pillow och reportlab saknas), och skaparen skriver en
  kompositionsstudie som SVG i det egna projektet.
- En misslyckad aktivering av ett alternativ stoppar inget automatiskt: sessionen skriver felet och väljer något annat;
  bara kärnan ger omförsök (passen rörelse och granskning) eller `genomford` falskt (skissen). Ett stopp för alternativ
  kräver en regel i kandidater.py (gren E eller I).
- De sex typsnittsfilerna utan OFL-fil tas in när licensfilen finns i upstream eller hämtas från typsnittets källa.
- Krockarna i canvas-designs KALLA.md har inga K-nummer i `kunskap/skillkrockar.md`.
- Skaparens kärna ligger 29 tecken under taket 160 000 (prov_revision, kompetenskedjan och granskning 3; 362 före
  grenen). Nästa tillägg i `bild.md`, `copy-kontroll.md` eller `redaktionellt-pass.md` kräver att något kortas, eller
  att taket omprövas med en mätning av lästiden; taket höjs inte utan den (inventeringens fynd e om läsvolymen).

## Tillägg 2026-10-07: H5:s webbanpassning, läskvitto och konceptgräns

**Status:** gäller.

Codex samlade rättelse efter källkontroll och separat granskning. Inga nya ägarbeslut eller universella
storleksregler införs. HIG-principerna skiljer webb från native: disclosure från modal dialog, textförstoring från
reflow, WCAG:s rörelsevillkor och stor text från egna designkrav. Axe och stillbilder bevisar inte full
WCAG-täckning eller fungerande interaktion; mänsklig bedömning och funktionella prov redovisas separat.

Metodkvittot kräver ett matchat lyckat Read-/Skill-svar och använder dess tidpunkt. Obesvarade anrop räknas inte
som lästa och sena svar räknas inte före en redan gjord kodändring. Äldre syntetiska positiva provloggar har fått
explicita svar; produktionskravet försvagas inte. Koncept, filosofitext och studier registreras i kandidatens
koncept/BILDER.md, aldrig bland gemensamma kundbilder; den befintliga blindgränsen gäller därmed också dessa filer.

Regressionsfallen prövar de felaktiga HIG-formuleringarna, obesvarade och sena Skill-/Read-svar, positiv svarsföljd
och den dokumenterade konceptvägen genom blindkritikens verkliga nekanden. Detta visar lokal mekanik och
instruktionernas avgränsning. Verklig skaparsession, extern åtkomst och förbättrad designkvalitet lämnas oprövade
under övertagandets sessionsförbud. Slutliga provbevis redovisas i överlämningens rapportförteckning.
## Tillägg 2026-10-07: Motion AI Kit och GSAP (gren H2)

**Status:** gäller.

Ägarens uppdrag 2026-10-07 om full verktygslåda och kundrepon (ordagrant i gren H5:s post), punkt 5C: "Inför officiell
Motion-kompetens och relevanta MCP-funktioner. Inför GSAP och dess officiella skills som en prövad möjlighet i
verktygslådan och beroendehanteringen. Använd ett medvetet val mellan CSS, Motion och GSAP för respektive beteende.
Valet ska följa designen och implementationens behov. Animationer ska inte läggas till för att fylla en
användningskvot." Ägarens beslut om Motion+: "Nej, bara den fria delen." Ägarens tillägg: "Du glömde Framer Motion
mcp/skill också" — Framer Motion är det äldre namnet på Motion, `motion/react` är gamla framer-motion och npm-paketet
`framer-motion` ett alias, så skillen `motion` är också Framer Motion-skillen (`kunskap/beroenden.md`, metodkartan).

Ägarens förtydligande samma dag (via samordnaren), ordagrant: "Varje arbetssteg ska uttryckligen aktivera sina
tilldelade skills genom skillsystemet där det stöds. Referensfiler som saknar egen aktivering ska läsas enligt skillens
instruktioner. Saknad aktivering eller misslyckad laddning ska synas och hanteras innan beroende arbete fortsätter.
Varje tilldelad verktygs-/MCP-uppgift ska genomföras genom ett faktiskt anrop och ge ett kontrollerat resultat. Att
verktyget finns installerat räcker inte. Dokumentera därefter hur resultatet användes. Verifiera detta i den riktiga
skaparsessionen. Skilj aktivering, lyckad användning och bedömd kvalitet åt."

Genomfört på grenen `motion-gsap-20261007`:

1. **Motion AI Kit, fria delen.** Skillen i `.claude/skills/motion/` (MIT enligt paketets deklaration; ingen
   LICENSE-fil finns hos källan, KALLA.md säger det), MCP:n `https://mcp.motion.dev` i `kontroller/mcp/motion.json`,
   given till ateljéns sessioner på samma väg som Mobbin (`atelje.session_args`), och kundvakten släpper dess enda
   verktyg `search-motion-docs` med Referos och Mobbins regel (`kundvakt.MATCH`, `kundvakt.tillatna` ur
   `kompetens.MCP`). Ingen Motion+-server, inget konto. Prövat i en verklig nästlad session utan kunddata.
2. **GSAP som låst, prövat beroende.** gsap 3.15.0 i `mall/astro` och `mall/leverans` (Standard "No Charge" GSAP
   License, fri sedan 2025-04-30), granskat enligt `kunskap/beroenden.md` och provbyggt i rökprovets sida `/rorelse/`,
   som står stilla vid `prefers-reduced-motion` (gsap.matchMedia) och bygger utan konsolfel. gsap-skills (MIT) i
   `.claude/skills/gsap/`. Kirurgens post 2026-10-03 står kvar som historik med en rad om ersättningen.
3. **Valet per beteende.** Rollen rorelse väljer CSS, Motion eller GSAP (eller stilla) per beteende med skäl i passets
   `teknikval` (kandidater.PASS_SCHEMA) och RIKTNING.md; kompetenskvittot visar valet som sessionens redovisning,
   inte som observation, och skiljer aktivering, lyckad användning och bedömd kvalitet åt (`kompetens.nivaer`).
   Passen redovisar också aktiveringen av sina skills, och prompten säger vad som aktiveras med skillverktyget och vad
   som läses med Read.
4. **Metodlåset** skrivet om efter de nya källorna; `metod.py --prova` och `kompetens.py --prova` gröna.

**Återstår:**
- Helbygget (`kor.sh`) laddar ingen MCP utan `NWP_MCP_CONFIG`, och dess kända lista har inte motion.json (filen hör
  till gren r105); passet rorelse i ateljén har den.
- Ingen verklig designkörning har gått med rollen rorelses nya val; provet gäller en syntetisk kund och en verklig
  session utan kunddata.
- Motion AI Kits licens är deklarerad (MIT) men saknar licensfil hos källan; ägaren avgör om det räcker.
- `generate-css-easing`, som skillen nämner, fanns inte på servern 2026-10-07 (beslut "ingen uppgift" i metodkartan
  tills det prövats).


## Tillägg 2026-10-07: H2:s verifieringsrättelse

**Status:** gäller.

Ingen ny teknik- eller designregel. Den separata förgranskningens B1–B4 rättas i den befintliga H2-vägen:

- Sessionsavtrycket binder alla MCP-konfigurationer, också fil två, upprepade flaggor, inline JSON och saknade filer.
- Kompetenspasset sparar observerade verktygs-/MCP-utfall och misslyckade skillanrop. Ett okänt utfall förblir okänt,
  även när andra verktyg i samma roll har lyckats. Aktiveringskravet gäller kärnans aktiverbara skills och de valda
  alternativen; rena referensfiler och ej valda alternativ är inte saknade Skill-anrop. Read och Skill hålls isär.
- Ett pass som redovisar Motion kräver observerat svar med innehåll från search-motion-docs. Ett saknat resultat
  ger ett avgränsat omförsök och därefter uppgiftsbrist, inte genomfört. CSS, GSAP och stilla kräver inget Motion-anrop.
- H5:s rättelse av obesvarade anrop och svarstid återanvänds; H2 bevarar dessutom skill_fel. Vid integration ska båda
  grenarnas ändringar bevaras. Ett laddningskvitto är fortfarande inte bevis för tillämpning eller designkvalitet.
- GSAP-provet mäter start, mellanläge, slutposition, reducerad rörelse och preferensbyte under en pågående rörelse,
  samt synligt innehåll utan JavaScript. Det använder den låsta biblioteksversionen och Playwright Clock.

Källorna för rörelseprovet lästa 2026-10-07: https://playwright.dev/docs/clock och
https://gsap.com/docs/v3/GSAP/gsap.matchMedia()/. Standardlicensen på https://gsap.com/standard-license/ verifierad
mot den tidigare beskrivningen. Provet gäller lokal mekanik; ingen ny riktig modell- eller MCP-session körs av Codex.
Resultat och kvarstående integration redovisas i RAPPORT-2026-10-07-r112-codex; inget pushas eller slås ihop här.


## Tillägg 2026-10-08: avgränsat metodförsök i skisskaparen

**Status:** gäller på försöksgrenen; sammanslagning och verklig körning återstår.

Genomförande av ägarens etapp 5: A/B-verktyget kan förbereda medium/high i det namngivna skisskaparpasset,
med samma ännu inte arbetade plan och separata kandidater. Bara skaparen och dess svar får försöksvärdet.
Gemensamma källor, kriterier och budget versionsbinds, tidigare material bevaras och den befintliga Prototypvyn
håller armarnas förklaring dold före ägarens val. Misslyckade försök och kända saknade svar räknas.

Detta ändrar varken standardmodell, effort, antal kandidater, granskningsnivå eller budget. Förberedelse ger
inte mandat att starta en modell eller ett betalt prov. Effektiv modellkonfiguration och designkvalitet är
oprövade när endast tekniska attrapper finns. Körmandat, privat underlag och senare ägardom lämnas uttryckligen
till nästa ordinarie session. README och kunskap/autonomi.md beskriver gränserna och återställningsvägen.


## Tillägg 2026-10-08: metodens villkor och semantiska resor

**Status:** gäller på arbetsgrenen; ingen ändrad skisskvot eller driftaktivering.

Genomförande av ägarens käll- och professionsuppdrag P4/P5 och G09. Den befintliga K46-regeln om väntande
skillflöden förs in i verkliga sessionsargument och inställningar: deras kunskap läses med Read, medan
Initial Response-anrop via Skill nekas. Uppdragets befintliga läge avgör varvkraven; ingen ny kvot införs.
CSS-animation är inte generellt fri från arbete på huvudtråden; den levererade metoden beskriver villkoret
och skiljer estetiska startvärden från normer. Uppströms skillfiler ändras inte.

Resformatets semantiska tillägg väljer kontroller genom roll och exakt namn eller etikett. Flera träffar
kräver ett entydigt område; CSS behåller det äldre beteendet. Provet prövas lokalt före bred användning och
är inget nytt obligatoriskt format för alla byggen. Lästa instruktioner, lokal åtkomst och passerade prov
får inte beskrivas som empirisk användbarhet, verklig modellåtkomst eller visad designförbättring.

Dokumentationens researchväg följer nu förberedelsens RESEARCH.md och mottagna kundsvar, inte det arkiverade repots intervju-kommandon. Omdömen är sekundärdata, aldrig ersättning för slutkundsintervjuer. Historiska urval och upptäcktsandelar är villkorade metodexempel, inga garantier för modellernas täckning. Detta inför inga nya obligatoriska intervjuer eller varv.

## Tillägg 2026-10-08: samstämmig läsning och aktivering i integrationen

**Status:** gäller genomförandet av befintliga K46-villkoret på integrationsgrenen, inte ett nytt ägarbeslut.

Samma klassificering av väntande Initial Response-skills styr sessionsnekandet, rollens instruktioner och
kompetenskvittot. Read får inte redovisas som saknad Skill-aktivering när den aktiveringen uttryckligen nekas.
Valda, aktiverbara Motion- och GSAP-skills behåller sina observerade lyckade eller misslyckade anrop. Kvitton
över läsning och aktivering intygar fortfarande varken tillämpning eller visuell kvalitet.


## Tillägg 2026-10-08: Kirurgens införandeobservation och versionsbundna uppföljning
**Status:** gäller implementationen på grenen kirurg-uppfoljning-codex-20261008, ingen aktivering eller nytt ägarmandat.

Genomförande av ägarens krav att förberedd patch, införd ändring och observerad eftereffekt ska skiljas åt.
Ordinarie separat kodgranskning och Git-väg består. Ett särskilt, av operatören tillhandahållet mandat och
versionsbundet granskningskvitto krävs för att registrera införandet. Observatören läser exakt Git-version och
berörda arbetsfiler; den kan inte skriva kod, mandat, granskningskvitton eller publicera. Uppföljning är märkt
inrapporterad observation med version, omfattning och belägg. En manuell återställning verifieras utan att
observatören ändrar arbetsfiler. Ingen positiv design-, drift- eller kundeffekt följer automatiskt av registreringen.

Lokala Git-/process-/HTTP-/webbläsarprov är syntetiska. Inga riktiga modeller, kunduppgifter, externa anrop,
införandemandat eller återkommande jobb skapas. Körformer och tillitsgränser: `kunskap/kirurg-forbattring.md`.

## Tillägg 2026-10-08: aktuellt ägarbesked genom hela flödet
**Status:** gäller integrationsrättelsen enligt befintligt krav på giltiga besked; inget nytt ägarbeslut.

Ett ja i domloggen är inte ett aktuellt godkännande när dess underlag eller version inte längre gäller.
Ateljéns läsande sammanfattning använder samma giltighetskontroll som helbyggstarten. Helbyggets och exportens
aktuella sammanfattning visar också ägardomen som historik när slutpostens beroenden ändrats. Okänd dom
förblir okänd. Den historiska domloggen och slutposten skrivs inte om av en statusläsning.

Riktiga lokala ingångar prövas med syntetisk Kundstart-databas, versionsbyte, ändrad eller saknad vinnare,
dashboardens besked och exportens aktualitetsvy. Proven är inte riktiga ägargodkännanden eller designbedömningar.

## Tillägg 2026-10-07: kundvaktens adresser, rubriker och orter

**Status:** gäller.

Omgranskningen GR-20261007-r104 (privat, `underlag/granskningar/`) fann två BÖR och två KAN i kundvakten. Adresser i
fritexten skyddades inte, och namn utan kännetecken i rubriker och först i en mening släpptes. Grenen
`kundvakt-adress-20261007` rättar r104#B1, B2, K1 och K2. Ägarens regler gäller som förut, ordagrant: "Refero och
Mobbin ska fortsatt få generiska researchfrågor utan kunduppgifter." och "Skicka inte kundmaterial till externa
loggtjänster, publika ärenden eller webbsökningar." Vad som prövas i detalj står i beskrivningen i
`kontroller/kundvakt.py`.

1. **Adresser (B1).** `skapande.forbjudna_termer` läser fritexten `not` och kontaktvägarnas belägg: gatan (känns igen
   på gatuledet, med eller utan husnummer), postnumret, orten efter postnumret eller gatan, orter i en mening med en
   adress, namnet efter c/o och långa nummer. Kundvakten läser samma uppgifter ur briefen, sidans text och RESEARCH.md.
2. **Namn och orter (B2).** "Möt", "Träffa" och "Enligt" är personord, och "Om" först i en rubrik. Säkra namn är också
   en rubrik som bara är ett par med stor bokstav, ett par under en rubrik om personer (Om oss, Team, Omdömen, Kontakt),
   ett par före ett personverb och genitiv efter en initial ("Ö:s"). En roll räknas också efter en tabellkant eller
   inom parentes. Ett par först i en mening stoppas som helt par. Orter stoppas efter fler platsverb och, utanför §7,
   efter varje platspreposition.
3. **Falsklarm (K1).** Engelska termer och rubriker ("Dark Mode", "Opening Hours", "Kitchen Renovation") delar paren,
   och ett typsnitt ur Google Fonts (listan i skillen ui-ux-pro-max) är varken ett namn eller en ort, också utanför §7.
4. **Där precisionen och täckningen krockar** går felet åt det säkra hållet:
   - en förlaga som briefen nämner utanför §7 stoppas som helt par, eftersom den inte går att skilja från ett firmanamn
     eller en person;
   - en rubrik som bara är ett par stoppas ord för ord, eftersom en sådan rubrik på en teamsida oftast är ett namn;
   - en ort som också är ett vanligt ord ("Mark", "Vara") stoppas, också i en generisk fråga som "check mark list";
   - ett säkert namn stoppas ord för ord också när ordet är vanligt ("White"), och ett efternamn som också är ett
     typsnitt ("Garamond") stoppas;
   - texternas långa nummer, också datum, prövas mot frågans siffror.

   Två regler går åt andra hållet. I provet mot verkliga data gav de två strängar som också står med liten bokstav i
   kundens texter, alltså vanliga ord: ett personverb räknas bara efter två ord ("Sidan svarar" är ingen person), och
   ett ensamt ord under en rubrik om personer räknas inte ("### Parkering" under Kontakt).
5. **Proven.** prov_startkvitto.py har fyra nya fall med fixturer i verkliga datas form, giltiga mot schemat: 10d (B1),
   10e (B2), 10f (K1) och 10g (K2). Alla fyra var röda mot a165e9c och är gröna här; 10g var röd genom genitiven efter
   en initial. 31 mutationer i egna kopior, minst en per rättelse och granskarens C17–C21, fälls alla: adresserna av
   10d, namnen och orterna av 10e, falsklarmen av 10f (en också av 10a) och C17–C21 av 10g. C19, som granskningen
   kallade likvärdig, var det inte: ett namn i fetstil efter ett personord tappade personordet.
6. **Mot verkliga data**, prövat i sandbox-exec utan nät och skrivningar (nekandet prövat med touch, curl och Python):
   - fritexten `not`: båda gatunamnen och båda postnumren hör nu till de förbjudna termerna (förut inget gatunamn och
     ett postnummer), och frågor med gatunamnen stoppas. Av granskarens fyra ord med stor bokstav stoppas tre. Det
     fjärde står först i en sats och har bestämd form, som ett vanligt ord;
   - briefens tre gatunamn och researchens två gatunamn och tre postnummer stoppas (förut inget gatunamn och ett
     postnummer);
   - personsträngarna är 15 som förut, och orterna är 4 (förut 0). Alla fyra står bara med stor bokstav i texterna;
   - de 41 generiska frågorna släpps. De verkliga tjänsteanropen får samma beslut som förut: 92 i kundens loggar, 93 i
     huvudutcheckningens transkript och 165 i alla repots transkript. Inget av dem nämner en av de nya strängarna;
   - kundvakten tar 66 ms per anrop i median (förut 31 ms) och högst 113 ms, mot fristen 20 s.
7. **Återstår:**
   - Ett hopskrivet namn under sex bokstäver släpps (HOPGRANS), liksom efternamnet ensamt efter ett par först i en
     mening utan kännetecken. Ett ensamt ord först i en sats räknas inte.
   - Recos omdömesfil läses inte, och RESEARCH.md läses bara för adresser.
   - Typsnittslistan är skillens data. Ändras dess format stoppas typsnitt utanför §7 som par igen.
   - Ingen verklig designkörning har observerats med rättelsen. Posterna verifieras av granskningen.
   - Ägaren avgör om en andra adress ska bli ett eget fält i schemat. r104#K3, radbrottet i metodkartan, har ingen post.


## Tillägg 2026-10-08: kundvaktens verifierade restvägar

**Status:** gäller på rättelsegrenen; sammanslagning och verklig åtkomst återstår.

Genomförande av den befintliga kundgränsen efter GR-20261007-r108-codex, inte ett nytt ägarbeslut. Kända nummer
ur samtliga lästa kundtexter prövas även i tjänsternas ID- och URL-fält. Befintliga underlag som inte kan läsas
eller avkodas ger inget anropstillstånd; bara frånvarande valfria filer lämnas. Bokadirekts underlag följer samma
princip. En postort i ett sammanhängande adressblock läses även på raden efter postnumret, utan att en ny
Markdown-rubrik eller ett nytt stycke fogas till adressen.

Även postorten med slutpunkt och listade kontaktfält omfattas. En följande setext-rubrik läggs inte till
adressblocket; dess streck eller likhetstecken kan vara korta enligt Markdown-syntaxen.

Riktiga krokingången provas med enbart syntetiska filer, också verkligt läsfel. Inga externa tjänster anropas.
Mönsterigenkänning har fortfarande begränsningar: provade exempel är inget generellt anonymiseringsbevis.
Originalgrenen r108 och dess underkända rapport bevaras; rättelsen ligger på en ny gren.

Den redan använda provisoleringen för Refero återanvänds här: processattrappen får en egen syntetisk
provnyckelfil i provets registrerade katalog, aldrig läsning av användarens hemligheter eller ett nätanrop.

## Tillägg 2026-10-08: helbyggets dom binds till kundöverlämningen

**Status:** gäller på integrationsgrenen; sammanslagning och verklig körning återstår.

Rättelse inom ägarens befintliga uppdrag om giltiga övergångar och godkännanden, inget nytt ägarbeslut.
`KUNDSTART.json` ingår i granskningens befintliga metodhash. En ny kundöverlämning kan ändra önskemål utan att
ändra företagsuppgifterna i `VERKSAMHET.json`; då får helbyggets gamla ägar-ja inte bli aktuellt igen. Slutbesked,
dashboard och export använder samma aktualitetskontroll, utan att skriva om tidigare domar eller slutposter.
Metodändringen gör även äldre granskningshashar för manuella underlag historiska; ingen gammal dom migreras till
ett nytt godkännande. Provet använder verklig metodhash och slutpost med en syntetisk kundkälla, ingen modell.

Det äldre provet för nekad riktningshistorik kräver nu också det tillkomna absoluta läsförbudet för Kundstarts
gemensamma lager. De båda tidigare kundnekandena och fallet utan slug prövas fortsatt exakt.

Städprovet tar bort ärvd `NPM_CONFIG_CACHE` när dess egen cache sätts. Dess eget npmrc-fall tar bort och återställer
båda stavningarna, eftersom npm läser dem före konfigurationsfilen. Därmed kan provet köras under en isolerad yttre cache utan att pröva fel cache;
produktionsstädningen ändras inte. Skapandeflödets beskrivning av ägarvalet följer nu README: själva valet startar
inget, medan nästa uttryckliga handling kan startas från Flöde eller samma CLI.

Lanseringsguiden och byggstandardens 6.6 hänvisar till samma nya mottagningskontrakt som formulärmottagaren.
Driftmätningen från 2026-10-05 räknas inte som verifiering av 422/413/503/202-kontraktet. Lagringskvittot och
mejlaviseringen hålls isär även i instruktionerna; inga historiska driftresultat eller ägardomar skrivs om.

Flödeshandlingens HTTP-fixtur serverar också dashboardens två separata skript som JavaScript och kräver att deras
funktioner laddats. Den tidigare allmänna HTML-reserven gav parserfel för skriptadresserna efter integrationen.
Okända filer ger nu 404 i fixturen; produktionsservern och kravet på tom lista med JavaScript-undantag
(`pageerror`) ändras inte. Provet intygar inte alla nät- eller konsolmeddelanden i andra vyer.

## Tillägg 2026-10-08: Claudes granskning av integrationen r117 och rättelserna efter den

**Status:** gäller på grenen `r117-granskning-claude-20261008` som genomförande av ägarens uppdrag 2026-10-08 (återupptagningen
efter Codex, punkt 3: bedöm integrationen); inget nytt ägarbeslut.

Ägarens uppdrag 2026-10-08 ~11:25Z, punkt 3, ordagrant:

> Granska R117:s samlade beteende och dokumentation, särskilt:
> - Kundstart → förberedelse → skiss → val → förfining → helbygge → export.
> - Att ändrat underlag gör äldre besked historiska.
> - Att stopp, återupptagning och återförsök fungerar utan dubbla starter.
> - Att tekniskt resultat, designgranskning, ägardom och leveransberedskap hålls isär.
> - Att kompetensens tillgänglighet, observerade användning och faktiska nytta inte blandas ihop.
>
> Återanvänd giltiga bevis. Kör om eller utöka prov när nya ändringar, fel eller konkreta frågetecken motiverar det.
>
> Vid fynd: skriv en ny granskning med reproduktion, konsekvens och minsta motiverade rättelse. Ändra inte historiska rapporter eller domar.

Granskningen GR-20261008-r117-claude (privat, `underlag/granskningar/`) fann tjugotvå fynd i r117 (a108560), varav tretton är
rättade här med prov som var röda mot a108560 och är gröna efter; resten står i backloggen med samma rapport som källa.

1. **Giltighetskedjan.** Helbyggets prövade besked (`korslut.aktuell`, Flöde, exportens vy) prövar nu också startsidans
   godkännande mot aktuellt underlag (`skapande.godkand_giltig`, samma kontroll som Flöde steg 5 och kor.sh), när det gällde
   vid körningens slut (A1). Ateljéposten för en äldre körning tar inte in en senare körnings domar (A2). En kort post om en
   start som stannade före körningen döljer inte det gällande beskedet i Flöde (A4).
2. **De fem tillstånden.** En körning som avbröts med en signal får slutkod 4 också när claude hann avsluta med kod 0, och
   klart för leverans kräver att sessionen avslutades normalt (C1). En dom som tillkommit efter en körning vars processer
   inte stoppades räknas inte i den prövade läsningen, som efter en avbruten körning (C2). Flöde steg 6 ur slutposten är
   kontrollerat bara när både tekniskt och designgranskaren godkänner; ett tekniskt ja utan godkänd granskning är skapat med
   bristen, aldrig grönt (C3). Byggkortet skiljer avstängd granskning från godkänd (C8).
3. **Stopp och omförsök.** Flödesarbetaren läser den sparade stoppbegäran under körningen och stoppar arbetet också när
   signalen inte når den (B2); stoppet går till kor.sh/exportera.py när arbetaren själv dött (B3); en arbetare som dog i
   steget startar är ett avbrott med återupptagning, inte en körning som pågår (B4); ett start-id vars begäran redan är
   avslutad svarar med sin slutkod i stället för som vägrad start, så fliken släpper det (B1); CLI:n skriver start-id och
   stoppväg (B8); förloraren av samma start-id under upptaget lås läser journalen (B6, rättelsen prövad bara med bokförd
   begäran).
4. **Kompetensens nivåer.** Ett MCP-svar som är en feltext utan felflagga, eller säger att inget matchade, är inte ett
   lyckat anrop med innehåll (C6). En läsning av ett verktygsskript (`cat …`) räknas inte som ett verktygsanrop (C7). Ett
   kompetenspass är genomfört bara när varje prövat beteende har sin bild, skissens pass visas som kärnan läst hel, och
   sessionens egen visuella bedömning och ändringslista märks som redovisade, inte observerade (C4, C5). Ateljépostens
   kompetenskedja säger var kvittona finns (C9).
5. **Formuläret.** Mottagaren sparar och skickar bara i produktionen (`VERCEL_ENV=production`); förhandsvisning och
   utveckling är demo också när variablerna råkar gälla alla miljöer (D2). Klientens och felsidans telefonmönster kräver en
   siffra som servern, filväljaren och felbeskedet nämner samma bildtyper som mottagaren tar emot (D5); kommentarerna och
   kunskapstexterna säger det som koden gör: 202-sidans omladdning, tidsfällan på felsidan, den föräldralösa bilagan och
   funktionens körtid (D1, D4, D7, D3).

**Kontroll:** prov_slutpost (46 fall), prov_kundstart_flode (23), prov_ateljeslut (26), prov_flodeshandling (12),
prov_flodesstart (10), prov_formularfel (18), prov_observation, prov_skisskritik (23), prov_flode och prov_dokumentationsvy är
gröna på grenen; de tio nya fallen är röda mot a108560 (loggarna i granskningens beviskatalog). Hela rökprovet på den
slutliga grenen redovisas i granskningen.

**Lämnat:** A3 (helbygget kan göra sitt eget godkännande historiskt genom att skriva i underlag/<slug>; gren E:s
promptkedja), D1 (202-sidan ska omdirigera), D3 (funktionens körtid i exporten), C4:s återstående krav på observerat
verktygsanrop per pass, B5/B7/B9/B10, D8/D9 står i backloggen. Ingen verklig session, extern tjänst, publicering eller
kundkontakt ingår; en grön gren är inte ett bevis för designkvalitet.

## Tillägg 2026-10-08: piloten — Kundstarts AI-intervju på det lokala abonnemanget, helbygget väntar, worktrees städade

**Status:** gäller.

Ägarens ord 2026-10-08 ~13:30Z, efter att granskningen av r117 slagits ihop och pushats, ordagrant:

> Vi väntar med helbygget, jag vill att ai intervjun ska ju gå på det lokala abonnemanget eftersom vi är i en pilot och inte mot faktiska kunder. du fixar worktrees som återstår också

Tre beslut:

1. **Helbygget väntar.** Inget verkligt helbygge genom den nya flödesingången nu; backlogposten om A3 (byggets skrivningar i
   underlag/<slug>) prövas när ägaren beställer det.
2. **Kundstarts AI-intervju går på det lokala Claude Code-abonnemanget i piloten.** Skälet är ägarens: piloten riktar sig
   inte mot faktiska kunder. Det avgränsar beslutet 2026-08-24 (Claude-prenumerationen driver inga kundtjänster: kundvänd AI
   går genom Gateway eller Console) till skarp kunddrift. Genomförandet i samma commit: `kundstart_modell.py --live-cli` kör en
   nästlad session per köjobb på abonnemanget (`ClaudeCLI`: metodtexten som systemprompt, kontexten som prompt, en tur,
   svaret i JSON-schema, utan verktyg, MCP:er eller API-nycklar, i en registrerad tempkatalog), och lagret lämnar bara jobb
   för ärenden märkta fiktiva till den transporten (`Lager.ta_jobb(bara_fiktiva=True)`): ett verkligt ärendes jobb stängs av
   utan lease och utan förbrukad budget. Server-API-vägen (`--live-api`) är oförändrad för skarp drift. Proven:
   prov_kundstart.py (tre nya fall, röda före). Det första verkliga pilotsamtalet redovisas i
   `underlag/rapporter/RAPPORT-2026-10-08-kundstart-pilot-abonnemang.md`.
3. **Worktrees.** De sjutton worktrees r105–r122 var rena och deras innehåll finns i main (a108560 och 81a222d); katalogerna
   togs bort med `git worktree remove`, grenarna står kvar så att historiken nås från git. r105:s och r108:s original är
   underkänd historik enligt Codex omgranskningar och finns kvar som grenar.

## Tillägg 2026-10-08: backlogavstämning och genomförande före första helbygget

**Status:** gäller; delvis ersatt av Tillägg 2026-10-09: ägarens precisering av "allt klart före första helbygget" (för de
sju backlogområdena där). Övrigt gäller.

Ägarens ord 2026-10-08 ~14:00Z, ordagrant: "Jag vill göra bort allt i backloggen innan vi sätter igång med första helbygget
och testar på nytt." Uppdraget i sin helhet (inventera först och ändra inget; fyra grupper GJORT, INTE AKTUELLT, SAMMANFÖR,
ÅTERSTÅR med belägg; genomför ÅTERSTÅR i ordningen A3/E1/C4:s rest/C6:s rest → D1/D3/D7/D8/D9 → småfynd → det som kräver
externt konto, publicering eller kundkontakt redovisas som väntande ägarbeslut; avsluta med en rapport) står ordagrant i
minnet och i `underlag/rapporter/RAPPORT-2026-10-08-backlogavstamning.md`. Helbygget väntar tills detta är klart; arbetet går
på det lokala abonnemanget, inga faktiska kunder.

Inventeringen 2026-10-08: 193 poster, 88 vilande. 31 var rättade i main (satta klar med commit och not), 3 ersatta av senare
beslut (kandidatflödet 2026-10-05/06, verktygslådan 2026-10-07, den äldre utforskningen), 6 sammanförda i bärare (spaningens
fyra, dokumentprovets tre, flödesvyns två), 48 återstår: 37 genomförbara (steg 1–3) och 11 som kräver verkligt prov,
ägarbeslut eller externt konto (steg 4). En klar post verifierad av GR-20261007-r99. Belägg per post i rapporten.

## Tillägg 2026-10-08: ägarens uppdrag ~14:35Z — ren start för Nortropic 2.0 och samlad startbesiktning (köat)

**Status:** gäller; köat 2026-10-08 (commit 7f77316, backlogposten B-20261008-ren-start-for-nortropic-2-0-och-samlad-startbesi); genomförs efter backlogavstämningen, delarna 3 och 5–7 sist på den gemensamma versionen.

Ägaren klistrade uppdraget i sessionen mitt i backlogavstämningen (tillägget ovan). Plats i ordningen: efter det pågående
uppdraget (backlogavstämningen 2026-10-08: steg 1–3 och slutrapporten) och före nästa ordinarie helbygge; inget parallellt
projekt och ingen avbruten provkörning. Backlogposten: `B-20261008-ren-start-for-nortropic-2-0-och-samlad-startbesi.md`. Codex motorinventering som
uppdraget hänvisar till: `underlag/granskningar/GR-20261008-motorinventering-codex.md` (gäller commit 062a930). Inget nytt
mandat för externa tjänster, köp, publicering eller kundkontakt. Ordagrant:

```text
Köa detta uppdrag efter ditt pågående arbete i nortropic-webb-pro. Avbryt inte en pågående provkörning och skapa inte ett parallellt, överlappande förbättringsprojekt. När det pågående arbetet är avslutat ska du genomföra uppdraget nedan före nästa ordinarie helbygge.

UPPDRAG: Ren start för Nortropic 2.0 och samlad startbesiktning

Målet är att nästa bygge får rätt underlag, att hela kedjans delar fungerar tillsammans och att vi kan följa var kvalitet eller information eventuellt försvinner.

Vi ska behålla kompetensen, verktygslådan och tillämpliga kvalitetsskydd. Äldre estetiska slutsatser ska inte automatiskt begränsa nya byggen. Fler dokument, regler eller lyckade verktygsanrop är inte i sig ett bättre resultat.

1. Köa och stäm av mot det pågående arbetet

Lägg uppdraget i befintlig uppdrags-/backlogstruktur och ange ordningen. Återanvänd befintliga poster där de täcker samma problem.

Läs:
- CLAUDE.md och README.md, särskilt kedjan och dokumentationsreglerna.
- Aktuella ägarbeslut och kunskap/designregler.md.
- underlag/granskningar/GR-20261008-motorinventering-codex.md
- Inventeringsbilagan i katalogen med samma namn.
- underlag/rapporter/RAPPORT-2026-10-08-backlogavstamning.md
- Senare rättelser, granskningar och provresultat.

Codex inventering gäller commit 062a930. Jämför varje fynd med den aktuella koden innan du rättar något. Något kan redan vara åtgärdat av ditt pågående arbete. Skilj genomfört från verifierat och skapa inga dubbla fynd.

2. Gör en avgränsad nollställning av designhistoriken

Klassificera befintligt styrande material som:
- aktivt och tillämpligt;
- historiskt;
- behöver omprövas.

Bevara historiken privat. Radera inte prototyper, kalibreringsoriginal, tidigare domar eller lärdomar permanent inom detta uppdrag. Koppla bort dem från automatiska arbetsunderlag där de inte längre ska styra.

Behåll:
- aktuella kundfakta och uttryckliga beslut inom rätt omfattning;
- relevant professionell kunskap och skills;
- verifierade tekniska lärdomar och regressionsprov;
- tillämpliga säkerhets-, integritets- och tillgänglighetskrav.

Avaktivera som generella designregler:
- äldre prototypers färg-, typsnitts- och layoutval;
- agenternas generaliseringar från tidigare misslyckanden;
- äldre modellbetyg som kvalitetsbevis för den nya motorn.

Kontrollera alla faktiska läsvägar, inklusive:
- riktningshistorik och aktuella domutdrag;
- UPPTAGNA-VAL och dess omgenerering;
- tidigare byggbilder i granskningen;
- automatiskt ärvda referenspaket och tjänsterapporter;
- härledda instruktioner i kunskapstexter och genererade uppdrag.

En ny riktning, en ny slug eller flyttade filer är inte ensamt bevis för en ren arbetskontext. Använd ett uttryckligt aktivt urval och återanvänd befintliga manifest och körningsidentiteter.

Bra externa referenser får återväljas uttryckligen. Kundfakta och aktuella sakbeslut får inte försvinna i rensningen.

3. Besiktiga hela kedjan och dess överlämningar

Gå igenom:
- miljö, beroenden, versionsunderhåll och startkontroll;
- Kundstart, research, brief, innehåll och material;
- referensfångst, Refero, Mobbin och övriga tilldelade tjänster;
- planering, skills, prototyper och specialistpass;
- ägarval, förfining, kalibrering och granskning;
- helbyggstart, stopp, fortsätt och felåterhämtning;
- tekniska kontroller, slutpost, export och kundrepo;
- leverans, dokumentation, observation och förbättringsloop.

För varje del redovisar du:
- verklig ingång och ansvar;
- indata och utdata;
- vilken version resultatet gäller;
- befintligt prov och vad det faktiskt bevisar;
- kvarstående fel eller obevisad förmåga;
- nästa konkreta kontroll.

Undersök särskilt överlämningarna: material som hämtats ska nå rätt uppdrag; det skaparen använder ska kunna observeras; godkännandet ska gälla det slutliga bygget.

4. Rätta och verifiera fynden

Hantera rapportens F01–F08 tillsammans med befintliga backlogposter. Prioritera:
- ren historik- och referensavgränsning;
- komplett identitet för granskningsunderlag och kalibrering;
- Motion-resultat som tappas i observationskedjan;
- saknade transkript som döljs i sammanvägda kvitton;
- skillernas föreskrivna läsordning och faktisk verktygsanvändning;
- nästlade sessioners avsedda MCP-konfiguration;
- misslyckad referensleverans som annars kan följas av planering;
- rätt sandlådemiljö genom den verkliga Flöde-ingången;
- bevarat godkänt underlag när helbygget tar vid.

Varje tilldelad kompetens ska få ett konkret arbete och användas enligt uppdraget. Skilj installerat, tilldelat, läst, anropat, returnerat material och visad tillämpning. Räkna inte ritualanrop eller skaparens egen redovisning som bevis på kvalitet.

Använd små rättelser och riktade negativa och positiva prov. Följ repots regler för regressioner, dokumentation och granskning. Kör ett tungt prov i taget på hela maskinen och redigera aldrig ett skalskript medan det körs.

5. Förnya kalibreringen med tydlig bevisgräns

Bekräfta vilka externa exempel som fortfarande motsvarar ägarens ribba. Skilj ankare från orörda utvärderingsexempel. Material som påverkat instruktionerna får inte samtidigt kallas oberoende slutprov.

Bind återanvända domar till den aktiva kalibreringen och det faktiska bedömningsunderlaget.

Mät särskilt om granskaren godkänner sådant ägaren underkänner. Hitta inte på ägardomar och sänk inte ribban för att få grönt.

6. Bevisa kedjan stegvis

Efter rättelserna:
- kör hela rökprovet på den färdiga versionen;
- gör avgränsade verkliga förmågeprov inom redan givet mandat, med fiktivt material;
- verifiera faktisk sessionskonfiguration, verktygsåtkomst, mottagna bilder och överföringen till uppdraget;
- låt ett bedömbart exempel gå genom research, plan, skiss och förfining.

Ägaren bedömer bilderna före skaparens förklaring. Nästa helbygge ska utgå från en faktiskt godkänd version.

Pröva därefter det riktiga helförloppet genom Flöde, inklusive stopp/fortsätt och normal avslutning, samt byggverifierad lokal export. Teknik, granskning, ägardom och export ska vara bundna till rätt slutversion.

Verkliga modell- eller tjänsteprov som saknar mandat redovisas som väntande. Aktivera inte externa tjänster, köp, publicering eller kundkontakt genom att tolka detta som ett nytt sådant mandat.

7. Leverera ett samlat besked

Återanvänd befintlig dokumentationsstruktur och dashboard. Håll dokumentationen aktuell i samma arbete och bevara äldre rapporter som historik.

Slutrapporten ska börja med:
- Redo för kontrollerat pilotbygge: JA/NEJ och skäl.
- Verkligt slutbygge godkänt: JA/NEJ/EJ PRÖVAT.
- Driftsatt leverans verifierad: JA/NEJ/EJ PRÖVAT.

Redovisa vad som rättats, vad som redan var gjort, exakta versioner och provresultat samt vad som återstår.

Lokalt fungerande mekanik, verklig extern åtkomst och professionell designkvalitet är tre olika saker. Ingen grön markering får betyda mer än sitt belägg.

Börja med att köa uppdraget och bekräfta dess plats efter det pågående arbetet. Genomför sedan arbetet i ordningen ovan inom befintligt mandat.
```

## Tillägg 2026-10-08: ägarens uppdrag ~14:58Z — slutför tidigare beställt införande (köat)

**Status:** gäller; köat 2026-10-08 (commit 62271a4, backlogposten B-20261008-slutfor-tidigare-bestallt-inforande-k01-k26-kund); genomförs efter backlogavstämningen, före ren start-uppdragets startbesiktning.

Ägaren klistrade uppdraget i sessionen strax efter uppdraget om ren start (tillägget ovan). Plats i ordningen: efter det
pågående uppdraget (backlogavstämningen 2026-10-08), sedan detta uppdrags del 1–5 tillsammans med ren start-uppdragets del 1–2
och 4, och sist ren start-uppdragets del 3 och 5–7 (startbesiktningen) på den slutliga gemensamma versionen. Backlogposten:
`B-20261008-slutfor-tidigare-bestallt-inforande-k01-k26-kund.md`. Codex kravavstämning som uppdraget hänvisar till:
`underlag/granskningar/GR-20261008-bestallning-mot-leverans-codex.md` med `KALLOR.json` (gäller commit 7f773165). Inget nytt
mandat för externa tjänster, köp, publicering eller kundkontakt; köläggningen ger inget mandat att starta nästa helbygge. Ordagrant:

```text
KÖA: slutför tidigare beställt införande i Nortropic

Detta är återstående arbete från mina tidigare beställningar, inte en ny produktinriktning. Köa arbetet efter pågående arbete och före nästa helbygge. Starta inget nytt bygge nu och avbryt inte pågående rättningar.

Återanvänd befintlig backlog, dokumentationsstruktur och körmekanik. Skapa inte en parallell uppgiftstavla eller nya poster för sådant som redan har en ansvarig post.

1. Läs och stäm av innan du planerar arbetet

Läs:
- CLAUDE.md och README.md.
- Gällande ägarbeslut i BESLUT.md, särskilt uppdraget om full verktygslåda, promptkedjan och automatiska kundrepon.
- underlag/granskningar/GR-20261008-bestallning-mot-leverans-codex.md
- Rapportens KALLOR.json.
- underlag/granskningar/GR-20261008-motorinventering-codex.md
- underlag/rapporter/HANDOVER-codex-2026-10-07.md
- underlag/granskningar/GR-20261008-aterupptagning-codex/STATUS.md

Kravavstämningen gäller 7f773165. Kontrollera aktuell kod, arbetsändringar, senare commits och prov innan du behandlar ett fynd som kvarstående. Senare uttryckliga ägarbeslut gäller.

Stäm av samtliga K01–K26. För varje rad:
- länka befintlig arbetsuppgift;
- ange vad som faktiskt är implementerat och inkopplat;
- ange verifieringsbevis och deras omfattning;
- ange exakt vad som återstår.

Redan rättat arbete ska verifieras och återanvändas. Gör inte om det.

2. Slutför de beställda delar som saknar körväg

A. Automatiska kundrepon och projektkontext

Varje nytt kundprojekt ska få ett eget lokalt repo och ett privat GitHub-repo enligt redan beslutade namn- och organisationsregler.

Projektet ska ha:
- stabil identitet och koppling mellan lokal sökväg och fjärrrepo;
- samma repo vid fortsättning, nya kandidater och återförsök;
- säker hantering av samtidiga starter och delvis misslyckad provisionering;
- ett kort kundspecifikt CLAUDE.md;
- rätt arbetsrot, skills, MCP-konfiguration och projektunderlag i de verkliga arbetssessionerna.

Flytta och verifiera skydden tillsammans med arbetskontexten. Privat underlag och hemligheter får inte följa med i repo, commit, push eller otillåtna tjänsteanrop.

En senare lokal export är inte en ersättning för detta krav.

B. Vercel och leverans

Koppla kundrepot till rätt befintligt Vercel-team och projekt. Återanvänd projektet vid fortsatta körningar.

Preview ska:
- bindas till rätt commit och byggversion;
- visas i dashboarden;
- få ett beständigt kvitto med faktisk status och kvarstående hinder.

Skilj lokal export, fungerande preview och godkänd produktionsleverans. Bevara befintliga publiceringsbeslut. Återanvänd den beslutade CLI-vägen om GitHub-appen fortfarande saknas; anta inte aktuell åtkomst utan verifiering.

C. 21st

Inför 21st i den faktiska skaparsessionens körväg:
- aktuell officiell integration och verktygslista;
- korrekt projektspecifik MCP-konfiguration och behörighet;
- konkret uppgift för komponentresearch, hämtning och anpassning;
- spårbar källa, licens, beroenden och användning;
- verifiering i den session som ska använda resultatet.

Builder är redan valt. Kontrollera faktisk åtkomst och rättigheter separat. Installation på användarnivå eller dokumentation räcker inte.

D. Bild- och videomaterialsteget

Bygg den redan beställda mekaniken för Higgsfield/Nano Banana/Seedance:
visuellt uppdrag → generation eller redigering → versionshanterad tillgång → webboptimering → faktisk användning.

Hantera relevanta bildformat, video, posterbild, mobilvariant, prestanda och reducerad rörelse. Bevara skillnaden mellan illustrativt material och bilder som påstår sig visa kundens verkliga verksamhet.

Ägarbeslutet var mekanik nu, konto senare. Bygg därför mekaniken och ärliga kontraktsprov utan att låtsas att extern åtkomst fungerar. Koppla Canvas-resultat till detta steg.

E. Planprövningens återgång

Planprövningen ska kunna leda till omprövad hypotes, annan referens, kompletterande research och ny planprövning innan skapandet fortsätter.

Ett konstaterat problem får inte bara bokföras medan körningen fortsätter med samma låsta plan. Återanvänd befintliga identiteter, budgetar och tillstånd.

3. Rätta och slutför övergångarna

Kontrollera särskilt:
- nya sessioner som felaktigt får beskedet att kompetensen redan lästs i en tidigare session;
- verklig återupptagning kontra ny session med explicit överlämning;
- motsägelsen mellan att börja från steg 1 och fortsätta från en godkänd startsida;
- bevarande av det underlag och den designversion som godkänts;
- skill- och MCP-konfiguration i nästlade sessioner;
- saknade transkript och ofullständiga kompetenskvitton;
- Motion-resultat genom observation, kvitto och kompetenspass;
- hantering av tomma eller misslyckade referenshämtningar.

Återanvänd pågående rättningar där de löser detta. Markera inte en rättning som färdig enbart för att den finns i arbetsdiffen.

4. Slutför kompetensens faktiska användning och verifiering

Tilldelade skills ska aktiveras där skillsystemet stöder det. Referensfiler ska läsas enligt instruktionerna. Tilldelade verktygsuppgifter ska ge ett kontrollerat resultat som faktiskt kan användas.

Följ:
tillgänglig → aktiverad/läst → anropad → användbart resultat → använd i arbetet → resultat bedömt.

Verifiera Refero/Mobbin, Motion/GSAP, Canvas/HIG och referensinspektionen utifrån deras beställda uppgifter. Klargör DevTools manuella respektive integrerade roll.

Kräv inte meningslösa anrop till varje endpoint. Ett lyckat anrop eller läskvitto är inte designkvalitet. Saknad observation ska beskrivas som en observationslucka, inte automatiskt som uteblivet arbete.

Genomför den beställda utvärderingen av Dynamic Workflows. Införande är inte obligatoriskt; ett belagt beslut att behålla befintlig orkestrering är ett möjligt resultat.

MotionSite.ai och Motion+ är avvalda och ska inte återinföras som krav.

5. Slutför Kundstart och Kirurgens kvarstående beviskedja

Bevara redan införd lokal mekanik.

Kundstart:
- skilj det genomförda enstaka AI-varvet från verifierad flertursförmåga;
- pröva informationsförlust, felaktiga antaganden, upprepningar, rättelser och korrekt överlämning;
- håll utvecklingsfall och orörda bedömningsfall åtskilda.

Kedjan:
- gör det möjligt att följa insamlat, förstått, överfört, använt och levererat;
- redovisa det som fortfarande inte går att fastställa;
- använd inte filöverföring som bevis för förståelse eller användning.

Kirurgen:
- slutför den avsedda vägen från signal till prövad förändring, tillåtet införande och observerad effekt;
- återanvänd ordinarie granskning och Git;
- bevara negativa och ofullständiga utfall;
- beskriv inte registrerad effekt som automatiskt bevisat orsakssamband.

Ingen självaktivering, mandatändring eller automatisk publicering får smygas in. Mänsklig användarprövning kräver deltagare, samtycke och mandat.

6. Verifiering och leveransredovisning

För varje genomförd del behövs proportionerliga prov genom den riktiga ingången, inklusive relevanta fel-, avbrotts- och återförsöksvägar.

Stubbar verifierar mekanik. De verifierar inte extern åtkomst, modellförmåga eller designkvalitet.

Verkliga modell-, MCP- och driftprov görs inom befintligt mandat och budget. Avgränsa väntande åtkomst utan att stoppa oberoende arbete.

Respektera ett tungt rökprov åt gången, pågående arbete och repots arbetsregler.

Håll en samlad aktuell leveransöversikt i befintlig dokumentationsstruktur:
- beställt;
- implementerat;
- inkopplat;
- lokalt prövat;
- verkligt prövat;
- kvalitetsbedömt;
- kvarstående arbete eller uttryckligt uppskjutet beslut;
- bevislänk och granskad version.

Bevara historiska rapporter. Uppdatera den aktuella överblicken så att jag inte behöver pussla ihop verklig status ur gamla rapporter.

Kalla inte hela införandet färdigt förrän kraven är levererade eller tydligt avgränsade genom ett befintligt ägarbeslut.

Avsluta köläggningen med:
- var uppdraget finns;
- vilka befintliga poster det knyts till;
- beroendeordningen;
- vad som redan är rättat;
- vad som återstår före nästa helbygge.

Samordna med det redan köade arbetet för ren 2.0-start och samlad startkontroll. Startkontrollen ska bedöma den slutliga gemensamma versionen. Köläggningen i sig ger inget mandat att starta nästa helbygge.
```

## Tillägg 2026-10-09: ägarens precisering av "allt klart före första helbygget", och avstämningen av de sju återstående backlogområdena

**Status:** gäller (preciseringen, för de sju områdena); uppdraget genomfört i RAPPORT-2026-10-09-sju-backlogomraden
(privat), med noter i de sju posterna.

Ägaren klistrade uppdraget i sessionen 2026-10-09 ~05:22Z, köat efter uppdraget om Codex omgranskning (N01–N06), och
godkände i det en precisering av kravet från 2026-10-08 (tillägget om backlogavstämningen ovan): det som kan göras före
bygget görs och prövas före starten; det som kräver ett verkligt helbygge verifieras under det; besökarprov genomförs vid
en användbar prototyp och inför lansering, med deltagare och mandat; strategiska experiment får ligga uttryckligen
uppskjutna och redovisas aldrig som genomförda eller verifierade. Preciseringen gäller de sju områdena (kalibreringen,
mobilreglerna, prototyp mot helbygge, besökarprovet, modellsållningen, granskare ur en annan modellfamilj, plattformsprovet
med Framer och Caliper) och upphäver inga säkerhetskrav, datagränser eller andra ägarbeslut. Inget mandat för köp, konton,
installationer av nya externa verktyg, publicering eller deltagarkontakter; ägaren startar helbygget själv. Ordagrant:

```text
UPPDRAG: stäm av och prioritera de sju återstående backlogområdena inför nästa helbygge när pågående arbete är klart.

Mitt beslut som ägare
Jag godkänner följande precisering av mitt tidigare krav ”allt ska vara klart före första helbygget”:

- All förberedelse och implementation som kan göras före bygget ska vara färdig och prövad före starten.
- Sådant som kräver ett verkligt helbygge verifieras under det bygget.
- Besökarprov genomförs när det finns en användbar prototyp och inför skarp lansering, med deltagare och mandat.
- Strategiska experiment får ligga kvar uttryckligen uppskjutna. De ska inte redovisas som genomförda eller verifierade.

Detta gäller de sju områdena nedan. Det upphäver inga säkerhetskrav, datagränser eller andra uttryckliga ägarbeslut.

Genomför det lokalt möjliga arbetet enligt repots arbetsregler. Starta inget helbygge; det startar jag själv. Gör inga köp, kontoregistreringar, installationer av nya externa verktyg, publiceringar eller deltagarkontakter inom detta uppdrag. Läsande omvärldsbevakning är tillåten.

1. STÄM AV VERKLIGHETEN FÖRST

Läs aktuella backlogposter, kod, prov och dokumentation. Kontrollera vad som redan är genomfört och vad som faktiskt återstår.

Codex uppgifter nedan kommer från granskningen av main 2c7aa5a. Kontrollera dem mot aktuellt HEAD; behandla dem inte som oföränderliga.

Dela varje post i:
- färdig implementation, med bevis;
- lokalt arbete före helbygget;
- verklig verifiering under pilotbygget;
- arbete inför skarp lansering;
- uppskjutet experiment;
- konkret ägarbeslut.

Återanvänd befintliga poster och dokumentationsstruktur. Skapa inte parallella rapporter eller nya backlogposter för samma ansvar. Uppdatera inaktuella beskrivningar och länka till befintliga bevis. Bevara historiska rapporter.

2. KALIBRERING: FÄRDIGSTÄLL UNDERLAGET FÖRE MINA DOMAR

Kontrollera att K14–K19 är kompletta och jämförbara. Vid Codex kontroll saknade K17 och K18 undersidornas kataloger, bilder och inspektionsrapporter.

Förbered det som går inom mandatet. Om kompletteringen kräver en körning utanför mandatet: redovisa exakt vilken. Sänk inte omfattningen tyst och presentera inte ofullständigt underlag som klart för bedömning.

Kontrollera även kvarstående anmärkningar på kalibreringsankarnas underlag. Jag ska få ett färdigt beslutsunderlag, inte behöva upptäcka tekniska brister själv.

För försöket gäller:
- Frys modell, instruktioner, kriterier, ankare och bilder före utvärderingen.
- Mina domar över K14–K19 får inte visas för granskarna.
- Använd inte domarna för att ändra visuell-niva.md eller granskarinstruktionerna före det oberoende försöket.
- Redovisa falska godkännanden och falska underkännanden separat, med antal och nämnare.
- Ogiltiga eller misslyckade anrop redovisas separat, aldrig som giltiga domar.
- Om resultaten används för metodutveckling är exemplen därefter utvecklingsdata.

Sex exempel är en första avgränsad kontroll, inte bevis på allmän träffsäkerhet. Kalibreringen prövar granskarens bedömning mot min ribba; den bevisar inte byggarens designförmåga eller sajtens användbarhet.

Källa:
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

3. MOBILREGLER: AVGRÄNSA DET VERKLIGA BESLUTET

Backlogposten är delvis inaktuell. Kontrollera detta:
- GRANSKARE.md tillåter redan standardiserad navigation och formulär.
- Byggskillen låter den godkända kandidaten bestämma mobilens komposition.
- designregler.md har fortfarande ett gemensamt krav på att primär handling syns i första mobilvyn och nås med tummen.

Gör en kort avstämning av de regler som fortfarande styr formgivningen:
regel → källa → räckvidd → var den verkställs → klassning → eventuell kvarstående fråga.

Skilj mellan:
- tillgänglighets- och funktionskrav;
- Nortropics uttryckliga produktkrav;
- belagda kundbehov;
- designhypoteser och visuella preferenser.

Återinför inte generella krav på viss menyplacering, sidhuvudshöjd, rubrikkomposition, foto ovanför vikningen eller fast kontaktlist.

Om ett ägarbeslut fortfarande behövs, förbered konkreta alternativ och en rekommendation. Använd befintligt bildmaterial där det räcker. Starta inte nya skaparsessioner enbart för detta utan mandat.

Ett smakbeslut får vara ett produktval med angiven räckvidd; kalla det inte universell UX-praxis utan belägg. Behåll fungerande tillgänglighetskrav. Exempelvis ska Nortropics krav på primära knappar inte blandas ihop med WCAG:s minimikrav eller göras till ett krav på alla länkar.

Källa:
https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html

4. PROTOTYP MOT HELBYGGE: FÄRDIGSTÄLL DEN AUTOMATISKA DELEN

Vid Codex kontroll jämförde prova.vinnarjamforelse:
- startsidans första ruta och helsida;
- bredderna 390 och 1440;
- totalt fyra bildpar.

Undersidorna ingick inte, och granskarens frysta vinnarunderlag tog bara startsidans bilder.

Kontrollera nuläget och färdigställ inom befintlig mekanik:
- jämförelse av godkända undersidor;
- rätt bildparning mellan godkänd prototyp och aktuellt bygge;
- överföring av relevant underlag till granskaren;
- tydlig rapportering av vad som jämförts och vad som saknas;
- versionsbindning så att rätt godkänd design jämförs med rätt slutbygge.

Bestäm vilka ytterligare bredder och interaktionstillstånd som faktiskt behöver jämföras utifrån den godkända designen. Skapa inte ett omfattande generellt mätsystem utan behov.

Pröva lokalt med fixturer enligt repots regler. Verklig verifiering sker i pilotbygget.

Pixelavvikelse visar förändring, inte kvalitet. Granskningen ska bedöma om förändringen är en försämring, en godkänd anpassning eller en förbättring. Saknat jämförelseunderlag får inte tolkas som bevarad design.

5. BESÖKARPROV: FÖRBERED NU, GENOMFÖR VID RÄTT TILLFÄLLE

Skilj detta från den automatiska bildjämförelsen.

Förbered ett kort protokoll utifrån besökarens viktigaste uppgifter:
- vad deltagaren ska försöka åstadkomma;
- vad vi observerar;
- var deltagaren tvekar, missförstår eller fastnar;
- vad som ändras efter observationen.

Uppgifterna ska vara neutrala och inte avslöja vilken knapp deltagaren ska använda. AI-simuleringar är inte verkliga användarobservationer.

Återanvänd befintlig lagring och dokumentationsvy där det går. Bygg inte en ny forskningsplattform. Rekrytering, deltagarnas medverkan och eventuell inspelning hanteras separat med mandat.

Källa:
https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing

6. ÖVRIGA EXPERIMENT: BEHÅLL DEM, MEN LÅT DEM INTE BLOCKERA PILOTEN

Modellsållning i spaningen:
- Kontrollera först om befintliga loggar räcker för en meningsfull baslinje.
- Ett senare försök jämför samma kandidater med och utan modellsållning.
- Mät användbara fynd, missade fynd, kvot och granskningsarbete.
- En vecka är ett insamlingsfönster, inte automatiskt tillräckligt bevis.

Annan modellfamilj:
- Behåll befintligt beslut att avvakta.
- Ett första försök ska vara kompletterande granskning utan att styra godkännandet.
- Nyttan mäts i relevanta brister som upptäcks och bekräftas, inte bara i att modellerna tycker olika.

Framer:
- Behåll som senare plattformsprov.
- Samma brief, material och omfattning.
- Jämför resultat, arbetstid, mänskliga ingripanden, redigerbarhet och löpande kostnad.
- Starta inget konto eller försök nu.

Caliper:
- Korrigera eventuell uppgift om ”npx caliper”.
- Det avsedda projektet är edonadei/caliper och dokumenterar Pythonpaketet caliper-eval; dess skill installeras separat.
- Installera inget inom detta uppdrag.
- Bedöm om verktyget förenklar våra befintliga jämförelser med och utan en skill eller instruktion.
- Verktygsaktivering och resultatkvalitet ska bedömas separat.

Källa:
https://github.com/edonadei/caliper

7. PROV, DOKUMENTATION OCH SLUTBESKED

Följ repots gällande regler för grenar, commits, dokumentation, tempkataloger och prov. Ett tungt prov åt gången. För beteenderättelser: relevant prov rött före och grönt efter. Attrapper bevisar mekanik, inte verklig designkvalitet eller extern åtkomst.

Avsluta med ett kort besked som länkar till den uppdaterade dokumentationen:
- Vad är färdigt och hur har det verifierats?
- Vad måste göras före helbygget?
- Vad ska själva pilotbygget verifiera?
- Vad behövs från mig, med färdigt underlag?
- Vad ligger uttryckligen uppskjutet och varför?

Markera aldrig uppskjutet, attrappat eller oprövat arbete som verifierat.

Målet är att nästa bygge ska kunna bevara en design jag faktiskt godkänt, och att vi kan se var kvaliteten förändras. Prioritera konkreta förbättringar i den kedjan. Leverera inte fler verktyg eller mer dokumentation som ersättning för ett bedömbart resultat.
```

## Tillägg 2026-10-09: ägarens beslut om den primära handlingen på mobilen, ankarna K07 och K03 och kalibreringsförsöket

**Status:** gäller. Mobilbeslutet genomfört i designreglerna, byggstandarden, granskarens text och uppdragen; K03 är
historik i kalibreringen; K07 väntar på ägarens bekräftelse; försöket följer ordningen nedan.

Ägaren klistrade besluten i sessionen 2026-10-09 ~08:30Z, som svar på underlaget i RAPPORT-2026-10-09-sju-backlogomraden
(alternativen A–C för mobilen, och för ankarna). Räckvidd: dagens erbjudande och kalibreringen av granskaren.
Kvalitetsprovet och förmågeprovet beslutas separat, och beskedet startar inget helbygge. Ordagrant:

```text
Mina beslut och nästa steg:

1. Mobil: C, med följande precisering.
Den primära handlingen ska vara tydlig och lätt att hitta. Placering i mobilens
första vy krävs när briefens prioriterade besökaruppgift motiverar det.
Motiveringen kan bygga på kundunderlag och relevant research; saknas direkt
användarbevis ska den märkas som en hypotes att pröva.

Behåll minst 44×44 CSS-pixlar som Nortropics produktkrav för primära
interaktiva kontroller. Skilj detta från WCAG:s minimikrav.
”Med tummen” och fast nederlist är inga generella layoutkrav.
Bedöm funktion och visuell kvalitet var för sig.

2. K07: förbered alternativ 1.
Visa den gamla och nya fångsten sida vid sida, tillsammans med mina tidigare
ord. Jag bekräftar eller ändrar domen innan den nya bilden används som ankare.
Bevara den gamla bilden med dess ursprungliga dom som historik.

3. K03: alternativ 2 för den aktiva kalibreringen.
Ta bort K03 som helhetsankare. Bevara bilderna och domen som historik med
fångstbegränsningen dokumenterad. Redovisa att nästan-nivån tills vidare bara
har K05. Använd inte K14–K19 för att komplettera ankarna.

Efter K07-bekräftelsen:
- genomför och prova ändringarna;
- frys metod, ankare, bilder, bedömningsregler och försöksupplägg;
- låt mig döma K14–K19 blint;
- därefter får du köra de sex planerade granskarsessionerna utan ytterligare
  klartecken, inom det redan beskrivna omfånget.

De undanhållna exemplens ägardomar får inte nå granskarna. Redovisa felaktiga
godkännanden, felaktiga underkännanden och ofullständiga körningar separat.
Sex exempel ger ett första diagnostiskt resultat, inte ett säkert mått på
generell träffsäkerhet. Ändras metoden efter resultatet blir urvalet
utvecklingsdata.

Kvalitetsprovet och förmågeprovet beslutas separat; de ingår inte i detta
klartecken. Starta inget helbygge genom detta besked.
```

Ersatt (ur `kunskap/designregler.md`, gemensamma kvalitetskrav, bevarat här):

| Ersatt regel | Hade räckvidd | Ersatt av | Varför |
|---|---|---|---|
| "Den primära handlingen nås: den syns i första vyn på mobilen och går att nå med tummen. Hur den löses (sidhuvud, list, sektion) är riktningens val." | alla kunder | kvalitetskravet att den primära handlingen är tydlig och lätt att hitta; första vyn på mobilen som kundens behov när briefens prioriterade uppgift motiverar det; tummens räckvidd och fast nederlist som designhypotes | ägarens beslut 2026-10-09 (alternativ C med precisering) |

## Tillägg 2026-10-09: den visuella arbetsytan — ägarens uppdrag ~07:24Z och genomförarens huvudväg

**Status:** gäller; genomfört och lokalt aktiverat 2026-10-09 (backlogposten
`B-20261009-visuella-arbetsytan-samtal-preview-sessioner-och`; hur arbetsytan fungerar, dess gränser och vad som inte är
prövat: `kunskap/arbetsyta.md`; granskningarna: `underlag/granskningar/GR-20261009-arbetsyta-oberoende.md` och
`GR-20261009-arbetsyta-omgranskning.md`). Valet av huvudväg nedan är genomförarens teknikbeslut inom uppdraget, inte ett
ägarbeslut; ägarens beslut är uppdraget självt.

Ägaren skickade uppdraget och ett byggpaket med tre konceptbilder i en ny session (första klockavläsning 07:24:48Z). Paketet
ligger privat i `underlag/arbetsyta/uppdraget-20261009/` (BYGGPROMPT.md, LAS-MIG.txt, `referenser/01-arbetsyta.png`,
`02-byggflode.png`, `03-kodvy.png`, SHA256SUMS; bildernas sha256 stämmer med paketets LAS-MIG.txt). Bilderna är
AI-genererade koncept: visuell riktning, inte data. Arbetsytan och dess gränser beskrivs i `kunskap/arbetsyta.md`.

**Huvudvägen: B, den befintliga dashboarden** med en tunn Claude-integration (partnerdialog genom `claude -p` med samma
sessions-id, en läsande mod i Claude Code). Jämförelsen gällde vad som faktiskt går att integrera, 2026-10-09:

- **A, Open WebUI Computer** (`cptr` v0.9.21 från 2026-08-04, senaste commit på main f9d1d8c 2026-08-17; licensen Open Use
  License ovanpå Elastic License 2.0, med förbud att ta bort, ersätta eller *komplettera* ursprungsmärkningen). Den startar
  egna Claude-sessioner genom claude-agent-sdk och hittar inte sessioner som startats utanför den (inget läser
  `~/.claude/projects`); egna vyer kräver en fork av Svelte-gränssnittet med byggsteg; förhandsvisningen går genom en proxy
  på appens eget ursprung med injicerat skript, alltså inte en isolerad och oförändrad preview. Den uppfyller därför inte
  kravet att följa Nortropics redan startade sessioner eller att visa preview skilt från kontrollytans ursprung. Den
  installerades inte; bedömningen bygger på källkoden, dokumentationen och licensen (läst 2026-10-09).
- **B, dashboarden** har redan ägarens nyckel och ursprungskontroll för skrivningar, flödets idempotenta start- och
  stoppväg (`/api/flode/<slug>/start`, start-id, startjournalen), blindningen före ägarens första val på servervägen,
  observatören med sessions-id från start (`kontroller/observation.py`) och förhandsvisning på en egen port. Det som saknas
  är en gemensam läsväg per körning och session, strömning, de tre vyerna, partnerdialogen och modden.
- **Open WebUI huvudprojektet** prövades inte vidare: det löser ingen nödvändig del bättre (Pipe-funktioner kör godtycklig
  Python i UI-serverns process).

**Nollmätning 2026-10-09** (dashboarden på :4771, main 12b7004): för att se vilka sessioner som arbetar för en kund och vad
de lämnat behövdes fyra vyer (Översikt, Flöde, Prototypens observation, Bygge); observationen svarade på 0,46 s (46 755
byte) för det enda projektet med ateljédata, sju sessioner varav en avbruten utan slutbesked; helbyggets session har inget
sessions-id från start (stream-json-loggen bär det på varje rad); inga körningar finns under `kunder/*/korningar/` efter den
rena starten; ingen dialog, ingen inbäddad preview, ingen strömning (vyn frågar om var 8–30 s).

**Datakällorna** är de befintliga: ateljéns `STATUS.json`, sessionsförteckningen och transkripten, startjournalen
(`underlag/<slug>/ateljestarter/`), helbyggets `START.json`, stream-json-logg och `SLUT.json`, ateljéns slutpost,
kandidaternas `STATUS.json` och `versioner/`, domloggen och kundrepots `KUNDREPO.json`/`EXPORT.json`. Det nya som lagras är
bara kopplingar: partnersamtalets sessions-id och meddelandenas id per kund, och ändringsbegärans id mot domloggens rad.
Ingen ny status för körningar, granskningar eller godkännanden.

**Claude Code 2.1.290** (installerat, `claude --version`): `--bg` kan inte kombineras med `-p`; `--resume <id>` återanvänder
id:t utom med `--fork-session`; `-p`-sessioner binder en inkorg för meddelanden mellan sessioner, men ett meddelande från en
okänd avsändare hålls i en `-p`-session tills det gått ut, och ett meddelande mitt i en skapares arbete binds inte till
kandidatens version; ändringar går därför den befintliga vägen över ägarens beslut och nästa handling. Mods finns från
2.1.287 (terminalen); kontraktet läses ur den inbyggda skillen plugin-authoring för just den versionen.

**Modellprofilen** är en hypotes som görs provbar, inte en ny standard: arbetsledningen (partnern) prövar Fable 5.1, och vyn
visar konfigurerad och observerad modell per roll. Kundflödets standarder ändras inte: ateljéns skapare kör i dag
`claude-fable-5-1` på `max` (`NWP_ATELJE_MODELL`), kandidatgranskarna `claude-sonnet-5-5[1m]` och helbygget `opus[1m]`.

**Överlappande arbete:** huvudsessionen arbetar samtidigt med de sju backlogområdena och därefter metod till resultat
(kandidater.py, granska.py, referenstjanster.py) i egna worktrees. Arbetsytan läser blindningen, arbetsroten och
återupptagningen som de är och löser inga av deras fynd en gång till.

Ordagrant:

```text
# Bygg Nortropics visuella arbetsyta med Claude Code

## Uppdrag och mål

Arbeta i `Nortropic/nortropic-webb-pro`:
https://github.com/Nortropic/nortropic-webb-pro

Du är ansvarig produktutvecklare och integrationsingenjör. Bygg en fungerande lokal arbetsyta utifrån de tre bifogade konceptbilderna: samtal, riktig sajtpreview, kodarbete, automatiskt synliga sessioner, arbetsflöde och verifierbara resultat på samma ställe.

Jag heter Johnny. Jag vill starta ett kunduppdrag, följa vilka verkliga sessioner som arbetar, se resultatet växa fram, diskutera med en arbetsledare och ge en avgränsad ändring utan att kopiera meddelanden mellan terminaler.

Detta är ett genomförandeuppdrag: undersök, välj en avgränsad teknisk väg, implementera, prova, dokumentera och aktivera det som verifierats lokalt. Stanna inte vid en plan, en mockup eller en ny lista förbättringsförslag. Ingen garanti om felfrihet ersätter faktiska prov.

Bygg vidare på Nortropics befintliga motor. Arbetsytan ska visa och använda samma uppdrag, sessioner, underlag, versioner, startvägar, kontroller och godkännanden. Skapa inte en parallell byggmotor, generell agentplattform eller konkurrerande sanningskälla.

## Målbilderna och deras räckvidd

Läs de tre bilderna visuellt innan du utformar gränssnittet. I byggpaketet heter de:

- `referenser/01-arbetsyta.png`: partnerdialog till vänster, stor verklig preview i mitten, rollsessioner till höger och åtgärder/bevis nära resultatet.
- `referenser/02-byggflode.png`: projektets moment, sessioner och överlämningar samt referenser, kompetenser och senaste preview.
- `referenser/03-kodvy.png`: projektfiler, kod-/körningsvy och webbläsare, med sessionens aktivitet och nästa handling nära till hands.

Bilderna anger godkänd visuell inriktning, inte en verifierad implementation. Bevara deras mörka grafittoner, återhållsamma blå accenter, tydliga typografiska hierarki, panelindelning och närheten mellan dialog och resultat. Gör en sammanhängande produkt med tre vyer, inte tre olika appar. Föredra ett tydligt primärt arbetsområde framför att visa alla paneler samtidigt.

Bilddetaljer som modellnamn, kundnamn, certifieringar, poäng, procenttal, datum, terminalkommandon och filstruktur är exempeldata. De godkänner inte nya leverantörer, kundlöften eller en teknikmigration. Använd Johnny eller befintlig användaridentitet, inte bildens ”Andrej”. Behåll sajtens faktiska stack; inför inte Next.js för att det står i en konceptbild. Gör inte ChatGPT, Perplexity eller Figma till nya aktörer för att deras logotyper syns där.

Redovisa större avvikelser från målbilden med skäl. Bildinnehåll får inte bli riktiga kunduppgifter. Testdata ska vara märkt och isolerad. Om bilderna saknas i sessionen: använd denna layoutbeskrivning och redovisa att direkt bildjämförelse återstår; påstå inte att du har sett dem.

## Mandat och avgränsning

Detta mandat omfattar arbetsytans utformning, nödvändiga små integrationsändringar, en tunn Claude-integration, relevanta tester och dokumentation. Här är en sammanhängande omarbetning av användarytan avsiktlig; det är inte mandat att omarbeta hela motorn eller genomföra hela backloggen.

Du får använda befintliga godkända verktyg och budgetar, skapa isolerade testprojekt och göra begränsade verkliga sessionsprov inom dem. Nya utvecklingsberoenden ska granskas, versionslåsas och tas in genom repots normala beroendeväg. Ingen godtycklig global installation eller massuppdatering.

Inga nya abonnemang, höjda användningsgränser, inhämtade lösenord, publika tunnlar, kundutskick, verkliga kundpubliceringar, DNS-ändringar eller fullskaliga kundbyggen ingår. En befintlig export eller preview kan ha sidoeffekter: kontrollera dem innan den används i prov. Tekniska testfall får inte skapa riktiga fjärrepon eller externa leveranser.

Följ aktuella regler för commits och push i motorrepot. Överskriv inte andras ändringar, avsluta inte deras processer och gör ingen bred städning, destruktiv reset eller force-push. Ändra inte mergepolicy som sidouppdrag.

Fortsätt mellan etapper utan rutinmässiga ägarstopp. Samla verkligt nödvändiga frågor om exempelvis obestämd budget eller utökad åtkomst i en kort fråga, och fortsätt med oberoende delar. Mina kundbeslut får aldrig ersättas av agentmeddelanden eller testdata.

# Etapp 1 av 6 — Verifiera nuläget och välj huvudväg

Den senast kontrollerade GitHub-versionen inför denna prompt var `12b700477ebebb65e537ab2ccaa8eaa9a4d9ec7c`, den 9 oktober 2026. Använd den som referens, inte som ett checkout- eller återställningskommando. Kontrollera aktuell gren, commit, remote, arbetskopior, lokala ändringar och pågående uppdrag. Läs relevanta senare beslut och överlappande granskningar; tidigare promptar är inte bevis för genomförd implementation.

Börja med `CLAUDE.md`, `README.md`, instruktionerna för dokumentationsändringar och de berörda delarna av `kunskap/skapandeflodet.md`, `kunskap/metodkarta.md` och `kunskap/designregler.md`. Följ den verkliga koden, särskilt:

`dashboard/`, `kontroller/observation.py`, `atelje.py`, `kandidater.py`, `prototyp.py`, `flodesstart.py`, `korregister.py`, `korslut.py`, `ateljeslut.py`, `nastlad.py`, `kompetens.py`, `kundrepo.py` och `kor.sh`.

Namnen är ingångar, inte ett krav att ändra alla filer. Läs större historik bara för konkreta frågor. Bevara pågående arbete kring blindning, arbetsrot och återupptagning; lös inte samma fynd en gång till.

Kontrollera verklig Claude Code-version, tillgängliga kommandon, stöd för plugins/Mods, sessioner och kommunikation. Skilj publika dokument, installerad funktion och lokalt verifierat beteende. De tidigare länkade Mods-sidorna gick inte att hämta vid denna promptförberedelse; det bevisar inte att funktionen saknas. Använd officiellt index, lokal hjälp och faktiska typer/exempel innan du skriver integrationskod. Hitta inte på ett Mod-API.

### Välj ett skal, inte tre implementationer

Gör en kort, praktisk jämförelse av:

A. Open WebUI Computer som befintlig arbetsstation, med Nortropics egna vyer och kontroller anslutna utan djup fork.
B. Den befintliga Nortropic-dashboarden som huvudapp, kompletterad med en liten Claude-integration.

Huvudprojektet Open WebUI är inte samma produkt som Computer. Utvärdera huvudprojektet bara om dess befintliga funktioner faktiskt löser en nödvändig del bättre. Bygg inte alla alternativen.

Computer är en kandidat att pröva, inte ett redan fattat plattformsbeslut. Kontrollera aktuell licens, villkor, autentisering, åtkomst till värddatorn, resursbehov och verkliga integrationspunkter. Behåll obligatorisk ursprungsmärkning. Ingen white-label-fork eller installation av en historisk osäker version för att kringgå villkor.

Ett användbart prov ska kunna visa rätt Nortropic-projekt, befintlig körningsinformation och riktig preview. Att kunna starta en ny Claude-chatt är inte bevis för att hitta Nortropics redan startade sessioner. Flytta inte motor och kunddata till Docker om det bryter lokala process-, sökvägs- eller säkerhetsantaganden.

Välj huvudväg efter faktisk integration, säkerhet, visuella krav, underhåll och resursåtgång. Om Computer inte vinner det avgränsade provet: fortsätt i befintlig dashboard, utan att låta plattformsutredningen stoppa uppdraget. Claude-panelen ska vara en tunn komplettering, inte en andra fullständig frontend.

Dokumentera beslutet, kort nollmätning, datakällor och acceptansvillkor i repots befintliga struktur. Skilj genomförarens teknikbeslut från ägarbeslut. Visa de sex etappernas status och fortsätt.

**Klart när:** huvudväg, faktisk startmiljö, överlappande arbete och ett testbart första genomgående flöde är bestämda.

# Etapp 2 av 6 — Koppla ett verkligt uppdrag till en levande följvy

Börja med ett litet fungerande samband: rätt kund → rätt körning → rätt session → observerad aktivitet → rätt artefakt. Använd sparade data och en liten verklig testsession, inte ett fullt kundbygge.

Återanvänd observatören och befintliga resultatläsare. Om en gemensam läsväg behövs, gör den liten och användbar för både huvudvyn och Claude-panelen. Tillåt lagring av nya nödvändiga konversationskopplingar och användarens layoutval, men skapa inte en andra auktoritativ uppgiftsstatus eller kopia av kundens faktaregister.

Varje post ska gå att knyta till relevant kund, uppdrag, körning, kandidat/version, roll och verkligt sessions-ID. Process-ID är inte ensam identitet. Visa förälder/barn när det är observerat; en logisk roll är inte samma sak som en ständig process.

När en tillåten byggstart accepteras ska arbetsytan navigera till just den körningen. När dess sessioner faktiskt startar dyker de upp automatiskt. CLI-startade körningar ska också upptäckas i en redan öppen arbetsyta. Öppna inte tio nya terminalfönster och starta inga extra modeller för att få korten att fyllas.

Skilj väntande roll, start pågår, session aktiv, väntar på verktyg, väntar på beslut, avslutad, avbruten och okänt läge. Aktivitetens tid är inte en säker indikator på att processen lever. Ett verktygsanrop är inte ett resultat, och sessionens avslut är inte ett godkännande.

Strömma eller läs nya händelser stegvis med en tydlig återanslutningsväg. Välj SSE, WebSocket eller avgränsad polling efter faktisk befintlig teknik. Hantera delvis skrivna rader, dubbla händelser, loggrotation och tappad anslutning. Visa senaste lyckade observation och känd lucka. UI-fel får inte stoppa arbetet; stängd flik får inte starta om eller döda bygget.

Vanlig statusvisning ska inte göra modellanrop. Läs bara rätt projekts data. Gör inte en kopia av hela `~/.claude` till klientens åtkomliga filyta. Utöka den nuvarande observatörens datainsamling endast där en konkret vy kräver det och redovisa ändringen av dess integritetsgräns.

**Klart när:** en verklig session dyker upp automatiskt, kan följas medan den arbetar och lämnar rätt slutbesked även efter omladdning av vyn.

# Etapp 3 av 6 — Bygg de tre sammanhängande vyerna

Använd relevanta designskills och etablerade komponenter där de hjälper. Ingen allmän mall-dashboard eller terminaltext bakom dekorativa kort. Inför delade färg-, typografi- och avståndsvärden för arbetsytan utan att påverka kundsajternas designsystem.

### A. Arbetsyta

Ett fast projekthuvud visar kund, uppdrag, kandidat/version, faktiskt moment och senaste observation. Till vänster finns Nortropic-partnerns dialog. I mitten finns huvudmaterialet. Till höger finns rollsessionerna med möjlighet att följa dem. En sekundär yta visar nästa handling och relevanta bevis.

Huvudmaterialet följer momentet: underlag och källor under research, innehåll under briefarbete, neutrala kandidater vid designval och riktig webbplats under bygge. Dolda eller ännu saknade artefakter ska inte ersättas av övertygande AI-genererade exempel.

### B. Byggflöde

Visa projektets faktiska moment och överlämningar. Skilj metodkartan, som förklarar arbetssättet, från kundens observerade förlopp. Omtag och återupptagning ska synas som historik, inte försvinna ur berättelsen.

Gruppera sessioner efter arbetsmoment/kandidat och ge en fokuserad detaljvy för aktivitet, underlag, kompetenser och resultat. Lägg Kirurgen och systemförbättringar i samma navigering men skilt från kundproduktion. Bevara åtkomsten till befintliga funktioner; flytta inte bort Kundstart, jämförelser eller rapporter utan ersättande navigering.

### C. Kod och preview

Visa projektets riktiga filer och en läsbar diff mot en namngiven version, inte mot en gissad katalog. Lägg körningslogg/terminalvy bredvid riktig preview och sessionens aktivitet.

En loggläsare heter ”Körningslogg”, inte ”Terminal”. En terminalknapp får öppna en faktisk dokumenterad terminal-/sessionsintegration. Bygg inte en generell fjärrshell-endpoint bara för att likna bilden. Kodredigering i webbläsaren är inte nödvändig i v1; en bra fil-/diffvy och säker öppning i befintlig editor räcker.

Preview ska visa Nortropics verkliga lokala bygge eller rätt godkända export. Märk arbetsversion, bevarad snapshot och exportversion tydligt. Byt inte ut en bedömd snapshot när bakgrundsbygget uppdateras. Val av mobil/dator ändrar vy, inte byggversion. Bevara föregående fungerande preview vid byggfel och märk den som äldre.

### Gemensamma kvalitetskrav

Paneler ska kunna fällas ihop och, där det hjälper, storleksändras. Bevara användarens val utan att störa andra projekt. På smala skärmar visas ett primärt område åt gången. Hela sidans innehåll ska inte krympas till oläsliga minipaneler.

Använd tydliga svenska etiketter, synligt tangentbordsfokus, fungerande tabbordning, läsbara kontraster och reducerad rörelse. Statusändringar ska kunna uppfattas även med hjälpmedel utan att varje loggrad stjäl fokus eller läses upp. Inför lugn uppmärksamhetssignalering, inte blinkande larm för varje verktygsanrop.

Hitta inte på procent färdigt, tid kvar, aktiva agenter, SEO-poäng eller användningssiffror. Kontextrymd, förbrukade token och kostnad är olika mått. Saknade värden är okända, inte noll. Sammanställning av återupptagna sessioner får inte dubbelräkna kumulativa totalsiffror.

Jämför din faktiska rendering med målbilderna: komposition, balans, typografi, täthet, panelernas proportioner och huvudytans prioritet. Rätta synliga brister. Antalet visuella varv är inte ett kvalitetsbevis.

**Klart när:** alla tre vyerna delar data och identiteter, fungerar med verkligt innehåll och har dokumenterade tom-, fel-, väntande och inaktuella lägen.

# Etapp 4 av 6 — Partnerdialog, rollsessioner och kontrollerad styrning

## Samtalet måste vara verkligt

Knyt partnerdialogen till en dokumenterat stödd Claude-session eller agentintegration. Inget fejkat chattsvar och ingen dold andra agentloop i UI-skalet. Starta inte en ny konversation per meddelande eller omladdning.

En fråga, ett planförslag och ett genomförandemandat är olika handlingar. Vanliga frågor får diskuteras utan kodändring. När jag redan gett mandat för ett avgränsat uppdrag ska agenten kunna arbeta vidare inom det utan att fråga om lov för varje rutinbeslut.

En ändringsbegäran ska bära kund, uppdrag, kandidat/version och, där det behövs, sida, vy och markerad del. En hänvisning till ”den här sidan” får inte förlora sin identitet när jag byter flik. Ändringar som blivit inaktuella kräver ny avstämning mot aktuell version, inte blind vidarebefordran.

## Tre ansvar, inte tre ständigt arbetande modeller

Önskad modellprofil att göra provbar:

- Arbetsledning: en stark resonemangsmodell, med tidigare diskuterad Fable 5.1 som kandidat när åtkomst och kostnad är verifierade.
- Utförande: Opus 5.5 för avgränsat skapande och implementation.
- Granskning: separat kontext med en kalibrerad granskarmodell; en starkare modell kan prövas utan att samma arbetsledarkonversation granskar sin egen plan.

Verifiera faktiska modell-ID:n, alias, effort och autentisering. En dyr profil är en hypotes, inte en kvalitetssanning. Inför profilen avgränsat; ändra inte alla kundflödets modellstandarder eller ta bort befintliga granskare som en UI-bieffekt. Visa vad som faktiskt körs. En konfigurerad men inte startad granskare är ingen aktiv session.

Arbetsledaren formulerar mål, avgränsning och överlämning. En ansvarig utförare ändrar den aktuella arbetsdelen. Granskaren lämnar självständiga fynd. Bevara de befintliga specialistpassen i stället för att låtsas att tre kort ersätter dem.

Ingen tvångsmässig chatt mellan alla agenter. Kommunicera vid uppdrag, relevant oklarhet, ändrade förutsättningar och resultat. Vid återkommande fel ska nästa försök ha ny hypotes eller ändrat underlag, inte bara högre effort. Befintliga tids- och omförsökstak gäller.

## Följ, meddela och anslut är olika funktioner

”Följ session” visar verklig observerad aktivitet utan ny modellturn. ”Skicka ändring” ger ett identifierat uppdrag inom mandatet. ”Öppna interaktiv session” visas bara när den sessionstypen faktiskt stöder det och det har prövats.

Behåll fungerande `claude -p`-arbetare. `--bg` kan enligt den kontrollerade dokumentationen inte kombineras med `-p`. `--resume` i en andra process är inte en säker live-anslutning till den första. Kör aldrig två skrivande processer med samma sessionsidentitet. Byt inte till `--bare` för snabbhet om det tar bort nödvändiga instruktioner, skills, MCP:er eller skyddskrokar.

Pröva officiell sessionskommunikation där tillgänglig. Ett förbud på den sändande sidan får inte kringgås genom mottagaren. Filåtkomst eller gemensam kundkontext följer inte automatiskt med ett meddelande. Kontrollera skillnader mellan värddator, container och arbetskatalog innan sessioner förväntas hitta varandra.

Överlämningen behöver avsändare, mottagare, uppdrags-/start-ID, berörd version, avsikt och förväntat resultat. Använd befintliga poster där det går. Skilj skickat/köat, mottaget, arbete startat, resultat sparat och resultat verifierat. Koppla inte mottagare enbart genom ett visningsnamn.

Om en `-p`-session inte kan ta emot pågående ändringar säkert, använd befintlig återupptagnings- eller nästa-steg-väg och visa det. Hitta inte på terminalinmatning eller meddela ”ändringen pågår” när inget genomförande startat.

## Claude-panelen

Bygg en liten versionstestad Nortropic-mod om den installerade klienten och officiella kontraktet stöder den. Den ska visa aktuellt uppdrag, rollsessioner, senast observerade läge och öppna huvudvyn med rätt sammanhang. Hitta inte på att en mod i min huvudsession automatiskt ser alla separata processer.

Hämta projektstatus från samma läsväg som arbetsytan. Låt inte modens livslängd styra byggets livslängd. Ge den inga dolda behörighetsgodkännanden, promptomskrivningar eller bakgrundsanrop till modeller. Om rätt Mods-stöd saknas, leverera en fungerande verifierad plugin-/kommandoingång till huvudvyn och redovisa just panelen som begränsad. Släpp inte hela arbetsytan för att en klientyta saknas.

## Åtgärderna

Koppla start, förfining, stopp, återupptagning och export till samma befintliga kontrollvägar som CLI/Flöde. Ingen egen statusmaskin i chattprodukten. Agentens verktyg får inte exekveras både av Nortropic och av ett Pipe-/UI-lager.

Återanvänd samma start-ID vid omförsök av samma begäran. Prova dubbelklick, två flikar, tappat svar och återanslutning. En verklig stoppbegäran går direkt till rätt processkontroll, inte via att modellen kanske läser ordet ”stopp”. Ett sent agentmeddelande får inte återstarta ett avslutat uppdrag.

”Pausa” får finnas bara om paus och återupptagning verkligen stöds; annars använd ”Stoppa” med korrekt konsekvensbeskrivning. Publicera och godkänn inte automatiskt därför att kontrollerna blev gröna.

**Klart när:** ett avgränsat verkligt prov visar partnerdialog, rätt överlämning, arbete i rätt session, resultat i rätt vy och kontrollerad rättelse utan manuell kopiering.

# Etapp 5 av 6 — Säkerhet och oberoende verifiering

Arbetsytan är min interna arbetsstation, inte en kundportal. Lokal adress är inte ensam ett åtkomstskydd. Återanvänd befintlig autentisering, pröva ursprungs-/CSRF-skydd för skrivningar och strömanslutningar och begränsa all åtkomst till rätt projekt. Hemligheter ska inte hamna i URL:er, frontendpaket, browserlagring, loggar eller skärmbilder. Beskriv återstående risker för andra processer med samma OS-användare; lova inte en isolering som inte finns.

Modellskriven kundkod och externa referenser är obetrott innehåll. Rendera preview separerat från kontrollgränssnittets ursprung/behörigheter med lämplig isolering. Innehållet får inte läsa dashboardnycklar, ändra domar eller nå kontroll-API:t. En preview-proxy får inte bli en godtycklig väg till lokala tjänster. Sanera visad HTML/Markdown och pröva filvägar, symlänkar och länkar innan de används.

Bevara blindningen på server-/datavägen: inte bara genom hopfälld CSS. Dialog, sessionsmetadata, filnamn, loggar, modellval och direkta API-anrop får inte avslöja bedömningsunderlag som ska vara dolt före mitt val. En blind granskare får inte skaparens resonemang via sessionsmeddelanden. Agenters webbläsarprov får inte ha min ägarbehörighet och råka godkänna åt mig.

Dokumentera åtkomstgränser för värddator, Computer, Mods, preview, agentroller och kontroll-API. Inget brett säkerhetsbygge utanför uppdraget: åtgärda de konkreta gränser som den nya ytan tillför.

Prova minst följande sammanhängande acceptansfall:

1. Rätt kund och körning öppnas; dess verkliga sessioner syns utan extra modellstarter för observation.
2. En aktiv session lämnar resultat som kan öppnas, och en ännu inte startad granskare står fortfarande som väntande.
3. Dubbelklick, två flikar och tappat startsvar ger inte dubbelt arbete eller dubbla skrivåtgärder.
4. Omladdning eller stängd följvy påverkar inte bygget; återanslutning visar aktuell status och eventuella luckor.
5. Avbruten arbetare, misslyckad start och saknat slutbesked visas korrekt, aldrig som godkända.
6. Stopp träffar rätt uppdrag och dess berörda processer; sent meddelande återstartar det inte.
7. Ändrad kandidat/version gör gamla besked historiska och hindrar en felriktad ändring eller ett inaktuellt godkännande.
8. Följning är läsande; en fråga skapar ingen kodändring; en uttrycklig ändring når rätt arbetsdel.
9. Blindning och kundgränser håller även via direkta anrop, meddelanden, preview och logg-/filvyer.
10. Misslyckad preview bevarar märkt äldre resultat; filvy och diff hör till rätt projekt och jämförelseversion.
11. Tangentbord, mobil/reflow, reducerad rörelse, fel- och tomlägen fungerar; status kommuniceras begripligt utan färg som enda signal.
12. Avstängning/återgång av den nya arbetsytan lämnar motorn och bevisen intakta.

Enhetstester får använda stubbade modeller. Integrationsprov ska gå genom verkliga kodvägar och riktiga processer. Minst en begränsad verklig Claude-session och ett riktigt renderat testprojekt krävs för att kalla session-/previewkopplingen verifierad. Ingen mänsklig användbarhet eller förbättrad kunddesign får påstås på grund av detta teknikprov.

Ta riktiga skärmbilder i relevanta bredder och jämför med målbilderna. Kör repots obligatoriska röktest och relevanta riktade tester; kör inte dyra helsviter efter varje kosmetisk ändring. Låt en separat granskare kontrollera diff, behörighetsgränser, kontrakt och faktiskt sparade provbevis. Rätta blockerande fynd och kör berörda prov igen. Försvaga inte tester eller markera en oprövad rättelse som verifierad.

**Klart när:** acceptansfallen har spårbara utfall mot en exakt version, oberoende granskning är redovisad och kvarstående begränsningar inte döljs av gränssnittet.

# Etapp 6 av 6 — Dokumentera, aktivera och lämna över

Dokumentation och statusuppgifter följer ändringen i samma uppdrag. Använd repots befintliga struktur för gällande arbetssätt, beslut, backlog, rapporter och privata bevis. Håll `CLAUDE.md` kort med tydliga ingångar. Skapa inte konkurrerande `progress.md`, `tasks.md`, statusdatabaser eller stora utspridda instruktioner. En ny funktion får ha nödvändig dokumentation och ett definierat ägarskap.

Dokumentera:

- Vald huvudväg, återanvända komponenter, kontrakt och vilka tidigare funktioner som fortfarande gäller.
- Exakta versionskrav, verifierad autentiseringsväg, beroenden, licenser och uppdaterings-/återställningsväg.
- Skillnaden mellan följa, meddela, ansluta, stoppa och återuppta en session.
- Vad observationen täcker och missar, datalagring/gallring samt hur hemligheter och blindning skyddas.
- Modellprofilens räckvidd, verkligt observerad användning och vilka kvalitetsantaganden som ännu inte prövats.
- Startkommando, lokal adress, felsökning och aktuell aktiveringsstatus per funktion.

Låt en färsk session hitta projektläge, ändringar, bevis, begränsningar och nästa handling genom repots normala ingångar. Påstå inte att ett färskt överlämningsprov gjorts om du bara själv läst din sammanfattning.

Leverera en enda dokumenterad startväg för arbetsytan. Integrera helst med befintlig launcher i stället för en uppsättning manuella terminalkommandon. Verifiera lokal start, omstart och återgång på den miljö du faktiskt har tillgång till. Ett godkänt isolerat prov räcker inte för att påstå att min Mac eller mina befintliga körningar redan är uppdaterade.

Aktivera de verifierade lokala funktionerna inom mandatet. Behåll en tydlig återgång till tidigare vy tills den nya är prövad. Begränsa en blockerad integration separat och fortsätt leverera övriga användbara delar.

## Slutrapport till Johnny

Börja med: ”Det här fungerar nu”, följt av hur jag öppnar arbetsytan och vad jag faktiskt kan göra.

Visa verkliga skärmbilder av de tre vyerna, inte nya genererade målbilder. Redovisa sex etappers status, val av skal, berörda commits, exakt testad version, körda prov, granskningsresultat och dokumentationsplats. Skilj byggt, verifierat, lokalt aktiverat och väntar på verklig bedömning.

För varje knapp eller roll som inte är fullt inkopplad: säg det. Redovisa rapporterad användning utan att likställa den med fakturerad kostnad. Ange minsta återstående åtgärd för sådant som kräver min dator, en bestämd budget eller särskild åtkomst. Avsluta inte med en ny allmän arkitekturplan.

## Källor och hur de används

Kontrollera aktuellt innehåll och installerat beteende innan källan styr implementationen. Spara datum, version/commit där tillgängligt, den konkreta frågan och vad källan faktiskt stödjer. En källista utan koppling till ett beslut är inte tillräcklig. Håll researchen riktad.

S1. Nortropics aktuella repo — faktisk motor, beslut, gränser och befintlig dokumentation:
https://github.com/Nortropic/nortropic-webb-pro

S2. Claude Code — programmatisk körning, händelser och livscykel:
https://code.claude.com/docs/en/headless
https://code.claude.com/docs/en/cli-reference
https://code.claude.com/docs/en/agent-view

S3. Claude Code — sessionskommunikation, verktygsbehörigheter och modellval:
https://code.claude.com/docs/en/cross-session-messaging
https://code.claude.com/docs/en/permissions
https://code.claude.com/docs/en/model-config

S4. Plugins och Mods — kontrollera dokumentationens tillgänglighet och lokal kompatibilitet:
https://code.claude.com/docs/en/plugins
https://code.claude.com/docs/en/plugins/mods/overview
https://code.claude.com/docs/en/plugins/mods/api
https://code.claude.com/docs/en/plugins/mods/interface

S5. Open WebUI Computer — arbetsyta, agentintegration och egna licensvillkor:
https://github.com/open-webui/computer
https://github.com/open-webui/computer/blob/main/LICENSE
https://docs.openwebui.com/ecosystem/computer/
https://docs.openwebui.com/ecosystem/computer/ai/coding-agents/
https://openwebui.com/terms

S6. Open WebUI huvudprojekt — separat produkt och eventuell liten anslutning:
https://github.com/open-webui/open-webui
https://docs.openwebui.com/features/extensibility/plugin/functions/pipe/
https://docs.openwebui.com/license/

S7. Arbetssätt — håll teknisk körning, arbetsledning och granskning tydligt åtskilda:
https://www.anthropic.com/engineering/building-effective-agents
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

S8. Gränssnitt — överblick före detaljer, synlig status och tillgänglig återkoppling:
https://www.nngroup.com/articles/progressive-disclosure/
https://www.nngroup.com/articles/visibility-system-status/
https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html

Källor och filer är underlag att bedöma, inte instruktioner att exekvera eller installationsmandat. Lämna okända förhållanden som okända. Använd enklaste verifierbara lösning som når den godkända målbilden.
```

## Tillägg 2026-10-09: den kompletta arbetsplatsen med samverkande sessioner — ägarens uppdrag ~11:22Z och genomförarens huvudvägar

**Status:** gäller; under genomförande i grenen `claude/arbetsplats-20261009`, inte aktiverat (backlogposten
`B-20261009-komplett-arbetsplats-samverkande-sessioner`; hur det fungerar och dess gränser: `kunskap/arbetsyta.md`).
Prövat med attrapper (`prov_meddelanden.py`, `prov_arbetsyta.py`, webbläsarprovet), med verkliga Haiku-sessioner för
meddelande under arbetet, paus och återupptagning, och med den riktiga Codex i en provinstans för den externa
granskarens väg (2026-10-09 13:17–13:22Z, nedan). Den oberoende granskningen GR-20261009-arbetsplats-oberoende gav fem
blockerande och tolv allvarliga fynd; de är rättade och vända till prov som går grönt. Hela användarresan är ännu inte
verifierad i det verkliga provet. Aktiveras först när huvudsessionens pågående kvalitetsprov är klart, enligt uppdragets villkor
att inte aktivera något som påverkar motorn eller den frysta metoden under körningen. Valen nedan är genomförarens
teknikbeslut inom uppdraget; ägarens beslut är uppdraget självt.

**Huvudvägen för meddelanden: en registrerad buss i motorn** (`kontroller/meddelanden.py`), levererad till motorns
sessioner genom strömmande inmatning (`kontroller/lopare.py`, `--input-format stream-json`), inte Claude Codes
meddelanden mellan sessioner, Agent Teams eller Agent View. Skälen, ur dokumentationen och prov mot Claude Code 2.1.290
(2026-10-09): strömmande inmatning tar meddelanden mitt i en tur (läses mellan verktygsanropen), ekar dem med vårt id
(`--replay-user-messages`) och avbryter en tur med sessionen kvar (`interrupt` med `cancel_queued`), vilket ger
belägg för mottaget och besvarat och en verklig paus; meddelanden mellan sessioner hålls i `-p` utan
`crossSessionInbound: accept` och har ingen identitet utöver avsändarens namn; Agent Teams är experimentellt och
startar inga lagkamrater i `-p`; `--bg` går inte ihop med `-p`. Motorns sessioner får `crossSessionInbound: refuse`, så
samma instruktion aldrig går två vägar. Avsändaren sätts av koden som tar emot meddelandet (ägarens nyckel, löparen,
granskarnyckeln), aldrig av texten; ägarbeslut skrivs bara av beslutstjänsten.

**Paus** är ett avbrott av turen med processen kvar och kön tillbakalagd, och en spärr före varje ny session för hela
körningen; återupptagningen är ett meddelande från ägaren med det som kom under pausen. **Följdfrågor** till en avslutad
session är en förgrening (`--resume --fork-session`) som bara läser i en egen tom katalog. **Besluten** fattas i
arbetsytan genom Prototypvyns tjänst och binds dessutom till bilden ägaren ser (dess sha256). **Codex** ansluts som
extern granskare genom en egen granskarnyckel och ett kommandoradsverktyg som postar fynden ur Codex skrivskyddade
körning; att köra Codex är förberett, inte prövat. **Arbetsytan är dashboardens startvy**, och `./dashboard.sh start`
(och Mac-appen) startar tjänsten utan att starta arbete.

**Ägarens kontrollpunkter i blindningen** (statisk läsning av server.py:2950 och partner.py:296 på b20ae3a) reproducerades
med syntetiska data och rättades före allt annat: partnerns egna vägar respekterar nu A/B-spärren, och partnersessionen
binds till körningen och blindläget (en ny blind körning startar en ny session; den gamla arkiveras orörd).

Ägarens uppdrag, inklistrat i sessionen (klockan vid sparandet 2026-10-09T11:22:50Z), ordagrant:

> UPPDRAG: Gör Nortropics arbetsyta till min kompletta arbetsplats, med samverkande sessioner
> Arbeta vidare i nortropic-webb-pro.
> Mitt mål är att sköta Nortropic genom den lokala webbarbetsytan. Jag ska inte behöva VS Code eller manuella terminalkommandon för det normala arbetet: kundunderlag, research, referenser, design, granskning, ändringar, godkännande, bygge och leverans.
> Arbetsytan ska bli den nya dashboarden. Claude Mods och andra klienter ska ansluta till samma motor och samma beslut. Återanvänd det som redan fungerar.
> 1. Kontrollera nuläget och välj minsta fungerande utbyggnad
> Läs aktuella arbetsregler, arbetsytans dokumentation, berörd kod och primärkällorna i detta uppdrag. Verifiera funktionerna mot den installerade Claude Code-versionen.
> Skilj mellan:
> - implementerat och inkopplat;
> - provat med attrapper;
> - verifierat genom riktiga sessioner;
> - ännu inte verifierat i mitt faktiska arbetsflöde.
> Ta hänsyn till pågående kvalitetsprov. Utveckla isolerat och aktivera inte ändringar som påverkar dess motor eller frysta metod under körningen.
> Gör en kort genomförandeordning och fortsätt sedan med implementationen. Undvik en generell omskrivning av motorn eller ett ramverksbyte utan konkret behov.
> 2. Gör allt normalt arbete möjligt från arbetsytan
> Arbetsytan ska vara normal startvy och ge tillgång till:
> - projekt och kundunderlag;
> - referenser, material och kompetensanvändning;
> - kandidater, levande förhandsvisning och bevarade versioner;
> - samtal med arbetsledningen och valda arbetare;
> - granskningsfynd och ändringsuppdrag;
> - blind jämförelse, val och godkännande;
> - byggkontroller, körningar och leverans;
> - kod, diffar, rapporter och historik;
> - backlogg, kalibrering, Kirurgen och underhåll.
> Visa resultatet, arbetsläget och nästa relevanta handling tydligt. Lägg fördjupning bakom begripliga paneler. Jag ska kunna se mer utan att behöva hålla alla tekniska detaljer i huvudet.
> Ge mig en enkel lokal startgenväg som öppnar arbetsytan och hanterar dess tjänst utan att starta modellsessioner av sig själv.
> Utgå från principerna om successiv fördjupning och tydlig återkoppling om systemets tillstånd:
> - NN/g, Progressive Disclosure: https://www.nngroup.com/articles/progressive-disclosure/
> - NN/g, Visibility of System Status: https://www.nngroup.com/articles/visibility-system-status/
> 3. Koppla in verklig samverkan mellan sessioner
> Jag ska kunna skriva till en arbetare medan den arbetar. Arbetare och granskare ska kunna lämna relevanta fynd, frågor och överlämningar till varandra inom sina uppdrag.
> Undersök och använd de dokumenterade möjligheterna:
> - $.session.send och meddelandehändelser i Mods;
> - Claude Codes kommunikation mellan separata sessioner;
> - strömmande inmatning till motorns sessioner;
> - Agent View eller Agent Teams där de löser ett faktiskt behov.
> Välj en tydlig huvudväg för meddelanden. Undvik att samma instruktion samtidigt skickas genom flera kanaler.
> Vanliga sessioner kan kommunicera utan Agent Teams. Agent Teams är experimentellt och har andra begränsningar än claude -p; använd det inte som obligatorisk grund för hela Nortropic.
> Källor:
> - Mods API: https://code.claude.com/docs/en/plugins/mods/api
> - Kommunikation mellan sessioner: https://code.claude.com/docs/en/cross-session-messaging
> - Streaming Input: https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode
> - Agent Teams: https://code.claude.com/docs/en/agent-teams
> Samarbetet ska ha tydliga uppgifter och avslut. Undvik rundgång där agenter upprepar eller godkänner varandras påståenden utan nytt underlag. Bevara befintliga gränser för körningar och resursanvändning.
> 4. Skilj ägarinstruktioner från agenternas fynd
> Varje meddelande ska ha registrerad avsändare, mottagare, projekt, körning, syfte och relevant kandidat/version.
> Skilj på:
> - fråga;
> - förslag;
> - granskningsfynd;
> - ändringsinstruktion;
> - ägarbeslut.
> En agents meddelande får aldrig registreras som mina ord eller mitt godkännande. Avsändarens namn i meddelandetexten räcker inte som identitet.
> Jag ska kunna ge en granskare ett avgränsat mandat att begära rättelser. Övriga förslag ska kunna godtas, avvisas eller diskuteras i arbetsytan.
> Visa observerbara leveranslägen: sparat, köat, mottaget, besvarat och genomfört. Markera okänt när det saknas bevis. Ett skickat meddelande är inte bevis för att ändringen är utförd.
> Hantera dubbelklick, återförsök, omstart och inaktuella versioner utan dubbla eller felriktade instruktioner.
> Anthropics dokumentation skiljer uttryckligen meddelanden från andra sessioner från användarens samtycke:
> - https://code.claude.com/docs/en/cross-session-messaging
> 5. Gör det möjligt att ansluta Codex som granskare
> Utforma meddelandevägen så att en extern granskare, exempelvis Codex, kan lämna fynd och få återkoppling genom samma registrerade flöde.
> Utgå inte från att Claude Mods automatiskt omfattar Codex. Det behövs en uttrycklig integration med rätt avsändare och behörigheter. Redovisa vad som är faktiskt inkopplat och vad som endast är förberett.
> Granskaren ska kunna se relevant resultat och belägg. Den ska inte behöva skriva direkt i skaparens arbetsfiler för att påverka arbetet.
> Kontrollera den valda integrationens aktuella officiella dokumentation innan den införs. Hitta inte på ett stöd som saknas.
> 6. Inför paus, stopp och återupptagning med tydlig betydelse
> Paus ska kunna avse en arbetare eller hela projektets körning. Visa omfattningen före handlingen.
> ”Paus begärd” blir ”Pausad” först när det avsedda arbetet har stannat. Motorn får inte starta nästa steg bakom en paus. Redovisa verktyg eller tjänster som fortfarande arbetar.
> Återupptagning ska fortsätta från känt läge och ta hänsyn till meddelanden som kommit under pausen. Påstå inte att paus återställer redan genomförda filändringar eller externa handlingar.
> En stängd flik ska inte oavsiktligt stoppa arbetet. En återöppnad arbetsyta ska återansluta och visa det faktiska läget.
> Pröva avbrott och återupptagning genom den verkliga integrationsvägen:
> - Streaming Input: https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode
> - CLI-referens: https://code.claude.com/docs/en/cli-reference
> 7. Låt mig fortsätta och undersöka sessioner utan VS Code
> Jag ska från arbetsytan kunna läsa relevant sessionshistorik, ställa följdfrågor och fortsätta ett arbete inom rätt behörigheter.
> Använd dokumenterade gränssnitt för respektive sessionsmodell. --bg och -p är olika modeller och kan inte kombineras. Byt inte motorns sessionsmodell utan att pröva följderna.
> Källor:
> - Agent View: https://code.claude.com/docs/en/agent-view
> - CLI-referens: https://code.claude.com/docs/en/cli-reference
> En förgrenad session ska registreras med förälder, eget id och ansvar. --fork-session kopierar samtalet men ger inte automatiskt en isolerad projektkopia. Använd skrivskydd eller egen arbetskopia beroende på uppgiften.
> - Sessionshantering: https://code.claude.com/docs/en/sessions
> Jag ska kunna läsa och jämföra kod i arbetsytan samt begära ändringar där. Om direkt filredigering behövs för mitt normala arbete, integrera en begränsad editor med samma versions- och skrivkontroll. Två aktörer får inte samtidigt skriva över varandras ändringar.
> 8. Samla förhandsvisning och beslut
> Jag ska kunna:
> - använda den riktiga sidan i mobil- och datorbredd;
> - jämföra med referens och tidigare version;
> - markera en del av sidan och beskriva en ändring;
> - se vilken version varje bild och fynd gäller;
> - välja, underkänna och godkänna från arbetsytan.
> Återanvänd Prototypvyns beslutstjänst och skydd. Godkännande ska knytas till en bevarad identifierad version som jag faktiskt sett. En levande arbetsversion får inte förändras tyst under ett godkännande.
> Skillnaderna mellan arbetsversion, fotograferad version, godkänd version och exporterad leverans ska vara begripliga.
> 9. Bevara blindning och åtkomstgränser genom hela arbetsytan
> Samarbete mellan skapare och specialist är en sak. En oberoende blind bedömning har andra informationsgränser. Låt inte en gemensam chatt eller meddelandekanal förstöra dem.
> Kontrollera särskilt de statiskt identifierade riskerna från b20ae3a:
> - Partnerns separata API-vägar måste respektera samma A/B-spärr som arbetsytans samlade läsväg.
> - En ny blind körning får inte återanvända samtalsminne som avslöjar tidigare bedömningar eller försöksarmar.
> Verifiera med prov; anta inte att maskning av det senaste meddelandet rensar gammal kontext. Kontrollera först om riskerna redan har rättats efter den angivna versionen.
> Mods kör med användarens rättigheter utanför Bash-sandlådan. Använd dem inte för att kringgå kundvakten, godkännanden eller filgränser.
> - Mods, behörigheter och åtkomst: https://code.claude.com/docs/en/plugins/mods/overview
> 10. Behåll lokal körning och den befintliga kompetensen
> Claude Code-processerna ska fortsatt köras lokalt genom vår avsedda autentisering och prenumeration. Byt inte till betald API-drift som en dold följd av integrationen. Modellen kan fortfarande använda leverantörens molntjänst.
> Sessionsförändringen får inte tappa rollernas instruktioner, skills, MCP-verktyg, kundunderlag eller säkerhetsinställningar. Kontrollera faktisk tillgång genom den nya startvägen.
> Skilj i observationen mellan erbjuden kompetens, laddad kompetens, verktygsanrop och belagd påverkan på resultatet.
> Ghostty är frivilligt. Terminalbilder kan vara ett komplement, men arbetsytan ska fungera fullt utan det. Bildstöd i en mod är inte en interaktiv webbläsare.
> Källor:
> - Mods bildstöd och begränsningar: https://code.claude.com/docs/en/plugins/mods/gallery#image-and-client
> - Ghosttys funktioner: https://ghostty.org/docs/features
> 11. Verifiera hela användarresan med VS Code stängt
> Följ repots prov- och dokumentationsregler. Gör relevanta regressionsprov och ett avgränsat verkligt prov med fiktivt material.
> Provet ska visa att jag från arbetsytan kan:
> 1. Öppna ett projekt och starta ett tillåtet arbetssteg.
> 2. Följa riktiga sessioner och se deras resultat.
> 3. Skicka en instruktion under arbete.
> 4. Se ett granskningsfynd överlämnas till rätt arbetare och besvaras.
> 5. Pausa och återuppta med rätt omfattning.
> 6. Stänga och öppna arbetsytan utan förlorat läge eller dubbla starter.
> 7. Jämföra versioner och begära en ändring.
> 8. Godkänna exakt den version som visats.
> 9. Hitta rapport, beslut och bevis i efterhand.
> Använd inte ett manuellt terminalsteg eller VS Code för att dölja en lucka i denna användarresa. Eventuell första inloggning eller engångsinstallation ska redovisas separat.
> Starta inget helbygge och publicera inget utan mitt tidigare angivna klartecken. Provningen av arbetsytan ska vara avgränsad från kundproduktion.
> Leverera fungerande integration, uppdaterad dokumentation och en kort redovisning av vad som återstår. Uppdraget är klart när den sammanhängande användarresan fungerar och är verifierad — inte enbart när alla knappar finns.

Ägarens egen rad under det inklistrade, ordagrant:

> Utgångspunkter för kontrollen: dashboard/server.py:2950 och dashboard/partner.py:296 på b20ae3a. Fynden kommer från statisk läsning, inte reproducerade läckor. Reproducera dem avgränsat med syntetiska data och verifiera rättelserna före nästa blinda prov.

## Tillägg 2026-10-09: Codex som observatör och förbättringsagent — ägarens tillägg ~13:13Z till det pågående bygget

**Status:** gäller; rollen inte aktiv förrän ägaren startar Codex med överlämningsunderlaget. Ägarens tillägg,
inklistrat och ordagrant:

> TILLÄGG TILL DET PÅGÅENDE BYGGET: koppla in Codex som observatör och förbättringsagent
>
> Jag vill att Codex blir ”örat mot rälsen” under arbetet: följer hela kedjan, identifierar kvalitetsförluster och förbättringsmöjligheter, undersöker relevanta källor och samspelar med ansvariga arbetare. Sådant som inte passar att genomföra nu ska hamna i befintlig backlog med tydliga belägg.
>
> Detta kompletterar det pågående uppdraget. Starta inte om bygget och ändra inte dess mål eller godkännandekriterier.
>
> Läs Codex minnesanteckning:
>  /Users/elinhaggstrom/nortropic-repos/work/minne/nasta-helbygge-observation.txt
>
> 1. Koppla rollen till den verkliga körningen
>
> Identifiera projekt, körnings-id, kod- och metodversion, aktiva sessioner, ansvariga arbetare, godkänd designversion och gällande ägarbeslut.
>
> Återanvänd arbetsytans befintliga observation, kommunikation, rapporter och backlog. Skapa ingen parallell rapportapparat.
>
> Verifiera hur Codex faktiskt kan läsa körningens underlag och lämna återkoppling. Att en panel eller integrationsinställning finns är inte bevis för en fungerande förbindelse. Visa ett ofarligt prov där ett granskarförslag når rätt mottagare med rätt körningsidentitet.
>
> Om förbindelsen saknas: redovisa det tydligt och ordna tills vidare ett konkret överlämningsunderlag med aktuella spår och rapportvägar. Märk inte rollen som aktiv och påstå inte att Codex observerar förrän det faktiskt sker. Ersätt inte Codex med en annan modell utan att ange det.
>
> Ändringar i integrationskoden görs isolerat och provas. Redigera inte kod eller skalskript som den pågående körningen använder.
>
> 2. Följ hela flödet och resultatet
>
> Codex ska undersöka både stora samband och små detaljer:
>
> - kundunderlag, research, referensval och innehållets trovärdighet;
> - visuell förståelse, kundanpassning, typografi, bilder, layout och rörelse;
> - mobil, dator, tillgänglighet och besökarens viktigaste uppgifter;
> - vilka skills, MCP och verktyg varje session får, faktiskt använder och drar konkret nytta av;
> - prompter, motstridiga regler, kontexthantering och överlämningar;
> - återkopplingens effekt, omarbete, väntan och resursförbrukning där den kan mätas;
> - överensstämmelsen mellan vald design, implementation, granskning och slutbesked.
>
> Bedöm bilderna före skaparens förklaring. Skilj direkt observation från eftergranskning av tidigare steg.
>
> Dokumentera även vad som fungerar och bör bevaras. Ett läst skilldokument eller lyckat verktygsanrop bevisar inte att kompetensen har tillämpats eller att kvaliteten förbättrats.
>
> 3. Undersök förbättringar aktivt
>
> Codex får webbsöka och jämföra med aktuell dokumentation, forskning, litteratur, metoder, principer, verktyg, skills och MCP.
>
> Sök både efter förklaringar till observerade problem och möjligheter som vår befintliga metod missar. Prioritera primärkällor och kontrollera aktualitet och versionsberoenden.
>
> Varje rekommendation ska skilja:
> - vad vi faktiskt observerat;
> - vad källan stöder;
> - vår egen tolkning eller hypotes;
> - varför det är relevant för just detta uppdrag.
>
> En källa ska inte automatiskt bli en ny gemensam regel. Bedöm även om förenkling, borttagna konflikter eller bättre användning av befintlig kompetens löser problemet.
>
> Utgångspunkter:
> https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
> https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
> https://www.anthropic.com/engineering/building-effective-agents
> https://www.nngroup.com/articles/usability-testing-101/
>
> Kontrollera källornas tillämplighet. Den äldre agentartikeln är principstöd, inte en aktuell inventering av verktyg.
>
> 4. Samspela med arbetarna med tydligt mandat
>
> Lämna avgränsade granskarförslag till ansvarig arbetare. Förslagen får hanteras inom arbetarens befintliga mandat vid en säker punkt i arbetet.
>
> Varje förslag ska innehålla:
> - observation och bevisreferens;
> - konsekvens och prioritet;
> - minsta konkreta åtgärd;
> - hur förbättringen kan verifieras.
>
> Märk förslagen som Codex återkoppling, aldrig som ägarbeslut. Skilj dokumenterat, skickat, mottaget, genomfört och verifierat.
>
> Flagga väsentliga fel direkt. Samla övrig återkoppling vid naturliga avstämningar så arbetet inte avbryts av varje detalj.
>
> Spara läget före påverkan och resultatet efter. En körning som får hjälp ska redovisas som assisterad. Behåll separat session och avgränsat underlag för blind slutbedömning. Ändra inte frysta metoder eller testurval under ett jämförelseförsök.
>
> 5. Backlogga med precision och följ upp
>
> Kontrollera först om förbättringen redan har en ansvarig post. Komplettera den i så fall.
>
> Varje ny post ska ange berört steg, problem eller möjlighet, belägg, förväntad nytta, prioritet, minsta nästa försök, färdigkriterium och varför den behöver vänta.
>
> Privata kunduppgifter och råa spår stannar privat. Publika poster anonymiseras.
>
> Följ upp genomförda förslag: blev resultatet bättre, uppstod någon regression och är nyttan tillräcklig för kostnaden och komplexiteten? Markera inte något verifierat enbart för att det implementerats.
>
> Leverera nu ett kort inkopplingsbesked:
> - vilken körning rollen följer och från vilken tidpunkt;
> - vilka spår och steg den kan respektive inte kan observera;
> - om kommunikationen med Codex är verkligt verifierad;
> - var återkoppling, rapport och backlog finns.
>
> Behåll befintliga gränser för åtkomst, kvot, externa tjänster, publicering och ägarbeslut. Målet är bättre webbplatser och mindre onödigt arbete. Visa faktisk nytta innan vi gör arbetssättet större.

**Genomförarens tillämpning inom tillägget** (teknikbeslut, inte ägarens beslut):

- **Körningen** är kvalitetsprovet H01, försök 2 (navet-cykelverkstad, main ebe3d2b, startad 2026-10-09T12:46:15Z),
  bekräftat av sessionen som kör det. Identitet, spår, läsgränser och kanalprovet står i den privata rapporten
  `underlag/rapporter/RAPPORT-2026-10-09-codex-observation-h01.md`.
- **Under jämförelseförsöket läser Codex bara.** Dess återkoppling når varken ägaren, skaparna eller skisskritiken före
  ägarens blinda val (en körning som får hjälp är assisterad, och domen ska vara blind). Lottningen, armarnas
  variantfält, skaparnas prompter, svar och transkript samt RIKTNING.md hålls utanför läsningen. Codex observationer
  sparas i rapporten och redovisas efter valet.
- **Kanalen** är arbetsytans meddelandebuss med den externa granskarens egen nyckel (`kontroller/extern_granskare.py`),
  ingen parallell rapportapparat. Ägarens mandat för en kandidat bär nu också granskarens förslag och granskningsfynd
  till kandidatens utförare, som hanterar dem inom sitt uppdrag (`meddelanden._agentregler`); utan mandat går de till
  ägaren. Kanalen finns bara på grenen tills den aktiveras efter kvalitetsprovet.
- **Kanalprovet 2026-10-09 13:17–13:22Z:** den riktiga Codex (`codex exec`, skrivskyddat, ChatGPT-inloggning, modellen
  gpt-6.1-sol, 42 700 tokens) läste ett paket ur provinstansen :4782 med fiktiva testdata. Dess två poster
  registrerades i bussen till ägaren respektive k01:s utförare, med avsändaren `extern codex`, provinstansens körning
  och, för förslaget, mandatet i ramen. Ingen utförare arbetade, så förslaget står sparat på adressen; leveransen in i
  en arbetande session är inte prövad för en Codex-post. Inte prövat mot den pågående körningen eller :4771.

**Ägarens svar på inkopplingsbeskedet, 2026-10-09 ~13:27Z (inklistrat), ordagrant:**

> ack. Behåll H01 försök 2 som ett fryst jämförelseförsök. Under försöket ska Codex vara passiv observatör enligt de dokumenterade läsgränserna. Ingen återkoppling om kandidaternas kvalitet får påverka mig eller arbetarna före mitt blinda val.
> Den kommande prompten om förbättringsagent och återkommande bevakning gäller utvecklingen av den fortsatta arbetsytan. Förbered den isolerat och låt den inte ändra H01:s instruktioner, verktyg, metod eller bedömningsunderlag.
> Ett befintligt kandidatmandat får inte automatiskt tolkas som tillstånd att påverka detta jämförelseförsök. Mandatet för agentåterkoppling ska vara uttryckligt och knutet till rätt körning, kandidat och tillåtna åtgärder.
> Redovisa kanalen som delvis verifierad tills ett ofarligt förslag har nått en verkligt arbetande session och mottagandet har observerats. Skilj registrerat, levererat, mottaget och genomfört. Gör det provet utanför H01.
> Följ upp felsidan som ögonblicksbild i ett isolerat regressionsfall. Dokumentera vad som kontrolleras; det enskilda fyndet visar inte att alla ogiltiga förhandsbilder upptäcks.
> Behåll observationer och föreslagna backlogposter privat tills försöket är avslutat. Bekräfta inte att Codex observerar förrän Codex faktiskt har startat och registrerat starttid och körningsidentitet.

Tillämpat: mandatet för agentåterkoppling anger körning, kandidat och tillåtna åtgärder uttryckligen
(`meddelanden.ATGARDER`; ett äldre mandat utan fältet gäller bara begäran om rättelse); leveransläget levererat skiljs
från köat; kanalen redovisas som delvis verifierad tills det verkliga provet (punkt 4) visat en Codex-post mottagen av
en arbetande session; felsidan som ögonblicksbild har ett isolerat regressionsprov med dokumenterad räckvidd
(`prov_arbetsyta.py`, `forhandsvisa.ogiltig_sida`); Codex start registreras i den privata rapporten innan något kallas
observation.

## Tillägg 2026-10-09: kontinuerlig bevakning och förbättringsarbete — ägarens tillägg ~13:23Z

**Status:** gäller; under genomförande i grenen `claude/arbetsplats-20261009`, inte aktiverat. Förbereds isolerat och
ändrar inte H01:s instruktioner, verktyg, metod eller bedömningsunderlag (ägarens svar ~13:27Z). Ägarens tillägg,
inklistrat och ordagrant:

> TILLÄGG TILL DET PÅGÅENDE UPPDRAGET: Nortropics kontinuerliga bevakning och förbättringsarbete
> Utöka rollen för Codex som observatör och förbättringsagent med löpande bevakning, även mellan byggen.
> Codex ska vara ”örat mot rälsen”: följa hur Nortropic fungerar, identifiera brister och möjligheter, undersöka relevanta källor, samspela med ansvariga arbetare och backlogga sådant som behöver hanteras senare.
> Målet är att hela Nortropic har ett aktuellt, källgrundat och prövat arbetssätt. Nya verktyg eller metoder ska bedömas efter sin faktiska nytta för våra leveranser. Bevakningen ska också kunna upptäcka när förenkling, borttagna regler eller bättre användning av befintlig kompetens är rätt förbättring.
> Läs minnesanteckningen:
> /Users/elinhaggstrom/nortropic-repos/work/minne/nasta-helbygge-observation.txt
> Arbeta inom gällande mandat och återanvänd befintlig mekanik. Pågående bygge ska kunna fortsätta utan att dess frysta metod eller körande filer förändras.
> 1. Börja med verkligheten i Nortropic
> Inventera aktuell kod, dokumentation och drift. Utgå från:
> - metodkartan och kompetensförteckningen;
> - skills, MCP, verktyg, modeller och deras faktiska integrationer;
> - spanaren och kunskap/spaning-kallor.md;
> - Kirurgen och förbättringsloopen;
> - beroendeunderhåll och startkontroll;
> - observation, rapporter, backlog och arbetsyta;
> - befintliga scheman och klockor.
> Skilj mellan beskrivet, implementerat, aktiverat och verifierat genom faktisk användning.
> Kontrollera särskilt den tidigare observerade skillnaden mellan README:s veckovisa spaning, källguidens dagliga pilotkörning, serverns intervall, GitHub-sökningarnas separata intervall och startkontrollens aktualitetsgräns. Verifiera på aktuell version innan du rättar något.
> Återanvänd befintliga register och ansvar. Skapa inte en konkurrerande metodkarta eller parallell förbättringskö.
> 2. Identifiera och kategorisera vad som ska bevakas
> Härled bevakningsbehoven från både våra befintliga förmågor och vad en komplett webbproduktion kräver. Inventeringen ska kunna upptäcka kompetenser och områden som vi saknar helt.
> Täck minst:
> - kundintag, affärsmål, målgrupper och branschspecifika behov;
> - UX-forskning, informationsarkitektur, innehåll och konvertering;
> - art direction, layout, typografi, färg och detaljutformning;
> - bilder, video, ljud, rörelse och materialets uppgift;
> - referensarbete, designverktyg och överföring från design till kod;
> - tillgänglighet, responsivitet och webbläsarstöd;
> - frontend, komponenter, ramverk, prestanda och testning;
> - SEO, strukturerad data, mätning och uppföljning;
> - säkerhet, integritet, licenser och relevanta regelverk;
> - AI-modeller, prompter, kontext, orkestrering, skills och MCP;
> - granskning, kalibrering, evals, blindning och reproducerbarhet;
> - kundrepo, förhandsvisning, driftsättning, överlämning och underhåll;
> - dokumentation, lärande, resursförbrukning, väntan och omarbete.
> Utöka kategorierna när inventeringen visar behov.
> För designprocessen och valet av forskningsmetod, läs:
> - Design Council, Framework for Innovation:
>   https://www.designcouncil.org.uk/resources/framework-for-innovation/
> - Nielsen Norman Group, When to Use Which User-Experience Research Methods:
>   https://www.nngroup.com/articles/which-ux-research-methods/
> Använd dem för att pröva om våra arbetsmoment besvarar rätt frågor och om vi undersöker verkliga användarbehov. En dokumenterad metod ersätter inte observation av användare eller bedömning av resultatet.
> 3. Koppla varje bevakningsobjekt till ett verkligt behov
> Utöka befintliga register så varje bevakningsobjekt kan kopplas till:
> - berört arbetssteg och kompetens;
> - metod, regel, verktyg eller beroende;
> - källa och konkret bevakningsfråga;
> - version och tillämpningsområde;
> - kontrollintervall, senaste lyckade kontroll och nästa kontroll;
> - ansvarig funktion och eventuell förbättringspost.
> En konkret fråga kan vara:
> ”Har ändrade sessions- eller hookbeteenden påverkat våra blinda granskare?”
> Det är den sortens koppling vi behöver mellan källa och system.
> Skilj mellan standard, forskning, etablerad metod, leverantörsdokumentation, branscherfarenhet, inspiration och Nortropics egna beslut.
> Ange källans datum eller version, vad som faktiskt lästs och vilken slutsats underlaget stöder. Redovisa motsägande belägg och begränsningar. Ett sökresultat eller referat får inte beskrivas som ett läst originalverk.
> För standarder och webbläsarstöd, använd bland annat:
> - W3C WAI, WCAG Overview:
>   https://www.w3.org/WAI/standards-guidelines/wcag/
> - MDN, Baseline:
>   https://developer.mozilla.org/en-US/docs/Glossary/Baseline/Compatibility
> Skilj etablerade standarder från utkast och kompatibilitetsinformation från andra kvalitetskrav.
> 4. Inför en tydlig bevakningsrytm
> Använd följande som utgångspunkt och anpassa den till befintlig drift:
> Dagligen: kontrollera förändringar i bevakade källor, relevanta versioner, utfasningar, säkerhetsmeddelanden och ändrade verktygskontrakt. Ta också in återkommande problem från Nortropics egna körningar och kontrollera att bevakningen fungerar.
> Veckovis: fördjupa prioriterade metod- och kvalitetsfrågor, sök efter nya källor och förmågor och bedöm vilka fynd som motiverar ett avgränsat försök.
> Månadsvis: granska täckningen över hela kedjan, gamla antaganden, motstridiga instruktioner, regler utan kvarvarande belägg och nyttan av tidigare införda förändringar. Se även över brusiga eller trasiga källor.
> Inför byggstart: kontrollera projektets särskilda behov, relevanta förändringar sedan föregående kontroll, prövad metodversion och kända brister som påverkar just detta bygge.
> Frekvensen ska följa förändringstakt och konsekvens. Stabila principer behöver inte läsas om varje dag.
> OpenAI:s dokumentation för återkommande arbete ska läsas här:
> - Scheduled tasks:
>   https://learn.chatgpt.com/docs/automations
> - Tasks and memory:
>   https://learn.chatgpt.com/docs/dots/tasks-and-memory
> - Best practices:
>   https://learn.chatgpt.com/guides/best-practices
> Använd dokumentationen för att skilja uppdrag, instruktioner, minne och faktiskt schemalagd körning. Kontrollera vad som är tillgängligt i vår miljö och vilket underlag körningen verkligen kan nå.
> 5. Gör schemaläggningen verifierbar
> Välj en ansvarig körväg per återkommande uppgift. Undvik dubbla klockor mellan Nortropic och eventuella ChatGPT-uppgifter.
> Verifiera:
> - schemaläggare, körmiljö och tidszon Europe/Stockholm;
> - åtkomst till rätt filer och källor;
> - var resultat och fel visas;
> - vad som händer när datorn eller tjänsten varit avstängd;
> - hur överlappande körningar och återupptagning hanteras;
> - hur tidigare fynd känns igen så de inte rapporteras på nytt.
> Prova uppgiften manuellt före schemaläggning. Redovisa sedan sparat schema, nästa körning och en verklig schemalagd körning.
> Märk inte bevakningen som aktiv enbart för att ett schema står i dokumentationen.
> ”Inget relevant nytt” kräver lyckad kontroll. Visa separat när kontrollen misslyckats, varit ofullständig eller inte utförts.
> Kontrollera om poängsättning, popularitet, ålder eller hämtningstak tränger undan viktiga områden. Kritiska förändringar i använda beroenden ska kunna uppmärksammas även när de inte blir högt rankade.
> För principer om handlingsbar övervakning, läs:
> - Google SRE Workbook, Monitoring:
>   https://sre.google/workbook/monitoring/
> Anpassningen till Nortropics omvärldsbevakning är vår tillämpning. Koppla aviseringar till konsekvens och möjlig åtgärd, och följ upp brus och missade signaler.
> 6. För fynd vidare till prövade förbättringar
> Varje relevant fynd ska besvara:
> - Vad har förändrats eller upptäckts?
> - Vilket konkret steg i Nortropic berörs?
> - Vad är observerat, källbelagt respektive en hypotes?
> - Vilken nytta eller risk finns?
> - Vad är minsta rimliga försök?
> - Hur avgör vi om förändringen hjälper?
> - Ska den hanteras nu, senare eller avfärdas?
> Läs följande för bedömning och förbättringsförsök:
> - Thoughtworks Technology Radar, FAQ:
>   https://www.thoughtworks.com/radar/faq
> - Institute for Healthcare Improvement, Model for Improvement:
>   https://www.ihi.org/library/model-for-improvement
> - Anthropic, Demystifying evals for AI agents:
>   https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
> IHI-sidan hänvisar också till metodlitteraturen The Improvement Guide. Redovisa om du använder den lästa webbsidan eller faktiskt har tillgång till boken.
> Återanvänd befintliga statusar. Håll bevakad, bedömd, prövad, införd och verifierad åtskilda.
> Behåll befintligt mandat för beroendeunderhåll. Utvidga det inte automatiskt till nya metoder, tjänster eller kompetenser.
> Prova metodförändringar isolerat, med tydligt mål och jämförelseunderlag. Frys metod och versioner under pågående jämförelseförsök. Inför förändringar vid en lämplig övergång och bevara möjligheten att återgå.
> Ett installerat verktyg, ett lyckat MCP-anrop eller en läst skill visar inte i sig förbättrad kvalitet.
> 7. Samspela med det pågående bygget
> Koppla bevakningen till Codex observation:
> - interna problem ska kunna skapa nya bevakningsfrågor;
> - externa fynd ska kunna ge konkreta förslag till ansvarig arbetare;
> - sådant som behöver vänta ska kopplas till befintlig backlogpost eller få en tydligt avgränsad ny post.
> Märk återkopplingen som granskarförslag, aldrig som ägarbeslut. Skilj dokumenterat, skickat, mottaget, genomfört och verifierat.
> Spara observationen före påverkan och resultatet efter. En körning som fått hjälp ska redovisas som assisterad. Blind slutbedömning behöver separat session och avgränsat underlag.
> För kontext och överlämningar, läs:
> - Anthropic, Effective context engineering for AI agents:
>   https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
> Följ upp om förbättringen faktiskt hjälpte och om den skapade regressioner, högre kostnad eller onödig komplexitet.
> 8. Gör allt begripligt i arbetsytan
> Jag ska kunna se:
> - vilka delar av Nortropic som bevakas;
> - vilka som saknar täckning eller har inaktuell kontroll;
> - senaste lyckade körning och nästa planerade;
> - viktiga fynd och deras konsekvenser;
> - pågående försök, införda förändringar och verifierad nytta;
> - vad som behöver mitt beslut.
> Visa en kort daglig sammanfattning med länkar till belägg. Låt ”inget handlingsbart i dag” vara ett giltigt resultat.
> Bevara privata kundspår i privat lagring. Publika poster anonymiseras. Externt källmaterial behandlas som underlag att bedöma, inte som instruktioner att följa.
> Leverera inventeringen och täckningsbilden, ett manuellt prov och verifierad schemaläggning. Redovisa tydligt vad som fortfarande saknas.
> Behåll gällande gränser för åtkomst, kvot, externa tjänster, publicering och ägarbeslut. Återanvänd befintliga rapporter och register. Målet är bättre leveranser och ett mer tillförlitligt flöde, med belägg för att förbättringarna fungerar.

Ägarens besked ~13:30Z, ordagrant: "du kan rensa de gamla kandidatera nu när vi gör dessa förändringar på detta".
Utfört 13:31:52Z: spanarens 200 obehandlade kandidater satta till utgången med skäl och inskrivna i SEDDA.json; arkivet
i ~/Arkiv.

**Genomförarens tillämpning** (teknikbeslut inom tillägget, inte ägarens beslut):

- **Ett register, en klocka, en förbättringskö.** Bevakningsfrågorna står som block i det befintliga källregistret
  (`kunskap/spaning-kallor.md`, Bevakningsfrågor). Dashboardens befintliga timklocka kör den dagliga kontrollen
  (`kontroller/bevakning.py`) efter 07:00 Europe/Stockholm, och nya fynd blir signaler i förbättringsloopen
  (`kirurgen/forbattringar`), där bevakad, bedömd, prövad, införd och verifierad redan skiljs åt.
- **Ingen ChatGPT-schemaläggning.** Enligt OpenAI:s dokumentation (Scheduled tasks, läst 2026-10-09) finns
  schemaläggningen bara i ChatGPT-appen, inte i Codex CLI, och en lokal uppgift kräver att appen är igång. Det vore en
  andra klocka. Codex prövar i stället de frågor som kräver omdöme med `codex --search exec` på bevakningspaketet,
  manuellt tills ägaren beslutar om en rytm.
- **Spanarens rytm.** Dagligen under piloten sedan ägarens ord 2026-10-03 ("jag vill ha den frekventare"; koden och
  driften), inte veckovis som README och tilläggen 2026-10-01 sade. README och spana.py är rättade. Den tidigare
  formuleringen här i BESLUT.md står kvar som historik.
- **Spanarens tak för sidor.** Bevakningens första manuella körning visade att 20 källor föll på taket 256 kB (sedan
  a108560 avvisas en större sida helt), bland dem Claudes release notes, Anthropic news, Prompting Claude och IMY.
  Taket för sidor är nu 4 MB, och flöden klipps åter vid sista hela posten. I torrkörningen föll 1 av de 20
  (Konsumentverket, utan läsbar text).

## Ägarbeslut 2026-10-09 ~14:25Z: aktivera arbetsytan, Codex-kanalen och bevakningen i ordinarie drift

**Status:** gäller. Det ersätter beskeden att vänta med Codex rytm, spanarens rytm efter piloten och luckorna
(tillägget om kontinuerlig bevakning, ovan). Inklistrat och ordagrant (texten började med "garbeslut:"):

> garbeslut: aktivera arbetsytan, Codex-kanalen och bevakningen i ordinarie drift
> Jag vill aktivera hela det planerade upplägget. Förslaget om en begränsad pilot med en Codex-fråga per vecka gäller inte.
> Du har mandat att genomföra återstående rättelser, kontroller, sammanslagning, push och aktivering enligt nedan. Återkom inte för samma klartecken igen.
> 1. Slutför och aktivera
> - Slutför den sammanhängande användarresans nio punkter i samma körning.
> - Rätta eventuella fel och kör hela rökprovet på det slutliga trädet.
> - Samordna med pågående förfining så att körande kod och sessioner inte störs. Ett tungt prov åt gången.
> - Efter godkända kontroller: slå samman, pusha och starta om arbetsytan på :4771 med bibehållen åtkomst.
> - Aktivera Codex-kanalen, arbetsytans funktioner och bevakningen. Verifiera dem även efter aktiveringen.
> Detta är mandat att slutföra och driftsätta nu. Ett faktiskt blockerande fel ska rättas och redovisas.
> 2. Bevakningen ska gå i ordinarie drift
> - Behåll spanarens dagliga körning som ordinarie drift. Ta bort den oavgjorda övergången till veckovis efter en pilot.
> - Aktivera automatisk Codex-granskning enligt bevakningsfrågornas planerade vecko- och månadsintervall.
> - Samtliga 22 frågor och 13 områden ska omfattas av sina angivna kontroller. Återanvänd den befintliga klockan, registret och förbättringsloopen.
> - Slutför kopplingen inför byggstart och visningen i arbetsytan.
> - Visa senaste lyckade kontroll, eventuella fel, nästa körning och kvarstående täckningsluckor.
> - Misslyckad hämtning, ofullständigt underlag och utebliven analys får aldrig presenteras som ”inget nytt”.
> - Hantera Konsumentverkets återstående hämtproblem genom en fungerande officiell källa eller lämplig läsmetod. Markera luckan tills den är verifierat löst.
> Bevakningen ska både upptäcka förändringar och undersöka obesvarade frågor. Förslag förs vidare genom befintlig bedömning, prövning och uppföljning. Införanden följer gällande mandat.
> 3. Alla identifierade luckor ska få ansvar och nästa åtgärd
> Det gäller verklig användarobservation, uppföljning efter leverans, upphovsrätt och AI-regler, ljud och video, verkligt kundintag samt förbrukning och kvot.
> Koppla varje lucka till befintlig roll och ansvarig post. Genomför det som ryms inom mandatet. Ange exakt vilket underlag eller vilken extern förutsättning som behövs för resten. Undvik dubbla poster.
> 4. Rätta och stäm av redovisningen
> - Precisera H01:s bedömningshistorik: den nya Codex-kanalen var inte aktiv under försöket, men ägaren fick Codex blinda A/B-bedömning i samtalet före det bokförda valet. Skilj detta från en oberoende mänsklig blinddom. Bevara historiken med ett daterat tillägg.
> - Stäm av rapporternas uppgifter om arbetsytans bevakningsvy och byggstartskopplingen mot den levererade koden.
> - Redovisa 59 720 tokens som ett uppmätt anrop. Det är inte en fast kostnad per fråga eller en mätning av abonnemangets kvot. Dokumentera faktisk förbrukning och saknade mätvärden.
> - Precisera OpenAI-uppgiften: kravet på påslagen dator och öppen app gäller schemalagt arbete med lokala projekt. Behåll Nortropics befintliga klocka. Källa: https://learn.chatgpt.com/docs/automations
> - Skilj genomgående mellan byggt, provat i provinstans, aktiverat, verifierat i drift och visad förbättring.
> 5. Leverera ett sammanhängande driftsbesked
> Redovisa slutlig commit, fullprovets slutrad, resultatet av användarresan, aktiverade funktioner, verifieringen på :4771 och nästa schemalagda körning. Följ därefter upp den första automatiska körningen och rapportera dess faktiska resultat.
> Befintliga gränser för helbyggstart, publicering, kundkontakt, köp, privat material och blinda försök gäller fortsatt.
> Målet är att hela det beställda upplägget arbetar i ordinarie drift och att kvarstående begränsningar är synliga och omhändertagna.

**Genomförarens tillämpning** (teknikbeslut inom beslutet):

- **Spanaren** körs dagligen i ordinarie drift. Övergången till veckovis efter en pilot är borttagen ur koden, README
  och källregistret.
- **Codex granskar automatiskt.** Frågor med kontrollen codex prövas av `codex --search exec`, i dashboardens befintliga
  timklocka, före den dagliga kontrollen, när frågans vecko- eller månadsintervall gått (`bevakning.codex_vid_behov`).
  - En granskning som faller registreras som fallen och ger utfallet misslyckad, aldrig "inget nytt".
  - Varje körning loggas med tid, modell och de tokens Codex redovisar (`codex-korningar.jsonl`).
- **Alla 22 frågor har en körbar kontroll.** De frågor som tidigare hade en manuell kontroll prövas av Codex, och
  förbrukningen har en egen mätande kontroll (`forbrukning`). En fråga med lucka prövas också, och luckan redovisas för
  sig.
- **Utfallet följer kontrollerna.** Det är ej utförd när ingen kontroll gjorts, misslyckad när de gjorda föll, och
  ofullständig eller fynd när något återstår. Inget nytt står bara när varje kontroll lyckats.
- **Luckorna.** Var och en har ansvar, befintlig post, nästa åtgärd och extern förutsättning i registret.
  - Två poster var nya, eftersom ingen fanns: upphovsrätt och AI-regler, samt förbrukning mot kvot.
  - Ljud fördes in som en daterad not i materialpostens del D.
- **Inför byggstart.** Startkontrollen får raden "bevakningen" (`bevakning.byggstart`): senaste körningen, fynd sedan
  kundens förra start, kontroller som inte lyckats och luckorna. Raden stoppar inget.
- **Konsumentverket.** Källan är det officiella nyhetsflödet `api/feed/rss/nyheter/`, eftersom sidan /aktuellt/ kräver
  JavaScript. Torrkörningen gav 5 poster och 0 fel. Luckan står som ofullständig tills spanaren har hämtat flödet i drift.
- **Precisering av OpenAI-uppgiften** (rättar tillägget om kontinuerlig bevakning, ovan, och historiken står kvar).
  Enligt https://learn.chatgpt.com/docs/automations gäller kravet på påslagen dator och öppen ChatGPT-app schemalagt
  arbete med lokala projekt. Nortropic behåller sin befintliga klocka.
- **Precisering av förbrukningen.** De 59 720 tokens från bevakningens Codex-prov 2026-10-09 är ett uppmätt anrop. De är
  ingen fast kostnad per fråga och ingen mätning av abonnemangets kvot, som inte exponeras.
- **H01:s bedömningshistorik.** Den nya Codex-kanalen var inte aktiv under försöket. Ägaren fick Codex blinda
  A/B-bedömning i samtalet före det bokförda valet 13:58:47Z. Valet är ägarens bekräftade val efter den bedömningen,
  inte en oberoende mänsklig blinddom. Daterade tillägg står i RAPPORT-2026-10-09-codex-observation-h01 och i 97:s
  RAPPORT-2026-10-09-formagoprov-kvalitetsprov. Domloggens rad är orörd.

**Status 2026-10-09 ~17:25Z** (byggt, provat i provinstans, aktiverat, verifierat i drift och visad förbättring hålls isär):
- **Aktiverat** 16:52Z: main a787bc5, efter fullprovet på exakt den versionen (slutraden "rökprovet OK"). :4771 är
  omstartad med samma nyckel.
- **Verifierat i drift:**
  - Codex-kanalen: läsning med driftens nyckel, utan nyckel 401, och ett riktigt Codex-fynd registrerat 16:58:04Z.
  - Konsumentverkets flöde hämtades av spanaren i drift 16:55Z; luckan är löst.
  - Bevakningens första automatiska körning 17:04:27Z gav utfallet delvis. Juridik är ofullständig, eftersom PTS svarade
    med en tidsgräns.
- **Visad förbättring:** ingen än.
- **Rättat efter aktiveringen** (1879f82): intervallen räknades i timmar. Efter den sena första körningen hade nästa dags
  07:00-körning därför hoppat över de dagliga frågorna. De räknas nu i lokala dagar.

## Ägarens besked 2026-10-09 ~17:11Z: allt ska in i arbetsytan

Efter aktiveringen frågade ägaren ~17:05Z: "varför är den klassiska vyn kvar?". På genomförarens svar (knappen Klassisk
vy är en reservväg, flera funktioner nås via Fler vyer i de gamla vyerna, förslaget att ta bort knappen nu och göra
flytten som en egen post) svarade ägaren ~17:11Z, ordagrant:

> hur menar du? allt ska ju in i det här nya vyn?

**Vad det rättar:** uppdragets punkt 2 ~11:22Z ("Arbetsytan ska vara normal startvy och ge tillgång till: …") tillämpades
som länkar från arbetsytan till de gamla vyerna. Ägaren menade att allt ska finnas i arbetsytan. Den kompletta
arbetsplatsen är därför inte klar, trots att genomföraren efter aktiveringen sa att den var det.

**Tillämpning:**
- Varje funktion i de klassiska vyerna flyttas in i arbetsytan, med arbetsytans navigering och utseende. Det gäller
  Flöde, Prototyp, Kundstart, Jämförelser, Översikt och byggen, Starta, Underhåll, Kirurgen, Backlog, Kalibrering,
  Lärdomar, Designprov, Prospekt och Dokumentation.
- Därefter tas knappen Klassisk vy, menyn Fler vyer och de gamla vyerna bort.
- Ingen funktion får försvinna på vägen (uppdraget ~07:24Z: "flytta inte bort … utan ersättande navigering").
- Gränserna för helbygge, publicering, kundkontakt, köp, privat material och blinda försök gäller som förut.

**Genomförarens tillämpning** (teknikval inom beskedet):
- **En ram.** Arbetsytan ritar varje adress. Delarna ritas i dess ram (`arbetsytaSektion` i `dashboard/arbetsyta.js`)
  med huvudet, kunden och arbetsytans färger. Delarnas egna klasser får arbetsytans värden genom samma variabler.
- **Samma funktioner.** Delarnas kod, adresser, skrivvägar och skydd är oförändrade (dashboardnyckeln, start-id,
  bekräftelser, utkast och generationsvakter). Ingen funktion skrevs om, så ingen kunde tappas på vägen.
- **Navigeringen.** Projektets tre vyer står bredvid två menyer, Kundproduktion och Systemförbättring, som hålls isär
  enligt uppdraget ~07:24Z, och Dokumentation och rapporter står för sig. Underhåll och verktygslådan blev en egen del,
  i stället för att ligga sist i Översikten. Översikten heter nu Byggen och dina domar.
- **Kvar efter flytten:** några funktioner finns två gånger i arbetsytan. Flöde ligger bredvid Byggflöde, och
  Prototyps beslut ligger bredvid beslutet i Arbetsyta. Att slå ihop dem är nästa steg och redovisas för ägaren.

**Ägarens ord ~18:28Z**, efter driftbeskedets tre öppna punkter, ordagrant: "Gör det det du anser är rekommendationen".
Genomförarens tillämpning, på det mandatet:
- **Codex fynd om B** (granskningsfynd för k02, 16:58Z): fyndet stämmer, men det ändrar inte B. B går inte till
  helbygge, och 97:s uppdrag ~17:53Z rensar de gamla kandidaterna. Sakfrågan förs till kundförståelsen i nästa omgång:
  obekräftade priser står bara som märkta utkast. Beställningens prisfrågor är redan öppna. Meddelandet står kvar
  obeslutat, eftersom arbetsytan visar ett beslut där som ägarens eget.
- **Dubbletterna:** Flöde förs in i Byggflöde, och Prototyps beslut förs in i arbetsytans förslagsyta inom 97:s uppdrag
  om tio förslag. Därefter tas båda posterna ur menyn.
- **Prospekt** står under Kundproduktion, eftersom det handlar om att hitta kunder och inte om att förbättra systemet.

## Tillägg 2026-10-09 ~17:53Z: ägarens uppdrag om tio förslag och en ren designstart

**Status:** gäller; genomfört 2026-10-09 (lägesrapporten `RAPPORT-2026-10-09-tio-forslag-ren-designstart`). Det ersätter
minimiantalet tre varv, valet som startade fördjupningen och ribban ur de gamla kalibreringsankarna (tabellen Ersatta
designregler). Inget helbygge och ingen publicering är godkända genom det.

Ägaren klistrade in ett uppdrag i tolv punkter (ordagrant i minnet, `nortropic-agaren-tio-forslag-ren-designstart-uppdrag-20261009`),
med raden "Var noggrann med att gå in på varje nämnd källa för förståelsen och websaercha". Ägarens egna formuleringar
som styr, ordagrant:

> Kundunderlag → kundförståelse → starka branschreferenser → visuell inspiration och användbara mallar/komponenter → tio kundanpassade förslag → kundens val → riktad förbättring → helbygge → verifierad leverans.

> Tio förslag är mitt beslut. Det tidigare förslaget att minska antalet är inte antaget.

> Målet är snabbare väg till hög kvalitet. Antalet rapporter, lästa skills, verktygsanrop eller iterationer är inget kvalitetsmått.

> Ta bort minimiantalet tre förfiningsvarv. Använd observerad brist → ändring → efterkontroll. Behåll rimliga resursgränser och möjlighet att stoppa rundgång.

> Detta uppdrag innebär inget automatiskt godkännande av helbygge eller publicering. Befintliga startmandat gäller.

**Nuläget på 361f1e6 (punkt 2):** Codex fem iakttagelser på 422ff6b gällde fortfarande: prototyp.py förde både valj och
kandidatens putsa till samma fördjupning; forfina_prompt beställde hela startsidan, undersidan och centralt flöde för
skisskörningar; efter_fordjupning körde båda specialistpassen; passens visuella bedömning sparades men styrde ingen
återställning; och minst tre förfiningsvarv var en instruktion fast metodkartan kallade antalet ett oprövat processval.

**Genomfört** (grenen `claude/tio-forslag-20261009`; detaljerna i `kunskap/skapandeflodet.md` och rapporten
`underlag/rapporter/RAPPORT-2026-10-09-tio-forslag-ren-designstart.md`, privat):
- **Ren designstart** (`kunskap/ren-designstart.md`, `kontroller/ren_designstart.py`): manifest, verifierat arkiv i
  `~/Arkiv/nortropic-ren-designstart-20261009/`, vakt i startkontrollen, läsförbud för arkivet, rapporterna och
  granskningarna i flödets sessioner. `LARDOMAR.md` börjar om vid brytpunkten (numreringen fortsätter med L7),
  `kunskap/visuell-niva.md` är borttagen, och granskaren säger sanningsenligt att den är okalibrerad
  (`granska.kalibreringsstatus`). Taggen `fore-ren-designstart-20261009` är läget före.
- **Uppdragen** (punkt 8): beslutet `uppdrag` med typen Rätta, Omarbeta designen eller Bygg ut, versionen, det
  önskade resultatet, omfattningen och det som ska bevaras (`skapande.uppdrag_giltigt`); ett val startar inget;
  `putsa` i kandidatflödet är ersatt; handlingens benämning är det som startas.
- **Kundens beslut** (punkt 11): källan `kunden` med belägg gäller val, uppdrag och underkännanden, aldrig godkännandet
  för helbygge eller publicering.
- **Specialistpassen** (punkt 9) bara på uppdragets begäran, ändrande eller bedömande; återkopplingen i formen bild,
  version, element, tillstånd, avvikelse och kodkoppling.
- **Före och efter** (punkt 10): en separat blind granskare jämför versionerna som X och Y utan skaparens förklaring,
  och regeln avgör fortsättningen; tidigare versioner kan väljas; inget minsta antal varv.
- **Kundförståelsen** (punkt 4): KUNDFORSTAELSE.md i förberedelsen, prövad före publiceringen.
- **Branschen och de tio förslagen** (punkt 5–6): branschgenomgången, förebilder utanför branschen, visuell
  utgångspunkt och implementationsgrund per förslag, skillnadens dimensioner (bara färg avvisas), bristen mot tio
  redovisad i stället för utfylld. 21st:s `get_theme` fick en uppgift (teman är CSS-variabler, användbara i Astro).

**Ersatt:** raderna i tabellen Ersatta designregler ovan (minst tre varv, ett val som fördjupar, ribban ur
kalibreringen) och designreglernas hypoteser ur gamla byggen (brödsmulor, upptagna val, tummen). Gällande ägarbeslut
utanför uppdraget står kvar.

**Öppna frågor för ägaren:** Mobbins villkor (§3.2) förbjuder cache och arkiv utan skriftligt medgivande, och
21st:s villkor (§3) är oklara för komponentkod i kundsajter; båda bör klaras ut skriftligt med leverantörerna innan
lagring och kundleveranser blir rutin. (Besvarat: ägarens besked 2026-10-09 ~21Z om licenserna, nedan.) Prototyps funktioner flyttas in i arbetsytans förslagsyta efter det här
uppdraget (b3:s förslag, delningen 2026-10-09 ~18:28Z).

## Ägarens besked 2026-10-09 ~18:2xZ: Dyad-provet, köat efter uppdraget ovan

**Status:** gäller; genomfört 2026-10-10 i alla tre stegen (`kunskap/dyad-prov.md`, `kontroller/falsk_modell.py`,
provläget i `kontroller/nastlad.py` och `kontroller/rokprov/revision/prov_dyad.py` i rökprovets lista). Steg 1 gick att
genomföra, och steg 2 och 3 höll för skisskritiken, före/efter-granskaren och skaparen i ett uppdrag.

Ordagrant:

> angående dyad:  Efter pågående uppdrag: bygg hela Dyad-provet. Steg 1 genomförbarhet (claude -p mot falsk server, stanna och redovisa om det inte går). Steg 2 provläge låst till prov, med prov att det aldrig gäller i drift. Steg 3 prov per roll: modell, instruktion, bildernas sha256 och att blinda roller saknar skaparens material. Inga riktiga nycklar i dumparna.

## Ägarens ord 2026-10-09 ~19:20Z: alla relevanta saker täckta med granskningar

Efter att det visat sig att juridikfrågan inte granskas av Codex, och att PTS bytts till sitt officiella pressrum, sa
ägaren ordagrant:

> alla relevanta saker ska vi täcka med våra granskningar, saknar vi någon?

**Det som saknades:**
- 14 av 22 frågor hade bara en mekanisk kontroll. Källan eller beroendet ändrat märktes, men ingen bedömde om det
  spelade roll.
- Åtta relevanta ämnen saknade fråga:
  - säkerhet;
  - personuppgifter i kundsajterna;
  - villkoren för tjänsterna;
  - prospekt och utskick;
  - formulär och e-post;
  - underhåll efter leverans;
  - konkurrenter och ribban;
  - text och språk.

**Genomförarens tillämpning** (teknikval):
- **Granskning vid fynd.** De 13 frågorna med mekanisk kontroll fick Codex-granskning med `bedömning: vid-fynd`, och
  den nya frågan om villkoren fick samma.
  - Codex bedömer frågan när kontrollerna hittat något nytt, högst en gång per vecka, och annars minst en gång i
    månaden.
  - Paketet bär de nya fynden att bedöma.
- **Åtta nya frågor.** Säkerheten granskas veckovis med källan Node.js säkerhetsflöde och Astros releaser. De andra
  granskas månadsvis.
- **Täckningen nu:** 30 frågor, varav 29 med en bedömande granskning. Den som saknar en är inför byggstart, som prövas
  vid varje byggstart.
- **Utspridning.** Högst åtta granskningar per daglig körning, så att de cirka 21 första granskningarna sprids över
  tre dagar.
- **Kostnaden** är uppskattad ur dagens uppmätta granskningar, ungefär 60 000 tokens var. Det blir cirka 2–5 miljoner
  tokens i månaden, mot cirka 0,9 miljoner före ändringen. Den faktiska förbrukningen mäts i förbrukningsfrågan. Kvoten
  exponeras inte.

## Tillägg 2026-10-09 ~21Z: ägarens besked om licenserna och godkännandena för verktygen

**Status:** gäller.

Efter rapporten om tio förslag och den rena designstarten klistrade ägaren in, ordagrant (platshållarna som de kom):

> ÄGARENS BESKED om licenserna (Mobbin och 21st), efter rapporten om tio förslag och den rena designstarten:
>
> Jag har skriftliga godkännanden från båda. Licensfrågorna i rapportens avsnitt 8 är därmed besvarade.
>
> 1. Mobbin: [datum, avsändare hos Mobbin]. Godkännandet gäller [t.ex. att vi sparar skärmar och flöden per körning
>    för vårt interna designarbete, och att de får ligga kvar i återställningsarkivet]. Villkor: [inga / ange].
> 2. 21st: [datum, avsändare hos 21st]. Godkännandet gäller [t.ex. att komponentkod från 21st får användas i våra
>    kunders webbplatser utan synlig länk tillbaka, med komponentens egen licens]. Villkor: [inga / ange].

På genomförarens fråga om omfattningen svarade ägaren för båda, ordagrant: "allt får vi göra". Därefter, ordagrant: "vi
har fulla godkännande för alla våra verktyg, mcps, skills, källor etc."

**Räckvidd:**
- Licens- och användningsvillkoren hos verktygen, MCP:erna, skills och källorna är klarade. Mobbins skärmar och flöden
  får sparas per körning och ligga kvar i återställningsarkivet. Komponentkod från 21st får användas i kundernas
  webbplatser utan synlig länk tillbaka, med komponentens egen licens.
- De skriftliga godkännandena har ägaren. Datum och avsändare är inte angivna här.
- Ägarens egna beslut om gränser som inte är licensfrågor står kvar tills ägaren säger annat. Det gäller
  kunddatagränsen mot externa tjänster, prenumerationsgränsen (2026-10-08) och att ursprung och licens noteras per
  komponent, typsnitt och bild (RIKTNING.md, DESIGN.md, BILDER.md). Lagkrav som dataskydd och marknadsföringslagen
  gäller som förut.

## Tillägg 2026-10-09 ~22Z: Prototyp är arbetsytans Förslagen

**Status:** gäller; genomfört (dubbletten Prototyp och arbetsytans beslut, efter ägarens besked ~17:11Z att allt ska in
i arbetsytan och mandatet ~18:28Z, "Gör det det du anser är rekommendationen", med b3:s och 97:s delning).

- **Förslagen** är en av projektets fyra flikar (`#/arbetsyta/<kund>/forslag`). Den har allt som vyn Prototyp hade:
  bilderna i alla bredder, förslagen sida vid sida, referensen bredvid, redovisningen, de tekniska kontrollerna, det du
  gillar per förslag, observationen och hela beslutet. Posten Prototyp i menyn är borta, och `#/prototyp/<kund>` leder
  till Förslagen för samma kund. Vyns innehåll flyttades oförändrat, och bara beslutets väg och avsändaren ändrades.
- **En beslutsväg.** Förslagens beslut går nu genom arbetsytans väg (`samverkan.beslut`), som raden under
  ögonblicksbilden. Ett godkännande binds alltså till versionen och bildernas sha256, och minuterna till beslutet
  sparas som förut. Kunden kan vara avsändare med belägg för alla beslut utom godkännandet, som är ägarens.
- `POST /api/prototyp/<kund>` står kvar för den äldre utforskningen med riktningar och för proven. Den används inte av
  Förslagen.

## Ägarens beslut 2026-10-09 ~21:17Z: Cloudflare Workers är målplattformen; sajterna på Vercel stannar

**Status:** gäller; under genomförande (b3, grenen `claude/cloudflare-20261009`). Ersätter Vercel som målväg för nya
leveranser i tidigare beslut ("Vercel väntar tills en kund ska ut"); historiken om Vercel står kvar som den var.

Ägarens ord ~21:17Z, ordagrant: "Då köar jag nästa arbete hos dig som du har fullt autonomt mandat att köra inatt." och
i samma meddelande: "Läs hela den bifogade filen: PROMPT-Nortropic-integrationer-och-Cloudflare-migrering-v2.md. Detta
är mitt gällande, samlade genomförandeuppdrag. Det ersätter den tidigare integrationsprompten. Cloudflare Workers är
beslutad målplattform. Genomför hela integrationsomfattningen och migreringen från Vercel enligt de åtta etapperna.
Gör inte en ny hostingjämförelse. Kontrollera aktuellt repo och pågående arbete först. Behåll redan verifierade
resultat och undvik dubbelarbete. Fortsätt sedan med implementation, migrering, dokumentation och prov — inte bara en
ny plan. Skilj implementerat, verifierat, driftaktiverat och avvecklat. Genomför externa åtgärder inom faktiskt
tillämpligt mandat."

Ägarens ord ~21:22Z, efter beskedet om inventeringen av Vercel-projekten, ordagrant: "inga att de som är på vercel ska
flyttas över, hemsidor alltså"

**Tolkning** (genomförarens, redovisad för ägaren att rätta): inga befintliga webbplatser på Vercel flyttas. De står
kvar där som tidigare drift, med status per projekt i uppdragets privata rapport, utan migrering eller avveckling.
Migreringen gäller leveransvägen: mallen, exporten, förhandsvisningen, proven, verktygen och dokumentationen.

**Räckvidd och gränser** (ur uppdragsfilen, som ligger privat i `underlag/uppdrag/`):
- Inga köp av domäner, abonnemang eller tjänster, inga uppgraderade planer, inga accepterade avtal, inga verkliga
  betalningar, återbetalningar, bokföringshandlingar, utskick eller kundpubliceringar utan ett separat tillämpligt
  mandat; ingen publik OAuth-app eller publik callback som bieffekt av ett lokalt prov.
- Befintliga nycklar är inte i sig tillstånd att använda dem; kundvalvet läses aldrig in i en modells kontext; inga
  privata kunduppgifter, leverantörsbevis eller hemligheter i det publika motorrepot.
- Ägarval, kundbeställningar, kontoåtkomst, samtycken, användarprov och leverantörsresultat förfalskas aldrig.
- Domänomkoppling, kopiering av personuppgifter, aktivering av skarpa resurser och avveckling görs bara inom
  tillämpligt kund-, konto- och kostnadsmandat.
- "Allt är klart" sägs inte när katalogen är fylld men anslutningskod, kombinationsprov eller leverantörsbevis saknas.

**Läget när detta skrevs:** leveransvägen är omskriven för Workers och prövad lokalt (export och förpackning utan
konto, Workern i workerd, formulärets felvägar), integrationskatalogen K01–K18 finns med validering och plan, och
Nortropics Cloudflare-konto är inte anslutet: inget är prövat mot Cloudflare, och inget är driftaktiverat eller
avvecklat. Var vägen och fakta står: `kunskap/lansering.md` (Cloudflare-steget) och `kunskap/forfragan.md`.

## Tillägg 2026-10-09: kompetensens verkliga användning i rätt steg

**Status:** gäller som uppdrag; rättelserna ligger i en separat gren och är inte aktiverade i drift.

Ägarens aktuella uppdrag, ordagrant:

> SE ÖVER ALLA SKILLS OCH MCPS OCH SÄKERSTÄLL ATT DE ANVÄNDER FULLT UT I I RÄTTA STEG

Codex tillämpning i en separat arbetsgren, inte ett nytt ägarbeslut om konton eller publicering:

- Inventeringen skiljer installerat, rollens uppgift, tillgång i sessionen, observerad användning, vald artefakt och
  bedömd effekt. Rapporten och de fullständiga tabellerna är privata under
  `underlag/granskningar/GR-20261009-kompetens-hela-flodet.md`.
- Refero, Mobbin och 21st undersöks före planen. 21st får även hämta ett valt tema. Vald komponent eller tema följer
  med som källa, id, rättigheter och beroenden; ett söksvar är inte bevis för implementerad kod. Leverantörens
  ordning är sök, välj, hämta kod och integrera: https://github.com/21st-dev/magic-mcp/blob/main/skills/21st-ui/SKILL.md.
- Varje kandidatflödessession prövas mot rollens kärna och aktiverbara skills. En ny session behöver ett eget
  kvitto. Laddning via Skill och full läsning binds till rätt lokala fil även när frontmatternamnet skiljer sig
  från mappen. Dokument och Initial Response-undantagen följer den befintliga läsformen.
- Brister sparas och hindrar ett aktuellt klart resultat, även vid återupptagning. Planering och förfining får
  egna kvitton. Gamla underlag bevaras; inga historiska domar ändras till ny evidens.
- Helbygget ansluter ateljéns fyra designtjänster med samma kundvakt och skyddade nyckelhantering. Ett uttryckligt
  av-läge finns för isolerade prov. Ingen tjänst får fria MCP-behörigheter och gamla Inspo-konfigurationen saknar
  den kundvakt som denna ingång kräver.
- Startkontrollen använder den aktuella fasens obligatoriska tjänster. Förfining med ett befintligt giltigt
  researchunderlag kräver inte en ny research. Flödesvyn visar inte helbygget som kontrollerat utan slutkod 0
  och ett uppfyllt eget kompetenskvitto.
- Räckvidden är mekanik, inte visad designförbättring. Automatisk DevTools-beställning och externa materialleverantörers
  generering är fortfarande luckor. Helbygget får ett eget kompetenskvitto knutet till byggsessionen, och dess
  obligatoriska aktivering och läsning måste vara observerad för slutkod 0. Verkliga sessioner och betald
  åtkomst har inte prövats i denna rättelseomgång. Inget helbygge, ingen extern publicering eller kontoändring ingår.

Samordna med det separata arbetet för tio förslag före sammanslagning. Rättelsen ändrar inte det arbetets
formgivningsval, arbetsordning eller ägarens godkännandegränser.

## Ägarens beslut 2026-10-10 ~06:05Z: Cloudflares e-post är K04:s huvudväg i stället för Resend

**Status:** gäller; genomfört i leveransvägen och prövat lokalt (b3, grenen `claude/cloudflare-20261009`). Ersätter
Resend för formulärets avisering; prospektens utskick (`kontroller/utskick.py`) går fortfarande genom Resend, som
beslutet inte rör. Resend-paketet står kvar i integrationskatalogen som inaktuellt (historik).

Ägarens ord ~06:05Z, ordagrant: "Vi gör gör Cloudflares e-post till huvudvägen för K04 efter du har kvalificerat mot
dokumentationen istället för resend"

Ägarens ord före 06:16:55Z, ordagrant: "ja" (på frågan om att slå på Email Routing för underdomänen
`notis.nortropic.se`: nya DNS-poster bara på underdomänen, apex-domänens MX hos Google Workspace orörda). Också,
ordagrant: "vi kommer göra om nortropic.se så det gör inget ifall det händer."

**Kvalificeringen** (Cloudflares dokumentation, läst 2026-10-10; källorna i katalogens `k04-cloudflare-epost`):
- Workern skickar med `send_email`-bindningen (`env.EMAIL.send({from, to, subject, text, attachments})`), som svarar med
  `messageId` och kastar fel med en kod (`E_*`). Ingen nyckel i Workern.
- Mejl till verifierade mottagare är gratis på alla planer och räknas inte mot kvoten; högst 200 verifierade adresser
  per konto, delade av alla kunder; 25 MiB per meddelande. Avsändaren måste ligga på en routing-domän i kontot.
- Mejl till godtyckliga mottagare (Email Sending) kräver Workers Paid; det ingår inte (inget planbyte utan mandat).
- Bindningen har ingen idempotensnyckel: ett osäkert utfall står som `skickar` i utkorgen och skickas aldrig om
  automatiskt. Var innehållet behandlas anges inte i källorna.
- Lokalt simulerar `wrangler dev` bindningen utan att skicka, så länge den saknar `remote: true`.

**Genomfört:** Email Routing påslaget för `notis.nortropic.se` 2026-10-10 06:16:55Z (MX och SPF på underdomänen, DKIM
under `cf2024-1._domainkey.nortropic.se`; posterna före ändringen sparade privat). Workern, mallens `wrangler.jsonc`
(bindningen låst till platshållare som releasen nekar), exporten (kundens mottagare och avsändare ur
`underlag/<slug>/CLOUDFLARE.json`), proven (attrappen av bindningen med felkoder; Wranglers simulering i
`workersprov.py`), katalogen och dokumentationen (`kunskap/forfragan.md`, `kunskap/lansering.md`). Inget riktigt mejl
är skickat: en verifierad mottagare och ett första skarpt prov kräver en verklig verksamhet och sitt eget mandat.

## Tillägg 2026-10-10: införande av kompetensens återstående körvägar

**Status:** gäller som uppdrag; genomförs i separat gren, inte aktiverat på main eller i dashboarden.

Ägarens ord:

> åtgärda sakerna du nämner

Uppdraget fortsätter granskningen av skills och MCP:er. Föregående rättelser integreras med det nya
uppdragsstyrda förfiningsflödet. Befintliga avgränsningar för konton, publicering och privata uppgifter gäller.

- Valda referenssidor får en separat DevTools-inspektion före skaparna, bunden till sida, bilder, paket och metod.
  Ett fullständigt oförändrat resultat återanvänds. Brister sparas och stoppar berört fortsatt skapande.
- Brand-, token-, Tailwind- och canvasfunktioner körs genom en kandidatbunden skriptbrygga med fasta åtgärder.
  Renderingen ger faktiska PNG/PDF-filer; utfallet är ett underlag för bedömning, aldrig ett designgodkännande.
- Materialsteget får transportkontrakt för text till bild/video hos de angivna leverantörerna. Beställning och
  betrodd verkställighet hålls isär: uppdragshash, kostnadsmedgivande, rättigheter och konto krävs före nätanrop.
  Ett sparat jobb återupptas utan en ny beställning. Denna rättelse aktiverar inget konto och beställer ingen media.
- Före/efter-bedömning kräver observerad kompetens och båda versionernas bilder. Ett gammalt jämförelsekvitto får
  inte styra en ny version. Specialistpass som bara bedömer får läsande verktyg; en faktisk kodändring återställs.
- Motion+ och Mobbins deep-läge öppnas inte genom detta uppdrag: tidigare uttryckliga ägaravgränsningar kvarstår.
  Cloudflare-arbetet fortsätter separat och denna gren ändrar inte leveransplattform eller aktiverar drift.

Kontrakt: `kunskap/referensprofil.md`, `kunskap/skillskript.md`, `kunskap/materialtransport.md` och metodkartan.
Verifieringen redovisas i `underlag/granskningar/GR-20261010-kompetens-inforande.md`. Lokala prov visar mekanik;
verkliga kontoresultat, modellens tillämpning och visuell kvalitet kräver fortfarande sina verkliga prov.

Provavgränsning: Dyad-provets verkliga CLI använder en lokal modellattrapp i en egen hem- och konfigurationskatalog,
med tomma MCP-konfigurationer och OS-nekande av andra nätmål. Ingen åtkomst till användarens riktiga Claude- eller
hemlighetsmappar behövs. Detta är transportprov, inte extern integration eller modellkvalitet.

Verifieringen hittade också ett tidsfönster i axe-kontrollens formulärläge: en blockerad navigation kunde
ha bytt dokument innan webbadressen ändrats. Kontrollen följer nu huvudramens navigationsbegäran och
publicerar inga formulärfynd från ett annat dokument, även om URL:en ligger kvar. Regressionen använder
riktig Chromium, läsvakt och axe med en kontrollerat kvarhållen URL; vanliga required-fel mäts fortfarande.
