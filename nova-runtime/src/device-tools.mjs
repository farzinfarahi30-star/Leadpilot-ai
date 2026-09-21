import * as device from '../../nova-device/src/core.mjs';
import {
  desktopCommanderConfigured,
  desktopCommanderHealth,
  executeDesktopCommanderTool
} from './desktop-commander-mcp.mjs';
import { dispatchNovaTokenTestnet } from './chain-ops.mjs';
import {
  novaChainPreflight,
  deployNovaTokenSepolia,
  verifyNovaTokenSepolia
} from './nova-chain-controller.mjs';
import {
  alchemySepoliaResources,
  alchemySepoliaRpc,
  alchemySepoliaChainId,
  alchemySepoliaBlockNumber,
  alchemySepoliaBalance,
  alchemySepoliaTransactionReceipt
} from './alchemy.mjs';
import {
  alchemyPlatformRequest,
  alchemyPortfolioTokensByAddress,
  alchemyPricesBySymbol,
  alchemyPricesByAddress,
  alchemyPortfolioHistory,
  alchemyNftRequest,
  alchemyTransferHistory,
  alchemyRpcGateway,
  alchemyBundlerRpc,
  alchemyCapabilityManifest
} from './alchemy-capabilities.mjs';

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

/**
 * Nova-owned NOVA token testnet deployment control.
 * Governor-style hard checks remain inside chain-ops.mjs; this tool only
 * dispatches the already-reviewed GitHub Actions deployment workflow.
 */
export async function deployNovaTokenTestnet(owner, maxSupplyTokens=1000000){
  return await dispatchNovaTokenTestnet({owner, maxSupplyTokens});
}

export async function novaSepoliaPreflight(options={}){
  return await novaChainPreflight(options);
}

export async function deployNovaTokenSepoliaOnChain(options={}){
  return await deployNovaTokenSepolia(options);
}

export async function verifyNovaTokenSepoliaOnChain(options={}){
  return await verifyNovaTokenSepolia(options);
}

/**
 * Alchemy integration for Nova's Ethereum data/control plane.
 * Read-only JSON-RPC is exposed here; signing remains in Nova's
 * dedicated chain controller so private keys never enter this adapter.
 */
export function alchemySepoliaNetwork(){
  return alchemySepoliaResources();
}

export async function alchemySepoliaRpcCall(method, params=[]){
  return await alchemySepoliaRpc(method, params);
}

export async function alchemySepoliaGetChainId(){
  return await alchemySepoliaChainId();
}

export async function alchemySepoliaGetBlockNumber(){
  return await alchemySepoliaBlockNumber();
}

export async function alchemySepoliaGetBalance(address, blockTag='latest'){
  return await alchemySepoliaBalance(address, blockTag);
}

export async function alchemySepoliaGetTransactionReceipt(hash){
  return await alchemySepoliaTransactionReceipt(hash);
}

export const NOVA_DEVICE_TOOLS={
  ...device.TOOL_REGISTRY,
  listDesktopCommanderTools,
  callDesktopCommanderTool,
  deployNovaTokenTestnet,
  novaSepoliaPreflight,
  deployNovaTokenSepoliaOnChain,
  verifyNovaTokenSepoliaOnChain,
  alchemySepoliaNetwork,
  alchemySepoliaRpcCall,
  alchemySepoliaGetChainId,
  alchemySepoliaGetBlockNumber,
  alchemySepoliaGetBalance,
  alchemySepoliaGetTransactionReceipt,
  alchemyPlatformRequest,
  alchemyPortfolioTokensByAddress,
  alchemyPricesBySymbol,
  alchemyPricesByAddress,
  alchemyPortfolioHistory,
  alchemyNftRequest,
  alchemyTransferHistory,
  alchemyRpcGateway,
  alchemyBundlerRpc,
  alchemyCapabilityManifest
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
