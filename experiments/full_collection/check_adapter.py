"""Compare prototype and production scoring on every target-bearing request."""

import argparse
import json
import math
from pathlib import Path

from collection import digest, write


def check(args):
    cases = json.loads(args.cases.read_text())["cases"]
    contract = json.loads((args.ablation / "contract.json").read_text())
    completion = json.loads((args.ablation / "complete.json").read_text())
    production = json.loads((args.corrected / "contract.json").read_text())
    if (
        digest(args.cases) != contract["cases_sha256"]
        or digest(args.cases) != production["cases_sha256"]
    ):
        raise ValueError("Case identity changed")
    if contract["base_contract_sha256"] != production["base_contract_sha256"]:
        raise ValueError("Different baseline contracts")
    if production["settings"]["reranker_max_length"] != 256:
        raise ValueError("Production context is not the 256-token condition")
    if digest(args.ablation / "records.jsonl") != completion["records_sha256"]:
        raise ValueError("Changed prototype journal")
    expected = {}
    with (args.ablation / "records.jsonl").open() as stream:
        for identifier, line in zip(contract["scheduled_ids"], stream, strict=True):
            row = json.loads(line)
            if row["query_id"] != identifier or identifier in expected:
                raise ValueError("Prototype schedule mismatch")
            expected[identifier] = row
    result = dict(
        requests=0,
        max_absolute_score_difference=0.0,
        neural_order_changed=0,
        mixture_order_changed=0,
        neural_top1_changed=0,
        mixture_top1_changed=0,
    )
    seen = set()
    with (args.corrected / "records.jsonl").open() as stream:
        for case, line in zip(cases, stream):
            if not line.endswith("\n"):
                break
            row = json.loads(line)
            if row["query_id"] != case["id"]:
                raise ValueError("Production schedule mismatch")
            if case["id"] not in expected:
                continue
            prototype = expected[case["id"]]
            if row["status"] != prototype["baseline_status"]:
                raise ValueError("Request status changed")
            seen.add(case["id"])
            pool = row.get("fixed_pool") or {}
            if prototype["candidate_ids"] != pool.get("candidate_ids", []):
                raise ValueError("Candidate pool changed")
            if prototype["conditions"]:
                variant = prototype["conditions"]["chat_yes_no_256"]
                actual = pool.get("scores", {}).get("neural_only", [])
                differences = [
                    abs(a - b) for a, b in zip(actual, variant["scores"], strict=True)
                ]
                if not all(math.isfinite(value) for value in differences):
                    raise ValueError("Non-finite score difference")
                result["max_absolute_score_difference"] = max(
                    result["max_absolute_score_difference"],
                    max(differences, default=0.0),
                )
                visible = {d["id"] for d in row["results"]}
                if visible != set(variant["mixture"]):
                    raise ValueError("Visible output set changed")
                rankings = dict(
                    neural=[
                        i
                        for i in pool.get("rankings", {}).get("neural_only", [])
                        if i in visible
                    ],
                    mixture=[d["id"] for d in row["results"]],
                )
                for mode, ranking in rankings.items():
                    result[mode + "_order_changed"] += ranking != variant[mode]
                    result[mode + "_top1_changed"] += ranking[:1] != variant[mode][:1]
            result["requests"] += 1
            if seen == set(expected):
                break
    if seen != set(expected):
        raise ValueError(
            f"Only {len(seen)} of {len(expected)} production records are available"
        )
    result["scope"] = (
        "Corrected production client with last-token-only projection versus full-logit prototype, CUDA float16 and 256 tokens, every target-bearing fixed pool. First-position and full-order comparisons are separate."
    )
    write(args.out, result)
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "ablation", "corrected", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    check(parser.parse_args())
