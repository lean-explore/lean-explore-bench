"""Publication policy tests use only invented paths."""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "publication_policy", ROOT / "scripts/check_publication.py"
)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class PublicationTests(unittest.TestCase):
    def test_code_and_source_metadata_are_allowed(self):
        for path in (
            "src/invented.py",
            "tools/offline/docs/method.md",
            "tools/offline/migration.json",
        ):
            self.assertTrue(policy.allowed_path(path))

    def test_benchmark_formats_and_disguised_data_directories_are_rejected(self):
        for path in (
            "experiments/example/queries.json",
            "docs/results/report.md",
            "tools/offline/data/fixture.py",
            "tests/reviews.jsonl",
            "docs/measurements.csv",
            "experiments/run.html",
        ):
            self.assertFalse(policy.allowed_path(path))
