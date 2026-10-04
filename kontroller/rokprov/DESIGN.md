# DESIGN.md · Rökprov (fiktiv testsajt)

Den aktuella designen för rökprovets testsajt. Den finns för att pröva designkontraktet (`kontroller/design.py`,
provets grind `design`), inte som förebild: neutral systemtypografi, vit yta, mörk text, blå länkfärg.

## Komposition

En spalt, högst 40rem bred, centrerad; sidhuvud, innehåll och sidfot har samma bredd och luft.

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
    "accent": {"varde": "#0b57d0", "roll": "länkar och tema", "kalla": "valt: mallens temafärg i provet"}
  },
  "typsnitt": {
    "rubrik": {"familj": "system-ui", "reserv": "sans-serif", "vikt": 700, "storlek": "2rem", "radavstand": "1.6", "kalla": "valt: systemtypsnitt"},
    "brodtext": {"familj": "system-ui", "reserv": "sans-serif", "vikt": 400, "storlek": "1rem", "radavstand": "1.6", "kalla": "valt: systemtypsnitt"}
  },
  "avstand": {"m": "1rem"},
  "spalter": {"390": {"maxbredd": "40rem"}, "1440": {"maxbredd": "40rem"}},
  "kontrast": [["text", "yta", 4.5], ["accent", "yta", 4.5]],
  "avvikelser": []
}
```
