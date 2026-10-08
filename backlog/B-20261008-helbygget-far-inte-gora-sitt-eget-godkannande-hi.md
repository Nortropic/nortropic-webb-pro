---
id: B-20261008-helbygget-far-inte-gora-sitt-eget-godkannande-hi
status: klar
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#A3
skapad: 2026-10-08
prio: hog
steg: main: .claude/skills/bygg-sajt/SKILL.md, kor.sh, kontroller/skapande.py
commit: 6e09f70
andrad: 2026-10-08T14:56Z
---
# Helbygget får inte göra sitt eget godkännande historiskt genom att skriva i underlag/<slug>

**Varför:** Skillen bygg-sajt (steg 1–4) och kor.sh:s prompt säger att bygget skriver INNEHALL.md, REFERENSER.md m.fl. i underlag/<slug>/, som ingår i godkännandets underlagsversion (skapande.UNDERLAGSGRUND). Efter bygget skulle godkand_giltig bli falskt: Flöde steg 5 inaktuellt, prototyp.lage stopp, flodesstart.krav nekar omstart. Mekaniken är reproducerad syntetiskt (GR-20261008-r117-claude#A3), inte i en verklig körning; samma motsägelse står i ägarens uppdrag 2026-10-07 punkt 2 (promptkedjan, gren E, aldrig implementerad).

**Förslag:** Antingen tar byggprompten vid efter steg 5 (ingen omskrivning av underlag/<slug> när en godkänd startsida finns), eller skrivs byggets egna utdata under kunder/<slug>/. Pröva i det första verkliga helbygget genom den nya flödesingången innan något annat ändras.

**Klart när:** Ett verkligt helbygge från en godkänd startsida lämnar godkand_giltig sant efteråt, och Flöde steg 5 och 6 visar samma sak.
