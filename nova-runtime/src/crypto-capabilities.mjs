import process from 'node:process';
import {
  alchemySepoliaBalance,
  alchemySepoliaRpcUrl,
  alchemySepoliaBlockNumber,
  alchemySepoliaChainId,
  alchemySepoliaTransactionReceipt
} from './alchemy.mjs';
import {
  coinbaseCdpConfigured,
  coinbaseCdpDoctor,
  coinbaseCdpRequestSepoliaEth,
  COINBASE_CDP_SEPOLIA
} from './coinbase-cdp.mjs';
import {
  chainstackMcpConfigured,
  chainstackMcpListTools,
  chainstackMcpRequestSepoliaEth
} from './chainstack-mcp.mjs';

const SEPOLIA_CHAIN_ID = 11155111;
const COINBASE_ETH_PER_CLAIM_WEI = 100000000000000n; // 0.0001 ETH; current CDP faucet limit.
const DEFAULT_MAX_CDP_CLAIMS = 20;

function env(name) {
  return String(process.env[name] || '').trim();
}

function assertAddress(address) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(String(address || ''))) {
    throw new Error('Ethereum address is invalid');
  }
}

export const NOVA_CRYPTO_CAPABILITIES = Object.freeze({
  primaryNetwork: {
    name: 'ethereum-sepolia',
    chainId: SEPOLIA_CHAIN_ID
  },
  providers: {
    alchemy: ['rpc', 'balance', 'blocks', 'receipts', 'portfolio', 'prices', 'transfers', 'nft', 'bundler'],
    coinbaseCdp: ['sepoliaFaucet', 'evmAccounts', 'onchainWallets'],
    chainstack: ['mcp', 'testnetFaucet', 'rpc', 'nodeInfrastructure']
  },
  controls: {
    ownerLocked: true,
    privateKeyNeverReturned: true,
    mainnetDeploymentDisabledByDefault: true,
    stateChangingAlchemyRpcBlocked: true
  }
});

export function novaCryptoCapabilityManifest() {
  return NOVA_CRYPTO_CAPABILITIES;
}

export function novaCryptoDoctor() {
  return {
    network: 'ethereum-sepolia',
    chainId: SEPOLIA_CHAIN_ID,
    alchemy: {
      configured: Boolean(env('NOVA_ALCHEMY_API_KEY') || env('ALCHEMY_API_KEY'))
    },
    coinbaseCdp: coinbaseCdpDoctor(),
    chainstack: {
      configured: chainstackMcpConfigured()
    }
  };
}

export async function novaCryptoChainDoctor() {
  const candidates = [];
  const configured = env('NOVA_SEPOLIA_RPC_URL') || env('SEPOLIA_RPC_URL');
  if (configured) candidates.push({ provider: 'configured', url: configured });
  if (env('NOVA_ALCHEMY_API_KEY') || env('ALCHEMY_API_KEY')) {
    candidates.push({ provider: 'alchemy', url: alchemySepoliaRpcUrl() });
  } else {
    candidates.push({ provider: 'alchemy-public', url: alchemySepoliaRpcUrl() });
  }
  candidates.push(
    { provider: 'sepolia-public-rpc', url: 'https://rpc.sepolia.org' },
    { provider: 'publicnode', url: 'https://ethereum-sepolia.publicnode.com' }
  );

  const errors = [];
  for (const candidate of candidates) {
    try {
      const response = await fetch(candidate.url, {
        method: 'POST',
        headers: { accept: 'application/json', 'content-type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'eth_chainId',
          params: []
        }),
        signal: AbortSignal.timeout(12000)
      });
      const body = await response.text();
      if (!response.ok) {
        throw new Error('HTTP ' + response.status + (body ? ': ' + body.slice(0, 300) : ''));
      }
      const payload = JSON.parse(body);
      if (payload?.error) throw new Error(payload.error.message || 'RPC error');
      const chainId = Number.parseInt(String(payload.result), 16);
      if (chainId !== SEPOLIA_CHAIN_ID) throw new Error('unexpected chain ID ' + chainId);

      const blockResponse = await fetch(candidate.url, {
        method: 'POST',
        headers: { accept: 'application/json', 'content-type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'eth_blockNumber',
          params: []
        }),
        signal: AbortSignal.timeout(12000)
      });
      const blockBody = await blockResponse.text();
      if (!blockResponse.ok) throw new Error('block HTTP ' + blockResponse.status);
      const blockPayload = JSON.parse(blockBody);
      if (blockPayload?.error) throw new Error(blockPayload.error.message || 'block RPC error');
      const blockNumber = Number.parseInt(String(blockPayload.result), 16);

      return { chainId, blockNumber, network: 'ethereum-sepolia', provider: candidate.provider };
    } catch (error) {
      errors.push({ provider: candidate.provider, error: String(error.message || error) });
    }
  }

  throw new Error('No read-only Sepolia RPC succeeded: ' + JSON.stringify(errors));
}

