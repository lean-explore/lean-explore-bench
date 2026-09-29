"""Plotly figures for query log views.

Figures built from count tables are safe to release once the tables have
passed :func:`lean_explore_bench.analysis.release.releasable_counts`.
:func:`query_map` shows individual queries and is for the server-only
explorer.
"""

from typing import Literal

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from lean_explore_bench.querylog.schema import SOURCES

_CATEGORY_ORDERS = {"source": list(SOURCES)}


def _style(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title=title,
        template="plotly_white",
        margin={"l": 40, "r": 20, "t": 60, "b": 40},
        legend_title_text="",
    )
    return figure


def bar(
    table: pd.DataFrame,
    x: str,
    title: str,
    color: str | None = None,
    y: str = "n",
    horizontal: bool = False,
) -> go.Figure:
    """Bar chart of a count table.

    Args:
        table: Count table with columns ``x``, ``y`` and optionally ``color``.
        x: Category column.
        title: Figure title.
        color: Optional column to stack by.
        y: Count column.
        horizontal: Draw horizontal bars.

    Returns:
        A plotly figure.
    """
    table = table.astype({x: str} | ({color: str} if color else {}))
    if horizontal:
        figure = px.bar(
            table,
            y=x,
            x=y,
            color=color,
            orientation="h",
            category_orders=_CATEGORY_ORDERS,
        )
    else:
        figure = px.bar(table, x=x, y=y, color=color, category_orders=_CATEGORY_ORDERS)
    return _style(figure, title)


def daily_volume(table: pd.DataFrame, title: str = "Searches per day") -> go.Figure:
    """Stacked bars of searches per UTC day by source.

    Args:
        table: Count table with ``collected_on``, ``source`` and ``n``.
        title: Figure title.

    Returns:
        A plotly figure.
    """
    figure = px.bar(
        table.astype({"collected_on": str}),
        x="collected_on",
        y="n",
        color="source",
        category_orders=_CATEGORY_ORDERS,
    )
    figure.update_xaxes(type="category", title="UTC day")
    return _style(figure, title)


def share_heatmap(
    table: pd.DataFrame, rows: str, columns: str, title: str, value: str = "n"
) -> go.Figure:
    """Heatmap of row-normalised shares, e.g. category by source.

    Args:
        table: Count table with ``rows``, ``columns`` and ``value``.
        rows: Column for the heatmap rows.
        columns: Column for the heatmap columns.
        title: Figure title.
        value: Count column.

    Returns:
        A plotly figure whose cells are shares of each row's total.
    """
    pivot = table.pivot_table(
        index=rows, columns=columns, values=value, aggfunc="sum", observed=False
    ).fillna(0)
    shares = pivot.div(pivot.sum(axis=1).replace(0, 1), axis=0)
    figure = px.imshow(
        shares,
        text_auto=".0%",
        color_continuous_scale="Blues",
        aspect="auto",
        zmin=0,
        zmax=1,
    )
    return _style(figure, title)


def query_map(
    points: pd.DataFrame,
    color: str = "category",
    hover: tuple[str, ...] = ("query", "n_rows", "sources"),
    title: str = "Distinct queries (2-D projection)",
) -> go.Figure:
    """Scatter plot of distinct queries in a 2-D projection.

    Server-only: the hover text shows real queries. Positions come from UMAP
    or PCA, so distances and apparent cluster sizes are not meaningful.

    Args:
        points: Distinct queries with ``x`` and ``y`` columns.
        color: Column to colour points by.
        hover: Columns shown on hover.
        title: Figure title.

    Returns:
        A plotly figure.
    """
    if not pd.api.types.is_float_dtype(points[color]):
        points = points.assign(**{color: points[color].astype(str)})
    figure = px.scatter(
        points,
        x="x",
        y="y",
        color=color,
        hover_data=list(hover),
        category_orders=_CATEGORY_ORDERS,
        render_mode="webgl",
    )
    figure.update_traces(marker={"size": 5, "opacity": 0.75})
    if points[color].nunique() > 20:
        figure.update_layout(showlegend=False)
    figure.update_xaxes(showticklabels=False, title="")
    figure.update_yaxes(showticklabels=False, title="")
    return _style(figure, title)


def correlation_heatmap(
    frame: pd.DataFrame,
    columns: list[str],
    title: str,
    method: Literal["pearson", "kendall", "spearman"] = "spearman",
) -> go.Figure:
    """Heatmap of pairwise correlations between numeric columns.

    Args:
        frame: Rows to correlate, e.g. distinct queries.
        columns: Numeric or boolean columns.
        title: Figure title.
        method: ``"spearman"`` (rank; robust to skew) or ``"pearson"``.

    Returns:
        A plotly figure.
    """
    matrix = frame[columns].astype(float).corr(method=method)
    figure = px.imshow(
        matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    return _style(figure, title)


def feature_scatter(
    frame: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    hover: tuple[str, ...] = ("query",),
    jitter: float = 0.0,
    seed: int = 0,
) -> go.Figure:
    """Scatter plot of two features, one dot per row.

    Server-only when ``hover`` includes query text.

    Args:
        frame: Rows to plot.
        x: Column for the x axis.
        y: Column for the y axis.
        color: Column to colour by.
        title: Figure title.
        hover: Columns shown on hover.
        jitter: Uniform noise added to both axes, as a fraction of each
            axis's range, so that ties on integer features stay visible.
        seed: Seed for the jitter.

    Returns:
        A plotly figure.
    """
    frame = frame.assign(**{color: frame[color].astype(str)})
    if jitter:
        rng = np.random.default_rng(seed)
        for column in (x, y):
            values = frame[column].astype(float)
            spread = (values.max() - values.min()) or 1.0
            frame[column] = values + rng.uniform(-jitter, jitter, len(frame)) * spread
    figure = px.scatter(
        frame,
        x=x,
        y=y,
        color=color,
        hover_data=list(hover),
        category_orders=_CATEGORY_ORDERS,
        render_mode="webgl",
    )
    figure.update_traces(marker={"size": 5, "opacity": 0.6})
    return _style(figure, title)
