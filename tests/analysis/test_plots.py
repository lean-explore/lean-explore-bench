import numpy as np
import pandas as pd
import pytest

from lean_explore_bench.analysis import plots


@pytest.fixture
def table() -> pd.DataFrame:
    return pd.DataFrame({"category": ["1", "2"], "source": ["api", "mcp"], "n": [5, 3]})


def test_bar_vertical_and_horizontal(table: pd.DataFrame) -> None:
    assert plots.bar(table, "category", "t").data[0].orientation in (None, "v")
    assert plots.bar(table, "category", "t", horizontal=True).data[0].orientation == "h"
    assert plots.bar(table, "category", "t").layout.title.text == "t"


def test_daily_volume_stacks_sources() -> None:
    table = pd.DataFrame(
        {"collected_on": ["2026-09-01"] * 2, "source": ["api", "mcp"], "n": [4, 1]}
    )
    figure = plots.daily_volume(table)
    assert {trace.name for trace in figure.data} == {"api", "mcp"}


def test_share_heatmap_rows_sum_to_one(table: pd.DataFrame) -> None:
    figure = plots.share_heatmap(table, "source", "category", "t")
    z = np.array(figure.data[0].z, dtype=float)
    assert np.allclose(z.sum(axis=1), 1)


def test_correlation_heatmap_is_symmetric() -> None:
    frame = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 4, 5, 9], "c": [4, 3, 2, 1]})
    z = np.array(plots.correlation_heatmap(frame, ["a", "b", "c"], "t").data[0].z)
    assert np.allclose(z, z.T)
    assert z[0, 2] == pytest.approx(-1)


def test_feature_scatter_jitter_stays_close() -> None:
    frame = pd.DataFrame({"x": [0, 10] * 50, "y": [0.0, 1.0] * 50, "c": ["a"] * 100})
    figure = plots.feature_scatter(frame, "x", "y", "c", "t", hover=("x",), jitter=0.01)
    xs = np.concatenate([np.asarray(trace.x, dtype=float) for trace in figure.data])
    assert xs.min() >= -0.1 and xs.max() <= 10.1
    assert len(set(xs.round(6))) > 2


def test_query_map_legend_and_continuous_colour() -> None:
    points = pd.DataFrame(
        {
            "x": range(30),
            "y": range(30),
            "label": range(30),
            "share": np.linspace(0, 1, 30),
        }
    )
    many = plots.query_map(points, "label", hover=("label",))
    assert many.layout.showlegend is False
    continuous = plots.query_map(points, "share", hover=("label",))
    assert len(continuous.data) == 1
