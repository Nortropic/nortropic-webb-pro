# Designfasen i Claude Design

Ägarens uppdrag 2026-10-12 (ordagrant i `underlag/uppdrag/PROMPT-Nortropic-Claude-Design-konvertering-20261012.md`,
tillägget om best practice samma dag i `…-tillagg-best-practice-2026-20261012.md`; sammanfattat i `BESLUT.md`):
formgivningen görs i Claude Design, från kundförståelse och referenser till riktningar, återkoppling, förfining och
godkänd design; därefter tar Claude Code över helbygget och verifierar leveransen. Nortropics metoder, litteratur,
skills, tjänster och specialistkompetenser har uppgifter genom hela designarbetet (placeringen:
`kunskap/metodkarta.md`, Designfasen i Claude Design). Verktyget är `kontroller/designfas.py`; utförarens instruktion är
skillen `designfas`.

## Målmiljön

Claude Design finns i fyra former (supportsidan Get started with Claude Design, läst 2026-10-12): som Design-typ i
Claude-konversationer och artefaktfliken, i Claude Code (`/design` och Artifact-verktyget), i mobilapparna, och som
fristående claude.ai/design, som **stängs 2026-12-14**. Vi använder **Design-typen driven från Claude Code**: en duk
(artefakt på claude.ai, privat) som en interaktiv Claude Code-session i repots rot skapar och skriver, och som ägaren
öppnar i webbläsaren för att se, jämföra, spela upp, kommentera, redigera och exportera.

| Egenskap | Prövat | Utfall |
|---|---|---|
| Skapa en duk och skriva ritningar (Design-typen, release 1791701246-7422) | provduken 2026-10-12 | fungerar: en flytande sida med tillstånd (meny) publicerad som version 2 med versions-id |
| Ladda upp kundens bild som tillgång | samma | fungerar: `/_blob/<id>`, sha256 i svaret |
| Läsa tillbaka dukens filer | samma | samma sha256 som publicerat; underlag för versionerna och överlämningen |
| Bevakning och kommentarer till utföraren | samma | bevakningen ansluten med automatiska svar; att ägarens "Send to Claude" når sessionen är **oprövat** (kräver ägarens hand) |
| Lokal rendering av ritningen med typens körmiljö (`dc-runtime.js`) | samma | fungerar i 390, 768, 1440 och med menyn öppen; bilderna är ritningens källa i Chromium, inte skärmbilder ur Designs gränssnitt |
| Duken i ägarens webbläsare | Chrome, 2026-10-12 | renderas med Play, export, kommentarer, Translate och Chat |
| Chat-knappen (öppnar duken i en Claude-konversation) | samma | ledde till en inloggningssida i den Chrome-profilen; **oprövad** vidare |
| Huvudlös session (`claude -p`) som utförare | 2026-10-12, med `enableArtifact` | **nej**: Artifact-verktyget finns inte i `-p`; flödets automatiska sessioner kan inte skriva duken |
| Interaktiv session i repots rot | 2026-10-12, transkript | Artifact-verktyget och repots skills (taste) finns |
| `/design` i repot | 2026-10-12, sessionens kommandolista | skuggas av repots skill `design` (bildgenererande); utföraren skapar duken med Artifact-verktyget och typens adress |
| Designsystem | Design System-typen finns för kontot; inga system ännu | se Designsystemet nedan |

Varför inte de andra: den fristående upphör; i en Claude-konversation når Claude varken repots skills (de måste laddas
upp som paket och kräver kodkörning), de lokala verktygen (Playwright, axe, referensfångsten, kundvakten) eller kundens
privata underlag, och Code kan inte observera vad som aktiverades där. Refero, Mobbin och 21st är fjärrservrar och
skulle kunna bli egna anslutningar i claude.ai (statisk nyckel i huvudet), men utan kundvakten; det är inte infört.
Konversationsvägen kan bli en kompletterande väg för ägarens egen utforskning; den är inte utföraren och inte prövad.

## Ansvarsfördelningen

