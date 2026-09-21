import process from 'node:process';

const SEPOLIA_CHAIN_ID = 11155111;
const DEFAULT_PUBLIC_RPC = 'https://ethereum-sepolia-rpc.publicnode.com';
const ALCHEMY_SEPOLIA_RPC = 'https://eth-sepolia.g.alchemy.com/v2/';
const ALCHEMY_SEPOLIA_WS = 'wss://eth-sepolia.g.alchemy.com/v2/';
const ALCHEMY_SEPOLIA_FAUCET = 'https://www.alchemy.com/faucets/ethereum-sepolia';

function env(name) {
  return String(process.env[name] || '').trim();
}

export function alchemySepoliaRpcUrl(apiKey = env('NOVA_ALCHEMY_API_KEY') || env('ALCHEMY_API_KEY')) {
  return apiKey ? ALCHEMY_SEPOLIA_RPC + encodeURIComponent(apiKey) : DEFAULT_PUBLIC_RPC;
}

export function alchemySepoliaWsUrl(apiKey = env('NOVA_ALCHEMY_API_KEY') || env('ALCHEMY_API_KEY')) {
  if (!apiKey) return null;
  return ALCHEMY_SEPOLIA_WS + encodeURIComponent(apiKey);
}

export function alchemySepoliaResources() {
  return {
    network: 'ethereum-sepolia',
    chainId: SEPOLIA_CHAIN_ID,
    rpcUrlConfigured: Boolean(env('NOVA_ALCHEMY_API_KEY') || env('ALCHEMY_API_KEY')),
    rpcUrl: alchemySepoliaRpcUrl(),
    wsUrl: alchemySepoliaWsUrl(),
    faucetUrl: ALCHEMY_SEPOLIA_FAUCET
  };
}

const BLOCKED_WRITE_METHODS = new Set([
  'eth_sendRawTransaction',
  'eth_sendTransaction',
  'personal_sign',
  'eth_sign',
  'eth_signTransaction',
  'wallet_addEthereumChain',
  'wallet_switchEthereumChain'
]);

export async function alchemySepoliaRpc(method, params = [], { apiKey } = {}) {
  const rpcMethod = String(method || '').trim();
  if (!rpcMethod) throw new Error('Alchemy RPC method is required');
  if (BLOCKED_WRITE_METHODS.has(rpcMethod)) {
    throw new Error(`Blocked state-changing wallet RPC method: ${rpcMethod}`);
  }
  if (!Array.isArray(params)) throw new Error('Alchemy RPC params must be an array');

  const response = await fetch(alchemySepoliaRpcUrl(apiKey), {
    method: 'POST',
    headers: {
      accept: 'application/json',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method: rpcMethod,
      params
    })
  });

  const body = await response.text();
  if (!response.ok) {
    throw new Error(`Alchemy RPC ${response.status}: ${body.slice(0, 500)}`);
  }

  let payload;
  try {
    payload = JSON.parse(body);
  } catch {
    throw new Error('Alchemy RPC returned invalid JSON');
  }

  if (payload?.error) {
    throw new Error(`Alchemy RPC ${payload.error.code ?? 'error'}: ${payload.error.message || 'request failed'}`);
  }

  return payload?.result;
}

export async function alchemySepoliaChainId() {
  const hex = await alchemySepoliaRpc('eth_chainId');
  return Number.parseInt(String(hex), 16);
}

export async function alchemySepoliaBlockNumber() {
  const hex = await alchemySepoliaRpc('eth_blockNumber');
  return Number.parseInt(String(hex), 16);
}

export async function alchemySepoliaBalance(address, blockTag = 'latest') {
  if (!/^0x[0-9a-fA-F]{40}$/.test(String(address || ''))) {
    throw new Error('Ethereum address must be a valid 20-byte hex address');
  }
  return await alchemySepoliaRpc('eth_getBalance', [address, blockTag]);
}

export async function alchemySepoliaTransactionReceipt(hash) {
  if (!/^0x[0-9a-fA-F]{64}$/.test(String(hash || ''))) {
    throw new Error('Transaction hash must be a valid 32-byte hex value');
  }
  return await alchemySepoliaRpc('eth_getTransactionReceipt', [hash]);
}
