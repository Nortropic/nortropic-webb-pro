# Referensjakt — uppgiften styr urvalet

Beslut DIGITALA-YRKESFORMAGA-20260928: ersätter de aktiva urvalsregler som härletts ur webbgrunden
`inspirationskallor.md @ e4c8c52` och ett tidigare kundfall. Historiken bevaras i Git och REGISTER;
Norrglänta är inte kvalitetsreferens. Ingen ort, omdömesnivå, minimalism eller företagsstorlek bestämmer urvalet.

## Sök efter vad som behöver lösas

Utgå från kundens viktigaste uppgifter, innehåll, erbjudande, målgrupp och osäkerheter. Skriv vilka frågor
researchen ska besvara och avsluta när underlaget räcker för välgrundade val. Antalet sajter, kompar eller
sökningar är inte en kvot. En komplettering ska lösa en faktisk lucka, inte fylla en lista.

Använd tre källroller, med uppgiftsmotiverat urval. Samma källa får bära flera roller:

- **Bransch**: verkliga starka verksamhetssajter för erbjudande, innehåll, förtroende, kundresa och affärsmodell.
  En direkt konkurrent kan samtidigt vara en professionell hantverksreferens. Lokal närhet väljs när den
  förklarar marknaden eller kunduppgiften; två lokala konkurrenter är aldrig ett krav.
- **Hantverk**: ledande komposition, typografi, bildbehandling, rytm, responsivitet eller interaktionskvalitet,
  även från andra branscher. Motivera vad som faktiskt är väl löst och relevant att lära av.
- **UX/funktion**: etablerade användbarhetsmönster och primärkällor för tillgänglighet, formulär, bokning,
  betalning, innehållsstruktur eller andra funktioner. En teknisk dokumentation säger inte hur vacker en sajt är.

Skilj marknadsposition, företagsomdömen, designutmärkelser och själv observerad kvalitet. Betyg kan ge en
branschobservation men är inget designfilter. En utmärkelse är en sökingång, inte bevis på användarnytta.
Gallerier som Awwwards, SiteInspire, Godly, FWA, CSS Design Awards, Httpster, One Page Love och Land-book är möjliga
sökingångar, inte en stilhierarki. Mobbin (flöden och sektioner ur riktiga produkter; dimension 7, mobil ergonomi)
och Refero (stilar, skärmar, flöden, med en beslutsliggare som arbetssätt) är sökingångar i rollerna hantverk och
UX/funktion när de är anslutna; de saknar hantverkare och lokala tjänster och ger därför inte branschrollen. Ett litet företag får ha avancerat hantverk när uppgift, budget och drift
bär det. Följ galleri till faktisk sajt när slutsatsen gäller beteende eller responsivitet.

**Luckor som ofta finns.** Pröva dessa sökingångar i rollen UX/funktion när briefen bär något av följande, öppna dem med
`kontroller/webblasare/inspektera.mjs` som alla andra och skriv i REFERENSER.md vad du såg, eller varför ingen
passade:

- **Förtroendeblocket hos en svensk hantverkare** (F-skatt, försäkring, org.nr, behörighet, omdömen): hur en svensk
  firma visar det på sin egen sajt, och hur Hantverkskollen, Reco och Offerta visar en profil; för elfirmor
  Elsäkerhetsverkets "Kolla elföretaget".
- **En daterad bildserie på 390 px** (jobb med ort och datum, före och efter): hur en serie läses i mobilens bredd utan
  att bli ett galleri.
- **Resultat med få bilder** (en eller två egna foton): en sajt där typografi, kvitton eller ett motiv bär sidan när
  bilderna inte räcker.

Ingen kvot och inget facit: luckan är en plats att leta på, inte själv en referens.

## Läs och se på riktigt

Öppna de utvalda sajterna i riktig webbläsare på relevant mobil och större vy. Läs representativt innehåll,
öppna relevant meny, tjänst, formulär/felväg eller annan tillåten interaktion. Ange exakt vad som observerats.
Läsande utforskning får inte bli verkliga inskick, köp, bokningar, konton eller kontakt utan mandat.

Spara ett litet användbart visuellt paket: de vyer och tillstånd som förklarar ett viktigt val, med URL,
fångsttid, viewport, avsnitt/tillstånd och kort observation. För varje referens ange:

- roller och urvalsskäl; vad som gör den stark för den aktuella frågan;
- status: faktisk livevy, galleribild, text, delvis läst eller otillgänglig;
- bild-/beteendepekare, vad som togs med, vad som avvisades och begränsningen i observationen;
- vilket konkret kandidatval den ska påverka och hur det ska prövas.

En sökträff eller marknadsföringstext är inte observerad layout eller funktion. En stillbild visar inte
animation, touchbeteende eller genomförd transaktion. En otillgänglig källa får inte märkas sedd; välj en
annan källa för nödvändig jämförelse. Kundens egna referenser får samma noggranna läsning som egen research.
Webbreferensernas skärmbilder är privat jämförelseunderlag, inte licens att återpublicera deras tillgångar.

## Från observation till skapande

För in observationerna i research.md §13 och det valda urvalet i SKAPARUNDERLAG.json enligt
skapandeunderlag.md. Brief §7 förklarar sambandet behov → observerat drag → egen lösning → prövning.
Ett moodboard med bara färg, serif och rundningar räcker inte: visa även innehåll, hierarki, rytm,
bildbeskärning och relevant interaktion. Palett, layout och typsnitt får kopieras som utgångspunkt, med vår touch och
verksamhetens material ovanpå; identitet, texter och bilder kopieras inte.

Bildinventeringen i research §7 skiljer kundmaterial, licensierat material och syntetiska illustrationer.
Dokumentera rättigheter och tänkt roll innan användning; genererad bild är inte verkligt kundbevis.
Referensbild och publicerbar tillgång är olika roller. Läs bild.md för bearbetning och responsiva leveranser.

## Insamlingen är ett eget, avgränsat steg

Kandidaterna undersöks innan urvalet låses (ägarbeslut 2026-10-04): byggaren skriver REFERENSUPPDRAG.json ur
researchen, och `kontroller/referens.py` öppnar varje kandidat läsande med en färsk webbläsarprofil, prövar värden
(publik adress, omdirigeringar hopp för hopp) och tillåter sajtens egna resursdomäner bara för den inspektionen, så att
bilder och typsnitt är laddade. Paketet `underlag/<slug>/referenser/paket-vNN/` bär adress, tidpunkt, observationer
(status, laddade bilder och typsnitt, kvarvarande blockeringar) och begränsningar (kakdialog, tomma bilder).
Byggare, ateljé och granskare pekar på samma version; en komplettering ger en ny version och öppnar aldrig
byggsessionens nät. Med sandlådan på körs steget av webbtjänsten med uppdraget och utkatalogen som enda
beröringspunkter; dess behörigheter är skilda från byggsessionens.
