import process from 'node:process';
import { CdpClient } from '@coinbase/cdp-sdk';

export const COINBASE_CDP_SEPOLIA = Object.freeze({
  provider: 'coinbase-developer-platform',
  network: 'ethereum-sepolia',
  chainId: 11155111,
  faucetAsset: 'eth'
});

function env(name) {
  return String(process.env[name] || '').trim();
}

export function coinbaseCdpConfigured() {
  return Boolean(
    env('CDP_API_KEY_ID') &&
    env('CDP_API_KEY_SECRET') &&
    env('CDP_WALLET_SECRET')
  );
}

export function coinbaseCdpDoctor() {
  return {
    configured: coinbaseCdpConfigured(),
    provider: COINBASE_CDP_SEPOLIA.provider,
    network: COINBASE_CDP_SEPOLIA.network,
    chainId: COINBASE_CDP_SEPOLIA.chainId,
    missing: [
      !env('CDP_API_KEY_ID') ? 'CDP_API_KEY_ID' : null,
      !env('CDP_API_KEY_SECRET') ? 'CDP_API_KEY_SECRET' : null,
      !env('CDP_WALLET_SECRET') ? 'CDP_WALLET_SECRET' : null
    ].filter(Boolean)
  };
}

function assertAddress(address) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(String(address || ''))) {
    throw new Error('Ethereum recipient address is invalid');
  }
}

export async function coinbaseCdpRequestSepoliaEth(address) {
  assertAddress(address);
  if (!coinbaseCdpConfigured()) {
    throw new Error('Coinbase CDP credentials are not configured');
  }

  const cdp = new CdpClient();
  try {
    const response = await cdp.evm.requestFaucet({
      address,
      network: COINBASE_CDP_SEPOLIA.network,
      token: COINBASE_CDP_SEPOLIA.faucetAsset
    });

    return {
      provider: COINBASE_CDP_SEPOLIA.provider,
      network: COINBASE_CDP_SEPOLIA.network,
      chainId: COINBASE_CDP_SEPOLIA.chainId,
      address,
      transactionHash: response.transactionHash
    };
  } finally {
    await cdp.close();
  }
}
