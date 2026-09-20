# Nova Runtime

Independent execution lane for the AI Business Factory.

## What it fixes

This worker does not consume Hatchable function runtime. It runs on a GitHub-hosted Linux runner and can execute browser tasks with Playwright, then call the Factory Boss heartbeat API.

The workflow runs in bounded sessions and restarts from schedule/checkpoints rather than relying on a permanently running process. Public repositories have no billable minutes for standard GitHub-hosted runners.

## Safety

- Factory calls are Boss-authorized only.
- No paid advertising is launched by this runtime itself.
- Browser automation must respect the Factory approval gate.
- Credentials are supplied only through GitHub Actions secrets.
