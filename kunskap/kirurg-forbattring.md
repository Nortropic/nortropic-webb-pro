# Kirurgens förbättringsloop

Status: gäller för den lokala, avgränsade förbättringsvägen. Införande sker genom ordinarie granskning/Git. Införandeobservation och inrapporterad eftereffekt kan versionsbindas; ingen automatisk driftsättning görs.

## Vad som händer

Befintlig spaning och Kundstarts överlämning ger observationer till Kirurgens befintliga vy. En observation beskriver
ett problem, källa och version. Diagnosen skiljer saknat underlag, tappad överföring, kunskap, metodkoppling,
verktygsåtkomst, implementation, bedömning och saknad verifiering. Konsekvens och beläggens styrka hålls isär.
En gammal källa eller en delidé kan vara relevant; ålder och popularitet bestämmer inte dess nyttovärde.

Registret är privat i `kirurgen/forbattringar/FORBATTRINGAR.json`, atomiskt och låst. Det ersätter varken
`kunskap/REGISTER.md` eller backloggen. `disposition` kan länka en befintlig backlogidentitet; ingen parallell
uppgiftstavla skapas. Samma uttryckliga problemnyckel och fas förenar signaler. Detta är inte automatisk semantisk
deduplicering av godtycklig text. Samma signalversion återanvänds; nytt innehåll bevaras och återöppnar parkerade
eller avslagna poster för bedömning. Stickprov tar även med bortsorterade poster, med en reproducerbar urvalsnyckel.

Kundstart verifierar aktuell överlämning mot ärendets källrevision och de deklarerade filernas bytes. Insamlat och
överfört kan mätas. Förstått, använt och levererat kan inte härledas ur detta. En senare kundrättelse kräver ny
överlämning. Ett äldre ersatt kvitto granskas inte mot senare kvittots aktiva filer. Observationens fel döljer aldrig
att själva överlämningen redan sparats. Automatiken kopierar metadata och hashade identiteter, inga kundsvar.
Manuellt inskriven observation är däremot privat fri text: håll den avidentifierad och skriv aldrig hemligheter.

## Spaning och källhälsa

`spana.py` använder den befintliga hämtaren med validerad anslutningsadress och omdirigeringsvakt. Varje hopp
förbrukar anropstaket och håller takten. Ett svar över bytetaket vägras, inte bokförs som en ny hel dokumentversion.
Dokumentets ordning, korta rekommendationer och kodexempel bevaras i jämförelsen. Tillagt, ändrat och borttaget
innehåll räknas; en ensam uppdateringsdatumrad är inte en ny rekommendation. Hämtat innehåll är analysdata,
inte instruktioner eller mandat att köra kod.

`kirurgen/spaning/HALSA.json` visar senaste försök, senaste lyckade hämtning, fel och innehållsversion per källa.
Misslyckat anrop behåller föregående lyckade tid. Oförändrat innehåll är inte ett fel. Ett försök som beror på en
spaningssignal kräver lyckad aktuell källa med samma version; ett oläsbart hälsoregister ersätts inte med tomt.
Den befintliga dashboardserverns spaningsklocka består. Ingen ny återkommande process har lagts till; utan den
serverprocessen finns ingen automatisk spaning. Källhälsan bevisar inte att hela externa källans innehåll har förståtts.

## Avgränsade försök

Dashboarden låter ägaren lägga till signal, diagnos, disposition och plan samt pausa försök. Läsning startar inget.
Planen anger fråga, jämförelse, förhandsbestämd framgång och försämring, provtyp, avgränsning, risk och ansvarig.
Den är inget körmandat. Lokala kommandot stöder regressionsprov; design, intervju och extern åtkomst har andra
beviskrav och får inte ersättas med ett grönt schema- eller stubbprov.

```sh
.venv/bin/python kontroller/kirurg_forbattring.py status
.venv/bin/python kontroller/kirurg_forbattring.py forsok < eget-forsoksuppdrag.json
```

