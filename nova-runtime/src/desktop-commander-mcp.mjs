const ENDPOINT=process.env.DESKTOP_COMMANDER_MCP_URL||'https://mcp.desktopcommander.app/mcp';
const TOKEN=process.env.DESKTOP_COMMANDER_OAUTH_TOKEN||'';

function authHeaders(){
  if(!TOKEN) throw new Error('DESKTOP_COMMANDER_OAUTH_TOKEN is not configured. Nova cannot impersonate or bypass Desktop Commander OAuth.');
  return {Authorization:`Bearer ${TOKEN}`,'Content-Type':'application/json',Accept:'application/json, text/event-stream'};
}

async function rpc(method,params={},id=1){
  const r=await fetch(ENDPOINT,{method:'POST',headers:authHeaders(),body:JSON.stringify({jsonrpc:'2.0',id,method,params})});
  const text=await r.text();
  if(!r.ok) throw new Error(`Desktop Commander MCP HTTP ${r.status}: ${text.slice(0,500)}`);
  try{return JSON.parse(text)}catch{return {raw:text}};
}

export async function desktopCommanderListTools(){
  return rpc('tools/list',{},1);
}

export async function desktopCommanderCall(name,args={},id=2){
  return rpc('tools/call',{name,arguments:args},id);
}

export async function desktopCommanderHealth(){
  const result=await desktopCommanderListTools();
  return {connected:true,endpoint:ENDPOINT,tools:result?.result?.tools||[]};
}

export function desktopCommanderConfigured(){
  return Boolean(TOKEN);
}
