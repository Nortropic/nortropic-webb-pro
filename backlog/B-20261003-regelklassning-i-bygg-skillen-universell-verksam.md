---
id: B-20261003-regelklassning-i-bygg-skillen-universell-verksam
status: klar
kalla: bevakning
kallref: Codex bedömning av den visuella nivån, 2026-10-03
skapad: 2026-10-03
prio: normal
commit: c964ea9
andrad: 2026-10-09T08:37Z
---
# Regelklassning i bygg-skillen: universell, verksamhetens behov eller visuell preferens från piloten (ägarbeslut om mobilreglerna)

**Varför:** Codex 2026-10-03: skillen föreskriver mycket av mobilens komposition (sidhuvud, synlig meny, rubrik, handling, foto, fast list) samtidigt som olika visuella riktningar efterfrågas; den samlade regelmängden gör kunderna lika. Originalitet bör bedömas i uttryck, bildspråk och komposition, medan navigation och formulär får vara standard.

**Precisering (Codex 2026-10-03):** agenten förbereder konkreta jämförelser, samma kund med och utan regeln som synliga alternativ (bilder, inte text), så att ägarens beslut om mobilreglerna bygger på vad som faktiskt hjälper olika kundtyper.

**Förslag:** Märk varje regel i .claude/skills/bygg-sajt/SKILL.md steg 5 och i kunskap/ med klass: universell (säkerhet, sanning, tillgänglighet), verksamhetens behov (styr kundens lösning) eller visuell preferens/lärdom (används när förutsättningarna passar). Mobilreglerna från L4–L6 märks som preferens tills ägaren säger universell. GRANSKARE.md: originalitet bedöms inte på navigation och formulär.

**Klart när:** Ägaren har beslutat om mobilreglerna med bildjämförelser som underlag; metodreglerna märker dem efter beslutet, och GRANSKARE.md säger att navigation och formulär får vara standard; stilvarningarna läses inte som fel av granskaren.

**Vilande (2026-10-05):** Avstämt 2026-10-05: klassningen finns i kunskap/metodregler.md, och stilrapportens mobilregler är varningar, inte provfel. Kvar: ägarens beslut om mobilreglerna med bildjämförelser (samma kund med och utan regeln), och en mening i GRANSKARE.md om att navigation och formulär får vara standard. Färdigkriteriet omskrivet i avstämningen; tidigare: "Ägaren har svarat på vilka mobilregler som är universella; SKILL.md och GRANSKARE.md bär klasserna; ett bygge för en annan kundtyp (boka behandling, bedöma hantverk, förstå företagstjänst) kan avvika från preferenserna utan fel i provet."

**Vilande (2026-10-09):** Avstämt 2026-10-09 (ägarens uppdrag punkt 3; avstämningstabellen regel → källa → räckvidd → verkställs → klassning → fråga i RAPPORT-2026-10-09-sju-backlogomraden). Redan på plats: GRANSKARE.md säger att navigation och formulär får vara standard, och bygg-skillen låter den godkända kandidaten avgöra mobilens komposition (rensningen inför 2.0). Rättat (3bd4455): klickytor 24×24 px (WCAG 2.2 AA, 2.5.8) och 44×44 för knappen för den primära handlingen (Nortropics produktkrav, inte WCAG:s minimum och inget krav på alla länkar) är åtskilda i designregler.md och byggstandarden 3.3; 'helst ingen gömd meny' (5.2) är en designhypotes; stilrapportens mått av mobilens första vy är underlag i GRANSKARE.md steg 9; kravexemplet i bygg-skillen beskriver en funktion, inte en placering. Inga nya krav på menyplacering, sidhuvudets höjd, rubrikkomposition, foto i första skärmen eller fast list. Kvar, ägarens beslut: det gemensamma kravet 'den primära handlingen syns i första vyn på mobilen och går att nå med tummen' (designregler.md); alternativ A–C med bilder ur de dömda K01–K13 i rapporten, rekommendation B (Nortropics produktkrav för dagens erbjudande: nås från mobilens första vy, 44×44; tummen en designhypotes).

**Vilande (2026-10-09):** 2026-10-09: GR-20261009-metod-till-resultat-codex#H03 hör hit: placeringen av den primära handlingen prövas mot toppuppgift och sidtyp med bildjämförelser; tillgänglighet och fungerande kontakt består. Alternativen A–C och rekommendationen står i RAPPORT-2026-10-09-sju-backlogomraden; inget ägarbeslut fattat.

**Klar (2026-10-09):** Ägarens beslut 2026-10-09 (alternativ C med precisering; BESLUT.md, tillägget samma dag) genomfört i c964ea9: den primära handlingen är tydlig och lätt att hitta; i mobilens första vy när briefens prioriterade besökaruppgift motiverar det, annars märkt som hypotes; minst 44×44 CSS-pixlar för primära interaktiva kontroller som Nortropics produktkrav, skilt från WCAG:s minimum; tummen och fast nederlist är designhypoteser; funktion och visuell kvalitet bedöms var för sig. Styrningsvakten fäller den ersatta formuleringen. Inte verifierad: ingen verklig granskare eller skapare har körts med texterna.
