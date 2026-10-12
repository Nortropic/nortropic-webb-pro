# Källa

- **Skill:** better-colors ur Jakub Krehels skills.
- **Källa:** https://github.com/jakubkrehel/skills, `skills/better-colors/`, commit `c0588bb6d654eb725046f0bf9deec338c34891ab` (c0588bb: 2026-10-10T21:15:26-04:00, sammanslagningen av PR #43 på standardgrenen main, plugin.json 1.10.3). Mappen ändrades senast i `9b03828` (2026-10-05T23:02:29-04:00).
- **Licens:** MIT. `LICENSE` (Jakub Krehel, 2026), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-03 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane Claude
  Design Skills + jakubkrehel/skills).
- **Filer:** 8 ur källan, alla byte för byte lika källan vid c0588bb (kontrollerat 2026-10-13), också SKILL.md med
  frontmatterns `description`: `SKILL.md`, `agents/openai.yaml`, `color-formats.md`, `color-usage.md`, `contrast.md`, `palette-generation.md`, `palette-structure.md`, `token-naming.md`.
- **Vårt tillägg:** `KALLA.md`, `LICENSE` och `NORTROPIC.md`, husets tillämpning: förordet "Så används skillen i
  nortropic-webb-pro", som till 2026-10-13 stod överst i SKILL.md tillsammans med en svensk beskrivning i
  frontmattern. Den svenska beskrivningen och routningen står i `kunskap/metodkarta.md` (kompetensblocken, bandets
  stationer och designfas-kartans rad `skill:better-colors`). Inget i källans filer är ändrat, så underhållets
  trevägssammanslagning tar källans nya version av varje fil utan krock (`kontroller/underhall.py`, `plan_for_skill`:
  en fil som är lika källan vid vår commit byts mot källans nya, och filer som källan inte har rörs aldrig).
- **Krockar med våra beslut:** tokenformen "Use one shape and never deviate" (token-naming.md:45, SKILL.md:30) är K56 (variablerna i design.css); `#2563eb` som exempelvärde (palette-generation.md:52, token-naming.md:14, :86) är inget reservvärde hos oss (Avgörandet Referens och stil).
- **Förgranskning:** `kontroller/granska_repo.py` gav LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript.
- **Tillägg 2026-10-05:** `agents/openai.yaml` (Codex-metadata: visningsnamn och kort beskrivning; Claude Code läser den inte) är tillagd ordagrant ur samma commit 267330e, på ägarens beslut samma dag att skillsen ska vara i sin fullo. Raden "Borttaget", som stod här till 2026-10-13, gällde därmed bara frontmatterns beskrivning. De användaranropade skillsen följer nu med i egna mappar: better-interface-review, better-variant, better-break och better-explain-interface (se deras KALLA.md). SKILL.md och referensfilerna är orörda; referensfilerna och SKILL.md utanför förordet och beskrivningen är byte för byte lika upstream (kontrollerat 2026-10-05).
- **Uppdaterad av underhållet 2026-10-06T08:38:18Z** från `267330e` till `eaf8d1b18cff` (1 filer, lokala anpassningar sammanslagna; Ersätter ett stycke i contrast.md om när ljus eller mörk text ska väljas (mät med projektets kontrastmått, APCA och WCAG 2 kan skilja sig) med ett WCAG 2-exempel; ren dokumentation utan instruktioner om körning, hämtning, dataskick eller inställningar.).
- **Förgranskning 2026-10-13:** `kontroller/granska_repo.py` på källans mapp vid c0588bb gav LÅG: inga dolda tecken,
  ingen text riktad till agenter, inga skript, behörigheter, krokar eller konfiguration. Varje ändrad fil är genomläst:
  inga instruktioner att hämta, installera eller köra något och inga nätanrop.
- **Uppdaterad för hand 2026-10-13** från `eaf8d1b` (2026-10-02, plugin.json 1.6.4) till `c0588bb` (2026-10-10, plugin.json 1.10.3), åtgärd B1 i
  valideringen 2026-10-12 på ägarens mandat ("genomför valideringarnas och regelinventeringens åtgärder").
  Underhållet avvisade uppdateringen 2026-10-10 för att sammanslagningen krockade i SKILL.md, där förordet och den
  svenska beskrivningen låg på rader som källan skrev om (`underlag/startkontroll/UNDERHALL.md` 2026-10-12). Förordet
  flyttades till `NORTROPIC.md`, alla källans filer i mappen togs in ordagranna, och metodkartans utdrag pekar på
  samma innehåll i den nya texten. Karenstiden (tre dygn) hade inte gått ut för c0588bb (incheckad 2026-10-11T01:15Z);
  intaget granskades därför fil för fil i stället för av underhållet. Vad ändringen gör: granskningsformen skiljer fynd från smak, med en detektionstabell, trösklar för WCAG 2 och APCA, `prefers-contrast` per utseende och en sRGB-reserv före P3. Issue #21 (bland annat att Tailwind 4 skapar utility-namn ur `--color-`) är öppen och berör token-naming.md.
