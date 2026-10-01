---
id: B-20261001-kritikfragorna-hanvisar-till-runtime-paketets-fi
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
---
# Kritikfrågorna hänvisar till Runtime-paketets FILES.md och schema som inte finns här

**Varför:** Luleå-Snickaren: kritik/FRAGA-renderingslasning.md kräver FILES.md, BEDOMNINGSBINDNING och ett JSON-schema, och FRAGA-femsekunderstest.md börjar med 'Börja med FILES.md'. Inget av det finns i bygg-sajt-flödet; subagenten fick en egen fältlista.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md steg 6.3–6.4: ange vilka delar av frågorna som gäller (frågorna 1–6 respektive de sju frågorna) och vilka JSON-fält femsekunderstestet ska svara med.
