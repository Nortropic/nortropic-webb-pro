# Ändringar: webbplatsens ändringsagent och repoväljaren

Fliken Ändringar i portalen (ägarens tillägg 2026-10-11, ordagrant i `BESLUT.md`): Johnny beskriver kundens önskemål i
en riktig Claude Code-terminal, och en agent som är förvaltare av just den webbplatsen gör ändringen i kundrepots
arbetskopia, provar den och redovisar den. Repoväljaren öppnar valfritt kundrepo i organisationen Nortropic i fliken
(ägarens tillägg samma dag). Tillägget ersätter innehållsservice-/CMS-tillägget och dess IN-etapper: de kraven är
ersatta, inte levererade. Metoden agenten följer står i `kunskap/andringsmetod.md`.

Resan: kundens sida eller ⌘O → välj repot → Ändringar → skriv önskemålet (bifoga bilder) → agenten ändrar, provar,
committar och redovisar → förhandsvisa och släpp under Bygge, med Johnnys mandat.

## Webbplatsen, repot och sessionen

- **Bindningen** står i kundens kvitto `kunder/<slug>/KUNDREPO.json`: projekt-id och det bundna fjärrepot. Ett repo
  gissas aldrig ur namnet. `kundrepo.bunden_adress` ger kvittots repo i organisationen, annars namnregelns
  `Nortropic/kund-<slug>`, och förkontrollen (`andringar.forkontroll`) prövar arbetskopians konfigurerade origin
  (`remote.origin.url`, inte `get-url`, som skriver om med gits insteadOf-regler) mot den. Ett hinder stoppar starten;
  en fråga ställs innan något gissas; fakta (gren, HEAD, lokala ändringar, export, förhandsvisning, produktion) står i
  huvudets tekniska detaljer.
- **Arbetskopian** är `kunder/<slug>/kundrepo`, och den privata katalogen `underlag/<slug>/andringar/` hör inte till
  repot.
- **Sessionen**: en levande agent per webbplats, ägd av dashboarden. Att öppna fliken ansluter till den som lever eller
  förbereder en start; ingen agent startar av att vyn öppnas. **Starta** ger en ny session som läser webbplatsens
  kunskap; **Återuppta** fortsätter förra samtalet (`claude --resume` med samma sessions-id ur `SESSION.json`).

## Kunskapen

Agenten är expert genom granskbara filer, inte genom en växande konversation:

- `KUNSKAP.md` i den privata katalogen: de sju områdena (verksamhet och innehåll, struktur, design, teknik och
  funktion, arbets- och provväg, aktuellt läge, mandat), var och en med källa och version. Den första sessionen
  skriver den efter en inventering; senare sessioner läser den och undersöker bara det uppdraget berör.
- `ANDRINGAR.md`: redovisningen av varje ändring (datum, uppdragets ord, ändrat, prövat, kvarstår, commit och
  publiceringsläge). Fliken visar den under Historik, som text.
- `underlag/`: färska kopior vid varje start av `VERKSAMHET.json` och `DESIGNDOMAR.jsonl`, och i `underlag/motorn/`
  motorns regler för en ändring (`andringar.MOTORNS_REGLER`: copy-kontroll, redaktionellt pass, byggstandarden) med
  versionerna i `VERSIONER.json`. Agentens sandlåda kan inte läsa motorns `kunskap/`, så reglerna kommer som kopior.
- Startinstruktionen bär rollen (ägarens §6 ordagrant), mandatet, arbetsloopen, provvägen och commitvägen och
  ändringsmetoden med dess version. Vid varje meddelande säger kroken vad som ändrats i arbetskopian sedan agentens
  förra tur, så att en ny session upptäcker en ändrad struktur i stället för att följa gammal kunskap.
- Inget automatiskt minne (`CLAUDE_CODE_DISABLE_AUTO_MEMORY`): det kundspecifika stannar i den kundens katalog, och
  ingen annan webbplats lär sig det.

## Terminalen

`dashboard/terminal.py` äger en riktig PTY (en enkeltrådad startare gör `setsid` och styrande terminal) och
`dashboard/andringsflik.py` sessionerna. Utdata går som en ström med offset och biljett (EventSource kan inte bära
nyckeln), så att en omladdad flik fortsätter där den var; inmatning, storlek, ta över och stopp är skrivande anrop med
nyckeln eller appens session. Inmatningen ägs av en flik åt gången (klient-id i `sessionStorage`); en annan vy ser
utdata och skriver först efter **Ta inmatningen**. Stoppet är processkontroll: SIGTERM till processgruppen och SIGKILL
efter fristen, och efteråt finns inget skal att skriva i. Tangenterna går till agenten när terminalen har fokus, utom F6
(fokus till flikens knappar) och Skift+F6 (till flikarna), så att terminalen aldrig blir en tangentfälla; Option skriver
tecken (@ [ ] { } | \ på ett svenskt tangentbord), inte Meta. xterm.js 6.0.0 och addon-fit ligger i
`dashboard/vendor/xterm/` med `KALLA.md`, som också redovisar raden som skrivits om för att Mac-appen fryser
`Object.prototype`; terminalens titlar, länkar och utdata är data.

