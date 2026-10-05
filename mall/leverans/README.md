# Webbplatsen för {{NAMN}}

Webbplatsens källkod, levererad av Nortropic. Byggd med [Astro](https://astro.build) och driftsatt på Vercel.

## Bygga och se lokalt

```sh
npm ci            # installerar de låsta versionerna ur package-lock.json
npm run build     # bygger sajten (Vercel-adaptern skriver .vercel/output)
npm run dev       # lokal server med omladdning
```

## Driftsättning

- Ett Vercel-projekt per webbplats, kopplat till det här repot. Varje gren får en skyddad förhandsvisning (Standard
  Protection med Vercel Authentication; kunden ser den genom en delbar länk). `main` är produktion på kundens domän.
- Förhandsvisningar svarar med `X-Robots-Tag: noindex` från Vercel; produktionen indexeras.
- Miljövariablerna står i `.env.example`. Värdena läggs bara i Vercels projektinställningar, aldrig i repot.

## Formuläret

`src/pages/api/forfragan.js` tar emot förfrågningar: honeypot och tidsfälla, validering, en bild på högst 4 MB,
lagring i ett privat Vercel Blob-lager före mejlet, och mejl genom Resend. Utan mottagare i en förhandsvisning skickas
ingenting (demoläge); i produktion utan mottagare går besökaren till `/fel/` och felet loggas utan personuppgifter.

## Innehåll

`DESIGN.md` är den godkända designens kontrakt (färger, typsnitt, tillstånd och importerade stilvärden).
Bilderna i `src/assets/` är verksamhetens egna; licenser och källor står i `LICENSER.md`.
