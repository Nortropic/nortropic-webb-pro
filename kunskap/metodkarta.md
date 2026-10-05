# Metodkartan — skills och kunskap per steg

Den enda källan för vad varje steg i skapandeflödet ska besvara, vilka skills och kunskapsfiler som stöder det, vilka
avsnitt av dem, och hur motsägande råd avgörs (ägarens begäran 2026-10-05: skillsen i sin fullo, krockarna avgjorda,
best practice som helhet; synpunkterna på kartan samma dag). Företrädet står i `kunskap/designregler.md`: gemensamma
kvalitetskrav, Nortropics produkt- och ägarbeslut med räckvidd, kundens behov, designhypoteser; en skills standardråd
står sist. Citaten och källorna bakom varje avgörande: `kunskap/skillkrockar.md` (K-numren nedan).

**Så levereras metoden:** `kontroller/metod.py` läser stegens block ```` ```utdrag ```` (en rad per källa: väg, och
rader eller en rubrik) och skriver vid varje körning stegets filer i `underlag/<slug>/atelje/metod/`: kartans text för
steget, avgörandena och utdragen med källa och hash, delade så att varje fil ryms i ett Read utan offset och limit
(högst 30 000 tecken). Prompterna pekar på de filerna, och kandidaternas status och granskningar bär hashen. Låset
`kunskap/metodkarta.lock.json` stoppar leveransen när en källa ändrats sedan utdragen prövades, så att rader aldrig
tyst pekar fel. I läget full prövas läsningen i transkriptet och redovisas skild från tillämpningen: en fil räknas som
läst när ett felfritt Read täckt alla dess rader. I skissläget, och i stegen med uppslag, redovisas vad som öppnades,
utan krav: före-filen är kärnan, och uppslaget slås upp när uppgiften behöver det.
**Verktygen, en källa:** kompetensblocken nedan säger vilka skills, verktyg och MCP:er varje pass har. Samma block ger
sessionens behörigheter (`kontroller/kompetens.py` till `--allowedTools`) och raderna i passets uppdrag, så att
dokumentationen, prompten och behörigheten säger samma sak. Sessionerna har skillverktyget och användarens
MCP-anslutningar; kundvakten (`kontroller/kundvakt.py`, en krok före varje anrop) stoppar ett anrop till en extern
designtjänst som bär kundens uppgifter. Bygget och fotograferingen går genom förhandsvisningen, och beroendena kommer
förberedda och låsta ur mallen (`kunskap/beroenden.md`); git, npm, npx och node körs inte direkt i sessionerna.

## Avgöranden

- **Bilder (äkthet):** en bild som visar verksamheten (arbeten, personer, lokaler, resultat) är dess egen; illustrativt
  material som inte utger sig för att dokumentera den (licensierade illustrationer, texturer, konceptbilder, form i
  koden) är tillåtet med källa i BILDER.md eller DESIGN.md (`kunskap/bild.md`). Bilderna serveras från sajten. Saknat
  material står under "Material" i RIKTNING.md, beställs och får en märkt platshållare (K06–K09, K11, K13).
- **Sanning (kvalitetskrav):** varje namn, tal, datum, omdöme och märke kommer ur underlaget, också i exempel; citat står
  ordagrant med källans attribution och avkortas bara synligt med "…"; löften, funktioner och certifieringar bara med
  källa (K10, K12, K43, K44).
- **Teknik (standardval för lokala tjänsteföretag):** Astro med förrenderade sidor, och en sammanhängande implementation
  per riktning ur mallens låsta beroenden: egen CSS, CSS-variabler (Referos direkt), Tailwind, Astro- och React-
  komponenter, Motion (`kunskap/beroenden.md`). Innehållet och navigationen fungerar utan JavaScript, rörelse respekterar
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
  korta rubriker, få produkter). Varje kandidat säger vilken kvalitet den återskapar, vad den kräver och om kundens
  material bär det; det tidiga kompositionsprovet avgör, och det som inte bär ändrar kompositionen och beställs
  (`kunskap/bild.md`, art direction).
- **Sektionsordningen** motiveras ur besökarens frågor och toppuppgifterna i BRIEF.md; skillsens sektionspaket (AIDA,
  landningssidans ordning) används inte (K22).
- **Process:** ingen svarar i flödets sessioner. Uppdraget och underlaget är svaret; antaganden skrivs i RIKTNING.md och
  arbetet fortsätter till stegets "Visar". Riktningen ges av UPPDRAG.md: ingen tärning, inget concept-seed, inga
  förhandsplaner eller egna sanningskällor ur skills (MASTER.md, PRODUCT.md, brand-guidelines). Varven: i skissläget
  inget fast antal, varje varv åtgärdar en konkret brist skaparen sett i sina bilder eller vid jämförelsen med
  referensen; i läget full och i förfiningen är minst tre förhandsvarv en arbetsregel, ingen kvalitetsbedömning.
  Verktygen per pass står i kompetensblocken. Inga test-, variant- eller prototypsidor i src/pages: varje index.astro
  där blir en undersida. DESIGN.md är kontraktet: värdena, valda tillstånd (mörkt läge) och importerade stilvärden
  (`kunskap/bygge-referens.md`). Granskaren svarar bara i sitt schema (K46–K55, K57, K58).
- **Före ägarens val i skissläget** granskar ingen panel och ingen förbättringsrunda körs: de snabba kontrollerna
  markerar brister och ändrar aldrig uttrycket.
- **Granskning före förbättring (läget full):** granskningen bedömer först det en besökare uppfattar (bilderna, trädet
  och axe mot besökarens uppgift) och sedan skaparens motivering. Förbättringsrundan före ägarens val rättar bara objektiva fel
  (kvalitetskrav och hinder för uppgiften), aldrig smak, så att kandidaterna inte jämnas ut; föreversionen bevaras, och
  ägaren kan jämföra och välja den.
- **En källa per värde:** better-ui för tryck, ikoner och skuggor; emil-animate för om och hur länge något rör sig;
  better-layout för innehållsstyrda brytpunkter (proven tar 390, 768 och 1440); svenska citattecken ” ” och tankstreck i
  intervall (9–17) enligt `kunskap/copy-kontroll.md`, högst ett tankstreck per stycke i löptext (K28, K64–K67).

## Kompetenserna

Ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA"; ägarens uppdrag 18:53Z, punkt 5: varje
roll läser de fullständiga relevanta delarna, utan tunna sammanfattningar och utan att varje metodtext läggs i varje
skapares uppdrag; Codex via ägaren 19:04Z, punkt 7–9: varje riktning får en sammanhängande tillämpning, med full tillgång
till alternativen och fullständig läsning av den valda metoden.

Varje roll har en **kärna** och **alternativ**. Kärnan är rollens sammanhängande metod och läses hel innan sessionen
ändrar något (en fil större än en läsning läses i delar med offset och limit tills alla rader är lästa). Alternativen är
stilvarianter och recept för olika riktningar: sessionen väljer de som passar riktningen, läser dem hela och skriver
valet med skäl, eller skriver varför inget passade. Ett recept som säger emot ett annat, ett ägarbeslut eller kundens
behov avgörs av Avgörandena ovan, designreglerna och kundens aktuella domar, som varje session med en roll får.

Rollerna arbetar där de gör nytta, en gång:

- **planera** och **planprövning** (före skaparna): planeraren skriver omkring tio uppdrag som skiljer sig i hur
  informationen ordnas, och planprövningen prövar dem mot kunden, materialet och referenserna.
- **skapa** (skissen): skaparen tillämpar design och komposition, typografi och färg, innehåll och UX och den
  responsiva implementationen i en sammanhängande skiss. Före ägarens val ändrar ingen annan session skissen.
- **fordjupa** (efter ägarens val): förfiningen bygger hela sajten med samma roller och designsystemet.
- **rorelse** och **granskning** (efter fördjupningen, en gång var): interaktion och rörelse, och tillgänglighet och
  visuell granskning, på den färdiga sidan med en avgränsad interaktionsväg (förhandsvisningens tillstånd: tangentbord,
  fokus, hovring, meny, reflow 320 och reducerad rörelse). Passet redovisar tre saker var för sig: koden som ändrades,
  beteendet som prövades och den visuella bedömningen före och efter.

Externa designtjänster når aldrig kundens uppgifter (kontroller/kundvakt.py). Varje block nedan: rollen, uppgiften,
passen, kärnan, alternativen, verktygen, MCP:erna och vad passet visar.

```kompetens plan
namn: Planering och planprövning (design och innehåll)
uppgift: Skriva och pröva uppdrag med verkligt skilda designriktningar (huvudreferens, makrostruktur, typografi, bildstrategi) mot kunden, materialet och referenserna innan någon bygger.
pass: planera, planprovning
kärna: refero-design/SKILL.md; impeccable/reference/shape.md; impeccable/reference/clarify.md; kunskap/bild.md
välj: hallmark/references/macrostructures.md; hallmark/references/structure.md; frontend-design/SKILL.md; taste-soft/SKILL.md; taste-minimalist/SKILL.md; taste-brutalist/SKILL.md; ui-ux-pro-max/SKILL.md; brand/SKILL.md
verktyg: uxsok
mcp: refero, mobbin
visar: varje uppdrag har en huvudreferens som bär riktningen, ett referenslås (det som ska bevaras, det som lånas, det som väljs bort) och en uppgift för besökaren; uppdragen skiljer sig i hur informationen ordnas
```

```kompetens komposition
namn: Design och komposition
uppgift: Forma en sammanhängande riktning ur huvudreferensen, kundens material och besökarens uppgift, och bevara referensens kvalitet (proportioner, komposition, bildstorlek och beskärning, komponenternas form) i kundens innehåll.
pass: skapa, fordjupa
kärna: refero-design/SKILL.md; impeccable/reference/craft-floor.md; kunskap/bild.md
välj: hallmark/references/structure.md; hallmark/references/macrostructures.md; hallmark/references/component-cookbook.md; frontend-design/SKILL.md; impeccable/SKILL.md; impeccable/reference/new-work.md; taste/SKILL.md; taste-soft/SKILL.md; taste-minimalist/SKILL.md; taste-brutalist/SKILL.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/delight.md; impeccable/reference/mode-persuade.md; brand/SKILL.md; banner-design/SKILL.md; better-variant/SKILL.md; ui-ux-pro-max/SKILL.md; refero-design/references/anti-ai-slop.md; refero-design/references/craft-details.md
verktyg: uxsok, förhandsvisning
mcp: refero, mobbin, trybloom
visar: referenslåset står i RIKTNING.md och syns i den renderade sidan; stilpaketets värden används i koden; skissen skiljer sig från de andra i hur informationen ordnas
```

```kompetens typografi
namn: Typografi och färg
uppgift: Ge sidan typskalan, hierarkin, radlängden och färgernas roller ur stilpaketet och huvudreferensen, anpassade till kundens innehåll.
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
uppgift: Bygga komponenterna och layouten så att mobilens omställning är genomtänkt och 390, 768 och 1440 håller ihop, i en implementation som är enkel att underhålla.
pass: skapa, fordjupa
kärna: impeccable/reference/layout.md; impeccable/reference/adapt.md; better-layout/SKILL.md
välj: emil-mobile-native/SKILL.md; ui-styling/SKILL.md; better-ui/SKILL.md; hallmark/references/responsive.md; hallmark/references/layout-and-space.md
verktyg: förhandsvisning
mcp: mobbin
visar: mobilen och datorn, och mellanbredden där layouten byter form, i den renderade sidan; komponenterna och stilarna i egna filer där de återanvänds
```

```kompetens rorelse
namn: Interaktion och rörelse
uppgift: Välja och genomföra de beteenden som passar sidan, var och en med ett syfte; ett genomtänkt beslut kan vara att något ska vara stilla.
pass: rorelse
kärna: impeccable/reference/animate.md; emil-design-eng/SKILL.md; emil-animate/SKILL.md
välj: emil-find-animation-opportunities/SKILL.md; emil-review-animations/SKILL.md; emil-improve-animations/SKILL.md; emil-animation-vocabulary/SKILL.md; emil-apple-design/SKILL.md; refero-design/references/motion.md; hallmark/references/microinteractions.md; hallmark/references/interaction-and-states.md
verktyg: förhandsvisning
mcp: refero
visar: varje beteende prövat med förhandsvisningens tillstånd (meny, hovring, fokus, tangentbord, reducerad rörelse) och redovisat för sig; rörelse respekterar prefers-reduced-motion
```

```kompetens granskning
namn: Tillgänglighet och visuell granskning
uppgift: Inspektera den renderade sidan och interaktionsvägen, och rätta de konkreta bristerna i en avgränsad omgång utan att byta stil.
pass: granskning
kärna: impeccable/SKILL.md; impeccable/reference/critique.md; impeccable/reference/polish.md; impeccable/reference/audit.md; impeccable/reference/craft-floor.md; better-accessibility/SKILL.md; refero-design/references/visual-workflow.md
välj: impeccable/reference/harden.md; impeccable/reference/optimize.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/degraded/finish-reviewer.md; better-interface-review/SKILL.md; better-interface/SKILL.md; emil-break-ui/SKILL.md; better-break/SKILL.md; taste-redesign/SKILL.md; hallmark/references/slop-test.md; hallmark/references/anti-patterns.md
verktyg: förhandsvisning, detektor
mcp: refero
visar: bristerna i den renderade sidan och i tillstånden (tangentbord, fokus, reflow 320, reducerad rörelse, axe) är rättade eller motiverade, före och efter; detektorns fynd är rättade eller prövade mot ägarbesluten
```

```kompetens leverans
namn: Designsystem och överlämning
uppgift: Låta DESIGN.md och koden säga samma sak, med stilpaketets importerade värden och de valda tillstånden, så att leveransen utvecklar den godkända koden vidare.
pass: fordjupa
kärna: kunskap/bygge-referens.md; impeccable/reference/extract.md; design-system/SKILL.md
välj: impeccable/reference/document.md; taste-stitch/SKILL.md
verktyg: design
mcp:
visar: DESIGN.md stämmer med koden, och sidorna använder dess variabler eller stilpaketets
```

**Ingen uppgift i flödet** (finns i verktygslådan, med skälet): emil-write-swift (Swift), emil-animate-expo (React Native
och Expo), emil-ask-sonner (en toast i en app), slides (presentationer), taste-imagegen-frontend-mobile (appskärmar),
emil-pick-ui-library (paketval görs utanför flödet, `kunskap/beroenden.md`), emil-prototype (kandidaterna är
varianterna), taste-v1 (ersatt av taste), taste-gpt (fast AIDA-ordning mot K22, och GSAP finns inte bland de låsta
beroendena). Bildgenererande skills (design, taste-brandkit, taste-imagegen-frontend-web, taste-image-to-code) kräver
en bildgenerator som flödets sessioner inte har; illustrativt material som inte utger sig för att visa verksamheten
beställs som material (Avgörandena, Bilder). Flödets egna processkills (bygg-sajt, kirurg, backlog,
writing-for-agents) styr arbetet och är inga designkompetenser. Övriga MCP-anslutningar (Gmail, Google Drive, GitHub,
Resend, Jotform, Railway, Claude Docs med flera) rör kunddata, utskick eller drift och har ingen uppgift i skapandet;
sessionerna nekar dem.

## Research

**Fråga:** vilka skilda grundidéer kan verksamhetens värld och material bära, och vilka antaganden om besökarna kan
ändra designbesluten?

**Underlag:** BRIEF.md (§2 målgrupper och toppuppgifter med insiktskällor, "Antaganden som behöver bekräftas"),
RESEARCH.md, bilder/BILDER.md, referenspaketet och tjänsternas förra undersökning, domloggen och historiken.

**Till nästa steg:** FORSKNING.md med antagandena (underlag, prövning, vad som ändras), nytt och återanvänt material
(nytt referenspaket, tjänsternas svar med hela stildokument och bilder) och riktningarna researchen öppnar.

**Visar:** frågorna och sajterna spänner över skilda grundidéer ur verksamhetens värld, inte varianter av samma
utseende; varje antagande har underlag eller "ännu inte observerat", en prövning som beskriver besökarens mål utan att
avslöja knappen, och en följd.

```utdrag före
kunskap/designregler.md
kunskap/referensjakt.md
kunskap/visuell-niva.md
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
kvaliteten som återskapas, vad den kräver och om kundens material bär det, antagandena, undersidan, materialbehovet och
skillnaden mot de andra.

