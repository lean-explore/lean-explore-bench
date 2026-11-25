"""Checks for the depth replay helpers and its summary."""

import unittest
from types import SimpleNamespace

import numpy as np

from fusion_variants import rrf, slots
from recall_depth import matched_documents, ordered, ranks_of
from recall_depth_report import memberships, recall_curves, selection_loss


def record(ranks, exhaustive=None, reach=None):
    """A completed journal record with identical ranks at every depth."""
    return dict(
        status="ok",
        depths={
            str(k): dict(ranks=ranks)
            for k in (50, 100, 250, 500, 1000, 2000, 3000, 5000)
        },
        exhaustive_dense=dict(ranks=exhaustive or {}),
        reachability=reach or {},
    )


class HelperTests(unittest.TestCase):
    def test_ranks_keep_first_position_and_report_missing_targets(self):
        self.assertEqual(ranks_of([5, 3, 5, 9], {5, 9, 7}), {"5": 1, "7": None, "9": 4})

    def test_order_matches_engine_tie_rule(self):
        self.assertEqual(ordered({1: 0.5, 2: 0.9, 3: 0.5}), [2, 1, 3])

    def test_matched_documents_ignore_unknown_tokens(self):
        index = SimpleNamespace(
            scores=dict(indices=np.array([0, 2, 2, 3]), indptr=np.array([0, 2, 4])),
            get_tokens_ids=lambda tokens: [t for t in tokens if t in (0, 1)],
        )
        self.assertEqual(matched_documents(index, [0, 1, 7]).tolist(), [0, 2, 3])
        self.assertEqual(len(matched_documents(index, [7])), 0)

    def test_rank_fusion_without_constant_matches_engine_and_weights_move_dense(self):
        lexical = {1: 9.0, 2: 8.0, 3: 7.0}
        dense = {3: 0.9, 4: 0.8, 5: 0.7, 1: 0.6}
        self.assertEqual(rrf(lexical, dense, 0), [3, 1, 4, 2, 5])
        self.assertEqual(rrf(lexical, dense, 60, dense_weight=2.0), [3, 4, 1, 5, 2])

    def test_slots_reserve_dense_share_and_fill_without_duplicates(self):
        self.assertEqual(slots([1, 2, 3], [3, 4, 5, 1], 4, 0.75), [3, 4, 5, 1])
        self.assertEqual(slots([1, 4], [3, 4, 5], 4, 0.5), [3, 4, 1, 5])


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.cases = [
            dict(
                id="q",
                packages=[],
                memberships=[dict(source="s", targets=["A", "B", "Gone"])],
            )
        ]
        self.availability = {"A": 1, "B": 2, "Gone": None}
        self.records = {
            "q": record(
                dict(
                    lexical={"1": 40, "2": None},
                    dense={"1": None, "2": 120},
                    fused={"1": 60, "2": 300},
                    selection={"1": 70},
                ),
                exhaustive={"2": 90},
                reach={
                    "1": dict(lexical_match=True, probed=False),
                    "2": dict(lexical_match=False, probed=True),
                },
            )
        }

    def test_absent_targets_stay_in_the_denominator(self):
        ((_, _, targets),) = memberships(self.cases, self.availability)
        self.assertEqual(targets, [1, 2, "absent:Gone"])
        recall = recall_curves(self.cases, self.records, self.availability)["s"][
            "recall"
        ]
        self.assertAlmostEqual(recall["lexical@50"], 1 / 3)
        self.assertAlmostEqual(recall["union@250"], 2 / 3)
        self.assertAlmostEqual(recall["fused@100"], 1 / 3)
        self.assertAlmostEqual(recall["fused_all@50"], 2 / 3)
        self.assertAlmostEqual(recall["dense_exhaustive@5000"], 1 / 3)

    def test_selection_loss_counts_channel_targets_outside_the_pool(self):
        counts = selection_loss(self.cases, self.records, self.availability)["1000"]
        stats = counts["counts"]["s"]
        self.assertEqual(stats["dense_not_selected"], 1)
        self.assertEqual(stats["union_not_selected"], 1)
        self.assertEqual(
            counts["fused_cutoffs"]["s"]["fused_cutoff_holding_whole_union"], 300
        )


if __name__ == "__main__":
    unittest.main()
