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
Detaljerna, och var felet går åt det säkra hållet, står i kundvaktens beskrivning. Mobbins `search_screens` kräver ett
uttryckligt `mode`, "standard" eller "deep"; deep ingår i kontots Pro-plan, är obegränsat under Mobbins beta och släpps
sedan ägarens beslut 2026-10-12. Sessionerna når Refero, Mobbin, 21st och Motion genom
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
  per riktning med de paket som höjer kvaliteten: egen CSS, CSS-variabler (Referos direkt), Tailwind, shadcn- och
  21st-komponenter, Astro- och React-komponenter, Motion, GSAP och WebGL (three, ogl); nya paket väljs fritt
  (`kunskap/beroenden.md`; ägarens besked 2026-10-12). Rörelsens teknik väljs per beteende ur designens och
  implementationens behov: CSS först när den räcker, Motion (`motion` i ett `<script>`, `motion/react` i en React-ö;
  det äldre namnet är Framer Motion) för fjädrar, avbrytbara gester och layoutanimationer, GSAP för tidslinjer och
  scrollsekvenser; valet skrivs med skäl av rollen rorelse, och ingen rörelse läggs till för att fylla en kvot (ägarens
  uppdrag 2026-10-07, punkt 5C). Innehållet och navigationen fungerar utan JavaScript, rörelse respekterar
  `prefers-reduced-motion`, prestandabudgeten håller, inget hämtas från ett CDN, och det som rör sig mer än 5 s kan
  pausas eller stoppas (WCAG 2.2.2; K14–K21, K40). Mjuk scroll är ett designval med villkoren i `kunskap/beroenden.md`.
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
  När en rörelse hackar, eller tekniken väljs av prestandaskäl, är `emil-animation-performance` diagnosen: orsaken
  namnges (egenskapen, huvudtråden, omritning per bildruta, ärvda variabler, blur), och mätningen på en riktig enhet
  redovisas som oprövad när den inte gjorts (intagen 2026-10-13).
- **Skills som väntar på ett svar:** en skill med Initial Response läses bara med Read; kunskapen används men
  väntesvaret körs inte. Emils skills är undantagna och aktiveras med Skill (`kompetens.SLAPPTA_VANTANDE`; fria tyglar,
  ägarens besked 2026-10-12): promptens villkor att ingen svarar och inga frågor ställs ersätter nekandet. `kompetens.skill_nekas` nekar både mappnamnet och metadatanamnet genom Skill i ateljéns
  argument och helbyggets inställningar. Övriga tillåtna skills kan fortfarande laddas med Skill (K46/P5).
- **Användaranropade skills:** en skill vars SKILL.md har `disable-model-invocation: true` (källan har gjort den
  användaranropad, och Claude Code vägrar då Skill-verktyget) läses hel med Read när den tilldelas eller väljs; det ger
  sessionen samma text, och kvittot kräver läsningen i stället för aktiveringen (`kompetens.anvandaranropade`;
  kandidatprovet 2026-10-10: better-explain-interface vägrades två gånger och fällde researchen).

## Kompetenserna

Körbara hjälpmedel följer rollens uppgift. Komposition och designsystem har `skillskript` för brand-, token-,
Tailwind- och canvasfunktionerna; kontrakt, exempel och begränsningar finns i `kunskap/skillskript.md`.
Valda referenssidor profileras genom DevTools efter planprövningen, i varje kandidats kedja, enligt
`kunskap/referensprofil.md`. Skaparen får bara profiler som är bundna till uppdraget, den valda sidan, paketet och
metoden. Äldre lösa profiler injiceras inte. En ofullständig profil är underlag, inte en spärr: skaparen startar och
får veta vad som saknas.
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
Read gäller fortfarande dokument, de uttryckliga Initial Response-undantagen och de användaranropade skillsen
(disable-model-invocation), som då ska vara lästa hela. Saknade transkript är okänt och
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

**Granskningen efter renderingen** (ägarens besked 2026-10-12, guidens ordning; `BESLUT.md`). En roll i ett ändrande
pass kan också ha `efter:`, den andra halvan av kärnan: det som granskar den renderade sidan. Skissen gör den i ordningen
Impeccables critique (med Referos visuella kontroll mot referensbilderna), audit, layout, typeset och colorize med
better-typography och better-colors, Emils rörelsepass, webbläsarprovet och polish sist, och skriver varje steg i
RIKTNING.md under "Granskning". Taste är art director före koden: designspråket och rattarna variation, rörelse och
täthet står i RIKTNING.md under "Taste" innan något byggs. Granskningens filer läses hela och dess skills aktiveras i
någon av passets sessioner; saknas något fäller det arbetskravet som en oläst kärna (`kompetens.efterfiler`,
`kompetens.kravbrister`). Kvittot visar läsningen och aktiveringen, inte att granskningen gjordes efter renderingen
eller att den förbättrade sidan; det visar sidan. Skissens kärna före koden hålls under 160 000 tecken (fördjupningens
är större, med Taste); granskningen räknas inte i taket men läses i samma frist.

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
möjlig ändring. Slutgranskarens kompetens är det frysta kriteriepaketet (`metod_sha`), inte Skill-aktivering:
Skill-verktyget ingår inte i granskarens session. Läsningen av instruktionen och designreglerna observeras ur transkriptet, och en granskare som
bevisligen inte läste dem kan inte godkänna (`metodbrister`); ett saknat transkript står som inte observerat.

Rollerna arbetar där de gör nytta, en gång:

- **forska** (före planen): researchen formulerar antagandena om besökarna, frågorna och sajterna, och prövar
  territorierna med egna generiska sökningar innan frågorna skrivs; referenssteget hämtar sedan materialet med belägg.
