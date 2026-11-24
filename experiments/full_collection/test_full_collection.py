"""Checks for coverage, provenance, scoring and restart safety."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from collection import digest, prepare, source_rows, write
from compare_replay import compare
from diagnose import first_loss
from replay_reranker import reranked_record
from replay_trace import normalize, normalized_trace
from report import render
from run import completed_ids
from score import metrics, rankings, score


class CollectionTests(unittest.TestCase):
    def test_trace_normalization_preserves_original_inference_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            original = dict(
                query_id="a",
                status="ok",
                results=[dict(id=2), dict(id=1)],
                fixed_pool=dict(scores={"neural_only": [0.1, 0.9]}),
                latency_ms=7,
                trace=dict(
                    stages=dict(reranked=[2, 1], results=[1, 2]),
                    elapsed_ms={"reranked": 12},
                ),
            )
            (source / "records.jsonl").write_text(json.dumps(original) + "\n")
            write(source / "contract.json", dict(scheduled_ids=["a"]))
            write(source / "target-availability.json", {"A": 1})
            (source / "executed_runner.py").write_text("# archived runner\n")
            original_hash = digest(source / "records.jsonl")
            write(
                source / "complete.json",
                dict(
                    scheduled=1,
                    completed=1,
                    records_sha256=original_hash,
                    contract_sha256=digest(source / "contract.json"),
                ),
            )
            normalize(SimpleNamespace(run=source, out=root / "derived"))
            derived = json.loads((root / "derived/records.jsonl").read_text())
            self.assertEqual(digest(source / "records.jsonl"), original_hash)
            for key in ("results", "fixed_pool", "latency_ms", "status", "query_id"):
                self.assertEqual(derived[key], original[key])
            self.assertEqual(derived["trace"]["stages"]["results"], [2, 1])
            contract = json.loads((root / "derived/contract.json").read_text())
            self.assertEqual(
                contract["record_transform"]["source_records_sha256"], original_hash
            )

    def test_replay_trace_labels_baseline_timings_and_corrected_results(self):
        original = dict(
            stages=dict(bm25=[1, 2], reranked=[2, 1], results=[1, 2]),
            elapsed_ms=dict(reranked=12),
            _started=100,
        )
        results = [dict(id=2), dict(id=1)]
        corrected = normalized_trace(original, results)
        self.assertEqual(corrected["stages"]["results"], [2, 1])
        self.assertEqual(corrected["stages"]["bm25"], [1, 2])
        self.assertEqual(corrected["baseline_elapsed_ms"], {"reranked": 12})
        self.assertNotIn("elapsed_ms", corrected)
        self.assertEqual(original["stages"]["results"], [1, 2])
        self.assertEqual(normalized_trace(corrected, results), corrected)

    def test_full_replay_audit_excludes_unlabelled_from_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = [
                dict(
                    id=str(i),
                    packages=["Mathlib"],
                    memberships=[dict(source="reference" if i < 2 else "log")],
                )
                for i in range(3)
            ]
            write(root / "cases.json", dict(cases=cases))
            for condition in ("base", "corrected"):
                target = root / condition
                target.mkdir()
                records, rows = [], []
                for i, case in enumerate(cases):
                    results = [
                        dict(id=1, module="Mathlib.A"),
                        dict(id=2, module="Mathlib.B"),
                    ]
                    if condition == "corrected":
                        results.reverse()
                    records.append(
                        dict(
                            query_id=case["id"],
                            status="ok",
                            results=results,
                            trace=dict(stages={}),
                            fixed_pool=dict(
                                candidate_ids=[1, 2], scores={"neural_only": [0.2, 0.8]}
                            ),
                        )
                    )
                    value = 1.0 if condition == "corrected" and i == 0 else 0.0
                    rows.append(
                        dict(
                            query_id=case["id"],
                            source=case["memberships"][0]["source"],
                            source_id=str(i),
                            group="one_target",
                            label_kind="unlabelled"
                            if i == 2
                            else "upstream_single_gold",
                            target_count=int(i < 2),
                            metrics={
                                "current_mixture": {
                                    metric: value
                                    for metric in (
                                        "success@1",
                                        "success@10",
                                        "ndcg@10",
                                        "recall@10",
                                    )
                                }
                            }
                            if i < 2
                            else None,
                        )
                    )
                for name, values in (
                    ("records.jsonl", records),
                    ("per-query.jsonl", rows),
                ):
                    (target / name).write_text(
                        "".join(json.dumps(row) + "\n" for row in values)
                    )
                write(target / "contract.json", {})
                write(
                    target / "complete.json",
                    dict(
                        records_sha256=digest(target / "records.jsonl"),
                        contract_sha256=digest(target / "contract.json"),
                    ),
                )
            compare(
                SimpleNamespace(
                    cases=root / "cases.json",
                    base=root / "base",
                    corrected=root / "corrected",
                    base_scores=root / "base",
                    corrected_scores=root / "corrected",
                    out=root / "comparison.json",
                )
            )
            result = json.loads((root / "comparison.json").read_text())
            self.assertEqual(result["operation"]["requests"], 3)
            self.assertEqual(result["operation"]["top1_changed"], 3)
            self.assertTrue(
                all(
                    row["groups"] == 1 and row["delta"] == 0.5
                    for row in result["paired_intervals"]
                )
            )
            self.assertEqual(
                {row["source"] for row in result["paired_intervals"]}, {"reference"}
            )

    def test_reranker_replay_preserves_filter_and_retrieval(self):
        original = dict(
            status="ok",
            results=[{"id": 1}, {"id": 3}],
            trace={
                "stages": {"bm25": [3, 2, 1], "reranked": [1, 2, 3], "results": [1, 3]},
                "elapsed_ms": {"reranked": 12},
            },
        )
        scores = {
            method: [0.1, 0.9, 0.5]
            for method in ("current_mixture", "neural_only", "without_final_dependency")
        }
        replayed = reranked_record(original, [1, 2, 3], scores, [100, 300, 200], 256)
        self.assertEqual(replayed["results"], [{"id": 3}, {"id": 1}])
        self.assertEqual(replayed["trace"]["stages"]["bm25"], [3, 2, 1])
        self.assertEqual(replayed["trace"]["stages"]["results"], [3, 1])
        self.assertEqual(replayed["trace"]["baseline_elapsed_ms"], {"reranked": 12})
        self.assertNotIn("elapsed_ms", replayed["trace"])
        self.assertEqual(original["trace"]["stages"]["reranked"], [1, 2, 3])
        self.assertEqual(original["trace"]["stages"]["results"], [1, 3])
        self.assertEqual(replayed["fixed_pool"]["truncated_pairs"], 1)
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            reranked_record(
                original,
                [1, 2, 3],
                {"current_mixture": [float("nan"), 0, 1]},
                [1, 1, 1],
                256,
            )

    def test_repeated_queries_retain_all_memberships_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(
                json.dumps(
                    {
                        "api": [
                            dict(
                                query="a b",
                                package_filters=["Mathlib"],
                                collected_on="2026-01-01",
                            ),
                            dict(
                                query="a b",
                                package_filters=["Mathlib"],
                                collected_on="2026-01-02",
                            ),
                            dict(
                                query="a b",
                                package_filters=[],
                                collected_on="2026-01-03",
                            ),
                            dict(
                                query="", package_filters=[], collected_on="2026-01-03"
                            ),
                        ]
                    }
                )
            )
            suite, inventory = prepare(
                [dict(name="log", kind="query_log", path=str(path))]
            )
            self.assertEqual(inventory["records"], 4)
            self.assertEqual(inventory["unique_requests"], 3)
            self.assertEqual(len(suite["cases"][0]["memberships"]), 2)
            self.assertEqual(suite["cases"][-1]["categories"]["form"], "empty")
            self.assertTrue(
                all(
                    m["label_kind"] == "unlabelled"
                    for c in suite["cases"]
                    for m in c["memberships"]
                )
            )

    def test_discussion_links_are_proxies_and_url_decoding_preserves_names(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text(
                json.dumps(
                    dict(
                        id="topic",
                        question="Which result?",
                        channel="discussion",
                        question_url="https://example.org/topic",
                        answer_candidates=[
                            dict(
                                documentation_url="https://example.org/docs?pattern=Nat.add%27"
                            )
                        ],
                    )
                )
                + "\n"
            )
            rows = list(source_rows(dict(kind="discussion_candidates", path=str(path))))
            self.assertEqual(rows[0]["targets"], ["Nat.add'"])
            self.assertEqual(rows[0]["label_kind"], "reply_link_proxy")

    def test_all_reference_styles_and_both_premise_inputs_are_scheduled(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(
                json.dumps(
                    [
                        dict(
                            id="x",
                            full_name="Nat.add",
                            difficulty="Easy",
                            q1a_lean="lean",
                            q1b_latex="latex",
                            q1c_natural="natural",
                            q2_slogan="slogan",
                            q3_nickname="nickname",
                            q4_special_case="special",
                        )
                    ]
                )
            )
            self.assertEqual(
                len(list(source_rows(dict(kind="mathlibqr", path=str(path))))), 6
            )
            path.write_text(
                json.dumps(
                    [
                        dict(
                            id="x",
                            NL_main_result="natural",
                            formal_statement="formal",
                            premise_group=[dict(docs=["A", "B"]), dict(docs=["C"])],
                        )
                    ]
                )
            )
            rows = list(source_rows(dict(kind="mathlibmpr", path=str(path))))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["routes"], [["A", "B"], ["C"]])

    def test_journal_rejects_incomplete_line_changed_schedule_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(json.dumps(dict(query_id="a", status="ok")) + "\n")
            self.assertEqual(completed_ids(path, ["a", "b"]), ["a"])
            with self.assertRaises(ValueError):
                completed_ids(path, ["b", "a"])
            path.write_text(path.read_text() * 2)
            with self.assertRaises(ValueError):
                completed_ids(path, ["a", "b"])
            path.write_text("{")
            with self.assertRaises(ValueError):
                completed_ids(path, ["a"])


class ScoreTests(unittest.TestCase):
    def test_fixed_pool_comparisons_keep_the_engine_output_filter(self):
        record = dict(
            status="ok",
            results=[dict(id=2)],
            trace=dict(stages={}),
            fixed_pool=dict(
                candidate_ids=[1, 2],
                rankings=dict(neural_only=[1, 2], without_final_dependency=[2, 1]),
            ),
        )
        compared = rankings(record)
        for method in (
            "pre_rerank_same_pool",
            "neural_only",
            "without_final_dependency",
            "current_mixture",
        ):
            self.assertEqual(compared[method], [2])

    def test_target_loss_is_a_partition_of_the_observed_pipeline(self):
        record = dict(
            status="ok",
            results=[dict(id=1)],
            trace=dict(
                stages=dict(
                    bm25=[1, 2, 3, 4, 5],
                    semantic=[6],
                    fusion=[1, 2, 3, 4, 6],
                    selection=[1, 2, 3, 6],
                    package_filter=[1, 2, 6],
                    reranker_input=[1, 6],
                )
            ),
        )
        expected = {
            None: "target_name_absent",
            7: "not_in_retrieval_union",
            5: "lost_at_fusion",
            4: "lost_at_selection",
            3: "lost_at_package_filter",
            2: "lost_at_reranker_input",
            6: "removed_by_output_filter",
            1: "retrieved_top10",
        }
        for target, stage in expected.items():
            self.assertEqual(first_loss(target, record), stage)
        record["results"] += [dict(id=i) for i in range(10, 19)] + [dict(id=6)]
        self.assertEqual(first_loss(6, record), "reranked_below_top10")

    def test_public_report_suppresses_small_log_cell_and_complement(self):
        summary = dict(
            inventory=dict(records=65, sources=[], categories=dict(form={})),
            operation=dict(
                requests=65,
                errors=0,
                empty_results=0,
                latency_ms_mean=1,
                top1_changed=0,
                reranked_pairs=0,
                truncated_pairs=0,
            ),
            limitations=[],
            slices=[
                dict(
                    source="query_log",
                    axis="intent_cue",
                    category=label,
                    requests=count,
                    metrics=None,
                    errors=0,
                    empty_results=0,
                    top1_changed=0,
                )
                for label, count in [("small", 5), ("complement", 20), ("visible", 40)]
            ],
        )
        text = render(summary)
        self.assertNotIn("| small |", text)
        self.assertNotIn("| complement |", text)
        self.assertIn("| visible |", text)

    def test_end_to_end_keeps_unlabelled_and_error_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            run.mkdir()
            cases = [
                dict(
                    id="a",
                    categories=dict(
                        form="name",
                        surface="identifier_only",
                        intent_cue="unknown",
                        domain_cue="unknown",
                    ),
                    memberships=[
                        dict(
                            source="reference",
                            source_id="r1",
                            label_kind="upstream_single_gold",
                            targets=["A"],
                        )
                    ],
                ),
                dict(
                    id="b",
                    categories=dict(
                        form="prose",
                        surface="other_text",
                        intent_cue="unknown",
                        domain_cue="unknown",
                    ),
                    memberships=[
                        dict(
                            source="log",
                            source_id="e1",
                            label_kind="unlabelled",
                            targets=[],
                            domain_tags=["algebra", "groups"],
                        )
                    ],
                ),
            ]
            write(root / "cases.json", dict(cases=cases))
            write(root / "inventory.json", dict(unique_requests=2, records=2))
            contract = dict(
                cases_sha256=digest(root / "cases.json"),
                scheduled_ids=["a", "b"],
                settings={},
            )
            write(run / "contract.json", contract)
            write(run / "target-availability.json", {"A": 1})
            records = [
                dict(query_id="a", status="error", results=[], latency_ms=5),
                dict(
                    query_id="b",
                    status="ok",
                    results=[dict(id=2)],
                    latency_ms=10,
                    trace=dict(stages={}),
                    fixed_pool=None,
                ),
            ]
            (run / "records.jsonl").write_text(
                "".join(json.dumps(r) + "\n" for r in records)
            )
            write(
                run / "complete.json",
                dict(
                    completed=2,
                    scheduled=2,
                    records_sha256=digest(run / "records.jsonl"),
                    contract_sha256=digest(run / "contract.json"),
                ),
            )
            score(
                SimpleNamespace(cases=root / "cases.json", run=run, out=root / "scores")
            )
            result = json.loads((root / "scores/summary.json").read_text())
            self.assertEqual(result["operation"]["requests"], 2)
            self.assertEqual(result["operation"]["errors"], 1)
            domains = [r for r in result["slices"] if r["axis"] == "upstream_domain"]
            self.assertEqual({r["category"] for r in domains}, {"algebra", "groups"})
            self.assertTrue(all(r["requests"] == 1 for r in domains))
            full = {r["source"]: r for r in result["slices"] if r["axis"] == "all"}
            self.assertIsNone(full["log"]["metrics"])
            self.assertEqual(
                full["reference"]["metrics"]["current_mixture"]["success@10"], 0
            )
            self.assertEqual(full["reference"]["labelled_requests"], 1)

    def test_unlabelled_is_unavailable_and_absent_gold_stays_in_denominator(self):
        self.assertEqual(metrics([1, 2], set()), {})
        values = metrics([1, 2], {1, "absent:B"})
        self.assertEqual(values["success@10"], 1)
        self.assertEqual(values["recall@10"], 0.5)
        self.assertLess(values["ndcg@10"], 1)

    def test_alternative_routes_do_not_require_every_route(self):
        values = metrics([3], {1, 2, 3}, [[1, 2], [3]])
        self.assertEqual(values["complete_route@1"], 1)
        self.assertEqual(values["recall@1"], 1 / 3)
        self.assertEqual(metrics([1], {1, 2, 3}, [[1, 2], [3]])["complete_route@1"], 0)

    def test_errors_score_zero_and_duplicate_results_are_rejected(self):
        record = dict(status="error", results=[])
        self.assertTrue(all(not r for r in rankings(record).values()))
        self.assertEqual(metrics([], {1})["success@10"], 0)
        with self.assertRaises(ValueError):
            metrics([1, 1], {1})


if __name__ == "__main__":
    unittest.main()
