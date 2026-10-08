#!/usr/bin/env node
// natproxy.mjs — nätgränsen som egen process, för en webbläsare som inte startas av Playwright: Chrome DevTools MCP:s
// Chrome (kontroller/devtools.py) startas med --proxy-server mot den här proxyn, så att sidorna och deras underresurser
// håller sig inom samma domänlista som webbtjänsten (NWP_NAT_TILLATNA, verkställd i gemensamt.natgrans: värdnamnet slås
// upp här, bara publika adresser ansluts, skrivande http bara lokalt, allt nekat loggas).
//   NWP_NAT_TILLATNA=värd,värd node natproxy.mjs --tillat 'https://värd;https://www.värd' --logg FIL
// Skriver {"server": "http://127.0.0.1:PORT"} på första raden och lever tills stdin stängs; då skrivs loggen över det
// som nekades (--logg) och processen avslutas. Utan NWP_NAT_TILLATNA startar den inte: ingen proxy utan domänlista.
import { writeFileSync } from 'node:fs';
import { args, natgrans } from './gemensamt.mjs';

const a = args(process.argv.slice(2));
const ursprung = a.tillat && a.tillat !== true ? String(a.tillat).split(';').map((x) => x.trim()).filter(Boolean) : [];
const g = await natgrans(ursprung);
if (!g) { console.error('natproxy: NWP_NAT_TILLATNA saknas; nätgränsen kräver en domänlista'); process.exit(2); }
process.stdout.write(JSON.stringify({ server: g.server, tillatna: ursprung, policy: String(process.env.NWP_NAT_TILLATNA) }) + '\n');
let stangd = false;
const slut = async () => {
  if (stangd) return; stangd = true;
  await g.stang();
  if (a.logg && a.logg !== true) writeFileSync(String(a.logg), JSON.stringify({ server: g.server, blockerade: g.blockerade }, null, 1) + '\n');
  process.exit(0);
};
process.stdin.resume();
process.stdin.on('end', slut);
process.stdin.on('close', slut);
process.on('SIGTERM', slut);
process.on('SIGINT', slut);
