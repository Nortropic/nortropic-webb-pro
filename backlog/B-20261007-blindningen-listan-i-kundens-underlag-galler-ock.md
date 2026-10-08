---
id: B-20261007-blindningen-listan-i-kundens-underlag-galler-ock
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r107.md
fynd: GR-20261007-r107#K2
skapad: 2026-10-07
prio: normal
steg: main: kontroller/kandidater.py (blind_nekas)
andrad: 2026-10-08T22:15Z
---
# Blindningen: listan i kundens underlag gäller också filer som uppstår efter starten

**Varför:** Listan i underlag/<slug> bygger på en uppräkning vid starten och på mönster. UPPTAGNA-VAL.md nekas bara om den finns vid starten. Det är en teoretisk lucka; inget skrivs dit under en skisskritik i dag utöver det mönstren täcker.

**Förslag:** Neka allt i underlag/<slug> utom listan med ett mönster som gäller också senare filer, om behörigheterna tillåter det.

**Klart när:** En fil som skapas i underlag/<slug> under kritikens session går inte att läsa.

**Vilande (2026-10-08):** Nattens uppdrag 2026-10-08/09, delvis i 3a1e19b: det systemet självt kan skriva i underlag/<slug>/ under en blind session nekas också när det uppstår efter starten (prov_skisskritik fall 10, rött mot 03fab0e). Kvar: en fil som något annat lägger dit under sessionen; behörigheterna kan inte säga allt utom listan. Väntar på ägarens beslut: en krok som prövar varje läsning, med ett verkligt sessionsprov, eller att täckningen räcker (RAPPORT-2026-10-08-natt-codex-rester-backlog).
