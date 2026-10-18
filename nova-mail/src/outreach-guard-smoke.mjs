import assert from 'node:assert/strict';
import os from 'node:os';
import fs from 'node:fs/promises';
import path from 'node:path';
import { activeContactHold, guardedOutbound } from './outreach-guard.mjs';

const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'nova-mail-smoke-'));
const options = {
  ledgerFile: path.join(dir, 'ledger.json'),
  suppressionFile: path.join(dir, 'suppressed.json'),
  now: Date.now(),
  env: {},
  findRecentSent: async () => false,
  findRecentDeliveryFailure: async () => false,
  deliver: async () => ({sent:true, provider:'mock'})
};
const offer = (to, subject='Free audit follow-up') =>
  ({to, subject, text:'Example only — do not send.', approved:true, purpose:'outreach'});
try {
  assert.equal(activeContactHold({to:'BESTEIGENOFFICE@gmail.com'}), true);
  assert.equal(activeContactHold({to:'Buyer <contact@wordykid.com>'}), true);
  assert.equal(activeContactHold({cc:'contact@wordykid.com'}), true);
  assert.equal(activeContactHold({bcc:'besteigenoffice@gmail.com'}), true);
  assert.equal(activeContactHold({to:'other@example.com'}, {NOVA_MAIL_SUPPRESSED_RECIPIENTS:'other@example.com'}), true);
  let delivered = 0;
  const forbidden = await guardedOutbound(offer('besteigenoffice@gmail.com'), {
    ...options, deliver: async () => { delivered++; return {sent:true}; }
  });
  assert.equal(forbidden.blocked, true);
  const transactional = await guardedOutbound({...offer('contact@wordykid.com'),purpose:'transactional'}, {
    ...options, deliver: async () => { delivered++; return {sent:true}; }
  });
  assert.equal(transactional.blocked, true);
  const unapprovedTransactional = await guardedOutbound({
    ...offer('allowed@example.com'), purpose:'transactional', approved:false
  }, {
    ...options, deliver: async () => { delivered++; return {sent:true}; }
  });
  assert.equal(unapprovedTransactional.blocked, true, 'No transactional bypass of approval');
  assert.equal(delivered, 0, 'No provider call for any explicitly suppressed contact');

  const first = await guardedOutbound(offer('buyer@example.com'), options);
  assert.equal(first.sent, true);
  const repeat = await guardedOutbound(offer('buyer@example.com', 'Another offer'), options);
  assert.equal(repeat.blocked, true, 'Seven-day local hold blocks follow-up');

  const alreadySent = await guardedOutbound(offer('sent@example.com'), {
    ...options, findRecentSent: async () => true,
    deliver: async () => { delivered++; return {sent:true}; }
  });
  assert.equal(alreadySent.blocked, true, 'Existing Gmail Sent history blocks send');
  assert.equal(delivered, 0);

  const uncertain = await guardedOutbound(offer('uncertain@example.com'), {
    ...options, deliver: async () => { throw new Error('Simulated timeout'); }
  });
  assert.equal(uncertain.blocked, true);
  const retry = await guardedOutbound(offer('uncertain@example.com', 'Edited subject'), options);
  assert.equal(retry.blocked, true, 'Provider error cannot trigger an automatic duplicate retry');

  const rows = JSON.parse(await fs.readFile(options.ledgerFile, 'utf8'));
  assert.equal(rows.some(row => row.recipient === 'buyer@example.com' && row.state === 'sent'), true);
  assert.equal(rows.some(row => row.recipient === 'uncertain@example.com' && row.state === 'uncertain'), true);
  console.log(JSON.stringify({ok:true, safetyAssertions:17, realEmailsSent:0}));
} finally {
  await fs.rm(dir, {recursive:true, force:true});
}
