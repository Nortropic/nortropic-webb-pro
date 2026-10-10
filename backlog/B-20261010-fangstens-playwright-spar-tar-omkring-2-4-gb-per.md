---
id: B-20261010-fangstens-playwright-spar-tar-omkring-2-4-gb-per
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F11
skapad: 2026-10-10
prio: normal
steg: referenser (referens.py, inspektera.mjs), städningen
---
# Fångstens Playwright-spår tar omkring 2,4 GB per referenspaket

**Varför:** Kandidatprovet 2026-10-10: ett paket med åtta sajter tog 2,4 GB, nästan allt i 93 spårfiler (vy-*-spar.zip, upp till 88 MB styck, en per sida och bredd). Diskvakten stod samtidigt på 7,7 % ledigt. Spåren är privata och används för att följa en inspektion i efterhand (Playwright Trace Viewer), men de flesta öppnas aldrig.

**Förslag:** Mät vilka spår som används; behåll spåret för en bredd per sida (eller bara vid fel) och låt städningen gallra spår i äldre paket efter en fast tid. Ägaren beslutar om gallringen eftersom spåren är bevis.

**Klart när:** Ett paket av samma storlek tar mindre än en tredjedel av utrymmet, spårens gallring står i städregeln och referensjakt.md, och ett prov visar att ett fel fortfarande sparar sitt spår.
