---
id: B-20261010-en-bild-cdn-som-vagrar-fangstens-webblasare-403
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F14
skapad: 2026-10-10
prio: normal
steg: referenser (referens.py, referenskontrakt)
---
# En bild-CDN som vägrar fångstens webbläsare (403) lämnar sidan delvis fångad

**Varför:** Kandidatprovet 2026-10-10: Wix- och Webflow-CDN:er svarade 403 på egna bilder hos två av fyra branschsajter, så sidorna fälldes fast vyerna fångats med status 200. Gjort (ägarens beslut 2026-10-10, BESLUT.md): sidan märks 'delvis fångad: bilder vägrade av CDN' med de saknade adresserna i PAKET.json, PAKET.md och arbetsytan, och den bär bara kontakt, bokning, navigation och interaktion; kontraktet räknar en branschsajt med sådana sidor bara för de funktionsuppgifter den deklarerar. Återstår: orsaken till vägran är inte utredd (troligen huvudlös webbläsare, saknad Referer eller CDN:ens bot-skydd), och bilderna saknas fortfarande för bildregi, typografi, komposition och färg.

**Förslag:** Mät vilka begäranden CDN:en vägrar (huvuden, Referer, användaragent) i ett avgränsat prov mot en publik sida; inför bara en ändring som håller fångsten läsande och inom webbläsarhjälparens policy. Bot-skydd kringgås aldrig.

**Klart när:** Orsaken är belagd med ett prov, och antingen fångas bilderna utan att policyn ändras (prov i prov_referenskontrakt eller prov_revision) eller så står gränsen i referensjakt.md med orsaken.
