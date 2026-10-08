# Lansering: procedur, kontroll, oåterkalleligt och återgång

Gäller när en verksamhet har sagt ja till sajten och ägaren beslutar att den ska ut. Inget bygge har lanserats än,
och Vercel väntar tills en kund ska ut (ägarens beslut, `BESLUT.md`). Privat förhandsvisning och slutrapport kommer
alltid först. Verktygen i repot: `kontroller/prova.py` (provet, också mot en förhandsvisning),
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
   Det är Claudes tolkning av kärnfrågan och inte bekräftad av ägaren; "Ja, efter små ändringar" räknas inte.
   `.venv/bin/python kontroller/korslut.py --visa kunder/<slug>` prövar domen mot posten, och har bygget, metoden eller
   startsidans godkännande ändrats sedan körningen är bygget inte klart för leverans.
3. **Exporten** (ägaren eller en session): `.venv/bin/python kontroller/exportera.py <slug> [--git]`. Den lägger
   sajtens källor, leveransens låsta beroenden, formulärets funktion, README, `.env.example`, `vercel.json` och
   LICENSER.md i `kunder/<slug>/kundrepo/` (en tidigare export flyttas till `kundrepo-tidigare/<tid>/` och raderas
   aldrig), fäller exporten om en fil nämner lokala sökvägar, Nortropics privata underlag eller en nyckel, och bygger
   kundrepot i en tom katalog utanför repot. `--git` gör ett lokalt repo med en första commit på `main`; inget skickas
   någonstans. Slutkod 0 klar, 1 läckage eller bygget föll, 2 fel i anropet.
4. **Versionskvitto och omfattning:** `kunder/<slug>/exporter/<id>/EXPORT.json` sparar exportens kontroller,
   källornas hash, exportens filmanifest och eventuell koppling till helbyggets körning och dist. Inget privat
   protokoll följer med till kundrepot. Samma kunds export låses under kopieringen; förändrade källor eller ett
   fallerat byggprov ersätter inte den tidigare exporten. `--kandidat kNN` är en testexport. Alla exporter går att
   förbereda utan kundgodkännande, men det är uttryckligen inte samma sak som kundklar leverans. Slutpostens
   godkännanden räknas om vid visning och blir historiska om version eller beslut inte längre gäller. Drift,
   mottagning av formulär och domän är separata prov. SIGKILL kan inte fångas mitt i katalogbytet; tidigare export
   finns då kvar i kundrepo-tidigare/, men återställning kan behövas innan nästa försök.
5. **Kundrepot till GitHub och Vercel** har inget verktyg i repot: människa, eller en session med ägarens ja, enligt
   Vercel-steget nedan. Ingenting från leveransen sparas i repot; `kontroller/driftkoll.py` prövar svaren från en
   driftsatt adress och skriver bara ut.

## Vercel-steget

Byggstandardens L-punkter 1.4, 4.5, 4.6 och 8.1 pekar hit. Stacken är Astro med förrenderade sidor och Vercel-adaptern
för formulärets funktion; kundrepot görs av exporten ovan.

**Förhandsvisning, produktion och skydd** (prövat med riktiga HTTP-svar 2026-10-05 i provprojektet
`nortropic-leveransprov`; Vercels dokumentation läst samma dag):

- **Ett bygge, två lägen.** Förhandsvisningen och produktionen är samma bygge. HTML:en har noindex bara på 404, `/tack/`
  och `/fel/`, och robots.txt tillåter genomsökning i båda lägena; skillnaden ligger i driftsättningen.
- **Skyddsmetoden är Vercel Authentication** (ingår i Pro). Lösenordsskydd är ett betalt tillägg på Pro (20 USD per
  skyddat projekt och månad) och används inte. Kunden ser en förhandsvisning genom en delbar länk (Shareable Links,
  alla planer); våra egna prov går genom förbikopplingen för automatisering (`x-vercel-protection-bypass`, hemligheten
  bara i en privat fil, aldrig i repot eller loggen).
- **Före lanseringen: skydd för alla driftsättningar** (`ssoProtection: all`). Standard Protection släpper
  produktionsdomänerna, också projektets `<projekt>.vercel.app`, och den första CLI-driftsättningen i ett nytt projekt
  blev produktion: i provet svarade aliaset 200 utan inloggning tills skyddet ändrades till alla driftsättningar.
  Driftsätt förhandsvisningar med `vercel deploy --target preview`.
- **Vid lanseringen: Standard Protection** (`all_except_custom_domains`): kundens domän är publik, förhandsvisningarna
  skyddade.
- **Svaren** (`kontroller/driftkoll.py <adress> --lage forhandsvisning|produktion`): förhandsvisningen svarar 302 till
  Vercels inloggning utan förbikoppling och `X-Robots-Tag: noindex` (Vercel sätter det på genererade adresser);
  produktionen svarar 200 utan noindex. Formulärsvaren som mättes 2026-10-05 gällde det äldre kontraktet och verifierar
  inte dagens mottagare. Det aktuella kontraktet är `kunskap/forfragan.md`, Vid lansering: 422/413 med bevarad text
  där kroppen kunde läsas, 503 utan lagringskvitto, 202 när lagringen är bekräftad men mejlaviseringen är okänd,
  och 303 till `/tack/` efter både lagringskvitto och identifierad mejlacceptans. Förhandsvisningens demo sparar
  och skickar inget; mejlvariabler finns bara i produktionen. Plattformens storleksgräns och Astros Origin-skydd
  ska prövas i den faktiska driftsättningen före lansering.

- **Projekt (människa eller session med ägarens ja):** ett Vercel-projekt per verksamhet i teamet Nortropic, kopplat
  till kundens privata repo; funktionen i Stockholm (`regions: ["arn1"]` i `vercel.json`) och ett privat Blob-lager i
  samma region för inskicken.
