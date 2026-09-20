import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';
import { searchThreads,getThread,createDraft,scheduleEmail } from './core.mjs';
import { sendEmailViaXx,buildXxTakeover,XX_MODE } from './xx-control.mjs';
import { buildDnsPlan,verifyDns,dnsAuthorityStatus } from './dns-manager.mjs';

const server=new McpServer({name:'nova-mail',version:'1.2.0'});

server.registerTool('mail_search',{
  title:'Search Email',
  description:'Search the connected Gmail or Outlook mailbox.',
  inputSchema:{provider:z.enum(['gmail','outlook']).optional(),query:z.string().default(''),maxResults:z.number().int().min(1).max(50).default(10)}
},async function(input){
  const data=await searchThreads(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('mail_get_thread',{
  title:'Get Email Thread',
  description:'Read a Gmail thread or Outlook message.',
  inputSchema:{provider:z.enum(['gmail','outlook']).optional(),id:z.string()}
},async function(input){
  const data=await getThread(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('mail_create_draft',{
  title:'Create Email Draft',
  description:'Create a Gmail draft without sending it.',
  inputSchema:{
    provider:z.enum(['gmail']).default('gmail'),
    to:z.string().default(''),from:z.string().default(''),cc:z.string().default(''),bcc:z.string().default(''),
    subject:z.string(),text:z.string()
  }
},async function(input){
  const data=await createDraft(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('mail_send',{
  title:'Send Email',
  description:'Route outbound email through Nova first; when Nova is blocked, xx takes over. No outside fallback path exists.',
  inputSchema:{
    provider:z.enum(['gmail','outlook','resend']).optional(),
    to:z.string(),from:z.string().optional(),replyTo:z.string().optional(),
    cc:z.string().default(''),bcc:z.string().default(''),
    subject:z.string(),text:z.string(),html:z.string().optional(),
    approved:z.boolean().default(false),idempotencyKey:z.string().max(256).optional()
  }
},async function(input){
  const data=await sendEmailViaXx(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('mail_schedule_send',{
  title:'Schedule Email',
  description:'Queue an approved email for future sending.',
  inputSchema:{
    provider:z.enum(['gmail','outlook','resend']).optional(),
    to:z.string(),from:z.string().optional(),replyTo:z.string().optional(),
    cc:z.string().default(''),bcc:z.string().default(''),
    subject:z.string(),text:z.string(),sendAt:z.string(),approved:z.boolean().default(false)
  }
},async function(input){
  const data=await scheduleEmail(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('xx_status',{
  title:'xx Escalation Status',
  description:'Show the exclusive xx takeover policy. Nova has no outside fallback path.',
  inputSchema:{}
},async function(){
  const data={control:'xx',mode:XX_MODE,takeoverOnlyOnBlock:true,alternateOutsideXx:false};
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('xx_takeover_plan',{
  title:'xx Takeover Plan',
  description:'Create an evidence-bearing xx takeover record when Nova is blocked. This does not bypass authorization.',
  inputSchema:{
    operation:z.string(),
    blocker:z.string(),
    context:z.record(z.string(),z.any()).optional()
  }
},async function(input){
  const data=buildXxTakeover(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('domain_status',{
  title:'Nova Domain Status',
  description:'Inspect Nova domain authority boundary and current public DNS evidence.',
  inputSchema:{}
},async function(){
  const data=dnsAuthorityStatus();
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('domain_plan',{
  title:'Nova DNS Plan',
  description:'Build a non-mutating DNS change plan. Public DNS changes require an explicit approved request.',
  inputSchema:{domain:z.string().optional()}
},async function(input){
  const data=buildDnsPlan(input.domain);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('domain_verify',{
  title:'Verify Nova Domain',
  description:'Read public DNS and verify Nova ownership, SPF, DKIM and MX evidence without mutating DNS.',
  inputSchema:{domain:z.string().optional()}
},async function(input){
  const data=await verifyDns(input.domain);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

await serveStdio(server);
