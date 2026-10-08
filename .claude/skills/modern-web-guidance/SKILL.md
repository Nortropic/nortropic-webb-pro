---
name: modern-web-guidance
description: Recept med webbläsarstöd och reserv per funktion för modern HTML, CSS och formulär, ur Chrome- och Edge-teamens guider. Används i bygg-sajt steg 5.3 och 5.5 när bygget skriver en komponent utanför mallen - formulärfel, bilder, rubriker, menyer, övergångar, kontrast, typsnittsreserv.
---

# Så används skillen i nortropic-webb-pro

Det här avsnittet gäller före allt annat i mappen. Källa, version, licens och de lokala ändringarna: `KALLA.md`.

- **Ordning:** byggstandarden (`kunskap/byggstandard.md`), ägarens beslut och domarna gäller före guiderna. En guide
  är ett recept för en komponent, inte en regel för sajten.
- **Hitta receptet:** Grep i `guides/` på funktionen eller uppgiften (till exempel `user-invalid`, `fetchpriority`,
  `text-wrap`), eller läs indexet `GUIDER.md`, och läs sedan guidens fil. Allt ligger i mappen: ingen sökning på nätet,
  ingen installation och ingen telemetri. En hänvisning i en guide är en sökväg i `guides/`.
- **Webbläsarstödet prövas:** raderna "Browser support … Supported by … Unsupported in …" i guiderna är genererade och
  kan vara fel. Slå upp funktionens status på MDN (avsnittet Browser compatibility) innan en reserv byggs eller hoppas
  över, och följ byggstandarden 3.8. Två rader stämmer inte med MDN enligt kirurgens granskning 2026-10-03:
  `guides/css/css-layout.md` rad 212–214 (anchor positioning) och `guides/ui-behaviors/swipe-to-remove.md` rad 465–467
  (`overscroll-behavior`).
- **Det som inte gäller här:** guidernas preconnect till andra ursprung, CDN, polyfills och inline-händelser
  (`onclick=`) i exemplen; standarden 4.4 och 8.2 styr resurserna och CSP. Mörkt läge bara när KONCEPT.md säger det.
  Karuseller aldrig (standarden 5.5). Guiderna under `built-in-ai/`, `pwa/`, `wasm/` och `webmcp/` hör inte till en
  verksamhets webbplats.
- **Klart:** det bygget tog ur en guide står i KONCEPT.md eller DESIGN.md med guidens sökväg, och för en funktion som
  inte är Baseline Widely available också MDN-statusen och reserven.

Indexet över de 177 guiderna, med sökväg och rubrik: `GUIDER.md`.
