---
id: B-20261002-ta-in-jakubkrehel-skills-better-layout-better-ty
status: pagar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane Claude Design Skills (YouTube Ysr7oNDajJI) + jakubkrehel/skills
skapad: 2026-10-02
prio: normal
steg: 5 (bygge, punkt 3 och 5), verktygslådan
andrad: 2026-10-03T00:35Z
---
# Ta in jakubkrehel/skills better-layout, better-typography, better-colors, better-accessibility, better-ui, better-writing och better-interface i verktygslådan, och peka på better-layout i bygg-sajt steg 5.5 för luft och hierarki

**Varför:** Ta in: luft och hierarki är den enda dimensionen ägaren satte Okej på i alla tre domarna (LARDOMAR.md rad 35, 60, 84), och ingen av våra texter ger byggaren en regel för gruppering och avstånd, bara frågan i referenser-professionella.md rad 24 och principen Gestalt/CRAP i teoretisk-grund.md rad 62. Jakub Krehels better-layout ger exakt det (avståndet mellan grupper minst dubbelt mot inom, delade kanter, 12/24 px mellan kontroller, knappar indragna 16 px, brytpunkter ur innehållet), de övriga sex ger hantverksregler för typografi, färg, tillgänglighet, polish och text med Före/Efter/Varför-format, allt text, MIT, inga skript, LÅG i förgranskningen.

**Förslag:** Kopiera från github.com/jakubkrehel/skills @ 267330e (MIT, LICENSE följer med i varje mapp) sju mappar: .claude/skills/better-layout/, better-typography/, better-colors/, better-accessibility/, better-ui/, better-writing/ och better-interface/, var och en med SKILL.md och sina referensfiler. Ta inte med interface-review, variant, break och explain-interface (användaranropade, kräver git-diff eller skriver kastbara sidor). Ta bort agents/openai.yaml (Codex-metadata); frontmatter har bara name och description, inga allowed-tools eller hooks. KALLA.md i varje mapp i samma form som humanizer. Överst i varje SKILL.md ett avsnitt Så används skillen i nortropic-webb-pro: används i bygg-sajt steg 5.3 under bygget och 5.5 efter JAMFORELSE.md, värdena är startpunkter och byggstandarden vinner (3.1 radlängd 45–75, 3.3 träffytor 24 px, 3.5), better-colors bara inom specifikationen i KONCEPT.md och aldrig nya paletter, better-ui bara CSS-recepten (ingen Motion/framer, ingen JS som inte behövs), better-writing: svenska texten följer copy-kontroll.md, regeln om vi/we är engelsk. Beskrivningarna skrivs om på svenska med när bygget ska använda dem. I .claude/skills/bygg-sajt/SKILL.md steg 5 punkt 5, efter raden Kopiera aldrig layout, palett eller typsnitt (rad 252), en mening: För luft och hierarki (dimension 4) gå igenom varje sida med better-layout i verktygslådan, och hantverksdetaljerna med better-typography och better-ui, innan JAMFORELSE.md skrivs.

**Klart när:** De sju mapparna finns med SKILL.md, KALLA.md och LICENSE, inga agents/openai.yaml, beskrivningarna på svenska, meningen står i bygg-sajt steg 5.5, kontroller/rokprov.sh grönt, och nästa bygges RAPPORT.md punkt 15 namnger vilka av dem som användes.
