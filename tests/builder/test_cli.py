import json
from pathlib import Path
from typing import Any

import pytest
from helpers import scripted_client, system_of, user_of

from lean_explore_bench import cli as user_cli
from lean_explore_bench import engines
from lean_explore_bench.builder import cli, prompts, zulip
from lean_explore_bench.builder.generate import read_journal
from lean_explore_bench.builder.llm import OpenRouterSettings
from lean_explore_bench.record import read_records
from lean_explore_bench.spec import MixSpec

SMALL = MixSpec(
    library_counts={"mathlib": 3, "cslib": 1},
    query_types=("name", "prose"),
    reserve=1.0,
)
GOOD = "sum of two numbers does not depend on the order in case"


@pytest.fixture
def small_mix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "MixSpec", lambda: SMALL)
    monkeypatch.setattr(
        OpenRouterSettings,
        "from_env",
        classmethod(lambda cls: OpenRouterSettings(api_key="k")),
    )


def _use_model(monkeypatch: pytest.MonkeyPatch, respond: Any) -> None:
    monkeypatch.setattr(
        cli, "OpenRouterClient", lambda _settings: scripted_client(respond)
    )


def _writer(body: dict[str, Any]) -> str:
    if system_of(body) == prompts.JUDGE_SYSTEM:
        return json.dumps({"grade": 3, "specific": True})
    if system_of(body) == zulip.EXTRACT_SYSTEM:
        return json.dumps(
            {
                "is_search": True,
                "query": "lemma that a + b = b + a",
                "answers": [{"name": "Demo.Algebra.add_comm_3", "grade": 3}],
            }
        )
    name = user_of(body).split("\n", 1)[0].removeprefix("Name: ")
    area, number = name.split(".")[1], name.rsplit("_", 1)[-1]
    return json.dumps({"query": f"{GOOD} {area} {number}"})


