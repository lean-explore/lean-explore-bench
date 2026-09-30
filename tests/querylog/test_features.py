import pandas as pd
import pytest

from lean_explore_bench.querylog.features import (
    FEATURE_COLUMNS,
    add_features,
    measure,
    skeleton,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Nat.add_comm", "ID"),
        ("Finset.sum_comm or a reindexing lemma", "ID or W W W"),
        ("_ + _ = _ + _", "HOLE + HOLE = HOLE + HOLE"),
        ("(?a : ℕ) ≤ ?a + _", "( HOLE : W ) ≤ HOLE + HOLE"),
        ("matrix invertible iff det is unit", "W W iff W is W"),
        ("x^2 + 1", "W ^ NUM + NUM"),
        ("isCompact IsOpen Fourier", "ID ID W"),
        ("", ""),
    ],
)
def test_skeleton_keeps_structure_not_content(text: str, expected: str) -> None:
    assert skeleton(text) == expected


def test_measure_shares() -> None:
    features = measure("Finset.sum_comm reindex bijection sums mul_comm")
    assert features.n_words == 5
    assert features.identifier_share == pytest.approx(2 / 5)
    assert features.function_word_share == 0
    prose = measure("a continuous function on a compact set is bounded")
    # "a" is a likely variable and is not counted; "on" and "is" are.
    assert prose.function_word_share == pytest.approx(2 / 9)
    assert measure("Riemann integral").identifier_share == 0


def test_measure_symbols_and_latex() -> None:
    features = measure("\\sum_{k=1}^n k^2")
    assert features.latex_commands == 1
    assert features.symbol_share > 0.3


def test_measure_empty_query() -> None:
    features = measure("")
    assert features.n_words == 0
    assert features.identifier_share == features.symbol_share == 0


def test_add_features_adds_every_feature_and_skeleton() -> None:
    frame = pd.DataFrame({"query": ["Nat.succ", "a b c"]}, index=[10, 20])
    result = add_features(frame)
    assert list(result.index) == [10, 20]
    assert set(FEATURE_COLUMNS) | {"skeleton"} <= set(result.columns)
    assert result.loc[10, "skeleton"] == "ID"


def test_add_features_on_an_empty_log_keeps_the_columns() -> None:
    result = add_features(pd.DataFrame({"query": pd.Series([], dtype=str)}))
    assert result.empty
    assert set(FEATURE_COLUMNS) | {"skeleton"} <= set(result.columns)
