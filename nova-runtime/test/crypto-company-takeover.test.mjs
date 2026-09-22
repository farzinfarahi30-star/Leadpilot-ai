import assert from 'node:assert/strict';
import {
  buildCryptoTakeoverPlan,
  loadCryptoTakeoverManifest,
  validateCryptoTakeoverManifest
} from '../src/crypto-company-takeover.mjs';

const manifest = loadCryptoTakeoverManifest();
const validation = validateCryptoTakeoverManifest(manifest);

assert.equal(validation.ok, true, validation.errors.join('; '));
assert.equal(manifest.control, 'XX');
assert.equal(manifest.owner, 'Nova');
assert.equal(manifest.handoff.takeoverMode, 'crypto-project-replication-takeover');
assert.equal(manifest.system.network.chainId, 11155111);
assert.equal(manifest.system.token.symbol, 'NOVA');
assert.equal(manifest.system.token.maxSupplyTokens, 1000000);
assert.equal(manifest.programs.token_and_contract.length > 0, true);
assert.equal(manifest.programs.provider_mesh.length > 0, true);
assert.equal(manifest.programs.liquidity_and_production.length > 0, true);

const plan = buildCryptoTakeoverPlan();
assert.equal(plan.takeover, true);
assert.equal(plan.mode, 'crypto-project-replication-takeover');
assert.equal(plan.owner, 'nova');
assert.equal(plan.validation.ok, true);

console.log(JSON.stringify({
  ok: true,
  control: plan.control,
  mode: plan.mode,
  source: plan.source,
  network: plan.system.network,
  token: {
    symbol: plan.system.token.symbol,
    maxSupplyTokens: plan.system.token.maxSupplyTokens
  },
  programGroups: Object.keys(plan.programs).length,
  toolCount: plan.tools.length,
  productionState: plan.productionGates.currentState
}, null, 2));
