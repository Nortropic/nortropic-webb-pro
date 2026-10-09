# Webbplatsen för {{NAMN}}

Webbplatsens källkod, förberedd av Nortropic med [Astro](https://astro.build) för Cloudflare Workers. Sidorna är
förrenderade och serveras som statiska filer; bara formulärets mottagning körs i Workern (`worker/index.js`).
Exporten är inte ett godkännande av design, rättigheter eller publicering. Driftsättning och leveransgodkännande
kontrolleras separat för den version och omfattning som faktiskt lämnas över.

## Bygga och se lokalt

```sh
npm ci                                                  # de låsta versionerna ur package-lock.json
npm run build                                           # förrenderade sidor i dist/
npx wrangler d1 migrations apply DB --local             # formulärets tabeller i en lokal D1
npx wrangler dev                                        # sidorna och Workern lokalt i workerd
```

Lokalt (`wrangler dev`) är `MILJO` produktion men utan mejlhemlighet: förfrågningar sparas i den lokala D1 och
aviseras inte. Lägg aldrig en riktig nyckel i `.dev.vars` i repot.

## Driftsättning

- En Cloudflare Worker per webbplats (`wrangler.jsonc`): produktionen på kundens godkända domän, utan workers.dev- och
  versionsadresser. `compatibility_date` är låst och ändras bara efter prov.
- Förhandsvisningen är en egen Worker (`--env forhandsvisning`) utan databas, bucket och mejlhemlighet: den kan inte
  läsa eller skriva produktionens data eller skicka ett riktigt mejl. Den skyddas med Cloudflare Access före första
  uppladdningen av verkligt material; `noindex` ersätter aldrig åtkomstskyddet.
- Hemligheter läggs med `wrangler secret put` (till exempel `RESEND_API_KEY`), aldrig i repot eller i `vars`.
- D1-databasen och R2-bucketen skapas vid aktiveringen med EU-jurisdiktion (`wrangler d1 create <namn> --jurisdiction
  eu`, `wrangler r2 bucket create <namn> --jurisdiction eu`; jurisdiktionen kan inte ändras efteråt), och databasens id
  skrivs in i `wrangler.jsonc`. Schemat ligger i `migrations/` och läggs med `wrangler d1 migrations apply DB --remote`.
- Återgång: `wrangler rollback` till en tidigare version. Den rör inte data i D1 eller R2 och inte domänens DNS.

## Formuläret

`worker/index.js` tar emot förfrågningar: skräpfälla och tidsfälla, kontroll att begäran kommer från webbplatsen,
validering och en bild på högst 4 MB. Förfrågan sparas i D1, och bilden privat i R2, före varje avisering. Utanför
produktionen (`MILJO` annat än `produktion`) sparas och skickas ingenting (demoläge). Serverns valideringsfel återger
textfälten säkert, även utan JavaScript; en bild måste väljas igen.

Utan bekräftad lagring skickas inget mejl: besökaren får 503 och texten kvar. Är förfrågan sparad men mejlet inte
bekräftat omdirigeras besökaren (303) till den förrenderade `/mottagen/`, utan uppmaning att skicka igen. Sparad och
accepterad av mejltjänsten ger 303 till tacksidan. Mejltjänstens acceptans bevisar inte inkorgsleverans eller läsning.

Samma inskick två gånger blir ett ärende: formuläret bär ett inskicks-id, och utan JavaScript känns samma innehåll
igen inom tio till tjugo minuter. Mejlet bär ärendets id som idempotensnyckel hos Resend, så ett nytt försök inom ett
dygn med samma innehåll skickar inget andra mejl. Resend lagrar kontots data i USA oavsett sändregion; det ska framgå
av integritetstexten.

### Följ upp mottagna ärenden

Varje förfrågan står i D1-tabellen `forfragningar`, och dess avisering i `utkorg`:
- `accepterad`: mejltjänsten tog emot mejlet (`mejl_id`).
- `fel`: mejlet föll; ärendet är sparat och ska följas upp. Kontrollera mejltjänstens logg innan en omsändning.
- `vantar` eller `skickar` som blir stående: utfallet är okänt. Stäm av mot mejltjänsten innan något skickas igen.

Läs ärendena bara med behörig åtkomst, till exempel `npx wrangler d1 execute DB --remote --command "SELECT ..."`.
Kopiera dem aldrig till Git, publika rapporter eller öppna loggar. `gallras` anger när ett ärende ska tas bort enligt
integritetssidans lagringstid. Ingen schemalagd omsändning eller gallring körs förrän den uttryckligen aktiverats.

## Innehåll

`DESIGN.md` beskriver designens kontrakt (färger, typsnitt, tillstånd och importerade stilvärden).
Bildkällor och eventuella licensuppgifter redovisas i `LICENSER.md`; filens existens intygar inte att varje
användning är tillåten. Okända rättigheter måste klarläggas före publicering. Källkodens tekniska export
ersätter inte verksamhetens beslut om innehåll, design eller bildanvändning.
