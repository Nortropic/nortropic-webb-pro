# Uppdragsmall — beställt kunduppdrag

Codex helhetsbedömning 2026-10-04, punkt 1: skilj prospektdemo från beställt kunduppdrag. En **prospektdemo** byggs
ur offentligt material; briefen är då en hypotes och varje antagande märks (`antagande` i RESEARCH.md, §12–§13 i
briefen). Ett **beställt kunduppdrag** har dessutom `underlag/<slug>/UPPDRAG.md` med det kunden själv har bekräftat,
samlat före körningen (kunden behöver inte svara under bygget). Bygget läser det före briefen, och det som står där
skrivs aldrig om till antagande. Mallen nedan är formen; rubrikerna är obligatoriska, svaren kortfattade.

```markdown
# Uppdrag · <verksamhet> · <datum> · bekräftat av <namn och roll hos kunden>

## Målgrupp och uppgift
Vilken målgrupp sajten främst ska hjälpa, och med vilken uppgift (i besökarens ord). Högst tre, rangordnade.

## Lyckat resultat
Vad som räknas som ett lyckat resultat för verksamheten (fler offertförfrågningar, färre samtal om öppettider,
bokningar av en viss tjänst) och hur det märks.

## Bekräftade fakta
Uppgifter kunden bekräftat (tjänster, orter, priser eller prisprincip, öppet- och telefontider, försäkring och
F-skatt, certifieringar), en rad var med datum.

## Antaganden
Det vi tror men kunden inte bekräftat; varje rad blir en öppen fråga i briefen (§13).

## Material och integrationer
Vilket innehåll som finns (texter, bilder med rättigheter, logotyp), vem som tar fram det som saknas, och vilka
system sajten ska använda (bokning, beställning, formulärmottagare, karta), med vem som äger kontot.

## Primär handling
Den handling sajten främst ska leda till (ring, boka, begär offert, beställ, hitta hit) och vad "klar" betyder för
den: samtalet, den mottagna förfrågan, den genomförda bokningen.
```

Den primära handlingen i briefen följer härifrån. Saknas UPPDRAG.md är det en prospektdemo, och briefen säger det.
