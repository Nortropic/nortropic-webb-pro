---
id: B-20261002-mat-kontextdjupet-per-bygge-i-a-b-posten-storsta
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · JuliusBrussee/caveman
skapad: 2026-10-02
prio: normal
steg: A/B-mätningen (kontroller/ab.py) och ramarna för körningen
commit: 2779656
andrad: 2026-10-03T00:00Z
---
# Mät kontextdjupet per bygge i A/B-posten: största kontexten och antal meddelanden över halva fönstret

**Varför:** Domen över caveman var nej, men dess mätidé bär: hur djupt en session går i modellens fönster är en kvalitetssignal som vi inte skriver upp. I det blinda effortparet 2026-10-02 nådde A 813 339 tokens läst kontext och låg över 500 000 i 238 av 653 meddelanden, B nådde drygt 500 000 i de sista 77 av 562, och ägaren valde B; ett par bevisar inget, men variabeln ska finnas när nästa par döms.

**Förslag:** kontroller/ab.py matt() (rad 45–62) läser redan körningens korning-*.jsonl: lägg till kontext_max (största summan av input_tokens, cache_creation_input_tokens och cache_read_input_tokens i ett meddelande) och over_halva (antal meddelanden där summan överstiger halva modellens fönster; opus[1m] = 500 000), så att de följer med i A/B-posten och i LARDOMAR.md:s AB-rad bredvid turer och minuter. Ingen regel och ingen grind, bara mätning.

**Klart när:** ab.py skriver kontext_max och over_halva för båda armarna i nästa A/B-post, och de två talen för paret lulea-snickaren-abx/-aby stämmer med loggarna (813 339 och 238 respektive cirka 502 000 och 77).

**Klar (2026-10-03):** ab.py mäter kontext_max och over_halva; paret: 694 131/243 och 563 203/79 ur loggarna (postens 813 339 gick inte att återfinna)
