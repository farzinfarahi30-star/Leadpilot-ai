# NOVA Website Technical Audit — Sample Report Extract

**Example client:** NOVA's own website (not a paying customer)  
**Historical inspection date:** 12 October 2026  
**Page:** `https://nova-global-first-sale.vercel.app/`  
**Scope:** One public homepage and a limited set of related technical endpoints.

This is a transparent **sample of the evidence-and-recommendation format** used in NOVA's £9 one-page technical audit. It does **not** represent a current scan or a client testimonial. Findings below come from NOVA's recorded tests on 12 October 2026; they are not claims about today's live site.

## Evidence and findings

| Check | Recorded observation | Assessment |
| --- | --- | --- |
| HTTP response on production hostname | Homepage returned HTTP 200 on 12 Oct | Accessible at test time |
| Robots header on initial deployment-specific alias | `X-Robots-Tag: noindex` was present | Do not promote that alias as the canonical organic-search URL |
| Robots header on production hostname | No `X-Robots-Tag: noindex` observed | This particular indexing blocker was absent at test time |
| Canonical | HTML pointed to `https://nova-global-first-sale.vercel.app/` | Consistent with intended production URL |
| robots.txt and sitemap.xml | Both returned HTTP 200 | Basic discovery endpoints were available |
| Frame protection | `X-Frame-Options: DENY` | Clickjacking mitigation configured |
| MIME sniffing | `X-Content-Type-Options: nosniff` | Protective response header configured |
| Content Security Policy | A restrictive CSP was observed | Reduce exposure to unapproved active content |

### Priority 1 — Use the correct public URL

**Issue:** A deployment-specific hostname was distributed while it returned a `noindex` header. Sharing a technically accessible URL is not the same as sharing the right URL for search discovery.

**Recommendation:** Use the production hostname consistently in marketing, link previews and canonical tags. Recheck response headers after each change.

**Verification:** On 12 October, the production homepage returned HTTP 200 without the measured `X-Robots-Tag: noindex` blocker. This does **not** prove search-engine indexing.

### Priority 2 — Keep discovery signals consistent

**Issue to monitor:** Robots rules, sitemap URLs and canonical markup can drift across deployments.

**Recommendation:** Validate `robots.txt`, `sitemap.xml` and the homepage canonical together whenever the primary host changes. They should point to the intended public website.

### Priority 3 — Preserve secure defaults

**Issue to monitor:** New scripts, embedded forms and external tools can require CSP changes.

**Recommendation:** Restrict permissions to services actually used, maintain HTTPS and protective headers, and test legitimate interactive features after CSP edits. A header check is not a penetration test.

## What the £9 customer report covers

For one public webpage URL supplied at checkout, NOVA checks available HTTP responses, title/description, canonical/robots/language signals, heading and link structure, image alt attributes, viewport/preview metadata, structured-data presence and selected security headers. The report explains observations, prioritises practical fixes and includes a transparent **heuristic**, not an independently certified score.

The actual findings depend on what the customer's page exposes at review time. Customer credentials are not required; we do not scan private infrastructure or claim to audit an entire website.

**Price:** £9 one-time. **[Order a one-page NOVA Website Technical Audit](https://buy.stripe.com/4gM9AT3jm1a656Hc0p9Zn0V)**

*This sample describes work performed on NOVA's own property. It does not imply a sale, client result, ranking improvement or guaranteed business outcome. Source notes: [12 October 2026 website-hardening evidence](./NOVA_SITE_HARDENING_2026-10-12.md).*
