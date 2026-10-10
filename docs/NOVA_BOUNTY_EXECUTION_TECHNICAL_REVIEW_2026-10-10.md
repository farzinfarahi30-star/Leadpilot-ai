# NOVA bounty execution: first technical review — 2026-10-10

## Goal and verified state

Goal: earn **actual accepted vulnerability rewards** in an authorized bug bounty, paid through the program's normal payout mechanism (often USDC/ETH). No live exploitation, stolen funds, or fabricated findings.

Data inventory already completed: 556 Immunefi/HackenProof public directory entries; 320 live public entries across these two directories. Source index: [NOVA WEB3 directory](NOVA_WEB3_BOUNTY_DIRECTORY_2026-10-10.md).

**Important:** A directory entry is not an audited contract. This document records actual source review, not 320 claimed security audits.

### Sources reviewed

1. **Twyne**: [official programme](https://immunefi.com/bug-bounty/twyne/information/), [scope](https://immunefi.com/bug-bounty/twyne/scope/); USDC, advertised critical max $50,000, no KYC, PoC required. [GitHub](https://github.com/0xTwyne/twyne-contracts-v1). Reviewed new Morpho operator sources and `MorphoCollateralVault.sol`, `CollateralVaultBase.sol`, `CollateralVaultFactory.sol`, `AssetZap.sol`.
2. **Hashflow**: [official programme](https://immunefi.com/bug-bounty/hashflow/information/), [scope](https://immunefi.com/bug-bounty/hashflow/scope/); advertised max $50,000, no KYC, PoC required. Reviewed public `hashflownetwork/x-protocol` `HashflowWormholeMessenger.sol` and `HashflowPool.sol` *as leads*; in-scope deployed bytecode still needs exact source/contract matching.
3. **Charm**: [official programme](https://immunefi.com/bug-bounty/charm/information/), [scope](https://immunefi.com/bug-bounty/charm/scope/); current advertised max **$6,000** (an older Immunefi snapshot showed $20,000; use CURRENT figure), no KYC, PoC required. Reviewed all three explicitly listed `charmfinance/alpha-vaults-v2-contracts` contracts: `CloneFactory.sol`, `AlphaProVaultFactory.sol`, `AlphaProVault.sol`.

### Checks executed and outcomes

- Twyne `MorphoCollateralVault.splitCollateralAfterExtLiq` and `CollateralVaultBase.collateralForBorrower`: reconstructed relevant integer arithmetic in the accompanying **offline Python test model**; 200,000 seeded randomized scenarios and collateral-conservation checks **passed**. This is NOT a fork test or an assertion of the absence of all vulnerabilities.
- Twyne callback review: initially considered unauthorized direct invocation of `MorphoLeverageOperator.onMorphoFlashLoan`; excluded the simple proposed trigger after checking **Morpho Blue's official implementation**: Morpho directs the flashloan callback to `msg.sender` of `flashLoan`, not to an arbitrary external receiver. For an outsider to call the protected operator's callback through Morpho, they would have to trigger the operator itself. No outsider-accessible exploit proven.
- Twyne prior known issue screen: searched public reports and changes. A third-party May 2026 Aave V3 callback report exists; do not re-submit an issue simply because its bug class resembles one in a different module. Compared Twyne commit `0aa37b02fca27025a049daf0d7ec31b94f1810eb` with `main` through GitHub API. The current branch has additional Morpho modules and changed factory/vault source; neither code added to the repo nor a theory constitutes a live deployed vulnerability. Verify deployed scope before deeper testing.
- Hashflow Wormhole cross-chain message replay lead: `HashflowPool.fillXChain` contains `_filledXChainTxids[txid]` replay rejection (source lines ~260–265). A naive replay finding would be incorrect. No replay exploit established.
- Charm reviewed public three-file in-scope code and checked vault deposit/withdraw fee accounting, factory access restrictions, and callbacks. No reward-eligible issue demonstrated.

### Eligibility and proof requirements

- Test on local EVM instances/forks only. **Never execute live mainnet/public-testnet vulnerability probes**, as the programmes prohibit them.
- An acceptable report needs a **novel in-scope finding**, credible user-funds impact and **reproducing PoC on a local fork**. We currently have **ZERO verified findings**, **ZERO submissions**, **ZERO accepted rewards**, **$0 payments**.
- The Android Termux Remote Desktop Commander bridge was offline when checked; no authenticated local forge mainnet-fork runtime was available for an end-to-end PoC in this pass. A local arithmetic test is not a substitute.
- Do not submit guesses, recycled public findings, best-practice issues, or claims about test/dev-only code. No permission has been granted to transfer any third-party funds.

### Immediate next security-research focus

Twyne newly introduced Morpho collateral-vault and operator pathways, emphasizing externally liquidated positions and **strict exact deployed-contract matching**. Once a reproducible in-scope effect is confirmed on a fork and checked against prior audits/known issues, submit privately via the official Immunefi programme. Prioritize actual confirmed findings, not merely high maximum rewards.

Artifacts: [offline conservation invariant test](../tools/nova_morpho_split_invariant.py). This is a source-based model; it performs no network calls or attacks.

**Verified payments: $0. No bounty award claimed.**
