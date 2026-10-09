# Beroenden — förberedda, granskade och versionslåsta

Ägarens uppdrag 2026-10-05 18:53Z, punkt 4: de interna generella förbuden mot Tailwind, React-komponenter,
komponentbibliotek och JavaScript-baserad förstärkning och rörelse omprövas när de saknar ett aktuellt sakskäl;
skyddet mot godtyckliga paketinstallationer i autonoma sessioner behålls, och förberedda, granskade och versionslåsta
beroenden ska gå att använda när de behövs. Referos CSS-variabler används direkt, utan nya paket.

Varje riktning väljer en sammanhängande implementation som bär den valda designen och är enkel att underhålla. Det
här är verktygen, inte en standard: en sida som inte använder dem får inga skript och ingen extra CSS.

## Mallens beroenden (`mall/astro/package.json` och `package-lock.json`)

| Paket | Version | Licens | Till vad | Kostnad i bygget (uppmätt 2026-10-05, gzip) |
|---|---|---|---|---|
| astro | 7.3.5 | MIT | sajten, förrenderade sidor | – |
| sharp | 0.35.5 | Apache-2.0 (libvips LGPL-3.0) | `astro:assets`, bildformat och storlekar | – |
| tailwindcss, @tailwindcss/vite | 4.3.3 | MIT | Tailwind 4 med `@theme` (stilpaketets tokens) | grundstilar och använda klasser: 2,4 kB CSS |
| @astrojs/react, react, react-dom | 7.0.0, 19.3.0 | MIT | React-komponenter; som ö bara där interaktionen kräver det | en ö: cirka 69 kB JS på sidan som har den |
| motion | 14.0.0 | MIT | rörelse i ett `<script>` (`motion`) och i en React-ö (`motion/react`, det som hette Framer Motion) | `motion/mini`: 3,3 kB; hela `motion`: 19 kB |
| gsap | 3.15.0 | Standard "No Charge" GSAP License (fri också kommersiellt, alla plugins inräknade; se nedan) | tidslinjer och scrollsekvenser i ett `<script>` | kärnan: 27 kB; med ScrollTrigger: 44 kB (uppmätt 2026-10-07, gzip) |

Granskningen 2026-10-05: 336 paket i låset, `npm audit` 0 sårbarheter, installationsskript bara i esbuild och fsevents
(fanns redan genom Astro och Vite), licenserna MIT, Apache-2.0, BSD, ISC, 0BSD, BlueOak, CC0, MPL-2.0 (lightningcss)
och LGPL-3.0 (sharps libvips). Provbygget av en sida med Tailwind, en React-ö och Motion gav inga konsolfel och inga
CSP-överträdelser (Astros CSP hashar öns skript); en sida utan dem fick inga skript.

