import process from 'node:process';
import {
  alchemySepoliaBalance,
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
  const [chainId, blockNumber] = await Promise.all([
    alchemySepoliaChainId(),
    alchemySepoliaBlockNumber()
  ]);
  if (chainId !== SEPOLIA_CHAIN_ID) {
    throw new Error(`Sepolia chain ID mismatch: expected ${SEPOLIA_CHAIN_ID}, received ${chainId}`);
  }
  return { chainId, blockNumber, network: 'ethereum-sepolia' };
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
  { provider = 'auto', minBalanceWei = 1n, pollMs = 5000, timeoutMs = 120000 } = {}
) {
  assertAddress(address);
  const before = BigInt(await novaCryptoBalance(address));
  const request = await requestSepoliaEth(address, { provider });
  const deadline = Date.now() + timeoutMs;

  while (Date.now() <= deadline) {
    const current = BigInt(await novaCryptoBalance(address));
    if (current >= minBalanceWei && current > before) {
      return {
        ...request,
        balanceBeforeWei: before.toString(),
        balanceAfterWei: current.toString(),
        funded: true
      };
    }
    await new Promise((resolve) => setTimeout(resolve, pollMs));
  }

  const finalBalance = BigInt(await novaCryptoBalance(address));
  throw new Error(
    `Sepolia funding request returned but balance did not increase before timeout; ` +
    `before=${before} after=${finalBalance} request=${JSON.stringify(request)}`
  );
}

export const COINBASE_SEPOLIA_NETWORK = COINBASE_CDP_SEPOLIA;
