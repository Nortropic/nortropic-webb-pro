---
id: B-20261002-sidor-md-sorterar-bildlistan-troliga-foton-forst
status: pagar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · unclecode/crawl4ai
skapad: 2026-10-02
prio: normal
steg: 1 (underlag: bilderna)
andrad: 2026-10-03T00:05Z
---
# SIDOR.md sorterar bildlistan: troliga foton först, ikoner, logotyper och knappbilder för sig, så att steg 1.2 hittar verksamhetens egna bilder snabbare

**Varför:** Egen innovation ur crawl4ai (dom nej): hamta_sajt.py listar alla bildadresser platt (72 på sundbomsel.se) och lämnar sorteringen till bygget, trots att ägarens domar L2 och L3 gör bildunderlaget till ett krav. Crawl4ai sållar bilder med billiga regler ur HTML (förälder eller adress med icon, logo eller button; width och height över 150; srcset eller picture; alt) innan de räknas, utan webbläsare.

**Förslag:** kontroller/hamta_sajt.py: bildtabellen i SIDOR.md får kolumnen 'trolig typ' (foto, logga/ikon, okänd) ur uppgifter verktyget redan läser eller lätt kan läsa med en taggstack: bildens och närmaste föräldras class samt adressen (icon, logo, button, sprite, favicon, emoji, avatar), width- och height-attribut under 150, filändelsen svg, och srcset, picture eller en jpg/webp-adress som tecken på foto; listan sorteras foto först. bygg-sajt/SKILL.md steg 1 punkt 2 (rad 75–79): ladda ner ur raderna märkta foto och kontrollera dem märkta okänd. Inga nya beroenden.

**Klart när:** SIDOR.md för en känd sajt (sundbomsel.se) visar kolumnen och fotona på de 15 handlistade sidorna står före ikoner och loggor; kontroller/rokprov.sh slutar grönt
