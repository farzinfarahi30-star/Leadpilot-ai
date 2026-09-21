import { chromium } from 'playwright';
import {
  NOVA_DEVICE_TOOLS,
  listDesktopCommanderTools,
  alchemySepoliaNetwork
} from './device-tools.mjs';
import { desktopCommanderConfigured } from './desktop-commander-mcp.mjs';

const required=[
  'listDesktopCommanderTools',
  'callDesktopCommanderTool',
  'deployNovaTokenTestnet',
  'novaSepoliaPreflight',
  'deployNovaTokenSepoliaOnChain',
  'verifyNovaTokenSepoliaOnChain',
  'alchemySepoliaNetwork',\n  'coinbaseCdpRequestSepoliaEth',
  'alchemySepoliaRpcCall',
  'alchemySepoliaGetChainId',
  'alchemySepoliaGetBlockNumber',
  'alchemySepoliaGetBalance',
  'alchemySepoliaGetTransactionReceipt',
  'alchemyPlatformRequest',
  'alchemyPortfolioTokensByAddress',
  'alchemyPricesBySymbol',
  'alchemyPricesByAddress',
  'alchemyPortfolioHistory',
  'alchemyNftRequest',
  'alchemyTransferHistory',
  'alchemyRpcGateway',
  'alchemyBundlerRpc',
  'alchemyCapabilityManifest',
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

const cdp=coinbaseCdpDoctor();\nif(cdp.network!=='ethereum-sepolia' || cdp.chainId!==11155111) throw new Error('Coinbase CDP Sepolia capability mismatch.');\n\nconst alchemy=alchemySepoliaNetwork();
const capabilities=alchemyCapabilityManifest();
if(alchemy.chainId!==11155111) throw new Error('Alchemy Sepolia chain ID mismatch.');
if(!alchemy.faucetUrl.includes('alchemy.com/faucets/ethereum-sepolia'))
  throw new Error('Alchemy Sepolia faucet integration mismatch.');
if(!alchemy.rpcUrl) throw new Error('Alchemy Sepolia RPC URL missing.');
if(!capabilities.chainApis.includes('jsonRpc')) throw new Error('Alchemy chain API capability missing.');
if(!capabilities.dataApis.includes('portfolio')) throw new Error('Alchemy portfolio capability missing.');
if(!capabilities.accountAbstraction.includes('bundler')) throw new Error('Alchemy bundler capability missing.');

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
    novaSepoliaControllerTools:true,
    alchemySepoliaIntegration:true,
    alchemyCapabilityGateway:true,\n    coinbaseCdpSepoliaFaucet:true,
    desktopCommander:{configured:remote.configured,connected:Boolean(remote.connected),toolCount:remote.toolCount??0}
  }));
}finally{await browser.close()}
