import { buildXxTakeoverRegistry } from './xx-takeover-registry.mjs';
import { buildCompanyTakeoverPlan } from './company-takeover.mjs';
import { buildCryptoTakeoverPlan } from './crypto-company-takeover.mjs';

export async function buildNovaXxHandoff() {
  const registry = await buildXxTakeoverRegistry();
  const company = buildCompanyTakeoverPlan();
  const crypto = buildCryptoTakeoverPlan();
  const validations = {
    registry: registry.validation,
    company: company.validation,
    crypto: crypto.validation
  };
  return {
    control:'xx',
    owner:'nova',
    takeover:true,
    status:Object.values(validations).every(x=>x.ok)?'handoff-ready':'blocked',
    targets:{company,crypto},
    validations,
    rule:'Nova is the operating owner of every registered XX target; external authority and irreversible actions remain governed by their real authorization boundaries.'
  };
}

buildNovaXxHandoff().then(x=>console.log(JSON.stringify(x,null,2))).catch(error=>{console.error(error);process.exitCode=1;});
