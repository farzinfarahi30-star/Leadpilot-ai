import readline from 'node:readline';
import {TOOL_REGISTRY} from './core.mjs';

const rl=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
async function callTool(id,tool,args){
  try{
    if(!TOOL_REGISTRY[tool])throw new Error('Unknown Nova device tool: '+tool);
    const result=await TOOL_REGISTRY[tool](...(Array.isArray(args)?args:[]));
    return {jsonrpc:'2.0',id,result};
  }catch(error){
    return {jsonrpc:'2.0',id,error:{code:-32000,message:String(error.message||error)}};
  }
}
for await(const line of rl){
  if(!line.trim())continue;
  let req;try{req=JSON.parse(line)}catch{process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Invalid JSON'}})+'\n');continue}
  if(req.method==='tools/list'){
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:req.id,result:{tools:Object.keys(TOOL_REGISTRY)}})+'\n');continue;
  }
  if(req.method==='tools/call'){
    process.stdout.write(JSON.stringify(await callTool(req.id,req.params?.name,req.params?.arguments))+'\n');continue;
  }
  process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:req.id,error:{code:-32601,message:'Method not found'}})+'\n');
}
