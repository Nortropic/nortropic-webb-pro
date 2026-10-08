# nortropic-webb-pro

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg, med Claude Code som utförare och ägaren som
domare. Varför repot finns och vad som beslutades: `BESLUT.md`.

## Dashboarden

```sh
./dashboard.sh        # http://127.0.0.1:4771 (öppnar sidan med dashboardnyckeln: ägarens domar och flödets handlingar
                      # skrivs bara av ett anrop med nyckeln, som ingen annan lokal process har; dashboard/server.py NYCKEL)
```

Allt på ett ställe: vyn Prototyp, där du väljer bland förslagen och godkänner en startsida (besluten skrivs i
domloggen `underlag/<slug>/DESIGNDOMAR.jsonl`), byggena (steg, grindar, före och efter, skärmbilder, rapport, underlag,
körningens händelser), frågeformuläret där du dömer ett bygge, Starta, de blinda jämförelserna, kalibreringen,
designprovet, backloggen, kirurgen (klistra in en länk) och lärdomarna. Vyn Dokumentation och rapporter börjar med en
sammanfattning och visar sedan hur Nortropic fungerar, pågående uppdrag, granskningarna och besluten, lästa ur de platser
som avsnittet Var information finns anger.

## Tre loopar och en backlog

| Loop | Vad | Var |
|---|---|---|
| 1. Inne i ett bygge | kontrollera, rätta, kör igen tills grönt och granskaren godkänner | `kontroller/prova.py`, `kontroller/granska.py`, stoppvakten i `.claude/hooks/` |
| 2. Genom stegen | upptäckt, definition, innehåll, design, bygge, prov, rapport | skillen `bygg-sajt` |
| 3. Mellan byggen | ägarens dom blir en textändring | frågeformuläret, `LARDOMAR.md`, backloggen |

**Backloggen** (`backlog/`) fylls automatiskt med vilande poster: kirurgens "ta in" och "prova", ägarens domar och
brister som byggena hittar i verktygen. Inget genomförs av sig självt. Starta en Claude Code-session i repot och säg
**"implementera enligt backlog"**.

## Kedjan från kundunderlag till leverans

Formulärens mottagning vid export beskrivs i `kunskap/forfragan.md`: bevarade textfält vid valideringsfel,
lagringskvitto före mejl och separata mottagningsbesked. Den lokalt prövade felhanteringen innebär ingen
verifierad extern tjänsteåtkomst; en tappad första framgångskvittens kan fortfarande orsaka dubbletter (mottagen-sidan
är förrenderad och nås med 303, så en omladdning där skickar inget). Utanför produktionen skickar mottagaren aldrig något.

Den här tabellen är grundkällan för vem som startar vad, med vilket kommando. Kommandona körs från repots rot.
Designflödet i detalj: `kunskap/skapandeflodet.md`; helbygget: skillen `bygg-sajt`; exporten och leveransen:
`kunskap/lansering.md`. Inget bygge har lanserats än.

