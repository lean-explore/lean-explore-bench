"""Collapse duplicate and near-duplicate queries.

Automated clients (agents, scripts) send bursts of identical or nearly
identical queries. Left in, they dominate every statistic. We therefore:

1. group exact duplicates after normalisation;
2. within each (source, UTC day), merge near-duplicates whose character
   4-gram Jaccard similarity is at least a threshold. MinHash LSH proposes
   candidate pairs and the exact Jaccard decides;
3. summarise each resulting group as one *distinct query*.

Near-duplicates are only merged within a source and day, so the same need
asked by different clients on different days stays visible as repetition.
"""

import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH

from lean_explore_bench.querylog.normalize import normalize_query

DEFAULT_THRESHOLD = 0.8
"""Jaccard threshold; Lee et al. 2021 use 0.8 for near-duplicate text."""

SHINGLE_SIZE = 4


def _shingles(text: str, size: int = SHINGLE_SIZE) -> set[str]:
    if len(text) <= size:
        return {text}
    return {text[i : i + size] for i in range(len(text) - size + 1)}


def _jaccard(first: str, second: str) -> float:
    """Exact shingle Jaccard; MinHash only proposes candidate pairs."""
    first_shingles, second_shingles = _shingles(first), _shingles(second)
    union = len(first_shingles | second_shingles)
    return len(first_shingles & second_shingles) / union if union else 1.0


def _minhash(text: str, num_perm: int) -> MinHash:
    signature = MinHash(num_perm=num_perm, seed=1)
    for shingle in _shingles(text):
        signature.update(shingle.encode("utf-8"))
    return signature


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, first: int, second: int) -> None:
        root_first, root_second = self.find(first), self.find(second)
        if root_first != root_second:
            self.parent[max(root_first, root_second)] = min(root_first, root_second)


def assign_duplicate_groups(
    frame: pd.DataFrame,
    threshold: float = DEFAULT_THRESHOLD,
    num_perm: int = 128,
) -> pd.DataFrame:
    """Label each log row with its exact and near-duplicate group.

    Args:
        frame: A query log with ``query``, ``source`` and ``collected_on``.
        threshold: Jaccard similarity above which two queries from the same
            source and day are merged. Use ``1.0`` to merge exact duplicates
            only.
        num_perm: MinHash permutations.

    Returns:
        A copy of ``frame`` with ``normalized`` (normalised text) and
        ``group_id`` (an integer shared by duplicates) columns.
    """
    result = frame.copy()
    result["normalized"] = [normalize_query(text) for text in result["query"]]

    texts = result["normalized"].unique().tolist()
    text_index = {text: index for index, text in enumerate(texts)}
    groups = _UnionFind(len(texts))

    if threshold < 1.0:
        signatures: dict[str, MinHash] = {}
        for _, bucket in result.groupby(["source", "collected_on"], sort=False):
            bucket_texts = bucket["normalized"].unique().tolist()
            if len(bucket_texts) < 2:
                continue
            lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
            for text in bucket_texts:
                if text not in signatures:
                    signatures[text] = _minhash(text, num_perm)
                for match in lsh.query(signatures[text]):
                    if _jaccard(text, match) >= threshold:
                        groups.union(text_index[text], text_index[match])
                lsh.insert(text, signatures[text])

    roots = np.array([groups.find(text_index[text]) for text in result["normalized"]])
    _, result["group_id"] = np.unique(roots, return_inverse=True)
    return result


def summarize_distinct_queries(grouped: pd.DataFrame) -> pd.DataFrame:
    """Summarise each duplicate group as one distinct query.

    Args:
        grouped: Output of :func:`assign_duplicate_groups`.

    Returns:
        One row per ``group_id`` with:

        - ``query``: the most frequent normalised text in the group;
        - ``n_rows``: log rows in the group;
        - ``n_variants``: distinct normalised texts merged into it;
        - ``n_days``: distinct UTC days it appeared on;
        - ``sources``: sorted tuple of sources;
        - ``first_seen`` / ``last_seen``: first and last day;
        - ``median_result_count`` and ``zero_result_share``;
        - ``uses_package_filter``: share of rows with a package filter.
    """

    def representative(texts: pd.Series) -> str:
        return str(texts.value_counts().index[0])

    summary = grouped.groupby("group_id").agg(
        query=("normalized", representative),
        n_rows=("normalized", "size"),
        n_variants=("normalized", "nunique"),
        n_days=("collected_on", "nunique"),
        sources=("source", lambda values: tuple(sorted(set(values)))),
        first_seen=("collected_on", "min"),
        last_seen=("collected_on", "max"),
        median_result_count=("result_count", "median"),
        zero_result_share=("result_count", lambda values: float((values == 0).mean())),
        uses_package_filter=(
            "packages",
            lambda values: float(np.mean([len(v) > 0 for v in values])),
        ),
    )
    return summary.reset_index()


def distinct_queries(
    frame: pd.DataFrame, threshold: float = DEFAULT_THRESHOLD
) -> pd.DataFrame:
    """Collapse a query log to distinct queries in one step.

    Args:
        frame: A query log.
        threshold: See :func:`assign_duplicate_groups`.

    Returns:
        See :func:`summarize_distinct_queries`.
    """
    return summarize_distinct_queries(assign_duplicate_groups(frame, threshold))
