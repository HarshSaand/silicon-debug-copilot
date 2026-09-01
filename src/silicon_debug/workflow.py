from __future__ import annotations

import uuid
from dataclasses import dataclass

from .observability import Trace
from .schemas import (
    Classification, DiagnosticAction, Evidence, Hypothesis, Incident, Severity,
    Symptom, TriageReport,
)
from .tools import filter_logs, search_docs, search_logs, summarize_event_codes, timeline_window


@dataclass(frozen=True)
class Rule:
    label: str
    terms: tuple[str, ...]
    statement: str
    diagnostic: str


RULES = (
    Rule("pcie_link_fault", ("pcie", "aer", "link down", "link training", "negotiated", "retrain", "degraded"),
         "The evidence is consistent with a PCIe link or transaction fault.",
         "Inspect PCIe AER counters and compare link width/speed with a known-good run."),
    Rule("memory_ecc_alert", ("ecc", "uncorrectable", "corrected error", "memory error", "memory scrub", "syndrome", "recurrence"),
         "The evidence is consistent with a memory ECC event.",
         "Collect read-only ECC counters and correlate them with the failing test window."),
    Rule("thermal_throttling", ("thermal", "overtemp", "throttl", "temperature"),
         "The evidence is consistent with thermal throttling or an over-temperature event.",
         "Compare temperature and clock telemetry with the same workload on a known-good run."),
    Rule("firmware_driver_mismatch", ("firmware mismatch", "version mismatch", "unsupported firmware", "driver mismatch", "firmware api", "expected=", "incompatible interface", "initialization blocked"),
         "The evidence is consistent with incompatible firmware and driver versions.",
         "Record firmware and driver versions and compare them with the validated compatibility matrix."),
    Rule("device_reset", ("gpu reset", "device reset", "driver reset", "resetting device", "reset initiated", "unresponsive", "reset_count", "recovery health"),
         "The evidence is consistent with a device or driver reset.",
         "Inspect the read-only timeline immediately before the reset and compare repeated reset signatures."),
    Rule("timeout", ("timeout", "timed out", "watchdog", "deadline exceeded", "completion absent", "retry held"),
         "The evidence is consistent with a timeout, but the upstream cause is not established.",
         "Collect the preceding event window and compare duration and retry counts with a known-good run."),
)


class IncidentStore:
    def __init__(self) -> None:
        self.incidents: dict[str, Incident] = {}
        self.reports: dict[str, TriageReport] = {}
        self.traces: dict[str, list[dict]] = {}

    def add(self, incident: Incident) -> None:
        self.incidents[incident.incident_id] = incident


class TriageWorkflow:
    def __init__(self, store: IncidentStore | None = None) -> None:
        self.store = store or IncidentStore()

    def run(self, incident: Incident, question: str = "What most likely caused this incident?") -> TriageReport:
        trace = Trace()
        trace.record("INGEST", incident_id=incident.incident_id, events=len(incident.events))
        codes = summarize_event_codes(incident)
        trace.record("NORMALIZE", parse_coverage=incident.parse_coverage, codes=codes)
        diagnostic_events = [event for event in incident.events if event.severity in {Severity.warning, Severity.error, Severity.fatal}]
        searchable = "\n".join(event.message.lower() for event in diagnostic_events)
        candidates: list[tuple[Rule, list[Evidence]]] = []
        for rule in RULES:
            matched = [term for term in rule.terms if term in searchable]
            if not matched:
                continue
            evidence: dict[str, Evidence] = {}
            for term in matched:
                for hit in search_logs(incident, term, top_k=3):
                    evidence[hit.evidence.evidence_id] = hit.evidence
            candidates.append((rule, list(evidence.values())[:6]))
        candidates.sort(key=lambda item: (-len(item[1]), RULES.index(item[0])))
        trace.record("DETECT", candidate_labels=[item[0].label for item in candidates])

        reason = None
        if incident.parse_coverage < 0.20:
            reason = "Insufficient structured log coverage for reliable triage."
        elif not candidates:
            reason = "No supported diagnostic signature was found in the supplied logs."
        elif len(candidates) > 1 and len(candidates[0][1]) == len(candidates[1][1]):
            reason = "Multiple diagnostic signatures have comparable support; a primary subsystem cannot be established."
        elif len(candidates[0][1]) < 2:
            reason = "Fewer than two supporting log events were found for the leading hypothesis."

        if reason:
            evidence = filter_logs(incident, severity=Severity.error, limit=5)
            report = TriageReport(
                incident_id=incident.incident_id,
                classification=Classification(label="insufficient_evidence", confidence=0.0),
                symptoms=[Symptom(text="Observed error-level event.", evidence_ids=[item.evidence_id]) for item in evidence[:3]],
                hypotheses=[],
                next_diagnostics=[DiagnosticAction(
                    action="Collect a longer, timestamped log window and platform/version metadata.",
                    rationale="Additional context is required before proposing a supported cause.",
                )], evidence=evidence, abstained=True, abstain_reason=reason,
                limitations=["Extractive rules cannot establish physical root cause.", "No corrective action was executed."],
                trace_id=trace.trace_id,
            )
        else:
            rule, core_evidence = candidates[0]
            expanded: dict[str, Evidence] = {item.evidence_id: item for item in core_evidence}
            for item in core_evidence[:2]:
                for context in timeline_window(incident, item.evidence_id, radius=1):
                    expanded[context.evidence_id] = context
            evidence = list(expanded.values())[:12]
            doc_hits = search_docs(" ".join(rule.terms), top_k=1)
            if doc_hits:
                evidence.append(doc_hits[0].evidence)
            confidence = min(0.9, 0.52 + 0.08 * min(len(core_evidence), 4))
            supporting = [item.evidence_id for item in core_evidence[:4]]
            if doc_hits:
                supporting.append(doc_hits[0].evidence.evidence_id)
            report = TriageReport(
                incident_id=incident.incident_id,
                classification=Classification(label=rule.label, confidence=confidence),
                symptoms=[Symptom(text=f"Observed {rule.label.replace('_', ' ')} signature.",
                                  evidence_ids=[item.evidence_id for item in core_evidence[:3]])],
                hypotheses=[Hypothesis(rank=1, statement=rule.statement,
                    supporting_evidence_ids=supporting, confidence=confidence)],
                next_diagnostics=[DiagnosticAction(action=rule.diagnostic,
                    rationale="This read-only check can confirm or contradict the leading evidence-backed hypothesis.")],
                evidence=evidence, abstained=False, abstain_reason=None,
                limitations=["This report identifies log signatures, not a confirmed physical root cause.",
                             "Public or synthetic data should not be treated as production silicon validation."],
                trace_id=trace.trace_id,
            )
        self._validate_evidence(report)
        trace.record("REPORT" if not report.abstained else "ABSTAIN", label=report.classification.label)
        run_id = uuid.uuid4().hex
        self.store.add(incident)
        self.store.reports[run_id] = report
        self.store.traces[trace.trace_id] = trace.events
        return report

    @staticmethod
    def _validate_evidence(report: TriageReport) -> None:
        available = {item.evidence_id for item in report.evidence}
        referenced = {eid for symptom in report.symptoms for eid in symptom.evidence_ids}
        referenced |= {eid for hyp in report.hypotheses for eid in hyp.supporting_evidence_ids + hyp.contradicting_evidence_ids}
        missing = referenced - available
        if missing:
            raise ValueError(f"report references missing evidence: {sorted(missing)}")
