---
id: B-20261002-stilrapporten-mater-sex-renderade-monster-ur-gst
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · garrytan/gstack
skapad: 2026-10-02
prio: normal
steg: 6 (provets stilrapport) och granskaren
commit: 06dafb5
andrad: 2026-10-02T15:34Z
---
# Stilrapporten mäter sex renderade mönster ur gstacks designkatalog: innehåll dolt i vila, radlängd, radhöjd i brödtext, marginaljusterad text, centrerad text och en enda stor radie

**Varför:** Ta in: gstacks katalog (lib/design-catalog.ts, delvis ur pbakaus/impeccable) har ett sextiotal mönster med mätbara trösklar; vår stil.mjs prövar ungefär tio och saknar dessa sex, som alla går att läsa ur den renderade sidan utan att köra något ur källan. GRANSKARE.md rad 45 säger att sida.mjs ger radlängder, men den mäter bara radhöjd (sida.mjs rad 113), så granskaren lovas ett mått som inte finns.

**Förslag:** kontroller/stil.mjs, i matPaSidan() och varningarna (info, aldrig grind): (1) element i main med opacity 0 eller visibility hidden vid laddning som blir synliga först efter skroll (innehåll dolt i vila); (2) radlängd i tecken för main p (bredd delat med teckenbredd), varning utanför 45-75; (3) radhöjd under 1,4 för main p; (4) text-align justify i main; (5) mer än 60 procent av textblocken i main centrerade; (6) mer än 80 procent av de rundade elementen delar en radie på 16 px eller mer. Radlängden skrivs också i STIL.md så att granskaren har den; kritik/GRANSKARE.md rad 45 pekar på stilrapporten för radlängder i stället för på sida.mjs. Ingen kod kopieras; trösklarna skrivs med egna ord och källan anges i filhuvudet. Rökprovet ska sluta grönt.

**Klart när:** STIL.md visar radlängd per sida och vy och varnar för de sex mönstren på en provsida som har dem; GRANSKARE.md lovar inget mått som saknas; kontroller/rokprov.sh grönt.

**Klar (2026-10-02):** sex mönster i stil.mjs, radlängd i STIL.md, granskaren läser stilrapporten