- **planera** och **planprövning** (före skaparna): planeraren skriver tre uppdrag som skiljer sig i hur
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
når aldrig kundens uppgifter (kontroller/kundvakt.py). Varje block nedan: rollen, uppgiften, passen, kärnan, granskningen efter renderingen (`efter:`),
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
välj: ui-ux-pro-max/SKILL.md; impeccable/SKILL.md; better-accessibility/SKILL.md; better-typography/SKILL.md; better-colors/SKILL.md; better-layout/SKILL.md; better-ui/SKILL.md; better-interface/SKILL.md; humanizer/SKILL.md; impeccable/reference/optimize.md; impeccable/reference/harden.md; motion/best-practices/css-or-motion.md; motion/SKILL.md; gsap/SKILL.md; gsap/gsap-core/SKILL.md; gsap/gsap-scrolltrigger/SKILL.md; gsap/gsap-performance/SKILL.md; emil-animate/SKILL.md; emil-animation-performance/SKILL.md; emil-review-animations/SKILL.md
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
pass: skapa, fordjupa, ds_komponent
kärna: taste/SKILL.md; frontend-design/SKILL.md; impeccable/reference/craft-floor.md; kunskap/bild.md
efter: refero-design/SKILL.md; impeccable/SKILL.md; impeccable/reference/critique.md; impeccable/reference/polish.md
välj: hallmark/references/structure.md; hallmark/references/macrostructures.md; hallmark/references/component-cookbook.md; impeccable/SKILL.md; impeccable/reference/new-work.md; taste/SKILL.md; taste-soft/SKILL.md; taste-minimalist/SKILL.md; taste-brutalist/SKILL.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/delight.md; impeccable/reference/mode-persuade.md; brand/SKILL.md; banner-design/SKILL.md; better-variant/SKILL.md; ui-ux-pro-max/SKILL.md; refero-design/references/anti-ai-slop.md; refero-design/references/craft-details.md; canvas-design/SKILL.md; kunskap/skillskript.md; kunskap/materialtransport.md; kunskap/referensprofil.md
verktyg: uxsok, förhandsvisning, material, skillskript
mcp: refero, mobbin, 21st
visar: riktningen syns i den renderade sidan i mobil, mellanbredd och dator; referensens bärande kvaliteter är prövade eller ersatta med något lika genomarbetat; RIKTNING.md säger vilken synlig förbättring varje kompetens gav; skissen skiljer sig från de andra i komposition, berättelse och bildanvändning; ett koncept ur canvas-design står i BILDER.md med källa, version och Egen nej och är aldrig prototypen (metodkartan, Grafiska koncept ur canvas-design)
```

```kompetens typografi
namn: Typografi och färg
uppgift: Ge sidan typskalan, de typografiska kontrasterna, hierarkin, radlängden och färgernas roller, med stilpaketet och huvudreferensen som material, anpassade till kundens innehåll.
pass: skapa, fordjupa, ds_typografi
kärna: impeccable/reference/typeset.md
efter: better-typography/SKILL.md; impeccable/reference/colorize.md; better-colors/SKILL.md
välj: refero-design/references/typography.md; refero-design/references/color.md; taste-output/SKILL.md; better-ui/SKILL.md; kunskap/byggstandard.md
verktyg: förhandsvisning
mcp: refero
visar: typskalan, radlängden och färgrollerna i den renderade sidan, med stilpaketets värden eller ett skäl att avvika
```

```kompetens innehall
namn: Innehåll och UX
uppgift: Göra erbjudandet begripligt och besökarens viktigaste uppgift enkel, i verksamhetens egna ord och med verifierade fakta.
pass: skapa, fordjupa, ds_innehall
kärna: impeccable/reference/clarify.md; better-writing/SKILL.md; kunskap/copy-kontroll.md; kunskap/redaktionellt-pass.md
välj: humanizer/SKILL.md; impeccable/reference/distill.md; better-explain-interface/SKILL.md; refero-design/references/copywriting.md; hallmark/references/copy.md
verktyg: förhandsvisning
mcp: mobbin
visar: besökarens viktigaste uppgift går att lösa från första vyn; rubriker, knappar och etiketter säger vad som händer; texten låter som verksamheten
```

```kompetens responsiv
namn: Responsiv implementation
uppgift: Bygga komponenterna och layouten så att mobilens omställning är genomtänkt och 390, 768, 1280 och 1440 håller ihop, i en implementation som är enkel att underhålla.
pass: skapa, fordjupa, ds_responsiv
kärna: impeccable/reference/adapt.md; better-layout/SKILL.md
efter: impeccable/reference/audit.md; impeccable/reference/layout.md
välj: emil-mobile-native/SKILL.md; better-ui/SKILL.md; hallmark/references/responsive.md; hallmark/references/layout-and-space.md; kunskap/byggstandard.md
verktyg: förhandsvisning
mcp: mobbin
visar: mobilen och datorn, och mellanbredden där layouten byter form, i den renderade sidan; komponenterna och stilarna i egna filer där de återanvänds
```

```kompetens rorelseskiss
namn: Interaktion och rörelse i skissen
uppgift: Bygga de interaktioner som behövs för att förstå förslaget (menyn på mobilen, den primära handlingen, fokus och tangentbord), avgöra med impeccables animate före koden vilka beteenden som har ett syfte, och efter första renderingen göra Emils rörelsepass på det som byggts (emil-design-eng, emil-animate, emil-improve-animations och emil-review-animations), lästa hela; ett genomtänkt beslut kan vara att sidan är stilla. CSS först när den räcker, Motion eller GSAP med skäl (motion/best-practices/css-or-motion.md), alltid med reducerad rörelse. Passet rörelse efter fördjupningen är specialistens eget pass.
pass: skapa
kärna: impeccable/reference/animate.md
efter: emil-design-eng/SKILL.md; emil-animate/SKILL.md; emil-improve-animations/SKILL.md; emil-review-animations/SKILL.md
välj: motion/best-practices/css-or-motion.md; motion/SKILL.md; motion/best-practices/index.md; motion/best-practices/motion.md; motion/best-practices/react.md; gsap/SKILL.md; gsap/gsap-core/SKILL.md; gsap/gsap-timeline/SKILL.md; gsap/gsap-scrolltrigger/SKILL.md; gsap/gsap-performance/SKILL.md; emil-find-animation-opportunities/SKILL.md; emil-review-animations/SKILL.md; emil-improve-animations/SKILL.md; emil-animation-vocabulary/SKILL.md; emil-animation-performance/SKILL.md; emil-apple-design/SKILL.md; refero-design/references/motion.md; hallmark/references/microinteractions.md; hallmark/references/interaction-and-states.md
verktyg: förhandsvisning
mcp: refero, motion
visar: menyn och den primära handlingen prövade i förhandsvisningens tillstånd (meny, fokus, tangentbord, reducerad rörelse); varje rörligt beteende har ett syfte och ett teknikval med skäl i RIKTNING.md, eller står beslutet att sidan är stilla där, och Emils granskning står under Granskning
```

```kompetens rorelse
namn: Interaktion och rörelse
uppgift: Välja och genomföra de beteenden som passar sidan, var och en med ett syfte, och välja tekniken per beteende med skäl: CSS först när den räcker, Motion (motion i ett <script>, motion/react i en React-ö) för fjädrar, avbrytbara gester och layoutanimationer, GSAP för tidslinjer och scrollsekvenser; ett genomtänkt beslut kan vara att något ska vara stilla, och ingen rörelse läggs till för att fylla en kvot (ägarens uppdrag 2026-10-07, punkt 5C). Beslutstabellen motion/best-practices/css-or-motion.md läses hel före valet i passet rörelse (i skissen när rörelse väljs). Motions dokumentations-MCP har sin uppgift bara genom ett faktiskt anrop med kontrollerat resultat när ett beteende byggs med Motion.
pass: rorelse, ds_rorelse
kärna: impeccable/reference/animate.md; emil-design-eng/SKILL.md; emil-animate/SKILL.md; kunskap/byggstandard.md
efter: emil-improve-animations/SKILL.md; emil-review-animations/SKILL.md
välj: motion/best-practices/css-or-motion.md; motion/SKILL.md; motion/best-practices/index.md; motion/best-practices/motion.md; motion/best-practices/react.md; gsap/SKILL.md; gsap/gsap-core/SKILL.md; gsap/gsap-timeline/SKILL.md; gsap/gsap-scrolltrigger/SKILL.md; gsap/gsap-performance/SKILL.md; emil-find-animation-opportunities/SKILL.md; emil-review-animations/SKILL.md; emil-improve-animations/SKILL.md; emil-animation-vocabulary/SKILL.md; emil-animation-performance/SKILL.md; emil-apple-design/SKILL.md; refero-design/references/motion.md; hallmark/references/microinteractions.md; hallmark/references/interaction-and-states.md
verktyg: förhandsvisning
mcp: refero, motion
visar: varje beteende prövat med förhandsvisningens tillstånd (meny, hovring, fokus, tangentbord, reducerad rörelse) och redovisat för sig; valet CSS, Motion, GSAP eller stilla står per beteende med skäl i passets teknikval och i RIKTNING.md, och en Motion-sökning som gjordes står där med vad svaret gav; rörelse respekterar prefers-reduced-motion
```

```kompetens granskning
namn: Tillgänglighet och visuell granskning
uppgift: Inspektera den renderade sidan och interaktionsvägen, och rätta de konkreta bristerna i en avgränsad omgång utan att byta stil; bedöm återkoppling, fokus, avbrytbar rörelse, begriplighet, textstorlek och tillgänglighet i tillstånden mot principerna i kunskap/hig-principer.md, läst hel med Read (frågor att pröva, inget krav på Apples visuella stil); emil-apple-design läses hel med Read när den väljs, enligt K46:s undantag för väntande Initial Response-skills.
pass: granskning, ds_granskning
kärna: impeccable/SKILL.md; impeccable/reference/critique.md; impeccable/reference/polish.md; impeccable/reference/audit.md; impeccable/reference/craft-floor.md; better-accessibility/SKILL.md; refero-design/references/visual-workflow.md; kunskap/hig-principer.md; kunskap/byggstandard.md
välj: impeccable/reference/harden.md; impeccable/reference/optimize.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/degraded/finish-reviewer.md; better-interface/SKILL.md; emil-break-ui/SKILL.md; better-break/SKILL.md; taste-redesign/SKILL.md; hallmark/references/slop-test.md; hallmark/references/anti-patterns.md; emil-apple-design/SKILL.md
verktyg: förhandsvisning, detektor
mcp: refero
visar: bristerna i den renderade sidan och i tillstånden (tangentbord, fokus, reflow 320, reducerad rörelse, axe) är rättade eller motiverade, före och efter; detektorns fynd är rättade eller prövade mot ägarbesluten; återkopplingen, fokus, den avbrytbara rörelsen, begripligheten, textstorleken och tillgängligheten är bedömda mot hig-principer.md med plats och tillstånd, före och efter
```

```kompetens leverans
namn: Designsystem och överlämning
uppgift: Låta DESIGN.md och koden säga samma sak, med stilpaketets importerade värden och de valda tillstånden, så att leveransen utvecklar den godkända koden vidare.
pass: fordjupa
kärna: kunskap/bygge-referens.md; impeccable/reference/extract.md; design-system/SKILL.md
välj: impeccable/reference/document.md; kunskap/skillskript.md
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
uppgift: Formulera antagandena om besökarna som kan ändra designbesluten, hitta starka verkliga branschsajter genom webbsökning (svenska och internationella, byråers kundprojekt, jämförbara verksamheter) och professionell visuell inspiration genom gallerierna (Awwwards i varje ny designomgång, kompletterat med SiteInspire, Land-book, Godly, FWA, CSS Design Awards, Httpster eller One Page Love), och undersöka visuella förebilder, besökarflöden och återanvändbar kod innan riktningarna bestäms. Refero ger stil, skärmar och sajter; Mobbin ger sektioner och flöden; 21st ger komponenter och teman att pröva som implementationsgrund. Sök generiskt i alla vägar, sålla först och fördjupa sedan ett mindre urval, och skilj verklig branschsajt, visuell förebild, skärm eller flöde, återanvändbar komponent och tillgängligt tema eller mall. För vidare id, källa, upptäcktsväg, användningsplats och skäl för urval eller bortval; en vald komponent hämtas med kod, licens och beroenden, och en skärmbild kallas aldrig kodmall.
pass: forska, ds_research
kärna: kunskap/referensjakt.md; refero-design/SKILL.md; refero-design/references/mcp-tools.md
välj: kunskap/referenser-professionella.md; impeccable/reference/shape.md; better-explain-interface/SKILL.md; hallmark/references/macrostructures.md; ui-ux-pro-max/SKILL.md; refero-design/references/example-workflow.md
verktyg: uxsok, webbsok
mcp: refero, mobbin, 21st
mcp-krav: refero, mobbin, 21st
visar: frågorna och sajterna spänner över skilda grundidéer ur verksamhetens värld och är prövade mot vad tjänsterna har; varje antagande har underlag eller "ännu inte observerat", en prövning och en följd; ett tomt eller misslyckat prov står som det är och är inget material
```

```kompetens kritik
namn: Kritik av den renderade sidan, blind
uppgift: Bedöma den renderade sidan som en besökare ser den, mot ribban, besökarens uppgift och ägarens aktuella domar i uppdraget, blind för skaparens text, uppdrag, referenspaket och kod och för tidigare riktningar (domloggen och riktningshistoriken är stängda som filer, och äldre domar slås inte upp): i mobil, mellanbredd och dator var för sig, och med menyn öppen, tangentbordet och reflow, första vyns huvudkomposition, hierarkin, bildval, bildskala och beskärning, rytmen och de typografiska kontrasterna, och om sidan har kundens särprägel eller om samma form kunde användas av nästan vilket lokalt tjänsteföretag som helst i branschen (generisk), prövat mot en eller två professionella förebilder av samma slag; och det bilderna visar av återkoppling, fokus, begriplighet, textstorlek och tillgänglighet i tillstånden (menyn öppen, tangentbordet, hovring och fokus på begäran, reflow 320) mot principerna i kunskap/hig-principer.md (läst hel med Read), där det som ingen bild visar står som inte bedömt.
blind: i underlag/<slug> läser rollen bara briefen och kundens fakta och material (BRIEF.md, VERKSAMHET.json, RESEARCH.md, texten, BESTALLNING.md, bilder/), metoden och kandidatens egna bilder; kunder/<slug>, de andra kandidaterna, research på begäran (REFERENSUPPDRAG-*, TJANSTEUPPDRAG-*, också när de uppstår under sessionen), referensbeslutet, referenspaketet och de läsande skalkommandona nekas (kandidater.blind_nekas). Riktningshistoriken och domloggen nekas som filer (RIKTNINGSHISTORIK.json, DESIGNDOMAR.jsonl): ägarens beslut 2026-10-07 ("Ja, neka historiken"; GR-20261007-r103#K4). Ägarens aktuella domar står i uppdraget, och kritiken dömer mot dem och ribban, inte mot tidigare riktningar (ägaren 2026-10-06: "Mina tidigare underkännanden ska inte omvandlas till en allt smalare uppsättning tillåtna uttryck"). Ändras i kandidater.BLIND_HISTORIK, i uppgiften ovan och på den här raden.
pass: skisskritik, kritik_a, fore_efter, ds_kritik
kärna: kunskap/designregler.md; kunskap/referenser-professionella.md; impeccable/reference/critique.md; impeccable/reference/craft-floor.md; kunskap/hig-principer.md
välj: hallmark/references/slop-test.md; hallmark/references/anti-patterns.md; refero-design/references/anti-ai-slop.md; kritik/GRANSKARE.md; frontend-design/SKILL.md; better-accessibility/SKILL.md; emil-break-ui/SKILL.md; ui-ux-pro-max/references/quick-reference.md; impeccable/reference/audit.md; kunskap/byggstandard.md; kunskap/granskningsfragor.md
verktyg: förhandsvisning, detektor
mcp: refero, mobbin
visar: svaret belägger kandidatens version och bilderna som bedömdes; en bredd (390, 768, 1280, 1440) eller ett tillstånd (menyn öppen, tangentbordet, reflow 320) räknas som bedömt bara ur en bild som lästes och inte är tom, också när svaret nämner det; kvittot visar kärnan, de valda alternativen, verktygsanropen och tjänsternas anrop med utfall; varje synligt problem har plats, bredd och vad, det största först; förebilderna står med vad jämförelsen visade; skissens rekommendation är fortsätt, byt komposition eller förkasta riktningen, och första passet i läget full ger nivån mot ribban
```

```kompetens jamforelse
namn: Falsk variation
uppgift: Se alla kandidaters första vyer och hela sidor och peka ut de par som är samma struktur och berättelse med andra färger, typsnitt eller bilder, med makrostrukturen och den axel som skiljer dem (struktur, täthet, betoning, typografi, röst).
pass: jamforelse, ds_jamforelse
kärna: hallmark/references/macrostructures.md; better-variant/SKILL.md
välj: hallmark/references/structure.md; refero-design/references/anti-ai-slop.md; kunskap/referenser-professionella.md
verktyg:
mcp:
visar: varje utpekat par säger vad som är lika (makrostrukturen, berättelsen, det som möter besökaren först) och varför skillnaden bara är ytlig; par som skiljer sig i struktur pekas inte ut
```

```kompetens motivering
namn: Motiveringen och referensens kvalitet
uppgift: Pröva för varje avvikelse som granskningens första pass fann om den är avsiktlig och välgrundad (skäl i kundens behov, material eller huvudreferensen, och fungerar för besökaren), och om kundens material bär den kvalitet i referensen som uppdraget ville återskapa, i de fyra relationerna med kandidatens bild och referensbilden bredvid varandra.
pass: kritik_b, ds_bild
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
refero_get_style: uppgift — stilens belagda värden (typografi, färger, layout, rytm, komponenter) i researchen och huvudreferensens stilpaket (kontroller/stilpaket.py) I bandet (inventeringen 2026-10-12): stationen typografi jämför typskalan och färgrollerna med huvudreferensens stil.
refero_search_screens: uppgift — skärmar för första vyn, projekt- och tjänstesidor, förtroende och kontakt (typ skarm), i researchen och i skaparnas egna sökningar I bandet (inventeringen 2026-10-12): stationen kritik, där kritikern söker generiskt själv efter en eller två förebilder av samma slag och aldrig läser referenspaketet, och formulär (förfrågans skärmar).
refero_get_screen: uppgift — skärmens typsnitt, färger, sidtyper och element, och skärmens bild i full storlek
refero_get_similar_screens: uppgift — bredda från en stark träff till fler lösningar på samma uppgift I bandet (inventeringen 2026-10-12): stationen kritik, förebilder av samma slag som den bedömda versionen.
refero_get_screen_image: uppgift — skärmens bild när svaret saknar den I bandet (inventeringen 2026-10-12): stationen kritik, bilden i full storlek bredvid versionens bild.
refero_search_flows: uppgift — flöden för förfrågan och projektgenomgång (typ flode) I bandet (inventeringen 2026-10-12): stationen formulär ("quote request", "form error state", "confirmation").
refero_get_flow: uppgift — flödets steg i ordning, med bilderna I bandet (inventeringen 2026-10-12): stationen formulär, stegen och felbeskeden i ordning.
refero_search_sites: uppgift — hela sajter som förlagor till referenspaketet, sökta med sajtens namn eller domän (branschord ger fel träffar: "bakery" gav Walmart och Starbucks, prövat 2026-10-12); en branschfråga går till refero_search_styles
refero_search_apps: ingen uppgift — i webbflödet, eftersom verktyget bara söker iOS-appar: dess egen beskrivning säger "Search iOS apps in Refero" och hänvisar webbplatser till refero_search_sites, och provet med frågan "home builder construction" gav 10 av 100 träffar, alla iOS-appar som LEGO Builder, Asana och LinkedIn, ingen om byggande eller lokala tjänster; dess nytta är ett app-id för iOS-skärmar och iOS-flöden, och webbflödet söker skärmar, sajter och flöden med refero_search_screens, refero_search_sites och refero_search_flows; prövat 2026-10-07
```

```tjanstverktyg mobbin
search_screens: uppgift — skärmar och tillstånd för besökarens uppgift (med platform web ger den webbprodukters skärmar, inte kurerade webbplatser; för webbplatsens form: search_sections), i researchen och i uppdragens material (en sökfras per uppdrag) I bandet (inventeringen 2026-10-12): stationerna underlag och formulär. Mobbins svar kan bära `ai_usage_notice`: dess text förs ordagrant in i svaret eller versionens orsak; `mode` är "standard" eller "deep" (deep för nyanserade frågor; ägarens beslut 2026-10-12), och `output_destination` är `design_tool` hos utföraren och `code` i helbygget.
search_flows: uppgift — användarresor med stegen i ordning I bandet (inventeringen 2026-10-12): stationen formulär (förfrågan, felbesked, bekräftelse). Mobbins svar kan bära `ai_usage_notice`: dess text förs ordagrant in i svaret eller versionens orsak; verktyget har inget `mode` (bara search_screens har deep), och `output_destination` är `design_tool` hos utföraren och `code` i helbygget.
search_sections: uppgift — kurerade webbplatsers sektioner (Mobbins Sites; hero, showcase, how it works, social proof, pricing, FAQ, footer), Mobbins starkaste källa för en webbplats; ett sajtnamn i frågan ger den sajtens sektioner, och nästa sida hämtas när `has_next_page` och träffarna är starka I bandet (inventeringen 2026-10-12): stationerna innehåll och komposition: sektionsmönstret för den viktigaste sektionen och ordningen i FAQ, omdömen och kontakt. Mobbins svar kan bära `ai_usage_notice`: dess text förs ordagrant in i svaret eller versionens orsak; verktyget har inget `mode` (bara search_screens har deep), och `output_destination` är `design_tool` hos utföraren och `code` i helbygget.
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
generate-css-easing: ingen uppgift — verktyget är Motion+ (betalt; motion.dev/docs/ai-kit-generate-css, läst 2026-10-12) och ingår inte i den fria delen; samma CSS-fjädrar ger `spring(visualDuration, bounce)` ur det låsta `motion` vid bygget (`String(spring(0.3, 0.25))` = `550ms linear(…)`, prövat 2026-10-12 med motion 14.0.0), i Astro-frontmattern eller `<style define:vars>`, utan JavaScript i webbläsaren (`kunskap/beroenden.md`, Motion)
```

```tjanstverktyg 21st
search: uppgift — researchens och kompositionens sökning i 21st.dev (fritt): formbeskrivande frågor per sektion i marknadsföringsblocken (heroes, features, galleri och portfolio, testimonials, calls to action, pricing och meny, navbars, footers, bakgrunder och shaders, texteffekter), biblioteken med author (Aceternity UI, Magic UI, Kokonut UI, Ruixen UI med flera), mallar med type template och branschord som förlagor till hela sidor, och teman på temats namn (beskrivande temasökningar ger tom lista); aldrig kundens uppgifter; svaret är metadata med förhandsbild, video och id, som bedöms innan något hämtas (valideringen på sajten 2026-10-12)
get_component: uppgift — hämtning av ett valt blocks kod och demo med installationskommando (betald nivå utan daglig gräns, get_usage 2026-10-12); svaret saknar licens, som läses på komponentsidan (url), och en saknad licens i svaret är aldrig ett skäl att välja bort koden; beroendena härleds ur kodens importer, inte ur svarets lista (de skilde sig för hero-07, valideringen 2026-10-12); koden anpassas enligt porteringsreceptet i kunskap/beroenden.md, och källan, författaren, licensen och beroendena skrivs i RIKTNING.md under Referenser
get_inspiration: uppgift — en rangordnad metadatasökning efter komponenter, teman och mallar med säkerhet och motivering, utan betald kod (verktygets beskrivning läst 2026-10-12: inget inspirationsflöde); argumentet `context`, projektets design.json, skickas aldrig. I bandet: underlag och komposition, som generiska förebilder bedömda som referenser och aldrig kopierade rakt av
search_logo: ingen uppgift — gav tomt svar för varje fråga, också verktygets eget exempel "discord" (prövat 2026-10-12 i två sessioner); tredjepartsmärken tas ur respektive märkesägares mediekit tills verktyget svarar; prövat 2026-10-12
search_picker: ingen uppgift — ett interaktivt urvalsverktyg för en människa i Builder; sessionen söker med search och bedömer själv; prövat 2026-10-08
get_profile: ingen uppgift — profilen på 21st.dev är ägarens konto och ändras aldrig av flödets sessioner; prövat 2026-10-08
edit_profile: ingen uppgift — profilen på 21st.dev är ägarens konto och ändras aldrig av flödets sessioner; prövat 2026-10-08
upload_profile_media: ingen uppgift — profilen på 21st.dev är ägarens konto och ändras aldrig av flödets sessioner; prövat 2026-10-08
get_usage: ingen uppgift — kvoten och `aiGenerationEnabled` läses av ägaren; ingen kod läser dem i dag, och att startkvittot och underhållet gör det är lyft till ägaren tillsammans med 21st-genereringen; prövat 2026-10-12
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
get_theme: uppgift — ett tema ur 21st.dev (CSS-variabler i :root och .dark i shadcn-format, oklch-färger, ur förinställningar eller utdraget ur verkliga sajter) som implementationsgrund av slaget tema, när planen anger det. Temats id kommer ur search med type "theme" och en generisk fråga (teman saknar beskrivning, så en beskrivande fråga ger en tom lista; prövat 2026-10-09). Värdena mappas till projektets CSS-variabler med bevarade roller och märks `valt:` med källan i DESIGN.md, ett webbplatstemas varumärkesursprung skrivs i RIKTNING.md, och temat är aldrig ett paket. Mallar ger i search bara metadata, pris och adress (prövat 2026-10-09), har inget sessionsverktyg för koden och väljs bara av en människa I bandet (inventeringen 2026-10-12): stationerna art och typografi: temats rollstruktur (ljust och mörkt, primary, muted, accent, border, ring) är mallen som kundens palett mappas till, aldrig paletten själv.
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
emil-pick-ui-library (paketval görs utanför flödet, `kunskap/beroenden.md`), emil-prototype (i kandidatflödet är
kandidaterna varianterna; i designfasens band har den en station i rörelsen, designfas-kartan), taste-v1 (ersatt av taste),
taste-stitch (kräver Stitch och ett eget format; överlämningen följer kundens designsystem, K55), ui-styling (varken
Tailwind 3-konfigen eller shadcn används i mallen; licensfrågan är lyft till ägaren), better-interface-review (kräver en
git-diff; kritiken är blind för källan och dukens versioner ligger inte i git; inventeringen 2026-10-12), taste-gpt (fast AIDA-ordning mot K22; dess GSAP-recept används inte heller
sedan GSAP togs in 2026-10-07, eftersom rollen rorelse väljer CSS, Motion eller GSAP per beteende med skillen gsap och
`kunskap/beroenden.md`). Bildgenererande skills (design, taste-brandkit, taste-imagegen-frontend-web, taste-image-to-code) kräver
en bildgenerator som flödets sessioner inte har; illustrativt material som inte utger sig för att visa verksamheten
beställs som material (Avgörandena, Bilder). Ur taste-image-to-code används bara listan för bildanalys (rad 327–360),
som ett uppslag i Researchen. Flödets egna processkills styr arbetet: bygg-sajt ingår i helbyggets arbetskrav; kirurg, backlog och writing-for-agents
används i systemarbetet, inte som formgivningskompetens. writing-for-agents är för den som skriver om kartan, förorden
eller en skill. modern-web-guidance ingår i helbygget och som uppslag i bandets stationer; en plats i en kärna kräver fortfarande det
avgränsade försöket i intagskrav 4. Övriga
MCP-anslutningar (Gmail, Google Drive, GitHub, Resend, Jotform, Railway, Claude Docs med flera) rör kunddata, utskick
eller drift och har ingen uppgift i skapandet; sessionerna nekar dem (designfas-kartan har raderna för de anslutningar
som finns i miljön, med det som är lyft till ägaren). Trybloom används inte (ägarens ord 2026-10-05) och
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
(`kandidater.planbrist`: minst två av makrostruktur, bildstrategi, typografisk hierarki, innehållsordning och ton). Tre riktningar är ägarens beslut (2026-10-12,
`kunskap/designregler.md`); parallella prototyper före låsning har stöd (Dow m.fl. 2010). Går tre verkligt olika inte att
göra med underlaget redovisas bristen
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

## Designfasen i Claude Design

Ägarens uppdrag 2026-10-12 (ordagrant i `underlag/uppdrag/PROMPT-Nortropic-Claude-Design-konvertering-20261012.md`,
sammanfattat i `BESLUT.md`): formgivningen flyttar till Claude Design, och Nortropics metoder, skills och verktyg ska få
fungerande uppgifter där. Flödet, miljön, rollerna, beställningarna, versionerna, godkännandet och överlämningen står i
`kunskap/claude-design.md`; det här avsnittet är placeringskartan: varje betydande metod knuten till ett arbetsmoment, och
varje skill, tjänst, specialistpass och lokalt verktyg knutet till en plats och en station. Formgivningen går på ett band
(Bandet: stationerna, nedan): varje station har sin fråga och sina skills, och utföraren och specialistpassen (`ds_*`)
får stationens skills, inte rollernas hela kärna. Kompetensblocken ovan gäller för kandidatflödet och ger
specialistpassen deras verktyg och behörigheter.

**Platserna.** *Design*: utföraren, den enda som skriver dukens versioner: en interaktiv Claude Code-session i repots rot
(`./design.sh <slug>`, skillen `designfas`) med skillverktyget, repots skills och tjänsterna bakom kundvakten. Den
publicerar ritningarna på duken (Design-typen på claude.ai), där ägaren ser, jämför, kommenterar och väljer. *Code*:
specialistpassen (`designfas.py specialist`, `claude -p` i repot med rollens block och kvitto), flödets egna steg
(förberedelsen, researchen, helbygget) och de lokala verktygen; de lämnar underlag och förslag, aldrig en egen kunddesign.
*Båda*: samma kompetens används av utföraren och av ett specialistpass. *Ingen*: ingen uppgift i designfasen, med skälet.
Versionen står i varje skills `KALLA.md` (underhållet för fram commit dagligen; raden nedan säger källan, inte en commit
som skulle bli inaktuell).

**Stegen.** D1 kundunderlag och D2 kundförståelse (Code: `prototyp.py <slug> --forbered`) · D3 branschresearch i tre
perspektiv: branschen, visuell inspiration, implementationsgrund (Code: researchen, `NWP_KANDIDAT_STOPP_EFTER=forskning`
eller en aktiv designfas) · D4 referenser och inspiration till duken (Design: dukens sida Underlag) · D5 tre
kundanpassade riktningar, fler på ägarens begäran två åt gången (Design) · D6 granskning före valet (Code: kontrollerna och specialistpassen; Design: utförarens
granskning efter renderingen) · D7 ägarens val (duken) · D8 förfining med specialistbeställningar (Design och Code) · D9
ägarens designgodkännande (ägarens eget kommando) · D10 överlämningen och kundens designsystem (Design) · D11 helbygge,
verifiering och leverans (Code, ägarens byggstart och publicering som egna beslut).

### Bandet: stationerna

Ägarens uppdrag 2026-10-12 (ordagrant i `underlag/uppdrag/PROMPT-Nortropic-Designfasen-produktionsband-v2-20261012.md`,
som ersätter den första bandprompten samma dag): sidan skapas på ett band där varje skill gör en insats i sin station,
med resultatet synligt på sidan, och bandet följer hur litteraturen och professionell praxis tar fram en webbplats.
Läsning är ingen insats, och skills som säger emot varandra läses aldrig samtidigt som lika auktoriteter: varje station
får sin tur, sin fråga och sina skills, och bara dem; en konflikt avgörs av Avgörandena ovan och designreglerna. Utförarens
grund är kort: `kunskap/designregler.md`, kundens KUNDFORSTAELSE.md och den här tabellen. Inventeringen samma dag
(`underlag/uppdrag/PROMPT-Nortropic-Full-inventering-formagor-20261012.md`) placerade förmågorna på filnivå: en station
kan ha ett radutdrag ur en skill (`väg rad a–b`), och då läses bara utdraget.

**Ordningen.** Processmodellerna (`process`: ISO 9241-210, Double Diamond, Lean UX) bär ramen: förstå, specificera,
utforma, utvärdera och iterera. Specificeringen är briefen och KUNDFORSTAELSE.md (D2), som ligger före bandet och är dess
indata. Ordningen inne i utformningen är praxis (innehåll före form: Zeldman 2008; mobilen först som prioritering:
Wroblewski 2011) och i övrigt vår hypotes (avvikelserna nedan): underlag, innehåll och struktur, art direction,
komposition, visuell form (typografi och färg, responsiv prövning), interaktion (rörelse, formulär), utvärdering (kritik,
tillgänglighet), iteration. Innehållet och strukturen kommer före kompositionen (`innehall`): riktningens första version
är strukturen med det verkliga innehållet. Mobilen först betyder att besökarens toppuppgift och den primära handlingen
prioriteras på den minsta skärmen och att samma prioritering styr de större (`mobil`): stationerna ritar 390 först, och
kontrollen i innehåll och komposition är att toppuppgiften och den primära handlingen syns i första skärmen i 390.
Stationen responsiv prövar och förfinar omställningen, den inför inte mobilen.

**Tillgängligheten** är ett krav i varje station som formar sidan (`wai`), från innehållet: rubrikordning, länktexter och
textalternativ per bildplats bestäms i innehållsstationen (en medveten utvidgning av ägarens "från art direction och
framåt", efter granskningen mot WAI), och från art direction riktiga element, kontrast 4,5:1 för text och 3:1 för
kontroller och fokusindikatorer (1.4.11), färg aldrig som enda bärare (1.4.1), synlig fokus som inte döljs av fasta
sidhuvuden (2.4.11), träffytor minst 24 px för alla mål (2.5.8) och reflow i 320. Ägarens golv går längre: primära
kontroller minst 44 px och reducerad rörelse [beslut; motsvarar WCAG 2.5.5 och 2.3.3, nivå AAA]. Renderingen prövar vid
varje version det axe och mätningarna når (axe med `wcag22aa`, fokus, reflow, rörelse); 1.4.11 och 2.4.11 prövas av
stationen tillgänglighet och kritiken i bilderna, inte automatiskt.

**Tre riktningar, två följder** (ägarens beslut 2026-10-12, som ersätter omkring tio: "kvaliteten per riktning är
flaskhalsen, inte bredden"). Riktningarna är tre, tydligt olika och kundspecifika: de skiljer sig i minst två av
makrostruktur, bildstrategi, typografisk hierarki, innehållsordning och ton, aldrig bara i färg och typsnitt, och var och en visar i själva designen varför den passar
kunden. Före ägarens val går varje riktning underlag, innehåll och struktur, art direction och komposition. Kritiken
och jämförelsen körs när alla tre finns, samlat och sida vid sida (`parallell`; Dow m.fl. 2010 fann parallell
återkoppling bättre än seriell): inget omtag per riktning innan de andra finns, och pekar jämförelsen ut två som för
lika görs en av dem om innan ägaren ser dem. Efter valet går den valda riktningen typografi, responsiv, rörelse,
formulär, kritik, tillgänglighet och polish, och överlämningen efter ägarens godkännande. Ägaren kan begära fler
riktningar, två åt gången, när ingen av de tre träffar; de går samma följd och jämförs med de tidigare.

**Iterationen.** Varje version utvärderas i renderingen. Kritiken kan skicka tillbaka till en tidigare station (`varv`):
omtag av underlaget (ny research eller nya förebilder), innehåll och struktur, art direction eller komposition när
helheten är svag, och huvuddelen av varven läggs inte på detaljer medan bildregi, innehåll eller hierarki brister. Omtaget
har verktyg i kompositionen (`impeccable/reference/bolder.md` och `quieter.md`, utlösta av kritikens fynd: platt eller
överlastad). En station körs när sidan har det den gäller, och en överhoppad station har sitt skäl i versionens orsak;
rörelsestationen ger alltid ett beslut (rörelse med syfte eller stilla), och kritiken kan inte hoppas över.
Tillståndskontrollen (meny, fokus, 390/768/1440, reflow 320) görs av renderingen vid varje version.

**Insatsen räknas, inte läsningen.** En station är genomförd när dess utdata finns: en ny version av riktningens
ritning med bilder före och efter (`designfas.py version --station <id> --ritning <fil>`), eller ett svar med fynd och
belägg (`designfas.py bestall --station <id>` och `specialist`). Kvittot redovisar tillgång, aktivering, användning och
bedömd kvalitet var för sig och fäller ingen version för oläst material (ägarens beslut i samma uppdrag, punkt 6; det
ersätter för designfasen kravet att rollens kärna läses hel; kandidatflödets kvitton är oförändrade). Kontrollen av
insatsen är renderingen: pixeljämförelsen mot förra versionen av samma ritning i 390 och 1440, och stationens egen
mätning. `designfas.py station <slug> <id> --ritning <fil>` skriver stationens arbetsinstruktion ur raden nedan; en
station som ändrar ritningen görs helst av en underagent som bara har stationens skills, och utföraren granskar,
publicerar och sparar versionen.

Skills och tjänster: kärnan aktiveras med Skill (en användaranropad skill eller en med `## Initial Response` läses hel
med Read, utom Emils, som aktiveras med Skill) eller läses hel, och ett radutdrag läses bara i sina rader, allt bara i stationen; alternativen väljs efter
riktningen. `mcp:` är en tjänst bakom kundvakten (verktygen och deras uppgifter: tjänstblocken ovan) och `pass:`
specialistpasset som Code kan köra för stationen. Metod: raden i metodtabellen nedan, med källa, slag och princip.

| Station | Indata | Fråga eller uppgift | Skills och tjänster | Metod | Synlig utdata | Kontroll i renderingen | Körs |
|---|---|---|---|---|---|---|---|
| `underlag` Underlag och referenser | KUNDFORSTAELSE.md, FORSKNING.md, referenspaketet, tjänsternas svar | Vilka besökaruppgifter och vilka två till fyra förebilder i tre perspektiv (branschsajter för förståelse, inspirationssajter för gestaltningsmöjligheter, implementationsgrund) bär den här riktningen, vilka observerbara egenskaper ska prövas att föras över (uppmätta, härledda eller slutna), och har kunden en etablerad identitet som är låst? | kärna: `refero-design/SKILL.md`, `refero-design/references/mcp-tools.md`, `mcp:refero`, `mcp:mobbin`, `mcp:21st`; alternativ: `hallmark/references/study.md`, `better-explain-interface/SKILL.md`, `taste-image-to-code/SKILL.md rad 289–317, 327–360`, `taste-brandkit/SKILL.md rad 97–121`, `brand/references/visual-identity.md`, `mcp:chrome-devtools`, `pass:ds_research` | `process`, `diamant`, `hcd`, `referens`, `observation` | referenslåset i riktningens anteckning och på dukens sida Underlag med bild och ursprung, eller ett svar | förebilderna har bild och skäl på duken, och nästa version säger vad som förts över | varje ny riktning; som beställning när en version behöver bättre förebilder |
| `innehall` Innehåll och struktur | KUNDFORSTAELSE.md, TEXTUNDERLAG.md, referenslåset | Vilka frågor har besökaren, i vilken ordning, och vad svarar sidan med i verksamhetens egna ord och med belägg: makrostrukturen, sektionerna, rubrikerna, den primära handlingen, texterna, textalternativen per bildplats och, om sidan har ett formulär, vilka fält och varför? | kärna: `better-writing/SKILL.md`, `impeccable/reference/clarify.md`, `humanizer/SKILL.md`; alternativ: `kunskap/precision.md`, `hallmark/references/macrostructures.md rad 25–49`, `impeccable/reference/shape.md rad 16–33`, `brand/references/voice-framework.md`, `brand/references/messaging-framework.md rad 47–85`, `refero-design/references/copywriting.md`, `hallmark/references/copy.md`, `kunskap/copy-kontroll.md`, `mcp:mobbin`, `pass:ds_innehall` | `innehall`, `hcd`, `skiss`, `mobil`, `wai` | riktningens första version: strukturen med det verkliga innehållet, ritad i 390 först; senare en ny version av texten | rubrikordningen och sidans text i renderingen; toppuppgiften och den primära handlingen i första skärmen i 390; varje sakuppgift finns i underlaget | varje ny riktning, först; igen när texten ändras |
| `art` Art direction | strukturen, referenslåset, kundens bilder | Vilket namngivet designspråk, vilka rattar (variation, rörelse, täthet), vilket typsnitt och vilken palett ur kundens material, vilken förebild bevaras (ingen medelvärdesbildning), vad gör riktningen omisskännlig för just den här kunden, och hur visar designen själv varför den passar kunden (verksamheten, besökarna, positioneringen och materialet)? | kärna: `taste/SKILL.md # 0. BRIEF INFERENCE (Read the Room Before Anything Else)`, `taste/SKILL.md # 1. THE THREE DIALS (Core Configuration)`, `taste/SKILL.md # 2.B When the brief is an aesthetic, not a system`, `taste/SKILL.md # 7. DIAL DEFINITIONS (Technical Reference)`, `frontend-design/SKILL.md`; alternativ: `kunskap/precision.md`, `refero-design/SKILL.md rad 20–55`, `refero-design/references/anti-ai-slop.md rad 45–77, 101–144`, `impeccable/reference/new-work.md rad 45–47, 65–67`, `hallmark/references/custom-theme.md rad 83–139`, `taste-soft/SKILL.md`, `taste-minimalist/SKILL.md`, `taste-brutalist/SKILL.md`, `brand/SKILL.md`, `mcp:21st` | `art`, `referens`, `wai` | ny version med språket och anteckningen med rattarna och "bevarat / avvisat / ryggrad", och frontend-designs två pass före koden: planen (palett med 4–6 namngivna hex ur kundens material, typsnitten och deras roller, layoutkonceptet i en mening och en ASCII-skiss, principerna) och planen prövad mot briefen, med det som ändrades för att det var en standardlösning och varför | renderingen i 390 och 1440 visar språket i typsnitt, palett och bildregi; synlig ändring mot strukturen | en gång per riktning; igen vid omtag |
| `komposition` Komposition | versionen, bilderna, referenslåset | Bär makrostrukturen besökarens viktigaste uppgift? Är hierarkin, rastret, bildvalet och beskärningen genomarbetade, ligger handlingen i fungerande form i första vyn, och skiljer sig strukturen från de andra riktningarna? | kärna: `hallmark/references/macrostructures.md`, `impeccable/reference/layout.md`, `impeccable/reference/craft-floor.md`, `kunskap/bild.md`, `refero-design/SKILL.md # Quality Gate`, `refero-design/references/visual-workflow.md rad 81–105`; alternativ: `kunskap/precision.md`, `kunskap/hig-principer.md`, `hallmark/references/structure.md`, `hallmark/references/component-cookbook.md`, `hallmark/references/layout-and-space.md`, `impeccable/reference/mode-persuade.md`, `impeccable/reference/bolder.md`, `impeccable/reference/quieter.md`, `hallmark/references/verbs/redesign.md rad 232–269`, `hallmark/references/hero-enrichment.md`, `better-variant/SKILL.md`, `banner-design/SKILL.md`, `canvas-design/SKILL.md`, `mcp:21st`, `mcp:mobbin`, `pass:ds_komponent`, `pass:ds_bild` | `komposition`, `skiss`, `bild`, `mobil`, `parallell`, `wai` | ny version med före och efter | synlig ändring i 390 och 1440; den primära handlingen i första skärmen i 390; detektorns layoutfynd rättade eller motiverade | alltid; igen vid omtag efter kritiken |
| `typografi` Typografi och färg | versionen, bilderna, stilrapporten | Håller typskalan, radlängden, de typografiska kontrasterna, färgrollerna och kontrasten (text 4,5:1, kontroller och fokus 3:1, färg aldrig ensam)? | kärna: `impeccable/reference/typeset.md`, `impeccable/reference/colorize.md`, `better-typography/SKILL.md`, `better-colors/SKILL.md`; alternativ: `kunskap/precision.md`, `emil-apple-design/SKILL.md # 15. Typography — optical sizing, tracking, leading`, `kunskap/hig-principer.md`, `refero-design/references/typography.md`, `refero-design/references/color.md`, `modern-web-guidance/guides/css/fluid-scaling.md`, `better-variant/SKILL.md`, `mcp:refero`, `mcp:21st`, `pass:ds_typografi` | `typografi`, `wai` | ny version med före och efter | stilrapporten och axe-kontrasten före och efter; detektorns typfynd rättade eller motiverade; synlig ändring | efter valet |
| `responsiv` Responsiv prövning | versionen, bilderna i 390, 768 och 1440, reflow 320 | Håller omställningen mellan 390, 768 och 1440, och följer brytpunkterna innehållet? Stationen prövar och förfinar; mobilen ritades först. | kärna: `better-layout/SKILL.md`, `impeccable/reference/adapt.md`, `emil-mobile-native/SKILL.md`; alternativ: `hallmark/references/responsive.md`, `impeccable/reference/layout.md`, `modern-web-guidance/guides/css/size-aware-styling.md`, `modern-web-guidance/guides/css/responsive-design.md`, `modern-web-guidance/guides/ui-atoms/responsive-table.md`, `emil-break-ui/SKILL.md`, `pass:ds_responsiv` | `mobil`, `wai` | ny version med före och efter, eller ett svar utan fynd med belägg | bilderna i tre bredder, reflow 320 utan sidledsspill; detektorns layoutfynd rättade eller motiverade | efter valet |
| `rorelse` Interaktion och rörelse | versionen, rörelsemätningen, rattvärdet för rörelse ur art-anteckningen | Vilka beteenden har ett syfte (urvalet med frekvens, syfte, hastighet och funktion, och listan över avvisade), med vilken teknik (CSS, Motion, GSAP), och fungerar de med reducerad rörelse, och kan rörelse som pågår mer än 5 s pausas eller stoppas (WCAG 2.2.2)? Eller beslutet att sidan är stilla. | kärna: `emil-find-animation-opportunities/SKILL.md`, `impeccable/reference/animate.md`, `emil-animate/SKILL.md`, `emil-review-animations/SKILL.md`, `motion/best-practices/css-or-motion.md`; alternativ: `kunskap/precision.md`, `motion/best-practices/index.md`, `better-accessibility/motion-and-zoom.md`, `better-ui/icon-transitions.md`, `hallmark/references/motion.md`, `hallmark/references/microinteractions.md`, `refero-design/references/motion.md`, `modern-web-guidance/guides/ui-behaviors/animate-element-entry-exit.md`, `modern-web-guidance/guides/ui-behaviors/physics-based-easing.md`, `modern-web-guidance/guides/css/animate-to-intrinsic-sizes.md`, `emil-improve-animations/SKILL.md`, `emil-animation-vocabulary/SKILL.md`, `emil-animation-performance/SKILL.md`, `emil-apple-design/SKILL.md`, `emil-prototype/SKILL.md`, `motion/SKILL.md`, `gsap/SKILL.md`, `mcp:motion`, `mcp:21st`, `pass:ds_rorelse` | `rorelse`, `wai` | ny version, eller beslutet "stilla" med skäl i versionens orsak; de valda och de avvisade beteendena står i orsaken | rörelsen med och utan reducerad rörelse; rörelse som pågår mer än 5 s kan pausas eller stoppas | efter valet; stilla är ett beslut |
| `formular` Formulär och tillstånd | versionen med formuläret, fälten och skälen ur innehållsstationen, designsystemet "Nortropic komponentbeteenden" (Formular) | Har fälten synliga etiketter, felbesked vid fältet efter interaktion och en felsammanfattning, står det skrivna kvar, och säger bekräftelsen vad som händer? | kärna: `better-accessibility/forms.md`, `impeccable/reference/harden.md`, `kunskap/forfragan.md`; alternativ: `kunskap/precision.md`, `impeccable/reference/clarify.md # Errors and permissions`, `hallmark/references/copy.md`, `hallmark/references/interaction-and-states.md`, `impeccable/reference/delight.md rad 37–46`, `refero-design/references/craft-details.md rad 57–191`, `ui-ux-pro-max/references/quick-reference.md rad 162–194`, `modern-web-guidance/guides/forms/required-field-feedback.md`, `modern-web-guidance/guides/forms/validate-input-after-interaction.md`, `modern-web-guidance/guides/accessibility/accessible-error-announcement.md`, `mcp:mobbin`, `mcp:refero`, `mcp:21st`, `pass:ds_granskning` | `formular`, `wai` | ny version med felläget ritat som interaktiv ritning | axe med formuläret skickat tomt; feltillståndet i bilderna | när sidan har ett formulär |
| `kritik` Kritik av helheten | bilderna och briefen, aldrig källan eller utförarens text | Håller helheten mot kvalitetskraven och standarden, och mot ägarens skrivna kriterier i måttstocken (AI-bedömning, inte ägarens dom: precisionen på ägarens nivå, inte ägarens stil)? Visar designen själv varför riktningen passar kunden, och skiljer den sig tydligt från de andra? Användbarheten (heuristikerna, genomgången) och den visuella kritiken (granskningsfrågorna) var för sig; och ska bandet gå tillbaka (omtag av underlaget, innehåll och struktur, art direction eller komposition)? | kärna: `kunskap/precision.md`, `impeccable/reference/critique.md`, `kunskap/granskningsfragor.md`, `hallmark/SKILL.md # Disciplines that hold across every verb`, `hallmark/references/slop-test.md`, `pass:ds_kritik`; alternativ: `hallmark/references/anti-patterns.md`, `hallmark/references/verbs/audit.md rad 3–12`, `impeccable/reference/degraded/finish-reviewer.md`, `impeccable/reference/craft-floor.md rad 19–42`, `impeccable/reference/mode-persuade.md`, `refero-design/references/anti-ai-slop.md rad 258–274`, `frontend-design/SKILL.md rad 38–45`, `mcp:refero` | `heuristik`, `genomgang`, `blind`, `varv`, `parallell` | svar med fynd, belägg och återgång, märkt AI-bedömning | varje fynd anger bild och bredd | före valet samlat när alla riktningar finns; efter valet på den valda; alltid före utförarens förklaring |
| `tillganglighet` Tillgänglighet och tillstånd | versionen, axe i tillstånden, fokusmätningen | Fungerar menyn, fokus (synlig och inte dold under fasta sidhuvuden), kontrasten för text och kontroller, färg som inte bär ensam, träffytorna, reflow och felbeskeden i tillstånden, på hela sidan? | kärna: `better-accessibility/SKILL.md`, `impeccable/reference/audit.md`; alternativ: `ui-ux-pro-max/references/quick-reference.md rad 7–53`, `refero-design/references/craft-details.md rad 7–53`, `hallmark/references/interaction-and-states.md`, `emil-break-ui/SKILL.md`, `better-break/SKILL.md`, `emil-apple-design/SKILL.md`, `kunskap/hig-principer.md`, `pass:ds_granskning` | `wai`, `genomgang` | ny version med rättelserna, eller ett svar med fynd | axe utan allvarliga fel i tillstånden, synlig fokus, menyn öppnar | alltid för den valda riktningen |
| `polish` Polish och detaljer | versionen, bilderna | Linjering, optiska justeringar, tryck, ikoner, skuggor, textputs och små tillstånd, när bildregi, innehåll och hierarki bär; fokus och träffytor före och efter. | kärna: `impeccable/reference/polish.md`, `impeccable/reference/craft-floor.md rad 5–17`, `emil-design-eng/SKILL.md`, `better-ui/SKILL.md`; alternativ: `kunskap/precision.md`, `kunskap/hig-principer.md`, `hallmark/references/microinteractions.md`, `impeccable/reference/delight.md`, `emil-animation-performance/SKILL.md`, `refero-design/references/icons.md`, `refero-design/references/typography.md rad 418–514` | `detalj`, `varv`, `wai` | ny version med före och efter | synlig ändring i 390 och 1440; fokus och träffytor oförändrade eller bättre | sist, när kritiken inte begär omtag |
| `jamforelse` Jämförelse av riktningarna | alla riktningars bilder | Vilka par är samma struktur och berättelse med andra färger, typsnitt eller bilder? Skiljer sig varje par i minst två av makrostruktur, bildstrategi, typografisk hierarki, innehållsordning och ton, och vilket par är för lika och ska göras om innan ägaren ser dem? | kärna: `hallmark/references/macrostructures.md`, `better-variant/SKILL.md rad 13–37`, `pass:ds_jamforelse`; alternativ: `hallmark/references/structure.md`, `hallmark/references/component-cookbook.md rad 91–148`, `impeccable/reference/live.md rad 137–173`, `impeccable/reference/mode-persuade.md`, `refero-design/references/anti-ai-slop.md` | `parallell` | svar med utpekade par och den riktning som görs om | – | när alla tre finns, före valet; igen när ägaren begärt fler |
| `overlamning` Överlämning och designsystem | den godkända versionen | Designvärdena (uppmätta ur den renderade versionen), komponenterna, de responsiva reglerna, tillstånden, fokus- och kontrastreglerna och rörelsen som kontrakt i överlämningen, och kundens designsystem. | kärna: `design-system/SKILL.md`, `impeccable/reference/extract.md`; alternativ: `impeccable/reference/degraded/documenter.md`, `hallmark/references/contract.md`, `hallmark/references/export-formats.md rad 14–43`, `hallmark/references/interaction-and-states.md`, `design-system/references/token-architecture.md`, `design-system/references/semantic-tokens.md`, `better-colors/token-naming.md`, `better-colors/palette-structure.md`, `better-typography/spacing-and-sizing.md`, `emil-animation-vocabulary/SKILL.md`, `emil-review-animations/STANDARDS.md`, `brand/SKILL.md`, `brand/references/logo-usage-rules.md`, `impeccable/reference/document.md` | `kontrakt`, `tema`, `wai` | överlämningspaketet och kundens designsystem | `designfas.py overlamna --prova` utan brister | efter ägarens godkännande |

**Avvikelser och hypoteser.** Där bandet går längre än eller skiljer sig från källorna är det vår hypotes, med skäl
(granskad mot primärkällorna av en oberoende granskare 2026-10-12, en AI-bedömning av text mot källor): (1) Art
direction som egen station står inte i processmodellerna, som inte delar upp utformningen. Bandet delar den visuella
formen i val (art, före kompositionen) och prövning (typografi, efter), och art direction kommer efter innehållets första
version, inte före ritningen; skälet är ägarens erfarenhet att förfining utan ett valt språk landar i en säker mittenform.
(2) En station i taget med bara stationens skills är inte litteraturens; skälet är ägarens bild av bandet och
iakttagelsen, ett enda fall, att motstridiga skills lästa samtidigt jämnade ut uttrycket (konditoriet). (3) Polish sist
följer professionell praxis (impeccable), inte en studie. (4) Bandet uppfyller inte principen att användarna medverkar
genom utformningen (ISO 9241-210) och prövar inte riktningarna med människor, som Double Diamond, Lean UX och GOV.UK gör.
Kritiken är en AI-bedömning, och ägarens val är ett estetiskt och affärsmässigt beslut; inget av dem är ett
användarbelägg. Besökarprovet (`kunskap/besokarprov.md`) är platsen för det, efter godkännandet och med ägarens mandat.
(5) Tre riktningar är ägarens produktval (2026-10-12, som ersätter omkring tio), inte ett tal ur studien om parallell
prototypning (Dow m.fl. 2010: noviser, webbannonser, en session; studiens parallella villkor gällde fler skisser än tre).
Att färre riktningar ger högre kvalitet per riktning är ägarens skäl och prövas först när ägaren sett en omgång. (6) Ordningen innehåll, art, komposition, typografi, responsiv, rörelse, formulär,
polish står inte i processmodellerna; innehåll före form och mobilen först är praxis, resten vår hypotes. (7) Detaljnivån
före valet, renderad kod med verkligt innehåll, är högre än skisslitteraturen förordar (Buxton: många billiga skisser
före förfining); skälet är att ägaren dömer helheten, och alternativet vore att sänka detaljnivån före valet.

### Metoderna i arbetet

Slaget står inom hakparentes (`kunskap/designregler.md`, Källornas slag): [standard], [forskning], [metod] professionell
metod eller erfarenhetsbaserat råd, [skill] en skills eller ett tredjepartsverktygs råd (aldrig ett krav av sig självt),
[beslut] Nortropics produkt- eller ägarbeslut, [kund] kundens fakta, [hypotes]. "Läst i andra hand" betyder att
källan inte är läst i original. Källorna styrker principen, inte vår AI-arkitektur: studien om parallell prototypning
säger inget om hur många AI-genererade riktningar som är rätt (antalet, tre, är ägarens produktval), och Buxtons
bokpresentation är inte boken. Bedömningen har tre slag som hålls isär: AI-bedömning (ds-passen), ägarens bedömning och
användarbelägg; användarbelägg saknas i designfasen (avvikelse 4).

| Metod och källa | Princip | Vår tillämpning | Steg | Kompetens och verktyg | Synligt resultat | Bedömning |
|---|---|---|---|---|---|---|
| `process` Processmodellen (ISO 9241-210:2019, läst i andra hand genom NHS England och NIST; Design Council, The Double Diamond; Gothelf & Seiden, Lean UX 2021, läst i andra hand; `kunskap/teoretisk-grund.md` A) [standard][metod] | förstå, specificera, utforma, utvärdera och iterera | ramen; specificeringen är briefen och KUNDFORSTAELSE.md före bandet; ordningen inne i utformningen [hypotes] (avvikelserna 1 och 6) | hela bandet | `designfas.py station`, bandets tabell | bandets läge per riktning i `designfas.py status` | AI: –; ägaren: bandets resultat; användare: saknas (avvikelse 4) |
| `diamant` Double Diamond (Design Council, The Double Diamond) [metod] | undersök problemet och lösningarna var för sig, divergera före konvergens, gå tillbaka när ny kunskap ändrar förutsättningarna | diamant ett: kunden, branschen och besökarna som antaganden ur kundens underlag (D1–D3); diamant två: riktningar, val och förfining (D5–D8); en dom eller ett fynd som visar att grunden inte bär öppnar underlaget eller riktningarna igen | D2–D8 | forbered, forska och ds_research, stationen underlag | KUNDFORSTAELSE.md och FORSKNING.md före duken; en återgång som ny beställning eller ny research med skäl | AI: återgången i kritikens svar; ägaren: valet [beslut]; användare: saknas |
| `hcd` Människocentrerad design (ISO 9241-210; Norman, The four fundamental principles of human-centered design, inte läst i original) [standard][metod] | utgå från människorna och det verkliga problemet; små, enkla ingrepp med iteration | besökarens toppuppgifter och primära handling ur briefen; varje riktning säger besökaruppgiften och den primära handlingen | D2, D3, D5 | forbered, forska; brief-mall, research-underlag | varje riktning säger besökaruppgiften och den primära handlingen | AI: ds_kritik; ägaren: valet; användare: besökarprov (`kunskap/besokarprov.md`) när ett skarpt uppdrag kräver det |
| `parallell` Parallell prototypning (Dow m.fl. 2010, Parallel Prototyping Leads to Better Design Results; noviser, webbannonser, en session) [forskning] | flera skilda idéer jämförs innan arbetet läggs på en; återkopplingen ges parallellt, inte seriellt | tre riktningar [beslut 2026-10-12, ersätter omkring tio] som skiljer sig i minst två av makrostruktur, bildstrategi, typografisk hierarki, innehållsordning och ton; fler på ägarens begäran, två åt gången, jämförda med de tidigare; kritiken och jämförelsen när alla finns, sida vid sida; falsk variation pekas ut (studiens mått på parvis likhet), och två för lika görs om innan ägaren ser dem | D5, D6 | stationerna underlag, innehall, art och komposition; ds_jamforelse, ds_kritik | ritningarna sida vid sida på dukens sida Riktningar i samma bredd; jämförelsens par i SVAR.md | AI: jämförelsen och kritiken; ägaren: väljer eller underkänner alla [beslut]; användare: saknas |
| `skiss` Prototyper (GOV.UK Service Manual, Making prototypes: "the prototype that best meets your needs at the time"; Buxton, Sketching User Experiences, bokpresentationen: många billiga skisser före förfining) [metod] | prototypen efter frågan som ska besvaras; prototypen är inte tjänsten | riktningarna visar första vyn, den viktigaste sektionen och navigationen i kundens innehåll; fördjupningen läggs på den valda (hela startsidan, tillstånden, interaktiva ritningar); detaljnivån före valet [hypotes] (avvikelse 7) | D5, D8 | stationerna innehall och komposition; emil-prototype och better-variant i förfiningen | riktning som skiss, vald riktning som interaktiv ritning (Play) | AI: –; ägaren: valet; det ritade prövas i bygget; överlämningen märker "Endast simulerat" |
| `heuristik` Heuristisk utvärdering (Nielsen, 10 Usability Heuristics; allvarsskalan ur Nielsen, Severity Ratings for Usability Problems; NN/g) [metod] | begriplighet, systemstatus, användarens kontroll, konsekvens, felhantering; flera granskare | den renderade versionen granskas mot heuristikerna med allvar 0–4, före utförarens förklaring; en granskare (modell), fast metoden förutsätter flera | D6, D8 | ds_granskning, ds_kritik (impeccable critique och audit, hig-principer) | fynd med plats, bredd och tillstånd i SVAR.md | AI: fynden, inget täckningslöfte; ägaren: –; användare: saknas |
| `genomgang` Kognitiv genomgång (Wharton m.fl. 1994, läst i andra hand) [metod] | fyra frågor per steg i besökarens uppgift | den primära handlingen gås igenom i 390 med menyn öppen och i 1440, också som tangentbordsanvändare | D6, D8 | ds_kritik, ds_granskning | stegen och svaren i SVAR.md | AI: genomgången; användare: saknas |
| `wai` Tillgänglighetsutvärdering (W3C WAI, Evaluating Web Accessibility och Designing for Web Accessibility; WCAG 2.2, nivå AA; WCAG-EM) [standard][metod]; 44 px och reducerad rörelse [beslut; WCAG 2.5.5 och 2.3.3, AAA] | tillgänglighet under utformningen; automatiska och manuella kontroller | rubrikordning, länktexter och textalternativ i innehållet; riktiga element, kontrast (1.4.3, 1.4.11), färg aldrig ensam (1.4.1), fokus som inte döljs (2.4.11), träffytor 24 px (2.5.8) i ritningarna; axe (`wcag22aa`) med menyn öppen och formulären skickade tomma mot varje renderad version; manuell kontroll med tangentbord och skärmläsare före lanseringen | D5–D11 | better-accessibility, granskning; `axe.mjs` genom `designfas.py rendera --kontroll` | `versioner/<v>/kontroll/axe/` per version; helbyggets prov | AI: axe ser en del, ds_granskning resten i bilderna; den manuella kontrollen återstår och redovisas; användare: saknas |
| `innehall` Innehåll före form (Zeldman 2008: "Content precedes design") [metod]; innehållsplanering och inventering (Halvorson 2008; Halvorson & Rach 2012, inte läst) [metod]; informationsarkitektur (Rosenfeld, Morville & Arango 2015, inte läst) [metod]; Sanning [standard: marknadsföringslagen; beslut] | innehållet kommer före formen; struktur ur besökarens frågor; inga påhittade uppgifter | ritningarna använder TEXTUNDERLAG.md, kundens fakta och bilder; saknat står som märkt platshållare; formulärets fält bestäms här | D5, D8 | stationen innehall, better-writing, copy-kontroll | texterna i ritningen med belägg | AI: ds_innehall; ägaren: texten; användare: saknas |
| `mobil` Mobilen först (Wroblewski 2011: "know what matters most") och responsiv design (Marcotte 2010: flytande raster, flexibla bilder och mediefrågor) [metod]; brytpunkter efter innehållet [hypotes] | prioritera det besökaren behöver mest på den minsta skärmen och låt samma prioritering styra de större | ritningarna ritas i 390 först; toppuppgiften och den primära handlingen i första skärmen i 390; ritningarna är sidor (expand fill) och renderas i 390, 768 och 1440 med menyn öppen | D5, D8, D11 | stationerna innehall, komposition och responsiv; `rendera.mjs` | bilder i tre bredder; sidledsspill fäller renderingen | AI: ds_responsiv; användare: saknas |
| `tema` Temabara designsystem (Brad Frost, The many faces of themeable design systems) [metod]; de fyra lagren [beslut] | en gemensam kärna med varumärkesteman och white-labeling (Frost); token i nivåer | fyra lager [beslut]: arbetsmetod och kvalitetskrav (kunskap/), komponentbeteenden (designsystemet "Nortropic komponentbeteenden"), kundens identitet (kundens designsystem), sidans komposition (duken) | D4, D10 | design-system, brand | designsystemens README, tokens och förhandsvisningar | AI: –; ägaren: designsystemet |
| `bild` Bildregi och äkthet (`kunskap/bild.md`) [beslut]; textalternativ (WCAG 1.1.1) [standard] | bildens uppgift, beskärning, verksamhetens egna bilder | kundens bilder laddas upp som tillgångar med ursprung; ds_bild prövar urval och beskärning mot referensens kvalitet | D5, D8 | motivering-rollen (bild.md, refero visual-workflow) | TILLGANGAR.json med källa; bildvalet i ritningen | AI: ds_bild; ägaren: bildvalet |
| `referens` Referensens kvalitet mot kundens material [beslut 2026-10-03, 2026-10-06] | en namngiven referens får bära layout, palett och typografi; kundens material avgör | varje riktning anger förebild och de observerbara egenskaper den prövar att föra över | D4, D5 | refero-design, ds_research | notering per riktning på duken | AI: ds_research; ägaren: valet |
| `observation` Observation, rekommendation och belagd effekt [beslut] | håll isär observerat, antaget och rekommenderat | FORSKNING.md och SVAR.md märker slaget; verifierat och antaget isär i KUNDFORSTAELSE.md; sökrankning, omdömen och utmärkelser är aldrig belägg för affärsmässig framgång | D3, D6 | forska, ds_research | – | – |
| `varv` En observerad brist per varv; omtag när helheten är svag [beslut 2026-10-09, H02; Anthropic, Harness design, inte läst i denna granskning] | varje ändring åtgärdar något som syns och efterkontrolleras; kompositionen får göras om | en version per ändring med orsak och bilder före och efter; bildregi, innehåll och hierarki före marginaler; återgång till underlaget, innehållet, art eller komposition | D8 | utföraren; `designfas.py version` | VERSIONER.jsonl, bilderna per version | AI: ds_kritik (återgången); ägaren: versionerna |
| `blind` Granskning före skaparens förklaring [beslut 2026-10-09, punkt 10] | bilderna och besökarens uppgift först | ds_kritik får bilderna och briefen, aldrig källan eller utförarens anteckningar | D6, D8 | kritik-rollen | SVAR.md | – |
| `kontrakt` Designkontraktet (DESIGN.md) [beslut; Codex-granskningen 2026-10-04, glapp 1] | värden som maskinen läser, med förklaring | överlämningens DESIGN.md med värdena märkta uppmätt eller valt, komponenterna, de responsiva reglerna, tillstånden och rörelsen | D10 | leverans-rollen (design-system, impeccable extract) | `design/overlamning/<v>/DESIGN.md` | `designfas.py overlamna --prova` |
| `art` Art direction (Anthropic frontend-design: ett sammanhängande, avsiktligt uttryck; Taste-skillens rattar) [skill]; avvägt mot igenkänning (Tuch m.fl. 2012, prototypikalitet, läst i andra hand) [forskning]; språket före kompositionen [hypotes] | ett namngivet språk; särprägeln i verksamhetens material, typografi och bild, strukturen igenkännbar för sin bransch | stationen art ger språket, rattarna, typsnittet och paletten ur kundens material efter innehållets första version och före kompositionen (avvikelse 1) | D5 | taste, frontend-design | riktningens version med språket och anteckningen | AI: ds_kritik (frågorna 1–3 i `kunskap/granskningsfragor.md`); ägaren: valet |
| `komposition` Hierarki och raster (Müller-Brockmann 1981; Lupton 2010; Gestaltlagarna, Wertheimer 1923; alla lästa i andra hand, `kunskap/teoretisk-grund.md` C) [metod]; makrostrukturer och kompositionsgolv (hallmark, impeccable) [skill] | visuell hierarki genom skala, kontrast, närhet och ett bärande raster | stationen komposition prövar makrostrukturen, hierarkin, rastret och bildens plats mot besökarens uppgift | D5, D8 | hallmark macrostructures, impeccable layout och craft-floor, bild.md | versionen före och efter | AI: ds_kritik; ägaren: valet |
| `typografi` Typografisk hierarki och läsbarhet (WCAG 2.2: 1.4.3 kontrast, 1.4.11 kontrast för annat än text, 1.4.12 texten tål användarens avstånd) [standard]; radlängd omkring 45–75 tecken och radhöjd (Bringhurst, The Elements of Typographic Style; läst i andra hand) [metod] | hierarki genom skala, vikt och kontrast; läsbar radlängd och radhöjd; färgroller med kontrast | stationen typografi prövar typskalan, radlängden, kontrasterna och färgrollerna i renderingen | D8 | impeccable typeset och colorize, better-typography, better-colors | versionen före och efter; stilrapporten | AI: axe-kontrasten, ds_typografi |
| `rorelse` Rörelse med syfte (WCAG 2.2.2 och 2.3.1, nivå A) [standard]; reducerad rörelse (WCAG 2.3.3, AAA, tekniken C39) [beslut]; Emil Kowalski, Motions och GSAP:s dokumentation [skill] | varje rörelse har ett syfte och stillhet är ett giltigt val (Emil Kowalski); rörelse som pågår mer än 5 s kan pausas eller stoppas (WCAG 2.2.2) | stationen rörelse väljer ut beteendena med skäl och avvisar resten, och beslutar per beteende (CSS, Motion, GSAP eller stilla) | D8 | emil-find-animation-opportunities, impeccable animate, Emils skills, Motion, GSAP | versionen eller beslutet stilla | AI: rörelsemätningen med och utan reducerad rörelse, ds_rorelse |
| `formular` Formulär (GOV.UK Design System: Question pages, Error summary, Error message; WCAG 2.2, 3.3.1–3.3.3 och 3.3.7) [metod][standard] | fråga bara det som behövs; synliga etiketter; felbesked vid fältet och en felsammanfattning; det skrivna står kvar | fälten och skälen i innehållsstationen; stationen formulär ritar tillstånden, felbeskeden och bekräftelsen efter komponentbeteendena | D8 | better-accessibility forms, impeccable harden, `kunskap/forfragan.md` | versionen med felläget ritat | AI: axe med formuläret skickat tomt |
| `detalj` Detaljarbete och hantverk (impeccable polish; Emil Kowalski) [skill]; den visuella designen är det som oftast nämns när människor bedömer trovärdighet (Fogg m.fl. 2003, läst i andra hand) [forskning] | linjering, optiska justeringar, tryck och tillstånd, efter helheten | stationen polish sist, när bildregi, innehåll och hierarki bär | D8 | impeccable polish och craft-floor, emil-design-eng, better-ui | versionen före och efter | AI: ds_kritik (fråga 4) |

### Placeringen

En rad per skill, tjänst, specialistpass och lokalt verktyg: namn | källa | plats | stationer (eller skäl) och uppgift
(indata → resultat; vägen till designen; beroenden) | status. `designfas.py karta --prova` fäller en skill eller tjänst
utan rad, en skill utan station och utan skrivet skäl, en rad vars stationer inte stämmer med bandets tabell och ett
specialistpass som saknas; statusen skiljer tillgång, aktivering, användning med resultat, belagd tillämpning och bedömd
kvalitet, och okänt står som okänt.

```designfas-karta
skill:designfas | Nortropic | Design | skäl: bandets egen instruktion till utföraren; den kör stationerna | ny 2026-10-12; aktivering i en ägarstartad utförarsession oprövad
skill:taste | Leonxlnx/taste-skill | båda | stationer: art; flöden: band, specialistpass; D5 art direction, avgränsad till §0, §1, §2.B och §7 (rad 13–81, 106–121, 552–571): språket och rattarna variation, rörelse och täthet → riktningens designspråk och anteckningen med rattarna; ds_komponent läser den | aktiverbar i repots sessioner (prövat i -p 2026-10-07); i designfasen oprövad
skill:taste-soft | Leonxlnx/taste-skill | Design | stationer: art; flöden: band, specialistpass; D5 alternativ i plan och komposition: en mjuk stilvariant för en riktning som behöver den → val med skäl i riktningens notering | alternativ; oprövad i designfasen
skill:taste-minimalist | Leonxlnx/taste-skill | Design | stationer: art; flöden: band, specialistpass; D5 alternativ i plan och komposition: minimalistisk stilvariant → val med skäl | alternativ; oprövad i designfasen
skill:taste-brutalist | Leonxlnx/taste-skill | Design | stationer: art; flöden: band, specialistpass; D5 alternativ i plan och komposition: brutalistisk stilvariant → val med skäl | alternativ; oprövad i designfasen
skill:taste-output | Leonxlnx/taste-skill | ingen | skäl: skillen handlar om att utdata inte ska trunkeras, inte om typografi (inventeringen 2026-10-12); flöden: specialistpass; om stationernas underagenter trunkerar ritningar är inte prövat | ingen uppgift, omprövad 2026-10-12
skill:taste-redesign | Leonxlnx/taste-skill | Code | flöden: specialistpass, leverans; skäl: omformgivning av en befintlig sajt; bandets omtag har bolder och quieter i kompositionen; rad 8–14 och 171–178 passar fliken Ändringar när ändringsagenten kan läsa en skill (dess sandlåda läser kopierade regler); ds_granskning alternativ | ingen station; ds_granskning alternativ; Ändringar oprövat
skill:taste-stitch | Leonxlnx/taste-skill | ingen | skäl: kräver Stitch och ett eget format; överlämningen följer kundens designsystem i Design System-typen (K55) | ingen uppgift, omprövad 2026-10-12
skill:taste-v1 | Leonxlnx/taste-skill | ingen | skäl: ersatt av taste (samma källa, äldre version) | ingen uppgift, prövat mot målflödet 2026-10-12
skill:taste-gpt | Leonxlnx/taste-skill | ingen | skäl: fast AIDA-ordning (K22) och eget GSAP-recept; sektionsordningen motiveras ur besökarens frågor och rörelsen väljs i stationen rorelse | ingen uppgift, prövat mot målflödet 2026-10-12
skill:taste-brandkit | Leonxlnx/taste-skill | Design | stationer: underlag; flöden: band; rad 97–121 för en kund med etablerad identitet: identitetsläget (ny, befintlig eller förnyelse) och vad som är låst; resten kräver en bildgenerator och väntar på ägarens mandat | radutdrag; oprövat
skill:taste-imagegen-frontend-web | Leonxlnx/taste-skill | ingen | skäl: bildgenererad sajtskiss; duken ritar riktningarna i kod; bildgenererad sajtskiss; duken ritar riktningarna i kod och generering kräver bildgenerator och mandat | ingen uppgift: blockerad av saknad bildgenerator
skill:taste-imagegen-frontend-mobile | Leonxlnx/taste-skill | ingen | skäl: bildgenererade appskärmar; flödet gör webbplatser; bildgenererade appskärmar; flödet gör webbplatser | ingen uppgift
skill:taste-image-to-code | Leonxlnx/taste-skill | Code | stationer: underlag; flöden: band; D3, D8 uppslag i ds_research och ds_bild: listan för bildanalys av en referensbild → observationer om komposition och bildregi i SVAR.md | uppslag; omprövad 2026-10-12 (förr bara researchens uppslag)
skill:frontend-design | anthropics/skills | båda | stationer: art, kritik; flöden: band, specialistpass, helbygge; D5 kärna i art direction (ett sammanhängande, avsiktligt uttryck); kritiken rad 38–45 (de generiska dragen som frågor); D11 kärna i helbygget → riktningens uttryck och bygget | aktiverbar; i designfasen oprövad
skill:impeccable | pbakaus/impeccable | båda | stationer: innehall, art, komposition, typografi, responsiv, rorelse, formular, kritik, tillganglighet, polish, jamforelse, overlamning; flöden: research, band, specialistpass, overlamning, helbygge; D5–D8 utförarens granskning efter renderingen (critique, audit, layout, typeset, colorize, polish); ds_granskning, ds_kritik, ds_typografi, ds_responsiv, ds_innehall, ds_rorelse läser sina referensfiler → fynd och rättelser | aktiverbar; specialistpassen prövas i fiktiva fallet
skill:hallmark | nutlope/hallmark | båda | stationer: underlag, innehall, art, komposition, responsiv, rorelse, formular, kritik, tillganglighet, polish, jamforelse, overlamning; flöden: research, band, specialistpass, overlamning; D5 plan-alternativ (21 makrostrukturer, komponentkokbok) för tre verkligt skilda riktningar; ds_jamforelse kärna; ds_kritik slop-test → riktningarnas struktur och jämförelsens par | referensfiler läses med Read; oprövad i designfasen
skill:refero-design | referodesign/refero_skill | båda | stationer: underlag, innehall, art, komposition, typografi, rorelse, formular, kritik, tillganglighet, polish, jamforelse; flöden: research, band, specialistpass; D3 ds_research kärna; D5 utförarens visuella kontroll mot referensbilderna; D8 granskningen efter renderingen → referenslåset och jämförelsen | aktiverbar
skill:ui-ux-pro-max | nextlevelbuilder/ui-ux-pro-max-skill | båda | stationer: formular, tillganglighet; flöden: research, band, specialistpass, helbygge; formulär och tillgänglighet som radutdrag ur quick-reference.md (§8 och §1–2, regel-id i versionens orsak); uxsok i researchen; D11 helbyggets alternativ; ger inga förebilder i underlaget (en lokal tjänstesajt gav 0 träffar), därför inte där | radutdrag i bandet oprövade; uxsok läsande
skill:ui-styling | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: varken Tailwind 3-konfigen eller shadcn används i mallen; licensfrågan (Apache-mall mot MIT i frontmattern, OFL saknas för två typsnitt) är lyft till ägaren | ingen uppgift, omprövad 2026-10-12
skill:brand | nextlevelbuilder/ui-ux-pro-max-skill | Design | stationer: underlag, innehall, art, overlamning; flöden: band, specialistpass, overlamning; D5 plan- och kompositionsalternativ; D10 kundens identitet i kundens designsystem → varumärkesregler | alternativ
skill:banner-design | nextlevelbuilder/ui-ux-pro-max-skill | Design | stationer: komposition; flöden: band, specialistpass; D5 kompositionsalternativ för en bildplats eller ett band → komposition i ritningen | alternativ
skill:design-system | nextlevelbuilder/ui-ux-pro-max-skill | Design | stationer: overlamning; flöden: band, overlamning; D10 leverans-kärna: designsystemet ur den godkända versionen → kundens designsystem (Design System-typen) och överlämningens värden | kärna i leveransrollen; oprövad i designfasen
skill:design | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: bildgenererande skill som kräver en bildgenerator varken duken eller sessionerna har; mappnamnet skuggar /design, så utföraren skapar duken med Artifact-verktyget | ingen uppgift; kollisionen prövad 2026-10-12
skill:slides | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: presentationer; ägaren väljer på duken. Kan få en station om riktningar ska visas för en kund (Slides-typen finns) | ingen uppgift, prövat mot målflödet 2026-10-12
skill:canvas-design | anthropics/skills | båda | stationer: komposition; flöden: band, specialistpass; D5, D8 koncept för en bildplats eller ett mönster (ritning eller PNG genom skillskript) → koncept i BILDER.md, aldrig verksamhetens bild | alternativ
skill:better-typography | jakubkrehel/skills | båda | stationer: typografi, overlamning; flöden: band, specialistpass, overlamning, helbygge; D8 granskning efter renderingen i typografi; ds_typografi → typskala, radlängd och hierarki | aktiverbar
skill:better-colors | jakubkrehel/skills | båda | stationer: typografi, overlamning; flöden: band, specialistpass, overlamning, helbygge; D8 granskning efter renderingen i färg; ds_typografi → färgroller och kontrast | aktiverbar
skill:better-accessibility | jakubkrehel/skills | båda | stationer: rorelse, formular, tillganglighet; flöden: band, specialistpass, helbygge; D8 tillgänglighet-kärna; forms.md som formulärets kärna och motion-and-zoom.md (WCAG 2.2.2) i rörelsen; ds_granskning kärna; D11 helbyggets alternativ → tillgänglighetsfynd | aktiverbar
skill:better-layout | jakubkrehel/skills | båda | stationer: responsiv; flöden: band, specialistpass, helbygge; D5, D8 responsiv kärna hos utföraren; ds_responsiv → brytpunkter och omställning | aktiverbar
skill:better-ui | jakubkrehel/skills | Design | stationer: rorelse, polish; flöden: band, specialistpass, helbygge; D8 polish-kärna: tryck, ikoner, skuggor och ytor (en källa per värde); icon-transitions.md för menyikonen i rörelsen; D11 helbyggets alternativ | alternativ
skill:better-writing | jakubkrehel/skills | båda | stationer: innehall; flöden: research, band, specialistpass; D2 förberedelsens kärna; D5 innehall-kärna; ds_innehall → texten i verksamhetens ord | aktiverbar
skill:better-explain-interface | jakubkrehel/skills | Code | stationer: underlag; flöden: research, band, specialistpass; D3 underlaget: gör förebildernas observerbara egenskaper mätta, märkta uppmätta, härledda eller slutna (read-the-system.md tolkar extrahera.mjs, from-an-image.md tjänsternas skärmbilder, också i ds_bild); skriver ingen gränssnittstext | användaranropad: läses hel med Read
skill:better-interface | jakubkrehel/skills | Code | flöden: specialistpass, helbygge; skäl: laddar sex skills samtidigt, mot bandets en station i taget; tvärgenomgången i bygg-sajt steg 5 före granska.py; ds_granskning alternativ | alternativ i helbygget; oprövad
skill:better-interface-review | jakubkrehel/skills | Code | skäl: kräver en git-diff; kritiken är blind för källan och dukens versioner ligger inte i git; flöden: leverans, underhall; ändringsagenten kan granska sin egen diff före commit, inte inkopplat | ingen station; användaranropad: läses hel med Read; oprövad
skill:better-variant | jakubkrehel/skills | båda | stationer: komposition, typografi, jamforelse; flöden: band, specialistpass; D6 jämförelsen: axeltabellen och golvet (rad 13–37) som kärna, inte varianterna (skillen väljer ingen vinnare); D8 varianter av en del i komposition och typografi bakom väljaren (picker.md), bara på duken | användaranropad: läses hel med Read
skill:better-break | jakubkrehel/skills | Code | stationer: tillganglighet; flöden: band, specialistpass; D8 ds_granskning alternativ: brytprov → robusthetsfynd | användaranropad: läses hel med Read
skill:emil-design-eng | emilkowalski/skills | båda | stationer: polish; flöden: band, specialistpass; D8 polish-kärna: detaljerna i tryck, tillstånd och övergångar; ds_rorelse kärna | aktiverbar
skill:emil-animate | emilkowalski/skills | båda | stationer: rorelse; flöden: band, specialistpass, helbygge; D8 rörelse-kärna: beteenden och teknikval; RECIPES.md för mobilmenyn, dragspelet och trycket; D11 rörelsens bygge | aktiverbar
skill:emil-improve-animations | emilkowalski/skills | båda | stationer: rorelse; flöden: band, specialistpass; D8 granskning efter renderingen i rörelse; ds_rorelse → förbättrade förlopp | användaranropad: läses hel med Read
skill:emil-animation-performance | emilkowalski/skills | båda | stationer: rorelse, polish; flöden: band, specialistpass, helbygge; diagnosen när en rörelse tappar bildrutor eller tekniken väljs av prestandaskäl: egenskapen, huvudtråden, omritning per bildruta (Avgörandena, Rörelserådets räckvidd) | aktiverbar (Initial Response, släppt till Skill)
skill:emil-review-animations | emilkowalski/skills | båda | stationer: rorelse, overlamning; flöden: band, specialistpass, overlamning, helbygge; D8 rörelse-kärna: granskningen av förloppen; STANDARDS.md ger kurvor och längder som rörelsetokens i överlämningen; D11 grinden Block/Approve för byggets rörelsekod | användaranropad: läses hel med Read
skill:emil-find-animation-opportunities | emilkowalski/skills | båda | stationer: rorelse; flöden: band, specialistpass; D8 rörelsestationens första moment (kärna): urvalet med frekvens, syfte, hastighet och funktion och listan över avvisade → beslutet med belägg i versionens orsak | kärna; oprövad i designfasen
skill:emil-animation-vocabulary | emilkowalski/skills | båda | stationer: rorelse, overlamning; flöden: band, specialistpass, overlamning; D8 alternativ i rörelse → beskrivningen av förloppen i överlämningen | alternativ
skill:emil-apple-design | emilkowalski/skills | Code | stationer: typografi, rorelse, tillganglighet; flöden: band, specialistpass; D8 ds_granskning alternativ: fysisk, avbrytbar rörelse → fynd | aktiverbar (Initial Response, släppt till Skill)
skill:emil-break-ui | emilkowalski/skills | Code | stationer: responsiv, tillganglighet; flöden: band, specialistpass; D6, D8 ds_granskning och ds_kritik alternativ → brytfynd | alternativ
skill:emil-mobile-native | emilkowalski/skills | båda | stationer: responsiv; flöden: band, specialistpass; D8 responsiv-kärna hos utföraren; ds_responsiv → mobilens känsla (tryck, 100vh, zoom, fältens 16 px och inputmode) | kärna; oprövad i designfasen
skill:emil-prototype | emilkowalski/skills | Design | stationer: rorelse; flöden: band; D8 interaktiva ritningar i förfiningen: prototyp av ett beteende att pröva → is_interactive-ritning | omprövad 2026-10-12 (förr ingen uppgift: kandidaterna var varianterna); användaranropad: läses hel med Read
skill:emil-pick-ui-library | emilkowalski/skills | ingen | skäl: paketval; beroendena är låsta i mallen och teknikvalet är ägarens | ingen uppgift, prövat mot målflödet 2026-10-12
skill:emil-ask-sonner | emilkowalski/skills | ingen | skäl: en toast i en app; inget i en lokal tjänsteverksamhets sajt | ingen uppgift
skill:emil-animate-expo | emilkowalski/skills | ingen | skäl: React Native och Expo; flödet gör webbplatser | ingen uppgift
skill:emil-write-swift | emilkowalski/skills | ingen | skäl: Swift för iOS-appar; flödet gör webbplatser | ingen uppgift
skill:motion | motiondivision/ai-kit | båda | stationer: rorelse; flöden: band, specialistpass, helbygge; D8 rörelsen: css-or-motion.md som kärna (CSS först, Motion med skäl), index.md för varaktigheter och syfte; D11 helbyggets block → teknikval per beteende | alternativ; Motions dokumentations-MCP vid användning
skill:gsap | greensock/gsap-skills | båda | stationer: rorelse; flöden: band, specialistpass, helbygge; D8 tidslinjer och scrollsekvenser när ett beteende kräver det; D11 helbyggets block (gsap-core, gsap-scrolltrigger, gsap-performance; reducerad rörelse med gsap.matchMedia) → teknikval | alternativ
skill:modern-web-guidance | GoogleChrome/modern-web-guidance | båda | stationer: typografi, responsiv, rorelse, formular; flöden: band, helbygge; uppslag i stationerna (flytande typskala, brytpunkter efter innehållet, CSS-recept för rörelse, fel efter interaktion); D11 helbyggets kärna; ett alternativ eller uppslag ersätter inget moment och blir ingen standard, så intagskrav 4:s avgränsade försök gäller först en plats i kärnan (vår läsning, lyft till ägaren) | alternativ i stationerna, oprövat; aktiverbar i helbygget
skill:humanizer | NousResearch/hermes-agent (upphov blader/humanizer) | båda | stationer: innehall; flöden: research, band, specialistpass, helbygge; D5 innehall-kärna; ds_innehall; D11 bygg-sajt steg 4 → text utan AI-mönster | kärna i bandet; aktiverbar
skill:writing-for-agents | mattpocock/skills | Code | skäl: systemarbete för den som skriver om designfas-skillen, kartan eller CLAUDE.md | ingen designuppgift; används i systemarbetet
skill:bygg-sajt | Nortropic | Code | flöden: helbygge; skäl: helbygget efter ägarens godkännande och byggstart (bygg-sajt steg 5, En godkänd design ur Claude Design), efter bandet | övertagandet från Claude Design mekaniskt prövat (prov_designfas); verklig körning efter ägarens byggstart
skill:kirurg | Nortropic | Code | skäl: systemarbete som bedömer källor; ingen designuppgift | ingen designuppgift
skill:backlog | Nortropic | Code | skäl: systemarbete som genomför vilande poster; ingen designuppgift | ingen designuppgift
mcp:refero | Refero (api.refero.design, MCP) | båda | stationer: underlag, typografi, formular, kritik; D3 ds_research (stilar, skärmar, flöden, sajter); D5, D8 utförarens kompletterande sökningar → referenser med bild och id; generiska frågor genom kundvakten | ansluten i repots sessioner; användning i designfasen prövas i fiktiva fallet
mcp:mobbin | Mobbin (api.mobbin.com, MCP) | båda | stationer: underlag, innehall, komposition, formular; D3 ds_research (skärmar, flöden, sektioner); D8 t.ex. mobilmenyn → mönster med bild | ansluten; search_screens med mode standard eller deep (deep obegränsat under Mobbins beta)
mcp:21st | 21st.dev Builder (MCP) | båda | stationer: underlag, art, komposition, typografi, rorelse, formular; D3, D8 ds_research och ds_komponent (search, get_component, get_theme, get_inspiration) → komponent eller tema med kod, licens och beroenden som implementationsgrund | ansluten med nyckel; betald nivå utan daglig gräns (get_usage 2026-10-12)
mcp:motion | Motion (mcp.motion.dev, fri dokumentation) | båda | stationer: rorelse; D8 rörelseskiss och ds_rorelse när ett beteende byggs med Motion → dokumentationssvar | ansluten
mcp:chrome-devtools | Chrome DevTools MCP (kontroller/mcp/chrome-devtools.json) | Code | stationer: underlag; D3 profil av en vald referenssida (prestanda, regler för första vyn) genom devtools.py → DEVTOOLS.md i referenspaketet | i researchens kedja; aldrig i utförarens session
pass:ds_research | metodkartan, rollen forska | Code | stationer: underlag; D3, D8 beställningstypen referenser: förebilder för en uppgift i tre perspektiv (bransch, visuell inspiration, implementationsgrund) → SVAR.md med referenser och tjänsternas bilder | mekanik prövad; verklig körning i fiktiva fallet
pass:ds_komponent | metodkartan, rollen komposition | Code | stationer: komposition; D8 beställningstypen komponent: en komponent eller ett tema ur 21st → kod, licens och beroenden i SVAR.md | mekanik prövad
pass:ds_typografi | metodkartan, rollen typografi | Code | stationer: typografi; D8 beställningstypen typografi: typografisk analys av en version → fynd och värden | mekanik prövad
pass:ds_innehall | metodkartan, rollen innehall | Code | stationer: innehall; D8 beställningstypen innehall: texten och besökarens uppgift → fynd och textförslag med belägg | mekanik prövad
pass:ds_responsiv | metodkartan, rollen responsiv | Code | stationer: responsiv; D8 beställningstypen responsiv: omställningen mellan 390, 768 och 1440 → fynd | mekanik prövad
pass:ds_rorelse | metodkartan, rollen rorelse | Code | stationer: rorelse; D8 beställningstypen rorelse: ett rörelseförlopp eller en interaktion → beteenden och teknikval | mekanik prövad
pass:ds_granskning | metodkartan, rollen granskning | Code | stationer: formular, tillganglighet; D6, D8 beställningstypen granskning: tillgänglighet och visuell granskning i tillstånden, t.ex. ett formulär → fynd med allvar | mekanik prövad
pass:ds_kritik | metodkartan, rollen kritik | Code | stationer: kritik; D6, D8 beställningstypen kritik: versionen som en besökare ser den, utan källan och utförarens text → fynd och rekommendation | mekanik prövad; blindheten är promptens, inte en spärr
pass:ds_bild | metodkartan, rollen motivering | Code | stationer: komposition; D8 beställningstypen bild: bildurval, beskärning och bildernas uppgift → förslag ur kundens bilder | mekanik prövad
pass:ds_jamforelse | metodkartan, rollen jamforelse | Code | stationer: jamforelse; D6 beställningstypen jamforelse: falsk variation mellan riktningarna → utpekade par | mekanik prövad
verktyg:designfas.py | Nortropic | båda | alla steg: duken registreras, versioner ur dukens filer, beställningar och svar, godkännandet (bara ägaren), överlämningen, startkommandot | prövat i prov_designfas
verktyg:rendera.mjs | Nortropic, Design-typens körmiljö (privat kopia) | Code | D5–D11 varje version renderad lokalt i 390, 768 och 1440 med menyn öppen, axe och stilrapporten → bilder och kontroller som specialistpassen, ägaren och bygget jämför med | prövat med provduken 2026-10-12
verktyg:referens.py | Nortropic | Code | D3 fångsten av branschsajter och galleriförebilder → referenspaketet med SEKTIONER.md och EXTRAKT.md | i researchen
verktyg:referenstjanster.py | Nortropic | Code | D3 Refero och Mobbin med belägg (21st anropas av rollerna själva) → tjänsternas svar och bilder | i researchen; specialistsvarens bilder hämtas med dess bildvakt
verktyg:inspektera.mjs | Nortropic | Code | D3, D8 inspekterad DOM, tillstånd och spår hos en referens → underlag i referenspaketet | i researchen
verktyg:extrahera.mjs | Nortropic | Code | D3, D8 beräknade stilar och layoutmått hos en referens (uppmätt) → EXTRAKT.md | i researchen
verktyg:devtools.py | Nortropic | Code | D3 DevTools-profilen för en vald referenssida → DEVTOOLS.md | i researchens kedja
verktyg:stilpaket.py | Nortropic | Code | D3, D10 Referos stilpaket → värden som riktningen kan utgå från och som överlämningen märker | i researchen och bygget
verktyg:uxsok.py | Nortropic (ui-ux-pro-max) | båda | D5 utförarens sökning i UI UX Pro Max; ds_research → riktlinjer | läsande
verktyg:axe.mjs | Nortropic (axe-core) | Code | D5–D11 genom rendera --kontroll och helbyggets prov → tillgänglighetsfynd per version | prövat mot provduken
verktyg:stil.mjs | Nortropic | Code | D5–D11 genom rendera --kontroll → stilrapport (typsnitt, klickytor, modellernas standardval) | prövat mot provduken
verktyg:detektor.py | Nortropic (impeccable detect) | Code | D11 helbyggets och kandidatflödets byggda sidor; i designfasen kör renderingen motorn på varje version i 390 och 1440 (`designfas.py rendera --kontroll`, fynden med området typografi eller layout i `kontroll/detektor/`), och stationerna typografi, komposition, responsiv, kritik och polish får fynden i sin instruktion | i designfasen prövad med en attrapp av motorn (prov_designfas), oprövad på en kunds duk
verktyg:copy_kontroll.py | Nortropic | Code | D11 texten i bygget; ds_innehall kan använda rapporten | i bygget
verktyg:typsnitt.py | Nortropic | Code | D11 typsnitten i bygget ur Fontsource; duken laddar Google Fonts | i bygget
verktyg:material.py | Nortropic | Code | D8 material- och konceptbeställningar med kostnadsmandat → tillgångar med källa och rättigheter | kräver mandat och konto
verktyg:skillskript.py | Nortropic | Code | D5, D8 skillernas skript (brand, tokens, Tailwind, canvas) → filer att ladda upp på duken | i kandidatflödet; i designfasen oprövad
verktyg:jamfor.mjs | Nortropic | Code | D11 bygget mot förlagans bilder (designfas.jamfor_bygget, prova) → DESIGNJAMFORELSE.md | mekanik prövad
verktyg:lighthouse.mjs | Nortropic (Lighthouse) | Code | D11 helbyggets prov mot byggets lokala server (4.1, 4.7); mot en designfasversion ger den inget meningsfullt (ritningens laddning är inte sajtens) | i bygget
verktyg:ikoner.mjs | Nortropic | Code | D11 favicon och apple-touch-icon ur kundens logotyp eller bild (byggstandarden 2.3) | i bygget
verktyg:resor.mjs | Nortropic | Code | D11 besökarens viktigaste uppgifter som prov i den byggda sajten (RESOR.json); mot en interaktiv ritning oprövad | i bygget
verktyg:utan-js.mjs | Nortropic | Code | D11 innehållet och navigationen utan JavaScript i den byggda sajten; ritningarna kräver Designs körmiljö, så provet gäller bygget | i bygget
verktyg:prova.py | Nortropic | Code | D11 provet och jämförelsen mot förlagan | i bygget
verktyg:kompetens.py | Nortropic | Code | alla pass: kvittot ur transkriptet (aktivering, läsning, anrop) → SVAR.json och utförarens kvitto (designfas.py kvitto) | prövat
miljo:design-typen | Anthropic (Design-typen, artifact-type/SKILL.md och reference/) | Design | D5–D10 dukens format och hantverksregler (format.md, craft.md, view-state.md) → giltiga ritningar och dukens tillstånd | läses av utföraren; prövat med provduken 2026-10-12
miljo:design-system-typen | Anthropic (Design System-typen) | Design | D10 kundens designsystem och "Nortropic komponentbeteenden" → README, tokens, komponenter med förhandsvisning | se kunskap/claude-design.md, Designsystemet
fil:*/agents/* | skillsens upphov | ingen | skäl: agentkonfiguration för andra verktyg (openai.yaml och liknande), ingen förmåga i Claude Code | ingen uppgift, prövat mot målflödet 2026-10-12
fil:better-accessibility/* | jakubkrehel/skills | båda | flöden: band, specialistpass, helbygge; nås genom better-accessibility/SKILL.md: fokus och tangentbord, träffytor, skärmläsare och semantik när skillen aktiveras i tillgänglighet och helbygget; forms.md och motion-and-zoom.md har egna stationer | uppslag; oprövat i designfasen
fil:better-colors/* | jakubkrehel/skills | båda | flöden: band, specialistpass, helbygge; nås genom better-colors/SKILL.md i typografi: format, användning, kontrast och palettgenerering; token-naming.md och palette-structure.md har stationen overlamning | uppslag; oprövat i designfasen
fil:better-typography/* | jakubkrehel/skills | båda | flöden: band, specialistpass, helbygge; nås genom better-typography/SKILL.md i typografi: typsnittsval, radbrytning och skiljetecken, variabla typsnitt, tillgänglighet; spacing-and-sizing.md har stationen overlamning | uppslag; oprövat i designfasen
fil:better-ui/* | jakubkrehel/skills | båda | flöden: band, specialistpass, helbygge; nås genom better-ui/SKILL.md i polish och helbygget: ytor, ikoner, in- och utgångar; animations.md och enter-exit.md överlappar emil-animate, som avgör rörelsen (Avgörandena); icon-transitions.md har stationen rorelse | uppslag; oprövat i designfasen
fil:better-layout/* | jakubkrehel/skills | båda | flöden: band, specialistpass, helbygge; nås genom better-layout/SKILL.md i responsiv: gruppering och linjering, mellanrum och anpassning | uppslag; oprövat i designfasen
fil:better-explain-interface/* | jakubkrehel/skills | båda | flöden: band, research, specialistpass; nås genom better-explain-interface/SKILL.md i underlag: read-the-system.md tolkar extrahera.mjs, from-an-image.md läser tjänsternas skärmbilder (också i ds_bild), find-the-effect.md för en namngiven effekt hos en förebild | uppslag; oprövat
fil:better-interface/* | jakubkrehel/skills | Code | flöden: helbygge; review-format.md är formatet för tvärgenomgången i bygg-sajt steg 5 | uppslag; oprövat
fil:better-interface-review/* | jakubkrehel/skills | Code | skäl: skillens egna filer för en granskning av en git-diff (avgränsning och borttagna signaler); ingen station, se skillens rad | ingen station; oprövat
fil:better-break/* | jakubkrehel/skills | Code | flöden: band, specialistpass; scenarios.md: brytscenarierna för en enskild komponent i tillgänglighet | uppslag; hur brytprov körs mot en version på duken är oavgjort
fil:better-variant/* | jakubkrehel/skills | Design | flöden: band, specialistpass; picker.md: väljaren för varianter av en del i förfiningen (komposition och typografi), som bara finns på duken | uppslag; oprövat
fil:emil-animate/* | emilkowalski/skills | båda | flöden: band, specialistpass, helbygge; RECIPES.md: mobilmenyn, dragspelet och trycket i rörelsen och i bygget (förutsätter Base UI:s attribut; överföringen till mallen oprövad) | uppslag; oprövat
fil:emil-break-ui/* | emilkowalski/skills | Code | flöden: band, specialistpass; CATALOG.md: katalogen över brytfall i responsiv och tillgänglighet | uppslag; oprövat
fil:emil-prototype/* | emilkowalski/skills | Design | flöden: band; PICKER.md: väljaren för varianter av ett beteende i rörelsen; kundens text i stället för påhittade namn, väljaren bara på duken | uppslag; oprövat
fil:emil-improve-animations/* | emilkowalski/skills | ingen | skäl: AUDIT.md har samma värden som emil-review-animations/STANDARDS.md, som används; PLAN-TEMPLATE.md är en kandidat för formatet på helbyggets underagentuppdrag (oprövat) | ingen egen plats
fil:emil-animate-expo/* | emilkowalski/skills | ingen | skäl: React Native och Expo; Nortropic.app är Tauri med en webbvy | ingen uppgift
fil:emil-ask-sonner/* | emilkowalski/skills | ingen | skäl: Sonners API; Sonner finns inte i låset och formulärets bekräftelse är en tacksida | ingen uppgift
fil:gsap/gsap-* | greensock/gsap-skills | Code | flöden: helbygge; nås genom gsap/SKILL.md när ett beteende kräver dem: plugins och verktyg; gsap-react bara med en React-ö; gsap-frameworks (Vue, Svelte) används inte | uppslag; oprövat
fil:motion/codex/* | motiondivision/ai-kit | Code | flöden: helbygge; bruksanvisningen för Motions sökning (search-motion-docs) före en icke-trivial animation | uppslag; Motion-servern saknades i inventeringens session
fil:motion/performance-audit/* | motiondivision/ai-kit | Code | flöden: helbygge, granskning; MotionScore graderar rörelsens kostnad i renderingen | uppslag; oprövat
fil:motion/css-spring/* | motiondivision/ai-kit | ingen | skäl: beskriver verktyget generate-css-easing, som är Motion+ (betalt) och aldrig finns på den fria servern; samma fjädrar ger `spring()` ur motion vid bygget (`kunskap/beroenden.md`, Motion) | ingen uppgift: Motion+ (betalt)
fil:motion/transition-preview/* | motiondivision/ai-kit | ingen | skäl: förhandsvisning av en övergångs känsla i Motions verktyg; duken och rendera.mjs visar övergångarna | ingen uppgift
fil:motion/best-practices/* | motiondivision/ai-kit | båda | flöden: band, specialistpass, helbygge; css-or-motion.md, index.md och motion.md har stationen rorelse; base-ui.md och vue.md används inte (varken Base UI eller Vue i mallen) | delvis i stationen
fil:hallmark/references/components/* | nutlope/hallmark | Design | flöden: band, specialistpass; nås genom component-cookbook.md i komposition: arketypernas förlagor | uppslag; oprövat
fil:hallmark/references/macrostructures/* | nutlope/hallmark | båda | flöden: band, research, specialistpass; nås genom macrostructures.md (kärna i komposition och jämförelse): en fil per makrostruktur | uppslag; oprövat i designfasen
fil:hallmark/references/genres/* | nutlope/hallmark | ingen | skäl: hallmarks färdiga genrer; riktningens språk kommer ur kundens material och art-stationen | ingen uppgift
fil:hallmark/references/themes/* | nutlope/hallmark | ingen | skäl: hallmarks färdiga teman; themes/hum.md rad 251–275 om falsk variation är en kandidat för jämförelsen (oprövad) | ingen uppgift
fil:hallmark/references/*.md | nutlope/hallmark | båda | skäl: nås genom hallmark/SKILL.md:s routing; i bandet läses de namngivna filerna; assets, custom-craft, design-md, floating-nav (rendera.mjs scrollar inte fram lägena), preview-examples, color och typography har ingen egen station | uppslag genom skillen
fil:impeccable/reference/*.md | pbakaus/impeccable | båda | skäl: nås genom impeccable/SKILL.md:s routing; i bandet läses de namngivna filerna; init, onboard och doctor skriver projektfiler, generate och degraded/asset-producer genererar bilder (mandat saknas), overdrive bryter konventioner utan kundskäl, live-setup och region-map hör till live-läget, android, ios och *.native.md till appar, hooks.md rad 53–70 är triageregeln för detektorns fynd (oprövad) | uppslag genom skillen
fil:impeccable/reference/mode-read.md | pbakaus/impeccable | Code | flöden: helbygge; läsläget för textsidor i bygget | uppslag; oprövat
fil:impeccable/scripts/* | pbakaus/impeccable | Code | flöden: granskning; motorn bakom `scripts/impeccable detect`, som kontroller/detektor.py kör på kandidaterna; mot dukens rendering oprövad; live-browser*.js hör till live-läget; modern-screenshot.umd.js saknar licenshuvud | detektorn prövad på kandidater; licensen för modern-screenshot ej fastställd
fil:impeccable/NOTICE.md | pbakaus/impeccable | ingen | skäl: upphovsupplysning, följer med skillen | ingen uppgift
fil:modern-web-guidance/GUIDER.md | GoogleChrome/modern-web-guidance | Code | flöden: helbygge; förteckningen som SKILL.md slår upp guiderna i | i helbygget
fil:modern-web-guidance/guides/performance/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge, leverans; uppslag när Lighthouse (4.1) eller insikterna (4.7) fäller; optimize-image-priority ger LCP-bilden per bredd | uppslag; oprövat
fil:modern-web-guidance/guides/security/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge, systemarbete; uppslag för formulär, CSP och obetrodd text | uppslag; oprövat
fil:modern-web-guidance/guides/privacy/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge; fråga bara det som behövs, integritetstexten vid formulärets knapp | uppslag; oprövat
fil:modern-web-guidance/guides/js/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge; uppslag när bygget behöver JavaScript-API:er (Temporal för datum och öppettider) | uppslag; oprövat
fil:modern-web-guidance/guides/built-in-ai/* | GoogleChrome/modern-web-guidance | ingen | skäl: kundsajterna har ingen inbyggd AI; prompt-api.md är byte för byte samma fil som language-model.md | ingen uppgift
fil:modern-web-guidance/guides/webmcp/* | GoogleChrome/modern-web-guidance | ingen | skäl: kundsajterna exponerar inga verktyg för agenter | ingen uppgift
fil:modern-web-guidance/guides/wasm/* | GoogleChrome/modern-web-guidance | ingen | skäl: ingen WebAssembly i kundsajterna | ingen uppgift
fil:modern-web-guidance/guides/pwa/* | GoogleChrome/modern-web-guidance | ingen | skäl: kundsajterna är inga installerbara appar | ingen uppgift
fil:modern-web-guidance/guides/css/* | GoogleChrome/modern-web-guidance | båda | flöden: band, helbygge; uppslag genom GUIDER.md i bygget; de namngivna guiderna har stationer (typografi, responsiv, rorelse); stödraderna prövas mot MDN före användning | uppslag; oprövat
fil:modern-web-guidance/guides/visual-design/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge; uppslag genom GUIDER.md i bygget | uppslag; oprövat
fil:modern-web-guidance/guides/ui-behaviors/* | GoogleChrome/modern-web-guidance | båda | flöden: band, helbygge; uppslag genom GUIDER.md; de namngivna guiderna har stationen rorelse; scrollberoende beteenden syns inte i rendera.mjs bilder | uppslag; oprövat
fil:modern-web-guidance/guides/ui-atoms/* | GoogleChrome/modern-web-guidance | båda | flöden: band, helbygge; uppslag genom GUIDER.md; responsive-table.md har stationen responsiv | uppslag; oprövat
fil:modern-web-guidance/guides/ui-components/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge; uppslag genom GUIDER.md i bygget | uppslag; oprövat
fil:modern-web-guidance/guides/html/* | GoogleChrome/modern-web-guidance | Code | flöden: helbygge; uppslag genom GUIDER.md i bygget | uppslag; oprövat
fil:modern-web-guidance/guides/forms/* | GoogleChrome/modern-web-guidance | båda | flöden: band, helbygge; uppslag genom GUIDER.md; required-field-feedback och validate-input-after-interaction har stationen formular; mallens Forfragan använder redan :user-invalid | uppslag; oprövat
fil:modern-web-guidance/guides/accessibility/* | GoogleChrome/modern-web-guidance | båda | flöden: band, helbygge; uppslag genom GUIDER.md; accessible-error-announcement.md har stationen formular | uppslag; oprövat
fil:design-system/references/* | nextlevelbuilder/ui-ux-pro-max-skill | Design | flöden: band, overlamning; nås genom design-system/SKILL.md i överlämningen: komponentspecifikationer, token i tre nivåer, tillstånd och varianter; tailwind-integration.md när bygget skriver Tailwind @theme | uppslag; oprövat
fil:design-system/scripts/*token* | nextlevelbuilder/ui-ux-pro-max-skill | Code | flöden: overlamning; validering av tokens på den godkända versionen och utkast till kundens tokens genom skillskript (kräver en designfasrot, inte byggd) | oprövat i designfasen
fil:design-system/templates/* | nextlevelbuilder/ui-ux-pro-max-skill | Design | flöden: overlamning; startfilen för kundens tokens | uppslag; oprövat
fil:design-system/*slide* | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: presentationsdäck; att visa riktningarna som presentation är lyft till ägaren (Slides-typen på claude.ai i så fall) | ingen uppgift
fil:design-system/scripts/fetch-background.py | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: bakgrundsbilder till presentationsdäck | ingen uppgift
fil:design-system/scripts/tests/* | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: skillens egna prov | ingen uppgift
fil:brand/references/* | nextlevelbuilder/ui-ux-pro-max-skill | båda | flöden: band, overlamning, leverans; nås genom brand/SKILL.md: identiteten för en kund med etablerad identitet (visual-identity.md i underlag), logotypreglerna i överlämningen, consistency-checklist.md vid en ändring mot kundens designsystem (oprövat) | uppslag; oprövat
fil:brand/scripts/* | nextlevelbuilder/ui-ux-pro-max-skill | Code | flöden: overlamning; färgextraktion och utkast till kundens tokens genom skillskript; tests/ är skillens egna prov | oprövat i designfasen
fil:brand/templates/* | nextlevelbuilder/ui-ux-pro-max-skill | Design | flöden: overlamning; mallen för kundens riktlinjer (README i kundens designsystem) | uppslag; oprövat
fil:banner-design/references/* | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: format för banners och sociala bilder; lanseringens bilder är lyfta till ägaren som produktval | ingen uppgift
fil:ui-ux-pro-max/data/* | nextlevelbuilder/ui-ux-pro-max-skill | Code | flöden: research, band, specialistpass, helbygge; datan bakom uxsok (kontroller/uxsok): riktlinjer, typsnitt med licenser och stackarna; google-fonts.csv som faktakoll av en vald familj, aldrig som urvalslista | uxsok prövat läsande
fil:ui-ux-pro-max/scripts/* | nextlevelbuilder/ui-ux-pro-max-skill | Code | flöden: research, helbygge; sökmotorn bakom uxsok; tests/ är skillens egna prov; validate_data.py efter varje intagen commit (läsande) | uxsok prövat läsande
fil:ui-ux-pro-max/references/* | nextlevelbuilder/ui-ux-pro-max-skill | båda | flöden: band, helbygge; quick-reference.md har stationerna formular och tillganglighet; övrigt nås genom skillen | uppslag
fil:ui-styling/* | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: se skillens rad (varken Tailwind 3-konfigen eller shadcn i mallen; licensfrågan lyft) | ingen uppgift
fil:slides/* | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: pitch- och investerardäck; att visa riktningarna som presentation är lyft till ägaren | ingen uppgift
fil:design/* | nextlevelbuilder/ui-ux-pro-max-skill | ingen | skäl: logotyper, CIP och ikoner med bildgenerering (Gemini med flera nycklar); lyft till ägaren med kostnad | ingen uppgift: blockerad av mandat
fil:taste-stitch/* | Leonxlnx/taste-skill | ingen | skäl: Stitch-formatet (K55) | ingen uppgift
fil:writing-for-agents/* | Nortropic | Code | flöden: systemarbete; för sessioner som ändrar en skill, CLAUDE.md eller kunskap/ | systemarbete
mcp:figma | Figma (plugin, 42 verktyg i sessionen 2026-10-12) | ingen | skäl: ingen uppgift i flödet utan ägarens beslut; lyft med kostnad och nytta: generate_image och Weave förbrukar Figmas AI-krediter och skulle ge flödet en bildgenerator för illustrativt material (aldrig verksamhetens bilder), läsvägen (get_variable_defs, search_design_system, get_libraries, download_assets, get_screenshot) ger exakta tokens och SVG-logotyp ur en kunds egen Figmafil, och överlämningen till Figma (html_to_figma, use_figma) kräver ägarens konto | lyft till ägaren 2026-10-12
mcp:claude-in-chrome | Claude in Chrome (22 verktyg i sessionen 2026-10-12) | ingen | skäl: ingen uppgift utan ägarens beslut; lyft: efter varje version kunde utföraren se duken i ägarens Chrome (skärmbild, zoom, konsolen) med bara läsande åtgärder, vilket stänger luckan att Code inte ser Designs gränssnitt; kräver ägarens inloggade webbläsare och är oprövat under --strict-mcp-config | lyft till ägaren 2026-10-12
mcp:claude-docs | Claude Docs (8 verktyg i sessionen 2026-10-12) | ingen | skäl: rapporter och kundsammanfattningar som dokument på claude.ai rör kundens texter (samma beslut som dukarna); ingen kostnad nämns | lyft till ägaren 2026-10-12
mcp:cloudflare | Cloudflare (plugin, 4 verktyg) | ingen | skäl: driften går genom cf och wrangler; docs är läsande och kan bli ett uppslag i helbygget (Turnstile, Email Routing), execute ändrar kontots resurser | ingen designuppgift; docs-uppslaget lyft
mcp:railway | Railway (68 verktyg) | ingen | skäl: kundsajterna har ingen backend på Railway; kontot, planen och destruktiva verktyg (accept-deploy) kräver ägarens beslut | ingen uppgift
mcp:computer-use | computer-use (24 verktyg) | ingen | skäl: ägarens beviljande per session och program; nyttan är prov av Nortropic.app i systemarbetet, inte designflödet | ingen designuppgift
```
