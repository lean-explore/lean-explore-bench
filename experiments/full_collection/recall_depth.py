"""Replay labelled requests at several first-stage depths, without reranking.

For each depth k the engine's own BM25 and FAISS calls run with
``bm25_k = faiss_k = k``. The runner records where every recorded target sits
in the lexical, dense, fused and selected rankings, plus an exhaustive FAISS
search at the largest depth. Selection keeps the engine's 500-candidate pool.
Only target ranks and list lengths are journalled.

``--profile N`` instead times retrieval and full declaration loading for the
first N labelled requests and measures traced Python memory at each depth.
"""

import argparse
import asyncio
import json
import os
import random
import sqlite3
import time
import tracemalloc
import types
from pathlib import Path

from collection import digest, write
from run import completed_ids

DEPTHS = (50, 100, 250, 500, 1000, 2000, 3000, 5000)


def ranks_of(ranking, wanted):
    """Return the 1-based rank of each wanted identifier, or None if absent."""
    found = {}
    for rank, identifier in enumerate(ranking, 1):
        if identifier in wanted and identifier not in found:
            found[identifier] = rank
    return {str(t): found.get(t) for t in sorted(wanted)}


def ordered(scores):
    """Engine ordering of a score map: descending score, insertion order on ties."""
    return sorted(scores, key=scores.__getitem__, reverse=True)


def matched_documents(bm25, tokens):
    """Index positions containing at least one query token.

    BM25+ gives every document a positive score, so a positive score does not
    mean a lexical match.
    """
    import numpy as np

    scores = bm25.scores
    slices = [
        scores["indices"][scores["indptr"][t] : scores["indptr"][t + 1]]
        for t in bm25.get_tokens_ids(tokens)
    ]
    return np.unique(np.concatenate(slices)) if slices else np.empty(0, dtype=int)


def labelled_cases(path):
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    return [c for c in cases if any(m["targets"] for m in c["memberships"])]


def load_corpus(database):
    """Read names, packages, dependencies and informalization presence once."""
    names, light, informal = {}, {}, {}
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as conn:
        query = (
            "SELECT id, name, module, dependencies,"
            " informalization IS NOT NULL AND length(informalization) > 0"
            " FROM declarations"
        )
        for ident, name, module, dependencies, has_informal in conn.execute(query):
            names[name] = ident
            light[ident] = types.SimpleNamespace(
                name=name, module=module, dependencies=dependencies
            )
            informal[ident] = bool(has_informal)
    return names, light, informal


def make_engine(args, models):
    from lean_explore.search.engine import SearchEngine

    return SearchEngine(
        db_url=f"sqlite+aiosqlite:///{args.data / 'lean_explore.db'}",
        data_directory=args.data,
        embedding_model_name=models["Qwen/Qwen3-Embedding-0.6B"]["path"],
        reranker_model_name=models["Qwen/Qwen3-Reranker-0.6B"]["path"],
    )


