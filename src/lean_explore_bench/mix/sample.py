"""Draw target declarations for every bucket of the mix.

Sampling is flattened across areas of a library: an area is chosen with
probability proportional to the square root of its size, then a declaration
uniformly within it. Large areas (``Mathlib.Algebra``) still appear most, but
small ones are not drowned out. No declaration is used twice, so each target
is its own independent group.
"""

import hashlib
import math
import random
from collections import defaultdict
from dataclasses import dataclass

from lean_explore_bench.mix.corpus import Corpus, Declaration
from lean_explore_bench.mix.spec import KINDS_OF_TYPE, MixSpec


@dataclass(frozen=True)
class Target:
    """A declaration assigned to a bucket.

    Attributes:
        declaration: The target declaration.
        query_type: The bucket.
        order: Position within its (bucket, library) cell. Targets beyond the
            cell's quota are reserves, used only when earlier ones fail.
    """

    declaration: Declaration
    query_type: str
    order: int

    @property
    def id(self) -> str:
        """Stable identifier of the query written for this target."""
        digest = hashlib.sha256(self.declaration.name.encode()).hexdigest()[:10]
        return f"{self.query_type}-{self.declaration.library}-{digest}"


def _draw(
    by_area: dict[str, list[Declaration]], count: int, rng: random.Random
) -> list[Declaration]:
    """Draw up to ``count`` declarations, flattening across areas."""
    pools = {area: list(items) for area, items in sorted(by_area.items()) if items}
    for items in pools.values():
        rng.shuffle(items)
    drawn: list[Declaration] = []
    while pools and len(drawn) < count:
        areas = list(pools)
        weights = [math.sqrt(len(by_area[area])) for area in areas]
        area = rng.choices(areas, weights=weights)[0]
        drawn.append(pools[area].pop())
        if not pools[area]:
            del pools[area]
    return drawn


def sample_targets(corpus: Corpus, spec: MixSpec) -> list[Target]:
    """Assign distinct target declarations to every bucket cell.

    Args:
        corpus: The corpus snapshot.
        spec: The mix specification.

    Returns:
        Targets ordered by bucket, library and position. Each cell holds its
        quota plus reserves.

    Raises:
        ValueError: If a library has too few eligible declarations.
    """
    rng = random.Random(spec.seed)
    used: set[str] = set()
    cells: dict[tuple[str, str], list[Declaration]] = {}

    def draw(query_type: str, library: str, wanted: int) -> list[Declaration]:
        by_area: dict[str, list[Declaration]] = defaultdict(list)
        for declaration in corpus.eligible:
            if (
                declaration.library == library
                and declaration.kind in KINDS_OF_TYPE[query_type]
                and declaration.name not in used
            ):
                by_area[declaration.area].append(declaration)
        drawn = _draw(by_area, wanted, rng)
        used.update(declaration.name for declaration in drawn)
        return drawn

    # The first draw does not depend on the shape, so its targets are the
    # same in every shape; a second draw adds what a cell still lacks.
    first = spec.draw_counts
    for query_type in spec.query_types:
        for library, quota in first.items():
            wanted = quota + math.ceil(quota * spec.reserve)
            cells[(query_type, library)] = draw(query_type, library, wanted)
    cells = {
        cell: drawn for cell, drawn in cells.items() if cell[1] in spec.library_counts
    }
    for query_type in spec.query_types:
        for library in spec.library_counts:
            extra = spec.count(query_type, library) - first.get(library, 0)
            if extra > 0:
                wanted = extra + math.ceil(extra * spec.reserve)
                drawn = cells.setdefault((query_type, library), [])
                drawn += draw(query_type, library, wanted)
    targets: list[Target] = []
    for (query_type, library), drawn in cells.items():
        quota = spec.count(query_type, library)
        if len(drawn) < quota:
            raise ValueError(
                f"Library {library!r} has {len(drawn)} eligible declarations "
                f"for {query_type!r} queries; {quota} are needed"
            )
        targets.extend(
            Target(declaration, query_type, order)
            for order, declaration in enumerate(drawn)
        )
    return targets
