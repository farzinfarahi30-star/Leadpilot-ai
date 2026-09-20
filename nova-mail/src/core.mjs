import fs from 'node:fs/promises';
import path from 'node:path';

const MAX_BODY=200000;
const clean=function(v){return String(v==null?'':v).replace(/[\\u0000-\\u001f]+/g,' ').trim();};
const b64url=function(s){return Buffer.from(String(s),'utf8').toString('base64url');};
const required=function(name){const v=process.env[name];if(!v)throw new Error(name+' missing');return v;};

async function gmailAccessToken(){
  if(process.env.GMAIL_ACCESS_TOKEN)return process.env.GMAIL_ACCESS_TOKEN;
  const refresh=required('GMAIL_REFRESH_TOKEN');
  const clientId=required('GMAIL_CLIENT_ID');
  const clientSecret=required('GMAIL_CLIENT_SECRET');
  const r=await fetch('https://oauth2.googleapis.com/token',{
    method:'POST',
    headers:{'content-type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({client_id:clientId,client_secret:clientSecret,refresh_token:refresh,grant_type:'refresh_token'})
  });
  const body=await r.json().catch(function(){return {};});
  if(!r.ok)throw new Error('Gmail token '+r.status+': '+clean(body.error_description||body.error||'token refresh failed'));
  return body.access_token;
}

async function gmail(endpoint,options){
  options=options||{};
  const token=await gmailAccessToken();
  const r=await fetch('https://gmail.googleapis.com/gmail/v1/users/me/'+endpoint,{
    method:options.method||'GET',
    headers:{authorization:'Bearer '+token,'content-type':'application/json'},
    body:options.body===undefined?undefined:JSON.stringify(options.body)
  });
  const text=await r.text();
  let data={};try{data=text?JSON.parse(text):{};}catch{data={raw:text};}
  if(!r.ok)throw new Error('Gmail '+r.status+': '+clean(data.error&&data.error.message||text));
  return data;
}

async function resend(input){
  const key=required('RESEND_API_KEY');
  const sender=input.from||required('RESEND_FROM');
  const r=await fetch('https://api.resend.com/emails',{
    method:'POST',
    headers:{authorization:'Bearer '+key,'content-type':'application/json'},
    body:JSON.stringify({from:sender,to:String(input.to).split(',').map(function(x){return clean(x);}).filter(Boolean),cc:String(input.cc||'').split(',').map(function(x){return clean(x);}).filter(Boolean),bcc:String(input.bcc||'').split(',').map(function(x){return clean(x);}).filter(Boolean),subject:input.subject,text:input.text})
  });
  const text=await r.text(); let data={}; try{data=text?JSON.parse(text):{};}catch{data={raw:text};}
  if(!r.ok)throw new Error('Resend '+r.status+': '+clean(data.message||data.name||text||'send failed'));
  return {sent:true,provider:'resend',messageId:data.id||null};
}

async function outlookAccessToken(){
  if(process.env.OUTLOOK_ACCESS_TOKEN)return process.env.OUTLOOK_ACCESS_TOKEN;
  const refresh=required('OUTLOOK_REFRESH_TOKEN');
  const clientId=required('OUTLOOK_CLIENT_ID');
  const clientSecret=required('OUTLOOK_CLIENT_SECRET');
  const r=await fetch('https://login.microsoftonline.com/common/oauth2/v2.0/token',{
    method:'POST',
    headers:{'content-type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({client_id:clientId,client_secret:clientSecret,refresh_token:refresh,grant_type:'refresh_token',scope:'https://graph.microsoft.com/.default offline_access'})
  });
  const body=await r.json().catch(function(){return {};});
  if(!r.ok)throw new Error('Outlook token '+r.status+': '+clean(body.error_description||body.error||'token refresh failed'));
  return body.access_token;
}

async function outlook(endpoint,options){
  options=options||{};
  const token=await outlookAccessToken();
  const r=await fetch('https://graph.microsoft.com/v1.0/'+endpoint,{
    method:options.method||'GET',
    headers:{authorization:'Bearer '+token,'content-type':'application/json'},
    body:options.body===undefined?undefined:JSON.stringify(options.body)
  });
  const text=await r.text();
  let data={};try{data=text?JSON.parse(text):{};}catch{data={raw:text};}
  if(!r.ok)throw new Error('Outlook '+r.status+': '+clean(data.error&&data.error.message||text));
  return data;
}

function mime(input){
  const lines=[
    'From: '+input.from,
    'To: '+input.to,
    input.cc?'Cc: '+input.cc:null,
    input.bcc?'Bcc: '+input.bcc:null,
    'Subject: '+input.subject,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    '',
    input.text
  ].filter(Boolean);
  return lines.join('\r\n');
}

export async function sendEmail(input){
  input=input||{};
  if(input.approved!==true)return {sent:false,blocked:true,reason:'explicit approval required'};
  if(!input.to||!input.subject||!input.text)throw new Error('to, subject and text are required');
  if(String(input.text).length>MAX_BODY)throw new Error('message body too large');
  const provider=input.provider||process.env.NOVA_MAIL_PROVIDER||'gmail';
  if(provider==='resend'){
    return await resend(input);
  }
  if(provider==='gmail'){
    const sender=input.from||process.env.GMAIL_FROM||required('GMAIL_ACCOUNT');
    const out=await gmail('messages/send',{method:'POST',body:{raw:b64url(mime({from:sender,to:input.to,cc:input.cc,bcc:input.bcc,subject:input.subject,text:input.text}))}});
    return {sent:true,provider:'gmail',messageId:out.id||null,threadId:out.threadId||null};
  }
  if(provider==='outlook'){
    const message={
      subject:input.subject,
      body:{contentType:'Text',content:input.text},
      toRecipients:String(input.to).split(',').map(function(address){return {emailAddress:{address:clean(address)}};}),
      ccRecipients:String(input.cc||'').split(',').filter(Boolean).map(function(address){return {emailAddress:{address:clean(address)}};}),
      bccRecipients:String(input.bcc||'').split(',').filter(Boolean).map(function(address){return {emailAddress:{address:clean(address)}};})
    };
    await outlook('me/sendMail',{method:'POST',body:{message:message,saveToSentItems:true}});
    return {sent:true,provider:'outlook',accepted:true};
  }
  throw new Error('Unsupported mail provider: '+provider);
}

export async function searchThreads(input){
  input=input||{};
  const provider=input.provider||process.env.NOVA_MAIL_PROVIDER||'gmail';
  const limit=Math.max(1,Math.min(Number(input.maxResults)||10,50));
  const query=String(input.query||'');
  if(provider==='gmail'){
    const out=await gmail('threads?maxResults='+limit+'&q='+encodeURIComponent(query));
    return {provider:provider,threads:(out.threads||[]).map(function(x){return {id:x.id};})};
  }
  if(provider==='outlook'){
    const endpoint=query?'me/messages?$top='+limit+'&$search='+encodeURIComponent('"'+query.replaceAll('"','')+'"'):'me/messages?$top='+limit;
    const out=await outlook(endpoint);
    return {provider:provider,messages:(out.value||[]).map(function(x){return {id:x.id,subject:x.subject,receivedDateTime:x.receivedDateTime,from:x.from&&x.from.emailAddress&&x.from.emailAddress.address};})};
  }
  throw new Error('Unsupported mail provider: '+provider);
}

export async function getThread(input){
  input=input||{};
  if(!input.id)throw new Error('id is required');
  const provider=input.provider||process.env.NOVA_MAIL_PROVIDER||'gmail';
  if(provider==='gmail'){
    const out=await gmail('threads/'+encodeURIComponent(input.id)+'?format=full');
    return {provider:provider,threadId:out.id,messages:(out.messages||[]).map(function(m){return {id:m.id,threadId:m.threadId,labels:m.labelIds,internalDate:m.internalDate,payload:m.payload};})};
  }
  if(provider==='outlook'){
    return {provider:provider,message:await outlook('me/messages/'+encodeURIComponent(input.id))};
  }
  throw new Error('Unsupported mail provider: '+provider);
}

export async function createDraft(input){
  input=input||{};
  const provider=input.provider||process.env.NOVA_MAIL_PROVIDER||'gmail';
  if(provider!=='gmail')throw new Error('Draft creation currently targets Gmail; Outlook send is supported.');
  const sender=input.from||process.env.GMAIL_FROM||required('GMAIL_ACCOUNT');
  const out=await gmail('drafts',{method:'POST',body:{message:{raw:b64url(mime({from:sender,to:input.to||'',cc:input.cc||'',bcc:input.bcc||'',subject:input.subject||'',text:input.text||''}))}}});
  return {provider:provider,draftId:out.id||null,messageId:out.message&&out.message.id||null};
}

async function ensureDir(file){await fs.mkdir(path.dirname(file),{recursive:true});}

export async function scheduleEmail(input){
  input=input||{};
  if(input.approved!==true)return {scheduled:false,blocked:true,reason:'explicit approval required'};
  const ts=new Date(input.sendAt).getTime();
  if(!Number.isFinite(ts)||ts<=Date.now())throw new Error('sendAt must be a future timestamp');
  const file=path.resolve(input.queueFile||'./status/scheduled-mail.json');
  await ensureDir(file);
  let queue=[];try{queue=JSON.parse(await fs.readFile(file,'utf8'));}catch{}
  const id='mail_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
  queue.push({id:id,provider:input.provider,to:input.to,from:input.from,cc:input.cc,bcc:input.bcc,subject:input.subject,text:input.text,sendAt:new Date(ts).toISOString(),approved:true,status:'scheduled'});
  await fs.writeFile(file,JSON.stringify(queue,null,2));
  return {scheduled:true,id:id,sendAt:new Date(ts).toISOString()};
}
