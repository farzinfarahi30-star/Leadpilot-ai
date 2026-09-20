import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';
import { sendEmail,searchThreads,getThread,createDraft,scheduleEmail } from './core.mjs';

const server=new McpServer({name:'nova-mail',version:'1.0.0'});

server.registerTool('mail_search',{
  title:'Search Email',
  description:'Search the connected Gmail or Outlook mailbox.',
  inputSchema:{provider:z.enum(['gmail','outlook','resend']).optional(),query:z.string().default(''),maxResults:z.number().int().min(1).max(50).default(10)}
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
  description:'Send an email only when approved is true. The approval gate is enforced server-side.',
  inputSchema:{
    provider:z.enum(['gmail','outlook']).optional(),
    to:z.string(),from:z.string().optional(),cc:z.string().default(''),bcc:z.string().default(''),
    subject:z.string(),text:z.string(),approved:z.boolean().default(false)
  }
},async function(input){
  const data=await sendEmail(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

server.registerTool('mail_schedule_send',{
  title:'Schedule Email',
  description:'Queue an approved email for future sending.',
  inputSchema:{
    provider:z.enum(['gmail','outlook']).optional(),
    to:z.string(),from:z.string().optional(),cc:z.string().default(''),bcc:z.string().default(''),
    subject:z.string(),text:z.string(),sendAt:z.string(),approved:z.boolean().default(false)
  }
},async function(input){
  const data=await scheduleEmail(input);
  return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};
});

await serveStdio(server);
