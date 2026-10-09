# Teoretisk grund: principer, metoder och litteratur

Ägarens bilaga B till byggstandarden (inklistrad 2026-10-02), med metoderna B.2–B.4 ur ägarens granskningsprompt.
Det här är **måttstocken för hur vi arbetar**: kirurgen jämför varje källa med vårt flöde och med det litteraturen
säger, och en session som genomför backloggen kontrollerar sina ändringar mot den. Byggena läser den inte i sin
helhet; metoderna som byggaren och granskaren använder står i `.claude/skills/bygg-sajt/SKILL.md` och
`kritik/GRANSKARE.md`, och de verifierbara punkterna i `kunskap/byggstandard.md`.

Varje avsnitt i byggstandarden förankras i (P) principer, (M) metoder och (L) litteratur och standarder. Kortform
Författare (år) i texten; fullständiga referenser under C.

## Våra åtta steg mot processmodellen

| Processmodellen (A) | Våra steg | Det vi inte gör obevakat |
|---|---|---|
| 1 Förstå | 1 Underlag, 2 Diagnos (med heuristisk utvärdering och kognitiv genomgång av deras sajt) | Intervjuer med verkliga slutkunder; omdömen är sekundärdata och hypotesunderlag, inte en ersättning |
| 2 Specificera | 3 Brief med toppuppgifter och krav i EARS-form; Definition of Done = provets grindar och granskaren | MoSCoW görs implicit i sajtkartan |
| 3 Designa | 4 Innehåll före form, 5 Koncept och bygge | |
| 4 Bygga | 5 Bygge, snabbprov | CI/CD och grenar hör till lanseringen |
| 5 Utvärdera | 6 Prov (axe, Lighthouse, byggstandarden, femsekunderstest), den oberoende granskaren (heuristisk utvärdering, kognitiv genomgång, WCAG-EM-urval) | Användartest med motiverat urval och eventuell SUS; en modellbaserad besökare är inte en människa |
| 6 Lansera och lära | 7 Rapport, 8 Ägarens dom som textändring (build–measure–learn) | Fältdata (CrUX, sökkonsolen) finns först efter lansering |

## A. Processmodell – så byggs en sajt enligt litteraturen

Ramverk: människocentrerad design (ISO 9241-210:2019) körd iterativt enligt Double Diamond (Design Council 2019) och
Lean UX (Gothelf & Seiden 2021). På uppsatsnivå: Design Science Research (Hevner m.fl. 2004; Peffers m.fl. 2007) –
bygg artefakten, utvärdera, iterera.

1. **Förstå.** Kundens verksamhet och kundens kunder: rich picture/CATWOE (Checkland 1999), jobs-to-be-done-intervjuer
   med verkliga slutkunder, urval efter fråga och målgrupp (Christensen m.fl. 2016), kundresa/service blueprint (Stickdorn m.fl. 2018),
   innehållsinventering (Halvorson & Rach 2012).
2. **Specificera.** Krav i EARS-syntax (Mavin m.fl. 2009), prioritering MoSCoW, Definition of Done (Schwaber &
   Sutherland 2020) = standardens 10.3.
3. **Designa.** Content first, mobile first (Wroblewski 2011), progressive enhancement (Gustafson 2015; Keith 2016),
   komponenter/tokens (Frost 2016), informationsarkitektur (Rosenfeld, Morville & Arango 2015).
4. **Bygga.** Continuous integration/delivery (Fowler 2006; Humble & Farley 2010), korta grenar, testpyramid,
   prestandabudget som CI-gate (Kadlec 2013).
5. **Utvärdera.** Expertgranskning: heuristisk utvärdering (Nielsen & Molich 1990; Nielsen 1994), kognitiv genomgång av
   nyckeluppgiften (Wharton m.fl. 1994), WCAG-EM-stickprov (W3C 2014), lab- och fältmätning (Walton 2020).
   Användartest: små iterativa urval för kvalitativ problemupptäckt (Nielsen & Landauer 1993), anpassade efter
   målgrupper och undersökningsfråga. SUS (Brooke 1996) kräver verkliga deltagares svar; ett referensvärde är ingen godkännandegräns.
