"""CLI operations for external benchmark preparation and review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from leanexplore_benchmark.collection import adapt_run, prepare_collection
from leanexplore_benchmark.corpus import Corpus
from leanexplore_benchmark.pooling import export_pool, validate_reviews


def add_commands(commands: Any) -> None:
    """Register dataset-independent workflow commands."""
    prepare = commands.add_parser("prepare", help="validate cases and prepare a split")
    prepare.add_argument("--cases", type=Path, required=True)
    prepare.add_argument("--corpus", type=Path, required=True)
    prepare.add_argument(
        "--split", choices=["train", "development", "test"], required=True
    )
    prepare.add_argument("--out", type=Path, required=True)
    run = commands.add_parser("adapt-run", help="validate external observations")
    run.add_argument("--observations", type=Path, required=True)
    run.add_argument("--collection", type=Path, required=True)
    run.add_argument("--corpus", type=Path, required=True)
    run.add_argument("--name", required=True)
    run.add_argument("--max-k", type=int, required=True)
    run.add_argument("--out", type=Path, required=True)
    pool = commands.add_parser("pool", help="export a development review packet")
    pool.add_argument("--prepared", type=Path, required=True)
    pool.add_argument("--corpus", type=Path, required=True)
    pool.add_argument("--run", type=Path, action="append", required=True)
    pool.add_argument("--depth", type=int, required=True)
    pool.add_argument("--seed", type=int, default=42)
    pool.add_argument("--out", type=Path, required=True)
    reviews = commands.add_parser(
        "check-reviews", help="validate an assessor submission"
    )
    reviews.add_argument("--packet", type=Path, required=True)
    reviews.add_argument("--submission", type=Path, required=True)
    reviews.add_argument("--out", type=Path, required=True)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Invalid benchmark JSON") from None
    if not isinstance(value, dict):
        raise ValueError("Benchmark input must be an object")
    return value


def _write(directory: Path, files: dict[str, object]) -> None:
    target = directory.resolve()
    if any((parent / ".git").exists() for parent in (target, *target.parents)):
        raise ValueError("Benchmark outputs must be outside Git checkouts")
    encoded = {
        name: json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        for name, value in files.items()
    }
    target.mkdir(parents=True, exist_ok=False)
    for name, content in encoded.items():
        (target / name).write_text(content, encoding="utf-8", newline="\n")


def dispatch(args: argparse.Namespace) -> bool:
    """Write validated artifacts externally; preserve existing outputs."""
    if args.command == "prepare":
        prepared = prepare_collection(
            _load(args.cases), Corpus.from_json(_load(args.corpus)), args.split
        )
        _write(
            args.out,
            {
                "prepared.json": prepared,
                "collection.json": prepared["collection"],
                "split-audit.json": prepared["split_audit"],
            },
        )
    elif args.command == "adapt-run":
        observations = _load(args.observations)
        corpus = Corpus.from_json(_load(args.corpus))
        if observations.get("corpus_revision") != corpus.revision:
            raise ValueError("Observation and corpus revisions differ")
        rows = observations.get("records")
        if not isinstance(rows, list):
            raise ValueError("Observations require records")
        result = adapt_run(rows, _load(args.collection), corpus, args.name, args.max_k)
        _write(args.out, {"run.json": result})
    elif args.command == "pool":
        pool = export_pool(
            _load(args.prepared),
            Corpus.from_json(_load(args.corpus)),
            [_load(path) for path in args.run],
            args.depth,
            args.seed,
        )
        _write(
            args.out,
            {
                "packet.json": pool["packet"],
                "pool-audit.json": {
                    key: value for key, value in pool.items() if key != "packet"
                },
            },
        )
    elif args.command == "check-reviews":
        result = validate_reviews(_load(args.packet), _load(args.submission))
        _write(args.out, {"submission.json": result})
    else:
        return False
    print("Benchmark artifacts written.")
    return True
