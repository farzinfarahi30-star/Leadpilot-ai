import process from 'node:process';

const REPO = process.env.GITHUB_REPOSITORY || 'farzinfarahi30-star/Leadpilot-ai';
const TOKEN = process.env.GITHUB_TOKEN || '';
const OWNER = '0x63970A951bd69975eF2aDAD27bf73584D2DCeF9B';

function assertToken() {
  if (!TOKEN) throw new Error('GITHUB_TOKEN missing');
}

function assertOwner(owner) {
  if (String(owner).toLowerCase() !== OWNER.toLowerCase()) {
    throw new Error('NOVA owner mismatch; refusing token deployment');
  }
}

export async function dispatchNovaTokenTestnet({ owner = OWNER, maxSupplyTokens = 1000000 } = {}) {
  assertToken();
  assertOwner(owner);
  const cap = Number(maxSupplyTokens);
  if (!Number.isSafeInteger(cap) || cap <= 0) {
    throw new Error('maxSupplyTokens must be a positive safe integer');
  }

  const url =
    'https://api.github.com/repos/' +
    REPO +
    '/actions/workflows/nova-token-testnet-deploy.yml/dispatches';

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      accept: 'application/vnd.github+json',
      authorization: 'Bearer ' + TOKEN,
      'x-github-api-version': '2022-11-28',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      ref: 'main',
      inputs: { owner, max_supply_tokens: String(cap) }
    })
  });

  const body = await res.text();
  if (!res.ok) {
    throw new Error('GitHub dispatch ' + res.status + ': ' + body.slice(0, 500));
  }

  return {
    dispatched: true,
    workflow: 'nova-token-testnet-deploy.yml',
    owner,
    maxSupplyTokens: cap
  };
}