- **Grenar (1.4):** en gren per ändring; varje gren får en egen skyddad förhandsvisning; `main` är produktion.
- **Cache (4.5):** filerna under `/_astro/` har hash i namnet och får `Cache-Control: public, max-age=31536000,
  immutable`; HTML får kort cache eller `must-revalidate`, så att en rättelse syns direkt. Pröva båda med `curl -sI`.
- **Mätning per ändring (4.6):** varje förhandsvisning prövas innan den slås ihop: `kontroller/prova.py` mot bygget,
  och Lighthouse mot förhandsvisningens adress. En regression mot 4.1 stoppar sammanslagningen.
- **HTTPS och värd (8.1):** Vercel ger certifikatet. En variant (med eller utan www) är kanonisk och den andra
  omdirigerar med 308; canonical, sitemap och `site` i `astro.config.mjs` pekar på den kanoniska. HSTS
  (`Strict-Transport-Security: max-age=63072000; includeSubDomains`) och `frame-ancestors 'none'` sätts som
  svarshuvuden i `vercel.json`, eftersom meta-CSP:n i mallen inte kan bära `frame-ancestors`.
- **Formuläret:** serverfunktionen på `/api/forfragan/` (`src/pages/api/forfragan.js`, ur `kontroller/exportera.py`) enligt
  `kunskap/forfragan.md`, Vid lansering: spara först, mejla sedan och skilj mottagning från avisering i beskedet.
  Hemligheter (mejltjänstens nyckel) ligger i Vercels miljövariabler, aldrig i repot.
- **Återgång:** föregående produktionsdriftsättning befordras tillbaka i Vercel (människa, eller Vercels CLI med
  ägarens ja). Det återställer inte DNS.

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

**E-postdomänen.** Domänen som formulärets mejl skickas från: SPF (`dig TXT <domän>`), DKIM under mejltjänstens
selektor (`dig TXT <selektor>._domainkey.<domän>`) och DMARC (`dig TXT _dmarc.<domän>`). Saknas både SPF och DKIM är
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

**Lanseringskonfigurationen** är densamma som förhandsvisningens bygge (ett bygge, två lägen ovan): kanonisk värd
vald, omdirigeringar från gamla adresser i `vercel.json` (301 eller 308), sökkonsolens verifieringstagg renderad,
formulärets mottagare satt i Vercels miljövariabler (`RESEND_API_KEY`, `FORFRAGAN_TILL`, `FORFRAGAN_FRAN`) och Blob-lagret
kopplat, provet grönt mot bygget och `kontroller/seo_kontroll.py --lage lansering` utan fynd. Skyddet byts från alla
driftsättningar till Standard Protection när kundens domän pekar rätt.

## Lanseringsdagen

1. Driftsätt `main`; startsidan svarar 200 med rätt innehåll.
2. Läsande kontroll mot den riktiga domänen: noindex borta (`curl -sI` och meta), sitemap 200, robots tillåter,
   kanonisk variant, och varje gammal adress ger 301 eller 308 och landar på sitt mål med 200 inom fem hopp
   (`curl -sIL <gammal adress>`). Formulärets riktiga väg prövas med ett inskick från verksamheten själv, inte från oss.
3. Sökkonsol och Bing Webmaster Tools: verifiera och lämna sitemap (människa, `kunskap/sokkonsol.md`).
4. Mätning: konverteringshändelserna syns på produktionsdomänen.
5. Verksamheten får sidan **Så ändrar du på sajten** (nedan).

## Så ändrar du på sajten

En sida till verksamheten, skriven i deras ord utan tekniska termer, överlämnad på lanseringsdagen tillsammans med
utvecklarens README (byggstandarden 1.6). Den säger:

- **vad som kan ändras utan ny beställning:** öppettider, telefon, priser, en bild, ett omdöme, en text som blivit fel;
- **hur man ber om det:** till vem, på vilket sätt, och vad som behövs (texten eller bilden, och var den ska stå);
- **svarstid:** när ändringen syns;
- **vem som äger domän och konton:** domänen, Vercel-projektet, mejltjänsten, sökkonsolen, och hur de lämnas över om
  verksamheten vill byta leverantör.

Sajten är statisk utan redigeringsverktyg, så kunden kan inte ändra själv; sidan ska säga det rakt.

## Oåterkalleligt

Första indexeringen av fel innehåll; ägarskap i sökkonsolen; omdirigeringar som ändrat inkommande länkars mål; mejl
som skickats till verkliga mottagare. Därför: noindex-kontrollen före sökkonsolen, och testdata bara i
förhandsvisningen.

## Återgång

Driftsättning: befordra föregående produktionsdriftsättning i Vercel; skydda alla driftsättningar igen om innehållet
inte får synas. DNS: en behörig människa återställer posterna till filen från före bytet. Ingen session ändrar DNS.
Återgången kan ta upp till den TTL som gällde innan; vid namnserverbyte räknas också delegeringens TTL. En återgång av
driftsättningen återställer inte DNS. Skriv tid, orsak, vem som beslutade och vad som återställdes i kundmappen, och
kör provet igen före nästa försök.

Källor: [RFC 1034 §3.6 och §4.2](https://datatracker.ietf.org/doc/html/rfc1034),
[Gmail Email sender guidelines](https://support.google.com/a/answer/81126?hl=en) (lästa 2026-09-30).

## Efter lansering

Veckorna 1–2: sökkonsolens indexeringsrapport var 2–3 dag; driftkontrollen enligt `kunskap/drift.md`; månadsrutinen
enligt `kunskap/uppfoljning.md`. Lanseringen redovisas i slutrapporten med tid, driftsättning och kontrollerna ovan.
