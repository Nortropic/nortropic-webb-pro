---
id: B-20261001-helsidesbilderna-fran-inspektera-mjs-visar-lata
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
---
# Helsidesbilderna från inspektera.mjs visar lata bilder som tomma rutor

**Varför:** Luleå-Snickarens prov/inspektion/projekt/vy-390-hela.png visade tomma ramar för de flesta projektbilderna (loading=lazy) fast de laddar i 1440-bilden och i webbläsaren. Renderingsläsningen kan då dra fel slutsats.

**Förslag:** kontroller/webblasare/inspektera.mjs: skrolla sidan till botten och tillbaka, och vänta på bilderna, innan vy-<bredd>-hela.png tas.
