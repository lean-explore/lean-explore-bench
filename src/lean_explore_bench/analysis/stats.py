"""Derived columns and summary tables for a loaded query log.

:func:`prepare` turns a raw log into two frames that every view uses:

- ``rows``: one row per logged search, with its duplicate group and
  category;
- ``distinct``: one row per duplicate group (see
  :mod:`lean_explore_bench.querylog.dedup`), with its measured features,
  skeleton and statistically fitted category.

Summary tables are plain counts over categorical columns, so the same table
can be shown in full on the server or passed through
:func:`lean_explore_bench.analysis.release.releasable_counts` for release.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from lean_explore_bench.analysis.categories import (
    CategoryFit,
    fit_categories,
    style_matrix,
)
from lean_explore_bench.analysis.release import round_count
from lean_explore_bench.querylog.dedup import (
    DEFAULT_THRESHOLD,
    assign_duplicate_groups,
    summarize_distinct_queries,
)
from lean_explore_bench.querylog.features import add_features

LENGTH_BINS = (0, 2, 4, 8, 16, 10_000)
LENGTH_LABELS = ("1–2", "3–4", "5–8", "9–16", "17+")

REPEAT_BINS = (0, 1, 2, 5, 20, 100, 10**9)
REPEAT_LABELS = ("1", "2", "3–5", "6–20", "21–100", "100+")

CORRELATION_COLUMNS = (
    "n_words",
    "n_chars",
    "identifier_share",
    "function_word_share",
    "symbol_share",
    "latex_commands",
    "median_result_count",
    "n_rows",
)
"""Numeric columns of ``distinct`` compared in the correlation view."""

MIN_QUERIES_FOR_CATEGORIES = 50
"""Below this many distinct queries, everything is one category."""


@dataclass(frozen=True)
class PreparedLog:
    """A query log with derived columns.

    Attributes:
        rows: One row per search, with ``group_id``, ``category``,
            ``length_bin``, ``has_package_filter`` and ``in_repeated_group``.
        distinct: One row per duplicate group, with feature columns,
            ``skeleton``, ``category``, ``main_source``, ``length_bin`` and
            ``repeat_bin``.
        categories: The category fit, or ``None`` for very small logs.
    """

    rows: pd.DataFrame
    distinct: pd.DataFrame
    categories: CategoryFit | None


def _bin(values: pd.Series, bins: Sequence[int], labels: Sequence[str]) -> pd.Series:
    return pd.cut(values, bins=list(bins), labels=list(labels))


def _distinct_frame(
    grouped: pd.DataFrame, seed: int
) -> tuple[pd.DataFrame, CategoryFit | None]:
    distinct = add_features(summarize_distinct_queries(grouped))
    distinct["main_source"] = distinct["sources"].map("+".join)
    distinct["length_bin"] = _bin(distinct["n_words"], LENGTH_BINS, LENGTH_LABELS)
    distinct["repeat_bin"] = _bin(distinct["n_rows"], REPEAT_BINS, REPEAT_LABELS)
    fit = None
    if len(distinct) >= MIN_QUERIES_FOR_CATEGORIES:
        fit = fit_categories(style_matrix(distinct, seed=seed), seed=seed)
        distinct["category"] = fit.labels
    else:
        distinct["category"] = "1"
    return distinct, fit


def prepare(
    frame: pd.DataFrame, threshold: float = DEFAULT_THRESHOLD, seed: int = 0
) -> PreparedLog:
    """Deduplicate a log, measure queries and fit categories.

    Args:
        frame: A query log from
            :func:`lean_explore_bench.querylog.load.load_query_log`.
        threshold: Near-duplicate Jaccard threshold.
        seed: Random seed for the category fit.

    Returns:
        A :class:`PreparedLog`.
    """
    grouped = assign_duplicate_groups(frame, threshold)
    distinct, fit = _distinct_frame(grouped, seed)
    rows = grouped.merge(
        distinct[["group_id", "category", "length_bin", "n_rows"]].rename(
            columns={"n_rows": "group_rows"}
        ),
        on="group_id",
    )
    rows["has_package_filter"] = rows["packages"].map(len) > 0
    rows["in_repeated_group"] = rows["group_rows"] > 1
    return PreparedLog(rows=rows, distinct=distinct, categories=fit)


def counts(frame: pd.DataFrame, by: list[str], count_column: str = "n") -> pd.DataFrame:
    """Count rows per group, keeping empty categories.

    Args:
        frame: ``rows`` or ``distinct`` from :class:`PreparedLog`.
        by: Grouping columns.
        count_column: Name of the count column.

    Returns:
        A DataFrame of ``by`` columns and counts.
    """
    return (
        frame.groupby(by, observed=False, dropna=False)
        .size()
        .rename(count_column)
        .reset_index()
    )


def overview(prepared: PreparedLog, rounding_base: int = 1) -> dict[str, float]:
    """Headline numbers about the log.

    Args:
        prepared: A :class:`PreparedLog`.
        rounding_base: Round counts to a multiple of this before computing
            shares, as the release report does; ``1`` keeps exact values.

    Returns:
        Counts and shares describing volume and duplication. None of them
        reveals an individual query.
    """
    rows, distinct = prepared.rows, prepared.distinct

    def count(n: int) -> int:
        return round_count(n, rounding_base)

    total = count(len(rows))

    def share(n: int) -> float:
        return count(n) / total if total else 0.0

    return {
        "rows": total,
        "distinct_queries": count(len(distinct)),
        "days": int(rows["collected_on"].nunique()),
        "categories": int(distinct["category"].nunique()),
        "share_rows_in_repeated_groups": share(int(rows["in_repeated_group"].sum())),
        "zero_result_share": share(int((rows["result_count"] == 0).sum())),
        "package_filter_share": share(int(rows["has_package_filter"].sum())),
    }
