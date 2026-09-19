#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

import torch

from model import EXPERTS, NovaSparseLM, parameter_count, save_checkpoint
from run_pipeline import stage_sft, stage_dpo, stage_eval, promote

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
CORPUS = ROOT / "corpus"
TARGET = int(os.getenv("NOVA_TARGET_TOKENS", "50000000"))
CHECKPOINT = STATE / "model_checkpoint.pt"


def main() -> int:
    expert_files = sorted(STATE.glob("expert_*.pt"))
    if len(expert_files) != EXPERTS:
        raise RuntimeError(f"expected {EXPERTS} expert checkpoints, found {len(expert_files)}")

    model = NovaSparseLM()
    total = 0
    seen_by_expert = {}
    for path in expert_files:
        payload = torch.load(path, map_location="cpu", weights_only=False)
        idx = int(payload.get("expert_idx", -1))
        tokens = int(payload.get("tokens_seen", -1))
        if idx < 0 or idx >= EXPERTS:
            raise RuntimeError(f"invalid expert index in {path}")
        if tokens < 1:
            raise RuntimeError(f"empty expert checkpoint: {path}")
        model.experts[idx].load_state_dict(payload["state"], strict=True)
        total += tokens
        seen_by_expert[str(idx)] = tokens

    if total != TARGET:
        raise RuntimeError(f"global token accounting mismatch: {total} != {TARGET}")
    if parameter_count(model) < 45_000_000:
        raise RuntimeError("parameter floor not met")

    STATE.mkdir(parents=True, exist_ok=True)
    CORPUS.mkdir(parents=True, exist_ok=True)
    save_checkpoint(CHECKPOINT, model, TARGET, "TRAIN_50M", {
        "expert_tokens": seen_by_expert,
        "parallel_experts": EXPERTS,
        "synthetic_pretraining": False,
    })

    corpus_manifest = CORPUS / "CORPUS_MANIFEST.json"
    license_file = CORPUS / "CORPUS_LICENSE.json"
    if not corpus_manifest.exists() or not license_file.exists():
        raise RuntimeError("corpus license/manifest missing")

    raw = (CORPUS / "wiki.train.tokens").read_bytes()
    stage_sft(model)
    stage_dpo(model)
    evaluation = stage_eval(model, raw)
    final = promote(model, TARGET, evaluation)

    manifest = json.loads((ROOT / "production" / "final_manifest.json").read_text(encoding="utf-8"))
    manifest["training_architecture"] = {
        "model": "NovaSparseLM",
        "parameters": parameter_count(model),
        "experts": EXPERTS,
        "token_definition": "UTF-8 byte tokens",
        "tokens_seen": TARGET,
        "expert_tokens": seen_by_expert,
    }
    manifest["production_sha256"] = hashlib.sha256(final.read_bytes()).hexdigest()
    (ROOT / "production" / "final_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({
        "complete": True,
        "final": str(final),
        "parameters": parameter_count(model),
        "tokens_seen": TARGET,
        "sha256": manifest["production_sha256"],
        "evaluation": evaluation,
    }), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
