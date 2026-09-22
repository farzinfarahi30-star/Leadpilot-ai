import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const REGISTRY_PATH = path.join(ROOT, 'nova-runtime', 'xx-takeover-registry.json');

export function loadXxRegistry() {
  return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
}

function requiredFiles(target) {
  return [target.manifest, target.validator, target.runner];
}

export async function validateXxRegistry(registry = loadXxRegistry()) {
  const errors = [];
  if (registry?.schema !== 'nova.xx.takeover.registry.v1') errors.push('schema mismatch');
  if (registry?.control !== 'XX') errors.push('control must be XX');
  if (registry?.owner !== 'Nova') errors.push('owner must be Nova');
  if (!Array.isArray(registry?.targets) || registry.targets.length < 2) errors.push('at least two takeover targets required');

  for (const target of registry.targets || []) {
    for (const rel of requiredFiles(target)) {
      if (!fs.existsSync(path.join(ROOT, rel))) errors.push(`${target.id}: missing ${rel}`);
    }
    if (!target.manifest || !target.validator) errors.push(`${target.id}: incomplete target definition`);
  }

  const security = registry?.security || {};
  for (const key of [
    'publicThirdPartyReplicationOnly',
    'neverStorePrivateKeys',
    'neverStoreWalletSeeds',
    'neverStoreOAuthRefreshTokens',
    'neverSelfGrantExternalAuthority',
    'neverFabricateEvidence'
  ]) {
    if (security[key] !== true) errors.push('security control disabled: ' + key);
  }

  return { ok: errors.length === 0, errors, checkedAt: new Date().toISOString() };
}

export async function buildXxTakeoverRegistry() {
  const registry = loadXxRegistry();
  const validation = await validateXxRegistry(registry);
  return {
    control: 'xx',
    owner: 'nova',
    registry: 'nova.xx.takeover.registry.v1',
    takeover: true,
    targets: registry.targets,
    security: registry.security,
    validation
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  console.log(JSON.stringify(await buildXxTakeoverRegistry(), null, 2));
}
