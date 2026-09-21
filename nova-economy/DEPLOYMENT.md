# Nova deployment runbook

## Current owner address

The intended owner/treasury address supplied by the user is:

`0x63970A951bd69975eF2aDAD27bf73584D2DCeF9B`

This is a public address. No private key or recovery phrase belongs in this repository.

## Testnet

Ethereum currently lists Sepolia as the recommended default public testnet for application/contract development. Use Sepolia for the first deployment and validation.

Required local secrets/config:
- `NOVA_DEPLOYER_PRIVATE_KEY`
- `SEPOLIA_RPC_URL`
- `NOVA_OWNER`
- `NOVA_MAX_SUPPLY`

Deploy with Foundry:

```bash
cd nova-economy
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install foundry-rs/forge-std --no-commit
source .env
forge build
forge test
forge script script/DeployNovaToken.s.sol:DeployNovaToken \
  --rpc-url "$SEPOLIA_RPC_URL" \
  --broadcast
```

The deployer key signs the transaction. The contract's `owner()` is set to `NOVA_OWNER`, so the Trust Wallet address remains the administrative owner even if a separate deployer key submits the deployment transaction.

## Verification

After deployment:
1. Record the contract address and deployment transaction hash outside source control.
2. Verify the contract source on the relevant Sepolia explorer.
3. Confirm `owner()` equals `NOVA_OWNER`.
4. Confirm `maxSupply()` equals the approved cap.
5. Confirm `totalSupply()` is initially zero.
6. Test minting, transfer, pause, and unpause on testnet.
7. Do not deploy to mainnet until security, operational, and applicable legal/compliance review is complete.

Never put a seed phrase or private key in GitHub, chat, source files, logs, or CI output.
