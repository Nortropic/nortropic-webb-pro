---
id: B-20261001-prova-om-kirurgen-nar-modellen-byts-mot-agarens
status: vilande
kalla: bevakning
kallref: Omvärldsbevakning 2026-10-01: Anthropic Demystifying evals (regression vs kapacitet), Hamel Husain om TPR/TNR
skapad: 2026-10-01
prio: normal
steg: kirurgen
---
# Pröva om kirurgen när modellen byts, mot ägarens omdömen

**Varför:** Kirurgens domar kalibreras mot ägarens överprövningar i kunskap/KIRURG-OMDOMEN.md. När modellen byts kan omdömet glida utan att någon märker det; forskningen kallar det regressionsprov och rekommenderar mått per domklass, inte total andel.

**Förslag:** När minst tio poster är bedömda av ägaren: ett skript som kör kirurgen om på de bedömda länkarna med --bilder och jämför domarna mot ägarens, per domklass. Körs vid modellbyte.

**Klart när:** Skriptet finns och har körts en gång; resultatet står i REGISTER.md.
