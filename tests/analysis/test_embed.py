import sys
import types

import numpy as np
import pytest

pytest.importorskip("sklearn")

from lean_explore_bench.analysis import embed  # noqa: E402


class _FakeModel:
    """Stands in for sentence_transformers.SentenceTransformer."""

    calls: list[dict[str, object]] = []

    def __init__(self, name: str, device: str | None = None) -> None:
        self.name, self.device = name, device

    def encode(self, texts: list[str], **kwargs: object) -> np.ndarray:
        _FakeModel.calls.append({"texts": texts, **kwargs})
        return np.ones((len(texts), 4), dtype=np.float64)


def test_embed_queries_uses_instruction_and_normalises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = types.ModuleType("sentence_transformers")
    setattr(module, "SentenceTransformer", _FakeModel)  # noqa: B010
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    result = embed.embed_queries(["a", "b"], device="cpu")
    assert result.shape == (2, 4) and result.dtype == np.float32
    call = _FakeModel.calls[-1]
    assert call["prompt"] == embed.DEFAULT_INSTRUCTION
    assert call["normalize_embeddings"] is True


def _points() -> np.ndarray:
    rng = np.random.default_rng(0)
    return np.vstack([rng.normal(0, 0.05, (40, 8)), rng.normal(3, 0.05, (40, 8))])


def test_project_2d_pca() -> None:
    assert embed.project_2d(_points(), method="pca").shape == (80, 2)


def test_project_2d_rejects_unknown_method() -> None:
    with pytest.raises(ValueError):
        embed.project_2d(_points(), method="tsne")


def test_umap_projection_and_reduction() -> None:
    pytest.importorskip("umap")
    assert embed.project_2d(_points(), method="umap").shape == (80, 2)
    assert embed.reduce_for_clustering(_points(), n_components=3).shape == (80, 3)


def test_hdbscan_never_mixes_separated_groups() -> None:
    labels = embed.cluster_hdbscan(_points(), min_cluster_size=10)
    first, second = set(labels[:40]) - {-1}, set(labels[40:]) - {-1}
    assert first and second and not first & second
