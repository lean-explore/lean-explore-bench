"""Build an explicitly AI-assisted evaluation without accepting AI as human."""

from __future__ import annotations

import copy
from typing import Any

from leanexplore_benchmark.corpus import Corpus, fingerprint
from leanexplore_benchmark.pooling import validate_reviews

Json = dict[str, Any]


def prepare_assisted(
    prepared: Json,
    corpus: Corpus,
    packet: Json,
    submission: Json,
    *,
    validation_profile: str,
    exclusions: dict[str, str] | None = None,
) -> Json:
    """Use resolved proposals, with accepted human grades taking precedence."""
    if validation_profile != "assisted-v1":
        raise ValueError("Explicit assisted-v1 validation profile required")
    if submission.get("assessor_type") != "assistant":
        raise ValueError("This input must be an assistant proposal submission")
    validated = validate_reviews(packet, submission)
    if packet.get("corpus_revision") != corpus.revision:
        raise ValueError("Packet and corpus revisions differ")
    base = prepared["collection"]
    if base.get("validation_profile") or any(
        "judgment_origins" in q for q in base["queries"]
    ):
        raise ValueError("Start from the human-only prepared collection")
    collection = copy.deepcopy(base)
    if collection["corpus_revision"] != corpus.revision:
        raise ValueError("Collection and corpus revisions differ")
    queries = {q["id"]: q for q in collection["queries"]}
    excluded = exclusions or {}
    if set(excluded) - queries.keys() or any(not r.strip() for r in excluded.values()):
        raise ValueError("Exclusions require known cases and reasons")
    origins: dict[str, dict[str, str]] = {
        qid: dict.fromkeys(q["judgments"], "accepted_human")
        for qid, q in queries.items()
    }
    targets = []
    canonical_pairs: set[tuple[str, str]] = set()
    for record in submission["records"]:
        qid = record["case_id"]
        if qid not in queries:
            raise ValueError("Proposal case missing from collection")
        doc = corpus.require(record["document_id"])
        pair = qid, doc
        if pair in canonical_pairs:
            raise ValueError("Repeated canonical proposal pair")
        canonical_pairs.add(pair)
        target = "HC-P-" + fingerprint(list(pair))[:16]
        targets.append(
            dict(
                id=target,
                case_id=qid,
                document_id=doc,
                proposed_grade=record["grade"],
                reason=record["reason"],
                status="pending",
                independent_human_review=False,
            )
        )
        if qid in excluded or record["uncertain"] or record["grade"] is None:
            continue
        if doc not in queries[qid]["judgments"]:
            queries[qid]["judgments"][doc] = record["grade"]
            origins[qid][doc] = "assistant_proposal"
    for qid, q in queries.items():
        if qid in excluded:
            q["judgments"] = {}
            origins[qid] = {}
            q["answerability"] = "unknown"
            q["quality_exclusion"] = excluded[qid]
        elif any(g >= 2 for g in q["judgments"].values()):
            q["answerability"] = "answerable"
        # No positive proposal never establishes that no answer exists.
        q["judgment_origins"] = origins[qid]
    collection["validation_profile"] = validation_profile
    collection["independent_human_validation"] = False
    return dict(
        collection=collection,
        original_human_collection_sha256=fingerprint(prepared["collection"]),
        validated_proposals=validated,
        human_check_targets=targets,
        exclusions=excluded,
        warning="AI-assisted labels; no independent human validation.",
    )


def apply_human_corrections(assisted: Json, corrections: list[Json]) -> Json:
    """Version explicit human decisions without changing stored retrieval runs."""
    from leanexplore_benchmark.collection import _review

    result = copy.deepcopy(assisted)
    queries = {q["id"]: q for q in result["collection"]["queries"]}
    targets = {
        (t["case_id"], t["document_id"]): t for t in result["human_check_targets"]
    }
    seen = set()
    for correction in corrections:
        _review(correction)
        if correction["assessor_type"] != "human" or correction["status"] != "accepted":
            raise ValueError(
                "Correction requires an explicitly accepted human decision"
            )
        pair = correction.get("case_id"), correction.get("document_id")
        grade = correction.get("grade")
        if pair not in targets or pair in seen:
            raise ValueError("Unknown or repeated correction pair")
        if type(grade) is not int or grade not in range(4):
            raise ValueError("Correction requires an integer grade 0..3")
        seen.add(pair)
        qid, doc = pair
        q = queries[qid]
        if qid in result.get("exclusions", {}):
            raise ValueError("Repair the excluded query in a separate version first")
        q["judgments"][doc] = grade
        q["judgment_origins"][doc] = "accepted_human"
        q["answerability"] = (
            "answerable" if any(g >= 2 for g in q["judgments"].values()) else "unknown"
        )
        targets[pair]["status"] = "reviewed"
        targets[pair]["human_decision"] = copy.deepcopy(correction)
    result["parent_assisted_sha256"] = fingerprint(assisted)
    result.setdefault("human_correction_history", []).append(copy.deepcopy(corrections))
    return result
