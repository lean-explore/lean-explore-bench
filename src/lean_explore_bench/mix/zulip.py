"""Turn questions asked on the Lean Zulip into benchmark queries.

The public channel "Is there code for X?" holds thousands of threads in
which someone asks whether a declaration exists and others answer with a
name, usually as a ``docs#Name`` link. Such a thread gives a realistic
request and a human-confirmed answer.

For each thread whose replies name a declaration of the corpus, a language
model rewrites the request as one search query and lists which named
declarations the thread confirms as answers. A judge from another model
family then checks the best answer against the query. Only the rewritten
query, the answers and a link to the thread are stored; message text and
author names are not. A query that repeats more than five consecutive words
of any message of its thread is rejected, so no post is reproduced.
"""

import asyncio
import base64
import configparser
import json
import re
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
from openai.types.chat import ChatCompletionMessageParam

from lean_explore_bench.infra import OpenRouterClient
from lean_explore_bench.mix import prompts
from lean_explore_bench.mix.checks import MAX_COPIED_WORDS, copied_run
from lean_explore_bench.mix.corpus import Corpus, library_and_area
from lean_explore_bench.mix.generate import GenerationSettings, read_journal
from lean_explore_bench.mix.record import QueryRecord

MESSAGES_PER_THREAD = 15
MAX_MESSAGE_CHARS = 1500
MAX_CANDIDATES = 12
REQUEST_INTERVAL_SECONDS = 0.4

_DOCS_LINK = re.compile(r"docs#([^\s`,;:)\]]+)")
_CODE_SPAN = re.compile(r"`([^`\s]+)`")

