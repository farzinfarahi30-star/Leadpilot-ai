import * as device from '../../nova-device/src/core.mjs';

export const DEVICE_AGENT_VERSION='1.0.0';

export async function runDeviceOperations(cycle=1){
  if(process.env.NOVA_DEVICE_CONTROL!=='true'){
    return {enabled:false,cycle,reason:'NOVA_DEVICE_CONTROL is not true'};
  }

  const info=device.deviceInfo();
  const status=await device.termuxStatus();
  const sessions=device.listActiveSessions();
  const searches=device.listActiveSearches();

  let provisioning=null;
  if(
    info.termux &&
    process.env.NOVA_DEVICE_AUTO_PROVISION==='true' &&
    !status.pkgAvailable
  ){
    provisioning=await device.termuxProvision(process.env.NOVA_TERMUX_PROFILE||'developer');
  }

  return {
    enabled:true,
    cycle,
    version:DEVICE_AGENT_VERSION,
    device:info,
    termux:status,
    activeSessions:sessions,
    activeSearches:searches,
    provisioning,
    control:'Nova local device control'
  };
}

export async function executeLocalDeviceTool(name,args=[]){
  if(process.env.NOVA_DEVICE_CONTROL!=='true')
    throw new Error('Local device control is disabled; set NOVA_DEVICE_CONTROL=true in the supervised runtime.');
  return device.TOOL_REGISTRY[name](...(Array.isArray(args)?args:[]));
}
