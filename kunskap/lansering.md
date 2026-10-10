# Lansering: procedur, kontroll, oåterkalleligt och återgång

Gäller när en verksamhet har sagt ja till sajten och ägaren beslutar att den ska ut. Inget bygge har lanserats på den
nya vägen än. Målplattformen är Cloudflare Workers (ägarens beslut 2026-10-09, `BESLUT.md`); sajterna som redan ligger
på Vercel stannar där (ägarens besked samma kväll). Privat förhandsvisning och slutrapport kommer alltid först.
Verktygen i repot: `kontroller/prova.py` (provet, också mot en förhandsvisning),
`kontroller/seo_kontroll.py --lage lansering`, `kontroller/webblasare/arkivera.mjs` (arkiv av den gamla sajten).
Det som inget verktyg gör står som **människa**: ägaren eller verksamheten gör det, ingen session.

## Från godkänt bygge till kundrepo

Kedjan före det här steget, och vem som startar vad: `README.md`.

1. **Helbygget är klart** när `./kor.sh` slutar med slutkod 0: provet grönt för det slutliga bygget, rapporten skriven
   i körningen och granskningen godkänd för samma bygge (`kontroller/korslut.py`). Det som sparas är provet
   (`kunder/<slug>/prov/`, med byggets `dist_sha256`), stoppvaktens besked (`prov/STOPPVAKT.json`, med rapportens
   sha256), granskningens omgångar (`kunder/<slug>/granskning/`), körningens logg och RAPPORT.md. Slutkoden, skälet och
   de fem tillstånden sparas i slutposten `kunder/<slug>/korningar/<körning>/SLUT.json` (README.md, Var information
   finns). Slutkod 0 betyder tekniskt godkänt och att designgranskaren godkänner; klart för leverans är det först när
   också ägaren godkänt bygget.
2. **Ägarens dom över bygget** skrivs i dashboarden (bygget, fliken Din dom) till `kunder/<slug>/DOM.json`, med byggets
   dist-hash, när inget bygge pågår: under en körning är filen låst, och en dom som tillkommer då räknas inte.
   Slutposten räknar svaret "Ja, som den är" på frågan om ägaren sätter sitt namn på sajten som ägarens godkännande.
   Det är Claudes tolkning av kärnfrågan och inte bekräftad av ägaren; "Ja, efter små ändringar" räknas inte, och
   posten och dashboarden visar det som ett eget värde, ja med villkor (`villkorat`), skilt från nej.
   `.venv/bin/python kontroller/korslut.py --visa kunder/<slug>` prövar domen mot posten, och har bygget, metoden eller
   startsidans godkännande ändrats sedan körningen är bygget inte klart för leverans.
3. **Exporten** (ägaren eller en session): `.venv/bin/python kontroller/exportera.py <slug> [--git]`. Den lägger
   sajtens källor, leveransens låsta beroenden (med Wrangler), Workern (`worker/index.js`), D1-schemat (`migrations/`),
   `wrangler.jsonc` med kundens namn, `public/_headers`, README, `.env.example` och LICENSER.md i
   `kunder/<slug>/kundrepo/` (en tidigare export flyttas till `kundrepo-tidigare/<tid>/` och raderas aldrig), fäller
   exporten om en fil nämner lokala sökvägar, Nortropics privata underlag eller en nyckel, och bygger kundrepot i en
   tom katalog utanför repot: `npm ci`, `astro build` innanför processgränsen, `dist/` utan filer som inte får bli
   publika och `wrangler deploy --dry-run` (förpackningen utan konto). `--git` gör ett lokalt repo med en första
   commit på `main`; inget skickas någonstans. Slutkod 0 klar, 1 läckage eller bygget föll, 2 fel i anropet.
