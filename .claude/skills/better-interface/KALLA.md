# Källa

- **Skill:** better-interface ur Jakub Krehels skills.
- **Källa:** https://github.com/jakubkrehel/skills, `skills/better-interface/`, commit `d574cc8a576dc24256ad38268b8d03d86724a1b3` (d574cc8: 2026-10-05T20:22:04-07:00, sammanslagningen av PR #41 på standardgrenen main, plugin.json 1.10.2). Mappen ändrades senast i `da5f6d5` (2026-10-04T21:26:49-07:00).
- **Licens:** MIT. `LICENSE` (Jakub Krehel, 2026), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-03 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane Claude
  Design Skills + jakubkrehel/skills).
- **Filer:** 3 ur källan, alla byte för byte lika källan vid d574cc8 (kontrollerat 2026-10-13), också SKILL.md med
  frontmatterns `description`: `SKILL.md`, `agents/openai.yaml`, `review-format.md`.
- **Vårt tillägg:** `KALLA.md`, `LICENSE` och `NORTROPIC.md`, husets tillämpning: förordet "Så används skillen i
  nortropic-webb-pro", som till 2026-10-13 stod överst i SKILL.md tillsammans med en svensk beskrivning i
  frontmattern. Den svenska beskrivningen och routningen står i `kunskap/metodkarta.md` (kompetensblocken, bandets
  stationer och designfas-kartans rad `skill:better-interface`). Inget i källans filer är ändrat, så underhållets
  trevägssammanslagning tar källans nya version av varje fil utan krock (`kontroller/underhall.py`, `plan_for_skill`:
  en fil som är lika källan vid vår commit byts mot källans nya, och filer som källan inte har rörs aldrig).
- **Krockar med våra beslut:** rapportformatet med tabell och Block/Approve (SKILL.md, "Review output format", och review-format.md) används inte i flödet (K57).
- **Förgranskning:** `kontroller/granska_repo.py` gav LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript.
- **Tillägg 2026-10-05:** `agents/openai.yaml` (Codex-metadata: visningsnamn och kort beskrivning; Claude Code läser den inte) är tillagd ordagrant ur samma commit 267330e, på ägarens beslut samma dag att skillsen ska vara i sin fullo. Raden "Borttaget", som stod här till 2026-10-13, gällde därmed bara frontmatterns beskrivning. De användaranropade skillsen följer nu med i egna mappar: better-interface-review, better-variant, better-break och better-explain-interface (se deras KALLA.md). SKILL.md och referensfilerna är orörda; referensfilerna och SKILL.md utanför förordet och beskrivningen är byte för byte lika upstream (kontrollerat 2026-10-05).
- **Förgranskning 2026-10-13:** `kontroller/granska_repo.py` på källans mapp vid d574cc8 gav LÅG: inga dolda tecken,
  ingen text riktad till agenter, inga skript, behörigheter, krokar eller konfiguration. Varje ändrad fil är genomläst:
  inga instruktioner att hämta, installera eller köra något och inga nätanrop.
- **Uppdaterad för hand 2026-10-13** från `267330e` (2026-08-29, plugin.json 1.6.3) till `d574cc8` (2026-10-05, plugin.json 1.10.2), åtgärd B1 i
  valideringen 2026-10-12 på ägarens mandat ("genomför valideringarnas och regelinventeringens åtgärder").
  Underhållet avvisade uppdateringen 2026-10-10 för att sammanslagningen krockade i SKILL.md, där förordet och den
  svenska beskrivningen låg på rader som källan skrev om (`underlag/startkontroll/UNDERHALL.md` 2026-10-12). Förordet
  flyttades till `NORTROPIC.md`, alla källans filer i mappen togs in ordagranna, och metodkartans utdrag pekar på
  samma innehåll i den nya texten. d574cc8 är den senaste commit i källan som är äldre än karenstiden (tre dygn; gränsen 2026-10-09T23:30Z vid intaget, `kunskap/beroenden.md`, Skydden runt en ny version). Underhållet tar in c0588bb (incheckad 2026-10-11T01:15Z) eller senare när karenstiden gått ut, och krocken i SKILL.md stoppar det inte längre. Vad ändringen gör: stramare orkestrering; taket och utlåtandet räknar bara fynden `Introduced` och `Regression` när interface-review lämnar tillbaka en granskning, och detektionstabellen är ny. Rubriken "6. Rank by user impact", som granskningens utdrag i metodkartan pekar på, finns kvar.
