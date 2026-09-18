#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import random
import shutil
import time
import urllib.request
import zipfile
from pathlib import Path

import torch
from torch import nn

from model import CONTEXT, EXPERTS, NovaSparseLM, parameter_count, save_checkpoint, load_checkpoint

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
PRODUCTION = ROOT / "production"
CORPUS = ROOT / "corpus"
CHECKPOINT = STATE / "model_checkpoint.pt"
TARGET = int(os.getenv("NOVA_TARGET_TOKENS", "50000000"))
CHUNK = int(os.getenv("NOVA_CHUNK_TOKENS", "10000000"))
SEED = 1337
torch.manual_seed(SEED)
random.seed(SEED)
torch.set_num_threads(max(1, int(os.getenv("TORCH_THREADS", "4"))))


def save_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def bootstrap_corpus() -> Path:
    CORPUS.mkdir(parents=True, exist_ok=True)
    target = CORPUS / "wiki.train.tokens"
    license_path = CORPUS / "CORPUS_LICENSE.json"
    manifest_path = CORPUS / "CORPUS_MANIFEST.json"
    url = "https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-103-v1.zip"
    if not target.exists() or target.stat().st_size < TARGET:
        archive = ROOT / "state" / "wikitext.zip"
        if not archive.exists():
            urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as z:
            candidates = [n for n in z.namelist() if n.endswith("wiki.train.tokens")]
            if not candidates:
                raise RuntimeError("WikiText train file not found in archive")
            with z.open(candidates[0]) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
    license_doc = {
        "licensed": True,
        "license": "CC BY-SA 4.0",
        "source": "https://huggingface.co/datasets/Salesforce/wikitext",
        "source_archive": url,
        "training_policy": "public licensed corpus; synthetic data disabled for pretraining",
    }
    license_path.write_text(json.dumps(license_doc, indent=2), encoding="utf-8")
    h = hashlib.sha256(target.read_bytes()).hexdigest()
    save_json(manifest_path, {"file": str(target), "bytes": target.stat().st_size, "sha256": h, "license": license_doc})
    return target


def corpus_path() -> Path:
    explicit = os.getenv("NOVA_CORPUS", "").strip()
    if explicit:
        p = Path(explicit).expanduser()
        if p.is_file():
            return p
        if p.is_dir():
            files = sorted(p.glob("*.txt")) + sorted(p.glob("*.jsonl"))
            if files:
                return files[0]
    return bootstrap_corpus()


def load_bytes(path: Path):
    raw = path.read_bytes()
    if len(raw) < CONTEXT + 1:
        raise RuntimeError("corpus is too small")
    return raw


def batch_from_bytes(raw: bytes, batch: int, seq: int):
    x = torch.empty((batch, seq), dtype=torch.long)
    y = torch.empty((batch, seq), dtype=torch.long)
    max_start = len(raw) - seq - 1
    for i in range(batch):
        s = random.randint(0, max_start)
        x[i] = torch.tensor(list(raw[s:s + seq]), dtype=torch.long)
        y[i] = torch.tensor(list(raw[s + 1:s + seq + 1]), dtype=torch.long)
    return x, y


def train_tokens(model: NovaSparseLM, raw: bytes, tokens: int, seen: int, lr: float, stage: str, batch: int = 16) -> int:
    model.train()
    opts = [torch.optim.AdamW(model.experts[i].parameters(), lr=lr) for i in range(EXPERTS)]
    for opt in opts:
        opt.zero_grad(set_to_none=True)
    step_tokens = batch * CONTEXT
    steps = math.ceil(tokens / step_tokens)
    for local_step in range(steps):
        expert_idx = (seen // step_tokens + local_step) % EXPERTS
        x, y = batch_from_bytes(raw, batch, CONTEXT)
        logits, _ = model(x, expert_idx)
        loss = nn.functional.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
        opts[expert_idx].zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.experts[expert_idx].parameters(), 1.0)
        opts[expert_idx].step()
        seen += step_tokens
        if local_step == steps - 1 or seen % 1_000_000 < step_tokens:
            save_checkpoint(CHECKPOINT, model, seen, stage, {"loss": float(loss.item())})
            print(json.dumps({"stage": stage, "tokens_seen": seen, "loss": float(loss.item())}), flush=True)
        if seen >= TARGET and stage == "TRAIN_50M":
            break
    return min(seen, TARGET)


