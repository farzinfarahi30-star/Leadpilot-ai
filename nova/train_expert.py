#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import math
import os
import random
from pathlib import Path

import torch
from torch import nn

from model import CONTEXT, EXPERTS, NovaSparseLM, parameter_count

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
BATCH = 32
LOG_EVERY = 500_000


def save_expert(path: Path, model: NovaSparseLM, expert_idx: int, tokens_seen: int, optimizer: torch.optim.Optimizer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    for k, v in model.experts[expert_idx].state_dict().items():
        t = v.detach().cpu()
        state[k] = t.half() if t.is_floating_point() else t
    payload = {
        "format": 2,
        "expert_idx": expert_idx,
        "tokens_seen": int(tokens_seen),
        "parameters": sum(p.numel() for p in model.experts[expert_idx].parameters()),
        "state": state,
        "optimizer": optimizer.state_dict(),
    }
    tmp = path.with_suffix(".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)


def load_expert(path: Path, model: NovaSparseLM, expert_idx: int, optimizer: torch.optim.Optimizer) -> int:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if int(payload.get("expert_idx", -1)) != expert_idx:
        raise RuntimeError("expert checkpoint index mismatch")
    model.experts[expert_idx].load_state_dict(payload["state"], strict=True)
    if payload.get("optimizer"):
        optimizer.load_state_dict(payload["optimizer"])
    return int(payload.get("tokens_seen", 0))


def batch_from_bytes(raw: bytes, batch: int, seq: int, rng: random.Random):
    x = torch.empty((batch, seq), dtype=torch.long)
    y = torch.empty((batch, seq), dtype=torch.long)
    max_start = len(raw) - seq - 1
    if max_start < 0:
        raise RuntimeError("corpus is too small for training context")
    for i in range(batch):
        s = rng.randint(0, max_start)
        x[i] = torch.tensor(list(raw[s:s + seq]), dtype=torch.long)
        y[i] = torch.tensor(list(raw[s + 1:s + seq + 1]), dtype=torch.long)
    return x, y


def train_exact(model: NovaSparseLM, raw: bytes, expert_idx: int, target: int, seen: int, optimizer: torch.optim.Optimizer, rng: random.Random, checkpoint: Path):
    model.train()
    while seen < target:
        remaining = target - seen
        if remaining >= BATCH * CONTEXT:
            batch = BATCH
            seq = CONTEXT
        else:
            batch = min(BATCH, max(1, remaining // CONTEXT))
            if batch == 0:
                batch = 1
            seq = min(CONTEXT, remaining // batch)
            if seq == 0:
                batch, seq = 1, min(CONTEXT, remaining)
            while batch * seq > remaining:
                if batch > 1:
                    batch -= 1
                    seq = min(CONTEXT, remaining // batch)
                else:
                    seq = remaining

        x, y = batch_from_bytes(raw, batch, seq, rng)
        z, _ = model.experts[expert_idx](x)
        logits = model.experts[expert_idx].head(z)
        loss = nn.functional.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.experts[expert_idx].parameters(), 1.0)
        optimizer.step()
        seen += batch * seq

        if seen >= target or seen % LOG_EVERY < batch * seq:
            save_expert(checkpoint, model, expert_idx, seen, optimizer)
            print(json.dumps({
                "expert": expert_idx,
                "tokens_seen": seen,
                "target": target,
                "loss": float(loss.item()),
            }), flush=True)

    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expert", type=int, required=True)
    ap.add_argument("--tokens", type=int, required=True)
    ap.add_argument("--corpus", default=os.environ.get("NOVA_CORPUS", "corpus/wiki.train.tokens"))
    args = ap.parse_args()
    if not 0 <= args.expert < EXPERTS:
        raise ValueError(f"expert must be in [0,{EXPERTS - 1}]")
    if args.tokens <= 0:
        raise ValueError("tokens must be positive")

    torch.set_num_threads(max(1, int(os.getenv("TORCH_THREADS", "4"))))
    seed = 1337 + args.expert
    torch.manual_seed(seed)
    rng = random.Random(seed)

    corpus = Path(args.corpus)
    raw = corpus.read_bytes()
    if len(raw) < CONTEXT + 1:
        raise RuntimeError("corpus is too small")

    model = NovaSparseLM()
    optimizer = torch.optim.AdamW(model.experts[args.expert].parameters(), lr=1e-3)
    checkpoint = STATE / f"expert_{args.expert}.pt"
    seen = 0
    if checkpoint.exists():
        seen = load_expert(checkpoint, model, args.expert, optimizer)
        print(json.dumps({"resume": True, "expert": args.expert, "tokens_seen": seen}), flush=True)

    seen = train_exact(model, raw, args.expert, args.tokens, seen, optimizer, rng, checkpoint)
    print(json.dumps({
        "complete": seen == args.tokens,
        "expert": args.expert,
        "tokens_seen": seen,
        "expert_parameters": sum(p.numel() for p in model.experts[args.expert].parameters()),
    }), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
