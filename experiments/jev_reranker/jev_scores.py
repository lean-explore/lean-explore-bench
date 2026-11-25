"""Score dumped candidate pools with Jev, TypeSafe's System One model.

Jev answers typed questions about a state instead of generating text. A Noul question
returns the probability that a statement holds, which serves as a relevance score.
Requests go to OpenRouter's System One endpoint and need OPENROUTER_API_KEY.

Two formulations are supported:

  pointwise  one request per query-candidate pair, like a cross-encoder
  listwise   one request per query; every candidate is in the state and each gets
             its own Noul question, so Jev can see the competing candidates

The instructions below were written once, before any result was seen, and are not tuned.
Standard library only. Finished queries are skipped when the output file already exists.
"""

import argparse
import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/systemone"
QUERY_KINDS = (
    "The query may be a declaration name (possibly partial or misspelt), a "
    "natural-language description, a Lean statement or pattern, a few keywords, a "
    "proof goal that the declaration should close, or a question."
)
CRITERIA = {
    "true": "The declaration is what the query describes, names, states or asks "
    "for, or it directly answers the query.",
    "false": "The declaration is a different one, even if it is on the same topic "
    "or has a similar name.",
}
POINTWISE = (
    "`query` was typed into a search engine for Lean 4 libraries. `declaration` is "
    "one candidate result: its name, then an informal description. "
    f"{QUERY_KINDS} Is this declaration what the query is looking for?"
)
LISTWISE = (
    "`query` was typed into a search engine for Lean 4 libraries. `candidates` are "
    "the retrieved declarations, each given as its name, then an informal "
    f"description. {QUERY_KINDS} Is candidate {{key}} what the query is looking for?"
)

_write_lock = threading.Lock()


def call(model: str, state: object, questions: dict, retries: int = 8) -> dict:
    """Send one System One request, retrying rate limits and server errors."""
    body = json.dumps({"model": model, "state": state, "questions": questions})
    request = urllib.request.Request(
        ENDPOINT,
        data=body.encode(),
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                answer = json.load(response)
            if "answers" in answer:
                return answer
            error: object = answer
        except urllib.error.HTTPError as http_error:
            error = f"{http_error.code} {http_error.read()[:300]!r}"
            if http_error.code not in (408, 429) and http_error.code < 500:
                raise RuntimeError(error) from http_error
        except (urllib.error.URLError, TimeoutError) as network_error:
            error = network_error
        time.sleep(min(60, 2**attempt))
    raise RuntimeError(f"giving up after {retries} attempts: {error}")


def score_pool(record: dict, mode: str, model: str, pair_workers: int) -> dict:
    """Return Jev's score for each candidate of one query, in pool order."""
    documents = [c["document"] for c in record["candidates"]]
    started = time.perf_counter()
    if mode == "listwise":
        keys = [f"c{i:02d}" for i in range(len(documents))]
        answer = call(
            model,
            {"query": record["query"], "candidates": dict(zip(keys, documents))},
            {
                key: {
                    "type": "noul",
                    "instructions": LISTWISE.format(key=key),
                    "criteria": CRITERIA,
                }
                for key in keys
            },
        )
        answers = [answer]
        scores = [answer["answers"][key]["noul"] for key in keys]
    else:
        question = {
            "relevant": {"type": "noul", "instructions": POINTWISE, "criteria": CRITERIA}
        }
        with ThreadPoolExecutor(pair_workers) as pool:
            answers = list(
                pool.map(
                    lambda document: call(
                        model,
                        {"query": record["query"], "declaration": document},
                        question,
                    ),
                    documents,
                )
            )
        scores = [answer["answers"]["relevant"]["noul"] for answer in answers]
    return {
        "id": record["id"],
        "mode": mode,
        "model": answers[0]["model"],
        "scores": scores,
        "seconds": round(time.perf_counter() - started, 3),
        "requests": len(answers),
        "input_tokens": sum(a["usage"]["input_tokens"] for a in answers),
        "cost": sum(a["usage"].get("cost", 0.0) for a in answers),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pools", required=True, help="output of dump_pools.py")
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=("pointwise", "listwise"), required=True)
    parser.add_argument("--model", default="jev-1.14")
    parser.add_argument("--limit", type=int, help="score only the first N queries")
    parser.add_argument("--query-workers", type=int, default=4)
    parser.add_argument("--pair-workers", type=int, default=8)
    args = parser.parse_args()

    records = [json.loads(line) for line in Path(args.pools).read_text().splitlines()]
    output = Path(args.output)
    done = set()
    if output.exists():
        done = {json.loads(line)["id"] for line in output.read_text().splitlines()}
    todo = [r for r in records[: args.limit] if r["id"] not in done]

    def run(record: dict) -> None:
        result = score_pool(record, args.mode, args.model, args.pair_workers)
        with _write_lock, output.open("a") as out:
            out.write(json.dumps(result) + "\n")
        print(f"{result['id']} {result['seconds']}s ${result['cost']:.5f}", flush=True)

    with ThreadPoolExecutor(args.query_workers) as pool:
        list(pool.map(run, todo))


if __name__ == "__main__":
    main()
