import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import process from 'node:process';

export const AGENTS = [
  ['advertising-expert','Advertising','campaign_prepare'],
  ['analytics-expert','Analytics','funnel_review'],
  ['compliance-expert','Compliance','policy_review'],
  ['customer-success-expert','Customer Success','outcomes_review'],
  ['engineering-expert','Engineering','change_prepare'],
  ['finance-expert','Finance','unit_economics'],
  ['growth-expert','Growth','experiment_prepare'],
  ['operations-expert','Operations','health_review'],
  ['partnerships-expert','Partnerships','partner_discovery'],
  ['portfolio-expert','Portfolio','capital_allocation'],
  ['product-expert','Product','experiment_design'],
  ['research-expert','Research','market_scan'],
  ['sales-expert','Sales','outreach_prepare'],
  ['security-expert','Security','control_review'],
  ['testing-expert','Testing','release_verify']
];

const FACTORY='https://ai-business-factory.hatchable.site';
const REPO=process.env.GITHUB_REPOSITORY||'farzinfarahi30-star/Leadpilot-ai';
const TOKEN=process.env.GITHUB_TOKEN||'';

const clean=(v)=>String(v??'').replace(/[\\u0000-\\u001f]+/g,' ').trim().slice(0,1000);

async function github(path,init={}){
  if(!TOKEN) throw new Error('GITHUB_TOKEN missing');
  const res=await fetch(`https://api.github.com/repos/${REPO}/${path}`,{
    ...init,
    headers:{
      accept:'application/vnd.github+json',
      authorization:`Bearer ${TOKEN}`,
      'x-github-api-version':'2022-11-28',
      ...(init.headers||{})
    }
  });
  const text=await res.text();
  let body; try{body=JSON.parse(text)}catch{body={raw:text}};
  if(!res.ok) throw new Error(`GitHub ${res.status}: ${clean(body?.message||text)}`);
  return body;
}

async function browserChecks(){
  const browser=await chromium.launch({headless:true});
  try{
    const page=await browser.newPage();
    const started=Date.now();
    const response=await page.goto(FACTORY,{waitUntil:'domcontentloaded',timeout:30000});
    return {
      ok:true,
      httpStatus:response?.status()??null,
      title:await page.title(),
      url:page.url(),
      latencyMs:Date.now()-started
    };
  }finally{await browser.close();}
}

function staticChecks(){
  const files=[
    './worker.mjs',
    './agent-runtime.mjs',
    './smoke.mjs',
    '../../.github/workflows/nova-runtime.yml'
  ];
  const checks=[];
  for(const rel of files){
    const p=new URL(rel,import.meta.url);
    if(fs.existsSync(p)){
      const ext=p.pathname.endsWith('.mjs')?'mjs':p.pathname.endsWith('.yml')?'yml':'file';
      let syntax='not-run';
      if(ext==='mjs'){
        const r=spawnSync(process.execPath,['--check',p.pathname],{encoding:'utf8'});
        syntax=r.status===0?'pass':(`fail: ${clean(r.stderr||r.stdout)}`);
      }
      checks.push({file:rel,exists:true,syntax});
    }else checks.push({file:rel,exists:false,syntax:'missing'});
  }
  return checks;
}

async function sendAgentEmail({to,from,subject,text}) {
  const apiKey=process.env.RESEND_API_KEY||'';
  if(!apiKey) return {sent:false,reason:'RESEND_API_KEY missing'};
  if(!to) return {sent:false,reason:'EMAIL_TEST_TO missing'};
  if(!from) return {sent:false,reason:'RESEND_FROM missing'};
  const response=await fetch('https://api.resend.com/emails',{
    method:'POST',
    headers:{authorization:`Bearer ${apiKey}`,'content-type':'application/json'},
    body:JSON.stringify({from,to:[to],subject,text})
  });
  const body=await response.json().catch(()=>({}));
  if(!response.ok) throw new Error(`Resend ${response.status}: ${clean(body?.message||body?.name||'email send failed')}`);
  return {sent:true,id:body?.id||null};
}

