// Isolated, in-memory PostgreSQL-compatible regression test: never connect to live DB.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PGlite } from '@electric-sql/pglite';

const here = path.dirname(fileURLToPath(import.meta.url));
const migration = await fs.readFile(path.resolve(here, '../prisma/migrations/20261010150100_positive_amount_check/migration.sql'), 'utf8');
const db = new PGlite();
const tables = ['payment_requests', 'payments', 'transactions'];
let assertions = 0;

try {
  for (const table of tables) {
    await db.exec(`CREATE TABLE "${table}" (id SERIAL PRIMARY KEY, amount DECIMAL(20,7) NOT NULL)`);
  }
  await db.exec(migration);
  for (const table of tables) {
    await db.query(`INSERT INTO "${table}" (amount) VALUES ($1)`, ['25.0000000']);
    assertions++;
    for (const amount of ['0', '-1.0000000']) {
      let checkFailed = false;
      try {
        await db.query(`INSERT INTO "${table}" (amount) VALUES ($1)`, [amount]);
      } catch (error) {
        checkFailed = error?.code === '23514';
      }
      if (!checkFailed) throw new Error(`Constraint failed for ${table}: rejected amount ${amount} was accepted`);
      assertions++;
    }
    const { rows } = await db.query('SELECT conname, pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conname = $1', [`${table}_amount_positive_check`]);
    if (rows.length !== 1 || !rows[0].definition.includes('amount >')) throw new Error(`Missing CHECK for ${table}`);
    assertions++;
  }
  console.log(JSON.stringify({status:'PASS',assertions,tables,engine:'local PostgreSQL via PGlite',fundsAffected:0},null,2));
} finally {
  await db.close();
}
