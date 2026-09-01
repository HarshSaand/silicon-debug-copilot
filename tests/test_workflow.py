from silicon_debug.parsers import parse_log
from silicon_debug.workflow import TriageWorkflow


def test_supported_report_has_resolvable_evidence():
    incident = parse_log(
        "2026-01-01T00:00:00 [INFO] start\n"
        "2026-01-01T00:00:01 [ERROR] PCIE AER completion timeout\n"
        "2026-01-01T00:00:02 [ERROR] PCIE link down\n", "pcie")
    report = TriageWorkflow().run(incident)
    assert not report.abstained
    assert report.classification.label == "pcie_link_fault"
    available = {item.evidence_id for item in report.evidence}
    assert set(report.hypotheses[0].supporting_evidence_ids) <= available


def test_unknown_case_abstains():
    incident = parse_log("[INFO] boot complete\n[INFO] workload complete", "ok")
    report = TriageWorkflow().run(incident)
    assert report.abstained
    assert not report.hypotheses


def test_unstructured_case_abstains_even_with_keywords():
    incident = parse_log("pcie failure happened\nanother pcie timeout", "raw")
    report = TriageWorkflow().run(incident)
    assert report.abstained
    assert "structured" in report.abstain_reason.lower()

