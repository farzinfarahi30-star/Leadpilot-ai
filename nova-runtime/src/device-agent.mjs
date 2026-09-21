import * as device from '../../nova-device/src/core.mjs';
import {desktopCommanderHealth,desktopCommanderConfigured} from './desktop-commander-mcp.mjs';

export const DEVICE_AGENT_VERSION='1.1.0';

export async function runDeviceOperations(cycle=1){
  if(process.env.NOVA_DEVICE_CONTROL!=='true'){
    return {enabled:false,cycle,reason:'NOVA_DEVICE_CONTROL is not true'};
  }
  const info=device.deviceInfo();
  const status=await device.termuxStatus();
  const sessions=device.listActiveSessions();
  const searches=device.listActiveSearches();
  let remote={configured:desktopCommanderConfigured(),connected:false};
  if(remote.configured){
    try{remote={...remote,...await desktopCommanderHealth()};}
    catch(error){remote={...remote,error:String(error)};}
  }
  let provisioning=null;
  if(info.termux && process.env.NOVA_DEVICE_AUTO_PROVISION==='true' && !status.pkgAvailable){
    provisioning=await device.termuxProvision(process.env.NOVA_TERMUX_PROFILE||'developer');
  }
  return {
    enabled:true,cycle,version:DEVICE_AGENT_VERSION,
    device:info,termux:status,activeSessions:sessions,activeSearches:searches,
    desktopCommander:remote,provisioning,
    control:'Nova local + Desktop Commander remote control'
  };
}