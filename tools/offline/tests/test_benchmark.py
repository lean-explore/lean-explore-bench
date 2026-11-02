"""Synthetic fixtures only; no real query is copied into these tests."""

from __future__ import annotations

import copy
import datetime as dt
import json
import math
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from leanexplore_benchmark.cli import main
from leanexplore_benchmark.evaluate import compare, evaluate, holm, ranking_metrics
from leanexplore_benchmark.profile import intent_cue, profile, release
from leanexplore_benchmark.querylog import Export, Query, load_export, normalize
from leanexplore_benchmark.report import render
from leanexplore_benchmark.review import make_server, sample


def collection() -> dict:
    return {
        "corpus_revision": "synthetic-v1",
        "queries": [
            {
                "id": "q1",
                "group_id": "task1",
                "track": "human",
                "answerability": "answerable",
                "judgments": {"a": 3, "b": 2, "z": 0},
            },
            {
                "id": "q2",
                "group_id": "task2",
                "track": "agent",
                "answerability": "answerable",
                "judgments": {"c": 3},
            },
            {
                "id": "q3",
                "group_id": "task3",
                "track": "human",
                "answerability": "unanswerable",
                "judgments": {"z": 0},
            },
            {
                "id": "q4",
                "group_id": "task4",
                "track": "unknown",
                "answerability": "unknown",
                "judgments": {},
            },
        ],
    }


def run() -> dict:
    return {
        "name": "synthetic",
        "corpus_revision": "synthetic-v1",
        "max_k": 10,
        "results": {
            "q1": {"status": "ok", "documents": ["a", "z", "b"], "latency_ms": 12},
            "q2": {"status": "ok", "documents": ["c"]},
            "q3": {"status": "ok", "documents": [], "abstained": True},
        },
    }


class LoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "input.json"
        self.payload = {
            "api": [
                {
                    "query": "PrivateSynthetic.canary",
                    "package_filters": [],
                    "result_count": 8,
                    "collected_on": "2026-10-01",
                }
            ]
        }

    def tearDown(self) -> None:
        self.directory.cleanup()

    def load(self, payload: object) -> Export:
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        return load_export(self.path)

    def test_round_trip_and_date_filter(self) -> None:
        exported = self.load(self.payload)
        self.assertEqual(exported.rows[0].source, "api")
        self.assertEqual(len(exported.sha256), 64)
        self.assertFalse(load_export(self.path, dt.date(2026, 10, 2)).rows)
        self.assertEqual(exported.rows_read, 1)

    def test_invalid_fields_fail_without_query_disclosure(self) -> None:
        for field, value in [
            ("query", None),
            ("package_filters", "bad"),
            ("package_filters", [2]),
            ("result_count", True),
            ("result_count", -1),
            ("result_count", 2.5),
            ("collected_on", "20261001"),
            ("collected_on", "bad"),
        ]:
            with self.subTest(field=field, value=value):
                payload = copy.deepcopy(self.payload)
                payload["api"][0][field] = value
                with self.assertRaises(ValueError) as error:
                    self.load(payload)
                self.assertNotIn("canary", str(error.exception))

    def test_missing_field_unknown_source_and_wrong_root(self) -> None:
        for payload in [
            [],
            {"secret-source": []},
            {"api": {}},
            {"api": [None]},
            {"api": [{}]},
        ]:
            with self.assertRaises(ValueError):
                self.load(payload)
        self.path.write_text("{PrivateSynthetic.canary", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Invalid query-export JSON"):
            load_export(self.path)

    def test_null_results_and_empty_query_are_observations(self) -> None:
        self.payload["api"][0].update(query="", result_count=None)
        self.assertEqual(self.load(self.payload).rows[0].text, "")

    def test_normalization_preserves_lean_semantics(self) -> None:
        self.assertEqual(normalize(" e\u0301  x\n"), "é x")
        self.assertNotEqual(normalize("Nat.add"), normalize("nat.add"))
        self.assertNotEqual(normalize("ℝ"), normalize("R"))
        self.assertNotEqual(normalize("x -> y"), normalize("x → y"))


class ProfileTests(unittest.TestCase):
    def rows(self) -> tuple[Query, ...]:
        return tuple(
            Query(i, "api", "CANARY_PRIVATE_SYMBOL.x", (), 8, dt.date(2026, 10, 1))
            for i in range(100)
        )

    def test_export_never_contains_query_identifiers(self) -> None:
        cells = profile(self.rows())
        page = render(cells, "Audit", "hash")
        self.assertNotIn("CANARY", json.dumps(cells) + page)
        self.assertNotIn("https://", page)
        events = [
            c for c in cells if c["view"] == "events" and c["dimension"] == "source"
        ]
        self.assertEqual(events[0]["count"], 100)
        distinct = [
            c
            for c in cells
            if c["view"] == "distinct_requests" and c["dimension"] == "source"
        ]
        self.assertIsNone(distinct[0]["count"])

    def test_small_cell_complement_and_threshold(self) -> None:
        from collections import Counter

        cells = release(
            Counter({("api", "a"): 1, ("web", "b"): 20, ("mcp", "c"): 100}), 10
        )
        self.assertFalse(any(c["category"] in {"a", "b"} for c in cells))
        with self.assertRaises(ValueError):
            profile(self.rows(), 1)
        with self.assertRaises(ValueError):
            profile(())

    def test_intent_is_unknown_or_ambiguous_without_supported_cues(self) -> None:
        self.assertEqual(intent_cue("red triangle"), "unknown")
        self.assertEqual(
            intent_cue("how to use a tactic to prove a goal"), "multiple_cues"
        )
        self.assertEqual(intent_cue("Nat.add_comm"), "known_item_candidate")

    def test_case_filters_and_source_survive_deduplication(self) -> None:
        rows = tuple(
            Query(i, source, text, packages, 1, dt.date(2026, 10, 1))
            for i, (source, text, packages) in enumerate(
                [
                    ("api", "Nat.x", ()),
                    ("api", "nat.x", ()),
                    ("api", "Nat.x", ("Mathlib",)),
                    ("mcp", "Nat.x", ()),
                ]
            )
        )
        selected = sample(Export(rows, "h", 4), 10, 1)
        self.assertEqual(len(selected), 4)


class MetricTests(unittest.TestCase):
    def test_hand_computed_metrics(self) -> None:
        m = ranking_metrics(["z", "a", "b"], {"a": 3, "b": 2, "z": 0}, 3)
        ideal = 3 + 2 / math.log2(3)
        self.assertAlmostEqual(m["ndcg@3"], (3 / math.log2(3) + 1) / ideal)
        self.assertEqual(m["recall@3"], 1)
        self.assertEqual(m["mrr@3"], 0.5)
        self.assertAlmostEqual(m["map@3"], (0.5 + 2 / 3) / 2)

    def test_duplicates_consume_rank_and_do_not_earn_extra_gain(self) -> None:
        m = ranking_metrics(["a", "a", "b"], {"a": 3, "b": 2}, 2)
        self.assertEqual(m["recall@2"], 0.5)
        self.assertEqual(m["judged@2"], 0.5)
        self.assertLess(m["ndcg@2"], 1)

    def test_missing_runs_unknown_and_no_answer_have_different_denominators(
        self,
    ) -> None:
        result = evaluate(collection(), run(), (1, 10, 100))
        metrics = result["summary"]["all"]["metrics"]
        self.assertEqual(metrics["ndcg@10"]["n"], 2)
        self.assertEqual(metrics["request_success"], {"mean": 0.75, "n": 4})
        self.assertEqual(metrics["correct_abstention"], {"mean": 1, "n": 1})
        self.assertNotIn("ndcg@100", metrics)
        self.assertEqual(result["unavailable_cutoffs"], [100])
        r = run()
        del r["results"]["q2"]
        scored = evaluate(collection(), r, (10,))
        self.assertEqual(scored["per_query"][1]["scores"]["ndcg@10"], 0)

    def test_alternative_routes_are_not_mixed_into_a_fake_complete_proof(self) -> None:
        from leanexplore_benchmark.evaluate import premise_metrics

        routes = [[["a", "a2"], ["b"]], [["c"], ["d"]]]
        self.assertEqual(premise_metrics(["a2", "d"], routes, 2)["route_covered@2"], 0)
        self.assertEqual(premise_metrics(["a2", "b"], routes, 2)["route_covered@2"], 1)

    def test_failures_are_not_abstentions(self) -> None:
        r = run()
        r["results"]["q3"] = {"status": "timeout", "documents": []}
        scores = evaluate(collection(), r, (1,))["per_query"][2]["scores"]
        self.assertEqual(scores["correct_abstention"], 0)
        self.assertEqual(scores["request_success"], 0)

    def test_invalid_runs_are_refused(self) -> None:
        mutations = [
            lambda r: r.update(corpus_revision="different"),
            lambda r: r.update(max_k=True),
            lambda r: r["results"]["q1"].update(latency_ms=float("nan")),
            lambda r: r["results"]["q1"].update(status="timeout"),
            lambda r: r["results"]["q1"].update(abstained=True),
            lambda r: r["results"].update(unknown={}),
        ]
        for mutate in mutations:
            r = run()
            mutate(r)
            with self.assertRaises(ValueError):
                evaluate(collection(), r, (10,))
        c = collection()
        c["queries"][0]["judgments"] = {}
        with self.assertRaises(ValueError):
            evaluate(c, run(), (10,))

    def test_identical_comparison_is_zero_reproducible_and_clustered(self) -> None:
        result = evaluate(collection(), run(), (10,))
        paired = compare(result, result, "ndcg@10", samples=100)
        self.assertEqual(paired["candidate_minus_baseline"], 0)
        self.assertEqual(paired["cluster_bootstrap_ci95"], [0, 0])
        self.assertEqual(paired["paired_group_randomization_p"], 1)
        self.assertEqual(paired["n_groups"], 2)
        self.assertEqual(paired, compare(result, result, "ndcg@10", samples=100))
        with self.assertRaises(ValueError):
            compare(result, result, "ndcg@10", track="human", samples=100)

    def test_holm_retains_order_and_bounds(self) -> None:
        self.assertEqual(holm([0.04, 0.001, 0.03]), [0.06, 0.003, 0.06])
        with self.assertRaises(ValueError):
            holm([float("nan")])

    def test_comparison_refuses_changed_judgments_and_metric_coverage(self) -> None:
        first = evaluate(collection(), run(), (10,))
        changed = collection()
        changed["queries"][0]["judgments"]["a"] = 2
        second = evaluate(changed, run(), (10,))
        with self.assertRaisesRegex(ValueError, "judgments differ"):
            compare(first, second, "ndcg@10", samples=100)
        limited = run()
        limited["max_k"] = 5
        with self.assertRaisesRegex(ValueError, "Metric coverage differs"):
            compare(
                first, evaluate(collection(), limited, (10,)), "ndcg@10", samples=100
            )


class ReviewTests(unittest.TestCase):
    def test_local_review_saves_labels_without_query_and_rejects_unsupported_actor(
        self,
    ) -> None:
        row = Query(
            1, "api", "<script>PRIVATE_CANARY</script>", (), 3, dt.date(2026, 10, 1)
        )
        exported = Export((row,), "testhash", 1)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "annotations.json"
            server = make_server(exported, output, "test-reviewer", size=1, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urllib.request.urlopen(base) as response:
                    page = response.read().decode()
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertIn("&lt;script&gt;PRIVATE_CANARY", page)
                token = re.search(r'X-Review-Token":"([^"]+)', page).group(1)
                labels = {
                    "intent": "unknown",
                    "actor": "human_confirmed",
                    "certainty": "ambiguous",
                    "evidence": "annotator_inference",
                    "language": "unknown",
                    "expected_output": "unknown",
                }

                def post() -> bytes:
                    request = urllib.request.Request(
                        base + "/label",
                        data=json.dumps({"position": "1", "labels": labels}).encode(),
                        headers={"X-Review-Token": token},
                    )
                    with urllib.request.urlopen(request) as response:
                        return response.read()

                with self.assertRaises(urllib.error.HTTPError):
                    post()
                labels["actor"] = "unknown"
                self.assertEqual(post(), b"Saved")
                self.assertNotIn("PRIVATE_CANARY", output.read_text())
                self.assertEqual(
                    json.loads(output.read_text())["annotations"]["1"]["intent"],
                    "unknown",
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_sample_is_deterministic_and_retains_inclusion_weights(self) -> None:
        rows = tuple(
            Query(
                i,
                "api" if i < 20 else "web",
                f"Synthetic.term{i}",
                (),
                3,
                dt.date(2026, 10, 1),
            )
            for i in range(40)
        )
        exported = Export(rows, "h", 40)
        selected = sample(exported, 10, 42)
        self.assertEqual(selected, sample(exported, 10, 42))
        self.assertEqual(len(selected), 10)
        self.assertTrue(
            all(population == 20 and n == 5 for _, population, n in selected)
        )


class CommandTests(unittest.TestCase):
    def test_cli_writes_audit_and_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.json"
            source.write_text(
                json.dumps(
                    {
                        "api": [
                            {
                                "query": "PRIVATE_SENTINEL",
                                "package_filters": [],
                                "result_count": 8,
                                "collected_on": "2026-10-01",
                            }
                        ]
                        * 20
                    }
                )
            )
            main(["audit", "--input", str(source), "--out", str(root / "audit")])
            for artifact in (root / "audit").iterdir():
                self.assertNotIn(
                    "PRIVATE_SENTINEL", artifact.read_text(encoding="utf-8")
                )
            (root / "collection.json").write_text(json.dumps(collection()))
            (root / "run.json").write_text(json.dumps(run()))
            main(
                [
                    "evaluate",
                    "--collection",
                    str(root / "collection.json"),
                    "--run",
                    str(root / "run.json"),
                    "--out",
                    str(root / "evaluation.json"),
                ]
            )
            self.assertEqual(
                json.loads((root / "evaluation.json").read_text())["summary"]["all"][
                    "scheduled"
                ],
                4,
            )


if __name__ == "__main__":
    unittest.main()
