---
id: B-20261003-ikoner-mjs-gor-inte-favicon-svg-och-en-genomskin
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 5.3
---
# ikoner.mjs gör inte favicon.svg och en genomskinlig logga ur en rasterlogga med vit bakgrund

**Varför:** Holms logga finns bara som PNG med vit bakgrund; bygget skrev underlag/holms-konditori-abx/skript/gubben.mjs för att göra loggan genomskinlig i blått och vitt och lägga en inbäddad PNG i favicon.svg.

**Förslag:** kontroller/ikoner.mjs: flaggan --logga FIL som tar bort vit bakgrund, ger genomskinliga varianter i given färg och skriver public/favicon.svg.
