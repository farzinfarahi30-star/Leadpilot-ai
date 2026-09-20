import { buildDnsPlan, verifyDns, dnsAuthorityStatus } from './dns-manager.mjs';

const plan=buildDnsPlan();
if(plan.authority!=='nova'||plan.records.length!==4)throw new Error('Nova DNS plan invalid');
const status=dnsAuthorityStatus();
if(status.authority!=='nova'||status.authoritativeDns!==false)throw new Error('Authority boundary invalid');
const live=await verifyDns();
console.log(JSON.stringify({ok:true,plan,status,live},null,2));