4. **Versionskvitto och omfattning:** `kunder/<slug>/exporter/<id>/EXPORT.json` sparar exportens kontroller,
   källornas hash, exportens filmanifest och eventuell koppling till helbyggets körning och dist. Inget privat
   protokoll följer med till kundrepot. Samma kunds export låses under kopieringen; förändrade källor eller ett
   fallerat byggprov ersätter inte den tidigare exporten. `--kandidat kNN` är en testexport. Alla exporter går att
   förbereda utan kundgodkännande, men det är uttryckligen inte samma sak som kundklar leverans. Slutpostens
   godkännanden räknas om vid visning och blir historiska om version eller beslut inte längre gäller. Drift,
   mottagning av formulär och domän är separata prov. SIGKILL kan inte fångas mitt i katalogbytet; tidigare export
   finns då kvar i kundrepo-tidigare/, men återställning kan behövas innan nästa försök.
5. **Kundrepot till GitHub och Cloudflare**: `kontroller/kundrepo.py` skapar kundens eget repo vid projektstarten
   (lokalt, och privat `Nortropic/kund-<slug>` för en verklig verksamhet), gör exporten till en commit och pushar den
   när fjärrepot är bundet, och laddar upp en förhandsvisning bunden till commit och export (`--preview`, kvitto i
   `kunder/<slug>/leverans/`): Workern `kund-<slug>-forhandsvisning` på kontots workers.dev-adress, med `wrangler deploy
   --env forhandsvisning` ur commitens filer, prövade mot exportens manifest, under kundens lås, så att kvittot gäller
   exakt de bytes som laddades upp (R07). Utan `cloudflare.env` väntar kvittot på kontot; för en verklig verksamhet
   laddas ingenting upp förrän Cloudflare Access skyddar adressen, och skyddet prövas igen efter uppladdningen.
   Före uppladdningen prövas att tokenen når just det angivna kontot (`wrangler whoami`). Ett tappat svar efter att
   uppladdningen kan ha börjat (tidsgräns eller nätfel) ger kvittot `osaker`: ett nytt försök spärras tills
   `kundrepo.py <slug> --stam-av` har stämt av mot Cloudflares lista över deployments (läsande, med commit och
   export som märke). Hittas försökets deployment blir den kvittot; annars är ett nytt försök säkert.
   Projektstarten, varje push och fjärrepot prövas först med exportens läckagekontroll, och briefens text följer aldrig
   med till CLAUDE.md (R08). Produktion, D1, R2, Access och domänen: människa, eller en session med ägarens ja, enligt
   Cloudflare-steget nedan. `kontroller/driftkoll.py` prövar svaren från en driftsatt adress och skriver bara ut.

## Cloudflare-steget

Byggstandardens L-punkter 1.4, 4.5, 4.6 och 8.1 pekar hit. Stacken är Astro med förrenderade sidor som Static Assets och
en avgränsad Worker för formuläret (`mall/leverans/`, `kunskap/forfragan.md`); kundrepot görs av exporten ovan. Fakta
nedan är lästa i Cloudflares dokumentation 2026-10-10 (källorna sist i avsnittet). Workern är prövad lokalt i
Cloudflares runtime (workerd, `kontroller/workersprov.py`); **ingenting här är prövat mot ett verkligt konto än**.

**Kontot (aktiveringen, människa eller session med ägarens ja).** Nortropics Cloudflare-konto ansluts med filen
`~/.nortropic-hemligheter/webb-pro/cloudflare.env` (0600, utanför repot): `CLOUDFLARE_API_TOKEN` (en API-token
avgränsad till kontot: Workers-skript, D1 och R2), `CLOUDFLARE_ACCOUNT_ID` och `CLOUDFLARE_WORKERS_UNDERDOMAN`.
Tokenen går bara till Wrangler-processen (`kundrepo.cloudflare_miljo`), aldrig till byggets eller sajtens kod, och
skrivs aldrig i ett kvitto. Ingen ägarinloggning: Wranglers konfiguration ligger i körningens tempkatalog.

**Förhandsvisning och skydd.**

