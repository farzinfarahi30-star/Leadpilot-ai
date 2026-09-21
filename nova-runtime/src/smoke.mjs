import { chromium } from 'playwright';
import {
  NOVA_DEVICE_TOOLS,
  listDesktopCommanderTools,
  alchemySepoliaNetwork
} from './device-tools.mjs';
import { desktopCommanderConfigured } from './desktop-commander-mcp.mjs';
import {
  novaCryptoCapabilityManifest,
  novaCryptoDoctor,
  novaCryptoChainDoctor
} from './crypto-capabilities.mjs';

const required=[
  'listDesktopCommanderTools',
  'callDesktopCommanderTool',
  'deployNovaTokenTestnet',
  'novaSepoliaPreflight',
  'deployNovaTokenSepoliaOnChain',
  'verifyNovaTokenSepoliaOnChain',
  'alchemySepoliaNetwork',
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
  'coinbaseCdpConfigured',
  'coinbaseCdpDoctor',
  'coinbaseCdpRequestSepoliaEth',
  'chainstackMcpConfigured',
  'chainstackMcpListTools',
  'chainstackMcpRequestSepoliaEth',
  'novaCryptoCapabilityManifest',
  'novaCryptoDoctor',
  'novaCryptoChainDoctor',
  'novaCryptoBalance',
  'novaCryptoReceipt',
  'requestSepoliaEth',
  'requestAndConfirmSepoliaEth',
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

const alchemy=alchemySepoliaNetwork();
const capabilities=alchemyCapabilityManifest();
const crypto=novaCryptoCapabilityManifest();
const doctor=novaCryptoDoctor();

if(alchemy.chainId!==11155111) throw new Error('Alchemy Sepolia chain ID mismatch.');
if(!alchemy.faucetUrl.includes('alchemy.com/faucets/ethereum-sepolia'))
  throw new Error('Alchemy Sepolia faucet integration mismatch.');
if(!alchemy.rpcUrl) throw new Error('Alchemy Sepolia RPC URL missing.');
if(!capabilities.chainApis.includes('jsonRpc')) throw new Error('Alchemy chain API capability missing.');
if(!capabilities.dataApis.includes('portfolio')) throw new Error('Alchemy portfolio capability missing.');
if(!capabilities.accountAbstraction.includes('bundler')) throw new Error('Alchemy bundler capability missing.');
if(crypto.primaryNetwork.chainId!==11155111) throw new Error('Nova crypto primary chain mismatch.');
if(!crypto.providers.coinbaseCdp.includes('sepoliaFaucet'))
  throw new Error('Coinbase CDP faucet capability missing.');
if(!crypto.providers.chainstack.includes('testnetFaucet'))
  throw new Error('Chainstack testnet faucet capability missing.');
if(!doctor.coinbaseCdp || !doctor.chainstack)
  throw new Error('Nova crypto provider doctor is incomplete.');

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
    alchemyCapabilityGateway:true,
    novaCryptoControlPlane:true,
    coinbaseCdpSepoliaFaucet:true,
    chainstackTestnetFaucet:true,
    desktopCommander:{configured:remote.configured,connected:Boolean(remote.connected),toolCount:remote.toolCount??0}
  }));
}finally{await browser.close()}
