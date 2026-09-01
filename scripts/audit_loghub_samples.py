#!/usr/bin/env python3
"""Audit observable fields in downloaded LogHub 2k samples.

This reports rows, labels, levels, event IDs, and components. It does not infer
incidents, causes, or diagnostic accuracy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def top(counter: Counter, limit: int = 15) -> list[dict]:
    return [{"value": str(value), "count": count} for value, count in counter.most_common(limit)]


def audit(path: Path) -> dict:
    rows = 0
    labels: Counter = Counter()
    components: Counter = Counter()
    levels: Counter = Counter()
    events: Counter = Counter()
    with path.open(newline="", encoding="utf-8", errors="replace") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        for row in reader:
            rows += 1
            if "Label" in row:
                labels[row.get("Label") or "<EMPTY>"] += 1
            components[row.get("Component") or "<EMPTY>"] += 1
            levels[row.get("Level") or "<EMPTY>"] += 1
            events[row.get("EventId") or "<EMPTY>"] += 1
    result = {
        "file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows": rows, "columns": fields, "unique_components": len(components),
        "unique_event_ids": len(events), "top_components": top(components),
        "levels": top(levels), "top_event_ids": top(events),
    }
    if "Label" in fields:
        result.update({"label_field_present": True, "labels": top(labels),
                       "non_alert_rows": labels.get("-", 0),
                       "alert_tagged_rows": rows - labels.get("-", 0)})
    else:
        result.update({"label_field_present": False, "labels": []})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="data/sample/loghub_2k")
    parser.add_argument("--output", default="outputs/loghub_sample_audit.json")
    args = parser.parse_args()
    source = Path(args.input_dir)
    files = [source / "HDFS_2k.log_structured.csv", source / "BGL_2k.log_structured.csv"]
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise SystemExit(f"missing samples; run scripts/download_loghub.py: {missing}")
    report = {
        "scope": "observable audit of public LogHub 2k structured samples",
        "caveat": "These statistics are not root-cause labels or diagnostic evaluation results.",
        "datasets": [audit(path) for path in files],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
