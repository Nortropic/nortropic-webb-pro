---
id: B-20261002-bilder-md-anger-nar-varje-egen-bild-togs-ur-exif
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · gohugoio/hugo
skapad: 2026-10-02
prio: normal
steg: 1 (underlag: bilderna)
---
# BILDER.md anger när varje egen bild togs, ur EXIF eller filnamnet, så att daterade bevis kan bära en sektion

**Varför:** Ägaren pekade i L1 ut byggdagboken med datum ur bilderna som det bästa på sajten (LARDOMAR.md:31), men steg 1.2 ber bara om fil, källa, vad bilden visar och kvalitet: ett bygge läste EXIF, ett tolkade filnamnet och ett skrev datum okänt. Hugo (dömd nej som generator) läser skapandedatum, GPS och orientering ur bildens metadata som rutin; hos oss är det ad hoc.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md steg 1 punkt 2 (rad 75–79): BILDER.md får kolumnen datum, med källa per rad: EXIF DateTimeOriginal (läst med ett litet skript, sharp eller Pillow), annars telefonkamerans filnamn ÅÅÅÅMMDD_hhmmss märkt tolkning, annars okänt. En mening i kunskap/bild.md: metadata läses i underlaget men följer aldrig med i publicerade filer (astro:assets strippar dem), eftersom GPS-läge är en personuppgift.

**Klart när:** Nästa bygge har en datumkolumn i underlag/<slug>/bilder/BILDER.md med källa per datum (EXIF, filnamn eller okänt), och ett bygge med daterade jobbilder kan använda dem utan att själv uppfinna läsningen.
