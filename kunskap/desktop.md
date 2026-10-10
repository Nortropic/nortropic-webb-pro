# Nortropic.app

Ägarens lokala Mac-app för kundportalen: ett eget fönster som öppnas från Finder eller Dock, med Hem (Ny kund, Kunder,
Testkunder), kundens arbetsområden och hela arbetsytan i appen, ovanpå den befintliga motorn. Uppdraget:
byggpaketet Nortropic Desktop och kundportal v2 (ägarens uppdrag 2026-10-10 ~16:58Z; beslutet i `BESLUT.md`, Tillägg
2026-10-10: Nortropic.app med Tauri 2 och hela den interaktiva kundportalen). Arbetsytans egna vyer och skydd: `kunskap/arbetsyta.md`.

Appen är ett tunt Tauri 2-skal (`desktop/`). Motorn är den befintliga utcheckningen av nortropic-webb-pro med
`dashboard.sh` och `dashboard/server.py`; inget av motorns arbete flyttas in i appen, och ingen affärslogik skrivs i Rust.
Lokalt betyder lokal arbetsyta och lokal motor. Modellerna och leverantörerna nås över nätet som förut.

## Starta, installera och bygga

- **Vardagen:** öppna Nortropic från Program eller Dock. Lås upp med Touch ID eller lösenordet. Hem öppnas.
- **Första starten:** appen föreslår huvudutcheckningen (`~/nortropic-repos/nortropic-webb-pro`) och port 4771, och
  visar verktygen den hittat på kända absoluta platser (claude, node). "Använd den här motorn" registrerar valet i
  appens inställningar; "Välj en annan mapp…" tar en annan utcheckning, som prövas (dashboard, `.venv`, origin
  Nortropic/nortropic-webb-pro) innan den godtas.
- **Motorn stoppad:** skalet säger det och erbjuder "Starta motorn", som kör `dashboard.sh start` med
  `NWP_UTAN_OPPNA=1`, porten och en kontrollerad PATH av de registrerade verktygens kataloger och systemets, utan
  inloggningsskal eller profil. En motor som redan kör återansluts, aldrig ersätts. Något annat på porten stoppas
  aldrig.
- **Bygga:** `cd desktop && npm ci && npm run bygg` ger `src-tauri/target/release/bundle/macos/Nortropic.app` och en
  DMG. Det kräver Rust (rustup, användarnivå) och Xcode Command Line Tools, inte i vardagen. Provbygget:
  `npm run bygg:prov` (debug, med provstyrningen; se Prov).
- **Installera:** `desktop/installera.sh` bygger releasen och kopierar appen till `~/Applications/Nortropic.app`
  (utan administratörsrätt). Appens data ligger utanför appen och berörs inte av en ny installation eller en
  borttagning.
- **Gamla genvägen:** `~/Applications/Nortropic arbetsyta.app` (AppleScript, `dashboard.sh genvag`) öppnar dashboarden i
  webbläsaren och finns kvar som uttrycklig reserv. Webbläsarvägen med nyckeln i adressens fragment fungerar som förut.

## Motorn och identiteten (kontraktet `desktop/1`)

Appen litar inte på att något svarar på porten. Före varje känsligt anrop prövar den:

1. att något lyssnar på `127.0.0.1:<port>` och vilken process det är (`/usr/sbin/lsof`), att processen tillhör samma
   användare och att dess arbetskatalog är den registrerade roten;
2. att motorn kan bevisa dashboardnyckeln: appen skickar en slumpad utmaning till `GET /api/desktop/identitet` och
   motorn svarar med HMAC-SHA256(nyckeln, utmaningen, instansen, roten, pid, porten, commit). Appen läser nyckeln
   native ur motorns nyckelfil (0600, samma användare; huvudutcheckningen `~/.nortropic-hemligheter/webb-pro/
   dashboard-nyckel`, en worktree `kunder/.dashboard-nyckel`) och jämför. Nyckeln lämnar aldrig appens native-lager
   och skickas först efter beviset;
3. att pid, port och rot i svaret är den lyssnande processens, och att kontraktet är `desktop/1`.

Fel process, fel rot, ett bevis som inte stämmer eller en motor utan kontraktet ger skalets diagnos, inga skrivningar.
Kompatibilitetsbeskedet (Motor och diagnos) visar appens version, kontraktet, motorns commit vid start, commit på disk
nu (ändrad sedan start: starta om motorn när inget arbete pågår), UI-versionen (en hash över arbetsytans filer) och
processen. Appen gör aldrig `git pull` och migrerar inget.

