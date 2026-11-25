"""Command line for building, running and scoring the query mix.

Typical order::

    leb-mix profile  --log --to log-profile.json            # on the log server
    leb-mix generate --corpus lean_explore.db --out data/mix --style log-profile.json
    leb-mix zulip    --corpus lean_explore.db --out data/mix
    leb-mix contribute --corpus lean_explore.db --out data/mix --queries more.jsonl
    leb-mix build    --corpus lean_explore.db --out data/mix
    leb-mix profile  --queries data/mix/queries.jsonl --to mix-profile.json
    leb-mix compare  --reference log-profile.json --candidate mix-profile.json
    leb-mix run      --engine leanexplore --out data/mix
    leb-mix score    --engine leanexplore --out data/mix --weights log-profile.json
"""

import argparse
import asyncio
import json
import random
from pathlib import Path
from typing import Any

from lean_explore_bench.infra import OpenRouterClient, OpenRouterSettings
from lean_explore_bench.mix import (
    assemble,
    combine,
    engines,
    names,
    pool,
    profile,
    score,
    zulip,
)
from lean_explore_bench.mix.corpus import (
    Corpus,
    library_and_area,
    load_corpus,
    read_statements,
)
from lean_explore_bench.mix.generate import (
    GenerationSettings,
    generate,
    read_journal,
    submit,
    tasks,
)
from lean_explore_bench.mix.record import QueryRecord, read_records, write_records
from lean_explore_bench.mix.sample import Target, sample_targets
from lean_explore_bench.mix.spec import BUCKET_SIZE, MixSpec, balanced

DEFAULT_WRITER = "anthropic/claude-sonnet-5.5"
DEFAULT_JUDGE = "openai/gpt-6.1-terra"
MAX_ROUNDS = 6


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_profile(path: Path | None, group: str) -> dict[str, Any] | None:
    """Read one group of a profile file; a bare profile has no groups."""
    if path is None:
        return None
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if "profiles" in value:
        selected: dict[str, Any] = value["profiles"][group]
        return selected
    return value


def _settings(args: argparse.Namespace) -> GenerationSettings:
    return GenerationSettings(
        writer_model=args.writer_model,
        judge_model=args.judge_model,
        budget_usd=args.budget,
        style_profile=_read_profile(getattr(args, "style", None), args.group),
    )


def _accepted(journal: Path) -> list[QueryRecord]:
    return [
        QueryRecord.from_json(entry["record"])
        for entry in read_journal(journal).values()
        if entry["accepted"]
    ]


def _threads(out: Path) -> tuple[list[QueryRecord], list[QueryRecord]]:
    """The mix's own and the contributed accepted thread queries."""
    return (
        _accepted(out / "zulip-journal.jsonl"),
        _accepted(out / "contributed-journal.jsonl"),
    )


def _spec(args: argparse.Namespace) -> MixSpec:
    return balanced() if args.shape == "balanced" else MixSpec()


def _corpus(args: argparse.Namespace) -> Corpus:
    return load_corpus(args.corpus, established=getattr(args, "established", None))


def _split_targets(corpus: Corpus, spec: MixSpec) -> tuple[list[Target], list[Target]]:
    """Sample targets and separate name targets from language-model ones."""
    targets = sample_targets(corpus, spec)
    named = [target for target in targets if target.query_type == "name"]
    written = [target for target in targets if target.query_type != "name"]
    return named, written


async def _generate(args: argparse.Namespace) -> None:
    spec = _spec(args)
    corpus = _corpus(args)
    _, written = _split_targets(corpus, spec)
    journal = args.out / "journal.jsonl"
    async with OpenRouterClient(OpenRouterSettings.from_env()) as client:
        for _ in range(MAX_ROUNDS):
            pending = assemble.needed(
                written, read_journal(journal), spec, corpus.is_established
            )
            if not pending:
                break
            print(f"Writing {len(pending)} queries")
            await generate(client, _settings(args), pending, journal)
        print(f"Spent ${client.usage.cost:.2f} in {client.usage.requests} requests")
    allowed = corpus.is_established
    short = assemble.needed(written, read_journal(journal), spec, allowed)
    selected = assemble.select(written, read_journal(journal), spec, allowed)
    print(f"Accepted {len(selected)} queries; {len(short)} cells still short")