**Visar:** uppdragen är olika sätt att presentera verksamheten och skiljer sig i hur sidan organiserar kundens
information (innehållshierarki, bildstrategi, typografiskt system, navigation, hur förtroende byggs), inte bara i färg och
typsnitt; varje uppdrag besvarar uppgiften, beslutsinnehållet, antagandena och prövningen och har en hypotes ur
researchen och kundens material; inget uppdrag är avsiktligt svagt. Antalet (cirka tio) är vårt val för omgången: parallella prototyper före låsning har stöd (Dow m.fl.
2010), men ingen studie fastställer ett antal.

```utdrag före
kunskap/designregler.md
kunskap/bild.md # Art direction
kunskap/visuell-niva.md
better-variant/SKILL.md rad 13–37
```

```utdrag uppslag
kunskap/referenser-professionella.md
frontend-design/SKILL.md rad 15–34, 47–53
impeccable/reference/new-work.md rad 65–67
impeccable/reference/mode-persuade.md rad 9
taste/SKILL.md rad 17–23, 38–39
```

## Skapa

**Fråga:** bär uppdragets idé med kundens riktiga material, på mobil och dator, och går besökarens viktigaste uppgift
att genomföra?

**Underlag:** UPPDRAG.md, kundens fakta och bilder, briefen, researchen och referensbilderna, domloggen.