Försöksuppdraget har exakt `pid`, `revision`, `mid`, `start_id`, `bas` och `andringar`. `bas` är ett fullständigt
commit-ID. Varje ändringsfil har `fore` (SHA256 eller null för ny fil) och `text`. Samma operations-id läser samma
beständiga resultat; annat innehåll med samma id nekas. Misslyckat och avbrutet arbete sparas också.

Ägaren måste separat tillhandahålla `kirurgen/AGARMANDAT.json`. Förbättringsverktygen skapar eller ändrar aldrig
mandatet. Filen har `schema: 1` och `mandat` med namngivna poster. Försökets åtgärdsklass är
`isolerat_regressionsprov`, med exakt fillista, `max_forsok`, `sekunder_per_variant`, numeriskt `giltig_till`,
`prov` och `prov_sha256`, `granskning: oberoende`, `aterstallning: kopian_kasseras` och `ansvarig`.
Ingen giltig standardpost följer med. Ett framtida klassmandat för aktivt införande kräver en separat kontrollerad
införandeväg; denna implementation kan inte ändra aktiv kod, publicera eller skapa ett sådant mandat åt sig själv.

Försöket kör en låst bas och en föreslagen ändring i egna registrerade kopior. Testfacit fryses utanför kandidatens
skrivrätt. Kandidaten får bara skriva egen `.tmp`, inte kod, metod, mandat, facit eller aktivt kundunderlag.
Processgränsen nekar nät, nya barnprocesser och signaler. En separat vakt håller försökslåset och väntar in barnet
även när styrenheten dör. Logg- och tidsgräns gäller; ingen obegränsad retry. Om styrenheten hårdstoppas kan en
registrerad tempkopia ligga kvar för den befintliga säkra städningen. Detta är inte bevis för att två samtidigt
hårdstoppade styr-/vaktprocesser alltid kan återhämta sig utan operativ tillsyn.

Högst ett försök körs samtidigt. Den beständiga totala budgeten reserveras före arbete och återställs inte vid
omstart, avbrott eller ändringsfel. Paus, utgånget/ändrat mandat, nya signaler, ändrad plan eller fallen källhälsa
stoppar det beroende försöket. Registrerat eller väntande kundbygge, globalt bygglås och Kundstarts modelllease
har företräde, också under provet. Okända externa arbeten kan inte upptäckas av denna kontroll.

## Vad ett resultat betyder

`regression_rattad` betyder att det låsta lokala facit reproducerade ett fel före och passerade efter. `oforandrat`,
`forsamrat` och `ofullstandigt` bevaras. Detta bevisar inte godtycklig testkods sanningsenlighet eller bättre
webbdesign. Oberoende kodgranskning behövs. Ändringsförslaget och loggarna ligger vid försöket; `inforande` är
`inte_infort` och `effekt` är `inte_observerad`. Det finns ingen HTTP-ingång för försök, införande, mandat eller shell.

Befintligt äldre `/kirurg`-intag har sin egen verktygslista och är inte denna avgränsade provprocess. Den nya
processgränsen får inte beskrivas som isolering av alla äldre intag eller som mandat att utöka deras åtkomst.
Införande sker tills vidare genom repots vanliga separata granskning och git-policy. Nattens utvecklingsmandat
omfattar inga pushar eller sammanslagningar; inga modeller eller externa tjänster har aktiverats av de lokala proven.

## Verifiering och kvarstående bevis

Riktade prov ligger i `kontroller/rokprov/revision/prov_kirurg_*.py` och `prov_kirurg_forbattring_webb.mjs`.
De omfattar riktiga lokala HTTP-anrop, Chromium, processgräns, samtidighet, avbrott och negativa fil-/mandatprov.
All data är syntetisk. Kundstarts modellresultat är testdubblar. Bevis och separat granskning registreras enligt
README:s rapportstruktur, inte i publik kunddata eller historiska domar.

Live-AI, intervjukvalitet, verklig källnytta och drift-/kundeffekt är egna kvarstående prov.
Ett sammanhängande lokalt förloppsprov får visa övergångar; det får inte kallas verklig kundprövning.