Vald anslutningsmodell: motorn levererar arbetsytans UI från loopback, och appen bär bara skalet. Skälet är att motorn
och UI:t ändras i samma commit flera gånger om dagen; ett UI inbakat i appen skulle glida isär från API:t. Skalet
(lås, första start, diagnos, senast kända läge) är paketerat och fungerar när motorn är stoppad.

## Upplåsning och session

- **Upplåsningen** är macOS LocalAuthentication (`deviceOwnerAuthentication`: Touch ID eller användarens lösenord). Den
  är en lokal operatörsupplåsning, ingen extern kontoinloggning, och den ger inget kostnads- eller publiceringsmandat.
- **Sessionen:** appen hämtar en engångskod (`POST /api/desktop/session`, 60 s, bunden till motorns instans) och
  navigerar fönstret till `/desktop/inloggning?kod=…`, som byter koden mot en slumpad session i en HttpOnly-kaka med
  SameSite=Strict utan Max-Age (`nwp_session_<port>`, en sessionskaka). JavaScript ser varken nyckeln eller kakan.
  Appens två skrivningar (koden och låset) bevisas med HMAC-SHA256(nyckeln, tid, nonce, väg, kroppens sha256) i
  `X-Desktop-Bevis`, med högst två minuters tidsskillnad och varje nonce en gång; nyckeln själv skickas aldrig.
- **Kakor i samma värd:** kakor skiljer inte på portar, så en förhandsvisad sajt kan sätta en kaka med samma namn.
  Motorn prövar därför varje värde med kakans namn, och utloggningssidan `/desktop/last` ändrar ingenting (utloggningen
  är `POST /api/desktop/utloggning` med sessionen och samma ursprung). Appen låses av `/desktop/last` bara när
  huvudramen laddar den, aldrig när en iframe gör det.
- **Skrivningar med sessionen** godtas bara med exakt samma ursprung (Origin `http://<Host>`) och Sec-Fetch-Site
  same-origin när WebKit skickar det. En förhandsvisad sajt på en annan port i samma värd, Origin null och same-site
  nekas. En session kan aldrig skapa en ny session eller låsa; det gör appens native-lager med nyckeln.
- **Lås:** menyn (Cmd-Shift-L), portalens "Lås Nortropic" och tidsgränsen (standard 30 minuter utan fokus,
  Inställningar) återkallar sessionerna i motorn (`POST /api/desktop/las`), visar skalets lås och spärrar motorns adress
  för fönstret. Strömmar som öppnats med en session stängs när den återkallas. Låset stoppar inget arbete: godkänt
  arbete fortsätter enligt sitt mandat i motorn.
- Sessionerna lever i motorns minne (högst 12 timmar, 2 timmar utan aktivitet). En omstartad motor har inga; appen
  märker den nya instansen och hämtar en ny kod genom samma väg.

## Fönster, meny och livscykel

| Händelse | Beteende i appen |
|---|---|
| Dubbelklick i Finder eller Dock | En appinstans (Tauri Single Instance och macOS); en andra start fokuserar fönstret. Motorns startlås i `dashboard.sh` gäller ändå. |
| Röda knappen, Cmd-W | Fönstret göms; appen och motorn lever. Dock visar samma fönster, vy och osparade fält igen. |
| Cmd-Q (Avsluta Nortropic) | Pågår arbete i motorn (körregistret) frågar appen: avsluta och låt arbetet fortsätta, visa det pågående arbetet, eller avbryt. Stopp görs i arbetsytan med motorns stoppväg (Kontroller). Valet "fråga inte" finns i Inställningar. Avslutet återkallar appens sessioner i motorn. |
| Dock-menyns Avsluta, utloggning ur macOS | Avslutar appen utan frågan (Apple Event); sessionerna återkallas, motorn och arbetet påverkas inte. |
| Lås | Se ovan. |
| UI eller webvy kraschar | Arbetet lever i motorn; nästa start läser läget ur motorn. |
| Motorn stoppas eller byter identitet | Vakten (var 20:e sekund) visar skalets frånkopplade läge; inget skickas förrän identiteten prövats igen. |
| Sömn | Ingen beräkning i appen att fortsätta; vid återkomst prövar vakten motorn igen. |