def _tasks(args: argparse.Namespace) -> None:
    spec = _spec(args)
    corpus = _corpus(args)
    _, written = _split_targets(corpus, spec)
    pending = assemble.needed(
        written, read_journal(args.out / "journal.jsonl"), spec, corpus.is_established
    )
    args.to.parent.mkdir(parents=True, exist_ok=True)
    with args.to.open("w", encoding="utf-8") as file:
        for task in tasks(_settings(args), pending):
            file.write(json.dumps(task, ensure_ascii=False) + "\n")
    print(f"Wrote {len(pending)} writing tasks to {args.to}")


async def _submit(args: argparse.Namespace) -> None:
    spec = _spec(args)
    corpus = _corpus(args)
    _, written = _split_targets(corpus, spec)
    journal = args.out / "journal.jsonl"
    pending = assemble.needed(
        written, read_journal(journal), spec, corpus.is_established
    )
    lines = args.queries.read_text(encoding="utf-8").splitlines()
    queries = {
        item["id"]: str(item["query"])
        for item in (json.loads(line) for line in lines if line.strip())
    }
    async with OpenRouterClient(OpenRouterSettings.from_env()) as client:
        before = read_journal(journal)
        taken = [target for target in pending if target.id in queries]
        if args.revise:
            by_name = corpus.by_name()
            taken += [
                Target(
                    by_name[entry["record"]["target"]], entry["record"]["query_type"], 0
                )
                for identifier, entry in before.items()
                if identifier in queries
                and entry["accepted"]
                and entry["record"]["target"] in by_name
            ]
        done = await submit(
            client, _settings(args), taken, queries, journal, revise=args.revise
        )
        print(f"Spent ${client.usage.cost:.2f} in {client.usage.requests} requests")
    changed = [t for t in taken if done.get(t.id) != before.get(t.id)]
    accepted = sum(done[target.id]["accepted"] for target in changed)
    print(f"Accepted {accepted} of {len(changed)} submitted queries")


async def _zulip(args: argparse.Namespace) -> None:
    corpus = _corpus(args)
    site = zulip.ZulipSite.from_zuliprc(args.zuliprc)
    cache = args.out / "zulip-threads.json"
    if cache.exists():
        threads = json.loads(cache.read_text(encoding="utf-8"))
    else:
        threads = zulip.fetch_threads(site, args.channel, args.max_topics)
        _write_json(cache, threads)
    print(f"Using {len(threads)} threads from {args.channel!r}")
    journal = args.out / "zulip-journal.jsonl"
    async with OpenRouterClient(OpenRouterSettings.from_env()) as client:
        if args.queries is None:
            await zulip.extract(client, _settings(args), threads, corpus, journal)
        else:
            lines = args.queries.read_text(encoding="utf-8").splitlines()
            items = (json.loads(line) for line in lines if line.strip())
            written = {str(item["id"]): item for item in items}
            done = await zulip.submit(
                client, _settings(args), threads, written, corpus, journal
            )
            accepted = sum(done[f"question-zulip-{key}"]["accepted"] for key in written)
            print(f"Accepted {accepted} of {len(written)} submitted items")
        print(f"Spent ${client.usage.cost:.2f} in {client.usage.requests} requests")


def _thread_fits(record: QueryRecord, spec: MixSpec, corpus: Corpus) -> bool:
    """Whether a thread query belongs in the balanced shape.

    It must come from a discussion thread, its best answer must lie in a
    library of the shape, and an answer of grade 2 or 3 must be established.
    """
    return (
        record.source == "zulip"
        and record.library in spec.library_counts
        and any(
            grade >= 2 and corpus.is_established(name)
            for name, grade in record.judgments.items()
        )
    )