| Steg | Vem startar, med vilket kommando | Resultat | Saknas i dag |
|---|---|---|---|
| 1. Kundunderlaget: verifierade fakta, research, brief och textutkast | Flöde → Förbered kundunderlaget, eller `.venv/bin/python kontroller/prototyp.py <slug> --forbered`; kräver VERKSAMHET.json och kunduppdrag eller befintlig research | privat förslagspaket, RESEARCH.md, BRIEF.md, TEXTUNDERLAG.md, BESTALLNING.md och versionsbundet FORBEREDELSE.json; inget webbprojekt behövs före steget | Kundstart och verklig modellkörning verifieras separat |
| 2. Prototypen: research, plan och cirka tio skisser | ägaren eller en session i terminalen: `.venv/bin/python kontroller/prototyp.py <slug>` (läget följer domloggen) | förslagen i vyn Prototyp; researchens referenspaket `underlag/<slug>/referenser/paket-vNN/` med, per fångad sida, det kuraterade underlaget `SEKTIONER.md` (bild, mått, typsnitt, regler, utdrag) och hela mätningen `EXTRAKT.md` (`kunskap/referensjakt.md`, Underlaget per sida); för huvudreferensen kan en DevTools-profil tas med `.venv/bin/python kontroller/devtools.py <slug> --adress https://värd/` (en egen inspektionssession) | DevTools-profilen startas för hand: prototyp.py tar den inte själv |
| 3. Ägarens val | ägaren i vyn Prototyp; en dom som kommit på annat sätt förs in med `.venv/bin/python kontroller/skapande.py dom` | en dom i domloggen, bunden till kandidat och version | valet startar inget arbete; nästa tillåtna handling visas i Flöde |
| 4. Förfiningen av de valda | Flöde → Förfina de valda förslagen, eller `prototyp.py <slug>` igen (läget valda) | förfinade kandidater med DESIGN.md | – |
| 5. Godkännandet | ägaren i vyn Prototyp: en förfinad kandidat godkänd för helbygge | `underlag/<slug>/atelje/vinnare/` och VINNARE.json | startar inget bygge; nästa handling finns i Flöde |
| 6. Helbygget | Flöde → Starta helbygget, `prototyp.py <slug> --helbygge --start-id <id>`, eller `./kor.sh <slug> "<verksamhet>"`; aktuell godkänd startsida krävs, och godkännandets underlag (steg 1–4) är fryst under bygget; finns Kundstarts ärendelager krävs sandlådan (`NWP_SANDLADA=pa ./dashboard.sh`), och Flöde visar startmiljön och nekar vid knappen i stället för i kor.sh | sajt, prov, granskning, RAPPORT.md, FRAGOR.json och SLUT.json per körning; Flöde visar slutpostens fem separata besked | verklig modellkörning genom den nya flödesingången återstår |
| 7. Ägarens dom över bygget | ägaren i dashboarden: bygget, fliken Din dom | `kunder/<slug>/DOM.json`, lärdomarna och en backlogpost | – |
| 8. Exporten till kundrepo | Flöde → Exportera till kundrepot, `prototyp.py <slug> --exportera --start-id <id>`, eller `exportera.py <slug> [--git]`; kundrepot (`kunder/<slug>/kundrepo`, ett eget git-repo med kort CLAUDE.md) skapas av `kontroller/kundrepo.py` när sajten skapas, och en verklig verksamhet får det privata `Nortropic/kund-<slug>` | en commit i kundrepot per export (pushad när fjärrepot är bundet), byggprov och privat EXPORT.json per export med käll- och exporthash, commit och godkännandenas omfattning; identiteten i `kunder/<slug>/KUNDREPO.json`; tidigare export bevaras i git | en testexport får göras utan godkännande, men är aldrig i sig en kundklar leverans; en fiktiv verksamhet får aldrig ett fjärrepo; extern publicering återstår |
| 9. Leveransen: förhandsvisning, skydd och DNS | Flöde → Förhandsvisa exportens commit, `prototyp.py <slug> --preview --start-id <id>` eller `kundrepo.py <slug> --preview` (Vercels CLI i teamet nortropic, projektet `kund-<slug>`, metadata commit och export); produktion, skyddet och DNS: människa med ägarens ja | privat `kunder/<slug>/leverans/PREVIEW-<tid>.json` med adress, commit, export och status; Flöde visar den | en förhandsvisning är inte produktion; `kontroller/driftkoll.py` prövar en driftsatt adress och skriver bara ut; verklig driftsättning är inte prövad av provet |

Helbygget går obevakat från den godkända startsidan: byggaren bygger resten av sajten i `kunder/<slug>/sajt/`, provar
tills grindarna är gröna och två oberoende granskare godkänt, eller tills taket nås (slutkod 1), och skriver `kunder/<slug>/RAPPORT.md` och sina egna
frågor till dig. Rapporten gäller bara när den skrivits i körningen; ett tidigare bygges rapport flyttas till
`kunder/<slug>/rapporter/` när bygget startar. Körningens slutbesked sparas i slutposten (Var information finns, nedan).
Alternativa lägen och återupptagning: `kunskap/skapandeflodet.md` och `./kor.sh` utan argument.
Råmaterial (`underlag/`) och byggen (`kunder/`) ligger utanför git.

