# Nova Device Bridge

Nova now has a dedicated device-execution capability modeled around the useful, documented capabilities of Termux and Desktop Commander.

## Capabilities

- Detect Android/Termux execution environments.
- Run approved local development commands.
- Read/write files inside an explicit Nova allowlist.
- Inspect Node/architecture/platform state.
- Detect whether npx is available.
- Start the official Desktop Commander remote device agent when explicitly requested.
- Keep Desktop Commander as an external protocol/provider rather than copying proprietary hosted code.

## Termux

The bridge is designed to run directly inside Termux. This gives Nova a local execution lane for Node, Python, Git, npm/npx and other development operations.

For Android, Nova should set:

NOVA_DEVICE_ALLOWED_ROOTS=$PREFIX/var/tmp/nova:$HOME/Leadpilot-ai

Adjust the repository path to the actual checkout. Never add credential directories or the entire filesystem unless there is a deliberate security review.

## Desktop Commander

Desktop Commander's documented remote agent is:

npx @wonderwhy-er/desktop-commander@latest remote

Nova can launch that agent through startDesktopCommanderRemote() when the device is explicitly paired and authorized. The hosted Remote MCP service still requires its own OAuth pairing; Nova does not bypass that authorization.

## Safety

The default command allowlist covers normal development/diagnostic tools. Destructive or otherwise unlisted executables require:

NOVA_DEVICE_ALLOW_DANGEROUS=true

Do not store wallet seed phrases or private keys in the bridge, repository, logs, or environment files committed to Git.

## Smoke test

From nova-runtime:

node src/device-bridge-smoke.mjs

This validates the bridge code itself. It does not claim that a physical Termux phone or Desktop Commander device is online.