def _build(args: argparse.Namespace) -> None:
    spec = _spec(args)
    corpus = _corpus(args)
    named, written = _split_targets(corpus, spec)
    index = names.suffix_index(corpus.names)
    rng = random.Random(spec.seed)
    name_records = {
        target.id: {
            "id": target.id,
            "accepted": True,
            "record": names.name_query(target, index, corpus.names, rng).to_json(),
        }
        for target in named
    }
    allowed = corpus.is_established
    records = assemble.select(named, name_records, spec, allowed)
    records += assemble.select(
        written, read_journal(args.out / "journal.jsonl"), spec, allowed
    )
    if spec.type_totals is None:
        records += zulip.select(
            read_journal(args.out / "zulip-journal.jsonl"), spec.per_type
        )
    else:
        own, contributed = (
            [record for record in group if _thread_fits(record, spec, corpus)]
            for group in _threads(args.out)
        )
        records += combine.thread_records(own, contributed, BUCKET_SIZE)
    records = assemble.assign_splits(records, spec)
    _write_mix(args.out, records, corpus.revision)


def _write_mix(out: Path, records: list[QueryRecord], revision: str) -> None:
    """Write the queries, both collections and the summary of a mix."""
    write_records(out / "queries.jsonl", records)
    for split in assemble.SPLITS:
        _write_json(
            out / f"collection.{split}.json",
            assemble.to_collection(records, revision, split),
        )
    (out / "summary.md").write_text(
        f"Corpus: `{revision}`\n\n" + assemble.summary_table(records),
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} queries to {out}")
    print(assemble.summary_table(records))


async def _contribute(args: argparse.Namespace) -> None:
    corpus = _corpus(args)
    items = [item for path in args.queries for item in combine.read_contributed(path)]
    settings = GenerationSettings(
        writer_model="", judge_model=args.judge_model, budget_usd=args.budget
    )
    async with OpenRouterClient(OpenRouterSettings.from_env()) as client:
        done = await combine.grade(
            client, settings, items, corpus, args.out / "contributed-journal.jsonl"
        )
        print(f"Spent ${client.usage.cost:.2f} in {client.usage.requests} requests")
    accepted = sum(item.id in done and done[item.id]["accepted"] for item in items)
    print(f"Accepted {accepted} of {len(items)} contributed queries")


def _fitting(
    names: dict[str, set[str]], spec: MixSpec, corpus: Corpus
) -> dict[str, set[str]]:
    """Keep the pooled names that could be targets of the shape.

    A candidate outside the shape's libraries, or one that is not
    established, is a declaration that some engines do not index. Labelling
    it would reward an engine for what it indexes, not for how it searches.
    """

    def fits(name: str) -> bool:
        module = corpus.modules.get(name)
        placed = library_and_area(module) if module else None
        return (
            placed is not None
            and placed[0] in spec.library_counts
            and corpus.is_established(name)
        )

    return {
        key: {name for name in pooled if fits(name)} for key, pooled in names.items()
    }


def _pool(args: argparse.Namespace) -> None:
    path = args.out / "queries.jsonl"
    records = read_records(path)
    if args.grades is None:
        results = {
            engine: engines.read_results(args.out / "runs" / f"{engine}.jsonl")
            for engine in args.engine
        }
        names = pool.pooled_names(records, results, args.limit, args.until_answer)
        if args.shape == "balanced":
            names = _fitting(names, _spec(args), _corpus(args))
        wanted = set().union(*names.values(), *(r.judgments for r in records))
        statements = read_statements(args.corpus, wanted)
        pooled = pool.tasks(records, names, statements)
        args.to.parent.mkdir(parents=True, exist_ok=True)
        with args.to.open("w", encoding="utf-8") as file:
            for task in pooled:
                file.write(json.dumps(task, ensure_ascii=False) + "\n")
        print(f"Wrote {len(pooled)} judging tasks to {args.to}")
        return
    lines = args.grades.read_text(encoding="utf-8").splitlines()
    items = (json.loads(line) for line in lines if line.strip())
    graded = {item["id"]: item["relevant"] for item in items}
    updated = pool.apply(records, graded, args.judge)
    write_records(path, updated)
    revision = _corpus(args).revision
    for split in assemble.SPLITS:
        _write_json(
            args.out / f"collection.{split}.json",
            assemble.to_collection(updated, revision, split),
        )
    added = sum(len(r.provenance.get("pooled", [])) for r in updated)
    changed = sum("pooled" in r.provenance for r in updated)
    print(f"Added {added} answers to {changed} queries")


