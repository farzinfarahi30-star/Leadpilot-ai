import * as device from '../../nova-device/src/core.mjs';

export const NOVA_DEVICE_TOOLS=device.TOOL_REGISTRY;
export async function executeDeviceTool(name,args=[]){
  const fn=NOVA_DEVICE_TOOLS[name];if(typeof fn!=='function')throw new Error('Unknown device tool: '+name);
  return fn(...(Array.isArray(args)?args:[]));
}
export async function deviceBootstrapAndDoctor(){
  const status=await device.termuxStatus();
  let provision=null;
  if(status.info.termux&&process.env.NOVA_DEVICE_AUTO_PROVISION==='true')
    provision=await device.termuxProvision(process.env.NOVA_TERMUX_PROFILE||'developer');
  return {status,provision,info:device.deviceInfo(),toolCount:Object.keys(NOVA_DEVICE_TOOLS).length};
}
