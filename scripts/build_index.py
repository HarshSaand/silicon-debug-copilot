#!/usr/bin/env python3
"""Build a transparent token index over the public runbooks."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9][a-z0-9_./-]+")


def runbook_id(text: str, fallback: str) -> str:
    match = re.search(r"Runbook ID: `([^`]+)`", text)
    return match.group(1) if match else fallback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runbooks", default="data/runbooks")
    parser.add_argument("--output", default="data/sample/runbook_index.json")
    args = parser.parse_args()
    docs = []
    for path in sorted(Path(args.runbooks).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        tokens = Counter(TOKEN.findall(text.lower()))
        docs.append({"runbook_id": runbook_id(text, path.stem), "path": str(path), "text": text, "tokens": tokens})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"version": 1, "documents": docs}, indent=2) + "\n", encoding="utf-8")
    print(f"indexed={len(docs)} output={output}")


if __name__ == "__main__":
    main()

