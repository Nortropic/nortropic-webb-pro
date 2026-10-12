# Källa

- **Skill:** better-accessibility ur Jakub Krehels skills.
- **Källa:** https://github.com/jakubkrehel/skills, `skills/better-accessibility/`, commit `c0588bb6d654eb725046f0bf9deec338c34891ab` (c0588bb: 2026-10-10T21:15:26-04:00, sammanslagningen av PR #43 på standardgrenen main, plugin.json 1.10.3). Mappen ändrades senast i `4650b9c` (2026-10-05T23:21:44-04:00).
- **Licens:** MIT. `LICENSE` (Jakub Krehel, 2026), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-03 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane Claude
  Design Skills + jakubkrehel/skills).
- **Filer:** 8 ur källan, alla byte för byte lika källan vid c0588bb (kontrollerat 2026-10-13), också SKILL.md med
  frontmatterns `description`: `SKILL.md`, `agents/openai.yaml`, `focus-and-keyboard.md`, `forms.md`, `hit-areas.md`, `motion-and-zoom.md`, `screen-readers.md`, `semantics-and-aria.md`.
- **Vårt tillägg:** `KALLA.md`, `LICENSE` och `NORTROPIC.md`, husets tillämpning: förordet "Så används skillen i
  nortropic-webb-pro", som till 2026-10-13 stod överst i SKILL.md tillsammans med en svensk beskrivning i
  frontmattern. Den svenska beskrivningen och routningen står i `kunskap/metodkarta.md` (kompetensblocken, bandets
  stationer och designfas-kartans rad `skill:better-accessibility`). Inget i källans filer är ändrat, så underhållets
  trevägssammanslagning tar källans nya version av varje fil utan krock (`kontroller/underhall.py`, `plan_for_skill`:
  en fil som är lika källan vid vår commit byts mot källans nya, och filer som källan inte har rörs aldrig).
- **Krockar med våra beslut:** allt som inte är ett numrerat WCAG-kriterium på nivå A eller AA är en rekommendation som aldrig blir `HIGH`, också målen 44 px och 40 px, en h1 med obrutna rubriknivåer och APG:s mönster (SKILL.md:16, :48), mot ägarbeslutet om 44 px för primära kontroller (byggstandarden 3.3, `kunskap/designregler.md`), kvalitetskravet om rubrikordningen, fokusringen på minst 2 px (3.4) och disclosure-mönstret (5.2); den globala reservregeln för reducerad rörelse är borta och bara opt-in återstår (motion-and-zoom.md:7), medan byggstandarden 3.5 kräver att ingen förflyttning, skalning eller rotation sker under reducerad rörelse; spinnare behålls under reducerad rörelse (motion-and-zoom.md:32), mot 3.5 vid laddning; "Auto-rotating carousels → start paused" (motion-and-zoom.md:34) förutsätter karuseller, som ägaren beslutat bort. `NORTROPIC.md` håller 44 px och reducerad rörelse som ägarbeslut [beslut].
- **Förgranskning:** `kontroller/granska_repo.py` gav LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript.
- **Tillägg 2026-10-05:** `agents/openai.yaml` (Codex-metadata: visningsnamn och kort beskrivning; Claude Code läser den inte) är tillagd ordagrant ur samma commit 267330e, på ägarens beslut samma dag att skillsen ska vara i sin fullo. Raden "Borttaget", som stod här till 2026-10-13, gällde därmed bara frontmatterns beskrivning. De användaranropade skillsen följer nu med i egna mappar: better-interface-review, better-variant, better-break och better-explain-interface (se deras KALLA.md). SKILL.md och referensfilerna är orörda; referensfilerna och SKILL.md utanför förordet och beskrivningen är byte för byte lika upstream (kontrollerat 2026-10-05).
- **Uppdaterad av underhållet 2026-10-06T08:37:53Z** från `267330e` till `eaf8d1b18cff` (1 filer, lokala anpassningar sammanslagna; Ändringen skriver om CSS-reservlösningen för prefers-reduced-motion så att spinners och framstegsindikatorer märkta med data-motion-feedback undantas, lägger till animation-delay och transition-delay och förtydligar att animationend och transitionend inte alltid avfyras. Det är ren dokumentation utan instruktioner om att hämta, köra eller skicka något.).
- **Förgranskning 2026-10-13:** `kontroller/granska_repo.py` på källans mapp vid c0588bb gav LÅG: inga dolda tecken,
  ingen text riktad till agenter, inga skript, behörigheter, krokar eller konfiguration. Varje ändrad fil är genomläst:
  inga instruktioner att hämta, installera eller köra något och inga nätanrop.
- **Uppdaterad för hand 2026-10-13** från `eaf8d1b` (2026-10-02, plugin.json 1.6.4) till `c0588bb` (2026-10-10, plugin.json 1.10.3), åtgärd B1 i
  valideringen 2026-10-12 på ägarens mandat ("genomför valideringarnas och regelinventeringens åtgärder").
  Underhållet avvisade uppdateringen 2026-10-10 för att sammanslagningen krockade i SKILL.md, där förordet och den
  svenska beskrivningen låg på rader som källan skrev om (`underlag/startkontroll/UNDERHALL.md` 2026-10-12). Förordet
  flyttades till `NORTROPIC.md`, alla källans filer i mappen togs in ordagranna, och metodkartans utdrag pekar på
  samma innehåll i den nya texten. Karenstiden (tre dygn) hade inte gått ut för c0588bb (incheckad 2026-10-11T01:15Z);
  intaget granskades därför fil för fil i stället för av underhållet. Vad ändringen gör: fynd graderas mot numrerade WCAG 2.2-kriterier på nivå A och AA och resten blir rekommendationer; nytt är 2.4.11 (fokus som inte döljs, `scroll-padding-top`), 2.5.7 (alternativ till drag), `<dialog>` med `showModal()`, fokus och titel vid ruttbyte och kontrasttabellen 1.4.3/1.4.11, och hovringsreglerna har flyttat till better-ui. Underhållets anteckning 2026-10-06 om `data-motion-feedback` gäller inte längre: reservregeln är borttagen i källan.
