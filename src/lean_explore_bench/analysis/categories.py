"""Find query categories statistically from topic-free features.

Each distinct query becomes a vector of its surface measurements (lengths,
identifier, prose and symbol shares) plus a low-rank TF-IDF summary of its
skeleton (see :mod:`lean_explore_bench.querylog.features`). Nothing in the
vector encodes subject matter, so categories describe *how* people search,
not *what about*.

Gaussian mixtures are fitted for a range of sizes, and the largest size whose
categories all reproduce on subsamples (Hennig's Jaccard at least 0.75) is
kept. The same rule is then applied inside each large category, giving a
two-level hierarchy. See ``docs/literature/test-collection-construction/
query-clustering-validation-and-visualization.md``.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from lean_explore_bench.analysis.release import round_count

NUMERIC_FEATURES: tuple[str, ...] = (
    "n_words",
    "n_chars",
    "identifier_share",
    "function_word_share",
    "symbol_share",
    "latex_commands",
)
_LOG_SCALED = frozenset({"n_words", "n_chars", "latex_commands"})


@dataclass(frozen=True)
class LevelFit:
    """Categories chosen at one level of the hierarchy.

    Attributes:
        labels: Category per row of ``matrix``, numbered from 0 by size.
        matrix: The rows this level was fitted on.
        selection: For each candidate size: BIC, mean ARI over subsamples and
            the smallest per-category Jaccard.
        jaccard: Per-category mean Jaccard for the chosen size.
    """

    labels: np.ndarray
    matrix: np.ndarray
    selection: pd.DataFrame
    jaccard: pd.DataFrame


@dataclass(frozen=True)
class CategoryFit:
    """A two-level category hierarchy.

    Attributes:
        labels: Category path per distinct query, e.g. ``"2"`` or ``"2.1"``.
        top: The top-level fit.
        children: Second-level fits, keyed by top-level category number.
    """

    labels: np.ndarray
    top: LevelFit
    children: dict[int, LevelFit]


def style_matrix(
    distinct: pd.DataFrame, n_components: int = 8, seed: int = 0
) -> np.ndarray:
    """Build the topic-free feature matrix for clustering.

    Args:
        distinct: Distinct queries with feature and ``skeleton`` columns.
        n_components: Dimensions kept from the skeleton TF-IDF.
        seed: Random seed for the SVD.

    Returns:
        A standardised matrix with one row per distinct query.
    """
    numeric = np.column_stack(
        [
            np.log1p(distinct[name]) if name in _LOG_SCALED else distinct[name]
            for name in NUMERIC_FEATURES
        ]
    ).astype(float)
    parts = [numeric, _skeleton_components(distinct["skeleton"], n_components, seed)]
    scaled = StandardScaler().fit_transform(np.hstack(parts))
    return np.asarray(scaled, dtype=float)


def _skeleton_components(
    skeletons: pd.Series, n_components: int, seed: int
) -> np.ndarray:
    """Low-rank TF-IDF summary of skeletons; no columns when too few features.

    ``TruncatedSVD`` needs at least two features, so a log whose skeletons
    are all alike (for example only single names, ``ID``) or empty
    contributes no skeleton columns and is clustered on its numeric
    features alone.
    """
    vectorizer = TfidfVectorizer(
        token_pattern=r"\S+",
        ngram_range=(1, 3),
        lowercase=False,
        min_df=min(5, len(skeletons)),
        sublinear_tf=True,
    )
    try:
        tfidf = vectorizer.fit_transform(skeletons)
    except ValueError:  # empty vocabulary
        return np.empty((len(skeletons), 0))
    if tfidf.shape[1] < 2:
        return np.empty((len(skeletons), 0))
    n_components = min(n_components, tfidf.shape[1] - 1)
    return np.asarray(
        TruncatedSVD(n_components, random_state=seed).fit_transform(tfidf), dtype=float
    )


def _by_size(labels: np.ndarray) -> np.ndarray:
    order = pd.Series(labels).value_counts().index
    mapping = {old: new for new, old in enumerate(order)}
    return np.array([mapping[label] for label in labels])


def _mixture(k: int, seed: int) -> GaussianMixture:
    return GaussianMixture(
        n_components=k, covariance_type="full", n_init=3, random_state=seed
    )


def _best_jaccard(members: np.ndarray, other: np.ndarray) -> float:
    best = 0.0
    for label in np.unique(other):
        candidate = other == label
        union = np.sum(members | candidate)
        best = max(best, float(np.sum(members & candidate) / union) if union else 0.0)
    return best


def stability(
    matrix: np.ndarray,
    labels: np.ndarray,
    n_boot: int = 8,
    fraction: float = 0.8,
    seed: int = 0,
) -> tuple[float, pd.DataFrame]:
    """Refit on subsamples and compare with a reference labelling.

    Args:
        matrix: Rows that were clustered.
        labels: Reference labels, numbered from 0.
        n_boot: Number of subsamples.
        fraction: Share of rows in each subsample.
        seed: Random seed.

    Returns:
        The mean adjusted Rand index over subsamples, and each category's
        mean best-match Jaccard (Hennig 2007: 0.75 or more is stable).
    """
    rng = np.random.default_rng(seed)
    k = int(labels.max()) + 1
    aris, jaccards = [], []
    for round_ in range(n_boot):
        sample = rng.choice(len(matrix), int(fraction * len(matrix)), replace=False)
        predicted = _mixture(k, seed + round_ + 1).fit(matrix[sample]).predict(matrix)
        aris.append(adjusted_rand_score(labels, predicted))
        jaccards.append([_best_jaccard(labels == c, predicted) for c in range(k)])
    table = pd.DataFrame(
        {"category": range(k), "jaccard": np.mean(jaccards, axis=0).round(3)}
    )
    return float(np.mean(aris)), table


def _single(matrix: np.ndarray, selection: pd.DataFrame) -> LevelFit:
    labels = np.zeros(len(matrix), dtype=int)
    jaccard = pd.DataFrame({"category": [0], "jaccard": [1.0]})
    return LevelFit(labels=labels, matrix=matrix, selection=selection, jaccard=jaccard)


def select_level(
    matrix: np.ndarray,
    sizes: range = range(2, 9),
    threshold: float = 0.75,
    n_boot: int = 8,
    seed: int = 0,
) -> LevelFit:
    """Keep the largest number of categories that are all stable.

    Every candidate size is fitted and checked on subsamples. BIC is
    recorded but not used: on these features it keeps improving as
    categories get finer, while stability does not (Ben-Hur et al. 2002;
    Lange et al. 2004). With no stable split, everything is one category.

    Args:
        matrix: Rows to cluster.
        sizes: Candidate numbers of categories.
        threshold: Smallest per-category Jaccard counted as stable.
        n_boot: Subsamples per candidate.
        seed: Random seed.

    Returns:
        A :class:`LevelFit`.
    """
    rows, chosen = [], None
    for k in (k for k in sizes if k < len(matrix)):
        model = _mixture(k, seed).fit(matrix)
        labels = _by_size(model.predict(matrix))
        ari, jaccard = stability(matrix, labels, n_boot, seed=seed)
        min_jaccard = float(jaccard["jaccard"].min())
        rows.append((k, float(model.bic(matrix)), round(ari, 3), min_jaccard))
        if min_jaccard >= threshold:
            chosen = (labels, jaccard)
    selection = pd.DataFrame(rows, columns=["categories", "bic", "ari", "min_jaccard"])
    if chosen is None:
        return _single(matrix, selection)
    return LevelFit(chosen[0], matrix, selection, chosen[1])


def fit_categories(
    matrix: np.ndarray, min_split: int = 200, n_boot: int = 8, seed: int = 0
) -> CategoryFit:
    """Fit stable top-level categories, then stable subcategories.

    Args:
        matrix: Output of :func:`style_matrix`.
        min_split: Smallest top-level category that is split further.
        n_boot: Subsamples per candidate size.
        seed: Random seed.

    Returns:
        A :class:`CategoryFit` with paths like ``"1"`` and ``"1.2"``.
    """
    top = select_level(matrix, n_boot=n_boot, seed=seed)
    paths = np.array([str(label + 1) for label in top.labels], dtype=object)
    children: dict[int, LevelFit] = {}
    for parent in np.unique(top.labels):
        rows = np.flatnonzero(top.labels == parent)
        if len(rows) < min_split:
            continue
        child = select_level(matrix[rows], n_boot=n_boot, seed=seed)
        if child.labels.max() > 0:
            children[int(parent)] = child
            paths[rows] = [f"{parent + 1}.{label + 1}" for label in child.labels]
    return CategoryFit(labels=paths, top=top, children=children)


def _common_skeletons(
    skeletons: pd.Series, min_count: int, top: int, rounding_base: int
) -> str:
    frequent = skeletons.value_counts()
    frequent = frequent[frequent >= min_count].head(top)
    return " · ".join(
        f"{pattern} ({round_count(int(count), rounding_base)})"
        for pattern, count in frequent.items()
    )


_SUMMARY_COLUMNS = (
    "category",
    "share_of_searches",
    "median_words",
    "identifier_share",
    "prose_share",
    "symbol_share",
    "common_skeletons",
)


def _category_row(
    category: str,
    members: pd.DataFrame,
    share: float,
    min_count: int,
    top: int,
    rounding_base: int,
) -> dict[str, object]:
    return {
        "category": category,
        "share_of_searches": round(100 * share, 2),
        "median_words": float(members["n_words"].median()),
        "identifier_share": round(float(members["identifier_share"].mean()), 2),
        "prose_share": round(float(members["function_word_share"].mean()), 2),
        "symbol_share": round(float(members["symbol_share"].mean()), 2),
        "common_skeletons": _common_skeletons(
            members["skeleton"], min_count, top, rounding_base
        ),
    }


def describe_categories(
    distinct: pd.DataFrame,
    rows: pd.DataFrame,
    min_count: int = 10,
    top: int = 3,
    rounding_base: int = 1,
) -> pd.DataFrame:
    """Summarise each category by its measurements; safe to publish.

    Only topic-free statistics are reported. Categories with fewer than
    ``min_count`` distinct queries are left out, and a skeleton is listed
    only if at least ``min_count`` distinct queries share it.

    Args:
        distinct: Distinct queries with ``category``, feature and
            ``skeleton`` columns.
        rows: Log rows with a ``category`` column.
        min_count: Smallest count that may be published.
        top: Skeletons listed per category.
        rounding_base: Round counts to a multiple of this, and compute shares
            from rounded counts, as the release report does; ``1`` keeps
            exact values.

    Returns:
        One row per category, in hierarchy order.
    """
    searches = rows["category"].value_counts()
    total = round_count(len(rows), rounding_base) or 1

    def share(category: object) -> float:
        return round_count(int(searches.get(category, 0)), rounding_base) / total

    records = [
        _category_row(
            str(category), members, share(category), min_count, top, rounding_base
        )
        for category in np.unique(distinct["category"].to_numpy())
        if len(members := distinct[distinct["category"] == category]) >= min_count
    ]
    if not records:
        return pd.DataFrame(columns=list(_SUMMARY_COLUMNS))
    return pd.DataFrame(records).sort_values("category", ignore_index=True)
