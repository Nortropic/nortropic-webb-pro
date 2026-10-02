---
id: B-20261002-undersidor-under-en-oversikt-far-brodsmulor-och
status: pagar
kalla: dom
kallref: LARDOMAR.md · AB · 2026-10-02
skapad: 2026-10-02
prio: hog
steg: 5 och 6
andrad: 2026-10-02T16:57Z
---
# Undersidor under en översikt får brödsmulor och BreadcrumbList, och standarden prövar det

**Varför:** Ägaren (AB 2026-10-02): B har fyra tjänstesidor med brödsmulor och BreadcrumbList. Byggstandarden 7.3 nämner BreadcrumbList men standard_kontroll prövar det inte.

**Förslag:** standard_kontroll: varje sida två nivåer ned (till exempel /tjanster/tillbyggnad/) har en synlig brödsmulenavigering med länk till föräldern och BreadcrumbList i JSON-LD; annars fel 7.3. En rad i bygg-sajt steg 5.3.

**Klart när:** Standarden fäller en undersida utan brödsmulor; rökprovet prövar det
