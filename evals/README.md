# Frozen evaluation

Generate the deterministic benchmark with:

```bash
python scripts/generate_incidents.py
python scripts/build_index.py
python scripts/evaluate.py --split test --output evals/baseline_results.json
python scripts/evaluate.py --split test --core --output evals/core_results.json
python scripts/audit_loghub_samples.py
```

The benchmark contains 80 explicitly synthetic incidents: 40 train, 16 dev,
and 24 frozen test cases. It includes 10 cases in each of seven incident
families plus 10 hard-normal cases. The test split is frozen by case numbering
within each category and by the SHA-256 sidecar. Do not
tune rules, prompts, retrieval, or thresholds using test results.

The keyword baseline is intentionally simple and transparent. A core copilot
adapter may be supplied to `evaluate.py`; its JSON output is scored under the
same schema and evidence-ID constraints.

`evals/results.json` mirrors the current core result for compatibility. The
canonical paired summary is `outputs/metrics.json`. LogHub sample statistics in
`outputs/loghub_sample_audit.json` are a data audit only and are not root-cause
or diagnostic evaluation results.
