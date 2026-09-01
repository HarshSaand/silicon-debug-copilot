# PCIe and link triage

Runbook ID: `RB-PCIE`

Use when logs explicitly report link training, width/speed degradation, replay,
or an uncorrectable link event.

1. Record negotiated generation and lane width.
2. Check whether retraining restored the expected state.
3. Preserve link/AER evidence and timestamps.
4. Compare firmware, topology, and power-state changes near the event.
5. Escalate persistent degradation or uncorrectable errors.

The benchmark uses simulated link messages; it does not validate real PCIe
electrical behavior.

