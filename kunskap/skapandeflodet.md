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

Sammanhållningen följer ett välgrundat val, och iterationen får ändra grundidén. Därför utforskas skilda grundidéer
först, och huvudreferensen blir den valda riktningens referens efteråt. Ägaren väljer själv bland förslagen innan
något fördjupas (ägarens uppdrag via Codex 2026-10-05); ingen panel utser en vinnare.

## Skissläget (standard): full verktygslåda, ren arbetsbänk

Ägarens uppdrag 2026-10-05 16:25Z: kortare väg till professionella, tydligt olika kundanpassade förslag. Första omgången
ger cirka tio skisser: första vyn, den viktigaste innehållssektionen, navigationen och de interaktioner som behövs för
att förstå förslaget, genomarbetade i mobil och dator. De skiljer sig i hur kundens information presenteras och
besökarens uppgift löses; färgbyten på samma layout är inga olika förslag.

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
  sessionen föll), ingen förlängning för att nå antalet. Inget fast antal varv: varje varv åtgärdar en brist skaparen
  sett i sina bilder eller vid jämförelsen med referensen. En skiss som inte blir klar redovisas som ofullständig med
  skälet och det sparade arbetet; ett avbrutet försök sparas i `forsok-<n>/` och startas om i ett nytt projekt.
- **Före ägarens val** ingen granskningspanel och ingen förbättringsrunda. En intern granskare ser skisserna när tiden
  räcker (bara bilderna, aldrig skaparens text) och skaparen svarar under "Svar på granskningen" i RIKTNING.md; granskarens omdöme och
  svaret visas först efter ägarens första beslut. De snabba kontrollerna (bygget, konsolen, spill, axe, siffror utan
  belägg i underlaget, menyn i 390 och 768, huvudreferensraden) markerar brister och ändrar aldrig uttrycket. Vyn visar
  skisserna neutralt, utan rekommendation eller poäng; ofullständiga står med.
- **Efter ägarens val** fördjupas de valda: hela startsidan, den relevanta undersidan och besökarens centrala flöde, med
  DESIGN.md i takt med koden. Den godkända kandidatens kod blir leveransens startpunkt (`installera_godkand`, bygg-sajt
  steg 5.1), så att ingen nästa agent återskapar designen.
- **Redovisningen** (REDOVISNING.md) har total väntan, tid till första valbara skissen, tid och försök per kandidat,
  bristerna, det som tillfördes varje uppdrag och verktygen som användes, de ofullständiga och det som behöver
  mänsklig bedömning. Antalet lästa filer, anrop eller varv är inget betyg.

