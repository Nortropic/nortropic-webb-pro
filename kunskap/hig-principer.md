# HIG-principerna i interaktionsgranskningen

Professionsfil för granskning och kritik enligt `kunskap/metodkarta.md` och ägarens uppdrag 2026-10-07, punkt 5E.
Det är inget krav på Apples visuella stil. Huvudreferensen bär layout, palett och typografi; HIG ger frågor om
beteende, återkoppling, fokus, avbrytbar rörelse, begriplighet, textstorlek och tillgänglighet. Texten är vår
webbanpassning. Apples plattformsmått och interaktionsmönster blir inte automatiskt webbkrav. WCAG och WAI-ARIA
APG används för webbens krav respektive mönster; `kunskap/designregler.md` och `kunskap/byggstandard.md` bär våra
befintliga kvalitetskrav. Den här filen inför inga nya universella stil- eller storleksregler.

## Rörelse: med syfte, valfri och avbrytbar

Rörelse förklarar en övergång eller ger återkoppling. Besökaren ska kunna fortsätta handla utan att vänta på
animationen. Status får inte bäras enbart av rörelse eller färg. Pröva `prefers-reduced-motion` med
onödiga förflyttningar, zoom och upprepningar borttagna; även en toning ska vara motiverad. Tid och easing kommer
från emil-animate. emil-apple-design kan användas för fysisk, avbrytbar rörelse utan att göra sidan Apple-lik.

WCAG 2.2.2 skiljer två fall: rörelse, blinkning eller skrollning som startar automatiskt, varar mer än fem sekunder
och visas parallellt med annat innehåll behöver kunna pausas, stoppas eller döljas, om den inte är väsentlig.
För automatisk uppdatering som startar själv och visas parallellt behövs paus, stopp, döljning eller styrning av
frekvensen, med samma väsentlighetsundantag; här finns ingen femsekundersgräns. Ett reducerat rörelseläge ersätter
inte dessa kontroller. Pröva också korta animationers obehag och blockerande beteende, utan att felaktigt kalla
varje automatisk rörelse ett brott mot 2.2.2.

Frågor: vad tillför rörelsen; kan nästa handling börja direkt; fungerar sidan med reducerad rörelse; finns
kontrollerna som just detta innehåll kräver? En stillbild visar inte rörelsens tid eller avbrytbarhet.

Källa: https://developer.apple.com/design/human-interface-guidelines/motion (läst 2026-10-07).
Källa: https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html (läst 2026-10-07).

## Fokus och val: synligt, förutsägbart, rätt för komponenten

Fokus är synligt och följer en begriplig ordning. Ett fast sidhuvud får inte skymma det. När en komponent stängs
eller tas bort återförs fokus till utlösaren eller nästa logiska plats; dölj inte fokus som lösning på ett fel.

Skilj vanlig webbplatsnavigation med disclosure från en modal dialog. En disclosure-knapp visar eller döljer
länkar och har `aria-expanded`; Tab får gå vidare ut ur navigationen. Gör ingen generell fokusfälla för öppna
menyer. En modal dialog får fokus när den öppnas, håller Tab och Shift+Tab inom dialogen, stängs normalt med
Escape och återför fokus vid stängning. En verklig ARIA-meny har ett eget tangentbordsmönster; välj den inte
enbart för att webbplatsen kallar navigationen meny.

Frågor: kommer tangentbordet åt allt; vilken komponent används; går det att lämna navigationen; återförs fokus
rätt; är bakgrunden inaktiv bara när dialogen är modal? Bilder av fokus ersätter inte tangentbordsprovet.

Källa: https://developer.apple.com/design/human-interface-guidelines/focus-and-selection (läst 2026-10-07).
Källa: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/examples/disclosure-navigation/ (läst 2026-10-07).
Källa: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/ (läst 2026-10-07).

## Återkoppling: tillstånd, fel och nästa handling

Besökaren behöver veta om en handling pågår, lyckades eller misslyckades. Visa fel nära fältet som text kopplad
med exempelvis `aria-describedby`, bevara inmatade uppgifter och ge en väg vidare. En skickad förfrågan ska ha
bekräftad status; en knappanimation bevisar inte leverans. Använd färg tillsammans med text eller form och gör
status tillgänglig för hjälpmedel utan onödiga avbrott. Bekräfta före oåterkallelig förlust.

