# Källa

- **Skill:** better-accessibility ur Jakub Krehels skills.
- **Källa:** https://github.com/jakubkrehel/skills, `skills/better-accessibility/`, commit eaf8d1b18cff50e9bb9bccdaa18b621ee281cc7f (2026-08-29).
- **Licens:** MIT. `LICENSE` (Jakub Krehel, 2026), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-03 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane Claude
  Design Skills + jakubkrehel/skills).
- **Borttaget:** `agents/openai.yaml` (Codex-metadata) och frontmatterns beskrivning. Inga allowed-tools eller hooks
  fanns. De användaranropade skillsen interface-review, variant, break och explain-interface följer inte med.
- **Tillagt:** avsnittet "Så används skillen i nortropic-webb-pro" överst och en svensk beskrivning. Resten av
  SKILL.md och referensfilerna (focus-and-keyboard.md, forms.md, hit-areas.md, motion-and-zoom.md, screen-readers.md, semantics-and-aria.md) är oförändrade.
- **Förgranskning:** `kontroller/granska_repo.py` gav LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript.
- **Tillägg 2026-10-05:** `agents/openai.yaml` (Codex-metadata: visningsnamn och kort beskrivning; Claude Code läser den inte) är tillagd ordagrant ur samma commit 267330e, på ägarens beslut samma dag att skillsen ska vara i sin fullo. Raden "Borttaget" ovan gäller därmed bara frontmatterns beskrivning. De användaranropade skillsen följer nu med i egna mappar: better-interface-review, better-variant, better-break och better-explain-interface (se deras KALLA.md). SKILL.md och referensfilerna är orörda; referensfilerna och SKILL.md utanför förordet och beskrivningen är byte för byte lika upstream (kontrollerat 2026-10-05).
- **Uppdaterad av underhållet 2026-10-06T08:37:53Z** från `267330e` till `eaf8d1b18cff` (1 filer, lokala anpassningar sammanslagna; Ändringen skriver om CSS-reservlösningen för prefers-reduced-motion så att spinners och framstegsindikatorer märkta med data-motion-feedback undantas, lägger till animation-delay och transition-delay och förtydligar att animationend och transitionend inte alltid avfyras. Det är ren dokumentation utan instruktioner om att hämta, köra eller skicka något.).
