# Autonomins mått och förmågeprovet

Codex helhetsbedömning 2026-10-04, punkt 8 och 9 (rekommenderad ordning 5): kvalitet, tillförlitlighet och
modellanvändning optimeras tillsammans, och tre frågor behöver egna belägg: känner granskaren igen ägarens ribba
(kalibreringen, `kontroller/granskarforsok/kalibrering.py`), kan byggaren återkommande nå den (förmågeprovet nedan), och
kan verkliga besökare använda sajterna (människor, aldrig en modell; NN/g: syntetiska användare ger hypoteser).

## Måtten

`.venv/bin/python kontroller/autonomi.py` skriver `kunder/AUTONOMI.md` och `kunder/AUTONOMI.json` (privata). Det läser
byggens loggar och domar och ändrar ingenting:

- **Accepterade:** andelen dömda byggen som ägaren skulle visa för verksamheten utan större ändringar (namnsvaret
  "Ja, som den är" eller "Ja, efter små ändringar"), och hur många som blev tydligt dåliga (namnsvaret "Nej").
  Namnsvaret gäller ribban när domen gavs; äldre domar gavs innan ägaren sa att de egna byggena inte håller
  (2026-10-03).
- **Modelltid, turer och listpris** per bygge: byggets sessioner med omtag, granskarnas omgångar och ateljén.
  Listpriset (`total_cost_usd`) är ett mått på kvoten, inte en kostnad.
- **Ägarens minuter:** från att byggets sida eller designprovet öppnades i dashboarden till att domen sparades
  (sparas med domen sedan 2026-10-05).
- **Återkommande fel:** hur ofta varje grind var röd över provets körningar.
- **Iterationens effekt:** om en granskningsomgång försämrade den bästa tidigare (godkänd före underkänd, färre
  blockerande fynd, högre betyg) och om den sista omgången var den bästa. Mer iteration är en hypotes om förbättring;
  ateljén bevarar redan sin vinnare, och en sista omgång som är sämre än den bästa är ett fynd.
- **Variation:** två körningar av samma verksamhet (A/B-paren) bredvid varandra.

## Förmågeprovet

Rökprovet (`kontroller/rokprov.sh`) är ett regressionsprov: det visar att kända beteenden håller. Förmågeprovet visar
om flödet kan lösa en svår kunduppgift, och redovisas för sig.

- **Varierade kundfall**, inte flera omtag av samma firma: olika innehållsmängd (få sidor eller många tjänster),
  bildunderlag (egna bra foton, få eller svaga foton), kontaktvägar (telefon, bokningssystem, offertformulär,
  beställning) och designbehov (hantverk, skönhet, mat, teknik och företagskunder).
- **Orörda fall:** några kundfall används aldrig för att ändra instruktionerna under utvecklingen; de körs bara för
  mätningen, som kalibreringens orörda exempel.
- **Två körningar per fall** med samma modell, brief och material, så att variationen syns.
- **Ägarens blinda dom** i dashboarden; kvalitet, fel, tid och kvot redovisas var för sig ur `autonomi.py`.
- **När:** först när designprovet visat att ateljévägen håller (ägarens blinda dom i dashboarden) och granskaren
  prövats på de orörda exemplen K14–K19. Annars mäts en väg som ändå ska ändras.
