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