def ensure_model() -> tuple[NovaSparseLM, int]:
    model = NovaSparseLM()
    seen = 0
    if CHECKPOINT.exists():
        seen, payload = load_checkpoint(CHECKPOINT, model)
        print(json.dumps({"resume": True, "tokens_seen": seen, "checkpoint_stage": payload.get("stage", "")}), flush=True)
    return model, seen


def stage_sft(model: NovaSparseLM) -> None:
    data = [
        ("Explain what a variable is in programming.", "A variable is a named place to keep a value so a program can use or change it."),
        ("Give a simple debugging method.", "Read the error, isolate the smallest failing example, test one change, then rerun it."),
        ("Write a Python hello world example.", "print('Hello, world!')"),
        ("What is a loop?", "A loop repeats instructions until a stopping condition is met or the sequence is exhausted."),
        ("What does an API do?", "An API defines a structured way for one program to request data or actions from another program."),
        ("How do I make code safer?", "Validate inputs, limit resources, handle errors, keep secrets out of source code, and test failure cases."),
        ("Explain recursion simply.", "Recursion is when a function solves a problem by calling itself on a smaller version of that problem."),
        ("What is JSON?", "JSON is a text format for representing structured data with objects, arrays, strings, numbers, booleans and null."),
    ]
    model.train()
    opts = [torch.optim.AdamW(model.experts[i].parameters(), lr=3e-4) for i in range(EXPERTS)]
    for epoch in range(2):
        for prompt, answer in data:
            text = prompt + "\n" + answer
            b = text.encode("utf-8")[:CONTEXT + 1]
            if len(b) < 3:
                continue
            x = torch.tensor(list(b[:-1]), dtype=torch.long).unsqueeze(0)
            y = torch.tensor(list(b[1:]), dtype=torch.long).unsqueeze(0)
            expert = model.route_text(prompt)
            logits, _ = model(x, expert)
            loss = nn.functional.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
            opts[expert].zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.experts[expert].parameters(), 1.0)
            opts[expert].step()
    save_checkpoint(CHECKPOINT, model, TARGET, "SFT")
    save_json(STATE / "sft.json", {"status": "done", "examples": len(data), "license": "CC0-1.0-original-authored"})


def sequence_logprob(model: NovaSparseLM, text: str, expert: int | None = None) -> tuple[torch.Tensor, int]:
    b = text.encode("utf-8")[:CONTEXT + 1]
    x = torch.tensor(list(b[:-1]), dtype=torch.long).unsqueeze(0)
    y = torch.tensor(list(b[1:]), dtype=torch.long).unsqueeze(0)
    expert = model.route_text(text) if expert is None else int(expert) % EXPERTS
    logits, _ = model(x, expert)
    logp = nn.functional.log_softmax(logits, dim=-1)
    vals = logp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return vals.mean(), int(len(b) - 1)


def stage_dpo(model: NovaSparseLM) -> None:
    prefs = [
        ("Give me a password.", "I can help with password best practices, but I should not expose or invent credentials.", "The password is hunter2."),
        ("How should input be validated?", "Validate type, size, shape and allowed values before using input.", "Trust whatever input the caller sends."),
        ("How do I debug a crash?", "Capture the error, isolate the failing case, reproduce it and test one change at a time.", "Restart randomly until it works."),
        ("What is safe secret handling?", "Store secrets in an appropriate secret manager and never commit them to source control.", "Put secrets directly into the repository."),
        ("How do I make an API robust?", "Use strict schemas, timeouts, bounded payloads, clear errors and retries only for transient failures.", "Accept unlimited payloads and ignore errors."),
        ("Can I claim an unverified result is complete?", "No. Report only evidence that was actually produced and verified.", "Yes, if the result sounds convincing."),
    ]
    model.train()
    opts = [torch.optim.AdamW(model.experts[i].parameters(), lr=1e-4) for i in range(EXPERTS)]
    beta = 0.1
    for _ in range(2):
        for prompt, chosen, rejected in prefs:
            expert = model.route_text(prompt)
            pc, _ = sequence_logprob(model, prompt + "\n" + chosen, expert)
            pr, _ = sequence_logprob(model, prompt + "\n" + rejected, expert)
            loss = -nn.functional.logsigmoid(beta * (pc - pr))
            expert = model.route_text(prompt)
            opts[expert].zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.experts[expert].parameters(), 1.0)
            opts[expert].step()
    save_checkpoint(CHECKPOINT, model, TARGET, "DPO")
    save_json(STATE / "dpo.json", {"status": "done", "examples": len(prefs), "license": "CC0-1.0-original-authored"})


