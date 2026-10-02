---
id: B-20261002-upptagna-val-byggaren-ser-tidigare-byggens-typsn
status: vilande
kalla: bevakning
kallref: Prompting Claude Opus 5.5, avsnittet Frontend design defaults (platform.claude.com, läst 2026-10-02)
skapad: 2026-10-02
prio: hog
steg: 5
---
# Upptagna val: byggaren ser tidigare byggens typsnitt, färg och toppsektion och modellens namngivna standardval

**Varför:** Alla tre nattbyggen valde Archivo, med en ny motivering varje gång, och granskaren underkände alla tre på originalitet. Anthropics promptsida för Opus 5.5: ett allmänt förbud mot AI-stil byter mest en standard mot en annan; namnge specifika mönster och bygg ut listan efter varje resultat.

**Förslag:** Nytt verktyg kontroller/upptagna_val.py som efter varje bygge skriver underlag/UPPTAGNA-VAL.md (utanför git): per tidigare bygge renderade typsnitt, dominerande färgfamilj och toppsektionens komposition ur sida.mjs designfakta, plus Opus 5.5:s namngivna standardval (cream eller off-white bakgrund, kursiva accentord i rubriker, numrerade 01/02/03-etiketter, monospace-etiketter, pillerformade knappar). bygg-sajt steg 5 läser filen: inget härifrån utan skäl ur verksamhetens eget material. Regeln att inte titta på andra byggens sajter står kvar.

**Klart när:** Nästa bygge läser filen i steg 5, och KONCEPT.md säger varför typsnitt och toppsektion skiljer sig från de upptagna.
