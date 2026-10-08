# Webbplatsen för {{NAMN}}

Webbplatsens källkod, förberedd av Nortropic med [Astro](https://astro.build) och adapter för Vercel.
Exporten är inte ett godkännande av design, rättigheter eller publicering. Driftsättning och leveransgodkännande
kontrolleras separat för den version och omfattning som faktiskt lämnas över.

## Bygga och se lokalt

```sh
npm ci            # installerar de låsta versionerna ur package-lock.json
npm run build     # bygger sajten (Vercel-adaptern skriver .vercel/output)
npm run dev       # lokal server med omladdning
```

## Driftsättning

- Ett Vercel-projekt per webbplats, kopplat till det här repot. Före lanseringen skyddas alla driftsättningar, också
  produktionsadressen, med Vercel Authentication; kunden ser förhandsvisningen genom en delbar länk. Vid lanseringen
  byts skyddet till Standard Protection: kundens domän blir publik, och varje gren får en skyddad förhandsvisning.
  `main` är produktion på kundens domän.
- Förhandsvisningar svarar med `X-Robots-Tag: noindex` från Vercel; produktionen indexeras.
- Miljövariablerna står i `.env.example`. Värdena läggs bara i Vercels projektinställningar, aldrig i repot.

## Formuläret

`src/pages/api/forfragan.js` tar emot förfrågningar: honeypot och tidsfälla, validering, en bild på högst 4 MB,
lagring i ett privat Vercel Blob-lager före mejlet, och mejl genom Resend. Utanför produktionen (`VERCEL_ENV` annat än
`production`: förhandsvisning och utveckling) sparas och skickas ingenting (demoläge), också när variablerna råkar gälla
alla miljöer i Vercel. Serverns valideringsfel återger textfälten säkert, även utan JavaScript; en bild måste väljas
igen. En oläsbar eller helt för stor begäran kan inte återställas.

Utan lagringskvitto skickas inget mejl: besökaren får 503 och texten kvar. Finns lagringskvittot men mejlaviseringen
inte kunde bekräftas visas ett eget mottaget-besked (202), utan uppmaning att skicka igen. Både lagring och
mejlacceptans ger 303 till tacksidan. Mejltjänstens acceptans bevisar inte inkorgsleverans eller mänsklig läsning.

### Följ upp mottagna ärenden

Före lansering ska en ansvarig ha åtkomst till det privata Blob-lagret och en rutin för att läsa inkomna ärenden.
I Vercel-projektets anslutna lagring ligger varje mottagen förfrågan i `forfragningar/<datum>/<id>/forfragan.json`
med text, tid och eventuell bildsökväg. Läs filerna endast via projektets behöriga lagringsverktyg och hantera dem
enligt integritetssidans lagringstid; kopiera dem aldrig till Git, publika rapporter eller öppna loggar.

I samma katalog betyder `avisering.json` med matchande mottagningsfil och `accepterat_av_mejltjansten` att
mejltjänsten returnerade ett identifierat acceptanskvitto. Saknas filen är aviseringen **okänd**: kvittoskrivningen
kan också ha misslyckats efter mejlacceptans. Läs ärendet och kontrollera mejltjänstens logg innan eventuell
manuell omsändning. Den här leveransen startar ingen automatisk omsändning eller ny aviseringskö.

Ett helt tappat framgångssvar kan fortfarande ge dubbla inskick vid besökarens omförsök, och 202-sidan (mottagen, ej
aviserad) svarar på POST-adressen: en omladdning av den sidan är ett nytt inskick om besökaren bekräftar webbläsarens
fråga om att skicka formuläret igen. Formuläret saknar ännu
individuell, beständig inskicksidentitet före första POST utan JS; här finns ingen garanti om exakt en sändning.
Externa konton, kvitton, driftövervakning och ansvarigs åtkomst ska prövas uttryckligen inför lansering.

## Innehåll

`DESIGN.md` beskriver designens kontrakt (färger, typsnitt, tillstånd och importerade stilvärden).
Bildkällor och eventuella licensuppgifter redovisas i `LICENSER.md`; filens existens intygar inte att varje
användning är tillåten. Okända rättigheter måste klarläggas före publicering. Källkodens tekniska export
ersätter inte verksamhetens beslut om innehåll, design eller bildanvändning.

Bilagan lagras under ett fast separat namn, före `forfragan.json`: faller lagringen av mottagningsfilen efter bildens kvitto
ligger `bilaga/bild` kvar utan mottagningsfil och ska gallras med samma rutin som ärendena. Lokala tidsgränser är 10 s för
lagring, 8 s för mejl inklusive kvitto och 2 s för aviseringsfilen. Vid en tidsgräns är ett leverantörsutfall utan kvitto fortfarande okänt; kontrollera lagringen/mejltjänsten före manuell omsändning.
