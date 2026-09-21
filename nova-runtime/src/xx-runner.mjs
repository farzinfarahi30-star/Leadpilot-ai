import process from 'node:process';
import { runAgentCycle, persistStatus } from './agent-runtime.mjs';
import { buildXxTakeover } from '../../nova-mail/src/xx-control.mjs';
import { buildCompanyTakeoverPlan } from './company-takeover.mjs';

function log(event,data={}){console.log(JSON.stringify({ts:new Date().toISOString(),event,...data}));}
export const XX_RUNTIME_MODE='company-replication-takeover';

export async function runXxTakeover(){
  const started=Date.now();
  const companyTakeover=buildCompanyTakeoverPlan();
  log('xx_takeover_started',{
    control:'xx',
    mode:XX_RUNTIME_MODE,
    fromOwner:'nova',
    targetCompany:companyTakeover.source.company,
    sourceProjectId:companyTakeover.source.projectId,
    sourceVersion:companyTakeover.source.version,
    handoffStatus:companyTakeover.handoffStatus,
    manifestValid:companyTakeover.validation.ok,
    alternateOutsideXx:false
  });
  if(process.env.NOVA_TAKEOVER_ONLY==='true'){
    const proof={control:'xx',mode:XX_RUNTIME_MODE,takeover:true,success:true,executedAt:new Date().toISOString(),fromOwner:'nova',targetCompany:companyTakeover.source.company,sourceProjectId:companyTakeover.source.projectId,sourceVersion:companyTakeover.source.version,inventory:companyTakeover.inventory,programGroups:Object.keys(companyTakeover.programGroups),manifestValidation:companyTakeover.validation,alternateOutsideXx:false};
    log('xx_takeover_live_execution_complete',proof);
    return proof;
  }
  if(!companyTakeover.validation.ok){
    const error=new Error('Company takeover manifest invalid: '+companyTakeover.validation.errors.join('; '));
    const takeover=buildXxTakeover({
      operation:'company.takeover',
      blocker:error.message,
      fromOwner:'nova',
      context:{mode:XX_RUNTIME_MODE}
    });
    const outcome={
      control:'xx',
      takeover:true,
      mode:XX_RUNTIME_MODE,
      alternateOutsideXx:false,
      success:false,
      companyTakeover,
      takeoverRecord:takeover,
      error:error.message,
      durationMs:Date.now()-started
    };
    log('xx_takeover_failed',outcome);
    process.exitCode=1;
    return outcome;
  }
  try{
    const result=await runAgentCycle(1);
    const saved=await persistStatus(result).catch(error=>({persisted:false,error:String(error)}));
    const outcome={
      control:'xx',
      mode:XX_RUNTIME_MODE,
      takeover:true,
      fromOwner:'nova',
      alternateOutsideXx:false,
      companyTakeover,
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
      operation:'company.takeover.runtime',
      blocker:String(error),
      fromOwner:'nova',
      context:{runner:'github-actions',mode:XX_RUNTIME_MODE,targetCompany:companyTakeover.source.company}
    });
    const outcome={
      control:'xx',
      takeover:true,
      mode:XX_RUNTIME_MODE,
      alternateOutsideXx:false,
      success:false,
      companyTakeover,
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
