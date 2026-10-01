export default {
  async fetch(request) {
    const url = new URL(request.url);
    const headers = {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer"
    };
    if (request.method === "GET" && url.pathname === "/health") {
      return new Response(JSON.stringify({ok:true,service:"Nova Website Audit Worker",version:"1.0.0"}), {headers});
    }
    if (request.method !== "POST" || url.pathname !== "/api/audit") {
      return new Response(JSON.stringify({error:"Not found"}), {status:404,headers});
    }
    let body;
    try { body = await request.json(); } catch { return new Response(JSON.stringify({error:"JSON body required"}),{status:400,headers}); }
    if (typeof body?.url !== "string" || body.url.length > 2048) return new Response(JSON.stringify({error:"Provide url"}),{status:400,headers});
    let target;
    try { target = new URL(body.url); } catch { return new Response(JSON.stringify({error:"Invalid URL"}),{status:400,headers}); }
    if (!["http:","https:"].includes(target.protocol) || target.username || target.password) return new Response(JSON.stringify({error:"Only public http/https URLs without credentials are allowed"}),{status:400,headers});
    const h=target.hostname.toLowerCase();
    if (h==="localhost" || h.endsWith(".local") || /^127\./.test(h) || /^10\./.test(h) || /^192\.168\./.test(h) || /^169\.254\./.test(h) || /^172\.(1[6-9]|2\d|3[01])\./.test(h)) return new Response(JSON.stringify({error:"Private/local targets are not allowed"}),{status:400,headers});
    const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),10000);
    let res;
    try { res=await fetch(target.toString(),{redirect:"follow",signal:controller.signal,headers:{"user-agent":"NovaWebsiteAudit/1.0"}}); }
    catch(e){ clearTimeout(timer); return new Response(JSON.stringify({ok:false,error:e?.name==="AbortError"?"Target timed out":"Target fetch failed"}),{status:422,headers}); }
    clearTimeout(timer);
    const ct=res.headers.get("content-type")||"";
    if(!ct.includes("text/html")) return new Response(JSON.stringify({ok:false,error:"Target is not HTML"}),{status:422,headers});
    const html=(await res.text()).slice(0,2000000);
    const count=(re)=>(html.match(re)||[]).length;
    const extract=(re)=>html.match(re)?.[1]?.replace(/\s+/g," ").trim()||"";
    const meta=(name)=>extract(new RegExp('<meta[^>]+(?:name|property)=["\\\']'+name+'["\\\'][^>]+content=["\\\']([^"\\\']*)["\\\']','i'))||extract(new RegExp('<meta[^>]+content=["\\\']([^"\\\']*)["\\\'][^>]+(?:name|property)=["\\\']'+name+'["\\\']','i'));
    const out={ok:true,inputUrl:target.toString(),finalUrl:res.url,checkedAt:new Date().toISOString(),http:{status:res.status,contentType:ct},seo:{title:extract(/<title[^>]*>([\s\S]*?)<\/title>/i),metaDescription:meta("description"),robots:meta("robots")},structure:{h1Count:count(/<h1\b[^>]*>/gi),h2Count:count(/<h2\b[^>]*>/gi),imageCount:count(/<img\b[^>]*>/gi),linkCount:count(/<a\b[^>]*href\s*=/gi)},mobile:{viewport:meta("viewport")},social:{openGraphTitle:meta("og:title"),openGraphImage:meta("og:image")},structuredData:{jsonLdCount:count(/<script[^>]+type=["']application\/ld\+json["'][^>]*>/gi)},security:{strictTransportSecurity:res.headers.get("strict-transport-security"),contentSecurityPolicy:res.headers.get("content-security-policy")}};
    return new Response(JSON.stringify(out),{headers});
  }
};