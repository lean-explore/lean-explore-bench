"""Pool what the engines returned, so that it can be judged.

A written query is labelled with the one declaration it was written from,
and a thread query with the declarations its thread names. Other
declarations can answer a query equally well, and an engine that returns
one of them is scored as wrong. Pooling is the standard remedy: for each
query, the top results of every engine are merged into one list without
saying which engine returned what, a judge grades each candidate, and the
grades are added to the query's labels.

:func:`tasks` builds the pools, and :func:`apply` adds the grades that come
back. Only grades 2 and 3 are added, because a result counts as a hit from
grade 2; a candidate the judge leaves out stays unlabelled.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from lean_explore_bench.mix.record import QueryRecord


def pooled_names(
    records: Iterable[QueryRecord],
    results: Mapping[str, Mapping[str, Mapping[str, Any]]],
    limit: int = 10,
    until_answer: bool = False,
) -> dict[str, set[str]]:
    """For each query, the names in the top ``limit`` results of any engine.

    Args:
        records: The queries of the mix.
        results: For each engine, its result for each query identifier.
        limit: How many results of each engine are pooled.
        until_answer: Pool an engine's results only as far as its first
            labelled answer. Whether an engine has an answer among its
            first k results, and at which rank the first one comes, depend
            only on those results, so success and reciprocal rank are then
            exact while about half as many candidates need a grade.
    """
    pooled: dict[str, set[str]] = {}
    for record in records:
        names: set[str] = set()
        for engine in results.values():
            for name in engine.get(record.id, {}).get("documents", [])[:limit]:
                if until_answer and record.judgments.get(name, 0) >= 2:
                    break
                names.add(name)
        pooled[record.id] = names
    return pooled


def tasks(
    records: Iterable[QueryRecord],
    pooled: Mapping[str, set[str]],
    statements: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Build one judging task per query that has unlabelled candidates.

    Args:
        records: The queries of the mix.
        pooled: The pooled names of each query, from :func:`pooled_names`.
        statements: The start of the source of every pooled or labelled
            declaration that the corpus holds.

    Returns:
        Tasks with the query, the declarations already labelled as answers,
        and the candidates: every pooled result that has no label yet and
        is a declaration of the corpus, in name order so that neither
        engine nor rank can be read off.
    """
    result = []
    for record in records:
        candidates = sorted(
            name
            for name in pooled.get(record.id, set())
            if name not in record.judgments and name in statements
        )
        if candidates:
            result.append(
                {
                    "id": record.id,
                    "query": record.query,
                    "answers": [
                        {
                            "name": name,
                            "grade": grade,
                            "statement": statements.get(name),
                        }
                        for name, grade in record.judgments.items()
                        if grade >= 2
                    ],
                    "candidates": [
                        {"name": name, "statement": statements[name]}
                        for name in candidates
                    ],
                }
            )
    return result


def apply(
    records: Iterable[QueryRecord],
    graded: Mapping[str, Mapping[str, int]],
    judge: str,
) -> list[QueryRecord]:
    """Add pooled grades to the records' labels.

    Args:
        records: The queries of the mix.
        graded: For a query identifier, the grade (2 or 3) of each candidate
            the judge found relevant.
        judge: Who graded the pools, recorded in the provenance.

    Returns:
        The records, with each accepted grade added to ``judgments``. A
        label that was already present is never changed. The names added
        are listed under ``pooled`` in the provenance.
    """
    updated = []
    for record in records:
        added = {
            name: grade
            for name, grade in graded.get(record.id, {}).items()
            if grade in (2, 3) and name not in record.judgments
        }
        if not added:
            updated.append(record)
            continue
        value = record.to_json()
        value["judgments"] = {**record.judgments, **added}
        value["provenance"] = {
            **record.provenance,
            "pooled": sorted(added),
            "pool_judge": judge,
        }
        updated.append(QueryRecord.from_json(value))
    return updated
