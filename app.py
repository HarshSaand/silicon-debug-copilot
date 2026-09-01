"""Streamlit incident workbench. Run: streamlit run app.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st

from silicon_debug.parsers import parse_log
from silicon_debug.workflow import TriageWorkflow


def load_examples() -> dict[str, dict]:
    cases: dict[str, dict] = {}
    with (ROOT / "evals" / "frozen_benchmark.jsonl").open() as handle:
        for line in handle:
            case = json.loads(line)
            if case["split"] == "test":
                cases[case["case_id"]] = case
    return cases


def case_to_log(case: dict) -> str:
    start = datetime(2026, 9, 1, 2, 0, tzinfo=timezone.utc)
    rows = []
    for item in case["lines"]:
        timestamp = start + timedelta(milliseconds=item["timestamp_offset_ms"])
        rows.append(f"{timestamp.isoformat().replace('+00:00', 'Z')} [{item['severity']}] {item['message']}")
    return "\n".join(rows)


st.set_page_config(page_title="Silicon Debug Copilot", page_icon="◈", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #071019; }
    [data-testid="stHeader"] { background: rgba(7,16,25,.82); }
    .hero { padding: 1rem 0 .6rem; }
    .eyebrow { color:#48d1b5; font:700 .72rem/1.2 monospace; letter-spacing:.16em; }
    .hero h1 { color:#f3f7fb; font-size:2.65rem; line-height:1.04; margin:.35rem 0; }
    .hero p { color:#aab8c5; max-width:760px; font-size:1.04rem; }
    .boundary { border:1px solid #263b4b; border-radius:12px; padding:.8rem 1rem; color:#aab8c5; background:#0d1923; }
    .supported { border-left:4px solid #48d1b5; background:#10251f; padding:.8rem 1rem; border-radius:8px; }
    .abstained { border-left:4px solid #f4b860; background:#2a2115; padding:.8rem 1rem; border-radius:8px; }
    div[data-testid="stMetric"] { background:#0d1923; border:1px solid #263b4b; padding:.65rem; border-radius:10px; }
    </style>
    <div class="hero">
      <div class="eyebrow">LOCAL • DETERMINISTIC • EVIDENCE-GROUNDED</div>
      <h1>Silicon Debug Copilot</h1>
      <p>A bounded workbench for triaging system-log failures. It shows the lines behind each conclusion, suggests read-only checks, and abstains when the evidence is weak.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Frozen test split")
    metrics = json.loads((ROOT / "outputs" / "metrics.json").read_text())
    core = metrics["systems"]["silicon_debug-core"]
    st.metric("Category macro-F1", f"{core['category_macro_f1']:.3f}")
    st.metric("Evidence recall@3", f"{core['evidence_recall_at_3']:.3f}")
    st.caption("24 deterministic synthetic test cases. Regression evidence, not hardware validation.")
    st.divider()
    st.caption("No model API. No commands. No corrective actions are executed. Uploaded logs remain in this local process.")

examples = load_examples()
mode = st.radio("Input", ["Curated benchmark case", "Upload a log"], horizontal=True)

if mode == "Curated benchmark case":
    preferred = ["SYN-PCIE-LINK-08", "SYN-UNKNOWN-MIXED-08", "SYN-NORMAL-08", "SYN-MEMORY-ECC-08", "SYN-THERMAL-08"]
    available = [case_id for case_id in preferred if case_id in examples]
    available += [case_id for case_id in examples if case_id not in available]
    case_id = st.selectbox("Example", available, format_func=lambda value: value.replace("SYN-", "").replace("-", " ").title())
    selected = examples[case_id]
    log_text = case_to_log(selected)
    filename = f"{case_id.lower()}.log"
    st.code(log_text, language="text")
    st.caption(f"Synthetic fixture • expected category: {selected['category'].replace('_', ' ')} • split: {selected['split']}")
else:
    uploaded = st.file_uploader("Upload a UTF-8 log", type=["log", "txt"])
    log_text = uploaded.getvalue().decode("utf-8") if uploaded else ""
    filename = uploaded.name if uploaded else "incident.log"

question = st.text_input("Triage question", "What most likely caused this incident?")
if st.button("Run evidence-grounded triage", type="primary", disabled=not log_text):
    try:
        incident = parse_log(log_text, "workbench-incident", filename)
        report = TriageWorkflow().run(incident, question)
        if report.abstained:
            st.markdown("<div class='abstained'><strong>ABSTAINED</strong> — evidence did not support a single diagnosis.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='supported'><strong>SUPPORTED</strong> — the conclusion is backed by cited log lines.</div>", unsafe_allow_html=True)

        left, middle, right = st.columns(3)
        left.metric("Classification", report.classification.label.replace("_", " ").title())
        middle.metric("Rule confidence", f"{report.classification.confidence:.0%}")
        right.metric("Parse coverage", f"{incident.parse_coverage:.0%}")
        if report.abstain_reason:
            st.warning(report.abstain_reason)
        for hypothesis in report.hypotheses:
            st.subheader("Leading hypothesis")
            st.write(hypothesis.statement)
            st.caption("Supports: " + ", ".join(hypothesis.supporting_evidence_ids))

        st.subheader("Safe next diagnostic")
        for action in report.next_diagnostics:
            st.write(action.action)
            st.caption(f"Why: {action.rationale} · Risk: {action.risk}")

        st.subheader("Evidence trail")
        for evidence in report.evidence:
            with st.expander(f"{evidence.evidence_id} · {evidence.provenance}", expanded=evidence.source == "log"):
                st.code(evidence.text, language="text")
        with st.expander("Structured report"):
            payload = report.model_dump(mode="json")
            st.json(payload)
            st.download_button("Download JSON", json.dumps(payload, indent=2), "triage-report.json", "application/json")
        boundary = (
            "this report declines to identify a primary signature because the evidence is insufficient or ambiguous."
            if report.abstained
            else "this report identifies a supported log signature."
        )
        st.markdown(f"<div class='boundary'><strong>Boundary:</strong> {boundary} It does not establish a physical silicon root cause.</div>", unsafe_allow_html=True)
    except (UnicodeDecodeError, ValueError) as exc:
        st.error(str(exc))
