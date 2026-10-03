---
id: B-20261003-byggaren-och-granskaren-laser-ocksa-provets-skar
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · waybarrios/opencode-power-pack
skapad: 2026-10-03
prio: normal
steg: steg 5.5 och granskaren
---
# Byggaren och granskaren läser också provets skärmrutor i 768 px, som provet redan tar men ingen tittar på

**Varför:** Provet tar skärmrutor i 390, 768 och 1440 (prova.py rad 369; kunder/<slug>/prov/inspektion/<sida>/vy-768-ruta-NN.png finns) och prövar spill i alla tre, men steg 5.5 och granskarens uppdrag (granska.py rad 204 och 311, GRANSKARE.md rad 23) listar bara 390 och 1440. Rubriker som spiller och en desktoplayout som bara staplats syns oftast i mellanbredden; ai-slop-rubriken i opencode-power-pack namnger just 'heading overflow at mid widths' och 'desktop merely stacked on mobile' som slopsignaler.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md steg 5.5 (rad 307–308): lägg till vy-768-ruta-NN.png i det byggaren läser, med en mening om vad mellanbredden visar (rubrikspill, staplad desktop). kritik/GRANSKARE.md rad 23: '390, 768 och 1440 px'. kontroller/granska.py rad 204 och 311: 768-rutorna i uppdragets lista mellan 390 och 1440. Ingen ny mätning; bilderna finns redan.

**Klart när:** En granskningsrapport (kunder/<slug>/granskning/GRANSKNING.md) listar vy-768-rutor under sett, och steg 5.5 i skillen nämner 768.
