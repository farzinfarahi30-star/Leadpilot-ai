# Nova AI — Desktop Commander Integration

Nova now has a native client layer for the official Desktop Commander Remote MCP service and exposes its discovered tools through the Nova device tool registry.

## Architecture

Desktop Commander documents the hosted endpoint as:

`https://mcp.desktopcommander.app/mcp`

The hosted service uses Streamable HTTP and OAuth 2.0. A paired machine must have the Desktop Commander remote device agent running to remain reachable.

Nova integration:

`Nova agents -> NOVA_DEVICE_TOOLS -> Desktop Commander MCP client -> hosted MCP -> paired device agent -> device`

Nova also retains the local `nova-device` capability layer for Termux/device-native operations.

## Nova tool surface

The runtime exposes:

- `listDesktopCommanderTools` — performs authenticated MCP initialization and dynamically discovers the complete available tool catalog, including pagination.
- `callDesktopCommanderTool` — invokes a discovered Desktop Commander tool by name with its arguments.
- All existing `nova-device` tools remain available in the same registry.

The client handles JSON responses and SSE response streams, tracks negotiated protocol information, supports MCP session identifiers when supplied by the server, and sends the Streamable HTTP protocol metadata required by modern MCP servers.

## Credentials

Nova expects:

`DESKTOP_COMMANDER_OAUTH_TOKEN`

Optional:

`DESKTOP_COMMANDER_MCP_URL`

`DESKTOP_COMMANDER_MCP_PROTOCOL`

The OAuth credential must come from an authorized Desktop Commander OAuth flow. Nova never fabricates, extracts, logs, or bypasses credentials.

For GitHub Actions, the optional repository secret is:

`DESKTOP_COMMANDER_OAUTH_TOKEN`

The workflow passes it only as a process environment variable. It is never written to the repository.

## Device side

The takeover supervisor continues to supervise:

`nova-runtime`

and:

`npx -y @wonderwhy-er/desktop-commander@latest remote`

If the remote agent exits, the supervisor restarts it. Termux wake-lock support remains enabled while the supervisor runs.

## Readiness states

`configured=false` means Nova has no OAuth credential and cannot make an authenticated Remote MCP request.

`configured=true, connected=false` means credentials are present but the MCP service/device path is unavailable.

`configured=true, connected=true` means Nova successfully initialized the MCP connection and discovered the remote tool catalog.

A successful local build or CI run does not by itself prove live device access; that requires a valid OAuth credential and an online paired device.

## Security boundary

“XX” here means reproducing the useful public capability surface and integrating it into Nova. It does not mean copying the proprietary hosted service implementation or bypassing OAuth, device pairing, Android permissions, or operating-system security.

## Verification

The canonical workflow validates:

- Nova Device syntax and smoke tests
- Nova Mail syntax and smoke tests
- Nova Runtime syntax
- Desktop Commander MCP client syntax
- unified Nova device-tool registry
- Desktop Commander doctor/readiness state

The workflow is intentionally safe when no OAuth credential is configured: it reports the missing credential instead of failing or attempting an authentication bypass.