## Behörigheterna, med verklig mekanik

Agenten startas av motorn som `claude --restricted --strict-mcp-config --tools <lista> --settings <json>` i
arbetskopian (`andringar.kommando`, `installningar`). Provat i Claude Code 2.1.290:

- **Sandlådan** för Bash: läsning av motorns repo, andra kunder, `~/.claude`, `~/.ssh` och `~/.config` nekas, bara
  arbetskopian och den privata katalogen är läsbara; inget nät (`deniedDomains: ['*']`; `strictAllowlist` gäller inte
  från `--settings` i den versionen). Skrivning till `.git/hooks`, `.git/config` och motorns poster i den privata
  katalogen (`andringar.MOTORNS`: kontrollernas logg, loggen, sessionen, kontrollerna, underlaget, bilagorna) nekas.
  Mekanismen under sandlådan (Seatbelt) prövar den upplösta sökvägen, så samma fil med andra versaler (`.GIT/config`,
  som APFS inte skiljer från `.git/config`) nekas också; provat med `sandbox-exec` och subpath-, literal- och
  regex-regler 2026-10-11.
- **Behörighetsregler**: git push, remote, reset, stash, rebase, clean, restore, tag, branch -D, config, filter-branch,
  wrangler och gh nekas; `Edit(./.claude/**)` och `Edit(./.git/**)` gäller alla filverktyg och blir sandlådans
  skrivförbud. WebFetch och WebSearch frågar Johnny.
- **Krokarna** (`andringar.krok`, med sessionens token mot dashboarden): kundens lås tas vid meddelandet och släpps vid
  turens slut, också när turen slutar på ett API-fel (`StopFailure`); ett skrivande verktyg utan låset nekas, en
  filskrivning utanför arbetskopian och den privata katalogen, i `.git` eller `.claude` (oavsett versaler), eller i den
  privata katalogen utom `KUNSKAP.md` och `ANDRINGAR.md` nekas. Krokarna stänger hellre än öppnar när dashboarden inte
  svarar.
- **De betrodda kommandona** (`andringar.betrodda`): provvägen (`andringar.py kontrollera <slug> [--sida …]`) och
  commitvägen (`andringar.py committa <slug> -m "Ändring: …" <filer>`) körs utanför sandlådan, utan fråga, och bara när
  hela anropet är ett av dem; en pipe, omdirigering eller kommandosubstitution håller anropet i sandlådan, där motorns
  filer inte går att läsa.
- **Commitvägen**: agentens egna kommandon kan inte skriva i `.git` (sandlådan och förbudet ovan; en smalare regel
  nekades som säkerhetsförsvagning), så motorn lägger till och committar de namngivna filerna och bara dem, med
  `core.hooksPath=/dev/null` och `core.fsmonitor=false` (`andringar.SAKER_GIT`); främmande ändringar står kvar.
  Sökvägarna är bokstavliga (`--literal-pathspecs`): ett mönster eller en katalog nekas, så att inget främmande följer
  med.
- `disableRemoteControl`: terminalen i appen är sessionens enda ingång. Förtroendedialogen för en ny arbetskopia
  besvaras av Johnny i terminalen (förvalt Nej).

Det som inte kan garanteras: andra processer med samma macOS-användare omfattas inte av agentens sandlåda.

## Låset och samtidigheten

Kundens lås är flödets startlås (`flodesstart.las`, `underlag/<slug>/.atelje-start.las`). Dashboarden tar det när
Johnny skickar ett meddelande och håller det tills turen är slut; under tiden startar ingen export, förhandsvisning,
kandidatkörning, kvittering, hämtning eller uppdatering för kunden, och agenten får inte meddelandet om ett annat
arbete håller låset. Håller ett annat arbete låset när meddelandet kommer (oftast kvitteringen efter förra turen)
väntar meddelandet upp till 20 sekunder (`andringsflik.TA_VANTA`) och stoppas sedan med skälet; väntan håller inte
flikens interna lås, så andra webbplatsers krokar och terminaler svarar under tiden. Designstudions skrivlås per
kandidat (`kandidater.skrivlas`) gäller kandidaterna, inte kundrepot.

