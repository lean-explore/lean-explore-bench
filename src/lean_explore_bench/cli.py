"""Command line for running and scoring search engines on the benchmark.

``DIR`` is a directory that holds the benchmark: the published dataset, or a
build directory. Engine results are read from and written to ``DIR/runs``.

    leb run   DIR --engine leanexplore
    leb run   DIR --engine bm25 --corpus lean_explore.db
    leb score DIR --engine leanexplore --split test
"""

import argparse
import json
from pathlib import Path
from typing import Any

from lean_explore_bench import dataset, engines, score
from lean_explore_bench.record import SPLITS


def write_json(path: Path, value: Any) -> None:
    """Write ``value`` as indented JSON, creating the directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_profile(path: Path | None, group: str) -> dict[str, Any] | None:
    """Read one group of a profile file; a bare profile has no groups."""
    if path is None:
        return None
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if "profiles" in value:
        selected: dict[str, Any] = value["profiles"][group]
        return selected
    return value


def _engine(args: argparse.Namespace) -> engines.Engine:
    """Build the engine named on the command line."""
    if args.engine in engines.ENGINES:
        return engines.ENGINES[args.engine]()
    if args.corpus is None:
        raise SystemExit(f"{args.engine} runs on a corpus snapshot: pass --corpus")
    from lean_explore_bench.engines.bm25 import BM25

    return BM25(corpus=args.corpus)


def _run(args: argparse.Namespace) -> None:
    records = [
        record
        for record in dataset.load_queries(args.directory)
        if args.split == "all" or record.split == args.split
    ]
    engine = _engine(args)
    path = args.directory / "runs" / f"{args.engine}.jsonl"
    results = engines.run(engine, records, path, limit=args.limit)
    failed = sum(results[record.id]["status"] != "ok" for record in records)
    print(f"{args.engine}: {len(records)} queries, {failed} failed; journal {path}")


def _score(args: argparse.Namespace) -> None:
    records = [
        record
        for record in dataset.load_queries(args.directory)
        if args.library is None or record.library == args.library
    ]
    reference = read_profile(args.weights, args.group)
    weights = (
        {form: entry["share_of_searches"] for form, entry in reference["forms"].items()}
        if reference is not None
        else None
    )
    for engine in args.engine:
        results = engines.read_results(args.directory / "runs" / f"{engine}.jsonl")
        limit = min(
            (result.get("limit", 10) for result in results.values()), default=10
        )
        report = score.score(
            records, results, engine, split=args.split, limit=limit, weights=weights
        )
        name = ".".join(filter(None, [engine, args.split, args.library]))
        write_json(args.directory / "scores" / f"{name}.json", report)
        print(score.render(report))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="leb", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    splits = [*SPLITS, "all"]
    command = commands.add_parser("run", help="send every query to a search engine")
    command.add_argument("directory", type=Path, help="directory of the benchmark")
    names = sorted([*engines.ENGINES, *engines.LOCAL_ENGINES])
    command.add_argument("--engine", choices=names, required=True)
    command.add_argument("--corpus", type=Path, help="corpus snapshot, for bm25")
    command.add_argument("--limit", type=int, default=10, help="results per query")
    command.add_argument("--split", choices=splits, default="all")
    command = commands.add_parser("score", help="score engine runs by bucket")
    command.add_argument("directory", type=Path, help="directory of the benchmark")
    command.add_argument("--engine", nargs="+", required=True)
    command.add_argument("--split", choices=splits, default="all")
    command.add_argument("--weights", type=Path, help="profile of real searches")
    command.add_argument("--library", help="score only targets in this library")
    command.add_argument(
        "--group", default="all", help="group of the profile file to use"
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the ``leb`` command line."""
    args = _parser().parse_args(argv)
    if args.command == "run":
        _run(args)
    else:
        _score(args)
