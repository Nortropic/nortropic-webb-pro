---
id: B-20261010-skalets-skrivningar-okanda-kommandon-klassas-som
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F6
skapad: 2026-10-10
prio: normal
steg: kompetensens kvitto (bildkedja.bash_andring)
---
# Skalets skrivningar: okända kommandon klassas som oklara

**Varför:** bildkedja.bash_andring klassar ett Bash-anrop som läsande, ändrande eller oklart med prefixlistor (2026-10-10). Det finns ingen fullständig skalparser, så sammansatta eller ovanliga kommandon blir oklara och räknas varken som läsning eller skrivning i läsordningen.

**Förslag:** Räkna andelen oklara anrop i verkliga skapar- och helbyggestranskript; utöka listorna eller tolka de vanligaste formerna om andelen är hög. Pröva mot sparade transkript, inte bara fixturer.

**Klart när:** En mätning över minst fem verkliga transkript visar andelen oklara anrop före och efter, och prov_kompetensluckor täcker de nya formerna.
