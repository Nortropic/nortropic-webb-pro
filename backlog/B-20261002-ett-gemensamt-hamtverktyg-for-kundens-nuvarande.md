---
id: B-20261002-ett-gemensamt-hamtverktyg-for-kundens-nuvarande
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · firecrawl/firecrawl
skapad: 2026-10-02
prio: normal
steg: 1 (hämta det publika, innehållsinventering)
commit: 3087e5c
andrad: 2026-10-02T15:55Z
---
# Ett gemensamt hämtverktyg för kundens nuvarande sajt i steg 1, i stället för att varje bygge skriver egna hämt- och lässkript

**Varför:** Egen innovation ur Firecrawl (dom nej): fyra byggen har skrivit var sina hamta.py/las.py, sundboms-el med en handskriven sidlista, så inventeringen ser olika ut varje gång och kostar tid. Ett verktyg som hittar adresserna via sitemap.xml och interna länkar och sparar text, länkar och bilder per sida gör steg 1 smartare och jämförbart mellan byggen.

**Förslag:** Nytt kontroller/hamta_sajt.py (bara GET, samma domän, högst 40 sidor, robots.txt respekteras): läser sitemap.xml och följer interna länkar från startsidan, sparar underlag/<slug>/kalla/<sida>.html och .txt (titel, meta, rubriker, text, länkar, bilder inkl. data-src/srcset och CSS-bakgrunder, som paint-it-black-maleri/skript/las.py) och skriver kalla/SIDOR.md med alla adresser, statuskod och ordantal. I .claude/skills/bygg-sajt/SKILL.md steg 1 punkt 1 och 2: hänvisa till verktyget för deras webbplats och till bildlistan i SIDOR.md för nedladdningen; WebFetch kvar för Google-profil och kanaler.

**Klart när:** kontroller/hamta_sajt.py finns och hämtar en känd sajt (t.ex. sundbomsel.se) till en tillfällig katalog med samma sidor som underlag/sundboms-el/kalla/ eller fler; bygg-sajt steg 1 hänvisar till det; kontroller/rokprov.sh slutar grönt

**Klar (2026-10-02):** hamta_sajt.py; sundbomsel.se 40 sidor inkl. alla 15 handlistade; steg 1 pekar på det; rökprov grönt
