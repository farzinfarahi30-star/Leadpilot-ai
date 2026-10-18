import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {guardedOutbound} from '../src/outreach-guard.mjs';

const input={to:'buyer@example.com',subject:'Proposal',text:'A respectful sales proposal',approved:true};
async function fixture() {
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'nova-guard-'));
  return {dir,ledgerFile:path.join(dir,'ledger.json'),suppressionFile:path.join(dir,'supp.json'),now:1760000000000,env:{},
    findRecentSent:async()=>false, findRecentDeliveryFailure:async()=>false};
}

test('first new outreach is delivered, repeat to same prospect is blocked',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  let sends=0;f.deliver=async()=>{sends++;return {sent:true,provider:'gmail'}};
  const first=await guardedOutbound(input,f);
  const second=await guardedOutbound({...input,subject:'Different pitch'},f);
  assert.equal(first.sent,true);assert.equal(second.blocked,true);assert.equal(sends,1);
});
test('fails closed when Gmail history cannot be checked',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  let sends=0;f.findRecentSent=async()=>{throw new Error('401')};f.deliver=async()=>{sends++;return {sent:true}};
  assert.equal((await guardedOutbound(input,f)).blocked,true);assert.equal(sends,0);
});
test('blocks existing Gmail Sent recipients',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  f.findRecentSent=async()=>true;f.deliver=async()=>{throw Error('must not send')};
  assert.equal((await guardedOutbound(input,f)).blocked,true);
});
test('blocks suppressed recipients',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  f.env={NOVA_MAIL_SUPPRESSED_RECIPIENTS:'buyer@example.com'};f.deliver=async()=>{throw Error('must not send')};
  assert.match((await guardedOutbound(input,f)).reason,/suppression/);
});
test('rejects mass outreach and Cc/Bcc',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  f.deliver=async()=>{throw Error('must not send')};
  assert.equal((await guardedOutbound({...input,to:'a@b.com,c@d.com'},f)).blocked,true);
  assert.equal((await guardedOutbound({...input,cc:'extra@example.com'},f)).blocked,true);
});
test('uncertain send never retries silently',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  let attempts=0;f.deliver=async()=>{attempts++;throw Error('socket timed out')};
  const a=await guardedOutbound(input,f);const b=await guardedOutbound(input,f);
  assert.equal(a.blocked,true);assert.match(a.reason,/uncertain/);assert.equal(b.blocked,true);assert.equal(attempts,1);
});
test('race cannot send the same recipient twice',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  let sends=0;f.deliver=async()=>{sends++;await new Promise(r=>setTimeout(r,25));return {sent:true}};
  const a=await Promise.all([guardedOutbound(input,f),guardedOutbound(input,f)]);
  assert.equal(a.filter(v=>v.sent).length,1);assert.equal(sends,1);
});
test('transactional mail is explicitly exempt from sales cooldown',async t=>{
  const f=await fixture();t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  f.deliver=async()=>({sent:true});f.findRecentSent=async()=>true;
  assert.equal((await guardedOutbound({...input,purpose:'transactional'},f)).sent,true);
});

test('blocks contacts with a recent delivery-failure notice',async t=>{
  const f=await fixture(); t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  let calls=0; f.findRecentDeliveryFailure=async recipient=>{
    assert.equal(recipient,'buyer@example.com');return true;
  };
  f.deliver=async()=>{calls++;return {sent:true}};
  const out=await guardedOutbound(input,f);
  assert.equal(out.blocked,true); assert.match(out.reason,/delivery-failure/);
  assert.equal(calls,0);
});
test('fails closed if bounce lookup cannot run',async t=>{
  const f=await fixture(); t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  f.findRecentDeliveryFailure=async()=>{throw Error('Gmail token expired')};
  f.deliver=async()=>{throw Error('must not send')};
  const out=await guardedOutbound(input,f);
  assert.equal(out.blocked,true); assert.match(out.reason,/verification failed/);
});
test('fails closed if bounce check not configured',async t=>{
  const f=await fixture(); t.after(()=>fs.rm(f.dir,{recursive:true,force:true}));
  delete f.findRecentDeliveryFailure;
  f.deliver=async()=>{throw Error('must not send')};
  const out=await guardedOutbound(input,f);
  assert.equal(out.blocked,true); assert.match(out.reason,/not configured/);
});
