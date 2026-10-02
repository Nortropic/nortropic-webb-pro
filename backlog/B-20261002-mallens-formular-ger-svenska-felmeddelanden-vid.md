---
id: B-20261002-mallens-formular-ger-svenska-felmeddelanden-vid
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · react-hook-form/react-hook-form
skapad: 2026-10-02
prio: normal
steg: 5 (mallens formulär)
---
# Mallens formulär ger svenska felmeddelanden vid fältet med setCustomValidity, med webbläsarens egna som reserv utan JavaScript

**Varför:** Egen innovation ur kirurgens intag av react-hook-form (domen över källan är nej). Byggstandarden 6.2 kräver svenska felmeddelanden vid fältet, men mallens Forfragan.astro lämnar det åt webbläsarens inbyggda validering, vars text följer webbläsarens språk, och ingen kontroll prövar det; källans väg för inbyggd validering, setCustomValidity följt av reportValidity (src/logic/validateField.ts rad 62–76), är samma mekanism utan bibliotek.

**Förslag:** mall/astro/src/components/Forfragan.astro, i det befintliga skriptet (rad 50–65): för varje fält med required i form.forfragan, lyssna på invalid och input, och sätt setCustomValidity till ett svenskt besked ur ett data-attribut på fältet (till exempel data-saknas="Skriv ditt namn") när validity.valueMissing, annars tomt; bygget skriver beskeden i verksamhetens ord. kunskap/forfragan.md efter rad 18: en rad om att felmeddelandena vid fältet är svenska med JavaScript och webbläsarens egna utan. Inga nya beroenden, inga nya fält.

**Klart när:** I en webbläsare med engelskt gränssnitt visar ett tomt namnfält det svenska beskedet vid inskick; med JavaScript avstängt stoppar webbläsaren inskicket med sitt eget besked och POST utan JS fungerar som förut; kontroller/rokprov.sh slutar grönt.
