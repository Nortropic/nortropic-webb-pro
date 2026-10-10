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

Lokalt (`wrangler dev`) är `MILJO` produktion: förfrågningar sparas i den lokala D1, och Wrangler simulerar
mejlbindningen: mejlet skrivs till terminalen och en lokal fil och skickas inte. Bindningen får aldrig `remote: true`,
som skickar riktiga mejl.

## Driftsättning

- En Cloudflare Worker per webbplats (`wrangler.jsonc`): produktionen på kundens godkända domän, utan workers.dev- och
  versionsadresser. `compatibility_date` är låst och ändras bara efter prov.
- Förhandsvisningen är en egen Worker (`--env forhandsvisning`) utan databas, bucket och mejlbindning: den kan inte
  läsa eller skriva produktionens data eller skicka ett riktigt mejl. Den skyddas med Cloudflare Access före första
  uppladdningen av verkligt material; `noindex` ersätter aldrig åtkomstskyddet.
- Mejlet går genom Cloudflares e-post (`send_email`-bindningen `EMAIL`), utan nyckel. Bindningen är låst till
  verksamhetens mottagare, verifierad i Nortropics Cloudflare-konto, och avsändaren på routing-domänen
  `notis.nortropic.se`. Hemligheter, om några, läggs med `wrangler secret put`, aldrig i repot eller i `vars`.
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
igen inom tio till tjugo minuter. Mejltjänsten har ingen idempotensnyckel, så ett mejl skickas aldrig om automatiskt.
Integritetstexten nämner Cloudflare som mottagare av förfrågan.

### Följ upp mottagna ärenden

Varje förfrågan står i D1-tabellen `forfragningar`, och dess avisering i `utkorg`:
- `accepterad`: mejltjänsten tog emot mejlet (`mejl_id`).
- `fel`: mejltjänsten nekade mejlet med en felkod som är ett slutligt besked (i `fel`); ärendet är sparat och ska
  följas upp.
- `skickar` som blir stående: utfallet är okänt (tidsgräns, serverfel, fel utan kod). Stäm av mot verksamhetens
  inkorg och Cloudflares e-postlogg innan något skickas igen, eftersom ett nytt försök kan ge ett andra mejl.
- `vantar`: ingen mejlbindning eller mottagare var konfigurerad.

Läs ärendena bara med behörig åtkomst, till exempel `npx wrangler d1 execute DB --remote --command "SELECT ..."`.
Kopiera dem aldrig till Git, publika rapporter eller öppna loggar. `gallras` anger när ett ärende ska tas bort enligt
integritetssidans lagringstid. Ingen schemalagd omsändning eller gallring körs förrän den uttryckligen aktiverats.

## Innehåll

`DESIGN.md` beskriver designens kontrakt (färger, typsnitt, tillstånd och importerade stilvärden).
Bildkällor och eventuella licensuppgifter redovisas i `LICENSER.md`; filens existens intygar inte att varje
användning är tillåten. Okända rättigheter måste klarläggas före publicering. Källkodens tekniska export
ersätter inte verksamhetens beslut om innehåll, design eller bildanvändning.
