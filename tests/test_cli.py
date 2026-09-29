import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lean_explore_bench import cli


def test_report_writes_only_gated_outputs(
    tmp_path: Path, encrypted_log: Path, shaped_log: pd.DataFrame
) -> None:
    out = tmp_path / "report"
    cli.main(["report", "--db", str(encrypted_log), "--out", str(out)])
    assert {path.suffix for path in out.iterdir()} == {".html", ".csv"}
    page = (out / "index.html").read_text(encoding="utf-8")
    assert not any(query in page for query in shaped_log["query"])


def test_explore_page_without_embeddings(encrypted_log: Path) -> None:
    args = cli.build_parser().parse_args(["explore", "--db", str(encrypted_log)])
    page = cli.explore_page(args).decode("utf-8")
    assert "Server only" in page and "Query map" not in page


def test_explore_page_with_embeddings(
    encrypted_log: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lean_explore_bench.analysis import embed

    monkeypatch.setattr(embed, "embed_queries", lambda texts, device=None: _grid(texts))
    monkeypatch.setattr(embed, "project_2d", lambda e, method, seed: e[:, :2])
    monkeypatch.setattr(embed, "reduce_for_clustering", lambda e, seed: e)
    monkeypatch.setattr(
        embed, "cluster_hdbscan", lambda e, min_cluster_size: e[:, 0] > 0
    )
    argv = ["explore", "--db", str(encrypted_log), "--embed", "--projection", "pca"]
    page = cli.explore_page(cli.build_parser().parse_args(argv)).decode("utf-8")
    assert "Query map by category" in page and "Topic clusters" in page


def _grid(texts: list[str]) -> np.ndarray:
    return np.array([[i % 2, i] for i in range(len(texts))], dtype=float)


def test_page_server_serves_the_page_and_nothing_else() -> None:
    server = cli.page_server(b"<p>hi</p>", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(base + "/") as response:
            assert response.read() == b"<p>hi</p>"
            assert response.headers["Cache-Control"] == "no-store"
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(base + "/other")
        assert error.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_parser_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])
    args = cli.build_parser().parse_args(
        ["report", "--out", "x", "--since", "2026-09-01"]
    )
    assert args.since == pd.Timestamp("2026-09-01").date()


def test_explore_command_serves_until_interrupted(
    encrypted_log: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeServer:
        server_address = ("127.0.0.1", 9999)
        closed = False

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            FakeServer.closed = True

    monkeypatch.setattr(cli, "page_server", lambda page, port: FakeServer())
    cli.main(["explore", "--db", str(encrypted_log)])
    assert FakeServer.closed
    assert "http://127.0.0.1:9999" in capsys.readouterr().err


def test_empty_selection_exits_with_a_message(encrypted_log: Path) -> None:
    argv = ["report", "--db", str(encrypted_log), "--out", "unused"]
    with pytest.raises(SystemExit, match="No queries to analyse"):
        cli.main([*argv, "--since", "2099-01-01"])
