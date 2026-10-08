"""Embed queries locally and project them to 2-D for plotting.

Real queries must not be sent to external APIs, so embeddings come from a
local model (by default the Qwen3-Embedding model LeanExplore already uses).
Embeddings can be inverted back to text, so treat them like raw queries:
keep them in memory and never save or publish them.

Requires the ``embed`` extra.
"""

import numpy as np

DEFAULT_MODEL = "Qwen/Qwen3-Embedding-0.6B"

DEFAULT_INSTRUCTION = (
    "Instruct: Identify what kind of Lean or Mathlib search request this is\nQuery: "
)
"""Asks the model to embed the *kind* of request rather than generic topic."""


def embed_queries(
    texts: list[str],
    model_name: str = DEFAULT_MODEL,
    instruction: str = DEFAULT_INSTRUCTION,
    device: str | None = None,
    batch_size: int = 64,
) -> np.ndarray:
    """Embed queries with a local sentence-transformers model.

    Args:
        texts: Query texts.
        model_name: Hugging Face model id or local path.
        instruction: Prompt prepended to every query.
        device: ``"cuda"``, ``"cpu"`` etc.; auto-detected when ``None``.
        batch_size: Encoding batch size.

    Returns:
        An array of shape ``(len(texts), dim)`` with L2-normalised rows.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, device=device)
    embeddings = model.encode(
        texts,
        prompt=instruction,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype=np.float32)


def project_2d(
    embeddings: np.ndarray,
    method: str = "umap",
    n_neighbors: int = 15,
    seed: int = 0,
) -> np.ndarray:
    """Project embeddings to two dimensions for viewing.

    2-D maps are for exploring only: distances between clusters and cluster
    sizes in the picture are not meaningful (Wattenberg et al. 2016). Look at
    more than one ``n_neighbors`` and seed before reading anything into one.

    Args:
        embeddings: Array from :func:`embed_queries`.
        method: ``"umap"`` (cosine metric) or ``"pca"``.
        n_neighbors: UMAP neighbourhood size.
        seed: Random seed.

    Returns:
        An array of shape ``(n, 2)``.
    """
    if method == "pca":
        from sklearn.decomposition import PCA

        projected = PCA(n_components=2, random_state=seed).fit_transform(embeddings)
        return np.asarray(projected, dtype=float)
    if method == "umap":
        from umap import UMAP

        reducer = UMAP(
            n_components=2,
            n_neighbors=min(n_neighbors, len(embeddings) - 1),
            metric="cosine",
            min_dist=0.1,
            random_state=seed,
        )
        return np.asarray(reducer.fit_transform(embeddings), dtype=float)
    raise ValueError(f"Unknown projection method {method!r}")


def reduce_for_clustering(
    embeddings: np.ndarray,
    n_components: int = 10,
    n_neighbors: int = 15,
    seed: int = 0,
) -> np.ndarray:
    """Reduce embeddings with UMAP before density-based clustering.

    HDBSCAN on raw high-dimensional embeddings labels much of the data as
    noise. BERTopic and the UMAP docs reduce to a few dimensions first, with
    ``min_dist=0`` so that points pack densely (see
    ``docs/literature/test-collection-construction/query-clustering-embeddings.md``).

    Args:
        embeddings: Array from :func:`embed_queries`.
        n_components: Output dimensions.
        n_neighbors: UMAP neighbourhood size.
        seed: Random seed.

    Returns:
        An array of shape ``(n, n_components)``.
    """
    from umap import UMAP

    reduced = UMAP(
        n_components=n_components,
        n_neighbors=min(n_neighbors, len(embeddings) - 1),
        metric="cosine",
        min_dist=0.0,
        random_state=seed,
    ).fit_transform(embeddings)
    return np.asarray(reduced, dtype=float)


def cluster_hdbscan(
    embeddings: np.ndarray, min_cluster_size: int = 5, min_samples: int = 2
) -> np.ndarray:
    """Cluster points with HDBSCAN.

    Pass the output of :func:`reduce_for_clustering`, not raw embeddings.

    Args:
        embeddings: Reduced embeddings.
        min_cluster_size: Smallest cluster; 5 matches the category floor in
            the literature notes.
        min_samples: HDBSCAN ``min_samples``.

    Returns:
        Cluster labels; ``-1`` marks noise.
    """
    from sklearn.cluster import HDBSCAN

    labels = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="leaf",
        copy=True,
    ).fit_predict(embeddings)
    return np.asarray(labels, dtype=int)
