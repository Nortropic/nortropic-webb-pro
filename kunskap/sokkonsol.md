# Sökkonsol (Google Search Console): ägarskap, egenskap, sitemap, inspektion och tolkning

Gäller en lanserad sajt åt en riktig verksamhet (`kunskap/lansering.md`, lanseringsdagen punkt 3). Det finns inget
verktyg för sökkonsolen i repot: allt nedan görs av en **människa** i Search Console i webbläsaren, och ingen session
har åtkomst till verksamhetens konto. En fiktiv verksamhet får ingen egenskap.

## Ägarskap och åtkomst

- Egenskapen är verksamhetens tillgång. Verifiering med META-taggen i `<head>` på den kanoniska produktionsdomänen;
  taggen ligger kvar för alltid (tas den bort tappas verifieringen tyst). Värdet i taggens `content` skrivs i
  `underlag/<slug>/VERKSAMHET.json` som `webb.sokkonsol_verifiering`; exporten lägger det i `src/verifiering.json`, och
  mallens Bas renderar taggen på varje sida (prövat i `prov_sokkonsol.py`). En fiktiv verksamhet får ingen tagg. DNS-verifiering (domänegenskap) bara när
  verksamheten själv förvaltar zonen och vill det; ingen session ändrar DNS.
- Verksamheten är ägare. Vi läggs till som användare medan vi hjälper till och tas bort vid avslut; vem som äger vad
  står på kundens sida Så ändrar du på sajten.
- Inga inloggningsuppgifter, tokens eller nycklar sparas i repot eller i `underlag/`.

## Lanseringsdagen

Ordning (lansering.md): (1) noindex borta, verifierat med `curl -sI` och i sidans meta; (2) verifiera egenskapen och
lämna `https://<domän>/sitemap.xml`; (3) URL-inspektion av startsidan och de viktigaste sidorna, och begär indexering;
(4) Bing Webmaster Tools importerar egenskapen; (5) inkluderingen i Googles generativa AI-funktioner slås på i
egenskapens inställningar om kunden vill synas där (`seo.md`, Generativ AI i Google Sök). Egenskapen är av URL-prefix-typ: www och apex är skilda egenskaper,
därför omdirigerar den andra varianten med 301 eller 308.

## Sökdata och tolkning: observationer till åtgärder

| Observation | Läsning | Åtgärd |
|---|---|---|
| "Upptäckt, för närvarande inte indexerad" > 2 veckor på viktiga sidor | Google har sett adressen men inte prioriterat den | begär indexering igen; stärk intern länkning; kontrollera att sidan har substans |
| "Genomsökt, för närvarande inte indexerad" | innehållet bedöms tunt eller dubblerat | fördjupa eller slå ihop sidor; kontrollera canonical |
| Frågor i position 5–20 med visningar | sidan svarar delvis | ta in frågans lydelse i sidan; förbättra rubrik |
| Visningar utan klick | titeln eller beskrivningen lockar inte | skriv om `description`, gör titeln konkret |
| Återkommande frågor om ny tjänst eller ort | ett behov utan sida | ny sida bara med genuint innehåll |
| Core Web Vitals-rapporten (fältdata) | verklig upplevelse hos besökare (saknas ofta vid låg trafik) | åtgärda LCP-, CLS- eller INP-orsaken; Lighthouse är labbdata och inget "Googles betyg" |
| Manuella åtgärder | ska vara tom | vid post: åtgärda och begär omprövning |
| Rapporten för generativ AI (visningar och klick i AI Overviews och AI Mode) | hur sajten syns i Googles AI-svar; låga tal är vanliga för lokala sajter | samma åtgärder som för vanliga sökresultat: innehåll som svarar på avsikten, inga AI-knep (`seo.md`) |

Rutin: veckorna 1–2 efter lansering var 2–3 dag; därefter månadsvis (`kunskap/uppfoljning.md`). Söktermslistan är
ofullständig (Google döljer sällsynta frågor); termer redovisas som exempel, aldrig som total. Data för en oindexerad
förhandsvisning finns inte och hittas inte på.

Ett API-verktyg (Site Verification API och Search Console API) byggs först när en lanserad kund behöver det och
verksamheten har gett åtkomst; tills dess är det här en checklista för en människa. Villkoren när det byggs: verktyget
läser bara (scope `webmasters.readonly`); det loggar in med ägarens eget Google-konto, som verksamheten lagt till som
användare, aldrig med ett servicekonto på kundens egendom; token sparas utanför repot och `underlag/`. Första kandidat
att pröva före ett eget skript: github.com/AminForou/mcp-gsc @ d49eea9 (MIT; tjugo läsande verktyg) med scopet ändrat
till läsande, de destruktiva verktygen avstängda och bara läsande verktyg i allowedTools (registerposten 2026-10-03 om
RoboNuggets och mcp-gsc).
