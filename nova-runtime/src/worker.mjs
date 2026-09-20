import { setTimeout as sleep } from 'node:timers/promises';
import process from 'node:process';
import { runAgentCycle, persistStatus } from './agent-runtime.mjs';

const RUN_MINUTES=Number(process.env.RUN_MINUTES||50);
const POLL_MS=Number(process.env.POLL_MS||600000);
const deadline=Date.now()+RUN_MINUTES*60_000;

function log(event,data={}){console.log(JSON.stringify({ts:new Date().toISOString(),event,...data}));}

log('runtime_started',{runMinutes:RUN_MINUTES,pollMs:POLL_MS,agentCount:15,controlPlane:'nova-independent'});

let cycle=0;
while(Date.now()<deadline){
  cycle++;
  try{
    const result=await runAgentCycle(cycle);
    log('agent_cycle_complete',{cycle,completed:result.completed,failed:result.failed,browser:result.browser});
    const saved=await persistStatus(result).catch(error=>({persisted:false,error:String(error)}));
    log('agent_status_persisted',saved);
  }catch(error){
    log('agent_cycle_failed',{cycle,error:String(error)});
  }
  const remaining=deadline-Date.now();
  if(remaining<=0) break;
  await sleep(Math.min(POLL_MS,remaining));
}

log('runtime_checkpoint_exit',{restartBySchedule:true,cycles:cycle});
