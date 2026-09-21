# Nova Economic Layer

Independent economic layer for the Nova ecosystem.

Current scope:
- ERC-20-compatible contract foundation using OpenZeppelin.
- Immutable maximum supply.
- Owner-controlled minting within that cap.
- Emergency pause control.
- No hidden transfer tax, blacklist, honeypot, or arbitrary confiscation.
- No automated public sale or production deployment.

## Nova-owned deployment control

Nova now has two deployment routes:
1. **Direct Sepolia controller** in `nova-runtime/src/nova-chain-controller.mjs`.
2. **GitHub Actions dispatch** in `nova-runtime/src/chain-ops.mjs` as a fallback/orchestrated route.

The direct controller performs the lifecycle in one controlled path:
**preflight → chain-ID check → Foundry deploy → extract contract address/tx → on-chain owner/cap/supply verification → write deployment record**.

Required execution-environment variables for direct deployment:
- `SEPOLIA_RPC_URL`
- `NOVA_DEPLOYER_PRIVATE_KEY` (keep local/secret; never paste it into chat or source control)
- `NOVA_DEPLOYER_ADDRESS` (public address; used for optional balance preflight)

Safe defaults:
- Sepolia chain ID: `11155111`
- NOVA owner/treasury: `0x63970A951bd69975eF2aDAD27bf73584D2DCeF9B`
- Maximum supply: `1,000,000` NOVA

Nova refuses deployment when the configured owner does not match the authorized treasury, when required credentials are missing, or when the RPC is not Sepolia.

Example runtime commands:
```bash
cd nova-runtime
npm run chain:preflight
npm run chain:deploy:sepolia
```

The deployer key must be funded with Sepolia ETH for gas. No mainnet deployment, public sale, or automatic minting is enabled by this controller.

The AI tokenizer and economic token must never share IDs, balances, or accounting. Deployment still requires an explicitly authorized chain, deployer account, RPC, treasury, security review, and applicable legal/compliance review.