def _run(args: argparse.Namespace) -> None:
    records = [
        record
        for record in read_records(args.out / "queries.jsonl")
        if args.split == "all" or record.split == args.split
    ]
    engine = engines.ENGINES[args.engine]()
    path = args.out / "runs" / f"{args.engine}.jsonl"
    results = engines.run(engine, records, path, limit=args.limit)
    failed = sum(results[record.id]["status"] != "ok" for record in records)
    print(f"{args.engine}: {len(records)} queries, {failed} failed; journal {path}")


def _score(args: argparse.Namespace) -> None:
    records = [
        record
        for record in read_records(args.out / "queries.jsonl")
        if args.library is None or record.library == args.library
    ]
    reference = _read_profile(args.weights, args.group)
    weights = (
        {form: entry["share_of_searches"] for form, entry in reference["forms"].items()}
        if reference is not None
        else None
    )
    for engine in args.engine:
        results = engines.read_results(args.out / "runs" / f"{engine}.jsonl")
        limit = min((result["limit"] for result in results.values()), default=10)
        report = score.score(
            records, results, engine, split=args.split, limit=limit, weights=weights
        )
        name = ".".join(filter(None, [engine, args.split, args.library]))
        _write_json(args.out / "scores" / f"{name}.json", report)
        print(score.render(report))


def _log_profiles() -> dict[str, Any]:
    """Profile the search log, overall and by source. Runs where the log is."""
    from lean_explore_bench.querylog.load import load_query_log

    frame, report = load_query_log()
    frame["normal"] = frame["query"].map(lambda query: " ".join(query.lower().split()))
    groups = {"all": frame}
    for source in sorted(frame["source"].unique()):
        groups[str(source)] = frame[frame["source"] == source]
    profiles = {}
    for name, group in groups.items():
        distinct = group.groupby("normal").agg(
            query=("query", "first"), searches=("query", "size")
        )
        profiles[name] = profile.profile(
            list(distinct["query"]), [float(n) for n in distinct["searches"]]
        )
    return {
        "rows": report.rows_loaded,
        "first_day": str(frame["collected_on"].min()),
        "last_day": str(frame["collected_on"].max()),
        "profiles": profiles,
    }


def _profile(args: argparse.Namespace) -> None:
    if args.log:
        value = _log_profiles()
    else:
        queries = profile.read_queries(args.queries)
        value = {"profiles": {"all": profile.profile(queries, min_count=1)}}
    _write_json(args.to, value)
    print(f"Wrote {args.to}")