Menyn: Nortropic (Om, Motor och diagnos, Sök efter uppdatering, Lås, Göm, Avsluta), Arkiv (Ny kund Cmd-N, Kunder Cmd-1, Testkunder Cmd-2,
Översikt Cmd-Shift-H, Stäng fönstret), Redigera (Ångra, Gör om, Klipp ut, Kopiera, Klistra in, Markera allt i det
fokuserade fältet), Visa (Läs in igen, Större, Mindre, Verklig storlek, Helskärm), Fönster och Hjälp. Menyval byter bara
vy (adressens fragment, ingen omladdning) och går genom sidans egna knappar och kontrakt; inget menyval skriver något.
Undantagen: Motor och diagnos, Sök efter uppdatering och Hjälp visar skalet, och då lämnas arbetsytan (formulärens utkast
står kvar i portalens lagring, ett öppet rättelsefält gör det inte).
Fönstrets plats sparas och används bara när den hamnar på en skärm som finns.

## Förhandsvisningen och native-gränsen

- Bara appens egna sidor (`tauri://localhost`, skalet) har native-kommandon, och bara de namngivna i
  `desktop/src-tauri/capabilities/huvud.json` (appmanifestet i `build.rs` gör varje kommando behörighetsstyrt). Motorns
  arbetsyta och förhandsvisningarna har inga: ett `invoke` från motorns sida nekas av Tauri (provat i riktig WKWebView).
- Kommandona tar inga sökvägar, kommandon eller adresser till godtyckliga mål: HTTP-klienten når bara 127.0.0.1 på den
  registrerade porten, och motorroten prövas innan den godtas.
- Navigeringen: wry frågar för varje ram, också förhandsvisningens iframes, så navigeringsspärren nekar filer, okända
  scheman och motorns adress när appen är låst. Huvudramen prövas dessutom vid varje sidladdning: bara skalet och den
  verifierade motorns arbetsyta får visas där; allt annat leds tillbaka. Kontrollen sker när sidan har börjat laddas
  (wry:s sidladdning), så en sida som motorns egen kod skulle leda huvudramen till hinner köra innan den leds tillbaka,
  utan native-rättigheter; motorns sidor öppnar externa länkar i nya fönster, och förhandsvisningens sandlåda saknar
  allow-top-navigation. Nya fönster (target=_blank, window.open) öppnas aldrig i appen: https och http, också
  förhandsvisningen i en ny flik, går till systemets webbläsare (det uttryckliga undantaget); andra scheman nekas.
- Förhandsvisningen körs som förut på en egen port i en sandlådad iframe och får inga native-rättigheter. Dashboardens
  förhandsvisningsserver lägger in arbetsytans brygga (`dashboard/forhandsbrygga.js`) för Markera och Redigera text; den
  pratar bara med motorns eget ursprung genom postMessage och kan inte nå appen, nyckeln eller sessionen. Det den skickar
  är data: en markering fyller samtalets kontext, och en direktredigering sparas först med ditt klick i arbetsytan
  (`kunskap/arbetsyta.md`, Den levande förhandsvisningen och direktredigering).
- Hotmodellen: skydden gäller webbangrepp (en förhandsvisad sajt, en annan webbsida, DNS-ombindning). Kod som redan kör
  som samma macOS-användare kan läsa nyckelfilen och motorns lästa vägar; appen skyddar inte mot ett komprometterat konto.
  Motorns läsvägar är som förut öppna för samma användares processer (`kunskap/arbetsyta.md`, Säkerhet).

## Portalen

`dashboard/portal.js` och `portal.css`, samma frontend i appen och i webbläsaren. I appen bär varje vy portalens ram:
mörk navigering (Hem, Kunder, Ny kund, Testkunder, Arbetsytan, Systemförbättring, Lås), topprad med sök och kundens
stegrad. I webbläsaren ritas ramen bara på portalens egna vyer, så att arbetsytan där ser ut som förut. I ramen får
arbetsytans variabler portalens ljusa värden (målbildens ljusa yta och mörka navigering), utan ett andra designsystem.

- **Hem** (`#/start`, appens startvy): Ny kund, Kunder och Testkunder, Fortsätt där du slutade, Behöver din
  uppmärksamhet (bara riktiga kunder; testkunder räknas för sig) och det som pågår i motorn. Tomt läge utan
  platshållarkunder. Datan: `GET /api/desktop/oversikt`, framräknad ur arbetsytans projekt, Kundstarts ärenden, flödets
  kundlägen och körregistret; ingen modell, inget bygge.
