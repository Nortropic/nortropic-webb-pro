---
id: B-20261003-spanaren-jamfor-en-github-release-med-versionen
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Lighthouse v13.5.0 (GoogleChrome/lighthouse, release)
skapad: 2026-10-03
prio: normal
steg: spanaren (kontroller/spana.py), kirurgen
commit: c4a092c
andrad: 2026-10-08T15:45Z
---
# Spanaren jämför en GitHub-release med versionen i kontroller/package.json och märker den som redan i bruk eller som uppdateringsfråga

**Varför:** Kirurgens dom över Lighthouse v13.5.0 blev nej eftersom det är exakt den version provet redan kör (kontroller/package.json rad 15, lighthouseVersion 13.5.0 i varje byggs lighthouse.json); spanaren matchade bara orden agent, audit, plugin och release. Fyra releaseflöden i kunskap/spaning-kallor.md (Astro rad 83, Lighthouse rad 100, axe-core rad 101, Playwright rad 102) gäller paket vi pinnar, så samma tomma intag återkommer vid varje release.

**Förslag:** kontroller/spana.py, i rss() för Atom-flöden från github.com/<ägare>/<repo>/releases.atom: läs taggen ur länken (…/releases/tag/vX.Y.Z), slå upp paketet i kontroller/package.json (en liten tabell repo → paketnamn: GoogleChrome/lighthouse → lighthouse, dequelabs/axe-core → axe-core, microsoft/playwright → playwright, withastro/astro → astro i mall/package.json). Är taggen lika med den pinnade versionen: sätt status 'redan i bruk' och lägg inte kandidaten i kön. Är taggen nyare: lägg 'pinnad X, release Y' i kandidatens varning så att kirurgen bedömer en uppdatering i stället för att läsa releasenoterna blint. Är repot inte i tabellen: som i dag.

**Klart när:** spana.py läser taggen ur GitHub-releaseflöden, jämför med kontroller/package.json och mall/astro/package.json och märker en pinnad version "redan i bruk" utanför kön; en nyare får varningen "pinnad X, release Y"; fixturer i kontroller/rokprov/spaning/ med en tagg lika med pinnad och en nyare.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord; dagens skarpa fall är axe-core 4.13.0 och playwright 1.63.0 som står som nya trots pinnade versioner. Samma ändringsställe som YouTube-posten (en commit, två poster). Färdigkriteriet omskrivet i avstämningen; tidigare: "spana.py --torr mot Lighthouse-flödet visar v13.5.0 som 'redan i bruk 13.5.0' och en påhittad nyare tagg i ett provflöde får varningen 'pinnad 13.5.0, release 13.6.0'; kontroller/rokprov.sh grönt"

**Ersatt (2026-10-08):** Backlogavstämningen 2026-10-08: sammanförd i B-20261003-spanaren-poangsatter-per-omrade-titel-2-negativa (samma körväg (spana.py:s poängsättning och märkning))
