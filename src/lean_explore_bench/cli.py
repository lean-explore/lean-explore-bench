"""``leb-querylog``: analyse the LeanExplore query log.

Subcommands:

- ``report --out DIR`` writes aggregate charts and CSV tables that passed the
  release gate. Safe to copy off the server.
- ``explore`` serves a page with individual queries on ``127.0.0.1`` from
  memory, writing nothing to disk. View it through an SSH tunnel, e.g.
  ``ssh -L 8050:localhost:8050 xtx``.

Both read the query log (see :mod:`lean_explore_bench.querylog.load` for
paths and the key).
"""

import argparse
import datetime
import http.server
import sys
from pathlib import Path

import pandas as pd

from lean_explore_bench.analysis.release import MIN_CELL_COUNT
from lean_explore_bench.analysis.stats import PreparedLog, prepare
from lean_explore_bench.analysis.views import (
    explore_sections,
    release_sections,
    render_page,
)
from lean_explore_bench.querylog.load import load_query_log


def _load(args: argparse.Namespace) -> pd.DataFrame:
    """Load the log, exiting with a message if there is nothing to analyse."""
    frame, report = load_query_log(args.db, since=args.since)
    print(
        f"Read {report.rows_read:,} rows; decrypted {report.rows_loaded:,}; "
        f"{report.rows_undecryptable:,} could not be decrypted.",
        file=sys.stderr,
    )
    if frame.empty:
        raise SystemExit("No queries to analyse (check --db and --since).")
    return frame


def _report(args: argparse.Namespace) -> None:
    prepared = prepare(_load(args), threshold=args.threshold, seed=args.seed)
    sections = release_sections(prepared, min_count=args.min_count, seed=args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for section in sections:
        if section.table is not None and section.table_name:
            section.table.to_csv(args.out / f"{section.table_name}.csv", index=False)
    page = render_page(sections, "LeanExplore query log: aggregate report")
    (args.out / "index.html").write_text(page, encoding="utf-8")
    print(f"Wrote {args.out / 'index.html'}", file=sys.stderr)


def _points(prepared: PreparedLog, args: argparse.Namespace) -> pd.DataFrame | None:
    if not args.embed:
        return None
    from lean_explore_bench.analysis.embed import (
        cluster_hdbscan,
        embed_queries,
        project_2d,
        reduce_for_clustering,
    )

    distinct = prepared.distinct
    print(f"Embedding {len(distinct):,} distinct queries…", file=sys.stderr)
    embeddings = embed_queries(distinct["query"].tolist(), device=args.device)
    xy = project_2d(embeddings, method=args.projection, seed=args.seed)
    return distinct.assign(
        x=xy[:, 0],
        y=xy[:, 1],
        cluster=cluster_hdbscan(
            reduce_for_clustering(embeddings, seed=args.seed),
            min_cluster_size=args.min_cluster_size,
        ),
    )


def explore_page(args: argparse.Namespace) -> bytes:
    """Build the server-only explorer page in memory.

    Args:
        args: Parsed ``explore`` arguments.

    Returns:
        The page as UTF-8 bytes.
    """
    prepared = prepare(_load(args), threshold=args.threshold, seed=args.seed)
    sections = explore_sections(prepared, _points(prepared, args), seed=args.seed)
    title = "LeanExplore query log: explorer (server only)"
    return render_page(sections, title).encode("utf-8")


def page_server(page: bytes, port: int) -> http.server.ThreadingHTTPServer:
    """Create a server for one in-memory page on 127.0.0.1.

    Only ``/`` and ``/index.html`` are served, with ``Cache-Control:
    no-store``; every other path is a 404. Nothing is written to disk.

    Args:
        page: The page to serve.
        port: Port to listen on; ``0`` picks a free one.

    Returns:
        The server, not yet serving.
    """

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server API)
            if self.path not in ("/", "/index.html"):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    return http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)


def _explore(args: argparse.Namespace) -> None:
    server = page_server(explore_page(args), args.port)
    port = server.server_address[1]
    print(
        f"Serving on http://127.0.0.1:{port} (Ctrl-C to stop). "
        f"From your laptop: ssh -L {port}:localhost:{port} <server>",
        file=sys.stderr,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        The parser.
    """
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", type=Path, help="query log SQLite database")
    common.add_argument(
        "--since",
        type=datetime.date.fromisoformat,
        help="only rows collected on or after this UTC day (YYYY-MM-DD)",
    )
    common.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="near-duplicate Jaccard threshold within a source and day",
    )
    common.add_argument("--seed", type=int, default=0)

    parser = argparse.ArgumentParser(prog="leb-querylog", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    report = commands.add_parser(
        "report", parents=[common], help="write gated aggregate charts and tables"
    )
    report.add_argument("--out", type=Path, required=True)
    report.add_argument("--min-count", type=int, default=MIN_CELL_COUNT)
    report.set_defaults(handler=_report)

    explore = commands.add_parser(
        "explore", parents=[common], help="serve a server-only page from memory"
    )
    explore.add_argument("--port", type=int, default=8050)
    explore.add_argument(
        "--embed", action="store_true", help="add a query map (needs the embed extra)"
    )
    explore.add_argument("--projection", choices=["umap", "pca"], default="umap")
    explore.add_argument("--device", help="torch device for embedding, e.g. cuda:7")
    explore.add_argument("--min-cluster-size", type=int, default=15)
    explore.set_defaults(handler=_explore)
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the command line.

    Args:
        argv: Arguments; defaults to ``sys.argv[1:]``.
    """
    args = build_parser().parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
