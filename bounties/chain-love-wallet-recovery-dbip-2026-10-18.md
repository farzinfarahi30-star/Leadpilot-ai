# Chain.Love DBIP submission — documented wallet recovery methods

**Status:** draft ready to submit. **Not submitted to Chain.Love** — the installed GitHub integration denied external issue creation (HTTP 403). **No prize earned.** Evidence checked 2026-10-18.

**Official $10 USDC DBIP approval program:** https://github.com/Chain-Love/chain-love/discussions/41
**Intake:** https://github.com/Chain-Love/chain-love/issues/new/choose
**Original schema:** https://github.com/Chain-Love/chain-love/blob/main/references/offers/wallets.csv

## Issue title

[DBIP] Add documented wallet recovery methods without inferring them from custody or key export

## Proposal type

Add column — wallet recovery mechanisms, scoped to documented product/configuration behavior.

## Affected scope

`references/offers/wallets.csv` (new nullable canonical offer field); corresponding `listings/all-networks/wallets.csv`, `listings/specific-networks/*/wallets.csv`, and wallet schema/column-definition documentation only after approval.

## Motivation / problem statement

The current canonical wallets.csv header includes `custodial,mfa,msig,hardware,keyExport`, but none distinguishes *how an owner restores access after device loss*. The existing `metamask` offer has `custodial=FALSE` and `keyExport=TRUE`, yet its official documentation now distinguishes SRP restoration and Google/Apple/Telegram account-linked backup/recovery, with different prerequisites. Argent official documentation separately describes guardian-assisted and off-chain encrypted-backup recovery for supported wallets/configurations. The difference cannot be reliably inferred from `custodial`, `msig`, or `keyExport`.

**First-party evidence (verified 2026-10-18):**
- https://support.metamask.io/configure/wallet/using-the-same-metamask-wallet-on-multiple-devices
- https://support.metamask.io/start/learn/what-is-a-secret-recovery-phrase-and-how-to-keep-your-crypto-wallet-secure
- https://www.argent.xyz/blog/off-chain-recovery
- https://www.argent.xyz/learn/what-is-social-recovery

These sources document recovery pathways; **they do not prove that every wallet version, user configuration, or chain has every option**.

## Detailed proposal

**Category/table:** wallets

**Column:** `recoveryMethods` (new; optional)

**Type:** JSON array of normalized enum strings, using the existing serialized-array convention in wallet CSVs. Suggested values:

- `secret-recovery-phrase` — restore access using a user-controlled SRP/mnemonic.
- `encrypted-cloud-backup` — restore access with documented encrypted online backup and required credentials.
- `guardian-assisted` — authorized guardians or thresholds explicitly supported by the named wallet/configuration.
- `provider-account-recovery` — custodian-assisted restoration of account *login*; never claim the provider can recover self-custodial keys without evidence.
- `hardware-device-backup` — restoration via a documented hardware-backed seed/backup workflow; not merely hardware-wallet connectivity.

NULL/empty = not independently verified, **not** a claim of no recovery mechanism. Several enum values may coexist; non-null values require first-party source and qualification of supported version, wallet type and setup prerequisites.

**Illustrative data semantics, not bulk-approved edits:** `metamask` may support `secret-recovery-phrase` and `encrypted-cloud-backup` for different onboarding routes; only mark the latter with qualification. If Argent is present as a future verified canonical wallet offer, `guardian-assisted` and `encrypted-cloud-backup` would need to be checked per supported wallet/version.

**Rollout and validation:** Schema nullable by default; add defined enum whitelist; document recovery-source evidence in the contributor PR; reject unknown enum strings; preserve NULL; check JSON-array parsing and canonical/listing inheritance. Never request or store user SRPs, private keys, 2FA codes or contact information.

**Scope vs earlier DBIPs:** #3725 concerns **key export formats**; #4055 concerns **smart-account / account abstraction support**. Neither specifies recovery workflows. This DBIP does not propose changing those fields.

## Contact

GitHub @farzinfarahi30-star. Research AI-assisted and clearly disclosed.

## Rewards address (optional)

Omitted. A user-controlled Ethereum-mainnet payout address can be added by the account owner at the official submission/approval stage if requested. Do not invent a receiving address. The program pays only if the maintainers approve, at their discretion, and acceptance/payment has not occurred.

---

**One remaining manual gate:** account owner opens [the official DBIP issue intake](https://github.com/Chain-Love/chain-love/issues/new/choose) and submits the proposal above. GitHub integration write permission to external repository was tested and failed (403). No other action or payment is claimed.
