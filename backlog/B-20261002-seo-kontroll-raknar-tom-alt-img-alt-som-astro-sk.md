---
id: B-20261002-seo-kontroll-raknar-tom-alt-img-alt-som-astro-sk
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren-aby/RAPPORT.md
skapad: 2026-10-02
prio: normal
steg: 6
---
# seo_kontroll räknar tom alt (<img alt>, som Astro skriver för alt="") som saknad alt

**Varför:** Tumnaglarna i startsidans tjänstelänkar fick alt="" för att inte upprepa länktexten (granskarens förslag); Astro renderar det som <img alt>, och seo-grinden blev röd med 4 fynd 'img utan alt'. Bygget fick i stället beskrivande alt + aria-hidden.

**Förslag:** kontroller/seo_kontroll.py: låt attrs() godta attribut utan värde (alt utan = är tom alt, giltigt för dekor); lägg ett prov med <img alt src=...>.
