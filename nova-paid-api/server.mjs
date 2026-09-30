import express from "express";
import dns from "node:dns/promises";
import net from "node:net";

const PORT = Number(process.env.PORT || 8879);
const PAY_TO = (process.env.PAY_TO || "").trim();
const X402_NETWORK = process.env.X402_NETWORK || "eip155:8453";
const AUDIT_PRICE = process.env.AUDIT_PRICE || "$0.05";
const DEV_MODE = process.env.DEV_MODE === "1";

function isPrivateIp(ip) {
  if (net.isIP(ip) === 4) {
    const [a,b] = ip.split(".").map(Number);
    return a===10 || a===127 || (a===169&&b===254) || (a===172&&b>=16&&b<=31) ||
      (a===192&&b===168) || a===0 || a>=224;
  }
  if (net.isIP(ip) === 6) {
    const x=ip.toLowerCase();
    return x==="::1" || x.startsWith("fc") || x.startsWith("fd") || x.startsWith("fe80:");
  }
  return true;
}

async function safeUrl(input) {
  const u = new URL(input);
  if (!["http:","https:"].includes(u.protocol)) throw new Error("Only http/https URLs are allowed");
  if (u.username || u.password) throw new Error("Credentials in URL are not allowed");
  const h=u.hostname.toLowerCase();
  if (h==="localhost" || h.endsWith(".local")) throw new Error("Local hosts are not allowed");
  const resolved=await dns.lookup(h,{all:true});
  if (!resolved.length || resolved.some(x=>isPrivateIp(x.address))) throw new Error("Private/reserved network targets are not allowed");
  return u;
}

function pick(html,re){
  const m=html.match(re); return m ? String(m[1]||"").replace(/\s+/g," ").trim().slice(0,500) : "";
}
function count(html,re){ return (html.match(re)||[]).length; }
function auditHtml(url,status,headers,html,ms){
  const title=pick(html,/<title[^>]*>([\s\S]*?)<\/title>/i);
  const metaDescription=pick(html,/<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)["'][^>]*>/i)
    || pick(html,/<meta[^>]+content=["']([^"']*)["'][^>]+name=["']description["'][^>]*>/i);
  const h1=count(html,/<h1\b/gi), h2=count(html,/<h2\b/gi);
  const forms=count(html,/<form\b/gi), links=count(html,/<a\b/gi), images=count(html,/<img\b/gi);
  const hasViewport=/<meta[^>]+name=["']viewport["']/i.test(html);
  const hasCanonical=/<link[^>]+rel=["'][^"']*canonical/i.test(html);
  const hasSchema=/application\/ld\+json/i.test(html);
  const hasPhone=/(tel:|\+?\d[\d\s().-]{7,}\d)/i.test(html);
  const hasEmail=/(mailto:|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i.test(html);
  const hasCTA=/(book|buy|start|contact|quote|demo|subscribe|sign up|join|get started)/i.test(html);
  const checks=[
    ["https",url.startsWith("https://")],
    ["http_2xx",status>=200&&status<300],
    ["title_present",!!title],
    ["meta_description_present",!!metaDescription],
    ["exactly_one_h1",h1===1],
    ["viewport_present",hasViewport],
    ["canonical_present",hasCanonical],
    ["structured_data_present",hasSchema],
    ["contact_signal",hasPhone||hasEmail],
    ["conversion_cta_signal",hasCTA],
    ["response_under_2500ms",ms<2500]
  ];
  const score=Math.round(100*checks.filter(x=>x[1]).length/checks.length);
  const opportunities=[];
  if(!title) opportunities.push("Add a descriptive HTML title.");
  if(!metaDescription) opportunities.push("Add a useful meta description.");
  if(h1!==1) opportunities.push("Use one clear H1 heading.");
  if(!hasViewport) opportunities.push("Add a mobile viewport meta tag.");
  if(!hasCanonical) opportunities.push("Add a canonical URL.");
  if(!hasSchema) opportunities.push("Consider relevant structured data.");
  if(!(hasPhone||hasEmail)) opportunities.push("Make a contact route obvious.");
  if(!hasCTA) opportunities.push("Add a clear conversion CTA.");
  if(ms>=2500) opportunities.push("Investigate response/performance latency.");
  return {url,status,responseMs:ms,contentType:headers.get("content-type")||"",score,title,metaDescription,
    signals:{h1,h2,forms,links,images,hasViewport,hasCanonical,hasSchema,hasPhone,hasEmail,hasCTA},
    opportunities,checks:Object.fromEntries(checks)};
}

async function runAudit(raw) {
  const u=await safeUrl(raw);
  const ac=new AbortController();
  const timer=setTimeout(()=>ac.abort(),10000);
  const start=Date.now();
  try{
    const res=await fetch(u,{redirect:"follow",signal:ac.signal,headers:{"user-agent":"NovaAuditBot/1.0"}});
    const ms=Date.now()-start;
    const type=res.headers.get("content-type")||"";
    if(!type.includes("text/html")) throw new Error("Target did not return HTML");
    const reader=res.body.getReader(); let chunks=[]; let total=0;
    while(true){
      const {done,value}=await reader.read(); if(done) break;
      total+=value.length; if(total>1_500_000) break; chunks.push(value);
    }
    const html=new TextDecoder().decode(Buffer.concat(chunks.map(v=>Buffer.from(v))));
    return auditHtml(res.url,res.status,res.headers,html,ms);
  } finally { clearTimeout(timer); }
}

const app=express();
app.disable("x-powered-by");
app.use(express.json({limit:"32kb"}));

app.get("/health",(_req,res)=>res.json({ok:true,service:"nova-website-audit",paidMode:!!PAY_TO,price:AUDIT_PRICE}));

app.get("/api/preview",async(req,res)=>{
  try{
    const r=await runAudit(String(req.query.url||""));
    res.json({url:r.url,status:r.status,responseMs:r.responseMs,title:r.title,score:r.score});
  }catch(e){res.status(400).json({error:String(e.message||e)});}
});

if (PAY_TO) {
  const { paymentMiddleware } = await import("@x402/express");
  const { x402ResourceServer, HTTPFacilitatorClient } = await import("@x402/core/server");
  const { ExactEvmScheme } = await import("@x402/evm/exact/server");
  const facilitator=new HTTPFacilitatorClient({url:"https://x402.org/facilitator"});
  const resourceServer=new x402ResourceServer(facilitator);
  resourceServer.register(X402_NETWORK,new ExactEvmScheme());
  await resourceServer.initialize();
  app.use(paymentMiddleware({
    "GET /api/audit":{
      accepts:{scheme:"exact",price:AUDIT_PRICE,network:X402_NETWORK,payTo:PAY_TO},
      description:"Website conversion and technical audit JSON",
      mimeType:"application/json"
    }
  },resourceServer));
  app.get("/api/audit",async(req,res)=>{
    try{res.json(await runAudit(String(req.query.url||"")));}
    catch(e){res.status(400).json({error:String(e.message||e)});}
  });
} else {
  app.get("/api/audit",(_req,res)=>res.status(503).json({error:"Paid mode not configured. Set PAY_TO to an EVM receiver address."}));
}

if (DEV_MODE) app.get("/api/dev-audit",async(req,res)=>{
  try{res.json(await runAudit(String(req.query.url||"")));}
  catch(e){res.status(400).json({error:String(e.message||e)});}
});

app.listen(PORT,"127.0.0.1",()=>console.log(JSON.stringify({ok:true,port:PORT,paidMode:!!PAY_TO,devMode:DEV_MODE})));