/**
 * Fail-closed outreach guard for the self-hosted Nova Mail service.
 * No paid service or tracking endpoint. Only email addresses, subject hashes,
 * timestamps and delivery state are stored locally; message bodies are not.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';

const QUIET_MS = 7 * 24 * 60 * 60 * 1000;
const MAX_WAIT_MS = 2500;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const blocked = reason => ({sent:false, blocked:true, reason, safeguard:'nova-mail-outreach'});
const canonical = v => String(v ?? '').trim().toLowerCase();
const PERMANENT_CONTACT_HOLD = new Set([
  'besteigenoffice@gmail.com',
  'contact@wordykid.com'
]);

// Explicit holds apply to To/Cc/Bcc, to scheduled and transactional mail too.
// A new substantive inbound request needs human review before lifting a hold.
export function activeContactHold(input = {}, env = process.env) {
  const extras = new Set(String(env.NOVA_MAIL_SUPPRESSED_RECIPIENTS || '')
    .split(/[;,]+/).map(canonical).filter(Boolean));
  return ['to', 'cc', 'bcc'].some(key => {
    const value = input[key];
    const items = Array.isArray(value) ? value : [value];
    return items.some(item => String(item ?? '').split(/[;,]/).some(part => {
      const address = canonical(part.match(/<([^<>]+)>/)?.[1] || part);
      return PERMANENT_CONTACT_HOLD.has(address) || extras.has(address);
    }));
  });
}
const digest = v => createHash('sha256').update(String(v ?? '')).digest('hex');

function singleRecipient(input) {
  const raw = String(input.to ?? '').trim();
  if (input.cc?.trim() || input.bcc?.trim() || /[,;]/.test(raw)) return null;
  const value = canonical(raw);
  return /^[a-z0-9.!#$%&'*+\-/=?^_`{|}~]+@[a-z0-9.-]+\.[a-z]{2,}$/i.test(value) ? value : null;
}

async function lock(file) {
  const started = Date.now();
  await fs.mkdir(path.dirname(file), {recursive:true});
  while (Date.now() - started < MAX_WAIT_MS) {
    try {
      const handle = await fs.open(file, 'wx', 0o600);
      return async () => { await handle.close(); await fs.unlink(file).catch(() => {}); };
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
      await sleep(50);
    }
  }
  throw new Error('ledger locked; retry only after reviewing status');
}

async function readJson(file, defaultValue) {
  try { return JSON.parse(await fs.readFile(file, 'utf8')); }
  catch (err) { if (err.code === 'ENOENT') return defaultValue; throw err; }
}

async function saveLedger(file, rows) {
  const temp = `${file}.${process.pid}.${Math.random().toString(36).slice(2)}.tmp`;
  await fs.writeFile(temp, JSON.stringify(rows, null, 2) + '\n', {mode:0o600});
  await fs.rename(temp, file);
}

async function suppressed(recipient, file, env) {
  const fromEnv = String(env.NOVA_MAIL_SUPPRESSED_RECIPIENTS || '').split(/[;,\n]/).map(canonical);
  if (fromEnv.includes(recipient)) return true;
  const rows = await readJson(file, []);
  if (!Array.isArray(rows)) throw new Error('Suppression file must be an array');
  return rows.some(value => canonical(typeof value === 'string' ? value : value?.email || value?.recipient) === recipient);
}

/**
 * An approved sales message is sent only if all checks pass.
 * A provider error is conservatively recorded as 'uncertain' and must not be
 * retried with a different provider until delivery is checked manually.
 * `findRecentSent` MUST check actual Gmail SENT messages (cross-chat history).
 */
export async function guardedOutbound(input, {findRecentSent, deliver, ledgerFile, suppressionFile, now, env}={}) {
  input = input || {};
  const config = env || process.env;
  const purpose = input.purpose || 'outreach'; // fail-closed default
  if (activeContactHold(input, config)) return blocked('Recipient is on explicit NOVA do-not-follow-up hold');
  // Enforce owner approval for every purpose, even for direct guard callers.
  if (input.approved !== true) return blocked('Explicit approval required');
  if (purpose !== 'outreach') {
    if (purpose !== 'transactional') return blocked('Unknown mail purpose');
    return await deliver();
  }
  const recipient = singleRecipient(input);
  if (!recipient) return blocked('Outreach requires exactly one valid To address and no Cc/Bcc');
  const ledger = path.resolve(ledgerFile || config.NOVA_MAIL_LEDGER_FILE || './status/nova-mail-ledger.json');
  const suppress = path.resolve(suppressionFile || config.NOVA_MAIL_SUPPRESSION_FILE || './status/nova-mail-suppressions.json');
  const timestamp = Number.isFinite(now) ? now : Date.now();
  const fingerprint = digest(recipient + '\n' + input.subject + '\n' + input.text);
  let release;
  let entryId;
  try {
    release = await lock(`${ledger}.lock`);
    if (await suppressed(recipient, suppress, config)) return blocked('Recipient is on the outreach suppression list');
    let entries = await readJson(ledger, []);
    if (!Array.isArray(entries)) throw new Error('Invalid mail ledger');
    entries = entries.filter(e => e && Number.isFinite(e.at) && timestamp - e.at < 90 * 86400000);
    if (entries.some(e => e.recipient === recipient && timestamp - e.at >= 0 && timestamp - e.at < QUIET_MS)) {
      return blocked('Recipient contacted in the last seven days or has an unresolved delivery attempt');
    }
    if (typeof findRecentSent !== 'function') return blocked('Gmail sent-history verification is not configured');
    let recent;
    try { recent = await findRecentSent(recipient); }
    catch { return blocked('Gmail sent-history verification failed; outreach paused'); }
    if (recent !== false) return blocked('Gmail sent history is not clear within the last seven days');
    entryId = digest(`${timestamp}:${recipient}:${fingerprint}:${Math.random()}`).slice(0,24);
    entries.push({id:entryId,recipient,bodyFingerprint:fingerprint,at:timestamp,state:'pending',provider:input.provider || config.NOVA_MAIL_PROVIDER || 'gmail'});
    await saveLedger(ledger, entries);
  } catch (err) {
    return blocked('Outreach preflight unavailable: ' + err.message);
  } finally {
    if (release) await release();
  }
  let result;
  try { result = await deliver(); }
  catch { result = blocked('Provider result uncertain; review sent mail before any retry'); }
  const delivered = result?.sent === true;
  // If provider outcome is ambiguous, preserve the hold even if updating fails.
  // Clear the FIRST lock's release callback before acquiring another lock;
  // otherwise a failed second acquisition could unlink another worker's lock.
  release = null;
  try {
    release = await lock(`${ledger}.lock`);
    const entries = await readJson(ledger, []);
    const item = entries.find(e => e.id === entryId);
    if (item) item.state = delivered ? 'sent' : 'uncertain';
    await saveLedger(ledger, entries);
  } catch {
    return blocked('Delivery attempted, but ledger update failed; verify provider history manually');
  } finally {
    if (release) await release();
  }
  return result;
}
