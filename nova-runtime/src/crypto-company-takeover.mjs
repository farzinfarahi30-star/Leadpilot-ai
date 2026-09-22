import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const ROOT = process.cwd();
const MANIFEST = path.join(ROOT, 'nova-runtime', 'crypto-company-takeover-manifest.json');

export function loadCryptoTakeoverManifest() {
  return JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
}

function exists(rel) {
  return fs.existsSync(path.join(ROOT, rel));
}

export function validateCryptoTakeoverManifest(manifest = loadCryptoTakeoverManifest()) {
  const errors = [];
  if (manifest?.schema !== 'nova.crypto.takeover.v1') errors.push('schema mismatch');
  if (manifest?.control !== 'XX') errors.push('control must be XX');
  if (manifest?.owner !== 'Nova') errors.push('owner must be Nova');
  if (manifest?.handoff?.takeoverMode !== 'crypto-project-replication-takeover') errors.push('takeover mode mismatch');
  if (manifest?.source?.repository !== 'farzinfarahi30-star/Leadpilot-ai') errors.push('source repository mismatch');
  if (manifest?.system?.network?.chainId !== 11155111) errors.push('network must be Sepolia');
  if (manifest?.system?.token?.symbol !== 'NOVA') errors.push('token symbol mismatch');
  if (Number(manifest?.system?.token?.maxSupplyTokens) !== 1000000) errors.push('max supply mismatch');
  if (String(manifest?.system?.token?.owner || '').toLowerCase() !== '0x63970a951bd69975ef2adad27bf73584d2dcef9b') errors.push('owner address mismatch');

  const requiredFiles = [
    ...(manifest?.importantFiles || []),
    'nova-economy/contracts/NovaToken.sol',
    'nova-economy/script/DeployNovaToken.s.sol',
    'nova-economy/script/AddUniswapV2Liquidity.s.sol',
    'nova-runtime/src/nova-chain-controller.mjs',
    'nova-runtime/src/crypto-capabilities.mjs',
    'nova-runtime/src/coinbase-cdp.mjs',
    'nova-runtime/src/chainstack-mcp.mjs',
    'nova-runtime/src/alchemy.mjs',
    'nova-runtime/src/device-tools.mjs'
  ];
  for (const rel of [...new Set(requiredFiles)]) {
    if (!exists(rel)) errors.push('missing required file: ' + rel);
  }

  const groups = manifest?.programs || {};
  for (const key of ['token_and_contract','chain_operations','provider_mesh','runtime_and_devices','liquidity_and_production','governance_and_safety']) {
    if (!Array.isArray(groups[key]) || groups[key].length === 0) errors.push('program group empty: ' + key);
  }

  const secretPolicy = String(manifest?.securityBoundary?.secretsPolicy || '');
  if (!/never private keys/i.test(secretPolicy) || !/wallet seeds/i.test(secretPolicy)) {
    errors.push('secret policy incomplete');
  }

  const encoded = JSON.stringify(manifest);
  if (/BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|0x[a-f-f0-9]{64}/i.test(encoded)) {
    errors.push('possible private-key material found in manifest');
  }

  return { ok: errors.length === 0, errors, checkedAt: new Date().toISOString() };
}

export function buildCryptoTakeoverPlan() {
  const manifest = loadCryptoTakeoverManifest();
  const validation = validateCryptoTakeoverManifest(manifest);
  return {
    control: 'xx',
    mode: manifest.handoff.takeoverMode,
    takeover: true,
    owner: 'nova',
    handoffStatus: manifest.handoff.status,
    source: manifest.source,
    system: manifest.system,
    programs: manifest.programs,
    tools: manifest.tools,
    importantFiles: manifest.importantFiles,
    productionGates: manifest.productionGates,
    validation,
    rule: 'Nova operates the replicated crypto project through the existing runtime/governance controls; no competing controller is created.'
  };
}

export function assertCryptoTakeoverReady() {
  const result = validateCryptoTakeoverManifest();
  if (!result.ok) throw new Error('Crypto takeover manifest invalid: ' + result.errors.join('; '));
  return result;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  console.log(JSON.stringify(buildCryptoTakeoverPlan(), null, 2));
}
