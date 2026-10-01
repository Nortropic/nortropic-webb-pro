---
id: B-20261001-rattvis-a-b-provning-med-claude-plugin-eval-pa-s
status: vilande
kalla: bevakning
kallref: Omvärldsbevakning 2026-10-01: Anthropic Demystifying evals, code.claude.com/docs/en/plugin-evals, OpenAI evaluation best practices, arXiv 2306.05685
skapad: 2026-10-01
prio: normal
steg: 4–6
---
# Rättvis A/B-prövning med claude plugin eval på stegnivå, när de första riktiga byggena finns

**Varför:** Kirurgens dom 'prova A/B' saknar en mätmetod. Forskningen: samma indata, minst tre körningar per arm, blind parvis jämförelse med ombytt ordning, en annan modell som domare, och kostnad bredvid kvalitet. Det kräver fall ur riktiga byggen, som inte finns än.

**Förslag:** Lägg en evals/-svit i repot (claude plugin eval, --ablation with-without, --judge-model sonnet, runs 3) med fall ur de första byggenas underlag: steg 4 (INNEHALL.md ur RESEARCH.md och BRIEF.md) och steg 5 (första vyn). LLM-graderare med rubrik som PASS/FAIL-villkor ur kunskap/referenser-professionella.md och copy-kontroll.md. Använd sviten för den vilande posten om ui-ux-pro-max.

**Klart när:** En körbar svit finns, och första A/B-prövningen är avgjord med den och bokförd i REGISTER.md.
