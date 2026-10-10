# NOVA bounty execution log — 2026-10-10

## Work actually executed

- Re-verified official bug bounty programme terms and reward structures for **Twyne**, **Enzyme Onyx**, **DAWN USD.infra Vault**, **GMTrade**, and **Hermetica**.
- Reviewed 6 open-source Solidity contracts in `0xTwyne/twyne-contracts-v1`: `src/twyne/CollateralVaultBase.sol`, `src/twyne/VaultManager.sol`, `src/twyne/AaveV3CollateralVault.sol`, `src/twyne/EulerCollateralVault.sol`, `src/twyne/MorphoCollateralVault.sol`, and `src/TwyneFactory/CollateralVaultFactory.sol`. Focus: owner/operator checks, collateral movement, liquidation, oracle conversions, credit accounting, snapshot invariants.
- Reviewed 3 explicitly scoped Enzyme Onyx files at immutable commit `7b48d243f505b362cd6f1fcf723c21bc8b047c06`: `SharesBurnHandler.sol`, `AddressListsSharesTransferValidator.sol`, `ChainlinkAceSharesTransferValidator.sol`.
- Independently recreated the core arithmetic cases of Twyne's `collateralForBorrower()` in an offline Python model and tested **50,000** randomized scenarios. The tested bounds, equity, and monotonicity properties all passed. **This is a narrow math sanity test, not a contract PoC, audit certificate, or proof of absence of bugs.**
- Built a standard-library-only offline bounty triage script with **5 passing unit tests**, delivered separately as `NOVA_Bounty_Execution_2026-10-10.zip` in the chat. The CSV input is `data/NOVA_WEB3_BUG_BOUNTIES_ALL_2026-10-10.csv`.

## Priorities for actually obtaining a reward

| Priority | Bounty | Maximum advertised | Minimum or lower-severity rewards | Required to submit |
|---|---|---|---|---|
| 1 | [Enzyme Onyx](https://immunefi.com/bug-bounty/enzyme-onyx/information/) | $200,000 | Medium: $1,000 | Match production code, distinguish excluded audit/role/config risks, reproduce on local fork |
| 2 | [Twyne](https://immunefi.com/bug-bounty/twyne/information/) | $50,000 | High: $3,000 | In-scope high/critical impact, deployed-code check, local-fork PoC |
| 3 | [DAWN USD.infra](https://immunefi.com/bug-bounty/dawn/information/) | $50,000 | Low: $1,000; Medium: $2,000 | In-scope Solana/web asset and genuine reproducible flaw |
| 4 | [GMTrade](https://immunefi.com/bug-bounty/gmtrade/information/) | $100,000 | Medium: $1,000 | Rust/Solana executable PoC, known-issue exclusions, treasury cap |
| 5 | [Hermetica](https://immunefi.com/bug-bounty/hermetica/information/) | $100,000 | High: $1,000 | Clarity/hBTC reproduction, prior-audit exclusion |

All five say **KYC not required for payout processing**, but platform/identity requirements must be checked before submission. All reward amounts are advertised eligibility ceilings/ranges, not income predictions.

## Evidence / completion

- Distinct programme entries in earlier saved 2-platform dataset: **556**, including **320 public live** at snapshot time.
- Reward-eligible vulnerabilities newly established: **0**.
- Official reports submitted: **0** (there is no sound reproducible finding yet).
- Crypto bounty payments received: **$0 confirmed**.
- No live exploits, mainnet/testnet testing, wallet signing, transfers, nor private/public disclosures performed.

Research will only count a successful bounty after a novel, in-scope flaw is established and sponsor pays. Submit privately via the official platform, with a legitimate local-fork proof and no prohibited attacks. Programme conditions and availability may change.
