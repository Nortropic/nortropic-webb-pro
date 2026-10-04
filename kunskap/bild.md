# Bild — funktion, äkthet, rättigheter, beskärning, storlekar och optimering

Professionsfil, läses i steg 5 i `.claude/skills/bygg-sajt/SKILL.md`. Ägarens regler gäller före allt annat här
(LARDOMAR.md): verksamhetens egna bilder, eller inga foton ("hellre inga foton än stock"); en saknad bild är en
beställning, inte ett designval ("gör 'inga egna foton' till en beställning"); ett foto av kundens arbete är just
kundens arbete. Samma regel står i skillens steg 1 punkt 2 ("Inga stockbilder") och i granskarens kriterium 2.

## Vad en bild får vara

| Anspråk | Betyder | Får komma från |
|---|---|---|
| `depicts_client_work` | visar verksamhetens faktiska arbete | bara verksamhetens egna foton, med rätt att publicera |
| `depicts_client_people` | visar verksamhetens personer | bara verksamhetens egna foton, med samtycke |
| `illustrative` / `none` | miljö, stämning eller form utan påstående | verksamhetens egna foton, eller form i koden (SVG ur märket, en karta, typografi) |

Stockbilder och genererade bilder används inte på sajten, inte heller som stämning: ägarens dom gäller alla
bildplatser. När egna bilder saknas bär typografin, färgen och formen, och bilderna beställs i `BESTALLNING.md`
med plats och syfte ("ta en sådan här, fast er egen"). En form som byggs i koden (en linje ur märket, en karta
över orterna) är ingen bild i den här meningen och får användas när den har en funktion.

## Varje viktig bildplats har ett syfte och prövat material

Inventeringen står i briefen (§8); de beslutade bildplatserna står i DESIGN.md under Bildbehandling: bildplats (`hero-*`, `env-*`, `proof-*`, `people-*`, `detail-*`), sida,
syfte (vad besökaren ska se eller förstå där), fil ur `underlag/<slug>/bilder/` (BILDER.md), anspråk, och hur
bilden prövats i kompositionen (ateljéns rendering eller byggets skärmbilder). En plats utan verkligt material står
tom i designen, typografin bär, och platsen står i beställningen; den fylls aldrig med en ersättare. Granskaren
bedömer två saker var för sig: om bristen är rätt identifierad och beställd, och om sajten som den visas nu ändå
håller nivån (`kritik/GRANSKARE.md`, Saknat underlag).

## Val och rättigheter

Kundens eget material: rättighetsläget per bild (vem tog den, vem äger den, får den publiceras, finns samtycke för
personerna). Bilder med okänt ursprung används inte. Licenser för typsnitt och ikoner står i registret nedan.

## Art direction

Bildspår ur briefen: foto-först (kunden har bärande foton), bevis-först (arbetet talar: före/efter, resultat,
detaljer), typografi-först (bilderna är stöd, typografin bär). Ett spår är ett val med skäl, inte en tröskeltabell.
Huvudreferensens bildbehandling (REFERENSER.md, `Huvudreferens:`) är utgångspunkten och anpassas till kundens
material: en komposition som förutsätter arkitekturfoto av hög klass byts mot en som bär kundens faktiska bilder
(Codex 2026-10-04). Behandling (beskärning, ton, kontrast) ger sammanhållning när bilderna har olika ursprung; ett
material som redan håller ihop behandlas inte.

## Beskärning, storlekar och optimering

Filnamn `<plats>__<beskrivning>.<ext>`. Beskärningar per plats (första vyn 16:9 och 4:5 för mobil, 3:2 för miljö,
kvadrat för porträtt) med fokuspunkten på det bilden ska visa, och responsiva storlekar med `sizes`; `astro:assets`
gör AVIF/WebP. Förslag till viktbudget: första vyns bild ≤ 150 kB, porträtt ≤ 100 kB, övriga ≤ 120 kB. Explicita
mått på varje bild (ingen layoutförskjutning), `loading="lazy"` utom första vyns bild, alt-text på svenska som
beskriver innehållet (tom alt bara för dekor).

- **Metadata stannar i underlaget.** Tagningsdatum och kamera läses där (`kontroller/bilddatum.py`) och kan bära
  en daterad sektion; GPS-läget är en personuppgift och följer aldrig med till sajten. `astro:assets` tar bort
  metadata; en fil som läggs direkt i `public/` gör det inte, och standarden (4.2) fäller den.

## Verktygen här

`astro:assets` gör format och storlekar, `kontroller/ikoner.mjs` apple-touch-ikonen och delningsbilden,
`kontroller/bilddatum.py` datumen. Digitalas bildverktyg (normalisering och märkesfiler för Next.js) finns inte
här och används inte.

## Typsnitt och ikonuppsättningar (2026-09-30, b35d4f-digitala)

Kundbygget innehåller `bilder/TYPSNITT-IKONER.json`, bredvid `bilder/LICENSER.md`.
Registret är kundspecifikt; inga kunduppgifter läggs i professionsrepot. Schema:

```json
{"schema":1,"poster":[{"typ":"typsnitt","filer":["fonts/exempel.woff2"],"licens":"OFL-1.1","kalla":"https://example.invalid/original","version":"1.0","datum":"2026-09-30","licensfil":"bilder/OFL.txt","andrad":false,"subset":false,"reserverade_namn":[],"anvandt_namn":"Exempel"}]}
```

Varje byggd woff2/woff/ttf/otf-fil ska finnas i registret. Ikonuppsättningar får
`typ: "ikoner"`, `namn`, samma käll-/licensfält, berörda `filer` och eventuell
`attribution`. Deklarera uppsättningens namn i HTML med `data-ikonuppsattning`;
inline-SVG binds genom HTML-filens sökväg. SVG utan post rapporteras för klassning.
Prelaunch grind 6 kontrollerar täckning och form. Registeruppgifternas sanningshalt
och rätt att använda materialet prövas genom källan; verktyget avgör inte juridik.

[OFL 1.1, villkor 2–3](https://openfontlicense.org/open-font-license-official-text/)
kräver att licens och copyrightinformation följer typsnittet. En ändrad eller
subsettad fil får inte behålla ett reserverat typsnittsnamn utan rättighetshavarens
uttryckliga tillstånd. Registret flaggar det för prövning; det döper inte om filer.
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) kräver bland annat
attribution och licenshänvisning. Båda primärkällorna omlästa 2026-09-30.
