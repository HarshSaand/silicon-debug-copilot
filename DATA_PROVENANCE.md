# Data provenance and scope

## Scope boundary

This repository evaluates evidence-linked triage of system logs. It does **not**
contain proprietary semiconductor data, physical register dumps, waveforms, or
verified silicon root-cause labels. The phrase “Silicon Debug Copilot” describes
the intended workflow, not the provenance of the benchmark.

## Public LogHub samples

`scripts/download_loghub.py` downloads only the public 2,000-line structured
samples for HDFS and BGL from the LogPAI LogHub repository. The samples are used
for parser and ingestion smoke tests, not for the frozen diagnostic benchmark.

- Source: https://github.com/logpai/loghub
- HDFS sample: `HDFS/HDFS_2k.log_structured.csv`
- BGL sample: `BGL/BGL_2k.log_structured.csv`
- Expected scale: 2,000 structured rows per dataset
- Access terms: LogHub states that its datasets are freely available for
  research or academic work and requests repository attribution and citation.
  The raw samples are downloaded by users and are not mirrored here.
- Required citation: Zhu et al., “Loghub: A Large Collection of System Log
  Datasets for AI-driven Log Analytics,” ISSRE 2023.

The download script records URL, retrieval time, byte count, and SHA-256 in
`data/sample/loghub_2k/download_manifest.json`. Upstream checksums are not asserted;
the generated manifest is the local provenance record.

## Synthetic benchmark

`data/sample/synthetic_incidents.jsonl` contains 80 deterministic, explicitly
synthetic incidents produced by `scripts/generate_incidents.py`. No event is a
copy of a proprietary log. Cases cover timeout, PCIe/link, memory/ECC, thermal,
firmware mismatch, driver reset, unknown/mixed, and hard-normal behavior. Each case includes
its construction recipe, gold category, anomaly label, minimal evidence IDs,
supported runbook IDs, and an answerability flag.

The synthetic benchmark is useful for testing schemas, retrieval, citations,
abstention, and regression behavior. It cannot establish field accuracy or
generalization to AMD, VDL, ASM, or any production semiconductor platform.

## Frozen evaluation

`evals/frozen_benchmark.jsonl` is generated deterministically and sorted by case
ID. `evals/frozen_benchmark.sha256` freezes its exact bytes. Changing a case,
label, split, or evidence span requires a benchmark version bump and a new hash.
The benchmark must never be used to tune prompts or thresholds after test
results are observed.
