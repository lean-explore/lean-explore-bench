import asyncio
import json
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from helpers import scripted_client, system_of, user_of

from lean_explore_bench.builder import prompts, zulip
from lean_explore_bench.builder.corpus import Corpus
from lean_explore_bench.builder.generate import GenerationSettings, read_journal

SETTINGS = GenerationSettings(writer_model="test/writer", judge_model="test/judge")
ANSWER = "Demo.Algebra.add_comm_3"
OTHER = "Demo.Algebra.Pair.left"


def _thread(identifier: int, replies: list[str]) -> dict[str, Any]:
    messages = [{"asker": True, "content": "Is there a lemma that a + b = b + a?"}]
    messages += [{"asker": False, "content": reply} for reply in replies]
    return {
        "topic": f"topic {identifier}",
        "url": f"https://zulip.example/#narrow/topic/{identifier}",
        "first_message_id": identifier,
        "messages": messages,
    }


def test_zuliprc_and_get(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rc = tmp_path / "zuliprc"
    rc.write_text("[api]\nemail=me@example.org\nkey=secret\nsite=https://z.example/\n")
    site = zulip.ZulipSite.from_zuliprc(rc)
    assert site == zulip.ZulipSite("https://z.example", "me@example.org", "secret")

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    seen: list[urllib.request.Request] = []

    def urlopen(request: urllib.request.Request, timeout: float) -> Response:
        seen.append(request)
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    assert site.get("messages", anchor="oldest", num_after=3) == {"ok": True}
    assert seen[0].full_url == (
        "https://z.example/api/v1/messages?anchor=oldest&num_after=3"
    )
    assert seen[0].get_header("Authorization", "").startswith("Basic ")


def test_fetch_threads_marks_the_asker_and_skips_empty_topics() -> None:
    class Site(zulip.ZulipSite):
        def get(self, path: str, **params: str | int) -> Any:
            if path == "get_stream_id":
                assert params == {"stream": "Is there code for X?"}
                return {"stream_id": 7}
            if path == "users/me/7/topics":
                return {"topics": [{"name": "a b"}, {"name": "empty"}, {"name": "x"}]}
            topic = json.loads(str(params["narrow"]))[1]["operand"]
            if topic == "empty":
                return {"messages": []}
            return {
                "messages": [
                    {"id": 11, "sender_id": 1, "content": "question " + "x" * 3000},
                    {"id": 12, "sender_id": 2, "content": "docs#Nat.add_comm"},
                    {"id": 13, "sender_id": 1, "content": "thanks"},
                ]
            }

    pauses: list[float] = []
    threads = zulip.fetch_threads(
        Site("https://z.example", "e", "k"), "Is there code for X?", 2, pauses.append
    )
    assert len(threads) == 1 and len(pauses) == 2
    thread = threads[0]
    assert thread["topic"] == "a b" and thread["first_message_id"] == 11
    assert thread["url"] == "https://z.example/#narrow/channel/7/topic/a%20b"
    assert [message["asker"] for message in thread["messages"]] == [True, False, True]
    assert len(thread["messages"][0]["content"]) == zulip.MAX_MESSAGE_CHARS


def test_candidates_come_from_replies_and_exist_in_the_corpus(corpus: Corpus) -> None:
    thread = _thread(
        1,
        [
            f"We have docs#{ANSWER}. Also `{OTHER}` and `Not.in_corpus`.",
            f"Again docs#{ANSWER}, or docs#Missing.name",
        ],
    )
    thread["messages"][0]["content"] += " I tried `Demo.Algebra.double`."
    assert zulip.candidates(thread, corpus) == [ANSWER, OTHER]


def _model(extracted: dict[str, Any], grade: int = 3) -> Any:
    def respond(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.JUDGE_SYSTEM:
            assert body["model"] == "test/judge"
            return json.dumps({"grade": grade, "specific": True})
        assert system_of(body) == zulip.EXTRACT_SYSTEM
        assert "[other] " in user_of(body) and f"- {ANSWER}" in user_of(body)
        return json.dumps(extracted)

    return respond


def _extract(
    corpus: Corpus, tmp_path: Path, respond: Any, replies: list[str]
) -> dict[str, Any]:
    done = asyncio.run(
        zulip.extract(
            scripted_client(respond),
            SETTINGS,
            [_thread(5, replies)],
            corpus,
            tmp_path / "zulip-journal.jsonl",
        )
    )
    return done["question-zulip-5"]


def test_confirmed_thread_becomes_a_record(corpus: Corpus, tmp_path: Path) -> None:
    extracted = {
        "is_search": True,
        "query": " addition of naturals commutes ",
        "answers": [
            {"name": ANSWER, "grade": 3},
            {"name": OTHER, "grade": 2},
            {"name": "Invented.name", "grade": 3},
        ],
    }
    replies = [f"docs#{ANSWER} or `{OTHER}`", "thanks"]
    entry = _extract(corpus, tmp_path, _model(extracted), replies)
    assert entry["accepted"]
    record = entry["record"]
    assert record["query"] == "addition of naturals commutes"
    assert record["judgments"] == {ANSWER: 3, OTHER: 2}
    assert record["target"] == ANSWER and record["library"] == "mathlib"
    assert record["query_type"] == "question" and record["source"] == "zulip"
    assert record["track"] == "human" and record["group_id"] == "zulip:5"
    assert record["provenance"]["url"].endswith("/5")
    assert record["provenance"]["judge_grade"] == 3
    assert "content" not in json.dumps(record)


@pytest.mark.parametrize(
    ("extracted", "grade", "reason"),
    [
        ({"is_search": False, "query": "", "answers": []}, 3, "not a confirmed"),
        (
            {
                "is_search": True,
                "query": "q",
                "answers": [{"name": ANSWER, "grade": 2}],
            },
            3,
            "not a confirmed",
        ),
        (
            {
                "is_search": True,
                "query": "a lemma that a + b = b + a",
                "answers": [{"name": ANSWER, "grade": 3}],
            },
            3,
            "copies a message",
        ),
        (
            {
                "is_search": True,
                "query": f"where is {ANSWER}",
                "answers": [{"name": ANSWER, "grade": 3}],
            },
            3,
            "names an answer",
        ),
        (
            {
                "is_search": True,
                "query": "q",
                "answers": [{"name": ANSWER, "grade": 3}],
            },
            1,
            "judge rejected",
        ),
        ({"unexpected": 1}, 3, "ValidationError"),
    ],
)
def test_rejections(
    corpus: Corpus,
    tmp_path: Path,
    extracted: dict[str, Any],
    grade: int,
    reason: str,
) -> None:
    entry = _extract(corpus, tmp_path, _model(extracted, grade), [f"docs#{ANSWER}"])
    assert not entry["accepted"] and entry["record"] is None
    assert reason in entry["reason"]


def test_thread_without_candidates_costs_nothing(
    corpus: Corpus, tmp_path: Path
) -> None:
    def respond(body: dict[str, Any]) -> str:
        raise AssertionError("no model call expected")

    entry = _extract(corpus, tmp_path, respond, ["no names here"])
    assert entry["reason"] == "no corpus declaration in the replies"


def test_ineligible_answer_is_accepted_without_a_judge(
    corpus: Corpus, tmp_path: Path
) -> None:
    def respond(body: dict[str, Any]) -> str:
        assert system_of(body) == zulip.EXTRACT_SYSTEM
        return json.dumps(
            {
                "is_search": True,
                "query": "left projection of a pair",
                "answers": [{"name": OTHER, "grade": 3}],
            }
        )

    done = asyncio.run(
        zulip.extract(
            scripted_client(respond),
            SETTINGS,
            [_thread(9, [f"`{OTHER}`"])],
            corpus,
            tmp_path / "journal.jsonl",
        )
    )
    record = done["question-zulip-9"]["record"]
    assert record["target"] == OTHER and record["provenance"]["judge_grade"] is None


def test_extract_resumes_and_select_prefers_recent_threads(
    corpus: Corpus, tmp_path: Path
) -> None:
    journal = tmp_path / "journal.jsonl"
    extracted = {
        "is_search": True,
        "query": "addition of naturals commutes",
        "answers": [{"name": ANSWER, "grade": 3}],
    }
    calls = {"count": 0}

    def respond(body: dict[str, Any]) -> str:
        calls["count"] += 1
        return str(_model(extracted)(body))

    threads = [_thread(i, [f"docs#{ANSWER}"]) for i in (3, 20, 100)]
    threads.append(_thread(50, ["nothing"]))
    for _ in range(2):
        done = asyncio.run(
            zulip.extract(scripted_client(respond), SETTINGS, threads, corpus, journal)
        )
    assert calls["count"] == 6
    assert done == read_journal(journal) and len(done) == 4
    chosen = zulip.select(done, 2)
    assert [record.id for record in chosen] == [
        "question-zulip-100",
        "question-zulip-20",
    ]
    assert zulip.select({}, 5) == []


def test_submit_takes_items_extracted_elsewhere(corpus: Corpus, tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    threads = [_thread(i, ["no linked name here"]) for i in (1, 2, 3)]
    written: dict[str, dict[str, Any]] = {
        "1": {
            "query": "addition of naturals commutes",
            "answers": [{"name": ANSWER, "grade": 3}],
        },
        "2": {
            "query": "a lemma that a + b = b + a",
            "answers": [{"name": ANSWER, "grade": 3}],
        },
        "7": {"query": "unknown thread", "answers": []},
    }

    def judge(body: dict[str, Any]) -> str:
        assert system_of(body) == prompts.JUDGE_SYSTEM
        return json.dumps({"grade": 3, "specific": True})

    def run() -> dict[str, dict[str, Any]]:
        return asyncio.run(
            zulip.submit(
                scripted_client(judge), SETTINGS, threads, written, corpus, journal
            )
        )

    done = run()
    assert done["question-zulip-1"]["accepted"]
    assert done["question-zulip-1"]["record"]["target"] == ANSWER
    assert done["question-zulip-2"]["reason"] == "the query copies a message"
    assert set(done) == {"question-zulip-1", "question-zulip-2"}
    # A second pass leaves the accepted item alone and retries the rejected one.
    written["2"]["query"] = "commutativity for sums of naturals"
    again = run()
    assert again["question-zulip-2"]["accepted"]
    assert len(journal.read_text().splitlines()) == 3
