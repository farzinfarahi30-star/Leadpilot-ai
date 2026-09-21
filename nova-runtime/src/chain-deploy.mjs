import process from 'node:process';
import { dispatchNovaTokenTestnet } from './chain-ops.mjs';

dispatchNovaTokenTestnet({
  owner: process.env.NOVA_CHAIN_OWNER,
  maxSupplyTokens: process.env.NOVA_CHAIN_MAX_SUPPLY || 1000000
})
  .then((result) => {
    console.log(JSON.stringify({ event: 'nova_chain_deploy_dispatched', ...result }));
  })
  .catch((error) => {
    console.error(JSON.stringify({ event: 'nova_chain_deploy_dispatch_failed', error: String(error) }));
    process.exitCode = 1;
  });
