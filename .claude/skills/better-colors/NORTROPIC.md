# Så används skillen i nortropic-webb-pro

Husets tillämpning av better-colors. Den gäller före skillens `SKILL.md` och referensfiler, som står
ordagrant som källan (commit, licens och vad som är vårt: `KALLA.md`). Var skillen används, i vilka roller,
stationer och flöden: `kunskap/metodkarta.md`, i kompetensblocken, bandets stationer och designfas-kartans rad
`skill:better-colors`.

- **I kandidatflödet** (`kunskap/metodkarta.md`): fynd och rättningar skrivs i kandidatens RIKTNING.md, och paletten
  och typografin är uppdragets (huvudreferensen eller verksamhetens material).
- **När:** bygg-sajt steg 5.3 och 5.5, för token, kontrast och tillstånd inom specifikationen i KONCEPT.md.
- **Värdena är startpunkter.** Byggstandarden (`kunskap/byggstandard.md`) vinner där de krockar: radlängd 45–75 tecken
  (3.1), träffytor minst 24 px och primära knappar 44 px (3.3), dämpad rörelse (3.5). Ägarens aktuella
  beslut (`kunskap/designregler.md`) och kundens domar (`DESIGNDOMAR.jsonl`) går före; äldre domar i `LARDOMAR.md` är historik.
- **Stacken är Astro med de låsta beroendena** (`kunskap/beroenden.md`): egen CSS, Tailwind 4, React-öar och Motion där
  riktningen behöver dem; innehållet och navigationen fungerar utan JavaScript.
- **Rapportformatet** (tabellen och Block/Approve) är till för en fristående granskning. I ett bygge skrivs fynd och
  rättningar i `underlag/<slug>/JAMFORELSE.md`; den oberoende granskningen gör `kontroller/granska.py`.
- **Paletten kommer ur uppdraget** (huvudreferensen, stilpaketet eller verksamhetens material): avsnittet om att generera paletter används inte för
  att byta deras färger, bara för att räkna fram steg och kontrast inom dem. Kontrast enligt byggstandarden.
