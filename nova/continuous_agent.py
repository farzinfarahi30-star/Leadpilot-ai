#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import torch
from torch import nn

from model import CONTEXT, EXPERTS, VOCAB_SIZE, NovaSparseLM, parameter_count

SEED = 2026
random.seed(SEED)
torch.manual_seed(SEED)
torch.set_num_threads(4)


def load_payload(path: Path) -> tuple[NovaSparseLM, dict]:
    payload = torch.load(path, map_location='cpu', weights_only=False)
    if not isinstance(payload, dict) or 'model' not in payload:
        raise RuntimeError('invalid production checkpoint')
    model = NovaSparseLM()
    model.load_state_dict(payload['model'], strict=True)
    model.eval()
    return model, payload


def sample_batch(raw: bytes, batch: int, seq: int, rng: random.Random) -> tuple[torch.Tensor, torch.Tensor]:
    if len(raw) < seq + 2:
        raise RuntimeError('corpus split is too small')
    x = torch.empty((batch, seq), dtype=torch.long)
    y = torch.empty((batch, seq), dtype=torch.long)
    high = len(raw) - seq - 1
    for i in range(batch):
        start = rng.randint(0, high)
        x[i] = torch.tensor(list(raw[start:start + seq]), dtype=torch.long)
        y[i] = torch.tensor(list(raw[start + 1:start + seq + 1]), dtype=torch.long)
    return x, y


@torch.no_grad()
def evaluate(model: NovaSparseLM, raw: bytes, samples: int = 64) -> dict:
    model.eval()
    rng = random.Random(9001)
    losses = []
    for i in range(samples):
        x, y = sample_batch(raw, 1, CONTEXT, rng)
        logits, _ = model(x, i % EXPERTS)
        loss = nn.functional.cross_entropy(logits.reshape(-1, VOCAB_SIZE), y.reshape(-1))
        losses.append(float(loss.item()))
    mean_loss = sum(losses) / len(losses)
    ppl = math.exp(min(mean_loss, 20.0))
    canary = model.generate('Nova:', max_new_tokens=48, temperature=0.7, top_k=24)
    return {
        'cross_entropy': mean_loss,
        'perplexity': ppl,
        'canary_nonempty': bool(canary.strip()),
        'parameters': parameter_count(model),
        'samples': samples,
    }


def improve(model: NovaSparseLM, raw: bytes, token_budget: int, lr: float) -> int:
    model.train()
    rng = random.Random(SEED)
    optimizers = [
        torch.optim.AdamW(model.experts[i].parameters(), lr=lr)
        for i in range(EXPERTS)
    ]
    step_tokens = 8 * CONTEXT
    steps = max(1, math.ceil(token_budget / step_tokens))
    seen = 0

    for step in range(steps):
        expert = step % EXPERTS
        x, y = sample_batch(raw, 8, CONTEXT, rng)
        logits, _ = model(x, expert)
        loss = nn.functional.cross_entropy(logits.reshape(-1, VOCAB_SIZE), y.reshape(-1))
        optimizers[expert].zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.experts[expert].parameters(), 1.0)
        optimizers[expert].step()
        seen += step_tokens

    return min(seen, token_budget)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--tokens', type=int, default=250_000)
    ap.add_argument('--lr', type=float, default=2e-4)
    ap.add_argument('--max-regression', type=float, default=0.0025)
    ap.add_argument('--telemetry', default='')
    args = ap.parse_args()

    checkpoint = Path(args.checkpoint)
    corpus_path = Path(args.corpus)
    output = Path(args.output)
    raw = corpus_path.read_bytes()
    if len(raw) < 2 * (CONTEXT + 2):
        raise RuntimeError('corpus is too small for train/holdout evaluation')

    split = int(len(raw) * 0.9)
    train_raw = raw[:split]
    holdout = raw[split:]

    baseline, baseline_payload = load_payload(checkpoint)
    baseline_eval = evaluate(baseline, holdout)

    candidate = NovaSparseLM()
    candidate.load_state_dict(baseline.state_dict(), strict=True)
    additional_tokens = improve(candidate, train_raw, args.tokens, args.lr)
    candidate_eval = evaluate(candidate, holdout)

    baseline_ppl = float(baseline_eval['perplexity'])
    candidate_ppl = float(candidate_eval['perplexity'])
    allowed = baseline_ppl * (1.0 + float(args.max_regression))
    accepted = (
        candidate_eval['canary_nonempty']
        and candidate_eval['parameters'] >= 45_000_000
        and math.isfinite(candidate_ppl)
        and candidate_ppl <= allowed
    )

    result = {
        'status': 'accepted' if accepted else 'rejected',
        'baseline': baseline_eval,
        'candidate': candidate_eval,
        'baseline_tokens_seen': int(baseline_payload.get('tokens_seen', 0)),
        'additional_tokens_trained': additional_tokens,
        'candidate_tokens_seen': int(baseline_payload.get('tokens_seen', 0)) + additional_tokens,
        'max_allowed_perplexity': allowed,
        'max_regression_fraction': float(args.max_regression),
        'telemetry_snapshot': json.loads(args.telemetry) if args.telemetry else None,
        'source_checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
    }

    if not accepted:
        Path(args.output + '.decision.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2), flush=True)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'format': 2,
        'model': candidate.state_dict(),
        'tokens_seen': result['candidate_tokens_seen'],
        'parameters': parameter_count(candidate),
        'stages': ['TRAIN_50M', 'CONTINUOUS_IMPROVEMENT'],
        'production': True,
        'synthetic_pretraining': False,
        'improvement': result,
    }, output)

    result['candidate_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    Path(args.output + '.decision.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
