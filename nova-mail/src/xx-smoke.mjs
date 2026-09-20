import { buildXxTakeover } from './xx-control.mjs';

const takeover=buildXxTakeover({
  operation:'mail.send',
  blocker:'primary Nova transport unavailable'
});

if(takeover.control!=='xx')throw new Error('xx control missing');
if(takeover.takeover!==true)throw new Error('xx takeover not enabled');
if(takeover.mode!=='xx-only-escalation')throw new Error('wrong escalation mode');
if(takeover.policy.alternateOutsideXx!==false)throw new Error('outside-xx fallback detected');
if(takeover.policy.inventNewController!==false)throw new Error('competing controller policy detected');

console.log(JSON.stringify({ok:true,control:takeover.control,mode:takeover.mode,policy:takeover.policy}));
