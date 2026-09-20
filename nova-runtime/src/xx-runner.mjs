import process from 'node:process';
import { runAgentCycle, persistStatus } from './agent-runtime.mjs';
import { buildXxTakeover } from '../../nova-mail/src/xx-control.mjs';

function log(event,data={}){console.log(JSON.stringify({ts:new Date().toISOString(),event,...data}));}
export const XX_RUNTIME_MODE='xx-runtime-takeover';

export async function runXxTakeover(){
  const started=Date.now();
  log('xx_takeover_started',{
    control:'xx',
    mode:XX_RUNTIME_MODE,
    fromOwner:'nova',
    blocker:'github-actions-runner-execution',
    alternateOutsideXx:false
  });
  try{
    const result=await runAgentCycle(1);
    const saved=await persistStatus(result).catch(error=>({persisted:false,error:String(error)}));
    const outcome={
      control:'xx',
      mode:XX_RUNTIME_MODE,
      takeover:true,
      fromOwner:'nova',
      blocker:'github-actions-runner-execution',
      alternateOutsideXx:false,
      cycle:result.cycle,
      completed:result.completed,
      failed:result.failed,
      browser:result.browser,
      persisted:saved,
      durationMs:Date.now()-started
    };
    log('xx_takeover_complete',outcome);
    return outcome;
  }catch(error){
    const takeover=buildXxTakeover({
      operation:'runtime.execute',
      blocker:String(error),
      fromOwner:'nova',
      context:{runner:'github-actions',mode:XX_RUNTIME_MODE}
    });
    const outcome={
      control:'xx',
      takeover:true,
      mode:XX_RUNTIME_MODE,
      alternateOutsideXx:false,
      success:false,
      error:String(error),
      takeoverRecord:takeover,
      durationMs:Date.now()-started
    };
    log('xx_takeover_failed',outcome);
    process.exitCode=1;
    return outcome;
  }
}

await runXxTakeover();
