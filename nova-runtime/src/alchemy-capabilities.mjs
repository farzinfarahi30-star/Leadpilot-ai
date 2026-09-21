import process from 'node:process';

const ALCHEMY_API = 'https://api.g.alchemy.com';
const ALCHEMY_SEPOLIA_RPC = 'https://eth-sepolia.g.alchemy.com/v2/';
const SEPOLIA_CHAIN_ID = 11155111;

function apiKey(explicit) {
  return String(explicit || process.env.NOVA_ALCHEMY_API_KEY || process.env.ALCHEMY_API_KEY || '').trim();
}

function requireApiKey(explicit) {
  const key = apiKey(explicit);
  if (!key) throw new Error('Alchemy API key is required for this capability.');
  return key;
}

function encode(value) {
  return encodeURIComponent(String(value));
}

function queryString(query = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query || {})) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const item of value) params.append(key, String(item));
    } else {
      params.set(key, String(value));
    }
  }
  const out = params.toString();
  return out ? '?' + out : '';
}

async function readResponse(response, label) {
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`${label} ${response.status}: ${body.slice(0, 1200)}`);
  }
  try {
    return JSON.parse(body);
  } catch {
    return body;
  }
}

/**
 * Generic Alchemy Data/Platform API gateway.
 * Host is fixed to api.g.alchemy.com so Nova cannot be redirected to an
 * arbitrary third-party endpoint by an untrusted path.
 */
export async function alchemyPlatformRequest(path, {
  method = 'GET',
  query = {},
  body,
  apiKey: explicitApiKey
} = {}) {
  if (!String(path || '').startsWith('/')) throw new Error('Alchemy path must start with /.');
  if (path.includes('://') || path.includes('..')) throw new Error('Unsafe Alchemy path.');
  const key = requireApiKey(explicitApiKey);
  const url = `${ALCHEMY_API}${path}`.replaceAll('{apiKey}', encode(key)) + queryString(query);
  const headers = { accept: 'application/json' };
  if (body !== undefined) headers['content-type'] = 'application/json';
  const response = await fetch(url, {
    method: String(method).toUpperCase(),
    headers,
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  return await readResponse(response, 'Alchemy API');
}

export async function alchemyPortfolioTokensByAddress(addresses, options = {}) {
  return await alchemyPlatformRequest('/data/v1/{apiKey}/assets/tokens/by-address', {
    method: 'POST',
    body: {
      addresses,
      withMetadata: options.withMetadata ?? true,
      withPrices: options.withPrices ?? true,
      includeNativeTokens: options.includeNativeTokens ?? true,
      includeErc20Tokens: options.includeErc20Tokens ?? true,
      includeBlockMetadata: options.includeBlockMetadata ?? false
    },
    apiKey: options.apiKey
  });
}

export async function alchemyPricesBySymbol(symbols, options = {}) {
  return await alchemyPlatformRequest('/prices/v1/{apiKey}/tokens/by-symbol', {
    method: 'GET',
    query: { symbols },
    apiKey: options.apiKey
  });
}

export async function alchemyPricesByAddress(addresses, options = {}) {
  return await alchemyPlatformRequest('/prices/v1/{apiKey}/tokens/by-address', {
    method: 'GET',
    query: { addresses },
    apiKey: options.apiKey
  });
}

export async function alchemyPortfolioHistory(addresses, options = {}) {
  return await alchemyPlatformRequest('/data/v1/{apiKey}/assets/history/by-address', {
    method: 'POST',
    body: { addresses },
    apiKey: options.apiKey
  });
}

export async function alchemyNftRequest(network, endpoint, query = {}, options = {}) {
  const key = requireApiKey(options.apiKey);
  const host = `https://${encode(network)}.g.alchemy.com`;
  const safeEndpoint = String(endpoint || '').replace(/^\/+/, '');
  if (!/^[A-Za-z0-9_/-]+$/.test(safeEndpoint)) throw new Error('Unsafe Alchemy NFT endpoint.');
  const url = `${host}/nft/v3/${encode(key)}/${safeEndpoint}${queryString(query)}`;
  const response = await fetch(url, { headers: { accept: 'application/json' } });
  return await readResponse(response, 'Alchemy NFT API');
}

export async function alchemyTransferHistory(network, params = {}, options = {}) {
  const key = requireApiKey(options.apiKey);
  const rpcUrl = `https://${encode(network)}.g.alchemy.com/v2/${encode(key)}`;
  return await alchemyRpcGateway(rpcUrl, 'alchemy_getAssetTransfers', [params]);
}

export async function alchemyRpcGateway(rpcUrl, method, params = []) {
  const url = String(rpcUrl || '');
  if (!/^https:\/\/[A-Za-z0-9.-]+\.g\.alchemy\.com\/v2\/[^/]+$/.test(url)) {
    throw new Error('RPC URL must be an Alchemy v2 endpoint.');
  }
  if (String(method || '').toLowerCase().startsWith('eth_send')) {
    throw new Error('State-changing eth_send* RPC calls must use Nova signed-transaction controls.');
  }
  if (!Array.isArray(params)) throw new Error('RPC params must be an array.');
  const response = await fetch(url, {
    method: 'POST',
    headers: { accept: 'application/json', 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method, params })
  });
  const payload = await readResponse(response, 'Alchemy RPC');
  if (payload?.error) throw new Error(`Alchemy RPC ${payload.error.code ?? 'error'}: ${payload.error.message || 'request failed'}`);
  return payload?.result;
}

export async function alchemyBundlerRpc(method, params = [], options = {}) {
  const key = requireApiKey(options.apiKey);
  const network = options.network || 'eth-sepolia';
  const rpcUrl = `https://${encode(network)}.g.alchemy.com/v2/${encode(key)}`;
  return await alchemyRpcGateway(rpcUrl, method, params);
}

export const NOVA_ALCHEMY_CAPABILITIES = Object.freeze({
  chainApis: ['jsonRpc', 'webSockets', 'traceApi', 'debugApi'],
  dataApis: ['portfolio', 'token', 'transfers', 'prices', 'nft'],
  notifications: ['webhooks'],
  simulation: { supported: true, deprecationDate: '2026-09-30' },
  accountAbstraction: ['bundler', 'gasManager', 'accountKit'],
  sepolia: { chainId: SEPOLIA_CHAIN_ID, rpc: ALCHEMY_SEPOLIA_RPC },
  platformGateway: true
});

export function alchemyCapabilityManifest() {
  return NOVA_ALCHEMY_CAPABILITIES;
}
