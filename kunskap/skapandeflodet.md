# Skapandeflödet

Ett designflöde för startsidan, samma kod och samma text vid varje ingång (Codex via ägaren 2026-10-05: tre designflöden,
där förbättringarna inte följde med mellan dem, blev ett). Orkestratorn är `kontroller/atelje.py`; de delar som alla
steg använder står i `kontroller/skapande.py`. Ingångarna:

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

**Kompetenserna** (ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA"; ägarens uppdrag
18:53Z, punkt 5: varje roll läser de fullständiga relevanta delarna; Codex via ägaren 19:04Z, punkt 7–9). Avsnittet
Kompetenserna i `kunskap/metodkarta.md` ger varje roll en kärna som läses hel och alternativ som väljs efter riktningen,
verktygen, MCP:erna och vad passet ska visa; `kontroller/kompetens.py` läser det och ger samma block till uppdraget och
till sessionens behörigheter. Kedjan:

1. **Planeringen och planprövningen:** uppdragen skrivs och prövas med Referos referenslås och Hallmarks makrostrukturer
   som stöd, så att förslagen skiljer sig i verkliga designriktningar; titel, hypotes och huvudreferens är låsta i
   prövningen (PLANPROVNING.md).
2. **Skaparen:** en sammanhängande skiss med fyra roller (design och komposition, typografi och färg, innehåll och UX,
   responsiv implementation): referenslåset och beslutsliggaren i RIKTNING.md, craft-floor direkt före varje ändring,
   researchens material (Referos stilpaket och skärmar, Mobbins skärmar) och kompletterande sökningar vid behov. Före
   ägarens val ändrar ingen annan session skissen.
3. **Fördjupningen** efter ägarens val: samma roller och designsystemet på hela sajten.
4. **Två pass på den fördjupade sidan**, en gång var: interaktion och rörelse, sedan tillgänglighet och visuell
   granskning (med Impeccables detektor). Varje pass har förhandsvisningens interaktionsväg (tangentbord, fokus,
   hovring, meny, reflow 320, reducerad rörelse) och redovisar tre saker var för sig: koden som ändrades, beteendet som
   prövades och den visuella bedömningen före och efter. Ett pass som bryter sidan eller ger fler allvarliga axe-fynd
   återställs; ett avbrutet pass tas om från versionen före; DESIGN.md prövas efter det sista passet.

Alla skills (skillverktyget) och användarens MCP-servrar är tillgängliga i sessionerna. Refero och Mobbin står
inte i sessionernas tillåtelselista: kundvakten (`kontroller/kundvakt.py`, en krok före varje anrop) öppnar ett anrop som
inte bär kundens uppgifter och stoppar resten, och en vakt som inte kan pröva lämnar anropet åt dontAsk, som nekar det.
Skills utan uppgift i flödet står med skäl i kartan. Kvittot (kärnan läst hel, valda alternativ, skillverktygets och
MCP:ernas lyckade anrop) och före och efter står i REDOVISNING.md och i vyn efter ägarens första beslut.

`NWP_KANDIDATLAGE=full` är en tillfällig växel till det tidigare förvalet (granskning i två pass och förbättringsrunda
före ägarens val, hela startsidan och undersidan, minst tre varv), för jämförelse och återställning. Växeln tas bort när
ägaren dömt skissläget (BESLUT.md 2026-10-05, kväll). Körningens läge står i planen, så en återupptagning följer
körningen.

## Stegen (kandidatflödet, `kontroller/kandidater.py`)

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
3. **Plan.** Ett planeringspass skriver cirka tio uppdrag (`NWP_KANDIDATER`, högst tolv) som besvarar kundens problem
   på olika sätt: innehållshierarkin, bildstrategin, typografin, navigationen och hur förtroende byggs. Varje uppdrag
   har en hypotes (varför lösningen passar verksamheten och besökaren), en namngiven huvudreferens ur researchen (den får
   vara utgångspunkt för layout, palett och typografi, ägarbeslut 2026-10-03; om namnet finns i researchen prövas och
   redovisas per kandidat) med kvaliteten som ska återskapas, vad den
   kräver och om kundens material bär det, antagandena den vilar på, referensbilder, undersidan, materialbehovet och de
   fynd som formade det.