**Handlingarna i Flöde** använder `prototyp.py` och ateljéns befintliga arbetare. `--start-id` binder ett osäkert
omförsök till samma beställning; dubbelklick, omladdning och nytt HTTP-försök startar inte samma arbete två gånger.
Läsning och val av kandidat startar inget. Stopp går förbi startlåset. En avbruten körning kan återupptas via samma
ingång. De fem beskeden är sessionsavslut, teknik, designgranskning, ägarens godkännande och leverans inom angiven
omfattning. Saknat, historiskt, dolt och underkänt är skilda lägen. Ingen grön markering betyder mer än sin omfattning.
Även ett äldre ägar-ja visas som historik när dess underlag eller godkända version inte längre gäller.
Ateljéns besked använder helbyggstartens giltighetskontroll; helbyggets besked prövar också aktuell Kundstart-källa.
Läsningen ändrar varken den ursprungliga domen eller den sparade slutposten.

Helbygge och export använder samma startjournal genom `kontroller/flodesstart.py`. Kundens flock-lås följer
arbetaren och helbyggets vakt; direkta CLI-starter prövar samma lås. Stopp begärs med `--stoppa-overgang` och sparas
också före processstart. Arbetaren läser den sparade stoppbegäran under körningen, så stoppet beror inte på att
signalen når den, och stoppet går till arbetets egen process (kor.sh eller exportera.py) också när arbetaren själv
inte lever. Slutkod 4 i journalen betyder att stoppet avbröt arbetet; ett stopp som kom efter att arbetet slutat står
som sent, och arbetets slutkod gäller. Ett start-id vars begäran redan är avslutad svarar med sin slutkod (HTTP 200,
`avslutad`), så fliken släpper det; bara ett okänt eller vägrat start-id ger 409 (GR-20261008-r117-claude, B1–B3). En avbruten reservation får slutkod 4 när låset är fritt; samma start-id körs aldrig igen.
Exportens arbetare följer byggprocessernas identitet och väntar in deras avslut före slutstatus. Den har samma
gräns för mycket kortlivade mellanprocesser som korvakt; att döda även arbetaren kan kräva manuell kontroll.
Startjournalen är ett mottagnings-/processbesked. `SLUT.json`, `EXPORT.json` respektive `PREVIEW-<tid>.json` anger arbetets resultat;
`KUNDREPO.json` kundrepots identitet (projekt-id, fjärrepots status, Vercel-projektet, senaste push).
## Kundstart i det befintliga flödet

Kundens senare ändringar prövas mot den levande källan genom förberedelse, start och godkännandets aktualitet.
En överlämnad snapshot är inte ett permanent godkännande. Helbygge med Kundstarts gemensamma ärendelager kräver
`NWP_SANDLADA=pa`; den privata databasen är inte byggmaterial. Mekanik, felvägar och begränsat syntetiskt
förloppsprov beskrivs i `kunskap/kundstart.md`. Live-AI och verklig designkvalitet är ännu inte verifierade.
Granskningsmetoden binder också `KUNDSTART.json`: en ny överlämning av ändrade kundönskemål gör tidigare domar
historiska även när `VERKSAMHET.json` är oförändrad. Äldre metodhashar gäller inte efter denna metodändring.

Kundstart-fliken i dashboarden hanterar privata ärenden, deltagare, erbjudanden, kompletteringar och
versionsbunden överlämning. Kunden har en separat lokal yta med Samtalet och Ditt uppdrag. Inga modeller,
servrar eller kundbyggen startar vid skapande eller läsning. Körväg, ansvar och bevisgräns:
`kunskap/kundstart.md`; professionen: `kunskap/kundintervju.md`.

Ärende och kö ligger på beständig privat lokal disk i `underlag/kundstart/arenden.sqlite3`. GALLRING.json under
samma rot styr avbruten gallring och återställning; säkerhetskopior ligger under `underlag/kundstart/sakerhetskopior/`.
Kundservern startas uttryckligen med `.venv/bin/python kontroller/kundstart_server.py --port 4773`.
Server-API till AI kräver egen verifierad konfiguration och aktivering. I piloten går intervjun i stället på det lokala
Claude Code-abonnemanget (`kundstart_modell.py --live-cli`, ägarens beslut 2026-10-08), bara för ärenden märkta fiktiva;
ett verkligt ärende kräver server-API.
Ingen sådan drift är aktiverad genom denna gren. Kirurgens observation av överlämningen och avgränsade lokala
försök beskrivs i `kunskap/kirurg-forbattring.md`. Koppling till byggövergångarna prövas separat vid integration.

