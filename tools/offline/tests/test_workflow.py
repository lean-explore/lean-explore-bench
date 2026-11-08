"""Invented cases exercise corpus, split and review boundaries."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from leanexplore_benchmark.cli import main
from leanexplore_benchmark.collection import adapt_run, audit_splits, prepare_collection
from leanexplore_benchmark.corpus import Corpus, fingerprint
from leanexplore_benchmark.evaluate import evaluate
from leanexplore_benchmark.pooling import export_pool, validate_reviews


def corpus(complete=True):
    return Corpus.from_json(
        {
            "corpus_revision": "invented-v1",
            "complete": complete,
            "documents": {
                "a": {
                    "name": "Invented.alpha",
                    "statement": "invented statement",
                    "secret_rank": 1,
                    "source_url": "PRIVATE_CANARY",
                },
                "b": {"name": "Invented.beta"},
                "c": {"name": "Invented.gamma"},
            },
            "aliases": {"alias-a": "a"},
        }
    )


def case(identifier="q1", split="development", targets=None):
    return {
        "id": identifier,
        "query": "Invented question " + identifier,
        "form": "prose",
        "track": "agent",
        "split": split,
        "links": ["request:" + identifier],
        "targets": targets or [],
        "family_reviewed": True,
        "test_exposed": False,
        "reviews": [],
        "provenance": {"private_reference": "PRIVATE_CANARY"},
    }


def dataset(*cases):
    return {
        "schema_version": 1,
        "corpus_revision": "invented-v1",
        "cases": list(cases) or [case()],
    }


def review(identifier="r1", document="a", grade=3, reviewer="assessor-1"):
    return {
        "id": identifier,
        "document_id": document,
        "grade": grade,
        "reviewer": reviewer,
        "assessor_type": "human",
        "status": "accepted",
        "reason": "Invented evidence",
        "uncertain": False,
    }


class CorpusTests(unittest.TestCase):
    def test_inventory_completeness_and_aliases(self):
        self.assertEqual(corpus().availability("alias-a")["document_id"], "a")
        self.assertEqual(corpus().availability("absent")["status"], "absent")
        self.assertEqual(corpus(False).availability("absent")["status"], "unresolved")
        with self.assertRaises(ValueError):
            corpus().require("absent")

    def test_ambiguous_or_dangling_aliases_are_rejected(self):
        for aliases in ({"a": "b"}, {"alias": "missing"}, {"alias": "alias"}):
            with self.subTest(aliases=aliases), self.assertRaises(ValueError):
                Corpus.from_json(
                    {
                        "corpus_revision": "v",
                        "complete": True,
                        "documents": {"a": {}},
                        "aliases": aliases,
                    }
                )


class SplitTests(unittest.TestCase):
    def test_transitive_link_and_alias_leakage(self):
        a, b, c = case("x"), case("y"), case("z", "test", ["alias-a"])
        a["links"] += ["family:shared"]
        b["links"] += ["family:shared"]
        b["targets"] = ["a"]
        with self.assertRaisesRegex(ValueError, "cross split"):
            audit_splits(dataset(a, b, c), corpus())

    def test_identical_queries_and_exposure_are_rejected(self):
        a, b = case("x"), case("y", "test")
        b["query"] = a["query"] + "  "
        with self.assertRaises(ValueError):
            audit_splits(dataset(a, b), corpus())
        for field, value in (("test_exposed", True), ("family_reviewed", False)):
            b = case("test-only", "test")
            b[field] = value
            with self.assertRaises(ValueError):
                audit_splits(dataset(b), corpus())

    def test_components_are_deterministic_and_case_sensitive(self):
        a, b = case("x"), case("y")
        a["links"] += ["family:shared"]
        b["links"] += ["family:shared"]
        groups = audit_splits(dataset(a, b), corpus())["groups"]
        self.assertEqual(groups, audit_splits(dataset(b, a), corpus())["groups"])
        self.assertEqual(len(groups), 1)
        b = case("y", "test")
        b["query"] = a["query"].upper()
        self.assertEqual(len(audit_splits(dataset(a, b), corpus())["groups"]), 2)


class PreparationTests(unittest.TestCase):
    def test_absence_and_proposals_do_not_become_relevance(self):
        c = case(targets=["missing"])
        c["reviews"] = [
            dict(
                review(document="missing"), status="proposed", assessor_type="assistant"
            )
        ]
        prepared = prepare_collection(dataset(c), corpus(), "development")
        self.assertEqual(prepared["collection"]["queries"][0]["judgments"], {})
        self.assertEqual(prepared["sidecar"][0]["availability"][0]["status"], "absent")
        self.assertEqual(
            prepared["collection"]["queries"][0]["answerability"], "unknown"
        )

    def test_accepted_reviews_resolve_aliases_and_keep_originals(self):
        c = case()
        c["reviews"] = [review(document="alias-a")]
        c["answerability"] = "answerable"
        original = copy.deepcopy(c)
        prepared = prepare_collection(dataset(c), corpus(), "development")
        self.assertEqual(prepared["collection"]["queries"][0]["judgments"], {"a": 3})
        self.assertEqual(c, original)
        self.assertEqual(prepared["sidecar"][0]["reviews"], original["reviews"])

    def test_absent_accepted_targets_and_unverified_no_answer_fail(self):
        c = case()
        c["reviews"] = [review(document="missing")]
        with self.assertRaises(ValueError):
            prepare_collection(dataset(c), corpus(), "development")
        c = dict(case(), answerability="unanswerable")
        with self.assertRaises(ValueError):
            prepare_collection(dataset(c), corpus(), "development")

    def test_adjudication_references_all_original_reviews(self):
        c = case()
        c["reviews"] = [review(), review("r2", grade=0, reviewer="assessor-2")]
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            prepare_collection(dataset(c), corpus(), "development")
        decision = dict(review("decision", grade=2), review_ids=["r1"])
        c["adjudications"] = [decision]
        with self.assertRaises(ValueError):
            prepare_collection(dataset(c), corpus(), "development")
        decision["review_ids"].append("r2")
        result = prepare_collection(dataset(c), corpus(), "development")
        self.assertEqual(result["collection"]["queries"][0]["judgments"], {"a": 2})
        self.assertEqual(len(result["sidecar"][0]["reviews"]), 2)

    def test_assistant_uncertain_and_boolean_grades_cannot_be_accepted(self):
        for patch in (
            {"assessor_type": "assistant"},
            {"uncertain": True},
            {"grade": True},
            {"grade": None},
        ):
            c = case()
            c["reviews"] = [dict(review(), **patch)]
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                prepare_collection(dataset(c), corpus(), "development")

    def test_revision_duplicate_and_empty_selection_fail(self):
        for data in (
            dict(dataset(), corpus_revision="wrong"),
            dataset(case(), case()),
            dict(dataset(), schema_version=True),
        ):
            with self.assertRaises(ValueError):
                prepare_collection(data, corpus(), "development")
        with self.assertRaises(ValueError):
            prepare_collection(dataset(), corpus(), "train")


class RunAndPoolTests(unittest.TestCase):
    def prepared(self):
        return prepare_collection(
            dataset(case("q1"), case("q2")), corpus(), "development"
        )

    def test_failures_and_missing_requests_remain_in_denominator(self):
        prepared = self.prepared()
        run = adapt_run(
            [{"id": "q1", "status": "timeout", "documents": []}],
            prepared["collection"],
            corpus(),
            "invented",
            10,
        )
        result = evaluate(prepared["collection"], run, (10, 100))
        self.assertEqual(
            result["summary"]["all"]["metrics"]["request_success"], {"mean": 0, "n": 2}
        )
        self.assertEqual(result["unavailable_cutoffs"], [100])
        self.assertNotIn("ndcg@10", result["summary"]["all"]["metrics"])

    def test_unknown_documents_duplicate_rows_and_failure_documents_fail(self):
        prepared = self.prepared()
        good = {"id": "q1", "status": "ok", "documents": ["a"]}
        for rows in (
            [dict(good, documents=["missing"])],
            [good, good],
            [dict(good, status="error")],
        ):
            with self.assertRaises(ValueError):
                adapt_run(rows, prepared["collection"], corpus(), "invented", 10)

    def test_pool_union_is_blinded_and_deduplicated(self):
        c = case(targets=["c"])
        prepared = prepare_collection(dataset(c), corpus(), "development")
        runs = [
            adapt_run(
                [{"id": "q1", "status": "ok", "documents": docs}],
                prepared["collection"],
                corpus(),
                "PRIVATE_ENGINE",
                10,
            )
            for docs in (["a", "alias-a"], ["b", "a"])
        ]
        bundle = export_pool(prepared, corpus(), runs, 10, 42)
        packet = bundle["packet"]
        self.assertEqual(
            {c["document_id"] for c in packet["cases"][0]["candidates"]},
            {"a", "b", "c"},
        )
        self.assertNotIn("PRIVATE", json.dumps(packet))
        self.assertNotIn("rank", json.dumps(packet))
        self.assertEqual(
            packet, export_pool(prepared, corpus(), runs[::-1], 10, 42)["packet"]
        )
        with self.assertRaises(ValueError):
            export_pool(prepared, corpus(), runs, 100, 42)

    def test_test_packets_and_changed_corpus_are_rejected(self):
        prepared = prepare_collection(dataset(case(split="test")), corpus(), "test")
        run = adapt_run([], prepared["collection"], corpus(), "invented", 10)
        with self.assertRaises(ValueError):
            export_pool(prepared, corpus(), [run], 10, 42)
        prepared = self.prepared()
        with self.assertRaises(ValueError):
            export_pool(prepared, corpus(False), [run], 10, 42)

    def test_submission_binding_and_original_assessor_are_retained(self):
        prepared = self.prepared()
        run = adapt_run(
            [{"id": "q1", "status": "ok", "documents": ["a"]}],
            prepared["collection"],
            corpus(),
            "invented",
            10,
        )
        packet = export_pool(prepared, corpus(), [run], 10, 42)["packet"]
        submission = {
            "packet_sha256": fingerprint(packet),
            "reviewer": "assessor-1",
            "assessor_type": "human",
            "records": [
                {
                    "case_id": "q1",
                    "document_id": "a",
                    "grade": 3,
                    "uncertain": False,
                    "reason": "Invented evidence",
                    "minutes": 2,
                }
            ],
        }
        self.assertEqual(
            validate_reviews(packet, submission)["original_submission"], submission
        )
        self.assertEqual(validate_reviews(packet, submission)["status"], "proposed")
        for patch in (
            {"packet_sha256": "wrong"},
            {"records": [dict(submission["records"][0], document_id="b")]},
            {"records": submission["records"] * 2},
            {"records": [dict(submission["records"][0], uncertain=True)]},
        ):
            with self.assertRaises(ValueError):
                validate_reviews(packet, dict(submission, **patch))


class CommandTests(unittest.TestCase):
    def test_external_workflow_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = {
                "corpus_revision": "invented-v1",
                "complete": True,
                "documents": {"a": {}},
            }
            for name, value in (("cases", dataset()), ("corpus", inventory)):
                (root / (name + ".json")).write_text(json.dumps(value))
            out = root / "prepared"
            command = [
                "prepare",
                "--cases",
                str(root / "cases.json"),
                "--corpus",
                str(root / "corpus.json"),
                "--split",
                "development",
                "--out",
                str(out),
            ]
            main(command)
            self.assertTrue((out / "collection.json").exists())
            observations = {
                "corpus_revision": "invented-v1",
                "records": [{"id": "q1", "status": "ok", "documents": ["a"]}],
            }
            (root / "observations.json").write_text(json.dumps(observations))
            main(
                [
                    "adapt-run",
                    "--observations",
                    str(root / "observations.json"),
                    "--collection",
                    str(out / "collection.json"),
                    "--corpus",
                    str(root / "corpus.json"),
                    "--name",
                    "invented",
                    "--max-k",
                    "10",
                    "--out",
                    str(root / "adapted"),
                ]
            )
            main(
                [
                    "pool",
                    "--prepared",
                    str(out / "prepared.json"),
                    "--corpus",
                    str(root / "corpus.json"),
                    "--run",
                    str(root / "adapted/run.json"),
                    "--depth",
                    "10",
                    "--out",
                    str(root / "pool"),
                ]
            )
            packet = json.loads((root / "pool/packet.json").read_text())
            submission = {
                "packet_sha256": fingerprint(packet),
                "reviewer": "invented-assessor",
                "assessor_type": "human",
                "records": [
                    {
                        "case_id": "q1",
                        "document_id": "a",
                        "grade": 3,
                        "uncertain": False,
                        "reason": "Invented evidence",
                        "minutes": 1,
                    }
                ],
            }
            (root / "assessor.json").write_text(json.dumps(submission))
            main(
                [
                    "check-reviews",
                    "--packet",
                    str(root / "pool/packet.json"),
                    "--submission",
                    str(root / "assessor.json"),
                    "--out",
                    str(root / "checked"),
                ]
            )
            checked = json.loads((root / "checked/submission.json").read_text())
            self.assertEqual(checked["status"], "proposed")
            self.assertEqual(checked["original_submission"], submission)
            with self.assertRaises(FileExistsError):
                main(command)
            repo = root / "repo"
            repo.mkdir()
            (repo / ".git").touch()
            with self.assertRaisesRegex(ValueError, "outside Git"):
                main(command[:-1] + [str(repo / "outputs")])