- **Ägaren** arbetar på duken: ser, jämför, spelar upp, kommenterar (Send to Claude), redigerar direkt och väljer.
  Ägaren godkänner en exakt version, startar bygget och beslutar om publicering: tre skilda beslut.
- **Utföraren**, den utsedda och enda som skriver dukens versioner: en interaktiv Claude Code-session i repots rot,
  startad av ägaren med `./design.sh <slug>`. Den har repots skills (Skill-verktyget), Refero, Mobbin, 21st och Motion
  bakom kundvakten (`--strict-mcp-config`), och nekas designgodkännandet.
- **Code** (flödets steg, specialistpassen och de lokala verktygen) gör research, material, specialistbedömningar och
  kontroller och lämnar underlag och förslag. När designfasen är aktiv (`underlag/<slug>/design/DESIGNFAS.json`)
  stannar kandidatflödet efter researchen (`steg forskad`), och ateljén nekar skiss, förfining och uppdrag i Code: ingen
  konkurrerande kunddesign.

## Stegen

| Steg | Vem och hur | Resultat |
|---|---|---|
| D1–D2 Kundunderlag och kundförståelse | Code: `prototyp.py <slug> --forbered` | KUNDFORSTAELSE.md, BRIEF.md, TEXTUNDERLAG.md med flera |
| D3 Research i tre perspektiv (bransch, visuell inspiration, implementationsgrund) | Code: `designfas.py ny <slug>` och sedan `prototyp.py <slug>` (eller `NWP_KANDIDAT_STOPP_EFTER=forskning`); stannar efter researchen | FORSKNING.md, referenspaketet, tjänsternas svar och bilder |
| D4 Underlaget på duken | utföraren | dukens sida Underlag: besökarnas uppgifter, det som bara verksamheten har, referenserna med bild och skäl |
| D5 Riktningarna | utföraren; en representativ riktning först, sedan omkring tio | en ritning per riktning med anteckning; versioner med bilder och kontroller |
| D6 Granskning före valet | utföraren efter renderingen; Code: kontrollerna och specialistpassen (kritik, jämförelse) | fynd före och efter; falsk variation utpekad |
| D7 Ägarens val | ägaren på duken | ägarens ord ordagrant i versionens orsak |
| D8 Förfining | utföraren med beställningar | nya versioner med bedömning före och efter |
| D9 Designgodkännande | **ägaren**: `! .venv/bin/python kontroller/designfas.py godkann <slug> <v> --ritning <fil>` | domloggen (källa ägaren, beslut godkand) och GODKANNANDE.json, bundna till versionens filer och bilder |
| D10 Överlämning och kundens designsystem | utföraren: `designfas.py overlamna <slug>`, DESIGN.md i paketet, Design System-artefakten | `design/overlamning/<v>/`; `overlamna --prova` utan brister |
| D11 Helbygge, verifiering, leverans | ägaren startar `./kor.sh <slug> "<verksamhet>"`; publicering enligt `kunskap/lansering.md` | sajten implementerad efter förlagan; provet jämför med förlagans bilder |

## Duken

Dukens sidor: **Underlag** (research och referenser, så att ägaren ser grunden), **Riktningar** (omkring tio, sida
vid sida i samma bredd) och **Förfining** (den valda, med tillstånden som interaktiva ritningar). Varje riktning har en
anteckning: idén, förebilden och de egenskaper den prövar att föra över, implementationsgrunden, besökarens uppgift och
primära handling, och antagandena. Ritningarna är sidor (`expand: "fill"`), flytande från 390 till 1440, med riktiga
knappar, länkar och fält. Motiveringar står i anteckningarna och i svaren, aldrig i själva ritningen.

## Versioner och observation

