"""Summarise a recall_depth.py journal: recall curves, misses, selection loss and cost.

Recall follows score.py: absent target names stay in the denominator, errors
count as zero, and each source is averaged over its own memberships.
"""

import argparse
import collections
import json
import sqlite3
import statistics
from pathlib import Path

from collection import digest, write
from recall_depth import DEPTHS, labelled_cases

STAGES = ("lexical", "dense", "fused", "selection")
GENERATED_KINDS = {"projection", "constructor", "recursor"}
BASE_STAGES = {
    "lexical": "bm25",
    "dense": "semantic",
    "fused": "fusion",
    "selection": "selection",
}


def load_journal(run, cases):
    contract = json.loads((run / "contract.json").read_text())
    completion = json.loads((run / "complete.json").read_text())
    if completion["records_sha256"] != digest(run / "records.jsonl"):
        raise ValueError("Journal changed after completion")
    if completion["contract_sha256"] != digest(run / "contract.json"):
        raise ValueError("Contract changed after completion")
    records = {}
    with (run / "records.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            records[record["query_id"]] = record
    if [c["id"] for c in cases] != contract["scheduled_ids"] or len(records) != len(
        cases
    ):
        raise ValueError("Journal does not cover the labelled schedule")
    return records


def rank(record, k, stage, target):
    if record["status"] != "ok" or not isinstance(target, int):
        return None
    return record["depths"][str(k)]["ranks"][stage].get(str(target))


def memberships(cases, availability):
    """Yield (case, membership, targets) with absent names kept as strings."""
    for case in cases:
        for membership in case["memberships"]:
            if not membership["targets"]:
                continue
            targets = [
                availability[t] if availability.get(t) is not None else "absent:" + t
                for t in membership["targets"]
            ]
            yield case, membership, list(dict.fromkeys(targets))


def recall_curves(cases, records, availability):
    sums = collections.defaultdict(lambda: collections.defaultdict(float))
    counts = collections.Counter()
    present_sums = collections.defaultdict(lambda: collections.defaultdict(float))
    present_counts = collections.Counter()
    for case, membership, targets in memberships(cases, availability):
        source = membership["source"]
        record = records[case["id"]]
        counts[source] += 1
        present = [t for t in targets if isinstance(t, int)]
        if present:
            present_counts[source] += 1
        for k in DEPTHS:
            hits = {}
            for stage in STAGES:
                hits[stage] = {
                    t
                    for t in present
                    if (r := rank(record, k, stage, t)) is not None and r <= k
                }
            hits["fused_all"] = {
                t for t in present if rank(record, k, "fused", t) is not None
            }
            hits["union"] = hits["lexical"] | hits["dense"]
            if record["status"] == "ok":
                exhaustive = record["exhaustive_dense"]["ranks"]
                reach = record["reachability"]
                if k == max(DEPTHS):
                    hits["dense_exhaustive"] = {
                        t
                        for t in present
                        if (r := exhaustive.get(str(t))) is not None and r <= k
                    }
                    hits["lexical_reachable"] = {
                        t for t in present if reach[str(t)]["lexical_match"]
                    }
                    hits["dense_reachable"] = {
                        t for t in present if reach[str(t)]["probed"]
                    }
            for name, found in hits.items():
                sums[source][f"{name}@{k}"] += len(found) / len(targets)
                if present:
                    present_sums[source][f"{name}@{k}"] += len(found) / len(present)
    return {
        source: dict(
            memberships=counts[source],
            memberships_with_present_target=present_counts[source],
            recall={m: v / counts[source] for m, v in values.items()},
            present_target_recall={
                m: v / present_counts[source] for m, v in present_sums[source].items()
            }
            if present_counts[source]
            else None,
        )
        for source, values in sorted(sums.items())
    }


def selection_loss(cases, records, availability):
    """Targets in the best single channel at a depth but outside the 500-candidate selection."""
    result = {}
    for k in (500, 1000, 2000, 5000):
        per_source = collections.defaultdict(collections.Counter)
        fused_ranks = collections.defaultdict(list)
        for case, membership, targets in memberships(cases, availability):
            source = membership["source"]
            record = records[case["id"]]
            for t in targets:
                stats = per_source[source]
                stats["target_instances"] += 1
                ranks = {s: rank(record, k, s, t) for s in STAGES}
                in_lex = ranks["lexical"] is not None and ranks["lexical"] <= k
                in_dense = ranks["dense"] is not None and ranks["dense"] <= k
                selected = ranks["selection"] is not None
                stats["in_lexical"] += in_lex
                stats["in_dense"] += in_dense
                stats["in_union"] += in_lex or in_dense
                stats["in_selection"] += selected
                stats["dense_not_selected"] += in_dense and not selected
                stats["lexical_not_selected"] += in_lex and not selected
                stats["union_not_selected"] += (in_lex or in_dense) and not selected
                if in_lex or in_dense:
                    fused_ranks[source].append(ranks["fused"])
        closes = {}
        for source, stats in per_source.items():
            best = max(stats["in_lexical"], stats["in_dense"])
            ranks_sorted = sorted(r for r in fused_ranks[source] if r is not None)
            needed_best = (
                ranks_sorted[best - 1] if 0 < best <= len(ranks_sorted) else None
            )
            # Smallest fused cutoff holding as many union targets as the best channel.
            closes[source] = dict(
                best_channel="dense"
                if stats["in_dense"] >= stats["in_lexical"]
                else "lexical",
                fused_cutoff_matching_best_channel=needed_best,
                fused_cutoff_holding_whole_union=ranks_sorted[-1]
                if ranks_sorted
                else None,
                fused_cutoff_holding_95pct_union=ranks_sorted[
                    max(0, int(0.95 * len(ranks_sorted)) - 1)
                ]
                if ranks_sorted
                else None,
            )
        result[str(k)] = dict(
            counts={s: dict(c) for s, c in sorted(per_source.items())},
            fused_cutoffs=closes,
        )
    return result


def corpus_names(database):
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as conn:
        return {
            name: (ident, module)
            for ident, name, module in conn.execute(
                "SELECT id, name, module FROM declarations"
            )
        }


def classify_misses(cases, records, availability, probe, corpus, deepest):
    by_suffix = collections.defaultdict(list)
    for name in corpus:
        parts = name.split(".")
        for i in range(1, len(parts)):
            by_suffix[".".join(parts[i:])].append(name)
    target_info = {row["name"]: row for row in probe}
    instance = collections.Counter()
    distinct = collections.defaultdict(set)
    examples = collections.defaultdict(list)
    for case, membership, _ in memberships(cases, availability):
        record = records[case["id"]]
        for name in dict.fromkeys(membership["targets"]):
            ident = availability.get(name)
            if record["status"] != "ok":
                label = "request_error"
            elif ident is None:
                info = target_info.get(name, {})
                renamed = [
                    n
                    for n in (
                        [info.get("deprecated_to")] if info.get("deprecated_to") else []
                    )
                    + info.get("deprecated_from", [])
                    if n in corpus
                ]
                if renamed:
                    label = "absent:renamed_deprecated_alias_in_corpus"
                elif info.get("exists") and info.get("kind") in GENERATED_KINDS:
                    label = "absent:generated_declaration_not_indexed"
                elif info.get("exists"):
                    label = "absent:in_current_mathlib_env_not_in_corpus"
                elif by_suffix.get(name):
                    label = "absent:namespace_variant_in_corpus"
                else:
                    label = "absent:not_found_in_corpus_or_current_env"
            else:
                lex = rank(record, deepest, "lexical", ident)
                dense = rank(record, deepest, "dense", ident)
                if (lex is not None and lex <= deepest) or (
                    dense is not None and dense <= deepest
                ):
                    continue
                reach = record["reachability"][str(ident)]
                exhaustive = record["exhaustive_dense"]["ranks"].get(str(ident))
                package = corpus[name][1].split(".")[0]
                if case["packages"] and package not in case["packages"]:
                    label = "present:excluded_by_package_filter"
                elif (
                    not reach["probed"]
                    and exhaustive is not None
                    and exhaustive <= deepest
                ):
                    label = "present:ivf_probe_miss"
                elif not reach["probed"]:
                    label = "present:outside_probed_lists_and_below_exhaustive_depth"
                elif not reach["lexical_match"]:
                    label = "present:no_lexical_overlap_dense_below_depth"
                else:
                    label = "present:ranked_below_depth_in_both_channels"
            instance[membership["source"], label] += 1
            distinct[label].add(name)
            if len(examples[label]) < 8:
                examples[label].append(name)
    totals = collections.Counter()
    for (source, label), value in instance.items():
        totals[label] += value
    return dict(
        depth=deepest,
        instances_by_source={
            f"{s}|{label}": v for (s, label), v in sorted(instance.items())
        },
        instances=dict(totals),
        distinct_names={label: len(v) for label, v in distinct.items()},
        example_names=dict(examples),
    )


def validate(cases, records, availability, base):
    """Compare depth-1000 ranks with the archived end-to-end run's trace."""
    by_id = {c["id"]: c for c in cases}
    agree = collections.Counter()
    compared = collections.Counter()
    with (base / "records.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            query_id = line[13:77]
            if query_id not in by_id:
                continue
            old = json.loads(line)
            new = records[old["query_id"]]
            if old["status"] != "ok" or new["status"] != "ok":
                continue
            targets = {
                availability[t]
                for m in by_id[old["query_id"]]["memberships"]
                for t in m["targets"]
                if availability.get(t) is not None
            }
            for stage, base_stage in BASE_STAGES.items():
                ranking = old["trace"]["stages"].get(base_stage, [])
                position = {d: i for i, d in enumerate(ranking, 1)}
                for t in targets:
                    compared[stage] += 1
                    agree[stage] += position.get(t) == new["depths"]["1000"]["ranks"][
                        stage
                    ].get(str(t))
    return {
        s: dict(compared=compared[s], identical_rank=agree[s] / compared[s])
        for s in STAGES
        if compared[s]
    }


def costs(records):
    out = {}
    ok = [r for r in records.values() if r["status"] == "ok"]
    for k in DEPTHS:
        out[str(k)] = {
            part: dict(
                median=statistics.median(r["depths"][str(k)]["ms"][part] for r in ok),
                p95=statistics.quantiles(
                    [r["depths"][str(k)]["ms"][part] for r in ok], n=20
                )[-1],
            )
            for part in ("lexical", "dense", "fusion", "selection")
        }
        out[str(k)]["fused_candidates_median"] = statistics.median(
            r["depths"][str(k)]["lengths"]["fused"] for r in ok
        )
    out["embedding_ms_median"] = statistics.median(r["embed_ms"] for r in ok)
    out["exhaustive_dense_ms_median"] = statistics.median(
        r["exhaustive_dense"]["ms"] for r in ok
    )
    out["probed_vectors_median"] = statistics.median(r["probed_vectors"] for r in ok)
    out["bm25_matched_documents_median"] = statistics.median(
        r["bm25_matched"]["union"] for r in ok
    )
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "run", "base", "probe", "data", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    cases = labelled_cases(args.cases)
    records = load_journal(args.run, cases)
    availability = json.loads(
        (args.run / "target-availability.json").read_text(encoding="utf-8")
    )
    base_availability = json.loads(
        (args.base / "target-availability.json").read_text(encoding="utf-8")
    )
    if any(base_availability.get(t, v) != v for t, v in availability.items()):
        raise ValueError("Target availability differs from the archived run")
    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    corpus = corpus_names(args.data / "lean_explore.db")
    summary = dict(
        run_contract_sha256=digest(args.run / "contract.json"),
        depths=list(DEPTHS),
        errors=sum(r["status"] != "ok" for r in records.values()),
        requests=len(records),
        recall=recall_curves(cases, records, availability),
        selection_loss=selection_loss(cases, records, availability),
        misses=classify_misses(
            cases, records, availability, probe, corpus, max(DEPTHS)
        ),
        costs=costs(records),
        validation_against_archived_run=validate(
            cases, records, availability, args.base
        ),
    )
    write(args.out, summary)


if __name__ == "__main__":
    main()
