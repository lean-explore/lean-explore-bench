"""Write declaration-name queries without a language model.

People and agents rarely type a full, correct name. Each name query is one
of five variants of the target's name:

- ``exact``: the full name;
- ``suffix``: the name without its leading namespaces;
- ``spaced``: the name with dots and underscores turned into spaces;
- ``typo``: the full name with one small typing error in its last part;
- ``lowercase``: the full name in lower case.

A suffix can match several declarations. Every declaration whose name ends
with the same suffix is then an equally good answer and is graded 3.
"""

import random
import re
from collections import defaultdict
from collections.abc import Iterable

from lean_explore_bench.builder.sample import Target
from lean_explore_bench.record import QueryRecord

VARIANT_WEIGHTS = {
    "exact": 0.30,
    "suffix": 0.25,
    "spaced": 0.15,
    "typo": 0.15,
    "lowercase": 0.15,
}
"""Share of each variant among name queries."""

MAX_SUFFIX_MATCHES = 5
"""A suffix shared by more declarations than this is too vague to use."""

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def suffix_index(names: Iterable[str]) -> dict[str, list[str]]:
    """Map every dotted suffix of every name, the name included, to its names."""
    index: dict[str, list[str]] = defaultdict(list)
    for name in names:
        parts = name.split(".")
        for start in range(len(parts)):
            index[".".join(parts[start:])].append(name)
    return index


def spaced(name: str) -> str:
    """Turn ``Nat.add_comm`` into ``Nat add comm``, splitting camel case."""
    words = _CAMEL.sub(" ", name.replace(".", " ").replace("_", " "))
    return " ".join(words.split())


def typo(name: str, rng: random.Random) -> str:
    """Introduce one typing error into the last component of ``name``.

    The error swaps two neighbouring letters or drops one letter. Names whose
    last component is shorter than four characters are returned unchanged.
    """
    head, _, last = name.rpartition(".")
    if len(last) < 4:
        return name
    position = rng.randrange(1, len(last) - 1)
    if rng.random() < 0.5 and last[position] != last[position + 1]:
        changed = (
            last[:position] + last[position + 1] + last[position] + last[position + 2 :]
        )
    else:
        changed = last[:position] + last[position + 1 :]
    return f"{head}.{changed}" if head else changed


def _suffix_query(
    name: str, index: dict[str, list[str]]
) -> tuple[str, list[str]] | None:
    """Return the shortest usable suffix of ``name`` and the names it matches."""
    parts = name.split(".")
    for start in range(len(parts) - 1, 0, -1):
        suffix = ".".join(parts[start:])
        matches = index[suffix]
        if len(matches) <= MAX_SUFFIX_MATCHES:
            return suffix, sorted(matches)
    return None


def name_query(
    target: Target,
    index: dict[str, list[str]],
    all_names: frozenset[str],
    rng: random.Random,
) -> QueryRecord:
    """Write the name query for one target.

    Args:
        target: The target; its bucket must be ``name``.
        index: Suffix index of the whole corpus, from :func:`suffix_index`.
        all_names: Every name in the corpus.
        rng: Random source for the variant and the typing error.

    Returns:
        The query record. A variant that cannot be applied to this name (no
        usable suffix, a name too short for a typo, a changed form that is
        itself another declaration) falls back to ``exact``.
    """
    name = target.declaration.name
    variant = rng.choices(
        list(VARIANT_WEIGHTS), weights=list(VARIANT_WEIGHTS.values())
    )[0]
    query = name
    answers = [name]
    if variant == "suffix":
        found = _suffix_query(name, index)
        if found is not None:
            query, answers = found
    elif variant == "spaced":
        query = spaced(name)
    elif variant == "typo":
        query = typo(name, rng)
    elif variant == "lowercase":
        query = name.lower()
    if variant != "exact" and (
        query == name or (variant != "suffix" and query in all_names)
    ):
        variant, query, answers = "exact", name, [name]
    return QueryRecord(
        id=target.id,
        query=query,
        query_type="name",
        variant=variant,
        source="declaration",
        library=target.declaration.library,
        area=target.declaration.area,
        target=name,
        judgments=dict.fromkeys(answers, 3),
        group_id=name,
        track="unknown",
        provenance={"method": "programmatic"},
    )
