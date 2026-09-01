from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .retrieval import BM25Index, SearchHit
from .schemas import Evidence, Incident, Severity

MAX_RESULTS = 20
MAX_QUERY = 200


def search_logs(incident: Incident, query: str, top_k: int = 5) -> list[SearchHit]:
    if not query.strip() or len(query) > MAX_QUERY:
        raise ValueError("query must contain 1-200 characters")
    documents = [Evidence(
        evidence_id=event.evidence_id, source="log", text=event.raw,
        provenance=f"{incident.filename}:line:{event.line_number}",
    ) for event in incident.events]
    return BM25Index(documents).search(query, min(top_k, MAX_RESULTS))


def filter_logs(incident: Incident, severity: Severity | None = None, pattern: str | None = None,
                limit: int = 10) -> list[Evidence]:
    limit = max(1, min(limit, MAX_RESULTS))
    regex = None
    if pattern:
        if len(pattern) > 100 or any(token in pattern for token in ("(?", "\\1", "{100")):
            raise ValueError("unsafe or oversized regex")
        regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for event in incident.events:
        if severity and event.severity != severity:
            continue
        if regex and not regex.search(event.raw):
            continue
        results.append(Evidence(
            evidence_id=event.evidence_id, source="log", text=event.raw,
            provenance=f"{incident.filename}:line:{event.line_number}",
        ))
        if len(results) >= limit:
            break
    return results


def summarize_event_codes(incident: Incident) -> dict[str, int]:
    values = [event.event_code or event.severity.value for event in incident.events]
    return dict(Counter(values).most_common(MAX_RESULTS))


def timeline_window(incident: Incident, evidence_id: str, radius: int = 2) -> list[Evidence]:
    radius = max(0, min(radius, 5))
    index = next((i for i, event in enumerate(incident.events) if event.evidence_id == evidence_id), None)
    if index is None:
        raise KeyError(f"unknown evidence id: {evidence_id}")
    start, end = max(0, index - radius), min(len(incident.events), index + radius + 1)
    return [Evidence(
        evidence_id=event.evidence_id, source="log", text=event.raw,
        provenance=f"{incident.filename}:line:{event.line_number}",
    ) for event in incident.events[start:end]]


def load_runbooks(root: Path | None = None) -> list[Evidence]:
    """Load the small, reviewed runbook corpus with stable citation IDs."""
    runbook_root = root or Path(__file__).resolve().parents[2] / "data" / "runbooks"
    documents: list[Evidence] = []
    for path in sorted(runbook_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"Runbook ID:\s*`([^`]+)`", text)
        runbook_id = match.group(1) if match else path.stem.upper()
        documents.append(Evidence(
            evidence_id=f"doc:{runbook_id}", source="doc", text=text,
            provenance=f"reviewed local runbook:{path.name}",
        ))
    return documents


def search_docs(query: str, top_k: int = 3, root: Path | None = None) -> list[SearchHit]:
    """Search reviewed runbooks; no open-web or arbitrary-file retrieval occurs."""
    if not query.strip() or len(query) > MAX_QUERY:
        raise ValueError("query must contain 1-200 characters")
    return BM25Index(load_runbooks(root)).search(query, min(top_k, 8))
