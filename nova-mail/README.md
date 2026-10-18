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


## Anti-duplicate outbound preflight (Gmail-backed)

Approved ordinary sends through `sendEmail` and the `mail_send` tool now check the Gmail account's **latest sent and incoming message** for the recipient immediately before sending. A message is blocked when:

- any matching Gmail message, including older conversation history, carries a label indicating a decline, opt-out, or outreach hold (for example, `NOVA / Declined - do not pitch`, `Cold Outreach / Do Not Contact`, or `NOVA / Pause outreach - awaiting reply`);
- there was an outbound message within the preceding seven days and no newer inbound reply;
- the message has multiple or invalid recipients, or a simultaneous send to the same recipient is in progress within this Node process;
- Gmail history/label verification is unavailable. This fails closed without retrying on an alternate transport.

One-to-one verified replies after new inbound messages are permitted unless a hold label remains. To resume a held conversation, review the entire thread and remove its hold label only when appropriate. **Never interpret a friendly acknowledgement as consent to repeated sales pitches.**

All non-transactional sends, including sends through Resend or Outlook, require valid Gmail read credentials for this history preflight. Only **trusted internal code** may deliberately pass `purpose:'transactional'` for legitimate receipts and non-marketing service messages; the MCP tool does not expose this override. Explicit `approved:true` is still always required.

These protections apply **only to Nova Mail code paths**. They do not intercept direct sends from Gmail, ChatGPT connectors, external automations, other Gmail accounts, or separate running Nova Mail processes. Concurrent sends across processes can still race; a shared durable lock would be needed for stronger multi-process guarantees. A 7-day cooldown is not permission to contact a recipient who opted out; keep decline labels in place. The history scan is read-only and does not guarantee deliverability or buyer interest.

Offline regression tests: `node --test src/outreach-guard.test.mjs` (10 synthetic checks verified on Node.js 22; no emails sent). Searches of historic labelled messages increase Gmail API reads per attempted send.
