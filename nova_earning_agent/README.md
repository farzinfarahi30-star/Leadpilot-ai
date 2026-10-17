# NOVA independent cash-opportunity scout (read-only)

**Mission:** reduce dependence on a phone being online or a ChatGPT conversation staying open. Every six hours a GitHub Action reads three primary public task feeds plus the independent Jobbi index, checks expiry, listed payment evidence, low competition, and obvious disqualifying obligations. It does not contact buyers, accept work, sign transactions, register accounts or claim money. It creates a public GitHub review issue only if a candidate passes conservative filters; repeat candidates are deduplicated.

**Important:** A listed reward, an escrow transaction hash, or an accepted deliverable is not verified income. The linked task must still be checked for genuine funding, payout eligibility, assigned winner/first-come conditions and acceptance, independently. A complete run finding zero candidates is not evidence that no paid opportunities exist elsewhere.

## Inputs

- TaskMarket official open tasks API (winner-only crowdsourced bounties have significant competition).
- Riner official public task feed (only available, first-come, ≥5 USDC listings).
- Task Bounty official public feed (counts only: it does not support safe automatic qualification yet).
- Jobbi public multi-board index (only recent, high-enough-value, escrow-*listed* developer tasks; every listing requires independent verification).

The scout excludes the Agent Bounties board because claim bonds and tasks requiring persuading unrelated maintainers to fund child jobs violate NOVA's zero-upfront-cost gate. On 2026-10-17, the first Jobbi result was screened manually and rejected as not actionable ([triage record](https://github.com/farzinfarahi30-star/Leadpilot-ai/issues/9)).

The scout intentionally excludes marketing/post-to-social requirements, token promotions, account creation, needing a wallet in the advertised deliverable, upfront bonds, high competition and imminent expiry. It is **not** a generalized search engine or bounty earner.

## State and security

- [Workflow](../.github/workflows/nova-funded-task-scout.yml)
- Run: `python -m unittest discover -v -s nova_earning_agent -p 'test_*.py'` then `python nova_earning_agent/scout.py`.
- Outputs: temporary `reports/public-paid-task-scout.json` Action artifact, with feed availability and candidate provenance.
- Alerts: *deduplicated* GitHub issues with "NOVA paid-task candidate" prefix, visible publicly. No customer data or wallet addresses are stored.
- Credentials: **none** for scans. GitHub Actions uses only its ephemeral repository-scoped `GITHUB_TOKEN` to open review issues. No Stripe, email, wallet or exchange key needed.
- Budget: standard public-repository GitHub Actions runners are currently free; third-party feeds may rate-limit or change. Cron may be delayed or automatically disabled after 60 days of repository inactivity.
- If GitHub workflow permissions block issue writing, the job will flag a failure rather than bypassing the gate.
- To stop: disable the `NOVA read-only funded task scout` workflow from GitHub Actions.

**Current revenue:** no new revenue attributable to this scout. It does not deliver paid work by itself.
