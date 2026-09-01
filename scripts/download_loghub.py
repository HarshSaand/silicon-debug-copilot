#!/usr/bin/env python3
"""Download small public LogHub structured samples with provenance metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

FILES = {
    "HDFS_2k.log_structured.csv": "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log_structured.csv",
    "BGL_2k.log_structured.csv": "https://raw.githubusercontent.com/logpai/loghub/master/BGL/BGL_2k.log_structured.csv",
}


def download(url: str, destination: Path) -> dict:
    request = Request(url, headers={"User-Agent": "silicon-debug-copilot-research/1.0"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed allowlist
        payload = response.read()
    destination.write_bytes(payload)
    return {
        "url": url,
        "path": str(destination),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/sample/loghub_2k")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = [download(url, output / name) for name, url in FILES.items()]
    manifest = {
        "source": "https://github.com/logpai/loghub",
        "usage": "parser/ingestion smoke tests only",
        "files": records,
    }
    (output / "download_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
