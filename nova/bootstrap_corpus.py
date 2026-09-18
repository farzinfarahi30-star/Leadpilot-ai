from __future__ import annotations
import hashlib
import json
import os
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
CORPUS = ROOT / "corpus"
TARGET = int(os.getenv("NOVA_TARGET_TOKENS", "50000000"))
MAX_BYTES = max(TARGET + 1_000_000, 60_000_000)
URL = os.getenv(
    "NOVA_CORPUS_URL",
    "https://huggingface.co/datasets/Salesforce/wikitext/resolve/main/wikitext-103-v1/train-00000-of-00002.parquet?download=true",
)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    CORPUS.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    target = CORPUS / "wiki.train.tokens"
    parquet = STATE / "wikitext-train-00000-of-00002.parquet"

    if not target.exists() or target.stat().st_size < TARGET + 129:
        if not parquet.exists() or parquet.stat().st_size < 100_000_000:
            tmp = parquet.with_suffix(".tmp")
            urllib.request.urlretrieve(URL, tmp)
            tmp.replace(parquet)

        written = 0
        with target.open("wb") as dst:
            pf = pq.ParquetFile(parquet)
            for batch in pf.iter_batches(batch_size=8192, columns=["text"]):
                for value in batch.column(0).to_pylist():
                    if not value:
                        continue
                    block = (value + "\n").encode("utf-8", "ignore")
                    remaining = MAX_BYTES - written
                    if remaining <= 0:
                        break
                    if len(block) > remaining:
                        block = block[:remaining]
                    dst.write(block)
                    written += len(block)
                    if written >= MAX_BYTES:
                        break
                if written >= MAX_BYTES:
                    break

    actual = target.stat().st_size
    if actual < TARGET + 129:
        raise RuntimeError(f"corpus too small: {actual} bytes; need at least {TARGET + 129}")

    h = hashlib.sha256(target.read_bytes()).hexdigest()
    license_doc = {
        "licensed": True,
        "source": "https://huggingface.co/datasets/Salesforce/wikitext",
        "config": "wikitext-103-v1",
        "license_evidence": "dataset_infos metadata states CC BY-SA 4.0; current dataset card also lists CC BY-SA 3.0/GFDL",
        "source_file": "wikitext-103-v1/train-00000-of-00002.parquet",
        "source_url": URL,
        "token_definition": "one UTF-8 byte is one Nova training token",
        "synthetic_pretraining": False,
        "training_target_tokens": TARGET,
    }
    (CORPUS / "CORPUS_LICENSE.json").write_text(json.dumps(license_doc, indent=2), encoding="utf-8")
    write_json(CORPUS / "CORPUS_MANIFEST.json", {
        "file": str(target),
        "bytes": actual,
        "sha256": h,
        "license": license_doc,
    })
    print(json.dumps({"corpus_bytes": actual, "sha256": h, "target_tokens": TARGET}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
