# Metodkartan — skills och kunskap per steg

Den enda källan för vad varje steg i skapandeflödet ska besvara, vilka skills och kunskapsfiler som stöder det, vilka
avsnitt av dem, och hur motsägande råd avgörs (ägarens begäran 2026-10-05: skillsen i sin fullo, krockarna avgjorda,
best practice som helhet; synpunkterna på kartan samma dag). Företrädet står i `kunskap/designregler.md`: gemensamma
kvalitetskrav, Nortropics produkt- och ägarbeslut med räckvidd, kundens behov, designhypoteser; en skills standardråd
står sist. Citaten och källorna bakom varje avgörande: `kunskap/skillkrockar.md` (K-numren nedan).

**Stegens sju delar** (ägarens uppdrag 2026-10-09 om ett källförankrat arbetssätt, punkt 4): varje stegavsnitt nedan
säger uppgiften (Fråga), kompetensen (rollen i Kompetenserna och stegets utdrag), tillämpningen, resultatet och
överlämningen (Till nästa steg), bedömningen (Visar) och återgången. Helbygget och leveransen har egna avsnitt sist;
de levereras inte som metod till skapandeflödets sessioner. En specialistroll är en uppgift med sin kompetens, inte
nödvändigtvis en egen session.

**Så levereras metoden:** `kontroller/metod.py` läser stegens block ```` ```utdrag ```` (en rad per källa: väg, och
rader eller en rubrik) och skriver vid varje körning stegets filer i `underlag/<slug>/atelje/metod/`: kartans text för
steget, avgörandena och utdragen med källa och hash, delade så att varje fil ryms i ett Read utan offset och limit
(högst 30 000 tecken). Prompterna pekar på de filerna, och kandidaternas status och granskningar bär hashen. Låset
`kunskap/metodkarta.lock.json` stoppar leveransen när en källa ändrats sedan utdragen prövades, så att rader aldrig
tyst pekar fel. Läsningen prövas i transkriptet och redovisas skild från tillämpningen: en fil räknas som läst när
ett felfritt Read täckt alla dess rader. Hos skaparen i läget full och i förfiningen prövas metodens före-fil; i
skissen, planprövningen, passen, researchen, skisskritiken, jämförelsen och granskningens två pass prövas rollernas
kärna (kompetenskvittot, avsnittet Kompetenserna). Uppslaget slås upp när uppgiften behöver det och har inget läskrav.
**Verktygen, en källa:** kompetensblocken nedan säger vilka skills, verktyg och MCP:er varje pass har. Samma block ger
sessionens behörigheter (`kontroller/kompetens.py` till `--allowedTools`) och raderna i passets uppdrag, så att
dokumentationen, prompten och behörigheten säger samma sak. Sessionerna har skillverktyget och verktygssökningen. Av
MCP-anslutningarna används Refero, Mobbin, 21st och Motions fria dokumentationssökning genom kundvakten
(`kontroller/kundvakt.py`, före varje anrop); Chrome DevTools når bara den separata lokala tjänsten enligt H1.
Kundvakten tillåter bara flödets angivna verktyg med generiska argument och stoppar resten,
och varje annat MCP-anrop nekas (dontAsk). Frågorna till tjänsterna är alltid generiska: bransch och uppgift, utan
kunduppgifter, namn eller citat. Personnamnen och orterna tar kundvakten ur briefen, sidans text, fritexten i
VERKSAMHET.json och Bokadirekts filer. Gator, postnummer och orter i en adress tar den också ur RESEARCH.md, och
fritextens adresser hör till kundens förbjudna termer (`skapande.forbjudna_termer`). Samma kända nummer prövas även
i tjänsternas ID:n och adresser. Läsfel i en befintlig underlagsfil nekar anropet; en valfri fil som inte finns gör
det inte. En postort på raden direkt efter postnumret räknas också, även med slutpunkt eller i ett listat
kontaktblock, men inte en ny rubrik (också setext) eller ett nytt stycke.
Det är prövade mönster, inte en garanti att alla personuppgifter känns igen. Ett namn stoppas också ord för ord
när det står efter ett personord (också "Möt", och "Om" först i en rubrik), före en roll eller ett personverb, i en
attribution eller i en mailto-länk. Detsamma gäller ett namn med ett vanligt förnamn, en rubrik som bara är namnet och
ett namn under en rubrik om personer (Om oss, Team, Omdömen, Kontakt). Andra par med stor bokstav, också först i en
mening, stoppas som hela par. En ort stoppas efter ett platsverb och, utanför §7, efter varje platspreposition. Briefens
§7, där förlagorna och typsnitten står, läses bara för orter och mailto-länkar. Ett typsnitt ur Google Fonts och en term
som "Dark Mode" är inga namn, så en generisk fråga med en förlaga eller ett typsnitt ur designriktningen går.
Detaljerna, och var felet går åt det säkra hållet, står i kundvaktens beskrivning. Mobbins `search_screens` går bara med
`mode` "standard", eftersom verktygets standardläge deep kostar krediter. Sessionerna når Refero, Mobbin, 21st och Motion genom
`kontroller/mcp/` (`--mcp-config` med `--strict-mcp-config` i `atelje.session_args`; Referos fil får nyckeln ur
hemlighetsmappen, `atelje.refero_mcp_fil`): inga servrar på användarnivån laddas (det verkliga sessionsprovet
2026-10-08 visade tio sådana bredvid flödets tre, GR-20261008-r117-claude#E1), och Mobbin, som annars bara finns på
användarnivån, som sessionernas `--setting-sources project,local` inte läser, når skaparna ändå (fynd 2026-10-07). Startkontrollen prövar åtkomsten med flödets egna argument
(`kunskap/beroenden.md`, Vad startkvittot säger). I de granskande passen (skisskritiken, jämförelsen och granskningens
två pass) är förhandsvisningen och detektorn granskarens form (`--granskare`): bilderna hamnar i kandidatens
`granskare/`, aldrig i skaparens varv, och verktygen ger ingen kod (inga byggloggar, inga kodutdrag, inga spårfiler). Ett
blint pass får bara verktyg som aldrig ger kod eller skaparens text; `kontroller/kompetens.py --prova` fäller ett annat.
Bygget och fotograferingen går genom förhandsvisningen, och
beroendena kommer förberedda och låsta ur mallen (`kunskap/beroenden.md`); git, npm, npx och node körs inte direkt i
sessionerna.

## Avgöranden

- **Arbetsprincipen** (ägarens uppdrag 2026-10-09): varje steg utgår från tillämpliga, trovärdiga källor och kundens
  faktiska förutsättningar, fattar motiverade beslut med rätt specialistkompetens, undersöker osäkerheter med en metod
  som kan besvara dem och bedömer resultatet innan steget räknas som uppfyllt. Källornas slag: `kunskap/designregler.md`.
  Vid motstridiga råd avgör källornas syfte och räckvidd, inte vilken instruktion som lästes sist. Ett betydande vägval
  står i beslutsliggaren: problemet, underlaget och källan, alternativet, antagandet och hur effekten bedöms.
- **Osäkerheter:** skriv först vad som är osäkert och välj metod efter slaget: teknik genom aktuell officiell
  dokumentation och ett avgränsat prov; metod genom primärkällor och vid behov ett jämförande försök; kundens fakta genom
  kunden eller verifierat underlag; besökarnas behov genom data, intervjuer, observation eller besökarprov; en visuell
  lösning genom renderade alternativ; modellens förmåga genom ett förmågeprov; motstridiga krav genom en skriven
  avvägning. Sök avgränsat och redovisa det som förblir osäkert.
- **Bilder (äkthet):** en bild som visar verksamheten (arbeten, personer, lokaler, resultat) är dess egen; illustrativt
  material som inte utger sig för att dokumentera den (licensierade illustrationer, texturer, konceptbilder, form i
  koden) är tillåtet med källa i BILDER.md eller DESIGN.md (`kunskap/bild.md`). Bilderna serveras från sajten. Saknat
  material står under "Material" i RIKTNING.md, beställs och får en märkt platshållare (K06–K09, K11, K13).
- **Sanning (kvalitetskrav):** varje namn, tal, datum, omdöme och märke kommer ur underlaget, också i exempel; citat står
  ordagrant med källans attribution och avkortas bara synligt med "…"; löften, funktioner och certifieringar bara med
  källa (K10, K12, K43, K44).
- **Teknik (standardval för lokala tjänsteföretag):** Astro med förrenderade sidor, och en sammanhängande implementation
  per riktning ur mallens låsta beroenden: egen CSS, CSS-variabler (Referos direkt), Tailwind, Astro- och React-
  komponenter, Motion och GSAP (`kunskap/beroenden.md`). Rörelsens teknik väljs per beteende ur designens och
  implementationens behov: CSS först när den räcker, Motion (`motion` i ett `<script>`, `motion/react` i en React-ö;
  det äldre namnet är Framer Motion) för fjädrar, avbrytbara gester och layoutanimationer, GSAP för tidslinjer och
  scrollsekvenser; valet skrivs med skäl av rollen rorelse, och ingen rörelse läggs till för att fylla en kvot (ägarens
  uppdrag 2026-10-07, punkt 5C). Innehållet och navigationen fungerar utan JavaScript, rörelse respekterar
  `prefers-reduced-motion`, prestandabudgeten håller, inget hämtas från ett CDN, inget rör sig av sig självt utan paus
  och scrollningen följer webbläsaren (WCAG 2.2.2; K14–K21, K40).
- **Referens och stil (ägarbeslut 2026-10-03):** huvudreferensen får bära layout, palett och typografi, och särprägeln
  ligger i vår touch och verksamhetens material. Skillsens listor över förbjudna paletter, typsnitt, centrering,
  etiketter över rubriker, gradienter och pilar är granskningsfrågan "valt av vana utan skäl?", aldrig förbud eller
  krav. Valet av typsnitt och färg skrivs med skäl i RIKTNING.md och märks `valt:` i DESIGN.md; inga reservvärden ur en
  skill (#2563EB, Inter) (K01–K05, K23–K27, K29, K34–K37).
- **Kundens behov (ur briefen, med belägg):** toppuppgifterna och den primära handlingen avgör vad första vyn och
  sidan måste klara. Kontaktvägarna följer kundens kontaktmodell (BRIEF.md §4): har den telefonen finns numret som
  tel-länk på varje sida, och placeringen är riktningens val. Brödsmulor finns när DESIGN.md:s struktur har dem.
  Kontaktuppgifter går att markera och kopiera. Hela listor (priser, tjänster) är tillåtna när besökaren frågar efter
  dem, och inget göms i sidled utan synlig ledtråd (K30–K33, K38, K39, K41).
- **Referensens kvalitet mot kundens material:** en referens fungerar under förutsättningar (stora arkitekturfoton,
  korta rubriker, få produkter). Varje kandidat säger vilka observerbara egenskaper som bär referensens kvalitet och
  som den prövar att föra över, vad de kräver och om kundens material bär det; det renderade resultatet avgör vilka
  anpassningar som håller, och en anpassning behåller eller ersätter referensens kvaliteter med något lika
  genomarbetat (ägarens uppdrag 2026-10-06; `kunskap/bild.md`, art direction).
- **Sektionsordningen** motiveras ur besökarens frågor och toppuppgifterna i BRIEF.md; skillsens sektionspaket (AIDA,
  landningssidans ordning) används inte (K22).
- **Process:** ingen svarar i flödets sessioner. Uppdraget och underlaget är svaret; antaganden skrivs i RIKTNING.md och
  arbetet fortsätter till stegets "Visar". Briefen är uppdragets fakta, besökarens uppgift och materialet; uppdragets
  formförslag får skaparen, som ansvarig designer, ompröva med skäl när renderingen visar något bättre (ägarens uppdrag
  2026-10-06). Ingen tärning, inget concept-seed och inga egna sanningskällor ur skills (MASTER.md, PRODUCT.md,
  brand-guidelines). refero-design är researchmetod och referenslåsets format, inte ensam designauktoritet: skaparen
  avgör motstridiga råd. Varven: i skissläget inget fast antal; första varvet efter renderingen prövar grunden
  (komposition, hierarki, bildval, rytm, kundens särprägel) och får byta grundidé, referens eller komposition, och varje
  varv därefter åtgärdar det största visuella problemet skaparen ser i sina bilder eller vid jämförelsen med referensen
  i samma bredd. Inget läge har ett minsta antal varv (ägarens uppdrag 2026-10-09, punkt 10): varje varv är en observerad
  brist, en ändring och en efterkontroll, och två varv i rad utan synlig förbättring är rundgång och ett skäl att sluta
  eller byta grundidé. Resursgränserna är fristerna och turerna, och ägaren kan stoppa. Impeccables metod har högst två
  samlade inspektionsomgångar och sedan en färsk granskare, vilket är förenligt (`kunskap/metodregler.md`).
  Verktygen per pass står i kompetensblocken. Inga test-, variant- eller prototypsidor i src/pages: varje index.astro
  där blir en undersida. DESIGN.md är kontraktet: värdena, valda tillstånd (mörkt läge) och importerade stilvärden
  (`kunskap/bygge-referens.md`). Granskaren svarar bara i sitt schema (K46–K55, K57, K58).
- **Före ägarens val i skissläget** granskar ingen panel och ingen förbättringsrunda körs: de snabba kontrollerna
  markerar brister och ändrar aldrig uttrycket. Inom skissförsöket ser en kritisk granskare den renderade skissen som en
  besökare: skaparens bilder och sin egen förhandsvisning i 390, 768, 1280 och 1440 med menyn öppen, tangentbordet och
  reflow, detektorn och egna jämförelser med förebilder ur Refero och Mobbin, aldrig skaparens text, uppdrag,
  referenspaket eller kod (rollen kritik i Kompetenserna). Den beskriver de synliga problemen och kan rekommendera att
  riktningen förkastas; skaparen svarar i en egen session och avgör (ägarens uppdrag 2026-10-06, punkt 6).
- **Granskning före förbättring (läget full):** granskningen bedömer först det en besökare uppfattar (bilderna, trädet
  och axe mot besökarens uppgift; samma blinda roll som skisskritiken) och sedan skaparens motivering (rollen
  motivering). Förbättringsrundan före ägarens val rättar bara objektiva fel
  (kvalitetskrav och hinder för uppgiften), aldrig smak, så att kandidaterna inte jämnas ut; föreversionen bevaras, och
  ägaren kan jämföra och välja den.
- **En källa per värde:** better-ui för tryck, ikoner och skuggor; emil-animate för om och hur länge något rör sig;
  better-layout för innehållsstyrda brytpunkter (proven tar 390, 768, 1280 och 1440); svenska citattecken ” ” och tankstreck i
  intervall (9–17) enligt `kunskap/copy-kontroll.md`, högst ett tankstreck per stycke i löptext (K28, K64–K67).
- **Rörelserådets räckvidd:** CSS garanterar inte körning utanför huvudtråden. Bedöm ändrade egenskaper och mät
  layout, paint och compositing vid relevant risk; transform och opacity är ofta gynnsamma men är inte mätbevis.
  Det kvalificerar emil-animate:s generella formulering, utan att ändra upstreammaterialet (P4; web.dev,
  `https://web.dev/articles/animations-guide`). Numeriska stilråd är startvärden inom sina villkor, inte nya normkrav.
