"""Describe clusters of queries without an LLM.

Server-only: keyword lists and examples come straight from real queries.
"""

import re

import numpy as np
import pandas as pd

_TOKEN = re.compile(r"[^\W\d][\w'.]*[\w']|[^\W\d]", re.UNICODE)


def cluster_keywords(
    texts: pd.Series, labels: np.ndarray, top_k: int = 8
) -> dict[int, list[str]]:
    """Top terms per cluster by class-based TF-IDF (as in BERTopic).

    Each cluster's queries are joined into one document; a term scores high
    when it is frequent in that cluster and rare across clusters. Lean names
    such as ``MeasureTheory.Measure`` and ``mul_comm`` stay whole.

    Args:
        texts: Query texts.
        labels: Cluster label per text; ``-1`` (noise) is skipped.
        top_k: Terms per cluster.

    Returns:
        Mapping from cluster label to its top terms.
    """
    from sklearn.feature_extraction.text import CountVectorizer

    frame = pd.DataFrame({"text": texts.to_numpy(), "label": labels})
    frame = frame[frame["label"] >= 0]
    if frame.empty:
        return {}
    documents = frame.groupby("label")["text"].apply(" ".join)
    vectorizer = CountVectorizer(
        tokenizer=_TOKEN.findall,
        lowercase=False,
        token_pattern=None,
        stop_words=None,
        min_df=1,
    )
    term_counts = vectorizer.fit_transform(documents.to_numpy()).toarray()
    term_frequency = term_counts / np.maximum(term_counts.sum(axis=1, keepdims=True), 1)
    average_words = term_counts.sum() / len(documents)
    idf = np.log(1 + average_words / np.maximum(term_counts.sum(axis=0), 1))
    scores = term_frequency * idf
    terms = vectorizer.get_feature_names_out()
    return {
        int(label): [terms[index] for index in np.argsort(-row)[:top_k]]
        for label, row in zip(documents.index, scores)
    }


def _cluster_row(
    label: int,
    members: pd.DataFrame,
    keywords: dict[int, list[str]],
    examples: int,
    seed: int,
) -> dict[str, object]:
    sources = members["sources"].explode().value_counts(normalize=True)
    sample = members["query"].sample(min(examples, len(members)), random_state=seed)
    return {
        "cluster": label,
        "queries": len(members),
        "sources": ", ".join(f"{s} {v:.0%}" for s, v in sources.items()),
        "main_category": str(members["category"].astype(str).mode().iloc[0]),
        "median_words": float(members["n_words"].median()),
        "identifier_share": round(float(members["identifier_share"].mean()), 2),
        "keywords": ", ".join(keywords.get(label, [])),
        "examples": " | ".join(sample.tolist()),
    }


def cluster_summary(
    points: pd.DataFrame, top_k: int = 8, examples: int = 3, seed: int = 0
) -> pd.DataFrame:
    """One row per topic cluster: size, sources, category, keywords, examples.

    Args:
        points: Distinct queries with ``cluster``, ``query``, ``category`` and
            ``sources`` columns.
        top_k: Keywords per cluster.
        examples: Example queries per cluster.
        seed: Seed for picking examples.

    Returns:
        A DataFrame sorted by cluster size, noise last.
    """
    keywords = cluster_keywords(points["query"], points["cluster"].to_numpy(), top_k)
    rows = [
        _cluster_row(
            int(label), points[points["cluster"] == label], keywords, examples, seed
        )
        for label in np.unique(points["cluster"].to_numpy())
    ]
    summary = pd.DataFrame(rows)
    summary["is_noise"] = summary["cluster"] < 0
    return (
        summary.sort_values(["is_noise", "queries"], ascending=[True, False])
        .drop(columns="is_noise")
        .reset_index(drop=True)
    )
