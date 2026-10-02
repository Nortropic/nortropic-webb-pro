---
id: B-20261002-mallens-formular-visar-ett-felbesked-utan-javasc
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · nextlevelbuilder/ui-ux-pro-max-skill
skapad: 2026-10-02
prio: normal
steg: 5 (mallens formulär) och 6 (provets demomottagare)
commit: f5abe90
andrad: 2026-10-02T15:32Z
---
# Mallens formulär visar ett felbesked utan JavaScript när ett ofullständigt inskick kommer tillbaka

**Varför:** Egen innovation ur kirurgens intag av ui-ux-pro-max (domen över källan är nej): demomottagaren skickar ett ofullständigt inskick till /kontakt/?saknas=1#forfragan (kontroller/prova.py rad 170), men varken Forfragan.astro, kunskap/forfragan.md eller bygg-sajt säger vad sidan ska visa då, så besökaren hamnar tyst på ett tomt formulär (Nielsens heuristik 9; GOV.UK:s felsammanfattning i teoretisk-grund.md rad 84). Av de två byggen som har mallens formulär (lulea-snickaren-abx och -aby) visar bara abx ett besked, och det med JavaScript (kontakt.astro rad 50–63).

**Förslag:** mall/astro/src/components/Forfragan.astro: ett felbesked överst i formuläret, <p id="forfragan-saknas" class="ff-saknas" tabindex="-1">, dolt med CSS utom när det är :target, med texten att namn, telefon och meddelandet behövs och telefonnumret som väg vidare; texten som prop i verksamhetens ord. kontroller/prova.py rad 170 och kontroller/rokprov.sh rad 61: målet blir /kontakt/?saknas=1#forfragan-saknas. kunskap/forfragan.md rad 22–24: samma mål och att felbeskedet följer med mallen. Det som skrevs försvinner fortfarande; det står som känd begränsning tills serverfunktionen vid lansering kan rendera svaret.

**Klart när:** Med JavaScript avstängt och fälten fyllda med bara mellanslag visar kontaktsidan efter inskick felbeskedet ovanför formuläret och sidan står skrollad till det; rokprov.sh slutar grönt.

**Klar (2026-10-02):** #forfragan-saknas med :target; provat utan JS
