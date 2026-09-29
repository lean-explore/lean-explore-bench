"""Assemble query log views into HTML pages.

Two kinds of page:

- :func:`release_sections` builds only from counts and topic-free category
  summaries that passed the release gate. Its output may be saved and
  shared.
- :func:`explore_sections` adds views of individual queries (samples per
  category, 2-D query maps, topic clusters). It must stay on the server: the
  ``explore`` command serves it from memory and never writes it to disk.
"""

import html
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

import pandas as pd
import plotly.graph_objects as go

from lean_explore_bench.analysis import plots
from lean_explore_bench.analysis.categories import CategoryFit, describe_categories
from lean_explore_bench.analysis.release import (
    MIN_CELL_COUNT,
    ROUNDING_BASE,
    releasable_counts,
)
from lean_explore_bench.analysis.stats import (
    CORRELATION_COLUMNS,
    PreparedLog,
    counts,
    overview,
)

Content: TypeAlias = go.Figure | pd.DataFrame | str
Counter: TypeAlias = Callable[[pd.DataFrame, list[str]], pd.DataFrame]

SAMPLE_COLUMNS = ["query", "category", "skeleton", "n_rows", "n_days", "sources"]


@dataclass(frozen=True)
class Section:
    """One block on a page.

    Attributes:
        title: Heading.
        content: A figure, a table, or a paragraph of plain text.
        table: Gated data behind the content, saved as CSV by ``report``.
        table_name: File stem for ``table``.
    """

    title: str
    content: Content
    table: pd.DataFrame | None = None
    table_name: str | None = None


def _overview_table(prepared: PreparedLog, rounding_base: int = 1) -> pd.DataFrame:
    numbers = overview(prepared, rounding_base)
    return pd.DataFrame(
        {
            "measure": list(numbers),
            "value": [
                f"{value:.2%}" if isinstance(value, float) else f"{value:,}"
                for value in numbers.values()
            ],
        }
    )


def _volume_sections(prepared: PreparedLog, count: Counter) -> list[Section]:
    daily = count(prepared.rows, ["collected_on", "source"])
    lengths = count(prepared.distinct, ["length_bin"])
    repeats = count(prepared.distinct, ["repeat_bin"])
    return [
        Section("Searches per day", plots.daily_volume(daily), daily, "daily"),
        Section(
            "Query length (distinct queries, words)",
            plots.bar(lengths, "length_bin", "Words per distinct query"),
            lengths,
            "length",
        ),
        Section(
            "How often distinct queries repeat",
            plots.bar(repeats, "repeat_bin", "Searches per distinct query"),
            repeats,
            "repeats",
        ),
    ]


def _category_sections(
    prepared: PreparedLog, count: Counter, min_count: int, rounding_base: int
) -> list[Section]:
    shares = count(prepared.rows, ["category"])
    by_source = count(prepared.rows, ["source", "category"])
    by_source = by_source[by_source["category"] != "<suppressed>"]
    summary = describe_categories(
        prepared.distinct, prepared.rows, min_count, rounding_base=rounding_base
    )
    return [
        Section(
            "Categories (statistical, topic-free)",
            plots.bar(shares, "category", "Searches per category"),
            shares,
            "categories",
        ),
        Section("What each category looks like", summary, summary, "category_summary"),
        Section(
            "Category mix by source",
            plots.share_heatmap(by_source, "source", "category", "Share by category"),
            by_source,
            "category_by_source",
        ),
    ]


def _selection_table(fit: CategoryFit) -> pd.DataFrame:
    levels = [("top", fit.top), *((str(p + 1), c) for p, c in fit.children.items())]
    return pd.concat(
        [level.selection.assign(level=name) for name, level in levels],
        ignore_index=True,
    )[["level", "categories", "bic", "ari", "min_jaccard"]]


def _fit_sections(prepared: PreparedLog) -> list[Section]:
    fit = prepared.categories
    if fit is None:
        return []
    selection = _selection_table(fit)
    return [
        Section(
            "How many categories: stability per candidate size "
            "(kept: the largest size whose categories all have Jaccard ≥ 0.75)",
            selection,
            selection,
            "category_selection",
        ),
        Section(
            "Top-level category stability (Jaccard over subsamples)",
            fit.top.jaccard,
            fit.top.jaccard,
            "category_stability",
        ),
    ]


def release_sections(
    prepared: PreparedLog, min_count: int = MIN_CELL_COUNT, seed: int = 0
) -> list[Section]:
    """Sections built only from gated, topic-free data; safe to share.

    Args:
        prepared: A prepared log.
        min_count: Smallest publishable count.
        seed: Seed for the stability check.

    Returns:
        Page sections.
    """

    def count(frame: pd.DataFrame, by: list[str]) -> pd.DataFrame:
        return releasable_counts(frame, by, min_count=min_count)

    notice = Section(
        "About this report",
        f"Aggregate counts only. Any group with fewer than {min_count} rows "
        f"is merged into '<suppressed>', every count is rounded to a multiple "
        f"of {ROUNDING_BASE}, and every share is computed from rounded counts. "
        "No query text is included.",
    )
    overview_table = _overview_table(prepared, ROUNDING_BASE)
    return [
        notice,
        Section("Overview", overview_table, overview_table, "overview"),
        *_volume_sections(prepared, count),
        *_category_sections(prepared, count, min_count, ROUNDING_BASE),
        *_fit_sections(prepared),
    ]