async def replay(args):
    import faiss
    import lean_explore
    import numpy as np
    import torch
    from lean_explore.search.indexes import FAISS_NPROBE
    from lean_explore.search.ranking import (
        DEPENDENCY_BOOST_POOL_SIZE,
        apply_dependency_boost,
        fuse_rankings,
    )
    from lean_explore.search.tokenization import tokenize_raw, tokenize_spaced

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    cases = labelled_cases(args.cases)
    scheduled = [c["id"] for c in cases]
    if len(set(scheduled)) != len(scheduled):
        raise ValueError("Duplicate request identifiers")
    package = Path(lean_explore.__file__).parent
    models = json.loads(args.models.read_text())
    deepest = max(DEPTHS)
    settings = dict(
        depths=list(DEPTHS),
        exhaustive_depth=deepest,
        faiss_nprobe=FAISS_NPROBE,
        selection_pool=DEPENDENCY_BOOST_POOL_SIZE,
        exclude_zero_bm25=False,
        dependency_boost=True,
        package_filter="not applied; raw stages precede package filtering",
        seed=42,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    contract = dict(
        cases_sha256=digest(args.cases),
        runner_sha256=digest(__file__),
        scope="Labelled requests; retrieval, fusion and selection without reranking.",
        models=models,
        settings=settings,
        scheduled_ids=scheduled,
        source_files_sha256={
            str(p.relative_to(package)): digest(p)
            for p in sorted(package.rglob("*.py"))
        },
        data_files_sha256={
            str(p.relative_to(args.data)): digest(p)
            for p in sorted(args.data.rglob("*"))
            if p.is_file()
        },
    )
    contract_path = args.out / "contract.json"
    journal = args.out / "records.jsonl"
    if contract_path.exists():
        if json.loads(contract_path.read_text()) != contract:
            raise ValueError("Resume inputs changed")
    elif journal.exists():
        raise ValueError("Journal exists without a contract")
    else:
        write(contract_path, contract)
        (args.out / "executed_runner.py").write_bytes(Path(__file__).read_bytes())
    done = completed_ids(journal, scheduled)

    names, light, informal = load_corpus(args.data / "lean_explore.db")
    targets = sorted({t for c in cases for m in c["memberships"] for t in m["targets"]})
    write(args.out / "target-availability.json", {t: names.get(t) for t in targets})
    write(
        args.out / "target-corpus.json",
        {
            t: dict(
                id=names[t],
                module=light[names[t]].module,
                has_informalization=informal[names[t]],
            )
            for t in targets
            if t in names
        },
    )

    engine = make_engine(args, models)
    indexes = engine.indexes
    spaced, raw = indexes._load_bm25()
    faiss_index = indexes.faiss_index
    faiss_ids = indexes.faiss_id_map
    faiss_position = {cid: p for p, cid in enumerate(faiss_ids)}
    bm25_position = {cid: p for p, cid in enumerate(indexes._bm25_id_map)}
    started = time.monotonic()
    errors = 0
    try:
        await engine.embedding_client.embed(["natural number addition"], is_query=True)
        with journal.open("a", encoding="utf-8") as stream:
            for index, case in enumerate(cases[len(done) :], len(done)):
                wanted = {
                    names[t]
                    for m in case["memberships"]
                    for t in m["targets"]
                    if t in names
                }
                record = dict(query_id=case["id"], status="error")
                try:
                    query = case["query"]
                    if not query.strip():
                        raise ValueError("Empty query")
                    tick = time.perf_counter()
                    embedded = await engine.embedding_client.embed(
                        [query], is_query=True
                    )
                    embedding = embedded.embeddings[0]
                    embed_ms = 1000 * (time.perf_counter() - tick)
                    vector = np.array([embedding], dtype=np.float32)
                    faiss.normalize_L2(vector)
                    _, lists = faiss_index.quantizer.search(vector, FAISS_NPROBE)
                    invlists = faiss_index.invlists
                    probed_positions = np.concatenate(
                        [
                            faiss.rev_swig_ptr(
                                invlists.get_ids(int(i)), invlists.list_size(int(i))
                            ).copy()
                            for i in lists[0]
                            if i >= 0
                        ]
                    )
                    probed = int(len(probed_positions))
                    spaced_docs = matched_documents(spaced, tokenize_spaced(query))
                    raw_docs = matched_documents(raw, tokenize_raw(query))
                    lexical_docs = np.union1d(spaced_docs, raw_docs)
                    matched = dict(
                        spaced=len(spaced_docs),
                        raw=len(raw_docs),
                        union=len(lexical_docs),
                    )
                    lexical_hits = set(
                        lexical_docs[
                            np.isin(lexical_docs, [bm25_position[t] for t in wanted])
                        ].tolist()
                    )
                    probed_hits = set(
                        probed_positions[
                            np.isin(
                                probed_positions, [faiss_position[t] for t in wanted]
                            )
                        ].tolist()
                    )
                    reachability = {
                        str(t): dict(
                            lexical_match=bm25_position[t] in lexical_hits,
                            probed=faiss_position[t] in probed_hits,
                        )
                        for t in sorted(wanted)
                    }
                    depths = {}
                    for k in DEPTHS:
                        t0 = time.perf_counter()
                        lexical = indexes.name_candidates(query, k)
                        t1 = time.perf_counter()
                        dense = indexes.semantic_candidates(embedding, k)
                        t2 = time.perf_counter()
                        fused = fuse_rankings(lexical, dense)
                        t3 = time.perf_counter()
                        pool = {
                            cid: light[cid]
                            for cid, _ in fused[:DEPENDENCY_BOOST_POOL_SIZE]
                            if cid in light
                        }
                        selection = apply_dependency_boost(fused, pool)
                        t4 = time.perf_counter()
                        depths[str(k)] = dict(
                            lengths=dict(
                                lexical=len(lexical),
                                dense=len(dense),
                                fused=len(fused),
                                selection=len(selection),
                            ),
                            ms=dict(
                                lexical=1000 * (t1 - t0),
                                dense=1000 * (t2 - t1),
                                fusion=1000 * (t3 - t2),
                                selection=1000 * (t4 - t3),
                            ),
                            ranks=dict(
                                lexical=ranks_of(ordered(lexical), wanted),
                                dense=ranks_of(ordered(dense), wanted),
                                fused=ranks_of((c for c, _ in fused), wanted),
                                selection=ranks_of((c for c, _ in selection), wanted),
                            ),
                        )
                    t0 = time.perf_counter()
                    faiss_index.nprobe = faiss_index.nlist
                    try:
                        similarities, positions = faiss_index.search(vector, deepest)
                    finally:
                        faiss_index.nprobe = FAISS_NPROBE
                    exhaustive = {}
                    for position, similarity in zip(positions[0], similarities[0]):
                        if 0 <= position < len(faiss_ids):
                            cid = faiss_ids[position]
                            exhaustive[cid] = max(
                                exhaustive.get(cid, -1.0), float(similarity)
                            )
                    exhaustive_ms = 1000 * (time.perf_counter() - t0)
                    record.update(
                        status="ok",
                        embed_ms=embed_ms,
                        probed_vectors=probed,
                        bm25_matched=matched,
                        reachability=reachability,
                        depths=depths,
                        exhaustive_dense=dict(
                            depth=deepest,
                            length=len(exhaustive),
                            ms=exhaustive_ms,
                            ranks=ranks_of(ordered(exhaustive), wanted),
                        ),
                    )
                except Exception as exc:
                    errors += 1
                    record["error"] = dict(type=type(exc).__name__, message=str(exc))
                stream.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                )
                stream.flush()
                if (index + 1) % 25 == 0 or index + 1 == len(cases):
                    os.fsync(stream.fileno())
                    count = index + 1 - len(done)
                    elapsed = time.monotonic() - started
                    progress = dict(
                        completed=index + 1,
                        scheduled=len(cases),
                        this_session_errors=errors,
                        elapsed_seconds=elapsed,
                        seconds_per_query=elapsed / count,
                        estimated_remaining_seconds=(len(cases) - index - 1)
                        * elapsed
                        / count,
                    )
                    write(args.out / "progress.json", progress)
                    print(json.dumps(progress), flush=True)
        write(
            args.out / "complete.json",
            dict(
                scheduled=len(cases),
                completed=len(completed_ids(journal, scheduled)),
                records_sha256=digest(journal),
                contract_sha256=digest(contract_path),
                gpu=torch.cuda.get_device_name(0),
                latency_scope="Local instrumented replay, not production latency",
            ),
        )
    finally:
        await engine.engine.dispose()