async function runAgent(key,domain,capability,shared){
  const base={agent:key,domain,capability,startedAt:new Date().toISOString()};
  try{
    const evidence=[];
    if(key==='research-expert'){
      const url='https://www.google.com/search?q='+encodeURIComponent('AI automation small business demand 2026');
      const res=await fetch(url,{headers:{'user-agent':'NovaRuntime/1.0'}});
      evidence.push({source:'public web',observation:`search request returned HTTP ${res.status}`,trace:url});
    }else if(key==='engineering-expert' || key==='testing-expert' || key==='security-expert'){
      evidence.push({source:'runtime filesystem',observation:JSON.stringify(shared.staticChecks),trace:'nova-runtime source and workflow'});
    }else if(key==='product-expert' || key==='growth-expert' || key==='sales-expert' || key==='customer-success-expert'){
      evidence.push({source:'Factory public site',observation:JSON.stringify(shared.browser),trace:FACTORY});
    }else if(key==='operations-expert' || key==='analytics-expert' || key==='portfolio-expert' || key==='finance-expert'){
      evidence.push({source:'Nova runtime control plane',observation:`15 specialist definitions loaded; cycle ${shared.cycle}`,trace:'nova-runtime/src/agent-runtime.mjs'});
    }else if(key==='sales-expert' && process.env.EMAIL_TEST_TO){
      const mail=await sendAgentEmail({
        to:process.env.EMAIL_TEST_TO,
        from:process.env.RESEND_FROM,
        subject:'Nova Runtime — Sales Agent Email Test',
        text:'This is a real outbound email test generated by the independent Nova Runtime sales-expert agent. If you received this, the agent email path is working.'
      });
      evidence.push({source:'Resend API',observation:mail.sent?'Email accepted by provider':'Email not sent: '+mail.reason,trace:mail.id||'provider response'});
      return {...base,status:mail.sent?'completed':'failed',confidence:mail.sent?100:0,evidence,recommendation:mail.sent?'Return verified outbound-email evidence to Boss.':'Configure the runtime email provider before claiming outbound email works.',finishedAt:new Date().toISOString(),email:mail};
    }else if(key==='advertising-expert'){
      evidence.push({source:'safety policy',observation:'Paid campaign launch is not implemented in the independent runtime; no spend was initiated.',trace:'nova-runtime runtime policy'});
    }else if(key==='compliance-expert' || key==='partnerships-expert'){
      evidence.push({source:'runtime policy',observation:'No outbound contact, credential change, or production deployment is performed by specialist workers.',trace:'nova-runtime execution boundary'});
    }
    return {...base,status:'completed',confidence:90,evidence,recommendation:'Return findings to Boss; do not create a second controller.',finishedAt:new Date().toISOString()};
  }catch(error){
    return {...base,status:'failed',confidence:0,evidence:[],error:String(error),finishedAt:new Date().toISOString()};
  }
}

export async function runAgentCycle(cycle=1){
  const checks=staticChecks();
  const browser=await browserChecks().catch(error=>({ok:false,error:String(error)}));
  const shared={cycle,staticChecks:checks,browser};
  const queue=AGENTS.map(([key,domain,capability])=>({key,domain,capability}));
  const results=[];
  while(queue.length){
    const job=queue.shift();
    results.push(await runAgent(job.key,job.domain,job.capability,shared));
  }
  return {
    runtime:'nova-runtime',
    cycle,
    timestamp:new Date().toISOString(),
    agentCount:AGENTS.length,
    completed:results.filter(x=>x.status==='completed').length,
    failed:results.filter(x=>x.status==='failed').length,
    browser,
    staticChecks:checks,
    agents:results
  };
}

export async function persistStatus(payload){
  if(!TOKEN) return {persisted:false,reason:'GITHUB_TOKEN missing'};
  const path='nova-runtime/status/agents.json';
  let sha=null;
  try{const current=await github(`contents/${path}?ref=main`);sha=current.sha;}catch{}
  const content=Buffer.from(JSON.stringify(payload,null,2)).toString('base64');
  const body={message:`nova-runtime: persist agent cycle ${payload.cycle}`,content,branch:'main'};
  if(sha) body.sha=sha;
  const res=await github(`contents/${path}`,{method:'PUT',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  return {persisted:true,commit:res.commit?.sha??null,path};
}