**Kompetenserna** (ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA"). Vilken roll som
arbetar i vilket pass, med vilken kärna och vilka alternativ, verktyg och MCP:er, och hur sessionerna når skills och
MCP:er, står bara i `kunskap/metodkarta.md` (inledningen och avsnittet Kompetenserna); `kontroller/kompetens.py` läser
kompetensblocken och ger samma block till uppdraget och till sessionens behörigheter. Var i flödet rollerna arbetar står
i stegen nedan. Kvittot (kärnan läst hel, valda alternativ, skillverktygets och MCP:ernas lyckade anrop) och före och
efter står i REDOVISNING.md och i vyn efter ägarens första beslut.

## Stegen (skissläget, `kontroller/kandidater.py`)

Vad varje steg ska besvara, vilket underlag det använder, vad nästa steg får och vad resultatet måste visa står i
`kunskap/metodkarta.md`; `kontroller/metod.py` levererar stegets utdrag med hash vid varje körning, och hashen följer
kandidaterna och granskningarna.

1. **Underlag.** Verksamhetens fakta gäller och ändras aldrig: VERKSAMHET.json, RESEARCH.md med belägg, `kalla/`,
   egna bilder och textens sakuppgifter. Designbesluten är grundidé, referensurval, palett, typografi, komposition,
   bildurval och beskärning, och rubrikernas form. De prövas mot ägarens domar (domloggen) och mot de prövade
   grundidéerna (historiken). Reglerna i fyra slag med räckvidd står i `kunskap/designregler.md`.
2. **Research.** Ett pass skriver antagandena om besökarna som kan ändra designen (underlag eller "ännu inte
   observerat", hur de prövas, vad som ändras), frågor till Refero och Mobbin (högst fjorton) och högst åtta nya sajter.
   Referenssteget hämtar dem med belägg: `referens.py` ger en ny paketversion, `referenstjanster.py` sparar per körning
   tjänsternas svar ordagrant, varje Refero-stils hela dokument och skärmarnas hela bilder. En sajt eller fråga utanför
   kanalens form släpps med skälet, och resten körs; ingen fråga får nämna kundens namn, orter eller nummer.
   FORSKNING.md säger vad som är nytt och vad som återanvänds.
3. **Plan och planprövning.** Ett planeringspass skriver cirka tio uppdrag (`NWP_KANDIDATER`, högst tolv) som besvarar
   kundens problem på olika sätt: innehållshierarkin, bildstrategin, typografin, navigationen och hur förtroende byggs.
   Varje uppdrag har en hypotes (varför lösningen passar verksamheten och besökaren), en namngiven huvudreferens ur
   researchen (den får vara utgångspunkt för layout, palett och typografi, ägarbeslut 2026-10-03; om namnet finns i
   researchen prövas och redovisas per kandidat) med kvaliteten som ska återskapas, vad den kräver och om kundens
   material bär det, antagandena den vilar på, referensbilder, undersidan, materialbehovet och de fynd som formade det.
   Sedan hämtas uppdragens material (huvudreferensens stilpaket och Mobbins skärmar, UPPDRAGSMATERIAL.json), och
   planprövningen prövar uppdragen mot kunden, materialet och referenserna innan någon skiss byggs; titel, hypotes och
   huvudreferens står fast i prövningen (PLANPROVNING.md).
4. **Skissa.** Varje kandidat har en stabil identitet (k01–k12), ett eget Astro-projekt
   (`kunder/<slug>/kandidater/<id>/sajt`: sajtens nuvarande src/ och public/ utan tidigare sidor, kundens bilder, och
   node_modules som länk till sajtens) och en egen skaparsession med samma faktaunderlag; några körs åt gången
   (`NWP_KANDIDATER_PARALLELLT`, högst tre), och ingen kan läsa de andras kataloger. Skaparen skriver RIKTNING.md först
   och bygger skissen: första vyn, den viktigaste innehållssektionen, navigationen och de interaktioner som behövs för
   att förstå förslaget, inte hela startsidan och ingen undersida. Förhandsvarven görs med `--mellan` i 390, 768, 1280
   och 1440, och i varje varv läses bilderna och en referensbild (vad varven prövar: metodkartan, Avgörandena, Process).
   En kritisk granskare ser skissens bilder när tiden räcker (bara bilderna, aldrig skaparens text), och skaparen svarar
   i en egen session (SKISSKRITIK.json, "Svar på granskningen" i RIKTNING.md). Klar är skissen när den är byggd och
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
   Beslutet binds till kandidat och version. Dashboarden startar ingen körning: nästa steg startas med prototyp.py.
7. **Förfina de valda, och två kompetenspass.** Ägaren kör prototyp.py igen (läget valda). Varje vald kandidat förfinas
   för sig i sitt eget projekt, från den version ägaren valde, med ägarens ord och det ägaren gillade i andra förslag
   (inarbetat i idén, inte inklistrat): hela startsidan, den relevanta undersidan och besökarens centrala flöde, i
   skissens form. Skaparen skriver DESIGN.md ur sidan och låter sidorna använda dess variabler (`design.py --kandidat`).
   Den fördjupade sidan fotograferas helt (startsidan i de fyra bredderna och undersidan i 390 och 1440, med axe), och
   sedan gör två kompetenspass sitt arbete en gång var: interaktion och rörelse, sedan tillgänglighet och visuell
   granskning (rollerna i metodkartan). Ett pass som bryter sidan eller ger fler allvarliga axe-fynd återställs, ett
   avbrutet pass tas om från versionen före, och DESIGN.md prövas efter det sista passet. Gör förfiningen inget eget
   varv, blir resultatet ofullständigt eller faller den, återställs den valda versionen. Ingen ny skisskritik och ingen
   granskningspanel körs efter förfiningen; ägaren bedömer den förfinade versionen själv.
8. **Godkännande och överlämning.** Ägaren godkänner en förfinad kandidat för helbygget. Den byggs som vinnare i en
   tempkatalog och byts in först när domen är skriven (`atelje/vinnare/`: alla sidor, DESIGN.md, bilderna och hasharna
   i VINNARE.json i granskarens format), och godkännandet binds till hashen över alla sidorna. Före bygget lägger kor.sh
   sidorna, komponenterna och DESIGN.md i sajten (`atelje.installera_godkand`; de ersatta flyttas med sin väg till
   `kunder/<slug>/startsida-ersatt/`), och bygget tar vid från dem (bygg-sajt steg 5.1). Utan godkänd startsida stannar
   kor.sh före bygget. Vad som sedan gäller för helbygget, exporten och leveransen: `README.md`.

Kandidatens status i ägarens ord: under arbete, klar för ägarens bedömning, vald för vidareutveckling, förkastad,
förfinad, godkänd för helbygge (och ofullständig eller föll, med skälen). Ett avbrott förstör inga klara kandidater:
`atelje.py <slug> --fortsatt` tar bara det som inte är gjort. En halvgjord förbättringsrunda eller förfining är märkt med
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
- Skaparen bygger hela startsidan och undersidan och gör förhandsvarv i 390 och 1440 (`--mellan` också 768 och 1280);
  minst tre varv är en arbetsregel. Undersidan fotograferas i 390 och 1440. Bygger kandidaten inte, eller saknas
  undersidan, huvudreferensraden eller tre varv, är den ofullständig med skälen, och den får ett andra skaparförsök med
  bristerna som kritik.
- **Granskning i två pass och en förbättringsrunda före ägarens val.** En granskare (en annan modell än skaparen som
  standard, `NWP_KANDIDAT_GRANSKARE`) bedömer först bilderna, tillgänglighetsträdet och axe mot besökarens uppgift i
  briefen, utan uppdraget och skaparens anteckningar (sessionen nekas dem): första intrycket, om uppgiften går att
  genomföra, och avvikelserna som krav (kvalitetskrav, hinder för uppgiften) eller smak. Sedan läser den motiveringen
  och märker vilka avvikelser som är avsiktliga och välgrundade. Läste den inte de första vyerna, eller går läsningen
  inte att pröva i transkriptet, styr granskningen ingenting. Förbättringsrundan rättar bara krav som inte är
  välgrundade val, och axe:s allvarliga fynd; smak rättas inte före ägarens val. Föreversionen bevaras med bilderna;
  blir den förbättrade ofullständig återställs föreversionen, och annars granskas den förbättrade igen.
- **Jämförelse:** en granskare ser alla kandidaters första vyer och hela sidor och pekar ut falsk variation.
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
- Piloten är inte avslutad. Dess sessioner slår på Figma-pluginen i sin egen `--settings` och har kundvakten kvar, men
  körskripten ingår inte i repot, och ingen kod prövar vad som laddas upp till Figma (kundvakten gäller Refero och
  Mobbin).
- Privat kundmaterial laddas upp bara till ett nytt projekt i ägarens team, bara för den kund som ägarens besked
  2026-10-06 gäller, med metadata borttagen (foton utan EXIF och GPS), texterna som de står i underlaget och inga
  uppgifter om privatpersoner utöver det som redan står på kundens sajt. Det ger ingen allmän rätt att föra
  kundmaterial till externa tjänster.
- Inget i leveransen är verifierat genom piloten: helbygget, exporten, kundrepot och driftsättningen prövas inte av den.
  Figma blir en del av normalflödet först genom ett beslut av ägaren.

## Domloggen och vad en dom återöppnar

`underlag/<slug>/DESIGNDOMAR.jsonl` har en rad per dom: tid, källa (ägaren, ägaren via Codex, panelen), beslut och text
ordagrant. Loggen arkiveras aldrig. Nästa körning läser den själv, och prompterna börjar med de senaste domarna. Vyn
Prototyp skriver ägarens dom. En dom som kom på annat sätt, via Codex eller i en session, förs in ordagrant med
`.venv/bin/python kontroller/skapande.py dom <slug> --kalla … --beslut … --fil <text>`. Båda går genom samma väg
(`atelje.doma`): bara en klar körning kan godkännas, en pågående körning döms inte, ett godkännande prövas innan
domen skrivs, och en annan dom från ägaren drar tillbaka det. Under ett
bygge är loggen låst (kor.sh, `chflags uchg`), så domen skrivs när bygget är klart; en ändring under bygget ger
slutkod 3. Finns tidigare designbeslut utan dom, eller en dom som inte gäller någon körning i skapandeflödet, vägrar
prototypen att gissa läget.

- `ny_riktning` återöppnar alla designbeslut, aldrig fakta. `kontroller/atelje.py <slug> --ny-riktning` (eller
  prototyp.py) sparar först det ägaren bedömt (ägarens beslut 2026-10-07, `BESLUT.md`). Varje kandidat som ägaren dömt i
  körningen sparas i `underlag/<slug>/omtag/<stämpel>/<kandidat>/<v12>/` med skärmbilderna, versionshashen, domen och
  underlaget som hashen räknas om ur, och `KVITTO.json` har sha256 för varje fil. Vinnaren, slutdomens bilder, tidigare
  körningars arkiv och en äldre prototyp sparas i `omtag/<stämpel>/atelje/` och `omtag/<stämpel>/prototyp/`: inget
  raderas osparat. Faller det raderas inget. Sedan för den
  in den dömda riktningen, eller kandidaterna ägaren såg, i historiken med domen och en pekare till det sparade. Sist raderar
  den REFERENSER.md, KONCEPT.md, ateljén, äldre prototyper, förhandsvarven, tvåan och hela `kunder/<slug>/sajt` och
  `kunder/<slug>/kandidater` (ägarens beslut 2026-10-06: inget arkiv), också en godkänd och helbyggd sajt. Fakta,
  bilder, texten, referenspaketen, domloggen, historiken och leveransen (`kunder/<slug>/kundrepo`) står kvar. Sajten
  görs om ur mallen. Utan en dom som gäller körningen raderas inget ägaren sett; förra körningens kvarlevande processer
  avslutas före raderingen.
- `putsa` behåller riktningen; i den äldre utforskningen körs förfiningen och slutdomen igen, med domen som kritik, och
  förra slutdomen och redovisningen arkiveras först.
- `godkand` lämnar över till bygget.
- Kandidatflödets beslut bär kandidaterna med sina versioner och det ägaren gillade per kandidat (`delar`): `valj`
  startar förfiningen av de valda (`prototyp.py` läget valda), `jamfor` sparar en jämförelse utan att köra något,
  `forkasta` förkastar alla och stannar tills ägaren ber om en ny riktning, och `putsa` förfinar de förfinade igen. En dom
  via Codex kan namnge förslagen: `skapande.py dom <slug> … --kandidater "Förslag C,Förslag F"`. Ett omtag efter
  kandidatflödet för in varje kandidat ägaren såg i historiken, med det ägaren gillade i den.

Ett tidigare designval, till exempel en färg, är inget förbud. Ett drag ur en underkänd grundidé behöver ett skäl ur
verksamhetens material, och skälet ska också svara på kritiken mot den.

`underlag/<slug>/RIKTNINGSHISTORIK.json` samlar prövade grundidéer: namn, huvudreferens, drag, utfall (vald eller
förkastad av panelen, lämnad av skaparen, underkänd av ägaren) och kritiken. Ateljén skriver efter varje panel och vid
TILLBAKA; omtaget skriver ägarens dom.

## Avbrott

Föll en körning tar `.venv/bin/python kontroller/atelje.py <slug> --fortsatt` vid efter den senaste klara fasen (i
kandidatflödet: stycket efter stegen ovan). I den äldre utforskningen tar den vid i omgången som föll, med samma kritik
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

I kandidatflödet sammanställer REDOVISNING.md researchen (nytt och återanvänt), varje kandidat (status, skäl, varv,
sessioner, minuter, listpris, granskningens nivå), kandidaterna som föll, falsk variation och materialbehoven; ägaren
ser den efter sitt första beslut. I den äldre utforskningen skrivs REDOVISNING.md ur sessionernas transkript
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
(`atelje.NEKAS`, `Read(//…)`; ägarens egna regler läses inte i en nästlad session). Paket installeras bara med `kontroller/typsnitt.py` (Fontsource, namnen prövade,
`--ignore-scripts`). Research går genom referenssteget. I kandidatflödet skriver skaparen med sina verktyg i
kandidatprojektets hela src/, RIKTNING.md och en begäran om komplettering, och förfiningen dessutom i projektets
DESIGN.md (`kandidater.verktyg` och `kandidater.forfina_verktyg`); i den äldre utforskningen (`NWP_KANDIDATFLODE=av`) bara sidorna, RIKTNINGAR.md,
KOMPLETTERING.json och urvalet, och förfiningen bara sajtens src/, DESIGN.md och sina tre filer. Det är
en gräns för verktygen, inte för koden: sidorna är kod som körs när sajten byggs (Astros frontmatter). Därför körs varje
bygge av skaparens sidor innanför processgränsen (`kontroller/processgrans.py`): förhandsvisningen, fotograferingen och
slutdomen. Där skrivs bara i det projekt som byggs (sajtens eller kandidatens katalog) och körningens tempkatalog, aldrig i
underlag/<slug> med domloggen och VINNARE.json, och bygget når inget nät: inte localhost, där dashboarden tar emot
ägarens domar, och inte namnuppslag (`processgrans.py --utan-nat --skrivbar <projektet>`). Byggen i samma kunds
projekt köas (`kunder/<slug>/.bygglas`), liksom typsnittsinstallationerna. Kandidaternas projekt delar sajtens
node_modules, som deras byggen kan skriva i (Vites och Astros cache ligger där); paketkod som en sida ändrat där körs
alltså i de andra kandidaternas byggen. Det är samma gräns som för sajtens eget bygge, nu delad av fler skapare. Ett sandlådat bygge (`NWP_SANDLADA=pa`)
kräver därför en godkänd startsida och tar vid från den. Nästlade sessioner skriver aldrig i ägarens automatiska minne
(`kontroller/nastlad.py`).
