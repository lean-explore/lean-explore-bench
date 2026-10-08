import datetime

from conftest import MakeLog

from lean_explore_bench.querylog.dedup import (
    assign_duplicate_groups,
    distinct_queries,
    summarize_distinct_queries,
)

LONG = "continuous function on a compact set attains its minimum"


def test_exact_and_near_duplicates_within_source_and_day(
    make_log: MakeLog, day: datetime.date
) -> None:
    frame = make_log(
        [
            (LONG, "api", day, 3),
            (LONG, "api", day, 3),
            (LONG.replace(" ", "  ", 1) + " lemma", "api", day, 3),
            (LONG + " lemma", "web", day, 3),
            ("prime divisor", "api", day, 0),
        ]
    )
    groups = assign_duplicate_groups(frame, threshold=0.8)["group_id"].tolist()
    assert groups[0] == groups[1] == groups[2]
    # The web row matches the merged API variant exactly after normalising.
    assert groups[3] == groups[0]
    assert groups[4] != groups[0]
    assert assign_duplicate_groups(frame, threshold=1.0)["group_id"].nunique() == 3


def test_near_duplicates_on_different_days_stay_apart(
    make_log: MakeLog, day: datetime.date
) -> None:
    later = day + datetime.timedelta(days=1)
    frame = make_log([(LONG, "api", day, 3), (LONG + " lemma", "api", later, 3)])
    assert assign_duplicate_groups(frame, threshold=0.8)["group_id"].nunique() == 2


def test_short_queries_are_compared_whole(
    make_log: MakeLog, day: datetime.date
) -> None:
    frame = make_log([("abc", "api", day, 1), ("abd", "api", day, 1)])
    assert assign_duplicate_groups(frame, threshold=0.8)["group_id"].nunique() == 2


def test_distinct_summary(make_log: MakeLog, day: datetime.date) -> None:
    frame = make_log(
        [
            ("prime divisor", "web", day, 0),
            ("prime divisor", "mcp", day + datetime.timedelta(days=1), 4),
        ]
    )
    row = distinct_queries(frame).iloc[0]
    assert (row["n_rows"], row["n_days"], row["n_variants"]) == (2, 2, 1)
    assert row["sources"] == ("mcp", "web")
    assert row["zero_result_share"] == 0.5
    assert row["uses_package_filter"] == 0.0


def test_representative_is_the_most_frequent_variant(
    make_log: MakeLog, day: datetime.date
) -> None:
    frame = make_log(
        [(LONG, "api", day, 1), (LONG, "api", day, 1), (LONG + " lemma", "api", day, 1)]
    )
    summary = summarize_distinct_queries(assign_duplicate_groups(frame))
    assert summary.loc[0, "query"] == LONG
    assert summary.loc[0, "n_variants"] == 2