4. **Skapa.** Varje kandidat har en stabil identitet (k01–k12), ett eget Astro-projekt
   (`kunder/<slug>/kandidater/<id>/sajt`: sajtens nuvarande src/ och public/ utan tidigare sidor, kundens bilder, och
   node_modules som länk till sajtens) och en egen skaparsession med samma faktaunderlag; några körs åt gången
   (`NWP_KANDIDATER_PARALLELLT`), och ingen kan läsa de andras kataloger. Skaparen skriver RIKTNING.md först, gör ett
   tidigt kompositionsprov där referensens kvalitet prövas mot kundens material, bygger hela startsidan och undersidan
   och gör förhandsvarv i 390 och 1440 (768 med `--mellan` när layouten byter form) där bilderna och en referensbild
   läses. Klar är den när den renderade sidan visar att grundidén syns, att kundens material bär kompositionen, att den
   viktigaste besökaruppgiften går att genomföra och att mobilen håller ihop, med bilderna under "Visar". Tre varv är en
   arbetsregel. Formulären postar till `/api/forfragan/` och landar på `/tack/` (lokal demonstration).
5. **Fotografera.** Bygget körs innanför processgränsen; startsidan fotograferas i 390, 768 och 1440 och undersidan i
   390 och 1440, och axe prövar startsidan och undersidan med menyn öppen och formulären skickade tomma. Koden bevaras i
   `kod/`, DESIGN.md bredvid och bilderna i `bilder/`; versionen är hashen över koden och DESIGN.md, så en ny
   fotografering av samma kod ger samma version. Bygger den inte, saknas undersidan, huvudreferensraden eller tre varv,
   är kandidaten ofullständig med skälen, och den får ett andra skaparförsök med bristerna som kritik.
6. **Granska i två pass och förbättra.** En granskare (en annan modell än skaparen som standard,
   `NWP_KANDIDAT_GRANSKARE`) bedömer först bilderna, tillgänglighetsträdet och axe mot besökarens uppgift i briefen,
   utan uppdraget och skaparens anteckningar (sessionen nekas dem): första intrycket, om uppgiften går att genomföra,
   och avvikelserna som krav (kvalitetskrav, hinder för uppgiften) eller smak. Sedan läser den motiveringen och märker
   vilka avvikelser som är avsiktliga och välgrundade. Läste den inte de första vyerna, eller går läsningen inte att
   pröva i transkriptet, styr granskningen ingenting. Förbättringsrundan rättar bara krav som inte är välgrundade val, och axe:s allvarliga fynd; smak rättas
   inte före ägarens val. Föreversionen bevaras med bilderna; blir den förbättrade ofullständig återställs föreversionen.
7. **Jämföra.** En granskare ser alla kandidaters första vyer och hela sidor och pekar ut falsk variation.
8. **Ägarens val.** Vyn Prototyp visar alla kandidater med neutrala namn (Förslag A–L, slumpad ordning ur planens tid)
   och lika stora bilder, mobil och dator bredvid varandra eller en bredd i taget (surfplattan, och mellanbredden 1280
   när den finns); bilderna öppnas i full storlek, varje prototyp klickbar med sina undersidor, och markerade förslag
   står sida vid sida. Ägaren bedömer bilderna först, sedan referensen och sist redovisningen (ägarens uppdrag
   2026-10-06, punkt 8). Därför står två delar hopfällda efter bilderna, för varje förslag från början: huvudreferensens
   fångade startsida bredvid förslaget i 390 och 1440, och skaparens korta redovisning ur RIKTNING.md under rubrikerna
   "Idén", "Referenser", "Överfört och avvikelser" och "Kvarvarande svagheter" (en rubrik som saknas eller är tom sägs,
   inget fylls i). De tekniska kontrollerna står för sig under en rubrik som säger att de inte är ett godkännande av
   designen. Panelens granskning, planens titlar och körningens redovisning visas först efter ägarens första beslut, och
   då också före och efter en förbättringsrunda, där ägaren kan säga vilken som är bättre och välja föreversionen.
   Ägaren väljer en eller flera för vidareutveckling, sparar en jämförelse, markerar det ägaren gillar per förslag (det
   följer med ordagrant till de valda), förkastar alla eller ber om en ny riktning. Beslutet binds till kandidat och
   version.
9. **Förfina de valda.** Varje vald kandidat förfinas för sig i sitt eget projekt, från den version ägaren valde, med
   ägarens ord, det ägaren gillade i andra förslag (inarbetat i idén, inte inklistrat) och granskningen. Skaparen skriver
   DESIGN.md ur sidan och låter sidorna använda dess variabler (`design.py --kandidat`). Gör förfiningen inget eget varv,
   blir resultatet ofullständigt eller faller den, återställs den valda versionen. Efter förfiningen körs ingen ny
   granskning: vyn och REDOVISNING.md säger att granskningen gäller versionen före, och ägaren bedömer den nya själv.