- **Skills som väntar på ett svar:** en skill med Initial Response läses bara med Read; kunskapen används men
  väntesvaret körs inte. `kompetens.skill_nekas` nekar både mappnamnet och metadatanamnet genom Skill i ateljéns
  argument och helbyggets inställningar. Övriga tillåtna skills kan fortfarande laddas med Skill (K46/P5).

## Kompetenserna

Körbara hjälpmedel följer rollens uppgift. Komposition och designsystem har `skillskript` för brand-, token-,
Tailwind- och canvasfunktionerna; kontrakt, exempel och begränsningar finns i `kunskap/skillskript.md`.
Valda referenssidor profileras genom DevTools efter planprövningen enligt `kunskap/referensprofil.md`. Skaparens
UPPDRAG.md får bara profiler som är bundna till den valda sidan, paketet och metoden. Äldre lösa profiler injiceras inte.
Materialbeställning och generering är skilda steg enligt `kunskap/materialtransport.md`: kandidaten kan beställa,
men den betrodda körningen behöver ett uppdragsspecifikt kostnadsmandat och konto innan något skickas.
Läsning, aktivering och tekniskt lyckat resultat redovisas separat från visuell kvalitet.

**Användningen i sex nivåer** (ägarens uppdrag 2026-10-09 om ett källförankrat arbetssätt, punkt 5): observationen
redovisar varje nivå för sig och okänt som okänt (`kompetens.anvandningsnivaer`, i specialistpassens post): erbjuden
(rollens kärna i uppdraget), laddad (kärnan läst hel, ur transkriptet), anrop med användbart resultat (verktygs- och
MCP-anrop med innehåll), redovisad av skaparen (ändringar knutna till en skill), belagd i artefakten (versionen ändrades
och står kvar) och effekt bedömd (bara av en oberoende bedömning: granskningen eller ägaren). En skill tillskrivs aldrig
en förbättring som inte går att belägga, och ett anrop görs aldrig bara för att fylla en ruta. Med ägarens ord
2026-10-09 (punkt 9): tillgänglig = erbjuden (och startkvittots sessionsprov), aktiverad = skillverktygets anrop
(`skill_anrop`), läst = laddad, använd = anrop med användbart resultat och belagd i artefakten, och bedömd effekt =
effekt bedömd. En misslyckad åtkomst (nekad av kundvakten, fel, saknad nyckel) står som det den är, en faktisk
begränsning, och aldrig som oanvänd. Återkopplingen har formen bild, version, element eller område, tillstånd och
avvikelse, med kodkoppling när den finns (`skapande.FYND_SCHEMA`, `kandidater.kodkoppling`).

**Arbetskrav före fortsättningen** (rättelse 2026-10-09). `kompetens.kravbrister` prövar kvittot mot rollen:
hela kärnan och lyckad Skill-aktivering av aktiverbara kärnskills i varje session. Samma kontroll gäller alternativ
som transkriptet visar fullständigt lästa. I ändrande pass krävs aktiveringen före den första observerade kodändringen.
Alternativ som bara deklarerats i svaret men aldrig observerats lästa omfattas inte av denna grind; det är en kvarstående
kontrollucka, inte bevis för genomförd aktivering. En ny session ärver inte ett tidigare kvitto. Skillens mappnamn och dess
frontmatternamn binds till samma lokala fil; ett främmande plugin med samma kortnamn får ingen lokal läskredit.
Read gäller fortfarande dokument och de uttryckliga Initial Response-undantagen. Saknade transkript är okänt och
kan inte göra ett obligatoriskt moment genomfört. Gamla resultat bevaras som historik, men återanvänds inte som
aktuella kompetensbevis när uppgiften kräver den nya kontrollen.

