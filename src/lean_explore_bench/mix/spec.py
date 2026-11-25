"""The shape of the query mix: which buckets exist and how large each is.

Two shapes exist. In the uniform shape every form holds the same number of
queries (200) written from a declaration, and thread queries are added on
top. In the balanced shape (:func:`balanced`) the mix has four buckets of
800 queries, defined by what the searcher is doing, not by how often
LeanExplore's own users do it:

- ``names and keywords``: search terms, with or without Lean names.
- ``natural language``: a statement or concept described in words.
- ``formal``: Lean code, a pattern or a proof state.
- ``real questions``: questions people asked on the Lean Zulip.

The benchmark score is the plain mean of the four bucket scores, so no
engine's own traffic decides the weights. Every target is in Mathlib,
because that is the one library every engine indexes; the uniform shape
spreads written queries over six libraries instead.
"""

from dataclasses import dataclass, field

from lean_explore_bench.mix.forms import FORMS

QUERY_TYPES = FORMS
"""Query types written from a known target declaration: the eight forms of
:mod:`lean_explore_bench.mix.forms`. Real questions from the Lean Zulip form
a ninth bucket, ``question``, which is not written from a target."""

_ANY = frozenset({"theorem", "definition", "structure"})

KINDS_OF_TYPE: dict[str, frozenset[str]] = {
    "name": _ANY,
    "names": frozenset({"theorem"}),
    "names+keywords": _ANY,
    "keywords": _ANY,
    "prose": _ANY,
    "prose+names": _ANY,
    "formal": frozenset({"theorem", "definition"}),
    "goal": frozenset({"theorem"}),
}
"""Declaration kinds that can be the target of each query type."""

DEFAULT_LIBRARY_COUNTS = {
    "mathlib": 100,
    "core": 20,
    "physlib": 20,
    "cslib": 20,
    "flt": 20,
    "formal-conjectures": 20,
}
"""Queries per library in each bucket. Half are outside Mathlib."""

FIRST_DRAW_COUNTS = {
    "mathlib": 100,
    "core": 20,
    "physlib": 20,
    "cslib": 20,
    "flt": 15,
    "formal-conjectures": 15,
    "quantuminfo": 10,
}
"""Counts used for the first draw of targets. The first build of the mix
drew with these counts, and drawing with them again keeps every target it
chose. Libraries dropped since then (``quantuminfo``) are drawn and not
used; libraries that grew get further targets in a second draw."""


BUCKET_OF_FORM = {
    "name": "names and keywords",
    "names": "names and keywords",
    "names+keywords": "names and keywords",
    "keywords": "names and keywords",
    "prose": "natural language",
    "prose+names": "natural language",
    "formal": "formal",
    "goal": "formal",
}
"""Bucket of each written form."""

THREAD_BUCKET = "real questions"
"""Bucket of every query that comes from a discussion thread."""

BUCKETS = ("names and keywords", "natural language", "formal", THREAD_BUCKET)

BALANCED_TOTALS = {
    "name": 160,
    "names": 80,
    "names+keywords": 240,
    "keywords": 320,
    "prose": 480,
    "prose+names": 320,
    "formal": 480,
    "goal": 320,
}
"""Written queries per form in the balanced shape: 800 per bucket."""

BUCKET_SIZE = 800
"""Queries per bucket in the balanced shape. The size is set by the real
questions bucket: about 800 thread queries have an established Mathlib
answer."""


@dataclass(frozen=True)
class MixSpec:
    """Sizes and seed of a query mix.

    Attributes:
        library_counts: Queries per library in a bucket of the uniform
            shape; in other shapes, the spread of every bucket over libraries.
        type_totals: Queries written from a declaration in each bucket, or
            None for the uniform shape.
        first_draw: Counts for the first draw of targets, or None for the
            default (see :attr:`draw_counts`).
        query_types: The buckets.
        reserve: Extra targets drawn per bucket cell, as a share of the cell,
            to replace queries that fail a check.
        development_share: Share of target groups placed in the development
            split; the rest form the test split.
        seed: Seed for every random choice.
    """

    library_counts: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_LIBRARY_COUNTS)
    )
    query_types: tuple[str, ...] = QUERY_TYPES
    reserve: float = 1.0
    development_share: float = 0.2
    seed: int = 20261111
    type_totals: dict[str, int] | None = None
    first_draw: dict[str, int] | None = None

    def __post_init__(self) -> None:
        """Check the specification."""
        unknown = set(self.query_types) - set(QUERY_TYPES)
        if unknown:
            raise ValueError(f"Unknown query types: {sorted(unknown)}")
        if not self.library_counts or min(self.library_counts.values()) < 1:
            raise ValueError("Every library needs at least one query per bucket")
        if not 0 <= self.reserve <= 5:
            raise ValueError("reserve must be between 0 and 5")
        if not 0 < self.development_share < 1:
            raise ValueError("development_share must be strictly between 0 and 1")

    @property
    def draw_counts(self) -> dict[str, int]:
        """Counts for the first draw of targets.

        The default spread is drawn with :data:`FIRST_DRAW_COUNTS`; any
        other spread is drawn with its own counts.
        """
        if self.first_draw is not None:
            return self.first_draw
        if self.library_counts == DEFAULT_LIBRARY_COUNTS:
            return FIRST_DRAW_COUNTS
        return self.library_counts

    @property
    def per_type(self) -> int:
        """Queries in each bucket of the uniform shape."""
        return sum(self.library_counts.values())

    def count(self, query_type: str, library: str) -> int:
        """Queries written for ``library`` in the bucket ``query_type``.

        In a shape with ``type_totals`` the bucket's total is spread over
        the libraries in proportion to ``library_counts``; fractions go to
        the libraries with the largest remainders, so the total is exact.
        """
        if self.type_totals is None:
            return self.library_counts[library]
        total = self.type_totals[query_type]
        exact = {
            name: total * count / self.per_type
            for name, count in self.library_counts.items()
        }
        counts = {name: int(value) for name, value in exact.items()}
        by_remainder = sorted(exact, key=lambda name: counts[name] - exact[name])
        for name in by_remainder[: total - sum(counts.values())]:
            counts[name] += 1
        return counts[library]


MATHLIB_ONLY = {"mathlib": 200}
"""Library spread of the balanced shape. Other engines index Mathlib only, so
a benchmark of search, not of coverage, keeps every target inside it."""


def balanced() -> MixSpec:
    """The balanced shape: four buckets of 800 queries, all in Mathlib."""
    return MixSpec(
        library_counts=dict(MATHLIB_ONLY),
        type_totals=dict(BALANCED_TOTALS),
        first_draw=dict(FIRST_DRAW_COUNTS),
    )