Ett avgränsat metodförsök kan förberedas med `kontroller/ab.py forbered-skiss <slug> --kandidat k01` när en ensam
skiss är planerad och prövad men ännu inte arbetad. Det startar inget arbete. Medium/high lottas för bara
skisskaparens pass; ägaren ser kandidaterna i den vanliga blinda Prototypvyn. Förutsättningar, körmandat,
återställning och mätgränser finns i `kunskap/autonomi.md`. Något verkligt kvalitetsexperiment är ännu inte verifierat.

Resproven stöder också roll och tillgängligt namn eller etikett, med uttrycklig avgränsning vid flera träffar.
Äldre CSS-resor fungerar fortsatt; användning och begränsningar står i `kunskap/resor.md`. Metodkartan beskriver
hur väntande skillflöden läses i obevakade pass och hur varvkraven följer uppdragets läge. Dessa mekaniska
kontroller är inte bevis för modellens tillämpning eller webbplatsens designkvalitet.

## Var information finns

Tabellen bestämmer var varje slag av information hör hemma (ägarens uppdrag 2026-10-06 om dokumentations- och
rapportstrukturen, `BESLUT.md`). Andra dokument länkar hit i stället för att upprepa den.

| Slag | Plats och namn | Skrivs av |
|---|---|---|
| Start och överblick | den här filen; `CLAUDE.md` för sessioner | agenten |
| Gällande arbetssätt: guider, krav, referens och förklaringar | `kunskap/<ämne>.md`, ett ämne per fil; skills i `.claude/skills/<namn>/SKILL.md`; granskarens kriterier i `kritik/`. En fil som inte gäller fullt ut börjar med raden `Status: historik, ersatt av …` eller `Status: vilande till …` | agenten, i samma commit som beteendet ändras |
| Beslut | `BESLUT.md`: ett `## Tillägg ÅÅÅÅ-MM-DD: <titel>` per beslut (rubriken är beslutets id), med raden `**Status:**` (gäller, delvis ersatt av … eller ersatt av …) direkt under rubriken, och sedan ägarens ord ordagrant, skälen och räckvidden. Ett ersatt beslut ligger kvar och märks. Kundbeslut: `underlag/<slug>/DESIGNDOMAR.jsonl`, med avsändaren på varje rad, och ägarens belägg i efterhand för en rad i bilagan `underlag/<slug>/DESIGNDOMAR-belagg.jsonl` (Avsändarna, nedan) | agenten med ägarens ord |
| Förbättringsarbete | `backlog/B-ÅÅÅÅMMDD-<namn>.md` (`backlog/README.md`). `klar` betyder genomförd och committad; verifierad är posten först när en senare granskning säger det | `kontroller/backlog.py`, agenten |
| Projekt- och körningsrapporter | i flödet där verktygen skriver: `underlag/<slug>/atelje/` och `kunder/<slug>/`; helbyggets slutpost per körning: `kunder/<slug>/korningar/<körning>/SLUT.json` (`kontroller/korslut.py`), och ett tidigare bygges rapport: `kunder/<slug>/rapporter/`; ateljéns slutpost per körning, med körningens STATUS.json och REDOVISNING.md bredvid: `kunder/<slug>/atelje/korningar/<körning>/SLUT.json` (`kontroller/ateljeslut.py`); utanför flödet: `underlag/<uppdrag>/` (som `underlag/figma-pilot/BESLUTSUNDERLAG.md`); lägesrapporter till ägaren: `underlag/rapporter/RAPPORT-ÅÅÅÅ-MM-DD-<namn>.md` | agenten, verktygen |
| Systemgranskningar | `underlag/granskningar/GR-ÅÅÅÅMMDD-<ämne>.md`, en fil per granskning, med bevisen i katalogen `underlag/granskningar/GR-ÅÅÅÅMMDD-<ämne>/`; en omgranskning är en ny fil som anger den föregående, och fynden heter `<rapportens id>#<fynd>`. Äldre rapporter ur sessioners arbetsytor ligger i `underlag/granskningar/sessioner/`. `FORTECKNING.jsonl` har en rad per fil, med ursprung och sha256 | den granskande sessionen |
| Bevismaterial: bilder, mätningar, loggar och kvitton | där verktyget skriver (`prov/`, startkvitton, `VERSION.json`, `bilder/`, `matning/`). Det ägaren bedömt före ett omtag, med bilder, versionens underlag och `KVITTO.json`, ligger i `underlag/<slug>/omtag/<stämpel>/` (BESLUT.md 2026-10-07). Frysta kvitton skrivs aldrig över; ett mätskript som ett kvitto hänvisar till kopieras till uppdragets `matning/` | verktygen |
| Historik och tillfälligt | git-historiken och filer märkta `Status: historik`. Tillfälliga anteckningar i sessionens arbetsyta och `/tmp` gallras (städregeln, `BESLUT.md`); det som en rapport, ett beslut eller en commit citerar kopieras först till `underlag/granskningar/`, och en arbetsyta tas bort först när varje fil i den är registrerad i `FORTECKNING.jsonl` eller ett annat kvitto, eller nås från en ref i git | agenten |

