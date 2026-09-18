# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "marimo>=0.20.4",
#   "requests>=2.32",
#   "datasets>=4.0",
#   "tokenizers>=0.21",
#   "torch",
# ]
#
# [[tool.uv.index]]
# name = "pytorch-cu130"
# url = "https://download.pytorch.org/whl/cu130"
# explicit = true
#
# [tool.uv.sources]
# torch = [{ index = "pytorch-cu130", marker = "sys_platform == 'linux'" }]
# ///

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

import marimo as mo

app = mo.App(width="full")
ROOT = pathlib.Path.home() / "nova_gpu"
ROOT.mkdir(parents=True, exist_ok=True)
RAW = "https://raw.githubusercontent.com/farzinfarahi30-star/Leadpilot-ai/nova-gpu/"
FILES = {
    "nova_ai/model.py": "nova_ai/model.py",
    "nova_ai/tokenizer.py": "nova_ai/tokenizer.py",
    "nova_ai/__init__.py": "nova_ai/__init__.py",
    "nova_ai/safety.py": "nova_ai/safety.py",
    "train_hf_stream.py": "nova/train_hf_stream.py",
    "instruction_tune.py": "nova/instruction_tune.py",
    "preference_tune.py": "nova/preference_tune.py",
    "prepare_posttraining.py": "nova/prepare_posttraining.py",
    "evaluate_suite.py": "nova/evaluate_suite.py",
    "evaluate_capabilities.py": "nova/evaluate_capabilities.py",
    "data/reasoning.jsonl": "data/reasoning.jsonl",
}


@app.cell
def _():
    mo.md(
        """# Nova AI — GPU completion runner

Uses the existing Nova source, resumable pretraining, post-training, evaluation gates, and final promotion.

**Target:** 27,795,968 parameters · 50,000,000 pretraining tokens · 1,500 SFT steps · 400 preference steps.

**MoLab:** enable the GPU from the **notebook-specs** control in the app header. Once CUDA is available, this runner starts/resumes automatically.
"""
    )


@app.cell
def _():
    status = mo.md("Preparing Nova GPU environment…")
    return status


@app.cell
def _(status):
    for rel, remote in FILES.items():
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(RAW + remote, dest)
    (ROOT / "checkpoints").mkdir(exist_ok=True)
    status.value = mo.md("Source synchronized from the Nova GPU branch.")
    return ROOT


@app.cell
def _(ROOT):
    sys.path.insert(0, str(ROOT))
    import torch

    cuda = torch.cuda.is_available()
    count = torch.cuda.device_count()
    gpu = torch.cuda.get_device_name(0) if cuda else "none"
    capability = torch.cuda.get_device_capability(0) if cuda else None

    from nova_ai.model import NovaLM, NovaConfig

    probe = NovaLM(NovaConfig())
    params = probe.num_parameters()
    del probe

    if cuda:
        a = torch.randn((256, 256), device="cuda", dtype=torch.float16)
        b = torch.randn((256, 256), device="cuda", dtype=torch.float16)
        _ = a @ b
        torch.cuda.synchronize()
        del a, b

    mo.md(
        f"""**GPU:** `{gpu}`  
**CUDA devices:** `{count}`  
**CUDA capability:** `{capability}`  
**Model parameters:** `{params:,}`  
**Parameter target:** `{27_795_968:,}`"""
    )

    assert cuda and count >= 1, (
        "GPU not attached yet. Use the MoLab notebook-specs control in the app header "
        "to enable the NVIDIA GPU; this runner will then continue automatically."
    )
    assert params == 27_795_968, f"Parameter mismatch: {params:,}"
    return torch


@app.cell
def _(ROOT):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    def call(args):
        print("$ " + " ".join(args), flush=True)
        return subprocess.run(args, cwd=ROOT, env=env, check=True)

    pre = ROOT / "checkpoints/nova-preference.pt"
    final = ROOT / "checkpoints/nova-final.pt"

    call(
        [
            sys.executable,
            "train_hf_stream.py",
            "--dataset",
            "HuggingFaceFW/fineweb_100BT",
            "--steps",
            "1526",
            "--block-size",
            "1024",
            "--layers",
            "8",
            "--heads",
            "8",
            "--kv-heads",
            "4",
            "--embd",
            "512",
            "--vocab-size",
            "8192",
            "--batch-size",
            "2",
            "--grad-accum",
            "16",
            "--lr",
            "3e-4",
            "--checkpoint-every",
            "50",
            "--max-seconds",
            "39000",
            "--tokenizer-chars",
            "5000000",
            "--out",
            "checkpoints/nova-stream.pt",
            "--resume",
            "checkpoints/nova-stream.pt",
            "--grad-checkpoint",
        ]
    )
    call([sys.executable, "prepare_posttraining.py"])
    call(
        [
            sys.executable,
            "instruction_tune.py",
            "--checkpoint",
            "checkpoints/nova-stream.pt",
            "--data",
            "data/instructions_all.jsonl",
            "--steps",
            "1500",
            "--out",
            "checkpoints/nova-instruct.pt",
            "--checkpoint-every",
            "100",
        ]
    )
    call(
        [
            sys.executable,
            "preference_tune.py",
            "--checkpoint",
            "checkpoints/nova-instruct.pt",
            "--data",
            "data/preferences_hf.jsonl",
            "--steps",
            "400",
            "--out",
            "checkpoints/nova-preference.pt",
            "--checkpoint-every",
            "50",
        ]
    )
    call([sys.executable, "evaluate_suite.py", "--checkpoint", "checkpoints/nova-preference.pt"])
    call(
        [
            sys.executable,
            "evaluate_capabilities.py",
            "--checkpoint",
            "checkpoints/nova-preference.pt",
            "--data",
            "data/reasoning.jsonl",
        ]
    )

    ckpt = torch.load(pre, map_location="cpu")
    model = NovaLM(NovaConfig(**dict(ckpt["config"])))
    model.load_state_dict(ckpt["model"])
    assert model.num_parameters() == 27_795_968

    shutil.copy2(pre, final)
    digest = hashlib.sha256(final.read_bytes()).hexdigest()
    payload = {
        "stage": "production-final",
        "parameters": model.num_parameters(),
        "pretraining_target_tokens": 50_000_000,
        "pretraining_target_steps": 1526,
        "sft_steps": 1500,
        "preference_steps": 400,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sha256": digest,
        "evaluation_gate": "passed",
    }

    (ROOT / "checkpoints/nova-final.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (ROOT / "COMPLETION_STATUS_FINAL.md").write_text(
        f"""# Nova AI final completion

- parameters: {model.num_parameters():,}
- pretraining target: 50,000,000 tokens / 1,526 optimizer steps
- instruction tuning: 1,500 steps
- preference tuning: 400 steps
- evaluation gate: passed
- final checkpoint: checkpoints/nova-final.pt
- sha256: {digest}
- GPU: {torch.cuda.get_device_name(0)}
- generated UTC: {payload["created_utc"]}
""",
        encoding="utf-8",
    )
    mo.md(
        f"""## COMPLETE

**Final checkpoint:** `{final}`  
**SHA-256:** `{digest}`  
**Parameters:** `{model.num_parameters():,}`  
**GPU:** `{torch.cuda.get_device_name(0)}`"""
    )


if __name__ == "__main__":
    app.run()