def _feature_sections(prepared: PreparedLog, seed: int) -> list[Section]:
    distinct = prepared.distinct.assign(
        category=prepared.distinct["category"].astype(str)
    )
    return [
        Section(
            "Feature correlations (Spearman, distinct queries)",
            plots.correlation_heatmap(
                distinct, list(CORRELATION_COLUMNS), "Spearman correlation"
            ),
        ),
        Section(
            "Length vs identifier share, by category",
            plots.feature_scatter(
                distinct,
                "n_words",
                "identifier_share",
                "category",
                "Words vs share of Lean identifiers (jittered)",
                jitter=0.01,
                seed=seed,
            ),
        ),
        Section(
            "Prose vs identifiers, by category",
            plots.feature_scatter(
                distinct,
                "function_word_share",
                "identifier_share",
                "category",
                "Function-word share vs identifier share (jittered)",
                jitter=0.01,
                seed=seed,
            ),
        ),
    ]


def _map_sections(points: pd.DataFrame | None, seed: int) -> list[Section]:
    if points is None:
        return []
    points = points.assign(category=points["category"].astype(str))
    sections = [
        Section("Query map by category", plots.query_map(points, "category")),
        Section("Query map by source", plots.query_map(points, "main_source")),
        Section(
            "Query map by identifier share", plots.query_map(points, "identifier_share")
        ),
    ]
    if "cluster" in points:
        from lean_explore_bench.analysis.clusters import cluster_summary

        sections += [
            Section("Query map by topic cluster", plots.query_map(points, "cluster")),
            Section(
                "Topic clusters (server only; not used for categories)",
                cluster_summary(points, seed=seed),
            ),
        ]
    return sections


def _sample_sections(
    prepared: PreparedLog, top_n: int, per_category: int, seed: int
) -> list[Section]:
    distinct = prepared.distinct
    sections = [
        Section(
            f"Most repeated distinct queries (top {top_n})",
            distinct.nlargest(top_n, "n_rows")[SAMPLE_COLUMNS],
        )
    ]
    for category, members in distinct.groupby("category"):
        sample = members.sample(min(per_category, len(members)), random_state=seed)
        sections.append(
            Section(
                f"Sample: category {category} ({len(members):,} distinct)",
                sample[SAMPLE_COLUMNS],
            )
        )
    return sections


def explore_sections(
    prepared: PreparedLog,
    points: pd.DataFrame | None = None,
    top_n: int = 50,
    per_category: int = 15,
    seed: int = 0,
) -> list[Section]:
    """Full, server-only sections, including individual queries.

    Args:
        prepared: A prepared log.
        points: Distinct queries with ``x``/``y`` (and optionally topic
            ``cluster``) columns for the query maps.
        top_n: Rows in the most-repeated-queries table.
        per_category: Random distinct queries shown per category.
        seed: Seed for samples, jitter and the stability check.

    Returns:
        Page sections.
    """
    notice = Section(
        "Server only",
        "This page shows real queries. It is served from memory; do not save, "
        "screenshot or share it.",
    )
    return [
        notice,
        Section("Overview", _overview_table(prepared)),
        *_volume_sections(prepared, counts),
        *_category_sections(prepared, counts, min_count=1, rounding_base=1),
        *_fit_sections(prepared),
        *_feature_sections(prepared, seed),
        *_map_sections(points, seed),
        *_sample_sections(prepared, top_n, per_category, seed),
    ]


def _render(section: Section, include_plotlyjs: bool) -> str:
    content = section.content
    if isinstance(content, go.Figure):
        return str(
            content.to_html(
                full_html=False, include_plotlyjs="cdn" if include_plotlyjs else False
            )
        )
    if isinstance(content, pd.DataFrame):
        return str(content.to_html(index=False, escape=True, border=0))
    return f"<p>{html.escape(content)}</p>"


_STYLE = """
body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1100px;
  padding: 0 1rem; color: #1f2328; }
table { border-collapse: collapse; font-size: 0.9rem; margin-bottom: 1rem; }
th, td { padding: 0.3rem 0.6rem; border-bottom: 1px solid #d0d7de;
  text-align: left; vertical-align: top; }
h2 { margin-top: 2.5rem; }
"""


def render_page(sections: list[Section], title: str) -> str:
    """Render sections as one self-contained HTML page.

    Args:
        sections: Page sections.
        title: Page title.

    Returns:
        HTML text. Plotly's script is loaded once from its CDN.
    """
    parts, script_loaded = [], False
    for section in sections:
        is_figure = isinstance(section.content, go.Figure)
        parts.append(f"<h2>{html.escape(section.title)}</h2>")
        parts.append(_render(section, include_plotlyjs=is_figure and not script_loaded))
        script_loaded = script_loaded or is_figure
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head>\n"
        f"<body><h1>{html.escape(title)}</h1>\n"
        + "\n".join(parts)
        + "\n</body></html>\n"
    )
