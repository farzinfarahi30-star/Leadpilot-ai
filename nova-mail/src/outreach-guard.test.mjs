import assert from 'node:assert/strict';
import test from 'node:test';
import {assessOutreachHistory, outreachRecipients, reserveOutreachRecipients, preflightOutreach} from './outreach-guard.mjs';

const day = 24 * 60 * 60 * 1000;
const now = Date.parse('2026-10-18T12:00:00Z');

test('blocks fresh outbound without new inbound', () => {
  assert.equal(assessOutreachHistory({latestSent:now-60_000}, now).allowed, false);
});
test('allows actual reply after latest send', () => {
  assert.equal(assessOutreachHistory({latestSent:now-day, latestInbound:now-1000}, now).allowed, true);
});
test('allows a new outreach after full cool-down', () => {
  assert.equal(assessOutreachHistory({latestSent:now-8*day}, now).allowed, true);
});
test('decline overrides newer inbound', () => {
  assert.equal(assessOutreachHistory({latestSent:now-day, latestInbound:now,heldLabels:['NOVA / Declined - do not pitch']}, now).allowed, false);
});
test('unique recipient normalisation and in-flight protection', () => {
  const recipients = outreachRecipients({to:'Test <TEST@Example.com>',cc:'test@example.com'});
  assert.deepEqual(recipients,['test@example.com']);
  const release = reserveOutreachRecipients(recipients);
  assert.equal(typeof release,'function');
  assert.equal(reserveOutreachRecipients(recipients),null);
  release();
  const releaseAgain=reserveOutreachRecipients(recipients);
  assert.equal(typeof releaseAgain,'function');
  releaseAgain();
});
test('preflight uses live Gmail metadata and detects existing outreach hold', async () => {
  const gmail = async endpoint => {
    if (endpoint === 'labels') return {labels:[{id:'Label_60',name:'NOVA / Declined - do not pitch'}]};
    if (endpoint.startsWith('messages?')) {
      const q=new URL('https://x.test/'+endpoint).searchParams.get('q');
      return {messages:[{id:q.startsWith('in:sent')?'out':'in'}]};
    }
    if (endpoint.includes('/out?')) return {internalDate:String(now-day),labelIds:[]};
    if (endpoint.includes('/in?')) return {internalDate:String(now-1000),labelIds:['Label_60']};
    throw new Error('unexpected endpoint '+endpoint);
  };
  const result=await preflightOutreach({to:'buyer@example.com'},gmail,now);
  assert.equal(result.allowed,false);
  assert.match(result.reason,/hold/);
});
test('preflight fails closed for multi-recipient email', async () => {
  const r=await preflightOutreach({to:'a@example.com,b@example.com'},async()=>{throw Error('should not fetch')},now);
  assert.equal(r.allowed,false);
});
