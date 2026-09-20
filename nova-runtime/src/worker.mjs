import { setTimeout as sleep } from 'node:timers/promises';
import process from 'node:process';
import { runAgentCycle, persistStatus } from './agent-runtime.mjs';

const RUN_MINUTES=Math.max(1,Number(process.env.RUN_MINUTES||5));
const POLL_MS=Math.max(1000,Number(process.env.POLL_MS||600000));
const deadline=Date.now()+RUN_MINUTES*60_000;

function log(event,data={}){console.log(JSON.stringify({ts:new Date().toISOString(),event,...data}));}

log('runtime_started',{runMinutes:RUN_MINUTES,pollMs:POLL_MS,agentCount:15,controlPlane:'nova-independent',escalation:'xx-only'});

let cycle=0;
let lastResult=null;
while(Date.now()<deadline){
  cycle++;
  const cycleStarted=Date.now();
  try{
    const result=await runAgentCycle(cycle);
    lastResult=result;
    log('agent_cycle_complete',{cycle,completed:result.completed,failed:result.failed,browser:result.browser});
    const saved=await persistStatus(result).catch(error=>({persisted:false,error:String(error)}));
    log('agent_status_persisted',saved);
  }catch(error){
    log('agent_cycle_failed',{cycle,error:String(error)});
    const remaining=deadline-Date.now();
    if(remaining>0) await sleep(Math.min(5000,remaining));
  }
  const elapsed=Date.now()-cycleStarted;
  const remaining=deadline-Date.now();
  if(remaining<=0) break;
  // Never sleep longer than the remaining runtime; a push run therefore exits promptly.
  await sleep(Math.min(POLL_MS,remaining));
}

log('runtime_checkpoint_exit',{
  restartBySchedule:true,
  cycles:cycle,
  completed:lastResult?.completed??0,
  failed:lastResult?.failed??0
});
