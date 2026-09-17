from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

import modal

ROOT = Path(__file__).resolve().parents[1]
VOLUME_NAME = "nova-ai-checkpoints"
VOLUME = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

IMAGE = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch>=2.2", "datasets>=3.0", "tokenizers>=0.21")
    .add_local_dir(str(ROOT / "nova_ai"), "/workspace/nova_ai")
    .add_local_file(str(ROOT / "nova" / "train_hf_stream.py"), "/workspace/train_hf_stream.py")
    .add_local_file(str(ROOT / "nova" / "autopilot.py"), "/workspace/autopilot.py")
    .add_local_file(str(ROOT / "nova" / "prepare_posttraining.py"), "/workspace/prepare_posttraining.py")
    .add_local_file(str(ROOT / "nova" / "instruction_tune.py"), "/workspace/instruction_tune.py")
    .add_local_file(str(ROOT / "nova" / "preference_tune.py"), "/workspace/preference_tune.py")
    .add_local_file(str(ROOT / "nova" / "evaluate_suite.py"), "/workspace/evaluate_suite.py")
    .add_local_file(str(ROOT / "nova" / "evaluate_capabilities.py"), "/workspace/evaluate_capabilities.py")
    .add_local_file(str(ROOT / "data" / "reasoning.jsonl"), "/workspace/data/reasoning.jsonl")
)

app = modal.App("nova-ai-training")


@app.function(
    image=IMAGE,
    gpu="T4",
    timeout=60 * 60,
    volumes={"/vol": VOLUME},
    memory=32768,
    cpu=8,
)
def train_chunk(
    pretrain_tokens=50_000_000,
    sft_steps=1_500,
    pref_steps=400,
    chunk_seconds=3_000,
):
    os.chdir("/workspace")
    os.environ.update(
        HF_HOME="/vol/hf",
        HF_DATASETS_CACHE="/vol/hf/datasets",
        TOKENIZERS_PARALLELISM="false",
        PYTHONUNBUFFERED="1",
    )
    Path("/vol/checkpoints").mkdir(parents=True, exist_ok=True)
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("Modal T4 was not provisioned")

    cmd = [
        sys.executable,
        "autopilot.py",
        "--checkpoint",
        "/vol/checkpoints/nova-stream.pt",
        "--pretrain-tokens",
        str(pretrain_tokens),
        "--chunk-seconds",
        str(chunk_seconds),
        "--sft-steps",
        str(sft_steps),
        "--pref-steps",
        str(pref_steps),
        "--do-posttrain",
    ]
    print("NOVA_GPU", torch.cuda.get_device_name(0), flush=True)
    print("NOVA_CMD", " ".join(cmd), flush=True)
    rc = subprocess.call(cmd)

    final = Path("/vol/checkpoints/nova-final.pt")
    if final.exists() and final.stat().st_size > 1_000_000:
        digest = hashlib.sha256(final.read_bytes()).hexdigest()
        try:
            ck = torch.load(final, map_location="cpu")
            params = int(sum(v.numel() for v in ck["model"].values()))
            step = int(ck.get("step", 0))
        except Exception as exc:
            params = -1
            step = -1
            print("NOVA_FINAL_INSPECT_ERROR", repr(exc), flush=True)
        meta = {
            "stage": "production-final",
            "parameters": params,
            "pretraining_target_tokens": int(pretrain_tokens),
            "sft_steps": int(sft_steps),
            "preference_steps": int(pref_steps),
            "checkpoint_step": step,
            "sha256": digest,
            "gpu": torch.cuda.get_device_name(0),
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        Path("/vol/checkpoints/nova-final.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
        print("NOVA_FINAL_READY", json.dumps(meta, sort_keys=True), flush=True)
    VOLUME.commit()
    print("NOVA_MODAL_EXIT", rc, flush=True)
    return int(rc)


@app.local_entrypoint()
def main():
    rc = train_chunk.remote()
    print("NOVA_MODAL_CHUNK_EXIT", rc)
