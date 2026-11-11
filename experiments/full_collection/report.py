"""Render aggregate coverage and results, excluding query text and small log cells."""

import argparse
from pathlib import Path

from report_aliases import load

LABELS = {
    "upstream_single_gold": "Upstream single-target labels",
    "upstream_alternative_premises": "Upstream alternative premise sets",
    "reply_link_proxy": "Reply-link targets (unverified proxies)",
    "historical_proposed_targets": "Historical proposed targets",
    "unlabelled": "No target labels in replay inputs",
}
RANKING_LABELS = {
    "lexical": "Lexical retrieval",
    "dense": "Dense retrieval",
    "fusion": "Rank fusion",
    "selection": "After candidate selection",
    "pre_rerank_same_pool": "Selected pool, before reranking",
    "current_mixture": "Final score mixture",
    "neural_only": "Neural score only",
    "without_final_dependency": "Mixture without final dependency term",
}
STYLE_LABELS = {
    "q1a_lean": "Lean statement",
    "q1b_latex": "LaTeX statement",
    "q1c_natural": "Natural-language statement",
    "q2_slogan": "Short description",
    "q3_nickname": "Nickname",
    "q4_special_case": "Special case",
    "NL_main_result": "Natural-language main result",
    "formal_statement": "Formal statement",
    "informal_statement": "Informal statement",
}
SOURCE_LABELS = {
    "query_log": "Usage logs",
    "discussion_candidates": "Discussion-derived queries",
    "mathlibqr": "MathlibQR",
    "mathlibmpr": "MathlibMPR",
    "fate_h": "FATE-H",
    "synthetic_discussion_pilot": "Synthetic discussion queries",
    "development_pilot": "Development pilot",
    "test_pilot": "Historical test requests",
    "candidate_selection_pilot": "Candidate-selection pilot",
    "earlier_calibration": "Earlier calibration queries",
}


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join(["---"] * len(headers)) + "|",
            *["| " + " | ".join(str(v) for v in row) + " |" for row in rows],
        ]
    )


def pct(value):
    return f"{100 * value:.2f}%"


