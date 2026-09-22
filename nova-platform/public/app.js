
const $=s=>document.querySelector(s),content=$("#content");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const staticMode = location.hostname.includes("jsdelivr.net") || location.hostname.includes("githubusercontent.com") || location.hostname.includes("github.io");
const localKey="nova-platform-local-state-v1";
const localDefault={projects:[],providers:[{id:"local",name:"Nova Local Runtime",kind:"runtime",status:"ready",external:false},{id:"cloudflare",name:"Cloudflare Runtime Adapter",kind:"hosting",status:"active",external:true},{id:"github",name:"GitHub Source Adapter",kind:"source",status:"active",external:true}],audit:[]};
function localState(){try{return JSON.parse(localStorage.getItem(localKey))||localDefault}catch{return localDefault}}
function saveLocal(s){localStorage.setItem(localKey,JSON.stringify(s))}
async function api(path,opts){
  if(staticMode){
    const s=localState();
    if(path==="/health") return {ok:true,platform:"Nova Platform",version:"0.2.0",mode:"static_portable_frontend",vendor_lock_in:false,stateful:false,runtime:"portable frontend"};
    if(path==="/platform") return {name:"Nova Platform",version:"0.2.0",mode:"static_portable_frontend",projects:s.projects.length,providers:s.providers,storage:"browser localStorage (static preview)"};
    if(path==="/projects" && (!opts || opts.method==="GET")) return s.projects;
    if(path==="/providers") return s.providers;
    if(path==="/audit") return s.audit;
    if(path==="/projects" && opts?.method==="POST"){const b=JSON.parse(opts.body||"{}"),p={id:"proj_"+Date.now(),name:String(b.name||"Untitled Project"),description:String(b.description||""),status:"draft",files:1,deployments:0};s.projects.unshift(p);s.audit.unshift({action:"project.create",detail:{projectId:p.id,name:p.name},createdAt:new Date().toISOString()});saveLocal(s);return p}
  }
  const r=await fetch("/api"+path,opts);const j=await r.json();if(!r.ok)throw new Error(j.error||"request failed");return j
}
async function overview(){
  const [p,pr,h]=await Promise.all([api("/platform"),api("/projects"),api("/health")]);
  content.innerHTML='<div class="grid">'+
    '<div class="card"><div class="kicker">Runtime</div><div class="value">'+(staticMode?"Browser":"Edge")+'</div><div class="sub">'+(staticMode?"portable public frontend":"Nova-owned control plane")+'</div></div>'+
    '<div class="card"><div class="kicker">Projects</div><div class="value">'+pr.length+'</div><div class="sub">'+(staticMode?"browser-local state":"persistent state")+'</div></div>'+
    '<div class="card"><div class="kicker">Providers</div><div class="value">'+p.providers.length+'</div><div class="sub">adapters, not the core</div></div>'+
    '<div class="card"><div class="kicker">Lock-in</div><div class="value">OFF</div><div class="sub">portable source + state model</div></div>'+
  '</div><div class="section"><h2>Independent deployment</h2><div class="rows">'+
    '<div class="row"><span>Hatchable</span><span class="pill ready">not required</span></div>'+
    '<div class="row"><span>AppDeploy</span><span class="pill ready">not required</span></div>'+
    '<div class="row"><span>State persistence</span><span class="pill ready">'+(staticMode?"browser localStorage":"Durable Object")+'</span></div>'+
    '<div class="row"><span>API health</span><span class="pill ready">'+(h.ok?"healthy":"degraded")+'</span></div>'+
  '</div></div>';
}
async function projects(){
  const pr=await api("/projects");
  content.innerHTML='<div class="actions"><button class="btn primary" id="new">Create project</button></div><div class="section rows">'+
    (pr.length?pr.map(p=>'<div class="row"><div><b>'+esc(p.name)+'</b><div class="sub">'+esc(p.description)+'</div></div><span class="pill ready">'+esc(p.status)+' · '+p.files+' files · '+p.deployments+' deploys</span></div>').join(""):'<div class="empty">No projects yet.</div>')+
  '</div>';
  $("#new").onclick=async()=>{const name=prompt("Project name");if(!name)return;try{await api("/projects",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({name,description:"Nova-managed project"})});await projects()}catch(e){alert(e.message)}}
}
async function providers(){const ps=await api("/providers");content.innerHTML='<div class="rows">'+ps.map(p=>'<div class="row"><div><b>'+esc(p.name)+'</b><div class="sub">'+esc(p.kind)+' · '+(p.external?"external adapter":"Nova-owned")+'</div></div><span class="pill '+(p.status==="ready"||p.status==="active"?"ready":"")+'">'+esc(p.status)+'</span></div>').join("")+'</div>'}
async function rules(){content.innerHTML='<div class="card"><div class="kicker">Standing agent rule</div><h2>External services are adapters, never the core.</h2><p class="sub">When a provider hits a quota, lock-in, plan restriction or outage, Nova switches to the self-hosted/portable lane and records the blocker instead of treating the vendor as permanent infrastructure.</p><div class="section rows"><div class="row"><span>Keep source + state portable</span><span class="pill ready">required</span></div><div class="row"><span>No fabricated live metrics</span><span class="pill ready">required</span></div><div class="row"><span>External resources still require authorization</span><span class="pill warn">human gate</span></div></div></div>'}
async function audit(){const a=await api("/audit");content.innerHTML='<div class="rows">'+(a.length?a.map(x=>'<div class="row"><div><b>'+esc(x.action)+'</b><div class="sub">'+esc(JSON.stringify(x.detail))+'</div></div><span class="pill">'+new Date(x.createdAt).toLocaleString()+'</span></div>').join(""):'<div class="empty">No audit entries yet.</div>')+'</div>'}
async function show(page){$("#title").textContent=page[0].toUpperCase()+page.slice(1);try{await ({overview,projects,providers,rules,audit}[page]||overview)()}catch(e){content.innerHTML='<div class="empty">Unable to load this view: '+esc(e.message)+'</div>'}}
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll("nav button").forEach(x=>x.classList.remove("active"));b.classList.add("active");show(b.dataset.page)});
api("/health").then(x=>$("#health").textContent=x.ok?(staticMode?"● public · portable":"● healthy · independent"):"● degraded").catch(()=>$("#health").textContent="● offline");show("overview");
