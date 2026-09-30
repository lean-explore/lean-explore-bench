import pandas as pd
import pytest

from lean_explore_bench.analysis.release import releasable_counts, round_count


def test_keeps_large_groups_sorted() -> None:
    frame = pd.DataFrame({"form": ["b"] * 12 + ["a"] * 20})
    table = releasable_counts(frame, ["form"], min_count=10)
    assert table.to_dict("list") == {"form": ["a", "b"], "n": [20, 10]}  # rounded


def test_a_lone_small_group_takes_the_next_smallest_with_it() -> None:
    frame = pd.DataFrame({"form": ["a"] * 20 + ["b"] * 15 + ["c"] * 3})
    table = releasable_counts(frame, ["form"], min_count=10)
    # "c" alone could be recovered from the total, so "b" is suppressed too.
    assert table.set_index("form")["n"].to_dict() == {"a": 20, "<suppressed>": 20}


def test_suppressed_total_under_the_floor_is_hidden() -> None:
    frame = pd.DataFrame({"form": ["a"] * 20 + ["b"] * 2 + ["c"]})
    table = releasable_counts(frame, ["form"], min_count=10)
    assert pd.isna(table.set_index("form").loc["<suppressed>", "n"])


def test_refuses_text_columns() -> None:
    for column in ("query", "normalized", "packages"):
        with pytest.raises(ValueError):
            releasable_counts(pd.DataFrame({column: ["x"]}), [column])


@pytest.mark.parametrize(
    ("count", "base", "expected"),
    [(0, 10, 0), (4, 10, 0), (5, 10, 10), (14, 10, 10), (15, 10, 20), (23, 1, 23)],
)
def test_round_count(count: int, base: int, expected: int) -> None:
    assert round_count(count, base) == expected


def test_unrounded_counts_are_available_for_server_views() -> None:
    frame = pd.DataFrame({"form": ["a"] * 23})
    assert releasable_counts(frame, ["form"], rounding_base=1)["n"].tolist() == [23]
