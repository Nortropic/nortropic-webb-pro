---
id: B-20261003-sokkonsol-md-villkoren-for-api-verktyget-skrivs
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · RoboNuggets, 3 plugins that turn Claude Code into an SEO expert + AminForou/mcp-gsc
skapad: 2026-10-03
prio: normal
steg: lanseringen, sökkonsolen (kunskap/sokkonsol.md)
commit: 962f74f
andrad: 2026-10-08T15:22Z
---
# sokkonsol.md: villkoren för API-verktyget skrivs nu: läsande scope, ägarens eget konto, ingen token i repot, och mcp-gsc som första kandidat

**Varför:** Kirurgen parkerade RoboNuggets-videon och mcp-gsc tills den första kunden är lanserad, men sokkonsol.md rad 39–40 säger bara att ett API-verktyg byggs då, inte på vilka villkor. Den session som bygger det ska inte behöva välja: mcp-gsc (MIT, d49eea9) gör våra läsningar i tjugo verktyg men begär skrivande scope och ber kunden ge ett servicekonto full åtkomst, vilket strider mot att verksamheten äger egenskapen och lägger till oss som användare (rad 12).

**Förslag:** kunskap/sokkonsol.md rad 39–40: tre rader. Verktyget läser bara (scope webmasters.readonly); det loggar in med ägarens eget Google-konto som verksamheten lagt till som användare, aldrig ett servicekonto på kundens egendom; token sparas utanför repo och underlag/. Första kandidat att pröva framför ett eget skript: github.com/AminForou/mcp-gsc @ d49eea9 (MIT), med scopet ändrat till läsande, destruktiva verktyg avstängda och bara läsande verktyg i allowedTools; se registerposten 2026-10-03.

**Klart när:** sokkonsol.md har de tre raderna med scope, konto, tokenplats och kandidaten; grep efter webmasters.readonly i kunskap/ träffar sokkonsol.md

**Vilande (2026-10-05):** Avstämt 2026-10-05: konto- och tokenvillkoren står redan i sokkonsol.md; kvar är scopet webmasters.readonly, förbudet mot servicekonto på kundens egendom och kandidaten. Skrivs i samma commit som Googles linje för generativ AI-sök.
