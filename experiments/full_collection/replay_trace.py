"""Keep reused baseline timings separate from corrected ranking diagnostics."""

import argparse
import json
from pathlib import Path

from collection import digest, write


def normalized_trace(trace, results):
    """Retain retrieval stages and label copied timings by their baseline origin."""
    return dict(
        stages={**trace["stages"], "results": [row["id"] for row in results]},
        baseline_elapsed_ms=trace.get(
            "baseline_elapsed_ms", trace.get("elapsed_ms", {})
        ),
        baseline_started=trace.get("baseline_started", trace.get("_started")),
        scope="Retrieval stages and timing diagnostics come from the baseline; reranked and results stages describe the corrected ranking.",
    )


def normalize(args):
    """Write a derived journal without changing scores, returned results or latency."""
    contract_path = args.run / "contract.json"
    journal = args.run / "records.jsonl"
    complete = json.loads((args.run / "complete.json").read_text())
    contract = json.loads(contract_path.read_text())
    if (
        digest(journal) != complete["records_sha256"]
        or digest(contract_path) != complete["contract_sha256"]
    ):
        raise ValueError("Changed source journal or contract")
    args.out.mkdir(parents=True, exist_ok=False)
    contract["record_transform"] = dict(
        source_records_sha256=complete["records_sha256"],
        source_contract_sha256=complete["contract_sha256"],
        transform_sha256=digest(__file__),
        scope="Diagnostic trace metadata only. Scores, result order and per-request latency are unchanged. The original journal remains preserved.",
    )
    write(args.out / "contract.json", contract)
    for name in ("executed_runner.py", "target-availability.json"):
        (args.out / name).write_bytes((args.run / name).read_bytes())
    (args.out / "executed_trace_normalization.py").write_bytes(
        Path(__file__).read_bytes()
    )
    count = changed = 0
    with journal.open() as source, (args.out / "records.jsonl").open("w") as output:
        for identifier, line in zip(contract["scheduled_ids"], source, strict=True):
            original = json.loads(line)
            if original["query_id"] != identifier:
                raise ValueError("Source schedule mismatch")
            record = {
                **original,
                "trace": normalized_trace(original["trace"], original["results"]),
            }
            before = {key: value for key, value in original.items() if key != "trace"}
            after = {key: value for key, value in record.items() if key != "trace"}
            if before != after:
                raise ValueError("Normalization altered an inference result")
            changed += (
                original["trace"]["stages"].get("results")
                != record["trace"]["stages"]["results"]
            )
            output.write(json.dumps(record, separators=(",", ":")) + "\n")
            count += 1
    if count != complete["completed"] or count != complete["scheduled"]:
        raise ValueError("Source completion counts differ")
    write(
        args.out / "complete.json",
        {
            **complete,
            "records_sha256": digest(args.out / "records.jsonl"),
            "contract_sha256": digest(args.out / "contract.json"),
            "trace_result_orders_synchronized": changed,
            "inference_records_preserved": count,
        },
    )
    print(
        json.dumps(
            dict(
                records=count,
                trace_result_orders_synchronized=changed,
                inference_results_unchanged=True,
            )
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    normalize(parser.parse_args())
