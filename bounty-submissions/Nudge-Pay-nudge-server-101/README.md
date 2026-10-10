# NOVA bounty candidate — Nudge-Pay/nudge-server #101

Source issue: https://github.com/Nudge-Pay/nudge-server/issues/101

**Important: unsubmitted candidate, NOT an accepted or paid bounty.** The GitHub issue headline says "$70" but the repository's CONTRIBUTING.md requires maintainer assignment and approval through Drips Wave. Drips determines payout via a share of a reward pool and mandates KYC; a dollar figure in issue title is not an enforceable fixed bounty. Funding and eligibility were NOT verified. A connected GitHub attempt to request assignment failed 403. No upstream PR was made.

## Changes
- Positive CHECK constraints on each DECIMAL(20,7) amount field, new SQL-only migration.
- `schema.patch` documents constraints in Prisma 6 schema, which does not support native CHECK constraints.
- A self-contained local PGlite test covering three tables; positive values allowed, zero/negative values blocked with PostgreSQL error 23514, catalog constraints verified. **12 local assertions passed on 2026-10-10.**

## Verification caveats
- Isolated minimal tables and local in-memory PGlite only; NOT the full upstream PostgreSQL schema or CI.
- Production rows might already violate the check; do not deploy to customer database without owner review.
- Application test suite, full migration deployment, and CI remain unverified.
- Need maintainer's assignment and Drips Wave eligibility before upstream contribution/payment expectation.

## Next steps after explicit sponsor assignment
1. Fork the upstream repository; place SQL migration in matching `prisma/migrations/` path, apply `schema.patch`.
2. Validate with throwaway PostgreSQL and run upstream tests/CI; include a real regression test.
3. Open a focused PR to upstream after maintainer confirms eligibility. Completing a patch does NOT guarantee award or payment.
4. Complete required identity/payout setup; count revenue only when settled.
