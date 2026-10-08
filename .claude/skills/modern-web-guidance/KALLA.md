# Källa

- **Skill:** `modern-web-guidance` (mappen `modern-web-guidance`). Chrome- och Edge-teamens guider för modern HTML,
  CSS, formulär, tillgänglighet, prestanda och säkerhet, var och en med webbläsarstöd (Baseline) och reserv per
  funktion.
- **Källa:** https://github.com/GoogleChrome/modern-web-guidance, `skills/modern-web-guidance/`, commit
  `a97286845f2baba38988f9e5fe2b2a1351021e50` (2026-10-07T16:21:45Z, Release v0.0.193).
- **Licens:** Apache-2.0 (`LICENSE` ur repots rot, kopierad till mappen). Guiderna är Googles; attribution: "Modern Web
  Guidance, Google LLC, Apache License 2.0".
- **Intagen:** 2026-10-08 (nattens uppdrag, backloggen B-20261003-ta-in-googlechrome-modern-web-guidance-i-verktyg;
  kirurgens dom 2026-10-03: ta in, `kunskap/REGISTER.md`). Förslaget pekade på `84ae725` (v0.0.191); intaget tar den
  senaste versionen, eftersom verktygslådan hålls i den senaste (CLAUDE.md, Arbetssätt). De två kända felen i
  förslaget står kvar på samma rader i den här versionen.
- **Ordagrant:** hela guidemappen följer med (intagskrav 1, postens not 2026-10-05): av källans 178 guider står 149
  byte för byte som i källan, 28 skiljer sig bara i hänvisningarna (Lokala ändringar) och en är utelämnad (Utelämnat).
- **Lokala ändringar:**
  - `SKILL.md` är vår, på svenska: källans beskrivning gör skillen obligatorisk för allt HTML-, CSS- och JS-arbete och
    hämtar guiderna med npx, som laddar opinnad kod; här läses de ur mappen.
  - Hänvisningarna mellan guiderna, `(via npx -y modern-web-guidance@latest retrieve "<id>")`, är mekaniskt ersatta med
    guidens sökväg, till exempel `guides/visual-design/typography.md`: 82 hänvisningar i 28 filer, ingen annan text
    ändrad. `fit-text-to-container` finns inte i källan, och hänvisningen säger det.
  - `GUIDER.md` är vårt index, en rad per guide med sökväg och guidens rubrik, genererat ur filerna.
- **Utelämnat:** `guides/security/restrict-outbound-connections.md` (huvudet Connection-Allowlist, som Firefox och
  Safari saknar; standarden 8.2 styr CSP): förgranskningen markerar två gånger ett ord för dataläckage i guidens text om
  huvudet, en falsk träff, och utan filen ger förgranskningen LÅG. Repots `skills/chrome-extensions/`, `policies/`, `.claude-plugin/`,
  `.github/`, `.grok-plugin/`, `package.json`, `gemini-extension.json` och `kimi.plugin.json` (pluginmanifest och
  paketets eget verktyg), README.md och CONTRIBUTING.md.
- **Förgranskning 2026-10-08:** `kontroller/granska_repo.py` gav LÅG för mappen: inga dolda tecken, ingen text riktad
  till agenter, inga behörigheter, hookar eller skript. Med den utelämnade filen var utfallet MEDEL, bara för ordet för
  dataläckage i guidens beskrivning av ett säkerhetshuvud.
- **Krockar med våra beslut:** källans "MANDATORY: Execute FIRST" och npx-hämtningen (ersatta av vår SKILL.md);
  guidernas preconnect, CDN, polyfills och inline-händelser (byggstandarden 4.4 och 8.2); mörkt läge som förval
  (bara när KONCEPT.md säger det); karuseller (standarden 5.5); genererade Baseline-rader som inte stämmer med MDN.
- **Så används skillen här:** i helbygget, bygg-sajt steg 5.3 och 5.5, när en komponent skrivs utanför mallen. Den har
  ingen roll i skapandeflödet än (`kunskap/metodkarta.md`, Ingen uppgift i flödet); innan den ersätter vårt sätt eller
  blir standard prövas den i ett avgränsat försök (intagskrav 4).