- **Två Workers.** Förhandsvisningen är en egen Worker (`--env forhandsvisning`, namnet `kund-<slug>-forhandsvisning`)
  på kontots workers.dev-adress, utan D1, R2 eller mejlbindning: `vars`, `d1_databases`, `r2_buckets` och `send_email`
  ärvs inte mellan miljöer (Wranglers bindningslista för miljön, prövat i `workersprov.py`), så den kan varken läsa
  produktionens ärenden eller skicka ett riktigt mejl. Workern går före varje
  fil där och märker varje svar `X-Robots-Tag: noindex, nofollow`. Produktionen har `workers_dev: false` och
  `preview_urls: false`: dess enda publika ingång är kundens domän.
- **Skyddsmetoden är Cloudflare Access** (Zero Trust Free räcker för färre än 50 användare). Access slås på för
  förhandsvisningens workers.dev-adress i Workerns inställningar (Domains). En anonym webbläsare får 302 till
  `<team>.cloudflareaccess.com`. Våra egna prov går genom en servicetoken (policy med handlingen Service Auth) med
  huvudena `CF-Access-Client-Id` och `CF-Access-Client-Secret`, i en privat fil (0600) som bara skickas till målets
  ursprung (`driftkoll.py --access-fil`, `webblasare/gemensamt.mjs`). Kunden släpps in med en Access-policy för sin
  e-postadress.
- **Ordningen för en verklig verksamhet:** Access-applikationen först, sedan uppladdningen. `kundrepo.py --preview`
  prövar att adressen svarar med Access före och efter uppladdningen och stannar annars med `vantar_pa_skydd`.
- **Svaren** (`kontroller/driftkoll.py <adress> --lage forhandsvisning|produktion [--access-fil F] [--formular]`):
  förhandsvisningen 302 till Access utan behörighet, med behörighet 200 och noindex; produktionen 200 utan noindex,
  robots.txt och sitemap.xml 200, säkerhetshuvudena på plats. Formulärets kontrakt: `kunskap/forfragan.md`.

**Data (aktiveringen).** D1 och R2 skapas per kund med EU-jurisdiktion: `wrangler d1 create kund-<slug>-forfragningar
--jurisdiction eu` och `wrangler r2 bucket create kund-<slug>-bilagor --jurisdiction eu`. Jurisdiktionen sätts bara
när resursen skapas och kan inte ändras efteråt; R2-bindningen i `wrangler.jsonc` bär `"jurisdiction": "eu"`.
`database_id` skrivs in i kundrepots `wrangler.jsonc`, schemat läggs med `wrangler d1 migrations apply DB --remote`,
och mottagaren och avsändaren står i `vars` (`FORFRAGAN_TILL`, `FORFRAGAN_FRAN`) och i `send_email`-bindningens
listor, som exporten skriver in. Mejlet går genom Cloudflares e-post (K04, ägarens beslut 2026-10-10), utan nyckel:
verksamhetens brevlåda läggs till som verifierad mottagare i Nortropics konto (Email Routing, Destination addresses),
och verksamheten klickar på Cloudflares verifieringslänk före lanseringen. Avsändaren är en adress på
`notis.nortropic.se`, routing-domänen i samma konto. Release nekas så länge bindningen bär mallens platshållare.
Integritetstexten nämner Cloudflare som mottagare av förfrågan.

Har kunden valt nyhetsbrevet (K14, `kunskap/integrationer.md`), gör så här:
- Skapa listan och bekräftelsemallen (dubbel bekräftelse) i kundens Brevo-konto.
- Skriv deras id i `CLOUDFLARE.json` (`nyhetsbrev_lista`, `nyhetsbrev_mall`).
- Lägg nyckeln med `wrangler secret put BREVO_API_NYCKEL` i produktionens Worker.
- Ge `/api/nyhetsbrev/` samma hastighetsbegränsning som formuläret.
- Låt integritetstexten nämna Brevo.

Pröva en anmälan till en egen adress efter releasen. Det första riktiga anropet till Brevo görs där.