**Till nästa steg:** en byggd startsida och undersida (kod/), skärmbilder i 390, 768 och 1440, axe, och RIKTNING.md med
huvudreferensen, hypotesen, referensens kvalitet, varven, "Visar" och materialet.

**Visar:** grundidén syns i den renderade sidan; kundens material bär kompositionen (eller kompositionen är anpassad
efter materialet och bristen beställd); den viktigaste besökaruppgiften går att genomföra från startsidan; mobilversionen
håller ihop; kvalitetskraven håller (bygget, konsolen, spill, axe). Huvudreferensens kvalitet syns i fyra relationer,
med referensbild och kandidatens bild bredvid varandra i RIKTNING.md: bildens beskärning mot rubriken, de typografiska
storlekarna och hierarkin, täta och luftiga sektioner och rytmen, navigation och interaktion mot innehållet. Skaparen
skriver under "Visar" vilken bild som visar var och en. Arbetsregel i läget full: minst tre förhandsvarv.

```utdrag före
kunskap/designregler.md
kunskap/bild.md
kunskap/visuell-niva.md
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
räckvidd och avgörandena. Kompetenserna (avsnittet Kompetenserna) är obligatoriska: skaparen tillämpar art direction
och typografi, layout och bild med sina skills fullständiga instruktioner, och efter skissen gör varje annan kompetens
sitt eget pass. Ägarens domar över tidigare byggen och kundens historik slås upp när de besvarar en konkret fråga.

**Till nästa steg:** en byggd skiss (första vyn, den viktigaste sektionen, navigationen och de interaktioner som behövs
för att förstå förslaget), skärmbilder i 390, 768 och 1440, de snabba kontrollerna (bygget, konsolen, spill, axe,
siffror utan belägg, menyn) och RIKTNING.md med huvudreferensen, hypotesen, vad referensen lärde, varven och
materialet. Hela startsidan, undersidan och besökarens centrala flöde byggs först när ägaren valt (Förfina).

**Visar:** grundidén syns i den renderade skissen och skiljer sig från de andra i hur kundens information presenteras och
uppgiften löses, inte bara i färg; kundens material bär kompositionen, eller ett tydligt märkt utkast eller en
platshållare står där material saknas; mobilen och datorn är genomarbetade. Inget fast antal varv: varje varv åtgärdar
en brist skaparen sett i sina egna bilder eller vid jämförelsen med referensen.

```utdrag före
kunskap/designregler.md
kunskap/bild.md
kunskap/visuell-niva.md
```

## Granska

**Fråga:** vad uppfattar en besökare, går den viktigaste uppgiften att genomföra, vilka avvikelser är objektiva fel och
vilka är smak, och bär kundens material referensens kvalitet (de fyra relationerna, jämförda med förebilden)? Granskningen
ersätter inte ägarens visuella val eller ett prov med riktiga besökare; den är underlag till båda.

**Underlag:** första passet: skärmbilderna, tillgänglighetsträdet, axe och briefens uppgifter (inte uppdraget eller
skaparens anteckningar); andra passet: uppdraget, anteckningarna och referensbilderna.

**Till nästa steg:** KRITIK.json med första intrycket, uppgiften med belägg, avvikelserna med slag (krav eller smak),
allvar och om de är avsiktliga och välgrundade, nivån mot ribban och materialbehovet. Förbättringsrundan rättar bara
krav; ägaren ser granskningen efter sitt första beslut.

**Visar:** varje avvikelse har plats, bredd, vad, åtgärd, allvar och slag; en skills förbud bär aldrig ensamt ett fynd;
granskaren har läst de första vyerna (prövas i transkriptet; annars styr granskningen ingenting).

```utdrag
kunskap/designregler.md
kunskap/visuell-niva.md
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