Varje publicering ger dukens versions-id. Utföraren läser tillbaka filerna och sparar versionen: `designfas.py version`
kopierar ritningarna och indexet oförändrade till `underlag/<slug>/design/versioner/vNN/`, hashar dem, och renderar dem
lokalt med typens körmiljö (`kontroller/designfas/rendera.mjs`): bilder i 390, 768 och 1440 och med menyn öppen, och
mätningarna i BILDER.json (LCP-kandidaten, layoutskiften, bildernas storlek mot visad storlek, rörelsen vid laddningen,
efter 5,5 s och med reducerad rörelse), axe med menyn öppen och formulären skickade tomma, och stilrapporten. Varningarna
är underlag; LCP och CLS gäller ritningen lokalt, aldrig fältdata. Ägarens egna ändringar på duken sparas som en egen
version (`--av agaren`) innan utföraren ändrar något. Designs gränssnitt har ännu ingen versionshistorik
(supportsidan); spåret i `design/` är därför versionshistoriken, och den äldre versionen kan alltid visas och väljas.

Code ser dukens filer (genom återläsningen), renderingen och sessionernas transkript, inte Designs gränssnitt: inte vad
ägaren tittat på, inte osparade redigeringar. Utförarens redovisning är utförarens egen och märks så. Redovisningen
skiljer fem nivåer: teknisk tillgång (verktyget eller tjänsten finns), aktivering och läsning (kvittot ur
transkriptet), verktygsanvändning (anrop med resultat), belagd tillämpning (versionen ändrades och står kvar, med bild
före och efter) och bedömd kvalitet (ägaren, eller en oberoende granskning märkt som AI-bedömning). AI-bedömning,
ägarens smakdom och användarprov är olika belägg och ersätter aldrig varandra.

## Beställningar och specialistpass

En specialistinsats som kräver den lokala verktygslådan: `designfas.py bestall <slug> --typ <typ> --version <v>
--ritning <fil> --uppgift "…"` ger B00N med projekt, duk, version, ritning, uppgift och material. `designfas.py
specialist <slug> B00N` kör den som ett pass i repot (`claude -p` genom `atelje.session`: rollens kompetensblock ur
metodkartan, kundvakten, tjänsterna, svaret i schemat och kvittot ur transkriptet), och svaret står i
`svar/B00N/SVAR.md` med fynd, förslag, referenser (tjänsternas bilder hämtade från deras egna bildvärdar) och
begränsningar. Utföraren för in det som bär i nästa version (`version --bestallning B00N`) och skriver bedömningen
(`designfas.py infor`). Typerna och passen: referenser (ds_research, rollen forska, med webben), komponent
(ds_komponent, 21st), typografi, innehall, responsiv, rorelse, granskning (t.ex. ett formulär), kritik (bilderna och
briefen, aldrig källan eller utförarens text), bild (bildurval och bildregi) och jamforelse (falsk variation).
Parallella pass lämnar underlag utan att skriva över varandra; bara utföraren ändrar duken. Ett svar som tagits fram
på annat sätt förs in som manuell överlämning (`designfas.py svar … --utforare "…"`) och märks så.

**Den kritiska granskaren.** ds_kritik kan köras med Fable 5.1 på max (`designfas.py specialist <slug> B00N --modell
claude-fable-5-1`; standardmodellen och ansträngningen är ateljéns) på betydande versioner. Den bedömer mot
kvalitetskraven och standarden och, när ägaren gett den, ägarens måttstock ur "Visa mig nivån"
(`underlag/niva/MATTSTOCK.md`). Dess dom är en AI-bedömning, märkt så, och ändrar aldrig designen av sig själv.

## Designsystemet

Fyra lager (Brad Frost, The many faces of themeable design systems): Nortropics arbetsmetod och kvalitetskrav
(`kunskap/`, gemensamt för alla), återanvändbara komponentbeteenden (designsystemet "Nortropic komponentbeteenden":
tillstånd, fokus, felbesked, menyns beteende och klickytor ur standarderna, neutralt i uttryck och aldrig ett utseende
som läggs på en kund), kundens visuella identitet (ett eget designsystem per kund med Design System-typen) och sidans
komposition (duken). En kund med etablerad identitet börjar med sitt designsystem ur sina verkliga källor (logotyp,
färger, typsnitt, material); en kund utan börjar med riktningarna, och den godkända riktningen formaliseras efter
godkännandet till kundens designsystem: README, tokens (färgroller, typskala, typsnitt, mellanrum, radier), komponenter
med förhandsvisning och tillstånd, bildprinciper och responsiva regler. Underkända tidigare Nortropic-byggen blir aldrig
norm (`kunskap/ren-designstart.md`).

