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
