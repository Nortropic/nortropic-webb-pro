# Källa

- **Skill:** `motion` (mappen `motion`). Motion AI Kits skill, den fria delen: animationsregler (tabellen CSS eller
  Motion, regler för vanilla JS, React, Vue och Base UI), dokumentations- och exempelsökning genom Motions MCP
  (codex), CSS-fjädrar som `linear()`, och två Motion+-delar (MotionScore-granskning, transition-editorn) som bara
  beskrivs. Skillen täcker `motion` (vanilla, i ett `<script>`), `motion/react` (React-öar) och `motion-v` (Vue), och
  migrering från `framer-motion`: Framer Motion är det äldre namnet på Motion, `motion/react` är gamla framer-motion,
  och npm-paketet `framer-motion` 14.0.0 är ett alias. Det finns därför ingen separat Framer Motion-skill eller -MCP;
  den här är den (ägarens tillägg 2026-10-07: "Du glömde Framer Motion mcp/skill också").
- **Källa:** https://github.com/motiondivision/ai-kit, `plugins/motion/skills/motion/`, commit
  `d1c5c26f424adfd47c112d894e9d424b57338c7e` (2026-09-25T10:55:41+02:00, standardgrenen main). Mappen ändrades senast
  i `f13f5734e7c742a18234ab198eb68599ba62f7f8` (2026-09-25T10:54:08+02:00). Samma filer ligger i npm-paketet
  `motion-ai` 14.1.0 (`content/skills/motion/`), installeraren `npx motion-ai`, som aldrig kördes mot ägarens
  Claude-konfiguration: filerna hämtades ur klonen och lades i repot. Dokumentationen: https://motion.dev/docs/ai-kit
  (läst 2026-10-07; `/docs/mcp` finns inte).
- **Licens:** MIT enligt `packages/motion-ai/package.json` (`"license": "MIT"`, författare Matt Perry, motion.dev),
  `plugins/motion/.cursor-plugin/plugin.json` (`"license": "MIT"`) och serverns egen instruktionstext vid initialize
  ("Motion's agent skill is free and open source (MIT)"). Repot och npm-tarbollen har ingen LICENSE-fil (kontrollerat
  2026-10-07). Ingen licenstext är kopierad hit: vi skriver inte en licensfil som upphovsmannen inte publicerat. Att
  mappen tas in trots att licensfilen saknas (jämför `kunskap/REGISTER.md`, Ursprung) följer av ägarens uppdrag
  2026-10-07, punkt 5C; ägaren avgör om deklarationen räcker eller om en fråga ska ställas till Motion.
- **Intagen:** 2026-10-07 på ägarens uppdrag samma dag (ordagrant i minnet, punkt 5C: "Inför officiell
  Motion-kompetens och relevanta MCP-funktioner") och ägarens beslut om Motion+: "Nej, bara den fria delen". Ordagrant:
  alla 11 git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar (SKILL.md bec11967,
  best-practices/base-ui.md 9a5f0144, css-or-motion.md b54192e3, index.md 375fb541, motion.md d0b59c8d, react.md
  a568fa54, vue.md 94db1ca0, codex/index.md d33bb523, css-spring/index.md a5c1e194, performance-audit/index.md
  eaa1693e, transition-preview/index.md b647c555); inget omskrivet eller borttaget.
- **Filer:** 11 från upstream (1 i mappens rot, 10 i best-practices/, codex/, css-spring/, performance-audit/,
  transition-preview/). Våra tillägg: `KALLA.md`.
- **Utelämnat:** `plugins/motion/mcp.json` (bär också Motion+-servern `https://mcp.motion.dev/plus`; vår
  `kontroller/mcp/motion.json` bär bara den fria), `rules/motion.mdc` (en Cursor-regel), `agents/motion-reviewer.md`
  (MotionScore-granskaren, kräver Motion+), `assets/`, `.cursor-plugin/`, installeraren `packages/motion-ai/`.
- **MCP:n:** `https://mcp.motion.dev` (fri, inget konto, ingen nyckel; `kontroller/mcp/motion.json`). `tools/list`
  2026-10-07 gav ett verktyg, `search-motion-docs` (`platform` js, react eller vue; `searchTerm`), och `resources/list`
  en tom lista: dokumentsidorna kommer som resource_links i svaret och läses med `resources/read`, som flödets
  sessioner inte har något verktyg för, så sessionen får titlar, beskrivningar, API-namn och demolänkar. Verktyget
  `generate-css-easing`, som skillen nämner (codex/index.md, css-spring/index.md), fanns inte på servern 2026-10-07;
  metodkartan har beslutet. Motion+-servern (search-motion-source, save-transition, open-transition-editor,
  MotionScore-metodiken) används inte.
- **Förgranskning 2026-10-07:** `kontroller/granska_repo.py` gav LÅG: 11 textfiler, omkring 8 350 tokens (160 alltid,
  1 110 när skillen används, 7 040 vid behov); inga dolda tecken, ingen text riktad till agenter, inga behörigheter,
  hookar eller skript.
- **Krockar med våra beslut:** "Install any packages the source imports" och `npx motionscore <url>` (codex,
  performance-audit): flödets sessioner kör aldrig npm, npx eller nät (`kunskap/beroenden.md`); paketen är de låsta.
  Motion UI och `motion-plus` installeras inte (bara den fria delen). `MotionConfig reducedMotion="user"` (react.md)
  behåller opacity- och färganimationer för den som bett om mindre rörelse; hos oss gäller byggstandarden 3.5 (mallens
  `Bas.astro` stänger övergångar och animationer, och skript prövar `prefers-reduced-motion` själva). "Do not add
  animation only for decoration" stämmer med Avgörandena och ägarens uppdrag ("Animationer ska inte läggas till för
  att fylla en användningskvot").
- **Så används skillen här:** rollen rorelse i `kunskap/metodkarta.md`: beslutstabellen `best-practices/css-or-motion.md`
  läses hel före valet i passet rörelse (valet CSS, Motion eller GSAP per beteende, tillsammans med
  `kunskap/beroenden.md`; den står bland alternativen, inte i kärnan, så att skissens kärna håller sig under läsvolymens
  tak), `SKILL.md`, `best-practices/index.md`, `motion.md` och `react.md` som alternativ, och MCP:n `search-motion-docs` genom kundvakten
  med generiska sökord (mönstret som byggs: inView, stagger, spring), aldrig kundens uppgifter. Valet skrivs med skäl i
  passets `teknikval` och i RIKTNING.md.
