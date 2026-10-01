# Nova Website Audit API — Cloudflare Worker

Stable Nova-owned edge deployment for RapidAPI.

Routes:
- GET /health
- GET /openapi.json
- POST /api/audit/rapid
- POST /api/audit

Request body:

{"url":"https://example.com"}

The Worker blocks obvious localhost/private literal targets, credential-bearing URLs, non-HTTP(S) URLs, non-HTML responses and HTML bodies above 2 MB.

If a RAPID_PROXY_SECRET Worker secret is added later, /api/audit and /api/audit/rapid will require RapidAPI's x-rapidapi-proxy-secret header.
