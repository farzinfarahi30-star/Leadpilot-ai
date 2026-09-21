import * as device from '../../nova-device/src/core.mjs';
import {
  desktopCommanderConfigured,
  desktopCommanderHealth,
  executeDesktopCommanderTool
} from './desktop-commander-mcp.mjs';

export async function listDesktopCommanderTools(){
  if(!desktopCommanderConfigured()){
    return {configured:false,connected:false,tools:[],toolCount:0,reason:'DESKTOP_COMMANDER_OAUTH_TOKEN not configured'};
  }
  return await desktopCommanderHealth();
}

export async function callDesktopCommanderTool(name,args={}){
  if(!desktopCommanderConfigured()) throw new Error('Desktop Commander OAuth token is not configured.');
  return await executeDesktopCommanderTool(name,args,Date.now());
}

export const NOVA_DEVICE_TOOLS={
  ...device.TOOL_REGISTRY,
  listDesktopCommanderTools,
  callDesktopCommanderTool
};

export async function executeDeviceTool(name,args=[]){
  const fn=NOVA_DEVICE_TOOLS[name];
  if(typeof fn!=='function') throw new Error('Unknown device tool: '+name);
  if(name==='callDesktopCommanderTool'){
    const values=Array.isArray(args)?args:[args];
    return await fn(values[0],values[1]||{});
  }
  return await fn(...(Array.isArray(args)?args:[]));
}

export async function deviceBootstrapAndDoctor(){
  const status=await device.termuxStatus();
  let provision=null;
  if(status.info.termux&&process.env.NOVA_DEVICE_AUTO_PROVISION==='true')
    provision=await device.termuxProvision(process.env.NOVA_TERMUX_PROFILE||'developer');
  const remote=await listDesktopCommanderTools().catch(error=>({
    configured:desktopCommanderConfigured(),
    connected:false,
    tools:[],
    toolCount:0,
    error:String(error)
  }));
  return {
    status,
    provision,
    info:device.deviceInfo(),
    toolCount:Object.keys(NOVA_DEVICE_TOOLS).length,
    desktopCommander:remote
  };
}
