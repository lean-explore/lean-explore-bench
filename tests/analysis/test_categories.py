import datetime

import numpy as np
import pandas as pd
import pytest
from conftest import MakeLog

from lean_explore_bench.analysis.categories import (
    NUMERIC_FEATURES,
    describe_categories,
    fit_categories,
    select_level,
    stability,
    style_matrix,
)
from lean_explore_bench.analysis.stats import PreparedLog, prepare


def _blobs(
    centres: list[tuple[float, float]], n: int = 60, spread: float = 0.1, seed: int = 0
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.vstack([rng.normal(c, spread, (n, 2)) for c in centres])


def test_style_matrix_is_standardised(prepared: PreparedLog) -> None:
    matrix = style_matrix(prepared.distinct)
    assert matrix.shape[0] == len(prepared.distinct)
    assert np.allclose(matrix.mean(axis=0), 0, atol=1e-6)


def test_stability_of_well_separated_groups() -> None:
    matrix = _blobs([(0, 0), (5, 5)])
    labels = np.repeat([0, 1], 60)
    ari, jaccard = stability(matrix, labels, n_boot=3)
    assert ari > 0.95
    assert (jaccard["jaccard"] > 0.95).all()


def test_select_level_finds_separated_groups() -> None:
    level = select_level(_blobs([(0, 0), (5, 5), (0, 5)]), sizes=range(2, 5), n_boot=3)
    assert level.labels.max() == 2
    assert (level.jaccard["jaccard"] >= 0.75).all()
    assert list(level.selection.columns) == ["categories", "bic", "ari", "min_jaccard"]


def test_select_level_without_a_stable_split_is_one_category() -> None:
    noise = np.random.default_rng(0).uniform(size=(80, 2))
    level = select_level(noise, sizes=range(2, 5), threshold=0.999, n_boot=3)
    assert set(level.labels) == {0}


def test_top_level_keeps_the_largest_stable_split() -> None:
    matrix = _blobs([(0, 0), (0, 5), (5, 0), (5, 5)])
    fit = fit_categories(matrix, min_split=10_000, n_boot=3)
    assert set(fit.labels) == {"1", "2", "3", "4"}
    assert fit.children == {}


def test_fit_categories_builds_paths_from_child_splits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from lean_explore_bench.analysis import categories

    def fake_select(matrix: np.ndarray, **_kwargs: object) -> categories.LevelFit:
        # Top level: first 6 rows vs last 4. Inside the first: halves.
        if len(matrix) == 10:
            labels = np.array([0] * 6 + [1] * 4)
        elif len(matrix) == 6:
            labels = np.array([0, 0, 0, 1, 1, 1])
        else:
            labels = np.zeros(len(matrix), dtype=int)
        empty = pd.DataFrame()
        return categories.LevelFit(labels, matrix, empty, empty)

    monkeypatch.setattr(categories, "select_level", fake_select)
    fit = fit_categories(np.zeros((10, 2)), min_split=5)
    assert fit.labels.tolist() == ["1.1"] * 3 + ["1.2"] * 3 + ["2"] * 4
    assert list(fit.children) == [0]


def test_categories_never_mix_query_shapes(prepared: PreparedLog) -> None:
    distinct = prepared.distinct
    shape = distinct["query"].map(
        lambda q: "name" if "." in q else ("prose" if q.startswith("is ") else "words")
    )
    assert (shape.groupby(distinct["category"]).nunique() == 1).all()
    assert distinct["category"].nunique() >= 3


def test_description_is_topic_free_and_gated(prepared: PreparedLog) -> None:
    summary = describe_categories(prepared.distinct, prepared.rows, min_count=10)
    text = summary.to_string()
    assert not any(query in text for query in prepared.distinct["query"])
    assert summary["share_of_searches"].sum() <= 100
    sizes = prepared.distinct["category"].value_counts()
    assert set(summary["category"]) == set(sizes[sizes >= 10].index)


@pytest.mark.parametrize("min_count", [1, 10_000])
def test_description_respects_min_count(prepared: PreparedLog, min_count: int) -> None:
    summary = describe_categories(prepared.distinct, prepared.rows, min_count=min_count)
    expected = prepared.distinct["category"].nunique() if min_count == 1 else 0
    assert len(summary) == expected


def test_identifier_only_logs_are_clustered_on_numeric_features(
    make_log: MakeLog, day: datetime.date
) -> None:
    # Every skeleton is "ID": one TF-IDF feature, too few for an SVD.
    log = make_log([(f"Foo{i}.bar_{i}", "api", day, 1) for i in range(60)])
    prepared = prepare(log, threshold=1.0)
    assert set(prepared.distinct["skeleton"]) == {"ID"}
    assert len(style_matrix(prepared.distinct)) == 60


def test_style_matrix_without_any_skeleton_tokens() -> None:
    distinct = pd.DataFrame(
        {name: [0.0] * 3 for name in NUMERIC_FEATURES} | {"skeleton": [""] * 3}
    )
    assert style_matrix(distinct).shape == (3, len(NUMERIC_FEATURES))