def render(summary):
    inventory = summary["inventory"]
    op = summary["operation"]
    corrected = "reranker_max_length" in summary.get("settings", {})
    sections = [
        "# Corrected reranker: full collection replay"
        if corrected
        else "# Full collection benchmark",
        f"The local replay covers {op['requests']:,} distinct requests from {inventory['records']:,} source records. "
        f"It finished with {op['errors']:,} request errors and {op['empty_results']:,} empty result lists. "
        "Every supplied query was scheduled. Exact duplicates share one execution and retain every source membership.",
        "This expands the earlier pilot to the full prepared query collections. Raw archive messages are source material, not additional benchmark queries. "
        "No query text, user identifiers, per-request results or input hashes are published here.",
        "Read the [preprint](full-collection-preprint.md) for what these findings mean and which experiments they support. This report retains the detailed source and category tables.",
        "## Coverage",
        table(
            ["Collection", "Source records / query variants", "Distinct requests"],
            [
                (
                    SOURCE_LABELS.get(s["name"], s["name"]),
                    f"{s['records']:,}",
                    f"{s['distinct_requests']:,}",
                )
                for s in inventory["sources"]
            ],
        ),
        "Source counts overlap where the same request belongs to several collections. Usage-log records include repeated searches. "
        "MathlibQR has 200 target groups; MathlibMPR has 69 problems and both natural-language and formal queries; FATE-H has 100 problems and both statement forms.",
        table(
            ["Query form", "Distinct requests"],
            [(k, f"{v:,}") for k, v in sorted(inventory["categories"]["form"].items())],
        ),
        "The five forms use documented surface rules. The additional surface, intent-cue and domain-cue breakdowns below retain unknown categories. "
        "They are not human annotations or a refit of the earlier first-day Gaussian-mixture categories.",
        "## Evaluation conditions",
        summary.get("execution_scope", "End-to-end instrumented baseline replay."),
        "The run uses the pinned local LeanExplore engine and corpus, Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B. "
        "BM25 and dense retrieval each request 1,000 candidates. Selection operates on the top 500 fused candidates. The current mixture reranks 25 candidates and returns up to 25 results. "
        "Original package filters are retained. The external run manifest pins code, data and model inputs.",
        "Eight diagnostic rankings are derived from each search: lexical, dense, fusion, selection, the same pool before reranking, "
        "the current mixture, neural-only scores, and the mixture without its final dependency term. Raw retrieval stages precede package filtering; "
        "only the same-pool comparisons isolate reranking. These are not eight independently executed search services.",
        "The earlier pilot used ten reranker candidates and the earlier MathlibQR reference used 100. Their scores are separate conditions and are not pooled with this run.",
        f"Mean instrumented {'reranking-only replay' if corrected else 'end-to-end'} time was {op['latency_ms_mean']:.1f} ms per distinct request. "
        f"Reranking changed the first result relative to the selected pool's incoming order for {op['top1_changed']:,} requests. "
        f"Of {op['reranked_pairs']:,} query-document pairs sent to the reranker, {op['truncated_pairs']:,} exceeded its input limit. "
        "The journal records per-pair token counts.",
        "## Results by collection and label type",
        "Success means at least one recorded target appears in the cutoff; recall is the fraction of recorded targets recovered. "
        "nDCG uses binary relevance for those targets. Absent target names and failed requests remain in the denominator. "
        "These metrics do not establish that other results are irrelevant. Reply-link and historical-proposal scores are diagnostics, not validated relevance.",
    ]
    for row in summary["slices"]:
        if row["axis"] != "all":
            continue
        sections += [
            f"### {SOURCE_LABELS.get(row['source'], row['source'])}: {LABELS[row['label_kind']]}",
            f"{row['requests']:,} source records; {row['labelled_requests']:,} with recorded targets; {row['errors']:,} request errors.",
        ]
        if row["metrics"]:
            sections.append(
                table(
                    ["Ranking", "Success@1", "Success@10", "Recall@10", "nDCG@10"],
                    [
                        (
                            RANKING_LABELS[c],
                            pct(m["success@1"]),
                            pct(m["success@10"]),
                            pct(m["recall@10"]),
                            f"{m['ndcg@10']:.4f}",
                        )
                        for c, m in row["metrics"].items()
                    ],
                )
            )
            current = row["metrics"]["current_mixture"]
            if "complete_route@10" in current:
                sections.append(
                    f"At least one complete recorded premise route appears in the top ten for {pct(current['complete_route@10'])} of queries. "
                    "This checks premise retrieval; it does not prove the theorem."
                )
            sections.append(
                table(
                    [
                        "Raw retrieval stage",
                        "Known-target recall@100",
                        "Known-target recall@1000",
                    ],
                    [
                        (RANKING_LABELS[c], pct(m["recall@100"]), pct(m["recall@1000"]))
                        for c, m in row["metrics"].items()
                        if "recall@100" in m
                    ],
                )
            )
        else:
            sections.append(
                "No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes."
            )
            if row["source"] == "fate_h":
                sections.append(
                    "FATE-H remains a retrieval diagnostic; no proof-completion claim is made."
                )
            if row["source"] == "test_pilot":
                sections.append(
                    "These frozen test requests are included in full. Their historical graded judgments remain in the separately versioned assisted-v2 pilot reports; this replay does not convert them into a target list."
                )
    sections += [
        "## Results by category",
        "The following tables use the current mixture. Repeated source records retain their frequency; the coverage table separately shows distinct requests. "
        "Usage-log category cells with fewer than ten records are suppressed. Metrics are never pooled across label types.",
        "Top-1 changes in these tables compare each condition with its candidate pool's order before reranking. The preprint reports the separate paired comparison between the original and corrected implementations.",
        "Upstream domain tags can overlap: a FATE-H query contributes to each of its recorded tags.",
    ]
    axes = (
        "form",
        "surface",
        "upstream_style",
        "difficulty",
        "intent_cue",
        "domain_cue",
        "upstream_domain",
        "channel",
        "original_form",
        "original_intent",
        "original_domain",
    )
    for axis in axes:
        rows = []
        log_cells = [
            r
            for r in summary["slices"]
            if r["axis"] == axis and r["source"] == "query_log"
        ]
        suppressed = {r["category"] for r in log_cells if r["requests"] < 10}
        visible = [r for r in log_cells if r["requests"] >= 10]
        if len(suppressed) == 1 and visible:
            suppressed.add(min(visible, key=lambda r: r["requests"])["category"])
        for row in summary["slices"]:
            if row["axis"] != axis or (
                row["source"] == "query_log" and row["category"] in suppressed
            ):
                continue
            m = (row["metrics"] or {}).get("current_mixture")
            rows.append(
                (
                    SOURCE_LABELS.get(row["source"], row["source"]),
                    STYLE_LABELS.get(
                        row["category"], row["category"].replace("_", " ")
                    ),
                    f"{row['requests']:,}",
                    pct(m["success@10"]) if m else "unlabelled",
                    f"{m['ndcg@10']:.4f}" if m else "unavailable",
                    row["errors"],
                    pct(1 - row["empty_results"] / row["requests"]),
                    pct(row["top1_changed"] / row["requests"]),
                )
            )
        if rows:
            sections += [
                f"### {axis.replace('_', ' ').capitalize()}",
                table(
                    [
                        "Collection",
                        "Category",
                        "Records",
                        "Success@10",
                        "nDCG@10",
                        "Errors",
                        "Nonempty results",
                        "Top-1 changed / records",
                    ],
                    rows,
                ),
            ]
    sections += [
        "## Limits and remaining review",
        *summary["limitations"],
        "A linked reply can mention a supporting lemma, an unsuitable answer or a newer declaration absent from the pinned corpus. "
        "The 2,079 discussion-derived queries came from a prior extraction that required a declaration link in a later reply. "
        "This selection excludes many unanswered requests and cannot measure general no-answer detection.",
        "Unknown intent and domain are retained explicitly. A larger run does not resolve missing judgments, source bias or mathematical equivalence. "
        "No model was tuned on this full collection, and the exposed material must not be presented as a fresh test set.",
        "## Reproduction",
        "See [the full-collection workflow](../experiments/full_collection/README.md). "
        "The external package contains the source inventory, frozen schedule, complete result journal, label provenance and per-request scores. "
        "Reconstruction refuses missing records, changed inputs or a changed schedule.",
    ]
    return "\n\n".join(sections) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-aliases", type=Path)
    args = parser.parse_args()
    text = render(load(args.summary, args.source_aliases))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
