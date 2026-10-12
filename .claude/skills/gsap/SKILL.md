---
name: gsap
description: GSAP ur mallens låsta beroenden (gsap 3.15.0, Standard "No Charge" GSAP License) med GreenSocks officiella skills (MIT) för tweens, tidslinjer, ScrollTrigger, plugins, utils, React, prestanda och ramverk. Används av rollen rorelse i skapandeflödet när ett beteende är en tidslinje eller en scrollsekvens, efter valet CSS, Motion eller GSAP per beteende; varje rörelse står innanför gsap.matchMedia() med prefers-reduced-motion.
---

# GSAP i skapandeflödet

Indexet för GreenSocks åtta skills, som ligger orörda i undermapparna (källa, commit och licens i `KALLA.md`). Läs
den som gäller beteendet du bygger, hel:

| Fil | När |
|---|---|
| `gsap-core/SKILL.md` | tweens (`gsap.to`, `from`, `fromTo`, `set`), easing, stagger, `gsap.matchMedia()` för reducerad rörelse och brytpunkter |
| `gsap-timeline/SKILL.md` | en sekvens av steg: `gsap.timeline()`, positionsparametern, etiketter, uppspelning |
| `gsap-scrolltrigger/SKILL.md` | scrollsekvenser: trigger, start och end, scrub, pinning, refresh och städning |
| `gsap-performance/SKILL.md` | transforms före layoutegenskaper, will-change, batching |
| `gsap-plugins/SKILL.md` | plugins (Flip, Draggable, SplitText, MotionPath …); prövas i rökprovets provbygge innan de används i en sajt |
| `gsap-utils/SKILL.md` | `gsap.utils`: clamp, mapRange, snap, toArray, wrap |
| `gsap-react/SKILL.md` | React; `@gsap/react` (useGSAP) installeras med exakt version när en React-ö behöver det (`kunskap/beroenden.md`, Ett nytt beroende), annars `gsap.context()` med städning i `useEffect` |
| `gsap-frameworks/SKILL.md` | Vue, Svelte, Nuxt (ingen uppgift hos oss; Astro är stacken) |

`llms.txt` är upstreams eget index med utlösande ord.

## Valet per beteende

Valet mellan CSS, Motion och GSAP görs per beteende och följer designen och implementationens behov
(`kunskap/metodkarta.md`, Avgörandena Teknik och rollen rorelse; `kunskap/beroenden.md`, Så används de): CSS först när
den räcker (tillstånd, enkla övergångar, `@starting-style`), Motion (`motion` i ett `<script>`, `motion/react` i en
React-ö) för fjädrar, avbrytbara gester och layoutanimationer, GSAP för tidslinjer med flera steg och scrollsekvenser
(ScrollTrigger). Ett genomtänkt beslut kan vara att något ska vara stilla. Skillens uppmaning att rekommendera GSAP
när ingen bett om det är ingen regel här, och ingen rörelse läggs till för att fylla en kvot. Valet skrivs med skäl i
passets `teknikval` och i RIKTNING.md.

## Kraven i en sajt

- `import gsap from 'gsap'` (och `import { ScrollTrigger } from 'gsap/ScrollTrigger'` med `gsap.registerPlugin`) i
  ett `<script>` i sidan eller komponenten: Astro bundlar och hashar det i sajtens CSP. Inget hämtas från ett CDN:
  paketet är låst i `mall/astro/package.json`, och ett nytt paket väljs fritt med exakt version (`kunskap/beroenden.md`,
  Ett nytt beroende).
- Varje rörelse står innanför `const mm = gsap.matchMedia(); mm.add('(prefers-reduced-motion: no-preference)', …)`,
  och den som bett om mindre rörelse får sidan färdig och stilla direkt (byggstandarden 3.5). Mallens `Bas.astro`
  stänger CSS-övergångar, men inte skriptdriven rörelse: det gör matchMedia.
- Innehållet och navigationen fungerar utan JavaScript: det som ScrollTrigger avtäcker ska synas också utan skript.
  Mjuk scroll (ScrollSmoother) är ett designval med villkoren i `kunskap/beroenden.md`: avstängd vid reducerad
  rörelse, utan att ta över tangentbordet och ankarlänkarna (WCAG 2.2.2 kräver paus eller stopp, inget förbud); pinning
  och scrub bara när rörelsen bär designen.
- Prestandabudgeten (byggstandarden 3.7): gsap-kärnan kostar 27 kB gzip per sida (69,8 kB rå), med ScrollTrigger
  44 kB gzip (112,5 kB rå); hela `motion` 19 kB gzip (uppmätt 2026-10-07, `kunskap/beroenden.md`). GSAP är det tyngsta
  valet och bär sig bara när beteendet kräver det. En sida utan rörelse får inga skript.

## Kända fel i upstream

Undermapparna är orörda kopior av gsap-skills `aed9cfd`, och upstream har öppna rättelser som inte är sammanslagna
(PR #8, #10 och #19, https://github.com/greensock/gsap-skills/pulls; lästa 2026-10-12). Två fel står ordagrant hos oss:

- `gsap-scrolltrigger/SKILL.md` rad 235, den horisontella scrollen: `Max.max` ger ReferenceError, och värdet är pixlar
  men står som `xPercent`. Skriv `x: () => -Math.max(0, scrollingEl.scrollWidth - window.innerWidth)` med
  `invalidateOnRefresh: true` i ScrollTrigger (vår rättelse).
- `gsap-plugins/SKILL.md` rad 333: `MotionPathHelper.create(".dot", "#path", …)` ska vara
  `MotionPathHelper.create(".dot", { path: "#path", end: 0.5 })` (PR #19).

PR #19 rättar också Flips `scale` (standardvärdet är `false`), Observers `type` (standardvärdet är
`"wheel,touch,pointer"`), ScrollToPlugin (ingen flagga `element`) och ScrollTriggers `containerAnimation`-exempel,
valfria `trigger` och refresh-ordning. Pröva ett plugin i rökprovets provbygge innan det används i en sajt.
