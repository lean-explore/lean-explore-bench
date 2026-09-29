"""Gate for anything that leaves the server.

The Privacy Policy allows publishing only synthetic queries and aggregate
statistics that "cannot identify anyone or reproduce any individual query".
The server-only explorer may show raw queries, but anything saved or shared
must go through :func:`releasable_counts`. See
``docs/literature/test-collection-construction/query-logs-private-analysis-pipeline.md``.
"""

import pandas as pd

MIN_CELL_COUNT = 10
"""Smallest count that may be published (the ONS default for output checks)."""

ROUNDING_BASE = 10
"""Published counts are rounded to a multiple of this.

Suppressing small cells in each table is not enough on its own: a total
published in one table minus the visible cells of another reveals the
suppressed cell. Rounding every published count (and deriving every
published share from rounded counts) limits what differencing can recover
to the rounding error, which is as large as the suppression threshold.
"""


def round_count(count: int, base: int = ROUNDING_BASE) -> int:
    """Round a count to the nearest multiple of ``base`` (halves round up).

    Args:
        count: A non-negative count.
        base: Rounding base; ``1`` leaves the count unchanged.

    Returns:
        The rounded count.
    """
    return int((count + base // 2) // base * base) if base > 1 else count


_TEXT_COLUMNS = frozenset({"query", "normalized", "packages"})


def releasable_counts(
    frame: pd.DataFrame,
    by: list[str],
    count_column: str = "n",
    min_count: int = MIN_CELL_COUNT,
    rounding_base: int = ROUNDING_BASE,
) -> pd.DataFrame:
    """Count rows per group, suppress small groups and round the rest.

    Suppressed groups are merged into one ``"<suppressed>"`` row. Its count
    is shown only if it is itself at least ``min_count``; otherwise it is
    missing. If exactly one group would be suppressed, the next-smallest
    group is suppressed with it. Every count that is shown is then rounded
    to a multiple of ``rounding_base``, so hidden counts cannot be recovered
    by subtracting across tables.

    Args:
        frame: Rows to count (log rows or distinct queries).
        by: Grouping columns. Text columns (``query``, ``normalized``,
            ``packages``) are refused.
        count_column: Name of the count column.
        min_count: Smallest publishable count.
        rounding_base: Base published counts are rounded to.

    Returns:
        A DataFrame of ``by`` columns and counts.

    Raises:
        ValueError: If a grouping column holds query text.
    """
    refused = _TEXT_COLUMNS.intersection(by)
    if refused:
        raise ValueError(f"Refusing to release counts keyed by {sorted(refused)}")

    counts = (
        frame.groupby(by, observed=True, dropna=False)
        .size()
        .rename(count_column)
        .reset_index()
        .sort_values(count_column)
    )
    small = counts[count_column] < min_count
    if small.sum() == 1 and len(counts) > 2:
        small.iloc[1] = True
    kept = counts.loc[~small].astype({column: "object" for column in by})
    kept[count_column] = [
        round_count(int(n), rounding_base) for n in kept[count_column]
    ]
    parts = [kept.sort_values(by)]
    if small.any():
        total = int(counts.loc[small, count_column].sum())
        shown: object = (
            round_count(total, rounding_base) if total >= min_count else pd.NA
        )
        parts.append(
            pd.DataFrame(
                [{**{column: "<suppressed>" for column in by}, count_column: shown}]
            )
        )
    released = pd.concat(parts, ignore_index=True)
    return released.astype({count_column: "Int64"})
