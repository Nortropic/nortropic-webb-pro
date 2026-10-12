---
id: B-20261012-underhallet-foljer-bara-de-intagna-filerna-nar-e
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-13 · blader/humanizer
skapad: 2026-10-12
prio: normal
steg: underhållet (kontroller/underhall.py, kontroller/verktygslada.py)
---
# Underhållet följer bara de intagna filerna när en skills källa är repots rot (blader/humanizer)

**Varför:** Humanizer följer sedan 2026-10-13 blader/humanizer, där skillen ligger i repots rot. plan_for_skill jämför då hela repot: varje utelämnad fil som upphovet ändrar blir en krock, och nya filer i repot läggs i mappen (plugin.json fälls sedan som konfigurationsfil). Nästa version stoppas därför, fast SKILL.md slås ihop rent; prövat med samma mapp på v3.0.0 mot v3.1.0: krockar i README.md, AGENTS.md, plugin-manifesten och scripts/validate-package.py.

**Förslag:** kontroller/underhall.py plan_for_skill: när källans väg är repots rot jämförs bara filerna som finns i mappen; en fil som saknas i mappen hoppas över i stället för att bli krock, och en ny fil i källan nämns i rapporten men läggs inte i mappen. kontroller/verktygslada.py EGNA_TILLAGG: lägg till NORTROPIC.md och ta bort LICENSE-nous-research. Ett prov i kontroller/rokprov/revision med en attrappklon i rotform, och provfilen i rökprovets lista. Ändringen gäller den automatiska intagsvägen och granskas som en ändring i underhållet.

**Klart när:** En mapp som humanizer på v3.0.0 mot v3.1.0 ger en plan med bara mappens egna filer (SKILL.md sammanslagen) och inga krockar, och rökprovet slutar grönt.
