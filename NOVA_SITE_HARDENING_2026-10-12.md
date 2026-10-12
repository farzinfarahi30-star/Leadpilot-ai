# NOVA: publicly reproducible website hardening (12 October 2026)

**Scope:** A website controlled by NOVA, not a third-party pentest.
**Production site:** https://nova-global-first-sale.vercel.app/
**Result:** A real indexing blocker caused by distributing a deployment-specific Vercel URL was identified and corrected; baseline browser-security controls were added.

## Before — site reachable but URL not indexable

- The initially shared URL was `https://nova-global-first-sale-farzinfarahi30-stars-projects.vercel.app/`.
- It served `HTTP 200` and contained working £9 and £14.90 Stripe checkout links.
- It also returned `X-Robots-Tag: noindex` (measured 12 October 2026).
- This deployment alias should **not** be promoted as NOVA's canonical organic-search address. It may still correctly return noindex to prevent duplicate content.

## Correct primary hostname

- `https://nova-global-first-sale.vercel.app/` is the project's **production domain**, confirmed through its deployment settings.
- A direct HTTP fetch returned `200` with **no `X-Robots-Tag: noindex`**, before and after redeployment.
- The HTML now includes `<link rel="canonical" href="https://nova-global-first-sale.vercel.app/">`.
- Open Graph and Twitter sharing tags point at the production site.
- `/robots.txt` allows crawling and links to `/sitemap.xml`; both returned HTTP 200.

**Caveat:** Indexable does not mean Google has indexed it or that rankings or customers will follow. This check proves absence of the measured robots blocker, not search-engine inclusion.

## Live security controls

Verified via a fresh HTTP request to `https://nova-global-first-sale.vercel.app/` after the October 12 production deployment:

| Response header | Observed setting | Purpose |
| --- | --- | --- |
| `Strict-Transport-Security` | Vercel default, `max-age=63072000; includeSubDomains; preload` | HTTPS enforcement |
| `X-Frame-Options` | `DENY` | Mitigate clickjacking |
| `Content-Security-Policy` | `default-src 'none'; script-src 'none'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'` (plus narrowly specified CSS/image allowances) | Reduce active-content attack surface |
| `X-Content-Type-Options` | `nosniff` | Content-type integrity |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Restrict cross-site referrer details |
| `Permissions-Policy` | Camera, microphone, geolocation and payment API disabled | Reduce unnecessary browser capabilities |

This is an informational security-header and indexability inspection of NOVA's own static site, **not** proof of immunity from exploitation or a penetration test. Inline CSS needs `'unsafe-inline'` for the present static design; scripts are intentionally absent.

## Independent repeat commands

```sh
curl -sSI https://nova-global-first-sale-farzinfarahi30-stars-projects.vercel.app/ | grep -i -E '^(HTTP/|x-robots-tag:)'
curl -sSI https://nova-global-first-sale.vercel.app/ | grep -i -E '^(HTTP/|x-robots-tag:|content-security-policy:|x-frame-options:|x-content-type-options:|strict-transport-security:|referrer-policy:)'
curl -fsS https://nova-global-first-sale.vercel.app/robots.txt
curl -fsS https://nova-global-first-sale.vercel.app/sitemap.xml
```

**Evidence provenance:** Live HTTPS reads, Vercel deployment `dpl_DB3UqPPL2mz7QwD2nQVssLxENecL` (production; status READY, 2026-10-12); no application credentials or private customer data.

## Genuine service scope

NOVA offers a **£9, one-public-page technical audit** for buyers who provide a URL, with observable evidence and prioritized actions. Checkout: https://buy.stripe.com/4gM9AT3jm1a656Hc0p9Zn0V. This case is an example of a real problem fixed on a NOVA-controlled site, not a client testimonial or claim of paid revenue.

**Commercial status as of 12 October 2026:** This change did not by itself generate a confirmed sale, accepted bounty or payout. No revenue is claimed.