10. **Godkännande och överlämning.** Ägaren godkänner en förfinad kandidat för helbygget. Den byggs som vinnare i en
    tempkatalog och byts in först när domen är skriven (`atelje/vinnare/`: alla sidor, DESIGN.md, bilderna och hasharna
    i VINNARE.json i granskarens format), och godkännandet binds till hashen över alla sidorna. Före bygget lägger kor.sh
    sidorna och DESIGN.md i sajten (`atelje.installera_godkand`; de ersatta flyttas med sin väg till
    `kunder/<slug>/startsida-ersatt/`), och bygget tar vid från dem (bygg-sajt steg 5.1). Utan godkänd startsida stannar
    kor.sh före bygget.

Kandidatens status i ägarens ord: under arbete, klar för ägarens bedömning, vald för vidareutveckling, förkastad,
förfinad, godkänd för helbygge (och ofullständig eller föll, med skälen). Ett avbrott förstör inga klara kandidater:
`atelje.py <slug> --fortsatt` tar bara det som inte är gjort. En halvgjord förbättringsrunda eller förfining är märkt med
sin föreversion och återställs; en körning vars arbetare dött tas aldrig om som en ny körning (prototyp.py och atelje.py
säger att den avbröts och pekar på `--fortsatt`), och ägaren dömer först när den tagits upp (vyn och `skapande.py dom`
vägrar under ett avbrott). Kandidatflödet känns igen på ateljén (KANDIDATPLAN.json, `kandidater/`), så en körning som
föll tidigt fortsätter i kandidatflödet, aldrig i den äldre utforskningen. En ny plan arkiverar förra körningens projekt
i `atelje/foregaende/`.

## Den äldre utforskningen (nödväg)

`NWP_KANDIDATFLODE=av` ger den äldre vägen: en skapare tar fram tre riktningar i samma session (`atelje-N`-sidor i
sajten), tre domare väljer eller förkastar dem, den valda förfinas och döms före mot efter, och ägaren dömer slutet
(godkänd, putsa eller ny riktning). Den finns kvar för återupptagning av äldre körningar och som nödväg.

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
  prototyp.py) för först in den dömda riktningen, eller kandidaterna ägaren såg, i historiken med domen. Sedan raderar
  den REFERENSER.md, KONCEPT.md, ateljén, äldre prototyper, förhandsvarven, tvåan och hela `kunder/<slug>/sajt` och
  `kunder/<slug>/kandidater` (ägarens beslut 2026-10-06: inget arkiv), också en godkänd och helbyggd sajt. Fakta,
  bilder, texten, referenspaketen, domloggen, historiken och leveransen (`kunder/<slug>/kundrepo`) står kvar. Sajten
  görs om ur mallen. Utan en dom som gäller körningen raderas inget ägaren sett; förra körningens kvarlevande processer
  avslutas före raderingen.
- `putsa` behåller riktningen: förfiningen och slutdomen körs igen, med domen som kritik. Förra slutdomen och
  redovisningen arkiveras först.
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

Föll en körning tar `.venv/bin/python kontroller/atelje.py <slug> --fortsatt` vid efter den senaste klara fasen: i
utforskningen vid omgången som föll, med samma kritik som första gången (skaparens TILLBAKA.md eller panelens VAL.md),
och i en putsning vid förfiningen eller slutdomen mot samma före. En avslutad körning (klar, förkastad, tillbaka) tas
aldrig upp igen, och varken `--fortsatt` eller `--bara-domare` körs när ägaren dömt efter körningen; där avgör
ägarens dom nästa steg. Det som flyttas undan, äldre riktningsbilder och en tidigare vinnare, hamnar i `atelje/foregaende/`. Inget
raderas.

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
ändrats; den äldre utforskningen räknar upp samma källor (`skapande.metodrader`, `skapande.metod_filer`).
Kandidatflödets sessioner har skillverktyget och verktygssökningen (`kompetens.verktyg`); varje roll läser sin kärna
hel och väljer alternativ efter riktningen (avsnittet Kompetenserna i metodkartan). Läsningen prövas i transkriptet
(metoden före första ändringen, varvens bilder) och redovisas skild från tillämpningen (varven i RIKTNING.md som namnger
vad i metoden som gav åtgärden).

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

## Sandlådan

Skapandeflödets sessioner har ingen egen sandlåda än: flödet körs utanför den, före bygget. Sessionerna har bara sina
namngivna verktyg och inget eget nät, och sandlådans lista över hemligheter nekas dem var de än ligger
(`atelje.NEKAS`, `Read(//…)`; ägarens egna regler läses inte i en nästlad session). Paket installeras bara med `kontroller/typsnitt.py` (Fontsource, namnen prövade,
`--ignore-scripts`). Research går genom referenssteget. Utforskningen skriver med sina verktyg bara sidorna,
RIKTNINGAR.md, KOMPLETTERING.json och urvalet, och förfiningen bara sajtens src/, DESIGN.md och sina tre filer. Det är
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
