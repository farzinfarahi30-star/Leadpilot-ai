# Nova Device XX

Nova's local capability layer reproduces the useful documented capability surface of Termux and Desktop Commander so Nova can use one governed interface.

Filesystem: list, read, multi-read, metadata, write, block-edit, move/rename, directory creation.

Search: start, paginate, stop and inspect active searches.

Terminal/processes: start commands, persistent sessions, stdin, output capture, active sessions, graceful termination, system-process listing and governed process termination.

Documents/data: PDF creation and XLSX read/write.

Termux: environment detection, developer-toolchain provisioning, approved Termux:API operations and background execution.

Operations: device diagnostics, persistent configuration, activity records and usage statistics.

Desktop Commander remote hosting is proprietary; this implementation recreates its documented local capability surface instead of copying hosted implementation code. The official service documents filesystem, search, write/edit, process/session, device, configuration and usage tools. citeturn369863search0

Termux provides the Android Linux environment and APT-based package ecosystem used by this toolkit. citeturn332547search4turn711078search0

Install with bash install-termux.sh. Termux:API is optional; its matching Android add-on and termux-api package are required for Android API commands. citeturn711078search2

Never store wallet seeds, private keys, OAuth refresh tokens or other secrets in this package, its logs or configuration.

A physical device still needs Termux running for local execution. A Desktop Commander remote connection still needs its device agent online and paired; this implementation does not bypass that requirement. citeturn369863search2


## Takeover mode

The full `xx` target is an operational takeover, not only a library adapter. `src/supervisor.mjs` keeps the Nova runtime and Desktop Commander remote agent running, restarts either process after an exit, records supervisor state, and acquires the Termux wake lock. `termux/boot/00-nova-supervisor` starts the supervisor at Android boot when Termux:Boot is installed and enabled. Termux:Boot officially supports boot scripts and recommends `termux-wake-lock` when a long-running process must remain active. citeturn939271search0

Run `INSTALL-TAKEOVER.sh` once on the device after the repository is reachable. It installs the Termux dependencies, installs the boot supervisor, enables Nova's local-device control environment, and starts the supervisor immediately. The Desktop Commander remote agent is the documented `npx @wonderwhy-er/desktop-commander@latest remote` process and must remain running for remote access. citeturn939271search1turn939271search3

This does not bypass Android permissions or a disconnected machine. The device still has to be powered on and the Termux/agent process must be allowed to run. No wallet seeds, private keys, OAuth refresh tokens, or other credentials are stored by the takeover layer.
