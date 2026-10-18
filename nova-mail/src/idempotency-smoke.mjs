import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { sendEmail } from './core.mjs';

// Offline verification of Resend's idempotency header through the real
// outreach guard. The Gmail sent-history check is mocked as empty.
const saved = Object.fromEntries(['RESEND_API_KEY','RESEND_FROM','GMAIL_ACCESS_TOKEN','NOVA_MAIL_LEDGER_FILE','NOVA_MAIL_SUPPRESSION_FILE'].map(k=>[k,process.env[k]]));
const originalFetch=globalThis.fetch;
const directory=await mkdtemp(path.join(tmpdir(),'nova-mail-idempotency-'));
const requests=[];
try {
  process.env.RESEND_API_KEY='test-api-key-not-real';
  process.env.RESEND_FROM='sender@example.test';
  process.env.GMAIL_ACCESS_TOKEN='test-gmail-token-not-real';
  process.env.NOVA_MAIL_LEDGER_FILE=path.join(directory,'ledger.json');
  process.env.NOVA_MAIL_SUPPRESSION_FILE=path.join(directory,'suppressions.json');
  globalThis.fetch=async (url,options={})=>{
    if(String(url).startsWith('https://gmail.googleapis.com/gmail/v1/users/me/messages?')){
      return {ok:true,status:200,text:async()=>JSON.stringify({messages:[]})};
    }
    assert.equal(url,'https://api.resend.com/emails');
    requests.push({url,options});
    return {ok:true,status:200,text:async()=>JSON.stringify({id:'fake-message-1'})};
  };

  const sample={approved:true,provider:'resend',to:'recipient1@example.test',
    subject:'Proof of idempotency',text:'This is only a local test.',
    idempotencyKey:'nova-test-abc123'};
  const sent=await sendEmail(sample);
  assert.equal(sent.sent,true);
  assert.equal(requests.length,1);
  assert.equal(requests[0].options.headers['Idempotency-Key'],'nova-test-abc123');
  const payload=JSON.parse(requests[0].options.body);
  assert.equal('idempotency_key' in payload,false);
  assert.equal(payload.to[0],'recipient1@example.test');

  const blocked=await sendEmail({...sample,approved:false});
  assert.equal(blocked.blocked,true);
  assert.equal(requests.length,1);

  const duplicate=await sendEmail(sample);
  assert.equal(duplicate.blocked,true);
  assert.equal(requests.length,1);

  const invalid=await sendEmail({...sample,to:'recipient2@example.test',idempotencyKey:'a'.repeat(257)});
  assert.equal(invalid.sent,false);
  assert.equal(invalid.blocked,true);
  assert.equal(requests.length,1);

  const noKey=await sendEmail({...sample,to:'recipient3@example.test',idempotencyKey:undefined});
  assert.equal(noKey.sent,true);
  assert.equal(requests.length,2);
  assert.equal('Idempotency-Key' in requests[1].options.headers,false);

  console.log(JSON.stringify({ok:true,checks:14,external_network_requests:0}));
} finally {
  globalThis.fetch=originalFetch;
  for(const [key,value] of Object.entries(saved)){
    if(value===undefined)delete process.env[key];else process.env[key]=value;
  }
  await rm(directory,{recursive:true,force:true});
}
