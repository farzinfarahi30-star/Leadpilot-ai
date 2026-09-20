import { inspectNovaDomain, novaDnsManifest, NOVA_MAIL_DOMAIN } from './domain-authority.mjs';

const clean=v=>String(v??'').trim().replace(/\.$/,'');
const norm=v=>clean(v).toLowerCase();

export function buildDnsPlan(domain=NOVA_MAIL_DOMAIN){
  const manifest=novaDnsManifest();
  return {
    authority:'nova',
    mode:'plan-only',
    domain:norm(domain),
    records:manifest.records.map(r=>({
      type:r.type,
      name:r.name,
      purpose:r.purpose,
      expected:r.expected
    })),
    safeguards:[
      'No DNS mutation without an explicit approved change request.',
      'Never create conflicting SPF records.',
      'Never create conflicting apex MX records.',
      'Record every mutation with before/after evidence and rollback data.',
      'Provider credentials remain outside source code.'
    ]
  };
}

export async function verifyDns(domain=NOVA_MAIL_DOMAIN){
  return await inspectNovaDomain(domain);
}

export function dnsAuthorityStatus(domain=NOVA_MAIL_DOMAIN){
  return {
    authority:'nova',
    domain:norm(domain),
    authoritativeDns:false,
    reason:'Registrar/nameserver delegation is not connected to this runtime yet.',
    nextBoundary:'Delegate the domain nameservers to Nova-controlled authoritative DNS before Nova can mutate public DNS directly.'
  };
}