**Fråga:** hur blir den valda kandidaten en sida ägaren godkänner för helbygget, med ägarens ord, det ägaren gillade i
andra förslag och DESIGN.md i takt med koden?

**Underlag:** ägarens dom och delar, RIKTNING.md, KRITIK.json, de andra kandidaternas kod och bilder för de delar
ägaren gillade.

**Till nästa steg:** förfinade sidor, DESIGN.md som sidorna använder, och RIKTNING.md med förfiningens varv och "Visar".

**Visar:** varje punkt i ägarens dom är åtgärdad eller besvarad med skäl; grundidén syns, kundens material bär,
uppgiften går att genomföra och mobilen håller ihop; DESIGN.md är giltig och koden använder dess variabler
(`kontroller/design.py --kandidat`). Arbetsregel: minst tre förfiningsvarv.

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

## Utanför flödet

Kvar i `.claude/skills/` (ägaren 2026-10-05: installerade i sin fullo), men inte i flödets steg, eftersom de bygger på
bildgenerering, React eller native-appar, egna processer eller verktyg som flödet inte har: design, design-system,
ui-styling, banner-design, slides, brand (utom röstramverket), taste-gpt, taste-soft, taste-v1, taste-stitch,
taste-output, taste-brandkit, taste-imagegen-frontend-mobile, taste-imagegen-frontend-web, taste-redesign,
taste-minimalist och taste-brutalist (bara när UPPDRAG.md pekar dit), ui-ux-pro-max:s designsystem, skript och data
(utom checklistan ovan), impeccables kommandon och skript, emil-improve-animations, emil-prototype,
emil-pick-ui-library, emil-ask-sonner, emil-animate-expo, emil-write-swift, emil-animation-vocabulary,
emil-apple-design, emil-find-animation-opportunities, better-break, better-interface-review och writing-for-agents (för
den som skriver om kartan, förorden eller en skill).
