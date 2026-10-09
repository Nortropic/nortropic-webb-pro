# Skapandeflödet

Ett designflöde för startsidan, samma kod och samma text vid varje ingång (Codex via ägaren 2026-10-05: tre designflöden,
där förbättringarna inte följde med mellan dem, blev ett). Orkestratorn är `kontroller/atelje.py`; de delar som alla
steg använder står i `kontroller/skapande.py`. Var flödet står i hela kedjan, från kundunderlag till leverans, och vem
som startar vad: `README.md`. Normalflödet är skissläget nedan; läget full, den äldre utforskningen och Figma-piloten
står i egna avsnitt. Ingångarna:

- **Ägarens prototyp:** `.venv/bin/python kontroller/prototyp.py <slug>`, utanför bygget. Läget följer ägarens senaste
  dom i domloggen. Ägaren dömer i dashboardens vy Prototyp.
- **Byggets steg 5.1:** `kor.sh` tar vid bara från en startsida som ägaren godkänt, som från ateljévinnaren; utan en
  stannar kor.sh före bygget och pekar på prototyp.py. `NWP_ATELJE=av` är nödvägen, där byggaren skriver KONCEPT.md
  själv.

**Normalflödet** (ägarens uppdrag 2026-10-09 ~17:53Z, ordagrant i minnet och sammanfattat i `BESLUT.md`, tillägget samma
dag): kundunderlag → kundförståelse → starka branschreferenser → visuell inspiration och användbara mallar och
komponenter → tio kundanpassade förslag → kundens val → riktad förbättring (Rätta, Omarbeta designen, Bygg ut) →
helbygge → verifierad leverans. Målet är en snabbare väg till hög kvalitet; antalet rapporter, lästa skills,
verktygsanrop eller varv är inget kvalitetsmått. Flödet startar från en ren designstart (`kunskap/ren-designstart.md`):
inget designmaterial från före 2026-10-09 finns i den aktiva miljön.

Sammanhållningen följer ett välgrundat val, och iterationen får ändra grundidén. Därför utforskas skilda grundidéer
först, och huvudreferensen blir den valda riktningens referens efteråt. Beställaren (ägaren, eller kunden med belägg)
väljer själv bland förslagen innan något förbättras; ingen panel utser en vinnare.

## Skissläget (standard): full verktygslåda, ren arbetsbänk

**Förberedelse före designen.** `prototyp.py <slug> --forbered` kör ett avgränsat pass i samma ateljéarbetare.
Verifierade verksamhetsuppgifter och kunduppdraget behövs, men ingen godkänd startsida eller installerad sajt.
Passet skriver först ett privat paket; hela paketet och oförändrade indata prövas före publicering. Äldre arbetsfiler
bevaras vid paketet. Ett äldre INNEHALL.md arkiveras så att det nya TEXTUNDERLAG.md faktiskt blir textkällan.
Fakta, kundönskemål, antaganden och kommersiellt accepterade villkor hålls isär. Paketet och kompetenskvittot finns
i `underlag/<slug>/atelje/forberedelse/`; FORBEREDELSE.json binder arbetsfilerna till indata. Ett avbrott mitt i
publiceringen är inte en klar förberedelse. Referensjakt och skiss startas därefter uttryckligen från Byggflöde i arbetsytan eller CLI.

**Återupptagning och material.** Skisskritiken binds till körning, kandidat, försök, projektets innehåll och aktuellt
underlag. Tidigare kritik och status följer med försöksarkivet; den används inte som ett nytt granskningsbevis.
En fotograferad kandidat omfattar också public/, src/assets/atelje/ och underlagets manifest. Vinnaren bär samma
material, och installationen av den godkända versionen ersätter dess materialområden så att borttagna filer inte
återkommer. Målkonflikter prövas före installationen. Underlagsändringar gör godkännandet inaktuellt. Detta binder
överlämningen till det bedömda exemplet; det bevisar inte att exemplet når ägarens designribba.

Tio förslag är ägarens beslut (2026-10-09; det tidigare förslaget att minska antalet är inte antaget). Första omgången
ger tio skisser med jämförbar omfattning: första vyn, den viktigaste innehållssektionen, navigationen och de
interaktioner som behövs för att förstå förslaget, genomarbetade i mobil och dator, med kundens rubriker, erbjudande,
bilder och kontaktvägar. Varje förslag utgår från en identifierad professionell förebild eller fungerande designgrund
(`utgangspunkt` i planen) och har en faktisk implementationsgrund (mall, komponenter, tema eller egen implementation;
`implementationsgrund`), och skillnaden syns i komposition, bildbehandling, typografi, innehållshierarki eller
interaktion; färgbyten på samma layout är inga olika förslag (`kandidater.planbrist`). Inga tio kompletta sajter byggs
före valet. Går tio inte att göra inom resurserna redovisas bristen (`brist_mot_begart`), utan kosmetiska dubbletter.

- **Ren arbetskontext.** Skaparen får uppdraget (designuppdraget, besökarens uppgift, den viktigaste sektionen,
  referensbilderna och vad de ska lära), kundens verifierade fakta och material, kundens aktuella domar och metodens
  kärna (`METOD-skiss.md`: kvalitetskraven, besluten med räckvidd, avgörandena mellan motstridiga råd och en
  förteckning över utdrag att slå upp i). Historiken, `LARDOMAR.md`, det privata originalet och beslutshistoriken slås
  upp när de besvarar en konkret fråga; de läses inte i förväg (`kunskap/designregler.md`, historik och smakdomar).
  Samma gäller `CLAUDE.md`, som laddas i varje nästlad session, och helbyggets uppstart.
- **Hela verktygslådan finns kvar:** skills med källa och licens, Refero, Mobbin, referensinsamlingen,
  webbläsarverktygen och kontrollerna. Uppgiften avgör vad som slås upp; inget krav på att allt läses.
- **Researchen** är gemensam före planen och återanvänder kundens befintliga referenspaket och tjänsterapport; nytt
  hämtas bara där materialet saknar något (för ett förslag högst fyra sajter och sex frågor, för en omgång med flera
  grundidéer högst 8 sajter och 14 frågor). En skapare kan begära en avgränsad
  komplettering en gång, inom sitt försöks tid.
- **Budgeten** är ett försöksvillkor: högst tre skisser samtidigt, högst 45 minuter per inledande skaparförsök med
  verktygsväntan, ett omförsök på 15 minuter bara vid ett identifierat tekniskt fel (bygget föll, bilderna saknas,
  sessionen föll), ingen förlängning för att nå antalet. Av försökets 45 minuter hålls 15 för den kritiska granskaren
  och skaparens svar: granskaren har högst 8 minuter (uppmätt 107 och 109 sekunder med kärnan, fyra bredder och menyn;
  `BESLUT.md`, tillägget 2026-10-07) och svaret minst 7. Fotograferingen har 3 minuter, och skaparen 27. Inget fast antal varv: varje varv åtgärdar en brist skaparen
  sett i sina bilder eller vid jämförelsen med referensen. En skiss som inte blir klar redovisas som ofullständig med
  skälet och det sparade arbetet; ett avbrutet försök sparas i `forsok-<n>/` och startas om i ett nytt projekt.
