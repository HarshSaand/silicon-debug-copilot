#!/usr/bin/env python3
"""Generate the frozen, explicitly synthetic incident benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SEED = 20260901
CATEGORIES = {
    "timeout": (10, "RB-TIMEOUT"),
    "pcie_link": (10, "RB-PCIE"),
    "memory_ecc": (10, "RB-ECC"),
    "thermal": (10, "RB-THERMAL"),
    "firmware_mismatch": (10, "RB-FW"),
    "driver_reset": (10, "RB-RESET"),
    "unknown_mixed": (10, "RB-UNKNOWN"),
    "normal": (10, "RB-UNKNOWN"),
}

MESSAGES = {
    "timeout": ["request queued id=req-{n}", "deadline exceeded after {ms} ms id=req-{n}", "completion absent; retry held"],
    "pcie_link": ["pcie link training started port={p}", "negotiated Gen3 x4 expected Gen4 x8", "link remains degraded after retrain"],
    "memory_ecc": ["memory scrub started bank={p}", "corrected ECC event bank={p} syndrome=0x{n:02x}", "recurrence count={r}"],
    "thermal": ["workload entered steady state", "sensor gpu0 temperature={temp}C threshold=90C", "thermal throttle asserted"],
    "firmware_mismatch": ["device discovery complete", "firmware API observed=3.{n} expected=4.0", "initialization blocked incompatible interface"],
    "driver_reset": ["driver submitted queue={p}", "device unresponsive; reset initiated", "recovery health check incomplete reset_count={r}"],
    "unknown_mixed": ["intermittent warning source unavailable", "timeout and corrected ECC observed in same window", "primary subsystem cannot be established"],
    "normal": ["thermal policy and timeout counters loaded", "memory scrub schedule enabled; corrected errors=0", "validation completed normally with no reset requested"],
}


def split_for(number: int) -> str:
    return "train" if number <= 5 else "dev" if number <= 7 else "test"


def make_case(category: str, number: int, runbook: str) -> dict:
    case_id = f"SYN-{category.upper().replace('_', '-')}-{number:02d}"
    values = {"n": number, "ms": 900 + number * 137, "p": number % 4, "r": 1 + number % 5, "temp": 89 + number % 8}
    is_anomaly = category != "normal"
    lines = [{
        "line_id": f"L{i+1}", "timestamp_offset_ms": i * 250,
        "severity": "ERROR" if is_anomaly and i > 0 else "INFO",
        "message": msg.format(**values),
    } for i, msg in enumerate(MESSAGES[category])]
    answerable = category not in {"unknown_mixed", "normal"}
    return {
        "case_id": case_id,
        "dataset": "synthetic-v1",
        "synthetic": True,
        "generation_seed": SEED,
        "split": split_for(number),
        "category": category,
        "is_anomaly": is_anomaly,
        "answerable": answerable,
        "lines": lines,
        "gold_evidence_line_ids": ["L2", "L3"] if is_anomaly else ["L3"],
        "gold_runbook_ids": [runbook],
        "gold_action": "manual_review" if not answerable else "follow_runbook",
        "forbidden_claims": ["verified silicon root cause", "production hardware failure"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="data/sample/synthetic_incidents.jsonl")
    parser.add_argument("--benchmark", default="evals/frozen_benchmark.jsonl")
    args = parser.parse_args()
    cases = []
    for category, (count, runbook) in CATEGORIES.items():
        cases.extend(make_case(category, number, runbook) for number in range(1, count + 1))
    cases.sort(key=lambda item: item["case_id"])
    payload = "".join(json.dumps(case, sort_keys=True) + "\n" for case in cases)
    for raw_path in (args.sample, args.benchmark):
        path = Path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode()).hexdigest()
    Path(args.benchmark).with_suffix(".sha256").write_text(
        f"{digest}  {Path(args.benchmark).name}\n", encoding="utf-8"
    )
    print(f"generated={len(cases)} sha256={digest}")


if __name__ == "__main__":
    main()
