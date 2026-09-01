import pytest

from silicon_debug.parsers import parse_log
from silicon_debug.schemas import Severity
from silicon_debug.tools import filter_logs, summarize_event_codes, timeline_window


def test_tools_are_bounded_and_evidence_grounded():
    incident = parse_log("[INFO] start\n[ERROR] ECC uncorrectable\n[ERROR] ECC retry failed", "x")
    assert len(filter_logs(incident, Severity.error, limit=100)) == 2
    assert summarize_event_codes(incident)["ECC"] == 2
    assert len(timeline_window(incident, incident.events[1].evidence_id, radius=99)) == 3


def test_unknown_evidence_rejected():
    incident = parse_log("[INFO] start", "x")
    with pytest.raises(KeyError):
        timeline_window(incident, "log:missing")