EXTRACT_SYSTEM = """\
You prepare items for a benchmark of Lean 4 declaration search engines from \
threads of the Lean Zulip channel "Is there code for X?".

You are shown the opening message of a thread, the replies, and the Lean \
declarations that the replies mention. Decide whether the thread is a search \
request: the asker wants an existing declaration and the replies point to \
one or more that answer the request.

If it is, write the request as the single query the asker would type into a \
search engine, in your own words. Keep the mathematical content, the level \
of detail and any Lean identifiers the asker used, but do not quote the \
asker: never reuse more than four consecutive words of any message. Drop \
greetings, background, code blocks and anything learned from the replies; in \
particular never use a name that only appears in the replies. At most 40 \
words.

Then grade each mentioned declaration that the thread presents as an answer:
- 3: the thread confirms it is what the asker wanted.
- 2: offered as a useful alternative or a close variant.
- 1: mentioned as related only.
Leave out declarations that are not offered as answers.

Reply with JSON: {"is_search": true, "query": "...", \
"answers": [{"name": "...", "grade": 3}]}. When the thread is not a search \
request, reply {"is_search": false, "query": "", "answers": []}."""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_search": {"type": "boolean"},
        "query": {"type": "string"},
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "grade": {"type": "integer", "enum": [1, 2, 3]},
                },
                "required": ["name", "grade"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["is_search", "query", "answers"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class ZulipSite:
    """Connection details of a Zulip server.

    Attributes:
        url: Base URL of the server.
        email: Account email.
        key: API key.
    """

    url: str
    email: str
    key: str

    @classmethod
    def from_zuliprc(cls, path: Path) -> "ZulipSite":
        """Read the ``[api]`` section of a ``zuliprc`` file."""
        parser = configparser.ConfigParser()
        parser.read(path)
        section = parser["api"]
        return cls(section["site"].rstrip("/"), section["email"], section["key"])

    def get(self, path: str, **params: str | int) -> Any:
        """Call a GET endpoint of the Zulip API and return the JSON reply."""
        query = urllib.parse.urlencode(params)
        token = base64.b64encode(f"{self.email}:{self.key}".encode()).decode()
        request = urllib.request.Request(
            f"{self.url}/api/v1/{path}?{query}",
            headers={
                "Authorization": f"Basic {token}",
                "User-Agent": "lean-search-benchmark",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)


def fetch_threads(
    site: ZulipSite,
    channel: str,
    max_topics: int,
    pause: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Fetch the opening messages of the most recent topics of a channel.

    Args:
        site: The Zulip server.
        channel: Channel name.
        max_topics: Number of topics to fetch, most recently active first.
        pause: Sleep function, replaceable in tests.

    Returns:
        One thread per topic: its title, a link, and the first messages in
        order, each as ``{"asker": bool, "content": str}``.
    """
    stream_id = site.get("get_stream_id", stream=channel)["stream_id"]
    topics = site.get(f"users/me/{stream_id}/topics")["topics"][:max_topics]
    threads = []
    for topic in topics:
        narrow = json.dumps(
            [
                {"operator": "channel", "operand": stream_id},
                {"operator": "topic", "operand": topic["name"]},
            ]
        )
        messages = site.get(
            "messages",
            anchor="oldest",
            num_before=0,
            num_after=MESSAGES_PER_THREAD,
            narrow=narrow,
            apply_markdown="false",
        )["messages"]
        pause(REQUEST_INTERVAL_SECONDS)
        if not messages:
            continue
        asker = messages[0]["sender_id"]
        encoded = urllib.parse.quote(topic["name"], safe="")
        threads.append(
            {
                "topic": topic["name"],
                "url": f"{site.url}/#narrow/channel/{stream_id}/topic/{encoded}",
                "first_message_id": messages[0]["id"],
                "messages": [
                    {
                        "asker": message["sender_id"] == asker,
                        "content": message["content"][:MAX_MESSAGE_CHARS],
                    }
                    for message in messages
                ],
            }
        )
    return threads


def candidates(thread: dict[str, Any], corpus: Corpus) -> list[str]:
    """Return corpus declarations named in the replies, in order of mention."""
    found: list[str] = []
    for message in thread["messages"][1:]:
        content = message["content"]
        for name in _DOCS_LINK.findall(content) + _CODE_SPAN.findall(content):
            name = name.rstrip(".")
            if name in corpus.names and name not in found:
                found.append(name)
    return found[:MAX_CANDIDATES]


def _thread_prompt(thread: dict[str, Any], names: list[str]) -> str:
    lines = [f"Topic: {thread['topic']}", "", "Opening message:"]
    lines.append(thread["messages"][0]["content"])
    lines += ["", "Replies:"]
    for message in thread["messages"][1:]:
        speaker = "asker" if message["asker"] else "other"
        lines.append(f"[{speaker}] {message['content']}")
    lines += ["", "Declarations mentioned in the replies:"]
    lines += [f"- {name}" for name in names]
    return "\n".join(lines)


async def _extract_one(
    client: OpenRouterClient,
    settings: GenerationSettings,
    thread: dict[str, Any],
    corpus: Corpus,
) -> dict[str, Any]:
    """Turn one thread into a journal entry."""
    entry: dict[str, Any] = {
        "id": f"question-zulip-{thread['first_message_id']}",
        "accepted": False,
        "record": None,
    }
    names = candidates(thread, corpus)
    if not names:
        return {**entry, "reason": "no corpus declaration in the replies"}
    try:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": _thread_prompt(thread, names)},
        ]
        extracted = await client.complete_json(
            messages,
            EXTRACT_SCHEMA,
            name="item",
            model=settings.writer_model,
            temperature=0.2,
        )
    except (KeyError, ValueError, jsonschema.ValidationError) as error:
        return {**entry, "reason": type(error).__name__}
    return await _finish(client, settings, thread, corpus, names, extracted)


async def _finish(
    client: OpenRouterClient,
    settings: GenerationSettings,
    thread: dict[str, Any],
    corpus: Corpus,
    names: Iterable[str],
    extracted: dict[str, Any],
) -> dict[str, Any]:
    """Check one extracted item and turn it into a journal entry.

    Args:
        client: OpenRouter client, used for the judge.
        settings: Models; ``writer_model`` names whoever extracted the item.
        thread: The thread the item was extracted from.
        corpus: The corpus snapshot.
        names: Declarations that may be graded as answers.
        extracted: The query and graded answers, as in :data:`EXTRACT_SCHEMA`.
    """
    entry: dict[str, Any] = {
        "id": f"question-zulip-{thread['first_message_id']}",
        "accepted": False,
        "record": None,
    }
    allowed = set(names)
    judgments = {
        answer["name"]: answer["grade"]
        for answer in extracted["answers"]
        if answer["name"] in allowed
    }
    query = extracted["query"].strip()
    if not extracted["is_search"] or not query or 3 not in judgments.values():
        return {**entry, "reason": "not a confirmed search request"}
    if any(name.lower() in query.lower() for name in judgments):
        return {**entry, "reason": "the query names an answer"}
    posts = " \n ".join(message["content"] for message in thread["messages"])
    if copied_run(query, posts) > MAX_COPIED_WORDS:
        return {**entry, "reason": "the query copies a message"}
    target = next(name for name, grade in judgments.items() if grade == 3)
    placed = library_and_area(corpus.modules[target])
    by_name = corpus.by_name()
    if target in by_name:
        verdict = await client.complete_json(
            prompts.judge_messages(by_name[target], query),
            prompts.JUDGE_SCHEMA,
            name="verdict",
            model=settings.judge_model,
            temperature=0.0,
        )
        if verdict["grade"] < 2:
            return {**entry, "reason": "the judge rejected the answer", **verdict}
    else:
        verdict = {}
    record = QueryRecord(
        id=entry["id"],
        query=query,
        query_type="question",
        variant="zulip",
        source="zulip",
        library=placed[0] if placed else "other",
        area=placed[1] if placed else "other",
        target=target,
        judgments=judgments,
        group_id=f"zulip:{thread['first_message_id']}",
        track="human",
        provenance={
            "method": "zulip-thread",
            "url": thread["url"],
            "writer_model": settings.writer_model,
            "judge_model": settings.judge_model,
            "judge_grade": verdict.get("grade"),
        },
    )
    return {**entry, "accepted": True, "record": record.to_json()}


async def extract(
    client: OpenRouterClient,
    settings: GenerationSettings,
    threads: list[dict[str, Any]],
    corpus: Corpus,
    journal: Path,
) -> dict[str, dict[str, Any]]:
    """Turn every thread not yet in the journal into a journal entry.

    Returns:
        Every journal entry, old and new, keyed by identifier.
    """
    done = read_journal(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    pending = [
        thread
        for thread in threads
        if f"question-zulip-{thread['first_message_id']}" not in done
    ]
    entries = await asyncio.gather(
        *(_extract_one(client, settings, thread, corpus) for thread in pending)
    )
    with journal.open("a", encoding="utf-8") as file:
        for entry in entries:
            done[entry["id"]] = entry
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return done


async def submit(
    client: OpenRouterClient,
    settings: GenerationSettings,
    threads: list[dict[str, Any]],
    written: dict[str, dict[str, Any]],
    corpus: Corpus,
    journal: Path,
) -> dict[str, dict[str, Any]]:
    """Check and judge items extracted outside this run.

    Args:
        client: OpenRouter client, used for the judge only.
        settings: ``writer_model`` names whoever extracted the items.
        threads: The fetched threads.
        written: For a thread's first message identifier, the query and
            graded answers extracted from it. Any declaration of the corpus
            may be an answer, not only those linked in the replies.
        corpus: The corpus snapshot.
        journal: JSON Lines file; an item replaces an earlier entry for the
            same thread unless that entry was accepted.

    Returns:
        Every journal entry, old and new, keyed by identifier.
    """
    done = read_journal(journal)
    pending = [
        thread
        for thread in threads
        if str(thread["first_message_id"]) in written
        and not done.get(f"question-zulip-{thread['first_message_id']}", {}).get(
            "accepted"
        )
    ]
    entries = await asyncio.gather(
        *(
            _finish(
                client,
                settings,
                thread,
                corpus,
                corpus.names,
                {"is_search": True, **written[str(thread["first_message_id"])]},
            )
            for thread in pending
        )
    )
    with journal.open("a", encoding="utf-8") as file:
        for entry in entries:
            done[entry["id"]] = entry
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return done


def select(done: dict[str, dict[str, Any]], quota: int) -> list[QueryRecord]:
    """Pick up to ``quota`` accepted Zulip queries, most recent threads first."""
    accepted = [
        QueryRecord.from_json(entry["record"])
        for entry in done.values()
        if entry["accepted"]
    ]
    accepted.sort(key=lambda record: -int(record.id.rsplit("-", 1)[-1]))
    return accepted[:quota]
