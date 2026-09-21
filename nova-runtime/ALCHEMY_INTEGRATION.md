# Nova × Alchemy Integration

Nova's runtime now has an Alchemy capability gateway covering the documented Alchemy infrastructure surface most relevant to onchain operation.

## Integrated capability surface

- Chain APIs: JSON-RPC, WebSocket endpoint metadata, Trace API access, Debug API access.
- Data APIs: Portfolio, Token, Transfers, Prices, NFT.
- Notifications: webhook capability metadata and platform gateway support.
- Account abstraction: Bundler, Gas Manager, Account Kit capability routing.
- Ethereum Sepolia: chain ID 11155111, public Alchemy RPC fallback, optional private API-key endpoint.
- Faucet: Alchemy Ethereum Sepolia faucet resource.
- Safety: state-changing eth_send* RPC calls remain blocked in the generic data gateway; Nova's dedicated signing/deployment controller remains the only deployment path.

## Configuration

Optional API key: `NOVA_ALCHEMY_API_KEY`

Fallback: Nova can use Alchemy's documented public Sepolia endpoint without an API key for basic RPC access.

For production/high-volume usage, provision an Alchemy API key through the user's Alchemy account and store it as a secret/environment variable rather than in source control.

## NOVA deployment boundary

Alchemy supplies infrastructure and testnet access, but does not remove the requirement for a valid signer. Nova's Sepolia deployment controller still requires:
- `NOVA_DEPLOYER_PRIVATE_KEY`
- Sepolia ETH for gas

Private keys must remain outside source control and must never be committed to the repository or pasted into application logs.

## Time-sensitive note

Alchemy documents its Transaction Simulation APIs as being deprecated on 2026-09-30. Nova exposes the generic RPC/capability gateway so deprecated simulation calls can be replaced without redesigning the runtime interface.