import process from 'node:process';
import {execFile} from 'node:child_process';
import {promises as fs} from 'node:fs';
import path from 'node:path';

export const NOVA_DEVICE_BRIDGE_VERSION='1.0.0';
const DEFAULT_TIMEOUT_MS=120_000;
const MAX_OUTPUT_BYTES=2_000_000;
const SAFE_COMMANDS=new Set([
  'bash','sh','zsh','node','npm','npx','pnpm','yarn','python','python3',
  'pip','pip3','git','curl','wget','grep','rg','find','ls','cat','pwd',
  'whoami','uname','which','termux-battery-status','termux-info'
]);

function android(){
  return process.platform==='android' ||
    Boolean(process.env.TERMUX_VERSION || process.env.PREFIX?.includes('/com.termux/'));
}

function resolveExecutable(command){
  const first=String(command).trim().split(/\\s+/,1)[0];
  return first.includes('/') ? path.basename(first) : first;
}

function assertCommandAllowed(command){
  const executable=resolveExecutable(command);
  if(SAFE_COMMANDS.has(executable)) return;
  if(process.env.NOVA_DEVICE_ALLOW_DANGEROUS==='true') return;
  throw new Error('Device command blocked: '+executable+'. Set NOVA_DEVICE_ALLOW_DANGEROUS=true only for explicitly approved operations.');
}

export function deviceInfo(){
  return {
    bridgeVersion:NOVA_DEVICE_BRIDGE_VERSION,
    platform:process.platform,
    arch:process.arch,
    isAndroid:android(),
    termux:Boolean(process.env.TERMUX_VERSION),
    cwd:process.cwd(),
    node:process.version,
    desktopCommanderMode:process.env.NOVA_DESKTOP_COMMANDER_MODE || 'local-agent'
  };
}

export async function runCommand(command,{cwd=process.cwd(),timeoutMs=DEFAULT_TIMEOUT_MS,env={}}={}){
  if(!command || typeof command!=='string') throw new Error('command must be a non-empty string');
  assertCommandAllowed(command);
  const [executable,...args]=command.trim().split(/\\s+/);
  return await new Promise((resolve,reject)=>{
    execFile(executable,args,{
      cwd,
      env:{...process.env,...env},
      timeout:Math.max(1000,Math.min(timeoutMs,600_000)),
      maxBuffer:MAX_OUTPUT_BYTES
    },(error,stdout,stderr)=>{
      const result={ok:!error,code:error?.code ?? 0,signal:error?.signal ?? null,stdout:String(stdout||''),stderr:String(stderr||'')};
      if(error) reject(Object.assign(new Error(result.stderr || error.message),{result}));
      else resolve(result);
    });
  });
}

function assertPathAllowed(target){
  const absolute=path.resolve(target);
  const roots=(process.env.NOVA_DEVICE_ALLOWED_ROOTS || process.cwd())
    .split(path.delimiter).filter(Boolean).map(p=>path.resolve(p));
  if(!roots.some(root=>absolute===root || absolute.startsWith(root+path.sep))){
    throw new Error('Path outside Nova device allowlist: '+absolute);
  }
  return absolute;
}

export async function readFile(target){
  const absolute=assertPathAllowed(target);
  return {path:absolute,content:await fs.readFile(absolute,'utf8')};
}

export async function writeFile(target,content){
  const absolute=assertPathAllowed(target);
  await fs.mkdir(path.dirname(absolute),{recursive:true});
  await fs.writeFile(absolute,String(content),'utf8');
  return {path:absolute,bytes:Buffer.byteLength(String(content),'utf8')};
}

export async function desktopCommanderDoctor(){
  const info=deviceInfo();
  let npx=null;
  try { npx=await runCommand('npx --version',{timeoutMs:15_000}); }
  catch(error){ npx={ok:false,error:String(error)}; }
  return {
    ...info,
    desktopCommander:{
      compatible:true,
      package:'@wonderwhy-er/desktop-commander',
      remoteAgentCommand:'npx @wonderwhy-er/desktop-commander@latest remote',
      npxAvailable:Boolean(npx?.ok),
      note:'Nova uses the public Desktop Commander capability through its documented agent/protocol; proprietary hosted implementation is not copied.'
    }
  };
}

export async function startDesktopCommanderRemote(){
  return runCommand('npx @wonderwhy-er/desktop-commander@latest remote',{timeoutMs:10_000});
}
