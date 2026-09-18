from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Optional

import torch
from torch import nn

VOCAB_SIZE = 256
HIDDEN = 700
LAYERS = 1
EXPERTS = 14
CONTEXT = 128


class Expert(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedding = nn.Embedding(VOCAB_SIZE, HIDDEN)
        self.gru = nn.GRU(HIDDEN, HIDDEN, LAYERS, batch_first=True)
        self.head = nn.Linear(HIDDEN, VOCAB_SIZE)

    def forward(self, x: torch.Tensor, hidden: Optional[torch.Tensor] = None):
        z = self.embedding(x)
        return self.gru(z, hidden)


class NovaSparseLM(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.experts = nn.ModuleList(Expert() for _ in range(EXPERTS))

    def forward(self, x: torch.Tensor, expert_idx: int, hidden=None):
        expert_idx = int(expert_idx) % EXPERTS
        z, h = self.experts[expert_idx](x, hidden)
        return self.experts[expert_idx].head(z), h

    @staticmethod
    def route_text(text: str) -> int:
        return int.from_bytes(hashlib.sha256(text.encode("utf-8", "ignore")).digest()[:4], "big") % EXPERTS

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.8,
        top_k: int = 40,
        device: str = "cpu",
    ) -> str:
        self.eval()
        expert_idx = self.route_text(prompt)
        data = prompt.encode("utf-8", "ignore")[:CONTEXT]
        if not data:
            data = b" "
        x = torch.tensor(list(data), dtype=torch.long, device=device).unsqueeze(0)
        with torch.no_grad():
            logits, hidden = self.forward(x, expert_idx)
            last = x[:, -1:]
            out = bytearray(data)
            cur = logits[:, -1, :]
            for _ in range(max_new_tokens):
                cur = cur / max(float(temperature), 1e-4)
                k = min(int(top_k), VOCAB_SIZE)
                vals, inds = torch.topk(cur, k=k, dim=-1)
                probs = torch.softmax(vals, dim=-1)
                pick = torch.multinomial(probs, 1)
                token = int(inds.gather(-1, pick).item())
                out.append(token)
                last = torch.tensor([[token]], dtype=torch.long, device=device)
                cur, hidden = self.forward(last, expert_idx, hidden)
                cur = cur[:, -1, :]
        return out.decode("utf-8", "replace")


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def packed_state(model: nn.Module) -> dict[str, torch.Tensor]:
    packed = {}
    for k, v in model.state_dict().items():
        t = v.detach().cpu()
        packed[k] = t.half() if t.is_floating_point() else t
    return packed


def save_checkpoint(path: Path, model: nn.Module, tokens_seen: int, stage: str, extra: Optional[dict] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": 2,
        "model": packed_state(model),
        "tokens_seen": int(tokens_seen),
        "stage": stage,
        "parameters": parameter_count(model),
        "extra": extra or {},
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)


def load_checkpoint(path: Path, model: nn.Module) -> tuple[int, dict]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or "model" not in payload:
        raise RuntimeError(f"invalid Nova checkpoint: {path}")
    model.load_state_dict(payload["model"], strict=True)
    return int(payload.get("tokens_seen", 0)), payload