- **Före ägarens val** ingen granskningspanel och ingen förbättringsrunda. En intern granskare ser den renderade skissen
  när tiden räcker, med rollen kritik i metodkartan: sin egen förhandsvisning i 390, 768, 1280 och 1440 med menyn
  öppen, tangentbordet och reflow, detektorn och förebilder ur Refero och Mobbin, aldrig skaparens text, uppdrag,
  referenspaket eller kod. Skaparen svarar under "Svar på granskningen" i RIKTNING.md; granskarens omdöme och
  svaret visas först efter ägarens första beslut. De snabba kontrollerna (bygget, konsolen, spill, axe, siffror utan
  belägg i underlaget, menyn i 390 och 768, huvudreferensraden) markerar brister och ändrar aldrig uttrycket. Vyn visar
  skisserna neutralt, utan rekommendation eller poäng; ofullständiga står med.
- **Efter beställarens val** startar inget av sig självt. Den riktade förbättringen är ett av tre uppdrag, som
  beställaren ger och startar uttryckligen (steg 7): Rätta, Omarbeta designen eller Bygg ut. Hela startsidan, den
  relevanta undersidan och besökarens centrala flöde byggs som uppdraget Bygg ut, med DESIGN.md i takt med koden. Den
  godkända kandidatens kod blir leveransens startpunkt (`installera_godkand`, bygg-sajt steg 5.1), så att ingen nästa
  agent återskapar designen.
- **Redovisningen** (REDOVISNING.md) har total väntan, tid till första valbara skissen, tid och försök per kandidat,
  bristerna, det som tillfördes varje uppdrag och verktygen som användes, de ofullständiga och det som behöver
  mänsklig bedömning. Antalet lästa filer, anrop eller varv är inget betyg.

