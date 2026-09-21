import {deviceInfo,TOOL_REGISTRY,getConfig,getUsageStatistics} from './core.mjs';
const info=deviceInfo();
const required=['listDirectory','readFile','readMultipleFiles','getFileInfo','writeFile','editFileBlock','moveFile','createDirectory',
  'searchFiles','getSearchResults','stopSearch','listActiveSearches','startProcess','sendInput','readProcessOutput','listActiveSessions',
  'terminateSession','listSystemProcesses','killSystemProcess','writePdf','readExcel','writeExcel','termuxStatus','termuxProvision',
  'termuxApi','termuxBackground','getConfig','setConfig','executeCode','writePdf','modifyPdfAppend','readExcel','writeExcel','listPairedDevices','currentUserInfo','pingDevice','shutdownDeviceAgent','getPromptLibrary','getConfig','setConfig','getUsageStatistics','getRecentToolActivity'];
const missing=required.filter(x=>typeof TOOL_REGISTRY[x]!=='function');
if(missing.length)throw new Error('Missing tools: '+missing.join(','));
console.log('NOVA_DEVICE_XX_TESTS_PASS');
console.log(JSON.stringify({platform:info.platform,termux:info.termux,toolCount:Object.keys(TOOL_REGISTRY).length,usage:await getUsageStatistics()},null,2));