Frågor: syns laddning, fel och framgång; är texten begriplig; kommer status fram med skärmläsare; kan besökaren
rätta felet utan att börja om? Skilj faktisk mottagning från en lokal bekräftelse i granskningen.

Källa: https://developer.apple.com/design/human-interface-guidelines/feedback (läst 2026-10-07).

## Begriplighet: bekanta mönster och alternativ

Samma slags element beter sig lika och har begripliga etiketter. Komplexa gester har ett enkelt alternativ,
exempelvis knappar till ett svep. Viktig information försvinner inte innan besökaren hunnit uppfatta eller använda
den. Pröva tid, instruktioner och möjligheten att rätta misstag i själva uppgiften, inte bara på en skärmbild.

Källa: https://developer.apple.com/design/human-interface-guidelines/accessibility (läst 2026-10-07).

## Typografi och textstorlek: hierarki och faktisk förstoring

Bedöm läsbarhet med sidans typsnitt, vikt, kontrast, radlängd och verkliga innehåll i mobil och dator. Apples
native-mått i pt översätts inte till CSS-px som ett nytt minimikrav. Tunna små tecken behöver prövas särskilt.
Använd relativa storlekar och undvik att viewport-enheter ensamma hindrar textförstoring.

WCAG 1.4.4 kräver att text kan förstoras till 200 % utan förlust av innehåll eller funktion, med kriteriets
undantag för undertexter och bilder av text. Kör ett faktiskt förstoringstest, exempelvis webbläsarzoom, och
kontrollera navigation, formulär och innehåll. Ett separat reflow-prov enligt 1.4.10 prövar layout vid motsvarande
320 CSS-px bredd (för vertikalt innehåll, med kriteriets undantag). En vanlig bild vid 320 px bevisar inte 200 %
textförstoring. Redovisa båda mätningarna och vad som inte prövats.

Källa: https://developer.apple.com/design/human-interface-guidelines/typography (läst 2026-10-07).
Källa: https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html (läst 2026-10-07).
Källa: https://www.w3.org/WAI/WCAG22/Understanding/reflow.html (läst 2026-10-07).

## Tillgänglighet: krav och provens räckvidd

För text enligt WCAG 1.4.3 gäller normalt 4,5:1. Stor text får 3:1: minst 18 pt, alltså 24 CSS-px, eller fet
text minst 14 pt, cirka 18,67 CSS-px. Fet stil ensam räcker inte. Kriteriet har undantag, exempelvis logotyper
och viss oväsentlig text. Pröva relevanta tillstånd och, när sidan har det, mörkt läge. Gränssnittskontrast
bedöms enligt 1.4.11 och våra befintliga designregler, inte genom att tillämpa textgränsen på alla ytor.

Träffytor följer befintlig byggstandard 3.3: 24 × 24 CSS-px för allt och 44 × 44 för primära knappar i 390.
Det är vår regel. WCAG 2.5.8 har även undantag för bland annat tillräckligt mellanrum, löptext och likvärdiga
kontroller; redovisa skillnaden mellan standardkravet och vår ribba. Apples native-mått är ingen enhetskonvertering
för dessa webbmått.

Axe hittar vissa maskinellt upptäckbara fel. Ett grönt resultat bevisar inte WCAG AA eller att sidan är användbar.
Det behövs mänsklig bedömning och funktionella prov, bland annat tangentbord, hjälpmedel, zoom, begriplighet och
återkoppling. Beskriv täckning och kvarvarande begränsningar; markera inte något som prövat bara för att en skill
laddats eller en skärmbild finns.

Källa: https://developer.apple.com/design/human-interface-guidelines/accessibility (läst 2026-10-07).
Källa: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html (läst 2026-10-07).
Källa: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html (läst 2026-10-07).
Källa: https://www.w3.org/WAI/test-evaluate/ (läst 2026-10-07).

## Så används filen

Granskningen läser filen med kärnan, prövar relevanta tillstånd i den renderade sidan och rättar konkreta brister
med plats, bredd, tillstånd och före/efter. Håll isär tekniskt prov, mänsklig bedömning och hypotes. Blindkritiken
bedömer bara det bilderna visar; tangentbordsfunktion, rörelse och bekräftad leverans står annars som inte bedömda.
Principerna är frågor, kvalitetskraven är krav. Ett motiv från HIG är inte ensamt ett skäl att underkänna en
visuell riktning eller byta dess stil.
