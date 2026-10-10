# NOVA — First Bounty: Grounded Research and Execution
Date: 10 October 2026

## Objective
Find one **genuinely eligible, reproducible and sponsor-accepted** bounty, then verify an actual transfer to an authorised wallet. Never treat a listing, scanner alert, competition allocation, proposed payout, submitted report, or points as income.

## VERIFIED NOW
- An Oct 10 Immunefi API inventory produced **232 programme entries: 169 live public, 1 active invite-only, 62 closed**.
- An Oct 10 HackenProof pagination scan collected all 33 pages, **324 directory entries: 151 live, 35 paused, 138 finished**.
- In total **320 publicly listed live programme entries**, not guaranteed to be independent sponsors or instantly fundable.
- Enzyme Onyx is currently advertised by Immunefi as offering **USDC on Ethereum** for qualifying smart contract findings: Medium $1,000-$5,000; High $5,000-$20,000; Critical $20,000-$200,000. **No KYC required by the programme**. A complete production-code/fork PoC is mandatory. Source: https://immunefi.com/bug-bounty/enzyme-onyx/information/
- Twyne currently advertises USDC rewards, High $3,000-$10,000 and Critical $10,000-$50,000. Local-fork PoC required; no programme KYC. Source: https://immunefi.com/bug-bounty/twyne/information/
- **The authorised Termux Remote Desktop Commander device was online** during the research session.
- Retrieved the pinned public Enzyme Onyx source commit `7b48d243f505b362cd6f1fcf723c21bc8b047c06`. Source archive and extracted repository reside in `~/.nova/bounty/` on the authorised Android device.
- Installed `solc@0.8.28` and `@ethereumjs/vm@10.1.0` under `~/.nova/bounty/devtools/` with no paid services.
- Compiled **7 actual first-party Onyx contract targets** (Shares, ValuationHandler, FeeHandler, deposit queue, redeem queue, open forwarder, restricted forwarder), pulling 42 dependency source units, using Solidity compiler 0.8.28. **0 compiler errors and 0 compiler warnings**. Local command: `node ~/.nova/bounty/onyx-compile-core.cjs`; generated local compilation artifacts at `~/.nova/bounty/onyx-compiled-core.json`.
- Executed `OneToOneAggregator` production code in the offline EthereumJS EVM; the two checks behaved normally (18 decimals, 1e18 quote). These are regression tests, **not exploit findings**. Local command: `node ~/.nova/bounty/onyx-local-contract-test.cjs`.
- Read the project's committed `slither.db.json`: 139 legacy static-analysis observations; neither the two High/High detections nor reviewed medium ones established an eligible, production-reproducible exploit. An access-surface scan of 73 Onyx files listed 81 public/external state-changing target functions and found no demonstrated unauthorised financial action. Local script: `node ~/.nova/bounty/onyx-surface-scan.mjs`.
- Wrote a separate `onyx-value-fuzz.cjs` math test script for actual code, but its execution was **not completed / not counted as passed**.
- Searched connected Gmail from October 1 for bounty award, acceptance and payment notices; **none found** in results.

