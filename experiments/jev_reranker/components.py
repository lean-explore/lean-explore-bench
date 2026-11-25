"""Add the non-neural terms of LeanExplore's final score to dumped pools.

For each candidate this records the three signals that combine_rerank_scores adds to
the reranker score: normalized BM25 over the informalization, the normalized dependent
count, and the fuzzy name match (raw and normalized). With these, final-score weights
can be retuned offline. Runs in a LeanExplore environment; no GPU is needed.
"""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from lean_explore.models import Declaration
from lean_explore.search.ranking import (
    DEFAULT_RERANK_WEIGHTS,
    count_dependents,
    informal_bm25_scores,
)
from lean_explore.search.scoring import (
    fuzzy_name_score,
    normalize_dependency_counts,
    normalize_scores,
)


async def main(args: argparse.Namespace) -> None:
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{Path(args.data_directory) / 'lean_explore.db'}"
    )
    weights = DEFAULT_RERANK_WEIGHTS
    with Path(args.output).open("x") as out:
        for line in Path(args.pools).read_text().splitlines():
            record = json.loads(line)
            names = [c["name"] for c in record["candidates"]]
            async with AsyncSession(engine) as session:
                rows = await session.execute(
                    select(Declaration).where(Declaration.name.in_(names))
                )
                by_name = {d.name: d for d in rows.scalars().all()}
            pool = [by_name[name] for name in names]
            query = record["query"]
            fuzzy = [fuzzy_name_score(query, d.name) for d in pool]
            dependents = count_dependents(pool)
            signals = {
                "bm25": normalize_scores(informal_bm25_scores(query, pool)),
                "dependency": normalize_dependency_counts(
                    [dependents[d.name] for d in pool]
                ),
                "fuzzy": fuzzy,
                "fuzzy_normalized": normalize_scores(fuzzy),
            }
            for i, candidate in enumerate(record["candidates"]):
                rest = (
                    weights.informal_bm25 * signals["bm25"][i]
                    + weights.dependency * signals["dependency"][i]
                )
                if fuzzy[i] >= weights.fuzzy_name_threshold:
                    rest += weights.fuzzy_name * signals["fuzzy_normalized"][i]
                assert abs(rest - candidate["rest"]) < 1e-6, (record["id"], i)
            out.write(json.dumps({"id": record["id"], **signals}) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", required=True)
    parser.add_argument("--pools", required=True)
    parser.add_argument("--output", required=True)
    asyncio.run(main(parser.parse_args()))
