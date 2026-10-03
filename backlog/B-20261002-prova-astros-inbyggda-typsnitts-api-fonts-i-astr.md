---
id: B-20261002-prova-astros-inbyggda-typsnitts-api-fonts-i-astr
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · withastro/astro
skapad: 2026-10-02
prio: normal
steg: 5 (bygge: mallen och typsnitten), byggstandarden 4.3
commit: 3e4a61f
andrad: 2026-10-03T00:52Z
---
# Pröva Astros inbyggda typsnitts-API (fonts i astro.config.mjs och <Font preload />) i mallen i stället för handskrivna @font-face, reservtypsnitt och preload

**Varför:** Prova: Astro 7, som mallen redan kör, räknar reservtypsnittets size-adjust, ascent-, descent- och line-gap-override ur typsnittsfilens mått och skriver @font-face, hashad fil, preload-länk och CSP-hash själv. Tre av fem byggen saknade reserven helt och de två som hade den gissade måtten för hand; går provet grönt med CSP utan överträdelser ersätter det fyra handgrepp per bygge.

**Förslag:** mall/astro/astro.config.mjs: fonts: [{ provider: fontProviders.local(), name: '<familj>', cssVariable: '--typsnitt', fallbacks: ['sans-serif'], options: { variants: [{ src: ['./src/assets/fonts/<fil>.woff2'], weight: '400 900' }] } }] (bygget byter familj och fil); mall/astro/src/layouts/Bas.astro: <Font cssVariable='--typsnitt' preload /> i head, eller via slot name=head från sajtens layout; mall/astro/README.md rad 15, kunskap/byggstandard.md rad 136 och .claude/skills/bygg-sajt/SKILL.md rad 38–42: typsnittsfilen i src/assets/fonts/ i stället för public/fonts/, och att reserv och preload kommer från API:t. Prövas i nästa bygge, inte blint: provet grönt (4.3 familjer och storlek läser dist/_astro, 8.2 CSP 0 överträdelser i konsolen), reservens size-adjust jämförs med den handskrivna i lulea-snickaren-abx (103 %), CLS i Lighthouse mobil.

**Klart när:** Ett bygge med fonts-API:t har gått grönt genom provet med CSP 0 överträdelser, kontroller/rokprov.sh är grönt, och mallen samt de tre textställena är ändrade; annars sätts posten avvisad med skäl.

**Klar (2026-10-03):** provbygge av mallen grönt (CSP 0, CLS 0, reserv 104,5 % ur filen); mallen, README, standarden och skillen ändrade; första kundbygget med API:t är nästa bekräftelse
