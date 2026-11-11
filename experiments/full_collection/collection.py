"""Prepare every supplied query, retaining source membership and label provenance."""

import argparse
import collections
import datetime
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/offline/src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lean_explore_bench.querylog.features import measure
from leanexplore_benchmark.profile import features
from leanexplore_benchmark.querylog import Query


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def categories(text):
    f = features(Query(0, "api", text, (), None, datetime.date(2000, 1, 1)))
    m = measure(text)
    surface = f["surface"]
    if surface == "empty":
        form = "empty"
    elif surface == "identifier_only":
        form = "name"
    elif surface == "proof_state_or_statement":
        form = "formula"
    elif surface == "mixed_identifier_text":
        form = "mixed"
    elif surface in {"symbolic_expression", "latex_present"}:
        form = "mixed" if m.function_word_share >= 0.1 else "formula"
    else:
        form = (
            "prose"
            if surface == "question_like" or m.function_word_share >= 0.1
            else "keywords"
        )
    return {**f, "form": form}


def source_rows(source):
    path = Path(source["path"])
    data = (
        [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()]
        if path.suffix == ".jsonl"
        else json.loads(path.read_text(encoding="utf-8-sig"))
    )
    kind = source["kind"]
    if kind == "query_log":
        for channel, rows in data.items():
            for i, row in enumerate(rows):
                yield {
                    "query": row["query"],
                    "packages": row["package_filters"],
                    "source_id": f"{channel}:{i}",
                    "channel": channel,
                    "day": row["collected_on"],
                    "label_kind": "unlabelled",
                    "targets": [],
                }
    elif kind == "discussion_candidates":
        for row in data:
            targets = []
            for answer in row["answer_candidates"]:
                url = urlparse(answer["documentation_url"])
                name = unquote(parse_qs(url.query).get("pattern", [url.fragment])[0])
                if name:
                    targets.append(name)
            yield {
                "query": row["question"],
                "packages": [],
                "source_id": row["id"],
                "channel": row["channel"],
                "group": row["id"],
                "reference": row["question_url"],
                "label_kind": "reply_link_proxy",
                "targets": sorted(set(targets)),
                "original_split": row.get("split"),
                "query_origin": "original_opening_message",
            }
    elif kind == "mathlibqr":
        for row in data:
            for field in (
                "q1a_lean",
                "q1b_latex",
                "q1c_natural",
                "q2_slogan",
                "q3_nickname",
                "q4_special_case",
            ):
                if row.get(field, "").strip():
                    yield {
                        "query": row[field].strip(),
                        "packages": [],
                        "source_id": row["id"] + ":" + field,
                        "group": row["id"],
                        "upstream_style": field,
                        "difficulty": row["difficulty"],
                        "label_kind": "upstream_single_gold",
                        "targets": [row["full_name"]],
                    }
    elif kind == "mathlibmpr":
        for row in data:
            routes = [g["docs"] for g in row["premise_group"]]
            for field in ("NL_main_result", "formal_statement"):
                yield {
                    "query": row[field],
                    "packages": [],
                    "source_id": row["id"] + ":" + field,
                    "group": row["id"],
                    "upstream_style": field,
                    "label_kind": "upstream_alternative_premises",
                    "routes": routes,
                    "targets": sorted({x for route in routes for x in route}),
                }
    elif kind == "fate_h":
        for row in data:
            for field in ("informal_statement", "formal_statement"):
                yield {
                    "query": row[field],
                    "packages": [],
                    "source_id": row["name"] + ":" + field,
                    "group": row["name"],
                    "upstream_style": field,
                    "domain_tags": row["tag"],
                    "label_kind": "unlabelled",
                    "targets": [],
                    "task": "proof_problem_retrieval_diagnostic",
                }
    elif kind == "cases":
        rows = data["cases"] if isinstance(data, dict) else data
        for row in rows:
            targets = row.get(
                "targets", row.get("candidate_targets", row.get("relevant", []))
            )
            yield {
                "query": row["query"],
                "packages": row.get("packages", []),
                "source_id": row["id"],
                "group": row.get("topic_id", row["id"]),
                "label_kind": "historical_proposed_targets"
                if targets
                else "unlabelled",
                "targets": targets,
                "original_form": row.get("form", row.get("category", row.get("style"))),
                "original_intent": row.get("intent"),
                "original_domain": row.get("domain"),
                "original_provenance": row.get("provenance", row.get("source")),
            }
    else:
        raise ValueError(f"Unknown input kind: {kind}")


def prepare(sources):
    cases = {}
    inventory = {
        "sources": [],
        "deduplication": "Exact query text and sorted unique package filters; every membership retained.",
        "category_status": "Deterministic surface rules; intent/domain cues are unvalidated.",
        "scope": "All supplied query records and all nonempty upstream query fields; no sample or cap.",
    }
    for source in sources:
        count = 0
        own_ids = set()
        for row in source_rows(source):
            count += 1
            if not isinstance(row["query"], str) or not all(
                isinstance(x, str) for x in row["packages"]
            ):
                raise ValueError(f"Invalid record in {source['name']}: {count}")
            key = json.dumps(
                [row["query"], sorted(set(row["packages"]))], ensure_ascii=False
            )
            identifier = hashlib.sha256(key.encode()).hexdigest()
            own_ids.add(identifier)
            if identifier not in cases:
                cases[identifier] = {
                    "id": identifier,
                    "query": row["query"],
                    "packages": sorted(set(row["packages"])),
                    "categories": categories(row["query"]),
                    "memberships": [],
                }
            cases[identifier]["memberships"].append(
                {
                    **{k: v for k, v in row.items() if k not in {"query", "packages"}},
                    "source": source["name"],
                }
            )
        inventory["sources"].append(
            {
                **source,
                "sha256": digest(source["path"]),
                "records": count,
                "distinct_requests": len(own_ids),
            }
        )
    inventory.update(
        records=sum(s["records"] for s in inventory["sources"]),
        unique_requests=len(cases),
        categories={
            axis: dict(
                collections.Counter(c["categories"][axis] for c in cases.values())
            )
            for axis in ("form", "surface", "intent_cue", "domain_cue")
        },
    )
    return {
        "schema_version": 1,
        "scope": "full-available-collection-v1",
        "cases": list(cases.values()),
    }, inventory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    suite, inventory = prepare(json.loads(args.sources.read_text())["sources"])
    write(args.out / "cases.json", suite)
    inventory["cases_sha256"] = digest(args.out / "cases.json")
    write(args.out / "inventory.json", inventory)
    print(
        json.dumps(
            {k: v for k, v in inventory.items() if k != "sources"}, ensure_ascii=False
        )
    )