## Provvägen, kvitteringen och leveransen

- **Provvägen** bygger arbetskopian innanför motorns processgräns (`npm ci --ignore-scripts` när låset ändrats, aldrig
  genom en länkad `node_modules`, `package.json` eller `package-lock.json`) och fotograferar sidan i 390 och 1440 px med
  bedömbarhet, konsol, spill och läckagekontroll; resultatet står i `KONTROLLER.jsonl` för exakt det trädet
  (`andringar.tradtillstand`).
- **Kvitteringen** (`exportera.fran_andring`, automatiskt efter turen eller med **Kvittera ändringen**): ett rent träd,
  en commit som bygger på den senaste exporten, en godkänd kontroll av exakt HEAD:s träd och ingen läcka i historiken
  ger ett exportkvitto med `kalla: andring`, så att förhandsvisningen och releasen under Bygge gäller ändringen som en
  export. Den automatiska kvitteringen pushar aldrig; **Kvittera ändringen** pushar dessutom den kvitterade commiten
  till det bundna fjärrepot (ingen publicering) och visar utfallet. Ett kvitteringsförsök som inte gick står i flikens
  huvud med skälet. Ett klonat repo får ett grundkvitto för den klonade commiten (`kalla: klon`,
  `exportera.fran_klon`), som kvitteringarna bygger vidare på.
- **Exportens skydd** (`exportera.andringar_som_skrivs_over`): en senare export eller ett helbygge stoppas, utan
  kvitto, när kundrepot har något som inte är committat, eller när en commit efter exporten ändrat en fil som exporten
  tar ur sajten (`src/`, `public/`, `astro.config.mjs`, `tsconfig.json`, `DESIGN.md`) och den nya exporten skulle ge den
  ett annat innehåll. Filer som exporten själv skriver (`CLAUDE.md`, README, paketen, Workern, `wrangler.jsonc`,
  `public/_headers`, `src/verifiering.json` och de andra i `exportera.fran_sajten`) skrivs över, och kvittot listar dem
  (`genererade_skrivs_over`). **Ta in ändringarna i sajten** tar kundrepots ändringar till sajten under låset, också en
  sida som exporten lade till och sajten saknar (funktionssidorna), och redovisar konflikter, genererade filer och det
  som redan är intaget.
- Publicering sker bara genom releasevägen under Bygge, med Johnnys mandat. En push som driftsätter produktion är en
  publicering.

## Repoväljaren

Öppnas med **Öppna kundrepo** i Ändringar och på kundens sida, eller ⌘O (Ctrl+Alt+O utanför Mac); genvägen fångas före
terminalen och når aldrig agenten. `dashboard/repovaljare.py` är motorn, `dashboard/repovaljare.js` vyn.

- **Listan**: först Senast öppnade, sedan organisationens kundrepon (gh som det är inloggat; `kund-<namn>` eller
  projektets markör i beskrivningen; främmande organisationer, motorns egna repon, förhandsvisningar och arkiverade
  syns inte). Varje rad: repo, kund, arbetskopia, gren och läge (i takt, efter, före, isär, lokala ändringar, ej
  hämtat), senaste push. Sökningen bortser från skiftläge och diakritiska tecken och markerar träffarna.
- **Bindningen**: ett repo är kopplat när en kunds kvitto binder det (adressen eller projekt-id i repots markör). Ett
  kopplat repo öppnas aldrig som en annan kund. Ett okopplat repo med markör kopplas med ett aktivt val bland befintliga
  kunder utan kvitto och utan arbetskopia (ett namnförslag visas men ska bekräftas); ett repo utan markör binds inte
  (samma regel som `kundrepo.fjarr_skapa`); en fiktiv verksamhet får aldrig ett fjärrepo. Ny kund går genom det
  vanliga flödet.
- **Klonen** efter bekräftelse: `gh repo clone` till `kunder/<slug>/kundrepo` under kundens lås, origin prövad mot
  repot, kvittot uppdaterat (`arbetskopia`), grundkvittot för den klonade commiten skrivet och förkontrollen körd.
- **Hämta** är `git fetch origin` med gh som inloggningshjälp och läget före och efter; **Uppdatera** är bara
  fast-forward till `origin/<standardgren>`, på en ren arbetskopia på standardgrenen, under kundens lås. Lokala
  ändringar och egna commits står kvar; vid isär läge uppdateras inget. Andra grenar visas men byts inte till.
- **Byte medan en agent lever**: väljaren frågar först. Stoppa ger processkontroll (väljaren väntar tills processen
  har slutat); Låt den arbeta låter den fortsätta i sitt eget repo. Två skrivare på samma repo uppstår inte: en session
  per webbplats, och ett repo binds till en kund.