def _compare(args: argparse.Namespace) -> None:
    reference = _read_profile(args.reference, args.group)
    candidate = _read_profile(args.candidate, "all")
    assert reference is not None and candidate is not None
    print(profile.render(profile.compare(reference, candidate)))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="leb-mix", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    def add(name: str, summary: str) -> argparse.ArgumentParser:
        command = commands.add_parser(name, help=summary)
        command.add_argument(
            "--out", type=Path, required=True, help="directory of the mix"
        )
        return command

    def add_models(command: argparse.ArgumentParser) -> None:
        command.add_argument("--corpus", type=Path, required=True)
        command.add_argument("--writer-model", default=DEFAULT_WRITER)
        command.add_argument("--judge-model", default=DEFAULT_JUDGE)
        command.add_argument("--budget", type=float, default=25.0, help="USD limit")

    def add_established(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--established",
            type=Path,
            help="older lean_explore.db; only declarations it holds are targets",
        )

    def add_shape(command: argparse.ArgumentParser) -> None:
        add_established(command)
        command.add_argument(
            "--shape",
            choices=["uniform", "balanced"],
            default="uniform",
            help="equal forms, or four buckets of 800 queries in Mathlib",
        )

    def add_group(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--group", default="all", help="group of the profile file to use"
        )

    command = add("generate", "write and judge queries for sampled declarations")
    add_models(command)
    command.add_argument("--style", type=Path, help="profile of real searches")
    add_group(command)
    add_shape(command)
    command = add("tasks", "export the queries still to write, for another writer")
    add_models(command)
    command.add_argument("--style", type=Path, help="profile of real searches")
    add_group(command)
    add_shape(command)
    command.add_argument("--to", type=Path, required=True, help="output JSON Lines")
    command = add("submit", "check and judge queries written for exported tasks")
    add_models(command)
    command.add_argument("--style", type=Path, help="profile of real searches")
    add_group(command)
    add_shape(command)
    command.add_argument("--queries", type=Path, required=True, help="JSON Lines")
    command.add_argument(
        "--revise",
        action="store_true",
        help="also replace accepted queries by submitted ones that differ",
    )
    command = add("zulip", "turn Lean Zulip questions into queries")
    add_models(command)
    add_group(command)
    command.add_argument("--zuliprc", type=Path, default=Path.home() / ".zuliprc")
    command.add_argument("--channel", default="Is there code for X?")
    command.add_argument("--max-topics", type=int, default=600)
    command.add_argument(
        "--queries", type=Path, help="items extracted elsewhere, as JSON Lines"
    )
    command = add("build", "assemble, split and export the mix")
    command.add_argument("--corpus", type=Path, required=True)
    add_shape(command)
    command = add("contribute", "grade contributed queries for the mix")
    command.add_argument("--corpus", type=Path, required=True)
    command.add_argument("--queries", type=Path, nargs="+", required=True)
    command.add_argument("--judge-model", default=DEFAULT_JUDGE)
    command.add_argument("--budget", type=float, default=10.0, help="USD limit")
    command = add("pool", "pool engine results for judging, or add the grades")
    command.add_argument("--corpus", type=Path, required=True)
    add_shape(command)
    command.add_argument("--engine", nargs="+", default=sorted(engines.ENGINES))
    command.add_argument("--limit", type=int, default=10, help="results per engine")
    command.add_argument(
        "--until-answer",
        action="store_true",
        help="pool each engine's results only up to its first labelled answer",
    )
    command.add_argument("--to", type=Path, help="write judging tasks here")
    command.add_argument("--grades", type=Path, help="grades to add, as JSON Lines")
    command.add_argument("--judge", default="unknown", help="who graded the pools")
    command = add("run", "send every query to a search engine")
    command.add_argument("--engine", choices=sorted(engines.ENGINES), required=True)
    command.add_argument("--limit", type=int, default=10, help="results per query")
    command.add_argument("--split", choices=[*assemble.SPLITS, "all"], default="all")
    command = add("score", "score engine runs by bucket and library")
    command.add_argument("--engine", nargs="+", required=True)
    command.add_argument("--split", choices=[*assemble.SPLITS, "all"], default="all")
    command.add_argument("--weights", type=Path, help="profile of real searches")
    command.add_argument("--library", help="score only targets in this library")
    add_group(command)
    command = commands.add_parser("profile", help="profile queries by form and style")
    source = command.add_mutually_exclusive_group(required=True)
    source.add_argument("--log", action="store_true", help="profile the search log")
    source.add_argument("--queries", type=Path, help="profile a file of queries")
    command.add_argument("--to", type=Path, required=True, help="output JSON file")
    command = commands.add_parser("compare", help="compare a profile with a reference")
    command.add_argument("--reference", type=Path, required=True)
    command.add_argument("--candidate", type=Path, required=True)
    add_group(command)
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the ``leb-mix`` command line."""
    args = _parser().parse_args(argv)
    if args.command == "generate":
        asyncio.run(_generate(args))
    elif args.command == "tasks":
        _tasks(args)
    elif args.command == "submit":
        asyncio.run(_submit(args))
    elif args.command == "zulip":
        asyncio.run(_zulip(args))
    elif args.command == "build":
        _build(args)
    elif args.command == "contribute":
        asyncio.run(_contribute(args))
    elif args.command == "pool":
        _pool(args)
    elif args.command == "run":
        _run(args)
    elif args.command == "score":
        _score(args)
    elif args.command == "profile":
        _profile(args)
    else:
        _compare(args)
