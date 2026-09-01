import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


evaluate = load_module("evaluate", ROOT / "scripts" / "evaluate.py")
generate = load_module("generate", ROOT / "scripts" / "generate_incidents.py")
audit_samples = load_module("audit_samples", ROOT / "scripts" / "audit_loghub_samples.py")


class EvaluationTests(unittest.TestCase):
    def test_generation_is_frozen_and_balanced(self):
        cases = []
        for category, (count, runbook) in generate.CATEGORIES.items():
            cases.extend(generate.make_case(category, number, runbook) for number in range(1, count + 1))
        self.assertEqual(len(cases), 80)
        self.assertTrue(all(case["synthetic"] is True for case in cases))
        self.assertEqual({case["category"] for case in cases}, set(generate.CATEGORIES))
        self.assertEqual({case["split"] for case in cases}, {"train", "dev", "test"})

    def test_keyword_baseline_has_valid_evidence_and_schema(self):
        cases = evaluate.load_jsonl(ROOT / "evals" / "frozen_benchmark.jsonl")
        predictions = [evaluate.baseline(case) for case in cases]
        metrics = evaluate.score(cases, predictions)
        self.assertEqual(metrics["schema_success"], 1.0)
        self.assertEqual(metrics["invented_evidence_ids"], 0)
        self.assertGreaterEqual(metrics["category_macro_f1"], 0.80)

    def test_manifest_hash_matches(self):
        path = ROOT / "evals" / "frozen_benchmark.jsonl"
        expected = (ROOT / "evals" / "frozen_benchmark.sha256").read_text().split()[0]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_unknown_cases_require_abstention(self):
        cases = evaluate.load_jsonl(ROOT / "evals" / "frozen_benchmark.jsonl")
        unknown = [case for case in cases if case["category"] == "unknown_mixed"]
        self.assertTrue(unknown)
        self.assertTrue(all(not case["answerable"] for case in unknown))
        self.assertTrue(all(evaluate.baseline(case)["abstain"] for case in unknown))

    def test_loghub_sample_audit_is_observational(self):
        sample_dir = ROOT / "data" / "sample" / "loghub_2k"
        hdfs = audit_samples.audit(sample_dir / "HDFS_2k.log_structured.csv")
        bgl = audit_samples.audit(sample_dir / "BGL_2k.log_structured.csv")
        self.assertEqual(hdfs["rows"], 2000)
        self.assertEqual(bgl["rows"], 2000)
        self.assertFalse(hdfs["label_field_present"])
        self.assertTrue(bgl["label_field_present"])
        self.assertEqual(bgl["non_alert_rows"] + bgl["alert_tagged_rows"], 2000)


if __name__ == "__main__":
    unittest.main()
