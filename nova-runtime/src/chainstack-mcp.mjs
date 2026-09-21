import process from 'node:process';

const ENDPOINT = process.env.CHAINSTACK_MCP_URL || 'https://mcp.chainstack.com/mcp';
const API_KEY = String(process.env.CHAINSTACK_API_KEY || '').trim();
const PROTOCOL = process.env.CHAINSTACK_MCP_PROTOCOL || '2025-06-18';
const CLIENT_NAME = 'Nova AI';
const CLIENT_VERSION = '1.0.0';

let sessionId = null;
let negotiatedProtocol = PROTOCOL;
let initPromise = null;

function authHeaders(extra = {}) {
  return {
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
    ...(API_KEY ? { Authorization: 'Bearer ' + API_KEY } : {}),
    ...extra
  };
}

function parseSseBody(body) {
  const events = String(body).split(/\n\n+/).map((x) => x.trim()).filter(Boolean);
  let last = null;
  for (const event of events) {
    const data = event.split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim())
      .join('\n');
    if (!data || data === '[DONE]') continue;
    try { last = JSON.parse(data); } catch {}
  }
  if (last) return last;
  try { return JSON.parse(String(body).trim()); }
  catch { return { raw: String(body).trim() }; }
}

function withProtocolMeta(method, params) {
  if (method === 'initialize' || method === 'notifications/initialized') return params || {};
  const next = { ...(params || {}) };
  next._meta = {
    ...(next._meta || {}),
    'io.modelcontextprotocol/protocolVersion': negotiatedProtocol,
    'io.modelcontextprotocol/clientInfo': { name: CLIENT_NAME, version: CLIENT_VERSION },
    'io.modelcontextprotocol/clientCapabilities': {}
  };
  return next;
}

async function rpc(method, params = {}, id = 1) {
  const headers = authHeaders({
    'MCP-Protocol-Version': negotiatedProtocol,
    'Mcp-Method': method
  });
  if (sessionId) headers['Mcp-Session-Id'] = sessionId;

  const response = await fetch(ENDPOINT, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      jsonrpc: '2.0',
      id,
      method,
      params: withProtocolMeta(method, params)
    })
  });

  const body = await response.text();
  const returnedSession = response.headers.get('mcp-session-id');
  if (returnedSession) sessionId = returnedSession;

  if (!response.ok) {
    throw new Error(`Chainstack MCP HTTP ${response.status}: ${body.slice(0, 1200)}`);
  }
  return parseSseBody(body);
}

async function ensureInitialized() {
  if (initPromise) return initPromise;

  initPromise = (async () => {
    const result = await rpc('initialize', {
      protocolVersion: PROTOCOL,
      capabilities: {},
      clientInfo: { name: CLIENT_NAME, version: CLIENT_VERSION }
    }, 0);

    const serverProtocol = result?.result?.protocolVersion;
    if (serverProtocol) negotiatedProtocol = serverProtocol;

    try { await rpc('notifications/initialized', {}, undefined); } catch {}
    return result;
  })().catch((error) => {
    initPromise = null;
    throw error;
  });

  return initPromise;
}

export function chainstackMcpConfigured() {
  return Boolean(API_KEY);
}

export async function chainstackMcpListTools() {
  await ensureInitialized();
  const tools = [];
  let cursor = null;
  do {
    const params = cursor ? { cursor } : {};
    const result = await rpc('tools/list', params, 1);
    tools.push(...(result?.result?.tools || []));
    cursor = result?.result?.nextCursor || null;
  } while (cursor);

  return {
    endpoint: ENDPOINT,
    protocolVersion: negotiatedProtocol,
    sessionId,
    tools,
    toolCount: tools.length
  };
}

export async function chainstackMcpCall(name, args = {}, id = 2) {
  if (!name) throw new Error('Chainstack MCP tool name is required');
  await ensureInitialized();
  const result = await rpc('tools/call', { name, arguments: args }, id);
  if (result?.error) {
    throw new Error(`Chainstack MCP ${result.error.code ?? 'error'}: ${result.error.message || 'tool call failed'}`);
  }
  return result;
}

export async function chainstackMcpRequestSepoliaEth(address) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(String(address || ''))) {
    throw new Error('Ethereum recipient address is invalid');
  }
  if (!chainstackMcpConfigured()) {
    throw new Error('Chainstack API key is not configured');
  }

  const result = await chainstackMcpCall('request_testnet_funds', {
    network: 'sepolia',
    address
  });

  return {
    provider: 'chainstack',
    network: 'sepolia',
    chainId: 11155111,
    address,
    result
  };
}
