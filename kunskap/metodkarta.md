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
Flödets sessioner har inget Skill-verktyg: det går inte att begränsa till namngivna skills, och flera skills bär
processinstruktioner för en interaktiv session. En skill eller ett avsnitt som kartan inte nämner används inte i flödet.

## Avgöranden

- **Bilder (ägarens dom L3):** verksamhetens egna foton, eller form i koden (SVG ur märket, en karta) när den har en
  funktion. Ingen bildgenerering, inga stockbilder, picsum, Pexels eller externa bild-URL:er; en textdriven första vy
  är ett giltigt val, och saknat material skrivs under "Material" i RIKTNING.md och beställs (K06–K09, K11, K13).
- **Sanning (kvalitetskrav):** varje namn, tal, datum, omdöme och märke kommer ur underlaget, också i exempel; citat står
  ordagrant med källans attribution och avkortas bara synligt med "…"; löften, funktioner och certifieringar bara med
  källa (K10, K12, K43, K44).
- **Teknik (Nortropics produktbeslut för dagens erbjudande, webbplatser åt lokala tjänsteföretag):** statisk Astro med
  sidans egen CSS. Innehållet syns utan JavaScript; rörelse förstärker bara det som redan syns, i CSS och med
  `prefers-reduced-motion`. Ett tema per riktning, inga karuseller, marquees eller scrollkapningar, inga CDN-resurser,
  inga paket utöver typsnitt via `kontroller/typsnitt.py`. Recept för React, Tailwind, shadcn och Motion översätts till
  CSS eller används inte. En bokningstjänst eller en större innehållssajt får ett eget beslut (K14–K21, K40).
