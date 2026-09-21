# Nova Economic Layer

Independent economic layer for the Nova ecosystem.

Current scope:
- ERC-20-compatible contract foundation using OpenZeppelin.
- Immutable maximum supply.
- Owner-controlled minting within that cap.
- Emergency pause control.
- No hidden transfer tax, blacklist, honeypot, or arbitrary confiscation.
- No automated public sale or production deployment.

Deployment requires an explicitly authorized chain, deployer account, RPC,
treasury, security review, and applicable legal/compliance review.

The AI tokenizer and economic token must never share IDs, balances, or accounting.
