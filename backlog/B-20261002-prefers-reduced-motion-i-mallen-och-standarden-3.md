---
id: B-20261002-prefers-reduced-motion-i-mallen-och-standarden-3
status: pagar
kalla: dom
kallref: LARDOMAR.md · AB · 2026-10-02
skapad: 2026-10-02
prio: hog
steg: 5
andrad: 2026-10-02T16:54Z
---
# prefers-reduced-motion i mallen, och standarden 3.5 gäller också övergångar

**Varför:** Ägaren (AB 2026-10-02): A har prefers-reduced-motion i CSS:en, vilket B saknar. Standarden 3.5 fäller bara @keyframes och mjuk skroll, inte transition.

**Förslag:** Mallens Bas.astro får ett globalt @media (prefers-reduced-motion: reduce)-block som stänger av övergångar, animationer och mjuk skroll. standard_kontroll 3.5 räknar också transition och animation.

**Klart när:** Mallen har blocket; standarden fäller transition utan reduced-motion; rökprovet grönt
