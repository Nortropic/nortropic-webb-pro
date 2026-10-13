# Precision på ägarens nivå

Ägarens kvalitetsribba (2026-10-12, ordagrant i `underlag/niva/MATTSTOCK.md`): Apple och Nike är ledtrådar till
kvalitetsnivån, inte mallar. Kundens färger, typsnitt, komposition och personlighet låses aldrig. Den här filen gör
nivån mätbar och stilneutral. En riktning kan vara rå, varm, lekfull eller sträng och ändå svara ja på varje fråga.
Frågorna mäter precisionen, inte uttrycket. Ett motiv från Apple eller Nike är aldrig ensamt ett skäl att underkänna en
riktning.

**Källor.** Apples Human Interface Guidelines, lästa 2026-10-12: Typography (med Tracking values), Layout (uppdaterad
2026-09-09), Color, Branding (2026-09-09), Icons, Images, Motion, Materials, Buttons, Writing, Accessibility och Design
principles (återinförd 2026-06-08). Till det kommer WWDC26 *Principles of great design* och WWDC20 *The details of UI
typography*. Mätningarna av apple.com/se och nike.com/se gjordes 2026-10-12 i 390 och 1440 med Playwright i Chromium,
med och utan reducerad rörelse (scratchpadens `validering/sajter/`). **T** betyder att talet är vår tolkning och inte
källans. **Pt** jämförs med CSS-px: i Safari på iPhone med `width=device-width` är 1 CSS-px = 1 pt. Måtten är
plattformsnormer och inga krav på webben.

## Det som ger precisionen (uppmätt)

- **Typskalan:**
  - Ett litet, fast register: 5–13 unika grader per sida.
  - Varje steg är ett fast par av storlek, radhöjd i hela pixlar och spärrning, och samma steg används överallt.
  - Disciplinen är det som räknas, inte antalet steg.
- **Radhöjd och spärrning efter grad:**
  - Radhöjdskvoten sjunker med graden: omkring 1,45–1,5 för löptext, 1,2 för mellanrubriker och 1,0–1,1 för display.
  - Spärrningen sätts per typsnitt och grad. Apple går från +0,012 em vid 19 px till −0,015 em vid 80–96 px, och Nike
    spärrar inte alls.
  - En och samma `letter-spacing` på alla grader är ett fynd. Ett typsnitt med opsz-axel sätts med
    `font-optical-sizing: auto`.
- **Skalningen mellan bredderna:**
  - Displaygraden skalar ungefär 2× mellan 390 och 1440, och brödtexten ändras högst omkring 20 %.
  - Ingen av sajterna använder `clamp()`: storlekarna byts stegvis vid brytpunkter.
- **Radlängden:**
  - Löptext i 390 har 30–45 tecken.
  - Varje texttyp har en egen maxbredd. Långa ingresser är en medveten regel, inte ett misstag.
- **Svensk brytning:**
  - Texten är redigerad för hand: 35–82 mjuka bindestreck och 32–714 fasta mellanslag per sida, till exempel i "2 995 kr".
  - Rubrikbrytningarna håller i varje bredd.
- **Marginaler och luft:**
  - En sidmarginal per bredd, 24 px i 390, och samma mått återkommer som inset och glapp.
  - Avståndsvärdena kommer antingen från ett litet set, där de tio vanligaste täcker minst 90 %, eller från en skriven regel.
- **Bilderna:**
  - Varje bild är beskuren för sin bredd och sin roll; Nike levererar 100 % i visat förhållande.
  - Hörnradien följer en regel.
  - Första vyns bild har en naturlig bredd på minst 2 × visad bredd i 390 (T).
- **Första vyn:**
  - Den har en rubrik, högst två handlingar och ett motiv.
  - Rubriken är omkring 3× brödtexten i 1440 och 2× i 390. Talet är T och prövas mot kundens uppgift, inte som ett mål.
- **Rörelsen:**
  - Ett litet register: 3–5 varaktigheter på högst omkring 0,4 s för gränssnittet och 1–2 kurvor.
  - Reducerad rörelse stoppar skrolleffekter och automatisk video.
  - Varje rörlig yta har en synlig paus med beskrivande namn.
- **Ribban brister också.** Nikes vita text var oläslig över videons första bildruta, och videon spelade vidare med
  reducerad rörelse. Text över bild eller video ska därför vara läsbar i varje bildruta.

## Detaljnivån: det som lyfter en sida från basic till premium