Har kunden valt kundregistret (K10, Pipedrive), gör så här:
- Lägg migreringen `0002_kundregister.sql` med `wrangler d1 migrations apply DB --remote` (den följer med varje export).
- Skriv kontots underdomän i `CLOUDFLARE.json` (`pipedrive_doman`).
- Lägg nyckeln med `wrangler secret put PIPEDRIVE_TOKEN`.
- Låt integritetstexten nämna Pipedrive.

Det första riktiga ärendet visar överföringen: se `forfragningar.py <kundrepo> --remote`, under kundregister.

**Gränser på gratisnivån** (Workers Free; läst 2026-10-10, prövas mot kontots faktiska plan): statiska filer är
gratis och obegränsade; Workern 100 000 anrop per dygn för hela kontot (därefter svarar `/api/*` 429 i stället för
att falla tillbaka), 10 ms CPU per anrop (väntan på D1, R2 och fetch räknas inte); D1 500 MB per databas, 5 GB per
konto, 10 databaser, 5 miljoner lästa och 100 000 skrivna rader per dygn; R2 10 GB-månader; 20 000 filer och 25 MiB per
fil i en sajt; 5 schemalagda körningar (Cron Triggers) per konto. Tio databaser per konto räcker inte för många
kunder på gratisnivån: en planfråga för ägaren före den elfte kunden, aldrig en uppgradering som bieffekt.

- **Grenar (1.4):** en gren per ändring; varje gren förhandsvisas (`kundrepo.py --preview` laddar upp exportens
  commit); `main` är produktion.
- **Cache (4.5):** filerna under `/_astro/` har hash i namnet och får `Cache-Control: public, max-age=31536000,
  immutable` ur `_headers`; HTML får plattformens förval. Pröva båda med `curl -sI`.
- **Mätning per ändring (4.6):** varje förhandsvisning prövas innan den slås ihop: `kontroller/prova.py` mot bygget,
  och Lighthouse mot förhandsvisningens adress (genom Access). En regression mot 4.1 stoppar sammanslagningen.
- **HTTPS och värd (8.1):** Cloudflare ger certifikatet för en Custom Domain. En variant (med eller utan www) är
  kanonisk och den andra omdirigerar med 308; canonical, sitemap och `site` i `astro.config.mjs` pekar på den
  kanoniska. HSTS och `frame-ancestors 'none'` sätts i `public/_headers` för de statiska filerna och i Workerns kod för
  dess egna svar (`_headers` gäller inte svar som Workern skapar).
- **Formuläret:** Workern på `/api/forfragan/` enligt `kunskap/forfragan.md`, Vid lansering: spara först i D1 och R2,
  mejla sedan och skilj mottagning från avisering i beskedet.
- **Återgång:** `wrangler rollback [<version-id>]` till en tidigare version (de 100 senaste går att välja; `wrangler
  deployments list` visar historiken). Återgången rör inte data: D1 och R2 står kvar som de är, och en återgång
  stoppas om en bunden bucket har tagits bort. Den återställer inte heller DNS.

**Domänen (K01; människa med kundens och ägarens ja).** En Workers Custom Domain kräver att domänens zon är aktiv på
Cloudflare (namnservrarna pekar dit), och den kan inte läggas på ett värdnamn som redan har en CNAME-post. Vägarna:

1. **Zonen till Cloudflare** (gratisplanen; standardvägen): zonen importeras, varje post jämförs med den sparade
   förteckningen (nedan), MX, SPF, DKIM och DMARC står kvar oförändrade, och först därefter byts namnservrarna hos
   registraren. Registraren kan vara kvar.
2. **Kunden behåller DNS hos sin nuvarande leverantör:** en partiell zon (CNAME-uppsättning) kräver Business-plan;
   Cloudflare for SaaS ger 100 egna värdnamn utan kostnad, med Workern som ursprung genom en route, men apex-domänen
   kan bara proxas med ett Enterprise-tillägg. Båda är planbeslut för ägaren, inte en standardväg.

