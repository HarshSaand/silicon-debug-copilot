# Thermal triage

Runbook ID: `RB-THERMAL`

Use when measured temperature, throttling, or a thermal shutdown is explicit.

1. Record temperature, threshold, sensor, workload, and timestamp.
2. Verify whether throttling reduced temperature.
3. Correlate fan/power telemetry when present.
4. Stop stress activity when a shutdown threshold is crossed.
5. Do not infer cooling-hardware failure without direct evidence.

