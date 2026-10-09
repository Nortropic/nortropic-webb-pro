---
id: B-20261009-tangentbordsvandringen-stannar-vid-tva-likadana
status: vilande
kalla: bygge
kallref: RAPPORT-2026-10-09-formagoprov-kvalitetsprov
skapad: 2026-10-09
prio: normal
steg: kontroller/webblasare/gemensamt.mjs (tangentbord)
---
# Tangentbordsvandringen stannar vid två likadana länkar i följd

**Varför:** Kvalitetsprovet 2026-10-09: på kontaktsidan stannade vandringen efter 8 steg, eftersom huvudradens 'Ring 070-174 06 42' följdes av en likadan länk i sidan (samma tagg och text). Formuläret nåddes aldrig, och provet rapporterade ändå 0 steg utan synligt fokus.

**Förslag:** Stoppa på samma element (nod eller samma läge och storlek) eller när fokus återvänder till det första, inte på samma text; rapportera när vandringen slutade före sidans sista fokuserbara element.

**Klart när:** Kontaktsidan i navet-cykelverkstad k02 når formulärets fält och knapp; ett prov med två likadana länkar i följd vandrar förbi dem.