Kundstarts primärkällor ligger i `underlag/kundstart/` (SQLite, gallringsjournal, egna backupkopior och bevis).
Kund-API och interna ärendeoperationer härleder versionsbundna byggunderlag till `underlag/<slug>/KUNDSTART.json`
och `underlag/<slug>/kundstart/`. Kunskapstexten `kunskap/kundstart.md` beskriver deras ansvar och återställning.

Allt under `underlag/` och `kunder/` är privat. Inget innehåll därifrån står i det publika repot, inte heller titlar ur
rapporter eller förteckningar; sökvägar och id:n får stå, i dokumentationen, commits och backlogposter, så länge de inte
bär privata uppgifter. Dashboardens vy Dokumentation och rapporter läser platserna och rapporthuvudena här vid varje
visning, utan egen förteckning, och visar det som ligger under `underlag/` och `kunder/` bara lokalt och inom flödesvyns
gränser, också blindningen före ägarens första val.

**Arbetsregeln** (ägaren 2026-10-06): ”Varje förändring i Nortropic ska hålla berörd dokumentation och spårbarhet
aktuell som en del av samma uppdrag. Ägaren ska inte behöva påminna om dokumentationen. Ett arbete redovisas inte som
färdigt förrän berörda instruktioner, rapportkopplingar och statusuppgifter är uppdaterade, eller en konkret
kvarstående begränsning har redovisats.” Ett skrivskyddat uppdrag ändrar inga filer och redovisar
dokumentationsbehovet i stället.

**Rapporthuvudet.** En bestående rapport börjar med ett huvud (YAML mellan `---`) med de fält som är relevanta:
- **Identitet och typ:** `id` (stabilt), `titel`, `typ`, `uppdrag`, `kund` eller `systemdel` och `moment`.
- **Vem och när:** `forfattare` (roll eller session) och `datum`.
- **Vad som granskats:** `granskad_identitet`, alltså repo och commit, körning, kandidatversion, designversion eller
  annat exakt underlag.
- **Status och utfall:** `rapportstatus` (utkast, färdig eller ersatt) och `bedomningsutfall` (godkänt, underkänt,
  ofullständigt eller ej bedömt).
- **Länkar:** `underlag`, `foregaende`, `ersatt_av`, `beslut` och `atgarder`.
- **Rättelser och giltighet** (valfria): `rattelser`, en lista med "datum: vad som rättats, var", och `giltighet`, till
  exempel utvecklingsdata eller historik, med skäl; en rättad slutsats skrivs inte om i texten, och dashboarden visar
  rättelserna vid rapporten och i översikten.

Ett värde som saknas skrivs "ej angivet". Rapportstatus och utfall är olika saker: en färdig rapport kan underkänna
resultatet. Ett exempel är `underlag/figma-pilot/BESLUTSUNDERLAG.md`.

**Avsändarna** (ägarens uppdrag 2026-10-07, punkt 7). Varje dom och bedömning har en avsändare av sju slag, med en
definition var i `kontroller/skapande.py` (`AVSANDARTYPER` och `KALLOR`), den enda källan i koden: ägarens egna ord och
beslut, Codex bedömning, Claudes eller skaparens bedömning, en annan granskares bedömning, maskinellt mätresultat,
hypotes och vidarebefordrad AI-bedömning. Bara ägarens egna ord och beslut räknas som ägarens: av godkännandet, läget,
stoppvakten och slutposterna. En AI-bedömning som ägaren vidarebefordrat är en egen källa, också när den är skriven i
första person. "Ägaren via Codex" betyder bara ägarens egna ord, ordagrant förmedlade, och kräver ett belägg för var
orden står. En äldre rad utan belägg skrivs inte om; den står som "ej belagd" och räknas inte. Ett belägg i efterhand
fästs vid raden i bilagan `underlag/<slug>/DESIGNDOMAR-belagg.jsonl`, bunden till radens sha256
(`kontroller/skapande.py belagg`), så att raden räknas som ägarens utan att bli en ny dom.