def test_generate_build_run_and_score(
    small_mix: None,
    corpus_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "mix"
    corpus = ["--corpus", str(corpus_path), "--out", str(out)]

    # The first informal query of every round is rejected, so reserves are used.
    state = {"writes": 0}

    def flaky(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.WRITER_SYSTEM:
            state["writes"] += 1
            if state["writes"] <= 6:
                return json.dumps({"query": "bad"})
        return _writer(body)

    _use_model(monkeypatch, flaky)
    cli.main(["generate", *corpus, "--budget", "5"])
    printed = capsys.readouterr().out
    assert "Writing 4 queries" in printed and "Writing 2 queries" in printed
    assert "Accepted 4 queries; 0 cells still short" in printed

    class Site(zulip.ZulipSite):
        pass

    monkeypatch.setattr(
        zulip.ZulipSite,
        "from_zuliprc",
        classmethod(lambda cls, path: Site("u", "e", "k")),
    )
    thread = {
        "topic": "t",
        "url": "https://z.example/t",
        "first_message_id": 42,
        "messages": [
            {"asker": True, "content": "is there a lemma?"},
            {"asker": False, "content": "docs#Demo.Algebra.add_comm_3"},
        ],
    }
    fetched: list[int] = []

    def fetch_threads(site: zulip.ZulipSite, channel: str, limit: int) -> list[Any]:
        fetched.append(limit)
        return [thread]

    monkeypatch.setattr(zulip, "fetch_threads", fetch_threads)
    _use_model(monkeypatch, _writer)
    cli.main(["zulip", *corpus, "--max-topics", "7"])
    cli.main(["zulip", *corpus])
    assert fetched == [7]
    assert "Using 1 threads" in capsys.readouterr().out

    cli.main(["build", *corpus])
    records = read_records(out / "queries.jsonl")
    counts: dict[str, int] = {}
    for record in records:
        counts[record.query_type] = counts.get(record.query_type, 0) + 1
    assert counts == {"name": 4, "prose": 4, "question": 1}
    assert {record.split for record in records} <= {"development", "test"}
    test_collection = json.loads((out / "collection.test.json").read_text())
    development = json.loads((out / "collection.development.json").read_text())
    assert len(test_collection["queries"]) + len(development["queries"]) == 9
    assert test_collection["corpus_revision"].startswith("leanexplore:snapshot-1:")
    summary = (out / "summary.md").read_text()
    assert "| question |" in summary and "leanexplore:snapshot-1:" in summary
    assert "Wrote 9 queries" in capsys.readouterr().out

    class Oracle(engines.Engine):
        def search(self, query: str, limit: int) -> list[str]:
            by_query = {record.query: list(record.judgments) for record in records}
            return by_query[query]

    monkeypatch.setitem(
        engines.ENGINES,
        "leanexplore",
        lambda: Oracle(name="oracle", interval_seconds=0.0),
    )
    run = ["run", str(out), "--engine", "leanexplore", "--limit", "5"]
    user_cli.main([*run, "--split", "development"])
    partial = capsys.readouterr().out
    assert "0 failed" in partial and "leanexplore: 9 queries" not in partial
    user_cli.main(run)
    assert "leanexplore: 9 queries, 0 failed" in capsys.readouterr().out

    user_cli.main(["score", str(out), "--engine", "leanexplore", "--split", "all"])
    printed = capsys.readouterr().out
    assert "### leanexplore (all queries)" in printed
    assert "success@5" in printed
    assert "| **All** | 9 | 1.000 | 1.000 | 1.000 | 1.000 |" in printed
    report = json.loads((out / "scores" / "leanexplore.all.json").read_text())
    assert report["overall"]["success@1"] == 1.0
    assert report["traffic_weighted"] is None

    mix_profile = tmp_path / "mix-profile.json"
    cli.main(
        ["profile", "--queries", str(out / "queries.jsonl"), "--to", str(mix_profile)]
    )
    profiled = json.loads(mix_profile.read_text())["profiles"]["all"]
    assert profiled["distinct"] == 9 and "prose" in profiled["forms"]
    bare = tmp_path / "bare-profile.json"
    bare.write_text(json.dumps(profiled))
    capsys.readouterr()
    cli.main(["compare", "--reference", str(bare), "--candidate", str(mix_profile)])
    compared = capsys.readouterr().out
    assert "Divergence between the form distributions: 0.000" in compared

    scored = ["score", str(out), "--engine", "leanexplore"]
    user_cli.main([*scored, "--weights", str(mix_profile)])
    assert "Weighted by real traffic: success@1 1.000" in capsys.readouterr().out
    report = json.loads((out / "scores" / "leanexplore.all.json").read_text())
    assert report["traffic_weighted"]["success@5"] == 1.0
    assert set(report["by_form"]) == set(profiled["forms"])

    user_cli.main([*scored, "--library", "mathlib"])
    report = json.loads((out / "scores" / "leanexplore.all.mathlib.json").read_text())
    assert set(report["by_library"]) == {"mathlib"}


def test_generate_uses_a_style_profile_and_log_profile_reads_the_log(
    small_mix: None,
    corpus_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    encrypted_log: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    style = tmp_path / "style.json"
    style.write_text(
        json.dumps({"profiles": {"web": {"forms": {"prose": {"words": {"13": 1.0}}}}}})
    )
    seen: list[str] = []

    def respond(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.WRITER_SYSTEM:
            seen.append(user_of(body))
        return _writer(body)

    _use_model(monkeypatch, respond)
    out = tmp_path / "mix"
    cli.main(
        [
            "generate",
            "--corpus",
            str(corpus_path),
            "--out",
            str(out),
            "--style",
            str(style),
            "--group",
            "web",
        ]
    )
    assert seen and all("Use about 13 words" in prompt for prompt in seen)

    monkeypatch.setenv("LEB_QUERY_LOG_DB", str(encrypted_log))
    target = tmp_path / "log-profile.json"
    cli.main(["profile", "--log", "--to", str(target)])
    logged = json.loads(target.read_text())
    assert logged["rows"] == 180 and logged["first_day"] == "2026-09-01"
    assert set(logged["profiles"]) == {"all", "api", "mcp"}
    assert logged["profiles"]["all"]["searches"] == 180
    assert logged["profiles"]["all"]["distinct"] == 150
    assert set(logged["profiles"]["mcp"]["forms"]) == {"name"}


def test_tasks_submit_and_thread_items(
    small_mix: None,
    corpus_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "mix"
    common = ["--corpus", str(corpus_path), "--out", str(out)]
    task_file = tmp_path / "tasks.jsonl"
    cli.main(["tasks", *common, "--to", str(task_file)])
    assert "Wrote 4 writing tasks" in capsys.readouterr().out
    tasks = [json.loads(line) for line in task_file.read_text().splitlines()]

    def query_for(task: dict[str, str]) -> str:
        name = task["task"].split("\n", 1)[0].removeprefix("Name: ")
        return f"{GOOD} {name.split('.')[1]} {name.rsplit('_', 1)[-1]}"

    written = [{"id": task["id"], "query": query_for(task)} for task in tasks]
    written[0]["query"] = "bad"
    written.append({"id": "not-a-task", "query": "ignored"})
    query_file = tmp_path / "written.jsonl"
    query_file.write_text("\n".join(json.dumps(item) for item in written) + "\n\n")

    def judge(body: dict[str, Any]) -> str:
        if "judge error" in user_of(body):
            return "{}"
        return json.dumps({"grade": 3, "specific": True})

    _use_model(monkeypatch, judge)
    cli.main(["submit", *common, "--queries", str(query_file)])
    assert "Accepted 3 of 4 submitted queries" in capsys.readouterr().out
    journal = read_journal(out / "journal.jsonl")
    accepted = next(entry for entry in journal.values() if entry["accepted"])
    assert accepted["record"]["provenance"]["attempts"] == 1
    # A revision replaces an accepted query only when it differs and passes.
    good = [item for item in written[1:4]]
    revised = [
        {"id": good[0]["id"], "query": good[0]["query"]},
        {"id": good[1]["id"], "query": good[1]["query"] + " indeed"},
        {"id": good[2]["id"], "query": "bad"},
    ]
    query_file.write_text("\n".join(json.dumps(item) for item in revised))
    cli.main(["submit", *common, "--queries", str(query_file), "--revise"])
    assert "Accepted 1 of 1 submitted queries" in capsys.readouterr().out
    journal = read_journal(out / "journal.jsonl")
    replaced = journal[good[1]["id"]]["record"]
    assert replaced["query"].endswith(" indeed")
    assert replaced["provenance"]["revised_from"] == cli.DEFAULT_WRITER
    assert journal[good[2]["id"]]["record"]["query"] == good[2]["query"]
    # The rejected target is replaced by a reserve in the next round of tasks.
    cli.main(["tasks", *common, "--to", str(task_file)])
    assert "Wrote 1 writing tasks" in capsys.readouterr().out
    retry = json.loads(task_file.read_text())
    retry_query = query_for(retry).replace(GOOD, GOOD + " judge error")
    query_file.write_text(json.dumps({"id": retry["id"], "query": retry_query}))
    cli.main(["submit", *common, "--queries", str(query_file)])
    assert "Accepted 0 of 1 submitted queries" in capsys.readouterr().out
    failed = read_journal(out / "journal.jsonl")[retry["id"]]
    assert failed["attempts"][0]["error"] == "ValidationError"

    monkeypatch.setattr(
        zulip.ZulipSite,
        "from_zuliprc",
        classmethod(lambda cls, path: zulip.ZulipSite("u", "e", "k")),
    )
    thread = {
        "topic": "t",
        "url": "https://z.example/t",
        "first_message_id": 42,
        "messages": [
            {"asker": True, "content": "is there a lemma?"},
            {"asker": False, "content": "try the commutativity one"},
        ],
    }
    (out / "zulip-threads.json").write_text(json.dumps([thread]))
    item = {
        "id": 42,
        "query": "addition of naturals commutes",
        "answers": [{"name": "Demo.Algebra.add_comm_3", "grade": 3}],
    }
    item_file = tmp_path / "items.jsonl"
    item_file.write_text(json.dumps(item) + "\n")
    cli.main(["zulip", *common, "--queries", str(item_file)])
    assert "Accepted 1 of 1 submitted items" in capsys.readouterr().out


def test_parser_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        cli.main([])
    with pytest.raises(SystemExit):
        user_cli.main([])
