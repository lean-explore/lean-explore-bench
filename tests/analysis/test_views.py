import datetime
import re

import pandas as pd
import plotly.graph_objects as go
from conftest import MakeLog

from lean_explore_bench.analysis.stats import PreparedLog, prepare
from lean_explore_bench.analysis.views import (
    Section,
    explore_sections,
    release_sections,
    render_page,
)


def test_release_page_contains_no_query_text_and_gates_counts(
    prepared: PreparedLog,
) -> None:
    sections = release_sections(prepared)
    page = render_page(sections, "report")
    assert not any(query in page for query in prepared.distinct["query"])
    for section in sections:
        if section.table is not None and "n" in section.table:
            assert (section.table["n"].dropna() >= 10).all()


def test_release_tables_are_named_for_export(prepared: PreparedLog) -> None:
    for section in release_sections(prepared):
        assert (section.table is None) == (section.table_name is None)


def test_explore_page_with_and_without_maps(prepared: PreparedLog) -> None:
    points = prepared.distinct.assign(
        x=0.0, y=0.0, cluster=[i % 3 - 1 for i in range(len(prepared.distinct))]
    )
    with_maps = render_page(explore_sections(prepared, points), "explore")
    assert "Query map by category" in with_maps
    assert "Topic clusters (server only" in with_maps
    without = render_page(explore_sections(prepared), "explore")
    assert "Query map" not in without
    assert "Sample: category" in without


def test_small_logs_have_no_fit_sections(make_log: MakeLog, day: datetime.date) -> None:
    small = prepare(make_log([(f"q {i}", "web", day, 1) for i in range(5)]))
    titles = [section.title for section in release_sections(small)]
    assert not any("stability" in title.lower() for title in titles)


def test_render_page_escapes_and_loads_plotly_once() -> None:
    figure = go.Figure(go.Bar(x=[1], y=[1]))
    sections = [
        Section("<b>title</b>", "text & more"),
        Section("table", pd.DataFrame({"a": ["<i>x</i>"]})),
        Section("one", figure),
        Section("two", figure),
    ]
    page = render_page(sections, "T & T")
    assert "&lt;b&gt;title&lt;/b&gt;" in page and "text &amp; more" in page
    assert "&lt;i&gt;x&lt;/i&gt;" in page
    assert page.count("cdn.plot.ly") == 1
    assert "<title>T &amp; T</title>" in page


def test_suppressed_cells_cannot_be_recovered_by_differencing(
    make_log: MakeLog, day: datetime.date
) -> None:
    # 20 API searches and 3 web searches: the web cell is suppressed, and the
    # published total must not give it away (23 - 20 = 3 would).
    log = make_log(
        [(f"q{i} alpha beta", "api", day, 1) for i in range(20)]
        + [(f"Name{i}.x", "web", day, 1) for i in range(3)]
    )
    tables = {
        s.table_name: s.table
        for s in release_sections(prepare(log))
        if s.table_name and s.table is not None
    }
    total = tables["overview"].set_index("measure")["value"]["rows"]
    visible = tables["daily"]["n"].dropna().sum()
    assert int(str(total).replace(",", "")) - int(visible) == 0


def test_release_counts_and_category_shares_are_rounded(prepared: PreparedLog) -> None:
    for section in release_sections(prepared):
        if section.table is not None and "n" in section.table:
            assert (section.table["n"].dropna() % 10 == 0).all()
    summary = next(
        s.table
        for s in release_sections(prepared)
        if s.table_name == "category_summary"
    )
    assert summary is not None
    for skeletons in summary["common_skeletons"]:
        for count in re.findall(r"\((\d+)\)", str(skeletons)):
            assert int(count) % 10 == 0