- **Referens och stil (ägarbeslut 2026-10-03):** huvudreferensen får bära layout, palett och typografi, och särprägeln
  ligger i vår touch och verksamhetens material. Skillsens listor över förbjudna paletter, typsnitt, centrering,
  etiketter över rubriker, gradienter och pilar är granskningsfrågan "valt av vana utan skäl?", aldrig förbud eller
  krav. Valet av typsnitt och färg skrivs med skäl i RIKTNING.md och märks `valt:` i DESIGN.md; inga reservvärden ur en
  skill (#2563EB, Inter) (K01–K05, K23–K27, K29, K34–K37).
- **Kundens behov (ur briefen, med belägg):** toppuppgifterna och den primära handlingen avgör vad första vyn och
  sidan måste klara. För en lokal tjänsteverksamhet brukar orten och kontaktvägen höra till första vyn, och bevis och en
  skriftlig väg får stå där; Nortropics byggstandard lägger telefonnumret som tel-länk på varje sida när kunderna ringer.
  Telefonnummer, e-post och adress går att markera och kopiera; `user-select: none` bara på draghandtag. Hela listor
  (priser, tjänster) är tillåtna när besökaren frågar efter dem, och inget göms i sidled utan synlig ledtråd (K30–K33,
  K38, K39, K41).
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
  referensen; i läget full och i förfiningen är minst tre förhandsvarv en arbetsregel, ingen kvalitetsbedömning. Inga
  skillskript, hookar, git eller MCP. Inga test-, variant- eller
  prototypsidor i src/pages: varje index.astro där blir en undersida som följer med kandidaten. DESIGN.md skrivs bara i
  husets format (`kunskap/bygge-referens.md`, `kontroller/design.py`). Granskaren svarar bara i sitt schema (K46–K55,
  K57, K58).
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

Ägarens ord 2026-10-05 18:15Z: "du ska använda ALLA SKILLS OCH MCPS TILLGÄNGLIGA". Varje kompetens har en obligatorisk
uppgift i kedjan, med sina skills fullständiga instruktioner (hela SKILL.md och de referensfiler som uppgiften kräver,
som Impeccables arbetsflöde: rätt arbetsbeskrivning för uppgiften, och craft-floor.md direkt före varje ändring i
gränssnittet) och fungerande verktyg. Lösningarna väljs med omdöme: där skillsens standardrecept säger emot varandra
eller ett ägarbeslut avgör Avgörandena ovan; en skill som inte passar uppgiften säger var och varför i passets svar. Ett
pass är genomfört när filerna lästs hela, ändringen syns i den renderade sidan (före och efter) eller passet säger varför
ingen ändring behövdes, och svaret säger vad varje skill förändrade. Att en fil öppnats räcker aldrig. Alla skills och
MCP:er är tillgängliga i sessionerna (skillverktyget, Refero, Mobbin, Trybloom med fler); externa designtjänster når
aldrig kundens uppgifter (kontroller/kundvakt.py).

Passen: **planprövning** (efter planen: specialisterna prövar planerarens designval), **skapa** (skissen), **ux**,
**rörelse**, **mobil** och **kritik** (efter skissen, i den ordningen), och **fördjupa** (efter ägarens val, sedan passen
igen på hela sidan). Varje block nedan: kompetensen, uppgiften, passen, filerna som läses hela, verktygen och vad
passet visar.

```kompetens art
namn: Visuell design och art direction
uppgift: Forma en sammanhängande riktning utifrån kund, material och referenser.
pass: planprovning, skapa, fordjupa
läs: impeccable/SKILL.md; impeccable/reference/new-work.md; impeccable/reference/shape.md; impeccable/reference/mode-persuade.md; frontend-design/SKILL.md; taste/SKILL.md; taste-soft/SKILL.md; taste-minimalist/SKILL.md; taste-brutalist/SKILL.md; ui-ux-pro-max/SKILL.md; brand/SKILL.md; design-system/SKILL.md; better-variant/SKILL.md; banner-design/SKILL.md; impeccable/reference/bolder.md; impeccable/reference/quieter.md; impeccable/reference/delight.md
verktyg: ui-ux-pro-max
mcp: refero, mobbin, trybloom
visar: riktningen bär kundens material och referensens kvalitet; skissen skiljer sig från de andra i hur informationen ordnas; vad varje skill förändrade i riktningen
```

```kompetens typo
namn: Typografi, layout och bild
uppgift: Bearbeta hierarki, proportioner, beskärningar, mellanrum och sidans rytm.
pass: skapa, fordjupa
läs: impeccable/reference/craft-floor.md; impeccable/reference/typeset.md; impeccable/reference/layout.md; impeccable/reference/colorize.md; better-typography/SKILL.md; better-layout/SKILL.md; better-colors/SKILL.md; better-ui/SKILL.md; taste-output/SKILL.md; kunskap/bild.md
verktyg: förhandsvisning
mcp: refero, mobbin
visar: typskalan, radlängden, beskärningarna och rytmen i den renderade sidan, före och efter
```

```kompetens ux
namn: UX och innehåll
uppgift: Göra erbjudandet begripligt och besökarens uppgifter enkla.
pass: planprovning, ux, fordjupa
läs: impeccable/reference/clarify.md; impeccable/reference/distill.md; better-writing/SKILL.md; humanizer/SKILL.md; better-explain-interface/SKILL.md; kunskap/copy-kontroll.md; kunskap/redaktionellt-pass.md
verktyg: förhandsvisning
mcp: mobbin
visar: besökarens viktigaste uppgift går att lösa från första vyn; rubriker, knappar och etiketter säger vad som händer; texten låter som verksamheten
```

```kompetens rorelse
namn: Interaktion och rörelse
uppgift: Välja och genomföra beteenden som passar sidan; ett genomtänkt beslut kan vara att något ska vara stilla.
pass: rorelse, fordjupa
läs: impeccable/reference/animate.md; emil-animate/SKILL.md; emil-design-eng/SKILL.md; emil-find-animation-opportunities/SKILL.md; emil-review-animations/SKILL.md; emil-improve-animations/SKILL.md; emil-animation-vocabulary/SKILL.md; emil-apple-design/SKILL.md
verktyg: förhandsvisning
mcp: refero
visar: varje rörelse har ett syfte och respekterar prefers-reduced-motion, eller passet säger varför sidan ska vara stilla
```

```kompetens mobil
namn: Mobil och tillgänglighet
uppgift: Kontrollera den verkliga upplevelsen över skärmstorlekar och inmatningssätt.
pass: mobil, fordjupa
läs: impeccable/reference/adapt.md; impeccable/reference/audit.md; better-accessibility/SKILL.md; emil-mobile-native/SKILL.md; emil-break-ui/SKILL.md; better-break/SKILL.md
verktyg: förhandsvisning
mcp: mobbin
visar: 390, 768 och 1440 håller ihop; tangentbord, fokus, träffytor, zoom och värsta tänkbara innehåll fungerar; axe utan allvarliga fynd
```

```kompetens kritik
namn: Visuell kritik och slutbearbetning
uppgift: Inspektera det renderade resultatet och rätta konkreta brister.
pass: kritik, fordjupa
läs: impeccable/reference/critique.md; impeccable/reference/polish.md; impeccable/reference/degraded/finish-reviewer.md; better-interface-review/SKILL.md; better-interface/SKILL.md; taste-redesign/SKILL.md; emil-design-eng/SKILL.md; impeccable/reference/harden.md; impeccable/reference/optimize.md
verktyg: förhandsvisning, detektor
mcp: refero
visar: de konkreta bristerna i den renderade sidan är rättade i en avgränsad omgång, före och efter; detektorns fynd är rättade eller motiverade
```

```kompetens leverans
namn: Designsystem och överlämning
uppgift: Låta DESIGN.md och koden säga samma sak, så att leveransen utvecklar den godkända koden vidare.
pass: fordjupa
läs: kunskap/bygge-referens.md; impeccable/reference/document.md; impeccable/reference/extract.md; design-system/SKILL.md; taste-stitch/SKILL.md
verktyg: design
mcp:
visar: DESIGN.md i husets format stämmer med koden, och sidorna använder dess variabler
```

**Ingen uppgift i en statisk webbsajt** (finns i verktygslådan, med skälet): emil-write-swift (Swift),
emil-animate-expo (React Native och Expo), emil-ask-sonner (Reacts toastbibliotek), slides (presentationer),
taste-imagegen-frontend-mobile (appskärmar), ui-styling (shadcn och Tailwind, vi skriver sidans egen CSS),
emil-pick-ui-library (paketval; i flödet installeras bara typsnitt), emil-prototype (våra kandidater är varianterna),
taste-v1 (ersatt av taste), taste-gpt (fast AIDA-ordning och GSAP, mot K22 och paketbeslutet). Bildgenererande skills
(design, taste-brandkit, taste-imagegen-frontend-web, taste-image-to-code) kräver en bildgenerator och ger genererade
bilder, mot ägarbeslutet om verksamhetens egna bilder; de används för designbilder bara efter ägarens beslut. Flödets
egna processkills (bygg-sajt, kirurg, backlog, writing-for-agents) styr arbetet och är inga designkompetenser.

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
