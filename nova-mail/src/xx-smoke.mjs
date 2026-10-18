import { buildXxTakeover, isDefinitelyPreSendFailure } from './xx-control.mjs';

const takeover=buildXxTakeover({
  operation:'mail.send',
  blocker:'primary Nova transport unavailable'
});

if(takeover.control!=='xx')throw new Error('xx control missing');
if(takeover.takeover!==true)throw new Error('xx takeover not enabled');
if(takeover.mode!=='xx-only-escalation')throw new Error('wrong escalation mode');
if(takeover.policy.alternateOutsideXx!==false)throw new Error('outside-xx fallback detected');
if(takeover.policy.inventNewController!==false)throw new Error('competing controller policy detected');

if(!isDefinitelyPreSendFailure(new Error('GMAIL_REFRESH_TOKEN missing')))throw new Error('pre-send credential failure should allow takeover');
if(!isDefinitelyPreSendFailure(new Error('Gmail token 400: invalid_grant')))throw new Error('pre-send token failure should allow takeover');
if(isDefinitelyPreSendFailure(new Error('Gmail 500: connection reset')))throw new Error('ambiguous Gmail request must block takeover');
if(isDefinitelyPreSendFailure(new Error('Resend 503: timed out')))throw new Error('ambiguous Resend request must block takeover');
if(isDefinitelyPreSendFailure(new Error('fetch failed')))throw new Error('network error must block takeover');
console.log(JSON.stringify({ok:true,control:takeover.control,mode:takeover.mode,policy:takeover.policy,duplicate_retry_guards:5}));