## Godkännandet och överlämningen

Ägaren godkänner en exakt version och ritning med sitt eget kommando; sessionerna nekas det (projektets inställningar
och `design.sh`). Godkännandet skrivs i domloggen och i `design/GODKANNANDE.json`, bundet till versionens filer och
bilder och till underlagets version. `designfas.py overlamna` skriver paketet i `design/overlamning/<v>/`: ritningarna
(prototypkoden i Designs format), jämförelsebilderna, kontrollerna, tillgångarna med ursprung och en DESIGN.md som
utföraren fyller i ur versionen: designvärden, komponenter, responsiva regler, interaktionstillstånd och beteenden,
innehåll, bilder och typsnitt med ursprung, prototypkod som kan återanvändas, öppna frågor och det som endast är
simulerat. `overlamna --prova` fäller ett tomt avsnitt, en saknad bild och en tillgång utan ursprung. kor.sh tar vid
bara när godkännandet gäller (`designfas.godkand_giltig`: senaste ägarbeslutet, oförändrade filer och bilder,
oförändrat underlag, komplett paket) och fryser `design/` för bygget. Bygget implementerar förlagan i Astro (bygg-sajt
steg 5, En godkänd design ur Claude Design); provet jämför startsidan med förlagans bilder i 390, 768 och 1440 och med
menyn öppen (`prov/designforlaga/DESIGNJAMFORELSE.md`; förändring, inte kvalitet). En betydande designändring blir ett
nytt beslut och en ny version på duken. En klickbar prototyp eller en grön kodkontroll är inte ett leveransgodkännande.

## Datagränser

Dukarna är privata artefakter på claude.ai (Anthropics infrastruktur, samma leverantör som Claude Code). Det fiktiva
fallet bär inga verkliga uppgifter. För en verklig kund lägger dukarna kundens texter och bilder där; det är ett beslut
för ägaren innan första verkliga kunden, och ingen duk delas eller publiceras av flödet. Externa designtjänster får
bara generiska frågor (kundvakten). Inget publiceras som bieffekt.

## Begränsningar och oprövat

- Att ägarens kommentar med Send to Claude når utförarsessionen, Chat-knappens konversationsväg, export från gränssnittet
  och Remote Control från telefonen är oprövade.
- Utföraren måste vara en interaktiv session; den startar inte av sig själv och tar bara emot kommentarer medan den lever.
- Att `!`-prefixet i sessionen kör godkännandet trots att sessionen nekas kommandot är oprövat; annars körs det i en egen terminal.
- Den lokala renderingen visar ritningens källa med typens körmiljö i en vanlig webbläsarvy, inte Designs ram; små
  skillnader mot duken är möjliga.
- Designs samredigering är enligt supportsidan ännu enkel; en utförare per duk.
- Kundens designsystem och komponentbeteendesystemet är beskrivna här; vad som är byggt står i slutrapporten.

## Så använder du flödet

1. Kundunderlaget: `.venv/bin/python kontroller/prototyp.py <slug> --forbered` (eller Byggflöde i portalen).
2. Starta designfasen och researchen: `.venv/bin/python kontroller/designfas.py ny <slug>` och
   `.venv/bin/python kontroller/prototyp.py <slug>` (stannar efter researchen).
3. Starta utföraren: `./design.sh <slug>`. Den skapar duken (eller öppnar den som finns) och ger dig länken.
4. Arbeta på duken: titta, spela upp, kommentera (Send to Claude) eller skriv i sessionen. Be om specialistinsatser
   med vanliga ord ("bättre referenser för mobilmenyn", "en komponent från 21st för tjänstelistan").
5. Godkänn en exakt version: `! .venv/bin/python kontroller/designfas.py godkann <slug> <v> --ritning <fil>`.
6. Låt utföraren skriva överlämningen; `designfas.py overlamna <slug> --prova` ska vara utan brister.
7. Starta bygget när du vill: `./kor.sh <slug> "<verksamhet>"`. Publiceringen är ett eget beslut.