def stage_eval(model: NovaSparseLM, raw: bytes) -> dict:
    model.eval()
    losses = []
    for i in range(128):
        s = (i * CONTEXT * 7919) % (len(raw) - CONTEXT - 1)
        b = raw[s:s + CONTEXT + 1]
        x = torch.tensor(list(b[:-1]), dtype=torch.long).unsqueeze(0)
        y = torch.tensor(list(b[1:]), dtype=torch.long).unsqueeze(0)
        expert = i % EXPERTS
        with torch.no_grad():
            logits, _ = model(x, expert)
            loss = nn.functional.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
        losses.append(float(loss.item()))
    mean_loss = sum(losses) / len(losses)
    sample = model.generate("Nova:", max_new_tokens=64, temperature=0.7, top_k=30)
    result = {
        "status": "done",
        "cross_entropy": mean_loss,
        "perplexity": math.exp(min(mean_loss, 20.0)),
        "canary_nonempty": bool(sample.strip()),
        "parameters": parameter_count(model),
    }
    save_json(STATE / "evaluation.json", result)
    return result


def promote(model: NovaSparseLM, seen: int, evaluation: dict) -> Path:
    if seen < TARGET:
        raise RuntimeError(f"production promotion refused: tokens_seen={seen} < {TARGET}")
    if parameter_count(model) < 45_000_000:
        raise RuntimeError("production promotion refused: parameter floor not met")
    if not evaluation.get("canary_nonempty") or not math.isfinite(float(evaluation["perplexity"])):
        raise RuntimeError("production promotion refused: evaluation failed")
    PRODUCTION.mkdir(parents=True, exist_ok=True)
    final = PRODUCTION / "final.pt"
    tmp = final.with_suffix(".pt.tmp")
    torch.save({
        "format": 2,
        "model": model.state_dict(),
        "tokens_seen": seen,
        "parameters": parameter_count(model),
        "stages": ["TRAIN_50M", "SFT", "DPO", "EVALUATION"],
        "corpus_manifest": json.loads((CORPUS / "CORPUS_MANIFEST.json").read_text(encoding="utf-8")),
        "evaluation": evaluation,
        "production": True,
        "synthetic_pretraining": False,
    }, tmp)
    tmp.replace(final)
    save_json(PRODUCTION / "final_manifest.json", {
        "status": "verified_candidate",
        "path": str(final),
        "sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
        "bytes": final.stat().st_size,
        "parameters": parameter_count(model),
        "tokens_seen": seen,
        "evaluation": evaluation,
    })
    # Load and generate once from the actual artifact.
    check = NovaSparseLM()
    payload = torch.load(final, map_location="cpu", weights_only=False)
    check.load_state_dict(payload["model"], strict=True)
    text = check.generate("Nova production check:", max_new_tokens=32, temperature=0.7, top_k=20)
    if not text.strip():
        raise RuntimeError("production verification generation was empty")
    save_json(PRODUCTION / "verification.json", {
        "status": "passed",
        "parameters": parameter_count(check),
        "tokens_seen": seen,
        "generation_nonempty": True,
        "artifact_sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
    })
    return final


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["auto", "pretrain", "finalize"], default="auto")
    args = ap.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    corpus = corpus_path()
    raw = load_bytes(corpus)
    model, seen = ensure_model()

    print(json.dumps({"parameters": parameter_count(model), "corpus_bytes": len(raw), "target_tokens": TARGET, "seen": seen}), flush=True)

    if seen < TARGET:
        budget = min(CHUNK, TARGET - seen)
        seen = train_tokens(model, raw, budget, seen, 1e-3, "TRAIN_50M")
        save_json(STATE / "pipeline.json", {"complete": seen >= TARGET, "stage": "TRAIN_50M", "tokens_seen": seen})
        return 0

    if not (STATE / "sft.json").exists():
        stage_sft(model)
    if not (STATE / "dpo.json").exists():
        stage_dpo(model)
    evaluation = stage_eval(model, raw)
    final = promote(model, seen, evaluation)
    save_json(STATE / "pipeline.json", {"complete": True, "stage": "VERIFY", "tokens_seen": seen, "final": str(final)})
    print(json.dumps({"complete": True, "final": str(final), "parameters": parameter_count(model), "tokens_seen": seen}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
