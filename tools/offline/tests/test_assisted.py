"""Synthetic checks protect human provenance and unresolved judgments."""

import copy
import unittest

from leanexplore_benchmark.assisted import prepare_assisted
from leanexplore_benchmark.collection import prepare_collection
from leanexplore_benchmark.corpus import fingerprint
from test_workflow import case, corpus, dataset, review


class AssistedTests(unittest.TestCase):
    def setUp(self):
        self.corpus = corpus()
        c = case()
        c["reviews"] = [review(grade=2)]
        self.prepared = prepare_collection(dataset(c), self.corpus, "development")
        self.packet = {
            "schema_version": 1,
            "corpus_revision": self.corpus.revision,
            "cases": [
                {
                    "id": "q1",
                    "query": "invented",
                    "candidates": [
                        {"document_id": d, "evidence": {}} for d in ("a", "b", "c")
                    ],
                }
            ],
        }
        self.submission = {
            "packet_sha256": fingerprint(self.packet),
            "reviewer": "assistant",
            "assessor_type": "assistant",
            "records": [
                {
                    "case_id": "q1",
                    "document_id": d,
                    "grade": grade,
                    "uncertain": grade is None,
                    "reason": "Invented evidence",
                }
                for d, grade in [("a", 0), ("b", 3), ("c", None)]
            ],
        }

    def build(self, **kwargs):
        return prepare_assisted(
            self.prepared,
            self.corpus,
            self.packet,
            self.submission,
            validation_profile="assisted-v1",
            **kwargs,
        )

    def test_human_grade_wins_without_mutating_inputs(self):
        before = copy.deepcopy(self.prepared)
        result = self.build()
        q = result["collection"]["queries"][0]
        self.assertEqual(q["judgments"], {"a": 2, "b": 3})
        self.assertEqual(q["judgment_origins"]["a"], "accepted_human")
        self.assertEqual(q["judgment_origins"]["b"], "assistant_proposal")
        self.assertEqual(self.prepared, before)
        self.assertEqual(len(result["human_check_targets"]), 3)

    def test_exclusion_keeps_case_in_operational_collection(self):
        q = self.build(exclusions={"q1": "Invalid original statement"})["collection"][
            "queries"
        ][0]
        self.assertEqual(q["judgments"], {})
        self.assertEqual(q["answerability"], "unknown")

    def test_rejects_implicit_profile_and_wrong_packet(self):
        with self.assertRaises(ValueError):
            prepare_assisted(
                self.prepared,
                self.corpus,
                self.packet,
                self.submission,
                validation_profile="human",
            )
        self.submission["packet_sha256"] = "wrong"
        with self.assertRaises(ValueError):
            self.build()

    def test_uncertain_or_zero_only_never_means_unanswerable(self):
        self.prepared = prepare_collection(dataset(case()), self.corpus, "development")
        for r in self.submission["records"]:
            r["grade"], r["uncertain"] = 0, False
        self.assertEqual(
            self.build()["collection"]["queries"][0]["answerability"], "unknown"
        )

    def test_unknown_exclusion_and_assessor_are_rejected(self):
        with self.assertRaises(ValueError):
            self.build(exclusions={"missing": "wrong case"})
        self.submission["assessor_type"] = "human"
        with self.assertRaises(ValueError):
            self.build()

    def test_corpus_binding_is_required(self):
        self.packet["corpus_revision"] = "different"
        self.submission["packet_sha256"] = fingerprint(self.packet)
        with self.assertRaises(ValueError):
            self.build()

    def test_human_correction_changes_gain_not_ranked_response(self):
        from leanexplore_benchmark.assisted import apply_human_corrections
        from leanexplore_benchmark.evaluate import ranking_metrics

        assisted = self.build()
        ranked = ["b", "a"]
        before = ranking_metrics(
            ranked, assisted["collection"]["queries"][0]["judgments"], 1
        )
        correction = review(document="b", grade=0)
        correction["case_id"] = "q1"
        updated = apply_human_corrections(assisted, [correction])
        after = ranking_metrics(
            ranked, updated["collection"]["queries"][0]["judgments"], 1
        )
        self.assertEqual(before["success@1"], 1)
        self.assertEqual(after["success@1"], 0)
        self.assertEqual(ranked, ["b", "a"])
        self.assertEqual(assisted["collection"]["queries"][0]["judgments"]["b"], 3)
        self.assertEqual(
            updated["collection"]["queries"][0]["judgment_origins"]["b"],
            "accepted_human",
        )

    def test_assistant_cannot_be_imported_as_human_correction(self):
        from leanexplore_benchmark.assisted import apply_human_corrections

        correction = review(document="b", grade=0)
        correction.update(case_id="q1", assessor_type="assistant", status="proposed")
        with self.assertRaises(ValueError):
            apply_human_corrections(self.build(), [correction])

    def test_rescore_versions_labels_and_keeps_run_identity(self):
        from leanexplore_benchmark.human_rescore import rescore

        profile = self.build()
        run = dict(
            corpus_revision=self.corpus.revision,
            max_k=2,
            results={"q1": dict(status="ok", documents=["b", "a"])},
        )
        original = copy.deepcopy(run)
        decision = review(document="b", grade=0)
        decision["case_id"] = "q1"
        result = rescore(profile, [decision], {"stored": run})
        comparison = result["comparisons"]["stored"]
        self.assertFalse(comparison["ranking_changed"])
        self.assertEqual(comparison["stored_run_sha256"], fingerprint(original))
        self.assertEqual(run, original)
        for stage, expected in [("before", 1), ("after", 0)]:
            metric = comparison[stage]["summary"]["all"]["metrics"]["success@1"]
            self.assertEqual(metric["mean"], expected)
        with self.assertRaises(ValueError):
            rescore(profile, [], {"stored": run})

    def test_assisted_profile_cannot_be_relabelled_as_human_base(self):
        profile = self.build()
        with self.assertRaisesRegex(ValueError, "human-only prepared collection"):
            prepare_assisted(
                profile,
                self.corpus,
                self.packet,
                self.submission,
                validation_profile="assisted-v1",
            )
