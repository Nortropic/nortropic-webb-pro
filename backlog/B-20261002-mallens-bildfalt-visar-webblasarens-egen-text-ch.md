---
id: B-20261002-mallens-bildfalt-visar-webblasarens-egen-text-ch
status: klar
kalla: bygge
kallref: kunder/lulea-snickaren-aby/RAPPORT.md
skapad: 2026-10-02
prio: normal
steg: 5
commit: b4d579e
andrad: 2026-10-02T17:17Z
---
# Mallens bildfält visar webbläsarens egen text ('Choose File / No file chosen')

**Varför:** Granskaren noterade i omgång 2–4 att filfältet 'Bild på jobbet (valfritt)' visar webbläsarens engelska text i provets motor; på en svensk telefon blir det troligen svenska, men det går inte att styra.

**Förslag:** mall/astro/src/components/Forfragan.astro: dölj input[type=file] visuellt men tillgängligt och lägg en egen etikett/knapp 'Välj bild' (label for=ff-bild) med vald filnamn som text; fungerar utan JS om etiketten är label.

**Klar (2026-10-02):** egen knapp Välj bild som etikett, filnamn med JS, fokus syns på knappen; fungerar utan JS
