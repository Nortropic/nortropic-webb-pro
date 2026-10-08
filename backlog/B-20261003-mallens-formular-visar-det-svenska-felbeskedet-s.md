---
id: B-20261003-mallens-formular-visar-det-svenska-felbeskedet-s
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Chrome for Developers, Modern Web Guidance: Swipe to remove + GoogleChrome/modern-web-guidance
skapad: 2026-10-03
prio: normal
steg: 5 (mallens formulär)
commit: 405a0be
andrad: 2026-10-08T15:24Z
---
# Mallens formulär visar det svenska felbeskedet som text vid fältet utan JavaScript, med :user-invalid i CSS

**Varför:** Egen innovation ur kirurgens intag av modern-web-guidance (domen över källan är ta in). Byggstandarden 6.2 kräver svenska felmeddelanden som text vid fältet med aria-describedby, men mallens Forfragan.astro fyller texten med JavaScript vid invalid, så utan JS visas webbläsarens bubbla på webbläsarens språk; källans forms-guider visar felet i ren CSS först när besökaren lämnat fältet eller försökt skicka (validate-input-after-interaction.md rad 9 och 66–74, required-field-feedback.md rad 52–59), så beskedet håller också utan JS.

**Förslag:** mall/astro/src/components/Forfragan.astro: skriv beskeden ur data-saknas (och data-format för telefonfältet) som text i felelementen (id ur aria-describedby) redan i HTML:en, dolda med CSS, och visa dem med 'input:user-invalid + .ff-fel' respektive textarea; telefonfältets formatbesked får ett eget element som visas vid :user-invalid när fältet inte är tomt (:not(:placeholder-shown) eller en tom placeholder). Skriptet (rad 61–95) behåller fokus till första felet, aria-invalid, setCustomValidity och knapplåsningen; .ff-fel:empty-regeln (rad 102) ersätts av regeln ovan. kunskap/forfragan.md: en rad om att felbeskeden är svenska också utan JavaScript.

**Klart när:** Med JavaScript avstängt visar ett tomt namnfält det svenska beskedet som text under fältet när besökaren lämnar fältet eller trycker Skicka, och 'abc' i telefonfältet visar formatbeskedet; med JavaScript på är beteendet som förut (fokus till första felet, aria-invalid); POST utan JS fungerar; axe 0 fel; kontroller/rokprov.sh slutar grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord (tomma ff-fel som skriptet fyller, ingen :user-invalid). Hör ihop med den klara B-20261002-mallens-formular-visar-ett-felbesked-utan-javasc, som löste återkomsten; denna gäller fältbeskeden.