## Registrera separat införd ändring och uppföljning

Den ordinarie Git-vägen gör ändringen. Observatören `kirurg_uppfoljning.py` skriver bara privat metadata och kan
varken installera kod, godkänna sig själv, ändra mandat eller återställa arbetsfiler. Lokal CLI, ingen HTTP- eller
modellverktygsingång:

```sh
.venv/bin/python kontroller/kirurg_forbattring.py registrera-inforande < inforandeuppdrag.json
.venv/bin/python kontroller/kirurg_forbattring.py folj-upp < uppfoljningsuppdrag.json
.venv/bin/python kontroller/kirurg_forbattring.py registrera-aterstallning < aterstallningsuppdrag.json
```

`registrera-inforande` kräver `pid`, `revision`, `forsok`, `mid`, `granskning` och `version`. Försöket måste vara
klart med reproducerat regressionsfel före och godkänt efter, samma signaler/diagnos/plan och oförändrad patchfil.
Git måste ha exakt den angivna HEAD-versionen på mandatets gren, rent index/spårade arbetsfiler och precis den
provade ändringen sedan basen. Arbetsfilernas bytes jämförs också, så assume-unchanged inte döljer avvikelser.
Införandet binds till commit, trädhash, filhashar, prov, mandat och granskningskvitto. En upprepning av samma
registrering förbrukar ingen ny budget. Infört i Git betyder aldrig publicerat, driftsatt eller förbättrat.

Operatören tillhandahåller ett klassmandat i befintliga `kirurgen/AGARMANDAT.json`: `klass: observera_gitinförande`,
`gren`, exakt `filer`, `granskare` (tillåtna identiteter), `max_registreringar` (1–100), `giltig_till` (UTC-epok) och
`ansvarig`. Inget giltigt exempelmandat installeras. Samma skyddade filer som i försöksvägen är undantagna.

Separat granskning kommer från operatörens `kirurgen/GRANSKNINGAR.json`, med `schema: 1` och `granskningar` per id.
Kvittot har `forsok`, `version`, `andringar` (patchhash), `plan` (planhash), `skapare`, `granskare`,
`utfall: godkand` och `tid` (UTC-epok efter provslutet). Granskaren måste vara tillåten och en annan identitet än
skaparen. Dessa två filer är betrodda lokala operatörsunderlag, inte kryptografiska personbevis. De är utanför
försöksprocessens läs-/skrivrätt. Att bara skriva ett annat namn i ett modellresultat ger inget godkännande.

`folj-upp` kräver `pid`, `revision`, `version`, `utfall`, `bevis`, `omfattning` och `observator`. Exakt införd
Git-version och filinnehåll prövas igen. Utfallet (förbättrat, försämrat, blandat, oförändrat, ofullständigt eller
inte observerat) är en inrapporterad observation med belägg; verktyget kan inte fastställa dess sanningshalt eller
orsakssamband. Dashboarden visar denna avgränsning och versionsidentiteten, även negativa utfall.

`registrera-aterstallning` kräver `pid`, `revision`, `version` och `mid`. Operatören återställer via ordinarie Git
först. En efterföljande ren Git-version måste bära alla berörda filers före-hashar (nya filer vara borta).
Observatören ändrar ingenting, så den kan inte skriva över senare orelaterat arbete. Införande- och
uppföljningshistoriken behålls. Automatisk aktivering, automatisk rollback och skarp eftereffekt ingår inte i
provbevisen; de behöver faktiskt mandat och operativa förutsättningar.

Införandeobservationen verifierar alla spårade vanliga arbetsfiler mot Git-trädets blob-id och kör Git utan ärvda
Git-styrvariabler. Spårade länkar och specialfiler stöds inte här. Ospårade filer ingår inte i Git-intyget.
Vid återställning eller ett nytt införande-id blir aktuell effekt `inte_observerad` både för posten och försöket;
äldre versionsbundna uppföljningar bevaras som historik. Ingen tidigare förbättring ärvs till en ny version.