**Ateljéns slutpost** (`kunder/<slug>/atelje/korningar/<körning>/SLUT.json`, skriven av `kontroller/ateljeslut.py`; ägarens
uppdrag 2026-10-07, punkt 4) har samma form som helbyggets nedan. Arbetaren skriver den vid normalt avslut, fel och stopp.
Den binder ihop körningen, kandidaterna med sina versioner, repots commit och METOD.json:s sha256, skisskritiken och vem
som gjorde den, ägarens beslut med avsändaren, och stoppet eller felet med steget. Bredvid ligger körningens STATUS.json
och REDOVISNING.md. `kontroller/atelje.py` och `kontroller/prototyp.py` skriver beskedet ur posten och ger dess
slutkod. Slutkoderna och resten står i `kunskap/skapandeflodet.md`, Körspåret.

**Helbyggets slutpost** (`kunder/<slug>/korningar/<körning>/SLUT.json`, skriven av `kontroller/korslut.py`; ägarens
uppdrag 2026-10-07) bär rapporthuvudets fält i JSON, så att den läses som ett huvud. `underlag` är länkarna till
rapporter och bevis, och `atgarder` är nästa steg. Därtill:
- körningen, bygget (`dist_sha256`), metoden och slutkoden;
- de fem tillstånden var för sig: sessionen avslutad normalt, tekniskt godkänt, designgranskaren godkänner, ägaren
  godkänner och klart för leverans inom angiven omfattning;
- bristerna.

Terminalens besked skrivs ur posten, också när terminalen har stängts: då är slutkoden postens.

Ägarens dom räknas bara när ingen körning kan ha skrivit den: den fanns i `kunder/<slug>/DOM.json` när filen låstes vid
körningens start, eller skrevs efter att körningen slutat. En körning som avbröts med en signal får slutkod 4 också när claude hann avsluta
med kod 0, och klart för leverans kräver att sessionen avslutades normalt. Prövas posten senare (`--visa`, Flöde)
blir ett äldre ja historik också när startsidans godkännande inte längre gäller aktuellt underlag (samma kontroll som
Flöde steg 5 och kor.sh), och en dom som tillkommit efter en körning vars processer inte stoppades räknas inte
(GR-20261008-r117-claude, A1, C1 och C2).
- **Under körningen** nekas byggets Write och Edit för DOM.json, kor.sh:s hashlistor (`kunder/<slug>/prov/.skyddat-*`)
  och körningarnas protokoll (`kunder/<slug>/korningar/`, `kunder/<slug>/rapporter/` och `kunder/<slug>/atelje/korningar/`).
  Domloggen och dess bilaga `underlag/<slug>/DESIGNDOMAR-belagg.jsonl` omfattas också. Förekomst och filtyp prövas,
  så en länk eller tom katalog i en skyddad fils ställe inte faller utanför innehållshashningen. Finns DOM.json vid starten
  låses den och kopieras till `kunder/<slug>/korningar/<körning>/DOM-START.json`.
- **Hashlistorna** prövas mot kor.sh:s minne. kor.sh håller deras sha256, och sha256 för DOM.json när den låstes, i
  minnet. Har ett eget skript skrivit om en lista blir slutkoden 3. Ändras eller tillkommer DOM.json blir slutkoden
  också 3, även när listan förfalskats.
