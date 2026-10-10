---
id: B-20261010-kundvakten-sparrar-branschord-som-ingar-i-kunden
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F2
skapad: 2026-10-10
prio: normal
steg: kundvakten, referenser (forska)
---
# Kundvakten spärrar branschord som ingår i kundens namn

**Varför:** När kundens namn innehåller kategorins ord spärrar kundvakten också sökningar på själva kategorin (provet 2026-10-10: en sökning på kategoriordet nekades eftersom det ingår i det fiktiva namnet). Researchen använder synonymer, men sökningen blir sämre och spärren syns inte för ägaren.

**Förslag:** Pröva om ett namnord som också är kundens kategori i VERKSAMHET.json får släppas när det står utan namnets övriga ord. Gränsen rör datagränsen, så ägaren beslutar efter ett underlag med prov för läckage och falsklarm.

**Klart när:** Underlaget och ägarens beslut finns; vid ja släpper kundvakten kategoriordet ensamt och spärrar det tillsammans med namnets övriga ord, med prov i prov_referenskontrakt eller kundvaktens prov.
