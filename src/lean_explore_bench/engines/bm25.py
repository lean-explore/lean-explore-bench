"""A BM25 baseline with no learned component.

Every Mathlib declaration of a corpus snapshot is one document: its name, its
docstring and the start of its source. Names are also split into their parts
(``Finset.sum_comm`` gives ``finset``, ``sum``, ``comm``), so that a query in
words can match a name. The parameters are the usual defaults and were not
tuned on the benchmark.

Needs the ``bm25`` extra (NumPy and SciPy) and a LeanExplore corpus snapshot::

    leb run DIR --engine bm25 --corpus lean_explore.db
"""

import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from lean_explore_bench.engines.base import Engine

K1, B = 1.2, 0.75
NAME_WEIGHT = 3
SOURCE_CHARS = 1500
_WORD = re.compile(r"[A-Za-z][a-z]*|[A-Z]+(?![a-z])|\d+|[^\sA-Za-z\d_.()\[\]{},:]")


def tokens(text: str) -> list[str]:
    """Split text into lower-case words, name parts, digits and symbols."""
    return [match.group().lower() for match in _WORD.finditer(text)]


def name_tokens(name: str) -> list[str]:
    """The parts of a name, and the name itself as one token."""
    return [*tokens(name), name.lower()]


def read_documents(corpus: Path) -> tuple[list[str], list[Counter[str]]]:
    """Read every Mathlib declaration as a bag of tokens."""
    connection = sqlite3.connect(corpus)
    rows = connection.execute(
        "SELECT name, docstring, source_text FROM declarations "
        "WHERE module LIKE 'Mathlib.%' ORDER BY name"
    )
    names, bags = [], []
    for name, docstring, source in rows:
        bag: Counter[str] = Counter()
        for token in name_tokens(name):
            bag[token] += NAME_WEIGHT
        bag.update(tokens(docstring or ""))
        bag.update(tokens(source[:SOURCE_CHARS]))
        names.append(name)
        bags.append(bag)
    connection.close()
    return names, bags


def build(bags: list[Counter[str]]) -> tuple[dict[str, int], Any]:
    """Return the vocabulary and the term-by-document matrix of BM25 weights."""
    vocabulary: dict[str, int] = {}
    rows, columns, counts = [], [], []
    for document, bag in enumerate(bags):
        for token, count in bag.items():
            rows.append(vocabulary.setdefault(token, len(vocabulary)))
            columns.append(document)
            counts.append(count)
    shape = (len(vocabulary), len(bags))
    frequency = sparse.csr_matrix((counts, (rows, columns)), shape=shape, dtype=float)
    lengths = np.asarray(frequency.sum(axis=0)).ravel()
    present = np.diff(frequency.indptr)
    idf = np.log(1 + (len(bags) - present + 0.5) / (present + 0.5))
    norm = K1 * (1 - B + B * lengths / lengths.mean())
    weighted = frequency.tocoo()
    weighted.data = (
        idf[weighted.row]
        * weighted.data
        * (K1 + 1)
        / (weighted.data + norm[weighted.col])
    )
    return vocabulary, weighted.tocsr()


def best_documents(
    query: str, vocabulary: dict[str, int], weights: Any, limit: int
) -> list[int]:
    """Indices of the ``limit`` best documents for ``query``, best first."""
    wanted = {*tokens(query), *(part.lower() for part in query.split())}
    rows = sorted({vocabulary[token] for token in wanted if token in vocabulary})
    if not rows:
        return []
    scores = np.asarray(weights[rows].sum(axis=0)).ravel()
    if limit < len(scores):
        best = np.argpartition(-scores, limit)[:limit]
    else:
        best = np.arange(len(scores))
    best = best[np.argsort(-scores[best], kind="stable")]
    return [int(index) for index in best[scores[best] > 0]]


@dataclass(frozen=True)
class BM25(Engine):
    """BM25 over the declarations of a corpus snapshot.

    Attributes:
        corpus: Path of the snapshot's ``lean_explore.db``.
    """

    name: str = "bm25"
    interval_seconds: float = 0.0
    corpus: Path = Path("lean_explore.db")

    @cached_property
    def _index(self) -> tuple[list[str], dict[str, int], Any]:
        names, bags = read_documents(self.corpus)
        vocabulary, weights = build(bags)
        return names, vocabulary, weights

    def search(self, query: str, limit: int) -> list[str]:
        """Search the snapshot."""
        names, vocabulary, weights = self._index
        found = best_documents(query, vocabulary, weights, limit)
        return [names[index] for index in found]
