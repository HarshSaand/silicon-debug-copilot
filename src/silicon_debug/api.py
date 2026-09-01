from __future__ import annotations

import re
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile

from .parsers import parse_log
from .schemas import IngestResponse, TriageReport, TriageRequest
from .workflow import IncidentStore, TriageWorkflow

app = FastAPI(title="Silicon Debug Copilot", version="0.1.0")
store = IncidentStore()
workflow = TriageWorkflow(store)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/incidents", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(415, "only UTF-8 text logs are supported") from exc
    incident_id = uuid.uuid4().hex[:16]
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file.filename or "incident.log")[:255]
    try:
        incident = parse_log(text, incident_id, safe_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    store.add(incident)
    return IngestResponse(incident_id=incident_id, event_count=len(incident.events), parse_coverage=incident.parse_coverage)


@app.post("/v1/incidents/{incident_id}/triage", response_model=TriageReport)
def triage(incident_id: str, request: TriageRequest) -> TriageReport:
    incident = store.incidents.get(incident_id)
    if not incident:
        raise HTTPException(404, "incident not found")
    return workflow.run(incident, request.question)


@app.get("/v1/traces/{trace_id}")
def trace(trace_id: str) -> dict:
    events = store.traces.get(trace_id)
    if events is None:
        raise HTTPException(404, "trace not found")
    return {"trace_id": trace_id, "events": events}

