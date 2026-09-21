import process from 'node:process';
import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';

const CHAIN_ID = 11155111;
const DEFAULT_OWNER = '0x63970A951bd69975eF2aDAD27bf73584D2DCeF9B';
const ROOT = process.cwd();
const SCRIPT = path.join(ROOT, 'nova-economy', 'script', 'DeployNovaToken.s.sol:DeployNovaToken');
const BROADCAST = path.join(
  ROOT,
  'nova-economy',
  'broadcast',
  'DeployNovaToken.s.sol',
  String(CHAIN_ID),
  'run-latest.json'
);

function env(name) {
  return String(process.env[name] || '').trim();
}

function assertOwner(owner = DEFAULT_OWNER) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(String(owner))) {
    throw new Error('NOVA owner must be a valid 20-byte address');
  }
  if (String(owner).toLowerCase() !== DEFAULT_OWNER.toLowerCase()) {
    throw new Error('NOVA owner mismatch; refusing deployment');
  }
  return owner;
}

function assertCap(value = 1000000) {
  const cap = Number(value);
  if (!Number.isSafeInteger(cap) || cap <= 0) {
    throw new Error('NOVA max supply must be a positive safe integer');
  }
  return cap;
}

async function command(cmd, args, { timeoutMs = 120000 } = {}) {
  return await new Promise((resolve, reject) => {
    const child = spawn(cmd, args, {
      cwd: ROOT,
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      reject(new Error(`${cmd} timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      if (code === 0) return resolve({ stdout: stdout.trim(), stderr: stderr.trim() });
      reject(new Error(`${cmd} exited with code ${code ?? 'null'}${signal ? ` signal ${signal}` : ''}: ${(stderr || stdout).slice(-1500)}`));
    });
  });
}

async function requireTool(name) {
  await command(name, ['--version'], { timeoutMs: 30000 });
  return true;
}

async function chainId() {
  const result = await command('cast', ['chain-id', '--rpc-url', env('SEPOLIA_RPC_URL')], { timeoutMs: 30000 });
  return Number(result.stdout);
}

async function tokenCalls(address) {
  const rpc = env('SEPOLIA_RPC_URL');
  const [owner, cap, supply] = await Promise.all([
    command('cast', ['call', address, 'owner()(address)', '--rpc-url', rpc], { timeoutMs: 30000 }),
    command('cast', ['call', address, 'maxSupply()(uint256)', '--rpc-url', rpc], { timeoutMs: 30000 }),
    command('cast', ['call', address, 'totalSupply()(uint256)', '--rpc-url', rpc], { timeoutMs: 30000 })
  ]);
  return {
    owner: owner.stdout,
    maxSupplyWei: owner.stdout && cap.stdout,
    totalSupplyWei: supply.stdout
  };
}

export async function novaChainPreflight({
  owner = DEFAULT_OWNER,
  maxSupplyTokens = 1000000,
  requireDeployerAddress = false
} = {}) {
  const expectedOwner = assertOwner(owner);
  const cap = assertCap(maxSupplyTokens);
  const rpc = env('SEPOLIA_RPC_URL');
  const privateKey = env('NOVA_DEPLOYER_PRIVATE_KEY');
  const deployerAddress = env('NOVA_DEPLOYER_ADDRESS');

  const missing = [];
  if (!rpc) missing.push('SEPOLIA_RPC_URL');
  if (!privateKey) missing.push('NOVA_DEPLOYER_PRIVATE_KEY');
  if (requireDeployerAddress && !deployerAddress) missing.push('NOVA_DEPLOYER_ADDRESS');
  if (deployerAddress && !/^0x[0-9a-fA-F]{40}$/.test(deployerAddress)) {
    throw new Error('NOVA_DEPLOYER_ADDRESS must be a valid 20-byte address');
  }
  if (missing.length) {
    return {
      ready: false,
      chain: 'sepolia',
      chainId: CHAIN_ID,
      owner: expectedOwner,
      maxSupplyTokens: cap,
      missing
    };
  }

  await requireTool('forge');
  await requireTool('cast');
  const actualChainId = await chainId();
  if (actualChainId !== CHAIN_ID) {
    throw new Error(`Wrong RPC chain ID: expected ${CHAIN_ID}, received ${actualChainId}`);
  }

  let balanceWei = null;
  if (deployerAddress) {
    const result = await command('cast', ['balance', deployerAddress, '--ether', '--rpc-url', rpc], { timeoutMs: 30000 });
    balanceWei = result.stdout;
  }

  return {
    ready: true,
    chain: 'sepolia',
    chainId: actualChainId,
    owner: expectedOwner,
    maxSupplyTokens: cap,
    deployerAddress: deployerAddress || null,
    deployerPrivateKeyConfigured: Boolean(privateKey),
    deployerBalanceEth: balanceWei
  };
}

function extractDeployment(data) {
  const transactions = Array.isArray(data?.transactions) ? data.transactions : [];
  const deployed = transactions.filter(
    (tx) => tx?.transactionType === 'CREATE' && tx?.contractName === 'NovaToken'
  );
  const tx = deployed.at(-1);
  if (!tx?.contractAddress) throw new Error('NovaToken CREATE transaction not found in Foundry broadcast output');
  const txHash = tx.hash || tx.transactionHash || tx.txHash || null;
  return {
    contractAddress: tx.contractAddress,
    transactionHash: txHash,
    blockNumber: tx.blockNumber ?? null
  };
}

export async function deployNovaTokenSepolia({
  owner = DEFAULT_OWNER,
  maxSupplyTokens = 1000000,
  verify = true
} = {}) {
  const preflight = await novaChainPreflight({ owner, maxSupplyTokens, requireDeployerAddress: false });
  if (!preflight.ready) {
    throw new Error('NOVA Sepolia preflight incomplete: missing ' + preflight.missing.join(', '));
  }

  const cap = assertCap(maxSupplyTokens);
  process.env.NOVA_OWNER = assertOwner(owner);
  process.env.NOVA_MAX_SUPPLY_TOKENS = String(cap);

  await command(
    'forge',
    ['script', SCRIPT, '--rpc-url', env('SEPOLIA_RPC_URL'), '--broadcast'],
    { timeoutMs: 180000 }
  );

  const data = JSON.parse(await fs.readFile(BROADCAST, 'utf8'));
  const deployment = extractDeployment(data);

  let verification = null;
  if (verify) {
    verification = await verifyNovaTokenSepolia({
      address: deployment.contractAddress,
      owner,
      maxSupplyTokens: cap,
      requireZeroSupply: true
    });
  }

  const record = {
    network: 'sepolia',
    chainId: CHAIN_ID,
    owner,
    maxSupplyTokens: cap,
    contractAddress: deployment.contractAddress,
    transactionHash: deployment.transactionHash,
    blockNumber: deployment.blockNumber,
    verification,
    recordedAt: new Date().toISOString()
  };
  await fs.writeFile(
    path.join(ROOT, 'nova-economy', 'deployment-sepolia.json'),
    JSON.stringify(record, null, 2) + '\n',
    { mode: 0o600 }
  );

  return record;
}

export async function verifyNovaTokenSepolia({
  address,
  owner = DEFAULT_OWNER,
  maxSupplyTokens = 1000000,
  requireZeroSupply = true
} = {}) {
  const contractAddress = String(address || '').trim();
  if (!/^0x[0-9a-fA-F]{40}$/.test(contractAddress)) {
    throw new Error('NOVA contract address is invalid');
  }

  const expectedOwner = assertOwner(owner);
  const cap = assertCap(maxSupplyTokens);
  const rpc = env('SEPOLIA_RPC_URL');
  if (!rpc) throw new Error('SEPOLIA_RPC_URL missing');

  const actualChainId = await chainId();
  if (actualChainId !== CHAIN_ID) {
    throw new Error(`Wrong RPC chain ID: expected ${CHAIN_ID}, received ${actualChainId}`);
  }

  const onchain = await tokenCalls(contractAddress);
  const expectedCapWei = String(BigInt(cap) * 1000000000000000000n);
  const observedOwner = onchain.owner.replace(/^"|"$/g, '').trim();
  const observedCap = onchain.maxSupplyWei.trim();
  const observedSupply = onchain.totalSupplyWei.trim();

  if (observedOwner.toLowerCase() !== expectedOwner.toLowerCase()) {
    throw new Error(`Owner mismatch: expected ${expectedOwner}, received ${observedOwner}`);
  }
  if (observedCap !== expectedCapWei) {
    throw new Error(`maxSupply mismatch: expected ${expectedCapWei}, received ${observedCap}`);
  }
  if (requireZeroSupply && observedSupply !== '0') {
    throw new Error(`Initial totalSupply must be zero, received ${observedSupply}`);
  }

  return {
    verified: true,
    network: 'sepolia',
    chainId: CHAIN_ID,
    contractAddress,
    owner: observedOwner,
    maxSupplyWei: observedCap,
    totalSupplyWei: observedSupply
  };
}
