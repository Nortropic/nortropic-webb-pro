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
| motion | 14.0.0 | MIT | rörelse i ett `<script>` | `motion/mini`: 3,3 kB; hela `motion`: 19 kB |

Granskningen 2026-10-05: 336 paket i låset, `npm audit` 0 sårbarheter, installationsskript bara i esbuild och fsevents
(fanns redan genom Astro och Vite), licenserna MIT, Apache-2.0, BSD, ISC, 0BSD, BlueOak, CC0, MPL-2.0 (lightningcss)
och LGPL-3.0 (sharps libvips). Provbygget av en sida med Tailwind, en React-ö och Motion gav inga konsolfel och inga
CSP-överträdelser (Astros CSP hashar öns skript); en sida utan dem fick inga skript.

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
  `prefers-reduced-motion` respekterat; hela `motion` (scroll, inView, fjädrar) när rörelsen kräver det.
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
  behållet med skäl, aldrig som uppdaterat.

Skydden runt en ny version (den oberoende granskningen 2026-10-06):

- **Karenstid:** en version räknas först när den varit publicerad i tre dygn (publiceringstiden hos npm och PyPI,
  Nodes utgivningsdatum, formelns senaste ändring i homebrew-core); förhandsversioner aldrig. En skill prövas i den
  senaste commit i källan som är äldre än karenstiden. Den senaste inom den installerade huvudversionen är en egen
  kandidat, så att en avvisad eller behållen huvudversion aldrig blockerar patchar.
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
  utan versionen behålls och prövas igen; en känd sårbarhet är aldrig tillfällig. Faller ett intag eller dess
  incheckning läggs filerna och miljön tillbaka och återställningen prövas; faller en incheckning tre gånger avvisas
  versionen. Faller en återställning står raden som FEL och rapporten säger att miljön kan vara trasig.
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
| Sajtens paket | `mall/astro/`, `mall/leverans/` (grupper: astro med @astrojs/*, react med react-dom, tailwind med @tailwindcss/vite) | installation utan skript, npm audit, rökprovets sajt byggd med mallen och kundrepots bygge med Vercel-adaptern, båda innanför processgränsen; huvudversion också hela rökprovet |
| Mätinstrumenten | `kontroller/package.json` och Playwrights webbläsare (Chromium, WebKit) | alltid hela rökprovet i en worktree med egna node_modules (utan installationsskript) och webbläsarna; bytet märks i nästa startkvitto, också ett byte utanför underhållet |
| Python-paketen | `requirements.txt` (de vi använder direkt) och `requirements-lock.txt` (alla) | egen venv ur färdiga hjul, pip check, OSV:s sårbarhetsdatabas, regressionsfallen i en worktree med egna kopior av .venv och node_modules; huvudversion hela rökprovet |
| Homebrew | bara node, python@3.12, git och gh, aldrig `brew upgrade` på allt | Senaste versionen ur Homebrews API (formulae.brew.sh); finns den inte i det lokala formelindexet redovisas att `brew update` behövs, eftersom den uppdaterar Homebrew självt. Node: senaste LTS som Vercel stöder (nu 24.x), installerad bredvid som `node@NN` under intagslåset och prövad med hela rökprovet innan den länkas; pinnar PATH den gamla formeln (ägarens skalprofil, som underhållet aldrig ändrar) behålls bytet med skälet. En formel som byts på plats: flaskans kontrollsumma, verifiering efter uppgraderingen, för en huvudversion (git, gh) hela rökprovet efter bytet, och den förra kegen tillbaka om något faller. Efter varje install och uppgradering prövas de fyra formlernas bibliotekslänkar (`brew linkage --test`), och det som gått sönder installeras om |
| Impeccables motor | `~/.impeccable/bin/<version>/` | den version skillen pinnar, med releasens kontrollsumma och detektering på en provsida |
| macOS, Xcode-verktygen, Homebrew självt | systemet | redovisas bara (lösenord eller omstart) |

Intag i kontrollernas `node_modules` och i `.venv` görs bara i utcheckningen som äger dem (en worktree länkar dem).
Läget (uppslag, prov, avvisade och godkända versioner, ändringslogg) ligger i `underlag/startkontroll/`, utanför git;
körregistret och intagslåset i `/tmp/nwp-korningar/`.