Ägarens dom 2026-10-13, ordagrant i `underlag/niva/MATTSTOCK.md`: "det är ju detaljer, detaljer, detaljer som lyfter den
från basic till premium känslan". Precision utan detaljer ger en ordnad men basic sida. Premiumkänslan kommer av att
varje kontaktyta är genomarbetad, och därför får ägaren se riktningarna med sina detaljer redan före valet (stationen
`detaljer`, ägarens beslut samma dag). Rörelsen tjänar upplevelsen och riktningens känsla; den läggs aldrig till för att
fylla en kvot (ägarens uppdrag 2026-10-07, punkt 5C), och den uteblir aldrig av försiktighet. Detaljerna är:

- **Tillstånd och övergångar på allt interaktivt.**
  - Hovring, tryck, fokus, öppna och stäng, formulärets svar och laddning har var sitt läge.
  - Övergången hör till riktningens rörelseregister: korta varaktigheter och en eller två kurvor, med fjädrar ur
    `spring()` där det passar.
  - Ett element som ändrar läge utan övergång syns som basic.
- **En koreograferad första vy.**
  - Riktningens signatur visas när sidan öppnas: rubriken, bilden och handlingen i en genomtänkt ordning, eller ett
    motiv som rör sig med syfte.
  - Med reducerad rörelse står första vyn färdig direkt.
- **Bilder som lever där det bär**, till exempel en avtäckning, en mjuk skala vid hovring, en lätt parallax eller ett byte
  mellan beskärningar. Bilden är alltid verksamhetens egen eller märkt illustrativ.
- **Sektionerna utgår från 21st-block** där ett passande block finns, till exempel hero, tjänster, pris, omdömen, frågor
  eller kontakt. Blocket porteras enligt `kunskap/beroenden.md` och formges om till riktningens språk. Id och licens
  står i RIKTNING.md, liksom de block som prövades och valdes bort.
- **Mikrotypografi:** hängande skiljetecken, optisk linjering, tabellsiffror i priser och tider, fasta mellanslag, och
  rubriker som bryts där meningen bryts.
- **Djup och material med en regel:** ytor, skuggor, linjer och radier som följer samma logik genom hela sidan.

Apple och Nike är ribban för detaljtätheten, inte för stilen (MATTSTOCK.md). Stilrapporten räknar de interaktiva
elementen med en övergång (`precision.overgangar` i STIL.json). Resten bedöms i bilderna och genom att använda sidan.

## Frågorna per station

**art**
- A1. Vilken känsla ska riktningen ge besökaren, i ett eller två ord? Var i designen förstärks den: typsnittet,
  bilden, rörelsen eller tonen? (Design principles, Delight; ägarens "visa i designen varför den passar kunden")
- A2. Används accentfärgen bara för handlingar och status? (Branding; Color)
- A3. Viker märket för innehållet, och tar dekor plats i första vyn som innehållet behövt? (Branding)

**typografi**
- T1. Är varje typsteg ett fast par av storlek, radhöjd och spärrning, samma i alla bredder och med radhöjden i hela
  pixlar? Hur många unika grader finns, och är stegen jämna eller har de ett medvetet hopp till displaygraden?
- T2. Bärs hierarkin också av vikt och färg, inte bara av storlek? (Conveying hierarchy)
- T3. Sjunker radhöjdskvoten med graden, och följer spärrningen graden för just det här typsnittet?
  (Tracking values; WWDC20)
- T4. Finns tunna vikter i små grader? (Ensuring legibility)
- T5. Har varje texttyp en egen maxbredd, och ligger löptexten på 30–45 tecken i 390 och 45–75 i 1440?
- T6. Skalar displaygraden ungefär 2× mellan 390 och 1440, medan brödtexten ändras högst omkring 20 %?
- T7. Är den svenska texten redigerad för brytning: mjuka bindestreck i långa sammansättningar, fasta mellanslag i
  belopp, telefonnummer och enheter?
- T8. Betyder en färg samma sak överallt, till exempel länkfärgen bara på det som är klickbart? (Color)

**komposition**
- K1. Svarar varje vy på tre frågor: vad ska jag se, vad kan jag trycka på, och hur? (WWDC26, Simplicity)
- K2. Finns en sidmarginal per bredd, och återkommer den som inset och glapp? Hur många unika vänsterkanter har
  textblocken i 1440? (Layout)
- K3. Är mellanrummen inom grupper mindre än mellanrummen mellan grupper, konsekvent? Hur många unika avståndsvärden
  finns? (Layout, Group related items)
