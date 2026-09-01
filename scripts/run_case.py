#!/usr/bin/env python3
"""Run one frozen case through the baseline or an optional silicon_debug API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluate import baseline, load_jsonl


def call_core(case: dict) -> dict | None:
    try:
        from evaluate import core_prediction
    except ImportError:
        return None
    try:
        return core_prediction(case)
    except ImportError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--benchmark", default="evals/frozen_benchmark.jsonl")
    parser.add_argument("--core", action="store_true", help="require silicon_debug.analyze_case")
    args = parser.parse_args()
    cases = {case["case_id"]: case for case in load_jsonl(Path(args.benchmark))}
    if args.case_id not in cases:
        raise SystemExit(f"unknown case_id: {args.case_id}")
    prediction = call_core(cases[args.case_id]) if args.core else None
    if args.core and prediction is None:
        raise SystemExit("the silicon_debug package is not available")
    print(json.dumps(prediction or baseline(cases[args.case_id]), indent=2))


if __name__ == "__main__":
    main()