Källor (lästa 2026-10-10): [Static Assets: run_worker_first](https://developers.cloudflare.com/workers/static-assets/binding/),
[_headers](https://developers.cloudflare.com/workers/static-assets/headers/),
[gränser](https://developers.cloudflare.com/workers/platform/limits/),
[statiska filers kostnad](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/),
[Access för workers.dev](https://developers.cloudflare.com/workers/configuration/cloudflare-access/),
[servicetokens](https://developers.cloudflare.com/cloudflare-one/identity/service-tokens/),
[D1:s placering](https://developers.cloudflare.com/d1/configuration/data-location/),
[D1:s gränser](https://developers.cloudflare.com/d1/platform/limits/),
[R2:s jurisdiktion](https://developers.cloudflare.com/r2/reference/data-location/),
[Wranglers miljöer](https://developers.cloudflare.com/workers/wrangler/configuration/),
[Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/),
[partiell zon](https://developers.cloudflare.com/dns/zone-setups/partial-setup/),
[Cloudflare for SaaS](https://developers.cloudflare.com/cloudflare-for-platforms/cloudflare-for-saas/plans/),
[återgång](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/),
[e-post från Workers](https://developers.cloudflare.com/email-service/api/send-emails/workers-api/),
[verifierade mottagare](https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/),
[e-postens gränser](https://developers.cloudflare.com/email-service/platform/limits/).

**Sajterna som ligger kvar på Vercel** (ägarens besked 2026-10-09: inga befintliga hemsidor flyttas) förvaltas som
förut: Vercels CLI finns kvar i verktygslådan, driftkollen tar `--bypass-fil` för en äldre förhandsvisning, och
återgång sker där genom att föregående produktionsdriftsättning befordras. Vercel-vägens tidigare mätningar
(provprojektet `nortropic-leveransprov`, 2026-10-05) gäller bara den vägen.

## Före lanseringsdagen

**Resorna som står kvar.** `prov/resor/RESOR.md` listar under "Kvar till lanseringen" de resor som provet inte kan
köra lokalt (`kunskap/resor.md`): nivån testintegration (till exempel en genomförd bokning i tjänstens testmiljö) och
verklig leverans (en förfrågan som kommer fram till verksamheten). Var och en genomförs och kvitteras, med datum och
vem som såg resultatet, innan lanseringen.

**DNS (människa).** Först sänker en behörig människa TTL för posterna som ska ändras, till exempel till 300 s, minst
en gammal TTL före bytet. TTL för delegeringens NS-poster sätts av registret och går inte att sänka i kundens zon.
Har kunden e-post på domänen är standardvägen att bara ändra webbposterna hos nuvarande DNS-värd. Ett
namnserverbyte kräver att hela zonen återskapas ur en zonexport, också namn som ingen kontroll räknar upp. Ingen
session ändrar DNS. Spara posterna före bytet (NS, MX, TXT, CAA, A och AAAA på domänen; A, AAAA och CNAME på www;
TXT på `_dmarc`) med `dig +noall +answer <namn> <typ>` i en fil i kundmappen, och läs samma poster igen när den
gamla TTL:en har löpt ut. Ändrad eller saknad MX, TXT eller `_dmarc` är ett fynd; webbposterna och NS ska ha
ändrats. När bytet är bekräftat höjer den behöriga människan TTL igen.

**E-postdomänen.** Formulärets mejl skickas från Nortropics routing-domän `notis.nortropic.se`. Cloudflare lade
posterna när Email Routing slogs på 2026-10-10: MX och SPF på `notis.nortropic.se` och DKIM under
`cf2024-1._domainkey.nortropic.se`; DMARC gäller via `_dmarc.nortropic.se` (`p=none`). Att signeringen och
leveransen fungerar visar först ett riktigt mejl till en verifierad mottagare. Kontrollen av en avsändardomän: SPF
(`dig TXT <domän>`), DKIM under mejltjänstens selektor (`dig TXT <selektor>._domainkey.<domän>`) och DMARC
(`dig TXT _dmarc.<domän>`). Saknas både SPF och DKIM är
det ett fynd; saknad DMARC en anmärkning; flera SPF-poster ett fynd. Det prövar att posterna finns, inte att
signeringen fungerar; läs också mejltjänstens eget verifieringsbesked. Gmail kräver SPF eller DKIM av alla avsändare.

**Arkiv av den gamla sajten.** Före omdirigeringar och DNS-byte:

```sh
node kontroller/webblasare/arkivera.mjs --adress https://gamla-domanen.se --kund <kundmapp utanför repot> \
  --intervju ADRESSER.json --ut <ny katalog i kundmappen>
```

Verktyget vägrar kataloger inuti repot; arkivet läggs därför utanför, till exempel i `~/Arkiv/<slug>/`.
`ADRESSER.json` är `{"migrering_adresser": ["https://gamla-domanen.se/sida/", ...]}` med de gamla adresserna som
ska omdirigeras. Verktyget förenar dem med sidkartan och sparar HTML, HAR och helsidesbild per sida; `MANIFEST.json`
anger varje adress, status, fel och SHA-256. Läs alla fel innan den gamla sajten försvinner. Arkivet är privat
kundmaterial.

**Releasen** (K02:s produktion; `kundrepo.py <slug> --release`, handlingen release i Byggflöde): exportens commit
laddas upp till produktionens Worker (`kund-<slug>`, toppnivån i `wrangler.jsonc`) ur det frysta underlaget, under
kundens lås, med kvittot `RELEASE-*.json`. Den kräver en verklig verksamhet, en aktuell och klar förhandsvisning av
samma commit och kundens driftvärden: `underlag/<slug>/CLOUDFLARE.json` (privat) med `database_id`, `forfragan_till`
och `forfragan_fran`, som exporten skriver in i kundrepots `wrangler.jsonc`. Mandatet är ägarens klick på releasen i
Byggflöde: dashboarden skriver då `RELEASEMANDAT.json`, bundet till förhandsvisningens commit och export, och mandatet
gäller en release. Ett okänt utfall spärrar nästa release tills den stämts av. Releasen gör inte domänen: Custom Domain
och DNS är egna handlingar (nedan), och återgången är `wrangler rollback`. Inget av detta är prövat mot ett konto.

**Migreringsläget** (`kontroller/migreringslage.py <slug>`, i Byggflöde under Leveransen) har fem skilda besked, vart och
ett med sitt belägg:
- förberedd: en aktuell export;
- måltestad: en klar förhandsvisning på Cloudflare;
- trafik flyttad: en klar release och, efter den, en observation av kundens egen adress som svarar från Workern;
- data avstämd: gäller bara kunder med äldre data på Vercel;
- legacy avvecklad: gäller bara kunder med ett äldre Vercel-projekt.

Observationen görs efter releasen och domänbytet: `migreringslage.py <slug> --observera https://<kundens domän>`. Den gör
två GET-anrop och sparar kvittot `TRAFIK-*.json`. Förhandsadresser, workers.dev och vercel.app nekas. "Migrerad" sägs
bara när kunden hade en äldre drift och alla fem är uppfyllda, och en ny kund blir "i drift på Cloudflare". Beståndet av
äldre Vercel-projekt är privat (`underlag/leverans/VERCEL-BESTAND.json`), och `--oversikt` visar varje kund och varje
äldre projekt.

**Lanseringskonfigurationen** är samma bygge som förhandsvisningens: kanonisk värd vald, omdirigeringar från gamla
adresser i `public/_redirects` (301 eller 308; högst 2 000 statiska regler, och de gäller inte vägar som Workern
svarar på, [källa](https://developers.cloudflare.com/workers/static-assets/redirects/), läst 2026-10-10), sökkonsolens verifieringstagg renderad,
D1 och R2 skapade med EU-jurisdiktion och bundna i `wrangler.jsonc`, schemat lagt, mottagaren verifierad och inskriven
med avsändaren i `vars` och mejlbindningen, provet grönt mot bygget och `kontroller/seo_kontroll.py --lage lansering`
utan fynd.
Produktionens Worker får kundens domän som Custom Domain först när domänvägen ovan är vald och posterna sparade.

## Lanseringsdagen

1. Driftsätt `main` (`wrangler deploy` i kundrepot, med ägarens ja); startsidan svarar 200 med rätt innehåll.
2. Läsande kontroll mot den riktiga domänen: noindex borta (`curl -sI` och meta), sitemap 200, robots tillåter,
   kanonisk variant, och varje gammal adress ger 301 eller 308 och landar på sitt mål med 200 inom fem hopp
   (`curl -sIL <gammal adress>`). Formulärets riktiga väg prövas med ett inskick från verksamheten själv, inte från oss.
3. Sökkonsol och Bing Webmaster Tools: verifiera och lämna sitemap (människa, `kunskap/sokkonsol.md`).
4. Mätning: konverteringshändelserna syns på produktionsdomänen.
5. Verksamheten får sidan **Så ändrar du på sajten** (nedan).
6. Google-företagsprofilen uppdateras samma dag: webbadress, öppettider och adress som på sajten (byggstandarden 7.4;
   `kunskap/lokal-synlighet.md`, Korrekta uppgifter; profilbladet i rapportens punkt 14).

## Så ändrar du på sajten

En sida till verksamheten, skriven i deras ord utan tekniska termer, överlämnad på lanseringsdagen tillsammans med
utvecklarens README (byggstandarden 1.6). Den säger:

- **vad som kan ändras utan ny beställning:** öppettider, telefon, priser, en bild, ett omdöme, en text som blivit fel;
- **hur man ber om det:** till vem, på vilket sätt, och vad som behövs (texten eller bilden, och var den ska stå);
- **svarstid:** när ändringen syns;
- **vem som äger domän och konton:** domänen, Workern och dess data (D1, R2) i Nortropics Cloudflare-konto,
  mejltjänsten, sökkonsolen, och hur de lämnas över om verksamheten vill byta leverantör.

Sajten är statisk utan redigeringsverktyg, så kunden kan inte ändra själv; sidan ska säga det rakt.

## Oåterkalleligt

Första indexeringen av fel innehåll; ägarskap i sökkonsolen; omdirigeringar som ändrat inkommande länkars mål; mejl
som skickats till verkliga mottagare. Därför: noindex-kontrollen före sökkonsolen, och testdata bara i
förhandsvisningen.

## Återgång

Driftsättning: `wrangler rollback` till föregående version (data i D1 och R2 rörs inte); ta bort Custom Domain om
innehållet inte får synas alls. För en sajt som ligger kvar på Vercel: befordra föregående produktionsdriftsättning
där. DNS: en behörig människa återställer posterna till filen från före bytet. Ingen session ändrar DNS.
Återgången kan ta upp till den TTL som gällde innan; vid namnserverbyte räknas också delegeringens TTL. En återgång av
driftsättningen återställer inte DNS. Skriv tid, orsak, vem som beslutade och vad som återställdes i kundmappen, och
kör provet igen före nästa försök.

Källor: [RFC 1034 §3.6 och §4.2](https://datatracker.ietf.org/doc/html/rfc1034),
[Gmail Email sender guidelines](https://support.google.com/a/answer/81126?hl=en) (lästa 2026-09-30).

## Efter lansering

Veckorna 1–2: sökkonsolens indexeringsrapport var 2–3 dag; driftkontrollen enligt `kunskap/drift.md`; månadsrutinen
enligt `kunskap/uppfoljning.md`. Lanseringen redovisas i slutrapporten med tid, driftsättning och kontrollerna ovan.
