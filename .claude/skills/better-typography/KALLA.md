# Källa

- **Skill:** better-typography ur Jakub Krehels skills.
- **Källa:** https://github.com/jakubkrehel/skills, `skills/better-typography/`, commit `d574cc8a576dc24256ad38268b8d03d86724a1b3` (d574cc8: 2026-10-05T20:22:04-07:00, sammanslagningen av PR #41 på standardgrenen main, plugin.json 1.10.2). Mappen ändrades senast i `4650b9c` (2026-10-05T23:21:44-04:00).
- **Licens:** MIT. `LICENSE` (Jakub Krehel, 2026), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-03 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane Claude
  Design Skills + jakubkrehel/skills).
- **Filer:** 8 ur källan, alla byte för byte lika källan vid d574cc8 (kontrollerat 2026-10-13), också SKILL.md med
  frontmatterns `description`: `SKILL.md`, `agents/openai.yaml`, `choosing-fonts.md`, `css-cheat-sheet.md`, `details-and-accessibility.md`, `spacing-and-sizing.md`, `variable-fonts-and-opentype.md`, `wrapping-and-punctuation.md`.
- **Vårt tillägg:** `KALLA.md`, `LICENSE` och `NORTROPIC.md`, husets tillämpning: förordet "Så används skillen i
  nortropic-webb-pro", som till 2026-10-13 stod överst i SKILL.md tillsammans med en svensk beskrivning i
  frontmattern. Den svenska beskrivningen och routningen står i `kunskap/metodkarta.md` (kompetensblocken, bandets
  stationer och designfas-kartans rad `skill:better-typography`). Inget i källans filer är ändrat, så underhållets
  trevägssammanslagning tar källans nya version av varje fil utan krock (`kontroller/underhall.py`, `plan_for_skill`:
  en fil som är lika källan vid vår commit byts mot källans nya, och filer som källan inte har rörs aldrig).
- **Krockar med våra beslut:** långt tankstreck för en inskjuten sats och raka mot krökta citattecken (wrapping-and-punctuation.md:13, :15; SKILL.md:83, :145) gäller engelska; svensk text följer `kunskap/copy-kontroll.md` med ” ” och tankstreck i intervall (K28, K66); "Rarely use more than three fonts" (SKILL.md:20) möter bara hypotesen om två familjer.
- **Förgranskning:** `kontroller/granska_repo.py` gav LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript.
- **Tillägg 2026-10-05:** `agents/openai.yaml` (Codex-metadata: visningsnamn och kort beskrivning; Claude Code läser den inte) är tillagd ordagrant ur samma commit 267330e, på ägarens beslut samma dag att skillsen ska vara i sin fullo. Raden "Borttaget", som stod här till 2026-10-13, gällde därmed bara frontmatterns beskrivning. De användaranropade skillsen följer nu med i egna mappar: better-interface-review, better-variant, better-break och better-explain-interface (se deras KALLA.md). SKILL.md och referensfilerna är orörda; referensfilerna och SKILL.md utanför förordet och beskrivningen är byte för byte lika upstream (kontrollerat 2026-10-05).
- **Uppdaterad av underhållet 2026-10-06T08:39:02Z** från `267330e` till `eaf8d1b18cff` (1 filer, lokala anpassningar sammanslagna; Ändringen justerar ett Tailwind-kodexempel för ett skalat inmatningsfält (shrink-0, rtl-ursprung, overflow-hidden och en fokusram på omslaget) och lägger till en förklarande mening, utan instruktioner om körning, hämtning, dataskick eller ändrade inställningar och utan dolda tecken.).
- **Förgranskning 2026-10-13:** `kontroller/granska_repo.py` på källans mapp vid d574cc8 gav LÅG: inga dolda tecken,
  ingen text riktad till agenter, inga skript, behörigheter, krokar eller konfiguration. Varje ändrad fil är genomläst:
  inga instruktioner att hämta, installera eller köra något och inga nätanrop.
- **Uppdaterad för hand 2026-10-13** från `eaf8d1b` (2026-10-02, plugin.json 1.6.4) till `d574cc8` (2026-10-05, plugin.json 1.10.2), åtgärd B1 i
  valideringen 2026-10-12 på ägarens mandat ("genomför valideringarnas och regelinventeringens åtgärder").
  Underhållet avvisade uppdateringen 2026-10-10 för att sammanslagningen krockade i SKILL.md, där förordet och den
  svenska beskrivningen låg på rader som källan skrev om (`underlag/startkontroll/UNDERHALL.md` 2026-10-12). Förordet
  flyttades till `NORTROPIC.md`, alla källans filer i mappen togs in ordagranna, och metodkartans utdrag pekar på
  samma innehåll i den nya texten. d574cc8 är den senaste commit i källan som är äldre än karenstiden (tre dygn; gränsen 2026-10-09T23:30Z vid intaget, `kunskap/beroenden.md`, Skydden runt en ny version). Underhållet tar in c0588bb (incheckad 2026-10-11T01:15Z) eller senare när karenstiden gått ut, och krocken i SKILL.md stoppar det inte längre. Vad ändringen gör: exakta mått skiljs från heuristik (inget nytt typsnitt utan att uppgiften ber om det, SKILL.md:16), med en detektionstabell, `text-box` och dekorativ text i CSS; avsnittet "Write copy naturally, style with CSS" heter nu "Natural case, typographic punctuation", och ersättningstabellen står i wrapping-and-punctuation.md, "Smart punctuation".
