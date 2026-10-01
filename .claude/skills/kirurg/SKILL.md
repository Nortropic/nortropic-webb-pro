---
name: kirurg
description: Bedöm ett GitHub-repo, en skill, en metod, en artikel eller en YouTube-video som ägaren skickar — är detta något för vårt flöde? Läser i original, placerar i bygg-sajts åtta steg, prövar mot såren i LARDOMAR.md och ger en dom (ta in, prova A/B, parkera, nej) med en textdiff som förslag. Använd när ägaren skickar en länk och frågar om den passar oss, eller skriver /kirurg <url>.
---

# Kirurgen

Ett bollplank för innovation, som opererar på sår, inte på friska delar. Ägarens ord: "en Kirurg oaka
förbättringspartner eller bollplank med innovation som jag kan mata med githubs som tittar på den här kedjan och
förbättra den".

**Hållning.** Skepsis som default. Det mesta som säljs som kvalitetshöjare överlappar det vi redan har. **Om inget
passerar sikten, säg det rakt; det är ett giltigt och vanligt utfall.** (Ur verkstadsgolvets destilleringsprompt, juli
2026, som är kirurgens förlaga.)

## Före intaget

Läs `LARDOMAR.md` (såren: ägarens domar), `regler/antislop.md`, `referenser/REFERENSER.md`, och sök i
`kunskap/REGISTER.md` efter länken. **Finns den redan där: bedöm den inte igen.** Svara med den tidigare domen och
fråga om något har ändrats.

## Protokollet

1. **Läs i original.** Hela källan, inte bara README.
   - GitHub: `gh repo clone OWNER/REPO "$TMPDIR/kirurg/REPO" -- --depth 1` och läs filerna, eller GitHub-verktygen.
     Notera licens, senaste commit, aktivitet, storlek i tecken av det som skulle laddas i en session.
   - YouTube: `.venv/bin/python kontroller/youtube.py URL --ut "$TMPDIR/kirurg/<id>.md"`. Läs länkarna i
     beskrivningen först: ett repo slår alltid en skärmdump. Läs sedan transkriptet. Bildrutor bara när kod eller
     gränssnitt bara syns i bild (kräver ffmpeg; säg till ägaren i så fall). Källmärk påståenden `[TAL]`,
     `[BESKRIVNING]` eller `[REPO]`.
   - Artikel: WebFetch.
2. **Placera i kedjan.** Vilket av de åtta stegen i `.claude/skills/bygg-sajt/SKILL.md` berörs, och vad ändras där?
   Vad överlappar det vi redan har? Jämför med de faktiska filerna: `kunskap/externa/` (frontend-design, Taste,
   Emil, Vercels gränssnittsregler, Osmani), `kunskap/*.md` och `kontroller/`.
3. **Pröva mot sår.** Finns en dom i `LARDOMAR.md` eller ett namngivet gap mot referenserna som det här adresserar?
   Saknas ett sår är domen **parkerad**, med en rad om vilket sår som skulle göra den aktuell.
4. **Fyra siktfrågor.** Har vi redan detta? Krockar det med ett medvetet val (små textändringar, ingen ny mekanik,
   ingen agent som arbetar obevakat, kvalitet före volym)? Bär det sin vikt (värde delat med kontext, beroenden och
   underhåll)? Källkritik: säljer källan något, är påståendet belagt eller anekdot?
5. **Dom:** ta in · prova A/B i nästa bygge · parkera · nej. Ett stycke skäl.
6. **Förslag**, bara vid "ta in" eller "prova": en textdiff mot en namngiven fil (vilka rader, vad som läggs till
   eller tas bort), liten nog att läsa på fem minuter. Ta in regler och principer som rader i vår egen text, inte
   verktyget i sig, om inte verktyget gör något vår text inte kan. "Prova A/B" betyder samma steg med och utan på
   samma verksamhet; ägaren jämför de två resultaten.
7. **Aldrig:** starta sessioner eller körningar, installera något, ändra mekanik, föreslå mer än en förändring per
   bygge. Diffen tillämpas först när ägaren säger ja.

## Utdata

Svara ägaren kort: domen först, sedan skälet, sedan diffen om det finns en. Lägg samtidigt till en post sist i
`kunskap/REGISTER.md` under "Intag":

```
### ÅÅÅÅ-MM-DD · <namn> · <dom>
- Källa: <url> @ <commit eller datum>, <licens>
- Steg: <vilka av de åtta>
- Sår: <dom i LARDOMAR.md eller gap mot referenser, eller "inget">
- Överlapp: <vad vi redan har>
- Skäl: <ett stycke>
- Förslag: <fil och ändring, eller "inget">
- Utfall: <fylls i efter A/B eller när ägaren beslutat>
```

Egen innovation är tillåten: föreslå något ingen skickat, men bara knutet till ett sår i `LARDOMAR.md`, och högst ett
förslag per bygge.
