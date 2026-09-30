# Nova Gemma 4 Developer Agent Starter

Prepared for the 2026 Google DeepMind / Kaggle Gemma 4 Developer Agent Competition.

## Competition fit

The current competition requires a `submission.zip` with `agent.yaml` at its root and currently supports the `gemma-4-31b-it-qat-w4a16-ct` model. The package here starts with a small evidence-first baseline so future changes can be measured instead of mixing prompts, subagents and adapters at once.

## Build

```bash
cd kaggle-gemma4
python3 build_submission.py
python3 -m zipfile -l submission.zip
```

The build step checks required files, symlinks, archive integrity and size. It does not prove that the competition harness accepts or scores the agent.

## Human/account gate

The account holder must join the Kaggle competition and accept its rules before the entry deadline. This repository does not attempt to bypass that gate.

## Next experiments

1. Baseline prompt only.
2. Add repository-graph localization as a controlled experiment.
3. Compare tool-call budget and pass rate.
4. Add a specialist read-only analyzer only if it beats the single-agent baseline.
5. Consider LoRA work only after prompt/tool changes are measured.

Do not claim prize eligibility, leaderboard score or revenue until Kaggle records a valid submission/result and any prize is actually paid.
