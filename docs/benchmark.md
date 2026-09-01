# Benchmark note

## What the saved numbers measure

The repository records two systems on 24 cases in the frozen synthetic test split. The full benchmark has 80 three-line fixtures across six supported fault families, ambiguous mixed behavior and hard-normal behavior. The hard-normal cases reuse terms such as `thermal`, `timeout`, `ECC` and `reset` without representing a failure. The keyword baseline counts phrases directly. The integrated workflow adapts each case into the same parser and `TriageWorkflow` used by the API, then maps returned evidence IDs back to benchmark line IDs.

The saved result is therefore a regression check for:

- benchmark loading and split selection
- prediction schema completeness
- evidence-ID validity
- scoring code behavior
- preservation of an intentionally simple baseline

It is not evidence of field accuracy, semantic reasoning, root-cause identification, hardware diagnosis or runbook-grounded RAG.

## Saved test result

| Metric | Keyword baseline | Integrated workflow | Interpretation |
|---|---:|---:|---|
| cases | 24 | 24 | frozen synthetic test split |
| category macro-F1 | 0.833 | 1.000 | eight generated categories, including normal and mixed cases |
| anomaly recall | 1.000 | 1.000 | every anomalous test case was marked anomalous; normal cases are outside this denominator |
| evidence recall@3 | 0.800 | 0.933 | overlap with the saved gold evidence lines |
| citation precision | 1.000 | 1.000 | no cited line ID was outside its case |
| schema success | 1.000 | 1.000 | every prediction contained required fields |
| invented evidence IDs | 0 | 0 | no fabricated line identifiers |

## Known weaknesses

1. **Lexical coupling:** anomalous category terms used to generate cases closely match the supported signatures. Hard-normal cases make this less trivial but not realistic.
2. **Incomplete anomaly metrics:** normal cases are present, but the saved scorer reports anomaly recall rather than precision, specificity or false-positive rate.
3. **Small test split:** 24 examples cannot support narrow confidence intervals or broad conclusions.
4. **Coupled rules and generator:** the integrated workflow runs end to end, but its signature vocabulary remains close to the case generator.
5. **No document-grounded score:** runbook retrieval occurs at runtime, but the benchmark metrics do not score the selected document or `doc:*` citation.
6. **No realistic ambiguity:** real failures can share vocabulary, unfold over long windows, or require waveform/register/configuration context.

## Acceptance thresholds

The thresholds in `evals/acceptance.json` are engineering regression gates chosen for this synthetic benchmark. They are not production service-level objectives and were not validated against field costs.

## Reproduction

```bash
python scripts/generate_incidents.py
sha256sum -c evals/frozen_benchmark.sha256
python scripts/evaluate.py --split test --output evals/baseline_results.json
python scripts/evaluate.py --split test --core --output evals/core_results.json
```

On macOS, replace `sha256sum` with:

```bash
shasum -a 256 -c evals/frozen_benchmark.sha256
```
