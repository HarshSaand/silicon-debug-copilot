from __future__ import annotations

import hashlib
import re
from datetime import datetime

from .schemas import Incident, LogEvent, Severity

MAX_UPLOAD_BYTES = 2_000_000
MAX_LINES = 20_000
_LINE = re.compile(
    r"^(?:(?P<ts>\d{4}-\d{2}-\d{2}[T ][0-9:.+Z-]+)\s+)?"
    r"(?:\[(?P<bracket>DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL)\]|"
    r"(?P<plain>DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL)[:\s]+)?(?P<msg>.*)$",
    re.IGNORECASE,
)
_CODE = re.compile(r"\b(?:AER|ECC|GPU|PCIE|THERMAL|FW|DRV|ERR)[-_]?[A-Z0-9]{0,12}\b", re.I)


def _severity(value: str | None, message: str) -> Severity:
    token = (value or "").upper()
    if token == "WARN":
        token = "WARNING"
    if token in Severity._value2member_map_:
        return Severity(token)
    lowered = message.lower()
    if "fatal" in lowered or "panic" in lowered:
        return Severity.fatal
    if "error" in lowered or "failed" in lowered or "timeout" in lowered:
        return Severity.error
    if "warning" in lowered or "warn" in lowered:
        return Severity.warning
    return Severity.info


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_log(text: str, incident_id: str, filename: str = "incident.log") -> Incident:
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_UPLOAD_BYTES:
        raise ValueError(f"upload exceeds {MAX_UPLOAD_BYTES} bytes")
    raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not raw_lines:
        raise ValueError("log contains no non-empty lines")
    if len(raw_lines) > MAX_LINES:
        raise ValueError(f"log exceeds {MAX_LINES} lines")
    events: list[LogEvent] = []
    structured = 0
    for number, raw in enumerate(raw_lines, 1):
        match = _LINE.match(raw)
        assert match is not None
        message = (match.group("msg") or raw).strip()
        ts = _timestamp(match.group("ts"))
        explicit = match.group("bracket") or match.group("plain")
        if ts or explicit:
            structured += 1
        digest = hashlib.sha1(f"{incident_id}:{number}:{raw}".encode()).hexdigest()[:12]
        code_match = _CODE.search(message)
        events.append(LogEvent(
            evidence_id=f"log:{digest}", line_number=number, timestamp=ts,
            severity=_severity(explicit, message),
            event_code=code_match.group(0).upper() if code_match else None,
            message=message, raw=raw,
        ))
    return Incident(
        incident_id=incident_id, filename=filename, events=events,
        parse_coverage=structured / len(events),
    )
