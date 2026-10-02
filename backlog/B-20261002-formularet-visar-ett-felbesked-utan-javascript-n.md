---
id: B-20261002-formularet-visar-ett-felbesked-utan-javascript-n
status: avvisad
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · nextlevelbuilder/ui-ux-pro-max-skill
skapad: 2026-10-02
prio: normal
steg: 5 (mallens formulär) och 6 (provets demomottagare)
andrad: 2026-10-02T15:06Z
---
# Formuläret visar ett felbesked utan JavaScript när mottagaren skickar tillbaka ett ofullständigt inskick

**Varför:** Egen innovation ur kirurgens intag av ui-ux-pro-max (domen över källan är nej): demomottagaren skickar ett ofullständigt inskick till /kontakt/?saknas=1#forfragan (kontroller/prova.py rad 170), men varken Forfragan.astro, kunskap/forfragan.md eller bygg-sajt säger vad sidan ska visa då, så besökaren hamnar tyst på ett tomt formulär (Nielsens heuristik 9; GOV.UK:s felsammanfattning i teoretisk-grund.md rad 84). Av fyra byggen löste bara lulea-snickaren-abx det, och med JavaScript.

**Förslag:** mall/astro/src/components/Forfragan.astro: ett felbesked överst i formuläret, <p id="forfragan-saknas" class="ff-saknas" tabindex="-1">, dolt med CSS utom när det är :target, med texten att namn, telefon och meddelandet behövs och telefonnumret som väg vidare; texten som prop i verksamhetens ord. kontroller/prova.py rad 170 och kontroller/rokprov.sh rad 61: målet blir /kontakt/?saknas=1#forfragan-saknas. kunskap/forfragan.md rad 22–24: samma mål och att felbeskedet följer med mallen. Det som skrevs försvinner fortfarande; det står som känd begränsning tills serverfunktionen vid lansering kan rendera svaret.

**Klart när:** Med JavaScript avstängt och fälten fyllda med bara mellanslag visar kontaktsidan efter inskick felbeskedet ovanför formuläret med fokus på det; rokprov.sh slutar grönt.

**Avvisad (2026-10-02):** ersatt av B-20261002-mallens-formular-visar-ett-felbesked-utan-javasc (rättat antal byggen och klart-villkor)
