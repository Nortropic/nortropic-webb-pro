# Så används skillen i nortropic-webb-pro

Husets tillämpning av better-accessibility. Den gäller före skillens `SKILL.md` och referensfiler, som står
ordagrant som källan (commit, licens och vad som är vårt: `KALLA.md`). Var skillen används, i vilka roller,
stationer och flöden: `kunskap/metodkarta.md`, i kompetensblocken, bandets stationer och designfas-kartans rad
`skill:better-accessibility`.

- **I kandidatflödet** (`kunskap/metodkarta.md`): fynd och rättningar skrivs i kandidatens RIKTNING.md, och paletten
  och typografin är uppdragets (huvudreferensen eller verksamhetens material).
- **När:** bygg-sajt steg 5.3 medan sidorna byggs och steg 6 bredvid provets axe och tangentbordsväg.
- **Värdena är startpunkter.** Byggstandarden (`kunskap/byggstandard.md`) vinner där de krockar: radlängd 45–75 tecken
  (3.1), träffytor minst 24 px och primära knappar 44 px (3.3), dämpad rörelse (3.5). Ägarens aktuella
  beslut (`kunskap/designregler.md`) och kundens domar (`DESIGNDOMAR.jsonl`) går före; äldre domar i `LARDOMAR.md` är historik.
- **Två ägarbeslut som skillen inte sänker** [beslut]: primära interaktiva kontroller är minst 44×44 CSS-pixlar
  (byggstandarden 3.3; `kunskap/designregler.md`, Nortropics produkt- och ägarbeslut), och rörelse följer reducerad
  rörelse (byggstandarden 3.5: med `prefers-reduced-motion: reduce` ingen förflyttning, skalning eller rotation).
  Skillen klassar i c0588bb målen 44 px och 40 px som rekommendationer som aldrig blir `HIGH` ("Criteria, not
  conventions" i SKILL.md), och dess reservregel för reducerad rörelse är borttagen så att bara opt-in återstår
  (motion-and-zoom.md). Hos oss är båda krav: en primär kontroll under 44 px och rörelse som inte följer reducerad
  rörelse är fynd mot byggstandarden, vad skillens allvarsgrad än säger. WCAG:s golv på 24 px (2.5.8) gäller alla mål.
- **Stacken är Astro med de låsta beroendena** (`kunskap/beroenden.md`): egen CSS, Tailwind 4, React-öar och Motion där
  riktningen behöver dem; innehållet och navigationen fungerar utan JavaScript.
- **Rapportformatet** (tabellen och Block/Approve) är till för en fristående granskning. I ett bygge skrivs fynd och
  rättningar i `underlag/<slug>/JAMFORELSE.md`; den oberoende granskningen gör `kontroller/granska.py`.
- **Formulären** följer mallens `Forfragan.astro` och `kunskap/forfragan.md`: fältnamnen och fällorna ändras inte,
  beskeden vid fältet är svenska (byggstandarden 6.2).