- K4. Har första vyn en rubrik, högst två handlingar och ett motiv, och är förstahandsvalet skilt med stil och inte med
  storlek? (Buttons, Style)
- K5. Har sektionerna ett återkommande vertikalt mått som skalar mellan bredderna?
- K6. Är varje bild beskuren för sin bredd och sin roll, följer hörnradien en regel, och är text över bild eller video
  läsbar i varje bildruta? (Images; Materials)

**detaljer** (före valet; Detaljnivån ovan)
- D1. Vilket är riktningens signaturögonblick i första vyn, och syns det i 390 och 1440? Står första vyn färdig med
  reducerad rörelse?
- D2. Har varje interaktivt element, alltså länkar, knappar, menyn, frågor och fält, ett eget läge för hovring, tryck
  och fokus med en övergång ur registret? Vilka byter läge utan övergång?
- D3. Vilka sektioner utgår från ett 21st-block, och vilka block prövades och valdes bort, med id och licens? Är blocket
  omformat till riktningens språk, eller syns det som ett lånat block?
- D4. Lever bilderna där det bär, och är varje bildrörelse avbrytbar och stilla med reducerad rörelse?
- D5. Är mikrotypografin gjord: tabellsiffror i priser och tider, fasta mellanslag, hängande skiljetecken och
  rubrikbrytningar?
- D6. Var känns sidan fortfarande basic, och vilken detalj saknas där?

**rörelse**
- R1. Har rörelsen ett litet register med 3–5 varaktigheter på högst omkring 0,4 s och 1–2 kurvor, och har varje
  rörelse ett syfte? (Motion)
- R2. Går rörelsen att avbryta, går den ut samma väg som in, och utgår menyn från sin knapp? (Motion; WWDC18)
- R3. Har varje egen knapp ett nedtryckt läge som syns direkt? (Buttons)
- R4. Stoppar reducerad rörelse skrolleffekter och automatisk video, och har varje rörlig yta en synlig paus?
  (Accessibility; WCAG 2.2.2)

**polish**
- P1. Har ikonerna samma storlek, detaljnivå och linjetjocklek, är linjevikten som den intilliggande textens, och är
  asymmetriska ikoner optiskt centrerade? (Icons)
- P2. Linjerar text, bild och knappkant optiskt mot samma kant, och inte bara mot sina boxar? (T)
- P3. Har handlingarna samma höjd, radie och stoppning per nivå, och finns omkring 12/24 px mellan intilliggande
  kontroller i 390? (Buttons; Accessibility, Mobility)
- P4. Syns hantverkets felsignaler: väntan efter tryck, hackig skrollning, felställda ikoner eller layout som går
  sönder i 768 eller i liggande 390? (WWDC26, Craft)

**innehåll och formulär**
- I1. Används kundens termer konsekvent, och börjar knapptexterna med verb? Säger länktexterna vart de leder? (Writing)
- I2. Står felmeddelandena vid fältet, utan skuld och utan "hoppsan", och säger de hur man rättar? (Writing)
- I3. Motsvarar fältets bredd den text som väntas? Bekräftar tacksidan att förfrågan kommit fram och vad som händer
  sedan? (Text fields; Feedback)

**kritik**
- C1. Vad är sidan till för, och vilket element kunde tas bort utan förlust? (Design principles, Purpose och Simplicity)
- C2. Beter sig det som ser likadant ut likadant, och står handlingarna på samma plats på alla sidor? (Familiarity)
- C3. Vilka detaljer avslöjar slarv (P1–P4)? (Craft)
- C4. Vilken känsla förmedlas, och passar den kunden? Står dekor i vägen för uppgiften? (Delight)
- C5. Känns sidan premium eller basic, med Apple och Nike som ribba för detaljtätheten? Var saknas detaljer (D1–D6)?
  (ägarens dom 2026-10-13)

Frågorna T1, T3, K2, K3 och P3 mäts ur renderingen av stilrapporten (`kontroller/stil.mjs`, avsnittet Precision i
STIL.md och fältet `precision` i STIL.json): typstegen som par av storlek, radhöjd och spärrning med antalet varianter per
grad, graderna med radhöjd utan hela pixlar, vänsterkanterna, avståndsvärdena med de tio vanligastes täckning och
handlingarnas höjd och radie. D2 mäts delvis: hur många interaktiva element som har en övergång. Talen prövas mot
riktningens egen regel, aldrig mot apple.com eller nike.com. De övriga
frågorna kräver bilderna och en bedömning, som är en AI-bedömning och aldrig ägarens dom.
