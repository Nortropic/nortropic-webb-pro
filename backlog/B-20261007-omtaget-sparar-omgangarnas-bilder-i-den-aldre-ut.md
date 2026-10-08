---
id: B-20261007-omtaget-sparar-omgangarnas-bilder-i-den-aldre-ut
status: ersatt
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#BÖR-3
skapad: 2026-10-07
prio: normal
steg: main: kontroller/atelje.py (ta_bort_beslut), kontroller/rokprov/revision/prov_revision.py
andrad: 2026-10-08T14:09Z
---
# Omtaget sparar omgångarnas bilder i den äldre utforskningen innan något raderas

**Varför:** Vinnaren, slutdomen, tidigare körningar och prototypen sparas, men omgångarnas bilder i den äldre utforskningen med riktningar, som ägaren dömt blint i dashboarden, raderas utan att sparas. I granskarens scenario sparades 0 av 30 dömda bilder. Ingen kund använder vägen i dag. BESLUT.md och skapandeflodet.md säger nu undantaget.

**Förslag:** Spara omgångarnas dömda bilder med sha256 och domraderna i omtag/<stämpel>/, som kandidaterna, eller vägra omtaget i den vägen.

**Klart när:** Granskarens scenario sparar 30 av 30 dömda bilder före raderingen, och undantaget stryks ur texterna.

**Ersatt (2026-10-08):** Backlogavstämningen 2026-10-08: gäller den äldre utforskningen med riktningar (NWP_KANDIDATFLODE=av), som ingen kund använder (BESLUT 2026-10-07 omtagens jämförelsepunkter: undantaget står kvar); kandidatflödet sparar det dömda
