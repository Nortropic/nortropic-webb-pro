---
id: B-20261003-standardkontrollens-lista-over-lokala-typer-sakn
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 6
---
# Standardkontrollens lista över lokala typer saknar Bakery, CafeOrCoffeeShop och andra FoodEstablishment-undertyper

**Varför:** Startsidans JSON-LD med @type Bakery gav felet 7.3 startsidan saknar JSON-LD för verksamheten; bygget lade till FoodEstablishment bara för att kontrollen skulle känna igen typen.

**Förslag:** kontroller/standard_kontroll.py LOKALA_TYPER: lägg till Bakery, CafeOrCoffeeShop, IceCreamShop, BarOrPub och övriga FoodEstablishment- och Store-undertyper (eller pröva mot schema.org-hierarkin).