- **Kunder och Testkunder** (`#/kunder`, `#/testkunder`): sök och urval (väntar på dig, påbörjade intervjuer, i
  skapandeflödet, pågår). Ett öppnande går dit arbetet står och startar inget.
- **Kundens sida** (`#/kund/<slug>`): företagets identitet, uppdragen (Kundstart och skapandeflödet) och var senare
  tillägg görs (Funktioner i det befintliga ärendet). Ett företag är en slug: Kundstarts ärende och byggprojektet med
  samma slug är samma kund.
- **Ny kund** (`#/ny-kund`, `#/ny-testkund`): företagets namn, valfri webbplats, vad de söker hjälp med och valfri
  kontaktperson. `POST /api/desktop/ny-kund` skapar ärendet genom Kundstarts skapandeväg: samma operations-id ger samma
  ärende (dubbelklick, tappat svar), samma namn ger 409 med länk till den befintliga kunden. Testmärkningen sätts av
  motorn ur vägens eget fält (testkunden får `fiktiv` och en testslug, `test-…`); en riktig kund får ingen modellbudget
  (AI kräver separat aktivering), en testkund tio anrop för syntetiskt material. Webbplatsen och syftet sparas som
  ägarens anteckningar (`anteckningar`, `kunskap: agarens_anteckning`), skilda från kundens uppgifter och AI:s förslag.
  Kundens personliga länk visas en gång i Kundstart.
- **Intervjun** (`#/intervju/<ärende>`, P04): samtalet bredvid det källmärkta underlaget. Ägaren antecknar kundens svar
  (`POST /api/desktop/intervju/<ärende>/svar`: ett kundmeddelande märkt via ägaren, en kundkälla), rättar en uppgift
  eller ett AI-antagande (`…/rattelse`: en uppgift märkt `agarens_rattelse`, AI-förslaget märkt rättat) och, för en
  testkund med budget kvar, låter AI ta en tur (`…/ai`: Kundstarts modellarbetare för just det ärendets köjobb,
  `kundstart_modell.py --live-cli --antal 1 --arende <ärende>`, högst två samtidigt). Ett verkligt ärende får ingen
  AI-tur och ingen kö som aldrig töms. AI:s frågor är frågekort utan sidoeffekter; AI:s funktionsförslag är kort som går
  genom Kundstarts planväg (`integrationsval`) och ansluter inget konto. Material läggs till med filväljaren eller genom
  att dra en fil från Finder till intervjun (`…/material`): samma prövning och lagring som kundens bilaga i Kundstart
  (PNG, JPEG, PDF eller UTF-8-text med rätt signatur, högst 4 MB och 20 filer), med ägaren som avsändare och läsningen
  och rätten som inte läst och okänd. En fil är data, inget kommando, och ger ingen åtkomst till mappen den kom ifrån. Samma revision som ägaren såg krävs; ett sent
  AI-svar ersätts när ärendet ändrats.
- **Förfining** (`#/granska/<kund>`, P07/E6): kommentarer på kandidatens bevarade ögonblicksbild (en punkt på bilden
  eller hela sidan), bundna till kandidat, hel version, bredd och bildens sha256; tråd, avvisa och verifierat löst (bara
  när en nyare version finns). De valda samlas till ett uppdrag (Rätta, Omarbeta designen, Bygg ut) genom arbetsytans
  ändringsväg och märks beställda; inget arbete startar förrän det startas under Kontroller. Kommentarerna ligger i
  bussens katalog, som sessionerna inte kan läsa.
- **Leverans och förvaltning** (`#/leverans-kund/<kund>`, P10–P12): migreringslägets fem belägg, aktiveringens
  torrkörning, leveranskvittona och Worker-namnen (`GET /api/desktop/leverans/<kund>`). Leveransbeskedet säger
  publicerat bara efter en klar release och en observation av kundens egen adress; ett läge som inte går att läsa står
  som det. Besök och förfrågningar står som ej anslutna. Releasen görs i Byggflöde med ditt klick som mandat.
