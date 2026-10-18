# Nova Mail

Nova Mail is the Factory's self-owned email layer. It reproduces the useful public behavior of an AI email MCP without depending on Superhuman.

## Included

- Gmail and Outlook mailbox search
- Read Gmail threads / Outlook messages
- Gmail draft creation
- Approved email sending
- Approved scheduled sends
- Provider response evidence
- MCP tools for AI assistants

## Providers

Gmail can use a short-lived access token or a refresh-token flow:
GMAIL_ACCOUNT
GMAIL_FROM
GMAIL_ACCESS_TOKEN OR GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET + GMAIL_REFRESH_TOKEN

Outlook can use:
OUTLOOK_ACCESS_TOKEN OR OUTLOOK_CLIENT_ID + OUTLOOK_CLIENT_SECRET + OUTLOOK_REFRESH_TOKEN

Credentials must live in encrypted runtime secrets, never in source control.

## Safety

Actual sending requires approved=true inside the mail service. A draft, database row, provider dashboard entry, or simulated response is never treated as proof of delivery.

## Scope

This package is intentionally email-only. No advertising, calendar, CRM, browser automation, business generation, or other product logic belongs here.


## Outreach protection (October 2026)

All `mail_send` calls default to `purpose: "outreach"`. To avoid duplicate pitches, the send path now:
- checks the **actual Gmail Sent folder** for a message to that recipient within the last seven days, including messages sent from other chats or through the Gmail app;
- enforces a seven-day per-recipient cooldown in a persistent on-disk ledger;
- checks Gmail for bounce notices (Delivery Status Notification / Undeliverable) naming that destination address in the last 90 days and blocks repeat outreach pending address verification;
- blocks multi-recipient, Cc and Bcc sales messages;
- blocks permanently suppressed contacts from `NOVA_MAIL_SUPPRESSED_RECIPIENTS` (comma-separated runtime secret) or an optional JSON array at `NOVA_MAIL_SUPPRESSION_FILE`;
- records failed or timed-out provider calls as **uncertain**, not safe to retry automatically through the xx fallback.

By default the ledger is `./status/nova-mail-ledger.json` and suppression file is `./status/nova-mail-suppressions.json`, relative to the **service working directory**. Keep these paths on persistent private storage across restarts; do not commit recipient records or credentials. The ledger stores recipient addresses, timestamps, content fingerprints, and delivery states, but not message bodies. Missing optional suppression file means no file-based permanent holds; **explicit opt-outs must be entered** into the runtime suppression list. Never remove an opt-out just because a cooldown expired.

Gmail read credentials are required even if the actual send provider is Resend or Outlook, because cross-chat Sent-history verification is mandatory for outreach. If Gmail checking, storage, or a lock fails, the sales send **fails closed**. `purpose: "transactional"` is reserved for genuine nonmarketing operational messages; it deliberately bypasses the sales cooldown, not the existing `approved: true` gate. Do not label sales follow-ups transactional to bypass a hold. This guard applies only to sends that pass through Nova Mail; other external sending tools need their own safeguards.

Run offline regression tests: `cd nova-mail && npm test`. Tests use temporary directories and mock providers; **no email is sent**.

## Outbound contact and duplicate-send safety

`sendEmail` is approval-gated. Outreach (`purpose: 'outreach'`, also the default)
additionally needs one valid recipient, a clear Gmail Sent-history check, and a
local serialized ledger that blocks repeat contact for seven days. A provider
timeout or uncertain delivery remains held until a human checks the provider.

**Explicit no-follow-up holds** for BESTEIGEN and WordyKid are enforced
for To, Cc and Bcc, including transactional sends and new scheduled queue items.
Only remove these holds after reviewing a new substantive request from the
recipient. Additional suppressed addresses can be specified with
`NOVA_MAIL_SUPPRESSED_RECIPIENTS` (comma/semicolon-separated) or the
`NOVA_MAIL_SUPPRESSION_FILE` JSON list for outreach.

The local state defaults to `./status/nova-mail-ledger.json` and
`./status/nova-mail-suppressions.json`; override paths with
`NOVA_MAIL_LEDGER_FILE` and `NOVA_MAIL_SUPPRESSION_FILE`. All NOVA Mail
worker processes must use the **same persistent volume** for the ledger and
lock. If a lock persists after a crash, verify the provider Sent history and
the ledger before removing it manually; never blindly replay an uncertain
send. These safeguards are fail-closed and may also suppress legitimate rapid
back-and-forth messages, requiring a human review.

Test without credentials, network calls or real sends:

```sh
npm run smoke:outreach
```

This is a guard only for mail routed through **Nova Mail**. It does not
automatically prevent emails sent directly by ChatGPT's Gmail connector,
Hatchable, Resend dashboards, or any other independent system. Such senders
must implement their own suppression/Sent-history check and should not be
assumed synchronized with the local ledger. Scheduled-message dispatchers
must route through `sendEmail` so the final send is rechecked.
