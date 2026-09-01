from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    fatal = "FATAL"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(pattern=r"^(log|doc):[A-Za-z0-9_.:#-]+$")
    source: Literal["log", "doc"]
    text: str = Field(min_length=1, max_length=4000)
    provenance: str = Field(min_length=1, max_length=1000)


class LogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(pattern=r"^log:[A-Za-z0-9_.:-]+$")
    line_number: int = Field(ge=1)
    timestamp: datetime | None = None
    severity: Severity = Severity.info
    source: str = Field(default="uploaded", max_length=100)
    event_code: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=1, max_length=10000)
    raw: str = Field(min_length=1, max_length=10000)


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    filename: str = Field(default="incident.log", max_length=255)
    events: list[LogEvent]
    parse_coverage: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)


class Symptom(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rank: int = Field(ge=1, le=3)
    statement: str = Field(min_length=1, max_length=1000)
    supporting_evidence_ids: list[str] = Field(min_length=1, max_length=8)
    contradicting_evidence_ids: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0, le=1)


class DiagnosticAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=1000)
    risk: Literal["read_only"] = "read_only"


class TriageReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str
    classification: Classification
    symptoms: list[Symptom] = Field(default_factory=list, max_length=5)
    hypotheses: list[Hypothesis] = Field(default_factory=list, max_length=3)
    next_diagnostics: list[DiagnosticAction] = Field(default_factory=list, max_length=5)
    evidence: list[Evidence] = Field(default_factory=list, max_length=20)
    abstained: bool
    abstain_reason: str | None = Field(default=None, max_length=1000)
    limitations: list[str] = Field(default_factory=list, max_length=8)
    trace_id: str

    @field_validator("hypotheses")
    @classmethod
    def ranks_are_unique(cls, value: list[Hypothesis]) -> list[Hypothesis]:
        ranks = [item.rank for item in value]
        if len(ranks) != len(set(ranks)):
            raise ValueError("hypothesis ranks must be unique")
        return value


class IngestResponse(BaseModel):
    incident_id: str
    event_count: int
    parse_coverage: float


class TriageRequest(BaseModel):
    question: str = Field(default="What most likely caused this incident?", min_length=3, max_length=500)