- **Arbetsområdena** i stegraden: Kundstart leder till intervjun, Underlag och Funktioner till kundens Kundstartärende,
  Förslag, Bygge och Granskning till arbetsytans Förslagen, Byggflöde och Kod och preview, Förfining till kommentarerna
  (arbetsytan med besluten nås därifrån), Leverans och Förvaltning till kundens leveransvy. Det är namn på befintliga
  steg, ingen ny statusmaskin.

## Uppdatering

- **Utgåvan:** `desktop/bygg-utgava.sh "<ändringen>"` bygger releasen, packar appen som `Nortropic.app.tar.gz` och
  signerar den med minisign-nyckeln `~/.nortropic-hemligheter/webb-pro/desktop-uppdatering.key` (skapad med
  `npx tauri signer generate`, 0600). Signaturen binds till versionen i `tauri.conf.json` (`--app-version`). Utgåvan
  ligger i `desktop/utgava/` (utanför git), och motorn serverar den från loopback (`/desktop/uppdatering/utgava` och
  `/artefakt`); ingen extern uppdateringstjänst finns eller påstås.
- **I appen:** Nortropic → Sök efter uppdatering (eller Motor och diagnos). Appen hämtar beskrivningen ur den
  verifierade motorn, kräver kontraktet `desktop/1` och en högre version, och visar Installera eller Senare. Pågår arbete
  i motorn säger knappen "Installera ändå" (arbetet körs av motorn och påverkas inte).
- **Kontrollen:** artefakten prövas mot den inbyggda publika nyckeln (`desktop/src-tauri/uppdatering.pub`) med samma
  minisign-kontroll som Tauris uppdateringsmodul, och den signerade versionen ska vara den annonserade (en äldre
  signatur kan inte spelas upp som ny). Först sedan packas den upp i en tom katalog bredvid appen (inga absoluta
  sökvägar eller `..`; tar-biblioteket prövar länkar), och paketet ska vara Nortropic (`se.nortropic.desktop`) i den
  versionen. Bara en app i `~/Applications` eller `/Applications` uppdateras på plats.
- **Bytet och återgången:** den nuvarande appen flyttas till appens datakatalog (`forra-version/`), den nya läggs på
  plats, och appen startar om när den gamla processen har slutat. Misslyckas bytet läggs den gamla tillbaka.
  "Gå tillbaka till föregående version" byter tillbaka; det gäller bara appkoden, aldrig motorns data eller kontrakt.
- **Inte gjort:** Developer ID-signering och notarisering (inget utvecklarkonto; appen är ad hoc-signerad och byggd
  lokalt) och en publik uppdateringskanal.

## Lagring

- Appens inställningar: `~/Library/Application Support/se.nortropic.desktop/installningar.json` (0600): motorrot, port,
  verktygens sökvägar, Cmd-Q-valet, låstiden och fönstrets plats.
- Senast kända översikt: `senast-kanda.json` i samma katalog (0600), visas bara när appen är upplåst och motorn inte
  svarar, märkt med tiden och som inaktuell.
- Webvyns lagring (utkast i formulär, vald vy) ligger i appens WebKit-katalog och nås bara när appen är upplåst.
- Inga kunddata i apppaketet, i en DMG eller i en tempkatalog. Kundernas underlag stannar i motorns `underlag/` och
  `kunder/`. Appen har ingen egen nyckel i Keychain: den enda långlivade hemligheten är motorns dashboardnyckel, som
  stannar i sin befintliga fil.

## Avinstallera

`desktop/avinstallera.sh` listar utan flagga det som skulle tas bort: appen (`~/Applications/Nortropic.app` eller
`/Applications/Nortropic.app`, prövad på paketets id) och appens egna data (`~/Library/Application Support/`,
`~/Library/WebKit/` och `~/Library/Caches/` för `se.nortropic.desktop`, och om de finns HTTPStorages, sparat
fönsterläge, Preferences och Logs). `--app` tar bort appen och behåller inställningarna; `--allt` tar bort appen och dess
data, också föregående version efter en uppdatering. Kör appen vägrar skriptet (slutkod 3) och tar inte bort något.
Motorn rörs aldrig: repot, `underlag/`, `kunder/`, dashboardens nyckel och arbetet i motorn står kvar. Prövat
2026-10-10 i ett eget provhem (torrt, vägran medan appen kör, borttagning efter) och torrt mot ägarens hem; den riktiga
borttagningen i ägarens hem görs inte av ett prov, eftersom den skulle ta bort den installerade appens data.

