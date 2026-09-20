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
