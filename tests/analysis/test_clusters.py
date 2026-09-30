import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")

from lean_explore_bench.analysis.clusters import (  # noqa: E402
    cluster_keywords,
    cluster_summary,
)


def test_keywords_are_distinctive_per_cluster_and_skip_noise() -> None:
    texts = pd.Series(
        ["Finset.sum x", "Finset.sum y", "group hom", "group kernel", "z"]
    )
    keywords = cluster_keywords(texts, np.array([0, 0, 1, 1, -1]), top_k=1)
    assert keywords == {0: ["Finset.sum"], 1: ["group"]}


def test_keywords_of_all_noise_is_empty() -> None:
    assert cluster_keywords(pd.Series(["a", "b"]), np.array([-1, -1])) == {}


def test_summary_lists_clusters_by_size_with_noise_last() -> None:
    points = pd.DataFrame(
        {
            "query": ["a x", "a y", "a z", "b x", "b y", "noise"],
            "cluster": [1, 1, 1, 0, 0, -1],
            "category": ["2"] * 6,
            "sources": [("api",)] * 5 + [("mcp",)],
            "n_words": [2] * 6,
            "identifier_share": [0.0] * 6,
        }
    )
    summary = cluster_summary(points, examples=2)
    assert summary["cluster"].tolist() == [1, 0, -1]
    assert summary["queries"].tolist() == [3, 2, 1]
    assert summary.loc[2, "sources"] == "mcp 100%"
    assert str(summary.loc[0, "examples"]).count(" | ") == 1
