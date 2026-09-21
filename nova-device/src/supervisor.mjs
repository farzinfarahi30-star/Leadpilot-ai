import {spawn} from 'node:child_process';
import {promises as fs} from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const ROOT=path.resolve(new URL('..',import.meta.url).pathname,'..');
const CONFIG=path.resolve(process.env.NOVA_DEVICE_CONFIG_DIR||path.join(ROOT,'.nova-device'));
const STATE=path.join(CONFIG,'supervisor.json');
const LOG=path.join(CONFIG,'supervisor.log');
const RESTART_MS=Math.max(2000,Number(process.env.NOVA_SUPERVISOR_RESTART_MS||5000));
const CHECK_MS=Math.max(2000,Number(process.env.NOVA_SUPERVISOR_CHECK_MS||10000));
const SUPERVISE_RUNTIME=process.env.NOVA_SUPERVISE_RUNTIME!=='false';
const SUPERVISE_DC=process.env.NOVA_SUPERVISE_DESKTOP_COMMANDER!=='false';
const REPO_ROOT=path.resolve(process.env.NOVA_PROJECT_ROOT||path.join(ROOT,'..'));

const children=new Map();
let stopping=false;

async function ensureDir(){await fs.mkdir(CONFIG,{recursive:true});}
async function log(event,data={}){
  const line=JSON.stringify({ts:new Date().toISOString(),event,...data})+'\n';
  process.stdout.write(line);
  try{await ensureDir();await fs.appendFile(LOG,line,'utf8');}catch{}
}
async function writeState(extra={}){
  const services={};
  for(const [name,s] of children){
    services[name]={pid:s.child.pid,status:s.status,restarts:s.restarts,startedAt:s.startedAt,lastExit:s.lastExit??null,lastError:s.lastError??null};
  }
  await ensureDir();
  await fs.writeFile(STATE,JSON.stringify({
    supervisor:'nova-device',
    version:'1.0.0',
    pid:process.pid,
    projectRoot:REPO_ROOT,
    android:Boolean(process.env.ANDROID_ROOT||process.env.TERMUX_VERSION),
    termux:Boolean(process.env.TERMUX_VERSION||process.env.PREFIX?.includes('/com.termux/')),
    uptimeMs:Math.round(process.uptime()*1000),
    services,
    updatedAt:new Date().toISOString(),
    ...extra
  },null,2));
}
function managed(name,command,args,cwd=REPO_ROOT,env={}){
  if(children.has(name)) return;
  const state={command,args,status:'starting',restarts:0,startedAt:new Date().toISOString(),lastExit:null,lastError:null,child:null,restartTimer:null};
  children.set(name,state);
  const launch=()=>{
    if(stopping)return;
    state.status='starting';
    state.startedAt=new Date().toISOString();
    state.lastError=null;
    state.child=spawn(command,args,{cwd,env:{...process.env,...env},stdio:['ignore','pipe','pipe'],detached:false});
    state.status='running';
    state.restarts++;
    state.child.stdout?.on('data',d=>process.stdout.write(String(d)));
    state.child.stderr?.on('data',d=>process.stderr.write(String(d)));
    state.child.on('error',error=>{state.lastError=String(error);log('service_error',{name,error:String(error)}).catch(()=>{});});
    state.child.on('exit',(code,signal)=>{
      state.status='stopped';
      state.lastExit={code,signal,at:new Date().toISOString()};
      state.child=null;
      log('service_exit',{name,code,signal,restart:!stopping}).catch(()=>{});
      if(!stopping){
        clearTimeout(state.restartTimer);
        state.restartTimer=setTimeout(launch,RESTART_MS);
      }
    });
    log('service_started',{name,pid:state.child.pid,command,args,restart:state.restarts-1}).catch(()=>{});
  };
  launch();
}
function stopAll(){
  stopping=true;
  for(const [name,state] of children){
    if(state.restartTimer)clearTimeout(state.restartTimer);
    if(state.child&&!state.child.killed){
      try{state.child.kill('SIGTERM');}catch{}
    }
    log('service_stop_requested',{name}).catch(()=>{});
  }
}
async function wakeLock(){
  if(!process.env.TERMUX_VERSION&&!process.env.PREFIX?.includes('/com.termux/'))return;
  const child=spawn('termux-wake-lock',[],{stdio:'ignore'});
  child.on('error',()=>{});
}
async function boot(){
  await ensureDir();
  await wakeLock();
  await log('supervisor_started',{pid:process.pid,projectRoot:REPO_ROOT,superviseRuntime:SUPERVISE_RUNTIME,superviseDesktopCommander:SUPERVISE_DC});
  if(SUPERVISE_RUNTIME){
    managed('nova-runtime',process.execPath,['nova-runtime/src/worker.mjs'],REPO_ROOT,{
      NOVA_LOCAL_DAEMON:'true',
      NOVA_DEVICE_CONTROL:'true',
      NOVA_DEVICE_ALLOWED_ROOTS:process.env.NOVA_DEVICE_ALLOWED_ROOTS||`${process.env.HOME||REPO_ROOT}:${REPO_ROOT}`,
      NOVA_DEVICE_AUTO_PROVISION:process.env.NOVA_DEVICE_AUTO_PROVISION||'true',
      NOVA_TERMUX_PROFILE:process.env.NOVA_TERMUX_PROFILE||'developer'
    });
  }
  if(SUPERVISE_DC){
    managed('desktop-commander','npx',['-y','@wonderwhy-er/desktop-commander@latest','remote'],REPO_ROOT,{
      npm_config_yes:'true'
    });
  }
  const interval=setInterval(()=>writeState().catch(()=>{}),CHECK_MS);
  process.on('SIGINT',()=>{clearInterval(interval);stopAll();});
  process.on('SIGTERM',()=>{clearInterval(interval);stopAll();});
  process.on('exit',()=>{try{clearInterval(interval);}catch{}});
  await writeState();
  while(!stopping){
    await new Promise(r=>setTimeout(r,CHECK_MS));
    await writeState();
  }
}
await boot();
