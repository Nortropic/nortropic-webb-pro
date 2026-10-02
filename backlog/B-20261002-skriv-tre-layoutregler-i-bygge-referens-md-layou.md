---
id: B-20261002-skriv-tre-layoutregler-i-bygge-referens-md-layou
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · foundation/yeti
skapad: 2026-10-02
prio: normal
steg: 5 (bygge); kunskap/bygge-referens.md
commit: 930978d
andrad: 2026-10-02T23:42Z
---
# Skriv tre layoutregler i bygge-referens.md: layouten äger avståndet, en skala för text och luft, tröskel per komponent före viewport-brytpunkt

**Varför:** Kirurgens dom om foundation/yeti är nej (ramverk med standardutseende, karusell och hamburgare), men dess metod är Every Layout, som teoretisk-grund.md redan namnger som princip utan att bygge-referens.md gör något av den. Luft och hierarki är den enda dimensionen som fått Okej i alla tre ägardomar (LARDOMAR.md rad 35, 60, 84), och det är just rytmen mellan sektioner och inuti dem som de reglerna styr.

**Förslag:** kunskap/bygge-referens.md, efter rad 10 under Krav på resultatet: tre punkter. (1) Avståndet ägs av layouten: gap på föräldern (stack, kluster, grid), aldrig marginaler på barnen; ett undantag skrivs på barnet och syns därför i samma fil. (2) Text och luft delar en skala ur en bas och en kvot, som CSS-variabler (byggstandarden 3.1), så att sektionsavstånd, radavstånd och rubrikstorlek är steg på samma trappa. (3) En sektion byter form vid sin egen tröskel (container query eller flex-basis mot en bredd ur skalan), inte vid en viewport-brytpunkt; media queries bara för besökarens preferenser (färgschema, rörelse, print). Källa att ange i raden: Bell & Pickering (2019), Every Layout.

**Klart när:** Raderna står i kunskap/bygge-referens.md; nästa bygges JAMFORELSE.md under 4. Luft och hierarki hänvisar till dem; rokprov.sh grönt.

**Klar (2026-10-02):** tre punkter under Krav på resultatet; prövas i nästa bygges JAMFORELSE.md
