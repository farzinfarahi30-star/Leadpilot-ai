import process from 'node:process';

const ENDPOINT=process.env.DESKTOP_COMMANDER_MCP_URL||'https://mcp.desktopcommander.app/mcp';
const TOKEN=process.env.DESKTOP_COMMANDER_OAUTH_TOKEN||'';
const PROTOCOL=process.env.DESKTOP_COMMANDER_MCP_PROTOCOL||'2025-06-18';
const CLIENT_NAME='Nova AI';
const CLIENT_VERSION='1.0.0';
let sessionId=null;
let negotiatedProtocol=PROTOCOL;
let initPromise=null;

function authHeaders(extra={}){
  if(!TOKEN) throw new Error('DESKTOP_COMMANDER_OAUTH_TOKEN is not configured. Nova cannot impersonate or bypass Desktop Commander OAuth.');
  return {
    Authorization:`Bearer ${TOKEN}`,
    'Content-Type':'application/json',
    Accept:'application/json, text/event-stream',
    ...extra
  };
}

function parseSseBody(body){
  const events=String(body).split(/\n\n+/).map(x=>x.trim()).filter(Boolean);
  let last=null;
  for(const event of events){
    const data=event.split('\n')
      .filter(line=>line.startsWith('data:'))
      .map(line=>line.slice(5).trim())
      .join('\n');
    if(!data || data==='[DONE]') continue;
    try{last=JSON.parse(data)}catch{}
  }
  if(last) return last;
  const trimmed=String(body).trim();
  try{return JSON.parse(trimmed)}catch{return {raw:trimmed}};
}

function withProtocolMeta(method,params){
  const next={...(params||{})};
  if(method!=='initialize' && method!=='notifications/initialized' && !next._meta){
    next._meta={
      'io.modelcontextprotocol/protocolVersion':negotiatedProtocol,
      'io.modelcontextprotocol/clientInfo':{name:CLIENT_NAME,version:CLIENT_VERSION},
      'io.modelcontextprotocol/clientCapabilities':{}
    };
  }
  return next;
}

async function rpc(method,params={},id=1,{headers={}}={}){
  const payload={jsonrpc:'2.0',id,method,params:withProtocolMeta(method,params)};
  if(sessionId) headers['Mcp-Session-Id']=sessionId;
  const r=await fetch(ENDPOINT,{
    method:'POST',
    headers:authHeaders({
      'MCP-Protocol-Version':negotiatedProtocol,
      'Mcp-Method':method,
      ...headers
    }),
    body:JSON.stringify(payload)
  });
  const body=await r.text();
  const returnedSession=r.headers.get('mcp-session-id');
  if(returnedSession) sessionId=returnedSession;
  if(!r.ok){
    throw new Error(`Desktop Commander MCP HTTP ${r.status}: ${body.slice(0,1000)}`);
  }
  return parseSseBody(body);
}

async function ensureInitialized(){
  if(!TOKEN) throw new Error('DESKTOP_COMMANDER_OAUTH_TOKEN is not configured.');
  if(initPromise) return initPromise;
  initPromise=(async()=>{
    const result=await rpc('initialize',{
      protocolVersion:PROTOCOL,
      capabilities:{},
      clientInfo:{name:CLIENT_NAME,version:CLIENT_VERSION},
      _meta:{
        'io.modelcontextprotocol/protocolVersion':PROTOCOL,
        'io.modelcontextprotocol/clientInfo':{name:CLIENT_NAME,version:CLIENT_VERSION},
        'io.modelcontextprotocol/clientCapabilities':{}
      }
    },0);
    const serverProtocol=result?.result?.protocolVersion;
    if(serverProtocol) negotiatedProtocol=serverProtocol;
    try{
      await rpc('notifications/initialized',{},undefined);
    }catch{}
    return result;
  })().catch(error=>{
    initPromise=null;
    throw error;
  });
  return initPromise;
}

export async function desktopCommanderListTools(){
  await ensureInitialized();
  const all=[];
  let cursor;
  do{
    const params={};
    if(cursor) params.cursor=cursor;
    const result=await rpc('tools/list',params,1);
    all.push(...(result?.result?.tools||[]));
    cursor=result?.result?.nextCursor||null;
  }while(cursor);
  return {
    jsonrpc:'2.0',
    result:{tools:all},
    protocolVersion:negotiatedProtocol,
    sessionId
  };
}

export async function desktopCommanderCall(name,args={},id=2){
  await ensureInitialized();
  if(!name || typeof name!=='string') throw new Error('Desktop Commander tool name is required.');
  return rpc('tools/call',{
    name,
    arguments:args
  },id,{headers:{'Mcp-Name':String(name)}});
}

export async function desktopCommanderHealth(){
  const listed=await desktopCommanderListTools();
  return {
    connected:true,
    endpoint:ENDPOINT,
    protocolVersion:listed.protocolVersion,
    sessionId:listed.sessionId,
    tools:listed.result?.tools||[],
    toolCount:(listed.result?.tools||[]).length
  };
}

export function desktopCommanderConfigured(){return Boolean(TOKEN);}

export async function executeDesktopCommanderTool(name,args={},id=2){
  if(!desktopCommanderConfigured()) throw new Error('Desktop Commander OAuth token is not configured.');
  return desktopCommanderCall(name,args,id);
}
