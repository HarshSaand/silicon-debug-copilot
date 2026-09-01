import pytest

from silicon_debug.parsers import parse_log
from silicon_debug.schemas import Severity


def test_parse_timestamp_severity_and_ids():
    incident = parse_log("2026-01-01T10:00:00Z [ERROR] PCIE AER failure\n[INFO] boot", "inc-1")
    assert incident.parse_coverage == 1
    assert incident.events[0].severity is Severity.error
    assert incident.events[0].evidence_id.startswith("log:")
    assert incident.events[0].event_code == "PCIE"


def test_rejects_empty_log():
    with pytest.raises(ValueError, match="no non-empty"):
        parse_log("\n", "inc")

