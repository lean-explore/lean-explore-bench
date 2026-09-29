import datetime

import pandas as pd
from conftest import MakeLog

from lean_explore_bench.analysis.stats import PreparedLog, counts, overview, prepare


def test_prepare_groups_repeats_and_assigns_categories(prepared: PreparedLog) -> None:
    assert len(prepared.rows) == 180
    assert len(prepared.distinct) == 150
    assert prepared.distinct["n_rows"].max() == 2
    assert prepared.rows["category"].notna().all()
    assert prepared.rows["in_repeated_group"].sum() == 60
    assert not prepared.rows["has_package_filter"].any()


def test_small_logs_are_one_category(make_log: MakeLog, day: datetime.date) -> None:
    log = make_log([(f"query {i}", "web", day, 1) for i in range(10)])
    small = prepare(log)
    assert small.categories is None
    assert set(small.distinct["category"]) == {"1"}


def test_counts_keeps_empty_categories() -> None:
    frame = pd.DataFrame({"bin": pd.Categorical(["a"], categories=["a", "b"])})
    assert counts(frame, ["bin"]).to_dict("list") == {"bin": ["a", "b"], "n": [1, 0]}


def test_overview(prepared: PreparedLog) -> None:
    numbers = overview(prepared)
    assert numbers["rows"] == 180
    assert numbers["distinct_queries"] == 150
    assert numbers["days"] == 2
    assert numbers["share_rows_in_repeated_groups"] == 60 / 180
    assert numbers["zero_result_share"] == 0


def test_empty_log_prepares_without_errors(make_log: MakeLog) -> None:
    empty = prepare(make_log([]))
    assert empty.rows.empty and empty.distinct.empty
    assert empty.categories is None
    assert overview(empty)["rows"] == 0


def test_overview_rounds_counts_and_derives_shares(prepared: PreparedLog) -> None:
    rounded = overview(prepared, rounding_base=10)
    assert rounded["rows"] == 180 and rounded["distinct_queries"] == 150
    assert rounded["share_rows_in_repeated_groups"] == 60 / 180