`mcp` anger vilka möjligheter rollen har; `mcp-krav` anger vilka undersökningar den måste genomföra med observerat
resultat före nästa steg. Researchen undersöker Refero, Mobbin och 21st före planen. Planeraren prövar den hämtade
grunden mot kundens material. Skaparen använder det som faktiskt hämtats och gör kompletterande anrop när underlaget
inte räcker; identiska sökningar upprepas inte bara för ett kvitto. Vald kod eller tema följer med som id, källa,
fil, licens och beroenden till implementationen. En lyckad sökning bevisar inte att koden integrerats: detta ska
visas i den renderade versionen och bedömas där. Uppgiften för 21st följer leverantörens ordning sök, välj, hämta kod,
integrera och anpassa ([officiell skill](https://github.com/21st-dev/magic-mcp/blob/main/skills/21st-ui/SKILL.md), läst
2026-10-09). Ett Builder-abonnemang bevisar inte åtkomst till separat AI-generering eller en viss betald mall.

**Räckvidd.** Grinden gäller skapandeflödets kvitton och helbyggets eget slutkvitto. Helbygget ansluter samma fyra
designtjänster via `byggmcp.py` och kundvakten. Det kräver sitt eget underlag från byggsessionen, inte prototypens
aktivering. DevTools beställs i en separat inspektionssession efter planprövningen. Materialleverantörernas
transport finns genom den betrodda CLI-vägen; automatisk vidarebefordran från en skaparsession ingår inte.
Tillgång, användning och kvalitet redovisas var för sig; kontraktsprov är inget bevis för ett fungerande konto.

Ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA"; ägarens uppdrag 18:53Z, punkt 5: varje
roll läser de fullständiga relevanta delarna, utan tunna sammanfattningar och utan att varje metodtext läggs i varje
skapares uppdrag; Codex via ägaren 19:04Z, punkt 7–9: varje riktning får en sammanhängande tillämpning, med full tillgång
till alternativen och fullständig läsning av den valda metoden.

Varje roll har en **kärna** och **alternativ**. Kärnan är rollens sammanhängande metod och läses hel innan sessionen
ändrar eller bedömer något (en fil större än en läsning läses i delar med offset och limit tills alla rader är lästa).
Kompetenskvittot visar ur transkriptet om den lästs: skissen och planprövningen redovisar det, i passen rörelse och
granskning får en session som inte läst sin kärna ett omförsök, och förfiningen redovisar bara metodens läsning.
Kvittot räknar sessionerna: saknas ett transkript av flera är kvittot ofullständigt (`sessioner`: förväntade, sedda och
de saknade med skäl), och det som inte sågs är då inte observerat, aldrig inte gjort (F04). Varje session är en egen
kontext (flödet återupptar aldrig en session): läsningen och läsordningen räknas per session (`per_session`), och
kärnan står som läst, och läst före första ändringen, bara när varje sedd session läste den så; en tidigare sessions
läsning döljer aldrig en ny sessions brist (R02). Ett kompetenspass som får ett omförsök börjar från versionen före
passet, och bara omförsökets session räknas. Läste passet en kärnfil först efter sin första ändring får det ett
omförsök, och ett pass med arbete före kärnan är aldrig genomfört (`sen_karna`; N03 i GR-20261009-natt-omgranskning-codex). I ett ändrande pass visar
kvittot också läsordningen: en kärna läst hel men först efter första kodändringen står som det (F05). Varje
MCP-tjänst sessionen anropade står i observationen, också Motion, vars dokumentsvar i text är ett lyckat anrop med
innehåll (F03); Referos och Mobbins svar är listor eller bilder, och en text utan känd lista där är ett svar utan känd form.
Researchen, skisskritiken, jämförelsen och granskningens två pass sparar kvittot i FORSKNING.json, SKISSKRITIK.json,
JAMFORELSE.json och KRITIK.json, med verktygsanropen och tjänsternas anrop och deras utfall. Alternativen är
stilvarianter och recept för olika riktningar: sessionen väljer de som passar riktningen, läser dem hela och skriver
valet med skäl, eller skriver varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller kundens
behov avgörs av Avgörandena ovan, designreglerna och kundens aktuella domar, som varje session med en roll får.

**Aktivering, användning och bedömning** (ägarens förtydligande 2026-10-07, ~15:20Z, ordagrant i `BESLUT.md`). En skill
i kärnan eller bland alternativen aktiveras med Skill-verktyget, som `-p`-sessionerna har: prövat 2026-10-07 i en
nästlad session med flödets egna argument, där anropet syns i kvittot som `skill_anrop` och räknas som läst SKILL.md,
medan en aktivering som nekas eller ger fel (okänd skill) inte räknas, som för Read (`kontroller/bildkedja.py`; förut
räknades den, rättat samma dag). En referensfil som inte är en skill (`kunskap/`, `kritik/`, en skills reference-fil) läses
hel med Read enligt skillens instruktion, och kvittot räknar den läst först när läsningarna täckt alla rader. Kvittot
skiljer tre saker som aldrig byter plats: aktiveringen och läsningen (kärnan hel, valda alternativ, `skill_anrop`),
användningen (verktygs- och tjänsteanrop med utfall) och bedömd kvalitet, som kvittot aldrig ser (`tillampning` står
alltid som inte observerat; kvaliteten bedöms av kritiken och ägaren). Saknad kärnläsning och misslyckad obligatorisk
Skill-aktivering fäller arbetskravet: i passen rörelse och granskning får sessionen ett omförsök
(`kontroller/kandidater.py`), i skissen står passet som inte genomfört (`genomford`), planprövningen redovisar kvittot
och kritiken sparar kvittot i SKISSKRITIK.json. Ett alternativ som inte gick att ladda ska skrivas i svaret med felet
och får inte redovisas som använt. Ett alternativ eller en skill som svaret redovisar som valt, lyckat aktiverat eller som
grund för en kodändring (schemafälten `valda`, `aktivering` och `kod_andrad`) måste vara observerat läst eller aktiverat i
någon av passets sessioner; annars är det en brist (`kompetens.redovisade_brister`). DESIGN.md:s rubrik Kompetenserna
ställs mot det observerade som en iakttagelse (`redovisat_ej_observerat`), eftersom texten också får säga att en skill
inte passade. Fri text räknas aldrig som aktivering. Att ett verktyg finns installerat räcker inte: tillståndsorden
nedan skiljer tillgängligt, provat, tilldelat och använt med resultat.

**Underagenter, skalet och slutgranskaren** (GR-20261010-kompetens-integration, luckorna 1, 3 och 4). En underagent
(Task eller Agent) har en egen kontext som varken ser huvudsessionens skills eller läsningar; dess transkript
(`<session>/subagents/agent-<id>.jsonl`) läses med samma kvitto. En underagent som ändrar i koden måste själv ha läst
kärnan och aktiverat rollens skills före sin första ändring, en läsande underagent (till exempel helbyggets blinda
rubrikprov) har inga krav, och en startad underagent utan transkript är okänd och aldrig genomförd. Bara helbygget
tillåter underagenter; ateljéns och granskarnas sessioner nekar Task. Läsordningen omfattar skalet: ett Bash-anrop som
skriver under kodens väg, eller ett program som inte känns igen som läsande (ett eget skript, `python -c`, `npm install`,
en relativ väg efter `cd`), räknas som första ändringen (`bildkedja.bash_andring`). Klassningen är konservativ och avgör
bara ordningen; den är ingen sandlåda, och ett program som skriver utan att det syns i kommandot fångas bara som en
möjlig ändring. Slutgranskarens kompetens är det frysta kriteriepaketet (`metod_sha`), inte Skill-aktivering: sessionen
har inget Skill-verktyg. Läsningen av instruktionen och designreglerna observeras ur transkriptet, och en granskare som
bevisligen inte läste dem kan inte godkänna (`metodbrister`); ett saknat transkript står som inte observerat.

Rollerna arbetar där de gör nytta, en gång:

- **forska** (före planen): researchen formulerar antagandena om besökarna, frågorna och sajterna, och prövar
  territorierna med egna generiska sökningar innan frågorna skrivs; referenssteget hämtar sedan materialet med belägg.
- **planera** och **planprövning** (före skaparna): planeraren skriver omkring tio uppdrag som skiljer sig i hur
  informationen ordnas, och planprövningen prövar dem mot kunden, materialet och referenserna.
- **skapa** (skissen): skaparen tillämpar design och komposition, typografi och färg, innehåll och UX och den
  responsiva implementationen i en sammanhängande skiss. Före ägarens val ändrar ingen annan session skissen.
- **skisskritik** (inom skissförsöket): den kritiska granskaren bedömer den renderade skissen blint, med sin egen
  förhandsvisning i fyra bredder, detektorn och förebilder, och rekommenderar; skaparen svarar och avgör.
- **jamforelse**, **kritik_a** och **kritik_b** (läget full, före ägarens val): jämförelsen pekar ut falsk variation,
  granskningens första pass bedömer bilderna blint med kritikens roll, och det andra prövar motiveringen och om kundens
  material bär referensens kvalitet.
- **fordjupa** (efter ägarens val): förfiningen bygger hela sajten med samma roller och designsystemet.
- **rorelse** och **granskning** (efter fördjupningen, en gång var): interaktion och rörelse, och tillgänglighet och
  visuell granskning, på den färdiga sidan med en avgränsad interaktionsväg (förhandsvisningens tillstånd: tangentbord,
  fokus, hovring, meny, reflow 320 och reducerad rörelse). Passet redovisar tre saker var för sig: koden som ändrades,
  beteendet som prövades och den visuella bedömningen före och efter, och dessutom aktiveringen av rollens skills och, i
  rörelsen, teknikvalet per beteende (CSS, Motion, GSAP eller stilla, med skäl).

I skapandeflödets kompetensroller ska sessionen aktivera kärnskills och valda alternativ uttryckligen med Skill där
Claude Code stöder det, med Read-undantagen ovan, och läsa referensfilerna enligt skillens egna instruktioner. En aktivering eller läsning som misslyckas
syns i svaret och hanteras innan beroende arbete fortsätter. En tilldelad verktygs- eller MCP-uppgift är genomförd
först genom ett faktiskt anrop med ett kontrollerat resultat och en redovisning av hur resultatet användes; att
verktyget finns räcker inte, och kvittot skiljer aktivering, lyckad användning och bedömd kvalitet åt (ägarens
förtydligande 2026-10-07; `kontroller/kompetens.py`, `nivaer`). Externa designtjänster och Motions dokumentations-MCP
når aldrig kundens uppgifter (kontroller/kundvakt.py). Varje block nedan: rollen, uppgiften, passen, kärnan,
alternativen, verktygen, MCP:erna och vad passet visar.

Sammanfattningen kräver aktiverbara kärnskills och de alternativ som observerats fullständigt lästa; Read är inte Skill. Sparade kvitton
behåller verktygs-/MCP-utfall, och okända resultat visas som inte observerade, också när andra verktyg har lyckats.
Motion-val i kompetenspasset kräver observerat söksvar med innehåll; ett misslyckat eller tomt söksvar ger
uppgiftsbrist efter det avgränsade omförsöket, aldrig genomfört pass.

```kompetens helbygge
namn: Helbygge och leveransförberedelse
uppgift: Bygga vidare på den av ägaren godkända startsidan och dess faktiska kod, innehåll och designsystem. Bevara designversionens kvaliteter genom undersidor, responsivitet, tillgänglighet, SEO och fungerande kontaktvägar; pröva resultatet i webbläsaren. Ny formgivning kräver det befintliga designbeslutets mandat.
pass: helbygge
kärna: bygg-sajt/SKILL.md; frontend-design/SKILL.md; modern-web-guidance/SKILL.md; kunskap/byggstandard.md; kunskap/designregler.md
välj: ui-ux-pro-max/SKILL.md; impeccable/SKILL.md; better-accessibility/SKILL.md; better-typography/SKILL.md; better-colors/SKILL.md
verktyg: uxsok
mcp: refero, mobbin, 21st, motion
visar: slutbygget jämförs mot den godkända startsidan; kompletteringar anger hämtad källa eller komponent och användningsplats; tekniska prov och granskning gäller samma slutliga version. Byggsessionens egen aktivering och läsning prövas i slutposten; prototypens kvitto återanvänds inte som byggets.
```

```kompetens plan
namn: Planering och planprövning (design och innehåll)
uppgift: Skriva och pröva uppdrag med verkligt skilda designriktningar (huvudreferens, makrostruktur, typografi, bildstrategi) mot kunden, materialet och referenserna innan någon bygger.
pass: planera, planprovning
kärna: refero-design/SKILL.md; impeccable/reference/shape.md; impeccable/reference/clarify.md; kunskap/bild.md
välj: hallmark/references/macrostructures.md; hallmark/references/structure.md; frontend-design/SKILL.md; taste-soft/SKILL.md; taste-minimalist/SKILL.md; taste-brutalist/SKILL.md; ui-ux-pro-max/SKILL.md; brand/SKILL.md
verktyg: uxsok
mcp: refero, mobbin, 21st
visar: varje uppdrag formulerar en idé, vad den prövar och en uppgift för besökaren, med huvudreferensen som förslag och de observerbara egenskaper som prövas, utan exakta värden; uppdragen skiljer sig i komposition, berättelse, bildanvändning och uttryck
```

```kompetens komposition
namn: Design och komposition
uppgift: Forma en sammanhängande, kundspecifik riktning ur referenserna, kundens material och besökarens uppgift, och pröva referensens kvalitet (proportioner, komposition, bildstorlek och beskärning, komponenternas form) i kundens innehåll, eller ersätt den med något lika genomarbetat.
pass: skapa, fordjupa
kärna: refero-design/SKILL.md; impeccable/reference/craft-floor.md; kunskap/bild.md; frontend-design/SKILL.md
välj: hallmark/references/structure.md; hallmark/references/macrostructures.md; hallmark/references/component-cookbook.md; impeccable/SKILL.md; impeccable/reference/new-work.md; taste/SKILL.md; taste-soft/SKILL.md; taste-minimalist/SKILL.md; taste-brutalist/SKILL.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/delight.md; impeccable/reference/mode-persuade.md; brand/SKILL.md; banner-design/SKILL.md; better-variant/SKILL.md; ui-ux-pro-max/SKILL.md; refero-design/references/anti-ai-slop.md; refero-design/references/craft-details.md; canvas-design/SKILL.md; kunskap/skillskript.md; kunskap/materialtransport.md; kunskap/referensprofil.md
verktyg: uxsok, förhandsvisning, material, skillskript
mcp: refero, mobbin, 21st
visar: riktningen syns i den renderade sidan i mobil, mellanbredd och dator; referensens bärande kvaliteter är prövade eller ersatta med något lika genomarbetat; RIKTNING.md säger vilken synlig förbättring varje kompetens gav; skissen skiljer sig från de andra i komposition, berättelse och bildanvändning; ett koncept ur canvas-design står i BILDER.md med källa, version och Egen nej och är aldrig prototypen (metodkartan, Grafiska koncept ur canvas-design)
```

```kompetens typografi
namn: Typografi och färg
uppgift: Ge sidan typskalan, de typografiska kontrasterna, hierarkin, radlängden och färgernas roller, med stilpaketet och huvudreferensen som material, anpassade till kundens innehåll.
pass: skapa, fordjupa
kärna: impeccable/reference/typeset.md; impeccable/reference/colorize.md; better-typography/SKILL.md; better-colors/SKILL.md
välj: refero-design/references/typography.md; refero-design/references/color.md; taste-output/SKILL.md; better-ui/SKILL.md
verktyg: förhandsvisning
mcp: refero
visar: typskalan, radlängden och färgrollerna i den renderade sidan, med stilpaketets värden eller ett skäl att avvika
```

```kompetens innehall
namn: Innehåll och UX
uppgift: Göra erbjudandet begripligt och besökarens viktigaste uppgift enkel, i verksamhetens egna ord och med verifierade fakta.
pass: skapa, fordjupa
kärna: impeccable/reference/clarify.md; better-writing/SKILL.md; kunskap/copy-kontroll.md; kunskap/redaktionellt-pass.md
välj: humanizer/SKILL.md; impeccable/reference/distill.md; better-explain-interface/SKILL.md; refero-design/references/copywriting.md; hallmark/references/copy.md
verktyg: förhandsvisning
mcp: mobbin
visar: besökarens viktigaste uppgift går att lösa från första vyn; rubriker, knappar och etiketter säger vad som händer; texten låter som verksamheten
```

```kompetens responsiv
namn: Responsiv implementation
uppgift: Bygga komponenterna och layouten så att mobilens omställning är genomtänkt och 390, 768, 1280 och 1440 håller ihop, i en implementation som är enkel att underhålla.
pass: skapa, fordjupa
kärna: impeccable/reference/layout.md; impeccable/reference/adapt.md; better-layout/SKILL.md
välj: emil-mobile-native/SKILL.md; ui-styling/SKILL.md; better-ui/SKILL.md; hallmark/references/responsive.md; hallmark/references/layout-and-space.md
verktyg: förhandsvisning
mcp: mobbin
visar: mobilen och datorn, och mellanbredden där layouten byter form, i den renderade sidan; komponenterna och stilarna i egna filer där de återanvänds
```

```kompetens rorelse
namn: Interaktion och rörelse
uppgift: Välja och genomföra de beteenden som passar sidan, var och en med ett syfte, och välja tekniken per beteende med skäl: CSS först när den räcker, Motion (motion i ett <script>, motion/react i en React-ö) för fjädrar, avbrytbara gester och layoutanimationer, GSAP för tidslinjer och scrollsekvenser; ett genomtänkt beslut kan vara att något ska vara stilla, och ingen rörelse läggs till för att fylla en kvot (ägarens uppdrag 2026-10-07, punkt 5C). Beslutstabellen motion/best-practices/css-or-motion.md läses hel före valet i passet rörelse (i skissen när rörelse väljs). Motions dokumentations-MCP har sin uppgift bara genom ett faktiskt anrop med kontrollerat resultat när ett beteende byggs med Motion.
pass: skapa, rorelse
kärna: impeccable/reference/animate.md; emil-design-eng/SKILL.md; emil-animate/SKILL.md
välj: motion/best-practices/css-or-motion.md; motion/SKILL.md; motion/best-practices/index.md; motion/best-practices/motion.md; motion/best-practices/react.md; gsap/SKILL.md; gsap/gsap-core/SKILL.md; gsap/gsap-timeline/SKILL.md; gsap/gsap-scrolltrigger/SKILL.md; gsap/gsap-performance/SKILL.md; emil-find-animation-opportunities/SKILL.md; emil-review-animations/SKILL.md; emil-improve-animations/SKILL.md; emil-animation-vocabulary/SKILL.md; emil-apple-design/SKILL.md; refero-design/references/motion.md; hallmark/references/microinteractions.md; hallmark/references/interaction-and-states.md
verktyg: förhandsvisning
mcp: refero, motion
visar: varje beteende prövat med förhandsvisningens tillstånd (meny, hovring, fokus, tangentbord, reducerad rörelse) och redovisat för sig; valet CSS, Motion, GSAP eller stilla står per beteende med skäl i passets teknikval och i RIKTNING.md, och en Motion-sökning som gjordes står där med vad svaret gav; rörelse respekterar prefers-reduced-motion
```

```kompetens granskning
namn: Tillgänglighet och visuell granskning
uppgift: Inspektera den renderade sidan och interaktionsvägen, och rätta de konkreta bristerna i en avgränsad omgång utan att byta stil; bedöm återkoppling, fokus, avbrytbar rörelse, begriplighet, textstorlek och tillgänglighet i tillstånden mot principerna i kunskap/hig-principer.md, läst hel med Read (frågor att pröva, inget krav på Apples visuella stil); emil-apple-design läses hel med Read när den väljs, enligt K46:s undantag för väntande Initial Response-skills.
pass: granskning
kärna: impeccable/SKILL.md; impeccable/reference/critique.md; impeccable/reference/polish.md; impeccable/reference/audit.md; impeccable/reference/craft-floor.md; better-accessibility/SKILL.md; refero-design/references/visual-workflow.md; kunskap/hig-principer.md
välj: impeccable/reference/harden.md; impeccable/reference/optimize.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/degraded/finish-reviewer.md; better-interface-review/SKILL.md; better-interface/SKILL.md; emil-break-ui/SKILL.md; better-break/SKILL.md; taste-redesign/SKILL.md; hallmark/references/slop-test.md; hallmark/references/anti-patterns.md; emil-apple-design/SKILL.md
verktyg: förhandsvisning, detektor
mcp: refero
visar: bristerna i den renderade sidan och i tillstånden (tangentbord, fokus, reflow 320, reducerad rörelse, axe) är rättade eller motiverade, före och efter; detektorns fynd är rättade eller prövade mot ägarbesluten; återkopplingen, fokus, den avbrytbara rörelsen, begripligheten, textstorleken och tillgängligheten är bedömda mot hig-principer.md med plats och tillstånd, före och efter
```

```kompetens leverans
namn: Designsystem och överlämning
uppgift: Låta DESIGN.md och koden säga samma sak, med stilpaketets importerade värden och de valda tillstånden, så att leveransen utvecklar den godkända koden vidare.
pass: fordjupa
kärna: kunskap/bygge-referens.md; impeccable/reference/extract.md; design-system/SKILL.md
välj: impeccable/reference/document.md; taste-stitch/SKILL.md; kunskap/skillskript.md
verktyg: design, skillskript
mcp:
visar: DESIGN.md stämmer med koden, och sidorna använder dess variabler eller stilpaketets
```

```kompetens forberedelse
namn: Kundunderlag och innehåll inför design
uppgift: Förbereda verifierbara fakta, besökarnas antagna toppuppgifter och ett bearbetningsbart innehållsutkast. Skilj kundens ord från tolkningar, rekommendationer och obesvarade frågor. Budget och önskad tid är inte ett accepterat kommersiellt åtagande.
pass: forbered
kärna: kunskap/kundintervju.md; kunskap/research-underlag.md; kunskap/brief-mall.md; better-writing/SKILL.md
välj: impeccable/reference/clarify.md; humanizer/SKILL.md; kunskap/redaktionellt-pass.md
verktyg:
mcp:
visar: RESEARCH.md, BRIEF.md, TEXTUNDERLAG.md och BESTALLNING.md med belägg, hypoteser och öppna frågor; inga påhittade uppgifter. Referenssökning och designbedömning kommer i nästa pass. WebSearch/WebFetch får bara publika sökfrågor och adresser; privat kundmaterial skickas inte som sökfråga. Skill-laddning visar metodåtkomst, inte att slutsatserna är verifierade.
```

```kompetens forska
namn: Research och referensjakt
uppgift: Formulera antagandena om besökarna som kan ändra designbesluten, och undersöka visuella förebilder, besökarflöden och återanvändbar kod innan riktningarna bestäms. Refero ger stil, skärmar och sajter; Mobbin ger sektioner och flöden; 21st ger komponenter och teman att pröva som implementationsgrund. Sök generiskt i alla tre och granska resultaten före planen. För vidare id, källa, användningsplats och skäl för urval eller bortval; en vald komponent hämtas med kod, licens och beroenden, och en skärmbild kallas aldrig kodmall.
pass: forska
kärna: kunskap/referensjakt.md; refero-design/SKILL.md; refero-design/references/mcp-tools.md
välj: kunskap/referenser-professionella.md; impeccable/reference/shape.md; better-explain-interface/SKILL.md; hallmark/references/macrostructures.md; ui-ux-pro-max/SKILL.md; refero-design/references/example-workflow.md
verktyg: uxsok
mcp: refero, mobbin, 21st
mcp-krav: refero, mobbin, 21st
visar: frågorna och sajterna spänner över skilda grundidéer ur verksamhetens värld och är prövade mot vad tjänsterna har; varje antagande har underlag eller "ännu inte observerat", en prövning och en följd; ett tomt eller misslyckat prov står som det är och är inget material
```

```kompetens kritik
namn: Kritik av den renderade sidan, blind
uppgift: Bedöma den renderade sidan som en besökare ser den, mot ribban, besökarens uppgift och ägarens aktuella domar i uppdraget, blind för skaparens text, uppdrag, referenspaket och kod och för tidigare riktningar (domloggen och riktningshistoriken är stängda som filer, och äldre domar slås inte upp): i mobil, mellanbredd och dator var för sig, och med menyn öppen, tangentbordet och reflow, första vyns huvudkomposition, hierarkin, bildval, bildskala och beskärning, rytmen och de typografiska kontrasterna, och om sidan har kundens särprägel eller om samma form kunde användas av nästan vilket lokalt tjänsteföretag som helst i branschen (generisk), prövat mot en eller två professionella förebilder av samma slag; och det bilderna visar av återkoppling, fokus, begriplighet, textstorlek och tillgänglighet i tillstånden (menyn öppen, tangentbordet, hovring och fokus på begäran, reflow 320) mot principerna i kunskap/hig-principer.md (läst hel med Read), där det som ingen bild visar står som inte bedömt.
blind: i underlag/<slug> läser rollen bara briefen och kundens fakta och material (BRIEF.md, VERKSAMHET.json, RESEARCH.md, texten, BESTALLNING.md, bilder/), metoden och kandidatens egna bilder; kunder/<slug>, de andra kandidaterna, research på begäran (REFERENSUPPDRAG-*, TJANSTEUPPDRAG-*, också när de uppstår under sessionen), referensbeslutet, referenspaketet och de läsande skalkommandona nekas (kandidater.blind_nekas). Riktningshistoriken och domloggen nekas som filer (RIKTNINGSHISTORIK.json, DESIGNDOMAR.jsonl): ägarens beslut 2026-10-07 ("Ja, neka historiken"; GR-20261007-r103#K4). Ägarens aktuella domar står i uppdraget, och kritiken dömer mot dem och ribban, inte mot tidigare riktningar (ägaren 2026-10-06: "Mina tidigare underkännanden ska inte omvandlas till en allt smalare uppsättning tillåtna uttryck"). Ändras i kandidater.BLIND_HISTORIK, i uppgiften ovan och på den här raden.
pass: skisskritik, kritik_a, fore_efter
kärna: kunskap/designregler.md; kunskap/referenser-professionella.md; impeccable/reference/critique.md; impeccable/reference/craft-floor.md; kunskap/hig-principer.md
välj: hallmark/references/slop-test.md; hallmark/references/anti-patterns.md; refero-design/references/anti-ai-slop.md; kritik/GRANSKARE.md; frontend-design/SKILL.md; better-interface-review/SKILL.md; better-accessibility/SKILL.md; emil-break-ui/SKILL.md; ui-ux-pro-max/references/quick-reference.md; impeccable/reference/audit.md
verktyg: förhandsvisning, detektor
mcp: refero, mobbin
visar: svaret belägger kandidatens version och bilderna som bedömdes; en bredd (390, 768, 1280, 1440) eller ett tillstånd (menyn öppen, tangentbordet, reflow 320) räknas som bedömt bara ur en bild som lästes och inte är tom, också när svaret nämner det; kvittot visar kärnan, de valda alternativen, verktygsanropen och tjänsternas anrop med utfall; varje synligt problem har plats, bredd och vad, det största först; förebilderna står med vad jämförelsen visade; skissens rekommendation är fortsätt, byt komposition eller förkasta riktningen, och första passet i läget full ger nivån mot ribban
```

```kompetens jamforelse
namn: Falsk variation
uppgift: Se alla kandidaters första vyer och hela sidor och peka ut de par som är samma struktur och berättelse med andra färger, typsnitt eller bilder, med makrostrukturen och den axel som skiljer dem (struktur, täthet, betoning, typografi, röst).
pass: jamforelse
kärna: hallmark/references/macrostructures.md; better-variant/SKILL.md
välj: hallmark/references/structure.md; refero-design/references/anti-ai-slop.md; kunskap/referenser-professionella.md
verktyg:
mcp:
visar: varje utpekat par säger vad som är lika (makrostrukturen, berättelsen, det som möter besökaren först) och varför skillnaden bara är ytlig; par som skiljer sig i struktur pekas inte ut
```

```kompetens motivering
namn: Motiveringen och referensens kvalitet
uppgift: Pröva för varje avvikelse som granskningens första pass fann om den är avsiktlig och välgrundad (skäl i kundens behov, material eller huvudreferensen, och fungerar för besökaren), och om kundens material bär den kvalitet i referensen som uppdraget ville återskapa, i de fyra relationerna med kandidatens bild och referensbilden bredvid varandra.
pass: kritik_b
kärna: kunskap/bild.md; refero-design/references/visual-workflow.md
välj: kunskap/referenser-professionella.md; refero-design/SKILL.md; refero-design/references/craft-details.md; kritik/GRANSKARE.md; hallmark/references/imagery-kit.md
verktyg:
mcp:
visar: varje avvikelse har avsiktlig och välgrundad med skäl; referensens kvalitet är bedömd i de fyra relationerna (bildens beskärning mot rubriken, de typografiska storlekarna och hierarkin, täta och luftiga sektioner och rytmen, navigation och interaktion mot innehållet)
```

**Skälen för de bedömande och forskande rollerna** (ägarens ord 2026-10-07: "Du behöver ju fixa luckan där med de verktyg
vi har tillgängliga"). Kritikens kärna är det som avgör om en skiss bär: kvalitetskraven och ägarbesluten
(`designregler.md`, Helhet och hierarki; nivåfilen ur de gamla ankarna är borttagen vid den rena designstarten), jämförelsen
med en förebild av samma slag i bredder och tillstånd som går att jämföra
(`referenser-professionella.md`), Impeccables kritik (om formen är skriven för just den här verksamheten eller utbytbar,
hierarkin, den kognitiva belastningen, heuristikerna och personerna) och golvet för hantverket (`craft-floor.md`). Kärnan
är omkring 60 000 tecken och ryms i kritikens frist (mätningen i `BESLUT.md`, tillägget 2026-10-07). Listorna över
AI-mönster och slop (hallmark, refero-design) är alternativ, eftersom de är frågor och inte regler (Avgörandena), och
granskarens fem kriterier (`kritik/GRANSKARE.md`) är skrivna för helbygget. Researchens kärna är vår referensjakt,
Referos researchmetod och tjänstens verktyg, som researchen nu själv använder. Jämförelsens kärna ger orden för en
sidas form (21 makrostrukturer) och för vad som skiljer två förslag på riktigt (en axel, inte en nyans). Andra passets
kärna är art direction mot kundens material (`bild.md`) och Referos visuella kontroll mot referenslåset.

**Verktyg och tjänster som en roll inte har.** Kritiken har inte uxsok: UI UX Pro Max ger allmänna riktlinjer med
kodexempel (prövat 2026-10-07: frågan "carpenter renovation landing page" i domänen ux gav bildoptimering och en aktiv
menypunkt, och frågan "home services contractor" i domänen landing ingen träff), och det kritiken ser i bilderna täcker
kärnan; verktyget skulle ta tid ur kritikens frist. Jämförelsen och granskningens andra pass har inga verktyg och inga tjänster: de jämför renderingar som
redan finns i alla bredder (alla kandidaters bilder; kandidatens bilder bredvid uppdragets referensbilder), och en ny
rendering eller sökning skulle bedöma något annat än det skaparen fick i uppdrag att föra över.

**HIG-principerna i interaktionsgranskningen** (ägarens uppdrag 2026-10-07, punkt 5E). `kunskap/hig-principer.md` är
kärna i rollerna granskning och kritik och ger frågorna om återkoppling, fokus, avbrytbar rörelse, begriplighet,
textstorlek och tillgänglighet, var och en med Apples sida som källa och i våra ord; `emil-apple-design` är alternativ
i granskningen för fysisk, avbrytbar rörelse. Principerna gäller hur sidan beter sig och läses, inte hur den ser ut:
inget krav på Apples visuella stil, huvudreferensen bär fortsatt layout, palett och typografi (Avgörandena), och
kvalitetskraven förblir kraven medan principerna är frågor. Kritiken bedömer bara det bilderna visar.

**Grafiska koncept ur canvas-design** (ägarens uppdrag 2026-10-07, punkt 5D). Skillen `canvas-design` (Apache-2.0,
`.claude/skills/canvas-design/KALLA.md`) är alternativ i rollen komposition för grafiska koncept, illustrationer och
statiska kompositionsstudier: en bild som prövar en komposition, ett mönster eller en illustration för en bildplats
innan sidan byggs, eller där kundens material saknas. Skillen aktiveras med Skill-verktyget när den väljs; en
aktivering som nekas eller misslyckas står i RIKTNING.md med felet, och skillen räknas då inte som använd. Skillens
egen arbetsgång (filosofin som .md, sedan kanvasen) gäller konceptet, inte sessionen: passets uppgift och svar är
oförändrade, och skillens "Output only .md, .pdf, .png" gäller aldrig sessionen som helhet (prövat 2026-10-07: en
nästlad session läste de injicerade instruktionerna som ett nytt uppdrag och stannade; kvittot visade ändå
aktiveringen, vilket är skillnaden mellan aktivering, användning och kvalitet). En PNG eller
PDF ur skillen är ett koncept och ett material- och
designunderlag, aldrig en fungerande responsiv prototyp: kandidaten är den byggda sidan i 390, 768, 1280 och 1440, och
ett koncept bedöms aldrig i dess ställe. Orden i ett koncept kommer ur underlaget (Sanning), och ett koncept utger sig
aldrig för att visa verksamheten (Bilder). Det som används registreras i `underlag/<slug>/atelje/kandidater/<id>/koncept/BILDER.md` (`kunskap/bild.md`
hänvisar hit; formen står här för att bild.md ingår i skaparens kärna, som hålls under 160 000 tecken) på en rad med
`fil` `<plats>__koncept-<beskrivning>.<png|pdf|svg>`; `källa` `canvas-design @ <commit ur KALLA.md>`, filosofifilen
(`<namn>.md`) och vem som gjorde den (kandidat och version, eller sessionen utanför flödet); `visar` (plats, uttryck,
format och beskärning, och ordet koncept); `datum`; `kvalitet` efter renderingen i kompositionen; och `Egen` nej:
`atelje.egna_bilder` tar aldrig med en rad som nämner koncept eller canvas-design bland verksamhetens egna bilder,
också om kolumnen saknas eller säger ja. Typsnitten i `canvas-fonts/` är OFL-1.1 med licensfil per familj; en PNG
rasteriserar texten, en PDF bäddar in typsnittet, som då står i `TYPSNITT-IKONER.json` när filen levereras. Ett koncept
som bara var en studie står kvar i samma kandidats koncept/BILDER.md som underlag. Ett koncept som ska in i sidan går
genom materialsteget (`kontroller/material.py --canvas`, roll koncept; uppdraget 2026-10-08, 2D), som lägger det i
kandidatens src/assets/material/ med källa och rättigheter. Bild, filosofi och skapartext
stannar i kandidatens konceptkatalog, som blindkritiken inte får läsa; de läggs aldrig i gemensamma `bilder/`.
Gemensamma kundbilder och deras faktauppgifter är fortsatt läsbara. Ett koncept som används i sidan bedöms i sidans
rendering, utan att ge blindkritiken andra studier eller skaparens avsikt. Materialsteget (gren H4 i uppdraget) får
uppdraget att ta koncepten som ingång: ett koncept som ska bli en tillgång får ett konkret visuellt uppdrag
(användningsplats, uttryck, format, beskärning, vad det ska bidra med), webboptimeras genom `astro:assets` och
registreras med källa och vald version. Skaparen skriver den statiska SVG-studien i sin konceptkatalog och ett
uppdrag i kompetens/skriptuppdrag/. `skillskript.py` renderar PNG/PDF med befintligt Playwright, utan Pillow eller
reportlab; i sandlådan delegeras just renderingen till webbtjänsten. Resultat och kvitto ligger i kandidatens
kompetens/skillskript/ och importeras därifrån med `material.py --canvas`. Kontrakt: `kunskap/skillskript.md`.

**Sessioner utan block**, för närvarande tom även för läget full och dess objektiva rättelser. Den enda listan över kandidatflödets sessioner utan en roll (`kontroller/kandidater.py`, varje
`atelje.session`): funktionen och skälet. `kontroller/kompetens.py --prova` jämför listan med koden, så att en session
utan block och utan skäl, eller ett skäl som bara säger "ingen tilldelning", fälls.

```sessioner-utan-block
```

**Tjänsternas verktyg** (ägarens uppdrag 2026-10-07, punkt 2 och 3): ett beslut per verktyg som Refero, Mobbin och
Motions dokumentations-MCP visar, uppgift eller ingen uppgift med skäl och provdatum. Verktygen med uppgift är exakt de
som kundvakten släpper (`referenstjanster.TJANSTER` för referenstjänsterna, som också helbyggets A/B-prövning läser, och
`kompetens.MCP` för Motion, vars server inte är en referenstjänst), och `kontroller/kompetens.py --prova` säger till
när kartan och listorna skiljer sig. Ett upptäckt verktyg utan rad här nekas av kundvakten tills beslutet är skrivet;
startkvittot visar besluten (`kunskap/beroenden.md`, Vad startkvittot säger).

```tjanstverktyg refero
refero_search_styles: uppgift — researchens stilfrågor (typ stil) i skilda estetiska territorier, och huvudreferensens stil i planen
refero_get_style: uppgift — stilens belagda värden (typografi, färger, layout, rytm, komponenter) i researchen och huvudreferensens stilpaket (kontroller/stilpaket.py)
refero_search_screens: uppgift — skärmar för första vyn, projekt- och tjänstesidor, förtroende och kontakt (typ skarm), i researchen och i skaparnas egna sökningar
refero_get_screen: uppgift — skärmens typsnitt, färger, sidtyper och element, och skärmens bild i full storlek
refero_get_similar_screens: uppgift — bredda från en stark träff till fler lösningar på samma uppgift
refero_get_screen_image: uppgift — skärmens bild när svaret saknar den
refero_search_flows: uppgift — flöden för förfrågan och projektgenomgång (typ flode)
refero_get_flow: uppgift — flödets steg i ordning, med bilderna
refero_search_sites: uppgift — hela sajter som förlagor till referenspaketet
refero_search_apps: ingen uppgift — i webbflödet, eftersom verktyget bara söker iOS-appar: dess egen beskrivning säger "Search iOS apps in Refero" och hänvisar webbplatser till refero_search_sites, och provet med frågan "home builder construction" gav 10 av 100 träffar, alla iOS-appar som LEGO Builder, Asana och LinkedIn, ingen om byggande eller lokala tjänster; dess nytta är ett app-id för iOS-skärmar och iOS-flöden, och webbflödet söker skärmar, sajter och flöden med refero_search_screens, refero_search_sites och refero_search_flows; prövat 2026-10-07
```

```tjanstverktyg mobbin
search_screens: uppgift — sidor och tillstånd för besökarens uppgift, i researchen och i uppdragens material (en sökfras per uppdrag)
search_flows: uppgift — användarresor med stegen i ordning
search_sections: uppgift — avgränsade sektioner, som ett formulärsteg eller en projektlista
```

**Chrome DevTools MCP** (ägarens uppdrag 2026-10-07, punkt 7 och 5; version och källa i `kunskap/beroenden.md`) körs bara
i en egen inspektionssession (`kontroller/devtools.py`, konfigurationen `kontroller/mcp/chrome-devtools.json` med
`--strict-mcp-config`), aldrig i skaparens eller kritikens session och aldrig på användarnivån. Den tillför det Playwright
inte ger: prestandaspåret med Chromes insikter och Lighthouse mot en främmande sajt. Det som bara dubblerar
`inspektera.mjs` och `extrahera.mjs` har ingen uppgift, och kategorierna inmatning, minne och skriptkörning är avstängda i
konfigurationen. Verktygen med uppgift är exakt de sessionen släpper (`devtools.VERKTYG`). Kvittot skiljer aktivering
(MCP:n ansluten), lyckad användning (anropet gav kontrollerat resultat) och bedömd kvalitet (kritiken och ägaren);
installation eller "connected" är ingen genomförd uppgift (ägarens förtydligande 2026-10-07).

```tjanstverktyg chrome-devtools
new_page: uppgift — öppnar referensens adress i den isolerade, huvudlösa Chrome bakom nätgränsen; den enda sidan sessionen öppnar
emulate: uppgift — mobilprofilen (390×844, 2×, mobil, pekskärm) och nätstrypning före prestandaspåret, så att måtten gäller en mobil besökare
performance_start_trace: uppgift — prestandaspåret med omladdning: LCP, CLS, TTFB och insikterna (LCP-nedbrytning, renderblockerande resurser, bildleverans, layoutskiften, dokumentlatens); det Playwright-spåret inte ger
performance_stop_trace: uppgift — avslutar ett spår som inte stoppades automatiskt
performance_analyze_insight: uppgift — varje insikt i detalj, med talen; sammanfattas i DEVTOOLS.md
take_snapshot: uppgift — tillgänglighetsträdet med uid per element, som get_css_styles behöver; trädet självt dubblerar ariaSnapshot i inspektera.mjs
get_css_styles: uppgift — reglerna för det element som bär första vyn (LCP-elementet) och huvudrubriken; de standardmätta elementens regler kommer ur extrahera.mjs (CSS.getMatchedStylesForNode)
list_network_requests: uppgift — antalet anrop och de största resurserna (bilder, typsnitt, stilar, skript) som insikterna pekar på
lighthouse_audit: uppgift — Lighthouse-poängen för referensen (mobil, navigation: tillgänglighet, bästa praxis och seo; prestandakategorin utesluter verktyget självt, prestandan kommer ur spåret); kontroller/lighthouse.mjs mäter bara byggets lokala server
get_network_request: ingen uppgift — svaret kan spara en resurs kropp (sajtens kod) till disk, och storlek och status står redan i list_network_requests; prövat 2026-10-07
take_screenshot: ingen uppgift — skärmbilderna tas av inspektera.mjs i samma bredder som prototypen och i paketets filkontrakt; en bild här saknar vyernas mått; prövat 2026-10-07
list_console_messages: ingen uppgift — konsolen loggas redan av inspektera.mjs (gemensamt.oppna) i varje vy; prövat 2026-10-07
get_console_message: ingen uppgift — se list_console_messages; ett enskilt meddelande ger inget mer för designunderlaget; prövat 2026-10-07
evaluate_script: ingen uppgift — fri skriptkörning i referensens sida för sajtens kod in i underlaget; extrahera.mjs mäter med fasta skript; avstängt med --no-javascript-evaluation; prövat 2026-10-07
resize_page: ingen uppgift — emulate täcker vyn; svepet över bredderna görs av inspektera.mjs --svep i Playwright; prövat 2026-10-07
navigate_page: ingen uppgift — new_page öppnar adressen och spåret laddar om själv; ingen bläddring på en främmande sajt i en läsande inspektion; prövat 2026-10-07
list_pages: ingen uppgift — sessionen har en sida, den som new_page öppnade; prövat 2026-10-07
select_page: ingen uppgift — en sida, se list_pages; prövat 2026-10-07
close_page: ingen uppgift — sessionen stängs av kontroller/devtools.py när kvittot är skrivet; prövat 2026-10-07
wait_for: ingen uppgift — new_page väntar in laddningen, och spåret laddar om själv; väntan på text gäller dynamiska appar; prövat 2026-10-07
click: ingen uppgift — läsande inspektion klickar inte; menyn i verkligt tillstånd fångas av inspektera.mjs --meny; kategorin inmatning är avstängd; prövat 2026-10-07
click_at: ingen uppgift — koordinatklick (experimentellt); läsande inspektion klickar inte; kategorin inmatning är avstängd; prövat 2026-10-07
hover: ingen uppgift — hovring fotograferas av inspektera.mjs --hover med flera väljare per uppdrag; kategorin inmatning är avstängd; prövat 2026-10-07
fill: ingen uppgift — inga inskick på främmande sajter (kunskap/referensjakt.md); kategorin inmatning är avstängd; prövat 2026-10-07
fill_form: ingen uppgift — se fill; kategorin inmatning är avstängd; prövat 2026-10-07
type_text: ingen uppgift — se fill; kategorin inmatning är avstängd; prövat 2026-10-07
press_key: ingen uppgift — tangentbordsvägen prövas av inspektera.mjs (gemensamt.tangentbord, 25 steg); kategorin inmatning är avstängd; prövat 2026-10-07
drag: ingen uppgift — ingen interaktion som flyttar innehåll i en läsande inspektion; kategorin inmatning är avstängd; prövat 2026-10-07
upload_file: ingen uppgift — inget lämnar maskinen till en referenssajt; kategorin inmatning är avstängd; prövat 2026-10-07
handle_dialog: ingen uppgift — en kakdialog är ett sidelement, ingen webbläsardialog; den står som begränsning i paketet (referens.observationer); prövat 2026-10-07
screencast_start: ingen uppgift — videon kräver ffmpeg och är stor; rörelsesekvensen kommer ur Playwright-spåret och sidans animationer (extrahera.mjs); prövat 2026-10-07
screencast_stop: ingen uppgift — avslutar en inspelning som aldrig startas (se screencast_start); prövat 2026-10-07
```

```tjanstverktyg motion
search-motion-docs: uppgift — rollen rorelses sökning i Motions dokumentation, exempel och Motion UI (platform js för motion i ett <script>, react för motion/react i en React-ö; sökordet är mönstret som byggs: inView, stagger, spring, layout) när ett beteende byggs med Motion; svaret är text och länkar, inga bilder, och träffar märkta Motion+ (betalda) används inte (ägarens beslut 2026-10-07: bara den fria delen); prövat 2026-10-07
generate-css-easing: ingen uppgift — verktyget står i skillen (motion/codex/index.md och css-spring/index.md) men fanns inte på servern vid tools/list, så CSS-fjädrar skrivs för hand med linear() eller cubic-bezier tills verktyget finns och prövats; prövat 2026-10-07
```

```tjanstverktyg 21st
search: uppgift — researchens undersökning före planen och kompositionens kompletterande komponent- och temaresearch i 21st.dev Builder (fritt): generiska sökningar efter komponenttyper för besökarens uppgift (hero, tjänstelista, kontaktformulär, galleri) och teman (type "theme"), aldrig kundens uppgifter; svaret är metadata med förhandsbild och id, som bedöms innan något hämtas (förhandsbilderna är 21st:s och visas aldrig för kunden)
get_component: uppgift — hämtning av en vald komponents kod och demo med installationskommando och beroenden (förbrukar Builders dagliga hämtningar; svaret kan vara låst eller saknat och är då inget material); koden är material att anpassa till riktningen, mallens CSS och CSP:n, aldrig ett paket som installeras på egen hand (kunskap/beroenden.md); källan (adressen), författaren, licensen och beroendena skrivs i RIKTNING.md under Referenser
get_inspiration: uppgift — inspirationsflödet som generisk förebild för komposition och detaljer, bedömt som referensbilder och aldrig kopierat rakt av
search_logo: ingen uppgift — logotyper tillhör kunden och hämtas ur kundens underlag, aldrig genom en logotypsökning i katalogen; prövat 2026-10-08
search_picker: ingen uppgift — ett interaktivt urvalsverktyg för en människa i Builder; sessionen söker med search och bedömer själv; prövat 2026-10-08
get_profile: ingen uppgift — profilen på 21st.dev är ägarens konto och ändras aldrig av flödets sessioner; prövat 2026-10-08
edit_profile: ingen uppgift — profilen på 21st.dev är ägarens konto och ändras aldrig av flödets sessioner; prövat 2026-10-08
upload_profile_media: ingen uppgift — profilen på 21st.dev är ägarens konto och ändras aldrig av flödets sessioner; prövat 2026-10-08
get_usage: ingen uppgift — kvoten för hämtningar läses av ägaren eller underhållet, inte av skaparsessionen; prövat 2026-10-08
bookmark: ingen uppgift — bokmärken och listor är kontots egna; flödets urval skrivs i RIKTNING.md med källa och licens; prövat 2026-10-08
create_bookmark_list: ingen uppgift — bokmärken och listor är kontots egna; flödets urval skrivs i RIKTNING.md med källa och licens; prövat 2026-10-08
add_to_list: ingen uppgift — bokmärken och listor är kontots egna; flödets urval skrivs i RIKTNING.md med källa och licens; prövat 2026-10-08
get_bookmark_list: ingen uppgift — bokmärken och listor är kontots egna; flödets urval skrivs i RIKTNING.md med källa och licens; prövat 2026-10-08
list_bookmark_lists: ingen uppgift — bokmärken och listor är kontots egna; flödets urval skrivs i RIKTNING.md med källa och licens; prövat 2026-10-08
list_bookmarks: ingen uppgift — bokmärken och listor är kontots egna; flödets urval skrivs i RIKTNING.md med källa och licens; prövat 2026-10-08
list_teams: ingen uppgift — teamets bibliotek hos 21st.dev är tomt, och kundens kod läggs aldrig där; prövat 2026-10-08
list_team_components: ingen uppgift — teamets bibliotek hos 21st.dev är tomt, och kundens kod läggs aldrig där; prövat 2026-10-08
list_team_libraries: ingen uppgift — teamets bibliotek hos 21st.dev är tomt, och kundens kod läggs aldrig där; prövat 2026-10-08
list_team_lists: ingen uppgift — teamets bibliotek hos 21st.dev är tomt, och kundens kod läggs aldrig där; prövat 2026-10-08
submit_component: ingen uppgift — publicering eller ändring av komponenter i katalogen är extern publicering som kräver ägarens beslut; kundens kod lämnar aldrig repot den vägen; prövat 2026-10-08
resubmit_component: ingen uppgift — publicering eller ändring av komponenter i katalogen är extern publicering som kräver ägarens beslut; kundens kod lämnar aldrig repot den vägen; prövat 2026-10-08
edit_component: ingen uppgift — publicering eller ändring av komponenter i katalogen är extern publicering som kräver ägarens beslut; kundens kod lämnar aldrig repot den vägen; prövat 2026-10-08
delete_component: ingen uppgift — publicering eller ändring av komponenter i katalogen är extern publicering som kräver ägarens beslut; kundens kod lämnar aldrig repot den vägen; prövat 2026-10-08
withdraw_component: ingen uppgift — publicering eller ändring av komponenter i katalogen är extern publicering som kräver ägarens beslut; kundens kod lämnar aldrig repot den vägen; prövat 2026-10-08
remove_component_from_catalog: ingen uppgift — publicering eller ändring av komponenter i katalogen är extern publicering som kräver ägarens beslut; kundens kod lämnar aldrig repot den vägen; prövat 2026-10-08
edit_template: ingen uppgift — teman och mallar hos 21st.dev är kontots; flödets stilpaket kommer ur Refero och mallens CSS (stilpaket.py); prövat 2026-10-08
delete_template: ingen uppgift — teman och mallar hos 21st.dev är kontots; flödets stilpaket kommer ur Refero och mallens CSS (stilpaket.py); prövat 2026-10-08
edit_theme: ingen uppgift — teman och mallar hos 21st.dev är kontots; flödets stilpaket kommer ur Refero och mallens CSS (stilpaket.py); prövat 2026-10-08
delete_theme: ingen uppgift — teman och mallar hos 21st.dev är kontots; flödets stilpaket kommer ur Refero och mallens CSS (stilpaket.py); prövat 2026-10-08
get_theme: uppgift — ett tema ur 21st.dev (CSS-variabler i :root och .dark i shadcn-format, oklch-färger, ur förinställningar eller utdraget ur verkliga sajter) som implementationsgrund av slaget tema, när planen anger det. Temats id kommer ur search med type "theme" och en generisk fråga (teman saknar beskrivning, så en beskrivande fråga ger en tom lista; prövat 2026-10-09). Värdena mappas till projektets CSS-variabler med bevarade roller och märks `valt:` med källan i DESIGN.md, ett webbplatstemas varumärkesursprung skrivs i RIKTNING.md, och temat är aldrig ett paket. Mallar ger i search bara metadata, pris och adress (prövat 2026-10-09), har inget sessionsverktyg för koden och väljs bara av en människa
get_generation: ingen uppgift — genererade komponenter ur Builder beställs inte av sessionen; en färdig komponent hämtas med get_component när den valts; prövat 2026-10-08
get_generation_job: ingen uppgift — genererade komponenter ur Builder beställs inte av sessionen; en färdig komponent hämtas med get_component när den valts; prövat 2026-10-08
get_changes: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
get_notes: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
update_note: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
get_take: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
edit_take: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
record_take_outcome: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
record_inspiration_feedback: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
send_feedback: ingen uppgift — anteckningar, utfall och återkoppling till 21st.dev är kontots dialog med tjänsten, inte designarbetet; prövat 2026-10-08
video_apply_ops: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_create_project: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_export: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_export_status: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_finalize_asset: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_get_doc: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_list_blocks: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_propose_variants: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_search_blocks: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_snapshot: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
video_upload_asset: ingen uppgift — videoverktygen hör till materialsteget (uppdraget 2026-10-08, 2D), som byggs med egen mekanik och kräver ägarens kontobeslut; prövat 2026-10-08
```

Om ägaren vill kan refero_search_apps få en smal roll i researchen: en namngiven app som förebild för ett mobilflöde.
Då förs verktyget in i `referenstjanster.TJANSTER` och i tjänstesessionens uppdrag, och raden ovan blir en uppgift.

**Tillståndsorden** (ägarens uppdrag 2026-10-07, punkt 3): startkvittot och kompetensens kvitton skiljer på
tillgängligt, provat och fungerande, tilldelat en uppgift, använt med resultat, planerat i ett senare steg, blockerat
eller misslyckat och inte observerat, och inte observerat skiljs från inte gjort (observatören såg sessionen men ingen
användning). Ett läskvitto är belägg för läsning, inte för tillämpning: att kärnan lästs hel säger inte att den
tillämpats, och ett lyckat anrop säger inte att svaret blev användbart material. Orden står i `kontroller/kompetens.py`
(`TILLSTAND`, och `tillstand` för kompetenskvittot).

**Ingen uppgift i flödet**, den enda listan över skills utan roll (de finns i verktygslådan; en skill i ett
kompetensblock ovan har sin uppgift där): emil-write-swift (Swift), emil-animate-expo (React Native och Expo),
emil-ask-sonner (en toast i en app), slides (presentationer), taste-imagegen-frontend-mobile (appskärmar),
emil-pick-ui-library (paketval görs utanför flödet, `kunskap/beroenden.md`), emil-prototype (kandidaterna är
varianterna), taste-v1 (ersatt av taste), taste-gpt (fast AIDA-ordning mot K22; dess GSAP-recept används inte heller
sedan GSAP togs in 2026-10-07, eftersom rollen rorelse väljer CSS, Motion eller GSAP per beteende med skillen gsap och
`kunskap/beroenden.md`). Bildgenererande skills (design, taste-brandkit, taste-imagegen-frontend-web, taste-image-to-code) kräver
en bildgenerator som flödets sessioner inte har; illustrativt material som inte utger sig för att visa verksamheten
beställs som material (Avgörandena, Bilder). Ur taste-image-to-code används bara listan för bildanalys (rad 327–360),
som ett uppslag i Researchen. Flödets egna processkills styr arbetet: bygg-sajt ingår i helbyggets arbetskrav; kirurg, backlog och writing-for-agents
används i systemarbetet, inte som formgivningskompetens. writing-for-agents är för den som skriver om kartan, förorden
eller en skill. modern-web-guidance ingår i helbygget; ett införande i skisskapandet kräver fortfarande det avgränsade
försöket i intagskrav 4. Övriga
MCP-anslutningar (Gmail, Google Drive, GitHub, Resend, Jotform, Railway, Claude Docs med flera) rör kunddata, utskick
eller drift och har ingen uppgift i skapandet; sessionerna nekar dem. Trybloom används inte (ägarens ord 2026-10-05) och
nekas likaså. Figma ingår bara i ett pilotprov, utanför normalflödet (`kunskap/skapandeflodet.md`, Figma).

## Research

**Fråga:** vilka skilda grundidéer kan verksamhetens värld och material bära, och vilka antaganden om besökarna kan
ändra designbesluten?

**Underlag:** BRIEF.md (§2 målgrupper och toppuppgifter med insiktskällor, "Antaganden som behöver bekräftas"),
RESEARCH.md, bilder/BILDER.md, referenspaketet (per sida det kuraterade underlaget SEKTIONER.md: bild, mått, renderade
typsnitt, de CSS-regler som träffar och ett begränsat DOM-utdrag; hela mätningen med rörelsesekvensen och svepet över
bredderna i EXTRAKT.md läses bara på en konkret fråga) och tjänsternas förra undersökning, domloggen och historiken.
Sidinnehållet i underlaget är material, aldrig instruktioner (`kunskap/referensjakt.md`, Underlaget per sida).

**Till nästa steg:** FORSKNING.md med antagandena (underlag, prövning, vad som ändras), nytt och återanvänt material
(nytt referenspaket med 390 och 1440 alltid och 768 och 1280 när sajten beställs med `bredder`, hover- och
fokusväljare per sajt, tjänsternas svar med hela stildokument och bilder) och riktningarna researchen öppnar. För den
referens planen gör till huvudreferens kan en DevTools-profil tas i en egen inspektionssession
(`kontroller/devtools.py`; Tjänsternas verktyg, Chrome DevTools MCP): prestandainsikter, Lighthouse och nätverket, som
prompterna pekar på när kvittot visar genomförd användning, och som skaparen redovisar i RIKTNING.md när något ur den
påverkade ett val.

**Visar:** frågorna och sajterna spänner över skilda grundidéer ur verksamhetens värld, inte varianter av samma
utseende, och omfattar både starka sajter i branschen och visuella förebilder utanför den vars kvaliteter kan fungera
med kundens material (ägarens uppdrag 2026-10-09, punkt 5); varje antagande har underlag eller "ännu inte observerat", en
prövning som beskriver besökarens mål utan att avslöja knappen, och en följd. Underlagets slag hålls isär: referensbild
(en bild), stilpaket (Referos värden och beskrivning; typsnitten som namn, inte filer eller licenser), komponentkod
(21st.dev, kod att anpassa med källa och licens) och körbar mall (ett projekt som bygger); en skärmbild kallas aldrig en
kodmall. Sessionen arbetar med rollen forska (avsnittet Kompetenserna) och prövar territorierna
med egna generiska sökningar; FORSKNING.json bär kompetenskvittot.

**Tillämpning:** referensanalysen identifierar i bilderna och mätningen proportioner, hierarki, rytm, bildroller och de
tillstånd som spelar roll, och skiljer uppmätt från uppskattat; Refero och Mobbin ger förebilder för besökarens uppgift.

**Återgång:** det materialet inte räcker till står i FORSKNING.md som ännu inte observerat eller som beställning, och
planprövningen kan begära mer research för ett uppdrag (återgången, en per plan).

```utdrag före
kunskap/designregler.md
kunskap/referensjakt.md
```

```utdrag uppslag
kunskap/referenser-professionella.md
frontend-design/SKILL.md rad 11–13, 38–45
impeccable/reference/new-work.md rad 45–46
better-explain-interface/SKILL.md rad 26–35, 54–107
taste-image-to-code/SKILL.md rad 327–360
```

## Plan

**Fråga:** vilka lösningar besvarar kundens problem på verkligt olika sätt, och varför skulle var och en passa
verksamheten och besökaren?

**Underlag:** FORSKNING.md, referenspaketet, tjänsternas svar, kundens material och briefen, domloggen och historiken.

**Till nästa steg:** ett uppdrag per kandidat (UPPDRAG.md): hypotesen, idén, den viktiga uppgift besökaren ska klara,
innehållet som hjälper besökaren att fatta beslut, hur förslaget prövas (en besökaruppgift som beskriver målet utan att
avslöja knappen), innehållshierarkin, bildstrategin, typografin, navigationen, hur förtroende byggs, huvudreferensen med
kvaliteten som uppdraget prövar, vad den kräver och om kundens material bär det, antagandena, undersidan, materialbehovet,
skillnaden mot de andra, den visuella utgångspunkten och implementationsgrunden (mall, komponenter, tema eller egen, med
källan, det som återanvänds och insatsen när något återskapas ur bilder). Planen bär också branschgenomgången (hur de
starka sajterna hanterar tjänster, förtroende, priser, navigation och kontakt, och deras svagheter) och förebilderna
utanför branschen.

**Visar:** uppdragen är olika sätt att presentera verksamheten och skiljer sig i hur sidan organiserar kundens
information (innehållshierarki, bildstrategi, typografiskt system, navigation, hur förtroende byggs), inte bara i färg och
typsnitt; varje uppdrag besvarar uppgiften, beslutsinnehållet, antagandena och prövningen och har en hypotes ur
researchen och kundens material; inget uppdrag är avsiktligt svagt, och ett uppdrag som bara skiljer sig i färg avvisas
(`kandidater.planbrist`). Tio förslag är ägarens beslut (2026-10-09, `kunskap/designregler.md`); parallella prototyper
före låsning har stöd (Dow m.fl. 2010). Går tio verkligt olika inte att göra med underlaget redovisas bristen
(KANDIDATPLAN.json, `brist_mot_begart`), utan kosmetiska dubbletter.

**Tillämpning:** art direction och UX gör uppdragen till skilda lösningar på kundens uppgift; varje uppdrag säger vilken
kvalitet i huvudreferensen det prövar och om kundens material bär den, och väljer Mobbins skärm eller flöde efter
uppgiften (`mobbin_typ`: ett flöde när uppgiften är en resa i steg).

**Återgång:** planprövningen bedömer varje uppdrag den släpper; ett uppdrag utan en giltig bedömning går inte till
skaparen, och en invändning som gör uppdraget ohållbart ger ny hypotes, ny referens eller mer research.

```utdrag före
kunskap/designregler.md
kunskap/bild.md # Art direction
```

```utdrag uppslag
kunskap/referenser-professionella.md
better-variant/SKILL.md rad 13–37
frontend-design/SKILL.md rad 15–34, 47–53
impeccable/reference/new-work.md rad 65–67
impeccable/reference/mode-persuade.md rad 9
taste/SKILL.md rad 17–23, 38–39
```

## Skapa

**Fråga:** bär uppdragets idé med kundens riktiga material, på mobil och dator, och går besökarens viktigaste uppgift
att genomföra?

**Underlag:** UPPDRAG.md, kundens fakta och bilder, briefen, researchen och referensbilderna, domloggen.

**Till nästa steg:** en byggd startsida och undersida (kod/), skärmbilder i 390, 768, 1280 och 1440, axe, och RIKTNING.md med
huvudreferensen, hypotesen, referensens kvalitet, varven, "Visar" och materialet.

**Visar:** grundidén syns i den renderade sidan; kundens material bär kompositionen (eller kompositionen är anpassad
efter materialet och bristen beställd); den viktigaste besökaruppgiften går att genomföra från startsidan; mobilversionen
håller ihop; kvalitetskraven håller (bygget, konsolen, spill, axe). Huvudreferensens kvalitet syns i fyra relationer,
med referensbild och kandidatens bild bredvid varandra i RIKTNING.md: bildens beskärning mot rubriken, de typografiska
storlekarna och hierarkin, täta och luftiga sektioner och rytmen, navigation och interaktion mot innehållet. Skaparen
skriver under "Visar" vilken bild som visar var och en. Varven: observerad brist, ändring, efterkontroll; inget minsta antal.

**Tillämpning:** som i skissen nedan, för hela startsidan och undersidan.

**Återgång:** som i skissen nedan.

```utdrag före
kunskap/designregler.md
kunskap/bild.md
frontend-design/SKILL.md
taste/SKILL.md rad 15–31, 38–39, 166–167, 179, 183, 213–260, 298–331, 599–613
impeccable/reference/craft-floor.md rad 5–42
impeccable/reference/new-work.md rad 126–127, 130, 132–134, 140
impeccable/reference/animate.md rad 13–48, 71–77
```

```utdrag varv
emil-design-eng/SKILL.md rad 62–145, 197–266, 525–555
emil-animate/SKILL.md rad 37–76, 78–80, 82–169
better-layout/SKILL.md
better-typography/SKILL.md
better-accessibility/SKILL.md
better-ui/SKILL.md
emil-mobile-native/SKILL.md rad 57–144, 167–187
taste/SKILL.md rad 630–680, 682–683
@Text
```

## Skiss

**Fråga:** visar första vyn och den viktigaste innehållssektionen, med kundens riktiga material, en egen idé om hur
besökaren förstår verksamheten och löser sin viktigaste uppgift, i mobil och dator?

**Underlag:** UPPDRAG.md (designuppdraget, besökarens uppgift, referensbilderna och vad de ska lära), kundens fakta
(VERKSAMHET.json, textunderlaget, RESEARCH.md) och bilder (BILDER.md), och den här filen: kvalitetskraven, besluten med
räckvidd och avgörandena. Kompetenserna (avsnittet Kompetenserna) är obligatoriska: skaparen tillämpar rollerna med
passet skapa (art direction och typografi, layout och bild, innehåll, responsivitet och rörelse) med sina skills
fullständiga instruktioner i en sammanhängande skiss. Före beställarens val ändrar ingen annan session skissen;
specialistpassen interaktion och rörelse och tillgänglighet och visuell granskning görs bara när ett uppdrag begär dem.
Material från före den rena designstarten 2026-10-09 finns inte i den aktiva miljön och slås inte upp.

**Till nästa steg:** en byggd skiss (första vyn, den viktigaste sektionen, navigationen och de interaktioner som behövs
för att förstå förslaget), skärmbilder i 390, 768, 1280 och 1440, de snabba kontrollerna (bygget, konsolen, spill, axe,
siffror utan belägg, menyn i verkligt öppnat läge) och RIKTNING.md med huvudreferensen, idén, referenserna, det överförda
och avvikelserna, de kvarvarande svagheterna, varven, materialet och kompetensernas synliga bidrag. Hela startsidan,
undersidan och besökarens centrala flöde byggs först efter valet, och bara som uppdraget Bygg ut (Förfina).

**Visar:** grundidén syns i den renderade skissen och skiljer sig från de andra i hur kundens information presenteras och
uppgiften löses, inte bara i färg; kundens material bär kompositionen, eller ett tydligt märkt utkast eller en
platshållare står där material saknas; mobilen, mellanbredden och datorn är genomarbetade. Inget fast antal varv:
första varvet prövar grunden, och varje varv därefter åtgärdar det största visuella problemet skaparen sett i sina egna
bilder eller vid jämförelsen med referensen i samma bredd. Inom skissförsöket bedömer den kritiska granskaren skissen
med rollen kritik (avsnittet Kompetenserna, Avgörandena): blind för skaparens text, uppdrag, referenspaket och kod, med
egen förhandsvisning i 390, 768, 1280 och 1440, menyn öppen, tangentbordet och reflow; SKISSKRITIK.json belägger
versionen, bilderna och kompetenskvittot.

**Tillämpning:** typografin avgör rollerna och hierarkin i den renderade sidan, art direction bildernas uppgift och
beskärning, UX uppgiftsflödet och återkopplingen, responsiviteten kompositionen från 390 till 1440; stilpaketet och
Mobbins underlag knyts i beslutsliggaren till formbesluten de används för.

**Återgång:** en svag helhet byter grundkomposition eller referens, med skälet, i stället för putsning; en stark
mellanversion får stå kvar.

```utdrag före
kunskap/designregler.md
kunskap/bild.md
```

## Granska

**Fråga:** vad uppfattar en besökare, går den viktigaste uppgiften att genomföra, vilka avvikelser är objektiva fel och
vilka är smak, och bär kundens material referensens kvalitet (de fyra relationerna, jämförda med förebilden)? Granskningen
ersätter inte ägarens visuella val eller ett prov med riktiga besökare; den är underlag till båda.

**Underlag:** första passet: skärmbilderna, tillgänglighetsträdet, axe och briefens uppgifter (inte uppdraget,
skaparens anteckningar, referenspaketet eller koden), med rollen kritik; andra passet: uppdraget, anteckningarna och
referensbilderna, med rollen motivering (avsnittet Kompetenserna).

**Till nästa steg:** KRITIK.json med första intrycket, uppgiften med belägg, avvikelserna med slag (krav eller smak),
allvar och om de är avsiktliga och välgrundade, nivån mot ribban och materialbehovet. Förbättringsrundan rättar bara
krav; ägaren ser granskningen efter sitt första beslut.

**Visar:** varje avvikelse har plats, bredd, vad, åtgärd, allvar och slag; en skills förbud bär aldrig ensamt ett fynd;
granskaren har läst de första vyerna (prövas i transkriptet; annars styr granskningen ingenting).

**Tillämpning:** kritiken bedömer bilderna först, som en besökare, och skaparens motivering sedan; tillgänglighets-
kompetensen används vid kontrollen (axe i tillstånd, tangentbordet, reflow) som i utformningen.

**Återgång:** ett fynd som kräver en ny riktning blir en rekommendation, och skaparen svarar i en egen session.

```utdrag
kunskap/designregler.md
kritik/GRANSKARE.md # Fem kriterier, betyg 1–10
frontend-design/SKILL.md rad 38–45
better-interface/SKILL.md # 6. Rank by user impact
impeccable/reference/critique.md rad 48, 122–126, 281–386, 390–610, 664–779
impeccable/reference/craft-floor.md rad 19–42
impeccable/reference/audit.md rad 9–62
ui-ux-pro-max/references/quick-reference.md rad 7–75, 93–112, 162–223
emil-break-ui/SKILL.md rad 91–125
emil-review-animations/SKILL.md rad 27–68
```

## Förfina

Den riktade förbättringen efter beställarens val, i tre uppdrag (ägarens uppdrag 2026-10-09, punkt 8; `skapande.UPPDRAGSTYPER`):
**Rätta** åtgärdar angivna brister inom befintlig omfattning, **Omarbeta designen** ändrar komposition, bildregi,
typografi, rytm och hierarki inom avtalat innehåll, och **Bygg ut** skapar överenskomna sektioner, undersidor och
funktioner. Ett val startar inget av dem.

**Fråga:** når det valda förslaget uppdragets önskade resultat inom uppdragets omfattning, med det som ska bevaras
kvar och DESIGN.md i takt med koden?

**Underlag:** uppdraget (typen, versionen det gäller, det önskade resultatet, omfattningen, det som ska bevaras och
avsändaren), beställarens ord och det beställaren gillade i andra förslag, RIKTNING.md och kundens fakta och material.

**Till nästa steg:** den nya versionen (den gamla bevarad och valbar), DESIGN.md som sidorna använder, RIKTNING.md med
uppdragets varv (brist, ändring, efterkontroll) och "Visar", de begärda specialistpassens poster (ändra eller bedöm, med
fynd i formen bild, version, element, tillstånd, avvikelse och kodkoppling) och den separata före/efter-bedömningen.

**Visar:** det önskade resultatet syns i bilderna; en rättelse och ett designomtag lägger inte till sidor
(`kandidater.omfattningsbrister`), en utbyggnad har varje angiven väg; DESIGN.md är giltig och koden använder dess
variabler (`kontroller/design.py --kandidat`). Före och efter styr fortsättningen (`kandidater.fore_efter_regel`): en
separat, blind granskare med rollen kritik ser de två versionernas bilder som X och Y utan skaparens förklaring, och en
bättre eller likvärdig version förs vidare, en sämre men tekniskt nödvändig kräver fortsatt lösning, en sämre utan
teknisk nödvändighet återställs (den sämre står bevarad och valbar), och ett oklart resultat står som oklart. Inget
minsta antal varv.

**Tillämpning:** uppdraget har rollerna i passet fordjupa (design och komposition, typografi, innehåll, responsivitet);
designomtaget har skissens kreativa frihet att lösa grundproblemet. Specialistpassen körs bara när uppdraget begär dem
(Rätta: inga; Omarbeta designen: granskningen bedömer utan att ändra; Bygg ut: båda ändrar det nya), med kärnan läst
före första ändringen.

**Återgång:** ett uppdrag som går utanför sin omfattning, inte gör något eget varv eller inte bygger återställs till
versionen det gällde; ett pass vars kärnkrav brister återställs och står som ej uppfyllt; ett nytt försök begärs
uttryckligen inom budgeten (`kontroller/kandidater.py <slug> --nytt-passforsok`).

```utdrag före
kunskap/designregler.md
kunskap/bygge-referens.md
```


## Text

**Fråga:** säger texten det verksamheten belagt, i deras röst, kort nog för kompositionen?

**Underlag:** BRIEF.md:s röstprov, omdömena ordagrant, textunderlaget.

**Till nästa steg:** rubriker och korta texter som bär i kompositionen, med sakuppgifterna oförändrade.

**Visar:** inga påhittade uppgifter, inga AI-mönster ur humanizer, svenska citattecken och tankstreck enligt
copy-kontroll.md.

**Tillämpning:** copy-kontrollen och humanizer avgör ordval, längd och ton i kompositionen.

**Återgång:** en uppgift utan belägg stryks eller beställs.

```utdrag
kunskap/copy-kontroll.md
kunskap/redaktionellt-pass.md
humanizer/SKILL.md
better-writing/SKILL.md
frontend-design/SKILL.md rad 61–71
impeccable/reference/clarify.md rad 5–92
taste/SKILL.md rad 321–331
better-typography/SKILL.md # Write copy naturally, style with CSS
brand/references/voice-framework.md
```

## Helbygge och prov

**Fråga:** genomför bygget den godkända prototypen på alla sidor, med fungerande tillgänglighet, prestanda, säkerhet och
sökbarhet? Helbyggets rollblock ovan prövas mot den egna sessionen i slutposten; prototypens aktivering ersätter det
inte. **Kompetens:** `.claude/skills/bygg-sajt/SKILL.md` steg 1–7, `kunskap/byggstandard.md`, `kunskap/seo.md`,
förfiningens DESIGN.md och provet (`kontroller/prova.py`: axe i tillstånd, Lighthouse-metoden, WebKit, resorna,
säkerhetshuvudena). **Tillämpning:** responsivitet, rörelse och tillgänglighet byggs in och kontrolleras med samma
kompetens. **Resultat och överlämning:** `kunder/<slug>/sajt/` med dist, provets rapporter och jämförelsen mot den
godkända prototypen, bunden till vinnarens version och byggets dist. **Bedömning:** provets grindar (tekniskt), två
oberoende granskare (designnivån), jämförelsen mot prototypen som ett eget besked (`visuell_jamforelse`) och ägarens
dom. **Återgång:** stoppvakten släpper inte bygget förrän granskningen godkänner eller taket nås; en försämring mot det
godkända är ett blockerande fynd.

## Leverans och uppföljning

**Fråga:** når sajten kunden i den granskade versionen, och fungerar den i drift och för besökarna? **Kompetens:**
`kunskap/lansering.md`, kundrepot och exporten (`kontroller/kundrepo.py`, `kontroller/exportera.py`) och besökarprovet
(`kunskap/besokarprov.md`). **Resultat och överlämning:** kundrepot med exakt den granskade dist och slutposten SLUT.json
med de fem tillstånden. **Bedömning:** lanseringens Definition of Done (byggstandarden 10.3) och, inför skarp lansering,
ett besökarprov. **Återgång:** en push som historikgranskningen stoppar görs inte; ett fynd i drift blir en backlogpost.

## Kundstart före skapandeflödet

Kundstart är en avgränsad server-API-koppling, inte en Claude Code-skaparsession. Modellen har inga fria verktyg eller
beställningsmandat. Hela `kunskap/kundintervju.md` läses av `kontroller/kundstart_modell.py` till den faktiska
systemprompten; den sammanlagda promptens hash sparas i varje anrops försökspost. Ingen separat skill-invokering
påstås. Filens A–J-täckning är internt beslutsstöd, inte ett obligatoriskt frågemanus. Aktuell kundkälla följer med
från ärendet. Modellen får föreslå, appen validerar och kunden kan rätta. Drift- och överlämningskontraktet står i
`kunskap/kundstart.md`. Detta steg ersätter inte research, referensval eller faktisk användarforskning.

## Kirurgens förbättringsväg

`kunskap/kirurg-forbattring.md` knyter befintlig spaning och Kundstarts överlämningsobservation till diagnos,
förhandsplanerat lokalt regressionsprov, separat granskning och ännu ej observerad eftereffekt. Det tillför ingen
obligatorisk metodlast till designskaparen. Befintligt `/kirurg`-intag och den processavgränsade provarbetaren har
olika åtkomst; ett läst dokument, lyckat anrop eller grönt facit är inte belägg för bättre design.
