---
id: B-20261013-emil-animation-performance-in-nar-karenstiden-ga
status: vilande
kalla: bevakning
kallref: github.com/emilkowalski/skills 6465079 (2026-10-11T13:30:58Z, Add /animation-performance skill), läst 2026-10-13; ägarens beslut 2026-10-13, punkt 8 (underlag/uppdrag/PROMPT-Nortropic-Astro-artefakt-resten-20261013.md)
skapad: 2026-10-13
prio: normal
steg: bandets station rorelse och helbygget (.claude/skills/emil-animation-performance/, kunskap/metodkarta.md)
---
# emil-animation-performance in när karenstiden gått ut, tidigast 2026-10-14T13:31Z

**Varför:** Ägarens beslut 2026-10-13, punkt 8: "emil-animation-performance: tas in när karenstiden gått ut, tidigast 2026-10-14." Emil Kowalski lade till skills/animation-performance/SKILL.md i 6465079 (2026-10-11T13:30:58Z; en fil, 223 rader, MIT; 2d22863 samma dag ändrade bara README). Karenstiden (tre dygn, kunskap/beroenden.md, Skydden runt en ny version) går ut 2026-10-14T13:30:58Z. Skillen diagnostiserar rörelse som tappar bildrutor: egenskaper som bara kräver compositing, huvudtråden, CSS mot WAAPI mot requestAnimationFrame, Motions hårdvaruaccelererade väg, will-change och blur; den saknas i stationen rorelse och i helbygget, där de andra Emil-skillsen står. Underhållet följer bara mappar som redan är intagna, så en ny skill tas in för hand.

**Förslag:** När date -u är efter 2026-10-14T13:31Z: välj den senaste commit i emilkowalski/skills som är äldre än gränsen (date -u minus 72 h) och har mappen (i dag 6465079 eller senare). Kopiera skills/animation-performance/ ordagrant till .claude/skills/emil-animation-performance/ med repots LICENSE (MIT) och KALLA.md i samma form som emil-animate (källa, commit, licens, intagen på ägarens beslut 2026-10-13, förgranskning, krockar, så används skillen här), och kontrollera filerna mot källans blobbar. Kör kontroller/granska_repo.py på en kopia (får inte bli HÖG). Placera den som alternativ i bandets station rorelse (Emils skills aktiveras med Skill trots ## Initial Response; promptens villkor att ingen svarar gäller) och i kompetensblocket rorelse eller helbygge under välj, inte i kärnan (prov_rorelse prövar kärnans tak); designfas.py inventera --placera ger en preliminär rad som skrivs om till den verkliga i designfas-kartan. Skriv krockarna: React-omrenderingar och Framer Motion gäller bara React-öar i Astro, och regeln om transition: all stämmer med taste efter 85fc47e. metod.py --las och --prova, kompetens.py --prova, designfas.py karta och inventera; en post i kunskap/REGISTER.md.

**Klart när:** Mappen står ordagrant vid en commit som är äldre än karenstiden, med KALLA.md och LICENSE; den har en plats i stationen rorelse och i ett kompetensblock; metod.py --prova, kompetens.py --prova, designfas.py karta och inventera är utan fel, och prov_startkontroll, prov_rorelse och prov_designfas är gröna.
