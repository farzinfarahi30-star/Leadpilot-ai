# NOVA outbound email safety gate (zero-cost)

This standalone Python 3 utility **never connects to Gmail and never sends email**. It prevents separate local workers that share its SQLite database from accidentally reserving the same recipient, enforces a 30-day default cooldown after a confirmed send, and persists do-not-contact records. It uses only the Python standard library.

## Usage

Run from the repository root:

~~~bash
python3 tools/nova_outreach_guard.py suppress 'no-more@example.com' --reason 'explicit opt-out'
python3 tools/nova_outreach_guard.py check 'lead@example.com'
python3 tools/nova_outreach_guard.py reserve 'lead@example.com' --campaign 'website-review' --body-file '/path/to/email.txt'
# If allowed=true, perform a separate FULL Gmail thread/recent-sent/consent check, send in the authorized sender, then:
python3 tools/nova_outreach_guard.py confirm-sent RESERVATION_TOKEN
# If definitely no email was sent, instead:
python3 tools/nova_outreach_guard.py cancel RESERVATION_TOKEN
~~~

## Important limits

- Before enabling any automation, load existing suppression records, existing sent history, and manually confirm current buyer consent / no-follow-up promises. Fresh local databases **do not know** Gmail history. Seed known opt-outs using the suppress command. The check command alone is not safe permission to send; reserve is the atomic step.
- If a send's outcome is unknown, **leave the reservation blocked** until resolved. Never cancel a possibly sent email. Do not interpret a request to review as permission to solicit repeatedly.
- All senders need to share the **same SQLite database on one device or host**. Independent cloud devices with separate SQLite copies are **not protected across each other**; use a centralized transactional store before enabling distributed outreach.
- This guard is for **unsolicited outbound sales**, not legitimate replies to fresh inbound customer requests. Handle those separately with thread-specific human-reviewed policies.
- Test: python3 -m unittest discover -s tests -p 'test_nova_outreach_guard.py' -v

No revenue, deliveries, or inbox protection are claimed merely by installing this library. Existing workflows must explicitly integrate it. This tool is not a substitute for legal compliance or unsubscribe handling.
