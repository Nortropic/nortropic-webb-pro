# Lärdomar — ägarens domar

**Ren designstart 2026-10-09** (ägarens uppdrag ~17:53Z, `kunskap/ren-designstart.md`): domarna L0–L6, A/B-omdömet och
de två kalibreringsförsöken från före brytpunkten är borttagna ur den aktiva miljön. De står ordagrant i git-historiken
(taggen `fore-ren-designstart-20261009`) och i det privata återställningsarkivet, styr inga agenter och verifierar inte
den nya metoden. Senaste dom före brytpunkten: L6; nästa dom får L7.

Loop 3: ägaren tittar på en sajt och dess rapport och dömer med egna ord, i dashboardens frågeformulär eller direkt
här. Domen står ordagrant i `underlag/LARDOMAR-original.md` (privat, utanför git) och i `kunder/<slug>/DOM.json`. Här,
i det publika repot, står domen utan personuppgifter: företagsnamn får stå; privatpersoners namn, telefonnummer,
adresser och hälsa inte, och det som tagits bort står i hakparentes, som [ägaren], [en kund] eller [numret] (ägarens
beslut 2026-10-03, BESLUT.md). Dashboarden skriver nya domar ordagrant i den privata filen och här bara betygen och
valen; den session som gör textändringen skriver lärdomen här, utan personuppgifter. Domen blir automatiskt en vilande
post i backloggen. Varje dom klassas först (kundbeslut, smakpreferens, metodhypotes eller generell rättelse), och bara
en generell rättelse blir en textändring i rätt fil, liten nog att läsa på fem minuter. Ingen dom blir ny mekanik.

Form:

```
## L<n> · ÅÅÅÅ-MM-DD · <slug>
- **<fråga med fast svar>** <svar>            (betygen och valen ur formuläret, aldrig fritext)
**Ägarens ord:** ordagrant i `underlag/LARDOMAR-original.md` (privat) och `kunder/<slug>/DOM.json`
**Lärdom:** <domen utan personuppgifter, skriven av sessionen som gör ändringen>
**Ändring:** <fil> — <vad som ändrades> (commit <sha>)
```