Granskningen 2026-10-07 (gsap 3.15.0, ägarens uppdrag samma dag, punkt 5C): installerat utan skript i kopior av båda
mallarna, 337 paket i `mall/astro` och 420 i `mall/leverans`, `npm audit --omit=dev` 0 sårbarheter, inga nya
installationsskript, gsap utan egna beroenden; paketet deklarerar licensen "Standard 'no charge' license:
https://gsap.com/standard-license". Licensen (gsap.com/licensing och gsap.com/standard-license, lästa 2026-10-07): i
kraft 2025-04-30, senast ändrad 2025-05-30, efter Webflows förvärv; fri också för kommersiellt bruk och för alla
plugins som förut var betalda (SplitText, MorphSVG, ScrollSmoother …); undantagen är verktyg för visuell
animationsbyggnad utan kod som konkurrerar med Webflow, reverse engineering för konkurrerande produkter och borttagna
notiser; AI-genererad kod är uttryckligen tillåten. Provbygget (rökprovets sida `/rorelse/`, `kontroller/rokprov.sh`):
sidan bygger under mallens CSP utan konsolfel, står stilla och färdig för den som bett om mindre rörelse och rör sig
annars. Beteendeprovet i `kontroller/rokprov/rorelse.mjs` mäter start, mellanläge och slutposition med Playwright
Clock, också preferensbyte under rörelsen och innehållet utan JavaScript (källor lästa 2026-10-07:
https://playwright.dev/docs/clock och https://gsap.com/docs/v3/GSAP/gsap.matchMedia()/). Kostnaden per sida, uppmätt i mallkopian: GSAP-kärnan 69,8 kB rå och 27,1 kB gzip,
med ScrollTrigger 112,5 kB rå och 44,3 kB gzip; hela `motion` (animate och inView) 53,4 kB rå och 19,1 kB gzip. Allt
under byggstandardens 200 kB (3.7), men GSAP är det tyngsta valet och bär sig bara när beteendet kräver det.

## Så används de

- **Stilpaketets CSS-variabler (Refero), utan paket:** `kontroller/stilpaket.py` lägger originalets variabler i
  kandidatens `src/styles/`; importera filen i layouten eller sidan (`import '../styles/stil/<namn>.css'`) och använd
  `var(--color-…)`, `var(--font-…)`, `var(--text-…)`. Kundanpassningen skrivs i en egen fil som läser originalet.
- **Tailwind 4:** en CSS-fil med `@import "tailwindcss";` och `@theme { … }` (stilpaketets Tailwind-tema är ett färdigt
  `@theme`-block), importerad i layouten. Ett system per projekt: Tailwind eller egna stilmallar som bärande metod.
- **React:** komponenten i `src/components/<Namn>.jsx`. Utan `client:`-direktiv renderas den till HTML utan skript;
  `client:visible` eller `client:idle` bara när interaktionen kräver tillstånd i webbläsaren. Innehållet och
  navigationen fungerar utan JavaScript (byggstandarden).
- **Motion:** `import { animate } from 'motion/mini'` i ett `<script>` (Astro bundlar och hashar det), med
  `prefers-reduced-motion` respekterat; hela `motion` (scroll, inView, fjädrar) när rörelsen kräver det; i en React-ö
  `import { motion } from 'motion/react'`. Motion är det nya namnet på Framer Motion: `motion/react` är gamla
  framer-motion, och npm-paketet `framer-motion` 14.0.0 är ett alias som aldrig installeras bredvid (båda får inte
  finnas). Skillen `.claude/skills/motion/` (Motion AI Kit, fria delen) är därför också Framer Motion-skillen, och
  dess MCP (`kontroller/mcp/motion.json`, `search-motion-docs`) söker dokumentation och exempel för `motion`,
  `motion/react` och `motion-v`; ingen separat Framer Motion-skill eller -MCP finns eller behövs.
- **21st.dev Builder** (ägarens val 2026-10-07): MCP:n `kontroller/mcp/21st.json` (https://21st.dev/api/mcp, nyckeln
  `TWENTYFIRST_API_KEY` ur `~/.nortropic-hemligheter/webb-pro/21st.env`, insatt av `atelje.tjugoforsta_mcp_fil` i en
  0600-fil bredvid nyckeln) ger rollen komposition komponentsök (`search`, fritt), en vald komponents kod
  (`get_component`, förbrukar Builders hämtningar) och inspiration. Komponenterna är React/shadcn med Tailwind: koden
  är material som anpassas till Astro, mallens CSS och CSP:n; `npx shadcn add` och Tailwind installeras aldrig på egen
  hand (beslut här först). Källa, författare, licens och beroenden skrivs i RIKTNING.md under Referenser.
- **GSAP:** `import gsap from 'gsap'` (och `import { ScrollTrigger } from 'gsap/ScrollTrigger'` med
  `gsap.registerPlugin`) i ett `<script>`. Varje rörelse står innanför `gsap.matchMedia()` med
  `(prefers-reduced-motion: no-preference)`, så att den som bett om mindre rörelse får sidan färdig och stilla
  (mallens `Bas.astro` stänger CSS-övergångar, inte skriptdriven rörelse; rökprovets `/rorelse/` prövar det). Ingen
  ScrollSmoother eller annan mjuk scroll (metodkartans Avgöranden, WCAG 2.2.2); det ScrollTrigger avtäcker syns
  också utan skript. Skillen `.claude/skills/gsap/` (gsap-skills, MIT) med vårt index.
- **Valet per beteende (ägarens uppdrag 2026-10-07, punkt 5C):** rollen rorelse väljer tekniken per beteende ur
  designens och implementationens behov och skriver valet med skäl i passets `teknikval` och i RIKTNING.md: CSS först
  när den räcker (tillstånd, enkla övergångar, `@starting-style`, korta staggers med `transition-delay`), Motion för
  fjädrar, avbrytbara gester, layoutanimationer och React-öar, GSAP för tidslinjer med flera steg och scrollsekvenser
  (ScrollTrigger). Ett genomtänkt beslut kan vara att något ska vara stilla, och ingen rörelse läggs till för att fylla
  en kvot. Beslutstabellen är `motion/best-practices/css-or-motion.md` (läses hel före valet i passet rörelse)
  tillsammans med raden ovan.
- **Komponentbibliotek** som kräver nya paket (shadcn/ui med Radix, Fluent, Carbon) finns inte i låset. Ett behov
  förbereds som ett nytt beroende nedan; mönstren går ofta att bygga som Astro-komponenter med de låsta paketen.

## Kvalitetskraven som består (inte teknikval)

Isolering och skydd för andra kunders filer, kontroll över nätåtkomst och hemligheter, tillgänglighet och
tangentbordsanvändning, prestandabudgeten (byggstandarden 4: bildvikt, typsnitt, Lighthouse), fungerande grundinnehåll
och robust navigation utan JavaScript, och `prefers-reduced-motion`. Ett beroende som bryter något av dem används inte
på den sidan, hur bra det än ser ut.

## Ett nytt beroende

Flödets sessioner kör aldrig npm, npx eller node direkt (`kontroller/atelje.py`, NEKAS); typsnitt går genom
`kontroller/typsnitt.py`. Ett nytt beroende förbereds utanför flödet, i den här ordningen:

1. Installera i en kopia av mallen (`npm install --ignore-scripts`), exakt version i `package.json`.
2. Granska: licensen för paketet och dess beroenden ur låset, installationsskripten (`hasInstallScript` i låset),
   `npm audit --omit=dev`, och paketets källa (underhåll, nedladdningar, ägare).
3. Provbygg en sida som använder det, under mallens CSP, och mät kostnaden (gzip) och konsolen i webbläsaren.
4. Lägg `package.json` och `package-lock.json` i `mall/astro/`, uppdatera tabellen ovan med granskningen, och kör
  `kontroller/rokprov.sh` tills det är grönt. Nya sajter installerar med `npm ci` mot låset (`kontroller/ny_sajt.py`).

## Chrome DevTools MCP (låst verktyg för inspektionssessionen)

Ägarens uppdrag 2026-10-07, punkt 7 och 5: MCP:n prövas i en egen inspektionssession (`kontroller/devtools.py`), aldrig i
skaparens eller kritikens session och aldrig på användarnivån. Den är inget paket i mallen eller i `kontroller/package.json`:
versionen låses i konfigurationen och körs ur npm:s npx-cache.

| Verktyg | Version | Källa och datum | Licens | Krav | Så körs den |
|---|---|---|---|---|---|
| chrome-devtools-mcp | 1.10.1 (npm 2026-09-23; prövad 2026-10-07) | github.com/ChromeDevTools/chrome-devtools-mcp (README, docs/configuration.md, docs/tool-reference.md, lästa 2026-10-07) och `npx chrome-devtools-mcp@1.10.1 --help` | Apache-2.0 | Node ^20.19 ‖ ^22.12 ‖ ≥23 (node@22 och node@24 går); Chrome: Playwrights Chromium ur `kontroller/node_modules` (`NWP_DEVTOOLS_CHROME`), aldrig ägarens installerade | `kontroller/mcp/chrome-devtools.json`: `npx -y chrome-devtools-mcp@1.10.1 --isolated --headless --no-usage-statistics --no-performance-crux --no-category-input --no-category-memory --no-javascript-evaluation --viewport=1440x900 --proxyServer=${NWP_DEVTOOLS_PROXY} --executablePath=${NWP_DEVTOOLS_CHROME}`, med `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS=1`; `--strict-mcp-config` i sessionen |

Gränserna: `--isolated` ger en tillfällig profil som tas bort efteråt; `--autoConnect`, `--browserUrl` och `--wsEndpoint`
(anslutning till en körande Chrome med öppen felsökningsport) används aldrig, och `devtools.konfig()` vägrar en
konfiguration som har dem eller saknar någon av de fyra flaggorna. Nätet går genom nätgränsen
(`kontroller/webblasare/natproxy.mjs`, samma regler som webbtjänsten: referensens värdar och resursursprungen ur
paketet, uppslag till publika adresser, allt annat nekat och loggat i `natgrans.json`); utan proxy- och Chrome-variablerna
står de oexpanderade i konfigurationen och ingen sida nås. Googles användningsstatistik och CrUX-anropen är avstängda.
Verktygen med uppgift är exakt de sessionen släpper (`devtools.VERKTYG`), beslutet per verktyg står i metodkartan
(Tjänsternas verktyg), och `kontroller/kompetens.py --prova` fäller en skillnad.

Ny version: pröva först med `devtools.py --torr` och sedan en verklig session mot provets syntetiska sajt (som
`prov_referensinspektion.py` fall 8 gör med provklienten), uppdatera versionen i konfigurationen och den här tabellen i
samma commit, och kör rökprovet. Underhållet (`kontroller/underhall.py`) slår ännu inte upp den här versionen: den byts för
hand, med samma karenstid som de globala npm-paketen.

## Underhåll: den senaste versionen som klarat proven

Ägarens uppdrag 2026-10-05 (19:13Z, 20:27Z och ~20:50Z, ordagrant i minnet): ingenting i verktygslådan släpar efter, och
varje körning låser sina versioner. Två verktyg delar komponenterna och läget (`kontroller/verktygslada.py`):

- **Underhållet** (`kontroller/underhall.py`), en gång per dygn från dashboarden när ingen körning pågår, eller för hand:
  slår upp senaste versionen, prövar varje uppdatering för sig i en isolerad kopia (installation, säkerhetsgranskning
  och ett provbygge; nya huvudversioner och mätinstrument med hela rökprovet i en egen worktree), tar in det som klarar
  proven, checkar in och skriver vad som byttes. Hur varje slag prövas står i verktygets beskrivning. En avvisad version
  sparas med felet och prövas igen först när en nyare kommer.
- **Startkontrollen** (`kontroller/startkontroll.py`), före varje start (arbetaren i `kontroller/atelje.py` och
  `kor.sh`): bekräftar läget utan nya uppslag, prövar förmågan med små prov som återanvänds medan förutsättningarna är
  oförändrade, låser versionerna och skriver startkvittot (`underlag/<slug>/atelje/STARTKVITTO.md`; helbyggets
  `STARTKVITTO-BYGGE.md`). Ett nödvändigt verktyg som inte fungerar stoppar starten; det som inte prövats står som
  behållet med skäl, aldrig som uppdaterat. Kvittot anger också repots commit, gren och antalet ocommittade filer
  ("ej angivet" utan git), och en informationsrad om dokumentationen (`README.md`, Var information finns) som aldrig
  stoppar en start.

**Vad startkvittot säger** (ägarens uppdrag 2026-10-07, punkt 3, ordagrant i minnet):

- **Körväg och fas.** Kvittot säger vilken körväg det gäller: prototypkörningen i kandidatflödet (före eller efter
  researchen), prototypkörningen i den äldre utforskningen (före utforskningen eller efter valet) eller helbygget. Det
  gäller aldrig Figma-piloten, vars sessioner startas utanför repots körvägar, och ett kvitto för en körväg verifierar
  ingen annan.
- **Referensunderlaget efter fasen.** Före researchen prövas förutsättningarna: underlaget som researchen läser, att
  kundvakten kan läsa kundens uppgifter, Refero, Mobbin och kundvakten. Underlaget står då som planerat i researchen.
  Efter researchen prövas FORSKNING.json (körningens egen), referenspaketet, TJANSTER.json och UPPDRAGSMATERIAL.json.
  Det körningen hämtade står som använt med resultat, och det som återanvändes ur en tidigare research som tillgängligt,
  med sin tid. Fel, tomma tjänster, en tilldelad tjänst som researchen aldrig frågade, tomt uppdragsmaterial, träffar
  utan bild och bilder som saknas på disken står som blockerade eller misslyckade, aldrig som använda. Den äldre
  utforskningen prövar REFERENSER.md:s rader, och en tom eller inaktuell fil godtas inte; helbygget och putsningen
  prövar VINNARE.json. Kontrollen skriver aldrig i underlaget och skapar aldrig REFERENSER.md.
- **Vad sessionerna når.** Raderna ur `claude mcp list` säger vad maskinen har. Vad ateljéns sessioner laddar prövas med
  en kort session med flödets egna argument (`verktygslada.prova_sessionen`: samma `--setting-sources`,
  `--strict-mcp-config`, `--mcp-config` och `--settings`), som bara läser sitt init-besked och avslutas före modellens svar, utan verktygsanrop och utan
  kunduppgifter. Det som inte gäller starten, till exempel underlaget vid en provstart, står för sig som inte prövat.
- **Tilldelad men åtkomst saknas.** En tilldelad tjänst som sessionen inte når står så, med konsekvens och åtgärd,
  aldrig som ok. Den stoppar inte starten, eftersom researchens tjänstesessioner når tjänsterna på en egen väg, men
  kvittot blir begränsat.
- **Upptäckta verktyg.** Varje verktyg som Refero och Mobbin visar har ett beslut i metodkartan (Kompetenserna,
  Tjänsternas verktyg), och kvittot visar det: uppgift, eller ingen uppgift med skälet. Ett verktyg utan beslut står
  som "nytt, obedömt" med åtgärden att pröva det och skriva beslutet, och det begränsar inte kvittot.
- **Rollerna och tillstånden.** Kvittot visar för varje roll i metodkartan det tilldelade och åtkomsten i sessionen,
  i tillståndsorden (metodkartan, Tillståndsorden). Att något är tillgängligt eller provat säger inte att det använts;
  användningen observeras i körningen.

Städningen (`kontroller/stadning.py`) följer städregeln i `BESLUT.md` (tillägget 2026-10-06 om arbetskopior, processer
och cacher). Underhållet kör den först i varje körning och skriver redovisningen i sin rapport (vad, sökväg, storlek
före, tid, utfall och skäl; det som väntar på ägaren med sitt material). Startkontrollens diskvakt kör den före starten
när disken har under 15 % ledigt, och kvittot och underhållets rapport visar ledigt före och efter. Den städar bara när
den körs från huvudutcheckningen (`~/nortropic-repos/nortropic-webb-pro`) eller en av dess worktrees, rör bara kopior
som heter `kopia*`, och allt i en kopia eller worktree som inte går att återskapa ur huvudutcheckningen (också ignorerade
filer som `kirurgen/` och `.env`) väntar på ägaren. En tempkatalog i /tmp och $TMPDIR raderas bara när den är registrerad
som en körnings egen (`korregister.egen_tmp`, ägarfilen `.nwp-agare.json`) och körningen är avslutad. En katalog med
repots prefix men utan registrering redovisas som äldre rest och raderas aldrig. Ingen symlänk följs, och ingen
gemensam förälder raderas. En sessions arbetsyta tas bort först när varje fil i den, oavsett ändelse, är registrerad i
en förteckning eller ett kvitto eller nås från en ref i huvudutcheckningens git (tillägget 2026-10-07). Förra rensningen av npm-cachen står i `underlag/startkontroll/NPM-CACHE.json`. Rökprovet sätter `NWP_STADNING=av`, så att inget prov städar det verkliga
systemet.

Skydden runt en ny version (den oberoende granskningen 2026-10-06):

- **Karenstid:** en version räknas först när den varit publicerad i tre dygn (publiceringstiden hos npm och PyPI,
  Nodes utgivningsdatum, formelns senaste ändring i homebrew-core); förhandsversioner aldrig. En skill prövas i den
  senaste commit i källan som är äldre än karenstiden. Claude Code och Vercel CLI (kvar för sajterna som ligger kvar på Vercel) prövas och tas in med npm:s
  `--before` vid karenstidens gräns (med en timmes marginal: plattformspaketen kommer ibland minuter efter
  huvudpaketet), så att karenstiden också gäller de transitiva beroendena och intaget installerar samma upplösning som
  provet. Utesluter gränsen kandidaten eller ett valfritt plattformspaket behålls versionen tills gränsen passerat det.
  Den senaste inom den installerade huvudversionen är en egen kandidat, så att en avvisad eller behållen huvudversion
  aldrig blockerar patchar.
- **Kandidatens kod** körs med en minimal miljö utan nycklar eller tokens, i provet och vid intaget. Paketen
  installeras utan skript där det går (inte Claude Code, vars skript länkar binären), Python bara ur färdiga hjul, och
  provbyggen, testsajtens installation och Impeccables motor körs innanför processgränsen (`kontroller/processgrans.py`):
  hemligheterna olästa, ingen skrivning i huvudutcheckningen, Homebrew eller skalprofilerna. Rökprovet prövar själv
  processgränsen, och macOS tillåter ingen sandlåda i en sandlåda, så det körs utan den, med egna kopior av `.venv` och
  `node_modules` (provet ändrar inte den delade miljön). Där har kandidatens kod användarens rättigheter; skyddet mot en
  komprometterad version är karenstiden, npm audit och installation utan skript.
- **Skillsen:** en uppdatering som ändrar behörigheter eller krokar i frontmatter, en konfigurationsfil, ett skript
  som flödet kör eller Impeccables motorversion tas aldrig in automatiskt, och inte heller en som flyttar eller bryter
  metodkartans radutdrag (prövas igen vid intaget). Metoden låses inte om över en ändring som aldrig låsts.
- **Fel:** ett nätsteg som faller av ett tillfälligt skäl (tidsgräns, DNS, 5xx, Claudes gränser) avvisar inget,
  utan versionen behålls och prövas igen; en känd sårbarhet är aldrig tillfällig. npm audit jämför advisory för advisory
  med den installerade versionen, för de globala paketen båda träden som de ligger på disk: en uppdatering som inte för in
  någon ny advisory (high eller kritisk) tas in, och de kända står i rapporten (Vercel CLI:s beroenden har kända
  sårbarheter i varje version). Går den installerade inte att granska behålls versionen, med skälet. En avvisning gäller
  provreglerna som gjorde den (`verktygslada.PROVREGLER`): när ett prov rättas för att det dömde fel höjs värdet, och de
  äldre avvisningarna prövas en gång till med raden märkt "prövad igen"; ett godkänt prov görs också om. Faller ett
  intag eller dess incheckning läggs filerna och miljön tillbaka och återställningen prövas (ett globalt paket: det
  installerade trädet sparas som APFS-klon före intaget och läggs tillbaka med binärens länkar, utan en ny upplösning);
  faller en incheckning tre gånger avvisas versionen. Faller en återställning står raden som FEL och rapporten säger att
  miljön kan vara trasig.
- **Körningar på hela maskinen:** ateljéns arbetare, `kor.sh` och `rokprov.sh` anmäler sig i körregistret
  (`kontroller/korregister.py`, `/tmp/nwp-korningar/`). Underhållet tar in en uppdatering i taget under intagslåset och
  prövar körningarna igen under låset. Startkontrollen väntar på ett pågående intag i högst 20 minuter och stoppar annars
  starten. Medan en start väntar avbryts underhållets långa prov efter ett byte på plats, och den förra versionen
  länkas tillbaka.

Slagen och vad som gäller för dem:

| Slag | Var | Prov före intaget |
|---|---|---|
| Claude Code, Vercel CLI | globala npm-paket | provkatalog, npm audit, versionen; Claude: flaggorna, ett strukturerat svar ur den minsta modellen och vaktprovet (kundvaktens mekanik); Vercel: hjälpen, utan ägarens inloggning; en huvudversion också hela rökprovet med kandidaten först i PATH |
| Skillsen | `.claude/skills/<namn>/`, källan i KALLA.md | trevägssammanslagning som bevarar våra anpassningar, inga ändrade behörigheter, krokar eller körda skript, `kontroller/granska_repo.py` utan nya risker, metodkartans radutdrag oförändrade, en kort granskning mot metodkartans Avgöranden, metodkartan och kompetensblocken i en kopia |
| Sajtens paket | `mall/astro/`, `mall/leverans/` (grupper: astro med @astrojs/*, react med react-dom, tailwind med @tailwindcss/vite, cloudflare med wrangler) | installation utan skript, npm audit, rökprovets sajt byggd med mallen och kundrepots bygge förpackat för Cloudflare Workers (`wrangler deploy --dry-run`, utan konto), båda innanför processgränsen; huvudversion också hela rökprovet, där leveransvägens prov kör Workern i workerd |
| Mätinstrumenten | `kontroller/package.json` och Playwrights webbläsare (Chromium, WebKit) | alltid hela rökprovet i en worktree med egna node_modules (utan installationsskript) och webbläsarna; bytet märks i nästa startkvitto, också ett byte utanför underhållet |
| Python-paketen | `requirements.txt` (de vi använder direkt) och `requirements-lock.txt` (alla) | egen venv ur färdiga hjul, pip check, OSV:s sårbarhetsdatabas, regressionsfallen i en worktree med egna kopior av .venv och node_modules; huvudversion hela rökprovet |
| Homebrew | bara node, python@3.12, git och gh, aldrig `brew upgrade` på allt | `brew update` högst en gång per dygn, före versionsuppslagen (ägarens beslut 2026-10-06): bara formelindexet och Homebrew självt, med Homebrews version före och efter i rapporten och startkvittot; `brew upgrade` utan formel spärras i koden. Senaste versionen ur Homebrews API (formulae.brew.sh). Node: senaste LTS (nu 24.x; byggen och verktygen körs i Node, kundsajtens Worker i Cloudflares workerd), installerad bredvid som `node@NN` under intagslåset och prövad med hela rökprovet innan den länkas; pinnar PATH den gamla formeln (ägarens skalprofil, som underhållet aldrig ändrar) behålls bytet med skälet. En formel som byts på plats: flaskans kontrollsumma, verifiering efter uppgraderingen, för en huvudversion (git, gh) hela rökprovet efter bytet, och den förra kegen tillbaka om något faller. Efter varje install och uppgradering prövas de fyra formlernas bibliotekslänkar (`brew linkage --test`, utan att node startas), och det som gått sönder installeras om när det inte byter version; en lagning som skulle byta version utan prov lämnas åt ägaren. En ny node-huvudversion installeras inte bredvid när installationen skulle uppgradera beroenden som den aktiva node delar (2026-10-06 bröt simdjson 5 node@22), och efter installationen prövas att den aktiva node svarar |
| Impeccables motor | `~/.impeccable/bin/<version>/` | den version skillen pinnar, med releasens kontrollsumma och detektering på en provsida |
| macOS, Xcode-verktygen, Homebrew självt | systemet | redovisas bara (lösenord eller omstart) |

Intag i kontrollernas `node_modules` och i `.venv` görs bara i utcheckningen som äger dem (en worktree länkar dem).
Läget (uppslag, prov, avvisade och godkända versioner, ändringslogg) ligger i `underlag/startkontroll/`, utanför git;
körregistret och intagslåset i `/tmp/nwp-korningar/`.

H1:s rättelse använder även ett lokalt, versionsbundet tillägg i `kontroller/webblasare/devtools-lasande/`.
Källverifierat 2026-10-07 mot npm 1.10.1 (gitHead e52c6b59b476c5e04d8dd9fd4bd017ba3b3d65df), dess
[konfigurationsdokumentation](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/e52c6b59b476c5e04d8dd9fd4bd017ba3b3d65df/docs/configuration.md),
[Chromes DNR-regler](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest) och
[Playwrights tilläggsstöd](https://playwright.dev/docs/chrome-extensions). Exakta argument finns i
`kontroller/mcp/chrome-devtools.json` och prövas i `devtools.konfig`; den kortare kommandoraden ovan är inte hela
startkonfigurationen efter rättelsen. `allowedUrlPattern` kräver Chromium 149+. Den låsta versionens startkod
fick `chromeArg` och `ignoreDefaultChromeArg` verifierade läsande; ingen ny MCP-session startades av Codex.
Dagens dokumentation för main är inte ett versionsbevis för 1.10.1.

Den låsta serverns `new_page.isolatedContext` skapar en extra webbläsarkontext som saknar tilläggsskyddet.
Startkommandot går därför genom `.venv/bin/python kontroller/devtools_transport.py` före samma låsta npx-paket.
Vakten kontrollerar verktyg och argument enligt [MCP:s stdio-transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
(läst 2026-10-07); ingen ny extern paketdependency. Provet använder en lokal npx-attrapp, inte verklig MCP-åtkomst.