6. **Lansera och lära.** Gate enligt DoD, fältdata (CrUX/GSC), build–measure–learn (Ries 2011), leveransmått enligt
   DORA (Forsgren, Humble & Kim 2018).

## B. Per avsnitt i standarden

**0 Principer.** P: Progressive enhancement; mobile first; responsiv design (Marcotte 2010); "rule of least power" –
HTML före JS (Berners-Lee & Mendelsohn 2006); evidens före åsikt – iterativ, användarcentrerad, utvärderingsdriven
(ISO 9241-210). M: Processmodellen i A. L: Marcotte (2010); Wroblewski (2011); Gustafson (2015); Keith (2016);
ISO 9241-210 (2019).

**1 Grund och arkitektur.** P: Separation of concerns; DRY/KISS/YAGNI (Hunt & Thomas 2019); konfiguration i miljön
(Wiggins 2011); fail-safe defaults och least privilege (Saltzer & Schroeder 1975); stabilitetsmönster (Nygard 2018);
leveranskedjan som attackyta (OWASP A03:2025). M: CI/CD; DORA-mått; beroendeskanning/SBOM; Definition of Done.
L: Hunt & Thomas (2019); Martin (2008); Humble & Farley (2010); Forsgren m.fl. (2018); Nygard (2018); OWASP (2025).

**2 HTML och semantik.** P: Webbstandarder – struktur, presentation och beteende åtskilda (Zeldman & Marcotte 2009);
POUR, särskilt Robust (WCAG 2.2, princip 4); semantisk HTML = tillgänglighetsträdet, grunden för både hjälpmedel och
AI-agenter. M: W3C-validering; inspektion av tillgänglighetsträdet; WCAG-EM. L: Zeldman & Marcotte (2009); W3C (2023);
Pickering (2016).

**3 CSS och design.** P: Gestaltlagar – närhet, likhet, slutenhet (Wertheimer 1923); CRAP – contrast, repetition,
alignment, proximity (Williams 2015); Fitts lag (1954) → tryckytor; Hicks lag (1952) → få val i navigationen; chunking
(Miller 1956); estetik–användbarhet-effekten (Kurosu & Kashimura 1995); atomic design/tokens (Frost 2016); intrinsisk
layout (Bell & Pickering 2019). M: Designsystem; kontrastmätning (WCAG 1.4.3, 1.4.11); visuell regression per PR.
L: Lidwell, Holden & Butler (2010); Yablonski (2024); Tidwell m.fl. (2020); Williams (2015).

**4 Prestanda.** P: Svarstidsgränser 0,1 s / 1 s / 10 s (Nielsen 1993, efter Miller 1968) och Doherty-tröskeln ~400 ms
(Doherty & Thadani 1982) → INP ≤ 200 ms; prestandabudget (Kadlec 2013); Souders regler – färre anrop, komprimera,
cacha, CDN, skript sist (Souders 2007); critical rendering path (Grigorik 2013); RAIL → Web Vitals (Walton 2020).
M: Lab (Lighthouse/PSI) och fält (CrUX/RUM); budget som CI-gate; bildpipeline. L: Souders (2007); Grigorik (2013);
Kadlec (2013); Nielsen (1993); Walton (2020).

**5 Tillgänglighet.** P: POUR (WCAG 2.2); Inclusive Design Principles – likvärdig upplevelse, ge kontroll, prioritera
innehåll (Swan m.fl. 2017); universell utformning – det som byggs för få hjälper alla. M: WCAG-EM 1.0 – avgränsa,
utforska, välj urval, granska, rapportera (W3C 2014); automatik hittar bara en del, manuell tangentbords- och
skärmläsarkoll är obligatorisk; DIGG:s webbriktlinjer som svensk tolkning. L: W3C (2023); W3C (2014); ETSI EN 301 549
(2021); Pickering (2016); Kalbag (2017); Swan m.fl. (2017); Lag (2023:254).

