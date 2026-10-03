---
id: B-20261003-standardens-lankkontroll-ger-404-for-imy-se-som
status: klar
kalla: bygge
kallref: kunder/salong-kreativ/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 6
commit: abbc0bf
andrad: 2026-10-03T09:50Z
---
# Standardens länkkontroll ger 404 för imy.se som svarar 200 i webbläsare

**Varför:** prov/standard.md 7.4 rapporterade https://www.imy.se/ som 404 på integritetssidan. curl med en vanlig webbläsar-User-Agent gav 200 samma minut. Granskarna lyfte länken som möjligt fel i två omgångar.

**Förslag:** Länkkontrollen i kontroller/standard (utgående länkar) provar igen med en webbläsar-User-Agent innan den skriver 404, och skriver 'svarar 200 med webbläsarhuvud, nekar robotar' när bara roboten nekas.

**Klar (2026-10-03):** omprövning med webbläsarhuvud före 404
