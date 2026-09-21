import {deviceInfo,desktopCommanderDoctor} from './device-bridge.mjs';

const info=deviceInfo();
const doctor=await desktopCommanderDoctor();

if(!info.node?.startsWith('v')) throw new Error('Node runtime detection failed');
if(doctor.desktopCommander.package!=='@wonderwhy-er/desktop-commander') throw new Error('Desktop Commander adapter missing');

console.log('NOVA_DEVICE_BRIDGE_TESTS_PASS');
console.log(JSON.stringify({info,desktopCommander:doctor.desktopCommander},null,2));
