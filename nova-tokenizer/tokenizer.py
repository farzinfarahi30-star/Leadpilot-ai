"""Deterministic UTF-8 byte tokenizer for Nova.

This conservative foundation is lossless for arbitrary Unicode text. A future
trained BPE/SentencePiece vocabulary can replace the byte fallback only through
an explicit, versioned compatibility change.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

class NovaTokenizer:
    FORMAT = "nova-tokenizer-v1"

    def __init__(self, special_tokens: dict[str, int], byte_offset: int = 0):
        if len(set(special_tokens.values())) != len(special_tokens):
            raise ValueError("special token IDs must be unique")
        self.special_tokens = dict(special_tokens)
        self.byte_offset = int(byte_offset)
        self.id_to_special = {v: k for k, v in self.special_tokens.items()}
        if any(i < 0 for i in self.special_tokens.values()):
            raise ValueError("token IDs must be non-negative")

    @classmethod
    def default(cls) -> "NovaTokenizer":
        return cls({"<pad>": 256, "<bos>": 257, "<eos>": 258, "<unk>": 259})

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False) -> list[int]:
        if not isinstance(text, str):
            raise TypeError("text must be str")
        out: list[int] = []
        if add_bos:
            out.append(self.special_tokens["<bos>"])
        out.extend(b + self.byte_offset for b in text.encode("utf-8"))
        if add_eos:
            out.append(self.special_tokens["<eos>"])
        return out

    def decode(self, ids: Iterable[int], skip_special: bool = True) -> str:
        raw = bytearray()
        pieces: list[str] = []
        for token_id in ids:
            token_id = int(token_id)
            if token_id in self.id_to_special:
                if not skip_special:
                    pieces.append(self.id_to_special[token_id])
                continue
            byte = token_id - self.byte_offset
            if not 0 <= byte <= 255:
                raise ValueError(f"unknown token id: {token_id}")
            raw.append(byte)
        if raw:
            pieces.insert(0, raw.decode("utf-8", errors="strict"))
        return "".join(pieces)

    def to_dict(self) -> dict:
        return {
            "format": self.FORMAT,
            "byte_offset": self.byte_offset,
            "special_tokens": self.special_tokens,
            "vocab_size": max([255 + self.byte_offset, *self.special_tokens.values()]) + 1,
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "NovaTokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != cls.FORMAT:
            raise ValueError("unsupported tokenizer format")
        return cls(data["special_tokens"], int(data.get("byte_offset", 0)))

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("text", nargs="?", default="Nova — build the future 🚀")
    args = p.parse_args()
    tok = NovaTokenizer.default()
    ids = tok.encode(args.text, add_bos=True, add_eos=True)
    print(json.dumps({"text": args.text, "ids": ids, "round_trip": tok.decode(ids)}))