- **Ändrade domar:** domarna i kopian från starten räknas fortfarande, aldrig de som tillkom (GR-20261007-r101-om#BÖR-1
  och #KAN-3).
- **Vakten** (`kontroller/korvakt.py`) följer byggets processer, också dem som lämnat sin session och bytt förälder. Den
  stoppar dem innan något jämförs eller låsen släpps.
- **Samtidiga starter** reserverar samma fasta flock-fil genom `kontroller/bygglas.py`. kor.sh och vakten håller
  filbeskrivaren till avslutet; byggsessionen och webbtjänsten ärver den inte. PID-filen visar status men är inte låset.
- **En signal under bygget** går till claudes processgrupp. claude får SIGKILL efter `NWP_FRIST` sekunder, 10 om inget
  annat anges (#BÖR-2, #KAN-5).
- **Dödas kor.sh** (SIGKILL) gör vakten avslutet: den stoppar bygget, skriver posten (slutkod 4, eller en kort post
  när kor.sh dog före bygget) och släpper låsen. En befintlig slutpost räcker inte som bevis: korslut måste ha bekräftat
  just dess innehållshash genom kor.sh:s privata rör. En oförändrad bekräftad post bevaras; en obekräftad post flyttas
  till `kunder/<slug>/korningar/<korning>/SLUT-obestyrkt-<id>.json` och avslutet räknas om. Skyddsbrott ger kod 3 även vid avbrott. Avbrott mellan
  skrivningen och bekräftelsen räknas konservativt om. Ägarens dom kan sparas efter att vakten släppt låsen (#KAN-2,
  #KAN-4).
- **Gränsen:** några vägar når fortfarande förbi skyddet, och en del är inte prövad. Gränsen på processnivå är ett eget
  steg i backloggen.
  - Ett eget skript kan ändra kontrollerna: kor.sh, korslut.py, korvakt.py och Python-miljön är skrivbara när
    sandlådan är av.
  - Ett eget skript kan döda vakten.
  - En process kan startas via launchd, eller byta förälder två gånger innan vakten sett den mellersta.
  - Vakten är prövad med en attrapp i stället för claude, inte med claudes egna verktygsskal.

`.venv/bin/python kontroller/korslut.py --visa kunder/<slug>` prövar posten mot läget nu. Har bygget i
`kunder/<slug>/sajt/dist/`, granskningens metod eller startsidans godkännande ändrats sedan körningen står postens
godkännanden som historik, och klart för leverans är nej.

En körning utan slutpost syns där och i nästa körnings post, på ett av två sätt:
- **avbruten:** både kor.sh och vakten dödades (SIGKILL mot båda, eller en omstart). Har DOM.json ändrats sedan
  körningen startade är ägarens dom ej belagd, och nästa körning räknar inte de domar som tillkom efter den starten.
- **en post som inte kunde skrivas:** `kunder/<slug>/korningar/<körning>/UTEBLEV.json` med felet och slutkoden.
  Slutkod 5 betyder att posten uteblev för en körning som annars fått 0 eller 1.

Slutar kor.sh före bygget utan att stanna med en post (ett kommando som faller under set -e, eller en trasig fil som
läses in) skrivs en kort post med skälet, och slutkoden blir 2.

**Läsordningen:**
1. slutsatsen och vad den gäller;
2. de viktigaste fynden;
3. underlag och jämförelser;
4. begränsningar och det som inte prövats;
5. nästa åtgärd och de beslut som behövs.

**En senare granskning** säger vad den gör med den föregående: bekräftar fynd, verifierar en rättelse, gäller en ny
version eller rättar en tidigare slutsats. Ett fynd behåller sitt id från upptäckt till rättelse och verifiering, och
består det efter rättelsen öppnas dess post i backloggen igen (`backlog/README.md`).

## Kirurgen

I dashboarden under Kirurgen, eller i en session i repots rot: `/kirurg <url>` (GitHub, artikel eller YouTube).
Bara transkriptet: `.venv/bin/python kontroller/youtube.py URL --ut video.md`.

Spanaren (`kontroller/spana.py`) letar kandidater åt kirurgen utan modell: flöden, leverantörsdokumentation, GitHub,
Hacker News och YouTube-kanaler ur `kunskap/spaning-kallor.md`. Dashboarden kör den en gång i veckan och visar de
rankade kandidaterna under Kirurgen; "Skicka till kirurgen" startar ett vanligt intag. Själv: `.venv/bin/python kontroller/spana.py
spana --torr` visar vad den skulle hitta utan att spara.

Kirurgens vy visar också signal → diagnos → försöksplan → lokalt resultat, källhälsa och paus.
En misslyckad källa försvinner inte bakom ”inget nytt”. Kundstarts observation skiljer insamlat och överfört
från ännu inte observerat använt/levererat. Läsning startar inget. Lokala regressionsförsök kräver ett separat
begränsat ägarmandat och ändrar aldrig aktiv kod; körväg och gränser: `kunskap/kirurg-forbattring.md`.
Privat primärlagring är `kirurgen/forbattringar/`, källhälsa `kirurgen/spaning/HALSA.json`; befintligt register och
backlogg består. Ingen ny schemaläggning eller faktisk förbättringseffekt är påstådd. Separat granskade införanden
kan registreras mot exakt lokal Git-version med ett särskilt observationsmandat; eftereffekt redovisas som
inrapporterad observation med version och belägg. Återställningsbekräftelsen läser redan återställda filer och
ändrar ingen kod. CLI-formerna och de betrodda operatörsfilerna beskrivs i samma kunskapsfil.

## Prospekt

Hittar verksamheter i en bransch och kommun, mäter deras webbplats och rankar dem efter vad de har att vinna.
Reglerna: `kunskap/prospekt-och-utskick.md`; beslutet: `BESLUT.md`, tillägget 2026-10-02.

```sh
.venv/bin/python kontroller/prospekt.py svep --kampanj hantverkare-lulea --kommun 2580 --bransch hantverkare
.venv/bin/python kontroller/prospekt.py sajter --kampanj hantverkare-lulea --max 40
.venv/bin/python kontroller/prospekt.py analysera --kampanj hantverkare-lulea --max 10
.venv/bin/python kontroller/prospekt.py lista --kampanj hantverkare-lulea
.venv/bin/python kontroller/utskick.py prov          # testbrev till din egen adress
```

Samma sak med knappar i dashboarden under Prospekt: kampanj, lista, kort per verksamhet, demo, brev. Knappen demo
startar `./kor.sh` och stannar därför, som helbygget, utan en godkänd startsida (kedjan ovan). Ett brev skrivs
ur det vi mätt, du godkänner det i dashboarden, och det går aldrig till en enskild firma. Allt om verksamheterna
ligger i `underlag/prospekt/` och `underlag/<slug>/`, utanför git.

Nycklar, en gång: `~/.nortropic-hemligheter/webb-pro/scb.env` med `SCB_API_NYCKEL=…` (avgiftsfri, BankID på
registreraafr.scb.se) och `resend.env` med `RESEND_API_NYCKEL`, `AVSANDARE`, `SVAR_TILL`, `FORETAG`, `TELEFON`.
Katalogen 0700, filerna 0600.

## Provet

```sh
.venv/bin/python kontroller/prova.py <slug>          # alla grindar
.venv/bin/python kontroller/prova.py <slug> --snabb  # utan Lighthouse och utforskning
.venv/bin/python kontroller/granska.py <slug>        # oberoende granskning i en egen session (efter provet)
kontroller/rokprov.sh                                 # regressionsprov efter ändringar i kontroller/ eller mall/
```

Grindar (nio): bygge, design, seo, standard, axe, lighthouse, spill, utan-js, resor. Grinden standard prövar
byggstandardens maskinkontrollerbara punkter (`kunskap/byggstandard.md`, `kontroller/standard_kontroll.py`), med giltig
HTML via html-validate lokalt. Grinden design prövar DESIGN.md mot koden (`kunskap/bygge-referens.md`), och grinden
resor kör briefens viktigaste resor i Chromium och WebKit (`kunskap/resor.md`). Copykontrollen är en rapport, inte en
grind (`kunskap/copy-kontroll.md`): varje fynd rättas eller motiveras i rapporten. Apple-touch-icon och delningsbild
görs med `node kontroller/ikoner.mjs`.

## Installation (en gång per maskin)

```sh
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
(cd kontroller && npm ci && npx playwright install chromium chromium-headless-shell webkit)
```

Kräver Node i den senaste LTS-versionen som Vercel stöder (Homebrews `node@NN`), Claude Code och Vercel CLI. Det
dagliga underhållet (`kontroller/underhall.py`, från dashboarden) håller allt detta i den senaste versionen som klarat
proven, och startkontrollen (`kontroller/startkontroll.py`) bekräftar läget före varje start (`kunskap/beroenden.md`,
Underhåll).
