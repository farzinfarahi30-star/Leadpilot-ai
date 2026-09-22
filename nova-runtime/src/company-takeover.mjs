import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const COMPANY_TAKEOVER_MODE='company-replication-takeover';
export const MANIFEST_PATH=fileURLToPath(new URL('../company-takeover-manifest.json',import.meta.url));
const REQUIRED_PROGRAM_GROUPS=['control_plane','company_os','product_and_factory','revenue_and_commercial','growth_and_distribution','infrastructure_and_tools','safety_and_governance'];

export function loadCompanyTakeoverManifest(){return JSON.parse(fs.readFileSync(MANIFEST_PATH,'utf8'));}
function hasAll(values,required){const set=new Set(values||[]);return required.every(x=>set.has(x));}

export function validateCompanyTakeoverManifest(manifest=loadCompanyTakeoverManifest()){
 const errors=[];
 if(manifest?.schema!=='nova.company.takeover.v1')errors.push('schema mismatch');
 if(manifest?.takeover?.mode!==COMPANY_TAKEOVER_MODE)errors.push('takeover mode mismatch');
 if(manifest?.takeover?.sourceCompany!=='AI Business Factory')errors.push('source company mismatch');
 if(manifest?.takeover?.sourceProjectId!=='proj_YdSUAosmSpN3')errors.push('source project mismatch');
 if(Number(manifest?.takeover?.sourceVersion)!==517)errors.push('source version mismatch');
 const inv=manifest?.inventory||{};
 for(const [key,expected] of [['totalFiles',515],['apiSourceFiles',239],['libraryFiles',30],['publicFiles',42],['deployedFunctions',279],['deployedApiFunctions',248],['scheduledFunctions',6],['databaseTables',221]])if(Number(inv[key])!==expected)errors.push(key+' inventory mismatch');
 if(!hasAll(Object.keys(manifest?.programs||{}),REQUIRED_PROGRAM_GROUPS))errors.push('program groups incomplete');
 if((manifest?.libraries||[]).length!==30)errors.push('library manifest incomplete');
 if((manifest?.sourcePaths?.allFiles||[]).length!==515)errors.push('file path manifest incomplete');
 if((manifest?.sourcePaths?.apiPaths||[]).length!==239)errors.push('api path manifest incomplete');
 if(!String(manifest?.securityBoundary?.secretsPolicy||'').match(/never private keys|wallet seeds|refresh tokens|API secret values/i))errors.push('secrets policy incomplete');
 return {ok:errors.length===0,errors,checkedAt:new Date().toISOString()};
}

export function buildCompanyTakeoverPlan(){
 const manifest=loadCompanyTakeoverManifest();
 const validation=validateCompanyTakeoverManifest(manifest);
 return {control:'xx',mode:COMPANY_TAKEOVER_MODE,takeover:true,owner:'nova',handoffStatus:manifest.takeover.handoffStatus,source:{company:manifest.takeover.sourceCompany,projectId:manifest.takeover.sourceProjectId,version:manifest.takeover.sourceVersion,url:manifest.takeover.sourceUrl},inventory:manifest.inventory,programGroups:Object.fromEntries(Object.entries(manifest.programs).map(([k,v])=>[k,{count:v.length,items:v}])),tools:{available:manifest.currentToolSummary.available,requiresConnection:manifest.currentToolSummary.requiresConnection,disabled:manifest.currentToolSummary.disabled,total:manifest.toolRegistry.length},workflow:manifest.workflows,importantProjectFiles:manifest.importantProjectFiles,validation,rule:'Nova operates the replicated company through the existing Boss/Governor control plane; no competing controller is created.'};
}

export function assertCompanyTakeoverReady(){const result=validateCompanyTakeoverManifest();if(!result.ok)throw new Error('Company takeover manifest invalid: '+result.errors.join('; '));return result;}
