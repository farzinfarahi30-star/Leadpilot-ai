import { chromium } from 'playwright';
import { setTimeout as sleep } from 'node:timers/promises';
import process from 'node:process';

const FACTORY_URL=process.env.FACTORY_HEARTBEAT_URL||'https://ai-business-factory.hatchable.site/api/boss-heartbeat';
const TOKEN=process.env.FACTORY_BOSS_TOKEN||'';
const RUN_MINUTES=Number(process.env.RUN_MINUTES||330);
const POLL_MS=Number(process.env.POLL_MS||300000);
const deadline=Date.now()+RUN_MINUTES*60_000;

function log(event,data={}){console.log(JSON.stringify({ts:new Date().toISOString(),event,...data}));}

async function factoryHeartbeat(){
  const headers={'content-type':'application/json'};
  if(TOKEN) headers.authorization=`Bearer ${TOKEN}`;
  const res=await fetch(FACTORY_URL,{method:'POST',headers,body:JSON.stringify({bossAuthorized:true,source:'nova-runtime',runtime:'github-actions'})});
  const text=await res.text();
  let body; try{body=JSON.parse(text)}catch{body={raw:text.slice(0,1000)}}
  return {status:res.status,ok:res.ok,body};
}

async function browserSmoke(){
  const browser=await chromium.launch({headless:true});
  try{
    const page=await browser.newPage();
    await page.goto('https://example.com',{waitUntil:'domcontentloaded',timeout:30000});
    return {ok:true,title:await page.title(),url:page.url()};
  } finally { await browser.close(); }
}

log('runtime_started',{factoryUrl:FACTORY_URL,runMinutes:RUN_MINUTES,pollMs:POLL_MS});
let first=true;
while(Date.now()<deadline){
  try{
    if(first){
      try{ log('browser_smoke',await browserSmoke()); }
      catch(error){ log('browser_smoke_failed',{error:String(error)}); }
      first=false;
    }
    try{ log('factory_heartbeat',await factoryHeartbeat()); }
    catch(error){ log('factory_heartbeat_failed',{error:String(error)}); }
  }catch(error){log('loop_error',{error:String(error)})}
  const remaining=deadline-Date.now();
  if(remaining<=0) break;
  await sleep(Math.min(POLL_MS,remaining));
}
log('runtime_checkpoint_exit',{restartBySchedule:true});
