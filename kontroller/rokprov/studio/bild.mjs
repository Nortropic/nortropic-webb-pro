// Studioprovets syntetiska bilder (kunskap/designstudio.md, Provkandidaten): en enkel gradient med två former i JPEG,
// skapad med sharp ur sajtens beroenden, så att inga binära bilder ligger i repot. Inga verkliga motiv.
//
//     node kontroller/rokprov/studio/bild.mjs <node_modules> <ut.jpg> <bredd> <höjd> <r> <g> <b>
const [,, nm, ut, b, h, r1, g1, b1] = process.argv;
const sharp = (await import(nm + '/sharp/dist/index.mjs')).default;
const W = +b, H = +h;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">`
  + `<stop offset="0" stop-color="rgb(${r1},${g1},${b1})"/><stop offset="1" stop-color="#2b2118"/></linearGradient></defs>`
  + `<rect width="100%" height="100%" fill="url(#g)"/><circle cx="${W * 0.7}" cy="${H * 0.45}" r="${H * 0.22}" fill="#e8d9c4"/>`
  + `<rect x="${W * 0.08}" y="${H * 0.62}" width="${W * 0.35}" height="${H * 0.2}" fill="#8a6a4a"/></svg>`;
await sharp(Buffer.from(svg)).jpeg({ quality: 82 }).toFile(ut);
console.log('ok', ut);
