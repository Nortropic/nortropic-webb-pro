# Rensningen inför Nortropic 2.0: vad som styr agenterna och vad som blev historik

Ägarens uppdrag 2026-10-05 ~21:11Z (ordagrant i minnet): en reversibel rensning. Historiken bevaras, men ersatta beslut
och gamla kundspecifika smakdomar styr inte längre automatiskt. Verifierade kvalitetskrav står kvar. Inget bygge
hittills har varit bra nog, allt har varit generiskt, så inget tidigare bygge är en förebild. Agentuppdragen kontrolleras
så att gamla regler inte kommer tillbaka genom utdrag, ankare, mallar eller cache.

**Återställning:** taggen `fore-rensning-nortropic-2` är läget före; `git revert` av rensningens commit återställer allt.

## Vad som når agenterna (inventeringen 2026-10-05)

| Roll | Det som når den |
|---|---|
| Alla nästlade sessioner | `CLAUDE.md` (`--setting-sources project,local`) |
| Research, planerare, planprövning | kundens underlag (`atelje.underlag_rader`), metodens utdrag (`kontroller/metod.py`), kompetensblocken, kundens aktuella domar |
| Skissens och fördjupningens skapare | uppdraget, kundens fakta och material, metoden, rollernas kärna (skills), stilpaketet och Mobbins skärmar |
| Kandidatgranskaren och förfiningen | metoden för granska och förfina, kundens aktuella domar |
| Ateljéns panel och skapare (äldre vägen) | samma underlag och metod, kalibreringsankarna (externa sajter) |
| Helbygget | `.claude/skills/bygg-sajt/SKILL.md`, designreglerna, byggstandarden, mallens README |
| Byggets granskare | `kritik/GRANSKARE.md`, måttstockarna, kalibreringsankarna, den godkända startsidan, tidigare byggens första vy |
| Kontrollerna | `kontroller/standard_kontroll.py`, `stil.mjs`, `copy_kontroll.py`, `seo_kontroll.py`, `design.py` |

## Klassningen

- **Verifierade kvalitetskrav (kvar):** sanning och belägg, äkthet i bilder som visar verksamheten, tillgänglighet
  (WCAG 2.2 AA, felbesked vid fältet, reflow), prestanda och typsnittsbudget, NAP i JSON-LD och på kontaktsidan,
  noindex-sidor utanför sitemap, en skriftlig förfrågningsväg (ägarens ord om alla sajter), beställning av det som saknas.
- **Hypoteser (kvar, märkta):** kalibreringsankarna (externa sajter, `kunskap/visuell-niva.md`), högst två
  typsnittsfamiljer, brödsmulor när DESIGN.md väljer dem, de upptagna valen som mönster att undvika.
- **Historik (styr inte längre):** ägarens domar över tidigare byggen (`LARDOMAR.md`, privat original) och tidigare
  byggen som exempel; A/B-formen för mobilens första vy (sidhuvud på en rad, synlig meny, fast list, numret högst två
  gånger); gatuadressen i sidfoten på varje sida; tolerans byggd på en enskild dom ("typsnittet godtogs");
  "Archivo för målaren"; LARDOMAR som "gäller före allt" i skillsens anpassningar; den gamla stacken ("Astro, statisk,
  utan JavaScript", "bara CSS-recepten").

## Vad som ändrades

- Skillsens anpassningar (sju better-*, humanizer, writing-for-agents, kirurg): ägarens aktuella beslut och kundens
  domar går före; LARDOMAR är historik; stacken är de låsta beroendena.
- `CLAUDE.md`, `kunskap/designregler.md`, `kunskap/bild.md`, `kunskap/referensjakt.md`, `kunskap/byggstandard.md`,
  `kunskap/forfragan.md`, `kunskap/metodregler.md`, `kunskap/skillkrockar.md` (K06, K09, K29, K32, K39): domhänvisningar
  bakom krav ersatta av kravets grund; gamla citat märkta "Ersatt"; A/B-hypotesen flyttad till BESLUT.md:s tabell.
- Byggskillen: LARDOMAR läses inte; byggexemplen borta; mobilens första vy är riktningens inom kvalitetskraven.
- Granskarna (`kontroller/granska.py`, `kritik/GRANSKARE.md`): ingen LARDOMAR-kopia; tidigare byggen bara som exempel
  på det generiska; en fryst vinnare kräver ägarens godkännande.
- Ateljén och kandidatflödet: inga A/B-rader, ingen LARDOMAR-hänvisning; kandidatgranskaren och förfiningen får bara
  kundens aktuella domar; läsförbud för `LARDOMAR.md`, det privata originalet och andra kunders mappar i varje session.
- Kontrollerna: stilrapporten mäter mobilens första vy men varnar inte för smak; 7.4 kräver adressen på kontaktsidan och
  i JSON-LD, sidfoten är information; `kontroller/upptagna_val.py` utan domcitat, och en äldre `UPPTAGNA-VAL.md` läses inte.
- Mallen: README och 404 pekar på kundens kontaktvägar, inte en fast tel-länk i sidhuvudet.
- Backloggen och grupperingen (granskningen av rensningen 2026-10-06): backlog-skillen låter inte en dom före
  rensningen fälla eller motivera en post, och `kontroller/gruppera.py` grupperar bara domar och granskningar efter
  rensningen (före dem körs ingen session). Kontrollernas texter citerar kraven, inte domarna (L4).

## Vakten

`kontroller/styrning.py` läser det som når agenterna (instruktionerna, skillsen, kunskapsfilerna utom historiken,
mallen, metodens utdrag per steg och, med en kund, körningens cachade metod och UPPTAGNA-VAL.md) och söker efter
ersatta beslut och gamla kundsmakdomar. Ett citat märkt "Ersatt …: \"…\"" räknas inte. Startkontrollen kör den före
varje start, och revisionens regressionsfall kräver att den inte hittar något.
