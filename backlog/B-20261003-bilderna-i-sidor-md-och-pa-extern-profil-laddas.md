---
id: B-20261003-bilderna-i-sidor-md-och-pa-extern-profil-laddas
status: klar
kalla: bygge
kallref: kunder/salong-kreativ/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 1
commit: ff49398
andrad: 2026-10-03T09:50Z
---
# Bilderna i SIDOR.md och på extern profil laddas ned för hand med skript

**Varför:** Steg 1 säger curl per bild. Bygget skrev underlag/salong-kreativ/skript/hamta_bilder.py och hamta_bd_bilder.py för att hämta elva bilder från egna sajten och sex från Bokadirekts CDN; en bild (k2.jpg, sajtens bästa) låg på servern men var inte länkad och hittades bara genom att pröva filnamnsmönstret k1–k6.

**Förslag:** kontroller/hamta_sajt.py får flaggan --bilder som laddar ned raderna märkta foto/okänd till underlag/<slug>/bilder/ och provar närliggande filnamn i samma uppladdningsmapp (k1…kN); hamta_bokadirekt.py (se posten om Bokadirekt) laddar profilens galleri.

**Klar (2026-10-03):** hamta_sajt.py --bilder med närliggande filnamn; Bokadirekts galleri laddas inte, bildadresserna står i bokadirekt-state.json