## Prov

| Prov | Vad | Hur |
|---|---|---|
| `kontroller/rokprov/revision/prov_desktop.py` | motorns sida: identiteten, engångskoden, sessionens skrivningar och återkallelse, strömmen, Ny kund, översikten, det pågående arbetet, portalens filer | i rökprovet |
| `desktop/prov/prov_app.py` | den riktiga appen (provbygget) i riktig WKWebView mot en provinstans: lås och upplåsning, kakan osynlig, invoke från motorns sida nekas, Hem, listorna, Ny testkund med dubbelklick, Kundstart i ramen, stäng och öppna, lås och spärrad navigering, menyn, bilder av fönstret | för hand på en Mac; startar ingen modell |
| `desktop/prov/prov_release.py` | användarbygget: ingen provsträng (`nwp-provstyrning`) i binären och ingen provport; arkitekturen arm64 | för hand efter `npm run bygg` |
| `desktop/prov/prov_mac.py` | Mac-livet i den riktiga appen: krasch med SIGKILL (motorn lever, utkastet står kvar), vila (SIGSTOP/SIGCONT kortare och längre än låstiden; väggklockan går som under en riktig vila), helskärm, kopiera och klistra in genom Redigera-menyns åtgärder (urklippet återställs), en motor som slutar svara och kommer tillbaka, en fientlig förhandsvisning (`desktop/prov/fientlig_sida.html`) och resurserna i upplåst läge | för hand; startar ingen modell |
| `desktop/prov/prov_redigering_app.py` | direktredigering i den levande förhandsvisningen med riktigt ombygge och riktig fotografering, och med `--partner`/`--genomfor` partnerns ström och Genomför i utkastet med en riktig modell (provinstansens `NWP_PARTNER_MODELL`) | för hand; `--partner` och `--genomfor` kostar modellanrop |

**Provinstansen:** en dashboard ur en worktree på en egen port (`NWP_KORREGISTER=<egen katalog>
NWP_DASHBOARD_NYCKEL=<nyckel> .venv/bin/python -B dashboard/server.py --port 4791 --utan-lan`), med
`arbetsyta_fixtur.py` för en fiktiv kund. Provbygget startas av `desktop/prov/appdrivare.py` med en egen datakatalog
(`NWP_DESKTOP_DATA`) och upplåsningens attrapp (`NWP_DESKTOP_PROV_UPPLAS=1`); provstyrningen lyssnar på en slumpad
loopbackport med token och kör JavaScript i den riktiga WKWebView:n. Bilderna tas med `screencapture -l` av bara
appens fönster. Inget av detta finns i användarbygget (cargo-funktionen `prov`). Provbygget har ett eget paket-id
(`se.nortropic.desktop.prov`, `desktop/src-tauri/tauri.prov.conf.json`): det krockar aldrig med en installerad app
(enkelinstansen skulle annars lämna över till den) och delar inte dess webbvylagring.

## Beroenden

`desktop/package.json` (exakt `@tauri-apps/cli` 2.12.1) och `desktop/src-tauri/Cargo.toml` med `Cargo.lock`: tauri
2.12.1, tauri-build 2.7.1, tauri-plugin-single-instance 2.5.2, tauri-plugin-dialog 2.8.1, tauri-plugin-notification
2.5.1, objc2-local-authentication 0.3.2, hmac 0.12 och sha2 0.10. Versionerna var publicerade minst tre dygn före
införandet (karenstiden i `kunskap/beroenden.md`). Rust installeras med rustup på användarnivå.

## Inte gjort eller inte prövat (2026-10-10)

Täckningsmatrisen U01–U40, D01–D28 och J01–J12 med bevisnivå per prov står i den privata rapporten
`underlag/rapporter/RAPPORT-2026-10-10-desktop-kundportal.md`. Byggt sedan: partnerns strömmande svar, Genomför i
utkastet ur partnerns överlämning, och markering och direktredigering av text i den levande förhandsvisningen
(`kunskap/arbetsyta.md`). I korthet inte gjort: direktredigering av annat än en entydig text (bilder, länkar, attribut,
text som byggs av ett uttryck), Developer ID och notarisering, en publik uppdateringskanal, VoiceOver-prov och ett
mänskligt användbarhetsprov med ägaren. Upplåsningen med Touch ID eller lösenord kan bara en människa pröva.
