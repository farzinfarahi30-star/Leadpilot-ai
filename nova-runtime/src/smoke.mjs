import { chromium } from 'playwright';
import { NOVA_DEVICE_TOOLS, listDesktopCommanderTools } from './device-tools.mjs';
import { desktopCommanderConfigured } from './desktop-commander-mcp.mjs';

const required=[
  'listDesktopCommanderTools',
  'callDesktopCommanderTool',
  'deployNovaTokenTestnet',
  'readFile',
  'writeFile',
  'startProcess',
  'listSystemProcesses'
];
const missing=required.filter(name=>typeof NOVA_DEVICE_TOOLS[name]!=='function');
if(missing.length) throw new Error('Missing Nova device tools: '+missing.join(','));

const remote=await listDesktopCommanderTools();
if(desktopCommanderConfigured()!==Boolean(process.env.DESKTOP_COMMANDER_OAUTH_TOKEN))
  throw new Error('Desktop Commander configuration state mismatch.');

const browser=await chromium.launch({headless:true});
try{
  const page=await browser.newPage();
  await page.goto('https://example.com',{waitUntil:'domcontentloaded',timeout:30000});
  console.log(JSON.stringify({
    ok:true,
    title:await page.title(),
    url:page.url(),
    deviceToolCount:Object.keys(NOVA_DEVICE_TOOLS).length,
    novaTokenDeploymentTool:true,
    desktopCommander:{configured:remote.configured,connected:Boolean(remote.connected),toolCount:remote.toolCount??0}
  }));
}finally{await browser.close()}
