"""A BM25 baseline for the query mix, with no learned component.

Every Mathlib declaration of a corpus snapshot is one document: its name, its
docstring and the start of its source. Names are also split into their parts
(``Finset.sum_comm`` gives ``finset``, ``sum``, ``comm``), so that a query in
words can match a name. The parameters are the usual defaults and were not
tuned on the benchmark.

    python experiments/bm25_baseline/run.py --corpus lean_explore.db --out data/mix

writes ``runs/bm25.jsonl`` in the format of ``leb-mix run``, so that
``leb-mix score --engine bm25`` scores it.
"""

import argparse
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse

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


def build(bags: list[Counter[str]]) -> tuple[dict[str, int], sparse.csr_matrix]:
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


def search(
    query: str, vocabulary: dict[str, int], weights: sparse.csr_matrix, limit: int
) -> np.ndarray:
    """Indices of the ``limit`` best documents for ``query``, best first."""
    wanted = {*tokens(query), *(part.lower() for part in query.split())}
    rows = sorted({vocabulary[token] for token in wanted if token in vocabulary})
    if not rows:
        return np.array([], dtype=int)
    scores = np.asarray(weights[rows].sum(axis=0)).ravel()
    best = np.argpartition(-scores, limit)[:limit]
    best = best[np.argsort(-scores[best], kind="stable")]
    return best[scores[best] > 0]


def main() -> None:
    """Run BM25 on every query of a mix and write the run file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="directory of the mix")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    names, bags = read_documents(args.corpus)
    vocabulary, weights = build(bags)
    print(f"{len(names)} documents, {len(vocabulary)} terms")
    lines = (args.out / "queries.jsonl").read_text(encoding="utf-8").splitlines()
    path = args.out / "runs" / "bm25.jsonl"
    with path.open("w", encoding="utf-8") as file:
        for line in filter(str.strip, lines):
            record = json.loads(line)
            found = search(record["query"], vocabulary, weights, args.limit)
            row = {
                "id": record["id"],
                "limit": args.limit,
                "status": "ok",
                "documents": [names[index] for index in found],
            }
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {path}")
    assert math.isfinite(weights.sum())


if __name__ == "__main__":
    main()
