import { promises as dns } from 'node:dns';

const clean=v=>String(v??'').trim().replace(/\.$/,'');
const norm=v=>clean(v).toLowerCase();

export const NOVA_MAIL_DOMAIN='novabusinessfactory.com';
export const NOVA_MAIL_FROM='hello@novabusinessfactory.com';

export const requiredRecords=[
  {type:'TXT',name:'_nova-verification',purpose:'Nova Domain Authority ownership proof',expectedEnv:'NOVA_DOMAIN_VERIFICATION_TOKEN'},
  {type:'TXT',name:'@',purpose:'SPF authorization for Nova mail infrastructure',expectedEnv:'NOVA_SPF_RECORD'},
  {type:'TXT',name:'nova._domainkey',purpose:'DKIM public key for Nova outbound mail',expectedEnv:'NOVA_DKIM_RECORD'},
  {type:'MX',name:'@',purpose:'Inbound mail delivery for Nova',expectedEnv:'NOVA_MX_HOST'}
];

async function txt(name){try{return (await dns.resolveTxt(name)).map(parts=>parts.join(''));}catch{return []}}
async function mx(name){try{return await dns.resolveMx(name);}catch{return []}}

export async function inspectNovaDomain(domain=NOVA_MAIL_DOMAIN){
  const d=norm(domain);
  const [rootTxt,verifyTxt,dkimTxt,mxRecords]=await Promise.all([
    txt(d),txt('_nova-verification.'+d),txt('nova._domainkey.'+d),mx(d)
  ]);
  const verificationToken=process.env.NOVA_DOMAIN_VERIFICATION_TOKEN||'';
  const spfExpected=process.env.NOVA_SPF_RECORD||'';
  const dkimExpected=process.env.NOVA_DKIM_RECORD||'';
  const mxExpected=norm(process.env.NOVA_MX_HOST||'');
  const spf=rootTxt.find(x=>/^v=spf1\b/i.test(x))||'';
  const checks={
    ownership:verificationToken?verifyTxt.includes(verificationToken):null,
    spf:spfExpected?norm(spf)===norm(spfExpected):/^v=spf1\b/i.test(spf),
    dkim:dkimExpected?norm(dkimTxt.join(''))===norm(dkimExpected):dkimTxt.some(x=>/^v=DKIM1;/i.test(x)),
    mx:mxExpected?mxRecords.some(x=>norm(x.exchange)===mxExpected):mxRecords.length>0
  };
  return {ok:Object.values(checks).every(v=>v===true),domain:d,from:NOVA_MAIL_FROM,checks,dns:{verificationTxt:verifyTxt,spf,dkim:dkimTxt,mx:mxRecords}};
}

export function novaDnsManifest(){
  return {domain:NOVA_MAIL_DOMAIN,records:requiredRecords.map(r=>({...r,expected:process.env[r.expectedEnv]||null}))};
}