async def profile(args):
    """Time retrieval plus full declaration loading, and trace Python memory."""
    import resource

    import numpy as np
    from lean_explore.search.ranking import fuse_rankings

    cases = labelled_cases(args.cases)[: args.profile]
    models = json.loads(args.models.read_text())
    engine = make_engine(args, models)
    indexes = engine.indexes
    rss_start = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    indexes._load_bm25()
    _ = indexes.faiss_index
    rss_loaded = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rows = {str(k): [] for k in DEPTHS}
    try:
        await engine.embedding_client.embed(["natural number addition"], is_query=True)
        await engine._load_declarations([1])
        embeddings = []
        for case in cases:
            response = await engine.embedding_client.embed(
                [case["query"]], is_query=True
            )
            embeddings.append(response.embeddings[0])
        for k in DEPTHS:
            for case, embedding in zip(cases, embeddings):
                # Timings come from an untraced pass; tracing slows allocation.
                t0 = time.perf_counter()
                lexical = indexes.name_candidates(case["query"], k)
                dense = indexes.semantic_candidates(embedding, k)
                fused = fuse_rankings(lexical, dense)
                t1 = time.perf_counter()
                ids = [c for c, _ in fused[:k]]
                loaded = await engine._load_declarations(ids)
                t2 = time.perf_counter()
                del loaded
                tracemalloc.start()
                lexical = indexes.name_candidates(case["query"], k)
                dense = indexes.semantic_candidates(embedding, k)
                fused = fuse_rankings(lexical, dense)
                retrieval_peak = tracemalloc.get_traced_memory()[1]
                tracemalloc.reset_peak()
                loaded = await engine._load_declarations(ids)
                load_peak = tracemalloc.get_traced_memory()[1]
                tracemalloc.stop()
                rows[str(k)].append(
                    dict(
                        retrieval_ms=1000 * (t1 - t0),
                        load_ms=1000 * (t2 - t1),
                        loaded=len(loaded),
                        retrieval_peak_bytes=retrieval_peak,
                        load_peak_bytes=load_peak,
                    )
                )
                del loaded
    finally:
        await engine.engine.dispose()
    summary = {}
    for k, values in rows.items():
        summary[k] = {
            key: dict(
                median=float(np.median([v[key] for v in values])),
                p95=float(np.percentile([v[key] for v in values], 95)),
            )
            for key in values[0]
        }
    write(
        args.out / "profile.json",
        dict(
            requests=len(cases),
            scope="Retrieval and fusion, then full ORM rows for the top-k fused candidates",
            max_rss_kib=dict(
                before_indexes=rss_start,
                after_indexes=rss_loaded,
                end=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            ),
            depths=summary,
        ),
    )


def main():
    os.environ.update(
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
        TOKENIZERS_PARALLELISM="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        LEAN_EXPLORE_EMBEDDING_BATCH_SIZE="32",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "data", "models", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--profile", type=int, default=0)
    args = parser.parse_args()
    asyncio.run(profile(args) if args.profile else replay(args))


if __name__ == "__main__":
    main()
