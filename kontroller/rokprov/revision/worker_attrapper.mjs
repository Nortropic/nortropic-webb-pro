// Märkta attrapper för kundsajtens Worker i Node: D1 som riktig SQLite (node:sqlite) med mallens migreringar, R2 som en
// karta, och en händelselogg med felinjektion. Det riktiga runtimeprovet i workerd är kontroller/workersprov.py; här prövas
// felvägarna som workerd inte kan framkalla (lagret svarar inte, kvittot stämmer inte, fristen går ut).
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

// krok(vad, detalj, argument) körs före varje operation och kan kasta, vänta eller ge ett eget svar ({ svar }).
export function d1(migreringar, krok = async () => null) {
  const db = new DatabaseSync(':memory:');
  for (const f of readdirSync(migreringar).filter((x) => x.endsWith('.sql')).sort()) db.exec(readFileSync(join(migreringar, f), 'utf8'));
  const kor = (sql, args) => { const r = db.prepare(sql).run(...args); return { success: true, meta: { changes: Number(r.changes) } }; };
  const sats = (sql) => {
    const s = { sql, args: [], bind(...a) { s.args = a; return s; },
      async first() { await krok('d1.first', sql); return db.prepare(sql).get(...s.args) ?? null; },
      async all() { await krok('d1.all', sql); return { success: true, results: db.prepare(sql).all(...s.args) }; },
      async run() { await krok('d1.run', sql, s.args); return kor(sql, s.args); } };
    return s;
  };
  return {
    db,
    prepare: sats,
    async batch(lista) {
      await krok('d1.batch', lista.map((x) => x.sql));
      db.exec('BEGIN');
      let ut;
      try { ut = lista.map((x) => kor(x.sql, x.args)); db.exec('COMMIT'); } catch (e) { db.exec('ROLLBACK'); throw e; }
      await krok('d1.batch.efter', null);  // ett fel här kommer efter att satsen sparats (ett tvetydigt fel)
      return ut;
    },
  };
}

export function r2(krok = async () => null) {
  const objekt = new Map();
  return {
    objekt,
    async put(nyckel, kropp, val = {}) {
      const ers = await krok('r2.put', nyckel);
      objekt.set(nyckel, { typ: val.httpMetadata?.contentType, meta: val.customMetadata, storlek: kropp.byteLength ?? String(kropp).length });
      return ers && 'svar' in ers ? ers.svar : { key: nyckel };
    },
    async delete(nyckel) { await krok('r2.delete', nyckel); objekt.delete(nyckel); },
  };
}

// Förrenderade sidor som Static Assets skulle servera dem.
export function assets(sidor) {
  return { fetch: async (req) => {
    const vag = new URL(req.url).pathname;
    return sidor[vag] ? new Response(sidor[vag], { headers: { 'content-type': 'text/html; charset=utf-8' } }) : new Response('saknas', { status: 404 });
  } };
}