- **Inloggningen**: saknas, gått ut, saknar `read:org`, SAML eller nätfel ger ett besked med åtgärden (till exempel
  `gh auth login` i Terminal), och det gör också en tom lista från en inloggning som inte ser organisationen. En
  organisation som syns men inte har några kundrepon än säger just det, utan att peka på inloggningen. Appen frågar
  aldrig efter en token, och arbetskopiorna ur kvittona står i listan och går att öppna ändå.
- **Senast öppnade** står i `underlag/repovaljaren/SENAST.json` (högst tolv, senast först, utan dubbletter) och överlever
  en omstart; en agentstart räknas också.

**Ur VS Code** (studerat i källkoden, microsoft/vscode eef761e; ingen kod lånad): Quick Picks form (etikett,
beskrivning, detaljrad, grupper), tangenterna (pilarna går runt, PageUp/PageDown, Ctrl+Home/End, Enter, Esc), fokus
kvar i sökrutan med `aria-activedescendant`, ett uppläst antal träffar och fokus tillbaka vid stängning; Open Recents
senast-först utan dubbletter; Source Controls läge som bara är så färskt som senaste hämtningen och ingen
automatisk hämtning (`git.autofetch` är av som standard). **Valdes bort:** mappväljaren och frågan efter klonen
(platsen är bestämd), en tokenruta (VS Code har ingen för github.com heller), GitHub-sökningen över alla repon,
Sync, pull med sammanfogning eller rebase (VS Code har ingen ren fast-forward-inställning; här är uppdatering alltid
`--ff-only`), grenbyte och Workspace Trusts dialoger: arbetskopian under `kunder/` är betrodd av konstruktion, och
Claude Codes egen förtroendedialog plus restricted-läget och sandlådan står för begränsningen.

## Proven

| Prov | Vad | Hur |
|---|---|---|
| `kontroller/rokprov/revision/prov_andringar.py` | förkontrollen, startvägen och inställningarna, krokarnas sökvägskontroll (också versaler), PTY med provagenten, låset via krokarna och väntan på kundens lås, HTTP-vägarna och strömmen, kvitteringen och att bara den manuella pushar, exportens skydd och intaget (funktionssidor, redan intaget), commitvägen (krokar och fsmonitor körs aldrig, bokstavliga sökvägar), kvittot fryser inte en länk ut, provvägen med riktigt bygge och utan installation genom en länk | i rökprovet |
| `…/prov_andringar_webb.py` | fliken i Chromium med provagenten: svenska tecken, inklistring, storlek, Ctrl+C, omladdning, två vyer, bilagor, stopp, axe och spill | i rökprovet |
| `…/prov_andringar_webb.py` med `NWP_ANDRINGAR_VERKLIGT=1` | en riktig Claude Code-session: text och bild, en följdfråga, en extern strukturändring och en helt ny session som hittar den nya källan; commit, kunskap och kvitto prövas | för hand; kostar modellanrop |
| `…/prov_repovaljaren.py` | listan med provets gh, klonen med grundkvittot och en kvittering ovanpå, bindningen, hämta och uppdatera bara framåt, inloggningen och en tom lista, Senast öppnade efter omstart | i rökprovet |
| `…/prov_repovaljaren_webb.py` | väljaren i Chromium: knappen och ⌘O från terminalen, sökning och tangentbord, axe och spill, byte under levande agent (båda vägarna), klon, koppling, utgången inloggning, hämta och uppdatera, ny serverinstans | i rökprovet |
| `desktop/prov/prov_repovaljaren_app.py` | väljaren i den riktiga appen (provbygget) mot en provinstans: lista, ⌘O med verklig tangent, klon med appens session, byte med stopp, utgången inloggning | för hand på en Mac |

Provets gh (`kontroller/rokprov/repovaljaren/fejkgh.py`) och lokala nakna repon nådda genom insteadOf
(`repovaljare_fixtur.py`) gör att riktiga GitHub aldrig nås i proven.

## Begränsningar

- Grenbyte ingår inte (ägarens val); en arbetskopia på en annan gren visas, men uppdateras inte.
- Workspace Trust i Claude Code: en ny arbetskopia får förtroendedialogen en gång, och Johnny svarar i terminalen.
- Agentens sandlåda omfattar inte andra processer med samma macOS-användare.
- En kvittering kräver att provvägen godkänt exakt den commit som ska bli leverabel; en commit som ändrats efter
  kontrollen kvitteras inte förrän provvägen körts igen.
