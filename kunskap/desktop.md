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
- **Sessionen:** appen hämtar med nyckeln en engångskod (`POST /api/desktop/session`, 60 s, bunden till motorns
  instans) och navigerar fönstret till `/desktop/inloggning?kod=…`, som byter koden mot en slumpad session i en
  HttpOnly-kaka med SameSite=Strict (`nwp_session_<port>`). JavaScript ser varken nyckeln eller kakan.
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
| Cmd-Q (Avsluta Nortropic) | Pågår arbete i motorn (körregistret) frågar appen: avsluta och låt arbetet fortsätta, visa det pågående arbetet, eller avbryt. Stopp görs i arbetsytan med motorns stoppväg (Kontroller). Valet "fråga inte" finns i Inställningar. |
| Dock-menyns Avsluta, utloggning ur macOS | Avslutar appen utan frågan (Apple Event); motorn och arbetet påverkas inte. |
| Lås | Se ovan. |
| UI eller webvy kraschar | Arbetet lever i motorn; nästa start läser läget ur motorn. |
| Motorn stoppas eller byter identitet | Vakten (var 20:e sekund) visar skalets frånkopplade läge; inget skickas förrän identiteten prövats igen. |
| Sömn | Ingen beräkning i appen att fortsätta; vid återkomst prövar vakten motorn igen. |

Menyn: Nortropic (Om, Motor och diagnos, Lås, Göm, Avsluta), Arkiv (Ny kund Cmd-N, Kunder Cmd-1, Testkunder Cmd-2,
Översikt Cmd-Shift-H, Stäng fönstret), Redigera (Ångra, Gör om, Klipp ut, Kopiera, Klistra in, Markera allt i det
fokuserade fältet), Visa (Läs in igen, Större, Mindre, Verklig storlek, Helskärm), Fönster och Hjälp. Menyval byter bara
vy (adressens fragment, ingen omladdning) och går genom sidans egna knappar och kontrakt; inget menyval skriver något.
Fönstrets plats sparas och används bara när den hamnar på en skärm som finns.

## Förhandsvisningen och native-gränsen

- Bara appens egna sidor (`tauri://localhost`, skalet) har native-kommandon, och bara de namngivna i
  `desktop/src-tauri/capabilities/huvud.json` (appmanifestet i `build.rs` gör varje kommando behörighetsstyrt). Motorns
  arbetsyta och förhandsvisningarna har inga: ett `invoke` från motorns sida nekas av Tauri (provat i riktig WKWebView).
- Kommandona tar inga sökvägar, kommandon eller adresser till godtyckliga mål: HTTP-klienten når bara 127.0.0.1 på den
  registrerade porten, och motorroten prövas innan den godtas.
- Navigeringen: wry frågar för varje ram, också förhandsvisningens iframes, så navigeringsspärren nekar filer, okända
  scheman och motorns adress när appen är låst. Huvudramen prövas dessutom vid varje sidladdning: bara skalet och den
  verifierade motorns arbetsyta får visas där; allt annat leds tillbaka. Nya fönster (target=_blank, window.open)
  öppnas aldrig i appen: https och http utanför loopback går till systemets webbläsare, resten nekas.
- Förhandsvisningen körs som förut på en egen port i en sandlådad iframe och får inga native-rättigheter.
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
- **Arbetsområdena** i stegraden: Kundstart, Underlag och Funktioner leder till kundens Kundstartärende; Förslag,
  Förfining, Bygge och Granskning till arbetsytans Förslagen, Arbetsyta, Byggflöde och Kod och preview; Leverans och
  Förvaltning till Leverans och förvaltning. Det är namn på befintliga steg, ingen ny statusmaskin.

## Lagring

- Appens inställningar: `~/Library/Application Support/se.nortropic.desktop/installningar.json` (0600): motorrot, port,
  verktygens sökvägar, Cmd-Q-valet, låstiden och fönstrets plats.
- Senast kända översikt: `senast-kanda.json` i samma katalog (0600), visas bara när appen är upplåst och motorn inte
  svarar, märkt med tiden och som inaktuell.
- Webvyns lagring (utkast i formulär, vald vy) ligger i appens WebKit-katalog och nås bara när appen är upplåst.
- Inga kunddata i apppaketet, i en DMG eller i en tempkatalog. Kundernas underlag stannar i motorns `underlag/` och
  `kunder/`. Appen har ingen egen nyckel i Keychain: den enda långlivade hemligheten är motorns dashboardnyckel, som
  stannar i sin befintliga fil.

## Prov

| Prov | Vad | Hur |
|---|---|---|
| `kontroller/rokprov/revision/prov_desktop.py` | motorns sida: identiteten, engångskoden, sessionens skrivningar och återkallelse, strömmen, Ny kund, översikten, det pågående arbetet, portalens filer | i rökprovet |
| `desktop/prov/prov_app.py` | den riktiga appen (provbygget) i riktig WKWebView mot en provinstans: lås och upplåsning, kakan osynlig, invoke från motorns sida nekas, Hem, listorna, Ny testkund med dubbelklick, Kundstart i ramen, stäng och öppna, lås och spärrad navigering, menyn, bilder av fönstret | för hand på en Mac; startar ingen modell |
| `desktop/prov/prov_release.py` | användarbygget: ingen provsträng (`nwp-provstyrning`) i binären och ingen provport; arkitekturen arm64 | för hand efter `npm run bygg` |

**Provinstansen:** en dashboard ur en worktree på en egen port (`NWP_KORREGISTER=<egen katalog>
NWP_DASHBOARD_NYCKEL=<nyckel> .venv/bin/python -B dashboard/server.py --port 4791 --utan-lan`), med
`arbetsyta_fixtur.py` för en fiktiv kund. Provbygget startas av `desktop/prov/appdrivare.py` med en egen datakatalog
(`NWP_DESKTOP_DATA`) och upplåsningens attrapp (`NWP_DESKTOP_PROV_UPPLAS=1`); provstyrningen lyssnar på en slumpad
loopbackport med token och kör JavaScript i den riktiga WKWebView:n. Bilderna tas med `screencapture -l` av bara
appens fönster. Inget av detta finns i användarbygget (cargo-funktionen `prov`).

## Beroenden

`desktop/package.json` (exakt `@tauri-apps/cli` 2.12.1) och `desktop/src-tauri/Cargo.toml` med `Cargo.lock`: tauri
2.12.1, tauri-build 2.7.1, tauri-plugin-single-instance 2.5.2, tauri-plugin-dialog 2.8.1, tauri-plugin-notification
2.5.1, objc2-local-authentication 0.3.2, hmac 0.12 och sha2 0.10. Versionerna var publicerade minst tre dygn före
införandet (karenstiden i `kunskap/beroenden.md`). Rust installeras med rustup på användarnivå.

## Inte gjort eller inte prövat (2026-10-10)

Se rapporten `underlag/rapporter/RAPPORT-2026-10-10-desktop-kundportal.md` (privat) för täckningsmatrisen U01–U40,
D01–D28 och J01–J12 med bevisnivå per prov. I korthet: intervjuvyn med samtal och växande underlag sida vid sida (P04),
typade handlingskort (E5), markering, kommentarer och direktredigering i förhandsvisningen (E6), signerad uppdatering
(E9), Developer ID och notarisering (inget utvecklarkonto), och ett mänskligt användbarhetsprov med ägaren.
