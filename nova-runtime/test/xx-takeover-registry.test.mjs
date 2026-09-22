import assert from 'node:assert/strict';
import { buildXxTakeoverRegistry, loadXxRegistry, validateXxRegistry } from '../src/xx-takeover-registry.mjs';

const registry = loadXxRegistry();
const validation = await validateXxRegistry(registry);

assert.equal(validation.ok, true, validation.errors.join('; '));
assert.equal(registry.control, 'XX');
assert.equal(registry.owner, 'Nova');
assert.equal(registry.targets.length >= 2, true);
assert.equal(registry.targets.some(x => x.id === 'ai-business-factory'), true);
assert.equal(registry.targets.some(x => x.id === 'nova-crypto-economic-layer'), true);

const plan = await buildXxTakeoverRegistry();
assert.equal(plan.takeover, true);
assert.equal(plan.validation.ok, true);

console.log(JSON.stringify({
  ok:true,
  control:plan.control,
  owner:plan.owner,
  targetCount:plan.targets.length,
  targets:plan.targets.map(x => ({id:x.id,kind:x.kind,mode:x.mode})),
  security:plan.security
},null,2));
