import assert from 'node:assert/strict';
import { createDraft } from './core.mjs';

// Exercise the real Gmail MIME builder via createDraft; never contact Gmail.
const originalFetch = globalThis.fetch;
const originalAccessToken = process.env.GMAIL_ACCESS_TOKEN;
const originalAccount = process.env.GMAIL_ACCOUNT;
let captured = [];
try {
  process.env.GMAIL_ACCESS_TOKEN = 'local-mime-test-only';
  process.env.GMAIL_ACCOUNT = 'sender@example.test';
  globalThis.fetch = async (url, options) => {
    assert.match(String(url), /gmail\.googleapis\.com\/gmail\/v1\/users\/me\/drafts$/);
    assert.equal(options.method, 'POST');
    captured.push(Buffer.from(JSON.parse(options.body).message.raw, 'base64url').toString('utf8'));
    return {ok:true,status:200,text:async()=>JSON.stringify({id:'fake-draft-id',message:{id:'fake-message-id'}})};
  };

  await createDraft({to:'recipient@example.test',from:'sender@example.test',subject:'MIME smoke',text:'First line\nSecond line'});
  assert.equal(captured.length,1);
  const raw = captured[0];
  assert.match(raw,/^From: sender@example\.test\r\nTo: recipient@example\.test\r\nSubject: MIME smoke\r\n/);
  assert.match(raw,/Content-Type: text\/plain; charset=UTF-8\r\n\r\nFirst line\nSecond line$/);
  assert.equal(raw.split('\r\n\r\n').length,2);

  await createDraft({to:'other@example.test',from:'sender@example.test',cc:'copy@example.test',bcc:'hidden@example.test',subject:'Copy smoke',text:''});
  assert.match(captured[1],/\r\nCc: copy@example\.test\r\nBcc: hidden@example\.test\r\n/);
  assert.ok(captured[1].endsWith('\r\n\r\n'));

  await assert.rejects(createDraft({to:'recipient@example.test',from:'sender@example.test',subject:'Safe\r\nBcc: attacker@example.test',text:'hello'}),/Invalid email header/);
  assert.equal(captured.length,2); // injection must not reach Gmail
  await assert.rejects(createDraft({to:'recipient@example.test\r\nBcc: attacker@example.test',from:'sender@example.test',subject:'Safe',text:'hello'}),/Invalid email header/);
  assert.equal(captured.length,2);
  console.log(JSON.stringify({ok:true,mime_checks:8,external_network_requests:0}));
} finally {
  globalThis.fetch = originalFetch;
  if(originalAccessToken===undefined)delete process.env.GMAIL_ACCESS_TOKEN;
  else process.env.GMAIL_ACCESS_TOKEN=originalAccessToken;
  if(originalAccount===undefined)delete process.env.GMAIL_ACCOUNT;
  else process.env.GMAIL_ACCOUNT=originalAccount;
}
