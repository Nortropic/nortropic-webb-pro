---
id: B-20261002-gruppera-agarens-domar-och-granskarens-fynd-efte
status: klar
kalla: bevakning
kallref: OpenAI Cookbook, Building resilient prompts using an evaluation flywheel (okt 2025)
skapad: 2026-10-02
prio: normal
steg: 8
commit: d81d3fb
andrad: 2026-10-02T11:57Z
---
# Gruppera ägarens domar och granskarens fynd efter var femte dom

**Varför:** OpenAI Cookbook om eval-svänghjulet: sätt först fria etiketter på misslyckanden, gruppera dem sedan i kategorier med antal, och låt den största kategorin styra nästa ändring.

**Förslag:** Efter var femte dom: en session grupperar LARDOMAR.md och granskningarnas blockerande fynd i kategorier med antal och föreslår en textändring mot den största kategorin, som en vilande backlogpost.

**Klart när:** En grupperingsrapport finns efter femte domen.

**Klar (2026-10-02):** gruppera.py, startas efter var femte dom; provad på fyra domar
