# Demo guide

The workbench is designed for a short engineering walkthrough, not as a chat demo.

## Suggested case

Save the following as `pcie-demo.log`:

```text
2026-01-01T00:00:00Z [INFO] validation workload started
2026-01-01T00:00:01Z [ERROR] PCIE AER completion timeout
2026-01-01T00:00:02Z [ERROR] PCIE link down after retrain
```

Run:

```bash
streamlit run app.py
```

Upload the file and select **Run evidence-grounded triage**. The supported path should show a PCIe/link classification, the matching evidence lines and a read-only next diagnostic.

## Abstention case

Save this as `unknown-demo.log`:

```text
2026-01-01T00:00:00Z [INFO] validation workload started
2026-01-01T00:00:01Z [WARN] intermittent event source unavailable
2026-01-01T00:00:02Z [INFO] validation workload ended
```

The workflow should abstain because none of its supported signatures has enough evidence.

## What to point out

- Evidence is shown verbatim with a source line.
- Unsupported cases return no hypothesis.
- Suggested checks are read-only.
- The structured JSON makes the boundary testable.

## What not to say

- Do not call this post-silicon validation unless real post-silicon data is later added.
- Do not describe the current workflow as an LLM, autonomous agent or RAG system.
- Do not quote the integrated 1.000 macro-F1 without stating that it comes from 24 deterministic synthetic test fixtures; the keyword baseline scored 0.833.
- Do not claim that the tool identifies a physical root cause.

## Screenshot checklist

Capture screenshots only after a local run and make the input visible or identify it in the caption. Useful frames are:

1. supported PCIe case with the evidence expander open
2. abstention case with the reason visible
3. structured report showing evidence IDs and read-only actions

The repository includes screenshots captured from the tested local application in `outputs/screenshots/`. They are application output rather than mockups.