export async function novaCryptoBalance(address) {
  assertAddress(address);
  return await alchemySepoliaBalance(address);
}

export async function novaCryptoReceipt(hash) {
  return await alchemySepoliaTransactionReceipt(hash);
}

export async function requestSepoliaEth(address, { provider = 'auto' } = {}) {
  assertAddress(address);
  if (provider === 'coinbase') return await coinbaseCdpRequestSepoliaEth(address);
  if (provider === 'chainstack') return await chainstackMcpRequestSepoliaEth(address);

  const errors = [];
  if (coinbaseCdpConfigured()) {
    try {
      return await coinbaseCdpRequestSepoliaEth(address);
    } catch (error) {
      errors.push({ provider: 'coinbase', error: String(error.message || error) });
    }
  }

  if (chainstackMcpConfigured()) {
    try {
      return await chainstackMcpRequestSepoliaEth(address);
    } catch (error) {
      errors.push({ provider: 'chainstack', error: String(error.message || error) });
    }
  }

  const detail = errors.length ? JSON.stringify(errors) : 'no authorized funding provider is configured';
  throw new Error('No authorized Sepolia funding path succeeded: ' + detail);
}

export async function requestAndConfirmSepoliaEth(
  address,
  {
    provider = 'auto',
    minBalanceWei = 1000000000000000n,
    pollMs = 5000,
    timeoutMs = 120000,
    maxCdpClaims = DEFAULT_MAX_CDP_CLAIMS,
    claimTimeoutMs = 30000
  } = {}
) {
  assertAddress(address);
  if (minBalanceWei < 0n) throw new Error('minBalanceWei cannot be negative');
  if (!Number.isInteger(maxCdpClaims) || maxCdpClaims < 1 || maxCdpClaims > 100) {
    throw new Error('maxCdpClaims must be an integer between 1 and 100');
  }
  if (!Number.isInteger(claimTimeoutMs) || claimTimeoutMs < 1000 || claimTimeoutMs > timeoutMs) {
    throw new Error('claimTimeoutMs must be an integer between 1000 and timeoutMs');
  }

  const providers = provider === 'auto' ? ['coinbase', 'chainstack'] : [provider];
  const errors = [];
  let before = BigInt(await novaCryptoBalance(address));

  if (before >= minBalanceWei) {
    return {
      fundingProvider: 'none',
      address,
      balanceBeforeWei: before.toString(),
      balanceAfterWei: before.toString(),
      funded: true,
      fundingClaims: 0,
      transactionHashes: []
    };
  }

  for (const candidate of providers) {
    if (candidate === 'coinbase' && !coinbaseCdpConfigured()) continue;
    if (candidate === 'chainstack' && !chainstackMcpConfigured()) continue;

    const deadline = Date.now() + timeoutMs;
    const remaining = minBalanceWei > before ? minBalanceWei - before : 0n;
    const requiredClaims = (remaining + COINBASE_ETH_PER_CLAIM_WEI - 1n) / COINBASE_ETH_PER_CLAIM_WEI;
    const maxClaims = candidate === 'coinbase'
      ? Math.min(maxCdpClaims, Number(requiredClaims + 2n))
      : 1;
    const transactionHashes = [];
    let claims = 0;

    try {
      while (claims < maxClaims && Date.now() <= deadline) {
        const request = await requestSepoliaEth(address, { provider: candidate });
        claims += 1;
        if (request?.transactionHash) transactionHashes.push(request.transactionHash);

        const claimDeadline = Math.min(deadline, Date.now() + claimTimeoutMs);
        while (Date.now() <= claimDeadline) {
          const current = BigInt(await novaCryptoBalance(address));
          if (current >= minBalanceWei) {
            return {
              ...request,
              fundingProvider: candidate,
              balanceBeforeWei: before.toString(),
              balanceAfterWei: current.toString(),
              funded: true,
              fundingClaims: claims,
              transactionHashes
            };
          }

          if (current > before) before = current;
          await new Promise((resolve) => setTimeout(resolve, pollMs));
        }
      }

      const after = BigInt(await novaCryptoBalance(address));
      errors.push({
        provider: candidate,
        claims,
        transactionHashes,
        error: `balance target not reached (before=${before} after=${after} target=${minBalanceWei})`
      });
      before = after;
    } catch (error) {
      errors.push({
        provider: candidate,
        claims,
        transactionHashes,
        error: String(error.message || error)
      });
    }
  }

  throw new Error('No authorized Sepolia funding provider reached the required balance: ' + JSON.stringify(errors));
}

export const COINBASE_SEPOLIA_NETWORK = COINBASE_CDP_SEPOLIA;
