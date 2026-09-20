import { sendEmail } from './core.mjs';

export const XX_MODE='xx-only-escalation';

const clean=v=>String(v??'').replace(/[\u0000-\u001f]+/g,' ').trim().slice(0,2000);

export function buildXxTakeover({operation,blocker,fromOwner='nova',context={}}={}){
  return {
    control:'xx',
    mode:XX_MODE,
    operation:clean(operation,200),
    takeover:true,
    fromOwner:clean(fromOwner,80)||'nova',
    blocker:clean(blocker,1200)||'unknown blocker',
    policy:{
      exclusiveEscalation:true,
      alternateOutsideXx:false,
      inventNewController:false,
      requireAuthorizedCapability:true
    },
    context
  };
}

export async function sendEmailViaXx(input){
  input=input||{};
  if(input.approved!==true)return {sent:false,blocked:true,reason:'explicit approval required',control:'xx'};
  try{
    const primary=await sendEmail(input);
    return {...primary,control:'nova',xx:{used:false}};
  }catch(primaryError){
    const takeover=buildXxTakeover({
      operation:'email.send',
      blocker:String(primaryError),
      fromOwner:'nova',
      context:{provider:input.provider||process.env.NOVA_MAIL_PROVIDER||null,to:clean(input.to,320)}
    });
    const xxProvider=process.env.XX_MAIL_PROVIDER||'';
    if(!xxProvider || xxProvider===(input.provider||process.env.NOVA_MAIL_PROVIDER||'')){
      return {
        sent:false,
        blocked:true,
        control:'xx',
        takeover,
        reason:'xx has taken control, but no distinct authorized XX_MAIL_PROVIDER is configured.'
      };
    }
    try{
      const result=await sendEmail({...input,provider:xxProvider,approved:true});
      return {...result,control:'xx',xx:{used:true,takeover,provider:xxProvider}};
    }catch(xxError){
      return {
        sent:false,
        blocked:true,
        control:'xx',
        takeover,
        reason:'xx takeover attempted and the authorized XX transport also failed.',
        error:clean(String(xxError),1800),
        provider:xxProvider
      };
    }
  }
}

export function xxDnsTakeoverStatus(status){
  return {
    control:'xx',
    mode:XX_MODE,
    takeover:true,
    sourceStatus:status,
    rule:'DNS authority blockers escalate only to xx; no outside fallback or competing controller is created.'
  };
}