**6 Formulär.** P: Formulärets tre lager – relation, konversation, utseende (Jarrett & Gaffney 2009); fråga bara det
som behövs – uppgiftsminimering (GDPR art. 5.1 c; Wroblewski 2008); felförebyggande och felåterhämtning (Nielsens
heuristik 5 och 9; Norman 2013 om slips/mistakes och återkoppling); Postels lag – generös tolkning av t.ex.
telefonformat; försvar i djupled (Saltzer & Schroeder 1975); korrekt undantagshantering (OWASP A10:2025). M: Kognitiv
genomgång av uppgiften "skicka förfrågan" (Wharton m.fl. 1994); forskningsbaserade mönster från GOV.UK Design System;
Baymards formulärforskning; serversidevalidering i lager; A/B-test av antal fält och CTA. L: Jarrett & Gaffney (2009);
Wroblewski (2008); Silver (2018); Norman (2013); GOV.UK; Baymard.

**7 SEO och lokal synlighet.** P: Findability – organisation, etiketter, navigation, sök (Rosenfeld m.fl. 2015);
information scent – länktexter och titlar som luktar rätt (Pirolli & Card 1999); folk skannar, F-mönster (Nielsen
2006; Redish 2012); content first (Halvorson & Rach 2012); entitetskonsistens (NAP); E-E-A-T (Google). M:
Sökintentsanalys per tjänstesida; card sorting/tree testing (Spencer 2009); crawl-audit; GSC-fältdata; Rich Results
Test; Googles riktlinjer för generativ AI-sök (2026). L: Rosenfeld, Morville & Arango (2015); Pirolli & Card (1999);
Redish (2012); Google Search Central.

**8 Säkerhet och integritet.** P: Saltzer & Schroeders designprinciper – least privilege, fail-safe defaults, economy
of mechanism, open design (1975); defense in depth; secure by default; privacy by design (Cavoukian 2009; GDPR art.
25); uppgiftsminimering (art. 5); OWASP Top 10:2025 – A01 åtkomstkontroll, A02 felkonfiguration, A03 leveranskedja,
A05 injektion, A10 undantagshantering. M: Hotmodellering light – STRIDE (Shostack 2014); OWASP ASVS som kravnivå;
beroendeskanning; header-skanning; registerförteckning (GDPR art. 30); IMY:s vägledning; cookie-regeln i LEK
(2022:482) 9 kap. 28 §. L: Saltzer & Schroeder (1975); Shostack (2014); OWASP (2025); Cavoukian (2009); GDPR
(2016/679).

**9 Innehåll och konvertering.** P: Självklara sidor, skanning, satisficing (Krug 2014); webbtrovärdighet –
presumerad, ryktesbaserad, ytlig, förtjänad (Fogg m.fl. 2003) → riktiga bilder, org.nr, omdömen; tillit driver
köpavsikt (Gefen, Karahanna & Straub 2003); beteende = motivation × förmåga × trigger (Fogg 2009) → CTA är triggern,
få fält är förmågan; socialt bevis och auktoritet (Cialdini 2021); signifiers och återkoppling (Norman 2013);
klarspråk (Språkrådet). M: 5-sekunderstest av startsidan; innehållsinventering; JTBD-intervjuer; läsbarhet
(LIX/klarspråkstest); A/B-test när trafiken räcker, annars kvalitativt. L: Krug (2014); Fogg m.fl. (2003); Gefen m.fl.
(2003); Fogg (2009); Cialdini (2021); Norman (2013); Redish (2012).

**10 Analys, drift och gate.** P: Build–measure–learn (Ries 2011); kvalitetsmodellen ISO/IEC 25010:2023 som ryggrad
för DoD – funktionell lämplighet, prestandaeffektivitet, kompatibilitet, interaktionsförmåga (f.d. användbarhet, nu
inkl. inkludering), tillförlitlighet, säkerhet, underhållbarhet, flexibilitet, safety; användbarhet = ändamålsenlighet,
effektivitet och tillfredsställelse i ett sammanhang (ISO 9241-11:2018). M: RUM/CrUX + GSC; uptime-övervakning;
incidentlogg; SUS när uppgift och urval motiverar det; användartest med motiverat urval per målgrupp; månatlig
underhållscykel. L: ISO/IEC 25010 (2023); ISO 9241-11 (2018); Ries (2011); Forsgren m.fl. (2018); Sauro & Lewis
(2016); Krug (2010); Rubin & Chisnell (2008).

