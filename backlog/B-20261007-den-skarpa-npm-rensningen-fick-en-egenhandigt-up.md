---
id: B-20261007-den-skarpa-npm-rensningen-fick-en-egenhandigt-up
status: klar
kalla: granskning
kallref: granskningar/GR-20261006-r94-slut.md
fynd: GR-20261006-r94-slut#KAN-2
skapad: 2026-10-07
prio: normal
steg: kontroller/stadning.py (npm_rensa)
commit: 0a4d7b6
verifierad: GR-20261006-r98
verifierad_tid: 2026-10-07T02:03Z
andrad: 2026-10-07T02:03Z
---
# Den skarpa npm-rensningen fick en egenhändigt uppskattad cachesökväg

**Varför:** Verifieringen av r94: sökvägen följde inte npm:s regler (NPM_CONFIG_USERCONFIG, sista raden vinner, kommentarer, ${VAR}) och gavs som --cache, så fel _cacache kunde tömmas.

**Förslag:** Kör npm cache clean --force utan --cache; uppskattningen används bara i redovisningen.

**Klart när:** Rensningen låter npm avgöra cachen, och torrläget kör aldrig npm.

**Klar (2026-10-07):** Rättat i stadning-foljd-20261007.

**Verifierad (2026-10-07):** GR-20261006-r98: Verifieringen GR-20261006-r98: K2a–K2g röda; varje riktig npm i provet hade cachen i provets TMP.
