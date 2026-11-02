"""Synthetic workload tests; no real query data."""

from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from leanexplore_benchmark.build import build
from leanexplore_benchmark.insights import analyze
from leanexplore_benchmark.querylog import Query


def row(i: int, day: int = 1, source: str = "api", suffix: str = "") -> Query:
    return Query(
        i,
        source,
        f"PRIVATE_SENTINEL_{i}{suffix}",
        ("PRIVATE_PACKAGE",),
        10,
        dt.date(2026, 1, day),
    )


class InsightTests(unittest.TestCase):
    def test_windows_and_repetition(self) -> None:
        rows = tuple(row(i) for i in range(20)) + tuple(row(i, 2) for i in range(20))
        result = analyze(rows)
        full = result["windows"]["full"]["all"]
        self.assertEqual(full["requests"], 40)
        self.assertEqual(
            full["repeat_accounting"], {"distinct": 20, "extra_occurrences": 20}
        )
        self.assertEqual(full["recurrence_distinct"], {"multiple_days": 20})
        self.assertEqual(result["windows"]["first_day"]["all"]["requests"], 20)
        self.assertEqual(result["windows"]["later"]["all"]["requests"], 20)
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_cross_channel_and_filter_identity(self) -> None:
        rows = tuple(row(i) for i in range(100)) + tuple(
            row(i, source="web") for i in range(100)
        )
        result = analyze(rows)["windows"]["full"]
        self.assertEqual(result["all"]["repeat_accounting"]["distinct"], 100)
        self.assertEqual(
            result["channels"]["api"]["repeat_accounting"]["distinct"], 100
        )
        changed = tuple(
            Query(r.position, r.source, r.text, ("other",), r.result_count, r.day)
            for r in rows
        )
        self.assertEqual(
            analyze(rows + changed)["windows"]["full"]["all"]["repeat_accounting"][
                "distinct"
            ],
            200,
        )

    def test_small_channel_and_no_later_window(self) -> None:
        result = analyze(tuple(row(i) for i in range(8)))
        self.assertIsNone(result["windows"]["full"]["all"]["requests"])
        self.assertEqual(result["windows"]["full"]["channels"], {})
        self.assertIsNone(result["windows"]["later"]["all"])

    def test_order_does_not_change_aggregates(self) -> None:
        rows = tuple(row(i, 1 + i % 2) for i in range(120))
        self.assertEqual(analyze(rows), analyze(tuple(reversed(rows))))

    def test_build_is_deterministic_and_contains_no_input_text(self) -> None:
        payload = {
            "api": [
                {
                    "query": f"PRIVATE_SENTINEL_{i}",
                    "package_filters": ["PRIVATE_PACKAGE"],
                    "result_count": 10,
                    "collected_on": "2026-01-01" if i < 50 else "2026-01-02",
                }
                for i in range(100)
            ]
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "input.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            build(input_path, root / "a")
            build(input_path, root / "b")
            for path in (root / "a").rglob("*"):
                if not path.is_file():
                    continue
                content = path.read_bytes()
                self.assertEqual(
                    content, (root / "b" / path.relative_to(root / "a")).read_bytes()
                )
                self.assertNotIn(b"PRIVATE_SENTINEL", content)
                self.assertNotIn(b"PRIVATE_PACKAGE", content)
            self.assertNotIn(
                "__SUMMARY__", (root / "a/index.html").read_text(encoding="utf-8")
            )

    def test_empty_export_rejected(self) -> None:
        with self.assertRaises(ValueError):
            analyze(())


if __name__ == "__main__":
    unittest.main()
