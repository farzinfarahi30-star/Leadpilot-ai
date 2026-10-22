# Nova Website Audit API

A reusable website-audit API designed for multiple monetization channels:
- x402 pay-per-call
- RapidAPI
- later wrappers for Bubble, WordPress, Google Workspace, monday.com, Wix and GitHub Marketplace

## Endpoints
- `GET /health`
- `GET /api/preview?url=https://example.com`
- `GET /api/audit?url=https://example.com` — x402-protected when `PAY_TO` is configured
- `GET /api/dev-audit?url=https://example.com` — local development only when `DEV_MODE=1`

## Local test
```bash
npm install
DEV_MODE=1 node server.mjs
curl 'http://127.0.0.1:8879/api/dev-audit?url=https://example.com'
```

## Paid mode
```bash
PAY_TO=0xYOUR_PUBLIC_RECEIVER_ADDRESS AUDIT_PRICE='$0.05' X402_NETWORK='eip155:8453' node server.mjs
```

No private wallet key is required when a public receiver address is supplied.

## Security
The API rejects localhost/private/reserved network targets, rejects credentials embedded in URLs, caps response size, and times out outbound fetches.

## Revenue rule
Test calls, testnet payments and pending balances are not revenue. Count only externally settled customer payments.
