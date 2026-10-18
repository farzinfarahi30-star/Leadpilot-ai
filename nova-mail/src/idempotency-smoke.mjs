import assert from 'node:assert/strict';
import { sendEmail } from './core.mjs';

// Local-only smoke test. No requests leave this process.
const originalFetch=globalThis.fetch;
const originalKey=process.env.RESEND_API_KEY;
const originalFrom=process.env.RESEND_FROM;
let requests=[];
try {
  process.env.RESEND_API_KEY='test-api-key-not-real';
  process.env.RESEND_FROM='sender@example.test';
  globalThis.fetch=async (url,options)=>{
    requests.push({url,options});
    return {ok:true,status:200,text:async()=>JSON.stringify({id:'fake-message-1'})};
  };

  const sample={approved:true,provider:'resend',to:'recipient@example.test',
    subject:'Proof of idempotency',text:'This is only a local test.',
    idempotencyKey:'nova-test-abc123'};
  const sent=await sendEmail(sample);
  assert.equal(sent.sent,true);
  assert.equal(requests.length,1);
  assert.equal(requests[0].url,'https://api.resend.com/emails');
  assert.equal(requests[0].options.headers['Idempotency-Key'],'nova-test-abc123');
  const payload=JSON.parse(requests[0].options.body);
  assert.equal('idempotency_key' in payload,false);
  assert.equal(payload.to[0],'recipient@example.test');

  const blocked=await sendEmail({...sample,approved:false});
  assert.equal(blocked.blocked,true);
  assert.equal(requests.length,1);

  await assert.rejects(sendEmail({...sample,idempotencyKey:'a'.repeat(257)}),/idempotencyKey/);
  assert.equal(requests.length,1);

  await sendEmail({...sample,idempotencyKey:undefined});
  assert.equal(requests.length,2);
  assert.equal('Idempotency-Key' in requests[1].options.headers,false);
  console.log(JSON.stringify({ok:true,checks:8,network_calls:0}));
} finally {
  globalThis.fetch=originalFetch;
  if(originalKey===undefined)delete process.env.RESEND_API_KEY;
  else process.env.RESEND_API_KEY=originalKey;
  if(originalFrom===undefined)delete process.env.RESEND_FROM;
  else process.env.RESEND_FROM=originalFrom;
}
