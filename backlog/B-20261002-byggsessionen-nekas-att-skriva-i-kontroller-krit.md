---
id: B-20261002-byggsessionen-nekas-att-skriva-i-kontroller-krit
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · affaan-m/ECC
skapad: 2026-10-02
prio: normal
steg: kor.sh (ramarna för körningen), stoppvakten
---
# Byggsessionen nekas att skriva i kontroller/, kritik/, kunskap/, mall/, .claude/ och LARDOMAR.md

**Varför:** Ta in: ECC:s loop-design-check säger att byggaren aldrig får kunna ändra sina egna acceptansvillkor (felläge 3, Goodhart). Hos oss står förbudet bara som text (bygg-sajt/SKILL.md:47), medan kor.sh:40 ger bygget Write och Edit överallt; stoppvakten kör kontroller/prova.py och granskaren läser kritik/GRANSKARE.md ur samma arbetsträd som bygget kan skriva i.

**Förslag:** kor.sh rad 51–52: lägg till Edit- och Write-regler i --disallowedTools för kontroller/**, kritik/**, kunskap/**, mall/**, .claude/** och LARDOMAR.md (sökvägssyntaxen prövas med ett barn, se kommentaren rad 53–54). I sammanfattningen efter körningen (rad 73–97) skrivs en rad om git status för samma sökvägar inte är ren. bygg-sajt/SKILL.md:47 får en halv mening om att förbudet nu också gäller i behörigheterna.

**Klart när:** En provsession startad med kor.sh-argumenten nekas Edit på kontroller/prova.py och Write på kritik/GRANSKARE.md men får skriva i kunder/<slug>/ och underlag/<slug>/; kontroller/rokprov.sh är grönt.
