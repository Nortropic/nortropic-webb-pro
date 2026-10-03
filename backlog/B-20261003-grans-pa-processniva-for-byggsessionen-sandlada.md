---
id: B-20261003-grans-pa-processniva-for-byggsessionen-sandlada
status: pagar
kalla: bevakning
kallref: Codex-revision 2026-10-03, F1; code.claude.com/docs/en/sandboxing
skapad: 2026-10-03
prio: hog
andrad: 2026-10-03T22:09Z
---
# Gräns på processnivå för byggsessionen: sandlåda för filskrivning och nät (revisionen F1)

**Varför:** Codex-revisionen 2026-10-03 (F1, hög): kor.sh tillåter python, node, npx och curl i former som når förbi varje Edit- och Write-regel; ett eget skript under underlag/<slug>/skript/ kan ändra kontrollerna, köra git själv (förbi commitvakten) eller göra POST-anrop ut. Tillåtelselistan smalnades (bara kontroller/-verktyg, egna skript under underlag/, npx astro, curl -o underlag/) och de skyddade filernas innehåll jämförs fil för fil efter körningen, men det stoppar inte exfiltration eller git via subprocess. Claude Code har en inbyggd sandlåda (settings sandbox: filesystem.denyWrite, filesystem.denyRead, network.allowedDomains; kan ges per anrop med --settings till claude -p, docs code.claude.com/docs/en/sandboxing).

**Förslag:** Prova sandlådan i ett helt bygge mot en kopia (port- och rotförskjuten) innan den slås på i kor.sh: denyWrite för kontroller/, kritik/, kunskap/, mall/, .claude/, dashboard/, kor.sh, LARDOMAR.md och .git/ utom det commitvakten släpper; denyRead för ~/.nortropic-hemligheter; nätet begränsat till verksamhetens domän, registry.npmjs.org, fontsource och det WebFetch behöver (WebFetch är ett verktyg, inte Bash). Risk att pröva: Playwright/Chromium, Lighthouse och npm install under seatbelt, och att crawlmålen (verksamhetens domän) måste in i allowedDomains per körning.

**Klart när:** Ett fullt bygge (prov grönt, granskning godkänd) har körts med sandlådan på, och ett syntetiskt försök att skriva i kontroller/ och att POST:a till en extern adress från ett skript under underlag/<slug>/skript/ nekas av sandlådan, inte av vakten efteråt.

**Pagar (2026-10-03):** steg 1 (gren sandlada-20261003): kontroller/sandlada.py, sandlada-domaner.txt, sandlada_prov.sh, kor.sh NWP_SANDLADA, ingen git i bygget. Blockerat: managed-settings.json låser sandbox.enabled=false och går före --settings; provet visar ingen proxy och inget stoppat. Ägaren ändrar filen (sudo), sedan fullt bygge i kopia
