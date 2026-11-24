"""Run local query profiling and offline retrieval evaluations."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import platform
from pathlib import Path

from leanexplore_benchmark import __version__
from leanexplore_benchmark.evaluate import compare, evaluate
from leanexplore_benchmark.profile import profile
from leanexplore_benchmark.querylog import load_export
from leanexplore_benchmark.report import render
from leanexplore_benchmark.workflow import add_commands, dispatch


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _audit(args: argparse.Namespace) -> None:
    exported = load_export(args.input, args.since)
    cells = profile(exported.rows, args.min_count)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "counts.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["view", "dimension", "source", "category", "count"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(cells)
    _write_json(args.out / "counts.json", cells)
    (args.out / "index.html").write_text(
        render(cells, "Real queries: evidence and limits", exported.sha256),
        encoding="utf-8",
        newline="\n",
    )
    source_dir = Path(__file__).parent
    manifest = {
        "version": __version__,
        "python": platform.python_version(),
        "input_sha256": exported.sha256,
        "since": args.since.isoformat() if args.since else None,
        "min_count": args.min_count,
        "rounding_base": 10,
        "normalization": "NFC_whitespace_case_preserving",
        "intent_and_domain": "unvalidated_English_Lean_rule_cues",
        "actor_identity": "unknown_for_all_rows",
        "retrieval_evaluated": False,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(source_dir.glob("*.py"))
        },
    }
    _write_json(args.out / "manifest.json", manifest)
    print(f"Audit written to {args.out / 'index.html'}")


def main(argv: list[str] | None = None) -> None:
    """Dispatch commands; no network or external model calls are performed."""
    parser = argparse.ArgumentParser(prog="leq-bench")
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser(
        "build", help="rebuild the complete offline report"
    )
    build_parser.add_argument("--input", type=Path, required=True)
    build_parser.add_argument("--out", type=Path, default=Path("reports/latest"))
    audit = commands.add_parser("audit", help="profile a source-keyed JSON export")
    audit.add_argument("--input", type=Path, required=True)
    audit.add_argument("--out", type=Path, required=True)
    audit.add_argument("--since", type=dt.date.fromisoformat)
    audit.add_argument("--min-count", type=int, default=10)
    review = commands.add_parser("review", help="review a stratified sample locally")
    review.add_argument("--input", type=Path, required=True)
    review.add_argument("--out", type=Path, required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--size", type=int, default=400)
    review.add_argument("--seed", type=int, default=42)
    review.add_argument("--port", type=int, default=8051)
    for name in ("evaluate", "compare"):
        command = commands.add_parser(name)
        command.add_argument("--collection", type=Path, required=True)
        command.add_argument("--run", type=Path, required=True)
        command.add_argument("--out", type=Path, required=True)
        command.add_argument(
            "--cutoffs", type=int, nargs="+", default=[1, 5, 10, 20, 50, 100]
        )
        if name == "compare":
            command.add_argument("--baseline", type=Path, required=True)
            command.add_argument("--metric", default="ndcg@10")
            command.add_argument(
                "--track", choices=["all", "human", "agent", "unknown"], default="all"
            )
            command.add_argument("--seed", type=int, default=42)
            command.add_argument("--samples", type=int, default=10000)
    add_commands(commands)
    args = parser.parse_args(argv)
    if dispatch(args):
        return
    if args.command == "build":
        from leanexplore_benchmark.build import build

        build(args.input, args.out)
        return
    if args.command == "audit":
        _audit(args)
        return
    if args.command == "review":
        from leanexplore_benchmark.review import make_server

        server = make_server(
            load_export(args.input),
            args.out,
            args.reviewer,
            args.size,
            args.seed,
            args.port,
        )
        print(f"Local review: http://127.0.0.1:{server.server_port} (Ctrl-C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return
    collection = json.loads(args.collection.read_text(encoding="utf-8"))
    run = json.loads(args.run.read_text(encoding="utf-8"))
    result = evaluate(collection, run, tuple(args.cutoffs))
    if args.command == "compare":
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        result = compare(
            evaluate(collection, baseline, tuple(args.cutoffs)),
            result,
            args.metric,
            args.track,
            args.seed,
            args.samples,
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    _write_json(args.out, result)
    print(f"Evaluation written to {args.out}")


if __name__ == "__main__":
    main()