**11 Ramverk och hosting.** P: Statisk förrendering och minimal klient-JS är tillämpning av 1, 4 och 8, inte egna
principer. M/L: Leverantörsdokumentation (för oss Astro och Cloudflare) – primärkälla men inte granskad litteratur.

## B.2 Nielsens tio heuristiker (Nielsen & Molich 1990; Nielsen 1994)

1 Synlig systemstatus · 2 Överensstämmelse med verkligheten · 3 Användarkontroll och frihet · 4 Konsekvens och
standarder · 5 Felförebyggande · 6 Igenkänning framför ihågkommande · 7 Flexibilitet och effektivitet · 8 Estetisk och
minimalistisk design · 9 Hjälp att känna igen, förstå och återhämta sig från fel · 10 Hjälp och dokumentation.

Historiska studier av mänskliga granskare visar nyttan av flera oberoende bedömningar
([NN/g](https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/theory-heuristic-evaluations/)).
Deras upptäcktsandelar är inte täckningslöften för vår sajt eller för flera modellinstanser.
En studie av multimodala språkmodeller som granskare fann att de hittade fler problem än fem erfarna människor men
missade fel som sträcker sig över flera skärmar ([arXiv 2507.02306](https://arxiv.org/abs/2507.02306)).

Forskningsplanen ska därför ange uppgift, målgrupp, urval, obesvarad fråga och vilket beslut resultatet kan ändra.
Fem deltagare är en tumregel för vissa kvalitativa rundor, inte för alla metoder eller för statistiska slutsatser
([NN/g](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/)). Kundintervju, expertgranskning,
modellprov och observation av verkliga användare redovisas var för sig
([GOV.UK](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service)).

## B.3 Kognitiv genomgång (Wharton m.fl. 1994) – fyra frågor per steg

1 Försöker användaren uppnå rätt effekt? 2 Ser användaren att rätt handling finns? 3 Kopplar användaren handlingen
till effekten? 4 Får användaren begriplig återkoppling på att det gick framåt?

## B.4 WCAG-EM 1.0 (W3C 2014) – fem steg

1 Avgränsa · 2 Utforska sajten · 3 Välj representativt urval (start, formulär eller kontakt, tjänstesida, 404) ·
4 Granska urvalet mot WCAG 2.2 AA · 5 Rapportera. Automatiska verktyg hittar bara en del – manuell koll krävs.

## B.5 Allvarlighet – Nielsens skala 0–4

Bedöms efter frekvens (hur många drabbas), konsekvens (hur illa) och persistens (går det att lära sig förbi).
4 kritisk: blockerar lansering eller konvertering · 3 hög: tydlig förlust av kunder eller förtroende · 2 medel: avsteg
från praxis utan direkt affärsförlust · 1 låg: kosmetiskt · 0 inget problem.

Regelverk: Lag (2023:254) om vissa produkters och tjänsters tillgänglighet (mikroföretag undantagna; lagkrav i
praktiken WCAG 2.1 AA via EN 301 549 v3.2.1, byggmål 2.2 AA); GDPR; DIGG:s webbriktlinjer.

## C. Referenser (Harvard)

Bell, A. & Pickering, H. (2019). Every Layout. every-layout.dev.
Berners-Lee, T. & Mendelsohn, N. (2006). The Rule of Least Power. W3C TAG Finding.
Brooke, J. (1996). SUS: A 'quick and dirty' usability scale. I: Jordan, P.W. m.fl. (red.) Usability Evaluation in Industry. Taylor & Francis.
Cavoukian, A. (2009). Privacy by Design: The 7 Foundational Principles. IPC Ontario.
Checkland, P. (1999). Systems Thinking, Systems Practice (30-year retrospective). Wiley.
Christensen, C.M., Hall, T., Dillon, K. & Duncan, D.S. (2016). Know your customers' "jobs to be done". Harvard Business Review, 94(9).
Cialdini, R.B. (2021). Influence, New and Expanded. Harper Business.
Design Council (2019). The Double Diamond: Framework for Innovation. Design Council.
Doherty, W.J. & Thadani, A.J. (1982). The economic value of rapid response time. IBM.
Fitts, P.M. (1954). The information capacity of the human motor system in controlling the amplitude of movement. Journal of Experimental Psychology, 47(6).
Fogg, B.J. (2009). A behavior model for persuasive design. Persuasive '09. ACM.
Fogg, B.J. m.fl. (2003). How do users evaluate the credibility of Web sites? DUX '03. ACM.
Forsgren, N., Humble, J. & Kim, G. (2018). Accelerate. IT Revolution.
Fowler, M. (2006). Continuous Integration. martinfowler.com.
Frost, B. (2016). Atomic Design. Brad Frost.
Gefen, D., Karahanna, E. & Straub, D.W. (2003). Trust and TAM in online shopping. MIS Quarterly, 27(1).
Gothelf, J. & Seiden, J. (2021). Lean UX. 3 uppl. O'Reilly.
Grigorik, I. (2013). High Performance Browser Networking. O'Reilly.
Gustafson, A. (2015). Adaptive Web Design. 2 uppl. New Riders.
Halvorson, K. & Rach, M. (2012). Content Strategy for the Web. 2 uppl. New Riders.
Hevner, A.R., March, S.T., Park, J. & Ram, S. (2004). Design science in information systems research. MIS Quarterly, 28(1).
Hick, W.E. (1952). On the rate of gain of information. Quarterly Journal of Experimental Psychology, 4(1).
Humble, J. & Farley, D. (2010). Continuous Delivery. Addison-Wesley.
Hunt, A. & Thomas, D. (2019). The Pragmatic Programmer. 20th Anniversary ed. Addison-Wesley.
ISO (2018). ISO 9241-11:2018 Usability: Definitions and concepts.
ISO (2019). ISO 9241-210:2019 Human-centred design for interactive systems.
ISO/IEC (2023). ISO/IEC 25010:2023 Product quality model.
Jarrett, C. & Gaffney, G. (2009). Forms that Work. Morgan Kaufmann.
Kadlec, T. (2013). Setting a performance budget. timkadlec.com.
Kalbag, L. (2017). Accessibility for Everyone. A Book Apart.
Keith, J. (2016). Resilient Web Design. resilientwebdesign.com.
Krug, S. (2010). Rocket Surgery Made Easy. New Riders.
Krug, S. (2014). Don't Make Me Think, Revisited. 3 uppl. New Riders.
Kurosu, M. & Kashimura, K. (1995). Apparent usability vs. inherent usability. CHI '95. ACM.
Lidwell, W., Holden, K. & Butler, J. (2010). Universal Principles of Design. Rev. uppl. Rockport.
Marcotte, E. (2010). Responsive Web Design. A List Apart, 306.
Martin, R.C. (2008). Clean Code. Prentice Hall.
Mavin, A., Wilkinson, P., Harwood, A. & Novak, M. (2009). Easy Approach to Requirements Syntax (EARS). RE '09. IEEE.
Miller, G.A. (1956). The magical number seven, plus or minus two. Psychological Review, 63(2).
Miller, R.B. (1968). Response time in man-computer conversational transactions. AFIPS FJCC.
Nielsen, J. (1993). Usability Engineering. Academic Press.
Nielsen, J. (1994). 10 Usability Heuristics for User Interface Design. Nielsen Norman Group.
Nielsen, J. (2006). F-Shaped Pattern for Reading Web Content. Nielsen Norman Group.
Nielsen, J. & Landauer, T.K. (1993). A mathematical model of the finding of usability problems. INTERCHI '93. ACM.
Nielsen, J. & Molich, R. (1990). Heuristic evaluation of user interfaces. CHI '90. ACM.
Norman, D.A. (2013). The Design of Everyday Things. Rev. uppl. Basic Books.
Nygard, M.T. (2018). Release It! 2 uppl. Pragmatic Bookshelf.
OWASP (2025). OWASP Top 10:2025; OWASP Application Security Verification Standard 5.0.
Peffers, K., Tuunanen, T., Rothenberger, M.A. & Chatterjee, S. (2007). A design science research methodology for information systems research. Journal of MIS, 24(3).
Pickering, H. (2016). Inclusive Design Patterns. Smashing Magazine.
Pirolli, P. & Card, S. (1999). Information foraging. Psychological Review, 106(4).
Redish, J. (2012). Letting Go of the Words. 2 uppl. Morgan Kaufmann.
Ries, E. (2011). The Lean Startup. Crown Business.
Rosenfeld, L., Morville, P. & Arango, J. (2015). Information Architecture: For the Web and Beyond. 4 uppl. O'Reilly.
Rubin, J. & Chisnell, D. (2008). Handbook of Usability Testing. 2 uppl. Wiley.
Saltzer, J.H. & Schroeder, M.D. (1975). The protection of information in computer systems. Proceedings of the IEEE, 63(9).
Sauro, J. & Lewis, J.R. (2016). Quantifying the User Experience. 2 uppl. Morgan Kaufmann.
Schwaber, K. & Sutherland, J. (2020). The Scrum Guide.
Sharp, H., Preece, J. & Rogers, Y. (2023). Interaction Design: Beyond Human–Computer Interaction. 6 uppl. Wiley.
Shostack, A. (2014). Threat Modeling: Designing for Security. Wiley.
Silver, A. (2018). Form Design Patterns. Smashing Magazine.
Souders, S. (2007). High Performance Web Sites. O'Reilly.
Spencer, D. (2009). Card Sorting. Rosenfeld Media.
Stickdorn, M., Hormess, M., Lawrence, A. & Schneider, J. (2018). This Is Service Design Doing. O'Reilly.
Swan, H., Pouncey, I., Pickering, H. & Watson, L. (2017). Inclusive Design Principles. inclusivedesignprinciples.org.
Tidwell, J., Brewer, C. & Valencia, A. (2020). Designing Interfaces. 3 uppl. O'Reilly.
W3C (2014). Website Accessibility Conformance Evaluation Methodology (WCAG-EM) 1.0.
W3C (2023). Web Content Accessibility Guidelines (WCAG) 2.2.
Walton, P. (2020). Web Vitals. web.dev.
Wertheimer, M. (1923). Untersuchungen zur Lehre von der Gestalt II. Psychologische Forschung, 4.
Wharton, C., Rieman, J., Lewis, C. & Polson, P. (1994). The cognitive walkthrough method. I: Nielsen, J. & Mack, R.L. (red.) Usability Inspection Methods. Wiley.
Wiggins, A. (2011). The Twelve-Factor App. 12factor.net.
Williams, R. (2015). The Non-Designer's Design Book. 4 uppl. Peachpit.
Wroblewski, L. (2008). Web Form Design. Rosenfeld Media.
Wroblewski, L. (2011). Mobile First. A Book Apart.
Yablonski, J. (2024). Laws of UX. 2 uppl. O'Reilly.
Zeldman, J. & Marcotte, E. (2009). Designing with Web Standards. 3 uppl. New Riders.

Tillagda 2026-10-04 ur Codex genomgångar (designöverföringen och helhetsbedömningen), som analysfrågor i extraktionen
och prövningen, inte som fler allmänna regler (Every Layout står redan ovan, Bell & Pickering 2019: pröva mellanbredder):
Albers, J. (1963/2013). Interaction of Color. Yale University Press. (färg i sitt sammanhang: roll och balans följer värdet)
Lupton, E. (2010). Thinking with Type. 2 uppl. Princeton Architectural Press. (hierarki, mellanrum, textens form och radbrytning)
Müller-Brockmann, J. (1981). Grid Systems in Graphic Design. Niggli. (linjering och proportioner som håller ihop sidan)
Nielsen Norman Group (2024). Synthetic Users: If, When, and How to Use AI-Generated "Research". nngroup.com. (syntetiska användare ger hypoteser, inte observationer)
Anthropic (2025). Erfarenheter av designloopar med modellgranskning (Codex 2026-10-04): mellanversioner var ibland bättre än slutversionen, och ordval i bedömningskriterier kan få genererade designer att konvergera.

Regelverk och riktlinjer: Lag (2023:254) om vissa produkters och tjänsters tillgänglighet; förordning (EU) 2016/679
(GDPR); lag (2022:482) om elektronisk kommunikation; ETSI EN 301 549 V3.2.1 (2021); DIGG, Webbriktlinjer; GOV.UK
Design System; Baymard Institute; Google Search Central.
