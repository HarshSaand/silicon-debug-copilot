#!/usr/bin/env python3
"""Evaluate transparent baselines or JSON predictions on the frozen cases."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

KEYWORDS = {
    "timeout": ("timeout", "deadline", "completion absent"),
    "pcie_link": ("pcie", "link", "retrain", "negotiated"),
    "memory_ecc": ("ecc", "syndrome", "memory scrub"),
    "thermal": ("thermal", "temperature", "throttle"),
    "firmware_mismatch": ("firmware", "incompatible", "expected="),
    "driver_reset": ("driver", "reset", "unresponsive"),
    "unknown_mixed": ("cannot be established", "mixed", "source unavailable"),
}
RUNBOOK = {key: value for key, value in zip(KEYWORDS, ["RB-TIMEOUT", "RB-PCIE", "RB-ECC", "RB-THERMAL", "RB-FW", "RB-RESET", "RB-UNKNOWN"])}
RUNBOOK["normal"] = "RB-UNKNOWN"
CORE_LABELS = {
    "timeout": "timeout", "pcie_link_fault": "pcie_link", "memory_ecc_alert": "memory_ecc",
    "thermal_throttling": "thermal", "firmware_driver_mismatch": "firmware_mismatch",
    "device_reset": "driver_reset", "insufficient_evidence": "unknown_mixed",
}
REQUIRED = {"case_id", "category", "is_anomaly", "evidence_line_ids", "runbook_ids", "abstain"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def baseline(case: dict) -> dict:
    text = " ".join(line["message"] for line in case["lines"]).lower()
    scores = {category: sum(term in text for term in terms) for category, terms in KEYWORDS.items()}
    category = max(scores, key=lambda item: (scores[item], item)) if max(scores.values()) else "normal"
    terms = KEYWORDS.get(category, ())
    evidence = [line["line_id"] for line in case["lines"] if any(term in line["message"].lower() for term in terms)][:3]
    if category == "normal" and case["lines"]:
        evidence = [case["lines"][-1]["line_id"]]
    return {
        "case_id": case["case_id"], "category": category, "is_anomaly": max(scores.values()) > 0,
        "evidence_line_ids": evidence, "runbook_ids": [RUNBOOK[category]], "abstain": category in {"unknown_mixed", "normal"},
    }


def core_prediction(case: dict) -> dict:
    """Adapt the shared silicon_debug workflow without modifying package code."""
    from silicon_debug.parsers import parse_log
    from silicon_debug.workflow import TriageWorkflow

    text = "\n".join(
        f"2026-01-01T00:00:00.{line['timestamp_offset_ms']:03d} [{line.get('severity', 'ERROR')}] {line['message']}"
        for line in case["lines"]
    )
    incident = parse_log(text, case["case_id"])
    report = TriageWorkflow().run(incident)
    evidence_to_line = {event.evidence_id: f"L{event.line_number}" for event in incident.events}
    cited = []
    for evidence in report.evidence:
        line_id = evidence_to_line.get(evidence.evidence_id)
        if line_id and line_id not in cited:
            cited.append(line_id)
    has_error_signal = any(event.severity.value in {"ERROR", "FATAL"} for event in incident.events)
    category = CORE_LABELS.get(report.classification.label, "unknown_mixed")
    if report.abstained and not has_error_signal:
        category = "normal"
    return {
        "case_id": case["case_id"], "category": category,
        "is_anomaly": has_error_signal, "evidence_line_ids": cited[:3],
        "runbook_ids": [RUNBOOK[category]], "abstain": report.abstained,
    }


def f1_by_category(gold: list[dict], pred: dict[str, dict]) -> float:
    categories = sorted({case["category"] for case in gold})
    values = []
    for category in categories:
        tp = sum(pred[c["case_id"]]["category"] == category and c["category"] == category for c in gold)
        fp = sum(pred[c["case_id"]]["category"] == category and c["category"] != category for c in gold)
        fn = sum(pred[c["case_id"]]["category"] != category and c["category"] == category for c in gold)
        values.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    return sum(values) / len(values)


def score(cases: list[dict], predictions: list[dict]) -> dict:
    mapped = {item.get("case_id"): item for item in predictions}
    valid, invented, evidence_hits, evidence_total, cited_total, anomaly_tp, anomaly_total = 0, 0, 0, 0, 0, 0, 0
    usable_cases = []
    for case in cases:
        item = mapped.get(case["case_id"], {})
        if REQUIRED <= item.keys(): valid += 1
        else: continue
        usable_cases.append(case)
        allowed = {line["line_id"] for line in case["lines"]}
        cited = set(item["evidence_line_ids"])
        invented += len(cited - allowed)
        cited_total += len(cited)
        gold_evidence = set(case["gold_evidence_line_ids"])
        evidence_hits += len(cited & gold_evidence)
        evidence_total += len(gold_evidence)
        if case["is_anomaly"]:
            anomaly_total += 1
            anomaly_tp += int(bool(item["is_anomaly"]))
    metrics = {
        "cases": len(cases),
        "schema_success": valid / len(cases) if cases else 0,
        "invented_evidence_ids": invented,
        "evidence_recall_at_3": evidence_hits / evidence_total if evidence_total else 0,
        "citation_precision": (cited_total - invented) / cited_total if cited_total else 0,
        "anomaly_recall": anomaly_tp / anomaly_total if anomaly_total else 0,
    }
    metrics["category_macro_f1"] = f1_by_category(usable_cases, mapped) if usable_cases else 0
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="evals/frozen_benchmark.jsonl")
    parser.add_argument("--split", choices=("train", "dev", "test", "all"), default="test")
    parser.add_argument("--predictions", help="JSONL from a silicon_debug adapter; omit for keyword baseline")
    parser.add_argument("--core", action="store_true", help="evaluate the installed silicon_debug workflow")
    parser.add_argument("--output", default="evals/results.json")
    args = parser.parse_args()
    cases = load_jsonl(Path(args.benchmark))
    if args.split != "all": cases = [case for case in cases if case["split"] == args.split]
    if args.predictions:
        predictions, system = load_jsonl(Path(args.predictions)), "external"
    elif args.core:
        predictions, system = [core_prediction(case) for case in cases], "silicon_debug-core"
    else:
        predictions, system = [baseline(case) for case in cases], "keyword-baseline"
    result = {"split": args.split, "system": system, "metrics": score(cases, predictions)}
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
