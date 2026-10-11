# xterm.js i dashboarden (ändringsflikens terminal)

Ändringsflikens terminal (ägarens tillägg 2026-10-11; `kunskap/andringar.md`) visar och tar emot tangenterna för den
Claude Code-process som dashboarden äger (`dashboard/terminal.py`). Komponenten är bara visningen och inmatningen, aldrig
agentprocessen. Filerna är de byggda UMD-filerna ur npm-paketen; källkartor och TypeScript-typer tas inte
med. Dashboarden serverar dem som egna statiska filer (`server.py`, listan över statiska filer, och `desktop.ui_version`).
`xterm.js` har en ändring mot paketet (nedan); de andra filerna är oförändrade.

| Fil | Paket och version | Publicerad | Tarball sha512 (npm `dist.integrity`) | Fil sha256 |
|---|---|---|---|---|
| `xterm.js` (lib/xterm.js) | `@xterm/xterm` 6.0.0 | 2025-12-22T13:50:12Z | `TQwDdQGtwwDt+2cgKDLn0IRaSxYu1tSUjgKarSDkUM0ZNiSRXFpjxEsvc/Zgc5kq5omJ+V0a8/kIM2WD3sMOYg==` | paketets `14903579ff54664cd72f8e8699e6961a6272c21863ec1c3b118cdc8af5d4a972`; med ändringen nedan `d138478eb2f74e0dab8caabe5a5f352b24ef3858fd3d410daac13116f18a0d61` |
| `xterm.css` (css/xterm.css) | `@xterm/xterm` 6.0.0 | samma | samma | `854a7c0fb70e8b1a083c16797ab827299fb18744f5ad34f227b48337e33293c6` |
| `addon-fit.js` (lib/addon-fit.js) | `@xterm/addon-fit` 0.11.0 | 2025-12-22T13:50:25Z | `jYcgT6xtVYhnhgxh3QgYDnnNMYTcf8ElbxxFzX0IZo+vabQqSPAjC3c1wJrKB5E19VwQei89QCiZZP86DCPF7g==` | `ba3ea256ce0620a0992a197d6c9baea64823fc93d8da07a9e366ca9943c18527` |

Källa: https://github.com/xtermjs/xterm.js (npm-registrets tarballer, hämtade 2026-10-11 med integriteten prövad mot
registrets `dist.integrity`). Licens: MIT för båda (`LICENSE-xterm`, `LICENSE-addon-fit`, oförändrade ur paketen).

Granskning 2026-10-11 (enligt `kunskap/beroenden.md`, Ett nytt beroende): inga beroenden och inga
installationsskript i någon av paketfilerna; ingen `eval` eller `new Function` i `xterm.js`; inga adresser som filen
hämtar (bara XML-namnrymder och en dokumentationslänk); karenstiden (minst tre dygn) uppfylld med god marginal. Storlek:
`xterm.js` 489 kB, 121 kB gzip. Prövad i dashboardens webbprov för ändringsfliken (svenska tecken, inklistring, storlek,
avbrott, återanslutning) i Chromium med `Object.prototype` fryst som i appen, och i Nortropic.app:s WKWebView
(`desktop/prov/prov_repovaljaren_app.py`).

**Ändringen mot paketet (2026-10-11):** Nortropic.app fryser `Object.prototype` i webbvyn (`freezePrototype` i
`desktop/src-tauri/tauri.conf.json`, ett skydd mot prototypförorening som står kvar). Då kastar en vanlig tilldelning av
en egenskap som prototypen redan har (JavaScripts "override mistake"), och `xterm.js` gör en sådan: `e.toString=function…`
i tangentkodernas namnrymd (KeyCodeUtils, ur VS Codes keyCodes), vid kolumn 450269 i den enda raden. Utan ändringen
definieras aldrig `Terminal` i appen (TypeError: Attempted to assign to readonly property; fångat i appens prov). Den
tilldelningen är skriven som `Object.defineProperty(e,"toString",{value:…,writable:!0,configurable:!0,enumerable:!0})`,
med samma värde och samma egenskaper som tilldelningen ger; inget annat i filen är ändrat, och ingen annan sådan
tilldelning finns i `xterm.js` eller `addon-fit.js` (sökt efter tilldelning av `toString`, `valueOf`, `constructor`,
`toLocaleString`, `hasOwnProperty`, `isPrototypeOf`, `propertyIsEnumerable` och `__proto__`). Vid ett versionsbyte görs
samma sökning, och webbprovet med fryst prototyp visar om ändringen behövs igen.

Säkerhet (xterm.js säkerhetsguide, https://xtermjs.org/docs/guides/security/, läst 2026-10-11): terminalens in- och
utdata går bara mellan portalen och dashboarden på samma ursprung, med sessionens bindning prövad på servern;
utdatan skrivs som bytes till terminalen och tolkas aldrig som HTML; länkar i utdata öppnas inte av sig själva.

Byte av version: samma granskning, nya rader i tabellen och webbprovet för ändringsfliken grönt.
