from fastapi.testclient import TestClient

from silicon_debug.api import app, store

client = TestClient(app)


def test_health_ingest_triage_and_trace():
    assert client.get("/healthz").json() == {"status": "ok"}
    response = client.post("/v1/incidents", files={"file": ("x.log", b"[ERROR] ECC failure\n[ERROR] ECC uncorrectable", "text/plain")})
    assert response.status_code == 200
    incident_id = response.json()["incident_id"]
    report = client.post(f"/v1/incidents/{incident_id}/triage", json={"question": "What failed?"})
    assert report.status_code == 200
    body = report.json()
    assert body["classification"]["label"] == "memory_ecc_alert"
    trace = client.get(f"/v1/traces/{body['trace_id']}")
    assert trace.status_code == 200


def test_binary_upload_and_missing_incident():
    response = client.post("/v1/incidents", files={"file": ("x.bin", b"\xff\xfe", "application/octet-stream")})
    assert response.status_code == 415
    assert client.post("/v1/incidents/missing/triage", json={"question": "What failed?"}).status_code == 404

