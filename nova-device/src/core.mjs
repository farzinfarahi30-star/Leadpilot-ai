import {spawn,execFile} from 'node:child_process';
import {promises as fs} from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {PDFDocument,StandardFonts,rgb} from 'pdf-lib';
import * as XLSX from 'xlsx';

const ROOTS=()=>((process.env.NOVA_DEVICE_ALLOWED_ROOTS||process.cwd()).split(path.delimiter).filter(Boolean).map(x=>path.resolve(x)));
const CONFIG_DIR=()=>path.resolve(process.env.NOVA_DEVICE_CONFIG_DIR||path.join(process.cwd(),'.nova-device'));
const LOG_FILE=()=>path.join(CONFIG_DIR(),'activity.jsonl');
const MAX_OUTPUT=2_000_000;
const sessions=new Map();
const searches=new Map();

function safePath(target){
  const absolute=path.resolve(String(target));
  if(!ROOTS().some(root=>absolute===root||absolute.startsWith(root+path.sep)))
    throw new Error('Path outside Nova device allowlist: '+absolute);
  return absolute;
}
async function record(event,data={}){
  await fs.mkdir(CONFIG_DIR(),{recursive:true});
  await fs.appendFile(LOG_FILE(),JSON.stringify({ts:new Date().toISOString(),event,...data})+'\n','utf8');
}
function firstArg(command){return String(command).trim().split(/\\s+/,1)[0]}
function assertCommand(command){
  const exe=path.basename(firstArg(command));
  const safe=new Set([
    'bash','sh','zsh','fish','node','npm','npx','pnpm','yarn','python','python3','pip','pip3',
    'git','curl','wget','ssh','scp','rsync','rg','grep','find','sed','awk','sort','uniq','head','tail',
    'cat','cp','mv','mkdir','rm','chmod','pwd','whoami','uname','which','tar','zip','unzip','make',
    'cmake','clang','clang++','rustc','cargo','go','ruby','perl','php','jq','ps','df','du','free',
    'termux-battery-status','termux-wifi-connectioninfo','termux-wifi-scaninfo','termux-clipboard-get',
    'termux-clipboard-set','termux-notification','termux-toast','termux-vibrate','termux-camera-photo',
    'termux-media-scan','termux-open','termux-open-url','termux-share','pkg','apt'
  ]);
  if(!safe.has(exe)&&process.env.NOVA_DEVICE_ALLOW_DANGEROUS!=='true')
    throw new Error('Command blocked by Nova device policy: '+exe);
}
async function execCommand(command,options={}){
  assertCommand(command);
  const [exe,...args]=String(command).trim().split(/\\s+/);
  return await new Promise((resolve,reject)=>{
    execFile(exe,args,{cwd:options.cwd||process.cwd(),env:{...process.env,...(options.env||{})},
      timeout:Math.min(600000,Math.max(1000,Number(options.timeoutMs||120000))),maxBuffer:MAX_OUTPUT},
      (error,stdout,stderr)=>{
        const result={ok:!error,code:error?.code??0,signal:error?.signal??null,stdout:String(stdout||''),stderr:String(stderr||'')};
        record('command_finished',{command:exe,ok:result.ok,code:result.code}).catch(()=>{});
        if(error) reject(Object.assign(new Error(result.stderr||error.message),{result})); else resolve(result);
      });
  });
}
export function deviceInfo(){
  return {platform:process.platform,arch:process.arch,node:process.version,hostname:os.hostname(),home:os.homedir(),
    cwd:process.cwd(),android:process.platform==='android'||Boolean(process.env.ANDROID_ROOT),
    termux:Boolean(process.env.TERMUX_VERSION||process.env.PREFIX?.includes('/com.termux/')),roots:ROOTS()};
}
export async function listDirectory(target='.'){
  const dir=safePath(target),entries=await fs.readdir(dir,{withFileTypes:true}),result=[];
  for(const e of entries){const p=path.join(dir,e.name);let s;try{s=await fs.stat(p)}catch{s=null}
    result.push({name:e.name,path:p,type:e.isDirectory()?'directory':e.isSymbolicLink()?'symlink':'file',size:s?.size??null,modifiedAt:s?.mtime?.toISOString()??null});
  }
  await record('list_directory',{path:dir,count:result.length});return result;
}
export async function readFile(target,encoding='utf8'){
  const p=safePath(target),content=await fs.readFile(p,encoding);await record('read_file',{path:p});return {path:p,content};
}
export async function readMultipleFiles(paths){
  const out=[];for(const p of paths){try{out.push({ok:true,...await readFile(p)})}catch(error){out.push({ok:false,path:p,error:String(error)})}}return out;
}
export async function getFileInfo(target){
  const p=safePath(target),s=await fs.stat(p);
  const result={path:p,size:s.size,createdAt:s.birthtime.toISOString(),modifiedAt:s.mtime.toISOString(),isDirectory:s.isDirectory(),isFile:s.isFile(),permissions:(s.mode&0o777).toString(8)};
  if(s.isFile()&&s.size<5000000){try{result.lineCount=(await fs.readFile(p,'utf8')).split(/\\r?\\n/).length}catch{}}
  return result;
}
export async function writeFile(target,content,mode='rewrite'){
  const p=safePath(target);await fs.mkdir(path.dirname(p),{recursive:true});
  if(mode==='append')await fs.appendFile(p,String(content),'utf8');else await fs.writeFile(p,String(content),'utf8');
  const result={path:p,bytes:Buffer.byteLength(String(content),'utf8'),mode};await record('write_file',result);return result;
}
export async function editFileBlock(target,oldString,newString,replaceAll=false){
  const p=safePath(target),text=await fs.readFile(p,'utf8');if(!text.includes(oldString))throw new Error('oldString not found');
  const next=replaceAll?text.split(oldString).join(newString):text.replace(oldString,newString);await fs.writeFile(p,next,'utf8');
  return {path:p,replacements:replaceAll?text.split(oldString).length-1:1};
}
export async function moveFile(source,destination){
  const s=safePath(source),d=safePath(destination);await fs.mkdir(path.dirname(d),{recursive:true});await fs.rename(s,d);return {source:s,destination:d};
}
export async function createDirectory(target){const p=safePath(target);await fs.mkdir(p,{recursive:true});return {path:p,created:true}}
export async function searchFiles(query,options={}){
  const root=safePath(options.root||'.'),id=crypto.randomUUID();searches.set(id,{id,status:'running',query,root,startedAt:new Date().toISOString()});
  const rg=await new Promise(resolve=>execFile('rg',['-n','--hidden','--glob','!.git/**',query,root],{timeout:60000,maxBuffer:MAX_OUTPUT},
    (error,stdout,stderr)=>resolve({error,stdout,stderr})));
  if(rg.error?.code==='ENOENT'){searches.get(id).status='failed';searches.get(id).error='ripgrep not installed';return searches.get(id)}
  const results=String(rg.stdout||'').split(/\\r?\\n/).filter(Boolean);
  Object.assign(searches.get(id),{status:'complete',count:results.length,results});return searches.get(id);
}
export function getSearchResults(searchId,offset=0,limit=100){
  const s=searches.get(searchId);if(!s)throw new Error('unknown search');return {searchId,status:s.status,total:s.results?.length||0,results:(s.results||[]).slice(offset,offset+limit)};
}
export function stopSearch(searchId){const s=searches.get(searchId);if(!s)throw new Error('unknown search');s.status='stopped';return s}
export function listActiveSearches(){return [...searches.values()].filter(x=>x.status==='running').map(({id,status,query,root,startedAt})=>({id,status,query,root,startedAt}))}
export async function startProcess(command,options={}){
  assertCommand(command);const id=crypto.randomUUID(),[exe,...args]=String(command).trim().split(/\\s+/);
  const child=spawn(exe,args,{cwd:options.cwd||process.cwd(),env:{...process.env,...(options.env||{})},shell:false});
  const session={id,pid:child.pid,command,status:'running',startedAt:new Date().toISOString(),stdout:'',stderr:'',child};sessions.set(id,session);
  child.stdout?.on('data',d=>{session.stdout+=String(d);if(session.stdout.length>MAX_OUTPUT)session.stdout=session.stdout.slice(-MAX_OUTPUT)});
  child.stderr?.on('data',d=>{session.stderr+=String(d);if(session.stderr.length>MAX_OUTPUT)session.stderr=session.stderr.slice(-MAX_OUTPUT)});
  child.on('close',(code,signal)=>{session.status='finished';session.code=code;session.signal=signal;session.finishedAt=new Date().toISOString()});
  return {sessionId:id,pid:child.pid,status:session.status};
}
export function sendInput(sessionId,input){const s=sessions.get(sessionId);if(!s?.child)throw new Error('unknown session');s.child.stdin.write(String(input));return {sessionId,ok:true}}
export function readProcessOutput(sessionId,offset=0,length=100){
  const s=sessions.get(sessionId);if(!s)throw new Error('unknown session');const lines=(s.stdout+'\n'+s.stderr).split(/\\r?\\n/).filter(Boolean);
  return {sessionId,status:s.status,code:s.code??null,signal:s.signal??null,lines:lines.slice(offset,offset+length),total:lines.length};
}
export function listActiveSessions(){return [...sessions.values()].map(s=>({sessionId:s.id,pid:s.pid,command:s.command,status:s.status,startedAt:s.startedAt,finishedAt:s.finishedAt??null}))}
export function terminateSession(sessionId){const s=sessions.get(sessionId);if(!s)throw new Error('unknown session');s.child.kill('SIGTERM');return {sessionId,terminated:true}}
export async function listSystemProcesses(){const r=await execFilePromise('ps',['-eo','pid,ppid,stat,etime,%cpu,%mem,comm,args']);return {ok:r.code===0,output:r.stdout}}
export async function killSystemProcess(pid){
  if(process.env.NOVA_DEVICE_ALLOW_DANGEROUS!=='true')throw new Error('Killing system processes requires NOVA_DEVICE_ALLOW_DANGEROUS=true');
  const r=await execFilePromise('kill',['-TERM',String(Number(pid))]);return {ok:r.code===0,output:r.stderr||r.stdout};
}
function execFilePromise(exe,args){return new Promise(resolve=>execFile(exe,args,{maxBuffer:MAX_OUTPUT},(error,stdout,stderr)=>resolve({code:error?.code??0,stdout:String(stdout||''),stderr:String(stderr||'')})))}
export async function writePdf(target,title='Nova Document',body=''){
  const p=safePath(target),doc=await PDFDocument.create(),font=await doc.embedFont(StandardFonts.Helvetica);let page=doc.addPage([595.28,841.89]),y=800;
  page.drawText(String(title),{x:50,y,size:18,font});y-=35;
  for(const raw of String(body).split(/\\r?\\n/)){if(y<50){page=doc.addPage([595.28,841.89]);y=800}page.drawText(raw.slice(0,105),{x:50,y,size:10,font,color:rgb(0,0,0)});y-=15}
  const bytes=await doc.save();await fs.mkdir(path.dirname(p),{recursive:true});await fs.writeFile(p,bytes);return {path:p,bytes:bytes.length};
}
export function readExcel(target){const p=safePath(target),book=XLSX.readFile(p,{cellDates:true});return Object.fromEntries(book.SheetNames.map(name=>[name,XLSX.utils.sheet_to_json(book.Sheets[name],{header:1,defval:null})]))}
export async function writeExcel(target,sheets){
  const p=safePath(target),book=XLSX.utils.book_new();for(const [name,rows] of Object.entries(sheets))XLSX.utils.book_append_sheet(book,XLSX.utils.aoa_to_sheet(rows),name.slice(0,31));
  XLSX.writeFile(book,p);return {path:p,sheets:Object.keys(sheets)};
}
export async function getConfig(){const p=path.join(CONFIG_DIR(),'config.json');try{return JSON.parse(await fs.readFile(p,'utf8'))}catch{return {version:1,roots:ROOTS(),policy:{allowDangerous:false}}}}
export async function setConfig(key,value){
  const current=await getConfig(),parts=String(key).split('.');let obj=current;for(let i=0;i<parts.length-1;i++){obj[parts[i]]??={};obj=obj[parts[i]]}obj[parts.at(-1)]=value;
  await fs.mkdir(CONFIG_DIR(),{recursive:true});await fs.writeFile(path.join(CONFIG_DIR(),'config.json'),JSON.stringify(current,null,2));return current;
}
export async function getUsageStatistics(){
  try{const lines=(await fs.readFile(LOG_FILE(),'utf8')).split(/\\r?\\n/).filter(Boolean),counts={};for(const line of lines){const e=JSON.parse(line);counts[e.event]=(counts[e.event]||0)+1}return {events:lines.length,byEvent:counts}}catch{return {events:0,byEvent:{}}}
}
export async function getRecentToolActivity(limit=100){try{return (await fs.readFile(LOG_FILE(),'utf8')).split(/\\r?\\n/).filter(Boolean).slice(-limit).map(JSON.parse)}catch{return []}}
export async function termuxStatus(){
  const info=deviceInfo();let pkg=null;if(info.termux){try{pkg=await execCommand('pkg --version',{timeoutMs:15000})}catch(error){pkg={ok:false,error:String(error)}}}
  return {info,pkgAvailable:Boolean(pkg?.ok),pkgVersion:pkg?.stdout?.trim()||null};
}
export const TERMUX_PROFILES={
  minimal:['git','curl','wget','openssh','ripgrep','jq','tar','unzip','zip'],
  developer:['git','curl','wget','openssh','ripgrep','jq','tar','unzip','zip','python','nodejs','npm','make','clang','cmake','pkg-config','rust','golang','perl','ruby'],
  build:['git','curl','wget','openssh','ripgrep','jq','tar','unzip','zip','python','nodejs','npm','make','clang','clang++','cmake','pkg-config','rust','golang','perl','ruby','php']
};
export async function termuxProvision(profile='developer'){
  const info=deviceInfo();if(!info.termux)return {ok:false,skipped:true,reason:'not running inside Termux'};
  const packages=TERMUX_PROFILES[profile]||TERMUX_PROFILES.developer;
  const update=await execCommand('pkg update -y',{timeoutMs:600000});
  const upgrade=await execCommand('pkg upgrade -y',{timeoutMs:600000});
  const install=await execCommand('pkg install -y '+packages.join(' '),{timeoutMs:600000});
  return {ok:update.ok&&upgrade.ok&&install.ok,profile,packages,update,upgrade,install};
}
export async function termuxApi(command,args=[]){
  if(!deviceInfo().termux)throw new Error('Termux API requires Termux');
  const allowed=new Set(['termux-battery-status','termux-wifi-connectioninfo','termux-wifi-scaninfo','termux-clipboard-get','termux-notification','termux-toast','termux-vibrate','termux-camera-photo','termux-media-scan','termux-open','termux-open-url','termux-share']);
  if(!allowed.has(command))throw new Error('Termux API command not allowlisted');
  return execCommand([command,...args].join(' '),{timeoutMs:30000});
}
export async function termuxBackground(command){if(!deviceInfo().termux)throw new Error('Termux required');return startProcess(command,{cwd:process.cwd()})}
export const TOOL_REGISTRY={
  deviceInfo,listDirectory,readFile,readMultipleFiles,getFileInfo,writeFile,editFileBlock,moveFile,createDirectory,
  searchFiles,getSearchResults,stopSearch,listActiveSearches,startProcess,sendInput,readProcessOutput,listActiveSessions,
  terminateSession,listSystemProcesses,killSystemProcess,writePdf,readExcel,writeExcel,getConfig,setConfig,getUsageStatistics,
  getRecentToolActivity,termuxStatus,termuxProvision,termuxApi,termuxBackground
};
