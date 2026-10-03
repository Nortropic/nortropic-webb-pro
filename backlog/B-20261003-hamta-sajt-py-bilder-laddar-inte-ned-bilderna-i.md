---
id: B-20261003-hamta-sajt-py-bilder-laddar-inte-ned-bilderna-i
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 1.2
---
# hamta_sajt.py --bilder laddar inte ned bilderna i ett inbäddat Instagramflöde

**Varför:** Holms startsida hade Smash Balloon-flödet med tio egna bilder i data-full-res; hämtningen såg bara platshållaren. Bygget skrev underlag/holms-konditori-abx/skript/instagram_bilder.py och fick åtta av sajtens bästa bilder (kanelbullar, blåbärskakor, disken).

**Förslag:** kontroller/hamta_sajt.py: läs data-full-res och data-img-src-set i instagram-feed och ladda ned dem till bilder/instagram/ med inläggets text (alt) i SIDOR.md.