**Kompetenserna** (ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA"). Vilken roll som
arbetar i vilket pass, med vilken kärna och vilka alternativ, verktyg och MCP:er, och hur sessionerna når skills och
MCP:er, står bara i `kunskap/metodkarta.md` (inledningen och avsnittet Kompetenserna); `kontroller/kompetens.py` läser
kompetensblocken och ger samma block till uppdraget och till sessionens behörigheter. Var i flödet rollerna arbetar står
i stegen nedan. Också sessionerna som bedömer eller forskar har roller (ägarens ord 2026-10-07: "Du behöver ju fixa
luckan där med de verktyg vi har tillgängliga"): researchen, skisskritiken, jämförelsen och granskningens två pass i
läget full. En session utan roll står med ett prövbart skäl i metodkartans lista över sessioner utan block, och
`kompetens.py --prova` jämför listan med koden. Kvittot (kärnan läst hel, valda alternativ, skillverktygets anrop,
verktygens och MCP:ernas anrop med utfall) och före och efter står i REDOVISNING.md och i vyn efter ägarens första
beslut.

## Stegen (skissläget, `kontroller/kandidater.py`)

Vad varje steg ska besvara, vilket underlag det använder, vad nästa steg får och vad resultatet måste visa står i
`kunskap/metodkarta.md`; `kontroller/metod.py` levererar stegets utdrag med hash vid varje körning, och hashen följer
kandidaterna och granskningarna.

1. **Underlag och kundförståelse.** Verksamhetens fakta gäller och ändras aldrig: VERKSAMHET.json, RESEARCH.md med
   belägg, `kalla/`, egna bilder och textens sakuppgifter. Förberedelsen (`prototyp.py <slug> --forbered`) skriver
   KUNDFORSTAELSE.md före allt val av uttryck: erbjudandet och verksamhetens egna särdrag, målgrupperna och besökarnas
   viktigaste uppgifter, tjänster, kontaktmodell och förtroendebevis, verkliga texter, foton och tillgångar, det som
   saknas, och vad som är verifierat respektive antaget (`forberedelse.KUNDFORSTAELSE_RUBRIKER`, prövat före
   publiceringen). Kunder utan webbplats deltar med märkta textutkast och avsiktliga platshållare; påhittade omdömen,
   meriter och resultat förekommer aldrig. Varje senare session läser KUNDFORSTAELSE.md först. Designbesluten är grundidé, referensurval, palett, typografi, komposition,
   bildurval och beskärning, och rubrikernas form. De prövas mot ägarens domar (domloggen) och mot de prövade
   grundidéerna (historiken). Reglerna i fyra slag med räckvidd står i `kunskap/designregler.md`.
2. **Research.** Ett pass med rollen forska skriver antagandena om besökarna som kan ändra designen (underlag eller
   "ännu inte observerat", hur de prövas, vad som ändras), frågor till Refero och Mobbin (högst fjorton) och högst åtta
   nya sajter; det prövar territorierna med egna generiska sökningar innan frågorna skrivs, och FORSKNING.json bär kvittot.
   Sajterna omfattar både starka sajter i branschen och visuella förebilder utanför den. Referenssteget hämtar dem med
   belägg: `referens.py` ger en ny paketversion, `referenstjanster.py` sparar per körning
   tjänsternas svar ordagrant, varje Refero-stils hela dokument och skärmarnas hela bilder. En sajt eller fråga utanför
   kanalens form släpps med skälet, och resten körs; ingen fråga får nämna kundens namn, orter eller nummer.
   FORSKNING.md säger vad som är nytt och vad som återanvänds.
3. **Plan och planprövning.** Ett planeringspass skriver först branschgenomgången (hur de starka sajterna hanterar
   tjänster, förtroende, priser, navigation och kontakt, och deras svagheter; att något förekommer hos konkurrenter gör
   det inte till bästa praxis) och förebilderna utanför branschen, och sedan tio uppdrag (`NWP_KANDIDATER`, högst tolv)
   som besvarar kundens problem på olika sätt: innehållshierarkin, bildstrategin, typografin, navigationen och hur
   förtroende byggs. Varje uppdrag har en visuell utgångspunkt och en implementationsgrund (avsnittet Skissläget ovan).
   Varje uppdrag har en hypotes (varför lösningen passar verksamheten och besökaren), en namngiven huvudreferens ur
   researchen (den får vara utgångspunkt för layout, palett och typografi, ägarbeslut 2026-10-03; om namnet finns i
   researchen prövas och redovisas per kandidat) med kvaliteten som ska återskapas, vad den kräver och om kundens
   material bär det, antagandena den vilar på, referensbilder, undersidan, materialbehovet och de fynd som formade det.
   Ett uppdrag vars huvudreferens inte är "egen" avvisas i planen när ingen av dess referensbilder finns i kundens
   referenser (KANDIDATPLAN.json, Avvisade; `kandidater.referensbrist`): en misslyckad referensleverans följs inte av
   planering på den referensen, och planeraren får veta när researchen levererade med brister (FORSKNING.json,
   slutkoderna). Sedan hämtas uppdragens material (huvudreferensens stilpaket och Mobbins skärmar, UPPDRAGSMATERIAL.json), och
   planprövningen prövar uppdragen mot kunden, materialet och referenserna innan någon skiss byggs; titel, hypotes och
   huvudreferens står fast i prövningen (PLANPROVNING.md), men en invändning som gör ett uppdrag ohållbart blir en
   återgång: kompletterande research på specialisternas begäran, omplanering av de uppdragen med samma identitet (ny
   hypotes eller huvudreferens, referensbrist avvisas) och nytt uppdragsmaterial för dem, och sedan en andra prövning,
   en gång per plan (PLANPROVNING-runda-1.json; uppdraget 2026-10-08, 2E). Ett konstaterat problem bokförs alltså inte
   bara medan körningen fortsätter med samma låsta plan. Ger omplaneringen inget användbart uppdrag för en kandidat
   stoppas den (status fel med `atergang_fel` och invändningen sparad); skaparen får aldrig det förkastade uppdraget, och
   en körning som tas upp med Återuppta gör ett nytt omplaneringsförsök för den (R01). Prövningen är bunden till
   planversionen: PLANPROVNING.json bär `provade`, uppdragets sha256 för varje uppdrag som prövningen släpper till
   skaparen. Ett uppdrag som ändrats sedan dess, som det omplanerade vid en återupptagning, prövas igen innan skaparen får
   det (den tidigare prövningen bevaras i PLANPROVNING-tidigare-N.json, och de redan prövade uppdragen ändras inte), och ett
   uppdrag utan prövning av sin nuvarande version står stoppat (`planprovning_saknas`) tills en prövning finns (N01 i
   GR-20261009-natt-omgranskning-codex).
4. **Skissa.** Varje kandidat har en stabil identitet (k01–k12), ett eget Astro-projekt
   (`kunder/<slug>/kandidater/<id>/sajt`: sajtens nuvarande src/ och public/ utan tidigare sidor, kundens bilder, och
   node_modules som länk till sajtens) och en egen skaparsession med samma faktaunderlag; några körs åt gången
   (`NWP_KANDIDATER_PARALLELLT`, högst tre), och ingen kan läsa de andras kataloger: Read, Grep och Glob nekas dem, och
   de läsande skalkommandona nekas varje session som arbetar med en kandidat (`kandidater.andra_nekas`; skapandets egna
   verktyg och det egna projektet berörs inte). Skaparen skriver RIKTNING.md först
   och bygger skissen: första vyn, den viktigaste innehållssektionen, navigationen och de interaktioner som behövs för
   att förstå förslaget, inte hela startsidan och ingen undersida. Förhandsvarven görs med `--mellan` i 390, 768, 1280
   och 1440, och i varje varv läses bilderna och en referensbild (vad varven prövar: metodkartan, Avgörandena, Process).
   En kritisk granskare bedömer den renderade skissen när tiden räcker, med rollen kritik (blind för skaparens text,
   uppdrag, referenspaket och kod och för tidigare riktningar; i `underlag/<slug>` läser den bara briefen och kundens
   fakta och material, och domloggen och riktningshistoriken nekas som filer, ett beslut av Claude i väntan på ägaren:
   `kandidater.blind_nekas`, metodkartans block kritik; varje läsning med Read, Glob och Grep prövas dessutom när den görs
   mot sessionens tillåtelselista, `kandidater.blind_tillatet` och `kontroller/blindvakt.py`, så att en fil som tillkommer
   efter starten inte blir läsbar; sessionen startar i en egen tom arbetskatalog utanför motorns rot,
   `atelje.blind_arbetsyta`, där dontAsk nekar det som vakten inte tillåtit, så att också en krok som inte svarar
   öppnar ingenting): skaparens senaste bilder och sin egen förhandsvisning (`forhandsvisa.py --granskare`,
   bilderna i kandidatens `granskare/`, aldrig i skaparens varv), detektorn utan kodutdrag och förebilder ur Refero och
   Mobbin. SKISSKRITIK.json bär kandidatens version, det granskaren bevisligen såg (en tom eller saknad bild räknas
   aldrig som sedd) och kompetenskvittot, och skaparen svarar i en egen session ("Svar på granskningen" i RIKTNING.md).
   Den sessionen är ny, som en fortsättning är: den får kompetensens rader och steg 0 igen och sägs aldrig ha läst
   kärnan i en tidigare session; kvittot räknar sessionerna var för sig (motorinventeringen 2026-10-08, K06).
   Klar är skissen när den är byggd och
   renderad i 390, 1280 och 1440 och RIKTNING.md har huvudreferensen, idén, referenserna, det överförda och
   avvikelserna, de kvarvarande svagheterna, varven, materialet och kompetensernas synliga bidrag. Formulären postar
   till `/api/forfragan/` och landar på `/tack/` (lokal demonstration). Tiden och vad som gäller före ägarens val står
   under Skissläget ovan.
5. **Fotografera och de snabba kontrollerna.** Bygget körs innanför processgränsen; startsidan fotograferas i 390, 768,
   1280 och 1440, med menyns knapp klickad i 390 och 768, och axe prövar startsidan med menyn öppen och formulären
   skickade tomma. Koden bevaras i `kod/` och `kod-src/`, DESIGN.md bredvid och bilderna i `bilder/`; versionen är
   hashen över koden och DESIGN.md, så en ny fotografering av samma kod ger samma version. Ett hinder (bygget föll,
   startsidan eller bilderna saknas) gör skissen ofullständig med skälen; bristerna (konsolfel, spill, axe, siffror utan
   belägg, menyn, huvudreferensraden) markeras, och skissen går ändå att bedöma. Ett omförsök ges bara vid ett
   identifierat tekniskt fel.
6. **Ägarens val.** Vyn Prototyp visar alla kandidater med neutrala namn (Förslag A–L, slumpad ordning ur planens tid)
   och lika stora bilder, mobil och dator bredvid varandra eller en bredd i taget (surfplattan, och mellanbredden 1280
   när den finns); bilderna öppnas i full storlek, varje prototyp klickbar med sina undersidor, och markerade förslag
   står sida vid sida. Ägaren bedömer bilderna först, sedan referensen och sist redovisningen (ägarens uppdrag
   2026-10-06, punkt 8). Därför står två delar hopfällda efter bilderna, för varje förslag från början: huvudreferensens
   fångade startsida bredvid förslaget i 390 och 1440, och skaparens korta redovisning ur RIKTNING.md under rubrikerna
   "Idén", "Referenser", "Överfört och avvikelser" och "Kvarvarande svagheter" (en rubrik som saknas eller är tom sägs,
   inget fylls i). De tekniska kontrollerna står för sig under en rubrik som säger att de inte är ett godkännande av
   designen. Skisskritiken (granskarens omdöme och skaparens svar), planens titlar och körningens redovisning visas
   först efter ägarens första beslut. Ägaren väljer en eller flera för vidareutveckling, sparar en jämförelse, markerar
   det ägaren gillar per förslag (det följer med ordagrant till de valda), förkastar alla eller ber om en ny riktning.
   Kunden kan välja, begära ett uppdrag eller underkänna alla; ägaren för in kundens egna ord med källan `kunden` och ett
   belägg för var de står (`skapande.KUNDENS_BESLUT`), och en AI-bedömning bokförs aldrig som kundens. Godkännandet för
   helbygge och godkännandet för publicering är ägarens och egna beslut. Beslutet binds till kandidat och version, och en
   tidigare bevarad version kan väljas (`kandidater.valbara_versioner`). Valet startar ingen körning. Nästa tillåtna
   handling startas uttryckligen i arbetsytan (Byggflöde) eller med prototyp.py, och dess benämning säger vad som
   startas; alla använder samma körlogik (`README.md`, Kedjan).
7. **Riktad förbättring: Rätta, Omarbeta designen eller Bygg ut.** Beställaren ger ett uppdrag på en vald kandidat
   (arbetsytan: Ändring; Prototyp; eller `skapande.py dom <slug> --beslut uppdrag --uppdrag ratta|omarbeta|bygg_ut
   --resultat … --omfattning … --bevara … --kandidater kNN[@version]`): versionen det gäller, det önskade resultatet,
   omfattningen och det som ska bevaras (`skapande.uppdrag_giltigt`), och startar det uttryckligen ("Starta uppdraget:
   …", läget valda i prototyp.py). Kandidaten arbetas i sitt eget projekt från den versionen (`kandidater.forfina_kandidat`):
   **Rätta** åtgärdar de angivna bristerna utan nya sidor, sektioner eller funktioner; **Omarbeta designen** ändrar
   komposition, bildregi, typografi, rytm och hierarki inom avtalat innehåll, med frihet att byta en svag grundidé;
   **Bygg ut** skapar de överenskomna sektionerna, undersidorna och funktionerna i kandidatens form. Sidorna före och
   efter prövas mot omfattningen (`omfattningsbrister`): en rättelse eller ett designomtag som lägger till sidor förs inte
   vidare. Varven är brist, ändring och efterkontroll, utan minsta antal. Specialistpassen görs bara när uppdraget begär
   dem, ändrande eller bedömande (`specialisterna`; Rätta: inga, Omarbeta designen: granskningen bedömer, Bygg ut: båda
   ändrar), och återkopplingen har formen bild, version, element, tillstånd, avvikelse och kodkoppling (`FYND_SCHEMA`,
   `kodkoppling`). Ett pass som själv bedömer sin ändring som sämre utan teknisk nödvändighet återställs. Sist jämför en
   separat, blind granskare med rollen kritik versionerna före och efter som X och Y utan skaparens förklaring
   (`fore_efter`, FORE-EFTER.json), och regeln (`fore_efter_regel`) avgör: bättre eller likvärdig förs vidare, sämre
   men tekniskt nödvändig kräver fortsatt lösning, sämre utan teknisk nödvändighet återställs (efter-versionen står
   bevarad och valbar), och oklart står som oklart. Den förbättrade sidan fotograferas helt (startsidan i de fyra
   bredderna och undersidorna i 390 och 1440, med axe) och DESIGN.md prövas efter sista passet. Faller uppdraget,
   eller gör det inget eget varv, står versionen det gällde kvar.
8. **Godkännande och överlämning.** Ägaren godkänner en förfinad kandidat för helbygget. Den byggs som vinnare i en
   tempkatalog och byts in först när domen är skriven (`atelje/vinnare/`: alla sidor, DESIGN.md, bilderna och hasharna
   i VINNARE.json i granskarens format), och godkännandet binds till hashen över alla sidorna. Före bygget lägger kor.sh
   sidorna, komponenterna och DESIGN.md i sajten (`atelje.installera_godkand`; de ersatta flyttas med sin väg till
   `kunder/<slug>/startsida-ersatt/`), och bygget tar vid från dem (bygg-sajt steg 5.1) utan att skriva om godkännandets
   underlag (`skapande.UNDERLAGSGRUND` och katalogerna; Write, Edit och sandlådan nekar det). Utan godkänd startsida
   stannar kor.sh före bygget. Vad som sedan gäller för helbygget, exporten och leveransen: `README.md`.

Kandidatens status i ägarens ord: under arbete, klar för ägarens bedömning, vald för vidareutveckling, förkastad,
förfinad, godkänd för helbygge (och ofullständig eller föll, med skälen). Ett avbrott förstör inga klara kandidater:
`atelje.py <slug> --fortsatt` tar bara det som inte är gjort. Stoppas körningen, eller faller den, märks varje kandidat
som körningen satte under arbete "avbruten vid stoppet" eller "avbruten av fel", med tiden (fältet `avbruten_vid`), och
en session som stoppet avslutade får sluttid och utfall i sessionsförteckningen (`atelje/sessioner/`). Efter ett stopp
skriver ingen kvarlevande tråd i kandidaternas status. Återupptagningen sparar det avbrutna försöket i `forsok-<n>/` och
gör om det, som förut. En halvgjord förbättringsrunda eller förfining är märkt med
sin föreversion och återställs; en körning vars arbetare dött tas aldrig om som en ny körning (prototyp.py och atelje.py
säger att den avbröts och pekar på `--fortsatt`), och ägaren dömer först när den tagits upp (vyn och `skapande.py dom`
vägrar under ett avbrott). Kandidatflödet känns igen på ateljén (KANDIDATPLAN.json, `kandidater/`), så en körning som
föll tidigt fortsätter i kandidatflödet, aldrig i den äldre utforskningen. En ny plan arkiverar förra körningens projekt
i `atelje/foregaende/`.

## Läget full (tillfällig växel)

`NWP_KANDIDATLAGE=full` ger det tidigare förvalet, för jämförelse och återställning. Växeln tas bort när ägaren dömt
skissläget (BESLUT.md 2026-10-05, kväll). Körningens läge står i planen, så en återupptagning följer körningen.
Skillnaderna mot stegen ovan:

- Ingen planprövning före skaparna.
- Skaparen bygger hela startsidan och undersidan och gör förhandsvarv i 390 och 1440 (`--mellan` också 768 och 1280),
  utan minsta antal varv. Undersidan fotograferas i 390 och 1440. Bygger kandidaten inte, eller saknas undersidan eller
  huvudreferensraden, är den ofullständig med skälen, och den får ett andra skaparförsök med bristerna som kritik.
- **Granskning i två pass och en förbättringsrunda före ägarens val.** En granskare (en annan modell än skaparen som
  standard, `NWP_KANDIDAT_GRANSKARE`) bedömer först bilderna, tillgänglighetsträdet och axe mot besökarens uppgift i
  briefen, med skisskritikens blinda roll kritik: utan uppdraget, skaparens anteckningar, referenspaketet och koden
  (sessionen nekas dem): första intrycket, om uppgiften går att genomföra, och avvikelserna som krav (kvalitetskrav,
  hinder för uppgiften) eller smak. Sedan läser den motiveringen med rollen motivering och märker vilka avvikelser som
  är avsiktliga och välgrundade. KRITIK.json bär båda passens kvitton. Läste den inte de första vyerna, eller går läsningen
  inte att pröva i transkriptet, styr granskningen ingenting. Förbättringsrundan rättar bara krav som inte är
  välgrundade val, och axe:s allvarliga fynd; smak rättas inte före ägarens val. Föreversionen bevaras med bilderna;
  blir den förbättrade ofullständig återställs föreversionen, och annars granskas den förbättrade igen.
- **Jämförelse:** en granskare med rollen jamforelse ser alla kandidaters första vyer och hela sidor och pekar ut falsk
  variation; JAMFORELSE.json bär kvittot.
- I ägarens val visas panelens granskning efter första beslutet, med före och efter en förbättringsrunda, där ägaren
  kan säga vilken som är bättre och välja föreversionen.
- Efter förfiningen körs ingen ny panelgranskning: vyn och REDOVISNING.md säger att panelens granskning gäller
  versionen före förfiningen, och ägaren bedömer den nya själv. Kompetenspasset tillgänglighet och visuell granskning
  (steg 7) är ett redigerande pass, ingen panelgranskning.

## Den äldre utforskningen (nödväg)

`NWP_KANDIDATFLODE=av` ger den äldre vägen: en skapare tar fram tre riktningar i samma session (`atelje-N`-sidor i
sajten), tre domare väljer eller förkastar dem, den valda förfinas och döms före mot efter, och ägaren dömer slutet
(godkänd, putsa eller ny riktning). Den finns kvar för återupptagning av äldre körningar och som nödväg.

## Figma (pilotprov, inte normalflödet)

Ägarens uppdrag 2026-10-06 (ordagrant i minnet; BESLUT.md, tillägget om Figma-metodprovet) prövar Figma som visuell
arbetsyta i ett avgränsat metodprov med tre moment, som prövas var för sig: **A**, en representativ komposition ur en
stark, namngiven referens återskapas noggrant med material vi får använda; **B**, kompositionen anpassas till kundens verkliga innehåll och material; **C**, den valda
designversionen överförs till fungerande webb och jämförs med webbläsarens rendering i samma bredder.

- Normalflödet går utan Figma: ingen kod i repot slår på Figma-pluginen eller anropar Figma, och flödets sessioner
  nekas varje MCP-anrop utom Refero och Mobbin (`kunskap/metodkarta.md`).
- Pilotens material är arkiverat vid den rena designstarten 2026-10-09 och kan återställas ur arkivet; piloten startas
  bara om genom ett beslut av ägaren. Dess sessioner slog på Figma-pluginen i sin egen `--settings` och hade kundvakten kvar, men
  körskripten ingår inte i repot, och ingen kod prövar vad som laddas upp till Figma (kundvakten gäller Refero och
  Mobbin).
- Privat kundmaterial laddas upp bara till ett nytt projekt i ägarens team, bara för den kund som ägarens besked
  2026-10-06 gäller, med metadata borttagen (foton utan EXIF och GPS), texterna som de står i underlaget och inga
  uppgifter om privatpersoner utöver det som redan står på kundens sajt. Det ger ingen allmän rätt att föra
  kundmaterial till externa tjänster.
- Inget i leveransen är verifierat genom piloten: helbygget, exporten, kundrepot och driftsättningen prövas inte av den.
  Figma blir en del av normalflödet först genom ett beslut av ägaren.

## Domloggen och vad en dom återöppnar

`underlag/<slug>/DESIGNDOMAR.jsonl` har en rad per dom: tid, källa, beslut och text ordagrant. Loggen arkiveras aldrig av
flödet; den rena designstarten 2026-10-09 flyttade de gamla loggarna till återställningsarkivet efter ägarens uppdrag,
med manifest och sha256 (`kunskap/ren-designstart.md`).
Nästa körning läser den själv, och prompterna börjar med ägarens senaste domar. Vyn Prototyp skriver ägarens dom.

Källan är avsändaren (ägarens uppdrag 2026-10-07, punkt 7). Typerna och definitionerna står på ett ställe i koden,
`kontroller/skapande.py` (`AVSANDARTYPER` och `KALLOR`):
- ägarens egna ord och beslut: källan `ägaren`, eller `ägaren via Codex`, som bara betyder ägarens egna ord ordagrant
  förmedlade och kräver ett belägg (fältet `belagg`: var ägarens egna ord står);
- kundens egna ord och beslut: källan `kunden`, med ett belägg för var kundens ord står; den gäller kundens val,
  uppdrag och underkännanden (`skapande.ar_kundens`), aldrig godkännandet för helbygge eller publicering;
- Codex bedömning (`Codex`), Claudes eller skaparens bedömning (`skaparen`), en annan granskares bedömning (`panelen`),
  ett maskinellt mätresultat (`mätning`) och en hypotes (`hypotes`);
- en vidarebefordrad AI-bedömning (`vidarebefordrad AI-bedömning`): en bedömning av Codex, Claude eller en annan modell
  som ägaren skickat vidare. Den är en egen källa och aldrig ägarens beslut, också när den är skriven i första person.

Bara ägarens egna beslut räknas (`skapande.ar_agarens`), av godkännandet, läget, stoppvakten, blindningen, omtaget och
slutposterna. En äldre rad skrivs aldrig om: `ägaren via Codex` utan belägg står som "ej belagd" och räknas inte. Ett
belägg i efterhand fästs vid raden i bilagan `underlag/<slug>/DESIGNDOMAR-belagg.jsonl`, bunden till radens sha256
(`.venv/bin/python kontroller/skapande.py belagg <slug> --rad <radnummer> --belagg "<var ägarens egna ord står>"`;
radnumret ur `skapande.py visa`): raden får ingen ny tid och blir ingen ny dom, utan räknas som ägarens från och med då.
Bara en rad `ägaren via Codex` kan få ett belägg; källan `ägaren` behöver inget, och en vidarebefordrad bedömning är
aldrig ägarens. En bilagerad som inte går att läsa syns i `skapande.py visa` och räknas inte.

En dom som kom på annat sätt förs in ordagrant med
`.venv/bin/python kontroller/skapande.py dom <slug> --kalla … --beslut … --fil <text>`. För ägarens egna ord, utanför
dashboarden, krävs `--belagg`, och en bedömning som ägaren vidarebefordrat förs in med `--kalla "vidarebefordrad
AI-bedömning"`. Båda vägarna går genom `atelje.doma`: bara en klar körning kan godkännas, en pågående körning döms inte,
ett godkännande prövas innan domen skrivs, och en annan dom från ägaren drar tillbaka det. Under ett
bygge är loggen låst (kor.sh, `chflags uchg`), så domen skrivs när bygget är klart; en ändring under bygget ger
slutkod 3. Finns tidigare designbeslut utan dom, eller en dom som inte gäller någon körning i skapandeflödet, vägrar
prototypen att gissa läget.

Loggen läses på radslut och inget annat (`skapande.jsonl_rader`). En dom med U+2028, U+2029 eller U+0085 i texten
räknas, och radnumren i omtagets kvitto är filens egna (GR-20261007-r100-om#KAN-A). En rad som inte går att läsa står med
plats och skäl (`skapande.domlogg`, i ateljéns slutpost och i `skapande.py visa`) och hoppas aldrig över tyst; en rad
som är JSON men ingen dom räknas också som oläsbar. Står den efter ägarens senaste läsbara dom gissar ingen förbi den,
eftersom ägarens senare beslut kan stå där: läget stannar, godkännandet gäller inte och stoppvakten låter inte bygget
fortsätta. Vägen vidare är ett nytt beslut från ägaren efter raden (vyn Prototyp, eller `skapande.py dom` med belägg),
som gäller från sin rad, eller ett uttryckligt läge (`--ny-riktning`, `--putsa`, `--om`, `--valda`); raden skrivs inte
om av sig själv. En ny dom efter en avbruten skrivning hamnar på en egen rad.

- `ny_riktning` återöppnar alla designbeslut, aldrig fakta. `kontroller/atelje.py <slug> --ny-riktning` (eller
  prototyp.py) sparar först det ägaren bedömt (ägarens beslut 2026-10-07, `BESLUT.md`). Varje kandidat som ägaren dömt i
  körningen sparas i `underlag/<slug>/omtag/<stämpel>/<kandidat>/<v12>/` med skärmbilderna, versionshashen, domen och
  underlaget som hashen räknas om ur, och `KVITTO.json` har sha256 för varje fil. Vinnaren, slutdomens bilder, tidigare
  körningars arkiv och en äldre prototyp sparas i `omtag/<stämpel>/atelje/` och `omtag/<stämpel>/prototyp/`. Det finns ett
  undantag: omgångarnas bilder i den äldre utforskningen med riktningar sparas ännu inte (GR-20261007-r100-om#BÖR-3).
  Faller sparandet raderas inget. Sedan för den
  in den dömda riktningen, eller kandidaterna ägaren såg, i historiken med domen och en pekare till det sparade. Sist raderar
  den REFERENSER.md, KONCEPT.md, ateljén, äldre prototyper, förhandsvarven, tvåan och hela `kunder/<slug>/sajt` och
  `kunder/<slug>/kandidater` (ägarens beslut 2026-10-06: inget arkiv), också en godkänd och helbyggd sajt. Fakta,
  bilder, texten, referenspaketen, domloggen, historiken och leveransen (`kunder/<slug>/kundrepo`) står kvar. Sajten
  görs om ur mallen. Utan en dom som gäller körningen raderas inget ägaren sett; förra körningens kvarlevande processer
  avslutas före raderingen.
- `putsa` behåller riktningen; i den äldre utforskningen körs förfiningen och slutdomen igen, med domen som kritik, och
  förra slutdomen och redovisningen arkiveras först.
- `godkand` lämnar över till bygget.
- Kandidatflödets beslut bär kandidaterna med sina versioner och det beställaren gillade per kandidat (`delar`): `valj`
  väljer för vidareutveckling och startar inget (en vald tidigare version tas fram när det startas uttryckligen),
  `uppdrag` är Rätta, Omarbeta designen eller Bygg ut (steg 7), `jamfor` sparar en jämförelse utan att köra något, och
  `forkasta` förkastar alla och stannar tills beställaren ber om en ny riktning. `putsa` i kandidatflödet är ersatt av
  uppdragen (2026-10-09) och stoppar läget med en hänvisning till dem. En dom via Codex kan namnge förslagen:
  `skapande.py dom <slug> … --kandidater "Förslag C,Förslag F"`. Ett omtag efter kandidatflödet för in varje kandidat
  beställaren såg i historiken, med det som gillades i den.

Ett tidigare designval, till exempel en färg, är inget förbud. Ett drag ur en underkänd grundidé behöver ett skäl ur
verksamhetens material, och skälet ska också svara på kritiken mot den.

**Arbetsroten** (R06; beställningen i BESLUT.md, tillägget 2026-10-07 punkt 3–4): med `NWP_ARBETSROT=kundrepo` startar
kundens arbetssessioner i kundprojektets eget repo (`kunder/<slug>/kundrepo`, `kontroller/kundrepo.py`) med dess korta
CLAUDE.md: kandidatskissen, kandidatförfiningen och de andra sessionerna i skapandeflödet (med slug), de äldre vägarna
med riktningar, utforskningen, förfiningen och panelen (med `arbetsslug`, utan MCP:er som förut), och helbygget genom
kor.sh (`kontroller/arbetsrot.py`, med projektets krokar, stoppvakten och commitvakten, i `--settings`). Motorns skills och
filer nås genom `--add-dir`, varje regel, sökväg och kommando görs absolut (`atelje.regel_absolut`, `text_absolut`), så att
datagränserna gäller oförändrade, och sessionen skriver aldrig i kundrepot (Write och Edit nekas där, och sandlådan nekar
Bash det). Ett kundrepo med egna Claude Code-inställningar används aldrig som arbetsrot. Granskarna i helbygget
(`granska.py`) är domare, inte arbetssessioner, och har motorns rot. Växeln är av som standard: det verkliga förmågeprovet
2026-10-09 (`kontroller/formagoprov.py`, S1) visade att motorns CLAUDE.md kommer med i kontexten ovanifrån, eftersom
kundrepot ligger under motorns rot; skillen, briefen, kandidatgränsen och skrivförbudet i kundrepot höll. Skissens sparade kvitto bär hela
kvittoformen, och kärnan står som läst bara när varje session observerades (R03); materialsteget nås av rollen
komposition genom ett kandidatavgränsat verktyg (`material.py <slug> --kandidat <id>`; R05) som prövar den slutligt
tolkade kandidaten och visar och använder bara kandidatens egna och det uttryckligen gemensamma kundmaterialet; registret
läses aldrig direkt (N02).

**Det aktiva urvalet** (ren start för Nortropic 2.0, ägarens uppdrag 2026-10-08, del 2): `underlag/<slug>/atelje/URVAL.json`
(`kontroller/urval.py`) skrivs när en körning startar och säger vilken historik som är inkopplad. Standard är av: andra
kunders byggbilder når inte granskaren (`granska.tidigare_byggen`), UPPTAGNA-VAL.md ur tidigare byggen når inte
agenterna (`atelje.underlag_rader`, startkontrollens styrning), planen läser inte RIKTNINGSHISTORIK.json i förväg
(`riktningshistorik`; den slås upp vid en konkret fråga), och äldre domar styr bara det de uttryckligen beslutar
(designregler.md, kundens aktuella domar efter senaste ny_riktning). Ett uttryckligt val (`urval.py <slug>
--tidigare-byggbilder pa`) kopplar in dem för just den kunden och står kvar vid nästa start. Urvalet bär också det
aktiva referenspaketet och kalibreringsankarnas hash som kvitto. En ny slug, en ny riktning eller flyttade filer är
inte ett urval. Historiken raderas inte: den slås upp när den besvarar en konkret fråga.

`underlag/<slug>/RIKTNINGSHISTORIK.json` samlar prövade grundidéer: namn, huvudreferens, drag, utfall (vald eller
förkastad av panelen, lämnad av skaparen, underkänd av ägaren) och kritiken. Ateljén skriver efter varje panel och vid
TILLBAKA; omtaget skriver ägarens dom.

## Avbrott

Föll en körning tar `.venv/bin/python kontroller/atelje.py <slug> --fortsatt` vid efter den senaste klara fasen (i
kandidatflödet: stycket efter stegen ovan). Körningens slutpost säger om den stoppades eller föll, i vilket steg och när
(Körspåret nedan). Startlåset `underlag/<slug>/.atelje-start.las` tas aldrig bort av någon kod: en raderad låsfil
skulle låta nästa start låsa en ny inod fritt (GR-20261008-r117-claude#B10). Ägarens stopp är `atelje.py <slug> --stoppa`: arbetaren får SIGTERM (SIGHUP och SIGINT är samma
stopp), avslutar sina sessioner med deras processträd, märker kandidaterna under arbete och skriver posten; sessioner
som överlevt arbetaren (kandidaternas `session_pid`, och förteckningens poster utan slut, som skisskritikens) avslutas
av `--stoppa` och får slut och utfall. Läget full prövar stoppet efter varje session, som skissa gör. Ett annat
avbrott i arbetaren (SystemExit) slutar också som fel med sessionerna avslutade, så statusen säger aldrig att körningen
pågår. I den äldre utforskningen tar den vid i omgången som föll, med samma kritik
som första gången (skaparens TILLBAKA.md eller panelens VAL.md), och i en putsning vid förfiningen eller slutdomen mot
samma före. En avslutad körning (klar, förkastad, tillbaka) tas aldrig upp igen, och varken `--fortsatt` eller
`--bara-domare` körs när ägaren dömt efter körningen; där avgör ägarens dom nästa steg. Det som den äldre utforskningen
flyttar undan, äldre riktningsbilder och en tidigare vinnare, hamnar i `atelje/foregaende/`. Inget raderas.

## Research på begäran

Före planen gör kandidatflödet sin egen research (steg 2) med en bredare kanal: samma form, högst åtta sajter och
fjorton frågor (`skapande.kanal_fel(…, bred=True)`). Under arbetet kan skaparen skriva
`underlag/<slug>/atelje/kandidater/<id>/KOMPLETTERING.json` (varför, och ett referensuppdrag och/eller frågor till
Refero och Mobbin) och avsluta sessionen. Orkestratorn kör det befintliga referenssteget: `kontroller/referens.py` ger
en ny, komplett paketversion som ärver den förra, och `kontroller/referenstjanster.py` söker i tjänsterna med belägg.
Sedan startar en ny session med resultatet. Det får ske högst en gång per kandidat: sessionerna efter researchen, och
förbättringsrundan och förfiningen, får varken erbjudandet eller rätten att skriva en begäran, och en begäran som ändå
finns sparas obesvarad i kandidatens `kompletteringar/` (i den äldre utforskningen två per omgång och fas, i
`underlag/<slug>/atelje/KOMPLETTERING.json`). Skaparens egna sessioner
har inget eget nät, så begäran är deras enda kanal ut, och dess form begränsas (`skapande.kanal_fel`): högst tre
kandidater med ursprungsadresser i korta etiketter (å, ä, ö i punycode), högst fyra sidvägar per kandidat med högst
fyra led (å, ä, ö procentkodade) utan frågesträng, och högst tre frågor på högst 160 tecken utan adresser. Kanalen är
smal, inte stängd: värdnamnet och vägarna går ut. Skaparens egna sidor når inget nät när de fotograferas
(inspektionen släpper bara sidans eget ursprung).

## Metoden per steg

`kunskap/metodkarta.md` är den enda källan för båda vägarna: vad steget ska besvara och visa, vilka skills och
kunskapsfiler som stöder research, plan, skapa, granska, förfina och text, vilka avsnitt och rader av dem, och hur
motsägande råd avgörs (företrädet i `designregler.md`; underlaget med citat i `kunskap/skillkrockar.md`).
`kontroller/metod.py` levererar stegets utdrag till kandidatflödet med hash, och låset stoppar leveransen när en källa
ändrats; den äldre utforskningen räknar upp samma källor (`skapande.metodrader`, `skapande.metod_filer`). Vilka
verktyg sessionerna har, och hur läsningen prövas och redovisas skild från tillämpningen, står i metodkartans inledning
och avsnittet Kompetenserna.

## Körspåret

Varje körning får en slutpost, `kunder/<slug>/atelje/korningar/<körning>/SLUT.json` (`kontroller/ateljeslut.py`; ägarens
uppdrag 2026-10-07, punkt 4), i helbyggets form: rapporthuvudets fält, de fem tillstånden var för sig, slutkoden,
bristerna, nästa steg och länkarna. Arbetaren skriver den vid normalt avslut, fel och stopp, och när startkontrollen
stoppar starten. Bredvid ligger körningens STATUS.json och REDOVISNING.md, så nästa körning skriver aldrig över dem
utan att den förra körningens version står kvar. Posten binder ihop körningen, kandidaterna med sina versioner, repots
commit, METOD.json:s sha256, skisskritiken och vem som gjort den (inte dess innehåll), ägarens beslut med avsändaren,
stoppet eller felet med steget, och tiden till första valbara skiss. Platsen för kompetenskedjan står som "inte
observerat". En start som stannar före körningen får en kort post (slutkod 2), och en körning utan post (en dödad
arbetare, eller en körning från före posterna) får sin i efterhand innan nästa start skriver över dess status. Stoppar
startkontrollen en ny start skriver den startens egen post (slutkod 4), som inte ersätter den förra körningens post,
och prototyp.py:s besked och slutkod kommer ur den direkt. En körning som slutar utan en enda valbar kandidat får
slutkod 6: ägaren har inget att välja bland. Ägarens `valj`, `jamfor` och `putsa` står i posten som ej bedömt med vad
beslutet betyder; `forkasta` och `ny_riktning` som nej, `godkand` som ja.
`atelje.py` och `prototyp.py` skriver beskedet ur posten och ger dess slutkod: 0 klar, 2 ingen körning startades, 4 föll,
stoppades eller avbröts, 5 väntan slut medan körningen pågår (det vanligaste, eftersom skisserna tar längre tid än
väntan), 6 ingen startsida att bygga vidare på. `.venv/bin/python kontroller/ateljeslut.py <slug>` visar den senaste
posten, prövad mot domloggen nu.

I kandidatflödet sammanställer REDOVISNING.md researchen (nytt och återanvänt), varje kandidat (status, skäl, varv,
sessioner, minuter, listpris, granskningens nivå), kandidaterna som föll, falsk variation och materialbehoven; ägaren
ser den efter sitt första beslut. Huvudet säger körningens utfall: klar, eller steget och stoppet eller felet. Tiden
till första valbara skiss sätts när den första kandidaten blir valbar, också om körningen stoppas före resten; i en
äldre körning utan fältet räknas den fram ur kandidaternas statuslogg och märks som framräknad. I den äldre
utforskningen skrivs REDOVISNING.md ur sessionernas transkript
(`kontroller/bildkedja.py`):

- metodkvittot: vilka metodfiler och skills som lästes före första skrivningen;
- läsningen per förhandsvarv i ordning: varvets fyra bilder och minst en referensbild, lästa efter varvets
  förhandsvisning och före nästa ändring;
- researchen;
- panelernas domar med läsning;
- slutdomen före mot efter.

Claude Codes medietak (omkring 24 MiB bilddata per anrop) tränger undan de äldsta bilderna ur kontexten. Därför läses
huvudreferensen om i varje varv. Ett räknat antal bildläsningar är inget belägg för en jämförelse.

Var körningens rapporter och bevis hör hemma i övrigt: `README.md`, Var information finns.

## Sandlådan

Skapandeflödets sessioner har ingen egen sandlåda än: flödet körs utanför den, före bygget. Sessionerna har bara sina
namngivna verktyg och inget eget nät, och sandlådans lista över hemligheter nekas dem var de än ligger
(`atelje.NEKAS`, `Read(//…)`; ägarens egna regler läses inte i en nästlad session). Läsförbuden gäller Read, Grep och
Glob men inte skalets egna läsare, så de läsande skalkommandona (`kandidater.LASANDE_SKAL`) nekas varje session som
arbetar med en kandidat. Paket installeras bara med `kontroller/typsnitt.py` (Fontsource, namnen prövade,
`--ignore-scripts`). Research går genom referenssteget. I kandidatflödet skriver skaparen med sina verktyg i
kandidatprojektets hela src/, RIKTNING.md och en begäran om komplettering, och förfiningen dessutom i projektets
DESIGN.md (`kandidater.verktyg` och `kandidater.forfina_verktyg`); i den äldre utforskningen (`NWP_KANDIDATFLODE=av`) bara sidorna, RIKTNINGAR.md,
KOMPLETTERING.json och urvalet, och förfiningen bara sajtens src/, DESIGN.md och sina tre filer. Det är
en gräns för verktygen, inte för koden: sidorna är kod som körs när sajten byggs (Astros frontmatter). Därför körs varje
bygge av skaparens sidor innanför processgränsen (`kontroller/processgrans.py`): förhandsvisningen, fotograferingen och
slutdomen. Där skrivs bara i det projekt som byggs (sajtens eller kandidatens katalog) och körningens tempkatalog, aldrig i
underlag/<slug> med domloggen och VINNARE.json, och bygget når inget nät: inte localhost, där dashboarden tar emot
ägarens domar, och inte namnuppslag (`processgrans.py --utan-nat --skrivbar <projektet>`). En kandidats bygge har
dessutom en läsgräns, mätt med ett verkligt bygge (`processgrans.lasgrans`; BESLUT.md, tillägget 2026-10-07 om
byggets läsgräns per kandidat): sidans kod läser bara kandidatens eget projekt, sajtens delade node_modules,
kandidatens egen temp, systemets delar och repots .gitignore och .git. De andra kandidaterna, underlaget med skaparens
text, sajtens grund, resten av repot och hemkatalogen är stängda, också när kritiken bygger kandidaten
(`forhandsvisa.py --granskare`), så kandidatens direkta filåtkomst är avgränsad även vid bygget. Kund- och kandidatrötterna måste vara förankrade utan länkar. Kandidatens angivna id bevaras före länkupplösning; länkar till andra projekt och skiftlägesalias i kundträdet vägras. Reporotens `/tmp`-alias tillåts. Sajtens eget bygge har ingen läsgräns. Byggen i samma kunds
projekt köas (`kunder/<slug>/.bygglas`), liksom typsnittsinstallationerna. Kandidaternas projekt delar sajtens
node_modules. Där skriver deras byggen bara i Vites och Astros cacher, och det ett bygge lämnar i dem kan nästa
kandidats bygge läsa; Vites förbuntade paket därifrån kör bygget inte (prövat 2026-10-07). Det är samma gräns som för
sajtens eget bygge, nu delad av fler skapare. Ett sandlådat bygge (`NWP_SANDLADA=pa`)
kräver därför en godkänd startsida och tar vid från den. Finns Kundstarts ärendelager kräver kor.sh sandlådan; Byggflöde
prövar det före starten (`flodesstart.startmiljo`) och visar startmiljön vid knappen, så att starten nekas där med
skälet i stället för i kor.sh efter att den registrerats (F07). Nästlade sessioner skriver aldrig i ägarens automatiska minne
(`kontroller/nastlad.py`).
