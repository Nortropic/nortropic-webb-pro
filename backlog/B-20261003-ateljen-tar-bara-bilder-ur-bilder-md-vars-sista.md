---
id: B-20261003-ateljen-tar-bara-bilder-ur-bilder-md-vars-sista
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 5.1
---
# Ateljén tar bara bilder ur BILDER.md vars sista kolumn börjar med ja, och skillen beskriver inte den kolumnen

**Varför:** I holms-konditori-abx hade BILDER.md 28 användbara bilder med kolumnen Kvalitet sist; atelje.py tog inga, src/assets/atelje/ var tom och alla tre riktningar dömdes utan foto, fast domarna själva efterlyste foto i första vyn.

**Förslag:** kontroller/atelje.py: läs varje bildrad som inte är märkt används inte, eller .claude/skills/bygg-sajt/SKILL.md steg 1.2: ange att BILDER.md har en sista kolumn Använd (ja/nej).
