---
id: B-20261002-provet-listar-sajtens-utgaende-lankar-och-om-de
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · sdmg15/Best-websites-a-programmer-should-visit
skapad: 2026-10-02
prio: normal
steg: steg 6 (prov), kontroller/standard_kontroll.py
commit: 19286c5
andrad: 2026-10-03T00:33Z
---
# Provet listar sajtens utgående länkar och om de svarar, med vitlista för domäner som stoppar robotar

**Varför:** Källan (dömd nej) kör en länkkontroll över sin README i CI med en vitlista för sajter som blockerar kontrollen; vårt prov läser bara interna adresser (standard_kontroll.py rad 118) och punkt 7.4 kräver länk till omdömena utan att pröva att den går dit. I A/B-domen 2026-10-02 kunde ägaren inte se vilken plattform omdömena låg på (LARDOMAR.md rad 102), och en felaktig Reco- eller Hitta-länk i sidfoten är ett förtroendefel som ingen grind fångar i dag.

**Förslag:** kontroller/standard_kontroll.py: en info-rad (inte F) per extern adress i dist/ som svarar 400+ eller inte alls på ett HEAD-anrop med GET som reserv och kort timeout; adresser i en liten vitlista (t.ex. google.com/maps, facebook.com, instagram.com) rapporteras som 'ej prövad'. Resultatet som en tabell 'Utgående länkar' i prov/STATUS.json och rapporten (steg 7). Ingen nätkontroll i rokprovet: hoppa över när miljövariabeln PROV_OFFLINE är satt.

**Klart när:** kontroller/rokprov.sh grönt; ett bygge visar tabellen i rapporten; en avsiktligt felstavad omdömeslänk i ett provbygge ger en info-rad.

**Klar (2026-10-03):** tabellen i standard.md och STATUS.json; felstavad länk ger info; rapportens punkt 14; rökprov grönt
