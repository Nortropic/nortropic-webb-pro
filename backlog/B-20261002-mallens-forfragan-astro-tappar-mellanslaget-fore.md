---
id: B-20261002-mallens-forfragan-astro-tappar-mellanslaget-fore
status: klar
kalla: bygge
kallref: kunder/lulea-snickaren-aby/RAPPORT.md
skapad: 2026-10-02
prio: normal
steg: 5
commit: b4d579e
andrad: 2026-10-02T17:17Z
---
# Mallens Forfragan.astro tappar mellanslaget före integritetslänken: 'förfrågan.Så hanterar vi personuppgifter'

**Varför:** Granskaren (omgång 1) såg '…svara på din förfrågan.Så hanterar vi personuppgifter' på /kontakt/ i 390; slot-fallbackens radbrytning försvinner när Astro komprimerar. Samma sorts fel som ägaren påpekade i L1 (').Läs').

**Förslag:** mall/astro/src/components/Forfragan.astro: skriv fallbacken på en rad med {' '} före <a href="/integritet/">, som bygget lulea-snickaren-aby gjorde i sin kopia.

**Klar (2026-10-02):** {' '} i mallen; standarden 9.4 fångar meningar som löper ihop (hittade också L1:s ').Läs')
