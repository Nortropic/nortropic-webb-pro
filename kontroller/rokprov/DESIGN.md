# DESIGN.md · Rökprov (fiktiv testsajt)

Den aktuella designen för rökprovets testsajt. Den finns för att pröva designkontraktet (`kontroller/design.py`,
provets grind `design`), inte som förebild: neutral systemtypografi, vit yta, mörk text, blå länkfärg.

## Komposition

En spalt, högst 40rem bred, centrerad; sidhuvud, innehåll och sidfot har samma bredd och luft.

## Typografi

Systemtypsnittet i två roller; rubriken 2rem fet, brödtexten 1rem. Etikettrollen och markeringsfärgen finns för att
pröva grinden mot minifierarens omskrivningar (0.5rem, -0.02em, clamp(), citerat typsnittsnamn, #ffd700 som gold).

## Bildbehandling

Inga bilder; beställningen står i underlaget.

## Responsiva regler

Samma spalt på alla bredder; luften är 1rem.

## Avvikelser från huvudreferensen

Ingen huvudreferens (testsajt).

```json design
{
  "schema": 1,
  "farger": {
    "yta": {"varde": "#ffffff", "roll": "sidans bakgrund, hela ytan", "kalla": "valt: neutral testyta"},
    "text": {"varde": "#1a1a1a", "roll": "brödtext och rubriker", "kalla": "valt: hög kontrast"},
    "accent": {"varde": "#0b57d0", "roll": "länkar och tema", "kalla": "valt: mallens temafärg i provet"},
    "markering": {"varde": "#ffd700", "roll": "provfärg som minifieraren skriver som gold", "kalla": "valt: prov av normeringen"}
  },
  "typsnitt": {
    "rubrik": {"familj": "system-ui", "reserv": "sans-serif", "vikt": 700, "storlek": "2rem", "radavstand": "1.6", "kalla": "valt: systemtypsnitt"},
    "brodtext": {"familj": "system-ui", "reserv": "sans-serif", "vikt": 400, "storlek": "1rem", "radavstand": "1.6", "kalla": "valt: systemtypsnitt"},
    "etikett": {"familj": "Helvetica Neue", "reserv": "Arial, sans-serif", "vikt": 500, "storlek": "clamp(0.875rem, 0.8rem + 0.3vw, 1rem)", "radavstand": "1.50", "teckenavstand": "-0.02em", "kalla": "valt: prov av normeringen"}
  },
  "avstand": {"s": "0.5rem", "m": "1rem"},
  "spalter": {"390": {"maxbredd": "40rem"}, "1440": {"maxbredd": "40rem"}},
  "kontrast": [["text", "yta", 4.5], ["accent", "yta", 4.5]],
  "struktur": {"brodsmulor": true},
  "avvikelser": []
}
```