## ALTERNATIVE SERIOUS ROUTES — EVIDENCE AND GATES
1. **Enzyme Onyx (immediate source-research focus):** zero-cost code download and local compilation; medium tier from $1k; complete reproduction against actual production code/fork, newly discovered in-scope impact, and accepted sponsor triage are mandatory. Known audit findings, documented configuration/admin risks and mock-only test PoCs are not reward-eligible. https://immunefi.com/bug-bounty/enzyme-onyx/scope/
2. **Twyne:** zero-cost public Solidity code and local testing; high/critical only (no $100 low tier). Requires genuine permanent/24h fund-freezing/asset loss/yield loss. https://immunefi.com/bug-bounty/twyne/scope/
3. **Other Immunefi funded-vault programmes:** ENS displayed approximately $39.9k USDC in its reward vault; Cosmos displayed approximately $100k, with lower-severity reward tiers but KYC required. Vault balance is *sponsor funds*, not the researcher's money and not a guarantee of any specific payout. https://immunefi.com/bug-bounty/ens/information/ ; https://immunefi.com/bug-bounty/cosmos/information/
4. **HackenProof security programmes:** 151 listed live in Oct 10 scrape. Eligibility can involve reputation points, KYC or submission fees; first verify individual programmes. https://hackenproof.com/programs
5. **Google Patch Rewards:** official security-improvement route; advertised $500 for qualifying Tier-1 small improvements, $2k/$7.5k/$15k tiers for larger patches, dependent on in-scope project and acceptance; typically requires a merged security PR, and reward is discretionary. https://bughunters.google.com/open-source-security/patch-rewards ; scope https://github.com/google/bughunters/blob/main/patch-rewards-program/scope.md. Note Google OSS VRP **product vulnerability** submissions stopped being accepted Oct 1, 2026; do not substitute a new OSS VRP report for a merged Patch Rewards submission. https://github.com/google/bughunters/blob/main/bughunters/articles/about/rules/open-source/google-open-source-software-vulnerability-reward-program-rules.md
6. **Funded open-source issue bounties (Algora/Opire):** potential payout after **accepted merged code**, but listings often remain open after a bounty is completed; some Github issues lack verified funding. A real $60-labelled Nudge-Pay issue #107 was open Oct10, but another contributor publicly asked whether the reward was funded and sponsor approval had not been verified. Avoid unpaid speculative PR churn. https://github.com/Nudge-Pay/nudge-server/issues/107
7. **Bitcoin research micro-bounties:** https://github.com/1btc-news/news-client/issues/30 contains a sponsor-reported 100,000-sats sBTC payout with an on-chain transaction reference. However the next https://github.com/1btc-news/news-client/issues/33 60-day paying period reportedly ended June 3, 2026, so do **not** assume its open issue is an available October bounty. Sponsor requests AIBTC identity and address; no user wallet has been supplied for that scheme.
8. **Audit competitions (Sherlock/Cantina/CodeHawks):** zero-cost source and usually competitive allocations, if currently open, with fees/reputation/KYC sometimes varying; inspect specific dates before applying. Many CodeHawks First Flights are `EXP` not cash. https://audits.sherlock.xyz/contests ; https://cantina.xyz/competitions ; https://codehawks.cyfrin.io/contests

## NOT VERIFIED
- No new reward-eligible vulnerability, no production-code exploit PoC, no submitted bounty report, no accepted sponsor award, no verified transfer to a wallet.
- None of the advertised maximum bounties or vault balances are user revenue.
- Previously saved July 2026 Enzyme source commit has **not** been proven byte-for-byte identical to every currently deployed October 2026 in-scope instance.

## BLOCKERS
- A novel eligible finding plus full reproducible proof in the legally authorised local testing environment is mandatory; static alerts alone are not actionable.
- No sponsor report has been submitted because there is no validated report.
- Researcher account / verified payout wallet may require a human once a real report is accepted, even on programmes listing 'no KYC'.
- Connected GitHub tool writes to owned repositories but does not provide a usable fork operation to make an upstream paid-issue PR from the current connection; paid-issue sponsors must also confirm active reward funding and merge approval.

## EXECUTED
- Multiple official programme/eligibility/documentation searches; excluded expired competitions and stale/uncertain payment claims.
- Existing Oct 10 full bounty-directory CSVs committed and verified on GitHub:
  - [556 entries](../data/NOVA_WEB3_BUG_BOUNTIES_ALL_2026-10-10.csv)
  - [320 live](../data/NOVA_WEB3_BUG_BOUNTIES_LIVE_2026-10-10.csv)
  - [71 no-KYC live Immunefi](../data/NOVA_WEB3_BUG_BOUNTIES_NO_KYC_IMMUNEFI_2026-10-10.csv)
- Live Termux source checkout, open-source Solidity/EVM tooling, compiled source units, executed two trivial production-code regression checks, and staged property tests not represented as executed.
- Hourly research/award condition-watch already enabled. Notify only for verified new findings, accepted reports or actual transfers.

## MY REQUIRED ACTIONS
- **None for ongoing offline code research.**
- When a true sponsor-eligible finding has been reproduced and a report is ready: sign into Immunefi and arrange the authorised USDC payout address if platform login or wallet verification is required. Do not provide private keys or seed phrases.

## NEXT MAXIMUM MOVE
Focus limited high-value time on original in-scope unauthorised asset/accounting flows. Prove any candidate on the actual production code or a local fork, cross-check published known risks/audits, privately submit the reproducible finding on the official bounty platform, await acceptance and settlement, then confirm the actual payment from an official transaction reference. If repeated candidates are duplicate or excluded, shift to a current, legitimate lower-severity cash programme or **accepted merged Google Patch Rewards** route, rather than sending weak speculative reports.

**Verified earnings and transfers as of this report: $0.**
